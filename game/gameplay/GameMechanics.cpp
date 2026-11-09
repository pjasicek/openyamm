#include "game/gameplay/GameMechanics.h"
#include "engine/Localization.h"

#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/party/SpellIds.h"
#include "game/rules/ExperienceRules.h"
#include "game/rules/GameRules.h"
#include "game/party/SkillData.h"
#include "game/tables/CharacterDollTable.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/SpellTable.h"

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <limits>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
constexpr float OeCharacterMeleeAttackDistance = 407.2f;
constexpr float OeCharacterRangedAttackDistance = 5120.0f;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr int OeMinimumMeleeRecoveryTicks = 30;
constexpr int OeMinimumRangedRecoveryTicks = 5;
constexpr uint32_t WandAttackSkillLevel = 8;
constexpr uint32_t Mm7WetsuitItemId = 1406;
// Blasters flagged ScatterBlaster (the Blaster Shotgun) fire a volley across Ice Blast's arc and recover slower.
constexpr const char *ScatterBlasterContentFlag = "ScatterBlaster";
constexpr uint8_t ScatterBlasterProjectileCount = 7;
constexpr float ScatterBlasterSpreadArcRadians = 3.14159265358979323846f / 3.0f;
constexpr int ScatterBlasterExtraRecoveryTicks = 20;
// Hesper's Kreegan weapons: their classic weapon skill as usual (Blaster for the guns, Sword, Axe... for the blades),
// plus Energy Guns or Energy Blades on top, like Armsmaster: a share of the weapon's own damage per rank by mastery.
constexpr const char *EnergyBladeContentFlag = "EnergyBlade";
constexpr const char *EnergyGunContentFlag = "EnergyGun";
constexpr std::array<int, 4> EnergyGunsPercentPerRank = {1, 4, 7, 10};
constexpr std::array<int, 4> EnergyBladesPercentPerRank = {2, 6, 10, 15};
// An energy gun's own base recovery (content flag Recovery<ticks>, e.g. Recovery90), else the blaster's 30; it recovers
// at most this fast, whatever the setting for classic blasters (blaster_min_recovery).
constexpr const char *RecoveryContentFlagPrefix = "Recovery";
constexpr int EnergyGunMinimumRecoveryTicks = 15;

constexpr int ParameterBonusThresholds[29] = {
    500, 400, 350, 300, 275, 250, 225, 200, 175, 150, 125, 100, 75, 50, 40,
    35, 30, 25, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3, 0,
};

constexpr int ParameterBonusValues[29] = {
    30, 25, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8,
    7, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5, -6,
};

const ClassMultiplierTable *g_pClassMultiplierTable = nullptr;

bool monsterHourOfPowerBoostsDamageResistance(CombatDamageType damageType)
{
    switch (damageType)
    {
        case CombatDamageType::Fire:
        case CombatDamageType::Air:
        case CombatDamageType::Water:
        case CombatDamageType::Earth:
        case CombatDamageType::Mind:
        case CombatDamageType::Body:
            return true;
        case CombatDamageType::Physical:
        case CombatDamageType::Spirit:
        case CombatDamageType::Light:
        case CombatDamageType::Dark:
        case CombatDamageType::Energy:
        case CombatDamageType::Irresistible:
        default:
            return false;
    }
}

bool canTrainToNextLevel(const Character &character, const ExperienceRules &experienceRules)
{
    return static_cast<uint64_t>(character.experience) >= experienceRules.experienceForNextLevel(character.level);
}

std::string experienceInspectSubject(const Character &character)
{
    return character.name.empty() ? Engine::tr("This character") : character.name;
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
    // The ruleset's numbers for each item in allEquippedItems order, where they replace the table's dice and armour.
    std::array<std::optional<ItemBaseStats>, 16> rulesetStats = {};
};

constexpr size_t OffHandItemIndex = 0;
constexpr size_t MainHandItemIndex = 1;
constexpr size_t BowItemIndex = 2;

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

std::optional<ClassMultiplierEntry> classMultiplierForClassName(
    const std::string &className,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    if (pClassMultiplierTable != nullptr)
    {
        const ClassMultiplierEntry *pEntry = pClassMultiplierTable->get(className);

        if (pEntry != nullptr)
        {
            return *pEntry;
        }
    }

    if (g_pClassMultiplierTable != nullptr)
    {
        const ClassMultiplierEntry *pEntry = g_pClassMultiplierTable->get(className);

        if (pEntry != nullptr)
        {
            return *pEntry;
        }
    }

    return std::nullopt;
}

int levelWithBonus(uint32_t level, int statBonus)
{
    return static_cast<int>(level) + statBonus;
}

uint32_t levelWithModifier(uint32_t level, int levelModifier)
{
    const int64_t adjustedLevel = static_cast<int64_t>(std::max(level, 1u)) + levelModifier;
    return static_cast<uint32_t>(std::clamp<int64_t>(
        adjustedLevel,
        1,
        std::numeric_limits<uint32_t>::max()));
}

bool hasCondition(const Character &character, CharacterCondition condition)
{
    return character.conditions.test(static_cast<size_t>(condition));
}

bool isDragon(const Character &character)
{
    return boundGameRules().classes.isDragon(character);
}

int skillLevel(const Character &character, std::string_view skillName)
{
    const CharacterSkill *pSkill = character.findSkill(std::string(skillName));
    const int bonusLevel = character.skillBonus(std::string(skillName));
    return (pSkill != nullptr ? static_cast<int>(pSkill->level) : 0) + bonusLevel;
}

SkillMastery skillMastery(const Character &character, std::string_view skillName)
{
    const CharacterSkill *pSkill = character.findSkill(std::string(skillName));
    return pSkill != nullptr ? pSkill->mastery : SkillMastery::None;
}

bool percentRoll(std::mt19937 &rng, int percentChance)
{
    if (percentChance <= 0)
    {
        return false;
    }

    if (percentChance >= 100)
    {
        return true;
    }

    return std::uniform_int_distribution<int>(1, 100)(rng) <= percentChance;
}

