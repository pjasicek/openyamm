#pragma once

#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"

namespace OpenYAMM::Game
{
// The loot summary MAW's gather key opens on a completed map (loot_summary.yml): the satchels and gold, then a
// scrollable list of every item taken and of those left for lack of room.
class GameplayLootSummaryRenderer
{
public:
    static void render(GameplayScreenRuntime &context, int width, int height);
    // Scrolls the list with the wheel and closes on the Close button; true while the summary is open, as it takes
    // the mouse from the game.
    static bool handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input, int width, int height);
    static void close(GameplayScreenRuntime &context);
};
}
