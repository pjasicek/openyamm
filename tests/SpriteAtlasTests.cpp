#include "doctest/doctest.h"

#include "engine/SpriteAtlas.h"
#include "game/render/SpriteAtlasMipmaps.h"
#include "engine/ImageAssetLoader.h"
#include "game/render/SpriteAtlasCache.h"

#include <fstream>
#include <sstream>

namespace
{
const std::string Fixture = R"(
schema_version: 1
recolor_model: green_chroma_srgb_v1
pixels_per_logical_pixel: 2
logical_canvas: [256, 256]
logical_pivot: [128, 128]
pages:
  - {base: atlas/base_0.png, mask: atlas/mask_0.png, size: [512, 512]}
frames:
  pose0: {page: 0, atlas_xywh: [4, 4, 100, 200], crop_origin_px: [-20, 40]}
variants:
  54: {exact_base_bypass: true}
  55: {chroma_vector: [0.2, 0.18, 1]}
)";
}

TEST_CASE("sprite atlas parses explicit references and rejects path traversal")
{
    using OpenYAMM::Engine::parseSpriteAtlasReference;
    CHECK_FALSE(parseSpriteAtlasReference("m230sa0"));
    CHECK_FALSE(parseSpriteAtlasReference("atlas:../crusader/pose0"));
    CHECK_FALSE(parseSpriteAtlasReference("atlas:crusader/../pose0"));
    const auto reference = parseSpriteAtlasReference("atlas:crusader/m230sa0");
    REQUIRE(reference);
    CHECK(reference->package == "crusader");
    CHECK(reference->frame == "m230sa0");
}

TEST_CASE("sprite atlas validates manifest and preserves crop origins and variant bypass")
{
    std::string error;
    const auto atlas = OpenYAMM::Engine::SpriteAtlas::parse(Fixture, error);
    REQUIRE_MESSAGE(atlas, error);
    CHECK(atlas->frames.at("pose0").cropOrigin[0] == -20);
    CHECK(atlas->variants.at(54).chroma[3] == 0);
    CHECK(atlas->variants.at(55).chroma[3] == 1);
    CHECK(atlas->variants.at(55).chroma[2] == 1);

    for (const std::pair<std::string, std::string> &replacement : {
        std::pair{"schema_version: 1", "schema_version: 2"},
        std::pair{"[4, 4, 100, 200]", "[500, 4, 100, 200]"},
        std::pair{"pixels_per_logical_pixel: 2", "pixels_per_logical_pixel: 0"},
        std::pair{"atlas/base_0.png", "atlas/../base_0.png"},
        std::pair{"green_chroma_srgb_v1", "unknown"}})
    {
        std::string malformed = Fixture;
        malformed.replace(malformed.find(replacement.first), replacement.first.size(), replacement.second);
        CHECK_FALSE(OpenYAMM::Engine::SpriteAtlas::parse(malformed, error));
        CHECK_FALSE(error.empty());
    }
}

TEST_CASE("sprite atlas cropped billboard maintains native pivot when mirrored and camera tilted")
{
    using namespace OpenYAMM::Game;
    const bx::Vec3 right = {1, 0, 0};
    const bx::Vec3 up = {0, -0.6f, 0.8f};
    SpriteBillboardTexture texture;
    texture.width = 50;
    texture.height = 100;
    // Fixture's crop: [-20,40] with extent [100,200] at 2x.
    texture.offsetX = -113;
    texture.offsetY = 136;
    const bx::Vec3 normal = spriteBillboardCenter(10, 20, 30, right, up, texture, 0.9f, false);
    const bx::Vec3 mirror = spriteBillboardCenter(10, 20, 30, right, up, texture, 0.9f, true);
    CHECK((normal.x + mirror.x) * 0.5f == doctest::Approx(10));
    CHECK(normal.z == doctest::Approx(30 + 186 * 0.9f * 0.8f));
    CHECK(normal.y == doctest::Approx(20 - 186 * 0.9f * 0.6f));
    CHECK(normal.y == mirror.y);
    CHECK(normal.z == mirror.z);
}

TEST_CASE("sprite atlas custom crusader package covers every native pose without variant page duplication")
{
    std::ifstream input(std::string(OPENYAMM_SOURCE_DIR) + "/assets_dev/engine/sprites_new/crusader/manifest.json");
    REQUIRE(input.good());
    std::stringstream text;
    text << input.rdbuf();
    std::string error;
    const auto atlas = OpenYAMM::Engine::SpriteAtlas::parse(text.str(), error);
    REQUIRE_MESSAGE(atlas, error);
    CHECK(atlas->frames.size() == 114);
    CHECK(atlas->pages.size() == 4);
    CHECK(atlas->variants.size() == 3);
    CHECK(atlas->logicalCanvas == std::array<int, 2>{256, 256});
    CHECK(atlas->pixelsPerLogicalPixel == 2);
}

