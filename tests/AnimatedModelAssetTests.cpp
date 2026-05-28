#include "doctest/doctest.h"

#include "game/mm9/Mm9AnimatedModelSidecar.h"
#include "game/render/AnimatedModelAsset.h"

#include <cstdint>
#include <cmath>
#include <filesystem>
#include <limits>
#include <optional>
#include <string>
#include <vector>

namespace
{
std::filesystem::path sourceRoot()
{
    return std::filesystem::path(OPENYAMM_SOURCE_DIR);
}

bool mm9ModelAssetsAvailable()
{
    return std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/banshee.glb")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/banshee.model.yml")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/bigfoot.glb")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/bigfoot.model.yml")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/dragon.glb")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/dragon.model.yml")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/guard.glb")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/guard.model.yml")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/props/barrel.glb")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/props/barrel.model.yml")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/spells/firebolt.glb")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/spells/firebolt.model.yml")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/projectiles/magicarrow.glb")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/projectiles/magicarrow.model.yml");
}

OpenYAMM::Game::AnimatedModelAsset loadMm9Model(const std::string &name)
{
    const std::filesystem::path modelRoot = sourceRoot() / "assets_dev/worlds/mm9/models";
    std::string errorMessage;
    std::optional<OpenYAMM::Game::AnimatedModelAsset> asset =
        OpenYAMM::Game::loadAnimatedModelAsset(modelRoot / (name + ".glb"), errorMessage);
    REQUIRE_MESSAGE(asset.has_value(), errorMessage.c_str());

    std::optional<OpenYAMM::Game::Mm9AnimatedModelSidecar> sidecar =
        OpenYAMM::Game::loadMm9AnimatedModelSidecar(modelRoot / (name + ".model.yml"), errorMessage);
    REQUIRE_MESSAGE(sidecar.has_value(), errorMessage.c_str());

    OpenYAMM::Game::mergeMm9AnimatedModelSidecar(*sidecar, *asset);
    return *asset;
}

void requireFinitePose(const OpenYAMM::Game::AnimatedModelPose &pose)
{
    for (const OpenYAMM::Game::AnimatedModelMat4 &matrix : pose.globalTransforms)
    {
        CHECK(OpenYAMM::Game::animatedModelMatrixIsFinite(matrix));
    }
    for (const OpenYAMM::Game::AnimatedModelMat4 &matrix : pose.skinningMatrices)
    {
        CHECK(OpenYAMM::Game::animatedModelMatrixIsFinite(matrix));
    }
}

