#include "doctest/doctest.h"

#include "game/indoor/IndoorBakedLighting.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapDeltaData.h"
#include "game/render/lighting/BakedLightingFormat.h"

#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

namespace
{
using OpenYAMM::Game::IndoorBakedLighting;
using OpenYAMM::Game::IndoorBakedLightingFace;
using OpenYAMM::Game::IndoorMapData;

void appendU16(std::vector<uint8_t> &bytes, uint16_t value)
{
    bytes.push_back(uint8_t(value));
    bytes.push_back(uint8_t(value >> 8));
}

void appendU32(std::vector<uint8_t> &bytes, uint32_t value)
{
    for (int shift = 0; shift < 32; shift += 8)
    {
        bytes.push_back(uint8_t(value >> shift));
    }
}

void appendU64(std::vector<uint8_t> &bytes, uint64_t value)
{
    appendU32(bytes, uint32_t(value));
    appendU32(bytes, uint32_t(value >> 32));
}

void appendFloat(std::vector<uint8_t> &bytes, float value)
{
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    appendU32(bytes, bits);
}

void putU32(std::vector<uint8_t> &bytes, size_t offset, uint32_t value)
{
    for (int index = 0; index < 4; ++index)
    {
        bytes[offset + index] = uint8_t(value >> (index * 8));
    }
}

// Two faces (the first lightmapped on a 2x1 page, the second vertex-lit, as a door would be) and one sector.
IndoorMapData makeMapData()
{
    IndoorMapData mapData;
    mapData.faces.resize(2);
    mapData.sectors.resize(1);
    return mapData;
}

// daylightPairs: version 2, the page followed by its daylight page (another two-texel span).
std::vector<uint8_t> makeLightingBytes(const std::vector<uint8_t> &geometryBytes, bool daylightPairs = false)
{
    const std::string dependency = "worlds/mm9/maps/test.blv";
    // One repeat span of two identical BGRM texels.
    const std::vector<uint8_t> payload = {0x81, 0x40, 0x80, 0xff, 0x10};
    const std::vector<uint8_t> daylightPayload = {0x81, 0x20, 0x20, 0x20, 0x08};
    const uint32_t pageCount = daylightPairs ? 2 : 1;
    constexpr uint32_t PageOffset = 64;
    const uint32_t faceOffset = PageOffset + 16 * pageCount;
    const uint32_t sectorOffset = faceOffset + 2 * 36;
    const uint32_t dependencyOffset = sectorOffset + 12;
    const uint32_t pixelOffset = dependencyOffset + 12 + uint32_t(dependency.size());
    const uint32_t fileSize =
        pixelOffset + uint32_t(payload.size()) + (daylightPairs ? uint32_t(daylightPayload.size()) : 0);

    std::vector<uint8_t> bytes = {'O', 'Y', 'I', 'L', 'I', 'T', '1', 0};
    appendU32(bytes, daylightPairs ? 2 : 1);
    appendU32(bytes, 64);
    appendU64(bytes, OpenYAMM::Game::BakedLightingFormat::contentHash(geometryBytes));
    for (uint32_t value : {2u, 1u, pageCount, 1u, PageOffset, faceOffset, sectorOffset, dependencyOffset, pixelOffset,
             fileSize})
    {
        appendU32(bytes, value);
    }
    appendU32(bytes, 2);
    appendU32(bytes, 1);
    appendU32(bytes, pixelOffset);
    appendU32(bytes, uint32_t(payload.size()));
    if (daylightPairs)
    {
        appendU32(bytes, 2);
        appendU32(bytes, 1);
        appendU32(bytes, pixelOffset + uint32_t(payload.size()));
        appendU32(bytes, uint32_t(daylightPayload.size()));
    }
    // Face 0: page 0, u = x / 64 + 0.25, v = y / 32.
    appendU16(bytes, 0);
    appendU16(bytes, 1);
    for (float value : {1.0f / 64.0f, 0.0f, 0.0f, 0.25f, 0.0f, 1.0f / 32.0f, 0.0f, 0.0f})
    {
        appendFloat(bytes, value);
    }
    appendU16(bytes, 0xffff);
    appendU16(bytes, 0);
    for (int index = 0; index < 8; ++index)
    {
        appendFloat(bytes, 0.0f);
    }
    for (float value : {0.3f, 0.45f, 0.6f})
    {
        appendFloat(bytes, value);
    }
    appendU32(bytes, uint32_t(dependency.size()));
    appendU64(bytes, 0x1234);
    bytes.insert(bytes.end(), dependency.begin(), dependency.end());
    bytes.insert(bytes.end(), payload.begin(), payload.end());
    if (daylightPairs)
    {
        bytes.insert(bytes.end(), daylightPayload.begin(), daylightPayload.end());
    }
    REQUIRE(bytes.size() == fileSize);
    return bytes;
}
}

