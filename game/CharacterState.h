#pragma once

#include "game/SkillData.h"

#include <bitset>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <unordered_set>

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
};

static constexpr size_t CharacterConditionCount = static_cast<size_t>(CharacterCondition::Count);

struct CharacterResistanceSet
{
    int fire = 0;
    int air = 0;
    int water = 0;
    int earth = 0;
    int mind = 0;
    int body = 0;
    int spirit = 0;
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
};
}