bool finiteVec3(const OpenYAMM::Game::AnimatedModelVec3 &value)
{
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

void requireLoopEndpointMatchesStart(
    const OpenYAMM::Game::AnimatedModelAsset &asset,
    const OpenYAMM::Game::AnimatedModelClip &clip)
{
    const OpenYAMM::Game::AnimatedModelPose startPose =
        OpenYAMM::Game::sampleAnimatedModelPose(asset, &clip, 0.0f, true);
    const OpenYAMM::Game::AnimatedModelPose endpointPose =
        OpenYAMM::Game::sampleAnimatedModelPose(asset, &clip, clip.durationSeconds, true);

    REQUIRE(startPose.globalTransforms.size() == endpointPose.globalTransforms.size());
    for (size_t matrixIndex = 0; matrixIndex < startPose.globalTransforms.size(); ++matrixIndex)
    {
        for (size_t valueIndex = 0; valueIndex < startPose.globalTransforms[matrixIndex].values.size(); ++valueIndex)
        {
            CHECK(
                endpointPose.globalTransforms[matrixIndex].values[valueIndex]
                == doctest::Approx(startPose.globalTransforms[matrixIndex].values[valueIndex]).epsilon(0.0001));
        }
    }
}

void requireClipSamplesAreFinite(
    const OpenYAMM::Game::AnimatedModelAsset &asset,
    const std::string &clipName)
{
    const OpenYAMM::Game::AnimatedModelClip *pClip = asset.findClip(clipName);
    REQUIRE_MESSAGE(pClip != nullptr, clipName.c_str());
    REQUIRE(pClip->durationSeconds > 0.0f);

    const float sampleTimes[] = {
        0.0f,
        pClip->durationSeconds * 0.5f,
        pClip->durationSeconds};
    for (const float sampleTime : sampleTimes)
    {
        const OpenYAMM::Game::AnimatedModelPose pose =
            OpenYAMM::Game::sampleAnimatedModelPose(asset, pClip, sampleTime, true);
        CHECK(pose.globalTransforms.size() == asset.nodes.size());
        CHECK(pose.skinningMatrices.size() == asset.skins.front().joints.size());
        requireFinitePose(pose);
    }

    requireLoopEndpointMatchesStart(asset, *pClip);
}

void requireSocketIsFiniteWhenPresent(
    const OpenYAMM::Game::AnimatedModelAsset &asset,
    const OpenYAMM::Game::AnimatedModelPose &pose,
    const std::string &socketName)
{
    if (!asset.findSocketIndex(socketName).has_value())
    {
        return;
    }

    const std::optional<OpenYAMM::Game::AnimatedModelMat4> transform =
        OpenYAMM::Game::animatedModelSocketTransform(asset, pose, socketName);
    REQUIRE_MESSAGE(transform.has_value(), socketName.c_str());
    CHECK(OpenYAMM::Game::animatedModelMatrixIsFinite(*transform));
}
}

TEST_CASE("animated model loader validates representative MM9 GLB and sidecar metadata")
{
    if (!mm9ModelAssetsAvailable())
    {
        WARN("MM9 model assets are not present; skipping real asset validation");
        return;
    }

    const OpenYAMM::Game::AnimatedModelAsset asset = loadMm9Model("banshee");

    CHECK_FALSE(asset.hasErrors());
    CHECK(asset.sourceId == "banshee");
    CHECK(asset.sourcePath.filename() == "banshee.glb");
    CHECK(asset.nodes.size() == 141);
    CHECK(asset.primitives.size() == 6);
    CHECK(asset.materials.size() == 1);
    CHECK(asset.skins.size() == 1);
    CHECK(asset.clips.size() == 17);
    CHECK(asset.sockets.size() == 3);
    REQUIRE(asset.lod.valid);
    CHECK(asset.lod.exportedIndex == 0);
    REQUIRE(asset.lod.distances.size() == 4);
    CHECK(asset.lod.distances[0] == doctest::Approx(614.4f));
    CHECK(asset.lod.distances[1] == doctest::Approx(896.0f));
    CHECK(asset.lod.distances[2] == doctest::Approx(2048.0f));
    CHECK(asset.lod.distances[3] > 1.0e20f);
    REQUIRE(asset.bounds.valid);
    CHECK(finiteVec3(asset.bounds.min));
    CHECK(finiteVec3(asset.bounds.max));
    CHECK(asset.bounds.min.x < asset.bounds.max.x);
    CHECK(asset.bounds.min.y < asset.bounds.max.y);
    CHECK(asset.bounds.min.z < asset.bounds.max.z);
    size_t vertexCount = 0;
    size_t indexCount = 0;
    for (const OpenYAMM::Game::AnimatedModelPrimitive &primitive : asset.primitives)
    {
        REQUIRE(primitive.bounds.valid);
        CHECK(finiteVec3(primitive.bounds.min));
        CHECK(finiteVec3(primitive.bounds.max));
        CHECK(primitive.vertexCount == primitive.vertices.size());
        CHECK(primitive.indexCount == primitive.indices.size());
        CHECK_FALSE(primitive.vertices.empty());
        CHECK_FALSE(primitive.indices.empty());
        vertexCount += primitive.vertices.size();
        indexCount += primitive.indices.size();
        for (const uint32_t index : primitive.indices)
        {
            CHECK(index < primitive.vertices.size());
        }
        for (const OpenYAMM::Game::AnimatedModelVertex &vertex : primitive.vertices)
        {
            for (size_t jointIndex = 0; jointIndex < vertex.joints.size(); ++jointIndex)
            {
                if (vertex.weights[jointIndex] > 0.0f)
                {
                    CHECK(vertex.joints[jointIndex] < asset.skins.front().joints.size());
                }
            }
        }
    }
    CHECK(vertexCount > 0);
    CHECK(indexCount > 0);
    CHECK(asset.findClip("fly") != nullptr);
    CHECK(asset.findClip("HattackAir1") != nullptr);
    CHECK(asset.findSocketIndex("RangeAttack").has_value());
    CHECK(asset.materials.front().baseColorTextureUri == "skins/bansheea.dtx");
    CHECK(asset.materials.front().alphaMask);
}

