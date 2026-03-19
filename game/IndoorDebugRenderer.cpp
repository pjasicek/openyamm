#include "game/IndoorDebugRenderer.h"

#include "game/SpawnPreview.h"
#include "game/StringUtils.h"

#include <bx/math.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
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
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
template <typename TVertex>
bool updateDynamicVertexBuffer(
    bgfx::DynamicVertexBufferHandle &vertexBufferHandle,
    uint32_t &vertexCapacity,
    const std::vector<TVertex> &vertices,
    const bgfx::VertexLayout &layout
)
{
    if (vertices.empty())
    {
        if (bgfx::isValid(vertexBufferHandle))
        {
            bgfx::destroy(vertexBufferHandle);
            vertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        vertexCapacity = 0;

        return true;
    }

    if (!bgfx::isValid(vertexBufferHandle) || vertexCapacity != vertices.size())
    {
        if (bgfx::isValid(vertexBufferHandle))
        {
            bgfx::destroy(vertexBufferHandle);
        }

        vertexBufferHandle = bgfx::createDynamicVertexBuffer(
            static_cast<uint32_t>(vertices.size()),
            layout
        );
        vertexCapacity = static_cast<uint32_t>(vertices.size());
    }

    if (!bgfx::isValid(vertexBufferHandle))
    {
        return false;
    }

    bgfx::update(
        vertexBufferHandle,
        0,
        bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(TVertex)))
    );
    return true;
}

constexpr uint16_t MainViewId = 0;
constexpr float Pi = 3.14159265358979323846f;
constexpr float InspectRayEpsilon = 0.0001f;

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

bx::Vec3 vecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
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

