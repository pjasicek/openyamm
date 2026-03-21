#include "engine/BgfxContext.h"
#include "engine/EngineApplication.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <filesystem>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
namespace
{
constexpr float SlowFrameLogThresholdSeconds = 0.008f;
constexpr float HitchFrameLogThresholdSeconds = 0.016f;
constexpr int MinimumWindowAspectWidth = 4;
constexpr int MinimumWindowAspectHeight = 3;

class SdlSubsystemGuard
{
public:
    explicit SdlSubsystemGuard(bool isInitialized)
        : m_isInitialized(isInitialized)
    {
    }

    SdlSubsystemGuard(const SdlSubsystemGuard &) = delete;
    SdlSubsystemGuard &operator=(const SdlSubsystemGuard &) = delete;

    ~SdlSubsystemGuard()
    {
        if (m_isInitialized)
        {
            SDL_Quit();
        }
    }

private:
    bool m_isInitialized;
};

struct SdlWindowDeleter
{
    void operator()(SDL_Window *pWindow) const
    {
        if (pWindow != nullptr)
        {
            SDL_DestroyWindow(pWindow);
        }
    }
};

void enforceMinimumWindowAspect(SDL_Window *pWindow)
{
    if (pWindow == nullptr)
    {
        return;
    }

    int windowWidth = 0;
    int windowHeight = 0;
    SDL_GetWindowSize(pWindow, &windowWidth, &windowHeight);

    if (windowWidth <= 0 || windowHeight <= 0)
    {
        return;
    }

    if (windowWidth * MinimumWindowAspectHeight >= windowHeight * MinimumWindowAspectWidth)
    {
        return;
    }

    const int correctedWidth =
        (windowHeight * MinimumWindowAspectWidth + MinimumWindowAspectHeight - 1) / MinimumWindowAspectHeight;

    if (correctedWidth != windowWidth)
    {
        SDL_SetWindowSize(pWindow, correctedWidth, windowHeight);
    }
}
}

EngineApplication::EngineApplication(
    const ApplicationConfig &config,
    StartupCallback startupCallback,
    RenderSetupCallback renderSetupCallback,
    RenderFrameCallback renderFrameCallback,
    ShutdownCallback shutdownCallback
)
    : m_config(config)
    , m_startupCallback(std::move(startupCallback))
    , m_renderSetupCallback(std::move(renderSetupCallback))
    , m_renderFrameCallback(std::move(renderFrameCallback))
    , m_shutdownCallback(std::move(shutdownCallback))
{
}

