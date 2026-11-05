#include "game/scenario/ScenarioRuntimeDriver.h"

#include "game/gameplay/GameplayMonsterSpawn.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayHeldItemController.h"

#include "game/gameplay/GameplayInteractionController.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/items/CraftingRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellSchool.h"
#include "game/ui/GameplayCraftingBenchView.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayInputController.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/indoor/IndoorWorldRuntime.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include "game/tables/MapStats.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <bitset>
#include <cctype>
#include <cmath>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
float normalizedAngleDelta(float fromRadians, float toRadians)
{
    constexpr float Pi = 3.14159265358979323846f;
    float delta = toRadians - fromRadians;

    while (delta > Pi)
    {
        delta -= Pi * 2.0f;
    }

    while (delta < -Pi)
    {
        delta += Pi * 2.0f;
    }

    return delta;
}

float interpolatedAngle(float fromRadians, float toRadians, float ratio)
{
    return fromRadians + normalizedAngleDelta(fromRadians, toRadians) * ratio;
}

const char *scenarioDialogActionKindName(EventDialogActionKind kind)
{
    switch (kind)
    {
        case EventDialogActionKind::None:
            return "none";
        case EventDialogActionKind::HouseService:
            return "house_service";
        case EventDialogActionKind::HouseProprietor:
            return "house_proprietor";
        case EventDialogActionKind::HouseExtraExit:
            return "house_extra_exit";
        case EventDialogActionKind::HouseResident:
            return "house_resident";
        case EventDialogActionKind::NpcTopic:
            return "npc_topic";
        case EventDialogActionKind::ArenaChallenge:
            return "arena_challenge";
        case EventDialogActionKind::NpcProfessionNews:
            return "npc_profession_news";
        case EventDialogActionKind::NpcProfessionAction:
            return "npc_profession_action";
        case EventDialogActionKind::NpcProfessionDescription:
            return "npc_profession_description";
        case EventDialogActionKind::NpcHireOffer:
            return "npc_hire_offer";
        case EventDialogActionKind::NpcHireAccept:
            return "npc_hire_accept";
        case EventDialogActionKind::NpcHireDecline:
            return "npc_hire_decline";
        case EventDialogActionKind::NpcDismiss:
            return "npc_dismiss";
        case EventDialogActionKind::NpcBtb:
            return "npc_btb";
        case EventDialogActionKind::MapTransitionConfirm:
            return "map_transition_confirm";
        case EventDialogActionKind::MapTransitionReset:
            return "map_transition_reset";
        case EventDialogActionKind::MapTransitionCancel:
            return "map_transition_cancel";
        case EventDialogActionKind::RosterJoinOffer:
            return "roster_join_offer";
        case EventDialogActionKind::RosterJoinAccept:
            return "roster_join_accept";
        case EventDialogActionKind::RosterJoinDecline:
            return "roster_join_decline";
        case EventDialogActionKind::MasteryTeacherOffer:
            return "mastery_teacher_offer";
        case EventDialogActionKind::MasteryTeacherLearn:
            return "mastery_teacher_learn";
        case EventDialogActionKind::GuildMembershipOffer:
            return "guild_membership_offer";
        case EventDialogActionKind::GuildMembershipJoin:
            return "guild_membership_join";
        case EventDialogActionKind::GeneratedMercenaryJoinOffer:
            return "generated_mercenary_join_offer";
        case EventDialogActionKind::Mm9RudeTopic:
            return "mm9_rude_topic";
        case EventDialogActionKind::Mm9RudeSkillTrainerOffer:
            return "mm9_rude_skill_trainer_offer";
        case EventDialogActionKind::Mm9RudeSkillTrainerLearn:
            return "mm9_rude_skill_trainer_learn";
        case EventDialogActionKind::Mm9RudeSkillTrainerBack:
            return "mm9_rude_skill_trainer_back";
        case EventDialogActionKind::EventChoice:
            return "event_choice";
        default:
            break;
    }

    return "unknown";
}

std::string normalizeScenarioPromptAnswer(const std::string &value)
{
    size_t first = 0;
    while (first < value.size() && std::isspace(static_cast<unsigned char>(value[first])) != 0)
    {
        ++first;
    }

    size_t last = value.size();
    while (last > first && std::isspace(static_cast<unsigned char>(value[last - 1])) != 0)
    {
        --last;
    }

    std::string normalized;
    normalized.reserve(last - first);

    for (size_t index = first; index < last; ++index)
    {
        normalized.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(value[index]))));
    }

    return normalized;
}

uint64_t fnv1aUpdate(uint64_t hash, const std::string &text)
{
    for (char character : text)
    {
        hash ^= static_cast<unsigned char>(character);
        hash *= 1099511628211ull;
    }

    return hash;
}

uint64_t dialogLinesHash(const EventDialogContent &dialog)
{
    uint64_t hash = 1469598103934665603ull;

    for (const std::string &line : dialog.lines)
    {
        hash = fnv1aUpdate(hash, line);
        hash = fnv1aUpdate(hash, "\n");
    }

    return hash;
}
}

struct ScenarioGameApplicationAccess
{
    static bool loadGameData(GameApplication &application, Engine::AssetFileSystem &assetFileSystem)
    {
        // Headless scenarios do not render the menu frames that trigger deferred common-data loading.
        if (!application.loadGameData(assetFileSystem) || !application.ensureCommonGameDataLoaded())
        {
            return false;
        }

        // The local settings.ini's Immortal cheat would make every party damage check pass or fail by machine.
        application.m_settings.immortal = false;
        return true;
    }

    static bool activateWorldForMapFileName(GameApplication &application, const std::string &mapFileName)
    {
        return application.activateWorldForMapFileName(mapFileName);
    }

    static GameDataLoader &gameDataLoader(GameApplication &application)
    {
        return application.m_gameDataLoader;
    }

    static GameSession &gameSession(GameApplication &application)
    {
        return application.m_gameSession;
    }

    static bool applyRulesetOptions(GameApplication &application, const RulesetOptions &options, std::string &error)
    {
        return application.applyRulesetOptions(options, error);
    }

    static const GameSession &gameSession(const GameApplication &application)
    {
        return application.m_gameSession;
    }

    static IMapSceneRuntime *mapSceneRuntime(GameApplication &application)
    {
        return application.m_pMapSceneRuntime.get();
    }

    static const IMapSceneRuntime *mapSceneRuntime(const GameApplication &application)
    {
        return application.m_pMapSceneRuntime.get();
    }

    static bool runConsoleLine(GameApplication &application, const std::string &line, std::string &output)
    {
        application.registerDebugConsoleCommands();
        const size_t before = application.m_debugConsole.totalMessageCount();
        application.m_debugConsole.executeLine(line);
        const std::vector<DebugConsole::Message> &messages = application.m_debugConsole.messages();
        const size_t added = std::min(application.m_debugConsole.totalMessageCount() - before, messages.size());
        bool success = true;

        for (size_t index = messages.size() - added; index < messages.size(); ++index)
        {
            output += (output.empty() ? "" : "\n") + messages[index].text;
            success = success && messages[index].kind != DebugConsole::MessageKind::Error;
        }

        return success;
    }

    static OutdoorPartyRuntime *outdoorPartyRuntime(GameApplication &application)
    {
        return application.m_pOutdoorPartyRuntime.get();
    }

    static OutdoorWorldRuntime *outdoorWorldRuntime(GameApplication &application)
    {
        return application.m_pOutdoorWorldRuntime.get();
    }

    static OutdoorGameView &outdoorGameView(GameApplication &application)
    {
        return application.m_outdoorGameView;
    }

    static IndoorRenderer &indoorRenderer(GameApplication &application)
    {
        return application.m_indoorRenderer;
    }

    static IndoorGameView &indoorGameView(GameApplication &application)
    {
        return application.m_indoorGameView;
    }

    static void shutdownRenderer(GameApplication &application)
    {
        application.shutdownRenderer();
    }

    static bool initializeSelectedMapRuntime(GameApplication &application, bool initializeView)
    {
        return application.initializeSelectedMapRuntime(initializeView);
    }

    static bool processPendingMapMove(GameApplication &application)
    {
        return application.processPendingMapMove();
    }

    static bool quickSaveToPath(
        GameApplication &application,
        const std::filesystem::path &path,
        const std::string &saveName)
    {
        return application.quickSaveToPath(path, saveName);
    }

    static bool quickLoadFromPath(GameApplication &application, const std::filesystem::path &path)
    {
        return application.quickLoadFromPath(path, true);
    }

    static bool pressQuickLoad(GameApplication &application)
    {
        application.m_pendingQuickLoad = true;
        return application.processPendingQuickSaveInput();
    }

    static bool activateRuleset(GameApplication &application, const std::string &rulesetId, std::string &error)
    {
        return application.activateRuleset(rulesetId, error);
    }

    static void captureCurrentSceneState(GameApplication &application)
    {
        application.captureCurrentSceneState();
    }

    static void applyRulesMapLeave(GameApplication &application)
    {
        application.applyRulesMapLeave();
    }

    static bool applyAiArena(
        GameApplication &application, const AiArena &arena, const std::filesystem::path &logPath, std::string &error)
    {
        return application.applyAiArena(arena, logPath, error);
    }

    static const ActorAiTrace &aiTrace(const GameApplication &application)
    {
        return application.m_aiArenaTrace;
    }

    // Poses the actors' 3D models as a frame of the game does (headless: the animation trace's presentation).
    static bool syncActorModels(GameApplication &application, IGameplayWorldRuntime &world, float deltaSeconds)
    {
        return application.syncActorModels(world, deltaSeconds, deltaSeconds);
    }

    static const std::vector<size_t> &aiArenaActorIndices(const GameApplication &application)
    {
        return application.m_aiArenaActorIndices;
    }

    static void bindPartyDependencies(const GameApplication &application, Party &party)
    {
        application.bindPartyDependencies(party);
    }

    static void submitPendingInputPrompt(GameApplication &application, const std::string &text)
    {
        application.m_pendingInputText = text;
        application.finishPendingInputPrompt(true);
    }
};

namespace
{
constexpr int ScenarioViewWidth = 640;
constexpr int ScenarioViewHeight = 480;
constexpr float RuntimeStepSeconds = 1.0f / 30.0f;
constexpr size_t ScenarioMaxWorldItemsToScan = 4096;
constexpr int ScenarioCombatLootDamage = 1000000;
constexpr float ScenarioCombatDeathAdvanceSeconds = 6.0f;

bool setDummyAudioDriver(std::string &failure)
{
    SDL_Environment *pEnvironment = SDL_GetEnvironment();

    if (pEnvironment == nullptr || !SDL_SetEnvironmentVariable(pEnvironment, "SDL_AUDIODRIVER", "dummy", true))
    {
        failure = "could not force dummy audio driver for scenario runtime";
        return false;
    }

    return true;
}

void setScenarioActionHeld(
    GameplayInputFrame &input,
    KeyboardAction action,
    SDL_Scancode scancode,
    bool held)
{
    input.actions[keyboardActionIndex(action)].held = held;
    input.keyboardHeld[scancode] = held;
}

GameplayInputFrame buildMovementInputFrame(const ScenarioMovementCommand &command)
{
    GameplayInputFrame input = {};
    input.screenWidth = ScenarioViewWidth;
    input.screenHeight = ScenarioViewHeight;
    input.pointerX = ScenarioViewWidth * 0.5f;
    input.pointerY = ScenarioViewHeight * 0.5f;

    setScenarioActionHeld(input, KeyboardAction::Forward, SDL_SCANCODE_W, command.forward);
    setScenarioActionHeld(input, KeyboardAction::Backward, SDL_SCANCODE_S, command.backward);
    setScenarioActionHeld(input, KeyboardAction::Left, SDL_SCANCODE_A, command.strafeLeft);
    setScenarioActionHeld(input, KeyboardAction::Right, SDL_SCANCODE_D, command.strafeRight);
    setScenarioActionHeld(input, KeyboardAction::Jump, SDL_SCANCODE_X, command.jump);
    setScenarioActionHeld(input, KeyboardAction::FlyUp, SDL_SCANCODE_PAGEUP, command.flyUp);
    setScenarioActionHeld(input, KeyboardAction::FlyDown, SDL_SCANCODE_PAGEDOWN, command.flyDown);

    input.keyboardHeld[SDL_SCANCODE_LSHIFT] = command.shift;
    input.keyboardHeld[SDL_SCANCODE_LCTRL] = command.ctrl;
    return input;
}

bool scenarioPartyHasItem(const Party *pParty, uint32_t itemId)
{
    if (pParty == nullptr || itemId == 0)
    {
        return false;
    }

    return pParty->inventoryItemCount(itemId) > 0 || pParty->heldItemIdForQueries() == itemId;
}

GameplayWorldHit buildScenarioActorHit(size_t actorIndex, const GameplayActorInspectState &inspectState)
{
    GameplayWorldHit hit = {};
    hit.hasHit = true;
    hit.kind = GameplayWorldHitKind::Actor;
    GameplayActorTargetHit actorHit = {};
    actorHit.actorIndex = actorIndex;
    actorHit.displayName = inspectState.displayName;
    hit.actor = actorHit;
    return hit;
}

GameplayWorldHit buildScenarioWorldItemHit(size_t worldItemIndex, const GameplayWorldItemInspectState &state)
{
    GameplayWorldHit hit = {};
    hit.hasHit = true;
    hit.kind = GameplayWorldHitKind::WorldItem;
    GameplayWorldItemTargetHit itemHit = {};
    itemHit.worldItemIndex = worldItemIndex;
    itemHit.objectDescriptionId = static_cast<uint16_t>(state.item.objectDescriptionId);
    hit.worldItem = itemHit;
    return hit;
}
}

