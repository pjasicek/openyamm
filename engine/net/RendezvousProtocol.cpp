#include "engine/net/RendezvousProtocol.h"

#include <algorithm>
#include <cstring>
#include <string_view>

namespace OpenYAMM::Engine
{
namespace
{
constexpr std::array<uint8_t, 4> Magic = {'O', 'Y', 'R', 'V'};
constexpr size_t HeaderLength = Magic.size() + 2;

// Letters and digits that are not mistaken for each other when read aloud or typed.
constexpr std::string_view CodeAlphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

ByteWriter begin(RendezvousMessage type)
{
    ByteWriter writer;
    writer.raw(Magic);
    writer.u8(RendezvousVersion);
    writer.u8(uint8_t(type));
    return writer;
}

// A reader placed after the header of a datagram of this type; a failed reader otherwise.
ByteReader open(std::span<const uint8_t> datagram, RendezvousMessage type)
{
    const std::optional<RendezvousMessage> actual = peekRendezvousMessage(datagram);

    if (!actual || *actual != type)
    {
        ByteReader failed(std::span<const uint8_t>{});
        failed.u8();
        return failed;
    }

    return ByteReader(datagram.subspan(HeaderLength));
}

std::vector<uint8_t> padded(const ByteWriter &writer, size_t length)
{
    std::vector<uint8_t> bytes = writer.bytes();

    if (bytes.size() < length)
    {
        bytes.resize(length, 0);
    }

    return bytes;
}

// The host's four numbers as they are written, the first first: the host is kept in the network's byte order,
// which is that order in memory on every machine.
std::array<uint8_t, 4> firstOctets(const NetAddress &address)
{
    std::array<uint8_t, 4> octets = {};
    std::memcpy(octets.data(), &address.host, octets.size());
    return octets;
}

void writeCode(ByteWriter &writer, const SessionCode &code)
{
    for (char letter : code)
    {
        writer.u8(uint8_t(letter));
    }
}

bool readCode(ByteReader &reader, SessionCode &code)
{
    for (char &letter : code)
    {
        letter = char(reader.u8());

        if (CodeAlphabet.find(letter) == std::string_view::npos)
        {
            return false;
        }
    }

    return reader.ok();
}

void writeInfo(ByteWriter &writer, const SessionInfo &info)
{
    writer.u32(info.protocolBuild);
    writer.u8(info.players);
    writer.u8(info.maxPlayers);
    writer.u8(info.flags);
    writer.text(info.name, MaxSessionNameLength);
    writer.text(info.world, MaxSessionTagLength);
    writer.text(info.ruleset, MaxSessionTagLength);
}

void readInfo(ByteReader &reader, SessionInfo &info)
{
    info.protocolBuild = reader.u32();
    info.players = reader.u8();
    info.maxPlayers = reader.u8();
    info.flags = reader.u8();
    info.name = reader.text(MaxSessionNameLength);
    info.world = reader.text(MaxSessionTagLength);
    info.ruleset = reader.text(MaxSessionTagLength);
}
}

std::string toString(const SessionCode &code)
{
    return std::string(code.begin(), code.end());
}

SessionCode makeSessionCode(uint64_t random)
{
    SessionCode code = {};

    for (char &letter : code)
    {
        letter = CodeAlphabet[random % CodeAlphabet.size()];
        random /= CodeAlphabet.size();
    }

    return code;
}

std::optional<SessionCode> parseSessionCode(const std::string &text)
{
    if (text.size() != SessionCodeLength)
    {
        return std::nullopt;
    }

    SessionCode code = {};

    for (size_t index = 0; index < SessionCodeLength; ++index)
    {
        const char letter = text[index] >= 'a' && text[index] <= 'z' ? char(text[index] - 'a' + 'A') : text[index];

        if (CodeAlphabet.find(letter) == std::string_view::npos)
        {
            return std::nullopt;
        }

        code[index] = letter;
    }

    return code;
}

bool isLoopbackAddress(const NetAddress &address)
{
    return firstOctets(address)[0] == 127;
}

bool isOwnNetworkAddress(const NetAddress &address)
{
    const std::array<uint8_t, 4> octets = firstOctets(address);
    return octets[0] == 127 || octets[0] == 10 || (octets[0] == 172 && octets[1] >= 16 && octets[1] <= 31)
        || (octets[0] == 192 && octets[1] == 168) || (octets[0] == 169 && octets[1] == 254);
}

bool isUnicastAddress(const NetAddress &address)
{
    const uint8_t first = firstOctets(address)[0];
    return address.port != 0 && first != 0 && first < 224;
}

NetAddress localNetworkAddress(const NetAddress &claimed, const NetAddress &publicAddress)
{
    const bool kept = claimed.valid() && isOwnNetworkAddress(claimed)
        && (!isLoopbackAddress(claimed) || isLoopbackAddress(publicAddress));
    return kept ? claimed : NetAddress{};
}

std::optional<RendezvousMessage> peekRendezvousMessage(std::span<const uint8_t> datagram)
{
    if (datagram.size() < HeaderLength || !std::equal(Magic.begin(), Magic.end(), datagram.begin())
        || datagram[Magic.size()] != RendezvousVersion)
    {
        return std::nullopt;
    }

    const uint8_t type = datagram[Magic.size() + 1];

    if (type < uint8_t(RendezvousMessage::HostRegister) || type > uint8_t(RendezvousMessage::AddressCookie))
    {
        return std::nullopt;
    }

    return RendezvousMessage(type);
}

std::vector<uint8_t> encode(const AddressCookieMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::AddressCookie);
    writer.u32(message.nonce);
    writer.u64(message.cookie);
    return writer.bytes();
}

