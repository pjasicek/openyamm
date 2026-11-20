#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// Reads rulesets/maw/data/npc_extra_houses.yml: the houses where each of MAW's moved teachers also teaches, by NPC id.
bool loadMawNpcExtraHouses(
    const std::string &text,
    std::unordered_map<uint32_t, std::vector<uint32_t>> &extraHouses,
    std::string &errorMessage);
}
