#pragma once

#include "engine/net/NetAddress.h"
#include "engine/net/RendezvousProtocol.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <list>
#include <random>
#include <span>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
struct RendezvousServerConfig
{
    // 0 lets the system pick the ports (tests); otherwise the relay ports are port + 1 ... port + relayPortCount.
    uint16_t port = 27910;
    uint16_t relayPortCount = 16;
    uint32_t sessionTimeoutMs = 20000;
    uint32_t joinMemoryMs = 15000;
    uint32_t relayIdleTimeoutMs = 30000;
    // The most one relayed pair may send through in a second, both directions together. 0: no limit.
    uint32_t relayBytesPerSecond = 512 * 1024;
    // Test only: this share of relayed datagrams is thrown away.
    uint32_t relayDropPermille = 0;
    size_t maxSessions = 1024;
    // What one address (whatever its port) may ask of the main port: so many requests a second on the average and
    // so many at once. A game's heartbeat, list and join requests are a few a second at the most. 0: no limit.
    // Only requests that carry the address's cookie are counted, so that datagrams sent with a forged address use
    // up nothing of what the address's owner may ask. What carries a session's key (its heartbeats) has the same
    // allowance for each session, apart from the address's.
    uint32_t requestsPerSecond = 10;
    uint32_t requestBurst = 40;
    // The most addresses whose allowance is remembered at a time.
    size_t maxRequesters = 4096;
    // The most sessions one address (whatever its port) may have open: several games behind one router, not a
    // table filled from one place. It holds for a session that moves to the address as well.
    size_t maxSessionsPerAddress = 8;
    // The most relay ports the joiners of one session, and the joiners at one address, may hold at a time, so that
    // one place cannot take every port. A session has three guests at the most. An address has one: its newer
    // request takes the place of an older one whose port carries nothing; two games behind one router that both
    // need the relay do not both get it.
    size_t maxRelaysPerSession = 4;
    size_t maxRelaysPerAddress = 1;
    // A relay port that both sides have not bound to within this time is taken back. A game keeps trying to bind
    // for five seconds.
    uint32_t relayBindTimeoutMs = 6000;
    // A relay port joins a game on the service's own network or machine (a private or loopback address) only with
    // another such game: the service is no way from the internet into its own network. True lets a game on the
    // service's network be relayed with one on the internet, for a service that runs beside its owner's games.
    bool relayBetweenLanAndInternet = false;
    // How long the secret behind the address cookies is used before a new one takes its place. A cookie is good
    // while its secret is the newest or the one before: for this long at least and twice as long at the most.
    uint32_t cookieLifetimeMs = 60000;
    // The most lines the log gets in a minute, however much happens; what was left out is counted in one line
    // afterwards. 0: no limit.
    uint32_t logLinesPerMinute = 120;
    bool verbose = false;
};

// What an address or a session may still ask: so many requests a second on the average, so many at once.
struct RequestAllowance
{
    float tokens = 0.0f;
    uint32_t lastMs = 0;
};

// The allowance of every address that asks something of the service. It remembers a bounded number of addresses
// and forgets the one heard from longest ago first, and finding an address does not take longer the more there are.
class RequestLimiter
{
public:
    // `requestsPerSecond` 0: no limit, and nothing is remembered.
    void configure(uint32_t requestsPerSecond, uint32_t burst, size_t maxAddresses);
    // True when the address (its host alone, as NetAddress keeps it) may ask now; the request is then counted.
    // `firstRefusal` is set for the first request refused since the address was last answered.
    bool allow(uint32_t host, uint32_t nowMs, bool &firstRefusal);
    // Forgets the addresses not heard from for `idleMs`: they have their whole allowance again.
    void expire(uint32_t nowMs, uint32_t idleMs);
    void clear();
    size_t size() const;

private:
    struct Requester
    {
        uint32_t host = 0;
        RequestAllowance allowance;
        bool refusalLogged = false;
    };

    uint32_t m_requestsPerSecond = 0;
    uint32_t m_burst = 0;
    size_t m_maxAddresses = 0;
    // The address heard from longest ago first.
    std::list<Requester> m_requesters;
    std::unordered_map<uint32_t, std::list<Requester>::iterator> m_byHost;
};

struct RendezvousServerStats
{
    size_t sessions = 0;
    size_t relaysInUse = 0;
    uint64_t relayedDatagrams = 0;
    uint64_t relayedBytes = 0;
    uint64_t droppedDatagrams = 0;
    // Requests of an address that asked too much, not answered.
    uint64_t refusedRequests = 0;
};

// The rendezvous and relay service. It keeps a list of hosted sessions, tells a joining game and the host each
// other's addresses, and where no direct path opens it forwards their datagrams through a relay port of its own.
// It never reads what it forwards and decides nothing about the game.
// A datagram's sender address can be forged, so the service does nothing for an address before that address has
// sent back the cookie the service sent to it (RendezvousProtocol.h, AddressCookieMessage): no session, no join,
// no relay port and no list. The cookie is a keyed hash of the address under a secret that changes every minute;
// the service keeps nothing for the addresses it gave one.
class RendezvousServer
{
public:
    RendezvousServer();
    ~RendezvousServer();