bool decode(std::span<const uint8_t> datagram, AddressCookieMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::AddressCookie);
    message.nonce = reader.u32();
    message.cookie = reader.u64();
    return reader.ok();
}

std::vector<uint8_t> encode(const HostRegisterMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::HostRegister);
    writer.u32(message.nonce);
    writer.u64(message.sessionKey);
    writer.u64(message.cookie);
    writer.address(message.localAddress);
    writeInfo(writer, message.info);
    return writer.bytes();
}

bool decode(std::span<const uint8_t> datagram, HostRegisterMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::HostRegister);
    message.nonce = reader.u32();
    message.sessionKey = reader.u64();
    message.cookie = reader.u64();
    message.localAddress = reader.address();
    readInfo(reader, message.info);
    return reader.ok() && message.info.maxPlayers > 0;
}

std::vector<uint8_t> encode(const HostRegisteredMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::HostRegistered);
    writer.u32(message.nonce);
    writer.u64(message.sessionKey);
    writeCode(writer, message.code);
    writer.address(message.publicAddress);
    return writer.bytes();
}

bool decode(std::span<const uint8_t> datagram, HostRegisteredMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::HostRegistered);
    message.nonce = reader.u32();
    message.sessionKey = reader.u64();
    const bool codeOk = readCode(reader, message.code);
    message.publicAddress = reader.address();
    return codeOk && reader.ok();
}

std::vector<uint8_t> encode(const HostUnregisterMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::HostUnregister);
    writer.u64(message.sessionKey);
    return writer.bytes();
}

bool decode(std::span<const uint8_t> datagram, HostUnregisterMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::HostUnregister);
    message.sessionKey = reader.u64();
    return reader.ok();
}

std::vector<uint8_t> encode(const ListRequestMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::ListRequest);
    writer.u32(message.nonce);
    writer.u16(message.offset);
    writer.u64(message.cookie);
    return padded(writer, ListRequestLength);
}

bool decode(std::span<const uint8_t> datagram, ListRequestMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::ListRequest);
    message.nonce = reader.u32();
    message.offset = reader.u16();
    message.cookie = reader.u64();
    return reader.ok();
}

std::vector<uint8_t> encode(const ListReplyMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::ListReply);
    const size_t count = std::min(message.entries.size(), MaxListEntriesPerReply);
    writer.u32(message.nonce);
    writer.u16(message.total);
    writer.u16(message.offset);
    writer.u8(uint8_t(count));

    for (size_t index = 0; index < count; ++index)
    {
        writeCode(writer, message.entries[index].code);
        writeInfo(writer, message.entries[index].info);
    }

    return writer.bytes();
}