bx::Vec3 vecNormalize(const bx::Vec3 &vector)
{
    const float vectorLength = vecLength(vector);

    if (vectorLength <= InspectRayEpsilon)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {vector.x / vectorLength, vector.y / vectorLength, vector.z / vectorLength};
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

std::string resolveFaceTextureName(
    const IndoorFace &face,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    if (!eventRuntimeState)
    {
        return face.textureName;
    }

    const uint32_t cogCandidates[2] = {face.cogNumber, face.textureFrameTableCog};

    for (uint32_t cogCandidate : cogCandidates)
    {
        if (cogCandidate == 0)
        {
            continue;
        }

        const std::unordered_map<uint32_t, std::string>::const_iterator iterator =
            eventRuntimeState->textureOverrides.find(cogCandidate);

        if (iterator != eventRuntimeState->textureOverrides.end() && !iterator->second.empty())
        {
            return iterator->second;
        }
    }

    return face.textureName;
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    const uint8_t alpha = 255;

    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

float fixedDoorDirectionComponentToFloat(int value)
{
    return static_cast<float>(value) / 65536.0f;
}

bool solve2x2(
    float a00,
    float a01,
    float a10,
    float a11,
    float b0,
    float b1,
    float &x0,
    float &x1
)
{
    const float determinant = a00 * a11 - a01 * a10;

    if (std::fabs(determinant) <= InspectRayEpsilon)
    {
        return false;
    }

    const float inverseDeterminant = 1.0f / determinant;
    x0 = (b0 * a11 - b1 * a01) * inverseDeterminant;
    x1 = (a00 * b1 - a10 * b0) * inverseDeterminant;
    return true;
}

bool computeFaceTextureBasis(
    const IndoorMapData &indoorMapData,
    const IndoorFace &face,
    bx::Vec3 &uAxis,
    bx::Vec3 &vAxis,
    float &uBase,
    float &vBase
)
{
    uAxis = {0.0f, 0.0f, 0.0f};
    vAxis = {0.0f, 0.0f, 0.0f};
    uBase = 0.0f;
    vBase = 0.0f;

    if (face.vertexIndices.size() < 3
        || face.textureUs.size() < 3
        || face.textureVs.size() < 3)
    {
        return false;
    }

    const uint16_t vertexId0 = face.vertexIndices[0];
    const uint16_t vertexId1 = face.vertexIndices[1];
    const uint16_t vertexId2 = face.vertexIndices[2];

    if (vertexId0 >= indoorMapData.vertices.size()
        || vertexId1 >= indoorMapData.vertices.size()
        || vertexId2 >= indoorMapData.vertices.size()
        || vertexId2 >= indoorMapData.vertices.size())
    {
        return false;
    }

    const IndoorVertex &original0 = indoorMapData.vertices[vertexId0];
    const IndoorVertex &original1 = indoorMapData.vertices[vertexId1];
    const IndoorVertex &original2 = indoorMapData.vertices[vertexId2];

    const bx::Vec3 p0 = {float(original0.x), float(original0.y), float(original0.z)};
    const bx::Vec3 p1 = {float(original1.x), float(original1.y), float(original1.z)};
    const bx::Vec3 p2 = {float(original2.x), float(original2.y), float(original2.z)};
    const bx::Vec3 e1 = vecSubtract(p1, p0);
    const bx::Vec3 e2 = vecSubtract(p2, p0);

    const float g00 = vecDot(e1, e1);
    const float g01 = vecDot(e1, e2);
    const float g10 = g01;
    const float g11 = vecDot(e2, e2);

    float c0 = 0.0f;
    float c1 = 0.0f;
    const float du1 = static_cast<float>(face.textureUs[1] - face.textureUs[0]);
    const float du2 = static_cast<float>(face.textureUs[2] - face.textureUs[0]);

    if (!solve2x2(g00, g01, g10, g11, du1, du2, c0, c1))
    {
        return false;
    }

    uAxis = {
        c0 * e1.x + c1 * e2.x,
        c0 * e1.y + c1 * e2.y,
        c0 * e1.z + c1 * e2.z
    };

    const float dv1 = static_cast<float>(face.textureVs[1] - face.textureVs[0]);
    const float dv2 = static_cast<float>(face.textureVs[2] - face.textureVs[0]);

    if (!solve2x2(g00, g01, g10, g11, dv1, dv2, c0, c1))
    {
        return false;
    }

    vAxis = {
        c0 * e1.x + c1 * e2.x,
        c0 * e1.y + c1 * e2.y,
        c0 * e1.z + c1 * e2.z
    };

    uBase = static_cast<float>(face.textureUs[0]) - vecDot(p0, uAxis);
    vBase = static_cast<float>(face.textureVs[0]) - vecDot(p0, vAxis);
    return true;
}

bool faceHasInvisibleOverride(
    size_t faceIndex,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    if (!eventRuntimeState)
    {
        return false;
    }

    const uint32_t faceId = static_cast<uint32_t>(faceIndex);
    uint32_t invisibleMask = 0;
    const std::unordered_map<uint32_t, uint32_t>::const_iterator setIterator =
        eventRuntimeState->facetSetMasks.find(faceId);

    if (setIterator != eventRuntimeState->facetSetMasks.end())
    {
        invisibleMask |= setIterator->second;
    }

    const std::unordered_map<uint32_t, uint32_t>::const_iterator clearIterator =
        eventRuntimeState->facetClearMasks.find(faceId);

    if (clearIterator != eventRuntimeState->facetClearMasks.end())
    {
        invisibleMask &= ~clearIterator->second;
    }

    return (invisibleMask & 0x00002000u) != 0;
}
}

bgfx::VertexLayout IndoorDebugRenderer::TerrainVertex::ms_layout;
bgfx::VertexLayout IndoorDebugRenderer::TexturedVertex::ms_layout;

IndoorDebugRenderer::IndoorDebugRenderer()
    : m_isInitialized(false)
    , m_isRenderable(false)
    , m_indoorMapData(std::nullopt)
    , m_indoorMapDeltaData(std::nullopt)
    , m_wireframeVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_portalVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_entityMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_spawnMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_doorMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_programHandle(BGFX_INVALID_HANDLE)
    , m_texturedProgramHandle(BGFX_INVALID_HANDLE)
    , m_textureSamplerHandle(BGFX_INVALID_HANDLE)
    , m_framesPerSecond(0.0f)
    , m_wireframeVertexCount(0)
    , m_wireframeVertexCapacity(0)
    , m_portalVertexCount(0)
    , m_portalVertexCapacity(0)
    , m_faceCount(0)
    , m_entityMarkerVertexCount(0)
    , m_spawnMarkerVertexCount(0)
    , m_doorMarkerVertexCount(0)
    , m_doorMarkerVertexCapacity(0)
    , m_cameraPositionX(0.0f)
    , m_cameraPositionY(0.0f)
    , m_cameraPositionZ(256.0f)
    , m_cameraYawRadians(0.0f)
    , m_cameraPitchRadians(0.15f)
    , m_mechanismAccumulatorMilliseconds(0.0f)
    , m_showFilled(true)
    , m_showWireframe(false)
    , m_showPortals(false)
    , m_showDecorationBillboards(true)
    , m_showActors(true)
    , m_showSpriteObjects(true)
    , m_isRotatingCamera(false)
    , m_lastMouseX(0.0f)
    , m_lastMouseY(0.0f)
    , m_toggleFilledLatch(false)
    , m_toggleWireframeLatch(false)
    , m_togglePortalsLatch(false)
    , m_toggleDecorationBillboardsLatch(false)
    , m_toggleActorsLatch(false)
    , m_toggleSpriteObjectsLatch(false)
    , m_showEntities(true)
    , m_showSpawns(true)
    , m_showDoors(true)
    , m_inspectMode(false)
    , m_toggleEntitiesLatch(false)
    , m_toggleSpawnsLatch(false)
    , m_toggleDoorsLatch(false)
    , m_toggleInspectLatch(false)
    , m_activateInspectLatch(false)
{
}

IndoorDebugRenderer::~IndoorDebugRenderer()
{
    shutdown();
}

bool IndoorDebugRenderer::initialize(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const IndoorMapData &indoorMapData,
    const std::optional<MapDeltaData> &indoorMapDeltaData,
    const std::optional<IndoorTextureSet> &indoorTextureSet,
    const std::optional<DecorationBillboardSet> &indoorDecorationBillboardSet,
    const std::optional<ActorPreviewBillboardSet> &indoorActorPreviewBillboardSet,
    const std::optional<SpriteObjectBillboardSet> &indoorSpriteObjectBillboardSet,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    const ChestTable &chestTable,
    const HouseTable &houseTable,
    const std::optional<StrTable> &localStrTable,
    const std::optional<EvtProgram> &localEvtProgram,
    const std::optional<EvtProgram> &globalEvtProgram,
    const std::optional<EventIrProgram> &localEventIrProgram,
    const std::optional<EventIrProgram> &globalEventIrProgram
)
{
    shutdown();
    m_isInitialized = true;
    m_map = map;
    m_monsterTable = monsterTable;
    m_indoorMapData = indoorMapData;
    m_renderVertices = buildMechanismAdjustedVertices(indoorMapData, indoorMapDeltaData, eventRuntimeState);
    m_indoorMapDeltaData = indoorMapDeltaData;
    m_indoorTextureSet = indoorTextureSet;
    m_eventRuntimeState = eventRuntimeState;
    m_indoorDecorationBillboardSet = indoorDecorationBillboardSet;
    m_indoorActorPreviewBillboardSet = indoorActorPreviewBillboardSet;
    m_indoorSpriteObjectBillboardSet = indoorSpriteObjectBillboardSet;
    m_chestTable = chestTable;
    m_houseTable = houseTable;
    m_localStrTable = localStrTable;
    m_localEvtProgram = localEvtProgram;
    m_globalEvtProgram = globalEvtProgram;
    m_localEventIrProgram = localEventIrProgram;
    m_globalEventIrProgram = globalEventIrProgram;
    rebuildMechanismBindings();

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return true;
    }

    TerrainVertex::init();
    TexturedVertex::init();

    const std::vector<TerrainVertex> entityMarkerVertices = buildEntityMarkerVertices(indoorMapData);
    const std::vector<TerrainVertex> spawnMarkerVertices = buildSpawnMarkerVertices(indoorMapData);

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

    if (indoorDecorationBillboardSet)
    {
        for (const OutdoorBitmapTexture &texture : indoorDecorationBillboardSet->textures)
        {
            BillboardTextureHandle billboardTexture = {};
            billboardTexture.textureName = toLowerCopy(texture.textureName);
            billboardTexture.paletteId = texture.paletteId;
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

    if (indoorActorPreviewBillboardSet)
    {
        for (const OutdoorBitmapTexture &texture : indoorActorPreviewBillboardSet->textures)
        {
            if (findBillboardTexture(texture.textureName, texture.paletteId) != nullptr)
            {
                continue;
            }

            BillboardTextureHandle billboardTexture = {};
            billboardTexture.textureName = toLowerCopy(texture.textureName);
            billboardTexture.paletteId = texture.paletteId;
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

    if (indoorSpriteObjectBillboardSet)
    {
        for (const OutdoorBitmapTexture &texture : indoorSpriteObjectBillboardSet->textures)
        {
            if (findBillboardTexture(texture.textureName, texture.paletteId) != nullptr)
            {
                continue;
            }

            BillboardTextureHandle billboardTexture = {};
            billboardTexture.textureName = toLowerCopy(texture.textureName);
            billboardTexture.paletteId = texture.paletteId;
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

    m_faceCount = static_cast<uint32_t>(indoorMapData.faces.size());
    m_programHandle = loadProgram("vs_cubes", "fs_cubes");
    m_texturedProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_shadowmaps_texture");
    m_textureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);

    if (!bgfx::isValid(m_programHandle))
    {
        shutdown();
        return false;
    }

    if (!rebuildDerivedGeometryResources())
    {
        shutdown();
        return false;
    }

    if (!indoorMapData.vertices.empty())
    {
        int minX = indoorMapData.vertices.front().x;
        int maxX = indoorMapData.vertices.front().x;
        int minY = indoorMapData.vertices.front().y;
        int maxY = indoorMapData.vertices.front().y;
        int minZ = indoorMapData.vertices.front().z;
        int maxZ = indoorMapData.vertices.front().z;

        for (const IndoorVertex &vertex : indoorMapData.vertices)
        {
            minX = std::min(minX, vertex.x);
            maxX = std::max(maxX, vertex.x);
            minY = std::min(minY, vertex.y);
            maxY = std::max(maxY, vertex.y);
            minZ = std::min(minZ, vertex.z);
            maxZ = std::max(maxZ, vertex.z);
        }

        m_cameraPositionX = static_cast<float>((minX + maxX) / 2);
        m_cameraPositionY = static_cast<float>(minY - 256);
        m_cameraPositionZ = static_cast<float>((minZ + maxZ) / 2);
    }

    m_isRenderable = true;
    return true;
}

bool IndoorDebugRenderer::isFaceVisible(
    size_t faceIndex,
    const IndoorFace &face,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    if ((face.attributes & 0x00002000u) != 0)
    {
        return false;
    }

    return !faceHasInvisibleOverride(faceIndex, eventRuntimeState);
}

void IndoorDebugRenderer::render(int width, int height, float mouseWheelDelta, float deltaSeconds)
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
        return;
    }

    const float deltaMilliseconds = deltaSeconds * 1000.0f;
    updateCameraFromInput(deltaSeconds);

    if (m_eventRuntimeState && m_indoorMapDeltaData && deltaMilliseconds > 0.0f)
    {
        bool hadMovingMechanism = false;

        for (const auto &entry : m_eventRuntimeState->mechanisms)
        {
            if (entry.second.isMoving)
            {
                hadMovingMechanism = true;
                break;
            }
        }

        int mechanismSteps = 0;
        constexpr float MechanismStepMilliseconds = 1000.0f / 120.0f;
        constexpr int MaximumMechanismStepsPerFrame = 8;

        if (hadMovingMechanism)
        {
            m_mechanismAccumulatorMilliseconds += deltaMilliseconds;

            while (
                m_mechanismAccumulatorMilliseconds >= MechanismStepMilliseconds
                && mechanismSteps < MaximumMechanismStepsPerFrame
            )
            {
                m_eventRuntime.advanceMechanisms(m_indoorMapDeltaData, MechanismStepMilliseconds, *m_eventRuntimeState);
                m_mechanismAccumulatorMilliseconds -= MechanismStepMilliseconds;
                ++mechanismSteps;
            }

            if (
                mechanismSteps == MaximumMechanismStepsPerFrame
                && m_mechanismAccumulatorMilliseconds > MechanismStepMilliseconds
            )
            {
                m_mechanismAccumulatorMilliseconds = MechanismStepMilliseconds;
            }
        }
        else
        {
            m_mechanismAccumulatorMilliseconds = 0.0f;
        }

        bool hasMovingMechanism = false;

        for (const auto &entry : m_eventRuntimeState->mechanisms)
        {
            if (entry.second.isMoving)
            {
                hasMovingMechanism = true;
            }
        }

        if (hasMovingMechanism)
        {
            if (mechanismSteps > 0)
            {
                rebuildDerivedGeometryResources();
            }
        }
    }

    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);

    if (mouseWheelDelta != 0.0f)
    {
        const bx::Vec3 forward = {cosYaw * cosPitch, -sinYaw * cosPitch, sinPitch};
        const float wheelMoveSpeed = 300.0f;
        m_cameraPositionX += forward.x * mouseWheelDelta * wheelMoveSpeed;
        m_cameraPositionY += forward.y * mouseWheelDelta * wheelMoveSpeed;
        m_cameraPositionZ += forward.z * mouseWheelDelta * wheelMoveSpeed;
    }

    const bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
    const bx::Vec3 at = {
        m_cameraPositionX + cosYaw * cosPitch,
        m_cameraPositionY - sinYaw * cosPitch,
        m_cameraPositionZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};

    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up);
    bx::mtxProj(
        projectionMatrix,
        60.0f,
        static_cast<float>(viewWidth) / static_cast<float>(viewHeight),
        0.1f,
        50000.0f,
        bgfx::getCaps()->homogeneousDepth
    );

    bgfx::setViewTransform(MainViewId, viewMatrix, projectionMatrix);
    bgfx::touch(MainViewId);

    InspectHit inspectHit = {};
    float mouseX = 0.0f;
    float mouseY = 0.0f;

    if (m_inspectMode && m_indoorMapData)
    {
        SDL_GetMouseState(&mouseX, &mouseY);
        const float normalizedMouseX = ((mouseX / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
        const float normalizedMouseY = 1.0f - ((mouseY / static_cast<float>(viewHeight)) * 2.0f);
        float viewProjectionMatrix[16] = {};
        float inverseViewProjectionMatrix[16] = {};
        bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);
        bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);
        const bx::Vec3 rayOrigin = bx::mulH({normalizedMouseX, normalizedMouseY, 0.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayTarget = bx::mulH({normalizedMouseX, normalizedMouseY, 1.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayDirection = vecNormalize(vecSubtract(rayTarget, rayOrigin));
        inspectHit = inspectAtCursor(*m_indoorMapData, m_renderVertices, rayOrigin, rayDirection);

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
                inspectHit = inspectAtCursor(*m_indoorMapData, m_renderVertices, rayOrigin, rayDirection);
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

    if (m_showFilled && bgfx::isValid(m_texturedProgramHandle) && bgfx::isValid(m_textureSamplerHandle))
    {
        for (const TexturedBatch &batch : m_texturedBatches)
        {
            if (!bgfx::isValid(batch.vertexBufferHandle) || !bgfx::isValid(batch.textureHandle) || batch.vertexCount == 0)
            {
                continue;
            }

            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, batch.vertexBufferHandle, 0, batch.vertexCount);
            bgfx::setTexture(0, m_textureSamplerHandle, batch.textureHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_BLEND_ALPHA
            );
            bgfx::submit(MainViewId, m_texturedProgramHandle);
        }
    }

    if (m_showDecorationBillboards)
    {
        renderDecorationBillboards(MainViewId, viewMatrix, eye);
    }

    if (m_showWireframe && bgfx::isValid(m_wireframeVertexBufferHandle) && m_wireframeVertexCount > 0)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, m_wireframeVertexBufferHandle, 0, m_wireframeVertexCount);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LESS
            | BGFX_STATE_PT_LINES
        );
        bgfx::submit(MainViewId, m_programHandle);
    }

    if (m_showPortals && bgfx::isValid(m_portalVertexBufferHandle) && m_portalVertexCount > 0)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, m_portalVertexBufferHandle, 0, m_portalVertexCount);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_PT_LINES
        );
        bgfx::submit(MainViewId, m_programHandle);
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
        renderActorPreviewBillboards(MainViewId, viewMatrix, eye);
    }

    if (m_showSpriteObjects)
    {
        renderSpriteObjectBillboards(MainViewId, viewMatrix, eye);
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

    if (m_showDoors && bgfx::isValid(m_doorMarkerVertexBufferHandle) && m_doorMarkerVertexCount > 0)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, m_doorMarkerVertexBufferHandle, 0, m_doorMarkerVertexCount);
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
    bgfx::dbgTextPrintf(0, 1, 0x0f, "Indoor debug renderer");
    bgfx::dbgTextPrintf(0, 2, 0x0f, "FPS: %.1f", m_framesPerSecond);
    bgfx::dbgTextPrintf(0, 3, 0x0f, "Faces: %u", m_faceCount);
    bgfx::dbgTextPrintf(
        0,
        4,
        0x0f,
        "Modes: 1 filled=%s  2 wire=%s  3 portals=%s  4 sprites=%s  5 actors=%s  6 objs=%s  7 ents=%s  8 spawns=%s  9 mechs=%s  0 inspect=%s textured=%s",
        m_showFilled ? "on" : "off",
        m_showWireframe ? "on" : "off",
        m_showPortals ? "on" : "off",
        m_showDecorationBillboards ? "on" : "off",
        m_showActors ? "on" : "off",
        m_showSpriteObjects ? "on" : "off",
        m_showEntities ? "on" : "off",
        m_showSpawns ? "on" : "off",
        m_showDoors ? "on" : "off",
        m_inspectMode ? "on" : "off",
        m_texturedBatches.empty() ? "no" : "yes"
    );
    bgfx::dbgTextPrintf(0, 5, 0x0f, "Move: WASD  Rotate: RMB drag");
    bgfx::dbgTextPrintf(
        0,
        6,
        0x0f,
        "Position: %.0f %.0f %.0f  sprites=%u ents=%u spawns=%u mechs=%u",
        m_cameraPositionX,
        m_cameraPositionY,
        m_cameraPositionZ,
        m_indoorDecorationBillboardSet ? static_cast<unsigned>(m_indoorDecorationBillboardSet->billboards.size()) : 0u,
        m_indoorMapData ? static_cast<unsigned>(m_indoorMapData->entities.size()) : 0u,
        m_indoorMapData ? static_cast<unsigned>(m_indoorMapData->spawns.size()) : 0u,
        m_indoorMapDeltaData ? static_cast<unsigned>(m_indoorMapDeltaData->doors.size()) : 0u
    );
    if (m_inspectMode)
    {
        bgfx::dbgTextPrintf(0, 8, 0x0f, "Activate: LeftClick/E");

        if (inspectHit.hasHit)
        {
            bgfx::dbgTextPrintf(
                0,
                7,
                0x0f,
                "Inspect: %s=%u dist=%.0f tex=%s name=%s",
                inspectHit.kind.c_str(),
                static_cast<unsigned>(inspectHit.index),
                inspectHit.distance,
                inspectHit.textureName.empty() ? "-" : inspectHit.textureName.c_str(),
                inspectHit.name.empty() ? "-" : inspectHit.name.c_str()
            );

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
                    m_indoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string secondaryChestSummary = summarizeLinkedChests(
                    inspectHit.eventIdSecondary,
                    m_indoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                bgfx::dbgTextPrintf(
                    0,
                    8,
                    0x0f,
                    "Entity: dec=%u evt=%u/%u var=%u/%u trig=%u",
                    inspectHit.decorationListId,
                    inspectHit.eventIdPrimary,
                    inspectHit.eventIdSecondary,
                    inspectHit.variablePrimary,
                    inspectHit.variableSecondary,
                    inspectHit.specialTrigger
                );
                bgfx::dbgTextPrintf(0, 9, 0x0f, "Script: P %s | S %s", primaryEventSummary.c_str(), secondaryEventSummary.c_str());
                if (!primaryChestSummary.empty() || !secondaryChestSummary.empty())
                {
                    bgfx::dbgTextPrintf(
                        0,
                        10,
                        0x0f,
                        "Chest: P %s | S %s",
                        primaryChestSummary.empty() ? "-" : primaryChestSummary.c_str(),
                        secondaryChestSummary.empty() ? "-" : secondaryChestSummary.c_str()
                    );
                }
            }
            else if (inspectHit.kind == "face")
            {
                const std::string faceEventSummary = summarizeLinkedEvent(
                    inspectHit.cogTriggered,
                    m_houseTable,
                    m_localStrTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                const std::string faceChestSummary = summarizeLinkedChests(
                    inspectHit.cogTriggered,
                    m_indoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                bgfx::dbgTextPrintf(
                    0,
                    8,
                    0x0f,
                    "Face: attr=0x%08x portal=%s room=%u behind=%u type=%u",
                    inspectHit.attributes,
                    inspectHit.isPortal ? "yes" : "no",
                    inspectHit.roomNumber,
                    inspectHit.roomBehindNumber,
                    static_cast<unsigned>(inspectHit.facetType)
                );
                bgfx::dbgTextPrintf(
                    0,
                    9,
                    0x0f,
                    "FaceEvt: cog=%u evt=%u trigType=%u",
                    inspectHit.cogNumber,
                    inspectHit.cogTriggered,
                    inspectHit.cogTriggerType
                );
                bgfx::dbgTextPrintf(0, 10, 0x0f, "Script: %s", faceEventSummary.c_str());
                if (!faceChestSummary.empty())
                {
                    bgfx::dbgTextPrintf(0, 11, 0x0f, "%s", faceChestSummary.c_str());
                }
            }
            else if (inspectHit.kind == "actor")
            {
                bgfx::dbgTextPrintf(
                    0,
                    8,
                    0x0f,
                    "Actor: %s %s",
                    inspectHit.name.empty() ? "-" : inspectHit.name.c_str(),
                    inspectHit.isFriendly ? "[friendly]" : "[hostile]"
                );
                bgfx::dbgTextPrintf(0, 9, 0x0f, "%s", inspectHit.spawnSummary.empty() ? "-" : inspectHit.spawnSummary.c_str());
                bgfx::dbgTextPrintf(0, 10, 0x0f, "%s", inspectHit.spawnDetail.empty() ? "-" : inspectHit.spawnDetail.c_str());
            }
            else if (inspectHit.kind == "object")
            {
                bgfx::dbgTextPrintf(
                    0,
                    8,
                    0x0f,
                    "Object: desc=%u sprite=%u attr=0x%04x spell=%d",
                    inspectHit.objectDescriptionId,
                    inspectHit.objectSpriteId,
                    inspectHit.attributes,
                    inspectHit.spellId
                );
                bgfx::dbgTextPrintf(0, 9, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
            }
            else if (inspectHit.kind == "mechanism")
            {
                const std::string mechanismChestSummary = summarizeLinkedChests(
                    inspectHit.mechanismLinkedEventId,
                    m_indoorMapDeltaData,
                    m_chestTable,
                    m_localEvtProgram,
                    m_globalEvtProgram
                );
                bgfx::dbgTextPrintf(
                    0,
                    8,
                    0x0f,
                    "Mechanism: id=%u state=%u attr=0x%08x",
                    inspectHit.doorId,
                    inspectHit.doorState,
                    inspectHit.doorAttributes
                );
                bgfx::dbgTextPrintf(
                    0,
                    9,
                    0x0f,
                    "%s",
                    inspectHit.mechanismFaceSummary.empty() ? "faces: -" : inspectHit.mechanismFaceSummary.c_str()
                );
                bgfx::dbgTextPrintf(
                    0,
                    10,
                    0x0f,
                    "%s",
                    inspectHit.mechanismLinkedEventSummary.empty()
                        ? "linked face evts: none"
                        : inspectHit.mechanismLinkedEventSummary.c_str()
                );
                if (!mechanismChestSummary.empty())
                {
                    bgfx::dbgTextPrintf(0, 11, 0x0f, "%s", mechanismChestSummary.c_str());
                    bgfx::dbgTextPrintf(0, 12, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
                }
                else
                {
                    bgfx::dbgTextPrintf(0, 11, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
                }
            }
            else
            {
                bgfx::dbgTextPrintf(0, 8, 0x0f, "%s", inspectHit.spawnSummary.empty() ? "-" : inspectHit.spawnSummary.c_str());
                bgfx::dbgTextPrintf(0, 9, 0x0f, "%s", inspectHit.spawnDetail.empty() ? "-" : inspectHit.spawnDetail.c_str());
                bgfx::dbgTextPrintf(0, 10, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);
            }

            if (m_eventRuntimeState && m_eventRuntimeState->lastActivationResult)
            {
                const uint16_t activationLine = inspectHit.kind == "mechanism" ? 13 : 12;
                bgfx::dbgTextPrintf(0, activationLine, 0x0f, "Activate: %s", m_eventRuntimeState->lastActivationResult->c_str());

                if (!m_eventRuntimeState->lastAffectedMechanismIds.empty())
                {
                    std::string mechanismsLine = "Affected mechs:";

                    for (uint32_t mechanismId : m_eventRuntimeState->lastAffectedMechanismIds)
                    {
                        mechanismsLine += " " + std::to_string(mechanismId);
                    }

                    bgfx::dbgTextPrintf(0, activationLine + 1, 0x0f, "%s", mechanismsLine.c_str());
                }
            }
        }
        else
        {
            bgfx::dbgTextPrintf(0, 7, 0x0f, "Inspect: no face/entity/spawn/mechanism under cursor");
            bgfx::dbgTextPrintf(0, 8, 0x0f, "Cursor: %.0f %.0f", mouseX, mouseY);

            if (m_eventRuntimeState && m_eventRuntimeState->lastActivationResult)
            {
                bgfx::dbgTextPrintf(0, 9, 0x0f, "Activate: %s", m_eventRuntimeState->lastActivationResult->c_str());

                if (!m_eventRuntimeState->lastAffectedMechanismIds.empty())
                {
                    std::string mechanismsLine = "Affected mechs:";

                    for (uint32_t mechanismId : m_eventRuntimeState->lastAffectedMechanismIds)
                    {
                        mechanismsLine += " " + std::to_string(mechanismId);
                    }

                    bgfx::dbgTextPrintf(0, 10, 0x0f, "%s", mechanismsLine.c_str());
                }
            }
        }
    }
}

void IndoorDebugRenderer::shutdown()
{
    m_indoorMapData.reset();
    m_renderVertices.clear();
    m_indoorMapDeltaData.reset();
    m_indoorTextureSet.reset();
    m_eventRuntimeState.reset();
    m_map.reset();
    m_monsterTable.reset();
    m_indoorDecorationBillboardSet.reset();
    m_indoorActorPreviewBillboardSet.reset();
    m_indoorSpriteObjectBillboardSet.reset();
    m_houseTable.reset();
    m_localStrTable.reset();
    m_localEvtProgram.reset();
    m_globalEvtProgram.reset();
    m_localEventIrProgram.reset();
    m_globalEventIrProgram.reset();
    m_mechanismAccumulatorMilliseconds = 0.0f;
    m_mechanismBindings.clear();

    if (bgfx::isValid(m_programHandle))
    {
        bgfx::destroy(m_programHandle);
        m_programHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_texturedProgramHandle))
    {
        bgfx::destroy(m_texturedProgramHandle);
        m_texturedProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_entityMarkerVertexBufferHandle))
    {
        bgfx::destroy(m_entityMarkerVertexBufferHandle);
        m_entityMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_portalVertexBufferHandle))
    {
        bgfx::destroy(m_portalVertexBufferHandle);
        m_portalVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_spawnMarkerVertexBufferHandle))
    {
        bgfx::destroy(m_spawnMarkerVertexBufferHandle);
        m_spawnMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_doorMarkerVertexBufferHandle))
    {
        bgfx::destroy(m_doorMarkerVertexBufferHandle);
        m_doorMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_textureSamplerHandle))
    {
        bgfx::destroy(m_textureSamplerHandle);
        m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    }

    destroyDerivedGeometryResources();
    destroyIndoorTextureHandles();

    for (BillboardTextureHandle &textureHandle : m_billboardTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
        }
    }

    m_billboardTextureHandles.clear();

    if (bgfx::isValid(m_wireframeVertexBufferHandle))
    {
        bgfx::destroy(m_wireframeVertexBufferHandle);
        m_wireframeVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    m_framesPerSecond = 0.0f;
    m_wireframeVertexCount = 0;
    m_wireframeVertexCapacity = 0;
    m_portalVertexCount = 0;
    m_portalVertexCapacity = 0;
    m_faceCount = 0;
    m_entityMarkerVertexCount = 0;
    m_spawnMarkerVertexCount = 0;
    m_doorMarkerVertexCount = 0;
    m_doorMarkerVertexCapacity = 0;
    m_isRotatingCamera = false;
    m_lastMouseX = 0.0f;
    m_lastMouseY = 0.0f;
    m_toggleFilledLatch = false;
    m_toggleWireframeLatch = false;
    m_togglePortalsLatch = false;
    m_toggleDecorationBillboardsLatch = false;
    m_toggleActorsLatch = false;
    m_toggleSpriteObjectsLatch = false;
    m_toggleEntitiesLatch = false;
    m_toggleSpawnsLatch = false;
    m_toggleDoorsLatch = false;
    m_toggleInspectLatch = false;
    m_isRenderable = false;
    m_isInitialized = false;
}

