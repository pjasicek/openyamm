#include "doctest/doctest.h"

#include "game/maps/OutdoorSceneYml.h"
#include "game/outdoor/OutdoorMapData.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>

namespace
{
const char *BaseScene = R"yaml(
format_version: 1
kind: outdoor_scene
geometry_file: oute3.odm
rendering:
  view_distance_scale: 1.5
)yaml";

const char *MinimalScene = R"yaml(
format_version: 1
kind: outdoor_scene
geometry_file: oute3.odm
source:
  geometry_file: oute3.odm
)yaml";

const char *PuddleOverlay = R"yaml(
format_version: 1
kind: outdoor_scene_overlay
rendering:
  puddles:
    mask: worlds/mm6/rendering/puddles/oute3.png
    origin: [-32768, 32768]
    extent: [65024, -65024]
)yaml";

bool loadOutE3Scene(OpenYAMM::Game::OutdoorSceneData &data, std::string &error)
{
    const std::filesystem::path scenePath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm6/maps/oute3.scene.yml";
    std::ifstream sceneFile(scenePath);
    REQUIRE(sceneFile.good());

    std::ostringstream sceneText;
    sceneText << sceneFile.rdbuf();

    OpenYAMM::Game::OutdoorSceneYmlLoader loader;
    const std::optional<OpenYAMM::Game::OutdoorSceneData> loaded =
        loader.loadFromText(sceneText.str(), error);

    if (loaded)
    {
        data = *loaded;
        return true;
    }

    return false;
}

bool loadOutE3WithOverlay(const char *overlayText, OpenYAMM::Game::OutdoorSceneData &data, std::string &error)
{
    OpenYAMM::Game::OutdoorSceneYmlLoader loader;

    if (!loadOutE3Scene(data, error))
    {
        return false;
    }

    return loader.applyOverlayFromText(data, overlayText, error);
}
}

TEST_CASE("puddles-only rendering block parses without view_distance_scale")
{
    const char *overlay = R"yaml(
format_version: 1
kind: outdoor_scene_overlay
rendering:
  puddles:
    mask: worlds/mm6/rendering/puddles/oute3.png
    origin: [-100.5, 200.0]
    extent: [512.0, -256.0]
)yaml";

    OpenYAMM::Game::OutdoorSceneData data;
    std::string error;
    CAPTURE(error);
    REQUIRE(loadOutE3WithOverlay(overlay, data, error));
    REQUIRE(data.rendering.puddles.has_value());
    CHECK(data.rendering.puddles->mask == "worlds/mm6/rendering/puddles/oute3.png");
    CHECK(data.rendering.puddles->origin[0] == doctest::Approx(-100.5f));
    CHECK(data.rendering.puddles->origin[1] == doctest::Approx(200.0f));
    CHECK(data.rendering.puddles->extent[0] == doctest::Approx(512.0f));
    CHECK(data.rendering.puddles->extent[1] == doctest::Approx(-256.0f));
    CHECK_FALSE(data.rendering.viewDistanceScale.has_value());
}

TEST_CASE("puddles validation rejects malformed blocks with named errors")
{
    struct Case
    {
        const char *name;
        const char *rendering;
        const char *fragment;
    };
    const Case cases[] = {
        {"empty mask", "  puddles:\n    mask: \"\"\n    origin: [0, 0]\n    extent: [1, 1]\n", "mask"},
        {"bad origin arity", "  puddles:\n    mask: a.png\n    origin: [0]\n    extent: [1, 1]\n", "origin"},
        {"non-finite extent", "  puddles:\n    mask: a.png\n    origin: [0, 0]\n    extent: [.nan, 1]\n", "extent"},
        {"zero extent", "  puddles:\n    mask: a.png\n    origin: [0, 0]\n    extent: [0, 1]\n", "extent"},
    };

    for (const Case &test : cases)
    {
        CAPTURE(test.name);
        const std::string overlay =
            std::string("format_version: 1\nkind: outdoor_scene_overlay\nrendering:\n") + test.rendering;
        OpenYAMM::Game::OutdoorSceneData data;
        std::string error;
        CHECK_FALSE(loadOutE3WithOverlay(overlay.c_str(), data, error));
        CHECK(error.find(test.fragment) != std::string::npos);
    }
}

TEST_CASE("overlay puddles replace while absence keeps base puddles")
{
    OpenYAMM::Game::OutdoorSceneData data;
    std::string error;
    REQUIRE(loadOutE3Scene(data, error));
    OpenYAMM::Game::OutdoorSceneYmlLoader loader;

    // Overlay without a rendering block keeps the base state (no puddles yet).
    REQUIRE(loader.applyOverlayFromText(
        data, "format_version: 1\nkind: outdoor_scene_overlay\n", error));
    CHECK_FALSE(data.rendering.puddles.has_value());
    const std::optional<float> baseScale = data.rendering.viewDistanceScale;

    // Overlay with a puddles block replaces the absent base one.
    REQUIRE(loader.applyOverlayFromText(data, PuddleOverlay, error));
    REQUIRE(data.rendering.puddles.has_value());
    CHECK(data.rendering.puddles->origin[1] == doctest::Approx(32768.0f));
    CHECK(data.rendering.viewDistanceScale == baseScale);

    // A later overlay without puddles keeps the previous puddles.
    REQUIRE(loader.applyOverlayFromText(
        data, "format_version: 1\nkind: outdoor_scene_overlay\nrendering:\n  view_distance_scale: 2.0\n", error));
    REQUIRE(data.rendering.puddles.has_value());
    CHECK(data.rendering.viewDistanceScale == doctest::Approx(2.0f));
}
