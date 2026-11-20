#include "game/maps/DecorationModelPlacement.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
std::array<float, 3> facingCardCorner(const Engine::ModelMatrix &m, const std::array<float, 3> &p,
    const std::array<float, 3> &viewer, const std::array<float, 3> &pivot)
{
    const auto toWorld = [&m](const std::array<float, 3> &v)
    {
        return std::array<float, 3>{m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12],
            m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13], m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14]};
    };
    const std::array<float, 3> world = toWorld(p);
    const std::array<float, 3> centre = toWorld(pivot);
    const float scale = std::max(std::sqrt(m[0] * m[0] + m[1] * m[1] + m[2] * m[2]), 0.0001f);
    const float across = ((world[0] - centre[0]) * m[0] + (world[1] - centre[1]) * m[1]
        + (world[2] - centre[2]) * m[2]) / scale;
    float towardX = viewer[0] - centre[0];
    float towardY = viewer[1] - centre[1];
    const float length = std::max(std::sqrt(towardX * towardX + towardY * towardY), 0.01f);
    towardX /= length;
    towardY /= length;
    return {centre[0] - towardY * across, centre[1] + towardX * across, world[2]};
}

float yawFacing(const std::array<float, 2> &direction)
{
    // Where the asset front points at zero yaw (the glTF y-up to map z-up turn decides it).
    const Engine::ModelMatrix rest = Engine::composeModelTransform(Engine::gltfModelPlacement({0.0f, 0.0f, 0.0f},
        0.0f, 1.0f));
    return std::atan2(direction[1], direction[0]) - std::atan2(rest[9], rest[8]);
}

Engine::ModelMatrix wallMountedPlacement(const DecorationWallContact &wall, float backZ, float z, float scale)
{
    const float out = -backZ * scale;
    return Engine::composeModelTransform(Engine::gltfModelPlacement({wall.point[0] + wall.normal[0] * out,
        wall.point[1] + wall.normal[1] * out, z}, yawFacing(wall.normal), scale));
}

Engine::ModelMatrix swungPlacement(const Engine::ModelMatrix &placement, const std::array<float, 3> &pivot,
    float angleRadians)
{
    // pivot * rotation about x * pivot^-1, in asset space, then the placement.
    const float c = std::cos(angleRadians);
    const float s = std::sin(angleRadians);
    Engine::ModelMatrix swing = {1.0f, 0.0f, 0.0f, 0.0f, 0.0f, c, s, 0.0f, 0.0f, -s, c, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f};
    swing[13] = pivot[1] - (c * pivot[1] - s * pivot[2]);
    swing[14] = pivot[2] - (s * pivot[1] + c * pivot[2]);
    return Engine::multiplyModelMatrices(placement, swing);
}

Engine::ModelMatrix turnedPlacement(const Engine::ModelMatrix &placement, const std::array<float, 3> &pivot,
    float angleRadians)
{
    // pivot * rotation about z * pivot^-1, in asset space, then the placement.
    const float c = std::cos(angleRadians);
    const float s = std::sin(angleRadians);
    Engine::ModelMatrix turn = {c, s, 0.0f, 0.0f, -s, c, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f};
    turn[12] = pivot[0] - (c * pivot[0] - s * pivot[1]);
    turn[13] = pivot[1] - (s * pivot[0] + c * pivot[1]);
    return Engine::multiplyModelMatrices(placement, turn);
}

float turnRemaining(float turnRadians, float durationSeconds, float elapsedSeconds)
{
    if (durationSeconds <= 0.0f || elapsedSeconds >= durationSeconds)
    {
        return 0.0f;
    }
    const float t = std::max(elapsedSeconds, 0.0f) / durationSeconds;
    return -turnRadians * (1.0f - t * t * (3.0f - 2.0f * t));
}
}
