#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/ImageAssetLoader.h"
#include "engine/models/GltfModelLoader.h"
#include "engine/render/CookedTexture.h"
#include "tools/TextureBlockEncode.h"

#include <Decode.hpp>
#include <bcdec.h>

#include <array>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace
{
using namespace OpenYAMM;
using Engine::TextureBlockCodec;

enum class Pattern
{
    Solid,
    // Tiny noise around one colour: both quantized BC1 endpoints become equal (metallic-roughness maps).
    NearlySolid,
    Ramp,
};

std::vector<uint8_t> testImage(int width, int height, Pattern pattern)
{
    std::vector<uint8_t> rgba(size_t(width) * height * 4);
    for (int y = 0; y < height; ++y)
    {
        for (int x = 0; x < width; ++x)
        {
            uint8_t *pTexel = rgba.data() + (size_t(y) * width + x) * 4;
            const int noise = pattern == Pattern::NearlySolid ? (x + y) % 2 : 0;
            const int ramp = (x + y * width) * 255 / (width * height - 1);
            pTexel[0] = uint8_t(pattern == Pattern::Ramp ? ramp : 255 - noise);
            pTexel[1] = uint8_t(pattern == Pattern::Ramp ? ramp * 3 / 4 + 20 : 200 + noise);
            pTexel[2] = uint8_t(pattern == Pattern::Ramp ? ramp / 2 + 40 : 8 + noise);
            pTexel[3] = 255;
        }
    }
    return rgba;
}

// Decodes with independent decoders (bcdec for BC, etcpak for ETC/EAC) to RGBA8.
std::vector<uint8_t> decode(TextureBlockCodec codec, const std::vector<uint8_t> &blocks, int width, int height)
{
    std::vector<uint8_t> rgba(size_t(width) * height * 4, 0);
    if (codec == TextureBlockCodec::Etc2Rgb || codec == TextureBlockCodec::Etc2Rgba || codec == TextureBlockCodec::EacR
        || codec == TextureBlockCodec::EacRg)
    {
        std::vector<uint64_t> input(blocks.size() / 8);
        std::memcpy(input.data(), blocks.data(), blocks.size());
        std::vector<uint32_t> output(size_t(width) * height);
        switch (codec)
        {
        case TextureBlockCodec::Etc2Rgb: DecodeRGB(input.data(), output.data(), width, height); break;
        case TextureBlockCodec::Etc2Rgba: DecodeRGBA(input.data(), output.data(), width, height); break;
        case TextureBlockCodec::EacR: DecodeR(input.data(), output.data(), width, height); break;
        default: DecodeRG(input.data(), output.data(), width, height); break;
        }
        std::memcpy(rgba.data(), output.data(), rgba.size());
        return rgba;
    }
    const size_t blockBytes = Engine::textureBlockBytes(codec, 4, 4);
    const uint8_t *pBlock = blocks.data();
    for (int y = 0; y < height; y += 4)
    {
        for (int x = 0; x < width; x += 4, pBlock += blockBytes)
        {
            uint8_t *pTarget = rgba.data() + (size_t(y) * width + x) * 4;
            std::array<uint8_t, 4 * 4 * 2> channels = {};
            switch (codec)
            {
            case TextureBlockCodec::Bc1: bcdec_bc1(pBlock, pTarget, width * 4); break;
            case TextureBlockCodec::Bc7: bcdec_bc7(pBlock, pTarget, width * 4); break;
            case TextureBlockCodec::Bc4:
            case TextureBlockCodec::Bc5:
            {
                const bool two = codec == TextureBlockCodec::Bc5;
                if (two)
                {
                    bcdec_bc5(pBlock, channels.data(), 4 * 2);
                }
                else
                {
                    bcdec_bc4(pBlock, channels.data(), 4);
                }
                for (int row = 0; row < 4; ++row)
                {
                    for (int column = 0; column < 4; ++column)
                    {
                        uint8_t *pTexel = pTarget + (size_t(row) * width + column) * 4;
                        pTexel[0] = channels[(row * 4 + column) * (two ? 2 : 1)];
                        pTexel[1] = two ? channels[(row * 4 + column) * 2 + 1] : 0;
                    }
                }
                break;
            }
            default: break;
            }
        }
    }
    return rgba;
}

int maximumError(const std::vector<uint8_t> &a, const std::vector<uint8_t> &b, int channels)
{
    int error = 0;
    for (size_t i = 0; i < a.size(); ++i)
    {
        if (int(i % 4) < channels)
        {
            error = std::max(error, std::abs(int(a[i]) - int(b[i])));
        }
    }
    return error;
}

std::filesystem::path temporaryRoot()
{
    const uint64_t ticks = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    std::filesystem::path root = std::filesystem::temp_directory_path() / ("openyamm_cooked_" + std::to_string(ticks));
    std::filesystem::create_directories(root);
    return root;
}

void writeBytes(const std::filesystem::path &path, const std::vector<uint8_t> &bytes)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    stream.write(reinterpret_cast<const char *>(bytes.data()), std::streamsize(bytes.size()));
}

