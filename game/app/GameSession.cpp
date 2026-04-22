#include "game/app/GameSession.h"

#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayInteractionController.h"
#include "game/gameplay/GameplayScreenController.h"
#include "game/ui/GameplaySpellTargetingOverlayRenderer.h"

#include <cassert>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
Party buildConfiguredParty(
    const Party::Snapshot &snapshot,
    const GameDataRepository &data)
{
    Party party = {};
    party.setItemTable(&data.itemTable());
    party.setItemEnchantTables(&data.standardItemEnchantTable(), &data.specialItemEnchantTable());
    party.setClassSkillTable(&data.classSkillTable());
    party.restoreSnapshot(snapshot);
    return party;
}

void synchronizeGameplayActiveMemberToReadyMember(
    GameplayScreenRuntime &screenRuntime,
    const GameplayScreenState &screenState)
{
    if (screenRuntime.currentHudScreenState() != GameplayHudScreenState::Gameplay)
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
}

void GameSession::bindDataRepository(const GameDataRepository *pDataRepository)
{
    m_pDataRepository = pDataRepository;
    m_gameplayUiRuntime.bindDataRepository(pDataRepository);

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
    m_gameplayUiRuntime.clear();
    m_gameplayScreenRuntime.clearTransientBindings();
    m_overlayInteractionState = {};
    m_previousKeyboardState.fill(0);
    m_pActiveWorldRuntime = nullptr;
    m_pCurrentGameplayInputFrame = nullptr;
    m_sharedInputFrameResult = {};
    m_sharedWorldInteractionBlockedThisFrame = false;
    m_relativeMouseMotionResetRequested = false;
    m_outdoorPartyState.reset();
    m_currentOutdoorWorldState.reset();
    m_outdoorWorldStates.clear();
    m_currentIndoorSceneState.reset();
    m_indoorSceneStates.clear();
    m_outdoorCameraYawRadians = 0.0f;
    m_outdoorCameraPitchRadians = 0.0f;
    m_currentSavePath.reset();
    m_pendingMapMove.reset();
}

const std::optional<Party> &GameSession::partyState() const
{
    return m_partyState;
}

std::optional<Party> &GameSession::partyState()
{
    return m_partyState;
}

void GameSession::setPartyState(const Party &party)
{
    m_partyState = party;
}

void GameSession::setPartyState(Party &&party)
{
    m_partyState = std::move(party);
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
}

void GameSession::setCurrentMapFileName(std::string &&mapFileName)
{
    m_currentMapFileName = std::move(mapFileName);
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
    m_pActiveWorldRuntime = pWorldRuntime;
}

const GameplayInputFrame *GameSession::currentGameplayInputFrame() const
{
    return m_pCurrentGameplayInputFrame;
}

void GameSession::bindCurrentGameplayInputFrame(const GameplayInputFrame *pInputFrame)
{
    m_pCurrentGameplayInputFrame = pInputFrame;
}

