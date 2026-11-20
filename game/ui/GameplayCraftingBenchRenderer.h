#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class GameplayBenchPainter;

// The Workbench's Crafting tab (devdocs/maw/CRAFTING_BENCH_DESIGN.md §4.1), drawn inside the bench's frame.
namespace GameplayCraftingBenchRenderer
{
void render(GameplayScreenRuntime &context, const GameplayBenchPainter &painter);
}
}