ScenarioRuntimeDriver::ScenarioRuntimeDriver(
    const std::filesystem::path &basePath,
    const Engine::ApplicationConfig &config,
    Engine::AssetFileSystem &assetFileSystem)
    : m_basePath(basePath)
    , m_config(config)
    , m_pAssetFileSystem(&assetFileSystem)
    , m_application(config)
{
}

ScenarioRuntimeDriver::~ScenarioRuntimeDriver()
{
    ScenarioGameApplicationAccess::shutdownRenderer(m_application);
}

bool ScenarioRuntimeDriver::initialize(std::string &failure)
{
    if (m_initialized)
    {
        return true;
    }

    if (!setDummyAudioDriver(failure))
    {
        return false;
    }

    if (m_pAssetFileSystem == nullptr)
    {
        failure = "scenario asset file system is not available";
        return false;
    }

    if (!ScenarioGameApplicationAccess::loadGameData(m_application, *m_pAssetFileSystem))
    {
        failure = "could not load scenario gameplay data";
        return false;
    }

    m_initialized = true;
    return true;
}

void ScenarioRuntimeDriver::setMadnessLedgerFile(const std::filesystem::path &file)
{
    ScenarioGameApplicationAccess::gameSession(m_application).setMadnessLedgerFile(file);
}

bool ScenarioRuntimeDriver::startNewGame(
    uint32_t continentId,
    const std::string &startMapFileName,
    std::string &failure,
    const PartySeed *pSeed,
    const RulesetSelection &ruleset)
{
    if (!initialize(failure))
    {
        return false;
    }

    // The same ruleset activation and option check as a new game from party creation.
    if (!ScenarioGameApplicationAccess::activateRuleset(m_application, ruleset.id, failure))
    {
        return false;
    }

    const RulesetDefinition &activeRuleset =
        ScenarioGameApplicationAccess::gameDataLoader(m_application).activeRuleset();

    if (!activeRuleset.offers(ruleset.options))
    {
        failure = "the " + activeRuleset.name + " ruleset does not offer the scenario's options";
        return false;
    }

    // Match the live new-session teardown before installing a fresh party. Loading a map otherwise captures
    // the previous runtime party and map state over the newly supplied seed.
    GameSession &session = ScenarioGameApplicationAccess::gameSession(m_application);
    session.gameplayScreenRuntime().clearSharedUiRuntime();
    ScenarioGameApplicationAccess::shutdownRenderer(m_application);
    session.clear();
    session.setRuleset(ruleset);
    // A fixed root seed, so a scenario rolls the same bosses, affixes and loot on every run (audit ROB-2-8).
    constexpr uint64_t ScenarioRandomRootSeed = 0x5eed20261024ull;
    session.setRandomRootSeed(ScenarioRandomRootSeed);
    Party party;
    if (pSeed != nullptr)
    {
        ScenarioGameApplicationAccess::bindPartyDependencies(m_application, party);
        party.seed(*pSeed);
        party.restoreAll();
    }
    else
    {
        party.seed(Party::createDefaultSeed());
    }
    session.setPartyState(party);
    // As a new game from party creation: the ruleset's own start.
    Party &sessionParty = *session.partyState();
    sessionParty.rules().experience.prepareNewParty(sessionParty);
    session.setGameMinutes(9.0f * 60.0f);
    static_cast<void>(continentId);
    return loadSelectedMapRuntime(startMapFileName, failure);
}

bool ScenarioRuntimeDriver::holdGameplayAction(KeyboardAction action, float seconds, std::string &failure)
{
    if (!std::isfinite(seconds) || seconds <= 0.0f || worldRuntime() == nullptr)
    {
        failure = "gameplay action requires an active world and a positive finite duration";
        return false;
    }

    GameSession &session = ScenarioGameApplicationAccess::gameSession(m_application);
    GameplayInputFrame input = {};
    input.screenWidth = ScenarioViewWidth;
    input.screenHeight = ScenarioViewHeight;
    input.pointerX = ScenarioViewWidth * 0.5f;
    input.pointerY = ScenarioViewHeight * 0.5f;
    GameplayButtonInputState &button = input.actions[keyboardActionIndex(action)];
    button.held = true;
    button.pressed = true;
    float remaining = seconds;
    while (remaining > 0.0f)
    {
        const float deltaSeconds = std::min(RuntimeStepSeconds, remaining);
        // Use the same input, selection, recovery, targeting and combat path as the live game.
        session.updateGameplay(input, deltaSeconds, false);
        IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
        if (pWorldRuntime == nullptr)
        {
            session.bindCurrentGameplayInputFrame(nullptr);
            failure = "gameplay action lost its active world";
            return false;
        }
        if (!session.sharedInputFrameResult().worldInputBlocked
            && !session.sharedWorldInteractionBlockedThisFrame()
            && !session.gameplayScreenState().pendingSpellTarget().active)
        {
            pWorldRuntime->updateWorld(deltaSeconds);
            IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);
            if (pSceneRuntime != nullptr && pSceneRuntime->kind() == SceneKind::Indoor)
            {
                static_cast<IndoorSceneRuntime *>(pSceneRuntime)->advanceSimulation(deltaSeconds * 1000.0f);
            }
        }
        button.pressed = false;
        remaining -= deltaSeconds;
    }
    button.held = false;
    button.released = true;
    session.updateGameplay(input, 0.0f, false);
    session.bindCurrentGameplayInputFrame(nullptr);
    return true;
}

bool ScenarioRuntimeDriver::selectPartyMember(size_t memberIndex, std::string &failure)
{
    if (party() == nullptr || memberIndex >= 5 || party()->member(memberIndex) == nullptr)
    {
        failure = "select_member requires an existing party member index from zero to four";
        return false;
    }
    GameSession &session = ScenarioGameApplicationAccess::gameSession(m_application);
    GameplayInputFrame input = {};
    input.screenWidth = ScenarioViewWidth;
    input.screenHeight = ScenarioViewHeight;
    const SDL_Scancode scancode = SDL_Scancode(int(SDL_SCANCODE_1) + int(memberIndex));
    input.keyboardHeld[scancode] = true;
    input.keyboardPressCounts[scancode] = 1;
    session.updateGameplay(input, 0.0f, false);
    input.keyboardHeld[scancode] = false;
    input.keyboardPressCounts[scancode] = 0;
    session.updateGameplay(input, 0.0f, false);
    session.bindCurrentGameplayInputFrame(nullptr);
    if (party()->activeMemberIndex() != memberIndex)
    {
        failure = "shared character-selection input did not select the requested member";
        return false;
    }
    return true;
}

bool ScenarioRuntimeDriver::loadMap(const std::string &mapFileName, std::string &failure)
{
    if (!initialize(failure))
    {
        return false;
    }

    return loadSelectedMapRuntime(mapFileName, failure);
}

