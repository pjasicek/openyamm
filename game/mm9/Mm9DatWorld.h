#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
constexpr float Mm9DatToOpenYammScale = 2.56f;
constexpr uint32_t Mm9DatSurfaceFlagSolid = 0x00000001u;
constexpr uint32_t Mm9DatSurfaceFlagNonexistent = 0x00000002u;
constexpr uint32_t Mm9DatSurfaceFlagInvisible = 0x00000004u;
constexpr uint32_t Mm9DatSurfaceFlagTransparent = 0x00000008u;
constexpr uint32_t Mm9DatSurfaceFlagSky = 0x00000010u;
constexpr uint32_t Mm9DatSurfaceFlagPortal = 0x00002000u;
constexpr uint32_t Mm9DatSurfaceFlagPhysicsBlocker = 0x00020000u;
constexpr uint32_t Mm9DatSurfaceFlagVisibilityBlocker = 0x00200000u;
constexpr uint32_t Mm9DatSurfaceFlagNotAStep = 0x00400000u;
constexpr uint32_t Mm9DatRenderFilterVisual = 0x00000001u;
constexpr uint32_t Mm9DatRenderFilterInvisible = 0x00000002u;
constexpr uint32_t Mm9DatRenderFilterSky = 0x00000004u;
constexpr uint32_t Mm9DatRenderFilterWater = 0x00000008u;
constexpr uint32_t Mm9DatRenderFilterHelper = 0x00000010u;
constexpr uint32_t Mm9DatRenderFilterPhysics = 0x00000020u;
constexpr uint32_t Mm9DatRenderFilterVisibility = 0x00000040u;
constexpr uint32_t Mm9DatRenderFilterTrigger = 0x00000080u;
constexpr uint32_t Mm9DatRenderFilterTerrain = 0x00000100u;
constexpr uint32_t Mm9DatRenderFilterMovable = 0x00000200u;
constexpr uint32_t Mm9DatRenderFilterVisibleWater = 0x00000400u;
constexpr uint32_t Mm9DatRenderFilterWaterVolume = 0x00000800u;
constexpr uint32_t Mm9DatRenderFilterRail = 0x00001000u;

struct Mm9DatVec3
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct Mm9DatPlane
{
    Mm9DatVec3 normalLt;
    float distance = 0.0f;
};

struct Mm9DatSurface
{
    Mm9DatVec3 uvOriginLt;
    Mm9DatVec3 uvULt;
    Mm9DatVec3 uvVLt;
    uint16_t textureIndex = 0;
    uint32_t unknown = 0;
    uint32_t flags = 0;
    uint32_t unknown2 = 0;
    uint16_t textureFlags = 0;
    std::string effectName;
    std::string effectParam;
};

struct Mm9DatPolyVertex
{
    uint16_t pointIndex = 0;
    std::array<uint8_t, 3> rawDummy = {};
};

struct Mm9DatPoly
{
    Mm9DatVec3 centerLt;
    uint16_t lightmapWidth = 0;
    uint16_t lightmapHeight = 0;
    uint16_t unknownFlag = 0;
    std::vector<uint16_t> unknownList;
    uint16_t surfaceIndex = 0;
    uint16_t planeIndex = 0;
    std::vector<Mm9DatPolyVertex> vertices;
};

struct Mm9DatNode
{
    uint32_t polyIndex = 0;
    uint16_t leafIndex = 0;
    uint32_t frontIndex = 0;
    uint32_t backIndex = 0;
};

struct Mm9DatLeafPortalData
{
    uint16_t portalId = 0;
    std::vector<uint8_t> contents;
};

struct Mm9DatLeaf
{
    uint16_t count = 0;
    std::optional<uint16_t> index;
    std::vector<Mm9DatLeafPortalData> portalData;
    std::vector<uint32_t> polygonEntries;
    uint32_t unknown = 0;
};

struct Mm9DatUserPortal
{
    std::string name;
    uint32_t unknownInt1 = 0;
    uint16_t unknownShort = 0;
    Mm9DatVec3 centerLt;
    Mm9DatVec3 dimsLt;
};

struct Mm9DatPBlockTableSummary
{
    uint32_t dimA = 0;
    uint32_t dimB = 0;
    uint32_t dimC = 0;
    Mm9DatVec3 boundsMinLt;
    Mm9DatVec3 boundsMaxLt;
    uint64_t recordCount = 0;
};

