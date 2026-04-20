#pragma once

#include "game/events/EventRuntime.h"
#include "game/app/GameSettings.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/maps/SaveGame.h"
#include "game/scene/SceneKind.h"
#include "game/data/GameDataRepository.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayUiRuntime.h"

#include <SDL3/SDL.h>

#include <array>
#include <filesystem>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
class GameSession
{
public:
    GameSession();

    using SaveGameToPathCallback = std::function<bool(
        const std::filesystem::path &,
        const std::string &,
        const std::vector<uint8_t> &,
        std::string &)>;
    using SettingsChangedCallback = std::function<void(const GameSettings &)>;

    void clear();
    void bindDataRepository(const GameDataRepository *pDataRepository);
    bool hasDataRepository() const;
    const GameDataRepository &data() const;

    const std::optional<Party> &partyState() const;
    std::optional<Party> &partyState();
    void setPartyState(const Party &party);
    void setPartyState(Party &&party);

    SceneKind currentSceneKind() const;
    void setCurrentSceneKind(SceneKind sceneKind);

    bool hasCurrentMapFileName() const;
    const std::string &currentMapFileName() const;
    void setCurrentMapFileName(const std::string &mapFileName);
    void setCurrentMapFileName(std::string &&mapFileName);

    GameplayUiController &gameplayUiController();
    const GameplayUiController &gameplayUiController() const;
    GameplayUiRuntime &gameplayUiRuntime();
    const GameplayUiRuntime &gameplayUiRuntime() const;
    GameplayScreenRuntime &gameplayScreenRuntime();
    const GameplayScreenRuntime &gameplayScreenRuntime() const;
    GameplayDialogController &gameplayDialogController();
    const GameplayDialogController &gameplayDialogController() const;
    GameplayOverlayInteractionState &overlayInteractionState();
    const GameplayOverlayInteractionState &overlayInteractionState() const;
    std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState();
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState() const;

    IGameplayWorldRuntime *activeWorldRuntime() const;
    void bindActiveWorldRuntime(IGameplayWorldRuntime *pWorldRuntime);

    const std::optional<OutdoorPartyRuntime::Snapshot> &outdoorPartyState() const;
    void setOutdoorPartyState(const OutdoorPartyRuntime::Snapshot &snapshot);
    void setOutdoorPartyState(OutdoorPartyRuntime::Snapshot &&snapshot);

    const std::optional<OutdoorWorldRuntime::Snapshot> &currentOutdoorWorldState() const;
    void setCurrentOutdoorWorldState(const OutdoorWorldRuntime::Snapshot &snapshot);
    void setCurrentOutdoorWorldState(OutdoorWorldRuntime::Snapshot &&snapshot);

    const std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &outdoorWorldStates() const;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &outdoorWorldStates();
    void storeOutdoorWorldState(const std::string &mapFileName, const OutdoorWorldRuntime::Snapshot &snapshot);

    const std::optional<IndoorSceneRuntime::Snapshot> &currentIndoorSceneState() const;
    void setCurrentIndoorSceneState(const IndoorSceneRuntime::Snapshot &snapshot);
    void setCurrentIndoorSceneState(IndoorSceneRuntime::Snapshot &&snapshot);

    const std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &indoorSceneStates() const;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &indoorSceneStates();
    void storeIndoorSceneState(const std::string &mapFileName, const IndoorSceneRuntime::Snapshot &snapshot);

    void setOutdoorCameraAngles(float yawRadians, float pitchRadians);
    float outdoorCameraYawRadians() const;
    float outdoorCameraPitchRadians() const;

    const std::optional<std::filesystem::path> &currentSavePath() const;
    void setCurrentSavePath(const std::filesystem::path &path);
    void clearCurrentSavePath();

    const std::optional<EventRuntimeState::PendingMapMove> &pendingMapMove() const;
    void setPendingMapMove(const EventRuntimeState::PendingMapMove &pendingMapMove);
    void setPendingMapMove(EventRuntimeState::PendingMapMove &&pendingMapMove);
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove();
    void clearPendingMapMove();

    void setSaveGameToPathCallback(SaveGameToPathCallback callback);
    bool canSaveGameToPath() const;
    bool saveGameToPath(
        const std::filesystem::path &path,
        const std::string &saveName,
        const std::vector<uint8_t> &previewBmp,
        std::string &error) const;

    void setSettingsChangedCallback(SettingsChangedCallback callback);
    void notifySettingsChanged(const GameSettings &settings) const;

    void requestOpenNewGameScreen();
    void requestOpenLoadGameScreen();
    bool consumePendingOpenNewGameScreenRequest();
    bool consumePendingOpenLoadGameScreenRequest();

    void captureOutdoorRuntimeState(
        const std::string &mapFileName,
        const Party &party,
        const OutdoorPartyRuntime::Snapshot &partySnapshot,
        const OutdoorWorldRuntime::Snapshot &worldSnapshot,
        float yawRadians,
        float pitchRadians
    );

    void captureIndoorRuntimeState(
        const std::string &mapFileName,
        const Party &party,
        const IndoorSceneRuntime::Snapshot &snapshot
    );

    std::optional<GameSaveData> buildSaveData() const;
    void restoreFromSaveData(const GameSaveData &saveData);

private:
    const GameDataRepository *m_pDataRepository = nullptr;
    std::optional<Party> m_partyState;
    SceneKind m_currentSceneKind = SceneKind::Outdoor;
    std::string m_currentMapFileName;
    GameplayUiController m_gameplayUiController;
    GameplayUiRuntime m_gameplayUiRuntime;
    GameplayScreenRuntime m_gameplayScreenRuntime;
    GameplayDialogController m_gameplayDialogController;
    GameplayOverlayInteractionState m_overlayInteractionState;
    std::array<uint8_t, SDL_SCANCODE_COUNT> m_previousKeyboardState = {};
    IGameplayWorldRuntime *m_pActiveWorldRuntime = nullptr;
    std::optional<OutdoorPartyRuntime::Snapshot> m_outdoorPartyState;
    std::optional<OutdoorWorldRuntime::Snapshot> m_currentOutdoorWorldState;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> m_outdoorWorldStates;
    std::optional<IndoorSceneRuntime::Snapshot> m_currentIndoorSceneState;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> m_indoorSceneStates;
    float m_outdoorCameraYawRadians = 0.0f;
    float m_outdoorCameraPitchRadians = 0.0f;
    std::optional<std::filesystem::path> m_currentSavePath;
    std::optional<EventRuntimeState::PendingMapMove> m_pendingMapMove;
    SaveGameToPathCallback m_saveGameToPathCallback;
    SettingsChangedCallback m_settingsChangedCallback;
    bool m_pendingOpenNewGameScreen = false;
    bool m_pendingOpenLoadGameScreen = false;
};
}
