#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/models/GltfModelLoader.h"
#include "engine/models/ModelInstance.h"
#include "game/gameplay/ActorModelPresentation.h"

#include <doctest/doctest.h>

#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <memory>
#include <numbers>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace
{
std::shared_ptr<OpenYAMM::Engine::ModelAsset> makeAnimatedAsset()
{
    using namespace OpenYAMM::Engine;
    std::shared_ptr<ModelAsset> asset = std::make_shared<ModelAsset>();
    asset->nodes.resize(2);
    asset->nodes[0].name = "child";
    asset->nodes[0].parentIndex = 1;
    asset->nodes[0].transform.translation = {1.0f, 0.0f, 0.0f};
    asset->nodes[0].matrix = composeModelTransform(asset->nodes[0].transform);
    asset->nodes[1].name = "root";
    asset->nodes[1].childIndices = {0};
    asset->nodes[1].matrix = identityModelMatrix();
    asset->hierarchyOrder = {1, 0};
    asset->nodeIndicesByName = {{"child", 0}, {"root", 1}};

    ModelAnimationChannel translation;
    translation.nodeIndex = 0;
    translation.target = ModelAnimationTarget::Translation;
    translation.interpolation = ModelAnimationInterpolation::Linear;
    translation.times = {0.0f, 1.0f};
    translation.values = {{0.0f, 0.0f, 0.0f, 0.0f}, {2.0f, 0.0f, 0.0f, 0.0f}};

    ModelAnimationChannel rotation;
    rotation.nodeIndex = 0;
    rotation.target = ModelAnimationTarget::Rotation;
    rotation.interpolation = ModelAnimationInterpolation::Linear;
    rotation.times = {0.0f, 1.0f};
    rotation.values = {{0.0f, 0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 0.0f}};

    ModelAnimationClip clip;
    clip.name = "move";
    clip.durationSeconds = 1.0f;
    clip.channels = {translation, rotation};
    asset->clips.push_back(std::move(clip));
    asset->clipIndicesByName.emplace("move", 0);
    return asset;
}

TEST_CASE("ModelAnimation blends local poses, interrupts transitions and masks actions without eager deformation")
{
    using namespace OpenYAMM::Engine;
    std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    asset->clips.push_back(asset->clips[0]);
    asset->clips[1].name = "hold";
    asset->clips[1].channels[0].values = {{4, 0, 0, 0}, {4, 0, 0, 0}};
    asset->clips[1].channels[1].values = {{0, 0, 0, -1}, {0, 0, 0, -1}};
    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(asset);
    REQUIRE(instances.sample(handle, 0, 0, {}));
    const ModelPose *pPose = instances.pose(handle, false);
    REQUIRE(pPose != nullptr);
    const uint64_t revision = pPose->matrixRevision;
    REQUIRE(instances.sampleBlended(handle, 1, 0, {}, .05f, .1f));
    CHECK(pPose->matrixRevision == revision);
    pPose = instances.pose(handle, false);
    CHECK(pPose->localTransforms[0].translation[0] == doctest::Approx(2));
    CHECK(std::abs(pPose->localTransforms[0].rotation[3]) == doctest::Approx(1));
    CHECK(std::all_of(pPose->deformedVertices.begin(), pPose->deformedVertices.end(),
        [](const auto &node) { return node.empty(); }));
    // Interrupt halfway through: the visible intermediate pose is the new source, so there is no pop.
    REQUIRE(instances.sampleBlended(handle, 0, 0, {}, 0, .1f));
    CHECK(instances.pose(handle, false)->localTransforms[0].translation[0] == doctest::Approx(2));
    REQUIRE(instances.sampleBlended(handle, 0, 0, {}, .05f, .1f));
    CHECK(instances.pose(handle, false)->localTransforms[0].translation[0] == doctest::Approx(1));
    REQUIRE(instances.sampleBlended(handle, 0, 0, {}, .05f, .1f));
    CHECK(instances.pose(handle, false)->localTransforms[0].translation[0] == doctest::Approx(0));
    const std::shared_ptr<const std::vector<float>> mask = std::make_shared<std::vector<float>>(
        std::initializer_list<float>{1.0f, 0.0f});
    const ModelAnimationLayer action{1, 0, .5f, mask};
    REQUIRE(instances.sampleBlended(handle, 0, .5f, {}, 0, 0, action));
    pPose = instances.pose(handle, false);
    CHECK(pPose->localTransforms[0].translation[0] == doctest::Approx(2.5));
    CHECK(pPose->localTransforms[1].translation[0] == doctest::Approx(0));
    CHECK((*instances.nodeMatrix(handle, "child"))[12] == doctest::Approx(2.5));
    CHECK_FALSE(instances.sampleBlended(handle, 0, 0, {}, .1f, .1f, {1, 0, 1, {}}));
    CHECK_FALSE(instances.sampleBlended(handle, 0, 0, {}, -1, .1f));
    REQUIRE(instances.destroy(handle));
    const ModelInstanceHandle recycled = instances.create(asset);
    REQUIRE(instances.sample(recycled, 0, 0, {}));
    CHECK(instances.pose(recycled, false)->localTransforms[0].translation[0] == doctest::Approx(0));
}

TEST_CASE("Actor model yaw wraps smoothly and gait follows travelled distance")
{
    using namespace OpenYAMM::Game;
    constexpr float Degrees = std::numbers::pi_v<float> / 180.0f;
    CHECK(advanceActorModelYaw(350 * Degrees, 10 * Degrees, .1f, 100 * Degrees)
        == doctest::Approx(360 * Degrees));
    CHECK(advanceActorModelYaw(0, 180 * Degrees, .1f, 540 * Degrees) == doctest::Approx(54 * Degrees));
    CHECK(advanceActorModelYaw(1, 2, 0, 540 * Degrees) == 1);
    CHECK(advanceActorModelGait(.9f, 30, 100) == doctest::Approx(.2f));
    CHECK(advanceActorModelGait(.4f, 0, 100) == doctest::Approx(.4f));
}

std::filesystem::path makeTemporaryRoot()
{
    const uint64_t ticks = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_model_" + std::to_string(ticks));
}

void appendFloat(std::vector<uint8_t> &bytes, float value)
{
    const size_t offset = bytes.size();
    bytes.resize(offset + sizeof(value));
    std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

void appendUInt16(std::vector<uint8_t> &bytes, uint16_t value)
{
    bytes.push_back(static_cast<uint8_t>(value & 0xff));
    bytes.push_back(static_cast<uint8_t>((value >> 8) & 0xff));
}

void appendUInt32(std::vector<uint8_t> &bytes, uint32_t value)
{
    bytes.push_back(static_cast<uint8_t>(value & 0xff));
    bytes.push_back(static_cast<uint8_t>((value >> 8) & 0xff));
    bytes.push_back(static_cast<uint8_t>((value >> 16) & 0xff));
    bytes.push_back(static_cast<uint8_t>((value >> 24) & 0xff));
}

void writeUInt16(std::ofstream &stream, uint16_t value)
{
    stream.put(static_cast<char>(value & 0xff));
    stream.put(static_cast<char>((value >> 8) & 0xff));
}

void writeUInt32(std::ofstream &stream, uint32_t value)
{
    stream.put(static_cast<char>(value & 0xff));
    stream.put(static_cast<char>((value >> 8) & 0xff));
    stream.put(static_cast<char>((value >> 16) & 0xff));
    stream.put(static_cast<char>((value >> 24) & 0xff));
}

uint32_t crc32(const std::vector<uint8_t> &bytes)
{
    uint32_t crc = 0xffffffffu;
    for (uint8_t byte : bytes)
    {
        crc ^= byte;
        for (int bit = 0; bit < 8; ++bit)
        {
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
        }
    }
    return crc ^ 0xffffffffu;
}

void writeFile(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    stream << text;
}

void writeFile(const std::filesystem::path &path, const std::vector<uint8_t> &bytes)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    stream.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
}

std::vector<uint8_t> fixtureBuffer()
{
    std::vector<uint8_t> bytes;
    for (float value : std::initializer_list<float>{0, 0, 0, 1, 0, 0, 0, 1, 0})
    {
        appendFloat(bytes, value);
    }
    for (int vertex = 0; vertex < 3; ++vertex)
    {
        appendFloat(bytes, 0.0f);
        appendFloat(bytes, 0.0f);
        appendFloat(bytes, 1.0f);
    }
    for (float value : std::initializer_list<float>{0, 0, 1, 0, 0, 1})
    {
        appendFloat(bytes, value);
    }
    appendUInt16(bytes, 0);
    appendUInt16(bytes, 1);
    appendUInt16(bytes, 2);
    appendUInt16(bytes, 0);
    appendUInt16(bytes, 2);
    appendUInt16(bytes, 1);
    appendFloat(bytes, 0.0f);
    appendFloat(bytes, 1.0f);
    for (float value : std::initializer_list<float>{0, 0, 0, 2, 0, 0})
    {
        appendFloat(bytes, value);
    }
    for (float value : std::initializer_list<float>{1, 1, 1, 2, 2, 2})
    {
        appendFloat(bytes, value);
    }
    return bytes;
}

std::string fixtureGltf(const std::string &interpolation = "LINEAR")
{
    return R"({
  "asset": {"version": "2.0"},
  "scene": 0,
  "scenes": [{"nodes": [1]}],
  "nodes": [
    {"name": "attachment", "mesh": 0, "translation": [1, 0, 0]},
    {"name": "root", "children": [0], "translation": [10, 0, 0]}
  ],
  "meshes": [{"name": "triangle", "primitives": [{
    "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0
  }]}],
  "materials": [{"name": "opaque", "pbrMetallicRoughness": {"baseColorFactor": [1, 0.5, 0.25, 1]}}],
  "animations": [
    {"name": "move", "samplers": [{"input": 4, "output": 5, "interpolation": ")" + interpolation + R"("}],
     "channels": [{"sampler": 0, "target": {"node": 0, "path": "translation"}}]},
    {"name": "grow", "samplers": [{"input": 4, "output": 6, "interpolation": "STEP"}],
     "channels": [{"sampler": 0, "target": {"node": 0, "path": "scale"}}]}
  ],
  "buffers": [{"uri": "fixture.bin", "byteLength": 164}],
  "bufferViews": [
    {"buffer": 0, "byteOffset": 0, "byteLength": 36},
    {"buffer": 0, "byteOffset": 36, "byteLength": 36},
    {"buffer": 0, "byteOffset": 72, "byteLength": 24},
    {"buffer": 0, "byteOffset": 96, "byteLength": 12},
    {"buffer": 0, "byteOffset": 108, "byteLength": 8},
    {"buffer": 0, "byteOffset": 116, "byteLength": 24},
    {"buffer": 0, "byteOffset": 140, "byteLength": 24}
  ],
  "accessors": [
    {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
    {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
    {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC2"},
    {"bufferView": 3, "componentType": 5123, "count": 6, "type": "SCALAR"},
    {"bufferView": 4, "componentType": 5126, "count": 2, "type": "SCALAR"},
    {"bufferView": 5, "componentType": 5126, "count": 2, "type": "VEC3"},
    {"bufferView": 6, "componentType": 5126, "count": 2, "type": "VEC3"}
  ]
})";
}

std::vector<uint8_t> fixtureGlb()
{
    std::string json = fixtureGltf();
    const std::string externalUri = "\"uri\": \"fixture.bin\", ";
    const size_t uriOffset = json.find(externalUri);
    if (uriOffset == std::string::npos)
    {
        throw std::runtime_error("fixture glTF has no external buffer URI");
    }
    json.erase(uriOffset, externalUri.size());
    while (json.size() % 4 != 0)
    {
        json.push_back(' ');
    }
    std::vector<uint8_t> binary = fixtureBuffer();
    while (binary.size() % 4 != 0)
    {
        binary.push_back(0);
    }

    std::vector<uint8_t> glb;
    appendUInt32(glb, 0x46546c67u);
    appendUInt32(glb, 2);
    appendUInt32(glb, static_cast<uint32_t>(12 + 8 + json.size() + 8 + binary.size()));
    appendUInt32(glb, static_cast<uint32_t>(json.size()));
    appendUInt32(glb, 0x4e4f534au);
    glb.insert(glb.end(), json.begin(), json.end());
    appendUInt32(glb, static_cast<uint32_t>(binary.size()));
    appendUInt32(glb, 0x004e4942u);
    glb.insert(glb.end(), binary.begin(), binary.end());
    return glb;
}

void writeZipFile(
    const std::filesystem::path &path,
    const std::vector<std::pair<std::string, std::vector<uint8_t>>> &files)
{
    struct Entry
    {
        std::string name;
        uint32_t checksum = 0;
        uint32_t size = 0;
        uint32_t offset = 0;
    };

    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    std::vector<Entry> entries;
    for (const auto &[name, bytes] : files)
    {
        const Entry entry = {
            .name = name,
            .checksum = crc32(bytes),
            .size = static_cast<uint32_t>(bytes.size()),
            .offset = static_cast<uint32_t>(stream.tellp()),
        };
        entries.push_back(entry);
        writeUInt32(stream, 0x04034b50u);
        writeUInt16(stream, 20);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt32(stream, entry.checksum);
        writeUInt32(stream, entry.size);
        writeUInt32(stream, entry.size);
        writeUInt16(stream, static_cast<uint16_t>(name.size()));
        writeUInt16(stream, 0);
        stream.write(name.data(), static_cast<std::streamsize>(name.size()));
        stream.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    }
    const uint32_t directoryOffset = static_cast<uint32_t>(stream.tellp());
    for (const Entry &entry : entries)
    {
        writeUInt32(stream, 0x02014b50u);
        writeUInt16(stream, 20);
        writeUInt16(stream, 20);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt32(stream, entry.checksum);
        writeUInt32(stream, entry.size);
        writeUInt32(stream, entry.size);
        writeUInt16(stream, static_cast<uint16_t>(entry.name.size()));
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt32(stream, 0);
        writeUInt32(stream, entry.offset);
        stream.write(entry.name.data(), static_cast<std::streamsize>(entry.name.size()));
    }
    const uint32_t directorySize = static_cast<uint32_t>(stream.tellp()) - directoryOffset;
    writeUInt32(stream, 0x06054b50u);
    writeUInt16(stream, 0);
    writeUInt16(stream, 0);
    writeUInt16(stream, static_cast<uint16_t>(entries.size()));
    writeUInt16(stream, static_cast<uint16_t>(entries.size()));
    writeUInt32(stream, directorySize);
    writeUInt32(stream, directoryOffset);
    writeUInt16(stream, 0);
}
}

TEST_CASE("ModelAnimation evaluates out-of-order hierarchies and quaternion shortest paths")
{
    using namespace OpenYAMM::Engine;
    const std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    ModelPose pose;
    evaluateModelClip(*asset, 0, 0.5f, pose);
    evaluateModelHierarchy(*asset, identityModelMatrix(), pose);

    CHECK(pose.globalMatrices[0][12] == doctest::Approx(1.0f));
    CHECK(pose.globalMatrices[0][0] == doctest::Approx(0.0f).epsilon(0.0001));
    CHECK(pose.globalMatrices[0][1] == doctest::Approx(1.0f).epsilon(0.0001));
}

TEST_CASE("ModelAnimation glTF placement maps Y-up into OpenYAMM Z-up")
{
    using namespace OpenYAMM::Engine;
    const ModelMatrix placement = composeModelTransform(gltfModelPlacement({10.0f, 20.0f, 30.0f}));

    CHECK(placement[4] + placement[12] == doctest::Approx(10.0f));
    CHECK(placement[5] + placement[13] == doctest::Approx(20.0f));
    CHECK(placement[6] + placement[14] == doctest::Approx(31.0f));
    CHECK(placement[8] + placement[12] == doctest::Approx(10.0f));
    CHECK(placement[9] + placement[13] == doctest::Approx(21.0f));
    CHECK(placement[10] + placement[14] == doctest::Approx(30.0f));
    constexpr float HalfPi = 1.5707963267948966192f;
    const ModelMatrix yawed = composeModelTransform(gltfModelPlacement({}, HalfPi, 2.0f));
    CHECK(yawed[0] == doctest::Approx(0.0f).epsilon(0.0001));
    CHECK(yawed[1] == doctest::Approx(2.0f).epsilon(0.0001));
    CHECK(yawed[6] == doctest::Approx(2.0f).epsilon(0.0001));
    CHECK(yawed[8] == doctest::Approx(-2.0f).epsilon(0.0001));
}

TEST_CASE("ModelAnimation instances have independent clocks and generation-checked handles")
{
    using namespace OpenYAMM::Engine;
    const std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    ModelInstanceSystem instances;
    const ModelInstanceHandle first = instances.create(asset);
    const ModelInstanceHandle second = instances.create(asset);
    CHECK_FALSE(instances.areNodeMarkersVisible(first));
    CHECK(instances.setNodeMarkersVisible(first, true));
    CHECK(instances.areNodeMarkersVisible(first));
    CHECK_FALSE(instances.areNodeMarkersVisible(second));
    REQUIRE(instances.play(first, "move", ModelPlaybackMode::Loop));
    REQUIRE(instances.play(second, "move", ModelPlaybackMode::Once));
    REQUIRE(instances.setTime(second, 0.5f));

    instances.update(0.25f);
    CHECK(instances.playbackTime(first) == doctest::Approx(0.25f));
    CHECK(instances.playbackTime(second) == doctest::Approx(0.75f));
    REQUIRE(instances.nodeMatrix(first, "child") != nullptr);
    REQUIRE(instances.nodeMatrix(second, "child") != nullptr);
    CHECK((*instances.nodeMatrix(first, "child"))[12] == doctest::Approx(0.5f));
    CHECK((*instances.nodeMatrix(second, "child"))[12] == doctest::Approx(1.5f));

    instances.update(0.5f);
    CHECK_FALSE(instances.isPlaying(second));
    CHECK((*instances.nodeMatrix(second, "child"))[12] == doctest::Approx(2.0f));
    REQUIRE(instances.destroy(first));
    CHECK_FALSE(instances.contains(first));
    const ModelInstanceHandle replacement = instances.create(asset);
    CHECK_EQ(replacement.index, first.index);
    CHECK_NE(replacement.generation, first.generation);
}

TEST_CASE("ModelAnimation loader reads external glTF buffers through AssetFileSystem")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeFile(assetRoot / "engine" / "models" / "fixture.gltf", fixtureGltf());
    writeFile(assetRoot / "engine" / "models" / "fixture.bin", fixtureBuffer());

    {
        AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1));
        ModelAssetCache cache;
        const ModelLoadResult loaded = cache.load(assetFileSystem, "engine/models/fixture.gltf");
        REQUIRE_MESSAGE(loaded, loaded.error.c_str());
        REQUIRE_EQ(loaded.asset->hierarchyOrder.size(), 2);
        CHECK_EQ(loaded.asset->hierarchyOrder[0], 1);
        CHECK_EQ(loaded.asset->hierarchyOrder[1], 0);
        CHECK_EQ(loaded.asset->clips.size(), 2);
        CHECK_EQ(loaded.asset->meshes[0].primitives[0].indices.size(), 6);
        CHECK(loaded.asset->staticBounds.min[0] == doctest::Approx(11.0f));
        CHECK(loaded.asset->staticBounds.max[0] == doctest::Approx(12.0f));

        ModelInstanceSystem instances;
        const ModelInstanceHandle handle = instances.create(loaded.asset);
        REQUIRE(instances.play(handle, "move", ModelPlaybackMode::Once));
        REQUIRE(instances.setTime(handle, 1.0f));
        REQUIRE(instances.bounds(handle) != nullptr);
        CHECK(instances.bounds(handle)->min[0] == doctest::Approx(12.0f));
        CHECK(instances.bounds(handle)->max[0] == doctest::Approx(13.0f));

        const ModelLoadResult cached = cache.load(assetFileSystem, "engine/models/fixture.gltf");
        REQUIRE(cached);
        CHECK_EQ(cached.asset.get(), loaded.asset.get());
        CHECK_EQ(cache.size(), 1);
        cache.clear();
        CHECK_EQ(cache.size(), 0);
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("ModelAnimation loader rejects unsupported interpolation explicitly")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeFile(assetRoot / "engine" / "models" / "fixture.gltf", fixtureGltf("CUBICSPLINE"));
    writeFile(assetRoot / "engine" / "models" / "fixture.bin", fixtureBuffer());

    {
        AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1));
        GltfModelLoader loader;
        const ModelLoadResult loaded = loader.load(assetFileSystem, "engine/models/fixture.gltf");
        CHECK_FALSE(loaded);
        CHECK(loaded.error.find("CUBICSPLINE") != std::string::npos);
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("ModelAnimation material factors retain defaults and reject invalid roughness")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    std::string json = fixtureGltf();
    writeFile(root / "assets_dev/engine/models/fixture.bin", fixtureBuffer());
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    const ModelLoadResult defaults = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    REQUIRE_MESSAGE(defaults, defaults.error);
    CHECK_EQ(defaults.asset->materials[0].metallic, 1.0f);
    CHECK_EQ(defaults.asset->materials[0].roughness, 1.0f);
    const size_t offset = json.find("\"baseColorFactor\"");
    REQUIRE_NE(offset, std::string::npos);
    json.insert(offset, "\"roughnessFactor\": -0.1, ");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    const ModelLoadResult invalid = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(invalid);
    CHECK(invalid.error.find("invalid colour or surface factors") != std::string::npos);
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("ModelAnimation loader reads GLB and packaged external buffers")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path developmentAssets = temporaryRoot / "assets_dev";
    writeFile(developmentAssets / "engine" / "models" / "fixture.glb", fixtureGlb());
    {
        AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, developmentAssets, AssetScaleTier::X1));
        const ModelLoadResult loaded = GltfModelLoader().load(assetFileSystem, "engine/models/fixture.glb");
        REQUIRE_MESSAGE(loaded, loaded.error.c_str());
        CHECK_EQ(loaded.asset->clips.size(), 2);
        CHECK_EQ(loaded.asset->meshes.size(), 1);
    }

    const std::filesystem::path packagedAssets = temporaryRoot / "assets";
    const std::string gltf = fixtureGltf();
    writeZipFile(
        packagedAssets / "engine.zip",
        {
            {"models/fixture.gltf", std::vector<uint8_t>(gltf.begin(), gltf.end())},
            {"models/fixture.bin", fixtureBuffer()},
        });
    {
        AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, packagedAssets, AssetScaleTier::X1));
        const ModelLoadResult loaded = GltfModelLoader().load(assetFileSystem, "engine/models/fixture.gltf");
        INFO(loaded.error);
        REQUIRE(loaded);
        CHECK_EQ(loaded.asset->hierarchyOrder.size(), 2);
        CHECK_EQ(loaded.asset->clips.size(), 2);
        CHECK_FALSE(assetFileSystem.resolvePhysicalPath("engine/models/fixture.bin").has_value());
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("ModelAnimation checked-in fixture covers rendering and animation contract")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));

    const ModelLoadResult loaded = GltfModelLoader().load(
        assetFileSystem,
        "engine/models/fixtures/shared_model_fixture.glb");
    INFO(loaded.error);
    REQUIRE(loaded);
    REQUIRE_EQ(loaded.asset->nodes.size(), 3);
    REQUIRE_EQ(loaded.asset->hierarchyOrder.size(), 3);
    CHECK_EQ(loaded.asset->hierarchyOrder[0], 2);
    CHECK_EQ(loaded.asset->hierarchyOrder[1], 0);
    CHECK_EQ(loaded.asset->hierarchyOrder[2], 1);
    CHECK_EQ(loaded.asset->nodes[2].matrix[12], doctest::Approx(0.25f));
    REQUIRE_EQ(loaded.asset->meshes.size(), 1);
    CHECK_EQ(loaded.asset->meshes[0].primitives.size(), 2);
    REQUIRE_EQ(loaded.asset->materials.size(), 2);
    CHECK_EQ(loaded.asset->materials[0].alphaMode, ModelAlphaMode::Opaque);
    CHECK_EQ(loaded.asset->materials[1].alphaMode, ModelAlphaMode::Blend);
    CHECK(loaded.asset->materials[1].doubleSided);
    CHECK(loaded.asset->materials[1].unlit);
    REQUIRE_EQ(loaded.asset->images.size(), 1);
    CHECK_EQ(loaded.asset->clips.size(), 2);
    CHECK(loaded.asset->findNode("animated_attachment").has_value());

    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(loaded.asset);
    REQUIRE(instances.play(handle, "bob_spin", ModelPlaybackMode::Loop));
    const ModelMatrix *pInitial = instances.nodeMatrix(handle, "animated_attachment");
    REQUIRE(pInitial != nullptr);
    const float initialY = (*pInitial)[13];
    instances.update(1.0f);
    const ModelMatrix *pAnimated = instances.nodeMatrix(handle, "animated_attachment");
    REQUIRE(pAnimated != nullptr);
    CHECK((*pAnimated)[13] > initialY);

    const ModelLoadResult masked = GltfModelLoader().load(
        assetFileSystem, "engine/models/fixtures/masked_emissive_fixture.glb");
    INFO(masked.error);
    REQUIRE(masked);
    REQUIRE_EQ(masked.asset->materials.size(), 2);
    CHECK_EQ(masked.asset->materials[0].alphaMode, ModelAlphaMode::Mask);
    CHECK_EQ(masked.asset->materials[0].alphaCutoff, 0.75f);
    CHECK_EQ(masked.asset->materials[0].emissive[0], 0.2f);
    CHECK_EQ(masked.asset->materials[0].metallic, 0.0f);
    CHECK_EQ(masked.asset->materials[0].roughness, 0.25f);
    CHECK(masked.asset->materials[1].unlit);
}