TEST_CASE("indoor baked lighting parses pages, face mappings, sector ambient and dependencies")
{
    const std::vector<uint8_t> geometry = {1, 2, 3, 4};
    std::string error;
    const std::optional<IndoorBakedLighting> lighting =
        OpenYAMM::Game::loadIndoorBakedLighting(makeLightingBytes(geometry), geometry, makeMapData(), error);
    REQUIRE_MESSAGE(lighting.has_value(), error);
    REQUIRE(lighting->pages.size() == 1);
    CHECK(lighting->pages[0].width == 2);
    CHECK(lighting->pages[0].decodePixels() == std::vector<uint32_t>{0x10ff8040u, 0x10ff8040u});
    REQUIRE(lighting->faces.size() == 2);
    CHECK(lighting->faces[0].lightmapped());
    CHECK_FALSE(lighting->faces[1].lightmapped());
    const std::array<float, 2> uv = lighting->faces[0].uvAt(32.0f, 16.0f, 100.0f);
    CHECK(uv[0] == doctest::Approx(0.75f));
    CHECK(uv[1] == doctest::Approx(0.5f));
    REQUIRE(lighting->sectorAmbient.size() == 1);
    CHECK(lighting->actorAmbient(0).value() == doctest::Approx(0.45f));
    CHECK_FALSE(lighting->actorAmbient(1).has_value());
    REQUIRE(lighting->dependencies.size() == 1);
    CHECK(lighting->dependencies[0].path == "worlds/mm9/maps/test.blv");
    CHECK(lighting->dependencies[0].hash == 0x1234);
}

TEST_CASE("indoor baked lighting version 2 pairs each page with its daylight page")
{
    const std::vector<uint8_t> geometry = {1, 2, 3, 4};
    std::string error;
    const std::vector<uint8_t> bytes = makeLightingBytes(geometry, true);
    const std::optional<IndoorBakedLighting> lighting =
        OpenYAMM::Game::loadIndoorBakedLighting(bytes, geometry, makeMapData(), error);
    REQUIRE_MESSAGE(lighting.has_value(), error);
    REQUIRE(lighting->pages.size() == 1);
    REQUIRE(lighting->daylightPages.size() == 1);
    CHECK(lighting->pages[0].decodePixels() == std::vector<uint32_t>{0x10ff8040u, 0x10ff8040u});
    CHECK(lighting->daylightPages[0].decodePixels() == std::vector<uint32_t>{0x08202020u, 0x08202020u});
    // The face's record names the pair's first page; it draws with page 0 of each.
    CHECK(IndoorBakedLighting::facePage(&*lighting, true, 0) == 0);

    // A version 1 file has no daylight pages.
    const std::optional<IndoorBakedLighting> plain =
        OpenYAMM::Game::loadIndoorBakedLighting(makeLightingBytes(geometry), geometry, makeMapData(), error);
    REQUIRE(plain.has_value());
    CHECK(plain->daylightPages.empty());

    // A face on a pair's daylight page.
    std::vector<uint8_t> oddPage = bytes;
    oddPage[96] = 1;
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(oddPage, geometry, makeMapData(), error).has_value());
    // A daylight page of another size.
    std::vector<uint8_t> otherSize = bytes;
    putU32(otherSize, 80, 1);
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(otherSize, geometry, makeMapData(), error).has_value());
}

TEST_CASE("indoor baked lighting of other geometry is stale and ignored")
{
    const std::vector<uint8_t> geometry = {1, 2, 3, 4};
    const std::vector<uint8_t> bytes = makeLightingBytes(geometry);
    std::string error;
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(bytes, {1, 2, 3, 5}, makeMapData(), error).has_value());
    CHECK(error.find("stale") != std::string::npos);

    IndoorMapData moreFaces = makeMapData();
    moreFaces.faces.resize(3);
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(bytes, geometry, moreFaces, error).has_value());
    CHECK(error.find("stale") != std::string::npos);
}

