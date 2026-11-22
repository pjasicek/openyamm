#include "engine/net/LoopbackTransport.h"

#include <algorithm>

namespace OpenYAMM::Engine
{
LoopbackTransport::LoopbackTransport() = default;

LoopbackTransport::~LoopbackTransport()
{
    for (Link &link : m_links)
    {
        if (link.open && link.pRemote != nullptr)
        {
            link.pRemote->dropLinkTo(this);
        }
    }
}

void LoopbackTransport::accept(LoopbackTransport &client)
{
    const NetPeerId hostSidePeer = NetPeerId(m_links.size());
    const NetPeerId clientSidePeer = NetPeerId(client.m_links.size());
    m_links.push_back(Link{&client, clientSidePeer, true});
    client.m_links.push_back(Link{this, hostSidePeer, true});
    m_arriving.push_back(NetEvent{NetEvent::Type::Connected, hostSidePeer, 0, {}});
    client.m_arriving.push_back(NetEvent{NetEvent::Type::Connected, clientSidePeer, 0, {}});
}

void LoopbackTransport::dropLinkTo(const LoopbackTransport *pRemote)
{
    for (size_t index = 0; index < m_links.size(); ++index)
    {
        Link &link = m_links[index];

        if (link.open && link.pRemote == pRemote)
        {
            link.open = false;
            link.pRemote = nullptr;
            m_arriving.push_back(NetEvent{NetEvent::Type::Disconnected, NetPeerId(index), 0, {}});
        }
    }
}

void LoopbackTransport::setFaults(const NetFaults &faults)
{
    m_faults = faults;
    m_faultRandom.seed(faults.seed);
}

void LoopbackTransport::advanceClock(float seconds)
{
    m_clockSeconds += std::max(0.0f, seconds);
    deliverDue();
}

uint32_t LoopbackTransport::sentCount() const
{
    return uint32_t(m_sentSequence);
}

uint32_t LoopbackTransport::droppedCount() const
{
    return m_droppedCount;
}

void LoopbackTransport::deliverDue()
{
    // Oldest arrival first; what was sent first goes first among those due at the same moment.
    std::stable_sort(m_inFlight.begin(), m_inFlight.end(), [](const InFlight &left, const InFlight &right)
    {
        return left.arrivalSeconds != right.arrivalSeconds ? left.arrivalSeconds < right.arrivalSeconds
            : left.sequence < right.sequence;
    });
    size_t delivered = 0;

    while (delivered < m_inFlight.size() && m_inFlight[delivered].arrivalSeconds <= m_clockSeconds)
    {
        InFlight &message = m_inFlight[delivered];
        ++delivered;

        if (message.link >= m_links.size() || !m_links[message.link].open)
        {
            continue;
        }

        if (message.delivery == NetDelivery::UnreliableNewest)
        {
            uint64_t &newest = m_newestArrived[message.link][message.event.channel];

            // Overtaken by a newer one of its channel.
            if (message.sequence < newest)
            {
                ++m_droppedCount;
                continue;
            }

            newest = message.sequence;
        }

        m_links[message.link].pRemote->m_arriving.push_back(std::move(message.event));
    }

    m_inFlight.erase(m_inFlight.begin(), m_inFlight.begin() + std::ptrdiff_t(delivered));

    for (size_t index = 0; index < m_links.size(); ++index)
    {
        const bool underWay = std::any_of(m_inFlight.begin(), m_inFlight.end(),
            [index](const auto &message) { return message.link == index; });

        if (m_links[index].closing && !underWay)
        {
            closeLink(NetPeerId(index));
        }
    }
}

void LoopbackTransport::service(uint32_t)
{
    while (!m_arriving.empty())
    {
        m_events.push_back(std::move(m_arriving.front()));
        m_arriving.pop_front();
    }
}

bool LoopbackTransport::pollEvent(NetEvent &event)
{
    if (m_events.empty())
    {
        return false;
    }

    event = std::move(m_events.front());
    m_events.pop_front();
    return true;
}

bool LoopbackTransport::send(NetPeerId peer, uint8_t channel, NetDelivery delivery, std::span<const uint8_t> payload)
{
    if (peer >= m_links.size() || !m_links[peer].open || m_links[peer].closing || channel >= ChannelCount)
    {
        return false;
    }

    const Link &link = m_links[peer];
    NetEvent event;
    event.type = NetEvent::Type::Message;
    event.peer = link.remotePeer;
    event.channel = channel;
    event.payload.assign(payload.begin(), payload.end());

    if (!m_faults.any() && m_inFlight.empty())
    {
        link.pRemote->m_arriving.push_back(std::move(event));
        return true;
    }

    ++m_sentSequence;

    if (delivery == NetDelivery::UnreliableNewest && m_faults.lossPermille != 0
        && std::uniform_int_distribution<uint32_t>(0, 999)(m_faultRandom) < m_faults.lossPermille)
    {
        ++m_droppedCount;
        return true;
    }

    if (m_reliableArrival.size() < m_links.size())
    {
        m_reliableArrival.resize(m_links.size(), {});
        m_newestArrived.resize(m_links.size(), {});
    }

    const uint32_t jitterMs =
        m_faults.jitterMs != 0 ? std::uniform_int_distribution<uint32_t>(0, m_faults.jitterMs)(m_faultRandom) : 0;
    double arrivalSeconds = m_clockSeconds + double(m_faults.delayMs + jitterMs) / 1000.0;

    if (delivery == NetDelivery::Reliable)
    {
        // In the order sent: never before the one sent before it.
        double &lastArrival = m_reliableArrival[peer][channel];
        arrivalSeconds = std::max(arrivalSeconds, lastArrival);
        lastArrival = arrivalSeconds;
    }

    m_inFlight.push_back(InFlight{arrivalSeconds, m_sentSequence, peer, delivery, std::move(event)});
    return true;
}

void LoopbackTransport::disconnect(NetPeerId peer)
{
    if (peer >= m_links.size() || !m_links[peer].open)
    {
        return;
    }

    // What was sent before the disconnecting arrives first, as over a real line (a refusal's reason, a leaving
    // game's last word): the link closes when nothing of it is under way any more.
    const bool underWay = std::any_of(m_inFlight.begin(), m_inFlight.end(),
        [peer](const auto &message) { return message.link == peer; });

    if (underWay)
    {
        m_links[peer].closing = true;
        return;
    }

    closeLink(peer);
}

void LoopbackTransport::closeLink(NetPeerId peer)
{
    if (peer >= m_links.size() || !m_links[peer].open)
    {
        return;
    }

    m_links[peer].closing = false;
    LoopbackTransport *pRemote = m_links[peer].pRemote;
    m_links[peer].open = false;
    m_links[peer].pRemote = nullptr;
    m_arriving.push_back(NetEvent{NetEvent::Type::Disconnected, peer, 0, {}});

    if (pRemote != nullptr)
    {
        pRemote->dropLinkTo(this);
    }
}

NetPeerStats LoopbackTransport::peerStats(NetPeerId) const
{
    return {};
}
}
