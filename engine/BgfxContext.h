#pragma once

#include <bgfx/bgfx.h>

struct SDL_Window;

namespace OpenYAMM::Engine
{
class BgfxContext
{
public:
    BgfxContext();
    ~BgfxContext();

    BgfxContext(const BgfxContext &) = delete;
    BgfxContext &operator=(const BgfxContext &) = delete;

    bool initialize(SDL_Window *pWindow, int windowWidth, int windowHeight);
    void resize(int windowWidth, int windowHeight) const;
    void shutdown();

    bool isInitialized() const;
    bgfx::RendererType::Enum getRendererType() const;

private:
    static bgfx::PlatformData resolvePlatformData(SDL_Window *pWindow);

    bool m_isInitialized;
    bgfx::RendererType::Enum m_rendererType;
};
}
