#pragma once

#include "game/OutdoorMovementController.h"

namespace OpenYAMM::Game
{
struct OutdoorMovementInput
{
    bool forward = false;
    bool backward = false;
    bool left = false;
    bool right = false;
    bool turbo = false;
    float yawRadians = 0.0f;
};

class OutdoorMovementDriver
{
public:
    explicit OutdoorMovementDriver(const OutdoorMapData &outdoorMapData);

    void initialize(float x, float y, float footZHint);
    void update(const OutdoorMovementInput &input, float deltaSeconds);
    const OutdoorMoveState &state() const;

private:
    OutdoorMovementController m_movementController;
    OutdoorMoveState m_state;
    float m_movementAccumulatorSeconds = 0.0f;
};
}
