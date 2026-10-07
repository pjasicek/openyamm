#include "engine/ImageAssetLoader.h"
#include "game/app/GameSettings.h"
#include "game/tables/ItemTable.h"

#include <chrono>

#include <doctest/doctest.h>

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <vector>

namespace
{
std::vector<uint8_t> readBinaryFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);

    if (!file)
    {
        return {};
    }

    return std::vector<uint8_t>(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
}

void appendUInt16(std::vector<uint8_t> &bytes, uint16_t value)
{
    bytes.push_back(static_cast<uint8_t>(value & 0xffu));
    bytes.push_back(static_cast<uint8_t>((value >> 8) & 0xffu));
}

void appendUInt32(std::vector<uint8_t> &bytes, uint32_t value)
{
    bytes.push_back(static_cast<uint8_t>(value & 0xffu));
    bytes.push_back(static_cast<uint8_t>((value >> 8) & 0xffu));
    bytes.push_back(static_cast<uint8_t>((value >> 16) & 0xffu));
    bytes.push_back(static_cast<uint8_t>((value >> 24) & 0xffu));
}

std::vector<uint8_t> makeTwoPixelIndexedBmp()
{
    constexpr uint32_t fileHeaderSize = 14;
    constexpr uint32_t dibHeaderSize = 40;
    constexpr uint32_t paletteBytes = 2 * 4;
    constexpr uint32_t pixelOffset = fileHeaderSize + dibHeaderSize + paletteBytes;
    constexpr uint32_t rowBytes = 4;
    constexpr uint32_t fileSize = pixelOffset + rowBytes;

    std::vector<uint8_t> bytes;
    bytes.reserve(fileSize);
    bytes.push_back('B');
    bytes.push_back('M');
    appendUInt32(bytes, fileSize);
    appendUInt16(bytes, 0);
    appendUInt16(bytes, 0);
    appendUInt32(bytes, pixelOffset);
    appendUInt32(bytes, dibHeaderSize);
    appendUInt32(bytes, 2);
    appendUInt32(bytes, 1);
    appendUInt16(bytes, 1);
    appendUInt16(bytes, 8);
    appendUInt32(bytes, 0);
    appendUInt32(bytes, rowBytes);
    appendUInt32(bytes, 0);
    appendUInt32(bytes, 0);
    appendUInt32(bytes, 2);
    appendUInt32(bytes, 0);
    bytes.insert(bytes.end(), {252, 252, 0, 0});
    bytes.insert(bytes.end(), {0, 0, 255, 0});
    bytes.insert(bytes.end(), {0, 1, 0, 0});
    return bytes;
}

std::vector<uint8_t> makeTwoPixelIndexedPcx()
{
    std::vector<uint8_t> bytes(128, 0);
    bytes[0] = 0x0a;
    bytes[1] = 5;
    bytes[2] = 1;
    bytes[3] = 8;
    bytes[8] = 1;
    bytes[65] = 1;
    bytes[66] = 2;
    bytes.push_back(0);
    bytes.push_back(1);
    bytes.push_back(0x0c);
    bytes.resize(bytes.size() + 256 * 3, 0);
    const size_t paletteOffset = bytes.size() - 256 * 3;
    bytes[paletteOffset + 1] = 255;
    bytes[paletteOffset + 2] = 255;
    bytes[paletteOffset + 3] = 10;
    bytes[paletteOffset + 4] = 20;
    bytes[paletteOffset + 5] = 30;
    return bytes;
}
}

TEST_CASE("ImageAssetLoader decodes PNG pixels through shared loader")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path pngPath =
        sourceRoot / "editor" / "assets" / "editor_ux_work" / "mockups" / "Level editor UI redesign mockup.png";
    const std::vector<uint8_t> bytes = readBinaryFile(pngPath);

    REQUIRE_FALSE(bytes.empty());

    const std::optional<OpenYAMM::Engine::ImagePixelsBgra> image =
        OpenYAMM::Engine::decodeImagePixelsBgra(bytes, pngPath.generic_string());

    REQUIRE(image.has_value());
    CHECK(image->width > 0);
    CHECK(image->height > 0);
    CHECK(image->pixels.size() == static_cast<size_t>(image->width) * static_cast<size_t>(image->height) * 4);
}

