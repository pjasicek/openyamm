#include "game/indoor/IndoorPartyRuntime.h"

#include "game/tables/ItemTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
constexpr float GameMinutesPerRealSecond = 0.5f;
constexpr float GameSecondsPerRealSecond = GameMinutesPerRealSecond * 60.0f;
constexpr float IndoorMovementStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedMovementSeconds = 0.1f;
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
}

void IndoorPartyRuntime::teleportPartyPosition(float x, float y, float z)
{
    const IndoorBodyDimensions body = {};
    m_movementState = m_movementController.initializeStateFromEyePosition(x, y, z + body.height, body);
    m_movementAccumulatorSeconds = 0.0f;
    m_pendingJumpRequested = false;
}

void IndoorPartyRuntime::update(float desiredVelocityX, float desiredVelocityY, bool jumpRequested, float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    m_party.updateRecovery(deltaSeconds);
    m_party.advanceTimedStates(deltaSeconds * GameSecondsPerRealSecond);

    const IndoorBodyDimensions body = {};
    m_pendingJumpRequested = m_pendingJumpRequested || jumpRequested;
    m_movementAccumulatorSeconds =
        std::min(m_movementAccumulatorSeconds + deltaSeconds, MaxAccumulatedMovementSeconds);
    const float impulseVelocityX = m_pendingImpulseVelocityX;
    const float impulseVelocityY = m_pendingImpulseVelocityY;
    const float impulseVelocityZ = m_pendingImpulseVelocityZ;
    const bool hasPendingImpulse =
        impulseVelocityX != 0.0f || impulseVelocityY != 0.0f || impulseVelocityZ != 0.0f;

    if (hasPendingImpulse)
    {
        m_movementState.verticalVelocity = std::max(m_movementState.verticalVelocity, impulseVelocityZ);
        m_pendingImpulseVelocityX = 0.0f;
        m_pendingImpulseVelocityY = 0.0f;
        m_pendingImpulseVelocityZ = 0.0f;
    }

    while (m_movementAccumulatorSeconds >= IndoorMovementStepSeconds)
    {
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
            nullptr);
        m_pendingJumpRequested = false;
        m_movementAccumulatorSeconds -= IndoorMovementStepSeconds;
    }
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
    m_alwaysRunEnabled = snapshot.alwaysRunEnabled;
}

void IndoorPartyRuntime::setMovementSpeedMultiplier(float multiplier)
{
    m_movementSpeedMultiplier = multiplier;
}

void IndoorPartyRuntime::setAlwaysRunEnabled(bool enabled)
{
    m_alwaysRunEnabled = enabled;
}

bool IndoorPartyRuntime::alwaysRunEnabled() const
{
    return m_alwaysRunEnabled;
}

void IndoorPartyRuntime::syncSpellMovementStatesFromPartyBuffs()
{
}

void IndoorPartyRuntime::requestJump()
{
    m_pendingJumpRequested = true;
}

void IndoorPartyRuntime::requestSpecialJump(float velocityX, float velocityY, float velocityZ)
{
    m_pendingImpulseVelocityX = velocityX;
    m_pendingImpulseVelocityY = velocityY;
    m_pendingImpulseVelocityZ = velocityZ;
}
}
