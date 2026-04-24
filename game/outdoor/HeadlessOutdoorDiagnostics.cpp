#include "game/data/ActorNameResolver.h"
#include "game/outdoor/HeadlessOutdoorDiagnostics.h"
#include "game/StringUtils.h"

#include "engine/AssetFileSystem.h"
#include "engine/AudioSystem.h"
#include "game/tables/CharacterDollTable.h"
#include "game/events/EventDialogContent.h"
#include "game/events/EventRuntime.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/app/GameApplication.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/indoor/IndoorWorldRuntime.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/outdoor/OutdoorMovementController.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/items/PriceCalculator.h"
#include "game/maps/MapAssetLoader.h"
#include "game/maps/SaveGame.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/SpellIds.h"
#include "game/SpriteObjectDefs.h"

#include <SDL3/SDL.h>

#include <fstream>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
GameplayActorService buildBoundGameplayActorService(const GameDataLoader &gameDataLoader)
{
    GameplayActorService service = {};
    service.bindTables(&gameDataLoader.getMonsterTable(), &gameDataLoader.getSpellTable());
    return service;
}

bool textContains(const std::string &text, const std::string &needle)
{
    return text.find(needle) != std::string::npos;
}

bool isKnownHeadlessRegressionSuite(const std::string &suiteName)
{
    static constexpr std::array<const char *, 19> KnownSuites = {{
        "dialogue",
        "chest",
        "arcomage",
        "indoor",
        "outdoor",
        "actors",
        "combat",
        "projectiles",
        "events",
        "scripts",
        "maps",
        "app",
        "audio",
        "movement",
        "weather",
        "items",
        "houses",
        "transitions",
        "save",
    }};

    return std::find(KnownSuites.begin(), KnownSuites.end(), suiteName) != KnownSuites.end();
}

void printHeadlessRegressionSuites()
{
    std::cerr
        << "Known regression suites: dialogue, chest, arcomage, indoor, outdoor, actors, combat, projectiles, "
        << "events, scripts, maps, app, audio, movement, weather, items, houses, transitions, save\n";
}

bool headlessRegressionCaseMatchesSuite(const std::string &suiteName, const std::string &caseName)
{
    if (suiteName == "indoor")
    {
        return true;
    }

    if (suiteName == "chest")
    {
        return textContains(caseName, "chest");
    }

    if (suiteName == "arcomage")
    {
        return textContains(caseName, "arcomage");
    }

    if (suiteName == "dialogue" || suiteName == "outdoor")
    {
        return true;
    }

    if (suiteName == "actors")
    {
        return textContains(caseName, "actor") || textContains(caseName, "monster");
    }

    if (suiteName == "combat")
    {
        return textContains(caseName, "attack")
            || textContains(caseName, "damage")
            || textContains(caseName, "kill")
            || textContains(caseName, "killed")
            || textContains(caseName, "death")
            || textContains(caseName, "hostile")
            || textContains(caseName, "aggro");
    }

    if (suiteName == "projectiles")
    {
        return textContains(caseName, "projectile")
            || textContains(caseName, "fireball")
            || textContains(caseName, "cannonball")
            || textContains(caseName, "arrow")
            || textContains(caseName, "meteor");
    }

    if (suiteName == "events")
    {
        return textContains(caseName, "event")
            || textContains(caseName, "qbit")
            || textContains(caseName, "barrel")
            || textContains(caseName, "campfire");
    }

    if (suiteName == "scripts")
    {
        return textContains(caseName, "lua")
            || textContains(caseName, "script")
            || textContains(caseName, "generated_lua");
    }

    if (suiteName == "maps")
    {
        return textContains(caseName, "map")
            || textContains(caseName, "scene")
            || textContains(caseName, "terrain")
            || textContains(caseName, "support_floor")
            || textContains(caseName, "startup")
            || textContains(caseName, "boundary")
            || textContains(caseName, "transition");
    }

    if (suiteName == "app")
    {
        return textContains(caseName, "app_") || textContains(caseName, "startup");
    }

    if (suiteName == "audio")
    {
        return textContains(caseName, "audio")
            || textContains(caseName, "music")
            || textContains(caseName, "sound");
    }

    if (suiteName == "movement")
    {
        return textContains(caseName, "movement")
            || textContains(caseName, "motion")
            || textContains(caseName, "move")
            || textContains(caseName, "floor")
            || textContains(caseName, "support")
            || textContains(caseName, "collision")
            || textContains(caseName, "overlap")
            || textContains(caseName, "snaps");
    }

    if (suiteName == "weather")
    {
        return textContains(caseName, "atmosphere")
            || textContains(caseName, "fog")
            || textContains(caseName, "rain")
            || textContains(caseName, "snow")
            || textContains(caseName, "weather");
    }

    if (suiteName == "items")
    {
        return textContains(caseName, "item")
            || textContains(caseName, "loot")
            || textContains(caseName, "chest")
            || textContains(caseName, "treasure")
            || textContains(caseName, "inventory")
            || textContains(caseName, "granted_item");
    }

    if (suiteName == "houses")
    {
        return textContains(caseName, "house")
            || textContains(caseName, "tavern")
            || textContains(caseName, "teacher")
            || textContains(caseName, "adventurers_inn")
            || textContains(caseName, "service");
    }

    if (suiteName == "transitions")
    {
        return textContains(caseName, "transition")
            || textContains(caseName, "transport")
            || textContains(caseName, "pending_map_move")
            || textContains(caseName, "boundary");
    }

    if (suiteName == "save")
    {
        return textContains(caseName, "save")
            || textContains(caseName, "quickload")
            || textContains(caseName, "quicksave")
            || textContains(caseName, "snapshot")
            || textContains(caseName, "roundtrip");
    }

    return false;
}
}

struct GameApplicationTestAccess
{
    static bool loadGameData(GameApplication &application, const Engine::AssetFileSystem &assetFileSystem)
    {
        return application.loadGameData(assetFileSystem);
    }

    static bool loadMapByFileNameForGameplay(
        GameApplication &application,
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &mapFileName)
    {
        return application.m_gameDataLoader.loadMapByFileNameForGameplay(assetFileSystem, mapFileName);
    }

    static void shutdownRenderer(GameApplication &application)
    {
        application.shutdownRenderer();
    }

    static bool initializeSelectedMapRuntime(GameApplication &application, bool initializeView)
    {
        return application.initializeSelectedMapRuntime(initializeView);
    }

    static bool initializeStartupSession(GameApplication &application, bool initializeView)
    {
        return application.initializeStartupSession(initializeView);
    }

    static bool bootSeededDwiOnNextRendererInit(const GameApplication &application)
    {
        return application.m_bootSeededDwiOnNextRendererInit;
    }

    static void setBootSeededDwiOnNextRendererInit(GameApplication &application, bool value)
    {
        application.m_bootSeededDwiOnNextRendererInit = value;
    }

    static OutdoorPartyRuntime *outdoorPartyRuntime(GameApplication &application)
    {
        return application.m_pOutdoorPartyRuntime.get();
    }

    static const OutdoorPartyRuntime *outdoorPartyRuntime(const GameApplication &application)
    {
        return application.m_pOutdoorPartyRuntime.get();
    }

    static OutdoorWorldRuntime *outdoorWorldRuntime(GameApplication &application)
    {
        return application.m_pOutdoorWorldRuntime.get();
    }

    static const OutdoorWorldRuntime *outdoorWorldRuntime(const GameApplication &application)
    {
        return application.m_pOutdoorWorldRuntime.get();
    }

    static IMapSceneRuntime *mapSceneRuntime(GameApplication &application)
    {
        return application.m_pMapSceneRuntime.get();
    }

    static const IMapSceneRuntime *mapSceneRuntime(const GameApplication &application)
    {
        return application.m_pMapSceneRuntime.get();
    }

    static GameDataLoader &gameDataLoader(GameApplication &application)
    {
        return application.m_gameDataLoader;
    }

    static const GameDataLoader &gameDataLoader(const GameApplication &application)
    {
        return application.m_gameDataLoader;
    }

    static const std::string &currentSessionMapFileName(const GameApplication &application)
    {
        return application.m_gameSession.currentMapFileName();
    }

    static bool quickSaveToPath(GameApplication &application, const std::filesystem::path &path)
    {
        return application.quickSaveToPath(path);
    }

    static bool quickLoadFromPath(GameApplication &application, const std::filesystem::path &path, bool initializeView)
    {
        return application.quickLoadFromPath(path, initializeView);
    }

    static void captureCurrentSceneState(GameApplication &application)
    {
        application.captureCurrentSceneState();
    }

    static bool shouldTriggerPartyDefeat(GameApplication &application)
    {
        return application.shouldTriggerPartyDefeat();
    }

    static std::string resolvePartyDefeatRespawnMapFileName(const GameApplication &application)
    {
        return application.resolvePartyDefeatRespawnMapFileName();
    }

    static void applyPartyDefeatConsequences(GameApplication &application)
    {
        application.applyPartyDefeatConsequences();
    }

    static void setCameraAngles(GameApplication &application, float yawRadians, float pitchRadians)
    {
        application.m_outdoorGameView.setCameraAngles(yawRadians, pitchRadians);
    }

    static float cameraYawRadians(const GameApplication &application)
    {
        return application.m_outdoorGameView.cameraYawRadians();
    }

    static float cameraPitchRadians(const GameApplication &application)
    {
        return application.m_outdoorGameView.cameraPitchRadians();
    }

    static GameAudioSystem &gameAudioSystem(GameApplication &application)
    {
        return application.m_gameAudioSystem;
    }

    static void updateHouseVideoPlayback(GameApplication &application, float deltaSeconds)
    {
        application.m_outdoorGameView.updateHouseVideoPlayback(deltaSeconds);
    }

    static void openPendingEventDialog(
        GameApplication &application,
        size_t previousMessageCount,
        bool allowNpcFallbackContent)
    {
        if (OutdoorWorldRuntime *pWorldRuntime = outdoorWorldRuntime(application))
        {
            pWorldRuntime->presentPendingEventDialog(previousMessageCount, allowNpcFallbackContent);
        }
    }

    static const std::string &statusBarEventText(const GameApplication &application)
    {
        return application.m_gameSession.gameplayScreenRuntime().statusBarEventText();
    }

    static bool hasActiveEventDialog(const GameApplication &application)
    {
        return application.m_gameSession.gameplayScreenRuntime().activeEventDialog().isActive;
    }

    static bool isRestScreenActive(const GameApplication &application)
    {
        return application.m_gameSession.gameplayScreenRuntime().restScreenState().active;
    }

    static float restRemainingMinutes(const GameApplication &application)
    {
        return application.m_gameSession.gameplayScreenRuntime().restScreenState().remainingMinutes;
    }

    static void updateRestScreen(GameApplication &application, float deltaSeconds)
    {
        GameplayScreenController::updateRestOverlayProgress(
            application.m_gameSession.gameplayScreenRuntime(),
            deltaSeconds);
    }

    static const EventDialogContent &activeEventDialog(const GameApplication &application)
    {
        return application.m_gameSession.gameplayScreenRuntime().activeEventDialog();
    }

    static void setEventDialogSelectionIndex(GameApplication &application, size_t selectionIndex)
    {
        application.m_gameSession.gameplayScreenRuntime().eventDialogSelectionIndex() = selectionIndex;
    }

    static void executeActiveDialogAction(GameApplication &application)
    {
        if (OutdoorWorldRuntime *pWorldRuntime = outdoorWorldRuntime(application))
        {
            pWorldRuntime->executeActiveDialogAction();
        }
    }

    static void handleDialogueCloseRequest(GameApplication &application)
    {
        if (OutdoorWorldRuntime *pWorldRuntime = outdoorWorldRuntime(application))
        {
            pWorldRuntime->handleDialogueCloseRequest();
        }
    }

    static bool processPendingMapMove(GameApplication &application)
    {
        return application.processPendingMapMove();
    }

    static SceneKind currentSceneKind(const GameApplication &application)
    {
        return application.m_gameSession.currentSceneKind();
    }

    static bool advanceTimeByOneHourHotkey(GameApplication &application)
    {
        application.m_pendingAdvanceTime = true;
        return application.processPendingQuickSaveInput();
    }

    static const GameplayUiController::CharacterScreenState &characterScreen(const GameApplication &application)
    {
        return application.m_gameSession.gameplayScreenRuntime().characterScreenReadOnly();
    }

    static OutdoorGameView &outdoorGameView(GameApplication &application)
    {
        return application.m_outdoorGameView;
    }

    static void consumePendingPortraitEventFxRequests(GameApplication &application)
    {
        application.m_gameSession.gameplayFxService().consumePendingEventFxRequests(
            application.m_gameSession.gameplayScreenRuntime());
    }

    static bool heldInventoryItemActive(const GameApplication &application)
    {
        return application.m_outdoorGameView.heldInventoryItem().active;
    }

    static const InventoryItem &heldInventoryItem(const GameApplication &application)
    {
        return application.m_outdoorGameView.heldInventoryItem().item;
    }

    static void setHeldInventoryItem(GameApplication &application, const InventoryItem &item)
    {
        GameplayUiController::HeldInventoryItemState &heldInventoryItem = application.m_outdoorGameView.heldInventoryItem();
        heldInventoryItem.active = true;
        heldInventoryItem.item = item;
        heldInventoryItem.grabCellOffsetX = 0;
        heldInventoryItem.grabCellOffsetY = 0;
        heldInventoryItem.grabOffsetX = 0.0f;
        heldInventoryItem.grabOffsetY = 0.0f;
    }

    static void setAutosavePath(GameApplication &application, const std::filesystem::path &path)
    {
        application.m_outdoorGameView.m_autosavePath = path;
    }

    static const OutdoorEntity *outdoorEntity(const GameApplication &application, size_t entityIndex)
    {
        const std::optional<MapAssetInfo> &selectedMap = application.m_gameDataLoader.getSelectedMap();

        if (!selectedMap || !selectedMap->outdoorMapData || entityIndex >= selectedMap->outdoorMapData->entities.size())
        {
            return nullptr;
        }

        return &selectedMap->outdoorMapData->entities[entityIndex];
    }

    static void presentPendingEventDialogDirect(
        GameApplication &application,
        size_t previousMessageCount,
        bool allowNpcFallbackContent,
        bool showBankInputCursor)
    {
        EventRuntimeState *pEventRuntimeState =
            application.m_pOutdoorWorldRuntime != nullptr ? application.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

        if (pEventRuntimeState == nullptr)
        {
            return;
        }

        const std::optional<MapAssetInfo> &selectedMap = application.m_gameDataLoader.getSelectedMap();
        const std::optional<ScriptedEventProgram> *pGlobalEventProgram =
            selectedMap && selectedMap->globalEventProgram
            ? &selectedMap->globalEventProgram
            : nullptr;
        GameplayScreenRuntime &screenRuntime = application.m_gameSession.gameplayScreenRuntime();
        GameplayDialogController::Context context = {
            application.m_gameSession.gameplayUiController(),
            *pEventRuntimeState,
            screenRuntime.activeEventDialog(),
            screenRuntime.eventDialogSelectionIndex(),
            &screenRuntime,
            application.m_pOutdoorPartyRuntime != nullptr ? &application.m_pOutdoorPartyRuntime->party() : nullptr,
            application.m_pOutdoorWorldRuntime.get(),
            pGlobalEventProgram,
            &application.m_gameDataLoader.getHouseTable(),
            &application.m_gameDataLoader.getClassSkillTable(),
            &application.m_gameDataLoader.getNpcDialogTable(),
            selectedMap ? &selectedMap->map : nullptr,
            &application.m_gameDataLoader.getMapStats().getEntries(),
            &application.m_gameDataLoader.getRosterTable(),
            &application.m_gameDataLoader.getArcomageLibrary(),
            false
        };

        application.m_gameSession.gameplayDialogController().presentPendingEventDialog(
            context,
            previousMessageCount,
            allowNpcFallbackContent,
            showBankInputCursor);
    }

    static OutdoorSceneRuntime::AdvanceFrameResult advanceOutdoorSceneFrame(
        GameApplication &application,
        const OutdoorMovementInput &movementInput,
        float deltaSeconds)
    {
        if (application.m_pMapSceneRuntime == nullptr || application.m_pMapSceneRuntime->kind() != SceneKind::Outdoor)
        {
            return {};
        }

        OutdoorSceneRuntime::AdvanceFrameResult result =
            static_cast<OutdoorSceneRuntime *>(application.m_pMapSceneRuntime.get())->advanceFrame(
            movementInput,
            deltaSeconds);

        if (IGameplayWorldRuntime *pWorldRuntime = application.m_gameSession.activeWorldRuntime())
        {
            pWorldRuntime->updateActorAi(deltaSeconds);
        }

        return result;
    }
};

namespace
{
constexpr uint32_t AdventurersInnHouseId = 185;
constexpr float HostilityCloseRange = 1024.0f;
constexpr float HostilityShortRange = 2560.0f;
constexpr float HostilityMediumRange = 5120.0f;
constexpr float HostilityLongRange = 10240.0f;

std::optional<ScriptedEventProgram> loadSyntheticScriptedProgram(
    const std::string &body,
    const std::string &chunkName,
    ScriptedEventScope scope,
    std::string &error)
{
    std::string luaSourceText = body;
    luaSourceText += "\n";
    luaSourceText += "evt.meta = evt.meta or {}\n";
    luaSourceText += "evt.meta.map = evt.meta.map or {}\n";
    luaSourceText += "evt.meta.global = evt.meta.global or {}\n";
    luaSourceText += "evt.meta.CanShowTopic = evt.meta.CanShowTopic or {}\n";

    const char *pScopeName = scope == ScriptedEventScope::Global ? "global" : "map";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".onLoad = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".hint = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".summary = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".openedChestIds = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".textureNames = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".spriteNames = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".castSpellIds = {}\n";
    luaSourceText += "evt.meta.";
    luaSourceText += pScopeName;
    luaSourceText += ".timers = {}\n";

    return ScriptedEventProgram::loadFromLuaText(luaSourceText, chunkName, scope, error);
}

struct SyntheticOutdoorWaterBoundaryScenario
{
    OutdoorMapData mapData;
    float landX = 0.0f;
    float landY = 0.0f;
    float waterX = 0.0f;
    float waterY = 0.0f;
};

bool isOutdoorLandMaskWaterForDiagnostics(
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    float x,
    float y)
{
    if (!outdoorLandMask || outdoorLandMask->empty())
    {
        return false;
    }

    const float gridX = outdoorWorldToGridXFloat(x);
    const float gridY = outdoorWorldToGridYFloat(y);
    const int tileX = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int tileY = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    const int landMaskWidth = OutdoorMapData::TerrainWidth - 1;
    const size_t tileIndex = static_cast<size_t>(tileY * landMaskWidth + tileX);

    if (tileIndex >= outdoorLandMask->size())
    {
        return false;
    }

    return (*outdoorLandMask)[tileIndex] == 0;
}

bool isOutdoorPositionWaterForDiagnostics(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    float x,
    float y)
{
    return isOutdoorTerrainWater(outdoorMapData, x, y)
        || isOutdoorLandMaskWaterForDiagnostics(outdoorLandMask, x, y);
}

SyntheticOutdoorWaterBoundaryScenario createSyntheticOutdoorWaterBoundaryScenario()
{
    SyntheticOutdoorWaterBoundaryScenario scenario = {};
    scenario.mapData.heightMap.resize(
        static_cast<size_t>(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight),
        0);
    scenario.mapData.attributeMap.resize(
        static_cast<size_t>(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight),
        0);
    const int landTileX = 63;
    const int landTileY = 63;
    const int waterTileX = 62;
    const int waterTileY = 63;
    const size_t waterTileIndex = static_cast<size_t>(waterTileY * OutdoorMapData::TerrainWidth + waterTileX);

    if (waterTileIndex < scenario.mapData.attributeMap.size())
    {
        scenario.mapData.attributeMap[waterTileIndex] = 0x02;
    }

    const float halfTile = static_cast<float>(OutdoorMapData::TerrainTileSize) * 0.5f;

    auto tileCenter =
        [halfTile](int tileX, int tileY) -> std::pair<float, float>
    {
        const float worldX = outdoorGridCornerWorldX(tileX) + halfTile;
        const float worldY = outdoorGridCornerWorldY(tileY) - halfTile;
        return {worldX, worldY};
    };

    const auto [landX, landY] = tileCenter(landTileX, landTileY);
    const auto [waterX, waterY] = tileCenter(waterTileX, waterTileY);
    scenario.landX = landX;
    scenario.landY = landY;
    scenario.waterX = waterX;
    scenario.waterY = waterY;
    return scenario;
}

float nextGameMinuteAtOrAfter(float currentGameMinutes, float targetMinuteOfDay)
{
    float targetGameMinutes = targetMinuteOfDay;

    while (targetGameMinutes <= currentGameMinutes)
    {
        targetGameMinutes += 24.0f * 60.0f;
    }

    return targetGameMinutes;
}

float definitelyClosedMinuteOfDay(const HouseEntry &houseEntry)
{
    if (houseEntry.openHour == houseEntry.closeHour)
    {
        return -1.0f;
    }

    return static_cast<float>(((houseEntry.closeHour + 1) % 24) * 60);
}

DialogueMenuId dialogueMenuIdForHouseAction(HouseActionId actionId)
{
    switch (actionId)
    {
        case HouseActionId::OpenLearnSkillsMenu:
            return DialogueMenuId::LearnSkills;

        case HouseActionId::OpenShopEquipmentMenu:
            return DialogueMenuId::ShopEquipment;

        case HouseActionId::OpenTavernArcomageMenu:
            return DialogueMenuId::TavernArcomage;

        default:
            return DialogueMenuId::None;
    }
}

const char *actorAiStateName(OutdoorWorldRuntime::ActorAiState state)
{
    switch (state)
    {
        case OutdoorWorldRuntime::ActorAiState::Standing:
            return "standing";
        case OutdoorWorldRuntime::ActorAiState::Wandering:
            return "wandering";
        case OutdoorWorldRuntime::ActorAiState::Pursuing:
            return "pursuing";
        case OutdoorWorldRuntime::ActorAiState::Fleeing:
            return "fleeing";
        case OutdoorWorldRuntime::ActorAiState::Stunned:
            return "stunned";
        case OutdoorWorldRuntime::ActorAiState::Attacking:
            return "attacking";
        case OutdoorWorldRuntime::ActorAiState::Dying:
            return "dying";
        case OutdoorWorldRuntime::ActorAiState::Dead:
            return "dead";
    }

    return "unknown";
}

const char *actorAnimationName(OutdoorWorldRuntime::ActorAnimation animation)
{
    switch (animation)
    {
        case OutdoorWorldRuntime::ActorAnimation::Standing:
            return "standing";
        case OutdoorWorldRuntime::ActorAnimation::Walking:
            return "walking";
        case OutdoorWorldRuntime::ActorAnimation::AttackMelee:
            return "attack_melee";
        case OutdoorWorldRuntime::ActorAnimation::AttackRanged:
            return "attack_ranged";
        case OutdoorWorldRuntime::ActorAnimation::GotHit:
            return "got_hit";
        case OutdoorWorldRuntime::ActorAnimation::Dying:
            return "dying";
        case OutdoorWorldRuntime::ActorAnimation::Dead:
            return "dead";
        case OutdoorWorldRuntime::ActorAnimation::Bored:
            return "bored";
    }

    return "unknown";
}

const char *debugTargetKindName(OutdoorWorldRuntime::DebugTargetKind kind)
{
    switch (kind)
    {
        case OutdoorWorldRuntime::DebugTargetKind::None:
            return "none";
        case OutdoorWorldRuntime::DebugTargetKind::Party:
            return "party";
        case OutdoorWorldRuntime::DebugTargetKind::Actor:
            return "actor";
    }

    return "unknown";
}

const char *monsterAiTypeName(int aiType)
{
    switch (static_cast<MonsterTable::MonsterAiType>(aiType))
    {
        case MonsterTable::MonsterAiType::Suicide:
            return "suicide";
        case MonsterTable::MonsterAiType::Wimp:
            return "wimp";
        case MonsterTable::MonsterAiType::Normal:
            return "normal";
        case MonsterTable::MonsterAiType::Aggressive:
            return "aggressive";
    }

    return "unknown";
}

struct TextureColorStats
{
    size_t opaquePixelCount = 0;
    size_t magentaPixelCount = 0;
    size_t greenPixelCount = 0;
};

struct ActorPreviewAnimationStats
{
    size_t sampleCount = 0;
    size_t greenDominantSampleCount = 0;
    size_t magentaDominantSampleCount = 0;
    size_t missingTextureSampleCount = 0;
    size_t distinctWalkingFrameCount = 0;
};

float normalizeAngleRadians(float angle)
{
    constexpr float Pi = 3.14159265358979323846f;

    while (angle <= -Pi)
    {
        angle += 2.0f * Pi;
    }

    while (angle > Pi)
    {
        angle -= 2.0f * Pi;
    }

    return angle;
}

float angleDistanceRadians(float left, float right)
{
    return std::abs(normalizeAngleRadians(left - right));
}

float hostilityRangeForRelation(int relation)
{
    switch (relation)
    {
        case 1:
            return HostilityCloseRange;
        case 2:
            return HostilityShortRange;
        case 3:
            return HostilityMediumRange;
        case 4:
            return HostilityLongRange;
        default:
            return 0.0f;
    }
}

float hostilePartyAcquisitionRange(
    const MonsterTable &monsterTable,
    const OutdoorWorldRuntime::MapActorState &actor)
{
    if (actor.hostileToParty)
    {
        return HostilityLongRange;
    }

    const int relationToParty = monsterTable.getRelationToParty(actor.monsterId);
    const float relationRange = hostilityRangeForRelation(relationToParty);

    return relationRange > 0.0f ? relationRange : 0.0f;
}

int firstTreasureLevelForItem(const ItemDefinition &itemDefinition)
{
    for (size_t tierIndex = 0; tierIndex < itemDefinition.randomTreasureWeights.size(); ++tierIndex)
    {
        if (itemDefinition.randomTreasureWeights[tierIndex] > 0)
        {
            return static_cast<int>(tierIndex) + 1;
        }
    }

    return 0;
}

bool itemHasTreasureWeightAtOrAboveTier(const ItemDefinition &itemDefinition, int tier)
{
    const int startTier = std::clamp(tier, 1, static_cast<int>(itemDefinition.randomTreasureWeights.size())) - 1;

    for (size_t tierIndex = static_cast<size_t>(startTier); tierIndex < itemDefinition.randomTreasureWeights.size();
         ++tierIndex)
    {
        if (itemDefinition.randomTreasureWeights[tierIndex] > 0)
        {
            return true;
        }
    }

    return false;
}

std::optional<uint16_t> findSpecialEnchantId(
    const SpecialItemEnchantTable &table,
    SpecialItemEnchantKind kind)
{
    const std::vector<SpecialItemEnchantEntry> &entries = table.entries();

    for (size_t index = 0; index < entries.size(); ++index)
    {
        if (entries[index].kind == kind)
        {
            return static_cast<uint16_t>(index + 1);
        }
    }

    return std::nullopt;
}

float signedDistanceToOutdoorFace(const OutdoorFaceGeometryData &geometry, const bx::Vec3 &point)
{
    if (!geometry.hasPlane || geometry.vertices.empty())
    {
        return 0.0f;
    }

    const bx::Vec3 delta = {
        point.x - geometry.vertices.front().x,
        point.y - geometry.vertices.front().y,
        point.z - geometry.vertices.front().z
    };
    return geometry.normal.x * delta.x + geometry.normal.y * delta.y + geometry.normal.z * delta.z;
}

TextureColorStats analyzeTextureColors(const std::vector<uint8_t> &pixels)
{
    TextureColorStats stats = {};

    for (size_t offset = 0; offset + 3 < pixels.size(); offset += 4)
    {
        const uint8_t blue = pixels[offset + 0];
        const uint8_t green = pixels[offset + 1];
        const uint8_t red = pixels[offset + 2];
        const uint8_t alpha = pixels[offset + 3];

        if (alpha == 0)
        {
            continue;
        }

        ++stats.opaquePixelCount;

        if (red >= 180 && blue >= 180 && green <= 120)
        {
            ++stats.magentaPixelCount;
        }

        if (green >= 100 && red <= 140 && blue <= 140)
        {
            ++stats.greenPixelCount;
        }
    }

    return stats;
}

const ActorPreviewBillboard *findCompanionActorBillboard(
    const ActorPreviewBillboardSet &billboardSet,
    size_t actorIndex,
    size_t &billboardIndex
)
{
    if (actorIndex >= billboardSet.mapDeltaActorCount || actorIndex >= billboardSet.billboards.size())
    {
        return nullptr;
    }

    billboardIndex = actorIndex;
    const ActorPreviewBillboard &billboard = billboardSet.billboards[billboardIndex];
    return billboard.source == ActorPreviewSource::Companion ? &billboard : nullptr;
}

const OutdoorBitmapTexture *findBillboardTexture(
    const ActorPreviewBillboardSet &billboardSet,
    const std::string &textureName,
    int16_t paletteId
)
{
    std::string normalizedTextureName = textureName;

    std::transform(
        normalizedTextureName.begin(),
        normalizedTextureName.end(),
        normalizedTextureName.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });

    for (const OutdoorBitmapTexture &texture : billboardSet.textures)
    {
        if (texture.textureName == normalizedTextureName && texture.paletteId == paletteId)
        {
            return &texture;
        }
    }

    return nullptr;
}

bool saveTextureAsPng(const OutdoorBitmapTexture &texture, const std::filesystem::path &outputPath)
{
    if (texture.physicalWidth <= 0 || texture.physicalHeight <= 0 || texture.pixels.empty())
    {
        return false;
    }

    SDL_Surface *pSurface = SDL_CreateSurfaceFrom(
        texture.physicalWidth,
        texture.physicalHeight,
        SDL_PIXELFORMAT_BGRA32,
        const_cast<uint8_t *>(texture.pixels.data()),
        texture.physicalWidth * 4);

    if (pSurface == nullptr)
    {
        return false;
    }

    const bool saved = SDL_SavePNG(pSurface, outputPath.string().c_str());
    SDL_DestroySurface(pSurface);
    return saved;
}

ActorPreviewAnimationStats analyzeActorPreviewAnimation(
    const ActorPreviewBillboardSet &billboardSet,
    const ActorPreviewBillboard &billboard
)
{
    ActorPreviewAnimationStats stats = {};
    std::vector<std::string> observedWalkingTextureKeys;
    const std::array<OutdoorWorldRuntime::ActorAnimation, 2> actions = {
        OutdoorWorldRuntime::ActorAnimation::Standing,
        OutdoorWorldRuntime::ActorAnimation::Walking
    };

    for (OutdoorWorldRuntime::ActorAnimation action : actions)
    {
        uint16_t spriteFrameIndex = billboard.spriteFrameIndex;
        const uint16_t actionFrameIndex = billboard.actionSpriteFrameIndices[static_cast<size_t>(action)];

        if (actionFrameIndex != 0)
        {
            spriteFrameIndex = actionFrameIndex;
        }

        const SpriteFrameEntry *pBaseFrame = billboardSet.spriteFrameTable.getFrame(spriteFrameIndex, 0);

        if (pBaseFrame == nullptr)
        {
            ++stats.missingTextureSampleCount;
            continue;
        }

        const uint32_t animationLengthTicks =
            pBaseFrame->animationLengthTicks > 0 ? static_cast<uint32_t>(pBaseFrame->animationLengthTicks) : 1u;
        const uint32_t sampleStride = std::max(1u, animationLengthTicks / 4u);

        for (uint32_t sampleTick = 0; sampleTick < animationLengthTicks; sampleTick += sampleStride)
        {
            const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(spriteFrameIndex, sampleTick);

            if (pFrame == nullptr)
            {
                ++stats.missingTextureSampleCount;
                continue;
            }

            for (int octant = 0; octant < 8; ++octant)
            {
                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
                const OutdoorBitmapTexture *pTexture =
                    findBillboardTexture(billboardSet, resolvedTexture.textureName, pFrame->paletteId);
                ++stats.sampleCount;

                if (pTexture == nullptr)
                {
                    ++stats.missingTextureSampleCount;
                    continue;
                }

                const TextureColorStats colorStats = analyzeTextureColors(pTexture->pixels);

                if (colorStats.greenPixelCount > colorStats.magentaPixelCount)
                {
                    ++stats.greenDominantSampleCount;
                }

                if (colorStats.magentaPixelCount > colorStats.greenPixelCount)
                {
                    ++stats.magentaDominantSampleCount;
                }
            }

            if (action == OutdoorWorldRuntime::ActorAnimation::Walking)
            {
                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
                const std::string textureKey =
                    resolvedTexture.textureName + "|" + std::to_string(static_cast<int>(pFrame->paletteId));

                if (std::find(
                        observedWalkingTextureKeys.begin(),
                        observedWalkingTextureKeys.end(),
                        textureKey) == observedWalkingTextureKeys.end())
                {
                    observedWalkingTextureKeys.push_back(textureKey);
                }
            }
        }
    }

    stats.distinctWalkingFrameCount = observedWalkingTextureKeys.size();
    return stats;
}

std::string resolveRuntimeActorTextureKey(
    const ActorPreviewBillboardSet &billboardSet,
    const ActorPreviewBillboard &billboard,
    const OutdoorWorldRuntime::MapActorState &actorState,
    float cameraX,
    float cameraY
)
{
    constexpr float Pi = 3.14159265358979323846f;
    uint16_t spriteFrameIndex = billboard.spriteFrameIndex;
    const size_t animationIndex = static_cast<size_t>(actorState.animation);

    if (animationIndex < billboard.actionSpriteFrameIndices.size()
        && billboard.actionSpriteFrameIndices[animationIndex] != 0)
    {
        spriteFrameIndex = billboard.actionSpriteFrameIndices[animationIndex];
    }

    const SpriteFrameEntry *pFrame =
        billboardSet.spriteFrameTable.getFrame(spriteFrameIndex, static_cast<uint32_t>(std::max(0.0f, actorState.animationTimeTicks)));

    if (pFrame == nullptr)
    {
        return {};
    }

    const float angleToCamera = std::atan2(
        static_cast<float>(actorState.y) - cameraY,
        static_cast<float>(actorState.x) - cameraX);
    const float actorYaw = actorState.yawRadians;
    const float octantAngle = actorYaw - angleToCamera + Pi + (Pi / 8.0f);
    const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);

    return resolvedTexture.textureName
        + "|"
        + std::to_string(static_cast<int>(pFrame->paletteId))
        + "|"
        + std::to_string(octant)
        + "|"
        + std::to_string(static_cast<int>(actorState.animation));
}

std::optional<uint32_t> singleSelectableResidentNpcId(
    const HouseEntry &houseEntry,
    const NpcDialogTable &npcDialogTable,
    const EventRuntimeState &eventRuntimeState
)
{
    std::vector<uint32_t> residentNpcIds;

    auto appendNpcId = [&](uint32_t npcId)
    {
        if (std::find(residentNpcIds.begin(), residentNpcIds.end(), npcId) != residentNpcIds.end())
        {
            return;
        }

        const NpcEntry *pResident = npcDialogTable.getNpc(npcId);

        if (pResident == nullptr || pResident->name.empty())
        {
            return;
        }

        if (eventRuntimeState.unavailableNpcIds.contains(npcId))
        {
            return;
        }

        const auto overrideIt = eventRuntimeState.npcHouseOverrides.find(npcId);

        if (overrideIt != eventRuntimeState.npcHouseOverrides.end() && overrideIt->second != houseEntry.id)
        {
            return;
        }

        residentNpcIds.push_back(npcId);
    };

    for (uint32_t npcId : houseEntry.residentNpcIds)
    {
        appendNpcId(npcId);
    }

    for (uint32_t npcId : npcDialogTable.getNpcIdsForHouse(houseEntry.id, &eventRuntimeState.npcHouseOverrides))
    {
        appendNpcId(npcId);
    }

    std::optional<uint32_t> residentNpcId;

    for (uint32_t candidateNpcId : residentNpcIds)
    {
        if (residentNpcId)
        {
            return std::nullopt;
        }

        residentNpcId = candidateNpcId;
    }

    return residentNpcId;
}

void printChestSummary(const OutdoorWorldRuntime::ChestViewState &chestView, const ItemTable &itemTable)
{
    std::cout << "Headless diagnostic: active chest #" << chestView.chestId
              << " type=" << chestView.chestTypeId
              << " flags=0x" << std::hex << chestView.flags << std::dec
              << " entries=" << chestView.items.size()
              << '\n';

    for (size_t itemIndex = 0; itemIndex < chestView.items.size(); ++itemIndex)
    {
        const OutdoorWorldRuntime::ChestItemState &item = chestView.items[itemIndex];
        std::cout << "  [" << itemIndex << "] ";

        if (item.isGold)
        {
            std::cout << "gold=" << item.goldAmount;

            if (item.goldRollCount > 1)
            {
                std::cout << " rolls=" << item.goldRollCount;
            }
        }
        else
        {
            const ItemDefinition *pItemDefinition = itemTable.get(item.itemId);
            std::cout << "item=" << item.itemId;

            if (pItemDefinition != nullptr && !pItemDefinition->name.empty())
            {
                std::cout << " \"" << pItemDefinition->name << "\"";
            }

            std::cout << " quantity=" << item.quantity;
        }

        std::cout << '\n';
    }
}

void printCorpseSummary(const OutdoorWorldRuntime::CorpseViewState &corpseView, const ItemTable &itemTable)
{
    std::cout << "Headless diagnostic: active corpse title=\"" << corpseView.title
              << "\" entries=" << corpseView.items.size()
              << " summoned=" << (corpseView.fromSummonedMonster ? "yes" : "no")
              << '\n';

    for (size_t itemIndex = 0; itemIndex < corpseView.items.size(); ++itemIndex)
    {
        const OutdoorWorldRuntime::ChestItemState &item = corpseView.items[itemIndex];
        std::cout << "  [" << itemIndex << "] ";

        if (item.isGold)
        {
            std::cout << "gold=" << item.goldAmount;
        }
        else
        {
            const ItemDefinition *pItemDefinition = itemTable.get(item.itemId);
            std::cout << "item=" << item.itemId;

            if (pItemDefinition != nullptr && !pItemDefinition->name.empty())
            {
                std::cout << " \"" << pItemDefinition->name << "\"";
            }

            std::cout << " quantity=" << item.quantity;
        }

        std::cout << '\n';
    }
}

bool chestLayoutItemsOverlap(
    const OutdoorWorldRuntime::ChestItemState &left,
    const OutdoorWorldRuntime::ChestItemState &right)
{
    return left.gridX < right.gridX + right.width
        && left.gridX + left.width > right.gridX
        && left.gridY < right.gridY + right.height
        && left.gridY + left.height > right.gridY;
}

bool validateChestLayout(const OutdoorWorldRuntime::ChestViewState &chestView, std::string &failure)
{
    if (chestView.gridWidth == 0 || chestView.gridHeight == 0)
    {
        failure = "grid size is zero";
        return false;
    }

    for (size_t itemIndex = 0; itemIndex < chestView.items.size(); ++itemIndex)
    {
        const OutdoorWorldRuntime::ChestItemState &item = chestView.items[itemIndex];

        if (item.width == 0 || item.height == 0)
        {
            failure = "item " + std::to_string(itemIndex) + " has zero size";
            return false;
        }

        if (item.gridX + item.width > chestView.gridWidth || item.gridY + item.height > chestView.gridHeight)
        {
            failure = "item " + std::to_string(itemIndex) + " is out of bounds";
            return false;
        }

        for (size_t otherIndex = itemIndex + 1; otherIndex < chestView.items.size(); ++otherIndex)
        {
            if (!chestLayoutItemsOverlap(item, chestView.items[otherIndex]))
            {
                continue;
            }

            failure = "items " + std::to_string(itemIndex) + " and " + std::to_string(otherIndex) + " overlap";
            return false;
        }
    }

    return true;
}

void printDialogSummary(const EventDialogContent &dialog)
{
    if (!dialog.isActive)
    {
        std::cout << "Headless diagnostic: no active dialog\n";
        return;
    }

    std::cout << "Headless diagnostic: dialog title=\"" << dialog.title << "\"\n";

    for (size_t lineIndex = 0; lineIndex < dialog.lines.size(); ++lineIndex)
    {
        std::cout << "  dialog[" << lineIndex << "] " << dialog.lines[lineIndex] << '\n';
    }

    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        const EventDialogAction &action = dialog.actions[actionIndex];
        std::cout << "  action[" << actionIndex << "] " << action.label
                  << " kind=" << static_cast<int>(action.kind)
                  << " id=" << action.id
                  << " enabled=" << (action.enabled ? "1" : "0");

        if (!action.disabledReason.empty())
        {
            std::cout << " reason=\"" << action.disabledReason << "\"";
        }

        std::cout << '\n';
    }
}

void promoteSingleResidentHouseContext(
    EventRuntimeState &eventRuntimeState,
    const HouseTable &houseTable,
    const NpcDialogTable &npcDialogTable,
    float currentGameMinutes
)
{
    if (!eventRuntimeState.pendingDialogueContext
        || eventRuntimeState.pendingDialogueContext->kind != DialogueContextKind::HouseService)
    {
        return;
    }

    const HouseEntry *pHouseEntry = houseTable.get(eventRuntimeState.pendingDialogueContext->sourceId);

    if (pHouseEntry == nullptr)
    {
        return;
    }

    const std::vector<HouseActionOption> houseActions = buildHouseActionOptions(
        *pHouseEntry,
        nullptr,
        nullptr,
        nullptr,
        currentGameMinutes,
        eventRuntimeState.dialogueState.menuStack.empty()
            ? DialogueMenuId::None
            : eventRuntimeState.dialogueState.menuStack.back()
    );
    const std::optional<uint32_t> residentNpcId = singleSelectableResidentNpcId(
        *pHouseEntry,
        npcDialogTable,
        eventRuntimeState
    );

    if (residentNpcId && houseActions.empty())
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = *residentNpcId;
        context.hostHouseId = pHouseEntry->id;
        eventRuntimeState.dialogueState.hostHouseId = pHouseEntry->id;
        eventRuntimeState.pendingDialogueContext = std::move(context);
    }
}

EventDialogContent buildHeadlessDialog(
    EventRuntimeState &eventRuntimeState,
    size_t previousMessageCount,
    bool allowNpcFallbackContent,
    const std::optional<ScriptedEventProgram> &globalEventProgram,
    const GameDataLoader &gameDataLoader,
    Party *pParty,
    float currentGameMinutes
)
{
    promoteSingleResidentHouseContext(
        eventRuntimeState,
        gameDataLoader.getHouseTable(),
        gameDataLoader.getNpcDialogTable(),
        currentGameMinutes
    );

    return buildEventDialogContent(
        eventRuntimeState,
        previousMessageCount,
        allowNpcFallbackContent,
        &globalEventProgram,
        &gameDataLoader.getHouseTable(),
        &gameDataLoader.getClassSkillTable(),
        &gameDataLoader.getNpcDialogTable(),
        nullptr,
        &gameDataLoader.getMapStats().getEntries(),
        pParty,
        nullptr,
        currentGameMinutes
    );
}

std::optional<size_t> findActionIndexByLabel(const EventDialogContent &dialog, const std::string &label)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label == label)
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

std::optional<size_t> findActionIndexByLabelPrefix(const EventDialogContent &dialog, const std::string &prefix)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label.rfind(prefix, 0) == 0)
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

bool dialogContainsText(const EventDialogContent &dialog, const std::string &fragment)
{
    for (const std::string &line : dialog.lines)
    {
        if (line.find(fragment) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

bool dialogHasActionLabel(const EventDialogContent &dialog, const std::string &label)
{
    return findActionIndexByLabel(dialog, label).has_value();
}

CharacterSkill *ensureCharacterSkill(
    Character &character,
    const std::string &skillName,
    uint32_t level,
    SkillMastery mastery
)
{
    CharacterSkill *pSkill = character.findSkill(skillName);

    if (pSkill == nullptr)
    {
        CharacterSkill skill = {};
        skill.name = canonicalSkillName(skillName);
        skill.level = level;
        skill.mastery = mastery;
        character.skills[skill.name] = skill;
        pSkill = character.findSkill(skillName);
    }

    if (pSkill != nullptr)
    {
        pSkill->level = level;
        pSkill->mastery = mastery;
    }

    return pSkill;
}

struct RegressionScenario
{
    OutdoorWorldRuntime world;
    GameplayActorService actorService;
    GameplayProjectileService projectileService;
    GameplayCombatController combatController;
    Party party;
    EventRuntime eventRuntime;
    EventRuntimeState *pEventRuntimeState = nullptr;
};

struct IndoorRegressionScenario
{
    IndoorWorldRuntime world;
    GameplayActorService actorService;
    Party party;
    EventRuntime eventRuntime;
    std::optional<MapDeltaData> mapDeltaData;
    std::optional<EventRuntimeState> eventRuntimeState;
};

Character makeRegressionPartyMember(
    const std::string &name,
    const std::string &className,
    const std::string &portraitTextureName,
    uint32_t characterDataId)
{
    Character member = {};
    member.name = name;
    member.className = className;
    member.role = className;
    member.portraitTextureName = portraitTextureName;
    member.characterDataId = characterDataId;
    member.birthYear = 1160;
    member.experience = 0;
    member.level = 1;
    member.skillPoints = 5;
    member.might = 14;
    member.intellect = 14;
    member.personality = 14;
    member.endurance = 14;
    member.speed = 14;
    member.accuracy = 14;
    member.luck = 14;
    member.maxHealth = 40;
    member.health = 40;
    member.maxSpellPoints = 20;
    member.spellPoints = 20;
    return member;
}

PartySeed createRegressionPartySeed()
{
    PartySeed seed = {};
    seed.gold = 200;
    seed.food = 7;
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));
    seed.members.push_back(makeRegressionPartyMember("Brom", "Cleric", "PC03-01", 3));
    seed.members.push_back(makeRegressionPartyMember("Cedric", "Druid", "PC05-01", 5));
    seed.members.push_back(makeRegressionPartyMember("Daria", "Sorcerer", "PC07-01", 7));
    return seed;
}

std::string bytesToUpperHex(const std::vector<uint8_t> &bytes)
{
    static constexpr char HexDigits[] = "0123456789ABCDEF";

    std::string text;
    text.reserve(bytes.size() * 2);

    for (uint8_t value : bytes)
    {
        text.push_back(HexDigits[(value >> 4) & 0x0F]);
        text.push_back(HexDigits[value & 0x0F]);
    }

    return text;
}

void appendNormalizedPosition(std::ostringstream &stream, int x, int y, int z)
{
    stream << x << ',' << y << ',' << z;
}

std::string buildNormalizedOutdoorAuthoredSnapshot(const MapAssetInfo &mapAssetInfo)
{
    std::ostringstream stream;

    if (!mapAssetInfo.outdoorMapData || !mapAssetInfo.outdoorMapDeltaData)
    {
        stream << "missing_outdoor_state\n";
        return stream.str();
    }

    const OutdoorMapData &outdoorMapData = *mapAssetInfo.outdoorMapData;
    const MapDeltaData &mapDeltaData = *mapAssetInfo.outdoorMapDeltaData;
    const std::string effectiveSkyTexture =
        !mapDeltaData.locationTime.skyTextureName.empty()
        ? mapDeltaData.locationTime.skyTextureName
        : outdoorMapData.skyTexture;
    uint32_t mapExtraBitsRaw = 0;
    int32_t ceiling = 0;

    if (mapDeltaData.locationTime.reserved.size() >= sizeof(mapExtraBitsRaw) + sizeof(ceiling))
    {
        std::memcpy(&mapExtraBitsRaw, mapDeltaData.locationTime.reserved.data(), sizeof(mapExtraBitsRaw));
        std::memcpy(
            &ceiling,
            mapDeltaData.locationTime.reserved.data() + sizeof(mapExtraBitsRaw),
            sizeof(ceiling));
    }

    stream << "environment\n";
    stream << "sky_texture=" << effectiveSkyTexture << '\n';
    stream << "ground_tileset_name=" << outdoorMapData.groundTilesetName << '\n';
    stream << "master_tile=" << static_cast<int>(outdoorMapData.masterTile) << '\n';
    stream << "tile_set_lookup_indices="
           << outdoorMapData.tileSetLookupIndices[0] << ','
           << outdoorMapData.tileSetLookupIndices[1] << ','
           << outdoorMapData.tileSetLookupIndices[2] << ','
           << outdoorMapData.tileSetLookupIndices[3] << '\n';
    stream << "day_bits_raw=" << mapDeltaData.locationTime.weatherFlags << '\n';
    stream << "map_extra_bits_raw=" << mapExtraBitsRaw << '\n';
    stream << "flag_foggy=" << (((mapDeltaData.locationTime.weatherFlags & 0x1) != 0) ? 1 : 0) << '\n';
    stream << "flag_raining=" << (((mapExtraBitsRaw & 0x1) != 0) ? 1 : 0) << '\n';
    stream << "flag_snowing=" << (((mapExtraBitsRaw & 0x2) != 0) ? 1 : 0) << '\n';
    stream << "flag_underwater=" << (((mapExtraBitsRaw & 0x4) != 0) ? 1 : 0) << '\n';
    stream << "flag_no_terrain=" << (((mapExtraBitsRaw & 0x8) != 0) ? 1 : 0) << '\n';
    stream << "flag_always_dark=" << (((mapExtraBitsRaw & 0x10) != 0) ? 1 : 0) << '\n';
    stream << "flag_always_light=" << (((mapExtraBitsRaw & 0x20) != 0) ? 1 : 0) << '\n';
    stream << "flag_always_foggy=" << (((mapExtraBitsRaw & 0x40) != 0) ? 1 : 0) << '\n';
    stream << "flag_red_fog=" << (((mapExtraBitsRaw & 0x80) != 0) ? 1 : 0) << '\n';
    stream << "fog_weak_distance=" << mapDeltaData.locationTime.fogWeakDistance << '\n';
    stream << "fog_strong_distance=" << mapDeltaData.locationTime.fogStrongDistance << '\n';
    stream << "ceiling=" << ceiling << '\n';

    stream << "terrain\n";

    for (size_t cellIndex = 0; cellIndex < outdoorMapData.attributeMap.size(); ++cellIndex)
    {
        const uint8_t value = outdoorMapData.attributeMap[cellIndex];

        if (value == 0)
        {
            continue;
        }

        const size_t x = cellIndex % OutdoorMapData::TerrainWidth;
        const size_t y = cellIndex / OutdoorMapData::TerrainWidth;
        stream << x << ',' << y << ',' << static_cast<int>(value)
               << ',' << (((value & 0x01) != 0) ? 1 : 0)
               << ',' << (((value & 0x02) != 0) ? 1 : 0) << '\n';
    }

    stream << "interactive_faces\n";

    size_t flattenedFaceIndex = 0;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex, ++flattenedFaceIndex)
        {
            const OutdoorBModelFace &face = bmodel.faces[faceIndex];

            if (face.attributes == 0
                && face.cogNumber == 0
                && face.cogTriggeredNumber == 0
                && face.cogTrigger == 0)
            {
                continue;
            }

            stream << bmodelIndex << ',' << faceIndex << ','
                   << face.attributes << ','
                   << face.cogNumber << ','
                   << face.cogTriggeredNumber << ','
                   << face.cogTrigger << '\n';
        }
    }

    stream << "entities\n";

    for (size_t entityIndex = 0; entityIndex < outdoorMapData.entities.size(); ++entityIndex)
    {
        const OutdoorEntity &entity = outdoorMapData.entities[entityIndex];
        const uint16_t decorationFlag =
            entityIndex < mapDeltaData.decorationFlags.size()
            ? mapDeltaData.decorationFlags[entityIndex]
            : 0;

        stream << entity.name << '|'
               << entity.decorationListId << '|'
               << entity.aiAttributes << '|';
        appendNormalizedPosition(stream, entity.x, entity.y, entity.z);
        stream << '|'
               << entity.facing << '|'
               << entity.eventIdPrimary << '|'
               << entity.eventIdSecondary << '|'
               << entity.variablePrimary << '|'
               << entity.variableSecondary << '|'
               << entity.specialTrigger << '|'
               << decorationFlag << '\n';
    }

    stream << "spawns\n";

    for (const OutdoorSpawn &spawn : outdoorMapData.spawns)
    {
        appendNormalizedPosition(stream, spawn.x, spawn.y, spawn.z);
        stream << '|'
               << spawn.radius << '|'
               << spawn.typeId << '|'
               << spawn.index << '|'
               << spawn.attributes << '|'
               << spawn.group << '\n';
    }

    stream << "location\n";
    stream << mapDeltaData.locationInfo.respawnCount << '|'
           << mapDeltaData.locationInfo.lastRespawnDay << '|'
           << mapDeltaData.locationInfo.reputation << '|'
           << mapDeltaData.locationInfo.alertStatus << '\n';

    stream << "face_attribute_overrides\n";
    flattenedFaceIndex = 0;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex, ++flattenedFaceIndex)
        {
            const uint32_t baseValue = bmodel.faces[faceIndex].attributes;
            const uint32_t overrideValue =
                flattenedFaceIndex < mapDeltaData.faceAttributes.size()
                ? mapDeltaData.faceAttributes[flattenedFaceIndex]
                : baseValue;

            if (overrideValue == baseValue)
            {
                continue;
            }

            stream << bmodelIndex << ',' << faceIndex << ',' << overrideValue << '\n';
        }
    }

    stream << "actors\n";

    for (const MapDeltaActor &actor : mapDeltaData.actors)
    {
        stream << actor.name << '|'
               << actor.npcId << '|'
               << actor.attributes << '|'
               << actor.hp << '|'
               << static_cast<int>(actor.hostilityType) << '|'
               << actor.monsterInfoId << '|'
               << actor.monsterId << '|'
               << actor.radius << '|'
               << actor.height << '|'
               << actor.moveSpeed << '|';
        appendNormalizedPosition(stream, actor.x, actor.y, actor.z);
        stream << '|'
               << actor.spriteIds[0] << ','
               << actor.spriteIds[1] << ','
               << actor.spriteIds[2] << ','
               << actor.spriteIds[3] << '|'
               << actor.sectorId << '|'
               << actor.currentActionAnimation << '|'
               << actor.group << '|'
               << actor.ally << '|'
               << actor.uniqueNameIndex << '\n';
    }

    stream << "sprite_objects\n";

    for (const MapDeltaSpriteObject &spriteObject : mapDeltaData.spriteObjects)
    {
        stream << spriteObject.spriteId << '|'
               << spriteObject.objectDescriptionId << '|';
        appendNormalizedPosition(stream, spriteObject.x, spriteObject.y, spriteObject.z);
        stream << '|';
        appendNormalizedPosition(stream, spriteObject.velocityX, spriteObject.velocityY, spriteObject.velocityZ);
        stream << '|'
               << spriteObject.yawAngle << '|'
               << spriteObject.soundId << '|'
               << spriteObject.attributes << '|'
               << spriteObject.sectorId << '|'
               << spriteObject.timeSinceCreated << '|'
               << spriteObject.temporaryLifetime << '|'
               << spriteObject.glowRadiusMultiplier << '|'
               << spriteObject.spellId << '|'
               << spriteObject.spellLevel << '|'
               << spriteObject.spellSkill << '|'
               << spriteObject.field54 << '|'
               << spriteObject.spellCasterPid << '|'
               << spriteObject.spellTargetPid << '|'
               << static_cast<int>(spriteObject.lodDistance) << '|'
               << static_cast<int>(spriteObject.spellCasterAbility) << '|';
        appendNormalizedPosition(stream, spriteObject.initialX, spriteObject.initialY, spriteObject.initialZ);
        stream << '|'
               << bytesToUpperHex(spriteObject.rawContainingItem) << '\n';
    }

    stream << "chests\n";

    for (const MapDeltaChest &chest : mapDeltaData.chests)
    {
        stream << chest.chestTypeId << '|'
               << chest.flags << '|'
               << bytesToUpperHex(chest.rawItems) << '|';

        for (size_t index = 0; index < chest.inventoryMatrix.size(); ++index)
        {
            if (index > 0)
            {
                stream << ',';
            }

            stream << chest.inventoryMatrix[index];
        }

        stream << '\n';
    }

    stream << "variables_map\n";

    for (size_t index = 0; index < mapDeltaData.eventVariables.mapVars.size(); ++index)
    {
        if (index > 0)
        {
            stream << ',';
        }

        stream << static_cast<int>(mapDeltaData.eventVariables.mapVars[index]);
    }

    stream << "\nvariables_decor\n";

    for (size_t index = 0; index < mapDeltaData.eventVariables.decorVars.size(); ++index)
    {
        if (index > 0)
        {
            stream << ',';
        }

        stream << static_cast<int>(mapDeltaData.eventVariables.decorVars[index]);
    }

    stream << '\n';
    return stream.str();
}

bool loadOutdoorMapWithCompanionOptions(
    const Engine::AssetFileSystem &assetFileSystem,
    const GameDataLoader &gameDataLoader,
    const std::string &mapFileName,
    MapLoadPurpose loadPurpose,
    const MapCompanionLoadOptions &loadOptions,
    MapAssetInfo &mapAssetInfo,
    std::string &failure)
{
    const MapStatsEntry *pMapEntry = gameDataLoader.getMapStats().findByFileName(mapFileName);

    if (pMapEntry == nullptr)
    {
        failure = "could not find map stats entry for " + mapFileName;
        return false;
    }

    MapAssetLoader loader = {};
    const std::optional<MapAssetInfo> loadedMap = loader.load(
        assetFileSystem,
        *pMapEntry,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getObjectTable(),
        loadPurpose,
        loadOptions);

    if (!loadedMap)
    {
        failure = "could not load map " + mapFileName;
        return false;
    }

    if (!loadedMap->outdoorMapData || !loadedMap->outdoorMapDeltaData)
    {
        failure = "loaded map missing outdoor authored state for " + mapFileName;
        return false;
    }

    mapAssetInfo = *loadedMap;
    return true;
}

bool hasMapGeometryAsset(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &fileName)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/games");
    const std::string normalizedFileName = toLowerCopy(fileName);

    for (const std::string &entry : entries)
    {
        if (toLowerCopy(entry) == normalizedFileName)
        {
            return true;
        }
    }

    return false;
}

std::vector<std::string> collectScriptedMapFileNames(
    const Engine::AssetFileSystem &assetFileSystem,
    const GameDataLoader &gameDataLoader)
{
    std::vector<std::string> scriptedMapFileNames;

    for (const MapStatsEntry &entry : gameDataLoader.getMapStats().getEntries())
    {
        if (entry.fileName.empty())
        {
            continue;
        }

        const std::string extension = toLowerCopy(std::filesystem::path(entry.fileName).extension().string());

        if (extension != ".odm" && extension != ".blv")
        {
            continue;
        }

        if (!hasMapGeometryAsset(assetFileSystem, entry.fileName))
        {
            continue;
        }

        const std::string scriptPath =
            "Data/scripts/maps/" + toLowerCopy(std::filesystem::path(entry.fileName).stem().string()) + ".lua";

        if (assetFileSystem.exists(scriptPath))
        {
            scriptedMapFileNames.push_back(entry.fileName);
        }
    }

    return scriptedMapFileNames;
}

EventDialogContent buildScenarioDialog(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t previousMessageCount,
    bool allowNpcFallbackContent
);

bool executeDialogActionInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t actionIndex,
    EventDialogContent &dialog
);

bool initializeRegressionScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario
)
{
    scenario.actorService = buildBoundGameplayActorService(gameDataLoader);
    scenario.world.initialize(
        selectedMap.map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        &scenario.party,
        nullptr,
        gameDataLoader.getStandardItemEnchantTable(),
        gameDataLoader.getSpecialItemEnchantTable(),
        &gameDataLoader.getChestTable(),
        selectedMap.outdoorMapData,
        selectedMap.outdoorMapDeltaData,
        selectedMap.outdoorWeatherProfile,
        selectedMap.eventRuntimeState,
        selectedMap.outdoorActorPreviewBillboardSet,
        selectedMap.outdoorLandMask,
        selectedMap.outdoorDecorationCollisionSet,
        selectedMap.outdoorActorCollisionSet,
        selectedMap.outdoorSpriteObjectCollisionSet,
        selectedMap.outdoorSpriteObjectBillboardSet,
        &scenario.actorService,
        &scenario.projectileService,
        &scenario.combatController
    );

    scenario.party = {};
    scenario.party.setItemTable(&gameDataLoader.getItemTable());
    scenario.party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
    scenario.party.setItemEnchantTables(
        &gameDataLoader.getStandardItemEnchantTable(),
        &gameDataLoader.getSpecialItemEnchantTable());
    scenario.party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    scenario.party.seed(createRegressionPartySeed());
    scenario.pEventRuntimeState = scenario.world.eventRuntimeState();
    return scenario.pEventRuntimeState != nullptr;
}

bool initializeIndoorRegressionScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    IndoorRegressionScenario &scenario
)
{
    if (!selectedMap.indoorMapData || !selectedMap.indoorMapDeltaData || !selectedMap.eventRuntimeState)
    {
        return false;
    }

    scenario.party = {};
    scenario.party.setItemTable(&gameDataLoader.getItemTable());
    scenario.party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
    scenario.party.setItemEnchantTables(
        &gameDataLoader.getStandardItemEnchantTable(),
        &gameDataLoader.getSpecialItemEnchantTable());
    scenario.party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    scenario.party.seed(createRegressionPartySeed());
    scenario.mapDeltaData = *selectedMap.indoorMapDeltaData;
    scenario.eventRuntimeState = *selectedMap.eventRuntimeState;
    scenario.actorService = buildBoundGameplayActorService(gameDataLoader);
    scenario.world.initialize(
        selectedMap.map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getItemTable(),
        gameDataLoader.getChestTable(),
        &scenario.party,
        nullptr,
        &scenario.mapDeltaData,
        &scenario.eventRuntimeState,
        &scenario.actorService
    );
    return scenario.world.eventRuntimeState() != nullptr;
}

std::string describeIndoorFaceMembership(const IndoorMapData &indoorMapData, size_t faceIndex)
{
    std::ostringstream stream;
    stream << "face=" << faceIndex;

    if (faceIndex >= indoorMapData.faces.size())
    {
        stream << " invalid";
        return stream.str();
    }

    const IndoorFace &face = indoorMapData.faces[faceIndex];
    stream << " room=" << face.roomNumber << " back=" << face.roomBehindNumber;

    for (size_t sectorIndex = 0; sectorIndex < indoorMapData.sectors.size(); ++sectorIndex)
    {
        const IndoorSector &sector = indoorMapData.sectors[sectorIndex];
        const bool inFloors =
            std::find(sector.floorFaceIds.begin(), sector.floorFaceIds.end(), faceIndex) != sector.floorFaceIds.end();
        const bool inWalls =
            std::find(sector.wallFaceIds.begin(), sector.wallFaceIds.end(), faceIndex) != sector.wallFaceIds.end();
        const bool inCeilings =
            std::find(sector.ceilingFaceIds.begin(), sector.ceilingFaceIds.end(), faceIndex) != sector.ceilingFaceIds.end();
        const bool inPortals =
            std::find(sector.portalFaceIds.begin(), sector.portalFaceIds.end(), faceIndex) != sector.portalFaceIds.end();
        const bool inFaces =
            std::find(sector.faceIds.begin(), sector.faceIds.end(), faceIndex) != sector.faceIds.end();

        if (!inFloors && !inWalls && !inCeilings && !inPortals && !inFaces)
        {
            continue;
        }

        stream << " [sector=" << sectorIndex
               << " floors=" << (inFloors ? 1 : 0)
               << " walls=" << (inWalls ? 1 : 0)
               << " ceilings=" << (inCeilings ? 1 : 0)
               << " portals=" << (inPortals ? 1 : 0)
               << " faces=" << (inFaces ? 1 : 0)
               << "]";
    }

    return stream.str();
}

struct SharedHeadlessApplicationSession
{
    explicit SharedHeadlessApplicationSession(const Engine::ApplicationConfig &config)
        : application(config)
    {
    }

    GameApplication application;
    bool isGameDataLoaded = false;
};

bool prepareSharedHeadlessGameApplication(
    SharedHeadlessApplicationSession &session,
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    bool initializeView,
    std::string &failure)
{
    SDL_Environment *pEnvironment = SDL_GetEnvironment();

    if (pEnvironment == nullptr || !SDL_SetEnvironmentVariable(pEnvironment, "SDL_AUDIODRIVER", "dummy", true))
    {
        failure = "could not force dummy audio driver for headless application";
        return false;
    }

    if (!session.isGameDataLoaded)
    {
        if (!GameApplicationTestAccess::loadGameData(session.application, assetFileSystem))
        {
            failure = "could not load gameplay data";
            return false;
        }

        session.isGameDataLoaded = true;
    }

    if (GameApplicationTestAccess::mapSceneRuntime(session.application) != nullptr)
    {
        GameApplicationTestAccess::captureCurrentSceneState(session.application);
    }

    if (!GameApplicationTestAccess::loadMapByFileNameForGameplay(session.application, assetFileSystem, mapFileName))
    {
        failure = "could not load gameplay map";
        return false;
    }

    GameApplicationTestAccess::shutdownRenderer(session.application);

    if (!GameApplicationTestAccess::initializeSelectedMapRuntime(session.application, initializeView))
    {
        failure = "could not initialize gameplay runtime";
        return false;
    }

    if (GameApplicationTestAccess::mapSceneRuntime(session.application) == nullptr)
    {
        failure = "gameplay runtime was not initialized";
        return false;
    }

    return true;
}

bool loadHeadlessGameApplicationMap(
    GameApplication &application,
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &mapFileName,
    std::string &failure)
{
    GameApplicationTestAccess::captureCurrentSceneState(application);

    if (!GameApplicationTestAccess::loadMapByFileNameForGameplay(application, assetFileSystem, mapFileName))
    {
        failure = "could not load target gameplay map";
        return false;
    }

    GameApplicationTestAccess::shutdownRenderer(application);

    if (!GameApplicationTestAccess::initializeSelectedMapRuntime(application, false))
    {
        failure = "could not initialize target gameplay map";
        return false;
    }

    if (GameApplicationTestAccess::mapSceneRuntime(application) == nullptr)
    {
        failure = "target gameplay runtime was not initialized";
        return false;
    }

    return true;
}

bool prepareSharedHeadlessStartupSession(
    SharedHeadlessApplicationSession &session,
    const Engine::AssetFileSystem &assetFileSystem,
    bool initializeView,
    std::string &failure)
{
    SDL_Environment *pEnvironment = SDL_GetEnvironment();

    if (pEnvironment == nullptr || !SDL_SetEnvironmentVariable(pEnvironment, "SDL_AUDIODRIVER", "dummy", true))
    {
        failure = "could not force dummy audio driver for headless application";
        return false;
    }

    if (!session.isGameDataLoaded)
    {
        if (!GameApplicationTestAccess::loadGameData(session.application, assetFileSystem))
        {
            failure = "could not load gameplay data";
            return false;
        }

        session.isGameDataLoaded = true;
    }
    else
    {
        GameApplicationTestAccess::setBootSeededDwiOnNextRendererInit(session.application, true);
    }

    if (!GameApplicationTestAccess::bootSeededDwiOnNextRendererInit(session.application))
    {
        failure = "startup boot flag was not armed after load";
        return false;
    }

    if (!GameApplicationTestAccess::initializeStartupSession(session.application, initializeView))
    {
        failure = "could not initialize startup session";
        return false;
    }

    if (GameApplicationTestAccess::bootSeededDwiOnNextRendererInit(session.application))
    {
        failure = "startup boot flag was not consumed";
        return false;
    }

    if (GameApplicationTestAccess::outdoorPartyRuntime(session.application) == nullptr
        || GameApplicationTestAccess::outdoorWorldRuntime(session.application) == nullptr)
    {
        failure = "startup session did not initialize outdoor runtime";
        return false;
    }

    return true;
}

bool initializeRegressionScenarioFromApplication(
    const GameApplication &application,
    RegressionScenario &scenario,
    std::string &failure)
{
    const std::optional<MapAssetInfo> &selectedMap = GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
    {
        failure = "application selected map is not an outdoor map";
        return false;
    }

    scenario.party = GameApplicationTestAccess::outdoorPartyRuntime(application)->party();
    scenario.party.setItemTable(&GameApplicationTestAccess::gameDataLoader(application).getItemTable());
    scenario.party.setCharacterDollTable(&GameApplicationTestAccess::gameDataLoader(application).getCharacterDollTable());
    scenario.party.setItemEnchantTables(
        &GameApplicationTestAccess::gameDataLoader(application).getStandardItemEnchantTable(),
        &GameApplicationTestAccess::gameDataLoader(application).getSpecialItemEnchantTable());
    scenario.party.setClassSkillTable(&GameApplicationTestAccess::gameDataLoader(application).getClassSkillTable());
    scenario.actorService = buildBoundGameplayActorService(GameApplicationTestAccess::gameDataLoader(application));

    scenario.world.initialize(
        selectedMap->map,
        GameApplicationTestAccess::gameDataLoader(application).getMonsterTable(),
        GameApplicationTestAccess::gameDataLoader(application).getMonsterProjectileTable(),
        GameApplicationTestAccess::gameDataLoader(application).getObjectTable(),
        GameApplicationTestAccess::gameDataLoader(application).getSpellTable(),
        GameApplicationTestAccess::gameDataLoader(application).getItemTable(),
        &scenario.party,
        nullptr,
        GameApplicationTestAccess::gameDataLoader(application).getStandardItemEnchantTable(),
        GameApplicationTestAccess::gameDataLoader(application).getSpecialItemEnchantTable(),
        &GameApplicationTestAccess::gameDataLoader(application).getChestTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->outdoorWeatherProfile,
        selectedMap->eventRuntimeState,
        selectedMap->outdoorActorPreviewBillboardSet,
        selectedMap->outdoorLandMask,
        selectedMap->outdoorDecorationCollisionSet,
        selectedMap->outdoorActorCollisionSet,
        selectedMap->outdoorSpriteObjectCollisionSet,
        selectedMap->outdoorSpriteObjectBillboardSet,
        &scenario.actorService,
        &scenario.projectileService,
        &scenario.combatController
    );
    scenario.world.restoreSnapshot(GameApplicationTestAccess::outdoorWorldRuntime(application)->snapshot());
    scenario.pEventRuntimeState = scenario.world.eventRuntimeState();

    if (scenario.pEventRuntimeState == nullptr)
    {
        failure = "application scenario event runtime state is missing";
        return false;
    }

    return true;
}

void applyPendingCombatEventsToScenarioParty(RegressionScenario &scenario)
{
    for (const OutdoorWorldRuntime::CombatEvent &event : scenario.world.pendingCombatEvents())
    {
        if (event.type == GameplayCombatController::CombatEventType::MonsterMeleeImpact
            || event.type == GameplayCombatController::CombatEventType::PartyProjectileImpact)
        {
            const std::string status = event.type == GameplayCombatController::CombatEventType::MonsterMeleeImpact
                ? "melee damage"
                : "projectile damage";
            if (event.affectsAllParty)
            {
                scenario.party.applyDamageToAllLivingMembers(event.damage, status);
            }
            else
            {
                scenario.party.applyDamageToActiveMember(event.damage, status);
            }
        }
    }

    scenario.world.clearPendingCombatEvents();
}

EventDialogContent openNpcDialogInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint32_t npcId
)
{
    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::NpcTalk;
    context.sourceId = npcId;
    scenario.pEventRuntimeState->pendingDialogueContext = context;
    return buildScenarioDialog(gameDataLoader, selectedMap, scenario, 0, true);
}

bool openMasteryTeacherOfferInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint32_t npcId,
    const std::string &topicLabel,
    EventDialogContent &dialog
)
{
    dialog = openNpcDialogInScenario(gameDataLoader, selectedMap, scenario, npcId);
    const std::optional<size_t> offerIndex = findActionIndexByLabel(dialog, topicLabel);

    if (!offerIndex)
    {
        return false;
    }

    return executeDialogActionInScenario(gameDataLoader, selectedMap, scenario, *offerIndex, dialog);
}

bool executeLocalEventInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint16_t eventId
)
{
    if (scenario.pEventRuntimeState == nullptr)
    {
        return false;
    }

    const bool executed = scenario.eventRuntime.executeEventById(
        selectedMap.localEventProgram,
        selectedMap.globalEventProgram,
        eventId,
        *scenario.pEventRuntimeState,
        &scenario.party,
        &scenario.world
    );

    if (!executed)
    {
        return false;
    }

    scenario.world.applyEventRuntimeState();
    scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);
    return true;
}

bool executeGlobalEventInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint16_t eventId
)
{
    if (scenario.pEventRuntimeState == nullptr)
    {
        return false;
    }

    const bool executed = scenario.eventRuntime.executeEventById(
        std::nullopt,
        selectedMap.globalEventProgram,
        eventId,
        *scenario.pEventRuntimeState,
        &scenario.party,
        &scenario.world
    );

    if (!executed)
    {
        return false;
    }

    scenario.world.applyEventRuntimeState();
    scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);
    return true;
}

bool executeLocalEventInIndoorScenario(
    const MapAssetInfo &selectedMap,
    IndoorRegressionScenario &scenario,
    uint16_t eventId
)
{
    EventRuntimeState *pEventRuntimeState = scenario.world.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    const bool executed = scenario.eventRuntime.executeEventById(
        selectedMap.localEventProgram,
        selectedMap.globalEventProgram,
        eventId,
        *pEventRuntimeState,
        &scenario.party,
        &scenario.world
    );

    if (!executed)
    {
        return false;
    }

    scenario.world.applyEventRuntimeState();
    scenario.party.applyEventRuntimeState(*pEventRuntimeState);
    return true;
}

bool openLocalEventDialogInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    uint16_t eventId,
    EventDialogContent &dialog
)
{
    if (!executeLocalEventInScenario(gameDataLoader, selectedMap, scenario, eventId))
    {
        return false;
    }

    dialog = buildScenarioDialog(gameDataLoader, selectedMap, scenario, 0, true);
    return dialog.isActive;
}

bool openActorInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t actorIndex
)
{
    if (scenario.pEventRuntimeState == nullptr || !selectedMap.outdoorMapDeltaData)
    {
        return false;
    }

    if (actorIndex >= selectedMap.outdoorMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = selectedMap.outdoorMapDeltaData->actors[actorIndex];
    const std::string actorName = resolveMapDeltaActorName(gameDataLoader.getMonsterTable(), actor);

    if (actor.npcId > 0)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = static_cast<uint32_t>(actor.npcId);
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        return true;
    }

    const std::optional<GenericActorDialogResolution> resolution = resolveGenericActorDialog(
        selectedMap.map.fileName,
        actorName,
        actor.group,
        *scenario.pEventRuntimeState,
        gameDataLoader.getNpcDialogTable()
    );

    if (!resolution)
    {
        return false;
    }

    const std::optional<std::string> newsText = gameDataLoader.getNpcDialogTable().getNewsText(resolution->newsId);

    if (!newsText)
    {
        return false;
    }

    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::NpcNews;
    context.sourceId = resolution->npcId;
    context.newsId = resolution->newsId;
    context.titleOverride = actorName;
    scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    scenario.pEventRuntimeState->messages.push_back(*newsText);
    return true;
}

EventDialogContent buildScenarioDialog(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t previousMessageCount,
    bool allowNpcFallbackContent
)
{
    promoteSingleResidentHouseContext(
        *scenario.pEventRuntimeState,
        gameDataLoader.getHouseTable(),
        gameDataLoader.getNpcDialogTable(),
        scenario.world.gameMinutes()
    );

    return buildEventDialogContent(
        *scenario.pEventRuntimeState,
        previousMessageCount,
        allowNpcFallbackContent,
        &selectedMap.globalEventProgram,
        &gameDataLoader.getHouseTable(),
        &gameDataLoader.getClassSkillTable(),
        &gameDataLoader.getNpcDialogTable(),
        &selectedMap.map,
        &gameDataLoader.getMapStats().getEntries(),
        &scenario.party,
        &scenario.world,
        scenario.world.gameMinutes()
    );
}

bool executeDialogActionInScenario(
    const GameDataLoader &gameDataLoader,
    const MapAssetInfo &selectedMap,
    RegressionScenario &scenario,
    size_t actionIndex,
    EventDialogContent &dialog
)
{
    if (scenario.pEventRuntimeState == nullptr || !dialog.isActive || actionIndex >= dialog.actions.size())
    {
        return false;
    }

    const EventDialogAction &action = dialog.actions[actionIndex];
    const size_t previousMessageCount = scenario.pEventRuntimeState->messages.size();

    if (action.kind == EventDialogActionKind::HouseResident)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = action.id;
        context.hostHouseId = dialog.sourceId;
        scenario.pEventRuntimeState->dialogueState.hostHouseId = dialog.sourceId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::HouseService)
    {
        const HouseEntry *pHouseEntry = gameDataLoader.getHouseTable().get(dialog.sourceId);

        if (pHouseEntry == nullptr)
        {
            return false;
        }

        const HouseActionId houseActionId = static_cast<HouseActionId>(action.id);
        const DialogueMenuId menuId = dialogueMenuIdForHouseAction(houseActionId);

        if (menuId != DialogueMenuId::None)
        {
            scenario.pEventRuntimeState->dialogueState.menuStack.push_back(menuId);
        }
        else if (houseActionId == HouseActionId::TavernArcomageRules)
        {
            const std::optional<std::string> rulesText = gameDataLoader.getNpcDialogTable().getText(136);

            if (rulesText.has_value() && !rulesText->empty())
            {
                scenario.pEventRuntimeState->messages.push_back(*rulesText);
            }
        }
        else if (houseActionId == HouseActionId::TavernArcomageVictoryConditions)
        {
            const ArcomageTavernRule *pRule = gameDataLoader.getArcomageLibrary().ruleForHouse(pHouseEntry->id);

            if (pRule != nullptr)
            {
                const std::optional<std::string> victoryText =
                    gameDataLoader.getNpcDialogTable().getText(pRule->victoryTextId);

                if (victoryText.has_value() && !victoryText->empty())
                {
                    scenario.pEventRuntimeState->messages.push_back(*victoryText);
                }
            }
        }
        else if (houseActionId == HouseActionId::TavernArcomagePlay)
        {
            EventRuntimeState::PendingArcomageGame pendingGame = {};
            pendingGame.houseId = pHouseEntry->id;
            scenario.pEventRuntimeState->pendingArcomageGame = std::move(pendingGame);
            dialog = {};
            return true;
        }
        else
        {
            HouseActionOption option = {};
            option.id = houseActionId;
            option.label = action.label;
            option.argument = action.argument;
            const HouseActionResult result = performHouseAction(
                option,
                *pHouseEntry,
                scenario.party,
                &gameDataLoader.getClassSkillTable(),
                &scenario.world
            );

            const bool suppressDialogueMessages =
                option.id == HouseActionId::TrainingTrainActiveMember
                || option.id == HouseActionId::TempleDonate;

            for (const std::string &message : result.messages)
            {
                if (!suppressDialogueMessages)
                {
                    scenario.pEventRuntimeState->messages.push_back(message);
                }
            }
        }

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::HouseService;
        context.sourceId = dialog.sourceId;
        context.hostHouseId = dialog.sourceId;
        scenario.pEventRuntimeState->dialogueState.hostHouseId = dialog.sourceId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::RosterJoinOffer)
    {
        const std::optional<NpcDialogTable::RosterJoinOffer> offer =
            gameDataLoader.getNpcDialogTable().getRosterJoinOfferForTopic(action.id);

        if (!offer)
        {
            return false;
        }

        const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(offer->inviteTextId);

        if (inviteText && !inviteText->empty())
        {
            scenario.pEventRuntimeState->messages.push_back(*inviteText);
        }

        EventRuntimeState::DialogueOfferState invite = {};
        invite.kind = DialogueOfferKind::RosterJoin;
        invite.npcId = dialog.sourceId;
        invite.topicId = action.id;
        invite.messageTextId = offer->inviteTextId;
        invite.rosterId = offer->rosterId;
        invite.partyFullTextId = offer->partyFullTextId;
        scenario.pEventRuntimeState->dialogueState.currentOffer = std::move(invite);

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = dialog.sourceId;
        context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::RosterJoinAccept)
    {
        if (!scenario.pEventRuntimeState->dialogueState.currentOffer
            || scenario.pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::RosterJoin)
        {
            return false;
        }

        const EventRuntimeState::DialogueOfferState invite = *scenario.pEventRuntimeState->dialogueState.currentOffer;
        scenario.pEventRuntimeState->dialogueState.currentOffer.reset();

        if (scenario.party.isFull())
        {
            scenario.pEventRuntimeState->npcHouseOverrides[invite.npcId] = AdventurersInnHouseId;
            const std::optional<std::string> fullPartyText =
                gameDataLoader.getNpcDialogTable().getText(invite.partyFullTextId);

            if (fullPartyText && !fullPartyText->empty())
            {
                scenario.pEventRuntimeState->messages.push_back(*fullPartyText);
            }
        }
        else
        {
            const RosterEntry *pRosterEntry = gameDataLoader.getRosterTable().get(invite.rosterId);

            if (pRosterEntry == nullptr || !scenario.party.recruitRosterMember(*pRosterEntry))
            {
                return false;
            }

            scenario.pEventRuntimeState->unavailableNpcIds.insert(invite.npcId);
            scenario.pEventRuntimeState->npcHouseOverrides.erase(invite.npcId);
            scenario.pEventRuntimeState->messages.push_back(pRosterEntry->name + " joined the party.");
        }

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = invite.npcId;
        context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::RosterJoinDecline)
    {
        const uint32_t npcId =
            (scenario.pEventRuntimeState->dialogueState.currentOffer
             && scenario.pEventRuntimeState->dialogueState.currentOffer->kind == DialogueOfferKind::RosterJoin)
            ? scenario.pEventRuntimeState->dialogueState.currentOffer->npcId
            : dialog.sourceId;
        scenario.pEventRuntimeState->dialogueState.currentOffer.reset();

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = npcId;
        context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::MasteryTeacherOffer)
    {
        EventRuntimeState::DialogueOfferState offer = {};
        offer.kind = DialogueOfferKind::MasteryTeacher;
        offer.npcId = dialog.sourceId;
        offer.topicId = action.id;
        scenario.pEventRuntimeState->dialogueState.currentOffer = std::move(offer);

        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = dialog.sourceId;
        context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
        scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else if (action.kind == EventDialogActionKind::MasteryTeacherLearn)
    {
        if (!scenario.pEventRuntimeState->dialogueState.currentOffer
            || scenario.pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::MasteryTeacher)
        {
            return false;
        }

        std::string message;

        if (applyMasteryTeacherTopic(
                scenario.pEventRuntimeState->dialogueState.currentOffer->topicId,
                scenario.party,
                gameDataLoader.getClassSkillTable(),
                gameDataLoader.getNpcDialogTable(),
                message))
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = scenario.pEventRuntimeState->dialogueState.currentOffer->npcId;
            context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
            scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = scenario.pEventRuntimeState->dialogueState.currentOffer->npcId;
            context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
            scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
    }
    else if (action.kind == EventDialogActionKind::NpcTopic)
    {
        bool executed = false;

        if (action.textOnly)
        {
            const std::optional<NpcDialogTable::ResolvedTopic> topic =
                gameDataLoader.getNpcDialogTable().getTopicById(action.secondaryId != 0 ? action.secondaryId : action.id);

            if (topic && !topic->text.empty())
            {
                scenario.pEventRuntimeState->messages.push_back(topic->text);
                executed = true;
            }
        }
        else
        {
            executed = scenario.eventRuntime.executeEventById(
                std::nullopt,
                selectedMap.globalEventProgram,
                static_cast<uint16_t>(action.id),
                *scenario.pEventRuntimeState,
                &scenario.party,
                &scenario.world
            );
        }

        if (!executed)
        {
            return false;
        }

        scenario.world.applyEventRuntimeState();
        scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);

        if (!scenario.pEventRuntimeState->pendingDialogueContext)
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = dialog.sourceId;
            context.hostHouseId = scenario.pEventRuntimeState->dialogueState.hostHouseId;
            scenario.pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
    }
    else
    {
        return false;
    }

    dialog = buildScenarioDialog(
        gameDataLoader,
        selectedMap,
        scenario,
        previousMessageCount,
        action.kind != EventDialogActionKind::RosterJoinAccept
    );
    return true;
}
}

HeadlessGameplayDiagnostics::HeadlessGameplayDiagnostics(const Engine::ApplicationConfig &config)
    : m_config(config)
{
}

int HeadlessGameplayDiagnostics::runProfileFullMapLoad(
    const std::filesystem::path &basePath,
    const std::string &mapFileName
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load base game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileName(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not full-load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap)
    {
        std::cerr << "Headless diagnostic failed: selected map missing after full load\n";
        return 1;
    }

    std::cout << "Headless load profile complete: map=\"" << selectedMap->map.name
              << "\" file=" << selectedMap->map.fileName
              << '\n';
    return 0;
}

int HeadlessGameplayDiagnostics::runSimulateActor(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex,
    int stepCount,
    float deltaSeconds
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        nullptr,
        nullptr,
        gameDataLoader.getStandardItemEnchantTable(),
        gameDataLoader.getSpecialItemEnchantTable(),
        &gameDataLoader.getChestTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->outdoorWeatherProfile,
        selectedMap->eventRuntimeState,
        selectedMap->outdoorActorPreviewBillboardSet,
        selectedMap->outdoorLandMask,
        selectedMap->outdoorDecorationCollisionSet,
        selectedMap->outdoorActorCollisionSet,
        selectedMap->outdoorSpriteObjectCollisionSet,
        selectedMap->outdoorSpriteObjectBillboardSet
    );

    const OutdoorWorldRuntime::MapActorState *pStartActor = outdoorWorldRuntime.mapActorState(actorIndex);

    if (pStartActor == nullptr)
    {
        std::cerr << "Headless diagnostic failed: actor " << actorIndex << " missing\n";
        return 1;
    }

    const int startX = pStartActor->x;
    const int startY = pStartActor->y;
    const int startZ = pStartActor->z;
    const float partyX = static_cast<float>(startX + 6000);
    const float partyY = static_cast<float>(startY);
    const float partyZ = static_cast<float>(startZ);
    bool sawStanding = pStartActor->aiState == OutdoorWorldRuntime::ActorAiState::Standing;
    bool sawWandering = pStartActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
    bool sawWalkingAnimation = pStartActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
    bool sawMovement = false;

    std::cout << "Headless actor simulation: actor=" << actorIndex
              << " start_pos=(" << startX << "," << startY << "," << startZ << ")"
              << " start_ai=" << static_cast<int>(pStartActor->aiState)
              << " start_anim=" << static_cast<int>(pStartActor->animation)
              << '\n';

    for (int step = 0; step < stepCount; ++step)
    {
        outdoorWorldRuntime.updateMapActors(deltaSeconds, partyX, partyY, partyZ);
        const OutdoorWorldRuntime::MapActorState *pActor = outdoorWorldRuntime.mapActorState(actorIndex);

        if (pActor == nullptr)
        {
            std::cerr << "Headless diagnostic failed: actor disappeared during simulation\n";
            return 1;
        }

        sawStanding = sawStanding || pActor->aiState == OutdoorWorldRuntime::ActorAiState::Standing;
        sawWandering = sawWandering || pActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
        sawWalkingAnimation = sawWalkingAnimation || pActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
        sawMovement = sawMovement || pActor->x != startX || pActor->y != startY;
    }

    const OutdoorWorldRuntime::MapActorState *pEndActor = outdoorWorldRuntime.mapActorState(actorIndex);
    std::cout << "Headless actor simulation result: actor=" << actorIndex
              << " end_pos=(" << pEndActor->x << "," << pEndActor->y << "," << pEndActor->z << ")"
              << " end_ai=" << static_cast<int>(pEndActor->aiState)
              << " end_anim=" << static_cast<int>(pEndActor->animation)
              << " saw_standing=" << (sawStanding ? "yes" : "no")
              << " saw_wandering=" << (sawWandering ? "yes" : "no")
              << " saw_walking_anim=" << (sawWalkingAnimation ? "yes" : "no")
              << " saw_movement=" << (sawMovement ? "yes" : "no")
              << '\n';
    return 0;
}

int HeadlessGameplayDiagnostics::runTraceActorAi(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex,
    int stepCount,
    float deltaSeconds
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        nullptr,
        nullptr,
        gameDataLoader.getStandardItemEnchantTable(),
        gameDataLoader.getSpecialItemEnchantTable(),
        &gameDataLoader.getChestTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->outdoorWeatherProfile,
        selectedMap->eventRuntimeState,
        selectedMap->outdoorActorPreviewBillboardSet,
        selectedMap->outdoorLandMask,
        selectedMap->outdoorDecorationCollisionSet,
        selectedMap->outdoorActorCollisionSet,
        selectedMap->outdoorSpriteObjectCollisionSet,
        selectedMap->outdoorSpriteObjectBillboardSet
    );

    const OutdoorWorldRuntime::MapActorState *pStartActor = outdoorWorldRuntime.mapActorState(actorIndex);

    if (pStartActor == nullptr)
    {
        std::cerr << "Headless diagnostic failed: actor " << actorIndex << " missing\n";
        return 1;
    }

    const float partyX = static_cast<float>(pStartActor->x + 6000);
    const float partyY = static_cast<float>(pStartActor->y);
    const float partyZ = static_cast<float>(pStartActor->z);

    std::cout << "Headless actor AI trace: actor=" << actorIndex
              << " start_pos=(" << pStartActor->x << "," << pStartActor->y << "," << pStartActor->z << ")"
              << " party_pos=(" << partyX << "," << partyY << "," << partyZ << ")"
              << " steps=" << stepCount
              << " delta=" << deltaSeconds
              << '\n';

    for (int step = 0; step < stepCount; ++step)
    {
        const std::optional<OutdoorWorldRuntime::ActorDecisionDebugInfo> before =
            outdoorWorldRuntime.debugActorDecisionInfo(actorIndex, partyX, partyY, partyZ);

        if (!before)
        {
            std::cerr << "Headless diagnostic failed: debug info unavailable before update\n";
            return 1;
        }

        std::cout << "step=" << step
                  << " before"
                  << " ai=" << actorAiStateName(before->aiState) << "(" << static_cast<int>(before->aiState) << ")"
                  << " anim=" << actorAnimationName(before->animation) << "(" << static_cast<int>(before->animation) << ")"
                  << " hostility=" << static_cast<unsigned>(before->hostilityType)
                  << " hostile_party=" << (before->hostileToParty ? "yes" : "no")
                  << " detected_party=" << (before->hasDetectedParty ? "yes" : "no")
                  << " ai_type=" << monsterAiTypeName(before->monsterAiType)
                  << " idle_secs=" << before->idleDecisionSeconds
                  << " action_secs=" << before->actionSeconds
                  << " cooldown=" << before->attackCooldownSeconds
                  << " decisions=(" << before->idleDecisionCount
                  << "," << before->pursueDecisionCount
                  << "," << before->attackDecisionCount << ")"
                  << " target=" << debugTargetKindName(before->targetKind);

        if (before->targetKind == OutdoorWorldRuntime::DebugTargetKind::Actor)
        {
            std::cout << ":" << before->targetActorIndex
                      << " monster=" << before->targetMonsterId;
        }

        std::cout << " relation=" << before->relationToTarget
                  << " target_dist=" << before->targetDistance
                  << " edge=" << before->targetEdgeDistance
                  << " target_sense=" << (before->targetCanSense ? "yes" : "no")
                  << " party_sense=" << (before->canSenseParty ? "yes" : "no")
                  << " party_range=" << before->partySenseRange
                  << " party_dist=" << before->distanceToParty
                  << " promote=" << (before->shouldPromoteHostility ? "yes" : "no")
                  << " promote_range=" << before->promotionRange
                  << " engage=" << (before->shouldEngageTarget ? "yes" : "no")
                  << " flee=" << (before->shouldFlee ? "yes" : "no")
                  << " melee=" << (before->inMeleeRange ? "yes" : "no")
                  << " atk_done=" << (before->attackJustCompleted ? "yes" : "no")
                  << " atk_progress=" << (before->attackInProgress ? "yes" : "no")
                  << " near_party=" << (before->friendlyNearParty ? "yes" : "no")
                  << '\n';

        outdoorWorldRuntime.updateMapActors(deltaSeconds, partyX, partyY, partyZ);

        const OutdoorWorldRuntime::MapActorState *pAfter = outdoorWorldRuntime.mapActorState(actorIndex);

        if (pAfter == nullptr)
        {
            std::cerr << "Headless diagnostic failed: actor disappeared during trace\n";
            return 1;
        }

        std::cout << "step=" << step
                  << " after"
                  << " pos=(" << pAfter->x << "," << pAfter->y << "," << pAfter->z << ")"
                  << " ai=" << actorAiStateName(pAfter->aiState) << "(" << static_cast<int>(pAfter->aiState) << ")"
                  << " anim=" << actorAnimationName(pAfter->animation) << "(" << static_cast<int>(pAfter->animation) << ")"
                  << " hostility=" << static_cast<unsigned>(pAfter->hostilityType)
                  << " detected_party=" << (pAfter->hasDetectedParty ? "yes" : "no")
                  << " decisions=(" << pAfter->idleDecisionCount
                  << "," << pAfter->pursueDecisionCount
                  << "," << pAfter->attackDecisionCount << ")"
                  << '\n';
    }

    return 0;
}

int HeadlessGameplayDiagnostics::runInspectActorPreview(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileName(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not full-load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorActorPreviewBillboardSet)
    {
        std::cerr << "Headless diagnostic failed: selected map has no outdoor actor previews\n";
        return 1;
    }

    const ActorPreviewBillboardSet &billboardSet = *selectedMap->outdoorActorPreviewBillboardSet;
    size_t billboardIndex = 0;
    const ActorPreviewBillboard *pBillboard = findCompanionActorBillboard(billboardSet, actorIndex, billboardIndex);

    if (pBillboard == nullptr)
    {
        std::cerr << "Headless diagnostic failed: companion actor billboard " << actorIndex << " missing\n";
        return 1;
    }

    std::cout << "Headless actor preview: actor=" << actorIndex
              << " billboard_index=" << billboardIndex
              << " name=\"" << pBillboard->actorName << "\""
              << '\n';

    const std::array<OutdoorWorldRuntime::ActorAnimation, 2> actions = {
        OutdoorWorldRuntime::ActorAnimation::Standing,
        OutdoorWorldRuntime::ActorAnimation::Walking
    };

    for (OutdoorWorldRuntime::ActorAnimation action : actions)
    {
        uint16_t spriteFrameIndex = pBillboard->spriteFrameIndex;
        const uint16_t actionFrameIndex = pBillboard->actionSpriteFrameIndices[static_cast<size_t>(action)];

        if (actionFrameIndex != 0)
        {
            spriteFrameIndex = actionFrameIndex;
        }

        const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(spriteFrameIndex, 0);

        if (pFrame == nullptr)
        {
            std::cout << "  action=" << static_cast<int>(action) << " sprite frame missing\n";
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const OutdoorBitmapTexture *pTexture = findBillboardTexture(
            billboardSet,
            resolvedTexture.textureName,
            pFrame->paletteId
        );

        std::cout << "  action=" << static_cast<int>(action)
                  << " sprite_frame=" << spriteFrameIndex
                  << " sprite=\"" << pFrame->spriteName << "\""
                  << " texture=\"" << resolvedTexture.textureName << "\""
                  << " palette=" << pFrame->paletteId
                  << '\n';

        if (pTexture == nullptr)
        {
            std::cout << "    texture not found in loaded billboard textures\n";
            continue;
        }

        const TextureColorStats colorStats = analyzeTextureColors(pTexture->pixels);
        std::cout << "    texture size=" << pTexture->width << "x" << pTexture->height
                  << " opaque_pixels=" << colorStats.opaquePixelCount
                  << " magenta_pixels=" << colorStats.magentaPixelCount
                  << " green_pixels=" << colorStats.greenPixelCount
                  << '\n';
    }

    const ActorPreviewAnimationStats animationStats = analyzeActorPreviewAnimation(billboardSet, *pBillboard);
    std::cout << "  sampled_animation"
              << " samples=" << animationStats.sampleCount
              << " green_dominant=" << animationStats.greenDominantSampleCount
              << " magenta_dominant=" << animationStats.magentaDominantSampleCount
              << " missing=" << animationStats.missingTextureSampleCount
              << " distinct_walking_variants=" << animationStats.distinctWalkingFrameCount
              << '\n';

    return 0;
}

int HeadlessGameplayDiagnostics::runDumpActorSupport(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem)
        || !gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    if (actorIndex >= selectedMap->outdoorMapDeltaData->actors.size())
    {
        std::cerr << "Headless diagnostic failed: actor index out of range\n";
        return 1;
    }

    const MapDeltaActor &rawActor = selectedMap->outdoorMapDeltaData->actors[actorIndex];
    const float worldX = static_cast<float>(rawActor.x);
    const float worldY = static_cast<float>(rawActor.y);
    const float worldZ = static_cast<float>(rawActor.z);
    const float terrainHeight = sampleOutdoorTerrainHeight(*selectedMap->outdoorMapData, worldX, worldY);
    const OutdoorSupportFloorSample pointSupport = sampleOutdoorSupportFloor(
        *selectedMap->outdoorMapData,
        worldX,
        worldY,
        worldZ,
        std::numeric_limits<float>::max(),
        5.0f);
    const OutdoorSupportFloorSample radiusSupport = sampleOutdoorSupportFloor(
        *selectedMap->outdoorMapData,
        worldX,
        worldY,
        worldZ,
        std::numeric_limits<float>::max(),
        std::max(5.0f, static_cast<float>(rawActor.radius)));

    std::cout << "Actor support dump: actor=" << actorIndex
              << " name=\"" << rawActor.name << "\""
              << " pos=" << worldX << "," << worldY << "," << worldZ
              << " radius=" << rawActor.radius
              << " height=" << rawActor.height
              << '\n';
    std::cout << "  terrain_height=" << terrainHeight << '\n';
    std::cout << "  point_support=" << pointSupport.height
              << " from_bmodel=" << (pointSupport.fromBModel ? "yes" : "no")
              << " bmodel=" << pointSupport.bModelIndex
              << " face=" << pointSupport.faceIndex
              << '\n';
    std::cout << "  radius_support=" << radiusSupport.height
              << " from_bmodel=" << (radiusSupport.fromBModel ? "yes" : "no")
              << " bmodel=" << radiusSupport.bModelIndex
              << " face=" << radiusSupport.faceIndex
              << '\n';

    size_t printedCount = 0;

    for (size_t bModelIndex = 0; bModelIndex < selectedMap->outdoorMapData->bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bModel = selectedMap->outdoorMapData->bmodels[bModelIndex];

        for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
        {
            OutdoorFaceGeometryData geometry = {};

            if (!buildOutdoorFaceGeometry(bModel, bModelIndex, bModel.faces[faceIndex], faceIndex, geometry)
                || !geometry.isWalkable)
            {
                continue;
            }

            if (worldX < geometry.minX - static_cast<float>(rawActor.radius)
                || worldX > geometry.maxX + static_cast<float>(rawActor.radius)
                || worldY < geometry.minY - static_cast<float>(rawActor.radius)
                || worldY > geometry.maxY + static_cast<float>(rawActor.radius))
            {
                continue;
            }

            const bool insidePoint = isPointInsideOutdoorPolygon(worldX, worldY, geometry.vertices);
            const bool insideRadius = insidePoint;

            if (!insidePoint && !insideRadius)
            {
                continue;
            }

            const float faceHeight = geometry.polygonType == 0x3
                ? geometry.vertices.front().z
                : geometry.vertices.front().z
                    - (geometry.normal.x * (worldX - geometry.vertices.front().x)
                        + geometry.normal.y * (worldY - geometry.vertices.front().y))
                        / geometry.normal.z;

            std::cout << "  candidate[" << printedCount << "]"
                      << " bmodel=" << bModelIndex
                      << " face=" << faceIndex
                      << " poly=" << static_cast<int>(geometry.polygonType)
                      << " attrs=0x" << std::hex << geometry.attributes << std::dec
                      << " height=" << faceHeight
                      << " inside_point=" << (insidePoint ? "yes" : "no")
                      << " inside_radius=" << (insideRadius ? "yes" : "no")
                      << " model=\"" << geometry.modelName << "\""
                      << '\n';

            ++printedCount;

            if (printedCount >= 24)
            {
                return 0;
            }
        }
    }

    return 0;
}

int HeadlessGameplayDiagnostics::runDumpActorPreviewTexture(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex,
    const std::filesystem::path &outputPath
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.load(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileName(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not full-load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorActorPreviewBillboardSet)
    {
        std::cerr << "Headless diagnostic failed: selected map has no outdoor actor previews\n";
        return 1;
    }

    const ActorPreviewBillboardSet &billboardSet = *selectedMap->outdoorActorPreviewBillboardSet;
    size_t billboardIndex = 0;
    const ActorPreviewBillboard *pBillboard = findCompanionActorBillboard(billboardSet, actorIndex, billboardIndex);

    if (pBillboard == nullptr)
    {
        std::cerr << "Headless diagnostic failed: companion actor billboard " << actorIndex << " missing\n";
        return 1;
    }

    const SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(pBillboard->spriteFrameIndex, 0);

    if (pFrame == nullptr)
    {
        std::cerr << "Headless diagnostic failed: actor preview frame missing\n";
        return 1;
    }

    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
    const OutdoorBitmapTexture *pTexture =
        findBillboardTexture(billboardSet, resolvedTexture.textureName, pFrame->paletteId);

    if (pTexture == nullptr)
    {
        std::cerr << "Headless diagnostic failed: resolved preview texture missing\n";
        return 1;
    }

    if (!saveTextureAsPng(*pTexture, outputPath))
    {
        std::cerr << "Headless diagnostic failed: could not save texture dump to \"" << outputPath.string() << "\"\n";
        return 1;
    }

    const TextureColorStats colorStats = analyzeTextureColors(pTexture->pixels);
    std::cout << "Headless actor preview dump: actor=" << actorIndex
              << " billboard_index=" << billboardIndex
              << " name=\"" << pBillboard->actorName << "\""
              << " sprite=\"" << pFrame->spriteName << "\""
              << " texture=\"" << resolvedTexture.textureName << "\""
              << " palette=" << pFrame->paletteId
              << " output=\"" << outputPath.string() << "\""
              << '\n';
    std::cout << "  size=" << pTexture->width << "x" << pTexture->height
              << " opaque_pixels=" << colorStats.opaquePixelCount
              << " magenta_pixels=" << colorStats.magentaPixelCount
              << " green_pixels=" << colorStats.greenPixelCount
              << '\n';

    return 0;
}

int HeadlessGameplayDiagnostics::runOpenEvent(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    uint16_t eventId
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        nullptr,
        nullptr,
        gameDataLoader.getStandardItemEnchantTable(),
        gameDataLoader.getSpecialItemEnchantTable(),
        &gameDataLoader.getChestTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->outdoorWeatherProfile,
        selectedMap->eventRuntimeState,
        selectedMap->outdoorActorPreviewBillboardSet,
        selectedMap->outdoorLandMask,
        selectedMap->outdoorDecorationCollisionSet,
        selectedMap->outdoorActorCollisionSet,
        selectedMap->outdoorSpriteObjectCollisionSet,
        selectedMap->outdoorSpriteObjectBillboardSet
    );

    Party party = {};
    party.setItemTable(&gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &gameDataLoader.getStandardItemEnchantTable(),
        &gameDataLoader.getSpecialItemEnchantTable());
    party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    party.reset();

    EventRuntime eventRuntime;
    EventRuntimeState *pEventRuntimeState = outdoorWorldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        std::cerr << "Headless diagnostic failed: event runtime state is not available\n";
        return 1;
    }

    std::cout << "Headless diagnostic: map=" << selectedMap->map.fileName
              << " id=" << selectedMap->map.id
              << " event=" << eventId
              << '\n';

    const bool executed = eventRuntime.executeEventById(
        selectedMap->localEventProgram,
        selectedMap->globalEventProgram,
        eventId,
        *pEventRuntimeState,
        &party,
        &outdoorWorldRuntime
    );

    if (!executed)
    {
        std::cout << "Headless diagnostic: event " << eventId << " unresolved\n";
        return 2;
    }

    outdoorWorldRuntime.applyEventRuntimeState();
    party.applyEventRuntimeState(*pEventRuntimeState);

    if (const EventRuntimeState::PendingMapMove *pPendingMapMove = outdoorWorldRuntime.pendingMapMove())
    {
        std::cout << "Headless diagnostic: pending map move=("
                  << pPendingMapMove->x << ","
                  << pPendingMapMove->y << ","
                  << pPendingMapMove->z << ")";

        if (pPendingMapMove->mapName && !pPendingMapMove->mapName->empty())
        {
            std::cout << " name=\"" << *pPendingMapMove->mapName << "\"";
        }

        std::cout << '\n';
    }

    if (pEventRuntimeState->pendingDialogueContext)
    {
        promoteSingleResidentHouseContext(
            *pEventRuntimeState,
            gameDataLoader.getHouseTable(),
            gameDataLoader.getNpcDialogTable(),
            outdoorWorldRuntime.currentHour()
        );

        const EventRuntimeState::PendingDialogueContext &context = *pEventRuntimeState->pendingDialogueContext;

        if (context.kind == DialogueContextKind::HouseService)
        {
            std::cout << "Headless diagnostic: pending house=" << context.sourceId << '\n';
        }
        else if (context.kind == DialogueContextKind::NpcTalk)
        {
            std::cout << "Headless diagnostic: pending npc=" << context.sourceId << '\n';
        }
        else if (context.kind == DialogueContextKind::NpcNews)
        {
            std::cout << "Headless diagnostic: pending news=" << context.newsId << '\n';
        }
    }

    const EventDialogContent dialog = buildHeadlessDialog(
        *pEventRuntimeState,
        0,
        true,
        selectedMap->globalEventProgram,
        gameDataLoader,
        &party,
        outdoorWorldRuntime.currentHour()
    );
    printDialogSummary(dialog);

    if (!pEventRuntimeState->grantedItemIds.empty())
    {
        std::cout << "Headless diagnostic: granted items=";

        for (size_t itemIndex = 0; itemIndex < pEventRuntimeState->grantedItemIds.size(); ++itemIndex)
        {
            if (itemIndex > 0)
            {
                std::cout << ',';
            }

            std::cout << pEventRuntimeState->grantedItemIds[itemIndex];
        }

        std::cout << '\n';
    }

    if (!pEventRuntimeState->removedItemIds.empty())
    {
        std::cout << "Headless diagnostic: removed items=";

        for (size_t itemIndex = 0; itemIndex < pEventRuntimeState->removedItemIds.size(); ++itemIndex)
        {
            if (itemIndex > 0)
            {
                std::cout << ',';
            }

            std::cout << pEventRuntimeState->removedItemIds[itemIndex];
        }

        std::cout << '\n';
    }

    if (const OutdoorWorldRuntime::ChestViewState *pActiveChestView = outdoorWorldRuntime.activeChestView())
    {
        printChestSummary(*pActiveChestView, gameDataLoader.getItemTable());
    }
    else
    {
        std::cout << "Headless diagnostic: no active chest view\n";
    }

    if (const OutdoorWorldRuntime::CorpseViewState *pActiveCorpseView = outdoorWorldRuntime.activeCorpseView())
    {
        printCorpseSummary(*pActiveCorpseView, gameDataLoader.getItemTable());
    }
    else
    {
        std::cout << "Headless diagnostic: no active corpse view\n";
    }

    if (!outdoorWorldRuntime.pendingAudioEvents().empty())
    {
        std::cout << "Headless diagnostic: audio events=" << outdoorWorldRuntime.pendingAudioEvents().size() << '\n';

        for (const OutdoorWorldRuntime::AudioEvent &event : outdoorWorldRuntime.pendingAudioEvents())
        {
            std::cout << "  sound=" << event.soundId
                      << " source=" << event.sourceId
                      << " reason=" << event.reason
                      << '\n';
        }
    }

    return 0;
}

int HeadlessGameplayDiagnostics::runOpenActor(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    size_t actorIndex
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
    {
        std::cerr << "Headless diagnostic failed: selected map has no outdoor actors\n";
        return 1;
    }

    if (actorIndex >= selectedMap->outdoorMapDeltaData->actors.size())
    {
        std::cerr << "Headless diagnostic failed: actor index out of range\n";
        return 2;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        nullptr,
        nullptr,
        gameDataLoader.getStandardItemEnchantTable(),
        gameDataLoader.getSpecialItemEnchantTable(),
        &gameDataLoader.getChestTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->outdoorWeatherProfile,
        selectedMap->eventRuntimeState,
        selectedMap->outdoorActorPreviewBillboardSet,
        selectedMap->outdoorLandMask,
        selectedMap->outdoorDecorationCollisionSet,
        selectedMap->outdoorActorCollisionSet,
        selectedMap->outdoorSpriteObjectCollisionSet,
        selectedMap->outdoorSpriteObjectBillboardSet
    );

    Party party = {};
    party.setItemTable(&gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &gameDataLoader.getStandardItemEnchantTable(),
        &gameDataLoader.getSpecialItemEnchantTable());
    party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    party.reset();

    EventRuntimeState *pEventRuntimeState = outdoorWorldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        std::cerr << "Headless diagnostic failed: event runtime state is not available\n";
        return 1;
    }

    const MapDeltaActor &actor = selectedMap->outdoorMapDeltaData->actors[actorIndex];
    const std::string actorName = resolveMapDeltaActorName(gameDataLoader.getMonsterTable(), actor);
    std::cout << "Headless actor diagnostic: index=" << actorIndex
              << " name=\"" << actorName << "\""
              << " npc=" << actor.npcId
              << " monsterInfo=" << actor.monsterInfoId
              << " monsterId=" << actor.monsterId
              << " group=" << actor.group
              << " unique=" << actor.uniqueNameIndex
              << '\n';

    if (const OutdoorWorldRuntime::MapActorState *pActorState = outdoorWorldRuntime.mapActorState(actorIndex))
    {
        std::cout << "  runtime monster=" << pActorState->monsterId
                  << " hp=" << pActorState->currentHp << "/" << pActorState->maxHp
                  << " hostile=" << (pActorState->hostileToParty ? "yes" : "no")
                  << " hostilityType=" << static_cast<unsigned>(pActorState->hostilityType)
                  << '\n';
    }

    if (actor.npcId > 0)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::NpcTalk;
        context.sourceId = static_cast<uint32_t>(actor.npcId);
        pEventRuntimeState->pendingDialogueContext = std::move(context);
    }
    else
    {
        const std::optional<GenericActorDialogResolution> resolution = resolveGenericActorDialog(
            selectedMap->map.fileName,
            actorName,
            actor.group,
            *pEventRuntimeState,
            gameDataLoader.getNpcDialogTable()
        );

        std::cout << "  resolved_generic_npc="
                  << (resolution ? std::to_string(resolution->npcId) : "-")
                  << " resolved_news="
                  << (resolution ? std::to_string(resolution->newsId) : "0")
                  << '\n';

        if (resolution)
        {
            const std::optional<std::string> newsText =
                gameDataLoader.getNpcDialogTable().getNewsText(resolution->newsId);

            if (newsText)
            {
                EventRuntimeState::PendingDialogueContext context = {};
                context.kind = DialogueContextKind::NpcNews;
                context.sourceId = resolution->npcId;
                context.newsId = resolution->newsId;
                context.titleOverride = actorName;
                pEventRuntimeState->pendingDialogueContext = std::move(context);
                pEventRuntimeState->messages.push_back(*newsText);
            }
        }
    }

    const EventDialogContent dialog = buildHeadlessDialog(
        *pEventRuntimeState,
        0,
        true,
        selectedMap->globalEventProgram,
        gameDataLoader,
        &party,
        outdoorWorldRuntime.currentHour()
    );

    if (!dialog.isActive)
    {
        std::cout << "Headless actor diagnostic: no dialog resolved\n";
        return 3;
    }

    printDialogSummary(dialog);
    return 0;
}

int HeadlessGameplayDiagnostics::runDialogSequence(
    const std::filesystem::path &basePath,
    const std::string &mapFileName,
    uint16_t eventId,
    const std::vector<size_t> &actionIndices
) const
{
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Headless diagnostic failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Headless diagnostic failed: could not load game data\n";
        return 1;
    }

    if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
    {
        std::cerr << "Headless diagnostic failed: could not load map \"" << mapFileName << "\"\n";
        return 1;
    }

    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (!selectedMap || !selectedMap->outdoorMapData)
    {
        std::cerr << "Headless diagnostic failed: selected map is not an outdoor map\n";
        return 1;
    }

    OutdoorWorldRuntime outdoorWorldRuntime;
    outdoorWorldRuntime.initialize(
        selectedMap->map,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getMonsterProjectileTable(),
        gameDataLoader.getObjectTable(),
        gameDataLoader.getSpellTable(),
        gameDataLoader.getItemTable(),
        nullptr,
        nullptr,
        gameDataLoader.getStandardItemEnchantTable(),
        gameDataLoader.getSpecialItemEnchantTable(),
        &gameDataLoader.getChestTable(),
        selectedMap->outdoorMapData,
        selectedMap->outdoorMapDeltaData,
        selectedMap->outdoorWeatherProfile,
        selectedMap->eventRuntimeState,
        selectedMap->outdoorActorPreviewBillboardSet,
        selectedMap->outdoorLandMask,
        selectedMap->outdoorDecorationCollisionSet,
        selectedMap->outdoorActorCollisionSet,
        selectedMap->outdoorSpriteObjectCollisionSet,
        selectedMap->outdoorSpriteObjectBillboardSet
    );

    Party party = {};
    party.setItemTable(&gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &gameDataLoader.getStandardItemEnchantTable(),
        &gameDataLoader.getSpecialItemEnchantTable());
    party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
    party.reset();

    EventRuntime eventRuntime;
    EventRuntimeState *pEventRuntimeState = outdoorWorldRuntime.eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        std::cerr << "Headless diagnostic failed: event runtime state is not available\n";
        return 1;
    }

    const bool executed = eventRuntime.executeEventById(
        selectedMap->localEventProgram,
        selectedMap->globalEventProgram,
        eventId,
        *pEventRuntimeState,
        &party,
        &outdoorWorldRuntime
    );

    if (!executed)
    {
        std::cerr << "Headless diagnostic failed: event " << eventId << " unresolved\n";
        return 2;
    }

    outdoorWorldRuntime.applyEventRuntimeState();
    party.applyEventRuntimeState(*pEventRuntimeState);

    EventDialogContent dialog = buildHeadlessDialog(
        *pEventRuntimeState,
        0,
        true,
        selectedMap->globalEventProgram,
        gameDataLoader,
        &party,
        outdoorWorldRuntime.currentHour()
    );
    std::cout << "Headless diagnostic: initial dialog after event " << eventId << '\n';
    printDialogSummary(dialog);

    for (size_t sequenceIndex = 0; sequenceIndex < actionIndices.size(); ++sequenceIndex)
    {
        const size_t requestedActionIndex = actionIndices[sequenceIndex];

        if (!dialog.isActive || requestedActionIndex >= dialog.actions.size())
        {
            std::cerr << "Headless diagnostic failed: action index out of range at step " << sequenceIndex << '\n';
            return 3;
        }

        const EventDialogAction &action = dialog.actions[requestedActionIndex];
        const size_t previousMessageCount = pEventRuntimeState->messages.size();

        if (action.kind == EventDialogActionKind::HouseResident)
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = action.id;
            context.hostHouseId = dialog.sourceId;
            pEventRuntimeState->dialogueState.hostHouseId = dialog.sourceId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::HouseService)
        {
            const HouseEntry *pHouseEntry = gameDataLoader.getHouseTable().get(dialog.sourceId);

            if (pHouseEntry == nullptr)
            {
                std::cerr << "Headless diagnostic failed: missing house entry for service action\n";
                return 4;
            }

            const DialogueMenuId menuId = dialogueMenuIdForHouseAction(static_cast<HouseActionId>(action.id));

            if (menuId != DialogueMenuId::None)
            {
                pEventRuntimeState->dialogueState.menuStack.push_back(menuId);
            }
            else
            {
                HouseActionOption option = {};
                option.id = static_cast<HouseActionId>(action.id);
                option.label = action.label;
                option.argument = action.argument;
                const HouseActionResult result = performHouseAction(
                    option,
                    *pHouseEntry,
                    party,
                    &gameDataLoader.getClassSkillTable(),
                    &outdoorWorldRuntime
                );

                for (const std::string &message : result.messages)
                {
                    pEventRuntimeState->messages.push_back(message);
                }
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = dialog.sourceId;
            context.hostHouseId = dialog.sourceId;
            pEventRuntimeState->dialogueState.hostHouseId = dialog.sourceId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::RosterJoinOffer)
        {
            const std::optional<NpcDialogTable::RosterJoinOffer> offer =
                gameDataLoader.getNpcDialogTable().getRosterJoinOfferForTopic(action.id);

            if (!offer)
            {
                std::cerr << "Headless diagnostic failed: missing roster join offer data\n";
                return 4;
            }

            const std::optional<std::string> inviteText = gameDataLoader.getNpcDialogTable().getText(offer->inviteTextId);

            if (inviteText && !inviteText->empty())
            {
                pEventRuntimeState->messages.push_back(*inviteText);
            }

            EventRuntimeState::DialogueOfferState invite = {};
            invite.kind = DialogueOfferKind::RosterJoin;
            invite.npcId = dialog.sourceId;
            invite.topicId = action.id;
            invite.messageTextId = offer->inviteTextId;
            invite.rosterId = offer->rosterId;
            invite.partyFullTextId = offer->partyFullTextId;
            pEventRuntimeState->dialogueState.currentOffer = std::move(invite);

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = dialog.sourceId;
            context.hostHouseId = pEventRuntimeState->dialogueState.hostHouseId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::RosterJoinAccept)
        {
            if (!pEventRuntimeState->dialogueState.currentOffer
                || pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::RosterJoin)
            {
                std::cerr << "Headless diagnostic failed: no pending roster invite\n";
                return 5;
            }

            const EventRuntimeState::DialogueOfferState invite = *pEventRuntimeState->dialogueState.currentOffer;
            pEventRuntimeState->dialogueState.currentOffer.reset();

            if (party.isFull())
            {
                pEventRuntimeState->npcHouseOverrides[invite.npcId] = AdventurersInnHouseId;

                const std::optional<std::string> fullPartyText =
                    gameDataLoader.getNpcDialogTable().getText(invite.partyFullTextId);

                if (fullPartyText && !fullPartyText->empty())
                {
                    pEventRuntimeState->messages.push_back(*fullPartyText);
                }
            }
            else
            {
                const RosterEntry *pRosterEntry = gameDataLoader.getRosterTable().get(invite.rosterId);

                if (pRosterEntry == nullptr || !party.recruitRosterMember(*pRosterEntry))
                {
                    std::cerr << "Headless diagnostic failed: recruitment failed\n";
                    return 6;
                }

                pEventRuntimeState->unavailableNpcIds.insert(invite.npcId);
                pEventRuntimeState->npcHouseOverrides.erase(invite.npcId);
                pEventRuntimeState->messages.push_back(pRosterEntry->name + " joined the party.");
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = invite.npcId;
            context.hostHouseId = pEventRuntimeState->dialogueState.hostHouseId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::RosterJoinDecline)
        {
            const uint32_t npcId =
                (pEventRuntimeState->dialogueState.currentOffer
                 && pEventRuntimeState->dialogueState.currentOffer->kind == DialogueOfferKind::RosterJoin)
                ? pEventRuntimeState->dialogueState.currentOffer->npcId
                : dialog.sourceId;
            pEventRuntimeState->dialogueState.currentOffer.reset();

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = npcId;
            context.hostHouseId = pEventRuntimeState->dialogueState.hostHouseId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::MasteryTeacherOffer)
        {
            EventRuntimeState::DialogueOfferState offer = {};
            offer.kind = DialogueOfferKind::MasteryTeacher;
            offer.npcId = dialog.sourceId;
            offer.topicId = action.id;
            pEventRuntimeState->dialogueState.currentOffer = std::move(offer);

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::NpcTalk;
            context.sourceId = dialog.sourceId;
            context.hostHouseId = pEventRuntimeState->dialogueState.hostHouseId;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
        }
        else if (action.kind == EventDialogActionKind::MasteryTeacherLearn)
        {
            if (!pEventRuntimeState->dialogueState.currentOffer
                || pEventRuntimeState->dialogueState.currentOffer->kind != DialogueOfferKind::MasteryTeacher)
            {
                std::cerr << "Headless diagnostic failed: no pending mastery teacher offer\n";
                return 7;
            }

            std::string message;

            if (applyMasteryTeacherTopic(
                    pEventRuntimeState->dialogueState.currentOffer->topicId,
                    party,
                    gameDataLoader.getClassSkillTable(),
                    gameDataLoader.getNpcDialogTable(),
                    message))
            {
                if (!message.empty())
                {
                    pEventRuntimeState->messages.push_back(message);
                }

                pEventRuntimeState->dialogueState.currentOffer.reset();
            }
        }
        else if (action.kind == EventDialogActionKind::NpcTopic)
        {
            bool topicExecuted = false;

            if (action.textOnly)
            {
                const std::optional<NpcDialogTable::ResolvedTopic> topic =
                    gameDataLoader.getNpcDialogTable().getTopicById(action.secondaryId != 0 ? action.secondaryId : action.id);

                if (topic && !topic->text.empty())
                {
                    pEventRuntimeState->messages.push_back(topic->text);
                    topicExecuted = true;
                }
            }
            else
            {
                topicExecuted = eventRuntime.executeEventById(
                    std::nullopt,
                    selectedMap->globalEventProgram,
                    static_cast<uint16_t>(action.id),
                    *pEventRuntimeState,
                    &party,
                    &outdoorWorldRuntime
                );
            }

            if (!topicExecuted)
            {
                std::cerr << "Headless diagnostic failed: topic event " << action.id << " unresolved\n";
                return 8;
            }

            outdoorWorldRuntime.applyEventRuntimeState();
            party.applyEventRuntimeState(*pEventRuntimeState);

            if (!pEventRuntimeState->pendingDialogueContext)
            {
                EventRuntimeState::PendingDialogueContext context = {};
                context.kind = DialogueContextKind::NpcTalk;
                context.sourceId = dialog.sourceId;
                pEventRuntimeState->pendingDialogueContext = std::move(context);
            }
        }
        else
        {
            std::cerr << "Headless diagnostic failed: unsupported action kind in sequence\n";
            return 9;
        }

        dialog = buildHeadlessDialog(
            *pEventRuntimeState,
            previousMessageCount,
            action.kind != EventDialogActionKind::RosterJoinAccept
                && action.kind != EventDialogActionKind::MasteryTeacherLearn,
            selectedMap->globalEventProgram,
            gameDataLoader,
            &party,
            outdoorWorldRuntime.currentHour()
        );
        std::cout << "Headless diagnostic: dialog after action[" << requestedActionIndex
                  << "] step " << sequenceIndex << '\n';
        printDialogSummary(dialog);
    }

    std::cout << "Headless diagnostic: party members=" << party.members().size() << '\n';
    for (const Character &member : party.members())
    {
        std::cout << "  party \"" << member.name << "\" role=\"" << member.role << "\" level=" << member.level << '\n';
    }

    return 0;
}

int HeadlessGameplayDiagnostics::runRegressionSuite(
    const std::filesystem::path &basePath,
    const std::string &suiteName
) const
{
    if (!isKnownHeadlessRegressionSuite(suiteName))
    {
        std::cerr << "Unknown regression suite: " << suiteName << '\n';
        printHeadlessRegressionSuites();
        return 2;
    }

    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(basePath, m_config.assetRoot, m_config.assetScaleTier))
    {
        std::cerr << "Regression suite failed: could not initialize asset file system\n";
        return 1;
    }

    GameDataLoader gameDataLoader;

    if (!gameDataLoader.loadForHeadlessGameplay(assetFileSystem))
    {
        std::cerr << "Regression suite failed: could not load game data\n";
        return 1;
    }

    const std::string mapFileName = "out01.odm";
    const std::optional<MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();

    if (suiteName != "indoor")
    {
        const std::optional<MapAssetInfo> &initialSelectedMap = gameDataLoader.getSelectedMap();
        const bool alreadyLoadedTargetMap =
            initialSelectedMap
            && toLowerCopy(std::filesystem::path(initialSelectedMap->map.fileName).filename().string()) == mapFileName;

        if (!alreadyLoadedTargetMap
            && !gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
        {
            std::cerr << "Regression suite failed: could not load map \"" << mapFileName << "\"\n";
            return 1;
        }

        if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
        {
            std::cerr << "Regression suite failed: selected map is not an outdoor map\n";
            return 1;
        }
    }

    int passedCount = 0;
    int failedCount = 0;
    const char *pFilter = std::getenv("OPENYAMM_REGRESSION_FILTER");
    const std::string caseFilter = pFilter != nullptr ? pFilter : "";

    auto runCase =
        [&](const std::string &caseName, auto &&fn)
        {
            if (!headlessRegressionCaseMatchesSuite(suiteName, caseName))
            {
                return;
            }

            if (!caseFilter.empty() && caseName.find(caseFilter) == std::string::npos)
            {
                return;
            }

            std::string failure;
            const bool passed = fn(failure);
            std::cout << "["
                      << (passed ? "PASS" : "FAIL")
                      << "] "
                      << caseName;

            if (!passed && !failure.empty())
            {
                std::cout << " - " << failure;
            }

            std::cout << '\n';

            if (passed)
            {
                ++passedCount;
            }
            else
            {
                ++failedCount;
            }
        };

    if (suiteName == "indoor")
    {
        runCase(
            "indoor_scene_runtime_activate_event_uses_scene_context_for_summons",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor authored/runtime state";
                    return false;
                }

                Party party = {};
                party.setItemTable(&gameDataLoader.getItemTable());
                party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
                party.setItemEnchantTables(
                    &gameDataLoader.getStandardItemEnchantTable(),
                    &gameDataLoader.getSpecialItemEnchantTable());
                party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
                party.seed(createRegressionPartySeed());

                GameplayActorService actorService = buildBoundGameplayActorService(gameDataLoader);
                IndoorSceneRuntime runtime(
                    loadedMap->map.fileName,
                    loadedMap->map,
                    *loadedMap->indoorMapData,
                    gameDataLoader.getMonsterTable(),
                    gameDataLoader.getObjectTable(),
                    gameDataLoader.getItemTable(),
                    gameDataLoader.getChestTable(),
                    party,
                    loadedMap->indoorMapDeltaData,
                    loadedMap->eventRuntimeState,
                    loadedMap->localEventProgram,
                    loadedMap->globalEventProgram,
                    &actorService
                );

                const size_t initialActorCount =
                    runtime.mapDeltaData() ? runtime.mapDeltaData()->actors.size() : 0;

                if (!runtime.activateEvent(11, "regression", 0))
                {
                    failure = "event 11 did not execute";
                    return false;
                }

                const std::optional<MapDeltaData> &runtimeMapDelta = runtime.mapDeltaData();

                if (!runtimeMapDelta || runtimeMapDelta->actors.size() != initialActorCount + 1)
                {
                    failure = "event 11 did not summon one indoor actor";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_scene_snapshot_roundtrips_party_and_world_runtime_state",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor authored/runtime state";
                    return false;
                }

                Party party = {};
                party.setItemTable(&gameDataLoader.getItemTable());
                party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
                party.setItemEnchantTables(
                    &gameDataLoader.getStandardItemEnchantTable(),
                    &gameDataLoader.getSpecialItemEnchantTable());
                party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
                party.seed(createRegressionPartySeed());

                GameplayActorService actorService = buildBoundGameplayActorService(gameDataLoader);
                IndoorSceneRuntime runtime(
                    loadedMap->map.fileName,
                    loadedMap->map,
                    *loadedMap->indoorMapData,
                    gameDataLoader.getMonsterTable(),
                    gameDataLoader.getObjectTable(),
                    gameDataLoader.getItemTable(),
                    gameDataLoader.getChestTable(),
                    party,
                    loadedMap->indoorMapDeltaData,
                    loadedMap->eventRuntimeState,
                    loadedMap->localEventProgram,
                    loadedMap->globalEventProgram,
                    &actorService
                );

                runtime.worldRuntime().advanceGameMinutes(137.0f);
                runtime.worldRuntime().setCurrentLocationReputation(-7);
                runtime.partyRuntime().teleportPartyPosition(-661.0f, -1059.0f, -39.0f);

                const IndoorSceneRuntime::Snapshot snapshot = runtime.snapshot();
                const std::filesystem::path savePath = "/tmp/openyamm_indoor_runtime_roundtrip.oysav";
                GameSaveData saveData = {};
                saveData.currentSceneKind = SceneKind::Indoor;
                saveData.mapFileName = loadedMap->map.fileName;
                saveData.party = runtime.party().snapshot();
                saveData.hasIndoorSceneState = true;
                saveData.indoorScene = snapshot;
                saveData.indoorSceneStates[saveData.mapFileName] = snapshot;
                saveData.savedGameMinutes = runtime.worldRuntime().gameMinutes();

                std::string error;

                if (!saveGameDataToPath(savePath, saveData, error))
                {
                    failure = "save failed: " + error;
                    return false;
                }

                const std::optional<GameSaveData> loadedSave = loadGameDataFromPath(savePath, error);
                std::error_code removeError;
                std::filesystem::remove(savePath, removeError);

                if (!loadedSave)
                {
                    failure = "load failed: " + error;
                    return false;
                }

                if (!loadedSave->hasIndoorSceneState)
                {
                    failure = "indoor scene state flag did not roundtrip";
                    return false;
                }

                if (std::abs(loadedSave->indoorScene.worldRuntime.gameMinutes - (9.0f * 60.0f + 137.0f)) > 0.01f)
                {
                    failure = "indoor world time did not roundtrip";
                    return false;
                }

                if (loadedSave->indoorScene.worldRuntime.currentLocationReputation != -7)
                {
                    failure = "indoor location reputation did not roundtrip";
                    return false;
                }

                const IndoorMoveState &savedMoveState = snapshot.partyRuntime.movementState;
                const IndoorMoveState &loadedMoveState = loadedSave->indoorScene.partyRuntime.movementState;

                if (std::abs(loadedMoveState.x - savedMoveState.x) > 0.01f
                    || std::abs(loadedMoveState.y - savedMoveState.y) > 0.01f
                    || std::abs(loadedMoveState.footZ - savedMoveState.footZ) > 0.01f
                    || std::abs(loadedMoveState.eyeHeight - savedMoveState.eyeHeight) > 0.01f
                    || std::abs(loadedMoveState.verticalVelocity - savedMoveState.verticalVelocity) > 0.01f
                    || loadedMoveState.sectorId != savedMoveState.sectorId
                    || loadedMoveState.eyeSectorId != savedMoveState.eyeSectorId
                    || loadedMoveState.supportFaceIndex != savedMoveState.supportFaceIndex
                    || loadedMoveState.grounded != savedMoveState.grounded)
                {
                    failure = "indoor party movement state did not roundtrip";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "party_spell_system_supports_indoor_shared_runtime_for_party_buff_and_beacon",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor authored/runtime state";
                    return false;
                }

                std::optional<MapDeltaData> indoorMapDeltaData = *loadedMap->indoorMapDeltaData;
                std::optional<EventRuntimeState> eventRuntimeState = *loadedMap->eventRuntimeState;
                IndoorPartyRuntime partyRuntime(
                    IndoorMovementController(
                        *loadedMap->indoorMapData,
                        &indoorMapDeltaData,
                        &eventRuntimeState),
                    gameDataLoader.getItemTable());

                Party &party = partyRuntime.party();
                party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
                party.setItemEnchantTables(
                    &gameDataLoader.getStandardItemEnchantTable(),
                    &gameDataLoader.getSpecialItemEnchantTable());
                party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
                party.seed(createRegressionPartySeed());
                partyRuntime.initializePartyPosition(-661.0f, -1059.0f, -39.0f, false);

                GameplayActorService actorService = buildBoundGameplayActorService(gameDataLoader);
                IndoorWorldRuntime worldRuntime = {};
                worldRuntime.initialize(
                    loadedMap->map,
                    gameDataLoader.getMonsterTable(),
                    gameDataLoader.getObjectTable(),
                    gameDataLoader.getItemTable(),
                    gameDataLoader.getChestTable(),
                    &party,
                    &partyRuntime,
                    &indoorMapDeltaData,
                    &eventRuntimeState,
                    &actorService,
                    nullptr,
                    &*loadedMap->indoorMapData);

                PartySpellCastRequest torchLightRequest = {};
                torchLightRequest.casterMemberIndex = 0;
                torchLightRequest.spellId = spellIdValue(SpellId::TorchLight);
                torchLightRequest.skillLevelOverride = 10;
                torchLightRequest.skillMasteryOverride = SkillMastery::Grandmaster;

                const PartySpellCastResult torchLightResult = PartySpellSystem::castSpell(
                    party,
                    worldRuntime,
                    gameDataLoader.getSpellTable(),
                    torchLightRequest);

                if (!torchLightResult.succeeded())
                {
                    failure = "Torch Light failed through indoor shared runtime";
                    return false;
                }

                if (!party.hasPartyBuff(PartyBuffId::TorchLight))
                {
                    failure = "Torch Light did not apply party buff through indoor shared runtime";
                    return false;
                }

                PartySpellCastRequest beaconSetRequest = {};
                beaconSetRequest.casterMemberIndex = 0;
                beaconSetRequest.spellId = spellIdValue(SpellId::LloydsBeacon);
                beaconSetRequest.skillLevelOverride = 10;
                beaconSetRequest.skillMasteryOverride = SkillMastery::Grandmaster;
                beaconSetRequest.spendMana = false;
                beaconSetRequest.utilityAction = PartySpellUtilityActionKind::LloydsBeaconSet;
                beaconSetRequest.utilitySlotIndex = 0;
                beaconSetRequest.hasViewTransform = true;
                beaconSetRequest.viewYawRadians = 0.5f;

                const PartySpellCastResult beaconSetResult = PartySpellSystem::castSpell(
                    party,
                    worldRuntime,
                    gameDataLoader.getSpellTable(),
                    beaconSetRequest);

                if (!beaconSetResult.succeeded())
                {
                    failure = "Lloyd's Beacon set failed through indoor shared runtime";
                    return false;
                }

                const Character *pCaster = party.member(0);

                if (pCaster == nullptr || !pCaster->lloydsBeacons[0].has_value())
                {
                    failure = "Lloyd's Beacon set did not store a beacon";
                    return false;
                }

                PartySpellCastRequest beaconRecallRequest = {};
                beaconRecallRequest.casterMemberIndex = 0;
                beaconRecallRequest.spellId = spellIdValue(SpellId::LloydsBeacon);
                beaconRecallRequest.skillLevelOverride = 10;
                beaconRecallRequest.skillMasteryOverride = SkillMastery::Grandmaster;
                beaconRecallRequest.spendMana = false;
                beaconRecallRequest.utilityAction = PartySpellUtilityActionKind::LloydsBeaconRecall;
                beaconRecallRequest.utilitySlotIndex = 0;

                const PartySpellCastResult beaconRecallResult = PartySpellSystem::castSpell(
                    party,
                    worldRuntime,
                    gameDataLoader.getSpellTable(),
                    beaconRecallRequest);

                if (!beaconRecallResult.succeeded())
                {
                    failure = "Lloyd's Beacon recall failed through indoor shared runtime";
                    return false;
                }

                EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

                if (pEventRuntimeState == nullptr || !pEventRuntimeState->pendingMapMove.has_value())
                {
                    failure = "Lloyd's Beacon recall did not queue a map move";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "house_transport_actions_work_through_indoor_shared_world_runtime_interface",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor authored/runtime state";
                    return false;
                }

                Party party = {};
                party.setItemTable(&gameDataLoader.getItemTable());
                party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
                party.setItemEnchantTables(
                    &gameDataLoader.getStandardItemEnchantTable(),
                    &gameDataLoader.getSpecialItemEnchantTable());
                party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
                party.seed(createRegressionPartySeed());
                party.setQuestBit(42, true);

                std::optional<MapDeltaData> indoorMapDeltaData = *loadedMap->indoorMapDeltaData;
                std::optional<EventRuntimeState> eventRuntimeState = *loadedMap->eventRuntimeState;
                GameplayActorService actorService = buildBoundGameplayActorService(gameDataLoader);
                IndoorWorldRuntime worldRuntime = {};
                worldRuntime.initialize(
                    loadedMap->map,
                    gameDataLoader.getMonsterTable(),
                    gameDataLoader.getObjectTable(),
                    gameDataLoader.getItemTable(),
                    gameDataLoader.getChestTable(),
                    &party,
                    nullptr,
                    &indoorMapDeltaData,
                    &eventRuntimeState,
                    &actorService,
                    nullptr,
                    &*loadedMap->indoorMapData
                );

                HouseEntry houseEntry = {};
                houseEntry.id = 1;
                houseEntry.type = "Boats";
                houseEntry.name = "Regression Docks";
                houseEntry.priceMultiplier = 1.0f;
                HouseEntry::TransportRoute route = {};
                route.routeIndex = 7;
                route.destinationName = "Ravenshore";
                route.mapFileName = "out02.odm";
                route.travelDays = 2;
                route.x = 100;
                route.y = 200;
                route.z = 300;
                route.directionDegrees = 90;
                route.requiredQBit = 42;
                houseEntry.transportRoutes.push_back(route);

                const std::vector<HouseActionOption> actions = buildHouseActionOptions(
                    houseEntry,
                    &party,
                    &gameDataLoader.getClassSkillTable(),
                    &worldRuntime,
                    worldRuntime.gameMinutes(),
                    DialogueMenuId::None
                );

                if (actions.size() != 1 || actions.front().id != HouseActionId::TransportRoute)
                {
                    failure = "transport actions were not built through the shared world interface";
                    return false;
                }

                const float initialMinutes = worldRuntime.gameMinutes();
                const HouseActionResult result = performHouseAction(
                    actions.front(),
                    houseEntry,
                    party,
                    &gameDataLoader.getClassSkillTable(),
                    &worldRuntime
                );

                if (!result.succeeded)
                {
                    failure = "transport action did not succeed through the shared world interface";
                    return false;
                }

                if (std::abs(worldRuntime.gameMinutes() - (initialMinutes + 2.0f * 24.0f * 60.0f)) > 0.01f)
                {
                    failure = "transport action did not advance indoor world time";
                    return false;
                }

                EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

                if (pEventRuntimeState == nullptr || !pEventRuntimeState->pendingMapMove)
                {
                    failure = "transport action did not populate pending map move";
                    return false;
                }

                if (pEventRuntimeState->pendingMapMove->mapName != "out02.odm"
                    || pEventRuntimeState->pendingMapMove->x != 100
                    || pEventRuntimeState->pendingMapMove->y != 200
                    || pEventRuntimeState->pendingMapMove->z != 300)
                {
                    failure = "transport action populated the wrong pending map move";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_movement_controller_snaps_to_floor_and_blocks_walls",
            [&](std::string &failure)
            {
                IndoorMapData indoorMapData = {};
                indoorMapData.vertices = {
                    {0, 0, 0},
                    {1024, 0, 0},
                    {1024, 1024, 0},
                    {0, 1024, 0},
                    {0, 0, 256},
                    {1024, 0, 256},
                    {1024, 1024, 256},
                    {0, 1024, 256},
                };

                IndoorFace floor = {};
                floor.vertexIndices = {0, 1, 2, 3};
                floor.facetType = 3;
                floor.roomNumber = 0;

                IndoorFace ceiling = {};
                ceiling.vertexIndices = {7, 6, 5, 4};
                ceiling.facetType = 5;
                ceiling.roomNumber = 0;

                IndoorFace westWall = {};
                westWall.vertexIndices = {0, 3, 7, 4};
                westWall.facetType = 1;
                westWall.roomNumber = 0;

                IndoorFace eastWall = {};
                eastWall.vertexIndices = {1, 5, 6, 2};
                eastWall.facetType = 1;
                eastWall.roomNumber = 0;

                IndoorFace southWall = {};
                southWall.vertexIndices = {0, 4, 5, 1};
                southWall.facetType = 1;
                southWall.roomNumber = 0;

                IndoorFace northWall = {};
                northWall.vertexIndices = {3, 2, 6, 7};
                northWall.facetType = 1;
                northWall.roomNumber = 0;

                indoorMapData.faces = {
                    floor,
                    ceiling,
                    westWall,
                    eastWall,
                    southWall,
                    northWall,
                };

                IndoorSector sector = {};
                sector.floorCount = 1;
                sector.wallCount = 4;
                sector.ceilingCount = 1;
                sector.faceCount = 6;
                sector.nonBspFaceCount = 6;
                sector.minX = 0;
                sector.maxX = 1024;
                sector.minY = 0;
                sector.maxY = 1024;
                sector.minZ = 0;
                sector.maxZ = 256;
                sector.floorFaceIds = {0};
                sector.wallFaceIds = {2, 3, 4, 5};
                sector.ceilingFaceIds = {1};
                sector.faceIds = {0, 1, 2, 3, 4, 5};
                sector.nonBspFaceIds = sector.faceIds;
                indoorMapData.sectors = {sector};

                std::optional<MapDeltaData> mapDeltaData = MapDeltaData {};
                std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState {};
                IndoorMovementController controller(indoorMapData, &mapDeltaData, &eventRuntimeState);
                const IndoorBodyDimensions body = {};
                const IndoorMoveState initialized =
                    controller.initializeStateFromEyePosition(512.0f, 512.0f, 160.0f, body);

                if (!initialized.grounded || std::fabs(initialized.footZ) > 0.1f)
                {
                    failure = "indoor movement did not snap the eye position to the floor";
                    return false;
                }

                const std::optional<int16_t> sectorId = findIndoorSectorForPoint(
                    indoorMapData,
                    buildIndoorMechanismAdjustedVertices(
                        indoorMapData,
                        mapDeltaData ? &mapDeltaData.value() : nullptr,
                        eventRuntimeState ? &eventRuntimeState.value() : nullptr),
                    {initialized.x, initialized.y, initialized.eyeZ()});

                if (!sectorId || *sectorId != 0)
                {
                    failure = "indoor sector query did not resolve the synthetic room sector";
                    return false;
                }

                const IndoorMoveState moved = controller.resolveMove(initialized, body, 1200.0f, 0.0f, false, 1.0f);

                if (moved.x > 1024.0f - body.radius)
                {
                    failure = "indoor wall collision allowed the body through the room wall";
                    return false;
                }

                IndoorMoveState nearEastWall = initialized;
                nearEastWall.x = 1024.0f - body.radius - 1.0f;
                nearEastWall.y = 512.0f;
                const IndoorMoveState slid =
                    controller.resolveMove(nearEastWall, body, 1200.0f, 300.0f, false, 0.1f);

                if (slid.x > 1024.0f - body.radius)
                {
                    failure = "indoor wall slide allowed the body through the room wall";
                    return false;
                }

                if (slid.y <= nearEastWall.y + 4.0f)
                {
                    failure = "indoor movement did not slide tangentially while pressed into a wall";
                    return false;
                }

                IndoorMoveState pressedIntoEastWall = initialized;
                pressedIntoEastWall.x = 1024.0f - body.radius + 1.0f;
                pressedIntoEastWall.y = 512.0f;
                const IndoorMoveState tangentialSlide =
                    controller.resolveMove(pressedIntoEastWall, body, 0.0f, 300.0f, false, 0.1f);

                if (tangentialSlide.y <= pressedIntoEastWall.y + 4.0f)
                {
                    failure = "indoor movement stuck while already pressed into a wall";
                    return false;
                }

                IndoorMoveState pressedIntoNorthEastCorner = initialized;
                pressedIntoNorthEastCorner.x = 1024.0f - body.radius + 1.0f;
                pressedIntoNorthEastCorner.y = 1024.0f - body.radius + 1.0f;
                IndoorMoveDebugInfo cornerDebug = {};
                const IndoorMoveState cornerSlide =
                    controller.resolveMove(
                        pressedIntoNorthEastCorner,
                        body,
                        -250.0f,
                        -250.0f,
                        false,
                        0.1f,
                        nullptr,
                        std::nullopt,
                        false,
                        &cornerDebug);

                if (cornerSlide.x >= pressedIntoNorthEastCorner.x - 4.0f
                    || cornerSlide.y >= pressedIntoNorthEastCorner.y - 4.0f)
                {
                    failure =
                        "indoor movement stuck while already pressed into a corner start=("
                        + std::to_string(pressedIntoNorthEastCorner.x) + ","
                        + std::to_string(pressedIntoNorthEastCorner.y) + ") moved=("
                        + std::to_string(cornerSlide.x) + "," + std::to_string(cornerSlide.y) + ") block="
                        + std::to_string(static_cast<int>(cornerDebug.primaryBlockKind)) + " hitFace="
                        + std::to_string(cornerDebug.hitFaceIndex) + " hitDist="
                        + std::to_string(cornerDebug.hitMoveDistance) + " adjusted="
                        + std::to_string(cornerDebug.hitAdjustedMoveDistance) + " response=("
                        + std::to_string(cornerDebug.responseStep.x) + ","
                        + std::to_string(cornerDebug.responseStep.y) + ","
                        + std::to_string(cornerDebug.responseStep.z) + ") tried="
                        + std::to_string(cornerDebug.collisionResponseTried ? 1 : 0) + " ok="
                        + std::to_string(cornerDebug.collisionResponseSucceeded ? 1 : 0) + " full="
                        + std::to_string(cornerDebug.fullMoveSucceeded ? 1 : 0);
                    return false;
                }

                IndoorBodyDimensions largeActorBody = {};
                largeActorBody.radius = 100.0f;
                largeActorBody.height = 220.0f;
                IndoorMoveState largeActorStart =
                    controller.initializeStateFromEyePosition(128.0f, 512.0f, largeActorBody.height, largeActorBody);
                controller.setActorColliders({IndoorActorCollision{
                    0,
                    360.0f,
                    512.0f,
                    0.0f,
                    40.0f,
                    220.0f}});
                const IndoorMoveState largeActorBlocked =
                    controller.resolveMove(
                        largeActorStart,
                        largeActorBody,
                        500.0f,
                        0.0f,
                        false,
                        1.0f,
                        nullptr,
                        std::nullopt,
                        true);

                if (largeActorBlocked.x > 240.0f)
                {
                    failure = "indoor actor-vs-actor collision did not preserve the moving actor authored radius";
                    return false;
                }

                controller.setActorColliders({
                    IndoorActorCollision{
                        11,
                        360.0f,
                        512.0f,
                        0.0f,
                        40.0f,
                        220.0f},
                    IndoorActorCollision{
                        22,
                        360.0f,
                        560.0f,
                        0.0f,
                        40.0f,
                        220.0f},
                });
                std::vector<size_t> contactedActorIndices;
                controller.resolveMove(
                    largeActorStart,
                    largeActorBody,
                    500.0f,
                    0.0f,
                    false,
                    1.0f,
                    &contactedActorIndices,
                    std::nullopt,
                    true);

                std::sort(contactedActorIndices.begin(), contactedActorIndices.end());
                contactedActorIndices.erase(
                    std::unique(contactedActorIndices.begin(), contactedActorIndices.end()),
                    contactedActorIndices.end());

                if (contactedActorIndices.size() != 2
                    || contactedActorIndices[0] != 11
                    || contactedActorIndices[1] != 22)
                {
                    failure = "indoor actor movement did not report every actor contact for crowd detection";
                    return false;
                }

                IndoorMoveState partyStart =
                    controller.initializeStateFromEyePosition(128.0f, 512.0f, body.height, body);
                controller.setActorColliders({IndoorActorCollision{
                    0,
                    360.0f,
                    512.0f,
                    0.0f,
                    100.0f,
                    220.0f}});
                const IndoorMoveState partyBlocked =
                    controller.resolveMove(
                        partyStart,
                        body,
                        500.0f,
                        0.0f,
                        false,
                        1.0f,
                        nullptr,
                        std::nullopt,
                        true);

                if (partyBlocked.x > 245.0f)
                {
                    failure = "indoor party-vs-actor collision did not use the actor authored radius";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_movement_controller_steps_over_low_wall_segments",
            [&](std::string &failure)
            {
                IndoorMapData indoorMapData = {};
                indoorMapData.vertices = {
                    {0, 0, 0},
                    {1024, 0, 0},
                    {1024, 1024, 0},
                    {0, 1024, 0},
                    {0, 0, 256},
                    {1024, 0, 256},
                    {1024, 1024, 256},
                    {0, 1024, 256},
                    {640, 256, 0},
                    {640, 768, 0},
                    {640, 768, 24},
                    {640, 256, 24},
                };

                IndoorFace floor = {};
                floor.vertexIndices = {0, 1, 2, 3};
                floor.facetType = 3;

                IndoorFace ceiling = {};
                ceiling.vertexIndices = {4, 7, 6, 5};
                ceiling.facetType = 4;

                IndoorFace wallNorth = {};
                wallNorth.vertexIndices = {0, 4, 5, 1};
                wallNorth.facetType = 1;

                IndoorFace wallEast = {};
                wallEast.vertexIndices = {1, 5, 6, 2};
                wallEast.facetType = 1;

                IndoorFace wallSouth = {};
                wallSouth.vertexIndices = {2, 6, 7, 3};
                wallSouth.facetType = 1;

                IndoorFace wallWest = {};
                wallWest.vertexIndices = {3, 7, 4, 0};
                wallWest.facetType = 1;

                IndoorFace lowWall = {};
                lowWall.vertexIndices = {8, 11, 10, 9};
                lowWall.facetType = 1;

                indoorMapData.faces = {
                    floor,
                    ceiling,
                    wallNorth,
                    wallEast,
                    wallSouth,
                    wallWest,
                    lowWall,
                };

                IndoorSector sector = {};
                sector.floorCount = 1;
                sector.wallCount = 5;
                sector.ceilingCount = 1;
                sector.faceCount = 7;
                sector.nonBspFaceCount = 7;
                sector.minX = 0;
                sector.maxX = 1024;
                sector.minY = 0;
                sector.maxY = 1024;
                sector.minZ = 0;
                sector.maxZ = 256;
                sector.floorFaceIds = {0};
                sector.wallFaceIds = {2, 3, 4, 5, 6};
                sector.ceilingFaceIds = {1};
                sector.faceIds = {0, 1, 2, 3, 4, 5, 6};
                sector.nonBspFaceIds = sector.faceIds;
                indoorMapData.sectors = {sector};

                std::optional<MapDeltaData> mapDeltaData = MapDeltaData {};
                std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState {};
                IndoorMovementController controller(indoorMapData, &mapDeltaData, &eventRuntimeState);
                const IndoorBodyDimensions body = {};
                const IndoorMoveState initialized =
                    controller.initializeStateFromEyePosition(512.0f, 512.0f, 160.0f, body);
                const IndoorMoveState moved = controller.resolveMove(initialized, body, 180.0f, 0.0f, false, 1.0f);

                if (moved.x <= 640.0f)
                {
                    failure = "indoor movement remained blocked by a low wall segment";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_movement_controller_crosses_portals_and_respects_mechanism_blocking",
            [&](std::string &failure)
            {
                IndoorMapData indoorMapData = {};
                indoorMapData.vertices = {
                    {0, 0, 0},
                    {1024, 0, 0},
                    {1024, 1024, 0},
                    {0, 1024, 0},
                    {0, 0, 256},
                    {1024, 0, 256},
                    {1024, 1024, 256},
                    {0, 1024, 256},
                    {2048, 0, 0},
                    {2048, 1024, 0},
                    {2048, 0, 256},
                    {2048, 1024, 256},
                    {1536, 256, 0},
                    {1536, 768, 0},
                    {1536, 768, 256},
                    {1536, 256, 256},
                };

                IndoorFace westFloor = {};
                westFloor.vertexIndices = {0, 1, 2, 3};
                westFloor.facetType = 3;
                westFloor.roomNumber = 1;

                IndoorFace westCeiling = {};
                westCeiling.vertexIndices = {7, 6, 5, 4};
                westCeiling.facetType = 5;
                westCeiling.roomNumber = 1;

                IndoorFace westOuterWall = {};
                westOuterWall.vertexIndices = {0, 3, 7, 4};
                westOuterWall.facetType = 1;
                westOuterWall.roomNumber = 1;

                IndoorFace westSouthWall = {};
                westSouthWall.vertexIndices = {0, 4, 5, 1};
                westSouthWall.facetType = 1;
                westSouthWall.roomNumber = 1;

                IndoorFace westNorthWall = {};
                westNorthWall.vertexIndices = {3, 2, 6, 7};
                westNorthWall.facetType = 1;
                westNorthWall.roomNumber = 1;

                IndoorFace portal = {};
                portal.vertexIndices = {1, 5, 6, 2};
                portal.facetType = 1;
                portal.roomNumber = 1;
                portal.roomBehindNumber = 2;
                portal.isPortal = true;

                IndoorFace eastFloor = {};
                eastFloor.vertexIndices = {1, 8, 9, 2};
                eastFloor.facetType = 3;
                eastFloor.roomNumber = 2;

                IndoorFace eastCeiling = {};
                eastCeiling.vertexIndices = {6, 11, 10, 5};
                eastCeiling.facetType = 5;
                eastCeiling.roomNumber = 2;

                IndoorFace eastOuterWall = {};
                eastOuterWall.vertexIndices = {8, 10, 11, 9};
                eastOuterWall.facetType = 1;
                eastOuterWall.roomNumber = 2;

                IndoorFace eastSouthWall = {};
                eastSouthWall.vertexIndices = {1, 5, 10, 8};
                eastSouthWall.facetType = 1;
                eastSouthWall.roomNumber = 2;

                IndoorFace eastNorthWall = {};
                eastNorthWall.vertexIndices = {2, 9, 11, 6};
                eastNorthWall.facetType = 1;
                eastNorthWall.roomNumber = 2;

                IndoorFace doorFace = {};
                doorFace.vertexIndices = {12, 15, 14, 13};
                doorFace.facetType = 1;
                doorFace.roomNumber = 2;

                indoorMapData.faces = {
                    westFloor,
                    westCeiling,
                    westOuterWall,
                    westSouthWall,
                    westNorthWall,
                    portal,
                    eastFloor,
                    eastCeiling,
                    eastOuterWall,
                    eastSouthWall,
                    eastNorthWall,
                    doorFace,
                };

                IndoorSector dummySector = {};

                IndoorSector westSector = {};
                westSector.floorCount = 1;
                westSector.wallCount = 3;
                westSector.ceilingCount = 1;
                westSector.portalCount = 1;
                westSector.faceCount = 6;
                westSector.nonBspFaceCount = 6;
                westSector.minX = 0;
                westSector.maxX = 1024;
                westSector.minY = 0;
                westSector.maxY = 1024;
                westSector.minZ = 0;
                westSector.maxZ = 256;
                westSector.floorFaceIds = {0};
                westSector.wallFaceIds = {2, 3, 4};
                westSector.ceilingFaceIds = {1};
                westSector.portalFaceIds = {5};
                westSector.faceIds = {0, 1, 2, 3, 4, 5};
                westSector.nonBspFaceIds = westSector.faceIds;

                IndoorSector eastSector = {};
                eastSector.floorCount = 1;
                eastSector.wallCount = 4;
                eastSector.ceilingCount = 1;
                eastSector.portalCount = 1;
                eastSector.faceCount = 7;
                eastSector.nonBspFaceCount = 7;
                eastSector.minX = 1024;
                eastSector.maxX = 2048;
                eastSector.minY = 0;
                eastSector.maxY = 1024;
                eastSector.minZ = 0;
                eastSector.maxZ = 256;
                eastSector.floorFaceIds = {6};
                eastSector.wallFaceIds = {8, 9, 10, 11};
                eastSector.ceilingFaceIds = {7};
                eastSector.portalFaceIds = {5};
                eastSector.faceIds = {5, 6, 7, 8, 9, 10, 11};
                eastSector.nonBspFaceIds = eastSector.faceIds;

                indoorMapData.sectors = {dummySector, westSector, eastSector};

                MapDeltaDoor door = {};
                door.doorId = 77;
                door.directionX = 65536;
                door.moveLength = 128;
                door.openSpeed = 128;
                door.closeSpeed = 128;
                door.state = static_cast<uint16_t>(EvtMechanismState::Closed);
                door.vertexIds = {12, 13, 14, 15};
                door.faceIds = {11};
                door.sectorIds = {2};
                door.xOffsets = {1408, 1408, 1408, 1408};
                door.yOffsets = {256, 768, 768, 256};
                door.zOffsets = {0, 0, 256, 256};

                std::optional<MapDeltaData> mapDeltaData = MapDeltaData {};
                mapDeltaData->doors.push_back(door);
                std::optional<EventRuntimeState> eventRuntimeState = EventRuntimeState {};
                RuntimeMechanismState closedMechanism = {};
                closedMechanism.state = static_cast<uint16_t>(EvtMechanismState::Closed);
                closedMechanism.currentDistance = 128.0f;
                closedMechanism.isMoving = false;
                eventRuntimeState->mechanisms[77] = closedMechanism;

                IndoorMovementController controller(indoorMapData, &mapDeltaData, &eventRuntimeState);
                const IndoorBodyDimensions body = {};
                const IndoorMoveState portalStart =
                    controller.initializeStateFromEyePosition(900.0f, 512.0f, 160.0f, body);
                const IndoorMoveState portalMoved =
                    controller.resolveMove(
                        portalStart,
                        body,
                        400.0f,
                        0.0f,
                        false,
                        1.0f,
                        nullptr,
                        std::nullopt,
                        false,
                        nullptr);

                if (portalStart.sectorId != 1 || portalMoved.sectorId != 2 || portalMoved.x <= 1024.0f + body.radius)
                {
                    failure = "portal movement did not cross into the adjacent sector";
                    return false;
                }

                const IndoorMoveState closedDoorStart =
                    controller.initializeStateFromEyePosition(1300.0f, 512.0f, 160.0f, body);
                const IndoorMoveState closedDoorMoved =
                    controller.resolveMove(
                        closedDoorStart,
                        body,
                        600.0f,
                        0.0f,
                        false,
                        1.0f,
                        nullptr,
                        std::nullopt,
                        false,
                        nullptr);

                if (closedDoorMoved.x > 1536.0f - body.radius + 1.0f)
                {
                    failure = "closed mechanism face did not block swept indoor movement";
                    return false;
                }

                RuntimeMechanismState openMechanism = {};
                openMechanism.state = static_cast<uint16_t>(EvtMechanismState::Open);
                openMechanism.currentDistance = 0.0f;
                openMechanism.isMoving = false;
                eventRuntimeState->mechanisms[77] = openMechanism;

                IndoorMovementController openController(indoorMapData, &mapDeltaData, &eventRuntimeState);
                const IndoorMoveState openDoorStart =
                    openController.initializeStateFromEyePosition(1300.0f, 512.0f, 160.0f, body);
                const IndoorMoveState openDoorMoved =
                    openController.resolveMove(
                        openDoorStart,
                        body,
                        600.0f,
                        0.0f,
                        false,
                        1.0f,
                        nullptr,
                        std::nullopt,
                        false,
                        nullptr);

                if (openDoorMoved.x < 1800.0f)
                {
                    failure = "open mechanism face still blocked swept indoor movement";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_d18_large_actor_crosses_portal_off_center",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData
                    || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor authored/runtime state";
                    return false;
                }

                IndoorBodyDimensions body = {};

                for (const MapDeltaActor &actor : loadedMap->indoorMapDeltaData->actors)
                {
                    if (actor.radius <= body.radius)
                    {
                        continue;
                    }

                    body.radius = actor.radius;
                    const float actorHeight = actor.height;
                    body.height =
                        actor.height > 0
                            ? std::max(actorHeight, body.radius * 2.0f + 2.0f)
                            : body.radius * 2.0f + 2.0f;
                }

                if (body.radius <= 40.0f)
                {
                    failure = "d18.blv did not expose a large authored indoor actor radius";
                    return false;
                }

                IndoorMovementController controller(
                    *loadedMap->indoorMapData,
                    &loadedMap->indoorMapDeltaData,
                    &loadedMap->eventRuntimeState);
                const std::vector<IndoorVertex> vertices = buildIndoorMechanismAdjustedVertices(
                    *loadedMap->indoorMapData,
                    &*loadedMap->indoorMapDeltaData,
                    &*loadedMap->eventRuntimeState);
                IndoorFaceGeometryCache geometryCache(loadedMap->indoorMapData->faces.size());
                size_t attemptedPortalCount = 0;

                for (size_t sectorIndex = 0; sectorIndex < loadedMap->indoorMapData->sectors.size(); ++sectorIndex)
                {
                    const IndoorSector &sector = loadedMap->indoorMapData->sectors[sectorIndex];

                    for (uint16_t faceId : sector.portalFaceIds)
                    {
                        const IndoorFaceGeometryData *pGeometry =
                            geometryCache.geometryForFace(*loadedMap->indoorMapData, vertices, faceId);

                        if (pGeometry == nullptr || !pGeometry->isPortal || pGeometry->kind != IndoorFaceKind::Wall)
                        {
                            continue;
                        }

                        bx::Vec3 horizontalNormal = {pGeometry->normal.x, pGeometry->normal.y, 0.0f};
                        const float normalLength = std::sqrt(
                            horizontalNormal.x * horizontalNormal.x + horizontalNormal.y * horizontalNormal.y);

                        if (normalLength <= 0.0001f || pGeometry->vertices.empty())
                        {
                            continue;
                        }

                        horizontalNormal.x /= normalLength;
                        horizontalNormal.y /= normalLength;
                        const bx::Vec3 tangent = {-horizontalNormal.y, horizontalNormal.x, 0.0f};
                        bx::Vec3 center = {0.0f, 0.0f, 0.0f};

                        for (const bx::Vec3 &vertex : pGeometry->vertices)
                        {
                            center.x += vertex.x;
                            center.y += vertex.y;
                            center.z += vertex.z;
                        }

                        const float inverseVertexCount = 1.0f / pGeometry->vertices.size();
                        center.x *= inverseVertexCount;
                        center.y *= inverseVertexCount;
                        center.z *= inverseVertexCount;
                        const std::array<float, 4> tangentOffsets = {{
                            body.radius * 0.25f,
                            -body.radius * 0.25f,
                            body.radius * 0.5f,
                            -body.radius * 0.5f
                        }};
                        const std::array<float, 2> sideSigns = {{-1.0f, 1.0f}};

                        for (float sideSign : sideSigns)
                        {
                            for (float tangentOffset : tangentOffsets)
                            {
                                ++attemptedPortalCount;
                                const float startDistance = body.radius + 24.0f;
                                const float moveDistance = body.radius * 2.0f + 192.0f;
                                const float startX =
                                    center.x - horizontalNormal.x * startDistance * sideSign
                                    + tangent.x * tangentOffset;
                                const float startY =
                                    center.y - horizontalNormal.y * startDistance * sideSign
                                    + tangent.y * tangentOffset;
                                const float eyeZ = pGeometry->minZ + body.height;
                                const IndoorMoveState start =
                                    controller.initializeStateFromEyePosition(startX, startY, eyeZ, body);

                                if (start.sectorId < 0)
                                {
                                    continue;
                                }

                                const IndoorMoveState moved =
                                    controller.resolveMove(
                                        start,
                                        body,
                                        horizontalNormal.x * moveDistance * sideSign,
                                        horizontalNormal.y * moveDistance * sideSign,
                                        false,
                                        1.0f);

                                if (moved.sectorId >= 0 && moved.sectorId != start.sectorId)
                                {
                                    return true;
                                }
                            }
                        }
                    }
                }

                failure =
                    "no off-center d18 portal crossing succeeded for large actor radius="
                    + std::to_string(body.radius)
                    + " height=" + std::to_string(body.height)
                    + " attempts=" + std::to_string(attemptedPortalCount);
                return false;
            }
        );

        runCase(
            "indoor_d18_large_actor_crosses_face_1366",
            [&](std::string &failure)
            {
                constexpr size_t PortalFaceIndex = 1366;

                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData
                    || !loadedMap->eventRuntimeState || PortalFaceIndex >= loadedMap->indoorMapData->faces.size())
                {
                    failure = "d18.blv missing indoor authored/runtime state or portal face";
                    return false;
                }

                IndoorBodyDimensions body = {};
                body.radius = 100.0f;
                body.height = 202.0f;
                IndoorMovementController controller(
                    *loadedMap->indoorMapData,
                    &loadedMap->indoorMapDeltaData,
                    &loadedMap->eventRuntimeState);
                const std::vector<IndoorVertex> vertices = buildIndoorMechanismAdjustedVertices(
                    *loadedMap->indoorMapData,
                    &*loadedMap->indoorMapDeltaData,
                    &*loadedMap->eventRuntimeState);
                IndoorFaceGeometryCache geometryCache(loadedMap->indoorMapData->faces.size());
                const IndoorFaceGeometryData *pGeometry =
                    geometryCache.geometryForFace(*loadedMap->indoorMapData, vertices, PortalFaceIndex);

                if (pGeometry == nullptr || !pGeometry->isPortal || pGeometry->vertices.empty())
                {
                    failure = "d18 face 1366 is not a usable portal";
                    return false;
                }

                bx::Vec3 horizontalNormal = {pGeometry->normal.x, pGeometry->normal.y, 0.0f};
                const float normalLength =
                    std::sqrt(horizontalNormal.x * horizontalNormal.x + horizontalNormal.y * horizontalNormal.y);

                if (normalLength <= 0.0001f)
                {
                    failure = "d18 face 1366 has no horizontal normal";
                    return false;
                }

                horizontalNormal.x /= normalLength;
                horizontalNormal.y /= normalLength;

                bx::Vec3 center = {0.0f, 0.0f, 0.0f};

                for (const bx::Vec3 &vertex : pGeometry->vertices)
                {
                    center.x += vertex.x;
                    center.y += vertex.y;
                    center.z += vertex.z;
                }

                const float inverseVertexCount = 1.0f / pGeometry->vertices.size();
                center.x *= inverseVertexCount;
                center.y *= inverseVertexCount;
                center.z *= inverseVertexCount;

                const float startDistance = body.radius + 24.0f;
                const float moveDistance = body.radius * 2.0f + 192.0f;
                const float startX = center.x + horizontalNormal.x * startDistance;
                const float startY = center.y + horizontalNormal.y * startDistance;
                const IndoorMoveState start =
                    controller.initializeStateFromEyePosition(startX, startY, pGeometry->minZ + body.height, body);

                if (start.sectorId < 0)
                {
                    failure = "d18 face 1366 large actor start did not resolve to an indoor sector";
                    return false;
                }

                const IndoorMoveState moved =
                    controller.resolveMove(
                        start,
                        body,
                        -horizontalNormal.x * moveDistance,
                        -horizontalNormal.y * moveDistance,
                        false,
                        1.0f);

                if (moved.sectorId >= 0 && moved.sectorId != start.sectorId)
                {
                    return true;
                }

                failure =
                    describeIndoorFaceMembership(*loadedMap->indoorMapData, PortalFaceIndex)
                    + " startSector=" + std::to_string(start.sectorId)
                    + " movedSector=" + std::to_string(moved.sectorId)
                    + " start=(" + std::to_string(start.x) + "," + std::to_string(start.y) + ","
                    + std::to_string(start.footZ) + ") moved=(" + std::to_string(moved.x) + ","
                    + std::to_string(moved.y) + "," + std::to_string(moved.footZ) + ")";
                return false;
            }
        );

        runCase(
            "indoor_d18_naga_lintel_slide_preserves_tangential_progress",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData
                    || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor authored/runtime state";
                    return false;
                }

                IndoorBodyDimensions body = {};
                body.radius = 135.0f;
                body.height = 272.0f;
                IndoorMovementController controller(
                    *loadedMap->indoorMapData,
                    &loadedMap->indoorMapDeltaData,
                    &loadedMap->eventRuntimeState);
                const IndoorMoveState start =
                    controller.initializeStateFromEyePosition(-503.041f, -511.796f, 144.0f, body);

                if (start.sectorId != 1 || start.supportFaceIndex != 1364)
                {
                    failure =
                        "d18 Naga lintel start did not resolve as expected sector="
                        + std::to_string(start.sectorId)
                        + " supportFace=" + std::to_string(start.supportFaceIndex);
                    return false;
                }

                IndoorMoveDebugInfo debugInfo = {};
                IndoorMoveState moved = start;

                for (int step = 0; step < 128; ++step)
                {
                    moved =
                        controller.resolveMove(
                            moved,
                            body,
                            150.608f,
                            131.595f,
                            false,
                            1.0f / 128.0f,
                            nullptr,
                            std::nullopt,
                            false,
                            &debugInfo);
                }

                if (moved.x <= start.x + 10.0f)
                {
                    failure =
                        "d18 Naga lintel slide did not preserve tangential progress start=("
                        + std::to_string(start.x) + "," + std::to_string(start.y) + ","
                        + std::to_string(start.footZ) + ") moved=(" + std::to_string(moved.x) + ","
                        + std::to_string(moved.y) + "," + std::to_string(moved.footZ)
                        + ") block=" + std::to_string(static_cast<int>(debugInfo.primaryBlockKind))
                        + " hitFace=" + std::to_string(debugInfo.hitFaceIndex)
                        + " responseTried=" + std::to_string(debugInfo.collisionResponseTried)
                        + " responseSucceeded=" + std::to_string(debugInfo.collisionResponseSucceeded)
                        + " fullMoveSucceeded=" + std::to_string(debugInfo.fullMoveSucceeded)
                        + " hitMove=" + std::to_string(debugInfo.hitMoveDistance)
                        + " hitAdjusted=" + std::to_string(debugInfo.hitAdjustedMoveDistance)
                        + " hitOffset=" + std::to_string(debugInfo.hitHeightOffset)
                        + " hitPoint=(" + std::to_string(debugInfo.hitPoint.x) + ","
                        + std::to_string(debugInfo.hitPoint.y) + "," + std::to_string(debugInfo.hitPoint.z) + ")"
                        + " hitNormal=(" + std::to_string(debugInfo.hitNormal.x) + ","
                        + std::to_string(debugInfo.hitNormal.y) + "," + std::to_string(debugInfo.hitNormal.z) + ")"
                        + " responseStep=(" + std::to_string(debugInfo.responseStep.x) + ","
                        + std::to_string(debugInfo.responseStep.y) + ","
                        + std::to_string(debugInfo.responseStep.z) + ")";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_event_runtime_trigger_mechanism_uses_authored_state_semantics",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor authored/runtime state";
                    return false;
                }

                const MapDeltaDoor *pDoor72 = nullptr;

                for (const MapDeltaDoor &door : loadedMap->indoorMapDeltaData->doors)
                {
                    if (door.doorId == 72)
                    {
                        pDoor72 = &door;
                        break;
                    }
                }

                if (pDoor72 == nullptr)
                {
                    failure = "mechanism 72 missing from d18.blv";
                    return false;
                }

                Party party = {};
                party.setItemTable(&gameDataLoader.getItemTable());
                party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
                party.setItemEnchantTables(
                    &gameDataLoader.getStandardItemEnchantTable(),
                    &gameDataLoader.getSpecialItemEnchantTable());
                party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
                party.seed(createRegressionPartySeed());

                GameplayActorService actorService = buildBoundGameplayActorService(gameDataLoader);
                IndoorSceneRuntime runtime(
                    loadedMap->map.fileName,
                    loadedMap->map,
                    *loadedMap->indoorMapData,
                    gameDataLoader.getMonsterTable(),
                    gameDataLoader.getObjectTable(),
                    gameDataLoader.getItemTable(),
                    gameDataLoader.getChestTable(),
                    party,
                    loadedMap->indoorMapDeltaData,
                    loadedMap->eventRuntimeState,
                    loadedMap->localEventProgram,
                    loadedMap->globalEventProgram,
                    &actorService
                );

                if (!runtime.activateEvent(12, "regression", 0))
                {
                    failure = "event 12 did not execute";
                    return false;
                }

                EventRuntimeState *pEventRuntimeState = runtime.eventRuntimeState();

                if (pEventRuntimeState == nullptr)
                {
                    failure = "event runtime state missing";
                    return false;
                }

                const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator iterator =
                    pEventRuntimeState->mechanisms.find(72);

                if (iterator == pEventRuntimeState->mechanisms.end())
                {
                    failure = "event 12 did not create mechanism state for 72";
                    return false;
                }

                const uint16_t expectedState = pDoor72->state == static_cast<uint16_t>(EvtMechanismState::Closed)
                    ? static_cast<uint16_t>(EvtMechanismState::Opening)
                    : static_cast<uint16_t>(EvtMechanismState::Closing);

                if (iterator->second.state != expectedState || !iterator->second.isMoving)
                {
                    failure = "event 12 trigger semantics do not match authored mechanism state";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_scene_party_buff_updates_shared_scene_party_state",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor state";
                    return false;
                }

                Party party = {};
                party.setItemTable(&gameDataLoader.getItemTable());
                party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
                party.setItemEnchantTables(
                    &gameDataLoader.getStandardItemEnchantTable(),
                    &gameDataLoader.getSpecialItemEnchantTable());
                party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
                party.seed(createRegressionPartySeed());

                GameplayActorService actorService = buildBoundGameplayActorService(gameDataLoader);
                IndoorSceneRuntime runtime(
                    loadedMap->map.fileName,
                    loadedMap->map,
                    *loadedMap->indoorMapData,
                    gameDataLoader.getMonsterTable(),
                    gameDataLoader.getObjectTable(),
                    gameDataLoader.getItemTable(),
                    gameDataLoader.getChestTable(),
                    party,
                    loadedMap->indoorMapDeltaData,
                    loadedMap->eventRuntimeState,
                    loadedMap->localEventProgram,
                    loadedMap->globalEventProgram,
                    &actorService
                );

                Character *pCaster = runtime.partyRuntime().party().member(0);

                if (pCaster == nullptr)
                {
                    failure = "caster missing";
                    return false;
                }

                pCaster->skills["SpiritMagic"] = {"SpiritMagic", 8, SkillMastery::Expert};

                PartySpellCastRequest request = {};
                request.casterMemberIndex = 0;
                request.spellId = spellIdValue(SpellId::Heroism);
                const PartySpellCastResult result = PartySpellSystem::castSpell(
                    runtime.partyRuntime().party(),
                    runtime.worldRuntime(),
                    gameDataLoader.getSpellTable(),
                    request);

                if (!result.succeeded())
                {
                    failure = "heroism cast did not succeed";
                    return false;
                }

                if (!runtime.partyRuntime().party().hasPartyBuff(PartyBuffId::Heroism))
                {
                    failure = "heroism not applied to indoor runtime party";
                    return false;
                }

                if (!runtime.party().hasPartyBuff(PartyBuffId::Heroism))
                {
                    failure = "indoor scene party did not reflect runtime-applied heroism";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_support_sampling_prefers_highest_floor_under_body_footprint",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor state";
                    return false;
                }

                std::optional<EventRuntimeState> runtimeState = *loadedMap->eventRuntimeState;
                RuntimeMechanismState mechanism = {};
                mechanism.state = static_cast<uint16_t>(EvtMechanismState::Open);
                mechanism.currentDistance = 0.0f;
                mechanism.isMoving = false;
                runtimeState->mechanisms[1] = mechanism;

                IndoorMovementController controller(
                    *loadedMap->indoorMapData,
                    &loadedMap->indoorMapDeltaData,
                    &runtimeState);

                for (size_t sectorIndex : {size_t(1), size_t(3), size_t(8)})
                {
                    if (sectorIndex >= loadedMap->indoorMapData->sectors.size())
                    {
                        failure = "expected d18 sector is missing from parsed indoor data";
                        return false;
                    }

                    const IndoorSector &sector = loadedMap->indoorMapData->sectors[sectorIndex];

                    if (sector.floorFaceIds.empty() || sector.faceIds.empty())
                    {
                        failure = "parsed d18 sector lists are incomplete for sector " + std::to_string(sectorIndex);
                        return false;
                    }
                }

                const IndoorBodyDimensions body = {};
                IndoorMoveState current =
                    controller.initializeStateFromEyePosition(480.0f, 930.0f, 16.0f, body);
                float minimumFootZ = current.footZ;
                float maximumFootZ = current.footZ;

                for (int step = 0; step < 24; ++step)
                {
                    current = controller.resolveMove(current, body, 0.0f, 40.0f, false, 0.1f);
                    minimumFootZ = std::min(minimumFootZ, current.footZ);
                    maximumFootZ = std::max(maximumFootZ, current.footZ);

                    if (current.footZ < -200.0f)
                    {
                        failure = "movement snapped into the retracted door pocket while approaching the doorway";
                        return false;
                    }
                }

                if (current.y < 980.0f)
                {
                    failure = "movement failed to continue through the open doorway "
                        + describeIndoorFaceMembership(*loadedMap->indoorMapData, 383);
                    return false;
                }

                if (maximumFootZ - minimumFootZ > 24.0f)
                {
                    failure = "movement oscillated vertically while crossing the open doorway pocket";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_support_sampling_prefers_raised_open_door_surface_at_d18_seam",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor state";
                    return false;
                }

                std::optional<EventRuntimeState> runtimeState = *loadedMap->eventRuntimeState;
                RuntimeMechanismState mechanism = {};
                mechanism.state = static_cast<uint16_t>(EvtMechanismState::Open);
                mechanism.currentDistance = 0.0f;
                mechanism.isMoving = false;
                runtimeState->mechanisms[1] = mechanism;

                IndoorMovementController controller(
                    *loadedMap->indoorMapData,
                    &loadedMap->indoorMapDeltaData,
                    &runtimeState);
                const IndoorBodyDimensions body = {};
                IndoorMoveState current =
                    controller.initializeStateFromEyePosition(-592.862f, -541.367f, 16.0f, body);
                bool reachedRaisedSupport = false;

                for (int step = 0; step < 8; ++step)
                {
                    current = controller.resolveMove(current, body, -37.2438f, 1279.46f, false, 0.00158256f);

                    if (current.footZ >= -128.5f)
                    {
                        reachedRaisedSupport = true;
                    }
                }

                if (!reachedRaisedSupport)
                {
                    failure = "movement did not step onto the raised doorway support at the seam "
                        + describeIndoorFaceMembership(*loadedMap->indoorMapData, 13);
                    return false;
                }

                if (current.footZ < -128.5f || current.footZ > -127.5f)
                {
                    failure = "movement did not remain on the raised doorway support after crossing the seam";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_world_runtime_exposes_actor_queries_and_direct_damage",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor authored/runtime state";
                    return false;
                }

                std::optional<MapDeltaData> indoorMapDeltaData = *loadedMap->indoorMapDeltaData;
                std::optional<EventRuntimeState> eventRuntimeState = *loadedMap->eventRuntimeState;
                Party party = {};
                party.setItemTable(&gameDataLoader.getItemTable());
                party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
                party.setItemEnchantTables(
                    &gameDataLoader.getStandardItemEnchantTable(),
                    &gameDataLoader.getSpecialItemEnchantTable());
                party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
                party.seed(createRegressionPartySeed());

                GameplayActorService actorService = buildBoundGameplayActorService(gameDataLoader);
                IndoorWorldRuntime worldRuntime = {};
                worldRuntime.initialize(
                    loadedMap->map,
                    gameDataLoader.getMonsterTable(),
                    gameDataLoader.getObjectTable(),
                    gameDataLoader.getItemTable(),
                    gameDataLoader.getChestTable(),
                    &party,
                    nullptr,
                    &indoorMapDeltaData,
                    &eventRuntimeState,
                    &actorService,
                    nullptr,
                    &*loadedMap->indoorMapData);

                if (worldRuntime.mapActorCount() != indoorMapDeltaData->actors.size())
                {
                    failure = "indoor actor count does not match delta actor count";
                    return false;
                }

                std::optional<size_t> selectedActorIndex;

                for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
                {
                    const MapDeltaActor &actor = indoorMapDeltaData->actors[actorIndex];

                    if (actor.hp > 20
                        && (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) == 0)
                    {
                        selectedActorIndex = actorIndex;
                        break;
                    }
                }

                if (!selectedActorIndex.has_value())
                {
                    failure = "could not find a living visible indoor actor";
                    return false;
                }

                const size_t actorIndex = *selectedActorIndex;
                const MapDeltaActor &initialActor = indoorMapDeltaData->actors[actorIndex];
                GameplayRuntimeActorState actorState = {};

                if (!worldRuntime.actorRuntimeState(actorIndex, actorState))
                {
                    failure = "actorRuntimeState failed for a valid indoor actor";
                    return false;
                }

                if (std::abs(actorState.preciseX - static_cast<float>(initialActor.x)) > 0.01f
                    || std::abs(actorState.preciseY - static_cast<float>(initialActor.y)) > 0.01f
                    || std::abs(actorState.preciseZ - static_cast<float>(initialActor.z)) > 0.01f
                    || actorState.height != initialActor.height)
                {
                    failure = "indoor actor query did not mirror delta actor geometry";
                    return false;
                }

                const float actorCenterZ =
                    actorState.preciseZ + std::max(24.0f, static_cast<float>(actorState.height) * 0.7f);
                const std::vector<size_t> nearbyActors = worldRuntime.collectMapActorIndicesWithinRadius(
                    actorState.preciseX,
                    actorState.preciseY,
                    actorCenterZ,
                    1.0f,
                    false,
                    actorState.preciseX,
                    actorState.preciseY,
                    actorCenterZ);

                if (std::find(nearbyActors.begin(), nearbyActors.end(), actorIndex) == nearbyActors.end())
                {
                    failure = "radius query did not return the actor at the query center";
                    return false;
                }

                const int initialHp = indoorMapDeltaData->actors[actorIndex].hp;

                if (!worldRuntime.applyPartySpellToActor(
                        actorIndex,
                        spellIdValue(SpellId::Blades),
                        10,
                        SkillMastery::Master,
                        17,
                        0.0f,
                        0.0f,
                        0.0f,
                        0))
                {
                    failure = "direct indoor actor damage failed";
                    return false;
                }

                if (indoorMapDeltaData->actors[actorIndex].hp != initialHp - 17)
                {
                    failure = "direct indoor actor damage did not update hp";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "party_spell_system_supports_indoor_shared_runtime_direct_actor_damage",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor authored/runtime state";
                    return false;
                }

                std::optional<MapDeltaData> indoorMapDeltaData = *loadedMap->indoorMapDeltaData;
                std::optional<EventRuntimeState> eventRuntimeState = *loadedMap->eventRuntimeState;
                IndoorPartyRuntime partyRuntime(
                    IndoorMovementController(
                        *loadedMap->indoorMapData,
                        &indoorMapDeltaData,
                        &eventRuntimeState),
                    gameDataLoader.getItemTable());

                Party &party = partyRuntime.party();
                party.setCharacterDollTable(&gameDataLoader.getCharacterDollTable());
                party.setItemEnchantTables(
                    &gameDataLoader.getStandardItemEnchantTable(),
                    &gameDataLoader.getSpecialItemEnchantTable());
                party.setClassSkillTable(&gameDataLoader.getClassSkillTable());
                party.seed(createRegressionPartySeed());
                partyRuntime.initializePartyPosition(-661.0f, -1059.0f, -39.0f, false);

                GameplayActorService actorService = buildBoundGameplayActorService(gameDataLoader);
                IndoorWorldRuntime worldRuntime = {};
                worldRuntime.initialize(
                    loadedMap->map,
                    gameDataLoader.getMonsterTable(),
                    gameDataLoader.getObjectTable(),
                    gameDataLoader.getItemTable(),
                    gameDataLoader.getChestTable(),
                    &party,
                    &partyRuntime,
                    &indoorMapDeltaData,
                    &eventRuntimeState,
                    &actorService,
                    nullptr,
                    &*loadedMap->indoorMapData);

                std::optional<size_t> targetActorIndex;

                for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
                {
                    const MapDeltaActor &actor = indoorMapDeltaData->actors[actorIndex];

                    if (actor.hp > 20
                        && (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) == 0)
                    {
                        targetActorIndex = actorIndex;
                        break;
                    }
                }

                if (!targetActorIndex.has_value())
                {
                    failure = "could not find a living visible indoor actor";
                    return false;
                }

                const int initialHp = indoorMapDeltaData->actors[*targetActorIndex].hp;
                PartySpellCastRequest castRequest = {};
                castRequest.casterMemberIndex = 0;
                castRequest.spellId = spellIdValue(SpellId::Blades);
                castRequest.skillLevelOverride = 10;
                castRequest.skillMasteryOverride = SkillMastery::Master;
                castRequest.spendMana = false;
                castRequest.targetActorIndex = *targetActorIndex;

                const PartySpellCastResult castResult = PartySpellSystem::castSpell(
                    party,
                    worldRuntime,
                    gameDataLoader.getSpellTable(),
                    castRequest);

                if (!castResult.succeeded())
                {
                    failure = "Blades failed through indoor shared runtime";
                    return false;
                }

                if (indoorMapDeltaData->actors[*targetActorIndex].hp >= initialHp)
                {
                    failure = "Blades did not reduce indoor actor hp";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_world_runtime_lethal_damage_generates_corpse_loot_and_exhausts_corpse",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap)
                {
                    failure = "selected map missing";
                    return false;
                }

                IndoorRegressionScenario scenario = {};

                if (!initializeIndoorRegressionScenario(gameDataLoader, *loadedMap, scenario))
                {
                    failure = "could not initialize indoor scenario";
                    return false;
                }

                const MonsterTable &monsterTable = gameDataLoader.getMonsterTable();
                const MonsterTable::MonsterStatsEntry *pLootStats = nullptr;

                for (int monsterId = 1; monsterId < 2000; ++monsterId)
                {
                    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(int16_t(monsterId));
                    const MonsterEntry *pEntry = monsterTable.findById(int16_t(monsterId));

                    if (pStats == nullptr || pEntry == nullptr)
                    {
                        continue;
                    }

                    const MonsterTable::LootPrototype &loot = pStats->loot;

                    if ((loot.goldDiceRolls > 0 && loot.goldDiceSides > 0)
                        || (loot.itemChance > 0 && loot.itemLevel > 0))
                    {
                        pLootStats = pStats;
                        break;
                    }
                }

                if (pLootStats == nullptr)
                {
                    failure = "could not find a loot-bearing monster definition";
                    return false;
                }

                MapDeltaActor syntheticActor = {};
                syntheticActor.name = pLootStats->name;
                syntheticActor.attributes = static_cast<uint32_t>(EvtActorAttribute::Active);
                syntheticActor.hp = 25;
                syntheticActor.monsterInfoId = int16_t(pLootStats->id);
                syntheticActor.monsterId = int16_t(pLootStats->id);
                scenario.mapDeltaData->actors.push_back(syntheticActor);

                const size_t actorIndex = scenario.mapDeltaData->actors.size() - 1;
                const int lethalDamage = scenario.mapDeltaData->actors[actorIndex].hp + 25;

                if (!scenario.world.applyPartySpellToActor(
                        actorIndex,
                        spellIdValue(SpellId::Blades),
                        10,
                        SkillMastery::Master,
                        lethalDamage,
                        0.0f,
                        0.0f,
                        0.0f,
                        0))
                {
                    failure = "could not apply lethal indoor damage";
                    return false;
                }

                if (scenario.mapDeltaData->actors[actorIndex].hp > 0)
                {
                    failure = "indoor lethal damage did not kill the actor";
                    return false;
                }

                if (!scenario.world.openMapActorCorpseView(actorIndex))
                {
                    failure = "indoor corpse view did not open";
                    return false;
                }

                const IndoorWorldRuntime::CorpseViewState *pCorpseView = scenario.world.activeCorpseView();

                if (pCorpseView == nullptr || pCorpseView->items.empty())
                {
                    failure = "indoor corpse loot did not materialize";
                    return false;
                }

                while (const IndoorWorldRuntime::CorpseViewState *pActiveCorpseView = scenario.world.activeCorpseView())
                {
                    if (pActiveCorpseView->items.empty())
                    {
                        break;
                    }

                    IndoorWorldRuntime::ChestItemState lootedItem = {};

                    if (!scenario.world.takeActiveCorpseItem(0, lootedItem))
                    {
                        failure = "could not remove indoor corpse loot item";
                        return false;
                    }
                }

                if (scenario.world.activeCorpseView() != nullptr)
                {
                    failure = "empty indoor corpse view should close itself";
                    return false;
                }

                const MapDeltaActor &actor = scenario.mapDeltaData->actors[actorIndex];

                if ((actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) == 0)
                {
                    failure = "fully looted indoor corpse actor should become invisible";
                    return false;
                }

                if (scenario.world.openMapActorCorpseView(actorIndex))
                {
                    failure = "fully looted indoor corpse should not reopen";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_world_runtime_summon_friendly_monster_materializes_non_hostile_actor",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap)
                {
                    failure = "selected map missing";
                    return false;
                }

                IndoorRegressionScenario scenario = {};

                if (!initializeIndoorRegressionScenario(gameDataLoader, *loadedMap, scenario))
                {
                    failure = "could not initialize indoor scenario";
                    return false;
                }

                const size_t initialActorCount = scenario.world.mapActorCount();

                int16_t summonMonsterId = 0;

                for (int monsterId = 1; monsterId < 2000; ++monsterId)
                {
                    if (gameDataLoader.getMonsterTable().findStatsById(int16_t(monsterId)) != nullptr
                        && gameDataLoader.getMonsterTable().findById(int16_t(monsterId)) != nullptr)
                    {
                        summonMonsterId = int16_t(monsterId);
                        break;
                    }
                }

                if (summonMonsterId == 0)
                {
                    failure = "could not find a summonable monster definition";
                    return false;
                }

                if (!scenario.world.summonFriendlyMonsterById(summonMonsterId, 1, 60.0f, -661.0f, -1059.0f, -39.0f))
                {
                    failure = "indoor friendly summon did not materialize";
                    return false;
                }

                if (scenario.world.mapActorCount() != initialActorCount + 1)
                {
                    failure = "indoor actor count did not increase after friendly summon";
                    return false;
                }

                GameplayRuntimeActorState actorState = {};

                if (!scenario.world.actorRuntimeState(initialActorCount, actorState))
                {
                    failure = "could not query summoned indoor actor runtime state";
                    return false;
                }

                if (actorState.hostileToParty)
                {
                    failure = "summoned indoor actor should not be hostile to the party";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_open_mechanism_faces_are_not_used_as_support_floor",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor state";
                    return false;
                }

                std::optional<EventRuntimeState> runtimeState = *loadedMap->eventRuntimeState;
                RuntimeMechanismState mechanism = {};
                mechanism.state = static_cast<uint16_t>(EvtMechanismState::Open);
                mechanism.currentDistance = 0.0f;
                mechanism.isMoving = false;
                runtimeState->mechanisms[6] = mechanism;

                IndoorMovementController controller(
                    *loadedMap->indoorMapData,
                    &loadedMap->indoorMapDeltaData,
                    &runtimeState);
                const IndoorBodyDimensions body = {};
                const IndoorMoveState initialized =
                    controller.initializeStateFromEyePosition(1904.0f, 368.0f, 160.0f, body);

                if (std::fabs(initialized.footZ - (-128.0f)) > 0.1f)
                {
                    failure = "open door 6 still contributes support floor at the doorway: footZ="
                        + std::to_string(initialized.footZ)
                        + " supportFace=" + std::to_string(initialized.supportFaceIndex)
                        + " " + describeIndoorFaceMembership(*loadedMap->indoorMapData, 389);
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_d18_local_startup_override_position_allows_movement",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData || !loadedMap->eventRuntimeState)
                {
                    failure = "d18.blv missing indoor state";
                    return false;
                }

                IndoorMovementController controller(
                    *loadedMap->indoorMapData,
                    &loadedMap->indoorMapDeltaData,
                    &loadedMap->eventRuntimeState);
                const IndoorBodyDimensions body = {};
                const IndoorMoveState initial =
                    controller.initializeStateFromEyePosition(-661.0f, -1059.0f, -39.0f, body);
                const IndoorMoveState settled =
                    controller.resolveMove(initial, body, 0.0f, 0.0f, false, 0.1f);
                const IndoorMoveState jumped = controller.resolveMove(initial, body, 0.0f, 0.0f, true, 0.1f);
                const IndoorMoveState moved = controller.resolveMove(initial, body, 0.0f, 160.0f, false, 0.1f);
                const IndoorMoveState footSemanticInitial =
                    controller.initializeStateFromEyePosition(-661.0f, -1059.0f, -39.0f + body.height, body);
                const IndoorMoveState footSemanticJumped =
                    controller.resolveMove(footSemanticInitial, body, 0.0f, 0.0f, true, 0.1f);
                const IndoorMoveState footSemanticMoved =
                    controller.resolveMove(footSemanticInitial, body, 0.0f, 160.0f, false, 0.1f);
                const IndoorMoveState authoredEntranceInitial =
                    controller.initializeStateFromEyePosition(-500.0f, -1567.0f, -63.0f + body.height, body);
                const IndoorMoveState authoredEntranceSettled =
                    controller.resolveMove(authoredEntranceInitial, body, 0.0f, 0.0f, false, 0.1f);
                const IndoorMoveState authoredEntranceJumped =
                    controller.resolveMove(authoredEntranceInitial, body, 0.0f, 0.0f, true, 0.1f);
                const IndoorMoveState authoredEntranceMoved =
                    controller.resolveMove(authoredEntranceInitial, body, 0.0f, 160.0f, false, 0.1f);

                if ((!initial.grounded && settled.footZ < initial.footZ - 0.1f)
                    || (!authoredEntranceInitial.grounded && authoredEntranceSettled.footZ < authoredEntranceInitial.footZ - 0.1f))
                {
                    failure =
                        "startup position is unsupported and falls immediately"
                        " eye_init=(" + std::to_string(initial.x)
                        + "," + std::to_string(initial.y)
                        + "," + std::to_string(initial.footZ)
                        + "," + std::to_string(initial.grounded ? 1.0f : 0.0f)
                        + ") eye_settled=(" + std::to_string(settled.footZ)
                        + "," + std::to_string(settled.grounded ? 1.0f : 0.0f)
                        + ") authored_init=(" + std::to_string(authoredEntranceInitial.x)
                        + "," + std::to_string(authoredEntranceInitial.y)
                        + "," + std::to_string(authoredEntranceInitial.footZ)
                        + "," + std::to_string(authoredEntranceInitial.grounded ? 1.0f : 0.0f)
                        + ") authored_settled=(" + std::to_string(authoredEntranceSettled.footZ)
                        + "," + std::to_string(authoredEntranceSettled.grounded ? 1.0f : 0.0f)
                        + ") " + describeIndoorFaceMembership(*loadedMap->indoorMapData, 1363);
                    return false;
                }

                if (jumped.footZ == initial.footZ && jumped.verticalVelocity == initial.verticalVelocity)
                {
                    failure =
                        "startup position rejected jump resolution"
                        " eye_init=(" + std::to_string(initial.x)
                        + "," + std::to_string(initial.y)
                        + "," + std::to_string(initial.footZ)
                        + ") eye_jump=(" + std::to_string(jumped.footZ)
                        + "," + std::to_string(jumped.verticalVelocity)
                        + ") foot_jump=(" + std::to_string(footSemanticJumped.footZ)
                        + "," + std::to_string(footSemanticJumped.verticalVelocity)
                        + ") authored_jump=(" + std::to_string(authoredEntranceJumped.footZ)
                        + "," + std::to_string(authoredEntranceJumped.verticalVelocity)
                        + ")";
                    return false;
                }

                if (std::abs(moved.x - initial.x) <= 0.01f && std::abs(moved.y - initial.y) <= 0.01f)
                {
                    failure =
                        "startup position rejected planar movement"
                        " eye_move=(" + std::to_string(moved.x)
                        + "," + std::to_string(moved.y)
                        + ") foot_move=(" + std::to_string(footSemanticMoved.x)
                        + "," + std::to_string(footSemanticMoved.y)
                        + ") authored_move=(" + std::to_string(authoredEntranceMoved.x)
                        + "," + std::to_string(authoredEntranceMoved.y)
                        + ")";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_event_runtime_summon_item_materializes_sprite_object",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap)
                {
                    failure = "selected map missing";
                    return false;
                }

                IndoorRegressionScenario scenario = {};

                if (!initializeIndoorRegressionScenario(gameDataLoader, *loadedMap, scenario))
                {
                    failure = "could not initialize indoor scenario";
                    return false;
                }

                std::string error;
                const std::optional<ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
                    "evt.map[1] = function()\n"
                    "    evt.SummonItem(200, 128, 256, 384, 0, 1, false)\n"
                    "end\n",
                    "indoor_summon_item.lua",
                    ScriptedEventScope::Map,
                    error
                );

                if (!scriptedProgram)
                {
                    failure = "could not build synthetic summon-item script: " + error;
                    return false;
                }

                const size_t initialObjectCount = scenario.mapDeltaData ? scenario.mapDeltaData->spriteObjects.size() : 0;
                EventRuntimeState *pEventRuntimeState = scenario.world.eventRuntimeState();

                if (pEventRuntimeState == nullptr)
                {
                    failure = "event runtime state missing";
                    return false;
                }

                if (!scenario.eventRuntime.executeEventById(
                        scriptedProgram,
                        loadedMap->globalEventProgram,
                        1,
                        *pEventRuntimeState,
                        &scenario.party,
                        &scenario.world))
                {
                    failure = "synthetic summon-item event did not execute";
                    return false;
                }

                scenario.world.applyEventRuntimeState();

                if (!scenario.mapDeltaData || scenario.mapDeltaData->spriteObjects.size() != initialObjectCount + 1)
                {
                    failure = "synthetic summon-item event did not add one sprite object";
                    return false;
                }

                const MapDeltaSpriteObject &object = scenario.mapDeltaData->spriteObjects.back();

                if (object.objectDescriptionId == 0 || object.rawContainingItem.size() < sizeof(int32_t))
                {
                    failure = "spawned indoor sprite object payload is incomplete";
                    return false;
                }

                int32_t rawItemId = 0;
                std::memcpy(&rawItemId, object.rawContainingItem.data(), sizeof(rawItemId));

                if (rawItemId != 200)
                {
                    failure = "spawned indoor sprite object carried wrong item payload";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_event_runtime_open_chest_materializes_layout_and_supports_grid_ops",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap)
                {
                    failure = "selected map missing";
                    return false;
                }

                IndoorRegressionScenario scenario = {};

                if (!initializeIndoorRegressionScenario(gameDataLoader, *loadedMap, scenario))
                {
                    failure = "could not initialize indoor scenario";
                    return false;
                }

                uint32_t fixedItemId = 0;

                for (const ItemDefinition &entry : gameDataLoader.getItemTable().entries())
                {
                    if (entry.itemId != 0 && entry.inventoryWidth == 1 && entry.inventoryHeight == 1)
                    {
                        fixedItemId = entry.itemId;
                        break;
                    }
                }

                if (fixedItemId == 0)
                {
                    failure = "could not find a 1x1 regression chest item";
                    return false;
                }

                const ChestEntry *pChestEntry = gameDataLoader.getChestTable().get(0);

                if (pChestEntry == nullptr)
                {
                    failure = "chest type 0 missing";
                    return false;
                }

                MapDeltaChest &chest = scenario.mapDeltaData->chests[0];
                chest.chestTypeId = 0;
                chest.flags = 0;
                chest.rawItems.assign(36, 0);
                std::memcpy(chest.rawItems.data(), &fixedItemId, sizeof(fixedItemId));
                chest.inventoryMatrix.assign(
                    static_cast<size_t>(pChestEntry->gridWidth) * pChestEntry->gridHeight,
                    0);
                chest.inventoryMatrix[0] = 1;

                std::string error;
                const std::optional<ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
                    "evt.map[1] = function()\n"
                    "    evt.OpenChest(0)\n"
                    "end\n",
                    "indoor_open_chest.lua",
                    ScriptedEventScope::Map,
                    error);

                if (!scriptedProgram)
                {
                    failure = "could not build synthetic open-chest script: " + error;
                    return false;
                }

                EventRuntimeState *pEventRuntimeState = scenario.world.eventRuntimeState();

                if (pEventRuntimeState == nullptr)
                {
                    failure = "event runtime state missing";
                    return false;
                }

                if (!scenario.eventRuntime.executeEventById(
                        scriptedProgram,
                        loadedMap->globalEventProgram,
                        1,
                        *pEventRuntimeState,
                        &scenario.party,
                        &scenario.world))
                {
                    failure = "synthetic open-chest event did not execute";
                    return false;
                }

                scenario.world.applyEventRuntimeState();

                const IndoorWorldRuntime::ChestViewState *pChestView = scenario.world.activeChestView();

                if (pChestView == nullptr)
                {
                    failure = "active indoor chest view missing";
                    return false;
                }

                if (pChestView->items.size() != 1 || pChestView->items[0].itemId != fixedItemId)
                {
                    failure = "indoor chest materialized the wrong items";
                    return false;
                }

                IndoorWorldRuntime::ChestItemState removedItem = {};

                if (!scenario.world.takeActiveChestItemAt(0, 0, removedItem))
                {
                    failure = "could not remove indoor chest item by grid cell";
                    return false;
                }

                if (!scenario.world.tryPlaceActiveChestItemAt(removedItem, 2, 2))
                {
                    failure = "could not place indoor chest item back into chest";
                    return false;
                }

                pChestView = scenario.world.activeChestView();

                if (pChestView == nullptr
                    || pChestView->items.size() != 1
                    || pChestView->items[0].gridX != 2
                    || pChestView->items[0].gridY != 2)
                {
                    failure = "indoor chest grid placement did not persist";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_world_runtime_snapshot_roundtrips_chest_runtime_state",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap)
                {
                    failure = "selected map missing";
                    return false;
                }

                IndoorRegressionScenario scenario = {};

                if (!initializeIndoorRegressionScenario(gameDataLoader, *loadedMap, scenario))
                {
                    failure = "could not initialize indoor scenario";
                    return false;
                }

                uint32_t fixedItemId = 0;

                for (const ItemDefinition &entry : gameDataLoader.getItemTable().entries())
                {
                    if (entry.itemId != 0 && entry.inventoryWidth == 1 && entry.inventoryHeight == 1)
                    {
                        fixedItemId = entry.itemId;
                        break;
                    }
                }

                if (fixedItemId == 0)
                {
                    failure = "could not find a 1x1 regression chest item";
                    return false;
                }

                const ChestEntry *pChestEntry = gameDataLoader.getChestTable().get(0);

                if (pChestEntry == nullptr)
                {
                    failure = "chest type 0 missing";
                    return false;
                }

                MapDeltaChest &chest = scenario.mapDeltaData->chests[0];
                chest.chestTypeId = 0;
                chest.flags = 0;
                chest.rawItems.assign(36, 0);
                std::memcpy(chest.rawItems.data(), &fixedItemId, sizeof(fixedItemId));
                chest.inventoryMatrix.assign(
                    static_cast<size_t>(pChestEntry->gridWidth) * pChestEntry->gridHeight,
                    0);
                chest.inventoryMatrix[0] = 1;
                scenario.eventRuntimeState->openedChestIds.push_back(0);
                scenario.world.applyEventRuntimeState();

                IndoorWorldRuntime::ChestItemState removedItem = {};

                if (!scenario.world.takeActiveChestItemAt(0, 0, removedItem)
                    || !scenario.world.tryPlaceActiveChestItemAt(removedItem, 3, 1))
                {
                    failure = "could not prepare indoor chest state before snapshot";
                    return false;
                }

                const IndoorWorldRuntime::Snapshot snapshot = scenario.world.snapshot();
                std::optional<MapDeltaData> restoredMapDelta = *scenario.mapDeltaData;
                std::optional<EventRuntimeState> restoredEventRuntimeState = *scenario.eventRuntimeState;
                GameplayActorService actorService = buildBoundGameplayActorService(gameDataLoader);
                IndoorWorldRuntime restoredWorld = {};
                restoredWorld.initialize(
                    loadedMap->map,
                    gameDataLoader.getMonsterTable(),
                    gameDataLoader.getObjectTable(),
                    gameDataLoader.getItemTable(),
                    gameDataLoader.getChestTable(),
                    &scenario.party,
                    nullptr,
                    &restoredMapDelta,
                    &restoredEventRuntimeState,
                    &actorService);
                restoredWorld.restoreSnapshot(snapshot);

                const IndoorWorldRuntime::ChestViewState *pRestoredChestView = restoredWorld.activeChestView();

                if (pRestoredChestView == nullptr
                    || pRestoredChestView->items.size() != 1
                    || pRestoredChestView->items[0].itemId != fixedItemId
                    || pRestoredChestView->items[0].gridX != 3
                    || pRestoredChestView->items[0].gridY != 1)
                {
                    failure = "indoor chest runtime state did not roundtrip through snapshot";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_check_monsters_killed_respects_invisible_as_dead",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap)
                {
                    failure = "selected map missing";
                    return false;
                }

                IndoorRegressionScenario scenario = {};

                if (!initializeIndoorRegressionScenario(gameDataLoader, *loadedMap, scenario))
                {
                    failure = "could not initialize indoor scenario";
                    return false;
                }

                MapDeltaActor actor = {};
                actor.hp = 100;
                actor.group = 77;
                scenario.mapDeltaData->actors.push_back(actor);

                if (scenario.world.checkMonstersKilled(
                        static_cast<uint32_t>(EvtActorKillCheck::Group),
                        77,
                        0,
                        false))
                {
                    failure = "visible living actor was treated as killed";
                    return false;
                }

                scenario.mapDeltaData->actors.back().attributes |= static_cast<uint32_t>(EvtActorAttribute::Invisible);

                if (!scenario.world.checkMonstersKilled(
                        static_cast<uint32_t>(EvtActorKillCheck::Group),
                        77,
                        0,
                        true))
                {
                    failure = "invisible indoor actor was not treated as defeated";
                    return false;
                }

                return true;
            }
        );

        runCase(
            "indoor_event_runtime_cast_spell_queues_fx_request",
            [&](std::string &failure)
            {
                if (!gameDataLoader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "d18.blv"))
                {
                    failure = "could not load d18.blv";
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = gameDataLoader.getSelectedMap();

                if (!loadedMap)
                {
                    failure = "selected map missing";
                    return false;
                }

                IndoorRegressionScenario scenario = {};

                if (!initializeIndoorRegressionScenario(gameDataLoader, *loadedMap, scenario))
                {
                    failure = "could not initialize indoor scenario";
                    return false;
                }

                std::string error;
                const std::optional<ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
                    "evt.map[1] = function()\n"
                    "    evt.CastSpell(6, 10, 3, 100, 200, 300, 400, 500, 600)\n"
                    "end\n",
                    "indoor_cast_spell.lua",
                    ScriptedEventScope::Map,
                    error
                );

                if (!scriptedProgram)
                {
                    failure = "could not build synthetic cast-spell script: " + error;
                    return false;
                }

                EventRuntimeState *pEventRuntimeState = scenario.world.eventRuntimeState();

                if (pEventRuntimeState == nullptr)
                {
                    failure = "event runtime state missing";
                    return false;
                }

                if (!scenario.eventRuntime.executeEventById(
                        scriptedProgram,
                        loadedMap->globalEventProgram,
                        1,
                        *pEventRuntimeState,
                        &scenario.party,
                        &scenario.world))
                {
                    failure = "synthetic cast-spell event did not execute";
                    return false;
                }

                if (pEventRuntimeState->spellFxRequests.empty() || pEventRuntimeState->spellFxRequests.back().spellId != 6)
                {
                    failure = "indoor cast-spell path did not queue spell fx";
                    return false;
                }

                return true;
            }
        );

        std::cout << "Regression suite summary: passed=" << passedCount << " failed=" << failedCount << '\n';
        return failedCount == 0 ? 0 : 1;
    }

    if (suiteName == "chest" || suiteName == "items" || suiteName == "outdoor")
    {
        runCase(
            "dwi_chest_events_materialize_non_empty_layouts",
            [&](std::string &failure)
            {
                static constexpr std::array<uint16_t, 18> chestEventIds = {{
                    81,
                    82,
                    83,
                    85,
                    86,
                    87,
                    88,
                    89,
                    90,
                    91,
                    92,
                    93,
                    94,
                    95,
                    96,
                    97,
                    98,
                    99
                }};

                for (uint16_t eventId : chestEventIds)
                {
                    RegressionScenario scenario = {};

                    if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
                    {
                        failure = "scenario init failed for event " + std::to_string(eventId);
                        return false;
                    }

                    if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, eventId))
                    {
                        failure = "event " + std::to_string(eventId) + " did not execute";
                        return false;
                    }

                    const OutdoorWorldRuntime::ChestViewState *pChestView = scenario.world.activeChestView();

                    if (pChestView == nullptr)
                    {
                        failure = "event " + std::to_string(eventId) + " did not open a chest";
                        return false;
                    }

                    if (pChestView->items.empty())
                    {
                        failure = "event " + std::to_string(eventId)
                            + " opened empty chest #" + std::to_string(pChestView->chestId);
                        return false;
                    }

                    std::string layoutFailure;

                    if (!validateChestLayout(*pChestView, layoutFailure))
                    {
                        failure = "event " + std::to_string(eventId) + " invalid layout: " + layoutFailure;
                        return false;
                    }
                }

                return true;
            }
        );

        runCase(
            "dwi_chest_event_100_materializes_final_chest",
            [&](std::string &failure)
            {
                RegressionScenario scenario = {};

                if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
                {
                    failure = "scenario init failed";
                    return false;
                }

                if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 100))
                {
                    failure = "event 100 did not execute";
                    return false;
                }

                const OutdoorWorldRuntime::ChestViewState *pChestView = scenario.world.activeChestView();

                if (pChestView == nullptr)
                {
                    failure = "event 100 did not open a chest";
                    return false;
                }

                if (pChestView->chestId != 19)
                {
                    failure = "event 100 opened chest #" + std::to_string(pChestView->chestId);
                    return false;
                }

                if (pChestView->items.empty())
                {
                    failure = "event 100 opened empty chest #19";
                    return false;
                }

                return true;
            }
        );

        std::cout << "Regression suite summary: passed=" << passedCount << " failed=" << failedCount << '\n';
        return failedCount == 0 ? 0 : 1;
    }

    runCase(
        "dwi_tavern_arcomage_play_requests_match",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            EventDialogContent dialog = {};

            if (!openLocalEventDialogInScenario(gameDataLoader, *selectedMap, scenario, 191, dialog))
            {
                failure = "could not open tavern";
                return false;
            }

            const std::optional<size_t> arcomageIndex = findActionIndexByLabel(dialog, "Play Arcomage");

            if (!arcomageIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *arcomageIndex, dialog))
            {
                failure = "could not open Arcomage submenu";
                return false;
            }

            const std::optional<size_t> playIndex = findActionIndexByLabel(dialog, "Play");

            if (!playIndex
                || !executeDialogActionInScenario(gameDataLoader, *selectedMap, scenario, *playIndex, dialog))
            {
                failure = "could not request Arcomage match";
                return false;
            }

            if (!scenario.pEventRuntimeState->pendingArcomageGame.has_value()
                || scenario.pEventRuntimeState->pendingArcomageGame->houseId == 0)
            {
                failure = "Arcomage play did not queue a pending match";
                return false;
            }

            return true;
        }
    );

    runCase(
        "local_event_457_spawns_runtime_fireball_and_cannonball_projectiles",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 457))
            {
                failure = "event 457 did not execute";
                return false;
            }

            if (scenario.world.projectileCount() < 2)
            {
                failure = "event 457 did not spawn both runtime projectiles";
                return false;
            }

            bool sawFireball = false;
            bool sawCannonball = false;

            for (size_t projectileIndex = 0; projectileIndex < scenario.world.projectileCount(); ++projectileIndex)
            {
                const OutdoorWorldRuntime::ProjectileState *pProjectile = scenario.world.projectileState(projectileIndex);

                if (pProjectile == nullptr)
                {
                    failure = "projectile state missing";
                    return false;
                }

                sawFireball =
                    sawFireball
                    || isSpellId(pProjectile->spellId, SpellId::Fireball)
                    || pProjectile->objectName == "Fireball";
                sawCannonball = sawCannonball || pProjectile->spellId == 136 || pProjectile->objectName == "Cannonball";
            }

            if (!sawFireball || !sawCannonball)
            {
                failure = !sawFireball ? "fireball projectile missing" : "cannonball projectile missing";
                return false;
            }

            bool sawImpact = false;

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, 0.0f, 0.0f, 0.0f);

                if (scenario.world.projectileImpactCount() > 0)
                {
                    sawImpact = true;
                    break;
                }
            }

            if (!sawImpact)
            {
                failure = "event 457 projectiles never produced an impact";
                return false;
            }

            return true;
        }
    );

    runCase(
        "local_event_457_cannonball_uses_gravity_but_fireball_does_not",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 457))
            {
                failure = "event 457 did not execute";
                return false;
            }

            const OutdoorWorldRuntime::ProjectileState *pFireball = nullptr;
            const OutdoorWorldRuntime::ProjectileState *pCannonball = nullptr;

            for (size_t projectileIndex = 0; projectileIndex < scenario.world.projectileCount(); ++projectileIndex)
            {
                const OutdoorWorldRuntime::ProjectileState *pProjectile = scenario.world.projectileState(projectileIndex);

                if (pProjectile == nullptr)
                {
                    failure = "projectile state missing";
                    return false;
                }

                if (isSpellId(pProjectile->spellId, SpellId::Fireball) || pProjectile->objectName == "Fireball")
                {
                    pFireball = pProjectile;
                }
                else if (pProjectile->spellId == 136 || pProjectile->objectName == "Cannonball")
                {
                    pCannonball = pProjectile;
                }
            }

            if (pFireball == nullptr || pCannonball == nullptr)
            {
                failure = pFireball == nullptr ? "fireball projectile missing" : "cannonball projectile missing";
                return false;
            }

            const float initialFireballZ = pFireball->z;
            const float initialCannonballZ = pCannonball->z;

            scenario.world.updateMapActors(1.0f / 128.0f, 0.0f, 0.0f, 0.0f);

            const OutdoorWorldRuntime::ProjectileState *pUpdatedFireball = nullptr;
            const OutdoorWorldRuntime::ProjectileState *pUpdatedCannonball = nullptr;

            for (size_t projectileIndex = 0; projectileIndex < scenario.world.projectileCount(); ++projectileIndex)
            {
                const OutdoorWorldRuntime::ProjectileState *pProjectile = scenario.world.projectileState(projectileIndex);

                if (pProjectile == nullptr)
                {
                    failure = "updated projectile state missing";
                    return false;
                }

                if (isSpellId(pProjectile->spellId, SpellId::Fireball) || pProjectile->objectName == "Fireball")
                {
                    pUpdatedFireball = pProjectile;
                }
                else if (pProjectile->spellId == 136 || pProjectile->objectName == "Cannonball")
                {
                    pUpdatedCannonball = pProjectile;
                }
            }

            if (pUpdatedFireball == nullptr || pUpdatedCannonball == nullptr)
            {
                failure =
                    pUpdatedFireball == nullptr
                        ? "updated fireball projectile missing"
                        : "updated cannonball projectile missing";
                return false;
            }

            if (!(pUpdatedCannonball->z < initialCannonballZ))
            {
                failure = "cannonball projectile did not drop under gravity";
                return false;
            }

            if (std::abs(pUpdatedFireball->z - initialFireballZ) > 0.5f)
            {
                failure = "fireball projectile unexpectedly changed height";
                return false;
            }

            return true;
        }
    );

    runCase(
        "map_delta_pickable_sprite_objects_materialize_runtime_world_items",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (scenario.world.worldItemCount() == 0)
            {
                failure = "selected map materialized no runtime world items";
                return false;
            }

            const ItemDefinition *pItemDefinition = gameDataLoader.getItemTable().get(104);

            if (pItemDefinition == nullptr || pItemDefinition->spriteIndex == 0)
            {
                failure = "missing test item 104 sprite mapping";
                return false;
            }

            const std::optional<uint16_t> objectDescriptionId =
                gameDataLoader.getObjectTable().findDescriptionIdByObjectId(
                    static_cast<int16_t>(pItemDefinition->spriteIndex));

            if (!objectDescriptionId)
            {
                failure = "could not resolve object description for test item 104";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;

            MapDeltaSpriteObject spriteObject = {};
            spriteObject.objectDescriptionId = *objectDescriptionId;
            spriteObject.rawContainingItem.assign(0x24, 0);

            const int32_t rawItemId = 104;
            std::memcpy(spriteObject.rawContainingItem.data(), &rawItemId, sizeof(rawItemId));
            modifiedMap.outdoorMapDeltaData->spriteObjects.push_back(std::move(spriteObject));

            RegressionScenario modifiedScenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, modifiedScenario))
            {
                failure = "scenario init failed";
                return false;
            }

            bool foundMaterializedItem = false;

            for (size_t worldItemIndex = 0; worldItemIndex < modifiedScenario.world.worldItemCount(); ++worldItemIndex)
            {
                const OutdoorWorldRuntime::WorldItemState *pWorldItem =
                    modifiedScenario.world.worldItemState(worldItemIndex);

                if (pWorldItem != nullptr && pWorldItem->item.objectDescriptionId == 104)
                {
                    foundMaterializedItem = true;
                    break;
                }
            }

            if (!foundMaterializedItem)
            {
                failure = "synthetic map-delta sprite object did not materialize as runtime world item";
                return false;
            }

            return true;
        }
    );

    runCase(
        "spawn_world_item_resolves_object_mapping_and_velocity",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const ItemDefinition *pItemDefinition = gameDataLoader.getItemTable().get(104);

            if (pItemDefinition == nullptr)
            {
                failure = "missing test item 104";
                return false;
            }

            InventoryItem item = {};
            item.objectDescriptionId = 104;
            item.quantity = 1;
            item.width = pItemDefinition->inventoryWidth;
            item.height = pItemDefinition->inventoryHeight;

            const size_t initialCount = scenario.world.worldItemCount();

            if (!scenario.world.spawnWorldItem(item, 10.0f, 20.0f, 100.0f, 0.0f))
            {
                failure = "spawnWorldItem rejected valid inventory item";
                return false;
            }

            if (scenario.world.worldItemCount() != initialCount + 1)
            {
                failure = "runtime world item count did not increase after spawn";
                return false;
            }

            const OutdoorWorldRuntime::WorldItemState *pWorldItem = scenario.world.worldItemState(initialCount);

            if (pWorldItem == nullptr)
            {
                failure = "spawned world item state missing";
                return false;
            }

            if (pWorldItem->item.objectDescriptionId != 104
                || pWorldItem->objectDescriptionId == 0
                || pWorldItem->objectSpriteId == 0)
            {
                failure = "spawned world item mapping is incomplete";
                return false;
            }

            if (pWorldItem->velocityX == 0.0f && pWorldItem->velocityY == 0.0f && pWorldItem->velocityZ == 0.0f)
            {
                failure = "spawned world item has no throw velocity";
                return false;
            }

            return true;
        }
    );

    runCase(
        "event_summon_item_supports_item_and_object_payloads",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t initialCount = scenario.world.worldItemCount();

            if (!scenario.world.summonEventItem(200, 100, 200, 300, 1000, 1, true))
            {
                failure = "direct item payload 200 did not spawn";
                return false;
            }

            const OutdoorWorldRuntime::WorldItemState *pDirectItem = scenario.world.worldItemState(initialCount);

            if (pDirectItem == nullptr || pDirectItem->item.objectDescriptionId != 200)
            {
                failure = "direct item payload did not preserve item id 200";
                return false;
            }

            if (pDirectItem->x != 100.0f || pDirectItem->y != 200.0f || pDirectItem->z != 300.0f)
            {
                failure = "direct item payload did not preserve summon position";
                return false;
            }

            if (!scenario.world.summonEventItem(35, 100, 200, 300, 1000, 1, true))
            {
                failure = "object payload 35 did not spawn";
                return false;
            }

            const OutdoorWorldRuntime::WorldItemState *pObjectBackedItem =
                scenario.world.worldItemState(initialCount + 1);

            if (pObjectBackedItem == nullptr || pObjectBackedItem->item.objectDescriptionId != 205)
            {
                failure = "object payload 35 did not resolve to item id 205";
                return false;
            }

            if (pObjectBackedItem->x != 100.0f || pObjectBackedItem->y != 200.0f || pObjectBackedItem->z != 300.0f)
            {
                failure = "object payload 35 did not preserve summon position";
                return false;
            }

            if (scenario.world.summonEventItem(2138, 100, 200, 300, 1000, 1, true))
            {
                failure = "unresolved payload 2138 unexpectedly spawned";
                return false;
            }

            if (scenario.world.worldItemCount() != initialCount + 2)
            {
                failure = "world item count changed unexpectedly after unresolved payload";
                return false;
            }

            return true;
        }
    );

    runCase(
        "campfire_global_event_adds_food_and_hides_on_clear",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (scenario.pEventRuntimeState == nullptr)
            {
                failure = "missing event runtime state";
                return false;
            }

            EventRuntimeState::ActiveDecorationContext context = {};
            context.decorVarIndex = 0;
            context.baseEventId = 285;
            context.currentEventId = 285;
            context.eventCount = 2;
            context.hideWhenCleared = true;
            scenario.pEventRuntimeState->activeDecorationContext = context;

            const int initialFood = scenario.party.food();
            const bool executed = scenario.eventRuntime.executeEventById(
                std::nullopt,
                selectedMap->globalEventProgram,
                285,
                *scenario.pEventRuntimeState,
                &scenario.party,
                &scenario.world);
            scenario.pEventRuntimeState->activeDecorationContext.reset();

            if (!executed)
            {
                failure = "campfire event 285 did not execute";
                return false;
            }

            scenario.world.applyEventRuntimeState();
            scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);

            const int gainedFood = scenario.party.food() - initialFood;

            if (gainedFood < 1 || gainedFood > 3)
            {
                failure = "campfire event granted " + std::to_string(gainedFood) + " food";
                return false;
            }

            if (scenario.pEventRuntimeState->decorVars[0] != 2)
            {
                failure = "campfire clear state was " + std::to_string(scenario.pEventRuntimeState->decorVars[0]);
                return false;
            }

            return true;
        }
    );

    runCase(
        "barrel_global_event_adds_permanent_stat_and_clears",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (scenario.pEventRuntimeState == nullptr)
            {
                failure = "missing event runtime state";
                return false;
            }

            Character *pActiveMember = scenario.party.activeMember();

            if (pActiveMember == nullptr)
            {
                failure = "missing active party member";
                return false;
            }

            const uint32_t initialIntellect = pActiveMember->intellect;

            EventRuntimeState::ActiveDecorationContext context = {};
            context.decorVarIndex = 2;
            context.baseEventId = 268;
            context.currentEventId = 272;
            context.eventCount = 8;
            context.hideWhenCleared = false;
            scenario.pEventRuntimeState->activeDecorationContext = context;

            const bool executed = scenario.eventRuntime.executeEventById(
                std::nullopt,
                selectedMap->globalEventProgram,
                272,
                *scenario.pEventRuntimeState,
                &scenario.party,
                &scenario.world);
            scenario.pEventRuntimeState->activeDecorationContext.reset();

            if (!executed)
            {
                failure = "barrel event 272 did not execute";
                return false;
            }

            scenario.world.applyEventRuntimeState();
            scenario.party.applyEventRuntimeState(*scenario.pEventRuntimeState);

            pActiveMember = scenario.party.activeMember();

            if (pActiveMember == nullptr)
            {
                failure = "missing active party member after event";
                return false;
            }

            if (pActiveMember->intellect != initialIntellect + 2)
            {
                failure = "barrel event changed intellect to " + std::to_string(pActiveMember->intellect);
                return false;
            }

            if (scenario.pEventRuntimeState->decorVars[2] != 0)
            {
                failure = "barrel clear state was " + std::to_string(scenario.pEventRuntimeState->decorVars[2]);
                return false;
            }

            return true;
        }
    );

    runCase(
        "event_meteor_shower_ground_impact_damages_party",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const float partyX = 9216.0f;
            const float partyY = -12848.0f;
            const float partyZ = 110.0f;
            const int initialHealth = scenario.party.totalHealth();

            if (!scenario.world.castEventSpell(
                    9,
                    10,
                    static_cast<uint32_t>(SkillMastery::Master),
                    19872,
                    -19824,
                    5084,
                    static_cast<int32_t>(partyX),
                    static_cast<int32_t>(partyY),
                    static_cast<int32_t>(partyZ)))
            {
                failure = "meteor shower cast failed";
                return false;
            }

            bool sawImpact = false;

            for (int step = 0; step < 8192; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                sawImpact = sawImpact || scenario.world.projectileImpactCount() > 0;
                applyPendingCombatEventsToScenarioParty(scenario);

                if (scenario.party.totalHealth() < initialHealth)
                {
                    return true;
                }
            }

            failure = !sawImpact ? "meteor shower never impacted" : "meteor shower impact never damaged party";
            return false;
        }
    );

    runCase(
        "dwi_world_actor_runtime_state",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pPeasant = scenario.world.mapActorState(5);
            const OutdoorWorldRuntime::MapActorState *pSergeant = scenario.world.mapActorState(53);

            if (pPeasant == nullptr || pSergeant == nullptr)
            {
                failure = "expected DWI actor runtime state is missing";
                return false;
            }

            if (pPeasant->monsterId != 1 || pPeasant->maxHp != 13 || pPeasant->hostileToParty)
            {
                failure = "unexpected peasant runtime state";
                return false;
            }

            if (pSergeant->monsterId != 5 || pSergeant->maxHp != 21 || pSergeant->hostileToParty)
            {
                failure = "unexpected sergeant runtime state";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_peasant_actor_5_does_not_flee_on_start",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(5);

            if (pBefore == nullptr)
            {
                failure = "actor 5 missing";
                return false;
            }

            if (pBefore->hostilityType != 0)
            {
                failure = "actor 5 did not start friendly to nearby actors";
                return false;
            }

            for (int step = 0; step < 8; ++step)
            {
                scenario.world.updateMapActors(
                    0.125f,
                    pBefore->preciseX + 20000.0f,
                    pBefore->preciseY + 20000.0f,
                    pBefore->preciseZ);
                const OutdoorWorldRuntime::MapActorState *pStep = scenario.world.mapActorState(5);

                if (pStep == nullptr)
                {
                    failure = "actor 5 disappeared during startup simulation";
                    return false;
                }

                if (pStep->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing)
                {
                    failure = "actor 5 entered fleeing state on map start";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "non_flying_actor_snaps_to_terrain",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map has no outdoor terrain";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            for (size_t actorIndex : {size_t(5), size_t(8)})
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr)
                {
                    failure = "expected grounded actor is missing";
                    return false;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats == nullptr)
                {
                    failure = "grounded actor stats missing";
                    return false;
                }

                if (pStats->canFly)
                {
                    failure = "grounded actor unexpectedly flies";
                    return false;
                }

                const int terrainZ = static_cast<int>(std::lround(sampleOutdoorSupportFloorHeight(
                    *selectedMap->outdoorMapData,
                    static_cast<float>(pActor->x),
                    static_cast<float>(pActor->y),
                    static_cast<float>(pActor->z))));

                if (pActor->z != terrainZ)
                {
                    failure = "non-flying actor is not grounded to terrain";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "dwi_world_spawn_runtime_state",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            bool foundFriendlyEncounterSpawn = false;
            bool foundHostileEncounterSpawn = false;

            for (size_t spawnIndex = 0; spawnIndex < scenario.world.spawnPointCount(); ++spawnIndex)
            {
                const OutdoorWorldRuntime::SpawnPointState *pSpawnState = scenario.world.spawnPointState(spawnIndex);

                if (pSpawnState == nullptr || pSpawnState->typeId != 3 || pSpawnState->encounterSlot == 0)
                {
                    continue;
                }

                if (pSpawnState->encounterSlot == 1 && !pSpawnState->hostileToParty)
                {
                    foundFriendlyEncounterSpawn = true;
                }

                if (pSpawnState->encounterSlot == 2 && pSpawnState->hostileToParty)
                {
                    foundHostileEncounterSpawn = true;
                }
            }

            if (!foundFriendlyEncounterSpawn)
            {
                failure = "missing friendly encounter spawn state";
                return false;
            }

            if (!foundHostileEncounterSpawn)
            {
                failure = "missing hostile encounter spawn state";
                return false;
            }

            return true;
        }
    );

    runCase(
        "spawn_points_materialize_on_first_outdoor_load",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map missing outdoor actor data";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t baseActorCount = selectedMap->outdoorMapDeltaData->actors.size();

            if (scenario.world.mapActorCount() <= baseActorCount)
            {
                failure = "spawn points did not materialize on first outdoor load";
                return false;
            }

            bool sawSpawnPointActor = false;

            for (size_t actorIndex = baseActorCount; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr)
                {
                    failure = "spawned actor state missing";
                    return false;
                }

                if (!pActor->spawnedAtRuntime || !pActor->fromSpawnPoint)
                {
                    failure = "first-load spawned actor metadata mismatch";
                    return false;
                }

                if (scenario.world.spawnPointState(pActor->spawnPointIndex) == nullptr)
                {
                    failure = "spawned actor does not reference a valid spawn point";
                    return false;
                }

                sawSpawnPointActor = true;
            }

            if (!sawSpawnPointActor)
            {
                failure = "no spawn point actors materialized on first outdoor load";
                return false;
            }

            return true;
        }
    );

    runCase(
        "treasure_spawn_points_materialize_world_items_on_first_outdoor_load",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map missing outdoor spawn data";
                return false;
            }

            RegressionScenario baseScenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, baseScenario))
            {
                failure = "base scenario init failed";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.map.treasureLevel = 5;
            modifiedMap.outdoorMapData = *selectedMap->outdoorMapData;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 0;

            OutdoorSpawn spawn = {};

            if (!modifiedMap.outdoorMapData->spawns.empty())
            {
                spawn = modifiedMap.outdoorMapData->spawns.front();
            }

            spawn.radius = 32;
            spawn.typeId = 2;
            spawn.index = 6;
            spawn.attributes = 0;
            spawn.group = 0;

            for (int spawnIndex = 0; spawnIndex < 16; ++spawnIndex)
            {
                OutdoorSpawn treasureSpawn = spawn;
                treasureSpawn.x += static_cast<int32_t>(spawnIndex * 64);
                treasureSpawn.index = 6;
                modifiedMap.outdoorMapData->spawns.push_back(treasureSpawn);
            }

            RegressionScenario modifiedScenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, modifiedScenario))
            {
                failure = "modified scenario init failed";
                return false;
            }

            if (modifiedScenario.world.worldItemCount() <= baseScenario.world.worldItemCount())
            {
                failure = "treasure spawn point did not materialize a runtime world item";
                return false;
            }

            return true;
        }
    );

    runCase(
        "spawn_points_remain_metadata_after_first_visit",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map missing outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t baseActorCount = selectedMap->outdoorMapDeltaData->actors.size();

            if (scenario.world.mapActorCount() != baseActorCount)
            {
                failure = "spawn points should remain metadata after first visit";
                return false;
            }

            size_t chosenSpawnIndex = static_cast<size_t>(-1);
            const OutdoorWorldRuntime::SpawnPointState *pChosenSpawn = nullptr;

            for (size_t spawnIndex = 0; spawnIndex < scenario.world.spawnPointCount(); ++spawnIndex)
            {
                const OutdoorWorldRuntime::SpawnPointState *pSpawn = scenario.world.spawnPointState(spawnIndex);

                if (pSpawn != nullptr
                    && pSpawn->typeId == 3
                    && pSpawn->encounterSlot > 0
                    && pSpawn->maxCount > 0)
                {
                    chosenSpawnIndex = spawnIndex;
                    pChosenSpawn = pSpawn;
                    break;
                }
            }

            if (pChosenSpawn == nullptr)
            {
                failure = "no executable monster spawn point found";
                return false;
            }

            if (!scenario.world.debugSpawnEncounterFromSpawnPoint(chosenSpawnIndex))
            {
                failure = "could not execute spawn point encounter";
                return false;
            }

            const size_t spawnedCount = scenario.world.mapActorCount() - baseActorCount;

            if (spawnedCount < static_cast<size_t>(std::max(0, pChosenSpawn->minCount))
                || spawnedCount > static_cast<size_t>(std::max(0, pChosenSpawn->maxCount)))
            {
                failure = "spawn point execution ignored configured min/max count";
                return false;
            }

            bool sawDifferentPosition = spawnedCount <= 1;

            for (size_t actorIndex = baseActorCount; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr)
                {
                    failure = "spawned actor state missing";
                    return false;
                }

                if (!pActor->spawnedAtRuntime || !pActor->fromSpawnPoint || pActor->spawnPointIndex != chosenSpawnIndex)
                {
                    failure = "spawned actor metadata mismatch";
                    return false;
                }

                if (actorIndex > baseActorCount)
                {
                    const OutdoorWorldRuntime::MapActorState *pFirstSpawnedActor =
                        scenario.world.mapActorState(baseActorCount);

                    if (pFirstSpawnedActor != nullptr
                        && (pActor->x != pFirstSpawnedActor->x || pActor->y != pFirstSpawnedActor->y))
                    {
                        sawDifferentPosition = true;
                    }
                }
            }

            if (!sawDifferentPosition)
            {
                failure = "multi-spawn encounter did not spread actor positions";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_actor_action_sprites_present_in_monster_data",
        [&](std::string &failure)
        {
            const MonsterEntry *pMonster = gameDataLoader.getMonsterTable().findById(5);

            if (pMonster == nullptr)
            {
                failure = "monster id 5 missing";
                return false;
            }

            if (pMonster->spriteNames[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::Standing)].empty())
            {
                failure = "standing sprite missing";
                return false;
            }

            if (pMonster->spriteNames[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::Walking)].empty())
            {
                failure = "walking sprite missing";
                return false;
            }

            if (pMonster->spriteNames[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::AttackRanged)].empty())
            {
                failure = "ranged attack sprite missing";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_does_not_engage_party",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            const int startX = pBefore->x;
            const int startY = pBefore->y;
            scenario.world.updateMapActors(3.0f, static_cast<float>(startX + 512), static_cast<float>(startY), pBefore->z);
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

            if (pAfter == nullptr)
            {
                failure = "actor 53 missing after update";
                return false;
            }

            if (pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                || pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                || pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing)
            {
                failure = "friendly actor should not engage the party";
                return false;
            }

            if (pAfter->hasDetectedParty)
            {
                failure = "friendly actor incorrectly detected the party as hostile";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_can_idle_wander",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            const int startX = pBefore->x;
            const int startY = pBefore->y;
            bool sawWandering = false;
            bool sawWalkingAnimation = false;

            for (int step = 0; step < 180; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 60.0f,
                    static_cast<float>(startX + 6000),
                    static_cast<float>(startY),
                    static_cast<float>(pBefore->z));

                const OutdoorWorldRuntime::MapActorState *pStepActor = scenario.world.mapActorState(53);

                if (pStepActor != nullptr)
                {
                    sawWandering = sawWandering || pStepActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
                    sawWalkingAnimation = sawWalkingAnimation
                        || pStepActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
                }
            }
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

            if (pAfter == nullptr)
            {
                failure = "actor 53 missing after update";
                return false;
            }

            if (pAfter->x == startX && pAfter->y == startY)
            {
                failure = "friendly actor did not idle-wander";
                return false;
            }

            if (!sawWandering)
            {
                failure = "friendly actor did not enter wandering state";
                return false;
            }

            if (!sawWalkingAnimation)
            {
                failure = "friendly actor did not enter walking animation";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_cycles_idle_and_walk",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const int startX = pBefore->x;
            const int startY = pBefore->y;
            bool sawStanding = pBefore->aiState == OutdoorWorldRuntime::ActorAiState::Standing;
            bool sawWandering = pBefore->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
            bool sawWalkingAnimation = pBefore->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
            bool sawBoredAnimation = pBefore->animation == OutdoorWorldRuntime::ActorAnimation::Bored;

            for (int step = 0; step < 360; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 60.0f,
                    static_cast<float>(startX + 6000),
                    static_cast<float>(startY),
                    static_cast<float>(pBefore->z));

                const OutdoorWorldRuntime::MapActorState *pStepActor = scenario.world.mapActorState(3);

                if (pStepActor != nullptr)
                {
                    sawStanding = sawStanding
                        || pStepActor->aiState == OutdoorWorldRuntime::ActorAiState::Standing;
                    sawWandering = sawWandering
                        || pStepActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
                    sawWalkingAnimation = sawWalkingAnimation
                        || pStepActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
                    sawBoredAnimation = sawBoredAnimation
                        || pStepActor->animation == OutdoorWorldRuntime::ActorAnimation::Bored;
                }
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after update";
                return false;
            }

            if (pAfter->x == startX && pAfter->y == startY)
            {
                failure = "actor 3 did not move";
                return false;
            }

            if (!sawStanding || !sawWandering || !sawWalkingAnimation)
            {
                failure = "actor 3 did not cycle through idle/walk states";
                return false;
            }

            if (sawBoredAnimation)
            {
                failure = "actor 3 unexpectedly entered bored animation during ordinary idle wander";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_accumulates_motion_under_tiny_deltas",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const int startX = pBefore->x;
            const int startY = pBefore->y;
            const float partyX = static_cast<float>(startX + 6000);
            const float partyY = static_cast<float>(startY);
            const float partyZ = static_cast<float>(pBefore->z);
            bool sawWandering = false;
            bool sawWalkingAnimation = false;

            for (int step = 0; step < 5000; ++step)
            {
                scenario.world.updateMapActors(0.0005f, partyX, partyY, partyZ);
                const OutdoorWorldRuntime::MapActorState *pStepActor = scenario.world.mapActorState(3);

                if (pStepActor != nullptr)
                {
                    sawWandering = sawWandering
                        || pStepActor->aiState == OutdoorWorldRuntime::ActorAiState::Wandering;
                    sawWalkingAnimation = sawWalkingAnimation
                        || pStepActor->animation == OutdoorWorldRuntime::ActorAnimation::Walking;
                }
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after tiny-delta simulation";
                return false;
            }

            if (pAfter->x == startX && pAfter->y == startY)
            {
                failure = "actor 3 did not accumulate movement under tiny deltas";
                return false;
            }

            if (!sawWandering || !sawWalkingAnimation)
            {
                failure = "actor 3 did not enter wandering/walking under tiny deltas";
                return false;
            }

            return true;
        }
    );

    runCase(
        "actor_3_runtime_preview_changes_while_wandering",
        [&](std::string &failure)
        {
            GameDataLoader fullMapLoader;

            if (!fullMapLoader.load(assetFileSystem)
                || !fullMapLoader.loadMapByFileName(assetFileSystem, mapFileName))
            {
                failure = "could not load full map assets for actor preview regression";
                return false;
            }

            const std::optional<MapAssetInfo> &fullSelectedMap = fullMapLoader.getSelectedMap();

            if (!fullSelectedMap || !fullSelectedMap->outdoorActorPreviewBillboardSet)
            {
                failure = "selected map missing actor previews";
                return false;
            }

            size_t billboardIndex = 0;
            const ActorPreviewBillboard *pBillboard =
                findCompanionActorBillboard(*fullSelectedMap->outdoorActorPreviewBillboardSet, 3, billboardIndex);

            if (pBillboard == nullptr)
            {
                failure = "actor 3 billboard missing";
                return false;
            }

            RegressionScenario scenario = {};

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const float cameraX = static_cast<float>(pBefore->x + 2048);
            const float cameraY = static_cast<float>(pBefore->y + 2048);
            std::vector<std::string> observedTextureKeys;

            for (int step = 0; step < 360; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 60.0f,
                    static_cast<float>(pBefore->x + 6000),
                    static_cast<float>(pBefore->y),
                    static_cast<float>(pBefore->z));

                const OutdoorWorldRuntime::MapActorState *pStepActor = scenario.world.mapActorState(3);

                if (pStepActor == nullptr)
                {
                    failure = "actor 3 vanished during runtime preview test";
                    return false;
                }

                const std::string textureKey = resolveRuntimeActorTextureKey(
                    *fullSelectedMap->outdoorActorPreviewBillboardSet,
                    *pBillboard,
                    *pStepActor,
                    cameraX,
                    cameraY);

                if (!textureKey.empty()
                    && std::find(observedTextureKeys.begin(), observedTextureKeys.end(), textureKey)
                        == observedTextureKeys.end())
                {
                    observedTextureKeys.push_back(textureKey);
                }
            }

            if (observedTextureKeys.size() < 2)
            {
                failure = "actor 3 runtime preview never changed texture/frame selection";
                return false;
            }

            return true;
        }
    );

    runCase(
        "actor_51_stays_on_ship_support",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            if (selectedMap->outdoorMapDeltaData->actors.size() <= 51)
            {
                failure = "actor 51 missing from map delta";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const MapDeltaActor &rawActor = selectedMap->outdoorMapDeltaData->actors[51];
            const float worldX = static_cast<float>(rawActor.x);
            const float worldY = static_cast<float>(rawActor.y);
            const float terrainHeight = sampleOutdoorTerrainHeight(*selectedMap->outdoorMapData, worldX, worldY);
            const float placementHeight = sampleOutdoorPlacementFloorHeight(
                *selectedMap->outdoorMapData,
                worldX,
                worldY,
                static_cast<float>(rawActor.z));
            const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(51);

            if (pActor == nullptr)
            {
                failure = "actor 51 missing";
                return false;
            }

            if (placementHeight <= terrainHeight + 32.0f)
            {
                failure = "actor 51 support floor was not above terrain";
                return false;
            }

            if (std::fabs(static_cast<float>(pActor->z) - placementHeight) > 2.0f)
            {
                failure = "actor 51 runtime z does not match resolved support floor";
                return false;
            }

            return true;
        }
    );

    runCase(
        "actor_51_movement_preserves_ship_floor",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(51);

            if (pBefore == nullptr)
            {
                failure = "actor 51 missing";
                return false;
            }

            const float startZ = pBefore->preciseZ;

            for (int step = 0; step < 300; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 60.0f,
                    static_cast<float>(pBefore->x + 20000),
                    static_cast<float>(pBefore->y + 20000),
                    static_cast<float>(pBefore->z));
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(51);

            if (pAfter == nullptr)
            {
                failure = "actor 51 missing after update";
                return false;
            }

            if (std::fabs(pAfter->preciseZ - startZ) > 2.0f)
            {
                failure = "actor 51 fell off ship support while moving";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_stands_and_faces_party_on_contact",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const float partyX = static_cast<float>(pBefore->x + 32);
            const float partyY = static_cast<float>(pBefore->y + 24);
            const float partyZ = static_cast<float>(pBefore->z);
            scenario.world.updateMapActors(0.25f, static_cast<float>(pBefore->x + 20000), static_cast<float>(pBefore->y + 20000), partyZ);
            scenario.world.notifyPartyContactWithMapActor(3, partyX, partyY, partyZ);
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after update";
                return false;
            }

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Standing)
            {
                failure = "actor 3 did not stand on party contact";
                return false;
            }

            if (pAfter->animation != OutdoorWorldRuntime::ActorAnimation::Standing)
            {
                failure = "actor 3 did not use standing animation on party contact";
                return false;
            }

            if (std::abs(pAfter->velocityX) > 0.01f || std::abs(pAfter->velocityY) > 0.01f)
            {
                failure = "actor 3 kept moving on party contact";
                return false;
            }

            const float expectedYaw = std::atan2(partyY - pAfter->preciseY, partyX - pAfter->preciseX);

            if (angleDistanceRadians(pAfter->yawRadians, expectedYaw) > 0.35f)
            {
                failure = "actor 3 did not face the party on contact";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_stops_wandering_when_party_is_near",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const float partyX = pBefore->preciseX + 70.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            scenario.world.updateMapActors(0.25f, partyX, partyY, partyZ);
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after update";
                return false;
            }

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Standing)
            {
                failure = "actor 3 did not stand when party was near";
                return false;
            }

            if (pAfter->animation != OutdoorWorldRuntime::ActorAnimation::Standing)
            {
                failure = "actor 3 did not use standing animation when party was near";
                return false;
            }

            if (std::abs(pAfter->velocityX) > 0.01f || std::abs(pAfter->velocityY) > 0.01f)
            {
                failure = "actor 3 kept moving when party was near";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_causes_damage_and_hostility",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            const int beforeHp = pBefore->currentHp;

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    2,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

            if (pAfter == nullptr)
            {
                failure = "actor 3 missing after attack";
                return false;
            }

            if (!pAfter->hostileToParty)
            {
                failure = "actor 3 did not become hostile";
                return false;
            }

            if (pAfter->currentHp != std::max(0, beforeHp - 2))
            {
                failure = "actor 3 did not take the expected damage";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_stunned_hit_reaction_does_not_restart_on_second_hit",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData || selectedMap->outdoorMapDeltaData->actors.size() <= 53)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            modifiedMap.outdoorMapDeltaData->actors[3].monsterInfoId =
                selectedMap->outdoorMapDeltaData->actors[53].monsterInfoId;
            modifiedMap.outdoorMapDeltaData->actors[3].monsterId =
                selectedMap->outdoorMapDeltaData->actors[53].monsterId;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    1,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "first party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfterFirstHit = scenario.world.mapActorState(3);

            if (pAfterFirstHit == nullptr)
            {
                failure = "actor 3 missing after first hit";
                return false;
            }

            if (pAfterFirstHit->aiState != OutdoorWorldRuntime::ActorAiState::Stunned
                || pAfterFirstHit->animation != OutdoorWorldRuntime::ActorAnimation::GotHit)
            {
                failure = "actor 3 did not enter stunned hit reaction";
                return false;
            }

            scenario.world.updateMapActors(
                1.0f / 128.0f,
                pAfterFirstHit->preciseX + 64.0f,
                pAfterFirstHit->preciseY,
                pAfterFirstHit->preciseZ);

            const OutdoorWorldRuntime::MapActorState *pDuringReaction = scenario.world.mapActorState(3);

            if (pDuringReaction == nullptr)
            {
                failure = "actor 3 missing during hit reaction";
                return false;
            }

            const float animationTicksBeforeSecondHit = pDuringReaction->animationTimeTicks;
            const float actionSecondsBeforeSecondHit = pDuringReaction->actionSeconds;

            if (animationTicksBeforeSecondHit <= 0.0f)
            {
                failure = "actor 3 hit reaction animation did not advance";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    1,
                    pDuringReaction->preciseX + 64.0f,
                    pDuringReaction->preciseY,
                    pDuringReaction->preciseZ))
            {
                failure = "second party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfterSecondHit = scenario.world.mapActorState(3);

            if (pAfterSecondHit == nullptr)
            {
                failure = "actor 3 missing after second hit";
                return false;
            }

            if (pAfterSecondHit->aiState != OutdoorWorldRuntime::ActorAiState::Stunned
                || pAfterSecondHit->animation != OutdoorWorldRuntime::ActorAnimation::GotHit)
            {
                failure = "actor 3 left stunned hit reaction after second hit";
                return false;
            }

            if (std::abs(pAfterSecondHit->animationTimeTicks - animationTicksBeforeSecondHit) > 0.001f)
            {
                failure = "actor 3 hit reaction animation restarted on second hit";
                return false;
            }

            if (pAfterSecondHit->actionSeconds > actionSecondsBeforeSecondHit + 0.001f)
            {
                failure = "actor 3 hit reaction duration increased on second hit";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_lethal_damage_enters_dying_before_dead",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    pBefore->currentHp,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "lethal party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfterLethalHit = scenario.world.mapActorState(3);

            if (pAfterLethalHit == nullptr)
            {
                failure = "actor 3 missing after lethal hit";
                return false;
            }

            if (pAfterLethalHit->isDead)
            {
                failure = "actor 3 became dead immediately without dying state";
                return false;
            }

            if (pAfterLethalHit->aiState != OutdoorWorldRuntime::ActorAiState::Dying
                || pAfterLethalHit->animation != OutdoorWorldRuntime::ActorAnimation::Dying)
            {
                failure = "actor 3 did not enter dying state";
                return false;
            }

            if (pAfterLethalHit->actionSeconds <= 0.0f)
            {
                failure = "actor 3 dying state has no duration";
                return false;
            }

            bool sawDeadState = false;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 128.0f,
                    pAfterLethalHit->preciseX + 64.0f,
                    pAfterLethalHit->preciseY,
                    pAfterLethalHit->preciseZ);

                const OutdoorWorldRuntime::MapActorState *pAfterUpdate = scenario.world.mapActorState(3);

                if (pAfterUpdate == nullptr)
                {
                    failure = "actor 3 missing during dying update";
                    return false;
                }

                if (pAfterUpdate->isDead)
                {
                    sawDeadState = true;

                    if (pAfterUpdate->aiState != OutdoorWorldRuntime::ActorAiState::Dead
                        || pAfterUpdate->animation != OutdoorWorldRuntime::ActorAnimation::Dead)
                    {
                        failure = "actor 3 dead state animation/state mismatch";
                        return false;
                    }

                    break;
                }
            }

            if (!sawDeadState)
            {
                failure = "actor 3 never transitioned from dying to dead";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_lethal_damage_stays_deadly_while_inactive",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(3);

            if (pBefore == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    pBefore->currentHp,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "lethal party attack did not apply";
                return false;
            }

            bool sawDeadState = false;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 128.0f,
                    pBefore->preciseX + 20000.0f,
                    pBefore->preciseY + 20000.0f,
                    pBefore->preciseZ);

                const OutdoorWorldRuntime::MapActorState *pAfterUpdate = scenario.world.mapActorState(3);

                if (pAfterUpdate == nullptr)
                {
                    failure = "actor 3 missing during inactive dying update";
                    return false;
                }

                if (pAfterUpdate->currentHp != 0)
                {
                    failure = "actor 3 regained hp after lethal hit";
                    return false;
                }

                if (!pAfterUpdate->isDead)
                {
                    if (pAfterUpdate->aiState != OutdoorWorldRuntime::ActorAiState::Dying
                        || pAfterUpdate->animation != OutdoorWorldRuntime::ActorAnimation::Dying)
                    {
                        failure = "inactive lethal actor left dying state before death";
                        return false;
                    }

                    if (std::abs(pAfterUpdate->velocityX) > 0.01f
                        || std::abs(pAfterUpdate->velocityY) > 0.01f
                        || std::abs(pAfterUpdate->velocityZ) > 0.01f)
                    {
                        failure = "inactive lethal actor kept moving";
                        return false;
                    }

                    continue;
                }

                if (pAfterUpdate->aiState != OutdoorWorldRuntime::ActorAiState::Dead
                    || pAfterUpdate->animation != OutdoorWorldRuntime::ActorAnimation::Dead)
                {
                    failure = "inactive lethal actor dead state mismatch";
                    return false;
                }

                sawDeadState = true;
                break;
            }

            if (!sawDeadState)
            {
                failure = "inactive lethal actor never reached dead state";
                return false;
            }

            for (int step = 0; step < 64; ++step)
            {
                scenario.world.updateMapActors(
                    1.0f / 128.0f,
                    pBefore->preciseX + 20000.0f,
                    pBefore->preciseY + 20000.0f,
                    pBefore->preciseZ);

                const OutdoorWorldRuntime::MapActorState *pAfterDeadInactiveUpdate =
                    scenario.world.mapActorState(3);

                if (pAfterDeadInactiveUpdate == nullptr)
                {
                    failure = "actor 3 missing after inactive dead update";
                    return false;
                }

                if (!pAfterDeadInactiveUpdate->isDead
                    || pAfterDeadInactiveUpdate->aiState != OutdoorWorldRuntime::ActorAiState::Dead
                    || pAfterDeadInactiveUpdate->animation != OutdoorWorldRuntime::ActorAnimation::Dead)
                {
                    failure = "inactive dead actor did not keep dead state and animation";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_aggros_nearby_lizard_guard",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pVictim = scenario.world.mapActorState(3);

            if (pVictim == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            size_t guardActorIndex = static_cast<size_t>(-1);

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || pActor->isDead || pActor->hostileToParty)
                {
                    continue;
                }

                if (!gameDataLoader.getMonsterTable().isLikelySameFaction(pVictim->monsterId, pActor->monsterId))
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats == nullptr || pStats->aiType == MonsterTable::MonsterAiType::Wimp)
                {
                    continue;
                }

                const float deltaX = pActor->preciseX - pVictim->preciseX;
                const float deltaY = pActor->preciseY - pVictim->preciseY;
                const float deltaZ = pActor->preciseZ - pVictim->preciseZ;
                const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);

                if (distance <= 4096.0f)
                {
                    guardActorIndex = actorIndex;
                    break;
                }
            }

            if (guardActorIndex == static_cast<size_t>(-1))
            {
                failure = "no nearby same-faction non-wimp actor found";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    2,
                    pVictim->preciseX + 64.0f,
                    pVictim->preciseY,
                    pVictim->preciseZ))
            {
                failure = "party attack did not apply";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pGuard = scenario.world.mapActorState(guardActorIndex);

            if (pGuard == nullptr || !pGuard->hostileToParty)
            {
                failure = "nearby same-faction guard did not become hostile";
                return false;
            }

            bool sawEngageState = false;

            for (size_t stepIndex = 0; stepIndex < 256; ++stepIndex)
            {
                scenario.world.updateMapActors(
                    1.0f / 128.0f,
                    pVictim->preciseX + 64.0f,
                    pVictim->preciseY,
                    pVictim->preciseZ);

                pGuard = scenario.world.mapActorState(guardActorIndex);

                if (pGuard != nullptr
                    && (pGuard->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                        || pGuard->aiState == OutdoorWorldRuntime::ActorAiState::Attacking))
                {
                    sawEngageState = true;
                    break;
                }
            }

            if (!sawEngageState)
            {
                failure = "nearby same-faction guard never engaged the party";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_actor_3_causes_wimp_flee",
        [&](std::string &failure)
        {
            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pVictim = scenario.world.mapActorState(3);

            if (pVictim == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    3,
                    2,
                    pVictim->preciseX + 64.0f,
                    pVictim->preciseY,
                    pVictim->preciseZ))
            {
                failure = "party attack did not apply";
                return false;
            }

            bool sawFleeing = false;

            for (size_t stepIndex = 0; stepIndex < 64; ++stepIndex)
            {
                scenario.world.updateMapActors(
                    1.0f / 128.0f,
                    pVictim->preciseX + 64.0f,
                    pVictim->preciseY,
                    pVictim->preciseZ);

                const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(3);

                if (pAfter != nullptr && pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing)
                {
                    sawFleeing = true;
                    break;
                }
            }

            if (!sawFleeing)
            {
                failure = "attacked wimp actor never entered fleeing state";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_attack_on_hostile_actor_61_still_applies_damage",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(61);

            if (pBefore == nullptr)
            {
                failure = "actor 61 missing";
                return false;
            }

            if (!pBefore->hostileToParty)
            {
                failure = "actor 61 is not hostile in baseline state";
                return false;
            }

            const int beforeHp = pBefore->currentHp;

            if (!scenario.world.applyPartyAttackToMapActor(
                    61,
                    3,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "party attack did not apply to hostile actor";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(61);

            if (pAfter == nullptr || pAfter->currentHp != std::max(0, beforeHp - 3))
            {
                failure = "hostile actor did not take expected damage";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_movement_ignores_friendly_actor_3_collision",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pFriendlyActor = scenario.world.mapActorState(3);

            if (pFriendlyActor == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            OutdoorMovementController movementController(
                *selectedMap->outdoorMapData,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                std::nullopt,
                selectedMap->outdoorSpriteObjectCollisionSet);

            std::vector<OutdoorActorCollision> hostileColliders;

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr
                    || pActor->isDead
                    || pActor->isInvisible
                    || !pActor->hostileToParty
                    || pActor->radius == 0
                    || pActor->height == 0)
                {
                    continue;
                }

                OutdoorActorCollision collider = {};
                collider.sourceIndex = actorIndex;
                collider.source = OutdoorActorCollisionSource::MapDelta;
                collider.radius = pActor->radius;
                collider.height = pActor->height;
                collider.worldX = pActor->x;
                collider.worldY = pActor->y;
                collider.worldZ = pActor->z;
                collider.group = pActor->group;
                collider.name = pActor->displayName;
                hostileColliders.push_back(std::move(collider));
            }

            movementController.setActorColliders(hostileColliders);

            OutdoorMoveState state = movementController.initializeState(
                pFriendlyActor->preciseX - 160.0f,
                pFriendlyActor->preciseY,
                pFriendlyActor->preciseZ);
            std::vector<size_t> contactedActorIndices;
            const OutdoorMoveState resolved = movementController.resolveMove(
                state,
                768.0f,
                0.0f,
                0.0f,
                false,
                false,
                false,
                false,
                false,
                0.0f,
                0.0f,
                4000.0f,
                0.5f,
                &contactedActorIndices);

            if (!contactedActorIndices.empty())
            {
                failure = "friendly actor produced a party collision contact";
                return false;
            }

            if (resolved.x <= pFriendlyActor->preciseX)
            {
                failure = "party did not move through friendly actor";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_movement_collides_with_hostile_actor_61",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pHostileActor = scenario.world.mapActorState(61);

            if (pHostileActor == nullptr)
            {
                failure = "actor 61 missing";
                return false;
            }

            if (!pHostileActor->hostileToParty)
            {
                failure = "actor 61 is not hostile in baseline state";
                return false;
            }

            OutdoorMovementController movementController(
                *selectedMap->outdoorMapData,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                std::nullopt,
                selectedMap->outdoorSpriteObjectCollisionSet);

            OutdoorActorCollision collider = {};
            collider.sourceIndex = 61;
            collider.source = OutdoorActorCollisionSource::MapDelta;
            collider.radius = pHostileActor->radius;
            collider.height = pHostileActor->height;
            collider.worldX = pHostileActor->x;
            collider.worldY = pHostileActor->y;
            collider.worldZ = pHostileActor->z;
            collider.group = pHostileActor->group;
            collider.name = pHostileActor->displayName;
            movementController.setActorColliders({collider});

            OutdoorMoveState state = movementController.initializeState(
                pHostileActor->preciseX - 160.0f,
                pHostileActor->preciseY,
                pHostileActor->preciseZ);
            std::vector<size_t> contactedActorIndices;
            const OutdoorMoveState resolved = movementController.resolveMove(
                state,
                768.0f,
                0.0f,
                0.0f,
                false,
                false,
                false,
                false,
                false,
                0.0f,
                0.0f,
                4000.0f,
                0.5f,
                &contactedActorIndices);

            if (contactedActorIndices.empty())
            {
                failure = "hostile actor did not produce a party collision contact";
                return false;
            }

            if (resolved.x > pHostileActor->preciseX - 16.0f)
            {
                failure = "party moved through hostile actor";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_is_pushed_out_of_actor_overlap",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            OutdoorMovementController movementController(
                *selectedMap->outdoorMapData,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                std::nullopt,
                selectedMap->outdoorSpriteObjectCollisionSet);

            OutdoorMoveState state = movementController.initializeState(0.0f, 0.0f, 0.0f);
            OutdoorActorCollision blocker = {};
            blocker.radius = 64;
            blocker.height = 160;
            blocker.worldX = static_cast<int>(std::lround(state.x));
            blocker.worldY = static_cast<int>(std::lround(state.y));
            blocker.worldZ = static_cast<int>(std::floor(state.footZ));
            blocker.name = "test actor";
            movementController.setActorColliders({blocker});

            const OutdoorMoveState resolved = movementController.resolveMove(
                state,
                0.0f,
                0.0f,
                0.0f,
                false,
                false,
                false,
                false,
                false,
                0.0f,
                0.0f,
                4000.0f,
                1.0f / 60.0f);

            const float deltaX = resolved.x - static_cast<float>(blocker.worldX);
            const float deltaY = resolved.y - static_cast<float>(blocker.worldY);
            const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY);

            if (distance < 101.0f)
            {
                failure = "party remained inside actor overlap after collision resolution";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_movement_reports_actor_contact",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            OutdoorMovementController movementController(
                *selectedMap->outdoorMapData,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                std::nullopt,
                selectedMap->outdoorSpriteObjectCollisionSet);

            OutdoorMoveState state = movementController.initializeState(0.0f, 0.0f, 0.0f);
            OutdoorActorCollision blocker = {};
            blocker.sourceIndex = 123;
            blocker.radius = 64;
            blocker.height = 160;
            blocker.worldX = static_cast<int>(std::lround(state.x + 90.0f));
            blocker.worldY = static_cast<int>(std::lround(state.y));
            blocker.worldZ = static_cast<int>(std::floor(state.footZ));
            blocker.name = "contact test actor";
            movementController.setActorColliders({blocker});

            std::vector<size_t> contactedActorIndices;
            movementController.resolveMove(
                state,
                384.0f,
                0.0f,
                0.0f,
                false,
                false,
                false,
                false,
                false,
                0.0f,
                0.0f,
                4000.0f,
                1.0f / 60.0f,
                &contactedActorIndices);

            if (contactedActorIndices.empty())
            {
                failure = "movement controller did not report actor contact";
                return false;
            }

            if (contactedActorIndices.front() != 123)
            {
                failure = "movement controller reported wrong actor contact index";
                return false;
            }

            return true;
        }
    );

    runCase(
        "friendly_actor_3_preview_palette_and_frame_cycle",
        [&](std::string &failure)
        {
            GameDataLoader fullMapLoader;

            if (!fullMapLoader.loadForHeadlessGameplay(assetFileSystem))
            {
                failure = "full preview loader init failed";
                return false;
            }

            if (!fullMapLoader.loadMapByFileName(assetFileSystem, "out01.odm"))
            {
                failure = "full preview map load failed";
                return false;
            }

            const std::optional<MapAssetInfo> &previewSelectedMap = fullMapLoader.getSelectedMap();

            if (!previewSelectedMap || !previewSelectedMap->outdoorActorPreviewBillboardSet)
            {
                failure = "selected map missing actor previews";
                return false;
            }

            size_t billboardIndex = 0;
            const ActorPreviewBillboardSet &billboardSet = *previewSelectedMap->outdoorActorPreviewBillboardSet;
            const ActorPreviewBillboard *pBillboard = findCompanionActorBillboard(billboardSet, 3, billboardIndex);

            if (pBillboard == nullptr)
            {
                failure = "actor 3 billboard missing";
                return false;
            }

            const ActorPreviewAnimationStats animationStats =
                analyzeActorPreviewAnimation(billboardSet, *pBillboard);

            if (animationStats.sampleCount == 0)
            {
                failure = "actor 3 preview produced no samples";
                return false;
            }

            if (animationStats.missingTextureSampleCount != 0)
            {
                failure = "actor 3 preview has missing textures";
                return false;
            }

            if (animationStats.greenDominantSampleCount <= animationStats.magentaDominantSampleCount)
            {
                failure = "actor 3 preview colors skew magenta instead of green";
                return false;
            }

            if (animationStats.distinctWalkingFrameCount < 2)
            {
                failure = "actor 3 walking preview does not cycle frames";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_pursues_party",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                if (hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pActor) >= 2000.0f)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float acquisitionRange = hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pBefore);
            const float partyDistance = std::min(2000.0f, acquisitionRange * 0.75f);
            const float partyX = static_cast<float>(pBefore->x) + partyDistance;
            const float partyY = static_cast<float>(pBefore->y);
            const float distanceBefore = std::abs(partyX - static_cast<float>(pBefore->x));
            scenario.world.updateMapActors(1.0f, partyX, partyY, static_cast<float>(pBefore->z));
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);
            const float distanceAfter = std::abs(partyX - static_cast<float>(pAfter->x));

            if (distanceAfter >= distanceBefore)
            {
                failure = "hostile actor did not move toward the party";
                return false;
            }

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Pursuing)
            {
                failure = "hostile actor did not enter pursuing state";
                return false;
            }

            if (pAfter->animation != OutdoorWorldRuntime::ActorAnimation::Walking)
            {
                failure = "hostile actor did not enter walking animation";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_uses_long_party_acquisition_despite_short_relation",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->locationInfo.lastRespawnDay = 1;
            const MapDeltaActor quietLandActor = modifiedMap.outdoorMapDeltaData->actors[3];
            modifiedMap.outdoorMapDeltaData->actors[53].monsterInfoId = 184;
            modifiedMap.outdoorMapDeltaData->actors[53].monsterId = 184;
            modifiedMap.outdoorMapDeltaData->actors[53].attributes = 0;
            modifiedMap.outdoorMapDeltaData->actors[53].x = quietLandActor.x;
            modifiedMap.outdoorMapDeltaData->actors[53].y = quietLandActor.y;
            modifiedMap.outdoorMapDeltaData->actors[53].z = quietLandActor.z;

            for (size_t actorIndex = 0; actorIndex < modifiedMap.outdoorMapDeltaData->actors.size(); ++actorIndex)
            {
                if (actorIndex == 53)
                {
                    continue;
                }

                MapDeltaActor &otherActor = modifiedMap.outdoorMapDeltaData->actors[actorIndex];
                otherActor.x = quietLandActor.x + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.y = quietLandActor.y + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.z = quietLandActor.z;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "synthetic actor 53 missing";
                return false;
            }

            if (std::abs(hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pBefore) - 10240.0f) > 0.1f)
            {
                failure = "synthetic actor 53 did not resolve a long party acquisition range";
                return false;
            }

            const float partyX = pBefore->preciseX + 2000.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            scenario.world.updateMapActors(1.0f, partyX, partyY, partyZ);
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

            if (pAfter == nullptr)
            {
                failure = "synthetic actor 53 disappeared";
                return false;
            }

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Pursuing
                && pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile actor did not engage the party despite long acquisition range";
                return false;
            }

            return true;
        }
    );

    runCase(
        "long_hostile_actor_pair_engages_at_2048",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            MapDeltaActor &leftActor = modifiedMap.outdoorMapDeltaData->actors[3];
            MapDeltaActor &rightActor = modifiedMap.outdoorMapDeltaData->actors[53];
            leftActor.monsterInfoId = 4;
            leftActor.monsterId = 4;
            rightActor.monsterInfoId = 181;
            rightActor.monsterId = 181;
            leftActor.x = -9216;
            leftActor.y = -12848;
            leftActor.z = 110;
            rightActor.x = leftActor.x + 2048;
            rightActor.y = leftActor.y;
            rightActor.z = leftActor.z;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pLeftBefore = scenario.world.mapActorState(3);
            const OutdoorWorldRuntime::MapActorState *pRightBefore = scenario.world.mapActorState(53);

            if (pLeftBefore == nullptr || pRightBefore == nullptr)
            {
                failure = "synthetic hostile actor pair missing";
                return false;
            }

            if (gameDataLoader.getMonsterTable().getRelationBetweenMonsters(
                    pLeftBefore->monsterId,
                    pRightBefore->monsterId) != 4)
            {
                failure = "synthetic hostile actor pair did not resolve a long hostility relation";
                return false;
            }

            const float partyX = (pLeftBefore->preciseX + pRightBefore->preciseX) * 0.5f;
            const float partyY = pLeftBefore->preciseY;
            const float partyZ = pLeftBefore->preciseZ;
            bool sawEngagement = false;

            for (int step = 0; step < 128; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                const OutdoorWorldRuntime::MapActorState *pLeftAfter = scenario.world.mapActorState(3);
                const OutdoorWorldRuntime::MapActorState *pRightAfter = scenario.world.mapActorState(53);

                if (pLeftAfter == nullptr || pRightAfter == nullptr)
                {
                    failure = "synthetic hostile actor pair disappeared";
                    return false;
                }

                sawEngagement = sawEngagement
                    || pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking;

                if (sawEngagement)
                {
                    return true;
                }
            }

            failure = "long-hostility actor pair never engaged from 2048 units apart";
            return false;
        }
    );

    runCase(
        "hostile_melee_actor_uses_side_pursuit_when_far",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary
                    && hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pActor) >= 2500.0f)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float partyX = static_cast<float>(pBefore->x + 2500);
            const float partyY = static_cast<float>(pBefore->y);
            scenario.world.updateMapActors(0.1f, partyX, partyY, static_cast<float>(pBefore->z));
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Pursuing)
            {
                failure = "hostile melee actor did not enter pursuing state";
                return false;
            }

            if (std::abs(pAfter->moveDirectionY) < 0.1f)
            {
                failure = "hostile melee actor did not choose a side-biased pursuit direction";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_melee_actor_far_pursuit_accumulates_motion",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary
                    && hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pActor) >= 2500.0f)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float startX = pBefore->preciseX;
            const float startY = pBefore->preciseY;
            const float partyX = startX + 2500.0f;
            const float partyY = startY;
            bool sawPursuing = false;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, pBefore->preciseZ);
                const OutdoorWorldRuntime::MapActorState *pStep = scenario.world.mapActorState(hostileActorIndex);

                if (pStep != nullptr && pStep->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing)
                {
                    sawPursuing = true;
                }
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);

            if (pAfter == nullptr)
            {
                failure = "hostile melee actor disappeared";
                return false;
            }

            if (!sawPursuing)
            {
                failure = "hostile melee actor never entered pursuing state";
                return false;
            }

            if (std::abs(pAfter->preciseX - startX) < 8.0f && std::abs(pAfter->preciseY - startY) < 8.0f)
            {
                failure = "hostile melee actor did not accumulate movement during far pursuit";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_melee_actor_uses_direct_pursuit_when_close",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary
                    && hostilePartyAcquisitionRange(gameDataLoader.getMonsterTable(), *pActor) >= 700.0f)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float partyX = static_cast<float>(pBefore->x + 700);
            const float partyY = static_cast<float>(pBefore->y);
            scenario.world.updateMapActors(0.1f, partyX, partyY, static_cast<float>(pBefore->z));
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Pursuing)
            {
                failure = "hostile melee actor did not enter pursuing state";
                return false;
            }

            if (std::abs(pAfter->moveDirectionY) >= 0.1f)
            {
                failure = "hostile melee actor did not choose direct pursuit when close";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_51_respects_nearby_blocking_face",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(51);

            if (pActor == nullptr)
            {
                failure = "actor 51 missing";
                return false;
            }

            std::vector<OutdoorFaceGeometryData> faces;

            for (size_t bModelIndex = 0; bModelIndex < selectedMap->outdoorMapData->bmodels.size(); ++bModelIndex)
            {
                const OutdoorBModel &bModel = selectedMap->outdoorMapData->bmodels[bModelIndex];

                for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
                {
                    OutdoorFaceGeometryData geometry = {};

                    if (buildOutdoorFaceGeometry(bModel, bModelIndex, bModel.faces[faceIndex], faceIndex, geometry))
                    {
                        faces.push_back(std::move(geometry));
                    }
                }
            }

            const OutdoorFaceGeometryData *pBlockingFace = nullptr;
            float bestDistance = std::numeric_limits<float>::max();
            const bx::Vec3 actorCenter = {
                pActor->preciseX,
                pActor->preciseY,
                pActor->preciseZ + static_cast<float>(pActor->height) * 0.5f
            };

            for (const OutdoorFaceGeometryData &face : faces)
            {
                if (face.isWalkable || !face.hasPlane)
                {
                    continue;
                }

                const float signedDistance = std::abs(signedDistanceToOutdoorFace(face, actorCenter));

                if (signedDistance >= bestDistance || signedDistance > 256.0f)
                {
                    continue;
                }

                const bx::Vec3 projectedPoint = {
                    actorCenter.x - face.normal.x * signedDistanceToOutdoorFace(face, actorCenter),
                    actorCenter.y - face.normal.y * signedDistanceToOutdoorFace(face, actorCenter),
                    actorCenter.z - face.normal.z * signedDistanceToOutdoorFace(face, actorCenter)
                };

                if (!isPointInsideOutdoorPolygonProjected(projectedPoint, face.vertices, face.normal))
                {
                    continue;
                }

                bestDistance = signedDistance;
                pBlockingFace = &face;
            }

            if (pBlockingFace == nullptr)
            {
                failure = "no nearby blocking face found for actor 51";
                return false;
            }

            const float initialSignedDistance = signedDistanceToOutdoorFace(*pBlockingFace, actorCenter);
            const float pushSign = initialSignedDistance >= 0.0f ? -1.0f : 1.0f;
            const float partyX = pActor->preciseX + pBlockingFace->normal.x * pushSign * 700.0f;
            const float partyY = pActor->preciseY + pBlockingFace->normal.y * pushSign * 700.0f;
            const float partyZ = pActor->preciseZ;

            for (int step = 0; step < 600; ++step)
            {
                scenario.world.updateMapActors(1.0f / 60.0f, partyX, partyY, partyZ);
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(51);

            if (pAfter == nullptr)
            {
                failure = "actor 51 missing after update";
                return false;
            }

            const bx::Vec3 afterCenter = {
                pAfter->preciseX,
                pAfter->preciseY,
                pAfter->preciseZ + static_cast<float>(pAfter->height) * 0.5f
            };
            const float afterSignedDistance = signedDistanceToOutdoorFace(*pBlockingFace, afterCenter);

            if ((initialSignedDistance > 0.0f && afterSignedDistance < -40.0f)
                || (initialSignedDistance < 0.0f && afterSignedDistance > 40.0f))
            {
                failure = "actor 51 crossed a nearby blocking face";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_51_ignores_hostile_actor_across_blocking_face",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(51);

            if (pActor == nullptr)
            {
                failure = "actor 51 missing";
                return false;
            }

            const float actorZ = pActor->preciseZ;

            std::vector<OutdoorFaceGeometryData> faces;

            for (size_t bModelIndex = 0; bModelIndex < selectedMap->outdoorMapData->bmodels.size(); ++bModelIndex)
            {
                const OutdoorBModel &bModel = selectedMap->outdoorMapData->bmodels[bModelIndex];

                for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
                {
                    OutdoorFaceGeometryData geometry = {};

                    if (buildOutdoorFaceGeometry(bModel, bModelIndex, bModel.faces[faceIndex], faceIndex, geometry))
                    {
                        faces.push_back(std::move(geometry));
                    }
                }
            }

            const OutdoorFaceGeometryData *pBlockingFace = nullptr;
            float bestDistance = std::numeric_limits<float>::max();
            const bx::Vec3 actorCenter = {
                pActor->preciseX,
                pActor->preciseY,
                pActor->preciseZ + static_cast<float>(pActor->height) * 0.5f
            };

            for (const OutdoorFaceGeometryData &face : faces)
            {
                if (face.isWalkable || !face.hasPlane)
                {
                    continue;
                }

                const float signedDistance = std::abs(signedDistanceToOutdoorFace(face, actorCenter));

                if (signedDistance >= bestDistance || signedDistance > 256.0f)
                {
                    continue;
                }

                const bx::Vec3 projectedPoint = {
                    actorCenter.x - face.normal.x * signedDistanceToOutdoorFace(face, actorCenter),
                    actorCenter.y - face.normal.y * signedDistanceToOutdoorFace(face, actorCenter),
                    actorCenter.z - face.normal.z * signedDistanceToOutdoorFace(face, actorCenter)
                };

                if (!isPointInsideOutdoorPolygonProjected(projectedPoint, face.vertices, face.normal))
                {
                    continue;
                }

                bestDistance = signedDistance;
                pBlockingFace = &face;
            }

            if (pBlockingFace == nullptr)
            {
                failure = "no nearby blocking face found for actor 51";
                return false;
            }

            const float signedDistance = signedDistanceToOutdoorFace(*pBlockingFace, actorCenter);
            const float actorSideSign = signedDistance >= 0.0f ? 1.0f : -1.0f;
            const bx::Vec3 projectedPoint = {
                actorCenter.x - pBlockingFace->normal.x * signedDistance,
                actorCenter.y - pBlockingFace->normal.y * signedDistance,
                actorCenter.z - pBlockingFace->normal.z * signedDistance
            };
            const float leftActorX = projectedPoint.x + pBlockingFace->normal.x * actorSideSign * 192.0f;
            const float leftActorY = projectedPoint.y + pBlockingFace->normal.y * actorSideSign * 192.0f;
            const float rightActorX = projectedPoint.x - pBlockingFace->normal.x * actorSideSign * 192.0f;
            const float rightActorY = projectedPoint.y - pBlockingFace->normal.y * actorSideSign * 192.0f;
            const float leftActorZ = sampleOutdoorPlacementFloorHeight(
                *selectedMap->outdoorMapData,
                leftActorX,
                leftActorY,
                actorZ + 256.0f);
            const float rightActorZ = sampleOutdoorPlacementFloorHeight(
                *selectedMap->outdoorMapData,
                rightActorX,
                rightActorY,
                actorZ + 256.0f);

            const size_t baseActorCount = scenario.world.mapActorCount();

            for (size_t actorIndex = 0; actorIndex < baseActorCount; ++actorIndex)
            {
                if (!scenario.world.setMapActorDead(actorIndex, true, false))
                {
                    failure = "could not clear existing actor";
                    return false;
                }
            }

            const size_t leftActorIndex = scenario.world.mapActorCount();

            if (!scenario.world.summonMonsters(
                    1,
                    2,
                    1,
                    static_cast<int32_t>(std::lround(leftActorX)),
                    static_cast<int32_t>(std::lround(leftActorY)),
                    static_cast<int32_t>(std::lround(leftActorZ)),
                    12,
                    0))
            {
                failure = "could not spawn left hostile actor across blocking face";
                return false;
            }

            if (!scenario.world.summonMonsters(
                    2,
                    2,
                    1,
                    static_cast<int32_t>(std::lround(rightActorX)),
                    static_cast<int32_t>(std::lround(rightActorY)),
                    static_cast<int32_t>(std::lround(rightActorZ)),
                    10,
                    0))
            {
                failure = "could not spawn right hostile actor across blocking face";
                return false;
            }

            const size_t rightActorIndex = leftActorIndex + 1;
            const OutdoorWorldRuntime::MapActorState *pLeftActor = scenario.world.mapActorState(leftActorIndex);
            const OutdoorWorldRuntime::MapActorState *pRightActor = scenario.world.mapActorState(rightActorIndex);

            if (pLeftActor == nullptr || pRightActor == nullptr)
            {
                failure = "spawned hostile actor pair missing";
                return false;
            }

            if (gameDataLoader.getMonsterTable().getRelationBetweenMonsters(
                    pLeftActor->monsterId,
                    pRightActor->monsterId) <= 0)
            {
                failure = "spawned actor pair is not hostile";
                return false;
            }

            const float partyX = actorCenter.x + 20000.0f;
            const float partyY = actorCenter.y + 20000.0f;
            const float partyZ = actorZ;
            const int leftInitialHp = pLeftActor->currentHp;
            const int rightInitialHp = pRightActor->currentHp;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);

                const OutdoorWorldRuntime::MapActorState *pLeftAfter = scenario.world.mapActorState(leftActorIndex);
                const OutdoorWorldRuntime::MapActorState *pRightAfter = scenario.world.mapActorState(rightActorIndex);

                if (pLeftAfter == nullptr || pRightAfter == nullptr)
                {
                    failure = "actor disappeared during blocked hostile simulation";
                    return false;
                }

                if (pLeftAfter->currentHp != leftInitialHp || pRightAfter->currentHp != rightInitialHp)
                {
                    failure = "blocked hostile actors still exchanged damage";
                    return false;
                }

                if (scenario.world.projectileCount() > 0)
                {
                    failure = "blocked hostile actors still launched a projectile";
                    return false;
                }

                if (pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || pLeftAfter->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || pRightAfter->aiState == OutdoorWorldRuntime::ActorAiState::Fleeing)
                {
                    failure = "blocked hostile actors still engaged through geometry";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "outdoor_geometry_reports_steep_terrain_tiles",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            bool foundSteepTile = false;

            for (int tileY = 0; tileY < OutdoorMapData::TerrainHeight - 1 && !foundSteepTile; ++tileY)
            {
                for (int tileX = 0; tileX < OutdoorMapData::TerrainWidth - 1; ++tileX)
                {
                    const float worldX =
                        static_cast<float>((64 - tileX - 1) * OutdoorMapData::TerrainTileSize + 256);
                    const float worldY =
                        static_cast<float>((64 - tileY) * OutdoorMapData::TerrainTileSize - 256);

                    if (outdoorTerrainSlopeTooHigh(*selectedMap->outdoorMapData, worldX, worldY))
                    {
                        foundSteepTile = true;
                        break;
                    }
                }
            }

            if (!foundSteepTile)
            {
                failure = "no steep terrain tile found on out01";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_actor_enters_attack_state",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor != nullptr && pActor->hostileToParty && !pActor->isDead)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            scenario.world.clearPendingAudioEvents();
            const float partyX = static_cast<float>(pBefore->x + 64);
            const float partyY = static_cast<float>(pBefore->y);
            const float partyZ = static_cast<float>(pBefore->z);
            const OutdoorWorldRuntime::MapActorState *pAfter = nullptr;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                pAfter = scenario.world.mapActorState(hostileActorIndex);

                if (pAfter != nullptr && pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking)
                {
                    break;
                }
            }

            if (pAfter == nullptr || pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile actor did not enter attack state";
                return false;
            }

            if (pAfter->animation != OutdoorWorldRuntime::ActorAnimation::AttackMelee
                && pAfter->animation != OutdoorWorldRuntime::ActorAnimation::AttackRanged)
            {
                failure = "hostile actor did not enter attack animation";
                return false;
            }

            if (scenario.world.pendingAudioEvents().empty())
            {
                failure = "attack sound event missing";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mixed_actor_53_pursues_and_can_choose_ranged_attack",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            const MonsterTable::MonsterStatsEntry *pStats =
                gameDataLoader.getMonsterTable().findStatsById(pBefore->monsterId);

            if (pStats == nullptr || pStats->attackStyle != MonsterTable::MonsterAttackStyle::MixedMeleeRanged)
            {
                failure = "actor 53 is not classified as mixed melee+ranged";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    53,
                    1,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "could not provoke actor 53";
                return false;
            }

            const float partyX = pBefore->preciseX + 3000.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            bool sawRangedAttack = false;
            bool sawPursuing = false;
            const float startX = pBefore->preciseX;
            const float startY = pBefore->preciseY;

            for (size_t stepIndex = 0; stepIndex < 4096; ++stepIndex)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

                if (pAfter != nullptr && pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing)
                {
                    sawPursuing = true;
                }

                if (pAfter != nullptr && pAfter->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    && pAfter->animation == OutdoorWorldRuntime::ActorAnimation::AttackRanged)
                {
                    sawRangedAttack = true;
                    break;
                }
            }

            if (!sawRangedAttack)
            {
                failure = "mixed actor 53 never chose a ranged attack";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

            if (pAfter == nullptr)
            {
                failure = "actor 53 missing after simulation";
                return false;
            }

            if (!sawPursuing)
            {
                failure = "mixed actor 53 never pursued the party";
                return false;
            }

            if (std::abs(pAfter->preciseX - startX) < 8.0f && std::abs(pAfter->preciseY - startY) < 8.0f)
            {
                failure = "mixed actor 53 never accumulated movement";
                return false;
            }

            return true;
        }
    );

    runCase(
        "mixed_actor_53_ranged_release_spawns_arrow_projectile",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    53,
                    1,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "could not provoke actor 53";
                return false;
            }

            const float partyX = pBefore->preciseX + 3000.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            bool sawRangedRelease = false;
            bool sawProjectileMove = false;
            float previousProjectileX = 0.0f;
            float previousProjectileY = 0.0f;

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);

                for (const OutdoorWorldRuntime::CombatEvent &event : scenario.world.pendingCombatEvents())
                {
                    if (event.type == GameplayCombatController::CombatEventType::MonsterRangedRelease
                        && event.sourceId == 53)
                    {
                        sawRangedRelease = true;
                    }
                }

                if (scenario.world.projectileCount() > 0)
                {
                    const OutdoorWorldRuntime::ProjectileState *pProjectile = scenario.world.projectileState(0);

                    if (pProjectile == nullptr)
                    {
                        failure = "projectile state missing";
                        return false;
                    }

                    if (pProjectile->objectName != "Arrow")
                    {
                        failure = "actor 53 did not spawn arrow projectile";
                        return false;
                    }

                    if (previousProjectileX != 0.0f || previousProjectileY != 0.0f)
                    {
                        const float deltaX = std::abs(pProjectile->x - previousProjectileX);
                        const float deltaY = std::abs(pProjectile->y - previousProjectileY);
                        sawProjectileMove = sawProjectileMove || deltaX > 1.0f || deltaY > 1.0f;
                    }

                    previousProjectileX = pProjectile->x;
                    previousProjectileY = pProjectile->y;

                    if (sawRangedRelease && sawProjectileMove)
                    {
                        return true;
                    }
                }

                scenario.world.clearPendingCombatEvents();
            }

            failure = !sawRangedRelease ? "actor 53 never released a ranged projectile" : "arrow never advanced";
            return false;
        }
    );

    runCase(
        "mixed_actor_53_arrow_hits_party_without_impact_effect",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            if (!scenario.world.applyPartyAttackToMapActor(
                    53,
                    1,
                    pBefore->preciseX + 64.0f,
                    pBefore->preciseY,
                    pBefore->preciseZ))
            {
                failure = "could not provoke actor 53";
                return false;
            }

            const float partyX = pBefore->preciseX + 2200.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;
            bool sawProjectile = false;
            const int initialTotalHealth = scenario.party.totalHealth();

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                applyPendingCombatEventsToScenarioParty(scenario);

                if (scenario.world.projectileCount() > 0)
                {
                    sawProjectile = true;
                }

                if (sawProjectile && scenario.party.totalHealth() < initialTotalHealth)
                {
                    if (scenario.world.projectileImpactCount() != 0)
                    {
                        failure = "arrow impact should not spawn a lingering impact effect";
                        return false;
                    }

                    return true;
                }
            }

            failure = !sawProjectile ? "actor 53 never spawned arrow projectile" : "arrow hit did not damage the party";
            return false;
        }
    );

    runCase(
        "party_arrow_projectile_can_damage_actor_53",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            OutdoorWorldRuntime::PartyProjectileRequest request = {};
            request.sourcePartyMemberIndex = 0;
            request.objectId = 545;
            request.damage = 7;
            request.attackBonus = 9999;
            request.useActorHitChance = true;
            request.sourceX = pBefore->preciseX + 256.0f;
            request.sourceY = pBefore->preciseY;
            request.sourceZ = pBefore->preciseZ + 96.0f;
            request.targetX = pBefore->preciseX;
            request.targetY = pBefore->preciseY;
            request.targetZ = pBefore->preciseZ + 96.0f;

            if (!scenario.world.spawnPartyProjectile(request))
            {
                failure = "party arrow projectile spawn failed";
                return false;
            }

            const int initialHp = pBefore->currentHp;
            bool sawProjectile = false;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, request.sourceX, request.sourceY, pBefore->preciseZ);
                sawProjectile = sawProjectile || scenario.world.projectileCount() > 0;
                const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

                if (pAfter != nullptr && pAfter->currentHp < initialHp)
                {
                    return true;
                }
            }

            failure = !sawProjectile ? "party arrow projectile never appeared" : "party arrow did not damage actor 53";
            return false;
        }
    );

    runCase(
        "party_spell_projectile_can_damage_actor_53",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            OutdoorWorldRuntime::SpellCastRequest request = {};
            request.sourceKind = OutdoorWorldRuntime::RuntimeSpellSourceKind::Party;
            request.sourceId = 1;
            request.sourcePartyMemberIndex = 0;
            request.ability = OutdoorWorldRuntime::MonsterAttackAbility::Spell1;
            request.spellId = spellIdValue(SpellId::FireBolt);
            request.skillLevel = 10;
            request.skillMastery = static_cast<uint32_t>(SkillMastery::Expert);
            request.damage = 9;
            request.attackBonus = 9999;
            request.useActorHitChance = true;
            request.sourceX = pBefore->preciseX + 256.0f;
            request.sourceY = pBefore->preciseY;
            request.sourceZ = pBefore->preciseZ + 96.0f;
            request.targetX = pBefore->preciseX;
            request.targetY = pBefore->preciseY;
            request.targetZ = pBefore->preciseZ + 96.0f;

            if (!scenario.world.castPartySpell(request))
            {
                failure = "party spell projectile spawn failed";
                return false;
            }

            const int initialHp = pBefore->currentHp;
            bool sawProjectile = false;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, request.sourceX, request.sourceY, pBefore->preciseZ);
                sawProjectile = sawProjectile || scenario.world.projectileCount() > 0;
                const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

                if (pAfter != nullptr && pAfter->currentHp < initialHp)
                {
                    return true;
                }
            }

            failure = !sawProjectile ? "party spell projectile never appeared" : "party spell did not damage actor 53";
            return false;
        }
    );

    runCase(
        "party_fireball_splash_can_damage_party_near_target_actor",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            OutdoorWorldRuntime::SpellCastRequest request = {};
            request.sourceKind = OutdoorWorldRuntime::RuntimeSpellSourceKind::Party;
            request.sourceId = 1;
            request.sourcePartyMemberIndex = 0;
            request.ability = OutdoorWorldRuntime::MonsterAttackAbility::Spell1;
            request.spellId = spellIdValue(SpellId::Fireball);
            request.skillLevel = 10;
            request.skillMastery = static_cast<uint32_t>(SkillMastery::Expert);
            request.damage = 18;
            request.attackBonus = 9999;
            request.useActorHitChance = false;
            request.sourceX = pBefore->preciseX + 256.0f;
            request.sourceY = pBefore->preciseY;
            request.sourceZ = pBefore->preciseZ + 96.0f;
            request.targetX = pBefore->preciseX;
            request.targetY = pBefore->preciseY;
            request.targetZ = pBefore->preciseZ + 96.0f;

            if (!scenario.world.castPartySpell(request))
            {
                failure = "party fireball spawn failed";
                return false;
            }

            const int initialActorHp = pBefore->currentHp;
            const int initialPartyHealth = scenario.party.totalHealth();
            std::array<int, 4> initialMemberHealth = {0, 0, 0, 0};

            for (size_t memberIndex = 0; memberIndex < initialMemberHealth.size(); ++memberIndex)
            {
                const Character *pMember = scenario.party.member(memberIndex);
                initialMemberHealth[memberIndex] = pMember != nullptr ? pMember->health : 0;
            }

            const float partyX = request.sourceX;
            const float partyY = request.sourceY;
            const float partyZ = pBefore->preciseZ;
            bool sawProjectile = false;
            bool damagedActor = false;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                applyPendingCombatEventsToScenarioParty(scenario);
                sawProjectile = sawProjectile || scenario.world.projectileCount() > 0;

                const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(53);

                if (pAfter != nullptr && pAfter->currentHp < initialActorHp)
                {
                    damagedActor = true;
                }

                if (damagedActor && scenario.party.totalHealth() < initialPartyHealth)
                {
                    const int partyDamage = initialPartyHealth - scenario.party.totalHealth();
                    size_t damagedMembers = 0;

                    for (size_t memberIndex = 0; memberIndex < initialMemberHealth.size(); ++memberIndex)
                    {
                        const Character *pMember = scenario.party.member(memberIndex);

                        if (pMember != nullptr && pMember->health < initialMemberHealth[memberIndex])
                        {
                            ++damagedMembers;
                        }
                    }

                    if (partyDamage <= 1)
                    {
                        failure = "party fireball splash damage was only " + std::to_string(partyDamage);
                        return false;
                    }

                    if (damagedMembers < 4)
                    {
                        failure = "party fireball splash damaged only " + std::to_string(damagedMembers)
                            + " party members";
                        return false;
                    }

                    return true;
                }
            }

            if (!sawProjectile)
            {
                failure = "party fireball projectile never appeared";
            }
            else if (!damagedActor)
            {
                failure = "party fireball did not damage actor 53";
            }
            else
            {
                failure = "party fireball splash did not damage the party";
            }

            return false;
        }
    );

    runCase(
        "party_fireball_splash_can_damage_multiple_nearby_actors",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData || selectedMap->outdoorMapDeltaData->actors.size() <= 53)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapData = *selectedMap->outdoorMapData;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapData->spawns.clear();

            const MapDeltaActor anchorActor = modifiedMap.outdoorMapDeltaData->actors[53];
            MapDeltaActor &leftActor = modifiedMap.outdoorMapDeltaData->actors[3];
            MapDeltaActor &rightActor = modifiedMap.outdoorMapDeltaData->actors[53];
            leftActor.x = anchorActor.x - 160;
            leftActor.y = anchorActor.y;
            leftActor.z = anchorActor.z;
            rightActor.x = anchorActor.x + 160;
            rightActor.y = anchorActor.y;
            rightActor.z = anchorActor.z;

            for (size_t actorIndex = 0; actorIndex < modifiedMap.outdoorMapDeltaData->actors.size(); ++actorIndex)
            {
                if (actorIndex == 3 || actorIndex == 53)
                {
                    continue;
                }

                MapDeltaActor &otherActor = modifiedMap.outdoorMapDeltaData->actors[actorIndex];
                otherActor.x = anchorActor.x + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.y = anchorActor.y + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.z = anchorActor.z;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pLeftBefore = scenario.world.mapActorState(3);
            const OutdoorWorldRuntime::MapActorState *pRightBefore = scenario.world.mapActorState(53);

            if (pLeftBefore == nullptr || pRightBefore == nullptr)
            {
                failure = "cluster actors missing";
                return false;
            }

            const int initialLeftHp = pLeftBefore->currentHp;
            const int initialRightHp = pRightBefore->currentHp;

            OutdoorWorldRuntime::SpellCastRequest request = {};
            request.sourceKind = OutdoorWorldRuntime::RuntimeSpellSourceKind::Party;
            request.sourceId = 1;
            request.sourcePartyMemberIndex = 0;
            request.ability = OutdoorWorldRuntime::MonsterAttackAbility::Spell1;
            request.spellId = spellIdValue(SpellId::Fireball);
            request.skillLevel = 10;
            request.skillMastery = static_cast<uint32_t>(SkillMastery::Expert);
            request.damage = 18;
            request.attackBonus = 9999;
            request.useActorHitChance = false;
            request.sourceX = pRightBefore->preciseX + 256.0f;
            request.sourceY = pRightBefore->preciseY;
            request.sourceZ = pRightBefore->preciseZ + 96.0f;
            request.targetX = pRightBefore->preciseX;
            request.targetY = pRightBefore->preciseY;
            request.targetZ = pRightBefore->preciseZ + 96.0f;

            if (!scenario.world.castPartySpell(request))
            {
                failure = "party fireball spawn failed";
                return false;
            }

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, request.sourceX, request.sourceY, pRightBefore->preciseZ);

                const OutdoorWorldRuntime::MapActorState *pLeftAfter = scenario.world.mapActorState(3);
                const OutdoorWorldRuntime::MapActorState *pRightAfter = scenario.world.mapActorState(53);

                if (pLeftAfter != nullptr
                    && pRightAfter != nullptr
                    && pLeftAfter->currentHp < initialLeftHp
                    && pRightAfter->currentHp < initialRightHp)
                {
                    return true;
                }
            }

            failure = "party fireball did not damage both nearby actors";
            return false;
        }
    );

    runCase(
        "mixed_actor_53_arrow_ignores_friendly_lizardman_blocker",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData || selectedMap->outdoorMapDeltaData->actors.size() <= 53)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapData = *selectedMap->outdoorMapData;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapData->spawns.clear();

            const MapDeltaActor quietLandActor = modifiedMap.outdoorMapDeltaData->actors[3];
            MapDeltaActor &guardActor = modifiedMap.outdoorMapDeltaData->actors[53];
            guardActor.x = quietLandActor.x;
            guardActor.y = quietLandActor.y;
            guardActor.z = quietLandActor.z;
            MapDeltaActor &blockingActor = modifiedMap.outdoorMapDeltaData->actors[3];
            blockingActor.x = quietLandActor.x + 1100;
            blockingActor.y = quietLandActor.y;
            blockingActor.z = quietLandActor.z;

            for (size_t actorIndex = 0; actorIndex < modifiedMap.outdoorMapDeltaData->actors.size(); ++actorIndex)
            {
                if (actorIndex == 3 || actorIndex == 53)
                {
                    continue;
                }

                MapDeltaActor &otherActor = modifiedMap.outdoorMapDeltaData->actors[actorIndex];
                otherActor.x = quietLandActor.x + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.y = quietLandActor.y + 40000 + static_cast<int>(actorIndex) * 64;
                otherActor.z = quietLandActor.z;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pGuard = scenario.world.mapActorState(53);
            const OutdoorWorldRuntime::MapActorState *pBlocker = scenario.world.mapActorState(3);

            if (pGuard == nullptr)
            {
                failure = "actor 53 missing";
                return false;
            }

            if (pBlocker == nullptr)
            {
                failure = "actor 3 missing";
                return false;
            }

            if (!gameDataLoader.getMonsterTable().isLikelySameFaction(pGuard->monsterId, pBlocker->monsterId))
            {
                failure = "actor 3 is not same-faction with actor 53";
                return false;
            }

            const float partyX = pGuard->preciseX + 2200.0f;
            const float partyY = pGuard->preciseY;
            const float partyZ = pGuard->preciseZ;
            const int initialTotalHealth = scenario.party.totalHealth();
            bool sawProjectile = false;

            if (!scenario.world.debugSpawnMapActorProjectile(
                    53,
                    OutdoorWorldRuntime::MonsterAttackAbility::Attack2,
                    partyX,
                    partyY,
                    partyZ))
            {
                failure = "could not spawn actor 53 arrow projectile";
                return false;
            }

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                applyPendingCombatEventsToScenarioParty(scenario);
                sawProjectile = sawProjectile || scenario.world.projectileCount() > 0;

                if (scenario.party.totalHealth() < initialTotalHealth)
                {
                    return true;
                }
            }

            failure = !sawProjectile
                ? "actor 53 arrow projectile never spawned"
                : "friendly actor blocked actor 53 arrow before it reached the party";
            return false;
        }
    );

    runCase(
        "pirate_and_lizardman_hostile_actors_damage_each_other",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t leftActorIndex = scenario.world.mapActorCount();
            constexpr float FightCenterX = -9216.0f;
            constexpr float FightCenterY = -12848.0f;
            constexpr float FightCenterZ = 110.0f;

            if (!scenario.world.summonMonsters(1, 2, 1, -9280, -12848, static_cast<int32_t>(FightCenterZ), 12, 0))
            {
                failure = "could not spawn lizardman encounter actor";
                return false;
            }

            if (!scenario.world.summonMonsters(2, 2, 1, -9152, -12848, static_cast<int32_t>(FightCenterZ), 10, 0))
            {
                failure = "could not spawn pirate encounter actor";
                return false;
            }

            const size_t rightActorIndex = leftActorIndex + 1;
            const OutdoorWorldRuntime::MapActorState *pLeftActorBefore =
                scenario.world.mapActorState(leftActorIndex);
            const OutdoorWorldRuntime::MapActorState *pRightActorBefore =
                scenario.world.mapActorState(rightActorIndex);

            if (pLeftActorBefore == nullptr || pRightActorBefore == nullptr)
            {
                failure = "spawned hostile actor pair missing";
                return false;
            }

            if (gameDataLoader.getMonsterTable().getRelationBetweenMonsters(
                    pLeftActorBefore->monsterId,
                    pRightActorBefore->monsterId) <= 0)
            {
                failure = "spawned pirate and lizardman are not hostile";
                return false;
            }

            const int leftInitialHp = pLeftActorBefore->currentHp;
            const int rightInitialHp = pRightActorBefore->currentHp;
            const float partyX = pRightActorBefore->preciseX + 6000.0f;
            const float partyY = pRightActorBefore->preciseY;
            const float partyZ = pRightActorBefore->preciseZ;
            bool sawEngagement = false;

            for (int step = 0; step < 8192; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);

                const OutdoorWorldRuntime::MapActorState *pLeftActor =
                    scenario.world.mapActorState(leftActorIndex);
                const OutdoorWorldRuntime::MapActorState *pRightActor =
                    scenario.world.mapActorState(rightActorIndex);

                if (pLeftActor == nullptr || pRightActor == nullptr)
                {
                    failure = "hostile actor disappeared during simulation";
                    return false;
                }

                sawEngagement = sawEngagement
                    || pLeftActor->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pLeftActor->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || pRightActor->aiState == OutdoorWorldRuntime::ActorAiState::Pursuing
                    || pRightActor->aiState == OutdoorWorldRuntime::ActorAiState::Attacking
                    || scenario.world.projectileCount() > 0;

                if (pLeftActor->currentHp < leftInitialHp || pRightActor->currentHp < rightInitialHp
                    || pLeftActor->isDead || pRightActor->isDead)
                {
                    if ((pLeftActor->isDead && pLeftActor->currentHp == 0 && leftInitialHp > 0)
                        || (pRightActor->isDead && pRightActor->currentHp == 0 && rightInitialHp > 0))
                    {
                        failure = "first hostile hit still one-shot a spawned actor";
                        return false;
                    }

                    return true;
                }
            }

            failure = sawEngagement
                ? "hostile actor engagement never produced damage"
                : "hostile actor pair never engaged each other";
            return false;
        }
    );

    runCase(
        "spell_projectile_spawns_visible_impact_effect",
        [&](std::string &failure)
        {
            if (!selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map has no outdoor actor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = *selectedMap->outdoorMapDeltaData;
            modifiedMap.outdoorMapDeltaData->actors[53].monsterInfoId = 80;
            modifiedMap.outdoorMapDeltaData->actors[53].monsterId = 80;
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(53);

            if (pBefore == nullptr)
            {
                failure = "synthetic actor 53 missing";
                return false;
            }

            const float partyX = pBefore->preciseX + 2600.0f;
            const float partyY = pBefore->preciseY;
            const float partyZ = pBefore->preciseZ;

            if (!scenario.world.debugSpawnMapActorProjectile(
                    53,
                    OutdoorWorldRuntime::MonsterAttackAbility::Spell1,
                    partyX,
                    partyY,
                    partyZ))
            {
                failure = "could not spawn synthetic spell projectile";
                return false;
            }

            bool sawProjectile = false;

            for (int step = 0; step < 4096; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);

                if (scenario.world.projectileCount() > 0)
                {
                    sawProjectile = true;
                }

                if (scenario.world.projectileImpactCount() > 0)
                {
                    const OutdoorWorldRuntime::ProjectileImpactState *pImpact =
                        scenario.world.projectileImpactState(0);

                    if (pImpact == nullptr)
                    {
                        failure = "impact state missing";
                        return false;
                    }

                    if (pImpact->objectName != "explosion")
                    {
                        failure = "spell impact did not spawn expected explosion effect";
                        return false;
                    }

                    return true;
                }
            }

            if (!sawProjectile)
            {
                failure = "synthetic spell projectile never spawned";
            }
            else
            {
                failure = "spell impact never spawned";
            }

            return false;
        }
    );

    runCase(
        "hostile_actor_attack_persists_when_party_moves_away",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float nearPartyX = static_cast<float>(pBefore->x + 64);
            const float nearPartyY = static_cast<float>(pBefore->y);
            const float partyZ = static_cast<float>(pBefore->z);
            const OutdoorWorldRuntime::MapActorState *pAttacking = nullptr;

            for (int step = 0; step < 256; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, nearPartyX, nearPartyY, partyZ);
                pAttacking = scenario.world.mapActorState(hostileActorIndex);

                if (pAttacking != nullptr && pAttacking->aiState == OutdoorWorldRuntime::ActorAiState::Attacking)
                {
                    break;
                }
            }

            if (pAttacking == nullptr || pAttacking->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile actor did not enter attack state";
                return false;
            }

            if (pAttacking->actionSeconds <= 0.0f)
            {
                failure = "hostile actor attack duration did not start";
                return false;
            }

            const float previousActionSeconds = pAttacking->actionSeconds;
            scenario.world.updateMapActors(
                0.05f,
                static_cast<float>(pBefore->x + 4000),
                static_cast<float>(pBefore->y),
                static_cast<float>(pBefore->z));
            const OutdoorWorldRuntime::MapActorState *pAfter = scenario.world.mapActorState(hostileActorIndex);

            if (pAfter->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile actor abandoned attack when party moved away";
                return false;
            }

            if (pAfter->actionSeconds >= previousActionSeconds)
            {
                failure = "hostile actor attack did not continue progressing";
                return false;
            }

            return true;
        }
    );

    runCase(
        "hostile_melee_actor_respects_recovery_after_attack",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t hostileActorIndex = std::numeric_limits<size_t>::max();

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || !pActor->hostileToParty || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr
                    && pStats->attackStyle == MonsterTable::MonsterAttackStyle::MeleeOnly
                    && pStats->aiType != MonsterTable::MonsterAiType::Wimp
                    && pStats->movementType != MonsterTable::MonsterMovementType::Stationary)
                {
                    hostileActorIndex = actorIndex;
                    break;
                }
            }

            if (hostileActorIndex == std::numeric_limits<size_t>::max())
            {
                failure = "no hostile melee actor found";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pBefore = scenario.world.mapActorState(hostileActorIndex);
            const float partyX = static_cast<float>(pBefore->x + 64);
            const float partyY = static_cast<float>(pBefore->y);
            const float partyZ = static_cast<float>(pBefore->z);
            const OutdoorWorldRuntime::MapActorState *pAttacking = nullptr;

            for (int step = 0; step < 512; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                pAttacking = scenario.world.mapActorState(hostileActorIndex);

                if (pAttacking != nullptr && pAttacking->aiState == OutdoorWorldRuntime::ActorAiState::Attacking)
                {
                    break;
                }
            }

            if (pAttacking == nullptr || pAttacking->aiState != OutdoorWorldRuntime::ActorAiState::Attacking)
            {
                failure = "hostile melee actor did not enter attack state";
                return false;
            }

            bool sawPostAttackStandWithCooldown = false;

            for (int step = 0; step < 512; ++step)
            {
                scenario.world.updateMapActors(1.0f / 128.0f, partyX, partyY, partyZ);
                const OutdoorWorldRuntime::MapActorState *pStep = scenario.world.mapActorState(hostileActorIndex);

                if (pStep == nullptr)
                {
                    failure = "hostile melee actor disappeared";
                    return false;
                }

                if (pStep->aiState != OutdoorWorldRuntime::ActorAiState::Attacking
                    && pStep->attackCooldownSeconds > 0.2f)
                {
                    sawPostAttackStandWithCooldown = true;
                    break;
                }
            }

            if (!sawPostAttackStandWithCooldown)
            {
                failure = "hostile melee actor did not expose a post-attack recovery window";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_reinforcement_wave_event_463_spawns_all_groups",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t baseActorCount = scenario.world.mapActorCount();

            for (size_t actorIndex = 0; actorIndex < baseActorCount; ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor != nullptr
                    && pActor->group >= 10
                    && pActor->group <= 13
                    && !pActor->isDead)
                {
                    if (!scenario.world.setMapActorDead(actorIndex, true))
                    {
                        failure = "could not clear reinforcement source actor";
                        return false;
                    }
                }
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 463))
            {
                failure = "event 463 execution failed";
                return false;
            }

            if (scenario.world.mapActorCount() != baseActorCount + 48)
            {
                failure = "expected 48 spawned runtime actors, got "
                    + std::to_string(scenario.world.mapActorCount() - baseActorCount);
                return false;
            }

            std::array<int, 4> counts = {};
            std::array<bool, 4> correctMonsterIds = {true, true, true, true};

            for (size_t actorIndex = baseActorCount; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pMonster = scenario.world.mapActorState(actorIndex);

                if (pMonster == nullptr)
                {
                    failure = "missing spawned actor state";
                    return false;
                }

                if (pMonster->group >= 10 && pMonster->group <= 13)
                {
                    const size_t groupOffset = pMonster->group - 10;
                    ++counts[groupOffset];

                    const int16_t expectedMonsterId = pMonster->group <= 11 ? 182 : 5;

                    if (pMonster->monsterId != expectedMonsterId)
                    {
                        correctMonsterIds[groupOffset] = false;
                    }
                }
            }

            for (size_t index = 0; index < counts.size(); ++index)
            {
                if (counts[index] != 12)
                {
                    failure = "group " + std::to_string(index + 10) + " expected 12 summons";
                    return false;
                }

                if (!correctMonsterIds[index])
                {
                    failure = "group " + std::to_string(index + 10) + " summoned wrong monster tier";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "dwi_reinforcement_wave_event_463_does_not_duplicate_alive_groups",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor != nullptr
                    && pActor->group >= 10
                    && pActor->group <= 13
                    && !pActor->isDead)
                {
                    if (!scenario.world.setMapActorDead(actorIndex, true))
                    {
                        failure = "could not clear reinforcement source actor";
                        return false;
                    }
                }
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 463))
            {
                failure = "first event 463 execution failed";
                return false;
            }

            const size_t firstCount = scenario.world.mapActorCount();

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 463))
            {
                failure = "second event 463 execution failed";
                return false;
            }

            if (scenario.world.mapActorCount() != firstCount)
            {
                failure = "reinforcement waves duplicated while groups were still alive";
                return false;
            }

            return true;
        }
    );

    runCase(
        "world_actor_killed_policy_actor_id_mm8",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (scenario.world.checkMonstersKilled(4, 8, 1, true))
            {
                failure = "actor 8 should not start as killed";
                return false;
            }

            if (!scenario.world.setMapActorDead(8, true))
            {
                failure = "could not mark actor 8 dead";
                return false;
            }

            if (!scenario.world.checkMonstersKilled(4, 8, 1, true))
            {
                failure = "actor-id kill check did not detect dead actor 8";
                return false;
            }

            return true;
        }
    );

    runCase(
        "event_can_show_topic_actor_killed_uses_scene_context",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            std::string error;
            std::optional<ScriptedEventProgram> scriptedProgram = loadSyntheticScriptedProgram(
                "evt.CanShowTopic[1] = function()\n"
                "    evt._BeginCanShowTopic(1)\n"
                "    if evt.CheckMonstersKilled(4, 8, 1, true) then\n"
                "        return true\n"
                "    end\n"
                "    return false\n"
                "end\n",
                "@SyntheticCanShowTopic.lua",
                ScriptedEventScope::Global,
                error);
            EventRuntime eventRuntime = {};

            if (!scriptedProgram)
            {
                failure = "could not build synthetic CanShowTopic script: " + error;
                return false;
            }

            if (eventRuntime.canShowTopic(
                    scriptedProgram,
                    1,
                    *scenario.pEventRuntimeState,
                    &scenario.party,
                    &scenario.world))
            {
                failure = "topic should start hidden while actor 8 is alive";
                return false;
            }

            if (!scenario.world.setMapActorDead(8, true))
            {
                failure = "could not kill actor 8";
                return false;
            }

            if (!eventRuntime.canShowTopic(
                    scriptedProgram,
                    1,
                    *scenario.pEventRuntimeState,
                    &scenario.party,
                    &scenario.world))
            {
                failure = "topic should become visible once actor 8 is dead";
                return false;
            }

            return true;
        }
    );

    runCase(
        "world_actor_death_generates_corpse_loot",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!scenario.world.setMapActorDead(5, true))
            {
                failure = "could not kill actor 5";
                return false;
            }

            if (!scenario.world.openMapActorCorpseView(5))
            {
                failure = "corpse view did not open";
                return false;
            }

            const OutdoorWorldRuntime::CorpseViewState *pCorpseView = scenario.world.activeCorpseView();

            if (pCorpseView == nullptr)
            {
                failure = "active corpse view missing";
                return false;
            }

            if (pCorpseView->title != "Lizardman Peasant")
            {
                failure = "unexpected corpse title \"" + pCorpseView->title + "\"";
                return false;
            }

            if (pCorpseView->items.empty() || !pCorpseView->items[0].isGold || pCorpseView->items[0].goldAmount == 0)
            {
                failure = "expected gold loot on corpse";
                return false;
            }

            while (const OutdoorWorldRuntime::CorpseViewState *pActiveCorpseView = scenario.world.activeCorpseView())
            {
                if (pActiveCorpseView->items.empty())
                {
                    break;
                }

                OutdoorWorldRuntime::ChestItemState lootedItem = {};

                if (!scenario.world.takeActiveCorpseItem(0, lootedItem))
                {
                    failure = "could not remove corpse loot item";
                    return false;
                }
            }

            if (scenario.world.activeCorpseView() != nullptr)
            {
                failure = "empty corpse view should close itself";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(5);

            if (pActor == nullptr || !pActor->isInvisible)
            {
                failure = "looted corpse actor should disappear";
                return false;
            }

            if (scenario.world.openMapActorCorpseView(5))
            {
                failure = "looted corpse should no longer be reopenable";
                return false;
            }

            return true;
        }
    );

    runCase(
        "world_actor_death_emits_audio_event",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            scenario.world.clearPendingAudioEvents();

            if (!scenario.world.setMapActorDead(53, true))
            {
                failure = "could not kill actor 53";
                return false;
            }

            if (scenario.world.pendingAudioEvents().empty())
            {
                failure = "missing death audio event";
                return false;
            }

            const OutdoorWorldRuntime::AudioEvent &event = scenario.world.pendingAudioEvents().front();

            if (event.soundId != 1011 || event.reason != "monster_death")
            {
                failure = "unexpected audio event payload";
                return false;
            }

            return true;
        }
    );

    runCase(
        "world_group_killed_policy_counts_spawned_runtime_actors",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const size_t baseActorCount = scenario.world.mapActorCount();

            for (size_t actorIndex = 0; actorIndex < baseActorCount; ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor != nullptr
                    && pActor->group == 10
                    && !pActor->isDead)
                {
                    if (!scenario.world.setMapActorDead(actorIndex, true))
                    {
                        failure = "could not clear group 10 source actor";
                        return false;
                    }
                }
            }

            if (!executeLocalEventInScenario(gameDataLoader, *selectedMap, scenario, 463))
            {
                failure = "event 463 execution failed";
                return false;
            }

            if (scenario.world.checkMonstersKilled(1, 10, 0, true))
            {
                failure = "group 10 should still be alive after spawning";
                return false;
            }

            for (size_t actorIndex = baseActorCount; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pMonster = scenario.world.mapActorState(actorIndex);

                if (pMonster != nullptr && pMonster->group == 10)
                {
                    if (!scenario.world.setMapActorDead(actorIndex, true))
                    {
                        failure = "could not mark spawned runtime actor dead";
                        return false;
                    }
                }
            }

            if (!scenario.world.checkMonstersKilled(1, 10, 0, true))
            {
                failure = "group kill check did not treat dead spawned runtime actors as defeated";
                return false;
            }

            return true;
        }
    );

    runCase(
        "party_monster_kill_grants_shared_experience",
        [&](std::string &failure)
        {
            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            size_t targetActorIndex = std::numeric_limits<size_t>::max();
            const MonsterTable::MonsterStatsEntry *pTargetStats = nullptr;

            for (size_t actorIndex = 0; actorIndex < scenario.world.mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = scenario.world.mapActorState(actorIndex);

                if (pActor == nullptr || pActor->isDead)
                {
                    continue;
                }

                const MonsterTable::MonsterStatsEntry *pStats =
                    gameDataLoader.getMonsterTable().findStatsById(pActor->monsterId);

                if (pStats != nullptr && pStats->experience >= 10)
                {
                    targetActorIndex = actorIndex;
                    pTargetStats = pStats;
                    break;
                }
            }

            if (targetActorIndex == std::numeric_limits<size_t>::max() || pTargetStats == nullptr)
            {
                failure = "no suitable monster with experience found";
                return false;
            }

            Character *pFirst = scenario.party.member(0);
            Character *pSecond = scenario.party.member(1);
            Character *pThird = scenario.party.member(2);
            Character *pFourth = scenario.party.member(3);
            const OutdoorWorldRuntime::MapActorState *pTargetActor = scenario.world.mapActorState(targetActorIndex);

            if (pFirst == nullptr || pSecond == nullptr || pThird == nullptr || pFourth == nullptr || pTargetActor == nullptr)
            {
                failure = "missing scenario state";
                return false;
            }

            pFirst->skills["Learning"] = {"Learning", 5, SkillMastery::Normal};
            pSecond->conditions.set(static_cast<size_t>(CharacterCondition::Unconscious));
            pThird->conditions.set(static_cast<size_t>(CharacterCondition::Petrified));

            const uint32_t expectedBaseExperience = static_cast<uint32_t>(pTargetStats->experience) / 2u;

            if (!scenario.world.applyPartyAttackToMapActor(
                    targetActorIndex,
                    pTargetActor->currentHp + 1000,
                    pTargetActor->preciseX + 64.0f,
                    pTargetActor->preciseY,
                    pTargetActor->preciseZ))
            {
                failure = "party attack did not apply";
                return false;
            }

            if (pFirst->experience != expectedBaseExperience + expectedBaseExperience * 14u / 100u)
            {
                failure = "first member received unexpected monster experience";
                return false;
            }

            if (pSecond->experience != 0 || pThird->experience != 0)
            {
                failure = "incapacitated members received monster experience";
                return false;
            }

            if (pFourth->experience != expectedBaseExperience)
            {
                failure = "fourth member received unexpected monster experience";
                return false;
            }

            return true;
        }
    );

    runCase(
        "outdoor_world_time_advances_without_timer_programs",
        [&](std::string &failure)
        {
            if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map is not an outdoor gameplay map";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const float beforeMinutes = scenario.world.gameMinutes();
            EventRuntime eventRuntime = {};

            if (scenario.world.updateTimers(1.0f, eventRuntime, std::nullopt, std::nullopt))
            {
                failure = "timer update unexpectedly executed an event";
                return false;
            }

            if (scenario.world.gameMinutes() <= beforeMinutes)
            {
                failure = "world time did not advance without timer programs";
                return false;
            }

            return true;
        }
    );

    runCase(
        "save_game_roundtrip_restores_party_world_and_movement_state",
        [&](std::string &failure)
        {
            if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorMapDeltaData)
            {
                failure = "selected map is not an outdoor gameplay map";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            scenario.party.addGold(123);
            scenario.party.depositGoldToBank(50);
            scenario.party.markArtifactItemFound(519);
            scenario.party.applyPartyBuff(PartyBuffId::Haste, 60.0f, 1, 6, 1, SkillMastery::Normal, 0);
            scenario.world.advanceGameMinutes(37.5f);

            Character *pActiveMember = scenario.party.activeMember();

            if (pActiveMember == nullptr)
            {
                failure = "missing active party member";
                return false;
            }

            pActiveMember->permanentBonuses.intellect = 2;
            pActiveMember->intellect += 2;

            InventoryItem savedInventoryItem =
                ItemGenerator::makeInventoryItem(137, gameDataLoader.getItemTable(), ItemGenerationMode::ChestLoot);
            savedInventoryItem.identified = true;
            savedInventoryItem.gridX = 4;
            savedInventoryItem.gridY = 2;

            if (!pActiveMember->addInventoryItemAt(savedInventoryItem, savedInventoryItem.gridX, savedInventoryItem.gridY))
            {
                failure = "could not seed saved inventory item";
                return false;
            }

            Party::HouseStockState &shopState = scenario.party.ensureHouseStockState(1);
            shopState.nextRefreshGameMinutes = scenario.world.gameMinutes() + 1440.0f;
            shopState.refreshSequence = 7;
            shopState.standardStock.push_back(savedInventoryItem);

            InventoryItem savedShopItem =
                ItemGenerator::makeInventoryItem(143, gameDataLoader.getItemTable(), ItemGenerationMode::Shop);
            savedShopItem.identified = true;
            shopState.specialStock.push_back(savedShopItem);

            InventoryItem savedSpellbook =
                ItemGenerator::makeInventoryItem(400, gameDataLoader.getItemTable(), ItemGenerationMode::Shop);
            savedSpellbook.identified = true;
            shopState.spellbookStock.push_back(savedSpellbook);

            if (scenario.world.mapActorCount() == 0)
            {
                failure = "scenario has no actors to persist";
                return false;
            }

            if (!scenario.world.setMapActorDead(0, true, false))
            {
                failure = "could not mark actor dead before save";
                return false;
            }

            InventoryItem droppedItem =
                ItemGenerator::makeInventoryItem(137, gameDataLoader.getItemTable(), ItemGenerationMode::ChestLoot);
            droppedItem.identified = true;

            if (!scenario.world.spawnWorldItem(droppedItem, 8704.0f, 2000.0f, 686.0f, 0.0f))
            {
                failure = "could not spawn world item before save";
                return false;
            }

            EventRuntimeState *pEventRuntimeState = scenario.world.eventRuntimeState();

            if (pEventRuntimeState == nullptr)
            {
                failure = "missing event runtime state";
                return false;
            }

            pEventRuntimeState->variables[0x1234u] = 99;
            pEventRuntimeState->messages.push_back("save roundtrip");

            const RosterEntry *pInnRosterEntry = gameDataLoader.getRosterTable().get(3);
            const NpcEntry *pInnNpcEntry =
                pInnRosterEntry != nullptr ? gameDataLoader.getNpcDialogTable().findNpcByName(pInnRosterEntry->name) : nullptr;

            if (pInnRosterEntry == nullptr
                || !scenario.party.addAdventurersInnMember(
                    *pInnRosterEntry,
                    pInnNpcEntry != nullptr ? pInnNpcEntry->pictureId : 0))
            {
                failure = "could not seed adventurer's inn before save";
                return false;
            }

            GameSaveData saveData = {};
            saveData.mapFileName = selectedMap->map.fileName;
            saveData.party = scenario.party.snapshot();
            saveData.hasOutdoorRuntimeState = true;
            saveData.outdoorParty.movementState.x = 123.0f;
            saveData.outdoorParty.movementState.y = -456.0f;
            saveData.outdoorParty.movementState.footZ = 789.0f;
            saveData.outdoorParty.movementState.verticalVelocity = 10.0f;
            saveData.outdoorParty.movementState.airborne = true;
            saveData.outdoorParty.partyMovementState.running = false;
            saveData.outdoorParty.partyMovementState.flying = true;
            saveData.outdoorParty.partyMovementState.waterWalk = true;
            saveData.outdoorParty.partyMovementState.featherFall = true;
            saveData.outdoorWorld = scenario.world.snapshot();
            saveData.outdoorWorld.atmosphere.sourceSkyTextureName = "sky06";
            saveData.outdoorWorld.atmosphere.skyTextureName = "sunsetclouds";
            saveData.outdoorWorld.atmosphere.weatherFlags = 1;
            saveData.outdoorWorld.atmosphere.fogWeakDistance = 2048;
            saveData.outdoorWorld.atmosphere.fogStrongDistance = 4096;
            saveData.outdoorWorld.gameMinutes = 20.0f * 60.0f + 30.0f;
            saveData.outdoorWorldStates[saveData.mapFileName] = saveData.outdoorWorld;
            saveData.outdoorWorldStates["Data/games/out02.odm"] = saveData.outdoorWorld;
            saveData.outdoorWorldStates["Data/games/out02.odm"].gameMinutes += 12.0f;
            saveData.savedGameMinutes = saveData.outdoorWorld.gameMinutes;
            saveData.outdoorCameraYawRadians = 1.25f;
            saveData.outdoorCameraPitchRadians = -0.45f;

            const std::filesystem::path savePath = "/tmp/openyamm_save_roundtrip.oysav";
            std::string error;

            if (!saveGameDataToPath(savePath, saveData, error))
            {
                failure = "save failed: " + error;
                return false;
            }

            const std::optional<GameSaveData> loadedSave = loadGameDataFromPath(savePath, error);
            std::error_code removeError;
            std::filesystem::remove(savePath, removeError);

            if (!loadedSave)
            {
                failure = "load failed: " + error;
                return false;
            }

            if (loadedSave->mapFileName != selectedMap->map.fileName)
            {
                failure = "loaded save used the wrong map file";
                return false;
            }

            const std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot>::const_iterator savedOut02It =
                loadedSave->outdoorWorldStates.find("Data/games/out02.odm");

            if (!loadedSave->outdoorWorldStates.contains(saveData.mapFileName)
                || savedOut02It == loadedSave->outdoorWorldStates.end()
                || std::abs(savedOut02It->second.gameMinutes - (saveData.outdoorWorld.gameMinutes + 12.0f)) > 0.01f)
            {
                failure = "visited map world states did not roundtrip";
                return false;
            }

            if (std::abs(loadedSave->outdoorCameraYawRadians - 1.25f) > 0.0001f
                || std::abs(loadedSave->outdoorCameraPitchRadians + 0.45f) > 0.0001f)
            {
                failure = "camera heading did not roundtrip";
                return false;
            }

            Party restoredParty = {};
            restoredParty.setItemTable(&gameDataLoader.getItemTable());
            restoredParty.setItemEnchantTables(
                &gameDataLoader.getStandardItemEnchantTable(),
                &gameDataLoader.getSpecialItemEnchantTable());
            restoredParty.setClassSkillTable(&gameDataLoader.getClassSkillTable());
            restoredParty.restoreSnapshot(loadedSave->party);

            if (restoredParty.gold() != scenario.party.gold() || restoredParty.bankGold() != scenario.party.bankGold())
            {
                failure = "party gold or bank gold did not roundtrip";
                return false;
            }

            if (!restoredParty.hasFoundArtifactItem(519) || !restoredParty.hasPartyBuff(PartyBuffId::Haste))
            {
                failure = "party artifact or buff state did not roundtrip";
                return false;
            }

            const Character *pRestoredMember = restoredParty.activeMember();

            if (pRestoredMember == nullptr)
            {
                failure = "missing restored active member";
                return false;
            }

            if (pRestoredMember->permanentBonuses.intellect != 2 || pRestoredMember->intellect != pActiveMember->intellect)
            {
                failure = "permanent stat changes did not roundtrip";
                return false;
            }

            const InventoryItem *pRestoredInventoryItem = pRestoredMember->inventoryItemAt(4, 2);

            if (pRestoredInventoryItem == nullptr || pRestoredInventoryItem->objectDescriptionId != 137)
            {
                failure = "member inventory did not roundtrip";
                return false;
            }

            const Party::HouseStockState *pRestoredShopState = restoredParty.houseStockState(1);

            if (pRestoredShopState == nullptr
                || pRestoredShopState->refreshSequence != 7
                || pRestoredShopState->standardStock.size() != 1
                || pRestoredShopState->specialStock.size() != 1
                || pRestoredShopState->spellbookStock.size() != 1)
            {
                failure = "house stock state did not roundtrip";
                return false;
            }

            const AdventurersInnMember *pRestoredInnMember = restoredParty.adventurersInnMember(0);

            if (pRestoredInnMember == nullptr
                || pRestoredInnMember->character.rosterId != 3
                || pRestoredInnMember->character.name.empty())
            {
                failure = "adventurer's inn state did not roundtrip";
                return false;
            }

            OutdoorPartyRuntime restoredPartyRuntime(
                OutdoorMovementDriver(
                    *selectedMap->outdoorMapData,
                    selectedMap->map.outdoorBounds.enabled
                        ? std::optional<MapBounds>(selectedMap->map.outdoorBounds)
                        : std::nullopt,
                    selectedMap->outdoorLandMask,
                    selectedMap->outdoorDecorationCollisionSet,
                    selectedMap->outdoorActorCollisionSet,
                    selectedMap->outdoorSpriteObjectCollisionSet),
                gameDataLoader.getItemTable());
            restoredPartyRuntime.setParty(restoredParty);
            restoredPartyRuntime.restoreSnapshot(loadedSave->outdoorParty);

            if (std::abs(restoredPartyRuntime.movementState().x - 123.0f) > 0.01f
                || std::abs(restoredPartyRuntime.movementState().y + 456.0f) > 0.01f
                || !restoredPartyRuntime.movementState().airborne
                || restoredPartyRuntime.partyMovementState().running
                || !restoredPartyRuntime.partyMovementState().flying)
            {
                failure = "party movement state did not roundtrip";
                return false;
            }

            OutdoorWorldRuntime restoredWorld = {};
            restoredWorld.initialize(
                selectedMap->map,
                gameDataLoader.getMonsterTable(),
                gameDataLoader.getMonsterProjectileTable(),
                gameDataLoader.getObjectTable(),
                gameDataLoader.getSpellTable(),
                gameDataLoader.getItemTable(),
                &restoredPartyRuntime.party(),
                &restoredPartyRuntime,
                gameDataLoader.getStandardItemEnchantTable(),
                gameDataLoader.getSpecialItemEnchantTable(),
                &gameDataLoader.getChestTable(),
                selectedMap->outdoorMapData,
                selectedMap->outdoorMapDeltaData,
                selectedMap->outdoorWeatherProfile,
                selectedMap->eventRuntimeState,
                selectedMap->outdoorActorPreviewBillboardSet,
                selectedMap->outdoorLandMask,
                selectedMap->outdoorDecorationCollisionSet,
                selectedMap->outdoorActorCollisionSet,
                selectedMap->outdoorSpriteObjectCollisionSet,
                selectedMap->outdoorSpriteObjectBillboardSet);
            restoredWorld.restoreSnapshot(loadedSave->outdoorWorld);

            if (std::abs(restoredWorld.gameMinutes() - saveData.outdoorWorld.gameMinutes) > 0.01f)
            {
                failure = "world time did not roundtrip";
                return false;
            }

            if (restoredWorld.atmosphereState().sourceSkyTextureName != "sky06"
                || restoredWorld.atmosphereState().skyTextureName != "sunsetclouds"
                || restoredWorld.atmosphereState().weatherFlags != 1
                || restoredWorld.atmosphereState().fogWeakDistance != 2048
                || restoredWorld.atmosphereState().fogStrongDistance != 4096
                || restoredWorld.atmosphereState().isNight
                || std::abs(restoredWorld.atmosphereState().fogDensity - 0.5f) > 0.01f)
            {
                failure = "outdoor atmosphere state did not roundtrip";
                return false;
            }

            if (restoredWorld.worldItemCount() != scenario.world.worldItemCount())
            {
                failure = "world item count did not roundtrip";
                return false;
            }

            const OutdoorWorldRuntime::MapActorState *pRestoredActor = restoredWorld.mapActorState(0);

            if (pRestoredActor == nullptr || !pRestoredActor->isDead)
            {
                failure = "actor death state did not roundtrip";
                return false;
            }

            EventRuntimeState *pRestoredEventRuntimeState = restoredWorld.eventRuntimeState();

            if (pRestoredEventRuntimeState == nullptr
                || !pRestoredEventRuntimeState->variables.contains(0x1234u)
                || pRestoredEventRuntimeState->variables[0x1234u] != 99)
            {
                failure = "event runtime variables did not roundtrip";
                return false;
            }

            return true;
        }
    );

    runCase(
        "outdoor_atmosphere_prefers_delta_sky_and_matches_oe_time_windows",
        [&](std::string &failure)
        {
            if (!selectedMap || !selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.map.id = 999;
            modifiedMap.map.environmentName = "FOREST";
            modifiedMap.outdoorMapData = *selectedMap->outdoorMapData;
            modifiedMap.outdoorMapData->skyTexture = "plansky1";
            modifiedMap.outdoorMapDeltaData = selectedMap->outdoorMapDeltaData
                ? *selectedMap->outdoorMapDeltaData
                : MapDeltaData{};
            modifiedMap.outdoorMapDeltaData->locationTime.skyTextureName = "sky05";
            modifiedMap.outdoorMapDeltaData->locationTime.weatherFlags = 1;
            modifiedMap.outdoorMapDeltaData->locationTime.fogWeakDistance = 4096;
            modifiedMap.outdoorMapDeltaData->locationTime.fogStrongDistance = 8192;

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::AtmosphereState &initialAtmosphere = scenario.world.atmosphereState();

            if (initialAtmosphere.sourceSkyTextureName != "sky05"
                || initialAtmosphere.skyTextureName != "sky05"
                || initialAtmosphere.weatherFlags != 1
                || initialAtmosphere.fogWeakDistance != 4096
                || initialAtmosphere.fogStrongDistance != 8192)
            {
                failure = "delta location time did not win atmosphere source precedence";
                return false;
            }

            OutdoorWorldRuntime::Snapshot snapshot = scenario.world.snapshot();
            snapshot.gameMinutes = 4.0f * 60.0f;
            scenario.world.restoreSnapshot(snapshot);

            if (!scenario.world.atmosphereState().isNight || std::abs(scenario.world.atmosphereState().fogDensity - 1.0f) > 0.01f)
            {
                failure = "4AM atmosphere did not match OE night window";
                return false;
            }

            snapshot.gameMinutes = 5.0f * 60.0f + 30.0f;
            scenario.world.restoreSnapshot(snapshot);

            if (scenario.world.atmosphereState().isNight
                || std::abs(scenario.world.atmosphereState().fogDensity - 0.5f) > 0.01f)
            {
                failure = "5:30AM atmosphere did not match OE dawn window";
                return false;
            }

            const float dawnAmbient = scenario.world.atmosphereState().ambientBrightness;

            snapshot.gameMinutes = 12.0f * 60.0f;
            scenario.world.restoreSnapshot(snapshot);

            if (scenario.world.atmosphereState().fogDensity > 0.001f
                || scenario.world.atmosphereState().ambientBrightness <= dawnAmbient)
            {
                failure = "midday atmosphere did not brighten as expected";
                return false;
            }

            snapshot.gameMinutes = 20.0f * 60.0f + 30.0f;
            scenario.world.restoreSnapshot(snapshot);

            if (scenario.world.atmosphereState().isNight
                || std::abs(scenario.world.atmosphereState().fogDensity - 0.5f) > 0.01f
                || scenario.world.atmosphereState().skyTextureName != "sunsetclouds")
            {
                failure = "8:30PM atmosphere did not match OE dusk window";
                return false;
            }

            snapshot.gameMinutes = 22.0f * 60.0f;
            scenario.world.restoreSnapshot(snapshot);

            if (!scenario.world.atmosphereState().isNight
                || scenario.world.atmosphereState().skyTextureName != "sky6pm")
            {
                failure = "10PM atmosphere did not switch to the expected night sky";
                return false;
            }

            return true;
        }
    );

    runCase(
        "outdoor_atmosphere_falls_back_to_environment_mapping",
        [&](std::string &failure)
        {
            if (!selectedMap || !selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.map.id = 999;
            modifiedMap.map.environmentName = "MOUNTAIN";
            modifiedMap.outdoorMapData = *selectedMap->outdoorMapData;
            modifiedMap.outdoorMapData->skyTexture.clear();
            modifiedMap.outdoorMapDeltaData = selectedMap->outdoorMapDeltaData
                ? *selectedMap->outdoorMapDeltaData
                : MapDeltaData{};
            modifiedMap.outdoorMapDeltaData->locationTime.skyTextureName.clear();
            modifiedMap.outdoorMapDeltaData->locationTime.weatherFlags = 0;
            modifiedMap.outdoorMapDeltaData->locationTime.fogWeakDistance = 0;
            modifiedMap.outdoorMapDeltaData->locationTime.fogStrongDistance = 0;

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (scenario.world.atmosphereState().sourceSkyTextureName != "plansky1"
                || scenario.world.atmosphereState().skyTextureName != "sky05")
            {
                failure = "environment fallback did not resolve the expected sky";
                return false;
            }

            return true;
        }
    );

    runCase(
        "out01_true_mettle_house_event_171_enters_house_1",
        [&](std::string &failure)
        {
            GameDataLoader loader = gameDataLoader;

            if (!loader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, "out01.odm"))
            {
                failure = "could not load out01.odm";
                return false;
            }

            const std::optional<MapAssetInfo> &selectedMap = loader.getSelectedMap();

            if (!selectedMap)
            {
                failure = "selected map missing";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(loader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            if (!executeLocalEventInScenario(loader, *selectedMap, scenario, 171))
            {
                failure = "event 171 was unresolved";
                return false;
            }

            if (!scenario.pEventRuntimeState->pendingDialogueContext)
            {
                failure = "event 171 did not queue a house dialogue";
                return false;
            }

            const EventRuntimeState::PendingDialogueContext &context = *scenario.pEventRuntimeState->pendingDialogueContext;

            if (context.kind != DialogueContextKind::HouseService || context.sourceId != 1 || context.hostHouseId != 1)
            {
                failure = "event 171 did not enter house 1";
                return false;
            }

            return true;
        }
    );

    runCase(
        "outdoor_event_runtime_snow_override_reaches_atmosphere_state",
        [&](std::string &failure)
        {
            if (!selectedMap || !selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            OutdoorWorldRuntime::Snapshot snapshot = scenario.world.snapshot();

            if (!snapshot.eventRuntimeState.has_value())
            {
                failure = "scenario snapshot missing event runtime state";
                return false;
            }

            snapshot.eventRuntimeState->snowEnabled = true;
            scenario.world.restoreSnapshot(snapshot);

            if ((scenario.world.atmosphereState().weatherFlags & 0x2) == 0)
            {
                failure = "snow override did not set the outdoor snow weather bit";
                return false;
            }

            snapshot = scenario.world.snapshot();
            snapshot.eventRuntimeState->snowEnabled = false;
            scenario.world.restoreSnapshot(snapshot);

            if ((scenario.world.atmosphereState().weatherFlags & 0x2) != 0)
            {
                failure = "snow override did not clear the outdoor snow weather bit";
                return false;
            }

            return true;
        }
    );

    runCase(
        "outdoor_event_runtime_rain_override_reaches_atmosphere_state",
        [&](std::string &failure)
        {
            if (!selectedMap || !selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, *selectedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            OutdoorWorldRuntime::Snapshot snapshot = scenario.world.snapshot();

            if (!snapshot.eventRuntimeState.has_value())
            {
                failure = "scenario snapshot missing event runtime state";
                return false;
            }

            snapshot.eventRuntimeState->rainEnabled = true;
            scenario.world.restoreSnapshot(snapshot);

            if ((scenario.world.atmosphereState().weatherFlags & 0x4) == 0)
            {
                failure = "rain override did not set the outdoor rain weather bit";
                return false;
            }

            snapshot = scenario.world.snapshot();
            snapshot.eventRuntimeState->rainEnabled = false;
            scenario.world.restoreSnapshot(snapshot);

            if ((scenario.world.atmosphereState().weatherFlags & 0x4) != 0)
            {
                failure = "rain override did not clear the outdoor rain weather bit";
                return false;
            }

            return true;
        }
    );

    runCase(
        "outdoor_daily_fog_rollover_happens_at_3am_not_midnight",
        [&](std::string &failure)
        {
            if (!selectedMap || !selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = selectedMap->outdoorMapDeltaData
                ? *selectedMap->outdoorMapDeltaData
                : MapDeltaData{};
            modifiedMap.outdoorMapDeltaData->locationTime.weatherFlags = 1;
            modifiedMap.outdoorMapDeltaData->locationTime.fogWeakDistance = 4096;
            modifiedMap.outdoorMapDeltaData->locationTime.fogStrongDistance = 8192;

            OutdoorWeatherProfile profile = {};
            profile.fogMode = OutdoorFogMode::DailyRandom;
            profile.smallFogChance = 0;
            profile.averageFogChance = 100;
            profile.denseFogChance = 0;
            profile.averageFog = {0, 4096};
            modifiedMap.outdoorWeatherProfile = profile;

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            OutdoorWorldRuntime::Snapshot snapshot = scenario.world.snapshot();
            snapshot.gameMinutes = 23.0f * 60.0f + 59.0f;
            scenario.world.restoreSnapshot(snapshot);
            scenario.world.advanceGameMinutes(2.0f);

            if (scenario.world.atmosphereState().fogWeakDistance != 4096
                || scenario.world.atmosphereState().fogStrongDistance != 8192)
            {
                failure = "daily fog changed at midnight instead of 3AM";
                return false;
            }

            snapshot = scenario.world.snapshot();
            snapshot.gameMinutes = 2.0f * 60.0f + 59.0f;
            snapshot.atmosphere.fogWeakDistance = 4096;
            snapshot.atmosphere.fogStrongDistance = 8192;
            snapshot.atmosphere.weatherFlags |= 1;
            scenario.world.restoreSnapshot(snapshot);
            scenario.world.advanceGameMinutes(2.0f);

            if ((scenario.world.atmosphereState().weatherFlags & 0x1) == 0
                || scenario.world.atmosphereState().fogWeakDistance != 0
                || scenario.world.atmosphereState().fogStrongDistance != 4096)
            {
                failure = "daily fog did not roll over to the authored 3AM state";
                return false;
            }

            return true;
        }
    );

    runCase(
        "outdoor_red_fog_profile_tints_atmosphere_state",
        [&](std::string &failure)
        {
            if (!selectedMap || !selectedMap->outdoorMapData)
            {
                failure = "selected map missing outdoor data";
                return false;
            }

            MapAssetInfo modifiedMap = *selectedMap;
            modifiedMap.outdoorMapDeltaData = selectedMap->outdoorMapDeltaData
                ? *selectedMap->outdoorMapDeltaData
                : MapDeltaData{};
            modifiedMap.outdoorMapDeltaData->locationTime.weatherFlags = 1;
            modifiedMap.outdoorMapDeltaData->locationTime.fogWeakDistance = 0;
            modifiedMap.outdoorMapDeltaData->locationTime.fogStrongDistance = 2048;

            OutdoorWeatherProfile profile = {};
            profile.alwaysFoggy = true;
            profile.redFog = true;
            profile.defaultFog = {0, 2048};
            modifiedMap.outdoorWeatherProfile = profile;

            RegressionScenario scenario = {};

            if (!initializeRegressionScenario(gameDataLoader, modifiedMap, scenario))
            {
                failure = "scenario init failed";
                return false;
            }

            const OutdoorWorldRuntime::AtmosphereState &atmosphere = scenario.world.atmosphereState();
            const uint32_t clearColorAbgr = atmosphere.clearColorAbgr;
            const uint32_t red = clearColorAbgr & 0xffu;
            const uint32_t green = (clearColorAbgr >> 8) & 0xffu;
            const uint32_t blue = (clearColorAbgr >> 16) & 0xffu;

            if (!atmosphere.redFog
                || (atmosphere.weatherFlags & 0x1) == 0
                || atmosphere.fogStrongDistance != 2048
                || red <= green
                || red <= blue)
            {
                failure = "red fog profile did not reach the outdoor atmosphere state";
                return false;
            }

            return true;
        }
    );

    SharedHeadlessApplicationSession out01StandaloneSession(m_config);

    runCase(
        "app_background_music_follows_selected_map",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01StandaloneSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01StandaloneSession.application;

            const std::optional<MapAssetInfo> &initialMap =
                GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!initialMap)
            {
                failure = "application did not select an initial map";
                return false;
            }

            if (GameApplicationTestAccess::gameAudioSystem(application).currentBackgroundMusicTrack()
                != initialMap->map.redbookTrack)
            {
                failure = "initial map music track did not match the selected map";
                return false;
            }

            if (!loadHeadlessGameApplicationMap(application, assetFileSystem, "out02.odm", failure))
            {
                return false;
            }

            for (int iteration = 0; iteration < 4; ++iteration)
            {
                GameApplicationTestAccess::gameAudioSystem(application).update(0.0f, 0.0f, 0.0f, 1.0f);
            }

            const std::optional<MapAssetInfo> &secondMap =
                GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!secondMap)
            {
                failure = "application did not select the second map";
                return false;
            }

            if (GameApplicationTestAccess::gameAudioSystem(application).currentBackgroundMusicTrack()
                != secondMap->map.redbookTrack)
            {
                failure = "second map music track did not match the selected map";
                return false;
            }

            return true;
        }
    );

    SharedHeadlessApplicationSession out01ViewSession(m_config);

    runCase(
        "app_house_entry_pauses_background_music_until_exit",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01ViewSession.application;

            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
            const HouseEntry *pHouseEntry = GameApplicationTestAccess::gameDataLoader(application).getHouseTable().get(1);

            if (pWorld == nullptr || pEventRuntimeState == nullptr || pHouseEntry == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            const std::optional<MapAssetInfo> &selectedMap =
                GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!selectedMap)
            {
                failure = "application did not select a gameplay map";
                return false;
            }

            const int outdoorTrack = selectedMap->map.redbookTrack;

            if (GameApplicationTestAccess::gameAudioSystem(application).currentBackgroundMusicTrack() != outdoorTrack)
            {
                failure = "initial outdoor music track did not match the selected map";
                return false;
            }

            if (GameApplicationTestAccess::gameAudioSystem(application).isBackgroundMusicPaused())
            {
                failure = "background music started paused before entering a house";
                return false;
            }

            const float openMinuteOfDay = static_cast<float>((pHouseEntry->openHour % 24) * 60);
            const float openGameMinutes = nextGameMinuteAtOrAfter(pWorld->gameMinutes(), openMinuteOfDay);
            pWorld->advanceGameMinutes(openGameMinutes - pWorld->gameMinutes());

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = pHouseEntry->id;
            context.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->dialogueState.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->pendingDialogueContext = std::move(context);

            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);
            GameApplicationTestAccess::updateHouseVideoPlayback(application, 0.016f);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "house dialog did not open for music pause test";
                return false;
            }

            if (!GameApplicationTestAccess::gameAudioSystem(application).isBackgroundMusicPaused())
            {
                failure = "background music did not pause after entering a house";
                return false;
            }

            if (GameApplicationTestAccess::gameAudioSystem(application).currentBackgroundMusicTrack() != outdoorTrack)
            {
                failure = "house entry cleared the outdoor music track instead of preserving it";
                return false;
            }

            GameApplicationTestAccess::handleDialogueCloseRequest(application);
            GameApplicationTestAccess::updateHouseVideoPlayback(application, 0.016f);

            if (GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "house dialog did not close in music pause test";
                return false;
            }

            if (GameApplicationTestAccess::gameAudioSystem(application).isBackgroundMusicPaused())
            {
                failure = "background music did not resume after leaving the house";
                return false;
            }

            if (GameApplicationTestAccess::gameAudioSystem(application).currentBackgroundMusicTrack() != outdoorTrack)
            {
                failure = "outdoor music track changed after leaving the house";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_f5_time_advance_reduces_party_buff_duration",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01StandaloneSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01StandaloneSession.application;
            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);
            OutdoorWorldRuntime *pWorldRuntime = GameApplicationTestAccess::outdoorWorldRuntime(application);

            if (pPartyRuntime == nullptr || pWorldRuntime == nullptr)
            {
                failure = "application runtimes were not initialized";
                return false;
            }

            Party &party = pPartyRuntime->party();
            party.applyPartyBuff(PartyBuffId::WizardEye, 7200.0f, 1, 0, 0, SkillMastery::None, 0);
            const PartyBuffState *pInitialBuff = party.partyBuff(PartyBuffId::WizardEye);

            if (pInitialBuff == nullptr || std::abs(pInitialBuff->remainingSeconds - 7200.0f) > 0.01f)
            {
                failure = "could not seed the initial party buff";
                return false;
            }

            const float initialGameMinutes = pWorldRuntime->gameMinutes();

            if (!GameApplicationTestAccess::advanceTimeByOneHourHotkey(application))
            {
                failure = "F5-style time advance failed";
                return false;
            }

            const PartyBuffState *pAdvancedBuff = party.partyBuff(PartyBuffId::WizardEye);

            if (std::abs(pWorldRuntime->gameMinutes() - (initialGameMinutes + 60.0f)) > 0.01f)
            {
                failure = "world time did not advance by one hour";
                return false;
            }

            if (pAdvancedBuff == nullptr || std::abs(pAdvancedBuff->remainingSeconds - 3600.0f) > 0.01f)
            {
                failure = "party buff duration did not drop by one hour";
                return false;
            }

            return true;
        }
    );

    SharedHeadlessApplicationSession out02ViewSession(m_config);

    runCase(
        "out02_boundary_transition_opens_west_and_east_neighbor_dialogs",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out02ViewSession,
                    assetFileSystem,
                    "out02.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out02ViewSession.application;

            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);
            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            const MapStatsEntry *pRavenshore = gameDataLoader.getMapStats().findByFileName("Out02.odm");

            if (pPartyRuntime == nullptr || pWorld == nullptr || pRavenshore == nullptr)
            {
                failure = "Out02 runtime state is incomplete";
                return false;
            }

            const OutdoorMoveState initialMoveState = pPartyRuntime->movementState();
            const float bodyRadius = 37.0f;
            const auto exerciseBoundaryTransition =
                [&](MapBoundaryEdge edge, float x, float y, float yawRadians, const std::string &expectedTitle) -> bool
            {
                pPartyRuntime->teleportTo(x, y, initialMoveState.footZ);
                EventRuntimeState *pEventRuntimeState = pWorld->eventRuntimeState();

                if (pEventRuntimeState == nullptr)
                {
                    failure = "missing event runtime state";
                    return false;
                }

                pEventRuntimeState->pendingDialogueContext.reset();
                pEventRuntimeState->pendingMapMove.reset();
                pEventRuntimeState->messages.clear();

                const OutdoorMovementInput movementInput = {
                    true,
                    false,
                    false,
                    false,
                    false,
                    false,
                    false,
                    false,
                    yawRadians,
                    0.0f
                };

                const OutdoorSceneRuntime::AdvanceFrameResult frameAdvanceResult =
                    GameApplicationTestAccess::advanceOutdoorSceneFrame(application, movementInput, 0.1f);

                if (!frameAdvanceResult.shouldOpenEventDialog)
                {
                    failure = "boundary transition did not request an event dialog for edge "
                        + std::to_string(static_cast<int>(edge));
                    return false;
                }

                GameApplicationTestAccess::openPendingEventDialog(application, frameAdvanceResult.previousMessageCount, true);

                if (!GameApplicationTestAccess::hasActiveEventDialog(application))
                {
                    failure = "boundary transition did not open an active event dialog";
                    return false;
                }

                const EventDialogContent &dialog = GameApplicationTestAccess::activeEventDialog(application);

                if (dialog.presentation != EventDialogPresentation::Transition || dialog.title != expectedTitle)
                {
                    failure = "boundary transition dialog did not target " + expectedTitle;
                    return false;
                }

                GameApplicationTestAccess::setEventDialogSelectionIndex(application, 1);
                GameApplicationTestAccess::executeActiveDialogAction(application);
                return true;
            };

            if (!exerciseBoundaryTransition(
                    MapBoundaryEdge::West,
                    static_cast<float>(pRavenshore->outdoorBounds.minX) + bodyRadius + 1.0f,
                    initialMoveState.y,
                    3.14159265358979323846f,
                    "Garrote Gorge"))
            {
                return false;
            }

            if (!exerciseBoundaryTransition(
                    MapBoundaryEdge::East,
                    static_cast<float>(pRavenshore->outdoorBounds.maxX) - bodyRadius - 1.0f,
                    initialMoveState.y,
                    0.0f,
                    "Shadowspire"))
            {
                return false;
            }

            return true;
        }
    );

    runCase(
        "map_transition_dialog_uses_transition_presentation_and_oe_copy",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out02ViewSession,
                    assetFileSystem,
                    "out02.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out02ViewSession.application;

            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
            const MapStatsEntry *pOriginMap = gameDataLoader.getMapStats().findByFileName("Out02.odm");
            const MapStatsEntry *pDestinationMap = gameDataLoader.getMapStats().findByFileName("Out06.odm");

            if (pWorld == nullptr || pEventRuntimeState == nullptr || pOriginMap == nullptr || pDestinationMap == nullptr)
            {
                failure = "missing transition dialog test state";
                return false;
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::MapTransition;
            context.sourceId = static_cast<uint32_t>(MapBoundaryEdge::East);
            pEventRuntimeState->pendingDialogueContext = context;
            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "map transition dialog did not open";
                return false;
            }

            const EventDialogContent &dialog = GameApplicationTestAccess::activeEventDialog(application);

            if (!dialog.isActive
                || dialog.presentation != EventDialogPresentation::Transition
                || dialog.participantVisual != EventDialogParticipantVisual::MapIcon)
            {
                failure = "map transition dialog did not use the dedicated transition presentation";
                return false;
            }

            if (dialog.title != pDestinationMap->name)
            {
                failure = "map transition dialog did not use the destination map title";
                return false;
            }

            if (!dialogContainsText(dialog, "It will take 1 day to travel to " + pDestinationMap->name + ".")
                || !dialogContainsText(dialog, "Do you wish to leave " + pOriginMap->name + "?"))
            {
                failure = "map transition dialog did not use the expected OE-style body text";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "OK") || !dialogHasActionLabel(dialog, "Close"))
            {
                failure = "map transition dialog did not expose the standard OK / Close actions";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_tavern_rent_room_closes_dialog_runs_rest_ui_and_wakes_at_6am",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out02ViewSession,
                    assetFileSystem,
                    "out02.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out02ViewSession.application;

            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
            const HouseEntry *pTavernHouse = GameApplicationTestAccess::gameDataLoader(application).getHouseTable().get(107);

            if (pWorld == nullptr || pPartyRuntime == nullptr || pEventRuntimeState == nullptr || pTavernHouse == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            Party &party = pPartyRuntime->party();
            Character *pActiveMember = party.activeMember();

            if (pActiveMember == nullptr)
            {
                failure = "missing active member";
                return false;
            }

            party.addGold(1000);
            party.applyPartyBuff(PartyBuffId::WizardEye, 600.0f, 1, 0, 0, SkillMastery::None, 0);
            pActiveMember->health = std::max(1, pActiveMember->health - 17);
            pActiveMember->spellPoints = std::max(0, pActiveMember->spellPoints - 4);
            pActiveMember->conditions.set(static_cast<size_t>(CharacterCondition::Asleep));
            pActiveMember->recoverySecondsRemaining = 2.0f;

            const float targetGameMinutes = nextGameMinuteAtOrAfter(pWorld->gameMinutes(), 16.0f * 60.0f + 30.0f);
            pWorld->advanceGameMinutes(targetGameMinutes - pWorld->gameMinutes());
            const float initialGameMinutes = pWorld->gameMinutes();
            const float expectedRestMinutes = 13.0f * 60.0f + 30.0f;

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = pTavernHouse->id;
            context.hostHouseId = pTavernHouse->id;
            pEventRuntimeState->dialogueState.hostHouseId = pTavernHouse->id;
            pEventRuntimeState->pendingDialogueContext = std::move(context);

            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "tavern did not open an active dialog";
                return false;
            }

            const EventDialogContent &dialog = GameApplicationTestAccess::activeEventDialog(application);
            const std::string expectedRoomActionLabel =
                "Rent room for " + std::to_string(PriceCalculator::tavernRoomPrice(pActiveMember, *pTavernHouse)) + " gold";

            if (dialog.actions.empty() || dialog.actions.front().label != expectedRoomActionLabel)
            {
                failure = "tavern dialog did not expose rent room as the first action";
                return false;
            }

            GameApplicationTestAccess::setEventDialogSelectionIndex(application, 0);
            GameApplicationTestAccess::executeActiveDialogAction(application);

            if (GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "rent room did not close the active dialog";
                return false;
            }

            if (!GameApplicationTestAccess::isRestScreenActive(application))
            {
                failure = "rent room did not open the rest screen";
                return false;
            }

            if (std::abs(GameApplicationTestAccess::restRemainingMinutes(application) - expectedRestMinutes) > 0.01f)
            {
                failure = "rest screen did not use the OE tavern rest duration";
                return false;
            }

            if (std::abs(pWorld->gameMinutes() - initialGameMinutes) > 0.01f)
            {
                failure = "rent room advanced time immediately instead of waiting in the rest screen";
                return false;
            }

            if (pActiveMember->recoverySecondsRemaining != 2.0f
                || !pActiveMember->conditions.test(static_cast<size_t>(CharacterCondition::Asleep))
                || !party.hasPartyBuff(PartyBuffId::WizardEye))
            {
                failure = "rent room applied recovery before the rest screen completed";
                return false;
            }

            GameApplicationTestAccess::updateRestScreen(application, 5.0f);

            if (GameApplicationTestAccess::isRestScreenActive(application))
            {
                failure = "rest screen did not close after the inn rest completed";
                return false;
            }

            if (std::abs(pWorld->gameMinutes() - (initialGameMinutes + expectedRestMinutes)) > 0.01f)
            {
                failure = "inn rest advanced an unexpected amount of time";
                return false;
            }

            const float wakeMinuteOfDay = std::fmod(std::max(0.0f, pWorld->gameMinutes()), 1440.0f);

            if (std::abs(wakeMinuteOfDay - 360.0f) > 0.01f)
            {
                failure = "inn rest did not finish at 6:00 AM";
                return false;
            }

            if (pActiveMember->health != pActiveMember->maxHealth + pActiveMember->magicalBonuses.maxHealth
                || pActiveMember->spellPoints != pActiveMember->maxSpellPoints + pActiveMember->magicalBonuses.maxSpellPoints
                || pActiveMember->recoverySecondsRemaining != 0.0f
                || pActiveMember->conditions.test(static_cast<size_t>(CharacterCondition::Asleep))
                || party.hasPartyBuff(PartyBuffId::WizardEye))
            {
                failure = "inn rest did not apply full rest recovery on completion";
                return false;
            }

            return true;
        }
    );

    SharedHeadlessApplicationSession out01PendingMapMoveSession(m_config);

    runCase(
        "app_transport_map_move_applies_cross_map_heading",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01PendingMapMoveSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01PendingMapMoveSession.application;
            EventRuntimeState *pEventRuntimeState = GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState();

            if (pEventRuntimeState == nullptr)
            {
                failure = "missing application event runtime state";
                return false;
            }

            EventRuntimeState::PendingMapMove pendingMapMove = {};
            pendingMapMove.mapName = std::string("Out02.odm");
            pendingMapMove.directionDegrees = 135;
            pendingMapMove.useMapStartPosition = true;
            pEventRuntimeState->pendingMapMove = std::move(pendingMapMove);

            if (!GameApplicationTestAccess::processPendingMapMove(application))
            {
                failure = "application did not process the pending transport map move";
                return false;
            }

            const std::optional<MapAssetInfo> &loadedMap = GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!loadedMap || toLowerCopy(loadedMap->map.fileName) != "out02.odm")
            {
                failure = "transport map move did not load the destination map";
                return false;
            }

            const float expectedYawRadians = 135.0f * 3.14159265358979323846f / 180.0f;

            if (angleDistanceRadians(GameApplicationTestAccess::cameraYawRadians(application), expectedYawRadians) > 0.0001f)
            {
                failure = "transport map move did not apply the arrival heading";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_pending_map_move_loads_outdoor_runtime_at_explicit_coordinates",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01PendingMapMoveSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01PendingMapMoveSession.application;
            EventRuntimeState *pEventRuntimeState = GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState();

            if (pEventRuntimeState == nullptr)
            {
                failure = "missing application event runtime state";
                return false;
            }

            EventRuntimeState::PendingMapMove pendingMapMove = {};
            pendingMapMove.mapName = std::string("Out02.odm");
            pendingMapMove.x = -15104;
            pendingMapMove.y = -22200;
            pendingMapMove.z = 192;
            pendingMapMove.directionDegrees = 180;
            pendingMapMove.useMapStartPosition = false;
            pEventRuntimeState->pendingMapMove = std::move(pendingMapMove);

            if (!GameApplicationTestAccess::processPendingMapMove(application))
            {
                failure = "application did not process the explicit outdoor pending map move";
                return false;
            }

            const std::optional<MapAssetInfo> &loadedMap = GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!loadedMap || toLowerCopy(loadedMap->map.fileName) != "out02.odm")
            {
                failure = "explicit outdoor pending map move did not load the destination map";
                return false;
            }

            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);

            if (pPartyRuntime == nullptr)
            {
                failure = "destination outdoor runtime is missing after explicit outdoor pending map move";
                return false;
            }

            const OutdoorMoveState &moveState = pPartyRuntime->movementState();

            if (std::abs(moveState.x - (-15104.0f)) > 0.01f
                || std::abs(moveState.y - (-22200.0f)) > 0.01f)
            {
                failure = "explicit outdoor pending map move did not apply the expected arrival position";
                return false;
            }

            const float expectedYawRadians = 180.0f * 3.14159265358979323846f / 180.0f;

            if (angleDistanceRadians(GameApplicationTestAccess::cameraYawRadians(application), expectedYawRadians) > 0.0001f)
            {
                failure = "explicit outdoor pending map move did not apply the arrival heading";
                return false;
            }

            return true;
        }
    );

    runCase(
        "outdoor_scene_start_uses_authored_party_start_facing",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01StandaloneSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01StandaloneSession.application;

            if (angleDistanceRadians(GameApplicationTestAccess::cameraYawRadians(application), 0.0f) > 0.0001f)
            {
                failure = "outdoor startup did not use the authored party start facing";
                return false;
            }

            return true;
        }
    );

    runCase(
        "outdoor_scene_forward_motion_follows_positive_world_yaw",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01StandaloneSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01StandaloneSession.application;

            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);

            if (pPartyRuntime == nullptr)
            {
                failure = "missing outdoor party runtime";
                return false;
            }

            const OutdoorMoveState startState = pPartyRuntime->movementState();
            const OutdoorMovementInput forwardInput = {
                true,
                false,
                false,
                false,
                false,
                false,
                false,
                false,
                0.0f,
                0.0f
            };

            GameApplicationTestAccess::setCameraAngles(application, 0.0f, 0.0f);
            GameApplicationTestAccess::advanceOutdoorSceneFrame(application, forwardInput, 0.1f);
            const OutdoorMoveState eastState = pPartyRuntime->movementState();

            if (eastState.x <= startState.x + 1.0f || std::abs(eastState.y - startState.y) > 64.0f)
            {
                failure = "forward movement at yaw 0 did not move east in world space";
                return false;
            }

            pPartyRuntime->teleportTo(startState.x, startState.y, startState.footZ);

            OutdoorMovementInput northInput = forwardInput;
            northInput.yawRadians = 3.14159265358979323846f * 0.5f;
            GameApplicationTestAccess::setCameraAngles(application, 3.14159265358979323846f * 0.5f, 0.0f);
            GameApplicationTestAccess::advanceOutdoorSceneFrame(application, northInput, 0.1f);
            const OutdoorMoveState northState = pPartyRuntime->movementState();

            if (northState.y <= startState.y + 1.0f || std::abs(northState.x - startState.x) > 64.0f)
            {
                failure = "forward movement at yaw +pi/2 did not move north in world space";
                return false;
            }

            return true;
        }
    );

    SharedHeadlessApplicationSession out01DataSession(m_config);

    runCase(
        "outdoor_support_floor_resolves_the_windling_at_original_coordinates",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01DataSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01DataSession.application;

            const std::optional<MapAssetInfo> &loadedMap = GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!loadedMap || !loadedMap->outdoorMapData)
            {
                failure = "missing outdoor map data for Windling support-floor test";
                return false;
            }

            constexpr float WindlingX = 16973.0f;
            constexpr float WindlingY = 21513.0f;
            constexpr float WindlingZ = 369.0f;
            constexpr size_t WindlingBModelIndex = 126;
            const OutdoorSupportFloorSample support = sampleOutdoorSupportFloor(
                *loadedMap->outdoorMapData,
                WindlingX,
                WindlingY,
                WindlingZ,
                std::numeric_limits<float>::max(),
                5.0f);

            if (!support.fromBModel)
            {
                failure = "Windling support-floor sample did not resolve to a bmodel face; bmodel="
                    + std::to_string(support.bModelIndex)
                    + " height=" + std::to_string(support.height);
                return false;
            }

            if (support.bModelIndex != WindlingBModelIndex)
            {
                failure = "Windling support-floor sample did not resolve to runtime bmodel 126 (original 127); actual="
                    + std::to_string(support.bModelIndex)
                    + " height=" + std::to_string(support.height);
                return false;
            }

            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);

            if (pPartyRuntime == nullptr)
            {
                failure = "missing outdoor party runtime for Windling support-floor test";
                return false;
            }

            pPartyRuntime->teleportTo(WindlingX, WindlingY, WindlingZ);
            const OutdoorMoveState &moveState = pPartyRuntime->movementState();

            if (moveState.supportKind != OutdoorSupportKind::BModelFace)
            {
                failure = "party support kind on Windling was not a bmodel face; kind="
                    + std::to_string(static_cast<int>(moveState.supportKind))
                    + " bmodel=" + std::to_string(moveState.supportBModelIndex);
                return false;
            }

            if (moveState.supportBModelIndex != WindlingBModelIndex)
            {
                failure = "party support bmodel on Windling was not runtime bmodel 126 (original 127); actual="
                    + std::to_string(moveState.supportBModelIndex);
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_boundary_map_transition_confirm_preserves_world_direction_on_all_edges",
        [&](std::string &failure)
        {
            struct DirectionCase
            {
                const char *pOriginMap;
                MapBoundaryEdge edge;
                const char *pExpectedDestinationMap;
                int expectedDirectionDegrees;
                float expectedYawRadians;
            };

            const std::array<DirectionCase, 4> cases = {{
                {"Out02.odm", MapBoundaryEdge::North, "Out03.odm", 90, 1.57079632679489661923f},
                {"Out03.odm", MapBoundaryEdge::South, "Out02.odm", 270, -1.57079632679489661923f},
                {"Out02.odm", MapBoundaryEdge::East, "Out06.odm", 0, 0.0f},
                {"Out02.odm", MapBoundaryEdge::West, "Out05.odm", 180, 3.14159265358979323846f}
            }};

            for (const DirectionCase &directionCase : cases)
            {
                if (!prepareSharedHeadlessGameApplication(
                        out02ViewSession,
                        assetFileSystem,
                        directionCase.pOriginMap,
                        true,
                        failure))
                {
                    return false;
                }

                GameApplication &application = out02ViewSession.application;

                OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
                EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;

                if (pWorld == nullptr || pEventRuntimeState == nullptr)
                {
                    failure = std::string("application state is incomplete for ")
                        + directionCase.pOriginMap;
                    return false;
                }

                EventRuntimeState::PendingDialogueContext context = {};
                context.kind = DialogueContextKind::MapTransition;
                context.sourceId = static_cast<uint32_t>(directionCase.edge);
                pEventRuntimeState->pendingDialogueContext = context;
                pEventRuntimeState->pendingMapMove.reset();
                pEventRuntimeState->messages.clear();

                GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

                if (!GameApplicationTestAccess::hasActiveEventDialog(application))
                {
                    failure = std::string("map transition did not open an active dialog for ")
                        + directionCase.pOriginMap;
                    return false;
                }

                GameApplicationTestAccess::setEventDialogSelectionIndex(application, 0);
                GameApplicationTestAccess::executeActiveDialogAction(application);

                const EventRuntimeState::PendingMapMove *pPendingMapMove = pWorld->pendingMapMove();

                if (pPendingMapMove == nullptr
                    || !pPendingMapMove->mapName.has_value()
                    || *pPendingMapMove->mapName != directionCase.pExpectedDestinationMap)
                {
                    failure = std::string("map transition confirm queued the wrong destination for ")
                        + directionCase.pOriginMap;
                    return false;
                }

                if (!pPendingMapMove->directionDegrees.has_value()
                    || *pPendingMapMove->directionDegrees != directionCase.expectedDirectionDegrees)
                {
                    failure = std::string("map transition confirm queued the wrong arrival heading for ")
                        + directionCase.pOriginMap;
                    return false;
                }

                if (!GameApplicationTestAccess::processPendingMapMove(application))
                {
                    failure = std::string("application did not process the confirmed map transition for ")
                        + directionCase.pOriginMap;
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap =
                    GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

                if (!loadedMap || toLowerCopy(loadedMap->map.fileName) != toLowerCopy(directionCase.pExpectedDestinationMap))
                {
                    failure = std::string("map transition confirm did not load the expected destination for ")
                        + directionCase.pOriginMap;
                    return false;
                }

                if (angleDistanceRadians(GameApplicationTestAccess::cameraYawRadians(application), directionCase.expectedYawRadians)
                    > 0.0001f)
                {
                    failure = std::string("map transition confirm did not preserve world facing for ")
                        + directionCase.pOriginMap;
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "app_map_transition_confirm_applies_oe_travel_side_effects",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out02ViewSession,
                    assetFileSystem,
                    "out02.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out02ViewSession.application;

            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;

            if (pWorld == nullptr || pPartyRuntime == nullptr || pEventRuntimeState == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            const MapStatsEntry *pCurrentMap =
                GameApplicationTestAccess::gameDataLoader(application).getMapStats().findByFileName("Out02.odm");

            if (pCurrentMap == nullptr || !pCurrentMap->eastTransition.has_value())
            {
                failure = "missing Out02 east transition";
                return false;
            }

            const int expectedTravelDays = pCurrentMap->eastTransition->travelDays;
            const float initialGameMinutes = pWorld->gameMinutes();
            Party &party = pPartyRuntime->party();
            Character *pActiveMember = party.activeMember();

            if (pActiveMember == nullptr)
            {
                failure = "missing active member";
                return false;
            }

            party.addFood(3 - party.food());
            const int initialFood = party.food();
            party.applyPartyBuff(PartyBuffId::TorchLight, 600.0f, 1, 0, 0, SkillMastery::None, 0);
            pActiveMember->health = std::max(1, pActiveMember->health - 23);
            pActiveMember->spellPoints = std::max(0, pActiveMember->spellPoints - 7);
            pActiveMember->recoverySecondsRemaining = 2.0f;
            pActiveMember->conditions.set(static_cast<size_t>(CharacterCondition::Fear));

            const float bodyRadius = 37.0f;
            const OutdoorMoveState initialMoveState = pPartyRuntime->movementState();
            pPartyRuntime->teleportTo(
                static_cast<float>(pCurrentMap->outdoorBounds.maxX) - bodyRadius - 1.0f,
                initialMoveState.y,
                initialMoveState.footZ);

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::MapTransition;
            context.sourceId = static_cast<uint32_t>(MapBoundaryEdge::East);
            pEventRuntimeState->pendingDialogueContext = context;
            pEventRuntimeState->pendingMapMove.reset();
            pEventRuntimeState->messages.clear();

            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "map transition did not open an active dialog";
                return false;
            }

            const EventDialogContent &dialog = GameApplicationTestAccess::activeEventDialog(application);

            if (dialog.presentation != EventDialogPresentation::Transition)
            {
                failure = "map transition dialog did not use transition presentation";
                return false;
            }

            if (dialog.actions.size() < 2
                || dialog.actions[0].label != "OK"
                || dialog.actions[1].label != "Close")
            {
                failure = "map transition dialog did not expose the standard OK / Close actions";
                return false;
            }

            GameApplicationTestAccess::setEventDialogSelectionIndex(application, 0);
            GameApplicationTestAccess::executeActiveDialogAction(application);

            if (GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "map transition confirm did not close the active dialog";
                return false;
            }

            const float expectedGameMinutes =
                initialGameMinutes + static_cast<float>(expectedTravelDays) * 1440.0f;

            if (std::abs(pWorld->gameMinutes() - expectedGameMinutes) > 0.01f)
            {
                failure = "map transition confirm did not advance travel time";
                return false;
            }

            if (party.food() != std::max(0, initialFood - expectedTravelDays))
            {
                failure = "map transition confirm did not consume travel food";
                return false;
            }

            const int expectedHealth = pActiveMember->maxHealth + pActiveMember->magicalBonuses.maxHealth;
            const int expectedSpellPoints =
                pActiveMember->maxSpellPoints + pActiveMember->magicalBonuses.maxSpellPoints;

            if (pActiveMember->health != expectedHealth
                || pActiveMember->spellPoints != expectedSpellPoints
                || pActiveMember->recoverySecondsRemaining != 0.0f
                || pActiveMember->conditions.test(static_cast<size_t>(CharacterCondition::Fear))
                || party.hasPartyBuff(PartyBuffId::TorchLight))
            {
                failure = "map transition confirm did not apply full-rest travel recovery";
                return false;
            }

            const EventRuntimeState::PendingMapMove *pPendingMapMove = pWorld->pendingMapMove();

            if (pPendingMapMove == nullptr
                || !pPendingMapMove->mapName.has_value()
                || *pPendingMapMove->mapName != "Out06.odm")
            {
                failure = "map transition confirm did not queue the destination map move";
                return false;
            }

            if (!pPendingMapMove->directionDegrees.has_value() || *pPendingMapMove->directionDegrees != 0)
            {
                failure = "map transition confirm did not preserve the crossed boundary facing";
                return false;
            }

            if (!GameApplicationTestAccess::processPendingMapMove(application))
            {
                failure = "application did not process the confirmed map transition";
                return false;
            }

            const std::optional<MapAssetInfo> &loadedMap = GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!loadedMap || toLowerCopy(loadedMap->map.fileName) != "out06.odm")
            {
                failure = "map transition confirm did not load the destination outdoor map";
                return false;
            }

            const float expectedYawRadians = 0.0f;

            if (angleDistanceRadians(GameApplicationTestAccess::cameraYawRadians(application), expectedYawRadians) > 0.0001f)
            {
                failure = "map transition confirm did not face east after an eastward boundary arrival";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_map_transition_cancel_leaves_state_unchanged",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out02ViewSession,
                    assetFileSystem,
                    "out02.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out02ViewSession.application;

            const std::filesystem::path autosavePath = "/tmp/openyamm_edge_travel_cancel_autosave.oysav";
            std::error_code removeError;
            std::filesystem::remove(autosavePath, removeError);
            GameApplicationTestAccess::setAutosavePath(application, autosavePath);

            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;

            if (pWorld == nullptr || pPartyRuntime == nullptr || pEventRuntimeState == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            Party &party = pPartyRuntime->party();
            Character *pActiveMember = party.activeMember();

            if (pActiveMember == nullptr)
            {
                failure = "missing active member";
                return false;
            }

            pPartyRuntime->teleportTo(26000.0f, 0.0f, pPartyRuntime->movementState().footZ);
            const float initialGameMinutes = pWorld->gameMinutes();
            const int initialFood = party.food();
            const int initialHealth = pActiveMember->health;
            const int initialSpellPoints = pActiveMember->spellPoints;

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::MapTransition;
            context.sourceId = static_cast<uint32_t>(MapBoundaryEdge::East);
            pEventRuntimeState->pendingDialogueContext = context;

            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "map transition did not open an active dialog";
                return false;
            }

            GameApplicationTestAccess::handleDialogueCloseRequest(application);

            if (GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "map transition cancel did not close the active dialog";
                return false;
            }

            if (std::filesystem::exists(autosavePath))
            {
                failure = "map transition cancel unexpectedly created an autosave";
                return false;
            }

            if (std::abs(pWorld->gameMinutes() - initialGameMinutes) > 0.01f
                || party.food() != initialFood
                || pActiveMember->health != initialHealth
                || pActiveMember->spellPoints != initialSpellPoints)
            {
                failure = "map transition cancel changed party state";
                return false;
            }

            const OutdoorMoveState &moveState = pPartyRuntime->movementState();

            if (moveState.x >= 25646.0f)
            {
                failure = "map transition cancel did not clamp the party back inside the outdoor bounds";
                return false;
            }

            if (pWorld->pendingMapMove() != nullptr)
            {
                failure = "map transition cancel still queued a map move";
                return false;
            }

            return true;
        }
    );

    runCase(
        "game_audio_nonresettable_common_sounds_do_not_restart_active_impact_clip",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01StandaloneSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01StandaloneSession.application;
            GameAudioSystem &audioSystem = GameApplicationTestAccess::gameAudioSystem(application);
            const bool playedFirst = audioSystem.playCommonSoundNonResettable(
                SoundId::DullStrike,
                GameAudioSystem::PlaybackGroup::Ui);
            const bool playedSecond = audioSystem.playCommonSoundNonResettable(
                SoundId::DullStrike,
                GameAudioSystem::PlaybackGroup::Ui);
            audioSystem.stopAllPlayback();

            if (!playedFirst || playedSecond)
            {
                failure = "non-resettable impact playback did not ignore the second request";
                return false;
            }

            return true;
        }
    );

    SharedHeadlessApplicationSession out01QuicksaveSession(m_config);

    runCase(
        "app_quicksave_quickload_restores_inventory_barrel_shop_and_qbits",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01QuicksaveSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01QuicksaveSession.application;
            const std::optional<MapAssetInfo> &appSelectedMap =
                GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!appSelectedMap)
            {
                failure = "application did not select a map";
                return false;
            }

            Party &party = GameApplicationTestAccess::outdoorPartyRuntime(application)->party();
            OutdoorWorldRuntime &world = *GameApplicationTestAccess::outdoorWorldRuntime(application);
            EventRuntimeState *pEventRuntimeState = world.eventRuntimeState();
            Character *pActiveMember = party.activeMember();

            if (pEventRuntimeState == nullptr || pActiveMember == nullptr)
            {
                failure = "application runtime state is incomplete";
                return false;
            }

            party.addGold(100000);
            const uint32_t baseIntellect = pActiveMember->intellect;
            GameApplicationTestAccess::setCameraAngles(application, 0.75f, -0.35f);
            const float savedGameMinutes = world.gameMinutes() + 123.0f;
            world.advanceGameMinutes(savedGameMinutes - world.gameMinutes());

            EventRuntime eventRuntime;
            EventRuntimeState::ActiveDecorationContext context = {};
            context.decorVarIndex = 2;
            context.baseEventId = 268;
            context.currentEventId = 272;
            context.eventCount = 8;
            context.hideWhenCleared = false;
            pEventRuntimeState->activeDecorationContext = context;

            const bool barrelExecuted = eventRuntime.executeEventById(
                std::nullopt,
                appSelectedMap->globalEventProgram,
                272,
                *pEventRuntimeState,
                &party,
                &world);
            pEventRuntimeState->activeDecorationContext.reset();

            if (!barrelExecuted)
            {
                failure = "barrel event 272 did not execute in application runtime";
                return false;
            }

            world.applyEventRuntimeState();
            party.applyEventRuntimeState(*pEventRuntimeState);

            if (pActiveMember->intellect != baseIntellect + 2)
            {
                failure = "barrel event did not update intellect before save";
                return false;
            }

            const HouseEntry *pHouseEntry = GameApplicationTestAccess::gameDataLoader(application).getHouseTable().get(1);

            if (pHouseEntry == nullptr)
            {
                failure = "missing house 1 entry";
                return false;
            }

            const std::vector<InventoryItem> &stock = HouseServiceRuntime::ensureStock(
                party,
                GameApplicationTestAccess::gameDataLoader(application).getItemTable(),
                GameApplicationTestAccess::gameDataLoader(application).getStandardItemEnchantTable(),
                GameApplicationTestAccess::gameDataLoader(application).getSpecialItemEnchantTable(),
                *pHouseEntry,
                world.gameMinutes(),
                HouseStockMode::ShopStandard);

            size_t purchasedSlotIndex = stock.size();

            for (size_t slotIndex = 0; slotIndex < stock.size(); ++slotIndex)
            {
                if (stock[slotIndex].objectDescriptionId != 0)
                {
                    purchasedSlotIndex = slotIndex;
                    break;
                }
            }

            if (purchasedSlotIndex >= stock.size())
            {
                failure = "shop stock did not generate a purchasable item";
                return false;
            }

            const InventoryItem purchasedItem = stock[purchasedSlotIndex];
            std::string statusText;

            if (!HouseServiceRuntime::tryBuyStockItem(
                    party,
                    GameApplicationTestAccess::gameDataLoader(application).getItemTable(),
                    GameApplicationTestAccess::gameDataLoader(application).getStandardItemEnchantTable(),
                    GameApplicationTestAccess::gameDataLoader(application).getSpecialItemEnchantTable(),
                    *pHouseEntry,
                    world.gameMinutes(),
                    HouseStockMode::ShopStandard,
                    purchasedSlotIndex,
                    statusText))
            {
                failure = "shop buy failed before save: " + statusText;
                return false;
            }

            const uint32_t qbitRawId = 458768;
            pEventRuntimeState->variables[qbitRawId] = 7;

            const std::filesystem::path savePath = "/tmp/openyamm_app_quicksave_state.oysav";

            if (!GameApplicationTestAccess::quickSaveToPath(application, savePath))
            {
                failure = "application quick save failed";
                return false;
            }

            pActiveMember->permanentBonuses.intellect = 0;
            pActiveMember->intellect = baseIntellect;
            pActiveMember->inventory.clear();
            party.clearHouseStockStates();
            pEventRuntimeState->variables.erase(qbitRawId);

            if (!GameApplicationTestAccess::quickLoadFromPath(application, savePath, true))
            {
                failure = "application quick load failed";
                return false;
            }

            std::error_code removeError;
            std::filesystem::remove(savePath, removeError);

            pActiveMember = GameApplicationTestAccess::outdoorPartyRuntime(application)->party().activeMember();
            pEventRuntimeState = GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState();

            if (pActiveMember == nullptr || pEventRuntimeState == nullptr)
            {
                failure = "loaded application runtime state is incomplete";
                return false;
            }

            if (pActiveMember->intellect != baseIntellect + 2)
            {
                failure = "barrel intellect bonus did not persist through app quick load";
                return false;
            }

            bool foundPurchasedItem = false;

            for (const InventoryItem &item : pActiveMember->inventory)
            {
                if (item.objectDescriptionId == purchasedItem.objectDescriptionId
                    && item.standardEnchantId == purchasedItem.standardEnchantId
                    && item.specialEnchantId == purchasedItem.specialEnchantId)
                {
                    foundPurchasedItem = true;
                    break;
                }
            }

            if (!foundPurchasedItem)
            {
                failure = "purchased inventory item did not persist through app quick load";
                return false;
            }

            const Party::HouseStockState *pLoadedShopState =
                GameApplicationTestAccess::outdoorPartyRuntime(application)->party().houseStockState(1);

            if (pLoadedShopState == nullptr
                || purchasedSlotIndex >= pLoadedShopState->standardStock.size()
                || pLoadedShopState->standardStock[purchasedSlotIndex].objectDescriptionId != 0)
            {
                failure = "shop stock purchase state did not persist through app quick load";
                return false;
            }

            if (!pEventRuntimeState->variables.contains(qbitRawId) || pEventRuntimeState->variables[qbitRawId] != 7)
            {
                failure = "event qbit state did not persist through app quick load";
                return false;
            }

            if (std::abs(GameApplicationTestAccess::cameraYawRadians(application) - 0.75f) > 0.0001f
                || std::abs(GameApplicationTestAccess::cameraPitchRadians(application) + 0.35f) > 0.0001f)
            {
                failure = "camera heading did not persist through app quick load";
                return false;
            }

            if (std::abs(GameApplicationTestAccess::outdoorWorldRuntime(application)->gameMinutes() - savedGameMinutes) > 0.01f)
            {
                failure = "current game time did not persist through app quick load";
                return false;
            }

            return true;
        }
    );

    runCase(
        "closed_house_entry_is_rejected_before_house_mode_with_oe_status_text",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01ViewSession.application;
            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
            const HouseEntry *pHouseEntry = GameApplicationTestAccess::gameDataLoader(application).getHouseTable().get(1);

            if (pWorld == nullptr || pPartyRuntime == nullptr || pEventRuntimeState == nullptr || pHouseEntry == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            const float closedMinuteOfDay = definitelyClosedMinuteOfDay(*pHouseEntry);

            if (closedMinuteOfDay < 0.0f)
            {
                failure = "house 1 does not have meaningful open/close hours";
                return false;
            }

            const float targetGameMinutes = nextGameMinuteAtOrAfter(pWorld->gameMinutes(), closedMinuteOfDay);
            pWorld->advanceGameMinutes(targetGameMinutes - pWorld->gameMinutes());

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = pHouseEntry->id;
            context.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->dialogueState.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->pendingDialogueContext = std::move(context);

            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

            if (GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "closed house still entered house mode";
                return false;
            }

            if (GameApplicationTestAccess::statusBarEventText(application) != buildClosedStatusText(*pHouseEntry))
            {
                failure = "closed house did not use the OE-style status text";
                return false;
            }

            if (pEventRuntimeState->pendingDialogueContext.has_value())
            {
                failure = "closed house left a pending dialogue context behind";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_quicksave_quickload_preserves_empty_house_after_departure",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01QuicksaveSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01QuicksaveSession.application;
            EventRuntimeState *pEventRuntimeState = GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState();

            if (pEventRuntimeState == nullptr)
            {
                failure = "missing application event runtime state";
                return false;
            }

            pEventRuntimeState->unavailableNpcIds.insert(32);

            const std::filesystem::path savePath = "/tmp/openyamm_app_empty_house.oysav";

            if (!GameApplicationTestAccess::quickSaveToPath(application, savePath))
            {
                failure = "application quick save failed";
                return false;
            }

            pEventRuntimeState->unavailableNpcIds.clear();

            if (!GameApplicationTestAccess::quickLoadFromPath(application, savePath, true))
            {
                failure = "application quick load failed";
                return false;
            }

            std::error_code removeError;
            std::filesystem::remove(savePath, removeError);

            RegressionScenario loadedScenario = {};

            if (!initializeRegressionScenarioFromApplication(application, loadedScenario, failure))
            {
                return false;
            }

            const std::optional<MapAssetInfo> &loadedMap =
                GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!loadedMap)
            {
                failure = "application map was not selected after load";
                return false;
            }

            if (!executeLocalEventInScenario(GameApplicationTestAccess::gameDataLoader(application), *loadedMap, loadedScenario, 37))
            {
                failure = "event 37 failed after app quick load";
                return false;
            }

            const EventDialogContent dialog =
                buildScenarioDialog(GameApplicationTestAccess::gameDataLoader(application), *loadedMap, loadedScenario, 0, true);

            if (!dialogContainsText(dialog, "The house is empty."))
            {
                failure = "loaded house did not remain empty after departure";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_open_house_action_rejects_after_closing_time",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01ViewSession.application;
            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
            const HouseEntry *pHouseEntry = GameApplicationTestAccess::gameDataLoader(application).getHouseTable().get(1);

            if (pWorld == nullptr || pEventRuntimeState == nullptr || pHouseEntry == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            const float openMinuteOfDay = static_cast<float>((pHouseEntry->openHour % 24) * 60);
            const float openGameMinutes = nextGameMinuteAtOrAfter(pWorld->gameMinutes(), openMinuteOfDay);
            pWorld->advanceGameMinutes(openGameMinutes - pWorld->gameMinutes());

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = pHouseEntry->id;
            context.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->dialogueState.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->pendingDialogueContext = std::move(context);

            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "open house did not enter house mode";
                return false;
            }

            const EventDialogContent &dialog = GameApplicationTestAccess::activeEventDialog(application);

            if (dialog.actions.empty())
            {
                failure = "open house dialog had no actions";
                return false;
            }

            const float closedMinuteOfDay = definitelyClosedMinuteOfDay(*pHouseEntry);

            if (closedMinuteOfDay < 0.0f)
            {
                failure = "house 1 does not have meaningful open/close hours";
                return false;
            }

            const float closedGameMinutes = nextGameMinuteAtOrAfter(pWorld->gameMinutes(), closedMinuteOfDay);
            pWorld->advanceGameMinutes(closedGameMinutes - pWorld->gameMinutes());

            GameApplicationTestAccess::setEventDialogSelectionIndex(application, 0);
            GameApplicationTestAccess::executeActiveDialogAction(application);

            if (GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "house action still executed after closing time";
                return false;
            }

            if (GameApplicationTestAccess::statusBarEventText(application) != buildClosedStatusText(*pHouseEntry))
            {
                failure = "late closed house action did not use closed status text";
                return false;
            }

            if (pEventRuntimeState->pendingDialogueContext.has_value())
            {
                failure = "late closed house action left a pending dialogue context";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_service_house_entry_opens_true_mettle_root_menu",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01ViewSession.application;
            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
            const HouseEntry *pHouseEntry = GameApplicationTestAccess::gameDataLoader(application).getHouseTable().get(1);

            if (pWorld == nullptr || pEventRuntimeState == nullptr || pHouseEntry == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            const float openMinuteOfDay = static_cast<float>((pHouseEntry->openHour % 24) * 60);
            const float openGameMinutes = nextGameMinuteAtOrAfter(pWorld->gameMinutes(), openMinuteOfDay);
            pWorld->advanceGameMinutes(openGameMinutes - pWorld->gameMinutes());

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = pHouseEntry->id;
            context.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->dialogueState.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->pendingDialogueContext = std::move(context);

            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "service house did not open an active dialog";
                return false;
            }

            const EventDialogContent &dialog = GameApplicationTestAccess::activeEventDialog(application);

            if (!dialogHasActionLabel(dialog, "Buy Standard")
                || !dialogHasActionLabel(dialog, "Buy Special")
                || !dialogHasActionLabel(dialog, "Display Equipment")
                || !dialogHasActionLabel(dialog, "Learn Skills"))
            {
                failure = "service house root menu is incomplete";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_party_defeat_zeros_gold_increments_num_deaths_and_uses_expected_respawn_map",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01StandaloneSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01StandaloneSession.application;
            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);

            if (pPartyRuntime == nullptr)
            {
                failure = "missing party runtime";
                return false;
            }

            Party &party = pPartyRuntime->party();
            party.addGold(1234);
            party.depositGoldToBank(234);

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                Character *pMember = party.member(memberIndex);

                if (pMember == nullptr)
                {
                    continue;
                }

                Character &member = *pMember;
                member.health = 0;
                member.conditions.set(static_cast<size_t>(CharacterCondition::Dead));
            }

            if (!GameApplicationTestAccess::shouldTriggerPartyDefeat(application))
            {
                failure = "party defeat did not trigger when all members were dead";
                return false;
            }

            if (GameApplicationTestAccess::resolvePartyDefeatRespawnMapFileName(application) != "out01.odm")
            {
                failure = "DWI defeat did not resolve to the DWI start map";
                return false;
            }

            if (!loadHeadlessGameApplicationMap(application, assetFileSystem, "d09.blv", failure))
            {
                return false;
            }

            if (GameApplicationTestAccess::resolvePartyDefeatRespawnMapFileName(application) != "out01.odm")
            {
                failure = "DWI indoor defeat did not resolve to the DWI start map";
                return false;
            }

            GameApplicationTestAccess::applyPartyDefeatConsequences(application);
            IMapSceneRuntime *pDefeatRuntime = GameApplicationTestAccess::mapSceneRuntime(application);
            Party *pDefeatedParty = pDefeatRuntime != nullptr ? &pDefeatRuntime->party() : nullptr;

            if (pDefeatedParty == nullptr)
            {
                failure = "missing defeated party runtime";
                return false;
            }

            if (pDefeatedParty->gold() != 0)
            {
                failure = "party defeat did not remove carried gold";
                return false;
            }

            if (pDefeatedParty->bankGold() != 234)
            {
                failure = "party defeat should not remove bank gold";
                return false;
            }

            if (pDefeatedParty->eventVariableValue(static_cast<uint16_t>(EvtVariable::NumDeaths)) != 1)
            {
                failure = "party defeat did not increment NumDeaths";
                return false;
            }

            if (!pDefeatedParty->hasActableMember())
            {
                failure = "party defeat did not revive the party";
                return false;
            }

            if (!loadHeadlessGameApplicationMap(application, assetFileSystem, "out02.odm", failure))
            {
                return false;
            }

            if (GameApplicationTestAccess::resolvePartyDefeatRespawnMapFileName(application) != "out02.odm")
            {
                failure = "non-DWI defeat did not resolve to Ravenshore";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_regular_house_entry_auto_opens_single_resident_dialog",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01ViewSession.application;
            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
            const HouseEntry *pHouseEntry = GameApplicationTestAccess::gameDataLoader(application).getHouseTable().get(237);

            if (pWorld == nullptr || pEventRuntimeState == nullptr || pHouseEntry == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            const float openMinuteOfDay = static_cast<float>((pHouseEntry->openHour % 24) * 60);
            const float openGameMinutes = nextGameMinuteAtOrAfter(pWorld->gameMinutes(), openMinuteOfDay);
            pWorld->advanceGameMinutes(openGameMinutes - pWorld->gameMinutes());

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = pHouseEntry->id;
            context.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->dialogueState.hostHouseId = pHouseEntry->id;
            pEventRuntimeState->pendingDialogueContext = std::move(context);

            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "regular house did not open an active dialog";
                return false;
            }

            const EventDialogContent &dialog = GameApplicationTestAccess::activeEventDialog(application);

            if (dialog.title != "Fredrick Talimere")
            {
                failure = "regular house opened unexpected resident dialog title";
                return false;
            }

            if (!dialogHasActionLabel(dialog, "Portals of Stone") || !dialogHasActionLabel(dialog, "Cataclysm"))
            {
                failure = "regular house resident dialog is missing expected topics";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_single_teacher_house_entry_unlocks_teacher_autonote",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01ViewSession.application;
            OutdoorWorldRuntime *pWorld = GameApplicationTestAccess::outdoorWorldRuntime(application);
            EventRuntimeState *pEventRuntimeState = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
            const GameDataLoader &gameDataLoader = GameApplicationTestAccess::gameDataLoader(application);
            const HouseTable &houseTable = gameDataLoader.getHouseTable();
            const NpcDialogTable &npcDialogTable = gameDataLoader.getNpcDialogTable();

            if (pWorld == nullptr || pEventRuntimeState == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            constexpr uint32_t TeacherHouseId = 371;
            constexpr uint32_t TeacherNpcId = 373;
            constexpr uint32_t TeacherTopicId = 388;
            constexpr uint32_t AutoNoteRawId = ((128u + (TeacherTopicId - 300u)) << 16) | 0x00E1u;
            const HouseEntry *pTeacherHouse = houseTable.get(TeacherHouseId);

            if (pTeacherHouse == nullptr)
            {
                failure = "missing Helga Steeleye house entry";
                return false;
            }

            const std::vector<HouseActionOption> houseActions = buildHouseActionOptions(
                *pTeacherHouse,
                nullptr,
                nullptr,
                nullptr,
                pWorld->gameMinutes(),
                DialogueMenuId::None);
            const std::vector<uint32_t> residentNpcIds =
                collectSelectableResidentNpcIds(*pTeacherHouse, npcDialogTable, *pEventRuntimeState);

            if (!houseActions.empty() || residentNpcIds.size() != 1 || residentNpcIds.front() != TeacherNpcId)
            {
                failure = "Helga Steeleye house is no longer a single-resident auto-open teacher house";
                return false;
            }

            if (pEventRuntimeState->variables.contains(AutoNoteRawId))
            {
                failure = "teacher autonote was already unlocked before house entry";
                return false;
            }

            const float openMinuteOfDay = static_cast<float>((pTeacherHouse->openHour % 24) * 60);
            const float openGameMinutes = nextGameMinuteAtOrAfter(pWorld->gameMinutes(), openMinuteOfDay);
            pWorld->advanceGameMinutes(openGameMinutes - pWorld->gameMinutes());

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = pTeacherHouse->id;
            context.hostHouseId = pTeacherHouse->id;
            pEventRuntimeState->dialogueState.hostHouseId = pTeacherHouse->id;
            pEventRuntimeState->pendingDialogueContext = std::move(context);

            GameApplicationTestAccess::openPendingEventDialog(application, pEventRuntimeState->messages.size(), true);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "teacher house did not open an active dialog";
                return false;
            }

            const EventDialogContent &dialog = GameApplicationTestAccess::activeEventDialog(application);

            if (dialog.sourceId != TeacherNpcId)
            {
                failure = "teacher house did not auto-open the teacher resident dialog";
                return false;
            }

            const auto noteIt = pEventRuntimeState->variables.find(AutoNoteRawId);

            if (noteIt == pEventRuntimeState->variables.end() || noteIt->second == 0)
            {
                failure = "teacher autonote was not unlocked on house entry";
                return false;
            }

            bool sawAutoNoteFx = false;

            for (const EventRuntimeState::PortraitFxRequest &request : pEventRuntimeState->portraitFxRequests)
            {
                if (request.kind != PortraitFxEventKind::AutoNote)
                {
                    continue;
                }

                if (std::find(
                        request.memberIndices.begin(),
                        request.memberIndices.end(),
                        GameApplicationTestAccess::outdoorPartyRuntime(application)->party().activeMemberIndex())
                    != request.memberIndices.end())
                {
                    sawAutoNoteFx = true;
                    break;
                }
            }

            if (!sawAutoNoteFx)
            {
                failure = "teacher house entry did not queue the autonote portrait fx";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_outdoor_decoration_billboard_activation_uses_global_decoration_events",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01ViewSession.application;

            const std::optional<MapAssetInfo> &selectedMap =
                GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!selectedMap
                || !selectedMap->outdoorMapData
                || !selectedMap->outdoorDecorationBillboardSet)
            {
                failure = "selected map is missing outdoor decoration data";
                return false;
            }

            const DecorationBillboardSet &billboardSet = *selectedMap->outdoorDecorationBillboardSet;
            const OutdoorMapData &outdoorMapData = *selectedMap->outdoorMapData;
            OutdoorGameView &view = GameApplicationTestAccess::outdoorGameView(application);
            std::optional<size_t> pedestalBillboardIndex;
            std::optional<size_t> beaconBillboardIndex;

            for (size_t billboardIndex = 0; billboardIndex < billboardSet.billboards.size(); ++billboardIndex)
            {
                const DecorationBillboard &billboard = billboardSet.billboards[billboardIndex];

                if (billboard.entityIndex >= outdoorMapData.entities.size())
                {
                    continue;
                }

                if (!pedestalBillboardIndex && toLowerCopy(billboard.name) == "dec49")
                {
                    pedestalBillboardIndex = billboardIndex;
                }

                if (!beaconBillboardIndex && toLowerCopy(billboard.name) == "dec40")
                {
                    beaconBillboardIndex = billboardIndex;
                }
            }

            if (!pedestalBillboardIndex)
            {
                failure = "could not find dec49 pedestal billboard on Out01";
                return false;
            }

            const DecorationBillboard &pedestalBillboard = billboardSet.billboards[*pedestalBillboardIndex];
            const std::optional<uint16_t> pedestalEventId =
                OutdoorInteractionController::resolveInteractiveDecorationEventId(view, pedestalBillboard.entityIndex);

            if (!pedestalEventId || *pedestalEventId != 536)
            {
                failure = "dec49 pedestal resolved to event "
                    + std::to_string(pedestalEventId.value_or(0))
                    + " instead of 536";
                return false;
            }

            OutdoorGameView::InspectHit pedestalInspectHit = {};
            pedestalInspectHit.hasHit = true;
            pedestalInspectHit.kind = "decoration";
            pedestalInspectHit.bModelIndex = *pedestalBillboardIndex;
            pedestalInspectHit.name = pedestalBillboard.name;
            pedestalInspectHit.distance = 0.0f;

            if (!OutdoorInteractionController::tryActivateInspectEvent(view, pedestalInspectHit))
            {
                failure = "dec49 pedestal did not activate through decoration inspect path";
                return false;
            }

            EventRuntimeState *pEventRuntimeState =
                GameApplicationTestAccess::outdoorWorldRuntime(application) != nullptr
                ? GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState()
                : nullptr;

            if (pEventRuntimeState == nullptr || pEventRuntimeState->spellFxRequests.empty())
            {
                failure = "dec49 pedestal did not queue spell presentation requests";
                return false;
            }

            GameApplicationTestAccess::consumePendingPortraitEventFxRequests(application);

            if (!pEventRuntimeState->spellFxRequests.empty())
            {
                failure = "dec49 pedestal spell presentation requests were not consumed";
                return false;
            }

            Party &party = GameApplicationTestAccess::outdoorPartyRuntime(application)->party();

            if (!party.hasPartyBuff(PartyBuffId::FireResistance))
            {
                failure = "dec49 pedestal did not apply fire resistance buff";
                return false;
            }

            const PartyBuffState *pFireResistanceBuff = party.partyBuff(PartyBuffId::FireResistance);

            if (pFireResistanceBuff == nullptr
                || pFireResistanceBuff->skillLevel != 5
                || pFireResistanceBuff->skillMastery != SkillMastery::Grandmaster
                || pFireResistanceBuff->power != 20)
            {
                failure = "dec49 pedestal applied unexpected fire resistance buff parameters";
                return false;
            }

            if (!beaconBillboardIndex)
            {
                failure = "could not find dec40 beacon billboard on Out01";
                return false;
            }

            const DecorationBillboard &beaconBillboard = billboardSet.billboards[*beaconBillboardIndex];
            const std::optional<uint16_t> beaconEventId =
                OutdoorInteractionController::resolveInteractiveDecorationEventId(view, beaconBillboard.entityIndex);

            if (!beaconEventId || *beaconEventId < 542 || *beaconEventId > 548)
            {
                failure = "dec40 beacon resolved to event "
                    + std::to_string(beaconEventId.value_or(0))
                    + " outside 542..548";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_pending_map_move_loads_indoor_runtime",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01PendingMapMoveSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01PendingMapMoveSession.application;
            EventRuntimeState *pEventRuntimeState = GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState();

            if (pEventRuntimeState == nullptr)
            {
                failure = "missing application event runtime state";
                return false;
            }

            EventRuntimeState::PendingMapMove pendingMapMove = {};
            pendingMapMove.mapName = std::string("D05.blv");
            pendingMapMove.useMapStartPosition = true;
            pEventRuntimeState->pendingMapMove = std::move(pendingMapMove);

            if (!GameApplicationTestAccess::processPendingMapMove(application))
            {
                failure = "application did not process the indoor pending map move";
                return false;
            }

            const std::optional<MapAssetInfo> &loadedMap = GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!loadedMap || toLowerCopy(loadedMap->map.fileName) != "d05.blv" || !loadedMap->indoorMapData)
            {
                failure = "indoor pending map move did not load the destination indoor map";
                return false;
            }

            if (GameApplicationTestAccess::currentSceneKind(application) != SceneKind::Indoor)
            {
                failure = "application did not switch to indoor scene kind";
                return false;
            }

            if (GameApplicationTestAccess::outdoorPartyRuntime(application) != nullptr
                || GameApplicationTestAccess::outdoorWorldRuntime(application) != nullptr)
            {
                failure = "outdoor runtime remained active after indoor transition";
                return false;
            }

            return true;
        }
    );

    runCase(
        "dwi_terrain_atlas_does_not_leave_opaque_magenta_water_transition_fill",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01DataSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01DataSession.application;

            const std::optional<MapAssetInfo> &selectedMap =
                GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            if (!selectedMap || !selectedMap->outdoorMapData || !selectedMap->outdoorTerrainTextureAtlas)
            {
                failure = "selected DWI map is missing outdoor atlas data";
                return false;
            }

            const OutdoorMapData &outdoorMapData = *selectedMap->outdoorMapData;
            const OutdoorTerrainTextureAtlas &atlas = *selectedMap->outdoorTerrainTextureAtlas;
            std::array<bool, 256> usedTileIds = {};

            for (uint8_t tileId : outdoorMapData.tileMap)
            {
                usedTileIds[static_cast<size_t>(tileId)] = true;
            }

            for (size_t tileIndex = 0; tileIndex < usedTileIds.size(); ++tileIndex)
            {
                if (!usedTileIds[tileIndex])
                {
                    continue;
                }

                const OutdoorTerrainAtlasRegion &region = atlas.tileRegions[tileIndex];

                if (!region.isValid)
                {
                    continue;
                }

                const int atlasX = static_cast<int>(region.u0 * static_cast<float>(atlas.width));
                const int atlasY = static_cast<int>(region.v0 * static_cast<float>(atlas.height));
                std::vector<uint8_t> tilePixels(static_cast<size_t>(atlas.tileSize * atlas.tileSize * 4), 0);

                for (int row = 0; row < atlas.tileSize; ++row)
                {
                    const size_t sourceOffset = static_cast<size_t>(((atlasY + row) * atlas.width + atlasX) * 4);
                    const size_t targetOffset = static_cast<size_t>(row * atlas.tileSize * 4);
                    std::memcpy(
                        tilePixels.data() + static_cast<ptrdiff_t>(targetOffset),
                        atlas.pixels.data() + static_cast<ptrdiff_t>(sourceOffset),
                        static_cast<size_t>(atlas.tileSize * 4)
                    );
                }

                const TextureColorStats colorStats = analyzeTextureColors(tilePixels);

                if (colorStats.magentaPixelCount > 0)
                {
                    failure =
                        "used terrain atlas tile " + std::to_string(tileIndex)
                        + " still contains opaque magenta fill";
                    return false;
                }
            }

            return true;
        }
    );

    Engine::ApplicationConfig startupConfig = m_config;
    startupConfig.startupMapFileOverride = "out01.odm";
    SharedHeadlessApplicationSession startupSession(startupConfig);

    runCase(
        "app_startup_boots_seeded_out01_session",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessStartupSession(startupSession, assetFileSystem, true, failure))
            {
                return false;
            }

            GameApplication &application = startupSession.application;
            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);

            const std::string currentMapFileName = toLowerCopy(
                std::filesystem::path(GameApplicationTestAccess::currentSessionMapFileName(application))
                    .filename()
                    .string());

            if (currentMapFileName != "out01.odm")
            {
                failure = "startup session did not select out01.odm";
                return false;
            }

            const std::optional<MapAssetInfo> &selectedMap =
                GameApplicationTestAccess::gameDataLoader(application).getSelectedMap();

            const std::string selectedMapFileName =
                selectedMap
                ? toLowerCopy(std::filesystem::path(selectedMap->map.fileName).filename().string())
                : std::string {};

            if (!selectedMap || selectedMapFileName != "out01.odm")
            {
                failure = "startup session did not load DWI map assets";
                return false;
            }

            const std::vector<Character> &members = pPartyRuntime->party().members();
            static constexpr std::array<const char *, 4> ExpectedNames = {
                "Ariel",
                "Leane Stormlance",
                "Arius",
                "Overdune Snapfinger"
            };
            static constexpr std::array<uint32_t, 4> ExpectedRosterIds = {{0, 11, 5, 4}};

            if (members.size() != ExpectedNames.size())
            {
                failure = "startup party did not use the seeded party";
                return false;
            }

            for (size_t memberIndex = 0; memberIndex < ExpectedNames.size(); ++memberIndex)
            {
                if (members[memberIndex].name != ExpectedNames[memberIndex])
                {
                    failure = "startup party member " + std::to_string(memberIndex) + " mismatch";
                    return false;
                }

                if (members[memberIndex].rosterId != ExpectedRosterIds[memberIndex])
                {
                    failure = "startup party member " + std::to_string(memberIndex) + " roster mismatch";
                    return false;
                }
            }

            const std::vector<AdventurersInnMember> &innMembers = pPartyRuntime->party().adventurersInnMembers();
            static constexpr std::array<const char *, 2> ExpectedInnNames = {
                "Devlin Arcanus",
                "Elsbeth Lamentia"
            };

            if (innMembers.size() != ExpectedInnNames.size())
            {
                failure = "startup adventurers inn seed mismatch";
                return false;
            }

            for (size_t innIndex = 0; innIndex < ExpectedInnNames.size(); ++innIndex)
            {
                if (innMembers[innIndex].character.name != ExpectedInnNames[innIndex])
                {
                    failure = "startup adventurers inn member " + std::to_string(innIndex) + " mismatch";
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "app_adventurers_inn_house_opens_character_overlay",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessStartupSession(startupSession, assetFileSystem, false, failure))
            {
                return false;
            }

            GameApplication &application = startupSession.application;
            OutdoorWorldRuntime *pWorldRuntime = GameApplicationTestAccess::outdoorWorldRuntime(application);
            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);

            EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState();

            if (pEventRuntimeState == nullptr)
            {
                failure = "missing event runtime state";
                return false;
            }

            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::HouseService;
            context.sourceId = AdventurersInnHouseId;
            context.hostHouseId = AdventurersInnHouseId;
            pEventRuntimeState->pendingDialogueContext = context;
            GameApplicationTestAccess::presentPendingEventDialogDirect(
                application,
                pEventRuntimeState->messages.size(),
                true,
                false);

            if (GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "adventurers inn house should open overlay instead of a house dialog";
                return false;
            }

            const GameplayUiController::CharacterScreenState &characterScreen =
                GameApplicationTestAccess::characterScreen(application);

            if (!characterScreen.open
                || !characterScreen.adventurersInnRosterOverlayOpen
                || characterScreen.source != GameplayUiController::CharacterScreenSource::AdventurersInn)
            {
                failure = "adventurers inn overlay state mismatch: open="
                    + std::to_string(characterScreen.open ? 1 : 0)
                    + " roster=" + std::to_string(characterScreen.adventurersInnRosterOverlayOpen ? 1 : 0)
                    + " source=" + std::to_string(static_cast<int>(characterScreen.source));
                return false;
            }

            if (pPartyRuntime->party().adventurersInnMembers().size() != 2)
            {
                failure = "startup adventurers inn seed was not available when opening the house";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_quicksave_quickload_preserves_visited_map_runtime_state",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01QuicksaveSession,
                    assetFileSystem,
                    "out01.odm",
                    false,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01QuicksaveSession.application;
            EventRuntimeState *pOut01State = GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState();

            if (pOut01State == nullptr)
            {
                failure = "missing out01 event runtime state";
                return false;
            }

            pOut01State->variables[0x1234u] = 77;

            if (!loadHeadlessGameApplicationMap(application, assetFileSystem, "out02.odm", failure))
            {
                return false;
            }

            EventRuntimeState *pOut02State = GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState();

            if (pOut02State == nullptr)
            {
                failure = "missing out02 event runtime state";
                return false;
            }

            pOut02State->variables[0x2345u] = 88;

            const std::filesystem::path savePath = "/tmp/openyamm_app_cross_map.oysav";

            if (!GameApplicationTestAccess::quickSaveToPath(application, savePath))
            {
                failure = "application quick save failed";
                return false;
            }

            if (!GameApplicationTestAccess::quickLoadFromPath(application, savePath, true))
            {
                failure = "application quick load failed";
                return false;
            }

            if (!loadHeadlessGameApplicationMap(application, assetFileSystem, "out01.odm", failure))
            {
                return false;
            }

            pOut01State = GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState();

            if (pOut01State == nullptr || !pOut01State->variables.contains(0x1234u) || pOut01State->variables[0x1234u] != 77)
            {
                failure = "visited out01 state did not persist across app quick load";
                return false;
            }

            if (!loadHeadlessGameApplicationMap(application, assetFileSystem, "out02.odm", failure))
            {
                return false;
            }

            std::error_code removeError;
            std::filesystem::remove(savePath, removeError);

            pOut02State = GameApplicationTestAccess::outdoorWorldRuntime(application)->eventRuntimeState();

            if (pOut02State == nullptr || !pOut02State->variables.contains(0x2345u) || pOut02State->variables[0x2345u] != 88)
            {
                failure = "current-map out02 state did not persist across app quick load";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_npc_granted_item_enters_held_cursor_slot",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01ViewSession.application;

            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);
            OutdoorWorldRuntime *pWorldRuntime = GameApplicationTestAccess::outdoorWorldRuntime(application);

            if (pPartyRuntime == nullptr || pWorldRuntime == nullptr)
            {
                failure = "missing outdoor runtime state";
                return false;
            }

            Party &party = pPartyRuntime->party();
            EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState();
            Character *pActiveMember = party.activeMember();

            if (pEventRuntimeState == nullptr || pActiveMember == nullptr)
            {
                failure = "missing event runtime or active member";
                return false;
            }

            party.addGold(1000);
            pWorldRuntime->openDebugNpcDialogue(279);

            if (!GameApplicationTestAccess::hasActiveEventDialog(application))
            {
                failure = "Long-Tail debug dialog did not open";
                return false;
            }

            const EventDialogContent &dialog = GameApplicationTestAccess::activeEventDialog(application);
            const std::optional<size_t> buyTopicIndex =
                findActionIndexByLabel(dialog, "Buy Tobersk Fruit for 200 gold");

            if (!buyTopicIndex)
            {
                failure = "Long-Tail debug dialog did not expose the Tobersk fruit buy topic";
                return false;
            }

            pActiveMember->portraitState = PortraitId::Normal;
            pActiveMember->portraitElapsedTicks = 0;
            pActiveMember->portraitDurationTicks = 0;

            GameApplicationTestAccess::setEventDialogSelectionIndex(application, *buyTopicIndex);
            GameApplicationTestAccess::executeActiveDialogAction(application);

            if (!GameApplicationTestAccess::heldInventoryItemActive(application))
            {
                failure = "NPC-granted item did not enter the held cursor slot";
                return false;
            }

            if (GameApplicationTestAccess::heldInventoryItem(application).objectDescriptionId != 643)
            {
                failure = "held cursor item was not Tobersk fruit after the buy topic";
                return false;
            }

            if (party.inventoryItemCount(643) != 0)
            {
                failure = "NPC-granted item was incorrectly placed into inventory";
                return false;
            }

            if (!pEventRuntimeState->portraitFxRequests.empty())
            {
                failure = "house trade topic still queued portrait event fx";
                return false;
            }

            if (pActiveMember->portraitState == PortraitId::Normal)
            {
                failure = "house trade topic did not trigger the face-only smile reaction";
                return false;
            }

            return true;
        }
    );

    runCase(
        "app_npc_granted_item_displaces_previous_held_item_to_inventory_or_ground",
        [&](std::string &failure)
        {
            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &application = out01ViewSession.application;

            OutdoorPartyRuntime *pPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(application);
            OutdoorWorldRuntime *pWorldRuntime = GameApplicationTestAccess::outdoorWorldRuntime(application);
            EventRuntimeState *pEventRuntimeState =
                pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

            if (pPartyRuntime == nullptr || pWorldRuntime == nullptr || pEventRuntimeState == nullptr)
            {
                failure = "application state is incomplete";
                return false;
            }

            Party &party = pPartyRuntime->party();
            const ItemTable &itemTable = GameApplicationTestAccess::gameDataLoader(application).getItemTable();
            const InventoryItem oldHeldItem =
                ItemGenerator::makeInventoryItem(645, itemTable, ItemGenerationMode::Generic);

            GameApplicationTestAccess::setHeldInventoryItem(application, oldHeldItem);
            pEventRuntimeState->grantedItemIds = {643};
            pWorldRuntime->applyGrantedEventItemsToHeldInventory();

            if (!GameApplicationTestAccess::heldInventoryItemActive(application)
                || GameApplicationTestAccess::heldInventoryItem(application).objectDescriptionId != 643)
            {
                failure = "new granted item did not replace the held cursor item";
                return false;
            }

            if (party.inventoryItemCount(645) != 1)
            {
                failure = "previously held item was not moved into inventory";
                return false;
            }

            if (!prepareSharedHeadlessGameApplication(
                    out01ViewSession,
                    assetFileSystem,
                    "out01.odm",
                    true,
                    failure))
            {
                return false;
            }

            GameApplication &fullInventoryApplication = out01ViewSession.application;
            OutdoorPartyRuntime *pFullPartyRuntime = GameApplicationTestAccess::outdoorPartyRuntime(fullInventoryApplication);
            OutdoorWorldRuntime *pFullWorldRuntime = GameApplicationTestAccess::outdoorWorldRuntime(fullInventoryApplication);
            EventRuntimeState *pFullEventRuntimeState =
                pFullWorldRuntime != nullptr ? pFullWorldRuntime->eventRuntimeState() : nullptr;

            if (pFullPartyRuntime == nullptr || pFullWorldRuntime == nullptr || pFullEventRuntimeState == nullptr)
            {
                failure = "full-inventory application state is incomplete";
                return false;
            }

            Party &fullParty = pFullPartyRuntime->party();
            InventoryItem fillerItem = {};
            fillerItem.objectDescriptionId = 643;
            fillerItem.quantity = 1;
            fillerItem.width = 1;
            fillerItem.height = 1;

            for (size_t memberIndex = 0; memberIndex < fullParty.members().size(); ++memberIndex)
            {
                Character *pMember = fullParty.member(memberIndex);

                if (pMember == nullptr)
                {
                    failure = "missing party member while filling inventory";
                    return false;
                }

                pMember->inventory.clear();

                for (uint8_t gridY = 0; gridY < Character::InventoryHeight; ++gridY)
                {
                    for (uint8_t gridX = 0; gridX < Character::InventoryWidth; ++gridX)
                    {
                        if (!pMember->addInventoryItemAt(fillerItem, gridX, gridY))
                        {
                            failure = "could not fill inventory cell "
                                + std::to_string(memberIndex) + ":" + std::to_string(gridX) + ","
                                + std::to_string(gridY);
                            return false;
                        }
                    }
                }
            }

            GameApplicationTestAccess::setHeldInventoryItem(fullInventoryApplication, oldHeldItem);
            const size_t initialWorldItemCount = pFullWorldRuntime->worldItemCount();
            pFullEventRuntimeState->grantedItemIds = {643};
            pFullWorldRuntime->applyGrantedEventItemsToHeldInventory();

            if (!GameApplicationTestAccess::heldInventoryItemActive(fullInventoryApplication)
                || GameApplicationTestAccess::heldInventoryItem(fullInventoryApplication).objectDescriptionId != 643)
            {
                failure = "new granted item did not remain held when inventory was full";
                return false;
            }

            if (fullParty.inventoryItemCount(645) != 0)
            {
                failure = "previously held item was duplicated into inventory when inventory was full";
                return false;
            }

            if (pFullWorldRuntime->worldItemCount() != initialWorldItemCount + 1)
            {
                failure = "previously held item was not thrown to the ground when inventory was full";
                return false;
            }

            const OutdoorWorldRuntime::WorldItemState *pDroppedItem =
                pFullWorldRuntime->worldItemState(pFullWorldRuntime->worldItemCount() - 1);

            if (pDroppedItem == nullptr || pDroppedItem->item.objectDescriptionId != 645)
            {
                failure = "the wrong item was thrown to the ground";
                return false;
            }

            if (!pFullEventRuntimeState->grantedItemIds.empty())
            {
                failure = "granted item ids were not consumed after the held-item handoff";
                return false;
            }

            return true;
        }
    );

    runCase(
        "generated_lua_event_scripts_load_for_every_scripted_map",
        [&](std::string &failure)
        {
            const std::vector<std::string> scriptedMapFileNames =
                collectScriptedMapFileNames(assetFileSystem, gameDataLoader);

            if (scriptedMapFileNames.empty())
            {
                failure = "no scripted maps were discovered";
                return false;
            }

            GameDataLoader loader = gameDataLoader;
            EventRuntime eventRuntime = {};

            for (const std::string &mapFileName : scriptedMapFileNames)
            {
                if (!loader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
                {
                    failure = "failed to load scripted map " + mapFileName;
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = loader.getSelectedMap();

                if (!loadedMap.has_value())
                {
                    failure = "loaded map was missing for " + mapFileName;
                    return false;
                }

                if (!loadedMap->globalEventProgram.has_value()
                    || !loadedMap->globalEventProgram->luaSourceText().has_value()
                    || !loadedMap->localEventProgram.has_value()
                    || !loadedMap->localEventProgram->luaSourceText().has_value())
                {
                    failure = "scripted map was missing Lua sources for " + mapFileName;
                    return false;
                }

                const std::optional<MapDeltaData> mapDeltaData =
                    loadedMap->outdoorMapDeltaData ? loadedMap->outdoorMapDeltaData : loadedMap->indoorMapDeltaData;
                EventRuntimeState runtimeState = {};

                if (!eventRuntime.buildOnLoadState(
                        loadedMap->localEventProgram,
                        loadedMap->globalEventProgram,
                        mapDeltaData,
                        runtimeState))
                {
                    failure = "buildOnLoadState failed for " + mapFileName;
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "outdoor_terrain_texture_atlas_builds_for_non_default_master_tiles",
        [&](std::string &failure)
        {
            static constexpr std::array<const char *, 2> requiredMaps = {
                "out04.odm",
                "out06.odm",
            };

            for (const char *pMapFileName : requiredMaps)
            {
                MapAssetInfo loadedMap = {};

                if (!loadOutdoorMapWithCompanionOptions(
                        assetFileSystem,
                        gameDataLoader,
                        pMapFileName,
                        MapLoadPurpose::Full,
                        MapCompanionLoadOptions{.allowSceneYml = true, .allowLegacyCompanion = true},
                        loadedMap,
                        failure))
                {
                    return false;
                }

                if (!loadedMap.outdoorMapData.has_value() || !loadedMap.outdoorTerrainTextureAtlas.has_value())
                {
                    failure = std::string("loaded map missing terrain atlas for ") + pMapFileName;
                    return false;
                }

                size_t validTileCount = 0;

                for (const OutdoorTerrainAtlasRegion &region : loadedMap.outdoorTerrainTextureAtlas->tileRegions)
                {
                    if (region.isValid)
                    {
                        ++validTileCount;
                    }
                }

                if (validTileCount == 0)
                {
                    failure = std::string("terrain atlas did not contain any valid tiles for ") + pMapFileName;
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "lua_event_runtime_has_complete_handler_inventory_for_every_scripted_map",
        [&](std::string &failure)
        {
            const std::vector<std::string> scriptedMapFileNames =
                collectScriptedMapFileNames(assetFileSystem, gameDataLoader);

            if (scriptedMapFileNames.empty())
            {
                failure = "no scripted maps were discovered";
                return false;
            }

            GameDataLoader loader = gameDataLoader;

            for (const std::string &mapFileName : scriptedMapFileNames)
            {
                if (!loader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
                {
                    failure = "failed to load scripted map " + mapFileName;
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = loader.getSelectedMap();

                if (!loadedMap.has_value())
                {
                    failure = "loaded map was missing for " + mapFileName;
                    return false;
                }

                EventRuntime eventRuntime = {};
                EventRuntimeBindingReport report = {};

                if (!eventRuntime.validateProgramBindings(
                        loadedMap->localEventProgram,
                        loadedMap->globalEventProgram,
                        report))
                {
                    failure = "validateProgramBindings failed for " + mapFileName;
                    return false;
                }

                if (!report.missingLocalHandlerEventIds.empty()
                    || !report.missingGlobalHandlerEventIds.empty()
                    || !report.missingCanShowTopicEventIds.empty()
                    || report.errorMessage.has_value())
                {
                    failure = "script binding report was incomplete for " + mapFileName;
                    return false;
                }
            }

            return true;
        }
    );

    runCase(
        "lua_event_runtime_executes_scripted_map_handlers_without_errors",
        [&](std::string &failure)
        {
            const std::vector<std::string> scriptedMapFileNames =
                collectScriptedMapFileNames(assetFileSystem, gameDataLoader);

            if (scriptedMapFileNames.empty())
            {
                failure = "no scripted maps were discovered";
                return false;
            }

            GameDataLoader loader = gameDataLoader;
            bool executedGlobalHandlers = false;

            for (const std::string &mapFileName : scriptedMapFileNames)
            {
                if (!loader.loadMapByFileNameForHeadlessGameplay(assetFileSystem, mapFileName))
                {
                    failure = "failed to load scripted map " + mapFileName;
                    return false;
                }

                const std::optional<MapAssetInfo> &loadedMap = loader.getSelectedMap();

                if (!loadedMap.has_value())
                {
                    failure = "loaded map was missing for " + mapFileName;
                    return false;
                }

                EventRuntime eventRuntime = {};
                const std::optional<MapDeltaData> mapDeltaData =
                    loadedMap->outdoorMapDeltaData ? loadedMap->outdoorMapDeltaData : loadedMap->indoorMapDeltaData;
                EventRuntimeState baseState = {};

                if (!eventRuntime.buildOnLoadState(
                        loadedMap->localEventProgram,
                        loadedMap->globalEventProgram,
                        mapDeltaData,
                        baseState))
                {
                    failure = "buildOnLoadState failed for " + mapFileName;
                    return false;
                }

                if (!executedGlobalHandlers && loadedMap->globalEventProgram.has_value())
                {
                    for (uint16_t eventId : loadedMap->globalEventProgram->eventIds())
                    {
                        EventRuntimeState eventState = baseState;

                        if (!eventRuntime.executeEventById(
                                std::nullopt,
                                loadedMap->globalEventProgram,
                                eventId,
                                eventState,
                                nullptr,
                                nullptr))
                        {
                            failure = "global event " + std::to_string(eventId) + " failed for " + mapFileName;
                            return false;
                        }
                    }

                    executedGlobalHandlers = true;
                }

                if (loadedMap->localEventProgram.has_value())
                {
                    for (uint16_t eventId : loadedMap->localEventProgram->eventIds())
                    {
                        EventRuntimeState eventState = baseState;

                        if (!eventRuntime.executeEventById(
                                loadedMap->localEventProgram,
                                loadedMap->globalEventProgram,
                                eventId,
                                eventState,
                                nullptr,
                                nullptr))
                        {
                            failure = "local event " + std::to_string(eventId) + " failed for " + mapFileName;
                            return false;
                        }
                    }
                }
            }

            return true;
        }
    );

    runCase(
        "outdoor_scene_yml_matches_legacy_ddm_authored_state",
        [&](std::string &failure)
        {
            static constexpr std::array<const char *, 4> requiredMaps = {
                "out01.odm",
                "out02.odm",
                "out05.odm",
                "out13.odm",
            };

            for (const char *pMapFileName : requiredMaps)
            {
                MapAssetInfo legacyMap = {};

                if (!loadOutdoorMapWithCompanionOptions(
                        assetFileSystem,
                        gameDataLoader,
                        pMapFileName,
                        MapLoadPurpose::HeadlessGameplay,
                        MapCompanionLoadOptions{
                            .allowSceneYml = false,
                            .allowLegacyCompanion = true,
                        },
                        legacyMap,
                        failure))
                {
                    return false;
                }

                MapAssetInfo migratedMap = {};

                if (!loadOutdoorMapWithCompanionOptions(
                        assetFileSystem,
                        gameDataLoader,
                        pMapFileName,
                        MapLoadPurpose::HeadlessGameplay,
                        MapCompanionLoadOptions{
                            .allowSceneYml = true,
                            .allowLegacyCompanion = false,
                        },
                        migratedMap,
                        failure))
                {
                    return false;
                }

                if (migratedMap.authoredCompanionSource != AuthoredCompanionSource::SceneYml)
                {
                    failure = std::string("migrated scene companion source was wrong for ") + pMapFileName;
                    return false;
                }

                const std::string legacySnapshot = buildNormalizedOutdoorAuthoredSnapshot(legacyMap);
                const std::string migratedSnapshot = buildNormalizedOutdoorAuthoredSnapshot(migratedMap);

                if (legacySnapshot != migratedSnapshot)
                {
                    failure = std::string("legacy and scene-authored outdoor state diverged for ") + pMapFileName;
                    return false;
                }

                MapAssetInfo mixedMap = {};

                if (!loadOutdoorMapWithCompanionOptions(
                        assetFileSystem,
                        gameDataLoader,
                        pMapFileName,
                        MapLoadPurpose::HeadlessGameplay,
                        MapCompanionLoadOptions{
                            .allowSceneYml = true,
                            .allowLegacyCompanion = true,
                        },
                        mixedMap,
                        failure))
                {
                    return false;
                }

                if (mixedMap.authoredCompanionSource != AuthoredCompanionSource::SceneYml)
                {
                    failure = std::string("mixed companion loading did not prefer scene yml for ") + pMapFileName;
                    return false;
                }

                const std::string mixedSnapshot = buildNormalizedOutdoorAuthoredSnapshot(mixedMap);

                if (mixedSnapshot != migratedSnapshot)
                {
                    failure = std::string("mixed companion loading diverged for ") + pMapFileName;
                    return false;
                }
            }

            return true;
        }
    );

    std::cout << "Regression suite summary: passed=" << passedCount << " failed=" << failedCount << '\n';
    return failedCount == 0 ? 0 : 1;
}
}
