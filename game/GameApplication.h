#pragma once

#include "engine/ApplicationConfig.h"
#include "engine/EngineApplication.h"
#include "game/GameDataLoader.h"
#include "game/IndoorDebugRenderer.h"
#include "game/OutdoorGameView.h"
#include "game/OutdoorPartyRuntime.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/Party.h"

#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>

namespace OpenYAMM::Game
{
class GameApplication
{
public:
    explicit GameApplication(const Engine::ApplicationConfig &config);

    int run();

private:
    bool loadGameData(const Engine::AssetFileSystem &assetFileSystem);
    bool initializeRenderer();
    bool reloadSelectedMap();
    bool processPendingOutdoorMapMove();
    void updateMapPickerInput();
    void renderMapPickerOverlay() const;
    void renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds);

    Engine::EngineApplication m_engineApplication;
    GameDataLoader m_gameDataLoader;
    IndoorDebugRenderer m_indoorDebugRenderer;
    OutdoorGameView m_outdoorGameView;
    std::unique_ptr<OutdoorPartyRuntime> m_pOutdoorPartyRuntime;
    std::unique_ptr<OutdoorWorldRuntime> m_pOutdoorWorldRuntime;
    std::optional<Party> m_partyState;
    const Engine::AssetFileSystem *m_pAssetFileSystem;
    size_t m_mapPickerIndex;
    bool m_showMapPicker;
    bool m_pickerToggleLatch;
    bool m_pickerApplyLatch;
    uint64_t m_pickerNextUpRepeatTick;
    uint64_t m_pickerNextDownRepeatTick;
};
}
