#pragma once

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayActorAiTypes.h"

namespace OpenYAMM::Game
{
// How close an evt.MoveActorTo walker's edge comes to its point (level) to arrive.
inline constexpr float ScriptedActorMoveArrivalDistance = 32.0f;
// A walker that walks this long without getting this far from one spot gives up: its move ends without its arrival.
inline constexpr float ScriptedActorMoveGiveUpSeconds = 10.0f;
inline constexpr float ScriptedActorMoveProgressDistance = 32.0f;

// evt.MoveActorTo for one AI step, shared by both world runtimes after the behaviour scripts' facts: a walker that has
// arrived stops there, its move ends and its arrival event is queued (EventRuntimeState::pendingActorArrivals, which
// the world runs at its next update); a dead or dying walker's move ends without it; every other walker walks to its
// point this step (ActorMovementFacts::scriptedMoveTarget). A walker the world counts as background (far from the
// party) waits until it is active again. One that walks for ScriptedActorMoveGiveUpSeconds without getting anywhere
// (stuck, its routes replanned to no avail) gives up: its move ends unarrived (evt.IsActorMoving turns false) and the
// log says where.
void applyScriptedActorMoves(EventRuntimeState &state, ActorAiFrameFacts &facts);

// evt.SetActorTarget for one AI step, after the behaviour scripts' facts: an active MM9 monster takes its ordered
// target as a behaviour script's self:setTarget gives it (ActorMm9ScriptFacts: held whatever their relation) and the
// order ends; a dead or dying one's order ends unused, as does one for an actor without the MM9 loop (the world made
// it hostile already). A background actor keeps its order until it is active.
void applyScriptedActorTargets(EventRuntimeState &state, ActorAiFrameFacts &facts);
}
