#include "game/gameplay/ArmageddonSpell.h"

#include "engine/Localization.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"

#include <algorithm>
#include <cmath>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr uint32_t ArmageddonShakeStepCount = 60;
constexpr float ArmageddonShakeYawRadians = 0.035f;
constexpr float ArmageddonShakePitchRadians = 0.024f;
// Enhanced visuals: meteors rain around the party while the ground shakes, then one strikes each nearby actor so that
// it lands as the detonation resolves. The fall time matches the generated armageddon impact effect.
constexpr float ArmageddonMeteorIntervalSeconds = 0.07f;
constexpr float ArmageddonMeteorRainEndSeconds = 1.4f;
constexpr float ArmageddonMeteorMinRadius = 500.0f;
constexpr float ArmageddonMeteorMaxRadius = 3000.0f;
constexpr float ArmageddonStrikeFallSeconds = 0.5f;
}

bool startArmageddon(
    ArmageddonState &state,
    Party *pParty,
    size_t casterMemberIndex,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    std::string &failureText)
{
    failureText.clear();

    if (pParty == nullptr)
    {
        failureText = Engine::tr("Spell failed");
        return false;
    }

    if (state.active())
    {
        failureText = Engine::tr("Armageddon already active");
        return false;
    }

    Character *pCaster = pParty->member(casterMemberIndex);

    if (pCaster == nullptr)
    {
        failureText = Engine::tr("Spell failed");
        return false;
    }

    const uint8_t castLimit = skillMastery == SkillMastery::Grandmaster ? 4 : 3;

    if (pCaster->armageddonCastsToday >= castLimit)
    {
        failureText = Engine::tr("No Armageddon casts left today");
        return false;
    }

    state.remainingSeconds = ArmageddonDurationSeconds;
    state.skillLevel = skillLevel;
    state.skillMastery = skillMastery;
    state.casterMemberIndex = static_cast<uint32_t>(casterMemberIndex);
    state.shakeStepsRemaining = ArmageddonShakeStepCount;
    ++state.shakeSequence;
    state.cameraShakeYawRadians = 0.0f;
    state.cameraShakePitchRadians = 0.0f;
    ++pCaster->armageddonCastsToday;
    return true;
}

ArmageddonStep advanceArmageddon(ArmageddonState &state, float deltaSeconds, uint32_t mapSeed)
{
    ArmageddonStep step = {};
    step.elapsedBefore = ArmageddonDurationSeconds - state.remainingSeconds;
    state.remainingSeconds = std::max(0.0f, state.remainingSeconds - deltaSeconds);
    step.elapsedAfter = ArmageddonDurationSeconds - state.remainingSeconds;

    if (state.shakeStepsRemaining > 0)
    {
        std::mt19937 rng(
            mapSeed * 2654435761u
            ^ (state.shakeSequence + 1u) * 2246822519u
            ^ state.shakeStepsRemaining * 3266489917u);
        std::uniform_real_distribution<float> yawDistribution(-ArmageddonShakeYawRadians, ArmageddonShakeYawRadians);
        std::uniform_real_distribution<float> pitchDistribution(-ArmageddonShakePitchRadians, ArmageddonShakePitchRadians);
        state.cameraShakeYawRadians = yawDistribution(rng);
        state.cameraShakePitchRadians = pitchDistribution(rng);
        --state.shakeStepsRemaining;
    }
    else
    {
        state.cameraShakeYawRadians = 0.0f;
        state.cameraShakePitchRadians = 0.0f;
    }

    step.detonate = state.remainingSeconds <= 0.0f;
    return step;
}

std::vector<ArmageddonMeteor> armageddonMeteors(
    const ArmageddonState &state,
    const ArmageddonStep &step,
    uint32_t mapSeed,
    float partyX,
    float partyY)
{
    std::vector<ArmageddonMeteor> meteors;
    const int firstMeteor = static_cast<int>(std::floor(step.elapsedBefore / ArmageddonMeteorIntervalSeconds)) + 1;
    const int lastMeteor = static_cast<int>(
        std::floor(std::min(step.elapsedAfter, ArmageddonMeteorRainEndSeconds) / ArmageddonMeteorIntervalSeconds));

    for (int meteor = firstMeteor; meteor <= lastMeteor; ++meteor)
    {
        const uint32_t seed =
            mapSeed * 2654435761u
            ^ (state.shakeSequence + 1u) * 2246822519u
            ^ static_cast<uint32_t>(meteor) * 3266489917u;
        std::mt19937 rng(seed);
        std::uniform_real_distribution<float> unit(0.0f, 1.0f);
        const float angle = unit(rng) * 2.0f * Pi;
        const float minSquared = ArmageddonMeteorMinRadius * ArmageddonMeteorMinRadius;
        const float maxSquared = ArmageddonMeteorMaxRadius * ArmageddonMeteorMaxRadius;
        const float radius = std::sqrt(minSquared + unit(rng) * (maxSquared - minSquared));
        meteors.push_back({partyX + std::cos(angle) * radius, partyY + std::sin(angle) * radius, seed});
    }

    return meteors;
}

bool armageddonStrikesDue(const ArmageddonStep &step)
{
    const float strikeSeconds = ArmageddonDurationSeconds - ArmageddonStrikeFallSeconds;
    return step.elapsedBefore < strikeSeconds && step.elapsedAfter >= strikeSeconds;
}

uint32_t armageddonStrikeSeed(const ArmageddonState &state, uint32_t actorId)
{
    return actorId * 2246822519u ^ (state.shakeSequence + 1u) * 3266489917u;
}

int armageddonMonsterDamage(const ArmageddonState &state, const Party *pParty, const SpellTable *pSpellTable)
{
    return GameplayProjectileService::partyWorldSpellDamage(pParty, pSpellTable, state.casterMemberIndex,
        spellIdValue(SpellId::Armageddon), state.skillLevel, uint32_t(state.skillMastery),
        50 + static_cast<int>(state.skillLevel));
}

void applyArmageddonToParty(const ArmageddonState &state, Party &party)
{
    const int damage = 50 + static_cast<int>(state.skillLevel);

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const Character *pMember = party.member(memberIndex);

        if (pMember == nullptr
            || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Dead))
            || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
            || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
        {
            continue;
        }

        party.applyDamageToMember(memberIndex, damage, "", true);
    }
}
}
