#include "game/gameplay/GameMechanics.h"
#include "game/items/ItemEnchantRuntime.h"

namespace OpenYAMM::Game
{
bool GameMechanics::characterRangedAttackHitsArmorClass(
    int targetArmorClass,
    int attackBonus,
    float targetDistance,
    std::mt19937 &rng)
{
    (void)targetArmorClass;
    (void)attackBonus;
    (void)targetDistance;
    (void)rng;
    return true;
}

int ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
    const Character &character,
    CharacterAttackMode attackMode,
    const ItemTable *pItemTable,
    const SpecialItemEnchantTable *pSpecialTable,
    const std::string &monsterName,
    const std::string &monsterPictureName)
{
    (void)character;
    (void)attackMode;
    (void)pItemTable;
    (void)pSpecialTable;
    (void)monsterName;
    (void)monsterPictureName;
    return 1;
}
}
