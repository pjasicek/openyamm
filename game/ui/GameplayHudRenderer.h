#pragma once

namespace OpenYAMM::Game
{
class OutdoorGameView;

class GameplayHudRenderer
{
public:
    static void renderGameplayHudArt(OutdoorGameView &view, int width, int height);
    static void renderGameplayHud(const OutdoorGameView &view, int width, int height);
};
} // namespace OpenYAMM::Game
