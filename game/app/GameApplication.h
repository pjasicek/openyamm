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
#include "game/indoor/IndoorRenderer.h"
#include "game/indoor/IndoorGameView.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/app/ScreenManager.h"
#include "game/maps/SaveGame.h"
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
struct GameApplicationTestAccess;

class GameApplication
{
public:
    explicit GameApplication(const Engine::ApplicationConfig &config);

    int run();

private:
    friend class HeadlessGameplayDiagnostics;
    friend struct GameApplicationTestAccess;

    bool loadGameData(const Engine::AssetFileSystem &assetFileSystem);
    void shutdownApplication();
    bool initializeSelectedMapRuntime(bool initializeView);
    bool initializeRenderer();
    void shutdownRenderer();
    bool reloadSelectedMap();
    Party &ensureSessionPartyState();
    void bindPartyDependencies(Party &party) const;
    void synchronizeSessionFromRuntime();
    bool loadCurrentSessionMap(
        bool initializeView,
        const std::function<void(int)> &progressCallback = {});
    bool applyCurrentSessionToRuntime(bool initializeView);
    void syncMapPickerToSelectedMap();
    bool processPendingMapMove();
    bool processPendingPartyDefeat();
    void handleCompletedPartyDefeatScreen();
    bool shouldTriggerPartyDefeat() const;
    std::string resolvePartyDefeatRespawnMapFileName() const;
    void applyPartyDefeatConsequences();
    bool respawnPartyAfterDefeat(bool initializeView);
    void captureCurrentSceneState();
    void restoreSavedOutdoorWorldStateForSelectedMap();
    void updateMapPickerInput();
    void updateQuickSaveInput();
    bool processPendingQuickSaveInput();
    bool quickSave();
    bool quickLoad();
    bool quickSaveToPath(
        const std::filesystem::path &path,
        const std::string &saveName = "",
        const std::vector<uint8_t> &previewBmp = {});
    bool quickLoadFromPath(const std::filesystem::path &path, bool initializeView);
    void openMainMenuScreen();
    void openLoadGameScreen(bool returnToGameplayMenu = false);
    void openNewGameScreen();
    bool processPendingArcomageGame();
    void handleCompletedArcomageScreen();
    bool initializeStartupSession(bool initializeView);
    bool startNewSession(std::optional<uint32_t> rosterId, bool initializeView = true);
    bool startNewSessionFromCharacterCreation(const Character &character, bool initializeView = true);
    bool loadSessionFromPath(const std::filesystem::path &path);
    void beginLoadingOverlay(
        LoadingOverlayScreen::Presentation presentation = LoadingOverlayScreen::Presentation::Fullscreen);
    void renderLoadingOverlayProgress(int progressPercent);
    void pumpLoadingOverlayAnimation();
    void completeLoadingOverlay();
    void cancelLoadingOverlay();
    std::filesystem::path settingsFilePath() const;
    void loadOrCreateSettings();
    void applyCurrentSettingsToActiveRuntime();
    void applyStartupDebugSettingsToActiveRuntime();
    void requestApplicationQuit() const;
    void reportQuickSaveStatus(const std::string &status);
    void renderMapPickerOverlay() const;
    void handleSdlEvent(const SDL_Event &event);
    void renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds);

    Engine::ApplicationConfig m_config;
    Engine::EngineApplication m_engineApplication;
    GameDataLoader m_gameDataLoader;
    GameDataRepository m_gameDataRepository;
    GameAudioSystem m_gameAudioSystem;
    GameSession m_gameSession;
    GameInputSystem m_gameInputSystem;
    IndoorRenderer m_indoorRenderer;
    IndoorGameView m_indoorGameView;
    OutdoorGameView m_outdoorGameView;
    ScreenManager m_screenManager;
    GameSettings m_settings = GameSettings::createDefault();
    GameplayController m_gameplayController;
    std::unique_ptr<OutdoorPartyRuntime> m_pOutdoorPartyRuntime;
    std::unique_ptr<OutdoorWorldRuntime> m_pOutdoorWorldRuntime;
    std::unique_ptr<IMapSceneRuntime> m_pMapSceneRuntime;
    const Engine::AssetFileSystem *m_pAssetFileSystem;
    size_t m_mapPickerIndex;
    bool m_showMapPicker;
    bool m_pickerToggleLatch;
    bool m_pickerApplyLatch;
    bool m_quickSaveLatch = false;
    bool m_quickLoadLatch = false;
    bool m_advanceTimeLatch = false;
    bool m_pendingQuickSave = false;
    bool m_pendingQuickLoad = false;
    bool m_pendingAdvanceTime = false;
    bool m_bootSeededDwiOnNextRendererInit = false;
    uint64_t m_pickerNextUpRepeatTick;
    uint64_t m_pickerNextDownRepeatTick;
    std::unique_ptr<LoadingOverlayScreen> m_pLoadingOverlayScreen;
    std::string m_loadingOverlayBackgroundTextureName;
    LoadingOverlayScreen::Presentation m_loadingOverlayPresentation = LoadingOverlayScreen::Presentation::Fullscreen;
    bool m_loadingOverlayActive = false;
    int m_loadingOverlayCurrentProgressPercent = 0;
    uint64_t m_loadingOverlayNextAnimationFrameTick = 0;
    int m_lastFrameWidth = 640;
    int m_lastFrameHeight = 480;
    std::optional<std::string> m_pendingPartyDefeatRespawnMapFileName;
};
}
