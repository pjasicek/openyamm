#pragma once

#include "game/outdoor/OutdoorMovementDriver.h"
#include "game/party/Party.h"

#include <optional>

namespace OpenYAMM::Game
{
class ItemTable;

class OutdoorPartyRuntime
{
public:
    struct Snapshot
    {
        OutdoorMoveState movementState = {};
        OutdoorPartyMovementState partyMovementState = {};
    };

    OutdoorPartyRuntime(OutdoorMovementDriver movementDriver, const ItemTable &itemTable);

    void initialize(float x, float y, float footZHint, bool resetParty = true);
    void teleportTo(float x, float y, float footZHint);
    void update(const OutdoorMovementInput &input, float deltaSeconds);
    void setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders);
    void applyEventRuntimeState(const EventRuntimeState &runtimeState, bool grantItemsToInventory = true);

    const OutdoorMoveState &movementState() const;
    const OutdoorMovementEvents &movementEvents() const;
    const OutdoorMovementConsequences &movementConsequences() const;
    const OutdoorPartyMovementState &partyMovementState() const;
    const Party &party() const;
    Party &party();
    void setParty(const Party &party);
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);

    void toggleRunning();
    void toggleFlying();
    void toggleWaterWalk();
    void toggleFeatherFall();
    void setRunning(bool active);
    void setDebugFlyingOverride(bool active);
    void setMovementSpeedMultiplier(float multiplier);
    void syncSpellMovementStatesFromPartyBuffs();
    void requestJump();

private:
    OutdoorMovementDriver m_movementDriver;
    Party m_party;
    bool m_debugFlyingOverride = false;
};
}
