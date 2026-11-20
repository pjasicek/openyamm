#pragma once

#include <bx/math.h>

#include <array>

namespace OpenYAMM::Game
{
// World-space gradients of a planar face's texture coordinates (their change per world unit), from one of its
// triangles: the tangent frame of the surface material shaders (game/shaders/surface_material.sh). Faces start their
// texture coordinates at their own edges, so screen-space derivatives break where two faces meet; these do not.
// Zero for a degenerate triangle.
inline void surfaceTextureGradients(const std::array<bx::Vec3, 3> &positions,
    const std::array<std::array<float, 2>, 3> &uvs, std::array<float, 3> &gradientU, std::array<float, 3> &gradientV)
{
    const bx::Vec3 edge1 = bx::sub(positions[1], positions[0]);
    const bx::Vec3 edge2 = bx::sub(positions[2], positions[0]);
    const bx::Vec3 normal = bx::cross(edge1, edge2);
    const bx::Vec3 edge2Perpendicular = bx::cross(edge2, normal);
    const bx::Vec3 edge1Perpendicular = bx::cross(normal, edge1);
    const float basis = bx::dot(edge1, edge2Perpendicular);
    gradientU = {};
    gradientV = {};
    if (bx::abs(basis) < 1.0e-6f)
    {
        return;
    }
    const float du1 = uvs[1][0] - uvs[0][0];
    const float du2 = uvs[2][0] - uvs[0][0];
    const float dv1 = uvs[1][1] - uvs[0][1];
    const float dv2 = uvs[2][1] - uvs[0][1];
    const bx::Vec3 u =
        bx::mul(bx::add(bx::mul(edge2Perpendicular, du1), bx::mul(edge1Perpendicular, du2)), 1.0f / basis);
    const bx::Vec3 v =
        bx::mul(bx::add(bx::mul(edge2Perpendicular, dv1), bx::mul(edge1Perpendicular, dv2)), 1.0f / basis);
    gradientU = {u.x, u.y, u.z};
    gradientV = {v.x, v.y, v.z};
}
}