TEST_CASE("sprite atlas grayscale mask decode retains coverage in BGRA red")
{
    // Three grayscale PNG samples: zero, partial, and complete recolor coverage.
    const std::vector<uint8_t> png = {
        137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82,
        0, 0, 0, 3, 0, 0, 0, 1, 8, 0, 0, 0, 0, 62, 139, 75, 104,
        0, 0, 0, 12, 73, 68, 65, 84, 120, 156, 99, 96, 168, 255, 15,
        0, 2, 1, 1, 127, 181, 230, 183, 205, 0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130};
    const auto decoded = OpenYAMM::Engine::decodeImagePixelsBgra(png, "mask.png");
    REQUIRE(decoded);
    REQUIRE(decoded->pixels.size() == 12);
    CHECK(decoded->pixels[2] == 0);
    CHECK(decoded->pixels[6] == 127);
    CHECK(decoded->pixels[10] == 255);
}

TEST_CASE("sprite atlas luminance variants require their own ramp and keep exact base bypass")
{
    std::string fixture = Fixture;
    fixture.replace(fixture.find("green_chroma_srgb_v1"), std::string("green_chroma_srgb_v1").size(),
        "masked_luminance_rgb_v1");
    std::string error;
    CHECK_FALSE(OpenYAMM::Engine::SpriteAtlas::parse(fixture, error));
    fixture.replace(fixture.find("chroma_vector"), std::string("chroma_vector").size(), "luminance_vector");
    const auto atlas = OpenYAMM::Engine::SpriteAtlas::parse(fixture, error);
    REQUIRE_MESSAGE(atlas, error);
    CHECK(atlas->variants.at(54).chroma[3] == 0);
    CHECK(atlas->variants.at(55).chroma[3] == 2);
    CHECK(atlas->variants.at(55).chroma[0] == doctest::Approx(0.2f));
}

TEST_CASE("sprite atlas palette lookups validate dimensions and retain exact base bypass")
{
    const std::array<std::string, 3> models = {
        "masked_luminance_lut_v1", "multi_mask_luminance_lut_v1", "masked_native_rgb_displacement_lut_v1"};
    const std::array<std::string, 3> sizes = {"[256, 1]", "[256, 4]", "[1089, 33]"};
    for (size_t i = 0; i < models.size(); ++i)
    {
        std::string fixture = Fixture;
        fixture.replace(fixture.find("green_chroma_srgb_v1"), std::string("green_chroma_srgb_v1").size(), models[i]);
        const std::string old = "chroma_vector: [0.2, 0.18, 1]";
        fixture.replace(fixture.find(old), old.size(),
            "lookup: atlas/palette_55.rgba32f, lookup_size: " + sizes[i]);
        std::string error;
        const auto atlas = OpenYAMM::Engine::SpriteAtlas::parse(fixture, error);
        REQUIRE_MESSAGE(atlas, error);
        CHECK(atlas->maskChannels == (i == 1 ? 4 : 1));
        CHECK(atlas->variants.at(54).lookup.empty());
        CHECK(atlas->variants.at(54).chroma[3] == 0);
        CHECK(atlas->variants.at(55).chroma[3] == float(5 + i));
        CHECK(atlas->variants.at(55).lookup == "atlas/palette_55.rgba32f");
        for (const std::pair<std::string, std::string> &replacement : {
            std::pair{sizes[i], std::string("[256, 2]")},
            std::pair{std::string("atlas/palette_55.rgba32f"), std::string("atlas/../palette_55.rgba32f")}})
        {
            std::string invalid = fixture;
            invalid.replace(invalid.find(replacement.first), replacement.first.size(), replacement.second);
            CHECK_FALSE(OpenYAMM::Engine::SpriteAtlas::parse(invalid, error));
        }
    }
}

