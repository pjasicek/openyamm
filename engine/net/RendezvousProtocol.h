#pragma once

#include "engine/net/ByteStream.h"

#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

// The rendezvous protocol, version 2: datagrams between a game and the rendezvous server, and between two games
// while they open a path to each other. Every datagram starts with the four bytes "OYRV", a version byte and a type
// byte, so that it is told apart from the transport's own datagrams on the same socket. A datagram of another
// version is none: a game and a server of different versions do not answer each other.
// Version 2 (2026-11-21): the address cookie in every request to the server, and the session key in an introduction.
namespace OpenYAMM::Engine
{
constexpr uint8_t RendezvousVersion = 2;
constexpr size_t SessionCodeLength = 6;
constexpr size_t MaxSessionNameLength = 48;
constexpr size_t MaxSessionTagLength = 24;
constexpr size_t MaxListEntriesPerReply = 10;
// A request is padded to at least the size of everything the server sends because of it, and the server ignores a
// shorter one. A request with a forged sender address then cannot make the server send more than it was sent. (With
// the address cookie such a request gets only the cookie in answer, eighteen bytes; the padding stays.)
constexpr size_t ListRequestLength = 1200;
constexpr size_t JoinRequestLength = 96;

using SessionCode = std::array<char, SessionCodeLength>;

enum class RendezvousMessage : uint8_t
{
    HostRegister = 1,
    HostRegistered = 2,
    HostUnregister = 3,
    ListRequest = 4,
    ListReply = 5,
    JoinRequest = 6,
    JoinReply = 7,
    PeerIntro = 8,
    Punch = 9,
    RelayBind = 10,
    RelayBound = 11,
    AddressCookie = 12,
};

enum SessionFlags : uint8_t
{
    SessionFlagPassword = 1 << 0,
    SessionFlagListed = 1 << 1,
};

// What a session list shows.
struct SessionInfo
{
    std::string name;
    std::string world;
    std::string ruleset;
    uint32_t protocolBuild = 0;
    uint8_t players = 1;
    uint8_t maxPlayers = 4;
    uint8_t flags = SessionFlagListed;
};

// Server to a game whose request came without a cookie, or with one that is no longer good: nothing was done and
// nothing is remembered; the game repeats its request with this cookie. The cookie is the server's own stamp on the
// address the request came from, so a game that sends it back is at that address: a sender address can be forged,
// but the forger never sees what is sent there. `nonce` is the request's.
struct AddressCookieMessage
{
    uint32_t nonce = 0;
    uint64_t cookie = 0;
};

// Host to server, repeated as the heartbeat. `sessionKey` is 0 the first time and the server's answer afterwards.
// A first registration needs the cookie, and so does a heartbeat from another address than the session's.
struct HostRegisterMessage
{
    uint32_t nonce = 0;
    uint64_t sessionKey = 0;
    uint64_t cookie = 0;
    NetAddress localAddress;
    SessionInfo info;
};

struct HostRegisteredMessage
{
    uint32_t nonce = 0;
    uint64_t sessionKey = 0;
    SessionCode code = {};
    NetAddress publicAddress;
};

struct HostUnregisterMessage
{
    uint64_t sessionKey = 0;
};

struct ListRequestMessage
{
    uint32_t nonce = 0;
    uint16_t offset = 0;
    uint64_t cookie = 0;
};

struct SessionListEntry
{
    SessionCode code = {};
    SessionInfo info;
};

struct ListReplyMessage
{
    uint32_t nonce = 0;
    uint16_t total = 0;
    uint16_t offset = 0;
    std::vector<SessionListEntry> entries;
};

struct JoinRequestMessage
{
    uint32_t nonce = 0;
    SessionCode code = {};
    NetAddress localAddress;
    bool wantRelay = false;
    uint64_t cookie = 0;
};

enum class JoinStatus : uint8_t
{
    Ok = 0,
    NoSuchSession = 1,
    RelayUnavailable = 2,
};

// Server to the joining game. The relay, when asked for, is the server's own address with `relayPort`.
struct JoinReplyMessage
{
    uint32_t nonce = 0;
    JoinStatus status = JoinStatus::Ok;
    NetAddress hostPublicAddress;
    NetAddress hostLocalAddress;
    NetAddress clientPublicAddress;
    uint16_t relayPort = 0;
    uint64_t relayToken = 0;
};

// Server to the host: a game wants to join. The host opens its router towards the two addresses and, when a relay
// port is named, binds to it. `sessionKey` is the host's own key, which only the server and the host know: the host
// acts on no introduction without it, whatever address it seems to come from.
struct PeerIntroMessage
{
    uint32_t introId = 0;
    NetAddress clientPublicAddress;
    NetAddress clientLocalAddress;
    uint16_t relayPort = 0;
    uint64_t relayToken = 0;
    uint64_t sessionKey = 0;
};

// Game to game. Both sides send it to open their routers; the answer has `isAck` set.
struct PunchMessage
{
    uint32_t id = 0;
    bool isAck = false;
};

// Game to a relay port and back. The token says which side of the pair the sender is.
struct RelayBindMessage
{
    uint64_t token = 0;
};

std::string toString(const SessionCode &code);
// A code from the letters and digits that are not mistaken for each other, taken from a random number.
SessionCode makeSessionCode(uint64_t random);
std::optional<SessionCode> parseSessionCode(const std::string &text);

// This machine itself (127/8).
bool isLoopbackAddress(const NetAddress &address);
// An address of somebody's own network or machine, which leads nowhere beyond it: the private ranges (10/8,
// 172.16/12, 192.168/16), the link-local one (169.254/16) and 127/8.
bool isOwnNetworkAddress(const NetAddress &address);
// An address one game can be at and be sent to: a port, and a host that is no group or broadcast address (224/4,
// 240/4) and not 0/8.
bool isUnicastAddress(const NetAddress &address);
// The address a game says it has on its own network, or none when it is no such address. The other side sends
// datagrams there to find a path, so a game could otherwise name anybody on the internet as their target. Kept are
// the private and link-local ranges, and this machine itself only for a game whose public address is this machine.
NetAddress localNetworkAddress(const NetAddress &claimed, const NetAddress &publicAddress);

// The type of a rendezvous datagram; none for anything else (a transport datagram).
std::optional<RendezvousMessage> peekRendezvousMessage(std::span<const uint8_t> datagram);

std::vector<uint8_t> encode(const AddressCookieMessage &message);
std::vector<uint8_t> encode(const HostRegisterMessage &message);
std::vector<uint8_t> encode(const HostRegisteredMessage &message);
std::vector<uint8_t> encode(const HostUnregisterMessage &message);
std::vector<uint8_t> encode(const ListRequestMessage &message);
std::vector<uint8_t> encode(const ListReplyMessage &message);
std::vector<uint8_t> encode(const JoinRequestMessage &message);
std::vector<uint8_t> encode(const JoinReplyMessage &message);
std::vector<uint8_t> encode(const PeerIntroMessage &message);
std::vector<uint8_t> encode(const PunchMessage &message);
std::vector<uint8_t> encode(const RelayBindMessage &message, RendezvousMessage type);

// Each returns false for a datagram that is cut short or carries a field out of range.
bool decode(std::span<const uint8_t> datagram, AddressCookieMessage &message);
bool decode(std::span<const uint8_t> datagram, HostRegisterMessage &message);
bool decode(std::span<const uint8_t> datagram, HostRegisteredMessage &message);
bool decode(std::span<const uint8_t> datagram, HostUnregisterMessage &message);
bool decode(std::span<const uint8_t> datagram, ListRequestMessage &message);
bool decode(std::span<const uint8_t> datagram, ListReplyMessage &message);
bool decode(std::span<const uint8_t> datagram, JoinRequestMessage &message);
bool decode(std::span<const uint8_t> datagram, JoinReplyMessage &message);
bool decode(std::span<const uint8_t> datagram, PeerIntroMessage &message);
bool decode(std::span<const uint8_t> datagram, PunchMessage &message);
bool decode(std::span<const uint8_t> datagram, RelayBindMessage &message);
}
