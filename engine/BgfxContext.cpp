#include "engine/BgfxContext.h"

#include <SDL3/SDL.h>
#include <SDL3/SDL_properties.h>
#include <SDL3/SDL_video.h>

#include <cstdint>
#include <iostream>

namespace OpenYAMM::Engine
{
BgfxContext::BgfxContext()
    : m_isInitialized(false)
    , m_rendererType(bgfx::RendererType::Noop)
{
}

BgfxContext::~BgfxContext()
{
    shutdown();
}

bool BgfxContext::initialize(SDL_Window *pWindow, int windowWidth, int windowHeight)
{
    shutdown();

    bgfx::Init init = {};
    const char *pVideoDriver = SDL_GetCurrentVideoDriver();
    const bool useNoopRenderer = (pVideoDriver != nullptr) && (SDL_strcmp(pVideoDriver, "dummy") == 0);

    init.type = useNoopRenderer ? bgfx::RendererType::Noop : bgfx::RendererType::OpenGL;
    init.vendorId = BGFX_PCI_ID_NONE;
    init.platformData = resolvePlatformData(pWindow);
    init.resolution.width = static_cast<uint32_t>(windowWidth);
    init.resolution.height = static_cast<uint32_t>(windowHeight);
    init.resolution.reset = BGFX_RESET_NONE;

    if (!bgfx::init(init))
    {
        std::cerr << "bgfx::init failed.\n";
        return false;
    }

    m_isInitialized = true;
    m_rendererType = bgfx::getRendererType();

    bgfx::setDebug(BGFX_DEBUG_TEXT);
    bgfx::setViewClear(0, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x000000ff, 1.0f, 0);

    return true;
}

void BgfxContext::resize(int windowWidth, int windowHeight) const
{
    if (!m_isInitialized)
    {
        return;
    }

    bgfx::reset(static_cast<uint32_t>(windowWidth), static_cast<uint32_t>(windowHeight), BGFX_RESET_NONE);
}

void BgfxContext::shutdown()
{
    if (!m_isInitialized)
    {
        return;
    }

    bgfx::shutdown();
    m_isInitialized = false;
    m_rendererType = bgfx::RendererType::Noop;
}

bool BgfxContext::isInitialized() const
{
    return m_isInitialized;
}

bgfx::RendererType::Enum BgfxContext::getRendererType() const
{
    return m_rendererType;
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
