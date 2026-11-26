#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorMeadow.h"

#include <doctest/doctest.h>

#include <cstring>
#include <optional>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
// A small map of the given side: a ramp along x, two tile kinds, one BModel, one entity and one spawn.
OutdoorMapData testMap(int side)
{
    OutdoorMapData map = {};
    map.version = 8;
    map.terrainSide = side;
    map.name = "v2test.odm";
    map.fileName = "v2test.odm";
    map.skyTexture = "plansky1";
    map.groundTilesetName = "hesper";
    map.heightMap.resize(map.terrainSampleCount());
    map.tileMap.resize(map.terrainSampleCount());
    map.attributeMap.resize(map.terrainSampleCount(), 0);
    map.decorationMap.resize(map.terrainSampleCount(), 0);
    for (int y = 0; y < side; ++y)
    {
        for (int x = 0; x < side; ++x)
        {
            map.heightMap[size_t(y) * side + x] = uint8_t(x % 200);
            map.tileMap[size_t(y) * side + x] = uint8_t(x < side / 2 ? 90 : 91);
        }
    }
    map.attributeMap[size_t(side - 2) * side + (side - 2)] = 0x02;
    map.decorationMap[size_t(side) * side - 1] = 7;

    OutdoorBModel bmodel = {};
    bmodel.name = "block";
    bmodel.vertices = {{37000, 37000, 0}, {37512, 37000, 0}, {37512, 37512, 0}, {37000, 37512, 0}};
    OutdoorBModelFace face = {};
    face.vertexIndices = {0, 1, 2, 3};
    face.textureUs = {0, 32, 32, 0};
    face.textureVs = {0, 0, 32, 32};
    face.planeNormalZ = 65536;
    face.polygonType = 3;
    face.textureName = "hhwall01";
    bmodel.faces.push_back(face);
    bmodel.bspNodes.push_back({-1, -1, 0, 1});
    map.bmodels.push_back(bmodel);

    OutdoorEntity entity = {};
    entity.decorationListId = 3;
    entity.x = -40000;
    entity.y = 40000;
    entity.z = 64;
    entity.name = "far corner";
    map.entities.push_back(entity);

    OutdoorSpawn spawn = {};
    spawn.x = 39000;
    spawn.y = -39000;
    spawn.radius = 256;
    spawn.typeId = 3;
    spawn.index = 1;
    map.spawns.push_back(spawn);
    return map;
}

std::string versionField(const std::vector<uint8_t> &bytes)
{
    return std::string(reinterpret_cast<const char *>(bytes.data() + 0x40));
}
}

TEST_CASE("odm v2 writes and reads a 160 terrain side")
{
    const OutdoorMapData source = testMap(160);
    REQUIRE(source.isOdmV2());
    const std::optional<std::vector<uint8_t>> bytes = OutdoorMapDataWriter().buildBytes(source);
    REQUIRE(bytes);
    CHECK(versionField(*bytes) == "OpenYAMM ODM v2");
    uint16_t storedSide = 0;
    std::memcpy(&storedSide, bytes->data() + 0x50, sizeof(storedSide));
    CHECK(storedSide == 160);

    const std::optional<OutdoorMapData> loaded = OutdoorMapDataLoader().loadFromBytes(*bytes);
    REQUIRE(loaded);
    CHECK(loaded->terrainSide == 160);
    CHECK(loaded->version == 8);
    CHECK(loaded->heightMap == source.heightMap);
    CHECK(loaded->tileMap == source.tileMap);
    CHECK(loaded->attributeMap == source.attributeMap);
    CHECK(loaded->decorationMap == source.decorationMap);
    CHECK(loaded->someOtherMap.size() == size_t(160) * 160 * 2);
    CHECK(loaded->normalMap.size() == size_t(160) * 160 * 2);
    REQUIRE(loaded->bmodels.size() == 1);
    CHECK(loaded->bmodels[0].faces.size() == 1);
    CHECK(loaded->bmodels[0].faces[0].textureName == "hhwall01");
    REQUIRE(loaded->entities.size() == 1);
    CHECK(loaded->entities[0].x == -40000);
    CHECK(loaded->entities[0].name == "far corner");
    REQUIRE(loaded->spawns.size() == 1);
    CHECK(loaded->spawns[0].y == -39000);

    // Written back unchanged, and patched in place without changing the side.
    const std::optional<std::vector<uint8_t>> rewritten = OutdoorMapDataWriter().buildBytes(*loaded);
    REQUIRE(rewritten);
    CHECK(*rewritten == *bytes);
    const std::optional<std::vector<uint8_t>> patched = OutdoorMapDataWriter().patchBytes(*loaded, *bytes);
    REQUIRE(patched);
    CHECK(*patched == *bytes);
}

