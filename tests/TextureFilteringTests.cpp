#include "engine/AssetFileSystem.h"
#include "game/content/ContentManifest.h"
#include "game/maps/MapAssetLoader.h"
#include "game/render/BillboardOpacityMask.h"
#include "game/render/TextureFiltering.h"

#include <doctest/doctest.h>

#include <cstdint>
#include <cmath>
#include <filesystem>
#include <future>
#include <memory>
#include <vector>

using namespace OpenYAMM::Game;

TEST_CASE("Model material mipmaps average sRGB in linear space and normalize normals")
{
    using namespace OpenYAMM::Engine;
    const std::vector<uint8_t> colors = {0, 0, 0, 0, 255, 255, 255, 255};
    const std::vector<BgraMipLevel> colorLevels = prepareBgraMipChain(2, 1, colors, 0, ImageMipSemantic::Srgb);
    REQUIRE_EQ(colorLevels.size(), 2);
    CHECK_EQ(colorLevels.back().pixels[0], 188);
    CHECK_EQ(colorLevels.back().pixels[3], 128);
    CHECK(srgbToLinear(linearToSrgb(0.18f)) == doctest::Approx(0.18f));
    const std::vector<uint8_t> normals = {255, 128, 128, 255, 128, 128, 255, 255};
    const std::vector<BgraMipLevel> normalLevels = prepareBgraMipChain(2, 1, normals, 0, ImageMipSemantic::Normal);
    const std::vector<uint8_t> &normal = normalLevels.back().pixels;
    float lengthSquared = 0;
    for (size_t channel = 0; channel < 3; ++channel)
    {
        const float value = normal[channel] / 127.5f - 1;
        lengthSquared += value * value;
    }
    CHECK(std::sqrt(lengthSquared) == doctest::Approx(1.0f).epsilon(0.01));
    const std::vector<uint8_t> odd = {0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255, 255};
    CHECK_EQ(prepareBgraMipChain(3, 1, odd, 0, ImageMipSemantic::Srgb).back().pixels[0], 156);
    CHECK(prepareBgraMipChain(2, 2, colors).empty());
}

namespace
{
OutdoorBitmapTexture textureWithBytes(size_t byteCount)
{
    OutdoorBitmapTexture texture = {};
    texture.textureName = "texture";
    texture.width = 8;
    texture.height = 8;
    texture.pixels.resize(byteCount, 1);
    return texture;
}
}

TEST_CASE("Billboard upload preparation fills transparent edge colors without changing alpha")
{
    std::vector<uint8_t> pixels = {
        20, 40, 60, 255,
        0, 0, 0, 0,
        90, 110, 130, 255,
    };

    const bool prepared = prepareBgraTexturePixelsForUploadInPlace(
        3,
        1,
        pixels,
        TextureFilterProfile::Billboard);

    CHECK(prepared);
    CHECK(pixels[4] == 20);
    CHECK(pixels[5] == 40);
    CHECK(pixels[6] == 60);
    CHECK(pixels[7] == 0);
}

TEST_CASE("Upload preparation leaves profiles without transparent edge bleeding unchanged")
{
    std::vector<uint8_t> pixels = {
        20, 40, 60, 255,
        0, 0, 0, 0,
    };
    const std::vector<uint8_t> originalPixels = pixels;

    const bool prepared = prepareBgraTexturePixelsForUploadInPlace(
        2,
        1,
        pixels,
        TextureFilterProfile::BModel);

    CHECK_FALSE(prepared);
    CHECK(pixels == originalPixels);
}

