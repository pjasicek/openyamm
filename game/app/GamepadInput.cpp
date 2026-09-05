#include "game/app/GamepadInput.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
const std::array<GamepadButtonDefinition, GamepadButtonCount> GamepadButtons = {{
    {GamepadButton::South, "a", "A", KeyboardAction::Trigger},
    {GamepadButton::East, "b", "B", KeyboardAction::Combat},
    {GamepadButton::West, "x", "X", KeyboardAction::Use},
    {GamepadButton::North, "y", "Y", KeyboardAction::Cast},
    {GamepadButton::LeftShoulder, "lb", "LB", KeyboardAction::CastReady},
    {GamepadButton::RightShoulder, "rb", "RB", KeyboardAction::CharCycle},
    {GamepadButton::LeftTrigger, "lt", "LT", KeyboardAction::Jump},
    {GamepadButton::RightTrigger, "rt", "RT", KeyboardAction::Attack},
    {GamepadButton::Start, "start", "Start", GamepadMenuAction},
    {GamepadButton::Back, "back", "Back", KeyboardAction::Quest},
    {GamepadButton::LeftStick, "l3", "L3", KeyboardAction::AlwaysRun},
    {GamepadButton::RightStick, "r3", "R3", KeyboardAction::QuickRef},
    {GamepadButton::DpadUp, "dpad_up", "D-Pad Up", KeyboardAction::Forward},
    {GamepadButton::DpadDown, "dpad_down", "D-Pad Down", KeyboardAction::Backward},
    {GamepadButton::DpadLeft, "dpad_left", "D-Pad Left", KeyboardAction::Left},
    {GamepadButton::DpadRight, "dpad_right", "D-Pad Right", KeyboardAction::Right},
}};

std::string normalizeActionName(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        if (character == ' ' || character == '-' || character == '_')
        {
            continue;
        }

        result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return result;
}

float axisToFloat(int16_t value)
{
    return value < 0 ? static_cast<float>(value) / 32768.0f : static_cast<float>(value) / 32767.0f;
}

// Rescales an axis so the deadzone edge reads as 0 and full deflection as 1.
float applyDeadzone(float value, float deadzone)
{
    const float magnitude = std::fabs(value);

    if (magnitude <= deadzone)
    {
        return 0.0f;
    }

    const float range = 1.0f - deadzone;
    const float scaled = range > 0.0f ? (magnitude - deadzone) / range : 1.0f;
    return std::copysign(std::min(scaled, 1.0f), value);
}

bool sdlButtonToGamepadButton(int sdlButton, GamepadButton &result)
{
    switch (sdlButton)
    {
    case SDL_GAMEPAD_BUTTON_SOUTH: result = GamepadButton::South; return true;
    case SDL_GAMEPAD_BUTTON_EAST: result = GamepadButton::East; return true;
    case SDL_GAMEPAD_BUTTON_WEST: result = GamepadButton::West; return true;
    case SDL_GAMEPAD_BUTTON_NORTH: result = GamepadButton::North; return true;
    case SDL_GAMEPAD_BUTTON_LEFT_SHOULDER: result = GamepadButton::LeftShoulder; return true;
    case SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER: result = GamepadButton::RightShoulder; return true;
    case SDL_GAMEPAD_BUTTON_START: result = GamepadButton::Start; return true;
    case SDL_GAMEPAD_BUTTON_BACK: result = GamepadButton::Back; return true;
    case SDL_GAMEPAD_BUTTON_LEFT_STICK: result = GamepadButton::LeftStick; return true;
    case SDL_GAMEPAD_BUTTON_RIGHT_STICK: result = GamepadButton::RightStick; return true;
    case SDL_GAMEPAD_BUTTON_DPAD_UP: result = GamepadButton::DpadUp; return true;
    case SDL_GAMEPAD_BUTTON_DPAD_DOWN: result = GamepadButton::DpadDown; return true;
    case SDL_GAMEPAD_BUTTON_DPAD_LEFT: result = GamepadButton::DpadLeft; return true;
    case SDL_GAMEPAD_BUTTON_DPAD_RIGHT: result = GamepadButton::DpadRight; return true;
    default: return false;
    }
}
} // namespace

