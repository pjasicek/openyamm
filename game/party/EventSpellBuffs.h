#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
class Party;

bool tryApplyEventSpellBuffs(
    Party &party,
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t rawSkillMastery);
}
