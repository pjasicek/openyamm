#include "game/indoor/IndoorPartyRuntime.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float GameMinutesPerRealSecond = 0.5f;
constexpr float GameSecondsPerRealSecond = GameMinutesPerRealSecond * 60.0f;
constexpr float IndoorMovementStepSeconds = 1.0f / 128.0f;
constexpr float DamageTickSeconds = 1.0f;
constexpr float FallDamageDistance = 512.0f;
constexpr float MaxAccumulatedMovementSeconds = 0.1f;
constexpr float DefaultJumpVelocity = 420.0f;

const char *indoorMoveBlockKindName(IndoorMoveBlockKind kind)
{
    switch (kind)
    {
        case IndoorMoveBlockKind::None:
            return "none";
        case IndoorMoveBlockKind::Wall:
            return "wall";
        case IndoorMoveBlockKind::Actor:
            return "actor";
        case IndoorMoveBlockKind::Party:
            return "party";
        case IndoorMoveBlockKind::InvalidPosition:
            return "invalid_position";
    }

    return "unknown";
}

std::string indoorCollisionTracePoint(const bx::Vec3 &point)
{
    std::ostringstream out;
    out << "(" << point.x << "," << point.y << "," << point.z << ")";
    return out.str();
}
}

IndoorPartyRuntime::IndoorPartyRuntime(IndoorMovementController movementController, const ItemTable &itemTable)
    : m_movementController(std::move(movementController))
{
    m_party.setItemTable(&itemTable);
}

void IndoorPartyRuntime::initializeEyePosition(float x, float y, float z, bool resetParty)
{
    if (resetParty)
    {
        m_party.reset();
    }

    const IndoorBodyDimensions body = {};
    m_movementState = m_movementController.initializeStateFromEyePosition(x, y, z, body);
    m_movementAccumulatorSeconds = 0.0f;
    m_pendingJumpRequested = false;
    m_pendingImpulseVelocityX = 0.0f;
    m_pendingImpulseVelocityY = 0.0f;
    m_pendingImpulseVelocityZ = 0.0f;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = 1.0f;
    m_burningDamageTimerSeconds = 0.0f;
}

void IndoorPartyRuntime::initializePartyPosition(float x, float y, float z, bool resetParty)
{
    const IndoorBodyDimensions body = {};
    initializeEyePosition(x, y, z + body.height, resetParty);
}

void IndoorPartyRuntime::teleportEyePosition(float x, float y, float z)
{
    const IndoorBodyDimensions body = {};
    m_movementState = m_movementController.initializeStateFromEyePosition(x, y, z, body);
    m_movementAccumulatorSeconds = 0.0f;
    m_pendingJumpRequested = false;
    m_pendingImpulseVelocityX = 0.0f;
    m_pendingImpulseVelocityY = 0.0f;
    m_pendingImpulseVelocityZ = 0.0f;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = 1.0f;
    m_burningDamageTimerSeconds = 0.0f;
}

void IndoorPartyRuntime::teleportPartyPosition(float x, float y, float z)
{
    const IndoorBodyDimensions body = {};
    m_movementState = m_movementController.initializeStateFromEyePosition(x, y, z + body.height, body);
    m_movementAccumulatorSeconds = 0.0f;
    m_pendingJumpRequested = false;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = 1.0f;
    m_burningDamageTimerSeconds = 0.0f;
}

void IndoorPartyRuntime::translatePartyPosition(float deltaX, float deltaY, float deltaZ)
{
    m_movementState.x += deltaX;
    m_movementState.y += deltaY;
    m_movementState.footZ += deltaZ;
    m_movementState.verticalVelocity = 0.0f;
    m_movementState.grounded = true;
    m_movementState.landedThisFrame = false;
    m_movementState.fallStartZ = m_movementState.footZ;
    m_movementState.fallDistance = 0.0f;
}

