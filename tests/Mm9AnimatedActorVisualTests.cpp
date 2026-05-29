#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/maps/Mm9EventsYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/mm9/Mm9AnimatedActorBinding.h"
#include "game/mm9/Mm9AnimatedActorVisual.h"
#include "game/mm9/Mm9AnimatedModelSidecar.h"
#include "game/mm9/Mm9DialoguePackage.h"
#include "game/mm9/Mm9DialogueRuntime.h"
#include "game/mm9/Mm9InteractionRouting.h"
#include "game/mm9/Mm9ScriptedObjectRuntime.h"
#include "game/mm9/Mm9ScriptRuntime.h"
#include "game/party/Party.h"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{
std::filesystem::path sourceRoot()
{
    return std::filesystem::path(OPENYAMM_SOURCE_DIR);
}

std::optional<std::string> readTextFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    if (!file)
    {
        return std::nullopt;
    }

    std::ostringstream stream;
    stream << file.rdbuf();
    return stream.str();
}

std::string readRequiredTextFile(const std::filesystem::path &path)
{
    std::optional<std::string> contents = readTextFile(path);
    const std::string message = "Missing source file: " + path.generic_string();
    REQUIRE_MESSAGE(contents.has_value(), message.c_str());
    return *contents;
}

std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_mm9_actor_visual_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

bool mm9ModelAssetsAvailable()
{
    return std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/bigfoot.glb")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/bigfoot.model.yml")
        && std::filesystem::exists(sourceRoot() / "assets_dev/worlds/mm9/models/model_registry.yml");
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

OpenYAMM::Game::AnimatedModelAsset loadMm9ResolvedModel(
    const OpenYAMM::Game::Mm9AnimatedModelResolution &resolution)
{
    std::string errorMessage;
    std::optional<OpenYAMM::Game::AnimatedModelAsset> asset =
        OpenYAMM::Game::loadAnimatedModelAsset(resolution.modelAssetPath, errorMessage);
    REQUIRE_MESSAGE(asset.has_value(), errorMessage.c_str());

    std::optional<OpenYAMM::Game::Mm9AnimatedModelSidecar> sidecar =
        OpenYAMM::Game::loadMm9AnimatedModelSidecar(resolution.modelSidecarPath, errorMessage);
    REQUIRE_MESSAGE(sidecar.has_value(), errorMessage.c_str());

    OpenYAMM::Game::mergeMm9AnimatedModelSidecar(*sidecar, *asset);
    return *asset;
}

OpenYAMM::Game::AnimatedModelClip makeTranslationClip(
    const std::string &name,
    float translationX)
{
    OpenYAMM::Game::AnimatedModelTransform transform = {};
    transform.translation.x = translationX;

    OpenYAMM::Game::AnimatedModelChannel channel = {};
    channel.path = OpenYAMM::Game::AnimatedModelChannelPath::Translation;
    channel.timesSeconds = {0.0f, 1.0f};
    channel.transforms = {transform, transform};

    OpenYAMM::Game::AnimatedModelClip clip = {};
    clip.name = name;
    clip.durationSeconds = 1.0f;
    clip.channels.push_back(channel);
    return clip;
}

size_t countOccurrences(const std::string &text, const std::string &needle)
{
    size_t count = 0;
    size_t cursor = 0;
    while (cursor < text.size())
    {
        const size_t found = text.find(needle, cursor);
        if (found == std::string::npos)
        {
            break;
        }

        ++count;
        cursor = found + needle.size();
    }

    return count;
}

bool containsAnyToken(const std::string &text, const std::vector<std::string> &tokens)
{
    for (const std::string &token : tokens)
    {
        if (text.find(token) != std::string::npos)
        {
            return true;
        }
    }
    return false;
}

bool clipHasEventContaining(
    const OpenYAMM::Game::AnimatedModelClip &clip,
    const std::string &token)
{
    for (const OpenYAMM::Game::AnimatedModelEvent &event : clip.events)
    {
        if (event.key.find(token) != std::string::npos)
        {
            return true;
        }
    }
    return false;
}
}

TEST_CASE("MM9 native animated actor runtime stays MM9-scoped and independent of Mm9DatWorld")
{
    const std::string outdoorGameView = readRequiredTextFile(sourceRoot() / "game/outdoor/OutdoorGameView.cpp");
    const std::string outdoorRenderer = readRequiredTextFile(sourceRoot() / "game/outdoor/OutdoorRenderer.cpp");
    const std::string actorBinding = readRequiredTextFile(sourceRoot() / "game/mm9/Mm9AnimatedActorBinding.cpp");
    const std::string actorVisual = readRequiredTextFile(sourceRoot() / "game/mm9/Mm9AnimatedActorVisual.cpp");
    const std::string modelResolver = readRequiredTextFile(sourceRoot() / "game/mm9/Mm9AnimatedModelResolver.cpp");
    const std::string datWorldHeader = readRequiredTextFile(sourceRoot() / "game/mm9/Mm9DatWorld.h");
    const std::string datWorldSource = readRequiredTextFile(sourceRoot() / "game/mm9/Mm9DatWorld.cpp");

    CHECK(outdoorGameView.find("normalizeWorldId(map.worldId) == \"mm9\"") != std::string::npos);
    CHECK(outdoorGameView.find("worlds/mm9/models/model_registry.yml") != std::string::npos);
    CHECK(outdoorGameView.find("resolveMm9AnimatedActorVisualSource") != std::string::npos);
    CHECK(outdoorGameView.find("m_mm9AnimatedActorInstances.push_back") != std::string::npos);
    CHECK(outdoorRenderer.find("renderMm9AnimatedActorModels(view, MainViewId") != std::string::npos);

    const std::vector<std::string> nativeActorSources = {
        outdoorGameView,
        outdoorRenderer,
        actorBinding,
        actorVisual,
        modelResolver,
    };

    for (const std::string &source : nativeActorSources)
    {
        CHECK(source.find("Mm9DatWorld") == std::string::npos);
    }

    const std::vector<std::string> forbiddenDatWorldAnimatedActorTokens = {
        "AnimatedModel",
        "Mm9Animated",
        "loadAnimatedModelAsset",
        "model_registry",
        ".glb",
        "bgfx",
    };
    CHECK_FALSE(containsAnyToken(datWorldHeader, forbiddenDatWorldAnimatedActorTokens));
    CHECK_FALSE(containsAnyToken(datWorldSource, forbiddenDatWorldAnimatedActorTokens));
}

