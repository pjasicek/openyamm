#include "doctest/doctest.h"

#include "game/app/GamepadInput.h"
#include "game/app/GameSettings.h"

#include <filesystem>
#include <fstream>

using namespace OpenYAMM::Game;

namespace
{
GamepadState connectedState()
{
    GamepadState state = {};
    state.connected = true;
    return state;
}
} // namespace

TEST_CASE("gamepad mapping ignores a disconnected pad")
{
    GamepadState state = {};
    state.leftY = -1.0f;
    state.buttons[gamepadButtonIndex(GamepadButton::South)] = true;

    const GamepadFrameResult result = mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f);

    CHECK_FALSE(result.actionHeld[keyboardActionIndex(KeyboardAction::Forward)]);
    CHECK_FALSE(result.actionHeld[keyboardActionIndex(KeyboardAction::Trigger)]);
    CHECK(result.lookDeltaX == 0.0f);
}

TEST_CASE("gamepad mapping ignores a disabled pad")
{
    GamepadState state = connectedState();
    state.leftY = -1.0f;
    GamepadSettings settings = {};
    settings.enabled = false;

    const GamepadFrameResult result = mapGamepadFrame(state, settings, 1.0f / 60.0f);

    CHECK_FALSE(result.actionHeld[keyboardActionIndex(KeyboardAction::Forward)]);
}

TEST_CASE("left stick inside the deadzone does not move")
{
    GamepadState state = connectedState();
    state.leftX = 0.1f;
    state.leftY = -0.1f;

    const GamepadFrameResult result = mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f);

    CHECK_FALSE(result.actionHeld[keyboardActionIndex(KeyboardAction::Forward)]);
    CHECK_FALSE(result.actionHeld[keyboardActionIndex(KeyboardAction::Right)]);
    CHECK_FALSE(result.movementActive);
}

TEST_CASE("left stick maps to forward backward left and right")
{
    GamepadSettings settings = {};

    GamepadState state = connectedState();
    state.leftY = -0.9f;
    GamepadFrameResult result = mapGamepadFrame(state, settings, 1.0f / 60.0f);
    CHECK(result.actionHeld[keyboardActionIndex(KeyboardAction::Forward)]);
    CHECK_FALSE(result.actionHeld[keyboardActionIndex(KeyboardAction::Backward)]);
    CHECK(result.movementActive);

    state = connectedState();
    state.leftY = 0.9f;
    result = mapGamepadFrame(state, settings, 1.0f / 60.0f);
    CHECK(result.actionHeld[keyboardActionIndex(KeyboardAction::Backward)]);

    state = connectedState();
    state.leftX = -0.9f;
    result = mapGamepadFrame(state, settings, 1.0f / 60.0f);
    CHECK(result.actionHeld[keyboardActionIndex(KeyboardAction::Left)]);
    CHECK_FALSE(result.actionHeld[keyboardActionIndex(KeyboardAction::Right)]);

    state = connectedState();
    state.leftX = 0.9f;
    result = mapGamepadFrame(state, settings, 1.0f / 60.0f);
    CHECK(result.actionHeld[keyboardActionIndex(KeyboardAction::Right)]);
}

TEST_CASE("diagonal left stick holds two movement actions")
{
    GamepadState state = connectedState();
    state.leftX = 0.7f;
    state.leftY = -0.7f;

    const GamepadFrameResult result = mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f);

    CHECK(result.actionHeld[keyboardActionIndex(KeyboardAction::Forward)]);
    CHECK(result.actionHeld[keyboardActionIndex(KeyboardAction::Right)]);
}

TEST_CASE("dpad defaults to movement")
{
    GamepadState state = connectedState();
    state.buttons[gamepadButtonIndex(GamepadButton::DpadUp)] = true;
    state.buttons[gamepadButtonIndex(GamepadButton::DpadLeft)] = true;

    const GamepadFrameResult result = mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f);

    CHECK(result.actionHeld[keyboardActionIndex(KeyboardAction::Forward)]);
    CHECK(result.actionHeld[keyboardActionIndex(KeyboardAction::Left)]);
    CHECK(result.movementActive);
}