TEST_CASE("animated model pose sampler produces finite matrices for MM9 actor clips")
{
    if (!mm9ModelAssetsAvailable())
    {
        WARN("MM9 model assets are not present; skipping real asset animation sampling");
        return;
    }

    const OpenYAMM::Game::AnimatedModelAsset banshee = loadMm9Model("banshee");
    const OpenYAMM::Game::AnimatedModelClip *pFly = banshee.findClip("Fly");
    REQUIRE(pFly != nullptr);
    const OpenYAMM::Game::AnimatedModelPose bansheePose =
        OpenYAMM::Game::sampleAnimatedModelPose(banshee, pFly, 0.5f, true);
    CHECK(bansheePose.globalTransforms.size() == banshee.nodes.size());
    CHECK(bansheePose.skinningMatrices.size() == banshee.skins.front().joints.size());
    requireFinitePose(bansheePose);

    const std::optional<OpenYAMM::Game::AnimatedModelMat4> rangeAttackTransform =
        OpenYAMM::Game::animatedModelSocketTransform(banshee, bansheePose, "RangeAttack");
    REQUIRE(rangeAttackTransform.has_value());
    CHECK(OpenYAMM::Game::animatedModelMatrixIsFinite(*rangeAttackTransform));

    const OpenYAMM::Game::AnimatedModelAsset bigfoot = loadMm9Model("bigfoot");
    const OpenYAMM::Game::AnimatedModelClip *pRun = bigfoot.findClip("run");
    REQUIRE(pRun != nullptr);
    const OpenYAMM::Game::AnimatedModelPose bigfootPose =
        OpenYAMM::Game::sampleAnimatedModelPose(bigfoot, pRun, 0.75f, true);
    CHECK(bigfootPose.globalTransforms.size() == bigfoot.nodes.size());
    CHECK(bigfootPose.skinningMatrices.size() == bigfoot.skins.front().joints.size());
    requireFinitePose(bigfootPose);
    CHECK(OpenYAMM::Game::animatedModelSocketTransform(bigfoot, bigfootPose, "RHand1").has_value());
}

