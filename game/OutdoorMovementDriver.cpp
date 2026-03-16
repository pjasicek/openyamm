#include "game/OutdoorMovementDriver.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float OutdoorMovementStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedMovementSeconds = 0.1f;
constexpr float BaseWalkSpeed = 576.0f;
constexpr float TurboMoveSpeed = 4000.0f;
}

OutdoorMovementDriver::OutdoorMovementDriver(const OutdoorMapData &outdoorMapData)
    : m_movementController(outdoorMapData)
{
}

void OutdoorMovementDriver::initialize(float x, float y, float footZHint)
{
    m_state = m_movementController.initializeState(x, y, footZHint);
    m_movementAccumulatorSeconds = 0.0f;
}

void OutdoorMovementDriver::update(const OutdoorMovementInput &input, float deltaSeconds)
{
    const float moveSpeed = input.turbo ? TurboMoveSpeed : BaseWalkSpeed;
    const float cosYaw = std::cos(input.yawRadians);
    const float sinYaw = std::sin(input.yawRadians);
    const bx::Vec3 forward = {cosYaw, -sinYaw, 0.0f};
    const bx::Vec3 right = {sinYaw, cosYaw, 0.0f};
    float moveVelocityX = 0.0f;
    float moveVelocityY = 0.0f;

    if (input.forward)
    {
        moveVelocityX += forward.x * moveSpeed;
        moveVelocityY += forward.y * moveSpeed;
    }

    if (input.backward)
    {
        moveVelocityX -= forward.x * moveSpeed;
        moveVelocityY -= forward.y * moveSpeed;
    }

    if (input.left)
    {
        moveVelocityX -= right.x * moveSpeed;
        moveVelocityY -= right.y * moveSpeed;
    }

    if (input.right)
    {
        moveVelocityX += right.x * moveSpeed;
        moveVelocityY += right.y * moveSpeed;
    }

    m_movementAccumulatorSeconds =
        std::min(m_movementAccumulatorSeconds + deltaSeconds, MaxAccumulatedMovementSeconds);

    while (m_movementAccumulatorSeconds >= OutdoorMovementStepSeconds)
    {
        m_state = m_movementController.resolveMove(
            m_state,
            moveVelocityX,
            moveVelocityY,
            OutdoorMovementStepSeconds
        );
        m_movementAccumulatorSeconds -= OutdoorMovementStepSeconds;
    }
}

const OutdoorMoveState &OutdoorMovementDriver::state() const
{
    return m_state;
}
}
