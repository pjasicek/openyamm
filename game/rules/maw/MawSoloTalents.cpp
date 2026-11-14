#include "game/rules/maw/MawSoloTalents.h"

#include "game/party/Party.h"
#include "game/rules/SoloTalents.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game::MawSoloTalents
{
namespace
{
// Frenzy's attack speed and Shield Wall's cut come from the table (per_rank: percent).
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

// A share of a base stat, rounded; the "+2 %" of Weapon Training and the others reads the character's own base stat
// (what training and potions raised), not items or buffs, so the passives do not compound with each other.
int share(uint32_t base, float percent)
{
    return int(std::lround(double(base) * percent / 100.0));
}

constexpr float StillSecondsForAim = 1.0f;
}

void applyPassives(Character &member)
{
    if (member.talentRanks.empty())
    {
        return;
    }

    CharacterStatBonuses &bonus = member.magicalBonuses;
    const float weapon = passivePercent(member, "weapon_training");
    const float marksman = passivePercent(member, "marksman");
    const float attunement = passivePercent(member, "attunement");
    const float resolve = passivePercent(member, "resolve");

    bonus.might += share(member.might, weapon);
    bonus.endurance += share(member.endurance, weapon + attunement);
    bonus.speed += share(member.speed, weapon + marksman);
    bonus.accuracy += share(member.accuracy, marksman);
    bonus.intellect += share(member.intellect, attunement);
    bonus.personality += share(member.personality, attunement);

    if (member.talentState.steadyAimOn)
    {
        bonus.luck += share(member.luck, passivePercent(member, "steady_aim"));
    }

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

void update(Party &party, float partyX, float partyY, float deltaSeconds)
{
    bool refresh = false;

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

        state.frenzySeconds = std::max(0.0f, state.frenzySeconds - deltaSeconds);
        state.shieldWallSeconds = std::max(0.0f, state.shieldWallSeconds - deltaSeconds);
        state.surgeDamageSeconds = std::max(0.0f, state.surgeDamageSeconds - deltaSeconds);
        state.purifySeconds = std::max(0.0f, state.purifySeconds - deltaSeconds);

        if (state.purifySeconds <= 0.0f)
        {
            state.purifyCondition.reset();
        }

        // Mana Font: per_rank spell points every 5 seconds for each 10 levels.
        if (const float font = passivePercent(member, "mana_font"); font > 0.0f && member.spellPoints < member.maxSpellPoints)
        {
            state.manaFontCarry += font * float(std::max(1u, member.level / 10)) / 5.0f * deltaSeconds;
            const int whole = int(state.manaFontCarry);
            state.manaFontCarry -= float(whole);
            member.spellPoints = std::min(member.maxSpellPoints, member.spellPoints + whole);
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

    if (refresh)
    {
        party.refreshDerivedState();
    }
}

float attackRecoveryScale(const Character &member)
{
    if (member.talentState.frenzySeconds <= 0.0f)
    {
        return 1.0f;
    }

    return 1.0f / (1.0f + tablePercent("frenzy", 25.0f) / 100.0f);
}

int absorbDamage(const Character &member, int damage)
{
    if (member.talentState.shieldWallSeconds <= 0.0f || member.equipment.offHand == 0 || damage <= 0)
    {
        return damage;
    }

    return int(std::lround(double(damage) * (1.0 - tablePercent("shield_wall", 50.0f) / 100.0)));
}

double spellDamageScale(const Character &caster)
{
    const double surge = caster.talentState.spellSurgeArmed || caster.talentState.surgeDamageSeconds > 0.0f
        ? 1.0 + tablePercent("spell_surge", 50.0f) / 100.0
        : 1.0;
    return (1.0 + passivePercent(caster, "attunement") / 100.0) * surge;
}

double healScale(const Character &caster)
{
    return 1.0 + passivePercent(caster, "attunement") / 100.0;
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

bool blocksCondition(const Character &member, CharacterCondition condition)
{
    return member.talentState.purifySeconds > 0.0f && member.talentState.purifyCondition
        && *member.talentState.purifyCondition == size_t(condition);
}
}
