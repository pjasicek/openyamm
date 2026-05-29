#pragma once

#include "game/mm9/Mm9DatPhysicsQuery.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9DatCollisionWorldBuildOptions
{
    float horizontalCellSize = 512.0f;
};

struct Mm9DatCollisionWorldStats
{
    size_t sourceTriangleCount = 0;
    size_t indexedTriangleCount = 0;
    size_t cellCount = 0;
    size_t cellTriangleRefs = 0;
    size_t maxCellTriangleRefs = 0;
    float horizontalCellSize = 0.0f;
    bool valid = false;
};

struct Mm9DatFloorSupportQuery
{
    Mm9DatVec3 position;
    uint32_t channelMask = Mm9DatPhysicsQueryChannelPhysics;
    float maxDropDistance = 10000.0f;
    float halfHeight = 0.0f;
    float placementBias = 0.1f;
    bool includeBackfaces = true;
};

struct Mm9DatFloorSupportHit
{
    Mm9DatVec3 floorPoint;
    Mm9DatVec3 normal;
    Mm9DatVec3 adjustedPosition;
    float rayDistance = 0.0f;
    float dropDistance = 0.0f;
    size_t testedTriangleCount = 0;
    size_t candidateTriangleCount = 0;
    Mm9DatPhysicsSourceRef source;
};

struct Mm9DatCollisionRayHit
{
    Mm9DatPhysicsRayHit hit;
    size_t testedTriangleCount = 0;
    size_t candidateTriangleCount = 0;
};

class Mm9DatCollisionWorld
{
public:
    bool build(
        const Mm9DatPhysicsQueryView &queryView,
        const Mm9DatCollisionWorldBuildOptions &options = {});

    const Mm9DatCollisionWorldStats &stats() const;

    std::optional<Mm9DatFloorSupportHit> findFloorSupport(
        const Mm9DatFloorSupportQuery &query) const;

    std::optional<Mm9DatCollisionRayHit> segmentcast(
        const Mm9DatVec3 &start,
        const Mm9DatVec3 &end,
        const Mm9DatPhysicsRaycastOptions &options = {}) const;

private:
    struct CellCoord
    {
        int32_t x = 0;
        int32_t z = 0;
    };

    static int64_t cellKey(const CellCoord &coord);
    CellCoord cellCoordForPoint(const Mm9DatVec3 &point) const;
    std::vector<size_t> triangleIndicesForHorizontalBounds(
        float minX,
        float maxX,
        float minZ,
        float maxZ) const;

    std::vector<Mm9DatPhysicsQueryTriangle> m_triangles;
    float m_horizontalCellSize = 512.0f;
    Mm9DatCollisionWorldStats m_stats;
    std::unordered_map<int64_t, std::vector<size_t>> m_triangleIndicesByCell;
};
}
