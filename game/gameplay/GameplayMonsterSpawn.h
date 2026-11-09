#pragma once

#include "game/tables/MonsterTable.h"
#include "game/tables/Mm9MonsterAi.h"

#include <array>
#include <cstdint>
#include <optional>
#include <random>
#include <vector>

namespace OpenYAMM::Game
{
// A scripted spawn: monsters of one family placed around a point (MAW's pseudoSpawnpoint, its ambushes, arena waves
// and bounties).
struct GameplayMonsterSpawnRequest
{
    // A monster id. With tier weights (A, B, C in percent) each monster takes the tier of the family they pick;
    // without, every monster is this one.
    int16_t monsterId = 0;
    std::array<int, 3> tierWeights = {};
    uint32_t count = 1;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    // Monsters stand at random points within this distance of the centre.
    float radius = 256.0f;
    uint32_t group = 0;
    // A place_mon.txt name (0: the monster's own).
    int32_t uniqueNameIndex = 0;
    bool hostile = true;
    // The rules' numbers: health times this and the level raised by this (MAW); a boss rolls its affix.
    float healthMultiplier = 1.0f;
    int levelBonus = 0;
    bool boss = false;
    // The boss's affix instead of a rolled one (0: rolled).
    uint8_t bossAffix = 0;
    std::optional<uint16_t> moveSpeed;
    uint32_t carriedItemId = 0;
    // A corpse with no gold or random item (MAW's arena).
    bool dropsLoot = true;
    // Seeds the tiers, the positions and a boss's rolls; 0 draws a fresh seed.
    uint64_t seed = 0;
    // The facing of every monster (an AI arena's placement); none keeps the world's default.
    std::optional<float> yawRadians;
    // An MM9 placement for every monster (an AI arena's mm9_ai, a death spawn's ScriptParams 1, a script's summon:
    // its wander path, its spawn-in).
    std::optional<Mm9AiPlacementRecord> mm9Ai;
    // Waypoints every monster walks in turn while it has nothing to fight (a scene actor's patrol).
    std::vector<std::array<int32_t, 3>> patrolPoints;
};

// The monster id of one spawned monster: the family's A, B or C as the weights pick, or the request's own id.
// The monster a spawn makes: the request's own, or with tier weights a tier of its family drawn. MM6-MM8's rows come in
// families of three by id (A at id % 3 == 1); a world's rows (MM9's 9000+) by their picture's tier letter ("MM9 Guard
// A"), where they may lie apart. Without a monster table the id triples are used.
int16_t gameplaySpawnMonsterId(
    const GameplayMonsterSpawnRequest &request, std::mt19937_64 &rng, const MonsterTable *pMonsterTable = nullptr);
// A random point within the request's radius of its centre.
std::array<float, 2> gameplaySpawnOffset(const GameplayMonsterSpawnRequest &request, std::mt19937_64 &rng);
std::mt19937_64 gameplaySpawnRng(const GameplayMonsterSpawnRequest &request);
}