Engine::CookedTexture sampleTexture()
{
    Engine::CookedTexture texture;
    texture.codec = TextureBlockCodec::Bc7;
    texture.semantic = Engine::ImageMipSemantic::Srgb;
    texture.alphaCutoff = 128;
    texture.width = 8;
    texture.height = 4;
    texture.levels = Engine::cookedTextureFullChainLevels(8, 4);
    texture.sourceHash = 0x1234;
    texture.statistics = Engine::CookedTextureStatistics{Engine::CookedTextureAlphaUse::Cutout, {256, 512, 65280}};
    texture.blocks.resize(Engine::cookedTextureBlockBytes(texture.codec, 8, 4, texture.levels));
    for (size_t i = 0; i < texture.blocks.size(); ++i)
    {
        texture.blocks[i] = uint8_t(i * 7);
    }
    return texture;
}
}

TEST_CASE("Texture block codecs keep stable names and block sizes")
{
    for (TextureBlockCodec codec : {TextureBlockCodec::Bc1, TextureBlockCodec::Bc4, TextureBlockCodec::Bc5,
             TextureBlockCodec::Bc7, TextureBlockCodec::Etc2Rgb, TextureBlockCodec::Etc2Rgba, TextureBlockCodec::EacR,
             TextureBlockCodec::EacRg})
    {
        CHECK(Engine::parseTextureBlockCodec(Engine::textureBlockCodecName(codec)) == codec);
    }
    CHECK_FALSE(Engine::parseTextureBlockCodec("png").has_value());
    CHECK_EQ(uint64_t(TextureBlockCodec::Bc7), 1);
    CHECK_EQ(uint64_t(TextureBlockCodec::Etc2Rgb), 8);
    CHECK_EQ(Engine::textureBlockBytes(TextureBlockCodec::Bc1, 1, 1), 8);
    CHECK_EQ(Engine::textureBlockBytes(TextureBlockCodec::Bc7, 5, 5), 64);
    CHECK_EQ(Engine::cookedTextureFullChainLevels(2080, 1024), 12);
}

TEST_CASE("Cooked textures round trip and reject damaged or incompatible files")
{
    const Engine::CookedTexture texture = sampleTexture();
    const std::vector<uint8_t> bytes = Engine::encodeCookedTexture(texture);
    CHECK(Engine::hasCookedTextureSignature(bytes));
    const Engine::CookedTexture decoded = Engine::decodeCookedTexture(bytes);
    CHECK(decoded.codec == texture.codec);
    CHECK(decoded.semantic == texture.semantic);
    CHECK_EQ(decoded.alphaCutoff, 128);
    CHECK_EQ(decoded.levels, 4);
    CHECK_EQ(decoded.sourceHash, 0x1234);
    REQUIRE(decoded.statistics.has_value());
    CHECK(decoded.statistics->alphaUse == Engine::CookedTextureAlphaUse::Cutout);
    CHECK(decoded.statistics->meanBgr256 == std::array<uint16_t, 3>{256, 512, 65280});
    CHECK(decoded.blocks == texture.blocks);

    std::vector<uint8_t> truncated = bytes;
    truncated.pop_back();
    CHECK_THROWS(Engine::decodeCookedTexture(truncated));
    std::vector<uint8_t> corrupt = bytes;
    corrupt.back() ^= 0x5a;
    CHECK_THROWS(Engine::decodeCookedTexture(corrupt));
    std::vector<uint8_t> version = bytes;
    version[8] = 99;
    CHECK_THROWS(Engine::decodeCookedTexture(version));
    std::vector<uint8_t> semantic = bytes;
    semantic[24] = 9;
    CHECK_THROWS(Engine::decodeCookedTexture(semantic));

    std::vector<uint8_t> alphaUse = bytes;
    alphaUse[96] = 7;
    CHECK_THROWS(Engine::decodeCookedTexture(alphaUse));
    Engine::CookedTexture noStatistics = texture;
    noStatistics.statistics.reset();
    CHECK_THROWS(Engine::encodeCookedTexture(noStatistics));

    Engine::CookedTexture partialChain = texture;
    partialChain.levels = 2;
    partialChain.blocks.resize(Engine::cookedTextureBlockBytes(partialChain.codec, 8, 4, 2));
    CHECK_THROWS(Engine::encodeCookedTexture(partialChain));
}

