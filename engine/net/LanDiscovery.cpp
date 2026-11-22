#include "engine/net/LanDiscovery.h"

#include "engine/net/ByteStream.h"

#include <enet/enet.h>

#include <algorithm>
#include <array>
#include <random>

namespace OpenYAMM::Engine
{
namespace
{
constexpr std::array<uint8_t, 4> Magic = {'O', 'Y', 'L', 'N'};
constexpr uint8_t Version = 1;
constexpr uint8_t TypeProbe = 1;
constexpr uint8_t TypeAnswer = 2;
constexpr size_t MaxNameLength = 48;
constexpr size_t MaxTagLength = 24;
// The longest answer there is: the ten bytes every datagram begins with, then the fields of encodeLanAnswer, each
// text with its two bytes of length.
constexpr size_t MaxAnswerLength =
    10 + 4 + 1 + 1 + (2 + MaxNameLength) + (2 + MaxTagLength) + (2 + MaxTagLength) + 4 + 1;
// A question is padded to the size of the longest answer, and a host ignores a shorter one. A question with a
// forged sender address then cannot make a host send anybody more than the forger sent itself.
constexpr size_t ProbeLength = MaxAnswerLength;
// The most games one scan lists: more than a local network has, and few enough to look through for every answer.
constexpr size_t MaxScannedSessions = 64;

ByteWriter begin(uint8_t type, uint32_t nonce)
{
    ByteWriter writer;
    writer.raw(Magic);
    writer.u8(Version);
    writer.u8(type);
    writer.u32(nonce);
    return writer;
}

// The number of a datagram of this kind, else nothing; the reader is left after the number.
std::optional<uint32_t> open(ByteReader &reader, uint8_t type)
{
    for (const uint8_t byte : Magic)
    {
        if (reader.u8() != byte)
        {
            return std::nullopt;
        }
    }

    if (reader.u8() != Version || reader.u8() != type)
    {
        return std::nullopt;
    }

    const uint32_t nonce = reader.u32();
    return reader.ok() ? std::optional<uint32_t>(nonce) : std::nullopt;
}
}

std::optional<uint32_t> decodeLanProbe(std::span<const uint8_t> datagram)
{
    if (datagram.size() < ProbeLength)
    {
        return std::nullopt;
    }

    ByteReader reader(datagram);
    return open(reader, TypeProbe);
}

std::vector<uint8_t> encodeLanProbe(uint32_t nonce)
{
    std::vector<uint8_t> question = begin(TypeProbe, nonce).take();
    question.resize(ProbeLength, 0);
    return question;
}

std::vector<uint8_t> encodeLanAnswer(uint32_t nonce, const LanSessionInfo &info)
{
    ByteWriter writer = begin(TypeAnswer, nonce);
    writer.u32(info.protocol);
    writer.u8(info.players);
    writer.u8(info.maxPlayers);
    writer.text(info.name, MaxNameLength);
    writer.text(info.world, MaxTagLength);
    writer.text(info.ruleset, MaxTagLength);
    writer.u32(info.sessionId);
    writer.boolean(info.locked);
    return writer.bytes();
}

std::optional<LanSessionInfo> decodeLanAnswer(std::span<const uint8_t> datagram, uint32_t nonce)
{
    ByteReader reader(datagram);
    const std::optional<uint32_t> answered = open(reader, TypeAnswer);

    if (!answered || *answered != nonce)
    {
        return std::nullopt;
    }

    LanSessionInfo info;
    info.protocol = reader.u32();
    info.players = reader.u8();
    info.maxPlayers = reader.u8();
    info.name = reader.text(MaxNameLength);
    info.world = reader.text(MaxTagLength);
    info.ruleset = reader.text(MaxTagLength);
    info.sessionId = reader.u32();
    info.locked = reader.boolean();
    return reader.ok() ? std::optional<LanSessionInfo>(info) : std::nullopt;
}

LanScanner::LanScanner() = default;

LanScanner::~LanScanner()
{
    close();
}

void LanScanner::close()
{
    if (m_socket >= 0)
    {
        enet_socket_destroy(ENetSocket(m_socket));
        m_socket = -1;
    }
}

bool LanScanner::probe(uint16_t port)
{
    close();
    m_sessions.clear();
    const ENetSocket socket = enet_socket_create(ENET_SOCKET_TYPE_DATAGRAM);

    if (socket == ENET_SOCKET_NULL)
    {
        return false;
    }

    if (enet_socket_set_option(socket, ENET_SOCKOPT_NONBLOCK, 1) != 0
        || enet_socket_set_option(socket, ENET_SOCKOPT_BROADCAST, 1) != 0)
    {
        enet_socket_destroy(socket);
        return false;
    }

    m_socket = intptr_t(socket);
    m_nonce = std::random_device{}();
    const std::vector<uint8_t> question = encodeLanProbe(m_nonce);
    ENetBuffer buffer = {};
    buffer.data = const_cast<uint8_t *>(question.data());
    buffer.dataLength = question.size();
    // The whole local network, and this machine itself (a second game on the same PC), which a broadcast does not
    // reach everywhere.
    ENetAddress everyone = {};
    everyone.host = ENET_HOST_BROADCAST;
    everyone.port = port;
    enet_socket_send(socket, &everyone, &buffer, 1);
    ENetAddress self = {};
    enet_address_set_host_ip(&self, "127.0.0.1");
    self.port = port;
    enet_socket_send(socket, &self, &buffer, 1);
    return true;
}

void LanScanner::service()
{
    if (m_socket < 0)
    {
        return;
    }

    std::array<uint8_t, 1500> bytes = {};

    for (int count = 0; count < 64; ++count)
    {
        ENetAddress from = {};
        ENetBuffer buffer = {};
        buffer.data = bytes.data();
        buffer.dataLength = bytes.size();
        const int length = enet_socket_receive(ENetSocket(m_socket), &from, &buffer, 1);

        if (length <= 0)
        {
            return;
        }

        // A full list takes no more: what still arrives is read off the socket and dropped unlooked at, so that
        // a flood of answers (anybody on the network can send them) costs neither memory nor time.
        if (m_sessions.size() >= MaxScannedSessions)
        {
            continue;
        }

        const std::optional<LanSessionInfo> info =
            decodeLanAnswer(std::span<const uint8_t>(bytes.data(), size_t(length)), m_nonce);
        const NetAddress address{from.host, from.port};

        // One line a game, however many of its answers arrive and from however many of its addresses.
        if (info && std::none_of(m_sessions.begin(), m_sessions.end(),
                [&address, &info](const LanSession &session)
                {
                    return session.address == address
                        || (info->sessionId != 0 && session.info.sessionId == info->sessionId);
                }))
        {
            m_sessions.push_back(LanSession{address, *info});
        }
    }
}

const std::vector<LanSession> &LanScanner::sessions() const
{
    return m_sessions;
}
}
