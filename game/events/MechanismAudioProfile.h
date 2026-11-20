#pragma once

#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
// A mechanism's own sounds (a scene mechanism's or door's `sounds` block: MM9's doors name theirs), world sound names.
// A mechanism without one keeps its world's default (indoors: the map environment's door loop and stop sound).
struct MechanismAudioProfile
{
    std::string openSound;
    std::string closeSound;
    std::string openStartSound;
    std::string openBusySound;
    std::string openStopSound;
    std::string closeStartSound;
    std::string closeBusySound;
    std::string closeStopSound;
    std::string jiggleSound;
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;
    bool positional = false;
};
}
