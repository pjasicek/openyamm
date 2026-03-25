#include "game/GameMechanics.h"

#include "game/CharacterDollTable.h"
#include "game/ItemTable.h"

#include <algorithm>
#include <array>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr int GameStartingYear = 1168;

constexpr int ParameterBonusThresholds[29] = {
    500, 400, 350, 300, 275, 250, 225, 200, 175, 150, 125, 100, 75, 50, 40,
    35, 30, 25, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3, 0,
};

constexpr int ParameterBonusValues[29] = {
    30, 25, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8,
    7, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5, -6,
};

struct DamageDice
{
    int rolls = 0;
    int sides = 0;
};

struct EquippedItems
{
    const ItemDefinition *pOffHand = nullptr;
    const ItemDefinition *pMainHand = nullptr;
    const ItemDefinition *pBow = nullptr;
    const ItemDefinition *pArmor = nullptr;
    const ItemDefinition *pHelm = nullptr;
    const ItemDefinition *pBelt = nullptr;
    const ItemDefinition *pCloak = nullptr;
    const ItemDefinition *pGauntlets = nullptr;
    const ItemDefinition *pBoots = nullptr;
    const ItemDefinition *pAmulet = nullptr;
    const ItemDefinition *pRing1 = nullptr;
    const ItemDefinition *pRing2 = nullptr;
    const ItemDefinition *pRing3 = nullptr;
    const ItemDefinition *pRing4 = nullptr;
    const ItemDefinition *pRing5 = nullptr;
    const ItemDefinition *pRing6 = nullptr;
};

uint32_t equippedItemId(const CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipment.offHand;

        case EquipmentSlot::MainHand:
            return equipment.mainHand;

        case EquipmentSlot::Bow:
            return equipment.bow;

        case EquipmentSlot::Armor:
            return equipment.armor;

        case EquipmentSlot::Helm:
            return equipment.helm;

        case EquipmentSlot::Belt:
            return equipment.belt;

        case EquipmentSlot::Cloak:
            return equipment.cloak;

        case EquipmentSlot::Gauntlets:
            return equipment.gauntlets;

        case EquipmentSlot::Boots:
            return equipment.boots;

        case EquipmentSlot::Amulet:
            return equipment.amulet;

        case EquipmentSlot::Ring1:
            return equipment.ring1;

        case EquipmentSlot::Ring2:
            return equipment.ring2;

        case EquipmentSlot::Ring3:
            return equipment.ring3;

        case EquipmentSlot::Ring4:
            return equipment.ring4;

        case EquipmentSlot::Ring5:
            return equipment.ring5;

        case EquipmentSlot::Ring6:
            return equipment.ring6;
    }

    return 0;
}

bool isRingSlot(EquipmentSlot slot)
{
    return slot == EquipmentSlot::Ring1
        || slot == EquipmentSlot::Ring2
        || slot == EquipmentSlot::Ring3
        || slot == EquipmentSlot::Ring4
        || slot == EquipmentSlot::Ring5
        || slot == EquipmentSlot::Ring6;
}

std::array<EquipmentSlot, 6> allRingSlots()
{
    return {
        EquipmentSlot::Ring1,
        EquipmentSlot::Ring2,
        EquipmentSlot::Ring3,
        EquipmentSlot::Ring4,
        EquipmentSlot::Ring5,
        EquipmentSlot::Ring6,
    };
}

int parseIntegerOrZero(const std::string &text)
{
    if (text.empty())
    {
        return 0;
    }

    try
    {
        return std::stoi(text);
    }
    catch (...)
    {
        return 0;
    }
}

bool tryParseDamageDice(const std::string &text, DamageDice &damageDice)
{
    const size_t separator = text.find('d');

    if (separator == std::string::npos)
    {
        return false;
    }

    const std::string rollCountText = text.substr(0, separator);
    const std::string sideCountText = text.substr(separator + 1);

    if (rollCountText.empty() || sideCountText.empty())
    {
        return false;
    }

    try
    {
        damageDice.rolls = std::stoi(rollCountText);
        damageDice.sides = std::stoi(sideCountText);
    }
    catch (...)
    {
        return false;
    }

    return damageDice.rolls > 0 && damageDice.sides > 0;
}

int parameterBonus(int value)
{
    for (size_t index = 0; index < std::size(ParameterBonusThresholds); ++index)
    {
        if (value >= ParameterBonusThresholds[index])
        {
            return ParameterBonusValues[index];
        }
    }

    return ParameterBonusValues[std::size(ParameterBonusValues) - 1];
}

bool hasCondition(const Character &character, CharacterCondition condition)
{
    return character.conditions.test(static_cast<size_t>(condition));
}

int skillLevel(const Character &character, std::string_view skillName)
{
    const CharacterSkill *pSkill = character.findSkill(std::string(skillName));
    return pSkill != nullptr ? static_cast<int>(pSkill->level) : 0;
}

SkillMastery skillMastery(const Character &character, std::string_view skillName)
{
    const CharacterSkill *pSkill = character.findSkill(std::string(skillName));
    return pSkill != nullptr ? pSkill->mastery : SkillMastery::None;
}

int masteryMultiplier(SkillMastery mastery, int novice, int expert, int master, int grandmaster)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return novice;

        case SkillMastery::Expert:
            return expert;

        case SkillMastery::Master:
            return master;

        case SkillMastery::Grandmaster:
            return grandmaster;

        case SkillMastery::None:
        default:
            return 0;
    }
}

