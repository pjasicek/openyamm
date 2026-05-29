#pragma once

#include "game/app/AppMode.h"
#include "game/app/GameInputSystem.h"
#include "game/app/GameSettings.h"
#include "game/app/GameSession.h"
#include "engine/ApplicationConfig.h"
#include "engine/EngineApplication.h"
#include "game/gameplay/GameplayController.h"
#include "game/data/GameDataRepository.h"
#include "game/data/GameDataLoader.h"
#include "game/audio/GameAudioSystem.h"
#include "game/events/EventRuntime.h"
#include "game/indoor/IndoorRenderer.h"
#include "game/indoor/IndoorGameView.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/app/ScreenManager.h"
#include "game/content/ContentManifest.h"
#include "game/debug/DebugConsole.h"
#include "game/debug/GameImGuiBgfxRenderer.h"
#include "game/maps/SaveGame.h"
#include "game/mm9/Mm9DialoguePackage.h"
#include "game/scene/IMapSceneRuntime.h"
#include "game/ui/screens/LoadingOverlayScreen.h"

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class HeadlessGameplayDiagnostics;
struct ScenarioGameApplicationAccess;
struct GameApplicationTestAccess;
struct WinGameCertificate;

class GameApplication
{
public:
    explicit GameApplication(const Engine::ApplicationConfig &config);

    int run();

private:
    struct DebugMapJumpStart
    {
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        int32_t directionYawUnits = 0;
    };

    struct MapStartDestination
    {
        std::string mapFileName;
        std::optional<DebugMapJumpStart> start;
    };

    struct PendingDebugMapJump
    {
        int mapId = 0;
        std::optional<DebugMapJumpStart> start;
        bool nativeMm9Dat = false;
    };

    struct GameplayTraceMovementSnapshot
    {
        std::string mapName;
        bool indoor = false;
        float partyX = 0.0f;
        float partyY = 0.0f;
        float partyZ = 0.0f;
        float yawRadians = 0.0f;
        float pitchRadians = 0.0f;
        float gameMinutes = 0.0f;
        uint64_t tickMilliseconds = 0;
        bool forwardHeld = false;
        bool runWalkModifierHeld = false;
        bool turboHeld = false;
        bool shiftHeld = false;
        bool ctrlHeld = false;
        bool altHeld = false;
        bool heldItemActive = false;
        uint32_t heldItemId = 0;
        bool outdoorRunning = false;
        bool outdoorFlying = false;
        bool outdoorWaterWalk = false;
        bool outdoorFeatherFall = false;
        bool outdoorAirborne = false;
        uint32_t outdoorSupportKind = 0;
        size_t outdoorSupportBModelIndex = 0;
        size_t outdoorSupportFaceIndex = 0;
        bool indoorGrounded = false;
        int16_t indoorSectorId = -1;
        int16_t indoorEyeSectorId = -1;
        size_t indoorSupportFaceIndex = static_cast<size_t>(-1);
    };

    struct GameplayTraceMovementCapture
    {
        bool armed = false;
        bool hasStart = false;
        bool hasStop = false;
        bool committed = false;
        bool previousForwardHeld = false;
        uint32_t sequence = 0;
        GameplayTraceMovementSnapshot start;
        GameplayTraceMovementSnapshot stop;
    };

    struct FramePerformanceDiagnostics
    {
        uint64_t frames = 0;
        uint64_t totalNanoseconds = 0;
        uint64_t pendingDebugMapJumpNanoseconds = 0;
        uint64_t debugConsoleBeginNanoseconds = 0;
        uint64_t inputNanoseconds = 0;
        uint64_t activeScreenNanoseconds = 0;
        uint64_t pendingStateNanoseconds = 0;
        uint64_t gameplayUpdateNanoseconds = 0;
        uint64_t worldUpdateNanoseconds = 0;
        uint64_t renderWorldNanoseconds = 0;
        uint64_t renderGameplayUiNanoseconds = 0;
        uint64_t audioNanoseconds = 0;
        uint64_t postWorldNanoseconds = 0;
        uint64_t debugConsoleRenderNanoseconds = 0;
        uint64_t activeScreenFrames = 0;
        uint64_t gameplayWorldFrames = 0;

        bool hasActivity() const
        {
            return frames != 0;
        }
    };

    friend class HeadlessGameplayDiagnostics;
    friend struct ScenarioGameApplicationAccess;
    friend struct GameApplicationTestAccess;