TEST_CASE("animated model sampler validates representative MM9 actor clip and socket acceptance cases")
{
    if (!mm9ModelAssetsAvailable())
    {
        WARN("MM9 model assets are not present; skipping representative animation acceptance validation");
        return;
    }

    struct ModelScenario
    {
        std::string modelName;
        std::vector<std::string> clipNames;
    };

    const std::vector<ModelScenario> scenarios = {
        {"banshee", {"standAir", "Fly", "HattackAir1"}},
        {"bigfoot", {"stand", "walk", "run", "Rattack1"}},
        {"dragon", {"fly", "stand", "rAttack1"}},
        {"guard", {"stand", "walk", "run", "Hattack1"}},
        {"props/barrel", {"Static_Model"}},
        {"spells/firebolt", {"STATIC_MODEL"}},
        {"projectiles/magicarrow", {"STATIC_MODEL"}},
    };

    for (const ModelScenario &scenario : scenarios)
    {
        CAPTURE(scenario.modelName);
        const OpenYAMM::Game::AnimatedModelAsset asset = loadMm9Model(scenario.modelName);
        CHECK_FALSE(asset.hasErrors());

        for (const std::string &clipName : scenario.clipNames)
        {
            CAPTURE(clipName);
            requireClipSamplesAreFinite(asset, clipName);
        }

        const OpenYAMM::Game::AnimatedModelClip *pFirstClip = asset.findClip(scenario.clipNames.front());
        REQUIRE(pFirstClip != nullptr);
        const OpenYAMM::Game::AnimatedModelPose pose =
            OpenYAMM::Game::sampleAnimatedModelPose(asset, pFirstClip, pFirstClip->durationSeconds * 0.5f, true);
        requireSocketIsFiniteWhenPresent(asset, pose, "RangeAttack");
        requireSocketIsFiniteWhenPresent(asset, pose, "LHand1");
        requireSocketIsFiniteWhenPresent(asset, pose, "RHand1");
        requireSocketIsFiniteWhenPresent(asset, pose, "Jaw");
    }
}

TEST_CASE("animated model render prep creates skinned draw items for MM9 actor meshes")
{
    if (!mm9ModelAssetsAvailable())
    {
        WARN("MM9 model assets are not present; skipping real asset render prep validation");
        return;
    }

    struct RenderPrepScenario
    {
        std::string modelName;
        std::string clipName;
        std::string firstTexture;
    };

    const std::vector<RenderPrepScenario> scenarios = {
        {"bigfoot", "run", "skins/bigfoot1.dtx"},
        {"guard", "stand", "skins/guard1.dtx"},
        {"props/barrel", "Static_Model", "skins/props/barrel.dtx"},
        {"projectiles/magicarrow", "STATIC_MODEL", "skins/projectiles/magicarrow.dtx"},
    };

    for (const RenderPrepScenario &scenario : scenarios)
    {
        CAPTURE(scenario.modelName);
        CAPTURE(scenario.clipName);
        const OpenYAMM::Game::AnimatedModelAsset asset = loadMm9Model(scenario.modelName);
        const OpenYAMM::Game::AnimatedModelClip *pClip = asset.findClip(scenario.clipName);
        REQUIRE(pClip != nullptr);
        const OpenYAMM::Game::AnimatedModelPose pose =
            OpenYAMM::Game::sampleAnimatedModelPose(asset, pClip, pClip->durationSeconds * 0.5f, true);

        const OpenYAMM::Game::AnimatedModelRenderPrep renderPrep =
            OpenYAMM::Game::buildAnimatedModelRenderPrep(asset, pose, 128);
        CHECK(renderPrep.diagnostics.empty());
        REQUIRE(renderPrep.drawItems.size() == asset.primitives.size());
        CHECK(renderPrep.counters.skinnedDrawCalls == renderPrep.drawItems.size());
        CHECK(renderPrep.counters.uploadedBoneMatrices > 0);

        const OpenYAMM::Game::AnimatedModelDrawItem &drawItem = renderPrep.drawItems.front();
        CHECK(drawItem.vertices.size() == asset.primitives.front().vertices.size());
        CHECK(drawItem.indices.size() == asset.primitives.front().indices.size());
        CHECK(drawItem.bonePalette.size() <= 128);
        CHECK(drawItem.texture == scenario.firstTexture);
        CHECK(drawItem.bounds.valid);

        for (const OpenYAMM::Game::AnimatedModelVertex &vertex : drawItem.vertices)
        {
            for (size_t slot = 0; slot < vertex.joints.size(); ++slot)
            {
                if (vertex.weights[slot] > 0.0f)
                {
                    CHECK(vertex.joints[slot] < drawItem.bonePalette.size());
                }
            }
        }
    }
}

