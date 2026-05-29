#include "game/mm9/Mm9DatPartyRuntime.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
Mm9DatVec3 addVec3(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.x + right.x,
        left.y + right.y,
        left.z + right.z,
    };
}

Mm9DatVec3 subtractVec3(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {
        left.x - right.x,
        left.y - right.y,
        left.z - right.z,
    };
}

Mm9DatVec3 multiplyVec3(const Mm9DatVec3 &value, float scale)
{
    return {
        value.x * scale,
        value.y * scale,
        value.z * scale,
    };
}

float vectorLength2d(float x, float z)
{
    return std::sqrt(x * x + z * z);
}

const Mm9DatMechanismInstance *findMechanism(
    const Mm9DatMechanismRuntime &runtime,
    uint32_t handle)
{
    const auto iterator = runtime.mechanismIndexByHandle.find(handle);
    if (iterator == runtime.mechanismIndexByHandle.end()
        || iterator->second >= runtime.mechanisms.size())
    {
        return nullptr;
    }

    return &runtime.mechanisms[iterator->second];
}

std::optional<Mm9DatPartyRuntimeMechanismCarry> carryMechanismSupport(
    const Mm9DatWorldRuntime &runtime,
    Mm9DatPartyRuntimeState &state)
{
    if (!state.mechanismSupportHandle.has_value())
    {
        return {};
    }

    const Mm9DatMechanismInstance *pMechanism =
        findMechanism(runtime.mechanismRuntime, *state.mechanismSupportHandle);
    if (pMechanism == nullptr)
    {
        state.mechanismSupportHandle.reset();
        state.mechanismSupportProgress = 0.0f;
        return {};
    }

    Mm9DatPartyRuntimeMechanismCarry carry = {};
    carry.mechanismHandle = pMechanism->handle;
    carry.previousProgress = state.mechanismSupportProgress;
    carry.newProgress = pMechanism->progress;
    if (std::fabs(carry.previousProgress - carry.newProgress) <= 0.0001f)
    {
        return carry;
    }

    Mm9DatMechanismPreviewMotion previousMotion = pMechanism->motion;
    previousMotion.progress = carry.previousProgress;
    const Mm9DatVec3 sourcePosition =
        inverseTransformMm9DatMechanismPreviewPoint(state.position, previousMotion);
    const Mm9DatVec3 transformedNewPosition =
        transformMm9DatMechanismPreviewPoint(sourcePosition, pMechanism->motion);
    carry.displacement = subtractVec3(transformedNewPosition, state.position);
    if (std::fabs(carry.displacement.x) > 0.0001f
        || std::fabs(carry.displacement.y) > 0.0001f
        || std::fabs(carry.displacement.z) > 0.0001f)
    {
        state.position = transformedNewPosition;
        carry.applied = true;
    }

    return carry;
}

void updateMechanismSupport(
    const Mm9DatWorldRuntime &runtime,
    Mm9DatPartyRuntimeState &state,
    const Mm9DatPartyMovementResult &movement)
{
    if (!movement.mechanismFloorHit.has_value())
    {
        state.mechanismSupportHandle.reset();
        state.mechanismSupportProgress = 0.0f;
        return;
    }

    const Mm9DatMechanismInstance *pMechanism =
        findMechanism(runtime.mechanismRuntime, movement.mechanismFloorHit->mechanismHandle);
    if (pMechanism == nullptr)
    {
        state.mechanismSupportHandle.reset();
        state.mechanismSupportProgress = 0.0f;
        return;
    }

    state.mechanismSupportHandle = pMechanism->handle;
    state.mechanismSupportProgress = pMechanism->progress;
}
}

Mm9DatPartyRuntimeState initializeMm9DatPartyRuntimeState(
    const Mm9DatDevStartPose &startPose)
{
    Mm9DatPartyRuntimeState state = {};
    state.position = startPose.position;
    state.yawRadians = startPose.yawRadians;
    state.pitchRadians = startPose.pitchRadians;
    state.onGround = startPose.snappedToFloor;
    return state;
}

Mm9DatVec3 mm9DatPartyForwardVector(float yawRadians, float pitchRadians)
{
    const float pitchCos = std::cos(pitchRadians);
    return {
        std::cos(yawRadians) * pitchCos,
        std::sin(pitchRadians),
        std::sin(yawRadians) * pitchCos,
    };
}

