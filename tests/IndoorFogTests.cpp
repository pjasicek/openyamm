#include "doctest/doctest.h"

#include "game/indoor/IndoorFog.h"
#include "game/maps/IndoorSceneYml.h"

#include <string>

using namespace OpenYAMM::Game;

TEST_CASE("indoor fog: disabled by default, and the uniforms are the old constants")
{
    const IndoorFog fog = {};
    CHECK_FALSE(fog.enabled);
    CHECK(indoorFogRatio(fog, 1.0e6f) == 0.0f);
    CHECK(indoorFogColorUniform(fog) == std::array<float, 4>{0.0f, 0.0f, 0.0f, 0.0f});
    CHECK(indoorFogDensitiesUniform(fog) == std::array<float, 4>{0.0f, 0.0f, 0.0f, 0.0f});
    CHECK(indoorFogDistancesUniform(fog) == std::array<float, 4>{4096.0f, 4096.0f, 4096.0f, 0.0f});
}

TEST_CASE("indoor fog: linear between near and far")
{
    IndoorFog fog = {};
    fog.enabled = true;
    fog.nearDistance = 100.0f;
    fog.farDistance = 300.0f;
    CHECK(indoorFogRatio(fog, 0.0f) == 0.0f);
    CHECK(indoorFogRatio(fog, 100.0f) == 0.0f);
    CHECK(indoorFogRatio(fog, 200.0f) == doctest::Approx(0.5f));
    CHECK(indoorFogRatio(fog, 300.0f) == 1.0f);
    CHECK(indoorFogRatio(fog, 5000.0f) == 1.0f);
    CHECK(indoorFogDensitiesUniform(fog)[3] == 1.0f);
    CHECK(indoorFogDistancesUniform(fog)[0] == 100.0f);
    CHECK(indoorFogDistancesUniform(fog)[1] == 300.0f);
}

TEST_CASE("indoor fog: scene parsing and refusals")
{
    IndoorFog fog = {};
    std::string error;
    REQUIRE(parseIndoorSceneFog("{color_rgb: [255, 0, 51], near_distance: 2.56, far_distance: 12800}", fog, error));
    CHECK(fog.enabled);
    CHECK(fog.color[0] == 1.0f);
    CHECK(fog.color[2] == doctest::Approx(0.2f));
    CHECK(fog.nearDistance == doctest::Approx(2.56f));
    CHECK(fog.farDistance == 12800.0f);

    const IndoorFog before = fog;
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0], near_distance: 1, far_distance: 2}", fog, error));
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0, 300], near_distance: 1, far_distance: 2}", fog, error));
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0, 0], near_distance: 5, far_distance: 5}", fog, error));
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0, 0], near_distance: -1, far_distance: 5}", fog, error));
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0, 0], far_distance: 5}", fog, error));
    CHECK_FALSE(parseIndoorSceneFog("[1, 2, 3]", fog, error));
    CHECK(fog.farDistance == before.farDistance);
}

TEST_CASE("indoor fog: MM9's model and night state are opt-in")
{
    IndoorFog fog = {};
    std::string error;
    REQUIRE_MESSAGE(parseIndoorSceneFog("{color_rgb: [127, 127, 127], near_distance: 64, far_distance: 11520}",
        fog, error), error);
    CHECK_FALSE(fog.lithtech);
    CHECK_FALSE(fog.hasNight);
    // Without the keys the face programs keep the plain fog, and the fog is the same at every hour.
    CHECK(indoorFogModeUniform(fog) == std::array<float, 4>{0.0f, 0.0f, 0.0f, 0.0f});
    CHECK(indoorFogLightUniform(fog) == std::array<float, 4>{0.0f, 0.0f, 0.0f, 0.0f});
    CHECK(indoorFogAt(fog, 1.0f).color == fog.color);
    CHECK(indoorFogAt(fog, 1.0f).farDistance == fog.farDistance);

    REQUIRE_MESSAGE(parseIndoorSceneFog("{color_rgb: [127, 127, 127], near_distance: 64, far_distance: 11520, "
        "model: lithtech, night: {color_rgb: [0, 0, 0], near_distance: 64, far_distance: 5000}}", fog, error), error);
    CHECK(fog.lithtech);
    REQUIRE(fog.hasNight);
    CHECK(indoorFogModeUniform(fog) == std::array<float, 4>{1.0f, 1.0f, 0.0f, 0.0f});
    const IndoorFog day = indoorFogAt(fog, 0.0f);
    CHECK(day.color[0] == doctest::Approx(127.0f / 255.0f));
    CHECK(day.farDistance == 11520.0f);
    const IndoorFog night = indoorFogAt(fog, 1.0f);
    CHECK(night.color[0] == 0.0f);
    CHECK(night.farDistance == 5000.0f);
    CHECK(night.lithtech);
    const IndoorFog dusk = indoorFogAt(fog, 0.5f);
    CHECK(dusk.color[1] == doctest::Approx(63.5f / 255.0f));
    CHECK(dusk.farDistance == doctest::Approx(8260.0f));

    IndoorFog untouched = {};
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0, 0], near_distance: 1, far_distance: 2, model: d3d}",
        untouched, error));
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0, 0], near_distance: 1, far_distance: 2, density: 3}",
        untouched, error));
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0, 0], near_distance: 1, far_distance: 2, "
        "night: {color_rgb: [0, 0, 0], near_distance: 5, far_distance: 2}}", untouched, error));
    CHECK_FALSE(untouched.enabled);
}

