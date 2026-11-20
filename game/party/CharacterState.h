#pragma once

#include "game/items/ItemRulesetFields.h"
#include "game/tables/ItemTable.h"
#include "game/party/SkillData.h"

#include <array>
#include <bitset>
#include <cstdint>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>

namespace OpenYAMM::Game
{
enum class CharacterCondition : uint8_t
{
    Cursed = 0,
    Weak,
    Asleep,
    Fear,
    Drunk,
    Insane,
    PoisonWeak,
    DiseaseWeak,
    PoisonMedium,
    DiseaseMedium,
    PoisonSevere,
    DiseaseSevere,
    Paralyzed,
    Unconscious,
    Dead,
    Petrified,
    Eradicated,
    Zombie,
    Count,
};

enum class EquipmentSlot : uint8_t
{
    OffHand = 0,
    MainHand,
    Bow,
    Armor,
    Helm,
    Belt,
    Cloak,
    Gauntlets,
    Boots,
    Amulet,
    Ring1,
    Ring2,
    Ring3,
    Ring4,
    Ring5,
    Ring6,
};

static constexpr size_t CharacterConditionCount = static_cast<size_t>(CharacterCondition::Count);

// The conditions' names in data tables (potions.yml, the MM9 hireling table), in enum order.
inline constexpr std::array<std::pair<std::string_view, CharacterCondition>, CharacterConditionCount>
    CharacterConditionNames = {{
        {"Cursed", CharacterCondition::Cursed},
        {"Weak", CharacterCondition::Weak},
        {"Asleep", CharacterCondition::Asleep},
        {"Fear", CharacterCondition::Fear},
        {"Drunk", CharacterCondition::Drunk},
        {"Insane", CharacterCondition::Insane},
        {"PoisonWeak", CharacterCondition::PoisonWeak},
        {"DiseaseWeak", CharacterCondition::DiseaseWeak},
        {"PoisonMedium", CharacterCondition::PoisonMedium},
        {"DiseaseMedium", CharacterCondition::DiseaseMedium},
        {"PoisonSevere", CharacterCondition::PoisonSevere},
        {"DiseaseSevere", CharacterCondition::DiseaseSevere},
        {"Paralyzed", CharacterCondition::Paralyzed},
        {"Unconscious", CharacterCondition::Unconscious},
        {"Dead", CharacterCondition::Dead},
        {"Petrified", CharacterCondition::Petrified},
        {"Eradicated", CharacterCondition::Eradicated},
        {"Zombie", CharacterCondition::Zombie},
    }};

struct CharacterResistanceSet
{
    int fire = 0;
    int air = 0;
    int water = 0;
    int earth = 0;
    int mind = 0;
    int body = 0;
    int spirit = 0;
    int light = 0;
    int dark = 0;
    int physical = 0;
    int magic = 0;
};

struct CharacterResistanceImmunitySet
{
    bool fire = false;
    bool air = false;
    bool water = false;
    bool earth = false;
    bool mind = false;
    bool body = false;
    bool spirit = false;
    bool light = false;
    bool dark = false;
    bool physical = false;
    bool magic = false;
};

struct CharacterStatBonuses
{
    int might = 0;
    int intellect = 0;
    int personality = 0;
    int endurance = 0;
    int speed = 0;
    int accuracy = 0;
    int luck = 0;
    int maxHealth = 0;
    int maxSpellPoints = 0;
    int armorClass = 0;
    int meleeAttack = 0;
    int rangedAttack = 0;
    int meleeDamage = 0;
    int rangedDamage = 0;
    CharacterResistanceSet resistances = {};
};

struct CharacterEquipment
{
    uint32_t offHand = 0;
    uint32_t mainHand = 0;
    uint32_t bow = 0;
    uint32_t armor = 0;
    uint32_t helm = 0;
    uint32_t belt = 0;
    uint32_t cloak = 0;
    uint32_t gauntlets = 0;
    uint32_t boots = 0;
    uint32_t amulet = 0;
    uint32_t ring1 = 0;
    uint32_t ring2 = 0;
    uint32_t ring3 = 0;
    uint32_t ring4 = 0;
    uint32_t ring5 = 0;
    uint32_t ring6 = 0;

    bool operator==(const CharacterEquipment &) const = default;
};

struct EquippedItemRuntimeState
{
    bool identified = true;
    bool broken = false;
    bool stolen = false;
    bool hardened = false;
    uint16_t standardEnchantId = 0;
    uint16_t standardEnchantPower = 0;
    uint16_t specialEnchantId = 0;
    uint16_t artifactId = 0;
    ItemRarity rarity = ItemRarity::Common;
    uint16_t currentCharges = 0;
    uint16_t maxCharges = 0;
    float temporaryBonusRemainingSeconds = 0.0f;
    ItemRulesetFields rulesetFields;
    // The Workshop mod fitted to it (InventoryItem::workshopModId).
    uint16_t workshopModId = 0;

    bool operator==(const EquippedItemRuntimeState &) const = default;
};

struct CharacterEquipmentRuntimeState
{
    EquippedItemRuntimeState offHand = {};
    EquippedItemRuntimeState mainHand = {};
    EquippedItemRuntimeState bow = {};
    EquippedItemRuntimeState armor = {};
    EquippedItemRuntimeState helm = {};
    EquippedItemRuntimeState belt = {};
    EquippedItemRuntimeState cloak = {};
    EquippedItemRuntimeState gauntlets = {};
    EquippedItemRuntimeState boots = {};
    EquippedItemRuntimeState amulet = {};
    EquippedItemRuntimeState ring1 = {};
    EquippedItemRuntimeState ring2 = {};
    EquippedItemRuntimeState ring3 = {};
    EquippedItemRuntimeState ring4 = {};
    EquippedItemRuntimeState ring5 = {};
    EquippedItemRuntimeState ring6 = {};

    bool operator==(const CharacterEquipmentRuntimeState &) const = default;
};
}