TEST_CASE("Native MM9 animated actor path does not replace classic MM6-MM8 actor billboards")
{
    const std::string outdoorGameView = readRequiredTextFile(sourceRoot() / "game/outdoor/OutdoorGameView.cpp");
    const std::string outdoorRenderer = readRequiredTextFile(sourceRoot() / "game/outdoor/OutdoorRenderer.cpp");
    const std::string outdoorWorldRuntime =
        readRequiredTextFile(sourceRoot() / "game/outdoor/OutdoorWorldRuntime.cpp");
    const std::string outdoorBillboardRenderer =
        readRequiredTextFile(sourceRoot() / "game/outdoor/OutdoorBillboardRenderer.cpp");
    const std::string indoorGameView = readRequiredTextFile(sourceRoot() / "game/indoor/IndoorGameView.cpp");
    const std::string indoorWorldRuntime =
        readRequiredTextFile(sourceRoot() / "game/indoor/IndoorWorldRuntime.cpp");

    CHECK(outdoorGameView.find("if (normalizeWorldId(map.worldId) == \"mm9\" && outdoorSceneData)")
        != std::string::npos);
    CHECK(outdoorGameView.find("m_mm9AnimatedActorInstances.clear()") != std::string::npos);
    CHECK(outdoorGameView.find("m_mm9AnimatedActorInstances.push_back") != std::string::npos);
    CHECK(outdoorRenderer.find("if (!view.m_showActors") != std::string::npos);
    CHECK(outdoorRenderer.find("|| view.m_mm9AnimatedActorInstances.empty()") != std::string::npos);
    CHECK(outdoorRenderer.find("OutdoorBillboardRenderer::renderActorPreviewBillboards") != std::string::npos);
    CHECK(outdoorRenderer.find("renderMm9AnimatedActorModels(view, MainViewId") != std::string::npos);

    CHECK(outdoorWorldRuntime.find("buildMonsterVisualState(*m_pActorSpriteFrameTable") != std::string::npos);
    CHECK(outdoorBillboardRenderer.find("renderActorPreviewBillboards") != std::string::npos);
    CHECK(outdoorBillboardRenderer.find("ActorPreviewBillboard") != std::string::npos);

    CHECK(indoorGameView.find("Mm9AnimatedActor") == std::string::npos);
    CHECK(indoorWorldRuntime.find("Mm9AnimatedActor") == std::string::npos);
    CHECK(countOccurrences(outdoorGameView, "resolveMm9AnimatedActorVisualSource") == 1);
    CHECK(countOccurrences(outdoorRenderer, "renderMm9AnimatedActorModels(view, MainViewId") == 1);
}

TEST_CASE("Native MM9 animated actor path keeps initial implementation non-goals out of runtime")
{
    const std::string animatedModelAsset = readRequiredTextFile(sourceRoot() / "game/render/AnimatedModelAsset.cpp");
    const std::string animatedModelRenderer =
        readRequiredTextFile(sourceRoot() / "game/render/AnimatedModelRenderer.cpp");
    const std::string actorBinding = readRequiredTextFile(sourceRoot() / "game/mm9/Mm9AnimatedActorBinding.cpp");
    const std::string actorVisual = readRequiredTextFile(sourceRoot() / "game/mm9/Mm9AnimatedActorVisual.cpp");
    const std::string outdoorGameView = readRequiredTextFile(sourceRoot() / "game/outdoor/OutdoorGameView.cpp");

    const std::vector<std::string> forbiddenCoreTokens = {
        "LithTech",
        "LTB",
        ".ltb",
        ".abc",
        "FEAR",
        "AnimationGraph",
    };

    CHECK_FALSE(containsAnyToken(animatedModelAsset, forbiddenCoreTokens));
    CHECK_FALSE(containsAnyToken(animatedModelRenderer, forbiddenCoreTokens));
    CHECK_FALSE(containsAnyToken(actorVisual, forbiddenCoreTokens));
    CHECK(actorBinding.find("Mm9ScriptedBillboardVisual") == std::string::npos);
    CHECK(actorVisual.find("Mm9ScriptedBillboardVisual") == std::string::npos);
    CHECK(outdoorGameView.find("resolveMm9AnimatedActorVisualSource(object, resolver, diagnostics)")
        != std::string::npos);
    CHECK(outdoorGameView.find("loadAnimatedModelAsset(resolved->resolution.modelAssetPath") != std::string::npos);
}

TEST_CASE("MM9 animated actor visual initializes source identity, clip, pose, socket, and collision state")
{
    if (!mm9ModelAssetsAvailable())
    {
        WARN("MM9 generated model assets are not present; skipping real animated actor visual validation");
        return;
    }

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(
        resolver.loadRegistry(sourceRoot() / "assets_dev/worlds/mm9/models/model_registry.yml", errorMessage),
        errorMessage);

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> resolution =
        resolver.resolve("MODELS\\BIGFOOT.ABC", "SKINS\\BIGFOOT3.DTX", diagnostics);
    REQUIRE(resolution.has_value());
    CHECK(diagnostics.empty());

    OpenYAMM::Game::AnimatedModelAsset asset = loadMm9Model("bigfoot");
    OpenYAMM::Game::Mm9AnimatedActorVisualSource source = {};
    source.mapId = "guberland";
    source.objectId = "mm9:guberland:object:12";
    source.sourceObjectIndex = 12;
    source.sourceClass = "Monster";
    source.sourceName = "Yeti";
    source.sourceModel = "MODELS\\BIGFOOT.ABC";
    source.sourceSkin = "SKINS\\BIGFOOT3.DTX";
    source.requestedClip = "run";
    source.semanticState = "running";
    source.visible = true;
    source.solid = true;
    source.rayHit = true;
    source.pickable = true;
    source.x = 100.0f;
    source.y = 200.0f;
    source.z = 300.0f;
    source.facingRadians = 1.25f;
    source.scale = 1.5f;
    source.radius = 48.0f;
    source.height = 160.0f;
    source.verticalOffset = -8.0f;

    OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
    REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(source, *resolution, asset, visual));
    CHECK(visual.mapId == "guberland");
    CHECK(visual.objectId == "mm9:guberland:object:12");
    CHECK(visual.sourceObjectIndex == 12);
    CHECK(visual.modelId == "bigfoot");
    CHECK(visual.skinBindingId == "bigfoot_bigfoot3");
    CHECK(visual.currentClipName == "run");
    CHECK(visual.semanticState == "running");
    CHECK(visual.visible);
    CHECK(visual.solid);
    CHECK(visual.rayHit);
    CHECK(visual.pickable);
    CHECK(visual.x == doctest::Approx(100.0f));
    CHECK(visual.y == doctest::Approx(200.0f));
    CHECK(visual.z == doctest::Approx(300.0f));
    CHECK(visual.facingRadians == doctest::Approx(1.25f));
    CHECK(visual.scale == doctest::Approx(1.5f));
    CHECK(visual.modelToWorld.values[12] == doctest::Approx(100.0f));
    CHECK(visual.modelToWorld.values[13] == doctest::Approx(200.0f));
    CHECK(visual.modelToWorld.values[14] == doctest::Approx(300.0f));
    CHECK(visual.worldBounds.valid);
    CHECK(visual.radius == doctest::Approx(48.0f));
    CHECK(visual.height == doctest::Approx(160.0f));
    CHECK(visual.verticalOffset == doctest::Approx(-8.0f));
    REQUIRE(visual.materialOverrides.size() == 1);
    CHECK(visual.materialOverrides[0].runtimeTexture == "skins/bigfoot3.dtx");
    CHECK(visual.poseCache.globalTransforms.size() == asset.nodes.size());
    CHECK(visual.poseCache.skinningMatrices.size() == asset.skins.front().joints.size());
    REQUIRE(visual.renderPrepCache.drawItems.size() == asset.primitives.size());
    CHECK(visual.renderPrepCache.diagnostics.empty());
    CHECK(visual.renderPrepCache.counters.skinnedDrawCalls == asset.primitives.size());
    CHECK(visual.renderPrepCache.counters.uploadedBoneMatrices > 0);
    CHECK(visual.renderPrepCache.drawItems.front().texture == "skins/bigfoot3.dtx");
    CHECK(OpenYAMM::Game::findMm9AnimatedActorSocketTransform(visual, "RHand1").has_value());
    const std::optional<OpenYAMM::Game::AnimatedModelMat4> worldSocket =
        OpenYAMM::Game::findMm9AnimatedActorWorldSocketTransform(visual, "RHand1");
    REQUIRE(worldSocket.has_value());
    CHECK(OpenYAMM::Game::animatedModelMatrixIsFinite(*worldSocket));
}

