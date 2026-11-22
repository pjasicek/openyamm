#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
// A player of the game. The one at this game is LocalPlayer; a co-op session's other players follow (GameSession's
// guests).
using PlayerId = uint8_t;

constexpr PlayerId LocalPlayer = 0;
}
