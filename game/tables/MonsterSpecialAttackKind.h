#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
// What a monster's hit may leave on a party member: the monster row's special attack (monster_data), or a spell's
// condition (the spell_conditions modifier, MonsterModifiers.h).
enum class MonsterSpecialAttackKind : uint8_t
{
    None,
    Curse,
    Weak,
    Sleep,
    Fear,
    Drunk,
    Insane,
    PoisonWeak,
    PoisonMedium,
    PoisonSevere,
    DiseaseWeak,
    DiseaseMedium,
    DiseaseSevere,
    Paralyze,
    Unconscious,
    Dead,
    Petrify,
    Eradicate,
    BreakAny,
    BreakArmor,
    BreakWeapon,
    Aging,
    ManaDrain,
};
}