TEST_CASE("right stick produces look motion scaled by time and sensitivity")
{
    GamepadSettings settings = {};
    settings.lookSensitivity = 1.0f;

    GamepadState state = connectedState();
    state.rightX = 1.0f;
    const GamepadFrameResult full = mapGamepadFrame(state, settings, 0.5f);
    CHECK(full.lookDeltaX == doctest::Approx(GamepadLookPixelsPerSecond * 0.5f));
    CHECK(full.lookDeltaY == 0.0f);

    const GamepadFrameResult half = mapGamepadFrame(state, settings, 0.25f);
    CHECK(half.lookDeltaX == doctest::Approx(full.lookDeltaX * 0.5f));

    settings.lookSensitivity = 2.0f;
    const GamepadFrameResult fast = mapGamepadFrame(state, settings, 0.5f);
    CHECK(fast.lookDeltaX == doctest::Approx(full.lookDeltaX * 2.0f));
}

TEST_CASE("right stick inside the deadzone does not look and deadzone edge is rescaled to zero")
{
    GamepadSettings settings = {};
    settings.deadzone = 0.25f;

    GamepadState state = connectedState();
    state.rightX = 0.2f;
    CHECK(mapGamepadFrame(state, settings, 1.0f).lookDeltaX == 0.0f);

    state.rightX = 0.25f;
    CHECK(mapGamepadFrame(state, settings, 1.0f).lookDeltaX == doctest::Approx(0.0f));

    state.rightX = 0.625f;
    CHECK(mapGamepadFrame(state, settings, 1.0f).lookDeltaX == doctest::Approx(GamepadLookPixelsPerSecond * 0.5f));
}

TEST_CASE("right stick vertical look follows the invert setting")
{
    GamepadSettings settings = {};
    GamepadState state = connectedState();
    state.rightY = 1.0f;

    CHECK(mapGamepadFrame(state, settings, 1.0f).lookDeltaY > 0.0f);

    settings.invertLookY = true;
    CHECK(mapGamepadFrame(state, settings, 1.0f).lookDeltaY < 0.0f);
}

TEST_CASE("buttons map to their bound actions and unbound buttons do nothing")
{
    GamepadSettings settings = {};
    settings.setAction(GamepadButton::South, KeyboardAction::Trigger);
    settings.setAction(GamepadButton::East, GamepadUnboundAction);

    GamepadState state = connectedState();
    state.buttons[gamepadButtonIndex(GamepadButton::South)] = true;
    state.buttons[gamepadButtonIndex(GamepadButton::East)] = true;

    const GamepadFrameResult result = mapGamepadFrame(state, settings, 1.0f / 60.0f);

    CHECK(result.actionHeld[keyboardActionIndex(KeyboardAction::Trigger)]);
    int heldCount = 0;
    for (bool held : result.actionHeld)
    {
        heldCount += held ? 1 : 0;
    }
    CHECK(heldCount == 1);
}

TEST_CASE("default layout binds the documented actions")
{
    const GamepadSettings settings = {};

    CHECK(settings.action(GamepadButton::RightTrigger) == KeyboardAction::Attack);
    CHECK(settings.action(GamepadButton::LeftTrigger) == KeyboardAction::Jump);
    CHECK(settings.action(GamepadButton::South) == KeyboardAction::Trigger);
    CHECK(settings.action(GamepadButton::East) == KeyboardAction::Combat);
    CHECK(settings.action(GamepadButton::West) == KeyboardAction::Use);
    CHECK(settings.action(GamepadButton::North) == KeyboardAction::Cast);
    CHECK(settings.action(GamepadButton::LeftShoulder) == KeyboardAction::CastReady);
    CHECK(settings.action(GamepadButton::RightShoulder) == KeyboardAction::CharCycle);
    CHECK(settings.action(GamepadButton::Start) == GamepadMenuAction);
    CHECK(settings.action(GamepadButton::Back) == KeyboardAction::Quest);
    CHECK(settings.action(GamepadButton::LeftStick) == KeyboardAction::AlwaysRun);
    CHECK(settings.action(GamepadButton::RightStick) == KeyboardAction::QuickRef);
}