size_t gamepadButtonIndex(GamepadButton button)
{
    return static_cast<size_t>(button);
}

const std::array<GamepadButtonDefinition, GamepadButtonCount> &gamepadButtonDefinitions()
{
    return GamepadButtons;
}

std::array<KeyboardAction, GamepadButtonCount> createDefaultGamepadActions()
{
    std::array<KeyboardAction, GamepadButtonCount> actions = {};
    actions.fill(GamepadUnboundAction);

    for (const GamepadButtonDefinition &definition : GamepadButtons)
    {
        actions[gamepadButtonIndex(definition.button)] = definition.defaultAction;
    }

    return actions;
}

KeyboardAction parseGamepadActionName(const std::string &name)
{
    const std::string normalized = normalizeActionName(name);

    if (normalized.empty() || normalized == "none" || normalized == "unbound")
    {
        return GamepadUnboundAction;
    }

    if (normalized == "menu" || normalized == "escape")
    {
        return GamepadMenuAction;
    }

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        if (normalizeActionName(std::string(definition.iniKey)) == normalized
            || normalizeActionName(std::string(definition.label)) == normalized)
        {
            return definition.action;
        }
    }

    return GamepadUnboundAction;
}

std::string gamepadActionName(KeyboardAction action)
{
    if (action == GamepadUnboundAction)
    {
        return "none";
    }

    if (action == GamepadMenuAction)
    {
        return "menu";
    }

    return std::string(keyboardBindingDefinition(action).iniKey);
}

GamepadFrameResult mapGamepadFrame(
    const GamepadState &state,
    const GamepadSettings &settings,
    float deltaSeconds,
    bool cursorMode)
{
    GamepadFrameResult result = {};

    if (!state.connected || !settings.enabled)
    {
        return result;
    }

    const float deadzone = std::clamp(settings.deadzone, 0.0f, 0.95f);
    const auto hold =
        [&result](KeyboardAction action)
        {
            if (action == GamepadMenuAction)
            {
                result.escapeHeld = true;
            }
            else if (action != GamepadUnboundAction)
            {
                result.actionHeld[keyboardActionIndex(action)] = true;
            }
        };

    const float moveX = applyDeadzone(state.leftX, deadzone);
    const float moveY = applyDeadzone(state.leftY, deadzone);

    if (moveY < 0.0f)
    {
        hold(KeyboardAction::Forward);
    }
    else if (moveY > 0.0f)
    {
        hold(KeyboardAction::Backward);
    }

    if (moveX < 0.0f)
    {
        hold(KeyboardAction::Left);
    }
    else if (moveX > 0.0f)
    {
        hold(KeyboardAction::Right);
    }

    for (const GamepadButtonDefinition &definition : GamepadButtons)
    {
        if (!state.buttons[gamepadButtonIndex(definition.button)])
        {
            continue;
        }

        if (cursorMode)
        {
            if (definition.button == GamepadButton::South)
            {
                result.cursorLeftHeld = true;
                continue;
            }

            if (definition.button == GamepadButton::East)
            {
                result.cursorRightHeld = true;
                continue;
            }

            if (definition.button == GamepadButton::Back)
            {
                result.escapeHeld = true;
                continue;
            }
        }

        hold(settings.action(definition.button));
    }

    result.movementActive =
        result.actionHeld[keyboardActionIndex(KeyboardAction::Forward)]
        || result.actionHeld[keyboardActionIndex(KeyboardAction::Backward)]
        || result.actionHeld[keyboardActionIndex(KeyboardAction::Left)]
        || result.actionHeld[keyboardActionIndex(KeyboardAction::Right)];

    const float sensitivity = std::max(settings.lookSensitivity, 0.0f) * std::max(deltaSeconds, 0.0f);
    const float rightX = applyDeadzone(state.rightX, deadzone);
    const float rightY = applyDeadzone(state.rightY, deadzone);

    if (cursorMode)
    {
        const float cursorScale = GamepadCursorPixelsPerSecond * sensitivity;
        result.cursorDeltaX = rightX * cursorScale;
        result.cursorDeltaY = rightY * cursorScale;
    }
    else
    {
        const float lookScale = GamepadLookPixelsPerSecond * sensitivity;
        result.lookDeltaX = rightX * lookScale;
        result.lookDeltaY = rightY * lookScale * (settings.invertLookY ? -1.0f : 1.0f);
    }

    return result;
}