void IndoorPartyRuntime::update(
    float desiredVelocityX,
    float desiredVelocityY,
    bool jumpRequested,
    bool running,
    float deltaSeconds,
    bool turnBasedMovementStep)
{
    m_movementStatusText.clear();

    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    m_party.updateRecovery(deltaSeconds, running ? 0.5f : 1.0f);
    m_party.advanceTimedStates(deltaSeconds * GameSecondsPerRealSecond);

    const IndoorBodyDimensions body = {};
    m_pendingJumpRequested = m_pendingJumpRequested || jumpRequested;
    const float maxAccumulatedMovementSeconds =
        turnBasedMovementStep ? std::max(deltaSeconds, MaxAccumulatedMovementSeconds) : MaxAccumulatedMovementSeconds;
    m_movementAccumulatorSeconds =
        std::min(m_movementAccumulatorSeconds + deltaSeconds, maxAccumulatedMovementSeconds);
    const float impulseVelocityX = m_pendingImpulseVelocityX;
    const float impulseVelocityY = m_pendingImpulseVelocityY;
    const float impulseVelocityZ = m_pendingImpulseVelocityZ;
    const bool hasPendingImpulse =
        impulseVelocityX != 0.0f || impulseVelocityY != 0.0f || impulseVelocityZ != 0.0f;
    float landingFallDistance = 0.0f;

    if (hasPendingImpulse)
    {
        m_movementState.verticalVelocity = std::max(m_movementState.verticalVelocity, impulseVelocityZ);
        m_pendingImpulseVelocityX = 0.0f;
        m_pendingImpulseVelocityY = 0.0f;
        m_pendingImpulseVelocityZ = 0.0f;
    }

    while (m_movementAccumulatorSeconds >= IndoorMovementStepSeconds)
    {
        m_collisionTraceClockSeconds += IndoorMovementStepSeconds;
        const IndoorMoveState previousMovementState = m_movementState;
        const float jumpVelocityThisStep = m_pendingJumpVelocity.value_or(DefaultJumpVelocity);
        const float jumpLiftThisStep = m_pendingJumpLift;
        IndoorMoveDebugInfo debugInfo = {};
        IndoorMoveDebugInfo *pDebugInfo = m_collisionTraceEnabled ? &debugInfo : nullptr;
        m_movementState = m_movementController.resolveMove(
            m_movementState,
            body,
            desiredVelocityX * m_movementSpeedMultiplier + impulseVelocityX,
            desiredVelocityY * m_movementSpeedMultiplier + impulseVelocityY,
            m_pendingJumpRequested,
            IndoorMovementStepSeconds,
            nullptr,
            std::nullopt,
            true,
            pDebugInfo,
            false,
            false,
            jumpVelocityThisStep,
            jumpLiftThisStep);
        if (m_movementState.landedThisFrame)
        {
            landingFallDistance = std::max(landingFallDistance, m_movementState.fallDistance);
        }
        if (m_collisionTraceEnabled)
        {
            const IndoorCollisionTraceInfo traceInfo =
                m_movementController.traceCollisionIssues(previousMovementState, m_movementState, body);
            const float deltaX = m_movementState.x - previousMovementState.x;
            const float deltaY = m_movementState.y - previousMovementState.y;
            const float deltaZ = m_movementState.footZ - previousMovementState.footZ;
            const float horizontalDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY);
            const bool sectorChangedWithoutPortal =
                traceInfo.sectorChanged && !traceInfo.sectorTransitionTouchedPortal;
            const bool acceptedThroughBlockingFace =
                debugInfo.fullMoveSucceeded && traceInfo.crossedBlockingFace;
            const bool suspiciousSupportLoss =
                traceInfo.supportLost
                && !m_pendingJumpRequested
                && previousMovementState.verticalVelocity <= 0.0f;
            const bool suspicious =
                acceptedThroughBlockingFace
                || sectorChangedWithoutPortal
                || traceInfo.suddenDrop
                || suspiciousSupportLoss;
            const bool periodicProbe = m_collisionTraceClockSeconds >= m_nextCollisionTraceSeconds;

            if ((suspicious || periodicProbe) && m_collisionTraceClockSeconds >= m_nextCollisionTraceSeconds)
            {
                const std::string probeDetails =
                    m_movementController.buildCollisionTraceProbeDetails(previousMovementState, m_movementState, body);
                std::ostringstream out;
                out << "indoor_collision_trace"
                    << " map=\"" << m_collisionTraceMapName << "\""
                    << " reason=" << (suspicious ? "suspicious" : "periodic")
                    << " start=(" << previousMovementState.x
                    << "," << previousMovementState.y
                    << "," << previousMovementState.footZ << ")"
                    << " end=(" << m_movementState.x
                    << "," << m_movementState.y
                    << "," << m_movementState.footZ << ")"
                    << " delta=(" << deltaX << "," << deltaY << "," << deltaZ << ")"
                    << " horizontal_distance=" << horizontalDistance
                    << " start_sector=" << previousMovementState.sectorId
                    << " end_sector=" << m_movementState.sectorId
                    << " start_eye_sector=" << previousMovementState.eyeSectorId
                    << " end_eye_sector=" << m_movementState.eyeSectorId
                    << " start_grounded=" << (previousMovementState.grounded ? "true" : "false")
                    << " end_grounded=" << (m_movementState.grounded ? "true" : "false")
                    << " start_support=" << previousMovementState.supportFaceIndex
                    << " end_support=" << m_movementState.supportFaceIndex
                    << " start_velocity_z=" << previousMovementState.verticalVelocity
                    << " end_velocity_z=" << m_movementState.verticalVelocity
                    << " requested_velocity=("
                    << desiredVelocityX * m_movementSpeedMultiplier + impulseVelocityX
                    << "," << desiredVelocityY * m_movementSpeedMultiplier + impulseVelocityY << ")"
                    << " jump_requested=" << (m_pendingJumpRequested ? "true" : "false")
                    << " debug_block=" << indoorMoveBlockKindName(debugInfo.primaryBlockKind)
                    << " full_succeeded=" << (debugInfo.fullMoveSucceeded ? "true" : "false")
                    << " response_tried=" << (debugInfo.collisionResponseTried ? "true" : "false")
                    << " response_succeeded=" << (debugInfo.collisionResponseSucceeded ? "true" : "false")
                    << " hit_face=" << debugInfo.hitFaceIndex
                    << " hit_normal=" << indoorCollisionTracePoint(debugInfo.hitNormal)
                    << " hit_point=" << indoorCollisionTracePoint(debugInfo.hitPoint)
                    << " hit_move=" << debugInfo.hitMoveDistance
                    << " hit_adjusted=" << debugInfo.hitAdjustedMoveDistance
                    << " hit_height_offset=" << debugInfo.hitHeightOffset
                    << " response_step=" << indoorCollisionTracePoint(debugInfo.responseStep)
                    << " crossed_blocking_face=" << (traceInfo.crossedBlockingFace ? "true" : "false")
                    << " blocking_face=" << traceInfo.blockingFaceIndex
                    << " blocking_face_normal=" << indoorCollisionTracePoint(traceInfo.blockingFaceNormal)
                    << " blocking_face_point=" << indoorCollisionTracePoint(traceInfo.blockingFacePoint)
                    << " blocking_face_move=" << traceInfo.blockingFaceMoveDistance
                    << " blocking_face_adjusted_move=" << traceInfo.blockingFaceAdjustedMoveDistance
                    << " sector_changed=" << (traceInfo.sectorChanged ? "true" : "false")
                    << " sector_transition_portal="
                    << (traceInfo.sectorTransitionTouchedPortal ? "true" : "false")
                    << " portal_face=" << traceInfo.portalFaceIndex
                    << " support_lost=" << (traceInfo.supportLost ? "true" : "false")
                    << " sudden_drop=" << (traceInfo.suddenDrop ? "true" : "false")
                    << probeDetails;
                gameplayDebugTraceWrite(out.str());
                m_nextCollisionTraceSeconds = m_collisionTraceClockSeconds + 1.0f;
            }
        }
        m_pendingJumpRequested = false;
        m_pendingJumpVelocity.reset();
        m_pendingJumpLift = 1.0f;
        m_movementAccumulatorSeconds -= IndoorMovementStepSeconds;
    }

    OutdoorMovementEffects effects = {};
    const bool featherFallActive = m_party.hasPartyBuff(PartyBuffId::FeatherFall);

    if (landingFallDistance > FallDamageDistance && !featherFallActive)
    {
        effects.maxFallDamageDistance = landingFallDistance;
    }

    if (featherFallActive)
    {
        m_movementState.landedThisFrame = false;
        m_movementState.fallStartZ = m_movementState.footZ;
        m_movementState.fallDistance = 0.0f;
    }
    else if (landingFallDistance > 0.0f)
    {
        m_movementState.landedThisFrame = true;
        m_movementState.fallDistance = landingFallDistance;
    }

    if (m_movementState.grounded && m_movementController.supportFaceIsBurning(m_movementState.supportFaceIndex))
    {
        m_burningDamageTimerSeconds += deltaSeconds;

        while (m_burningDamageTimerSeconds >= DamageTickSeconds)
        {
            effects.burningDamageTicks += 1;
            m_burningDamageTimerSeconds -= DamageTickSeconds;
        }

        if (effects.burningDamageTicks > 0)
        {
            m_movementStatusText = "You are burning!";
        }
    }
    else
    {
        m_burningDamageTimerSeconds = 0.0f;
    }

    m_party.applyMovementEffects(effects);
}