TEST_CASE("Billboard opacity masks retain alpha hit testing in one bit per pixel")
{
    const std::vector<uint8_t> pixels = {
        20, 40, 60, 255,
        0, 0, 0, 0,
        90, 110, 130, 1,
        0, 0, 0, 0,
        0, 0, 0, 0,
        10, 20, 30, 255,
        0, 0, 0, 0,
        10, 20, 30, 255,
        0, 0, 0, 0,
    };
    BillboardOpacityMask mask;

    mask.assignFromBgra(pixels, 3, 3);

    CHECK_EQ(mask.byteSize(), 2);
    CHECK(mask.isOpaque(0, 0));
    CHECK_FALSE(mask.isOpaque(1, 0));
    CHECK(mask.isOpaque(2, 0));
    CHECK(mask.isOpaque(2, 1));
    CHECK_FALSE(mask.isOpaque(0, 2));
    CHECK(mask.isOpaqueNormalized(0.99f, 0.66f));
    CHECK_FALSE(mask.isOpaque(-1, 0));
    CHECK(mask.opaqueTopNormalized() == doctest::Approx(0.0f));
}

TEST_CASE("Billboard opacity masks expose the visible top for world-space anchors")
{
    std::vector<uint8_t> pixels(2 * 4 * 4, 0);
    pixels[(2 * 2 + 1) * 4 + 3] = 255;
    BillboardOpacityMask mask;

    mask.assignFromBgra(pixels, 2, 4);

    CHECK(mask.opaqueTopNormalized() == doctest::Approx(0.5f));
}

TEST_CASE("Billboard opacity masks find the nearest visible silhouette point")
{
    std::vector<uint8_t> pixels(5 * 5 * 4, 0);
    for (int y = 1; y <= 3; ++y)
    {
        pixels[(y * 5 + 2) * 4 + 3] = 255;
    }
    for (int x = 1; x <= 3; ++x)
    {
        pixels[(2 * 5 + x) * 4 + 3] = 255;
    }
    BillboardOpacityMask mask;
    mask.assignFromBgra(pixels, 5, 5);

    const std::optional<std::array<float, 2>> right = mask.nearestOpaqueNormalized(1.4f, 0.5f);
    const std::optional<std::array<float, 2>> above = mask.nearestOpaqueNormalized(0.5f, -0.5f);
    const std::optional<std::array<float, 2>> below = mask.nearestOpaqueNormalized(0.5f, 1.5f);
    const std::optional<std::array<float, 2>> diagonal = mask.nearestOpaqueNormalized(1.4f, -0.5f);

    REQUIRE(right.has_value());
    CHECK((*right)[0] == doctest::Approx(0.8f));
    CHECK((*right)[1] == doctest::Approx(0.5f));
    REQUIRE(above.has_value());
    CHECK((*above)[0] == doctest::Approx(0.5f));
    CHECK((*above)[1] == doctest::Approx(0.2f));
    REQUIRE(below.has_value());
    CHECK((*below)[0] == doctest::Approx(0.5f));
    CHECK((*below)[1] == doctest::Approx(0.8f));
    REQUIRE(diagonal.has_value());
    CHECK((*diagonal)[0] == doctest::Approx(0.6f));
    CHECK((*diagonal)[1] == doctest::Approx(0.2f));
}

TEST_CASE("Billboard opacity masks reject an entirely transparent silhouette")
{
    const std::vector<uint8_t> pixels(3 * 3 * 4, 0);
    BillboardOpacityMask mask;
    mask.assignFromBgra(pixels, 3, 3);

    CHECK_FALSE(mask.nearestOpaqueNormalized(0.5f, 0.5f).has_value());
}

TEST_CASE("Billboard opacity masks move transparent filler hits to the nearest opaque pixel")
{
    std::vector<uint8_t> pixels(3 * 3 * 4, 255);
    pixels[(1 * 3 + 1) * 4 + 3] = 0;
    BillboardOpacityMask mask;
    mask.assignFromBgra(pixels, 3, 3);

    const std::optional<std::array<float, 2>> nearest = mask.nearestOpaqueNormalized(0.5f, 0.5f);

    REQUIRE(nearest.has_value());
    CHECK((*nearest)[0] == doctest::Approx(0.5f));
    CHECK((*nearest)[1] == doctest::Approx(1.0f / 3.0f));
}

