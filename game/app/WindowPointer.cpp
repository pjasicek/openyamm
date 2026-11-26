#include "game/app/WindowPointer.h"

#include <SDL3/SDL.h>

namespace OpenYAMM::Game
{
float windowPixelDensity(SDL_Window *pWindow)
{
    const float density = pWindow != nullptr ? SDL_GetWindowPixelDensity(pWindow) : 0.0f;
    return density > 0.0f ? density : 1.0f;
}

bool warpMouseToWindowCenter(SDL_Window *pWindow)
{
    int windowWidth = 0;
    int windowHeight = 0;

    if (pWindow == nullptr || !SDL_GetWindowSize(pWindow, &windowWidth, &windowHeight) || windowWidth <= 0
        || windowHeight <= 0)
    {
        return false;
    }

    SDL_WarpMouseInWindow(pWindow, float(windowWidth) * 0.5f, float(windowHeight) * 0.5f);
    return true;
}
}
