#include "game/indoor/IndoorPartyRuntime.h"
#include "engine/Localization.h"
#include "game/indoor/IndoorMovers.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <utility>
#include <vector>

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
constexpr float DefaultJumpVelocity = 480.0f;
constexpr float DefaultJumpLift = 0.0f;
// A floor this close to the party's feet over a ladder's hold spot covers the ladder's top (no grab there).
constexpr float LadderCoverRise = 32.0f;
constexpr float LadderCoverDrop = 32.0f;
constexpr float PartyGravityPerSecond = 1280.0f;
// MM9's water sounds (worlds/mm9/audio): the eye goes under, comes out, a drowning tick.
constexpr const char *WaterSplashSound = "events/watersplash.wav";
constexpr const char *WaterOutSound = "events/out_water.wav";
constexpr const char *DrowningSounds[] = {"events/drown01.wav", "events/drown02.wav"};

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

const char *indoorMoveInvalidPositionReasonName(IndoorMoveInvalidPositionReason reason)
{
    switch (reason)
    {
        case IndoorMoveInvalidPositionReason::None:
            return "none";
        case IndoorMoveInvalidPositionReason::ActorLedgeDrop:
            return "actor_ledge_drop";
        case IndoorMoveInvalidPositionReason::LeadingActorLedgeDrop:
            return "leading_actor_ledge_drop";
        case IndoorMoveInvalidPositionReason::SteepFloor:
            return "steep_floor";
        case IndoorMoveInvalidPositionReason::StepUpTooHigh:
            return "step_up_too_high";
        case IndoorMoveInvalidPositionReason::CeilingFloorCrush:
            return "ceiling_floor_crush";
        case IndoorMoveInvalidPositionReason::MissingEyeSector:
            return "missing_eye_sector";
        case IndoorMoveInvalidPositionReason::FaceCollision:
            return "face_collision";
        case IndoorMoveInvalidPositionReason::ActorCollision:
            return "actor_collision";
        case IndoorMoveInvalidPositionReason::UnsupportedStepUp:
            return "unsupported_step_up";
    }

    return "unknown";
}

std::string indoorCollisionTracePoint(const bx::Vec3 &point)
{
    std::ostringstream out;
    out << "(" << point.x << "," << point.y << "," << point.z << ")";
    return out.str();
}

void recordSteppedFloorFace(std::vector<size_t> &faces, const IndoorMoveState &state)
{
    // Bounded in case nothing consumes the faces; a frame crosses only a few.
    constexpr size_t MaximumSteppedFloorFaces = 16;

    if (!state.grounded
        || state.supportFaceIndex == static_cast<size_t>(-1)
        || (!faces.empty() && faces.back() == state.supportFaceIndex))
    {
        return;
    }

    if (faces.size() >= MaximumSteppedFloorFaces)
    {
        faces.erase(faces.begin());
    }

    faces.push_back(state.supportFaceIndex);
}
}

IndoorPartyRuntime::IndoorPartyRuntime(IndoorMovementController movementController, const ItemTable &itemTable)
    : m_movementController(std::move(movementController))
{
    // MM6-MM8's party climbs any slope; an MM9 open-air map's scene blocks it at the monsters' limit (its cliffs).
    const IndoorMapData *pMapData = m_movementController.indoorMapData();
    m_movementController.setSlopeRule(
        pMapData != nullptr && pMapData->partySteepSlopesBlock ? IndoorSlopeRule::Actor : IndoorSlopeRule::Party);
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
    keepPlacementInWater(z - body.height, body);
    m_movementAccumulatorSeconds = 0.0f;
    m_pendingJumpRequested = false;
    m_pendingImpulseVelocityX = 0.0f;
    m_pendingImpulseVelocityY = 0.0f;
    m_pendingImpulseVelocityZ = 0.0f;
    m_jumpCarryVelocityX = 0.0f;
    m_jumpCarryVelocityY = 0.0f;
    m_dashSeconds = 0.0f;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = DefaultJumpLift;
    m_burningDamageTimerSeconds = 0.0f;
    resetWaterState(true);
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
    keepPlacementInWater(z - body.height, body);
    m_movementAccumulatorSeconds = 0.0f;
    m_pendingJumpRequested = false;
    m_pendingImpulseVelocityX = 0.0f;
    m_pendingImpulseVelocityY = 0.0f;
    m_pendingImpulseVelocityZ = 0.0f;
    m_jumpCarryVelocityX = 0.0f;
    m_jumpCarryVelocityY = 0.0f;
    m_dashSeconds = 0.0f;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = DefaultJumpLift;
    m_burningDamageTimerSeconds = 0.0f;
    resetWaterState(false);
}

