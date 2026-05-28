#include "game/mm9/Mm9DtxTexture.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t Mm9DtxHeaderSize = 164;
constexpr size_t Mm9DtxSectionHeaderSize = 29;

template <typename ValueType>
ValueType readLittleEndianValue(const std::vector<uint8_t> &bytes, size_t offset)
{
    ValueType value = {};
    std::memcpy(&value, bytes.data() + offset, sizeof(ValueType));
    return value;
}

std::vector<uint8_t> readBinaryFile(const std::filesystem::path &path)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        return {};
    }

    return std::vector<uint8_t>(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
}

std::string readFixedString(const std::vector<uint8_t> &bytes, size_t offset, size_t maxLength)
{
    size_t length = 0;

    while (length < maxLength && bytes[offset + length] != '\0')
    {
        ++length;
    }

    return std::string(reinterpret_cast<const char *>(bytes.data() + offset), length);
}

std::optional<size_t> mm9DtxMipPayloadSize(uint8_t bpp, uint32_t width, uint32_t height, bool cubeMap)
{
    size_t size = 0;

    if (bpp == Mm9DtxBpp8P || bpp == Mm9DtxBpp32)
    {
        size = static_cast<size_t>(width) * static_cast<size_t>(height) * 4u;
    }
    else if (bpp == Mm9DtxBppDxt1)
    {
        size = (static_cast<size_t>(width) * static_cast<size_t>(height)) / 2u;
    }
    else if (bpp == Mm9DtxBppDxt3 || bpp == Mm9DtxBppDxt5)
    {
        size = static_cast<size_t>(width) * static_cast<size_t>(height);
    }
    else
    {
        return std::nullopt;
    }

    if (cubeMap)
    {
        size *= 6u;
    }

    return size;
}

uint8_t expand5To8(uint16_t value)
{
    return static_cast<uint8_t>((value * 255u) / 31u);
}

uint8_t expand6To8(uint16_t value)
{
    return static_cast<uint8_t>((value * 255u) / 63u);
}

std::array<uint8_t, 4> rgb565ToBgra(uint16_t value)
{
    const uint8_t red = expand5To8((value >> 11) & 0x1fu);
    const uint8_t green = expand6To8((value >> 5) & 0x3fu);
    const uint8_t blue = expand5To8(value & 0x1fu);
    return {blue, green, red, 255};
}

std::array<std::array<uint8_t, 4>, 4> decodeDxtColors(const uint8_t *pBlock)
{
    const uint16_t color0 = static_cast<uint16_t>(pBlock[0] | (pBlock[1] << 8));
    const uint16_t color1 = static_cast<uint16_t>(pBlock[2] | (pBlock[3] << 8));
    std::array<std::array<uint8_t, 4>, 4> colors = {};
    colors[0] = rgb565ToBgra(color0);
    colors[1] = rgb565ToBgra(color1);

    if (color0 > color1)
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            colors[2][channel] = static_cast<uint8_t>((2u * colors[0][channel] + colors[1][channel]) / 3u);
            colors[3][channel] = static_cast<uint8_t>((colors[0][channel] + 2u * colors[1][channel]) / 3u);
        }
        colors[2][3] = 255;
        colors[3][3] = 255;
    }
    else
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            colors[2][channel] = static_cast<uint8_t>((colors[0][channel] + colors[1][channel]) / 2u);
        }
        colors[2][3] = 255;
        colors[3] = {0, 0, 0, 0};
    }

    return colors;
}

