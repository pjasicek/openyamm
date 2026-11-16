#include "core/RgbaPng.h"

#include <algorithm>
#include <array>
#include <cstdlib>

namespace OpenYAMM::Studio
{
namespace
{
uint32_t crc32Of(const uint8_t *pData, size_t length, uint32_t crc)
{
    static const std::array<uint32_t, 256> table = []()
    {
        std::array<uint32_t, 256> values = {};

        for (uint32_t index = 0; index < 256; ++index)
        {
            uint32_t value = index;

            for (int bit = 0; bit < 8; ++bit)
            {
                value = (value & 1) ? 0xedb88320u ^ (value >> 1) : value >> 1;
            }

            values[index] = value;
        }

        return values;
    }();

    for (size_t index = 0; index < length; ++index)
    {
        crc = table[(crc ^ pData[index]) & 0xff] ^ (crc >> 8);
    }

    return crc;
}

void appendBigEndian(std::vector<uint8_t> &bytes, uint32_t value)
{
    for (int shift = 24; shift >= 0; shift -= 8)
    {
        bytes.push_back(uint8_t((value >> shift) & 0xff));
    }
}

void appendChunk(std::vector<uint8_t> &file, const char *pType, const std::vector<uint8_t> &data)
{
    appendBigEndian(file, uint32_t(data.size()));
    const size_t start = file.size();
    file.insert(file.end(), pType, pType + 4);
    file.insert(file.end(), data.begin(), data.end());
    appendBigEndian(file, crc32Of(file.data() + start, file.size() - start, 0xffffffffu) ^ 0xffffffffu);
}

// Bits into bytes, least significant first (RFC 1951 3.1.1).
class BitWriter
{
public:
    explicit BitWriter(std::vector<uint8_t> &out)
        : m_out(out)
    {
    }

    void bits(uint32_t value, int count)
    {
        m_buffer |= uint64_t(value) << m_count;
        m_count += count;

        while (m_count >= 8)
        {
            m_out.push_back(uint8_t(m_buffer & 0xff));
            m_buffer >>= 8;
            m_count -= 8;
        }
    }

    // A Huffman code, whose bits go most significant first.
    void code(uint32_t value, int count)
    {
        uint32_t reversed = 0;

        for (int bit = 0; bit < count; ++bit)
        {
            reversed = (reversed << 1) | ((value >> bit) & 1u);
        }

        bits(reversed, count);
    }

