#include "game/gameplay/GameplaySparring.h"

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenRuntime.h"

namespace OpenYAMM::Game
{
namespace
{
const GameplaySparringState *sparringState(const IGameplayWorldRuntime *pWorld)
{
    const EventRuntimeState *pEvents = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
    return pEvents != nullptr && pEvents->sparring ? &*pEvents->sparring : nullptr;
}
}

bool isSparringOpponent(const IGameplayWorldRuntime *pWorld, size_t actorIndex)
{
    const GameplaySparringState *pMatch = sparringState(pWorld);
    if (pMatch == nullptr || pMatch->actorIndex != actorIndex)
    {
        return false;
    }

    GameplayRuntimeActorState actor;
    return pWorld->actorRuntimeState(actorIndex, actor) && actor.actorId == pMatch->actorId;
}

bool isSparringSource(const IGameplayWorldRuntime *pWorld, uint32_t actorId)
{
    const GameplaySparringState *pMatch = sparringState(pWorld);
    return pMatch != nullptr && actorId == pMatch->actorId;
}

void scoreSparringHit(IGameplayWorldRuntime &world, GameplayScreenRuntime *pRuntime, bool byParty, int damage)
{
    EventRuntimeState *pEvents = world.eventRuntimeState();
    if (damage <= 0 || pEvents == nullptr || !pEvents->sparring || !pEvents->sparring->active)
    {
        return;
    }

    GameplaySparringState &match = *pEvents->sparring;
    const bool finished = byParty ? ++match.partyScore == match.partyGoal
                                  : ++match.opponentScore == match.opponentGoal;
    if (pRuntime != nullptr)
    {
        pRuntime->setStatusBarEvent(
            "Party " + std::to_string(match.partyScore) + "/" + std::to_string(match.partyGoal)
                + "   " + match.opponentName + " " + std::to_string(match.opponentScore)
                + "/" + std::to_string(match.opponentGoal),
            3.0f,
            GameplayUiController::StatusBarEventPriority::High);
    }
    if (finished)
    {
        // Queued impacts from this opponent still belong to the match, but cannot score again.
        match.active = false;
        size_t previousMessageCount = 0;
        if (world.executeMapEvent(byParty ? match.winEvent : match.lossEvent, previousMessageCount)
            && pRuntime != nullptr)
        {
            pRuntime->ensurePendingEventDialogPresented(true);
        }
    }
}
}
