#include "game/debug/ScreenshotCaptureService.h"

#include "engine/BgfxContext.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <optional>
#include <system_error>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t CaptureTimeoutMilliseconds = 3000;

bool saveBgraPixelsAsPng(
    const std::filesystem::path &outputPath,
    uint32_t width,
    uint32_t height,
    const std::vector<uint8_t> &bgraPixels)
{
    if (width == 0 || height == 0 || bgraPixels.size() < static_cast<size_t>(width) * height * 4u)
    {
        return false;
    }

    if (outputPath.has_parent_path())
    {
        std::error_code errorCode;
        std::filesystem::create_directories(outputPath.parent_path(), errorCode);
    }

    SDL_Surface *pSurface = SDL_CreateSurfaceFrom(
        static_cast<int>(width),
        static_cast<int>(height),
        SDL_PIXELFORMAT_BGRA32,
        const_cast<uint8_t *>(bgraPixels.data()),
        static_cast<int>(width) * 4);

    if (pSurface == nullptr)
    {
        return false;
    }

    const bool saved = SDL_SavePNG(pSurface, outputPath.string().c_str());
    SDL_DestroySurface(pSurface);
    return saved;
}
}

void ScreenshotCaptureService::requestCapture(
    const std::filesystem::path &outputPath,
    CompletionCallback completionCallback)
{
    PendingCapture pending = {};
    pending.outputPath = outputPath;
    pending.completionCallback = std::move(completionCallback);
    pending.token = "appshot-" + std::to_string(m_nextCaptureToken);
    ++m_nextCaptureToken;
    m_pendingCaptures.push_back(std::move(pending));
}

bool ScreenshotCaptureService::hasPendingCaptures() const
{
    return !m_pendingCaptures.empty();
}

void ScreenshotCaptureService::update()
{
    if (m_pendingCaptures.empty())
    {
        return;
    }

    PendingCapture &pending = m_pendingCaptures.front();

    if (!pending.screenshotRequested)
    {
        bgfx::requestScreenShot(BGFX_INVALID_HANDLE, pending.token.c_str());
        pending.requestedTicks = SDL_GetTicks();
        pending.screenshotRequested = true;
        return;
    }

    const std::optional<Engine::BgfxContext::ScreenshotCapture> screenshot =
        Engine::BgfxContext::consumeScreenshot(pending.token);

    if (!screenshot)
    {
        if (SDL_GetTicks() - pending.requestedTicks > CaptureTimeoutMilliseconds)
        {
            const std::string outputPathText = pending.outputPath.string();
            CompletionCallback completionCallback = std::move(pending.completionCallback);
            m_pendingCaptures.erase(m_pendingCaptures.begin());

            if (completionCallback)
            {
                completionCallback(false, "screenshot capture timed out: " + outputPathText);
            }
        }

        return;
    }

    const bool saved = saveBgraPixelsAsPng(
        pending.outputPath,
        screenshot->width,
        screenshot->height,
        screenshot->bgraPixels);
    const std::string outputPathText = pending.outputPath.string();
    CompletionCallback completionCallback = std::move(pending.completionCallback);
    m_pendingCaptures.erase(m_pendingCaptures.begin());

    if (completionCallback)
    {
        completionCallback(
            saved,
            saved ? "saved screenshot: " + outputPathText : "failed to write screenshot: " + outputPathText);
    }
}
}