TEST_CASE("Billboard opacity masks read atlas crops with row stride and partial alpha")
{
    std::vector<uint8_t> pixels(7 * 6 * 4, 0);
    pixels[(1 * 7 + 1) * 4 + 3] = 255; // Outside the crop must not affect its top.
    pixels[(3 * 7 + 2) * 4 + 3] = 1;
    pixels[(4 * 7 + 4) * 4 + 3] = 255;
    BillboardOpacityMask mask;
    mask.assignFromBgraRegion(pixels, 7, 6, 2, 2, 3, 3);
    REQUIRE(mask.byteSize() == 2);
    CHECK(mask.opaqueTopNormalized() == doctest::Approx(1.0f / 3));
    for (int y = 0; y < 3; ++y)
    {
        for (int x = 0; x < 3; ++x)
        {
            CHECK(mask.isOpaque(x, y) == (pixels[((y + 2) * 7 + x + 2) * 4 + 3] != 0));
        }
    }
    CHECK(mask.isOpaqueNormalized(1, 1));
    mask.assignFromBgraRegion(pixels, 7, 6, 6, 4, 3, 3);
    CHECK(mask.empty());
    mask.assignFromBgraRegion(pixels, 7, 6, -1, 0, 3, 3);
    CHECK(mask.empty());
    pixels.resize(8);
    mask.assignFromBgraRegion(pixels, 7, 6, 2, 2, 3, 3);
    CHECK(mask.empty());
}

TEST_CASE("Map render source cleanup releases decoded pixels while preserving texture metadata")
{
    MapAssetInfo mapAssetInfo = {};
    mapAssetInfo.outdoorBModelTextureSet.emplace();
    mapAssetInfo.outdoorBModelTextureSet->textures.push_back(textureWithBytes(5));
    mapAssetInfo.outdoorDecorationBillboardSet.emplace();
    mapAssetInfo.outdoorDecorationBillboardSet->textures.push_back(textureWithBytes(7));
    mapAssetInfo.outdoorActorPreviewBillboardSet.emplace();
    mapAssetInfo.outdoorActorPreviewBillboardSet->textures.push_back(textureWithBytes(11));
    mapAssetInfo.outdoorSpriteObjectBillboardSet.emplace();
    mapAssetInfo.outdoorSpriteObjectBillboardSet->textures.push_back(textureWithBytes(13));
    mapAssetInfo.indoorDecorationBillboardSet.emplace();
    mapAssetInfo.indoorDecorationBillboardSet->textures.push_back(textureWithBytes(17));
    mapAssetInfo.indoorActorPreviewBillboardSet.emplace();
    mapAssetInfo.indoorActorPreviewBillboardSet->textures.push_back(textureWithBytes(19));
    mapAssetInfo.indoorSpriteObjectBillboardSet.emplace();
    mapAssetInfo.indoorSpriteObjectBillboardSet->textures.push_back(textureWithBytes(23));
    mapAssetInfo.indoorTextureSet.emplace();
    mapAssetInfo.indoorTextureSet->textures.push_back(textureWithBytes(29));

    CHECK_EQ(mapRenderSourcePixelBytes(mapAssetInfo), 124);

    clearMapRenderSourcePixels(mapAssetInfo);

    CHECK_EQ(mapRenderSourcePixelBytes(mapAssetInfo), 0);
    REQUIRE(mapAssetInfo.outdoorBModelTextureSet);
    REQUIRE_EQ(mapAssetInfo.outdoorBModelTextureSet->textures.size(), 1);
    CHECK_EQ(mapAssetInfo.outdoorBModelTextureSet->textures[0].textureName, "texture");
}