struct Mm9DatWorldModel
{
    std::string name;
    uint32_t worldInfoFlags = 0;
    uint32_t unknownValue = 0;
    uint32_t unknownValue2 = 0;
    uint32_t unknownValue3 = 0;
    Mm9DatVec3 boundsMinLt;
    Mm9DatVec3 boundsMaxLt;
    Mm9DatVec3 worldTranslationLt;
    uint32_t vertCount = 0;
    uint32_t totalVisListSize = 0;
    uint32_t leafListCount = 0;
    uint32_t rootNodeIndex = 0;
    uint32_t sectionCount = 0;
    std::vector<std::string> textures;
    std::vector<Mm9DatVec3> pointsLt;
    std::vector<Mm9DatVec3> pointNormalsLt;
    std::vector<Mm9DatPlane> planes;
    std::vector<Mm9DatSurface> surfaces;
    std::vector<Mm9DatPoly> polies;
    std::vector<Mm9DatLeaf> leaves;
    std::vector<Mm9DatNode> nodes;
    std::vector<Mm9DatUserPortal> userPortals;
    Mm9DatPBlockTableSummary pblockTable;
};

struct Mm9DatWorldInfo
{
    std::string propertyString;
    float lightMapGridSize = 0.0f;
    Mm9DatVec3 extentsMinLt;
    Mm9DatVec3 extentsMaxLt;
};

struct Mm9DatWorld
{
    uint32_t version = 0;
    uint32_t objectDataPos = 0;
    uint32_t renderDataPos = 0;
    uint32_t worldModelPos = 0;
    Mm9DatWorldInfo worldInfo;
    std::vector<Mm9DatWorldModel> worldModels;
};

struct Mm9DatRenderVertex
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float uPixels = 0.0f;
    float vPixels = 0.0f;
};

struct Mm9DatRenderTriangle
{
    size_t sourceModelIndex = 0;
    size_t sourcePolyIndex = 0;
    size_t sourceSurfaceIndex = 0;
    size_t sourceTextureIndex = 0;
    std::string sourceModelName;
    std::string sourceTexture;
    uint32_t surfaceFlags = 0;
    uint16_t textureFlags = 0;
    bool sourcePlaneOrientationFlipped = false;
    std::array<Mm9DatRenderVertex, 3> vertices;
};

struct Mm9DatRenderMesh
{
    std::vector<Mm9DatRenderTriangle> triangles;
    size_t sourcePolyCount = 0;
    size_t skippedPolyCount = 0;
    size_t triangulatedPolyCount = 0;
    size_t skippedDegenerateTriangleCount = 0;
    size_t sourcePlaneOrientationFlipCount = 0;
};

struct Mm9DatPickRay
{
    Mm9DatVec3 origin;
    Mm9DatVec3 direction;
};

struct Mm9DatRenderMeshPickHit
{
    size_t triangleIndex = 0;
    size_t sourceModelIndex = 0;
    size_t sourcePolyIndex = 0;
    size_t sourceSurfaceIndex = 0;
    size_t sourceTextureIndex = 0;
    std::string sourceModelName;
    std::string sourceTexture;
    float distance = 0.0f;
    float barycentricU = 0.0f;
    float barycentricV = 0.0f;
    Mm9DatVec3 position;
};

struct Mm9DatMaterialPreview
{
    size_t materialIndex = 0;
    std::string alias;
    std::string sourceTexture;
    std::string resolvedSourcePath;
    std::string resolvedPreviewPath;
    bool sourceDtxResolved = false;
    bool previewCacheAvailable = false;
    bool placeholderMissingSource = false;
};

struct Mm9DatRenderMaterialAssignment
{
    size_t triangleIndex = 0;
    size_t sourceModelIndex = 0;
    size_t sourcePolyIndex = 0;
    size_t sourceSurfaceIndex = 0;
    size_t sourceTextureIndex = 0;
    std::string sourceTexture;
    size_t materialCandidateCount = 0;
    size_t materialIndex = 0;
    std::string alias;
    std::string resolvedSourcePath;
    std::string resolvedPreviewPath;
    bool assigned = false;
    bool ambiguous = false;
    bool sourceDtxResolved = false;
    bool previewCacheAvailable = false;
    bool placeholderMissingSource = false;
};

struct Mm9DatRenderBounds
{
    Mm9DatVec3 min;
    Mm9DatVec3 max;
    Mm9DatVec3 center;
    float radius = 0.0f;
    bool valid = false;
};

