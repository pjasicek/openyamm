#pragma once

#include "game/FaceEnums.h"
#include "game/render/BillboardGeometry.h"
#include "game/render/WaterRenderer.h"
#include "game/tables/SurfaceMaterialTable.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <map>
#include <stdexcept>
#include <yaml-cpp/yaml.h>

namespace OpenYAMM::Game
{
inline std::map<std::string, std::vector<std::vector<std::array<float, 3>>>>
parseSpriteWaterStrips(const std::string &yaml)
{
    const YAML::Node textures = YAML::Load(yaml)["textures"];
    if (!textures.IsMap())
    {
        throw std::invalid_argument("Water sprite textures must be a map");
    }
    std::map<std::string, std::vector<std::vector<std::array<float, 3>>>> materials;
    for (const auto &texture : textures)
    {
        if (!texture.second.IsSequence())
        {
            throw std::invalid_argument("Water sprite strips must be a sequence");
        }
        auto &strips = materials[texture.first.as<std::string>()];
        for (const YAML::Node &strip : texture.second)
        {
            if (!strip.IsSequence() || strip.size() < 2)
            {
                throw std::invalid_argument("Water strip requires at least two cross sections");
            }
            std::vector<std::array<float, 3>> sections;
            for (const YAML::Node &section : strip)
            {
                if (!section.IsSequence() || section.size() != 3)
                {
                    throw std::invalid_argument("Water cross section requires [left, right, v]");
                }
                const float invalid = std::numeric_limits<float>::quiet_NaN();
                const std::array<float, 3> point = {
                    section[0].as<float>(invalid), section[1].as<float>(invalid), section[2].as<float>(invalid)};
                if (!std::all_of(point.begin(), point.end(), [](float value)
                        { return std::isfinite(value) && value >= 0.0f && value <= 1.0f; })
                    || point[0] >= point[1] || (!sections.empty() && point[2] <= sections.back()[2]))
                {
                    throw std::invalid_argument("Water strip must stay inside the sprite and advance downward");
                }
                sections.push_back(point);
            }
            strips.push_back(std::move(sections));
        }
    }
    return materials;
}

inline bool isWaterSurface(uint32_t attributes, SurfaceMaterialSemantic semantic)
{
    return !hasFaceAttribute(attributes, FaceAttribute::Lava)
        && !hasFaceAttribute(attributes, FaceAttribute::IndoorSky)
        && semantic != SurfaceMaterialSemantic::Lava
        && (hasFaceAttribute(attributes, FaceAttribute::Fluid) || semantic == SurfaceMaterialSemantic::Water);
}

inline std::array<float, 2> waterFaceFlow(const std::array<bx::Vec3, 3> &positions,
    const std::array<std::array<float, 2>, 3> &uvs, float flowU, float flowV)
{
    const bx::Vec3 edge1 = bx::sub(positions[1], positions[0]);
    const bx::Vec3 edge2 = bx::sub(positions[2], positions[0]);
    const float u1 = uvs[1][0] - uvs[0][0];
    const float v1 = uvs[1][1] - uvs[0][1];
    const float u2 = uvs[2][0] - uvs[0][0];
    const float v2 = uvs[2][1] - uvs[0][1];
    const float determinant = u1 * v2 - v1 * u2;
    const bx::Vec3 normal = bx::cross(edge1, edge2);
    if (std::abs(determinant) < 0.000001f || bx::dot(normal, normal) < 0.0001f)
    {
        return {};
    }
    const bx::Vec3 velocity = bx::mul(bx::add(
        bx::mul(bx::sub(bx::mul(edge1, v2), bx::mul(edge2, v1)), flowU),
        bx::mul(bx::sub(bx::mul(edge2, u1), bx::mul(edge1, u2)), flowV)), 1.0f / determinant);
    const bx::Vec3 unitNormal = bx::normalize(normal);
    const bx::Vec3 tangent = std::abs(unitNormal.z) > 0.99f ? bx::Vec3{1.0f, 0.0f, 0.0f}
        : bx::normalize(bx::cross(bx::Vec3{0.0f, 0.0f, 1.0f}, unitNormal));
    const bx::Vec3 bitangent = bx::cross(unitNormal, tangent);
    return {bx::dot(velocity, tangent) / 768.0f, bx::dot(velocity, bitangent) / 768.0f};
}

inline std::vector<WaterVertex> buildSpriteWaterGeometry(const BillboardQuad &quad,
    std::span<const std::vector<std::array<float, 3>>> strips, bool mirrored)
{
    std::vector<WaterVertex> vertices;
    const bx::Vec3 normal = bx::normalize(bx::cross(quad.right, quad.up));
    for (const std::vector<std::array<float, 3>> &strip : strips)
    {
        for (size_t index = 1; index < strip.size(); ++index)
        {
            const auto &a = strip[index - 1];
            const auto &b = strip[index];
            const std::array<std::array<float, 2>, 4> uv = {{{a[0], a[2]}, {a[1], a[2]},
                {b[0], b[2]}, {b[1], b[2]}}};
            std::array<bx::Vec3, 4> positions = {bx::Vec3{0, 0, 0}, bx::Vec3{0, 0, 0},
                bx::Vec3{0, 0, 0}, bx::Vec3{0, 0, 0}};
            for (size_t corner = 0; corner < positions.size(); ++corner)
            {
                const float u = mirrored ? 1.0f - uv[corner][0] : uv[corner][0];
                positions[corner] = bx::add(quad.center, bx::add(bx::mul(quad.right, u * 2.0f - 1.0f),
                    bx::mul(quad.up, 1.0f - uv[corner][1] * 2.0f)));
                positions[corner] = bx::add(positions[corner], bx::mul(normal, 0.1f));
            }
            for (size_t corner : {0u, 2u, 1u, 1u, 2u, 3u})
            {
                const bx::Vec3 &position = positions[corner];
                vertices.push_back({position.x, position.y, position.z, normal.x, normal.y, normal.z,
                    uv[corner][0], uv[corner][1], -2.0f, 0.0f, 0xcc634529u});
            }
        }
    }
    return vertices;
}

// Partition horizontal levels so a waterfall or a stepped pool cannot acquire an incorrect planar reflection.
inline std::vector<WaterSurfaceGeometry> buildWaterFaceGeometry(std::span<const WaterVertex> vertices,
    int16_t sectorId, int16_t backSectorId)
{
    std::vector<WaterSurfaceGeometry> geometry;
    for (size_t index = 0; index + 2 < vertices.size(); index += 3)
    {
        const WaterVertex &a = vertices[index];
        const WaterVertex &b = vertices[index + 1];
        const WaterVertex &c = vertices[index + 2];
        const bx::Vec3 normal = bx::cross(bx::Vec3{b.x - a.x, b.y - a.y, b.z - a.z},
            bx::Vec3{c.x - a.x, c.y - a.y, c.z - a.z});
        if (bx::dot(normal, normal) < 0.0001f)
        {
            continue;
        }
        const bool planar = normal.z > 0.0f && std::abs(a.z - b.z) < 0.01f && std::abs(a.z - c.z) < 0.01f;
        const float height = a.z;
        std::vector<WaterSurfaceGeometry>::iterator found = std::find_if(geometry.begin(), geometry.end(),
            [&](const WaterSurfaceGeometry &surface)
            { return surface.planar == planar && (!planar || std::abs(surface.height - height) < 0.01f); });
        if (found == geometry.end())
        {
            WaterSurfaceGeometry surface;
            surface.height = height;
            surface.planar = planar;
            surface.sectorId = sectorId;
            surface.backSectorId = backSectorId;
            surface.patches.push_back({bx::Vec3{a.x, a.y, a.z}, bx::Vec3{a.x, a.y, a.z}});
            geometry.push_back(std::move(surface));
            found = geometry.end() - 1;
        }
        const bx::Vec3 unitNormal = bx::normalize(normal);
        for (size_t corner = 0; corner < 3; ++corner)
        {
            WaterVertex vertex = vertices[index + corner];
            vertex.normalX = unitNormal.x;
            vertex.normalY = unitNormal.y;
            vertex.normalZ = unitNormal.z;
            found->vertices.push_back(vertex);
            bx::Vec3 &lo = found->patches.front()[0];
            bx::Vec3 &hi = found->patches.front()[1];
            lo = {std::min(lo.x, vertex.x), std::min(lo.y, vertex.y), std::min(lo.z, vertex.z)};
            hi = {std::max(hi.x, vertex.x), std::max(hi.y, vertex.y), std::max(hi.z, vertex.z)};
        }
    }
    return geometry;
}
}