TEST_CASE("ImageAssetLoader decodes the restored Arcomage PNG atlas with its legacy PCX name")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::string atlasPath = "engine/icons_x2/sprites.pcx";
    const std::vector<uint8_t> bytes = readBinaryFile(sourceRoot / "assets_dev" / atlasPath);
    REQUIRE_FALSE(bytes.empty());

    const std::optional<ImagePixelsBgra> image = decodeImagePixelsBgra(bytes, atlasPath);
    REQUIRE(image);
    CHECK(scalePhysicalPixelsToLogical(image->width, assetScaleTierFromResolvedPath(atlasPath)) == 960);
    CHECK(scalePhysicalPixelsToLogical(image->height, assetScaleTierFromResolvedPath(atlasPath)) == 2500);
    CHECK(image->pixels.size() == static_cast<size_t>(image->width) * static_cast<size_t>(image->height) * 4);
}

TEST_CASE("ImageAssetLoader applies palette zero transparency without override palette")
{
    OpenYAMM::Engine::ImageDecodeOptions options = {};
    options.applyPaletteZeroTransparencyKey = true;
    const std::vector<uint8_t> bytes = makeTwoPixelIndexedBmp();

    const std::optional<OpenYAMM::Engine::ImagePixelsBgra> image =
        OpenYAMM::Engine::decodeImagePixelsBgra(bytes, "indexed-zero-key.bmp", options);

    REQUIRE(image.has_value());
    REQUIRE(image->width == 2);
    REQUIRE(image->height == 1);
    REQUIRE(image->pixels.size() == 8);
    CHECK(image->pixels[0] == 252);
    CHECK(image->pixels[1] == 252);
    CHECK(image->pixels[2] == 0);
    CHECK(image->pixels[3] == 0);
    CHECK(image->pixels[4] == 0);
    CHECK(image->pixels[5] == 0);
    CHECK(image->pixels[6] == 255);
    CHECK(image->pixels[7] == 255);
}

TEST_CASE("ImageAssetLoader decodes indexed PCX and applies the teal transparency key")
{
    OpenYAMM::Engine::ImageDecodeOptions options = {};
    options.applyTealTransparencyKey = true;
    const std::vector<uint8_t> bytes = makeTwoPixelIndexedPcx();

    const std::optional<OpenYAMM::Engine::ImagePixelsBgra> image =
        OpenYAMM::Engine::decodeImagePixelsBgra(bytes, "dialogue-background.pcx", options);

    REQUIRE(image.has_value());
    REQUIRE(image->width == 2);
    REQUIRE(image->height == 1);
    REQUIRE(image->pixels.size() == 8);
    CHECK(image->pixels[3] == 0);
    CHECK(image->pixels[4] == 30);
    CHECK(image->pixels[5] == 20);
    CHECK(image->pixels[6] == 10);
    CHECK(image->pixels[7] == 255);
}