TEST_CASE("MM9 animated actor visual updates controller pose, socket cache, and animation events")
{
    if (!mm9ModelAssetsAvailable())
    {
        WARN("MM9 generated model assets are not present; skipping real animated actor visual update validation");
        return;
    }

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(
        resolver.loadRegistry(sourceRoot() / "assets_dev/worlds/mm9/models/model_registry.yml", errorMessage),
        errorMessage);

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> resolution =
        resolver.resolve("models/bigfoot.abc", "skins/bigfoot1.dtx", diagnostics);
    REQUIRE(resolution.has_value());

    OpenYAMM::Game::AnimatedModelAsset asset = loadMm9Model("bigfoot");
    OpenYAMM::Game::Mm9AnimatedActorVisualSource source = {};
    source.sourceModel = "models/bigfoot.abc";
    source.sourceSkin = "skins/bigfoot1.dtx";
    source.requestedClip = "run";
    source.semanticState = "running";

    OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
    REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(source, *resolution, asset, visual));

    const OpenYAMM::Game::Mm9AnimatedActorVisualUpdate update =
        OpenYAMM::Game::updateMm9AnimatedActorVisual(visual, asset, 0.2f);
    REQUIRE(update.events.size() == 1);
    CHECK(update.events[0].key == "footstep");
    CHECK(visual.controller.currentTimeSeconds == doctest::Approx(0.2f));
    CHECK(visual.poseCache.globalTransforms.size() == asset.nodes.size());
    CHECK(visual.renderPrepCache.drawItems.size() == asset.primitives.size());
    CHECK(visual.renderPrepCache.counters.skinnedTriangles == asset.primitives.front().indices.size() / 3);
    CHECK(OpenYAMM::Game::findMm9AnimatedActorSocketTransform(visual, "rhand1").has_value());
    CHECK(OpenYAMM::Game::findMm9AnimatedActorWorldSocketTransform(visual, "rhand1").has_value());
}

TEST_CASE("MM9 animated actor visual updates model-to-world transform and world bounds")
{
    if (!mm9ModelAssetsAvailable())
    {
        WARN("MM9 generated model assets are not present; skipping visual transform update validation");
        return;
    }

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(
        resolver.loadRegistry(sourceRoot() / "assets_dev/worlds/mm9/models/model_registry.yml", errorMessage),
        errorMessage);

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> resolution =
        resolver.resolve("models/bigfoot.abc", "skins/bigfoot1.dtx", diagnostics);
    REQUIRE(resolution.has_value());

    OpenYAMM::Game::AnimatedModelAsset asset = loadMm9Model("bigfoot");
    OpenYAMM::Game::Mm9AnimatedActorVisualSource source = {};
    source.sourceModel = "models/bigfoot.abc";
    source.sourceSkin = "skins/bigfoot1.dtx";
    source.requestedClip = "run";
    source.semanticState = "running";

    OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
    REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(source, *resolution, asset, visual));
    OpenYAMM::Game::setMm9AnimatedActorVisualTransform(visual, asset, 10.0f, 20.0f, 30.0f, 0.0f, 2.0f);

    CHECK(visual.x == doctest::Approx(10.0f));
    CHECK(visual.y == doctest::Approx(20.0f));
    CHECK(visual.z == doctest::Approx(30.0f));
    CHECK(visual.scale == doctest::Approx(2.0f));
    CHECK(visual.modelToWorld.values[0] == doctest::Approx(2.0f));
    CHECK(visual.modelToWorld.values[5] == doctest::Approx(2.0f));
    CHECK(visual.modelToWorld.values[10] == doctest::Approx(2.0f));
    CHECK(visual.modelToWorld.values[12] == doctest::Approx(10.0f));
    CHECK(visual.modelToWorld.values[13] == doctest::Approx(20.0f));
    CHECK(visual.modelToWorld.values[14] == doctest::Approx(30.0f));
    REQUIRE(visual.worldBounds.valid);
    CHECK(visual.worldBounds.min.x == doctest::Approx(10.0f + asset.bounds.min.x * 2.0f));
    CHECK(visual.worldBounds.max.x == doctest::Approx(10.0f + asset.bounds.max.x * 2.0f));
    CHECK(visual.worldBounds.min.y == doctest::Approx(20.0f + asset.bounds.min.y * 2.0f));
    CHECK(visual.worldBounds.max.y == doctest::Approx(20.0f + asset.bounds.max.y * 2.0f));
    CHECK(visual.worldBounds.min.z == doctest::Approx(30.0f + asset.bounds.min.z * 2.0f));
    CHECK(visual.worldBounds.max.z == doctest::Approx(30.0f + asset.bounds.max.z * 2.0f));
    CHECK(OpenYAMM::Game::findMm9AnimatedActorWorldSocketTransform(visual, "RHand1").has_value());
}

TEST_CASE("MM9 animated actor visual reports render prep palette limit diagnostics")
{
    if (!mm9ModelAssetsAvailable())
    {
        WARN("MM9 generated model assets are not present; skipping visual render prep diagnostic validation");
        return;
    }

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(
        resolver.loadRegistry(sourceRoot() / "assets_dev/worlds/mm9/models/model_registry.yml", errorMessage),
        errorMessage);

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> resolution =
        resolver.resolve("models/bigfoot.abc", "skins/bigfoot1.dtx", diagnostics);
    REQUIRE(resolution.has_value());

    OpenYAMM::Game::AnimatedModelAsset asset = loadMm9Model("bigfoot");
    OpenYAMM::Game::Mm9AnimatedActorVisualSource source = {};
    source.sourceModel = "models/bigfoot.abc";
    source.sourceSkin = "skins/bigfoot1.dtx";
    source.requestedClip = "run";
    source.semanticState = "running";
    source.maxBoneMatrices = 1;

    OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
    REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(source, *resolution, asset, visual));
    CHECK(visual.renderPrepCache.drawItems.empty());
    REQUIRE(visual.renderPrepCache.diagnostics.size() == 1);
    CHECK(visual.renderPrepCache.diagnostics[0].error);
}