TEST_CASE("odm v2 leaves a classic 128 map in the classic layout")
{
    const OutdoorMapData source = testMap(128);
    CHECK_FALSE(source.isOdmV2());
    const std::optional<std::vector<uint8_t>> bytes = OutdoorMapDataWriter().buildBytes(source);
    REQUIRE(bytes);
    // MM8's layout: a zero version field, no side, 0x4000-byte terrain maps.
    CHECK(versionField(*bytes).empty());
    CHECK((*bytes)[0x50] == 0);
    CHECK((*bytes)[0x51] == 0);
    const std::optional<OutdoorMapData> loaded = OutdoorMapDataLoader().loadFromBytes(*bytes);
    REQUIRE(loaded);
    CHECK(loaded->terrainSide == 128);
    CHECK(loaded->heightMap.size() == 0x4000);
    CHECK(loaded->someOtherMap.size() * sizeof(uint32_t) == 0x20000);
    CHECK(loaded->normalMap.size() * sizeof(uint16_t) == 0x10000);
    const std::optional<std::vector<uint8_t>> rewritten = OutdoorMapDataWriter().buildBytes(*loaded);
    REQUIRE(rewritten);
    CHECK(*rewritten == *bytes);

    // A side the classic tags cannot hold makes a map v2 whatever its version says.
    OutdoorMapData mm7 = testMap(160);
    mm7.version = 7;
    const std::optional<std::vector<uint8_t>> mm7Bytes = OutdoorMapDataWriter().buildBytes(mm7);
    REQUIRE(mm7Bytes);
    CHECK(versionField(*mm7Bytes) == "OpenYAMM ODM v2");
}

TEST_CASE("odm v2 rejects bad sides and short files")
{
    const std::optional<std::vector<uint8_t>> bytes = OutdoorMapDataWriter().buildBytes(testMap(160));
    REQUIRE(bytes);

    for (const uint16_t side : {uint16_t(0), uint16_t(161), uint16_t(30), uint16_t(258)})
    {
        std::vector<uint8_t> broken = *bytes;
        std::memcpy(broken.data() + 0x50, &side, sizeof(side));
        CHECK_FALSE(OutdoorMapDataLoader().loadFromBytes(broken));
    }

    std::vector<uint8_t> truncated(bytes->begin(), bytes->begin() + 0xb4 + 128 * 128 * 3);
    CHECK_FALSE(OutdoorMapDataLoader().loadFromBytes(truncated));

    OutdoorMapData oddSide = testMap(160);
    oddSide.terrainSide = 161;
    CHECK_FALSE(OutdoorMapDataWriter().buildBytes(oddSide));

    // A patch keeps the base file's side.
    CHECK_FALSE(OutdoorMapDataWriter().patchBytes(testMap(128), *bytes));
}

