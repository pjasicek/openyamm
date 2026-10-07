#include "game/outdoor/OutdoorMovementDriver.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float OutdoorMovementStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedMovementSeconds = 0.1f;
constexpr float HardLandingDistance = 512.0f;
constexpr float EventHoldSeconds = 0.75f;
constexpr float DamageTickSeconds = 1.0f;

const char *supportKindName(OutdoorSupportKind supportKind)
{
    switch (supportKind)
    {
        case OutdoorSupportKind::None:
            return "none";
        case OutdoorSupportKind::Terrain:
            return "terrain";
        case OutdoorSupportKind::BModelFace:
            return "bmodel";
    }

    return "unknown";
}

const char *collisionHitKindName(int kind)
{
    switch (kind)
    {
        case 0:
            return "none";
        case 1:
            return "face";
        case 2:
            return "decoration";
        case 3:
            return "actor";
        case 4:
            return "sprite_object";
    }

    return "unknown";
}

void appendVec3(std::ostream &out, const bx::Vec3 &value)
{
    out << "(" << value.x << "," << value.y << "," << value.z << ")";
}

void appendFloor(std::ostream &out, const char *prefix, const OutdoorMoveFloorDebugInfo &floor)
{
    out << " " << prefix << "_has_floor=" << (floor.hasFloor ? "true" : "false")
        << " " << prefix << "_height=" << floor.height
        << " " << prefix << "_normal_z=" << floor.normalZ
        << " " << prefix << "_from_bmodel=" << (floor.fromBModel ? "true" : "false")
        << " " << prefix << "_fluid=" << (floor.isFluid ? "true" : "false")
        << " " << prefix << "_bmodel=" << floor.bModelIndex
        << " " << prefix << "_face=" << floor.faceIndex;
}
}

OutdoorMovementDriver::OutdoorMovementDriver(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet
)
    : OutdoorMovementDriver(
        outdoorMapData,
        std::nullopt,
        outdoorLandMask,
        outdoorDecorationCollisionSet,
        outdoorActorCollisionSet,
        outdoorSpriteObjectCollisionSet
    )
{
}

OutdoorMovementDriver::OutdoorMovementDriver(
    const OutdoorMapData &outdoorMapData,
    const std::optional<MapBounds> &mapBounds,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet
)
    : m_movementController(
        outdoorMapData,
        mapBounds,
        outdoorLandMask,
        outdoorDecorationCollisionSet,
        outdoorActorCollisionSet,
        outdoorSpriteObjectCollisionSet
    )
{
}

void OutdoorMovementDriver::initialize(float x, float y, float footZHint)
{
    m_state = m_movementController.initializeStateForBody(x, y, footZHint, m_bodyDimensions.radius);
    m_partyMovementState = {};
    m_tuning = {};
    m_lastEvents = {};
    m_lastConsequences = {};
    m_pendingEffects = {};
    m_jumpHeld = false;
    m_flyUpHeld = false;
    m_pendingFlyHeightDelta = 0.0f;
    m_pendingJumpPress = false;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = 1.0f;
    m_pendingImpulseVelocityX = 0.0f;
    m_pendingImpulseVelocityY = 0.0f;
    m_pendingImpulseVelocityZ = 0.0f;
    m_flyingAvailable = false;
    m_movementAccumulatorSeconds = 0.0f;
    m_startedFallingEventSeconds = 0.0f;
    m_landedEventSeconds = 0.0f;
    m_enteredWaterEventSeconds = 0.0f;
    m_leftWaterEventSeconds = 0.0f;
    m_enteredBurningEventSeconds = 0.0f;
    m_leftBurningEventSeconds = 0.0f;
    m_waterDamageConsequenceSeconds = 0.0f;
    m_burningDamageConsequenceSeconds = 0.0f;
    m_fallDamageConsequenceSeconds = 0.0f;
    m_splashSoundConsequenceSeconds = 0.0f;
    m_landingSoundConsequenceSeconds = 0.0f;
    m_hardLandingSoundConsequenceSeconds = 0.0f;
    m_waterDamageTimerSeconds = 0.0f;
    m_burningDamageTimerSeconds = 0.0f;
    m_speedMultiplier = 1.0f;
}

