#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
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

    Engine::CookedTexture partialChain = texture;
    partialChain.levels = 2;
    partialChain.blocks.resize(Engine::cookedTextureBlockBytes(partialChain.codec, 8, 4, 2));
    CHECK_THROWS(Engine::encodeCookedTexture(partialChain));
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
        CHECK(Engine::hasCookedTextureSignature(loaded.asset->images[0].bytes));

        writeBytes(models / "textures/colour.oytex", std::vector<uint8_t>{1, 2, 3, 4, 5, 6, 7, 8, 9});
        const Engine::ModelLoadResult rejected = Engine::GltfModelLoader().load(assets, "engine/models/cooked.gltf");
        CHECK_FALSE(rejected);
        CHECK(rejected.error.find("neither a PNG nor a cooked texture") != std::string::npos);
        assets.shutdown();
    }
    std::filesystem::remove_all(root);
}
