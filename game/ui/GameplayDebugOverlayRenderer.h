#pragma once

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

class GameplayDebugOverlayRenderer
{
public:
    static void renderChestPanel(GameplayOverlayContext &context, int width, int height);
    static void renderEventDialogPanel(GameplayOverlayContext &context, int width, int height);
};
} // namespace OpenYAMM::Game
