#include "game/rules/GameRules.h"

#include "game/party/Party.h"

namespace OpenYAMM::Game
{
namespace
{
const GameRules *g_pBoundGameRules = nullptr;
}

const GameRules &standardGameRules()
{
    static const CombatRules Combat;
    static const MonsterRules Monsters;
    static const GameRules Rules{
        standardExperienceRules(),
        Combat,
        Monsters,
        standardItemRules(),
        standardSkillRules(),
        standardSpellRules(),
        standardClassRules(),
        standardPotionRules(),
        standardCraftingRules()};
    return Rules;
}

const GameRules &gameRulesFor(const Party *pParty)
{
    return pParty != nullptr ? pParty->rules() : standardGameRules();
}

const GameRules &boundGameRules()
{
    return g_pBoundGameRules != nullptr ? *g_pBoundGameRules : standardGameRules();
}

void bindGameRules(const GameRules *pRules)
{
    g_pBoundGameRules = pRules;
}
}
