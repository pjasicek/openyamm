#pragma once

#include "game/party/SkillData.h"

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class CharacterBuffId : uint8_t;
enum class CharacterCondition : uint8_t;
enum class PartyBuffId : uint8_t;
enum class SpecialItemEnchantKind : uint8_t;

enum class PotionPool : uint8_t
{
    HitPoints,
    SpellPoints,
};

// An amount by the potion power P: constant + perPower * P (linear); ceil(P / divisor); floor(P / divisor) * a
// (step); a s^2 + b s with s = floor(P / divisor) (step_quadratic); ceil(sqrt(P) / divisor) + a (sqrt_ceil); or a
// + b times the pool a character of level P is expected to have (pool_share, the rules' estimate).
struct PotionAmount
{
    enum class Kind : uint8_t
    {
        Linear,
        CeilDivide,
        Step,
        StepQuadratic,
        SqrtCeil,
        PoolShare,
    };

    Kind kind = Kind::Linear;
    int constant = 0;
    int perPower = 0;
    int divisor = 0;
    double a = 0;
    double b = 0;
    PotionPool pool = PotionPool::HitPoints;

    // `estimatedPool` is the rules' expected pool at level P, read only by pool_share.
    int evaluate(int power, double estimatedPool = 0) const;
};

enum class PotionEffectKind : uint8_t
{
    Restore,
    Cure,
    CureAllRestorable,
    Buff,
    PartyBuff,
    PermanentStat,
    PermanentResistance,
    Age,
    LevelModifier,
    // Blocks conditions for the potion's duration.
    Immunity,
    // The drinker's own copy of a buff aura at the potion's strength (MAW).
    AuraBuff,
    // Timed extra levels of a skill.
    SkillBonus,
    SkillPoints,
    // Timed regeneration at a skill of `amount` (MAW: HP/s = sqrt(full HP) x skill^1.25 x 0.005; the stronger of it
    // and the Regeneration aura heals).
    Regeneration,
};

// How often a permanent effect may work on one character.
enum class PotionLimit : uint8_t
{
    None,
    OncePerCharacter,
    // Only the part above the strongest of this potion the character drank before counts (MAW's black potions).
    BestStep,
};

enum class PotionStat : uint8_t
{
    Might,
    Intellect,
    Personality,
    Endurance,
    Accuracy,
    Speed,
    Luck,
};

enum class PotionResistance : uint8_t
{
    Fire,
    Air,
    Water,
    Earth,
    Mind,
    Body,
};

struct PotionEffect
{
    PotionEffectKind kind = PotionEffectKind::Restore;
    PotionAmount amount;
    PotionPool pool = PotionPool::HitPoints;
    // Cure: the conditions removed. Buff: the condition that stops it (at most one).
    std::vector<CharacterCondition> conditions;
    CharacterBuffId buffId = {};
    PartyBuffId partyBuffId = {};
    int partyBuffSkillLevel = 0;
    SkillMastery partyBuffMastery = SkillMastery::Normal;
    std::vector<PotionStat> stats;
    // PermanentStat: into the permanent bonuses rather than the base stats.
    bool intoBonus = false;
    std::vector<PotionResistance> resistances;
    // Age: makes the drinker younger instead of older; clears magical ageing first if there is any; or sets the
    // drinker's age.
    bool younger = false;
    bool clearMagicAgeFirst = false;
    int setYears = 0;
    PotionLimit limit = PotionLimit::None;
    // AuraBuff: the aura's spell. SkillBonus: the skill.
    uint32_t spellId = 0;
    std::string skillName;
};

// A potion poured onto an item instead of drunk.
enum class PotionItemAction : uint8_t
{
    None,
    RechargeWand,
    Harden,
    TemporarySpecialEnchant,
    // The ruleset's crafting rules handle it (MAW's Enchant Item and element potions, on the Workbench).
    Crafting,
};

struct PotionDefinition
{
    uint32_t itemId = 0;
    bool oncePerCharacter = false;
    // Refused (and kept) below this power; drinks a bottle holds (1: consumed on the first).
    int minimumPower = 0;
    int charges = 1;
    // The Endless Potion adds drinks to it (MAW).
    bool rechargeable = false;
    std::vector<PotionEffect> effects;
    PotionItemAction itemAction = PotionItemAction::None;
    SpecialItemEnchantKind enchant = {};
};

// What drinking or applying each potion does: engine/data_tables/potion_effects.yml, whose header documents the
// format. A ruleset replaces the whole file.
class PotionEffectTable
{
public:
    bool loadFromYaml(const std::string &text, std::string &errorMessage);
    const PotionDefinition *find(uint32_t itemId) const;
    // Standard: timed effects last a number of game minutes per point of power.
    float timedSecondsPerPower() const;
    // Otherwise (MAW) a fixed number of game hours, plus game minutes per Alchemy point of the party's best
    // Grandmaster alchemist.
    float fixedDurationSeconds() const;
    float grandmasterAlchemySecondsPerSkill() const;
    // Potion power is clamped to this before any effect; 0 for no cap.
    int powerCap() const;
    // Recovery a drink costs a ready member, and whether only while monsters are near (0 for none). With a cost, a drink
    // needs a ready member even where it costs nothing.
    float combatRecoveryTicks() const;
    bool combatRecoveryOnlyNearEnemies() const;
    // The active member pays (the original games), not the drinker when ready (MAW).
    bool combatRecoveryActiveMemberPays() const;
    // Every recipe shows in the recipe book from the start (MAW).
    bool allRecipesKnown() const;

private:
    std::unordered_map<uint32_t, PotionDefinition> m_potions;
    float m_timedSecondsPerPower = 0.0f;
    float m_fixedDurationSeconds = 0.0f;
    float m_grandmasterAlchemySecondsPerSkill = 0.0f;
    int m_powerCap = 0;
    float m_combatRecoveryTicks = 0.0f;
    bool m_combatRecoveryOnlyNearEnemies = false;
    bool m_combatRecoveryActiveMemberPays = false;
    bool m_allRecipesKnown = false;
};
}
