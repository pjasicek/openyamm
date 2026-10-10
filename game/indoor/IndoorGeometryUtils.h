#pragma once

#include "game/indoor/IndoorMapData.h"
#include "game/events/EventRuntime.h"
#include "game/maps/DecorationModelPlacement.h"
#include "game/maps/MapDeltaData.h"

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
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

private:
    const MapDeltaData *m_pAttributeOverrides = nullptr;
    uint64_t m_attributeRevision = 0;
    std::vector<uint8_t> m_entryStates;
    std::vector<IndoorFaceGeometryData> m_entries;
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
void applyIndoorMechanismDoorToVertices(
    const MapDeltaDoor &door,
    float distance,
    std::vector<IndoorVertex> &vertices
);
std::vector<std::vector<uint16_t>> buildNeighboringIndoorSectorIds(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pMapDeltaData = nullptr);
float fixedIndoorDoorDirectionComponentToFloat(int value);
bool indoorDoorCarriesPartySupport(const MapDeltaDoor &door);
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
