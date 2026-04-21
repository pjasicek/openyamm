#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

class GameplayHudRenderer
{
public:
    static void renderGameplayHud(GameplayScreenRuntime &context, int width, int height);
};
} // namespace OpenYAMM::Game
