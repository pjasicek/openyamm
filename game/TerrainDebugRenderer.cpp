#include "game/TerrainDebugRenderer.h"

#include "game/OutdoorGeometryUtils.h"
#include "game/OutdoorPartyRuntime.h"
#include "game/SpawnPreview.h"

#include <bx/math.h>

#include <bgfx/bgfx.h>
#include <SDL3/SDL.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t MainViewId = 0;
constexpr uint16_t HudViewId = 1;
constexpr float Pi = 3.14159265358979323846f;
constexpr float CameraVerticalFovDegrees = 60.0f;
constexpr float CameraVerticalFovRadians = CameraVerticalFovDegrees * (Pi / 180.0f);
constexpr int DebugTextCellWidthPixels = 8;
constexpr int DebugTextCellHeightPixels = 16;
constexpr float BillboardNearDepth = 0.1f;
constexpr float InspectRayEpsilon = 0.0001f;
constexpr float OutdoorWalkableNormalZ = 0.70710678f;
constexpr float OutdoorMaxStepHeight = 128.0f;
constexpr uint8_t OutdoorPolygonFloor = 0x3;
constexpr uint8_t OutdoorPolygonInBetweenFloorAndWall = 0x4;

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

using OutdoorFaceGeometry = OutdoorFaceGeometryData;

const char *outdoorSupportKindName(OutdoorSupportKind supportKind)
{
    switch (supportKind)
    {
        case OutdoorSupportKind::Terrain:
            return "terrain";
        case OutdoorSupportKind::BModelFace:
            return "bmodel";
        case OutdoorSupportKind::None:
        default:
            return "none";
    }
}

std::string buildGameplayHudCharacterLine(const Character &character, bool isLeader)
{
    std::ostringstream stream;
    stream << (isLeader ? "*" : " ")
           << character.name
           << " Lv"
           << character.level
           << " "
           << character.role;
    return stream.str();
}

bool isOutdoorFaceSlopeTooSteep(const OutdoorFaceGeometry &geometry)
{
    if (!geometry.hasPlane)
    {
        return false;
    }

    const float normalZ = std::fabs(geometry.normal.z);

    if (normalZ <= InspectRayEpsilon || normalZ >= OutdoorWalkableNormalZ)
    {
        return false;
    }

    return (geometry.maxZ - geometry.minZ) >= OutdoorMaxStepHeight;
}

bx::Vec3 vecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

bx::Vec3 vecAdd(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

bx::Vec3 vecScale(const bx::Vec3 &vector, float scalar)
{
    return {vector.x * scalar, vector.y * scalar, vector.z * scalar};
}

bx::Vec3 vecCross(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
}

float vecDot(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

float vecLength(const bx::Vec3 &vector)
{
    return std::sqrt(vecDot(vector, vector));
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    const uint8_t alpha = 255;

    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

bx::Vec3 vecNormalize(const bx::Vec3 &vector)
{
    const float vectorLength = vecLength(vector);

    if (vectorLength <= InspectRayEpsilon)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {vector.x / vectorLength, vector.y / vectorLength, vector.z / vectorLength};
}

std::optional<std::vector<uint8_t>> loadBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    int &width,
    int &height,
    bool applyTransparencyKey
)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/icons");
    std::string targetFileName = textureName;
    std::transform(
        targetFileName.begin(),
        targetFileName.end(),
        targetFileName.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        }
    );
    targetFileName += ".bmp";
    std::string resolvedPath;

    for (const std::string &entry : entries)
    {
        std::string lowerEntry = entry;
        std::transform(
            lowerEntry.begin(),
            lowerEntry.end(),
            lowerEntry.begin(),
            [](unsigned char character)
            {
                return static_cast<char>(std::tolower(character));
            }
        );

        if (lowerEntry == targetFileName)
        {
            resolvedPath = "Data/icons/" + entry;
            break;
        }
    }

    if (resolvedPath.empty())
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = assetFileSystem.readBinaryFile(resolvedPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return std::nullopt;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return std::nullopt;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height) * 4;
    std::vector<uint8_t> pixels(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);

    for (size_t pixelOffset = 0; pixelOffset < pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = pixels[pixelOffset + 0];
        const uint8_t green = pixels[pixelOffset + 1];
        const uint8_t red = pixels[pixelOffset + 2];

        const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
        const bool isTealKey = applyTransparencyKey && red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isTealKey)
        {
            pixels[pixelOffset + 3] = 0;
        }
    }

    SDL_DestroySurface(pConvertedSurface);
    return pixels;
}

float pointSegmentDistanceSquared2d(
    float pointX,
    float pointY,
    float segmentStartX,
    float segmentStartY,
    float segmentEndX,
    float segmentEndY
);

float cross2d(float ax, float ay, float bx, float by)
{
    return ax * by - ay * bx;
}

bool rangesOverlap(float a0, float a1, float b0, float b1)
{
    const float minA = std::min(a0, a1);
    const float maxA = std::max(a0, a1);
    const float minB = std::min(b0, b1);
    const float maxB = std::max(b0, b1);
    return maxA + InspectRayEpsilon >= minB && maxB + InspectRayEpsilon >= minA;
}

bool segmentsIntersect2d(
    float ax,
    float ay,
    float bx,
    float by,
    float cx,
    float cy,
    float dx,
    float dy
)
{
    if (!rangesOverlap(ax, bx, cx, dx) || !rangesOverlap(ay, by, cy, dy))
    {
        return false;
    }

    const float abx = bx - ax;
    const float aby = by - ay;
    const float acx = cx - ax;
    const float acy = cy - ay;
    const float adx = dx - ax;
    const float ady = dy - ay;
    const float cdx = dx - cx;
    const float cdy = dy - cy;
    const float cax = ax - cx;
    const float cay = ay - cy;
    const float cbx = bx - cx;
    const float cby = by - cy;
    const float cross1 = cross2d(abx, aby, acx, acy);
    const float cross2 = cross2d(abx, aby, adx, ady);
    const float cross3 = cross2d(cdx, cdy, cax, cay);
    const float cross4 = cross2d(cdx, cdy, cbx, cby);

    if (((cross1 > InspectRayEpsilon && cross2 < -InspectRayEpsilon)
            || (cross1 < -InspectRayEpsilon && cross2 > InspectRayEpsilon))
        && ((cross3 > InspectRayEpsilon && cross4 < -InspectRayEpsilon)
            || (cross3 < -InspectRayEpsilon && cross4 > InspectRayEpsilon)))
    {
        return true;
    }

    return std::fabs(cross1) <= InspectRayEpsilon
        || std::fabs(cross2) <= InspectRayEpsilon
        || std::fabs(cross3) <= InspectRayEpsilon
        || std::fabs(cross4) <= InspectRayEpsilon;
}

float pointSegmentDistanceSquared2d(
    float pointX,
    float pointY,
    float segmentStartX,
    float segmentStartY,
    float segmentEndX,
    float segmentEndY
)
{
    const float segmentX = segmentEndX - segmentStartX;
    const float segmentY = segmentEndY - segmentStartY;
    const float segmentLengthSquared = segmentX * segmentX + segmentY * segmentY;

    if (segmentLengthSquared <= InspectRayEpsilon)
    {
        const float dx = pointX - segmentStartX;
        const float dy = pointY - segmentStartY;
        return dx * dx + dy * dy;
    }

    const float pointProjection =
        ((pointX - segmentStartX) * segmentX + (pointY - segmentStartY) * segmentY) / segmentLengthSquared;
    const float clampedProjection = std::clamp(pointProjection, 0.0f, 1.0f);
    const float closestX = segmentStartX + segmentX * clampedProjection;
    const float closestY = segmentStartY + segmentY * clampedProjection;
    const float dx = pointX - closestX;
    const float dy = pointY - closestY;
    return dx * dx + dy * dy;
}

std::string summarizeLinkedEvent(
    uint16_t eventId,
    const std::optional<HouseTable> &houseTable,
    const std::optional<StrTable> &localStrTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram
)
{
    if (eventId == 0)
    {
        return "-";
    }

    const HouseTable emptyHouseTable = {};
    const HouseTable &resolvedHouseTable = houseTable ? *houseTable : emptyHouseTable;
    const StrTable emptyStrTable = {};
    const StrTable &strTable = localStrTable ? *localStrTable : emptyStrTable;

    if (localEvtProgram)
    {
        const std::optional<std::string> summary = localEvtProgram->summarizeEvent(eventId, strTable, resolvedHouseTable);

        if (summary)
        {
            return "L:" + *summary;
        }
    }

    if (globalEvtProgram)
    {
        const std::optional<std::string> summary = globalEvtProgram->summarizeEvent(eventId, emptyStrTable, resolvedHouseTable);

        if (summary)
        {
            return "G:" + *summary;
        }
    }

    return std::to_string(eventId) + ":unresolved";
}

size_t countChestItemSlots(const MapDeltaChest &chest)
{
    size_t occupiedSlots = 0;

    for (int16_t itemIndex : chest.inventoryMatrix)
    {
        if (itemIndex > 0)
        {
            ++occupiedSlots;
        }
    }

    return occupiedSlots;
}

std::string summarizeLinkedChests(
    uint16_t eventId,
    const std::optional<MapDeltaData> &mapDeltaData,
    const std::optional<ChestTable> &chestTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram
)
{
    if (eventId == 0 || !mapDeltaData || !chestTable)
    {
        return {};
    }

    std::vector<uint32_t> chestIds;

    if (localEvtProgram && localEvtProgram->hasEvent(eventId))
    {
        chestIds = localEvtProgram->getOpenedChestIds(eventId);
    }
    else if (globalEvtProgram && globalEvtProgram->hasEvent(eventId))
    {
        chestIds = globalEvtProgram->getOpenedChestIds(eventId);
    }

    if (chestIds.empty())
    {
        return {};
    }

    std::string summary = "Chest:";
    const size_t chestCount = std::min<size_t>(chestIds.size(), 2);

    for (size_t chestIndex = 0; chestIndex < chestCount; ++chestIndex)
    {
        const uint32_t chestId = chestIds[chestIndex];
        summary += " #" + std::to_string(chestId);

        if (chestId >= mapDeltaData->chests.size())
        {
            summary += ":out";
            continue;
        }

        const MapDeltaChest &chest = mapDeltaData->chests[chestId];
        const ChestEntry *pEntry = chestTable->get(chest.chestTypeId);
        summary += ":" + std::to_string(chest.chestTypeId);

        if (pEntry != nullptr && !pEntry->name.empty())
        {
            summary += ":" + pEntry->name;
        }

        std::ostringstream flagsStream;
        flagsStream << std::hex << chest.flags;
        summary += " f=0x" + flagsStream.str();
        summary += " s=" + std::to_string(countChestItemSlots(chest));
    }

    if (chestIds.size() > chestCount)
    {
        summary += " ...";
    }

    return summary;
}

bool intersectRayTriangle(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const bx::Vec3 &vertex0,
    const bx::Vec3 &vertex1,
    const bx::Vec3 &vertex2,
    float &distance
)
{
    const bx::Vec3 edge1 = vecSubtract(vertex1, vertex0);
    const bx::Vec3 edge2 = vecSubtract(vertex2, vertex0);
    const bx::Vec3 pVector = vecCross(rayDirection, edge2);
    const float determinant = vecDot(edge1, pVector);

    if (std::fabs(determinant) <= InspectRayEpsilon)
    {
        return false;
    }

    const float inverseDeterminant = 1.0f / determinant;
    const bx::Vec3 tVector = vecSubtract(rayOrigin, vertex0);
    const float barycentricU = vecDot(tVector, pVector) * inverseDeterminant;

    if (barycentricU < 0.0f || barycentricU > 1.0f)
    {
        return false;
    }

    const bx::Vec3 qVector = vecCross(tVector, edge1);
    const float barycentricV = vecDot(rayDirection, qVector) * inverseDeterminant;

    if (barycentricV < 0.0f || barycentricU + barycentricV > 1.0f)
    {
        return false;
    }

    distance = vecDot(edge2, qVector) * inverseDeterminant;
    return distance > InspectRayEpsilon;
}

bool intersectRayAabb(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const bx::Vec3 &minBounds,
    const bx::Vec3 &maxBounds,
    float &distance
)
{
    float tMin = 0.0f;
    float tMax = std::numeric_limits<float>::max();

    const float rayOriginValues[3] = {rayOrigin.x, rayOrigin.y, rayOrigin.z};
    const float rayDirectionValues[3] = {rayDirection.x, rayDirection.y, rayDirection.z};
    const float minValues[3] = {minBounds.x, minBounds.y, minBounds.z};
    const float maxValues[3] = {maxBounds.x, maxBounds.y, maxBounds.z};

    for (int axis = 0; axis < 3; ++axis)
    {
        if (std::fabs(rayDirectionValues[axis]) <= InspectRayEpsilon)
        {
            if (rayOriginValues[axis] < minValues[axis] || rayOriginValues[axis] > maxValues[axis])
            {
                return false;
            }

            continue;
        }

        const float inverseDirection = 1.0f / rayDirectionValues[axis];
        float t1 = (minValues[axis] - rayOriginValues[axis]) * inverseDirection;
        float t2 = (maxValues[axis] - rayOriginValues[axis]) * inverseDirection;

        if (t1 > t2)
        {
            std::swap(t1, t2);
        }

        tMin = std::max(tMin, t1);
        tMax = std::min(tMax, t2);

        if (tMin > tMax)
        {
            return false;
        }
    }

    distance = tMin;
    return true;
}

