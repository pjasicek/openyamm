#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace OpenYAMM::Engine
{
// What identifies a cooked texture (.oytex, CookedTexture.h) and what its header says without its blocks. In its own
// header and source file, free of the renderer's headers, so that code which only needs to recognise a cooked
// texture or know its size (asset lookups, tools) builds and links without bgfx and bimg.

// "OYTEX001" in file byte order.
constexpr uint64_t CookedTextureMagic = 0x313030584554594full;
constexpr uint32_t CookedTextureVersion = 3;
constexpr size_t CookedTextureHeaderBytes = 120;
constexpr int CookedTextureSizeLimit = 8192;

bool hasCookedTextureSignature(std::span<const uint8_t> bytes);
// Width and height of a cooked texture's top level; nothing when the bytes are not a cooked texture of the current
// version.
std::optional<std::array<int, 2>> readCookedTextureSize(std::span<const uint8_t> bytes);
}
