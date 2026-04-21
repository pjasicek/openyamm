#include "game/app/GameInputSystem.h"

#include <SDL3/SDL.h>

namespace OpenYAMM::Game
{
namespace
{
GameplayButtonInputState buildButtonState(bool held, bool previousHeld)
{
    GameplayButtonInputState state = {};
    state.held = held;
    state.pressed = held && !previousHeld;
    state.released = !held && previousHeld;
    return state;
}
} // namespace

void GameInputSystem::updateFromEngineInput(
    int screenWidth,
    int screenHeight,
    float mouseWheelDelta,
    const GameSettings &settings)
{
    m_frame = {};
    m_frame.screenWidth = screenWidth;
    m_frame.screenHeight = screenHeight;
    m_frame.mouseWheelDelta = mouseWheelDelta;

    int keyboardStateCount = 0;
    const bool *pKeyboardState = SDL_GetKeyboardState(&keyboardStateCount);

    if (pKeyboardState != nullptr)
    {
        for (int scancode = 0; scancode < keyboardStateCount && scancode < SDL_SCANCODE_COUNT; ++scancode)
        {
            m_frame.keyboardHeld[scancode] = pKeyboardState[scancode];
        }
    }

    float pointerX = 0.0f;
    float pointerY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&pointerX, &pointerY);
    m_frame.pointerX = pointerX;
    m_frame.pointerY = pointerY;

    float relativeMouseX = 0.0f;
    float relativeMouseY = 0.0f;
    SDL_GetRelativeMouseState(&relativeMouseX, &relativeMouseY);
    m_frame.relativeMouseX = relativeMouseX;
    m_frame.relativeMouseY = relativeMouseY;

    const bool leftMouseButtonHeld = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const bool rightMouseButtonHeld = (mouseButtons & SDL_BUTTON_RMASK) != 0;
    const bool middleMouseButtonHeld = (mouseButtons & SDL_BUTTON_MMASK) != 0;
    m_frame.leftMouseButton = buildButtonState(leftMouseButtonHeld, m_previousLeftMouseButtonHeld);
    m_frame.rightMouseButton = buildButtonState(rightMouseButtonHeld, m_previousRightMouseButtonHeld);
    m_frame.middleMouseButton = buildButtonState(middleMouseButtonHeld, m_previousMiddleMouseButtonHeld);

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        const SDL_Scancode scancode = settings.keyboard.binding(definition.action);
        const bool held =
            scancode > SDL_SCANCODE_UNKNOWN
            && scancode < SDL_SCANCODE_COUNT
            && m_frame.keyboardHeld[scancode];
        const bool previousHeld =
            scancode > SDL_SCANCODE_UNKNOWN
            && scancode < SDL_SCANCODE_COUNT
            && m_previousKeyboardHeld[scancode];

        m_frame.actions[keyboardActionIndex(definition.action)] = buildButtonState(held, previousHeld);
    }

    m_previousKeyboardHeld = m_frame.keyboardHeld;
    m_previousLeftMouseButtonHeld = leftMouseButtonHeld;
    m_previousRightMouseButtonHeld = rightMouseButtonHeld;
    m_previousMiddleMouseButtonHeld = middleMouseButtonHeld;
}

const GameplayInputFrame &GameInputSystem::frame() const
{
    return m_frame;
}

void GameInputSystem::resetRelativeMouseMotion()
{
    SDL_GetRelativeMouseState(nullptr, nullptr);
    m_frame.relativeMouseX = 0.0f;
    m_frame.relativeMouseY = 0.0f;
}
} // namespace OpenYAMM::Game
