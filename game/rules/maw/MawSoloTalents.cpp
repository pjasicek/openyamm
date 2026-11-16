#include "game/rules/maw/MawSoloTalents.h"

#include "game/party/Party.h"
#include "game/rules/SoloTalents.h"
#include "game/rules/maw/MawExperienceCurve.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game::MawSoloTalents
{
namespace
{
// Shield Wall's cut and Spell Surge's damage come from the table (per_rank: percent).
float tablePercent(std::string_view id, float fallback)
{
    const TalentDefinition *pTalent = soloTalentTable().find(id);
    return pTalent != nullptr ? pTalent->perRank : fallback;
}

// A passive's percent at the character's rank.
float passivePercent(const Character &member, std::string_view id)
{
    const int rank = talentRank(member, id);
    const TalentDefinition *pTalent = rank > 0 ? soloTalentTable().find(id) : nullptr;
    return pTalent != nullptr ? talentValue(*pTalent, rank) : 0.0f;
}

// A share of a base stat, rounded; Conditioning's and Steady Aim's percent reads the character's own base stat (what
// training and potions raised), not items or buffs, so the passives do not compound with each other.
int share(uint32_t base, float percent)
{
    return int(std::lround(double(base) * percent / 100.0));
}

constexpr float StillSecondsForAim = 1.0f;
// Onslaught: each stack is 1 % attack speed.
constexpr float OnslaughtPercentPerStack = 1.0f;
// Unbroken halves the part of a hit above this share of the maximum HP.
constexpr double UnbrokenThreshold = 0.30;
// Cheat Death: what a fatal hit leaves, and the cut that follows.
constexpr double CheatDeathHealthLeft = 0.05;
constexpr double CheatDeathDamageTaken = 0.05;
}

void applyPassives(Character &member)
{
    if (member.talentRanks.empty())
    {
        return;
    }

    CharacterStatBonuses &bonus = member.magicalBonuses;
    const float conditioning = passivePercent(member, "conditioning");
    const float aim = member.talentState.steadyAimOn ? passivePercent(member, "steady_aim") : 0.0f;
    const float resolve = passivePercent(member, "resolve");

    bonus.might += share(member.might, conditioning);
    bonus.intellect += share(member.intellect, conditioning);
    bonus.personality += share(member.personality, conditioning);
    bonus.endurance += share(member.endurance, conditioning);
    bonus.accuracy += share(member.accuracy, conditioning);
    bonus.speed += share(member.speed, conditioning);
    bonus.luck += share(member.luck, conditioning + aim);

    if (resolve > 0.0f)
    {
        CharacterResistanceSet &res = bonus.resistances;
        const CharacterResistanceSet &base = member.baseResistances;
        const auto raise = [resolve](int &value, int baseValue)
        {
            value += int(std::lround(double(std::max(0, value + baseValue)) * resolve / 100.0));
        };
        raise(res.fire, base.fire);
        raise(res.air, base.air);
        raise(res.water, base.water);
        raise(res.earth, base.earth);
        raise(res.mind, base.mind);
        raise(res.body, base.body);
        raise(res.spirit, base.spirit);
        raise(res.light, base.light);
        raise(res.dark, base.dark);
    }
}

void update(Party &party, float partyX, float partyY, bool calm, float deltaSeconds)
{
    bool refresh = false;
    float movement = 1.0f;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        Character &member = *party.member(memberIndex);

        if (member.talentRanks.empty())
        {
            continue;
        }

        SoloTalentState &state = member.talentState;

        for (auto &[id, seconds] : state.cooldownSeconds)
        {
            seconds = std::max(0.0f, seconds - deltaSeconds);
        }

        state.shieldWallSeconds = std::max(0.0f, state.shieldWallSeconds - deltaSeconds);
        state.surgeDamageSeconds = std::max(0.0f, state.surgeDamageSeconds - deltaSeconds);
        state.cheatDeathSeconds = std::max(0.0f, state.cheatDeathSeconds - deltaSeconds);
        state.cheatDeathCooldown = std::max(0.0f, state.cheatDeathCooldown - deltaSeconds);
        state.onslaughtSeconds = std::max(0.0f, state.onslaughtSeconds - deltaSeconds);

        if (state.onslaughtSeconds <= 0.0f)
        {
            state.onslaughtStacks = 0;
        }

        // Quickfoot: the solo's movement, faster out of combat.
        if (const int rank = talentRank(member, "quickfoot"); rank > 0)
        {
            if (const TalentDefinition *pTalent = soloTalentTable().find("quickfoot"))
            {
                const float percent = (calm && pTalent->perRankCalm > 0.0f ? pTalent->perRankCalm : pTalent->perRank)
                    * float(rank);
                movement = std::max(movement, 1.0f + percent / 100.0f);
            }
        }

        // Steady Aim: the party has not moved for a second.
        if (talentRank(member, "steady_aim") > 0)
        {
            const bool moved = state.hasLastPosition && std::hypot(partyX - state.lastX, partyY - state.lastY) > 1.0f;
            state.stillSeconds = moved ? 0.0f : state.stillSeconds + deltaSeconds;
            state.lastX = partyX;
            state.lastY = partyY;
            state.hasLastPosition = true;
            const bool aiming = state.stillSeconds >= StillSecondsForAim;

            if (aiming != state.steadyAimOn)
            {
                state.steadyAimOn = aiming;
                refresh = true;
            }
        }
    }

    party.setTalentMovementMultiplier(movement);

    if (refresh)
    {
        party.refreshDerivedState();
    }
}

