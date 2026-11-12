#include "game/app/GameSession.h"
#include "game/StringUtils.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/events/EvtEnums.h"
#include "game/events/ISceneEventContext.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayActorHitFeedback.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayInteractionController.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/gameplay/MercenaryRecruitmentRuntime.h"
#include "game/gameplay/PartyHostileAlert.h"
#include "game/items/InventoryBags.h"
#include "game/maps/MapIdentity.h"
#include "game/party/WorldSpells.h"
#include "game/rules/RandomStreams.h"
#include "game/rules/maw/MawRulesFactory.h"
#include "game/ui/GameplayFormationBuilder.h"
#include "game/ui/GameplaySpellTargetingOverlayRenderer.h"
#include "game/ui/GameplayUiSkin.h"

#include <cassert>
#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t BlazenStormlanceRosterUnlockQBit = 435;
constexpr uint32_t RescuedBlazenStormlanceQBit = 1542;

uint64_t averageNanoseconds(uint64_t totalNanoseconds, uint64_t count)
{
    return count != 0 ? totalNanoseconds / count : 0;
}

uint64_t nanosecondsToMicroseconds(uint64_t nanoseconds)
{
    return nanoseconds / 1000ULL;
}

const char *turnBasedStageName(TurnBasedCombatStage stage)
{
    switch (stage)
    {
        case TurnBasedCombatStage::None:
            return "none";
        case TurnBasedCombatStage::Wait:
            return "wait";
        case TurnBasedCombatStage::Attack:
            return "attack";
        case TurnBasedCombatStage::Movement:
            return "movement";
        default:
            return "unknown";
    }
}

void synchronizeTurnBasedPendingWorldActions(
    TurnBasedCombatRuntime &turnBasedCombatRuntime,
    IGameplayWorldRuntime *pWorldRuntime,
    size_t &syncedPendingWorldActions)
{
    if (!turnBasedCombatRuntime.active() || pWorldRuntime == nullptr)
    {
        syncedPendingWorldActions = 0;
        return;
    }

    const size_t pendingWorldActions = pWorldRuntime->turnBasedPendingWorldActionCount();

    while (syncedPendingWorldActions < pendingWorldActions)
    {
        turnBasedCombatRuntime.registerPendingAction();
        ++syncedPendingWorldActions;
    }

    while (syncedPendingWorldActions > pendingWorldActions)
    {
        turnBasedCombatRuntime.resolvePendingAction();
        --syncedPendingWorldActions;
    }
}

void pulseGameplayAction(GameplayInputFrame &input, KeyboardAction action)
{
    GameplayButtonInputState &state = input.actions[keyboardActionIndex(action)];
    state.held = true;
    state.pressed = true;
    state.released = false;
}

Party buildConfiguredParty(
    const Party::Snapshot &snapshot,
    const GameDataRepository &data,
    const GameRules *pRules)
{
    Party party = {};
    party.setRules(pRules);
    party.setItemTable(&data.itemTable());
    party.setJournalQuestTable(&data.journalQuestTable());
    party.setItemEnchantTables(&data.standardItemEnchantTable(), &data.specialItemEnchantTable());
    party.setClassMultiplierTable(&data.classMultiplierTable());
    party.setClassSkillTable(&data.classSkillTable());
    party.setTrainerDirectory(&data.trainerDirectory());
    party.restoreSnapshot(snapshot);
    return party;
}

void migrateSavedRuntimeFollowersToParty(
    Party &party,
    const std::optional<EventRuntimeState> &eventRuntimeState)
{
    if (!eventRuntimeState)
    {
        return;
    }

    for (const HiredNpcFollower &savedFollower : eventRuntimeState->hiredNpcFollowers)
    {
        HiredNpcFollower follower = savedFollower;

        const std::unordered_map<uint32_t, std::string>::const_iterator nameIt =
            eventRuntimeState->npcNameOverrides.find(follower.npcId);
        if (follower.name.empty() && nameIt != eventRuntimeState->npcNameOverrides.end())
        {
            follower.name = nameIt->second;
        }

        const std::unordered_map<uint32_t, uint32_t>::const_iterator pictureIt =
            eventRuntimeState->npcPictureOverrides.find(follower.npcId);
        if (follower.pictureId == 0 && pictureIt != eventRuntimeState->npcPictureOverrides.end())
        {
            follower.pictureId = pictureIt->second;
        }

        party.addHiredNpcFollower(follower);
    }
}

void migrateBlazenRescueRosterUnlock(Party &party)
{
    if (!party.hasQuestBit(RescuedBlazenStormlanceQBit)
        || party.hasQuestBit(BlazenStormlanceRosterUnlockQBit))
    {
        return;
    }

    party.setQuestBit(BlazenStormlanceRosterUnlockQBit, true);
    GAMEPLAY_DEBUG_TRACE(
        "save_migration name=blazen_rescue_roster_unlock"
        " source_qbit=" + std::to_string(RescuedBlazenStormlanceQBit)
        + " restored_qbit=" + std::to_string(BlazenStormlanceRosterUnlockQBit));
}

void synchronizeGameplayActiveMemberToReadyMember(
    GameplayScreenRuntime &screenRuntime,
    const GameplayScreenState &screenState,
    const TurnBasedCombatRuntime &turnBasedCombatRuntime)
{
    if (screenRuntime.currentHudScreenState() != GameplayHudScreenState::Gameplay)
    {
        return;
    }

    if (turnBasedCombatRuntime.active())
    {
        return;
    }

    if (screenState.pendingSpellTarget().active || screenRuntime.heldInventoryItem().active)
    {
        return;
    }

    Party *pParty = screenRuntime.party();

    if (pParty == nullptr)
    {
        return;
    }

    const Character *pActiveMember = pParty->activeMember();

    if (pActiveMember == nullptr || !GameMechanics::canTakeGameplayAction(*pActiveMember))
    {
        pParty->switchToNextReadyMember();
    }
}
}

GameSession::GameSession()
    : m_gameplayItemService(*this)
    , m_gameplayFxService(*this)
    , m_gameplaySpellService(*this)
    , m_gameplayScreenRuntime(*this)
{
    m_gameplayUiController.bindExternalState(&m_gameplayScreenState.uiState());
    m_turnBasedCombatRuntime.seedRandom(std::random_device{}());
    // Under the user data root, beside the saves (devdocs/PLAYTHROUGH_STATISTICS_PLAN.md).
    m_playthroughStatistics.setDirectory(std::filesystem::path("saves") / "playthroughs");
}

GameSession::~GameSession()
{
    // The class multiplier table bound in bindDataRepository belongs to the repository, which may go before the
    // next session binds its own.
    if (m_pDataRepository != nullptr)
    {
        GameMechanics::bindClassMultiplierTable(nullptr);
    }
}

void GameSession::bindDataRepository(const GameDataRepository *pDataRepository)
{
    m_pDataRepository = pDataRepository;
    m_mm9QuestMarkerCache.clear();
    ++m_mm9QuestMarkerMapRevision;
    m_gameplayUiRuntime.bindDataRepository(pDataRepository);
    GameMechanics::bindClassMultiplierTable(
        pDataRepository != nullptr && pDataRepository->isBound() ? &pDataRepository->classMultiplierTable() : nullptr);

    if (m_pDataRepository != nullptr && m_pDataRepository->isBound())
    {
        m_gameplayActorService.bindTables(&m_pDataRepository->monsterTable(), &m_pDataRepository->spellTable());
    }
    else
    {
        m_gameplayActorService.bindTables(nullptr, nullptr);
    }
}

bool GameSession::hasDataRepository() const
{
    return m_pDataRepository != nullptr;
}

const GameDataRepository &GameSession::data() const
{
    assert(m_pDataRepository != nullptr);
    return *m_pDataRepository;
}

void GameSession::clear()
{
    m_partyState.reset();
    m_currentSceneKind = SceneKind::Outdoor;
    m_currentMapFileName.clear();
    m_gameplayScreenState.clear();
    m_gameplayCombatController.clear();
    m_gameplayProjectileService.clear();
    m_gameplayFxService.clear();
    m_turnBasedCombatRuntime.reset();
    m_turnBasedPendingWorldActions = 0;
    m_turnBasedFrameTraceState = {};
    m_gameplayUiRuntime.clear();
    m_gameplayScreenRuntime.clearTransientBindings();
    m_overlayInteractionState = {};
    m_previousKeyboardState.fill(0);
    stopCinematics();
    m_mapCinematics.reset();
    m_pActiveWorldRuntime = nullptr;
    m_mm9QuestMarkerCache.clear();
    ++m_mm9QuestMarkerMapRevision;
    m_pCurrentGameplayInputFrame = nullptr;
    m_sharedInputFrameResult = {};
    m_sharedWorldInteractionBlockedThisFrame = false;
    m_relativeMouseMotionResetRequested = false;
    m_outdoorPartyState.reset();
    m_currentOutdoorWorldState.reset();
    m_outdoorWorldStates.clear();
    m_currentIndoorSceneState.reset();
    m_indoorSceneStates.clear();
    m_currentMapLayoutIdentity = 0;
    m_namedGlobalVars.clear();
    m_gameMinutes = 9.0f * 60.0f;
    m_ruleset = {};
    m_pMawRules.reset();
    bindGameRules(nullptr);
    m_randomRootSeed = 0;
    m_cameraYawRadians = 0.0f;
    m_cameraPitchRadians = 0.0f;
    m_cameraAnglesValid = false;
    m_currentSavePath.reset();
    m_pendingMapMove.reset();
    m_framePerformanceDiagnosticsEnabled = false;
    m_lastGameplayUpdateFramePerformanceDiagnostics = {};
    m_lastGameplayUiFramePerformanceDiagnostics = {};
}

const std::optional<Party> &GameSession::partyState() const
{
    return m_partyState;
}

std::optional<Party> &GameSession::partyState()
{
    return m_partyState;
}

PlaythroughStatistics &GameSession::playthroughStatistics()
{
    return m_playthroughStatistics;
}

const PlaythroughStatistics &GameSession::playthroughStatistics() const
{
    return m_playthroughStatistics;
}

void GameSession::setPartyState(const Party &party)
{
    m_partyState = party;
    m_partyState->setRules(rulesetGameRules());
    m_partyState->setOtherWorldsLoot(m_ruleset.options.otherWorldsLoot);
    m_partyState->setStatistics(&m_playthroughStatistics);
}

void GameSession::setPartyState(Party &&party)
{
    m_partyState = std::move(party);
    m_partyState->setRules(rulesetGameRules());
    m_partyState->setOtherWorldsLoot(m_ruleset.options.otherWorldsLoot);
    m_partyState->setStatistics(&m_playthroughStatistics);
}

SceneKind GameSession::currentSceneKind() const
{
    return m_currentSceneKind;
}

void GameSession::setCurrentSceneKind(SceneKind sceneKind)
{
    m_currentSceneKind = sceneKind;
}

bool GameSession::hasCurrentMapFileName() const
{
    return !m_currentMapFileName.empty();
}

const std::string &GameSession::currentMapFileName() const
{
    return m_currentMapFileName;
}

void GameSession::setCurrentMapFileName(const std::string &mapFileName)
{
    m_currentMapFileName = mapFileName;
    m_mm9QuestMarkerCache.clear();
    ++m_mm9QuestMarkerMapRevision;
}

void GameSession::setCurrentMapFileName(std::string &&mapFileName)
{
    m_currentMapFileName = std::move(mapFileName);
    m_mm9QuestMarkerCache.clear();
    ++m_mm9QuestMarkerMapRevision;
}

float GameSession::gameMinutes() const
{
    return m_gameMinutes;
}

