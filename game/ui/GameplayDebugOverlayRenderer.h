#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

class GameplayDebugOverlayRenderer
{
public:
    static void renderEventDialogPanel(GameplayScreenRuntime &context, int width, int height);
};
} // namespace OpenYAMM::Game
