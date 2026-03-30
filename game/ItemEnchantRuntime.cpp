#include "game/ItemEnchantRuntime.h"

#include "game/ItemTable.h"

#include <algorithm>
#include <cctype>
#include <limits>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr int StandardEnchantMinimumByTreasureLevel[6] = {0, 1, 3, 6, 10, 15};
constexpr int StandardEnchantMaximumByTreasureLevel[6] = {0, 5, 8, 12, 17, 25};
constexpr int StandardEnchantChanceByTreasureLevel[6] = {0, 40, 40, 40, 40, 75};
constexpr int SpecialEnchantChanceForEquipmentByTreasureLevel[6] = {0, 0, 10, 15, 20, 25};
constexpr int SpecialEnchantChanceForWeaponsByTreasureLevel[6] = {0, 0, 10, 20, 30, 50};

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

bool isWeaponCategory(ItemEnchantCategory category)
{
    return category == ItemEnchantCategory::OneHandedWeapon
        || category == ItemEnchantCategory::TwoHandedWeapon
        || category == ItemEnchantCategory::Missile;
}

size_t standardSlotIndex(ItemEnchantCategory category)
{
    switch (category)
    {
        case ItemEnchantCategory::Armor:
            return 0;

        case ItemEnchantCategory::Shield:
            return 1;

        case ItemEnchantCategory::Helm:
            return 2;

        case ItemEnchantCategory::Belt:
            return 3;

        case ItemEnchantCategory::Cloak:
            return 4;

        case ItemEnchantCategory::Gauntlets:
            return 5;

        case ItemEnchantCategory::Boots:
            return 6;

        case ItemEnchantCategory::Ring:
            return 7;

        case ItemEnchantCategory::Amulet:
            return 8;

        case ItemEnchantCategory::None:
        case ItemEnchantCategory::OneHandedWeapon:
        case ItemEnchantCategory::TwoHandedWeapon:
        case ItemEnchantCategory::Missile:
        default:
            return std::numeric_limits<size_t>::max();
    }
}

size_t specialSlotIndex(ItemEnchantCategory category)
{
    switch (category)
    {
        case ItemEnchantCategory::OneHandedWeapon:
            return 0;

        case ItemEnchantCategory::TwoHandedWeapon:
            return 1;

        case ItemEnchantCategory::Missile:
            return 2;

        case ItemEnchantCategory::Armor:
            return 3;

        case ItemEnchantCategory::Shield:
            return 4;

        case ItemEnchantCategory::Helm:
            return 5;

        case ItemEnchantCategory::Belt:
            return 6;

        case ItemEnchantCategory::Cloak:
            return 7;

        case ItemEnchantCategory::Gauntlets:
            return 8;

        case ItemEnchantCategory::Boots:
            return 9;

        case ItemEnchantCategory::Ring:
            return 10;

        case ItemEnchantCategory::Amulet:
            return 11;

        case ItemEnchantCategory::None:
        default:
            return std::numeric_limits<size_t>::max();
    }
}

bool isSpellSchoolSkill(const std::string &skillName)
{
    return skillName == "AirMagic"
        || skillName == "BodyMagic"
        || skillName == "DarkMagic"
        || skillName == "EarthMagic"
        || skillName == "FireMagic"
        || skillName == "LightMagic"
        || skillName == "MindMagic"
        || skillName == "SpiritMagic"
        || skillName == "WaterMagic";
}

void addSkillBonus(Character &member, const std::string &skillName, int amount)
{
    if (skillName.empty() || amount == 0)
    {
        return;
    }

    member.itemSkillBonuses[skillName] += amount;
}

int learnedSkillLevel(const Character &member, const std::string &skillName)
{
    const CharacterSkill *pSkill = member.findSkill(skillName);

    if (pSkill == nullptr || pSkill->mastery == SkillMastery::None)
    {
        return 0;
    }

    return static_cast<int>(pSkill->level);
}

void addHalfLearnedSkillBonus(Character &member, const std::string &skillName)
{
    const int bonus = learnedSkillLevel(member, skillName) / 2;

    if (bonus > 0)
    {
        addSkillBonus(member, skillName, bonus);
    }
}

