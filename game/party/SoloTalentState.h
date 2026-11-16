#pragma once

#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
// A character's transient special-skill (talent) state in a MAW solo run (devdocs/solo_action/TALENTS.md): the
// actives' cooldowns and the timed effects they leave. Saved with the character (SaveGame.cpp, from save 187), so a
// load resumes cooldowns, Onslaught's stacks and every effect where the save left them. The learned ranks and bound
// keystones are saved separately (Character::talentRanks).
struct SoloTalentState
{
    // Seconds left before each active (by talent id) may be used again.
    std::unordered_map<std::string, float> cooldownSeconds;
    // Shield Wall's damage cut: seconds left.
    float shieldWallSeconds = 0.0f;
    // Spell Surge: the next spell costs no SP and hits harder. The cast disarms it and opens a short window in which its
    // damage is rolled (a missile rolls on impact).
    bool spellSurgeArmed = false;
    float surgeDamageSeconds = 0.0f;
    // Onslaught: attack-speed stacks from kills and the seconds they still last.
    int onslaughtStacks = 0;
    float onslaughtSeconds = 0.0f;
    // Cheat Death (keystone): the seconds of its 95 % cut after it saved the character, and its cooldown.
    float cheatDeathSeconds = 0.0f;
    float cheatDeathCooldown = 0.0f;
    // Steady Aim: seconds the party has stood still, where it stood, and whether the bonus is in the stats.
    float stillSeconds = 0.0f;
    float lastX = 0.0f;
    float lastY = 0.0f;
    bool hasLastPosition = false;
    bool steadyAimOn = false;
    // Manathirst: monsters an area spell gave SP for in the current short window, and the seconds it still lasts (not
    // saved: it lasts a fraction of a second).
    int areaManaLeechHits = 0;
    float areaManaLeechSeconds = 0.0f;
};
}
