#pragma once

#include "game/events/EventRuntime.h"
#include "game/app/GameSettings.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayInputController.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/maps/SaveGame.h"
#include "game/scene/SceneKind.h"
#include "game/data/GameDataRepository.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayUiRuntime.h"

#include <SDL3/SDL.h>

#include <array>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
struct GameplayInputFrame;
struct Mm9DialoguePackage;

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
    float gameMinutes() const;
    void setGameMinutes(float gameMinutes);

    GameplayUiController &gameplayUiController();
    const GameplayUiController &gameplayUiController() const;
    GameplayScreenState &gameplayScreenState();
    const GameplayScreenState &gameplayScreenState() const;
    GameplayUiRuntime &gameplayUiRuntime();
    const GameplayUiRuntime &gameplayUiRuntime() const;
    GameplayActorService &gameplayActorService();
    const GameplayActorService &gameplayActorService() const;
    GameplayCombatController &gameplayCombatController();
    const GameplayCombatController &gameplayCombatController() const;
    GameplayItemService &gameplayItemService();
    const GameplayItemService &gameplayItemService() const;
    GameplayProjectileService &gameplayProjectileService();
    const GameplayProjectileService &gameplayProjectileService() const;
    GameplayFxService &gameplayFxService();
    const GameplayFxService &gameplayFxService() const;
    GameplaySpellService &gameplaySpellService();
    const GameplaySpellService &gameplaySpellService() const;
    TurnBasedCombatRuntime &turnBasedCombatRuntime();
    const TurnBasedCombatRuntime &turnBasedCombatRuntime() const;
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
    const GameplayInputFrame *currentGameplayInputFrame() const;
    void bindCurrentGameplayInputFrame(const GameplayInputFrame *pInputFrame);
    void updateGameplay(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool collectPerformanceDiagnostics = false);
    void clearSharedInputFrameResult();
    void consumePendingGameplayAudioRequests();
    void renderGameplayUi(int width, int height);
    const GameplaySharedInputFrameResult &sharedInputFrameResult() const;
    bool sharedWorldInteractionBlockedThisFrame() const;
    void requestRelativeMouseMotionReset();
    bool consumeRelativeMouseMotionResetRequest();

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
    void clearMapRuntimeState(const std::string &mapFileName, const std::string &canonicalId);

    const std::unordered_map<std::string, int32_t> &namedGlobalVars() const;
    int32_t namedGlobalVar(const std::string &name, int32_t defaultValue = 0) const;
    void setNamedGlobalVar(const std::string &name, int32_t value);
    void clearNamedGlobalVar(const std::string &name);
    void mergeNamedGlobalVarsFromRuntime(const EventRuntimeState &runtimeState);
    void applyNamedGlobalVarsToRuntime(EventRuntimeState &runtimeState) const;
    const Mm9ScriptRuntimeState &mm9ScriptState() const;
    void initializeMm9ScriptState(const Mm9DialoguePackage &package);
    void setMm9ScriptState(const Mm9ScriptRuntimeState &state);
    void clearMm9ScriptState();

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
    struct GameplayUpdatePerformanceDiagnostics
    {
        uint64_t frames = 0;
        uint64_t activeWorldFrames = 0;
        uint64_t actorAiFrames = 0;
        uint64_t totalNanoseconds = 0;
        uint64_t sharedFrameStateNanoseconds = 0;
        uint64_t worldInteractionStateNanoseconds = 0;
        uint64_t activeMemberSyncNanoseconds = 0;
        uint64_t sharedInputNanoseconds = 0;
        uint64_t worldMovementNanoseconds = 0;
        uint64_t actorAiNanoseconds = 0;
        uint64_t combatEventsNanoseconds = 0;
        uint64_t interactionFrameNanoseconds = 0;
        uint64_t projectileAndCooldownNanoseconds = 0;
        uint64_t preloadNanoseconds = 0;

        bool hasActivity() const
        {
            return frames != 0;
        }
    };

    struct TurnBasedFrameTraceState
    {
        bool active = false;
        uint32_t lastLogTick = 0;
        TurnBasedCombatStage stage = TurnBasedCombatStage::None;
        bool actorAiUpdate = false;
        bool gameplayPaused = false;
        bool allowMoveInput = false;
        bool cursorMode = false;
        bool modalBlocked = false;
        bool pendingSpellTarget = false;
        bool sharedWorldBlocked = false;
        int movementActionPoints = 0;
        int pendingActions = 0;
    };

    void logGameplayUpdatePerformanceDiagnostics(uint32_t currentTick) const;
    void logTurnBasedFrameTraceIfNeeded(
        bool actorAiUpdate,
        bool gameplayPaused,
        bool allowMoveInput,
        bool movementStep,
        bool cursorMode,
        bool modalBlocked,
        bool pendingSpellTarget,
        bool sharedWorldBlocked,
        float movementDeltaSeconds,
        float frameDeltaSeconds);

    const GameDataRepository *m_pDataRepository = nullptr;
    std::optional<Party> m_partyState;
    SceneKind m_currentSceneKind = SceneKind::Outdoor;
    std::string m_currentMapFileName;
    GameplayScreenState m_gameplayScreenState;
    GameplayUiController m_gameplayUiController;
    GameplayUiRuntime m_gameplayUiRuntime;
    GameplayActorService m_gameplayActorService;
    GameplayCombatController m_gameplayCombatController;
    GameplayItemService m_gameplayItemService;
    GameplayProjectileService m_gameplayProjectileService;
    GameplayFxService m_gameplayFxService;
    GameplaySpellService m_gameplaySpellService;
    TurnBasedCombatRuntime m_turnBasedCombatRuntime;
    size_t m_turnBasedPendingWorldActions = 0;
    GameplayScreenRuntime m_gameplayScreenRuntime;
    GameplayDialogController m_gameplayDialogController;
    GameplayOverlayInteractionState m_overlayInteractionState;
    std::array<uint8_t, SDL_SCANCODE_COUNT> m_previousKeyboardState = {};
    IGameplayWorldRuntime *m_pActiveWorldRuntime = nullptr;
    const GameplayInputFrame *m_pCurrentGameplayInputFrame = nullptr;
    GameplaySharedInputFrameResult m_sharedInputFrameResult = {};
    bool m_sharedWorldInteractionBlockedThisFrame = false;
    bool m_relativeMouseMotionResetRequested = false;
    std::optional<OutdoorPartyRuntime::Snapshot> m_outdoorPartyState;
    std::optional<OutdoorWorldRuntime::Snapshot> m_currentOutdoorWorldState;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> m_outdoorWorldStates;
    std::optional<IndoorSceneRuntime::Snapshot> m_currentIndoorSceneState;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> m_indoorSceneStates;
    std::unordered_map<std::string, int32_t> m_namedGlobalVars;
    Mm9ScriptRuntimeState m_mm9ScriptState;
    float m_gameMinutes = 9.0f * 60.0f;
    float m_outdoorCameraYawRadians = 0.0f;
    float m_outdoorCameraPitchRadians = 0.0f;
    std::optional<std::filesystem::path> m_currentSavePath;
    std::optional<EventRuntimeState::PendingMapMove> m_pendingMapMove;
    SaveGameToPathCallback m_saveGameToPathCallback;
    SettingsChangedCallback m_settingsChangedCallback;
    mutable GameplayUpdatePerformanceDiagnostics m_gameplayUpdatePerformanceDiagnostics;
    mutable uint32_t m_lastGameplayUpdatePerformanceLogTick = 0;
    TurnBasedFrameTraceState m_turnBasedFrameTraceState;
};
}