TEST_CASE("sprite atlas mage package preserves variable crops and three shared palette variants")
{
    std::ifstream input(std::string(OPENYAMM_SOURCE_DIR) + "/assets_dev/engine/sprites_new/pmn2/manifest.json");
    REQUIRE(input.good());
    std::stringstream text;
    text << input.rdbuf();
    std::string error;
    const auto atlas = OpenYAMM::Engine::SpriteAtlas::parse(text.str(), error);
    REQUIRE_MESSAGE(atlas, error);
    CHECK(atlas->frames.size() == 59);
    CHECK(atlas->pages.size() == 3);
    CHECK(atlas->logicalCanvas == std::array<int, 2>{331, 272});
    CHECK(atlas->logicalPivot == std::array<float, 2>{165.5f, 272});
    CHECK(atlas->variants.at(801).chroma[3] == 2);
    CHECK(atlas->variants.at(802).chroma[3] == 0);
    CHECK(atlas->variants.at(803).chroma[3] == 2);
}

TEST_CASE("sprite atlas two-region recoloring retains separate ramps and rejects incomplete variants")
{
    std::string fixture = Fixture;
    fixture.replace(fixture.find("green_chroma_srgb_v1"), std::string("green_chroma_srgb_v1").size(),
        "masked_regions_luminance_rgb_v1");
    const std::string originalRamp = "chroma_vector: [0.2, 0.18, 1]";
    const std::string regionRamps = "region_luminance_vectors: [[0.2, 0.18, 1], [1.4, 0.8, 0.5]]";
    std::string error;
    CHECK_FALSE(OpenYAMM::Engine::SpriteAtlas::parse(fixture, error));
    fixture.replace(fixture.find(originalRamp), originalRamp.size(), regionRamps);
    const auto atlas = OpenYAMM::Engine::SpriteAtlas::parse(fixture, error);
    REQUIRE_MESSAGE(atlas, error);
    CHECK(atlas->maskChannels == 2);
    CHECK(atlas->variants.at(54).chroma[3] == 0);
    CHECK(atlas->variants.at(54).secondChroma == std::array<float, 4>{});
    CHECK(atlas->variants.at(55).chroma[3] == 3);
    CHECK(atlas->variants.at(55).chroma[0] == doctest::Approx(0.2f));
    CHECK(atlas->variants.at(55).secondChroma[0] == doctest::Approx(1.4f));
    CHECK(atlas->variants.at(55).secondChroma[2] == doctest::Approx(0.5f));
    for (const std::string &invalid : {
        "[[0.2, 0.18, 1]]", "[[0.2, 0.18, 1], [1, 1, 1], [1, 1, 1]]",
        "[[0.2, 0.18, 1], [1, 1]]", "[[0.2, 0.18, 1], [-1, 1, 1]]",
        "[[0.2, 0.18, 1], [5, 1, 1]]", "[[0.2, 0.18, 1], [.nan, 1, 1]]"})
    {
        std::string malformed = fixture;
        malformed.replace(malformed.find(regionRamps), regionRamps.size(), "region_luminance_vectors: " + invalid);
        CHECK_FALSE(OpenYAMM::Engine::SpriteAtlas::parse(malformed, error));
    }
    const auto nativeModel = OpenYAMM::Engine::SpriteAtlas::parse(Fixture, error);
    REQUIRE(nativeModel);
    CHECK(nativeModel->maskChannels == 1);
}

TEST_CASE("sprite atlas RGB masks decode red and green independently of opacity")
{
    // Pure first region, pure second region, then partial coverage of both. PNG alpha is not a mask.
    const std::vector<uint8_t> png = {
        137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82,
        0, 0, 0, 3, 0, 0, 0, 1, 8, 2, 0, 0, 0, 148, 130, 131, 227,
        0, 0, 0, 18, 73, 68, 65, 84, 120, 156, 99, 248, 207, 192, 192,
        240, 159, 193, 161, 129, 1, 0, 15, 188, 2, 191, 13, 89, 106, 94,
        0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130};
    const auto decoded = OpenYAMM::Engine::decodeImagePixelsBgra(png, "mask.png");
    REQUIRE(decoded);
    CHECK(decoded->pixels == std::vector<uint8_t>{0, 0, 255, 255, 0, 255, 0, 255, 0, 128, 64, 255});
}