void applyStandardEnchantBonus(Character &member, StandardItemEnchantKind kind, int amount)
{
    if (amount <= 0)
    {
        return;
    }

    switch (kind)
    {
        case StandardItemEnchantKind::Might:
            member.magicalBonuses.might += amount;
            break;

        case StandardItemEnchantKind::Intellect:
            member.magicalBonuses.intellect += amount;
            break;

        case StandardItemEnchantKind::Personality:
            member.magicalBonuses.personality += amount;
            break;

        case StandardItemEnchantKind::Endurance:
            member.magicalBonuses.endurance += amount;
            break;

        case StandardItemEnchantKind::Accuracy:
            member.magicalBonuses.accuracy += amount;
            break;

        case StandardItemEnchantKind::Speed:
            member.magicalBonuses.speed += amount;
            break;

        case StandardItemEnchantKind::Luck:
            member.magicalBonuses.luck += amount;
            break;

        case StandardItemEnchantKind::HitPoints:
            member.magicalBonuses.maxHealth += amount;
            break;

        case StandardItemEnchantKind::SpellPoints:
            member.magicalBonuses.maxSpellPoints += amount;
            break;

        case StandardItemEnchantKind::ArmorClass:
            member.magicalBonuses.armorClass += amount;
            break;

        case StandardItemEnchantKind::FireResistance:
            member.magicalBonuses.resistances.fire += amount;
            break;

        case StandardItemEnchantKind::AirResistance:
            member.magicalBonuses.resistances.air += amount;
            break;

        case StandardItemEnchantKind::WaterResistance:
            member.magicalBonuses.resistances.water += amount;
            break;

        case StandardItemEnchantKind::EarthResistance:
            member.magicalBonuses.resistances.earth += amount;
            break;

        case StandardItemEnchantKind::MindResistance:
            member.magicalBonuses.resistances.mind += amount;
            break;

        case StandardItemEnchantKind::BodyResistance:
            member.magicalBonuses.resistances.body += amount;
            break;

        case StandardItemEnchantKind::Alchemy:
            addSkillBonus(member, "Alchemy", amount);
            break;

        case StandardItemEnchantKind::Stealing:
            addSkillBonus(member, "Stealing", amount);
            break;

        case StandardItemEnchantKind::Disarm:
            addSkillBonus(member, "Disarm", amount);
            break;

        case StandardItemEnchantKind::IdentifyItem:
            addSkillBonus(member, "IdentifyItem", amount);
            break;

        case StandardItemEnchantKind::IdentifyMonster:
            addSkillBonus(member, "IdentifyMonster", amount);
            break;

        case StandardItemEnchantKind::Armsmaster:
            addSkillBonus(member, "Armsmaster", amount);
            break;

        case StandardItemEnchantKind::Dodge:
            addSkillBonus(member, "Dodging", amount);
            break;

        case StandardItemEnchantKind::Unarmed:
            addSkillBonus(member, "Unarmed", amount);
            break;

        case StandardItemEnchantKind::None:
        default:
            break;
    }
}

