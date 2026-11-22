#pragma once

#include <cstdint>
#include <span>
#include <vector>

namespace OpenYAMM::Engine
{
// A connection as the transport names it. Valid from its Connected event to its Disconnected event; a later
// connection never gets the id of an earlier one.
using NetPeerId = uint32_t;

constexpr NetPeerId InvalidNetPeer = 0xFFFFFFFFu;

enum class NetDelivery : uint8_t
{
    // Arrives, in the order sent on its channel. For commands, results and state that must not be lost.
    Reliable,
    // May be lost; one that arrives after a newer one of its channel is dropped. For positions and snapshots.
    UnreliableNewest,
};

struct NetEvent
{
    enum class Type : uint8_t
    {
        Connected,
        Disconnected,
        Message,
    };

    Type type = Type::Message;
    NetPeerId peer = InvalidNetPeer;
    uint8_t channel = 0;
    std::vector<uint8_t> payload;
};

struct NetPeerStats
{
    uint32_t roundTripMs = 0;
    // The share of sent datagrams the transport counts as lost, in thousandths.
    uint32_t lossPermille = 0;
    // How much of its full send window the transport allows itself now, in hundredths (a transport that holds
    // back on a line it judges crowded sends big messages slower and drops newest-wins messages).
    uint32_t sendWindowPercent = 100;
};

// What the game needs from a network library (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "Transport,
// lobby and relay"): messages on channels, reliable or newest-wins, between a host and the games that joined it.
// LoopbackTransport joins two games in one process; EnetTransport carries the same over UDP.
class INetTransport
{
public:
    static constexpr uint8_t ChannelCount = 4;

    virtual ~INetTransport() = default;

    // Sends what is queued and receives what arrived, waiting up to `timeoutMs` when there is nothing to do.
    virtual void service(uint32_t timeoutMs) = 0;
    // The next event, oldest first. False when there is none.
    virtual bool pollEvent(NetEvent &event) = 0;
    virtual bool send(NetPeerId peer, uint8_t channel, NetDelivery delivery, std::span<const uint8_t> payload) = 0;
    virtual void disconnect(NetPeerId peer) = 0;
    virtual NetPeerStats peerStats(NetPeerId peer) const = 0;
};
}
