#pragma once

#include "editor/app/EditorImGuiBgfxRenderer.h"
#include "editor/app/EditorMainWindow.h"
#include "editor/document/EditorSession.h"
#include "engine/ApplicationConfig.h"
#include "engine/AssetFileSystem.h"
#include "engine/EngineApplication.h"

#include <SDL3/SDL_events.h>

#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <string>

namespace OpenYAMM::Editor
{
enum class EditorRenderSmokeMode
{
    FullScene,
    ModelInstancesOnly,
    SkyOnly,
    PhysicsOnly,
    WaterOnly,
    VisibilityOnly,
    InvisibleOnly,
    HelperOnly,
    TriggerOnly
};

struct EditorRenderSmokeConfig
{
    bool enabled = false;
    std::filesystem::path mapPath;
    EditorRenderSmokeMode mode = EditorRenderSmokeMode::FullScene;
    uint32_t maxFrames = 600;
};

class EditorApplication
{
public:
    explicit EditorApplication(
        const Engine::ApplicationConfig &config,
        const EditorRenderSmokeConfig &renderSmokeConfig = {});

    int run();

private:
    bool startup(Engine::AssetFileSystem &assetFileSystem);
    bool setupRendering();
    void handleEvent(const SDL_Event &event);
    void renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds);
    void shutdown();
    void updateRenderSmokeState();
    void requestRenderSmokeExit(bool success, const std::string &message);

    Engine::EngineApplication m_engineApplication;
    Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    EditorImGuiBgfxRenderer m_imguiRenderer;
    EditorMainWindow m_mainWindow;
    std::unique_ptr<EditorOutdoorViewport> m_pRenderSmokeViewport;
    EditorSession m_session;
    EditorRenderSmokeConfig m_renderSmokeConfig;
    std::string m_renderSmokeCaptureToken;
    std::optional<int> m_renderSmokeExitCode;
    bool m_renderSmokeScreenshotRequested = false;
    bool m_renderSmokeScreenshotReceived = false;
    bool m_renderSmokeScreenshotCaptured = false;
    uint32_t m_renderSmokeScreenshotRequestFrame = 0;
    uint32_t m_renderSmokeScreenshotVisiblePixels = 0;
    uint32_t m_renderSmokeScreenshotColorBuckets = 0;
    bool m_renderSmokeSubmittedGeometry = false;
    uint32_t m_frameNumber = 0;
};
}
