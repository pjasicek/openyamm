#pragma once

#include <array>
#include <cstdint>
#include <string>
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
};

class StandardItemEnchantTable
{
public:
    bool load(const std::vector<std::vector<std::string>> &rows);
    const std::vector<StandardItemEnchantEntry> &entries() const;
    const StandardItemEnchantEntry *get(uint16_t enchantId) const;

private:
    std::vector<StandardItemEnchantEntry> m_entries;
};

class SpecialItemEnchantTable
{
public:
    bool load(const std::vector<std::vector<std::string>> &rows);
    const std::vector<SpecialItemEnchantEntry> &entries() const;
    const SpecialItemEnchantEntry *get(uint16_t enchantId) const;

private:
    std::vector<SpecialItemEnchantEntry> m_entries;
};
}
