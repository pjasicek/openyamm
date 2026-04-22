#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
class OutdoorGameView;

class OutdoorPresentationController
{
public:
    static void consumePendingWorldAudioEvents(OutdoorGameView &view);
    static void updateFootstepAudio(OutdoorGameView &view, float deltaSeconds);
};
} // namespace OpenYAMM::Game
