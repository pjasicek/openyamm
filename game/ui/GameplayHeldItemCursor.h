#pragma once

#include <array>
#include <cstdint>

struct SDL_Cursor;

namespace OpenYAMM::Game
{
// Native cursor feedback stays responsive independently of the rendered item icon.
class GameplayHeldItemCursor
{
public:
    void update(bool holdingItem);
    void shutdown();

private:
    std::array<SDL_Cursor *, 3> m_frames = {};
    uint64_t m_grabStartTicks = 0;
    bool m_holdingItem = false;
    bool m_initializationAttempted = false;
};
} // namespace OpenYAMM::Game
