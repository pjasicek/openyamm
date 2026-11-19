#pragma once

struct SDL_Window;

namespace OpenYAMM::Game
{
// SDL reports the mouse in window coordinates, which are points on macOS and iOS, while the game draws and hit-tests
// in the window's pixels. The pixels per window unit: 2 on a Retina display, 1 elsewhere and without a window.
float windowPixelDensity(SDL_Window *pWindow);

// Moves the system cursor to the middle of the window. False when the window has no size.
bool warpMouseToWindowCenter(SDL_Window *pWindow);
}