std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName)
{
    std::filesystem::path shaderRoot = OPENYAMM_BGFX_SHADER_DIR;

    if (rendererType == bgfx::RendererType::OpenGL)
    {
        return shaderRoot / "glsl" / (std::string(pShaderName) + ".bin");
    }

    if (rendererType == bgfx::RendererType::Noop)
    {
        return {};
    }

    return {};
}

std::vector<uint8_t> readBinaryFile(const std::filesystem::path &path)
{
    std::ifstream inputStream(path, std::ios::binary);

    if (!inputStream)
    {
        return {};
    }

    return std::vector<uint8_t>(std::istreambuf_iterator<char>(inputStream), std::istreambuf_iterator<char>());
}

std::string toLowerCopy(const std::string &value)
{
    std::string lowered = value;

    for (char &character : lowered)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return lowered;
}
}

bgfx::VertexLayout TerrainDebugRenderer::TerrainVertex::ms_layout;
bgfx::VertexLayout TerrainDebugRenderer::TexturedTerrainVertex::ms_layout;

TerrainDebugRenderer::TerrainDebugRenderer()
    : m_isInitialized(false)
    , m_isRenderable(false)
    , m_outdoorMapData(std::nullopt)
    , m_vertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_indexBufferHandle(BGFX_INVALID_HANDLE)
    , m_texturedTerrainVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_filledTerrainVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_bmodelVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_bmodelCollisionVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_entityMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_spawnMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_programHandle(BGFX_INVALID_HANDLE)
    , m_texturedTerrainProgramHandle(BGFX_INVALID_HANDLE)
    , m_terrainTextureAtlasHandle(BGFX_INVALID_HANDLE)
    , m_terrainTextureSamplerHandle(BGFX_INVALID_HANDLE)
    , m_elapsedTime(0.0f)
    , m_framesPerSecond(0.0f)
    , m_bmodelLineVertexCount(0)
    , m_bmodelCollisionVertexCount(0)
    , m_bmodelFaceCount(0)
    , m_entityMarkerVertexCount(0)
    , m_spawnMarkerVertexCount(0)
    , m_cameraTargetX(-80000.0f)
    , m_cameraTargetY(0.0f)
    , m_cameraTargetZ(28000.0f)
    , m_cameraYawRadians(0.0f)
    , m_cameraPitchRadians(0.30f)
    , m_cameraEyeHeight(176.0f)
    , m_cameraDistance(0.0f)
    , m_cameraOrthoScale(1.2f)
    , m_lastTickCount(0)
    , m_showFilledTerrain(true)
    , m_showTerrainWireframe(false)
    , m_showBModels(true)
    , m_showBModelWireframe(true)
    , m_showBModelCollisionFaces(false)
    , m_showDecorationBillboards(true)
    , m_showActors(true)
    , m_showSpriteObjects(true)
    , m_showEntities(true)
    , m_showSpawns(true)
    , m_inspectMode(false)
    , m_isRotatingCamera(false)
    , m_lastMouseX(0.0f)
    , m_lastMouseY(0.0f)
    , m_toggleFilledLatch(false)
    , m_toggleWireframeLatch(false)
    , m_toggleBModelsLatch(false)
    , m_toggleBModelWireframeLatch(false)
    , m_toggleBModelCollisionFacesLatch(false)
    , m_toggleDecorationBillboardsLatch(false)
    , m_toggleActorsLatch(false)
    , m_toggleSpriteObjectsLatch(false)
    , m_toggleEntitiesLatch(false)
    , m_toggleSpawnsLatch(false)
    , m_toggleInspectLatch(false)
    , m_activateInspectLatch(false)
    , m_toggleRunningLatch(false)
    , m_toggleFlyingLatch(false)
    , m_toggleWaterWalkLatch(false)
    , m_toggleFeatherFallLatch(false)
{
}

TerrainDebugRenderer::~TerrainDebugRenderer()
{
    shutdown();
}

bool TerrainDebugRenderer::initialize(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<std::vector<uint32_t>> &outdoorTileColors,
    const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas,
    const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet,
    const std::optional<DecorationBillboardSet> &outdoorDecorationBillboardSet,
    const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet,
    const std::optional<SpriteObjectBillboardSet> &outdoorSpriteObjectBillboardSet,
    const std::optional<MapDeltaData> &outdoorMapDeltaData,
    const ChestTable &chestTable,
    const HouseTable &houseTable,
    const std::optional<StrTable> &localStrTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    const std::optional<EventIrProgram> &localEventIrProgram,
    const std::optional<EventIrProgram> &globalEventIrProgram,
    OutdoorPartyRuntime *pOutdoorPartyRuntime
)
{
    shutdown();

    m_isInitialized = true;
    m_map = map;
    m_monsterTable = monsterTable;
    m_outdoorMapData = outdoorMapData;
    m_outdoorDecorationBillboardSet = outdoorDecorationBillboardSet;
    m_outdoorActorPreviewBillboardSet = outdoorActorPreviewBillboardSet;
    m_outdoorSpriteObjectBillboardSet = outdoorSpriteObjectBillboardSet;
    m_outdoorMapDeltaData = outdoorMapDeltaData;
    m_chestTable = chestTable;
    m_houseTable = houseTable;
    m_localStrTable = localStrTable;
    m_localEvtProgram = localEvtProgram;
    m_globalEvtProgram = globalEvtProgram;
    m_eventRuntimeState = eventRuntimeState;
    m_localEventIrProgram = localEventIrProgram;
    m_globalEventIrProgram = globalEventIrProgram;
    m_pOutdoorPartyRuntime = pOutdoorPartyRuntime;

    const int centerGridX = OutdoorMapData::TerrainWidth / 2;
    const int centerGridY = OutdoorMapData::TerrainHeight / 2;
    const size_t centerSampleIndex =
        static_cast<size_t>(centerGridY * OutdoorMapData::TerrainWidth + centerGridX);
    const float centerHeightWorld =
        static_cast<float>(outdoorMapData.heightMap[centerSampleIndex] * OutdoorMapData::TerrainHeightScale);
    m_cameraTargetX = 0.0f;
    m_cameraTargetY = 0.0f;
    if (m_pOutdoorPartyRuntime)
    {
        m_pOutdoorPartyRuntime->initialize(m_cameraTargetX, m_cameraTargetY, centerHeightWorld);
        m_cameraTargetZ = m_pOutdoorPartyRuntime->movementState().footZ + m_cameraEyeHeight;
    }
    else
    {
        m_cameraTargetZ = centerHeightWorld + m_cameraEyeHeight;
    }
    m_cameraYawRadians = -Pi * 0.5f;
    m_cameraPitchRadians = -0.15f;
    m_cameraDistance = 0.0f;
    m_cameraOrthoScale = 1.2f;

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return true;
    }

    TerrainVertex::init();
    TexturedTerrainVertex::init();

    const std::vector<TerrainVertex> vertices = buildVertices(outdoorMapData);
    const std::vector<uint16_t> indices = buildIndices();
    std::vector<TexturedTerrainVertex> texturedTerrainVertices;
    const std::vector<TerrainVertex> filledTerrainVertices = buildFilledTerrainVertices(outdoorMapData, outdoorTileColors);
    const std::vector<TerrainVertex> bmodelVertices = buildBModelWireframeVertices(outdoorMapData);
    const std::vector<TerrainVertex> bmodelCollisionVertices = buildBModelCollisionFaceVertices(outdoorMapData);
    const std::vector<TerrainVertex> entityMarkerVertices = buildEntityMarkerVertices(outdoorMapData);
    const std::vector<TerrainVertex> spawnMarkerVertices = buildSpawnMarkerVertices(outdoorMapData);

    if (outdoorTerrainTextureAtlas)
    {
        texturedTerrainVertices = buildTexturedTerrainVertices(outdoorMapData, *outdoorTerrainTextureAtlas);
    }

    if (vertices.empty() || indices.empty())
    {
        std::cerr << "TerrainDebugRenderer received empty terrain mesh.\n";
        return false;
    }

    m_vertexBufferHandle = bgfx::createVertexBuffer(
        bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(TerrainVertex))),
        TerrainVertex::ms_layout
    );

    m_indexBufferHandle = bgfx::createIndexBuffer(
        bgfx::copy(indices.data(), static_cast<uint32_t>(indices.size() * sizeof(uint16_t)))
    );

    if (!texturedTerrainVertices.empty())
    {
        m_texturedTerrainVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                texturedTerrainVertices.data(),
                static_cast<uint32_t>(texturedTerrainVertices.size() * sizeof(TexturedTerrainVertex))
            ),
            TexturedTerrainVertex::ms_layout
        );
    }

    if (!filledTerrainVertices.empty())
    {
        m_filledTerrainVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                filledTerrainVertices.data(),
                static_cast<uint32_t>(filledTerrainVertices.size() * sizeof(TerrainVertex))
            ),
            TerrainVertex::ms_layout
        );
    }

    if (!bmodelVertices.empty())
    {
        m_bmodelVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(bmodelVertices.data(), static_cast<uint32_t>(bmodelVertices.size() * sizeof(TerrainVertex))),
            TerrainVertex::ms_layout
        );
        m_bmodelLineVertexCount = static_cast<uint32_t>(bmodelVertices.size());
    }

    if (!bmodelCollisionVertices.empty())
    {
        m_bmodelCollisionVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                bmodelCollisionVertices.data(),
                static_cast<uint32_t>(bmodelCollisionVertices.size() * sizeof(TerrainVertex))
            ),
            TerrainVertex::ms_layout
        );
        m_bmodelCollisionVertexCount = static_cast<uint32_t>(bmodelCollisionVertices.size());
    }

    if (!entityMarkerVertices.empty())
    {
        m_entityMarkerVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                entityMarkerVertices.data(),
                static_cast<uint32_t>(entityMarkerVertices.size() * sizeof(TerrainVertex))
            ),
            TerrainVertex::ms_layout
        );
        m_entityMarkerVertexCount = static_cast<uint32_t>(entityMarkerVertices.size());
    }

    if (!spawnMarkerVertices.empty())
    {
        m_spawnMarkerVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                spawnMarkerVertices.data(),
                static_cast<uint32_t>(spawnMarkerVertices.size() * sizeof(TerrainVertex))
            ),
            TerrainVertex::ms_layout
        );
        m_spawnMarkerVertexCount = static_cast<uint32_t>(spawnMarkerVertices.size());
    }

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        m_bmodelFaceCount += static_cast<uint32_t>(bmodel.faces.size());
    }

    m_programHandle = loadProgram("vs_cubes", "fs_cubes");
    m_texturedTerrainProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_shadowmaps_texture");

    if (outdoorTerrainTextureAtlas && !outdoorTerrainTextureAtlas->pixels.empty())
    {
        m_terrainTextureAtlasHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(outdoorTerrainTextureAtlas->width),
            static_cast<uint16_t>(outdoorTerrainTextureAtlas->height),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
            bgfx::copy(
                outdoorTerrainTextureAtlas->pixels.data(),
                static_cast<uint32_t>(outdoorTerrainTextureAtlas->pixels.size())
            )
        );
    }

    if (outdoorBModelTextureSet)
    {
        for (const OutdoorBitmapTexture &texture : outdoorBModelTextureSet->textures)
        {
            const std::vector<TexturedTerrainVertex> texturedBModelVertices =
                buildTexturedBModelVertices(outdoorMapData, texture);

            if (texturedBModelVertices.empty())
            {
                continue;
            }

            TexturedBModelBatch batch = {};
            batch.vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    texturedBModelVertices.data(),
                    static_cast<uint32_t>(texturedBModelVertices.size() * sizeof(TexturedTerrainVertex))
                ),
                TexturedTerrainVertex::ms_layout
            );
            batch.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(texture.width),
                static_cast<uint16_t>(texture.height),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
                bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size()))
            );
            batch.vertexCount = static_cast<uint32_t>(texturedBModelVertices.size());

            if (!bgfx::isValid(batch.vertexBufferHandle) || !bgfx::isValid(batch.textureHandle))
            {
                if (bgfx::isValid(batch.vertexBufferHandle))
                {
                    bgfx::destroy(batch.vertexBufferHandle);
                }

                if (bgfx::isValid(batch.textureHandle))
                {
                    bgfx::destroy(batch.textureHandle);
                }

                continue;
            }

            m_texturedBModelBatches.push_back(batch);
        }
    }

    if (outdoorDecorationBillboardSet)
    {
        for (const OutdoorBitmapTexture &texture : outdoorDecorationBillboardSet->textures)
        {
            BillboardTextureHandle billboardTexture = {};
            billboardTexture.textureName = toLowerCopy(texture.textureName);
            billboardTexture.width = texture.width;
            billboardTexture.height = texture.height;
            billboardTexture.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(texture.width),
                static_cast<uint16_t>(texture.height),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
                bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size()))
            );

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                m_billboardTextureHandles.push_back(std::move(billboardTexture));
            }
        }
    }

    if (outdoorActorPreviewBillboardSet)
    {
        for (const OutdoorBitmapTexture &texture : outdoorActorPreviewBillboardSet->textures)
        {
            if (findBillboardTexture(texture.textureName) != nullptr)
            {
                continue;
            }

            BillboardTextureHandle billboardTexture = {};
            billboardTexture.textureName = toLowerCopy(texture.textureName);
            billboardTexture.width = texture.width;
            billboardTexture.height = texture.height;
            billboardTexture.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(texture.width),
                static_cast<uint16_t>(texture.height),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
                bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size()))
            );

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                m_billboardTextureHandles.push_back(std::move(billboardTexture));
            }
        }
    }

    if (outdoorSpriteObjectBillboardSet)
    {
        for (const OutdoorBitmapTexture &texture : outdoorSpriteObjectBillboardSet->textures)
        {
            if (findBillboardTexture(texture.textureName) != nullptr)
            {
                continue;
            }

            BillboardTextureHandle billboardTexture = {};
            billboardTexture.textureName = toLowerCopy(texture.textureName);
            billboardTexture.width = texture.width;
            billboardTexture.height = texture.height;
            billboardTexture.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(texture.width),
                static_cast<uint16_t>(texture.height),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
                bgfx::copy(texture.pixels.data(), static_cast<uint32_t>(texture.pixels.size()))
            );

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                m_billboardTextureHandles.push_back(std::move(billboardTexture));
            }
        }
    }

    const std::vector<std::string> hudTextureNames = {
        "Basebar",
        "FACEMASK",
        "selring",
        "manaFRM",
        "ManaG",
        "manaB",
        "PC01-01",
        "PC05-01",
        "PC08-01",
        "PC16-01"
    };

    for (const std::string &textureName : hudTextureNames)
    {
        loadHudTexture(assetFileSystem, textureName);
    }

    m_terrainTextureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);

    if (!bgfx::isValid(m_vertexBufferHandle) || !bgfx::isValid(m_indexBufferHandle) || !bgfx::isValid(m_programHandle))
    {
        std::cerr << "TerrainDebugRenderer failed to create bgfx resources.\n";
        shutdown();
        return false;
    }

    m_isRenderable = true;
    m_lastTickCount = SDL_GetTicksNS();
    return true;
}