TEST_CASE("indoor baked lighting rejects corrupt files")
{
    const std::vector<uint8_t> geometry = {9};
    const IndoorMapData mapData = makeMapData();
    const std::vector<uint8_t> valid = makeLightingBytes(geometry);
    std::string error;

    std::vector<uint8_t> truncated = valid;
    truncated.pop_back();
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(truncated, geometry, mapData, error).has_value());

    std::vector<uint8_t> outdoorMagic = valid;
    outdoorMagic[2] = 'M';
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(outdoorMagic, geometry, mapData, error).has_value());

    // A face on a page the file does not have.
    std::vector<uint8_t> missingPage = valid;
    missingPage[80] = 3;
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(missingPage, geometry, mapData, error).has_value());

    // An RLE span producing three texels for a two-texel page.
    std::vector<uint8_t> badSpan = valid;
    badSpan[badSpan.size() - 5] = 0x82;
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(badSpan, geometry, mapData, error).has_value());

    // A dependency outside the asset roots.
    std::vector<uint8_t> badPath = valid;
    const std::string dependency = "worlds/mm9/maps/test.blv";
    const size_t pathOffset = valid.size() - 5 - dependency.size();
    badPath[pathOffset] = '.';
    badPath[pathOffset + 1] = '.';
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(badPath, geometry, mapData, error).has_value());

    // A non-finite face mapping.
    std::vector<uint8_t> nonFinite = valid;
    putU32(nonFinite, 84, 0x7fc00000u);
    CHECK_FALSE(OpenYAMM::Game::loadIndoorBakedLighting(nonFinite, geometry, mapData, error).has_value());
}

TEST_CASE("indoor baked lighting is opt-in per map and per face")
{
    const std::vector<uint8_t> geometry = {1, 2, 3, 4};
    std::string error;
    const std::optional<IndoorBakedLighting> lighting =
        OpenYAMM::Game::loadIndoorBakedLighting(makeLightingBytes(geometry), geometry, makeMapData(), error);
    REQUIRE(lighting.has_value());

    // A map without a bake keeps every face vertex-lit.
    CHECK(IndoorBakedLighting::facePage(nullptr, true, 0) == -1);
    // A lightmapped face samples its page while lightmaps are on, and is vertex-lit with them off.
    CHECK(IndoorBakedLighting::facePage(&*lighting, true, 0) == 0);
    CHECK(IndoorBakedLighting::facePage(&*lighting, false, 0) == -1);
    // A face the bake left out (a door) and a face beyond the records stay vertex-lit.
    CHECK(IndoorBakedLighting::facePage(&*lighting, true, 1) == -1);
    CHECK(IndoorBakedLighting::facePage(&*lighting, true, 7) == -1);
    CHECK(IndoorBakedLightingFace{}.page == IndoorBakedLightingFace::NoPage);
}

TEST_CASE("indoor baked lighting bakes rigid short movers and leaves stretching or long ones vertex-lit")
{
    using OpenYAMM::Game::IndoorBakedMoverMaxTravel;
    using OpenYAMM::Game::IndoorFace;
    using OpenYAMM::Game::MapDeltaDoor;
    using OpenYAMM::Game::indoorMoverFaceBakeable;

    IndoorFace leaf;
    leaf.vertexIndices = {4, 5, 6, 7};
    MapDeltaDoor door;
    door.vertexIds = {4, 5, 6, 7, 8};
    door.moveLength = 254;
    const MapDeltaDoor *pDoor = &door;

    // A leaf whose every vertex the door moves: baked in its stored pose.
    CHECK(indoorMoverFaceBakeable(leaf, std::span<const MapDeltaDoor *const>(&pDoor, 1)));
    // A frame face that stretches (one vertex stays): vertex-lit.
    IndoorFace frame;
    frame.vertexIndices = {4, 5, 9};
    CHECK_FALSE(indoorMoverFaceBakeable(frame, std::span<const MapDeltaDoor *const>(&pDoor, 1)));
    // Moved by two doors, or by none: vertex-lit.
    const std::vector<const MapDeltaDoor *> twoDoors = {&door, &door};
    CHECK_FALSE(indoorMoverFaceBakeable(leaf, twoDoors));
    CHECK_FALSE(indoorMoverFaceBakeable(leaf, {}));
    // A long mover (a lift crossing rooms) would carry one room's light into another: vertex-lit.
    door.moveLength = IndoorBakedMoverMaxTravel;
    CHECK(indoorMoverFaceBakeable(leaf, std::span<const MapDeltaDoor *const>(&pDoor, 1)));
    door.moveLength = IndoorBakedMoverMaxTravel + 1;
    CHECK_FALSE(indoorMoverFaceBakeable(leaf, std::span<const MapDeltaDoor *const>(&pDoor, 1)));
}

