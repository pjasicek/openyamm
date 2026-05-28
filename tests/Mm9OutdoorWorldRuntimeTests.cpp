#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/app/GameSession.h"
#include "game/events/EventDialogContent.h"
#include "game/mm9/Mm9DialoguePackage.h"
#include "game/mm9/Mm9InteractionRouting.h"
#include "game/mm9/Mm9ScriptRuntime.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorMovementDriver.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/tables/ItemTable.h"
#include "tools/Mm9RudeTranscode.h"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <algorithm>
#include <string>
#include <system_error>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorGameViewMm9TestAccess
{
    static void bindHeadlessWorldInteraction(
        OutdoorGameView &view,
        const Engine::AssetFileSystem &assetFileSystem,
        OutdoorPartyRuntime &partyRuntime,
        OutdoorWorldRuntime &worldRuntime,
        const OutdoorMapData &outdoorMapData)
    {
        view.m_pAssetFileSystem = &assetFileSystem;
        view.m_pOutdoorPartyRuntime = &partyRuntime;
        view.m_pOutdoorWorldRuntime = &worldRuntime;
        view.m_outdoorMapData = outdoorMapData;
        worldRuntime.bindInteractionView(&view);
    }
};
}

namespace
{
void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    REQUIRE(stream.good());
    stream << contents;
}

std::string rudeRow(
    int32_t rudeId,
    int32_t nodeId,
    int32_t choiceSlot,
    const std::string &prompt,
    const std::string &response,
    int32_t next,
    int32_t requiredKey)
{
    std::vector<std::string> columns = {
        std::to_string(rudeId),
        std::to_string(nodeId),
        std::to_string(choiceSlot),
        prompt,
        response,
        std::to_string(next),
    };
    while (columns.size() < 30)
    {
        columns.push_back("0");
    }
    columns[6] = std::to_string(requiredKey);
    return OpenYAMM::Game::serializeMm9RudeCsvLine(columns) + "\n";
}

std::filesystem::path makeMm9OutdoorRuntimeFixtureRoot()
{
    const int64_t suffix = std::chrono::steady_clock::now().time_since_epoch().count();
    const std::filesystem::path root =
        std::filesystem::temp_directory_path() / ("openyamm_mm9_outdoor_runtime_fixture_"
            + std::to_string(suffix));
    std::error_code error;
    std::filesystem::remove_all(root, error);

    const std::filesystem::path rudeDirectory = root / "extracted/RUDE/RUDE";
    writeTextFile(
        rudeDirectory / "NPC1.rude",
        rudeRow(1, 1, 2, "Locked", "QBit-gated response", -1, 44) +
            rudeRow(1, 1, 1, "Continue", "Go to service node", 2, 0) +
            rudeRow(1, 1, 3, "Bye", "Goodbye", -1, 0));
    writeTextFile(rudeDirectory / "NPCNAME.rude", "1,Test NPC\n");
    writeTextFile(rudeDirectory / "TOPBLURB.rude", "1,Test NPC,Test blurb\n");
    writeTextFile(rudeDirectory / "NPC997.rude", rudeRow(997, 997, 1, "Quest", "Quest text", 0, 0));
    writeTextFile(rudeDirectory / "NPC998.rude", rudeRow(998, 998, 1, "Note", "Note text", 0, 0));
    writeTextFile(rudeDirectory / "NPC999.rude", rudeRow(999, 999, 1, "Award", "Award text", 0, 0));

    const std::filesystem::path scriptsDirectory = root / "extracted/SCRIPTS/SCRIPTS";
    writeTextFile(scriptsDirectory / "globals.inc", "#number TEST_KEY = 44\n");
    writeTextFile(
        scriptsDirectory / "DORUDE.scr",
        "#include globals.inc\n"
        ":OnUse\n"
        "HasKey TEST_KEY\n"
        "DoRude 1\n"
        "OnRudeExit OnRude\n"
        ":OnRude\n"
        "GiveKey 44\n");

    writeTextFile(
        root / "source_maps/testmap.raw_objects.yml",
        "format_version: 1\n"
        "kind: mm9_raw_world_objects\n"
        "objects:\n"
        "  - object_index: 7\n"
        "    name: ShopkeeperHuman2MaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Fixture NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"0000803f\"\n"
        "        value_json: \"\"\n"
        "      - name: ScriptName\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"DORUDE.scr\\\"\"\n"
        "      - name: ScriptParams\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"1 FixtureTarget\\\"\"\n"
        "      - name: GreetingSound\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"greeting.wav\\\"\"\n");

    writeTextFile(
        root / "assets_dev/worlds/mm9/world.yml",
        "id: mm9\n"
        "name: MM9\n"
        "sourceGame: mm9\n");

    const OpenYAMM::Game::Mm9DialoguePipelineResult generated =
        OpenYAMM::Game::generateMm9DialoguePipelineFiles(root / "extracted", root / "source_maps");
    REQUIRE(generated.errors.empty());

    const OpenYAMM::Game::Mm9DialoguePipelineWriteResult writeResult =
        OpenYAMM::Game::writeMm9DialoguePipelineFiles(root / "assets_dev/worlds/mm9", generated.files, false);
    REQUIRE(writeResult.errors.empty());

    return root;
}