void TerrainDebugRenderer::render(int width, int height, float mouseWheelDelta)
{
    if (!m_isInitialized)
    {
        return;
    }

    const uint16_t viewWidth = static_cast<uint16_t>(std::max(width, 1));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(height, 1));

    bgfx::setViewRect(MainViewId, 0, 0, viewWidth, viewHeight);

    if (!m_isRenderable)
    {
        bgfx::touch(MainViewId);
        bgfx::dbgTextClear();
        bgfx::dbgTextPrintf(0, 1, 0x0f, "bgfx noop renderer active");
        return;
    }

    updateCameraFromInput();

    const float wireframeAspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);

    float wireframeViewMatrix[16] = {};
    float wireframeProjectionMatrix[16] = {};

    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    const bx::Vec3 wireframeEye = {
        m_cameraTargetX,
        m_cameraTargetY,
        m_cameraTargetZ
    };
    const bx::Vec3 wireframeAt = {
        m_cameraTargetX + cosYaw * cosPitch,
        m_cameraTargetY - sinYaw * cosPitch,
        m_cameraTargetZ + sinPitch
    };
    const bx::Vec3 wireframeUp = {0.0f, 0.0f, 1.0f};
    bx::mtxLookAt(wireframeViewMatrix, wireframeEye, wireframeAt, wireframeUp);
    bx::mtxProj(
        wireframeProjectionMatrix,
        CameraVerticalFovDegrees,
        wireframeAspectRatio,
        0.1f,
        200000.0f,
        bgfx::getCaps()->homogeneousDepth
    );

    bgfx::setViewTransform(MainViewId, wireframeViewMatrix, wireframeProjectionMatrix);
    bgfx::touch(MainViewId);

    InspectHit inspectHit = {};
    float mouseX = 0.0f;
    float mouseY = 0.0f;

    if (m_inspectMode && m_outdoorMapData)
    {
        SDL_GetMouseState(&mouseX, &mouseY);
        const float normalizedMouseX =
            ((static_cast<float>(mouseX) / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
        const float normalizedMouseY =
            1.0f - ((static_cast<float>(mouseY) / static_cast<float>(viewHeight)) * 2.0f);
        float viewProjectionMatrix[16] = {};
        float inverseViewProjectionMatrix[16] = {};
        bx::mtxMul(viewProjectionMatrix, wireframeViewMatrix, wireframeProjectionMatrix);
        bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);
        const bx::Vec3 rayOrigin = bx::mulH({normalizedMouseX, normalizedMouseY, 0.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayTarget = bx::mulH({normalizedMouseX, normalizedMouseY, 1.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayDirection = vecNormalize(vecSubtract(rayTarget, rayOrigin));
        inspectHit = inspectBModelFace(*m_outdoorMapData, rayOrigin, rayDirection);

        const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);
        const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(nullptr, nullptr);
        const bool isActivationPressed =
            pKeyboardState != nullptr
            && pKeyboardState[SDL_SCANCODE_E]
            && (mouseButtons & SDL_BUTTON_RMASK) == 0;
        const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;

        if ((isActivationPressed || isLeftMousePressed) && !m_activateInspectLatch)
        {
            if (tryActivateInspectEvent(inspectHit))
            {
                inspectHit = inspectBModelFace(*m_outdoorMapData, rayOrigin, rayDirection);
            }

            m_activateInspectLatch = true;
        }
        else if (!isActivationPressed && !isLeftMousePressed)
        {
            m_activateInspectLatch = false;
        }
    }
    else
    {
        m_activateInspectLatch = false;
    }

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);

    bgfx::setTransform(modelMatrix);
    if (m_showFilledTerrain && bgfx::isValid(m_filledTerrainVertexBufferHandle))
    {
        bgfx::setVertexBuffer(0, m_filledTerrainVertexBufferHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LESS
        );
        bgfx::submit(MainViewId, m_programHandle);
    }

    if (m_showFilledTerrain
        && bgfx::isValid(m_texturedTerrainVertexBufferHandle)
        && bgfx::isValid(m_texturedTerrainProgramHandle)
        && bgfx::isValid(m_terrainTextureAtlasHandle)
        && bgfx::isValid(m_terrainTextureSamplerHandle))
    {
        bgfx::setVertexBuffer(0, m_texturedTerrainVertexBufferHandle);
        bgfx::setTexture(0, m_terrainTextureSamplerHandle, m_terrainTextureAtlasHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(MainViewId, m_texturedTerrainProgramHandle);
    }

    if (m_showTerrainWireframe)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, m_vertexBufferHandle);
        bgfx::setIndexBuffer(m_indexBufferHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LESS
            | BGFX_STATE_PT_LINES
        );
        bgfx::submit(MainViewId, m_programHandle);
    }

    if (m_showBModels && bgfx::isValid(m_bmodelVertexBufferHandle) && m_bmodelLineVertexCount > 0)
    {
        if (bgfx::isValid(m_texturedTerrainProgramHandle) && bgfx::isValid(m_terrainTextureSamplerHandle))
        {
            for (const TexturedBModelBatch &batch : m_texturedBModelBatches)
            {
                if (!bgfx::isValid(batch.vertexBufferHandle) || !bgfx::isValid(batch.textureHandle) || batch.vertexCount == 0)
                {
                    continue;
                }

                bgfx::setTransform(modelMatrix);
                bgfx::setVertexBuffer(0, batch.vertexBufferHandle, 0, batch.vertexCount);
                bgfx::setTexture(0, m_terrainTextureSamplerHandle, batch.textureHandle);
                bgfx::setState(
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LEQUAL
                    | BGFX_STATE_BLEND_ALPHA
                );
                bgfx::submit(MainViewId, m_texturedTerrainProgramHandle);
            }
        }

        if (m_showBModelWireframe)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, m_bmodelVertexBufferHandle, 0, m_bmodelLineVertexCount);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_PT_LINES
            );
            bgfx::submit(MainViewId, m_programHandle);
        }
    }

    if (m_showBModelCollisionFaces
        && bgfx::isValid(m_bmodelCollisionVertexBufferHandle)
        && m_bmodelCollisionVertexCount > 0)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, m_bmodelCollisionVertexBufferHandle, 0, m_bmodelCollisionVertexCount);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LESS
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(MainViewId, m_programHandle);
    }

    if (m_showDecorationBillboards)
    {
        renderDecorationBillboards(MainViewId, viewWidth, viewHeight, wireframeViewMatrix, wireframeEye);
    }

    if (m_showEntities && bgfx::isValid(m_entityMarkerVertexBufferHandle) && m_entityMarkerVertexCount > 0)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, m_entityMarkerVertexBufferHandle, 0, m_entityMarkerVertexCount);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_PT_LINES
        );
        bgfx::submit(MainViewId, m_programHandle);
    }

    if (m_showActors)
    {
        renderActorPreviewBillboards(MainViewId, wireframeViewMatrix, wireframeEye);
    }

    if (m_showSpriteObjects)
    {
        renderSpriteObjectBillboards(MainViewId, wireframeViewMatrix, wireframeEye);
    }

    if (m_showSpawns && bgfx::isValid(m_spawnMarkerVertexBufferHandle) && m_spawnMarkerVertexCount > 0)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, m_spawnMarkerVertexBufferHandle, 0, m_spawnMarkerVertexCount);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_PT_LINES
        );
        bgfx::submit(MainViewId, m_programHandle);
    }

    bgfx::dbgTextClear();
    bgfx::dbgTextPrintf(0, 1, 0x0f, "Terrain debug renderer");
    bgfx::dbgTextPrintf(0, 2, 0x0f, "FPS: %.1f", m_framesPerSecond);
    bgfx::dbgTextPrintf(
        0,
        3,
        0x0f,
        "Terrain vertices: %d",
        OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight
    );
    bgfx::dbgTextPrintf(0, 4, 0x0f, "BModels: %u", m_bmodelFaceCount);
    bgfx::dbgTextPrintf(
        0,
        5,
        0x0f,
        "Modes: 1 filled=%s  2 wire=%s  3 bmodels=%s  4 bmwire=%s  5 coll=%s  6 sprites=%s  7 actors=%s  8 objs=%s  9 ents=%s  0 spawns=%s  inspect=%s  textured=%s/%s",
        m_showFilledTerrain ? "on" : "off",
        m_showTerrainWireframe ? "on" : "off",
        m_showBModels ? "on" : "off",
        m_showBModelWireframe ? "on" : "off",
        m_showBModelCollisionFaces ? "on" : "off",
        m_showDecorationBillboards ? "on" : "off",
        m_showActors ? "on" : "off",
        m_showSpriteObjects ? "on" : "off",
        m_showEntities ? "on" : "off",
        m_showSpawns ? "on" : "off",
        m_inspectMode ? "on" : "off",
        bgfx::isValid(m_terrainTextureAtlasHandle) ? "yes" : "no",
        m_texturedBModelBatches.empty() ? "no" : "yes"
    );
    bgfx::dbgTextPrintf(0, 6, 0x0f, "Move: WASD Space jump Ctrl down Shift turbo  R run F fly T waterwalk G feather");

    int nextHudLine = 7;

    if (m_pOutdoorPartyRuntime)
    {
        const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
        const OutdoorMovementEvents &moveEvents = m_pOutdoorPartyRuntime->movementEvents();
        const OutdoorMovementConsequences &moveConsequences = m_pOutdoorPartyRuntime->movementConsequences();
        const OutdoorPartyMovementState &partyMovementState = m_pOutdoorPartyRuntime->partyMovementState();
        const Party &party = m_pOutdoorPartyRuntime->party();
        std::string leaderSummary = "-";

        if (!party.members().empty())
        {
            const Character &leader = party.members().front();
            leaderSummary = leader.name + "/" + leader.role + " lv" + std::to_string(leader.level);
        }

        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Pos: %.0f %.0f %.0f  support=%s  water=%s  burn=%s  air=%s  land=%s  fall=%.0f",
            m_cameraTargetX,
            m_cameraTargetY,
            m_cameraTargetZ,
            outdoorSupportKindName(moveState.supportKind),
            moveState.supportOnWater ? "on" : "off",
            moveState.supportOnBurning ? "on" : "off",
            moveState.airborne ? "on" : "off",
            moveState.landedThisFrame ? "yes" : "no",
            moveState.fallDistance
        );
        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Mods: run=%s fly=%s waterwalk=%s feather=%s",
            partyMovementState.running ? "on" : "off",
            partyMovementState.flying ? "on" : "off",
            partyMovementState.waterWalk ? "on" : "off",
            partyMovementState.featherFall ? "on" : "off"
        );
        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Events: fall=%s land=%s hard=%s water=%s/%s burn=%s/%s",
            moveEvents.startedFalling ? "yes" : "no",
            moveEvents.landed ? "yes" : "no",
            moveEvents.hardLanding ? "yes" : "no",
            moveEvents.enteredWater ? "in" : "-",
            moveEvents.leftWater ? "out" : "-",
            moveEvents.enteredBurning ? "in" : "-",
            moveEvents.leftBurning ? "out" : "-"
        );
        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Fx: waterDmg=%s burnDmg=%s fallDmg=%s splash=%s land=%s hard=%s",
            moveConsequences.applyWaterDamage ? "yes" : "no",
            moveConsequences.applyBurningDamage ? "yes" : "no",
            moveConsequences.applyFallDamage ? "yes" : "no",
            moveConsequences.playSplashSound ? "yes" : "no",
            moveConsequences.playLandingSound ? "yes" : "no",
            moveConsequences.playHardLandingSound ? "yes" : "no"
        );

        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "Party: members=%u hp=%d/%d gold=%d food=%d items=%u inv=%u/%u lead=%s",
            static_cast<unsigned>(party.members().size()),
            party.totalHealth(),
            party.totalMaxHealth(),
            party.gold(),
            party.food(),
            static_cast<unsigned>(party.inventoryItemCount()),
            static_cast<unsigned>(party.usedInventoryCells()),
            static_cast<unsigned>(party.inventoryCapacity()),
            leaderSummary.c_str()
        );
        bgfx::dbgTextPrintf(
            0,
            nextHudLine++,
            0x0f,
            "PartyFx: waterTicks=%u burnTicks=%u fall=%.0f status=%s",
            party.waterDamageTicks(),
            party.burningDamageTicks(),
            party.lastFallDamageDistance(),
            party.lastStatus().c_str()
        );

        if (m_eventRuntimeState && m_eventRuntimeState->lastActivationResult)
        {
            bgfx::dbgTextPrintf(
                0,
                nextHudLine++,
                0x0f,
                "Activate: %s",
                m_eventRuntimeState->lastActivationResult->c_str()
            );
        }

        if (m_eventRuntimeState)
        {
            std::string runtimeSummary;

            if (m_eventRuntimeState->pendingHouseId)
            {
                runtimeSummary += " house=" + std::to_string(*m_eventRuntimeState->pendingHouseId);
            }

            if (m_eventRuntimeState->pendingNpcId)
            {
                runtimeSummary += " npc=" + std::to_string(*m_eventRuntimeState->pendingNpcId);
            }

            if (m_eventRuntimeState->pendingMapMove)
            {
                runtimeSummary += " map=" + std::to_string(m_eventRuntimeState->pendingMapMove->mapId);

                if (m_eventRuntimeState->pendingMapMove->mapName
                    && !m_eventRuntimeState->pendingMapMove->mapName->empty())
                {
                    runtimeSummary += ":" + *m_eventRuntimeState->pendingMapMove->mapName;
                }
            }

            if (!m_eventRuntimeState->openedChestIds.empty())
            {
                runtimeSummary += " chest=" + std::to_string(m_eventRuntimeState->openedChestIds.back());
            }

            if (!m_eventRuntimeState->grantedItemIds.empty())
            {
                runtimeSummary += " give=" + std::to_string(m_eventRuntimeState->grantedItemIds.back());
            }

            if (!runtimeSummary.empty())
            {
                bgfx::dbgTextPrintf(0, nextHudLine++, 0x0f, "Event:%s", runtimeSummary.c_str());
            }
        }
    }
    else
    {
        bgfx::dbgTextPrintf(0, nextHudLine++, 0x0f, "Pos: %.0f %.0f %.0f", m_cameraTargetX, m_cameraTargetY, m_cameraTargetZ);
    }

    if (m_inspectMode)
    {
        const int inspectBaseLine = nextHudLine + 1;

        if (inspectHit.hasHit)
        {
            if (inspectHit.kind == "entity")
            {
                const std::string primaryEventSummary = summarizeLinkedEvent(
                    inspectHit.eventIdPrimary,
                    m_houseTable,
                    m_localStrTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string secondaryEventSummary = summarizeLinkedEvent(
                    inspectHit.eventIdSecondary,
                    m_houseTable,
                    m_localStrTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string primaryChestSummary = summarizeLinkedChests(
                    inspectHit.eventIdPrimary,
                    m_outdoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string secondaryChestSummary = summarizeLinkedChests(
                    inspectHit.eventIdSecondary,
                    m_outdoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: entity=%u dist=%.0f name=%s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.name.empty() ? "-" : inspectHit.name.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "Entity: dec=%u evt=%u/%u var=%u/%u trig=%u",
                    inspectHit.decorationListId,
                    inspectHit.eventIdPrimary,
                    inspectHit.eventIdSecondary,
                    inspectHit.variablePrimary,
                    inspectHit.variableSecondary,
                    inspectHit.specialTrigger
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 2,
                    0x0f,
                    "Script: P %s | S %s",
                    primaryEventSummary.c_str(),
                    secondaryEventSummary.c_str()
                );
                if (!primaryChestSummary.empty() || !secondaryChestSummary.empty())
                {
                    bgfx::dbgTextPrintf(
                        0,
                        inspectBaseLine + 3,
                        0x0f,
                        "Chest: P %s | S %s",
                        primaryChestSummary.empty() ? "-" : primaryChestSummary.c_str(),
                        secondaryChestSummary.empty() ? "-" : secondaryChestSummary.c_str()
                    );
                }
            }
            else if (inspectHit.kind == "actor")
            {
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: actor=%u dist=%.0f name=%s %s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.name.empty() ? "-" : inspectHit.name.c_str(),
                    inspectHit.isFriendly ? "[friendly]" : "[hostile]"
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "%s",
                    inspectHit.spawnSummary.empty() ? "-" : inspectHit.spawnSummary.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 2,
                    0x0f,
                    "%s",
                    inspectHit.spawnDetail.empty() ? "-" : inspectHit.spawnDetail.c_str()
                );
            }
            else if (inspectHit.kind == "spawn")
            {
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: spawn=%u dist=%.0f type=%u %s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.spawnTypeId,
                    inspectHit.spawnSummary.empty() ? "-" : inspectHit.spawnSummary.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "%s",
                    inspectHit.spawnDetail.empty() ? "-" : inspectHit.spawnDetail.c_str()
                );
                bgfx::dbgTextPrintf(0, inspectBaseLine + 2, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
            }
            else if (inspectHit.kind == "object")
            {
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: object=%u dist=%.0f name=%s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    inspectHit.distance,
                    inspectHit.name.empty() ? "-" : inspectHit.name.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "Object: desc=%u sprite=%u attr=0x%04x spell=%d",
                    inspectHit.objectDescriptionId,
                    inspectHit.objectSpriteId,
                    inspectHit.attributes,
                    inspectHit.spellId
                );
                bgfx::dbgTextPrintf(0, inspectBaseLine + 2, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
            }
            else
            {
                const std::string faceEventSummary = summarizeLinkedEvent(
                    inspectHit.cogTriggeredNumber,
                    m_houseTable,
                    m_localStrTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string faceChestSummary = summarizeLinkedChests(
                    inspectHit.cogTriggeredNumber,
                    m_outdoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine,
                    0x0f,
                    "Inspect: bmodel=%u face=%u distance=%.0f tex=%s",
                    static_cast<unsigned>(inspectHit.bModelIndex),
                    static_cast<unsigned>(inspectHit.faceIndex),
                    inspectHit.distance,
                    inspectHit.textureName.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 1,
                    0x0f,
                    "Face: attr=0x%08x bmp=%d cog=%u evt=%u trig=%u",
                    inspectHit.attributes,
                    inspectHit.bitmapIndex,
                    inspectHit.cogNumber,
                    inspectHit.cogTriggeredNumber,
                    inspectHit.cogTrigger
                );
                bgfx::dbgTextPrintf(
                    0,
                    inspectBaseLine + 2,
                    0x0f,
                    "Type: poly=%u shade=%u vis=%u  Script: %s",
                    static_cast<unsigned>(inspectHit.polygonType),
                    static_cast<unsigned>(inspectHit.shade),
                    static_cast<unsigned>(inspectHit.visibility),
                    faceEventSummary.c_str()
                );
                if (!faceChestSummary.empty())
                {
                    bgfx::dbgTextPrintf(0, inspectBaseLine + 3, 0x0f, "%s", faceChestSummary.c_str());
                }
            }
        }
        else
        {
            bgfx::dbgTextPrintf(0, inspectBaseLine, 0x0f, "Inspect: no outdoor object under cursor");
            bgfx::dbgTextPrintf(0, inspectBaseLine + 1, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
        }
    }

    renderGameplayHudArt(width, height);
    renderGameplayHud(width, height);
}

void TerrainDebugRenderer::renderGameplayHudArt(int width, int height)
{
    if (m_pOutdoorPartyRuntime == nullptr
        || !bgfx::isValid(m_texturedTerrainProgramHandle)
        || !bgfx::isValid(m_terrainTextureSamplerHandle)
        || !bgfx::isValid(m_programHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const HudTextureHandle *pBasebar = findHudTexture("Basebar");
    const HudTextureHandle *pFaceMask = findHudTexture("FACEMASK");
    const HudTextureHandle *pSelectionRing = findHudTexture("selring");
    const HudTextureHandle *pManaFrame = findHudTexture("manaFRM");
    const HudTextureHandle *pHealthBar = findHudTexture("ManaG");
    const HudTextureHandle *pManaBar = findHudTexture("manaB");
    const std::vector<Character> &members = m_pOutdoorPartyRuntime->party().members();

    if (pBasebar == nullptr || pFaceMask == nullptr || members.empty())
    {
        return;
    }

    const float uiScale = std::clamp(static_cast<float>(height) / 600.0f, 1.0f, 1.5f);
    const float basebarWidth = pBasebar->width * uiScale;
    const float basebarHeight = pBasebar->height * uiScale;
    const float basebarX = std::max(0.0f, (static_cast<float>(width) - basebarWidth) * 0.5f);
    const float basebarY = static_cast<float>(height) - basebarHeight;
    const float portraitWidth = pFaceMask->width * uiScale;
    const float portraitHeight = pFaceMask->height * uiScale;
    const float portraitStartX = basebarX + 20.0f * uiScale;
    const float portraitY = basebarY + 23.0f * uiScale;
    const float portraitDeltaX = 97.0f * uiScale;
    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth
    );
    bgfx::setViewRect(HudViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewTransform(HudViewId, nullptr, projectionMatrix);
    bgfx::touch(HudViewId);

    auto submitTexturedQuad =
        [this](
            const HudTextureHandle &texture,
            float x,
            float y,
            float quadWidth,
            float quadHeight)
        {
            if (!bgfx::isValid(texture.textureHandle)
                || bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;
            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
            TexturedTerrainVertex *pVertices = reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);

            pVertices[0] = {x, y, 0.0f, 0.0f, 0.0f};
            pVertices[1] = {x + quadWidth, y, 0.0f, 1.0f, 0.0f};
            pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, 1.0f, 1.0f};
            pVertices[3] = {x, y, 0.0f, 0.0f, 0.0f};
            pVertices[4] = {x + quadWidth, y + quadHeight, 0.0f, 1.0f, 1.0f};
            pVertices[5] = {x, y + quadHeight, 0.0f, 0.0f, 1.0f};

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setTexture(0, m_terrainTextureSamplerHandle, texture.textureHandle);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
        };

    auto submitTexturedQuadUv =
        [this](
            const HudTextureHandle &texture,
            float x,
            float y,
            float quadWidth,
            float quadHeight,
            float u0,
            float v0,
            float u1,
            float v1)
        {
            if (!bgfx::isValid(texture.textureHandle)
                || bgfx::getAvailTransientVertexBuffer(6, TexturedTerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;
            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedTerrainVertex::ms_layout);
            TexturedTerrainVertex *pVertices = reinterpret_cast<TexturedTerrainVertex *>(transientVertexBuffer.data);

            pVertices[0] = {x, y, 0.0f, u0, v0};
            pVertices[1] = {x + quadWidth, y, 0.0f, u1, v0};
            pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
            pVertices[3] = {x, y, 0.0f, u0, v0};
            pVertices[4] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
            pVertices[5] = {x, y + quadHeight, 0.0f, u0, v1};

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setTexture(0, m_terrainTextureSamplerHandle, texture.textureHandle);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, m_texturedTerrainProgramHandle);
        };

    auto submitColoredQuad =
        [this](
            float x,
            float y,
            float quadWidth,
            float quadHeight,
            uint32_t color)
        {
            if (bgfx::getAvailTransientVertexBuffer(6, TerrainVertex::ms_layout) < 6)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer;
            bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TerrainVertex::ms_layout);
            TerrainVertex *pVertices = reinterpret_cast<TerrainVertex *>(transientVertexBuffer.data);

            pVertices[0] = {x, y, 0.0f, color};
            pVertices[1] = {x + quadWidth, y, 0.0f, color};
            pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, color};
            pVertices[3] = {x, y, 0.0f, color};
            pVertices[4] = {x + quadWidth, y + quadHeight, 0.0f, color};
            pVertices[5] = {x, y + quadHeight, 0.0f, color};

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(HudViewId, m_programHandle);
        };

    submitTexturedQuad(*pBasebar, basebarX, basebarY, basebarWidth, basebarHeight);

    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        const Character &member = members[memberIndex];
        const float portraitX = portraitStartX + static_cast<float>(memberIndex) * portraitDeltaX;
        const float portraitInset = 2.0f * uiScale;
        const HudTextureHandle *pPortrait = findHudTexture(member.portraitTextureName);

        if (pPortrait != nullptr)
        {
            submitTexturedQuad(
                *pPortrait,
                portraitX + portraitInset,
                portraitY + portraitInset,
                portraitWidth - portraitInset * 2.0f,
                portraitHeight - portraitInset * 2.0f
            );
        }

        submitTexturedQuad(*pFaceMask, portraitX, portraitY, portraitWidth, portraitHeight);

        if (memberIndex == 0 && pSelectionRing != nullptr)
        {
            submitTexturedQuad(*pSelectionRing, portraitX - uiScale, portraitY, portraitWidth, portraitHeight);
        }

        if (pManaFrame != nullptr)
        {
            const float barFrameX = portraitX + 63.0f * uiScale;
            const float barFrameWidth = pManaFrame->width * uiScale;
            const float barFrameHeight = pManaFrame->height * uiScale;
            const float barFrameY = basebarY + basebarHeight - barFrameHeight - 3.0f * uiScale;
            submitTexturedQuad(*pManaFrame, barFrameX, barFrameY, barFrameWidth, barFrameHeight);

            const float fillHeight = 49.0f * uiScale;
            const float fillY = barFrameY + 1.0f * uiScale;
            const float leftFillX = barFrameX + 2.0f * uiScale;
            const float rightFillX = barFrameX + 5.0f * uiScale;
            const float fillWidth = 3.0f * uiScale;
            const float healthPercent = (member.maxHealth > 0)
                ? std::clamp(static_cast<float>(member.health) / static_cast<float>(member.maxHealth), 0.0f, 1.0f)
                : 0.0f;
            const float manaPercent = (member.maxSpellPoints > 0)
                ? std::clamp(static_cast<float>(member.spellPoints) / static_cast<float>(member.maxSpellPoints), 0.0f, 1.0f)
                : 0.0f;

            if (pHealthBar != nullptr && healthPercent > 0.0f)
            {
                submitTexturedQuadUv(
                    *pHealthBar,
                    leftFillX,
                    fillY + (1.0f - healthPercent) * fillHeight,
                    fillWidth,
                    healthPercent * fillHeight,
                    0.0f,
                    1.0f - healthPercent,
                    1.0f,
                    1.0f
                );
            }

            if (pManaBar != nullptr && manaPercent > 0.0f)
            {
                submitTexturedQuadUv(
                    *pManaBar,
                    rightFillX,
                    fillY + (1.0f - manaPercent) * fillHeight,
                    fillWidth,
                    manaPercent * fillHeight,
                    0.0f,
                    1.0f - manaPercent,
                    1.0f,
                    1.0f
                );
            }
        }
    }
}

void TerrainDebugRenderer::renderGameplayHud(int width, int height) const
{
    if (m_pOutdoorPartyRuntime == nullptr || width <= 0 || height <= 0)
    {
        return;
    }

    const HudTextureHandle *pBasebar = findHudTexture("Basebar");

    if (pBasebar == nullptr)
    {
        return;
    }

    const Party &party = m_pOutdoorPartyRuntime->party();
    const OutdoorMoveState &moveState = m_pOutdoorPartyRuntime->movementState();
    const OutdoorPartyMovementState &partyMovementState = m_pOutdoorPartyRuntime->partyMovementState();
    const std::vector<Character> &members = party.members();
    const int textColumns = std::max(80, width / DebugTextCellWidthPixels);
    const float uiScale = std::clamp(static_cast<float>(height) / 600.0f, 1.0f, 1.5f);
    const float basebarHeight = pBasebar->height * uiScale;
    const float basebarY = static_cast<float>(height) - basebarHeight;
    const float statusCenterY = basebarY + 13.0f * uiScale;
    const int row = std::max(0, static_cast<int>(statusCenterY / DebugTextCellHeightPixels));
    std::ostringstream stream;

    if (!members.empty())
    {
        const Character &leader = members.front();
        stream << leader.name
               << " HP "
               << leader.health
               << "/"
               << leader.maxHealth
               << " SP "
               << leader.spellPoints
               << "/"
               << leader.maxSpellPoints
               << "   ";
    }

    stream << "Gold "
           << party.gold()
           << "  Food "
           << party.food()
           << "  "
           << outdoorSupportKindName(moveState.supportKind);

    if (moveState.supportOnWater)
    {
        stream << " water";
    }

    if (moveState.supportOnBurning)
    {
        stream << " burn";
    }

    if (partyMovementState.running)
    {
        stream << " run";
    }

    if (partyMovementState.flying)
    {
        stream << " fly";
    }

    const std::string status = stream.str();
    const int startColumn = std::max(0, (textColumns - static_cast<int>(status.size())) / 2);
    bgfx::dbgTextPrintf(static_cast<uint16_t>(startColumn), static_cast<uint16_t>(row), 0x0f, "%s", status.c_str());
}

void TerrainDebugRenderer::shutdown()
{
    if (bgfx::isValid(m_programHandle))
    {
        bgfx::destroy(m_programHandle);
        m_programHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_texturedTerrainProgramHandle))
    {
        bgfx::destroy(m_texturedTerrainProgramHandle);
        m_texturedTerrainProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainTextureAtlasHandle))
    {
        bgfx::destroy(m_terrainTextureAtlasHandle);
        m_terrainTextureAtlasHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainTextureSamplerHandle))
    {
        bgfx::destroy(m_terrainTextureSamplerHandle);
        m_terrainTextureSamplerHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_indexBufferHandle))
    {
        bgfx::destroy(m_indexBufferHandle);
        m_indexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_filledTerrainVertexBufferHandle))
    {
        bgfx::destroy(m_filledTerrainVertexBufferHandle);
        m_filledTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    for (TexturedBModelBatch &batch : m_texturedBModelBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
            batch.vertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        if (bgfx::isValid(batch.textureHandle))
        {
            bgfx::destroy(batch.textureHandle);
            batch.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_texturedBModelBatches.clear();

    for (BillboardTextureHandle &textureHandle : m_billboardTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_billboardTextureHandles.clear();

    for (HudTextureHandle &textureHandle : m_hudTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_hudTextureHandles.clear();

    if (bgfx::isValid(m_texturedTerrainVertexBufferHandle))
    {
        bgfx::destroy(m_texturedTerrainVertexBufferHandle);
        m_texturedTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_bmodelVertexBufferHandle))
    {
        bgfx::destroy(m_bmodelVertexBufferHandle);
        m_bmodelVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_bmodelCollisionVertexBufferHandle))
    {
        bgfx::destroy(m_bmodelCollisionVertexBufferHandle);
        m_bmodelCollisionVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_entityMarkerVertexBufferHandle))
    {
        bgfx::destroy(m_entityMarkerVertexBufferHandle);
        m_entityMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_spawnMarkerVertexBufferHandle))
    {
        bgfx::destroy(m_spawnMarkerVertexBufferHandle);
        m_spawnMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_vertexBufferHandle))
    {
        bgfx::destroy(m_vertexBufferHandle);
        m_vertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    m_isRenderable = false;
    m_isInitialized = false;
    m_map.reset();
    m_monsterTable.reset();
    m_outdoorMapData.reset();
    m_pOutdoorPartyRuntime = nullptr;
    m_eventRuntimeState.reset();
    m_localEventIrProgram.reset();
    m_globalEventIrProgram.reset();
    m_outdoorDecorationBillboardSet.reset();
    m_outdoorActorPreviewBillboardSet.reset();
    m_outdoorSpriteObjectBillboardSet.reset();
    m_elapsedTime = 0.0f;
    m_framesPerSecond = 0.0f;
    m_bmodelLineVertexCount = 0;
    m_bmodelCollisionVertexCount = 0;
    m_bmodelFaceCount = 0;
    m_entityMarkerVertexCount = 0;
    m_spawnMarkerVertexCount = 0;
    m_lastTickCount = 0;
    m_toggleFilledLatch = false;
    m_toggleWireframeLatch = false;
    m_toggleBModelsLatch = false;
    m_toggleBModelWireframeLatch = false;
    m_toggleDecorationBillboardsLatch = false;
    m_toggleActorsLatch = false;
    m_toggleSpriteObjectsLatch = false;
    m_toggleEntitiesLatch = false;
    m_toggleSpawnsLatch = false;
    m_toggleInspectLatch = false;
    m_isRotatingCamera = false;
    m_lastMouseX = 0.0f;
    m_lastMouseY = 0.0f;
}

