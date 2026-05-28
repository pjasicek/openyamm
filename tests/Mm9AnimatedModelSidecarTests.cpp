#include "doctest/doctest.h"

#include "game/mm9/Mm9AnimatedModelSidecar.h"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <string>

namespace
{
std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_mm9_model_sidecar_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

OpenYAMM::Game::AnimatedModelAsset makeMergeTargetAsset()
{
    OpenYAMM::Game::AnimatedModelAsset asset = {};
    asset.nodes.push_back(OpenYAMM::Game::AnimatedModelNode{});
    asset.nodes.push_back(OpenYAMM::Game::AnimatedModelNode{});

    OpenYAMM::Game::AnimatedModelMaterial bodyMaterial = {};
    bodyMaterial.name = "body";
    bodyMaterial.baseColorTextureUri = "placeholder/body.png";
    asset.materials.push_back(bodyMaterial);

    OpenYAMM::Game::AnimatedModelMaterial weaponMaterial = {};
    weaponMaterial.name = "weapon";
    weaponMaterial.baseColorTextureUri = "placeholder/weapon.png";
    asset.materials.push_back(weaponMaterial);

    OpenYAMM::Game::AnimatedModelPrimitive bodyPrimitive = {};
    bodyPrimitive.materialIndex = 0;
    asset.primitives.push_back(bodyPrimitive);

    OpenYAMM::Game::AnimatedModelPrimitive weaponPrimitive = {};
    weaponPrimitive.materialIndex = 1;
    asset.primitives.push_back(weaponPrimitive);

    OpenYAMM::Game::AnimatedModelClip idle = {};
    idle.name = "stand";
    idle.durationSeconds = 1.0f;
    asset.clips.push_back(idle);

    OpenYAMM::Game::AnimatedModelClip attack = {};
    attack.name = "Attack1";
    attack.durationSeconds = 2.0f;
    asset.clips.push_back(attack);
    return asset;
}
}

