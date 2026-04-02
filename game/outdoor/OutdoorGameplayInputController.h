#pragma once

namespace OpenYAMM::Game
{
class OutdoorGameView;

class OutdoorGameplayInputController
{
public:
    static void updateCameraFromInput(OutdoorGameView &view, float deltaSeconds);
};
} // namespace OpenYAMM::Game
