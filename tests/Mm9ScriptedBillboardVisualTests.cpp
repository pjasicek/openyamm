#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/maps/Mm9EventsYml.h"
#include "game/mm9/Mm9ScriptedObjectRuntime.h"
#include "game/mm9/Mm9ScriptedBillboardVisuals.h"
#include "game/maps/OutdoorSceneYml.h"

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>

namespace
{
std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_mm9_billboard_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

void writeBinaryFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file.write(contents.data(), static_cast<std::streamsize>(contents.size()));
}
}

TEST_CASE("MM9 scripted billboard visuals load generated asset metadata and frame references")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    const std::filesystem::path visualRoot =
        assetRoot / "worlds" / "mm9" / "rendering" / "scripted_billboards";

    writeBinaryFile(visualRoot / "frames" / "mm9_guard" / "idle.png", "not-a-real-png");
    writeTextFile(
        visualRoot / "mm9_guard.yml",
        R"(
schema: openyamm.mm9.scripted_billboard_visual.v1
visual_id: mm9_guard
source_model: models/guard.abc
source_glb: assets_dev/worlds/mm9/models/actors/guard/variants/guard/guard.glb
source_skins: [skins/guard3.dtx, skins/guardpole2.dtx]
variant_id: guard_guard3_guardpole2
model_id: guard
angle_count: 8
angle_names: [front, front_right, right, back_right, back, back_left, left, front_left]
clips:
  stand:
    semantic: idle
    angles: 8
    duration_ms: 1000
    frames:
      - texture: mm9_guard_stand_000
        duration_ms: 1000
        angle: front
        path: frames/mm9_guard/idle.png
      - texture: mm9_guard_stand_001
        duration_ms: 1000
        angle: right
        path: frames/mm9_guard/idle.png
  idle:
    semantic: idle
    angles: 8
    duration_ms: 1000
    source_clip: stand
    frames:
      - texture: mm9_guard_stand_000
        duration_ms: 250
        angle: front
        path: frames/mm9_guard/idle.png
        anchor_x: 41.5
        anchor_y: 148
      - texture: mm9_guard_stand_001
        duration_ms: 750
        angle: front
        path: frames/mm9_guard/idle.png
      - texture: mm9_guard_stand_right
        duration_ms: 1000
        angle: right
        path: frames/mm9_guard/idle.png
collision:
  radius: 116
  height: 188
  vertical_offset: -4
  anchor: feet
  source: glb_bounds
used_by:
  - map: guberland
    object_id: mm9:guberland:object:12
    source_object_index: 12
    source_class: Guard
    source_name: DockGuard
    script_name: guard.scr
    script_params: patrol=1
)");

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        temporaryRoot,
        assetRoot,
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9ScriptedBillboardVisualSet visualSet = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(visualSet.loadFromAssetFileSystem(assetFileSystem, errorMessage), errorMessage);

    REQUIRE(visualSet.visuals().size() == 1);
    const OpenYAMM::Game::Mm9ScriptedBillboardVisual *pVisual = visualSet.findVisual("MM9_GUARD");
    REQUIRE(pVisual != nullptr);
    CHECK(pVisual->visualId == "mm9_guard");
    CHECK(pVisual->sourceModel == "models/guard.abc");
    CHECK(pVisual->sourceSkins.size() == 2);
    CHECK(pVisual->collision.radius == 116);
    CHECK(pVisual->collision.height == 188);
    REQUIRE(pVisual->usedBy.size() == 1);
    CHECK(pVisual->usedBy[0].sourceClass == "Guard");
    CHECK(pVisual->usedBy[0].scriptName == "guard.scr");

    const OpenYAMM::Game::Mm9ScriptedBillboardFrame *pIdleFrame = visualSet.findFirstIdleFrame(*pVisual);
    REQUIRE(pIdleFrame != nullptr);
    CHECK(pIdleFrame->textureName == "mm9_guard_stand_000");
    CHECK(pIdleFrame->path == "frames/mm9_guard/idle.png");
    CHECK(pIdleFrame->anchorX == doctest::Approx(41.5f));
    CHECK(pIdleFrame->anchorY == doctest::Approx(148.0f));

    const OpenYAMM::Game::Mm9ScriptedBillboardClip *pResolvedClip =
        visualSet.resolveClip(*pVisual, "stand", "idle");
    REQUIRE(pResolvedClip != nullptr);
    CHECK(pResolvedClip->name == "stand");

    const OpenYAMM::Game::Mm9ScriptedBillboardFrame *pAngleFrame =
        visualSet.resolveFrame(*pVisual, "stand", "idle", "right", 0);
    REQUIRE(pAngleFrame != nullptr);
    CHECK(pAngleFrame->textureName == "mm9_guard_stand_001");

    const OpenYAMM::Game::Mm9ScriptedBillboardFrame *pSemanticFallbackFrame =
        visualSet.resolveFrame(*pVisual, "missing_clip", "idle", "right", 0);
    REQUIRE(pSemanticFallbackFrame != nullptr);
    CHECK(pSemanticFallbackFrame->textureName == "mm9_guard_stand_001");

    const OpenYAMM::Game::Mm9ScriptedBillboardFrame *pAnimatedFrame =
        visualSet.resolveFrame(*pVisual, "idle", "idle", "front", 250);
    REQUIRE(pAnimatedFrame != nullptr);
    CHECK(pAnimatedFrame->textureName == "mm9_guard_stand_001");

    OpenYAMM::Game::OutdoorSceneModelInstance modelInstance = {};
    modelInstance.sourceObjectIndex = 12;
    modelInstance.sourceClass = "Guard";
    modelInstance.sourceName = "DockGuard";
    modelInstance.sourceModel = "models/guard.abc";
    modelInstance.sourceSkin = "skins/guard3.dtx;skins/guardpole2.dtx";

    const std::optional<std::string> visualId =
        visualSet.resolveVisualIdForModelInstance("guberland", modelInstance);
    REQUIRE(visualId.has_value());
    CHECK(*visualId == "mm9_guard");

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("MM9 scripted billboard visual loader rejects missing generated frame files")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    const std::filesystem::path visualRoot =
        assetRoot / "worlds" / "mm9" / "rendering" / "scripted_billboards";

    writeTextFile(
        visualRoot / "mm9_missing.yml",
        R"(
schema: openyamm.mm9.scripted_billboard_visual.v1
visual_id: mm9_missing
source_model: models/missing.abc
source_glb: assets_dev/worlds/mm9/models/actors/missing/missing.glb
source_skins: []
variant_id: missing
model_id: missing
angle_count: 8
angle_names: [front]
clips:
  idle:
    semantic: idle
    angles: 8
    duration_ms: 1000
    frames:
      - texture: mm9_missing_idle
        duration_ms: 1000
        angle: front
        path: frames/mm9_missing/missing.png
)");

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        temporaryRoot,
        assetRoot,
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9ScriptedBillboardVisualSet visualSet = {};
    std::string errorMessage;
    CHECK(!visualSet.loadFromAssetFileSystem(assetFileSystem, errorMessage));
    CHECK(errorMessage.find("frame asset is missing") != std::string::npos);

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("MM9 scripted object runtime preserves event sidecar identity and runtime state")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    const std::filesystem::path visualRoot =
        assetRoot / "worlds" / "mm9" / "rendering" / "scripted_billboards";

    writeBinaryFile(visualRoot / "frames" / "mm9_guard" / "idle.png", "not-a-real-png");
    writeTextFile(
        visualRoot / "mm9_guard.yml",
        R"(
schema: openyamm.mm9.scripted_billboard_visual.v1
visual_id: mm9_guard
source_model: models/guard.abc
source_glb: assets_dev/worlds/mm9/models/actors/guard/variants/guard/guard.glb
source_skins: [skins/guard3.dtx]
variant_id: guard_guard3
model_id: guard
angle_count: 1
angle_names: [front]
clips:
  idle:
    semantic: idle
    angles: 1
    duration_ms: 1000
    frames:
      - texture: mm9_guard_idle
        duration_ms: 1000
        angle: front
        path: frames/mm9_guard/idle.png
collision:
  radius: 44
  height: 188
  vertical_offset: -4
  anchor: feet
  source: glb_bounds
used_by:
  - map: guberland
    object_id: mm9:guberland:object:42
    source_object_index: 42
    source_class: Guard
    source_name: DockGuard
    script_name: guard.scr
    script_params: patrol=1
)");

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        temporaryRoot,
        assetRoot,
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9ScriptedBillboardVisualSet visualSet = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(visualSet.loadFromAssetFileSystem(assetFileSystem, errorMessage), errorMessage);

    OpenYAMM::Game::OutdoorSceneData sceneData = {};
    OpenYAMM::Game::OutdoorSceneModelInstance modelInstance = {};
    modelInstance.instanceId = "mm9:guberland:object:42";
    modelInstance.sourceObjectIndex = 42;
    modelInstance.sourceClass = "Guard";
    modelInstance.sourceName = "SceneGuard";
    modelInstance.sourceModel = "models/guard.abc";
    modelInstance.sourceSkin = "skins/guard3.dtx";
    modelInstance.x = 100;
    modelInstance.y = 200;
    modelInstance.z = 300;
    sceneData.modelInstances.push_back(modelInstance);

    OpenYAMM::Game::Mm9EventsData eventsData = {};
    OpenYAMM::Game::Mm9EventObject eventObject = {};
    eventObject.objectId = "mm9:guberland:object:42";
    eventObject.sourceObjectIndex = 42;
    eventObject.sourceClass = "FireDragonFly";
    eventObject.sourceName = "EventGuard";
    eventObject.rawObjectRef = "guberland.raw_objects.yml#objects[42]";
    eventObject.rawPropertyCount = 9;
    eventObject.rawProperties.push_back(
        OpenYAMM::Game::Mm9EventObject::RawPropertyRef{
            .propertyIndex = 0,
            .name = "Filename",
            .decoded = true,
            .code = 0,
            .flags = 0,
            .rawRef = "properties[0]",
        });
    eventObject.normalizedProperties["Filename"] = "models\\Guard.ABC";
    eventObject.normalizedProperties["Skin"] = "skins\\guard3.dtx";
    eventObject.normalizedProperties["ScriptName"] = "event_guard.scr";
    eventObject.normalizedProperties["ScriptParams"] = "watch=1";
    eventObject.normalizedProperties["Visible"] = "1";
    eventObject.normalizedProperties["Solid"] = "0";
    eventObject.normalizedProperties["Rayhit"] = "1";
    eventObject.normalizedProperties["NeedsTick"] = "1";
    eventObject.normalizedProperties["Scale"] = "1.5";
    eventObject.normalizedProperties["MoveToFloor"] = "0";
    eventObject.normalizedProperties["WanderON"] = "1";
    eventObject.normalizedProperties["WanderPathName"] = "guard_patrol";
    eventObject.normalizedProperties["WanderLeash"] = "128";
    eventObject.normalizedProperties["RunawayChance"] = "25";
    eventObject.normalizedProperties["Speed"] = "350";
    eventObject.normalizedProperties["ClosingSpeed"] = "500";
    eventObject.normalizedProperties["AnimationSpeed"] = "1.25";
    eventsData.objects.push_back(eventObject);

    OpenYAMM::Game::Mm9ScriptedObjectRuntime runtime = {};
    REQUIRE(runtime.initialize("guberland", sceneData, visualSet, &eventsData));
    REQUIRE(runtime.objects().size() == 1);

    const OpenYAMM::Game::Mm9ScriptedObject &object = runtime.objects()[0];
    CHECK(object.objectId == "mm9:guberland:object:42");
    CHECK(object.sourceObjectIndex == 42);
    CHECK(object.sourceClass == "FireDragonFly");
    CHECK(object.sourceName == "EventGuard");
    CHECK(object.sourceModel == "models\\Guard.ABC");
    CHECK(object.sourceSkin == "skins\\guard3.dtx");
    CHECK(object.scriptName == "event_guard.scr");
    CHECK(object.scriptParams == "watch=1");
    CHECK(object.rawObjectRef == "guberland.raw_objects.yml#objects[42]");
    CHECK(object.rawPropertyCount == 9);
    REQUIRE(object.rawProperties.size() == 1);
    CHECK(object.rawProperties[0].rawRef == "properties[0]");
    CHECK(object.visible);
    CHECK(!object.solid);
    CHECK(object.rayHit);
    CHECK(object.needsTick);
    CHECK(object.pickable);
    CHECK(object.scale == doctest::Approx(1.5f));
    CHECK(object.visualId == "mm9_guard");
    CHECK(object.currentClip == "idle");
    CHECK(object.movement.flying);
    CHECK(object.movement.fleeing);
    CHECK(object.movement.running);
    CHECK(object.movement.scriptedPath);
    CHECK_FALSE(object.movement.moveToFloor);
    CHECK_FALSE(object.movement.stationary);
    CHECK(object.movementState == "fleeing");
    CHECK(object.movement.wanderPathName == "guard_patrol");
    CHECK(object.movement.wanderLeash == doctest::Approx(128.0f));
    CHECK(object.movement.runawayChance == doctest::Approx(25.0f));
    CHECK(object.movement.speed == doctest::Approx(350.0f));
    CHECK(object.movement.closingSpeed == doctest::Approx(500.0f));
    CHECK(object.movement.animationSpeed == doctest::Approx(1.25f));
    CHECK(object.radius == doctest::Approx(44.0f));
    CHECK(object.height == doctest::Approx(188.0f));
    CHECK(object.verticalOffset == doctest::Approx(-4.0f));

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("Generated Guberland MM9 scripted billboard visuals resolve from scene model instances")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetRoot = sourceRoot / "assets_dev";

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        assetRoot,
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9ScriptedBillboardVisualSet visualSet = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(
        visualSet.loadFromAssetFileSystem(
            assetFileSystem,
            errorMessage,
            OpenYAMM::Game::Mm9ScriptedBillboardVisualRoot,
            false),
        errorMessage);

    const std::optional<std::string> sceneText =
        assetFileSystem.readTextFile("worlds/mm9/maps/guberland.scene.yml");
    REQUIRE(sceneText.has_value());

    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<OpenYAMM::Game::OutdoorSceneData> sceneData =
        sceneLoader.loadFromText(*sceneText, errorMessage);
    REQUIRE_MESSAGE(sceneData.has_value(), errorMessage);

    size_t usedByGuberlandCount = 0;
    size_t resolvedUsedByGuberlandCount = 0;

    for (const OpenYAMM::Game::Mm9ScriptedBillboardVisual &visual : visualSet.visuals())
    {
        for (const OpenYAMM::Game::Mm9ScriptedBillboardUse &usedBy : visual.usedBy)
        {
            if (usedBy.mapId != "guberland")
            {
                continue;
            }

            ++usedByGuberlandCount;
            bool resolved = false;

            for (const OpenYAMM::Game::OutdoorSceneModelInstance &modelInstance : sceneData->modelInstances)
            {
                if (modelInstance.sourceObjectIndex != usedBy.sourceObjectIndex)
                {
                    continue;
                }

                const std::optional<std::string> resolvedVisualId =
                    visualSet.resolveVisualIdForModelInstance("guberland", modelInstance);
                resolved = resolvedVisualId.has_value() && *resolvedVisualId == visual.visualId;
                break;
            }

            CHECK_MESSAGE(resolved, usedBy.objectId.c_str());
            resolvedUsedByGuberlandCount += resolved ? 1 : 0;
        }
    }

    CHECK(usedByGuberlandCount == 64);
    CHECK(resolvedUsedByGuberlandCount == usedByGuberlandCount);
}

