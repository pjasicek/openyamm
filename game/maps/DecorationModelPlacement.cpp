#include "game/maps/DecorationModelPlacement.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
std::array<float, 3> facingCardCorner(const Engine::ModelMatrix &m, const std::array<float, 3> &p,
    const std::array<float, 3> &viewer)
{
    const std::array<float, 3> world = {m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
        m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13], m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]};
    const std::array<float, 3> origin = {m[12], m[13], m[14]};
    const float scale = std::max(std::sqrt(m[0] * m[0] + m[1] * m[1] + m[2] * m[2]), 0.0001f);
    const float across = ((world[0] - origin[0]) * m[0] + (world[1] - origin[1]) * m[1]
        + (world[2] - origin[2]) * m[2]) / scale;
    float towardX = viewer[0] - origin[0];
    float towardY = viewer[1] - origin[1];
    const float length = std::max(std::sqrt(towardX * towardX + towardY * towardY), 0.01f);
    towardX /= length;
    towardY /= length;
    return {origin[0] - towardY * across, origin[1] + towardX * across, world[2]};
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
}