struct Mm9DatMechanismPreviewMotion
{
    size_t sourceModelIndex = 0;
    float progress = 1.0f;
    bool hasLinearMotion = false;
    Mm9DatVec3 moveDirLt;
    float moveDistLt = 0.0f;
    bool hasRotationMotion = false;
    Mm9DatVec3 rotationPointLt;
    Mm9DatVec3 rotationAnglesDeg;
};

struct Mm9DatMechanismPreviewResult
{
    Mm9DatRenderMesh previewMesh;
    Mm9DatRenderBounds originalTargetBounds;
    Mm9DatRenderBounds previewTargetBounds;
    size_t transformedTriangles = 0;
    bool targetFound = false;
    bool boundsChanged = false;
};

struct Mm9DatCameraFrame
{
    Mm9DatVec3 target;
    Mm9DatVec3 position;
    float nearPlane = 1.0f;
    float farPlane = 1.0f;
    float radius = 0.0f;
    bool valid = false;
};

struct Mm9DatModelRenderRole
{
    size_t sourceModelIndex = 0;
    bool visible = false;
    bool terrain = false;
    bool physicsBsp = false;
    bool visBsp = false;
    bool sky = false;
    bool water = false;
    bool triggerOrVolume = false;
    bool movable = false;
};

struct Mm9DatRenderFilterEntry
{
    size_t triangleIndex = 0;
    size_t sourceModelIndex = 0;
    size_t sourcePolyIndex = 0;
    size_t sourceSurfaceIndex = 0;
    uint32_t flags = 0;
};

struct Mm9DatRenderFilterSummary
{
    size_t totalTriangles = 0;
    size_t visualTriangles = 0;
    size_t invisibleTriangles = 0;
    size_t skyTriangles = 0;
    size_t waterTriangles = 0;
    size_t visibleWaterTriangles = 0;
    size_t waterVolumeTriangles = 0;
    size_t railTriangles = 0;
    size_t helperTriangles = 0;
    size_t physicsTriangles = 0;
    size_t visibilityTriangles = 0;
    size_t triggerTriangles = 0;
    size_t terrainTriangles = 0;
    size_t movableTriangles = 0;
    size_t unclassifiedTriangles = 0;
    size_t portalOverlays = 0;
};

struct Mm9DatRenderFilterResult
{
    std::vector<Mm9DatRenderFilterEntry> entries;
    Mm9DatRenderFilterSummary summary;
};

std::optional<Mm9DatWorld> loadMm9DatWorld(
    const std::filesystem::path &path,
    std::string &errorMessage);

std::optional<Mm9DatWorld> parseMm9DatWorld(
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage);

Mm9DatRenderMesh buildMm9DatRenderMesh(const Mm9DatWorld &world, float scale = Mm9DatToOpenYammScale);

std::optional<Mm9DatRenderMeshPickHit> pickMm9DatRenderMesh(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatPickRay &ray,
    bool includeBackfaces = true);

std::vector<Mm9DatRenderMaterialAssignment> assignMm9DatRenderMeshMaterials(
    const Mm9DatRenderMesh &mesh,
    const std::vector<Mm9DatMaterialPreview> &materials);

Mm9DatRenderBounds computeMm9DatRenderBounds(const Mm9DatRenderMesh &mesh);

Mm9DatRenderBounds computeMm9DatRenderBoundsForSourceModel(
    const Mm9DatRenderMesh &mesh,
    size_t sourceModelIndex);

Mm9DatMechanismPreviewResult buildMm9DatMechanismPreviewMesh(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismPreviewMotion &motion,
    float scale = Mm9DatToOpenYammScale);

Mm9DatCameraFrame frameMm9DatRenderMeshCamera(
    const Mm9DatRenderMesh &mesh,
    float verticalFovDegrees = 60.0f,
    float paddingScale = 1.35f);

Mm9DatCameraFrame frameMm9DatRenderBoundsCamera(
    const Mm9DatRenderBounds &bounds,
    float verticalFovDegrees = 60.0f,
    float paddingScale = 1.35f);

Mm9DatRenderFilterResult classifyMm9DatRenderMeshFilters(
    const Mm9DatRenderMesh &mesh,
    const std::vector<Mm9DatModelRenderRole> &modelRoles,
    size_t portalOverlayCount = 0);
}