bool isGamepadSdlEvent(const SDL_Event &event)
{
    return event.type == SDL_EVENT_GAMEPAD_ADDED
        || event.type == SDL_EVENT_GAMEPAD_REMOVED
        || event.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN
        || event.type == SDL_EVENT_GAMEPAD_BUTTON_UP
        || event.type == SDL_EVENT_GAMEPAD_AXIS_MOTION;
}

GamepadInput::~GamepadInput()
{
    closeAll();
}

void GamepadInput::handleSdlEvent(const SDL_Event &event)
{
    switch (event.type)
    {
    case SDL_EVENT_GAMEPAD_ADDED:
        openGamepad(event.gdevice.which);
        return;

    case SDL_EVENT_GAMEPAD_REMOVED:
        closeGamepad(event.gdevice.which);
        return;

    case SDL_EVENT_GAMEPAD_BUTTON_DOWN:
    case SDL_EVENT_GAMEPAD_BUTTON_UP:
    {
        GamepadButton button = GamepadButton::South;

        if (sdlButtonToGamepadButton(event.gbutton.button, button))
        {
            m_state.connected = true;
            m_state.buttons[gamepadButtonIndex(button)] = event.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN;
        }

        return;
    }

    case SDL_EVENT_GAMEPAD_AXIS_MOTION:
    {
        const float value = axisToFloat(event.gaxis.value);
        m_state.connected = true;

        switch (event.gaxis.axis)
        {
        case SDL_GAMEPAD_AXIS_LEFTX: m_state.leftX = value; break;
        case SDL_GAMEPAD_AXIS_LEFTY: m_state.leftY = value; break;
        case SDL_GAMEPAD_AXIS_RIGHTX: m_state.rightX = value; break;
        case SDL_GAMEPAD_AXIS_RIGHTY: m_state.rightY = value; break;
        case SDL_GAMEPAD_AXIS_LEFT_TRIGGER:
            m_state.buttons[gamepadButtonIndex(GamepadButton::LeftTrigger)] = value >= GamepadTriggerPressThreshold;
            break;
        case SDL_GAMEPAD_AXIS_RIGHT_TRIGGER:
            m_state.buttons[gamepadButtonIndex(GamepadButton::RightTrigger)] = value >= GamepadTriggerPressThreshold;
            break;
        default: break;
        }

        return;
    }

    default:
        return;
    }
}

const GamepadState &GamepadInput::state() const
{
    return m_state;
}

void GamepadInput::openGamepad(SDL_JoystickID id)
{
    for (const auto &[openId, pGamepad] : m_gamepads)
    {
        if (openId == id)
        {
            return;
        }
    }

    SDL_Gamepad *pGamepad = SDL_OpenGamepad(id);

    if (pGamepad == nullptr)
    {
        std::cerr << "GamepadInput: failed to open gamepad " << id << ": " << SDL_GetError() << '\n';
        return;
    }

    const char *pName = SDL_GetGamepadName(pGamepad);
    std::cout << "GamepadInput: opened gamepad " << id << " (" << (pName != nullptr ? pName : "unknown") << ")"
              << std::endl;
    m_gamepads.emplace_back(id, pGamepad);
    m_state.connected = true;
}

void GamepadInput::closeGamepad(SDL_JoystickID id)
{
    const auto it = std::find_if(
        m_gamepads.begin(),
        m_gamepads.end(),
        [id](const auto &entry) { return entry.first == id; });

    if (it == m_gamepads.end())
    {
        return;
    }

    SDL_CloseGamepad(it->second);
    m_gamepads.erase(it);

    if (m_gamepads.empty())
    {
        // Drop any held state so a yanked pad does not leave the party walking.
        m_state = {};
    }
}

void GamepadInput::closeAll()
{
    for (auto &[id, pGamepad] : m_gamepads)
    {
        SDL_CloseGamepad(pGamepad);
    }

    m_gamepads.clear();
    m_state = {};
}
} // namespace OpenYAMM::Game
