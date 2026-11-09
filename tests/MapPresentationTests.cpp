#include "doctest/doctest.h"

#include "engine/ImageAssetLoader.h"
#include "engine/AssetScaleTier.h"
#include "game/maps/MapPresentation.h"
#include "game/ui/GameplayJournalMapUi.h"
#include "game/ui/GameplayMinimapTransform.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

namespace
{
std::vector<uint8_t> readMapAsset(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::vector<uint8_t>(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}
}

TEST_CASE("map presentation catalog resolves elevation variants and omits unlisted maps")
{
    const std::string catalog = R"(
format_version: 1
kind: world_map_presentation_catalog
maps:
  - map: lichlab
    world_bounds: {min_x: -100, max_x: 300, min_y: -200, max_y: 600}
    flip_u: false
    flip_v: true
    reveal_entire_map: true
    variants:
      - {texture: ui/maps/lichlaba.pcx, width: 682, height: 695, maximum_z: 100}
      - {texture: ui/maps/lichlabb.pcx, width: 678, height: 691, minimum_z: 100, maximum_z: 200}
      - {texture: ui/maps/lichlabc.pcx, width: 677, height: 690, minimum_z: 200}
)";
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::MapPresentation> presentation =
        OpenYAMM::Game::loadMapPresentationFromCatalog(catalog, "LICHLAB.blv", errorMessage);

    REQUIRE(presentation.has_value());
    CHECK(errorMessage.empty());
    REQUIRE(OpenYAMM::Game::resolveMapPresentationVariant(*presentation, 100.0f) != nullptr);
    CHECK(OpenYAMM::Game::resolveMapPresentationVariant(*presentation, 100.0f)->textureName
        == "ui/maps/lichlaba.pcx");
    CHECK(OpenYAMM::Game::resolveMapPresentationVariant(*presentation, 150.0f)->textureName
        == "ui/maps/lichlabb.pcx");
    CHECK(OpenYAMM::Game::resolveMapPresentationVariant(*presentation, 250.0f)->textureName
        == "ui/maps/lichlabc.pcx");

    const std::optional<OpenYAMM::Game::MapPresentation> greatGate =
        OpenYAMM::Game::loadMapPresentationFromCatalog(catalog, "greatgate.odm", errorMessage);
    CHECK_FALSE(greatGate.has_value());
    CHECK(errorMessage.empty());
}

TEST_CASE("MM9 map transform preserves flipped world coordinates and source aspect ratio")
{
    OpenYAMM::Game::GameplayMinimapState state = {};
    state.worldMinX = 100.0f;
    state.worldMaxX = 500.0f;
    state.worldMinY = -200.0f;
    state.worldMaxY = 600.0f;
    state.flipU = true;
    state.flipV = false;
    state.zoomWidth = 1000.0f;
    state.zoomHeight = 500.0f;

    const OpenYAMM::Game::GameplayMinimapPoint uv =
        OpenYAMM::Game::gameplayMinimapWorldToUv(state, 200.0f, 0.0f);
    CHECK(uv.x == doctest::Approx(0.75f));
    CHECK(uv.y == doctest::Approx(0.25f));

    const OpenYAMM::Game::GameplayMinimapPoint world =
        OpenYAMM::Game::gameplayMinimapUvToWorld(state, uv.x, uv.y);
    CHECK(world.x == doctest::Approx(200.0f));
    CHECK(world.y == doctest::Approx(0.0f));

    OpenYAMM::Game::GameplayUiController::JournalScreenState journal = {};
    journal.mapCenterX = 300.0f;
    journal.mapCenterY = 200.0f;
    journal.mapZoomStep = 0;
    const OpenYAMM::Game::GameplayJournalMapTransform transform =
        OpenYAMM::Game::gameplayJournalMapTransform(journal, &state, 300.0f, 300.0f);
    CHECK(transform.uSpan == doctest::Approx(1.0f));
    CHECK(transform.vSpan == doctest::Approx(2.0f));
}

TEST_CASE("map party arrow follows the image flips")
{
    constexpr float HalfPi = 1.57079633f;
    OpenYAMM::Game::GameplayMinimapState state = {};

    // Native MM6-MM8 orientation (+X right, +Y up): the heading is unchanged.
    CHECK(OpenYAMM::Game::gameplayMinimapDisplayYaw(state, 0.5f) == doctest::Approx(0.5f));

    // MM9 exteriors are drawn rotated 180 degrees: walking east (+X) moves the marker left.
    state.flipU = true;
    state.flipV = false;
    CHECK(std::abs(OpenYAMM::Game::gameplayMinimapDisplayYaw(state, 0.0f)) == doctest::Approx(2.0f * HalfPi));
    CHECK(OpenYAMM::Game::gameplayMinimapDisplayYaw(state, HalfPi) == doctest::Approx(-HalfPi));

    // Every heading points the way the marker moves on the image.
    for (float yaw = -3.0f; yaw < 3.2f; yaw += 0.25f)
    {
        const OpenYAMM::Game::GameplayMinimapPoint from =
            OpenYAMM::Game::gameplayMinimapWorldToUv(state, 0.0f, 0.0f);
        const OpenYAMM::Game::GameplayMinimapPoint to =
            OpenYAMM::Game::gameplayMinimapWorldToUv(state, std::cos(yaw) * 100.0f, std::sin(yaw) * 100.0f);
        const float displayYaw = OpenYAMM::Game::gameplayMinimapDisplayYaw(state, yaw);
        // Image v grows downwards; the arrow convention has +Y up.
        CHECK(std::cos(displayYaw) * (to.x - from.x) - std::sin(displayYaw) * (to.y - from.y) > 0.0f);
    }
}

