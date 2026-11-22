#include "engine/net/RendezvousClient.h"

#include <algorithm>

namespace OpenYAMM::Engine
{
namespace
{
constexpr uint32_t RegisterRetryMs = 500;
constexpr uint32_t HeartbeatMs = 5000;
// Three heartbeats without an answer.
constexpr uint32_t HeartbeatLostMs = 16000;
constexpr uint32_t ServerRetryMs = 300;
constexpr uint32_t ServerTimeoutMs = 5000;
constexpr uint32_t PunchIntervalMs = 100;
constexpr uint32_t PunchTimeoutMs = 2500;
constexpr uint32_t HostPunchMs = 5000;
constexpr uint32_t RelayBindIntervalMs = 200;
constexpr uint32_t RelayBindTimeoutMs = 5000;
constexpr size_t MaxHostPunches = 64;
// How many joining games a host sends punches towards at a time: at one public address (the games of one household
// behind its router; a session has three guests at the most), and in all. A join request's sender address can be
// forged, and every one the host believes costs somebody fifty datagrams.
constexpr size_t MaxPunchedPerAddress = 3;
constexpr size_t MaxPunchTargets = 12;
// A joining game sends ten punches a second to each of the host's two addresses.
constexpr uint32_t MaxPunchAnswersPerSecond = 20;
}

const char *toString(JoinPath path)
{
    switch (path)
    {
    case JoinPath::Lan:
        return "lan";

    case JoinPath::Direct:
        return "direct";

    case JoinPath::Relay:
        return "relay";

    default:
        return "none";
    }
}

const char *toString(JoinFailure failure)
{
    switch (failure)
    {
    case JoinFailure::ServerSilent:
        return "the rendezvous server does not answer";

    case JoinFailure::NoSuchSession:
        return "no session has this code";

    case JoinFailure::RelayUnavailable:
        return "no direct path opened and the relay has no free port";

    case JoinFailure::RelaySilent:
        return "the relay does not answer";

    default:
        return "none";
    }
}

RendezvousClient::RendezvousClient(SendFunction send, const NetAddress &server)
    : m_send(std::move(send))
    , m_server(server)
{
}

void RendezvousClient::send(const NetAddress &to, const std::vector<uint8_t> &datagram)
{
    if (to.valid())
    {
        m_send(to, datagram);
    }
}

void RendezvousClient::startHosting(const SessionInfo &info, const NetAddress &localAddress)
{
    m_hosting = true;
    m_sessionInfo = info;
    m_hostLocalAddress = localAddress;
    m_registerNonce = m_random();
    m_sessionKey = 0;
    m_registerSentOnce = false;
}

void RendezvousClient::updateSessionInfo(const SessionInfo &info)
{
    m_sessionInfo = info;
}

void RendezvousClient::stopHosting()
{
    if (m_hosting && m_sessionKey != 0)
    {
        HostUnregisterMessage message;
        message.sessionKey = m_sessionKey;
        send(m_server, encode(message));
    }

    m_hosting = false;
    m_sessionKey = 0;
    m_hostPunches.clear();
}

bool RendezvousClient::registered() const
{
    return m_hosting && m_sessionKey != 0;
}

std::string RendezvousClient::sessionCode() const
{
    return registered() ? toString(m_sessionCode) : std::string();
}

NetAddress RendezvousClient::publicAddress() const
{
    return m_publicAddress;
}

void RendezvousClient::setAnswerPunches(bool answer)
{
    m_answerPunches = answer;
}

void RendezvousClient::requestList()
{
    m_listNonce = m_random();
    m_sessionList.reset();
    m_listPending = true;
    sendListRequest();
}

void RendezvousClient::sendListRequest()
{
    ListRequestMessage message;
    message.nonce = m_listNonce;
    message.cookie = m_cookie;
    send(m_server, encode(message));
}

const std::optional<std::vector<SessionListEntry>> &RendezvousClient::sessionList() const
{
    return m_sessionList;
}

void RendezvousClient::startJoin(const SessionCode &code, const NetAddress &localAddress, bool relayOnly)
{
    m_joinCode = code;
    m_joinLocalAddress = localAddress;
    m_joinRelayOnly = relayOnly;
    m_joinPath = JoinPath::None;
    m_joinFailure = JoinFailure::None;
    m_joinAddress = {};
    m_joinNonce = m_random();
    m_joinState = relayOnly ? JoinState::AskingForRelay : JoinState::AskingServer;
    m_joinStateFresh = true;
}

JoinState RendezvousClient::joinState() const
{
    return m_joinState;
}

JoinPath RendezvousClient::joinPath() const
{
    return m_joinPath;
}

JoinFailure RendezvousClient::joinFailure() const
{
    return m_joinFailure;
}

NetAddress RendezvousClient::joinAddress() const
{
    return m_joinAddress;
}

bool RendezvousClient::isRelayAddress(const NetAddress &address) const
{
    if (address.host != m_server.host)
    {
        return false;
    }

    if (m_joinPath == JoinPath::Relay && address == m_joinAddress)
    {
        return true;
    }

    return std::any_of(m_hostPunches.begin(), m_hostPunches.end(), [&](const HostPunch &punch) {
        return punch.relayPort != 0 && punch.relayPort == address.port;
    });
}

void RendezvousClient::sendJoinRequest(uint32_t nowMs)
{
    JoinRequestMessage message;
    message.nonce = m_joinNonce;
    message.code = m_joinCode;
    message.localAddress = m_joinLocalAddress;
    message.wantRelay = m_joinState == JoinState::AskingForRelay;
    message.cookie = m_cookie;
    send(m_server, encode(message));
    m_joinLastSentMs = nowMs;
}

void RendezvousClient::failJoin(JoinFailure failure)
{
    m_joinState = JoinState::Failed;
    m_joinFailure = failure;
}

void RendezvousClient::update(uint32_t nowMs)
{
    if (m_hosting)
    {
        // A server that no longer answers the heartbeats has lost the session (it was restarted, or the session
        // lapsed while the line was down): it is registered anew, under a new code.
        if (m_sessionKey != 0 && nowMs - m_lastRegisteredMs >= HeartbeatLostMs)
        {
            m_sessionKey = 0;
            m_sessionCode = {};
            m_registerNonce = m_random();
            m_registerSentOnce = false;
        }

        const uint32_t interval = m_sessionKey == 0 ? RegisterRetryMs : HeartbeatMs;

        if (!m_registerSentOnce || nowMs - m_lastRegisterMs >= interval)
        {
            HostRegisterMessage message;
            message.nonce = m_registerNonce;
            message.sessionKey = m_sessionKey;
            message.cookie = m_cookie;
            message.localAddress = m_hostLocalAddress;
            message.info = m_sessionInfo;
            send(m_server, encode(message));
            m_lastRegisterMs = nowMs;
            m_registerSentOnce = true;
        }

        for (HostPunch &punch : m_hostPunches)
        {
            if (nowMs - punch.lastSentMs < PunchIntervalMs)
            {
                continue;
            }

            punch.lastSentMs = nowMs;

            if (nowMs - punch.startedMs > HostPunchMs)
            {
                continue;
            }

            // A game that asked for a relay port gave up on a direct path, or never wanted one: it gets no punches,
            // only this side's binding to the port, which goes to the server and nowhere else.
            if (punch.relayPort != 0)
            {
                if (!punch.relayBound)
                {
                    RelayBindMessage bind;
                    bind.token = punch.relayToken;
                    send({m_server.host, punch.relayPort}, encode(bind, RendezvousMessage::RelayBind));
                }

                continue;
            }

            // Sent whether or not punches are answered: this is what opens the host's own router.
            PunchMessage message;
            message.id = punch.introId;
            send(punch.publicAddress, encode(message));

            if (punch.localAddress != punch.publicAddress)
            {
                send(punch.localAddress, encode(message));
            }
        }

        // A relay port that was bound stays in the list after its time, so that isRelayAddress can answer for its
        // peer. The list is bounded: the oldest entries go first.
        std::erase_if(m_hostPunches, [&](const HostPunch &punch) {
            return (punch.relayPort == 0 || !punch.relayBound) && nowMs - punch.startedMs > HostPunchMs;
        });

        if (m_hostPunches.size() > MaxHostPunches)
        {
            m_hostPunches.erase(m_hostPunches.begin(), m_hostPunches.end() - ptrdiff_t(MaxHostPunches));
        }
    }

    if (m_joinState == JoinState::Idle || m_joinState == JoinState::Ready || m_joinState == JoinState::Failed)
    {
        return;
    }

    if (m_joinStateFresh)
    {
        m_joinStateFresh = false;
        m_joinStateStartedMs = nowMs;
        m_joinLastSentMs = nowMs - 100000;
    }

    const uint32_t elapsedMs = nowMs - m_joinStateStartedMs;

    switch (m_joinState)
    {
    case JoinState::AskingServer:
    case JoinState::AskingForRelay:
        if (elapsedMs > ServerTimeoutMs)
        {
            failJoin(JoinFailure::ServerSilent);
        }
        else if (nowMs - m_joinLastSentMs >= ServerRetryMs)
        {
            sendJoinRequest(nowMs);
        }

        break;

    case JoinState::OpeningPath:
        if (elapsedMs > PunchTimeoutMs)
        {
            // No direct path: ask again, this time for a relay port. A new nonce makes it a new request.
            m_joinNonce = m_random();
            m_joinState = JoinState::AskingForRelay;
            m_joinStateFresh = true;
        }
        else if (nowMs - m_joinLastSentMs >= PunchIntervalMs)
        {
            PunchMessage message;
            message.id = m_joinNonce;
            send(m_joinReply.hostPublicAddress, encode(message));

            if (m_joinReply.hostLocalAddress != m_joinReply.hostPublicAddress)
            {
                send(m_joinReply.hostLocalAddress, encode(message));
            }

            m_joinLastSentMs = nowMs;
        }

        break;

    case JoinState::BindingRelay:
        if (elapsedMs > RelayBindTimeoutMs)
        {
            failJoin(JoinFailure::RelaySilent);
        }
        else if (nowMs - m_joinLastSentMs >= RelayBindIntervalMs)
        {
            RelayBindMessage bind;
            bind.token = m_joinReply.relayToken;
            send(m_joinAddress, encode(bind, RendezvousMessage::RelayBind));
            m_joinLastSentMs = nowMs;
        }

        break;

    default:
        break;
    }
}

bool RendezvousClient::handleDatagram(const NetAddress &from, std::span<const uint8_t> datagram, uint32_t nowMs)
{
    const std::optional<RendezvousMessage> type = peekRendezvousMessage(datagram);

    if (!type)
    {
        return false;
    }

    switch (*type)
    {
    case RendezvousMessage::AddressCookie:
    {
        AddressCookieMessage message;

        // The same cookie again changes nothing: it answers an earlier repeat of the request.
        if (!(from == m_server) || !decode(datagram, message) || message.cookie == 0 || message.cookie == m_cookie)
        {
            break;
        }

        const bool forRegistration = m_hosting && message.nonce == m_registerNonce;
        const bool forList = m_listPending && message.nonce == m_listNonce;
        const bool forJoin = (m_joinState == JoinState::AskingServer || m_joinState == JoinState::AskingForRelay)
            && message.nonce == m_joinNonce;

        if (!forRegistration && !forList && !forJoin)
        {
            break;
        }

        // The server did nothing for the request yet: it is said again at once, with the cookie.
        m_cookie = message.cookie;

        if (forRegistration)
        {
            m_registerSentOnce = false;
        }

        if (forJoin)
        {
            m_joinLastSentMs = nowMs - ServerRetryMs;
        }

        if (forList)
        {
            sendListRequest();
        }

        break;
    }

    case RendezvousMessage::HostRegistered:
    {
        HostRegisteredMessage message;

        if (m_hosting && from == m_server && decode(datagram, message) && message.nonce == m_registerNonce)
        {
            m_sessionKey = message.sessionKey;
            m_sessionCode = message.code;
            m_publicAddress = message.publicAddress;
            m_lastRegisteredMs = nowMs;
        }

        break;
    }

    case RendezvousMessage::ListReply:
    {
        ListReplyMessage message;

        if (from == m_server && decode(datagram, message) && message.nonce == m_listNonce)
        {
            m_sessionList = std::move(message.entries);
            m_listPending = false;
        }

        break;
    }

    case RendezvousMessage::PeerIntro:
    {
        PeerIntroMessage message;

        if (!m_hosting || !(from == m_server) || !decode(datagram, message))
        {
            break;
        }

        // An introduction makes this game send datagrams to the addresses in it, and the server's address as a
        // datagram's sender can be forged. The session's key cannot: only the server and this game have it.
        if (m_sessionKey == 0 || message.sessionKey != m_sessionKey || !isUnicastAddress(message.clientPublicAddress))
        {
            break;
        }

        // The server repeats an introduction with every repeat of the join request.
        const bool known = std::any_of(m_hostPunches.begin(), m_hostPunches.end(), [&](const HostPunch &punch) {
            return punch.introId == message.introId;
        });
        // The address the game gave for its own network, when it is such an address (the server filters it the
        // same way; a game does not rely on that).
        const NetAddress localAddress =
            localNetworkAddress(message.clientLocalAddress, message.clientPublicAddress);
        const bool hasLocal = localAddress.valid() && localAddress != message.clientPublicAddress;

        // Only so many addresses are punched at a time, and an address only so often, the games' own-network
        // addresses counted like their public ones. An introduction over that is left out; the server repeats
        // it while the game still asks, and a game that gets no punches joins through the relay.
        size_t targets = 0;
        size_t atPublicHost = 0;
        size_t atLocalHost = 0;
        const auto count = [&](const NetAddress &target)
        {
            ++targets;
            atPublicHost += target.host == message.clientPublicAddress.host ? 1 : 0;
            atLocalHost += hasLocal && target.host == localAddress.host ? 1 : 0;
        };

        for (const HostPunch &punch : m_hostPunches)
        {
            if (punch.relayPort != 0 || nowMs - punch.startedMs > HostPunchMs)
            {
                continue;
            }

            count(punch.publicAddress);

            if (punch.localAddress.valid() && punch.localAddress != punch.publicAddress)
            {
                count(punch.localAddress);
            }
        }

        const bool overLimit = message.relayPort == 0
            && (targets + (hasLocal ? 2 : 1) > MaxPunchTargets || atPublicHost >= MaxPunchedPerAddress
                || atLocalHost >= MaxPunchedPerAddress);

        if (!known && !overLimit)
        {
            HostPunch punch;
            punch.introId = message.introId;
            punch.publicAddress = message.clientPublicAddress;
            punch.localAddress = localAddress;
            punch.relayPort = message.relayPort;
            punch.relayToken = message.relayToken;
            punch.startedMs = nowMs;
            punch.lastSentMs = nowMs - PunchIntervalMs;
            punch.answersSinceMs = nowMs;
            m_hostPunches.push_back(punch);
        }

        break;
    }

    case RendezvousMessage::JoinReply:
    {
        JoinReplyMessage message;
        const bool waiting = m_joinState == JoinState::AskingServer || m_joinState == JoinState::AskingForRelay;

        if (!waiting || !(from == m_server) || !decode(datagram, message) || message.nonce != m_joinNonce)
        {
            break;
        }

        // This game sends punches to the host's own-network address: only when it is such an address (the
        // server filters it the same way; a game does not rely on that).
        message.hostLocalAddress = localNetworkAddress(message.hostLocalAddress, message.hostPublicAddress);

        if (message.status == JoinStatus::NoSuchSession)
        {
            failJoin(JoinFailure::NoSuchSession);
        }
        else if (message.status == JoinStatus::RelayUnavailable)
        {
            failJoin(JoinFailure::RelayUnavailable);
        }
        else if (m_joinState == JoinState::AskingServer)
        {
            m_joinReply = message;
            m_joinState = JoinState::OpeningPath;
            m_joinStateFresh = true;
        }
        else if (message.relayPort != 0)
        {
            m_joinReply = message;
            m_joinAddress = {m_server.host, message.relayPort};
            m_joinState = JoinState::BindingRelay;
            m_joinStateFresh = true;
        }

        break;
    }

    case RendezvousMessage::Punch:
    {
        PunchMessage message;

        if (!decode(datagram, message))
        {
            break;
        }

        if (!message.isAck)
        {
            if (!m_hosting || !m_answerPunches)
            {
                break;
            }

            // Answered are the games the server introduced, while their punches last, and so many times a
            // second: a punch from anywhere else (its sender address may be forged) gets nothing sent anywhere.
            // The port may be another than the server saw, the host must be the game's.
            for (HostPunch &punch : m_hostPunches)
            {
                const bool introduced = punch.relayPort == 0 && nowMs - punch.startedMs <= HostPunchMs
                    && (from.host == punch.publicAddress.host
                        || (punch.localAddress.valid() && from.host == punch.localAddress.host));

                if (!introduced)
                {
                    continue;
                }

                if (nowMs - punch.answersSinceMs >= 1000)
                {
                    punch.answersSinceMs = nowMs;
                    punch.answers = 0;
                }

                if (punch.answers < MaxPunchAnswersPerSecond)
                {
                    ++punch.answers;
                    PunchMessage ack;
                    ack.id = message.id;
                    ack.isAck = true;
                    send(from, encode(ack));
                }

                break;
            }

            break;
        }

        // Only the host the server named may answer: its address on its own network, or its public address. Of
        // the public one the port may differ from what the server reported, when the host's router gives every
        // destination its own port. An answer from anywhere else is not the host's, whatever number it carries.
        const bool fromNamedHost = from == m_joinReply.hostLocalAddress
            || (from.host == m_joinReply.hostPublicAddress.host && m_joinReply.hostPublicAddress.valid());

        // The first address the host answers from is the path. It is the sender's address as it arrived.
        if (m_joinState == JoinState::OpeningPath && message.id == m_joinNonce && fromNamedHost)
        {
            const bool lan = from == m_joinReply.hostLocalAddress
                && m_joinReply.hostLocalAddress != m_joinReply.hostPublicAddress;
            m_joinAddress = from;
            m_joinPath = lan ? JoinPath::Lan : JoinPath::Direct;
            m_joinState = JoinState::Ready;
        }

        break;
    }

    case RendezvousMessage::RelayBound:
    {
        RelayBindMessage message;

        if (!decode(datagram, message))
        {
            break;
        }

        if (m_joinState == JoinState::BindingRelay && from == m_joinAddress
            && message.token == m_joinReply.relayToken)
        {
            m_joinPath = JoinPath::Relay;
            m_joinState = JoinState::Ready;
        }

        for (HostPunch &punch : m_hostPunches)
        {
            if (punch.relayPort == from.port && from.host == m_server.host && punch.relayToken == message.token)
            {
                punch.relayBound = true;
            }
        }

        break;
    }

    default:
        break;
    }

    return true;
}
}