TEST_CASE("ModelAnimation skinning applies inverse bind, all influences, morphs and root placement")
{
    using namespace OpenYAMM::Engine;
    std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    asset->nodes[0].meshIndex = 0;
    asset->nodes[0].skinIndex = 0;
    asset->nodes[0].weights = {0};
    ModelSkin skin;
    skin.joints = {1, 0};
    skin.inverseBindMatrices = {identityModelMatrix(), identityModelMatrix()};
    skin.inverseBindMatrices[1][12] = -1;
    asset->skins.push_back(skin);
    ModelPrimitive primitive;
    primitive.vertices = {{{1, 0, 0}, {0, 1, 0}, {0, 0}}};
    ModelVertexInfluences influences;
    influences.joints = {0, 0, 0, 0, 1, 1, 1, 1};
    influences.weights = {0.125f, 0.125f, 0.125f, 0.125f, 0.125f, 0.125f, 0.125f, 0.125f};
    primitive.influences.push_back(influences);
    primitive.morphTargets.push_back({{{2, 0, 0}}, {}});
    ModelMesh mesh;
    mesh.primitives.push_back(primitive);
    asset->meshes.push_back(mesh);
    ModelAnimationChannel weights;
    weights.nodeIndex = 0;
    weights.target = ModelAnimationTarget::Weights;
    weights.times = {0, 1};
    weights.weightValues = {{0}, {1}};
    // Move the joint, keeping its rotation fixed so the weighted translation is independently measurable.
    asset->clips[0].channels = {asset->clips[0].channels[0], weights};
    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(asset);
    ModelTransform transform;
    transform.translation = {10, 20, 30};
    REQUIRE(instances.sample(handle, 0, 0.5f, transform));
    CHECK(instances.bounds(handle)->min[0] == doctest::Approx(12));
    const ModelVertex &vertex = instances.pose(handle)->deformedVertices[0][0][0];
    CHECK(vertex.position[0] == doctest::Approx(12));
    CHECK(vertex.position[1] == doctest::Approx(20));
    CHECK(vertex.normal[1] == doctest::Approx(1));
    CHECK(instances.bounds(handle)->min[0] == doctest::Approx(12));
    REQUIRE(instances.sample(handle, 0, 1, transform));
    CHECK(instances.pose(handle)->deformedVertices[0][0][0].position[0] == doctest::Approx(13.5));
    weights.interpolation = ModelAnimationInterpolation::Step;
    asset->clips[0].channels[1] = weights;
    REQUIRE(instances.sample(handle, 0, 1, transform));
    CHECK(instances.pose(handle)->morphWeights[0][0] == doctest::Approx(1));
    asset->clips[0].channels[1].weightValues = {{-2}, {1}};
    REQUIRE(instances.sample(handle, 0, 0, transform));
    const ModelBounds conservative = *instances.cullingBounds(handle);
    const ModelBounds exact = *instances.bounds(handle);
    CHECK(conservative.min[0] <= exact.min[0]);
    CHECK(conservative.max[0] >= exact.max[0]);
}

