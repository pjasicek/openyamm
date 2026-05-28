#pragma once

#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
constexpr int Mm9DtxResourceType = 0;
constexpr int Mm9DtxVersionV2 = -5;
constexpr uint8_t Mm9DtxBpp8P = 0;
constexpr uint8_t Mm9DtxBpp32 = 3;
constexpr uint8_t Mm9DtxBppDxt1 = 4;
constexpr uint8_t Mm9DtxBppDxt3 = 5;
constexpr uint8_t Mm9DtxBppDxt5 = 6;
constexpr int32_t Mm9DtxFlagCubemap = 1 << 10;

struct Mm9DtxHeader
{
    int32_t resourceType = 0;
    int32_t version = 0;
    uint16_t width = 0;
    uint16_t height = 0;
    uint16_t mipmapCount = 0;
    uint16_t sectionCount = 0;
    int32_t flags = 0;
    int32_t userFlags = 0;
    uint8_t textureGroup = 0;
    uint8_t mipmapsUsed = 0;
    uint8_t bpp = 0;
    uint8_t nonS3tcOffset = 0;
    uint8_t uiMipmapOffset = 0;
    int8_t texturePriority = 0;
    float detailScale = 0.0f;
    int16_t detailAngle = 0;
    std::string commandString;
};

struct Mm9DtxTexture
{
    Mm9DtxHeader header;
    size_t mipLevel = 0;
    uint32_t width = 0;
    uint32_t height = 0;
    std::vector<uint8_t> pixelsBgra;
    std::string decodeMode;
};

struct Mm9DtxMipLevel
{
    size_t level = 0;
    uint32_t width = 0;
    uint32_t height = 0;
    size_t payloadOffset = 0;
    size_t payloadSize = 0;
    bool payloadAvailable = false;
};

struct Mm9DtxSection
{
    size_t sectionIndex = 0;
    std::string type;
    std::string name;
    size_t payloadOffset = 0;
    size_t payloadSize = 0;
    bool payloadAvailable = false;
};

struct Mm9DtxLayout
{
    Mm9DtxHeader header;
    std::vector<Mm9DtxMipLevel> mips;
    std::vector<Mm9DtxSection> sections;
    size_t trailingBytes = 0;
};

std::optional<Mm9DtxHeader> parseMm9DtxHeader(
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage);

std::optional<Mm9DtxLayout> parseMm9DtxLayout(
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage);

std::optional<Mm9DtxTexture> decodeMm9DtxTexture(
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage);

std::optional<Mm9DtxTexture> decodeMm9DtxMipTexture(
    const std::vector<uint8_t> &bytes,
    size_t mipLevel,
    std::string &errorMessage);

std::optional<Mm9DtxTexture> loadMm9DtxTexture(
    const std::filesystem::path &path,
    std::string &errorMessage);
}