void GameSession::setGameMinutes(float gameMinutes)
{
    m_gameMinutes = std::max(0.0f, gameMinutes);
}

const RulesetSelection &GameSession::ruleset() const
{
    return m_ruleset;
}

void GameSession::setRuleset(const RulesetSelection &ruleset)
{
    m_ruleset = ruleset;
    m_pMawRules.reset();

    if (ruleset.id == MawRulesetId)
    {
        // GameApplication::activateRuleset loads the MAW data before the session gets the ruleset.
        m_pMawRules = createMawRules(data(), ruleset.options);
        assert(m_pMawRules != nullptr);

        if (m_pMawRules)
        {
            if (m_madnessLedgerFile)
            {
                m_pMawRules->setMadnessLedgerFile(*m_madnessLedgerFile);
            }

            m_pMawRules->setRandomRootSeed(m_randomRootSeed);
            m_pMawRules->setCurrentMap(m_currentMapFileName);
        }
    }

    if (m_partyState)
    {
        m_partyState->setRules(rulesetGameRules());
        m_partyState->setOtherWorldsLoot(ruleset.options.otherWorldsLoot);
    }

    bindGameRules(m_pMawRules ? &m_pMawRules->gameRules() : nullptr);
}

void GameSession::setRulesetOptions(const RulesetOptions &options)
{
    m_ruleset.options = options;

    if (m_partyState)
    {
        m_partyState->setOtherWorldsLoot(options.otherWorldsLoot);
    }

    if (m_pMawRules)
    {
        m_pMawRules->setOptions(options);
    }

    if (m_pActiveWorldRuntime != nullptr)
    {
        m_pActiveWorldRuntime->refreshRulesetMonsters();
    }
}

const GameRules *GameSession::rulesetGameRules() const
{
    return m_pMawRules ? &m_pMawRules->gameRules() : nullptr;
}

MawRules *GameSession::mawRules()
{
    return m_pMawRules.get();
}

const MawRules *GameSession::mawRules() const
{
    return m_pMawRules.get();
}

uint64_t GameSession::randomRootSeed() const
{
    return m_randomRootSeed;
}

void GameSession::setMadnessLedgerFile(const std::filesystem::path &file)
{
    m_madnessLedgerFile = file;

    if (m_pMawRules)
    {
        m_pMawRules->setMadnessLedgerFile(file);
    }
}

void GameSession::setRandomRootSeed(uint64_t rootSeed)
{
    m_randomRootSeed = rootSeed;

    if (m_pMawRules)
    {
        m_pMawRules->setRandomRootSeed(rootSeed);
    }
}

GameplayUiController &GameSession::gameplayUiController()
{
    return m_gameplayUiController;
}

const GameplayUiController &GameSession::gameplayUiController() const
{
    return m_gameplayUiController;
}

GameplayScreenState &GameSession::gameplayScreenState()
{
    return m_gameplayScreenState;
}

const GameplayScreenState &GameSession::gameplayScreenState() const
{
    return m_gameplayScreenState;
}

GameplayUiRuntime &GameSession::gameplayUiRuntime()
{
    return m_gameplayUiRuntime;
}

const GameplayUiRuntime &GameSession::gameplayUiRuntime() const
{
    return m_gameplayUiRuntime;
}

GameplayActorService &GameSession::gameplayActorService()
{
    return m_gameplayActorService;
}

const GameplayActorService &GameSession::gameplayActorService() const
{
    return m_gameplayActorService;
}

GameplayCombatController &GameSession::gameplayCombatController()
{
    return m_gameplayCombatController;
}

const GameplayCombatController &GameSession::gameplayCombatController() const
{
    return m_gameplayCombatController;
}

GameplayItemService &GameSession::gameplayItemService()
{
    return m_gameplayItemService;
}

const GameplayItemService &GameSession::gameplayItemService() const
{
    return m_gameplayItemService;
}

GameplayProjectileService &GameSession::gameplayProjectileService()
{
    return m_gameplayProjectileService;
}

const GameplayProjectileService &GameSession::gameplayProjectileService() const
{
    return m_gameplayProjectileService;
}

GameplayFxService &GameSession::gameplayFxService()
{
    return m_gameplayFxService;
}

const GameplayFxService &GameSession::gameplayFxService() const
{
    return m_gameplayFxService;
}

GameplaySpellService &GameSession::gameplaySpellService()
{
    return m_gameplaySpellService;
}

const GameplaySpellService &GameSession::gameplaySpellService() const
{
    return m_gameplaySpellService;
}

TurnBasedCombatRuntime &GameSession::turnBasedCombatRuntime()
{
    return m_turnBasedCombatRuntime;
}

const TurnBasedCombatRuntime &GameSession::turnBasedCombatRuntime() const
{
    return m_turnBasedCombatRuntime;
}

GameplayScreenRuntime &GameSession::gameplayScreenRuntime()
{
    return m_gameplayScreenRuntime;
}

const GameplayScreenRuntime &GameSession::gameplayScreenRuntime() const
{
    return m_gameplayScreenRuntime;
}

GameplayDialogController &GameSession::gameplayDialogController()
{
    return m_gameplayDialogController;
}

const GameplayDialogController &GameSession::gameplayDialogController() const
{
    return m_gameplayDialogController;
}

GameplayOverlayInteractionState &GameSession::overlayInteractionState()
{
    return m_overlayInteractionState;
}

const GameplayOverlayInteractionState &GameSession::overlayInteractionState() const
{
    return m_overlayInteractionState;
}

std::array<uint8_t, SDL_SCANCODE_COUNT> &GameSession::previousKeyboardState()
{
    return m_previousKeyboardState;
}

const std::array<uint8_t, SDL_SCANCODE_COUNT> &GameSession::previousKeyboardState() const
{
    return m_previousKeyboardState;
}

IGameplayWorldRuntime *GameSession::activeWorldRuntime() const
{
    return m_pActiveWorldRuntime;
}

void GameSession::bindActiveWorldRuntime(IGameplayWorldRuntime *pWorldRuntime)
{
    if (m_pActiveWorldRuntime != pWorldRuntime)
    {
        m_turnBasedCombatRuntime.end(
            m_pActiveWorldRuntime != nullptr ? m_pActiveWorldRuntime->party() : nullptr,
            m_pActiveWorldRuntime);
        m_turnBasedFrameTraceState = {};
    }

    m_pActiveWorldRuntime = pWorldRuntime;

    if (pWorldRuntime != nullptr && data().isBound())
    {
        const MapStatsEntry *pMap = data().mapStats().findByFileName(m_currentMapFileName);
        EventRuntimeState *pState = pWorldRuntime->eventRuntimeState();
        Party *pParty = pWorldRuntime->party();
        if (pMap != nullptr && pState != nullptr && pParty != nullptr)
        {
            const MergedBolsterMapEntry *pBolsterMap = data().mergedBolsterMapTable().findById(pMap->id);
            if (pBolsterMap != nullptr && pBolsterMap->professionMaxRarity.value_or(0) > 0)
            {
                refreshGenericActorNpcRoster(*pState, pWorldRuntime->gameMinutes());
            }
            // House prices that an objective switches read the active party's QBits.
            data().houseTable().setQuestBitQuery([this](uint32_t qbit)
            {
                const Party *pActiveParty =
                    m_pActiveWorldRuntime != nullptr ? m_pActiveWorldRuntime->party() : nullptr;
                return pActiveParty != nullptr && pActiveParty->hasQuestBit(qbit);
            });
            const auto mapHum = m_worldHum.mapPercents.find(toLowerCopy(m_currentMapFileName));
            pParty->setSpellField(m_worldHum.qbits, m_worldHum.percents,
                mapHum != m_worldHum.mapPercents.end() ? std::optional<int>(mapHum->second) : std::nullopt);
            const auto mapBurn = m_worldFloorBurn.mapTypes.find(toLowerCopy(m_currentMapFileName));
            pParty->setFloorBurn(GameMechanics::parseCombatDamageType(
                mapBurn != m_worldFloorBurn.mapTypes.end() ? mapBurn->second : m_worldFloorBurn.type),
                m_worldFloorBurn.resisted);
            pParty->setObjectiveQBits(m_worldObjectiveQBits);
            pParty->setNpcFollowersActive(m_npcFollowers);
            pParty->setFormationTargetingActive(m_formations);
            pParty->setFleetFootWorld(m_fleetFoot);
            if (!m_npcFollowers)
            {
                // The map loaded its followers before the party knew the world has none (Party::applyGlobalNpcStateTo).
                pState->hiredNpcFollowers.clear();
            }

            if (m_tavernHirelings)
            {
                refreshMercenaryRecruitmentForCurrentMap(
                    *pMap, *pParty, *pState, pWorldRuntime->gameMinutes(),
                    MercenaryRecruitmentTables{
                        .pHouseTable = &data().houseTable(),
                        .pNpcNameTable = &data().mergedNpcNameTable(),
                        .pCharacterSelectionTable = &data().mergedCharacterSelectionTable(),
                        .pCharacterDollTable = &data().characterDollTable(),
                        .pClassSkillTable = &data().classSkillTable(),
                        .pClassMultiplierTable = &data().classMultiplierTable(),
                        .pRaceStartingStatsTable = &data().raceStartingStatsTable(),
                        .pItemTable = &data().itemTable(),
                        .pStandardItemEnchantTable = &data().standardItemEnchantTable(),
                        .pSpecialItemEnchantTable = &data().specialItemEnchantTable(),
                        .pSpellTable = &data().spellTable(),
                    });
            }
            else
            {
                // A world without tavern hirelings: none seated, and none kept from an older save.
                for (const auto &[npcId, recruit] : pState->generatedMercenaryRecruitsByNpcId)
                {
                    pState->npcHouseOverrides.erase(npcId);
                    pParty->clearNpcHouseOverride(npcId);
                }

                pState->generatedMercenaryRecruitsByNpcId.clear();
            }
        }
    }
    m_mm9QuestMarkerCache.clear();
    ++m_mm9QuestMarkerMapRevision;
}

Mm9QuestMarkerState GameSession::questMarkerForActor(size_t actorIndex) const
{
    return actorIndex <= static_cast<size_t>(std::numeric_limits<uint32_t>::max())
        ? m_mm9QuestMarkerCache.markerForActor(static_cast<uint32_t>(actorIndex))
        : Mm9QuestMarkerState::None;
}

const GameplayInputFrame *GameSession::currentGameplayInputFrame() const
{
    return m_pCurrentGameplayInputFrame;
}

void GameSession::bindCurrentGameplayInputFrame(const GameplayInputFrame *pInputFrame)
{
    m_pCurrentGameplayInputFrame = pInputFrame;
}

void GameSession::beginFramePerformanceDiagnostics(bool enabled)
{
    if (!enabled)
    {
        if (m_framePerformanceDiagnosticsEnabled)
        {
            m_framePerformanceDiagnosticsEnabled = false;
            m_lastGameplayUpdateFramePerformanceDiagnostics = {};
            m_lastGameplayUiFramePerformanceDiagnostics = {};
            m_gameplayUiRuntime.beginPerformanceFrame(false);
        }

        return;
    }

    m_framePerformanceDiagnosticsEnabled = true;
    m_lastGameplayUpdateFramePerformanceDiagnostics = {};
    m_lastGameplayUpdateFramePerformanceDiagnostics.collected = true;
    m_lastGameplayUiFramePerformanceDiagnostics = {};
    m_lastGameplayUiFramePerformanceDiagnostics.collected = true;
    m_gameplayUiRuntime.beginPerformanceFrame(true);
}

const GameplayUpdateFramePerformanceDiagnostics &
GameSession::lastGameplayUpdateFramePerformanceDiagnostics() const
{
    return m_lastGameplayUpdateFramePerformanceDiagnostics;
}

