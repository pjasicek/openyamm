#pragma once

#include "game/tables/MonsterTable.h"

#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
struct EventRuntimeState;
class IGameplayWorldRuntime;
struct MergedContinentSettingEntry;

struct MonsterKillReputationResult
{
    bool applied = false;
    int reputationDelta = 0;
};

enum class ReputationLevel : uint8_t
{
    Saintly,
    Friendly,
    Neutral,
    Unfriendly,
    Notorious,
};

constexpr int MinReputation = -10000;
constexpr int MaxReputation = 10000;

int clampReputation(int value);
bool continentUsesMergedReputation(const MergedContinentSettingEntry *pContinentSetting);
int hiredNpcReputationPenalty(const EventRuntimeState &runtimeState);
int effectivePartyReputation(int storedReputation, const EventRuntimeState *pRuntimeState);
void applyReputationGuardHostility(IGameplayWorldRuntime &worldRuntime, int hostileThreshold = 25);
void addStoredCurrentLocationReputation(IGameplayWorldRuntime &worldRuntime, int delta);
MonsterKillReputationResult applyMonsterKillReputationPenalty(
    IGameplayWorldRuntime &worldRuntime,
    const MonsterTable::MonsterStatsEntry *pStats,
    uint32_t actorGroup);
bool actorSharesCivilianAggression(
    uint32_t leftActorGroup,
    const MonsterTable::MonsterStatsEntry *pLeftStats,
    uint32_t rightActorGroup,
    const MonsterTable::MonsterStatsEntry *pRightStats);
ReputationLevel reputationLevel(int effectiveReputation);
std::string reputationLabel(int effectiveReputation);
}