void applySpecialEnchantBonus(Character &member, SpecialItemEnchantKind kind)
{
    switch (kind)
    {
        case SpecialItemEnchantKind::Protection:
            member.magicalBonuses.resistances.fire += 10;
            member.magicalBonuses.resistances.air += 10;
            member.magicalBonuses.resistances.water += 10;
            member.magicalBonuses.resistances.earth += 10;
            break;

        case SpecialItemEnchantKind::Gods:
            member.magicalBonuses.might += 10;
            member.magicalBonuses.intellect += 10;
            member.magicalBonuses.personality += 10;
            member.magicalBonuses.endurance += 10;
            member.magicalBonuses.speed += 10;
            member.magicalBonuses.accuracy += 10;
            member.magicalBonuses.luck += 10;
            break;

        case SpecialItemEnchantKind::Vampiric:
            member.vampiricHealFraction = std::max(member.vampiricHealFraction, 0.2f);
            break;

        case SpecialItemEnchantKind::Recovery:
            member.recoveryProgressMultiplier = std::max(member.recoveryProgressMultiplier, 1.5f);
            break;

        case SpecialItemEnchantKind::Immunity:
            break;

        case SpecialItemEnchantKind::Force:
        case SpecialItemEnchantKind::Carnage:
        case SpecialItemEnchantKind::OgreSlaying:
        case SpecialItemEnchantKind::DragonSlaying:
        case SpecialItemEnchantKind::ElementalSlaying:
        case SpecialItemEnchantKind::UndeadSlaying:
        case SpecialItemEnchantKind::David:
            break;

        case SpecialItemEnchantKind::Power:
            break;

        case SpecialItemEnchantKind::AirMagic:
            addHalfLearnedSkillBonus(member, "AirMagic");
            break;

        case SpecialItemEnchantKind::BodyMagic:
            addHalfLearnedSkillBonus(member, "BodyMagic");
            break;

        case SpecialItemEnchantKind::DarkMagic:
            addHalfLearnedSkillBonus(member, "DarkMagic");
            break;

        case SpecialItemEnchantKind::EarthMagic:
            addHalfLearnedSkillBonus(member, "EarthMagic");
            break;

        case SpecialItemEnchantKind::FireMagic:
            addHalfLearnedSkillBonus(member, "FireMagic");
            break;

        case SpecialItemEnchantKind::LightMagic:
            addHalfLearnedSkillBonus(member, "LightMagic");
            break;

        case SpecialItemEnchantKind::MindMagic:
            addHalfLearnedSkillBonus(member, "MindMagic");
            break;

        case SpecialItemEnchantKind::SpiritMagic:
            addHalfLearnedSkillBonus(member, "SpiritMagic");
            break;

        case SpecialItemEnchantKind::WaterMagic:
            addHalfLearnedSkillBonus(member, "WaterMagic");
            break;

        case SpecialItemEnchantKind::Thievery:
            addSkillBonus(member, "Stealing", 2);
            addSkillBonus(member, "Disarm", 2);
            break;

        case SpecialItemEnchantKind::Shielding:
            member.halfMissileDamage = true;
            break;

        case SpecialItemEnchantKind::Regeneration:
            member.healthRegenPerSecond += 1.0f;
            break;

        case SpecialItemEnchantKind::Mana:
            member.spellRegenPerSecond += 1.0f;
            break;

        case SpecialItemEnchantKind::Darkness:
            member.vampiricHealFraction = std::max(member.vampiricHealFraction, 0.2f);
            member.attackRecoveryReductionTicks += 20;
            break;

        case SpecialItemEnchantKind::Doom:
            member.magicalBonuses.might += 1;
            member.magicalBonuses.intellect += 1;
            member.magicalBonuses.personality += 1;
            member.magicalBonuses.endurance += 1;
            member.magicalBonuses.speed += 1;
            member.magicalBonuses.accuracy += 1;
            member.magicalBonuses.luck += 1;
            member.magicalBonuses.maxHealth += 1;
            member.magicalBonuses.maxSpellPoints += 1;
            member.magicalBonuses.armorClass += 1;
            member.magicalBonuses.resistances.fire += 1;
            member.magicalBonuses.resistances.air += 1;
            member.magicalBonuses.resistances.water += 1;
            member.magicalBonuses.resistances.earth += 1;
            break;

        case SpecialItemEnchantKind::Earth:
            member.magicalBonuses.endurance += 10;
            member.magicalBonuses.armorClass += 10;
            member.magicalBonuses.maxHealth += 10;
            break;

        case SpecialItemEnchantKind::Life:
            member.magicalBonuses.maxHealth += 10;
            member.healthRegenPerSecond += 1.0f;
            break;

        case SpecialItemEnchantKind::Rogues:
            member.magicalBonuses.speed += 5;
            member.magicalBonuses.accuracy += 5;
            break;

        case SpecialItemEnchantKind::TheDragon:
            member.magicalBonuses.might += 25;
            break;

        case SpecialItemEnchantKind::TheEclipse:
            member.magicalBonuses.maxSpellPoints += 10;
            member.spellRegenPerSecond += 1.0f;
            break;

        case SpecialItemEnchantKind::TheGolem:
            member.magicalBonuses.endurance += 15;
            member.magicalBonuses.armorClass += 5;
            break;

        case SpecialItemEnchantKind::TheMoon:
            member.magicalBonuses.luck += 10;
            member.magicalBonuses.intellect += 10;
            break;

        case SpecialItemEnchantKind::ThePhoenix:
            member.magicalBonuses.resistances.fire += 30;
            member.healthRegenPerSecond += 1.0f;
            break;

        case SpecialItemEnchantKind::TheSky:
            member.magicalBonuses.intellect += 10;
            member.magicalBonuses.speed += 10;
            member.magicalBonuses.maxSpellPoints += 10;
            break;

        case SpecialItemEnchantKind::TheStars:
            member.magicalBonuses.endurance += 10;
            member.magicalBonuses.accuracy += 10;
            break;

        case SpecialItemEnchantKind::TheSun:
            member.magicalBonuses.might += 10;
            member.magicalBonuses.personality += 10;
            break;

        case SpecialItemEnchantKind::TheTroll:
            member.magicalBonuses.endurance += 15;
            member.healthRegenPerSecond += 1.0f;
            break;

        case SpecialItemEnchantKind::TheUnicorn:
            member.magicalBonuses.luck += 15;
            member.spellRegenPerSecond += 1.0f;
            break;

        case SpecialItemEnchantKind::Warriors:
            member.magicalBonuses.might += 5;
            member.magicalBonuses.endurance += 5;
            break;

        case SpecialItemEnchantKind::Wizards:
            member.magicalBonuses.intellect += 5;
            member.magicalBonuses.personality += 5;
            break;

        case SpecialItemEnchantKind::Antique:
            break;

        case SpecialItemEnchantKind::Swift:
            member.attackRecoveryReductionTicks += 20;
            break;

        case SpecialItemEnchantKind::Monks:
            addSkillBonus(member, "Dodging", 3);
            addSkillBonus(member, "Unarmed", 3);
            break;

        case SpecialItemEnchantKind::Thieves:
            addSkillBonus(member, "Stealing", 3);
            addSkillBonus(member, "Disarm", 3);
            break;

        case SpecialItemEnchantKind::Identifying:
            addSkillBonus(member, "IdentifyItem", 3);
            addSkillBonus(member, "IdentifyMonster", 3);
            break;

        case SpecialItemEnchantKind::Plenty:
            member.healthRegenPerSecond += 1.0f;
            member.spellRegenPerSecond += 1.0f;
            break;

        case SpecialItemEnchantKind::Assassins:
            addSkillBonus(member, "Disarm", 2);
            break;

        case SpecialItemEnchantKind::Barbarians:
            member.magicalBonuses.armorClass += 5;
            break;

        case SpecialItemEnchantKind::TheStorm:
            member.magicalBonuses.resistances.air += 20;
            member.halfMissileDamage = true;
            break;

        case SpecialItemEnchantKind::TheOcean:
            member.magicalBonuses.resistances.water += 10;
            addSkillBonus(member, "Alchemy", 2);
            break;

        case SpecialItemEnchantKind::WaterWalking:
            member.waterWalking = true;
            break;

        case SpecialItemEnchantKind::FeatherFalling:
            member.featherFalling = true;
            break;

        case SpecialItemEnchantKind::Sanity:
        case SpecialItemEnchantKind::Freedom:
        case SpecialItemEnchantKind::Antidotes:
        case SpecialItemEnchantKind::Alarms:
        case SpecialItemEnchantKind::Medusa:
        case SpecialItemEnchantKind::Cold:
        case SpecialItemEnchantKind::Frost:
        case SpecialItemEnchantKind::Ice:
        case SpecialItemEnchantKind::Sparks:
        case SpecialItemEnchantKind::Lightning:
        case SpecialItemEnchantKind::Thunderbolts:
        case SpecialItemEnchantKind::Fire:
        case SpecialItemEnchantKind::Flame:
        case SpecialItemEnchantKind::Infernos:
        case SpecialItemEnchantKind::Poison:
        case SpecialItemEnchantKind::Venom:
        case SpecialItemEnchantKind::Acid:
        case SpecialItemEnchantKind::None:
        default:
            break;
    }
}

