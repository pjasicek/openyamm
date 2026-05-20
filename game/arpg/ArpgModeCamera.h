#pragma once

#include <array>

#include <bx/math.h>

namespace OpenYAMM::Game
{
struct ArpgModeCameraInput
{
    bx::Vec3 target = {0.0f, 0.0f, 0.0f};
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
    float distance = 2600.0f;
    float fovDegrees = 45.0f;
    float aspectRatio = 1.0f;
    float nearClip = 0.1f;
    float farClip = 18000.0f;
    bool homogeneousDepth = false;
};

struct ArpgModeCameraFrame
{
    bx::Vec3 eye = {0.0f, 0.0f, 0.0f};
    bx::Vec3 at = {0.0f, 0.0f, 0.0f};
    bx::Vec3 forward = {1.0f, 0.0f, 0.0f};
    bx::Vec3 right = {0.0f, -1.0f, 0.0f};
    bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    std::array<float, 16> viewMatrix = {};
    std::array<float, 16> projectionMatrix = {};
};

float degreesToRadians(float degrees);
ArpgModeCameraFrame buildArpgModeCameraFrame(const ArpgModeCameraInput &input);
} // namespace OpenYAMM::Game