TEST_CASE("Cooked textures record their content size and cut out block-aligned regions")
{
    Engine::CookedTexture texture;
    texture.codec = TextureBlockCodec::Bc7;
    texture.width = 8;
    texture.height = 8;
    texture.contentWidth = 6;
    texture.contentHeight = 7;
    texture.statistics = Engine::CookedTextureStatistics{};
    // Four 16-byte BC7 blocks, each filled with its block index.
    for (uint8_t block = 0; block < 4; ++block)
    {
        texture.blocks.insert(texture.blocks.end(), 16, block);
    }
    const Engine::CookedTexture decoded = Engine::decodeCookedTexture(Engine::encodeCookedTexture(texture));
    CHECK_EQ(decoded.contentWidth, 6);
    CHECK_EQ(decoded.contentHeight, 7);
    const std::vector<uint8_t> lowerRight = Engine::cookedTextureRegionBlocks(decoded, 4, 4, 4, 4);
    CHECK(lowerRight == std::vector<uint8_t>(16, 3));
    const std::vector<uint8_t> rightColumn = Engine::cookedTextureRegionBlocks(decoded, 4, 0, 4, 8);
    REQUIRE_EQ(rightColumn.size(), 32);
    CHECK_EQ(rightColumn[0], 1);
    CHECK_EQ(rightColumn[16], 3);
    CHECK_THROWS(Engine::cookedTextureRegionBlocks(decoded, 2, 0, 4, 4));
    CHECK_THROWS(Engine::cookedTextureRegionBlocks(decoded, 4, 4, 8, 4));
    Engine::CookedTexture oversizedContent = texture;
    oversizedContent.contentWidth = 9;
    CHECK_THROWS(Engine::encodeCookedTexture(oversizedContent));
}

TEST_CASE("Cooked texture regions decode back to BGRA on the CPU")
{
    // Two 4x4 blocks side by side: opaque red, then transparent green (RGBA input to the encoder).
    std::vector<uint8_t> rgba;
    for (int y = 0; y < 4; ++y)
    {
        for (int x = 0; x < 8; ++x)
        {
            const std::array<uint8_t, 4> texel = x < 4 ? std::array<uint8_t, 4>{200, 20, 10, 255}
                                                       : std::array<uint8_t, 4>{10, 180, 30, 0};
            rgba.insert(rgba.end(), texel.begin(), texel.end());
        }
    }
    Engine::CookedTexture texture;
    texture.codec = TextureBlockCodec::Bc7;
    texture.width = 8;
    texture.height = 4;
    texture.blocks = Tools::encodeTextureBlocks(rgba, 8, 4, TextureBlockCodec::Bc7, {});
    const std::vector<uint8_t> right = Engine::decodeCookedTextureRegionBgra(texture, 4, 0, 4, 4);
    REQUIRE_EQ(right.size(), 4 * 4 * 4);
    CHECK(std::abs(int(right[0]) - 30) <= 2);   // blue
    CHECK(std::abs(int(right[1]) - 180) <= 2);  // green
    CHECK(std::abs(int(right[2]) - 10) <= 2);   // red
    CHECK(right[3] == 0);
    const std::vector<uint8_t> left = Engine::decodeCookedTextureRegionBgra(texture, 0, 0, 4, 4);
    CHECK(std::abs(int(left[2]) - 200) <= 2);
    CHECK(left[3] >= 250);
}