const GameplayUiFramePerformanceDiagnostics &GameSession::lastGameplayUiFramePerformanceDiagnostics() const
{
    return m_lastGameplayUiFramePerformanceDiagnostics;
}

bool GameSession::logGameplayUpdatePerformanceDiagnostics(uint32_t currentTick) const
{
    constexpr uint32_t LogIntervalMs = 1000;

    if (!m_gameplayUpdatePerformanceDiagnostics.hasActivity()
        || currentTick - m_lastGameplayUpdatePerformanceLogTick < LogIntervalMs)
    {
        return false;
    }

    m_lastGameplayUpdatePerformanceLogTick = currentTick;

    const GameplayUpdatePerformanceDiagnostics diagnostics = m_gameplayUpdatePerformanceDiagnostics;
    const uint64_t measuredNanoseconds =
        diagnostics.sharedFrameStateNanoseconds
        + diagnostics.worldInteractionStateNanoseconds
        + diagnostics.activeMemberSyncNanoseconds
        + diagnostics.sharedInputNanoseconds
        + diagnostics.worldMovementNanoseconds
        + diagnostics.actorAiNanoseconds
        + diagnostics.combatEventsNanoseconds
        + diagnostics.interactionFrameNanoseconds
        + diagnostics.projectileAndCooldownNanoseconds
        + diagnostics.performanceTraceLogNanoseconds;
    const uint64_t untrackedNanoseconds =
        diagnostics.totalNanoseconds > measuredNanoseconds
            ? diagnostics.totalNanoseconds - measuredNanoseconds
            : 0;

    std::cout << "[GameplayUpdatePerf]"
              << " frames=" << diagnostics.frames
              << " active_world_frames=" << diagnostics.activeWorldFrames
              << " actor_ai_frames=" << diagnostics.actorAiFrames
              << " avg_total_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.totalNanoseconds,
                  diagnostics.frames))
              << " avg_untracked_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  untrackedNanoseconds,
                  diagnostics.frames))
              << " avg_shared_frame_state_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.sharedFrameStateNanoseconds,
                  diagnostics.frames))
              << " avg_world_interaction_state_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.worldInteractionStateNanoseconds,
                  diagnostics.frames))
              << " avg_active_member_sync_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.activeMemberSyncNanoseconds,
                  diagnostics.frames))
              << " avg_shared_input_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.sharedInputNanoseconds,
                  diagnostics.frames))
              << " avg_world_movement_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.worldMovementNanoseconds,
                  diagnostics.frames))
              << " avg_actor_ai_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.actorAiNanoseconds,
                  diagnostics.frames))
              << " avg_combat_events_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.combatEventsNanoseconds,
                  diagnostics.frames))
              << " avg_interaction_frame_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.interactionFrameNanoseconds,
                  diagnostics.frames))
              << " avg_projectile_cooldown_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.projectileAndCooldownNanoseconds,
                  diagnostics.frames))
              << " avg_performance_trace_log_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                  diagnostics.performanceTraceLogNanoseconds,
                  diagnostics.frames))
              << '\n';

    m_gameplayUpdatePerformanceDiagnostics = {};
    return true;
}

void GameSession::logTurnBasedFrameTraceIfNeeded(
    bool actorAiUpdate,
    bool gameplayPaused,
    bool allowMoveInput,
    bool movementStep,
    bool cursorMode,
    bool modalBlocked,
    bool pendingSpellTarget,
    bool sharedWorldBlocked,
    float movementDeltaSeconds,
    float frameDeltaSeconds)
{
    constexpr uint32_t LogIntervalMs = 1000;

    if (!m_turnBasedCombatRuntime.active())
    {
        m_turnBasedFrameTraceState = {};
        return;
    }

    const uint32_t currentTick = SDL_GetTicks();
    const TurnBasedCombatStage stage = m_turnBasedCombatRuntime.stage();
    const int movementActionPoints = m_turnBasedCombatRuntime.movementActionPoints();
    const int pendingActions = m_turnBasedCombatRuntime.pendingActions();

    const bool stateChanged =
        !m_turnBasedFrameTraceState.active
        || m_turnBasedFrameTraceState.stage != stage
        || m_turnBasedFrameTraceState.actorAiUpdate != actorAiUpdate
        || m_turnBasedFrameTraceState.gameplayPaused != gameplayPaused
        || m_turnBasedFrameTraceState.allowMoveInput != allowMoveInput
        || m_turnBasedFrameTraceState.cursorMode != cursorMode
        || m_turnBasedFrameTraceState.modalBlocked != modalBlocked
        || m_turnBasedFrameTraceState.pendingSpellTarget != pendingSpellTarget
        || m_turnBasedFrameTraceState.sharedWorldBlocked != sharedWorldBlocked
        || m_turnBasedFrameTraceState.movementActionPoints != movementActionPoints
        || m_turnBasedFrameTraceState.pendingActions != pendingActions;
    const bool periodic =
        !m_turnBasedFrameTraceState.active
        || currentTick - m_turnBasedFrameTraceState.lastLogTick >= LogIntervalMs;

    if (stateChanged || movementStep || periodic)
    {
        const char *reason = movementStep ? "movement_step" : (stateChanged ? "state" : "periodic");
        GAMEPLAY_DEBUG_TRACE(
            "turn_based_frame reason=" + std::string(reason)
            + " stage=" + std::string(turnBasedStageName(stage))
            + " actor_ai_update=" + (actorAiUpdate ? "true" : "false")
            + " gameplay_paused=" + (gameplayPaused ? "true" : "false")
            + " allow_move_input=" + (allowMoveInput ? "true" : "false")
            + " cursor_mode=" + (cursorMode ? "true" : "false")
            + " modal_blocked=" + (modalBlocked ? "true" : "false")
            + " pending_spell_target=" + (pendingSpellTarget ? "true" : "false")
            + " shared_world_blocked=" + (sharedWorldBlocked ? "true" : "false")
            + " movement_dt=" + std::to_string(movementDeltaSeconds)
            + " frame_dt=" + std::to_string(frameDeltaSeconds)
            + " movement_ap=" + std::to_string(movementActionPoints)
            + " pending=" + std::to_string(pendingActions));
        m_turnBasedFrameTraceState.lastLogTick = currentTick;
    }

    m_turnBasedFrameTraceState.active = true;
    m_turnBasedFrameTraceState.stage = stage;
    m_turnBasedFrameTraceState.actorAiUpdate = actorAiUpdate;
    m_turnBasedFrameTraceState.gameplayPaused = gameplayPaused;
    m_turnBasedFrameTraceState.allowMoveInput = allowMoveInput;
    m_turnBasedFrameTraceState.cursorMode = cursorMode;
    m_turnBasedFrameTraceState.modalBlocked = modalBlocked;
    m_turnBasedFrameTraceState.pendingSpellTarget = pendingSpellTarget;
    m_turnBasedFrameTraceState.sharedWorldBlocked = sharedWorldBlocked;
    m_turnBasedFrameTraceState.movementActionPoints = movementActionPoints;
    m_turnBasedFrameTraceState.pendingActions = pendingActions;
}

void GameSession::setGameSpeed(float speed)
{
    m_gameSpeed = speed > 0.0f ? speed : 1.0f;
}

