#pragma once

#include <SDL3/SDL_video.h>

#include <cstddef>
#include <optional>
#include <span>
#include <vector>

namespace OpenYAMM::Engine
{
// Apple windows render in device pixels (SDL_WINDOW_HIGH_PIXEL_DENSITY): on a Retina display the drawable is the
// window's size in points times the display's backing scale, and display modes are listed in points with a density.
#if defined(__APPLE__)
constexpr bool HighPixelDensityWindows = true;
#else
constexpr bool HighPixelDensityWindows = false;
#endif

struct RenderSize
{
    int width = 0;
    int height = 0;

    bool operator==(const RenderSize &) const = default;
};

// The parts of an SDL_DisplayMode that choosing one needs: its size in window coordinates (points on macOS).
struct DisplayModeSize
{
    int width = 0;
    int height = 0;
    float pixelDensity = 1.0f;
    float refreshRate = 0.0f;
};

// The size of the image a fullscreen mode renders: its pixels for a high pixel density window, its listed size
// otherwise.
RenderSize displayModeRenderSize(const DisplayModeSize &mode, bool highPixelDensity);

// The mode that renders exactly the given size. Several can (on macOS 3456x2234 pixels is both 3456x2234 points at 1x
// and 1728x1117 points at 2x): the one nearest the desktop's size in points keeps the system cursor's size and speed
// nearest the desktop's, then the refresh rate nearest the desktop's.
std::optional<size_t> findDisplayModeForRenderSize(
    std::span<const DisplayModeSize> modes, RenderSize size, const DisplayModeSize &desktop, bool highPixelDensity);

// The render sizes of a display's fullscreen modes, each once.
std::vector<RenderSize> fullscreenRenderSizes(SDL_DisplayID display);

// The fullscreen mode for a render size: the mode that renders exactly that size, else SDL's closest mode.
bool findFullscreenDisplayMode(SDL_DisplayID display, int width, int height, SDL_DisplayMode &mode);

// The size of the display's panel in pixels (macOS), the render size that maps one to one onto it.
std::optional<RenderSize> nativeDisplayRenderSize(SDL_DisplayID display);
}