void IndoorPartyRuntime::teleportPartyPosition(float x, float y, float z)
{
    const IndoorBodyDimensions body = {};
    m_movementState = m_movementController.initializeStateFromEyePosition(x, y, z + body.height, body);
    keepPlacementInWater(z, body);
    m_movementAccumulatorSeconds = 0.0f;
    m_pendingJumpRequested = false;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = DefaultJumpLift;
    m_burningDamageTimerSeconds = 0.0f;
    m_ladderGlide.reset();
    resetWaterState(false);
}

bool IndoorPartyRuntime::partyFitsAt(float x, float y, float footZ) const
{
    // One unit up, so the floor the point stands on does not count as a face the body is in.
    const IndoorBodyDimensions body = {};
    return m_movementController.airborneStateAt(x, y, footZ + 1.0f, body).has_value();
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

void IndoorPartyRuntime::pushPartyPosition(float deltaX, float deltaY, float deltaZ)
{
    m_movementState.x += deltaX;
    m_movementState.y += deltaY;
    m_movementState.footZ += deltaZ;
    m_movementState.verticalVelocity = std::min(m_movementState.verticalVelocity, 0.0f);
    m_movementState.grounded = false;
    m_movementState.supportFaceIndex = static_cast<size_t>(-1);
    m_movementState.landedThisFrame = false;
    m_movementState.fallStartZ = std::max(m_movementState.fallStartZ, m_movementState.footZ);
}

void IndoorPartyRuntime::lift(float height)
{
    m_movementState.footZ += height;
    m_movementState.verticalVelocity = 0.0f;
    m_movementState.grounded = false;
    m_movementState.landedThisFrame = false;
    m_movementState.fallStartZ = m_movementState.footZ;
    m_movementState.fallDistance = 0.0f;
}

void IndoorPartyRuntime::setLadderVerticalInput(int verticalInput)
{
    m_ladderVerticalInput = verticalInput;
}

bool IndoorPartyRuntime::climbingLadder() const
{
    return m_ladderIndex.has_value() || m_ladderGlide.has_value();
}

void IndoorPartyRuntime::startLadderGlide(float toX, float toY, float toFootZ, std::optional<size_t> ontoLadderIndex)
{
    // About walking speed, never so short that it reads as a jump.
    constexpr float GlideSpeed = 448.0f;
    constexpr float MinGlideSeconds = 0.2f;
    LadderGlide glide;
    glide.from = {m_movementState.x, m_movementState.y, m_movementState.footZ};
    glide.to = {toX, toY, toFootZ};
    // Across at the higher end's height, then down (onto a ladder), or up first, then across (off its top).
    glide.corner = glide.from[2] >= glide.to[2]
        ? std::array<float, 3>{glide.to[0], glide.to[1], glide.from[2]}
        : std::array<float, 3>{glide.from[0], glide.from[1], glide.to[2]};
    const float across = std::hypot(glide.to[0] - glide.from[0], glide.to[1] - glide.from[1]);
    const float vertical = std::fabs(glide.to[2] - glide.from[2]);
    glide.duration = std::max(MinGlideSeconds, (across + vertical) / GlideSpeed);
    glide.ontoLadderIndex = ontoLadderIndex;
    m_ladderGlide = glide;
    m_ladderIndex.reset();
    m_movementState.grounded = false;
    m_movementState.supportFaceIndex = static_cast<size_t>(-1);
    m_movementState.verticalVelocity = 0.0f;
    m_movementState.fallStartZ = m_movementState.footZ;
}

void IndoorPartyRuntime::stepLadderGlide(const IndoorBodyDimensions &body)
{
    LadderGlide &glide = *m_ladderGlide;
    glide.seconds += IndoorMovementStepSeconds;
    m_pendingJumpRequested = false;

    if (glide.seconds >= glide.duration)
    {
        const std::array<float, 3> to = glide.to;
        const std::optional<size_t> ontoLadderIndex = glide.ontoLadderIndex;
        m_ladderGlide.reset();

        if (!ontoLadderIndex)
        {
            teleportPartyPosition(to[0], to[1], to[2]);
            return;
        }

        const std::optional<IndoorMoveState> held = m_movementController.airborneStateAt(to[0], to[1], to[2], body);

        if (held)
        {
            m_movementState = *held;
        }

        m_movementState.x = to[0];
        m_movementState.y = to[1];
        m_movementState.footZ = to[2];
        m_movementState.fallStartZ = to[2];
        m_ladderIndex = ontoLadderIndex;
        return;
    }

    // Eased along the two legs by length.
    const float progress = glide.seconds / glide.duration;
    const float eased = progress * progress * (3.0f - 2.0f * progress);
    const auto legLength = [](const std::array<float, 3> &a, const std::array<float, 3> &b)
    {
        return std::sqrt((b[0] - a[0]) * (b[0] - a[0]) + (b[1] - a[1]) * (b[1] - a[1]) + (b[2] - a[2]) * (b[2] - a[2]));
    };
    const float first = legLength(glide.from, glide.corner);
    const float total = first + legLength(glide.corner, glide.to);
    const float travelled = eased * total;
    const bool onFirst = travelled <= first || total - first < 1.0e-3f;
    const std::array<float, 3> &start = onFirst ? glide.from : glide.corner;
    const std::array<float, 3> &end = onFirst ? glide.corner : glide.to;
    const float legFraction = onFirst
        ? (first > 1.0e-3f ? travelled / first : 1.0f)
        : (travelled - first) / (total - first);
    const float x = start[0] + (end[0] - start[0]) * legFraction;
    const float y = start[1] + (end[1] - start[1]) * legFraction;
    const float footZ = start[2] + (end[2] - start[2]) * legFraction;

    // Keep the sectors current where the body fits; a graze of the floor's edge on the way keeps the last ones.
    const std::optional<IndoorMoveState> placed = m_movementController.airborneStateAt(x, y, footZ, body);

    if (placed)
    {
        m_movementState = *placed;
    }

    m_movementState.x = x;
    m_movementState.y = y;
    m_movementState.footZ = footZ;
    m_movementState.grounded = false;
    m_movementState.verticalVelocity = 0.0f;
    m_movementState.fallStartZ = footZ;
    m_movementState.fallDistance = 0.0f;
}

bool IndoorPartyRuntime::stepOnLadder(
    float desiredVelocityX,
    float desiredVelocityY,
    bool runningMovement,
    const IndoorBodyDimensions &body,
    std::vector<size_t> &contactedActorIndices)
{
    const IndoorMapData *pMapData = m_movementController.indoorMapData();

    if (pMapData == nullptr || pMapData->ladders.empty())
    {
        return false;
    }

    if (m_ladderGlide)
    {
        stepLadderGlide(body);
        return true;
    }

    const IndoorMoverBody moverBody = {
        m_movementState.x, m_movementState.y, m_movementState.footZ, body.radius, body.height};

    if (!m_ladderIndex)
    {
        for (size_t index = 0; index < pMapData->ladders.size(); ++index)
        {
            const IndoorLadder &candidate = pMapData->ladders[index];

            // A swimming party takes hold of a ladder that reaches into its water (MM9: Beethoven's, Dook's Castle's).
            if (indoorLadderGrabAllowed(candidate, m_movementState.grounded || swimming(), m_pendingJumpRequested)
                && indoorLadderCanGrab(candidate, moverBody, desiredVelocityX, desiredVelocityY))
            {
                m_ladderIndex = index;
                break;
            }
        }
    }

    if (!m_ladderIndex && m_movementState.grounded && !m_pendingJumpRequested)
    {
        // Walking from a ladder's top exit toward its top: the body glides onto the strip just under the top.
        for (size_t index = 0; index < pMapData->ladders.size(); ++index)
        {
            const IndoorLadder &candidate = pMapData->ladders[index];

            if (!indoorLadderCanGrabAtTop(candidate, moverBody, desiredVelocityX, desiredVelocityY))
            {
                continue;
            }

            const bx::Vec3 hold = indoorLadderTopEntryPosition(candidate, moverBody);

            // The way down is through a hole: a floor where the party stands over the hold spot (a shut trap's floor,
            // Anskram's pivot traps over their pits' ladders) covers the ladder.
            if (m_movementController.hasFloorAt(
                    hold.x, hold.y, m_movementState.footZ, LadderCoverRise, LadderCoverDrop))
            {
                continue;
            }

            const std::optional<IndoorMoveState> held =
                m_movementController.airborneStateAt(hold.x, hold.y, hold.z, body);

            if (held)
            {
                startLadderGlide(hold.x, hold.y, hold.z, index);
                stepLadderGlide(body);
                return true;
            }
        }
    }

    if (!m_ladderIndex)
    {
        return false;
    }

    const IndoorLadder &ladder = pMapData->ladders[*m_ladderIndex];
    const IndoorLadderClimbStep step = indoorLadderClimbStep(
        ladder,
        moverBody,
        desiredVelocityX,
        desiredVelocityY,
        m_ladderVerticalInput,
        runningMovement,
        IndoorMovementStepSeconds);

    if (m_pendingJumpRequested || step.detach)
    {
        // Letting go is not a fall from any height above here.
        m_ladderIndex.reset();
        m_movementState.fallStartZ = m_movementState.footZ;
        return false;
    }

    if (step.exitTop)
    {
        startLadderGlide(ladder.topExit[0], ladder.topExit[1], ladder.topExit[2], std::nullopt);
        stepLadderGlide(body);
        return true;
    }

    const float footBefore = m_movementState.footZ;
    IndoorMoveState climbing = m_movementState;
    climbing.grounded = false;
    climbing.supportFaceIndex = static_cast<size_t>(-1);
    climbing.verticalVelocity = step.verticalVelocity;
    m_movementState = m_movementController.resolveMove(
        climbing,
        body,
        step.velocityX,
        step.velocityY,
        false,
        IndoorMovementStepSeconds,
        &contactedActorIndices,
        std::nullopt,
        true,
        nullptr,
        true);
    m_movementState.verticalVelocity = 0.0f;
    m_movementState.fallStartZ = m_movementState.footZ;

    // Descending stops on the floor: the party stands there and walks on.
    const float expectedDrop = -step.verticalVelocity * IndoorMovementStepSeconds;

    if (expectedDrop > 0.0f && footBefore - m_movementState.footZ < expectedDrop * 0.25f)
    {
        m_ladderIndex.reset();
        m_movementState.grounded = true;
    }

    return true;
}

void IndoorPartyRuntime::update(
    float desiredVelocityX,
    float desiredVelocityY,
    bool jumpRequested,
    bool runningMovement,
    float deltaSeconds,
    bool turnBasedMovementStep,
    bool turnBasedPhysicsStep)
{
    m_movementStatusText.clear();
    m_runningMovement = runningMovement;

    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    // Turn-based walking spends the turn's movement points, not game time: the clock, buffs and regeneration
    // advance once per turn (TurnBasedCombatRuntime), as in the original.
    if (!turnBasedPhysicsStep && !turnBasedMovementStep)
    {
        // Running halves recovery speed, but only while the party actually runs.
        m_party.updateRecovery(deltaSeconds, runningMovement ? 0.5f : 1.0f);
        m_party.advanceTimedStates(deltaSeconds * GameSecondsPerRealSecond);
    }

    const IndoorBodyDimensions body = {};
    m_pendingJumpRequested = m_pendingJumpRequested || jumpRequested;
    const float maxAccumulatedMovementSeconds =
        turnBasedMovementStep ? std::max(deltaSeconds, MaxAccumulatedMovementSeconds) : MaxAccumulatedMovementSeconds;
    m_movementAccumulatorSeconds =
        std::min(m_movementAccumulatorSeconds + deltaSeconds, maxAccumulatedMovementSeconds);
    const bool hasPendingImpulse = m_pendingImpulseVelocityX != 0.0f || m_pendingImpulseVelocityY != 0.0f
        || m_pendingImpulseVelocityZ != 0.0f;
    float landingFallDistance = 0.0f;
    std::vector<size_t> contactedActorIndices;

    if (hasPendingImpulse)
    {
        m_movementState.verticalVelocity = std::max(m_movementState.verticalVelocity, m_pendingImpulseVelocityZ);
        m_jumpCarryVelocityX = m_pendingImpulseVelocityX;
        m_jumpCarryVelocityY = m_pendingImpulseVelocityY;
        m_pendingImpulseVelocityX = 0.0f;
        m_pendingImpulseVelocityY = 0.0f;
        m_pendingImpulseVelocityZ = 0.0f;
    }

    // The settings' speed, a ruleset's slow (MAW's dimension affix 25), a spell's speed-up (MM9's Fleet Foot) and
    // wading through a shallow liquid floor.
    const size_t supportFace = m_movementState.supportFaceIndex;
    const float wadeSpeed = m_movementState.grounded && supportFace < m_faceWadeSpeeds.size()
        ? m_faceWadeSpeeds[supportFace] : 1.0f;
    const float speedMultiplier = m_movementSpeedMultiplier * m_party.movementMultiplier() * wadeSpeed;
    // Scene water volumes (MM9's deep water): their tops where their movers stand now; nothing on any other map.
    const bool inWaterMap = waterActive();

    if (inWaterMap)
    {
        m_waterTopOffsets = indoorWaterTopOffsets(m_movementController.indoorMapData()->waterVolumes,
            m_movementController.indoorMapData()->vertices, m_movementController.runtimeVertices());
    }

    while (m_movementAccumulatorSeconds >= IndoorMovementStepSeconds)
    {
        m_collisionTraceClockSeconds += IndoorMovementStepSeconds;

        if (stepOnLadder(
                desiredVelocityX * speedMultiplier,
                desiredVelocityY * speedMultiplier,
                runningMovement,
                body,
                contactedActorIndices))
        {
            m_movementAccumulatorSeconds = std::max(0.0f, m_movementAccumulatorSeconds - IndoorMovementStepSeconds);
            continue;
        }

        if (inWaterMap
            && stepInWater(m_movementSpeedMultiplier * m_party.movementMultiplier(), body, contactedActorIndices))
        {
            recordSteppedFloorFace(m_steppedFloorFaces, m_movementState);
            m_pendingJumpRequested = false;
            m_pendingJumpVelocity.reset();
            m_pendingJumpLift = DefaultJumpLift;
            m_movementAccumulatorSeconds -= IndoorMovementStepSeconds;
            continue;
        }

        // A current carries a body that stands or falls in its water too (MM9 adds it to every mover's velocity).
        float currentX = 0.0f;
        float currentY = 0.0f;

        if (inWaterMap && m_swimState != IndoorSwimState::Dry)
        {
            if (const std::optional<IndoorWaterSample> water = bodyWaterSample(m_movementState, body))
            {
                const IndoorWaterVolume &volume =
                    m_movementController.indoorMapData()->waterVolumes[water->volumeIndex];
                currentX = volume.current[0];
                currentY = volume.current[1];
            }
        }

        const IndoorMoveState previousMovementState = m_movementState;
        const float jumpVelocityThisStep = m_pendingJumpVelocity.value_or(DefaultJumpVelocity);
        const float jumpLiftThisStep = m_pendingJumpLift;
        IndoorMoveDebugInfo debugInfo = {};
        IndoorMoveDebugInfo *pDebugInfo = m_collisionTraceEnabled ? &debugInfo : nullptr;
        const bool dashing = m_dashSeconds > 0.0f;
        m_dashSeconds = std::max(0.0f, m_dashSeconds - IndoorMovementStepSeconds);
        m_movementState = m_movementController.resolveMove(
            m_movementState,
            body,
            desiredVelocityX * speedMultiplier + m_jumpCarryVelocityX + (dashing ? m_dashVelocityX : 0.0f) + currentX,
            desiredVelocityY * speedMultiplier + m_jumpCarryVelocityY + (dashing ? m_dashVelocityY : 0.0f) + currentY,
            m_pendingJumpRequested,
            IndoorMovementStepSeconds,
            &contactedActorIndices,
            std::nullopt,
            true,
            pDebugInfo,
            false,
            false,
            jumpVelocityThisStep,
            jumpLiftThisStep,
            false,
            false,
            false,
            false,
            false,
            PartyGravityPerSecond);
        // Landing in water does not hurt (MM9 skips its landing path in water).
        if (m_movementState.landedThisFrame
            && !(inWaterMap && bodyWaterSample(m_movementState, body).has_value()))
        {
            landingFallDistance = std::max(landingFallDistance, m_movementState.fallDistance);
        }
        if (m_movementState.grounded && m_movementState.verticalVelocity <= 0.0f)
        {
            m_jumpCarryVelocityX = 0.0f;
            m_jumpCarryVelocityY = 0.0f;
        }
        recordSteppedFloorFace(m_steppedFloorFaces, m_movementState);
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
                    << desiredVelocityX * speedMultiplier + m_jumpCarryVelocityX
                    << "," << desiredVelocityY * speedMultiplier + m_jumpCarryVelocityY << ")"
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
                    << " invalid_reason="
                    << indoorMoveInvalidPositionReasonName(debugInfo.invalidPositionReason)
                    << " invalid_candidate="
                    << indoorCollisionTracePoint(debugInfo.invalidCandidatePosition)
                    << " invalid_floor_has=" << (debugInfo.invalidFloorHas ? "true" : "false")
                    << " invalid_floor=" << debugInfo.invalidFloorFaceIndex
                    << " invalid_floor_sector=" << debugInfo.invalidFloorSectorId
                    << " invalid_floor_height=" << debugInfo.invalidFloorHeight
                    << " invalid_floor_normal_z=" << debugInfo.invalidFloorNormalZ
                    << " invalid_leading_floor_has="
                    << (debugInfo.invalidLeadingFloorHas ? "true" : "false")
                    << " invalid_leading_floor=" << debugInfo.invalidLeadingFloorFaceIndex
                    << " invalid_leading_floor_sector=" << debugInfo.invalidLeadingFloorSectorId
                    << " invalid_leading_floor_height=" << debugInfo.invalidLeadingFloorHeight
                    << " invalid_leading_floor_normal_z=" << debugInfo.invalidLeadingFloorNormalZ
                    << " invalid_ceiling_has=" << (debugInfo.invalidCeilingHas ? "true" : "false")
                    << " invalid_ceiling_height=" << debugInfo.invalidCeilingHeight
                    << " invalid_eye_sector=" << debugInfo.invalidEyeSectorId
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
        m_pendingJumpLift = DefaultJumpLift;
        m_movementAccumulatorSeconds -= IndoorMovementStepSeconds;
    }

    if (!contactedActorIndices.empty() && m_party.hasPartyBuff(PartyBuffId::Invisibility))
    {
        m_party.clearPartyBuff(PartyBuffId::Invisibility);
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

    // A lava volume (scene water_volumes, liquid lava: MM9's Kato liquid, Drangheim Prison's Lava0) burns whoever is
    // in it, as a lava floor does; Levitate does not lift the party out of it.
    bool inLava = false;

    if (inWaterMap)
    {
        if (const std::optional<IndoorWaterSample> water = bodyWaterSample(m_movementState, body))
        {
            inLava = m_movementController.indoorMapData()->waterVolumes[water->volumeIndex].liquid
                == IndoorLiquid::Lava;
        }
    }

    // Levitate keeps the party just off the lava, as MM8 does in every world.
    if (inLava
        || (m_movementState.grounded
            && !m_party.hasPartyBuff(PartyBuffId::Levitate)
            && m_movementController.supportFaceIsBurning(m_movementState.supportFaceIndex)))
    {
        m_burningDamageTimerSeconds += deltaSeconds;

        while (m_burningDamageTimerSeconds >= DamageTickSeconds)
        {
            effects.burningDamageTicks += 1;
            m_burningDamageTimerSeconds -= DamageTickSeconds;
        }

        if (effects.burningDamageTicks > 0)
        {
            m_movementStatusText = Engine::tr("You are burning!");
        }
    }
    else
    {
        m_burningDamageTimerSeconds = 0.0f;
    }

    effects.indoor = !m_openAir;
    m_party.applyMovementEffects(effects);

    if (inWaterMap)
    {
        updateWaterBreath(deltaSeconds);
    }
}

bool IndoorPartyRuntime::waterActive() const
{
    const IndoorMapData *pMapData = m_movementController.indoorMapData();
    return pMapData != nullptr && !pMapData->waterVolumes.empty();
}

std::optional<IndoorWaterSample> IndoorPartyRuntime::bodyWaterSample(
    const IndoorMoveState &state,
    const IndoorBodyDimensions &body) const
{
    const IndoorMapData *pMapData = m_movementController.indoorMapData();

    if (pMapData == nullptr || pMapData->waterVolumes.empty())
    {
        return std::nullopt;
    }

    return indoorBodyWaterSample(pMapData->waterVolumes, m_waterTopOffsets, state.x, state.y, state.footZ, body.height);
}

bool IndoorPartyRuntime::stepInWater(
    float speedMultiplier,
    const IndoorBodyDimensions &body,
    std::vector<size_t> &contactedActorIndices)
{
    const IndoorMapData &mapData = *m_movementController.indoorMapData();
    const std::optional<IndoorWaterSample> bodyWater = bodyWaterSample(m_movementState, body);
    const float eyePointZ = m_movementState.eyeZ() - IndoorSwimEyePointDrop;
    const std::optional<IndoorWaterSample> eyeWater =
        indoorWaterAt(mapData.waterVolumes, m_waterTopOffsets, m_movementState.x, m_movementState.y, eyePointZ);
    IndoorSwimFacts facts = {};
    facts.bodyInWater = bodyWater.has_value() || eyeWater.has_value();
    facts.eyeUnder = eyeWater.has_value();
    facts.grounded = m_movementState.grounded;
    IndoorSwimState state = indoorSwimState(facts, m_swimMemory);

    if (state == IndoorSwimState::Surface && m_pendingJumpRequested)
    {
        // The jump out of the water (MM9 0x10099df0): the land jump's speed upward, gravity on, air control.
        m_swimMemory.surfaceJump = true;
        state = IndoorSwimState::SurfaceJump;
        m_movementState.verticalVelocity = IndoorSurfaceJumpVelocity;
        m_movementState.grounded = false;
        m_movementState.supportFaceIndex = static_cast<size_t>(-1);
    }
    else if (state == IndoorSwimState::Bed && m_swimInput.vertical > 0)
    {
        // Rising off the bed: MM9's land jump there leaves the floor and its UnderWater mover takes over at once.
        state = IndoorSwimState::Submerged;
    }

    m_swimState = state;
    std::array<float, 3> current = {0.0f, 0.0f, 0.0f};

    if (bodyWater)
    {
        current = mapData.waterVolumes[bodyWater->volumeIndex].current;
    }
    else if (eyeWater)
    {
        current = mapData.waterVolumes[eyeWater->volumeIndex].current;
    }

    if (state == IndoorSwimState::Submerged || state == IndoorSwimState::Surface)
    {
        const float surfaceZ = bodyWater ? bodyWater->surfaceZ : (eyeWater ? eyeWater->surfaceZ : eyePointZ);
        const IndoorSwimVelocity velocity = indoorSwimVelocity(
            state, m_swimInput, speedMultiplier, eyePointZ - surfaceZ, IndoorMovementStepSeconds);
        // Gravity off, no momentum: the step's velocity is the input's (MM9 sets it from zero each frame).
        IndoorMoveState swimming = m_movementState;
        swimming.grounded = false;
        swimming.supportFaceIndex = static_cast<size_t>(-1);
        swimming.verticalVelocity = velocity.z + current[2];
        m_movementState = m_movementController.resolveMove(
            swimming,
            body,
            velocity.x + current[0],
            velocity.y + current[1],
            false,
            IndoorMovementStepSeconds,
            &contactedActorIndices,
            std::nullopt,
            true,
            nullptr,
            false,
            false,
            DefaultJumpVelocity,
            DefaultJumpLift,
            false,
            false,
            false,
            false,
            false,
            0.0f);
        m_movementState.verticalVelocity = 0.0f;
        m_movementState.landedThisFrame = false;
        m_movementState.fallStartZ = m_movementState.footZ;
        m_movementState.fallDistance = 0.0f;
        return true;
    }

    if (state == IndoorSwimState::SurfaceJump)
    {
        const IndoorSwimVelocity air = indoorSurfaceJumpAirControl(m_swimInput, speedMultiplier);
        m_movementState = m_movementController.resolveMove(
            m_movementState,
            body,
            air.x + current[0],
            air.y + current[1],
            false,
            IndoorMovementStepSeconds,
            &contactedActorIndices,
            std::nullopt,
            true,
            nullptr,
            false,
            false,
            DefaultJumpVelocity,
            DefaultJumpLift,
            false,
            false,
            false,
            false,
            false,
            PartyGravityPerSecond);
        // Landing back in the water or on a rim: no fall damage.
        m_movementState.landedThisFrame = false;
        m_movementState.fallStartZ = m_movementState.footZ;
        m_movementState.fallDistance = 0.0f;
        return true;
    }

    return false;
}

void IndoorPartyRuntime::updateWaterBreath(float deltaSeconds)
{
    const IndoorMapData &mapData = *m_movementController.indoorMapData();
    const float eyePointZ = m_movementState.eyeZ() - IndoorSwimEyePointDrop;
    const std::optional<IndoorWaterSample> eyeWater =
        indoorWaterAt(mapData.waterVolumes, m_waterTopOffsets, m_movementState.x, m_movementState.y, eyePointZ);
    const bool eyeUnder = eyeWater.has_value();

    if (m_eyeUnderWaterKnown && eyeUnder != m_eyeUnderWater)
    {
        m_waterSounds.push_back(eyeUnder ? WaterSplashSound : WaterOutSound);
    }

    m_eyeUnderWater = eyeUnder;
    m_eyeUnderWaterKnown = true;
    m_eyeWaterVolumeIndex = eyeWater ? std::optional<size_t>(eyeWater->volumeIndex) : std::nullopt;

    if (m_ladderIndex)
    {
        m_swimState = IndoorSwimState::Dry;
    }

    const uint32_t ticks = advanceIndoorBreath(m_breath, eyeUnder, deltaSeconds);

    for (uint32_t tick = 0; tick < ticks; ++tick)
    {
        // MM9's tick (object.lto 0x100559c0): every member loses 1/6 of its maximum HP, through the ordinary damage
        // path (armour and resistances do not reduce it), then a drowning sound.
        for (size_t memberIndex = 0; memberIndex < m_party.members().size(); ++memberIndex)
        {
            m_party.applyDamageToMember(
                memberIndex, indoorDrowningDamage(m_party.members()[memberIndex].maxHealth), "", true);
        }

        m_waterSounds.push_back(DrowningSounds[m_drowningTicks % 2]);
        ++m_drowningTicks;
        m_movementStatusText = Engine::tr("You are drowning!");
    }
}

void IndoorPartyRuntime::keepPlacementInWater(float requestedFootZ, const IndoorBodyDimensions &body)
{
    // A party placed in deep water (a save made swimming, a teleport into a lake) stays where it was put instead of
    // standing on the bed under it.
    if (!waterActive() || requestedFootZ <= m_movementState.footZ + 1.0f)
    {
        return;
    }

    IndoorMoveState requested = m_movementState;
    requested.footZ = requestedFootZ;

    if (!bodyWaterSample(requested, body))
    {
        return;
    }

    if (const std::optional<IndoorMoveState> held =
            m_movementController.airborneStateAt(m_movementState.x, m_movementState.y, requestedFootZ, body))
    {
        m_movementState = *held;
        m_movementState.verticalVelocity = 0.0f;
        m_movementState.fallStartZ = requestedFootZ;
    }
}

void IndoorPartyRuntime::resetWaterState(bool refillBreath)
{
    // A party placed in deep water with its eye out is held at the surface (it counts as having been under).
    m_swimMemory = {};
    m_swimMemory.wasSubmerged = true;
    m_swimState = IndoorSwimState::Dry;
    m_eyeUnderWaterKnown = false;
    m_eyeUnderWater = false;
    m_eyeWaterVolumeIndex.reset();

    if (refillBreath)
    {
        m_breath = {};
        m_drowningTicks = 0;
    }

    if (!waterActive())
    {
        return;
    }

    // The state where the party now is (a load under water is under water at once, without a splash).
    const IndoorMapData &mapData = *m_movementController.indoorMapData();
    m_waterTopOffsets =
        indoorWaterTopOffsets(mapData.waterVolumes, mapData.vertices, m_movementController.runtimeVertices());
    const IndoorBodyDimensions body = {};
    const std::optional<IndoorWaterSample> eyeWater = indoorWaterAt(mapData.waterVolumes, m_waterTopOffsets,
        m_movementState.x, m_movementState.y, m_movementState.eyeZ() - IndoorSwimEyePointDrop);
    IndoorSwimFacts facts = {};
    facts.bodyInWater = eyeWater.has_value() || bodyWaterSample(m_movementState, body).has_value();
    facts.eyeUnder = eyeWater.has_value();
    facts.grounded = m_movementState.grounded;
    IndoorSwimMemory memory = m_swimMemory;
    m_swimState = indoorSwimState(facts, memory);
    m_eyeUnderWater = eyeWater.has_value();
    m_eyeUnderWaterKnown = true;
    m_eyeWaterVolumeIndex = eyeWater ? std::optional<size_t>(eyeWater->volumeIndex) : std::nullopt;
}

void IndoorPartyRuntime::setSwimInput(const IndoorSwimInput &input)
{
    m_swimInput = input;
}

bool IndoorPartyRuntime::swimming() const
{
    return m_swimState == IndoorSwimState::Submerged || m_swimState == IndoorSwimState::Surface
        || m_swimState == IndoorSwimState::Bed;
}

const IndoorWaterVolume *IndoorPartyRuntime::eyeWaterVolume() const
{
    const IndoorMapData *pMapData = m_movementController.indoorMapData();

    if (pMapData == nullptr || !m_eyeWaterVolumeIndex || *m_eyeWaterVolumeIndex >= pMapData->waterVolumes.size())
    {
        return nullptr;
    }

    return &pMapData->waterVolumes[*m_eyeWaterVolumeIndex];
}

std::optional<float> IndoorPartyRuntime::breathFraction() const
{
    if (!m_eyeUnderWater)
    {
        return std::nullopt;
    }

    return indoorBreathFraction(m_breath);
}

void IndoorPartyRuntime::takeWaterSounds(std::vector<std::string> &sounds)
{
    sounds.clear();
    std::swap(sounds, m_waterSounds);
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

void IndoorPartyRuntime::takeSteppedFloorFaces(std::vector<size_t> &faces)
{
    faces.clear();
    std::swap(faces, m_steppedFloorFaces);
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
    snapshot.swimMemory = m_swimMemory;
    return snapshot;
}

void IndoorPartyRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    m_movementState = snapshot.movementState;
    m_steppedFloorFaces.clear();
    m_movementAccumulatorSeconds = snapshot.movementAccumulatorSeconds;
    m_pendingJumpRequested = snapshot.pendingJumpRequested;
    m_pendingImpulseVelocityX = snapshot.pendingImpulseVelocityX;
    m_pendingImpulseVelocityY = snapshot.pendingImpulseVelocityY;
    m_pendingImpulseVelocityZ = snapshot.pendingImpulseVelocityZ;
    m_jumpCarryVelocityX = 0.0f;
    m_jumpCarryVelocityY = 0.0f;
    m_pendingJumpVelocity.reset();
    m_pendingJumpLift = DefaultJumpLift;
    m_burningDamageTimerSeconds = 0.0f;
    m_alwaysRunEnabled = snapshot.alwaysRunEnabled;
    m_movementController.invalidateRuntimeGeometryCache();
    resetWaterState(true);

    if (snapshot.swimMemory)
    {
        m_swimMemory = *snapshot.swimMemory;
    }
}

void IndoorPartyRuntime::setMovementSpeedMultiplier(float multiplier)
{
    m_movementSpeedMultiplier = multiplier;
}

void IndoorPartyRuntime::setFaceWadeSpeeds(std::vector<float> speeds)
{
    m_faceWadeSpeeds = std::move(speeds);
}

void IndoorPartyRuntime::setOpenAir(bool openAir)
{
    m_openAir = openAir;
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
    m_pendingJumpLift = std::max(0.0f, lift);
}

void IndoorPartyRuntime::requestDash(float velocityX, float velocityY, float seconds)
{
    m_dashVelocityX = velocityX;
    m_dashVelocityY = velocityY;
    m_dashSeconds = seconds;
}

void IndoorPartyRuntime::requestSpecialJump(float velocityX, float velocityY, float velocityZ)
{
    m_pendingImpulseVelocityX = velocityX;
    m_pendingImpulseVelocityY = velocityY;
    m_pendingImpulseVelocityZ = velocityZ;
}
}
