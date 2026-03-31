#pragma once

#include "engine/ApplicationConfig.h"
#include "engine/EngineApplication.h"
#include "game/GameDataLoader.h"
#include "game/GameAudioSystem.h"
#include "game/IndoorDebugRenderer.h"
#include "game/OutdoorGameView.h"
#include "game/OutdoorPartyRuntime.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/Party.h"
#include "game/SaveGame.h"

#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <unordered_map>

namespace OpenYAMM::Game
{
class HeadlessOutdoorDiagnostics;
struct GameApplicationTestAccess;

class GameApplication
{
public:
    explicit GameApplication(const Engine::ApplicationConfig &config);

    int run();

private:
    friend class HeadlessOutdoorDiagnostics;
    friend struct GameApplicationTestAccess;

    bool loadGameData(const Engine::AssetFileSystem &assetFileSystem);
    void shutdownApplication();
    bool initializeSelectedMapRuntime(bool initializeView);
    bool initializeRenderer();
    void shutdownRenderer();
    bool reloadSelectedMap();
    bool processPendingOutdoorMapMove();
    void captureCurrentOutdoorWorldState();
    void restoreSavedOutdoorWorldStateForSelectedMap();
    void updateMapPickerInput();
    void updateQuickSaveInput();
    bool processPendingQuickSaveInput();
    bool quickSave();
    bool quickLoad();
    bool quickSaveToPath(const std::filesystem::path &path);
    bool quickLoadFromPath(const std::filesystem::path &path, bool initializeView);
    void reportQuickSaveStatus(const std::string &status) const;
    void renderMapPickerOverlay() const;
    void renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds);

    Engine::EngineApplication m_engineApplication;
    GameDataLoader m_gameDataLoader;
    GameAudioSystem m_gameAudioSystem;
    IndoorDebugRenderer m_indoorDebugRenderer;
    OutdoorGameView m_outdoorGameView;
    std::unique_ptr<OutdoorPartyRuntime> m_pOutdoorPartyRuntime;
    std::unique_ptr<OutdoorWorldRuntime> m_pOutdoorWorldRuntime;
    std::optional<Party> m_partyState;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> m_outdoorWorldStates;
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
    uint64_t m_pickerNextUpRepeatTick;
    uint64_t m_pickerNextDownRepeatTick;
};
}