void IndoorDebugRenderer::TerrainVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

void IndoorDebugRenderer::TexturedVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
}

bgfx::ProgramHandle IndoorDebugRenderer::loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadShader(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadShader(pFragmentShaderName);

    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

bgfx::ShaderHandle IndoorDebugRenderer::loadShader(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createShader(bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size())));
}

const IndoorDebugRenderer::BillboardTextureHandle *IndoorDebugRenderer::findBillboardTexture(
    const std::string &textureName,
    int16_t paletteId
) const
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const BillboardTextureHandle &textureHandle : m_billboardTextureHandles)
    {
        if (textureHandle.textureName == normalizedTextureName && textureHandle.paletteId == paletteId)
        {
            return &textureHandle;
        }
    }

    return nullptr;
}

void IndoorDebugRenderer::renderDecorationBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition
)
{
    if (!m_indoorDecorationBillboardSet
        || !bgfx::isValid(m_texturedProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle))
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
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
    drawItems.reserve(m_indoorDecorationBillboardSet->billboards.size());

    for (const DecorationBillboard &billboard : m_indoorDecorationBillboardSet->billboards)
    {
        if (billboard.spriteId == 0)
        {
            continue;
        }

        const uint32_t animationOffsetTicks =
            animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
        const SpriteFrameEntry *pFrame =
            m_indoorDecorationBillboardSet->spriteFrameTable.getFrame(billboard.spriteId, animationOffsetTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
        const float angleToCamera = std::atan2(
            static_cast<float>(billboard.y) - cameraPosition.y,
            static_cast<float>(billboard.x) - cameraPosition.x
        );
        const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
        const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
        const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle) || pTexture->width <= 0 || pTexture->height <= 0)
        {
            continue;
        }

        const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
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
        constexpr float BillboardDepthBias = 128.0f;
        const DecorationBillboard &billboard = *drawItem.pBillboard;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const float centerOffset = worldHeight * 0.5f;
        const bx::Vec3 toCamera = vecNormalize({
            cameraPosition.x - static_cast<float>(billboard.x),
            cameraPosition.y - static_cast<float>(billboard.y),
            cameraPosition.z - (static_cast<float>(billboard.z) + centerOffset)
        });
        const bx::Vec3 center = {
            static_cast<float>(billboard.x) + toCamera.x * BillboardDepthBias,
            static_cast<float>(billboard.y) + toCamera.y * BillboardDepthBias,
            static_cast<float>(billboard.z) + centerOffset + toCamera.z * BillboardDepthBias
        };
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {cameraUp.x * worldHeight * 0.5f, cameraUp.y * worldHeight * 0.5f, cameraUp.z * worldHeight * 0.5f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        std::array<TexturedVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), TexturedVertex::ms_layout)
            < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            TexturedVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, m_textureSamplerHandle, texture.textureHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(viewId, m_texturedProgramHandle);
    }
}

