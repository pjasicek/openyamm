#pragma once

#include <cstdint>
#include <vector>

namespace OpenYAMM::Studio
{
// An 8-bit RGBA PNG of `rgba` (width x height x 4 bytes, rows from the top), compressed: each row with the filter
// of the five whose bytes sum smallest (as libpng chooses), deflated with the fixed codes and a greedy LZ77 search.
// The same input always gives the same bytes, on every target. Weight images (core/GroundTerrain) are mostly flat,
// so they shrink to a few hundred kilobytes where stored blocks would take 16 MB.
std::vector<uint8_t> encodeRgbaPng(int width, int height, const std::vector<uint8_t> &rgba);

// The zlib stream of `data` as encodeRgbaPng writes it (for tests).
std::vector<uint8_t> deflateZlib(const std::vector<uint8_t> &data);
}