TEST_CASE("ModelAnimation MM6 demon loads all native clips and resets death visibility")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm6/models/mm6_demon.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    REQUIRE_EQ(loaded.asset->skins.size(), 1);
    CHECK_EQ(loaded.asset->skins[0].joints.size(), 85);
    CHECK_EQ(loaded.asset->clips.size(), 10);
    for (const ModelMaterial &material : loaded.asset->materials)
    {
        if (material.name == "Demon_Meshy_Body")
        {
            CHECK_EQ(material.metallic, 0.0f);
            CHECK_EQ(material.metallicRoughnessImageIndex, 2);
            CHECK_EQ(material.baseSampler.minFilter, 9987);
            CHECK_EQ(material.baseSampler.wrapS, 10497);
        }
        else if (material.name == "Demon_Red_Iris")
        {
            CHECK_EQ(material.metallic, 0.0f);
            CHECK(material.roughness == doctest::Approx(0.22f));
        }
    }
    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(loaded.asset);
    const uint32_t body = *loaded.asset->findNode("Demon_Native_Mesh");
    const uint32_t ash = *loaded.asset->findNode("Demon_Ash_Remains");
    const uint32_t plume = *loaded.asset->findNode("Demon_Death_Plume");
    // The portable authoring effect is replaced by batched runtime particles.
    CHECK_EQ(loaded.asset->nodes[plume].meshIndex, -1);
    CHECK(loaded.asset->nodes[plume].weights.empty());
    for (const ModelMesh &mesh : loaded.asset->meshes)
    {
        for (const ModelPrimitive &primitive : mesh.primitives)
        {
            CHECK(primitive.morphTargets.empty());
        }
    }
    const std::array<std::pair<const char *, float>, 7> nativeClips = {{{"Standing", .125f}, {"Walk_Native", 1.125f},
        {"Attack", .75f}, {"Hit", .75f}, {"Fidget", .625f}, {"Death", 1.25f}, {"Cast_FireBolt", 1.0f}}};
    for (const auto &[name, duration] : nativeClips)
    {
        const uint32_t clip = *loaded.asset->findClip(name);
        CHECK(loaded.asset->clips[clip].durationSeconds == doctest::Approx(duration));
        REQUIRE(instances.sample(handle, clip, duration * .5f, gltfModelPlacement({1, 2, 3}, 0, 100)));
        // After 375 ms the body is hidden; runtime particles do not contribute to pick bounds.
        CHECK(instances.bounds(handle)->valid == (std::string(name) != "Death"));
        for (const auto &node : instances.pose(handle)->deformedVertices)
        {
            for (const auto &primitive : node)
            {
                for (const ModelVertex &vertex : primitive)
                {
                    if (!std::isfinite(vertex.position[0]) || !std::isfinite(vertex.position[1])
                        || !std::isfinite(vertex.position[2]))
                    {
                        FAIL("Non-finite deformed vertex");
                    }
                }
            }
        }
    }
    REQUIRE(instances.sample(handle, *loaded.asset->findClip("Ash_Remains"), 0, {}));
    CHECK_FALSE(modelMatrixVisible(*instances.nodeMatrix(handle, body)));
    CHECK(modelMatrixVisible(*instances.nodeMatrix(handle, ash)));
    REQUIRE(instances.sample(handle, *loaded.asset->findClip("Standing"), 0, {}));
    CHECK(modelMatrixVisible(*instances.nodeMatrix(handle, body)));
    CHECK_FALSE(modelMatrixVisible(*instances.nodeMatrix(handle, ash)));
    for (float weight : instances.pose(handle)->morphWeights[plume])
    {
        CHECK(weight == 0.0f);
    }
    CHECK(instances.bounds(handle)->max[1] == doctest::Approx(1.707f).epsilon(.01));
    REQUIRE(instances.sample(handle, *loaded.asset->findClip("Cast_FireBolt"), .65f, {}));
    CHECK(modelMatrixVisible(*instances.nodeMatrix(handle, body)));
    CHECK_FALSE(modelMatrixVisible(*instances.nodeMatrix(handle, ash)));
    for (const char *socket : {"Socket_Eye_Left", "Socket_Eye_Right", "Socket_Palm_Left", "Socket_Palm_Right"})
    {
        CHECK(instances.nodeMatrix(handle, socket) != nullptr);
    }
}

