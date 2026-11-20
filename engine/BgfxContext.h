#pragma once

#include <bgfx/bgfx.h>

#include <memory>
#include <optional>
#include <string>
#include <vector>

struct SDL_Window;

namespace OpenYAMM::Engine
{
class BgfxContext
{
public:
    struct ScreenshotCapture
    {
        std::string token;
        uint32_t width = 0;
        uint32_t height = 0;
        std::vector<uint8_t> bgraPixels;
    };

    BgfxContext();
    ~BgfxContext();

    BgfxContext(const BgfxContext &) = delete;
    BgfxContext &operator=(const BgfxContext &) = delete;

    bool initialize(SDL_Window *pWindow, int windowWidth, int windowHeight, bool verticalSync, uint8_t maxAnisotropy);
    void resize(SDL_Window *pWindow, int windowWidth, int windowHeight) const;
    void setVerticalSync(bool enabled)
    {
        m_verticalSync = enabled;
    }
    void setMaxAnisotropy(uint8_t level)
    {
        m_maxAnisotropy = level;
    }
    void shutdown();

    bool isInitialized() const;
    bgfx::RendererType::Enum getRendererType() const;
    static bool isBgfxInitialized();
    static std::optional<ScreenshotCapture> consumeScreenshot(const std::string &token);

private:
    class Callback;

    static bgfx::PlatformData resolvePlatformData(SDL_Window *pWindow);

    bool m_isInitialized;
    bool m_verticalSync;
    uint8_t m_maxAnisotropy;
    bgfx::RendererType::Enum m_rendererType;
    std::unique_ptr<Callback> m_pCallback;
#if defined(__APPLE__)
    void *m_pMetalView = nullptr;
#endif
};
}