TEST_CASE("animated model render prep remaps primitive joints and rejects palette overflow")
{
    OpenYAMM::Game::AnimatedModelAsset asset = {};
    asset.materials.push_back(OpenYAMM::Game::AnimatedModelMaterial{});
    OpenYAMM::Game::AnimatedModelPrimitive primitive = {};
    primitive.materialIndex = 0;
    primitive.vertexCount = 3;
    primitive.indexCount = 3;
    primitive.indices = {0, 1, 2};

    OpenYAMM::Game::AnimatedModelVertex first = {};
    first.joints = {5, 0, 0, 0};
    first.weights = {1.0f, 0.0f, 0.0f, 0.0f};
    OpenYAMM::Game::AnimatedModelVertex second = {};
    second.joints = {9, 0, 0, 0};
    second.weights = {1.0f, 0.0f, 0.0f, 0.0f};
    OpenYAMM::Game::AnimatedModelVertex third = {};
    third.joints = {5, 9, 0, 0};
    third.weights = {0.5f, 0.5f, 0.0f, 0.0f};
    primitive.vertices = {first, second, third};
    asset.primitives.push_back(primitive);

    OpenYAMM::Game::AnimatedModelPose pose = {};
    pose.skinningMatrices.resize(10);

    const OpenYAMM::Game::AnimatedModelRenderPrep renderPrep =
        OpenYAMM::Game::buildAnimatedModelRenderPrep(asset, pose, 2);
    REQUIRE(renderPrep.drawItems.size() == 1);
    CHECK(renderPrep.diagnostics.empty());
    const OpenYAMM::Game::AnimatedModelDrawItem &drawItem = renderPrep.drawItems.front();
    REQUIRE(drawItem.bonePalette.size() == 2);
    CHECK(drawItem.vertices[0].joints[0] == 0);
    CHECK(drawItem.vertices[1].joints[0] == 1);
    CHECK(drawItem.vertices[2].joints[0] == 0);
    CHECK(drawItem.vertices[2].joints[1] == 1);

    const OpenYAMM::Game::AnimatedModelRenderPrep rejected =
        OpenYAMM::Game::buildAnimatedModelRenderPrep(asset, pose, 1);
    CHECK(rejected.drawItems.empty());
    REQUIRE(rejected.diagnostics.size() == 1);
    CHECK(rejected.diagnostics[0].error);
}

