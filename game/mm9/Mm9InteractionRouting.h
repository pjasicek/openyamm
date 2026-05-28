#pragma once

#include "game/gameplay/GameplayWorldInteraction.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

#include <bx/math.h>

namespace OpenYAMM::Game
{
struct Mm9InteractionObjectBinding
{
    std::string mapId;
    std::string objectId;
    int32_t sourceObjectIndex = -1;
    std::string sourceClass;
    std::string sourceName;
    std::string visualId;
    std::string scriptName;
    std::string scriptParams;
    size_t routerTargetIndex = GameplayInvalidWorldIndex;
    bx::Vec3 hitPoint = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
};

GameplayWorldHit buildMm9ScriptedObjectWorldHit(const Mm9InteractionObjectBinding &binding);
std::optional<Mm9InteractionObjectBinding> mm9InteractionObjectBindingFromWorldHit(const GameplayWorldHit &hit);
}
