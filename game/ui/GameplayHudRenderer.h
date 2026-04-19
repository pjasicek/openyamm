#pragma once

namespace OpenYAMM::Game
{
class GameplayOverlayContext;

class GameplayHudRenderer
{
public:
    static void renderGameplayHudArt(GameplayOverlayContext &context, int width, int height);
    static void renderGameplayHud(GameplayOverlayContext &context, int width, int height);
};
} // namespace OpenYAMM::Game
