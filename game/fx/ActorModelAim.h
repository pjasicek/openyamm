#pragma once

#include "engine/models/ModelInstance.h"

#include <cmath>
#include <optional>
#include <span>

namespace OpenYAMM::Game
{
// World-space rotations, applied root to tip after sampling the clip. A mounted gun turns on its traverse joint
// before the barrel pitches about its new horizontal side axis. A normal head look shares its rotation as before.
inline std::vector<Engine::ModelNodeRotation> actorModelAimRotations(std::optional<uint32_t> traverseNode,
    float traverseYaw, std::span<const uint32_t> lookNodes, float facing, float lookYaw, float lookPitch)
{
    std::vector<Engine::ModelNodeRotation> rotations;
    using Quaternion = std::array<float, 4>;
    const auto axisAngle = [](float x, float y, float z, float angle)
    {
        const float half = 0.5f * angle;
        return Quaternion{x * std::sin(half), y * std::sin(half), z * std::sin(half), std::cos(half)};
    };
    if (traverseNode && traverseYaw != 0.0f)
    {
        rotations.push_back({*traverseNode, axisAngle(0.0f, 0.0f, 1.0f, traverseYaw)});
    }
    if (lookNodes.empty() || (lookYaw == 0.0f && lookPitch == 0.0f))
    {
        return rotations;
    }
    // Pitch about forward x up, then yaw about up. Each node takes an equal power of that rotation.
    const Quaternion pitch = axisAngle(std::sin(facing), -std::cos(facing), 0.0f, lookPitch);
    const Quaternion yaw = axisAngle(0.0f, 0.0f, 1.0f, lookYaw);
    const Quaternion turn = {yaw[3] * pitch[0] - yaw[2] * pitch[1], yaw[3] * pitch[1] + yaw[2] * pitch[0],
        yaw[2] * pitch[3], yaw[3] * pitch[3]};
    const float sinHalf = std::hypot(turn[0], turn[1], turn[2]);
    const float angle = 2.0f * std::atan2(sinHalf, turn[3]) / float(lookNodes.size());
    const Quaternion share = axisAngle(turn[0] / sinHalf, turn[1] / sinHalf, turn[2] / sinHalf, angle);
    rotations.reserve(rotations.size() + lookNodes.size());
    for (uint32_t node : lookNodes)
    {
        rotations.push_back({node, share});
    }
    return rotations;
}
}
