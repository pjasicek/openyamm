#include "game/maps/OutdoorTerrainTiles.h"
#include "game/outdoor/OutdoorMovementDriver.h"
#include "game/outdoor/OutdoorTerrainMaterialConfig.h"
#include "game/outdoor/OutdoorWaterDepthData.h"

#include <doctest/doctest.h>

#include <cmath>
#include <limits>
#include <utility>

namespace
{
using namespace OpenYAMM::Game;

constexpr int WaterX = 62;
constexpr int WaterY = 63;

OutdoorMapData waterMap(uint8_t encodedDepth)
{
    OutdoorMapData map;
    map.heightMap.assign(128 * 128, 4);
    map.tileMap.assign(128 * 128, 0);
    map.attributeMap.assign(128 * 128, 0);
    map.tileMap[WaterY * 128 + WaterX] = 1;
    map.attributeMap[WaterY * 128 + WaterX] = 2;
    std::array<OutdoorTerrainTile, 256> tiles;
    tiles[0].valid = true;
    tiles[1].valid = true;
    tiles[1].water = true;
    tiles[1].waterSurface = true;
    tiles[1].liquid = LiquidKind::Water;
    std::vector<uint8_t> distance(128 * 128, 255);
    distance[WaterY * 128 + WaterX] = encodedDepth;
    OutdoorTerrainMaterialShore shore;
    shore.range = 1024.0f;
    shore.seabedSlope = 0.4f;
    shore.seabedDepth = 96.0f;
    map.waterDepth = buildOutdoorWaterDepthData(map, tiles, shore, std::move(distance), 128);
    return map;
}

float waterCenterX()
{
    return outdoorGridCornerWorldX(WaterX) + 256.0f;
}

float waterCenterY()
{
    return outdoorGridCornerWorldY(WaterY) - 256.0f;
}
}

