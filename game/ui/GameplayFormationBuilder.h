#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct GameplayInputFrame;

// The MM9 formation builder (devdocs/mm9/MM9_HIRELINGS_PLAN.md phase 10; the accepted design
// level_generation/ui/mm9_formation_20261106, laid out by mm9_formation.yml): MM9's 3 x 3 grid of the members and
// hirelings over the dimmed, paused game. A face is dragged onto an empty cell (no swaps); pointing at one shows the
// name; Accept applies the arrangement unless someone stands behind an empty cell (the refusal is said in the
// instruction line and the builder stays open); Cancel or Escape keep the old one. Opened by the button under the
// minimap (gameplay.yml Mm9FormationButton) and the Party Formation key, in a world with world.yml formations only.
namespace GameplayFormationBuilder
{
// The world has formations (the same capability as the formation targeting).
bool available(const GameplayScreenRuntime &context);
bool isOpen(const GameplayScreenRuntime &context);
// Starts editing a copy of the party's formation; nothing outside a formations world.
void open(GameplayScreenRuntime &context);
// Closes without applying.
void close(GameplayScreenRuntime &context);
// Applies the arrangement and closes; refused (false, stays open) while someone stands behind an empty cell.
bool accept(GameplayScreenRuntime &context);

// The button under the minimap, on the plain gameplay HUD.
void renderButton(GameplayScreenRuntime &context, int width, int height);
bool buttonContains(const GameplayScreenRuntime &context, int width, int height, float x, float y);

// The shade, the panel, the grid and the dragged face, over everything else.
void render(GameplayScreenRuntime &context, int width, int height);
// The open builder's pointer: dragging, the name under the pointer (drawn by render), Cancel and Accept.
void handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input, int width, int height);
}
}
