#include "game/gameplay/ScriptedActorMoves.h"

#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
bool walkerDeadOrDying(const ActorAiFacts &actor)
{
    return actor.status.dead || actor.stats.currentHp <= 0
        || actor.runtime.motionState == ActorAiMotionState::Dying
        || actor.runtime.motionState == ActorAiMotionState::Dead;
}

void applyToActors(EventRuntimeState &state, std::vector<ActorAiFacts> &actors)
{
    for (ActorAiFacts &actor : actors)
    {
        const auto iterator = state.scriptedActorMoves.find(uint32_t(actor.actorIndex));

        if (iterator == state.scriptedActorMoves.end())
        {
            continue;
        }

        const EventRuntimeState::ScriptedActorMove &move = iterator->second;

        if (walkerDeadOrDying(actor))
        {
            state.scriptedActorMoves.erase(iterator);
            continue;
        }

        const float distance = std::hypot(
            move.point[0] - actor.movement.position.x, move.point[1] - actor.movement.position.y);

        if (distance <= float(actor.stats.radius) + ScriptedActorMoveArrivalDistance)
        {
            if (move.arrivalEventId != 0)
            {
                state.pendingActorArrivals.push_back({uint32_t(actor.actorIndex), move.arrivalEventId});
            }

            state.scriptedActorMoves.erase(iterator);
            continue;
        }

        actor.movement.scriptedMoveTarget = GameplayWorldPoint{move.point[0], move.point[1], move.point[2]};
        actor.movement.scriptedMoveRun = move.run;
    }
}

void applyTargetsToActors(EventRuntimeState &state, std::vector<ActorAiFacts> &actors, bool active)
{
    for (ActorAiFacts &actor : actors)
    {
        const auto iterator = state.scriptedActorTargets.find(uint32_t(actor.actorIndex));

        if (iterator == state.scriptedActorTargets.end())
        {
            continue;
        }

        if (walkerDeadOrDying(actor) || (active && !actor.tactics.mm9Profile))
        {
            state.scriptedActorTargets.erase(iterator);
            continue;
        }

        if (!active)
        {
            continue;
        }

        ActorMm9ScriptFacts &directives = actor.behavior.mm9Script;
        directives.setTarget = true;
        directives.targetKind = iterator->second.actorIndex ? ActorAiTargetKind::Actor : ActorAiTargetKind::Party;
        directives.targetActorIndex =
            iterator->second.actorIndex ? size_t(*iterator->second.actorIndex) : static_cast<size_t>(-1);
        state.scriptedActorTargets.erase(iterator);
    }
}
}

void applyScriptedActorTargets(EventRuntimeState &state, ActorAiFrameFacts &facts)
{
    if (state.scriptedActorTargets.empty())
    {
        return;
    }

    applyTargetsToActors(state, facts.activeActors, true);
    applyTargetsToActors(state, facts.backgroundActors, false);
}

void applyScriptedActorMoves(EventRuntimeState &state, ActorAiFrameFacts &facts)
{
    if (state.scriptedActorMoves.empty())
    {
        return;
    }

    applyToActors(state, facts.activeActors);
    applyToActors(state, facts.backgroundActors);
}
}
