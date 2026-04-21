#pragma once

namespace OpenYAMM::Game
{
struct GameplayInputFrame;
class OutdoorGameView;

class OutdoorGameplayInputController
{
public:
    static void updateCameraFromInput(
        OutdoorGameView &view,
        const GameplayInputFrame &input,
        float deltaSeconds);
};
} // namespace OpenYAMM::Game