int standardEnchantChanceForTreasureLevel(int treasureLevel)
{
    const int clamped = std::clamp(treasureLevel, 1, 6);
    return StandardEnchantChanceByTreasureLevel[clamped - 1];
}

int specialEnchantChanceForTreasureLevel(bool weapon, int treasureLevel)
{
    const int clamped = std::clamp(treasureLevel, 1, 6);
    return weapon
        ? SpecialEnchantChanceForWeaponsByTreasureLevel[clamped - 1]
        : SpecialEnchantChanceForEquipmentByTreasureLevel[clamped - 1];
}
}

bool ItemEnchantRuntime::isEnchantable(const ItemDefinition &itemDefinition)
{
    return categoryForItem(itemDefinition) != ItemEnchantCategory::None;
}

bool ItemEnchantRuntime::canHaveStandardEnchant(const ItemDefinition &itemDefinition)
{
    const ItemEnchantCategory category = categoryForItem(itemDefinition);
    return category != ItemEnchantCategory::None && !isWeaponCategory(category);
}

bool ItemEnchantRuntime::canHaveSpecialEnchant(const ItemDefinition &itemDefinition)
{
    return categoryForItem(itemDefinition) != ItemEnchantCategory::None;
}

ItemEnchantCategory ItemEnchantRuntime::categoryForItem(const ItemDefinition &itemDefinition)
{
    if (itemDefinition.equipStat == "Weapon" || itemDefinition.equipStat == "Weapon1or2")
    {
        return ItemEnchantCategory::OneHandedWeapon;
    }

    if (itemDefinition.equipStat == "Weapon2")
    {
        return ItemEnchantCategory::TwoHandedWeapon;
    }

    if (itemDefinition.equipStat == "Missile")
    {
        return ItemEnchantCategory::Missile;
    }

    if (itemDefinition.equipStat == "Armor")
    {
        return ItemEnchantCategory::Armor;
    }

    if (itemDefinition.equipStat == "Shield")
    {
        return ItemEnchantCategory::Shield;
    }

    if (itemDefinition.equipStat == "Helm")
    {
        return ItemEnchantCategory::Helm;
    }

    if (itemDefinition.equipStat == "Belt")
    {
        return ItemEnchantCategory::Belt;
    }

    if (itemDefinition.equipStat == "Cloak")
    {
        return ItemEnchantCategory::Cloak;
    }

    if (itemDefinition.equipStat == "Gauntlets")
    {
        return ItemEnchantCategory::Gauntlets;
    }

    if (itemDefinition.equipStat == "Boots")
    {
        return ItemEnchantCategory::Boots;
    }

    if (itemDefinition.equipStat == "Ring")
    {
        return ItemEnchantCategory::Ring;
    }

    if (itemDefinition.equipStat == "Amulet")
    {
        return ItemEnchantCategory::Amulet;
    }

    return ItemEnchantCategory::None;
}

