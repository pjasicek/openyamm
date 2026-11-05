#include "doctest/doctest.h"

#include "game/indoor/IndoorLightingRuntime.h"
#include "game/indoor/IndoorModelLighting.h"
#include "game/maps/IndoorSceneYml.h"

#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
uint32_t abgr(uint32_t red, uint32_t green, uint32_t blue, uint32_t alpha)
{
    return (alpha << 24) | (blue << 16) | (green << 8) | red;
}

std::string readSceneText(const char *pRelativePath)
{
    std::ifstream stream(std::filesystem::path(OPENYAMM_SOURCE_DIR) / pRelativePath);
    REQUIRE(stream.good());
    std::ostringstream text;
    text << stream.rdbuf();
    return text.str();
}
}

TEST_CASE("indoor model lighting: disabled by default, MM9's ModelAdd")
{
    const IndoorModelLighting lighting = {};
    CHECK_FALSE(lighting.enabled);
    CHECK(lighting.add[0] == doctest::Approx(30.0f / 255.0f));
    CHECK(lighting.lightScale == 1.0f);
}

TEST_CASE("indoor model lighting: MM9's falloff and the clamped sum")
{
    CHECK(indoorModelLightFalloff(0.0f, 300.0f) == 1.0f);
    CHECK(indoorModelLightFalloff(150.0f * 150.0f, 300.0f) == doctest::Approx(0.75f));
    CHECK(indoorModelLightFalloff(300.0f * 300.0f, 300.0f) == 0.0f);
    CHECK(indoorModelLightFalloff(400.0f * 400.0f, 300.0f) == 0.0f);
    CHECK(indoorModelLightFalloff(10.0f, 0.0f) == 0.0f);

    // Klusos House: AmbientLight 60, ModelAdd 30, a (231, 157, 90) light at half strength.
    IndoorModelLighting lighting = {};
    lighting.enabled = true;
    lighting.ambient = {60.0f / 255.0f, 60.0f / 255.0f, 60.0f / 255.0f};
    const std::array<float, 3> base = indoorModelLight(lighting, {0.0f, 0.0f, 0.0f});
    CHECK(base[0] == doctest::Approx(90.0f / 255.0f));
    const std::array<float, 3> lit =
        indoorModelLight(lighting, {231.0f / 255.0f * 0.5f, 157.0f / 255.0f * 0.5f, 90.0f / 255.0f * 0.5f});
    CHECK(lit[0] == doctest::Approx((90.0f + 115.5f) / 255.0f));
    CHECK(lit[2] == doctest::Approx((90.0f + 45.0f) / 255.0f));
    // MM9 clamps each channel at 255.
    const std::array<float, 3> saturated = indoorModelLight(lighting, {231.0f / 255.0f, 0.0f, 0.0f});
    CHECK(saturated[0] == 1.0f);
    CHECK(saturated[1] == doctest::Approx(90.0f / 255.0f));
}

TEST_CASE("indoor model lighting: a sprite takes each light at its BLV colour, without occlusion")
{
    IndoorLightingFrame frame = {};
    IndoorRenderLight light = {};
    light.position = {0.0f, 0.0f, 0.0f};
    light.radius = 300.0f;
    // A map light as the frame carries it: its colour at the map-light alpha.
    light.colorAbgr = abgr(231, 157, 90, 224);
    light.intensity = 1.0f;
    light.sectorId = 0;
    frame.lights.push_back(light);
    frame.lightIndicesBySector.resize(2);
    frame.lightIndicesBySector[0].push_back(0);

    const std::array<float, 3> atHalf = IndoorLightingRuntime::sampleModelLightRgb(frame, {150.0f, 0.0f, 0.0f}, 1.0f);
    CHECK(atHalf[0] == doctest::Approx(231.0f / 255.0f * 0.75f));
    CHECK(atHalf[1] == doctest::Approx(157.0f / 255.0f * 0.75f));
    CHECK(atHalf[2] == doctest::Approx(90.0f / 255.0f * 0.75f));
    const std::array<float, 3> scaled = IndoorLightingRuntime::sampleModelLightRgb(frame, {150.0f, 0.0f, 0.0f}, 0.5f);
    CHECK(scaled[0] == doctest::Approx(231.0f / 255.0f * 0.375f));
    CHECK(IndoorLightingRuntime::sampleModelLightRgb(frame, {301.0f, 0.0f, 0.0f}, 1.0f)[0] == 0.0f);
    // A second light in another room adds as well (MM9 has no occlusion for models).
    light.sectorId = 1;
    frame.lights.push_back(light);
    frame.lightIndicesBySector[1].push_back(1);
    CHECK(IndoorLightingRuntime::sampleModelLightRgb(frame, {150.0f, 0.0f, 0.0f}, 1.0f)[0]
        == doctest::Approx(2.0f * atHalf[0]));
}

