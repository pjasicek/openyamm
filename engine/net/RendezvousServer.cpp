#include "engine/net/RendezvousServer.h"

#include <enet/enet.h>

#include <algorithm>
#include <array>
#include <cstdio>
#include <cstring>

namespace OpenYAMM::Engine
{
namespace
{
constexpr intptr_t NoSocket = -1;

ENetSocket enetSocket(intptr_t socket)
{
    return ENetSocket(socket);
}

intptr_t openDatagramSocket(uint16_t port, uint16_t &boundPort)
{
    const ENetSocket socket = enet_socket_create(ENET_SOCKET_TYPE_DATAGRAM);

    if (socket == ENET_SOCKET_NULL)
    {
        return NoSocket;
    }

#ifndef _WIN32
    // The set of sockets the service waits on is indexed by the socket's number here: one beyond its size would
    // be written outside it.
    if (socket >= FD_SETSIZE)
    {
        enet_socket_destroy(socket);
        return NoSocket;
    }
#endif

    ENetAddress address = {};
    address.host = ENET_HOST_ANY;
    address.port = port;

    if (enet_socket_bind(socket, &address) != 0 || enet_socket_set_option(socket, ENET_SOCKOPT_NONBLOCK, 1) != 0
        || enet_socket_get_address(socket, &address) != 0)
    {
        enet_socket_destroy(socket);
        return NoSocket;
    }

    boundPort = address.port;
    return intptr_t(socket);
}

// One datagram from the socket, without waiting. Length 0 when there is none.
size_t receiveFrom(intptr_t socket, NetAddress &from, std::array<uint8_t, 4096> &storage)
{
    ENetAddress address = {};
    ENetBuffer buffer = {};
    buffer.data = storage.data();
    buffer.dataLength = storage.size();
    const int length = enet_socket_receive(enetSocket(socket), &address, &buffer, 1);

    if (length <= 0)
    {
        return 0;
    }

    from.host = address.host;
    from.port = address.port;
    return size_t(length);
}

// Takes one request out of an allowance, which first gets back what was not used since, up to `burst`. False when
// nothing is left.
bool takeRequest(RequestAllowance &allowance, uint32_t requestsPerSecond, uint32_t burst, uint32_t nowMs)
{
    allowance.tokens = std::min(float(burst),
        allowance.tokens + float(nowMs - allowance.lastMs) * 0.001f * float(requestsPerSecond));
    allowance.lastMs = nowMs;

    if (allowance.tokens < 1.0f)
    {
        return false;
    }

    allowance.tokens -= 1.0f;
    return true;
}

// Join requests remembered at a time; the oldest is forgotten first.
constexpr size_t MaxJoinRecords = 1024;
// A relay port that forwarded something this short a while ago carries a game; a quieter one of the same address
// gives way to that address's next request.
constexpr uint32_t RelayLiveMs = 10000;

uint64_t rotateLeft(uint64_t value, int bits)
{
    return (value << bits) | (value >> (64 - bits));
}

// SipHash-2-4 (Aumasson and Bernstein) of a short message under a 128-bit key: a keyed hash made for this, numbers
// that nobody without the key can make or tell from chance.
uint64_t sipHash(const std::array<uint64_t, 2> &key, std::span<const uint8_t> message)
{
    uint64_t v0 = key[0] ^ 0x736f6d6570736575ull;
    uint64_t v1 = key[1] ^ 0x646f72616e646f6dull;
    uint64_t v2 = key[0] ^ 0x6c7967656e657261ull;
    uint64_t v3 = key[1] ^ 0x7465646279746573ull;
    const auto mix = [&v0, &v1, &v2, &v3](int rounds)
    {
        for (int round = 0; round < rounds; ++round)
        {
            v0 += v1;
            v1 = rotateLeft(v1, 13) ^ v0;
            v0 = rotateLeft(v0, 32);
            v2 += v3;
            v3 = rotateLeft(v3, 16) ^ v2;
            v0 += v3;
            v3 = rotateLeft(v3, 21) ^ v0;
            v2 += v1;
            v1 = rotateLeft(v1, 17) ^ v2;
            v2 = rotateLeft(v2, 32);
        }
    };
    // Eight bytes at a time, the lowest first; the last word carries what is left and the length in its top byte.
    uint64_t word = 0;

    for (size_t index = 0; index < message.size(); ++index)
    {
        word |= uint64_t(message[index]) << (8 * (index % 8));

        if (index % 8 == 7)
        {
            v3 ^= word;
            mix(2);
            v0 ^= word;
            word = 0;
        }
    }

    word |= uint64_t(message.size()) << 56;
    v3 ^= word;
    mix(2);
    v0 ^= word;
    v2 ^= 0xFF;
    mix(4);
    return v0 ^ v1 ^ v2 ^ v3;
}

// The service's stamp on an address under one of its secrets. Never 0, which is a request without a cookie.
uint64_t addressCookie(const std::array<uint64_t, 2> &secret, const NetAddress &address)
{
    std::array<uint8_t, 6> bytes = {};
    std::memcpy(bytes.data(), &address.host, 4);
    bytes[4] = uint8_t(address.port);
    bytes[5] = uint8_t(address.port >> 8);
    const uint64_t cookie = sipHash(secret, bytes);
    return cookie != 0 ? cookie : 1;
}
}

void RequestLimiter::configure(uint32_t requestsPerSecond, uint32_t burst, size_t maxAddresses)
{
    clear();
    m_requestsPerSecond = requestsPerSecond;
    m_burst = burst;
    m_maxAddresses = std::max<size_t>(maxAddresses, 1);
}

bool RequestLimiter::allow(uint32_t host, uint32_t nowMs, bool &firstRefusal)
{
    firstRefusal = false;

    if (m_requestsPerSecond == 0)
    {
        return true;
    }

    const std::unordered_map<uint32_t, std::list<Requester>::iterator>::iterator found = m_byHost.find(host);

    if (found != m_byHost.end())
    {
        // Heard from now: to the end of the list, the last to be forgotten.
        m_requesters.splice(m_requesters.end(), m_requesters, found->second);
    }
    else
    {
        // A full table forgets the address heard from longest ago. That address then starts with a whole
        // allowance when it asks again, which is all a flood of forged addresses gains.
        if (m_requesters.size() >= m_maxAddresses)
        {
            m_byHost.erase(m_requesters.front().host);
            m_requesters.pop_front();
        }

        m_requesters.push_back(Requester{host, RequestAllowance{float(m_burst), nowMs}, false});
        m_byHost[host] = std::prev(m_requesters.end());
    }

    Requester &requester = m_requesters.back();

    if (!takeRequest(requester.allowance, m_requestsPerSecond, m_burst, nowMs))
    {
        firstRefusal = !requester.refusalLogged;
        requester.refusalLogged = true;
        return false;
    }

    requester.refusalLogged = false;
    return true;
}

void RequestLimiter::expire(uint32_t nowMs, uint32_t idleMs)
{
    while (!m_requesters.empty() && nowMs - m_requesters.front().allowance.lastMs > idleMs)
    {
        m_byHost.erase(m_requesters.front().host);
        m_requesters.pop_front();
    }
}

void RequestLimiter::clear()
{
    m_requesters.clear();
    m_byHost.clear();
}

size_t RequestLimiter::size() const
{
    return m_requesters.size();
}

RendezvousServer::RendezvousServer()
    : m_random(std::random_device{}())
{
}

size_t RendezvousServer::maxRelayPorts()
{
#ifdef _WIN32
    // The set holds so many sockets, whatever their numbers; one place is the main port's.
    return FD_SETSIZE - 1;
#else
    // The set is indexed by the sockets' numbers, which the system gives out from the lowest free one. Some are
    // the program's before the service starts; a socket that still gets too high a number fails the start.
    return FD_SETSIZE - 16;
#endif
}

RendezvousServer::~RendezvousServer()
{
    stop();
}

bool RendezvousServer::start(const RendezvousServerConfig &config)
{
    stop();

    // More relay ports than the service can wait on at once, or ports beyond the last one there is.
    if (config.relayPortCount > maxRelayPorts() || (config.port != 0 && config.port + config.relayPortCount > 65535))
    {
        return false;
    }

    m_config = config;
    m_requestLimiter.configure(config.requestsPerSecond, config.requestBurst, config.maxRequesters);
    // Both secrets new: no cookie from before this start is good.
    m_cookieSecrets = {{{randomValue(), randomValue()}, {randomValue(), randomValue()}}};
    m_cookieSecretSinceMs = netNowMilliseconds();
    m_logMinuteSinceMs = m_cookieSecretSinceMs;
    m_logLinesThisMinute = 0;
    m_logLinesLeftOut = 0;
    m_socket = openDatagramSocket(config.port, m_port);

    if (m_socket == NoSocket)
    {
        return false;
    }

    for (uint16_t index = 0; index < config.relayPortCount; ++index)
    {
        RelaySlot slot;
        const uint16_t wanted = config.port == 0 ? uint16_t(0) : uint16_t(config.port + 1 + index);
        slot.socket = openDatagramSocket(wanted, slot.port);

        if (slot.socket == NoSocket)
        {
            stop();
            return false;
        }

        m_relaySlots.push_back(slot);
    }

    return true;
}

void RendezvousServer::stop()
{
    if (m_socket != NoSocket)
    {
        enet_socket_destroy(enetSocket(m_socket));
        m_socket = NoSocket;
    }

    for (RelaySlot &slot : m_relaySlots)
    {
        enet_socket_destroy(enetSocket(slot.socket));
    }

    m_relaySlots.clear();
    m_sessions.clear();
    m_joins.clear();
    m_requestLimiter.clear();
    m_stats = {};
}

uint16_t RendezvousServer::port() const
{
    return m_port;
}

RendezvousServerStats RendezvousServer::stats() const
{
    RendezvousServerStats stats = m_stats;
    stats.sessions = m_sessions.size();
    stats.relaysInUse = size_t(std::count_if(
        m_relaySlots.begin(), m_relaySlots.end(), [](const RelaySlot &slot) { return slot.inUse; }));
    return stats;
}

void RendezvousServer::service(uint32_t timeoutMs)
{
    if (m_socket == NoSocket)
    {
        return;
    }

    ENetSocketSet readSet;
    ENET_SOCKETSET_EMPTY(readSet);
    ENET_SOCKETSET_ADD(readSet, enetSocket(m_socket));
    ENetSocket highest = enetSocket(m_socket);

    // Only relay ports in use are watched; a datagram to a free one waits unread until the port is given out, and
    // is then dropped as coming from neither side.
    for (const RelaySlot &slot : m_relaySlots)
    {
        if (slot.inUse)
        {
            ENET_SOCKETSET_ADD(readSet, enetSocket(slot.socket));
            highest = std::max(highest, enetSocket(slot.socket));
        }
    }

    if (enet_socketset_select(highest, &readSet, nullptr, timeoutMs) < 0)
    {
        return;
    }

    const uint32_t nowMs = netNowMilliseconds();
    std::array<uint8_t, 4096> storage = {};
    NetAddress from;

    // A bounded number per call, so that one busy socket cannot starve the others.
    for (int count = 0; count < 256; ++count)
    {
        const size_t length = receiveFrom(m_socket, from, storage);

        if (length == 0)
        {
            break;
        }

        handleMainDatagram(from, std::span<const uint8_t>(storage.data(), length), nowMs);
    }

    for (RelaySlot &slot : m_relaySlots)
    {
        for (int count = 0; slot.inUse && count < 256; ++count)
        {
            const size_t length = receiveFrom(slot.socket, from, storage);

            if (length == 0)
            {
                break;
            }

            handleRelayDatagram(slot, from, std::span<const uint8_t>(storage.data(), length), nowMs);
        }
    }

    expire(nowMs);
}

bool RendezvousServer::hasCookie(const NetAddress &from, uint64_t cookie) const
{
    return cookie != 0
        && (cookie == addressCookie(m_cookieSecrets[0], from) || cookie == addressCookie(m_cookieSecrets[1], from));
}

void RendezvousServer::sendCookie(const NetAddress &to, uint32_t nonce)
{
    // Eighteen bytes, less than any request, and nothing is remembered: this answer is all that a request from
    // a forged address gets out of the service, and it counts against nobody's allowance.
    AddressCookieMessage message;
    message.nonce = nonce;
    message.cookie = addressCookie(m_cookieSecrets[0], to);
    sendFrom(m_socket, to, encode(message));
}

size_t RendezvousServer::sessionsOfAddress(uint32_t host) const
{
    return size_t(std::count_if(m_sessions.begin(), m_sessions.end(),
        [host](const Session &session) { return session.publicAddress.host == host; }));
}

bool RendezvousServer::mayLog(uint32_t nowMs)
{
    if (!m_config.verbose)
    {
        return false;
    }

    if (m_config.logLinesPerMinute == 0)
    {
        return true;
    }

    turnLogMinute(nowMs);

    if (m_logLinesThisMinute >= m_config.logLinesPerMinute)
    {
        ++m_logLinesLeftOut;
        return false;
    }

    ++m_logLinesThisMinute;
    return true;
}

void RendezvousServer::turnLogMinute(uint32_t nowMs)
{
    if (nowMs - m_logMinuteSinceMs < 60000)
    {
        return;
    }

    m_logMinuteSinceMs = nowMs;
    m_logLinesThisMinute = 0;

    if (m_logLinesLeftOut != 0)
    {
        std::printf("%llu lines were left out of the log: more happened than it takes in a minute\n",
            static_cast<unsigned long long>(m_logLinesLeftOut));
        m_logLinesLeftOut = 0;
        m_logLinesThisMinute = 1;
    }
}

void RendezvousServer::handleMainDatagram(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs)
{
    const std::optional<RendezvousMessage> type = peekRendezvousMessage(datagram);

    // Nobody is at a group or broadcast address, or at port 0: an answer there would go to a whole network.
    if (!type || !isUnicastAddress(from))
    {
        return;
    }

    // Every request shows first that its sender is at the address it names (the cookie, or a session's key from
    // the session's own address). Until then it gets the cookie in answer and nothing else: nothing is kept for
    // it and no allowance is counted, so a forged address costs the address's owner nothing.
    switch (*type)
    {
    case RendezvousMessage::HostRegister:
        handleHostRegister(from, datagram, nowMs);
        break;

    case RendezvousMessage::HostUnregister:
        handleHostUnregister(from, datagram, nowMs);
        break;

    case RendezvousMessage::ListRequest:
        handleListRequest(from, datagram, nowMs);
        break;

    case RendezvousMessage::JoinRequest:
        handleJoinRequest(from, datagram, nowMs);
        break;

    default:
        break;
    }
}

void RendezvousServer::handleHostUnregister(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs)
{
    HostUnregisterMessage message;

    if (!decode(datagram, message) || message.sessionKey == 0)
    {
        return;
    }

    // Only from where the session is: the key sent from elsewhere ends nothing.
    const Session *pSession = findSessionByKey(message.sessionKey);

    if (pSession == nullptr || pSession->publicAddress != from)
    {
        return;
    }

    if (mayLog(nowMs))
    {
        std::printf("session %s closed by its host\n", toString(pSession->code).c_str());
    }

    const uint64_t endedKey = pSession->sessionKey;
    std::erase_if(m_sessions, [endedKey](const Session &session) { return session.sessionKey == endedKey; });
}

void RendezvousServer::handleListRequest(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs)
{
    ListRequestMessage message;

    if (datagram.size() < ListRequestLength || !decode(datagram, message))
    {
        return;
    }

    if (!hasCookie(from, message.cookie))
    {
        sendCookie(from, message.nonce);
        return;
    }

    if (!allowRequest(from, nowMs))
    {
        ++m_stats.refusedRequests;
        return;
    }

    ListReplyMessage reply;
    reply.nonce = message.nonce;
    reply.offset = message.offset;
    size_t listed = 0;

    for (const Session &session : m_sessions)
    {
        if ((session.info.flags & SessionFlagListed) == 0)
        {
            continue;
        }

        if (listed >= message.offset && reply.entries.size() < MaxListEntriesPerReply)
        {
            reply.entries.push_back({session.code, session.info});
        }

        ++listed;
    }

    reply.total = uint16_t(std::min<size_t>(listed, 65535));
    sendFrom(m_socket, from, encode(reply));
}

void RendezvousServer::handleHostRegister(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs)
{
    HostRegisterMessage message;

    if (!decode(datagram, message))
    {
        return;
    }

    if (message.sessionKey != 0)
    {
        // A heartbeat. The key is the host's secret, so nobody else can rename or move its session. A key that
        // names no session gets no answer: the session lapsed, and the host registers anew once its heartbeats
        // stay unanswered.
        Session *pSession = findSessionByKey(message.sessionKey);

        if (pSession == nullptr)
        {
            return;
        }

        // Counted against the session and not against the address, so that whatever else comes from the
        // address, a host's heartbeats get through and its session does not lapse.
        if (m_config.requestsPerSecond != 0
            && !takeRequest(pSession->allowance, m_config.requestsPerSecond, m_config.requestBurst, nowMs))
        {
            ++m_stats.refusedRequests;
            return;
        }

        if (pSession->publicAddress != from)
        {
            // The host's address changed (its router gave it another), or somebody who has the key names an
            // address that is not his. The session moves only to an address that sent this address's cookie
            // back, and only while that address has room for a session more: else one real address could put
            // sessions wherever it liked, as many as the table holds.
            if (!hasCookie(from, message.cookie))
            {
                sendCookie(from, message.nonce);
                return;
            }

            if (pSession->publicAddress.host != from.host
                && sessionsOfAddress(from.host) >= m_config.maxSessionsPerAddress)
            {
                return;
            }
        }

        pSession->info = message.info;
        pSession->publicAddress = from;
        pSession->localAddress = localNetworkAddress(message.localAddress, from);
        pSession->lastSeenMs = nowMs;
        sendRegistered(*pSession, from, message.nonce);
        return;
    }

    // A first registration. Nothing is kept for an address that has not sent its cookie back: a session is a
    // host's from its first moment, never something a forged datagram left behind.
    if (!hasCookie(from, message.cookie))
    {
        sendCookie(from, message.nonce);
        return;
    }

    if (!allowRequest(from, nowMs))
    {
        ++m_stats.refusedRequests;
        return;
    }

    // The repeat of a registration whose answer was lost gets the same answer. It changes nothing of the session
    // and does not keep it alive: only the key does that. A registration from a session's address with another
    // number opens a session of its own; the first keeps its name and addresses.
    for (const Session &session : m_sessions)
    {
        if (session.publicAddress == from && session.registerNonce == message.nonce)
        {
            sendRegistered(session, from, message.nonce);
            return;
        }
    }

    if (m_sessions.size() >= m_config.maxSessions || sessionsOfAddress(from.host) >= m_config.maxSessionsPerAddress)
    {
        return;
    }

    Session session;

    do
    {
        session.sessionKey = randomNonZero();
    } while (findSessionByKey(session.sessionKey) != nullptr);

    do
    {
        session.code = makeSessionCode(randomValue());
    } while (findSession(session.code) != nullptr);

    session.registerNonce = message.nonce;
    session.info = message.info;
    session.publicAddress = from;
    session.localAddress = localNetworkAddress(message.localAddress, from);
    session.lastSeenMs = nowMs;
    session.allowance = RequestAllowance{float(m_config.requestBurst), nowMs};
    m_sessions.push_back(session);

    if (mayLog(nowMs))
    {
        std::printf("session %s opened by %s\n", toString(session.code).c_str(), toString(from).c_str());
    }

    sendRegistered(session, from, message.nonce);
}

void RendezvousServer::sendRegistered(const Session &session, const NetAddress &to, uint32_t nonce)
{
    HostRegisteredMessage reply;
    reply.nonce = nonce;
    reply.sessionKey = session.sessionKey;
    reply.code = session.code;
    reply.publicAddress = to;
    sendFrom(m_socket, to, encode(reply));
}

void RendezvousServer::handleJoinRequest(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs)
{
    JoinRequestMessage message;

    if (datagram.size() < JoinRequestLength || !decode(datagram, message))
    {
        return;
    }

    // A join request makes the service remember it, perhaps give out a relay port, and tell the host, who then
    // sends datagrams to the asker: none of it for an address that has not sent its cookie back.
    if (!hasCookie(from, message.cookie))
    {
        sendCookie(from, message.nonce);
        return;
    }

    if (!allowRequest(from, nowMs))
    {
        ++m_stats.refusedRequests;
        return;
    }

    JoinReplyMessage reply;
    reply.nonce = message.nonce;
    reply.clientPublicAddress = from;
    const Session *pSession = findSession(message.code);

    if (pSession == nullptr)
    {
        reply.status = JoinStatus::NoSuchSession;
        sendFrom(m_socket, from, encode(reply));
        return;
    }

    JoinRecord *pRecord = nullptr;

    for (JoinRecord &record : m_joins)
    {
        if (record.clientAddress == from && record.nonce == message.nonce)
        {
            pRecord = &record;
        }
    }

    if (pRecord == nullptr)
    {
        JoinRecord record;
        record.clientAddress = from;
        record.nonce = message.nonce;
        record.introId = m_nextIntroId++;
        record.createdMs = nowMs;

        if (message.wantRelay)
        {
            record.relaySlot = allocateRelaySlot(*pSession, from, record.introId, nowMs);

            if (record.relaySlot < 0)
            {
                reply.status = JoinStatus::RelayUnavailable;
                sendFrom(m_socket, from, encode(reply));
                return;
            }
        }

        // The oldest goes when there are too many; a relay port it held is taken back when nobody binds to it.
        if (m_joins.size() >= MaxJoinRecords)
        {
            m_joins.erase(m_joins.begin());
        }

        m_joins.push_back(record);
        pRecord = &m_joins.back();

        if (mayLog(nowMs))
        {
            std::printf("join %s by %s%s\n", toString(message.code).c_str(), toString(from).c_str(),
                message.wantRelay ? " through the relay" : "");
        }
    }

    PeerIntroMessage intro;
    intro.sessionKey = pSession->sessionKey;
    intro.introId = pRecord->introId;
    intro.clientPublicAddress = from;
    intro.clientLocalAddress = localNetworkAddress(message.localAddress, from);
    reply.hostPublicAddress = pSession->publicAddress;
    reply.hostLocalAddress = pSession->localAddress;

    // A relay slot given out earlier for this request may have been taken back since (nobody bound to it, or it
    // ran idle), and given to another request.
    if (pRecord->relaySlot >= 0 && m_relaySlots[size_t(pRecord->relaySlot)].inUse
        && m_relaySlots[size_t(pRecord->relaySlot)].introId == pRecord->introId)
    {
        const RelaySlot &slot = m_relaySlots[size_t(pRecord->relaySlot)];
        reply.relayPort = slot.port;
        reply.relayToken = slot.clientToken;
        intro.relayPort = slot.port;
        intro.relayToken = slot.hostToken;
    }

    sendFrom(m_socket, from, encode(reply));
    sendFrom(m_socket, pSession->publicAddress, encode(intro));
}

void RendezvousServer::handleRelayDatagram(
    RelaySlot &slot,
    const NetAddress &from,
    std::span<const uint8_t> datagram,
    uint32_t nowMs)
{
    if (peekRendezvousMessage(datagram) == RendezvousMessage::RelayBind)
    {
        RelayBindMessage message;

        if (!decode(datagram, message) || !isUnicastAddress(from))
        {
            return;
        }

        // Each side binds from the host its token was sent to, whatever the port (a router may give this port
        // another one than it gave the main port). A token alone, sent with anybody's address as its sender,
        // would make the port forward to somebody who never asked.
        if (message.token == slot.hostToken && from.host == slot.sessionHost)
        {
            slot.hostAddress = from;
        }
        else if (message.token == slot.clientToken && from.host == slot.requesterHost)
        {
            slot.clientAddress = from;
        }
        else
        {
            return;
        }

        slot.lastActivityMs = nowMs;
        sendFrom(slot.socket, from, encode(message, RendezvousMessage::RelayBound));
        return;
    }

    const NetAddress *pTo = nullptr;

    if (from == slot.hostAddress)
    {
        pTo = &slot.clientAddress;
    }
    else if (from == slot.clientAddress)
    {
        pTo = &slot.hostAddress;
    }

    // From neither side, or the other side has not bound yet.
    if (pTo == nullptr || !pTo->valid())
    {
        ++m_stats.droppedDatagrams;
        return;
    }

    if (nowMs - slot.budgetWindowMs >= 1000)
    {
        slot.budgetWindowMs = nowMs;
        slot.budgetBytes = 0;
    }

    slot.budgetBytes += uint32_t(datagram.size());
    const bool overBudget = m_config.relayBytesPerSecond != 0 && slot.budgetBytes > m_config.relayBytesPerSecond;
    const bool testDrop = m_config.relayDropPermille != 0 && m_random() % 1000 < m_config.relayDropPermille;

    if (overBudget || testDrop)
    {
        ++m_stats.droppedDatagrams;
        return;
    }

    slot.lastActivityMs = nowMs;
    ++m_stats.relayedDatagrams;
    m_stats.relayedBytes += datagram.size();
    slot.relayedBytes += datagram.size();
    sendFrom(slot.socket, *pTo, datagram);
}

bool RendezvousServer::allowRequest(const NetAddress &from, uint32_t nowMs)
{
    bool firstRefusal = false;
    const bool allowed = m_requestLimiter.allow(from.host, nowMs, firstRefusal);

    if (firstRefusal && mayLog(nowMs))
    {
        std::printf("%s asks too much: not answered until it slows down\n", toString(from).c_str());
    }

    return allowed;
}

void RendezvousServer::expire(uint32_t nowMs)
{
    std::erase_if(m_sessions, [&](const Session &session) {
        const bool expired = nowMs - session.lastSeenMs > m_config.sessionTimeoutMs;

        if (expired && mayLog(nowMs))
        {
            std::printf("session %s timed out\n", toString(session.code).c_str());
        }

        return expired;
    });
    std::erase_if(m_joins, [&](const JoinRecord &record) { return nowMs - record.createdMs > m_config.joinMemoryMs; });
    // An address not heard from for a minute has its full allowance again, and need not be remembered.
    m_requestLimiter.expire(nowMs, 60000);

    for (RelaySlot &slot : m_relaySlots)
    {
        if (!slot.inUse)
        {
            continue;
        }

        // A port one side never bound to carries nothing: it was asked for from a forged address, or its game
        // gave up. It is not kept from the others for the whole idle time.
        const bool bound = slot.hostAddress.valid() && slot.clientAddress.valid();
        const bool neverBound = !bound && nowMs - slot.startedMs > m_config.relayBindTimeoutMs;

        if (neverBound || nowMs - slot.lastActivityMs > m_config.relayIdleTimeoutMs)
        {
            releaseRelaySlot(slot, nowMs);
        }
    }

    // A new secret for the cookies; those made with the one before stay good until the next change.
    if (nowMs - m_cookieSecretSinceMs >= m_config.cookieLifetimeMs)
    {
        m_cookieSecrets[1] = m_cookieSecrets[0];
        m_cookieSecrets[0] = {randomValue(), randomValue()};
        m_cookieSecretSinceMs = nowMs;
    }

    // The line that says how much the log left out is not kept waiting for the next thing worth a line.
    turnLogMinute(nowMs);
}

RendezvousServer::Session *RendezvousServer::findSession(const SessionCode &code)
{
    for (Session &session : m_sessions)
    {
        if (session.code == code)
        {
            return &session;
        }
    }

    return nullptr;
}

RendezvousServer::Session *RendezvousServer::findSessionByKey(uint64_t sessionKey)
{
    for (Session &session : m_sessions)
    {
        if (session.sessionKey == sessionKey)
        {
            return &session;
        }
    }

    return nullptr;
}

int RendezvousServer::allocateRelaySlot(
    const Session &session,
    const NetAddress &requester,
    uint32_t introId,
    uint32_t nowMs)
{
    // A game on the service's own network or machine is relayed only with another such game, unless the service
    // is set up to stand between its network and the internet.
    if (!m_config.relayBetweenLanAndInternet
        && isOwnNetworkAddress(session.publicAddress) != isOwnNetworkAddress(requester))
    {
        return -1;
    }

    // The address's earlier ports that carry no game give way to this request: a game that asks again has given
    // the earlier request up (or lost its connection), and its port would otherwise stand in its own way.
    size_t ofAddress = 0;

    for (RelaySlot &slot : m_relaySlots)
    {
        if (!slot.inUse || slot.requesterHost != requester.host)
        {
            continue;
        }

        const bool bound = slot.hostAddress.valid() && slot.clientAddress.valid();

        if (bound && nowMs - slot.lastActivityMs <= RelayLiveMs)
        {
            ++ofAddress;
        }
        else
        {
            releaseRelaySlot(slot, nowMs);
        }
    }

    const size_t ofSession = size_t(std::count_if(m_relaySlots.begin(), m_relaySlots.end(),
        [&session](const RelaySlot &slot) { return slot.inUse && slot.sessionKey == session.sessionKey; }));

    if (ofSession >= m_config.maxRelaysPerSession || ofAddress >= m_config.maxRelaysPerAddress)
    {
        return -1;
    }

    for (size_t index = 0; index < m_relaySlots.size(); ++index)
    {
        RelaySlot &slot = m_relaySlots[index];

        if (slot.inUse)
        {
            continue;
        }

        // Whatever reached the port while it was free is thrown away unread.
        std::array<uint8_t, 4096> storage = {};
        NetAddress from;

        while (receiveFrom(slot.socket, from, storage) != 0)
        {
        }

        slot.inUse = true;
        slot.introId = introId;
        slot.sessionKey = session.sessionKey;
        slot.requesterHost = requester.host;
        slot.sessionHost = session.publicAddress.host;
        slot.hostToken = randomNonZero();

        // The token says which side a game is, so the two must differ.
        do
        {
            slot.clientToken = randomNonZero();
        } while (slot.clientToken == slot.hostToken);

        slot.hostAddress = {};
        slot.clientAddress = {};
        slot.lastActivityMs = nowMs;
        slot.budgetWindowMs = nowMs;
        slot.budgetBytes = 0;
        slot.relayedBytes = 0;
        slot.startedMs = nowMs;
        return int(index);
    }

    return -1;
}

void RendezvousServer::releaseRelaySlot(RelaySlot &slot, uint32_t nowMs)
{
    if (slot.relayedBytes != 0 && mayLog(nowMs))
    {
        std::printf("relay port %u freed: %llu bytes in %u s between %s and %s\n", slot.port,
            static_cast<unsigned long long>(slot.relayedBytes), (slot.lastActivityMs - slot.startedMs) / 1000,
            toString(slot.hostAddress).c_str(), toString(slot.clientAddress).c_str());
    }

    slot.inUse = false;
    slot.introId = 0;
    slot.sessionKey = 0;
    slot.requesterHost = 0;
    slot.sessionHost = 0;
    slot.hostToken = 0;
    slot.clientToken = 0;
    slot.hostAddress = {};
    slot.clientAddress = {};
}

void RendezvousServer::sendFrom(intptr_t socket, const NetAddress &to, std::span<const uint8_t> datagram)
{
    ENetAddress address = {};
    address.host = to.host;
    address.port = to.port;
    ENetBuffer buffer = {};
    buffer.data = const_cast<uint8_t *>(datagram.data());
    buffer.dataLength = datagram.size();
    enet_socket_send(enetSocket(socket), &address, &buffer, 1);
}

uint64_t RendezvousServer::randomValue()
{
    return (uint64_t(m_entropy()) << 32) | uint64_t(m_entropy());
}

uint64_t RendezvousServer::randomNonZero()
{
    uint64_t value = 0;

    while (value == 0)
    {
        value = randomValue();
    }

    return value;
}
}