TEST_CASE("MM9 animated actor visual resolves semantic fallbacks and reports unresolved clips")
{
    OpenYAMM::Game::AnimatedModelAsset asset = {};
    asset.nodes.push_back(OpenYAMM::Game::AnimatedModelNode{});
    asset.clips.push_back(makeTranslationClip("stand", 0.0f));
    asset.clips.push_back(makeTranslationClip("walk", 1.0f));
    asset.clips.push_back(makeTranslationClip("Rattack1", 2.0f));

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    const OpenYAMM::Game::AnimatedModelClip *pClip =
        OpenYAMM::Game::resolveMm9AnimatedActorClip(asset, "missing", "walking", diagnostics);
    REQUIRE(pClip != nullptr);
    CHECK(pClip->name == "walk");
    REQUIRE(diagnostics.size() == 1);
    CHECK_FALSE(diagnostics[0].error);

    diagnostics.clear();
    pClip = OpenYAMM::Game::resolveMm9AnimatedActorClip(asset, "", "ranged_attack", diagnostics);
    REQUIRE(pClip != nullptr);
    CHECK(pClip->name == "Rattack1");
    CHECK(diagnostics.empty());

    OpenYAMM::Game::AnimatedModelAsset singleClipAsset = {};
    singleClipAsset.clips.push_back(makeTranslationClip("MP_2a", 0.0f));
    diagnostics.clear();
    pClip = OpenYAMM::Game::resolveMm9AnimatedActorClip(singleClipAsset, "", "idle", diagnostics);
    REQUIRE(pClip != nullptr);
    CHECK(pClip->name == "MP_2a");
    REQUIRE(diagnostics.size() == 1);
    CHECK_FALSE(diagnostics[0].error);

    OpenYAMM::Game::AnimatedModelAsset emptyAsset = {};
    diagnostics.clear();
    pClip = OpenYAMM::Game::resolveMm9AnimatedActorClip(emptyAsset, "", "death", diagnostics);
    CHECK(pClip == nullptr);
    REQUIRE(diagnostics.size() == 1);
    CHECK(diagnostics[0].error);

    OpenYAMM::Game::Mm9AnimatedModelResolution resolution = {};
    resolution.modelId = "missing_animation";
    OpenYAMM::Game::Mm9AnimatedActorVisualSource source = {};
    source.semanticState = "death";
    OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
    CHECK_FALSE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(source, resolution, emptyAsset, visual));
    CHECK(visual.currentClipName.empty());
    REQUIRE(!visual.diagnostics.empty());
    CHECK(visual.diagnostics.back().error);
    CHECK(visual.diagnostics.back().message.find("no clip") != std::string::npos);
}

TEST_CASE("MM9 animated actor visual transition blends cached pose")
{
    OpenYAMM::Game::AnimatedModelAsset asset = {};
    asset.nodes.push_back(OpenYAMM::Game::AnimatedModelNode{});
    asset.clips.push_back(makeTranslationClip("stand", 0.0f));
    asset.clips.push_back(makeTranslationClip("walk", 10.0f));

    OpenYAMM::Game::Mm9AnimatedModelResolution resolution = {};
    resolution.modelId = "test";
    resolution.modelAssetPath = "models/test.glb";
    resolution.modelSidecarPath = "models/test.model.yml";

    OpenYAMM::Game::Mm9AnimatedActorVisualSource source = {};
    source.requestedClip = "stand";
    source.semanticState = "idle";

    OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
    REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(source, resolution, asset, visual));
    REQUIRE(OpenYAMM::Game::setMm9AnimatedActorVisualClip(visual, asset, "walk", "walking", true, 1.0f));

    OpenYAMM::Game::updateMm9AnimatedActorVisual(visual, asset, 0.5f);
    REQUIRE(visual.poseCache.localTransforms.size() == 1);
    CHECK(visual.poseCache.localTransforms[0].translation.x == doctest::Approx(5.0f));
    CHECK(visual.poseCache.globalTransforms[0].values[12] == doctest::Approx(5.0f));
}

TEST_CASE("MM9 scripted object binds visibility, collision, movement, and pick identity to animated visual")
{
    OpenYAMM::Game::Mm9ScriptedObject object = {};
    object.mapId = "guberland";
    object.objectId = "mm9:guberland:object:42";
    object.sourceObjectIndex = 42;
    object.sourceClass = "Guard";
    object.sourceName = "DockGuard";
    object.sourceModel = "models\\guard.abc";
    object.sourceSkin = "skins\\guard3.dtx";
    object.currentClip = "placeholder";
    object.visible = true;
    object.solid = false;
    object.rayHit = true;
    object.pickable = true;
    object.x = 100.0f;
    object.y = 200.0f;
    object.z = 300.0f;
    object.facingRadians = 0.5f;
    object.scale = 1.25f;
    object.radius = 44.0f;
    object.height = 188.0f;
    object.verticalOffset = -4.0f;
    object.movement.walking = true;
    object.movement.stationary = false;

    OpenYAMM::Game::Mm9AnimatedActorVisualSource source =
        OpenYAMM::Game::makeMm9AnimatedActorVisualSource(object, 96);
    CHECK(source.mapId == object.mapId);
    CHECK(source.objectId == object.objectId);
    CHECK(source.sourceObjectIndex == object.sourceObjectIndex);
    CHECK(source.sourceModel == object.sourceModel);
    CHECK(source.sourceSkin == object.sourceSkin);
    CHECK(source.requestedClip.empty());
    CHECK(source.semanticState == "walking");
    CHECK(source.visible);
    CHECK_FALSE(source.solid);
    CHECK(source.rayHit);
    CHECK(source.pickable);
    CHECK(source.radius == doctest::Approx(44.0f));
    CHECK(source.height == doctest::Approx(188.0f));
    CHECK(source.verticalOffset == doctest::Approx(-4.0f));
    CHECK(source.maxBoneMatrices == 96);

    OpenYAMM::Game::AnimatedModelAsset asset = {};
    asset.nodes.push_back(OpenYAMM::Game::AnimatedModelNode{});
    asset.clips.push_back(makeTranslationClip("walk", 0.0f));

    OpenYAMM::Game::Mm9AnimatedModelResolution resolution = {};
    resolution.modelId = "guard";
    resolution.modelAssetPath = "models/guard.glb";
    resolution.modelSidecarPath = "models/guard.model.yml";

    OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
    REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(source, resolution, asset, visual));
    CHECK(visual.currentClipName == "walk");
    CHECK(visual.visible);
    CHECK_FALSE(visual.solid);
    CHECK(visual.rayHit);
    CHECK(visual.pickable);
    CHECK_FALSE(OpenYAMM::Game::mm9AnimatedActorBlocksMovement(visual));

    const std::optional<OpenYAMM::Game::Mm9AnimatedActorPickIdentity> pickIdentity =
        OpenYAMM::Game::mm9AnimatedActorPickIdentity(visual);
    REQUIRE(pickIdentity.has_value());
    CHECK(pickIdentity->mapId == "guberland");
    CHECK(pickIdentity->objectId == "mm9:guberland:object:42");
    CHECK(pickIdentity->sourceObjectIndex == 42);
    CHECK(pickIdentity->sourceClass == "Guard");
    CHECK(pickIdentity->sourceName == "DockGuard");

    visual.rayHit = false;
    CHECK_FALSE(OpenYAMM::Game::mm9AnimatedActorCanBePicked(visual));
    CHECK_FALSE(OpenYAMM::Game::mm9AnimatedActorPickIdentity(visual).has_value());

    visual.rayHit = true;
    visual.visible = false;
    CHECK_FALSE(OpenYAMM::Game::mm9AnimatedActorCanBePicked(visual));
    CHECK_FALSE(OpenYAMM::Game::mm9AnimatedActorPickIdentity(visual).has_value());

    visual.visible = true;
    visual.solid = true;
    CHECK(OpenYAMM::Game::mm9AnimatedActorBlocksMovement(visual));
}