const ItemDefinition *getEquippedItem(const Character &character, EquipmentSlot slot, const ItemTable *pItemTable)
{
    if (pItemTable == nullptr)
    {
        return nullptr;
    }

    const uint32_t itemId = equippedItemId(character.equipment, slot);
    return itemId != 0 ? pItemTable->get(itemId) : nullptr;
}

EquippedItems resolveEquippedItems(const Character &character, const ItemTable *pItemTable)
{
    EquippedItems equippedItems = {};
    equippedItems.pOffHand = getEquippedItem(character, EquipmentSlot::OffHand, pItemTable);
    equippedItems.pMainHand = getEquippedItem(character, EquipmentSlot::MainHand, pItemTable);
    equippedItems.pBow = getEquippedItem(character, EquipmentSlot::Bow, pItemTable);
    equippedItems.pArmor = getEquippedItem(character, EquipmentSlot::Armor, pItemTable);
    equippedItems.pHelm = getEquippedItem(character, EquipmentSlot::Helm, pItemTable);
    equippedItems.pBelt = getEquippedItem(character, EquipmentSlot::Belt, pItemTable);
    equippedItems.pCloak = getEquippedItem(character, EquipmentSlot::Cloak, pItemTable);
    equippedItems.pGauntlets = getEquippedItem(character, EquipmentSlot::Gauntlets, pItemTable);
    equippedItems.pBoots = getEquippedItem(character, EquipmentSlot::Boots, pItemTable);
    equippedItems.pAmulet = getEquippedItem(character, EquipmentSlot::Amulet, pItemTable);
    equippedItems.pRing1 = getEquippedItem(character, EquipmentSlot::Ring1, pItemTable);
    equippedItems.pRing2 = getEquippedItem(character, EquipmentSlot::Ring2, pItemTable);
    equippedItems.pRing3 = getEquippedItem(character, EquipmentSlot::Ring3, pItemTable);
    equippedItems.pRing4 = getEquippedItem(character, EquipmentSlot::Ring4, pItemTable);
    equippedItems.pRing5 = getEquippedItem(character, EquipmentSlot::Ring5, pItemTable);
    equippedItems.pRing6 = getEquippedItem(character, EquipmentSlot::Ring6, pItemTable);
    return equippedItems;
}

std::array<const ItemDefinition *, 16> allEquippedItems(const EquippedItems &equippedItems)
{
    return {
        equippedItems.pOffHand,
        equippedItems.pMainHand,
        equippedItems.pBow,
        equippedItems.pArmor,
        equippedItems.pHelm,
        equippedItems.pBelt,
        equippedItems.pCloak,
        equippedItems.pGauntlets,
        equippedItems.pBoots,
        equippedItems.pAmulet,
        equippedItems.pRing1,
        equippedItems.pRing2,
        equippedItems.pRing3,
        equippedItems.pRing4,
        equippedItems.pRing5,
        equippedItems.pRing6,
    };
}

bool isPassiveArmorItem(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "Armor"
        || itemDefinition.equipStat == "Shield"
        || itemDefinition.equipStat == "Helm"
        || itemDefinition.equipStat == "Belt"
        || itemDefinition.equipStat == "Cloak"
        || itemDefinition.equipStat == "Gauntlets"
        || itemDefinition.equipStat == "Boots"
        || itemDefinition.equipStat == "Amulet"
        || itemDefinition.equipStat == "Ring";
}

bool isMeleeWeapon(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "Weapon"
        || itemDefinition.equipStat == "Weapon2"
        || itemDefinition.equipStat == "Weapon1or2";
}

bool isRangedWeapon(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "Missile";
}

bool isWandWeapon(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "WeaponW";
}

bool isShieldItem(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "Shield";
}

bool isTwoHandedWeapon(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "Weapon2";
}

bool isSpearItem(const ItemDefinition &itemDefinition)
{
    return canonicalSkillName(itemDefinition.skillGroup) == "Spear";
}

bool isWeaponItem(const ItemDefinition &itemDefinition)
{
    return isMeleeWeapon(itemDefinition) || isWandWeapon(itemDefinition);
}

bool requiresLearnedSkillToEquip(const ItemDefinition &itemDefinition)
{
    const std::string skillName = canonicalSkillName(itemDefinition.skillGroup);
    return !skillName.empty() && skillName != "Misc";
}

bool isRestrictedByDollType(const ItemDefinition &itemDefinition, const CharacterDollTypeEntry *pCharacterDollType)
{
    if (pCharacterDollType == nullptr)
    {
        return false;
    }

    if (itemDefinition.equipStat == "Missile")
    {
        return !pCharacterDollType->canEquipBow;
    }

    if (itemDefinition.equipStat == "Armor")
    {
        return !pCharacterDollType->canEquipArmor;
    }

    if (itemDefinition.equipStat == "Helm")
    {
        return !pCharacterDollType->canEquipHelm;
    }

    if (itemDefinition.equipStat == "Belt")
    {
        return !pCharacterDollType->canEquipBelt;
    }

    if (itemDefinition.equipStat == "Boots")
    {
        return !pCharacterDollType->canEquipBoots;
    }

    if (itemDefinition.equipStat == "Cloak")
    {
        return !pCharacterDollType->canEquipCloak;
    }

    if (isWeaponItem(itemDefinition) || isShieldItem(itemDefinition))
    {
        return !pCharacterDollType->canEquipWeapon;
    }

    return false;
}