void OutdoorMovementDriver::restoreState(
    const OutdoorMoveState &state,
    const OutdoorPartyMovementState &partyMovementState)
{
    m_state = state;
    m_partyMovementState = partyMovementState;
    m_tuning = {};
    m_lastEvents = {};
    m_lastConsequences = {};
    m_pendingEffects = {};
    m_jumpHeld = false;
    m_flyUpHeld = false;
    m_pendingFlyHeightDelta = 0.0f;
    m_pendingJumpPress = false;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = 1.0f;
    m_pendingImpulseVelocityX = 0.0f;
    m_pendingImpulseVelocityY = 0.0f;
    m_pendingImpulseVelocityZ = 0.0f;
    m_movementAccumulatorSeconds = 0.0f;
    m_startedFallingEventSeconds = 0.0f;
    m_landedEventSeconds = 0.0f;
    m_enteredWaterEventSeconds = 0.0f;
    m_leftWaterEventSeconds = 0.0f;
    m_enteredBurningEventSeconds = 0.0f;
    m_leftBurningEventSeconds = 0.0f;
    m_waterDamageConsequenceSeconds = 0.0f;
    m_burningDamageConsequenceSeconds = 0.0f;
    m_fallDamageConsequenceSeconds = 0.0f;
    m_splashSoundConsequenceSeconds = 0.0f;
    m_landingSoundConsequenceSeconds = 0.0f;
    m_hardLandingSoundConsequenceSeconds = 0.0f;
    m_waterDamageTimerSeconds = 0.0f;
    m_burningDamageTimerSeconds = 0.0f;
    m_speedMultiplier = 1.0f;
}

