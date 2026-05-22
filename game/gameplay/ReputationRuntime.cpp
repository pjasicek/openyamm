#include "game/gameplay/ReputationRuntime.h"

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/tables/MergedBaseTables.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t PirateProfessionId = 45;
constexpr uint32_t GypsyProfessionId = 48;
constexpr uint32_t DuperProfessionId = 50;
constexpr uint32_t BurglarProfessionId = 51;
constexpr uint32_t FallenWizardProfessionId = 52;
constexpr uint32_t MMergeGuardGroup38 = 38;
constexpr uint32_t MMergeGuardGroup55 = 55;
constexpr int MMergePeasantKillReputationDelta = 1;
constexpr int MMergeGuardKillReputationDelta = 2;

bool professionHurtsReputation(uint32_t professionId)
{
    switch (professionId)
    {
        case PirateProfessionId:
        case GypsyProfessionId:
        case DuperProfessionId:
        case BurglarProfessionId:
        case FallenWizardProfessionId:
            return true;

        default:
            return false;
    }
}

bool isMMergeGuardGroup(uint32_t actorGroup)
{
    return actorGroup == MMergeGuardGroup38 || actorGroup == MMergeGuardGroup55;
}

bool isCivilianAggressionActor(uint32_t actorGroup, const MonsterTable::MonsterStatsEntry *pStats)
{
    return isMMergeGuardGroup(actorGroup)
        || (pStats != nullptr && pStats->hasKind(MonsterKind::Peasant));
}
}

int clampReputation(int value)
{
    return std::clamp(value, MinReputation, MaxReputation);
}

bool continentUsesMergedReputation(const MergedContinentSettingEntry *pContinentSetting)
{
    return pContinentSetting != nullptr
        && (pContinentSetting->reputationAffectsGuards
            || pContinentSetting->reputationAffectsShops
            || pContinentSetting->reputationAffectsNpc);
}

int hiredNpcReputationPenalty(const EventRuntimeState &runtimeState)
{
    int penalty = 0;

    for (const HiredNpcFollower &follower : runtimeState.hiredNpcFollowers)
    {
        if (professionHurtsReputation(follower.professionId))
        {
            penalty += 5;
        }
    }

    return penalty;
}

int effectivePartyReputation(int storedReputation, const EventRuntimeState *pRuntimeState)
{
    if (pRuntimeState == nullptr)
    {
        return storedReputation;
    }

    return storedReputation + hiredNpcReputationPenalty(*pRuntimeState);
}

void applyReputationGuardHostility(IGameplayWorldRuntime &worldRuntime, int hostileThreshold)
{
    EventRuntimeState *pRuntimeState = worldRuntime.eventRuntimeState();

    if (pRuntimeState == nullptr)
    {
        return;
    }

    const int effectiveReputation =
        effectivePartyReputation(worldRuntime.currentLocationReputation(), pRuntimeState);

    if (effectiveReputation >= hostileThreshold)
    {
        pRuntimeState->actorGroupHostilityRequests[38] = true;
        pRuntimeState->actorGroupHostilityRequests[55] = true;
        worldRuntime.applyEventRuntimeState(true);
    }
    else if (effectiveReputation <= 20)
    {
        pRuntimeState->actorGroupHostilityRequests[38] = false;
        pRuntimeState->actorGroupHostilityRequests[55] = false;
        worldRuntime.applyEventRuntimeState(true);
    }
}

void addStoredCurrentLocationReputation(IGameplayWorldRuntime &worldRuntime, int delta)
{
    if (delta == 0)
    {
        return;
    }

    worldRuntime.setCurrentLocationReputation(clampReputation(worldRuntime.currentLocationReputation() + delta));
    applyReputationGuardHostility(worldRuntime, delta > 0 ? 20 : 25);
}

MonsterKillReputationResult applyMonsterKillReputationPenalty(
    IGameplayWorldRuntime &worldRuntime,
    const MonsterTable::MonsterStatsEntry *pStats,
    uint32_t actorGroup)
{
    MonsterKillReputationResult result = {};

    if (pStats != nullptr && pStats->hasKind(MonsterKind::Peasant))
    {
        result.reputationDelta += MMergePeasantKillReputationDelta;
    }

    if (actorGroup == MMergeGuardGroup38 || actorGroup == MMergeGuardGroup55)
    {
        result.reputationDelta += MMergeGuardKillReputationDelta;
    }

    if (result.reputationDelta == 0)
    {
        return result;
    }

    result.applied = true;
    addStoredCurrentLocationReputation(worldRuntime, result.reputationDelta);

    return result;
}

bool actorSharesCivilianAggression(
    uint32_t leftActorGroup,
    const MonsterTable::MonsterStatsEntry *pLeftStats,
    uint32_t rightActorGroup,
    const MonsterTable::MonsterStatsEntry *pRightStats)
{
    return isCivilianAggressionActor(leftActorGroup, pLeftStats)
        && isCivilianAggressionActor(rightActorGroup, pRightStats);
}

ReputationLevel reputationLevel(int effectiveReputation)
{
    if (effectiveReputation >= 25)
    {
        return ReputationLevel::Notorious;
    }

    if (effectiveReputation >= 6)
    {
        return ReputationLevel::Unfriendly;
    }

    if (effectiveReputation >= -5)
    {
        return ReputationLevel::Neutral;
    }

    if (effectiveReputation >= -24)
    {
        return ReputationLevel::Friendly;
    }

    return ReputationLevel::Saintly;
}

std::string reputationLabel(int effectiveReputation)
{
    switch (reputationLevel(effectiveReputation))
    {
        case ReputationLevel::Saintly:
            return "Saintly";

        case ReputationLevel::Friendly:
            return "Friendly";

        case ReputationLevel::Neutral:
            return "Neutral";

        case ReputationLevel::Unfriendly:
            return "Unfriendly";

        case ReputationLevel::Notorious:
            return "Notorious";
    }

    return "Neutral";
}
}
