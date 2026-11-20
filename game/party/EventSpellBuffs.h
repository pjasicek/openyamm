#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
class Party;

// Where a buff spell cast without a party member's skill comes from.
enum class BuffSource : uint8_t
{
    Scroll,
    // A map event or pedestal.
    MapEvent,
    Temple,
    // A hired NPC follower.
    Hireling,
};

// Applies a buff spell cast by an event, a temple or a hireling; the party's rules may take it instead
// (SpellRules::castSourceBuff).
bool tryApplyEventSpellBuffs(
    Party &party,
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t rawSkillMastery,
    float durationSecondsOverride = 0.0f,
    BuffSource source = BuffSource::MapEvent);
}
