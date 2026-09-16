#pragma once

#include <bx/math.h>

#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
// World-space planes from the exact matrices used for submission. Plane tests
// deliberately retain intersecting bounds; this does not test occlusion.
class ViewFrustum
{
public:
    ViewFrustum(const float *pViewMatrix, const float *pProjectionMatrix, bool homogeneousDepth)
    {
        float matrix[16] = {};
        bx::mtxMul(matrix, pViewMatrix, pProjectionMatrix);
        for (size_t axis = 0; axis < 3; ++axis)
        {
            for (size_t component = 0; component < 4; ++component)
            {
                const float coordinate = matrix[component * 4 + axis];
                const float w = matrix[component * 4 + 3];
                m_planes[axis * 2][component] = axis == 2 && !homogeneousDepth ? coordinate : w + coordinate;
                m_planes[axis * 2 + 1][component] = w - coordinate;
            }
        }
        for (std::array<float, 4> &plane : m_planes)
        {
            const float length = std::sqrt(plane[0] * plane[0] + plane[1] * plane[1] + plane[2] * plane[2]);
            if (length > 0.0f)
            {
                for (float &component : plane)
                {
                    component /= length;
                }
            }
        }
    }

    bool intersectsBounds(const bx::Vec3 &min, const bx::Vec3 &max) const
    {
        for (const std::array<float, 4> &plane : m_planes)
        {
            const bx::Vec3 furthest = {
                plane[0] >= 0.0f ? max.x : min.x,
                plane[1] >= 0.0f ? max.y : min.y,
                plane[2] >= 0.0f ? max.z : min.z
            };
            if (signedDistance(plane, furthest) < -BoundaryMargin)
            {
                return false;
            }
        }
        return true;
    }

    bool intersectsQuad(const bx::Vec3 &center, const bx::Vec3 &right, const bx::Vec3 &up) const
    {
        for (const std::array<float, 4> &plane : m_planes)
        {
            const float radius = std::abs(plane[0] * right.x + plane[1] * right.y + plane[2] * right.z)
                + std::abs(plane[0] * up.x + plane[1] * up.y + plane[2] * up.z);
            if (signedDistance(plane, center) + radius < -BoundaryMargin)
            {
                return false;
            }
        }
        return true;
    }

private:
    // World units: retain a small sliver beyond a clip plane to absorb float
    // roundoff at outdoor coordinates without expanding bounds by camera depth.
    static constexpr float BoundaryMargin = 0.25f;
    std::array<std::array<float, 4>, 6> m_planes = {};

    static float signedDistance(const std::array<float, 4> &plane, const bx::Vec3 &point)
    {
        return plane[0] * point.x + plane[1] * point.y + plane[2] * point.z + plane[3];
    }
};
}