TEST_CASE("Cooked textures need the current version and a zstd frame checksum")
{
    const std::vector<uint8_t> current = Engine::encodeCookedTexture(sampleTexture());
    std::vector<uint8_t> version2 = current;
    version2[8] = 2;
    CHECK_THROWS(Engine::decodeCookedTexture(version2));

    // Clearing the frame's Content_Checksum_flag (descriptor bit 2) leaves a payload nothing verifies.
    std::vector<uint8_t> unchecked = current;
    unchecked[Engine::CookedTextureHeaderBytes + 4] &= uint8_t(~0x04);
    CHECK_THROWS(Engine::decodeCookedTexture(unchecked));

    // A flipped block byte fails the checksum while decompressing.
    Engine::CookedTexture texture = sampleTexture();
    std::vector<uint8_t> damaged = Engine::encodeCookedTexture(texture);
    damaged[damaged.size() - 6] ^= 0x01;
    CHECK_THROWS(Engine::decodeCookedTexture(damaged));
}

TEST_CASE("World surface lookup prefers the cooked file within each scale tier")
{
    const std::filesystem::path root = temporaryRoot();
    const std::filesystem::path textures = root / "assets_dev/worlds/mm6";
    const std::vector<uint8_t> placeholder = {1};
    writeBytes(textures / "textures/wall.bmp", placeholder);
    writeBytes(textures / "textures/wall.oytex", placeholder);
    writeBytes(textures / "textures_x2/wall.png", placeholder);
    writeBytes(textures / "textures/door.bmp", placeholder);
    writeBytes(textures / "textures_x2/door.png", placeholder);
    writeBytes(textures / "textures_x2/door.oytex", placeholder);
    const auto lookup = [&](Engine::AssetScaleTier tier, const std::string &name)
    {
        Engine::AssetFileSystem assets;
        Engine::AssetScaleProfile profile;
        profile.textures = tier;
        REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1, profile, "mm6"));
        Engine::DirectoryAssetPathCache directories;
        Engine::AssetPathLookupCache paths;
        const std::optional<std::string> path =
            Engine::findCookedOrImageAssetPath(assets, "Data/bitmaps", name, directories, paths);
        assets.shutdown();
        REQUIRE(path);
        return std::filesystem::path(*path).parent_path().filename().string() + "/"
            + std::filesystem::path(*path).filename().string();
    };
    CHECK_EQ(lookup(Engine::AssetScaleTier::X1, "wall"), "textures/wall.oytex");
    // A source in the active tier wins over a cooked file of another tier (a tex.py review stage's new x2 art).
    CHECK_EQ(lookup(Engine::AssetScaleTier::X2, "wall"), "textures_x2/wall.png");
    CHECK_EQ(lookup(Engine::AssetScaleTier::X2, "door"), "textures_x2/door.oytex");
    CHECK_EQ(lookup(Engine::AssetScaleTier::X1, "door"), "textures/door.bmp");
    std::filesystem::remove_all(root);
}

TEST_CASE("A borrowed surface texture resolves to its own world's folder, where its material maps lie")
{
    // A6 (D4's hkm3elw): a Xeen map lays an MM7 texture; its surface material maps sit in MM7's
    // surface_materials_x4 beside the textures_x4 the lookup found.
    const std::filesystem::path root = temporaryRoot();
    const std::vector<uint8_t> placeholder = {1};
    writeBytes(root / "assets_dev/worlds/mm7/textures_x4/wall.oytex", placeholder);
    writeBytes(root / "assets_dev/worlds/mm7/surface_materials_x4/wall_n.oytex", placeholder);
    writeBytes(root / "assets_dev/worlds/xeen/textures_x4/own.oytex", placeholder);
    std::filesystem::create_directories(root / "assets_dev/worlds/xeen/maps");
    Engine::AssetFileSystem assets;
    Engine::AssetScaleProfile profile;
    profile.textures = Engine::AssetScaleTier::X4;
    REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1, profile, "xeen"));
    Engine::DirectoryAssetPathCache directories;
    Engine::AssetPathLookupCache paths;
    const std::optional<std::string> path =
        Engine::findCookedOrImageAssetPath(assets, "Data/bitmaps", "wall", directories, paths);
    REQUIRE(path);
    const std::filesystem::path found(*path);
    const std::string material =
        (found.parent_path().parent_path() / "surface_materials_x4" / "wall_n.oytex").generic_string();
    CHECK(assets.readBinaryFile(material).has_value());
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("Cooked texture statistics record alpha use and the mean colour")
{
    // BGRA: an opaque texel, a keyed texel, then a partly transparent one.
    const std::vector<uint8_t> cutout = {10, 20, 30, 255, 30, 40, 50, 0};
    const Engine::CookedTextureStatistics statistics = Engine::measureCookedTextureStatistics(cutout);
    CHECK(statistics.alphaUse == Engine::CookedTextureAlphaUse::Cutout);
    CHECK(statistics.meanBgr256 == std::array<uint16_t, 3>{20 * 256, 30 * 256, 40 * 256});
    const std::vector<uint8_t> partial = {0, 0, 0, 0, 255, 255, 255, 128};
    CHECK(Engine::measureCookedTextureStatistics(partial).alphaUse == Engine::CookedTextureAlphaUse::Partial);
    const std::vector<uint8_t> opaque = {1, 2, 3, 255};
    CHECK(Engine::measureCookedTextureStatistics(opaque).alphaUse == Engine::CookedTextureAlphaUse::Opaque);
}

