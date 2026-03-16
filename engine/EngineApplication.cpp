#include "engine/BgfxContext.h"
#include "engine/EngineApplication.h"

#include <SDL3/SDL.h>

#include <filesystem>
#include <iostream>
#include <memory>
#include <string>

namespace OpenYAMM::Engine
{
namespace
{
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
}

EngineApplication::EngineApplication(
    const ApplicationConfig &config,
    StartupCallback startupCallback,
    RenderSetupCallback renderSetupCallback,
    RenderFrameCallback renderFrameCallback
)
    : m_config(config)
    , m_startupCallback(std::move(startupCallback))
    , m_renderSetupCallback(std::move(renderSetupCallback))
    , m_renderFrameCallback(std::move(renderFrameCallback))
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
                bgfxContext.resize(event.window.data1, event.window.data2);
            }

            if (event.type == SDL_EVENT_MOUSE_WHEEL)
            {
                mouseWheelDelta += event.wheel.y;
            }
        }

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

        bgfx::frame();
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
