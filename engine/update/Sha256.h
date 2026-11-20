#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>

namespace OpenYAMM::Engine
{
// Streaming SHA-256 (FIPS 180-4), used to check downloaded update files against their signed manifest.
class Sha256
{
public:
    Sha256();
    void update(const void *pData, size_t size);
    // The digest as 64 lowercase hex characters. Call once, after the last update.
    std::string finishHex();

private:
    void processBlock(const uint8_t *pBlock);

    std::array<uint32_t, 8> m_state;
    std::array<uint8_t, 64> m_buffer = {};
    size_t m_bufferSize = 0;
    uint64_t m_totalBytes = 0;
};

std::string sha256Hex(const void *pData, size_t size);
// Empty when the file cannot be read.
std::optional<std::string> sha256File(const std::filesystem::path &path);
}
