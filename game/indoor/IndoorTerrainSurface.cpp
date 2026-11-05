#include "game/indoor/IndoorTerrainSurface.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float CellSize = 128.0f;
// The normal's reach: about a quarter of MM9's terrain polygons, so the shading turns over a band along each edge and
// the flat middle of a big polygon keeps its own slope.
constexpr float NormalReach = 96.0f;
// Wider for the slope layer, so it follows the cliffs, not each facet.
constexpr float SteepnessReach = 192.0f;
// Faces meeting at more than about 70 degrees keep a crease.
constexpr float CreaseCosine = 0.34f;

bx::Vec3 closestPointOnTriangle(const bx::Vec3 &p, const bx::Vec3 &a, const bx::Vec3 &b, const bx::Vec3 &c)
{
    const bx::Vec3 ab = bx::sub(b, a);
    const bx::Vec3 ac = bx::sub(c, a);
    const bx::Vec3 ap = bx::sub(p, a);
    const float d1 = bx::dot(ab, ap);
    const float d2 = bx::dot(ac, ap);
    if (d1 <= 0.0f && d2 <= 0.0f)
    {
        return a;
    }
    const bx::Vec3 bp = bx::sub(p, b);
    const float d3 = bx::dot(ab, bp);
    const float d4 = bx::dot(ac, bp);
    if (d3 >= 0.0f && d4 <= d3)
    {
        return b;
    }
    const float vc = d1 * d4 - d3 * d2;
    if (vc <= 0.0f && d1 >= 0.0f && d3 <= 0.0f)
    {
        return bx::mad(ab, d1 / (d1 - d3), a);
    }
    const bx::Vec3 cp = bx::sub(p, c);
    const float d5 = bx::dot(ab, cp);
    const float d6 = bx::dot(ac, cp);
    if (d6 >= 0.0f && d5 <= d6)
    {
        return c;
    }
    const float vb = d5 * d2 - d1 * d6;
    if (vb <= 0.0f && d2 >= 0.0f && d6 <= 0.0f)
    {
        return bx::mad(ac, d2 / (d2 - d6), a);
    }
    const float va = d3 * d6 - d5 * d4;
    if (va <= 0.0f && (d4 - d3) >= 0.0f && (d5 - d6) >= 0.0f)
    {
        return bx::mad(bx::sub(c, b), (d4 - d3) / ((d4 - d3) + (d5 - d6)), b);
    }
    const float denominator = 1.0f / (va + vb + vc);
    return bx::add(a, bx::add(bx::mul(ab, vb * denominator), bx::mul(ac, vc * denominator)));
}
}

void IndoorTerrainSurface::build(const IndoorMapData &map, const std::vector<IndoorVertex> &vertices,
    const std::vector<uint8_t> &terrainFaces)
{
    clear();
    m_faceNormals.assign(map.faces.size(), {0.0f, 0.0f, 0.0f});
    for (size_t faceIndex = 0; faceIndex < map.faces.size() && faceIndex < terrainFaces.size(); ++faceIndex)
    {
        const IndoorFace &face = map.faces[faceIndex];
        if (terrainFaces[faceIndex] == 0 || face.vertexIndices.size() < 3)
        {
            continue;
        }
        std::vector<bx::Vec3> points;
        points.reserve(face.vertexIndices.size());
        for (uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= vertices.size())
            {
                points.clear();
                break;
            }
            const IndoorVertex &vertex = vertices[vertexIndex];
            points.push_back({float(vertex.x), float(vertex.y), float(vertex.z)});
        }
        if (points.size() < 3)
        {
            continue;
        }
        // Newell's normal of the winding.
        bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
        for (size_t index = 0; index < points.size(); ++index)
        {
            const bx::Vec3 &current = points[index];
            const bx::Vec3 &next = points[(index + 1) % points.size()];
            normal.x += (current.y - next.y) * (current.z + next.z);
            normal.y += (current.z - next.z) * (current.x + next.x);
            normal.z += (current.x - next.x) * (current.y + next.y);
        }
        const float length = bx::length(normal);
        if (length < 1.0e-3f)
        {
            continue;
        }
        normal = bx::mul(normal, 1.0f / length);
        // The imported plane gives the front where the face has one.
        if (face.planeNormal)
        {
            const bx::Vec3 plane = {float((*face.planeNormal)[0]), float((*face.planeNormal)[1]),
                float((*face.planeNormal)[2])};
            if (bx::dot(plane, normal) < 0.0f)
            {
                normal = bx::neg(normal);
            }
        }
        m_faceNormals[faceIndex] = normal;
        for (size_t index = 1; index + 1 < points.size(); ++index)
        {
            Triangle triangle;
            triangle.a = points[0];
            triangle.b = points[index];
            triangle.c = points[index + 1];
            triangle.normal = normal;
            triangle.area = 0.5f * bx::length(bx::cross(bx::sub(triangle.b, triangle.a),
                bx::sub(triangle.c, triangle.a)));
            if (triangle.area <= 0.0f)
            {
                continue;
            }
            const uint32_t triangleIndex = uint32_t(m_triangles.size());
            const float minX = std::min({triangle.a.x, triangle.b.x, triangle.c.x});
            const float maxX = std::max({triangle.a.x, triangle.b.x, triangle.c.x});
            const float minY = std::min({triangle.a.y, triangle.b.y, triangle.c.y});
            const float maxY = std::max({triangle.a.y, triangle.b.y, triangle.c.y});
            for (int cellY = int(std::floor(minY / CellSize)); cellY <= int(std::floor(maxY / CellSize)); ++cellY)
            {
                for (int cellX = int(std::floor(minX / CellSize)); cellX <= int(std::floor(maxX / CellSize)); ++cellX)
                {
                    m_cells[cellKey(cellX, cellY)].push_back(triangleIndex);
                }
            }
            m_triangles.push_back(triangle);
        }
    }
}