TEST_CASE("indoor model lighting: block parsing and refusals")
{
    IndoorModelLighting lighting = {};
    std::string error;
    REQUIRE(parseIndoorSceneModelLighting("{mode: mm9, ambient: [60, 60, 51]}", lighting, error));
    CHECK(lighting.enabled);
    CHECK(lighting.ambient[0] == doctest::Approx(60.0f / 255.0f));
    CHECK(lighting.ambient[2] == doctest::Approx(0.2f));
    CHECK(lighting.add[1] == doctest::Approx(30.0f / 255.0f));
    CHECK(lighting.lightScale == 1.0f);

    REQUIRE(parseIndoorSceneModelLighting(
        "{mode: mm9, ambient: [0, 0, 0], add: [0, 255, 10], light_scale: 1.5}", lighting, error));
    CHECK(lighting.add[0] == 0.0f);
    CHECK(lighting.add[1] == 1.0f);
    CHECK(lighting.lightScale == 1.5f);

    const IndoorModelLighting before = lighting;
    CHECK_FALSE(parseIndoorSceneModelLighting("{mode: mm8, ambient: [0, 0, 0]}", lighting, error));
    CHECK_FALSE(parseIndoorSceneModelLighting("{ambient: [0, 0, 0]}", lighting, error));
    CHECK_FALSE(parseIndoorSceneModelLighting("{mode: mm9}", lighting, error));
    CHECK_FALSE(parseIndoorSceneModelLighting("{mode: mm9, ambient: [0, 0]}", lighting, error));
    CHECK_FALSE(parseIndoorSceneModelLighting("{mode: mm9, ambient: [0, 0, 256]}", lighting, error));
    CHECK_FALSE(parseIndoorSceneModelLighting("{mode: mm9, ambient: [0, 0, 0], add: [-1, 0, 0]}", lighting, error));
    CHECK_FALSE(parseIndoorSceneModelLighting("{mode: mm9, ambient: [0, 0, 0], light_scale: -1}", lighting, error));
    CHECK_FALSE(parseIndoorSceneModelLighting("[1, 2, 3]", lighting, error));
    CHECK(lighting.lightScale == before.lightScale);
    CHECK(lighting.add == before.add);
}

TEST_CASE("indoor model lighting: a scene without the block keeps the native lighting")
{
    const std::string sceneText = readSceneText("assets_dev/worlds/mm6/maps/6d02.scene.yml");
    std::string error;
    const std::optional<IndoorSceneData> scene = IndoorSceneYmlLoader{}.loadFromText(sceneText, error);
    REQUIRE_MESSAGE(scene, error);
    CHECK_FALSE(scene->modelLighting.enabled);

    const std::optional<IndoorSceneData> mm9Scene = IndoorSceneYmlLoader{}.loadFromText(
        sceneText + "\nmodel_lighting: {mode: mm9, ambient: [60, 60, 60]}\n", error);
    REQUIRE_MESSAGE(mm9Scene, error);
    CHECK(mm9Scene->modelLighting.enabled);
    CHECK(mm9Scene->modelLighting.ambient[1] == doctest::Approx(60.0f / 255.0f));

    // An overlay's block replaces the base scene's; an overlay without one keeps it.
    IndoorSceneData overlaid = *scene;
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(
        overlaid, "format_version: 1\nkind: indoor_scene_overlay\nmodel_lighting: {mode: mm9, ambient: [50, 50, 50]}\n",
        error), error);
    CHECK(overlaid.modelLighting.enabled);
    CHECK(overlaid.modelLighting.ambient[0] == doctest::Approx(50.0f / 255.0f));
    CHECK_FALSE(IndoorSceneYmlLoader{}.loadFromText(sceneText + "\nmodel_lighting: {mode: mm9}\n", error));
}
