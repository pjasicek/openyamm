#include "game/OutdoorMovementDriver.h"

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
    m_modifiers = {};
    m_lastEvents = {};
    m_lastConsequences = {};
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
}

void OutdoorMovementDriver::update(const OutdoorMovementInput &input, float deltaSeconds)
{
    const bool jumpPressed = input.jump && !m_jumpHeld;
    m_jumpHeld = input.jump;
    m_pendingJumpPress = m_pendingJumpPress || jumpPressed;
    const float cosYaw = std::cos(input.yawRadians);
    const float sinYaw = std::sin(input.yawRadians);
    const bx::Vec3 forward = {cosYaw, -sinYaw, 0.0f};
    const bx::Vec3 right = {sinYaw, cosYaw, 0.0f};
    float moveVelocityX = 0.0f;
    float moveVelocityY = 0.0f;

    if (input.turbo)
    {
        if (input.forward)
        {
            moveVelocityX += forward.x * m_modifiers.turboMoveSpeed;
            moveVelocityY += forward.y * m_modifiers.turboMoveSpeed;
        }

        if (input.backward)
        {
            moveVelocityX -= forward.x * m_modifiers.turboMoveSpeed;
            moveVelocityY -= forward.y * m_modifiers.turboMoveSpeed;
        }

        if (input.left)
        {
            moveVelocityX -= right.x * m_modifiers.turboMoveSpeed;
            moveVelocityY -= right.y * m_modifiers.turboMoveSpeed;
        }

        if (input.right)
        {
            moveVelocityX += right.x * m_modifiers.turboMoveSpeed;
            moveVelocityY += right.y * m_modifiers.turboMoveSpeed;
        }
    }
    else
    {
        const float forwardSpeedMultiplier = m_modifiers.running ? m_modifiers.runForwardMultiplier : 1.0f;

        if (input.left)
        {
            moveVelocityX -= right.x * m_modifiers.walkSpeed * m_modifiers.strafeMultiplier;
            moveVelocityY -= right.y * m_modifiers.walkSpeed * m_modifiers.strafeMultiplier;
        }

        if (input.right)
        {
            moveVelocityX += right.x * m_modifiers.walkSpeed * m_modifiers.strafeMultiplier;
            moveVelocityY += right.y * m_modifiers.walkSpeed * m_modifiers.strafeMultiplier;
        }

        if (input.forward)
        {
            moveVelocityX += forward.x * m_modifiers.walkSpeed * forwardSpeedMultiplier;
            moveVelocityY += forward.y * m_modifiers.walkSpeed * forwardSpeedMultiplier;
        }

        if (input.backward)
        {
            moveVelocityX -= forward.x * m_modifiers.walkSpeed * m_modifiers.backwardWalkMultiplier;
            moveVelocityY -= forward.y * m_modifiers.walkSpeed * m_modifiers.backwardWalkMultiplier;
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
        m_state = m_movementController.resolveMove(
            m_state,
            moveVelocityX,
            moveVelocityY,
            jumpRequestedThisStep,
            input.flyDown,
            m_modifiers.flying,
            m_modifiers.jumpVelocity,
            m_modifiers.flyVerticalSpeed,
            OutdoorMovementStepSeconds
        );
        m_pendingJumpPress = false;
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

    if (m_state.supportOnWater && !m_modifiers.waterWalk && !m_modifiers.flying)
    {
        m_waterDamageTimerSeconds += deltaSeconds;

        while (m_waterDamageTimerSeconds >= DamageTickSeconds)
        {
            m_waterDamageConsequenceSeconds = EventHoldSeconds;
            m_waterDamageTimerSeconds -= DamageTickSeconds;
        }
    }
    else
    {
        m_waterDamageTimerSeconds = 0.0f;
    }

    if (m_state.supportOnBurning && !m_modifiers.flying)
    {
        m_burningDamageTimerSeconds += deltaSeconds;

        while (m_burningDamageTimerSeconds >= DamageTickSeconds)
        {
            m_burningDamageConsequenceSeconds = EventHoldSeconds;
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
    }

    if (m_lastEvents.hardLanding)
    {
        m_hardLandingSoundConsequenceSeconds = EventHoldSeconds;
    }

    if (m_lastEvents.landed && m_state.supportOnWater && m_lastEvents.landingFallDistance > 0.0f)
    {
        m_splashSoundConsequenceSeconds = EventHoldSeconds;
    }

    if (m_lastEvents.hardLanding && !m_modifiers.featherFall && !m_modifiers.flying && !m_state.supportOnWater)
    {
        m_fallDamageConsequenceSeconds = EventHoldSeconds;
        m_lastConsequences.fallDamageDistance = m_lastEvents.landingFallDistance;
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

OutdoorMovementModifiers &OutdoorMovementDriver::modifiers()
{
    return m_modifiers;
}

const OutdoorMovementModifiers &OutdoorMovementDriver::modifiers() const
{
    return m_modifiers;
}
}