TEST_CASE("indoor baked lighting moves a mover's stored-pose lightmap with it and falls back without mover data")
{
    using OpenYAMM::Game::IndoorBakedFaceLightmap;
    using OpenYAMM::Game::IndoorFace;
    using OpenYAMM::Game::IndoorVertex;

    const std::vector<uint8_t> geometry = {1, 2, 3, 4};
    std::string error;
    const std::optional<IndoorBakedLighting> lighting =
        OpenYAMM::Game::loadIndoorBakedLighting(makeLightingBytes(geometry), geometry, makeMapData(), error);
    REQUIRE(lighting.has_value());

    IndoorFace face;
    face.vertexIndices = {0, 1, 2};
    const std::vector<IndoorVertex> stored = {{0, 0, 0}, {64, 0, 0}, {64, 32, 0}};

    // A static face: its page, no offset.
    IndoorBakedFaceLightmap result =
        IndoorBakedLighting::faceLightmap(&*lighting, true, 0, face, false, stored, stored);
    CHECK(result.page == 0);
    CHECK(result.uvOffset[0] == 0.0f);
    CHECK(result.uvOffset[1] == 0.0f);

    // A baked mover in its stored pose, then slid 32 along x and 16 along y: the UVs shift back to the stored pose
    // (u = x / 64 + 0.25, v = y / 32).
    result = IndoorBakedLighting::faceLightmap(&*lighting, true, 0, face, true, stored, stored);
    CHECK(result.page == 0);
    CHECK(result.uvOffset[0] == 0.0f);
    const std::vector<IndoorVertex> slid = {{32, 16, 0}, {96, 16, 0}, {96, 48, 0}};
    result = IndoorBakedLighting::faceLightmap(&*lighting, true, 0, face, true, slid, stored);
    CHECK(result.page == 0);
    CHECK(result.uvOffset[0] == doctest::Approx(-0.5f));
    CHECK(result.uvOffset[1] == doctest::Approx(-0.5f));
    const std::array<float, 2> uv = lighting->faces[0].uvAt(96.0f, 48.0f, 0.0f);
    CHECK(uv[0] + result.uvOffset[0] == doctest::Approx(lighting->faces[0].uvAt(64.0f, 32.0f, 0.0f)[0]));
    CHECK(uv[1] + result.uvOffset[1] == doctest::Approx(lighting->faces[0].uvAt(64.0f, 32.0f, 0.0f)[1]));

    // A mover that is not one translation of its stored pose (it stretches): the vertex-lit path.
    const std::vector<IndoorVertex> stretched = {{0, 0, 0}, {96, 0, 0}, {96, 32, 0}};
    CHECK(IndoorBakedLighting::faceLightmap(&*lighting, true, 0, face, true, stretched, stored).page == -1);
    // A sidecar without mover data (an older bake: the mover's record has no page) keeps the vertex-lit path, as do
    // a map without a bake and lightmaps switched off.
    CHECK(IndoorBakedLighting::faceLightmap(&*lighting, true, 1, face, true, slid, stored).page == -1);
    CHECK(IndoorBakedLighting::faceLightmap(nullptr, true, 0, face, true, slid, stored).page == -1);
    CHECK(IndoorBakedLighting::faceLightmap(&*lighting, false, 0, face, true, slid, stored).page == -1);
    // A vertex index outside the map: vertex-lit.
    IndoorFace broken;
    broken.vertexIndices = {0, 1, 9};
    CHECK(IndoorBakedLighting::faceLightmap(&*lighting, true, 0, broken, true, slid, stored).page == -1);
}
