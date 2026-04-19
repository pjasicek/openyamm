#include "game/app/GameSession.h"

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
}

void GameSession::bindDataRepository(const GameDataRepository *pDataRepository)
{
    m_pDataRepository = pDataRepository;
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
    m_gameplayUiController.clearRuntimeState();
    m_overlayInteractionState = {};
    m_previousKeyboardState.fill(0);
    m_pActiveWorldRuntime = nullptr;
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