void GameSession::updateGameplay(
    const GameplayInputFrame &rawInput,
    float deltaSeconds,
    bool collectPerformanceDiagnostics)
{
    const uint64_t totalBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
    // While a cinematic plays the party takes no input: the frame runs on an input with nothing held.
    const bool cinematicPlaying = updateCinematics(rawInput, deltaSeconds);
    const GameplayInputFrame &input = cinematicPlaying ? m_cinematicInputFrame : rawInput;

    if (collectPerformanceDiagnostics)
    {
        ++m_gameplayUpdatePerformanceDiagnostics.frames;
    }

    const auto recordDiagnostics =
        [&](uint64_t &aggregateField, uint64_t &frameField, uint64_t beginTickCount)
    {
        if (collectPerformanceDiagnostics)
        {
            const uint64_t elapsedNanoseconds = SDL_GetTicksNS() - beginTickCount;
            aggregateField += elapsedNanoseconds;
            frameField += elapsedNanoseconds;
        }
    };

    bindCurrentGameplayInputFrame(&input);
    m_sharedInputFrameResult = {};

    const uint64_t sharedFrameStateBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
    GameplayScreenFrameUpdateConfig frameUpdateConfig = {};
    frameUpdateConfig.updateBuffInspectOverlay =
        m_currentSceneKind == SceneKind::Outdoor || m_currentSceneKind == SceneKind::Indoor;
    GameplayScreenController::updateSharedFrameState(
        m_gameplayScreenRuntime,
        input.screenWidth,
        input.screenHeight,
        deltaSeconds,
        frameUpdateConfig);
    recordDiagnostics(
        m_gameplayUpdatePerformanceDiagnostics.sharedFrameStateNanoseconds,
        m_lastGameplayUpdateFramePerformanceDiagnostics.sharedFrameStateNanoseconds,
        sharedFrameStateBeginTickCount);

    IGameplayWorldRuntime *pWorldRuntime = activeWorldRuntime();
    const uint64_t worldInteractionStateBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    const GameplayStandardWorldInteractionFrameState worldInteractionFrameState =
        GameplayScreenController::captureStandardWorldInteractionFrameState(m_gameplayScreenRuntime);
    m_sharedWorldInteractionBlockedThisFrame =
        GameplayScreenController::isStandardWorldInteractionBlockedForFrame(
            m_gameplayScreenRuntime,
            GameplayStandardWorldInteractionFrameGateConfig{
                .state = worldInteractionFrameState,
                .hasActiveLootView = hasActiveLootView,
            });
    recordDiagnostics(
        m_gameplayUpdatePerformanceDiagnostics.worldInteractionStateNanoseconds,
        m_lastGameplayUpdateFramePerformanceDiagnostics.worldInteractionStateNanoseconds,
        worldInteractionStateBeginTickCount);

    if (pWorldRuntime != nullptr)
    {
        if (collectPerformanceDiagnostics)
        {
            ++m_gameplayUpdatePerformanceDiagnostics.activeWorldFrames;
        }

        const uint64_t activeMemberSyncBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
        synchronizeGameplayActiveMemberToReadyMember(
            m_gameplayScreenRuntime,
            m_gameplayScreenState,
            m_turnBasedCombatRuntime);
        recordDiagnostics(
            m_gameplayUpdatePerformanceDiagnostics.activeMemberSyncNanoseconds,
            m_lastGameplayUpdateFramePerformanceDiagnostics.activeMemberSyncNanoseconds,
            activeMemberSyncBeginTickCount);

        const Party *pParty = pWorldRuntime->party();
        const bool hasReadyMember = pParty != nullptr && pParty->hasSelectableMemberInGameplay();
        const bool isUtilitySpellModalActive =
            m_gameplayScreenRuntime.utilitySpellOverlayReadOnly().active
            && m_gameplayScreenRuntime.utilitySpellOverlayReadOnly().mode
                != GameplayUiController::UtilitySpellOverlayMode::InventoryTarget;
        const bool isModalOverlayActive =
            m_gameplayScreenRuntime.readableScrollOverlayReadOnly().active
            || m_gameplayScreenRuntime.lootSummaryOverlayReadOnly().active
            || GameplayFormationBuilder::isOpen(m_gameplayScreenRuntime);

        const uint64_t sharedInputBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
        m_sharedInputFrameResult =
            GameplayInputController::updateSharedGameplayInputFrame(
                m_gameplayScreenState,
                m_gameplayScreenRuntime,
                m_gameplaySpellService,
                GameplaySharedInputFrameConfig{
                    .pKeyboardState = input.keyboardState(),
                    .pInputFrame = &input,
                    .mouseWheelDelta = input.mouseWheelDelta,
                    .screenWidth = input.screenWidth,
                    .screenHeight = input.screenHeight,
                    .pointerX = input.pointerX,
                    .pointerY = input.pointerY,
                    .leftButtonPressed = input.leftMouseButton.held,
                    .rightButtonPressed = input.rightMouseButton.held,
                    .hasReadyMember = hasReadyMember,
                    .canBeginQuickCast = true,
                    .isUtilitySpellModalActive = isUtilitySpellModalActive,
                    .isModalOverlayActive = isModalOverlayActive,
                    .processSharedGameplayHotkeys = true,
                    .processQuickCast = true,
                });
        recordDiagnostics(
            m_gameplayUpdatePerformanceDiagnostics.sharedInputNanoseconds,
            m_lastGameplayUpdateFramePerformanceDiagnostics.sharedInputNanoseconds,
            sharedInputBeginTickCount);

        GameplayInputFrame worldInput = input;

        if (m_overlayInteractionState.gameplayHudAttackRequested)
        {
            pulseGameplayAction(worldInput, KeyboardAction::Attack);
            m_overlayInteractionState.gameplayHudAttackRequested = false;
        }

        if (m_overlayInteractionState.gameplayHudTriggerRequested)
        {
            pulseGameplayAction(worldInput, KeyboardAction::Trigger);
            m_overlayInteractionState.gameplayHudTriggerRequested = false;
        }

        const bool gameplayHudPointerActive =
            m_overlayInteractionState.gameplayHudClickLatch
            && m_overlayInteractionState.gameplayHudPressedTarget.type != GameplayHudPointerTargetType::None;
        const bool quickCastHudPointerActive =
            gameplayHudPointerActive
            && m_overlayInteractionState.gameplayHudPressedTarget.type
                == GameplayHudPointerTargetType::QuickCastButton;
        const bool gameplayCursorModeActive = m_sharedInputFrameResult.mouseLookPolicy.cursorModeActive;
        const bool pendingSpellTargetActive = m_gameplayScreenState.pendingSpellTarget().active;
        const bool gameplayHudPointerBlocksWorldInput =
            gameplayHudPointerActive
            && (!quickCastHudPointerActive || pendingSpellTargetActive);
        const bool rightMouseInspectPauseActive = input.rightMouseButton.held;
        const bool modalWorldInputBlocked =
            m_sharedInputFrameResult.journalInputConsumed
            || m_sharedInputFrameResult.worldInputBlocked
            || gameplayHudPointerBlocksWorldInput;
        const bool standardWorldInputBlocked =
            gameplayCursorModeActive
            || modalWorldInputBlocked;
        const bool allowWorldMovementInput =
            !standardWorldInputBlocked
            && !pendingSpellTargetActive
            && !rightMouseInspectPauseActive;
        // Modal screens (inventory, dialogue, rest, menus) freeze party timers and physics like the original; outdoor
        // movement already returns early on the same flags.
        const bool worldMovementPaused =
            rightMouseInspectPauseActive
            || m_sharedInputFrameResult.journalInputConsumed
            || m_sharedInputFrameResult.worldInputBlocked;
        float worldMovementDeltaSeconds = worldMovementPaused ? 0.0f : deltaSeconds;
        worldInput.cameraDeltaSeconds = worldMovementDeltaSeconds;
        bool turnBasedMovementStep = false;
        if (m_turnBasedCombatRuntime.active() && !worldMovementPaused)
        {
            const bool classicTurnKeys =
                m_gameplayScreenRuntime.settingsSnapshot().controlScheme == ControlScheme::Classic;
            turnBasedMovementStep =
                m_turnBasedCombatRuntime.noteMovementInput(worldInput, deltaSeconds, classicTurnKeys);
            worldMovementDeltaSeconds = m_turnBasedCombatRuntime.movementDeltaSecondsForFrame(deltaSeconds);
            if (!turnBasedMovementStep && pWorldRuntime->partyNeedsTurnBasedPhysicsUpdate())
            {
                worldInput.turnBasedPhysicsStep = true;
                worldMovementDeltaSeconds = deltaSeconds;
            }
        }

        const uint64_t worldMovementBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
        pWorldRuntime->updateWorldMovement(worldInput, worldMovementDeltaSeconds, allowWorldMovementInput);
        recordDiagnostics(
            m_gameplayUpdatePerformanceDiagnostics.worldMovementNanoseconds,
            m_lastGameplayUpdateFramePerformanceDiagnostics.worldMovementNanoseconds,
            worldMovementBeginTickCount);

        if (collectPerformanceDiagnostics)
        {
            const GameplayWorldMovementFrameDiagnostics *pWorldMovementDiagnostics =
                pWorldRuntime->lastWorldMovementFrameDiagnostics();

            if (pWorldMovementDiagnostics != nullptr)
            {
                m_lastGameplayUpdateFramePerformanceDiagnostics.worldMovement = *pWorldMovementDiagnostics;
            }
        }

        const bool gameplayWorldPaused =
            modalWorldInputBlocked
            || pendingSpellTargetActive
            || m_sharedWorldInteractionBlockedThisFrame
            || rightMouseInspectPauseActive;

        const Party *pTurnBasedParty = pWorldRuntime->party();
        const bool turnBasedWorldPaused =
            m_turnBasedCombatRuntime.active()
            && !m_turnBasedCombatRuntime.shouldUpdateActorAi(pTurnBasedParty);
        pWorldRuntime->setTurnBasedActorMode(m_turnBasedCombatRuntime.actorMode());

        synchronizeTurnBasedPendingWorldActions(
            m_turnBasedCombatRuntime,
            pWorldRuntime,
            m_turnBasedPendingWorldActions);

        logTurnBasedFrameTraceIfNeeded(
            !turnBasedWorldPaused,
            gameplayWorldPaused,
            allowWorldMovementInput,
            turnBasedMovementStep,
            gameplayCursorModeActive,
            modalWorldInputBlocked,
            pendingSpellTargetActive,
            m_sharedWorldInteractionBlockedThisFrame,
            worldMovementDeltaSeconds,
            deltaSeconds);

        if (!gameplayWorldPaused && !turnBasedWorldPaused)
        {
            if (collectPerformanceDiagnostics)
            {
                ++m_gameplayUpdatePerformanceDiagnostics.actorAiFrames;
            }

            const uint64_t actorAiBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
            pWorldRuntime->updateActorAi(deltaSeconds);
            gameRulesFor(pWorldRuntime->party()).monsters.updateMonsters(*pWorldRuntime, deltaSeconds);

            if (Party *pParty = pWorldRuntime->party())
            {
                // MM9's Fleet Foot: its speed, the speed-up a quarter larger while no hostile is near.
                const PartyBuffState *pFleetFoot = pParty->partyBuff(PartyBuffId::FleetFoot);
                pParty->setSpellMovementMultiplier(pFleetFoot != nullptr
                    ? fleetFootSpeedMultiplier(pFleetFoot->power, partyHasGreenAlert(*pWorldRuntime))
                    : 1.0f);
                pParty->rules().spells.updateAuras(*pParty, deltaSeconds);
                // Turn-based combat regenerates once per completed turn (GameplayController).
                if (!m_turnBasedCombatRuntime.active())
                {
                    pParty->rules().skills.updateRegeneration(*pParty, *pWorldRuntime, deltaSeconds);
                }

                pParty->rules().combat.updateCombat(*pParty, *pWorldRuntime, deltaSeconds);
                pParty->rules().classes.update(*pParty, *pWorldRuntime, deltaSeconds);
            }
            recordDiagnostics(
                m_gameplayUpdatePerformanceDiagnostics.actorAiNanoseconds,
                m_lastGameplayUpdateFramePerformanceDiagnostics.actorAiNanoseconds,
                actorAiBeginTickCount);
        }
        else if (turnBasedWorldPaused)
        {
            pWorldRuntime->updateTurnBasedPausedActorAnimations(deltaSeconds);
        }

        if (!gameplayWorldPaused)
        {
            pWorldRuntime->actorHitFeedback().update(deltaSeconds);
        }

        synchronizeTurnBasedPendingWorldActions(
            m_turnBasedCombatRuntime,
            pWorldRuntime,
            m_turnBasedPendingWorldActions);

        if (!gameplayWorldPaused)
        {
            m_turnBasedCombatRuntime.update(pWorldRuntime->party(), pWorldRuntime, deltaSeconds);
        }

        const uint64_t combatEventsBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
        // The combat log records only while it is shown (nothing is kept or worded otherwise).
        m_gameplayScreenRuntime.combatLog().setRecording(m_gameplayScreenRuntime.combatLogShown());
        m_gameplayScreenRuntime.combatLog().setGameMinutes(pWorldRuntime->gameMinutes());
        Party *pMutableParty = pWorldRuntime->party();
        if (pMutableParty != nullptr && !m_gameplayCombatController.pendingCombatEvents().empty())
        {
            GameplayCombatController::PendingCombatEventContext combatEventContext{
                .party = *pMutableParty,
                .pWorldRuntime = pWorldRuntime,
                .pRuntime = &m_gameplayScreenRuntime,
            };
            m_gameplayCombatController.handleAndClearPendingCombatEvents(combatEventContext);
        }
        recordDiagnostics(
            m_gameplayUpdatePerformanceDiagnostics.combatEventsNanoseconds,
            m_lastGameplayUpdateFramePerformanceDiagnostics.combatEventsNanoseconds,
            combatEventsBeginTickCount);

        const bool worldInputBlocked = modalWorldInputBlocked || m_sharedWorldInteractionBlockedThisFrame;
        const uint64_t interactionFrameBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
        GameplayInteractionController::updateWorldInteractionFrame(
            m_gameplayScreenState,
            m_overlayInteractionState,
            m_gameplayScreenRuntime,
            m_gameplaySpellService,
            worldInput,
            m_sharedInputFrameResult,
            worldInputBlocked);
        recordDiagnostics(
            m_gameplayUpdatePerformanceDiagnostics.interactionFrameNanoseconds,
            m_lastGameplayUpdateFramePerformanceDiagnostics.interactionFrameNanoseconds,
            interactionFrameBeginTickCount);
    }

    updateMm9QuestMarkerCache();

    if (deltaSeconds > 0.0f && !input.rightMouseButton.held)
    {
        const uint64_t projectileCooldownBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
        m_gameplayProjectileService.updateProjectileImpactPresentation(deltaSeconds);
        GameplayActionController::updateCooldowns(m_gameplayScreenState, deltaSeconds);
        recordDiagnostics(
            m_gameplayUpdatePerformanceDiagnostics.projectileAndCooldownNanoseconds,
            m_lastGameplayUpdateFramePerformanceDiagnostics.projectileAndCooldownNanoseconds,
            projectileCooldownBeginTickCount);
    }

    if (collectPerformanceDiagnostics)
    {
        const uint64_t totalNanoseconds = SDL_GetTicksNS() - totalBeginTickCount;
        m_gameplayUpdatePerformanceDiagnostics.totalNanoseconds += totalNanoseconds;
        m_lastGameplayUpdateFramePerformanceDiagnostics.totalNanoseconds += totalNanoseconds;
        const uint64_t performanceLogBeginTickCount = SDL_GetTicksNS();
        const bool loggedPerformanceDiagnostics = logGameplayUpdatePerformanceDiagnostics(SDL_GetTicks());
        const uint64_t performanceLogNanoseconds = SDL_GetTicksNS() - performanceLogBeginTickCount;
        m_lastGameplayUpdateFramePerformanceDiagnostics.performanceTraceLogNanoseconds +=
            performanceLogNanoseconds;
        m_lastGameplayUpdateFramePerformanceDiagnostics.totalNanoseconds += performanceLogNanoseconds;

        if (!loggedPerformanceDiagnostics)
        {
            m_gameplayUpdatePerformanceDiagnostics.performanceTraceLogNanoseconds +=
                performanceLogNanoseconds;
            m_gameplayUpdatePerformanceDiagnostics.totalNanoseconds += performanceLogNanoseconds;
        }
    }
}

