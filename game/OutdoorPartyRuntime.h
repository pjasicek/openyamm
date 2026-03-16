#pragma once

#include "game/OutdoorMovementDriver.h"
#include "game/OutdoorPartyState.h"

namespace OpenYAMM::Game
{
class OutdoorPartyRuntime
{
public:
    explicit OutdoorPartyRuntime(OutdoorMovementDriver movementDriver);

    void initialize(float x, float y, float footZHint);
    void update(const OutdoorMovementInput &input, float deltaSeconds);

    const OutdoorMoveState &movementState() const;
    const OutdoorMovementEvents &movementEvents() const;
    const OutdoorMovementConsequences &movementConsequences() const;
    const OutdoorPartyMovementState &partyMovementState() const;
    const OutdoorPartyState &partyState() const;

    void toggleRunning();
    void toggleFlying();
    void toggleWaterWalk();
    void toggleFeatherFall();

private:
    OutdoorMovementDriver m_movementDriver;
    OutdoorPartyState m_partyState;
};
}
