#pragma once

#include <bx/math.h>

namespace OpenYAMM::Game
{
struct BillboardQuad
{
    bx::Vec3 center = {0.0f, 0.0f, 0.0f};
    bx::Vec3 right = {0.0f, 0.0f, 0.0f};
    bx::Vec3 up = {0.0f, 0.0f, 0.0f};
};

inline BillboardQuad billboardQuad(
    const bx::Vec3 &center, const bx::Vec3 &cameraRight, const bx::Vec3 &cameraUp,
    float worldWidth, float worldHeight)
{
    return {center, bx::mul(cameraRight, worldWidth * 0.5f), bx::mul(cameraUp, worldHeight * 0.5f)};
}

inline bx::Vec3 bottomAnchoredBillboardCenter(
    float x,
    float y,
    float z,
    const bx::Vec3 &cameraUp,
    float worldHeight)
{
    const float halfHeight = worldHeight * 0.5f;

    return {
        x + cameraUp.x * halfHeight,
        y + cameraUp.y * halfHeight,
        z + cameraUp.z * halfHeight,
    };
}
}