void OutdoorMovementDriver::update(
    const OutdoorMovementInput &input,
    float deltaSeconds,
    GameplayWorldMovementFrameDiagnostics *pPerformanceDiagnostics)
{
    const uint64_t totalBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
    const bool jumpPressed = input.jump && !m_jumpHeld;
    m_jumpHeld = input.jump;
    m_pendingJumpPress = m_pendingJumpPress || jumpPressed;
    const bool flyUpPressed = (input.flyUp && !m_flyUpHeld) || input.flyHeightDelta > 0.0f;
    m_flyUpHeld = input.flyUp;

    if (!m_flyingAvailable)
    {
        m_partyMovementState.flying = false;
    }
    else if (!m_partyMovementState.flying && flyUpPressed && canActivateFlying())
    {
        m_partyMovementState.flying = true;
        m_state.verticalVelocity = 0.0f;
        m_state.fallStartZ = m_state.footZ;
        m_state.fallDistance = 0.0f;
    }

    if (m_partyMovementState.flying)
    {
        m_pendingFlyHeightDelta += input.flyHeightDelta;
    }
    else
    {
        m_pendingFlyHeightDelta = 0.0f;
    }
    const bool flyHeightChangeRequested = m_pendingFlyHeightDelta != 0.0f;

    const float cosYaw = std::cos(input.yawRadians);
    const float sinYaw = std::sin(input.yawRadians);
    const float movementPitchRadians = input.usePitchForFlyingMovement ? input.pitchRadians : 0.0f;
    const float cosPitch = std::cos(movementPitchRadians);
    const float sinPitch = std::sin(movementPitchRadians);
    const float inputSpeedScale = std::clamp(input.movementSpeedScale, 0.0f, 1.0f);
    const float speedMultiplier = std::max(m_speedMultiplier, 0.0f) * inputSpeedScale;
    const bx::Vec3 forward = {cosYaw, sinYaw, 0.0f};
    const bx::Vec3 forwardFlying = {cosYaw * cosPitch, sinYaw * cosPitch, sinPitch};
    const bx::Vec3 right = {sinYaw, -cosYaw, 0.0f};
    const bool effectiveRunning =
        input.runWalkModifier ? !m_partyMovementState.running : m_partyMovementState.running;
    float moveVelocityX = 0.0f;
    float moveVelocityY = 0.0f;
    float moveVelocityZ = 0.0f;

    if (input.turbo)
    {
        const float forwardTurboMultiplier =
            m_partyMovementState.flying && effectiveRunning
                ? m_tuning.flyingRunTurboMultiplier
                : m_tuning.turboMultiplier;
        const float backwardTurboMultiplier =
            m_partyMovementState.flying && effectiveRunning
                ? m_tuning.flyingRunTurboMultiplier
                : m_tuning.turboMultiplier;
        const float sideTurboMultiplier =
            m_partyMovementState.flying && effectiveRunning
                ? m_tuning.flyingRunTurboMultiplier
                : m_tuning.turboMultiplier;
        const float sideTurboSpeed =
            m_tuning.walkSpeed * m_tuning.strafeMultiplier * sideTurboMultiplier * speedMultiplier;

        if (input.forward)
        {
            const bx::Vec3 &forwardVector = m_partyMovementState.flying ? forwardFlying : forward;
            const float forwardSpeed = m_tuning.walkSpeed * forwardTurboMultiplier * speedMultiplier;
            moveVelocityX += forwardVector.x * forwardSpeed;
            moveVelocityY += forwardVector.y * forwardSpeed;
            moveVelocityZ += forwardVector.z * forwardSpeed;
        }

        if (input.backward)
        {
            const bx::Vec3 &forwardVector = m_partyMovementState.flying ? forwardFlying : forward;
            const float backwardSpeed = m_tuning.walkSpeed * backwardTurboMultiplier * speedMultiplier;
            moveVelocityX -= forwardVector.x * backwardSpeed;
            moveVelocityY -= forwardVector.y * backwardSpeed;
            moveVelocityZ -= forwardVector.z * backwardSpeed;
        }

        if (input.left)
        {
            moveVelocityX -= right.x * sideTurboSpeed;
            moveVelocityY -= right.y * sideTurboSpeed;
        }

        if (input.right)
        {
            moveVelocityX += right.x * sideTurboSpeed;
            moveVelocityY += right.y * sideTurboSpeed;
        }
    }
    else
    {
        const float forwardSpeedMultiplier =
            effectiveRunning
                ? (m_partyMovementState.flying ? m_tuning.flyingRunMultiplier : m_tuning.runForwardMultiplier)
                : 1.0f;
        const float backwardSpeedMultiplier =
            m_partyMovementState.flying && effectiveRunning
                ? m_tuning.flyingRunMultiplier
                : m_tuning.backwardWalkMultiplier;
        const float sideSpeedMultiplier =
            effectiveRunning
                ? (m_partyMovementState.flying ? m_tuning.flyingRunMultiplier : m_tuning.runForwardMultiplier)
                : 1.0f;
        const float sideSpeed =
            m_tuning.walkSpeed * m_tuning.strafeMultiplier * sideSpeedMultiplier * speedMultiplier;

        if (input.left)
        {
            moveVelocityX -= right.x * sideSpeed;
            moveVelocityY -= right.y * sideSpeed;
        }

        if (input.right)
        {
            moveVelocityX += right.x * sideSpeed;
            moveVelocityY += right.y * sideSpeed;
        }

        if (input.forward)
        {
            const bx::Vec3 &forwardVector = m_partyMovementState.flying ? forwardFlying : forward;
            moveVelocityX += forwardVector.x * m_tuning.walkSpeed * forwardSpeedMultiplier * speedMultiplier;
            moveVelocityY += forwardVector.y * m_tuning.walkSpeed * forwardSpeedMultiplier * speedMultiplier;
            moveVelocityZ += forwardVector.z * m_tuning.walkSpeed * forwardSpeedMultiplier * speedMultiplier;
        }

        if (input.backward)
        {
            const bx::Vec3 &forwardVector = m_partyMovementState.flying ? forwardFlying : forward;
            moveVelocityX -= forwardVector.x * m_tuning.walkSpeed * backwardSpeedMultiplier * speedMultiplier;
            moveVelocityY -= forwardVector.y * m_tuning.walkSpeed * backwardSpeedMultiplier * speedMultiplier;
            moveVelocityZ -= forwardVector.z * m_tuning.walkSpeed * backwardSpeedMultiplier * speedMultiplier;
        }
    }

    m_startedFallingEventSeconds = std::max(0.0f, m_startedFallingEventSeconds - deltaSeconds);
    m_landedEventSeconds = std::max(0.0f, m_landedEventSeconds - deltaSeconds);
    m_enteredWaterEventSeconds = std::max(0.0f, m_enteredWaterEventSeconds - deltaSeconds);
    m_leftWaterEventSeconds = std::max(0.0f, m_leftWaterEventSeconds - deltaSeconds);
    m_enteredBurningEventSeconds = std::max(0.0f, m_enteredBurningEventSeconds - deltaSeconds);
    m_leftBurningEventSeconds = std::max(0.0f, m_leftBurningEventSeconds - deltaSeconds);
    m_waterDamageConsequenceSeconds = std::max(0.0f, m_waterDamageConsequenceSeconds - deltaSeconds);
    m_burningDamageConsequenceSeconds = std::max(0.0f, m_burningDamageConsequenceSeconds - deltaSeconds);
    m_fallDamageConsequenceSeconds = std::max(0.0f, m_fallDamageConsequenceSeconds - deltaSeconds);
    m_splashSoundConsequenceSeconds = std::max(0.0f, m_splashSoundConsequenceSeconds - deltaSeconds);
    m_landingSoundConsequenceSeconds = std::max(0.0f, m_landingSoundConsequenceSeconds - deltaSeconds);
    m_hardLandingSoundConsequenceSeconds = std::max(0.0f, m_hardLandingSoundConsequenceSeconds - deltaSeconds);
    m_lastEvents = {};
    m_lastConsequences = {};
    const float maxAccumulatedMovementSeconds =
        input.turnBasedMovementStep
            ? std::max(deltaSeconds, MaxAccumulatedMovementSeconds)
            : MaxAccumulatedMovementSeconds;
    m_movementAccumulatorSeconds =
        std::min(m_movementAccumulatorSeconds + deltaSeconds, maxAccumulatedMovementSeconds);
    float impulseVelocityX = 0.0f;
    float impulseVelocityY = 0.0f;
    float impulseVelocityZ = 0.0f;

    if (m_movementAccumulatorSeconds >= OutdoorMovementStepSeconds)
    {
        impulseVelocityX = m_pendingImpulseVelocityX;
        impulseVelocityY = m_pendingImpulseVelocityY;
        impulseVelocityZ = m_pendingImpulseVelocityZ;
        const bool hasPendingImpulse =
            impulseVelocityX != 0.0f || impulseVelocityY != 0.0f || impulseVelocityZ != 0.0f;

        if (hasPendingImpulse)
        {
            m_state.verticalVelocity = std::max(m_state.verticalVelocity, impulseVelocityZ);
            m_pendingImpulseVelocityX = 0.0f;
            m_pendingImpulseVelocityY = 0.0f;
            m_pendingImpulseVelocityZ = 0.0f;
        }
    }

    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->movementInputNanoseconds += SDL_GetTicksNS() - totalBeginTickCount;
    }

    while (m_movementAccumulatorSeconds >= OutdoorMovementStepSeconds)
    {
        if (pPerformanceDiagnostics != nullptr)
        {
            ++pPerformanceDiagnostics->movementStepCount;
        }

        m_collisionTraceClockSeconds += OutdoorMovementStepSeconds;
        const OutdoorMoveState previousState = m_state;
        const bool jumpRequestedThisStep = m_pendingJumpPress;
        const float jumpVelocityThisStep =
            m_pendingJumpVelocity.value_or(m_tuning.jumpVelocity * speedMultiplier);
        const float jumpLiftThisStep = m_pendingJumpLift;
        std::vector<size_t> contactedActorIndices;
        const bool traceOutdoorMovement = m_collisionTraceEnabled || gameplayDebugTraceEnabled();
        OutdoorMoveDebugInfo debugInfo = {};
        OutdoorMoveDebugInfo *pDebugInfo = traceOutdoorMovement ? &debugInfo : nullptr;
        const uint64_t collisionBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
        m_state = m_movementController.resolveMoveForBody(
            m_state,
            m_bodyDimensions,
            moveVelocityX + impulseVelocityX,
            moveVelocityY + impulseVelocityY,
            moveVelocityZ + m_pendingFlyHeightDelta / OutdoorMovementStepSeconds,
            jumpRequestedThisStep,
            input.flyUp,
            input.flyDown,
            m_partyMovementState.flying,
            m_partyMovementState.waterWalk,
            jumpVelocityThisStep,
            m_tuning.flyVerticalSpeed * speedMultiplier,
            m_tuning.maxFlightHeight,
            OutdoorMovementStepSeconds,
            &contactedActorIndices,
            std::nullopt,
            jumpLiftThisStep,
            pDebugInfo
        );

        if (pPerformanceDiagnostics != nullptr)
        {
            pPerformanceDiagnostics->movementCollisionNanoseconds += SDL_GetTicksNS() - collisionBeginTickCount;
        }

        m_pendingJumpPress = false;
        m_pendingFlyHeightDelta = 0.0f;
        m_pendingJumpVelocity.reset();
        m_pendingJumpLift = 1.0f;

        const uint64_t traceBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
        if (traceOutdoorMovement)
        {
            const float deltaX = m_state.x - previousState.x;
            const float deltaY = m_state.y - previousState.y;
            const float deltaZ = m_state.footZ - previousState.footZ;
            const float horizontalDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY);
            const bool supportChanged =
                previousState.supportKind != m_state.supportKind
                || previousState.supportBModelIndex != m_state.supportBModelIndex
                || previousState.supportFaceIndex != m_state.supportFaceIndex;
            const bool suspiciousUpwardMove =
                deltaZ > 96.0f
                && !m_partyMovementState.flying
                && !jumpRequestedThisStep;
            const bool suspiciousHorizontalRaise =
                debugInfo.horizontalPassRaisedZ
                && !debugInfo.verticalPassRan
                && deltaZ > 32.0f
                && !m_partyMovementState.flying;
            const bool periodicProbe = m_collisionTraceClockSeconds >= m_nextCollisionTraceSeconds;
            const bool suspicious = suspiciousUpwardMove || suspiciousHorizontalRaise;

            if (suspicious || periodicProbe)
            {
                std::ostringstream out;
                out << "outdoor_collision_trace"
                    << " map=\"" << m_collisionTraceMapName << "\""
                    << " reason=" << (suspicious ? "suspicious" : "periodic")
                    << " start=(" << previousState.x
                    << "," << previousState.y
                    << "," << previousState.footZ << ")"
                    << " end=(" << m_state.x
                    << "," << m_state.y
                    << "," << m_state.footZ << ")"
                    << " delta=(" << deltaX << "," << deltaY << "," << deltaZ << ")"
                    << " horizontal_distance=" << horizontalDistance
                    << " start_velocity_z=" << previousState.verticalVelocity
                    << " end_velocity_z=" << m_state.verticalVelocity
                    << " requested_velocity=("
                    << debugInfo.requestedVelocityX
                    << "," << debugInfo.requestedVelocityY
                    << "," << debugInfo.requestedVelocityZ << ")"
                    << " input_velocity_z_before_collision=" << debugInfo.inputVelocityZBeforeCollision
                    << " flying=" << (m_partyMovementState.flying ? "true" : "false")
                    << " jump_requested=" << (jumpRequestedThisStep ? "true" : "false")
                    << " fly_up=" << (input.flyUp ? "true" : "false")
                    << " fly_down=" << (input.flyDown ? "true" : "false")
                    << " was_airborne=" << (debugInfo.wasAirborne ? "true" : "false")
                    << " start_airborne=" << (previousState.airborne ? "true" : "false")
                    << " end_airborne=" << (m_state.airborne ? "true" : "false")
                    << " party_not_touching_floor="
                    << (debugInfo.partyNotTouchingFloor ? "true" : "false")
                    << " party_close_to_ground=" << (debugInfo.partyCloseToGround ? "true" : "false")
                    << " party_on_steep_bmodel=" << (debugInfo.partyOnSteepBModel ? "true" : "false")
                    << " slope_slide=" << (debugInfo.slopeSlideActive ? "true" : "false")
                    << " horizontal_pass_z=("
                    << debugInfo.horizontalPassStartZ
                    << "," << debugInfo.horizontalPassEndZ << ")"
                    << " horizontal_pass_raised_z="
                    << (debugInfo.horizontalPassRaisedZ ? "true" : "false")
                    << " vertical_pass_ran=" << (debugInfo.verticalPassRan ? "true" : "false")
                    << " vertical_pass_z=("
                    << debugInfo.verticalPassStartZ
                    << "," << debugInfo.verticalPassEndZ << ")"
                    << " collision_attempts=" << debugInfo.collisionAttempts
                    << " last_collision_pass=" << debugInfo.lastCollisionPass
                    << " last_hit_kind=" << collisionHitKindName(debugInfo.lastHitKind)
                    << " last_hit_bmodel=" << debugInfo.lastHitBModelIndex
                    << " last_hit_face=" << debugInfo.lastHitFaceIndex
                    << " last_hit_collider=" << debugInfo.lastHitColliderIndex
                    << " last_hit_polygon_type=" << static_cast<int>(debugInfo.lastHitPolygonType)
                    << " last_hit_floor_height=" << debugInfo.lastHitFloorHeight
                    << " last_hit_move=" << debugInfo.lastHitMoveDistance
                    << " last_hit_adjusted=" << debugInfo.lastHitAdjustedMoveDistance
                    << " last_hit_height_offset=" << debugInfo.lastHitHeightOffset
                    << " last_hit_point=";
                appendVec3(out, debugInfo.lastHitPoint);
                out << " last_hit_normal=";
                appendVec3(out, debugInfo.lastHitNormal);
                out << " last_pass_start=";
                appendVec3(out, debugInfo.lastPassStart);
                out << " last_pass_input_velocity=";
                appendVec3(out, debugInfo.lastPassInputVelocity);
                out << " last_pass_new_low=";
                appendVec3(out, debugInfo.lastPassNewLow);
                out << " last_pass_output_velocity=";
                appendVec3(out, debugInfo.lastPassOutputVelocity);
                out << " start_support_kind=" << supportKindName(previousState.supportKind)
                    << " start_support_bmodel=" << previousState.supportBModelIndex
                    << " start_support_face=" << previousState.supportFaceIndex
                    << " end_support_kind=" << supportKindName(m_state.supportKind)
                    << " end_support_bmodel=" << m_state.supportBModelIndex
                    << " end_support_face=" << m_state.supportFaceIndex
                    << " support_changed=" << (supportChanged ? "true" : "false");
                appendFloor(out, "current_floor", debugInfo.currentFloor);
                appendFloor(out, "all_new_floor", debugInfo.lastAllNewFloor);
                appendFloor(out, "x_advance_floor", debugInfo.lastXAdvanceFloor);
                appendFloor(out, "y_advance_floor", debugInfo.lastYAdvanceFloor);
                appendFloor(out, "stepped_bmodel_floor", debugInfo.steppedBModelFloor);
                appendFloor(out, "final_floor", debugInfo.finalFloor);
                gameplayDebugTraceWrite(out.str());
                m_nextCollisionTraceSeconds = m_collisionTraceClockSeconds + (suspicious ? 0.125f : 1.0f);
            }
        }

        if (pPerformanceDiagnostics != nullptr)
        {
            pPerformanceDiagnostics->movementTraceNanoseconds += SDL_GetTicksNS() - traceBeginTickCount;
        }

        const uint64_t contactsBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
        if (!m_lastEvents.blockedBoundaryEdge.has_value())
        {
            m_lastEvents.blockedBoundaryEdge = m_movementController.detectBoundaryBlock(
                previousState,
                m_state,
                moveVelocityX,
                moveVelocityY);
        }

        for (size_t actorIndex : contactedActorIndices)
        {
            if (std::find(
                    m_lastEvents.contactedActorIndices.begin(),
                    m_lastEvents.contactedActorIndices.end(),
                    actorIndex) == m_lastEvents.contactedActorIndices.end())
            {
                m_lastEvents.contactedActorIndices.push_back(actorIndex);
            }
        }

        if (!previousState.airborne && m_state.airborne)
        {
            m_startedFallingEventSeconds = EventHoldSeconds;
        }

        if (m_state.landedThisFrame)
        {
            m_landedEventSeconds = EventHoldSeconds;
        }

        if (!previousState.supportOnWater && m_state.supportOnWater)
        {
            m_enteredWaterEventSeconds = EventHoldSeconds;
        }

        if (previousState.supportOnWater && !m_state.supportOnWater)
        {
            m_leftWaterEventSeconds = EventHoldSeconds;
        }

        if (!previousState.supportOnBurning && m_state.supportOnBurning)
        {
            m_enteredBurningEventSeconds = EventHoldSeconds;
        }

        if (previousState.supportOnBurning && !m_state.supportOnBurning)
        {
            m_leftBurningEventSeconds = EventHoldSeconds;
        }

        if (m_state.landedThisFrame)
        {
            m_lastEvents.landingFallDistance = std::max(m_lastEvents.landingFallDistance, m_state.fallDistance);
        }

        if (pPerformanceDiagnostics != nullptr)
        {
            pPerformanceDiagnostics->movementContactsNanoseconds += SDL_GetTicksNS() - contactsBeginTickCount;
        }

        m_movementAccumulatorSeconds -= OutdoorMovementStepSeconds;
    }

    const uint64_t consequencesBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
    m_lastEvents.startedFalling = m_startedFallingEventSeconds > 0.0f;
    m_lastEvents.landed = m_landedEventSeconds > 0.0f;
    m_lastEvents.enteredWater = m_enteredWaterEventSeconds > 0.0f;
    m_lastEvents.leftWater = m_leftWaterEventSeconds > 0.0f;
    m_lastEvents.enteredBurning = m_enteredBurningEventSeconds > 0.0f;
    m_lastEvents.leftBurning = m_leftBurningEventSeconds > 0.0f;
    m_lastEvents.hardLanding = m_lastEvents.landed && m_lastEvents.landingFallDistance > HardLandingDistance;

    if (m_partyMovementState.flying || m_partyMovementState.featherFall)
    {
        m_state.fallStartZ = m_state.footZ;
        m_state.fallDistance = 0.0f;
    }

    if (!input.turnBasedPhysicsStep
        && m_state.supportOnWater
        && !m_partyMovementState.waterWalk
        && !m_partyMovementState.flying)
    {
        m_waterDamageTimerSeconds += deltaSeconds;

        while (m_waterDamageTimerSeconds >= DamageTickSeconds)
        {
            m_waterDamageConsequenceSeconds = EventHoldSeconds;
            m_pendingEffects.waterDamageTicks += 1;
            m_waterDamageTimerSeconds -= DamageTickSeconds;
        }
    }
    else
    {
        m_waterDamageTimerSeconds = 0.0f;
    }

    if (!input.turnBasedPhysicsStep && m_state.supportOnBurning && !m_partyMovementState.flying)
    {
        m_burningDamageTimerSeconds += deltaSeconds;

        while (m_burningDamageTimerSeconds >= DamageTickSeconds)
        {
            m_burningDamageConsequenceSeconds = EventHoldSeconds;
            m_pendingEffects.burningDamageTicks += 1;
            m_burningDamageTimerSeconds -= DamageTickSeconds;
        }
    }
    else
    {
        m_burningDamageTimerSeconds = 0.0f;
    }

    if (m_lastEvents.landed)
    {
        m_landingSoundConsequenceSeconds = EventHoldSeconds;
        m_lastConsequences.fallDamageDistance = m_lastEvents.landingFallDistance;
        m_pendingEffects.playLandingSound = true;
    }

    if (m_lastEvents.hardLanding)
    {
        m_hardLandingSoundConsequenceSeconds = EventHoldSeconds;
        m_pendingEffects.playHardLandingSound = true;
    }

    if (m_lastEvents.landed && m_state.supportOnWater && m_lastEvents.landingFallDistance > 0.0f)
    {
        m_splashSoundConsequenceSeconds = EventHoldSeconds;
        m_pendingEffects.playSplashSound = true;
    }

    if (m_lastEvents.hardLanding
        && !m_partyMovementState.featherFall
        && !m_partyMovementState.flying)
    {
        m_fallDamageConsequenceSeconds = EventHoldSeconds;
        m_lastConsequences.fallDamageDistance = m_lastEvents.landingFallDistance;
        m_pendingEffects.maxFallDamageDistance =
            std::max(m_pendingEffects.maxFallDamageDistance, m_lastEvents.landingFallDistance);
    }

    m_lastConsequences.applyWaterDamage = m_waterDamageConsequenceSeconds > 0.0f;
    m_lastConsequences.applyBurningDamage = m_burningDamageConsequenceSeconds > 0.0f;
    m_lastConsequences.applyFallDamage = m_fallDamageConsequenceSeconds > 0.0f;
    m_lastConsequences.playSplashSound = m_splashSoundConsequenceSeconds > 0.0f;
    m_lastConsequences.playLandingSound = m_landingSoundConsequenceSeconds > 0.0f;
    m_lastConsequences.playHardLandingSound = m_hardLandingSoundConsequenceSeconds > 0.0f;

    if (m_lastEvents.landed)
    {
        m_partyMovementState.flying = false;
    }

    const float requestedMovementSpeedSquared =
        moveVelocityX * moveVelocityX + moveVelocityY * moveVelocityY + moveVelocityZ * moveVelocityZ;
    m_partyMovementState.activelyFlying =
        m_partyMovementState.flying
        && m_state.airborne
        && (requestedMovementSpeedSquared > 0.01f || input.flyUp || input.flyDown || flyHeightChangeRequested);

    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->movementConsequencesNanoseconds +=
            SDL_GetTicksNS() - consequencesBeginTickCount;
        pPerformanceDiagnostics->movementDriverNanoseconds += SDL_GetTicksNS() - totalBeginTickCount;
    }
}

