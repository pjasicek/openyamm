#pragma once

#include "game/OutdoorMovementDriver.h"
#include "game/Party.h"

#include <optional>

namespace OpenYAMM::Game
{
class ItemTable;

class OutdoorPartyRuntime
{
public:
    OutdoorPartyRuntime(OutdoorMovementDriver movementDriver, const ItemTable &itemTable);

    void initialize(float x, float y, float footZHint, bool resetParty = true);
    void teleportTo(float x, float y, float footZHint);
    void update(const OutdoorMovementInput &input, float deltaSeconds);
    void applyEventRuntimeState(const EventRuntimeState &runtimeState);

    const OutdoorMoveState &movementState() const;
    const OutdoorMovementEvents &movementEvents() const;
    const OutdoorMovementConsequences &movementConsequences() const;
    const OutdoorPartyMovementState &partyMovementState() const;
    const Party &party() const;
    Party &party();
    void setParty(const Party &party);

    void toggleRunning();
    void toggleFlying();
    void toggleWaterWalk();
    void toggleFeatherFall();

private:
    OutdoorMovementDriver m_movementDriver;
    Party m_party;
};
}
