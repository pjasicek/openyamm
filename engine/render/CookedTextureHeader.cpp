#include "engine/render/CookedTextureHeader.h"

#include <cstring>

namespace OpenYAMM::Engine
{
bool hasCookedTextureSignature(std::span<const uint8_t> bytes)
{
    uint64_t magic = 0;
    if (bytes.size() < sizeof(magic))
    {
        return false;
    }
    std::memcpy(&magic, bytes.data(), sizeof(magic));
    return magic == CookedTextureMagic;
}

std::optional<std::array<int, 2>> readCookedTextureSize(std::span<const uint8_t> bytes)
{
    if (bytes.size() < CookedTextureHeaderBytes || !hasCookedTextureSignature(bytes))
    {
        return std::nullopt;
    }

    // Header fields are 64-bit, in file byte order: the version second, width and height sixth and seventh.
    uint64_t fields[7] = {};
    std::memcpy(fields, bytes.data(), sizeof(fields));

    if (fields[1] != CookedTextureVersion || fields[5] == 0 || fields[6] == 0
        || fields[5] > uint64_t(CookedTextureSizeLimit) || fields[6] > uint64_t(CookedTextureSizeLimit))
    {
        return std::nullopt;
    }

    return std::array<int, 2>{int(fields[5]), int(fields[6])};
}
}