TEST_CASE("animated model validator reports invalid animation targets and non-finite transforms")
{
    OpenYAMM::Game::AnimatedModelAsset asset = {};
    asset.nodes.push_back(OpenYAMM::Game::AnimatedModelNode{});
    asset.bounds.valid = true;
    asset.bounds.min = {0.0f, 0.0f, 0.0f};
    asset.bounds.max = {1.0f, 1.0f, 1.0f};
    asset.materials.push_back(OpenYAMM::Game::AnimatedModelMaterial{});

    OpenYAMM::Game::AnimatedModelPrimitive primitive = {};
    primitive.materialIndex = 0;
    primitive.vertexCount = 1;
    primitive.indexCount = 1;
    primitive.hasPositions = true;
    primitive.hasNormals = true;
    primitive.hasTexcoords = true;
    primitive.hasJoints = true;
    primitive.hasWeights = true;
    primitive.bounds = asset.bounds;
    OpenYAMM::Game::AnimatedModelVertex vertex = {};
    vertex.normal = {0.0f, 0.0f, 1.0f};
    vertex.weights = {1.0f, 0.0f, 0.0f, 0.0f};
    primitive.vertices.push_back(vertex);
    primitive.indices.push_back(0);
    asset.primitives.push_back(primitive);

    OpenYAMM::Game::AnimatedModelSkin skin = {};
    skin.joints.push_back(OpenYAMM::Game::AnimatedModelJoint{});
    asset.skins.push_back(skin);

    OpenYAMM::Game::AnimatedModelClip clip = {};
    clip.name = "invalid";
    clip.durationSeconds = 1.0f;
    OpenYAMM::Game::AnimatedModelTransform invalidTransform = {};
    invalidTransform.translation.x = std::numeric_limits<float>::quiet_NaN();
    OpenYAMM::Game::AnimatedModelChannel channel = {};
    channel.nodeIndex = 7;
    channel.path = OpenYAMM::Game::AnimatedModelChannelPath::Translation;
    channel.timesSeconds = {0.0f, 0.8f, 0.4f};
    channel.transforms = {
        OpenYAMM::Game::AnimatedModelTransform{},
        invalidTransform,
        OpenYAMM::Game::AnimatedModelTransform{}};
    clip.channels.push_back(channel);
    asset.clips.push_back(clip);

    OpenYAMM::Game::validateAnimatedModelAsset(asset);

    bool foundInvalidNode = false;
    bool foundNonMonotonicTime = false;
    bool foundNonFiniteTransform = false;
    for (const OpenYAMM::Game::AnimatedModelDiagnostic &diagnostic : asset.diagnostics)
    {
        foundInvalidNode = foundInvalidNode
            || diagnostic.message == "animation channel references an invalid node";
        foundNonMonotonicTime = foundNonMonotonicTime
            || diagnostic.message == "animation channel key times are not monotonic";
        foundNonFiniteTransform = foundNonFiniteTransform
            || diagnostic.message == "animation channel has a non-finite key transform";
    }

    CHECK(foundInvalidNode);
    CHECK(foundNonMonotonicTime);
    CHECK(foundNonFiniteTransform);
}

TEST_CASE("animated model event queries preserve MM9 sidecar animation events")
{
    if (!mm9ModelAssetsAvailable())
    {
        WARN("MM9 model assets are not present; skipping real asset animation event validation");
        return;
    }

    const OpenYAMM::Game::AnimatedModelAsset bigfoot = loadMm9Model("bigfoot");
    const OpenYAMM::Game::AnimatedModelClip *pRun = bigfoot.findClip("run");
    REQUIRE(pRun != nullptr);
    REQUIRE(pRun->events.size() == 2);
    CHECK(pRun->events[0].timeSeconds == doctest::Approx(0.105f));
    CHECK(pRun->events[0].key == "footstep");
    CHECK(pRun->events[1].timeSeconds == doctest::Approx(0.385f));
    CHECK(pRun->events[1].key == "footstep");

    const std::vector<OpenYAMM::Game::AnimatedModelEvent> firstStep =
        OpenYAMM::Game::animatedModelEventsInInterval(*pRun, 0.0f, 0.2f, false);
    REQUIRE(firstStep.size() == 1);
    CHECK(firstStep[0].timeSeconds == doctest::Approx(0.105f));
    CHECK(firstStep[0].key == "footstep");

    const std::vector<OpenYAMM::Game::AnimatedModelEvent> loopedStep =
        OpenYAMM::Game::animatedModelEventsInInterval(*pRun, 0.6f, 0.85f, true);
    REQUIRE(loopedStep.size() == 1);
    CHECK(loopedStep[0].timeSeconds == doctest::Approx(0.105f));
    CHECK(loopedStep[0].key == "footstep");
}