TEST_CASE("MM9 scripted object resolves native model source through animated actor binding")
{
    OpenYAMM::Game::Mm9ScriptedObject object = {};
    object.mapId = "guberland";
    object.objectId = "mm9:guberland:object:12";
    object.sourceObjectIndex = 12;
    object.sourceClass = "Monster";
    object.sourceName = "Yeti";
    object.sourceModel = "MODELS\\BIGFOOT.ABC";
    object.sourceSkin = "SKINS\\BIGFOOT3.DTX";
    object.visible = true;
    object.rayHit = true;
    object.pickable = true;

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(
        resolver.loadRegistry(sourceRoot() / "assets_dev/worlds/mm9/models/model_registry.yml", errorMessage),
        errorMessage);

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    const std::optional<OpenYAMM::Game::Mm9AnimatedActorResolvedSource> resolved =
        OpenYAMM::Game::resolveMm9AnimatedActorVisualSource(object, resolver, diagnostics, 96);
    REQUIRE(resolved.has_value());
    CHECK(diagnostics.empty());
    CHECK(resolved->source.objectId == "mm9:guberland:object:12");
    CHECK(resolved->source.sourceModel == "MODELS\\BIGFOOT.ABC");
    CHECK(resolved->source.sourceSkin == "SKINS\\BIGFOOT3.DTX");
    CHECK(resolved->source.maxBoneMatrices == 96);
    CHECK(resolved->resolution.modelId == "bigfoot");
    CHECK(resolved->resolution.skinBindingId == "bigfoot_bigfoot3");
    CHECK(resolved->resolution.modelAssetPath.filename() == "bigfoot.glb");
    REQUIRE(resolved->resolution.materialOverrides.size() == 1);
    CHECK(resolved->resolution.materialOverrides[0].runtimeTexture == "skins/bigfoot3.dtx");
}

TEST_CASE("MM9 native actor visual preserves original source model semantics needed by scripts")
{
    const std::filesystem::path modelRoot = sourceRoot() / "assets_dev/worlds/mm9/models";
    if (!std::filesystem::exists(modelRoot / "dragon.glb")
        || !std::filesystem::exists(modelRoot / "dragon.model.yml")
        || !std::filesystem::exists(modelRoot / "model_registry.yml"))
    {
        WARN("MM9 dragon model assets are not present; skipping source semantic validation");
        return;
    }

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(resolver.loadRegistry(modelRoot / "model_registry.yml", errorMessage), errorMessage);

    OpenYAMM::Game::Mm9ScriptedObject object = {};
    object.mapId = "guberland";
    object.objectId = "mm9:guberland:object:212";
    object.sourceObjectIndex = 212;
    object.sourceClass = "Monster";
    object.sourceName = "Dragon King";
    object.sourceModel = "MODELS\\DRAGON.ABC";
    object.sourceSkin = "SKINS\\GREENDRAGONLT.DTX";
    object.modelAsset = "models/dragon.glb";
    object.modelSkinBinding = "dragon_greendragonlt";
    object.visible = true;
    object.solid = true;
    object.rayHit = true;
    object.pickable = true;
    object.movement.flying = true;

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    const std::optional<OpenYAMM::Game::Mm9AnimatedActorResolvedSource> resolved =
        OpenYAMM::Game::resolveMm9AnimatedActorVisualSource(object, resolver, diagnostics);
    REQUIRE(resolved.has_value());
    CHECK(diagnostics.empty());
    CHECK(resolved->source.sourceModel == "MODELS\\DRAGON.ABC");
    CHECK(resolved->source.sourceSkin == "SKINS\\GREENDRAGONLT.DTX");
    CHECK(resolved->source.semanticState == "flying");
    CHECK(resolved->resolution.modelId == "dragon");
    CHECK(resolved->resolution.skinBindingId == "dragon_greendragonlt");
    REQUIRE(resolved->resolution.normalizedSourceSkins.size() == 1);
    CHECK(resolved->resolution.normalizedSourceSkins[0] == "skins/greendragonlt.dtx");
    REQUIRE(resolved->resolution.materialOverrides.size() == 1);
    CHECK(resolved->resolution.materialOverrides[0].runtimeTexture == "skins/greendragonlt.dtx");

    OpenYAMM::Game::AnimatedModelAsset asset = loadMm9ResolvedModel(resolved->resolution);
    CHECK(asset.lod.valid);
    CHECK(asset.lod.exportedIndex == 0);
    REQUIRE(asset.lod.distances.size() == 2);
    CHECK(asset.lod.distances[0] == doctest::Approx(3840.0f));
    CHECK(asset.findSocketIndex("RangeAttack").has_value());
    CHECK(asset.findSocketIndex("Jaw").has_value());

    const OpenYAMM::Game::AnimatedModelClip *pBreathAttack = asset.findClip("Rattack2");
    REQUIRE(pBreathAttack != nullptr);
    CHECK(pBreathAttack->name == "Rattack2");
    CHECK(clipHasEventContaining(*pBreathAttack, "HeadFollowPause"));
    CHECK(clipHasEventContaining(*pBreathAttack, "BreathAttack"));
    CHECK(clipHasEventContaining(*pBreathAttack, "HeadFollowResume"));

    const std::vector<OpenYAMM::Game::AnimatedModelEvent> resumeEvents =
        OpenYAMM::Game::animatedModelEventsInInterval(*pBreathAttack, 1.9f, 2.0f, false);
    REQUIRE(resumeEvents.size() == 1);
    CHECK(resumeEvents[0].key.find("HeadFollowResume") != std::string::npos);

    OpenYAMM::Game::Mm9AnimatedActorVisualSource source = resolved->source;
    source.requestedClip = "Rattack2";
    source.semanticState = "ranged_attack";

    OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
    REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(
        source,
        resolved->resolution,
        asset,
        visual));
    CHECK(visual.objectId == "mm9:guberland:object:212");
    CHECK(visual.sourceObjectIndex == 212);
    CHECK(visual.sourceClass == "Monster");
    CHECK(visual.sourceName == "Dragon King");
    CHECK(visual.sourceModel == "MODELS\\DRAGON.ABC");
    CHECK(visual.sourceSkin == "SKINS\\GREENDRAGONLT.DTX");
    CHECK(visual.currentClipName == "Rattack2");
    CHECK(visual.semanticState == "ranged_attack");
    CHECK(visual.skinBindingId == "dragon_greendragonlt");
    CHECK(visual.renderPrepCache.drawItems.size() == asset.primitives.size());
    CHECK(visual.renderPrepCache.drawItems.front().texture == "skins/greendragonlt.dtx");
    CHECK(OpenYAMM::Game::findMm9AnimatedActorSocketTransform(visual, "RangeAttack").has_value());
    CHECK(OpenYAMM::Game::findMm9AnimatedActorWorldSocketTransform(visual, "RangeAttack").has_value());

    const std::optional<OpenYAMM::Game::Mm9AnimatedActorPickIdentity> pickIdentity =
        OpenYAMM::Game::mm9AnimatedActorPickIdentity(visual);
    REQUIRE(pickIdentity.has_value());
    CHECK(pickIdentity->objectId == "mm9:guberland:object:212");
    CHECK(pickIdentity->sourceClass == "Monster");
    CHECK(pickIdentity->sourceName == "Dragon King");
}

