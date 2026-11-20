#include "game/ui/GameplayHeldItemCursor.h"

#include <SDL3/SDL.h>

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
#if !defined(__ANDROID__)
SDL_Cursor *createGauntletCursor(int frame)
{
    SDL_Surface *pSurface = SDL_CreateSurface(32, 36, SDL_PIXELFORMAT_RGBA32);
    if (pSurface == nullptr)
    {
        return nullptr;
    }

    SDL_FillSurfaceRect(pSurface, nullptr, 0);
    const auto color = [&](uint8_t r, uint8_t g, uint8_t b)
    {
        return SDL_MapSurfaceRGBA(pSurface, r, g, b, 255);
    };
    const uint32_t outline = color(24, 28, 35);
    const uint32_t shadow = color(59, 69, 82);
    const uint32_t steel = color(121, 140, 157);
    const uint32_t light = color(208, 220, 226);
    const uint32_t brass = color(161, 127, 72);
    const auto rect = [&](int x, int y, int width, int height, uint32_t fill)
    {
        const SDL_Rect bounds = {x, y, width, height};
        SDL_FillSurfaceRect(pSurface, &bounds, fill);
    };
    const auto plate = [&](int x, int y, int width, int height)
    {
        rect(x, y, width, height, outline);
        rect(x + 1, y + 1, width - 2, height - 2, steel);
        rect(x + 1, y + 1, width - 2, 1, light);
        rect(x + 1, y + 2, 1, height - 3, light);
        rect(x + width - 2, y + 2, 1, height - 3, shadow);
        rect(x + 2, y + height - 2, width - 3, 1, shadow);
    };

    // Original pixel artwork: articulated steel fingers, overlapping thumb and brass-edged cuff.
    // The knuckle hotspot stays fixed while the fingertips curl towards the palm.
    plate(8, 13, 20, 15);
    plate(10, 26, 16, 8);
    rect(11, 27, 14, 1, brass);
    rect(11, 32, 14, 1, brass);
    for (int finger = 0; finger < 4; ++finger)
    {
        const int x = 7 + finger * 5;
        const int top = 4 + (finger == 0 || finger == 3 ? 2 : 0) + frame * 3;
        plate(x, top, 6, 19 - top);
        rect(x + 1, top + 4, 4, 1, shadow);
        if (frame < 2)
        {
            rect(x + 1, top + 7, 4, 1, light);
        }
        plate(x, 16, 6, 5);
    }
    plate(4 + frame, 16 + frame, 7, 10);
    plate(7 + frame, 21, 11, 6);
    rect(18, 23, 7, 1, light);
    rect(21, 28, 2, 2, brass);

    SDL_Cursor *pCursor = SDL_CreateColorCursor(pSurface, 9, 17);
    SDL_DestroySurface(pSurface);
    return pCursor;
}
#endif
} // namespace

void GameplayHeldItemCursor::update(bool holdingItem)
{
#if !defined(__ANDROID__)
    if (!holdingItem)
    {
        if (m_holdingItem)
        {
            SDL_SetCursor(SDL_GetDefaultCursor());
        }
        m_holdingItem = false;
        return;
    }

    if (!m_initializationAttempted)
    {
        m_initializationAttempted = true;
        for (size_t frame = 0; frame < m_frames.size(); ++frame)
        {
            m_frames[frame] = createGauntletCursor(static_cast<int>(frame));
            if (m_frames[frame] == nullptr)
            {
                SDL_Log("Could not create held-item cursor: %s", SDL_GetError());
                shutdown();
                m_initializationAttempted = true;
                return;
            }
        }
    }

    if (m_frames.back() == nullptr)
    {
        return;
    }
    const uint64_t now = SDL_GetTicks();
    if (!m_holdingItem)
    {
        m_grabStartTicks = now;
    }
    m_holdingItem = true;
    const size_t frame = std::min<size_t>((now - m_grabStartTicks) / 55, m_frames.size() - 1);
    // ImGui's SDL backend can restore its arrow each frame; apply after its NewFrame call.
    SDL_SetCursor(m_frames[frame]);
#else
    (void)holdingItem;
#endif
}

void GameplayHeldItemCursor::shutdown()
{
    if (m_holdingItem)
    {
        SDL_SetCursor(SDL_GetDefaultCursor());
    }
    for (SDL_Cursor *&pCursor : m_frames)
    {
        SDL_DestroyCursor(pCursor);
        pCursor = nullptr;
    }
    m_holdingItem = false;
    m_initializationAttempted = false;
}
} // namespace OpenYAMM::Game