std::optional<EquipmentSlot> firstFreeRingSlot(const Character &character)
{
    for (EquipmentSlot slot : allRingSlots())
    {
        if (equippedItemId(character.equipment, slot) == 0)
        {
            return slot;
        }
    }

    return std::nullopt;
}

int itemDamageModifier(const ItemDefinition &itemDefinition)
{
    return parseIntegerOrZero(itemDefinition.mod2);
}

int passiveArmorValue(const ItemDefinition &itemDefinition)
{
    if (!isPassiveArmorItem(itemDefinition))
    {
        return 0;
    }

    return parseIntegerOrZero(itemDefinition.mod1) + parseIntegerOrZero(itemDefinition.mod2);
}

int weaponMinDamage(const ItemDefinition &itemDefinition)
{
    DamageDice damageDice = {};

    if (!tryParseDamageDice(itemDefinition.mod1, damageDice))
    {
        return std::max(0, itemDamageModifier(itemDefinition));
    }

    return damageDice.rolls + itemDamageModifier(itemDefinition);
}

int weaponMaxDamage(const ItemDefinition &itemDefinition)
{
    DamageDice damageDice = {};

    if (!tryParseDamageDice(itemDefinition.mod1, damageDice))
    {
        return std::max(0, itemDamageModifier(itemDefinition));
    }

    return damageDice.rolls * damageDice.sides + itemDamageModifier(itemDefinition);
}

bool isUnarmed(const EquippedItems &equippedItems)
{
    const bool hasMainWeapon = equippedItems.pMainHand != nullptr && isMeleeWeapon(*equippedItems.pMainHand);
    const bool hasOffWeapon = equippedItems.pOffHand != nullptr && isMeleeWeapon(*equippedItems.pOffHand);
    return !hasMainWeapon && !hasOffWeapon;
}

int resolveArmsmasterAttackBonus(const Character &character)
{
    const int level = skillLevel(character, "Armsmaster");

    if (level <= 0)
    {
        return 0;
    }

    const int multiplier = masteryMultiplier(skillMastery(character, "Armsmaster"), 0, 1, 1, 2);
    return multiplier * level;
}

int resolveArmsmasterDamageBonus(const Character &character)
{
    const int level = skillLevel(character, "Armsmaster");

    if (level <= 0)
    {
        return 0;
    }

    const int multiplier = masteryMultiplier(skillMastery(character, "Armsmaster"), 0, 0, 1, 2);
    return multiplier * level;
}

int resolveMeleeAttackSkillBonus(const Character &character, const EquippedItems &equippedItems)
{
    const int armsmasterBonus = resolveArmsmasterAttackBonus(character);

    if (isUnarmed(equippedItems))
    {
        const int level = skillLevel(character, "Unarmed");
        const int multiplier = masteryMultiplier(skillMastery(character, "Unarmed"), 1, 1, 2, 2);
        return armsmasterBonus + multiplier * level;
    }

    if (equippedItems.pMainHand != nullptr && isMeleeWeapon(*equippedItems.pMainHand))
    {
        const std::string skillName = canonicalSkillName(equippedItems.pMainHand->skillGroup);
        const int level = skillLevel(character, skillName);

        if (skillName == "Blaster")
        {
            const int multiplier = masteryMultiplier(skillMastery(character, "Blaster"), 1, 2, 3, 5);
            return multiplier * level;
        }

        if (skillName == "Staff" && skillMastery(character, "Staff") == SkillMastery::Grandmaster)
        {
            const int unarmedLevel = skillLevel(character, "Unarmed");
            const int unarmedMultiplier = masteryMultiplier(skillMastery(character, "Unarmed"), 1, 1, 2, 2);
            return armsmasterBonus + level + unarmedMultiplier * unarmedLevel;
        }

        return armsmasterBonus + level;
    }

    return armsmasterBonus;
}

int resolveMeleeDamageSkillBonus(const Character &character, const EquippedItems &equippedItems)
{
    const int armsmasterBonus = resolveArmsmasterDamageBonus(character);

    if (isUnarmed(equippedItems))
    {
        const int level = skillLevel(character, "Unarmed");
        const int multiplier = masteryMultiplier(skillMastery(character, "Unarmed"), 0, 1, 2, 2);
        return multiplier * level;
    }

    if (equippedItems.pMainHand == nullptr || !isMeleeWeapon(*equippedItems.pMainHand))
    {
        return armsmasterBonus;
    }

    const std::string skillName = canonicalSkillName(equippedItems.pMainHand->skillGroup);
    const int level = skillLevel(character, skillName);

    if (skillName == "Staff")
    {
        if (skillMastery(character, "Staff") == SkillMastery::Grandmaster)
        {
            const int unarmedLevel = skillLevel(character, "Unarmed");
            const int unarmedMultiplier = masteryMultiplier(skillMastery(character, "Unarmed"), 0, 1, 2, 2);
            return unarmedMultiplier * unarmedLevel;
        }

        return armsmasterBonus;
    }

    if (skillName == "Dagger")
    {
        return armsmasterBonus + masteryMultiplier(skillMastery(character, "Dagger"), 0, 0, 0, 1) * level;
    }

    if (skillName == "Sword")
    {
        return armsmasterBonus;
    }

    if (skillName == "Mace" || skillName == "Spear")
    {
        return armsmasterBonus + masteryMultiplier(skillMastery(character, skillName), 0, 1, 1, 1) * level;
    }

    if (skillName == "Axe")
    {
        return armsmasterBonus + masteryMultiplier(skillMastery(character, "Axe"), 0, 0, 1, 1) * level;
    }

    if (skillName == "Blaster")
    {
        return masteryMultiplier(skillMastery(character, "Blaster"), 0, 0, 0, 0) * level;
    }

    return armsmasterBonus;
}