TEST_CASE("sprite atlas guard package supports four material ramps on shared pages")
{
    std::ifstream input(std::string(OPENYAMM_SOURCE_DIR)
        + "/level_generation/creatures/mm6_gua/manifest.json");
    REQUIRE(input.good());
    std::stringstream text;
    text << input.rdbuf();
    std::string error;
    const auto atlas = OpenYAMM::Engine::SpriteAtlas::parse(text.str(), error);
    REQUIRE_MESSAGE(atlas, error);
    CHECK(atlas->maskChannels == 4);
    CHECK(atlas->frames.size() == 59);
    CHECK(atlas->pages.size() == 4);
    CHECK(atlas->variants.size() == 3);
    CHECK(atlas->logicalCanvas == std::array<int, 2>{350, 296});
    CHECK(atlas->logicalPivot == std::array<float, 2>{175, 296});
    CHECK(atlas->variants.at(748).chroma[3] == 0);
    CHECK(atlas->variants.at(749).chroma[3] == 4);
    CHECK(atlas->variants.at(750).chroma[3] == 4);
    CHECK(atlas->variants.at(749).thirdChroma[0] > 0);
    CHECK(atlas->variants.at(750).fourthChroma[0] > 0);
}

TEST_CASE("sprite atlas four-region model requires four valid independent ramps")
{
    std::string fixture = Fixture;
    fixture.replace(fixture.find("green_chroma_srgb_v1"), std::string("green_chroma_srgb_v1").size(),
        "multi_mask_luminance_rgb_v1");
    const std::string originalRamp = "chroma_vector: [0.2, 0.18, 1]";
    const std::string ramps = "[[0.2, 0.18, 1], [1.4, 0.8, 0.5], [1.1, 1.2, 1.3], [2.1, 2.2, 2.3]]";
    fixture.replace(fixture.find(originalRamp), originalRamp.size(), "region_luminance_vectors: " + ramps);
    std::string error;
    const auto atlas = OpenYAMM::Engine::SpriteAtlas::parse(fixture, error);
    REQUIRE_MESSAGE(atlas, error);
    CHECK(atlas->maskChannels == 4);
    CHECK(atlas->variants.at(54).chroma[3] == 0);
    CHECK(atlas->variants.at(55).chroma[3] == 4);
    CHECK(atlas->variants.at(55).secondChroma[0] == doctest::Approx(1.4f));
    CHECK(atlas->variants.at(55).thirdChroma[1] == doctest::Approx(1.2f));
    CHECK(atlas->variants.at(55).fourthChroma[2] == doctest::Approx(2.3f));
    for (const std::string &invalid : {
        "[[1, 1, 1], [1, 1, 1]]", "[[1, 1, 1], [1, 1, 1], [1, 1, 1]]",
        "[[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]]",
        "[[1, 1, 1], [1, 1, 1], [1, 1], [1, 1, 1]]",
        "[[1, 1, 1], [1, 1, 1], [1, 1, 1], [-1, 1, 1]]",
        "[[1, 1, 1], [1, 1, 1], [1, 1, 1], [5, 1, 1]]",
        "[[1, 1, 1], [1, 1, 1], [.nan, 1, 1], [1, 1, 1]]"})
    {
        std::string malformed = fixture;
        malformed.replace(malformed.find(ramps), ramps.size(), invalid);
        CHECK_FALSE(OpenYAMM::Engine::SpriteAtlas::parse(malformed, error));
    }
}

TEST_CASE("sprite atlas RGBA mask decode keeps all weights including RGB at zero alpha")
{
    const std::vector<uint8_t> png = {
        137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82,
        0, 0, 0, 3, 0, 0, 0, 1, 8, 6, 0, 0, 0, 27, 224, 20,
        180, 0, 0, 0, 21, 73, 68, 65, 84, 120, 156, 99, 248, 207, 192, 192,
        192, 192, 192, 240, 95, 68, 195, 38, 0, 0, 18, 140, 2, 199, 191, 126,
        11, 73, 0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130};
    const auto decoded = OpenYAMM::Engine::decodeImagePixelsBgra(png, "mask.png");
    REQUIRE(decoded);
    CHECK(decoded->pixels == std::vector<uint8_t>{0, 0, 255, 0, 0, 0, 0, 255, 60, 40, 20, 80});
}