std::vector<uint8_t> decodeDxt1Bgra(const uint8_t *pPayload, size_t payloadSize, int width, int height)
{
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4u, 0);
    const int blocksX = (width + 3) / 4;
    const int blocksY = (height + 3) / 4;
    size_t offset = 0;

    for (int blockY = 0; blockY < blocksY; ++blockY)
    {
        for (int blockX = 0; blockX < blocksX; ++blockX)
        {
            if (offset + 8 > payloadSize)
            {
                return pixels;
            }

            const uint8_t *pBlock = pPayload + offset;
            offset += 8;
            const std::array<std::array<uint8_t, 4>, 4> colors = decodeDxtColors(pBlock);
            const uint32_t indices =
                static_cast<uint32_t>(pBlock[4])
                | (static_cast<uint32_t>(pBlock[5]) << 8)
                | (static_cast<uint32_t>(pBlock[6]) << 16)
                | (static_cast<uint32_t>(pBlock[7]) << 24);

            for (int row = 0; row < 4; ++row)
            {
                for (int col = 0; col < 4; ++col)
                {
                    const int x = blockX * 4 + col;
                    const int y = blockY * 4 + row;

                    if (x >= width || y >= height)
                    {
                        continue;
                    }

                    const size_t pixelOffset = (static_cast<size_t>(y) * width + x) * 4u;
                    const std::array<uint8_t, 4> &color = colors[(indices >> (2 * (row * 4 + col))) & 0x03u];
                    std::copy(color.begin(), color.end(), pixels.begin() + static_cast<std::ptrdiff_t>(pixelOffset));
                }
            }
        }
    }

    return pixels;
}

std::array<uint8_t, 16> decodeDxt5Alpha(const uint8_t *pBlock)
{
    std::array<uint8_t, 8> alphaTable = {};
    alphaTable[0] = pBlock[0];
    alphaTable[1] = pBlock[1];

    if (alphaTable[0] > alphaTable[1])
    {
        for (uint8_t index = 1; index < 7; ++index)
        {
            alphaTable[index + 1] =
                static_cast<uint8_t>(((7u - index) * alphaTable[0] + index * alphaTable[1]) / 7u);
        }
    }
    else
    {
        for (uint8_t index = 1; index < 5; ++index)
        {
            alphaTable[index + 1] =
                static_cast<uint8_t>(((5u - index) * alphaTable[0] + index * alphaTable[1]) / 5u);
        }
        alphaTable[6] = 0;
        alphaTable[7] = 255;
    }

    uint64_t alphaBits = 0;
    for (size_t byteIndex = 0; byteIndex < 6; ++byteIndex)
    {
        alphaBits |= static_cast<uint64_t>(pBlock[2 + byteIndex]) << (8 * byteIndex);
    }

    std::array<uint8_t, 16> alphas = {};
    for (size_t index = 0; index < alphas.size(); ++index)
    {
        alphas[index] = alphaTable[(alphaBits >> (3 * index)) & 0x07u];
    }

    return alphas;
}

std::vector<uint8_t> decodeDxt3Bgra(const uint8_t *pPayload, size_t payloadSize, int width, int height)
{
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4u, 0);
    const int blocksX = (width + 3) / 4;
    const int blocksY = (height + 3) / 4;
    size_t offset = 0;

    for (int blockY = 0; blockY < blocksY; ++blockY)
    {
        for (int blockX = 0; blockX < blocksX; ++blockX)
        {
            if (offset + 16 > payloadSize)
            {
                return pixels;
            }

            const uint8_t *pBlock = pPayload + offset;
            offset += 16;
            const std::array<std::array<uint8_t, 4>, 4> colors = decodeDxtColors(pBlock + 8);
            const uint32_t indices =
                static_cast<uint32_t>(pBlock[12])
                | (static_cast<uint32_t>(pBlock[13]) << 8)
                | (static_cast<uint32_t>(pBlock[14]) << 16)
                | (static_cast<uint32_t>(pBlock[15]) << 24);

            for (int row = 0; row < 4; ++row)
            {
                const uint16_t alphaRow = static_cast<uint16_t>(pBlock[row * 2] | (pBlock[row * 2 + 1] << 8));
                for (int col = 0; col < 4; ++col)
                {
                    const int x = blockX * 4 + col;
                    const int y = blockY * 4 + row;

                    if (x >= width || y >= height)
                    {
                        continue;
                    }

                    const size_t localIndex = static_cast<size_t>(row * 4 + col);
                    std::array<uint8_t, 4> color = colors[(indices >> (2 * localIndex)) & 0x03u];
                    const uint8_t alpha4 = static_cast<uint8_t>((alphaRow >> (col * 4)) & 0x0fu);
                    color[3] = static_cast<uint8_t>(alpha4 * 17u);
                    const size_t pixelOffset = (static_cast<size_t>(y) * width + x) * 4u;
                    std::copy(color.begin(), color.end(), pixels.begin() + static_cast<std::ptrdiff_t>(pixelOffset));
                }
            }
        }
    }

    return pixels;
}

