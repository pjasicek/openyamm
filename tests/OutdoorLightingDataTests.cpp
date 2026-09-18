#include "doctest/doctest.h"

#include "game/outdoor/OutdoorLightingData.h"
#include "game/outdoor/OutdoorMapData.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

namespace
{
uint64_t fnv1a64(const std::vector<uint8_t> &bytes)
{
    uint64_t value = 14695981039346656037ULL;
    for (uint8_t byte : bytes)
    {
        value ^= byte;
        value *= 1099511628211ULL;
    }
    return value;
}

void appendU16(std::vector<uint8_t> &bytes, uint16_t value)
{
    bytes.push_back(static_cast<uint8_t>(value));
    bytes.push_back(static_cast<uint8_t>(value >> 8));
}

void appendU32(std::vector<uint8_t> &bytes, uint32_t value)
{
    appendU16(bytes, static_cast<uint16_t>(value));
    appendU16(bytes, static_cast<uint16_t>(value >> 16));
}

void appendU64(std::vector<uint8_t> &bytes, uint64_t value)
{
    appendU32(bytes, static_cast<uint32_t>(value));
    appendU32(bytes, static_cast<uint32_t>(value >> 32));
}

void appendFloat(std::vector<uint8_t> &bytes, float value)
{
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    appendU32(bytes, bits);
}

OpenYAMM::Game::OutdoorMapData makeMapData()
{
    OpenYAMM::Game::OutdoorMapData mapData = {};
    mapData.bmodels.resize(1);
    mapData.bmodels[0].faces.resize(1);
    mapData.bmodels[0].faces[0].vertexIndices = {0, 1, 2};
    return mapData;
}

std::vector<uint8_t> makeLightingBytes(const std::vector<uint8_t> &geometryBytes)
{
    constexpr uint32_t PageOffset = 96;
    constexpr uint32_t FaceOffset = 112;
    constexpr uint32_t VertexOffset = 136;
    constexpr uint32_t LightOffset = 172;
    constexpr uint32_t PixelOffset = 252;
    constexpr uint32_t FileSize = 257;
    const std::array<uint8_t, 8> magic = {'O', 'Y', 'M', 'L', 'I', 'T', '1', 0};
    std::vector<uint8_t> result(magic.begin(), magic.end());
    appendU32(result, 3);
    appendU32(result, 96);
    appendU64(result, fnv1a64(geometryBytes));
    appendU32(result, 1);
    appendU32(result, 1);
    appendU32(result, 1);
    appendU32(result, 1);
    appendU32(result, 3);
    appendU32(result, 1);
    appendU32(result, PageOffset);
    appendU32(result, FaceOffset);
    appendU32(result, VertexOffset);
    appendU32(result, LightOffset);
    appendU32(result, PixelOffset);
    appendU32(result, FileSize);
    appendU32(result, 0xff302010);
    result.resize(PageOffset, 0);

    appendU32(result, 1);
    appendU32(result, 1);
    appendU32(result, PixelOffset);
    appendU32(result, 5);

    appendU64(result, 0);
    appendU32(result, 0);
    appendU32(result, 0);
    appendU16(result, 0);
    appendU16(result, 1);
    appendU32(result, 0);

    for (size_t index = 0; index < 3; ++index)
    {
        appendFloat(result, 0.25f * static_cast<float>(index));
        appendFloat(result, 0.5f);
        appendU32(result, 0xffffffff);
    }

    appendU32(result, 42);
    appendU32(result, 1);
    appendFloat(result, 10.0f);
    appendFloat(result, 20.0f);
    appendFloat(result, 30.0f);
    appendFloat(result, 400.0f);
    appendU32(result, 0xff604020);
    appendU32(result, 0x23);
    for (size_t index = 0; index < 4; ++index)
    {
        appendFloat(result, index == 3 ? 1.0f : 0.0f);
    }
    appendFloat(result, 90.0f);
    appendFloat(result, 0.75f);
    appendFloat(result, 0.5f);
    appendU32(result, 0xffc08040);
    appendU32(result, 1234);
    appendU32(result, 0);
    appendU32(result, 0);
    appendU32(result, 0);
    result.push_back(0);
    appendU32(result, 0xffc0a080);
    return result;
}
}

