#include "game/debug/ScreenshotCaptureService.h"

#include "engine/BgfxContext.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <algorithm>
#include <cmath>
#include <optional>
#include <system_error>
#include <utility>

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
        if (errorCode)
        {
            return false;
        }
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

// The pixels of region, clamped to the frame; width and height become the region's.
std::vector<uint8_t> cropBgraPixels(
    const std::vector<uint8_t> &bgraPixels,
    uint32_t &width,
    uint32_t &height,
    const ScreenshotCaptureService::Region &region)
{
    const uint32_t left = std::min(width - 1, uint32_t(std::max(0.0f, std::round(region.x * float(width)))));
    const uint32_t top = std::min(height - 1, uint32_t(std::max(0.0f, std::round(region.y * float(height)))));
    const uint32_t right =
        std::clamp(uint32_t(std::max(0.0f, std::round((region.x + region.width) * float(width)))), left + 1, width);
    const uint32_t bottom =
        std::clamp(uint32_t(std::max(0.0f, std::round((region.y + region.height) * float(height)))), top + 1, height);
    std::vector<uint8_t> cropped;
    cropped.reserve(size_t(right - left) * (bottom - top) * 4u);

    for (uint32_t row = top; row < bottom; ++row)
    {
        const auto rowBegin = bgraPixels.begin() + (size_t(row) * width + left) * 4u;
        cropped.insert(cropped.end(), rowBegin, rowBegin + size_t(right - left) * 4u);
    }

    width = right - left;
    height = bottom - top;
    return cropped;
}
}

void ScreenshotCaptureService::requestCapture(
    const std::filesystem::path &outputPath,
    CompletionCallback completionCallback,
    const std::optional<Region> &region)
{
    PendingCapture pending = {};
    pending.outputPath = outputPath;
    pending.completionCallback = std::move(completionCallback);
    pending.region = region;
    pending.token = "appshot-" + std::to_string(m_nextCaptureToken);
    ++m_nextCaptureToken;
    m_pendingCaptures.push_back(std::move(pending));
}

bool ScreenshotCaptureService::hasPendingCaptures() const
{
    return !m_pendingCaptures.empty();
}

void ScreenshotCaptureService::requestPixels(PixelsCallback callback)
{
    PendingCapture pending;
    pending.pixelsCallback = std::move(callback);
    pending.token = "appshot-" + std::to_string(m_nextCaptureToken++);
    m_pendingCaptures.push_back(std::move(pending));
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
            PixelsCallback pixelsCallback = std::move(pending.pixelsCallback);
            m_pendingCaptures.erase(m_pendingCaptures.begin());

            if (completionCallback)
            {
                completionCallback(false, "screenshot capture timed out: " + outputPathText);
            }
            if (pixelsCallback)
            {
                pixelsCallback(0, 0, {});
            }
        }

        return;
    }

    if (pending.pixelsCallback)
    {
        PixelsCallback callback = std::move(pending.pixelsCallback);
        m_pendingCaptures.erase(m_pendingCaptures.begin());
        callback(screenshot->width, screenshot->height, screenshot->bgraPixels);
        return;
    }

    uint32_t width = screenshot->width;
    uint32_t height = screenshot->height;
    bool saved = false;

    if (pending.region && width != 0 && height != 0)
    {
        const std::vector<uint8_t> cropped = cropBgraPixels(screenshot->bgraPixels, width, height, *pending.region);
        saved = saveBgraPixelsAsPng(pending.outputPath, width, height, cropped);
    }
    else
    {
        saved = saveBgraPixelsAsPng(pending.outputPath, width, height, screenshot->bgraPixels);
    }
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
