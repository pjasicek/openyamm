#pragma once

#include "game/app/AppMode.h"
#include "game/render/ActorModelPreview.h"
#include "game/render/CinematicGrading.h"
#include "game/app/GameInputSystem.h"
#include "game/app/GameSettings.h"
#include "game/app/GameUpdater.h"
#include "game/app/NewGameOptions.h"
#include "game/app/GameSession.h"
#include "engine/ApplicationConfig.h"
#include "engine/EngineApplication.h"
#include "game/gameplay/ActorBehaviorCatalog.h"
#include "game/gameplay/GameplayController.h"
#include "game/data/GameDataRepository.h"
#include "game/data/GameDataLoader.h"
#include "game/audio/GameAudioSystem.h"
#include "game/audio/WorldAmbientSounds.h"
#include "game/events/EventRuntime.h"
#include "game/indoor/IndoorRenderer.h"
#include "game/indoor/IndoorGameView.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/app/ScreenManager.h"
#include "game/content/CompletionCertificates.h"
#include "game/content/ContentManifest.h"
#include "game/debug/AiArena.h"
#include "game/debug/DebugConsole.h"
#include "game/debug/GameImGuiBgfxRenderer.h"
#include "game/debug/ScreenshotCaptureService.h"
#include "game/debug/ScreenshotTour.h"
#include "game/debug/MenuInputTour.h"
#include "game/maps/SaveGame.h"
#include "game/scene/IMapSceneRuntime.h"
#include "game/ui/screens/LoadGameScreen.h"
#include "game/ui/screens/LoadingOverlayScreen.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
class HeadlessGameplayDiagnostics;
struct MawTestPartyCatalog;
struct ScenarioGameApplicationAccess;
struct GameApplicationTestAccess;

class GameApplication
{
public:
    explicit GameApplication(const Engine::ApplicationConfig &config);

    int run();

private:
  MenuInputTour m_menuInputTour;
  std::vector<uint8_t> m_menuSavePreviewBmp;
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

    enum class ScreenshotTourStage
    {
        NotStarted,
        Settling,
        WaitingForCapture,
        Finished,
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
        uint64_t performanceTraceLogNanoseconds = 0;
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
    // Loads the common data under this ruleset's tables when they are not the loaded ones. Tear the session down
    // first: the reload replaces the tables that runtimes and screens point into.
    bool activateRuleset(const std::string &rulesetId, std::string &error);
    // The pause menu's Rules tab: what the ruleset lets change mid-game.
    bool applyRulesetOptions(const RulesetOptions &options, std::string &error);
    void updateDeferredStartupLoads();
    // The active scene's (outdoor or indoor) effects and actor models.
    WorldFxSystem &activeWorldFxSystem();
    // Builds the active map's actor model bindings on first use and poses the actor models for this frame; false
    // (application quitting) when a model the map needs fails to load.
    bool syncActorModels(IGameplayWorldRuntime &world, float deltaSeconds, float liveDeltaSeconds);
    void updateDeferredMainMenuChildWarmup();
    void shutdownApplication();
    bool initializeSelectedMapRuntime(bool initializeView);
    const ActorBehaviorCatalog *reloadActorBehaviorCatalog();
    bool initializeRenderer();
    bool initializeDebugConsoleRenderer();
    void shutdownDebugConsoleRenderer();
    void configureDebugConsoleStyle();
    void registerDebugConsoleCommands();
    void updateDebugConsoleDataOptions();
    void beginDebugConsoleFrame();
    void renderDebugConsoleFrame(int width, int height);
    // The indoor portal debug view (console `portals`): its per-second averages, the readout and the sector labels in
    // the ImGui pass, and the `[PortalView]` log line. Returns whether it drew anything.
    bool renderIndoorPortalDebugReadout(int width, int height);
    void applyIndoorPortalDebugSettings(const IndoorPortalDebugSettings &settings);
    bool processPendingDebugMapJump();
    // The debug console's `testparty`: a new MAW game with a test party (game/debug/MawTestParties.h).
    bool processPendingTestParty();
    bool loadMawTestPartyCatalog(MawTestPartyCatalog &catalog, std::string &error) const;
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
    bool requestAutosaveBeforeMapMove();
    bool activeViewSavePreviewCapturePending() const;
    bool processPendingCompletionCertificate();
    bool processPendingEventMovie();
    bool processPendingReturnToMainMenu();
    bool processPendingDimensionDoorOverlay();
    bool executeCurrentMapOnLeaveEvents();
    // What the party's rules do as it leaves the current map (MonsterRules::leaveMap).
    void applyRulesMapLeave();
    bool processPendingPartyDefeat();
    void handleCompletedPartyDefeatScreen();
    void handleCompletedEventMovieScreen();
    void handleCompletedWinGameScreen();
    void saveCompletionCertificateImage(
        const std::string &certificateId, const ScreenshotCaptureService::Region &region);
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
    // What saving costs in food at the party's place now (MAW from Nightmare), zero without a party.
    SaveFoodCost saveFoodCost();
    void openMainMenuScreen();
    void openMenuScreen(bool paused);
    void openPauseMenuScreen();
    void openSaveGameScreen();
    void resumeMenuGameplay();
    bool applyMenuSettings(const GameSettings &settings, bool persist, std::string &error);
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
        const NewGameOptions &options,
        bool initializeView);
    bool loadSessionFromPath(const std::filesystem::path &path);
    void beginLoadingOverlay(
        LoadingOverlayScreen::Presentation presentation = LoadingOverlayScreen::Presentation::Fullscreen);
    void drawLoadingOverlay();
    uint32_t renderLoadingOverlayProgress(int progressPercent);
    void prepareGameplayRendering();
    void pumpLoadingOverlayAnimation();
    void completeLoadingOverlay();
    void cancelLoadingOverlay();
    void closeTransientGameplayUiForMapMove();
    std::filesystem::path settingsFilePath() const;
    bool saveSettings(const GameSettings &settings, std::string &error) const;
    void loadOrCreateSettings();
    void applyCurrentSettingsToActiveRuntime();
    void applyStartupDebugSettingsToActiveRuntime();
    void requestApplicationQuit() const;
    void reportQuickSaveStatus(const std::string &status);
    // Writes the next rendered frame to screenshots/<local date and time>.png.
    void requestScreenshotFile();
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
    void updateScreenshotCaptureFrame();
    bool applyScreenshotTourShotPose(const ScreenshotTourShot &shot);
    // Sets up an AI arena on the current map (game/debug/AiArena.h): its map must be loaded. logPath: where the trace
    // log goes (empty: none).
    bool applyAiArena(const AiArena &arena, const std::filesystem::path &logPath, std::string &error);
    bool loadAndApplyAiArena(const std::filesystem::path &arenaPath, std::string &message);
    void runTourConsoleLine(const std::string &line, std::string_view logPrefix);
    bool advanceDebugGameMinutes(float minutes);
    bool setDebugClockMinute(int targetMinute);
    void advanceScreenshotTourAfterCapture(size_t shotIndex, bool success);
    bool logFramePerformanceDiagnostics(uint32_t currentTick);
    void logFrameHitchDiagnostics(const FramePerformanceDiagnostics &diagnostics) const;