int ItemEnchantRuntime::standardEnchantChance(int treasureLevel)
{
    return standardEnchantChanceForTreasureLevel(treasureLevel);
}

int ItemEnchantRuntime::specialEnchantChance(const ItemDefinition &itemDefinition, int treasureLevel)
{
    return specialEnchantChanceForTreasureLevel(isWeaponCategory(categoryForItem(itemDefinition)), treasureLevel);
}

bool ItemEnchantRuntime::isSpecialRarityAllowed(char rarityLevel, int treasureLevel)
{
    const char rarity = static_cast<char>(std::toupper(static_cast<unsigned char>(rarityLevel)));

    switch (std::clamp(treasureLevel, 1, 6))
    {
        case 3:
            return rarity == 'A' || rarity == 'B';

        case 4:
            return rarity == 'A' || rarity == 'B' || rarity == 'C';

        case 5:
            return rarity == 'B' || rarity == 'C' || rarity == 'D';

        case 6:
            return rarity == 'D';

        default:
            return false;
    }
}

std::optional<uint16_t> ItemEnchantRuntime::chooseStandardEnchantId(
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable &table,
    std::mt19937 &rng)
{
    const size_t slotIndex = standardSlotIndex(categoryForItem(itemDefinition));

    if (slotIndex == std::numeric_limits<size_t>::max())
    {
        return std::nullopt;
    }

    std::vector<uint16_t> enchantIds;
    std::vector<int> weights;

    for (size_t index = 0; index < table.entries().size(); ++index)
    {
        const StandardItemEnchantEntry &entry = table.entries()[index];
        const int weight = entry.slotValues[slotIndex];

        if (entry.kind == StandardItemEnchantKind::None || weight <= 0)
        {
            continue;
        }

        enchantIds.push_back(static_cast<uint16_t>(index + 1));
        weights.push_back(weight);
    }

    if (weights.empty())
    {
        return std::nullopt;
    }

    std::discrete_distribution<size_t> distribution(weights.begin(), weights.end());
    return enchantIds[distribution(rng)];
}

