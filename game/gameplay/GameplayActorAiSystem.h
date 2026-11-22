#pragma once

#include "game/gameplay/GameplayActorAiTypes.h"

namespace OpenYAMM::Game
{
class GameplayActorAiSystem
{
public:
    ActorAiFrameResult updateActors(const ActorAiFrameFacts &facts) const;
    ActorAiUpdate updateActorAfterWorldMovement(const ActorAiFacts &facts) const;
};

// A post's leash on the step a world finally takes (ActorMovementIntent::leashRadius, D-54): once the actor is at or
// beyond the leash from home (measured level), the part of its direction that leads further out is dropped, so it
// slides along the circle or stands; a step back inside, or any step within the leash, is kept. A flyer still climbs
// or sinks.
void keepStepOnLeash(float leashRadius, const GameplayWorldPoint &home, float positionX, float positionY,
    float &directionX, float &directionY);
}