void IndoorPartyRuntime::setActorColliders(const std::vector<IndoorActorCollision> &actorColliders)
{
    m_movementController.setActorColliders(actorColliders);
}

void IndoorPartyRuntime::setDecorationColliders(const std::vector<IndoorCylinderCollision> &decorationColliders)
{
    m_movementController.setDecorationColliders(decorationColliders);
}

void IndoorPartyRuntime::setSpriteObjectColliders(const std::vector<IndoorCylinderCollision> &spriteObjectColliders)
{
    m_movementController.setSpriteObjectColliders(spriteObjectColliders);
}

void IndoorPartyRuntime::applyMechanismGeometryUpdate(const std::vector<uint32_t> &changedDoorIds)
{
    m_movementController.applyMechanismGeometryUpdate(changedDoorIds);
}

void IndoorPartyRuntime::invalidateRuntimeGeometryCache()
{
    m_movementController.invalidateRuntimeGeometryCache();
}

const IndoorMoveState &IndoorPartyRuntime::movementState() const
{
    return m_movementState;
}

const Party &IndoorPartyRuntime::party() const
{
    return m_party;
}

Party &IndoorPartyRuntime::party()
{
    return m_party;
}

const std::string &IndoorPartyRuntime::movementStatusText() const
{
    return m_movementStatusText;
}