TEST_CASE("animated model controller advances clips, emits events, and tracks transitions")
{
    OpenYAMM::Game::AnimatedModelClip idle = {};
    idle.name = "idle";
    idle.durationSeconds = 1.0f;
    idle.events.push_back(OpenYAMM::Game::AnimatedModelEvent{0.0f, "loop_start"});
    idle.events.push_back(OpenYAMM::Game::AnimatedModelEvent{0.25f, "step_a"});
    idle.events.push_back(OpenYAMM::Game::AnimatedModelEvent{0.75f, "step_b"});

    OpenYAMM::Game::AnimatedModelClip attack = {};
    attack.name = "attack";
    attack.durationSeconds = 0.5f;
    attack.events.push_back(OpenYAMM::Game::AnimatedModelEvent{0.2f, "hit"});

    OpenYAMM::Game::AnimatedModelController controller = {};
    OpenYAMM::Game::animatedModelControllerPlay(controller, &idle, true, 0.0f);

    OpenYAMM::Game::AnimatedModelControllerUpdate update =
        OpenYAMM::Game::animatedModelControllerUpdate(controller, 0.3f);
    CHECK(controller.currentTimeSeconds == doctest::Approx(0.3f));
    REQUIRE(update.events.size() == 1);
    CHECK(update.events[0].key == "step_a");
    CHECK_FALSE(update.clipFinished);

    update = OpenYAMM::Game::animatedModelControllerUpdate(controller, 0.5f);
    CHECK(controller.currentTimeSeconds == doctest::Approx(0.8f));
    REQUIRE(update.events.size() == 1);
    CHECK(update.events[0].key == "step_b");

    update = OpenYAMM::Game::animatedModelControllerUpdate(controller, 0.5f);
    CHECK(controller.currentTimeSeconds == doctest::Approx(0.3f));
    REQUIRE(update.events.size() == 2);
    CHECK(update.events[0].key == "loop_start");
    CHECK(update.events[1].key == "step_a");

    OpenYAMM::Game::animatedModelControllerPlay(controller, &attack, false, 0.5f);
    CHECK(controller.pPreviousClip == &idle);
    CHECK(controller.previousTimeSeconds == doctest::Approx(0.3f));
    CHECK(controller.pCurrentClip == &attack);
    CHECK(controller.currentTimeSeconds == doctest::Approx(0.0f));

    update = OpenYAMM::Game::animatedModelControllerUpdate(controller, 0.25f);
    CHECK(controller.currentTimeSeconds == doctest::Approx(0.25f));
    CHECK(controller.transitionElapsedSeconds == doctest::Approx(0.25f));
    CHECK(controller.pPreviousClip == &idle);
    REQUIRE(update.events.size() == 1);
    CHECK(update.events[0].key == "hit");

    update = OpenYAMM::Game::animatedModelControllerUpdate(controller, 0.4f);
    CHECK(controller.currentTimeSeconds == doctest::Approx(0.5f));
    CHECK(update.clipFinished);
    CHECK(controller.pPreviousClip == nullptr);
    CHECK(controller.transitionDurationSeconds == doctest::Approx(0.0f));
}