const OutdoorMoveState &OutdoorMovementDriver::state() const
{
    return m_state;
}

const OutdoorMovementEvents &OutdoorMovementDriver::lastEvents() const
{
    return m_lastEvents;
}

const OutdoorMovementConsequences &OutdoorMovementDriver::lastConsequences() const
{
    return m_lastConsequences;
}

const OutdoorPartyMovementState &OutdoorMovementDriver::partyMovementState() const
{
    return m_partyMovementState;
}

const OutdoorMovementTuning &OutdoorMovementDriver::tuning() const
{
    return m_tuning;
}

const OutdoorMovementEffects &OutdoorMovementDriver::pendingEffects() const
{
    return m_pendingEffects;
}

OutdoorMovementEffects OutdoorMovementDriver::consumePendingEffects()
{
    const OutdoorMovementEffects effects = m_pendingEffects;
    m_pendingEffects = {};
    return effects;
}

void OutdoorMovementDriver::toggleRunning()
{
    m_partyMovementState.running = !m_partyMovementState.running;
}

void OutdoorMovementDriver::toggleFlying()
{
    if (!m_flyingAvailable)
    {
        return;
    }

    if (!m_partyMovementState.flying && !canActivateFlying())
    {
        return;
    }

    m_partyMovementState.flying = !m_partyMovementState.flying;

    if (m_partyMovementState.flying)
    {
        m_state.verticalVelocity = 0.0f;
        m_state.fallStartZ = m_state.footZ;
        m_state.fallDistance = 0.0f;
    }
}