std::string normalizedToken(std::string value)
{
    value.erase(
        std::remove_if(
            value.begin(),
            value.end(),
            [](unsigned char character)
            {
                return std::isspace(character) || character == '_' || character == '-';
            }),
        value.end());

    for (char &character : value)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return value;
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

int resourceSkillBonus(const Character &character, std::string_view skillName, int resourcePerLevel)
{
    if (resourcePerLevel == 0)
    {
        return 0;
    }

    const int level = skillLevel(character, skillName);
    const int multiplier = masteryMultiplier(skillMastery(character, skillName), 1, 2, 3, 5);
    return resourcePerLevel * level * multiplier;
}

std::optional<std::pair<int, int>> dragonBasicAttackDamageRange(const Character &character)
{
    if (!isDragon(character))
    {
        return std::nullopt;
    }

    const int dragonSkillLevel = skillLevel(character, "DragonAbility");
    const SkillMastery dragonMastery = skillMastery(character, "DragonAbility");

    if (dragonSkillLevel <= 0 || dragonMastery == SkillMastery::None)
    {
        return std::nullopt;
    }

    const int minimumDamage = std::max(1, dragonSkillLevel);
    const int maximumDamage = std::max(minimumDamage, dragonSkillLevel * 10);
    return {{minimumDamage, maximumDamage}};
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

    if (skillName == "Bow" || skillName == "Throwing" || skillName == "Staff")
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

const EquippedItemRuntimeState *equippedRuntimeState(const Character &character, EquipmentSlot slot)
{
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

    return pRuntimeState;
}

const ItemDefinition *getEquippedItem(const Character &character, EquipmentSlot slot, const ItemTable *pItemTable)
{
    if (pItemTable == nullptr)
    {
        return nullptr;
    }

    const EquippedItemRuntimeState *pRuntimeState = equippedRuntimeState(character, slot);

    const uint32_t itemId = equippedItemId(character.equipment, slot);
    const ItemDefinition *pItemDefinition = itemId != 0 ? pItemTable->get(itemId) : nullptr;

    if (pRuntimeState != nullptr && pRuntimeState->broken)
    {
        return nullptr;
    }

    if (pItemDefinition != nullptr
        && pItemDefinition->equipStat == "WeaponW"
        && (pRuntimeState == nullptr || pRuntimeState->currentCharges == 0))
    {
        return nullptr;
    }

    return pItemDefinition;
}

std::array<const ItemDefinition *, 16> allEquippedItems(const EquippedItems &equippedItems);

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
    const std::array<const ItemDefinition *, 16> items = allEquippedItems(equippedItems);
    const std::array<EquipmentSlot, 16> slots = {
        EquipmentSlot::OffHand, EquipmentSlot::MainHand, EquipmentSlot::Bow, EquipmentSlot::Armor,
        EquipmentSlot::Helm, EquipmentSlot::Belt, EquipmentSlot::Cloak, EquipmentSlot::Gauntlets,
        EquipmentSlot::Boots, EquipmentSlot::Amulet, EquipmentSlot::Ring1, EquipmentSlot::Ring2,
        EquipmentSlot::Ring3, EquipmentSlot::Ring4, EquipmentSlot::Ring5, EquipmentSlot::Ring6,
    };

    for (size_t index = 0; index < items.size(); ++index)
    {
        if (items[index] != nullptr)
        {
            equippedItems.rulesetStats[index] = boundGameRules().items.baseStats(
                *items[index], equippedRuntimeState(character, slots[index])->rulesetFields, int(character.level));
        }
    }

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

bool isSpearItem(const ItemDefinition &itemDefinition)
{
    return canonicalSkillName(itemDefinition.skillGroup) == "Spear";
}

bool isWetsuitItem(const ItemDefinition &itemDefinition)
{
    return itemDefinition.itemId == Mm7WetsuitItemId;
}

// Classic blasters and Hesper's energy guns (Blaster items flagged EnergyGun) fire the same blaster bolt.
bool isBlasterItem(const ItemDefinition &itemDefinition)
{
    return canonicalSkillName(itemDefinition.skillGroup) == "Blaster";
}

bool isEnergyGunItem(const ItemDefinition &itemDefinition)
{
    return isBlasterItem(itemDefinition) && itemDefinition.hasContentFlag(EnergyGunContentFlag);
}

// The share of a Kreegan weapon's own damage its tech skill adds, in per cent: rank times the mastery's rate.
int techWeaponDamagePercent(const Character &character, const char *pSkillName, const std::array<int, 4> &rates)
{
    const int level = std::max(0, skillLevel(character, pSkillName));
    const SkillMastery mastery = skillMastery(character, pSkillName);
    const int rate = mastery >= SkillMastery::Grandmaster ? rates[3] : mastery >= SkillMastery::Master ? rates[2]
        : mastery >= SkillMastery::Expert ? rates[1] : rates[0];
    return level * rate;
}

// The largest <percent> of the character's equipped item flags named <prefix><percent> (Coupler30), 0 without one:
// two implants of a family do not add up.
int equippedFlagPercent(const Character &character, std::string_view prefix)
{
    int best = 0;
    for (const std::string &flag : character.equippedItemEffectFlags)
    {
        if (flag.size() > prefix.size() && flag.rfind(prefix, 0) == 0
            && std::all_of(flag.begin() + prefix.size(), flag.end(), [](char c) { return c >= '0' && c <= '9'; }))
        {
            best = std::max(best, std::stoi(flag.substr(prefix.size())));
        }
    }
    return best;
}

// The sum of a list's ShieldDamage<percent> flags.
int shieldDamageFlagPercent(const std::vector<std::string> &flags)
{
    int percent = 0;
    for (const std::string &flag : flags)
    {
        constexpr std::string_view Prefix = "ShieldDamage";
        if (flag.size() > Prefix.size() && flag.rfind(Prefix, 0) == 0
            && std::all_of(flag.begin() + Prefix.size(), flag.end(), [](char c) { return c >= '0' && c <= '9'; }))
        {
            percent += std::stoi(flag.substr(Prefix.size()));
        }
    }
    return percent;
}

// A weapon's Workshop mod's ShieldDamage<percent> (the Shieldbreaker), 0 without one.
int workshopModShieldPercent(const EquippedItemRuntimeState &runtimeState, const ItemTable *pItemTable)
{
    const WorkshopModDefinition *pMod = pItemTable != nullptr && runtimeState.workshopModId != 0
        ? pItemTable->workshopMod(runtimeState.workshopModId) : nullptr;
    return pMod != nullptr ? shieldDamageFlagPercent(pMod->effect.flags) : 0;
}

// A Kreegan weapon's damage to raised shields: +25 % from Expert in its tech skill, its ShieldDamage<percent> flag and
// its Workshop mod's; together at most +100 % (ITEMS, "Stacking").
float techWeaponShieldDamageMultiplier(const ItemDefinition &weapon, SkillMastery mastery, int modPercent)
{
    const int percent = (mastery >= SkillMastery::Expert ? 25 : 0) + shieldDamageFlagPercent(weapon.contentFlags)
        + modPercent;
    return 1.0f + float(std::min(percent, 100)) / 100.0f;
}

std::optional<int> recoveryTicksContentFlag(const ItemDefinition &itemDefinition)
{
    for (const std::string &flag : itemDefinition.contentFlags)
    {
        if (flag.size() > std::char_traits<char>::length(RecoveryContentFlagPrefix)
            && flag.rfind(RecoveryContentFlagPrefix, 0) == 0
            && std::all_of(flag.begin() + std::char_traits<char>::length(RecoveryContentFlagPrefix), flag.end(),
                [](char character) { return character >= '0' && character <= '9'; }))
        {
            return std::stoi(flag.substr(std::char_traits<char>::length(RecoveryContentFlagPrefix)));
        }
    }
    return std::nullopt;
}

bool isWeaponItem(const ItemDefinition &itemDefinition)
{
    return isMeleeWeapon(itemDefinition) || isWandWeapon(itemDefinition);
}

bool requiresLearnedSkillToEquip(const ItemDefinition &itemDefinition)
{
    const std::string skillName = canonicalSkillName(itemDefinition.skillGroup);

    // Anyone can wield a club: it has no skill of its own (MM7, MM8 and MMerge).
    return !skillName.empty() && skillName != "Misc" && skillName != "Club";
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

// An equipped weapon's attack bonus and damage: the ruleset's numbers where it has them, else the table's.
int equippedAttackModifier(const EquippedItems &equippedItems, size_t index, const ItemDefinition &itemDefinition)
{
    const std::optional<ItemBaseStats> &stats = equippedItems.rulesetStats[index];
    return stats ? stats->attackBonus : itemDamageModifier(itemDefinition);
}

int equippedMinDamage(const EquippedItems &equippedItems, size_t index, const ItemDefinition &itemDefinition)
{
    const std::optional<ItemBaseStats> &stats = equippedItems.rulesetStats[index];
    return stats ? stats->minimumDamage : weaponMinDamage(itemDefinition);
}

int equippedMaxDamage(const EquippedItems &equippedItems, size_t index, const ItemDefinition &itemDefinition)
{
    const std::optional<ItemBaseStats> &stats = equippedItems.rulesetStats[index];
    return stats ? stats->maximumDamage : weaponMaxDamage(itemDefinition);
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

// Energy Blades with an energy blade in the main hand, on top of its classic weapon skill: a share of the blade's own
// damage (its minimum or maximum).
int resolveEnergyBladeDamageBonus(const Character &character, const EquippedItems &equippedItems, bool maximum)
{
    const ItemDefinition *pWeapon = equippedItems.pMainHand;

    if (pWeapon == nullptr || !pWeapon->hasContentFlag(EnergyBladeContentFlag))
    {
        return 0;
    }

    const int weaponDamage = maximum ? equippedMaxDamage(equippedItems, MainHandItemIndex, *pWeapon)
                                     : equippedMinDamage(equippedItems, MainHandItemIndex, *pWeapon);
    return weaponDamage * techWeaponDamagePercent(character, "EnergyBlades", EnergyBladesPercentPerRank) / 100;
}

int resolveBlasterDamageSkillBonus(const Character &character, CharacterAttackTuning attackTuning)
{
    if (attackTuning.blasterSkillScaling != BlasterSkillScalingMode::ScalingDamage)
    {
        return 0;
    }

    const int level = skillLevel(character, "Blaster");

    if (level <= 0)
    {
        return 0;
    }

    return masteryMultiplier(skillMastery(character, "Blaster"), 0, 0, 0, 1) * level;
}

std::pair<int, int> resolveBlasterDamageRange(
    const Character &character,
    const ItemDefinition *pBlasterItem,
    CharacterAttackTuning attackTuning)
{
    const int skillDamageBonus = resolveBlasterDamageSkillBonus(character, attackTuning);
    // An energy gun adds Energy Guns' share of its own damage.
    const int energyPercent = pBlasterItem != nullptr && isEnergyGunItem(*pBlasterItem)
        ? techWeaponDamagePercent(character, "EnergyGuns", EnergyGunsPercentPerRank) : 0;
    const int weaponMinimum = pBlasterItem != nullptr ? weaponMinDamage(*pBlasterItem) : 0;
    const int weaponMaximum = pBlasterItem != nullptr ? weaponMaxDamage(*pBlasterItem) : 0;
    const int minimumDamage = std::max(0, weaponMinimum + weaponMinimum * energyPercent / 100 + skillDamageBonus);
    const int maximumDamage =
        std::max(minimumDamage, weaponMaximum + weaponMaximum * energyPercent / 100 + skillDamageBonus);
    return {minimumDamage, maximumDamage};
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

int resolveClassicMeleeDamageSkillBonus(
    const Character &character,
    const EquippedItems &equippedItems,
    CharacterAttackTuning attackTuning)
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
        return resolveBlasterDamageSkillBonus(character, attackTuning);
    }

    return armsmasterBonus;
}

int resolveMeleeDamageSkillBonus(
    const Character &character,
    const EquippedItems &equippedItems,
    CharacterAttackTuning attackTuning,
    bool maximum)
{
    return resolveClassicMeleeDamageSkillBonus(character, equippedItems, attackTuning)
        + resolveEnergyBladeDamageBonus(character, equippedItems, maximum);
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

    if (skillName == "Throwing")
    {
        return masteryMultiplier(skillMastery(character, "Throwing"), 1, 1, 2, 3) * level;
    }

    if (skillName == "Blaster")
    {
        return masteryMultiplier(skillMastery(character, "Blaster"), 1, 2, 3, 5) * level;
    }

    return level;
}

int resolveRangedDamageSkillBonus(
    const Character &character,
    const EquippedItems &equippedItems,
    CharacterAttackTuning attackTuning)
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

    if (skillName == "Throwing")
    {
        return masteryMultiplier(skillMastery(character, "Throwing"), 0, 1, 1, 2) * level;
    }

    if (skillName == "Blaster")
    {
        return resolveBlasterDamageSkillBonus(character, attackTuning);
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

    for (size_t index = 0; index < equipped.size(); ++index)
    {
        if (equipped[index] == nullptr)
        {
            continue;
        }

        const std::optional<ItemBaseStats> &stats = equippedItems.rulesetStats[index];
        armorValue += stats ? stats->armorClass : passiveArmorValue(*equipped[index]);
    }

    return armorValue;
}

int resolveMeleeAttackItemBonus(const EquippedItems &equippedItems)
{
    int attackBonus = 0;

    if (equippedItems.pMainHand != nullptr && isMeleeWeapon(*equippedItems.pMainHand))
    {
        attackBonus += equippedAttackModifier(equippedItems, MainHandItemIndex, *equippedItems.pMainHand);
    }

    if (equippedItems.pOffHand != nullptr && isMeleeWeapon(*equippedItems.pOffHand))
    {
        attackBonus += equippedAttackModifier(equippedItems, OffHandItemIndex, *equippedItems.pOffHand);
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
        damage += equippedMinDamage(equippedItems, MainHandItemIndex, *equippedItems.pMainHand);

        if (canonicalSkillName(equippedItems.pMainHand->skillGroup) == "Spear" && equippedItems.pOffHand == nullptr)
        {
            damage += 1;
        }
    }

    if (equippedItems.pOffHand != nullptr && isMeleeWeapon(*equippedItems.pOffHand))
    {
        damage += equippedMinDamage(equippedItems, OffHandItemIndex, *equippedItems.pOffHand);
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
        damage += equippedMaxDamage(equippedItems, MainHandItemIndex, *equippedItems.pMainHand);
    }

    if (equippedItems.pOffHand != nullptr && isMeleeWeapon(*equippedItems.pOffHand))
    {
        damage += equippedMaxDamage(equippedItems, OffHandItemIndex, *equippedItems.pOffHand);
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
        + equippedAttackModifier(equippedItems, BowItemIndex, *equippedItems.pBow)
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

            boundGameRules().items.applyEquippedEnchantEffects(
                *pItemDefinition,
                runtimeState,
                pStandardItemEnchantTable,
                pSpecialItemEnchantTable,
                character,
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

// The original's ageing: from 50, 100 and 150 years a primary stat's own value is scaled, Might and Endurance to
// 75, 40 and 10 %, Intellect and Personality to 150, 100 and 10 %, Speed and Accuracy to 100, 40 and 10 %; Luck keeps
// its value (OY-349).
int ageingPercent(const Character &character, uint32_t rawStatId)
{
    const int age = GameMechanics::characterAge(character);
    const int bracket = age >= 150 ? 3 : age >= 100 ? 2 : age >= 50 ? 1 : 0;

    if (bracket == 0)
    {
        return 100;
    }

    static constexpr std::array<std::array<int, 3>, 7> Percents = {{
        {75, 40, 10}, {150, 100, 10}, {150, 100, 10}, {75, 40, 10}, {100, 40, 10}, {100, 40, 10}, {100, 100, 100}}};
    const uint32_t statIndex = rawStatId >= 0x27 ? rawStatId - 0x27 : rawStatId - 0x20;
    return statIndex < Percents.size() ? Percents[statIndex][size_t(bracket - 1)] : 100;
}

int resolveCharacterSheetActualPrimaryStatValue(
    const Character &character,
    uint32_t rawStatId,
    const CharacterStatBonuses &equippedItemBonuses)
{
    const int baseValue = resolveCharacterPrimaryStatBaseValue(character, rawStatId);
    const int agedBaseValue = baseValue * ageingPercent(character, rawStatId) / 100;
    return resolveCharacterSheetBasePrimaryStatValue(character, rawStatId, equippedItemBonuses)
        - baseValue + agedBaseValue
        + resolveCharacterPrimaryStatMagicalBonusValue(character, rawStatId)
        - resolveCharacterPrimaryStatEquippedItemBonusValue(equippedItemBonuses, rawStatId);
}

std::string conditionNameText(CharacterCondition condition)
{
    if (condition == CharacterCondition::Eradicated)
    {
        return std::string(Engine::trNoop("Eradicated"));
    }

    if (condition == CharacterCondition::Petrified)
    {
        return std::string(Engine::trNoop("Petrified"));
    }

    if (condition == CharacterCondition::Dead)
    {
        return std::string(Engine::trNoop("Dead"));
    }

    if (condition == CharacterCondition::Unconscious)
    {
        return std::string(Engine::trNoop("Unconscious"));
    }

    if (condition == CharacterCondition::Paralyzed)
    {
        return std::string(Engine::trNoop("Paralyzed"));
    }

    if (condition == CharacterCondition::Asleep)
    {
        return std::string(Engine::trNoop("Asleep"));
    }

    if (condition == CharacterCondition::Insane)
    {
        return std::string(Engine::trNoop("Insane"));
    }

    if (condition == CharacterCondition::Fear)
    {
        return std::string(Engine::trNoop("Afraid"));
    }

    if (condition == CharacterCondition::DiseaseSevere
        || condition == CharacterCondition::DiseaseMedium
        || condition == CharacterCondition::DiseaseWeak)
    {
        return std::string(Engine::trNoop("Diseased"));
    }

    if (condition == CharacterCondition::PoisonSevere
        || condition == CharacterCondition::PoisonMedium
        || condition == CharacterCondition::PoisonWeak)
    {
        return std::string(Engine::trNoop("Poisoned"));
    }

    if (condition == CharacterCondition::Weak)
    {
        return std::string(Engine::trNoop("Weak"));
    }

    if (condition == CharacterCondition::Cursed)
    {
        return std::string(Engine::trNoop("Cursed"));
    }

    if (condition == CharacterCondition::Drunk)
    {
        return std::string(Engine::trNoop("Drunk"));
    }

    return std::string(Engine::trNoop("Good"));
}

std::string resolveConditionText(const Character &character)
{
    const std::optional<CharacterCondition> condition = GameMechanics::displayedCondition(character);
    return condition ? conditionNameText(*condition) : "Good";
}

float resolveAttackRecoverySeconds(
    const Character &character,
    const EquippedItems &equippedItems,
    const SpellTable *pSpellTable,
    CharacterAttackMode mode,
    CharacterAttackTuning attackTuning)
{
    bool usesBow = mode == CharacterAttackMode::Bow;
    bool usesBlaster = mode == CharacterAttackMode::Blaster;
    bool usesDragonBreath = mode == CharacterAttackMode::DragonBreath;
    const ItemDefinition *pWeapon = nullptr;
    int weaponRecoveryTicks = baseRecoveryTicksForSkillName("Staff");

    if (usesBow)
    {
        pWeapon = equippedItems.pBow;

        if (pWeapon != nullptr)
        {
            const std::string weaponSkillName = canonicalSkillName(pWeapon->skillGroup);
            weaponRecoveryTicks = baseRecoveryTicksForSkillName(weaponSkillName);

            if (weaponSkillName == "Throwing")
            {
                const SkillMastery throwingMastery = skillMastery(character, "Throwing");
                weaponRecoveryTicks += throwingMastery >= SkillMastery::Grandmaster
                    ? 0
                    : throwingMastery >= SkillMastery::Master ? 15 : 30;
            }
        }
    }
    else if (usesDragonBreath)
    {
        if (pSpellTable != nullptr)
        {
            const SpellEntry *pSpellEntry = pSpellTable->findById(spellIdValue(SpellId::DragonBreath));

            if (pSpellEntry != nullptr)
            {
                switch (skillMastery(character, "DragonAbility"))
                {
                    case SkillMastery::Expert:
                        weaponRecoveryTicks = std::max(pSpellEntry->expertRecoveryTicks, 1);
                        break;

                    case SkillMastery::Master:
                        weaponRecoveryTicks = std::max(pSpellEntry->masterRecoveryTicks, 1);
                        break;

                    case SkillMastery::Grandmaster:
                        weaponRecoveryTicks = std::max(pSpellEntry->grandmasterRecoveryTicks, 1);
                        break;

                    case SkillMastery::Normal:
                    case SkillMastery::None:
                    default:
                        weaponRecoveryTicks = std::max(pSpellEntry->normalRecoveryTicks, 1);
                        break;
                }
            }
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

    if (usesBlaster && pWeapon != nullptr && pWeapon->hasContentFlag(ScatterBlasterContentFlag))
    {
        weaponRecoveryTicks += ScatterBlasterExtraRecoveryTicks;
    }

    const bool energyGun = usesBlaster && pWeapon != nullptr && isEnergyGunItem(*pWeapon);

    if (energyGun)
    {
        weaponRecoveryTicks = recoveryTicksContentFlag(*pWeapon).value_or(weaponRecoveryTicks);
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

    if (!usesBow && !usesBlaster && !usesDragonBreath)
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

    // Hesper's items: ticks off an energy gun's or a melee strike's recovery (item_effects), a melee recovery share
    // (MeleeRecovery<percent>Pct) and floor (MeleeAttackFloor<ticks>, MeleeAttackFloorMinus5).
    if (mode == CharacterAttackMode::Melee)
    {
        recoveryTicks -= character.meleeRecoveryReductionTicks;
        for (const std::string &flag : character.equippedItemEffectFlags)
        {
            if (flag == "MeleeAttackFloorMinus5")
            {
                continue;
            }
            if (flag.rfind("MeleeRecovery", 0) == 0 && flag.size() > 16 && flag.substr(flag.size() - 3) == "Pct")
            {
                recoveryTicks = recoveryTicks * (100 - std::stoi(flag.substr(13, flag.size() - 16))) / 100;
            }
            else if (flag.rfind("MeleeAttackFloor", 0) == 0)
            {
                minimumRecoveryTicks = std::min(minimumRecoveryTicks, std::stoi(flag.substr(16)));
            }
        }
        if (character.equippedItemEffectFlags.contains("MeleeAttackFloorMinus5"))
        {
            minimumRecoveryTicks -= 5;
        }
    }

    if (energyGun)
    {
        recoveryTicks -= character.gunRecoveryReductionTicks;
        minimumRecoveryTicks = EnergyGunMinimumRecoveryTicks;
    }
    else if (mode == CharacterAttackMode::Blaster)
    {
        minimumRecoveryTicks = std::clamp(attackTuning.blasterMinimumRecoveryTicks, 0, 300);
    }
    else if (mode == CharacterAttackMode::Bow
        || mode == CharacterAttackMode::Wand
        || mode == CharacterAttackMode::DragonBreath)
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

int characterSheetFiniteValue(const CharacterSheetValue &value)
{
    return value.infinite ? 200 : value.actual;
}

int resistanceValueForDamageType(const CharacterSheetSummary &summary, CombatDamageType damageType)
{
    switch (damageType)
    {
        case CombatDamageType::Fire: return summary.fireResistance.actual;
        case CombatDamageType::Air: return summary.airResistance.actual;
        case CombatDamageType::Water: return summary.waterResistance.actual;
        case CombatDamageType::Earth: return summary.earthResistance.actual;
        case CombatDamageType::Mind: return summary.mindResistance.actual;
        case CombatDamageType::Body: return summary.bodyResistance.actual;
        case CombatDamageType::Spirit: return characterSheetFiniteValue(summary.bodyResistance);
        case CombatDamageType::Physical:
        case CombatDamageType::Light:
        case CombatDamageType::Dark:
        case CombatDamageType::Energy:
        case CombatDamageType::Irresistible:
        default:
            return 0;
    }
}

bool resistanceImmuneForDamageType(const CharacterSheetSummary &summary, CombatDamageType damageType)
{
    switch (damageType)
    {
        case CombatDamageType::Fire: return summary.fireResistance.infinite;
        case CombatDamageType::Air: return summary.airResistance.infinite;
        case CombatDamageType::Water: return summary.waterResistance.infinite;
        case CombatDamageType::Earth: return summary.earthResistance.infinite;
        case CombatDamageType::Mind: return summary.mindResistance.infinite;
        case CombatDamageType::Body:
        case CombatDamageType::Spirit:
            return summary.bodyResistance.infinite;
        case CombatDamageType::Physical:
        case CombatDamageType::Light:
        case CombatDamageType::Dark:
        case CombatDamageType::Energy:
        case CombatDamageType::Irresistible:
        default:
            return false;
    }
}

bool characterWearsArmorSkill(
    const Character &character,
    const ItemTable *pItemTable,
    const std::string &skillName)
{
    if (pItemTable == nullptr || character.equipment.armor == 0)
    {
        return false;
    }

    const ItemDefinition *pArmor = pItemTable->get(character.equipment.armor);
    return pArmor != nullptr && canonicalSkillName(pArmor->skillGroup) == skillName;
}

bool weaponUsesSkill(const ItemDefinition *pItemDefinition, const std::string &skillName)
{
    return pItemDefinition != nullptr && canonicalSkillName(pItemDefinition->skillGroup) == skillName;
}

void applyMeleeWeaponEffects(
    const Character &character,
    const EquippedItems &equippedItems,
    CharacterAttackResult &result,
    std::mt19937 &rng)
{
    result.itemStunTarget = result.stunTarget;
    const bool staffHit = weaponUsesSkill(equippedItems.pMainHand, "Staff");
    const int staffLevel = skillLevel(character, "Staff");

    if (staffHit && staffLevel > 0 && skillMastery(character, "Staff") >= SkillMastery::Master
        && percentRoll(rng, staffLevel))
    {
        result.stunTarget = true;
        result.skillLevel = std::max<uint32_t>(result.skillLevel, static_cast<uint32_t>(staffLevel));
    }

    if (weaponUsesSkill(equippedItems.pMainHand, "Mace"))
    {
        const int maceLevel = skillLevel(character, "Mace");

        if (maceLevel > 0 && skillMastery(character, "Mace") >= SkillMastery::Master
            && percentRoll(rng, maceLevel))
        {
            result.stunTarget = true;
            result.skillLevel = std::max<uint32_t>(result.skillLevel, static_cast<uint32_t>(maceLevel));
        }

        if (maceLevel > 0 && skillMastery(character, "Mace") >= SkillMastery::Grandmaster
            && percentRoll(rng, maceLevel))
        {
            result.paralyzeTarget = true;
            result.skillLevel = std::max<uint32_t>(result.skillLevel, static_cast<uint32_t>(maceLevel));
        }
    }

    if (weaponUsesSkill(equippedItems.pMainHand, "Axe"))
    {
        const int axeLevel = skillLevel(character, "Axe");

        if (axeLevel > 0 && skillMastery(character, "Axe") >= SkillMastery::Grandmaster
            && percentRoll(rng, axeLevel))
        {
            result.halveTargetArmorClass = true;
            result.skillLevel = std::max<uint32_t>(result.skillLevel, static_cast<uint32_t>(axeLevel));
        }
    }

    const bool daggerHit =
        weaponUsesSkill(equippedItems.pMainHand, "Dagger")
        || weaponUsesSkill(equippedItems.pOffHand, "Dagger");

    if (daggerHit && skillMastery(character, "Dagger") >= SkillMastery::Master && percentRoll(rng, 10))
    {
        result.damage *= 3;
        result.criticalDamage = true;
    }
}
}

void GameMechanics::bindClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable)
{
    g_pClassMultiplierTable = pClassMultiplierTable;
}

uint32_t GameMechanics::maximumTrainableLevelFromExperience(
    const Character &character,
    const ExperienceRules &experienceRules)
{
    uint32_t trainableLevel = character.level;

    while (static_cast<uint64_t>(character.experience) >= experienceRules.experienceForNextLevel(trainableLevel))
    {
        ++trainableLevel;
    }

    return trainableLevel;
}

int GameMechanics::calculateBaseCharacterMaxHealth(
    const Character &character,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    const std::string className = character.className.empty() ? character.role : character.className;
    const std::optional<ClassMultiplierEntry> multiplier =
        classMultiplierForClassName(className, pClassMultiplierTable);

    if (!multiplier.has_value())
    {
        const int endurance = std::max(10, static_cast<int>(character.endurance));
        return std::max(1, 40 + endurance * 2 + static_cast<int>(character.level) * 5);
    }

    if (const std::optional<int> health = boundGameRules().classes.baseMaxHealth(character, *multiplier))
    {
        return *health;
    }

    const int enduranceBonus = parameterBonus(static_cast<int>(character.endurance));
    const int healthByLevel =
        multiplier->healthPerLevel * levelWithBonus(std::max(character.level, 1u), enduranceBonus);
    const int healthBySkill = resourceSkillBonus(character, "Bodybuilding", multiplier->healthPerLevel);
    return std::max(0, multiplier->baseHealth + healthByLevel + healthBySkill);
}

int GameMechanics::calculateBaseCharacterMaxSpellPoints(
    const Character &character,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    const std::string className = character.className.empty() ? character.role : character.className;
    const std::optional<ClassMultiplierEntry> multiplier =
        classMultiplierForClassName(className, pClassMultiplierTable);

    if (!multiplier.has_value())
    {
        const int intellect = std::max(0, static_cast<int>(character.intellect));
        const int personality = std::max(0, static_cast<int>(character.personality));
        const bool isCaster = intellect > 0 || personality > 0;
        return isCaster
            ? std::max(0, ((intellect + personality) / 2) + static_cast<int>(character.level) * 3)
            : 0;
    }

    if (const std::optional<int> mana = boundGameRules().classes.baseMaxSpellPoints(character, *multiplier))
    {
        return *mana;
    }

    int statBonus = 0;

    switch (multiplier->manaMode)
    {
        case ClassManaMode::Intellect:
            statBonus = parameterBonus(static_cast<int>(character.intellect));
            break;

        case ClassManaMode::Personality:
            statBonus = parameterBonus(static_cast<int>(character.personality));
            break;

        case ClassManaMode::Mixed:
            statBonus = parameterBonus(static_cast<int>(character.intellect))
                + parameterBonus(static_cast<int>(character.personality));
            break;

        case ClassManaMode::Level:
            statBonus = 0;
            break;

        case ClassManaMode::None:
        default:
            return 0;
    }

    const int manaByLevel =
        multiplier->manaPerLevel * levelWithBonus(std::max(character.level, 1u), statBonus);
    const int manaBySkill = resourceSkillBonus(character, "Meditation", multiplier->manaPerLevel);
    return std::max(0, multiplier->baseMana + manaByLevel + manaBySkill);
}

int GameMechanics::calculateEffectiveCharacterMaxHealth(
    const Character &character,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    int maximum = character.maxHealth + character.permanentBonuses.maxHealth + character.magicalBonuses.maxHealth;

    if (character.levelModifier != 0)
    {
        Character baseCharacter = character;
        baseCharacter.levelModifier = 0;

        Character adjustedCharacter = baseCharacter;
        adjustedCharacter.level = levelWithModifier(character.level, character.levelModifier);

        maximum += calculateBaseCharacterMaxHealth(adjustedCharacter, pClassMultiplierTable)
            - calculateBaseCharacterMaxHealth(baseCharacter, pClassMultiplierTable);
    }

    return std::max(1, maximum);
}

int GameMechanics::calculateEffectiveCharacterMaxSpellPoints(
    const Character &character,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    int maximum =
        character.maxSpellPoints + character.permanentBonuses.maxSpellPoints + character.magicalBonuses.maxSpellPoints;

    if (character.levelModifier != 0)
    {
        Character baseCharacter = character;
        baseCharacter.levelModifier = 0;

        Character adjustedCharacter = baseCharacter;
        adjustedCharacter.level = levelWithModifier(character.level, character.levelModifier);

        maximum += calculateBaseCharacterMaxSpellPoints(adjustedCharacter, pClassMultiplierTable)
            - calculateBaseCharacterMaxSpellPoints(baseCharacter, pClassMultiplierTable);
    }

    return std::max(0, maximum);
}

void GameMechanics::refreshCharacterBaseResources(
    Character &character,
    bool restoreCurrentToMaximum,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    const int previousMaxHealth = calculateEffectiveCharacterMaxHealth(character, pClassMultiplierTable);
    const int previousMaxSpellPoints = calculateEffectiveCharacterMaxSpellPoints(character, pClassMultiplierTable);
    const bool wasAtMaxHealth = character.health >= previousMaxHealth;
    const bool wasAtMaxSpellPoints = character.spellPoints >= previousMaxSpellPoints;

    character.maxHealth = calculateBaseCharacterMaxHealth(character, pClassMultiplierTable);
    character.maxSpellPoints = calculateBaseCharacterMaxSpellPoints(character, pClassMultiplierTable);

    const int currentMaxHealth = calculateEffectiveCharacterMaxHealth(character, pClassMultiplierTable);
    const int currentMaxSpellPoints = calculateEffectiveCharacterMaxSpellPoints(character, pClassMultiplierTable);

    if (restoreCurrentToMaximum || wasAtMaxHealth)
    {
        character.health = currentMaxHealth;
    }
    else
    {
        character.health = std::clamp(character.health, 0, currentMaxHealth);
    }

    if (restoreCurrentToMaximum || wasAtMaxSpellPoints)
    {
        character.spellPoints = currentMaxSpellPoints;
    }
    else
    {
        character.spellPoints = std::clamp(character.spellPoints, 0, currentMaxSpellPoints);
    }
}

std::string GameMechanics::buildExperienceInspectSupplement(
    const Character &character,
    const ExperienceRules &experienceRules)
{
    const std::string subject = experienceInspectSubject(character);
    const uint64_t nextLevelExperience = experienceRules.experienceForNextLevel(character.level);

    if (static_cast<uint64_t>(character.experience) < nextLevelExperience)
    {
        return Engine::tr("{name} needs {experience} more experience to train to level {level}.",
            {{"name", subject},
                {"experience", nextLevelExperience - static_cast<uint64_t>(character.experience)},
                {"level", character.level + 1}});
    }

    // Eligible: also what the level after that needs (Discord request, 2026-11-02).
    const uint32_t trainableLevel = maximumTrainableLevelFromExperience(character, experienceRules);
    const uint64_t beyondExperience = experienceRules.experienceForNextLevel(trainableLevel);
    return Engine::tr("{name} is eligible to train up to level {level}. "
                      "{name} needs {experience} more experience for level {next}.",
        {{"name", subject},
            {"level", trainableLevel},
            {"experience", beyondExperience - static_cast<uint64_t>(character.experience)},
            {"next", trainableLevel + 1}});
}

int GameMechanics::primaryStatBonus(int value)
{
    return parameterBonus(value);
}

std::optional<int> GameMechanics::nextPrimaryStatBonusValue(int value)
{
    // The thresholds run from the highest down: the next one is the lowest above the value.
    for (size_t index = std::size(ParameterBonusThresholds); index-- > 0;)
    {
        if (ParameterBonusThresholds[index] > value)
        {
            return ParameterBonusThresholds[index];
        }
    }

    return std::nullopt;
}

float GameMechanics::averageResistedDamageShare(int resistance)
{
    if (resistance <= 0)
    {
        return 0.0f;
    }

    const float halveChance = float(resistance) / float(resistance + 30);
    float reachChance = 1.0f;
    float damageShare = 0.0f;

    // The rolls stop at the first that does not halve: after k halvings the hit keeps 1 / 2^k of its damage.
    for (int halvings = 0; halvings < 4; ++halvings)
    {
        damageShare += reachChance * (1.0f - halveChance) / float(1 << halvings);
        reachChance *= halveChance;
    }

    damageShare += reachChance / 16.0f;
    return 1.0f - damageShare;
}

float GameMechanics::monsterEffectResistChance(int bonus)
{
    return bonus > 0 ? float(bonus) / float(bonus + 30) : 0.0f;
}

int GameMechanics::enduranceHealthBonus(const Character &character, int endurance)
{
    const std::string className = character.className.empty() ? character.role : character.className;
    const std::optional<ClassMultiplierEntry> multiplier = classMultiplierForClassName(className, nullptr);
    return multiplier ? multiplier->healthPerLevel * parameterBonus(endurance) : 0;
}

std::optional<int> GameMechanics::primaryStatSpellPointBonus(
    const Character &character,
    const std::string &statName,
    int value)
{
    const std::string className = character.className.empty() ? character.role : character.className;
    const std::optional<ClassMultiplierEntry> multiplier = classMultiplierForClassName(className, nullptr);

    if (!multiplier)
    {
        return std::nullopt;
    }

    const bool counts = multiplier->manaMode == ClassManaMode::Mixed
        || (multiplier->manaMode == ClassManaMode::Intellect && statName == "Intellect")
        || (multiplier->manaMode == ClassManaMode::Personality && statName == "Personality");

    if (!counts)
    {
        return std::nullopt;
    }

    return multiplier->manaPerLevel * parameterBonus(value);
}

int GameMechanics::resolveCharacterItemSkillBonus(const Character &character, const std::string &skillName)
{
    const std::string canonicalName = canonicalSkillName(skillName);
    int totalBonus = 0;

    for (const std::pair<const std::string, int> &bonus : character.itemSkillBonuses)
    {
        if (canonicalSkillName(bonus.first) == canonicalName)
        {
            totalBonus += bonus.second;
        }
    }

    return totalBonus;
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
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    CharacterAttackTuning attackTuning,
    const ExperienceRules &experienceRules)
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

    // Rules that build attack, damage, armour and resistance from items and skills themselves (MAW).
    const std::optional<CharacterCombatRows> rulesetRows = boundGameRules().skills.combatRows(
        character, pItemTable, CharacterStatValues{actualMight, actualAccuracy, actualLuck});

    summary.might = makeSheetValue(baseMight, actualMight);
    summary.intellect = makeSheetValue(baseIntellect, actualIntellect);
    summary.personality = makeSheetValue(basePersonality, actualPersonality);
    summary.endurance = makeSheetValue(baseEndurance, actualEndurance);
    summary.accuracy = makeSheetValue(baseAccuracy, actualAccuracy);
    summary.speed = makeSheetValue(baseSpeed, actualSpeed);
    summary.luck = makeSheetValue(baseLuck, actualLuck);

    summary.health.baseMaximum = character.maxHealth + character.permanentBonuses.maxHealth;
    summary.health.maximum = calculateEffectiveCharacterMaxHealth(character);
    summary.health.current = std::min(character.health, std::max(0, summary.health.maximum));

    summary.spellPoints.baseMaximum = character.maxSpellPoints + character.permanentBonuses.maxSpellPoints;
    summary.spellPoints.maximum = calculateEffectiveCharacterMaxSpellPoints(character);
    summary.spellPoints.current = std::clamp(character.spellPoints, 0, std::max(0, summary.spellPoints.maximum));

    const int dragonArmorBonus = isDragon(character)
        ? 5 * std::max(0, skillLevel(character, "DragonAbility"))
        : 0;
    const int armorBase = rulesetRows
        ? rulesetRows->armorClass + character.permanentBonuses.armorClass
        : parameterBonus(actualSpeed)
            + resolvePassiveArmorBonus(equippedItems)
            + resolveArmorSkillBonus(character, equippedItems)
            + dragonArmorBonus
            + character.permanentBonuses.armorClass;
    const int armorActual = std::max(0, armorBase + character.magicalBonuses.armorClass);
    summary.armorClass = makeSheetValue(std::max(0, armorBase), armorActual);

    const int levelBonus = character.levelModifier + character.equippedLevelBonus;
    const int displayedActualLevel = levelBonus != 0
        ? static_cast<int>(levelWithModifier(character.level, levelBonus))
        : static_cast<int>(maximumTrainableLevelFromExperience(character, experienceRules));
    summary.level = makeSheetValue(static_cast<int>(character.level), displayedActualLevel);

    const bool leatherGrandmaster =
        equippedItems.pArmor != nullptr
        && canonicalSkillName(equippedItems.pArmor->skillGroup) == "LeatherArmor"
        && skillMastery(character, "LeatherArmor") >= SkillMastery::Grandmaster;
    const int leatherElementalResistanceBonus =
        leatherGrandmaster && !rulesetRows ? std::max(0, skillLevel(character, "LeatherArmor")) : 0;
    const CharacterResistanceSet skillResistances = rulesetRows ? rulesetRows->resistances : CharacterResistanceSet{};

    const int fireBase = character.baseResistances.fire
        + character.permanentBonuses.resistances.fire
        + equippedItemBonuses.resistances.fire
        + leatherElementalResistanceBonus
        + skillResistances.fire;
    const int airBase = character.baseResistances.air
        + character.permanentBonuses.resistances.air
        + equippedItemBonuses.resistances.air
        + leatherElementalResistanceBonus
        + skillResistances.air;
    const int waterBase = character.baseResistances.water
        + character.permanentBonuses.resistances.water
        + equippedItemBonuses.resistances.water
        + leatherElementalResistanceBonus
        + skillResistances.water;
    const int earthBase = character.baseResistances.earth
        + character.permanentBonuses.resistances.earth
        + equippedItemBonuses.resistances.earth
        + leatherElementalResistanceBonus
        + skillResistances.earth;
    const int mindBase = character.baseResistances.mind
        + character.permanentBonuses.resistances.mind
        + equippedItemBonuses.resistances.mind
        + skillResistances.mind;
    const int bodyBase = character.baseResistances.body
        + character.permanentBonuses.resistances.body
        + equippedItemBonuses.resistances.body
        + skillResistances.body;

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
        character.permanentImmunities.fire || character.magicalImmunities.fire
            || character.equippedItemEffectFlags.contains("FireImmune"));
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

    if (character.birthYear > 0 && character.birthYear <= static_cast<uint32_t>(CharacterAgeReferenceYear))
    {
        summary.ageText = std::to_string(characterAge(character));
    }
    else
    {
        summary.ageText = Engine::tr("N/A");
    }

    summary.experienceText = std::to_string(character.experience);
    summary.canTrainToNextLevel = canTrainToNextLevel(character, experienceRules);
    summary.conditionText = resolveConditionText(character);
    summary.quickSpellText = character.quickSpellName.empty() ? Engine::tr("None")
                                                              : Engine::localize(character.quickSpellName, "spell");

    const int meleeAttack = (rulesetRows
            ? rulesetRows->meleeAttack
            : parameterBonus(actualAccuracy)
                + resolveMeleeAttackItemBonus(equippedItems)
                + resolveMeleeAttackSkillBonus(character, equippedItems))
        + character.permanentBonuses.meleeAttack
        + character.magicalBonuses.meleeAttack;
    summary.combat.attack = meleeAttack;
    // A ruleset's rows hold its dragons' fangs and breath.
    const std::optional<std::pair<int, int>> dragonDamageRange =
        rulesetRows ? std::nullopt : dragonBasicAttackDamageRange(character);

    const int meleeMightBonus = parameterBonus(actualMight);
    // The weapons' elemental enchantments roll on each hit; the sheet shows their range with the physical one.
    const ElementalDamageRange meleeElementalDamage = ItemEnchantRuntime::characterAttackElementalDamageRange(
        character, CharacterAttackMode::Melee, pItemTable, pSpecialItemEnchantTable);
    const int meleeMinDamage = std::max(
        1,
        meleeMightBonus
            + resolveMeleeMinDamageItemBonus(equippedItems)
            + resolveMeleeDamageSkillBonus(character, equippedItems, attackTuning, false)
            + character.meleeWeaponDamageBonus
            + character.permanentBonuses.meleeDamage
            + character.magicalBonuses.meleeDamage)
        + meleeElementalDamage.minimum.total();
    const int meleeMaxDamage = std::max(
        1,
        meleeMightBonus
            + resolveMeleeMaxDamageItemBonus(equippedItems)
            + resolveMeleeDamageSkillBonus(character, equippedItems, attackTuning, true)
            + character.meleeWeaponDamageBonus
            + character.permanentBonuses.meleeDamage
            + character.magicalBonuses.meleeDamage)
        + meleeElementalDamage.maximum.total();

    if (equippedItems.pMainHand != nullptr && isWandWeapon(*equippedItems.pMainHand))
    {
        summary.combat.meleeDamageText = Engine::tr("Wand");
    }
    else if (equippedItems.pMainHand != nullptr && isBlasterItem(*equippedItems.pMainHand))
    {
        const std::pair<int, int> damageRange = rulesetRows && rulesetRows->blasterDamage
            ? *rulesetRows->blasterDamage
            : resolveBlasterDamageRange(character, equippedItems.pMainHand, attackTuning);
        summary.combat.meleeDamageText = formatDamageRange(damageRange.first, damageRange.second);
    }
    else if (dragonDamageRange.has_value())
    {
        summary.combat.attack = skillLevel(character, "DragonAbility");
        summary.combat.meleeDamageText = formatDamageRange(dragonDamageRange->first, dragonDamageRange->second);
    }
    else if (rulesetRows)
    {
        summary.combat.meleeDamageText =
            formatDamageRange(rulesetRows->meleeMinimumDamage, rulesetRows->meleeMaximumDamage);
    }
    else
    {
        summary.combat.meleeDamageText = formatDamageRange(meleeMinDamage, meleeMaxDamage);
    }

    summary.combat.shoot = resolveRangedAttack(character, equippedItems);

    const bool bowIsBlasterItem = equippedItems.pBow != nullptr && isBlasterItem(*equippedItems.pBow);

    if (rulesetRows && summary.combat.shoot && !bowIsBlasterItem)
    {
        summary.combat.shoot = rulesetRows->rangedAttack + character.permanentBonuses.rangedAttack
            + character.magicalBonuses.rangedAttack;
    }

    if (dragonDamageRange.has_value())
    {
        summary.combat.shoot = skillLevel(character, "DragonAbility");
        summary.combat.rangedDamageText = formatDamageRange(dragonDamageRange->first, dragonDamageRange->second);
    }
    else if (rulesetRows && isDragon(character))
    {
        summary.combat.shoot = rulesetRows->rangedAttack + character.permanentBonuses.rangedAttack
            + character.magicalBonuses.rangedAttack;
        summary.combat.rangedDamageText =
            formatDamageRange(rulesetRows->rangedMinimumDamage, rulesetRows->rangedMaximumDamage);
    }
    else if (summary.combat.shoot && rulesetRows && !bowIsBlasterItem)
    {
        summary.combat.rangedDamageText =
            formatDamageRange(rulesetRows->rangedMinimumDamage, rulesetRows->rangedMaximumDamage);
    }
    else if (summary.combat.shoot)
    {
        const bool bowIsBlaster =
            equippedItems.pBow != nullptr && isBlasterItem(*equippedItems.pBow);
        const int rangedSkillDamageBonus =
            bowIsBlaster
                ? resolveBlasterDamageSkillBonus(character, attackTuning)
                : resolveRangedDamageSkillBonus(character, equippedItems, attackTuning);
        const int rangedFlatDamageBonus =
            bowIsBlaster
                ? 0
                : character.rangedWeaponDamageBonus
                    + character.permanentBonuses.rangedDamage
                    + character.magicalBonuses.rangedDamage;
        const ElementalDamageRange rangedElementalDamage = bowIsBlaster
            ? ElementalDamageRange{}
            : ItemEnchantRuntime::characterAttackElementalDamageRange(
                  character, CharacterAttackMode::Bow, pItemTable, pSpecialItemEnchantTable);
        const int rangedMinDamage = std::max(
            0,
            equippedMinDamage(equippedItems, BowItemIndex, *equippedItems.pBow)
                + rangedSkillDamageBonus
                + rangedFlatDamageBonus)
            + rangedElementalDamage.minimum.total();
        const int rangedMaxDamage = std::max(
            0,
            equippedMaxDamage(equippedItems, BowItemIndex, *equippedItems.pBow)
                + rangedSkillDamageBonus
                + rangedFlatDamageBonus)
            + rangedElementalDamage.maximum.total();
        summary.combat.rangedDamageText = formatDamageRange(rangedMinDamage, rangedMaxDamage);
    }
    else if (equippedItems.pMainHand != nullptr && isWandWeapon(*equippedItems.pMainHand))
    {
        summary.combat.rangedDamageText = Engine::tr("Wand");
    }
    else
    {
        summary.combat.rangedDamageText = Engine::tr("N/A");
    }

    return summary;
}

CharacterAttackProfile GameMechanics::buildCharacterAttackProfile(
    const Character &character,
    const ItemTable *pItemTable,
    const SpellTable *pSpellTable,
    CharacterAttackTuning attackTuning)
{
    CharacterAttackProfile profile = buildBaseCharacterAttackProfile(character, pItemTable, pSpellTable, attackTuning);

    // Hesper's item effects: per-cent melee damage, and ranged damage with bows, blasters and guns.
    const auto scale = [](int &damage, int percent)
    {
        damage = std::max(0, damage + damage * percent / 100);
    };
    if (character.meleeDamagePercent != 0)
    {
        scale(profile.meleeMinDamage, character.meleeDamagePercent);
        scale(profile.meleeMaxDamage, character.meleeDamagePercent);
    }
    if (character.rangedDamagePercent != 0 && !profile.hasWand && !profile.hasDragonBreath)
    {
        scale(profile.rangedMinDamage, character.rangedDamagePercent);
        scale(profile.rangedMaxDamage, character.rangedDamagePercent);
    }

    // A world's own weapon enchantments (Hesper's): more to shields (with the rest at most +100 %) and to bodies
    // without one, the overload chance, and the added Energy damage on the weapon's range.
    const auto applyWorldEnchant = [](const WorldEnchantEffect &effect, ShieldHitModifiers &modifiers, int &minimum,
                                       int &maximum)
    {
        modifiers.shieldDamageMultiplier =
            std::min(2.0f, modifiers.shieldDamageMultiplier + float(effect.shieldDamagePercent) / 100.0f);
        modifiers.exposedMultiplier *= 1.0f + float(effect.exposedDamagePercent) / 100.0f;
        minimum += effect.energyDamageMinimum;
        maximum += effect.energyDamageMaximum;
    };
    applyWorldEnchant(character.meleeWeaponEnchant, profile.meleeShieldModifiers, profile.meleeMinDamage,
        profile.meleeMaxDamage);
    profile.meleeShieldOverloadChance = float(character.meleeWeaponEnchant.overloadChancePercent) / 100.0f;

    if (profile.hasBow || profile.hasBlaster)
    {
        applyWorldEnchant(character.rangedWeaponEnchant, profile.rangedShieldModifiers, profile.rangedMinDamage,
            profile.rangedMaxDamage);
    }

    return profile;
}

ShieldHitModifiers GameMechanics::spellShieldModifiers(const Character &character)
{
    ShieldHitModifiers modifiers;
    modifiers.energyShare = float(equippedFlagPercent(character, "Resonator")) / 100.0f;
    return modifiers;
}

CharacterAttackProfile GameMechanics::buildBaseCharacterAttackProfile(
    const Character &character,
    const ItemTable *pItemTable,
    const SpellTable *pSpellTable,
    CharacterAttackTuning attackTuning)
{
    CharacterAttackProfile profile = {};
    const EquippedItems equippedItems = resolveEquippedItems(character, pItemTable);
    const CharacterSheetSummary summary = buildCharacterSheetSummary(
        character,
        pItemTable,
        nullptr,
        nullptr,
        attackTuning);

    profile.canMelee = !character.physicalAttackDisabled;
    profile.hasBow =
        !character.physicalAttackDisabled && equippedItems.pBow != nullptr && isRangedWeapon(*equippedItems.pBow);
    profile.hasWand = equippedItems.pMainHand != nullptr && isWandWeapon(*equippedItems.pMainHand);
    const bool mainHandIsBlaster = equippedItems.pMainHand != nullptr && isBlasterItem(*equippedItems.pMainHand);
    const bool bowIsBlaster = equippedItems.pBow != nullptr && isBlasterItem(*equippedItems.pBow);
    profile.hasBlaster =
        !character.physicalAttackDisabled && (mainHandIsBlaster || bowIsBlaster);
    const CharacterSkill *pDragonAbility = character.findSkill("DragonAbility");
    profile.hasDragonBreath =
        !character.physicalAttackDisabled
        && isDragon(character)
        && pDragonAbility != nullptr
        && pDragonAbility->level > 0
        && pDragonAbility->mastery != SkillMastery::None;

    // MAW's Bow preference off (disableBow): no arrow leaves the bow and no dragon breathes, so the attack is the melee
    // one at its pace. Wands and blasters still fire.
    if (boundGameRules().combat.bowDisabled())
    {
        profile.hasBow = false;
        profile.hasDragonBreath = false;
    }
    profile.canShoot = profile.hasBow || profile.hasWand || profile.hasBlaster || profile.hasDragonBreath;
    profile.meleeAttackBonus = summary.combat.attack;
    const std::string meleeSkillName = canonicalSkillName(
        equippedItems.pMainHand != nullptr ? equippedItems.pMainHand->skillGroup : std::string("Unarmed"));
    profile.meleeSkillLevel = static_cast<uint32_t>(std::max(0, skillLevel(character, meleeSkillName)));
    profile.meleeSkillMastery = static_cast<uint32_t>(skillMastery(character, meleeSkillName));
    const bool energyBlade =
        equippedItems.pMainHand != nullptr && equippedItems.pMainHand->hasContentFlag(EnergyBladeContentFlag);
    profile.meleeShieldTier = energyBlade ? ShieldAttackTier::KreeganEnergy : ShieldAttackTier::Physical;
    profile.meleeShieldOverload = energyBlade && skillMastery(character, "EnergyBlades") == SkillMastery::Grandmaster;
    // The Arc Coupler: a share of an ordinary weapon's hit strikes raised shields as Kreegan energy.
    const float couplerShare = float(equippedFlagPercent(character, "Coupler")) / 100.0f;
    const int meleeModPercent = workshopModShieldPercent(character.equipmentRuntime.mainHand, pItemTable);
    if (!energyBlade)
    {
        profile.meleeShieldModifiers.energyShare = couplerShare;
        profile.meleeShieldModifiers.shieldDamageMultiplier = 1.0f + float(std::min(meleeModPercent, 100)) / 100.0f;
    }
    if (energyBlade)
    {
        // Expert: +25 % to shields; Master: shield cleave.
        const SkillMastery bladesMastery = skillMastery(character, "EnergyBlades");
        profile.meleeShieldModifiers.shieldDamageMultiplier =
            techWeaponShieldDamageMultiplier(*equippedItems.pMainHand, bladesMastery, meleeModPercent);
        profile.meleeShieldModifiers.cleave = bladesMastery >= SkillMastery::Master;
    }
    CharacterAttackMode rangedRecoveryMode = CharacterAttackMode::Bow;

    if (profile.hasDragonBreath)
    {
        rangedRecoveryMode = CharacterAttackMode::DragonBreath;
    }
    else if (profile.hasBlaster)
    {
        rangedRecoveryMode = CharacterAttackMode::Blaster;
    }
    else if (profile.hasWand)
    {
        rangedRecoveryMode = CharacterAttackMode::Wand;
    }

    profile.meleeRecoverySeconds = resolveAttackRecoverySeconds(
        character,
        equippedItems,
        pSpellTable,
        CharacterAttackMode::Melee,
        attackTuning);
    profile.rangedRecoverySeconds = resolveAttackRecoverySeconds(
        character,
        equippedItems,
        pSpellTable,
        rangedRecoveryMode,
        attackTuning);

    const int actualMight = static_cast<int>(character.might)
        + character.permanentBonuses.might
        + character.magicalBonuses.might;
    const int meleeMightBonus = parameterBonus(actualMight);
    const std::optional<CharacterCombatRows> rulesetRows = boundGameRules().skills.combatRows(
        character,
        pItemTable,
        CharacterStatValues{summary.might.actual, summary.accuracy.actual, summary.luck.actual});
    profile.meleeMinDamage = std::max(
        1,
        meleeMightBonus
            + resolveMeleeMinDamageItemBonus(equippedItems)
            + resolveMeleeDamageSkillBonus(character, equippedItems, attackTuning, false)
            + character.meleeWeaponDamageBonus
            + character.permanentBonuses.meleeDamage
            + character.magicalBonuses.meleeDamage);
    profile.meleeMaxDamage = std::max(
        1,
        meleeMightBonus
            + resolveMeleeMaxDamageItemBonus(equippedItems)
            + resolveMeleeDamageSkillBonus(character, equippedItems, attackTuning, true)
            + character.meleeWeaponDamageBonus
            + character.permanentBonuses.meleeDamage
            + character.magicalBonuses.meleeDamage);

    if (rulesetRows)
    {
        profile.meleeMinDamage = rulesetRows->meleeMinimumDamage;
        profile.meleeMaxDamage = rulesetRows->meleeMaximumDamage;
    }

    if (profile.hasDragonBreath || profile.hasWand)
    {
        profile.rangedShieldTier = ShieldAttackTier::Spell;
    }
    else if (profile.hasBlaster)
    {
        const ItemDefinition *pBlasterItem = mainHandIsBlaster ? equippedItems.pMainHand : equippedItems.pBow;
        profile.rangedShieldTier = pBlasterItem != nullptr && isEnergyGunItem(*pBlasterItem)
            ? ShieldAttackTier::KreeganEnergy : ShieldAttackTier::ClassicBlaster;

        const int rangedModPercent = workshopModShieldPercent(
            mainHandIsBlaster ? character.equipmentRuntime.mainHand : character.equipmentRuntime.bow, pItemTable);
        if (pBlasterItem == nullptr || !isEnergyGunItem(*pBlasterItem))
        {
            profile.rangedShieldModifiers.energyShare = float(equippedFlagPercent(character, "Coupler")) / 100.0f;
            profile.rangedShieldModifiers.shieldDamageMultiplier =
                1.0f + float(std::min(rangedModPercent, 100)) / 100.0f;
        }
        if (pBlasterItem != nullptr && isEnergyGunItem(*pBlasterItem))
        {
            // Expert: +25 % to shields; Master: +20 % on exposed bodies; Grandmaster: homing shots (not a scatter gun).
            const SkillMastery gunsMastery = skillMastery(character, "EnergyGuns");
            profile.rangedShieldModifiers.shieldDamageMultiplier =
                techWeaponShieldDamageMultiplier(*pBlasterItem, gunsMastery, rangedModPercent);
            profile.rangedShieldModifiers.exposedMultiplier = gunsMastery >= SkillMastery::Master ? 1.2f : 1.0f;
            profile.rangedHoming = gunsMastery >= SkillMastery::Grandmaster
                && std::none_of(pBlasterItem->contentFlags.begin(), pBlasterItem->contentFlags.end(),
                    [](const std::string &flag) { return flag.rfind("Scatter", 0) == 0; });
        }
    }

    if (profile.hasDragonBreath && pDragonAbility != nullptr)
    {
        const int dragonSkillLevel = skillLevel(character, "DragonAbility");
        const std::optional<std::pair<int, int>> dragonDamageRange = rulesetRows
            ? std::optional<std::pair<int, int>>({rulesetRows->rangedMinimumDamage, rulesetRows->rangedMaximumDamage})
            : dragonBasicAttackDamageRange(character);
        profile.rangedAttackBonus = rulesetRows ? rulesetRows->rangedAttack : dragonSkillLevel;
        profile.rangedSkillLevel = static_cast<uint32_t>(std::max(0, dragonSkillLevel));
        profile.rangedSkillMastery = static_cast<uint32_t>(pDragonAbility->mastery);
        profile.rangedMinDamage = dragonDamageRange ? dragonDamageRange->first : std::max(1, dragonSkillLevel);
        profile.rangedMaxDamage = dragonDamageRange ? dragonDamageRange->second : profile.rangedMinDamage;
        profile.rangedSpellId = spellIdValue(SpellId::FireBolt);
    }
    else if (profile.hasWand)
    {
        profile.rangedAttackBonus = summary.combat.attack;
        profile.rangedSkillLevel = WandAttackSkillLevel;
        profile.rangedSkillMastery = static_cast<uint32_t>(SkillMastery::Normal);
        profile.rangedMinDamage = profile.meleeMinDamage;
        profile.rangedMaxDamage = profile.meleeMaxDamage;

        if (equippedItems.pMainHand != nullptr)
        {
            int spellId = 0;

            if (tryParseSpellIdToken(equippedItems.pMainHand->mod1, spellId))
            {
                profile.wandSpellId = spellId;
                profile.rangedSpellId = spellId;
            }
        }
    }
    else if (profile.hasBlaster)
    {
        const ItemDefinition *pBlasterItem = mainHandIsBlaster ? equippedItems.pMainHand : equippedItems.pBow;
        profile.rangedAttackBonus = mainHandIsBlaster ? summary.combat.attack : summary.combat.shoot;
        const std::string rangedSkillName =
            canonicalSkillName(pBlasterItem != nullptr ? pBlasterItem->skillGroup : std::string());
        profile.rangedSkillLevel = static_cast<uint32_t>(std::max(0, skillLevel(character, rangedSkillName)));
        profile.rangedSkillMastery = static_cast<uint32_t>(skillMastery(character, rangedSkillName));
        const std::pair<int, int> damageRange = rulesetRows && rulesetRows->blasterDamage
            ? *rulesetRows->blasterDamage
            : resolveBlasterDamageRange(character, pBlasterItem, attackTuning);
        profile.rangedMinDamage = damageRange.first;
        profile.rangedMaxDamage = damageRange.second;

        if (pBlasterItem != nullptr && pBlasterItem->hasContentFlag(ScatterBlasterContentFlag))
        {
            profile.rangedProjectileCount = ScatterBlasterProjectileCount;
            profile.rangedSpreadArcRadians = ScatterBlasterSpreadArcRadians;
        }
    }
    else if (summary.combat.shoot.has_value())
    {
        profile.rangedShieldModifiers.energyShare = float(equippedFlagPercent(character, "Coupler")) / 100.0f;
        profile.rangedAttackBonus = summary.combat.shoot;
        const std::string rangedSkillName = canonicalSkillName(
            equippedItems.pBow != nullptr ? equippedItems.pBow->skillGroup : std::string());
        profile.rangedSkillLevel = static_cast<uint32_t>(std::max(0, skillLevel(character, rangedSkillName)));
        profile.rangedSkillMastery = static_cast<uint32_t>(skillMastery(character, rangedSkillName));
        profile.rangedProjectileCount = rangedSkillName == "Bow"
                && skillMastery(character, rangedSkillName) >= SkillMastery::Master
            ? 2
            : rangedSkillName == "Throwing"
                    && skillMastery(character, rangedSkillName) >= SkillMastery::Grandmaster
                    && equippedItems.pBow != nullptr
                    && equippedItems.pBow->hasContentFlag("ExtraProjectileAtGrandmaster")
                ? 2
                : 1;
        if (character.equippedItemEffectFlags.contains("TripleProjectile"))
        {
            profile.rangedProjectileCount = std::max<uint8_t>(profile.rangedProjectileCount, 3);
        }
        if (rulesetRows)
        {
            profile.rangedMinDamage = rulesetRows->rangedMinimumDamage;
            profile.rangedMaxDamage = rulesetRows->rangedMaximumDamage;
            return profile;
        }
        profile.rangedMinDamage = std::max(
            0,
            resolveRangedDamageSkillBonus(character, equippedItems, attackTuning)
                + (equippedItems.pBow != nullptr
                    ? equippedMinDamage(equippedItems, BowItemIndex, *equippedItems.pBow)
                    : 0)
                + character.rangedWeaponDamageBonus
                + character.permanentBonuses.rangedDamage
                + character.magicalBonuses.rangedDamage);
        profile.rangedMaxDamage = std::max(
            profile.rangedMinDamage,
            resolveRangedDamageSkillBonus(character, equippedItems, attackTuning)
                + (equippedItems.pBow != nullptr
                    ? equippedMaxDamage(equippedItems, BowItemIndex, *equippedItems.pBow)
                    : 0)
                + character.rangedWeaponDamageBonus
                + character.permanentBonuses.rangedDamage
                + character.magicalBonuses.rangedDamage);
    }
    return profile;
}

CharacterAttackResult GameMechanics::resolveCharacterAttackAgainstArmorClass(
    const Character &character,
    const ItemTable *pItemTable,
    const SpellTable *pSpellTable,
    int targetArmorClass,
    float targetDistance,
    std::mt19937 &rng,
    CharacterAttackTuning attackTuning)
{
    CharacterAttackResult result = {};
    const EquippedItems equippedItems = resolveEquippedItems(character, pItemTable);
    const CharacterAttackProfile profile = buildCharacterAttackProfile(
        character,
        pItemTable,
        pSpellTable,
        attackTuning);
    const bool inMeleeRange = targetDistance <= OeCharacterMeleeAttackDistance;
    const bool inRangedRange = targetDistance <= OeCharacterRangedAttackDistance;
    result.targetArmorClass = std::max(0, targetArmorClass);
    result.targetDistance = std::max(0.0f, targetDistance);

    // A dragon bites a target in melee range and breathes at anything further; a blaster or wand fires at any range.
    if (profile.hasDragonBreath && profile.rangedAttackBonus.has_value() && !inMeleeRange)
    {
        result.mode = CharacterAttackMode::DragonBreath;
    }
    else if (profile.hasBlaster && profile.rangedAttackBonus.has_value())
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
        result.projectileCount = profile.rangedProjectileCount;
        result.spellId = profile.rangedSpellId;
        result.attackSoundHook = "wand_cast";

        if (result.mode == CharacterAttackMode::Bow)
        {
            result.attackSoundHook = "bow_shot";
        }
        else if (result.mode == CharacterAttackMode::Blaster)
        {
            result.attackSoundHook = "blaster_shot";
        }
    }

    result.voiceHook = "attack";
    result.shieldTier = result.mode == CharacterAttackMode::Melee ? profile.meleeShieldTier : profile.rangedShieldTier;
    result.shieldOverload = result.mode == CharacterAttackMode::Melee && profile.meleeShieldOverload;
    result.shieldOverloadChance =
        result.mode == CharacterAttackMode::Melee ? profile.meleeShieldOverloadChance : 0.0f;
    result.shieldModifiers =
        result.mode == CharacterAttackMode::Melee ? profile.meleeShieldModifiers : profile.rangedShieldModifiers;
    result.homing = result.mode == CharacterAttackMode::Blaster && profile.rangedHoming;

    if (!result.canAttack)
    {
        return result;
    }

    int effectiveTargetArmorClass = result.targetArmorClass;

    if (character.equippedItemEffectFlags.contains("HalveTargetArmor"))
    {
        effectiveTargetArmorClass /= 2;
    }
    else if (character.equippedItemEffectFlags.contains("BypassArmorChance20") && percentRoll(rng, 20))
    {
        effectiveTargetArmorClass = 0;
    }

    if (result.mode == CharacterAttackMode::DragonBreath
        || character.equippedItemEffectFlags.contains("PerfectAccuracy"))
    {
        result.hit = true;
        if (result.mode == CharacterAttackMode::DragonBreath)
        {
            result.damageType = CombatDamageType::Irresistible;
        }
    }
    else if (result.mode == CharacterAttackMode::Blaster)
    {
        result.damageType = CombatDamageType::Irresistible;
        result.hit = characterRangedAttackHitsArmorClass(
            effectiveTargetArmorClass,
            result.attackBonus,
            targetDistance,
            rng);
    }
    else if (result.mode != CharacterAttackMode::Melee)
    {
        result.hit = characterRangedAttackHitsArmorClass(
            effectiveTargetArmorClass,
            result.attackBonus,
            targetDistance,
            rng);

        if (result.mode == CharacterAttackMode::Wand)
        {
            result.damageType = spellCombatDamageType(result.spellId, pSpellTable);
        }
    }
    else
    {
        result.damageType = CombatDamageType::Physical;
        result.hit = characterAttackHitsArmorClass(effectiveTargetArmorClass, result.attackBonus, 0, 0, rng);

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

    if (result.hit && character.equippedItemEffectFlags.contains("KillOnHit10") && percentRoll(rng, 10))
    {
        result.damage = std::numeric_limits<int>::max() / 4;
        result.damageType = CombatDamageType::Irresistible;
    }

    if (result.hit && character.equippedItemEffectFlags.contains("StunOnHit5") && percentRoll(rng, 5))
    {
        result.stunTarget = true;
    }

    if (result.hit && character.equippedItemEffectFlags.contains("FearOnHit10") && percentRoll(rng, 10))
    {
        result.fearTarget = true;
    }

    if (result.hit
        && character.equippedItemEffectFlags.contains("EnrageOnHit5Grandmaster")
        && result.skillMastery >= static_cast<uint32_t>(SkillMastery::Grandmaster)
        && percentRoll(rng, 5))
    {
        result.enrageTarget = true;
    }

    if (result.hit && character.equippedItemEffectFlags.contains("ReelOnHit"))
    {
        result.stunTarget = true;
    }

    if (result.hit
        && character.equippedItemEffectFlags.contains("PoisonOnHit40Grandmaster")
        && result.skillMastery >= static_cast<uint32_t>(SkillMastery::Grandmaster)
        && percentRoll(rng, 40))
    {
        result.damageType = CombatDamageType::Body;
    }

    if (hasCondition(character, CharacterCondition::Weak))
    {
        result.damage /= 2;
    }

    if (result.mode == CharacterAttackMode::Melee)
    {
        result.skillLevel = profile.meleeSkillLevel;
        result.skillMastery = profile.meleeSkillMastery;
        applyMeleeWeaponEffects(character, equippedItems, result, rng);
    }

    if (result.mode == CharacterAttackMode::Bow && character.equippedItemEffectFlags.contains("ExplosiveArrows"))
    {
        result.explosiveArrow = true;
        result.damageType = CombatDamageType::Fire;
    }

    if (!result.resolvesOnImpact)
    {
        result.damageSoundHook = "target_hit";
    }

    return result;
}

SoundId GameMechanics::resolveCharacterAttackSoundId(
    const Character &character,
    const ItemTable *pItemTable,
    CharacterAttackMode attackMode)
{
    if (attackMode == CharacterAttackMode::Bow)
    {
        return SoundId::ShootBow;
    }

    if (attackMode == CharacterAttackMode::Blaster)
    {
        return SoundId::ShootBlaster;
    }

    if (attackMode == CharacterAttackMode::DragonBreath)
    {
        return SoundId::DragonBreath;
    }

    if (attackMode != CharacterAttackMode::Melee || pItemTable == nullptr)
    {
        return SoundId::SwingBlunt01;
    }

    const uint32_t itemId = character.equipment.mainHand;

    if (itemId == 0)
    {
        return SoundId::SwingBlunt01;
    }

    const ItemDefinition *pItemDefinition = pItemTable->get(itemId);

    if (pItemDefinition == nullptr)
    {
        return SoundId::SwingBlunt01;
    }

    if (pItemDefinition->skillGroup == "Sword")
    {
        return SoundId::SwingSword01;
    }

    if (pItemDefinition->skillGroup == "Dagger")
    {
        return SoundId::SwingSword02;
    }

    if (pItemDefinition->skillGroup == "Axe")
    {
        return SoundId::SwingAxe01;
    }

    if (pItemDefinition->skillGroup == "Spear")
    {
        return SoundId::SwingAxe03;
    }

    if (pItemDefinition->skillGroup == "Mace")
    {
        return SoundId::SwingBlunt03;
    }

    return SoundId::SwingBlunt01;
}

float GameMechanics::actorTargetHeight(uint16_t actorHeight)
{
    // A fixed minimum can put the aim point above a short creature's collision volume.
    return actorHeight * 0.6f;
}

bool GameMechanics::actorBoxInViewport(
    const float viewProjection[16], float x, float y, float footZ, float radius, float height)
{
    // The screen rectangle of the box's corners in front of the camera, against the viewport.
    float minX = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float minY = std::numeric_limits<float>::max();
    float maxY = std::numeric_limits<float>::lowest();
    bool anyInFront = false;

    for (int corner = 0; corner < 8; ++corner)
    {
        const bx::Vec3 point = {
            x + ((corner & 1) != 0 ? radius : -radius),
            y + ((corner & 2) != 0 ? radius : -radius),
            footZ + ((corner & 4) != 0 ? height : 0.0f)};
        const bx::Vec3 projected = bx::mulH(point, viewProjection);

        if (projected.z < 0.0f || projected.z > 1.0f)
        {
            continue;
        }

        anyInFront = true;
        minX = std::min(minX, projected.x);
        maxX = std::max(maxX, projected.x);
        minY = std::min(minY, projected.y);
        maxY = std::max(maxY, projected.y);
    }

    return anyInFront && minX <= 1.0f && maxX >= -1.0f && minY <= 1.0f && maxY >= -1.0f;
}

float GameMechanics::projectileFanYawOffsetRadians(
    uint32_t projectileCount,
    uint32_t projectileIndex,
    float arcRadians)
{
    if (projectileCount <= 1)
    {
        return 0.0f;
    }

    return -arcRadians * 0.5f + arcRadians * float(projectileIndex) / float(projectileCount - 1);
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

bool GameMechanics::monsterAttackHitsArmorClass(
    int targetArmorClass,
    int monsterLevel,
    int attackBonus,
    std::mt19937 &rng)
{
    const int armorClass = std::max(0, targetArmorClass);
    const int level = std::max(0, monsterLevel);
    const int bonus = std::max(0, attackBonus);
    const int rollUpperBound = std::max(1, armorClass + 2 * level + 10);
    const int hitRoll = std::uniform_int_distribution<int>(1, rollUpperBound)(rng);
    return hitRoll + bonus > armorClass + 5;
}

int GameMechanics::rollMonsterAttackDamage(int diceRolls, int diceSides, int damageBonus, std::mt19937 &rng)
{
    int damage = damageBonus;

    if (diceRolls <= 0 || diceSides <= 0)
    {
        return damage;
    }

    std::uniform_int_distribution<int> distribution(1, diceSides);

    for (int rollIndex = 0; rollIndex < diceRolls; ++rollIndex)
    {
        damage += distribution(rng);
    }

    return damage;
}

int GameMechanics::resolveShieldedPhysicalProjectileDamage(int damage)
{
    return damage / 2;
}

IdentifyMonsterReveal GameMechanics::resolveIdentifyMonsterReveal(
    int identifySkillLevel,
    SkillMastery mastery,
    int monsterLevel)
{
    IdentifyMonsterReveal reveal = {};

    if (identifySkillLevel <= 0 || mastery == SkillMastery::None)
    {
        return reveal;
    }

    reveal.hasSkill = true;

    // A mastery reveals its own sections and every lower one, but only if the monster is not too strong for it;
    // a failed check reveals nothing (it does not fall back to a lower mastery).
    switch (mastery)
    {
        case SkillMastery::Normal:
            reveal.hitPointsAndArmorClass = identifySkillLevel + 10 >= monsterLevel;
            break;

        case SkillMastery::Expert:
            reveal.hitPointsAndArmorClass = 2 * identifySkillLevel + 10 >= monsterLevel;
            reveal.attackAndDamage = reveal.hitPointsAndArmorClass;
            break;

        case SkillMastery::Master:
            reveal.hitPointsAndArmorClass = 3 * identifySkillLevel + 10 >= monsterLevel;
            reveal.attackAndDamage = reveal.hitPointsAndArmorClass;
            reveal.spellsAndEffects = reveal.hitPointsAndArmorClass;
            break;

        case SkillMastery::Grandmaster:
            reveal.hitPointsAndArmorClass = true;
            reveal.attackAndDamage = true;
            reveal.spellsAndEffects = true;
            reveal.resistances = true;
            break;

        case SkillMastery::None:
            break;
    }

    return reveal;
}

IdentifyMonsterReveal GameMechanics::resolveIdentifyMonsterReveal(const Character &character, int monsterLevel)
{
    return resolveIdentifyMonsterReveal(
        skillLevel(character, "IdentifyMonster"),
        skillMastery(character, "IdentifyMonster"),
        monsterLevel);
}

SpeechId GameMechanics::resolveIdentifyMonsterSpeech(const Character &character, int monsterLevel)
{
    return resolveIdentifyMonsterSpeech(resolveIdentifyMonsterReveal(character, monsterLevel), character, monsterLevel);
}

SpeechId GameMechanics::resolveIdentifyMonsterSpeech(
    const IdentifyMonsterReveal &reveal,
    const Character &character,
    int monsterLevel)
{
    if (!reveal.hasSkill)
    {
        return SpeechId::None;
    }

    if (!reveal.identified())
    {
        return SpeechId::IdentifyMonsterFail;
    }

    return monsterLevel >= static_cast<int>(character.level) - 5
        ? SpeechId::IdentifyMonsterBig
        : SpeechId::IdentifyMonsterWeak;
}

CombatDamageType GameMechanics::parseCombatDamageType(const std::string &value)
{
    const std::string normalized = normalizedToken(value);

    if (normalized == "fire") return CombatDamageType::Fire;
    if (normalized == "air") return CombatDamageType::Air;
    if (normalized == "water") return CombatDamageType::Water;
    if (normalized == "earth") return CombatDamageType::Earth;
    if (normalized == "spirit") return CombatDamageType::Spirit;
    if (normalized == "mind") return CombatDamageType::Mind;
    if (normalized == "body") return CombatDamageType::Body;
    if (normalized == "light") return CombatDamageType::Light;
    if (normalized == "dark") return CombatDamageType::Dark;
    if (normalized == "ener" || normalized == "energy") return CombatDamageType::Energy;
    if (normalized == "irresistible") return CombatDamageType::Irresistible;
    return CombatDamageType::Physical;
}

CombatDamageType GameMechanics::spellCombatDamageType(uint32_t spellId, const SpellTable *pSpellTable)
{
    if (spellIdFromValue(spellId) == SpellId::DragonBreath)
    {
        return CombatDamageType::Fire;
    }

    const SpellEntry *pSpellEntry =
        pSpellTable != nullptr ? pSpellTable->findById(static_cast<int>(spellId)) : nullptr;

    if (pSpellEntry == nullptr)
    {
        return CombatDamageType::Physical;
    }

    return parseCombatDamageType(pSpellEntry->schoolName);
}

int GameMechanics::resolveCharacterIncomingDamage(
    const Character &character,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    int damage,
    CombatDamageType damageType,
    std::mt19937 &rng)
{
    int resolvedDamage = std::max(0, damage);

    if (resolvedDamage <= 0 || damageType == CombatDamageType::Irresistible)
    {
        return resolvedDamage;
    }

    const CharacterSheetSummary summary = buildCharacterSheetSummary(
        character,
        pItemTable,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable);

    const auto directResistance =
        [&character](int CharacterResistanceSet::*field)
        {
            return character.baseResistances.*field
                + character.permanentBonuses.resistances.*field
                + character.magicalBonuses.resistances.*field;
        };

    const bool directImmunity =
        (damageType == CombatDamageType::Spirit
            && (character.permanentImmunities.spirit || character.magicalImmunities.spirit))
        || (damageType == CombatDamageType::Light
            && (character.permanentImmunities.light || character.magicalImmunities.light))
        || (damageType == CombatDamageType::Dark
            && (character.permanentImmunities.dark || character.magicalImmunities.dark));

    if (resistanceImmuneForDamageType(summary, damageType) || directImmunity)
    {
        return 0;
    }

    int resistance = resistanceValueForDamageType(summary, damageType);

    if (damageType == CombatDamageType::Spirit)
    {
        resistance = directResistance(&CharacterResistanceSet::spirit);
    }
    else if (damageType == CombatDamageType::Light)
    {
        resistance = directResistance(&CharacterResistanceSet::light);
    }
    else if (damageType == CombatDamageType::Dark)
    {
        resistance = directResistance(&CharacterResistanceSet::dark);
    }
    else if (damageType == CombatDamageType::Energy)
    {
        // Hesper gear only (item_effects energy_resistance); 0 for every other character.
        resistance = character.energyResistance;
    }

    const int luckBonus = parameterBonus(static_cast<int>(character.luck)
        + character.permanentBonuses.luck
        + character.magicalBonuses.luck);

    if (resistance + luckBonus > 0)
    {
        const int rollUpperBound = std::max(1, resistance + luckBonus + 30);

        for (int rollIndex = 0; rollIndex < 4; ++rollIndex)
        {
            if (std::uniform_int_distribution<int>(0, rollUpperBound - 1)(rng) < 30)
            {
                break;
            }

            resolvedDamage /= 2;
        }
    }

    if (damageType == CombatDamageType::Physical)
    {
        if (characterWearsArmorSkill(character, pItemTable, "PlateArmor")
            && skillMastery(character, "PlateArmor") >= SkillMastery::Master)
        {
            resolvedDamage /= 2;
        }
        else if (characterWearsArmorSkill(character, pItemTable, "ChainArmor")
            && skillMastery(character, "ChainArmor") >= SkillMastery::Grandmaster)
        {
            resolvedDamage = (resolvedDamage * 2) / 3;
        }
    }

    // Hesper's Damping Weave (item_effects energy_damage_taken_pct).
    if (damageType == CombatDamageType::Energy && character.energyDamageTakenPercent != 0)
    {
        resolvedDamage = resolvedDamage * std::max(0, 100 + character.energyDamageTakenPercent) / 100;
    }

    return std::max(0, resolvedDamage);
}

int GameMechanics::resolveMonsterIncomingDamage(
    int damage,
    CombatDamageType damageType,
    int resistance,
    int hourOfPowerResistanceBonus,
    std::mt19937 &rng)
{
    int resolvedDamage = std::max(0, damage);

    if (resolvedDamage <= 0 || damageType == CombatDamageType::Irresistible)
    {
        return resolvedDamage;
    }

    if (resistance >= 200)
    {
        return 0;
    }

    const int effectiveHourOfPowerBonus =
        monsterHourOfPowerBoostsDamageResistance(damageType) ? std::max(0, hourOfPowerResistanceBonus) : 0;
    const int rollUpperBound = std::max(1, std::max(0, resistance) + effectiveHourOfPowerBonus + 30);

    for (int rollIndex = 0; rollIndex < 4; ++rollIndex)
    {
        if (std::uniform_int_distribution<int>(0, rollUpperBound - 1)(rng) < 30)
        {
            break;
        }

        resolvedDamage /= 2;
    }

    return std::max(0, resolvedDamage);
}

int GameMechanics::resolveMonsterIncomingWeaponDamage(
    int damage,
    CombatDamageType damageType,
    const ElementalDamageBonuses &additionalDamage,
    const MonsterDamageResistances &resistances,
    int hourOfPowerResistanceBonus,
    std::mt19937 &rng)
{
    const auto resistanceForType = [&resistances](CombatDamageType type)
    {
        switch (type)
        {
            case CombatDamageType::Fire: return resistances.fire;
            case CombatDamageType::Air: return resistances.air;
            case CombatDamageType::Water: return resistances.water;
            case CombatDamageType::Earth: return resistances.earth;
            case CombatDamageType::Spirit: return resistances.spirit;
            case CombatDamageType::Mind: return resistances.mind;
            case CombatDamageType::Body: return resistances.body;
            case CombatDamageType::Light: return resistances.light;
            case CombatDamageType::Dark: return resistances.dark;
            case CombatDamageType::Energy:
            case CombatDamageType::Irresistible:
                return 0;
            case CombatDamageType::Physical:
            default:
                return resistances.physical;
        }
    };
    const auto resolveComponent =
        [hourOfPowerResistanceBonus, &resistanceForType, &rng](int componentDamage, CombatDamageType type)
    {
        return resolveMonsterIncomingDamage(
            componentDamage,
            type,
            resistanceForType(type),
            hourOfPowerResistanceBonus,
            rng);
    };

    int resolvedDamage = resolveComponent(
        std::max(0, damage - additionalDamage.total()),
        damageType);
    resolvedDamage += resolveComponent(additionalDamage.fire, CombatDamageType::Fire);
    resolvedDamage += resolveComponent(additionalDamage.air, CombatDamageType::Air);
    resolvedDamage += resolveComponent(additionalDamage.water, CombatDamageType::Water);
    resolvedDamage += resolveComponent(additionalDamage.body, CombatDamageType::Body);
    resolvedDamage += resolveComponent(additionalDamage.light, CombatDamageType::Light);
    resolvedDamage += resolveComponent(additionalDamage.dark, CombatDamageType::Dark);
    return resolvedDamage;
}

std::string GameMechanics::conditionName(CharacterCondition condition)
{
    return conditionNameText(condition);
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

int GameMechanics::resolveCharacterPerceptionValue(const Character &character)
{
    static const std::string PerceptionSkillName = "Perception";

    if (!canAct(character))
    {
        return 0;
    }

    const CharacterSkill *pSkill = character.findSkillByCanonicalName(PerceptionSkillName);

    if (pSkill == nullptr || pSkill->mastery == SkillMastery::None || pSkill->level == 0)
    {
        return 0;
    }

    if (pSkill->mastery == SkillMastery::Grandmaster)
    {
        return 10000;
    }

    return (static_cast<int>(pSkill->level) + character.skillBonus("Perception"))
        * masteryMultiplier(pSkill->mastery, 1, 2, 3, 5);
}

int GameMechanics::resolveCharacterDisarmTrapValue(const Character &character)
{
    static const std::string DisarmTrapSkillName = "DisarmTraps";

    const CharacterSkill *pSkill = character.findSkillByCanonicalName(DisarmTrapSkillName);

    if (pSkill == nullptr || pSkill->mastery == SkillMastery::None || pSkill->level == 0)
    {
        return 0;
    }

    if (pSkill->mastery == SkillMastery::Grandmaster)
    {
        return 10000;
    }

    const int itemBonus = character.skillBonus("DisarmTraps");

    const int effectiveLevel = std::max(0, static_cast<int>(pSkill->level) + itemBonus);
    return effectiveLevel * masteryMultiplier(pSkill->mastery, 1, 2, 3, 5);
}

int GameMechanics::resolvePartyPerceptionValue(const Party &party)
{
    int partyPerception = 0;

    for (const Character &member : party.members())
    {
        partyPerception = std::max(partyPerception, resolveCharacterPerceptionValue(member));
    }

    return partyPerception;
}

bool GameMechanics::partyDetectsSecretFaces(const Party &party, const MapStatsEntry &map)
{
    const int requiredPerception = map.perceptionDifficulty * 2;
    return resolvePartyPerceptionValue(party) >= requiredPerception;
}

float ticksToRecoverySeconds(int ticks)
{
    return std::max(0.0f, static_cast<float>(ticks) / 128.0f * OeRealtimeRecoveryScale);
}

bool GameMechanics::canSelectInGameplay(const Character &character)
{
    return canAct(character);
}

bool GameMechanics::canTakeGameplayAction(const Character &character)
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

    if (!isWetsuitItem(itemDefinition)
        && requiresLearnedSkillToEquip(itemDefinition)
        && !character.hasSkill(itemDefinition.skillGroup))
    {
        return false;
    }

    return ItemRuntime::characterMeetsClassRestriction(character, itemDefinition)
        && ItemRuntime::characterMeetsRaceRestriction(character, itemDefinition);
}

std::optional<std::string> GameMechanics::equipRefusalReason(
    const Character &character,
    const ItemDefinition &itemDefinition,
    const CharacterDollTypeEntry *pCharacterDollType)
{
    if (itemDefinition.equipStat.empty() || itemDefinition.equipStat == "0"
        || canCharacterEquipItem(character, itemDefinition, pCharacterDollType)
        || isRestrictedByDollType(itemDefinition, pCharacterDollType))
    {
        return std::nullopt;
    }

    if (!isWetsuitItem(itemDefinition)
        && requiresLearnedSkillToEquip(itemDefinition)
        && !character.hasSkill(itemDefinition.skillGroup))
    {
        return Engine::tr("Requires the {skill} skill",
            {{"skill", Engine::localize(displaySkillName(itemDefinition.skillGroup), "skill")}});
    }

    const int actualMight = static_cast<int>(character.might)
        + character.permanentBonuses.might + character.magicalBonuses.might;
    const int actualAccuracy = static_cast<int>(character.accuracy)
        + character.permanentBonuses.accuracy + character.magicalBonuses.accuracy;
    const bool lacksMight = itemDefinition.requiredMight > 0 && actualMight < itemDefinition.requiredMight;
    const bool lacksAccuracy =
        itemDefinition.requiredAccuracy > 0 && actualAccuracy < itemDefinition.requiredAccuracy;

    if (ItemRuntime::characterMeetsRaceRestriction(character, itemDefinition))
    {
        if (lacksMight)
        {
            return Engine::tr("Requires {value} Might", {{"value", int64_t(itemDefinition.requiredMight)}});
        }

        if (lacksAccuracy)
        {
            return Engine::tr("Requires {value} Accuracy", {{"value", int64_t(itemDefinition.requiredAccuracy)}});
        }
    }

    return ItemRuntime::wearRequirementText(itemDefinition);
}

int GameMechanics::characterAge(const Character &character)
{
    if (character.birthYear == 0)
    {
        return std::max(0, character.ageModifier);
    }

    return std::max(0, CharacterAgeReferenceYear + int(character.playedYears) - int(character.birthYear)
        + character.ageModifier);
}

bool GameMechanics::hasWetsuitEquipped(const Character &character)
{
    return equippedItemId(character.equipment, EquipmentSlot::Armor) == Mm7WetsuitItemId;
}

bool GameMechanics::isEquipmentAllowedWithWetsuit(
    const Character &character,
    const ItemTable *pItemTable,
    EquipmentSlot targetSlot,
    uint32_t targetItemId,
    std::optional<EquipmentSlot> displacedSlot)
{
    static constexpr std::array<EquipmentSlot, 16> EquipmentSlots = {{
        EquipmentSlot::OffHand,
        EquipmentSlot::MainHand,
        EquipmentSlot::Bow,
        EquipmentSlot::Armor,
        EquipmentSlot::Helm,
        EquipmentSlot::Belt,
        EquipmentSlot::Cloak,
        EquipmentSlot::Gauntlets,
        EquipmentSlot::Boots,
        EquipmentSlot::Amulet,
        EquipmentSlot::Ring1,
        EquipmentSlot::Ring2,
        EquipmentSlot::Ring3,
        EquipmentSlot::Ring4,
        EquipmentSlot::Ring5,
        EquipmentSlot::Ring6,
    }};

    bool hasWetsuit = false;

    for (EquipmentSlot slot : EquipmentSlots)
    {
        uint32_t itemId = equippedItemId(character.equipment, slot);

        if (displacedSlot.has_value() && *displacedSlot == slot)
        {
            itemId = 0;
        }

        if (slot == targetSlot)
        {
            itemId = targetItemId;
        }

        if (itemId == Mm7WetsuitItemId)
        {
            hasWetsuit = true;
            break;
        }
    }

    if (!hasWetsuit)
    {
        return true;
    }

    for (EquipmentSlot slot : EquipmentSlots)
    {
        uint32_t itemId = equippedItemId(character.equipment, slot);

        if (displacedSlot.has_value() && *displacedSlot == slot)
        {
            itemId = 0;
        }

        if (slot == targetSlot)
        {
            itemId = targetItemId;
        }

        if (itemId == 0 || itemId == Mm7WetsuitItemId)
        {
            continue;
        }

        const ItemDefinition *pItemDefinition = pItemTable != nullptr ? pItemTable->get(itemId) : nullptr;
        const bool weaponSlot =
            slot == EquipmentSlot::MainHand || slot == EquipmentSlot::OffHand || slot == EquipmentSlot::Bow;

        if (weaponSlot && pItemDefinition != nullptr && isBlasterItem(*pItemDefinition))
        {
            continue;
        }

        return false;
    }

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
    const ItemRules &itemRules = boundGameRules().items;
    const bool hasTwoHandedMain = pMainHand != nullptr ? itemRules.wield(character, *pMainHand).twoHanded : false;
    const ItemWield wield = itemRules.wield(character, itemDefinition);
    const auto finishPlan =
        [&](const CharacterEquipPlan &candidate) -> std::optional<CharacterEquipPlan>
        {
            if (!isEquipmentAllowedWithWetsuit(
                    character,
                    pItemTable,
                    candidate.targetSlot,
                    itemDefinition.itemId,
                    candidate.displacedSlot))
            {
                return std::nullopt;
            }

            return candidate;
        };

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

            return finishPlan(plan);
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
            return finishPlan(plan);
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
            return finishPlan(plan);
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

        return finishPlan(plan);
    }

    if (itemDefinition.equipStat == "Ring")
    {
        const std::optional<EquipmentSlot> freeRing = firstFreeRingSlot(character);
        plan.targetSlot = freeRing.value_or(EquipmentSlot::Ring1);

        if (!freeRing)
        {
            plan.displacedSlot = EquipmentSlot::Ring1;
        }

        return finishPlan(plan);
    }

    if (itemDefinition.equipStat == "Gauntlets")
    {
        plan.targetSlot = EquipmentSlot::Gauntlets;
        plan.displacedSlot = equippedItemId(character.equipment, EquipmentSlot::Gauntlets) != 0
            ? std::optional<EquipmentSlot>(EquipmentSlot::Gauntlets)
            : std::nullopt;
        return finishPlan(plan);
    }

    if (itemDefinition.equipStat == "Amulet")
    {
        plan.targetSlot = EquipmentSlot::Amulet;
        plan.displacedSlot = equippedItemId(character.equipment, EquipmentSlot::Amulet) != 0
            ? std::optional<EquipmentSlot>(EquipmentSlot::Amulet)
            : std::nullopt;
        return finishPlan(plan);
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

        return finishPlan(plan);
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

        return finishPlan(plan);
    }
    else if (itemDefinition.equipStat == "Weapon2" && wield.twoHanded)
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

        return finishPlan(plan);
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

        return finishPlan(plan);
    }
    else if (itemDefinition.equipStat == "Weapon" || itemDefinition.equipStat == "WeaponW"
        || itemDefinition.equipStat == "Weapon2")
    {
        const bool canUseOffHand = !hasTwoHandedMain && wield.offHand;

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

            return finishPlan(plan);
        }

        plan.targetSlot = EquipmentSlot::MainHand;

        if (hasMainItem)
        {
            plan.displacedSlot = EquipmentSlot::MainHand;
        }

        return finishPlan(plan);
    }

    return std::nullopt;
}
}
