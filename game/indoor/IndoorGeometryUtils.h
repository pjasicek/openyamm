#pragma once

#include "game/indoor/IndoorMapData.h"
#include "game/indoor/IndoorMovers.h"
#include "game/events/EventRuntime.h"
#include "game/maps/DecorationModelPlacement.h"
#include "game/maps/MapDeltaData.h"

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace OpenYAMM::Game
{
// Integer vertex rounding tilts many vertical in-between facets slightly upward (one unit over a 256-unit cave wall
// gives 0.004). Facets steeper than about 84 degrees have almost no floor footprint, so they are walls: they neither
// define floor height nor act as steep floors.
inline constexpr float IndoorMinimumSteepFloorNormalZ = 0.1f;

enum class IndoorProjectionAxis : uint8_t
{
    DropX = 0,
    DropY,
    DropZ,
};

struct IndoorProjectedFacePoint
{
    float x = 0.0f;
    float y = 0.0f;
};

enum class IndoorFaceKind : uint8_t
{
    Unknown = 0,
    Floor,
    Ceiling,
    Wall,
};

struct IndoorFaceGeometryData
{
    size_t faceIndex = 0;
    uint32_t attributes = 0;
    uint16_t sectorId = 0;
    uint16_t backSectorId = 0;
    uint8_t facetType = 0;
    bool isPortal = false;
    bool hasPlane = false;
    bool isWalkable = false;
    IndoorFaceKind kind = IndoorFaceKind::Unknown;
    float minX = 0.0f;
    float maxX = 0.0f;
    float minY = 0.0f;
    float maxY = 0.0f;
    float minZ = 0.0f;
    float maxZ = 0.0f;
    IndoorProjectionAxis projectionAxis = IndoorProjectionAxis::DropZ;
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
    std::vector<bx::Vec3> vertices;
    std::vector<IndoorProjectedFacePoint> projectedVertices;
};

class IndoorSectorFaceGrid;

class IndoorFaceGeometryCache
{
public:
    IndoorFaceGeometryCache() = default;
    explicit IndoorFaceGeometryCache(size_t faceCount);

    void reset(size_t faceCount);
    void invalidateFace(size_t faceIndex);
    void setAttributeOverrides(const MapDeltaData *pMapDeltaData);
    const IndoorFaceGeometryData *geometryForFace(
        const IndoorMapData &indoorMapData,
        const std::vector<IndoorVertex> &vertices,
        size_t faceIndex
    );
    // De-duplication of face lists without sorting: beginFaceVisit() starts an empty set, and markFaceVisited()
    // returns true only the first time a face is marked in it.
    void beginFaceVisit();
    bool markFaceVisited(size_t faceIndex);
    // The sector face grid (IndoorSectorFaceGrid.h) that queries through this cache may use; none by default. It must
    // belong to the map and vertices the cache serves.
    void setSectorFaceGrid(const IndoorSectorFaceGrid *pGrid)
    {
        m_pSectorFaceGrid = pGrid;
    }

    const IndoorSectorFaceGrid *sectorFaceGrid() const
    {
        return m_pSectorFaceGrid;
    }

private:
    const IndoorSectorFaceGrid *m_pSectorFaceGrid = nullptr;
    const MapDeltaData *m_pAttributeOverrides = nullptr;
    uint64_t m_attributeRevision = 0;
    std::vector<uint8_t> m_entryStates;
    std::vector<IndoorFaceGeometryData> m_entries;
    std::vector<uint32_t> m_faceVisitStamps;
    uint32_t m_faceVisitStamp = 1;
};

struct IndoorFloorSample
{
    bool hasFloor = false;
    bool isWalkable = false;
    float height = 0.0f;
    float normalZ = 1.0f;
    int16_t sectorId = -1;
    size_t faceIndex = static_cast<size_t>(-1);
};

struct IndoorCeilingSample
{
    bool hasCeiling = false;
    float height = 0.0f;
    int16_t sectorId = -1;
    size_t faceIndex = static_cast<size_t>(-1);
};

struct IndoorInitialActorPlacement
{
    bool hasFloor = false;
    // Report body-size/room mismatches separately from missing support.
    bool hasClearance = false;
    bool movedHorizontally = false;
    bool wallOverlapResolved = false;
    bool verticalOverlapResolved = false;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    int16_t sectorId = -1;
};

struct IndoorPortalSectorTrace
{
    bool reachedTargetSector = false;
    std::vector<int16_t> sectorIds;
};

std::vector<IndoorVertex> buildIndoorMechanismAdjustedVertices(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pIndoorMapDeltaData,
    const EventRuntimeState *pEventRuntimeState
);
// A door's vertices at `distance`: linear doors as the original engines move them; a door with a rotating mover
// (pMover, devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md) turned about its hinge, `rotationDirection` its open-away
// sign.
void applyIndoorMechanismDoorToVertices(
    const MapDeltaDoor &door,
    const IndoorMoverDefinition *pMover,
    float distance,
    int8_t rotationDirection,
    std::vector<IndoorVertex> &vertices
);
std::vector<std::vector<uint16_t>> buildNeighboringIndoorSectorIds(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pMapDeltaData = nullptr);
float fixedIndoorDoorDirectionComponentToFloat(int value);
bool indoorDoorCarriesPartySupport(const MapDeltaDoor &door);
bool mechanismDoorContainsFace(const MapDeltaDoor &door, size_t faceIndex);
// Per face, the motion of the rotating mover that moves it from its stored pose to its current pose; empty when the
// map has no rotating mover (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md).
std::vector<std::optional<IndoorRigidMotion>> buildIndoorRotatingFaceMotions(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pIndoorMapDeltaData,
    const EventRuntimeState *pEventRuntimeState);
bx::Vec3 indoorVertexToWorld(const IndoorVertex &vertex);
bool buildIndoorFaceGeometry(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    size_t faceIndex,
    IndoorFaceGeometryData &geometry,
    const MapDeltaData *pMapDeltaData = nullptr
);
bool isPointInsideIndoorPolygonProjected(
    const bx::Vec3 &point,
    const std::vector<bx::Vec3> &vertices,
    const bx::Vec3 &normal
);
int16_t indoorSectorBehindPortal(const IndoorFaceGeometryData &geometry, int16_t currentSectorId);
IndoorPortalSectorTrace traceIndoorLineThroughPortalSectors(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    const bx::Vec3 &start,
    int16_t sourceSectorId,
    const bx::Vec3 &end,
    int16_t targetSectorId,
    int portalLimit
);
float calculateIndoorFaceHeight(const IndoorFaceGeometryData &geometry, float x, float y);
bool isIndoorCylinderBlockedByFace(
    const IndoorFaceGeometryData &geometry,
    float x,
    float y,
    float z,
    float radius,
    float height
);
IndoorInitialActorPlacement resolveIndoorInitialActorPlacement(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    float x,
    float y,
    float z,
    float radius,
    float height,
    bool canFly,
    float maxRise,
    float maxDrop,
    std::optional<int16_t> preferredSectorId = std::nullopt
);
// Placement only: unlike movement queries, search the requested vertical interval for misplaced markers.
IndoorFloorSample sampleIndoorPlacementFloor(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    std::optional<int16_t> preferredSectorId = std::nullopt
);
IndoorInitialActorPlacement resolveIndoorEncounterPlacement(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    const IndoorSpawn &spawn,
    uint32_t spawnOrdinal,
    float radius,
    float height,
    bool canFly
);
IndoorFloorSample sampleIndoorFloor(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    std::optional<int16_t> preferredSectorId = std::nullopt,
    const std::vector<uint8_t> *pFaceExclusionMask = nullptr,
    IndoorFaceGeometryCache *pGeometryCache = nullptr
);
IndoorFloorSample sampleIndoorFloorOnFace(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    size_t faceIndex,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    const std::vector<uint8_t> *pFaceExclusionMask = nullptr,
    IndoorFaceGeometryCache *pGeometryCache = nullptr
);
std::optional<bx::Vec3> chooseIndoorBountyHuntSpawnPoint(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pIndoorMapDeltaData,
    const EventRuntimeState *pEventRuntimeState,
    uint32_t seed
);
IndoorCeilingSample sampleIndoorCeiling(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    float x,
    float y,
    float z,
    std::optional<int16_t> preferredSectorId = std::nullopt,
    const std::vector<uint8_t> *pFaceExclusionMask = nullptr,
    IndoorFaceGeometryCache *pGeometryCache = nullptr
);
std::optional<int16_t> findIndoorSectorForPoint(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const bx::Vec3 &point,
    IndoorFaceGeometryCache *pGeometryCache = nullptr,
    bool allowBoundingSectorFallback = true
);
// The wall face nearest to a point among the solid (non-portal) faces as steep as walls (cave walls are often
// classed as ceilings or floors), within reach: the nearest point of the face and its horizontal normal turned
// toward the point.
std::optional<DecorationWallContact> findIndoorWallContact(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const bx::Vec3 &point,
    float reach
);
// Texels a door-moved face may differ by from the original engines' door mapping and still count as that mapping:
// integer texels on integer vertices round by up to a texel either way.
inline constexpr float IndoorMoverFaceTexelTolerance = 2.0f;

// Whether a face that moves whole with its door keeps its stored texels. The original engines redraw a door face
// from its geometry at one texel per unit (the projection's texels per vertex, `geometryTexels`), ignoring the BLV's
// texels (`storedTexels`, with the face's delta, in the BLV's vertex pose). Every MM6-MM8 face that moves whole
// stores that mapping up to a constant offset (within the tolerance), so it keeps the geometric rule. A converted
// map's mover (the MM9 rework's doors, about 0.52 texels per unit and often rotated) stores its own mapping, which
// then moves with the face as MM9 draws it.
bool indoorMoverFaceKeepsStoredTexels(
    std::span<const IndoorProjectedFacePoint> geometryTexels,
    std::span<const IndoorProjectedFacePoint> storedTexels
);

// Where a wall-mounted decoration standing at (x, y, z) hangs: the nearest wall within a few dozen units, measured
// at half its height.
std::optional<DecorationWallContact> findIndoorDecorationWall(
    const IndoorMapData &indoorMapData,
    int x,
    int y,
    int z,
    float height
);
}
