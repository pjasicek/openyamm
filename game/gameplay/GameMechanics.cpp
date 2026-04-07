#include "game/gameplay/GameMechanics.h"

#include "game/items/ItemEnchantRuntime.h"
#include "game/tables/CharacterDollTable.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr int GameStartingYear = 1168;
constexpr float OeCharacterMeleeAttackDistance = 407.2f;
constexpr float OeCharacterRangedAttackDistance = 5120.0f;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr int OeMinimumMeleeRecoveryTicks = 30;
constexpr int OeMinimumRangedRecoveryTicks = 5;
constexpr int OeMinimumBlasterRecoveryTicks = 5;

constexpr int ParameterBonusThresholds[29] = {
    500, 400, 350, 300, 275, 250, 225, 200, 175, 150, 125, 100, 75, 50, 40,
    35, 30, 25, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3, 0,
};

constexpr int ParameterBonusValues[29] = {
    30, 25, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8,
    7, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5, -6,
};

uint64_t experienceRequiredForNextLevel(uint32_t currentLevel)
{
    return 1000ull * currentLevel * (currentLevel + 1) / 2;
}

bool canTrainToNextLevel(const Character &character)
{
    return static_cast<uint64_t>(character.experience) >= experienceRequiredForNextLevel(character.level);
}

std::string experienceInspectSubject(const Character &character)
{
    return character.name.empty() ? "This character" : character.name;
}

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