TEST_CASE("MM9 animated actor binding reports scripted object context for missing model and skin")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path worldRoot = temporaryRoot / "assets_dev" / "worlds" / "mm9";
    const std::filesystem::path registryPath = worldRoot / "models" / "model_registry.yml";

    writeTextFile(
        registryPath,
        R"(
schema: openyamm.mm9.model_registry.v2
world: mm9
models:
- model_id: bigfoot
  roles: [actor_model]
  source_model: models/bigfoot.abc
  model_asset: models/bigfoot.glb
  model_sidecar: models/bigfoot.model.yml
  source_skins: [skins/bigfoot1.dtx]
  skin_bindings:
  - id: bigfoot_bigfoot1
    source_skins: [skins/bigfoot1.dtx]
)");

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(resolver.loadRegistry(registryPath, errorMessage), errorMessage);

    OpenYAMM::Game::Mm9ScriptedObject object = {};
    object.mapId = "guberland";
    object.objectId = "mm9:guberland:object:77";
    object.sourceObjectIndex = 77;
    object.sourceClass = "Monster";
    object.sourceName = "MissingYeti";
    object.sourceModel = "MODELS\\MISSING.ABC";
    object.sourceSkin = "SKINS\\BIGFOOT1.DTX";

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    CHECK_FALSE(OpenYAMM::Game::resolveMm9AnimatedActorVisualSource(
        object,
        resolver,
        diagnostics).has_value());
    REQUIRE(diagnostics.size() == 2);
    CHECK(diagnostics[0].error);
    CHECK(diagnostics[0].message.find("Filename") != std::string::npos);
    CHECK(diagnostics[0].message.find("MODELS\\MISSING.ABC") != std::string::npos);
    CHECK(diagnostics[1].error);
    CHECK(diagnostics[1].message.find("object_id=mm9:guberland:object:77") != std::string::npos);
    CHECK(diagnostics[1].message.find("source_object_index=77") != std::string::npos);
    CHECK(diagnostics[1].message.find("MODELS\\MISSING.ABC") != std::string::npos);

    object.sourceModel = "MODELS\\BIGFOOT.ABC";
    object.sourceSkin = "SKINS\\UNKNOWN.DTX";
    diagnostics.clear();
    CHECK_FALSE(OpenYAMM::Game::resolveMm9AnimatedActorVisualSource(
        object,
        resolver,
        diagnostics).has_value());
    REQUIRE(diagnostics.size() == 2);
    CHECK(diagnostics[0].error);
    CHECK(diagnostics[0].message.find("Skin") != std::string::npos);
    CHECK(diagnostics[0].message.find("SKINS\\UNKNOWN.DTX") != std::string::npos);
    CHECK(diagnostics[1].error);
    CHECK(diagnostics[1].message.find("object_id=mm9:guberland:object:77") != std::string::npos);
    CHECK(diagnostics[1].message.find("source_name=MissingYeti") != std::string::npos);
    CHECK(diagnostics[1].message.find("SKINS\\UNKNOWN.DTX") != std::string::npos);

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("MM9 scripted object movement maps to native animated actor semantic clips")
{
    OpenYAMM::Game::Mm9ScriptedObject object = {};
    CHECK(OpenYAMM::Game::mm9AnimatedActorSemanticStateForScriptedObject(object) == "idle");

    OpenYAMM::Game::AnimatedModelAsset asset = {};
    asset.nodes.push_back(OpenYAMM::Game::AnimatedModelNode{});
    asset.clips.push_back(makeTranslationClip("stand", 0.0f));
    OpenYAMM::Game::Mm9AnimatedModelResolution resolution = {};
    resolution.modelId = "stationary";
    OpenYAMM::Game::Mm9AnimatedActorVisual stationaryVisual = {};
    const OpenYAMM::Game::Mm9AnimatedActorVisualSource stationarySource =
        OpenYAMM::Game::makeMm9AnimatedActorVisualSource(object);
    REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(
        stationarySource,
        resolution,
        asset,
        stationaryVisual));
    CHECK(stationaryVisual.currentClipName == "stand");

    object.movement.walking = true;
    CHECK(OpenYAMM::Game::mm9AnimatedActorSemanticStateForScriptedObject(object) == "walking");

    object.movement.running = true;
    CHECK(OpenYAMM::Game::mm9AnimatedActorSemanticStateForScriptedObject(object) == "running");

    object.movement.flying = true;
    CHECK(OpenYAMM::Game::mm9AnimatedActorSemanticStateForScriptedObject(object) == "flying");
}

