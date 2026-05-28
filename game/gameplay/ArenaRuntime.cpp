#include "game/gameplay/ArenaRuntime.h"

#include "game/events/EvtEnums.h"
#include "game/audio/SoundIds.h"
#include "game/gameplay/GameplayBolsterRuntime.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/tables/MonsterTable.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<ArenaMonsterSpawn, 20> ArenaPlacements = {{
    {0, 1524.0f, 8332.0f, 1.0f},
    {0, 2186.0f, 8844.0f, 1.0f},
    {0, 3219.0f, 9339.0f, 1.0f},
    {0, 4500.0f, 9339.0f, 1.0f},
    {0, 5323.0f, 9004.0f, 1.0f},
    {0, 6013.0f, 8344.0f, 1.0f},
    {0, 1291.0f, 7701.0f, 1.0f},
    {0, 6399.0f, 7701.0f, 1.0f},
    {0, 1291.0f, 3433.0f, 1.0f},
    {0, 6399.0f, 6933.0f, 1.0f},
    {0, 1291.0f, 4129.0f, 1.0f},
    {0, 6399.0f, 6216.0f, 1.0f},
    {0, 1291.0f, 4823.0f, 1.0f},
    {0, 6399.0f, 5539.0f, 1.0f},
    {0, 1291.0f, 5339.0f, 1.0f},
    {0, 6399.0f, 4823.0f, 1.0f},
    {0, 1291.0f, 6216.0f, 1.0f},
    {0, 6399.0f, 4129.0f, 1.0f},
    {0, 1291.0f, 6933.0f, 1.0f},
    {0, 6399.0f, 3433.0f, 1.0f},
}};

int arenaBaseReward(ArenaDifficulty difficulty)
{
    switch (difficulty)
    {
        case ArenaDifficulty::Page: return 50;
        case ArenaDifficulty::Squire: return 100;
        case ArenaDifficulty::Knight: return 200;
        case ArenaDifficulty::Lord: return 500;
        default: return 0;
    }
}

int arenaMonsterCount(ArenaDifficulty difficulty, std::mt19937 &rng)
{
    switch (difficulty)
    {
        case ArenaDifficulty::Page: return std::uniform_int_distribution<int>(6, 8)(rng);
        case ArenaDifficulty::Squire: return std::uniform_int_distribution<int>(6, 12)(rng);
        case ArenaDifficulty::Knight: return std::uniform_int_distribution<int>(10, 20)(rng);
        case ArenaDifficulty::Lord: return 20;
        default: return 0;
    }
}

int arenaMonsterTierKind(int16_t monsterId)
{
    return 3 - (std::max<int16_t>(1, monsterId) % 3);
}

std::pair<int, int> arenaMonsterLevelRange(ArenaDifficulty difficulty, int partyLevel)
{
    const int baseMaximum = std::max(partyLevel, 10);

    switch (difficulty)
    {
        case ArenaDifficulty::Page:
            return {0, baseMaximum};
        case ArenaDifficulty::Squire:
            return {std::min(static_cast<int>(std::ceil(static_cast<double>(partyLevel) / 5.0)), 70), baseMaximum + 5};
        case ArenaDifficulty::Knight:
            return {std::min(static_cast<int>(std::ceil(static_cast<double>(partyLevel) / 3.0)), 70), baseMaximum + 7};
        case ArenaDifficulty::Lord:
            return {std::min(static_cast<int>(std::ceil(static_cast<double>(partyLevel) / 2.0)), 70), baseMaximum + 10};
        default:
            return {0, 0};
    }
}

std::pair<int, int> arenaMonsterKindRange(ArenaDifficulty difficulty)
{
    switch (difficulty)
    {
        case ArenaDifficulty::Page: return {1, 1};
        case ArenaDifficulty::Squire: return {1, 2};
        case ArenaDifficulty::Knight: return {2, 3};
        case ArenaDifficulty::Lord: return {3, 3};
        default: return {0, 0};
    }
}
}

bool isArenaDifficulty(ArenaDifficulty difficulty)
{
    return difficulty >= ArenaDifficulty::Page && difficulty <= ArenaDifficulty::Lord;
}

const char *arenaDifficultyLabel(ArenaDifficulty difficulty)
{
    switch (difficulty)
    {
        case ArenaDifficulty::Page: return "Page";
        case ArenaDifficulty::Squire: return "Squire";
        case ArenaDifficulty::Knight: return "Knight";
        case ArenaDifficulty::Lord: return "Lord";
        default: return "";
    }
}

uint16_t arenaWinCounterVariable(ArenaDifficulty difficulty)
{
    switch (difficulty)
    {
        case ArenaDifficulty::Page: return static_cast<uint16_t>(EvtVariable::ArenaWinsPage);
        case ArenaDifficulty::Squire: return static_cast<uint16_t>(EvtVariable::ArenaWinsSquire);
        case ArenaDifficulty::Knight: return static_cast<uint16_t>(EvtVariable::ArenaWinsKnight);
        case ArenaDifficulty::Lord: return static_cast<uint16_t>(EvtVariable::ArenaWinsLord);
        default: return 0;
    }
}

uint32_t arenaAwardId(ArenaDifficulty difficulty)
{
    switch (difficulty)
    {
        case ArenaDifficulty::Page: return 88;
        case ArenaDifficulty::Squire: return 89;
        case ArenaDifficulty::Knight: return 90;
        case ArenaDifficulty::Lord: return 91;
        default: return 0;
    }
}

int arenaDifficultyIndex(ArenaDifficulty difficulty)
{
    return static_cast<int>(difficulty) - static_cast<int>(ArenaDifficulty::Page);
}

