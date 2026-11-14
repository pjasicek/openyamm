#pragma once

#include <cstddef>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
// A character's transient special-skill (talent) state in a MAW solo run (devdocs/solo_action/TALENTS.md): the
// actives' cooldowns and the timed effects they leave. Never saved: a load starts every cooldown ready and every effect
// off. The learned ranks are saved separately (Character::talentRanks).
struct SoloTalentState
{
    // Seconds left before each active (by talent id) may be used again.
    std::unordered_map<std::string, float> cooldownSeconds;
    // Frenzy's attack speed, Shield Wall's damage cut: seconds left.
    float frenzySeconds = 0.0f;
    float shieldWallSeconds = 0.0f;
    // Spell Surge: the next spell costs no SP and hits harder. The cast disarms it and opens a short window in which its
    // damage is rolled (a missile rolls on impact).
    bool spellSurgeArmed = false;
    float surgeDamageSeconds = 0.0f;
    // Purify's immunity: the condition (a CharacterCondition index) and its seconds left.
    std::optional<size_t> purifyCondition;
    float purifySeconds = 0.0f;
    // Steady Aim: seconds the party has stood still, where it stood, and whether the bonus is in the stats.
    float stillSeconds = 0.0f;
    float lastX = 0.0f;
    float lastY = 0.0f;
    bool hasLastPosition = false;
    bool steadyAimOn = false;
    // Mana Font's fraction of a spell point carried between updates.
    float manaFontCarry = 0.0f;
};
}