void IndoorDebugRenderer::renderActorPreviewBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition
)
{
    if (!m_indoorActorPreviewBillboardSet
        || !bgfx::isValid(m_texturedProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle))
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
    drawItems.reserve(m_indoorActorPreviewBillboardSet->billboards.size());

    for (const ActorPreviewBillboard &billboard : m_indoorActorPreviewBillboardSet->billboards)
    {
        const uint32_t frameTimeTicks = billboard.useStaticFrame ? 0U : animationTimeTicks;
        const SpriteFrameEntry *pFrame =
            m_indoorActorPreviewBillboardSet->spriteFrameTable.getFrame(billboard.spriteFrameIndex, frameTimeTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const float angleToCamera = std::atan2(
            static_cast<float>(billboard.y) - cameraPosition.y,
            static_cast<float>(billboard.x) - cameraPosition.x
        );
        const float octantAngle = -angleToCamera + Pi + (Pi / 8.0f);
        const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
        const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
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
        const ActorPreviewBillboard &billboard = *drawItem.pBillboard;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            static_cast<float>(billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z) + worldHeight * 0.5f
        };
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {cameraUp.x * worldHeight * 0.5f, cameraUp.y * worldHeight * 0.5f, cameraUp.z * worldHeight * 0.5f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        std::array<TexturedVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), TexturedVertex::ms_layout)
            < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            TexturedVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, m_textureSamplerHandle, texture.textureHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(viewId, m_texturedProgramHandle);
    }
}

void IndoorDebugRenderer::renderSpriteObjectBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition
)
{
    if (!m_indoorSpriteObjectBillboardSet
        || !bgfx::isValid(m_texturedProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle))
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
    drawItems.reserve(m_indoorSpriteObjectBillboardSet->billboards.size());

    for (const SpriteObjectBillboard &billboard : m_indoorSpriteObjectBillboardSet->billboards)
    {
        const SpriteFrameEntry *pFrame =
            m_indoorSpriteObjectBillboardSet->spriteFrameTable.getFrame(
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

        const float deltaX = float(billboard.x) - cameraPosition.x;
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
            float(billboard.x),
            float(billboard.y),
            float(billboard.z) + worldHeight * 0.5f
        };
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {cameraUp.x * worldHeight * 0.5f, cameraUp.y * worldHeight * 0.5f, cameraUp.z * worldHeight * 0.5f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        std::array<TexturedVertex, 6> vertices = {{
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f},
            {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f},
            {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f}
        }};

        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), TexturedVertex::ms_layout)
            < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            TexturedVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedVertex))
        );

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setTexture(0, m_textureSamplerHandle, texture.textureHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(viewId, m_texturedProgramHandle);
    }
}

const bgfx::TextureHandle *IndoorDebugRenderer::findIndoorTextureHandle(const std::string &textureName) const
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const IndoorTextureHandle &textureHandle : m_indoorTextureHandles)
    {
        if (textureHandle.textureName == normalizedTextureName && bgfx::isValid(textureHandle.textureHandle))
        {
            return &textureHandle.textureHandle;
        }
    }

    return nullptr;
}

bool IndoorDebugRenderer::hasScriptVisualOverrides() const
{
    if (!m_eventRuntimeState)
    {
        return false;
    }

    return !m_eventRuntimeState->textureOverrides.empty()
        || !m_eventRuntimeState->facetSetMasks.empty()
        || !m_eventRuntimeState->facetClearMasks.empty();
}

void IndoorDebugRenderer::rebuildMechanismBindings()
{
    m_mechanismBindings.clear();

    if (!m_indoorMapDeltaData || !m_indoorMapData)
    {
        return;
    }

    m_mechanismBindings.resize(m_indoorMapDeltaData->doors.size());

    for (size_t doorIndex = 0; doorIndex < m_indoorMapDeltaData->doors.size(); ++doorIndex)
    {
        const MapDeltaDoor &door = m_indoorMapDeltaData->doors[doorIndex];
        MechanismBinding binding = {};
        std::string faceSummary = "faces:";
        size_t shownFaceCount = 0;
        std::string linkedEventSummary = "linked face evts:";
        size_t shownEventCount = 0;

        for (uint16_t faceId : door.faceIds)
        {
            if (faceId >= m_indoorMapData->faces.size())
            {
                continue;
            }

            if (shownFaceCount < 6)
            {
                faceSummary += " " + std::to_string(faceId);
            }

            ++shownFaceCount;

            const IndoorFace &linkedFace = m_indoorMapData->faces[faceId];

            if (linkedFace.cogTriggered == 0)
            {
                continue;
            }

            bool hasLinkedEvent = false;

            if (m_localEvtProgram && m_localEvtProgram->hasEvent(linkedFace.cogTriggered))
            {
                hasLinkedEvent = true;
            }
            else if (m_globalEvtProgram && m_globalEvtProgram->hasEvent(linkedFace.cogTriggered))
            {
                hasLinkedEvent = true;
            }

            if (!hasLinkedEvent)
            {
                continue;
            }

            if (binding.linkedEventId == 0)
            {
                binding.linkedEventId = linkedFace.cogTriggered;
            }

            if (shownEventCount < 4)
            {
                linkedEventSummary += " f" + std::to_string(faceId) + "->" + std::to_string(linkedFace.cogTriggered);
            }

            ++shownEventCount;
        }

        if (shownFaceCount == 0)
        {
            faceSummary += " -";
        }
        else if (shownFaceCount > 6)
        {
            faceSummary += " ...";
        }

        if (shownEventCount == 0)
        {
            linkedEventSummary += " none";
        }
        else if (shownEventCount > 4)
        {
            linkedEventSummary += " ...";
        }

        binding.faceSummary = std::move(faceSummary);
        binding.linkedEventSummary = std::move(linkedEventSummary);
        m_mechanismBindings[doorIndex] = std::move(binding);
    }
}

