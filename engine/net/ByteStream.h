#pragma once

#include "engine/net/NetAddress.h"

#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
// Writes fields one by one, little-endian, into a byte buffer: what a message between two games is made of. No
// structs, no pointers; every text and block carries its length.
class ByteWriter
{
public:
    void u8(uint8_t value);
    void u16(uint16_t value);
    void u32(uint32_t value);
    void u64(uint64_t value);
    void i16(int16_t value);
    void i32(int32_t value);
    void f32(float value);
    void boolean(bool value);
    // The four bytes of the host as they are kept, then the port.
    void address(const NetAddress &value);
    // A two-byte length and the text, cut to `maxLength` (at most 65535).
    void text(const std::string &value, size_t maxLength = 65535);
    // A four-byte length and the bytes.
    void block(std::span<const uint8_t> bytes);
    void raw(std::span<const uint8_t> bytes);

    const std::vector<uint8_t> &bytes() const
    {
        return m_bytes;
    }

    std::vector<uint8_t> take()
    {
        return std::move(m_bytes);
    }

private:
    std::vector<uint8_t> m_bytes;
};

// Reads what ByteWriter wrote. A read past the end fails the reader and returns zero or empty; check ok() once at the
// end.
class ByteReader
{
public:
    explicit ByteReader(std::span<const uint8_t> bytes);

    uint8_t u8();
    uint16_t u16();
    uint32_t u32();
    uint64_t u64();
    int16_t i16();
    int32_t i32();
    float f32();
    bool boolean();
    NetAddress address();
    // Fails the reader when the text is longer than `maxLength`.
    std::string text(size_t maxLength = 65535);
    // Fails the reader when the block is longer than `maxLength`.
    std::vector<uint8_t> block(size_t maxLength);
    std::span<const uint8_t> rest();
    size_t remaining() const;

    void fail()
    {
        m_failed = true;
    }

    bool ok() const
    {
        return !m_failed;
    }

private:
    bool take(size_t count, const uint8_t *&pBytes);

    std::span<const uint8_t> m_bytes;
    size_t m_offset = 0;
    bool m_failed = false;
};
}