TEST_CASE("ModelAnimation defers crowd deformation and bounds contain every demon animation")
{
    using namespace OpenYAMM::Engine;
    AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm6/models/mm6_demon.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    ModelInstanceSystem instances;
    const ModelInstanceHandle first = instances.create(loaded.asset);
    const ModelInstanceHandle second = instances.create(loaded.asset);
    const ModelPose *pPose = instances.pose(first, false);
    const uint32_t body = *loaded.asset->findNode("Demon_Native_Mesh");
    for (const std::vector<ModelVertex> &primitive : pPose->deformedVertices[body])
    {
        CHECK(primitive.empty());
    }
    uint64_t revision = pPose->deformationRevision;
    for (uint32_t clip = 0; clip < loaded.asset->clips.size(); ++clip)
    {
        for (float fraction : {0.0f, 0.2f, 0.5f, 0.8f, 1.0f})
        {
            ModelTransform placement = gltfModelPlacement({-9728, -11319, 161}, fraction * 6.0f, 104.8623316f);
            placement.scale[0] *= 0.7f;
            placement.scale[2] *= 1.3f;
            const float time = loaded.asset->clips[clip].durationSeconds * fraction;
            REQUIRE(instances.sample(first, clip, time, placement));
            const ModelBounds conservative = *instances.cullingBounds(first);
            const ModelBounds envelope = *instances.motionBounds(first);
            CHECK(pPose->deformationRevision == revision);
            REQUIRE(instances.nodeMatrix(first, 0) != nullptr);
            CHECK(pPose->deformationRevision == revision);
            const ModelBounds exact = *instances.bounds(first);
            CHECK(pPose->deformationRevision == revision);
            CHECK(conservative.valid == exact.valid);
            if (exact.valid)
            {
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    CHECK(conservative.min[axis] <= exact.min[axis] + 0.01f);
                    CHECK(conservative.max[axis] >= exact.max[axis] - 0.01f);
                    CHECK(envelope.min[axis] <= exact.min[axis] + 0.01f);
                    CHECK(envelope.max[axis] >= exact.max[axis] - 0.01f);
                }
            }
            REQUIRE(instances.sample(first, clip, time, placement));
            CHECK(instances.bounds(first)->min == exact.min);
            CHECK(instances.pose(first)->deformationRevision == revision + 1);
            revision = pPose->deformationRevision;
            const ModelBounds cpuVertices = *instances.bounds(first);
            CHECK(cpuVertices.valid == exact.valid);
            for (size_t axis = 0; axis < 3; ++axis)
            {
                CHECK(cpuVertices.min[axis] == doctest::Approx(exact.min[axis]));
                CHECK(cpuVertices.max[axis] == doctest::Approx(exact.max[axis]));
            }
        }
    }
    // A second instance has its own pose and does not inherit the first actor's deformation.
    CHECK(instances.pose(second)->deformationRevision == 1);
    REQUIRE(instances.destroy(first));
    const ModelInstanceHandle reused = instances.create(loaded.asset);
    CHECK(reused.index == first.index);
    CHECK(reused.generation != first.generation);
    CHECK(instances.pose(reused)->deformationRevision == 1);
}