TEST_CASE("Cutout mip coverage keeps sparse grass visible without coloring transparent borders")
{
    const std::vector<uint8_t> reference = {
        30, 90, 60, 255, 30, 90, 60, 255, 30, 90, 60, 0, 30, 90, 60, 0};
    std::vector<uint8_t> reduced = {
        30, 90, 60, 80, 30, 90, 60, 70, 30, 90, 60, 20, 30, 90, 60, 0};
    const std::vector<uint8_t> before = reduced;
    preserveBgraCutoutCoverage(reduced, reference, 102);
    int covered = 0;
    for (size_t i = 0; i < reduced.size(); ++i)
    {
        if (i % 4 == 3)
        {
            covered += reduced[i] >= 102 ? 1 : 0;
        }
        else
        {
            CHECK(reduced[i] == before[i]);
        }
    }
    CHECK(covered == 2);
    CHECK(reduced[15] == 0);
    const std::vector<uint8_t> corrected = reduced;
    preserveBgraCutoutCoverage(reduced, reference, 102);
    CHECK(reduced == corrected);
    reduced = before;
    preserveBgraCutoutCoverage(reduced, reference, 0);
    CHECK(reduced == before);
    const std::vector<uint8_t> emptyReference = {30, 90, 60, 0};
    preserveBgraCutoutCoverage(reduced, emptyReference, 102);
    for (size_t i = 3; i < reduced.size(); i += 4)
    {
        CHECK(reduced[i] < 102);
    }
}

TEST_CASE("Cached animation mip chains preserve frame pixels and deterministic downsampling")
{
    const std::vector<uint8_t> firstFrame = {
        0, 20, 40, 255, 20, 40, 60, 255,
        40, 60, 80, 255, 60, 80, 100, 255,
    };
    const std::vector<uint8_t> secondFrame(16, 120);
    const std::vector<BgraMipLevel> first = prepareBgraMipChain(2, 2, firstFrame);
    const std::vector<BgraMipLevel> second = prepareBgraMipChain(2, 2, secondFrame);
    REQUIRE(first.size() == 2);
    REQUIRE(second.size() == 2);
    CHECK(first[0].pixels == firstFrame);
    CHECK(second[0].pixels == secondFrame);
    CHECK(first[1].width == 1);
    CHECK(first[1].height == 1);
    CHECK(first[1].pixels == std::vector<uint8_t>{30, 50, 70, 255});
    CHECK(second[1].pixels == std::vector<uint8_t>{120, 120, 120, 120});
    CHECK(prepareBgraMipChain(2, 2, firstFrame)[1].pixels == first[1].pixels);
    CHECK(prepareBgraMipChain(0, 2, firstFrame).empty());
    CHECK(prepareBgraMipChain(8, 8, firstFrame).empty());
}

TEST_CASE("Cached animation mip chains retain rectangular dimensions and cutout coverage")
{
    std::vector<uint8_t> pixels(8 * 2 * 4, 255);
    for (size_t pixel = 0; pixel < 16; ++pixel)
    {
        pixels[pixel * 4 + 3] = pixel % 3 == 0 ? 0 : 255;
    }
    const std::vector<BgraMipLevel> raw = prepareBgraMipChain(8, 2, pixels);
    const std::vector<BgraMipLevel> cutout = prepareBgraMipChain(8, 2, pixels, 160);
    REQUIRE(raw.size() == 4);
    REQUIRE(cutout.size() == raw.size());
    CHECK(raw[1].width == 4);
    CHECK(raw[1].height == 1);
    CHECK(raw[2].width == 2);
    CHECK(raw[3].width == 1);
    CHECK(cutout[0].pixels == pixels);
    for (size_t level = 1; level < raw.size(); ++level)
    {
        std::vector<uint8_t> expected = raw[level].pixels;
        preserveBgraCutoutCoverage(expected, pixels, 160);
        CHECK(cutout[level].pixels == expected);
    }
}

