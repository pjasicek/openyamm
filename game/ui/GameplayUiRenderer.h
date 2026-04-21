#pragma once

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

class GameplayUiRenderer
{
public:
    static void renderGameplayHudArt(GameplayScreenRuntime &context, int width, int height);
};
} // namespace OpenYAMM::Game
