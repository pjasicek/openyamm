#include "game/arpg/ArpgModeCamera.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;

bx::Vec3 normalizeOrFallback(const bx::Vec3 &value, const bx::Vec3 &fallback)
{
    const float lengthSquared = value.x * value.x + value.y * value.y + value.z * value.z;

    if (lengthSquared <= 0.000001f)
    {
        return fallback;
    }

    const float invLength = 1.0f / std::sqrt(lengthSquared);
    return {value.x * invLength, value.y * invLength, value.z * invLength};
}
} // namespace

float degreesToRadians(float degrees)
{
    return degrees * (Pi / 180.0f);
}

ArpgModeCameraFrame buildArpgModeCameraFrame(const ArpgModeCameraInput &input)
{
    const float pitchRadians = std::clamp(input.pitchRadians, -1.4835298f, -0.08726646f);
    const float distance = std::max(1.0f, input.distance);
    const float cosPitch = std::cos(pitchRadians);
    const bx::Vec3 forward = normalizeOrFallback(
        bx::Vec3{
            std::cos(input.yawRadians) * cosPitch,
            std::sin(input.yawRadians) * cosPitch,
            std::sin(pitchRadians),
        },
        bx::Vec3{1.0f, 0.0f, -1.0f});

    ArpgModeCameraFrame frame = {};
    frame.at = input.target;
    frame.eye = {
        input.target.x - forward.x * distance,
        input.target.y - forward.y * distance,
        input.target.z - forward.z * distance,
    };
    frame.forward = forward;
    frame.right =
        normalizeOrFallback(
            bx::cross(frame.forward, bx::Vec3{0.0f, 0.0f, 1.0f}),
            bx::Vec3{0.0f, -1.0f, 0.0f});
    frame.up = normalizeOrFallback(bx::cross(frame.right, frame.forward), bx::Vec3{0.0f, 0.0f, 1.0f});

    bx::mtxLookAt(
        frame.viewMatrix.data(),
        frame.eye,
        frame.at,
        frame.up,
        bx::Handedness::Right);
    bx::mtxProj(
        frame.projectionMatrix.data(),
        std::clamp(input.fovDegrees, 20.0f, 90.0f),
        std::max(0.1f, input.aspectRatio),
        std::max(0.001f, input.nearClip),
        std::max(input.nearClip + 1.0f, input.farClip),
        input.homogeneousDepth,
        bx::Handedness::Right);
    return frame;
}
} // namespace OpenYAMM::Game
