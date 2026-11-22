#pragma once

#include "engine/net/NetAddress.h"
#include "engine/net/NetTransport.h"

#include <cstddef>
#include <deque>
#include <functional>

struct _ENetHost;
struct _ENetEvent;

namespace OpenYAMM::Engine
{
// The transport over ENet 1.3.18 (tools/net_spike, the spike that chose it): one UDP socket for a game, whether it
// hosts or joins. No encryption and IPv4 only; both are left for the step that takes sessions beyond one machine
// and a LAN.
class EnetTransport : public INetTransport
{
public:
    EnetTransport();
    ~EnetTransport() override;

    EnetTransport(const EnetTransport &) = delete;
    EnetTransport &operator=(const EnetTransport &) = delete;

    // Binds the socket. Port 0 lets the system pick one.
    bool open(uint16_t port, size_t maxPeers);
    void close();
    bool isOpen() const;

    // Starts a connection; its Connected or Disconnected event follows.
    NetPeerId connect(const NetAddress &address);
    uint16_t localPort() const;
    // Where a peer is, as the socket sees it (a relay's port for a relayed peer).
    NetAddress peerAddress(NetPeerId peer) const;
    // A datagram of its own on the connection's socket, beside the connection's traffic: the lobby's datagrams go
    // this way, so that the address a router gives this socket is the one the other games are told.
    void sendDatagram(const NetAddress &to, std::span<const uint8_t> datagram);
    // Every arriving datagram is shown to the handler before the connection sees it; one it takes (true) is not the
    // connection's.
    using DatagramHandler = std::function<bool(const NetAddress &from, std::span<const uint8_t> datagram)>;
    void setDatagramHandler(DatagramHandler handler);

    void service(uint32_t timeoutMs) override;
    bool pollEvent(NetEvent &event) override;
    bool send(NetPeerId peer, uint8_t channel, NetDelivery delivery, std::span<const uint8_t> payload) override;
    void disconnect(NetPeerId peer) override;
    NetPeerStats peerStats(NetPeerId peer) const override;

private:
    // ENet names a peer by its slot in the host's table and uses a slot again; the id carries the slot's generation
    // too, so that nothing sent to an old connection reaches a new one in its slot.
    static int intercept(_ENetHost *pHost, _ENetEvent *pEvent);
    NetPeerId peerIdOfSlot(size_t slot) const;
    // The slot of a peer that is still the one the id names; none otherwise.
    bool slotOfPeer(NetPeerId peer, size_t &slot) const;
    void queueEvent(const _ENetEvent &enetEvent);

    _ENetHost *m_pHost = nullptr;
    std::vector<uint16_t> m_slotGenerations;
    std::deque<NetEvent> m_events;
    DatagramHandler m_datagramHandler;
};
}
