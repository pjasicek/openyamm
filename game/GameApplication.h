#pragma once

#include "engine/ApplicationConfig.h"
#include "engine/EngineApplication.h"
#include "game/GameDataLoader.h"
#include "game/IndoorDebugRenderer.h"
#include "game/TerrainDebugRenderer.h"

#include <cstddef>
#include <cstdint>

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
    void updateMapPickerInput();
    void renderMapPickerOverlay() const;
    void renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds);

    Engine::EngineApplication m_engineApplication;
    GameDataLoader m_gameDataLoader;
    IndoorDebugRenderer m_indoorDebugRenderer;
    TerrainDebugRenderer m_terrainDebugRenderer;
    const Engine::AssetFileSystem *m_pAssetFileSystem;
    size_t m_mapPickerIndex;
    bool m_showMapPicker;
    bool m_pickerToggleLatch;
    bool m_pickerApplyLatch;
    uint64_t m_pickerNextUpRepeatTick;
    uint64_t m_pickerNextDownRepeatTick;
};
}
