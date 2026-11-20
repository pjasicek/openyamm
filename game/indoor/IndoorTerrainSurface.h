#pragma once

#include "game/indoor/IndoorMapData.h"

#include <bx/math.h>

#include <cstdint>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// The ground of an open-air BLV's terrain faces (scene `terrain`) as a smooth surface for its blended materials
// (devdocs/INDOOR_OPEN_SKY.md "Terrain"). MM9 lit each polygon flat; here a point's normal averages the terrain
// triangles around it with a falloff over a fixed reach, so it is the same on both sides of every edge and the
// shading runs on across them, except where two faces meet at a crease sharper than the limit (a cliff's foot).
class IndoorTerrainSurface
{
public:
    // terrainFaces: per face of the map, nonzero for a terrain face; vertices: the map's (render) vertices.
    void build(const IndoorMapData &map, const std::vector<IndoorVertex> &vertices,
        const std::vector<uint8_t> &terrainFaces);
    void clear();
    bool empty() const
    {
        return m_triangles.empty();
    }
    // The smooth normal at a point of a terrain face whose own (front) normal is faceNormal.
    bx::Vec3 normalAt(const bx::Vec3 &point, const bx::Vec3 &faceNormal) const;
    // A terrain face's own front normal (zero for any other face).
    bx::Vec3 faceNormal(size_t faceIndex) const
    {
        return faceIndex < m_faceNormals.size() ? m_faceNormals[faceIndex] : bx::Vec3{0.0f, 0.0f, 0.0f};
    }
    // 1 - normal.z of the ground averaged over a wider reach (the blend's slope layer: cliffs, not every bump).
    float steepnessAt(const bx::Vec3 &point) const;

private:
    struct Triangle
    {
        bx::Vec3 a = {0.0f, 0.0f, 0.0f};
        bx::Vec3 b = {0.0f, 0.0f, 0.0f};
        bx::Vec3 c = {0.0f, 0.0f, 0.0f};
        bx::Vec3 normal = {0.0f, 0.0f, 1.0f};
        float area = 0.0f;
    };

    // The terrain normal sum within reach of the point: each triangle's normal weighted by its area within reach
    // (its distance falloff), only those within the crease limit of faceNormal when it is given.
    bx::Vec3 weightedNormal(const bx::Vec3 &point, float reach, const bx::Vec3 *pFaceNormal) const;
    int64_t cellKey(int x, int y) const
    {
        return (int64_t(x) << 32) ^ int64_t(uint32_t(y));
    }

    std::vector<Triangle> m_triangles;
    std::vector<bx::Vec3> m_faceNormals;
    // Triangle indices by the cells (CellSize square, in x and y) their bounds overlap.
    std::unordered_map<int64_t, std::vector<uint32_t>> m_cells;
};
} // namespace OpenYAMM::Game
