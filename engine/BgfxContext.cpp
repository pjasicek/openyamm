#include "engine/BgfxContext.h"

#include <SDL3/SDL.h>
#include <SDL3/SDL_properties.h>
#include <SDL3/SDL_video.h>

#include <cstdarg>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cctype>
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <optional>
#include <string>
#include <utility>

namespace OpenYAMM::Engine
{
namespace
{
std::mutex g_screenshotMutex;
std::optional<BgfxContext::ScreenshotCapture> g_screenshotCapture;
bool g_bgfxInitialized = false;

std::string lowerCopy(const char *pValue)
{
    std::string value = pValue != nullptr ? pValue : "";
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return value;
}

std::optional<bgfx::RendererType::Enum> rendererTypeFromEnvironment()
{
    const char *pRenderer = std::getenv("OPENYAMM_BGFX_RENDERER");

    if (pRenderer == nullptr || pRenderer[0] == '\0')
    {
        return std::nullopt;
    }

    const std::string renderer = lowerCopy(pRenderer);

    if (renderer == "noop")
    {
        return bgfx::RendererType::Noop;
    }
    if (renderer == "opengl" || renderer == "gl")
    {
        return bgfx::RendererType::OpenGL;
    }
    if (renderer == "opengles" || renderer == "gles")
    {
        return bgfx::RendererType::OpenGLES;
    }
    if (renderer == "vulkan" || renderer == "vk")
    {
        return bgfx::RendererType::Vulkan;
    }
    if (renderer == "d3d11" || renderer == "direct3d11")
    {
        return bgfx::RendererType::Direct3D11;
    }
    if (renderer == "d3d12" || renderer == "direct3d12")
    {
        return bgfx::RendererType::Direct3D12;
    }

    std::cerr << "Ignoring unknown OPENYAMM_BGFX_RENDERER=" << pRenderer << '\n';
    return std::nullopt;
}

bgfx::RendererType::Enum selectRendererType(bool useNoopRenderer)
{
    const std::optional<bgfx::RendererType::Enum> environmentRenderer = rendererTypeFromEnvironment();

    if (environmentRenderer)
    {
        return *environmentRenderer;
    }

    if (useNoopRenderer)
    {
        return bgfx::RendererType::Noop;
    }

#if defined(__ANDROID__)
    return bgfx::RendererType::OpenGLES;
#elif defined(_WIN32)
    return bgfx::RendererType::Direct3D11;
#else
    return bgfx::RendererType::OpenGL;
#endif
}
}

class BgfxContext::Callback final : public bgfx::CallbackI
{
public:
    void fatal(const char *pFilePath, uint16_t line, bgfx::Fatal::Enum code, const char *pMessage) override
    {
        std::cerr
            << "bgfx fatal"
            << " [" << (pFilePath != nullptr ? pFilePath : "?") << ":" << line << "] "
            << (pMessage != nullptr ? pMessage : "")
            << '\n';

        if (code != bgfx::Fatal::DebugCheck)
        {
            std::abort();
        }
    }

    void traceVargs(const char *pFilePath, uint16_t line, const char *pFormat, va_list argList) override
    {
        std::fprintf(stderr, "bgfx trace [%s:%u] ", pFilePath != nullptr ? pFilePath : "?", line);
        std::vfprintf(stderr, pFormat, argList);
    }

    void profilerBegin(const char *, uint32_t, const char *, uint16_t) override
    {
    }

    void profilerBeginLiteral(const char *, uint32_t, const char *, uint16_t) override
    {
    }

    void profilerEnd() override
    {
    }

    uint32_t cacheReadSize(uint64_t) override
    {
        return 0;
    }

    bool cacheRead(uint64_t, void *, uint32_t) override
    {
        return false;
    }

    void cacheWrite(uint64_t, const void *, uint32_t) override
    {
    }

