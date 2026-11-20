#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
enum class StandardItemEnchantKind : uint8_t
{
    None = 0,
    Might,
    Intellect,
    Personality,
    Endurance,
    Accuracy,
    Speed,
    Luck,
    HitPoints,
    SpellPoints,
    ArmorClass,
    FireResistance,
    AirResistance,
    WaterResistance,
    EarthResistance,
    MindResistance,
    BodyResistance,
    Alchemy,
    Stealing,
    Disarm,
    IdentifyItem,
    IdentifyMonster,
    Armsmaster,
    Dodge,
    Unarmed,
    // A world's own (worlds/<id>/enchantments.yml): Energy resistance (Hesper's "of Insulation").
    EnergyResistance,
};

enum class SpecialItemEnchantKind : uint8_t
{
    None = 0,
    Protection,
    Gods,
    Carnage,
    Cold,
    Frost,
    Ice,
    Sparks,
    Lightning,
    Thunderbolts,
    Fire,
    Flame,
    Infernos,
    Poison,
    Venom,
    Acid,
    Vampiric,
    Recovery,
    Immunity,
    Sanity,
    Freedom,
    Antidotes,
    Alarms,
    Medusa,
    Force,
    Power,
    AirMagic,
    BodyMagic,
    DarkMagic,
    EarthMagic,
    FireMagic,
    LightMagic,
    MindMagic,
    SpiritMagic,
    WaterMagic,
    Thievery,
    Shielding,
    Regeneration,
    Mana,
    OgreSlaying,
    DragonSlaying,
    Darkness,
    Doom,
    Earth,
    Life,
    Rogues,
    TheDragon,
    TheEclipse,
    TheGolem,
    TheMoon,
    ThePhoenix,
    TheSky,
    TheStars,
    TheSun,
    TheTroll,
    TheUnicorn,
    Warriors,
    Wizards,
    Antique,
    Swift,
    Monks,
    Thieves,
    Identifying,
    ElementalSlaying,
    UndeadSlaying,
    David,
    Plenty,
    Assassins,
    Barbarians,
    TheStorm,
    TheOcean,
    WaterWalking,
    FeatherFalling,
    // A special a ruleset adds or renames (MAW's "of Ascension", "Lichs'" and the class specials 74-80); its effect
    // comes from the ruleset's item rules alone.
    RulesetSpecial,
    // A world's own special (worlds/<id>/enchantments.yml): its effect is SpecialItemEnchantEntry::worldEffect.
    World,
};

// What a world's own special enchantment does (worlds/<id>/enchantments.yml effect). On a weapon: more damage to
// raised shields (with the rest at most +100 %) and to bodies without one, a chance per melee hit to halve the target's
// remaining shield, added Energy damage (irresistible) and more damage to the listed monsters. Worn: personal shield
// points and a share more or less Energy damage taken.
struct WorldEnchantEffect
{
    int shieldDamagePercent = 0;
    int exposedDamagePercent = 0;
    int overloadChancePercent = 0;
    int energyDamageMinimum = 0;
    int energyDamageMaximum = 0;
    int bonusDamagePercent = 0;
    std::vector<std::pair<int, int>> bonusMonsterIds;
    int personalShield = 0;
    int energyDamageTakenPercent = 0;

    bool bonusAgainst(int monsterId) const
    {
        for (const auto &[first, last] : bonusMonsterIds)
        {
            if (monsterId >= first && monsterId <= last)
            {
                return true;
            }
        }

        return false;
    }
};

struct ItemEnchantPriceModifier
{
    bool multiplicative = false;
    int amount = 0;
};

struct StandardItemEnchantEntry
{
    StandardItemEnchantKind kind = StandardItemEnchantKind::None;
    std::string statName;
    std::string suffix;
    std::array<int, 9> slotValues = {};
    // A world's own enchantment rolls only on that world's items; empty: everywhere.
    std::vector<std::string> worlds;
};

struct SpecialItemEnchantEntry
{
    SpecialItemEnchantKind kind = SpecialItemEnchantKind::None;
    std::string name;
    std::string suffix;
    std::array<int, 12> slotWeights = {};
    ItemEnchantPriceModifier priceModifier = {};
    char rarityLevel = 0;
    std::string description;
    bool displayAsPrefix = false;
    // A world's own enchantment (kind World): its effect, the worlds whose items roll it (empty: every world) and a
    // content flag the item must carry (Hesper's Overloading: EnergyBlade).
    WorldEnchantEffect worldEffect;
    std::vector<std::string> worlds;
    std::string requiredContentFlag;
};

class StandardItemEnchantTable
{
public:
    bool load(const std::vector<std::vector<std::string>> &rows);
    bool addAt(uint16_t enchantId, StandardItemEnchantEntry entry);
    const std::vector<StandardItemEnchantEntry> &entries() const;
    const StandardItemEnchantEntry *get(uint16_t enchantId) const;

private:
    std::vector<StandardItemEnchantEntry> m_entries;
};

// Adds a world's own enchantments (worlds/<id>/enchantments.yml, schema openyamm.worldEnchantments.v1) at the ids it
// gives them (100-999: past the MM tables and the rulesets' additions), each rolling only on that world's items:
//   standard: [{id, name, stat: energy_resistance, slots: [9 weights: armour ... amulet]}]
//   special: [{id, name, rarity: A-D, slots: [12 weights: W1 W2 Miss Arm ... Amul], value, description,
//              requires_flag, effect: {shield_damage, exposed_damage, overload_chance, energy_damage: [min, max],
//                                      bonus_damage, against: [[first, last] monster ids], personal_shield,
//                                      energy_damage_taken}}]
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
bool loadWorldEnchantments(const std::string &text, const std::string &worldId, StandardItemEnchantTable &standard,
    SpecialItemEnchantTable &special, std::string &errorMessage);

class SpecialItemEnchantTable
{
public:
    bool load(const std::vector<std::vector<std::string>> &rows);
    // Places an entry at its id (padding the ids between with empty entries); false when the id is taken.
    bool addAt(uint16_t enchantId, SpecialItemEnchantEntry entry);
    const std::vector<SpecialItemEnchantEntry> &entries() const;
    const SpecialItemEnchantEntry *get(uint16_t enchantId) const;
    // The id of the first enchantment of this kind, or 0 when the table has none.
    uint16_t findId(SpecialItemEnchantKind kind) const;

private:
    std::vector<SpecialItemEnchantEntry> m_entries;
};
}
