#include "engine/net/EnetTransport.h"

#include <enet/enet.h>

#include <atomic>
#include <chrono>
#include <cstdlib>

namespace OpenYAMM::Engine
{
namespace
{
// How long a connected peer may be silent before it counts as lost: at least the first, whatever the line; the
// second at most. A map load on a slow machine is the longest silence of a healthy peer.
constexpr uint32_t PeerSilenceMinimumMs = 45000;
constexpr uint32_t PeerSilenceMaximumMs = 120000;
// The longest a lost reliable packet waits before it is sent again. ENet doubles that wait at every loss of the
// same packet, without a limit, starting from its estimate of the round trip, and a game that was busy loading a
// map has stretched that estimate to seconds. A message of two hundred packets on a line that loses one in ten
// then stood for a minute and more. A line slower than this there and back gets packets sent twice, no worse.
constexpr uint32_t RetryWaitMaximumMs = 2000;

std::atomic<int> g_enetUsers = 0;

void acquireEnet()
{
    if (g_enetUsers.fetch_add(1) == 0)
    {
        enet_initialize();
    }
}

void releaseEnet()
{
    if (g_enetUsers.fetch_sub(1) == 1)
    {
        enet_deinitialize();
    }
}

// The transport being serviced on this thread: ENet's intercept callback has no user pointer of its own.
thread_local EnetTransport *t_pServicing = nullptr;
}

NetLibrary::NetLibrary()
{
    acquireEnet();
}

NetLibrary::~NetLibrary()
{
    releaseEnet();
}

uint32_t netNowMilliseconds()
{
    // A clock that only goes forward. ENet's own is the wall clock, and when that is set back everything timed by
    // it looks older than the 32 bits can tell: every session and relay port lapsed at once. The callers only
    // ever take the difference of two readings, so where the count starts does not matter.
    const std::chrono::steady_clock::duration sinceStart = std::chrono::steady_clock::now().time_since_epoch();
    return uint32_t(std::chrono::duration_cast<std::chrono::milliseconds>(sinceStart).count());
}

NetAddress localAddressTowards(const NetAddress &remote)
{
    NetAddress local;
    acquireEnet();
    const ENetSocket socket = enet_socket_create(ENET_SOCKET_TYPE_DATAGRAM);

    if (socket != ENET_SOCKET_NULL)
    {
        ENetAddress enetRemote = {};
        enetRemote.host = remote.host;
        enetRemote.port = remote.port;
        ENetAddress enetLocal = {};

        // Connecting a UDP socket sends nothing; it only makes the system pick the route and with it the local
        // address.
        if (enet_socket_connect(socket, &enetRemote) == 0 && enet_socket_get_address(socket, &enetLocal) == 0)
        {
            local.host = enetLocal.host;
        }

        enet_socket_destroy(socket);
    }

    releaseEnet();
    return local;
}

std::string toString(const NetAddress &address)
{
    ENetAddress enetAddress = {};
    enetAddress.host = address.host;
    enetAddress.port = address.port;
    char text[64] = {};

    if (enet_address_get_host_ip(&enetAddress, text, sizeof(text)) != 0)
    {
        return "?:" + std::to_string(address.port);
    }

    return std::string(text) + ":" + std::to_string(address.port);
}

std::optional<NetAddress> parseNetAddress(const std::string &text)
{
    const size_t colon = text.rfind(':');

    if (colon == std::string::npos || colon == 0 || colon + 1 >= text.size())
    {
        return std::nullopt;
    }

    const long port = std::strtol(text.c_str() + colon + 1, nullptr, 10);

    if (port <= 0 || port > 65535)
    {
        return std::nullopt;
    }

    acquireEnet();
    ENetAddress enetAddress = {};
    const bool resolved = enet_address_set_host(&enetAddress, text.substr(0, colon).c_str()) == 0;
    releaseEnet();

    if (!resolved)
    {
        return std::nullopt;
    }

    NetAddress address;
    address.host = enetAddress.host;
    address.port = uint16_t(port);
    return address;
}

EnetTransport::EnetTransport()
{
    acquireEnet();
}

EnetTransport::~EnetTransport()
{
    close();
    releaseEnet();
}

bool EnetTransport::open(uint16_t port, size_t maxPeers)
{
    close();
    ENetAddress address = {};
    address.host = ENET_HOST_ANY;
    address.port = port;
    m_pHost = enet_host_create(&address, maxPeers, ChannelCount, 0, 0);

    if (m_pHost == nullptr)
    {
        return false;
    }

    m_slotGenerations.assign(m_pHost->peerCount, 0);
    m_pHost->intercept = &EnetTransport::intercept;
    return true;
}

void EnetTransport::close()
{
    if (m_pHost != nullptr)
    {
        // A goodbye for every peer, sent at once: the other side then learns of the end now and not by a timeout.
        for (size_t slot = 0; slot < m_pHost->peerCount; ++slot)
        {
            if (m_pHost->peers[slot].state == ENET_PEER_STATE_CONNECTED)
            {
                enet_peer_disconnect_now(&m_pHost->peers[slot], 0);
            }
        }

        enet_host_flush(m_pHost);
        enet_host_destroy(m_pHost);
        m_pHost = nullptr;
    }

    m_slotGenerations.clear();
    m_events.clear();
}

bool EnetTransport::isOpen() const
{
    return m_pHost != nullptr;
}

NetPeerId EnetTransport::peerIdOfSlot(size_t slot) const
{
    return (NetPeerId(m_slotGenerations[slot]) << 16) | NetPeerId(slot);
}

bool EnetTransport::slotOfPeer(NetPeerId peer, size_t &slot) const
{
    slot = peer & 0xFFFFu;
    return m_pHost != nullptr && slot < m_pHost->peerCount && peerIdOfSlot(slot) == peer;
}

NetPeerId EnetTransport::connect(const NetAddress &address)
{
    if (m_pHost == nullptr)
    {
        return InvalidNetPeer;
    }

    ENetAddress enetAddress = {};
    enetAddress.host = address.host;
    enetAddress.port = address.port;
    const ENetPeer *pPeer = enet_host_connect(m_pHost, &enetAddress, ChannelCount, 0);
    return pPeer != nullptr ? peerIdOfSlot(size_t(pPeer - m_pHost->peers)) : InvalidNetPeer;
}

uint16_t EnetTransport::localPort() const
{
    ENetAddress address = {};

    if (m_pHost == nullptr || enet_socket_get_address(m_pHost->socket, &address) != 0)
    {
        return 0;
    }

    return address.port;
}

NetAddress EnetTransport::peerAddress(NetPeerId peer) const
{
    NetAddress address;
    size_t slot = 0;

    if (m_pHost != nullptr && slotOfPeer(peer, slot))
    {
        address.host = m_pHost->peers[slot].address.host;
        address.port = m_pHost->peers[slot].address.port;
    }

    return address;
}

void EnetTransport::sendDatagram(const NetAddress &to, std::span<const uint8_t> datagram)
{
    if (m_pHost == nullptr)
    {
        return;
    }

    ENetAddress address = {};
    address.host = to.host;
    address.port = to.port;
    ENetBuffer buffer = {};
    buffer.data = const_cast<uint8_t *>(datagram.data());
    buffer.dataLength = datagram.size();
    enet_socket_send(m_pHost->socket, &address, &buffer, 1);
}

void EnetTransport::setDatagramHandler(DatagramHandler handler)
{
    m_datagramHandler = std::move(handler);
}

int EnetTransport::intercept(_ENetHost *pHost, _ENetEvent *)
{
    EnetTransport *pTransport = t_pServicing;

    if (pTransport == nullptr || pTransport->m_pHost != pHost || !pTransport->m_datagramHandler)
    {
        return 0;
    }

    NetAddress from;
    from.host = pHost->receivedAddress.host;
    from.port = pHost->receivedAddress.port;
    const std::span<const uint8_t> datagram(pHost->receivedData, pHost->receivedDataLength);
    return pTransport->m_datagramHandler(from, datagram) ? 1 : 0;
}

void EnetTransport::service(uint32_t timeoutMs)
{
    if (m_pHost == nullptr)
    {
        return;
    }

    t_pServicing = this;
    ENetEvent enetEvent = {};
    int result = enet_host_service(m_pHost, &enetEvent, timeoutMs);

    while (result > 0)
    {
        queueEvent(enetEvent);
        result = enet_host_service(m_pHost, &enetEvent, 0);
    }

    t_pServicing = nullptr;

    for (size_t slot = 0; slot < m_pHost->peerCount; ++slot)
    {
        ENetPeer &peer = m_pHost->peers[slot];

        if (peer.state != ENET_PEER_STATE_CONNECTED)
        {
            continue;
        }

        bool shortened = false;

        for (ENetListIterator position = enet_list_begin(&peer.sentReliableCommands);
             position != enet_list_end(&peer.sentReliableCommands); position = enet_list_next(position))
        {
            ENetOutgoingCommand *pCommand = reinterpret_cast<ENetOutgoingCommand *>(position);

            if (pCommand->roundTripTimeout > RetryWaitMaximumMs)
            {
                pCommand->roundTripTimeout = RetryWaitMaximumMs;
                shortened = true;
            }
        }

        // The peer's next look at its waiting packets was set by the longer wait.
        if (shortened)
        {
            peer.nextTimeout = m_pHost->serviceTime;
        }
    }
}

void EnetTransport::queueEvent(const _ENetEvent &enetEvent)
{
    const size_t slot = size_t(enetEvent.peer - m_pHost->peers);
    NetEvent event;
    event.peer = peerIdOfSlot(slot);

    switch (enetEvent.type)
    {
    case ENET_EVENT_TYPE_CONNECT:
        // A game that loads a map answers nothing for as long as the load takes. ENet's own limits give a peer up
        // after five seconds of that on a quick line, where its retry interval is short.
        enet_peer_timeout(enetEvent.peer, 0, PeerSilenceMinimumMs, PeerSilenceMaximumMs);
        event.type = NetEvent::Type::Connected;
        break;

    case ENET_EVENT_TYPE_DISCONNECT:
        event.type = NetEvent::Type::Disconnected;
        // Whoever takes the slot next is another peer.
        ++m_slotGenerations[slot];
        break;

    case ENET_EVENT_TYPE_RECEIVE:
        event.type = NetEvent::Type::Message;
        event.channel = enetEvent.channelID;
        event.payload.assign(enetEvent.packet->data, enetEvent.packet->data + enetEvent.packet->dataLength);
        enet_packet_destroy(enetEvent.packet);
        break;

    default:
        return;
    }

    m_events.push_back(std::move(event));
}

bool EnetTransport::pollEvent(NetEvent &event)
{
    if (m_events.empty())
    {
        return false;
    }

    event = std::move(m_events.front());
    m_events.pop_front();
    return true;
}

bool EnetTransport::send(NetPeerId peer, uint8_t channel, NetDelivery delivery, std::span<const uint8_t> payload)
{
    size_t slot = 0;

    if (!slotOfPeer(peer, slot) || channel >= ChannelCount)
    {
        return false;
    }

    // Without the reliable flag ENet sends unreliably and drops what arrives behind a newer packet of the channel.
    const enet_uint32 flags = delivery == NetDelivery::Reliable ? enet_uint32(ENET_PACKET_FLAG_RELIABLE) : 0u;
    ENetPacket *pPacket = enet_packet_create(payload.data(), payload.size(), flags);

    if (pPacket == nullptr)
    {
        return false;
    }

    if (enet_peer_send(&m_pHost->peers[slot], channel, pPacket) != 0)
    {
        enet_packet_destroy(pPacket);
        return false;
    }

    return true;
}

void EnetTransport::disconnect(NetPeerId peer)
{
    size_t slot = 0;

    if (!slotOfPeer(peer, slot))
    {
        return;
    }

    ENetPeer &enetPeer = m_pHost->peers[slot];
    const bool wasFree = enetPeer.state == ENET_PEER_STATE_DISCONNECTED;
    // After what is queued for the peer has gone out: a refusal's reason, a leaving game's last word.
    enet_peer_disconnect_later(&enetPeer, 0);

    // A connection that was still being made is ended by ENet on the spot, its slot free again, and no event
    // follows. The owner was given the peer's id by connect() and is owed its Disconnected event; and whoever takes
    // the slot next is another peer.
    if (!wasFree && enetPeer.state == ENET_PEER_STATE_DISCONNECTED)
    {
        NetEvent event;
        event.type = NetEvent::Type::Disconnected;
        event.peer = peer;
        ++m_slotGenerations[slot];
        m_events.push_back(std::move(event));
    }
}

NetPeerStats EnetTransport::peerStats(NetPeerId peer) const
{
    NetPeerStats stats;
    size_t slot = 0;

    if (slotOfPeer(peer, slot))
    {
        const ENetPeer &enetPeer = m_pHost->peers[slot];
        stats.roundTripMs = enetPeer.roundTripTime;
        stats.lossPermille = uint32_t(uint64_t(enetPeer.packetLoss) * 1000 / ENET_PEER_PACKET_LOSS_SCALE);
        stats.sendWindowPercent = enetPeer.packetThrottle * 100 / ENET_PEER_PACKET_THROTTLE_SCALE;
    }

    return stats;
}
}