    void screenShot(
        const char *pFilePath,
        uint32_t width,
        uint32_t height,
        uint32_t pitch,
        bgfx::TextureFormat::Enum format,
        const void *pData,
        uint32_t size,
        bool yFlip) override
    {
        if (pFilePath == nullptr || pData == nullptr || width == 0 || height == 0 || pitch < width * 4)
        {
            return;
        }

        const size_t expectedSize = static_cast<size_t>(pitch) * static_cast<size_t>(height);

        if (size < expectedSize)
        {
            return;
        }

        ScreenshotCapture capture = {};
        capture.token = pFilePath;
        capture.width = width;
        capture.height = height;
        capture.bgraPixels.resize(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);

        const uint8_t *pSourceBytes = static_cast<const uint8_t *>(pData);

        for (uint32_t y = 0; y < height; ++y)
        {
            const uint32_t sourceY = yFlip ? (height - 1 - y) : y;
            const uint8_t *pSourceRow = pSourceBytes + static_cast<size_t>(sourceY) * pitch;
            uint8_t *pDestinationRow = capture.bgraPixels.data() + static_cast<size_t>(y) * width * 4;

            if (format == bgfx::TextureFormat::RGBA8)
            {
                for (uint32_t x = 0; x < width; ++x)
                {
                    const size_t sourceIndex = static_cast<size_t>(x) * 4;
                    const size_t destinationIndex = static_cast<size_t>(x) * 4;
                    pDestinationRow[destinationIndex + 0] = pSourceRow[sourceIndex + 2];
                    pDestinationRow[destinationIndex + 1] = pSourceRow[sourceIndex + 1];
                    pDestinationRow[destinationIndex + 2] = pSourceRow[sourceIndex + 0];
                    pDestinationRow[destinationIndex + 3] = pSourceRow[sourceIndex + 3];
                }
            }
            else
            {
                std::memcpy(pDestinationRow, pSourceRow, static_cast<size_t>(width) * 4);
            }
        }

        std::scoped_lock lock(g_screenshotMutex);
        g_screenshotCapture = std::move(capture);
    }

    void captureBegin(uint32_t, uint32_t, uint32_t, bgfx::TextureFormat::Enum, bool) override
    {
    }

    void captureEnd() override
    {
    }

