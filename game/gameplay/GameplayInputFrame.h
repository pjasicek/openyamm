#pragma once

#include "game/app/KeyboardBindings.h"

#include <SDL3/SDL.h>

#include <array>

namespace OpenYAMM::Game
{
struct GameplayButtonInputState
{
    bool held = false;
    bool pressed = false;
    bool released = false;
};

struct GameplayInputFrame
{
    int screenWidth = 0;
    int screenHeight = 0;
    float mouseWheelDelta = 0.0f;
    float pointerX = 0.0f;
    float pointerY = 0.0f;
    float relativeMouseX = 0.0f;
    float relativeMouseY = 0.0f;
    GameplayButtonInputState leftMouseButton = {};
    GameplayButtonInputState rightMouseButton = {};
    GameplayButtonInputState middleMouseButton = {};
    std::array<bool, SDL_SCANCODE_COUNT> keyboardHeld = {};
    std::array<GameplayButtonInputState, KeyboardActionCount> actions = {};

    const bool *keyboardState() const
    {
        return keyboardHeld.data();
    }

    bool isScancodeHeld(SDL_Scancode scancode) const
    {
        return scancode > SDL_SCANCODE_UNKNOWN
            && scancode < SDL_SCANCODE_COUNT
            && keyboardHeld[scancode];
    }

    const GameplayButtonInputState &action(KeyboardAction keyboardAction) const
    {
        return actions[keyboardActionIndex(keyboardAction)];
    }
};
} // namespace OpenYAMM::Game