std::optional<uint16_t> ItemEnchantRuntime::chooseSpecialEnchantId(
    const ItemDefinition &itemDefinition,
    const SpecialItemEnchantTable &table,
    int treasureLevel,
    std::mt19937 &rng)
{
    const size_t slotIndex = specialSlotIndex(categoryForItem(itemDefinition));

    if (slotIndex == std::numeric_limits<size_t>::max())
    {
        return std::nullopt;
    }

    std::vector<uint16_t> enchantIds;
    std::vector<int> weights;

    for (size_t index = 0; index < table.entries().size(); ++index)
    {
        const SpecialItemEnchantEntry &entry = table.entries()[index];
        const int weight = entry.slotWeights[slotIndex];

        if (entry.kind == SpecialItemEnchantKind::None
            || weight <= 0
            || !isSpecialRarityAllowed(entry.rarityLevel, treasureLevel))
        {
            continue;
        }

        enchantIds.push_back(static_cast<uint16_t>(index + 1));
        weights.push_back(weight);
    }

    if (weights.empty())
    {
        return std::nullopt;
    }

    std::discrete_distribution<size_t> distribution(weights.begin(), weights.end());
    return enchantIds[distribution(rng)];
}

int ItemEnchantRuntime::generateStandardEnchantPower(StandardItemEnchantKind kind, int treasureLevel, std::mt19937 &rng)
{
    const int clamped = std::clamp(treasureLevel, 1, 6);
    const int minimumValue = StandardEnchantMinimumByTreasureLevel[clamped - 1];
    const int maximumValue = StandardEnchantMaximumByTreasureLevel[clamped - 1];

    if (maximumValue <= 0)
    {
        return 0;
    }

    int value = std::uniform_int_distribution<int>(minimumValue, maximumValue)(rng);

    if (kind == StandardItemEnchantKind::Armsmaster
        || kind == StandardItemEnchantKind::Dodge
        || kind == StandardItemEnchantKind::Unarmed)
    {
        value /= 2;
    }

    return std::max(1, value);
}

std::string ItemEnchantRuntime::displayName(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable)
{
    const std::string baseName = itemDefinition.name.empty() ? "Unknown item" : itemDefinition.name;

    if (item.standardEnchantId != 0 && pStandardTable != nullptr)
    {
        if (const StandardItemEnchantEntry *pEntry = pStandardTable->get(item.standardEnchantId))
        {
            if (!pEntry->suffix.empty())
            {
                return baseName + " " + pEntry->suffix;
            }
        }
    }

    if (item.specialEnchantId != 0 && pSpecialTable != nullptr)
    {
        if (const SpecialItemEnchantEntry *pEntry = pSpecialTable->get(item.specialEnchantId))
        {
            if (!pEntry->suffix.empty())
            {
                return pEntry->displayAsPrefix ? (pEntry->suffix + " " + baseName) : (baseName + " " + pEntry->suffix);
            }
        }
    }

    return baseName;
}