TEST_CASE("gamepad action names round trip and accept none")
{
    CHECK(parseGamepadActionName("attack") == KeyboardAction::Attack);
    CHECK(parseGamepadActionName("Cast Ready") == KeyboardAction::CastReady);
    CHECK(parseGamepadActionName("cast_ready") == KeyboardAction::CastReady);
    CHECK(parseGamepadActionName("none") == GamepadUnboundAction);
    CHECK(parseGamepadActionName("") == GamepadUnboundAction);
    CHECK(parseGamepadActionName("bogus") == GamepadUnboundAction);
    CHECK(gamepadActionName(KeyboardAction::CastReady) == "cast_ready");
    CHECK(gamepadActionName(GamepadUnboundAction) == "none");
    CHECK(parseGamepadActionName("menu") == GamepadMenuAction);
    CHECK(parseGamepadActionName("escape") == GamepadMenuAction);
    CHECK(gamepadActionName(GamepadMenuAction) == "menu");
}

TEST_CASE("start opens the menu as escape in gameplay and back only closes in cursor mode")
{
    GamepadState state = connectedState();
    state.buttons[gamepadButtonIndex(GamepadButton::Start)] = true;
    CHECK(mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f, false).escapeHeld);
    CHECK(mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f, true).escapeHeld);

    state = connectedState();
    state.buttons[gamepadButtonIndex(GamepadButton::Back)] = true;
    const GamepadFrameResult gameplay = mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f, false);
    CHECK_FALSE(gameplay.escapeHeld);
    CHECK(gameplay.actionHeld[keyboardActionIndex(KeyboardAction::Quest)]);
    CHECK(mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f, true).escapeHeld);
}

TEST_CASE("gamepad settings load from and save to the ini gamepad section")
{
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "openyamm_gamepad_settings_test.ini";

    {
        std::ofstream output(path);
        output << "[gamepad]\n"
               << "enabled=false\n"
               << "deadzone=0.4\n"
               << "look_sensitivity=1.5\n"
               << "invert_look_y=true\n"
               << "a=attack\n"
               << "rt=none\n"
               << "dpad_up=look_up\n";
    }

    std::string error;
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE(loaded.has_value());
    CHECK_FALSE(loaded->gamepad.enabled);
    CHECK(loaded->gamepad.deadzone == doctest::Approx(0.4f));
    CHECK(loaded->gamepad.lookSensitivity == doctest::Approx(1.5f));
    CHECK(loaded->gamepad.invertLookY);
    CHECK(loaded->gamepad.action(GamepadButton::South) == KeyboardAction::Attack);
    CHECK(loaded->gamepad.action(GamepadButton::RightTrigger) == GamepadUnboundAction);
    CHECK(loaded->gamepad.action(GamepadButton::DpadUp) == KeyboardAction::LookUp);
    CHECK(loaded->gamepad.action(GamepadButton::East) == KeyboardAction::Combat);

    REQUIRE(saveGameSettings(path, *loaded, error));
    const std::optional<GameSettings> reloaded = loadGameSettings(path, error);
    REQUIRE(reloaded.has_value());
    CHECK_FALSE(reloaded->gamepad.enabled);
    CHECK(reloaded->gamepad.deadzone == doctest::Approx(0.4f));
    CHECK(reloaded->gamepad.action(GamepadButton::South) == KeyboardAction::Attack);
    CHECK(reloaded->gamepad.action(GamepadButton::RightTrigger) == GamepadUnboundAction);
    CHECK(reloaded->gamepad.action(GamepadButton::DpadUp) == KeyboardAction::LookUp);

    std::filesystem::remove(path);
}