TEST_CASE("outdoor lighting data loader validates atlas faces and authored lights")
{
    const std::vector<uint8_t> geometryBytes = {3, 1, 4, 1, 5};
    const OpenYAMM::Game::OutdoorMapData mapData = makeMapData();
    OpenYAMM::Game::OutdoorLightingDataLoader loader = {};
    std::string errorMessage;

    const std::optional<OpenYAMM::Game::OutdoorLightingData> lighting =
        loader.loadFromBytes(makeLightingBytes(geometryBytes), geometryBytes, mapData, errorMessage);

    REQUIRE_MESSAGE(lighting.has_value(), errorMessage);
    REQUIRE_EQ(lighting->atlasPages.size(), 1);
    CHECK_EQ(lighting->atlasPages[0].pixelsBgra[0], 0xffc0a080);
    REQUIRE_EQ(lighting->facesByBModel[0][0].vertices.size(), 3);
    CHECK(lighting->facesByBModel[0][0].hasLightmap);
    CHECK_EQ(lighting->facesByBModel[0][0].atlasPageIndex, 0);
    REQUIRE_EQ(lighting->authoredLights.size(), 1);
    CHECK_EQ(lighting->authoredLights[0].sourceObjectIndex, 42);
    CHECK(lighting->authoredLights[0].lightsObjects());
    CHECK(lighting->authoredLights[0].lightsFastObjects());
    CHECK_FALSE(lighting->authoredLights[0].staticObjectLightEligible());
    CHECK(lighting->authoredLights[0].globalObjectLight());
}

TEST_CASE("outdoor lighting data loader rejects stale geometry")
{
    const std::vector<uint8_t> geometryBytes = {3, 1, 4, 1, 5};
    const OpenYAMM::Game::OutdoorMapData mapData = makeMapData();
    OpenYAMM::Game::OutdoorLightingDataLoader loader = {};
    std::string errorMessage;

    CHECK_FALSE(loader.loadFromBytes(makeLightingBytes(geometryBytes), {1}, mapData, errorMessage));
    CHECK(errorMessage.find("different geometry") != std::string::npos);
}

TEST_CASE("outdoor lighting brightness scaling raises lightmap and fallback RGB and preserves alpha")
{
    OpenYAMM::Game::OutdoorLightingData lighting = {};
    lighting.atlasPages.push_back({2, 1, {0xffc0a080, 0x80f0e0d0}});
    lighting.facesByBModel.resize(1);
    lighting.facesByBModel[0].resize(2);
    lighting.facesByBModel[0][0].hasLightmap = false;
    lighting.facesByBModel[0][0].vertices.push_back({0.5f, 0.5f, 0xff806040});
    lighting.facesByBModel[0][1].hasLightmap = true;
    lighting.facesByBModel[0][1].vertices.push_back({0.5f, 0.5f, 0xff604020});

    OpenYAMM::Game::scaleOutdoorLightingBrightness(lighting, 1.25f);

    REQUIRE_EQ(lighting.atlasPages.size(), 1);
    REQUIRE_EQ(lighting.atlasPages[0].pixelsBgra.size(), 2);
    CHECK_EQ(lighting.atlasPages[0].pixelsBgra[0], 0xfff0c8a0);
    CHECK_EQ(lighting.atlasPages[0].pixelsBgra[1], 0x80ffffff);
    REQUIRE_EQ(lighting.facesByBModel[0][0].vertices.size(), 1);
    CHECK_EQ(lighting.facesByBModel[0][0].vertices[0].staticColorAbgr, 0xffa07850);
    REQUIRE_EQ(lighting.facesByBModel[0][1].vertices.size(), 1);
    CHECK_EQ(lighting.facesByBModel[0][1].vertices[0].staticColorAbgr, 0xff604020);
}