int resolveRangedAttackSkillBonus(const Character &character, const EquippedItems &equippedItems)
{
    if (equippedItems.pBow == nullptr || !isRangedWeapon(*equippedItems.pBow))
    {
        return 0;
    }

    const std::string skillName = canonicalSkillName(equippedItems.pBow->skillGroup);
    const int level = skillLevel(character, skillName);

    if (skillName == "Bow")
    {
        return masteryMultiplier(skillMastery(character, "Bow"), 1, 1, 1, 1) * level;
    }

    if (skillName == "Blaster")
    {
        return masteryMultiplier(skillMastery(character, "Blaster"), 1, 2, 3, 5) * level;
    }

    return level;
}

int resolveRangedDamageSkillBonus(const Character &character, const EquippedItems &equippedItems)
{
    if (equippedItems.pBow == nullptr || !isRangedWeapon(*equippedItems.pBow))
    {
        return 0;
    }

    const std::string skillName = canonicalSkillName(equippedItems.pBow->skillGroup);
    const int level = skillLevel(character, skillName);

    if (skillName == "Bow")
    {
        return masteryMultiplier(skillMastery(character, "Bow"), 0, 0, 0, 1) * level;
    }

    return 0;
}

int resolveArmorSkillBonus(const Character &character, const EquippedItems &equippedItems)
{
    bool wearingArmor = false;
    bool wearingLeather = false;
    int armorClassBonus = 0;
    const std::array<const ItemDefinition *, 16> equipped = allEquippedItems(equippedItems);

    for (const ItemDefinition *pItemDefinition : equipped)
    {
        if (pItemDefinition == nullptr)
        {
            continue;
        }

        const std::string skillName = canonicalSkillName(pItemDefinition->skillGroup);

        if (skillName == "Staff")
        {
            armorClassBonus +=
                masteryMultiplier(skillMastery(character, "Staff"), 0, 1, 1, 1) * skillLevel(character, "Staff");
        }
        else if (skillName == "Sword")
        {
            armorClassBonus +=
                masteryMultiplier(skillMastery(character, "Sword"), 0, 0, 0, 1) * skillLevel(character, "Sword");
        }
        else if (skillName == "Spear")
        {
            armorClassBonus +=
                masteryMultiplier(skillMastery(character, "Spear"), 0, 0, 0, 1) * skillLevel(character, "Spear");
        }
        else if (skillName == "Shield")
        {
            wearingArmor = true;
            armorClassBonus +=
                masteryMultiplier(skillMastery(character, "Shield"), 1, 1, 2, 2) * skillLevel(character, "Shield");
        }
        else if (skillName == "LeatherArmor")
        {
            wearingLeather = true;
            armorClassBonus +=
                masteryMultiplier(skillMastery(character, "LeatherArmor"), 1, 1, 2, 2)
                * skillLevel(character, "LeatherArmor");
        }
        else if (skillName == "ChainArmor")
        {
            wearingArmor = true;
            armorClassBonus +=
                masteryMultiplier(skillMastery(character, "ChainArmor"), 1, 1, 1, 1)
                * skillLevel(character, "ChainArmor");
        }
        else if (skillName == "PlateArmor")
        {
            wearingArmor = true;
            armorClassBonus +=
                masteryMultiplier(skillMastery(character, "PlateArmor"), 1, 1, 1, 1)
                * skillLevel(character, "PlateArmor");
        }
    }

    const int dodgeLevel = skillLevel(character, "Dodging");
    const SkillMastery dodgeMastery = skillMastery(character, "Dodging");

    if (!wearingArmor && (!wearingLeather || dodgeMastery == SkillMastery::Grandmaster))
    {
        armorClassBonus += masteryMultiplier(dodgeMastery, 1, 2, 3, 3) * dodgeLevel;
    }

    return armorClassBonus;
}

int resolvePassiveArmorBonus(const EquippedItems &equippedItems)
{
    int armorValue = 0;
    const std::array<const ItemDefinition *, 16> equipped = allEquippedItems(equippedItems);

    for (const ItemDefinition *pItemDefinition : equipped)
    {
        if (pItemDefinition == nullptr)
        {
            continue;
        }

        armorValue += passiveArmorValue(*pItemDefinition);
    }

    return armorValue;
}

int resolveMeleeAttackItemBonus(const EquippedItems &equippedItems)
{
    int attackBonus = 0;

    if (equippedItems.pMainHand != nullptr && isMeleeWeapon(*equippedItems.pMainHand))
    {
        attackBonus += itemDamageModifier(*equippedItems.pMainHand);
    }

    if (equippedItems.pOffHand != nullptr && isMeleeWeapon(*equippedItems.pOffHand))
    {
        attackBonus += itemDamageModifier(*equippedItems.pOffHand);
    }

    return attackBonus;
}