void TerrainDebugRenderer::TerrainVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

void TerrainDebugRenderer::TexturedTerrainVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
}

uint32_t TerrainDebugRenderer::colorFromHeight(float normalizedHeight)
{
    BX_UNUSED(normalizedHeight);
    const uint8_t red = 160;
    const uint8_t green = 160;
    const uint8_t blue = 160;
    const uint8_t alpha = 255;

    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

uint32_t TerrainDebugRenderer::colorFromBModel()
{
    const uint8_t red = 255;
    const uint8_t green = 255;
    const uint8_t blue = 255;
    const uint8_t alpha = 255;

    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

bgfx::ProgramHandle TerrainDebugRenderer::loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadShader(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadShader(pFragmentShaderName);

    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

bgfx::ShaderHandle TerrainDebugRenderer::loadShader(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        std::cerr << "Failed to read shader: " << shaderPath << '\n';
        return BGFX_INVALID_HANDLE;
    }

    const bgfx::Memory *pShaderMemory = bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size()));
    return bgfx::createShader(pShaderMemory);
}

const TerrainDebugRenderer::BillboardTextureHandle *TerrainDebugRenderer::findBillboardTexture(
    const std::string &textureName
) const
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const BillboardTextureHandle &textureHandle : m_billboardTextureHandles)
    {
        if (textureHandle.textureName == normalizedTextureName)
        {
            return &textureHandle;
        }
    }

    return nullptr;
}

