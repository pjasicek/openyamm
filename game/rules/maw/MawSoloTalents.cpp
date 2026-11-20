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
// Spell Surge's damage comes from the table (per_rank: percent).
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

// A share of a whole stat, rounded: Conditioning's and Steady Aim's percent reads the stat as the sheet shows it
// without them (base, permanent bonuses, items and buffs). Both read the same value, so they do not compound with
// each other.
int share(uint32_t base, int bonuses, float percent)
{
    return int(std::lround(double(std::max<int64_t>(0, int64_t(base) + bonuses)) * percent / 100.0));
}

constexpr float StillSecondsForAim = 1.0f;
// Nimble: the party counts as moving this long after its last step.
constexpr float MovingGraceSeconds = 0.2f;
// Spell Surge's cooldown_per_cast: the hits of one cast land within this of its first.
constexpr float CastCreditWindowSeconds = 0.75f;
// Onslaught: each stack is 1 % attack speed.
constexpr float OnslaughtPercentPerStack = 1.0f;
// Unbroken halves the part of a hit above this share of the maximum HP.
constexpr double UnbrokenThreshold = 0.30;
// Cheat Death: what a fatal hit leaves, and the cut that follows.
constexpr double CheatDeathHealthLeft = 0.05;
constexpr double CheatDeathDamageTaken = 0.05;
// Manathirst: an area spell gives SP for at most this many monsters within the window after its first hit (a Fireball
// lands at once; a Meteor Shower's stones fall within it).
constexpr int AreaManaLeechMonsters = 3;
constexpr float AreaManaLeechWindowSeconds = 0.5f;

// Bloodthirst's and Manathirst's leech floor divisor at a rank: ÷5 without it, half a step a rank down to ÷2.5 at the
// fifth.
double thirstFloorDivisor(int rank)
{
    return 5.0 - 0.5 * std::clamp(rank, 0, 5);
}
}