TEST_CASE("outdoor map presentation crop and flips preserve saved exploration coordinates")
{
    OpenYAMM::Game::GameplayMinimapState state = {};
    const OpenYAMM::Game::GameplayMinimapPoint legacy =
        OpenYAMM::Game::gameplayMinimapUvToOutdoorRevealUv(state, 0.875f, 0.25f);
    CHECK(legacy.x == doctest::Approx(0.875f));
    CHECK(legacy.y == doctest::Approx(0.25f));

    state.worldMinX = -24576.0f;
    state.worldMaxX = 24576.0f;
    state.worldMinY = -24576.0f;
    state.worldMaxY = 24576.0f;
    const OpenYAMM::Game::GameplayMinimapPoint cropped =
        OpenYAMM::Game::gameplayMinimapUvToOutdoorRevealUv(state, 0.875f, 0.25f);
    // World (18432, 12288) must read native reveal cell (68, 27), not (77, 22).
    CHECK(cropped.x * 88.0f == doctest::Approx(68.75f));
    CHECK(cropped.y * 88.0f == doctest::Approx(27.5f));

    state.flipU = true;
    state.flipV = false;
    const OpenYAMM::Game::GameplayMinimapPoint flipped =
        OpenYAMM::Game::gameplayMinimapUvToOutdoorRevealUv(state, 0.125f, 0.75f);
    CHECK(flipped.x == doctest::Approx(cropped.x));
    CHECK(flipped.y == doctest::Approx(cropped.y));
}

TEST_CASE("promoted MM9 map catalog covers every rebuilt map with runtime decodable 2x images")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path worldRoot = sourceRoot / "assets_dev" / "worlds" / "mm9";
    const std::vector<uint8_t> catalogBytes = readMapAsset(worldRoot / "ui" / "maps" / "catalog.yml");

    REQUIRE_FALSE(catalogBytes.empty());
    const std::string catalog(catalogBytes.begin(), catalogBytes.end());
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::MapPresentation> bootcamp =
        OpenYAMM::Game::loadMapPresentationFromCatalog(catalog, "bootcamp.blv", errorMessage);
    REQUIRE(bootcamp.has_value());
    CHECK(errorMessage.empty());
    // The rebuilt Boot Camp's frame: the old import's bounds moved by the conversion offset (-25646, -1777).
    CHECK(bootcamp->worldMinX == doctest::Approx(-37442.48f));
    CHECK(bootcamp->worldMaxX == doctest::Approx(34647.12f));

    OpenYAMM::Game::GameplayMinimapState bootcampState = {};
    REQUIRE(OpenYAMM::Game::applyMapPresentationToMinimapState(*bootcamp, 0.0f, bootcampState));
    const OpenYAMM::Game::GameplayMinimapPoint ravensfordParty =
        OpenYAMM::Game::gameplayMinimapWorldToUv(bootcampState, 323.0f, -8494.0f);
    CHECK(ravensfordParty.x == doctest::Approx(0.52387f));
    CHECK(ravensfordParty.y == doctest::Approx(0.88933f));
    // The catalog keeps the native size (the zoom); the image is the 2x Real-ESRGAN map.
    CHECK(bootcampState.zoomWidth == doctest::Approx(1000.0f));
    CHECK(bootcampState.textureName == "ui/maps/bootcamp.png");

    // MM9 picks a dungeon's floor image by the party's height (1000 Terrors: three floors).
    const std::optional<OpenYAMM::Game::MapPresentation> terrors =
        OpenYAMM::Game::loadMapPresentationFromCatalog(catalog, "1000terrors.blv", errorMessage);
    REQUIRE(terrors.has_value());
    REQUIRE(terrors->variants.size() == 3);
    CHECK(OpenYAMM::Game::resolveMapPresentationVariant(*terrors, 2000.0f)->textureName
        == "ui/maps/1000terrorsa.png");
    CHECK(OpenYAMM::Game::resolveMapPresentationVariant(*terrors, 0.0f)->textureName
        == "ui/maps/1000terrorsb.png");
    CHECK(OpenYAMM::Game::resolveMapPresentationVariant(*terrors, -2000.0f)->textureName
        == "ui/maps/1000terrorsc.png");
    CHECK_FALSE(OpenYAMM::Game::loadMapPresentationFromCatalog(catalog, "greatgate.odm", errorMessage).has_value());

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));
    OpenYAMM::Engine::DirectoryAssetPathCache directoryCache;
    OpenYAMM::Engine::AssetPathLookupCache pathCache;
    OpenYAMM::Engine::BinaryAssetCache binaryCache;
    size_t mapCount = 0;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(worldRoot / "maps"))
    {
        if (entry.path().extension() != ".blv")
        {
            continue;
        }

        const std::string mapFileName = entry.path().filename().string();
        CAPTURE(mapFileName);
        const std::optional<OpenYAMM::Game::MapPresentation> presentation =
            OpenYAMM::Game::loadMapPresentationFromCatalog(catalog, mapFileName, errorMessage);
        REQUIRE(presentation.has_value());
        ++mapCount;

        for (const OpenYAMM::Game::MapPresentationVariant &variant : presentation->variants)
        {
            CAPTURE(variant.textureName);
            const std::string fileName = variant.textureName.substr(variant.textureName.find_last_of('/') + 1);
            const std::optional<OpenYAMM::Engine::ImagePixelsBgra> image = OpenYAMM::Engine::loadImageAssetPixelsBgra(
                assetFileSystem, "ui/maps", fileName, directoryCache, pathCache, binaryCache);
            REQUIRE(image.has_value());
            CHECK(image->width == variant.pixelWidth * 2);
            CHECK(image->height == variant.pixelHeight * 2);
        }
    }

    CHECK(mapCount == 44);
}
