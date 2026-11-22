#include "game/coop/CoopLobbyBrowser.h"

#include "game/coop/CoopProtocol.h"

namespace OpenYAMM::Game
{
void CoopLobbyBrowser::refresh(uint16_t port, const std::string &lobbyAddress, std::string &error)
{
    error.clear();
    m_pLobby.reset();
    m_pSocket.reset();

    if (!m_scanner.probe(port))
    {
        error = "could not open a socket to scan the local network";
    }

    if (lobbyAddress.empty())
    {
        return;
    }

    constexpr uint32_t RetryFailedAfterMs = 30000;
    const uint32_t nowMs = Engine::netNowMilliseconds();

    if (lobbyAddress != m_lookup.text() || (m_lookup.failed() && nowMs - m_lookupAtMs >= RetryFailedAfterMs))
    {
        m_lookupAtMs = nowMs;
        m_lookup.start(lobbyAddress, Coop::DefaultLobbyPort);
    }

    // Still being looked up: the local network's games show meanwhile, the lobby's at the refresh after.
    if (m_lookup.pending())
    {
        return;
    }

    const std::optional<Engine::NetAddress> lobby = m_lookup.address();
    m_pSocket = std::make_unique<Engine::EnetTransport>();

    if (!lobby || !m_pSocket->open(0, 1))
    {
        error = !lobby ? "could not resolve the lobby at " + lobbyAddress : "could not open a socket for the lobby";
        m_pSocket.reset();
        return;
    }

    Engine::EnetTransport *pSocket = m_pSocket.get();
    m_pLobby = std::make_unique<Engine::RendezvousClient>(
        [pSocket](const Engine::NetAddress &to, std::span<const uint8_t> datagram)
        {
            pSocket->sendDatagram(to, datagram);
        },
        *lobby);
    Engine::RendezvousClient *pLobby = m_pLobby.get();
    m_pSocket->setDatagramHandler([pLobby](const Engine::NetAddress &from, std::span<const uint8_t> datagram)
    {
        return pLobby->handleDatagram(from, datagram, Engine::netNowMilliseconds());
    });
    m_pLobby->requestList();
}

void CoopLobbyBrowser::update()
{
    m_scanner.service();

    if (m_pSocket && m_pLobby)
    {
        m_pSocket->service(0);
        m_pLobby->update(Engine::netNowMilliseconds());
    }
}

bool CoopLobbyBrowser::takeLobbyFound()
{
    return m_lookup.takeDone();
}

bool CoopLobbyBrowser::lobbyAnswered() const
{
    return m_pLobby == nullptr || m_pLobby->sessionList().has_value();
}

std::vector<CoopLobbyBrowser::Entry> CoopLobbyBrowser::entries() const
{
    std::vector<Entry> entries;

    for (const Engine::LanSession &session : m_scanner.sessions())
    {
        Entry entry;
        entry.name = session.info.name;
        entry.world = session.info.world;
        entry.ruleset = session.info.ruleset;
        entry.protocol = session.info.protocol;
        entry.players = session.info.players;
        entry.maxPlayers = session.info.maxPlayers;
        entry.address = Engine::toString(session.address);
        entry.locked = session.info.locked;
        entries.push_back(std::move(entry));
    }

    if (m_pLobby != nullptr && m_pLobby->sessionList())
    {
        for (const Engine::SessionListEntry &session : *m_pLobby->sessionList())
        {
            Entry entry;
            entry.name = session.info.name;
            entry.world = session.info.world;
            entry.ruleset = session.info.ruleset;
            entry.protocol = session.info.protocolBuild;
            entry.players = session.info.players;
            entry.maxPlayers = session.info.maxPlayers;
            entry.code = Engine::toString(session.code);
            entry.locked = (session.info.flags & Engine::SessionFlagPassword) != 0;
            entries.push_back(std::move(entry));
        }
    }

    return entries;
}
}
