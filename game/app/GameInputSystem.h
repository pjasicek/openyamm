#pragma once

#include "game/app/GameSettings.h"
#include "game/gameplay/GameplayInputFrame.h"

#include <array>

namespace OpenYAMM::Game
{
class GameInputSystem
{
public:
    void updateFromEngineInput(
        int screenWidth,
        int screenHeight,
        float mouseWheelDelta,
        const GameSettings &settings);

    const GameplayInputFrame &frame() const;
    void resetRelativeMouseMotion();

private:
    GameplayInputFrame m_frame = {};
    std::array<bool, SDL_SCANCODE_COUNT> m_previousKeyboardHeld = {};
    bool m_previousLeftMouseButtonHeld = false;
    bool m_previousRightMouseButtonHeld = false;
    bool m_previousMiddleMouseButtonHeld = false;
};
} // namespace OpenYAMM::Game
