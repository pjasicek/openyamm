#pragma once

#include "game/indoor/IndoorMapData.h"
#include "game/events/EventRuntime.h"
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

std::vector<IndoorVertex> buildIndoorMechanismAdjustedVertices(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pIndoorMapDeltaData,
    const EventRuntimeState *pEventRuntimeState
);
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
float calculateIndoorFaceHeight(const IndoorFaceGeometryData &geometry, float x, float y);
bool isIndoorCylinderBlockedByFace(
    const IndoorFaceGeometryData &geometry,
    float x,
    float y,
    float z,
    float radius,
    float height
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
}