    void flush()
    {
        if (m_count > 0)
        {
            m_out.push_back(uint8_t(m_buffer & 0xff));
        }

        m_buffer = 0;
        m_count = 0;
    }

private:
    std::vector<uint8_t> &m_out;
    uint64_t m_buffer = 0;
    int m_count = 0;
};

constexpr std::array<int, 29> LengthBase = {3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59,
    67, 83, 99, 115, 131, 163, 195, 227, 258};
constexpr std::array<int, 29> LengthExtra = {0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4,
    5, 5, 5, 5, 0};
constexpr std::array<int, 30> DistanceBase = {1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385,
    513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577};
constexpr std::array<int, 30> DistanceExtra = {0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10,
    10, 11, 11, 12, 12, 13, 13};

// The fixed literal/length code of `symbol` (RFC 1951 3.2.6).
void writeLiteral(BitWriter &writer, int symbol)
{
    if (symbol < 144)
    {
        writer.code(uint32_t(0x30 + symbol), 8);
    }
    else if (symbol < 256)
    {
        writer.code(uint32_t(0x190 + symbol - 144), 9);
    }
    else if (symbol < 280)
    {
        writer.code(uint32_t(symbol - 256), 7);
    }
    else
    {
        writer.code(uint32_t(0xc0 + symbol - 280), 8);
    }
}

void writeMatch(BitWriter &writer, int length, int distance)
{
    int lengthCode = 28;

    while (LengthBase[size_t(lengthCode)] > length)
    {
        --lengthCode;
    }

    writeLiteral(writer, 257 + lengthCode);
    writer.bits(uint32_t(length - LengthBase[size_t(lengthCode)]), LengthExtra[size_t(lengthCode)]);
    int distanceCode = 29;

    while (DistanceBase[size_t(distanceCode)] > distance)
    {
        --distanceCode;
    }

    writer.code(uint32_t(distanceCode), 5);
    writer.bits(uint32_t(distance - DistanceBase[size_t(distanceCode)]), DistanceExtra[size_t(distanceCode)]);
}

uint8_t paeth(int left, int up, int upLeft)
{
    const int estimate = left + up - upLeft;
    const int toLeft = std::abs(estimate - left);
    const int toUp = std::abs(estimate - up);
    const int toUpLeft = std::abs(estimate - upLeft);

    if (toLeft <= toUp && toLeft <= toUpLeft)
    {
        return uint8_t(left);
    }

    return uint8_t(toUp <= toUpLeft ? up : upLeft);
}
}

std::vector<uint8_t> deflateZlib(const std::vector<uint8_t> &data)
{
    constexpr int WindowSize = 32768;
    constexpr int HashSize = 1 << 15;
    constexpr int MaxChain = 64;
    constexpr int MaxMatch = 258;
    std::vector<uint8_t> out = {0x78, 0x01};
    BitWriter writer(out);
    // One final block with the fixed codes.
    writer.bits(1, 1);
    writer.bits(1, 2);
    std::vector<int32_t> head(HashSize, -1);
    std::vector<int32_t> previous(WindowSize, -1);
    const size_t size = data.size();

    const auto hashAt = [&data](size_t position)
    {
        return int((uint32_t(data[position]) << 10 ^ uint32_t(data[position + 1]) << 5 ^ uint32_t(data[position + 2]))
            & uint32_t(HashSize - 1));
    };

    const auto insert = [&](size_t position)
    {
        if (position + 2 < size)
        {
            const int hash = hashAt(position);
            previous[position % WindowSize] = head[size_t(hash)];
            head[size_t(hash)] = int32_t(position);
        }
    };

    size_t position = 0;

    while (position < size)
    {
        int bestLength = 0;
        int bestDistance = 0;

        if (position + 2 < size)
        {
            int32_t candidate = head[size_t(hashAt(position))];
            int chain = 0;
            const size_t limit = std::min<size_t>(MaxMatch, size - position);

            while (candidate >= 0 && position - size_t(candidate) <= size_t(WindowSize) && chain < MaxChain)
            {
                size_t length = 0;

                while (length < limit && data[size_t(candidate) + length] == data[position + length])
                {
                    ++length;
                }

                if (int(length) > bestLength)
                {
                    bestLength = int(length);
                    bestDistance = int(position - size_t(candidate));

                    if (length == limit)
                    {
                        break;
                    }
                }

                const int32_t next = previous[size_t(candidate) % WindowSize];

                if (next >= candidate)
                {
                    break;
                }

                candidate = next;
                ++chain;
            }
        }

        if (bestLength >= 3)
        {
            writeMatch(writer, bestLength, bestDistance);

            for (int step = 0; step < bestLength; ++step)
            {
                insert(position + size_t(step));
            }

            position += size_t(bestLength);
        }
        else
        {
            writeLiteral(writer, data[position]);
            insert(position);
            ++position;
        }
    }

    writeLiteral(writer, 256);
    writer.flush();
    uint32_t adlerLow = 1;
    uint32_t adlerHigh = 0;

    for (const uint8_t value : data)
    {
        adlerLow = (adlerLow + value) % 65521;
        adlerHigh = (adlerHigh + adlerLow) % 65521;
    }

    appendBigEndian(out, (adlerHigh << 16) | adlerLow);
    return out;
}

std::vector<uint8_t> encodeRgbaPng(int width, int height, const std::vector<uint8_t> &rgba)
{
    std::vector<uint8_t> file = {0x89, 'P', 'N', 'G', 0x0d, 0x0a, 0x1a, 0x0a};
    std::vector<uint8_t> header;
    appendBigEndian(header, uint32_t(width));
    appendBigEndian(header, uint32_t(height));
    header.insert(header.end(), {8, 6, 0, 0, 0});
    appendChunk(file, "IHDR", header);
    const size_t stride = size_t(width) * 4;
    std::vector<uint8_t> raw;
    raw.reserve(size_t(height) * (stride + 1));
    std::array<std::vector<uint8_t>, 5> filtered;

    for (std::vector<uint8_t> &row : filtered)
    {
        row.resize(stride);
    }

    const std::vector<uint8_t> zeros(stride, 0);

    for (int row = 0; row < height; ++row)
    {
        const uint8_t *pRow = rgba.data() + size_t(row) * stride;
        const uint8_t *pUp = row > 0 ? pRow - stride : zeros.data();

        for (size_t index = 0; index < stride; ++index)
        {
            const int value = pRow[index];
            const int left = index >= 4 ? pRow[index - 4] : 0;
            const int up = pUp[index];
            const int upLeft = index >= 4 ? pUp[index - 4] : 0;
            filtered[0][index] = uint8_t(value);
            filtered[1][index] = uint8_t(value - left);
            filtered[2][index] = uint8_t(value - up);
            filtered[3][index] = uint8_t(value - ((left + up) >> 1));
            filtered[4][index] = uint8_t(value - paeth(left, up, upLeft));
        }

        // The filter whose bytes, read as signed, sum smallest; the lowest type on a tie.
        size_t best = 0;
        uint64_t bestSum = 0;

        for (size_t type = 0; type < filtered.size(); ++type)
        {
            uint64_t sum = 0;

            for (const uint8_t value : filtered[type])
            {
                sum += uint64_t(value < 128 ? value : 256 - value);
            }

            if (type == 0 || sum < bestSum)
            {
                best = type;
                bestSum = sum;
            }
        }

        raw.push_back(uint8_t(best));
        raw.insert(raw.end(), filtered[best].begin(), filtered[best].end());
    }

    appendChunk(file, "IDAT", deflateZlib(raw));
    appendChunk(file, "IEND", {});
    return file;
}
}
