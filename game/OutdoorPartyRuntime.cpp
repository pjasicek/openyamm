#include "game/OutdoorPartyRuntime.h"

namespace OpenYAMM::Game
{
OutdoorPartyRuntime::OutdoorPartyRuntime(OutdoorMovementDriver movementDriver)
    : m_movementDriver(std::move(movementDriver))
{
}

void OutdoorPartyRuntime::initialize(float x, float y, float footZHint)
{
    m_movementDriver.initialize(x, y, footZHint);
    m_partyState.reset();
}

void OutdoorPartyRuntime::update(const OutdoorMovementInput &input, float deltaSeconds)
{
    m_movementDriver.update(input, deltaSeconds);
    m_partyState.applyMovementEffects(m_movementDriver.consumePendingEffects());
}

const OutdoorMoveState &OutdoorPartyRuntime::movementState() const
{
    return m_movementDriver.state();
}

const OutdoorMovementEvents &OutdoorPartyRuntime::movementEvents() const
{
    return m_movementDriver.lastEvents();
}

const OutdoorMovementConsequences &OutdoorPartyRuntime::movementConsequences() const
{
    return m_movementDriver.lastConsequences();
}

const OutdoorPartyMovementState &OutdoorPartyRuntime::partyMovementState() const
{
    return m_movementDriver.partyMovementState();
}

const OutdoorPartyState &OutdoorPartyRuntime::partyState() const
{
    return m_partyState;
}

void OutdoorPartyRuntime::toggleRunning()
{
    m_movementDriver.toggleRunning();
}

void OutdoorPartyRuntime::toggleFlying()
{
    m_movementDriver.toggleFlying();
}

void OutdoorPartyRuntime::toggleWaterWalk()
{
    m_movementDriver.toggleWaterWalk();
}

void OutdoorPartyRuntime::toggleFeatherFall()
{
    m_movementDriver.toggleFeatherFall();
}
}
