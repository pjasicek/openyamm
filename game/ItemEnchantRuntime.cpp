#include "game/ItemEnchantRuntime.h"

#include "game/GameMechanics.h"
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

bool isMeleeWeaponCategory(ItemEnchantCategory category)
{
    return category == ItemEnchantCategory::OneHandedWeapon || category == ItemEnchantCategory::TwoHandedWeapon;
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

void addConditionImmunity(Character &member, CharacterCondition condition)
{
    member.magicalConditionImmunities.set(static_cast<size_t>(condition));
}

void addPoisonImmunity(Character &member)
{
    addConditionImmunity(member, CharacterCondition::PoisonWeak);
    addConditionImmunity(member, CharacterCondition::PoisonMedium);
    addConditionImmunity(member, CharacterCondition::PoisonSevere);
}

void addDiseaseImmunity(Character &member)
{
    addConditionImmunity(member, CharacterCondition::DiseaseWeak);
    addConditionImmunity(member, CharacterCondition::DiseaseMedium);
    addConditionImmunity(member, CharacterCondition::DiseaseSevere);
}

bool nameContainsToken(const std::string &name, const std::vector<std::string_view> &tokens)
{
    const std::string normalizedName = toLowerCopy(name);

    for (std::string_view token : tokens)
    {
        if (normalizedName.find(std::string(token)) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

bool monsterMatchesAnyToken(
    const std::string &monsterName,
    const std::string &monsterPictureName,
    const std::vector<std::string_view> &tokens)
{
    return nameContainsToken(monsterName, tokens) || nameContainsToken(monsterPictureName, tokens);
}

bool monsterLooksOgreFamily(const std::string &monsterName, const std::string &monsterPictureName)
{
    static const std::vector<std::string_view> OgreTokens = {"ogre", "troll", "cyclops"};
    return monsterMatchesAnyToken(monsterName, monsterPictureName, OgreTokens);
}

bool monsterLooksDragon(const std::string &monsterName, const std::string &monsterPictureName)
{
    static const std::vector<std::string_view> DragonTokens = {"dragon", "wyrm"};
    return monsterMatchesAnyToken(monsterName, monsterPictureName, DragonTokens);
}

bool monsterLooksElemental(const std::string &monsterName, const std::string &monsterPictureName)
{
    static const std::vector<std::string_view> ElementalTokens = {
        "fire elemental",
        "air elemental",
        "water elemental",
        "earth elemental",
        "elemental",
    };
    return monsterMatchesAnyToken(monsterName, monsterPictureName, ElementalTokens);
}

bool monsterLooksUndead(const std::string &monsterName, const std::string &monsterPictureName)
{
    static const std::vector<std::string_view> UndeadTokens = {
        "skeleton",
        "zombie",
        "ghost",
        "ghoul",
        "vampire",
        "lich",
        "mummy",
        "wight",
        "spectre",
        "spirit",
        "undead",
    };
    return monsterMatchesAnyToken(monsterName, monsterPictureName, UndeadTokens);
}

bool monsterLooksTitan(const std::string &monsterName, const std::string &monsterPictureName)
{
    static const std::vector<std::string_view> TitanTokens = {"titan"};
    return monsterMatchesAnyToken(monsterName, monsterPictureName, TitanTokens);
}

uint32_t rareItemId(const ItemDefinition &itemDefinition, const EquippedItemRuntimeState &runtimeState)
{
    if (runtimeState.artifactId != 0)
    {
        return runtimeState.artifactId;
    }

    return itemDefinition.rarity != ItemRarity::Common ? itemDefinition.itemId : 0;
}

int rareItemDamageMultiplierAgainstMonster(
    uint32_t itemId,
    const std::string &monsterName,
    const std::string &monsterPictureName)
{
    switch (itemId)
    {
        case 503:
            return monsterLooksOgreFamily(monsterName, monsterPictureName) ? 2 : 1;

        case 506:
        case 539:
        case 540:
            return monsterLooksDragon(monsterName, monsterPictureName) ? 2 : 1;

        case 538:
            return monsterLooksElemental(monsterName, monsterPictureName) ? 2 : 1;

        default:
            return 1;
    }
}

int specialEnchantDamageMultiplierAgainstMonster(
    uint16_t specialEnchantId,
    const SpecialItemEnchantTable *pSpecialTable,
    const std::string &monsterName,
    const std::string &monsterPictureName)
{
    if (specialEnchantId == 0 || pSpecialTable == nullptr)
    {
        return 1;
    }

    const SpecialItemEnchantEntry *pEntry = pSpecialTable->get(specialEnchantId);

    if (pEntry == nullptr)
    {
        return 1;
    }

    switch (pEntry->kind)
    {
        case SpecialItemEnchantKind::OgreSlaying:
            return monsterLooksOgreFamily(monsterName, monsterPictureName) ? 2 : 1;

        case SpecialItemEnchantKind::DragonSlaying:
            return monsterLooksDragon(monsterName, monsterPictureName) ? 2 : 1;

        case SpecialItemEnchantKind::ElementalSlaying:
            return monsterLooksElemental(monsterName, monsterPictureName) ? 2 : 1;

        case SpecialItemEnchantKind::UndeadSlaying:
            return monsterLooksUndead(monsterName, monsterPictureName) ? 2 : 1;

        case SpecialItemEnchantKind::David:
            return monsterLooksTitan(monsterName, monsterPictureName) ? 2 : 1;

        default:
            return 1;
    }
}

int weaponDamageMultiplierAgainstMonster(
    const ItemDefinition &itemDefinition,
    const EquippedItemRuntimeState &runtimeState,
    const SpecialItemEnchantTable *pSpecialTable,
    const std::string &monsterName,
    const std::string &monsterPictureName)
{
    if (runtimeState.broken)
    {
        return 1;
    }

    const int rareMultiplier = rareItemDamageMultiplierAgainstMonster(
        rareItemId(itemDefinition, runtimeState),
        monsterName,
        monsterPictureName);
    const int specialMultiplier = specialEnchantDamageMultiplierAgainstMonster(
        runtimeState.specialEnchantId,
        pSpecialTable,
        monsterName,
        monsterPictureName);

    return std::max(rareMultiplier, specialMultiplier);
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
            addDiseaseImmunity(member);
            break;

        case SpecialItemEnchantKind::Sanity:
            addConditionImmunity(member, CharacterCondition::Insane);
            break;

        case SpecialItemEnchantKind::Freedom:
            addConditionImmunity(member, CharacterCondition::Paralyzed);
            break;

        case SpecialItemEnchantKind::Antidotes:
            addPoisonImmunity(member);
            break;

        case SpecialItemEnchantKind::Alarms:
            addConditionImmunity(member, CharacterCondition::Asleep);
            break;

        case SpecialItemEnchantKind::Medusa:
            addConditionImmunity(member, CharacterCondition::Petrified);
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

void addAllPrimaryStats(Character &member, int amount)
{
    member.magicalBonuses.might += amount;
    member.magicalBonuses.intellect += amount;
    member.magicalBonuses.personality += amount;
    member.magicalBonuses.endurance += amount;
    member.magicalBonuses.speed += amount;
    member.magicalBonuses.accuracy += amount;
    member.magicalBonuses.luck += amount;
}

void addAllMagicResistances(Character &member, int amount, bool includeSpirit = true)
{
    member.magicalBonuses.resistances.fire += amount;
    member.magicalBonuses.resistances.air += amount;
    member.magicalBonuses.resistances.water += amount;
    member.magicalBonuses.resistances.earth += amount;
    member.magicalBonuses.resistances.mind += amount;
    member.magicalBonuses.resistances.body += amount;

    if (includeSpirit)
    {
        member.magicalBonuses.resistances.spirit += amount;
    }
}

void applyRareItemBonus(Character &member, uint32_t itemId)
{
    switch (itemId)
    {
        case 500:
            member.magicalBonuses.accuracy += 40;
            member.weaponEnchantmentDamageBonus += 20;
            break;

        case 501:
            member.magicalBonuses.might += 40;
            member.weaponEnchantmentDamageBonus += 20;
            break;

        case 502:
            addSkillBonus(member, "Armsmaster", 7);
            member.magicalBonuses.resistances.air += 30;
            break;

        case 503:
            member.magicalBonuses.endurance += 40;
            member.magicalBonuses.luck += 40;
            break;

        case 504:
            member.magicalBonuses.might += 20;
            member.attackRecoveryReductionTicks += 20;
            member.weaponEnchantmentDamageBonus += 12;
            break;

        case 505:
            member.magicalBonuses.resistances.fire += 40;
            member.weaponEnchantmentDamageBonus += 20;
            break;

        case 506:
            member.magicalBonuses.endurance += 20;
            member.attackRecoveryReductionTicks += 20;
            break;

        case 507:
            addAllPrimaryStats(member, 10);
            member.weaponEnchantmentDamageBonus += 20;
            break;

        case 508:
            member.vampiricHealFraction = std::max(member.vampiricHealFraction, 0.2f);
            member.weaponEnchantmentDamageBonus += 10;
            break;

        case 509:
            member.magicalBonuses.personality += 40;
            member.healthRegenPerSecond += 1.0f;
            break;

        case 510:
            member.magicalBonuses.might += 20;
            member.magicalBonuses.endurance += 20;
            member.weaponEnchantmentDamageBonus += 20;
            break;

        case 511:
            member.halfMissileDamage = true;
            addDiseaseImmunity(member);
            addPoisonImmunity(member);
            addConditionImmunity(member, CharacterCondition::Paralyzed);
            break;

        case 512:
            member.magicalBonuses.accuracy += 50;
            addSkillBonus(member, "Bow", 4);
            member.attackRecoveryReductionTicks += 20;
            break;

        case 513:
            member.magicalBonuses.endurance += 30;
            member.spellRegenPerSecond += 1.0f;
            break;

        case 514:
            addAllPrimaryStats(member, 10);
            addAllMagicResistances(member, 10);
            break;

        case 515:
            member.attackRecoveryReductionTicks += 20;
            member.magicalBonuses.speed += 15;
            member.magicalBonuses.accuracy += 15;
            break;

        case 516:
            addHalfLearnedSkillBonus(member, "SpiritMagic");
            addHalfLearnedSkillBonus(member, "MindMagic");
            addHalfLearnedSkillBonus(member, "BodyMagic");
            break;

        case 517:
            addSkillBonus(member, "Disarm", 8);
            addSkillBonus(member, "Bow", 8);
            addSkillBonus(member, "Armsmaster", 8);
            break;

        case 518:
            member.magicalBonuses.speed += 30;
            member.attackRecoveryReductionTicks += 20;
            addConditionImmunity(member, CharacterCondition::Asleep);
            break;

        case 519:
            member.magicalBonuses.resistances.fire += 40;
            member.magicalBonuses.resistances.air += 40;
            member.magicalBonuses.resistances.water += 40;
            member.magicalBonuses.resistances.earth += 40;
            break;

        case 520:
            member.magicalBonuses.personality += 15;
            member.magicalBonuses.intellect += 15;
            member.healthRegenPerSecond += 1.0f;
            break;

        case 521:
            member.magicalBonuses.intellect += 50;
            addHalfLearnedSkillBonus(member, "DarkMagic");
            break;

        case 522:
            member.featherFalling = true;
            member.magicalBonuses.intellect += 30;
            addAllMagicResistances(member, 10);
            break;

        case 523:
            member.magicalBonuses.resistances.water -= 50;
            member.magicalBonuses.personality -= 15;
            break;

        case 524:
            member.magicalBonuses.speed += 70;
            member.magicalBonuses.accuracy += 70;
            member.magicalBonuses.armorClass -= 20;
            break;

        case 525:
            member.magicalBonuses.speed -= 20;
            member.weaponEnchantmentDamageBonus += 20;
            break;

        case 526:
            member.magicalBonuses.might += 70;
            member.magicalBonuses.accuracy += 70;
            member.magicalBonuses.personality -= 50;
            member.magicalBonuses.intellect -= 50;
            break;

        case 527:
            member.vampiricHealFraction = std::max(member.vampiricHealFraction, 0.2f);
            member.magicalBonuses.might += 50;
            member.magicalBonuses.luck -= 40;
            break;

        case 528:
            member.waterWalking = true;
            member.magicalBonuses.resistances.water += 70;
            member.magicalBonuses.resistances.fire -= 70;
            break;

        case 529:
            member.magicalBonuses.might += 40;
            member.weaponEnchantmentDamageBonus += 10;
            member.magicalBonuses.accuracy -= 40;
            break;

        case 530:
            addHalfLearnedSkillBonus(member, "AirMagic");
            addHalfLearnedSkillBonus(member, "FireMagic");
            addHalfLearnedSkillBonus(member, "WaterMagic");
            addHalfLearnedSkillBonus(member, "EarthMagic");
            member.magicalBonuses.armorClass -= 40;
            break;

        case 531:
            member.magicalBonuses.accuracy += 100;
            addSkillBonus(member, "Bow", 5);
            member.magicalBonuses.armorClass -= 20;
            break;

        case 532:
            member.attackRecoveryReductionTicks += 20;
            member.magicalBonuses.accuracy -= 50;
            break;

        case 533:
            member.magicalBonuses.personality += 80;
            member.magicalBonuses.intellect += 70;
            member.magicalBonuses.resistances.mind -= 30;
            member.magicalBonuses.resistances.spirit -= 30;
            break;

        case 534:
            addConditionImmunity(member, CharacterCondition::Fear);
            addConditionImmunity(member, CharacterCondition::Petrified);
            addConditionImmunity(member, CharacterCondition::Paralyzed);
            addConditionImmunity(member, CharacterCondition::Asleep);
            member.magicalBonuses.personality -= 15;
            member.magicalBonuses.luck -= 15;
            break;

        case 535:
            addHalfLearnedSkillBonus(member, "WaterMagic");
            addSkillBonus(member, "Alchemy", 5);
            member.magicalBonuses.intellect += 40;
            member.magicalBonuses.endurance -= 20;
            break;

        case 536:
            member.magicalBonuses.luck += 90;
            member.magicalBonuses.personality -= 50;
            break;

        case 537:
            member.magicalBonuses.might += 100;
            addConditionImmunity(member, CharacterCondition::Fear);
            member.magicalBonuses.accuracy -= 30;
            member.magicalBonuses.armorClass -= 15;
            break;

        case 541:
            member.weaponEnchantmentDamageBonus += 12;
            break;

        case 542:
            break;

        case 538:
        case 539:
        case 540:
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

    const uint32_t rareItemId = runtimeState.artifactId != 0
        ? runtimeState.artifactId
        : (itemDefinition.rarity != ItemRarity::Common ? itemDefinition.itemId : 0);

    if (rareItemId != 0)
    {
        applyRareItemBonus(member, rareItemId);
    }

    if (runtimeState.standardEnchantId != 0 && pStandardTable != nullptr)
    {
        if (const StandardItemEnchantEntry *pEntry = pStandardTable->get(runtimeState.standardEnchantId))
        {
            applyStandardEnchantBonus(
                member,
                pEntry->kind,
                std::max(1, static_cast<int>(runtimeState.standardEnchantPower)));
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

int ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
    const Character &character,
    CharacterAttackMode attackMode,
    const ItemTable *pItemTable,
    const SpecialItemEnchantTable *pSpecialTable,
    const std::string &monsterName,
    const std::string &monsterPictureName)
{
    if (pItemTable == nullptr)
    {
        return 1;
    }

    int multiplier = 1;
    const auto tryWeapon = [&](
                               uint32_t itemId,
                               const EquippedItemRuntimeState &runtimeState,
                               bool requireMissileCategory)
    {
        if (itemId == 0)
        {
            return;
        }

        const ItemDefinition *pItemDefinition = pItemTable->get(itemId);

        if (pItemDefinition == nullptr)
        {
            return;
        }

        const ItemEnchantCategory category = categoryForItem(*pItemDefinition);

        if (requireMissileCategory)
        {
            if (category != ItemEnchantCategory::Missile)
            {
                return;
            }
        }
        else if (!isMeleeWeaponCategory(category))
        {
            return;
        }

        multiplier = std::max(
            multiplier,
            weaponDamageMultiplierAgainstMonster(
                *pItemDefinition,
                runtimeState,
                pSpecialTable,
                monsterName,
                monsterPictureName));
    };

    if (attackMode == CharacterAttackMode::Bow)
    {
        tryWeapon(character.equipment.bow, character.equipmentRuntime.bow, true);
        return multiplier;
    }

    if (attackMode != CharacterAttackMode::Melee)
    {
        return 1;
    }

    tryWeapon(character.equipment.mainHand, character.equipmentRuntime.mainHand, false);
    tryWeapon(character.equipment.offHand, character.equipmentRuntime.offHand, false);
    return multiplier;
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