bool ScenarioRuntimeDriver::loadSelectedMapRuntime(const std::string &mapFileName, std::string &failure)
{
    if (ScenarioGameApplicationAccess::mapSceneRuntime(m_application) != nullptr)
    {
        ScenarioGameApplicationAccess::applyRulesMapLeave(m_application);
        ScenarioGameApplicationAccess::captureCurrentSceneState(m_application);
    }

    if (!ScenarioGameApplicationAccess::activateWorldForMapFileName(m_application, mapFileName))
    {
        failure = "could not activate scenario map '" + mapFileName + "'";
        return false;
    }

    if (!ScenarioGameApplicationAccess::gameDataLoader(m_application).loadMapByFileNameForGameplay(
            *m_pAssetFileSystem,
            mapFileName))
    {
        failure = "could not load scenario map '" + mapFileName + "'";
        return false;
    }

    ScenarioGameApplicationAccess::shutdownRenderer(m_application);

    if (!ScenarioGameApplicationAccess::initializeSelectedMapRuntime(m_application, true))
    {
        failure = "could not initialize scenario runtime for map '" + mapFileName + "'";
        return false;
    }

    if (ScenarioGameApplicationAccess::mapSceneRuntime(m_application) == nullptr)
    {
        failure = "scenario runtime was not initialized for map '" + mapFileName + "'";
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::processPendingMapMove(std::string &failure)
{
    std::optional<EventRuntimeState::MapTransitionTrace> lastRequested;
    std::optional<EventRuntimeState::MapTransitionTrace> lastConfirmed;
    std::optional<EventRuntimeState::MapTransitionTrace> lastCanceled;

    if (const EventRuntimeState *pState = eventRuntimeState())
    {
        lastRequested = pState->lastMapTransitionRequested;
        lastConfirmed = pState->lastMapTransitionConfirmed;
        lastCanceled = pState->lastMapTransitionCanceled;
    }

    if (!ScenarioGameApplicationAccess::processPendingMapMove(m_application))
    {
        failure = "no pending scenario map move could be processed";
        return false;
    }

    if (EventRuntimeState *pState = eventRuntimeState())
    {
        if (lastRequested)
        {
            pState->lastMapTransitionRequested = lastRequested;
        }

        if (lastConfirmed)
        {
            pState->lastMapTransitionConfirmed = lastConfirmed;
        }

        if (lastCanceled)
        {
            pState->lastMapTransitionCanceled = lastCanceled;
        }
    }

    // The live loop refreshes modal state and the transferred camera before the next input.
    // A neutral shared frame also clears the departing transition dialog's input-block flags.
    if (worldRuntime() != nullptr)
    {
        GameplayInputFrame input = {};
        input.screenWidth = ScenarioViewWidth;
        input.screenHeight = ScenarioViewHeight;
        input.pointerX = ScenarioViewWidth * 0.5f;
        input.pointerY = ScenarioViewHeight * 0.5f;
        GameSession &session = ScenarioGameApplicationAccess::gameSession(m_application);
        session.updateGameplay(input, 0.0f, false);
        session.bindCurrentGameplayInputFrame(nullptr);
    }

    return true;
}

bool ScenarioRuntimeDriver::openMapTransitionPrompt(uint32_t sourceId, std::string &failure)
{
    if (!initialize(failure))
    {
        return false;
    }

    if (worldRuntime() == nullptr)
    {
        failure = "cannot open map transition prompt without an active world runtime";
        return false;
    }

    EventRuntimeState *pEventRuntimeState = eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        failure = "cannot open map transition prompt without event runtime state";
        return false;
    }

    const MapStatsEntry *pCurrentMap =
        ScenarioGameApplicationAccess::gameDataLoader(m_application)
            .getMapStats()
            .findByFileName(currentMapFileName());
    const MapBoundaryEdge edge = static_cast<MapBoundaryEdge>(sourceId);
    const std::optional<MapEdgeTransition> *pTransition =
        pCurrentMap != nullptr ? pCurrentMap->edgeTransition(edge) : nullptr;

    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::MapTransition;
    context.sourceId = sourceId;
    context.boundaryTravel = true;
    std::optional<EventRuntimeState::PendingMapMove> move;

    if (pTransition != nullptr && pTransition->has_value())
    {
        const IGameplayWorldRuntime *pWorld = worldRuntime();
        move = buildBoundaryTravelMapMove(
            **pTransition,
            edge,
            pWorld->partyX(),
            pWorld->partyY(),
            pWorld->partyFootZ(),
            pWorld->gameplayCameraYawRadians());
        context.transitionMapMove = move;
    }

    pEventRuntimeState->pendingDialogueContext = context;
    pEventRuntimeState->pendingMapMove.reset();
    pEventRuntimeState->messages.clear();

    GameplayScreenRuntime &screenRuntime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    screenRuntime.ensurePendingEventDialogPresented(true);

    if (!screenRuntime.activeEventDialog().isActive)
    {
        failure = "map transition prompt did not open an active dialog";
        return false;
    }

    if (pTransition != nullptr && pTransition->has_value())
    {
        EventRuntimeState::MapTransitionTrace trace = {};
        trace.sourceKind = "map_boundary";
        trace.sourceId = sourceId;
        trace.confirmationRequired = true;
        trace.destinationMap = (*pTransition)->destinationMapFileName;
        trace.destinationName = (*pTransition)->destinationMapFileName;
        trace.travelDays = static_cast<uint32_t>(std::max(0, (*pTransition)->travelDays));
        trace.useStartPosition = move->useMapStartPosition;
        trace.x = move->x;
        trace.y = move->y;
        trace.z = move->z;
        trace.directionDegrees = move->directionDegrees;
        pEventRuntimeState->lastMapTransitionRequested = std::move(trace);
    }

    return true;
}

bool ScenarioRuntimeDriver::speakNpc(uint32_t npcId, std::string &failure)
{
    if (!initialize(failure))
    {
        return false;
    }

    if (worldRuntime() == nullptr)
    {
        failure = "cannot open NPC dialogue without an active world runtime";
        return false;
    }

    EventRuntimeState *pEventRuntimeState = eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        failure = "cannot open NPC dialogue without event runtime state";
        return false;
    }

    pEventRuntimeState->messages.clear();

    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::NpcTalk;
    context.sourceId = npcId;
    context.hostHouseId = pEventRuntimeState->dialogueState.hostHouseId;
    pEventRuntimeState->pendingDialogueContext = std::move(context);

    GameplayScreenRuntime &screenRuntime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    screenRuntime.ensurePendingEventDialogPresented(true);

    if (!screenRuntime.activeEventDialog().isActive)
    {
        failure = "NPC dialogue " + std::to_string(npcId) + " did not open an active dialog";
        return false;
    }

    if (screenRuntime.activeEventDialog().sourceId != npcId)
    {
        failure = "NPC dialogue opened source " + std::to_string(screenRuntime.activeEventDialog().sourceId)
            + " instead of " + std::to_string(npcId);
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::saveGameToPath(
    const std::filesystem::path &path,
    const std::string &saveName,
    std::string &failure)
{
    if (!initialize(failure))
    {
        return false;
    }

    if (!ScenarioGameApplicationAccess::quickSaveToPath(m_application, path, saveName))
    {
        failure = "could not save scenario game to '" + path.string() + "'";
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::loadGameFromPath(const std::filesystem::path &path, std::string &failure)
{
    if (!initialize(failure))
    {
        return false;
    }

    if (!ScenarioGameApplicationAccess::quickLoadFromPath(m_application, path))
    {
        failure = "could not load scenario game from '" + path.string() + "'";
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::pressQuickLoad(
    const std::filesystem::path &savePath,
    const std::filesystem::path &workDirectory,
    bool &loaded,
    std::string &status,
    std::string &failure)
{
    if (!initialize(failure))
    {
        return false;
    }

    std::error_code error;
    const std::filesystem::path quickSavePath = workDirectory / "saves" / "quicksave.oysav";
    std::filesystem::create_directories(quickSavePath.parent_path(), error);

    if (!error)
    {
        std::filesystem::copy_file(savePath, quickSavePath, std::filesystem::copy_options::overwrite_existing, error);
    }

    const std::filesystem::path previousDirectory = std::filesystem::current_path(error);

    if (error || !std::filesystem::exists(quickSavePath))
    {
        failure = "quick_load could not prepare '" + quickSavePath.string() + "' from '" + savePath.string() + "'";
        return false;
    }

    std::filesystem::current_path(workDirectory, error);

    if (error)
    {
        failure = "quick_load could not enter '" + workDirectory.string() + "': " + error.message();
        return false;
    }

    loaded = ScenarioGameApplicationAccess::pressQuickLoad(m_application);
    std::filesystem::current_path(previousDirectory, error);
    status = ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime().statusBarEventText();
    return true;
}

bool ScenarioRuntimeDriver::setPose(const ScenarioPose &pose, std::string &failure)
{
    if (!pose.mapFileName.empty()
        && (ScenarioGameApplicationAccess::mapSceneRuntime(m_application) == nullptr
            || currentMapFileName() != pose.mapFileName))
    {
        if (!loadMap(pose.mapFileName, failure))
        {
            return false;
        }
    }

    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);

    if (pSceneRuntime == nullptr)
    {
        failure = "cannot set scenario pose without an active map";
        return false;
    }

    if (pSceneRuntime->kind() == SceneKind::Outdoor)
    {
        OutdoorPartyRuntime *pPartyRuntime = ScenarioGameApplicationAccess::outdoorPartyRuntime(m_application);

        if (pPartyRuntime == nullptr)
        {
            failure = "cannot set outdoor scenario pose without outdoor party runtime";
            return false;
        }

        pPartyRuntime->teleportTo(pose.x, pose.y, pose.z);
        ScenarioGameApplicationAccess::outdoorGameView(m_application).setCameraAngles(
            pose.yawRadians,
            pose.pitchRadians);
        GameplayInputFrame input = {};
        input.screenWidth = ScenarioViewWidth;
        input.screenHeight = ScenarioViewHeight;
        if (OutdoorWorldRuntime *pOutdoorWorldRuntime =
            ScenarioGameApplicationAccess::outdoorWorldRuntime(m_application))
        {
            pOutdoorWorldRuntime->updateWorldMovement(input, 0.0f, true);
        }
        return true;
    }

    if (pSceneRuntime->kind() == SceneKind::Indoor)
    {
        IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(pSceneRuntime);
        pIndoorRuntime->partyRuntime().teleportPartyPosition(pose.x, pose.y, pose.z);
        const IndoorMoveState &moveState = pIndoorRuntime->partyRuntime().movementState();
        ScenarioGameApplicationAccess::indoorRenderer(m_application).setCameraPosition(
            moveState.x,
            moveState.y,
            moveState.eyeZ());
        ScenarioGameApplicationAccess::indoorRenderer(m_application).setCameraAngles(
            pose.yawRadians,
            pose.pitchRadians);
        return true;
    }

    failure = "unsupported scenario scene kind";
    return false;
}

bool setScenarioCameraAngles(GameApplication &application, float yawRadians, float pitchRadians)
{
    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(application);

    if (pSceneRuntime == nullptr)
    {
        return false;
    }

    if (pSceneRuntime->kind() == SceneKind::Outdoor)
    {
        ScenarioGameApplicationAccess::outdoorGameView(application).setCameraAngles(yawRadians, pitchRadians);
        return true;
    }

    if (pSceneRuntime->kind() == SceneKind::Indoor)
    {
        ScenarioGameApplicationAccess::indoorRenderer(application).setCameraAngles(yawRadians, pitchRadians);
        return true;
    }

    return false;
}

const RulesetSelection &ScenarioRuntimeDriver::ruleset() const
{
    return ScenarioGameApplicationAccess::gameSession(m_application).ruleset();
}

const MawRules *ScenarioRuntimeDriver::mawRules() const
{
    return ScenarioGameApplicationAccess::gameSession(m_application).mawRules();
}

const CombatLog &ScenarioRuntimeDriver::combatLog() const
{
    return ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime().combatLog();
}

ScenarioPose ScenarioRuntimeDriver::currentPose() const
{
    ScenarioPose pose = {};
    pose.mapFileName = currentMapFileName();

    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return pose;
    }

    pose.x = pWorldRuntime->partyX();
    pose.y = pWorldRuntime->partyY();
    pose.z = pWorldRuntime->partyFootZ();
    pose.yawRadians = pWorldRuntime->gameplayCameraYawRadians();
    pose.pitchRadians = pWorldRuntime->gameplayCameraPitchRadians();
    return pose;
}

bool ScenarioRuntimeDriver::simulateMovementSegment(
    const ScenarioMovementCommand &command,
    ScenarioMovementResult &result,
    std::string &failure)
{
    if (!setPose(command.startPose, failure))
    {
        return false;
    }

    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot simulate movement without an active world runtime";
        return false;
    }

    result.startPose = currentPose();

    if (command.durationSeconds < 0.0f)
    {
        failure = "cannot simulate movement for a negative duration";
        return false;
    }

    GameplayInputFrame input = buildMovementInputFrame(command);
    input.turboMovementEnabled = ScenarioGameApplicationAccess::gameSession(m_application)
        .gameplayScreenRuntime().settingsSnapshot().turboMovementEnabled;
    float remainingSeconds = command.durationSeconds;
    float elapsedSeconds = 0.0f;
    pWorldRuntime->setScenarioPartyActorCollisionEnabled(command.actorCollision);

    while (remainingSeconds > 0.0f)
    {
        const float deltaSeconds = std::min(RuntimeStepSeconds, remainingSeconds);

        if (command.endYawRadians || command.endPitchRadians)
        {
            const float ratio = command.durationSeconds > 0.0f
                ? std::clamp(elapsedSeconds / command.durationSeconds, 0.0f, 1.0f)
                : 1.0f;
            const float yawRadians = command.endYawRadians
                ? interpolatedAngle(command.startPose.yawRadians, *command.endYawRadians, ratio)
                : command.startPose.yawRadians;
            const float pitchRadians = command.endPitchRadians
                ? command.startPose.pitchRadians + (*command.endPitchRadians - command.startPose.pitchRadians) * ratio
                : command.startPose.pitchRadians;

            setScenarioCameraAngles(m_application, yawRadians, pitchRadians);
        }

        if (command.actorAi)
        {
            GameSession &session = ScenarioGameApplicationAccess::gameSession(m_application);
            session.updateGameplay(input, deltaSeconds, false);
            session.bindCurrentGameplayInputFrame(nullptr);
        }
        else
        {
            // Explicit geometry-only diagnostics omit AI and the shared gameplay update.
            pWorldRuntime->updateWorldMovement(input, deltaSeconds, true);
        }
        pWorldRuntime->updateWorld(deltaSeconds);

        IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);
        if (pSceneRuntime != nullptr && pSceneRuntime->kind() == SceneKind::Indoor)
        {
            static_cast<IndoorSceneRuntime *>(pSceneRuntime)->advanceSimulation(deltaSeconds * 1000.0f);
        }

        // An arena poses its monsters' models as the window does, so it plays as the window plays: a model's
        // missile leaves from its release socket (WorldFxSystem::actorLaunchPoint). trace_animation only adds the
        // `anim` lines.
        if (pWorldRuntime->actorAiTrace() != nullptr
            && !ScenarioGameApplicationAccess::syncActorModels(m_application, *pWorldRuntime, deltaSeconds))
        {
            failure = "actor models failed to load";
            return false;
        }

        elapsedSeconds += deltaSeconds;
        remainingSeconds -= deltaSeconds;

        if (EventRuntimeState *pEventRuntimeState = eventRuntimeState())
        {
            if (pEventRuntimeState->pendingMapMove.has_value())
            {
                if (!processPendingMapMove(failure))
                {
                    pWorldRuntime->setScenarioPartyActorCollisionEnabled(true);
                    return false;
                }

                pWorldRuntime = worldRuntime();
                if (pWorldRuntime == nullptr)
                {
                    failure = "movement segment map transition left no active world runtime";
                    return false;
                }
                pWorldRuntime->setScenarioPartyActorCollisionEnabled(command.actorCollision);
            }
        }
    }

    if (command.endYawRadians || command.endPitchRadians)
    {
        const float yawRadians = command.endYawRadians ? *command.endYawRadians : command.startPose.yawRadians;
        const float pitchRadians = command.endPitchRadians ? *command.endPitchRadians : command.startPose.pitchRadians;
        setScenarioCameraAngles(m_application, yawRadians, pitchRadians);
    }

    pWorldRuntime->setScenarioPartyActorCollisionEnabled(true);
    result.finalPose = currentPose();
    return true;
}

bool ScenarioRuntimeDriver::waterStatus(ScenarioWaterStatus &status, std::string &failure)
{
    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);

    if (pSceneRuntime == nullptr || pSceneRuntime->kind() != SceneKind::Indoor)
    {
        failure = "the water assertion needs an indoor map";
        return false;
    }

    const IndoorPartyRuntime &partyRuntime = static_cast<IndoorSceneRuntime *>(pSceneRuntime)->partyRuntime();
    status.state = indoorSwimStateName(partyRuntime.swimState());
    status.eyeUnder = partyRuntime.eyeUnderWater();
    status.breath = partyRuntime.breathFraction().value_or(1.0f);
    status.drowningTicks = partyRuntime.drowningTicks();
    status.footZ = partyRuntime.movementState().footZ;
    return true;
}

bool ScenarioRuntimeDriver::actorInspectState(
    size_t actorIndex,
    GameplayActorInspectState &inspectState,
    GameplayRuntimeActorState &runtimeState,
    bool &hasRuntimeState,
    std::string &failure) const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot inspect actor without an active world runtime";
        return false;
    }

    if (actorIndex >= pWorldRuntime->mapActorCount())
    {
        failure = "actor index " + std::to_string(actorIndex) + " is out of range";
        return false;
    }

    if (!pWorldRuntime->actorInspectState(actorIndex, 0, inspectState))
    {
        failure = "actor index " + std::to_string(actorIndex) + " has no inspect state";
        return false;
    }

    hasRuntimeState = pWorldRuntime->actorRuntimeState(actorIndex, runtimeState);
    return true;
}

