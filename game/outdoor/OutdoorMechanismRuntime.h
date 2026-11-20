#pragma once

#include "game/events/EventRuntime.h"
#include "game/outdoor/OutdoorGeometryUtils.h"

#include <cstddef>
#include <optional>

namespace OpenYAMM::Game
{
struct OutdoorBModelRuntimeTransformState
{
    OutdoorBModelTransform transform = {};
    float fraction = 0.0f;
};

float outdoorMechanismOpenFraction(
    const RuntimeMechanismState &mechanism,
    const EventRuntimeState::OutdoorModelMechanismDefinition &definition);
// The outdoor model mechanisms' sound key (MechanismAudio.h: their busy loop, its stop).
uint64_t outdoorMechanismAudioKey(uint32_t mechanismId);
std::optional<uint16_t> outdoorBModelRuntimeInteractionEventId(
    const EventRuntimeState *pEventRuntimeState,
    size_t bModelIndex);
int8_t outdoorMechanismOpenAwayRotationDirection(
    const EventRuntimeState::OutdoorModelMechanismDefinition &definition,
    const bx::Vec3 &closedCenter,
    const bx::Vec3 &activatorPosition);
std::optional<OutdoorBModelRuntimeTransformState> outdoorBModelRuntimeTransform(
    const EventRuntimeState *pEventRuntimeState,
    size_t bModelIndex);
bx::Vec3 applyOutdoorBModelRuntimeTransform(
    const std::optional<OutdoorBModelRuntimeTransformState> &runtimeTransform,
    const bx::Vec3 &point);
OutdoorBModel transformOutdoorBModelForRuntime(
    const OutdoorBModel &bmodel,
    const EventRuntimeState *pEventRuntimeState,
    size_t bModelIndex);
}