int resolveMeleeMinDamageItemBonus(const EquippedItems &equippedItems)
{
    if (isUnarmed(equippedItems))
    {
        return 1;
    }

    int damage = 0;

    if (equippedItems.pMainHand != nullptr && isMeleeWeapon(*equippedItems.pMainHand))
    {
        damage += weaponMinDamage(*equippedItems.pMainHand);

        if (canonicalSkillName(equippedItems.pMainHand->skillGroup) == "Spear" && equippedItems.pOffHand == nullptr)
        {
            damage += 1;
        }
    }

    if (equippedItems.pOffHand != nullptr && isMeleeWeapon(*equippedItems.pOffHand))
    {
        damage += weaponMinDamage(*equippedItems.pOffHand);
    }

    return damage;
}

int resolveMeleeMaxDamageItemBonus(const EquippedItems &equippedItems)
{
    if (isUnarmed(equippedItems))
    {
        return 3;
    }

    int damage = 0;

    if (equippedItems.pMainHand != nullptr && isMeleeWeapon(*equippedItems.pMainHand))
    {
        damage += weaponMaxDamage(*equippedItems.pMainHand);
    }

    if (equippedItems.pOffHand != nullptr && isMeleeWeapon(*equippedItems.pOffHand))
    {
        damage += weaponMaxDamage(*equippedItems.pOffHand);
    }

    return damage;
}

std::optional<int> resolveRangedAttack(const Character &character, const EquippedItems &equippedItems)
{
    if (equippedItems.pBow == nullptr || !isRangedWeapon(*equippedItems.pBow))
    {
        return std::nullopt;
    }

    const int accuracy = static_cast<int>(character.accuracy)
        + character.permanentBonuses.accuracy
        + character.magicalBonuses.accuracy;
    const int attack = parameterBonus(accuracy)
        + itemDamageModifier(*equippedItems.pBow)
        + resolveRangedAttackSkillBonus(character, equippedItems)
        + character.permanentBonuses.rangedAttack
        + character.magicalBonuses.rangedAttack;
    return attack;
}

std::string formatDamageRange(int minimumDamage, int maximumDamage)
{
    if (minimumDamage == maximumDamage)
    {
        return std::to_string(minimumDamage);
    }

    return std::to_string(minimumDamage) + " - " + std::to_string(maximumDamage);
}

CharacterSheetValue makeSheetValue(int baseValue, int actualValue)
{
    CharacterSheetValue value = {};
    value.base = baseValue;
    value.actual = actualValue;
    return value;
}

CharacterSheetValue makeInfiniteSheetValue(int baseValue)
{
    CharacterSheetValue value = {};
    value.base = baseValue;
    value.actual = baseValue;
    value.infinite = true;
    return value;
}

CharacterSheetValue makeResistanceValue(int baseValue, int actualValue, bool immune)
{
    return immune ? makeInfiniteSheetValue(baseValue) : makeSheetValue(baseValue, actualValue);
}

std::string resolveConditionText(const Character &character)
{
    if (hasCondition(character, CharacterCondition::Eradicated))
    {
        return "Eradicated";
    }

    if (hasCondition(character, CharacterCondition::Petrified))
    {
        return "Petrified";
    }

    if (hasCondition(character, CharacterCondition::Dead))
    {
        return "Dead";
    }

    if (hasCondition(character, CharacterCondition::Unconscious))
    {
        return "Unconscious";
    }

    if (hasCondition(character, CharacterCondition::Paralyzed))
    {
        return "Paralyzed";
    }

    if (hasCondition(character, CharacterCondition::Asleep))
    {
        return "Asleep";
    }

    if (hasCondition(character, CharacterCondition::Insane))
    {
        return "Insane";
    }

    if (hasCondition(character, CharacterCondition::Fear))
    {
        return "Afraid";
    }

    if (hasCondition(character, CharacterCondition::Zombie))
    {
        return "Zombie";
    }

    if (hasCondition(character, CharacterCondition::DiseaseSevere)
        || hasCondition(character, CharacterCondition::DiseaseMedium)
        || hasCondition(character, CharacterCondition::DiseaseWeak))
    {
        return "Diseased";
    }

    if (hasCondition(character, CharacterCondition::PoisonSevere)
        || hasCondition(character, CharacterCondition::PoisonMedium)
        || hasCondition(character, CharacterCondition::PoisonWeak))
    {
        return "Poisoned";
    }

    if (hasCondition(character, CharacterCondition::Weak))
    {
        return "Weak";
    }

    if (hasCondition(character, CharacterCondition::Cursed))
    {
        return "Cursed";
    }

    if (hasCondition(character, CharacterCondition::Drunk))
    {
        return "Drunk";
    }

    return "Good";
}
}

