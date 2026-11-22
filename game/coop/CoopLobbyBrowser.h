#pragma once

#include "engine/net/EnetTransport.h"
#include "engine/net/LanDiscovery.h"
#include "engine/net/RendezvousClient.h"
#include "game/coop/LobbyLookup.h"

#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The games a player could join, for the Join screen: those hosting on the local network, found by a scan, and the
// sessions a lobby lists. It has a socket of its own and belongs to no session.
class CoopLobbyBrowser
{
public:
    // A game to join, by an address (the local network) or by a lobby's code.
    struct Entry
    {
        std::string name;
        std::string world;
        std::string ruleset;
        uint32_t protocol = 0;
        int players = 0;
        int maxPlayers = 0;
        // "host:port" of a game on the local network; empty for a lobby's session.
        std::string address;
        // A lobby's code; empty for a game on the local network.
        std::string code;
        // Joining asks for the game's password.
        bool locked = false;
    };

    // Asks again: the local network for games hosting on `port`, and the lobby at `lobbyAddress` ("host:port" or a
    // host, empty for none) for its list. The entries so far are dropped. `error` says what could not be asked;
    // what could be is asked anyway.
    void refresh(uint16_t port, const std::string &lobbyAddress, std::string &error);
    // Every frame while the list is shown: takes in the answers.
    void update();
    // The games found so far, the local network's first.
    std::vector<Entry> entries() const;
    // Whether the lobby has answered the last refresh (true when none was asked).
    bool lobbyAnswered() const;
    // True once when the lobby's address has just been found (or not): the moment to refresh again.
    bool takeLobbyFound();

private:
    Engine::LanScanner m_scanner;
    std::unique_ptr<Engine::EnetTransport> m_pSocket;
    std::unique_ptr<Engine::RendezvousClient> m_pLobby;
    // The lobby's address, looked up beside the game when its text changes (and again after a while when that
    // failed), not on every refresh.
    LobbyLookup m_lookup;
    uint32_t m_lookupAtMs = 0;
};
}