TEST_CASE("MM9 animated model sidecar parses materials, sockets, animation events, and LOD metadata")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path sidecarPath = temporaryRoot / "models" / "guard.model.yml";
    writeTextFile(
        sidecarPath,
        R"(
schema: openyamm.model3d.v1
id: guard
model: guard.glb
source:
  format: ABC
  path: models\guard.abc
  commandString: GuardCommand
  version: 66
lod:
  exportedIndex: 1
  distances: [128.0, 512.0, 2048.0]
materials:
  - index: 0
    texture: guard_body
    runtime_texture: skins/guard3.dtx
    preview_texture: previews/guard3.png
    alphaMode: MASK
    alphaCutoff: 0.35
    doubleSided: true
  - index: 1
    texture: guard_sword
    runtime_texture: skins/guardsword.dtx
skeleton:
  nodes:
    - index: 0
      name: Scene Root
      parent: null
      flags: 1
      children: [1]
    - index: 1
      name: Bip01 R Hand
      parent: 0
      flags: 3
      children: []
sockets:
  - name: RHand1
    node: 1
    translation: [1.0, 2.0, 3.0]
    rotation: [0.0, 0.0, 0.0, 1.0]
animations:
  - name: stand
    durationMs: 1000
    keyframes: 10
    interpolationTimeMs: 100
    events:
      - timeMs: 250
        event: footstep
      - timeMs: 750
        event: idle_shift
)");

    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9AnimatedModelSidecar> sidecar =
        OpenYAMM::Game::loadMm9AnimatedModelSidecar(sidecarPath, errorMessage);
    REQUIRE_MESSAGE(sidecar.has_value(), errorMessage);
    CHECK(sidecar->schema == "openyamm.model3d.v1");
    CHECK(sidecar->id == "guard");
    CHECK(sidecar->sourceFormat == "ABC");
    CHECK(sidecar->sourcePath == "models\\guard.abc");
    CHECK(sidecar->sourceCommandString == "GuardCommand");
    CHECK(sidecar->sourceVersion == 66);
    CHECK(sidecar->exportedLodIndex == 1);
    REQUIRE(sidecar->lodDistances.size() == 3);
    CHECK(sidecar->lodDistances[2] == doctest::Approx(2048.0f));
    REQUIRE(sidecar->materials.size() == 2);
    CHECK(sidecar->materials[0].index == 0);
    CHECK(sidecar->materials[0].runtimeTexture == "skins/guard3.dtx");
    CHECK(sidecar->materials[0].alphaMask);
    CHECK(sidecar->materials[0].alphaCutoff == doctest::Approx(0.35f));
    CHECK(sidecar->materials[0].doubleSided);
    REQUIRE(sidecar->skeleton.nodes.size() == 2);
    CHECK(sidecar->skeleton.nodes[0].name == "Scene Root");
    CHECK(sidecar->skeleton.nodes[0].parentIndex == -1);
    CHECK(sidecar->skeleton.nodes[0].flags == 1);
    REQUIRE(sidecar->skeleton.nodes[0].childIndices.size() == 1);
    CHECK(sidecar->skeleton.nodes[0].childIndices[0] == 1);
    CHECK(sidecar->skeleton.nodes[1].parentIndex == 0);
    CHECK(sidecar->skeleton.nodes[1].flags == 3);
    REQUIRE(sidecar->sockets.size() == 1);
    CHECK(sidecar->sockets[0].name == "RHand1");
    CHECK(sidecar->sockets[0].nodeIndex == 1);
    CHECK(sidecar->sockets[0].localTransform.translation.z == doctest::Approx(3.0f));
    REQUIRE(sidecar->animations.size() == 1);
    REQUIRE(sidecar->animations[0].events.size() == 2);
    CHECK(sidecar->animations[0].events[1].timeMs == 750);
    CHECK(sidecar->animations[0].events[1].event == "idle_shift");

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("MM9 animated model sidecar merge applies materials, sockets, events, and diagnostics")
{
    OpenYAMM::Game::Mm9AnimatedModelSidecar sidecar = {};
    sidecar.exportedLodIndex = 0;
    sidecar.lodDistances = {128.0f, 256.0f};

    OpenYAMM::Game::Mm9AnimatedModelMaterialRef material0 = {};
    material0.index = 0;
    material0.runtimeTexture = "skins/guard3.dtx";
    material0.alphaMask = true;
    material0.alphaCutoff = 0.25f;
    material0.doubleSided = true;
    sidecar.materials.push_back(material0);

    OpenYAMM::Game::Mm9AnimatedModelMaterialRef invalidMaterial = {};
    invalidMaterial.index = 7;
    invalidMaterial.runtimeTexture = "skins/missing.dtx";
    sidecar.materials.push_back(invalidMaterial);

    OpenYAMM::Game::Mm9AnimatedModelSkeletonNode validSkeletonNode = {};
    validSkeletonNode.index = 0;
    validSkeletonNode.name = "Scene Root";
    validSkeletonNode.parentIndex = -1;
    validSkeletonNode.flags = 1;
    validSkeletonNode.childIndices = {1};
    sidecar.skeleton.nodes.push_back(validSkeletonNode);

    OpenYAMM::Game::Mm9AnimatedModelSkeletonNode invalidSkeletonNode = {};
    invalidSkeletonNode.index = 8;
    invalidSkeletonNode.name = "Broken Bone";
    invalidSkeletonNode.parentIndex = 9;
    invalidSkeletonNode.childIndices = {10};
    sidecar.skeleton.nodes.push_back(invalidSkeletonNode);

    OpenYAMM::Game::AnimatedModelSocket validSocket = {};
    validSocket.name = "RHand1";
    validSocket.nodeIndex = 1;
    sidecar.sockets.push_back(validSocket);

    OpenYAMM::Game::AnimatedModelSocket invalidSocket = {};
    invalidSocket.name = "MissingSocket";
    invalidSocket.nodeIndex = 99;
    sidecar.sockets.push_back(invalidSocket);

    OpenYAMM::Game::Mm9AnimatedModelAnimationInfo standAnimation = {};
    standAnimation.name = "STAND";
    standAnimation.events.push_back(OpenYAMM::Game::Mm9AnimatedModelAnimationEvent{125, "footstep"});
    sidecar.animations.push_back(standAnimation);

    OpenYAMM::Game::AnimatedModelAsset asset = makeMergeTargetAsset();
    OpenYAMM::Game::mergeMm9AnimatedModelSidecar(sidecar, asset);

    CHECK(asset.lod.valid);
    CHECK(asset.lod.distances.size() == 2);
    REQUIRE(asset.materials.size() == 2);
    CHECK(asset.materials[0].baseColorTextureUri == "skins/guard3.dtx");
    CHECK(asset.materials[0].alphaMask);
    CHECK(asset.materials[0].alphaCutoff == doctest::Approx(0.25f));
    CHECK(asset.materials[0].doubleSided);
    REQUIRE(asset.sockets.size() == 2);
    CHECK(asset.sockets[0].name == "RHand1");
    REQUIRE(asset.clips.size() == 2);
    REQUIRE(asset.clips[0].events.size() == 1);
    CHECK(asset.clips[0].events[0].timeSeconds == doctest::Approx(0.125f));
    CHECK(asset.clips[0].events[0].key == "footstep");

    bool foundInvalidSocket = false;
    bool foundInvalidMaterial = false;
    bool foundMissingMaterialEntry = false;
    bool foundInvalidSkeletonNode = false;
    bool foundInvalidSkeletonParent = false;
    bool foundInvalidSkeletonChild = false;
    for (const OpenYAMM::Game::AnimatedModelDiagnostic &diagnostic : asset.diagnostics)
    {
        foundInvalidSocket = foundInvalidSocket
            || diagnostic.message.find("MissingSocket") != std::string::npos;
        foundInvalidMaterial = foundInvalidMaterial
            || diagnostic.message.find("material index") != std::string::npos;
        foundMissingMaterialEntry = foundMissingMaterialEntry
            || diagnostic.message.find("no MM9 sidecar material entry") != std::string::npos;
        foundInvalidSkeletonNode = foundInvalidSkeletonNode
            || diagnostic.message.find("invalid node index") != std::string::npos;
        foundInvalidSkeletonParent = foundInvalidSkeletonParent
            || diagnostic.message.find("invalid parent node") != std::string::npos;
        foundInvalidSkeletonChild = foundInvalidSkeletonChild
            || diagnostic.message.find("invalid child node") != std::string::npos;
    }

    CHECK(foundInvalidSocket);
    CHECK(foundInvalidMaterial);
    CHECK(foundMissingMaterialEntry);
    CHECK(foundInvalidSkeletonNode);
    CHECK(foundInvalidSkeletonParent);
    CHECK(foundInvalidSkeletonChild);
}