size_t ScenarioRuntimeDriver::mapActorCount() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->mapActorCount() : 0;
}

bool ScenarioRuntimeDriver::fireActorProjectileAtParty(
    size_t actorIndex, GameplayActorAttackAbility ability, int damage, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr || actorIndex >= pWorldRuntime->mapActorCount()
        || !pWorldRuntime->debugFireActorProjectileAtParty(actorIndex, ability, damage))
    {
        failure = "fire_actor_projectile: actor " + std::to_string(actorIndex) + " fired nothing";
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::blinkActor(size_t actorIndex, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr || actorIndex >= pWorldRuntime->mapActorCount()
        || !pWorldRuntime->blinkActor(actorIndex))
    {
        failure = "blink_actor: actor " + std::to_string(actorIndex) + " did not blink";
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::chargeActor(size_t actorIndex, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr || actorIndex >= pWorldRuntime->mapActorCount()
        || !pWorldRuntime->chargeActor(actorIndex))
    {
        failure = "charge_actor: actor " + std::to_string(actorIndex) + " did not start a charge";
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::frenzyActor(size_t actorIndex, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr || actorIndex >= pWorldRuntime->mapActorCount()
        || !pWorldRuntime->frenzyActor(actorIndex))
    {
        failure = "frenzy_actor: actor " + std::to_string(actorIndex) + " did not start a frenzy";
        return false;
    }

    return true;
}

std::optional<GameplayChargeCounts> ScenarioRuntimeDriver::chargeCounts() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->chargeCounts() : std::nullopt;
}

const GameplayProjectileService *ScenarioRuntimeDriver::projectileService() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    return pWorldRuntime != nullptr ? pWorldRuntime->projectileServiceView() : nullptr;
}

bool ScenarioRuntimeDriver::spawnActor(int16_t monsterId, uint32_t count, float x, float y, float z, uint32_t group,
    uint8_t bossAffix, bool partyAlly, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    // A party ally: summoned as a party spell's summon is, for a day, by no member.
    if (partyAlly)
    {
        constexpr float AllySeconds = 24.0f * 60.0f * 60.0f;

        if (pWorldRuntime == nullptr || bossAffix != 0
            || !pWorldRuntime->summonFriendlyMonsterById(monsterId, count, AllySeconds, x, y, z, -1))
        {
            failure = "spawn_actor could not summon party ally " + std::to_string(monsterId);
            return false;
        }

        return true;
    }

    if (pWorldRuntime != nullptr && bossAffix != 0)
    {
        GameplayMonsterSpawnRequest request;
        request.monsterId = monsterId;
        request.count = count;
        request.x = x;
        request.y = y;
        request.z = z;
        request.radius = 1.0f;
        request.group = group;
        request.boss = true;
        request.bossAffix = bossAffix;

        if (pWorldRuntime->spawnMonsters(request).size() == count)
        {
            return true;
        }
    }

    if (pWorldRuntime == nullptr || bossAffix != 0
        || !pWorldRuntime->summonHostileMonsterById(monsterId, count, x, y, z, group))
    {
        failure = "spawn_actor could not summon monster " + std::to_string(monsterId);
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::applyAiArena(
    const AiArena &arena, const std::filesystem::path &logPath, std::string &failure)
{
    if ((ScenarioGameApplicationAccess::mapSceneRuntime(m_application) == nullptr
            || currentMapFileName() != arena.map)
        && !loadMap(arena.map, failure))
    {
        return false;
    }

    return ScenarioGameApplicationAccess::applyAiArena(m_application, arena, logPath, failure);
}

const ActorAiTrace &ScenarioRuntimeDriver::aiTrace() const
{
    return ScenarioGameApplicationAccess::aiTrace(m_application);
}

const std::vector<size_t> &ScenarioRuntimeDriver::aiArenaActorIndices() const
{
    return ScenarioGameApplicationAccess::aiArenaActorIndices(m_application);
}

bool ScenarioRuntimeDriver::setRulesetOptions(const std::string &optionIds, std::string &failure)
{
    RulesetOptions options = ScenarioGameApplicationAccess::gameSession(m_application).ruleset().options;

    if (!applyRulesetOptionIds(optionIds, options))
    {
        failure = "set_ruleset: unknown option in '" + optionIds + "'";
        return false;
    }

    return ScenarioGameApplicationAccess::applyRulesetOptions(m_application, options, failure);
}

bool ScenarioRuntimeDriver::damageActor(
    size_t actorIndex, int amount, ShieldAttackTier shieldTier, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    GameplayRuntimeActorState state = {};

    if (pWorldRuntime == nullptr || amount <= 0 || !pWorldRuntime->actorRuntimeState(actorIndex, state)
        || state.isDead)
    {
        failure = "damage_actor needs an active map, a living actor " + std::to_string(actorIndex)
            + " and a positive amount";
        return false;
    }

    const ScenarioPose pose = currentPose();

    if (!pWorldRuntime->applyPartyAttackMeleeDamage(
            actorIndex, amount, GameplayWorldPoint{pose.x, pose.y, pose.z}, shieldTier))
    {
        failure = "damage_actor could not damage actor " + std::to_string(actorIndex);
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::partyAttack(
    const ScenarioPartyAttackRequest &request, ScenarioPartyAttackResult &result, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    Party *pParty = party();
    GameplayRuntimeActorState state = {};

    if (pWorldRuntime == nullptr || pParty == nullptr || pParty->member(request.memberIndex) == nullptr
        || !pWorldRuntime->actorRuntimeState(request.actorIndex, state) || state.isDead || request.count <= 0)
    {
        failure = "party_attack needs an active map, member " + std::to_string(request.memberIndex)
            + ", a living actor " + std::to_string(request.actorIndex) + " and a positive count";
        return false;
    }

    GameDataLoader &data = ScenarioGameApplicationAccess::gameDataLoader(m_application);
    Character &member = *pParty->member(request.memberIndex);
    const std::bitset<CharacterConditionCount> conditionsBefore = member.conditions;
    const std::string attackSpellBefore = member.attackSpellName;
    GameplayScreenRuntime &screenRuntime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();

    for (CharacterCondition condition : request.conditions)
    {
        member.conditions.set(size_t(condition));
    }

    if (request.attackSpell)
    {
        member.attackSpellName = *request.attackSpell;
    }

    double damage = 0;
    double applied = 0;
    double recovery = 0;
    result = {};

    for (int attack = 0; attack < request.count; ++attack)
    {
        member.recoverySecondsRemaining = 0;
        pParty->setActiveMemberIndex(request.memberIndex);
        pWorldRuntime->actorRuntimeState(request.actorIndex, state);

        if (state.isDead)
        {
            failure = "party_attack: actor " + std::to_string(request.actorIndex) + " died after "
                + std::to_string(attack) + " attacks";
            member.conditions = conditionsBefore;
            member.attackSpellName = attackSpellBefore;
            return false;
        }
        // Within reach of a blow, one step off the actor.
        const GameplayActionController::PartyAttackExecutionResult outcome =
            GameplayActionController::executePartyAttack(GameplayActionController::PartyAttackConfig{
                .pRuntime = request.attackSpell ? &screenRuntime : nullptr,
                .pSpellService = request.attackSpell ? &screenRuntime.spellService() : nullptr,
                .pWorldRuntime = pWorldRuntime,
                .pParty = pParty,
                .pItemTable = &data.getItemTable(),
                .pSpellTable = &data.getSpellTable(),
                .pMonsterTable = &data.getMonsterTable(),
                .pSpecialItemEnchantTable = &data.getSpecialItemEnchantTable(),
                .directTargetActorIndex = request.actorIndex,
                .partyPosition = {state.preciseX + 64.0f, state.preciseY, state.preciseZ},
                .randomSeed = uint32_t(attack + 1) * 2654435761u,
            });
        GameplayRuntimeActorState after = {};
        pWorldRuntime->actorRuntimeState(request.actorIndex, after);
        const int lost = std::max(0, state.currentHp - after.currentHp);

        // A blow that kills cannot be healed away: the run needs a sturdier target.
        if (after.isDead || after.currentHp <= 0)
        {
            failure = "party_attack: actor " + std::to_string(request.actorIndex) + " died on attack "
                + std::to_string(attack + 1) + "; use a sturdier target";
            member.conditions = conditionsBefore;
            member.attackSpellName = attackSpellBefore;
            return false;
        }

        if (lost > 0)
        {
            pWorldRuntime->healMapActor(request.actorIndex, lost);
        }

        ++result.attacks;
        result.weaponAttacks += outcome.actionPerformed ? 1 : 0;
        recovery += outcome.attack.recoverySeconds;

        if (outcome.attacked && outcome.attack.hit)
        {
            ++result.hits;
            result.criticals += outcome.attack.criticalDamage ? 1 : 0;
            damage += outcome.attack.damage;
            applied += lost;
        }
    }

    member.conditions = conditionsBefore;
    member.attackSpellName = attackSpellBefore;
    member.recoverySecondsRemaining = 0;
    result.averageDamage = result.hits > 0 ? damage / result.hits : 0;
    result.averageAppliedDamage = result.hits > 0 ? applied / result.hits : 0;
    result.averageRecoverySeconds = recovery / result.attacks;
    return true;
}

bool ScenarioRuntimeDriver::executeCombatLoot(
    const ScenarioCombatLootRequest &request,
    ScenarioCombatLootResult &result,
    std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot execute combat loot without an active world runtime";
        return false;
    }

    size_t actorIndex = request.actorIndex.value_or(GameplayInvalidWorldIndex);

    if (actorIndex == GameplayInvalidWorldIndex)
    {
        if (request.targetName.empty())
        {
            failure = "combat loot requires either actor_index or target";
            return false;
        }

        for (size_t candidate = 0; candidate < pWorldRuntime->mapActorCount(); ++candidate)
        {
            GameplayActorInspectState candidateInspect = {};

            if (!pWorldRuntime->actorInspectState(candidate, 0, candidateInspect))
            {
                continue;
            }

            if (!candidateInspect.isDead && candidateInspect.displayName == request.targetName)
            {
                actorIndex = candidate;
                break;
            }
        }
    }

    if (actorIndex == GameplayInvalidWorldIndex || actorIndex >= pWorldRuntime->mapActorCount())
    {
        failure = "could not resolve combat loot actor '" + request.targetName + "'";
        return false;
    }

    result.actorIndex = actorIndex;

    GameplayActorInspectState inspectState = {};

    if (!pWorldRuntime->actorInspectState(actorIndex, 0, inspectState))
    {
        failure = "combat loot actor " + std::to_string(actorIndex) + " has no inspect state";
        return false;
    }

    if (!inspectState.isDead)
    {
        const ScenarioPose pose = currentPose();
        GameplayWorldPoint source = {};
        source.x = pose.x;
        source.y = pose.y;
        source.z = pose.z;
        IndoorWorldRuntime *pIndoorWorldRuntime = dynamic_cast<IndoorWorldRuntime *>(pWorldRuntime);
        if (pIndoorWorldRuntime != nullptr)
        {
            result.damageApplied = pIndoorWorldRuntime->applyPartyAttackMeleeDamage(
                actorIndex,
                ScenarioCombatLootDamage,
                CombatDamageType::Irresistible,
                source,
                ShieldAttackTier::Physical);
        }
        else
        {
            result.damageApplied =
                pWorldRuntime->applyPartyAttackMeleeDamage(
                    actorIndex, ScenarioCombatLootDamage, source, ShieldAttackTier::Physical);
        }

        if (!result.damageApplied)
        {
            failure = "combat loot could not apply party damage to actor " + std::to_string(actorIndex);
            return false;
        }

        if (!advanceRuntime(ScenarioCombatDeathAdvanceSeconds, failure))
        {
            return false;
        }

        pWorldRuntime = worldRuntime();

        if (pWorldRuntime == nullptr)
        {
            failure = "combat loot lost active world runtime after death advance";
            return false;
        }

        if (!pWorldRuntime->actorInspectState(actorIndex, 0, inspectState))
        {
            failure = "combat loot actor " + std::to_string(actorIndex) + " lost inspect state after death";
            return false;
        }
    }

    if (request.expectedItemId != 0 && scenarioPartyHasItem(party(), request.expectedItemId))
    {
        result.expectedItemAcquired = true;
        return true;
    }

    if (inspectState.isDead)
    {
        const GameplayWorldHit actorHit = buildScenarioActorHit(actorIndex, inspectState);
        result.corpseActivated = pWorldRuntime->activateWorldHit(actorHit);

        if (request.expectedItemId == 0 || scenarioPartyHasItem(party(), request.expectedItemId))
        {
            result.expectedItemAcquired = request.expectedItemId != 0;
            return true;
        }
    }

    if (request.expectedItemId == 0)
    {
        return inspectState.isDead || result.corpseActivated;
    }

    for (size_t worldItemIndex = 0; worldItemIndex < ScenarioMaxWorldItemsToScan; ++worldItemIndex)
    {
        GameplayWorldItemInspectState worldItemState = {};

        if (!pWorldRuntime->worldItemInspectState(worldItemIndex, worldItemState)
            || worldItemState.isGold
            || worldItemState.item.objectDescriptionId != request.expectedItemId)
        {
            continue;
        }

        result.expectedItemExposed = true;
        return true;
    }

    failure = "combat loot did not acquire expected item " + std::to_string(request.expectedItemId)
        + " from actor " + std::to_string(actorIndex);
    return false;
}

ScenarioInteractionResult ScenarioRuntimeDriver::activateActor(size_t actorIndex, std::string &failure)
{
    ScenarioInteractionResult result = {};
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot activate actor without an active world runtime";
        return result;
    }

    if (actorIndex >= pWorldRuntime->mapActorCount())
    {
        failure = "actor index " + std::to_string(actorIndex) + " is out of range";
        return result;
    }

    GameplayActorInspectState inspectState = {};

    if (!pWorldRuntime->actorInspectState(actorIndex, 0, inspectState))
    {
        failure = "actor index " + std::to_string(actorIndex) + " has no inspect state";
        return result;
    }

    result.hit = buildScenarioActorHit(actorIndex, inspectState);
    result.picked = true;
    result.activated = pWorldRuntime->activateWorldHit(result.hit);

    if (!result.activated)
    {
        failure = "actor activation failed for actor " + std::to_string(actorIndex);
    }

    return result;
}

ScenarioInteractionResult ScenarioRuntimeDriver::activateWorldItem(
    size_t worldItemIndex,
    std::optional<uint16_t> recordedObjectDescriptionId,
    std::optional<uint16_t> recordedSpriteId,
    std::string &failure)
{
    ScenarioInteractionResult result = {};
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot activate world item without an active world runtime";
        return result;
    }

    GameplayWorldItemInspectState worldItemState = {};

    if (!pWorldRuntime->worldItemInspectState(worldItemIndex, worldItemState))
    {
        failure = "world item index " + std::to_string(worldItemIndex) + " has no inspect state";
        return result;
    }

    result.mapFileName = currentMapFileName();
    result.hit = buildScenarioWorldItemHit(worldItemIndex, worldItemState);

    if (result.hit.worldItem)
    {
        if (recordedObjectDescriptionId)
        {
            result.hit.worldItem->objectDescriptionId = *recordedObjectDescriptionId;
        }

        if (recordedSpriteId)
        {
            result.hit.worldItem->objectSpriteId = *recordedSpriteId;
        }
    }

    result.picked = true;
    result.activated = pWorldRuntime->activateWorldHit(result.hit);

    if (!result.activated)
    {
        failure = "world item activation failed for item " + std::to_string(worldItemIndex);
    }

    return result;
}

bool ScenarioRuntimeDriver::worldItemContainsItem(
    std::optional<size_t> worldItemIndex,
    uint32_t itemId,
    bool &containsItem,
    std::string &failure) const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    containsItem = false;

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot inspect world item without an active world runtime";
        return false;
    }

    const size_t startIndex = worldItemIndex.value_or(0);
    const size_t endIndex = worldItemIndex ? *worldItemIndex + 1 : ScenarioMaxWorldItemsToScan;

    for (size_t candidateIndex = startIndex; candidateIndex < endIndex; ++candidateIndex)
    {
        GameplayWorldItemInspectState state = {};

        if (pWorldRuntime->worldItemInspectState(candidateIndex, state)
            && !state.isGold
            && state.item.objectDescriptionId == itemId)
        {
            containsItem = true;
            return true;
        }
    }

    return true;
}