std::vector<uint8_t> decodeDxt5Bgra(const uint8_t *pPayload, size_t payloadSize, int width, int height)
{
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4u, 0);
    const int blocksX = (width + 3) / 4;
    const int blocksY = (height + 3) / 4;
    size_t offset = 0;

    for (int blockY = 0; blockY < blocksY; ++blockY)
    {
        for (int blockX = 0; blockX < blocksX; ++blockX)
        {
            if (offset + 16 > payloadSize)
            {
                return pixels;
            }

            const uint8_t *pBlock = pPayload + offset;
            offset += 16;
            const std::array<uint8_t, 16> alphas = decodeDxt5Alpha(pBlock);
            const std::array<std::array<uint8_t, 4>, 4> colors = decodeDxtColors(pBlock + 8);
            const uint32_t indices =
                static_cast<uint32_t>(pBlock[12])
                | (static_cast<uint32_t>(pBlock[13]) << 8)
                | (static_cast<uint32_t>(pBlock[14]) << 16)
                | (static_cast<uint32_t>(pBlock[15]) << 24);

            for (int row = 0; row < 4; ++row)
            {
                for (int col = 0; col < 4; ++col)
                {
                    const int x = blockX * 4 + col;
                    const int y = blockY * 4 + row;

                    if (x >= width || y >= height)
                    {
                        continue;
                    }

                    const size_t localIndex = static_cast<size_t>(row * 4 + col);
                    std::array<uint8_t, 4> color = colors[(indices >> (2 * localIndex)) & 0x03u];
                    color[3] = alphas[localIndex];
                    const size_t pixelOffset = (static_cast<size_t>(y) * width + x) * 4u;
                    std::copy(color.begin(), color.end(), pixels.begin() + static_cast<std::ptrdiff_t>(pixelOffset));
                }
            }
        }
    }

    return pixels;
}
}

std::optional<Mm9DtxHeader> parseMm9DtxHeader(
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage)
{
    errorMessage.clear();

    if (bytes.size() < Mm9DtxHeaderSize)
    {
        errorMessage = "DTX file is too small";
        return std::nullopt;
    }

    Mm9DtxHeader header = {};
    header.resourceType = readLittleEndianValue<int32_t>(bytes, 0);
    header.version = readLittleEndianValue<int32_t>(bytes, 4);
    header.width = readLittleEndianValue<uint16_t>(bytes, 8);
    header.height = readLittleEndianValue<uint16_t>(bytes, 10);
    header.mipmapCount = readLittleEndianValue<uint16_t>(bytes, 12);
    header.sectionCount = readLittleEndianValue<uint16_t>(bytes, 14);
    header.flags = readLittleEndianValue<int32_t>(bytes, 16);
    header.userFlags = readLittleEndianValue<int32_t>(bytes, 20);
    header.textureGroup = bytes[24];
    header.mipmapsUsed = bytes[25] != 0 ? bytes[25] : static_cast<uint8_t>(header.mipmapCount);
    header.bpp = bytes[26];
    header.nonS3tcOffset = bytes[27];
    header.uiMipmapOffset = bytes[28];
    header.texturePriority = readLittleEndianValue<int8_t>(bytes, 29);
    header.detailScale = readLittleEndianValue<float>(bytes, 30);
    header.detailAngle = readLittleEndianValue<int16_t>(bytes, 34);

    const char *pCommandStart = reinterpret_cast<const char *>(bytes.data() + 36);
    size_t commandLength = 0;

    while (commandLength < 128 && pCommandStart[commandLength] != '\0')
    {
        ++commandLength;
    }

    header.commandString.assign(pCommandStart, commandLength);

    if (header.resourceType != Mm9DtxResourceType
        || header.version != Mm9DtxVersionV2
        || header.width == 0
        || header.height == 0)
    {
        errorMessage = "file is not an MM9 DTX v2 texture";
        return std::nullopt;
    }

    return header;
}