TEST_CASE("odm v2 world grid conversion at 128 and 160")
{
    OutdoorMapData classic = {};
    CHECK(classic.terrainHalfSide() == 64);
    CHECK(classic.terrainHalfExtent() == 32768.0f);
    CHECK(classic.journalRevealSide() == 88);
    for (int grid : {0, 1, 63, 64, 100, 127})
    {
        // The map-aware forms equal the classic ones exactly on a classic map.
        CHECK(outdoorGridCornerWorldX(classic, grid) == outdoorGridCornerWorldX(grid));
        CHECK(outdoorGridCornerWorldY(classic, grid) == outdoorGridCornerWorldY(grid));
    }
    for (float world : {-32768.0f, -1234.5f, 0.0f, 511.0f, 32767.0f})
    {
        CHECK(outdoorWorldToGridXFloat(classic, world) == outdoorWorldToGridXFloat(world));
        CHECK(outdoorWorldToGridYFloat(classic, world) == outdoorWorldToGridYFloat(world));
    }

    OutdoorMapData large = {};
    large.terrainSide = 160;
    CHECK(large.terrainHalfSide() == 80);
    CHECK(large.terrainHalfExtent() == 40960.0f);
    CHECK(large.journalRevealSide() == 110);
    CHECK(outdoorGridCornerWorldX(large, 0) == -40960.0f);
    CHECK(outdoorGridCornerWorldY(large, 0) == 40960.0f);
    CHECK(outdoorGridCornerWorldX(large, 159) == 40448.0f);
    CHECK(outdoorWorldToGridXFloat(large, -40960.0f) == 0.0f);
    CHECK(outdoorWorldToGridYFloat(large, 40960.0f) == 0.0f);
    CHECK(outdoorWorldToGridXFloat(large, 0.0f) == 80.0f);
    // The walkable square of a Hesper map: 113 cells, its edge about 28 930 units out, 23 cells of rim beyond.
    CHECK(outdoorWorldToGridXFloat(large, 28930.0f) == doctest::Approx(136.5f).epsilon(0.001));
}

TEST_CASE("odm v2 terrain sampling reaches the far edge of a 160 map")
{
    const OutdoorMapData map = testMap(160);
    // The ramp rises one height step (32 units) per cell eastward.
    const float east = outdoorGridCornerWorldX(map, 150);
    const float north = outdoorGridCornerWorldY(map, 10);
    CHECK(sampleOutdoorTerrainHeight(map, east, north) == doctest::Approx(150.0f * 32.0f));
    CHECK(sampleOutdoorTerrainHeight(map, outdoorGridCornerWorldX(map, 158), north)
        == doctest::Approx(158.0f * 32.0f));
    // The water cell sits at (158, 158), past the classic grid.
    const float waterX = outdoorGridCornerWorldX(map, 158) + 256.0f;
    const float waterY = outdoorGridCornerWorldY(map, 158) - 256.0f;
    CHECK(isOutdoorTerrainWater(map, waterX, waterY));
    CHECK_FALSE(isOutdoorTerrainWater(map, waterX - 512.0f, waterY));

    OutdoorMapData voidMap = map;
    voidMap.voidCells.assign(voidMap.terrainSampleCount(), 0);
    voidMap.voidCells[size_t(150) * 160 + 155] = 1;
    CHECK(isOutdoorVoidCell(voidMap, 155, 150));
    CHECK_FALSE(isOutdoorVoidCell(voidMap, 150, 155));
    CHECK_FALSE(isOutdoorVoidCell(voidMap, 160, 150));
}

TEST_CASE("odm v2 meadow field covers the 160 grid")
{
    const OutdoorMapData map = testMap(160);
    const OutdoorMeadowField field = buildOutdoorMeadowField(map);
    CHECK(field.side == 160);
    CHECK(field.values.size() == size_t(160) * 160);
    // A sample at the far corner reads the field's last corner, not the classic grid's.
    const float corner = field.sample(outdoorGridCornerWorldX(map, 159), outdoorGridCornerWorldY(map, 159));
    CHECK(corner == doctest::Approx(field.values.back()));
}