bool ScenarioRuntimeDriver::activeChestContainsItem(
    std::optional<uint32_t> chestId,
    uint32_t itemId,
    bool &containsItem,
    std::string &failure) const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    containsItem = false;

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot inspect active chest without an active world runtime";
        return false;
    }

    const GameplayChestViewState *pChestView = pWorldRuntime->activeChestView();

    if (pChestView == nullptr)
    {
        return true;
    }

    if (chestId && pChestView->chestId != *chestId)
    {
        return true;
    }

    for (const GameplayChestItemState &item : pChestView->items)
    {
        if (!item.isGold && item.item.objectDescriptionId == itemId)
        {
            containsItem = true;
            return true;
        }
    }

    for (const GameplayChestItemState &item : pChestView->hiddenItems)
    {
        if (!item.isGold && item.item.objectDescriptionId == itemId)
        {
            containsItem = true;
            return true;
        }
    }

    return true;
}

bool ScenarioRuntimeDriver::takeActiveChestItemById(
    std::optional<uint32_t> chestId,
    uint32_t itemId,
    GameplayChestItemState &item,
    std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot take active chest item without an active world runtime";
        return false;
    }

    GameplayScreenRuntime &screenRuntime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    if (screenRuntime.heldInventoryItem().active)
    {
        failure = "cannot take a chest item while the cursor already holds an item";
        return false;
    }

    const GameplayChestViewState *pChestView = pWorldRuntime->activeChestView();

    if (pChestView == nullptr)
    {
        failure = "no active chest is open";
        return false;
    }

    if (chestId && pChestView->chestId != *chestId)
    {
        failure = "active chest " + std::to_string(pChestView->chestId)
            + " does not match expected chest " + std::to_string(*chestId);
        return false;
    }

    for (size_t itemIndex = 0; itemIndex < pChestView->items.size(); ++itemIndex)
    {
        const GameplayChestItemState &candidate = pChestView->items[itemIndex];
        const uint32_t candidateItemId =
            candidate.item.objectDescriptionId != 0 ? candidate.item.objectDescriptionId : candidate.itemId;

        if (candidate.isGold || candidateItemId != itemId)
        {
            continue;
        }

        if (!pWorldRuntime->takeActiveChestItem(itemIndex, item))
        {
            failure = "failed to take item " + std::to_string(itemId) + " from active chest";
            return false;
        }

        // Use the same held-item owner as real chest clicks. A Party query-only copy disappears
        // at save/load because the save serializes GameplayScreenRuntime's cursor state.
        InventoryItem heldItem = item.item;
        heldItem.objectDescriptionId = candidateItemId;
        heldItem.quantity = std::max(1u, heldItem.quantity);
        GameplayHeldItemController::setHeldInventoryItem(screenRuntime.heldInventoryItem(), heldItem);
        screenRuntime.party()->setHeldItemForQueries(heldItem);

        return true;
    }

    failure = "active chest does not contain item " + std::to_string(itemId);
    return false;
}

bool ScenarioRuntimeDriver::takeInventoryItemToCursor(
    size_t memberIndex, uint8_t gridX, uint8_t gridY, std::string &failure)
{
    GameplayScreenRuntime &runtime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    Party *pParty = runtime.party();
    InventoryItem item;
    if (pParty == nullptr || runtime.heldInventoryItem().active
        || !pParty->takeItemFromMemberInventoryCell(memberIndex, gridX, gridY, item))
    {
        failure = "could not take inventory item onto the empty cursor";
        return false;
    }
    GameplayHeldItemController::setHeldInventoryItem(runtime.heldInventoryItem(), item);
    pParty->setHeldItemForQueries(item);
    return true;
}

bool ScenarioRuntimeDriver::placeHeldItemInInventory(std::string &failure)
{
    GameplayScreenRuntime &runtime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    Party *pParty = runtime.party();
    if (pParty == nullptr || !runtime.heldInventoryItem().active)
    {
        failure = "no actual cursor item is available to place in inventory";
        return false;
    }
    if (!runtime.tryAutoPlaceHeldInventoryItemOnPartyMember(pParty->activeMemberIndex(), false))
    {
        failure = "held item does not fit the active member's inventory";
        return false;
    }
    pParty->clearHeldItemForQueries();
    return true;
}

MawRules *ScenarioRuntimeDriver::mawRules()
{
    return ScenarioGameApplicationAccess::gameSession(m_application).mawRules();
}

