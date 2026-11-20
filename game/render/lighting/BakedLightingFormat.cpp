#include "game/render/lighting/BakedLightingFormat.h"

#include <cstring>

namespace OpenYAMM::Game::BakedLightingFormat
{
uint16_t readU16(const std::vector<uint8_t> &bytes, size_t offset)
{
    return static_cast<uint16_t>(bytes[offset]) | (static_cast<uint16_t>(bytes[offset + 1]) << 8);
}

uint32_t readU32(const std::vector<uint8_t> &bytes, size_t offset)
{
    return static_cast<uint32_t>(bytes[offset])
        | (static_cast<uint32_t>(bytes[offset + 1]) << 8)
        | (static_cast<uint32_t>(bytes[offset + 2]) << 16)
        | (static_cast<uint32_t>(bytes[offset + 3]) << 24);
}

uint64_t readU64(const std::vector<uint8_t> &bytes, size_t offset)
{
    return static_cast<uint64_t>(readU32(bytes, offset))
        | (static_cast<uint64_t>(readU32(bytes, offset + 4)) << 32);
}

float readFloat(const std::vector<uint8_t> &bytes, size_t offset)
{
    const uint32_t bits = readU32(bytes, offset);
    float value = 0.0f;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

bool decodeRle(
    const std::vector<uint8_t> &bytes,
    size_t offset,
    size_t byteCount,
    size_t expectedPixelCount,
    std::vector<uint32_t> *pPixels)
{
    if (offset > bytes.size() || byteCount > bytes.size() - offset)
    {
        return false;
    }

    const size_t end = offset + byteCount;
    size_t decodedPixelCount = 0;
    if (pPixels != nullptr)
    {
        pPixels->reserve(expectedPixelCount);
    }
    while (offset < end && decodedPixelCount < expectedPixelCount)
    {
        const uint8_t tag = bytes[offset++];
        const size_t spanLength = size_t(tag & 0x7f) + 1;
        if (spanLength > expectedPixelCount - decodedPixelCount)
        {
            return false;
        }
        if ((tag & 0x80) != 0)
        {
            if (end - offset < sizeof(uint32_t))
            {
                return false;
            }
            const uint32_t pixel = readU32(bytes, offset);
            offset += sizeof(uint32_t);
            if (pPixels != nullptr)
            {
                pPixels->insert(pPixels->end(), spanLength, pixel);
            }
        }
        else
        {
            const size_t spanBytes = spanLength * sizeof(uint32_t);
            if (end - offset < spanBytes)
            {
                return false;
            }
            if (pPixels != nullptr)
            {
                for (size_t index = 0; index < spanLength; ++index)
                {
                    pPixels->push_back(readU32(bytes, offset + index * sizeof(uint32_t)));
                }
            }
            offset += spanBytes;
        }
        decodedPixelCount += spanLength;
    }
    return offset == end && decodedPixelCount == expectedPixelCount;
}

uint64_t contentHash(const std::vector<uint8_t> &bytes)
{
    uint64_t value = 14695981039346656037ULL;

    for (uint8_t byte : bytes)
    {
        value ^= byte;
        value *= 1099511628211ULL;
    }

    return value;
}

bool validDependencyPath(const std::string &path)
{
    return (path.starts_with("worlds/") || path.starts_with("engine/")
            || path.starts_with("_legacy/sprites_original/"))
        && path.find("..") == std::string::npos && path.find('\\') == std::string::npos
        && path.find('\0') == std::string::npos;
}
}
