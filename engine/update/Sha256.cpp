#include "engine/update/Sha256.h"

#include <algorithm>
#include <fstream>
#include <vector>

namespace OpenYAMM::Engine
{
namespace
{
constexpr std::array<uint32_t, 64> RoundConstants = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};

uint32_t rotateRight(uint32_t value, int count)
{
    return (value >> count) | (value << (32 - count));
}
}

Sha256::Sha256()
    : m_state({0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19})
{
}

void Sha256::update(const void *pData, size_t size)
{
    const uint8_t *pBytes = static_cast<const uint8_t *>(pData);
    m_totalBytes += size;

    while (size > 0)
    {
        if (m_bufferSize == 0 && size >= m_buffer.size())
        {
            processBlock(pBytes);
            pBytes += m_buffer.size();
            size -= m_buffer.size();
            continue;
        }

        const size_t count = std::min(size, m_buffer.size() - m_bufferSize);
        std::copy(pBytes, pBytes + count, m_buffer.begin() + m_bufferSize);
        m_bufferSize += count;
        pBytes += count;
        size -= count;

        if (m_bufferSize == m_buffer.size())
        {
            processBlock(m_buffer.data());
            m_bufferSize = 0;
        }
    }
}

std::string Sha256::finishHex()
{
    const uint64_t bitCount = m_totalBytes * 8;
    const uint8_t padding = 0x80;
    update(&padding, 1);
    const uint8_t zero = 0;

    while (m_bufferSize != 56)
    {
        update(&zero, 1);
    }

    std::array<uint8_t, 8> length;

    for (size_t index = 0; index < length.size(); ++index)
    {
        length[index] = uint8_t(bitCount >> (56 - 8 * index));
    }

    update(length.data(), length.size());
    constexpr const char *pDigits = "0123456789abcdef";
    std::string hex;
    hex.reserve(64);

    for (const uint32_t word : m_state)
    {
        for (int shift = 28; shift >= 0; shift -= 4)
        {
            hex.push_back(pDigits[(word >> shift) & 0xf]);
        }
    }

    return hex;
}

void Sha256::processBlock(const uint8_t *pBlock)
{
    std::array<uint32_t, 64> words;

    for (size_t index = 0; index < 16; ++index)
    {
        words[index] = uint32_t(pBlock[index * 4]) << 24 | uint32_t(pBlock[index * 4 + 1]) << 16
            | uint32_t(pBlock[index * 4 + 2]) << 8 | uint32_t(pBlock[index * 4 + 3]);
    }

    for (size_t index = 16; index < 64; ++index)
    {
        const uint32_t sigma0 = rotateRight(words[index - 15], 7) ^ rotateRight(words[index - 15], 18)
            ^ (words[index - 15] >> 3);
        const uint32_t sigma1 = rotateRight(words[index - 2], 17) ^ rotateRight(words[index - 2], 19)
            ^ (words[index - 2] >> 10);
        words[index] = words[index - 16] + sigma0 + words[index - 7] + sigma1;
    }

    uint32_t a = m_state[0], b = m_state[1], c = m_state[2], d = m_state[3];
    uint32_t e = m_state[4], f = m_state[5], g = m_state[6], h = m_state[7];

    for (size_t index = 0; index < 64; ++index)
    {
        const uint32_t sum1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
        const uint32_t choice = (e & f) ^ (~e & g);
        const uint32_t first = h + sum1 + choice + RoundConstants[index] + words[index];
        const uint32_t sum0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
        const uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        const uint32_t second = sum0 + majority;
        h = g;
        g = f;
        f = e;
        e = d + first;
        d = c;
        c = b;
        b = a;
        a = first + second;
    }

    m_state[0] += a;
    m_state[1] += b;
    m_state[2] += c;
    m_state[3] += d;
    m_state[4] += e;
    m_state[5] += f;
    m_state[6] += g;
    m_state[7] += h;
}

std::string sha256Hex(const void *pData, size_t size)
{
    Sha256 hash;
    hash.update(pData, size);
    return hash.finishHex();
}

std::optional<std::string> sha256File(const std::filesystem::path &path)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        return std::nullopt;
    }

    Sha256 hash;
    std::vector<char> buffer(1 << 20);

    while (input)
    {
        input.read(buffer.data(), std::streamsize(buffer.size()));
        hash.update(buffer.data(), size_t(input.gcount()));
    }

    if (!input.eof())
    {
        return std::nullopt;
    }

    return hash.finishHex();
}
}