bool ScenarioRuntimeDriver::runConsoleLine(const std::string &line, std::string &output, std::string &failure)
{
    if (!ScenarioGameApplicationAccess::runConsoleLine(m_application, line, output))
    {
        failure = "console: " + line + ": " + output;
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::setRulesetBanks(const std::array<double, 4> &levels, std::string &failure)
{
    MawRules *pMawRules = ScenarioGameApplicationAccess::gameSession(m_application).mawRules();

    if (pMawRules == nullptr)
    {
        failure = "ruleset_banks needs a MAW game";
        return false;
    }

    MawGameState state = pMawRules->state();

    for (size_t continent = 0; continent < levels.size() && continent < MawGameState::ContinentCount; ++continent)
    {
        state.continentLevels[continent] = levels[continent];
    }

    pMawRules->setState(state);
    return true;
}

bool ScenarioRuntimeDriver::grantItem(
    size_t memberIndex,
    const InventoryItem &item,
    uint32_t count,
    std::optional<EquipmentSlot> equipSlot,
    std::string &failure)
{
    Party *pParty = party();

    if (pParty == nullptr || pParty->member(memberIndex) == nullptr)
    {
        failure = "grant_item needs a party member " + std::to_string(memberIndex);
        return false;
    }

    if (equipSlot)
    {
        std::optional<InventoryItem> held;

        if (!pParty->tryEquipItemOnMember(memberIndex, *equipSlot, item, std::nullopt, true, held))
        {
            failure = "grant_item: member " + std::to_string(memberIndex) + " cannot wear item "
                + std::to_string(item.objectDescriptionId);
            return false;
        }

        return true;
    }

    for (uint32_t index = 0; index < count; ++index)
    {
        if (!pParty->tryAutoPlaceItemInMemberInventory(memberIndex, item) && !pParty->tryGrantInventoryItem(item))
        {
            failure = "grant_item: no room for item " + std::to_string(item.objectDescriptionId);
            return false;
        }
    }

    return true;
}

bool ScenarioRuntimeDriver::useInventoryItem(size_t memberIndex, uint32_t itemId, bool &used, std::string &failure)
{
    GameplayScreenRuntime &runtime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    Party *pParty = runtime.party();
    const Character *pMember = pParty != nullptr ? pParty->member(memberIndex) : nullptr;
    const auto found = pMember != nullptr
        ? std::find_if(pMember->inventory.begin(), pMember->inventory.end(),
              [itemId](const InventoryItem &item)
              {
                  return item.objectDescriptionId == itemId;
              })
        : std::vector<InventoryItem>::const_iterator{};

    if (pMember == nullptr || found == pMember->inventory.end())
    {
        failure = "use_item: member " + std::to_string(memberIndex) + " carries no item " + std::to_string(itemId);
        return false;
    }

    if (!takeInventoryItemToCursor(memberIndex, found->gridX, found->gridY, failure))
    {
        return false;
    }

    const InventoryItem before = runtime.heldInventoryItem().item;
    runtime.itemService().tryUseHeldItemOnPartyMember(runtime, memberIndex, false);
    used = !runtime.heldInventoryItem().active || !(runtime.heldInventoryItem().item == before);

    // A bottle with drinks left, or a refused item, goes back to the pack.
    if (runtime.heldInventoryItem().active && !placeHeldItemInInventory(failure))
    {
        return false;
    }

    // An item that travels (a MAW dimension map) takes the party along.
    const EventRuntimeState *pEventRuntimeState = eventRuntimeState();

    if (pEventRuntimeState != nullptr && pEventRuntimeState->pendingMapMove.has_value())
    {
        return processPendingMapMove(failure);
    }

    return true;
}

bool ScenarioRuntimeDriver::rightClickPortraitWithItem(
    size_t carrierIndex,
    size_t targetIndex,
    uint32_t itemId,
    bool inventoryOpen,
    bool releaseOverPortrait,
    bool &used,
    std::string &failure)
{
    GameSession &session = ScenarioGameApplicationAccess::gameSession(m_application);
    GameplayScreenRuntime &runtime = session.gameplayScreenRuntime();
    Party *pParty = runtime.party();
    const Character *pCarrier = pParty != nullptr ? pParty->member(carrierIndex) : nullptr;
    const auto found = pCarrier != nullptr
        ? std::find_if(pCarrier->inventory.begin(), pCarrier->inventory.end(),
              [itemId](const InventoryItem &item)
              {
                  return item.objectDescriptionId == itemId;
              })
        : std::vector<InventoryItem>::const_iterator{};

    if (pCarrier == nullptr || found == pCarrier->inventory.end())
    {
        failure = "right_click_portrait: member " + std::to_string(carrierIndex) + " carries no item "
            + std::to_string(itemId);
        return false;
    }

    if (!takeInventoryItemToCursor(carrierIndex, found->gridX, found->gridY, failure))
    {
        return false;
    }

    GameplayInputFrame input = {};
    input.screenWidth = ScenarioViewWidth;
    input.screenHeight = ScenarioViewHeight;
    input.pointerX = ScenarioViewWidth * 0.5f;
    input.pointerY = ScenarioViewHeight * 0.5f;

    // The inventory page lays the portraits out on its own frame: open it and let one frame settle first.
    if (inventoryOpen)
    {
        GameplayUiController::CharacterScreenState &characterScreen = runtime.characterScreen();
        characterScreen = {};
        characterScreen.open = true;
        characterScreen.page = GameplayUiController::CharacterPage::Inventory;
        characterScreen.source = GameplayUiController::CharacterScreenSource::Party;
        characterScreen.sourceIndex = carrierIndex;
        session.updateGameplay(input, RuntimeStepSeconds, false);
    }

    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> portrait =
        runtime.resolvePartyPortraitRect(ScenarioViewWidth, ScenarioViewHeight, targetIndex);

    if (!portrait)
    {
        session.bindCurrentGameplayInputFrame(nullptr);
        runtime.characterScreen().open = false;
        placeHeldItemInInventory(failure);
        failure = "right_click_portrait: no portrait for member " + std::to_string(targetIndex);
        return false;
    }

    const InventoryItem before = runtime.heldInventoryItem().item;
    const float portraitX = portrait->x + portrait->width * 0.5f;
    const float portraitY = portrait->y + portrait->height * 0.5f;
    const auto runFrames =
        [&session, &input](int frames)
        {
            for (int frame = 0; frame < frames; ++frame)
            {
                session.updateGameplay(input, RuntimeStepSeconds, false);
                input.leftMouseButton.pressed = false;
                input.leftMouseButton.released = false;
                input.rightMouseButton.pressed = false;
                input.rightMouseButton.released = false;
            }
        };
    const auto itemUsed =
        [&runtime, &before]()
        {
            return !runtime.heldInventoryItem().active || !(runtime.heldInventoryItem().item == before);
        };
    bool readableAfterRelease = false;

    if (releaseOverPortrait)
    {
        // Modern controls: the press lands on the crosshair (the screen centre), the held button frees the cursor,
        // and the release over the portrait uses the item.
        input.rightMouseButton.held = true;
        input.rightMouseButton.pressed = true;
        runFrames(2);
        input.pointerX = portraitX;
        input.pointerY = portraitY;
        runFrames(2);

        if (runtime.readableScrollOverlayReadOnly().active || itemUsed())
        {
            failure = "right_click_portrait: the item was used before the button was released";
        }

        input.rightMouseButton.held = false;
        input.rightMouseButton.released = true;
        runFrames(3);
        const bool readable = runtime.readableScrollOverlayReadOnly().active;
        used = readable || itemUsed();

        // A scroll stays open until a click, which closes it without dropping the item.
        if (readable && failure.empty())
        {
            input.leftMouseButton.held = true;
            input.leftMouseButton.pressed = true;
            runFrames(2);

            if (!runtime.readableScrollOverlayReadOnly().active)
            {
                failure = "right_click_portrait: the scroll closed on the press of the closing click";
            }

            input.leftMouseButton.held = false;
            input.leftMouseButton.released = true;
            runFrames(2);
            readableAfterRelease = runtime.readableScrollOverlayReadOnly().active;

            if (!runtime.heldInventoryItem().active && failure.empty())
            {
                failure = "right_click_portrait: the click that closed the scroll dropped the item";
            }
        }
    }
    else
    {
        input.pointerX = portraitX;
        input.pointerY = portraitY;
        input.rightMouseButton.held = true;
        input.rightMouseButton.pressed = true;
        // A few frames with the button down, so an overlay that only lasts the press frame would show as closed.
        runFrames(4);
        used = runtime.readableScrollOverlayReadOnly().active || itemUsed();
        input.rightMouseButton.held = false;
        input.rightMouseButton.released = true;
        runFrames(2);
        readableAfterRelease = runtime.readableScrollOverlayReadOnly().active;
    }

    session.bindCurrentGameplayInputFrame(nullptr);
    runtime.characterScreen().open = false;

    if (readableAfterRelease && failure.empty())
    {
        failure = "right_click_portrait: the scroll text stayed open";
    }

    if (readableAfterRelease)
    {
        runtime.itemService().closeReadableScrollOverlay();
    }

    if (runtime.heldInventoryItem().active)
    {
        std::string placeFailure;

        if (!placeHeldItemInInventory(placeFailure) && failure.empty())
        {
            failure = placeFailure;
        }
    }

    return failure.empty();
}

bool ScenarioRuntimeDriver::partyCharge(
    std::optional<size_t> actorIndex,
    std::optional<std::string> &status,
    std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    Party *pParty = party();

    if (pWorldRuntime == nullptr || pParty == nullptr)
    {
        failure = "party_charge needs an active map and party";
        return false;
    }

    status = GameplayActionController::tryPartyCharge(*pParty, *pWorldRuntime, actorIndex);
    return true;
}

bool ScenarioRuntimeDriver::castSpell(const ScenarioSpellCastRequest &request, bool &cast, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    Party *pParty = party();
    Character *pMember = pParty != nullptr ? pParty->member(request.memberIndex) : nullptr;
    const SpellTable &spellTable = ScenarioGameApplicationAccess::gameDataLoader(m_application).getSpellTable();

    if (pWorldRuntime == nullptr || pMember == nullptr || spellTable.findById(int(request.spellId)) == nullptr)
    {
        failure = "cast_spell needs an active map, member " + std::to_string(request.memberIndex) + " and spell "
            + std::to_string(request.spellId);
        return false;
    }

    const std::optional<std::string> school = resolveMagicSkillName(request.spellId);

    if (request.skill > 0 && school && !request.scroll)
    {
        pMember->skills[*school] = {*school, request.skill, request.mastery};
    }

    pMember->knownSpellIds.insert(request.spellId);
    pMember->spellPoints = Party::effectiveMaximumSpellPoints(*pMember);
    pMember->recoverySecondsRemaining = 0;
    pParty->setActiveMemberIndex(request.memberIndex);

    PartySpellCastRequest castRequest;
    castRequest.casterMemberIndex = request.memberIndex;
    castRequest.spellId = request.spellId;
    castRequest.targetActorIndex = request.actorIndex;
    castRequest.targetCharacterIndex = request.targetMemberIndex;

    if (request.scroll)
    {
        castRequest.skillLevelOverride = std::max(request.skill, 1u);
        castRequest.skillMasteryOverride = request.mastery;
        castRequest.bypassRequiredMastery = true;
        castRequest.fromScroll = true;
        castRequest.spendMana = false;
    }

    const PartySpellCastResult result = PartySpellSystem::castSpell(*pParty, *pWorldRuntime, spellTable, castRequest);
    pWorldRuntime->applyPendingSpellCastWorldEffects(result);
    cast = result.status == PartySpellCastStatus::Succeeded;
    pMember->recoverySecondsRemaining = 0;
    return true;
}

bool ScenarioRuntimeDriver::craftItem(
    size_t memberIndex,
    uint32_t targetItemId,
    std::optional<EquipmentSlot> wornSlot,
    uint32_t materialItemId,
    bool all,
    size_t choice,
    bool &crafted,
    std::string &reason,
    std::string &failure)
{
    GameplayScreenRuntime &runtime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    Party *pParty = runtime.party();
    const Character *pMember = pParty != nullptr ? pParty->member(memberIndex) : nullptr;

    if (pMember == nullptr)
    {
        failure = "craft needs a party member " + std::to_string(memberIndex);
        return false;
    }

    std::optional<CraftItemRef> target;

    if (wornSlot)
    {
        if (pParty->equippedItemId(memberIndex, *wornSlot) == targetItemId)
        {
            target = CraftItemRef{memberIndex, true, 0, 0, *wornSlot};
        }
    }
    else
    {
        for (const InventoryItem &item : pMember->inventory)
        {
            if (item.objectDescriptionId == targetItemId)
            {
                target = CraftItemRef{memberIndex, false, item.gridX, item.gridY, EquipmentSlot::MainHand,
                    pMember->rulesetState.currentBag};
                break;
            }
        }
    }

    const std::vector<CraftMaterialEntry> materials =
        CraftingRuntime::collectMaterials(*pParty, GameplayCraftingBenchView::rules(runtime));
    const auto material = std::find_if(materials.begin(), materials.end(),
        [materialItemId](const CraftMaterialEntry &entry)
        {
            return entry.key.itemId == materialItemId;
        });

    if (!target || material == materials.end())
    {
        failure = "craft: no item " + std::to_string(targetItemId) + " or material " + std::to_string(materialItemId);
        return false;
    }

    GameplayUiController::CraftingBenchState &bench = runtime.characterScreen().alchemyBench.crafting;
    bench.target = target;
    bench.material = material->key;
    bench.choice = choice;
    const std::optional<CraftingTables> tables = GameplayCraftingBenchView::tables(runtime);
    const CraftPlan preview = tables ? CraftingRuntime::plan(*pParty, *target, material->key, 1, false, choice,
                                           GameplayCraftingBenchView::rules(runtime), *tables)
                                     : CraftPlan{};
    reason = preview.result.reason;
    crafted = runtime.itemService().applyCraft(runtime, all);
    return true;
}

bool ScenarioRuntimeDriver::combineGems(uint32_t gemItemId, bool all, bool &combined, std::string &failure)
{
    GameplayScreenRuntime &runtime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();

    if (runtime.party() == nullptr)
    {
        failure = "combine_gems needs a party";
        return false;
    }

    runtime.characterScreen().alchemyBench.crafting.material = CraftMaterialKey{gemItemId, 0, 0};
    combined = runtime.itemService().combineGems(runtime, all);
    return true;
}

bool ScenarioRuntimeDriver::triggerIndoorPressurePlate(size_t faceIndex, std::string &failure)
{
    IndoorWorldRuntime *pIndoorWorldRuntime = dynamic_cast<IndoorWorldRuntime *>(worldRuntime());

    if (pIndoorWorldRuntime == nullptr)
    {
        failure = "cannot trigger indoor pressure plate without an active indoor world runtime";
        return false;
    }

    if (!pIndoorWorldRuntime->executeFaceTriggeredEvent(faceIndex, FaceAttribute::PressurePlate, false))
    {
        failure = "failed to trigger indoor pressure plate face " + std::to_string(faceIndex);
        return false;
    }

    return true;
}

bool ScenarioRuntimeDriver::triggerIndoorEventTarget(size_t faceIndex, std::string &failure)
{
    IndoorWorldRuntime *pIndoorWorldRuntime = dynamic_cast<IndoorWorldRuntime *>(worldRuntime());

    if (pIndoorWorldRuntime == nullptr)
    {
        failure = "cannot trigger indoor event target without an active indoor world runtime";
        return false;
    }

    if (!pIndoorWorldRuntime->executeFaceTriggeredEvent(faceIndex, FaceAttribute::Clickable, false))
    {
        failure = "failed to trigger indoor event target face " + std::to_string(faceIndex);
        return false;
    }

    ScenarioGameApplicationAccess::gameSession(m_application)
        .gameplayScreenRuntime()
        .ensurePendingEventDialogPresented(true);
    return true;
}

bool ScenarioRuntimeDriver::activeCorpseContainsItem(
    std::optional<uint32_t> sourceIndex,
    uint32_t itemId,
    bool &containsItem,
    std::string &failure) const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    containsItem = false;

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot inspect active corpse without an active world runtime";
        return false;
    }

    const GameplayCorpseViewState *pCorpseView = pWorldRuntime->activeCorpseView();

    if (pCorpseView == nullptr)
    {
        return true;
    }

    if (sourceIndex && pCorpseView->sourceIndex != *sourceIndex)
    {
        return true;
    }

    for (const GameplayChestItemState &item : pCorpseView->items)
    {
        if (!item.isGold && item.item.objectDescriptionId == itemId)
        {
            containsItem = true;
            return true;
        }
    }

    return true;
}