bool tryParseSpellIdToken(const std::string &text, int &spellId)
{
    if (text.size() < 2 || (text[0] != 'S' && text[0] != 's'))
    {
        return false;
    }

    for (size_t index = 1; index < text.size(); ++index)
    {
        if (!std::isdigit(static_cast<unsigned char>(text[index])))
        {
            return false;
        }
    }

    try
    {
        spellId = std::stoi(text.substr(1));
    }
    catch (...)
    {
        return false;
    }

    return spellId > 0;
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
    const auto bonusIt = character.itemSkillBonuses.find(std::string(skillName));
    const int bonusLevel = bonusIt != character.itemSkillBonuses.end() ? bonusIt->second : 0;
    return (pSkill != nullptr ? static_cast<int>(pSkill->level) : 0) + bonusLevel;
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

float ticksToRecoverySeconds(int ticks)
{
    return std::max(0.0f, static_cast<float>(ticks) / 128.0f * OeRealtimeRecoveryScale);
}

int baseRecoveryTicksForSkillName(const std::string &skillName)
{
    if (skillName == "Unarmed")
    {
        return 60;
    }

    if (skillName == "Sword")
    {
        return 90;
    }

    if (skillName == "Dagger")
    {
        return 60;
    }

    if (skillName == "Axe")
    {
        return 100;
    }

    if (skillName == "Spear" || skillName == "Mace")
    {
        return 80;
    }

    if (skillName == "Bow" || skillName == "Staff")
    {
        return 100;
    }

    if (skillName == "Blaster")
    {
        return 30;
    }

    if (skillName == "Shield" || skillName == "LeatherArmor")
    {
        return 10;
    }

    if (skillName == "ChainArmor")
    {
        return 20;
    }

    if (skillName == "PlateArmor")
    {
        return 30;
    }

    return 100;
}

float armorRecoveryMultiplier(const Character &character, const std::string &skillName)
{
    const SkillMastery mastery = skillMastery(character, skillName);

    if (skillName == "LeatherArmor")
    {
        return 1.0f;
    }

    if (skillName == "ChainArmor")
    {
        switch (mastery)
        {
            case SkillMastery::Grandmaster:
            case SkillMastery::Master:
                return 0.0f;

            case SkillMastery::Expert:
                return 0.5f;

            case SkillMastery::Normal:
            case SkillMastery::None:
            default:
                return 1.0f;
        }
    }

    if (skillName == "PlateArmor")
    {
        switch (mastery)
        {
            case SkillMastery::Grandmaster:
                return 0.0f;

            case SkillMastery::Master:
            case SkillMastery::Expert:
                return 0.5f;

            case SkillMastery::Normal:
            case SkillMastery::None:
            default:
                return 1.0f;
        }
    }

    if (skillName == "Shield")
    {
        switch (mastery)
        {
            case SkillMastery::Grandmaster:
            case SkillMastery::Master:
            case SkillMastery::Expert:
                return 0.0f;

            case SkillMastery::Normal:
            case SkillMastery::None:
            default:
                return 1.0f;
        }
    }

    return 1.0f;
}

const ItemDefinition *getEquippedItem(const Character &character, EquipmentSlot slot, const ItemTable *pItemTable)
{
    if (pItemTable == nullptr)
    {
        return nullptr;
    }

    const EquippedItemRuntimeState *pRuntimeState = nullptr;

    switch (slot)
    {
        case EquipmentSlot::OffHand:
            pRuntimeState = &character.equipmentRuntime.offHand;
            break;

        case EquipmentSlot::MainHand:
            pRuntimeState = &character.equipmentRuntime.mainHand;
            break;

        case EquipmentSlot::Bow:
            pRuntimeState = &character.equipmentRuntime.bow;
            break;

        case EquipmentSlot::Armor:
            pRuntimeState = &character.equipmentRuntime.armor;
            break;

        case EquipmentSlot::Helm:
            pRuntimeState = &character.equipmentRuntime.helm;
            break;

        case EquipmentSlot::Belt:
            pRuntimeState = &character.equipmentRuntime.belt;
            break;

        case EquipmentSlot::Cloak:
            pRuntimeState = &character.equipmentRuntime.cloak;
            break;

        case EquipmentSlot::Gauntlets:
            pRuntimeState = &character.equipmentRuntime.gauntlets;
            break;

        case EquipmentSlot::Boots:
            pRuntimeState = &character.equipmentRuntime.boots;
            break;

        case EquipmentSlot::Amulet:
            pRuntimeState = &character.equipmentRuntime.amulet;
            break;

        case EquipmentSlot::Ring1:
            pRuntimeState = &character.equipmentRuntime.ring1;
            break;

        case EquipmentSlot::Ring2:
            pRuntimeState = &character.equipmentRuntime.ring2;
            break;

        case EquipmentSlot::Ring3:
            pRuntimeState = &character.equipmentRuntime.ring3;
            break;

        case EquipmentSlot::Ring4:
            pRuntimeState = &character.equipmentRuntime.ring4;
            break;

        case EquipmentSlot::Ring5:
            pRuntimeState = &character.equipmentRuntime.ring5;
            break;

        case EquipmentSlot::Ring6:
            pRuntimeState = &character.equipmentRuntime.ring6;
            break;
    }

    if (pRuntimeState != nullptr && pRuntimeState->broken)
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

CharacterStatBonuses resolveEquippedItemStatBonuses(
    const Character &character,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    CharacterStatBonuses bonuses = {};

    if (pItemTable == nullptr)
    {
        return bonuses;
    }

    Character bonusCharacter = {};

    const auto applyEquippedItemEnchant =
        [&](uint32_t itemId, const EquippedItemRuntimeState &runtimeState)
        {
            if (itemId == 0 || runtimeState.broken)
            {
                return;
            }

            const ItemDefinition *pItemDefinition = pItemTable->get(itemId);

            if (pItemDefinition == nullptr)
            {
                return;
            }

            ItemEnchantRuntime::applyEquippedEnchantEffects(
                *pItemDefinition,
                runtimeState,
                pStandardItemEnchantTable,
                pSpecialItemEnchantTable,
                bonusCharacter);
        };

    applyEquippedItemEnchant(character.equipment.offHand, character.equipmentRuntime.offHand);
    applyEquippedItemEnchant(character.equipment.mainHand, character.equipmentRuntime.mainHand);
    applyEquippedItemEnchant(character.equipment.bow, character.equipmentRuntime.bow);
    applyEquippedItemEnchant(character.equipment.armor, character.equipmentRuntime.armor);
    applyEquippedItemEnchant(character.equipment.helm, character.equipmentRuntime.helm);
    applyEquippedItemEnchant(character.equipment.belt, character.equipmentRuntime.belt);
    applyEquippedItemEnchant(character.equipment.cloak, character.equipmentRuntime.cloak);
    applyEquippedItemEnchant(character.equipment.gauntlets, character.equipmentRuntime.gauntlets);
    applyEquippedItemEnchant(character.equipment.boots, character.equipmentRuntime.boots);
    applyEquippedItemEnchant(character.equipment.amulet, character.equipmentRuntime.amulet);
    applyEquippedItemEnchant(character.equipment.ring1, character.equipmentRuntime.ring1);
    applyEquippedItemEnchant(character.equipment.ring2, character.equipmentRuntime.ring2);
    applyEquippedItemEnchant(character.equipment.ring3, character.equipmentRuntime.ring3);
    applyEquippedItemEnchant(character.equipment.ring4, character.equipmentRuntime.ring4);
    applyEquippedItemEnchant(character.equipment.ring5, character.equipmentRuntime.ring5);
    applyEquippedItemEnchant(character.equipment.ring6, character.equipmentRuntime.ring6);

    return bonusCharacter.magicalBonuses;
}

int resolveCharacterPrimaryStatBaseValue(const Character &character, uint32_t rawStatId)
{
    switch (rawStatId)
    {
        case 0x20:
        case 0x27:
            return static_cast<int>(character.might);

        case 0x21:
        case 0x28:
            return static_cast<int>(character.intellect);

        case 0x22:
        case 0x29:
            return static_cast<int>(character.personality);

        case 0x23:
        case 0x2A:
            return static_cast<int>(character.endurance);

        case 0x24:
        case 0x2B:
            return static_cast<int>(character.speed);

        case 0x25:
        case 0x2C:
            return static_cast<int>(character.accuracy);

        case 0x26:
        case 0x2D:
            return static_cast<int>(character.luck);

        default:
            break;
    }

    return 0;
}

int resolveCharacterPrimaryStatPermanentBonusValue(const Character &character, uint32_t rawStatId)
{
    switch (rawStatId)
    {
        case 0x20:
        case 0x27:
            return character.permanentBonuses.might;

        case 0x21:
        case 0x28:
            return character.permanentBonuses.intellect;

        case 0x22:
        case 0x29:
            return character.permanentBonuses.personality;

        case 0x23:
        case 0x2A:
            return character.permanentBonuses.endurance;

        case 0x24:
        case 0x2B:
            return character.permanentBonuses.speed;

        case 0x25:
        case 0x2C:
            return character.permanentBonuses.accuracy;

        case 0x26:
        case 0x2D:
            return character.permanentBonuses.luck;

        default:
            break;
    }

    return 0;
}

int resolveCharacterPrimaryStatMagicalBonusValue(const Character &character, uint32_t rawStatId)
{
    switch (rawStatId)
    {
        case 0x20:
        case 0x27:
            return character.magicalBonuses.might;

        case 0x21:
        case 0x28:
            return character.magicalBonuses.intellect;

        case 0x22:
        case 0x29:
            return character.magicalBonuses.personality;

        case 0x23:
        case 0x2A:
            return character.magicalBonuses.endurance;

        case 0x24:
        case 0x2B:
            return character.magicalBonuses.speed;

        case 0x25:
        case 0x2C:
            return character.magicalBonuses.accuracy;

        case 0x26:
        case 0x2D:
            return character.magicalBonuses.luck;

        default:
            break;
    }

    return 0;
}

int resolveCharacterPrimaryStatEquippedItemBonusValue(const CharacterStatBonuses &bonuses, uint32_t rawStatId)
{
    switch (rawStatId)
    {
        case 0x20:
        case 0x27:
            return bonuses.might;

        case 0x21:
        case 0x28:
            return bonuses.intellect;

        case 0x22:
        case 0x29:
            return bonuses.personality;

        case 0x23:
        case 0x2A:
            return bonuses.endurance;

        case 0x24:
        case 0x2B:
            return bonuses.speed;

        case 0x25:
        case 0x2C:
            return bonuses.accuracy;

        case 0x26:
        case 0x2D:
            return bonuses.luck;

        default:
            break;
    }

    return 0;
}

int resolveCharacterSheetBasePrimaryStatValue(
    const Character &character,
    uint32_t rawStatId,
    const CharacterStatBonuses &equippedItemBonuses)
{
    return resolveCharacterPrimaryStatBaseValue(character, rawStatId)
        + resolveCharacterPrimaryStatPermanentBonusValue(character, rawStatId)
        + resolveCharacterPrimaryStatEquippedItemBonusValue(equippedItemBonuses, rawStatId);
}

int resolveCharacterSheetActualPrimaryStatValue(
    const Character &character,
    uint32_t rawStatId,
    const CharacterStatBonuses &equippedItemBonuses)
{
    return resolveCharacterSheetBasePrimaryStatValue(character, rawStatId, equippedItemBonuses)
        + resolveCharacterPrimaryStatMagicalBonusValue(character, rawStatId)
        - resolveCharacterPrimaryStatEquippedItemBonusValue(equippedItemBonuses, rawStatId);
}

std::string resolveConditionText(const Character &character)
{
    const std::optional<CharacterCondition> condition = GameMechanics::displayedCondition(character);

    if (!condition)
    {
        return "Good";
    }

    if (*condition == CharacterCondition::Eradicated)
    {
        return "Eradicated";
    }

    if (*condition == CharacterCondition::Petrified)
    {
        return "Petrified";
    }

    if (*condition == CharacterCondition::Dead)
    {
        return "Dead";
    }

    if (*condition == CharacterCondition::Unconscious)
    {
        return "Unconscious";
    }

    if (*condition == CharacterCondition::Paralyzed)
    {
        return "Paralyzed";
    }

    if (*condition == CharacterCondition::Asleep)
    {
        return "Asleep";
    }

    if (*condition == CharacterCondition::Insane)
    {
        return "Insane";
    }

    if (*condition == CharacterCondition::Fear)
    {
        return "Afraid";
    }

    if (*condition == CharacterCondition::DiseaseSevere
        || *condition == CharacterCondition::DiseaseMedium
        || *condition == CharacterCondition::DiseaseWeak)
    {
        return "Diseased";
    }

    if (*condition == CharacterCondition::PoisonSevere
        || *condition == CharacterCondition::PoisonMedium
        || *condition == CharacterCondition::PoisonWeak)
    {
        return "Poisoned";
    }

    if (*condition == CharacterCondition::Weak)
    {
        return "Weak";
    }

    if (*condition == CharacterCondition::Cursed)
    {
        return "Cursed";
    }

    if (*condition == CharacterCondition::Drunk)
    {
        return "Drunk";
    }

    return "Good";
}

float resolveAttackRecoverySeconds(
    const Character &character,
    const EquippedItems &equippedItems,
    const SpellTable *pSpellTable,
    CharacterAttackMode mode)
{
    bool usesBow = mode == CharacterAttackMode::Bow;
    bool usesBlaster = mode == CharacterAttackMode::Blaster;
    const ItemDefinition *pWeapon = nullptr;
    int weaponRecoveryTicks = baseRecoveryTicksForSkillName("Staff");

    if (usesBow)
    {
        pWeapon = equippedItems.pBow;

        if (pWeapon != nullptr)
        {
            weaponRecoveryTicks = baseRecoveryTicksForSkillName(canonicalSkillName(pWeapon->skillGroup));
        }
    }
    else if (isUnarmed(equippedItems) && skillLevel(character, "Unarmed") > 0)
    {
        weaponRecoveryTicks = baseRecoveryTicksForSkillName("Unarmed");
    }
    else if (equippedItems.pMainHand != nullptr)
    {
        pWeapon = equippedItems.pMainHand;

        if (mode == CharacterAttackMode::Wand)
        {
            int spellId = 0;

            if (pSpellTable != nullptr
                && tryParseSpellIdToken(equippedItems.pMainHand->mod1, spellId))
            {
                const SpellEntry *pSpellEntry = pSpellTable->findById(spellId);

                if (pSpellEntry != nullptr)
                {
                    weaponRecoveryTicks = std::max(pSpellEntry->expertRecoveryTicks, 1);
                }
            }
        }
        else
        {
            weaponRecoveryTicks = baseRecoveryTicksForSkillName(canonicalSkillName(equippedItems.pMainHand->skillGroup));
        }
    }

    int shieldRecoveryTicks = 0;

    if (equippedItems.pOffHand != nullptr)
    {
        const std::string offHandSkillName = canonicalSkillName(equippedItems.pOffHand->skillGroup);

        if (isShieldItem(*equippedItems.pOffHand))
        {
            shieldRecoveryTicks = static_cast<int>(std::lround(
                static_cast<float>(baseRecoveryTicksForSkillName(offHandSkillName))
                * armorRecoveryMultiplier(character, "Shield")));
        }
        else if (baseRecoveryTicksForSkillName(offHandSkillName) > weaponRecoveryTicks)
        {
            pWeapon = equippedItems.pOffHand;
            weaponRecoveryTicks = baseRecoveryTicksForSkillName(offHandSkillName);
        }
    }

    int armorRecoveryTicks = 0;

    if (equippedItems.pArmor != nullptr)
    {
        const std::string armorSkillName = canonicalSkillName(equippedItems.pArmor->skillGroup);
        armorRecoveryTicks = static_cast<int>(std::lround(
            static_cast<float>(baseRecoveryTicksForSkillName(armorSkillName))
            * armorRecoveryMultiplier(character, armorSkillName)));
    }

    const int actualSpeed = static_cast<int>(character.speed)
        + character.permanentBonuses.speed
        + character.magicalBonuses.speed;
    const int playerSpeedRecoveryReduction = parameterBonus(actualSpeed);
    int weaponSkillRecoveryReduction = 0;

    if (pWeapon != nullptr)
    {
        const std::string weaponSkillName = canonicalSkillName(pWeapon->skillGroup);
        const SkillMastery weaponMastery = skillMastery(character, weaponSkillName);

        if ((weaponSkillName == "Sword" || weaponSkillName == "Axe" || weaponSkillName == "Bow")
            && weaponMastery >= SkillMastery::Expert)
        {
            weaponSkillRecoveryReduction = skillLevel(character, weaponSkillName);
        }
    }

    int armsmasterRecoveryReduction = 0;

    if (!usesBow && !usesBlaster)
    {
        armsmasterRecoveryReduction = skillLevel(character, "Armsmaster");

        if (skillMastery(character, "Armsmaster") == SkillMastery::Grandmaster)
        {
            armsmasterRecoveryReduction *= 2;
        }
    }

    int recoveryTicks = weaponRecoveryTicks + shieldRecoveryTicks + armorRecoveryTicks
        - playerSpeedRecoveryReduction - weaponSkillRecoveryReduction - armsmasterRecoveryReduction
        - character.attackRecoveryReductionTicks;
    int minimumRecoveryTicks = OeMinimumMeleeRecoveryTicks;

    if (mode == CharacterAttackMode::Blaster)
    {
        minimumRecoveryTicks = OeMinimumBlasterRecoveryTicks;
    }
    else if (mode == CharacterAttackMode::Bow || mode == CharacterAttackMode::Wand)
    {
        minimumRecoveryTicks = OeMinimumRangedRecoveryTicks;
    }

    return ticksToRecoverySeconds(std::max(recoveryTicks, minimumRecoveryTicks));
}

int randomInclusive(std::mt19937 &rng, int minimumValue, int maximumValue)
{
    if (maximumValue < minimumValue)
    {
        std::swap(minimumValue, maximumValue);
    }

    return std::uniform_int_distribution<int>(minimumValue, maximumValue)(rng);
}

bool characterAttackHitsArmorClass(
    int targetArmorClass,
    int attackBonus,
    int distanceMode,
    int skillModifier,
    std::mt19937 &rng)
{
    const int rollUpperBound = std::max(1, targetArmorClass + 2 * attackBonus + 30);
    const int positiveModifier =
        skillModifier + std::uniform_int_distribution<int>(0, rollUpperBound - 1)(rng);
    int negativeModifier = targetArmorClass + 15;

    if (distanceMode == 2)
    {
        negativeModifier = ((targetArmorClass + 15) / 2) + targetArmorClass + 15;
    }
    else if (distanceMode >= 3)
    {
        negativeModifier = 2 * targetArmorClass + 30;
    }

    return positiveModifier > negativeModifier;
}
}

uint64_t GameMechanics::experienceRequiredForNextLevel(uint32_t currentLevel)
{
    return OpenYAMM::Game::experienceRequiredForNextLevel(currentLevel);
}

uint32_t GameMechanics::maximumTrainableLevelFromExperience(const Character &character)
{
    uint32_t trainableLevel = character.level;

    while (static_cast<uint64_t>(character.experience) >= experienceRequiredForNextLevel(trainableLevel))
    {
        ++trainableLevel;
    }

    return trainableLevel;
}

std::string GameMechanics::buildExperienceInspectSupplement(const Character &character)
{
    const std::string subject = experienceInspectSubject(character);
    const uint64_t nextLevelExperience = experienceRequiredForNextLevel(character.level);

    if (static_cast<uint64_t>(character.experience) < nextLevelExperience)
    {
        return subject
            + " needs "
            + std::to_string(nextLevelExperience - static_cast<uint64_t>(character.experience))
            + " more experience to train to level "
            + std::to_string(character.level + 1)
            + ".";
    }

    return subject
        + " is eligible to train up to level "
        + std::to_string(maximumTrainableLevelFromExperience(character))
        + ".";
}

int GameMechanics::resolveCharacterDisplayedBasePrimaryStat(
    const Character &character,
    uint32_t rawStatId,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    const CharacterStatBonuses equippedItemBonuses = resolveEquippedItemStatBonuses(
        character,
        pItemTable,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable);

    return resolveCharacterPrimaryStatBaseValue(character, rawStatId)
        + resolveCharacterPrimaryStatPermanentBonusValue(character, rawStatId)
        + resolveCharacterPrimaryStatEquippedItemBonusValue(equippedItemBonuses, rawStatId);
}

int GameMechanics::resolveCharacterDisplayedActualPrimaryStat(
    const Character &character,
    uint32_t rawStatId,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    return resolveCharacterDisplayedBasePrimaryStat(
            character,
            rawStatId,
            pItemTable,
            pStandardItemEnchantTable,
            pSpecialItemEnchantTable)
        + resolveCharacterPrimaryStatMagicalBonusValue(character, rawStatId);
}

CharacterSheetSummary GameMechanics::buildCharacterSheetSummary(
    const Character &character,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    CharacterSheetSummary summary = {};
    const EquippedItems equippedItems = resolveEquippedItems(character, pItemTable);
    const CharacterStatBonuses equippedItemBonuses = resolveEquippedItemStatBonuses(
        character,
        pItemTable,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable);

    const int baseMight = resolveCharacterSheetBasePrimaryStatValue(character, 0x20, equippedItemBonuses);
    const int baseIntellect = resolveCharacterSheetBasePrimaryStatValue(character, 0x21, equippedItemBonuses);
    const int basePersonality = resolveCharacterSheetBasePrimaryStatValue(character, 0x22, equippedItemBonuses);
    const int baseEndurance = resolveCharacterSheetBasePrimaryStatValue(character, 0x23, equippedItemBonuses);
    const int baseAccuracy = resolveCharacterSheetBasePrimaryStatValue(character, 0x25, equippedItemBonuses);
    const int baseSpeed = resolveCharacterSheetBasePrimaryStatValue(character, 0x24, equippedItemBonuses);
    const int baseLuck = resolveCharacterSheetBasePrimaryStatValue(character, 0x26, equippedItemBonuses);

    const int actualMight = resolveCharacterSheetActualPrimaryStatValue(character, 0x27, equippedItemBonuses);
    const int actualIntellect = resolveCharacterSheetActualPrimaryStatValue(character, 0x28, equippedItemBonuses);
    const int actualPersonality = resolveCharacterSheetActualPrimaryStatValue(character, 0x29, equippedItemBonuses);
    const int actualEndurance = resolveCharacterSheetActualPrimaryStatValue(character, 0x2A, equippedItemBonuses);
    const int actualAccuracy = resolveCharacterSheetActualPrimaryStatValue(character, 0x2C, equippedItemBonuses);
    const int actualSpeed = resolveCharacterSheetActualPrimaryStatValue(character, 0x2B, equippedItemBonuses);
    const int actualLuck = resolveCharacterSheetActualPrimaryStatValue(character, 0x2D, equippedItemBonuses);

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

    summary.level = makeSheetValue(
        static_cast<int>(character.level),
        static_cast<int>(maximumTrainableLevelFromExperience(character)));

    const int fireBase = character.baseResistances.fire
        + character.permanentBonuses.resistances.fire
        + equippedItemBonuses.resistances.fire;
    const int airBase = character.baseResistances.air
        + character.permanentBonuses.resistances.air
        + equippedItemBonuses.resistances.air;
    const int waterBase = character.baseResistances.water
        + character.permanentBonuses.resistances.water
        + equippedItemBonuses.resistances.water;
    const int earthBase = character.baseResistances.earth
        + character.permanentBonuses.resistances.earth
        + equippedItemBonuses.resistances.earth;
    const int mindBase = character.baseResistances.mind
        + character.permanentBonuses.resistances.mind
        + equippedItemBonuses.resistances.mind;
    const int bodyBase = character.baseResistances.body
        + character.permanentBonuses.resistances.body
        + equippedItemBonuses.resistances.body;

    const int fireActual = fireBase
        + character.magicalBonuses.resistances.fire
        - equippedItemBonuses.resistances.fire;
    const int airActual = airBase
        + character.magicalBonuses.resistances.air
        - equippedItemBonuses.resistances.air;
    const int waterActual = waterBase
        + character.magicalBonuses.resistances.water
        - equippedItemBonuses.resistances.water;
    const int earthActual = earthBase
        + character.magicalBonuses.resistances.earth
        - equippedItemBonuses.resistances.earth;
    const int mindActual = mindBase
        + character.magicalBonuses.resistances.mind
        - equippedItemBonuses.resistances.mind;
    const int bodyActual = bodyBase
        + character.magicalBonuses.resistances.body
        - equippedItemBonuses.resistances.body;

    summary.fireResistance = makeResistanceValue(
        fireBase,
        fireActual,
        character.permanentImmunities.fire || character.magicalImmunities.fire);
    summary.airResistance = makeResistanceValue(
        airBase,
        airActual,
        character.permanentImmunities.air || character.magicalImmunities.air);
    summary.waterResistance = makeResistanceValue(
        waterBase,
        waterActual,
        character.permanentImmunities.water || character.magicalImmunities.water);
    summary.earthResistance = makeResistanceValue(
        earthBase,
        earthActual,
        character.permanentImmunities.earth || character.magicalImmunities.earth);
    summary.mindResistance = makeResistanceValue(
        mindBase,
        mindActual,
        character.permanentImmunities.mind || character.magicalImmunities.mind);
    summary.bodyResistance = makeResistanceValue(
        bodyBase,
        bodyActual,
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
    summary.canTrainToNextLevel = canTrainToNextLevel(character);
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
            + character.weaponEnchantmentDamageBonus
            + character.permanentBonuses.meleeDamage
            + character.magicalBonuses.meleeDamage);
    const int meleeMaxDamage = std::max(
        1,
        meleeMightBonus
            + resolveMeleeMaxDamageItemBonus(equippedItems)
            + resolveMeleeDamageSkillBonus(character, equippedItems)
            + character.weaponEnchantmentDamageBonus
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
                + character.weaponEnchantmentDamageBonus
                + character.permanentBonuses.rangedDamage
                + character.magicalBonuses.rangedDamage);
        const int rangedMaxDamage = std::max(
            0,
            weaponMaxDamage(*equippedItems.pBow)
                + resolveRangedDamageSkillBonus(character, equippedItems)
                + character.weaponEnchantmentDamageBonus
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

CharacterAttackProfile GameMechanics::buildCharacterAttackProfile(
    const Character &character,
    const ItemTable *pItemTable,
    const SpellTable *pSpellTable)
{
    CharacterAttackProfile profile = {};
    const EquippedItems equippedItems = resolveEquippedItems(character, pItemTable);
    const CharacterSheetSummary summary = buildCharacterSheetSummary(character, pItemTable);

    profile.canMelee = !character.physicalAttackDisabled;
    profile.hasBow =
        !character.physicalAttackDisabled && equippedItems.pBow != nullptr && isRangedWeapon(*equippedItems.pBow);
    profile.hasWand = equippedItems.pMainHand != nullptr && isWandWeapon(*equippedItems.pMainHand);
    profile.hasBlaster =
        !character.physicalAttackDisabled
        && ((equippedItems.pBow != nullptr && canonicalSkillName(equippedItems.pBow->skillGroup) == "Blaster")
            || (equippedItems.pMainHand != nullptr && canonicalSkillName(equippedItems.pMainHand->skillGroup) == "Blaster"));
    profile.canShoot = profile.hasBow || profile.hasWand || profile.hasBlaster;
    profile.meleeAttackBonus = summary.combat.attack;
    profile.meleeRecoverySeconds = resolveAttackRecoverySeconds(
        character,
        equippedItems,
        pSpellTable,
        CharacterAttackMode::Melee);
    profile.rangedRecoverySeconds = resolveAttackRecoverySeconds(
        character,
        equippedItems,
        pSpellTable,
        profile.hasBlaster
            ? CharacterAttackMode::Blaster
            : (profile.hasWand ? CharacterAttackMode::Wand : CharacterAttackMode::Bow));

    const int actualMight = static_cast<int>(character.might)
        + character.permanentBonuses.might
        + character.magicalBonuses.might;
    const int meleeMightBonus = parameterBonus(actualMight);
    profile.meleeMinDamage = std::max(
        1,
        meleeMightBonus
            + resolveMeleeMinDamageItemBonus(equippedItems)
            + resolveMeleeDamageSkillBonus(character, equippedItems)
            + character.weaponEnchantmentDamageBonus
            + character.permanentBonuses.meleeDamage
            + character.magicalBonuses.meleeDamage);
    profile.meleeMaxDamage = std::max(
        1,
        meleeMightBonus
            + resolveMeleeMaxDamageItemBonus(equippedItems)
            + resolveMeleeDamageSkillBonus(character, equippedItems)
            + character.weaponEnchantmentDamageBonus
            + character.permanentBonuses.meleeDamage
            + character.magicalBonuses.meleeDamage);

    if (summary.combat.shoot.has_value())
    {
        profile.rangedAttackBonus = summary.combat.shoot;
        const std::string rangedSkillName = canonicalSkillName(
            equippedItems.pBow != nullptr ? equippedItems.pBow->skillGroup : std::string());
        profile.rangedSkillLevel = static_cast<uint32_t>(std::max(0, skillLevel(character, rangedSkillName)));
        profile.rangedSkillMastery = static_cast<uint32_t>(skillMastery(character, rangedSkillName));
        profile.rangedMinDamage = std::max(
            0,
            resolveRangedDamageSkillBonus(character, equippedItems)
                + (equippedItems.pBow != nullptr ? weaponMinDamage(*equippedItems.pBow) : 0)
                + character.weaponEnchantmentDamageBonus
                + character.permanentBonuses.rangedDamage
                + character.magicalBonuses.rangedDamage);
        profile.rangedMaxDamage = std::max(
            profile.rangedMinDamage,
            resolveRangedDamageSkillBonus(character, equippedItems)
                + (equippedItems.pBow != nullptr ? weaponMaxDamage(*equippedItems.pBow) : 0)
                + character.weaponEnchantmentDamageBonus
                + character.permanentBonuses.rangedDamage
                + character.magicalBonuses.rangedDamage);
    }
    else if (profile.hasWand || profile.hasBlaster)
    {
        profile.rangedAttackBonus = summary.combat.attack;
        const std::string rangedSkillName =
            profile.hasBlaster ? "Blaster" : canonicalSkillName(
                equippedItems.pMainHand != nullptr ? equippedItems.pMainHand->skillGroup : std::string());
        profile.rangedSkillLevel = static_cast<uint32_t>(std::max(0, skillLevel(character, rangedSkillName)));
        profile.rangedSkillMastery = static_cast<uint32_t>(skillMastery(character, rangedSkillName));
        profile.rangedMinDamage = profile.meleeMinDamage;
        profile.rangedMaxDamage = profile.meleeMaxDamage;

        if (profile.hasWand && equippedItems.pMainHand != nullptr)
        {
            int spellId = 0;

            if (tryParseSpellIdToken(equippedItems.pMainHand->mod1, spellId))
            {
                profile.wandSpellId = spellId;
            }
        }
    }

    return profile;
}

CharacterAttackResult GameMechanics::resolveCharacterAttackAgainstArmorClass(
    const Character &character,
    const ItemTable *pItemTable,
    const SpellTable *pSpellTable,
    int targetArmorClass,
    float targetDistance,
    std::mt19937 &rng)
{
    CharacterAttackResult result = {};
    const CharacterAttackProfile profile = buildCharacterAttackProfile(character, pItemTable, pSpellTable);
    const bool inMeleeRange = targetDistance <= OeCharacterMeleeAttackDistance;
    const bool inRangedRange = targetDistance <= OeCharacterRangedAttackDistance;
    result.targetArmorClass = std::max(0, targetArmorClass);
    result.targetDistance = std::max(0.0f, targetDistance);

    if (profile.hasBlaster && profile.rangedAttackBonus.has_value())
    {
        result.mode = CharacterAttackMode::Blaster;
    }
    else if (profile.hasWand && profile.rangedAttackBonus.has_value())
    {
        result.mode = CharacterAttackMode::Wand;
    }
    else if (inMeleeRange)
    {
        result.mode = CharacterAttackMode::Melee;
    }
    else if (profile.hasBow && profile.rangedAttackBonus.has_value())
    {
        result.mode = CharacterAttackMode::Bow;
    }

    if (result.mode == CharacterAttackMode::None)
    {
        result.mode = CharacterAttackMode::Melee;
        result.recoverySeconds = profile.meleeRecoverySeconds;
        result.attackSoundHook = "melee_swing";
        result.voiceHook = "attack";
        return result;
    }

    if (result.mode == CharacterAttackMode::Melee)
    {
        result.canAttack = inMeleeRange;
        result.attackBonus = profile.meleeAttackBonus;
        result.recoverySeconds = profile.meleeRecoverySeconds;
        result.attackSoundHook = "melee_swing";
    }
    else
    {
        result.canAttack = inRangedRange && profile.rangedAttackBonus.has_value();
        result.attackBonus = profile.rangedAttackBonus.value_or(profile.meleeAttackBonus);
        result.recoverySeconds = profile.rangedRecoverySeconds;
        result.resolvesOnImpact = true;
        result.skillLevel = profile.rangedSkillLevel;
        result.skillMastery = profile.rangedSkillMastery;
        result.spellId = profile.wandSpellId;
        result.attackSoundHook =
            result.mode == CharacterAttackMode::Bow
                ? "bow_shot"
                : (result.mode == CharacterAttackMode::Blaster ? "blaster_shot" : "wand_cast");
    }

    result.voiceHook = "attack";

    if (!result.canAttack)
    {
        return result;
    }

    if (result.mode != CharacterAttackMode::Melee)
    {
        result.hit = characterRangedAttackHitsArmorClass(result.targetArmorClass, result.attackBonus, targetDistance, rng);
    }
    else
    {
        result.hit = characterAttackHitsArmorClass(result.targetArmorClass, result.attackBonus, 0, 0, rng);

        if (!result.hit)
        {
            result.voiceHook = "attack_miss";
            return result;
        }
    }

    if (!result.hit)
    {
        result.voiceHook = "attack_miss";
    }

    const int minimumDamage =
        result.mode == CharacterAttackMode::Melee ? profile.meleeMinDamage : profile.rangedMinDamage;
    const int maximumDamage =
        result.mode == CharacterAttackMode::Melee ? profile.meleeMaxDamage : profile.rangedMaxDamage;
    result.damage = randomInclusive(rng, minimumDamage, maximumDamage);

    if (!result.resolvesOnImpact)
    {
        result.damageSoundHook = "target_hit";
    }

    return result;
}

bool GameMechanics::characterRangedAttackHitsArmorClass(
    int targetArmorClass,
    int attackBonus,
    float targetDistance,
    std::mt19937 &rng)
{
    int distanceMode = 1;

    if (targetDistance >= OeCharacterRangedAttackDistance)
    {
        distanceMode = 3;
    }
    else if (targetDistance >= 2560.0f)
    {
        distanceMode = 2;
    }

    return characterAttackHitsArmorClass(std::max(0, targetArmorClass), attackBonus, distanceMode, 0, rng);
}

std::optional<CharacterCondition> GameMechanics::displayedCondition(const Character &character)
{
    if (hasCondition(character, CharacterCondition::Eradicated))
    {
        return CharacterCondition::Eradicated;
    }

    if (hasCondition(character, CharacterCondition::Petrified))
    {
        return CharacterCondition::Petrified;
    }

    if (hasCondition(character, CharacterCondition::Dead))
    {
        return CharacterCondition::Dead;
    }

    if (hasCondition(character, CharacterCondition::Unconscious) || character.health <= 0)
    {
        return CharacterCondition::Unconscious;
    }

    if (hasCondition(character, CharacterCondition::Paralyzed))
    {
        return CharacterCondition::Paralyzed;
    }

    if (hasCondition(character, CharacterCondition::Asleep))
    {
        return CharacterCondition::Asleep;
    }

    if (hasCondition(character, CharacterCondition::Insane))
    {
        return CharacterCondition::Insane;
    }

    if (hasCondition(character, CharacterCondition::Fear))
    {
        return CharacterCondition::Fear;
    }

    if (hasCondition(character, CharacterCondition::DiseaseSevere)
        || hasCondition(character, CharacterCondition::DiseaseMedium)
        || hasCondition(character, CharacterCondition::DiseaseWeak))
    {
        return CharacterCondition::DiseaseSevere;
    }

    if (hasCondition(character, CharacterCondition::PoisonSevere)
        || hasCondition(character, CharacterCondition::PoisonMedium)
        || hasCondition(character, CharacterCondition::PoisonWeak))
    {
        return CharacterCondition::PoisonSevere;
    }

    if (hasCondition(character, CharacterCondition::Weak))
    {
        return CharacterCondition::Weak;
    }

    if (hasCondition(character, CharacterCondition::Cursed))
    {
        return CharacterCondition::Cursed;
    }

    if (hasCondition(character, CharacterCondition::Drunk))
    {
        return CharacterCondition::Drunk;
    }

    return std::nullopt;
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
    return canAct(character) && character.recoverySecondsRemaining <= 0.0f;
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

    return ItemRuntime::characterMeetsClassRestriction(character, itemDefinition)
        && ItemRuntime::characterMeetsRaceRestriction(character, itemDefinition);
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
