#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

class GameplayHudOverlayRenderer
{
public:
    static void renderChestPanel(GameplayScreenRuntime &context, int width, int height, bool renderAboveHud);
    static void renderInventoryNestedOverlay(GameplayScreenRuntime &context, int width, int height, bool renderAboveHud);
};
} // namespace OpenYAMM::Game