namespace
{
// The cinematic's view of the active world: actor positions and the party for its camera, map events, sounds and actor
// steps through the same channels the event scripts use.
class SessionCinematicWorld : public ICinematicWorld
{
public:
    explicit SessionCinematicWorld(IGameplayWorldRuntime &world)
        : m_world(world)
    {
    }

    std::optional<GameplayWorldPoint> actorFeet(size_t actorIndex) const override
    {
        GameplayRuntimeActorState state = {};

        if (!m_world.actorRuntimeState(actorIndex, state))
        {
            return std::nullopt;
        }

        return GameplayWorldPoint{state.preciseX, state.preciseY, state.preciseZ};
    }

    float actorHeight(size_t actorIndex) const override
    {
        GameplayRuntimeActorState state = {};
        return m_world.actorRuntimeState(actorIndex, state) ? float(state.bodyHeight != 0 ? state.bodyHeight
            : state.height) : 0.0f;
    }

    GameplayWorldPoint partyEye() const override
    {
        return {m_world.partyX(), m_world.partyY(), m_world.partyEyeZ()};
    }

    void runEvent(uint16_t eventId) override
    {
        size_t previousMessageCount = 0;

        if (!m_world.executeMapEvent(eventId, previousMessageCount))
        {
            std::cerr << "Cinematic: map event " << eventId << " did not run\n";
        }
    }

    void playSound(const std::string &soundName) override
    {
        if (EventRuntimeState *pEvents = m_world.eventRuntimeState())
        {
            EventRuntimeState::PendingSound request = {};
            request.soundScope = SoundScope::World;
            request.soundName = soundName;
            pEvents->pendingSounds.push_back(std::move(request));
        }
    }

    void setActorHidden(size_t actorIndex, bool hidden) override
    {
        EventRuntimeState *pEvents = m_world.eventRuntimeState();

        if (pEvents == nullptr)
        {
            return;
        }

        // As evt.SetMonsterBit(actor, Invisible, hidden) does.
        const uint32_t actorId = uint32_t(actorIndex);
        const uint32_t bit = uint32_t(EvtActorAttribute::Invisible);
        std::unordered_map<uint32_t, uint32_t> &setMasks = hidden ? pEvents->actorSetMasks : pEvents->actorClearMasks;
        std::unordered_map<uint32_t, uint32_t> &clearMasks = hidden ? pEvents->actorClearMasks : pEvents->actorSetMasks;
        setMasks[actorId] |= bit;

        if (const auto found = clearMasks.find(actorId); found != clearMasks.end())
        {
            found->second &= ~bit;

            if (found->second == 0)
            {
                clearMasks.erase(found);
            }
        }

        m_world.applyEventRuntimeState();
    }

    void placeActor(size_t actorIndex, const GameplayWorldPoint &feet) override
    {
        if (ISceneEventContext *pContext = m_world.sceneEventContext())
        {
            pContext->setMapActorPosition(actorIndex, feet.x, feet.y, feet.z);
        }
    }

    void faceActor(size_t actorIndex, float yawRadians, float seconds) override
    {
        EventRuntimeState *pEvents = m_world.eventRuntimeState();
        GameplayRuntimeActorState state = {};

        if (pEvents == nullptr || !m_world.actorRuntimeState(actorIndex, state))
        {
            return;
        }

        // From the heading it shows now (its AI's, or a turn already given).
        EventRuntimeState::ActorPresentation &presentation = pEvents->actorPresentations[uint32_t(actorIndex)];
        presentation.yawFromRadians = state.yawRadians;
        presentation.yawToRadians = yawRadians;
        presentation.turnSeconds = std::max(seconds, 0.0f);
        presentation.turnElapsedSeconds = 0.0f;
        presentation.yawRadians = presentation.turnSeconds > 0.0f ? state.yawRadians : yawRadians;
    }

    void playActorClip(size_t actorIndex, const std::string &clip, bool loop) override
    {
        if (EventRuntimeState *pEvents = m_world.eventRuntimeState())
        {
            EventRuntimeState::ActorPresentation &presentation = pEvents->actorPresentations[uint32_t(actorIndex)];
            presentation.clip = clip;
            presentation.then.clear();
            presentation.hold = false;
            presentation.loop = loop;
            presentation.clipSeconds = 0.0f;
        }
    }

    void clearActorPresentation(size_t actorIndex) override
    {
        if (EventRuntimeState *pEvents = m_world.eventRuntimeState())
        {
            pEvents->actorPresentations.erase(uint32_t(actorIndex));
        }
    }

    void moveDecoration(uint32_t decorationKey, const GameplayWorldPoint &offset, float seconds) override
    {
        if (EventRuntimeState *pEvents = m_world.eventRuntimeState())
        {
            OpenYAMM::Game::moveDecoration(*pEvents, decorationKey, {offset.x, offset.y, offset.z}, seconds);
        }
    }

private:
    IGameplayWorldRuntime &m_world;
};

bool newlyPressed(const GameplayInputFrame &input, SDL_Scancode scancode)
{
    return input.scancodePressCount(scancode) > 0;
}
}

void GameSession::setMapCinematics(std::optional<CinematicLibrary> library)
{
    m_mapCinematics = std::move(library);
}

const std::optional<CinematicLibrary> &GameSession::mapCinematics() const
{
    return m_mapCinematics;
}

CinematicRuntime &GameSession::cinematicRuntime()
{
    return m_cinematicRuntime;
}

const CinematicRuntime &GameSession::cinematicRuntime() const
{
    return m_cinematicRuntime;
}

bool GameSession::playCinematic(const std::string &id, uint16_t doneEventId)
{
    IGameplayWorldRuntime *pWorldRuntime = activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return false;
    }

    SessionCinematicWorld world(*pWorldRuntime);
    const CinematicDefinition *pDefinition = m_mapCinematics ? m_mapCinematics->find(id) : nullptr;

    if (pDefinition == nullptr)
    {
        // The script goes on as if it had played (its done event runs), so a missing cinematic loses no progress.
        std::cerr << "Cinematic: " << m_currentMapFileName << " has no cinematic '" << id << "'\n";

        if (doneEventId != 0)
        {
            world.runEvent(doneEventId);
        }

        return false;
    }

    std::cout << "Cinematic: " << id << " starts (" << pDefinition->durationSeconds << " s)\n";
    m_cinematicRuntime.start(*pDefinition, doneEventId, world);
    return true;
}

void GameSession::stopCinematics()
{
    m_cinematicRuntime.stop();
    m_cinematicRuntime.shake().clear();
}

void GameSession::finishAmbientCinematic()
{
    IGameplayWorldRuntime *pWorldRuntime = activeWorldRuntime();

    if (pWorldRuntime == nullptr || !m_cinematicRuntime.active() || m_cinematicRuntime.takesOverView())
    {
        return;
    }

    SessionCinematicWorld world(*pWorldRuntime);
    m_cinematicRuntime.skip(world, true);
    // The skip leaves it ending; this update finishes it (actors released, its done event run).
    m_cinematicRuntime.update(0.0f, world);
}

bool GameSession::updateCinematics(const GameplayInputFrame &input, float deltaSeconds)
{
    IGameplayWorldRuntime *pWorldRuntime = activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        stopCinematics();
        return false;
    }

    SessionCinematicWorld world(*pWorldRuntime);
    bool skipped = false;

    if (EventRuntimeState *pEvents = pWorldRuntime->eventRuntimeState())
    {
        for (const EventRuntimeState::CameraShakeRequest &request : pEvents->cameraShakeRequests)
        {
            float intensity = request.intensity;

            if (request.positional)
            {
                // MM9's EarthQuake: full within the inner radius, fading to nothing at the outer one.
                const float dx = pWorldRuntime->partyX() - request.x;
                const float dy = pWorldRuntime->partyY() - request.y;
                const float dz = pWorldRuntime->partyFootZ() - request.z;
                const float distance = std::sqrt(dx * dx + dy * dy + dz * dz);
                const float band = request.outerRadius - request.innerRadius;
                const float share = distance <= request.innerRadius ? 1.0f
                    : band > 0.0f ? std::clamp(1.0f - (distance - request.innerRadius) / band, 0.0f, 1.0f) : 0.0f;
                intensity *= share;
            }

            m_cinematicRuntime.shake().start(intensity, request.seconds);
        }

        pEvents->cameraShakeRequests.clear();

        if (pEvents->pendingCinematicSkip)
        {
            pEvents->pendingCinematicSkip = false;
            skipped = m_cinematicRuntime.skip(world, true);
        }

        if (pEvents->pendingCinematic)
        {
            const EventRuntimeState::PendingCinematic request = std::move(*pEvents->pendingCinematic);
            pEvents->pendingCinematic.reset();
            playCinematic(request.id, request.doneEventId);
        }
    }

    m_cinematicRuntime.shake().update(deltaSeconds);

    if (!m_cinematicRuntime.active())
    {
        return false;
    }

    // Overheard talk plays on while the party moves: no lock, no skip keys.
    if (!m_cinematicRuntime.takesOverView())
    {
        m_cinematicRuntime.update(deltaSeconds / m_gameSpeed, world);
        return false;
    }

    const bool escapeHeld = input.isScancodeHeld(SDL_SCANCODE_ESCAPE);

    if (!skipped && m_cinematicRuntime.skippable()
        && (newlyPressed(input, SDL_SCANCODE_ESCAPE) || newlyPressed(input, SDL_SCANCODE_SPACE)
            || newlyPressed(input, SDL_SCANCODE_RETURN) || newlyPressed(input, SDL_SCANCODE_KP_ENTER)))
    {
        std::cout << "Cinematic: " << m_cinematicRuntime.activeId() << " skipped at "
                  << m_cinematicRuntime.elapsedSeconds() << " s\n";
        skipped = m_cinematicRuntime.skip(world);
    }

    // A skip's events ran this frame: the cinematic finishes (its done event) next frame, after a map move they asked
    // for has happened (a map change ends it without the done event; an event's start clears a pending move).
    if (!skipped)
    {
        m_cinematicRuntime.update(deltaSeconds, world);
    }

    // The Escape that skipped (or was held through the end) must not open the menu once play resumes.
    if (escapeHeld)
    {
        m_overlayInteractionState.menuToggleLatch = true;
    }

    m_cinematicInputFrame = {};
    m_cinematicInputFrame.screenWidth = input.screenWidth;
    m_cinematicInputFrame.screenHeight = input.screenHeight;
    m_cinematicInputFrame.pointerX = input.pointerX;
    m_cinematicInputFrame.pointerY = input.pointerY;
    m_cinematicInputFrame.cameraDeltaSeconds = 0.0f;
    return true;
}

