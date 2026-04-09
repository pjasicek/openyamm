#include "game/outdoor/OutdoorMovementDriver.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float OutdoorMovementStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedMovementSeconds = 0.1f;
constexpr float HardLandingDistance = 512.0f;
constexpr float EventHoldSeconds = 0.75f;
constexpr float DamageTickSeconds = 1.0f;
}

OutdoorMovementDriver::OutdoorMovementDriver(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet
)
    : m_movementController(
        outdoorMapData,
        outdoorLandMask,
        outdoorDecorationCollisionSet,
        outdoorActorCollisionSet,
        outdoorSpriteObjectCollisionSet
    )
{
}

void OutdoorMovementDriver::initialize(float x, float y, float footZHint)
{
    m_state = m_movementController.initializeState(x, y, footZHint);
    m_partyMovementState = {};
    m_tuning = {};
    m_lastEvents = {};
    m_lastConsequences = {};
    m_pendingEffects = {};
    m_jumpHeld = false;
    m_pendingJumpPress = false;
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
    m_pendingJumpPress = false;
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

void OutdoorMovementDriver::update(const OutdoorMovementInput &input, float deltaSeconds)
{
    const bool jumpPressed = input.jump && !m_jumpHeld;
    m_jumpHeld = input.jump;
    m_pendingJumpPress = m_pendingJumpPress || jumpPressed;
    const float cosYaw = std::cos(input.yawRadians);
    const float sinYaw = std::sin(input.yawRadians);
    const float speedMultiplier = std::max(m_speedMultiplier, 0.0f);
    const bx::Vec3 forward = {cosYaw, -sinYaw, 0.0f};
    const bx::Vec3 right = {sinYaw, cosYaw, 0.0f};
    float moveVelocityX = 0.0f;
    float moveVelocityY = 0.0f;

    if (input.turbo)
    {
        if (input.forward)
        {
            moveVelocityX += forward.x * m_tuning.turboMoveSpeed * speedMultiplier;
            moveVelocityY += forward.y * m_tuning.turboMoveSpeed * speedMultiplier;
        }

        if (input.backward)
        {
            moveVelocityX -= forward.x * m_tuning.turboMoveSpeed * speedMultiplier;
            moveVelocityY -= forward.y * m_tuning.turboMoveSpeed * speedMultiplier;
        }

        if (input.left)
        {
            moveVelocityX -= right.x * m_tuning.turboMoveSpeed * speedMultiplier;
            moveVelocityY -= right.y * m_tuning.turboMoveSpeed * speedMultiplier;
        }

        if (input.right)
        {
            moveVelocityX += right.x * m_tuning.turboMoveSpeed * speedMultiplier;
            moveVelocityY += right.y * m_tuning.turboMoveSpeed * speedMultiplier;
        }
    }
    else
    {
        const float forwardSpeedMultiplier = m_partyMovementState.running ? m_tuning.runForwardMultiplier : 1.0f;

        if (input.left)
        {
            moveVelocityX -= right.x * m_tuning.walkSpeed * m_tuning.strafeMultiplier * speedMultiplier;
            moveVelocityY -= right.y * m_tuning.walkSpeed * m_tuning.strafeMultiplier * speedMultiplier;
        }

        if (input.right)
        {
            moveVelocityX += right.x * m_tuning.walkSpeed * m_tuning.strafeMultiplier * speedMultiplier;
            moveVelocityY += right.y * m_tuning.walkSpeed * m_tuning.strafeMultiplier * speedMultiplier;
        }

        if (input.forward)
        {
            moveVelocityX += forward.x * m_tuning.walkSpeed * forwardSpeedMultiplier * speedMultiplier;
            moveVelocityY += forward.y * m_tuning.walkSpeed * forwardSpeedMultiplier * speedMultiplier;
        }

        if (input.backward)
        {
            moveVelocityX -= forward.x * m_tuning.walkSpeed * m_tuning.backwardWalkMultiplier * speedMultiplier;
            moveVelocityY -= forward.y * m_tuning.walkSpeed * m_tuning.backwardWalkMultiplier * speedMultiplier;
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
    m_movementAccumulatorSeconds =
        std::min(m_movementAccumulatorSeconds + deltaSeconds, MaxAccumulatedMovementSeconds);

    while (m_movementAccumulatorSeconds >= OutdoorMovementStepSeconds)
    {
        const OutdoorMoveState previousState = m_state;
        const bool jumpRequestedThisStep = m_pendingJumpPress;
        std::vector<size_t> contactedActorIndices;
        m_state = m_movementController.resolveMove(
            m_state,
            moveVelocityX,
            moveVelocityY,
            jumpRequestedThisStep,
            input.flyDown,
            m_partyMovementState.flying,
            m_partyMovementState.waterWalk,
            m_tuning.jumpVelocity * speedMultiplier,
            m_tuning.flyVerticalSpeed * speedMultiplier,
            OutdoorMovementStepSeconds,
            &contactedActorIndices
        );
        m_pendingJumpPress = false;

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

        m_movementAccumulatorSeconds -= OutdoorMovementStepSeconds;
    }

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

    if (m_state.supportOnWater && !m_partyMovementState.waterWalk && !m_partyMovementState.flying)
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

    if (m_state.supportOnBurning && !m_partyMovementState.flying)
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
        && !m_partyMovementState.flying
        && !m_state.supportOnWater)
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
    m_partyMovementState.flying = active;

    if (m_partyMovementState.flying)
    {
        m_state.verticalVelocity = 0.0f;
        m_state.fallStartZ = m_state.footZ;
        m_state.fallDistance = 0.0f;
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

void OutdoorMovementDriver::requestJump()
{
    m_pendingJumpPress = true;
}

void OutdoorMovementDriver::setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders)
{
    m_movementController.setActorColliders(actorColliders);
}

}
