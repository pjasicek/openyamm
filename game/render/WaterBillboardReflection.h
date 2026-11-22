#pragma once

#include "game/render/BillboardGeometry.h"
#include "game/render/ViewFrustum.h"
#include "game/render/WaterMath.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
constexpr float WaterBillboardDistance = 4096.0f;
constexpr float WaterBillboardFadeDistance = 3072.0f;
constexpr size_t MaxWaterBillboards = 64;

inline float waterBillboardFade(float distanceSquared)
{
    constexpr float end = WaterBillboardDistance * WaterBillboardDistance;
    constexpr float start = WaterBillboardFadeDistance * WaterBillboardFadeDistance;
    return std::clamp((end - distanceSquared) / (end - start), 0.0f, 1.0f);
}

inline uint32_t waterBillboardColor(uint32_t colorAbgr, float distanceSquared)
{
    const uint32_t alpha = uint32_t(float(colorAbgr >> 24) * waterBillboardFade(distanceSquared) + 0.5f);
    return (colorAbgr & 0x00ffffffu) | (alpha << 24);
}

// Some part of the quad lies in front of the reflecting plane (WaterMath.h) and in the reflection's frustum.
inline bool waterBillboardVisible(const BillboardQuad &quad, const ViewFrustum &frustum, const ReflectionPlane &plane)
{
    const auto along = [&plane](const bx::Vec3 &vector)
    {
        return plane[0] * vector.x + plane[1] * vector.y + plane[2] * vector.z;
    };
    return reflectionPlaneDistance(plane, quad.center) + std::abs(along(quad.right)) + std::abs(along(quad.up)) > 0.0f
        && frustum.intersectsQuad(quad.center, quad.right, quad.up);
}

// Keep the nearest candidates before the caller applies its normal transparency ordering.
template<class DrawItem>
void limitWaterBillboards(std::vector<DrawItem> &items, size_t limit)
{
    if (items.size() > limit)
    {
        std::nth_element(items.begin(), items.begin() + limit, items.end(),
            [](const DrawItem &left, const DrawItem &right)
            {
                return left.distanceSquared < right.distanceSquared;
            });
        items.resize(limit);
    }
}
}