std::optional<Mm9DtxLayout> parseMm9DtxLayout(
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage)
{
    const std::optional<Mm9DtxHeader> header = parseMm9DtxHeader(bytes, errorMessage);

    if (!header)
    {
        return std::nullopt;
    }

    const bool cubeMap = (header->flags & Mm9DtxFlagCubemap) != 0;
    size_t payloadOffset = Mm9DtxHeaderSize;
    uint32_t mipWidth = header->width;
    uint32_t mipHeight = header->height;
    Mm9DtxLayout layout = {};
    layout.header = *header;
    layout.mips.reserve(header->mipmapCount);
    layout.sections.reserve(header->sectionCount);

    for (size_t level = 0; level < header->mipmapCount; ++level)
    {
        const std::optional<size_t> payloadSize =
            mm9DtxMipPayloadSize(header->bpp, mipWidth, mipHeight, cubeMap);

        if (!payloadSize)
        {
            errorMessage = "unsupported MM9 DTX bpp: " + std::to_string(static_cast<int>(header->bpp));
            return std::nullopt;
        }

        Mm9DtxMipLevel mip = {};
        mip.level = level;
        mip.width = mipWidth;
        mip.height = mipHeight;
        mip.payloadOffset = payloadOffset;
        mip.payloadSize = *payloadSize;
        mip.payloadAvailable = payloadOffset <= bytes.size() && *payloadSize <= bytes.size() - payloadOffset;
        layout.mips.push_back(mip);

        if (!mip.payloadAvailable)
        {
            errorMessage = "DTX mip payload is truncated";
            return std::nullopt;
        }

        payloadOffset += *payloadSize;
        mipWidth = std::max<uint32_t>(1, mipWidth / 2u);
        mipHeight = std::max<uint32_t>(1, mipHeight / 2u);
    }

    for (size_t sectionIndex = 0; sectionIndex < header->sectionCount; ++sectionIndex)
    {
        if (payloadOffset + Mm9DtxSectionHeaderSize > bytes.size())
        {
            errorMessage = "DTX section header is truncated";
            return std::nullopt;
        }

        Mm9DtxSection section = {};
        section.sectionIndex = sectionIndex;
        section.type = readFixedString(bytes, payloadOffset, 15);
        section.name = readFixedString(bytes, payloadOffset + 15, 10);
        section.payloadSize = readLittleEndianValue<uint32_t>(bytes, payloadOffset + 25);
        section.payloadOffset = payloadOffset + Mm9DtxSectionHeaderSize;
        section.payloadAvailable =
            section.payloadOffset <= bytes.size() && section.payloadSize <= bytes.size() - section.payloadOffset;

        if (!section.payloadAvailable)
        {
            errorMessage = "DTX section payload is truncated";
            return std::nullopt;
        }

        layout.sections.push_back(section);
        payloadOffset = section.payloadOffset + section.payloadSize;
    }

    if (payloadOffset < bytes.size())
    {
        layout.trailingBytes = bytes.size() - payloadOffset;
    }

    return layout;
}