TEST_CASE("ModelAnimation demon LOD meshes share the rig and retain posed bounds across all clips")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm6/models/mm6_demon.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    const ModelAsset &asset = *loaded.asset;
    const uint32_t nodeIndex = *asset.findNode("Demon_Native_Mesh");
    const ModelMesh &mesh = asset.meshes[asset.nodes[nodeIndex].meshIndex];
    REQUIRE(mesh.lodMeshes.size() == 3);
    REQUIRE(mesh.shadowMeshes.size() == 4);
    const std::array<size_t, 4> triangles = {16474, 8237, 2980, 1019};
    for (size_t level = 0; level < 4; ++level)
    {
        const uint32_t meshIndex = level == 0 ? uint32_t(asset.nodes[nodeIndex].meshIndex) : mesh.lodMeshes[level - 1];
        size_t indices = 0;
        for (const ModelPrimitive &primitive : asset.meshes[meshIndex].primitives)
        {
            indices += primitive.indices.size();
            CHECK(primitive.influences.size() == primitive.vertices.size());
        }
        CHECK(indices / 3 == triangles[level]);
        const ModelMesh &shadow = asset.meshes[mesh.shadowMeshes[level]];
        REQUIRE(shadow.primitives.size() == 1);
        CHECK(shadow.primitives[0].indices.size() == indices);
        ModelAsset lower = asset;
        lower.nodes[nodeIndex].meshIndex = int(meshIndex);
        for (uint32_t clip = 0; clip < asset.clips.size(); ++clip)
        {
            for (int sample = 0; sample < 5; ++sample)
            {
                ModelPose pose;
                evaluateModelClip(asset, clip, asset.clips[clip].durationSeconds * sample / 4.0f, pose);
                evaluateModelHierarchy(asset, identityModelMatrix(), pose);
                const ModelBounds reference = modelExactPoseBounds(asset, pose);
                const ModelBounds actual = modelExactPoseBounds(lower, pose);
                CHECK(actual.valid == reference.valid);
                if (actual.valid)
                {
                    for (size_t axis = 0; axis < 3; ++axis)
                    {
                        // Detect changed bind spaces, bad joint remapping and exploded decimated weights.
                        CHECK(std::abs(reference.min[axis] - actual.min[axis]) < 0.15f);
                        CHECK(std::abs(reference.max[axis] - actual.max[axis]) < 0.15f);
                    }
                }
            }
        }
    }
}

TEST_CASE("ModelAnimation loader rejects self-referencing LOD metadata")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    std::string json = fixtureGltf();
    const size_t position = json.find("\"primitives\"");
    REQUIRE(position != std::string::npos);
    json.insert(position, "\"extras\":{\"openyamm_lods\":[0]},");
    writeFile(root / "assets_dev/engine/models/fixture.bin", fixtureBuffer());
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(loaded);
    CHECK(loaded.error.find("LOD reference") != std::string::npos);
    assets.shutdown();
    std::filesystem::remove_all(root);
}