void noteKill(Character &member)
{
    const int rank = talentRank(member, "onslaught");
    const TalentDefinition *pTalent = rank > 0 ? soloTalentTable().find("onslaught") : nullptr;

    if (pTalent == nullptr)
    {
        return;
    }

    SoloTalentState &state = member.talentState;
    const int maximum = int(std::lround(pTalent->perRank * float(rank)));
    state.onslaughtStacks = std::min(maximum, (state.onslaughtSeconds > 0.0f ? state.onslaughtStacks : 0) + 1);
    state.onslaughtSeconds = std::max(pTalent->duration, 1.0f);
}

float attackRecoveryScale(const Character &member)
{
    const SoloTalentState &state = member.talentState;

    if (state.onslaughtSeconds <= 0.0f || state.onslaughtStacks <= 0)
    {
        return 1.0f;
    }

    return 1.0f / (1.0f + OnslaughtPercentPerStack * float(state.onslaughtStacks) / 100.0f);
}

int absorbDamage(const Character &member, int damage, int maximumHealth)
{
    if (damage <= 0 || member.talentRanks.empty())
    {
        return damage;
    }

    const SoloTalentState &state = member.talentState;
    double amount = damage;

    if (state.shieldWallSeconds > 0.0f && member.equipment.offHand != 0)
    {
        amount *= 1.0 - tablePercent("shield_wall", 50.0f) / 100.0;
    }

    // Unbroken: the part of one hit above 30 % of the maximum HP is halved.
    if (hasKeystone(member, "unbroken") && maximumHealth > 0)
    {
        const double threshold = UnbrokenThreshold * maximumHealth;

        if (amount > threshold)
        {
            amount = threshold + (amount - threshold) / 2.0;
        }
    }

    if (state.cheatDeathSeconds > 0.0f)
    {
        amount *= CheatDeathDamageTaken;
    }

    return int(std::lround(amount));
}

int cheatDeath(Character &member, int damage, int currentHealth, int maximumHealth)
{
    SoloTalentState &state = member.talentState;

    if (damage < currentHealth || currentHealth <= 0 || maximumHealth <= 0 || !hasKeystone(member, "cheat_death")
        || state.cheatDeathCooldown > 0.0f)
    {
        return damage;
    }

    const TalentDefinition *pKeystone = soloTalentTable().findKeystone("cheat_death");
    const int left = std::max(1, int(std::ceil(CheatDeathHealthLeft * maximumHealth)));
    state.cheatDeathSeconds = pKeystone != nullptr ? pKeystone->duration : 2.0f;
    state.cheatDeathCooldown = pKeystone != nullptr ? pKeystone->cooldown : 180.0f;
    return std::max(0, currentHealth - left);
}

double spellDamageScale(const Character &caster)
{
    return caster.talentState.spellSurgeArmed || caster.talentState.surgeDamageSeconds > 0.0f
        ? 1.0 + tablePercent("spell_surge", 50.0f) / 100.0
        : 1.0;
}

double overloadScale(const Character &caster, int monstersNearTarget)
{
    const int rank = talentRank(caster, "overload");
    const TalentDefinition *pTalent = rank > 0 ? soloTalentTable().find("overload") : nullptr;

    if (pTalent == nullptr || monstersNearTarget <= 1)
    {
        return 1.0;
    }

    const int extra = std::min(monstersNearTarget - 1, std::max(1, pTalent->targets));
    return 1.0 + double(pTalent->perRank) * rank * extra / 100.0;
}

double leechBonus(const Character &member)
{
    return passivePercent(member, "bloodthirst") / 100.0;
}

double leechFloorDivisor(const Character &member)
{
    // Five ranks: ÷5 without it, half a step per rank down to ÷2.5.
    return 5.0 - 0.5 * std::clamp(talentRank(member, "bloodthirst"), 0, 5);
}

double nonPhysicalDamageScale(const Character &member)
{
    return std::clamp(1.0 - passivePercent(member, "spell_suppression") / 100.0, 0.0, 1.0);
}

bool nextSpellFree(const Character &caster)
{
    return caster.talentState.spellSurgeArmed;
}

void spendSurge(Character &caster)
{
    if (caster.talentState.spellSurgeArmed)
    {
        caster.talentState.spellSurgeArmed = false;
        // A missile rolls its damage when it lands: a few seconds' window keeps the surge on it.
        caster.talentState.surgeDamageSeconds = 3.0f;
    }
}

double earlyMonsterCut(const Character &member)
{
    // MAW's curve: a solo's own surcharge only starts at level 100, after the cut has ended.
    const double earnedLevel = std::floor(mawLevelForExperience(double(member.experience)));
    return soloTalentTable().earlyMonsterCut(std::max(double(member.level), earnedLevel));
}
}
