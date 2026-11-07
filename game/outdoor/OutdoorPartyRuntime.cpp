#include "game/outdoor/OutdoorPartyRuntime.h"

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/tables/ItemTable.h"

#include <SDL3/SDL.h>

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

void OutdoorPartyRuntime::update(
    const OutdoorMovementInput &input,
    float deltaSeconds,
    GameplayWorldMovementFrameDiagnostics *pPerformanceDiagnostics)
{
    m_movementStatusText.clear();
    OutdoorMovementInput rulesInput = input;
    rulesInput.movementSpeedScale *= m_party.rulesMovementMultiplier();
    m_movementDriver.update(rulesInput, deltaSeconds, pPerformanceDiagnostics);

    uint64_t stageBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
    if (!input.turnBasedPhysicsStep)
    {
        // Running halves recovery speed, but only while the party actually runs.
        m_party.updateRecovery(deltaSeconds, m_movementDriver.isRunningMovement(input) ? 0.5f : 1.0f);
        if (pPerformanceDiagnostics != nullptr)
        {
            pPerformanceDiagnostics->partyRecoveryNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
            stageBeginTickCount = SDL_GetTicksNS();
        }

        m_party.advanceTimedStates(deltaSeconds * GameSecondsPerRealSecond);
    }

    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->partyTimedStateNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
        stageBeginTickCount = SDL_GetTicksNS();
    }

    syncSpellMovementStatesFromPartyBuffs();

    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->partySpellStateNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
        stageBeginTickCount = SDL_GetTicksNS();
    }

    const OutdoorMovementEffects effects = m_movementDriver.consumePendingEffects();
    m_party.applyMovementEffects(effects);

    if (effects.burningDamageTicks > 0)
    {
        m_movementStatusText = "You are burning!";
    }
    else if (effects.waterDamageTicks > 0)
    {
        m_movementStatusText = "You are drowning!";
    }

    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->partyEffectsNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
    }
}

void OutdoorPartyRuntime::setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders)
{
    m_movementDriver.setActorColliders(actorColliders);
}

void OutdoorPartyRuntime::setHiddenDecorationEntities(const std::vector<bool> &hiddenEntities)
{
    m_movementDriver.setHiddenDecorationEntities(hiddenEntities);
}

void OutdoorPartyRuntime::setFaceAttributes(size_t bModelIndex, size_t faceIndex, uint32_t attributes)
{
    m_movementDriver.setFaceAttributes(bModelIndex, faceIndex, attributes);
}

void OutdoorPartyRuntime::updateFaceGeometries(const std::vector<OutdoorFaceGeometryData> &geometries)
{
    m_movementDriver.updateFaceGeometries(geometries);
}

void OutdoorPartyRuntime::lift(float height)
{
    m_movementDriver.lift(height);
}

void OutdoorPartyRuntime::requestDash(float velocityX, float velocityY, float seconds)
{
    m_movementDriver.requestDash(velocityX, velocityY, seconds);
}

bool OutdoorPartyRuntime::translateWithSupportedBModel(
    size_t bModelIndex,
    float deltaX,
    float deltaY,
    float deltaZ)
{
    return m_movementDriver.translateWithSupportedBModel(bModelIndex, deltaX, deltaY, deltaZ);
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

const std::string &OutdoorPartyRuntime::movementStatusText() const
{
    return m_movementStatusText;
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

float OutdoorPartyRuntime::partyEyeZ() const
{
    return m_movementDriver.state().footZ + m_eyeHeight;
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

void OutdoorPartyRuntime::requestLanding()
{
    m_movementDriver.requestLanding();
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

void OutdoorPartyRuntime::setUnderwater(bool active)
{
    m_underwater = active;
    m_movementDriver.setSwimming(active);
    syncSpellMovementStatesFromPartyBuffs();
}

void OutdoorPartyRuntime::setMovementSpeedMultiplier(float multiplier)
{
    m_movementDriver.setSpeedMultiplier(multiplier);
}

void OutdoorPartyRuntime::setBodyDimensions(float radius, float height, float maxStepHeight)
{
    m_movementDriver.setBodyDimensions(radius, height, maxStepHeight);
}

void OutdoorPartyRuntime::setEyeHeight(float eyeHeight)
{
    m_eyeHeight = eyeHeight;
}

void OutdoorPartyRuntime::setCollisionTraceEnabled(bool enabled, const std::string &mapName)
{
    m_movementDriver.setCollisionTraceEnabled(enabled, mapName);
}

void OutdoorPartyRuntime::syncSpellMovementStatesFromPartyBuffs()
{
    m_movementDriver.setFeatherFallActive(m_party.hasPartyBuff(PartyBuffId::FeatherFall));
    m_movementDriver.setWaterWalkActive(m_party.hasPartyBuff(PartyBuffId::WaterWalk));
    m_movementDriver.setLevitateActive(m_party.hasPartyBuff(PartyBuffId::Levitate));
    m_movementDriver.setFlyingAvailable(
        m_party.hasPartyBuff(PartyBuffId::Fly) || m_debugFlyingOverride || m_underwater);
}

void OutdoorPartyRuntime::requestJump(std::optional<float> verticalVelocity, float lift)
{
    m_movementDriver.requestJump(verticalVelocity, lift);
}

void OutdoorPartyRuntime::requestSpecialJump(float velocityX, float velocityY, float velocityZ)
{
    m_movementDriver.requestSpecialJump(velocityX, velocityY, velocityZ);
}
}
