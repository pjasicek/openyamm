#pragma once

#include "engine/ApplicationConfig.h"
#include "engine/AssetFileSystem.h"

#include <SDL3/SDL.h>

#include <functional>

namespace OpenYAMM::Engine
{
class BgfxContext;
class EngineApplication
{
public:
    using StartupCallback = std::function<bool(AssetFileSystem &)>;
    using RenderSetupCallback = std::function<bool()>;
    using RenderFrameCallback = std::function<void(int, int, float, float)>;
    using EventCallback = std::function<void(const SDL_Event &)>;
    using ShutdownCallback = std::function<void()>;
    using TextInputActiveCallback = std::function<bool()>;
    using UndrawnFrameCallback = std::function<void(float)>;

    EngineApplication(
        const ApplicationConfig &config,
        StartupCallback startupCallback,
        RenderSetupCallback renderSetupCallback,
        EventCallback eventCallback,
        RenderFrameCallback renderFrameCallback,
        ShutdownCallback shutdownCallback = {},
        TextInputActiveCallback textInputActiveCallback = {}
    );

    int run() const;
    void setConfiguration(const ApplicationConfig &config);
    bool applyDisplaySettings(WindowMode mode, int width, int height, bool verticalSync, std::string &error);
    // Anisotropic filtering limit of every anisotropic sampler; applies immediately while running.
    void setMaxAnisotropy(uint8_t level);
    // Above 0 every frame advances by exactly this many seconds whatever the wall clock says (a video capture's
    // frame step); 0 returns to real time.
    void setFixedFrameSeconds(float seconds);
    // Called with the frame's seconds for every frame the window has no drawable for (a zero size: Android in the
    // background, some desktops while minimized), in place of the render callback. Nothing is drawn or presented.
    void setUndrawnFrameCallback(UndrawnFrameCallback callback);

  private:
    bool initializeAssetFileSystem(AssetFileSystem &assetFileSystem) const;
    bool validateConfiguration() const;

    ApplicationConfig m_config;
    mutable SDL_Window *m_pRunningWindow = nullptr;
    mutable BgfxContext *m_pRunningContext = nullptr;
    StartupCallback m_startupCallback;
    RenderSetupCallback m_renderSetupCallback;
    EventCallback m_eventCallback;
    RenderFrameCallback m_renderFrameCallback;
    ShutdownCallback m_shutdownCallback;
    TextInputActiveCallback m_textInputActiveCallback;
    UndrawnFrameCallback m_undrawnFrameCallback;
    float m_fixedFrameSeconds = 0.0f;
};
}