GameplayWorldPickRequest ScenarioRuntimeDriver::buildCenterPickRequest()
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return {};
    }

    return pWorldRuntime->buildWorldPickRequest(GameplayWorldPickRequestInput{
        .screenX = ScenarioViewWidth * 0.5f,
        .screenY = ScenarioViewHeight * 0.5f,
        .screenWidth = ScenarioViewWidth,
        .screenHeight = ScenarioViewHeight,
        .includeRay = true,
    });
}

ScenarioInteractionResult ScenarioRuntimeDriver::pickCenterInteractionTarget(bool ignoreActors, std::string &failure)
{
    ScenarioInteractionResult result = {};
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot pick scenario interaction without an active world runtime";
        return result;
    }

    result.mapFileName = currentMapFileName();

    GameplayWorldPickRequest pickRequest = buildCenterPickRequest();
    pickRequest.ignoreActors = ignoreActors;
    result.hit = GameplayInteractionController::pickKeyboardUseTarget(*pWorldRuntime, pickRequest);
    result.picked = result.hit.hasHit;
    return result;
}

bool ScenarioRuntimeDriver::activateInteractionResult(ScenarioInteractionResult &result, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot activate scenario interaction without an active world runtime";
        return false;
    }

    GameplayScreenState::WorldInteractionInputState &interactionState =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenState().worldInteractionInputState();
    GameplayInteractionController::updateKeyboardInteraction(
        interactionState,
        GameplayInteractionController::KeyboardInteractionInput{
            .interactionPressed = false,
            .allowInteraction = true,
            .pickedHit = {},
            .hasPickedHit = false,
            .pRuntime = &ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime(),
            .pWorldRuntime = pWorldRuntime,
            .interactionMethod = GameplayInteractionMethod::Keyboard,
        });

    const GameplayInteractionController::KeyboardInteractionResult activation =
        GameplayInteractionController::updateKeyboardInteraction(
            interactionState,
            GameplayInteractionController::KeyboardInteractionInput{
                .interactionPressed = true,
                .allowInteraction = true,
                .pickedHit = result.hit,
                .hasPickedHit = result.hit.hasHit,
                .pRuntime = &ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime(),
                .pWorldRuntime = pWorldRuntime,
                .interactionMethod = GameplayInteractionMethod::Keyboard,
            });

    result.activated = activation.activated;

    if (!result.activated)
    {
        failure = result.picked
            ? "scenario keyboard interaction picked a target but activation failed: "
                + gameplayDebugTraceWorldHitSummary(result.hit)
            : "scenario keyboard interaction did not pick a target";
        return false;
    }

    if (EventRuntimeState *pEventRuntimeState = eventRuntimeState())
    {
        if (pEventRuntimeState->pendingMapMove.has_value())
        {
            std::string mapMoveFailure;
            if (!processPendingMapMove(mapMoveFailure))
            {
                result.activated = false;
                failure = mapMoveFailure;
            }
        }
    }

    if (result.activated)
    {
        GameSession &session = ScenarioGameApplicationAccess::gameSession(m_application);

        // As the game views do after a click: the items the event gave (evt.GiveItem) come to the hand.
        if (EventRuntimeState *pEventRuntimeState = eventRuntimeState())
        {
            GameplayHeldItemController::applyGrantedEventItemsToHeldInventory(
                session.gameplayScreenRuntime(), *pEventRuntimeState, session.data().itemTable());
        }

        session.gameplayScreenRuntime().ensurePendingEventDialogPresented(true);
    }

    return result.activated;
}

ScenarioInteractionResult ScenarioRuntimeDriver::pressKeyboardInteract(std::string &failure)
{
    ScenarioInteractionResult result = pickCenterInteractionTarget(false, failure);

    if (!failure.empty())
    {
        return result;
    }

    activateInteractionResult(result, failure);
    return result;
}

ScenarioInteractionResult ScenarioRuntimeDriver::pressKeyboardInteractWithEventTargetActorOcclusion(
    uint32_t expectedTargetKind,
    size_t expectedTargetIndex,
    size_t expectedSecondaryIndex,
    uint16_t expectedTriggeredEventId,
    std::optional<uint16_t> expectedTrigger,
    bool &usedActorlessPick,
    std::string &failure)
{
    usedActorlessPick = false;
    ScenarioInteractionResult result = pickCenterInteractionTarget(false, failure);

    if (!failure.empty())
    {
        return result;
    }

    if (result.hit.kind != GameplayWorldHitKind::Actor)
    {
        activateInteractionResult(result, failure);
        return result;
    }

    ScenarioInteractionResult actorlessResult = pickCenterInteractionTarget(true, failure);

    if (!failure.empty())
    {
        return result;
    }

    const bool actorlessMatchesExact =
        actorlessResult.hit.kind == GameplayWorldHitKind::EventTarget
        && actorlessResult.hit.eventTarget
        && static_cast<uint32_t>(actorlessResult.hit.eventTarget->targetKind) == expectedTargetKind
        && actorlessResult.hit.eventTarget->targetIndex == expectedTargetIndex
        && actorlessResult.hit.eventTarget->secondaryIndex == expectedSecondaryIndex
        && actorlessResult.hit.eventTarget->triggeredEventId == expectedTriggeredEventId
        && (!expectedTrigger || actorlessResult.hit.eventTarget->trigger == *expectedTrigger);
    const bool actorlessMatchesEquivalentEvent =
        actorlessResult.hit.kind == GameplayWorldHitKind::EventTarget
        && actorlessResult.hit.eventTarget
        && static_cast<uint32_t>(actorlessResult.hit.eventTarget->targetKind) == expectedTargetKind
        && actorlessResult.hit.eventTarget->triggeredEventId == expectedTriggeredEventId
        && (!expectedTrigger || actorlessResult.hit.eventTarget->trigger == *expectedTrigger);

    if (!actorlessMatchesExact && !actorlessMatchesEquivalentEvent)
    {
        failure = "scenario event target was blocked by an actor, but actorless pick did not hit the recorded target; "
            "actor hit: " + gameplayDebugTraceWorldHitSummary(result.hit)
            + "; actorless hit: " + gameplayDebugTraceWorldHitSummary(actorlessResult.hit);
        return result;
    }

    usedActorlessPick = true;
    activateInteractionResult(actorlessResult, failure);
    return actorlessResult;
}

bool ScenarioRuntimeDriver::executeMapEvent(uint16_t eventId, std::string &failure)
{
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot execute scenario map event without an active world runtime";
        return false;
    }

    size_t previousMessageCount = 0;

    if (!pWorldRuntime->executeMapEvent(eventId, previousMessageCount))
    {
        failure = "scenario map event " + std::to_string(eventId) + " did not execute";
        return false;
    }

    if (EventRuntimeState *pEventRuntimeState = eventRuntimeState())
    {
        if (pEventRuntimeState->pendingMapMove.has_value())
        {
            return processPendingMapMove(failure);
        }
    }

    ScenarioGameApplicationAccess::gameSession(m_application)
        .gameplayScreenRuntime()
        .ensurePendingEventDialogPresented(true);
    return true;
}

bool ScenarioRuntimeDriver::selectDialogAction(size_t actionIndex, std::string &failure)
{
    GameplayScreenRuntime &screenRuntime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();

    if (!screenRuntime.activeEventDialog().isActive)
    {
        failure = "cannot select scenario dialog action because no dialog is active";
        return false;
    }

    if (actionIndex >= screenRuntime.activeEventDialog().actions.size())
    {
        failure = "scenario dialog action index is out of range";
        return false;
    }

    screenRuntime.eventDialogSelectionIndex() = actionIndex;

    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);

    if (pSceneRuntime != nullptr && pSceneRuntime->kind() == SceneKind::Outdoor)
    {
        OutdoorWorldRuntime *pOutdoorWorldRuntime = ScenarioGameApplicationAccess::outdoorWorldRuntime(m_application);

        if (pOutdoorWorldRuntime != nullptr)
        {
            pOutdoorWorldRuntime->executeActiveDialogAction();
        }
    }
    else if (pSceneRuntime != nullptr && pSceneRuntime->kind() == SceneKind::Indoor)
    {
        ScenarioGameApplicationAccess::indoorGameView(m_application).executeActiveDialogAction();
    }

    const EventRuntimeState *pEventRuntimeState = eventRuntimeState();

    // Closing a transition dialog transfers its move from event state into the session queue.
    if ((pEventRuntimeState != nullptr && pEventRuntimeState->pendingMapMove.has_value())
        || ScenarioGameApplicationAccess::gameSession(m_application).pendingMapMove().has_value())
    {
        if (!processPendingMapMove(failure))
        {
            return false;
        }
    }

    return true;
}

bool ScenarioRuntimeDriver::selectDialogActionById(uint32_t actionId, std::string &failure)
{
    GameplayScreenRuntime &screenRuntime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();

    if (!screenRuntime.activeEventDialog().isActive)
    {
        failure = "cannot select scenario dialog action because no dialog is active";
        return false;
    }

    const std::vector<EventDialogAction> &actions = screenRuntime.activeEventDialog().actions;

    for (size_t actionIndex = 0; actionIndex < actions.size(); ++actionIndex)
    {
        if (actions[actionIndex].id == actionId)
        {
            return selectDialogAction(actionIndex, failure);
        }
    }

    failure = "scenario dialog action id " + std::to_string(actionId) + " is not available";
    return false;
}

bool ScenarioRuntimeDriver::answerPendingInputPrompt(
    const std::string &text,
    ScenarioInputPromptAnswerResult &result,
    std::string &failure)
{
    EventRuntimeState *pRuntimeState = eventRuntimeState();

    if (pRuntimeState == nullptr || !pRuntimeState->pendingInputPrompt)
    {
        failure = "cannot answer scenario input prompt because no input prompt is pending";
        return false;
    }

    const EventRuntimeState::PendingInputPrompt prompt = *pRuntimeState->pendingInputPrompt;
    result.prompt = activeInputPromptSnapshot();
    result.selectedContinueStep = prompt.continueStep;

    const std::string normalizedInput = normalizeScenarioPromptAnswer(text);
    for (size_t answerIndex = 0; answerIndex < prompt.answers.size(); ++answerIndex)
    {
        const std::string normalizedAnswer = normalizeScenarioPromptAnswer(prompt.answers[answerIndex]);
        if (!prompt.answers[answerIndex].empty() && normalizedAnswer == normalizedInput)
        {
            result.matched = true;
            result.matchedIndex = answerIndex;

            if (answerIndex < prompt.answerContinueSteps.size()
                && prompt.answerContinueSteps[answerIndex] != 0)
            {
                result.selectedContinueStep = prompt.answerContinueSteps[answerIndex];
            }
            else if (prompt.correctStep != 0)
            {
                result.selectedContinueStep = prompt.correctStep;
            }
            break;
        }
    }

    ScenarioGameApplicationAccess::submitPendingInputPrompt(m_application, text);

    if (EventRuntimeState *pUpdatedRuntimeState = eventRuntimeState())
    {
        if (pUpdatedRuntimeState->pendingMapMove.has_value())
        {
            std::string mapMoveFailure;
            if (!processPendingMapMove(mapMoveFailure))
            {
                failure = mapMoveFailure;
                return false;
            }
        }
    }

    ScenarioGameApplicationAccess::gameSession(m_application)
        .gameplayScreenRuntime()
        .ensurePendingEventDialogPresented(true);
    return true;
}

ScenarioInputPromptSnapshot ScenarioRuntimeDriver::activeInputPromptSnapshot() const
{
    ScenarioInputPromptSnapshot snapshot = {};
    const EventRuntimeState *pRuntimeState = eventRuntimeState();

    if (pRuntimeState == nullptr || !pRuntimeState->pendingInputPrompt)
    {
        return snapshot;
    }

    const EventRuntimeState::PendingInputPrompt &prompt = *pRuntimeState->pendingInputPrompt;
    snapshot.active = true;
    snapshot.eventId = prompt.eventId;
    snapshot.continueStep = prompt.continueStep;
    snapshot.correctStep = prompt.correctStep;
    snapshot.textId = prompt.textId;
    snapshot.text = prompt.text.value_or(std::string());
    snapshot.answerCount = prompt.answers.size();
    return snapshot;
}