Mm9DatPartyRuntimeMoveResult moveMm9DatPartyRuntime(
    Mm9DatWorldRuntime &runtime,
    Mm9DatPartyRuntimeState &state,
    const Mm9DatPartyRuntimeMoveInput &input,
    const Mm9DatPartyRuntimeMovementOptions &options)
{
    Mm9DatPartyRuntimeMoveResult result = {};
    result.worldUpdate = updateMm9DatWorldRuntime(runtime, input.deltaSeconds);
    result.mechanismCarry = carryMechanismSupport(runtime, state);
    result.previousVerticalVelocityLtPerSecond = state.verticalVelocityLtPerSecond;

    const float clampedDeltaSeconds = std::max(0.0f, input.deltaSeconds);
    const Mm9DatVec3 forward = mm9DatPartyForwardVector(state.yawRadians, 0.0f);
    const Mm9DatVec3 right = {-forward.z, 0.0f, forward.x};
    const float inputLength = std::max(1.0f, vectorLength2d(input.forward, input.strafe));
    const float speed = std::max(0.0f, options.walkSpeedLtPerSecond)
        * (input.running ? std::max(0.0f, options.runSpeedMultiplier) : 1.0f);
    const float movementScale = speed * clampedDeltaSeconds / inputLength;

    const bool hasManualVerticalInput = std::fabs(input.vertical) > 0.0001f;
    float verticalDisplacement = input.vertical * movementScale;
    if (hasManualVerticalInput)
    {
        state.verticalVelocityLtPerSecond = 0.0f;
    }
    else if (!state.onGround && options.gravityLtPerSecondSquared > 0.0f && clampedDeltaSeconds > 0.0f)
    {
        const float terminalFallSpeed = std::max(0.0f, options.terminalFallSpeedLtPerSecond);
        state.verticalVelocityLtPerSecond = std::max(
            -terminalFallSpeed,
            state.verticalVelocityLtPerSecond - options.gravityLtPerSecondSquared * clampedDeltaSeconds);
        verticalDisplacement += state.verticalVelocityLtPerSecond * clampedDeltaSeconds;
        result.gravityApplied = true;
    }
    else if (state.onGround && state.verticalVelocityLtPerSecond < 0.0f)
    {
        state.verticalVelocityLtPerSecond = 0.0f;
    }

    result.desiredDisplacement = addVec3(
        addVec3(
            multiplyVec3(forward, input.forward * movementScale),
            multiplyVec3(right, input.strafe * movementScale)),
        {0.0f, verticalDisplacement, 0.0f});

    Mm9DatPartyMovementStep step = {};
    step.position = state.position;
    step.desiredDisplacement = result.desiredDisplacement;
    step.radius = options.radius;
    step.halfHeight = options.halfHeight;
    step.floorSnapDistance = options.floorSnapDistance;
    step.floorBias = options.floorBias;
    step.maxStepHeight = options.maxStepHeight;
    step.wallChannelMask = options.wallChannelMask;
    step.floorChannelMask = options.floorChannelMask;

    result.movement = moveMm9DatPartyInWorldRuntime(runtime, step);
    state.position = result.movement.finalPosition;
    state.onGround = result.movement.onGround;
    if (state.onGround && state.verticalVelocityLtPerSecond < 0.0f)
    {
        state.verticalVelocityLtPerSecond = 0.0f;
    }
    updateMechanismSupport(runtime, state, result.movement);
    result.newVerticalVelocityLtPerSecond = state.verticalVelocityLtPerSecond;
    return result;
}

Mm9DatPartyRuntimeTeleportResult teleportMm9DatPartyRuntime(
    Mm9DatWorldRuntime &runtime,
    Mm9DatPartyRuntimeState &state,
    const Mm9DatVec3 &position,
    float yawRadians,
    const Mm9DatPartyRuntimeTeleportOptions &options)
{
    Mm9DatPartyRuntimeTeleportResult result = {};
    result.requestedPosition = position;
    result.finalPosition = position;

    if (options.snapToFloor && options.floorSnapDistance > 0.0f)
    {
        Mm9DatPartyMovementStep step = {};
        step.position = position;
        step.desiredDisplacement = {};
        step.halfHeight = std::max(0.0f, options.halfHeight);
        step.floorSnapDistance = options.floorSnapDistance;
        step.floorBias = options.floorBias;
        step.maxStepHeight = 0.0f;
        step.wallChannelMask = 0;
        step.floorChannelMask = options.floorChannelMask;

        const Mm9DatPartyMovementResult movement =
            moveMm9DatPartyInWorldRuntime(runtime, step);
        if (movement.floorHit)
        {
            result.floorHit = movement.floorHit;
            result.mechanismFloorHit = movement.mechanismFloorHit;
            result.finalPosition = movement.finalPosition;
            result.snappedToFloor = true;
            result.onGround = true;
            result.floorCandidateTriangleCount = movement.floorCandidateTriangleCount;
            result.floorTestedTriangleCount = movement.floorTestedTriangleCount;
            result.mechanismCandidateCount = movement.mechanismCandidateCount;
            result.mechanismTestedCount = movement.mechanismTestedCount;
            result.mechanismCandidateTriangleCount = movement.mechanismCandidateTriangleCount;
            result.mechanismTestedTriangleCount = movement.mechanismTestedTriangleCount;
        }
    }

    state.position = result.finalPosition;
    state.yawRadians = yawRadians;
    state.onGround = result.onGround;
    state.verticalVelocityLtPerSecond = 0.0f;
    if (result.mechanismFloorHit)
    {
        const Mm9DatMechanismInstance *pMechanism =
            findMechanism(runtime.mechanismRuntime, result.mechanismFloorHit->mechanismHandle);
        if (pMechanism != nullptr)
        {
            state.mechanismSupportHandle = pMechanism->handle;
            state.mechanismSupportProgress = pMechanism->progress;
        }
        else
        {
            state.mechanismSupportHandle.reset();
            state.mechanismSupportProgress = 0.0f;
        }
    }
    else
    {
        state.mechanismSupportHandle.reset();
        state.mechanismSupportProgress = 0.0f;
    }
    return result;
}

Mm9DatWorldUseResult useMm9DatPartyRuntime(
    Mm9DatWorldRuntime &runtime,
    const Mm9DatPartyRuntimeState &state,
    const Mm9DatPartyRuntimeUseOptions &options)
{
    Mm9DatPickRay ray = {};
    ray.origin = addVec3(state.position, {0.0f, std::max(0.0f, options.eyeHeight), 0.0f});
    ray.direction = mm9DatPartyForwardVector(state.yawRadians, state.pitchRadians);

    Mm9DatWorldPickOptions pickOptions = {};
    pickOptions.maxDistance = options.maxDistance;
    pickOptions.includeWorld = options.includeWorld;
    pickOptions.includeObjects = options.includeObjects;
    pickOptions.includeMechanisms = options.includeMechanisms;

    return useMm9DatWorldRuntime(
        runtime,
        ray,
        pickOptions,
        options.command,
        options.ignoreLocks);
}
}
