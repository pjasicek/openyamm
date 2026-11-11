#include "game/gameplay/ScriptedActorMoves.h"

#include <cmath>
#include <iostream>

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

// It walked its move last step: AI_ScriptedMove's walk or run, not an attack, a status, a scripted hold or a door it
// waits at.
bool walkerWalking(const ActorAiFacts &actor)
{
    return (actor.runtime.motionState == ActorAiMotionState::Wandering
            || actor.runtime.motionState == ActorAiMotionState::Pursuing)
        && actor.runtime.animationState == ActorAiAnimationState::Walking;
}

// Whether a walker that keeps walking has stood on one spot too long: its route replanned in the meantime
// (ActorPathRuntime drops a route held at a corner) got it no farther.
bool walkerGaveUp(EventRuntimeState::ScriptedActorMove &move, const ActorAiFacts &actor, float stepSeconds)
{
    const float x = actor.movement.position.x;
    const float y = actor.movement.position.y;

    if (!move.progressAnchor
        || std::hypot(x - (*move.progressAnchor)[0], y - (*move.progressAnchor)[1]) > ScriptedActorMoveProgressDistance)
    {
        move.progressAnchor = std::array<float, 2>{x, y};
        move.stuckSeconds = 0.0f;
        return false;
    }

    move.stuckSeconds += stepSeconds;
    return move.stuckSeconds >= ScriptedActorMoveGiveUpSeconds;
}

void applyToActors(
    EventRuntimeState &state,
    std::vector<ActorAiFacts> &actors,
    const ActorAiFrameFacts &frame,
    bool active)
{
    for (ActorAiFacts &actor : actors)
    {
        const auto iterator = state.scriptedActorMoves.find(uint32_t(actor.actorIndex));

        if (iterator == state.scriptedActorMoves.end())
        {
            continue;
        }

        EventRuntimeState::ScriptedActorMove &move = iterator->second;

        if (walkerDeadOrDying(actor))
        {
            state.scriptedActorMoves.erase(iterator);
            continue;
        }

        const float distance = std::hypot(
            move.point[0] - actor.movement.position.x, move.point[1] - actor.movement.position.y);
        const float arrivalDistance = float(actor.stats.radius) + ScriptedActorMoveArrivalDistance;

        if (distance <= arrivalDistance)
        {
            if (move.arrivalEventId != 0)
            {
                state.pendingActorArrivals.push_back({uint32_t(actor.actorIndex), move.arrivalEventId});
            }

            state.scriptedActorMoves.erase(iterator);
            continue;
        }

        if (active && frame.turnBased.mode != ActorTurnBasedMode::Hold && walkerWalking(actor)
            && walkerGaveUp(move, actor, frame.fixedStepSeconds))
        {
            std::cerr << "evt.MoveActorTo: actor " << actor.actorIndex << " got no farther than ("
                << actor.movement.position.x << ", " << actor.movement.position.y << ") in "
                << ScriptedActorMoveGiveUpSeconds << " s on its way to (" << move.point[0] << ", " << move.point[1]
                << "): the walk ends there, without its arrival\n";
            state.scriptedActorMoves.erase(iterator);
            continue;
        }

        actor.movement.scriptedMoveTarget = GameplayWorldPoint{move.point[0], move.point[1], move.point[2]};
        actor.movement.scriptedMoveArrivalDistance = arrivalDistance;
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

    applyToActors(state, facts.activeActors, facts, true);
    applyToActors(state, facts.backgroundActors, facts, false);
}
}
