#pragma once

#include <cstdint>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class IGameplayWorldRuntime;
class MonsterTable;
class Party;
struct MapStatsEntry;

constexpr uint32_t ArenaTopicId = 704;

enum class ArenaDifficulty : uint32_t
{
    Page = 1,
    Squire,
    Knight,
    Lord,
};

struct ArenaChallenge
{
    uint32_t goldReward = 0;
    std::vector<int16_t> monsterIds;
};

const char *arenaDifficultyName(ArenaDifficulty difficulty);
std::optional<ArenaChallenge> generateArenaChallenge(
    const MonsterTable &monsters, const MapStatsEntry &map,
    const Party &party, ArenaDifficulty difficulty, uint32_t seed);
// Returns true when the conversation should close and the party returns to the combat floor.
bool interactWithArena(IGameplayWorldRuntime &world, uint32_t npcId);
bool startArenaChallenge(
    IGameplayWorldRuntime &world, ArenaDifficulty difficulty, uint32_t seed);
}
