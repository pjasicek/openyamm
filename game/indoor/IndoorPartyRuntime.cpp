#include "game/indoor/IndoorPartyRuntime.h"

#include "game/tables/ItemTable.h"

namespace OpenYAMM::Game
{
namespace
{
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

    const IndoorBodyDimensions body = {};
    m_pendingJumpRequested = m_pendingJumpRequested || jumpRequested;
    m_movementAccumulatorSeconds =
        std::min(m_movementAccumulatorSeconds + deltaSeconds, MaxAccumulatedMovementSeconds);

    while (m_movementAccumulatorSeconds >= IndoorMovementStepSeconds)
    {
        m_movementState = m_movementController.resolveMove(
            m_movementState,
            body,
            desiredVelocityX * m_movementSpeedMultiplier,
            desiredVelocityY * m_movementSpeedMultiplier,
            m_pendingJumpRequested,
            IndoorMovementStepSeconds);
        m_pendingJumpRequested = false;
        m_movementAccumulatorSeconds -= IndoorMovementStepSeconds;
    }
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
    return snapshot;
}

void IndoorPartyRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    m_movementState = snapshot.movementState;
    m_movementAccumulatorSeconds = snapshot.movementAccumulatorSeconds;
    m_pendingJumpRequested = snapshot.pendingJumpRequested;
}

void IndoorPartyRuntime::setMovementSpeedMultiplier(float multiplier)
{
    m_movementSpeedMultiplier = multiplier;
}
}
