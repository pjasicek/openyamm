#include "game/outdoor/OutdoorPartyRuntime.h"

#include "game/tables/ItemTable.h"

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

void OutdoorPartyRuntime::applyEventRuntimeState(const EventRuntimeState &runtimeState, bool grantItemsToInventory)
{
    m_party.applyEventRuntimeState(runtimeState, grantItemsToInventory);
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

float OutdoorPartyRuntime::partyX() const
{
    return m_movementDriver.state().x;
}

float OutdoorPartyRuntime::partyY() const
{
    return m_movementDriver.state().y;
}

float OutdoorPartyRuntime::partyFootZ() const
{
    return m_movementDriver.state().footZ;
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

void OutdoorPartyRuntime::setRunning(bool active)
{
    m_movementDriver.setRunning(active);
}

void OutdoorPartyRuntime::setDebugFlyingOverride(bool active)
{
    m_debugFlyingOverride = active;
    syncSpellMovementStatesFromPartyBuffs();
}

void OutdoorPartyRuntime::setMovementSpeedMultiplier(float multiplier)
{
    m_movementDriver.setSpeedMultiplier(multiplier);
}

void OutdoorPartyRuntime::syncSpellMovementStatesFromPartyBuffs()
{
    m_movementDriver.setFeatherFallActive(m_party.hasPartyBuff(PartyBuffId::FeatherFall));
    m_movementDriver.setWaterWalkActive(m_party.hasPartyBuff(PartyBuffId::WaterWalk));
    m_movementDriver.setFlyingAvailable(m_party.hasPartyBuff(PartyBuffId::Fly) || m_debugFlyingOverride);
}

void OutdoorPartyRuntime::requestJump()
{
    m_movementDriver.requestJump();
}
}