void OutdoorMovementDriver::toggleWaterWalk()
{
    m_partyMovementState.waterWalk = !m_partyMovementState.waterWalk;
}

void OutdoorMovementDriver::toggleFeatherFall()
{
    m_partyMovementState.featherFall = !m_partyMovementState.featherFall;

    if (m_partyMovementState.featherFall)
    {
        m_state.fallStartZ = m_state.footZ;
        m_state.fallDistance = 0.0f;
    }
}

void OutdoorMovementDriver::setFlying(bool active)
{
    if (active && !canActivateFlying())
    {
        return;
    }

    m_partyMovementState.flying = active;
    if (!active)
    {
        m_pendingFlyHeightDelta = 0.0f;
    }

    if (m_partyMovementState.flying)
    {
        m_state.verticalVelocity = 0.0f;
        m_state.fallStartZ = m_state.footZ;
        m_state.fallDistance = 0.0f;
    }
}

void OutdoorMovementDriver::setFlyingAvailable(bool active)
{
    m_flyingAvailable = active;

    if (!m_flyingAvailable)
    {
        m_partyMovementState.flying = false;
        m_pendingFlyHeightDelta = 0.0f;
    }
}

void OutdoorMovementDriver::setRunning(bool active)
{
    m_partyMovementState.running = active;
}