void GameSession::renderCinematicOverlay(int width, int height)
{
    GameplayUiRuntime &ui = m_gameplayUiRuntime;

    if (!ui.hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }

    ui.prepareHudView(width, height);
    const std::optional<GameplayHudTextureHandle> black = ui.ensureSolidHudTextureLoaded("__cinematic_black",
        0xff000000u);

    if (!black)
    {
        return;
    }

    // Letterbox: at full, bars top and bottom leave MM9's 2:1 picture (its 800 x 400 view on 800 x 600: a sixth of a
    // 4:3 screen each, 5.6 % of a 16:9 one; none on a screen already wider than 2:1).
    const float fullBar = std::max(0.0f, (float(height) - float(width) * 0.5f) * 0.5f);
    const float bar = std::round(fullBar * m_cinematicRuntime.letterboxAmount());

    if (bar > 0.0f)
    {
        ui.submitHudTexturedQuad(black->textureHandle, 0.0f, 0.0f, float(width), bar);
        ui.submitHudTexturedQuad(black->textureHandle, 0.0f, float(height) - bar, float(width), bar);
    }

    const std::string &subtitle = m_cinematicRuntime.subtitle();

    if (!subtitle.empty())
    {
        const float scale = std::max(0.75f, float(height) / 1080.0f);
        const char *pFont = GameplayUiSkin::CombatFontName;
        const float lineHeight = float(m_gameplayScreenRuntime.hudFontHeight(pFont)) * scale * 1.1f;
        const std::vector<std::string> lines =
            m_gameplayScreenRuntime.wrapHudTextToWidth(pFont, subtitle, float(width) * 0.8f / scale);
        float y = float(height) - std::max(bar, float(height) * 0.06f) + float(height) * 0.015f;

        if (bar < lineHeight * float(lines.size()))
        {
            y = float(height) - float(height) * 0.06f - lineHeight * float(lines.size());
        }

        for (const std::string &line : lines)
        {
            const float lineWidth = m_gameplayScreenRuntime.measureHudTextWidth(pFont, line) * scale;
            m_gameplayScreenRuntime.renderHudTextLine(pFont, 0xffe8f0f4u, line,
                std::round((float(width) - lineWidth) * 0.5f), std::round(y), scale);
            y += lineHeight;
        }
    }

    const float fade = m_cinematicRuntime.fadeAmount();

    if (fade > 0.0f)
    {
        const uint32_t alpha = uint32_t(std::lround(std::clamp(fade, 0.0f, 1.0f) * 255.0f));
        char name[40] = {};
        std::snprintf(name, sizeof(name), "__cinematic_fade_%02x", alpha);

        if (const std::optional<GameplayHudTextureHandle> veil = ui.ensureSolidHudTextureLoaded(name, alpha << 24))
        {
            ui.submitHudTexturedQuad(veil->textureHandle, 0.0f, 0.0f, float(width), float(height));
        }
    }
}

void GameSession::updateMm9QuestMarkerCache()
{
    if (m_pDataRepository == nullptr
        || !m_pDataRepository->isBound()
        || m_pActiveWorldRuntime == nullptr
        || data().mm9QuestInteractionTable().interactions().empty())
    {
        if (m_mm9QuestMarkerCache.active())
        {
            m_mm9QuestMarkerCache.clear();
        }
        return;
    }

    Party *pParty = m_pActiveWorldRuntime->party();
    if (pParty == nullptr)
    {
        m_mm9QuestMarkerCache.clear();
        return;
    }

    std::string mapId = std::filesystem::path(m_currentMapFileName).stem().string();
    std::transform(
        mapId.begin(),
        mapId.end(),
        mapId.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
    std::vector<Mm9LoadedQuestMarkerActor> actors;
    uint64_t actorEligibilitySignature = 1469598103934665603ULL;
    const auto addSignatureValue = [&actorEligibilitySignature](uint64_t value)
    {
        actorEligibilitySignature ^= value;
        actorEligibilitySignature *= 1099511628211ULL;
    };
    for (size_t actorIndex = 0; actorIndex < m_pActiveWorldRuntime->mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState state = {};
        if (!m_pActiveWorldRuntime->actorRuntimeState(actorIndex, state) || state.mm9RudeId <= 0)
        {
            continue;
        }
        const bool interactable = !state.isDead && !state.isInvisible && !state.hostileToParty;
        actors.push_back({
            static_cast<uint32_t>(actorIndex),
            {
                mapId,
                state.mm9SourceObjectIndex,
                static_cast<uint32_t>(state.mm9RudeId),
                interactable,
            },
        });
        addSignatureValue(actorIndex);
        addSignatureValue(state.mm9SourceObjectIndex);
        addSignatureValue(static_cast<uint32_t>(state.mm9RudeId));
        addSignatureValue(interactable ? 1 : 0);
    }

    // Trainer markers follow what the members could learn: class, race, the base stats some masteries ask for, and
    // every skill's level and mastery. Characters change these in many places, so the update compares a signature
    // (order-independent over the skill map) instead of a revision.
    const Mm9TrainerMarkerTables trainerTables = {
        &data().mm9SkillTrainerTable(),
        &data().classSkillTable(),
        &data().npcDialogTable(),
    };
    if (!actors.empty() && !data().mm9SkillTrainerTable().entries().empty())
    {
        const std::hash<std::string> hashString;
        for (const Character &member : pParty->members())
        {
            addSignatureValue(hashString(member.className));
            addSignatureValue(member.raceId);
            addSignatureValue(member.intellect);
            addSignatureValue(member.personality);
            addSignatureValue(member.endurance);
            uint64_t skillsSignature = 0;
            for (const auto &[skillName, skill] : member.skills)
            {
                skillsSignature += (hashString(skillName) * 1099511628211ULL)
                    ^ (static_cast<uint64_t>(skill.level) << 8)
                    ^ static_cast<uint64_t>(skill.mastery);
            }
            addSignatureValue(skillsSignature);
        }
    }

    const Mm9QuestEligibilityStamp stamp = {
        pParty->dialogueEligibilityRevision(),
        m_mm9QuestMarkerMapRevision ^ actorEligibilitySignature,
    };
    if (!m_mm9QuestMarkerCache.active())
    {
        m_mm9QuestMarkerCache.loadLocation(
            true,
            actors,
            stamp,
            *pParty,
            data().journalQuestTable(),
            data().mm9RudeDialogueTable(),
            data().mm9QuestInteractionTable(),
            &trainerTables);
        return;
    }
    m_mm9QuestMarkerCache.update(
        actors,
        stamp,
        *pParty,
        data().journalQuestTable(),
        data().mm9RudeDialogueTable(),
        data().mm9QuestInteractionTable(),
        &trainerTables);
}

void GameSession::clearSharedInputFrameResult(bool blockWorldInput)
{
    m_sharedInputFrameResult = {};
    m_sharedInputFrameResult.worldInputBlocked = blockWorldInput;
    m_sharedWorldInteractionBlockedThisFrame = blockWorldInput;
    m_gameplayScreenState.gameplayMouseLookState().clear();
}

void GameSession::consumePendingGameplayAudioRequests()
{
    m_gameplayScreenRuntime.consumePendingEventRuntimeAudioRequests();
}

void GameSession::renderGameplayUi(int width, int height)
{
    const bool collectPerformanceDiagnostics = m_framePerformanceDiagnosticsEnabled;
    const uint64_t totalBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
    const auto recordDiagnostics =
        [&](uint64_t &field, uint64_t beginTickCount)
        {
            if (collectPerformanceDiagnostics)
            {
                field += SDL_GetTicksNS() - beginTickCount;
            }
        };
    const auto finishDiagnostics =
        [&]()
        {
            if (!collectPerformanceDiagnostics)
            {
                return;
            }

            m_lastGameplayUiFramePerformanceDiagnostics.totalNanoseconds =
                SDL_GetTicksNS() - totalBeginTickCount;
            m_lastGameplayUiFramePerformanceDiagnostics.overlays =
                m_gameplayUiRuntime.lastOverlayFramePerformanceDiagnostics();
        };

    IGameplayWorldRuntime *pWorldRuntime = activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        finishDiagnostics();
        return;
    }

    // A cinematic hides the gameplay HUD: its bars, fade and subtitle only.
    if (m_cinematicRuntime.takesOverView())
    {
        renderCinematicOverlay(width, height);
        finishDiagnostics();
        return;
    }

    const uint64_t uiRenderStateBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
    const GameplayWorldUiRenderState uiRenderState = pWorldRuntime->gameplayUiRenderState(width, height);
    recordDiagnostics(
        m_lastGameplayUiFramePerformanceDiagnostics.worldUiRenderStateNanoseconds,
        uiRenderStateBeginTickCount);

    if (!uiRenderState.renderGameplayHud)
    {
        finishDiagnostics();
        return;
    }

    const GameplayScreenState::GameplayMouseLookState &gameplayMouseLookState =
        m_gameplayScreenState.gameplayMouseLookState();
    const GameplayScreenState::PendingSpellTargetState &pendingSpellCast =
        m_gameplayScreenState.pendingSpellTarget();

    const uint64_t standardUiBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
    GameplayScreenController::renderStandardUi(
        m_gameplayScreenRuntime,
        width,
        height,
        GameplayStandardUiRenderConfig{
            .canRenderHudOverlays = uiRenderState.canRenderHudOverlays,
            .renderGameplayHud = uiRenderState.renderGameplayHud,
            .renderGameplayMouseLookOverlay =
                gameplayMouseLookState.mouseLookActive
                    && !gameplayMouseLookState.cursorModeActive
                    && !pendingSpellCast.active,
            .renderActorInspectOverlay = uiRenderState.renderActorInspectOverlay,
            .renderDebugFallbacks = uiRenderState.renderDebugFallbacks,
        });
    recordDiagnostics(
        m_lastGameplayUiFramePerformanceDiagnostics.standardUiNanoseconds,
        standardUiBeginTickCount);

    const GameplayInputFrame *pInputFrame = currentGameplayInputFrame();

    if (pInputFrame == nullptr)
    {
        finishDiagnostics();
        return;
    }

    const uint64_t pendingSpellOverlayBeginTickCount = collectPerformanceDiagnostics ? SDL_GetTicksNS() : 0;
    if (pendingSpellCast.active)
    {
        GameplaySpellTargetingOverlayRenderer::renderPendingSpellTargetingOverlay(
            m_gameplayScreenRuntime,
            m_gameplaySpellService,
            pendingSpellCast,
            width,
            height,
            pInputFrame->pointerX,
            pInputFrame->pointerY);
    }
    recordDiagnostics(
        m_lastGameplayUiFramePerformanceDiagnostics.pendingSpellOverlayNanoseconds,
        pendingSpellOverlayBeginTickCount);

    // Overheard talk's subtitles over the HUD.
    if (m_cinematicRuntime.active() && !m_cinematicRuntime.subtitle().empty())
    {
        renderCinematicOverlay(width, height);
    }

    finishDiagnostics();
}

const GameplaySharedInputFrameResult &GameSession::sharedInputFrameResult() const
{
    return m_sharedInputFrameResult;
}

bool GameSession::sharedWorldInteractionBlockedThisFrame() const
{
    return m_sharedWorldInteractionBlockedThisFrame;
}

void GameSession::requestRelativeMouseMotionReset()
{
    m_relativeMouseMotionResetRequested = true;
}

bool GameSession::consumeRelativeMouseMotionResetRequest()
{
    const bool requested = m_relativeMouseMotionResetRequested;
    m_relativeMouseMotionResetRequested = false;
    return requested;
}

const std::optional<OutdoorPartyRuntime::Snapshot> &GameSession::outdoorPartyState() const
{
    return m_outdoorPartyState;
}

void GameSession::setOutdoorPartyState(const OutdoorPartyRuntime::Snapshot &snapshot)
{
    m_outdoorPartyState = snapshot;
}

void GameSession::setOutdoorPartyState(OutdoorPartyRuntime::Snapshot &&snapshot)
{
    m_outdoorPartyState = std::move(snapshot);
}

const std::optional<OutdoorWorldRuntime::Snapshot> &GameSession::currentOutdoorWorldState() const
{
    return m_currentOutdoorWorldState;
}