    void captureFrame(const void *, uint32_t) override
    {
    }
};

BgfxContext::BgfxContext()
    : m_isInitialized(false)
    , m_verticalSync(false)
    , m_rendererType(bgfx::RendererType::Noop)
    , m_pCallback(std::make_unique<Callback>())
{
}

BgfxContext::~BgfxContext()
{
    shutdown();
}

uint32_t bgfxResetFlags(bool verticalSync)
{
    uint32_t flags = BGFX_RESET_MAXANISOTROPY;

    if (verticalSync)
    {
        flags |= BGFX_RESET_VSYNC;
    }

    return flags;
}

bool BgfxContext::initialize(SDL_Window *pWindow, int windowWidth, int windowHeight, bool verticalSync)
{
    shutdown();

    bgfx::Init init = {};
    const char *pVideoDriver = SDL_GetCurrentVideoDriver();
    const bool useNoopRenderer = (pVideoDriver != nullptr) && (SDL_strcmp(pVideoDriver, "dummy") == 0);

    init.type = selectRendererType(useNoopRenderer);
    init.vendorId = BGFX_PCI_ID_NONE;
    init.platformData = resolvePlatformData(pWindow);
    init.resolution.width = static_cast<uint32_t>(windowWidth);
    init.resolution.height = static_cast<uint32_t>(windowHeight);
    init.resolution.reset = bgfxResetFlags(verticalSync);
    init.callback = m_pCallback.get();

    if (!bgfx::init(init))
    {
        std::cerr << "bgfx::init failed.\n";
        return false;
    }

    g_bgfxInitialized = true;
    m_isInitialized = true;
    m_verticalSync = verticalSync;
    m_rendererType = bgfx::getRendererType();

    bgfx::setDebug(BGFX_DEBUG_NONE);
    bgfx::setViewClear(0, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x000000ff, 1.0f, 0);

    return true;
}

void BgfxContext::resize(int windowWidth, int windowHeight) const
{
    if (!m_isInitialized)
    {
        return;
    }

    bgfx::reset(
        static_cast<uint32_t>(windowWidth),
        static_cast<uint32_t>(windowHeight),
        bgfxResetFlags(m_verticalSync));
}

void BgfxContext::shutdown()
{
    if (!m_isInitialized)
    {
        return;
    }

    bgfx::shutdown();
    m_isInitialized = false;
    m_verticalSync = false;
    m_rendererType = bgfx::RendererType::Noop;
    g_bgfxInitialized = false;
}

bool BgfxContext::isInitialized() const
{
    return m_isInitialized;
}

bool BgfxContext::isBgfxInitialized()
{
    return g_bgfxInitialized;
}

bgfx::RendererType::Enum BgfxContext::getRendererType() const
{
    return m_rendererType;
}

std::optional<BgfxContext::ScreenshotCapture> BgfxContext::consumeScreenshot(const std::string &token)
{
    std::scoped_lock lock(g_screenshotMutex);

    if (!g_screenshotCapture || g_screenshotCapture->token != token)
    {
        return std::nullopt;
    }

    std::optional<ScreenshotCapture> capture = std::move(g_screenshotCapture);
    g_screenshotCapture.reset();
    return capture;
}

bgfx::PlatformData BgfxContext::resolvePlatformData(SDL_Window *pWindow)
{
    bgfx::PlatformData platformData = {};

    if (pWindow == nullptr)
    {
        return platformData;
    }

    const SDL_PropertiesID windowProperties = SDL_GetWindowProperties(pWindow);

    if (windowProperties == 0)
    {
        return platformData;
    }

#if defined(SDL_PROP_WINDOW_ANDROID_WINDOW_POINTER)
    void *pAndroidWindow = SDL_GetPointerProperty(windowProperties, SDL_PROP_WINDOW_ANDROID_WINDOW_POINTER, nullptr);

    if (pAndroidWindow != nullptr)
    {
        platformData.nwh = pAndroidWindow;
        platformData.type = bgfx::NativeWindowHandleType::Default;
        return platformData;
    }
#endif

    void *pWaylandDisplay = SDL_GetPointerProperty(windowProperties, SDL_PROP_WINDOW_WAYLAND_DISPLAY_POINTER, nullptr);
    void *pWaylandSurface = SDL_GetPointerProperty(windowProperties, SDL_PROP_WINDOW_WAYLAND_SURFACE_POINTER, nullptr);

    if (pWaylandDisplay != nullptr && pWaylandSurface != nullptr)
    {
        platformData.ndt = pWaylandDisplay;
        platformData.nwh = pWaylandSurface;
        platformData.type = bgfx::NativeWindowHandleType::Wayland;
        return platformData;
    }

    void *pX11Display = SDL_GetPointerProperty(windowProperties, SDL_PROP_WINDOW_X11_DISPLAY_POINTER, nullptr);
    const Sint64 x11WindowNumber = SDL_GetNumberProperty(windowProperties, SDL_PROP_WINDOW_X11_WINDOW_NUMBER, 0);

    if (pX11Display != nullptr && x11WindowNumber != 0)
    {
        platformData.ndt = pX11Display;
        platformData.nwh = reinterpret_cast<void *>(static_cast<uintptr_t>(x11WindowNumber));
        platformData.type = bgfx::NativeWindowHandleType::Default;
        return platformData;
    }

    void *pWin32Handle = SDL_GetPointerProperty(windowProperties, SDL_PROP_WINDOW_WIN32_HWND_POINTER, nullptr);

    if (pWin32Handle != nullptr)
    {
        platformData.nwh = pWin32Handle;
        platformData.type = bgfx::NativeWindowHandleType::Default;
        return platformData;
    }

    void *pCocoaWindow = SDL_GetPointerProperty(windowProperties, SDL_PROP_WINDOW_COCOA_WINDOW_POINTER, nullptr);

    if (pCocoaWindow != nullptr)
    {
        platformData.nwh = pCocoaWindow;
        platformData.type = bgfx::NativeWindowHandleType::Default;
        return platformData;
    }

    return platformData;
}
}
