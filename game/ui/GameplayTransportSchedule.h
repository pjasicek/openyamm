#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct GameplayInputFrame;

// A stable's or boat's Schedule popup over the house dialogue
// (level_generation/ui/transport_schedule_20261104/README.md): the week's departures from Monday to Sunday with today
// marked. A click on a day selects its departure (a second click on a day of several picks the next one, a click on a
// name picks that one); the footer shows the departure, the days on the road, the arrival, the fare and the food the
// wait costs, and its button waits for the day and travels.
namespace GameplayTransportSchedule
{
// Whether the popup is open over the active house dialogue; a stale one (another dialogue) is closed.
bool isOpen(GameplayScreenRuntime &context);
// Draws the popup above the dialogue.
void render(GameplayScreenRuntime &context, int width, int height);
// The popup's clicks and keys while it is open; it takes all of the dialogue's input.
void handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input);
}
}