ArenaDifficulty arenaDifficultyFromActionId(uint32_t actionId)
{
    switch (actionId)
    {
        case 0: return ArenaDifficulty::Page;
        case 1: return ArenaDifficulty::Squire;
        case 2: return ArenaDifficulty::Knight;
        case 3: return ArenaDifficulty::Lord;
        default: return ArenaDifficulty::Invalid;
    }
}

int arenaPartyMaxLevel(const Party &party)
{
    int result = 1;

    for (const Character &member : party.members())
    {
        result = std::max(result, static_cast<int>(member.level) + member.levelModifier);
    }

    return std::max(1, result);
}

std::vector<int16_t> collectArenaMonsterCandidates(
    const MonsterTable &monsterTable,
    ArenaDifficulty difficulty,
    int partyLevel,
    const std::string &monsterWorldId)
{
    const std::pair<int, int> levelRange = arenaMonsterLevelRange(difficulty, partyLevel);
    const std::pair<int, int> kindRange = arenaMonsterKindRange(difficulty);
    std::vector<int16_t> monsterIds;

    for (const auto &entryPair : monsterTable.statsEntries())
    {
        const MonsterTable::MonsterStatsEntry &stats = entryPair.second;

        if (stats.id <= 0 || stats.hasKind(MonsterKind::NoArena))
        {
            continue;
        }

        const int kind = arenaMonsterTierKind(static_cast<int16_t>(stats.id));

        if (kind < kindRange.first || kind > kindRange.second)
        {
            continue;
        }

        if (stats.level < levelRange.first || stats.level > levelRange.second)
        {
            continue;
        }

        const int16_t monsterId = static_cast<int16_t>(stats.id);

        if (!mergedMonsterBelongsToWorld(monsterId, monsterWorldId))
        {
            continue;
        }

        monsterIds.push_back(monsterId);
    }

    std::sort(monsterIds.begin(), monsterIds.end());
    return monsterIds;
}

std::optional<ArenaFightPlan> buildArenaFightPlan(
    const MonsterTable &monsterTable,
    const Party &party,
    ArenaDifficulty difficulty,
    std::mt19937 &rng,
    const std::string &monsterWorldId)
{
    if (!isArenaDifficulty(difficulty))
    {
        return std::nullopt;
    }

    const int partyLevel = gameplayBolsterAveragePartyLevel(&party);
    const std::vector<int16_t> candidates =
        collectArenaMonsterCandidates(monsterTable, difficulty, partyLevel, monsterWorldId);

    if (candidates.empty())
    {
        return std::nullopt;
    }

    const int monsterCount = arenaMonsterCount(difficulty, rng);
    const int maxPartyLevel = arenaPartyMaxLevel(party);
    ArenaFightPlan plan = {};
    plan.difficulty = difficulty;
    plan.goldReward = maxPartyLevel * arenaBaseReward(difficulty);
    plan.spawns.reserve(static_cast<size_t>(monsterCount));

    for (int index = 0; index < monsterCount && index < static_cast<int>(ArenaPlacements.size()); ++index)
    {
        ArenaMonsterSpawn spawn = ArenaPlacements[static_cast<size_t>(index)];
        spawn.monsterId = candidates[
            std::uniform_int_distribution<size_t>(0, candidates.size() - 1u)(rng)];
        plan.spawns.push_back(spawn);
    }

    return plan;
}

bool arenaFightIsComplete(const IGameplayWorldRuntime &worldRuntime)
{
    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actor = {};

        if (!worldRuntime.actorRuntimeState(actorIndex, actor) || actor.group != ArenaMonsterGroup)
        {
            continue;
        }

        if (!actor.isDead && !actor.isInvisible)
        {
            return false;
        }
    }

    return true;
}

bool startArenaFight(
    Party &party,
    IGameplayWorldRuntime &worldRuntime,
    ArenaDifficulty difficulty,
    std::mt19937 &rng)
{
    const MonsterTable *pMonsterTable = worldRuntime.monsterTable();

    if (pMonsterTable == nullptr)
    {
        return false;
    }

    const std::optional<ArenaFightPlan> plan =
        buildArenaFightPlan(*pMonsterTable, party, difficulty, rng, worldRuntime.currentMapWorldId());

    if (!plan.has_value())
    {
        return false;
    }

    worldRuntime.teleportPartyTo(3849.0f, 5770.0f, 1.0f, 90);

    uint32_t spawnedCount = 0;

    for (const ArenaMonsterSpawn &spawn : plan->spawns)
    {
        if (worldRuntime.summonArenaMonsterById(spawn.monsterId, spawn.x, spawn.y, spawn.z, ArenaMonsterGroup))
        {
            ++spawnedCount;
        }
    }

    if (spawnedCount == 0)
    {
        return false;
    }

    party.startArenaFight(difficulty, plan->goldReward);
    return true;
}

bool claimArenaReward(Party &party)
{
    const ArenaDifficulty difficulty = party.arenaDifficulty();
    const uint16_t counterVariable = arenaWinCounterVariable(difficulty);
    const uint32_t awardId = arenaAwardId(difficulty);

    if (!isArenaDifficulty(difficulty) || counterVariable == 0 || awardId == 0)
    {
        return false;
    }

    party.setEventVariableValue(counterVariable, party.eventVariableValue(counterVariable) + 1);
    party.addAward(awardId);
    party.addGold(party.arenaGoldReward());
    party.markArenaWon();
    party.requestSound(SoundId::Heroism);
    return true;
}
}
