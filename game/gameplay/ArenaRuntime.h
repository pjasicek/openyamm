#pragma once

#include "game/party/Party.h"

#include <cstdint>
#include <optional>
#include <random>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class IGameplayWorldRuntime;
class MergedBolsterMapTable;
class MonsterTable;
struct MapStatsEntry;

constexpr uint32_t ArenaNpcTopicId = 704;
constexpr uint32_t ArenaMonsterGroup = 1;

struct ArenaMonsterSpawn
{
    int16_t monsterId = 0;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct ArenaFightPlan
{
    ArenaDifficulty difficulty = ArenaDifficulty::Invalid;
    int goldReward = 0;
    std::vector<ArenaMonsterSpawn> spawns;
};

bool isArenaDifficulty(ArenaDifficulty difficulty);
const char *arenaDifficultyLabel(ArenaDifficulty difficulty);
uint16_t arenaWinCounterVariable(ArenaDifficulty difficulty);
uint32_t arenaAwardId(ArenaDifficulty difficulty);
int arenaDifficultyIndex(ArenaDifficulty difficulty);
ArenaDifficulty arenaDifficultyFromActionId(uint32_t actionId);

int arenaPartyMaxLevel(const Party &party);
std::vector<int16_t> collectArenaMonsterCandidates(
    const MonsterTable &monsterTable,
    ArenaDifficulty difficulty,
    int partyLevel,
    const std::string &monsterWorldId = {});

std::optional<ArenaFightPlan> buildArenaFightPlan(
    const MonsterTable &monsterTable,
    const Party &party,
    ArenaDifficulty difficulty,
    std::mt19937 &rng,
    const std::string &monsterWorldId = {});

bool arenaFightIsComplete(const IGameplayWorldRuntime &worldRuntime);
bool startArenaFight(
    Party &party,
    IGameplayWorldRuntime &worldRuntime,
    ArenaDifficulty difficulty,
    std::mt19937 &rng);
bool claimArenaReward(Party &party);
}