std::vector<size_t> IndoorDebugRenderer::collectMovingMechanismFaceIndices() const
{
    std::vector<size_t> faceIndices;

    if (!m_indoorMapDeltaData || !m_eventRuntimeState)
    {
        return faceIndices;
    }

    std::vector<bool> seen(m_indoorMapData->faces.size(), false);

    for (const MapDeltaDoor &door : m_indoorMapDeltaData->doors)
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator iterator =
            m_eventRuntimeState->mechanisms.find(door.doorId);

        if (iterator == m_eventRuntimeState->mechanisms.end() || !iterator->second.isMoving)
        {
            continue;
        }

        for (uint16_t faceId : door.faceIds)
        {
            if (faceId >= seen.size() || seen[faceId])
            {
                continue;
            }

            seen[faceId] = true;
            faceIndices.push_back(faceId);
        }
    }

    return faceIndices;
}

bool IndoorDebugRenderer::rebuildAllTexturedBatches(uint64_t &texturedBuildNanoseconds)
{
    if (!m_indoorTextureSet || !m_indoorMapData)
    {
        m_texturedBatches.clear();
        m_faceBatchIndices.clear();
        m_faceVertexOffsets.clear();
        m_faceVertexCounts.clear();
        return true;
    }

    std::vector<TexturedBatch> previousBatches = std::move(m_texturedBatches);
    m_texturedBatches.clear();
    m_faceBatchIndices.assign(m_indoorMapData->faces.size(), -1);
    m_faceVertexOffsets.assign(m_indoorMapData->faces.size(), 0);
    m_faceVertexCounts.assign(m_indoorMapData->faces.size(), 0);

    std::unordered_map<std::string, size_t> batchIndicesByTexture;

    for (size_t faceIndex = 0; faceIndex < m_indoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_indoorMapData->faces[faceIndex];
        const std::string textureName = resolveFaceTextureName(face, m_eventRuntimeState);

        if (face.isPortal || textureName.empty() || face.vertexIndices.size() < 3)
        {
            continue;
        }

        if (!isFaceVisible(faceIndex, face, m_eventRuntimeState))
        {
            continue;
        }

        const std::string normalizedTextureName = toLowerCopy(textureName);
        size_t batchIndex = 0;
        const std::unordered_map<std::string, size_t>::const_iterator batchIterator =
            batchIndicesByTexture.find(normalizedTextureName);

        if (batchIterator == batchIndicesByTexture.end())
        {
            TexturedBatch batch = {};
            batch.textureName = normalizedTextureName;

            for (TexturedBatch &previousBatch : previousBatches)
            {
                if (previousBatch.textureName == normalizedTextureName)
                {
                    batch.vertexBufferHandle = previousBatch.vertexBufferHandle;
                    batch.textureHandle = previousBatch.textureHandle;
                    batch.vertexCapacity = previousBatch.vertexCapacity;
                    previousBatch.vertexBufferHandle = BGFX_INVALID_HANDLE;
                    previousBatch.textureHandle = BGFX_INVALID_HANDLE;
                    break;
                }
            }

            const bgfx::TextureHandle *pTextureHandle = findIndoorTextureHandle(textureName);

            if (pTextureHandle != nullptr)
            {
                batch.textureHandle = *pTextureHandle;
            }
            else
            {
                const OutdoorBitmapTexture *pTexture = nullptr;

                for (const OutdoorBitmapTexture &candidate : m_indoorTextureSet->textures)
                {
                    if (toLowerCopy(candidate.textureName) == normalizedTextureName)
                    {
                        pTexture = &candidate;
                        break;
                    }
                }

                if (pTexture != nullptr)
                {
                    batch.textureHandle = bgfx::createTexture2D(
                        static_cast<uint16_t>(pTexture->width),
                        static_cast<uint16_t>(pTexture->height),
                        false,
                        1,
                        bgfx::TextureFormat::BGRA8,
                        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
                        bgfx::copy(pTexture->pixels.data(), static_cast<uint32_t>(pTexture->pixels.size()))
                    );

                    if (bgfx::isValid(batch.textureHandle))
                    {
                        IndoorTextureHandle textureHandle = {};
                        textureHandle.textureName = normalizedTextureName;
                        textureHandle.textureHandle = batch.textureHandle;
                        m_indoorTextureHandles.push_back(std::move(textureHandle));
                    }
                }
            }

            batchIndex = m_texturedBatches.size();
            batchIndicesByTexture[normalizedTextureName] = batchIndex;
            m_texturedBatches.push_back(std::move(batch));
        }
        else
        {
            batchIndex = batchIterator->second;
        }

        const OutdoorBitmapTexture *pTexture = nullptr;

        for (const OutdoorBitmapTexture &candidate : m_indoorTextureSet->textures)
        {
            if (toLowerCopy(candidate.textureName) == normalizedTextureName)
            {
                pTexture = &candidate;
                break;
            }
        }

        if (pTexture == nullptr)
        {
            continue;
        }

        const uint64_t faceBuildBeginTickCount = SDL_GetTicksNS();
        const std::vector<TexturedVertex> faceVertices =
            buildFaceTexturedVertices(*m_indoorMapData, m_renderVertices, *pTexture, faceIndex, m_eventRuntimeState);
        texturedBuildNanoseconds += SDL_GetTicksNS() - faceBuildBeginTickCount;

        if (faceVertices.empty())
        {
            continue;
        }

        TexturedBatch &batch = m_texturedBatches[batchIndex];
        m_faceBatchIndices[faceIndex] = static_cast<int32_t>(batchIndex);
        m_faceVertexOffsets[faceIndex] = static_cast<uint32_t>(batch.vertices.size());
        m_faceVertexCounts[faceIndex] = static_cast<uint32_t>(faceVertices.size());
        batch.vertices.insert(batch.vertices.end(), faceVertices.begin(), faceVertices.end());
    }

    for (TexturedBatch &batch : m_texturedBatches)
    {
        batch.vertexCount = static_cast<uint32_t>(batch.vertices.size());

        if (batch.vertices.empty())
        {
            continue;
        }

        if (!updateDynamicVertexBuffer(
                batch.vertexBufferHandle,
                batch.vertexCapacity,
                batch.vertices,
                TexturedVertex::ms_layout))
        {
            return false;
        }
    }

    for (TexturedBatch &previousBatch : previousBatches)
    {
        if (bgfx::isValid(previousBatch.vertexBufferHandle))
        {
            bgfx::destroy(previousBatch.vertexBufferHandle);
        }
    }

    return true;
}

bool IndoorDebugRenderer::updateMovingMechanismFaceVertices(
    uint64_t &texturedBuildNanoseconds,
    uint64_t &uploadNanoseconds
)
{
    const std::vector<size_t> faceIndices = collectMovingMechanismFaceIndices();

    for (size_t faceIndex : faceIndices)
    {
        if (faceIndex >= m_faceBatchIndices.size())
        {
            continue;
        }

        const int32_t batchIndex = m_faceBatchIndices[faceIndex];

        if (batchIndex < 0 || static_cast<size_t>(batchIndex) >= m_texturedBatches.size())
        {
            continue;
        }

        TexturedBatch &batch = m_texturedBatches[static_cast<size_t>(batchIndex)];
        const uint32_t vertexOffset = m_faceVertexOffsets[faceIndex];
        const uint32_t vertexCount = m_faceVertexCounts[faceIndex];

        if (vertexCount == 0 || vertexOffset + vertexCount > batch.vertices.size())
        {
            continue;
        }

        const OutdoorBitmapTexture *pTexture = nullptr;

        for (const OutdoorBitmapTexture &candidate : m_indoorTextureSet->textures)
        {
            if (toLowerCopy(candidate.textureName) == batch.textureName)
            {
                pTexture = &candidate;
                break;
            }
        }

        if (pTexture == nullptr)
        {
            continue;
        }

        const uint64_t faceBuildBeginTickCount = SDL_GetTicksNS();
        const std::vector<TexturedVertex> faceVertices =
            buildFaceTexturedVertices(*m_indoorMapData, m_renderVertices, *pTexture, faceIndex, m_eventRuntimeState);
        texturedBuildNanoseconds += SDL_GetTicksNS() - faceBuildBeginTickCount;

        if (faceVertices.size() != vertexCount)
        {
            return false;
        }

        std::copy(faceVertices.begin(), faceVertices.end(), batch.vertices.begin() + vertexOffset);

        const uint64_t uploadBeginTickCount = SDL_GetTicksNS();
        bgfx::update(
            batch.vertexBufferHandle,
            vertexOffset,
            bgfx::copy(faceVertices.data(), static_cast<uint32_t>(faceVertices.size() * sizeof(TexturedVertex)))
        );
        uploadNanoseconds += SDL_GetTicksNS() - uploadBeginTickCount;
    }

    return true;
}

