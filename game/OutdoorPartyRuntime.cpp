#include "game/OutdoorPartyRuntime.h"

#include "game/ItemTable.h"

namespace OpenYAMM::Game
{
namespace
{
constexpr float GameMinutesPerRealSecond = 0.5f;
constexpr float GameSecondsPerRealSecond = GameMinutesPerRealSecond * 60.0f;
}

OutdoorPartyRuntime::OutdoorPartyRuntime(OutdoorMovementDriver movementDriver, const ItemTable &itemTable)
    : m_movementDriver(std::move(movementDriver))
{
    m_party.setItemTable(&itemTable);
}

void OutdoorPartyRuntime::initialize(float x, float y, float footZHint, bool resetParty)
{
    m_movementDriver.initialize(x, y, footZHint);

    if (resetParty)
    {
        m_party.reset();
    }

    syncSpellMovementStatesFromPartyBuffs();
}

void OutdoorPartyRuntime::teleportTo(float x, float y, float footZHint)
{
    m_movementDriver.initialize(x, y, footZHint);
}

void OutdoorPartyRuntime::update(const OutdoorMovementInput &input, float deltaSeconds)
{
    m_movementDriver.update(input, deltaSeconds);
    m_party.updateRecovery(deltaSeconds);
    m_party.advanceTimedStates(deltaSeconds * GameSecondsPerRealSecond);
    syncSpellMovementStatesFromPartyBuffs();
    m_party.applyMovementEffects(m_movementDriver.consumePendingEffects());
}

void OutdoorPartyRuntime::setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders)
{
    m_movementDriver.setActorColliders(actorColliders);
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

Party &OutdoorPartyRuntime::party()
{
    return m_party;
}

void OutdoorPartyRuntime::setParty(const Party &party)
{
    m_party = party;
    syncSpellMovementStatesFromPartyBuffs();
}

OutdoorPartyRuntime::Snapshot OutdoorPartyRuntime::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.movementState = m_movementDriver.state();
    snapshot.partyMovementState = m_movementDriver.partyMovementState();
    return snapshot;
}

void OutdoorPartyRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    m_movementDriver.restoreState(snapshot.movementState, snapshot.partyMovementState);
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

void OutdoorPartyRuntime::syncSpellMovementStatesFromPartyBuffs()
{
    m_movementDriver.setFeatherFallActive(m_party.hasPartyBuff(PartyBuffId::FeatherFall));
    m_movementDriver.setWaterWalkActive(m_party.hasPartyBuff(PartyBuffId::WaterWalk));
    m_movementDriver.setFlying(m_party.hasPartyBuff(PartyBuffId::Fly));
}

void OutdoorPartyRuntime::requestJump()
{
    m_movementDriver.requestJump();
}
}