std::optional<Mm9DtxTexture> decodeMm9DtxTexture(
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage)
{
    return decodeMm9DtxMipTexture(bytes, 0, errorMessage);
}

std::optional<Mm9DtxTexture> decodeMm9DtxMipTexture(
    const std::vector<uint8_t> &bytes,
    size_t mipLevel,
    std::string &errorMessage)
{
    const std::optional<Mm9DtxLayout> layout = parseMm9DtxLayout(bytes, errorMessage);

    if (!layout)
    {
        return std::nullopt;
    }

    if (mipLevel >= layout->mips.size())
    {
        errorMessage = "DTX mip level is out of range";
        return std::nullopt;
    }

    if (layout->mips.empty())
    {
        errorMessage = "DTX file has no mip payloads";
        return std::nullopt;
    }

    const Mm9DtxHeader &header = layout->header;
    const Mm9DtxMipLevel &mip = layout->mips[mipLevel];
    const uint8_t *pPayload = bytes.data() + mip.payloadOffset;
    const size_t payloadSize = mip.payloadSize;
    const int width = static_cast<int>(mip.width);
    const int height = static_cast<int>(mip.height);
    Mm9DtxTexture texture = {};
    texture.header = header;
    texture.mipLevel = mipLevel;
    texture.width = mip.width;
    texture.height = mip.height;

    if (header.bpp == Mm9DtxBpp8P || header.bpp == Mm9DtxBpp32)
    {
        const size_t expectedBytes = static_cast<size_t>(width) * static_cast<size_t>(height) * 4u;
        if (payloadSize < expectedBytes)
        {
            errorMessage = "DTX BGRA texture payload is truncated";
            return std::nullopt;
        }

        texture.pixelsBgra.assign(pPayload, pPayload + expectedBytes);

        bool allAlphaZero = header.bpp == Mm9DtxBpp32;

        if (allAlphaZero)
        {
            for (size_t offset = 3; offset < texture.pixelsBgra.size(); offset += 4)
            {
                if (texture.pixelsBgra[offset] != 0)
                {
                    allAlphaZero = false;
                    break;
                }
            }
        }

        if (header.bpp == Mm9DtxBpp8P || allAlphaZero)
        {
            for (size_t offset = 3; offset < texture.pixelsBgra.size(); offset += 4)
            {
                texture.pixelsBgra[offset] = 255;
            }
        }

        texture.decodeMode = header.bpp == Mm9DtxBpp8P ? "bgra8p" : "bgra32";
        return texture;
    }

    if (header.bpp == Mm9DtxBppDxt1)
    {
        texture.pixelsBgra = decodeDxt1Bgra(pPayload, payloadSize, width, height);
        texture.decodeMode = "dxt1";
        return texture;
    }

    if (header.bpp == Mm9DtxBppDxt3)
    {
        texture.pixelsBgra = decodeDxt3Bgra(pPayload, payloadSize, width, height);
        texture.decodeMode = "dxt3";
        return texture;
    }

    if (header.bpp == Mm9DtxBppDxt5)
    {
        texture.pixelsBgra = decodeDxt5Bgra(pPayload, payloadSize, width, height);
        texture.decodeMode = "dxt5";
        return texture;
    }

    errorMessage = "unsupported MM9 DTX bpp: " + std::to_string(static_cast<int>(header.bpp));
    return std::nullopt;
}

std::optional<Mm9DtxTexture> loadMm9DtxTexture(
    const std::filesystem::path &path,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::vector<uint8_t> bytes = readBinaryFile(path);

    if (bytes.empty())
    {
        errorMessage = "could not read DTX file: " + path.generic_string();
        return std::nullopt;
    }

    std::optional<Mm9DtxTexture> texture = decodeMm9DtxTexture(bytes, errorMessage);

    if (!texture && !errorMessage.empty())
    {
        errorMessage += ": " + path.generic_string();
    }

    return texture;
}
}
