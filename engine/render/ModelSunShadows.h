#pragma once

#include "engine/models/ModelAsset.h"

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

namespace OpenYAMM::Engine
{
constexpr size_t ModelSunShadowCascades = 2;
constexpr uint16_t ModelSunShadowSize = 2048;
constexpr std::array<float, ModelSunShadowCascades> ModelSunShadowRadii = {1024.0f, 4096.0f};

struct ModelShadowSettings
{
    uint16_t size = 0;
    std::array<float, 2> radii = {};
};

inline ModelShadowSettings modelShadowSettings(int quality)
{
    switch (quality)
    {
    case 1: return {512, {512, 1536}};
    case 2: return {1024, {768, 3072}};
    case 3: return {2048, ModelSunShadowRadii};
    default: return {};
    }
}

struct ModelSunShadowCascade
{
    ModelMatrix view = {};
    ModelMatrix projection = {};
    ModelMatrix textureMatrix = {};
};

inline ModelSunShadowCascade modelSunShadowCascade(const std::array<float, 3> &camera,
    const std::array<float, 3> &direction, float radius, bool homogeneousDepth, bool originBottomLeft,
    uint16_t resolution = ModelSunShadowSize)
{
    const bx::Vec3 light = bx::normalize({direction[0], direction[1], direction[2]});
    const bx::Vec3 up = std::abs(light.z) > 0.95f ? bx::Vec3{0, 1, 0} : bx::Vec3{0, 0, 1};
    const bx::Vec3 right = bx::normalize(bx::cross(up, light));
    const bx::Vec3 vertical = bx::cross(light, right);
    const bx::Vec3 eye = {camera[0], camera[1], camera[2]};
    const float texel = 2.0f * radius / resolution;
    const float x = bx::dot(eye, right);
    const float y = bx::dot(eye, vertical);
    // Fixed extents and texel-snapped light-space translation keep camera turns and subtexel movement stable.
    const bx::Vec3 center = bx::add(eye, bx::add(
        bx::mul(right, std::round(x / texel) * texel - x),
        bx::mul(vertical, std::round(y / texel) * texel - y)));
    constexpr float depthRadius = 8192.0f;
    ModelSunShadowCascade result;
    bx::mtxLookAt(result.view.data(), bx::add(center, bx::mul(light, depthRadius)), center,
        up, bx::Handedness::Right);
    bx::mtxOrtho(result.projection.data(), -radius, radius, -radius, radius, 0.0f, 2.0f * depthRadius,
        0.0f, homogeneousDepth, bx::Handedness::Right);
    ModelMatrix clipToTexture = identityModelMatrix();
    clipToTexture[0] = 0.5f;
    clipToTexture[5] = originBottomLeft ? 0.5f : -0.5f;
    clipToTexture[10] = homogeneousDepth ? 0.5f : 1.0f;
    clipToTexture[12] = clipToTexture[13] = 0.5f;
    clipToTexture[14] = homogeneousDepth ? 0.5f : 0.0f;
    ModelMatrix viewProjection;
    bx::mtxMul(viewProjection.data(), result.view.data(), result.projection.data());
    bx::mtxMul(result.textureMatrix.data(), viewProjection.data(), clipToTexture.data());
    return result;
}

inline bool modelSunShadowIntersects(const ModelSunShadowCascade &cascade, const ModelBounds &bounds)
{
    if (!bounds.valid)
    {
        return false;
    }
    constexpr float infinity = std::numeric_limits<float>::infinity();
    std::array<float, 3> low = {infinity, infinity, infinity};
    std::array<float, 3> high = {-infinity, -infinity, -infinity};
    for (uint32_t corner = 0; corner < 8; ++corner)
    {
        const float point[4] = {corner & 1 ? bounds.max[0] : bounds.min[0],
            corner & 2 ? bounds.max[1] : bounds.min[1], corner & 4 ? bounds.max[2] : bounds.min[2], 1.0f};
        float projected[4];
        bx::vec4MulMtx(projected, point, cascade.textureMatrix.data());
        for (size_t axis = 0; axis < 3; ++axis)
        {
            low[axis] = std::min(low[axis], projected[axis]);
            high[axis] = std::max(high[axis], projected[axis]);
        }
    }
    for (size_t axis = 0; axis < 3; ++axis)
    {
        if (low[axis] > 1.00001f || high[axis] < -0.00001f)
        {
            return false;
        }
    }
    return true;
}
}