void OutdoorMovementDriver::setWaterWalkActive(bool active)
{
    m_partyMovementState.waterWalk = active;
}

void OutdoorMovementDriver::setFeatherFallActive(bool active)
{
    m_partyMovementState.featherFall = active;

    if (m_partyMovementState.featherFall)
    {
        m_state.fallStartZ = m_state.footZ;
        m_state.fallDistance = 0.0f;
    }
}

void OutdoorMovementDriver::setSpeedMultiplier(float multiplier)
{
    m_speedMultiplier = std::clamp(multiplier, 0.1f, 20.0f);
}

void OutdoorMovementDriver::setBodyDimensions(float radius, float height, float maxStepHeight)
{
    m_bodyDimensions.radius = radius;
    m_bodyDimensions.height = height;
    m_bodyDimensions.maxStepHeight = maxStepHeight;
}

void OutdoorMovementDriver::setCollisionTraceEnabled(bool enabled, std::string mapName)
{
    const bool wasEnabled = m_collisionTraceEnabled;
    const std::string previousMapName = m_collisionTraceMapName;
    m_collisionTraceEnabled = enabled;
    m_collisionTraceMapName = std::move(mapName);
    m_collisionTraceClockSeconds = 0.0f;
    m_nextCollisionTraceSeconds = 0.0f;

    if (enabled && (!wasEnabled || m_collisionTraceMapName != previousMapName))
    {
        gameplayDebugTraceWrite("outdoor_collision_trace_enabled map=\"" + m_collisionTraceMapName + "\"");
    }
}

