#include "doctest/doctest.h"
#include "game/maps/MapDecorationTextures.h"

#include <chrono>
#include <filesystem>
#include <fstream>

namespace
{
const std::string Manifest = R"(schema_version: 1
textures:
  - {name: tree, file: tree.png, palette_id: 140, logical_size: [1, 1], pixel_scale: 2}
)";

// RGBA 2x2: opaque magenta, half-alpha color, transparent black, opaque color.
const uint8_t Png2x2[] = {
    137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, 0, 0, 0, 2, 0, 0, 0, 2,
    8, 6, 0, 0, 0, 114, 182, 13, 36, 0, 0, 0, 26, 73, 68, 65, 84, 120, 156, 99, 248, 207, 240,
    255, 63, 151, 136, 92, 3, 11, 35, 3, 35, 163, 134, 156, 205, 127, 0, 56, 72, 5, 66, 134,
    107, 38, 117, 0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130};

struct DecorationTextureFixture
{
    std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("openyamm_decoration_" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));

    ~DecorationTextureFixture()
    {
        std::filesystem::remove_all(root);
    }
};
}

TEST_CASE("map decoration textures reject ambiguous keys and invalid placement metadata")
{
    using OpenYAMM::Game::parseMapDecorationTextures;
    std::string error;
    const auto parsed = parseMapDecorationTextures(Manifest, error);
    REQUIRE_MESSAGE(parsed, error);
    REQUIRE(parsed->size() == 1);
    CHECK(parsed->front().width == 1);
    CHECK(parsed->front().pixelScale == 2);
    CHECK_FALSE(parseMapDecorationTextures(Manifest + Manifest.substr(Manifest.find("  -")), error));
    for (const std::pair<std::string, std::string> &change : {
        std::pair{"tree.png", "../tree.png"}, std::pair{"pixel_scale: 2", "pixel_scale: 0"},
        std::pair{"[1, 1]", "[0, 1]"}, std::pair{"[1, 1]", "[99999999, 1]"},
        std::pair{"schema_version: 1", "schema_version: 2"}})
    {
        std::string invalid = Manifest;
        invalid.replace(invalid.find(change.first), change.first.size(), change.second);
        CHECK_FALSE(parseMapDecorationTextures(invalid, error));
        CHECK_FALSE(error.empty());
    }
}

TEST_CASE("map decoration textures preserve RGBA and native size only in their exact world and map")
{
    using namespace OpenYAMM;
    DecorationTextureFixture fixture;
    const std::filesystem::path assetsRoot = fixture.root / "assets_dev";
    const std::filesystem::path directory =
        assetsRoot / "worlds/mm6/rendering/decoration_overrides/oute3.odm";
    std::filesystem::create_directories(directory);
    std::filesystem::create_directories(assetsRoot / "engine");
    std::ofstream(directory / "manifest.yml") << Manifest;
    std::ofstream(directory / "tree.png", std::ios::binary).write(
        reinterpret_cast<const char *>(Png2x2), sizeof(Png2x2));
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(fixture.root, assetsRoot, Engine::AssetScaleTier::X1, "mm6"));
    std::string error;
    const auto textures = Game::loadMapDecorationTextures(assets, "mm6", "oute3.odm", error);
    REQUIRE_MESSAGE(textures, error);
    REQUIRE(textures->size() == 1);
    CHECK_FALSE(textures->front().resourceIdentity.empty());
    const Game::OutdoorBitmapTexture &texture = textures->front();
    CHECK(texture.width == 1);
    CHECK(texture.height == 1);
    CHECK(texture.physicalWidth == 2);
    CHECK(texture.physicalHeight == 2);
    CHECK(texture.paletteId == 140);
    CHECK(texture.hasTransparentPixels);
    CHECK(texture.hasPartialAlphaPixels);
    CHECK(texture.pixels == std::vector<uint8_t>{255, 0, 255, 255, 30, 20, 10, 128, 0, 0, 0, 0, 60, 50, 40, 255});
    for (const std::pair<std::string, std::string> &scope : {
        std::pair{"mm6", "outd3.odm"}, std::pair{"mm8", "oute3.odm"}, std::pair{"mm6", "oute3.blv"}})
    {
        const auto native = Game::loadMapDecorationTextures(assets, scope.first, scope.second, error);
        REQUIRE_MESSAGE(native, error);
        CHECK(native->empty());
    }
    std::string invalid = Manifest;
    invalid.replace(invalid.find("[1, 1]"), 6, "[2, 1]");
    std::ofstream(directory / "manifest.yml") << invalid;
    CHECK_FALSE(Game::loadMapDecorationTextures(assets, "mm6", "oute3.odm", error));
    CHECK_FALSE(error.empty());
    std::ofstream(directory / "manifest.yml") << Manifest;
    std::filesystem::remove(directory / "tree.png");
    CHECK_FALSE(Game::loadMapDecorationTextures(assets, "mm6", "oute3.odm", error));
}
