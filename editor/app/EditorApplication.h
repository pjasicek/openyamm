#pragma once

#include "editor/app/EditorImGuiBgfxRenderer.h"
#include "editor/app/EditorMainWindow.h"
#include "editor/document/EditorSession.h"
#include "engine/ApplicationConfig.h"
#include "engine/AssetFileSystem.h"
#include "engine/EngineApplication.h"

#include <SDL3/SDL_events.h>

#include <cstdint>
#include <string>

namespace OpenYAMM::Editor
{
class EditorApplication
{
public:
    explicit EditorApplication(const Engine::ApplicationConfig &config);

    int run();

private:
    bool startup(Engine::AssetFileSystem &assetFileSystem);
    bool setupRendering();
    void handleEvent(const SDL_Event &event);
    void renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds);
    void shutdown();

    Engine::EngineApplication m_engineApplication;
    Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    EditorImGuiBgfxRenderer m_imguiRenderer;
    EditorMainWindow m_mainWindow;
    EditorSession m_session;
    uint32_t m_frameNumber = 0;
};
}