TEST_CASE("indoor fog: following the daylight is opt-in")
{
    IndoorFog fog = {};
    std::string error;
    REQUIRE(parseIndoorSceneFog("{color_rgb: [127, 127, 127], near_distance: 2.56, far_distance: 5120}", fog, error));
    CHECK_FALSE(fog.followsDaylight);
    REQUIRE(parseIndoorSceneFog("{color_rgb: [127, 127, 127], near_distance: 2.56, far_distance: 5120, "
        "follow_daylight: true}", fog, error));
    CHECK(fog.followsDaylight);
    CHECK(indoorFogAt(fog, 1.0f).followsDaylight);
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [127, 127, 127], near_distance: 2.56, far_distance: 5120, "
        "follow_daylight: maybe}", fog, error));
}

TEST_CASE("indoor fog: the open sky's fog cover is opt-in and follows the night state")
{
    IndoorFog fog = {};
    std::string error;
    REQUIRE_MESSAGE(parseIndoorSceneFog("{color_rgb: [127, 127, 127], near_distance: 2.56, far_distance: 5120}",
        fog, error), error);
    CHECK(fog.sky == 0.0f);
    CHECK(indoorFogSkyCover(fog) == 0.0f);
    CHECK(indoorFogSkyCover(IndoorFog{}) == 0.0f);

    // Frosgard City: the same fog day and night, the sky in its colour.
    REQUIRE_MESSAGE(parseIndoorSceneFog("{color_rgb: [127, 127, 127], near_distance: 2.56, far_distance: 5120, "
        "sky: 1, model: lithtech}", fog, error), error);
    CHECK(indoorFogSkyCover(fog) == 1.0f);
    CHECK(indoorFogSkyCover(indoorFogAt(fog, 1.0f)) == 1.0f);

    // Thjorgard City's data: the grey day fog covers the sky, the black night fog leaves it clear.
    REQUIRE_MESSAGE(parseIndoorSceneFog("{color_rgb: [127, 127, 127], near_distance: 64, far_distance: 11520, sky: 1, "
        "night: {color_rgb: [0, 0, 0], near_distance: 64, far_distance: 11520}}", fog, error), error);
    CHECK(fog.nightSky == 0.0f);
    CHECK(indoorFogSkyCover(indoorFogAt(fog, 0.0f)) == 1.0f);
    CHECK(indoorFogSkyCover(indoorFogAt(fog, 0.5f)) == doctest::Approx(0.5f));
    CHECK(indoorFogSkyCover(indoorFogAt(fog, 1.0f)) == 0.0f);
    REQUIRE_MESSAGE(parseIndoorSceneFog("{color_rgb: [0, 0, 0], near_distance: 1, far_distance: 2, "
        "night: {color_rgb: [0, 0, 0], near_distance: 1, far_distance: 2, sky: 0.25}}", fog, error), error);
    CHECK(fog.nightSky == 0.25f);

    IndoorFog untouched = {};
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0, 0], near_distance: 1, far_distance: 2, sky: 2}",
        untouched, error));
    CHECK_FALSE(parseIndoorSceneFog("{color_rgb: [0, 0, 0], near_distance: 1, far_distance: 2, sky: -0.5}",
        untouched, error));
    CHECK_FALSE(untouched.enabled);
}

TEST_CASE("indoor fog: MM9's lightmap pass fog colour")
{
    // d3d.ren's table: 255 sqrt(i / 512), truncated; 127 stays 127, white becomes 179, black stays black.
    const std::array<float, 3> light = indoorFogLightPassColor({127.0f / 255.0f, 1.0f, 0.0f});
    CHECK(light[0] * 255.0f == doctest::Approx(127.0f));
    CHECK(light[1] * 255.0f == doctest::Approx(179.0f));
    CHECK(light[2] == 0.0f);
}

TEST_CASE("indoor fog: a script's fog fades in from the fog shown and out again")
{
    IndoorFog haze = {};
    haze.enabled = true;
    haze.color = {0.5f, 0.5f, 0.5f};
    haze.nearDistance = 20000.0f;
    haze.farDistance = 40000.0f;
    IndoorFog thick = haze;
    thick.color = {0.0f, 0.0f, 1.0f};
    thick.nearDistance = 2.0f;
    thick.farDistance = 16000.0f;
    thick.sky = 1.0f;

    const IndoorFog half = indoorFogBlend(haze, thick, 0.5f);
    CHECK(half.enabled);
    CHECK(half.color[2] == doctest::Approx(0.75f));
    CHECK(half.nearDistance == doctest::Approx(10001.0f));
    CHECK(half.farDistance == doctest::Approx(28000.0f));
    CHECK(half.sky == doctest::Approx(0.5f));
    CHECK(indoorFogBlend(haze, thick, 1.0f).nearDistance == doctest::Approx(2.0f));
    CHECK(indoorFogBlend(haze, thick, 0.0f).nearDistance == doctest::Approx(20000.0f));

    // from no fog: the colour is the new fog's from the start, the distances come in from out of sight
    const IndoorFog none = {};
    const IndoorFog rising = indoorFogBlend(none, thick, 0.5f);
    CHECK(rising.enabled);
    CHECK(rising.color[2] == doctest::Approx(1.0f));
    CHECK(rising.nearDistance > 100000.0f);
    CHECK(indoorFogBlend(none, thick, 1.0f).nearDistance == doctest::Approx(2.0f));
}
