#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct GameplayInputFrame;

// Pointer, drag and keys of the Workbench's Crafting tab; the alchemy bench's controller hands its input here while
// the tab is shown.
namespace GameplayCraftingBenchInputController
{
void handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input);
}
}
