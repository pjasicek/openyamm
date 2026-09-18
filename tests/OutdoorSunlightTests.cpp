#include "doctest/doctest.h"

#include "game/outdoor/OutdoorSunlight.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorLightingData.h"

#include <fstream>

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

TEST_CASE("outdoor lighting source colors preserve clock weights and tune sun and sky independently")
{
    OutdoorWorldRuntime::AtmosphereState atmosphere = {};
    atmosphere.isNight = false;
    atmosphere.ambientBrightness = 0.69f;
    atmosphere.fogDensity = 0.0f;
    GameSettings settings;
    // Explicit identity settings still reproduce the authored bake, independently of presentation defaults.
    settings.bakedSkyStrength = 1.0f;
    settings.bakedSkyColor = {1.0f, 1.0f, 1.0f};
    for (const bool night : {false, true})
    {
        atmosphere.isNight = night;
        const std::array<float, 4> weights = outdoorBakedLightingWeights(atmosphere);
        const auto colors = outdoorBakedLightingColors(atmosphere, settings);
        for (size_t channel = 0; channel < 3; ++channel)
        {
            CHECK(colors[0][channel] == doctest::Approx(weights[0]));
            CHECK(colors[1][channel] == doctest::Approx(weights[1]));
        }
    }
    atmosphere.isNight = false;
    settings.bakedSunStrength = 0.5f;
    settings.bakedSkyStrength = 2.0f;
    settings.bakedSunColor = {1.0f, 0.8f, 0.6f};
    settings.bakedSkyColor = {0.65f, 0.8f, 1.0f};
    const auto day = outdoorBakedLightingColors(atmosphere, settings);
    CHECK(day[0][0] == doctest::Approx(0.5f));
    CHECK(day[0][2] == doctest::Approx(0.3f));
    CHECK(day[1][0] == doctest::Approx(1.3f));
    CHECK(day[1][2] == doctest::Approx(2.0f));
    atmosphere.fogDensity = 0.5f;
    const auto dusk = outdoorBakedLightingColors(atmosphere, settings);
    CHECK(dusk[0][0] == doctest::Approx(0.25f));
    CHECK(dusk[1][2] == doctest::Approx(1.12f));
    atmosphere.isNight = true;
    const auto night = outdoorBakedLightingColors(atmosphere, settings);
    CHECK(night[0][0] == 0.0f);
    CHECK(night[1][2] == doctest::Approx(0.24f));
    settings.bakedSkyStrength = 0.0f;
    CHECK(outdoorBakedLightingColors(atmosphere, settings)[1][2] == 0.0f);
}