CharacterSheetSummary GameMechanics::buildCharacterSheetSummary(const Character &character, const ItemTable *pItemTable)
{
    CharacterSheetSummary summary = {};
    const EquippedItems equippedItems = resolveEquippedItems(character, pItemTable);

    const int baseMight = static_cast<int>(character.might) + character.permanentBonuses.might;
    const int baseIntellect = static_cast<int>(character.intellect) + character.permanentBonuses.intellect;
    const int basePersonality = static_cast<int>(character.personality) + character.permanentBonuses.personality;
    const int baseEndurance = static_cast<int>(character.endurance) + character.permanentBonuses.endurance;
    const int baseAccuracy = static_cast<int>(character.accuracy) + character.permanentBonuses.accuracy;
    const int baseSpeed = static_cast<int>(character.speed) + character.permanentBonuses.speed;
    const int baseLuck = static_cast<int>(character.luck) + character.permanentBonuses.luck;

    const int actualMight = baseMight + character.magicalBonuses.might;
    const int actualIntellect = baseIntellect + character.magicalBonuses.intellect;
    const int actualPersonality = basePersonality + character.magicalBonuses.personality;
    const int actualEndurance = baseEndurance + character.magicalBonuses.endurance;
    const int actualAccuracy = baseAccuracy + character.magicalBonuses.accuracy;
    const int actualSpeed = baseSpeed + character.magicalBonuses.speed;
    const int actualLuck = baseLuck + character.magicalBonuses.luck;

    summary.might = makeSheetValue(baseMight, actualMight);
    summary.intellect = makeSheetValue(baseIntellect, actualIntellect);
    summary.personality = makeSheetValue(basePersonality, actualPersonality);
    summary.endurance = makeSheetValue(baseEndurance, actualEndurance);
    summary.accuracy = makeSheetValue(baseAccuracy, actualAccuracy);
    summary.speed = makeSheetValue(baseSpeed, actualSpeed);
    summary.luck = makeSheetValue(baseLuck, actualLuck);

    summary.health.baseMaximum = character.maxHealth + character.permanentBonuses.maxHealth;
    summary.health.maximum = summary.health.baseMaximum + character.magicalBonuses.maxHealth;
    summary.health.current = std::clamp(character.health, 0, std::max(0, summary.health.maximum));

    summary.spellPoints.baseMaximum = character.maxSpellPoints + character.permanentBonuses.maxSpellPoints;
    summary.spellPoints.maximum = summary.spellPoints.baseMaximum + character.magicalBonuses.maxSpellPoints;
    summary.spellPoints.current = std::clamp(character.spellPoints, 0, std::max(0, summary.spellPoints.maximum));

    const int armorBase = parameterBonus(actualSpeed)
        + resolvePassiveArmorBonus(equippedItems)
        + resolveArmorSkillBonus(character, equippedItems)
        + character.permanentBonuses.armorClass;
    const int armorActual = std::max(0, armorBase + character.magicalBonuses.armorClass);
    summary.armorClass = makeSheetValue(std::max(0, armorBase), armorActual);

    summary.level = makeSheetValue(static_cast<int>(character.level), static_cast<int>(character.level));

    const int fireBase = character.baseResistances.fire + character.permanentBonuses.resistances.fire;
    const int airBase = character.baseResistances.air + character.permanentBonuses.resistances.air;
    const int waterBase = character.baseResistances.water + character.permanentBonuses.resistances.water;
    const int earthBase = character.baseResistances.earth + character.permanentBonuses.resistances.earth;
    const int mindBase = character.baseResistances.mind + character.permanentBonuses.resistances.mind;
    const int bodyBase = character.baseResistances.body + character.permanentBonuses.resistances.body;

    summary.fireResistance = makeResistanceValue(
        fireBase,
        fireBase + character.magicalBonuses.resistances.fire,
        character.permanentImmunities.fire || character.magicalImmunities.fire);
    summary.airResistance = makeResistanceValue(
        airBase,
        airBase + character.magicalBonuses.resistances.air,
        character.permanentImmunities.air || character.magicalImmunities.air);
    summary.waterResistance = makeResistanceValue(
        waterBase,
        waterBase + character.magicalBonuses.resistances.water,
        character.permanentImmunities.water || character.magicalImmunities.water);
    summary.earthResistance = makeResistanceValue(
        earthBase,
        earthBase + character.magicalBonuses.resistances.earth,
        character.permanentImmunities.earth || character.magicalImmunities.earth);
    summary.mindResistance = makeResistanceValue(
        mindBase,
        mindBase + character.magicalBonuses.resistances.mind,
        character.permanentImmunities.mind || character.magicalImmunities.mind);
    summary.bodyResistance = makeResistanceValue(
        bodyBase,
        bodyBase + character.magicalBonuses.resistances.body,
        character.permanentImmunities.body || character.magicalImmunities.body);

    if (character.birthYear > 0 && character.birthYear <= static_cast<uint32_t>(GameStartingYear))
    {
        summary.ageText = std::to_string(GameStartingYear - character.birthYear);
    }
    else
    {
        summary.ageText = "N/A";
    }

    summary.experienceText = std::to_string(character.experience);
    summary.conditionText = resolveConditionText(character);
    summary.quickSpellText = character.quickSpellName.empty() ? "None" : character.quickSpellName;

    const int meleeAttack = parameterBonus(actualAccuracy)
        + resolveMeleeAttackItemBonus(equippedItems)
        + resolveMeleeAttackSkillBonus(character, equippedItems)
        + character.permanentBonuses.meleeAttack
        + character.magicalBonuses.meleeAttack;
    summary.combat.attack = meleeAttack;

    const int meleeMightBonus = parameterBonus(actualMight);
    const int meleeMinDamage = std::max(
        1,
        meleeMightBonus
            + resolveMeleeMinDamageItemBonus(equippedItems)
            + resolveMeleeDamageSkillBonus(character, equippedItems)
            + character.permanentBonuses.meleeDamage
            + character.magicalBonuses.meleeDamage);
    const int meleeMaxDamage = std::max(
        1,
        meleeMightBonus
            + resolveMeleeMaxDamageItemBonus(equippedItems)
            + resolveMeleeDamageSkillBonus(character, equippedItems)
            + character.permanentBonuses.meleeDamage
            + character.magicalBonuses.meleeDamage);

    if (equippedItems.pMainHand != nullptr && isWandWeapon(*equippedItems.pMainHand))
    {
        summary.combat.meleeDamageText = "Wand";
    }
    else
    {
        summary.combat.meleeDamageText = formatDamageRange(meleeMinDamage, meleeMaxDamage);
    }

    summary.combat.shoot = resolveRangedAttack(character, equippedItems);

    if (summary.combat.shoot)
    {
        const int rangedMinDamage = std::max(
            0,
            weaponMinDamage(*equippedItems.pBow)
                + resolveRangedDamageSkillBonus(character, equippedItems)
                + character.permanentBonuses.rangedDamage
                + character.magicalBonuses.rangedDamage);
        const int rangedMaxDamage = std::max(
            0,
            weaponMaxDamage(*equippedItems.pBow)
                + resolveRangedDamageSkillBonus(character, equippedItems)
                + character.permanentBonuses.rangedDamage
                + character.magicalBonuses.rangedDamage);
        summary.combat.rangedDamageText = formatDamageRange(rangedMinDamage, rangedMaxDamage);
    }
    else if (equippedItems.pMainHand != nullptr && isWandWeapon(*equippedItems.pMainHand))
    {
        summary.combat.rangedDamageText = "Wand";
    }
    else
    {
        summary.combat.rangedDamageText = "N/A";
    }

    return summary;
}