const TerrainDebugRenderer::HudTextureHandle *TerrainDebugRenderer::findHudTexture(const std::string &textureName) const
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const HudTextureHandle &textureHandle : m_hudTextureHandles)
    {
        if (textureHandle.textureName == normalizedTextureName)
        {
            return &textureHandle;
        }
    }

    return nullptr;
}

bool TerrainDebugRenderer::loadHudTexture(const Engine::AssetFileSystem &assetFileSystem, const std::string &textureName)
{
    if (findHudTexture(textureName) != nullptr)
    {
        return true;
    }

    int width = 0;
    int height = 0;
    const std::optional<std::vector<uint8_t>> pixels =
        loadBitmapPixelsBgra(assetFileSystem, textureName, width, height, true);

    if (!pixels || width <= 0 || height <= 0)
    {
        return false;
    }

    HudTextureHandle textureHandle = {};
    textureHandle.textureName = toLowerCopy(textureName);
    textureHandle.width = width;
    textureHandle.height = height;
    textureHandle.textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(pixels->data(), static_cast<uint32_t>(pixels->size()))
    );

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        return false;
    }

    m_hudTextureHandles.push_back(std::move(textureHandle));
    return true;
}

void TerrainDebugRenderer::renderDecorationBillboards(
    uint16_t viewId,
    uint16_t viewWidth,
    uint16_t viewHeight,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition
)
{
    if (!m_outdoorDecorationBillboardSet
        || !bgfx::isValid(m_texturedTerrainProgramHandle)
        || !bgfx::isValid(m_terrainTextureSamplerHandle))
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const float cosPitch = std::cos(m_cameraPitchRadians);
    const bx::Vec3 cameraForward = {
        std::cos(m_cameraYawRadians) * cosPitch,
        -std::sin(m_cameraYawRadians) * cosPitch,
        std::sin(m_cameraPitchRadians)
    };
    const float aspectRatio = static_cast<float>(std::max<uint16_t>(viewWidth, 1))
        / static_cast<float>(std::max<uint16_t>(viewHeight, 1));
    const float tanHalfFovY = std::tan(CameraVerticalFovRadians * 0.5f);
    const float tanHalfFovX = tanHalfFovY * aspectRatio;
    const float viewPlaneDistPixels = (static_cast<float>(viewHeight) * 0.5f) / tanHalfFovY;
    const uint32_t animationTimeTicks = currentAnimationTicks();
    struct BillboardDrawItem
    {
        const DecorationBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(m_outdoorDecorationBillboardSet->billboards.size());

    for (const DecorationBillboard &billboard : m_outdoorDecorationBillboardSet->billboards)
    {
        if (billboard.spriteId == 0)
        {
            continue;
        }

        const uint32_t animationOffsetTicks =
            animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
        const SpriteFrameEntry *pFrame =
            m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(billboard.spriteId, animationOffsetTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
        const float angleToCamera = std::atan2(
            static_cast<float>(-billboard.x) - cameraPosition.x,
            static_cast<float>(billboard.y) - cameraPosition.y
        );
        const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
        const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
        const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle) || pTexture->width <= 0 || pTexture->height <= 0)
        {
            continue;
        }

        const float deltaX = static_cast<float>(-billboard.x) - cameraPosition.x;
        const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
        const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;

        BillboardDrawItem drawItem = {};
        drawItem.pBillboard = &billboard;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        drawItems.push_back(drawItem);
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            return left.distanceSquared > right.distanceSquared;
        }
    );

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const DecorationBillboard &billboard = *drawItem.pBillboard;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;

        const float spriteScale = std::max(frame.scale, 0.01f);
        const bx::Vec3 basePosition = {
            static_cast<float>(-billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z)
        };
        const bx::Vec3 cameraToBase = vecSubtract(basePosition, cameraPosition);
        const float forwardDistance = vecDot(cameraToBase, cameraForward);

        if (forwardDistance <= BillboardNearDepth)
        {
            continue;
        }

        const float cameraRightDistance = vecDot(cameraToBase, cameraRight);
        const float cameraUpDistance = vecDot(cameraToBase, cameraUp);
        const float centerNdcX = cameraRightDistance / (forwardDistance * tanHalfFovX);
        const float baseNdcY = cameraUpDistance / (forwardDistance * tanHalfFovY);
        const float billboardWidthPixels =
            spriteScale * static_cast<float>(texture.width) * viewPlaneDistPixels / forwardDistance;
        const float billboardHeightPixels =
            spriteScale * static_cast<float>(texture.height) * viewPlaneDistPixels / forwardDistance;
        const float halfWidthNdc =
            billboardWidthPixels / static_cast<float>(std::max<uint16_t>(viewWidth, 1));
        const float heightNdc =
            (2.0f * billboardHeightPixels) / static_cast<float>(std::max<uint16_t>(viewHeight, 1));

        if (centerNdcX + halfWidthNdc < -1.0f
            || centerNdcX - halfWidthNdc > 1.0f
            || baseNdcY > 1.0f
            || (baseNdcY + heightNdc) < -1.0f)
        {
            continue;
        }

        const auto unprojectBillboardPoint =
            [&cameraPosition, &cameraForward, &cameraRight, &cameraUp, forwardDistance, tanHalfFovX, tanHalfFovY](
                float ndcX,
                float ndcY
            )
        {
            const float offsetRight = ndcX * forwardDistance * tanHalfFovX;
            const float offsetUp = ndcY * forwardDistance * tanHalfFovY;
            bx::Vec3 position = vecAdd(cameraPosition, vecScale(cameraForward, forwardDistance));
            position = vecAdd(position, vecScale(cameraRight, offsetRight));
            position = vecAdd(position, vecScale(cameraUp, offsetUp));
            return position;
        };

        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
        const float v0 = 0.0f;
        const float v1 = 1.0f;
        const bx::Vec3 bottomLeft = unprojectBillboardPoint(centerNdcX - halfWidthNdc, baseNdcY);
        const bx::Vec3 topLeft = unprojectBillboardPoint(centerNdcX - halfWidthNdc, baseNdcY + heightNdc);
        const bx::Vec3 topRight = unprojectBillboardPoint(centerNdcX + halfWidthNdc, baseNdcY + heightNdc);
        const bx::Vec3 bottomRight = unprojectBillboardPoint(centerNdcX + halfWidthNdc, baseNdcY);

        std::array<TexturedTerrainVertex, 6> vertices = {{
            {bottomLeft.x, bottomLeft.y, bottomLeft.z, u0, v1},
            {topLeft.x, topLeft.y, topLeft.z, u0, v0},
            {topRight.x, topRight.y, topRight.z, u1, v0},
            {bottomLeft.x, bottomLeft.y, bottomLeft.z, u0, v1},
            {topRight.x, topRight.y, topRight.z, u1, v0},
            {bottomRight.x, bottomRight.y, bottomRight.z, u1, v1}
        }};

        if (bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(vertices.size()),
                TexturedTerrainVertex::ms_layout
            ) < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            TexturedTerrainVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedTerrainVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, m_terrainTextureSamplerHandle, texture.textureHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(viewId, m_texturedTerrainProgramHandle);
    }
}