TEST_CASE("Guberland MM9 scripted objects resolve native animated model assets without billboard sidecars")
{
    const std::filesystem::path assetRoot = sourceRoot() / "assets_dev";
    const std::filesystem::path scenePath = assetRoot / "worlds/mm9/maps/guberland.scene.yml";
    const std::filesystem::path eventsPath = assetRoot / "worlds/mm9/maps/guberland.events.yml";
    const std::filesystem::path registryPath = assetRoot / "worlds/mm9/models/model_registry.yml";
    if (!std::filesystem::exists(scenePath)
        || !std::filesystem::exists(eventsPath)
        || !std::filesystem::exists(registryPath))
    {
        WARN("MM9 Guberland generated assets are not present; skipping native animated actor resolution validation");
        return;
    }

    std::string errorMessage;
    const std::optional<std::string> sceneText = readTextFile(scenePath);
    REQUIRE(sceneText.has_value());
    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<OpenYAMM::Game::OutdoorSceneData> sceneData =
        sceneLoader.loadFromText(*sceneText, errorMessage);
    REQUIRE_MESSAGE(sceneData.has_value(), errorMessage);

    const std::optional<std::string> eventsText = readTextFile(eventsPath);
    REQUIRE(eventsText.has_value());
    OpenYAMM::Game::Mm9EventsYmlLoader eventsLoader = {};
    const std::optional<OpenYAMM::Game::Mm9EventsData> eventsData =
        eventsLoader.loadFromText(*eventsText, errorMessage);
    REQUIRE_MESSAGE(eventsData.has_value(), errorMessage);

    OpenYAMM::Game::Mm9ScriptedObjectRuntime objectRuntime = {};
    REQUIRE(objectRuntime.initialize("guberland", *sceneData, &*eventsData));

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    REQUIRE_MESSAGE(resolver.loadRegistry(registryPath, errorMessage), errorMessage);

    size_t visibleActorObjects = 0;
    size_t datGeneratedActorObjects = 0;
    size_t datGeneratedModelAssetMatches = 0;
    size_t resolvedVisibleActors = 0;
    for (const OpenYAMM::Game::Mm9ScriptedObject &object : objectRuntime.objects())
    {
        if (!object.visible || object.sourceModel.empty())
        {
            continue;
        }

        ++visibleActorObjects;
        std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
        const std::optional<OpenYAMM::Game::Mm9AnimatedActorResolvedSource> resolved =
            OpenYAMM::Game::resolveMm9AnimatedActorVisualSource(object, resolver, diagnostics);
        CAPTURE(object.sourceObjectIndex);
        CAPTURE(object.sourceClass);
        CAPTURE(object.sourceModel);
        CAPTURE(object.sourceSkin);
        REQUIRE(resolved.has_value());
        CHECK(diagnostics.empty());
        CHECK(object.sourceKind == "mm9_dat_object");
        CHECK(object.sourceRef.find("objects/") == 0);
        CHECK(!resolved->source.objectId.empty());
        CHECK(!resolved->resolution.modelId.empty());
        CHECK(std::filesystem::exists(resolved->resolution.modelAssetPath));
        CHECK(std::filesystem::exists(resolved->resolution.modelSidecarPath));

        if (!object.modelAsset.empty())
        {
            ++datGeneratedActorObjects;
            if (!object.modelSkinBinding.empty())
            {
                CHECK(object.modelSkinBinding == resolved->resolution.skinBindingId);
            }
            const std::filesystem::path expectedModelAssetPath =
                (assetRoot / "worlds/mm9" / object.modelAsset).lexically_normal();
            CHECK(resolved->resolution.modelAssetPath.lexically_normal() == expectedModelAssetPath);
            if (resolved->resolution.modelAssetPath.lexically_normal() == expectedModelAssetPath)
            {
                ++datGeneratedModelAssetMatches;
            }
        }

        ++resolvedVisibleActors;
    }

    CHECK(visibleActorObjects > 0);
    CHECK(resolvedVisibleActors == visibleActorObjects);
    CHECK(datGeneratedActorObjects > 0);
    CHECK(datGeneratedModelAssetMatches == datGeneratedActorObjects);
}

TEST_CASE("Guberland MM9 resolved visible actors initialize native visual render prep")
{
    const std::filesystem::path assetRoot = sourceRoot() / "assets_dev";
    const std::filesystem::path scenePath = assetRoot / "worlds/mm9/maps/guberland.scene.yml";
    const std::filesystem::path eventsPath = assetRoot / "worlds/mm9/maps/guberland.events.yml";
    const std::filesystem::path registryPath = assetRoot / "worlds/mm9/models/model_registry.yml";
    if (!std::filesystem::exists(scenePath)
        || !std::filesystem::exists(eventsPath)
        || !std::filesystem::exists(registryPath))
    {
        WARN("MM9 Guberland generated assets are not present; skipping native animated actor visual validation");
        return;
    }

    std::string errorMessage;
    const std::optional<std::string> sceneText = readTextFile(scenePath);
    REQUIRE(sceneText.has_value());
    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<OpenYAMM::Game::OutdoorSceneData> sceneData =
        sceneLoader.loadFromText(*sceneText, errorMessage);
    REQUIRE_MESSAGE(sceneData.has_value(), errorMessage);

    const std::optional<std::string> eventsText = readTextFile(eventsPath);
    REQUIRE(eventsText.has_value());
    OpenYAMM::Game::Mm9EventsYmlLoader eventsLoader = {};
    const std::optional<OpenYAMM::Game::Mm9EventsData> eventsData =
        eventsLoader.loadFromText(*eventsText, errorMessage);
    REQUIRE_MESSAGE(eventsData.has_value(), errorMessage);

    OpenYAMM::Game::Mm9ScriptedObjectRuntime objectRuntime = {};
    REQUIRE(objectRuntime.initialize("guberland", *sceneData, &*eventsData));

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    REQUIRE_MESSAGE(resolver.loadRegistry(registryPath, errorMessage), errorMessage);

    std::unordered_map<std::string, OpenYAMM::Game::AnimatedModelAsset> assetCache;
    size_t initializedVisibleActors = 0;
    for (const OpenYAMM::Game::Mm9ScriptedObject &object : objectRuntime.objects())
    {
        if (!object.visible || object.sourceModel.empty())
        {
            continue;
        }

        std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
        const std::optional<OpenYAMM::Game::Mm9AnimatedActorResolvedSource> resolved =
            OpenYAMM::Game::resolveMm9AnimatedActorVisualSource(object, resolver, diagnostics);
        REQUIRE(resolved.has_value());

        const std::string assetKey = resolved->resolution.modelAssetPath.string();
        if (assetCache.find(assetKey) == assetCache.end())
        {
            OpenYAMM::Game::AnimatedModelAsset asset = loadMm9ResolvedModel(resolved->resolution);
            CHECK_FALSE(asset.hasErrors());
            assetCache.emplace(assetKey, std::move(asset));
        }

        const OpenYAMM::Game::AnimatedModelAsset &asset = assetCache.at(assetKey);
        OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
        CAPTURE(object.sourceObjectIndex);
        CAPTURE(object.sourceClass);
        CAPTURE(object.sourceModel);
        CAPTURE(object.sourceSkin);
        REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(
            resolved->source,
            resolved->resolution,
            asset,
            visual));
        CHECK(visual.visible);
        CHECK(!visual.currentClipName.empty());
        CHECK(!visual.renderPrepCache.drawItems.empty());
        CHECK(visual.worldBounds.valid);
        CHECK(visual.poseCache.globalTransforms.size() == asset.nodes.size());
        CHECK_FALSE(visual.renderPrepCache.counters.skinnedDrawCalls == 0);
        ++initializedVisibleActors;
    }

    CHECK(initializedVisibleActors > 0);
}