std::vector<IndoorVertex> IndoorDebugRenderer::buildMechanismAdjustedVertices(
    const IndoorMapData &indoorMapData,
    const std::optional<MapDeltaData> &indoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    std::vector<IndoorVertex> vertices = indoorMapData.vertices;

    if (!indoorMapDeltaData)
    {
        return vertices;
    }

    for (const MapDeltaDoor &baseDoor : indoorMapDeltaData->doors)
    {
        MapDeltaDoor door = baseDoor;
        RuntimeMechanismState runtimeMechanism = {};
        runtimeMechanism.state = door.state;
        runtimeMechanism.timeSinceTriggeredMs = float(door.timeSinceTriggered);
        runtimeMechanism.currentDistance = EventRuntime::calculateMechanismDistance(door, runtimeMechanism);
        runtimeMechanism.isMoving = door.state == 1 || door.state == 3;
        float distance = runtimeMechanism.currentDistance;

        if (eventRuntimeState)
        {
            const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
                eventRuntimeState->mechanisms.find(door.doorId);

            if (mechanismIterator != eventRuntimeState->mechanisms.end())
            {
                door.state = mechanismIterator->second.state;
                if (!mechanismIterator->second.isMoving && mechanismIterator->second.currentDistance > 0.0f)
                {
                    door.attributes &= ~0x2u;
                }
                distance = mechanismIterator->second.isMoving
                    ? EventRuntime::calculateMechanismDistance(door, mechanismIterator->second)
                    : mechanismIterator->second.currentDistance;
            }
        }

        if (door.vertexIds.empty() || door.xOffsets.empty() || door.yOffsets.empty() || door.zOffsets.empty())
        {
            continue;
        }

        const size_t movableVertexCount = std::min(
            door.vertexIds.size(),
            std::min(door.xOffsets.size(), std::min(door.yOffsets.size(), door.zOffsets.size()))
        );

        const float directionX = fixedDoorDirectionComponentToFloat(door.directionX);
        const float directionY = fixedDoorDirectionComponentToFloat(door.directionY);
        const float directionZ = fixedDoorDirectionComponentToFloat(door.directionZ);

        for (size_t vertexOffsetIndex = 0; vertexOffsetIndex < movableVertexCount; ++vertexOffsetIndex)
        {
            const uint16_t vertexId = door.vertexIds[vertexOffsetIndex];

            if (vertexId >= vertices.size())
            {
                continue;
            }

            IndoorVertex &vertex = vertices[vertexId];
            vertex.x = static_cast<int>(std::lround(
                static_cast<float>(door.xOffsets[vertexOffsetIndex]) + directionX * distance));
            vertex.y = static_cast<int>(std::lround(
                static_cast<float>(door.yOffsets[vertexOffsetIndex]) + directionY * distance));
            vertex.z = static_cast<int>(std::lround(
                static_cast<float>(door.zOffsets[vertexOffsetIndex]) + directionZ * distance));
        }
    }

    return vertices;
}

void IndoorDebugRenderer::destroyDerivedGeometryResources()
{
    if (bgfx::isValid(m_wireframeVertexBufferHandle))
    {
        bgfx::destroy(m_wireframeVertexBufferHandle);
        m_wireframeVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_portalVertexBufferHandle))
    {
        bgfx::destroy(m_portalVertexBufferHandle);
        m_portalVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_doorMarkerVertexBufferHandle))
    {
        bgfx::destroy(m_doorMarkerVertexBufferHandle);
        m_doorMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    m_wireframeVertexCount = 0;
    m_wireframeVertexCapacity = 0;
    m_portalVertexCount = 0;
    m_portalVertexCapacity = 0;
    m_doorMarkerVertexCount = 0;
    m_doorMarkerVertexCapacity = 0;

    for (TexturedBatch &batch : m_texturedBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    m_texturedBatches.clear();
    m_faceBatchIndices.clear();
    m_faceVertexOffsets.clear();
    m_faceVertexCounts.clear();
}

void IndoorDebugRenderer::destroyIndoorTextureHandles()
{
    for (IndoorTextureHandle &textureHandle : m_indoorTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
        }
    }

    m_indoorTextureHandles.clear();
}

bool IndoorDebugRenderer::rebuildDerivedGeometryResources()
{
    if (!m_indoorMapData)
    {
        return false;
    }

    m_renderVertices = buildMechanismAdjustedVertices(*m_indoorMapData, m_indoorMapDeltaData, m_eventRuntimeState);

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return true;
    }

    const std::vector<TerrainVertex> wireframeVertices =
        buildWireframeVertices(*m_indoorMapData, m_renderVertices, m_eventRuntimeState);
    const std::vector<TerrainVertex> portalVertices = buildPortalVertices(*m_indoorMapData, m_renderVertices);
    const std::vector<TerrainVertex> doorMarkerVertices =
        m_indoorMapDeltaData
            ? buildDoorMarkerVertices(m_renderVertices, *m_indoorMapDeltaData, m_eventRuntimeState)
            : std::vector<TerrainVertex>();

    if (!updateDynamicVertexBuffer(
            m_wireframeVertexBufferHandle,
            m_wireframeVertexCapacity,
            wireframeVertices,
            TerrainVertex::ms_layout))
    {
        return false;
    }
    m_wireframeVertexCount = static_cast<uint32_t>(wireframeVertices.size());

    if (!updateDynamicVertexBuffer(
            m_portalVertexBufferHandle,
            m_portalVertexCapacity,
            portalVertices,
            TerrainVertex::ms_layout))
    {
        return false;
    }
    m_portalVertexCount = static_cast<uint32_t>(portalVertices.size());

    if (!updateDynamicVertexBuffer(
            m_doorMarkerVertexBufferHandle,
            m_doorMarkerVertexCapacity,
            doorMarkerVertices,
            TerrainVertex::ms_layout))
    {
        return false;
    }
    m_doorMarkerVertexCount = static_cast<uint32_t>(doorMarkerVertices.size());

    if (m_indoorTextureSet)
    {
        const bool requiresFullTexturedRebuild =
            m_texturedBatches.empty()
            || hasScriptVisualOverrides();

        if (requiresFullTexturedRebuild)
        {
            uint64_t texturedBuildNanoseconds = 0;
            if (!rebuildAllTexturedBatches(texturedBuildNanoseconds))
            {
                return false;
            }
        }
        else
        {
            uint64_t texturedBuildNanoseconds = 0;
            uint64_t uploadNanoseconds = 0;

            if (!updateMovingMechanismFaceVertices(texturedBuildNanoseconds, uploadNanoseconds))
            {
                return false;
            }
        }
    }

    return true;
}

bool IndoorDebugRenderer::tryActivateInspectEvent(const InspectHit &inspectHit)
{
    if (!m_indoorMapData || !m_eventRuntimeState)
    {
        return false;
    }

    uint16_t eventId = 0;

    if (inspectHit.kind == "entity")
    {
        eventId = inspectHit.eventIdPrimary != 0 ? inspectHit.eventIdPrimary : inspectHit.eventIdSecondary;
    }
    else if (inspectHit.kind == "face")
    {
        eventId = inspectHit.cogTriggered;
    }
    else if (inspectHit.kind == "mechanism")
    {
        eventId = inspectHit.mechanismLinkedEventId != 0
            ? inspectHit.mechanismLinkedEventId
            : static_cast<uint16_t>(inspectHit.doorId);
    }
    else
    {
        return false;
    }

    if (eventId == 0)
    {
        m_eventRuntimeState->lastActivationResult = "no event on hovered target";
        return false;
    }

    std::cout << "Activating indoor event " << eventId
              << " from " << inspectHit.kind
              << " index=" << inspectHit.index << '\n';

    bool executed = m_eventRuntime.executeEventById(
        m_localEventIrProgram,
        m_globalEventIrProgram,
        eventId,
        *m_eventRuntimeState
    );

    if (!executed)
    {
        m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        return false;
    }

    if (!rebuildDerivedGeometryResources())
    {
        m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " execute failed";
        return false;
    }

    m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    return true;
}

std::vector<IndoorDebugRenderer::TexturedVertex> IndoorDebugRenderer::buildTexturedVertices(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &transformedVertices,
    const OutdoorBitmapTexture &texture,
    const std::vector<size_t> *pFaceIndices,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    std::vector<TexturedVertex> vertices;
    const std::string normalizedTextureName = toLowerCopy(texture.textureName);
    std::vector<size_t> allFaceIndices;

    if (pFaceIndices == nullptr)
    {
        allFaceIndices.resize(indoorMapData.faces.size());

        for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
        {
            allFaceIndices[faceIndex] = faceIndex;
        }

        pFaceIndices = &allFaceIndices;
    }

    for (size_t faceIndex : *pFaceIndices)
    {
        if (faceIndex >= indoorMapData.faces.size())
        {
            continue;
        }

        const std::vector<TexturedVertex> faceVertices =
            buildFaceTexturedVertices(indoorMapData, transformedVertices, texture, faceIndex, eventRuntimeState);

        if (!faceVertices.empty())
        {
            vertices.insert(vertices.end(), faceVertices.begin(), faceVertices.end());
        }
    }

    return vertices;
}

std::vector<IndoorDebugRenderer::TexturedVertex> IndoorDebugRenderer::buildFaceTexturedVertices(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &transformedVertices,
    const OutdoorBitmapTexture &texture,
    size_t faceIndex,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    std::vector<TexturedVertex> vertices;

    if (faceIndex >= indoorMapData.faces.size())
    {
        return vertices;
    }

    const IndoorFace &face = indoorMapData.faces[faceIndex];
    const std::string effectiveTextureName = resolveFaceTextureName(face, eventRuntimeState);

    if (face.isPortal || effectiveTextureName.empty() || face.vertexIndices.size() < 3)
    {
        return vertices;
    }

    if (!isFaceVisible(faceIndex, face, eventRuntimeState))
    {
        return vertices;
    }

    if (toLowerCopy(effectiveTextureName) != toLowerCopy(texture.textureName))
    {
        return vertices;
    }

    bx::Vec3 uAxis = {0.0f, 0.0f, 0.0f};
    bx::Vec3 vAxis = {0.0f, 0.0f, 0.0f};
    float uBase = 0.0f;
    float vBase = 0.0f;
    const bool hasTextureBasis = computeFaceTextureBasis(indoorMapData, face, uAxis, vAxis, uBase, vBase);

    for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
    {
        const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
        TexturedVertex triangleVertices[3] = {};
        bool isTriangleValid = true;

        for (size_t triangleVertexSlot = 0; triangleVertexSlot < 3; ++triangleVertexSlot)
        {
            const size_t faceVertexIndex = triangleVertexIndices[triangleVertexSlot];
            const uint16_t vertexIndex = face.vertexIndices[faceVertexIndex];

            if (vertexIndex >= transformedVertices.size()
                || faceVertexIndex >= face.textureUs.size()
                || faceVertexIndex >= face.textureVs.size())
            {
                isTriangleValid = false;
                break;
            }

            const IndoorVertex &vertex = transformedVertices[vertexIndex];
            TexturedVertex texturedVertex = {};
            texturedVertex.x = static_cast<float>(vertex.x);
            texturedVertex.y = static_cast<float>(vertex.y);
            texturedVertex.z = static_cast<float>(vertex.z);

            if (hasTextureBasis)
            {
                const bx::Vec3 point = {texturedVertex.x, texturedVertex.y, texturedVertex.z};
                texturedVertex.u =
                    (static_cast<float>(face.textureDeltaU) + vecDot(point, uAxis) + uBase)
                    / static_cast<float>(texture.width);
                texturedVertex.v =
                    (static_cast<float>(face.textureDeltaV) + vecDot(point, vAxis) + vBase)
                    / static_cast<float>(texture.height);
            }
            else
            {
                texturedVertex.u =
                    static_cast<float>(face.textureDeltaU + face.textureUs[faceVertexIndex])
                    / static_cast<float>(texture.width);
                texturedVertex.v =
                    static_cast<float>(face.textureDeltaV + face.textureVs[faceVertexIndex])
                    / static_cast<float>(texture.height);
            }

            triangleVertices[triangleVertexSlot] = texturedVertex;
        }

        if (!isTriangleValid)
        {
            continue;
        }

        for (const TexturedVertex &triangleVertex : triangleVertices)
        {
            vertices.push_back(triangleVertex);
        }
    }

    return vertices;
}

