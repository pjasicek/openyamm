#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct GameplayInputFrame;

// The Talents page of a MAW solo run (devdocs/solo_action/TALENTS.md, the study's layout A): reached through a
// Skills / Talents switch on the character screen's Skills page, it covers the skill lists with the three trees (melee,
// ranged, caster) as rows of icon, name, rank pips and n/max, and a detail card for the talent under the pointer.
// A click on a row learns its next rank; a right click puts an active on the action bar. Nothing shows in other games.
class GameplaySoloTalentsPage
{
public:
    // The switch shows (a MAW solo run on the Skills page of the party's own character screen).
    static bool switchShown(const GameplayScreenRuntime &context);
    // The talents cover the Skills page.
    static bool pageShown(const GameplayScreenRuntime &context);
    static void render(GameplayScreenRuntime &context, int width, int height);
    // The switch and the page's rows; true when the mouse input was theirs (the rest of the screen then ignores it).
    static bool handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input);
    // The talents cover the pointer: the Skills page under them takes no hover.
    static bool coversPointer(const GameplayScreenRuntime &context, const GameplayInputFrame &input);
};
}
