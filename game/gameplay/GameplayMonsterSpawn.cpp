#include "game/gameplay/GameplayMonsterSpawn.h"

#include <cmath>
#include <numbers>

namespace OpenYAMM::Game
{
int16_t gameplaySpawnMonsterId(
    const GameplayMonsterSpawnRequest &request, std::mt19937_64 &rng, const MonsterTable *pMonsterTable)
{
    const int total = request.tierWeights[0] + request.tierWeights[1] + request.tierWeights[2];

    if (total <= 0 || request.monsterId <= 0)
    {
        return request.monsterId;
    }

    int roll = std::uniform_int_distribution<int>(1, total)(rng);
    int tier = 0;

    while (tier < 2 && roll > request.tierWeights[size_t(tier)])
    {
        roll -= request.tierWeights[size_t(tier)];
        ++tier;
    }

    // A world's row (from 1000) goes by its picture's tier letter; a family without that tier keeps the monster.
    constexpr int WorldMonsterRows = 1000;
    const MonsterTable::MonsterStatsEntry *pStats =
        pMonsterTable != nullptr && request.monsterId >= WorldMonsterRows ? pMonsterTable->findStatsById(request.monsterId)
                                                                          : nullptr;

    if (pStats != nullptr)
    {
        const std::string &picture = pStats->pictureName;

        if (picture.size() < 2 || picture[picture.size() - 2] != ' ' || picture.back() < 'A' || picture.back() > 'C')
        {
            return request.monsterId;
        }

        const std::string tierPicture = picture.substr(0, picture.size() - 1) + char('A' + tier);
        const MonsterTable::MonsterStatsEntry *pTier = pMonsterTable->findStatsByPictureName(tierPicture);
        return pTier != nullptr && pTier->pictureName == tierPicture ? int16_t(pTier->id) : request.monsterId;
    }

    // MM6-MM8's monster ids come in families of three: A, B and C.
    const int familyFirst = (request.monsterId - 1) / 3 * 3 + 1;
    return int16_t(familyFirst + tier);
}

std::array<float, 2> gameplaySpawnOffset(const GameplayMonsterSpawnRequest &request, std::mt19937_64 &rng)
{
    if (request.radius <= 1.0f)
    {
        return {request.x, request.y};
    }

    const float angle = std::uniform_real_distribution<float>(0.0f, 2.0f * std::numbers::pi_v<float>)(rng);
    const float distance = std::uniform_real_distribution<float>(1.0f, request.radius)(rng);
    return {request.x + std::cos(angle) * distance, request.y + std::sin(angle) * distance};
}

std::mt19937_64 gameplaySpawnRng(const GameplayMonsterSpawnRequest &request)
{
    std::random_device device;
    return std::mt19937_64(request.seed != 0 ? request.seed : device() ^ (uint64_t(device()) << 32));
}
}