std::vector<IndoorDebugRenderer::TerrainVertex> IndoorDebugRenderer::buildEntityMarkerVertices(
    const IndoorMapData &indoorMapData
)
{
    std::vector<TerrainVertex> vertices;
    const uint32_t color = makeAbgr(255, 208, 64);
    const float halfExtent = 24.0f;
    const float height = 64.0f;
    vertices.reserve(indoorMapData.entities.size() * 6);

    for (const IndoorEntity &entity : indoorMapData.entities)
    {
        const float centerX = static_cast<float>(entity.x);
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

std::vector<IndoorDebugRenderer::TerrainVertex> IndoorDebugRenderer::buildSpawnMarkerVertices(
    const IndoorMapData &indoorMapData
)
{
    std::vector<TerrainVertex> vertices;
    const uint32_t color = makeAbgr(96, 192, 255);
    vertices.reserve(indoorMapData.spawns.size() * 6);

    for (const IndoorSpawn &spawn : indoorMapData.spawns)
    {
        const float centerX = static_cast<float>(spawn.x);
        const float centerY = static_cast<float>(spawn.y);
        const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.radius, 32));
        const float centerZ = static_cast<float>(spawn.z) + halfExtent;

        vertices.push_back({centerX - halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX + halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX, centerY - halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY + halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY, centerZ - halfExtent, color});
        vertices.push_back({centerX, centerY, centerZ + halfExtent, color});
    }

    return vertices;
}

std::vector<IndoorDebugRenderer::TerrainVertex> IndoorDebugRenderer::buildDoorMarkerVertices(
    const std::vector<IndoorVertex> &transformedVertices,
    const MapDeltaData &mapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    std::vector<TerrainVertex> vertices;
    const uint32_t defaultColor = makeAbgr(64, 255, 128);
    const uint32_t highlightedColor = makeAbgr(255, 220, 64);
    vertices.reserve(mapDeltaData.doors.size() * 6);

    for (const MapDeltaDoor &door : mapDeltaData.doors)
    {
        if (door.vertexIds.empty())
        {
            continue;
        }

        float centerX = 0.0f;
        float centerY = 0.0f;
        float centerZ = 0.0f;
        uint32_t validVertexCount = 0;

        for (uint16_t vertexId : door.vertexIds)
        {
            if (vertexId >= transformedVertices.size())
            {
                continue;
            }

            const IndoorVertex &vertex = transformedVertices[vertexId];
            centerX += static_cast<float>(vertex.x);
            centerY += static_cast<float>(vertex.y);
            centerZ += static_cast<float>(vertex.z);
            ++validVertexCount;
        }

        if (validVertexCount == 0)
        {
            continue;
        }

        centerX /= static_cast<float>(validVertexCount);
        centerY /= static_cast<float>(validVertexCount);
        centerZ /= static_cast<float>(validVertexCount);
        const float halfExtent = 48.0f;
        uint32_t color = defaultColor;

        if (eventRuntimeState)
        {
            const std::vector<uint32_t> &affectedMechanismIds = eventRuntimeState->lastAffectedMechanismIds;

            if (std::find(affectedMechanismIds.begin(), affectedMechanismIds.end(), door.doorId) != affectedMechanismIds.end())
            {
                color = highlightedColor;
            }
        }

        vertices.push_back({centerX - halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX + halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX, centerY - halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY + halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY, centerZ - halfExtent, color});
        vertices.push_back({centerX, centerY, centerZ + halfExtent, color});
    }

    return vertices;
}

IndoorDebugRenderer::InspectHit IndoorDebugRenderer::inspectAtCursor(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection
)
{
    InspectHit bestHit = {};
    float bestDistance = std::numeric_limits<float>::max();

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = indoorMapData.faces[faceIndex];

        if (face.vertexIndices.size() < 3)
        {
            continue;
        }

        if (!isFaceVisible(faceIndex, face, m_eventRuntimeState))
        {
            continue;
        }

        for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
        {
            const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
            bx::Vec3 triangleVertices[3] = {
                {0.0f, 0.0f, 0.0f},
                {0.0f, 0.0f, 0.0f},
                {0.0f, 0.0f, 0.0f}
            };
            bool isTriangleValid = true;

            for (size_t vertexSlot = 0; vertexSlot < 3; ++vertexSlot)
            {
                const uint16_t vertexIndex = face.vertexIndices[triangleVertexIndices[vertexSlot]];

                if (vertexIndex >= vertices.size())
                {
                    isTriangleValid = false;
                    break;
                }

                const IndoorVertex &vertex = vertices[vertexIndex];
                triangleVertices[vertexSlot] = {
                    static_cast<float>(vertex.x),
                    static_cast<float>(vertex.y),
                    static_cast<float>(vertex.z)
                };
            }

            if (!isTriangleValid)
            {
                continue;
            }

            float distance = 0.0f;

            if (intersectRayTriangle(
                    rayOrigin,
                    rayDirection,
                    triangleVertices[0],
                    triangleVertices[1],
                    triangleVertices[2],
                    distance)
                && distance < bestDistance)
            {
                bestDistance = distance;
                bestHit.hasHit = true;
                bestHit.kind = "face";
                bestHit.index = faceIndex;
                bestHit.textureName = face.textureName;
                bestHit.name.clear();
                bestHit.distance = distance;
                bestHit.attributes = face.attributes;
                bestHit.cogNumber = face.cogNumber;
                bestHit.cogTriggered = face.cogTriggered;
                bestHit.cogTriggerType = face.cogTriggerType;
                bestHit.roomNumber = face.roomNumber;
                bestHit.roomBehindNumber = face.roomBehindNumber;
                bestHit.facetType = face.facetType;
                bestHit.isPortal = face.isPortal;
            }
        }
    }

    for (size_t entityIndex = 0; entityIndex < indoorMapData.entities.size(); ++entityIndex)
    {
        const IndoorEntity &entity = indoorMapData.entities[entityIndex];
        const bx::Vec3 minBounds = {
            static_cast<float>(entity.x - 24),
            static_cast<float>(entity.y - 24),
            static_cast<float>(entity.z)
        };
        const bx::Vec3 maxBounds = {
            static_cast<float>(entity.x + 24),
            static_cast<float>(entity.y + 24),
            static_cast<float>(entity.z + 64)
        };
        float distance = 0.0f;

        if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance) && distance < bestDistance)
        {
            bestDistance = distance;
            bestHit.hasHit = true;
            bestHit.kind = "entity";
            bestHit.index = entityIndex;
            bestHit.name = entity.name;
            bestHit.textureName.clear();
            bestHit.distance = distance;
            bestHit.decorationListId = entity.decorationListId;
            bestHit.eventIdPrimary = entity.eventIdPrimary;
            bestHit.eventIdSecondary = entity.eventIdSecondary;
            bestHit.variablePrimary = entity.variablePrimary;
            bestHit.variableSecondary = entity.variableSecondary;
            bestHit.specialTrigger = entity.specialTrigger;
        }
    }

    for (size_t spawnIndex = 0; spawnIndex < indoorMapData.spawns.size(); ++spawnIndex)
    {
        const IndoorSpawn &spawn = indoorMapData.spawns[spawnIndex];
        const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.radius, 32));
        const bx::Vec3 minBounds = {
            static_cast<float>(spawn.x) - halfExtent,
            static_cast<float>(spawn.y) - halfExtent,
            static_cast<float>(spawn.z)
        };
        const bx::Vec3 maxBounds = {
            static_cast<float>(spawn.x) + halfExtent,
            static_cast<float>(spawn.y) + halfExtent,
            static_cast<float>(spawn.z) + halfExtent * 2.0f
        };
        float distance = 0.0f;

        if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance) && distance < bestDistance)
        {
            bestDistance = distance;
            bestHit.hasHit = true;
            bestHit.kind = "spawn";
            bestHit.index = spawnIndex;
            bestHit.name.clear();
            bestHit.textureName.clear();
            bestHit.distance = distance;

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

    if (m_indoorActorPreviewBillboardSet)
    {
        for (size_t actorIndex = 0; actorIndex < m_indoorActorPreviewBillboardSet->billboards.size(); ++actorIndex)
        {
            const ActorPreviewBillboard &actor = m_indoorActorPreviewBillboardSet->billboards[actorIndex];
            const float halfExtent = static_cast<float>(std::max<uint16_t>(actor.radius, 32));
            const float height = static_cast<float>(std::max<uint16_t>(actor.height, 96));
            const bx::Vec3 minBounds = {
                static_cast<float>(actor.x) - halfExtent,
                static_cast<float>(actor.y) - halfExtent,
                static_cast<float>(actor.z)
            };
            const bx::Vec3 maxBounds = {
                static_cast<float>(actor.x) + halfExtent,
                static_cast<float>(actor.y) + halfExtent,
                static_cast<float>(actor.z) + height
            };
            float distance = 0.0f;

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance) && distance < bestDistance)
            {
                bestDistance = distance;
                bestHit.hasHit = true;
                bestHit.kind = "actor";
                bestHit.index = actorIndex;
                bestHit.name = actor.actorName;
                bestHit.textureName.clear();
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

    if (m_indoorSpriteObjectBillboardSet)
    {
        for (size_t objectIndex = 0; objectIndex < m_indoorSpriteObjectBillboardSet->billboards.size(); ++objectIndex)
        {
            const SpriteObjectBillboard &object = m_indoorSpriteObjectBillboardSet->billboards[objectIndex];
            const float halfExtent = std::max(32.0f, float(std::max(object.radius, int16_t(32))));
            const float height = std::max(64.0f, float(std::max(object.height, int16_t(64))));
            const bx::Vec3 minBounds = {
                float(object.x) - halfExtent,
                float(object.y) - halfExtent,
                float(object.z)
            };
            const bx::Vec3 maxBounds = {
                float(object.x) + halfExtent,
                float(object.y) + halfExtent,
                float(object.z) + height
            };
            float distance = 0.0f;

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance) && distance < bestDistance)
            {
                bestDistance = distance;
                bestHit.hasHit = true;
                bestHit.kind = "object";
                bestHit.index = objectIndex;
                bestHit.name = object.objectName;
                bestHit.distance = distance;
                bestHit.objectDescriptionId = object.objectDescriptionId;
                bestHit.objectSpriteId = object.objectSpriteId;
                bestHit.attributes = object.attributes;
                bestHit.spellId = object.spellId;
            }
        }
    }

    if (m_indoorMapDeltaData)
    {
        for (size_t doorIndex = 0; doorIndex < m_indoorMapDeltaData->doors.size(); ++doorIndex)
        {
            const MapDeltaDoor &door = m_indoorMapDeltaData->doors[doorIndex];

            if (door.vertexIds.empty())
            {
                continue;
            }

            float centerX = 0.0f;
            float centerY = 0.0f;
            float centerZ = 0.0f;
            uint32_t validVertexCount = 0;

            for (uint16_t vertexId : door.vertexIds)
            {
                if (vertexId >= vertices.size())
                {
                    continue;
                }

                const IndoorVertex &vertex = vertices[vertexId];
                centerX += static_cast<float>(vertex.x);
                centerY += static_cast<float>(vertex.y);
                centerZ += static_cast<float>(vertex.z);
                ++validVertexCount;
            }

            if (validVertexCount == 0)
            {
                continue;
            }

            centerX /= static_cast<float>(validVertexCount);
            centerY /= static_cast<float>(validVertexCount);
            centerZ /= static_cast<float>(validVertexCount);
            const float halfExtent = 48.0f;
            const bx::Vec3 minBounds = {centerX - halfExtent, centerY - halfExtent, centerZ - halfExtent};
            const bx::Vec3 maxBounds = {centerX + halfExtent, centerY + halfExtent, centerZ + halfExtent};
            float distance = 0.0f;

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance) && distance < bestDistance)
            {
                bestDistance = distance;
                bestHit.hasHit = true;
                bestHit.kind = "mechanism";
                bestHit.index = doorIndex;
                bestHit.name.clear();
                bestHit.distance = distance;
                bestHit.doorAttributes = door.attributes;
                bestHit.doorId = door.doorId;
                bestHit.doorState = door.state;

                if (doorIndex < m_mechanismBindings.size())
                {
                    const MechanismBinding &binding = m_mechanismBindings[doorIndex];
                    bestHit.mechanismLinkedEventId = binding.linkedEventId;
                    bestHit.mechanismFaceSummary = binding.faceSummary;
                    bestHit.mechanismLinkedEventSummary = binding.linkedEventSummary;
                }
            }
        }
    }

    return bestHit;
}