bool ScenarioRuntimeDriver::closeDialog(std::string &failure)
{
    GameplayScreenRuntime &screenRuntime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr))
    {
        // Chests/corpses are loot overlays, not EventDialogContent. Exercise the shared Escape input path.
        std::array<bool, SDL_SCANCODE_COUNT> keyboardState = {};
        GameplayStandardUiHotkeyConfig config = {};
        config.pKeyboardState = keyboardState.data();
        screenRuntime.updatePreviousKeyboardStateSnapshot(nullptr);
        keyboardState[SDL_SCANCODE_ESCAPE] = true;
        GameplayInputController::handleStandardUiHotkeys(screenRuntime, config);
        screenRuntime.updatePreviousKeyboardStateSnapshot(keyboardState.data());
        keyboardState[SDL_SCANCODE_ESCAPE] = false;
        GameplayInputController::handleStandardUiHotkeys(screenRuntime, config);
        screenRuntime.updatePreviousKeyboardStateSnapshot(keyboardState.data());
        return true;
    }

    if (!screenRuntime.activeEventDialog().isActive)
    {
        failure = "cannot close scenario dialog because no dialog is active; current "
            + activeDialogSummary();
        return false;
    }

    const std::vector<EventDialogAction> &actions = screenRuntime.activeEventDialog().actions;
    for (size_t actionIndex = 0; actionIndex < actions.size(); ++actionIndex)
    {
        if (actions[actionIndex].kind == EventDialogActionKind::MapTransitionCancel)
        {
            return selectDialogAction(actionIndex, failure);
        }
    }

    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);

    if (pSceneRuntime != nullptr && pSceneRuntime->kind() == SceneKind::Outdoor)
    {
        OutdoorWorldRuntime *pOutdoorWorldRuntime = ScenarioGameApplicationAccess::outdoorWorldRuntime(m_application);

        if (pOutdoorWorldRuntime != nullptr)
        {
            pOutdoorWorldRuntime->handleDialogueCloseRequest();
        }
    }
    else
    {
        screenRuntime.handleDialogueCloseRequest();
    }
    // A direct scenario close must finish the UI frame, as the live application does. Otherwise a previous
    // character-selection frame can leave worldInputBlocked set and prevent the next pose from reaching the camera.
    GameplayInputFrame input = {};
    input.screenWidth = ScenarioViewWidth;
    input.screenHeight = ScenarioViewHeight;
    GameSession &session = ScenarioGameApplicationAccess::gameSession(m_application);
    session.updateGameplay(input, 0.0f, false);
    session.bindCurrentGameplayInputFrame(nullptr);
    static_cast<void>(failure);
    return true;
}

std::optional<size_t> ScenarioRuntimeDriver::quickItemRingMember() const
{
    const GameplayOverlayInteractionState &state =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime().interactionState();
    return state.quickItemRingOpen ? std::optional<size_t>(state.quickItemRingMember) : std::nullopt;
}

std::pair<std::string, size_t> ScenarioRuntimeDriver::quickItemPopup() const
{
    const GameplayOverlayInteractionState &state =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime().interactionState();
    const std::string kind = state.quickItemPopup == QuickItemPopupKind::Potions ? "potions"
        : state.quickItemPopup == QuickItemPopupKind::Scrolls                   ? "scrolls"
                                                                                : "none";
    return {kind, state.quickItemPopupMember};
}

ScenarioDialogSnapshot ScenarioRuntimeDriver::activeDialogSnapshot() const
{
    const GameplayScreenRuntime &screenRuntime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    const EventDialogContent &dialog = screenRuntime.activeEventDialog();

    ScenarioDialogSnapshot snapshot = {};
    snapshot.active = dialog.isActive;
    snapshot.houseDialog = dialog.isHouseDialog;
    snapshot.sourceId = dialog.sourceId;
    snapshot.title = dialog.title;
    snapshot.houseTitle = dialog.houseTitle;
    snapshot.lineCount = dialog.lines.size();
    snapshot.textHash = dialogLinesHash(dialog);

    for (const std::string &line : dialog.lines)
    {
        snapshot.text += snapshot.text.empty() ? line : "\n" + line;
    }

    snapshot.actions.reserve(dialog.actions.size());

    for (size_t index = 0; index < dialog.actions.size(); ++index)
    {
        const EventDialogAction &action = dialog.actions[index];
        ScenarioDialogActionSnapshot actionSnapshot = {};
        actionSnapshot.index = index;
        actionSnapshot.kind = scenarioDialogActionKindName(action.kind);
        actionSnapshot.id = action.id;
        actionSnapshot.secondaryId = action.secondaryId;
        actionSnapshot.enabled = action.enabled;
        actionSnapshot.textOnly = action.textOnly;
        actionSnapshot.label = action.label;
        snapshot.actions.push_back(std::move(actionSnapshot));
    }

    return snapshot;
}

std::string ScenarioRuntimeDriver::activeDialogSummary() const
{
    const GameplayScreenRuntime &screenRuntime =
        ScenarioGameApplicationAccess::gameSession(m_application).gameplayScreenRuntime();
    const EventDialogContent &dialog = screenRuntime.activeEventDialog();
    std::ostringstream stream;
    stream << "dialog active=" << (dialog.isActive ? "true" : "false")
           << " house_dialog=" << (dialog.isHouseDialog ? "true" : "false")
           << " source_id=" << dialog.sourceId
           << " action_count=" << dialog.actions.size();

    if (!dialog.title.empty())
    {
        stream << " title=\"" << dialog.title << '"';
    }

    if (!dialog.houseTitle.empty())
    {
        stream << " house_title=\"" << dialog.houseTitle << '"';
    }

    if (!dialog.actions.empty())
    {
        stream << " actions=[";

        for (size_t index = 0; index < dialog.actions.size(); ++index)
        {
            const EventDialogAction &action = dialog.actions[index];

            if (index != 0)
            {
                stream << ", ";
            }

            stream << "{index=" << index
                   << ", kind=" << static_cast<uint32_t>(action.kind)
                   << ", id=" << action.id
                   << ", secondary_id=" << action.secondaryId
                   << ", label=\"" << action.label << "\"}";
        }

        stream << ']';
    }

    return stream.str();
}

bool ScenarioRuntimeDriver::advanceRuntime(float seconds, std::string &failure)
{
    if (seconds < 0.0f)
    {
        failure = "cannot advance scenario runtime by a negative duration";
        return false;
    }

    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        failure = "cannot advance scenario runtime without an active world runtime";
        return false;
    }

    float remaining = seconds;
    GameSession &session = ScenarioGameApplicationAccess::gameSession(m_application);
    GameplayInputFrame input = {};
    input.screenWidth = ScenarioViewWidth;
    input.screenHeight = ScenarioViewHeight;
    input.pointerX = ScenarioViewWidth * 0.5f;
    input.pointerY = ScenarioViewHeight * 0.5f;

    while (remaining > 0.0f)
    {
        const float deltaSeconds = std::min(RuntimeStepSeconds, remaining);
        session.updateGameplay(input, deltaSeconds, false);
        session.bindCurrentGameplayInputFrame(nullptr);
        if (session.sharedInputFrameResult().worldInputBlocked
            || session.sharedWorldInteractionBlockedThisFrame()
            || session.gameplayScreenState().pendingSpellTarget().active)
        {
            remaining -= deltaSeconds;
            continue;
        }
        pWorldRuntime->updateWorld(deltaSeconds);

        IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);
        if (pSceneRuntime != nullptr && pSceneRuntime->kind() == SceneKind::Indoor)
        {
            static_cast<IndoorSceneRuntime *>(pSceneRuntime)->advanceSimulation(deltaSeconds * 1000.0f);
        }

        // An arena poses its monsters' models as the window does, so it plays as the window plays: a model's
        // missile leaves from its release socket (WorldFxSystem::actorLaunchPoint). trace_animation only adds the
        // `anim` lines.
        if (pWorldRuntime->actorAiTrace() != nullptr
            && !ScenarioGameApplicationAccess::syncActorModels(m_application, *pWorldRuntime, deltaSeconds))
        {
            failure = "actor models failed to load";
            return false;
        }

        remaining -= deltaSeconds;
    }

    return true;
}

bool ScenarioRuntimeDriver::advanceGameMinutes(float minutes, std::string &failure)
{
    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);

    if (pSceneRuntime == nullptr)
    {
        failure = "cannot advance scenario game time without an active map";
        return false;
    }

    // As the game's own time skips (GameplayController::advanceGameMinutes): the party's buffs and timers run too.
    pSceneRuntime->advanceGameMinutes(minutes);
    pSceneRuntime->party().advanceTimedStates(minutes * 60.0f);
    ScenarioGameApplicationAccess::gameSession(m_application).setGameMinutes(
        ScenarioGameApplicationAccess::gameSession(m_application).gameMinutes() + minutes);
    return true;
}

bool ScenarioRuntimeDriver::hasActiveRuntime() const
{
    return ScenarioGameApplicationAccess::mapSceneRuntime(m_application) != nullptr;
}

const std::string &ScenarioRuntimeDriver::currentMapFileName() const
{
    const IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);

    if (pSceneRuntime != nullptr)
    {
        return pSceneRuntime->currentMapFileName();
    }

    return ScenarioGameApplicationAccess::gameSession(m_application).currentMapFileName();
}

float ScenarioRuntimeDriver::gameMinutes() const
{
    const IGameplayWorldRuntime *pWorldRuntime = worldRuntime();

    if (pWorldRuntime != nullptr)
    {
        return pWorldRuntime->gameMinutes();
    }

    return ScenarioGameApplicationAccess::gameSession(m_application).gameMinutes();
}

void ScenarioRuntimeDriver::setPartyState(const Party &party)
{
    Party runtimeParty = party;
    ScenarioGameApplicationAccess::bindPartyDependencies(m_application, runtimeParty);
    ScenarioGameApplicationAccess::gameSession(m_application).setPartyState(runtimeParty);

    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);

    if (pSceneRuntime != nullptr)
    {
        pSceneRuntime->party() = runtimeParty;
        ScenarioGameApplicationAccess::bindPartyDependencies(m_application, pSceneRuntime->party());
    }
}

void ScenarioRuntimeDriver::setEventRuntimeState(const EventRuntimeState &eventRuntimeState)
{
    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);
    EventRuntimeState *pRuntimeState = pSceneRuntime != nullptr ? pSceneRuntime->eventRuntimeState() : nullptr;

    if (pRuntimeState != nullptr)
    {
        *pRuntimeState = eventRuntimeState;
    }
}

void ScenarioRuntimeDriver::setGameMinutes(float gameMinutes)
{
    if (IGameplayWorldRuntime *pWorldRuntime = worldRuntime())
    {
        pWorldRuntime->advanceGameMinutes(gameMinutes - pWorldRuntime->gameMinutes());
    }

    ScenarioGameApplicationAccess::gameSession(m_application).setGameMinutes(gameMinutes);
}

Party *ScenarioRuntimeDriver::party()
{
    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);
    return pSceneRuntime != nullptr ? &pSceneRuntime->party() : nullptr;
}

const Party *ScenarioRuntimeDriver::party() const
{
    const IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);
    return pSceneRuntime != nullptr ? &pSceneRuntime->party() : nullptr;
}

EventRuntimeState *ScenarioRuntimeDriver::eventRuntimeState()
{
    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);
    return pSceneRuntime != nullptr ? pSceneRuntime->eventRuntimeState() : nullptr;
}

const EventRuntimeState *ScenarioRuntimeDriver::eventRuntimeState() const
{
    const IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);
    return pSceneRuntime != nullptr ? pSceneRuntime->eventRuntimeState() : nullptr;
}

IGameplayWorldRuntime *ScenarioRuntimeDriver::worldRuntime()
{
    IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);

    if (pSceneRuntime == nullptr)
    {
        return nullptr;
    }

    if (pSceneRuntime->kind() == SceneKind::Outdoor)
    {
        OutdoorSceneRuntime *pOutdoorRuntime = static_cast<OutdoorSceneRuntime *>(pSceneRuntime);
        return &pOutdoorRuntime->worldRuntime();
    }

    if (pSceneRuntime->kind() == SceneKind::Indoor)
    {
        IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(pSceneRuntime);
        return &pIndoorRuntime->worldRuntime();
    }

    return nullptr;
}

const IGameplayWorldRuntime *ScenarioRuntimeDriver::worldRuntime() const
{
    const IMapSceneRuntime *pSceneRuntime = ScenarioGameApplicationAccess::mapSceneRuntime(m_application);

    if (pSceneRuntime == nullptr)
    {
        return nullptr;
    }

    if (pSceneRuntime->kind() == SceneKind::Outdoor)
    {
        const OutdoorSceneRuntime *pOutdoorRuntime = static_cast<const OutdoorSceneRuntime *>(pSceneRuntime);
        return &pOutdoorRuntime->worldRuntime();
    }

    if (pSceneRuntime->kind() == SceneKind::Indoor)
    {
        const IndoorSceneRuntime *pIndoorRuntime = static_cast<const IndoorSceneRuntime *>(pSceneRuntime);
        return &pIndoorRuntime->worldRuntime();
    }

    return nullptr;
}
}