void IndoorTerrainSurface::clear()
{
    m_triangles.clear();
    m_faceNormals.clear();
    m_cells.clear();
}

bx::Vec3 IndoorTerrainSurface::weightedNormal(const bx::Vec3 &point, float reach, const bx::Vec3 *pFaceNormal) const
{
    bx::Vec3 sum = {0.0f, 0.0f, 0.0f};
    // Triangles smaller than a quarter of the reach squared count by their area, so slivers barely tilt it.
    const float fullArea = reach * reach * 0.25f;
    const int firstX = int(std::floor((point.x - reach) / CellSize));
    const int lastX = int(std::floor((point.x + reach) / CellSize));
    const int firstY = int(std::floor((point.y - reach) / CellSize));
    const int lastY = int(std::floor((point.y + reach) / CellSize));
    std::vector<uint32_t> seen;
    for (int cellY = firstY; cellY <= lastY; ++cellY)
    {
        for (int cellX = firstX; cellX <= lastX; ++cellX)
        {
            const auto cell = m_cells.find(cellKey(cellX, cellY));
            if (cell == m_cells.end())
            {
                continue;
            }
            for (uint32_t triangleIndex : cell->second)
            {
                if (std::find(seen.begin(), seen.end(), triangleIndex) != seen.end())
                {
                    continue;
                }
                seen.push_back(triangleIndex);
                const Triangle &triangle = m_triangles[triangleIndex];
                if (pFaceNormal != nullptr && bx::dot(triangle.normal, *pFaceNormal) < CreaseCosine)
                {
                    continue;
                }
                const float distance =
                    bx::length(bx::sub(closestPointOnTriangle(point, triangle.a, triangle.b, triangle.c), point));
                if (distance >= reach)
                {
                    continue;
                }
                const float falloff = 1.0f - distance / reach;
                const float weight = falloff * falloff * std::min(triangle.area / fullArea, 1.0f);
                sum = bx::mad(triangle.normal, weight, sum);
            }
        }
    }
    return sum;
}

bx::Vec3 IndoorTerrainSurface::normalAt(const bx::Vec3 &point, const bx::Vec3 &faceNormal) const
{
    const bx::Vec3 sum = weightedNormal(point, NormalReach, &faceNormal);
    const float length = bx::length(sum);
    return length > 1.0e-6f ? bx::mul(sum, 1.0f / length) : faceNormal;
}

float IndoorTerrainSurface::steepnessAt(const bx::Vec3 &point) const
{
    const bx::Vec3 sum = weightedNormal(point, SteepnessReach, nullptr);
    const float length = bx::length(sum);
    return length > 1.0e-6f ? std::clamp(1.0f - sum.z / length, 0.0f, 1.0f) : 0.0f;
}
} // namespace OpenYAMM::Game