void TerrainDebugRenderer::renderActorPreviewBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition
)
{
    if (!m_outdoorActorPreviewBillboardSet)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const uint32_t animationTimeTicks = currentAnimationTicks();

    struct BillboardDrawItem
    {
        const ActorPreviewBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(m_outdoorActorPreviewBillboardSet->billboards.size());

    std::vector<TerrainVertex> placeholderVertices;
    placeholderVertices.reserve(m_outdoorActorPreviewBillboardSet->billboards.size() * 6);

    for (const ActorPreviewBillboard &billboard : m_outdoorActorPreviewBillboardSet->billboards)
    {
        const float markerHalfSize =
            std::max(48.0f, static_cast<float>(std::max(billboard.radius, static_cast<uint16_t>(48))));
        const float baseX = static_cast<float>(-billboard.x);
        const float baseY = static_cast<float>(billboard.y);
        const float baseZ = static_cast<float>(billboard.z) + 96.0f;
        const uint32_t markerColor = 0xff3030ff;

        placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
        placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
        placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
        placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
        placeholderVertices.push_back({baseX, baseY - markerHalfSize, baseZ, markerColor});
        placeholderVertices.push_back({baseX, baseY + markerHalfSize, baseZ, markerColor});

        const uint32_t frameTimeTicks = billboard.useStaticFrame ? 0U : animationTimeTicks;
        const SpriteFrameEntry *pFrame =
            m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(billboard.spriteFrameIndex, frameTimeTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const float angleToCamera = std::atan2(
            static_cast<float>(-billboard.x) - cameraPosition.x,
            static_cast<float>(billboard.y) - cameraPosition.y
        );
        const float octantAngle = -angleToCamera + Pi + (Pi / 8.0f);
        const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
        const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        const float deltaX = static_cast<float>(-billboard.x) - cameraPosition.x;
        const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
        const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;

        BillboardDrawItem drawItem = {};
        drawItem.pBillboard = &billboard;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        drawItems.push_back(drawItem);
    }

    if (!placeholderVertices.empty())
    {
        if (bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(placeholderVertices.size()),
                TerrainVertex::ms_layout) >= placeholderVertices.size())
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(placeholderVertices.size()),
                TerrainVertex::ms_layout
            );
            std::memcpy(
                transientVertexBuffer.data,
                placeholderVertices.data(),
                static_cast<size_t>(placeholderVertices.size() * sizeof(TerrainVertex))
            );

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(placeholderVertices.size()));
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_LINEAA
                | BGFX_STATE_DEPTH_TEST_LEQUAL
            );
            bgfx::submit(viewId, m_programHandle);
        }
    }

    if (!bgfx::isValid(m_texturedTerrainProgramHandle) || !bgfx::isValid(m_terrainTextureSamplerHandle))
    {
        return;
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            return left.distanceSquared > right.distanceSquared;
        }
    );

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const ActorPreviewBillboard &billboard = *drawItem.pBillboard;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            static_cast<float>(-billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z) + worldHeight * 0.5f
        };
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {cameraUp.x * worldHeight * 0.5f, cameraUp.y * worldHeight * 0.5f, cameraUp.z * worldHeight * 0.5f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        std::array<TexturedTerrainVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), TexturedTerrainVertex::ms_layout)
            < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            TexturedTerrainVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedTerrainVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, m_terrainTextureSamplerHandle, texture.textureHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(viewId, m_texturedTerrainProgramHandle);
    }
}

void TerrainDebugRenderer::renderSpriteObjectBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition
)
{
    if (!m_outdoorSpriteObjectBillboardSet)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};

    struct BillboardDrawItem
    {
        const SpriteObjectBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(m_outdoorSpriteObjectBillboardSet->billboards.size());

    for (const SpriteObjectBillboard &billboard : m_outdoorSpriteObjectBillboardSet->billboards)
    {
        const SpriteFrameEntry *pFrame =
            m_outdoorSpriteObjectBillboardSet->spriteFrameTable.getFrame(
                billboard.objectSpriteId,
                billboard.timeSinceCreatedTicks
            );

        if (pFrame == nullptr)
        {
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        const float deltaX = float(-billboard.x) - cameraPosition.x;
        const float deltaY = float(billboard.y) - cameraPosition.y;
        const float deltaZ = float(billboard.z) - cameraPosition.z;

        BillboardDrawItem drawItem = {};
        drawItem.pBillboard = &billboard;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        drawItems.push_back(drawItem);
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            return left.distanceSquared > right.distanceSquared;
        }
    );

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const SpriteObjectBillboard &billboard = *drawItem.pBillboard;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = float(texture.width) * spriteScale;
        const float worldHeight = float(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            float(-billboard.x),
            float(billboard.y),
            float(billboard.z) + worldHeight * 0.5f
        };
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {cameraUp.x * worldHeight * 0.5f, cameraUp.y * worldHeight * 0.5f, cameraUp.z * worldHeight * 0.5f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        std::array<TexturedTerrainVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), TexturedTerrainVertex::ms_layout)
            < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            TexturedTerrainVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedTerrainVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, m_terrainTextureSamplerHandle, texture.textureHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(viewId, m_texturedTerrainProgramHandle);
    }
}

std::vector<TerrainDebugRenderer::TerrainVertex> TerrainDebugRenderer::buildVertices(const OutdoorMapData &outdoorMapData)
{
    std::vector<TerrainVertex> vertices;
    vertices.reserve(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight);

    const float minHeight = static_cast<float>(outdoorMapData.minHeightSample);
    const float maxHeight = static_cast<float>(outdoorMapData.maxHeightSample);
    const float heightRange = std::max(maxHeight - minHeight, 1.0f);

    for (int gridY = 0; gridY < OutdoorMapData::TerrainHeight; ++gridY)
    {
        for (int gridX = 0; gridX < OutdoorMapData::TerrainWidth; ++gridX)
        {
            const size_t sampleIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const float heightSample = static_cast<float>(outdoorMapData.heightMap[sampleIndex]);
            const float normalizedHeight = (heightSample - minHeight) / heightRange;
            TerrainVertex vertex = {};
            vertex.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            vertex.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            vertex.z = heightSample * static_cast<float>(OutdoorMapData::TerrainHeightScale);
            vertex.abgr = colorFromHeight(normalizedHeight);
            vertices.push_back(vertex);
        }
    }

    return vertices;
}

std::vector<uint16_t> TerrainDebugRenderer::buildIndices()
{
    std::vector<uint16_t> indices;
    indices.reserve((OutdoorMapData::TerrainWidth - 1) * (OutdoorMapData::TerrainHeight - 1) * 8);

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const uint16_t topLeft =
                static_cast<uint16_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint16_t topRight = static_cast<uint16_t>(topLeft + 1);
            const uint16_t bottomLeft =
                static_cast<uint16_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const uint16_t bottomRight = static_cast<uint16_t>(bottomLeft + 1);

            indices.push_back(topLeft);
            indices.push_back(topRight);

            indices.push_back(topRight);
            indices.push_back(bottomRight);

            indices.push_back(bottomRight);
            indices.push_back(bottomLeft);

            indices.push_back(bottomLeft);
            indices.push_back(topLeft);
        }
    }

    return indices;
}

std::vector<TerrainDebugRenderer::TexturedTerrainVertex> TerrainDebugRenderer::buildTexturedTerrainVertices(
    const OutdoorMapData &outdoorMapData,
    const OutdoorTerrainTextureAtlas &outdoorTerrainTextureAtlas
)
{
    std::vector<TexturedTerrainVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1)
        * 6
    );

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const OutdoorTerrainAtlasRegion &region =
                outdoorTerrainTextureAtlas.tileRegions[static_cast<size_t>(rawTileId)];

            if (!region.isValid)
            {
                continue;
            }

            const size_t topLeftIndex = tileMapIndex;
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex =
                static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;

            TexturedTerrainVertex topLeft = {};
            topLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            topLeft.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topLeft.z = static_cast<float>(outdoorMapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale);
            topLeft.u = region.u0;
            topLeft.v = region.v0;

            TexturedTerrainVertex topRight = {};
            topRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            topRight.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topRight.z = static_cast<float>(outdoorMapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale);
            topRight.u = region.u1;
            topRight.v = region.v0;

            TexturedTerrainVertex bottomLeft = {};
            bottomLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            bottomLeft.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomLeft.z =
                static_cast<float>(outdoorMapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale);
            bottomLeft.u = region.u0;
            bottomLeft.v = region.v1;

            TexturedTerrainVertex bottomRight = {};
            bottomRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.z =
                static_cast<float>(outdoorMapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale);
            bottomRight.u = region.u1;
            bottomRight.v = region.v1;

            vertices.push_back(topLeft);
            vertices.push_back(bottomLeft);
            vertices.push_back(topRight);
            vertices.push_back(topRight);
            vertices.push_back(bottomLeft);
            vertices.push_back(bottomRight);
        }
    }

    return vertices;
}

std::vector<TerrainDebugRenderer::TexturedTerrainVertex> TerrainDebugRenderer::buildTexturedBModelVertices(
    const OutdoorMapData &outdoorMapData,
    const OutdoorBitmapTexture &texture
)
{
    std::vector<TexturedTerrainVertex> vertices;
    const std::string normalizedTextureName = toLowerCopy(texture.textureName);

    if (texture.width <= 0 || texture.height <= 0)
    {
        return vertices;
    }

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.vertexIndices.size() < 3 || face.textureName.empty())
            {
                continue;
            }

            if (toLowerCopy(face.textureName) != normalizedTextureName)
            {
                continue;
            }

            for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
            {
                const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
                TexturedTerrainVertex triangleVertices[3] = {};
                bool isTriangleValid = true;

                for (size_t triangleVertexSlot = 0; triangleVertexSlot < 3; ++triangleVertexSlot)
                {
                    const size_t localTriangleVertexIndex = triangleVertexIndices[triangleVertexSlot];
                    const uint16_t modelVertexIndex = face.vertexIndices[localTriangleVertexIndex];

                    if (modelVertexIndex >= bmodel.vertices.size()
                        || localTriangleVertexIndex >= face.textureUs.size()
                        || localTriangleVertexIndex >= face.textureVs.size())
                    {
                        isTriangleValid = false;
                        break;
                    }

                    const bx::Vec3 worldVertex = outdoorBModelVertexToWorld(bmodel.vertices[modelVertexIndex]);
                    const float normalizedU =
                        static_cast<float>(face.textureUs[localTriangleVertexIndex] + face.textureDeltaU)
                        / static_cast<float>(texture.width);
                    const float normalizedV =
                        static_cast<float>(face.textureVs[localTriangleVertexIndex] + face.textureDeltaV)
                        / static_cast<float>(texture.height);

                    TexturedTerrainVertex vertex = {};
                    vertex.x = worldVertex.x;
                    vertex.y = worldVertex.y;
                    vertex.z = worldVertex.z;
                    vertex.u = normalizedU;
                    vertex.v = normalizedV;
                    triangleVertices[triangleVertexSlot] = vertex;
                }

                if (!isTriangleValid)
                {
                    continue;
                }

                for (const TexturedTerrainVertex &vertex : triangleVertices)
                {
                    vertices.push_back(vertex);
                }
            }
        }
    }

    return vertices;
}

