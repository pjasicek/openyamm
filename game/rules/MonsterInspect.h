#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/tables/MonsterTable.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
struct ActorRulesetFacts;

// What the monster inspect panel asks the rules about the monster under the cursor.
struct MonsterInspectQuery
{
    const MonsterTable::MonsterStatsEntry *pStats = nullptr;
    const ActorRulesetFacts *pFacts = nullptr;
    const Party *pParty = nullptr;
    // The member the damage and experience are for: the selected one.
    size_t viewerIndex = 0;
    // Whether the monster has a second attack (its own or one the rules gave it).
    bool hasAttack2 = false;
    // The monster's first spell when it deals damage (0 otherwise), and the damage's type.
    uint32_t spellId = 0;
    CombatDamageType spellDamageType = CombatDamageType::Physical;
    // The numbers before the viewer's armour and resistances (MAW: while Alt is held).
    bool rawNumbers = false;
    int maxHp = 0;
};

// The rules' own numbers for the panel; the panel keeps its own rows where these are empty.
struct MonsterInspectNumbers
{
    // The monster's level, shown above its armour class.
    int level = 0;
    // What attacks 1 and 2 deal (one row each) and what the spell deals.
    std::vector<std::string> damageRows;
    std::string spellDamage;
    // Lines the Effects box shows before the monster's effects: its special attack, the experience a kill gives the
    // viewer, the rules' stacks on it.
    std::vector<std::string> effectLines;
};
}
