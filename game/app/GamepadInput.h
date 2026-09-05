#pragma once

#include "game/app/KeyboardBindings.h"

#include <SDL3/SDL.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
enum class GamepadButton : uint8_t
{
    South = 0,
    East,
    West,
    North,
    LeftShoulder,
    RightShoulder,
    LeftTrigger,
    RightTrigger,
    Start,
    Back,
    LeftStick,
    RightStick,
    DpadUp,
    DpadDown,
    DpadLeft,
    DpadRight,
    Count
};

constexpr size_t GamepadButtonCount = static_cast<size_t>(GamepadButton::Count);

// Sentinel for a button that drives no action.
constexpr KeyboardAction GamepadUnboundAction = KeyboardAction::Count;

// Sentinel for a button that acts as the Escape key: opens the game menu in gameplay, closes screens otherwise.
constexpr KeyboardAction GamepadMenuAction = static_cast<KeyboardAction>(KeyboardActionCount + 1);

// Full deflection of the right stick looks this many mouse pixels per second at sensitivity 1.0.
constexpr float GamepadLookPixelsPerSecond = 900.0f;

// Full deflection of the right stick moves the emulated cursor this many pixels per second at sensitivity 1.0.
constexpr float GamepadCursorPixelsPerSecond = 1100.0f;

// Trigger axes count as pressed above this fraction of full travel.
constexpr float GamepadTriggerPressThreshold = 0.5f;

struct GamepadButtonDefinition
{
    GamepadButton button = GamepadButton::South;
    std::string_view iniKey;
    std::string_view label;
    KeyboardAction defaultAction = GamepadUnboundAction;
};

size_t gamepadButtonIndex(GamepadButton button);
const std::array<GamepadButtonDefinition, GamepadButtonCount> &gamepadButtonDefinitions();
std::array<KeyboardAction, GamepadButtonCount> createDefaultGamepadActions();

// Action names are the [input] ini keys ("attack", "cast_ready", ...), "menu" (Escape) or "none".
KeyboardAction parseGamepadActionName(const std::string &name);
std::string gamepadActionName(KeyboardAction action);

struct GamepadSettings
{
    bool enabled = true;
    float deadzone = 0.25f;
    float lookSensitivity = 1.0f;
    bool invertLookY = false;
    std::array<KeyboardAction, GamepadButtonCount> actions = createDefaultGamepadActions();

    KeyboardAction action(GamepadButton button) const
    {
        return actions[gamepadButtonIndex(button)];
    }

    void setAction(GamepadButton button, KeyboardAction action)
    {
        actions[gamepadButtonIndex(button)] = action;
    }
};

// Snapshot of the most recent pad state. Axes are -1..1 with SDL's convention (positive Y is down).
struct GamepadState
{
    bool connected = false;
    std::array<bool, GamepadButtonCount> buttons = {};
    float leftX = 0.0f;
    float leftY = 0.0f;
    float rightX = 0.0f;
    float rightY = 0.0f;
};

struct GamepadFrameResult
{
    std::array<bool, KeyboardActionCount> actionHeld = {};
    float lookDeltaX = 0.0f;
    float lookDeltaY = 0.0f;
    bool movementActive = false;
    // Cursor mode only: right stick drives the pointer, A/B click, Back acts as Escape.
    float cursorDeltaX = 0.0f;
    float cursorDeltaY = 0.0f;
    bool cursorLeftHeld = false;
    bool cursorRightHeld = false;
    // Escape is held by a button bound to the menu action, or by Back while in cursor mode.
    bool escapeHeld = false;
};

// Pure mapping from pad state to gameplay actions and look motion for one frame.
// In cursor mode (a menu, inventory, dialog or any screen with a free cursor is open) the right
// stick and the A, B and Back buttons are diverted to pointer emulation instead of look and actions.
GamepadFrameResult mapGamepadFrame(
    const GamepadState &state,
    const GamepadSettings &settings,
    float deltaSeconds,
    bool cursorMode = false);

bool isGamepadSdlEvent(const SDL_Event &event);

// Owns opened SDL gamepads and folds their events into a single GamepadState.
class GamepadInput
{
public:
    GamepadInput() = default;
    ~GamepadInput();
    GamepadInput(const GamepadInput &) = delete;
    GamepadInput &operator=(const GamepadInput &) = delete;

    void handleSdlEvent(const SDL_Event &event);
    const GamepadState &state() const;

private:
    void openGamepad(SDL_JoystickID id);
    void closeGamepad(SDL_JoystickID id);
    void closeAll();

    std::vector<std::pair<SDL_JoystickID, SDL_Gamepad *>> m_gamepads;
    GamepadState m_state = {};
};
} // namespace OpenYAMM::Game