TEST_CASE("Guberland MM9 scripted object runtime builds visible pickable billboard objects from sidecars")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetRoot = sourceRoot / "assets_dev";

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        assetRoot,
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9ScriptedBillboardVisualSet visualSet = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(
        visualSet.loadFromAssetFileSystem(
            assetFileSystem,
            errorMessage,
            OpenYAMM::Game::Mm9ScriptedBillboardVisualRoot,
            false),
        errorMessage);

    const std::optional<std::string> sceneText =
        assetFileSystem.readTextFile("worlds/mm9/maps/guberland.scene.yml");
    REQUIRE(sceneText.has_value());

    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<OpenYAMM::Game::OutdoorSceneData> sceneData =
        sceneLoader.loadFromText(*sceneText, errorMessage);
    REQUIRE_MESSAGE(sceneData.has_value(), errorMessage);

    const std::optional<std::string> eventsText =
        assetFileSystem.readTextFile("worlds/mm9/maps/guberland.events.yml");
    REQUIRE(eventsText.has_value());

    OpenYAMM::Game::Mm9EventsYmlLoader eventsLoader = {};
    const std::optional<OpenYAMM::Game::Mm9EventsData> eventsData =
        eventsLoader.loadFromText(*eventsText, errorMessage);
    REQUIRE_MESSAGE(eventsData.has_value(), errorMessage);

    OpenYAMM::Game::Mm9ScriptedObjectRuntime runtime = {};
    REQUIRE(runtime.initialize("guberland", *sceneData, visualSet, &*eventsData));

    std::unordered_set<size_t> usedByObjectIndices;
    for (const OpenYAMM::Game::Mm9ScriptedBillboardVisual &visual : visualSet.visuals())
    {
        for (const OpenYAMM::Game::Mm9ScriptedBillboardUse &usedBy : visual.usedBy)
        {
            if (usedBy.mapId == "guberland")
            {
                usedByObjectIndices.insert(usedBy.sourceObjectIndex);
            }
        }
    }
    REQUIRE(usedByObjectIndices.size() == 64);

    std::unordered_map<size_t, const OpenYAMM::Game::Mm9ScriptedObject *> objectBySourceIndex;
    for (const OpenYAMM::Game::Mm9ScriptedObject &object : runtime.objects())
    {
        objectBySourceIndex.emplace(object.sourceObjectIndex, &object);
    }

    size_t matchedObjects = 0;
    size_t visiblePickableObjects = 0;
    size_t hiddenObjects = 0;
    size_t flyingObjects = 0;
    size_t groundedObjects = 0;
    size_t stationaryObjects = 0;

    for (size_t sourceObjectIndex : usedByObjectIndices)
    {
        const auto objectIterator = objectBySourceIndex.find(sourceObjectIndex);
        REQUIRE_MESSAGE(
            objectIterator != objectBySourceIndex.end(),
            ("missing runtime object " + std::to_string(sourceObjectIndex)).c_str());

        const OpenYAMM::Game::Mm9ScriptedObject &object = *objectIterator->second;
        CHECK_FALSE(object.missingVisual);
        CHECK(visualSet.findVisual(object.visualId) != nullptr);
        CHECK(!object.objectId.empty());
        CHECK(object.rawObjectRef.find("guberland.raw_objects.yml") != std::string::npos);
        CHECK(!object.rawProperties.empty());
        CHECK(object.normalizedProperties.find("Filename") != object.normalizedProperties.end());
        CHECK(!object.sourceModel.empty());
        CHECK(object.rayHit);
        CHECK(object.radius > 0.0f);
        CHECK(object.height > 0.0f);
        CHECK(!object.currentClip.empty());
        CHECK(!object.movementState.empty());

        if (object.movement.flying)
        {
            ++flyingObjects;
        }
        if (object.movement.moveToFloor)
        {
            ++groundedObjects;
        }
        if (object.movement.stationary)
        {
            ++stationaryObjects;
        }

        if (object.visible)
        {
            CHECK(object.pickable);
            ++visiblePickableObjects;
        }
        else
        {
            CHECK_FALSE(object.pickable);
            ++hiddenObjects;
        }

        ++matchedObjects;
    }

    CHECK(matchedObjects == usedByObjectIndices.size());
    CHECK(visiblePickableObjects == 62);
    CHECK(hiddenObjects == 2);
    CHECK(flyingObjects >= 20);
    CHECK(groundedObjects >= 30);
    CHECK(stationaryObjects >= 40);
}