TEST_CASE("ImageAssetLoader restored icons preserve fallback sizes and extension priority")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("openyamm_restored_icons_" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    const std::filesystem::path assets = root / "assets_dev";
    const std::vector<uint8_t> nativePng = {
        137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, 0, 0, 0, 32,
        0, 0, 0, 32, 8, 6, 0, 0, 0, 115, 122, 122, 244, 0, 0, 0, 53, 73, 68, 65,
        84, 120, 156, 237, 206, 65, 1, 0, 48, 8, 196, 176, 99, 26, 38, 98, 34, 240, 111, 107,
        200, 224, 147, 26, 104, 234, 190, 254, 89, 236, 108, 206, 1, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 146, 100, 0, 175, 99, 1, 183, 129, 6, 149, 96, 0, 0,
        0, 0, 73, 69, 78, 68, 174, 66, 96, 130
    };
    const auto writeBytes = [](const std::filesystem::path &path, const std::vector<uint8_t> &bytes)
    {
        std::filesystem::create_directories(path.parent_path());
        std::ofstream file(path, std::ios::binary);
        file.write(reinterpret_cast<const char *>(bytes.data()), bytes.size());
    };
    writeBytes(assets / "engine/icons/restored.png", nativePng);
    writeBytes(assets / "engine/icons/fallback.png", nativePng);
    // Real 64x64 BMP, deliberately a lower-priority extension than the original PNG.
    std::vector<uint8_t> restoredBmp;
    restoredBmp.insert(restoredBmp.end(), {'B', 'M'});
    appendUInt32(restoredBmp, 54 + 64 * 64 * 3);
    appendUInt32(restoredBmp, 0);
    appendUInt32(restoredBmp, 54);
    appendUInt32(restoredBmp, 40);
    appendUInt32(restoredBmp, 64);
    appendUInt32(restoredBmp, 64);
    appendUInt16(restoredBmp, 1);
    appendUInt16(restoredBmp, 24);
    restoredBmp.resize(54, 0);
    restoredBmp.resize(54 + 64 * 64 * 3, 180);

    SUBCASE("partial restoration")
    {
        writeBytes(assets / "engine/icons_x2/ReStOrEd.BMP", restoredBmp);
    }
    SUBCASE("no restored directory yet")
    {
    }
    SUBCASE("world-local restoration")
    {
        writeBytes(assets / "worlds/mm6/icons/portrait.png", nativePng);
        writeBytes(assets / "worlds/mm6/icons_x2/portrait.bmp", restoredBmp);
    }

    for (const bool enabled : {false, true})
    {
        AssetFileSystem fs;
        AssetScaleProfile profile;
        profile.preferRestoredIcons = enabled;
        // A different global tier must never shrink original icons.
        REQUIRE(fs.initialize(root, assets, AssetScaleTier::X4, profile, "mm6"));
        DirectoryAssetPathCache directories;
        AssetPathLookupCache paths;
        BinaryAssetCache binaries;
        for (const std::string &name : {"restored", "fallback"})
        {
            const std::optional<ImagePixelsBgra> image = loadImageAssetPixelsBgra(
                fs, "Data/icons", name, directories, paths, binaries);
            REQUIRE(image);
            const bool restored = enabled && name == "restored"
                && std::filesystem::exists(assets / "engine/icons_x2/ReStOrEd.BMP");
            CHECK(image->assetScaleTier == (restored ? AssetScaleTier::X2 : AssetScaleTier::X1));
            CHECK(image->width == (restored ? 64 : 32));
            CHECK(scalePhysicalPixelsToLogical(image->width, image->assetScaleTier) == 32);
            CHECK(scalePhysicalPixelsToLogical(image->height, image->assetScaleTier) == 32);
            const size_t cachedPaths = paths.size();
            REQUIRE(loadImageAssetPixelsBgra(fs, "Data/icons", name, directories, paths, binaries));
            CHECK(paths.size() == cachedPaths);
        }
        OpenYAMM::Game::ItemTable items;
        REQUIRE(items.load(fs, {{"1", "restored", "Restored item"}, {"2", "fallback", "Original item"}}, {}));
        for (const uint32_t id : {1u, 2u})
        {
            REQUIRE(items.get(id) != nullptr);
            CHECK(items.get(id)->inventoryWidth == 1);
            CHECK(items.get(id)->inventoryHeight == 1);
        }
        if (std::filesystem::exists(assets / "worlds/mm6/icons/portrait.png"))
        {
            const std::optional<ImagePixelsBgra> portrait = loadImageAssetPixelsBgra(
                fs, "worlds/mm6/icons", "portrait", directories, paths, binaries);
            REQUIRE(portrait);
            CHECK(portrait->assetScaleTier == (enabled ? AssetScaleTier::X2 : AssetScaleTier::X1));
            CHECK(portrait->width == (enabled ? 64 : 32));
        }
    }
    std::filesystem::remove_all(root);
}