void OutdoorMovementDriver::requestJump(std::optional<float> verticalVelocity, float lift)
{
    m_pendingJumpPress = true;
    m_pendingJumpVelocity = verticalVelocity;
    m_pendingJumpLift = std::max(1.0f, lift);
}

void OutdoorMovementDriver::requestSpecialJump(float velocityX, float velocityY, float velocityZ)
{
    m_pendingImpulseVelocityX = velocityX;
    m_pendingImpulseVelocityY = velocityY;
    m_pendingImpulseVelocityZ = velocityZ;
}

void OutdoorMovementDriver::setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders)
{
    m_movementController.setActorColliders(actorColliders);
}

void OutdoorMovementDriver::setFaceAttributes(size_t bModelIndex, size_t faceIndex, uint32_t attributes)
{
    m_movementController.setFaceAttributes(bModelIndex, faceIndex, attributes);
}

void OutdoorMovementDriver::updateFaceGeometries(const std::vector<OutdoorFaceGeometryData> &geometries)
{
    m_movementController.updateFaceGeometries(geometries);
}

bool OutdoorMovementDriver::translateWithSupportedBModel(
    size_t bModelIndex,
    float deltaX,
    float deltaY,
    float deltaZ)
{
    if (m_partyMovementState.flying
        || m_state.airborne
        || m_state.supportKind != OutdoorSupportKind::BModelFace
        || m_state.supportBModelIndex != bModelIndex)
    {
        return false;
    }

    m_state.x += deltaX;
    m_state.y += deltaY;
    m_state.footZ += deltaZ;
    m_state.fallStartZ += deltaZ;
    return true;
}

bool OutdoorMovementDriver::canActivateFlying() const
{
    return m_flyingAvailable && m_state.footZ <= m_tuning.maxFlightHeight;
}

}