std::vector<TerrainDebugRenderer::TerrainVertex> TerrainDebugRenderer::buildFilledTerrainVertices(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint32_t>> &outdoorTileColors
)
{
    std::vector<TerrainVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1)
        * 6
    );

    const uint32_t fallbackColor = 0xff707070u;

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t topLeftIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex =
                static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const size_t tileColorIndex =
                static_cast<size_t>(gridY * (OutdoorMapData::TerrainWidth - 1) + gridX);
            const uint32_t tileColor =
                outdoorTileColors ? (*outdoorTileColors)[tileColorIndex] : fallbackColor;

            TerrainVertex topLeft = {};
            topLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            topLeft.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topLeft.z = static_cast<float>(outdoorMapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale);
            topLeft.abgr = tileColor;

            TerrainVertex topRight = {};
            topRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            topRight.y = static_cast<float>((64 - gridY) * OutdoorMapData::TerrainTileSize);
            topRight.z = static_cast<float>(outdoorMapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale);
            topRight.abgr = tileColor;

            TerrainVertex bottomLeft = {};
            bottomLeft.x = static_cast<float>((64 - gridX) * OutdoorMapData::TerrainTileSize);
            bottomLeft.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomLeft.z =
                static_cast<float>(outdoorMapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale);
            bottomLeft.abgr = tileColor;

            TerrainVertex bottomRight = {};
            bottomRight.x = static_cast<float>((64 - (gridX + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.y = static_cast<float>((64 - (gridY + 1)) * OutdoorMapData::TerrainTileSize);
            bottomRight.z =
                static_cast<float>(outdoorMapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale);
            bottomRight.abgr = tileColor;

            vertices.push_back(topLeft);
            vertices.push_back(bottomLeft);
            vertices.push_back(topRight);
            vertices.push_back(topRight);
            vertices.push_back(bottomLeft);
            vertices.push_back(bottomRight);
        }
    }

    return vertices;
}

std::vector<TerrainDebugRenderer::TerrainVertex> TerrainDebugRenderer::buildBModelWireframeVertices(
    const OutdoorMapData &outdoorMapData
)
{
    std::vector<TerrainVertex> vertices;

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.vertexIndices.size() < 2)
            {
                continue;
            }

            for (size_t vertexIndex = 0; vertexIndex < face.vertexIndices.size(); ++vertexIndex)
            {
                const uint16_t startIndex = face.vertexIndices[vertexIndex];
                const uint16_t endIndex = face.vertexIndices[(vertexIndex + 1) % face.vertexIndices.size()];

                if (startIndex >= bmodel.vertices.size() || endIndex >= bmodel.vertices.size())
                {
                    continue;
                }

                const bx::Vec3 startVertex = outdoorBModelVertexToWorld(bmodel.vertices[startIndex]);
                const bx::Vec3 endVertex = outdoorBModelVertexToWorld(bmodel.vertices[endIndex]);

                TerrainVertex lineStart = {};
                lineStart.x = startVertex.x;
                lineStart.y = startVertex.y;
                lineStart.z = startVertex.z;
                lineStart.abgr = colorFromBModel();
                vertices.push_back(lineStart);

                TerrainVertex lineEnd = {};
                lineEnd.x = endVertex.x;
                lineEnd.y = endVertex.y;
                lineEnd.z = endVertex.z;
                lineEnd.abgr = colorFromBModel();
                vertices.push_back(lineEnd);
            }
        }
    }

    return vertices;
}

std::vector<TerrainDebugRenderer::TerrainVertex> TerrainDebugRenderer::buildBModelCollisionFaceVertices(
    const OutdoorMapData &outdoorMapData
)
{
    std::vector<TerrainVertex> vertices;
    const uint32_t walkableColor = 0x6600ff00u;
    const uint32_t blockingColor = 0x66ff0000u;

    for (const OutdoorBModel &bModel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bModel.faces)
        {
            if (face.vertexIndices.size() < 3)
            {
                continue;
            }

            std::vector<bx::Vec3> polygonVertices;
            polygonVertices.reserve(face.vertexIndices.size());

            for (uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex >= bModel.vertices.size())
                {
                    polygonVertices.clear();
                    break;
                }

                polygonVertices.push_back(outdoorBModelVertexToWorld(bModel.vertices[vertexIndex]));
            }

            if (polygonVertices.size() < 3)
            {
                continue;
            }

            const uint32_t color = isOutdoorWalkablePolygonType(face.polygonType) ? walkableColor : blockingColor;

            for (size_t triangleIndex = 1; triangleIndex + 1 < polygonVertices.size(); ++triangleIndex)
            {
                const bx::Vec3 &vertex0 = polygonVertices[0];
                const bx::Vec3 &vertex1 = polygonVertices[triangleIndex];
                const bx::Vec3 &vertex2 = polygonVertices[triangleIndex + 1];

                vertices.push_back({vertex0.x, vertex0.y, vertex0.z, color});
                vertices.push_back({vertex1.x, vertex1.y, vertex1.z, color});
                vertices.push_back({vertex2.x, vertex2.y, vertex2.z, color});
            }
        }
    }

    return vertices;
}

std::vector<TerrainDebugRenderer::TerrainVertex> TerrainDebugRenderer::buildEntityMarkerVertices(
    const OutdoorMapData &outdoorMapData
)
{
    std::vector<TerrainVertex> vertices;
    const uint32_t color = makeAbgr(255, 208, 64);
    const float halfExtent = 96.0f;
    const float height = 192.0f;
    vertices.reserve(outdoorMapData.entities.size() * 6);

    for (const OutdoorEntity &entity : outdoorMapData.entities)
    {
        const float centerX = static_cast<float>(-entity.x);
        const float centerY = static_cast<float>(entity.y);
        const float baseZ = static_cast<float>(entity.z);

        vertices.push_back({centerX - halfExtent, centerY, baseZ + height * 0.5f, color});
        vertices.push_back({centerX + halfExtent, centerY, baseZ + height * 0.5f, color});
        vertices.push_back({centerX, centerY - halfExtent, baseZ + height * 0.5f, color});
        vertices.push_back({centerX, centerY + halfExtent, baseZ + height * 0.5f, color});
        vertices.push_back({centerX, centerY, baseZ, color});
        vertices.push_back({centerX, centerY, baseZ + height, color});
    }

    return vertices;
}

std::vector<TerrainDebugRenderer::TerrainVertex> TerrainDebugRenderer::buildSpawnMarkerVertices(
    const OutdoorMapData &outdoorMapData
)
{
    std::vector<TerrainVertex> vertices;
    const uint32_t color = makeAbgr(96, 192, 255);
    vertices.reserve(outdoorMapData.spawns.size() * 6);

    for (const OutdoorSpawn &spawn : outdoorMapData.spawns)
    {
        const float centerX = static_cast<float>(-spawn.x);
        const float centerY = static_cast<float>(spawn.y);
        const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.radius, 64));
        const float groundHeight = sampleOutdoorTerrainHeight(
            outdoorMapData,
            static_cast<float>(spawn.x),
            static_cast<float>(spawn.y)
        );
        const int groundedZ = std::max(spawn.z, static_cast<int>(std::lround(groundHeight)));
        const float centerZ = static_cast<float>(groundedZ) + halfExtent;

        vertices.push_back({centerX - halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX + halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX, centerY - halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY + halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY, centerZ - halfExtent, color});
        vertices.push_back({centerX, centerY, centerZ + halfExtent, color});
    }

    return vertices;
}

TerrainDebugRenderer::InspectHit TerrainDebugRenderer::inspectBModelFace(
    const OutdoorMapData &outdoorMapData,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection
)
{
    InspectHit bestHit = {};
    bestHit.distance = std::numeric_limits<float>::max();

    if (vecLength(rayDirection) <= InspectRayEpsilon)
    {
        return {};
    }

    for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bModel = outdoorMapData.bmodels[bModelIndex];

        for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
        {
            const OutdoorBModelFace &face = bModel.faces[faceIndex];

            if (face.vertexIndices.size() < 3)
            {
                continue;
            }

            for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
            {
                const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
                bx::Vec3 triangleVertices[3] = {
                    bx::Vec3 {0.0f, 0.0f, 0.0f},
                    bx::Vec3 {0.0f, 0.0f, 0.0f},
                    bx::Vec3 {0.0f, 0.0f, 0.0f}
                };
                bool isTriangleValid = true;

                for (size_t triangleVertexSlot = 0; triangleVertexSlot < 3; ++triangleVertexSlot)
                {
                    const uint16_t vertexIndex = face.vertexIndices[triangleVertexIndices[triangleVertexSlot]];

                    if (vertexIndex >= bModel.vertices.size())
                    {
                        isTriangleValid = false;
                        break;
                    }

                    triangleVertices[triangleVertexSlot] = outdoorBModelVertexToWorld(bModel.vertices[vertexIndex]);
                }

                if (!isTriangleValid)
                {
                    continue;
                }

                float distance = 0.0f;

                if (!intersectRayTriangle(
                        rayOrigin,
                        rayDirection,
                        triangleVertices[0],
                        triangleVertices[1],
                        triangleVertices[2],
                        distance))
                {
                    continue;
                }

                if (!bestHit.hasHit || distance < bestHit.distance)
                {
                    bestHit.hasHit = true;
                    bestHit.kind = "face";
                    bestHit.bModelIndex = bModelIndex;
                    bestHit.faceIndex = faceIndex;
                    bestHit.textureName = face.textureName;
                    bestHit.distance = distance;
                    bestHit.attributes = face.attributes;
                    bestHit.bitmapIndex = face.bitmapIndex;
                    bestHit.cogNumber = face.cogNumber;
                    bestHit.cogTriggeredNumber = face.cogTriggeredNumber;
                    bestHit.cogTrigger = face.cogTrigger;
                    bestHit.polygonType = face.polygonType;
                    bestHit.shade = face.shade;
                    bestHit.visibility = face.visibility;
                }
            }
        }
    }

    for (size_t entityIndex = 0; entityIndex < outdoorMapData.entities.size(); ++entityIndex)
    {
        const OutdoorEntity &entity = outdoorMapData.entities[entityIndex];
        const float halfExtent = 96.0f;
        float distance = 0.0f;

        const bx::Vec3 minBounds = {
            static_cast<float>(-entity.x) - halfExtent,
            static_cast<float>(entity.y) - halfExtent,
            static_cast<float>(entity.z)
        };
        const bx::Vec3 maxBounds = {
            static_cast<float>(-entity.x) + halfExtent,
            static_cast<float>(entity.y) + halfExtent,
            static_cast<float>(entity.z) + 192.0f
        };

        if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
            && (!bestHit.hasHit || distance < bestHit.distance))
        {
            bestHit.hasHit = true;
            bestHit.kind = "entity";
            bestHit.bModelIndex = entityIndex;
            bestHit.faceIndex = 0;
            bestHit.name = entity.name;
            bestHit.distance = distance;
            bestHit.decorationListId = entity.decorationListId;
            bestHit.eventIdPrimary = entity.eventIdPrimary;
            bestHit.eventIdSecondary = entity.eventIdSecondary;
            bestHit.variablePrimary = entity.variablePrimary;
            bestHit.variableSecondary = entity.variableSecondary;
            bestHit.specialTrigger = entity.specialTrigger;
        }
    }

    for (size_t spawnIndex = 0; spawnIndex < outdoorMapData.spawns.size(); ++spawnIndex)
    {
        const OutdoorSpawn &spawn = outdoorMapData.spawns[spawnIndex];
        const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.radius, 64));
        const float groundHeight = sampleOutdoorTerrainHeight(
            outdoorMapData,
            static_cast<float>(spawn.x),
            static_cast<float>(spawn.y)
        );
        const int groundedZ = std::max(spawn.z, static_cast<int>(std::lround(groundHeight)));
        float distance = 0.0f;
        const bx::Vec3 minBounds = {
            static_cast<float>(-spawn.x) - halfExtent,
            static_cast<float>(spawn.y) - halfExtent,
            static_cast<float>(groundedZ)
        };
        const bx::Vec3 maxBounds = {
            static_cast<float>(-spawn.x) + halfExtent,
            static_cast<float>(spawn.y) + halfExtent,
            static_cast<float>(groundedZ) + halfExtent * 2.0f
        };

        if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
            && (!bestHit.hasHit || distance < bestHit.distance))
        {
            bestHit.hasHit = true;
            bestHit.kind = "spawn";
            bestHit.bModelIndex = spawnIndex;
            bestHit.faceIndex = 0;
            bestHit.distance = distance;
            bestHit.spawnTypeId = spawn.typeId;

            if (m_map)
            {
                const SpawnPreview preview =
                    SpawnPreviewResolver::describe(
                        *m_map,
                        m_monsterTable ? &*m_monsterTable : nullptr,
                        spawn.typeId,
                        spawn.index,
                        spawn.attributes,
                        spawn.group
                    );
                bestHit.spawnSummary = preview.summary;
                bestHit.spawnDetail = preview.detail;
            }
        }
    }

    if (m_outdoorActorPreviewBillboardSet)
    {
        for (size_t actorIndex = 0; actorIndex < m_outdoorActorPreviewBillboardSet->billboards.size(); ++actorIndex)
        {
            const ActorPreviewBillboard &actor = m_outdoorActorPreviewBillboardSet->billboards[actorIndex];
            const float halfExtent = static_cast<float>(std::max<uint16_t>(actor.radius, 64));
            const float height = static_cast<float>(std::max<uint16_t>(actor.height, 128));
            float distance = 0.0f;
            const bx::Vec3 minBounds = {
                static_cast<float>(-actor.x) - halfExtent,
                static_cast<float>(actor.y) - halfExtent,
                static_cast<float>(actor.z)
            };
            const bx::Vec3 maxBounds = {
                static_cast<float>(-actor.x) + halfExtent,
                static_cast<float>(actor.y) + halfExtent,
                static_cast<float>(actor.z) + height
            };

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                && (!bestHit.hasHit || distance < bestHit.distance))
            {
                bestHit.hasHit = true;
                bestHit.kind = "actor";
                bestHit.bModelIndex = actorIndex;
                bestHit.faceIndex = 0;
                bestHit.name = actor.actorName;
                bestHit.distance = distance;
                bestHit.isFriendly = actor.isFriendly;

                if (m_map)
                {
                    const SpawnPreview preview =
                        SpawnPreviewResolver::describe(
                            *m_map,
                            m_monsterTable ? &*m_monsterTable : nullptr,
                            actor.typeId,
                            actor.index,
                            actor.attributes,
                            actor.group
                        );
                    bestHit.spawnSummary = preview.summary;
                    bestHit.spawnDetail = preview.detail;
                }
            }
        }
    }

    if (m_outdoorSpriteObjectBillboardSet)
    {
        for (size_t objectIndex = 0; objectIndex < m_outdoorSpriteObjectBillboardSet->billboards.size(); ++objectIndex)
        {
            const SpriteObjectBillboard &object = m_outdoorSpriteObjectBillboardSet->billboards[objectIndex];
            const float halfExtent = std::max(32.0f, float(std::max(object.radius, int16_t(32))));
            const float height = std::max(64.0f, float(std::max(object.height, int16_t(64))));
            float distance = 0.0f;
            const bx::Vec3 minBounds = {
                float(-object.x) - halfExtent,
                float(object.y) - halfExtent,
                float(object.z)
            };
            const bx::Vec3 maxBounds = {
                float(-object.x) + halfExtent,
                float(object.y) + halfExtent,
                float(object.z) + height
            };

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                && (!bestHit.hasHit || distance < bestHit.distance))
            {
                bestHit.hasHit = true;
                bestHit.kind = "object";
                bestHit.bModelIndex = objectIndex;
                bestHit.name = object.objectName;
                bestHit.distance = distance;
                bestHit.objectDescriptionId = object.objectDescriptionId;
                bestHit.objectSpriteId = object.objectSpriteId;
                bestHit.attributes = object.attributes;
                bestHit.spellId = object.spellId;
            }
        }
    }

    return bestHit;
}

