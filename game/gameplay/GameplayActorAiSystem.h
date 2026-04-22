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
}
