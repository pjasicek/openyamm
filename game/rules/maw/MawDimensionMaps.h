#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class RandomStream;
struct ItemRulesetFields;

// How an affix value reads (calculateAffixPower, zzMaw-Maps.lua:1084-1112).
enum class MawAffixKind : uint8_t
{
    Flat,
    // A chance, at most 100.
    Proc,
    // Shown and applied as 100 x (1 - 1 / (1 + value / 100)), so it never reaches 100.
    Reduction,
};

// The 33 affixes by number (devdocs/maw/data/dimension_affixes.yml).
enum class MawMapAffix : uint8_t
{
    MonsterDamage = 1,
    MonsterCritical = 2,
    Fireball = 3,
    DragonBreath = 4,
    ReflectPhysical = 5,
    ReflectMagic = 6,
    MonsterRegeneration = 7,
    IgnoreStatusResistance = 8,
    SummonOnDeath = 9,
    PlayerHealthDamage = 10,
    MonsterSpeed = 11,
    MonsterResistance = 12,
    ControlResistance = 13,
    EnergyDamage = 14,
    MonsterHealth = 15,
    BossDensity = 16,
    HigherTier = 17,
    BossStrength = 18,
    BecomeBoss = 19,
    PlayerCriticalChance = 20,
    PlayerCriticalDamage = 21,
    PlayerRegeneration = 22,
    PlayerPhysicalDamage = 23,
    PlayerMagicDamage = 24,
    PlayerMovement = 25,
    PlayerAttackSpeed = 26,
    PlayerSpellRecovery = 27,
    PlayerArmor = 28,
    PlayerResistance = 29,
    PlayerMiss = 30,
    Healing = 31,
    Leech = 32,
    BuffEffects = 33,
};

struct MawDimensionAffix
{
    // The inspect line, with {X} for the value.
    std::string text;
    double base = 0;
    double scale = 0;
    MawAffixKind kind = MawAffixKind::Flat;
};

// A dimension map as its item carries it: the target map, four affix slots (0 empty), how many of them are active
// and the power (MAW's BonusStrength, the four affix fields, Bonus and MaxCharges).
struct MawDimensionMap
{
    uint16_t mapId = 0;
    std::array<uint8_t, 4> affixes = {};
    // 1-3; 0 means all four slots (MAW's Bonus 0).
    uint8_t activeSlots = 0;
    uint8_t power = 0;

    static MawDimensionMap fromFields(const ItemRulesetFields &fields);
    void writeFields(ItemRulesetFields &fields) const;
    // The affixes in force on the map: those in the active slots.
    std::array<uint8_t, 4> activeAffixes() const;
    int activeAffixCount() const;
};

// The Dimensional Maps topic's numbers (Global/zzMaw_DimensionalMapsQuest.lua).
struct MawDimensionQuestRules
{
    int firstTier = 80;
    int unlockTier = 500;
    // The ladder's steps: the first tier plus firstStep, each later step one smaller, never below lastStep.
    int firstStep = 30;
    int lastStep = 10;
    std::string textTooLow;
    std::string textGive;
    std::string textNotCleared;
    std::string textReward;
};

// rulesets/maw/data/dimension_maps.yml: the maps a dimension map may open, the families that fill it, the affixes,
// the kill drop and the quest.
class MawDimensionData
{
public:
    bool loadFromYaml(const std::string &text, std::string &errorMessage);

    uint32_t mapItemId() const;
    const std::vector<uint16_t> &dungeons() const;
    const std::vector<int16_t> &families(bool indoor) const;
    const MawDimensionAffix *affix(int affixId) const;
    int affixCount() const;
    // An affix's value at a map power, as it shows and applies; nothing for an unknown affix.
    std::optional<double> affixValue(int affixId, int power) const;
    // The inspect line of an affix at a power.
    std::string affixLine(int affixId, int power) const;
    double dropChance() const;
    int dropLevelRequired() const;
    double bossDropMultiplier() const;
    const MawDimensionQuestRules &quest() const;
    // The first tier of the ladder above a level (nextTier); a tier from an older ladder moves onto this one.
    int nextQuestTier(int tier) const;

    // Fills slots with distinct affixes drawn from the stream, in MAW's order (affix 2, 3, 4, then 1; getUniqueAffix).
    std::array<uint8_t, 4> rollAffixes(RandomStream &stream, const std::array<bool, 4> &slots) const;

private:
    uint32_t m_mapItemId = 0;
    std::vector<uint16_t> m_dungeons;
    std::vector<int16_t> m_indoorFamilies;
    std::vector<int16_t> m_outdoorFamilies;
    std::vector<MawDimensionAffix> m_affixes;
    double m_dropChance = 0;
    int m_dropLevelRequired = 0;
    double m_bossDropMultiplier = 1;
    MawDimensionQuestRules m_quest;
};

// MAW's "power" of a map's active affixes, which scales density, loot and crafting drops: (power + 20) x count.
double mawDimensionStrength(int power, int activeAffixes);
// The map level a dimension map shows and the quest records (getDimensionMapLevel): power x 10 + 20 + the rounded mean
// of the target's level band.
int mawDimensionMapLevel(int power, const std::array<double, 3> &band);
}
