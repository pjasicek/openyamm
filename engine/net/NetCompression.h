#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace OpenYAMM::Engine
{
// The bytes of a network message, made smaller (zstd) and made whole again.
std::vector<uint8_t> packBytes(std::span<const uint8_t> bytes);
// Nothing when the bytes are not packed ones, or when they would unpack to more than maxLength bytes.
std::optional<std::vector<uint8_t>> unpackBytes(std::span<const uint8_t> packed, size_t maxLength);
}
