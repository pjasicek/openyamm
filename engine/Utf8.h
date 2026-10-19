#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Engine
{
struct Utf8CodePoint
{
    uint32_t value = 0;
    size_t byteOffset = 0;
    size_t byteLength = 0;
};

// Decodes well-formed UTF-8. Invalid bytes are preserved as their unsigned byte
// value so legacy single-byte game tables remain readable during migration.
std::vector<Utf8CodePoint> decodeUtf8(std::string_view text);
Utf8CodePoint nextUtf8CodePoint(std::string_view text, size_t &offset);

size_t utf8Length(std::string_view text);
void eraseLastUtf8CodePoint(std::string &text);
std::string truncateUtf8(std::string_view text, size_t maximumCodePoints);
}
