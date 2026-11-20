#pragma once

#include "game/content/RulesetOptions.h"

#include <cstdint>

namespace OpenYAMM::Game
{
// What the new-game flow hands to the new session besides the party.
struct NewGameOptions
{
    uint32_t continentId = 0;
    // The debug God Lich party keeps its debug loadout.
    bool preserveDebugLoadout = false;
    RulesetSelection ruleset;
};
}