TEST_CASE("Texture block encoders reproduce gradients and solid colours in every codec")
{
    struct Case
    {
        TextureBlockCodec codec;
        int channels;
        int gradientTolerance;
    };
    // Uniform colours must survive nearly exactly (metallic-roughness maps are mostly uniform blocks); a BC1 block
    // decoded in three-colour mode would show its transparent-black index here.
    for (const Case &test : {Case{TextureBlockCodec::Bc1, 3, 12}, Case{TextureBlockCodec::Bc7, 4, 8},
             Case{TextureBlockCodec::Bc4, 1, 12}, Case{TextureBlockCodec::Bc5, 2, 12},
             Case{TextureBlockCodec::Etc2Rgb, 3, 16}, Case{TextureBlockCodec::Etc2Rgba, 4, 16},
             Case{TextureBlockCodec::EacR, 1, 12}, Case{TextureBlockCodec::EacRg, 2, 12}})
    {
        CAPTURE(Engine::textureBlockCodecName(test.codec));
        for (Pattern pattern : {Pattern::Solid, Pattern::NearlySolid, Pattern::Ramp})
        {
            CAPTURE(int(pattern));
            const std::vector<uint8_t> rgba = testImage(16, 8, pattern);
            const std::vector<uint8_t> blocks = Tools::encodeTextureBlocks(rgba, 16, 8, test.codec, {});
            REQUIRE_EQ(blocks.size(), Engine::textureBlockBytes(test.codec, 16, 8));
            const std::vector<uint8_t> decoded = decode(test.codec, blocks, 16, 8);
            CHECK_LE(maximumError(rgba, decoded, test.channels), pattern == Pattern::Ramp ? test.gradientTolerance : 8);
            if (test.codec == TextureBlockCodec::Bc1 || test.codec == TextureBlockCodec::Etc2Rgb)
            {
                for (size_t alpha = 3; alpha < decoded.size(); alpha += 4)
                {
                    REQUIRE_EQ(decoded[alpha], 255);
                }
            }
        }
    }
}

TEST_CASE("glTF loader reads cooked textures by URI and rejects unknown image bytes")
{
    const std::filesystem::path root = temporaryRoot();
    const std::filesystem::path models = root / "assets_dev/engine/models";
    std::vector<uint8_t> buffer;
    for (float value : {0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f,
             0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f})
    {
        const uint8_t *pBytes = reinterpret_cast<const uint8_t *>(&value);
        buffer.insert(buffer.end(), pBytes, pBytes + 4);
    }
    for (uint16_t index : {uint16_t(0), uint16_t(1), uint16_t(2), uint16_t(0)})
    {
        const uint8_t *pBytes = reinterpret_cast<const uint8_t *>(&index);
        buffer.insert(buffer.end(), pBytes, pBytes + 2);
    }
    writeBytes(models / "cooked.bin", buffer);
    const std::string json = R"({
  "asset": {"version": "2.0"},
  "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
  "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3,
    "material": 0}]}],
  "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
  "textures": [{"source": 0}],
  "images": [{"uri": "textures/colour.oytex"}],
  "buffers": [{"uri": "cooked.bin", "byteLength": 104}],
  "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36}, {"buffer": 0, "byteOffset": 36, "byteLength": 36},
    {"buffer": 0, "byteOffset": 72, "byteLength": 24}, {"buffer": 0, "byteOffset": 96, "byteLength": 6}],
  "accessors": [
    {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]},
    {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
    {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC2"},
    {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"}]
})";
    writeBytes(models / "cooked.gltf", std::vector<uint8_t>(json.begin(), json.end()));
    writeBytes(models / "textures/colour.oytex", Engine::encodeCookedTexture(sampleTexture()));
    {
        Engine::AssetFileSystem assets;
        REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1));
        const Engine::ModelLoadResult loaded = Engine::GltfModelLoader().load(assets, "engine/models/cooked.gltf");
        REQUIRE_MESSAGE(loaded, loaded.error);
        REQUIRE_EQ(loaded.asset->images.size(), 1);
        CHECK(loaded.asset->images[0].cooked);
        // The texture stays in its file until the renderer uploads it.
        CHECK(loaded.asset->images[0].bytes.empty());
        CHECK_EQ(loaded.asset->images[0].pFileSystem, &assets);

        writeBytes(models / "textures/colour.oytex", std::vector<uint8_t>{1, 2, 3, 4, 5, 6, 7, 8, 9});
        const Engine::ModelLoadResult rejected = Engine::GltfModelLoader().load(assets, "engine/models/cooked.gltf");
        CHECK_FALSE(rejected);
        CHECK(rejected.error.find("neither a PNG nor a cooked texture") != std::string::npos);
        assets.shutdown();
    }
    std::filesystem::remove_all(root);
}