TEST_CASE("baked lighting settings validate input atomically and round trip through the INI")
{
    GameSettings settings;
    settings.lightmaps = false;
    std::string error;
    REQUIRE(setBakedLightingSetting(settings, "baked_sun_strength", "0.75", error));
    REQUIRE(setBakedLightingSetting(settings, "baked_sky_strength", "2", error));
    REQUIRE(setBakedLightingSetting(settings, "baked_sun_color", "1, 0.9, 0.8", error));
    REQUIRE(setBakedLightingSetting(settings, "baked_sky_color", "0.65,0.8,1", error));
    const std::array<float, 3> original = settings.bakedSkyColor;
    for (const char *pInvalid : {"nan", "inf", "-1", "17", "", "1junk"})
    {
        CAPTURE(pInvalid);
        CHECK_FALSE(setBakedLightingSetting(settings, "baked_sky_strength", pInvalid, error));
        CHECK_FALSE(error.empty());
        CHECK(settings.bakedSkyStrength == 2.0f);
    }
    for (const char *pInvalid : {"1,1", "1,1,1,1", "1,1,1,", "1,,1", "1,1,nan", "1,-1,1", "1,1,2", ""})
    {
        CAPTURE(pInvalid);
        CHECK_FALSE(setBakedLightingSetting(settings, "baked_sky_color", pInvalid, error));
        CHECK_FALSE(error.empty());
        CHECK(settings.bakedSkyColor == original);
    }
    CHECK_FALSE(getBakedLightingSetting(settings, "not_a_setting"));
    CHECK_FALSE(setBakedLightingSetting(settings, "not_a_setting", "1", error));
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-baked-lighting-test.ini";
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE(loaded);
    CHECK_FALSE(loaded->lightmaps);
    CHECK(loaded->bakedSunStrength == settings.bakedSunStrength);
    CHECK(loaded->bakedSkyStrength == settings.bakedSkyStrength);
    CHECK(loaded->bakedSunColor == settings.bakedSunColor);
    CHECK(loaded->bakedSkyColor == settings.bakedSkyColor);
    {
        std::ofstream output(path);
        output << "[video]\nbaked_sky_color=1,1,nan\n";
    }
    CHECK_FALSE(loadGameSettings(path, error));
    CHECK(error.find("baked_sky_color") != std::string::npos);
    {
        std::ofstream output(path);
        output << "[video]\n";
    }
    const std::optional<GameSettings> legacy = loadGameSettings(path, error);
    REQUIRE(legacy);
    CHECK(legacy->lightmaps);
    CHECK(legacy->bakedSunStrength == 1.0f);
    CHECK(legacy->bakedSkyStrength == 3.0f);
    CHECK(legacy->bakedSkyColor[0] == doctest::Approx(0.8f));
    CHECK(legacy->bakedSkyColor[1] == doctest::Approx(0.9f));
    CHECK(legacy->bakedSkyColor == GameSettings{}.bakedSkyColor);
    CHECK(legacy->cinematicGrading);
    CHECK(legacy->cinematicStrength == 60);
    std::filesystem::remove(path);
}

TEST_CASE("material bake sun direction derives a unit vector from recipe angles")
{
    const std::optional<bx::Vec3> northWest = surfaceMaterialBakeSunDirection(315.0f, 45.0f);
    REQUIRE(northWest.has_value());
    CHECK(northWest->x == doctest::Approx(0.5f).epsilon(0.001f));
    CHECK(northWest->y == doctest::Approx(-0.5f).epsilon(0.001f));
    CHECK(northWest->z == doctest::Approx(0.7071f).epsilon(0.001f));

    const std::optional<bx::Vec3> east = surfaceMaterialBakeSunDirection(90.0f, 0.0f);
    REQUIRE(east.has_value());
    CHECK(east->x == doctest::Approx(0.0f).epsilon(0.001f));
    CHECK(east->y == doctest::Approx(1.0f).epsilon(0.001f));
    CHECK(east->z == doctest::Approx(0.0f).epsilon(0.001f));

    const std::optional<bx::Vec3> zenith = surfaceMaterialBakeSunDirection(0.0f, 90.0f);
    REQUIRE(zenith.has_value());
    CHECK(zenith->x == doctest::Approx(0.0f).epsilon(0.001f));
    CHECK(zenith->y == doctest::Approx(0.0f).epsilon(0.001f));
    CHECK(zenith->z == doctest::Approx(1.0f).epsilon(0.001f));

    // Full-circle azimuths stay finite and unit length.
    const std::optional<bx::Vec3> wrapped = surfaceMaterialBakeSunDirection(315.0f + 360.0f, 45.0f);
    REQUIRE(wrapped.has_value());
    CHECK(wrapped->x == doctest::Approx(northWest->x).epsilon(0.001f));
    CHECK(wrapped->y == doctest::Approx(northWest->y).epsilon(0.001f));
    CHECK(wrapped->z == doctest::Approx(northWest->z).epsilon(0.001f));
}

