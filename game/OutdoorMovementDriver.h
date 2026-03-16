#pragma once

#include "game/OutdoorCollisionData.h"
#include "game/OutdoorMovementController.h"

#include <optional>

namespace OpenYAMM::Game
{
struct OutdoorMovementInput
{
    bool forward = false;
    bool backward = false;
    bool left = false;
    bool right = false;
    bool jump = false;
    bool flyDown = false;
    bool turbo = false;
    float yawRadians = 0.0f;
};

struct OutdoorMovementModifiers
{
    bool running = true;
    bool flying = false;
    bool featherFall = false;
    bool waterWalk = false;
    float walkSpeed = 384.0f;
    float runForwardMultiplier = 2.0f;
    float backwardWalkMultiplier = 1.0f;
    float strafeMultiplier = 0.75f;
    float turboMoveSpeed = 4000.0f;
    float jumpVelocity = 1000.0f;
    float flyVerticalSpeed = 900.0f;
};

struct OutdoorMovementConsequences
{
    bool applyWaterDamage = false;
    bool applyBurningDamage = false;
    bool applyFallDamage = false;
    float fallDamageDistance = 0.0f;
    bool playSplashSound = false;
    bool playLandingSound = false;
    bool playHardLandingSound = false;
};

struct OutdoorMovementEvents
{
    bool startedFalling = false;
    bool landed = false;
    bool enteredWater = false;
    bool leftWater = false;
    bool enteredBurning = false;
    bool leftBurning = false;
    float landingFallDistance = 0.0f;
    bool hardLanding = false;
};

class OutdoorMovementDriver
{
public:
    OutdoorMovementDriver(
        const OutdoorMapData &outdoorMapData,
        const std::optional<std::vector<uint8_t>> &outdoorLandMask,
        const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
        const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
        const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet
    );

    void initialize(float x, float y, float footZHint);
    void update(const OutdoorMovementInput &input, float deltaSeconds);
    const OutdoorMoveState &state() const;
    const OutdoorMovementEvents &lastEvents() const;
    const OutdoorMovementConsequences &lastConsequences() const;
    OutdoorMovementModifiers &modifiers();
    const OutdoorMovementModifiers &modifiers() const;

private:
    OutdoorMovementController m_movementController;
    OutdoorMoveState m_state;
    OutdoorMovementModifiers m_modifiers;
    OutdoorMovementEvents m_lastEvents;
    OutdoorMovementConsequences m_lastConsequences;
    bool m_jumpHeld = false;
    bool m_pendingJumpPress = false;
    float m_movementAccumulatorSeconds = 0.0f;
    float m_startedFallingEventSeconds = 0.0f;
    float m_landedEventSeconds = 0.0f;
    float m_enteredWaterEventSeconds = 0.0f;
    float m_leftWaterEventSeconds = 0.0f;
    float m_enteredBurningEventSeconds = 0.0f;
    float m_leftBurningEventSeconds = 0.0f;
    float m_waterDamageConsequenceSeconds = 0.0f;
    float m_burningDamageConsequenceSeconds = 0.0f;
    float m_fallDamageConsequenceSeconds = 0.0f;
    float m_splashSoundConsequenceSeconds = 0.0f;
    float m_landingSoundConsequenceSeconds = 0.0f;
    float m_hardLandingSoundConsequenceSeconds = 0.0f;
    float m_waterDamageTimerSeconds = 0.0f;
    float m_burningDamageTimerSeconds = 0.0f;
};
}