TEST_CASE("outdoor shallow water supports the party on its bed without drowning")
{
    const OutdoorMapData map = waterMap(112);
    const float x = waterCenterX();
    const float y = waterCenterY();
    const float depth = *map.waterDepth->depth(x, y);
    REQUIRE(depth > 0.0f);
    REQUIRE(depth < OutdoorWaterDepthData::WadingDepth);
    OutdoorMovementDriver driver(map, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    driver.initialize(x, y, 128.0f);
    CHECK(driver.state().supportOnWater);
    CHECK(driver.state().footZ == doctest::Approx(128.0f - depth + 1.0f));
    driver.update({}, 2.0f);
    CHECK(driver.pendingEffects().waterDamageTicks == 0);
}

TEST_CASE("outdoor party can enter and leave shallow water without water walking")
{
    const OutdoorMapData map = waterMap(112);
    OutdoorMovementDriver driver(map, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    driver.initialize(waterCenterX() + 512.0f, waterCenterY(), 128.0f);
    OutdoorMovementInput input;
    input.forward = true;
    input.yawRadians = 3.14159265f;
    for (int frame = 0; frame < 160; ++frame)
    {
        driver.update(input, 1.0f / 128.0f);
    }
    CHECK(driver.state().x < waterCenterX() + 256.0f);
    CHECK(driver.pendingEffects().waterDamageTicks == 0);
    input.yawRadians = 0.0f;
    for (int frame = 0; frame < 160; ++frame)
    {
        driver.update(input, 1.0f / 128.0f);
    }
    CHECK(driver.state().x > waterCenterX() + 256.0f);
    CHECK_FALSE(driver.state().supportOnWater);
}

TEST_CASE("outdoor opaque seabed draw limit does not make deep water safe")
{
    const OutdoorMapData map = waterMap(0);
    REQUIRE(*map.waterDepth->depth(waterCenterX(), waterCenterY()) > OutdoorWaterDepthData::WadingDepth);
    OutdoorMovementDriver driver(map, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    driver.initialize(waterCenterX(), waterCenterY(), 128.0f);
    driver.update({}, 1.0f);
    CHECK(driver.pendingEffects().waterDamageTicks == 1);
}

TEST_CASE("outdoor water walking stays on the water surface and prevents drowning")
{
    const OutdoorMapData map = waterMap(0);
    OutdoorMovementDriver driver(map, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    driver.initialize(waterCenterX(), waterCenterY(), 128.0f);
    driver.setWaterWalkActive(true);
    driver.update({}, 1.0f);
    CHECK(driver.state().footZ == doctest::Approx(129.0f));
    CHECK(driver.pendingEffects().waterDamageTicks == 0);
}

TEST_CASE("outdoor deep water still blocks ordinary walking past the shallows")
{
    const OutdoorMapData map = waterMap(0);
    OutdoorMovementDriver driver(map, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    driver.initialize(waterCenterX() + 320.0f, waterCenterY(), 128.0f);
    OutdoorMovementInput input;
    input.forward = true;
    input.yawRadians = 3.14159265f;
    for (int frame = 0; frame < 256; ++frame)
    {
        driver.update(input, 1.0f / 128.0f);
    }
    REQUIRE(map.waterDepth->depth(driver.state().x, driver.state().y));
    CHECK(*map.waterDepth->depth(driver.state().x, driver.state().y) <= OutdoorWaterDepthData::WadingDepth);
    CHECK(driver.pendingEffects().waterDamageTicks == 0);
}

TEST_CASE("outdoor solid bridge support does not inherit the deep water beneath it")
{
    OutdoorMapData map = waterMap(0);
    const int x = int(waterCenterX());
    const int y = int(waterCenterY());
    OutdoorBModel bridge;
    bridge.vertices = {{x - 128, y - 128, 256}, {x + 128, y - 128, 256},
        {x + 128, y + 128, 256}, {x - 128, y + 128, 256}};
    OutdoorBModelFace face;
    face.planeNormalZ = 65536;
    face.planeDistance = -256 * 65536;
    face.polygonType = 3;
    face.vertexIndices = {0, 1, 2, 3};
    bridge.faces.push_back(face);
    map.bmodels.push_back(std::move(bridge));
    OutdoorMovementDriver driver(map, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    driver.initialize(float(x), float(y), 256.0f);
    CHECK(driver.state().supportKind == OutdoorSupportKind::BModelFace);
    CHECK_FALSE(driver.state().supportOnWater);
    driver.update({}, 1.0f);
    CHECK(driver.pendingEffects().waterDamageTicks == 0);
}

TEST_CASE("outdoor shallow water calculation does not make other liquids safe")
{
    OutdoorMapData map = waterMap(112);
    map.waterDepth->otherLiquids[WaterY * 128 + WaterX] = 1;
    map.attributeMap[WaterY * 128 + WaterX] = 3;
    CHECK_FALSE(map.waterDepth->depth(waterCenterX(), waterCenterY()));
    OutdoorMovementDriver driver(map, std::nullopt, std::nullopt, std::nullopt, std::nullopt);
    driver.initialize(waterCenterX(), waterCenterY(), 128.0f);
    driver.update({}, 1.0f);
    CHECK(driver.pendingEffects().burningDamageTicks == 1);
}

TEST_CASE("outdoor shore depth stops at dry land and preserves sloping water levels")
{
    OutdoorMapData map = waterMap(112);
    const float x = waterCenterX();
    const float y = waterCenterY();
    CHECK(*map.waterDepth->depth(x + 512.0f, y) == 0.0f);
    CHECK_FALSE(map.waterDepth->movementHeight(x + 512.0f, y, false));
    const size_t northWest = WaterY * 128 + WaterX;
    map.waterDepth->levels[northWest] = 128.0f;
    map.waterDepth->levels[northWest + 1] = 160.0f;
    map.waterDepth->levels[northWest + 128] = 192.0f;
    map.waterDepth->levels[northWest + 129] = 224.0f;
    CHECK(*map.waterDepth->movementHeight(x, y, true) == doctest::Approx(176.0f));
    map.waterDepth->levels.assign(128 * 128, std::numeric_limits<float>::quiet_NaN());
    CHECK_FALSE(map.waterDepth->depth(x, y));
}