void GameSession::updateGameplay(const GameplayInputFrame &input, float deltaSeconds)
{
    bindCurrentGameplayInputFrame(&input);
    m_sharedInputFrameResult = {};

    GameplayScreenFrameUpdateConfig frameUpdateConfig = {};
    frameUpdateConfig.updateBuffInspectOverlay = m_currentSceneKind == SceneKind::Outdoor;
    GameplayScreenController::updateSharedFrameState(
        m_gameplayScreenRuntime,
        input.screenWidth,
        input.screenHeight,
        deltaSeconds,
        frameUpdateConfig);

    IGameplayWorldRuntime *pWorldRuntime = activeWorldRuntime();
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

    if (pWorldRuntime != nullptr)
    {
        synchronizeGameplayActiveMemberToReadyMember(m_gameplayScreenRuntime, m_gameplayScreenState);

        const Party *pParty = pWorldRuntime->party();
        const bool hasReadyMember = pParty != nullptr && pParty->hasSelectableMemberInGameplay();
        const bool isUtilitySpellModalActive =
            m_gameplayScreenRuntime.utilitySpellOverlayReadOnly().active
            && m_gameplayScreenRuntime.utilitySpellOverlayReadOnly().mode
                != GameplayUiController::UtilitySpellOverlayMode::InventoryTarget;
        const bool isReadableScrollOverlayActive =
            m_gameplayScreenRuntime.readableScrollOverlayReadOnly().active;

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
                    .isReadableScrollOverlayActive = isReadableScrollOverlayActive,
                    .processSharedGameplayHotkeys = true,
                    .processQuickCast = true,
                });

        const bool gameplayCursorModeActive = m_sharedInputFrameResult.mouseLookPolicy.cursorModeActive;
        const bool allowWorldMovementInput =
            !gameplayCursorModeActive
            && !m_sharedInputFrameResult.journalInputConsumed
            && !m_sharedInputFrameResult.worldInputBlocked;
        pWorldRuntime->updateWorldMovement(input, deltaSeconds, allowWorldMovementInput);

        if (!gameplayCursorModeActive)
        {
            pWorldRuntime->updateActorAi(deltaSeconds);
        }

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

        const bool worldInputBlocked =
            m_currentSceneKind == SceneKind::Indoor
                ? !allowWorldMovementInput
                : m_sharedWorldInteractionBlockedThisFrame;
        GameplayInteractionController::updateWorldInteractionFrame(
            m_gameplayScreenState,
            m_overlayInteractionState,
            m_gameplayScreenRuntime,
            m_gameplaySpellService,
            input,
            m_sharedInputFrameResult,
            worldInputBlocked);
    }

    if (deltaSeconds > 0.0f)
    {
        m_gameplayProjectileService.updateProjectileImpactPresentation(deltaSeconds);
        GameplayActionController::updateCooldowns(m_gameplayScreenState, deltaSeconds);
    }

    m_gameplayScreenRuntime.updateHouseVideoBackgroundPreloads();
}

void GameSession::consumePendingGameplayAudioRequests()
{
    m_gameplayScreenRuntime.consumePendingEventRuntimeAudioRequests();
}

void GameSession::renderGameplayUi(int width, int height)
{
    IGameplayWorldRuntime *pWorldRuntime = activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    const GameplayWorldUiRenderState uiRenderState = pWorldRuntime->gameplayUiRenderState(width, height);

    if (!uiRenderState.renderGameplayHud)
    {
        return;
    }

    const GameplayScreenState::GameplayMouseLookState &gameplayMouseLookState =
        m_gameplayScreenState.gameplayMouseLookState();
    const GameplayScreenState::PendingSpellTargetState &pendingSpellCast =
        m_gameplayScreenState.pendingSpellTarget();

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

    const GameplayInputFrame *pInputFrame = currentGameplayInputFrame();

    if (pInputFrame == nullptr)
    {
        return;
    }

    GameplaySpellTargetingOverlayRenderer::renderPendingSpellTargetingOverlay(
        m_gameplayScreenRuntime,
        m_gameplaySpellService,
        pendingSpellCast,
        width,
        height,
        pInputFrame->pointerX,
        pInputFrame->pointerY);
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
}

void GameSession::setCurrentOutdoorWorldState(OutdoorWorldRuntime::Snapshot &&snapshot)
{
    m_currentOutdoorWorldState = std::move(snapshot);
}

const std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &GameSession::outdoorWorldStates() const
{
    return m_outdoorWorldStates;
}

std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &GameSession::outdoorWorldStates()
{
    return m_outdoorWorldStates;
}

void GameSession::storeOutdoorWorldState(const std::string &mapFileName, const OutdoorWorldRuntime::Snapshot &snapshot)
{
    m_outdoorWorldStates[mapFileName] = snapshot;
}

const std::optional<IndoorSceneRuntime::Snapshot> &GameSession::currentIndoorSceneState() const
{
    return m_currentIndoorSceneState;
}

void GameSession::setCurrentIndoorSceneState(const IndoorSceneRuntime::Snapshot &snapshot)
{
    m_currentIndoorSceneState = snapshot;
}

void GameSession::setCurrentIndoorSceneState(IndoorSceneRuntime::Snapshot &&snapshot)
{
    m_currentIndoorSceneState = std::move(snapshot);
}

