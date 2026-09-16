#include "doctest/doctest.h"

#include "game/outdoor/OutdoorSunlight.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorLightingData.h"

using namespace OpenYAMM::Game;

TEST_CASE("outdoor sunlight uses atmosphere brightness for night surfaces and ordinary sprites")
{
    const OutdoorMapData map = {};
    OutdoorWorldRuntime::AtmosphereState atmosphere = {};
    atmosphere.isNight = true;
    atmosphere.ambientBrightness = 0.255634f; // Existing daily ambient curve at 03:30.
    atmosphere.sunDirectionZ = 1.0f;
    const std::array<float, 4> night = buildOutdoorSunlight(map, atmosphere);
    CHECK(night[0] == 0.0f);
    CHECK(night[1] == 0.0f);
    CHECK(night[2] == 0.0f);
    CHECK(night[3] == doctest::Approx(0.255634f));
    CHECK(outdoorBillboardBaseLight(night) == doctest::Approx(night[3]));

    atmosphere.isNight = false;
    atmosphere.fogDensity = 0.0f;
    atmosphere.ambientBrightness = 0.69f;
    const std::array<float, 4> noon = buildOutdoorSunlight(map, atmosphere);
    CHECK(noon[2] == doctest::Approx(0.99f));
    CHECK(noon[3] == doctest::Approx(0.69f));
    CHECK(outdoorBillboardBaseLight(noon) == doctest::Approx(0.85f));
}

TEST_CASE("outdoor sunlight fades direct illumination through atmospheric twilight")
{
    const OutdoorMapData map = {};
    OutdoorWorldRuntime::AtmosphereState atmosphere = {};
    atmosphere.isNight = false;
    atmosphere.ambientBrightness = 0.4f;
    atmosphere.sunDirectionX = 0.8f;
    atmosphere.sunDirectionZ = 0.6f;
    atmosphere.fogDensity = 0.0f;
    const std::array<float, 4> day = buildOutdoorSunlight(map, atmosphere);
    atmosphere.fogDensity = 0.5f;
    const std::array<float, 4> twilight = buildOutdoorSunlight(map, atmosphere);
    CHECK(twilight[0] == doctest::Approx(day[0] * 0.5f));
    CHECK(twilight[2] == doctest::Approx(day[2] * 0.5f));
    CHECK(twilight[3] == doctest::Approx(day[3]));
    atmosphere.fogDensity = 1.0f;
    const std::array<float, 4> horizon = buildOutdoorSunlight(map, atmosphere);
    CHECK(horizon[0] == 0.0f);
    CHECK(horizon[2] == 0.0f);
    CHECK(outdoorBillboardBaseLight(horizon) == doctest::Approx(atmosphere.ambientBrightness));
}

TEST_CASE("outdoor sunlight excludes underwater and authored polygon worlds")
{
    OutdoorMapData map = {};
    OutdoorWorldRuntime::AtmosphereState atmosphere = {};
    atmosphere.isNight = false;
    atmosphere.fogDensity = 0.0f;
    atmosphere.sunDirectionZ = 1.0f;
    REQUIRE(buildOutdoorSunlight(map, atmosphere)[2] > 0.0f);
    atmosphere.underwater = true;
    CHECK(buildOutdoorSunlight(map, atmosphere)[3] == 1.0f);
    atmosphere.underwater = false;
    map.sceneProfile = OutdoorSceneProfile::BModelWorld;
    CHECK(buildOutdoorSunlight(map, atmosphere)[3] == 1.0f);
    map.sceneProfile = OutdoorSceneProfile::ClassicOdm;
    map.locationType = OutdoorLocationType::Enclosed;
    CHECK(buildOutdoorSunlight(map, atmosphere)[3] == 1.0f);
    map.locationType = OutdoorLocationType::Exterior;
    map.lightingData.emplace();
    const std::array<float, 4> authored = buildOutdoorSunlight(map, atmosphere);
    CHECK(authored[2] == 0.0f);
    CHECK(authored[3] == 1.0f);
    CHECK(outdoorBillboardBaseLight(authored) == doctest::Approx(0.85f));
}

TEST_CASE("outdoor sunlight terrain normals agree across cells on a slope")
{
    OutdoorMapData map = {};
    map.heightMap.resize(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight);
    for (int y = 0; y < OutdoorMapData::TerrainHeight; ++y)
    {
        for (int x = 0; x < OutdoorMapData::TerrainWidth; ++x)
        {
            map.heightMap[y * OutdoorMapData::TerrainWidth + x] = static_cast<uint8_t>(x);
        }
    }
    const bx::Vec3 normal = sampleOutdoorRenderedTerrainNormal(map, 100.0f, -100.0f);
    CHECK(normal.x < 0.0f);
    CHECK(normal.y == doctest::Approx(0.0f));
    CHECK(normal.z > 0.0f);
    CHECK(bx::dot(normal, normal) == doctest::Approx(1.0f));
    for (const bx::Vec3 point : {bx::Vec3{450.0f, -450.0f, 0.0f}, bx::Vec3{600.0f, -100.0f, 0.0f}})
    {
        const bx::Vec3 neighbor = sampleOutdoorRenderedTerrainNormal(map, point.x, point.y);
        CHECK(bx::dot(normal, neighbor) == doctest::Approx(1.0f));
    }
    OutdoorWorldRuntime::AtmosphereState atmosphere = {};
    atmosphere.isNight = false;
    atmosphere.fogDensity = 0.0f;
    atmosphere.sunDirectionX = 0.8f;
    atmosphere.sunDirectionZ = 0.6f;
    const std::array<float, 4> morning = buildOutdoorSunlight(map, atmosphere);
    atmosphere.sunDirectionX = -0.8f;
    const std::array<float, 4> evening = buildOutdoorSunlight(map, atmosphere);
    CHECK(bx::dot(normal, bx::Vec3{evening[0], evening[1], evening[2]})
        > bx::dot(normal, bx::Vec3{morning[0], morning[1], morning[2]}));
}

TEST_CASE("outdoor lighting baked weights fade sun at dusk and preserve sky at night")
{
    OutdoorWorldRuntime::AtmosphereState atmosphere = {};
    atmosphere.isNight = false;
    atmosphere.ambientBrightness = 0.69f;
    atmosphere.fogDensity = 0.0f;
    CHECK(outdoorBakedLightingWeights(atmosphere)[0] == doctest::Approx(1.0f));
    CHECK(outdoorBakedLightingWeights(atmosphere)[1] == doctest::Approx(1.0f));
    atmosphere.fogDensity = 1.0f;
    CHECK(outdoorBakedLightingWeights(atmosphere)[0] == 0.0f);
    CHECK(outdoorBakedLightingWeights(atmosphere)[1] == doctest::Approx(0.12f));
    atmosphere.isNight = true;
    atmosphere.fogDensity = 0.0f;
    CHECK(outdoorBakedLightingWeights(atmosphere)[0] == 0.0f);
    CHECK(outdoorBakedLightingWeights(atmosphere)[1] == doctest::Approx(0.12f));
}