bool TerrainDebugRenderer::tryActivateInspectEvent(const InspectHit &inspectHit)
{
    if (!m_outdoorMapData || !m_eventRuntimeState)
    {
        std::cout << "Outdoor inspect activation ignored: runtime not available\n";
        return false;
    }

    uint16_t eventId = 0;

    if (inspectHit.kind == "entity")
    {
        eventId = inspectHit.eventIdPrimary != 0 ? inspectHit.eventIdPrimary : inspectHit.eventIdSecondary;
    }
    else if (inspectHit.kind == "face")
    {
        eventId = inspectHit.cogTriggeredNumber;
    }
    else
    {
        m_eventRuntimeState->lastActivationResult = "no activatable event on hovered target";
        std::cout << "Outdoor inspect activation ignored: unsupported target kind '"
                  << inspectHit.kind << "'\n";
        return false;
    }

    if (eventId == 0)
    {
        m_eventRuntimeState->lastActivationResult = "no event on hovered target";
        std::cout << "Outdoor inspect activation ignored: target has no event id\n";
        return false;
    }

    std::cout << "Activating outdoor event " << eventId
              << " from " << inspectHit.kind
              << " index=" << inspectHit.bModelIndex << '\n';

    const bool executed = m_eventRuntime.executeEventById(
        m_localEventIrProgram,
        m_globalEventIrProgram,
        eventId,
        *m_eventRuntimeState
    );

    if (!executed)
    {
        m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        std::cout << "Outdoor event " << eventId << " unresolved\n";
        return false;
    }

    if (m_pOutdoorPartyRuntime)
    {
        m_pOutdoorPartyRuntime->applyEventRuntimeState(*m_eventRuntimeState);
    }

    m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    std::cout << "Outdoor event " << eventId << " executed\n";
    return true;
}

void TerrainDebugRenderer::updateCameraFromInput()
{
    const uint64_t currentTickCount = SDL_GetTicksNS();
    float deltaSeconds = 1.0f / 60.0f;

    if (m_lastTickCount != 0 && currentTickCount > m_lastTickCount)
    {
        deltaSeconds = static_cast<float>(currentTickCount - m_lastTickCount) / 1000000000.0f;
    }

    m_lastTickCount = currentTickCount;
    const float displayDeltaSeconds = std::max(deltaSeconds, 0.000001f);
    const float instantaneousFramesPerSecond = 1.0f / displayDeltaSeconds;
    m_framesPerSecond = (m_framesPerSecond == 0.0f)
        ? instantaneousFramesPerSecond
        : (m_framesPerSecond * 0.9f + instantaneousFramesPerSecond * 0.1f);
    deltaSeconds = std::min(deltaSeconds, 0.05f);

    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);

    if (pKeyboardState == nullptr)
    {
        return;
    }

    const bool turboSpeed = pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    const float mouseRotateSpeed = 0.0045f;
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isRightMousePressed = (mouseButtons & SDL_BUTTON_RMASK) != 0;

    if (isRightMousePressed)
    {
        if (m_isRotatingCamera)
        {
            const float deltaMouseX = mouseX - m_lastMouseX;
            const float deltaMouseY = mouseY - m_lastMouseY;
            m_cameraYawRadians -= deltaMouseX * mouseRotateSpeed;
            m_cameraPitchRadians -= deltaMouseY * mouseRotateSpeed;
        }

        m_isRotatingCamera = true;
        m_lastMouseX = mouseX;
        m_lastMouseY = mouseY;
    }
    else
    {
        m_isRotatingCamera = false;
    }

    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    const bx::Vec3 forward = {
        cosYaw,
        -sinYaw,
        0.0f
    };
    const bx::Vec3 right = {
        sinYaw,
        cosYaw,
        0.0f
    };

    if (m_outdoorMapData)
    {
        if (m_pOutdoorPartyRuntime)
        {
            const OutdoorMovementInput movementInput = {
                pKeyboardState[SDL_SCANCODE_W],
                pKeyboardState[SDL_SCANCODE_S],
                pKeyboardState[SDL_SCANCODE_A],
                pKeyboardState[SDL_SCANCODE_D],
                pKeyboardState[SDL_SCANCODE_SPACE],
                pKeyboardState[SDL_SCANCODE_LCTRL] || pKeyboardState[SDL_SCANCODE_RCTRL],
                turboSpeed,
                m_cameraYawRadians
            };
            m_pOutdoorPartyRuntime->update(movementInput, deltaSeconds);
            m_cameraTargetX = m_pOutdoorPartyRuntime->movementState().x;
            m_cameraTargetY = m_pOutdoorPartyRuntime->movementState().y;
            m_cameraTargetZ = m_pOutdoorPartyRuntime->movementState().footZ + m_cameraEyeHeight;
        }
    }
    else
    {
        float moveVelocityX = 0.0f;
        float moveVelocityY = 0.0f;
        const float freeMoveSpeed = turboSpeed ? 4000.0f : 576.0f;

        if (pKeyboardState[SDL_SCANCODE_A])
        {
            moveVelocityX -= right.x * freeMoveSpeed;
            moveVelocityY -= right.y * freeMoveSpeed;
        }

        if (pKeyboardState[SDL_SCANCODE_D])
        {
            moveVelocityX += right.x * freeMoveSpeed;
            moveVelocityY += right.y * freeMoveSpeed;
        }

        if (pKeyboardState[SDL_SCANCODE_W])
        {
            moveVelocityX += forward.x * freeMoveSpeed;
            moveVelocityY += forward.y * freeMoveSpeed;
        }

        if (pKeyboardState[SDL_SCANCODE_S])
        {
            moveVelocityX -= forward.x * freeMoveSpeed;
            moveVelocityY -= forward.y * freeMoveSpeed;
        }

        m_cameraTargetX += moveVelocityX * deltaSeconds;
        m_cameraTargetY += moveVelocityY * deltaSeconds;
    }

    if (pKeyboardState[SDL_SCANCODE_1])
    {
        if (!m_toggleFilledLatch)
        {
            m_showFilledTerrain = !m_showFilledTerrain;
            m_toggleFilledLatch = true;
        }
    }
    else
    {
        m_toggleFilledLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_2])
    {
        if (!m_toggleWireframeLatch)
        {
            m_showTerrainWireframe = !m_showTerrainWireframe;
            m_toggleWireframeLatch = true;
        }
    }
    else
    {
        m_toggleWireframeLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_3])
    {
        if (!m_toggleBModelsLatch)
        {
            m_showBModels = !m_showBModels;
            m_toggleBModelsLatch = true;
        }
    }
    else
    {
        m_toggleBModelsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_4])
    {
        if (!m_toggleBModelWireframeLatch)
        {
            m_showBModelWireframe = !m_showBModelWireframe;
            m_toggleBModelWireframeLatch = true;
        }
    }
    else
    {
        m_toggleBModelWireframeLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_5])
    {
        if (!m_toggleBModelCollisionFacesLatch)
        {
            m_showBModelCollisionFaces = !m_showBModelCollisionFaces;
            m_toggleBModelCollisionFacesLatch = true;
        }
    }
    else
    {
        m_toggleBModelCollisionFacesLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_6])
    {
        if (!m_toggleDecorationBillboardsLatch)
        {
            m_showDecorationBillboards = !m_showDecorationBillboards;
            m_toggleDecorationBillboardsLatch = true;
        }
    }
    else
    {
        m_toggleDecorationBillboardsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_7])
    {
        if (!m_toggleActorsLatch)
        {
            m_showActors = !m_showActors;
            m_toggleActorsLatch = true;
        }
    }
    else
    {
        m_toggleActorsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_8])
    {
        if (!m_toggleSpriteObjectsLatch)
        {
            m_showSpriteObjects = !m_showSpriteObjects;
            m_toggleSpriteObjectsLatch = true;
        }
    }
    else
    {
        m_toggleSpriteObjectsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_9])
    {
        if (!m_toggleEntitiesLatch)
        {
            m_showEntities = !m_showEntities;
            m_toggleEntitiesLatch = true;
        }
    }
    else
    {
        m_toggleEntitiesLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_0])
    {
        if (!m_toggleSpawnsLatch)
        {
            m_showSpawns = !m_showSpawns;
            m_toggleSpawnsLatch = true;
        }
    }
    else
    {
        m_toggleSpawnsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_MINUS])
    {
        if (!m_toggleInspectLatch)
        {
            m_inspectMode = !m_inspectMode;
            m_toggleInspectLatch = true;
        }
    }
    else
    {
        m_toggleInspectLatch = false;
    }

    if (m_pOutdoorPartyRuntime)
    {
        if (pKeyboardState[SDL_SCANCODE_R])
        {
            if (!m_toggleRunningLatch)
            {
                m_pOutdoorPartyRuntime->toggleRunning();
                m_toggleRunningLatch = true;
            }
        }
        else
        {
            m_toggleRunningLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_F])
        {
            if (!m_toggleFlyingLatch)
            {
                m_pOutdoorPartyRuntime->toggleFlying();
                m_toggleFlyingLatch = true;
            }
        }
        else
        {
            m_toggleFlyingLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_T])
        {
            if (!m_toggleWaterWalkLatch)
            {
                m_pOutdoorPartyRuntime->toggleWaterWalk();
                m_toggleWaterWalkLatch = true;
            }
        }
        else
        {
            m_toggleWaterWalkLatch = false;
        }

        if (pKeyboardState[SDL_SCANCODE_G])
        {
            if (!m_toggleFeatherFallLatch)
            {
                m_pOutdoorPartyRuntime->toggleFeatherFall();
                m_toggleFeatherFallLatch = true;
            }
        }
        else
        {
            m_toggleFeatherFallLatch = false;
        }
    }

    if (m_cameraYawRadians > Pi)
    {
        m_cameraYawRadians -= Pi * 2.0f;
    }
    else if (m_cameraYawRadians < -Pi)
    {
        m_cameraYawRadians += Pi * 2.0f;
    }

    m_cameraPitchRadians = std::clamp(m_cameraPitchRadians, -1.55f, 1.55f);
    m_cameraTargetZ = std::clamp(m_cameraTargetZ, -2000.0f, 30000.0f);
    m_cameraOrthoScale = std::clamp(m_cameraOrthoScale, 0.05f, 3.5f);
}

}
