#include "game/maps/MapAssetLoader.h"
#include "game/render/BillboardOpacityMask.h"
#include "game/render/TextureFiltering.h"

#include <doctest/doctest.h>

#include <cstdint>
#include <future>
#include <memory>
#include <vector>

using namespace OpenYAMM::Game;

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
    mapAssetInfo.outdoorTerrainTextureAtlas.emplace();
    mapAssetInfo.outdoorTerrainTextureAtlas->pixels.resize(3, 1);
    mapAssetInfo.outdoorTerrainTextureAtlas->animatedWaterTiles.push_back({});
    mapAssetInfo.outdoorTerrainTextureAtlas->animatedWaterTiles[0].framePixels = {
        std::vector<uint8_t>(2, 1),
        std::vector<uint8_t>(4, 1),
    };
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

    CHECK_EQ(mapRenderSourcePixelBytes(mapAssetInfo), 133);

    clearMapRenderSourcePixels(mapAssetInfo);

    CHECK_EQ(mapRenderSourcePixelBytes(mapAssetInfo), 0);
    REQUIRE(mapAssetInfo.outdoorBModelTextureSet);
    REQUIRE_EQ(mapAssetInfo.outdoorBModelTextureSet->textures.size(), 1);
    CHECK_EQ(mapAssetInfo.outdoorBModelTextureSet->textures[0].textureName, "texture");
    CHECK(mapAssetInfo.outdoorTerrainTextureAtlas->animatedWaterTiles[0].framePixels.empty());
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