TEST_CASE("MM9 visible stationary dialogue actor initializes native visual and opens generated dialogue")
{
    const std::filesystem::path assetRoot = sourceRoot() / "assets_dev";
    const std::filesystem::path scenePath = assetRoot / "worlds/mm9/maps/afterworld.scene.yml";
    const std::filesystem::path eventsPath = assetRoot / "worlds/mm9/maps/afterworld.events.yml";
    const std::filesystem::path registryPath = assetRoot / "worlds/mm9/models/model_registry.yml";
    if (!std::filesystem::exists(scenePath)
        || !std::filesystem::exists(eventsPath)
        || !std::filesystem::exists(registryPath))
    {
        WARN("MM9 Afterworld generated assets are not present; skipping native dialogue actor validation");
        return;
    }

    std::string errorMessage;
    const std::optional<std::string> sceneText = readTextFile(scenePath);
    REQUIRE(sceneText.has_value());
    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<OpenYAMM::Game::OutdoorSceneData> sceneData =
        sceneLoader.loadFromText(*sceneText, errorMessage);
    REQUIRE_MESSAGE(sceneData.has_value(), errorMessage);

    const std::optional<std::string> eventsText = readTextFile(eventsPath);
    REQUIRE(eventsText.has_value());
    OpenYAMM::Game::Mm9EventsYmlLoader eventsLoader = {};
    const std::optional<OpenYAMM::Game::Mm9EventsData> eventsData =
        eventsLoader.loadFromText(*eventsText, errorMessage);
    REQUIRE_MESSAGE(eventsData.has_value(), errorMessage);

    OpenYAMM::Game::Mm9ScriptedObjectRuntime objectRuntime = {};
    REQUIRE(objectRuntime.initialize("afterworld", *sceneData, &*eventsData));

    const OpenYAMM::Game::Mm9ScriptedObject *pSkraelosObject = nullptr;
    for (const OpenYAMM::Game::Mm9ScriptedObject &object : objectRuntime.objects())
    {
        if (object.sourceObjectIndex == 94)
        {
            pSkraelosObject = &object;
            break;
        }
    }
    REQUIRE(pSkraelosObject != nullptr);
    CHECK(pSkraelosObject->objectId == "mm9:afterworld:object:94");
    CHECK(pSkraelosObject->sourceKind == "mm9_dat_object");
    CHECK(pSkraelosObject->sourceRef == "objects/94");
    CHECK(pSkraelosObject->sourceName == "Skraelos0");
    CHECK(pSkraelosObject->sourceModel == "models\\Skraelos.abc");
    CHECK(pSkraelosObject->modelAsset == "models/skraelos.glb");
    CHECK(pSkraelosObject->scriptName == "NPC336.scr");
    CHECK(pSkraelosObject->scriptParams == "Afterworld");
    CHECK(pSkraelosObject->visible);
    CHECK(pSkraelosObject->pickable);
    CHECK(pSkraelosObject->movement.stationary);
    CHECK(pSkraelosObject->movement.rooted);

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    REQUIRE_MESSAGE(resolver.loadRegistry(registryPath, errorMessage), errorMessage);

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    const std::optional<OpenYAMM::Game::Mm9AnimatedActorResolvedSource> resolved =
        OpenYAMM::Game::resolveMm9AnimatedActorVisualSource(*pSkraelosObject, resolver, diagnostics);
    REQUIRE(resolved.has_value());
    CHECK(diagnostics.empty());
    CHECK(resolved->resolution.modelId == "skraelos");
    CHECK(resolved->resolution.skinBindingId == "skraelos_skraelos");
    CHECK(resolved->resolution.modelAssetPath.lexically_normal()
        == (assetRoot / "worlds/mm9/models/skraelos.glb").lexically_normal());
    REQUIRE(resolved->resolution.materialOverrides.size() == 1);
    CHECK(resolved->resolution.materialOverrides[0].runtimeTexture == "skins/skraelos.dtx");

    const OpenYAMM::Game::AnimatedModelAsset asset = loadMm9ResolvedModel(resolved->resolution);
    OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
    REQUIRE(OpenYAMM::Game::initializeMm9AnimatedActorVisual(
        resolved->source,
        resolved->resolution,
        asset,
        visual));
    CHECK(visual.visible);
    CHECK(visual.pickable);
    CHECK(visual.currentClipName == "stand");
    CHECK(!visual.renderPrepCache.drawItems.empty());
    CHECK(visual.worldBounds.valid);

    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    REQUIRE(assetFileSystem.initialize(
        sourceRoot(),
        assetRoot,
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9DialoguePackage package = {};
    REQUIRE(OpenYAMM::Game::loadMm9DialoguePackage(assetFileSystem, package));
    REQUIRE(package.errors.empty());

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    OpenYAMM::Game::Mm9InteractionObjectBinding binding = {};
    binding.mapId = pSkraelosObject->mapId;
    binding.objectId = pSkraelosObject->objectId;
    binding.sourceObjectIndex = static_cast<int32_t>(pSkraelosObject->sourceObjectIndex);
    binding.sourceClass = pSkraelosObject->sourceClass;
    binding.sourceName = pSkraelosObject->sourceName;
    binding.visualId = pSkraelosObject->visualId;
    binding.scriptName = pSkraelosObject->scriptName;
    binding.scriptParams = pSkraelosObject->scriptParams;
    binding.hitPoint = {pSkraelosObject->x, pSkraelosObject->y, pSkraelosObject->z};
    binding.distance = 64.0f;

    const OpenYAMM::Game::GameplayWorldHit hit =
        OpenYAMM::Game::buildMm9ScriptedObjectWorldHit(binding);
    const OpenYAMM::Game::Mm9ObjectActivationResult activation = scriptRuntime.activateObject(hit);
    REQUIRE(activation.activated);
    CHECK(activation.ranScript);
    CHECK(activation.openedDialogue);
    CHECK(activation.error.empty());
    CHECK(dialogueRuntime.currentRudeId() == 336);
    CHECK(dialogueRuntime.owner().mapId == "afterworld");
    CHECK(dialogueRuntime.owner().objectIndex == 94);
    CHECK(dialogueRuntime.owner().objectName == "Skraelos0");
    CHECK(dialogueRuntime.owner().scriptName == "NPC336.scr");
}