    Engine::ApplicationConfig m_config;
    Engine::EngineApplication m_engineApplication;
    CinematicGrading m_cinematicGrading;
    ActorModelPreview m_actorModelPreview;
    GameDataLoader m_gameDataLoader;
    GameDataRepository m_gameDataRepository;
    WorldManifest m_activeWorldManifest;
    ActorBehaviorCatalog m_actorBehaviorCatalog;
    GameAudioSystem m_gameAudioSystem;
    WorldAmbientSoundRuntime m_worldAmbientSounds;
    GameSession m_gameSession;
    GameInputSystem m_gameInputSystem;
    SpriteAtlasCache m_spriteAtlasCache;
    NativeSpriteTextureCache m_nativeSpriteCache;
    IndoorRenderer m_indoorRenderer;
    IndoorGameView m_indoorGameView;
    OutdoorGameView m_outdoorGameView;
    ScreenManager m_screenManager;
    GameSettings m_settings = GameSettings::createDefault();
    GameplayController m_gameplayController;
    std::unique_ptr<OutdoorPartyRuntime> m_pOutdoorPartyRuntime;
    std::unique_ptr<OutdoorWorldRuntime> m_pOutdoorWorldRuntime;
    std::unique_ptr<IMapSceneRuntime> m_pMapSceneRuntime;
    Engine::AssetFileSystem *m_pAssetFileSystem;
    // Console `render` profiling switches: decoration-model foliage, and a frozen world (no actor/time updates) so a
    // view stays identical while layers are measured. Without the HUD, gameplay draws only the world (clean captures).
    bool m_renderFoliage = true;
    bool m_renderHud = true;
    bool m_renderInstancing = true;
    bool m_renderFreezeWorld = false;
    // The portal debug view's timings averaged over the last second, and the running sums of the current one.
    struct PortalDebugAverages
    {
        uint32_t frames = 0;
        std::array<uint64_t, 8> cpuNanoseconds = {};
        // GPU microseconds per bgfx view id, with the view names.
        std::vector<std::pair<std::string, uint64_t>> gpuViews;
        uint64_t gpuFrameMicroseconds = 0;
        uint64_t drawCalls = 0;
        uint64_t triangles = 0;
    };
    PortalDebugAverages m_portalDebugShown;
    PortalDebugAverages m_portalDebugSums;
    std::vector<uint64_t> m_portalDebugGpuSums;
    std::vector<std::string> m_portalDebugGpuNames;
    uint64_t m_portalDebugWindowStartTicks = 0;
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
    // When quick load last stopped to warn what loading costs now (MAW's pending Beyond Madness death); a second
    // press soon after loads.
    std::optional<uint64_t> m_quickLoadWarnedTicks;
    bool m_pendingAdvanceTime = false;
    bool m_bootSeededDwiOnNextRendererInit = false;
    bool m_commonGameDataLoaded = false;
    bool m_commonGameDataLoadFailed = false;
    bool m_deferredCommonGameDataLoadPending = false;
    uint32_t m_mainMenuRenderedFrameCount = 0;
    uint8_t m_deferredMainMenuChildWarmupStage = 0;
    std::unique_ptr<LoadingOverlayScreen> m_pLoadingOverlayScreen;
    // Monsters' own sounds (MonsterModifierSet::sounds): the loops while they move and the one-shot when they notice the
    // party, by actor id, for the world runtime they belong to.
    void syncActorSounds(IGameplayWorldRuntime &world);
    const IGameplayWorldRuntime *m_pActorSoundWorld = nullptr;
    std::unordered_map<uint32_t, uint64_t> m_actorLoopSounds;
    std::unordered_map<uint32_t, bool> m_actorAwareStates;
    // The map's ambience bed and music areas (world.yml ambience, musicAreas) and the track playing for its area.
    void startMapAmbienceAndMusic(const std::string &mapFileName, int mapMusicTrack);
    void updateMusicArea(float partyX, float partyY);
    const std::vector<WorldManifest::MusicArea> *m_mapMusicAreas = nullptr;
    int m_mapMusicTrack = 0;
    int m_areaMusicTrack = 0;
    std::string m_loadingOverlayBackgroundTextureName;
    LoadingOverlayScreen::Presentation m_loadingOverlayPresentation = LoadingOverlayScreen::Presentation::Fullscreen;
    bool m_loadingOverlayActive = false;
    bool m_loadingOverlayReadyToDismiss = false;
    int m_loadingOverlayCurrentProgressPercent = 0;
    uint64_t m_loadingOverlayNextAnimationFrameTick = 0;
    bool m_mainMenuChildScreensPrepared = false;
    // The Settings section the menu last showed; kept for the session only.
    std::string m_settingsMenuSection = "gameplay";
    // Null where the game does not update itself (development runs).
    std::unique_ptr<GameUpdater> m_pUpdater;
    int m_lastFrameWidth = 640;
    int m_lastFrameHeight = 480;
    std::optional<std::string> m_pendingPartyDefeatRespawnMapFileName;
    std::optional<DebugMapJumpStart> m_pendingPartyDefeatRespawnStart;
    std::vector<CompletionCertificateDefinition> m_completionCertificates;
    bool m_completionCertificatesLoaded = false;
    // Certificates earned at once (a world and the grand one), shown one after another.
    std::vector<std::string> m_pendingCompletionCertificateIds;
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
    // The arguments of a `testparty` that starts a new game, run at the start of the next frame.
    std::optional<std::vector<std::string>> m_pendingTestParty;
    // A map move held for a few frames while the leaving map's autosave captures its preview.
    std::optional<EventRuntimeState::PendingMapMove> m_mapMoveAwaitingAutosave;
    std::vector<EffectHandle> m_debugEffectHandles;
    std::vector<Engine::ModelInstanceHandle> m_debugModelHandles;
    ScreenshotCaptureService m_screenshotCaptureService;
    std::optional<ScreenshotTour> m_screenshotTour;
    ScreenshotTourStage m_screenshotTourStage = ScreenshotTourStage::NotStarted;
    size_t m_screenshotTourShotIndex = 0;
    uint64_t m_screenshotTourSettleStartTicks = 0;
    bool m_screenshotTourLoadFailed = false;
    bool m_debugLaunchEffectSpawned = false;
    bool m_debugLaunchEffectStatsLogged = false;
    bool m_debugLaunchModelSpawned = false;
    bool m_debugLaunchActorsSpawned = false;
    bool m_debugLaunchAiArenaApplied = false;
    // The AI arena in play (console `arena`, debug.ai_arena_path, scenario ai_arena) and its decision trace, which the
    // active world runtime is bound to.
    std::optional<AiArena> m_aiArena;
    std::vector<size_t> m_aiArenaActorIndices;
    ActorAiTrace m_aiArenaTrace;
    // Delayed captures requested so far (debug.screenshot_path, screenshot_burst_count).
    uint32_t m_screenshotScheduledCaptures = 0;
    bool m_screenshotGameplayStartTicksValid = false;
    uint64_t m_screenshotGameplayStartTicks = 0;
};
}