bool GameMechanics::canAct(const Character &character)
{
    if (character.health <= 0)
    {
        return false;
    }

    return !hasCondition(character, CharacterCondition::Asleep)
        && !hasCondition(character, CharacterCondition::Paralyzed)
        && !hasCondition(character, CharacterCondition::Unconscious)
        && !hasCondition(character, CharacterCondition::Dead)
        && !hasCondition(character, CharacterCondition::Petrified)
        && !hasCondition(character, CharacterCondition::Eradicated);
}

bool GameMechanics::canSelectInGameplay(const Character &character)
{
    return canAct(character);
}

bool GameMechanics::canCharacterEquipItem(
    const Character &character,
    const ItemDefinition &itemDefinition,
    const CharacterDollTypeEntry *pCharacterDollType)
{
    if (itemDefinition.equipStat.empty() || itemDefinition.equipStat == "0")
    {
        return false;
    }

    if (isRestrictedByDollType(itemDefinition, pCharacterDollType))
    {
        return false;
    }

    if (requiresLearnedSkillToEquip(itemDefinition) && !character.hasSkill(itemDefinition.skillGroup))
    {
        return false;
    }

    // TODO: enforce artifact/relic/class/race-specific item restrictions once those data tables are wired.
    return true;
}

std::optional<CharacterEquipPlan> GameMechanics::resolveCharacterEquipPlan(
    const Character &character,
    const ItemDefinition &itemDefinition,
    const ItemTable *pItemTable,
    const CharacterDollTypeEntry *pCharacterDollType,
    std::optional<EquipmentSlot> explicitSlot,
    bool preferOffHand)
{
    if (!canCharacterEquipItem(character, itemDefinition, pCharacterDollType))
    {
        return std::nullopt;
    }

    CharacterEquipPlan plan = {};
    const ItemDefinition *pMainHand = getEquippedItem(character, EquipmentSlot::MainHand, pItemTable);
    const bool hasMainItem = character.equipment.mainHand != 0;
    const bool hasOffHandItem = character.equipment.offHand != 0;
    const bool hasTwoHandedMain =
        pMainHand != nullptr ? isTwoHandedWeapon(*pMainHand) : false;

    if (explicitSlot)
    {
        const EquipmentSlot slot = *explicitSlot;

        if (itemDefinition.equipStat == "Ring")
        {
            if (!isRingSlot(slot))
            {
                return std::nullopt;
            }

            plan.targetSlot = slot;

            if (equippedItemId(character.equipment, slot) != 0)
            {
                plan.displacedSlot = slot;
            }

            return plan;
        }

        if (itemDefinition.equipStat == "Gauntlets")
        {
            if (slot != EquipmentSlot::Gauntlets)
            {
                return std::nullopt;
            }

            plan.targetSlot = EquipmentSlot::Gauntlets;
            plan.displacedSlot = equippedItemId(character.equipment, EquipmentSlot::Gauntlets) != 0
                ? std::optional<EquipmentSlot>(EquipmentSlot::Gauntlets)
                : std::nullopt;
            return plan;
        }

        if (itemDefinition.equipStat == "Amulet")
        {
            if (slot != EquipmentSlot::Amulet)
            {
                return std::nullopt;
            }

            plan.targetSlot = EquipmentSlot::Amulet;
            plan.displacedSlot = equippedItemId(character.equipment, EquipmentSlot::Amulet) != 0
                ? std::optional<EquipmentSlot>(EquipmentSlot::Amulet)
                : std::nullopt;
            return plan;
        }

        if (slot == EquipmentSlot::Armor && itemDefinition.equipStat == "Armor")
        {
            plan.targetSlot = EquipmentSlot::Armor;
        }
        else if (slot == EquipmentSlot::Helm && itemDefinition.equipStat == "Helm")
        {
            plan.targetSlot = EquipmentSlot::Helm;
        }
        else if (slot == EquipmentSlot::Belt && itemDefinition.equipStat == "Belt")
        {
            plan.targetSlot = EquipmentSlot::Belt;
        }
        else if (slot == EquipmentSlot::Cloak && itemDefinition.equipStat == "Cloak")
        {
            plan.targetSlot = EquipmentSlot::Cloak;
        }
        else if (slot == EquipmentSlot::Boots && itemDefinition.equipStat == "Boots")
        {
            plan.targetSlot = EquipmentSlot::Boots;
        }
        else if (slot == EquipmentSlot::Bow && itemDefinition.equipStat == "Missile")
        {
            plan.targetSlot = EquipmentSlot::Bow;
        }
        else
        {
            return std::nullopt;
        }

        if (equippedItemId(character.equipment, plan.targetSlot) != 0)
        {
            plan.displacedSlot = plan.targetSlot;
        }

        return plan;
    }

    if (itemDefinition.equipStat == "Ring")
    {
        const std::optional<EquipmentSlot> freeRing = firstFreeRingSlot(character);
        plan.targetSlot = freeRing.value_or(EquipmentSlot::Ring1);

        if (!freeRing)
        {
            plan.displacedSlot = EquipmentSlot::Ring1;
        }

        return plan;
    }

    if (itemDefinition.equipStat == "Gauntlets")
    {
        plan.targetSlot = EquipmentSlot::Gauntlets;
        plan.displacedSlot = equippedItemId(character.equipment, EquipmentSlot::Gauntlets) != 0
            ? std::optional<EquipmentSlot>(EquipmentSlot::Gauntlets)
            : std::nullopt;
        return plan;
    }

    if (itemDefinition.equipStat == "Amulet")
    {
        plan.targetSlot = EquipmentSlot::Amulet;
        plan.displacedSlot = equippedItemId(character.equipment, EquipmentSlot::Amulet) != 0
            ? std::optional<EquipmentSlot>(EquipmentSlot::Amulet)
            : std::nullopt;
        return plan;
    }

    if (itemDefinition.equipStat == "Armor")
    {
        plan.targetSlot = EquipmentSlot::Armor;
    }
    else if (itemDefinition.equipStat == "Helm")
    {
        plan.targetSlot = EquipmentSlot::Helm;
    }
    else if (itemDefinition.equipStat == "Belt")
    {
        plan.targetSlot = EquipmentSlot::Belt;
    }
    else if (itemDefinition.equipStat == "Cloak")
    {
        plan.targetSlot = EquipmentSlot::Cloak;
    }
    else if (itemDefinition.equipStat == "Boots")
    {
        plan.targetSlot = EquipmentSlot::Boots;
    }
    else if (itemDefinition.equipStat == "Missile")
    {
        plan.targetSlot = EquipmentSlot::Bow;
    }
    
    if (itemDefinition.equipStat == "Armor"
        || itemDefinition.equipStat == "Helm"
        || itemDefinition.equipStat == "Belt"
        || itemDefinition.equipStat == "Cloak"
        || itemDefinition.equipStat == "Boots"
        || itemDefinition.equipStat == "Missile")
    {
        if (equippedItemId(character.equipment, plan.targetSlot) != 0)
        {
            plan.displacedSlot = plan.targetSlot;
        }

        return plan;
    }

    else if (itemDefinition.equipStat == "Shield")
    {
        if (pMainHand != nullptr
            && isSpearItem(*pMainHand)
            && skillMastery(character, "Spear") < SkillMastery::Master)
        {
            return std::nullopt;
        }

        plan.targetSlot = EquipmentSlot::OffHand;

        if (hasOffHandItem)
        {
            plan.displacedSlot = EquipmentSlot::OffHand;
        }
        else if (hasTwoHandedMain)
        {
            plan.displacedSlot = EquipmentSlot::MainHand;
        }

        return plan;
    }
    else if (itemDefinition.equipStat == "Weapon2")
    {
        plan.targetSlot = EquipmentSlot::MainHand;

        if (hasMainItem && hasOffHandItem)
        {
            return std::nullopt;
        }

        if (hasMainItem)
        {
            plan.displacedSlot = EquipmentSlot::MainHand;
        }
        else if (hasOffHandItem)
        {
            plan.displacedSlot = EquipmentSlot::OffHand;
        }

        return plan;
    }
    else if (itemDefinition.equipStat == "Weapon1or2")
    {
        if (hasOffHandItem && skillMastery(character, "Spear") < SkillMastery::Master)
        {
            return std::nullopt;
        }

        plan.targetSlot = EquipmentSlot::MainHand;

        if (hasMainItem)
        {
            plan.displacedSlot = EquipmentSlot::MainHand;
        }

        return plan;
    }
    else if (itemDefinition.equipStat == "Weapon" || itemDefinition.equipStat == "WeaponW")
    {
        const std::string skillName = canonicalSkillName(itemDefinition.skillGroup);
        const bool canUseOffHand =
            !hasTwoHandedMain
            && ((skillName == "Dagger" && skillMastery(character, "Dagger") >= SkillMastery::Expert)
                || (skillName == "Sword" && skillMastery(character, "Sword") >= SkillMastery::Master));

        if (preferOffHand && canUseOffHand)
        {
            if (pMainHand != nullptr
                && isSpearItem(*pMainHand)
                && skillMastery(character, "Spear") < SkillMastery::Master)
            {
                return std::nullopt;
            }

            plan.targetSlot = EquipmentSlot::OffHand;

            if (hasOffHandItem)
            {
                plan.displacedSlot = EquipmentSlot::OffHand;
            }

            return plan;
        }

        plan.targetSlot = EquipmentSlot::MainHand;

        if (hasMainItem)
        {
            plan.displacedSlot = EquipmentSlot::MainHand;
        }

        return plan;
    }

    return std::nullopt;
}
}