namespace
{
void setU32(std::vector<uint8_t> &bytes, size_t offset, uint32_t value)
{
    for (size_t index = 0; index < 4; ++index)
    {
        bytes[offset + index] = uint8_t(value >> (index * 8));
    }
}

std::vector<uint8_t> makeBakedLightingBytes(const std::vector<uint8_t> &geometry)
{
    std::vector<uint8_t> bytes = makeLightingBytes(geometry);
    // Add a second page record, preserving the original face and light payload.
    bytes.insert(bytes.begin() + 112, 16, 0);
    setU32(bytes, 8, 3);
    setU32(bytes, 32, 2);
    for (size_t offset : {52, 56, 60, 64})
    {
        const uint32_t old = bytes[offset] | (uint32_t(bytes[offset + 1]) << 8);
        setU32(bytes, offset, old + 16);
    }
    setU32(bytes, 104, 268);
    setU32(bytes, 112, 1);
    setU32(bytes, 116, 1);
    setU32(bytes, 120, 273);
    setU32(bytes, 124, 5);
    bytes.push_back(0);
    appendU32(bytes, 0x40ffffff);
    setU32(bytes, 76, 1);
    std::vector<uint8_t> bounds;
    for (float value : {-32768.0f, 32768.0f, 65024.0f, -65024.0f})
    {
        appendFloat(bounds, value);
    }
    std::copy(bounds.begin(), bounds.end(), bytes.begin() + 80);
    appendU32(bytes, 0);
    appendU32(bytes, 1);
    const std::string path = "worlds/mm6/maps/fixture.odm";
    appendU32(bytes, uint32_t(path.size()));
    appendU64(bytes, fnv1a64(geometry));
    bytes.insert(bytes.end(), path.begin(), path.end());
    setU32(bytes, 68, uint32_t(bytes.size()));
    return bytes;
}

}

TEST_CASE("outdoor lighting v3 accepts separate source pages and validates the extension")
{
    const std::vector<uint8_t> geometry = {1, 2, 3};
    const OpenYAMM::Game::OutdoorMapData mapData = makeMapData();
    OpenYAMM::Game::OutdoorLightingDataLoader loader;
    std::string error;
    std::vector<uint8_t> bytes = makeBakedLightingBytes(geometry);
    const std::optional<OpenYAMM::Game::OutdoorLightingData> data =
        loader.loadFromBytes(bytes, geometry, mapData, error);
    REQUIRE_MESSAGE(data, error);
    CHECK(data->hasBakedSources());
    CHECK(data->atlasPages.size() == 2);
    CHECK(data->terrainBounds[3] == -65024.0f);
    REQUIRE(data->dependencies.size() == 1);
    CHECK(data->dependencies.front().hash == OpenYAMM::Game::outdoorLightingContentHash(geometry));

    SUBCASE("legacy brightness scaling cannot corrupt RGBM encoding")
    {
        OpenYAMM::Game::OutdoorLightingData scaled = *data;
        OpenYAMM::Game::scaleOutdoorLightingBrightness(scaled, 2.0f);
        CHECK(scaled.atlasPages[0].pixelsBgra == data->atlasPages[0].pixelsBgra);
        CHECK(scaled.atlasPages[1].pixelsBgra == data->atlasPages[1].pixelsBgra);
    }
    SUBCASE("dependency paths cannot escape a package")
    {
        const std::string original = "worlds/mm6/maps/fixture.odm";
        const auto found = std::search(bytes.begin(), bytes.end(), original.begin(), original.end());
        REQUIRE(found != bytes.end());
        *(found + 7) = '.';
        *(found + 8) = '.';
        CHECK_FALSE(loader.loadFromBytes(bytes, geometry, mapData, error));
    }
    SUBCASE("probe payloads reject negative illumination")
    {
        std::vector<uint8_t> probe;
        for (float value : {0.0f, 0.0f, 128.0f, -1.0f, 0.0f, 0.0f, 0.2f, 0.2f, 0.2f})
        {
            appendFloat(probe, value);
        }
        setU32(bytes, 278, 1);
        bytes.insert(bytes.begin() + 286, probe.begin(), probe.end());
        setU32(bytes, 68, uint32_t(bytes.size()));
        CHECK_FALSE(loader.loadFromBytes(bytes, geometry, mapData, error));
        CHECK(error.find("RGBM4") != std::string::npos);
    }
    SUBCASE("unknown format flags are rejected")
    {
        setU32(bytes, 76, 2);
        CHECK_FALSE(loader.loadFromBytes(bytes, geometry, mapData, error));
    }
    SUBCASE("truncated extension is rejected")
    {
        bytes.pop_back();
        setU32(bytes, 68, uint32_t(bytes.size()));
        CHECK_FALSE(loader.loadFromBytes(bytes, geometry, mapData, error));
    }
    SUBCASE("mismatched paired dimensions are rejected")
    {
        setU32(bytes, 112, 2);
        CHECK_FALSE(loader.loadFromBytes(bytes, geometry, mapData, error));
    }
    SUBCASE("unexpected trailing payload is rejected")
    {
        bytes.push_back(0);
        setU32(bytes, 68, uint32_t(bytes.size()));
        CHECK_FALSE(loader.loadFromBytes(bytes, geometry, mapData, error));
    }
    SUBCASE("invalid floating point bounds are rejected")
    {
        setU32(bytes, 80, 0x7fc00000);
        CHECK_FALSE(loader.loadFromBytes(bytes, geometry, mapData, error));
    }
}