TEST_CASE("restored icon preference settings round trip without changing explicit tiers")
{
    using namespace OpenYAMM;
    Game::GameSettings settings = Game::GameSettings::createDefault();
    CHECK_FALSE(settings.assetScaleProfile.preferRestoredIcons);
    settings.assetScaleProfile.icons = Engine::AssetScaleTier::X4;
    const std::filesystem::path path = std::filesystem::temp_directory_path()
        / "openyamm_restored_icons_settings.ini";
    for (const bool enabled : {true, false})
    {
        settings.assetScaleProfile.preferRestoredIcons = enabled;
        std::string error;
        REQUIRE(Game::saveGameSettings(path, settings, error));
        const std::optional<Game::GameSettings> loaded = Game::loadGameSettings(path, error);
        REQUIRE(loaded);
        CHECK(loaded->assetScaleProfile.preferRestoredIcons == enabled);
        CHECK(loaded->assetScaleProfile.icons == Engine::AssetScaleTier::X4);
        CHECK(Engine::assetScaleTierForCategory(loaded->assetScaleProfile, Engine::AssetScaleCategory::Icons)
            == (enabled ? Engine::AssetScaleTier::X2 : Engine::AssetScaleTier::X4));
    }
    std::filesystem::remove(path);
}

TEST_CASE("ImageAssetLoader reads dimensions without pixel data and rejects invalid headers")
{
    using namespace OpenYAMM::Engine;
    const std::vector<uint8_t> png = {
        137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, 0, 0, 0, 4, 0, 0, 0, 1,
        8, 6, 0, 0, 0, 249, 60, 15, 205};
    const std::optional<ImageDimensions> dimensions = readImageDimensions(png);
    REQUIRE(dimensions);
    CHECK(dimensions->width == 4);
    CHECK(dimensions->height == 1);
    CHECK_FALSE(decodeImagePixelsBgra(png, "header-only.png"));
    std::vector<uint8_t> invalid = png;
    invalid[20] = 1;
    CHECK_FALSE(readImageDimensions(invalid));
    CHECK_FALSE(readImageDimensions(std::span(png.data(), 24)));
    const std::vector<uint8_t> bmp = makeTwoPixelIndexedBmp();
    REQUIRE(readImageDimensions(bmp));
    CHECK(readImageDimensions(bmp)->width == 2);
    std::vector<uint8_t> topDown = bmp;
    topDown[22] = topDown[23] = topDown[24] = topDown[25] = 255;
    REQUIRE(readImageDimensions(topDown));
    CHECK(readImageDimensions(topDown)->height == 1);
    topDown[22] = topDown[23] = topDown[24] = 0;
    topDown[25] = 128;
    CHECK_FALSE(readImageDimensions(topDown));
    REQUIRE(readImageDimensions(makeTwoPixelIndexedPcx()));
    CHECK(readImageDimensions(makeTwoPixelIndexedPcx())->width == 2);
}

TEST_CASE("ImageAssetLoader PNG channel conversion preserves alpha and transparency keys")
{
    using namespace OpenYAMM::Engine;
    const std::vector<uint8_t> png = {
        137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, 0, 0, 0, 4, 0, 0, 0, 1, 8, 6,
        0, 0, 0, 249, 60, 15, 205, 0, 0, 0, 22, 73, 68, 65, 84, 120, 156, 99, 224, 18, 145, 251, 207,
        240, 31, 8, 128, 132, 134, 145, 141, 32, 0, 67, 2, 7, 221, 30, 88, 140, 144, 0, 0, 0, 0, 73,
        69, 78, 68, 174, 66, 96, 130};
    ImageDecodeOptions options;
    options.applyTealTransparencyKey = true;
    options.applyMagentaTransparencyKey = true;
    const std::optional<ImagePixelsBgra> image = decodeImagePixelsBgra(png, "colors.png", options);
    REQUIRE(image);
    const std::vector<uint8_t> expected = {30, 20, 10, 255, 255, 255, 0, 0, 255, 0, 255, 0, 60, 50, 40, 17};
    CHECK(image->pixels == expected);
}
