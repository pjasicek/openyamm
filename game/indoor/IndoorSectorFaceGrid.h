#pragma once

#include "game/indoor/IndoorMapData.h"

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace OpenYAMM::Game
{
struct MapDeltaData;
class IndoorFaceGeometryCache;

// A uniform x/y grid over each sector's faces, so that line of sight, projectile and item sweeps and the sector
// lookup for a point test only the faces near them instead of every face of the sector
// (devdocs/mm9_rework/BLV_GEOMETRY_COSTS.md, E2). A cell lists the faces whose bounds, widened by a small padding,
// overlap it. Faces a door or mover can move (and faces without usable geometry) are not placed by their bounds:
// segment queries always return them, and point queries list them in every cell.
class IndoorSectorFaceGrid
{
public:
    // `vertices` are the map's vertices in the current door pose; only faces no door moves are placed by them.
    void build(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        const MapDeltaData *pMapDeltaData);
    void clear();
    bool empty() const;
    size_t memoryBytes() const;

    // Appends the faces of a sector's floor, wall, ceiling and cylinder lists that a segment, widened by `margin` in
    // x and y, may touch, skipping faces already marked in the cache's current face visit. A face is in the result
    // whenever the segment crosses it, or passes within `margin` of it.
    void appendSegmentFaces(
        int16_t sectorId,
        const bx::Vec3 &start,
        const bx::Vec3 &end,
        float margin,
        IndoorFaceGeometryCache &geometryCache,
        std::vector<size_t> &faceIndices) const;
    // The faces of a sector's floor (or portal, or ceiling) list whose bounds, widened by up to PointSlack, may hold
    // the point (x, y): a subsequence of the sector's list in its order.
    std::span<const uint16_t> floorFacesAt(int16_t sectorId, float x, float y) const;
    std::span<const uint16_t> portalFacesAt(int16_t sectorId, float x, float y) const;
    std::span<const uint16_t> ceilingFacesAt(int16_t sectorId, float x, float y) const;

    static constexpr float PointSlack = 8.0f;

private:
    struct CellLists
    {
        // Cell c holds faceIds[cellStarts[c] .. cellStarts[c + 1]).
        std::vector<uint32_t> cellStarts;
        std::vector<uint16_t> faceIds;
    };

    struct SectorGrid
    {
        float originX = 0.0f;
        float originY = 0.0f;
        float cellSize = 1.0f;
        int32_t cellsX = 1;
        int32_t cellsY = 1;
        CellLists collision;
        CellLists floor;
        CellLists portal;
        CellLists ceiling;
        std::vector<uint16_t> movingCollisionFaceIds;
    };

    int32_t cellIndexAt(const SectorGrid &grid, float x, float y) const;
    static std::span<const uint16_t> cellFaces(const CellLists &lists, int32_t cellIndex);

    std::vector<SectorGrid> m_sectors;
};

// The faces of the sectors' floor, wall, ceiling and cylinder lists that a segment may touch (see
// IndoorSectorFaceGrid::appendSegmentFaces), each once and in no particular order. With a grid attached to the cache
// only the faces near the segment are returned; without one, every face of those lists.
void collectIndoorSegmentFaceCandidates(
    const IndoorMapData &indoorMapData,
    IndoorFaceGeometryCache &geometryCache,
    const std::vector<int16_t> &sectorIds,
    const bx::Vec3 &start,
    const bx::Vec3 &end,
    float margin,
    std::vector<size_t> &faceIndices);
}