TEST_CASE("outdoor lighting v3 decodes strict compressed RGBM pages")
{
    const std::vector<uint8_t> geometry = {1, 2, 3};
    const OpenYAMM::Game::OutdoorMapData mapData = makeMapData();
    OpenYAMM::Game::OutdoorLightingDataLoader loader;
    std::string error;
    std::vector<uint8_t> bytes = makeBakedLightingBytes(geometry);

    const std::optional<OpenYAMM::Game::OutdoorLightingData> data =
        loader.loadFromBytes(bytes, geometry, mapData, error);
    REQUIRE_MESSAGE(data, error);
    CHECK(data->formatVersion == 3);
    REQUIRE(data->atlasPages.size() == 2);
    CHECK(data->atlasPages[0].pixelsBgra[0] == 0xffc0a080);
    CHECK(data->atlasPages[1].pixelsBgra[0] == 0x40ffffff);

    bytes[268] = 0x81;
    CHECK_FALSE(loader.loadFromBytes(bytes, geometry, mapData, error));
    CHECK(error.find("compression") != std::string::npos);
}

TEST_CASE("outdoor lighting rejects obsolete format versions")
{
    const std::vector<uint8_t> geometry = {1, 2, 3};
    const OpenYAMM::Game::OutdoorMapData mapData = makeMapData();
    OpenYAMM::Game::OutdoorLightingDataLoader loader;
    std::string error;
    std::vector<uint8_t> bytes = makeLightingBytes(geometry);

    for (uint32_t version : {1U, 2U})
    {
        setU32(bytes, 8, version);
        CHECK_FALSE(loader.loadFromBytes(bytes, geometry, mapData, error));
        CHECK(error.find("unsupported") != std::string::npos);
    }
}

TEST_CASE("outdoor lighting probes interpolate visible neighbors without light leaking through walls")
{
    OpenYAMM::Game::OutdoorLightingData data;
    data.probes = {
        {{0, 0, 128}, {1, 0, 0}, {0.2f, 0.2f, 0.2f}},
        {{128, 0, 128}, {0, 1, 0}, {0.4f, 0.4f, 0.4f}},
    };
    data.indexProbes();
    const auto visible = [](const std::array<float, 3> &) { return true; };
    const std::optional<OpenYAMM::Game::OutdoorLightingData::Probe> mixed =
        data.sampleProbe({64, 0, 128}, visible);
    REQUIRE(mixed);
    CHECK(mixed->sun[0] == doctest::Approx(0.5));
    CHECK(mixed->sun[1] == doctest::Approx(0.5));
    const std::optional<OpenYAMM::Game::OutdoorLightingData::Probe> sheltered =
        data.sampleProbe({64, 0, 128}, [](const std::array<float, 3> &p) { return p[0] < 64; });
    REQUIRE(sheltered);
    CHECK(sheltered->sun[0] == doctest::Approx(1));
    CHECK(sheltered->sun[1] == doctest::Approx(0));
    CHECK_FALSE(data.sampleProbe({64, 0, 128}, [](const std::array<float, 3> &) { return false; }));
    CHECK_FALSE(data.sampleProbe({10000, 0, 128}, visible));
}
