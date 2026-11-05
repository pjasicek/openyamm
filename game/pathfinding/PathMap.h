#pragma once

#include "game/pathfinding/PathfindingTypes.h"

#include <cstddef>
#include <cstdint>
#include <span>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct PathTraceResult
{
    bool blocked = false;
    size_t facetIndex = 0;
    PathPoint point;
};

class PathMap
{
public:
    void clear();
    void setFacets(std::vector<PathFacet> facets);
    size_t addFacet(const PathFacet &facet);
    void buildSpatialGrid(float cellSize);

    const std::vector<PathFacet> &facets() const;
    size_t revision() const;

    PathFloorSample floorAt(const PathPoint &position) const;
    PathPoint snapToWalkableSourceFacet(
        int32_t sourceId,
        const PathPoint &position,
        float maxDistance,
        bool &valid,
        PathFloorSample *pFloorSample = nullptr
    ) const;
    PathPoint snapToNearestWalkableFloor(
        const PathPoint &position,
        float maxDistance,
        bool &valid,
        PathFloorSample *pFloorSample = nullptr
    ) const;
    PathFloorQueryDebug debugFloorQuery(const PathPoint &position) const;
    PathTraceResult traceLine(
        const PathPoint &from,
        const PathPoint &to,
        float radius = 0.0f,
        bool checkBody = false
    ) const;
    bool traceWalkSegment(const PathPoint &from, const PathPoint &to, const PathObject &object) const;
    bool resolveWalkStep(const PathPoint &from, PathPoint &to, const PathObject &object) const;
    PathWalkSegmentDebug debugTraceWalkSegment(
        const PathPoint &from,
        const PathPoint &to,
        const PathObject &object
    ) const;
    bool canReachDirectly(const PathPoint &from, const PathPoint &to, const PathObject &object) const;

private:
    struct FacetGeometry
    {
        PathBounds bounds;
        PathPoint normal;
        bool valid = false;
        bool nonBlocking = false;
    };

    struct GridCellKey
    {
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;

        bool operator==(const GridCellKey &other) const;
    };

    struct GridCellKeyHash
    {
        size_t operator()(const GridCellKey &key) const;
    };

    struct FloorCellKey
    {
        int32_t x = 0;
        int32_t y = 0;

        bool operator==(const FloorCellKey &other) const;
    };

    struct FloorCellKeyHash
    {
        size_t operator()(const FloorCellKey &key) const;
    };

    struct TraceCandidateCache
    {
        struct Entry
        {
            GridCellKey minCell;
            GridCellKey maxCell;
            std::vector<size_t> facets;
        };

        std::vector<Entry> entries;
        size_t nextEntry = 0;
    };

    void candidateFacetsForBounds(
        const PathBounds &bounds,
        std::vector<size_t> &candidates,
        TraceCandidateCache *pCache = nullptr) const;
    std::span<const size_t> candidateFloorFacetsForPoint(float x, float y) const;
    // A face the walking body's low probes may touch because it will climb it (PathObject::riserHeight).
    bool isSteppableRiser(const FacetGeometry &geometry, float fromFloorZ, float riserHeight) const;
    // A riser with its tread on top, or a step's underside with its tread just above, within riserHeight of the feet:
    // a squat body's upper sphere passes it, as the low probes do (traceWalkBody).
    bool isClimbedStepFace(const PathFacet &facet, const FacetGeometry &geometry, const PathPoint &from,
        const PathPoint &to, const PathObject &object) const;
    PathTraceResult traceLineInternal(
        const PathPoint &from,
        const PathPoint &to,
        float radius,
        bool checkBody,
        TraceCandidateCache *pCache,
        float riserHeight = 0.0f,
        bool probeVerticalMoves = false) const;
    bool traceWalkSegmentInternal(
        const PathPoint &from,
        const PathPoint &to,
        const PathObject &object,
        PathWalkSegmentDebug *pDebug
    ) const;
    PathTraceResult traceWalkBody(
        const PathPoint &from,
        const PathPoint &to,
        const PathObject &object,
        TraceCandidateCache &cache) const;
    PathTraceResult traceFlyingBody(const PathPoint &from, const PathPoint &to, const PathObject &object) const;
    void rebuildGeometry();
    void rebuildSpatialGrid();
    int32_t gridCoordinate(float value) const;

    std::vector<PathFacet> m_facets;
    std::vector<FacetGeometry> m_geometry;
    std::vector<size_t> m_floorFacetIndices;
    // A cell's facets: a range of m_spatialGridFacets (m_floorGridFacets), ascending. Built from one sorted list of
    // (cell, facet) pairs: per-cell vectors cost a region-sized map (20 000 faces) ~100 ms on every rebuild.
    struct GridRange
    {
        uint32_t offset = 0;
        uint32_t count = 0;
    };
    std::unordered_map<GridCellKey, GridRange, GridCellKeyHash> m_spatialGrid;
    std::vector<size_t> m_spatialGridFacets;
    std::unordered_map<FloorCellKey, GridRange, FloorCellKeyHash> m_floorGrid;
    std::vector<size_t> m_floorGridFacets;
    // Facets in no spatial cell (too large for them, rebuildSpatialGrid): each spatial query tests them.
    std::vector<size_t> m_largeSpatialFacets;
    size_t m_revision = 0;
    float m_gridCellSize = 0.0f;
};
}