TEST_CASE("sprite atlas mipmaps isolate odd-sized neighboring frames and preserve source placement")
{
    using namespace OpenYAMM::Game;
    OpenYAMM::Engine::SpriteAtlas atlas;
    atlas.maskChannels = 4;
    atlas.pages.push_back({"", "", {64, 32}});
    atlas.frames["red"] = {0, {1, 2, 19, 21}, {-5, 12}};
    atlas.frames["alias"] = atlas.frames.at("red");
    atlas.frames["blue"] = {0, {22, 3, 23, 17}, {15, 16}};
    std::vector<uint8_t> base(64 * 32 * 4);
    std::vector<uint8_t> mask(base.size());
    for (const auto &[name, frame] : atlas.frames)
    {
        const auto &r = frame.rectangle;
        for (int y = r[1]; y < r[1] + r[3]; ++y)
        {
            for (int x = r[0]; x < r[0] + r[2]; ++x)
            {
                const size_t pixel = size_t(y) * 64 + x;
                base[pixel * 4 + (name == "blue" ? 0 : 2)] = 255;
                base[pixel * 4 + 3] = 255;
                mask[pixel * 4 + (name == "blue" ? 3 : 2)] = 255;
            }
        }
    }
    const SpriteAtlasMipPage page = buildSpriteAtlasMipPage(atlas, 0, base, mask, 2048);
    REQUIRE(page.levels.size() == SpriteAtlasMaxMip + 1);
    CHECK(page.rectangles.at("red") == page.rectangles.at("alias"));
    CHECK(atlas.frames.at("red").cropOrigin == std::array<int, 2>{-5, 12});
    const auto &rect = page.rectangles.at("red");
    CHECK(rect[2] == 19);
    CHECK(rect[3] == 21);
    CHECK(rect[0] % 16 == 0);
    CHECK(rect[1] % 16 == 0);
    for (int mip = 0; mip <= SpriteAtlasMaxMip; ++mip)
    {
        const SpriteAtlasMipLevel &level = page.levels[mip];
        // Include the bilinear footprint on either side of the frame's normalized UV edges.
        for (int y = (rect[1] >> mip) - 1; y <= (rect[1] + rect[3]) >> mip; ++y)
        {
            for (int x = (rect[0] >> mip) - 1; x <= (rect[0] + rect[2]) >> mip; ++x)
            {
                const size_t pixel = size_t(y) * level.width + x;
                CHECK(level.baseBgra[pixel * 4] == 0);
                CHECK(level.baseBgra[pixel * 4 + 2] == 255);
                CHECK(level.baseBgra[pixel * 4 + 3] == 255);
                CHECK(level.mask[pixel * 4] == 255);
                CHECK(level.mask[pixel * 4 + 3] == 0);
            }
        }
    }
    CHECK_THROWS(buildSpriteAtlasMipPage(atlas, 0, base, mask, 32));
    base.pop_back();
    CHECK_THROWS(buildSpriteAtlasMipPage(atlas, 0, base, mask, 2048));
}

TEST_CASE("sprite atlas mipmaps weight color and all material channels by sprite opacity")
{
    using namespace OpenYAMM::Game;
    for (int channels : {1, 2, 4})
    {
        OpenYAMM::Engine::SpriteAtlas atlas;
        atlas.maskChannels = channels;
        atlas.pages.push_back({"", "", {2, 2}});
        atlas.frames["pose"] = {0, {0, 0, 2, 2}, {0, 0}};
        // Opaque red, then three fully transparent green texels. Mask alpha is material data.
        const std::vector<uint8_t> base = {0, 0, 200, 255, 0, 250, 0, 0, 0, 250, 0, 0, 0, 250, 0, 0};
        const std::vector<uint8_t> mask = {60, 40, 20, 80, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255};
        const SpriteAtlasMipPage page = buildSpriteAtlasMipPage(atlas, 0, base, mask, 2048);
        const auto &rect = page.rectangles.at("pose");
        const auto &full = page.levels[0];
        for (int y = 0; y < 2; ++y)
        {
            for (int x = 0; x < 2; ++x)
            {
                const size_t pixel = size_t(rect[1] + y) * full.width + rect[0] + x;
                for (int c = 0; c < 4; ++c)
                {
                    CHECK(full.baseBgra[pixel * 4 + c] == base[(y * 2 + x) * 4 + c]);
                }
            }
        }
        const auto &mip = page.levels[1];
        const size_t pixel = size_t(rect[1] / 2) * mip.width + rect[0] / 2;
        CHECK(mip.baseBgra[pixel * 4] == 0);
        CHECK(mip.baseBgra[pixel * 4 + 1] == 0);
        CHECK(mip.baseBgra[pixel * 4 + 2] == 200);
        CHECK(mip.baseBgra[pixel * 4 + 3] == 64);
        const std::array<int, 4> expected = {20, 40, 60, 80};
        for (int c = 0; c < channels; ++c)
        {
            CHECK(mip.mask[pixel * channels + c] == expected[c]);
        }
        // Adjacent transparent mip texels receive color/masks, but remain transparent.
        CHECK(mip.baseBgra[(pixel + 1) * 4 + 2] == 200);
        CHECK(mip.baseBgra[(pixel + 1) * 4 + 3] == 0);
        CHECK(mip.mask[(pixel + 1) * channels] == 20);
    }
}