    RendezvousServer(const RendezvousServer &) = delete;
    RendezvousServer &operator=(const RendezvousServer &) = delete;

    bool start(const RendezvousServerConfig &config);
    void stop();

    // Waits up to `timeoutMs` for datagrams, handles what arrived and expires what is old.
    void service(uint32_t timeoutMs);

    uint16_t port() const;
    RendezvousServerStats stats() const;
    // The most relay ports a configuration may ask for: the service waits on all its sockets at once, and the
    // system's set of sockets to wait on has a fixed size.
    static size_t maxRelayPorts();

private:
    struct Session
    {
        uint64_t sessionKey = 0;
        // The number of the registration that opened it. Its repeat (the answer was lost) is told by it from
        // another registration from the same address, which opens a session of its own and never changes this one.
        uint32_t registerNonce = 0;
        SessionCode code = {};
        SessionInfo info;
        NetAddress publicAddress;
        NetAddress localAddress;
        uint32_t lastSeenMs = 0;
        // What may still be asked with the session's key (heartbeats), counted apart from its address.
        RequestAllowance allowance;
    };

    struct RelaySlot
    {
        intptr_t socket = -1;
        uint16_t port = 0;
        bool inUse = false;
        // Whose it is while in use: the join request it was given out for, that request's session and the
        // address that asked.
        uint32_t introId = 0;
        uint64_t sessionKey = 0;
        uint32_t requesterHost = 0;
        // The session's host as the service saw it when the port was given out. Each side binds from the host
        // its token was sent to and from no other, so a port never forwards to somebody who did not ask for it.
        uint32_t sessionHost = 0;
        uint64_t hostToken = 0;
        uint64_t clientToken = 0;
        NetAddress hostAddress;
        NetAddress clientAddress;
        uint32_t lastActivityMs = 0;
        uint32_t budgetWindowMs = 0;
        uint32_t budgetBytes = 0;
        // What went through since the port was given out, for the log.
        uint64_t relayedBytes = 0;
        uint32_t startedMs = 0;
    };

    // One join request, remembered so that its repeats get the same answer and the same relay port.
    struct JoinRecord
    {
        NetAddress clientAddress;
        uint32_t nonce = 0;
        uint32_t introId = 0;
        int relaySlot = -1;
        uint32_t createdMs = 0;
    };

    void handleMainDatagram(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs);
    void handleRelayDatagram(
        RelaySlot &slot,
        const NetAddress &from,
        std::span<const uint8_t> datagram,
        uint32_t nowMs);
    void handleHostRegister(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs);
    void handleHostUnregister(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs);
    void handleListRequest(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs);
    // True when the cookie is the service's own stamp on this address: who sent it is there.
    bool hasCookie(const NetAddress &from, uint64_t cookie) const;
    void sendCookie(const NetAddress &to, uint32_t nonce);
    size_t sessionsOfAddress(uint32_t host) const;
    // True when a line may be written to the log now; the line is then counted.
    bool mayLog(uint32_t nowMs);
    // Begins the log's next minute when the last is over, and says how many lines that one left out.
    void turnLogMinute(uint32_t nowMs);
    void handleJoinRequest(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs);
    void expire(uint32_t nowMs);
    bool allowRequest(const NetAddress &from, uint32_t nowMs);
    Session *findSession(const SessionCode &code);
    Session *findSessionByKey(uint64_t sessionKey);
    void sendRegistered(const Session &session, const NetAddress &to, uint32_t nonce);
    // A free relay port for a join request, or -1: none is free, or the session or the address has its share.
    int allocateRelaySlot(const Session &session, const NetAddress &requester, uint32_t introId, uint32_t nowMs);
    void releaseRelaySlot(RelaySlot &slot, uint32_t nowMs);
    void sendFrom(intptr_t socket, const NetAddress &to, std::span<const uint8_t> datagram);
    // A number from the system's own source, drawn for each key, code and token.
    uint64_t randomValue();
    uint64_t randomNonZero();

    NetLibrary m_enet;
    RendezvousServerConfig m_config;
    intptr_t m_socket = -1;
    uint16_t m_port = 0;
    std::vector<Session> m_sessions;
    std::vector<RelaySlot> m_relaySlots;
    std::vector<JoinRecord> m_joins;
    // What each address may still ask of the main port (requestsPerSecond, requestBurst).
    RequestLimiter m_requestLimiter;
    uint32_t m_nextIntroId = 1;
    // Session keys, codes and relay tokens are handed to games, and whoever holds some must not be able to work
    // out the others: each is drawn from the system, never from a generator that continues from a seed.
    std::random_device m_entropy;
    // The secrets behind the address cookies, the newest first, and when the newest was drawn.
    std::array<std::array<uint64_t, 2>, 2> m_cookieSecrets = {};
    uint32_t m_cookieSecretSinceMs = 0;
    // The log's minute: when it began, the lines written in it and the lines left out.
    uint32_t m_logMinuteSinceMs = 0;
    uint32_t m_logLinesThisMinute = 0;
    uint64_t m_logLinesLeftOut = 0;
    // Only for relayDropPermille, the test's thrown-away datagrams.
    std::mt19937_64 m_random;
    RendezvousServerStats m_stats;
};
}