int EngineApplication::run() const
{
    if (!validateConfiguration())
    {
        return 1;
    }

    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS))
    {
        std::cerr << "SDL_Init failed: " << SDL_GetError() << '\n';
        return 1;
    }

    const SdlSubsystemGuard sdlGuard(true);
    AssetFileSystem assetFileSystem;

    if (!initializeAssetFileSystem(assetFileSystem))
    {
        return 1;
    }

    if (m_startupCallback && !m_startupCallback(assetFileSystem))
    {
        return 1;
    }

    SDL_Window *pRawWindow = SDL_CreateWindow(
        m_config.appName.c_str(),
        m_config.windowWidth,
        m_config.windowHeight,
        SDL_WINDOW_RESIZABLE
    );

    if (pRawWindow == nullptr)
    {
        std::cerr << "SDL_CreateWindow failed: " << SDL_GetError() << '\n';
        return 1;
    }

    std::unique_ptr<SDL_Window, SdlWindowDeleter> pWindow(pRawWindow);
    enforceMinimumWindowAspect(pWindow.get());
    BgfxContext bgfxContext;

    if (!bgfxContext.initialize(pWindow.get(), m_config.windowWidth, m_config.windowHeight))
    {
        return 1;
    }

    if (m_renderSetupCallback && !m_renderSetupCallback())
    {
        return 1;
    }

    std::cout << m_config.appName << '\n';
    std::cout << "Development assets: " << m_config.assetRoot << '\n';
    std::cout << "Window: " << m_config.windowWidth << "x" << m_config.windowHeight << '\n';
    std::cout << "Renderer: " << bgfx::getRendererName(bgfxContext.getRendererType()) << '\n';
    std::cout << "Mounted search paths:\n";

    const std::vector<std::string> searchPaths = assetFileSystem.getSearchPaths();

    for (const std::string &searchPath : searchPaths)
    {
        std::cout << "  " << searchPath << '\n';
    }

    const bool hasDataDirectory = assetFileSystem.exists("Data");
    std::cout << "Data directory available: " << (hasDataDirectory ? "yes" : "no") << '\n';
    std::cout << "Close the window to exit.\n";

    bool isRunning = true;
    uint64_t lastFrameTickCount = SDL_GetTicksNS();
    float fpsSampleSeconds = 0.0f;
    uint32_t fpsSampleFrameCount = 0;
    std::vector<float> slowFrameSamples;
    slowFrameSamples.reserve(16);
    float worstSlowFrameSeconds = 0.0f;
    uint32_t slowFrameCount = 0;

    while (isRunning)
    {
        const uint64_t currentFrameTickCount = SDL_GetTicksNS();
        float deltaSeconds = 1.0f / 60.0f;

        if (currentFrameTickCount > lastFrameTickCount)
        {
            deltaSeconds = static_cast<float>(currentFrameTickCount - lastFrameTickCount) / 1000000000.0f;
        }

        lastFrameTickCount = currentFrameTickCount;
        float mouseWheelDelta = 0.0f;
        SDL_Event event;

        while (SDL_PollEvent(&event))
        {
            if (event.type == SDL_EVENT_QUIT)
            {
                isRunning = false;
            }

            if (event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED)
            {
                isRunning = false;
            }

            if (event.type == SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED)
            {
                enforceMinimumWindowAspect(pWindow.get());

                int drawableWidth = 0;
                int drawableHeight = 0;
                SDL_GetWindowSizeInPixels(pWindow.get(), &drawableWidth, &drawableHeight);
                bgfxContext.resize(drawableWidth, drawableHeight);
            }

            if (event.type == SDL_EVENT_MOUSE_WHEEL)
            {
                mouseWheelDelta += event.wheel.y;
            }
        }

        const uint64_t afterEventTickCount = SDL_GetTicksNS();

        int drawableWidth = 0;
        int drawableHeight = 0;
        SDL_GetWindowSizeInPixels(pWindow.get(), &drawableWidth, &drawableHeight);

        if (m_renderFrameCallback)
        {
            m_renderFrameCallback(drawableWidth, drawableHeight, mouseWheelDelta, deltaSeconds);
        }
        else
        {
            bgfx::setViewRect(0, 0, 0, static_cast<uint16_t>(drawableWidth), static_cast<uint16_t>(drawableHeight));
            bgfx::touch(0);
        }

        const uint64_t afterRenderTickCount = SDL_GetTicksNS();
        bgfx::frame();
        const uint64_t afterBgfxFrameTickCount = SDL_GetTicksNS();

        const uint64_t requestedDelayNanoseconds = 0;
        const uint64_t actualDelayNanoseconds = 0;

        const uint64_t frameEndTickCount = SDL_GetTicksNS();
        const float frameDurationSeconds = frameEndTickCount > currentFrameTickCount
            ? static_cast<float>(frameEndTickCount - currentFrameTickCount) / 1000000000.0f
            : 0.0f;

        if (frameDurationSeconds > SlowFrameLogThresholdSeconds)
        {
            ++slowFrameCount;
            worstSlowFrameSeconds = std::max(worstSlowFrameSeconds, frameDurationSeconds);

            if (slowFrameSamples.size() < 16)
            {
                slowFrameSamples.push_back(frameDurationSeconds);
            }
        }

        if (frameDurationSeconds > HitchFrameLogThresholdSeconds)
        {
            const float eventMilliseconds = afterEventTickCount > currentFrameTickCount
                ? static_cast<float>(afterEventTickCount - currentFrameTickCount) / 1000000.0f
                : 0.0f;
            const float renderMilliseconds = afterRenderTickCount > afterEventTickCount
                ? static_cast<float>(afterRenderTickCount - afterEventTickCount) / 1000000.0f
                : 0.0f;
            const float bgfxMilliseconds = afterBgfxFrameTickCount > afterRenderTickCount
                ? static_cast<float>(afterBgfxFrameTickCount - afterRenderTickCount) / 1000000.0f
                : 0.0f;
            const float requestedDelayMilliseconds = static_cast<float>(requestedDelayNanoseconds) / 1000000.0f;
            const float actualDelayMilliseconds = static_cast<float>(actualDelayNanoseconds) / 1000000.0f;
            std::cout << "Hitch frame: total_ms=" << (frameDurationSeconds * 1000.0f)
                      << " delta_ms=" << (deltaSeconds * 1000.0f)
                      << " events_ms=" << eventMilliseconds
                      << " render_ms=" << renderMilliseconds
                      << " bgfx_ms=" << bgfxMilliseconds
                      << " delay_req_ms=" << requestedDelayMilliseconds
                      << " delay_actual_ms=" << actualDelayMilliseconds
                      << '\n';
        }

        fpsSampleSeconds += deltaSeconds;
        ++fpsSampleFrameCount;

        if (fpsSampleSeconds >= 1.0f)
        {
            const float averageFps = fpsSampleSeconds > 0.0f
                ? static_cast<float>(fpsSampleFrameCount) / fpsSampleSeconds
                : 0.0f;
            std::cout << "Average FPS (last second): " << averageFps << '\n';

            if (slowFrameCount > 0)
            {
                std::cout << "Slow frames (last second): count=" << slowFrameCount
                          << " worst_ms=" << (worstSlowFrameSeconds * 1000.0f)
                          << " samples_ms=";

                for (size_t i = 0; i < slowFrameSamples.size(); ++i)
                {
                    if (i > 0)
                    {
                        std::cout << ',';
                    }

                    std::cout << (slowFrameSamples[i] * 1000.0f);
                }

                if (slowFrameCount > slowFrameSamples.size())
                {
                    std::cout << ",...";
                }

                std::cout << '\n';
            }

            fpsSampleSeconds = 0.0f;
            fpsSampleFrameCount = 0;
            slowFrameSamples.clear();
            worstSlowFrameSeconds = 0.0f;
            slowFrameCount = 0;
        }
    }

    if (m_shutdownCallback)
    {
        m_shutdownCallback();
    }

    return 0;
}

bool EngineApplication::validateConfiguration() const
{
    if (!std::filesystem::exists(m_config.assetRoot))
    {
        std::cerr << "Development asset root does not exist: " << m_config.assetRoot << '\n';
        return false;
    }

    if (m_config.windowWidth <= 0 || m_config.windowHeight <= 0)
    {
        std::cerr << "Invalid window size: " << m_config.windowWidth << "x" << m_config.windowHeight << '\n';
        return false;
    }

    return true;
}

bool EngineApplication::initializeAssetFileSystem(AssetFileSystem &assetFileSystem) const
{
    const char *pBasePathChars = SDL_GetBasePath();
    std::filesystem::path basePath = std::filesystem::current_path();

    if (pBasePathChars != nullptr)
    {
        basePath = pBasePathChars;
    }

    return assetFileSystem.initialize(basePath, m_config.assetRoot);
}
}
