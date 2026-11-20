#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

// Building blocks shared by the outdoor (ODM) and indoor (BLV) baked lighting sidecars: little-endian readers, the
// RLE page payload of RGBM texels, the content hash that names the baked geometry and the dependency path rule.
// See tools/lighting/baked_outdoors/FORMAT.md and devdocs/INDOOR_BAKED_LIGHTING.md.
namespace OpenYAMM::Game::BakedLightingFormat
{
uint16_t readU16(const std::vector<uint8_t> &bytes, size_t offset);
uint32_t readU32(const std::vector<uint8_t> &bytes, size_t offset);
uint64_t readU64(const std::vector<uint8_t> &bytes, size_t offset);
float readFloat(const std::vector<uint8_t> &bytes, size_t offset);

// Decodes `byteCount` bytes of BGRM spans at `offset` (a tag byte: low seven bits are the span length minus one; a set
// high bit repeats the following texel, a clear one is followed by that many literal texels). The spans must end
// exactly at the byte count and produce exactly `expectedPixelCount` texels. pPixels may be null to validate only.
bool decodeRle(
    const std::vector<uint8_t> &bytes,
    size_t offset,
    size_t byteCount,
    size_t expectedPixelCount,
    std::vector<uint32_t> *pPixels);

// FNV-1a 64 of the native map bytes: the identity a bake records for the geometry it was made from.
uint64_t contentHash(const std::vector<uint8_t> &bytes);

// A recorded source: rooted at engine/ or worlds/ (or the archived original sprites), no parent traversal,
// backslashes or NULs.
bool validDependencyPath(const std::string &path);
}
