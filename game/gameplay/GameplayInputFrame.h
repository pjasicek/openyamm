#pragma once

#include "game/app/KeyboardBindings.h"

#include <SDL3/SDL.h>

#include <array>
#include <cstdint>
#include <string>

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
    std::string textInput;
    bool mobileJoystickActive = false;
    bool autoRunActive = false;
    bool turnBasedMovementStep = false;
    bool turnBasedPhysicsStep = false;
    float movementSpeedScale = 1.0f;
    bool turboMovementEnabled = true;
    float mobileJoystickBaseX = 0.0f;
    float mobileJoystickBaseY = 0.0f;
    float mobileJoystickKnobX = 0.0f;
    float mobileJoystickKnobY = 0.0f;
    bool mobileTouchDragStarted = false;
    bool mobileTouchDragActive = false;
    bool mobileTouchDragReleased = false;
    float mobileTouchDragStartX = 0.0f;
    float mobileTouchDragStartY = 0.0f;
    GameplayButtonInputState leftMouseButton = {};
    GameplayButtonInputState rightMouseButton = {};
    GameplayButtonInputState middleMouseButton = {};
    std::array<bool, SDL_SCANCODE_COUNT> keyboardHeld = {};
    std::array<uint16_t, SDL_SCANCODE_COUNT> keyboardPressCounts = {};
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

    bool turboMovementHeld() const
    {
        return turboMovementEnabled
            && (isScancodeHeld(SDL_SCANCODE_LCTRL) || isScancodeHeld(SDL_SCANCODE_RCTRL));
    }

    uint16_t scancodePressCount(SDL_Scancode scancode) const
    {
        return scancode > SDL_SCANCODE_UNKNOWN && scancode < SDL_SCANCODE_COUNT
            ? keyboardPressCounts[scancode]
            : 0;
    }

    const GameplayButtonInputState &action(KeyboardAction keyboardAction) const
    {
        return actions[keyboardActionIndex(keyboardAction)];
    }
};
} // namespace OpenYAMM::Game