std::vector<IndoorDebugRenderer::TerrainVertex> IndoorDebugRenderer::buildWireframeVertices(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &transformedVertices,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    std::vector<TerrainVertex> lineVertices;
    const uint32_t lineColor = makeAbgr(255, 255, 255);

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = indoorMapData.faces[faceIndex];

        if (face.isPortal || face.vertexIndices.size() < 2)
        {
            continue;
        }

        if (!isFaceVisible(faceIndex, face, eventRuntimeState))
        {
            continue;
        }

        for (size_t vertexIndex = 0; vertexIndex < face.vertexIndices.size(); ++vertexIndex)
        {
            const uint16_t startIndex = face.vertexIndices[vertexIndex];
            const uint16_t endIndex = face.vertexIndices[(vertexIndex + 1) % face.vertexIndices.size()];

            if (startIndex >= transformedVertices.size() || endIndex >= transformedVertices.size())
            {
                continue;
            }

            const IndoorVertex &startVertex = transformedVertices[startIndex];
            const IndoorVertex &endVertex = transformedVertices[endIndex];

            TerrainVertex lineStart = {};
            lineStart.x = static_cast<float>(startVertex.x);
            lineStart.y = static_cast<float>(startVertex.y);
            lineStart.z = static_cast<float>(startVertex.z);
            lineStart.abgr = lineColor;
            lineVertices.push_back(lineStart);

            TerrainVertex lineEnd = {};
            lineEnd.x = static_cast<float>(endVertex.x);
            lineEnd.y = static_cast<float>(endVertex.y);
            lineEnd.z = static_cast<float>(endVertex.z);
            lineEnd.abgr = lineColor;
            lineVertices.push_back(lineEnd);
        }
    }

    return lineVertices;
}

std::vector<IndoorDebugRenderer::TerrainVertex> IndoorDebugRenderer::buildPortalVertices(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &transformedVertices
)
{
    std::vector<TerrainVertex> portalVertices;
    const uint32_t portalColor = makeAbgr(255, 64, 192);

    for (const IndoorFace &face : indoorMapData.faces)
    {
        if (!face.isPortal || face.vertexIndices.size() < 2)
        {
            continue;
        }

        for (size_t vertexIndex = 0; vertexIndex < face.vertexIndices.size(); ++vertexIndex)
        {
            const uint16_t startIndex = face.vertexIndices[vertexIndex];
            const uint16_t endIndex = face.vertexIndices[(vertexIndex + 1) % face.vertexIndices.size()];

            if (startIndex >= transformedVertices.size() || endIndex >= transformedVertices.size())
            {
                continue;
            }

            const IndoorVertex &startVertex = transformedVertices[startIndex];
            const IndoorVertex &endVertex = transformedVertices[endIndex];
            portalVertices.push_back({
                static_cast<float>(startVertex.x),
                static_cast<float>(startVertex.y),
                static_cast<float>(startVertex.z),
                portalColor
            });
            portalVertices.push_back({
                static_cast<float>(endVertex.x),
                static_cast<float>(endVertex.y),
                static_cast<float>(endVertex.z),
                portalColor
            });
        }
    }

    return portalVertices;
}

void IndoorDebugRenderer::updateCameraFromInput(float deltaSeconds)
{
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

    const float moveSpeed = 320.0f;
    const float fastMoveMultiplier = 4.0f;
    const float mouseRotateSpeed = 0.0045f;
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isRightMousePressed = (mouseButtons & SDL_BUTTON_RMASK) != 0;

    if (isRightMousePressed)
    {
        if (m_isRotatingCamera)
        {
            m_cameraYawRadians -= (mouseX - m_lastMouseX) * mouseRotateSpeed;
            m_cameraPitchRadians -= (mouseY - m_lastMouseY) * mouseRotateSpeed;
        }

        m_isRotatingCamera = true;
        m_lastMouseX = mouseX;
        m_lastMouseY = mouseY;
    }
    else
    {
        m_isRotatingCamera = false;
    }

    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    const bx::Vec3 forward = {cosYaw * cosPitch, -sinYaw * cosPitch, sinPitch};
    const bx::Vec3 right = {sinYaw, cosYaw, 0.0f};
    const bool isFastMovePressed =
        pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    const float currentMoveSpeed = isFastMovePressed ? moveSpeed * fastMoveMultiplier : moveSpeed;

    if (pKeyboardState[SDL_SCANCODE_W])
    {
        m_cameraPositionX += forward.x * currentMoveSpeed * deltaSeconds;
        m_cameraPositionY += forward.y * currentMoveSpeed * deltaSeconds;
        m_cameraPositionZ += forward.z * currentMoveSpeed * deltaSeconds;
    }

    if (pKeyboardState[SDL_SCANCODE_S])
    {
        m_cameraPositionX -= forward.x * currentMoveSpeed * deltaSeconds;
        m_cameraPositionY -= forward.y * currentMoveSpeed * deltaSeconds;
        m_cameraPositionZ -= forward.z * currentMoveSpeed * deltaSeconds;
    }

    if (pKeyboardState[SDL_SCANCODE_A])
    {
        m_cameraPositionX -= right.x * currentMoveSpeed * deltaSeconds;
        m_cameraPositionY -= right.y * currentMoveSpeed * deltaSeconds;
    }

    if (pKeyboardState[SDL_SCANCODE_D])
    {
        m_cameraPositionX += right.x * currentMoveSpeed * deltaSeconds;
        m_cameraPositionY += right.y * currentMoveSpeed * deltaSeconds;
    }

    if (pKeyboardState[SDL_SCANCODE_1])
    {
        if (!m_toggleFilledLatch)
        {
            m_showFilled = !m_showFilled;
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
            m_showWireframe = !m_showWireframe;
            m_toggleWireframeLatch = true;
        }
    }
    else
    {
        m_toggleWireframeLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_3])
    {
        if (!m_togglePortalsLatch)
        {
            m_showPortals = !m_showPortals;
            m_togglePortalsLatch = true;
        }
    }
    else
    {
        m_togglePortalsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_4])
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

    if (pKeyboardState[SDL_SCANCODE_5])
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

    if (pKeyboardState[SDL_SCANCODE_6])
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

    if (pKeyboardState[SDL_SCANCODE_7])
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

    if (pKeyboardState[SDL_SCANCODE_8])
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

    if (pKeyboardState[SDL_SCANCODE_9])
    {
        if (!m_toggleDoorsLatch)
        {
            m_showDoors = !m_showDoors;
            m_toggleDoorsLatch = true;
        }
    }
    else
    {
        m_toggleDoorsLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_0])
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

    if (m_cameraYawRadians > Pi)
    {
        m_cameraYawRadians -= Pi * 2.0f;
    }
    else if (m_cameraYawRadians < -Pi)
    {
        m_cameraYawRadians += Pi * 2.0f;
    }

    m_cameraPitchRadians = std::clamp(m_cameraPitchRadians, -1.55f, 1.55f);
}
}
