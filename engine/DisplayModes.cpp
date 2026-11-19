#include "engine/DisplayModes.h"

#include <SDL3/SDL.h>

#if defined(__APPLE__) && !defined(OPENYAMM_IOS)
#include <CoreGraphics/CoreGraphics.h>
#include <IOKit/graphics/IOGraphicsTypes.h>
#endif

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Engine
{
namespace
{
DisplayModeSize displayModeSize(const SDL_DisplayMode &mode)
{
    return {mode.w, mode.h, mode.pixel_density, mode.refresh_rate};
}

#if defined(__APPLE__) && !defined(OPENYAMM_IOS)
// SDL takes a Cocoa display's bounds from CGDisplayBounds, so the bounds name the display.
std::optional<CGDirectDisplayID> coreGraphicsDisplay(SDL_DisplayID display)
{
    SDL_Rect bounds = {};

    if (!SDL_GetDisplayBounds(display, &bounds))
    {
        return std::nullopt;
    }

    CGDirectDisplayID displays[16] = {};
    uint32_t displayCount = 0;

    if (CGGetActiveDisplayList(16, displays, &displayCount) != kCGErrorSuccess)
    {
        return std::nullopt;
    }

    for (uint32_t index = 0; index < displayCount; ++index)
    {
        const CGRect displayBounds = CGDisplayBounds(displays[index]);

        if (int(displayBounds.origin.x) == bounds.x && int(displayBounds.origin.y) == bounds.y
            && int(displayBounds.size.width) == bounds.w && int(displayBounds.size.height) == bounds.h)
        {
            return displays[index];
        }
    }

    return std::nullopt;
}
#endif
}

bool windowHasHighPixelDensity(SDL_Window *pWindow)
{
    return pWindow != nullptr && (SDL_GetWindowFlags(pWindow) & SDL_WINDOW_HIGH_PIXEL_DENSITY) != 0;
}

RenderSize displayModeRenderSize(const DisplayModeSize &mode, bool highPixelDensity)
{
    if (!highPixelDensity || mode.pixelDensity <= 0.0f)
    {
        return {mode.width, mode.height};
    }

    return {int(std::lround(float(mode.width) * mode.pixelDensity)),
            int(std::lround(float(mode.height) * mode.pixelDensity))};
}

std::optional<size_t> findDisplayModeForRenderSize(
    std::span<const DisplayModeSize> modes, RenderSize size, const DisplayModeSize &desktop, bool highPixelDensity)
{
    // The cursor's size on screen and the distance it moves for a hand movement follow the mode's width in points.
    const auto pointScaleDistance = [&desktop](const DisplayModeSize &mode)
    {
        return desktop.width > 0 && mode.width > 0 ? std::abs(std::log(float(mode.width) / float(desktop.width)))
                                                   : 0.0f;
    };
    std::optional<size_t> best;

    for (size_t index = 0; index < modes.size(); ++index)
    {
        const DisplayModeSize &mode = modes[index];

        if (displayModeRenderSize(mode, highPixelDensity) != size)
        {
            continue;
        }

        if (best)
        {
            const DisplayModeSize &bestMode = modes[*best];
            const float scaleDistance = pointScaleDistance(mode);
            const float bestScaleDistance = pointScaleDistance(bestMode);

            if (scaleDistance > bestScaleDistance
                || (scaleDistance == bestScaleDistance
                    && std::abs(mode.refreshRate - desktop.refreshRate)
                        >= std::abs(bestMode.refreshRate - desktop.refreshRate)))
            {
                continue;
            }
        }

        best = index;
    }

    return best;
}

std::vector<RenderSize> fullscreenRenderSizes(SDL_DisplayID display, bool highPixelDensity)
{
    std::vector<RenderSize> sizes;
    int count = 0;
    SDL_DisplayMode **pModes = SDL_GetFullscreenDisplayModes(display, &count);

    for (int index = 0; pModes != nullptr && index < count; ++index)
    {
        const RenderSize size = displayModeRenderSize(displayModeSize(*pModes[index]), highPixelDensity);

        if (std::find(sizes.begin(), sizes.end(), size) == sizes.end())
        {
            sizes.push_back(size);
        }
    }

    SDL_free(pModes);
    return sizes;
}

bool findFullscreenDisplayMode(
    SDL_DisplayID display, int width, int height, bool highPixelDensity, SDL_DisplayMode &mode)
{
    if (highPixelDensity)
    {
        const SDL_DisplayMode *pDesktopMode = SDL_GetDesktopDisplayMode(display);
        int count = 0;
        SDL_DisplayMode **pModes = SDL_GetFullscreenDisplayModes(display, &count);
        std::vector<DisplayModeSize> modeSizes;

        for (int index = 0; pModes != nullptr && index < count; ++index)
        {
            modeSizes.push_back(displayModeSize(*pModes[index]));
        }

        const std::optional<size_t> index = pDesktopMode != nullptr
            ? findDisplayModeForRenderSize(modeSizes, {width, height}, displayModeSize(*pDesktopMode), true)
            : std::nullopt;

        if (index)
        {
            mode = *pModes[*index];
        }

        SDL_free(pModes);

        if (index)
        {
            return true;
        }
    }

    // A size that no mode renders (another display, an edited settings file): SDL's closest mode.
    return SDL_GetClosestFullscreenDisplayMode(display, width, height, 0.0f, true, &mode);
}

std::optional<RenderSize> nativeDisplayRenderSize(SDL_DisplayID display)
{
#if defined(__APPLE__) && !defined(OPENYAMM_IOS)
    const std::optional<CGDirectDisplayID> coreGraphicsDisplayId = coreGraphicsDisplay(display);

    if (!coreGraphicsDisplayId)
    {
        return std::nullopt;
    }

    // The native mode is listed only with the low resolution duplicates of the HiDPI modes.
    const void *pKeys[] = {kCGDisplayShowDuplicateLowResolutionModes};
    const void *pValues[] = {kCFBooleanTrue};
    CFDictionaryRef options = CFDictionaryCreate(
        nullptr, pKeys, pValues, 1, &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks);
    CFArrayRef modes = CGDisplayCopyAllDisplayModes(*coreGraphicsDisplayId, options);
    CFRelease(options);

    if (modes == nullptr)
    {
        return std::nullopt;
    }

    std::optional<RenderSize> nativeSize;

    for (CFIndex index = 0; index < CFArrayGetCount(modes) && !nativeSize; ++index)
    {
        CGDisplayModeRef pMode = (CGDisplayModeRef)CFArrayGetValueAtIndex(modes, index);

        if ((CGDisplayModeGetIOFlags(pMode) & kDisplayModeNativeFlag) != 0)
        {
            nativeSize = RenderSize{
                int(CGDisplayModeGetPixelWidth(pMode)), int(CGDisplayModeGetPixelHeight(pMode))};
        }
    }

    CFRelease(modes);
    return nativeSize;
#else
    static_cast<void>(display);
    return std::nullopt;
#endif
}
}