const std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &GameSession::indoorSceneStates() const
{
    return m_indoorSceneStates;
}

std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &GameSession::indoorSceneStates()
{
    return m_indoorSceneStates;
}

void GameSession::storeIndoorSceneState(const std::string &mapFileName, const IndoorSceneRuntime::Snapshot &snapshot)
{
    m_indoorSceneStates[mapFileName] = snapshot;
}

void GameSession::setOutdoorCameraAngles(float yawRadians, float pitchRadians)
{
    m_outdoorCameraYawRadians = yawRadians;
    m_outdoorCameraPitchRadians = pitchRadians;
}

float GameSession::outdoorCameraYawRadians() const
{
    return m_outdoorCameraYawRadians;
}

float GameSession::outdoorCameraPitchRadians() const
{
    return m_outdoorCameraPitchRadians;
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
    m_outdoorPartyState = partySnapshot;
    m_currentOutdoorWorldState = worldSnapshot;
    m_outdoorWorldStates[mapFileName] = worldSnapshot;
    m_outdoorCameraYawRadians = yawRadians;
    m_outdoorCameraPitchRadians = pitchRadians;
}

void GameSession::captureIndoorRuntimeState(
    const std::string &mapFileName,
    const Party &party,
    const IndoorSceneRuntime::Snapshot &snapshot)
{
    m_currentSceneKind = SceneKind::Indoor;
    m_currentMapFileName = mapFileName;
    m_partyState = party;
    m_currentIndoorSceneState = snapshot;
    m_indoorSceneStates[mapFileName] = snapshot;
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

    if (m_outdoorPartyState && m_currentOutdoorWorldState)
    {
        saveData.hasOutdoorRuntimeState = true;
        saveData.outdoorParty = *m_outdoorPartyState;
        saveData.outdoorWorld = *m_currentOutdoorWorldState;
        saveData.savedGameMinutes = m_currentOutdoorWorldState->gameMinutes;
    }

    saveData.outdoorWorldStates = m_outdoorWorldStates;

    if (m_currentIndoorSceneState)
    {
        saveData.hasIndoorSceneState = true;
        saveData.indoorScene = *m_currentIndoorSceneState;
    }

    saveData.indoorSceneStates = m_indoorSceneStates;
    saveData.outdoorCameraYawRadians = m_outdoorCameraYawRadians;
    saveData.outdoorCameraPitchRadians = m_outdoorCameraPitchRadians;
    return saveData;
}

void GameSession::restoreFromSaveData(const GameSaveData &saveData)
{
    m_partyState = buildConfiguredParty(saveData.party, data());
    m_currentSceneKind = saveData.currentSceneKind;
    m_currentMapFileName = saveData.mapFileName;
    m_outdoorPartyState = saveData.hasOutdoorRuntimeState
        ? std::optional<OutdoorPartyRuntime::Snapshot>(saveData.outdoorParty)
        : std::nullopt;
    m_currentOutdoorWorldState = saveData.hasOutdoorRuntimeState
        ? std::optional<OutdoorWorldRuntime::Snapshot>(saveData.outdoorWorld)
        : std::nullopt;
    m_outdoorWorldStates = saveData.outdoorWorldStates;

    if (saveData.hasOutdoorRuntimeState && m_currentSceneKind == SceneKind::Outdoor)
    {
        m_outdoorWorldStates[m_currentMapFileName] = saveData.outdoorWorld;
    }

    m_currentIndoorSceneState = saveData.hasIndoorSceneState
        ? std::optional<IndoorSceneRuntime::Snapshot>(saveData.indoorScene)
        : std::nullopt;
    m_indoorSceneStates = saveData.indoorSceneStates;

    if (saveData.hasIndoorSceneState && m_currentSceneKind == SceneKind::Indoor)
    {
        m_indoorSceneStates[m_currentMapFileName] = saveData.indoorScene;
    }

    m_outdoorCameraYawRadians = saveData.outdoorCameraYawRadians;
    m_outdoorCameraPitchRadians = saveData.outdoorCameraPitchRadians;
    m_pendingMapMove.reset();
}
}