TEST_CASE("material sun inputs follow the diffuse-disabled sun policy inverts")
{
    GameSettings settings = {};
    OutdoorWorldRuntime::AtmosphereState atmosphere = {};
    atmosphere.isNight = false;
    atmosphere.fogDensity = 0.0f;
    atmosphere.ambientBrightness = 0.69f;
    atmosphere.sunDirectionX = 0.8f;
    atmosphere.sunDirectionZ = 0.6f;

    SUBCASE("nonbaked classic exterior uses atmosphere direction and daylight gating")
    {
        const OutdoorMapData map = {};
        const OutdoorMaterialSunInputs day =
            buildOutdoorMaterialSunInputs(map, atmosphere, settings, false, {0.0f, 0.0f, 0.0f});
        CHECK(day.enabled);
        CHECK(day.direction.x == doctest::Approx(0.8f).epsilon(0.01f));
        CHECK(day.direction.z == doctest::Approx(0.6f).epsilon(0.01f));
        CHECK(day.color[0] == doctest::Approx(0.99f).epsilon(0.001f));

        atmosphere.isNight = true;
        const OutdoorMaterialSunInputs night =
            buildOutdoorMaterialSunInputs(map, atmosphere, settings, false, {0.0f, 0.0f, 0.0f});
        CHECK(!night.enabled);
    }

    SUBCASE("paired baked exterior with applied lightmaps uses the fixed bake direction")
    {
        OutdoorMapData map = {};
        map.lightingData = OutdoorLightingData{};
        map.lightingData->bakedSourcePages = true;
        const bx::Vec3 bakeDirection = {0.5f, -0.5f, 0.7071f};
        const OutdoorMaterialSunInputs baked =
            buildOutdoorMaterialSunInputs(map, atmosphere, settings, true, bakeDirection);
        CHECK(baked.enabled);
        CHECK(baked.direction.x == doctest::Approx(0.5f).epsilon(0.001f));
        CHECK(baked.direction.y == doctest::Approx(-0.5f).epsilon(0.001f));
        CHECK(baked.direction.z == doctest::Approx(0.7071f).epsilon(0.001f));
        // Night attenuates the baked sun response to zero together with the diffuse weights.
        atmosphere.isNight = true;
        const OutdoorMaterialSunInputs bakedNight =
            buildOutdoorMaterialSunInputs(map, atmosphere, settings, true, bakeDirection);
        CHECK(bakedNight.enabled);
        CHECK(bakedNight.color[0] == doctest::Approx(0.0f).epsilon(0.001f));
        CHECK(bakedNight.color[1] == doctest::Approx(0.0f).epsilon(0.001f));
        CHECK(bakedNight.color[2] == doctest::Approx(0.0f).epsilon(0.001f));
    }

    SUBCASE("paired bake with lightmaps disabled falls back to the atmosphere direction")
    {
        OutdoorMapData map = {};
        map.lightingData = OutdoorLightingData{};
        map.lightingData->bakedSourcePages = true;
        settings.lightmaps = false;
        const OutdoorMaterialSunInputs fallback =
            buildOutdoorMaterialSunInputs(map, atmosphere, settings, true, {0.0f, 0.0f, 1.0f});
        CHECK(fallback.enabled);
        CHECK(fallback.direction.x == doctest::Approx(0.8f).epsilon(0.01f));
        CHECK(fallback.direction.z == doctest::Approx(0.6f).epsilon(0.01f));
    }

    SUBCASE("underwater and authored polygon worlds carry no directional sheen")
    {
        OutdoorWorldRuntime::AtmosphereState underwaterAtmosphere = atmosphere;
        underwaterAtmosphere.underwater = true;
        const OutdoorMapData map = {};
        CHECK(!buildOutdoorMaterialSunInputs(map, underwaterAtmosphere, settings, true, {0.0f, 0.0f, 1.0f})
                  .enabled);

        OutdoorMapData bmodelWorldMap = {};
        bmodelWorldMap.sceneProfile = OutdoorSceneProfile::BModelWorld;
        CHECK(!buildOutdoorMaterialSunInputs(bmodelWorldMap, atmosphere, settings, true, {0.0f, 0.0f, 1.0f})
                  .enabled);
    }
}