void applyStatPassives(Character &member)
{
    if (member.talentRanks.empty())
    {
        return;
    }

    CharacterStatBonuses &bonus = member.magicalBonuses;
    const CharacterStatBonuses &permanent = member.permanentBonuses;
    const float conditioning = passivePercent(member, "conditioning");
    const float aim = member.talentState.steadyAimOn ? passivePercent(member, "steady_aim") : 0.0f;

    bonus.might += share(member.might, permanent.might + bonus.might, conditioning);
    bonus.intellect += share(member.intellect, permanent.intellect + bonus.intellect, conditioning);
    bonus.personality += share(member.personality, permanent.personality + bonus.personality, conditioning);
    bonus.endurance += share(member.endurance, permanent.endurance + bonus.endurance, conditioning);
    bonus.accuracy += share(member.accuracy, permanent.accuracy + bonus.accuracy, conditioning);
    bonus.speed += share(member.speed, permanent.speed + bonus.speed, conditioning);
    bonus.luck += share(member.luck, permanent.luck + bonus.luck, conditioning + aim);
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

        state.phaseSeconds = std::max(0.0f, state.phaseSeconds - deltaSeconds);
        state.castCreditSeconds = std::max(0.0f, state.castCreditSeconds - deltaSeconds);
        state.surgeDamageSeconds = std::max(0.0f, state.surgeDamageSeconds - deltaSeconds);
        state.cheatDeathSeconds = std::max(0.0f, state.cheatDeathSeconds - deltaSeconds);
        state.cheatDeathCooldown = std::max(0.0f, state.cheatDeathCooldown - deltaSeconds);
        state.areaManaLeechSeconds = std::max(0.0f, state.areaManaLeechSeconds - deltaSeconds);
        state.onslaughtSeconds = std::max(0.0f, state.onslaughtSeconds - deltaSeconds);

        if (state.onslaughtSeconds <= 0.0f)
        {
            state.onslaughtStacks = 0;
        }

        // Rage: its limit counts a second at a time, and the bar drains while nothing fights the character.
        state.rageSecondLeft -= deltaSeconds;

        if (state.rageSecondLeft <= 0.0f)
        {
            state.rageSecondLeft = 1.0f;
            state.rageSecondGained = 0.0f;
        }

        if (calm && state.rage > 0.0f)
        {
            state.rage = std::max(0.0f, state.rage - soloTalentTable().rage().drainPerSecond * deltaSeconds);
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

        // Steady Aim (the party has not moved for a second) and Nimble (it is moving) read the same stillness.
        if (talentRank(member, "steady_aim") > 0 || talentRank(member, "nimble") > 0)
        {
            const bool moved = state.hasLastPosition && std::hypot(partyX - state.lastX, partyY - state.lastY) > 1.0f;
            // Before its first step the party stands: Nimble must not count the moments after a load as movement.
            state.stillSeconds = moved          ? 0.0f
                : !state.hasLastPosition ? StillSecondsForAim
                                         : state.stillSeconds + deltaSeconds;
            state.lastX = partyX;
            state.lastY = partyY;
            state.hasLastPosition = true;
            const bool aiming = talentRank(member, "steady_aim") > 0 && state.stillSeconds >= StillSecondsForAim;

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
    shortenTalentCooldownsOnKill(soloTalentTable(), member);
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

double incomingDamageScale(const Character &member, const IncomingHit &hit)
{
    if (member.talentRanks.empty())
    {
        return 1.0;
    }

    const SoloTalentTable &table = soloTalentTable();
    const SoloTalentState &state = member.talentState;
    double scale = 1.0;
    const auto cut = [&scale](double percent) { scale *= std::clamp(1.0 - percent / 100.0, 0.0, 1.0); };

    if (!hit.physical)
    {
        cut(passivePercent(member, "spell_suppression"));
    }

    if (hit.monsterAttack && state.meleeDrawn)
    {
        const TalentDefinition *pVanguard = table.find("vanguard");

        if (hit.missile && pVanguard != nullptr && hit.firedFromDistance > pVanguard->distance)
        {
            cut(passivePercent(member, "vanguard"));
        }

        if (const TalentDefinition *pOutnumbered = table.find("outnumbered"))
        {
            const int counted = std::min(hit.nearbyMonsters, std::max(1, pOutnumbered->targets));
            cut(passivePercent(member, "outnumbered") * std::max(0, counted));
        }
    }

    if (state.hasLastPosition && state.stillSeconds < MovingGraceSeconds)
    {
        cut(passivePercent(member, "nimble"));
    }

    if (state.phaseSeconds > 0.0f)
    {
        cut(passivePercent(member, "phase"));
    }

    return scale < 1.0 ? std::max(scale, table.damageFloor()) : 1.0;
}

double battleFrenzyScale(const Character &attacker, int nearbyMonsters)
{
    const TalentDefinition *pTalent = soloTalentTable().find("battle_frenzy");
    const int counted = pTalent != nullptr ? std::min(nearbyMonsters, std::max(1, pTalent->targets)) : 0;
    return 1.0 + passivePercent(attacker, "battle_frenzy") * std::max(0, counted) / 100.0;
}

float packReach(std::string_view talentId)
{
    const TalentDefinition *pTalent = soloTalentTable().find(talentId);
    return pTalent != nullptr ? pTalent->distance : 0.0f;
}

double longShotScale(const Character &shooter, float flightDistance)
{
    const TalentDefinition *pTalent = soloTalentTable().find("long_shot");

    if (pTalent == nullptr || pTalent->fullDistance <= pTalent->distance)
    {
        return 1.0;
    }

    const double share =
        std::clamp((flightDistance - pTalent->distance) / (pTalent->fullDistance - pTalent->distance), 0.0f, 1.0f);
    return 1.0 + passivePercent(shooter, "long_shot") * share / 100.0;
}

double spellDamageBonus(const Character &caster, bool areaSpell, int blastMonsters, bool targetAtFullHealth)
{
    double bonus = caster.talentState.spellSurgeArmed || caster.talentState.surgeDamageSeconds > 0.0f
        ? tablePercent("spell_surge", 50.0f) / 100.0
        : 0.0;
    const int overload = talentRank(caster, "overload");
    const TalentDefinition *pOverload = overload > 0 && areaSpell ? soloTalentTable().find("overload") : nullptr;

    if (pOverload != nullptr && blastMonsters > 1)
    {
        const int extra = std::min(blastMonsters - 1, std::max(1, pOverload->targets));
        bonus += double(pOverload->perRank) * overload * extra / 100.0;
    }

    if (targetAtFullHealth)
    {
        bonus += passivePercent(caster, "opening_volley") / 100.0;
    }

    return bonus;
}

double breachShare(const Character &caster)
{
    return std::clamp(passivePercent(caster, "breach") / 100.0, 0.0, 1.0);
}

double manaShieldCostScale(const Character &member)
{
    return std::clamp(1.0 - passivePercent(member, "arcane_ward") / 100.0, 0.1, 1.0);
}

float exposeWeaknessPercent(const Character &shooter)
{
    return passivePercent(shooter, "expose_weakness");
}

float exposeWeaknessSeconds()
{
    const TalentDefinition *pTalent = soloTalentTable().find("expose_weakness");
    return pTalent != nullptr ? pTalent->duration : 0.0f;
}

float hamstringPercent(const Character &shooter)
{
    return passivePercent(shooter, "hamstring");
}

float hamstringSeconds()
{
    const TalentDefinition *pTalent = soloTalentTable().find("hamstring");
    return pTalent != nullptr ? pTalent->duration : 0.0f;
}

namespace
{
void gainRage(Character &member, double amount)
{
    const SoloRageRules &rules = soloTalentTable().rage();
    SoloTalentState &state = member.talentState;

    if (amount <= 0.0 || !hasRageBar(soloTalentTable(), member))
    {
        return;
    }

    const double room = rules.limitPerSecond > 0.0f
        ? std::max(0.0, double(rules.limitPerSecond) - state.rageSecondGained)
        : amount;
    const double gained = std::min(amount, room);
    state.rageSecondGained += float(gained);
    state.rage = std::min(rules.maximum, state.rage + float(gained));
}
}

void gainRageFromBlow(Character &member, double monsterBarShare, float recoverySeconds, bool extraBlow)
{
    const SoloRageRules &rules = soloTalentTable().rage();
    const double blow = rules.perRecoverySecond * std::max(0.0f, recoverySeconds)
        + rules.perMonsterBar * std::clamp(monsterBarShare, 0.0, 1.0);
    gainRage(member, extraBlow ? blow * rules.extraBlowShare : blow);
}

void gainRageFromHit(Character &member, double ownBarShare)
{
    gainRage(member, soloTalentTable().rage().perOwnBar * std::clamp(ownBarShare, 0.0, 1.0));
}

void noteSpellHit(Character &caster)
{
    SoloTalentState &state = caster.talentState;

    if (state.castCreditSeconds <= 0.0f)
    {
        shortenTalentCooldownsOnCast(soloTalentTable(), caster);
    }

    state.castCreditSeconds = CastCreditWindowSeconds;
}

double leechBonus(const Character &member)
{
    return passivePercent(member, "bloodthirst") / 100.0;
}

double leechFloorDivisor(const Character &member)
{
    return thirstFloorDivisor(talentRank(member, "bloodthirst"));
}

double manaLeechShare(const Character &member)
{
    return passivePercent(member, "manathirst") / 100.0;
}

double manaLeechFloorDivisor(const Character &member)
{
    return thirstFloorDivisor(talentRank(member, "manathirst"));
}

bool takeAreaManaLeech(Character &member)
{
    SoloTalentState &state = member.talentState;

    if (state.areaManaLeechSeconds <= 0.0f)
    {
        state.areaManaLeechHits = 0;
        state.areaManaLeechSeconds = AreaManaLeechWindowSeconds;
    }

    if (state.areaManaLeechHits >= AreaManaLeechMonsters)
    {
        return false;
    }

    ++state.areaManaLeechHits;
    return true;
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

namespace
{
// The level the early rules read: the trained one, or the one the experience has earned when that is higher.
double earlyRuleLevel(const Character &member)
{
    // MAW's curve: a solo's own surcharge only starts at level 100, after the early rules have ended.
    const double earnedLevel = std::floor(mawLevelForExperience(double(member.experience)));
    return std::max(double(member.level), earnedLevel);
}
}

double earlyMonsterCut(const Character &member)
{
    return soloTalentTable().earlyMonsterCut(earlyRuleLevel(member));
}

double earlyRegeneration(const Character &member)
{
    return soloTalentTable().earlyRegeneration(earlyRuleLevel(member));
}
}
