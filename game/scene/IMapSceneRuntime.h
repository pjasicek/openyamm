#pragma once

#include "game/EventRuntime.h"
#include "game/Party.h"
#include "game/scene/SceneKind.h"

#include <optional>

namespace OpenYAMM::Game
{
class IMapSceneRuntime
{
public:
    virtual ~IMapSceneRuntime() = default;

    virtual SceneKind kind() const = 0;
    virtual const std::string &currentMapFileName() const = 0;
    virtual Party &party() = 0;
    virtual const Party &party() const = 0;
    virtual EventRuntimeState *eventRuntimeState() = 0;
    virtual const EventRuntimeState *eventRuntimeState() const = 0;
    virtual std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove() = 0;
    virtual void advanceGameMinutes(float minutes) = 0;
};
}