bool decode(std::span<const uint8_t> datagram, ListReplyMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::ListReply);
    message.nonce = reader.u32();
    message.total = reader.u16();
    message.offset = reader.u16();
    const size_t count = reader.u8();

    if (count > MaxListEntriesPerReply)
    {
        return false;
    }

    message.entries.clear();

    for (size_t index = 0; index < count; ++index)
    {
        SessionListEntry entry;

        if (!readCode(reader, entry.code))
        {
            return false;
        }

        readInfo(reader, entry.info);
        message.entries.push_back(std::move(entry));
    }

    return reader.ok();
}

std::vector<uint8_t> encode(const JoinRequestMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::JoinRequest);
    writer.u32(message.nonce);
    writeCode(writer, message.code);
    writer.address(message.localAddress);
    writer.u8(message.wantRelay ? 1 : 0);
    writer.u64(message.cookie);
    return padded(writer, JoinRequestLength);
}

bool decode(std::span<const uint8_t> datagram, JoinRequestMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::JoinRequest);
    message.nonce = reader.u32();
    const bool codeOk = readCode(reader, message.code);
    message.localAddress = reader.address();
    message.wantRelay = reader.u8() != 0;
    message.cookie = reader.u64();
    return codeOk && reader.ok();
}

std::vector<uint8_t> encode(const JoinReplyMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::JoinReply);
    writer.u32(message.nonce);
    writer.u8(uint8_t(message.status));
    writer.address(message.hostPublicAddress);
    writer.address(message.hostLocalAddress);
    writer.address(message.clientPublicAddress);
    writer.u16(message.relayPort);
    writer.u64(message.relayToken);
    return writer.bytes();
}

bool decode(std::span<const uint8_t> datagram, JoinReplyMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::JoinReply);
    message.nonce = reader.u32();
    const uint8_t status = reader.u8();
    message.hostPublicAddress = reader.address();
    message.hostLocalAddress = reader.address();
    message.clientPublicAddress = reader.address();
    message.relayPort = reader.u16();
    message.relayToken = reader.u64();

    if (status > uint8_t(JoinStatus::RelayUnavailable))
    {
        return false;
    }

    message.status = JoinStatus(status);
    return reader.ok();
}

std::vector<uint8_t> encode(const PeerIntroMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::PeerIntro);
    writer.u32(message.introId);
    writer.address(message.clientPublicAddress);
    writer.address(message.clientLocalAddress);
    writer.u16(message.relayPort);
    writer.u64(message.relayToken);
    writer.u64(message.sessionKey);
    return writer.bytes();
}

bool decode(std::span<const uint8_t> datagram, PeerIntroMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::PeerIntro);
    message.introId = reader.u32();
    message.clientPublicAddress = reader.address();
    message.clientLocalAddress = reader.address();
    message.relayPort = reader.u16();
    message.relayToken = reader.u64();
    message.sessionKey = reader.u64();
    return reader.ok();
}

std::vector<uint8_t> encode(const PunchMessage &message)
{
    ByteWriter writer = begin(RendezvousMessage::Punch);
    writer.u32(message.id);
    writer.u8(message.isAck ? 1 : 0);
    return writer.bytes();
}

bool decode(std::span<const uint8_t> datagram, PunchMessage &message)
{
    ByteReader reader = open(datagram, RendezvousMessage::Punch);
    message.id = reader.u32();
    message.isAck = reader.u8() != 0;
    return reader.ok();
}

std::vector<uint8_t> encode(const RelayBindMessage &message, RendezvousMessage type)
{
    ByteWriter writer = begin(type);
    writer.u64(message.token);
    return writer.bytes();
}

bool decode(std::span<const uint8_t> datagram, RelayBindMessage &message)
{
    const std::optional<RendezvousMessage> type = peekRendezvousMessage(datagram);

    if (!type || (*type != RendezvousMessage::RelayBind && *type != RendezvousMessage::RelayBound))
    {
        return false;
    }

    ByteReader reader = open(datagram, *type);
    message.token = reader.u64();
    return reader.ok();
}
}