TEST_CASE("gamepad input tracks SDL button and axis events")
{
    GamepadInput input;

    SDL_Event buttonDown = {};
    buttonDown.type = SDL_EVENT_GAMEPAD_BUTTON_DOWN;
    buttonDown.gbutton.which = 7;
    buttonDown.gbutton.button = SDL_GAMEPAD_BUTTON_SOUTH;
    buttonDown.gbutton.down = true;
    input.handleSdlEvent(buttonDown);
    CHECK(input.state().buttons[gamepadButtonIndex(GamepadButton::South)]);

    SDL_Event buttonUp = buttonDown;
    buttonUp.type = SDL_EVENT_GAMEPAD_BUTTON_UP;
    buttonUp.gbutton.down = false;
    input.handleSdlEvent(buttonUp);
    CHECK_FALSE(input.state().buttons[gamepadButtonIndex(GamepadButton::South)]);

    SDL_Event axis = {};
    axis.type = SDL_EVENT_GAMEPAD_AXIS_MOTION;
    axis.gaxis.which = 7;
    axis.gaxis.axis = SDL_GAMEPAD_AXIS_LEFTY;
    axis.gaxis.value = -32768;
    input.handleSdlEvent(axis);
    CHECK(input.state().leftY == doctest::Approx(-1.0f));

    axis.gaxis.axis = SDL_GAMEPAD_AXIS_RIGHT_TRIGGER;
    axis.gaxis.value = 32767;
    input.handleSdlEvent(axis);
    CHECK(input.state().buttons[gamepadButtonIndex(GamepadButton::RightTrigger)]);

    axis.gaxis.value = 0;
    input.handleSdlEvent(axis);
    CHECK_FALSE(input.state().buttons[gamepadButtonIndex(GamepadButton::RightTrigger)]);
}

TEST_CASE("cursor mode diverts the right stick to pointer motion instead of look")
{
    GamepadSettings settings = {};
    GamepadState state = connectedState();
    state.rightX = 1.0f;
    state.rightY = -1.0f;

    const GamepadFrameResult cursor = mapGamepadFrame(state, settings, 0.5f, true);
    CHECK(cursor.lookDeltaX == 0.0f);
    CHECK(cursor.lookDeltaY == 0.0f);
    CHECK(cursor.cursorDeltaX == doctest::Approx(GamepadCursorPixelsPerSecond * 0.5f));
    CHECK(cursor.cursorDeltaY == doctest::Approx(-GamepadCursorPixelsPerSecond * 0.5f));

    settings.invertLookY = true;
    const GamepadFrameResult inverted = mapGamepadFrame(state, settings, 0.5f, true);
    CHECK(inverted.cursorDeltaY == doctest::Approx(cursor.cursorDeltaY));

    const GamepadFrameResult gameplay = mapGamepadFrame(state, settings, 0.5f, false);
    CHECK(gameplay.cursorDeltaX == 0.0f);
    CHECK(gameplay.lookDeltaX != 0.0f);
}

TEST_CASE("cursor mode turns A B and Back into clicks and escape without firing their actions")
{
    GamepadState state = connectedState();
    state.buttons[gamepadButtonIndex(GamepadButton::South)] = true;
    state.buttons[gamepadButtonIndex(GamepadButton::East)] = true;
    state.buttons[gamepadButtonIndex(GamepadButton::Back)] = true;
    state.buttons[gamepadButtonIndex(GamepadButton::North)] = true;

    const GamepadFrameResult cursor = mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f, true);
    CHECK(cursor.cursorLeftHeld);
    CHECK(cursor.cursorRightHeld);
    CHECK(cursor.escapeHeld);
    CHECK_FALSE(cursor.actionHeld[keyboardActionIndex(KeyboardAction::Trigger)]);
    CHECK_FALSE(cursor.actionHeld[keyboardActionIndex(KeyboardAction::Combat)]);
    CHECK_FALSE(cursor.actionHeld[keyboardActionIndex(KeyboardAction::Quest)]);
    CHECK(cursor.actionHeld[keyboardActionIndex(KeyboardAction::Cast)]);

    const GamepadFrameResult gameplay = mapGamepadFrame(state, GamepadSettings{}, 1.0f / 60.0f, false);
    CHECK_FALSE(gameplay.cursorLeftHeld);
    CHECK(gameplay.actionHeld[keyboardActionIndex(KeyboardAction::Trigger)]);
    CHECK(gameplay.actionHeld[keyboardActionIndex(KeyboardAction::Combat)]);
}
