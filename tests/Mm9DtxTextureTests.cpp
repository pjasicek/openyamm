#include "doctest/doctest.h"

#include "game/mm9/Mm9DtxTexture.h"

#include <algorithm>
#include <cstring>
#include <optional>
#include <string>
#include <vector>

namespace
{
template <typename ValueType>
void writeLittleEndianValue(std::vector<uint8_t> &bytes, size_t offset, ValueType value)
{
    std::memcpy(bytes.data() + offset, &value, sizeof(ValueType));
}

std::vector<uint8_t> makeDtxBytes(
    uint16_t width,
    uint16_t height,
    uint8_t bpp,
    const std::vector<uint8_t> &payload,
    uint16_t mipmapCount = 1,
    uint16_t sectionCount = 0)
{
    std::vector<uint8_t> bytes(164 + payload.size(), 0);
    writeLittleEndianValue<int32_t>(bytes, 0, OpenYAMM::Game::Mm9DtxResourceType);
    writeLittleEndianValue<int32_t>(bytes, 4, OpenYAMM::Game::Mm9DtxVersionV2);
    writeLittleEndianValue<uint16_t>(bytes, 8, width);
    writeLittleEndianValue<uint16_t>(bytes, 10, height);
    writeLittleEndianValue<uint16_t>(bytes, 12, mipmapCount);
    writeLittleEndianValue<uint16_t>(bytes, 14, sectionCount);
    writeLittleEndianValue<int32_t>(bytes, 16, 8);
    writeLittleEndianValue<int32_t>(bytes, 20, 12);
    bytes[24] = 2;
    bytes[25] = static_cast<uint8_t>(mipmapCount);
    bytes[26] = bpp;
    bytes[27] = 0;
    bytes[28] = 0;
    writeLittleEndianValue<float>(bytes, 30, 5.0f);
    writeLittleEndianValue<int16_t>(bytes, 34, 45);

    const std::string command = "DetailTex Textures\\detailtextures\\det_01.dtx";
    std::memcpy(bytes.data() + 36, command.data(), command.size());
    std::memcpy(bytes.data() + 164, payload.data(), payload.size());
    return bytes;
}

void appendDtxSection(
    std::vector<uint8_t> &bytes,
    const std::string &type,
    const std::string &name,
    const std::vector<uint8_t> &payload)
{
    const size_t offset = bytes.size();
    bytes.resize(bytes.size() + 29 + payload.size(), 0);
    std::memcpy(bytes.data() + offset, type.data(), std::min<size_t>(type.size(), 15));
    std::memcpy(bytes.data() + offset + 15, name.data(), std::min<size_t>(name.size(), 10));
    writeLittleEndianValue<uint32_t>(bytes, offset + 25, static_cast<uint32_t>(payload.size()));
    std::memcpy(bytes.data() + offset + 29, payload.data(), payload.size());
}
}

TEST_CASE("MM9 DTX parser preserves v2 header metadata")
{
    const std::vector<uint8_t> bytes =
        makeDtxBytes(8, 4, OpenYAMM::Game::Mm9DtxBpp32, std::vector<uint8_t>(8 * 4 * 4, 0xff));
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9DtxHeader> header =
        OpenYAMM::Game::parseMm9DtxHeader(bytes, errorMessage);

    REQUIRE_MESSAGE(header.has_value(), errorMessage.c_str());
    CHECK(header->resourceType == OpenYAMM::Game::Mm9DtxResourceType);
    CHECK(header->version == OpenYAMM::Game::Mm9DtxVersionV2);
    CHECK(header->width == 8);
    CHECK(header->height == 4);
    CHECK(header->mipmapCount == 1);
    CHECK(header->flags == 8);
    CHECK(header->userFlags == 12);
    CHECK(header->textureGroup == 2);
    CHECK(header->mipmapsUsed == 1);
    CHECK(header->bpp == OpenYAMM::Game::Mm9DtxBpp32);
    CHECK(header->detailScale == doctest::Approx(5.0f));
    CHECK(header->detailAngle == 45);
    CHECK(header->commandString == "DetailTex Textures\\detailtextures\\det_01.dtx");
}

TEST_CASE("MM9 DTX decoder preserves raw BGRA32 pixels")
{
    const std::vector<uint8_t> payload = {
        10, 20, 30, 40,
        50, 60, 70, 80,
        90, 100, 110, 120,
        130, 140, 150, 160,
    };
    const std::vector<uint8_t> bytes = makeDtxBytes(2, 2, OpenYAMM::Game::Mm9DtxBpp32, payload);
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9DtxTexture> texture =
        OpenYAMM::Game::decodeMm9DtxTexture(bytes, errorMessage);

    REQUIRE_MESSAGE(texture.has_value(), errorMessage.c_str());
    CHECK(texture->header.width == 2);
    CHECK(texture->header.height == 2);
    CHECK(texture->mipLevel == 0);
    CHECK(texture->width == 2);
    CHECK(texture->height == 2);
    CHECK(texture->decodeMode == "bgra32");
    CHECK(texture->pixelsBgra == payload);
}

