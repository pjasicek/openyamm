#pragma once

#include "engine/net/NetTransport.h"

#include <array>
#include <deque>
#include <memory>
#include <random>

namespace OpenYAMM::Engine
{
// A bad line, for tests. What an end sends arrives late: `delayMs` and up to `jitterMs` more, by the end's own clock
// (advanceClock). A Reliable message still arrives, in the order sent on its channel, as on a real connection. An
// UnreliableNewest one is lost `lossPermille` times in a thousand, and one that a newer one of its channel overtook
// is dropped. The same seed gives the same line.
struct NetFaults
{
    uint32_t delayMs = 0;
    uint32_t jitterMs = 0;
    uint32_t lossPermille = 0;
    uint32_t seed = 1;

    bool any() const
    {
        return delayMs != 0 || jitterMs != 0 || lossPermille != 0;
    }
};

// Two games in one process: what one end sends, the other end receives at its next service(), as the same bytes a
// socket would carry. A hub is the host's end; every end made from it is a game that joined.
class LoopbackTransport : public INetTransport
{
public:
    LoopbackTransport();
    ~LoopbackTransport() override;

    LoopbackTransport(const LoopbackTransport &) = delete;
    LoopbackTransport &operator=(const LoopbackTransport &) = delete;

    // Joins `client` to this transport as its host. The Connected events follow at each side's next service().
    void accept(LoopbackTransport &client);
    // Makes the line bad for what this end sends from now on (both ends set it for a line bad both ways).
    void setFaults(const NetFaults &faults);
    // Moves this end's clock, which times what it sends over a bad line. Without faults nothing needs it.
    void advanceClock(float seconds);
    // What this end sent over a bad line: how many messages, and how many of them were lost or overtaken.
    uint32_t sentCount() const;
    uint32_t droppedCount() const;

    void service(uint32_t timeoutMs) override;
    bool pollEvent(NetEvent &event) override;
    bool send(NetPeerId peer, uint8_t channel, NetDelivery delivery, std::span<const uint8_t> payload) override;
    void disconnect(NetPeerId peer) override;
    NetPeerStats peerStats(NetPeerId peer) const override;

private:
    struct Link
    {
        LoopbackTransport *pRemote = nullptr;
        // The id the remote end knows this end by.
        NetPeerId remotePeer = InvalidNetPeer;
        bool open = false;
        // Asked to disconnect while its messages were still under way: it closes when they have arrived.
        bool closing = false;
    };

    // A message on its way over a bad line.
    struct InFlight
    {
        double arrivalSeconds = 0.0;
        // Counts what this end sent, so that messages due at the same moment keep their order.
        uint64_t sequence = 0;
        size_t link = 0;
        NetDelivery delivery = NetDelivery::Reliable;
        NetEvent event;
    };

    void dropLinkTo(const LoopbackTransport *pRemote);
    void closeLink(NetPeerId peer);
    void deliverDue();

    std::vector<Link> m_links;
    NetFaults m_faults;
    std::mt19937 m_faultRandom{1};
    double m_clockSeconds = 0.0;
    uint64_t m_sentSequence = 0;
    uint32_t m_droppedCount = 0;
    std::vector<InFlight> m_inFlight;
    // By link and channel: when the last Reliable message arrives (a later one never arrives before it), and the
    // newest UnreliableNewest message that arrived (an older one is dropped).
    std::vector<std::array<double, ChannelCount>> m_reliableArrival;
    std::vector<std::array<uint64_t, ChannelCount>> m_newestArrived;
    // What arrived and waits for the next service().
    std::deque<NetEvent> m_arriving;
    std::deque<NetEvent> m_events;
};
}
