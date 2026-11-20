#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayInteractionController.h"

#include <doctest/doctest.h>

using namespace OpenYAMM::Game;

TEST_CASE("Ctrl and left click steal with a free cursor and with mouse look")
{
    using Controller = GameplayInteractionController;
    GameplayInputFrame input = {};
    input.leftMouseButton.pressed = true;
    input.leftMouseButton.held = true;
    Controller::WorldInteractionPointerPolicy cursor = {};
    cursor.leftMousePressed = true;
    Controller::WorldInteractionPointerPolicy mouseLook = {};
    mouseLook.useCenterGameplayPoint = true;

    // Without Ctrl the click is an ordinary one: an attack with mouse look, a pick with the cursor.
    CHECK_FALSE(Controller::stealClickPressed(input, cursor));
    CHECK_FALSE(Controller::stealClickPressed(input, mouseLook));

    input.keyboardHeld[SDL_SCANCODE_LCTRL] = true;
    CHECK(Controller::stealClickPressed(input, cursor));
    // Mouse look takes the creature in the crosshair, as its attack does.
    CHECK(Controller::stealClickPressed(input, mouseLook));

    input.leftMouseButton.pressed = false;
    CHECK_FALSE(Controller::stealClickPressed(input, mouseLook));
}

TEST_CASE("the left button held after a steal does not attack until it is released")
{
    using Controller = GameplayInteractionController;
    GameplayInputFrame input = {};
    bool latch = false;

    // The frame of the Ctrl click steals, and the frames the button stays down after it hold the attack back:
    // the left button is the attack too, so the next ready member would strike.
    input.leftMouseButton.pressed = true;
    input.leftMouseButton.held = true;
    CHECK(Controller::stealClickHoldsAttack(latch, input, true));
    input.leftMouseButton.pressed = false;
    CHECK(Controller::stealClickHoldsAttack(latch, input, false));
    CHECK(Controller::stealClickHoldsAttack(latch, input, false));

    input.leftMouseButton.held = false;
    CHECK_FALSE(Controller::stealClickHoldsAttack(latch, input, false));

    // An ordinary click attacks as before.
    input.leftMouseButton.pressed = true;
    input.leftMouseButton.held = true;
    CHECK_FALSE(Controller::stealClickHoldsAttack(latch, input, false));
}
