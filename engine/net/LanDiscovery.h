#pragma once

#include "engine/net/NetAddress.h"

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
// Finding games on the local network without a server: a game that looks broadcasts a question to the port
// games host on, and every hosting game answers on its own socket with what its session is. The datagrams start with
// "OYLN", so a host tells them from its connection's traffic and from the lobby's.
struct LanSessionInfo
{
    std::string name;
    std::string world;
    std::string ruleset;
    uint32_t protocol = 0;
    uint8_t players = 1;
    uint8_t maxPlayers = 4;
    // The hosting's own number, drawn when it began: one game that answers from several of its addresses (a
    // machine on two networks, or the scanning game's own machine) is one line. 0: none given.
    uint32_t sessionId = 0;
    // Joining asks for the session's password.
    bool locked = false;
};

// A session that answered, at the address its answer came from.
struct LanSession
{
    NetAddress address;
    LanSessionInfo info;
};

// The question's number when the datagram is one, else nothing. A question is as long as the longest answer; a
// shorter one is none, so that a host never answers with more than it was sent.
std::optional<uint32_t> decodeLanProbe(std::span<const uint8_t> datagram);
std::vector<uint8_t> encodeLanProbe(uint32_t nonce);
std::vector<uint8_t> encodeLanAnswer(uint32_t nonce, const LanSessionInfo &info);
// The session of an answer to the question numbered `nonce`, else nothing.
std::optional<LanSessionInfo> decodeLanAnswer(std::span<const uint8_t> datagram, uint32_t nonce);

// The asking side: a socket of its own that broadcasts the question and gathers the answers.
class LanScanner
{
public:
    LanScanner();
    ~LanScanner();

    LanScanner(const LanScanner &) = delete;
    LanScanner &operator=(const LanScanner &) = delete;

    // Asks every game hosting on `port` on the local network, and this machine itself. The answers so far are
    // dropped. False when no socket could be opened.
    bool probe(uint16_t port);
    // Takes in the answers that arrived, up to 64 games in all: anybody on the network can send answers, and a
    // flood of them must not grow the list.
    void service();
    const std::vector<LanSession> &sessions() const;

private:
    void close();

    NetLibrary m_library;
    intptr_t m_socket = -1;
    uint32_t m_nonce = 0;
    std::vector<LanSession> m_sessions;
};
}
