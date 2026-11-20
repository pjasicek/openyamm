#pragma once

#include <array>
#include <cstdint>
#include <random>

namespace OpenYAMM::Game
{
// MAW's item formulas (devdocs/maw/data/loot.yml, ITEMS.md §1). Pure: random draws are passed in, so the golden tables
// of loot.yml and data/rarity_golden.csv can be checked exactly.

// The loot rarity of a MAW item, stored on the item (ItemRulesetFields::lootRarity); 0 for an item MAW never rolled.
enum class MawRarity : uint8_t
{
    None = 0,
    Common = 1,
    Uncommon,
    Rare,
    Epic,
    Ancient,
    Primordial,
    Legendary,
    Celestial,
};

const char *mawRarityName(MawRarity rarity);

// MAW's difficulty-dependent loot settings, from the difficulty index 1-9 (MawModelConfig::difficulty).
struct MawLootConfig
{
    int difficulty = 3;
    bool austerity = false;
    // 1.2 Road to Insanity and Beyond Madness, 1.1 Doom, 1.05 Nightmare, else 1 (GetDifficultyExtraPower).
    double enchantPower = 1;
};

// The enchant strength of a loot tier (encStrUp): 1 + 2t to tier 12, then +3 per tier to 100 at tier 37. Tiers may be
// fractional (Celestial items and artifacts scale with a level).
double mawEnchantStrengthCurve(double lootTier, bool austerity);

// The per-twentieth range a rarity rolls its enchant strength from (8-20 Common to Epic, 16-20 Legendary, 20-25
// Ancient, 25 Primordial and Celestial).
struct MawStrengthRange
{
    int minimum = 8;
    int maximum = 20;
};

MawStrengthRange mawEnchantStrengthRange(MawRarity rarity);

// A base enchant's strength at a loot tier for a draw in mawEnchantStrengthRange (rollEnchantStrength).
int mawEnchantStrength(int lootTier, MawRarity rarity, int draw, const MawLootConfig &config);

// Band shares of Common, Uncommon, Rare and Epic in percent (GetEnchantBands); a boss only reaches the first quarter
// of the table.
std::array<double, 4> mawRarityBands(int lootTier, int difficulty, bool boss);

// The chance multiplier of the Epic upgrades (GetRarityMultiplier).
double mawRarityUpgradeMultiplier(int lootTier, int difficulty, bool boss);

// Bad-luck protection (pity_chance): base^(1.38 - base x failures / 2), certain from failures = 2.76 / base.
double mawPityChance(double base, double failures);

inline constexpr double MawCelestialChance = 0.002;
inline constexpr double MawLegendaryChance = 0.03;
inline constexpr double MawPrimordialChance = 0.04;
inline constexpr double MawAncientChance = 0.12;

// The bad-luck counters of the Epic upgrades (MawGameState).
struct MawRarityPity
{
    double celestial = 0;
    double legendary = 0;
    double primordial = 0;
};

struct MawRarityRollInputs
{
    int lootTier = 0;
    int difficulty = 3;
    bool boss = false;
    // Shops never roll Primordial or better and roll Ancient at 4 % without bad-luck protection.
    bool shop = false;
    // Austerity (and shops): no Legendary or Celestial.
    bool noLegendary = false;
    // An Omnipotent boss's drop is always Celestial.
    bool omnipotent = false;
    // On the upgrade chances: a dimension map's 1 + (power + 20) x affixes / 400.
    double upgradeMultiplier = 1;
};

// One drop's rarity (RollItemRarity): a band roll best-first, then on Epic the upgrade cascade Celestial, Legendary,
// Primordial, Ancient with bad-luck protection; updates the counters.
MawRarity mawRollRarity(const MawRarityRollInputs &inputs, MawRarityPity &pity, std::mt19937 &rng);

// The long-run share of each rarity in percent (index MawRarity - 1), with bad-luck protection: the oracle of
// data/rarity_golden.csv and of an in-game odds page.
std::array<double, 8> mawLongRunRarityShares(int lootTier, int difficulty, bool boss);

// Item power (MAW's MaxCharges, item level = 5 x power) for a level: min(floor(level / 5), 100).
int mawItemPowerForLevel(double level);

// The item power a drop rolls (rollTierCharges): Common to Epic draw 12-20, Legendary 16-20, Ancient 20-24 (at least
// +2), Primordial and Celestial 1.2x (at least +4); capped at 255.
MawStrengthRange mawItemPowerRange(MawRarity rarity);
int mawItemPower(int dropLevel, MawRarity rarity, int draw);

// A weapon's damage at an item level (getWeaponDamageForLevel, GetWeaponDamageMinMax): only the dice count comes from
// the table; the ladder rung (1-6) is the base item's place in its family.
struct MawWeaponDamage
{
    double bonus = 0;
    double sides = 0;
    int diceCount = 0;
    int shownBonus = 0;
    int minimum = 0;
    int maximum = 0;
};

MawWeaponDamage mawWeaponDamage(double itemLevel, bool twoHanded, double rung, int diceCount, double quality = 1);

// Armour class at an item power: base AC + round(reference AC x power / 40) (collectArmorAC), the reference being the
// top rung of the family.
int mawArmorClass(int baseArmorClass, int referenceArmorClass, int itemPower, double quality = 1);

// The level a character needs to wear an item (GetLevelRquirement, ItemLevel.WearLevel).
struct MawLevelRequirementRules
{
    bool nightmare = false;
    bool doom = false;
    bool insanity = false;
};

int mawLevelRequirement(int dropLevel, double rung, const MawLevelRequirementRules &rules);

// MAW's item value (getItemValue) before the shop and selling multipliers. Enchant types are the standard enchant ids
// 1-24. Enchant 2's HP and SP branch is priced like enchant 1's (devdocs/maw/DEVIATIONS.md).
struct MawValueInputs
{
    int baseValue = 0;
    int itemPower = 0;
    int enchant1Type = 0;
    int enchant1Strength = 0;
    int enchant2Type = 0;
    int enchant2Strength = 0;
    // The special's price from its table (a factor below 11, else gold added), and whether it grows with the item's
    // power (the stat specials of bonusEffects: x power / 20 before that test, IT:1950-1961).
    int specialValue = 0;
    bool specialScales = false;
    bool legendary = false;
};

double mawItemValue(const MawValueInputs &inputs);
// What a buy screen asks before the merchant: value^(1 + 0.08 x count), count being the enchantments present plus 2
// for an Ancient or Primordial item.
double mawShopBuyValue(double value, int enchantCount, bool ancientTier);
// MAW's price rounding: to 1000 above 200000, 500 above 50000, 100 above 1000, 10 above 100.
int mawRoundPrice(double value);

// A drop's loot tier (the master number): grade + floor(dropLevel / 15) + bonuses, +1 when `fraction` (a uniform draw
// in [0, 1)) is below (dropLevel mod 15) / 15.
int mawLootTier(int grade, double dropLevel, bool boss, bool omnipotent, int extraBonus, double fraction);
}
