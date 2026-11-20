#pragma once

#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
class SpellTable;

// Armageddon (Dark, spell 98), shared by the outdoor maps and the BLVs open to the sky (isOpenAirMap): the ground
// shakes for 256 ticks while meteors rain around the party (the enhanced spell effects), one strikes each nearby actor
// at the end, and then every monster on the map takes the spell's damage and every living member 50 + skill. A
// caster casts it 3 times a day, 4 at Grandmaster. The world keeps the state and saves it with its map.

constexpr float ArmageddonDurationSeconds = 256.0f / 128.0f;
// The actors within this horizontal range of the party take a strike's effect at the end (at most this many).
constexpr float ArmageddonStrikeRange = 6000.0f;
constexpr size_t ArmageddonMaxActorStrikes = 40;

struct ArmageddonState
{
    float remainingSeconds = 0.0f;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    uint32_t casterMemberIndex = 0;
    uint32_t shakeStepsRemaining = 0;
    uint32_t shakeSequence = 0;
    float cameraShakeYawRadians = 0.0f;
    float cameraShakePitchRadians = 0.0f;

    bool active() const
    {
        return remainingSeconds > 0.0f;
    }
};

// Starts the spell for the caster. False with the failure text when one is active, there is no such caster or the
// caster has no casts left today; a start counts one of them.
bool startArmageddon(
    ArmageddonState &state,
    Party *pParty,
    size_t casterMemberIndex,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    std::string &failureText);

struct ArmageddonStep
{
    // The spell's time before and after the step, for its meteors and strikes.
    float elapsedBefore = 0.0f;
    float elapsedAfter = 0.0f;
    // It ran out: the world resolves the detonation now and clears the state.
    bool detonate = false;
};

// Advances an active spell by deltaSeconds: its time and the next step of its camera shake (mapSeed: the map's id).
ArmageddonStep advanceArmageddon(ArmageddonState &state, float deltaSeconds, uint32_t mapSeed);

struct ArmageddonMeteor
{
    float x = 0.0f;
    float y = 0.0f;
    uint32_t seed = 0;
};

// The meteors whose time falls in the step, around the party. They are presentation only and derive from the cast, so
// they need no saved state; the world puts each on its ground.
std::vector<ArmageddonMeteor> armageddonMeteors(
    const ArmageddonState &state,
    const ArmageddonStep &step,
    uint32_t mapSeed,
    float partyX,
    float partyY);

// Whether the strikes on the nearby actors fall in the step, and the seed of the one on an actor.
bool armageddonStrikesDue(const ArmageddonStep &step);
uint32_t armageddonStrikeSeed(const ArmageddonState &state, uint32_t actorId);

// The damage a monster takes: the rules' roll of the spell where they have one (MAW), else 50 + skill.
int armageddonMonsterDamage(const ArmageddonState &state, const Party *pParty, const SpellTable *pSpellTable);
// Every living member takes 50 + skill.
void applyArmageddonToParty(const ArmageddonState &state, Party &party);
}