    bool loadGameData(Engine::AssetFileSystem &assetFileSystem);
    bool ensureCommonGameDataLoaded();
    void updateDeferredStartupLoads();
    void updateDeferredMainMenuChildWarmup();
    void shutdownApplication();
    bool initializeSelectedMapRuntime(bool initializeView);
    bool ensureMm9DialoguePackageLoaded(std::string &errorMessage);
    bool initializeRenderer();
    bool initializeDebugConsoleRenderer();
    void shutdownDebugConsoleRenderer();
    void configureDebugConsoleStyle();
    void registerDebugConsoleCommands();
    void updateDebugConsoleDataOptions();
    void beginDebugConsoleFrame();
    void renderDebugConsoleFrame(int width, int height);
    bool processPendingDebugMapJump();
    bool initializeNativeMm9DatSceneRuntime(const MapAssetInfo &selectedMap, std::string &errorMessage);
    void shutdownRenderer();
    Party &ensureSessionPartyState();
    void bindPartyDependencies(Party &party) const;
    void synchronizeSessionFromRuntime();
    void synchronizeActiveReputationToParty();
    bool loadCurrentSessionMap(
        bool initializeView,
        const std::function<void(int)> &progressCallback = {});
    bool activateWorldForMap(const MapStatsEntry &map);
    bool activateWorldForMapFileName(const std::string &mapFileName);
    bool applyCurrentSessionToRuntime(bool initializeView);
    bool processPendingMapMove();
    bool processPendingWinGame();
    bool processPendingEventMovie();
    bool processPendingReturnToMainMenu();
    bool processPendingDimensionDoorOverlay();
    bool executeCurrentMapOnLeaveEvents();
    bool processPendingPartyDefeat();
    void handleCompletedPartyDefeatScreen();
    void handleCompletedEventMovieScreen();
    void handleCompletedWinGameScreen();
    WinGameCertificate buildWinGameCertificate() const;
    bool shouldTriggerPartyDefeat() const;
    MapStartDestination resolveStartupDestination() const;
    std::optional<MapStartDestination> resolveContinentStartDestination(uint32_t continentId) const;
    std::optional<uint32_t> activeWorldContinentId() const;
    void applyMapStartDestination(const MapStartDestination &destination);
    std::string resolvePartyDefeatRespawnMapFileName() const;
    MapStartDestination resolvePartyDefeatRespawnDestination() const;
    std::string resolvePartyDefeatCutsceneStem() const;
    void applyPartyDefeatConsequences();
    bool respawnPartyAfterDefeat(bool initializeView);
    void captureCurrentSceneState();
    void restoreSavedOutdoorWorldStateForSelectedMap();
    void updateQuickSaveInput();
    void updateDoubleSpeedInput();
    float gameplayDeltaSeconds(float deltaSeconds) const;
    void updateGameplayTraceSnapshotHotkeys();
    bool processPendingQuickSaveInput();
    bool quickSave();
    bool quickLoad();
    bool quickSaveToPath(
        const std::filesystem::path &path,
        const std::string &saveName = "",
        const std::vector<uint8_t> &previewBmp = {});
    bool quickLoadFromPath(const std::filesystem::path &path, bool initializeView);
    void openMainMenuScreen();
    void openLoadGameScreen(bool returnToGameplayMenu = false, const std::string &source = "main_menu");
    void openNewGameScreen(const std::string &source = "main_menu");
    bool processPendingArcomageGame();
    void handleCompletedArcomageScreen();
    bool initializeStartupSession(bool initializeView);
    std::string resolveStartupMapFile() const;
    bool startNewSession(std::optional<uint32_t> rosterId, bool initializeView = true);
    bool startNewSessionFromCharacterCreation(const std::vector<Character> &characters, bool initializeView = true);
    bool startNewSessionFromCharacterCreation(
        const std::vector<Character> &characters,
        uint32_t continentId,
        bool initializeView);
    bool loadSessionFromPath(const std::filesystem::path &path);
    void beginLoadingOverlay(
        LoadingOverlayScreen::Presentation presentation = LoadingOverlayScreen::Presentation::Fullscreen);
    void renderLoadingOverlayProgress(int progressPercent);
    void pumpLoadingOverlayAnimation();
    void completeLoadingOverlay();
    void cancelLoadingOverlay();
    void closeTransientGameplayUiForMapMove();
    std::filesystem::path settingsFilePath() const;
    void loadOrCreateSettings();
    void applyCurrentSettingsToActiveRuntime();
    void applyStartupDebugSettingsToActiveRuntime();
    bool initializeMm9NewGameStateIfNeeded();
    void requestApplicationQuit() const;
    void reportQuickSaveStatus(const std::string &status);
    void handleSdlEvent(const SDL_Event &event);
    bool handlePendingInputPromptSdlEvent(const SDL_Event &event);
    bool pendingInputPromptActive() const;
    bool applicationTextInputActive() const;
    void clearPendingInputPromptUi(bool clearStatusBar);
    void updatePendingInputPrompt();
    void finishPendingInputPrompt(bool accepted);
    void presentPendingInputPromptDialogResult(size_t previousMessageCount);
    std::vector<std::string> resolvePendingInputAnswers(
        const EventRuntimeState::PendingInputPrompt &prompt) const;
    void renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds);
    void logFramePerformanceDiagnostics(uint32_t currentTick);

    Engine::ApplicationConfig m_config;
    Engine::EngineApplication m_engineApplication;
    GameDataLoader m_gameDataLoader;
    GameDataRepository m_gameDataRepository;
    WorldManifest m_activeWorldManifest;
    GameAudioSystem m_gameAudioSystem;
    GameSession m_gameSession;
    GameInputSystem m_gameInputSystem;
    IndoorRenderer m_indoorRenderer;
    IndoorGameView m_indoorGameView;
    OutdoorGameView m_outdoorGameView;
    std::optional<Mm9DialoguePackage> m_mm9DialoguePackage;
    ScreenManager m_screenManager;
    GameSettings m_settings = GameSettings::createDefault();
    GameplayController m_gameplayController;
    std::unique_ptr<OutdoorPartyRuntime> m_pOutdoorPartyRuntime;
    std::unique_ptr<OutdoorWorldRuntime> m_pOutdoorWorldRuntime;
    std::unique_ptr<IMapSceneRuntime> m_pMapSceneRuntime;
    Engine::AssetFileSystem *m_pAssetFileSystem;
    bool m_quickSaveLatch = false;
    bool m_quickLoadLatch = false;
    bool m_doubleSpeedActive = false;
    bool m_advanceTimeLatch = false;
    bool m_traceSnapshotStartLatch = false;
    bool m_traceSnapshotEndLatch = false;
    bool m_traceMarkerLatch = false;
    uint32_t m_traceMarkerSequence = 0;
    bool m_traceSessionHeaderLogged = false;
    GameplayTraceMovementCapture m_traceMovementCapture = {};
    bool m_pendingQuickSave = false;
    bool m_pendingQuickLoad = false;
    bool m_pendingAdvanceTime = false;
    bool m_bootSeededDwiOnNextRendererInit = false;
    bool m_commonGameDataLoaded = false;
    bool m_commonGameDataLoadFailed = false;
    bool m_deferredCommonGameDataLoadPending = false;
    uint32_t m_mainMenuRenderedFrameCount = 0;
    uint8_t m_deferredMainMenuChildWarmupStage = 0;
    std::unique_ptr<LoadingOverlayScreen> m_pLoadingOverlayScreen;
    std::string m_loadingOverlayBackgroundTextureName;
    LoadingOverlayScreen::Presentation m_loadingOverlayPresentation = LoadingOverlayScreen::Presentation::Fullscreen;
    bool m_loadingOverlayActive = false;
    int m_loadingOverlayCurrentProgressPercent = 0;
    uint64_t m_loadingOverlayNextAnimationFrameTick = 0;
    bool m_mainMenuChildScreensPrepared = false;
    int m_lastFrameWidth = 640;
    int m_lastFrameHeight = 480;
    std::optional<std::string> m_pendingPartyDefeatRespawnMapFileName;
    std::optional<DebugMapJumpStart> m_pendingPartyDefeatRespawnStart;
    bool m_pendingWinGameCertificateAfterMovie = false;
    std::string m_pendingInputText;
    std::string m_pendingInputStatusText;
    bool m_pendingInputTextActive = false;
    bool m_skipGameplayUpdateUntilPromptSubmitKeysReleased = false;
    bool m_loadingSavedGameRuntime = false;
    FramePerformanceDiagnostics m_framePerformanceDiagnostics;
    uint32_t m_lastFramePerformanceLogTick = 0;
    DebugConsole m_debugConsole;
    GameImGuiBgfxRenderer m_debugConsoleRenderer;
    bool m_debugConsoleRendererInitialized = false;
    bool m_debugConsoleFrameBegun = false;
    bool m_debugConsoleCommandsRegistered = false;
    std::optional<PendingDebugMapJump> m_pendingDebugMapJump;
};
}
