#pragma once

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

class GameplayHudOverlayRenderer
{
public:
    static void renderChestPanel(GameplayOverlayContext &context, int width, int height, bool renderAboveHud);
    static void renderInventoryNestedOverlay(GameplayOverlayContext &context, int width, int height, bool renderAboveHud);
};
} // namespace OpenYAMM::Game
