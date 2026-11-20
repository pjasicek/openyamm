#include "game/outdoor/OutdoorMechanismRuntime.h"

#include "game/events/EvtEnums.h"

#include <algorithm>

namespace OpenYAMM::Game
{
uint64_t outdoorMechanismAudioKey(uint32_t mechanismId)
{
    constexpr uint64_t MechanismAudioKeyPrefix = uint64_t{0x4d394d45} << 32; // "M9ME"
    return MechanismAudioKeyPrefix | uint64_t{mechanismId};
}

float outdoorMechanismOpenFraction(
    const RuntimeMechanismState &mechanism,
    const EventRuntimeState::OutdoorModelMechanismDefinition &definition)
{
    const float moveTimeMs = std::max(1.0f, static_cast<float>(definition.moveTimeMs));

    if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Open))
    {
        return 1.0f;
    }

    if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closed))
    {
        return 0.0f;
    }

    if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
    {
        return std::clamp(mechanism.timeSinceTriggeredMs / moveTimeMs, 0.0f, 1.0f);
    }

    if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
    {
        return 1.0f - std::clamp(mechanism.timeSinceTriggeredMs / moveTimeMs, 0.0f, 1.0f);
    }

    return definition.closed ? 0.0f : 1.0f;
}

std::optional<uint16_t> outdoorBModelRuntimeInteractionEventId(
    const EventRuntimeState *pEventRuntimeState,
    size_t bModelIndex)
{
    if (pEventRuntimeState == nullptr)
    {
        return std::nullopt;
    }

    for (const std::pair<const uint32_t, EventRuntimeState::OutdoorModelMechanismDefinition> &entry :
        pEventRuntimeState->outdoorModelMechanisms)
    {
        const EventRuntimeState::OutdoorModelMechanismDefinition &definition = entry.second;

        if (definition.bmodelIndex == bModelIndex && definition.interactionEventId != 0)
        {
            return definition.interactionEventId;
        }
    }

    return std::nullopt;
}

int8_t outdoorMechanismOpenAwayRotationDirection(
    const EventRuntimeState::OutdoorModelMechanismDefinition &definition,
    const bx::Vec3 &closedCenter,
    const bx::Vec3 &activatorPosition)
{
    OutdoorBModelTransform transform = {};
    transform.pivotX = static_cast<float>(definition.pivotX);
    transform.pivotY = static_cast<float>(definition.pivotY);
    transform.pivotZ = static_cast<float>(definition.pivotZ);
    transform.rotationDegreesX = definition.rotationDegreesX;
    transform.rotationDegreesY = definition.rotationDegreesY;
    transform.rotationDegreesZ = definition.rotationDegreesZ;
    const bx::Vec3 positiveCenter = transformOutdoorBModelPoint(closedCenter, transform, 1.0f);
    transform.rotationDegreesX = -transform.rotationDegreesX;
    transform.rotationDegreesY = -transform.rotationDegreesY;
    transform.rotationDegreesZ = -transform.rotationDegreesZ;
    const bx::Vec3 negativeCenter = transformOutdoorBModelPoint(closedCenter, transform, 1.0f);
    const auto distanceSquared = [&activatorPosition](const bx::Vec3 &point)
    {
        const float dx = point.x - activatorPosition.x;
        const float dy = point.y - activatorPosition.y;
        const float dz = point.z - activatorPosition.z;
        return dx * dx + dy * dy + dz * dz;
    };

    return distanceSquared(negativeCenter) > distanceSquared(positiveCenter) ? -1 : 1;
}

std::optional<OutdoorBModelRuntimeTransformState> outdoorBModelRuntimeTransform(
    const EventRuntimeState *pEventRuntimeState,
    size_t bModelIndex)
{
    if (pEventRuntimeState == nullptr)
    {
        return std::nullopt;
    }

    for (const std::pair<const uint32_t, EventRuntimeState::OutdoorModelMechanismDefinition> &entry :
        pEventRuntimeState->outdoorModelMechanisms)
    {
        const EventRuntimeState::OutdoorModelMechanismDefinition &definition = entry.second;

        if (definition.bmodelIndex != bModelIndex)
        {
            continue;
        }

        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
            pEventRuntimeState->mechanisms.find(entry.first);

        if (mechanismIterator == pEventRuntimeState->mechanisms.end())
        {
            continue;
        }

        OutdoorBModelRuntimeTransformState state = {};
        state.transform.translationX = static_cast<float>(definition.dx);
        state.transform.translationY = static_cast<float>(definition.dy);
        state.transform.translationZ = static_cast<float>(definition.dz);
        state.transform.pivotX = static_cast<float>(definition.pivotX);
        state.transform.pivotY = static_cast<float>(definition.pivotY);
        state.transform.pivotZ = static_cast<float>(definition.pivotZ);
        const float rotationDirection = mechanismIterator->second.rotationDirection < 0 ? -1.0f : 1.0f;
        state.transform.rotationDegreesX = definition.rotationDegreesX * rotationDirection;
        state.transform.rotationDegreesY = definition.rotationDegreesY * rotationDirection;
        state.transform.rotationDegreesZ = definition.rotationDegreesZ * rotationDirection;
        state.fraction = outdoorMechanismOpenFraction(mechanismIterator->second, definition);
        return state;
    }

    return std::nullopt;
}

bx::Vec3 applyOutdoorBModelRuntimeTransform(
    const std::optional<OutdoorBModelRuntimeTransformState> &runtimeTransform,
    const bx::Vec3 &point)
{
    if (!runtimeTransform)
    {
        return point;
    }

    return transformOutdoorBModelPoint(point, runtimeTransform->transform, runtimeTransform->fraction);
}

OutdoorBModel transformOutdoorBModelForRuntime(
    const OutdoorBModel &bmodel,
    const EventRuntimeState *pEventRuntimeState,
    size_t bModelIndex)
{
    const std::optional<OutdoorBModelRuntimeTransformState> runtimeTransform =
        outdoorBModelRuntimeTransform(pEventRuntimeState, bModelIndex);

    if (!runtimeTransform)
    {
        return bmodel;
    }

    return transformOutdoorBModel(bmodel, runtimeTransform->transform, runtimeTransform->fraction);
}
}