float IndoorPartyRuntime::partyX() const
{
    return m_movementState.x;
}

float IndoorPartyRuntime::partyY() const
{
    return m_movementState.y;
}

float IndoorPartyRuntime::partyFootZ() const
{
    return m_movementState.footZ;
}

void IndoorPartyRuntime::setParty(const Party &party)
{
    m_party = party;
}

IndoorPartyRuntime::Snapshot IndoorPartyRuntime::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.movementState = m_movementState;
    snapshot.movementAccumulatorSeconds = m_movementAccumulatorSeconds;
    snapshot.pendingJumpRequested = m_pendingJumpRequested;
    snapshot.pendingImpulseVelocityX = m_pendingImpulseVelocityX;
    snapshot.pendingImpulseVelocityY = m_pendingImpulseVelocityY;
    snapshot.pendingImpulseVelocityZ = m_pendingImpulseVelocityZ;
    snapshot.alwaysRunEnabled = m_alwaysRunEnabled;
    return snapshot;
}

void IndoorPartyRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    m_movementState = snapshot.movementState;
    m_movementAccumulatorSeconds = snapshot.movementAccumulatorSeconds;
    m_pendingJumpRequested = snapshot.pendingJumpRequested;
    m_pendingImpulseVelocityX = snapshot.pendingImpulseVelocityX;
    m_pendingImpulseVelocityY = snapshot.pendingImpulseVelocityY;
    m_pendingImpulseVelocityZ = snapshot.pendingImpulseVelocityZ;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = 1.0f;
    m_burningDamageTimerSeconds = 0.0f;
    m_alwaysRunEnabled = snapshot.alwaysRunEnabled;
    m_movementController.invalidateRuntimeGeometryCache();
}

void IndoorPartyRuntime::setMovementSpeedMultiplier(float multiplier)
{
    m_movementSpeedMultiplier = multiplier;
}

void IndoorPartyRuntime::setAlwaysRunEnabled(bool enabled)
{
    m_alwaysRunEnabled = enabled;
}

void IndoorPartyRuntime::setCollisionTraceEnabled(bool enabled, std::string mapName)
{
    const bool wasEnabled = m_collisionTraceEnabled;
    const std::string previousMapName = m_collisionTraceMapName;
    m_collisionTraceEnabled = enabled;
    m_collisionTraceMapName = std::move(mapName);
    m_collisionTraceClockSeconds = 0.0f;
    m_nextCollisionTraceSeconds = 0.0f;

    if (enabled && (!wasEnabled || m_collisionTraceMapName != previousMapName))
    {
        gameplayDebugTraceWrite("indoor_collision_trace_enabled map=\"" + m_collisionTraceMapName + "\"");
    }
}

bool IndoorPartyRuntime::alwaysRunEnabled() const
{
    return m_alwaysRunEnabled;
}

void IndoorPartyRuntime::syncSpellMovementStatesFromPartyBuffs()
{
}

void IndoorPartyRuntime::requestJump(std::optional<float> verticalVelocity, float lift)
{
    m_pendingJumpRequested = true;
    m_pendingJumpVelocity = verticalVelocity;
    m_pendingJumpLift = std::max(1.0f, lift);
}

void IndoorPartyRuntime::requestSpecialJump(float velocityX, float velocityY, float velocityZ)
{
    m_pendingImpulseVelocityX = velocityX;
    m_pendingImpulseVelocityY = velocityY;
    m_pendingImpulseVelocityZ = velocityZ;
}
}