void GameSession::setCurrentOutdoorWorldState(const OutdoorWorldRuntime::Snapshot &snapshot)
{
    m_currentOutdoorWorldState = snapshot;
    m_currentOutdoorWorldState->gameMinutes = m_gameMinutes;
    if (m_currentOutdoorWorldState->eventRuntimeState)
    {
        mergeNamedGlobalVarsFromRuntime(*m_currentOutdoorWorldState->eventRuntimeState);
        applyNamedGlobalVarsToRuntime(*m_currentOutdoorWorldState->eventRuntimeState);
    }
}

void GameSession::setCurrentOutdoorWorldState(OutdoorWorldRuntime::Snapshot &&snapshot)
{
    m_currentOutdoorWorldState = std::move(snapshot);
    m_currentOutdoorWorldState->gameMinutes = m_gameMinutes;
    if (m_currentOutdoorWorldState->eventRuntimeState)
    {
        mergeNamedGlobalVarsFromRuntime(*m_currentOutdoorWorldState->eventRuntimeState);
        applyNamedGlobalVarsToRuntime(*m_currentOutdoorWorldState->eventRuntimeState);
    }
}

const std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &GameSession::outdoorWorldStates() const
{
    return m_outdoorWorldStates;
}

std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &GameSession::outdoorWorldStates()
{
    return m_outdoorWorldStates;
}

std::string GameSession::mapStateKey(const std::string &mapFileName) const
{
    const MapStatsEntry *pMap = data().mapStats().findByFileName(mapFileName);
    return pMap != nullptr && !pMap->canonicalId.empty() ? pMap->canonicalId : mapFileName;
}

const std::optional<IndoorSceneRuntime::Snapshot> &GameSession::currentIndoorSceneState() const
{
    return m_currentIndoorSceneState;
}

void GameSession::setCurrentIndoorSceneState(const IndoorSceneRuntime::Snapshot &snapshot)
{
    m_currentIndoorSceneState = snapshot;
    m_currentIndoorSceneState->worldRuntime.gameMinutes = m_gameMinutes;
    if (m_currentIndoorSceneState->eventRuntimeState)
    {
        mergeNamedGlobalVarsFromRuntime(*m_currentIndoorSceneState->eventRuntimeState);
        applyNamedGlobalVarsToRuntime(*m_currentIndoorSceneState->eventRuntimeState);
    }
}

void GameSession::setCurrentIndoorSceneState(IndoorSceneRuntime::Snapshot &&snapshot)
{
    m_currentIndoorSceneState = std::move(snapshot);
    m_currentIndoorSceneState->worldRuntime.gameMinutes = m_gameMinutes;
    if (m_currentIndoorSceneState->eventRuntimeState)
    {
        mergeNamedGlobalVarsFromRuntime(*m_currentIndoorSceneState->eventRuntimeState);
        applyNamedGlobalVarsToRuntime(*m_currentIndoorSceneState->eventRuntimeState);
    }
}

const std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &GameSession::indoorSceneStates() const
{
    return m_indoorSceneStates;
}

std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &GameSession::indoorSceneStates()
{
    return m_indoorSceneStates;
}

const std::unordered_map<std::string, int32_t> &GameSession::namedGlobalVars() const
{
    return m_namedGlobalVars;
}

int32_t GameSession::namedGlobalVar(const std::string &name, int32_t defaultValue) const
{
    const std::unordered_map<std::string, int32_t>::const_iterator it = m_namedGlobalVars.find(name);
    return it != m_namedGlobalVars.end() ? it->second : defaultValue;
}

void GameSession::setNamedGlobalVar(const std::string &name, int32_t value)
{
    if (name.empty())
    {
        return;
    }

    m_namedGlobalVars[name] = value;
}

void GameSession::clearNamedGlobalVar(const std::string &name)
{
    m_namedGlobalVars.erase(name);
}

void GameSession::mergeNamedGlobalVarsFromRuntime(const EventRuntimeState &runtimeState)
{
    for (const auto &[name, value] : runtimeState.namedGlobalVars)
    {
        if (!name.empty())
        {
            m_namedGlobalVars[name] = value;
        }
    }
}

void GameSession::applyNamedGlobalVarsToRuntime(EventRuntimeState &runtimeState) const
{
    for (const auto &[name, value] : m_namedGlobalVars)
    {
        runtimeState.namedGlobalVars[name] = value;
    }
}

void GameSession::setCameraAngles(float yawRadians, float pitchRadians)
{
    m_cameraYawRadians = yawRadians;
    m_cameraPitchRadians = pitchRadians;
    m_cameraAnglesValid = true;
}

float GameSession::cameraYawRadians() const
{
    return m_cameraYawRadians;
}

float GameSession::cameraPitchRadians() const
{
    return m_cameraPitchRadians;
}

bool GameSession::cameraAnglesValid() const
{
    return m_cameraAnglesValid;
}

const std::optional<std::filesystem::path> &GameSession::currentSavePath() const
{
    return m_currentSavePath;
}

void GameSession::setCurrentSavePath(const std::filesystem::path &path)
{
    m_currentSavePath = path;
}

void GameSession::clearCurrentSavePath()
{
    m_currentSavePath.reset();
}

const std::optional<EventRuntimeState::PendingMapMove> &GameSession::pendingMapMove() const
{
    return m_pendingMapMove;
}

void GameSession::setPendingMapMove(const EventRuntimeState::PendingMapMove &pendingMapMove)
{
    m_pendingMapMove = pendingMapMove;
}

void GameSession::setPendingMapMove(EventRuntimeState::PendingMapMove &&pendingMapMove)
{
    m_pendingMapMove = std::move(pendingMapMove);
}

std::optional<EventRuntimeState::PendingMapMove> GameSession::consumePendingMapMove()
{
    std::optional<EventRuntimeState::PendingMapMove> pendingMapMove = std::move(m_pendingMapMove);
    m_pendingMapMove.reset();
    return pendingMapMove;
}

void GameSession::clearPendingMapMove()
{
    m_pendingMapMove.reset();
}

void GameSession::setSaveGameToPathCallback(SaveGameToPathCallback callback)
{
    m_saveGameToPathCallback = std::move(callback);
}

bool GameSession::canSaveGameToPath() const
{
    return static_cast<bool>(m_saveGameToPathCallback);
}

bool GameSession::saveGameToPath(
    const std::filesystem::path &path,
    const std::string &saveName,
    const std::vector<uint8_t> &previewBmp,
    std::string &error) const
{
    return m_saveGameToPathCallback && m_saveGameToPathCallback(path, saveName, previewBmp, error);
}

void GameSession::setSettingsChangedCallback(SettingsChangedCallback callback)
{
    m_settingsChangedCallback = std::move(callback);
}

void GameSession::notifySettingsChanged(const GameSettings &settings) const
{
    if (m_settingsChangedCallback)
    {
        m_settingsChangedCallback(settings);
    }
}

void GameSession::requestOpenNewGameScreen()
{
    m_gameplayScreenState.requestOpenNewGameScreen();
}

void GameSession::requestOpenLoadGameScreen()
{
    m_gameplayScreenState.requestOpenLoadGameScreen();
}

bool GameSession::consumePendingOpenNewGameScreenRequest()
{
    return m_gameplayScreenState.consumePendingOpenNewGameScreenRequest();
}

bool GameSession::consumePendingOpenLoadGameScreenRequest()
{
    return m_gameplayScreenState.consumePendingOpenLoadGameScreenRequest();
}

void GameSession::captureOutdoorRuntimeState(
    const std::string &mapFileName,
    const Party &party,
    const OutdoorPartyRuntime::Snapshot &partySnapshot,
    const OutdoorWorldRuntime::Snapshot &worldSnapshot,
    float yawRadians,
    float pitchRadians)
{
    m_currentSceneKind = SceneKind::Outdoor;
    m_currentMapFileName = mapFileName;
    m_partyState = party;
    m_partyState->setStatistics(&m_playthroughStatistics);
    m_outdoorPartyState = partySnapshot;
    m_gameMinutes = std::max(0.0f, worldSnapshot.gameMinutes);

    OutdoorWorldRuntime::Snapshot normalizedWorldSnapshot = worldSnapshot;
    normalizedWorldSnapshot.gameMinutes = m_gameMinutes;
    normalizedWorldSnapshot.mapLayoutIdentity = m_currentMapLayoutIdentity;
    if (normalizedWorldSnapshot.eventRuntimeState)
    {
        mergeNamedGlobalVarsFromRuntime(*normalizedWorldSnapshot.eventRuntimeState);
        applyNamedGlobalVarsToRuntime(*normalizedWorldSnapshot.eventRuntimeState);
    }
    m_currentOutdoorWorldState = normalizedWorldSnapshot;
    m_outdoorWorldStates[mapStateKey(mapFileName)] = normalizedWorldSnapshot;
    setCameraAngles(yawRadians, pitchRadians);
}

void GameSession::captureIndoorRuntimeState(
    const std::string &mapFileName,
    const Party &party,
    const IndoorSceneRuntime::Snapshot &snapshot)
{
    m_currentSceneKind = SceneKind::Indoor;
    m_currentMapFileName = mapFileName;
    m_partyState = party;
    m_partyState->setStatistics(&m_playthroughStatistics);
    m_gameMinutes = std::max(0.0f, snapshot.worldRuntime.gameMinutes);

    IndoorSceneRuntime::Snapshot normalizedSnapshot = snapshot;
    normalizedSnapshot.worldRuntime.gameMinutes = m_gameMinutes;
    normalizedSnapshot.mapLayoutIdentity = m_currentMapLayoutIdentity;
    if (normalizedSnapshot.eventRuntimeState)
    {
        mergeNamedGlobalVarsFromRuntime(*normalizedSnapshot.eventRuntimeState);
        applyNamedGlobalVarsToRuntime(*normalizedSnapshot.eventRuntimeState);
    }
    m_currentIndoorSceneState = normalizedSnapshot;
    m_indoorSceneStates[mapStateKey(mapFileName)] = normalizedSnapshot;
}

void GameSession::setCurrentMapLayoutIdentity(uint64_t identity)
{
    m_currentMapLayoutIdentity = identity;
}

void GameSession::discardMapState(const std::string &mapFileName, bool partyInside)
{
    const std::string key = mapStateKey(mapFileName);
    m_outdoorWorldStates.erase(key);
    m_outdoorWorldStates.erase(mapFileName);
    m_indoorSceneStates.erase(key);
    m_indoorSceneStates.erase(mapFileName);

    if (!partyInside)
    {
        return;
    }

    if (m_currentSceneKind == SceneKind::Outdoor)
    {
        m_currentOutdoorWorldState.reset();
        m_outdoorPartyState.reset();
    }
    else
    {
        m_currentIndoorSceneState.reset();
    }

    m_cameraAnglesValid = false;
}