TEST_CASE("animated model controller samples blended transition poses")
{
    OpenYAMM::Game::AnimatedModelAsset asset = {};
    asset.nodes.push_back(OpenYAMM::Game::AnimatedModelNode{});

    OpenYAMM::Game::AnimatedModelClip idle = {};
    idle.name = "idle";
    idle.durationSeconds = 1.0f;
    OpenYAMM::Game::AnimatedModelChannel idleChannel = {};
    idleChannel.path = OpenYAMM::Game::AnimatedModelChannelPath::Translation;
    idleChannel.timesSeconds = {0.0f, 1.0f};
    idleChannel.transforms = {
        OpenYAMM::Game::AnimatedModelTransform{},
        OpenYAMM::Game::AnimatedModelTransform{}};
    idle.channels.push_back(idleChannel);

    OpenYAMM::Game::AnimatedModelClip attack = {};
    attack.name = "attack";
    attack.durationSeconds = 1.0f;
    OpenYAMM::Game::AnimatedModelTransform attackTransform = {};
    attackTransform.translation.x = 10.0f;
    OpenYAMM::Game::AnimatedModelChannel attackChannel = {};
    attackChannel.path = OpenYAMM::Game::AnimatedModelChannelPath::Translation;
    attackChannel.timesSeconds = {0.0f, 1.0f};
    attackChannel.transforms = {attackTransform, attackTransform};
    attack.channels.push_back(attackChannel);

    OpenYAMM::Game::AnimatedModelController controller = {};
    OpenYAMM::Game::animatedModelControllerPlay(controller, &idle, true, 0.0f);
    OpenYAMM::Game::animatedModelControllerUpdate(controller, 0.25f);

    OpenYAMM::Game::animatedModelControllerPlay(controller, &attack, false, 1.0f);
    OpenYAMM::Game::AnimatedModelPose pose =
        OpenYAMM::Game::sampleAnimatedModelControllerPose(asset, controller);
    REQUIRE(pose.localTransforms.size() == 1);
    CHECK(pose.localTransforms[0].translation.x == doctest::Approx(0.0f));
    CHECK(pose.globalTransforms[0].values[12] == doctest::Approx(0.0f));

    OpenYAMM::Game::animatedModelControllerUpdate(controller, 0.5f);
    pose = OpenYAMM::Game::sampleAnimatedModelControllerPose(asset, controller);
    REQUIRE(pose.localTransforms.size() == 1);
    CHECK(pose.localTransforms[0].translation.x == doctest::Approx(5.0f));
    CHECK(pose.globalTransforms[0].values[12] == doctest::Approx(5.0f));
    CHECK(OpenYAMM::Game::animatedModelMatrixIsFinite(pose.globalTransforms[0]));

    OpenYAMM::Game::animatedModelControllerUpdate(controller, 0.6f);
    pose = OpenYAMM::Game::sampleAnimatedModelControllerPose(asset, controller);
    REQUIRE(pose.localTransforms.size() == 1);
    CHECK(pose.localTransforms[0].translation.x == doctest::Approx(10.0f));
    CHECK(pose.globalTransforms[0].values[12] == doctest::Approx(10.0f));
    CHECK(controller.pPreviousClip == nullptr);
}

TEST_CASE("animated model pose sampling composes parent and child transforms")
{
    OpenYAMM::Game::AnimatedModelAsset asset = {};
    OpenYAMM::Game::AnimatedModelNode root = {};
    root.childIndices.push_back(1);
    asset.nodes.push_back(root);

    OpenYAMM::Game::AnimatedModelNode child = {};
    child.parentIndex = 0;
    child.bindTransform.translation.y = 2.0f;
    asset.nodes.push_back(child);

    OpenYAMM::Game::AnimatedModelTransform rootStart = {};
    rootStart.translation.x = 4.0f;
    OpenYAMM::Game::AnimatedModelTransform rootEnd = {};
    rootEnd.translation.x = 10.0f;

    OpenYAMM::Game::AnimatedModelChannel channel = {};
    channel.nodeIndex = 0;
    channel.path = OpenYAMM::Game::AnimatedModelChannelPath::Translation;
    channel.timesSeconds = {0.0f, 1.0f};
    channel.transforms = {rootStart, rootEnd};

    OpenYAMM::Game::AnimatedModelClip clip = {};
    clip.name = "move_root";
    clip.durationSeconds = 1.0f;
    clip.channels.push_back(channel);
    asset.clips.push_back(clip);

    const OpenYAMM::Game::AnimatedModelPose pose =
        OpenYAMM::Game::sampleAnimatedModelPose(asset, &asset.clips.front(), 1.0f, false);
    REQUIRE(pose.globalTransforms.size() == 2);
    CHECK(pose.globalTransforms[0].values[12] == doctest::Approx(10.0f));
    CHECK(pose.globalTransforms[0].values[13] == doctest::Approx(0.0f));
    CHECK(pose.globalTransforms[1].values[12] == doctest::Approx(10.0f));
    CHECK(pose.globalTransforms[1].values[13] == doctest::Approx(2.0f));
    CHECK(OpenYAMM::Game::animatedModelMatrixIsFinite(pose.globalTransforms[0]));
    CHECK(OpenYAMM::Game::animatedModelMatrixIsFinite(pose.globalTransforms[1]));
}