int ItemEnchantRuntime::itemValue(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable)
{
    if (item.broken)
    {
        return 1;
    }

    int value = std::max(1, itemDefinition.value);

    if (item.standardEnchantId != 0 && pStandardTable != nullptr)
    {
        if (pStandardTable->get(item.standardEnchantId) != nullptr)
        {
            value += 100 * std::max(1, static_cast<int>(item.standardEnchantPower));
        }
    }

    if (item.specialEnchantId != 0 && pSpecialTable != nullptr)
    {
        if (const SpecialItemEnchantEntry *pEntry = pSpecialTable->get(item.specialEnchantId))
        {
            if (pEntry->priceModifier.multiplicative && pEntry->priceModifier.amount > 1)
            {
                value *= pEntry->priceModifier.amount;
            }
            else
            {
                value += std::max(0, pEntry->priceModifier.amount);
            }
        }
    }

    return std::max(1, value);
}

std::string ItemEnchantRuntime::buildEnchantDescription(
    const InventoryItem &item,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable)
{
    if (item.standardEnchantId != 0 && pStandardTable != nullptr)
    {
        if (const StandardItemEnchantEntry *pEntry = pStandardTable->get(item.standardEnchantId))
        {
            if (!pEntry->statName.empty() && item.standardEnchantPower > 0)
            {
                return pEntry->statName + " +" + std::to_string(item.standardEnchantPower);
            }
        }
    }

    if (item.specialEnchantId != 0 && pSpecialTable != nullptr)
    {
        if (const SpecialItemEnchantEntry *pEntry = pSpecialTable->get(item.specialEnchantId))
        {
            return pEntry->description;
        }
    }

    return {};
}

void ItemEnchantRuntime::applyEquippedEnchantEffects(
    const ItemDefinition &itemDefinition,
    const EquippedItemRuntimeState &runtimeState,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    Character &member)
{
    if (runtimeState.broken)
    {
        return;
    }

    if (runtimeState.standardEnchantId != 0 && pStandardTable != nullptr)
    {
        if (const StandardItemEnchantEntry *pEntry = pStandardTable->get(runtimeState.standardEnchantId))
        {
            applyStandardEnchantBonus(member, pEntry->kind, std::max(1, static_cast<int>(runtimeState.standardEnchantPower)));
        }
    }

    if (runtimeState.specialEnchantId != 0 && pSpecialTable != nullptr)
    {
        if (const SpecialItemEnchantEntry *pEntry = pSpecialTable->get(runtimeState.specialEnchantId))
        {
            applySpecialEnchantBonus(member, pEntry->kind);
            member.weaponEnchantmentDamageBonus += elementalDamageBonus(
                InventoryItem{
                    itemDefinition.itemId,
                    1,
                    1,
                    1,
                    0,
                    0,
                    true,
                    false,
                    false,
                    0,
                    0,
                    runtimeState.specialEnchantId,
                    0},
                pSpecialTable);
        }
    }
}

int ItemEnchantRuntime::elementalDamageBonus(const InventoryItem &item, const SpecialItemEnchantTable *pSpecialTable)
{
    if (item.specialEnchantId == 0 || pSpecialTable == nullptr)
    {
        return 0;
    }

    const SpecialItemEnchantEntry *pEntry = pSpecialTable->get(item.specialEnchantId);

    if (pEntry == nullptr)
    {
        return 0;
    }

    switch (pEntry->kind)
    {
        case SpecialItemEnchantKind::Cold:
            return 4;

        case SpecialItemEnchantKind::Frost:
            return 8;

        case SpecialItemEnchantKind::Ice:
            return 12;

        case SpecialItemEnchantKind::Sparks:
            return 5;

        case SpecialItemEnchantKind::Lightning:
            return 10;

        case SpecialItemEnchantKind::Thunderbolts:
            return 15;

        case SpecialItemEnchantKind::Fire:
            return 6;

        case SpecialItemEnchantKind::Flame:
            return 12;

        case SpecialItemEnchantKind::Infernos:
            return 18;

        case SpecialItemEnchantKind::Poison:
            return 5;

        case SpecialItemEnchantKind::Venom:
            return 8;

        case SpecialItemEnchantKind::Acid:
            return 12;

        case SpecialItemEnchantKind::TheDragon:
            return 20;

        case SpecialItemEnchantKind::Assassins:
            return 5;

        case SpecialItemEnchantKind::Barbarians:
            return 8;

        case SpecialItemEnchantKind::None:
        default:
            return 0;
    }
}
}