std::optional<GameSaveData> GameSession::buildSaveData() const
{
    if (!m_partyState || m_currentMapFileName.empty())
    {
        return std::nullopt;
    }

    if (m_currentSceneKind == SceneKind::Outdoor && (!m_outdoorPartyState || !m_currentOutdoorWorldState))
    {
        return std::nullopt;
    }

    if (m_currentSceneKind == SceneKind::Indoor && !m_currentIndoorSceneState)
    {
        return std::nullopt;
    }

    GameSaveData saveData = {};
    saveData.currentSceneKind = m_currentSceneKind;
    saveData.mapFileName = m_currentMapFileName;
    saveData.party = m_partyState->snapshot();
    saveData.namedGlobalVars = m_namedGlobalVars;
    saveData.savedGameMinutes = m_gameMinutes;
    saveData.ruleset = m_ruleset;
    saveData.mawState = m_pMawRules ? std::optional<MawGameState>(m_pMawRules->state()) : std::nullopt;
    saveData.randomRootSeed = m_randomRootSeed;
    saveData.playthroughId = m_playthroughStatistics.playthroughId();
    saveData.playthroughTimeline = m_playthroughStatistics.serializedTimeline();
    saveData.playthroughPlayedSeconds = m_playthroughStatistics.timeline().playedSeconds;

    if (m_outdoorPartyState && m_currentOutdoorWorldState)
    {
        saveData.hasOutdoorRuntimeState = true;
        saveData.outdoorParty = *m_outdoorPartyState;
        saveData.outdoorWorld = *m_currentOutdoorWorldState;
        saveData.outdoorWorld.gameMinutes = m_gameMinutes;
        if (saveData.outdoorWorld.eventRuntimeState)
        {
            applyNamedGlobalVarsToRuntime(*saveData.outdoorWorld.eventRuntimeState);
        }
    }

    saveData.outdoorWorldStates = m_outdoorWorldStates;
    for (auto &[mapFileName, worldState] : saveData.outdoorWorldStates)
    {
        worldState.gameMinutes = m_gameMinutes;
        if (worldState.eventRuntimeState)
        {
            applyNamedGlobalVarsToRuntime(*worldState.eventRuntimeState);
        }
    }

    if (m_currentIndoorSceneState)
    {
        saveData.hasIndoorSceneState = true;
        saveData.indoorScene = *m_currentIndoorSceneState;
        saveData.indoorScene.worldRuntime.gameMinutes = m_gameMinutes;
        if (saveData.indoorScene.eventRuntimeState)
        {
            applyNamedGlobalVarsToRuntime(*saveData.indoorScene.eventRuntimeState);
        }
    }

    saveData.indoorSceneStates = m_indoorSceneStates;
    for (auto &[mapFileName, sceneState] : saveData.indoorSceneStates)
    {
        sceneState.worldRuntime.gameMinutes = m_gameMinutes;
        if (sceneState.eventRuntimeState)
        {
            applyNamedGlobalVarsToRuntime(*sceneState.eventRuntimeState);
        }
    }

    saveData.cameraYawRadians = m_cameraYawRadians;
    saveData.cameraPitchRadians = m_cameraPitchRadians;
    saveData.cameraAnglesValid = m_cameraAnglesValid;

    const GameplayUiController::HeldInventoryItemState &heldItem = m_gameplayUiController.heldInventoryItem();
    saveData.heldInventoryItemActive = heldItem.active;
    if (heldItem.active)
    {
        saveData.heldInventoryItem = heldItem.item;
        saveData.heldInventoryItemGrabCellOffsetX = heldItem.grabCellOffsetX;
        saveData.heldInventoryItemGrabCellOffsetY = heldItem.grabCellOffsetY;
        saveData.heldInventoryItemGrabOffsetX = heldItem.grabOffsetX;
        saveData.heldInventoryItemGrabOffsetY = heldItem.grabOffsetY;
    }

    return saveData;
}

void GameSession::restoreFromSaveData(const GameSaveData &saveData)
{
    m_turnBasedCombatRuntime.reset();
    m_currentSceneKind = saveData.currentSceneKind;
    m_currentMapFileName = saveData.mapFileName;
    m_gameMinutes = std::max(0.0f, saveData.savedGameMinutes);
    // The ruleset and its state come before the party: restoring the party works out the members' maximum hit and
    // spell points under them and clamps the saved ones to those (under Standard's they would lose what MAW adds).
    m_partyState.reset();
    setRuleset(saveData.ruleset);

    if (m_pMawRules && saveData.mawState)
    {
        m_pMawRules->setState(*saveData.mawState);
    }

    m_partyState = buildConfiguredParty(saveData.party, data(), rulesetGameRules());
    restoreHeldInventoryItemFromSaveData(saveData);

    if (m_partyState)
    {
        m_partyState->setOtherWorldsLoot(m_ruleset.options.otherWorldsLoot);
        m_partyState->setStatistics(&m_playthroughStatistics);
        migrateBlazenRescueRosterUnlock(*m_partyState);

        if (saveData.currentSceneKind == SceneKind::Outdoor && saveData.hasOutdoorRuntimeState)
        {
            migrateSavedRuntimeFollowersToParty(*m_partyState, saveData.outdoorWorld.eventRuntimeState);
        }
        else if (saveData.currentSceneKind == SceneKind::Indoor && saveData.hasIndoorSceneState)
        {
            migrateSavedRuntimeFollowersToParty(*m_partyState, saveData.indoorScene.eventRuntimeState);
        }
    }

    // A save from when the ruleset had more bags: their items move into the bags there are now; what fits nowhere
    // falls at the party's feet once the world runs (GameplayScreenController).
    if (m_partyState && saveData.sourceSaveVersion < SaveVersionFourMawBags)
    {
        InventoryBags::fitIntoBagCount(*m_partyState, m_partyState->rules().items.bagCount(*m_partyState));
    }

    if (m_partyState && saveData.sourceSaveVersion < SaveVersionClassChangeMasteries)
    {
        m_partyState->grantClassChangeMasteries();
    }

    // Saves from before the random streams get their root seed when first loaded.
    setRandomRootSeed(saveData.randomRootSeed != 0 ? saveData.randomRootSeed : freshRandomRootSeed());
    m_namedGlobalVars = saveData.namedGlobalVars;
    const bool collectLegacyNamedGlobalVars = m_namedGlobalVars.empty();

    if (m_gameMinutes <= 0.0f)
    {
        if (saveData.currentSceneKind == SceneKind::Outdoor && saveData.hasOutdoorRuntimeState)
        {
            m_gameMinutes = std::max(0.0f, saveData.outdoorWorld.gameMinutes);
        }
        else if (saveData.currentSceneKind == SceneKind::Indoor && saveData.hasIndoorSceneState)
        {
            m_gameMinutes = std::max(0.0f, saveData.indoorScene.worldRuntime.gameMinutes);
        }
    }

    m_outdoorPartyState = saveData.hasOutdoorRuntimeState
        ? std::optional<OutdoorPartyRuntime::Snapshot>(saveData.outdoorParty)
        : std::nullopt;
    m_currentOutdoorWorldState = saveData.hasOutdoorRuntimeState
        ? std::optional<OutdoorWorldRuntime::Snapshot>(saveData.outdoorWorld)
        : std::nullopt;
    if (m_currentOutdoorWorldState)
    {
        m_currentOutdoorWorldState->gameMinutes = m_gameMinutes;
        if (m_currentOutdoorWorldState->eventRuntimeState)
        {
            if (collectLegacyNamedGlobalVars)
            {
                mergeNamedGlobalVarsFromRuntime(*m_currentOutdoorWorldState->eventRuntimeState);
            }
            applyNamedGlobalVarsToRuntime(*m_currentOutdoorWorldState->eventRuntimeState);
        }
    }

    m_outdoorWorldStates = saveData.outdoorWorldStates;
    for (auto &[mapFileName, worldState] : m_outdoorWorldStates)
    {
        worldState.gameMinutes = m_gameMinutes;
        if (worldState.eventRuntimeState)
        {
            if (collectLegacyNamedGlobalVars)
            {
                mergeNamedGlobalVarsFromRuntime(*worldState.eventRuntimeState);
            }
            applyNamedGlobalVarsToRuntime(*worldState.eventRuntimeState);
        }
    }

    if (saveData.hasOutdoorRuntimeState && m_currentSceneKind == SceneKind::Outdoor)
    {
        m_outdoorWorldStates[mapStateKey(m_currentMapFileName)] = *m_currentOutdoorWorldState;
    }

    m_currentIndoorSceneState = saveData.hasIndoorSceneState
        ? std::optional<IndoorSceneRuntime::Snapshot>(saveData.indoorScene)
        : std::nullopt;
    if (m_currentIndoorSceneState)
    {
        m_currentIndoorSceneState->worldRuntime.gameMinutes = m_gameMinutes;
        if (m_currentIndoorSceneState->eventRuntimeState)
        {
            if (collectLegacyNamedGlobalVars)
            {
                mergeNamedGlobalVarsFromRuntime(*m_currentIndoorSceneState->eventRuntimeState);
            }
            applyNamedGlobalVarsToRuntime(*m_currentIndoorSceneState->eventRuntimeState);
        }
    }

    m_indoorSceneStates = saveData.indoorSceneStates;
    for (auto &[mapFileName, sceneState] : m_indoorSceneStates)
    {
        sceneState.worldRuntime.gameMinutes = m_gameMinutes;
        if (sceneState.eventRuntimeState)
        {
            if (collectLegacyNamedGlobalVars)
            {
                mergeNamedGlobalVarsFromRuntime(*sceneState.eventRuntimeState);
            }
            applyNamedGlobalVarsToRuntime(*sceneState.eventRuntimeState);
        }
    }

    if (saveData.hasIndoorSceneState && m_currentSceneKind == SceneKind::Indoor)
    {
        m_indoorSceneStates[mapStateKey(m_currentMapFileName)] = *m_currentIndoorSceneState;
    }

    for (const auto &[legacyCanonicalId, canonicalId] : data().mapStats().legacyCanonicalIdRenames())
    {
        migrateMapStateKey(m_outdoorWorldStates, legacyCanonicalId, canonicalId);
        migrateMapStateKey(m_indoorSceneStates, legacyCanonicalId, canonicalId);
    }

    // Saves before this kept every map twice, under its file name and its canonical id (which loading preferred).
    const auto keyByCanonicalId = [this](auto &states)
    {
        for (auto stateIt = states.begin(); stateIt != states.end();)
        {
            const std::string key = mapStateKey(stateIt->first);

            if (key == stateIt->first)
            {
                ++stateIt;
                continue;
            }

            auto node = states.extract(stateIt++);

            if (!states.contains(key))
            {
                node.key() = key;
                states.insert(std::move(node));
            }
        }
    };
    keyByCanonicalId(m_outdoorWorldStates);
    keyByCanonicalId(m_indoorSceneStates);

    m_cameraYawRadians = saveData.cameraYawRadians;
    m_cameraPitchRadians = saveData.cameraPitchRadians;
    m_cameraAnglesValid = saveData.cameraAnglesValid;
    m_pendingMapMove.reset();
}

void GameSession::restoreHeldInventoryItemFromSaveData(const GameSaveData &saveData)
{
    GameplayUiController::HeldInventoryItemState &heldItem = m_gameplayUiController.heldInventoryItem();
    heldItem = {};
    if (saveData.heldInventoryItemActive && saveData.heldInventoryItem.objectDescriptionId != 0)
    {
        heldItem.active = true;
        heldItem.item = saveData.heldInventoryItem;
        heldItem.grabCellOffsetX = saveData.heldInventoryItemGrabCellOffsetX;
        heldItem.grabCellOffsetY = saveData.heldInventoryItemGrabCellOffsetY;
        heldItem.grabOffsetX = saveData.heldInventoryItemGrabOffsetX;
        heldItem.grabOffsetY = saveData.heldInventoryItemGrabOffsetY;
    }

    auto applyHeldItemQueryState =
        [&heldItem](Party &party)
        {
            if (heldItem.active)
            {
                party.setHeldItemForQueries(heldItem.item);
            }
            else
            {
                party.clearHeldItemForQueries();
            }
        };

    if (m_partyState)
    {
        applyHeldItemQueryState(*m_partyState);
    }

    Party *pRuntimeParty = m_pActiveWorldRuntime != nullptr ? m_pActiveWorldRuntime->party() : nullptr;
    if (pRuntimeParty != nullptr && (!m_partyState || pRuntimeParty != &*m_partyState))
    {
        applyHeldItemQueryState(*pRuntimeParty);
    }
}
}
