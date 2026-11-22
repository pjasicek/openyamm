#include "engine/net/ByteStream.h"

#include <algorithm>
#include <cstring>

namespace OpenYAMM::Engine
{
void ByteWriter::u8(uint8_t value)
{
    m_bytes.push_back(value);
}

void ByteWriter::u16(uint16_t value)
{
    u8(uint8_t(value));
    u8(uint8_t(value >> 8));
}

void ByteWriter::u32(uint32_t value)
{
    u16(uint16_t(value));
    u16(uint16_t(value >> 16));
}

void ByteWriter::u64(uint64_t value)
{
    u32(uint32_t(value));
    u32(uint32_t(value >> 32));
}

void ByteWriter::i16(int16_t value)
{
    u16(uint16_t(value));
}

void ByteWriter::i32(int32_t value)
{
    u32(uint32_t(value));
}

void ByteWriter::f32(float value)
{
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    u32(bits);
}

void ByteWriter::boolean(bool value)
{
    u8(value ? 1 : 0);
}

void ByteWriter::address(const NetAddress &value)
{
    // The host's four bytes as they lie in memory, which is network order on every machine.
    uint8_t host[4] = {};
    std::memcpy(host, &value.host, sizeof(host));
    raw(host);
    u16(value.port);
}

void ByteWriter::text(const std::string &value, size_t maxLength)
{
    const size_t length = std::min({value.size(), maxLength, size_t(65535)});
    u16(uint16_t(length));
    m_bytes.insert(m_bytes.end(), value.begin(), value.begin() + ptrdiff_t(length));
}

void ByteWriter::block(std::span<const uint8_t> bytes)
{
    u32(uint32_t(bytes.size()));
    raw(bytes);
}

void ByteWriter::raw(std::span<const uint8_t> bytes)
{
    m_bytes.insert(m_bytes.end(), bytes.begin(), bytes.end());
}

ByteReader::ByteReader(std::span<const uint8_t> bytes)
    : m_bytes(bytes)
{
}

bool ByteReader::take(size_t count, const uint8_t *&pBytes)
{
    if (m_failed || m_bytes.size() - m_offset < count)
    {
        m_failed = true;
        return false;
    }

    pBytes = m_bytes.data() + m_offset;
    m_offset += count;
    return true;
}

uint8_t ByteReader::u8()
{
    const uint8_t *pBytes = nullptr;
    return take(1, pBytes) ? pBytes[0] : uint8_t(0);
}

uint16_t ByteReader::u16()
{
    const uint16_t low = u8();
    const uint16_t high = u8();
    return uint16_t(low | (high << 8));
}

uint32_t ByteReader::u32()
{
    const uint32_t low = u16();
    const uint32_t high = u16();
    return low | (high << 16);
}

uint64_t ByteReader::u64()
{
    const uint64_t low = u32();
    const uint64_t high = u32();
    return low | (high << 32);
}

int16_t ByteReader::i16()
{
    return int16_t(u16());
}

int32_t ByteReader::i32()
{
    return int32_t(u32());
}

float ByteReader::f32()
{
    const uint32_t bits = u32();
    float value = 0.0f;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

bool ByteReader::boolean()
{
    return u8() != 0;
}

NetAddress ByteReader::address()
{
    NetAddress value;
    const uint8_t *pBytes = nullptr;

    if (take(4, pBytes))
    {
        std::memcpy(&value.host, pBytes, 4);
    }

    value.port = u16();
    return value;
}

std::string ByteReader::text(size_t maxLength)
{
    const size_t length = u16();
    const uint8_t *pBytes = nullptr;

    if (length > maxLength)
    {
        m_failed = true;
        return {};
    }

    if (!take(length, pBytes))
    {
        return {};
    }

    return std::string(reinterpret_cast<const char *>(pBytes), length);
}

std::vector<uint8_t> ByteReader::block(size_t maxLength)
{
    const size_t length = u32();
    const uint8_t *pBytes = nullptr;

    if (length > maxLength)
    {
        m_failed = true;
        return {};
    }

    if (!take(length, pBytes))
    {
        return {};
    }

    return std::vector<uint8_t>(pBytes, pBytes + length);
}

std::span<const uint8_t> ByteReader::rest()
{
    if (m_failed)
    {
        return {};
    }

    const std::span<const uint8_t> bytes = m_bytes.subspan(m_offset);
    m_offset = m_bytes.size();
    return bytes;
}

size_t ByteReader::remaining() const
{
    return m_failed ? 0 : m_bytes.size() - m_offset;
}
}