TEST_CASE("map bitmap residency retains recently used images within its byte budget")
{
    using namespace OpenYAMM::Game;
    MapAssetLoadSharedCache cache;
    cache.beginLoad(1);
    cache.bitmapPixelsByKey["old"] = MapAssetBitmapPixelsResult{1, 1, {1, 2, 3, 4}};
    cache.touchBitmap("old");
    cache.bitmapPixelsByKey["new"] = MapAssetBitmapPixelsResult{1, 1, {5, 6, 7, 8}};
    cache.touchBitmap("new");
    cache.bitmapBinaryFilesByPath["source"] = std::vector<uint8_t>{1, 2};
    cache.trimBitmapData(4);
    CHECK_FALSE(cache.bitmapPixelsByKey.contains("old"));
    CHECK(cache.bitmapPixelsByKey.contains("new"));
    CHECK(cache.bitmapBinaryFilesByPath.empty());
    CHECK(cache.retainedBitmapBytes() == 4);
    cache.beginLoad(1);
    CHECK(cache.retainedBitmapBytes() == 4);
    cache.beginLoad(2);
    CHECK(cache.bitmapPixelsByKey.empty());
    CHECK(cache.bitmapLastUse.empty());
}

TEST_CASE("D-55: a world whose glow is content loads the normal maps of its glowing textures alone, others nothing")
{
    CHECK(parseSurfaceGlowList("# generated\nXaEnergy\n  xafield \r\n\n") == std::vector<std::string>{
        "xaenergy", "xafield"});

    WorldManifest mm7;
    mm7.id = "mm7";
    WorldManifest xeen;
    xeen.id = "xeen";
    xeen.surfaceGlowContent = true;
    const std::vector<WorldManifest> worlds = {mm7, xeen};
    // Only a declaring world's maps with Surface materials off read the lists, and they read every mounted world's
    // (a texture borrowed from MM7 finds MM7's).
    CHECK(surfaceGlowListWorlds(worlds, "xeen", false) == std::vector<std::string>{"mm7", "xeen"});
    CHECK(surfaceGlowListWorlds(worlds, "XEEN", false) == std::vector<std::string>{"mm7", "xeen"});
    CHECK(surfaceGlowListWorlds(worlds, "xeen", true).empty());
    CHECK(surfaceGlowListWorlds(worlds, "mm7", false).empty());

    // MM7's hkm3elw glows (its glow list, tools/surface_materials.py); 7solid01 has maps but no glow.
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    OpenYAMM::Engine::AssetScaleProfile profile;
    profile.textures = OpenYAMM::Engine::AssetScaleTier::X4;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1,
        profile, "mm7"));
    MapCompanionLoadOptions glowOnly;
    glowOnly.surfaceGlowWorlds = {"mm7"};
    const std::optional<OutdoorBitmapTexture> glowing = loadSurfaceTexture(assetFileSystem, "hkm3elw", glowOnly);
    REQUIRE(glowing.has_value());
    REQUIRE(glowing->cookedTexture != nullptr);
    CHECK(glowing->materialNormal != nullptr);
    CHECK(glowing->materialDetail == nullptr);
    const std::optional<OutdoorBitmapTexture> plain = loadSurfaceTexture(assetFileSystem, "7solid01", glowOnly);
    REQUIRE(plain.has_value());
    CHECK(plain->materialNormal == nullptr);
    CHECK(plain->materialDetail == nullptr);

    // A world without the field (no glow worlds, the setting off): nothing.
    const std::optional<OutdoorBitmapTexture> off = loadSurfaceTexture(assetFileSystem, "hkm3elw", {});
    REQUIRE(off.has_value());
    CHECK(off->materialNormal == nullptr);
    CHECK(off->materialDetail == nullptr);

    // The setting on: both maps, as before.
    MapCompanionLoadOptions materials;
    materials.surfaceMaterials = true;
    const std::optional<OutdoorBitmapTexture> full = loadSurfaceTexture(assetFileSystem, "hkm3elw", materials);
    REQUIRE(full.has_value());
    CHECK(full->materialNormal != nullptr);
    CHECK(full->materialDetail != nullptr);
}
