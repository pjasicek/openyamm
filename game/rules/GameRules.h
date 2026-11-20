#pragma once

#include "game/rules/ClassRules.h"
#include "game/rules/CombatRules.h"
#include "game/rules/CraftingRules.h"
#include "game/rules/ExperienceRules.h"
#include "game/rules/ItemRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/PotionRules.h"
#include "game/rules/SkillRules.h"
#include "game/rules/SpellRules.h"

namespace OpenYAMM::Game
{
class Party;

// The rules of one ruleset, one object per rules area that differs in code (devdocs/maw/HANDOFF.md §3.5); areas that
// only differ in numbers read the ruleset's tables instead. The party carries the active set: Standard until the
// session installs a ruleset's.
struct GameRules
{
    const ExperienceRules &experience;
    const CombatRules &combat;
    const MonsterRules &monsters;
    const ItemRules &items;
    const SkillRules &skills;
    const SpellRules &spells;
    const ClassRules &classes;
    const PotionRules &potions;
    const CraftingRules &crafting;
};

const GameRules &standardGameRules();
// The party's rules; Standard where there is no party (previews and tools).
const GameRules &gameRulesFor(const Party *pParty);
// The rules reads use where no party is at hand (the character sheet, item values and names): the session binds the
// active game's; Standard when nothing is bound.
const GameRules &boundGameRules();
void bindGameRules(const GameRules *pRules);
}
