#include "game/OutdoorPartyRuntime.h"

#include "game/ItemTable.h"

namespace OpenYAMM::Game
{
OutdoorPartyRuntime::OutdoorPartyRuntime(OutdoorMovementDriver movementDriver, const ItemTable &itemTable)
    : m_movementDriver(std::move(movementDriver))
{
    m_party.setItemTable(&itemTable);
}

void OutdoorPartyRuntime::initialize(float x, float y, float footZHint)
{
    m_movementDriver.initialize(x, y, footZHint);
    m_party.reset();
}

void OutdoorPartyRuntime::update(const OutdoorMovementInput &input, float deltaSeconds)
{
    m_movementDriver.update(input, deltaSeconds);
    m_party.applyMovementEffects(m_movementDriver.consumePendingEffects());
}

void OutdoorPartyRuntime::applyEventRuntimeState(const EventRuntimeState &runtimeState)
{
    m_party.applyEventRuntimeState(runtimeState);
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

const Party &OutdoorPartyRuntime::party() const
{
    return m_party;
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