TEST_CASE("glTF loader reads a cooked texture its package leaves out from the engine's or another world's copy")
{
    // Lane P (2026-11-22): the packager leaves out a world's model textures that the engine or another world ships.
    const std::filesystem::path root = temporaryRoot();
    std::vector<uint8_t> buffer;
    for (float value : {0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f,
             0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 1.0f})
    {
        const uint8_t *pBytes = reinterpret_cast<const uint8_t *>(&value);
        buffer.insert(buffer.end(), pBytes, pBytes + 4);
    }
    for (uint16_t index : {uint16_t(0), uint16_t(1), uint16_t(2), uint16_t(0)})
    {
        const uint8_t *pBytes = reinterpret_cast<const uint8_t *>(&index);
        buffer.insert(buffer.end(), pBytes, pBytes + 2);
    }
    const std::string json = R"({
  "asset": {"version": "2.0"},
  "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
  "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3,
    "material": 0}]}],
  "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
  "textures": [{"source": 0}],
  "images": [{"uri": "textures/k.oytex"}],
  "buffers": [{"uri": "m.bin", "byteLength": 104}],
  "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36}, {"buffer": 0, "byteOffset": 36, "byteLength": 36},
    {"buffer": 0, "byteOffset": 72, "byteLength": 24}, {"buffer": 0, "byteOffset": 96, "byteLength": 6}],
  "accessors": [
    {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]},
    {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
    {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC2"},
    {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"}]
})";
    const std::filesystem::path models = root / "assets_dev/worlds/a/models";
    writeBytes(models / "m.bin", buffer);
    writeBytes(models / "m.gltf", std::vector<uint8_t>(json.begin(), json.end()));
    std::filesystem::create_directories(root / "assets_dev/worlds/a/maps");
    const std::vector<uint8_t> cooked = Engine::encodeCookedTexture(sampleTexture());
    {
        // Missing everywhere: today's error.
        Engine::AssetFileSystem assets;
        REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1, "a"));
        const Engine::ModelLoadResult missing = Engine::GltfModelLoader().load(assets, "worlds/a/models/m.gltf");
        CHECK_FALSE(missing);
        CHECK(missing.error.find("model image was not found: worlds/a/models/textures/k.oytex") != std::string::npos);
        assets.shutdown();
    }
    writeBytes(root / "assets_dev/worlds/b/models/textures/k.oytex", cooked);
    {
        // Another world's copy.
        Engine::AssetFileSystem assets;
        REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1, "a"));
        const Engine::ModelLoadResult loaded = Engine::GltfModelLoader().load(assets, "worlds/a/models/m.gltf");
        REQUIRE_MESSAGE(loaded, loaded.error);
        CHECK_EQ(loaded.asset->images[0].sourcePath, "worlds/b/models/textures/k.oytex");
        assets.shutdown();
    }
    writeBytes(root / "assets_dev/engine/models/textures/k.oytex", cooked);
    {
        // The engine's copy first.
        Engine::AssetFileSystem assets;
        REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1, "a"));
        const Engine::ModelLoadResult loaded = Engine::GltfModelLoader().load(assets, "worlds/a/models/m.gltf");
        REQUIRE_MESSAGE(loaded, loaded.error);
        CHECK_EQ(loaded.asset->images[0].sourcePath, "engine/models/textures/k.oytex");
        CHECK(loaded.asset->images[0].cooked);
        assets.shutdown();
    }
    std::filesystem::remove_all(root);
}
