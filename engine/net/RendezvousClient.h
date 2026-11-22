#pragma once

#include "engine/net/NetAddress.h"
#include "engine/net/RendezvousProtocol.h"

#include <cstdint>
#include <functional>
#include <optional>
#include <random>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
// How a joining game reaches its host.
enum class JoinPath : uint8_t
{
    None,
    // The host's own address on a shared network.
    Lan,
    // The host's public address, through both routers.
    Direct,
    // Through the rendezvous server's relay port.
    Relay,
};

enum class JoinState : uint8_t
{
    Idle,
    AskingServer,
    OpeningPath,
    AskingForRelay,
    BindingRelay,
    Ready,
    Failed,
};

enum class JoinFailure : uint8_t
{
    None,
    ServerSilent,
    NoSuchSession,
    RelayUnavailable,
    RelaySilent,
};

const char *toString(JoinPath path);
const char *toString(JoinFailure failure);

// A game's side of the rendezvous protocol, for a host and for a joining game. It sends and receives through the
// game's one UDP socket (the functions given to it) and holds no socket of its own.
class RendezvousClient
{
public:
    using SendFunction = std::function<void(const NetAddress &to, std::span<const uint8_t> datagram)>;

    RendezvousClient(SendFunction send, const NetAddress &server);

    // Host: registers the session and keeps it alive. `localAddress` is the host's address on its own network.
    void startHosting(const SessionInfo &info, const NetAddress &localAddress);
    void updateSessionInfo(const SessionInfo &info);
    void stopHosting();
    bool registered() const;
    std::string sessionCode() const;
    NetAddress publicAddress() const;
    // Test only: a host that does not answer punches, as behind a router no path opens through.
    void setAnswerPunches(bool answer);

    // Joining game: asks for the session list. The answer replaces sessionList().
    void requestList();
    const std::optional<std::vector<SessionListEntry>> &sessionList() const;

    // Joining game: finds a path to the session's host. With `relayOnly` no direct path is tried.
    void startJoin(const SessionCode &code, const NetAddress &localAddress, bool relayOnly);
    JoinState joinState() const;
    JoinPath joinPath() const;
    JoinFailure joinFailure() const;
    // The address to connect the transport to, once the state is Ready.
    NetAddress joinAddress() const;

    // True for a relay port of the server: a peer at such an address is a relayed one.
    bool isRelayAddress(const NetAddress &address) const;

    void update(uint32_t nowMs);
    // Returns true when the datagram was a rendezvous one (and so not the transport's).
    bool handleDatagram(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs);

private:
    struct HostPunch
    {
        uint32_t introId = 0;
        NetAddress publicAddress;
        NetAddress localAddress;
        uint16_t relayPort = 0;
        uint64_t relayToken = 0;
        bool relayBound = false;
        uint32_t startedMs = 0;
        uint32_t lastSentMs = 0;
        // The game's punches answered in the second that began at `answersSinceMs`.
        uint32_t answersSinceMs = 0;
        uint32_t answers = 0;
    };

    void send(const NetAddress &to, const std::vector<uint8_t> &datagram);
    void sendListRequest();
    void sendJoinRequest(uint32_t nowMs);
    void failJoin(JoinFailure failure);

    SendFunction m_send;
    NetAddress m_server;
    // The numbers that tell this game's answers from anyone else's datagrams. Each is drawn from the system: a
    // host or a server that was sent some must not be able to work out the next.
    std::random_device m_random;
    // The server's stamp on this game's address (AddressCookieMessage), sent with every request. 0 until the
    // server gave one; a request without a good one is answered with the cookie and said again.
    uint64_t m_cookie = 0;

    bool m_hosting = false;
    bool m_answerPunches = true;
    SessionInfo m_sessionInfo;
    NetAddress m_hostLocalAddress;
    uint32_t m_registerNonce = 0;
    uint64_t m_sessionKey = 0;
    SessionCode m_sessionCode = {};
    NetAddress m_publicAddress;
    uint32_t m_lastRegisterMs = 0;
    // When the server last answered a registration or a heartbeat.
    uint32_t m_lastRegisteredMs = 0;
    bool m_registerSentOnce = false;
    std::vector<HostPunch> m_hostPunches;

    uint32_t m_listNonce = 0;
    // A list was asked for and has not come yet.
    bool m_listPending = false;
    std::optional<std::vector<SessionListEntry>> m_sessionList;

    JoinState m_joinState = JoinState::Idle;
    JoinPath m_joinPath = JoinPath::None;
    JoinFailure m_joinFailure = JoinFailure::None;
    SessionCode m_joinCode = {};
    NetAddress m_joinLocalAddress;
    bool m_joinRelayOnly = false;
    uint32_t m_joinNonce = 0;
    uint32_t m_joinStateStartedMs = 0;
    uint32_t m_joinLastSentMs = 0;
    bool m_joinStateFresh = false;
    JoinReplyMessage m_joinReply;
    NetAddress m_joinAddress;
};
}
