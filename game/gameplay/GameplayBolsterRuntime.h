#pragma once

#include "game/party/SkillData.h"
#include "game/rules/ActorRulesetFacts.h"
#include "game/tables/MonsterTable.h"

#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
class MergedBolsterMapTable;
class MergedBolsterMonsterTable;
class Party;
struct MapStatsEntry;
struct MonsterEntry;

struct GameplayBolsterRuntimeContext
{
    const MapStatsEntry *pMap = nullptr;
    const MonsterTable *pMonsterTable = nullptr;
    const MergedBolsterMapTable *pBolsterMapTable = nullptr;
    const MergedBolsterMonsterTable *pBolsterMonsterTable = nullptr;
    const Party *pParty = nullptr;
    bool bolsterMonstersEnabled = false;
    // What the ruleset resolved for this actor before: a reload or re-resolve keeps its rolls (bosses).
    const ActorRulesetFacts *pExistingFacts = nullptr;
};

struct GameplayMonsterBolsterResult
{
    bool mapEnabled = false;
    bool statsEnabled = false;
    bool mapAllowsSpells = false;
    bool mapAllowsSummons = false;
    bool monsterAllowsNewRangedAttacks = false;
    bool monsterAllowsNewSpells = false;
    bool monsterAllowsSummons = false;
    bool monsterAllowsReplicate = false;
    bool generatedAttack2 = false;
    bool generatedAttack2IsRanged = false;
    bool copyAttack1DamageToAttack2 = false;
    std::string generatedAttack2MissileType;
    int generatedAttack2Chance = 0;
    uint32_t generatedSpell1Id = 0;
    uint32_t generatedSpell2Id = 0;
    int generatedSpell1UseChance = 0;
    int generatedSpell2UseChance = 0;
    bool immobile = false;
    bool stationarySummonAsSpawnPoint = false;
    uint32_t summonMonsterId = 0;
    int partyLevel = 0;
    int monsterFamilyLevel = 0;
    int bolsterStep = 0;
    float rewardMultiplier = 1.0f;
    int maxHp = 0;
    int armorClass = 0;
    uint16_t moveSpeed = 0;
    // The speed while the monster is not hostile to the party, when the rules give one (MAW: no speed bonus until it
    // fights); 0 for moveSpeed always.
    uint16_t calmMoveSpeed = 0;
    int attack1DamageDiceRolls = 0;
    int attack1DamageDiceSides = 0;
    int attack1DamageBonus = 0;
    int attack2DamageDiceRolls = 0;
    int attack2DamageDiceSides = 0;
    int attack2DamageBonus = 0;
    uint32_t spell1SkillLevel = 0;
    SkillMastery spell1SkillMastery = SkillMastery::None;
    uint32_t spell2SkillLevel = 0;
    SkillMastery spell2SkillMastery = SkillMastery::None;
    // The special attack the rules give the monster instead of its table's (MAW: weak diseases become poisons).
    std::optional<MonsterSpecialAttackKind> specialAttackKind;
    ActorRulesetFacts rulesetFacts;
};

int gameplayBolsterAveragePartyLevel(const Party *pParty);

int gameplayBolsterPlayerArmorClass(
    int armorClass,
    int monsterLevel,
    int playerBaseLevel,
    bool bolsterAffectsArmorClass);

float gameplayBolsterRewardMultiplier(int baseMaxHp, int bolsteredMaxHp, bool statsEnabled = true);

uint32_t gameplayBolsterExperienceReward(int baseExperience, int baseHitPoints, float rewardMultiplier);

MonsterTable::LootPrototype gameplayBolsterLootPrototype(
    const MonsterTable::LootPrototype &loot,
    int baseHitPoints,
    float rewardMultiplier);

GameplayMonsterBolsterResult resolveGameplayMonsterBolster(
    const GameplayBolsterRuntimeContext &context,
    const MonsterTable::MonsterStatsEntry &stats,
    const MonsterEntry *pMonsterEntry);
}
