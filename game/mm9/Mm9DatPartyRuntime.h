#pragma once

#include "game/mm9/Mm9DatRuntimeDevEntry.h"

#include <optional>

namespace OpenYAMM::Game
{
struct Mm9DatPartyRuntimeState
{
    Mm9DatVec3 position;
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
    float verticalVelocityLtPerSecond = 0.0f;
    bool onGround = false;
    std::optional<uint32_t> mechanismSupportHandle;
    float mechanismSupportProgress = 0.0f;
};

struct Mm9DatPartyRuntimeMovementOptions
{
    float walkSpeedLtPerSecond = 224.0f;
    float runSpeedMultiplier = 1.8f;
    float radius = 24.0f;
    float halfHeight = 64.0f;
    float floorSnapDistance = 96.0f;
    float floorBias = 0.1f;
    float maxStepHeight = 24.0f;
    float gravityLtPerSecondSquared = 1536.0f;
    float terminalFallSpeedLtPerSecond = 2048.0f;
    uint32_t wallChannelMask = Mm9DatPhysicsQueryChannelPhysics;
    uint32_t floorChannelMask = Mm9DatPhysicsQueryChannelPhysics;
};

struct Mm9DatPartyRuntimeMoveInput
{
    float forward = 0.0f;
    float strafe = 0.0f;
    float vertical = 0.0f;
    float deltaSeconds = 0.0f;
    bool running = false;
};

struct Mm9DatPartyRuntimeMechanismCarry
{
    uint32_t mechanismHandle = 0;
    float previousProgress = 0.0f;
    float newProgress = 0.0f;
    Mm9DatVec3 displacement;
    bool applied = false;
};

struct Mm9DatPartyRuntimeMoveResult
{
    Mm9DatVec3 desiredDisplacement;
    Mm9DatWorldRuntimeUpdateStats worldUpdate;
    Mm9DatPartyMovementResult movement;
    std::optional<Mm9DatPartyRuntimeMechanismCarry> mechanismCarry;
    float previousVerticalVelocityLtPerSecond = 0.0f;
    float newVerticalVelocityLtPerSecond = 0.0f;
    bool gravityApplied = false;
};

struct Mm9DatPartyRuntimeTeleportOptions
{
    bool snapToFloor = true;
    float halfHeight = 64.0f;
    float floorSnapDistance = 512.0f;
    float floorBias = 0.1f;
    uint32_t floorChannelMask = Mm9DatPhysicsQueryChannelPhysics;
};

struct Mm9DatPartyRuntimeTeleportResult
{
    Mm9DatVec3 requestedPosition;
    Mm9DatVec3 finalPosition;
    bool snappedToFloor = false;
    bool onGround = false;
    size_t floorCandidateTriangleCount = 0;
    size_t floorTestedTriangleCount = 0;
    size_t mechanismCandidateCount = 0;
    size_t mechanismTestedCount = 0;
    size_t mechanismCandidateTriangleCount = 0;
    size_t mechanismTestedTriangleCount = 0;
    std::optional<Mm9DatFloorSupportHit> floorHit;
    std::optional<Mm9DatMechanismCollisionHit> mechanismFloorHit;
};

struct Mm9DatPartyRuntimeUseOptions
{
    float maxDistance = 512.0f;
    float eyeHeight = 48.0f;
    Mm9DatMechanismCommand command = Mm9DatMechanismCommand::Toggle;
    bool ignoreLocks = false;
    bool includeWorld = true;
    bool includeObjects = true;
    bool includeMechanisms = true;
};

Mm9DatPartyRuntimeState initializeMm9DatPartyRuntimeState(
    const Mm9DatDevStartPose &startPose);

Mm9DatVec3 mm9DatPartyForwardVector(float yawRadians, float pitchRadians = 0.0f);

Mm9DatPartyRuntimeMoveResult moveMm9DatPartyRuntime(
    Mm9DatWorldRuntime &runtime,
    Mm9DatPartyRuntimeState &state,
    const Mm9DatPartyRuntimeMoveInput &input,
    const Mm9DatPartyRuntimeMovementOptions &options = {});

Mm9DatPartyRuntimeTeleportResult teleportMm9DatPartyRuntime(
    Mm9DatWorldRuntime &runtime,
    Mm9DatPartyRuntimeState &state,
    const Mm9DatVec3 &position,
    float yawRadians,
    const Mm9DatPartyRuntimeTeleportOptions &options = {});

Mm9DatWorldUseResult useMm9DatPartyRuntime(
    Mm9DatWorldRuntime &runtime,
    const Mm9DatPartyRuntimeState &state,
    const Mm9DatPartyRuntimeUseOptions &options = {});
}