TEST_CASE("MM9 DTX decoder decodes selected raw mip level")
{
    const std::vector<uint8_t> mip0(4 * 4 * 4, 1);
    const std::vector<uint8_t> mip1 = {
        10, 20, 30, 40,
        50, 60, 70, 80,
        90, 100, 110, 120,
        130, 140, 150, 160,
    };
    const std::vector<uint8_t> mip2 = {
        210, 220, 230, 240,
    };
    std::vector<uint8_t> payload;
    payload.insert(payload.end(), mip0.begin(), mip0.end());
    payload.insert(payload.end(), mip1.begin(), mip1.end());
    payload.insert(payload.end(), mip2.begin(), mip2.end());

    const std::vector<uint8_t> bytes = makeDtxBytes(4, 4, OpenYAMM::Game::Mm9DtxBpp32, payload, 3);
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9DtxTexture> texture =
        OpenYAMM::Game::decodeMm9DtxMipTexture(bytes, 1, errorMessage);

    REQUIRE_MESSAGE(texture.has_value(), errorMessage.c_str());
    CHECK(texture->header.width == 4);
    CHECK(texture->header.height == 4);
    CHECK(texture->mipLevel == 1);
    CHECK(texture->width == 2);
    CHECK(texture->height == 2);
    CHECK(texture->decodeMode == "bgra32");
    CHECK(texture->pixelsBgra == mip1);
}

TEST_CASE("MM9 DTX layout enumerates mip payloads and sections")
{
    std::vector<uint8_t> payload(4 * 4 * 4 + 2 * 2 * 4 + 1 * 1 * 4, 0x7f);
    std::vector<uint8_t> bytes =
        makeDtxBytes(4, 4, OpenYAMM::Game::Mm9DtxBpp32, payload, 3, 1);
    appendDtxSection(bytes, "Command", "Water", {1, 2, 3, 4, 5});

    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9DtxLayout> layout =
        OpenYAMM::Game::parseMm9DtxLayout(bytes, errorMessage);

    REQUIRE_MESSAGE(layout.has_value(), errorMessage.c_str());
    REQUIRE(layout->mips.size() == 3);
    CHECK(layout->mips[0].level == 0);
    CHECK(layout->mips[0].width == 4);
    CHECK(layout->mips[0].height == 4);
    CHECK(layout->mips[0].payloadOffset == 164);
    CHECK(layout->mips[0].payloadSize == 64);
    CHECK(layout->mips[0].payloadAvailable);
    CHECK(layout->mips[1].width == 2);
    CHECK(layout->mips[1].height == 2);
    CHECK(layout->mips[1].payloadOffset == 228);
    CHECK(layout->mips[1].payloadSize == 16);
    CHECK(layout->mips[2].width == 1);
    CHECK(layout->mips[2].height == 1);
    CHECK(layout->mips[2].payloadOffset == 244);
    CHECK(layout->mips[2].payloadSize == 4);
    REQUIRE(layout->sections.size() == 1);
    CHECK(layout->sections[0].sectionIndex == 0);
    CHECK(layout->sections[0].type == "Command");
    CHECK(layout->sections[0].name == "Water");
    CHECK(layout->sections[0].payloadOffset == 277);
    CHECK(layout->sections[0].payloadSize == 5);
    CHECK(layout->sections[0].payloadAvailable);
    CHECK(layout->trailingBytes == 0);
}

TEST_CASE("MM9 DTX decoder treats all-zero BGRA32 alpha as opaque")
{
    const std::vector<uint8_t> payload = {
        10, 20, 30, 0,
        50, 60, 70, 0,
        90, 100, 110, 0,
        130, 140, 150, 0,
    };
    const std::vector<uint8_t> bytes = makeDtxBytes(2, 2, OpenYAMM::Game::Mm9DtxBpp32, payload);
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9DtxTexture> texture =
        OpenYAMM::Game::decodeMm9DtxTexture(bytes, errorMessage);

    REQUIRE_MESSAGE(texture.has_value(), errorMessage.c_str());
    CHECK(texture->pixelsBgra[3] == 255);
    CHECK(texture->pixelsBgra[7] == 255);
    CHECK(texture->pixelsBgra[11] == 255);
    CHECK(texture->pixelsBgra[15] == 255);
}

TEST_CASE("MM9 DTX decoder expands DXT1 blocks to BGRA")
{
    std::vector<uint8_t> payload(8, 0);
    writeLittleEndianValue<uint16_t>(payload, 0, 0xf800u);
    writeLittleEndianValue<uint16_t>(payload, 2, 0x001fu);

    uint32_t indices = 0;
    for (uint32_t pixelIndex = 0; pixelIndex < 16; ++pixelIndex)
    {
        indices |= (pixelIndex % 4) << (2 * pixelIndex);
    }
    writeLittleEndianValue<uint32_t>(payload, 4, indices);

    const std::vector<uint8_t> bytes = makeDtxBytes(4, 4, OpenYAMM::Game::Mm9DtxBppDxt1, payload);
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9DtxTexture> texture =
        OpenYAMM::Game::decodeMm9DtxTexture(bytes, errorMessage);

    REQUIRE_MESSAGE(texture.has_value(), errorMessage.c_str());
    CHECK(texture->decodeMode == "dxt1");
    REQUIRE(texture->pixelsBgra.size() == 4 * 4 * 4);
    CHECK(texture->pixelsBgra[0] == 0);
    CHECK(texture->pixelsBgra[1] == 0);
    CHECK(texture->pixelsBgra[2] == 255);
    CHECK(texture->pixelsBgra[3] == 255);
    CHECK(texture->pixelsBgra[4] == 255);
    CHECK(texture->pixelsBgra[5] == 0);
    CHECK(texture->pixelsBgra[6] == 0);
    CHECK(texture->pixelsBgra[7] == 255);
}