std::vector<OpenYAMM::Game::EventDialogAction>::const_iterator findMm9TopicAction(
    const OpenYAMM::Game::EventDialogContent &dialog,
    const std::string &label)
{
    return std::find_if(
        dialog.actions.begin(),
        dialog.actions.end(),
        [&](const OpenYAMM::Game::EventDialogAction &action)
        {
            return action.kind == OpenYAMM::Game::EventDialogActionKind::Mm9Topic
                && action.label == label;
        });
}
}

TEST_CASE("MM9 OutdoorWorldRuntime activation opens generated dialogue for scripted billboard hit")
{
    const std::filesystem::path fixtureRoot = makeMm9OutdoorRuntimeFixtureRoot();

    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    REQUIRE(assetFileSystem.initialize(
        fixtureRoot,
        fixtureRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::GameSession session = {};
    OpenYAMM::Game::ItemTable itemTable = {};
    OpenYAMM::Game::OutdoorMapData outdoorMapData = {};
    OpenYAMM::Game::OutdoorMovementDriver movementDriver(
        outdoorMapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    OpenYAMM::Game::OutdoorPartyRuntime partyRuntime(std::move(movementDriver), itemTable);

    OpenYAMM::Game::OutdoorWorldRuntime worldRuntime = {};
    OpenYAMM::Game::OutdoorWorldRuntime::Snapshot snapshot = {};
    snapshot.eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    worldRuntime.restoreSnapshot(snapshot);

    OpenYAMM::Game::OutdoorGameView view(session);
    OpenYAMM::Game::OutdoorGameViewMm9TestAccess::bindHeadlessWorldInteraction(
        view,
        assetFileSystem,
        partyRuntime,
        worldRuntime,
        outdoorMapData);

    OpenYAMM::Game::Mm9InteractionObjectBinding binding = {};
    binding.mapId = "testmap";
    binding.objectId = "mm9:testmap:object:7";
    binding.sourceObjectIndex = 7;
    binding.sourceClass = "NPC";
    binding.sourceName = "Fixture NPC";
    binding.visualId = "fixture_npc";
    binding.scriptName = "DORUDE.scr";
    binding.scriptParams = "1 FixtureTarget";
    binding.routerTargetIndex = 0;
    binding.hitPoint = {10.0f, 20.0f, 30.0f};
    binding.distance = 64.0f;

    const OpenYAMM::Game::GameplayWorldHit hit =
        OpenYAMM::Game::buildMm9ScriptedObjectWorldHit(binding);
    REQUIRE(worldRuntime.activateWorldHit(hit));

    const OpenYAMM::Game::EventDialogContent &dialog =
        session.gameplayScreenRuntime().activeEventDialog();
    REQUIRE(dialog.isActive);
    CHECK(dialog.sourceId == 1);
    CHECK(dialog.title == "Fixture NPC");
    REQUIRE(dialog.actions.size() == 2);
    CHECK(dialog.actions[0].kind == OpenYAMM::Game::EventDialogActionKind::Mm9Topic);
    CHECK(dialog.actions[0].label == "Continue");
    CHECK(dialog.actions[1].label == "Bye");
    REQUIRE(worldRuntime.eventRuntimeState() != nullptr);
    REQUIRE(worldRuntime.eventRuntimeState()->lastActivationResult.has_value());
    CHECK(worldRuntime.eventRuntimeState()->lastActivationResult->find("Fixture NPC") != std::string::npos);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 GameSession initializes script state from generated defaults")
{
    const std::filesystem::path fixtureRoot = makeMm9OutdoorRuntimeFixtureRoot();

    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    REQUIRE(assetFileSystem.initialize(
        fixtureRoot,
        fixtureRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9DialoguePackage package = {};
    REQUIRE(OpenYAMM::Game::loadMm9DialoguePackage(assetFileSystem, package));
    REQUIRE(package.errors.empty());
    CHECK(package.stateDefaults.loaded);
    CHECK(package.stateDefaults.keyQbitBase == 9000);
    REQUIRE(package.keys.count(44) == 1);
    CHECK(package.keys.at(44).qbitId == 9044);

    OpenYAMM::Game::GameSession session = {};
    OpenYAMM::Game::Mm9ScriptRuntimeState dirtyState = {};
    dirtyState.consoleNumVars["STALE"] = 7;
    dirtyState.consoleStrVars["STALE"] = "old";
    dirtyState.mapNumVars["testmap"]["STALE"] = 9;
    dirtyState.objectNumberProperties["testmap:7:STALE"] = 11;
    dirtyState.triggers.push_back({});
    dirtyState.triggerDispatches.push_back({});
    session.setMm9ScriptState(dirtyState);

    session.initializeMm9ScriptState(package);
    const OpenYAMM::Game::Mm9ScriptRuntimeState &initialState = session.mm9ScriptState();
    CHECK(initialState.consoleNumVars.empty());
    CHECK(initialState.consoleStrVars.empty());
    CHECK(initialState.mapNumVars.empty());
    CHECK(initialState.mapStrVars.empty());
    CHECK(initialState.scriptNumVars.empty());
    CHECK(initialState.scriptStrVars.empty());
    CHECK(initialState.objectHandleVars.empty());
    CHECK(initialState.objectNumberProperties.empty());
    CHECK(initialState.triggers.empty());
    CHECK(initialState.triggerDispatches.empty());

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 real scene object activation opens correct dialogue through OutdoorWorldRuntime GUI route")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    const std::optional<std::string> sceneText =
        assetFileSystem.readTextFile("worlds/mm9/maps/afterworld.scene.yml");
    REQUIRE(sceneText.has_value());

    std::string sceneError;
    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<OpenYAMM::Game::OutdoorSceneData> sceneData =
        sceneLoader.loadFromText(*sceneText, sceneError);
    REQUIRE_MESSAGE(sceneData.has_value(), sceneError);

    const OpenYAMM::Game::OutdoorSceneModelInstance *pTryggvaInstance = nullptr;
    for (const OpenYAMM::Game::OutdoorSceneModelInstance &modelInstance : sceneData->modelInstances)
    {
        if (modelInstance.sourceObjectIndex == 96)
        {
            pTryggvaInstance = &modelInstance;
            break;
        }
    }
    REQUIRE(pTryggvaInstance != nullptr);
    CHECK(pTryggvaInstance->instanceId == "mm9:afterworld:object:96");
    CHECK(pTryggvaInstance->sourceClass == "TryggvaRavenlocks");

    OpenYAMM::Game::GameSession session = {};
    OpenYAMM::Game::ItemTable itemTable = {};
    OpenYAMM::Game::OutdoorMapData outdoorMapData = {};
    OpenYAMM::Game::OutdoorMovementDriver movementDriver(
        outdoorMapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    OpenYAMM::Game::OutdoorPartyRuntime partyRuntime(std::move(movementDriver), itemTable);

    OpenYAMM::Game::OutdoorWorldRuntime worldRuntime = {};
    OpenYAMM::Game::OutdoorWorldRuntime::Snapshot snapshot = {};
    snapshot.eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    worldRuntime.restoreSnapshot(snapshot);

    OpenYAMM::Game::OutdoorGameView view(session);
    OpenYAMM::Game::OutdoorGameViewMm9TestAccess::bindHeadlessWorldInteraction(
        view,
        assetFileSystem,
        partyRuntime,
        worldRuntime,
        outdoorMapData);

    OpenYAMM::Game::Mm9InteractionObjectBinding binding = {};
    binding.mapId = "afterworld";
    binding.objectId = pTryggvaInstance->instanceId;
    binding.sourceObjectIndex = static_cast<int32_t>(pTryggvaInstance->sourceObjectIndex);
    binding.sourceClass = pTryggvaInstance->sourceClass;
    binding.sourceName = pTryggvaInstance->sourceName;
    binding.visualId = pTryggvaInstance->sourceModel;
    binding.routerTargetIndex = 0;
    binding.hitPoint = {0.0f, 0.0f, 0.0f};
    binding.distance = 64.0f;

    const OpenYAMM::Game::GameplayWorldHit hit =
        OpenYAMM::Game::buildMm9ScriptedObjectWorldHit(binding);
    REQUIRE(worldRuntime.activateWorldHit(hit));

    const OpenYAMM::Game::EventDialogContent &dialog =
        session.gameplayScreenRuntime().activeEventDialog();
    REQUIRE(dialog.isActive);
    CHECK(dialog.sourceId == 180);
    CHECK(dialog.title == "TryggvaRavenlocks0");
    REQUIRE_FALSE(dialog.actions.empty());
    CHECK(dialog.actions[0].kind == OpenYAMM::Game::EventDialogActionKind::Mm9Topic);
    REQUIRE(worldRuntime.eventRuntimeState() != nullptr);
    REQUIRE(worldRuntime.eventRuntimeState()->lastActivationResult.has_value());
    CHECK(worldRuntime.eventRuntimeState()->lastActivationResult->find("TryggvaRavenlocks0") != std::string::npos);
}

TEST_CASE("MM9 arena scripted NPC close runs authored OnRudeExit state mutation through OutdoorWorldRuntime")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::GameSession session = {};
    OpenYAMM::Game::ItemTable itemTable = {};
    OpenYAMM::Game::OutdoorMapData outdoorMapData = {};
    OpenYAMM::Game::OutdoorMovementDriver movementDriver(
        outdoorMapData,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt);
    OpenYAMM::Game::OutdoorPartyRuntime partyRuntime(std::move(movementDriver), itemTable);

    OpenYAMM::Game::OutdoorWorldRuntime worldRuntime = {};
    OpenYAMM::Game::OutdoorWorldRuntime::Snapshot snapshot = {};
    snapshot.eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    worldRuntime.restoreSnapshot(snapshot);

    OpenYAMM::Game::OutdoorGameView view(session);
    OpenYAMM::Game::OutdoorGameViewMm9TestAccess::bindHeadlessWorldInteraction(
        view,
        assetFileSystem,
        partyRuntime,
        worldRuntime,
        outdoorMapData);

    OpenYAMM::Game::Mm9InteractionObjectBinding binding = {};
    binding.mapId = "thearena";
    binding.objectId = "mm9:thearena:object:20";
    binding.sourceObjectIndex = 20;
    binding.sourceClass = "SvenSvenssen";
    binding.sourceName = "SvenArena";
    binding.visualId = "sven_arena";
    binding.routerTargetIndex = 0;
    binding.hitPoint = {0.0f, 0.0f, 0.0f};
    binding.distance = 64.0f;

    CHECK_FALSE(partyRuntime.party().hasQuestBit(10034));
    const OpenYAMM::Game::GameplayWorldHit hit =
        OpenYAMM::Game::buildMm9ScriptedObjectWorldHit(binding);
    const bool activated = worldRuntime.activateWorldHit(hit);
    const std::string activationResult =
        worldRuntime.eventRuntimeState() != nullptr && worldRuntime.eventRuntimeState()->lastActivationResult
            ? *worldRuntime.eventRuntimeState()->lastActivationResult
            : std::string();
    REQUIRE_MESSAGE(activated, activationResult);
    CHECK(partyRuntime.party().hasQuestBit(10034));

    OpenYAMM::Game::EventDialogContent dialog =
        session.gameplayScreenRuntime().activeEventDialog();
    REQUIRE(dialog.isActive);
    CHECK(dialog.sourceId == 428);
    CHECK(dialog.title == "SvenArena");
    std::vector<OpenYAMM::Game::EventDialogAction>::const_iterator topicAction =
        findMm9TopicAction(dialog, "Sorry to bother you.");
    REQUIRE(topicAction != dialog.actions.end());

    OpenYAMM::Game::EventDialogContent updatedDialog = {};
    REQUIRE(worldRuntime.executeMm9DialogueAction(*topicAction, updatedDialog));
    REQUIRE(updatedDialog.isActive);
    REQUIRE(updatedDialog.lines.size() == 1);
    CHECK(updatedDialog.lines[0] == "Goodbye.");
    topicAction = findMm9TopicAction(updatedDialog, "Goodbye.");
    REQUIRE(topicAction != updatedDialog.actions.end());

    OpenYAMM::Game::EventDialogContent closeDialog = {};
    REQUIRE(worldRuntime.executeMm9DialogueAction(*topicAction, closeDialog));
    REQUIRE(closeDialog.isActive);
    REQUIRE(closeDialog.lines.size() == 1);
    CHECK(closeDialog.lines[0] == "asdf");
    CHECK(closeDialog.actions.empty());
    CHECK_FALSE(partyRuntime.party().hasQuestBit(10034));
}
