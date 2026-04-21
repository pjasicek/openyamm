#include "game/indoor/IndoorDebugRenderer.h"

#include "game/data/ActorNameResolver.h"
#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/render/TextureFiltering.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/SpriteObjectDefs.h"
#include "game/SpawnPreview.h"
#include "game/StringUtils.h"

#include <bx/math.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <bit>
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
constexpr uint16_t HudViewId = 2;
constexpr float Pi = 3.14159265358979323846f;
constexpr float InspectRayEpsilon = 0.0001f;

struct RuntimeActorBillboard
{
    size_t actorIndex = static_cast<size_t>(-1);
    int x = 0;
    int y = 0;
    int z = 0;
    int16_t sectorId = -1;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint16_t spriteFrameIndex = 0;
    bool useStaticFrame = false;
    bool isFriendly = false;
    std::string actorName;
};

struct RuntimeSpriteObjectBillboard
{
    size_t objectIndex = static_cast<size_t>(-1);
    int x = 0;
    int y = 0;
    int z = 0;
    int16_t sectorId = -1;
    int16_t radius = 0;
    int16_t height = 0;
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t attributes = 0;
    int32_t spellId = 0;
    uint32_t timeSinceCreatedTicks = 0;
    std::string objectName;
};

struct ProjectedPoint
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

bool projectWorldPointToScreen(
    const bx::Vec3 &worldPoint,
    int width,
    int height,
    const float *pViewProjectionMatrix,
    ProjectedPoint &projected)
{
    const float clipX =
        worldPoint.x * pViewProjectionMatrix[0]
        + worldPoint.y * pViewProjectionMatrix[4]
        + worldPoint.z * pViewProjectionMatrix[8]
        + pViewProjectionMatrix[12];
    const float clipY =
        worldPoint.x * pViewProjectionMatrix[1]
        + worldPoint.y * pViewProjectionMatrix[5]
        + worldPoint.z * pViewProjectionMatrix[9]
        + pViewProjectionMatrix[13];
    const float clipZ =
        worldPoint.x * pViewProjectionMatrix[2]
        + worldPoint.y * pViewProjectionMatrix[6]
        + worldPoint.z * pViewProjectionMatrix[10]
        + pViewProjectionMatrix[14];
    const float clipW =
        worldPoint.x * pViewProjectionMatrix[3]
        + worldPoint.y * pViewProjectionMatrix[7]
        + worldPoint.z * pViewProjectionMatrix[11]
        + pViewProjectionMatrix[15];

    if (clipW <= 0.0f)
    {
        return false;
    }

    const float reciprocalW = 1.0f / clipW;
    projected.x = ((clipX * reciprocalW) * 0.5f + 0.5f) * static_cast<float>(width);
    projected.y = (1.0f - ((clipY * reciprocalW) * 0.5f + 0.5f)) * static_cast<float>(height);
    projected.z = clipZ * reciprocalW;
    return true;
}

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

float resolveMechanismDistance(
    const MapDeltaDoor &baseDoor,
    const std::optional<EventRuntimeState> &eventRuntimeState
);

std::vector<uint32_t> buildDoorStateSignature(
    const std::optional<MapDeltaData> &mapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    std::vector<uint32_t> signature;

    if (!mapDeltaData)
    {
        return signature;
    }

    signature.reserve(mapDeltaData->doors.size() * 2);

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        signature.push_back(door.doorId);
        signature.push_back(std::bit_cast<uint32_t>(resolveMechanismDistance(door, eventRuntimeState)));
    }

    return signature;
}

const MonsterEntry *resolveRuntimeMonsterEntry(const MonsterTable &monsterTable, const MapDeltaActor &actor)
{
    const MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
        monsterTable.findDisplayEntryById(actor.monsterInfoId);

    if (pDisplayEntry != nullptr)
    {
        const MonsterEntry *pMonsterEntry = monsterTable.findByInternalName(pDisplayEntry->pictureName);

        if (pMonsterEntry != nullptr)
        {
            return pMonsterEntry;
        }
    }

    return monsterTable.findById(actor.monsterId);
}

uint16_t resolveRuntimeActorSpriteFrameIndex(
    const SpriteFrameTable &spriteFrameTable,
    const MapDeltaActor &actor,
    const MonsterEntry *pMonsterEntry
)
{
    if (pMonsterEntry != nullptr)
    {
        for (const std::string &spriteName : pMonsterEntry->spriteNames)
        {
            if (spriteName.empty())
            {
                continue;
            }

            const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

            if (frameIndex)
            {
                return *frameIndex;
            }
        }
    }

    for (uint16_t spriteId : actor.spriteIds)
    {
        if (spriteId != 0)
        {
            return spriteId;
        }
    }

    return 0;
}

std::vector<RuntimeActorBillboard> buildRuntimeActorBillboards(
    const MonsterTable &monsterTable,
    const SpriteFrameTable &spriteFrameTable,
    const MapDeltaData &mapDeltaData
)
{
    std::vector<RuntimeActorBillboard> billboards;
    billboards.reserve(mapDeltaData.actors.size());

    for (size_t actorIndex = 0; actorIndex < mapDeltaData.actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = mapDeltaData.actors[actorIndex];
        const MonsterEntry *pMonsterEntry = resolveRuntimeMonsterEntry(monsterTable, actor);
        const uint16_t spriteFrameIndex =
            resolveRuntimeActorSpriteFrameIndex(spriteFrameTable, actor, pMonsterEntry);

        if (spriteFrameIndex == 0)
        {
            continue;
        }

        RuntimeActorBillboard billboard = {};
        billboard.actorIndex = actorIndex;
        billboard.x = actor.x;
        billboard.y = actor.y;
        billboard.z = actor.z;
        billboard.sectorId = actor.sectorId;
        billboard.radius = actor.radius;
        billboard.height = actor.height;
        billboard.spriteFrameIndex = spriteFrameIndex;
        billboard.useStaticFrame = false;
        billboard.isFriendly = (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) == 0;
        billboard.actorName = resolveMapDeltaActorName(monsterTable, actor);
        billboards.push_back(std::move(billboard));
    }

    return billboards;
}

std::vector<RuntimeSpriteObjectBillboard> buildRuntimeSpriteObjectBillboards(
    const ObjectTable &objectTable,
    const MapDeltaData &mapDeltaData
)
{
    std::vector<RuntimeSpriteObjectBillboard> billboards;
    billboards.reserve(mapDeltaData.spriteObjects.size());

    for (size_t objectIndex = 0; objectIndex < mapDeltaData.spriteObjects.size(); ++objectIndex)
    {
        const MapDeltaSpriteObject &spriteObject = mapDeltaData.spriteObjects[objectIndex];
        const ObjectEntry *pObjectEntry = objectTable.get(spriteObject.objectDescriptionId);

        if (pObjectEntry == nullptr || (pObjectEntry->flags & ObjectDescNoSprite) != 0 || pObjectEntry->spriteId == 0)
        {
            continue;
        }

        if (hasContainingItemPayload(spriteObject.rawContainingItem)
            && (pObjectEntry->flags & ObjectDescUnpickable) == 0)
        {
            continue;
        }

        RuntimeSpriteObjectBillboard billboard = {};
        billboard.objectIndex = objectIndex;
        billboard.x = spriteObject.x;
        billboard.y = spriteObject.y;
        billboard.z = spriteObject.z;
        billboard.sectorId = spriteObject.sectorId;
        billboard.radius = pObjectEntry->radius;
        billboard.height = pObjectEntry->height;
        billboard.objectDescriptionId = spriteObject.objectDescriptionId;
        billboard.objectSpriteId = pObjectEntry->spriteId;
        billboard.attributes = spriteObject.attributes;
        billboard.spellId = spriteObject.spellId;
        billboard.timeSinceCreatedTicks = uint32_t(spriteObject.timeSinceCreated) * 8;
        billboard.objectName = pObjectEntry->internalName;
        billboards.push_back(std::move(billboard));
    }

    return billboards;
}

const SurfaceAnimationSequence *findTextureAnimationBinding(
    const std::vector<std::pair<std::string, SurfaceAnimationSequence>> &bindings,
    const std::string &textureName)
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const auto &binding : bindings)
    {
        if (binding.first == normalizedTextureName)
        {
            return &binding.second;
        }
    }

    return nullptr;
}

size_t frameIndexForAnimation(
    const std::vector<uint32_t> &frameLengthTicks,
    uint32_t animationLengthTicks,
    uint32_t elapsedTicks)
{
    if (frameLengthTicks.empty() || frameLengthTicks.size() == 1 || animationLengthTicks == 0)
    {
        return 0;
    }

    uint32_t localTicks = elapsedTicks % animationLengthTicks;

    for (size_t frameIndex = 0; frameIndex < frameLengthTicks.size(); ++frameIndex)
    {
        const uint32_t frameLength = frameLengthTicks[frameIndex];

        if (frameLength == 0 || localTicks < frameLength)
        {
            return frameIndex;
        }

        localTicks -= frameLength;
    }

    return frameLengthTicks.size() - 1;
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

struct ProjectedFacePoint
{
    float x = 0.0f;
    float y = 0.0f;
};

struct MechanismFaceTextureState
{
    const MapDeltaDoor *pDoor = nullptr;
    size_t faceOffset = 0;
    float distance = 0.0f;
    bx::Vec3 direction = {0.0f, 0.0f, 0.0f};
};

bx::Vec3 computeFaceNormal(
    const std::vector<IndoorVertex> &transformedVertices,
    const IndoorFace &face
)
{
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};

    if (face.vertexIndices.size() < 3)
    {
        return normal;
    }

    for (size_t index = 0; index < face.vertexIndices.size(); ++index)
    {
        const uint16_t currentVertexIndex = face.vertexIndices[index];
        const uint16_t nextVertexIndex = face.vertexIndices[(index + 1) % face.vertexIndices.size()];

        if (currentVertexIndex >= transformedVertices.size() || nextVertexIndex >= transformedVertices.size())
        {
            return {0.0f, 0.0f, 0.0f};
        }

        const IndoorVertex &currentVertex = transformedVertices[currentVertexIndex];
        const IndoorVertex &nextVertex = transformedVertices[nextVertexIndex];

        normal.x += (static_cast<float>(currentVertex.y) - static_cast<float>(nextVertex.y))
            * (static_cast<float>(currentVertex.z) + static_cast<float>(nextVertex.z));
        normal.y += (static_cast<float>(currentVertex.z) - static_cast<float>(nextVertex.z))
            * (static_cast<float>(currentVertex.x) + static_cast<float>(nextVertex.x));
        normal.z += (static_cast<float>(currentVertex.x) - static_cast<float>(nextVertex.x))
            * (static_cast<float>(currentVertex.y) + static_cast<float>(nextVertex.y));
    }

    return normal;
}

ProjectedFacePoint projectFacePoint(const bx::Vec3 &normal, const IndoorVertex &vertex)
{
    const float absoluteX = std::fabs(normal.x);
    const float absoluteY = std::fabs(normal.y);
    const float absoluteZ = std::fabs(normal.z);

    if (absoluteX >= absoluteY && absoluteX >= absoluteZ)
    {
        return {static_cast<float>(vertex.y), static_cast<float>(vertex.z)};
    }

    if (absoluteY >= absoluteX && absoluteY >= absoluteZ)
    {
        return {static_cast<float>(vertex.x), static_cast<float>(vertex.z)};
    }

    return {static_cast<float>(vertex.x), static_cast<float>(vertex.y)};
}

float resolveMechanismDistance(
    const MapDeltaDoor &baseDoor,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    MapDeltaDoor door = baseDoor;
    RuntimeMechanismState runtimeMechanism = {};
    runtimeMechanism.state = door.state;
    runtimeMechanism.timeSinceTriggeredMs = float(door.timeSinceTriggered);
    runtimeMechanism.currentDistance = EventRuntime::calculateMechanismDistance(door, runtimeMechanism);
    runtimeMechanism.isMoving =
        door.state == static_cast<uint16_t>(EvtMechanismState::Opening)
        || door.state == static_cast<uint16_t>(EvtMechanismState::Closing);

    if (!eventRuntimeState)
    {
        return runtimeMechanism.currentDistance;
    }

    const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
        eventRuntimeState->mechanisms.find(door.doorId);

    if (mechanismIterator == eventRuntimeState->mechanisms.end())
    {
        return runtimeMechanism.currentDistance;
    }

    door.state = mechanismIterator->second.state;
    return mechanismIterator->second.isMoving
        ? EventRuntime::calculateMechanismDistance(door, mechanismIterator->second)
        : mechanismIterator->second.currentDistance;
}

std::optional<MechanismFaceTextureState> findMechanismFaceTextureState(
    size_t faceIndex,
    const std::optional<MapDeltaData> &indoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    if (!indoorMapDeltaData)
    {
        return std::nullopt;
    }

    for (const MapDeltaDoor &door : indoorMapDeltaData->doors)
    {
        for (size_t doorFaceIndex = 0; doorFaceIndex < door.faceIds.size(); ++doorFaceIndex)
        {
            if (door.faceIds[doorFaceIndex] != faceIndex)
            {
                continue;
            }

            MechanismFaceTextureState state = {};
            state.pDoor = &door;
            state.faceOffset = doorFaceIndex;
            state.distance = resolveMechanismDistance(door, eventRuntimeState);
            state.direction = {
                static_cast<float>(door.directionX) / 65536.0f,
                static_cast<float>(door.directionY) / 65536.0f,
                static_cast<float>(door.directionZ) / 65536.0f
            };
            return state;
        }
    }

    return std::nullopt;
}

bool calculateFaceTextureAxes(const IndoorFace &face, const bx::Vec3 &normal, bx::Vec3 &axisU, bx::Vec3 &axisV)
{
    if (face.facetType == 1)
    {
        axisU = {-normal.y, normal.x, 0.0f};
        axisV = {0.0f, 0.0f, -1.0f};
    }
    else if (face.facetType == 3 || face.facetType == 5)
    {
        axisU = {1.0f, 0.0f, 0.0f};
        axisV = {0.0f, -1.0f, 0.0f};
    }
    else if (face.facetType == 4 || face.facetType == 6)
    {
        if (std::abs(normal.z) < 0.70863342285f)
        {
            axisU = vecNormalize({-normal.y, normal.x, 0.0f});
            axisV = {0.0f, 0.0f, -1.0f};
        }
        else
        {
            axisU = {1.0f, 0.0f, 0.0f};
            axisV = {0.0f, -1.0f, 0.0f};
        }
    }
    else
    {
        return false;
    }

    if (hasFaceAttribute(face.attributes, FaceAttribute::FlipNormalU))
    {
        axisU = {-axisU.x, -axisU.y, -axisU.z};
    }

    if (hasFaceAttribute(face.attributes, FaceAttribute::FlipNormalV))
    {
        axisV = {-axisV.x, -axisV.y, -axisV.z};
    }

    return true;
}

float orient2d(
    const ProjectedFacePoint &a,
    const ProjectedFacePoint &b,
    const ProjectedFacePoint &c
)
{
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
}

float signedPolygonArea2d(
    const std::vector<ProjectedFacePoint> &points,
    const std::vector<size_t> &indices
)
{
    float area = 0.0f;

    if (indices.size() < 3)
    {
        return area;
    }

    for (size_t index = 0; index < indices.size(); ++index)
    {
        const ProjectedFacePoint &current = points[indices[index]];
        const ProjectedFacePoint &next = points[indices[(index + 1) % indices.size()]];
        area += current.x * next.y - next.x * current.y;
    }

    return area * 0.5f;
}

bool pointInTriangle2d(
    const ProjectedFacePoint &point,
    const ProjectedFacePoint &a,
    const ProjectedFacePoint &b,
    const ProjectedFacePoint &c,
    bool isCounterClockwise
)
{
    constexpr float TriangleEpsilon = 0.0001f;
    const float ab = orient2d(a, b, point);
    const float bc = orient2d(b, c, point);
    const float ca = orient2d(c, a, point);

    if (isCounterClockwise)
    {
        return ab >= -TriangleEpsilon && bc >= -TriangleEpsilon && ca >= -TriangleEpsilon;
    }

    return ab <= TriangleEpsilon && bc <= TriangleEpsilon && ca <= TriangleEpsilon;
}

bool triangulateFaceProjected(
    const std::vector<IndoorVertex> &transformedVertices,
    const IndoorFace &face,
    std::vector<std::array<size_t, 3>> &triangleVertexOrders
)
{
    triangleVertexOrders.clear();

    if (face.vertexIndices.size() < 3)
    {
        return false;
    }

    const bx::Vec3 normal = computeFaceNormal(transformedVertices, face);

    if (vecDot(normal, normal) <= 0.0001f)
    {
        return false;
    }

    std::vector<ProjectedFacePoint> projectedPoints;
    projectedPoints.reserve(face.vertexIndices.size());

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= transformedVertices.size())
        {
            triangleVertexOrders.clear();
            return false;
        }

        projectedPoints.push_back(projectFacePoint(normal, transformedVertices[vertexIndex]));
    }

    std::vector<size_t> polygonIndices(face.vertexIndices.size());

    for (size_t index = 0; index < polygonIndices.size(); ++index)
    {
        polygonIndices[index] = index;
    }

    const float signedArea = signedPolygonArea2d(projectedPoints, polygonIndices);

    if (std::fabs(signedArea) <= 0.0001f)
    {
        return false;
    }

    const bool isCounterClockwise = signedArea > 0.0f;
    size_t safetyCounter = 0;
    const size_t safetyLimit = polygonIndices.size() * polygonIndices.size();

    while (polygonIndices.size() > 3 && safetyCounter < safetyLimit)
    {
        bool clippedEar = false;

        for (size_t polygonIndex = 0; polygonIndex < polygonIndices.size(); ++polygonIndex)
        {
            const size_t previous =
                polygonIndices[(polygonIndex + polygonIndices.size() - 1) % polygonIndices.size()];
            const size_t current = polygonIndices[polygonIndex];
            const size_t next = polygonIndices[(polygonIndex + 1) % polygonIndices.size()];
            const float cornerOrientation =
                orient2d(projectedPoints[previous], projectedPoints[current], projectedPoints[next]);

            if ((isCounterClockwise && cornerOrientation <= 0.0001f)
                || (!isCounterClockwise && cornerOrientation >= -0.0001f))
            {
                continue;
            }

            bool containsInteriorPoint = false;

            for (size_t candidate : polygonIndices)
            {
                if (candidate == previous || candidate == current || candidate == next)
                {
                    continue;
                }

                if (pointInTriangle2d(
                        projectedPoints[candidate],
                        projectedPoints[previous],
                        projectedPoints[current],
                        projectedPoints[next],
                        isCounterClockwise))
                {
                    containsInteriorPoint = true;
                    break;
                }
            }

            if (containsInteriorPoint)
            {
                continue;
            }

            triangleVertexOrders.push_back({previous, current, next});
            polygonIndices.erase(polygonIndices.begin() + static_cast<std::ptrdiff_t>(polygonIndex));
            clippedEar = true;
            break;
        }

        if (!clippedEar)
        {
            triangleVertexOrders.clear();
            return false;
        }

        ++safetyCounter;
    }

    if (polygonIndices.size() == 3)
    {
        triangleVertexOrders.push_back({polygonIndices[0], polygonIndices[1], polygonIndices[2]});
    }

    return !triangleVertexOrders.empty();
}

std::string summarizeLinkedEvent(
    uint16_t eventId,
    const std::optional<HouseTable> &houseTable,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram
)
{
    static_cast<void>(houseTable);

    if (eventId == 0)
    {
        return "-";
    }

    if (localEventProgram)
    {
        const std::optional<std::string> summary = localEventProgram->summarizeEvent(eventId);

        if (summary)
        {
            return "L:" + *summary;
        }
    }

    if (globalEventProgram)
    {
        const std::optional<std::string> summary = globalEventProgram->summarizeEvent(eventId);

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
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram
)
{
    if (eventId == 0 || !mapDeltaData || !chestTable)
    {
        return {};
    }

    std::vector<uint32_t> chestIds;

    if (localEventProgram && localEventProgram->hasEvent(eventId))
    {
        chestIds = localEventProgram->getOpenedChestIds(eventId);
    }
    else if (globalEventProgram && globalEventProgram->hasEvent(eventId))
    {
        chestIds = globalEventProgram->getOpenedChestIds(eventId);
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

    return hasFaceAttribute(invisibleMask, FaceAttribute::Invisible);
}
}

bgfx::VertexLayout IndoorDebugRenderer::TerrainVertex::ms_layout;
bgfx::VertexLayout IndoorDebugRenderer::TexturedVertex::ms_layout;

IndoorDebugRenderer::IndoorDebugRenderer()
    : m_isInitialized(false)
    , m_isRenderable(false)
    , m_indoorMapData(std::nullopt)
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
    , m_toggleTextureFilteringLatch(false)
    , m_toggleInspectLatch(false)
    , m_activateInspectLatch(false)
    , m_jumpHeld(false)
{
}

IndoorDebugRenderer::~IndoorDebugRenderer()
{
    shutdown();
}

bool IndoorDebugRenderer::initialize(
    Engine::AssetScaleTier assetScaleTier,
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const IndoorMapData &indoorMapData,
    const std::optional<IndoorTextureSet> &indoorTextureSet,
    const std::optional<DecorationBillboardSet> &indoorDecorationBillboardSet,
    const std::optional<ActorPreviewBillboardSet> &indoorActorPreviewBillboardSet,
    const std::optional<SpriteObjectBillboardSet> &indoorSpriteObjectBillboardSet,
    IndoorSceneRuntime &sceneRuntime,
    const ObjectTable &objectTable,
    const ChestTable &chestTable,
    const HouseTable &houseTable
)
{
    shutdown();
    m_isInitialized = true;
    m_map = map;
    m_assetScaleTier = assetScaleTier;
    m_monsterTable = monsterTable;
    m_objectTable = objectTable;
    m_indoorMapData = indoorMapData;
    m_pSceneRuntime = &sceneRuntime;
    m_renderVertices = buildMechanismAdjustedVertices(
        indoorMapData,
        runtimeMapDeltaData(),
        runtimeEventRuntimeStateStorage());
    m_indoorTextureSet = indoorTextureSet;
    m_indoorDecorationBillboardSet = indoorDecorationBillboardSet;
    m_indoorActorPreviewBillboardSet = indoorActorPreviewBillboardSet;
    m_indoorSpriteObjectBillboardSet = indoorSpriteObjectBillboardSet;
    m_chestTable = chestTable;
    m_houseTable = houseTable;
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

        if (!bgfx::isValid(m_entityMarkerVertexBufferHandle))
        {
            std::cerr << "IndoorDebugRenderer: failed to create entity marker vertex buffer\n";
            shutdown();
            return false;
        }
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

        if (!bgfx::isValid(m_spawnMarkerVertexBufferHandle))
        {
            std::cerr << "IndoorDebugRenderer: failed to create spawn marker vertex buffer\n";
            shutdown();
            return false;
        }
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
            billboardTexture.physicalWidth = texture.physicalWidth;
            billboardTexture.physicalHeight = texture.physicalHeight;
            billboardTexture.textureHandle = createBgraTexture2D(
                uint16_t(texture.physicalWidth),
                uint16_t(texture.physicalHeight),
                texture.pixels.data(),
                uint32_t(texture.pixels.size()),
                TextureFilterProfile::Billboard,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
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
            billboardTexture.physicalWidth = texture.physicalWidth;
            billboardTexture.physicalHeight = texture.physicalHeight;
            billboardTexture.textureHandle = createBgraTexture2D(
                uint16_t(texture.physicalWidth),
                uint16_t(texture.physicalHeight),
                texture.pixels.data(),
                uint32_t(texture.pixels.size()),
                TextureFilterProfile::Billboard,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
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
            billboardTexture.physicalWidth = texture.physicalWidth;
            billboardTexture.physicalHeight = texture.physicalHeight;
            billboardTexture.textureHandle = createBgraTexture2D(
                uint16_t(texture.physicalWidth),
                uint16_t(texture.physicalHeight),
                texture.pixels.data(),
                uint32_t(texture.pixels.size()),
                TextureFilterProfile::Billboard,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP
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
        std::cerr << "IndoorDebugRenderer: failed to create debug program handle\n";
        shutdown();
        return false;
    }

    if (!bgfx::isValid(m_texturedProgramHandle))
    {
        std::cerr << "IndoorDebugRenderer: failed to create textured program handle\n";
        shutdown();
        return false;
    }

    if (!bgfx::isValid(m_textureSamplerHandle))
    {
        std::cerr << "IndoorDebugRenderer: failed to create texture sampler uniform\n";
        shutdown();
        return false;
    }

    if (!rebuildDerivedGeometryResources())
    {
        std::cerr << "IndoorDebugRenderer: failed to rebuild derived geometry resources during initialize\n";
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

    if (m_pSceneRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        m_cameraPositionX = moveState.x;
        m_cameraPositionY = moveState.y;
        m_cameraPositionZ = moveState.eyeZ();
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
    if (hasFaceAttribute(face.attributes, FaceAttribute::Invisible))
    {
        return false;
    }

    return !faceHasInvisibleOverride(faceIndex, eventRuntimeState);
}

std::vector<uint8_t> IndoorDebugRenderer::buildVisibleSectorMask(const bx::Vec3 &cameraPosition) const
{
    (void)cameraPosition;

    if (!m_indoorMapData || m_indoorMapData->sectors.empty())
    {
        return {};
    }

    std::vector<uint8_t> visibleSectorMask(m_indoorMapData->sectors.size(), 0);
    int16_t startSectorId = -1;

    if (m_pSceneRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();

        if (moveState.eyeSectorId >= 0 && static_cast<size_t>(moveState.eyeSectorId) < visibleSectorMask.size())
        {
            startSectorId = moveState.eyeSectorId;
        }
        else if (moveState.sectorId >= 0 && static_cast<size_t>(moveState.sectorId) < visibleSectorMask.size())
        {
            startSectorId = moveState.sectorId;
        }
    }

    if (startSectorId < 0)
    {
        m_cachedVisibleSectorId = -1;
        m_cachedVisibleDoorStateSignature.clear();
        m_cachedVisibleSectorMask.clear();
        return {};
    }

    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();
    const std::vector<uint32_t> doorStateSignature =
        buildDoorStateSignature(runtimeMapDeltaData(), eventRuntimeState);

    if (m_cachedVisibleSectorId == startSectorId && m_cachedVisibleDoorStateSignature == doorStateSignature)
    {
        return m_cachedVisibleSectorMask;
    }

    std::vector<int16_t> pendingSectorIds;
    pendingSectorIds.push_back(startSectorId);

    while (!pendingSectorIds.empty())
    {
        const int16_t sectorId = pendingSectorIds.back();
        pendingSectorIds.pop_back();

        if (sectorId < 0 || static_cast<size_t>(sectorId) >= visibleSectorMask.size())
        {
            continue;
        }

        if (visibleSectorMask[sectorId] != 0)
        {
            continue;
        }

        visibleSectorMask[sectorId] = 1;
        const IndoorSector &sector = m_indoorMapData->sectors[sectorId];

        auto appendPortalConnectedSectors = [&](const std::vector<uint16_t> &faceIds)
        {
            for (uint16_t faceId : faceIds)
            {
                if (faceId >= m_indoorMapData->faces.size())
                {
                    continue;
                }

                const IndoorFace &face = m_indoorMapData->faces[faceId];

                if (!face.isPortal && !hasFaceAttribute(face.attributes, FaceAttribute::IsPortal))
                {
                    continue;
                }

                if (!isFaceVisible(faceId, face, eventRuntimeState))
                {
                    continue;
                }

                int16_t connectedSectorId = -1;

                if (face.roomNumber == sectorId)
                {
                    connectedSectorId = static_cast<int16_t>(face.roomBehindNumber);
                }
                else if (face.roomBehindNumber == sectorId)
                {
                    connectedSectorId = static_cast<int16_t>(face.roomNumber);
                }

                if (connectedSectorId < 0 || static_cast<size_t>(connectedSectorId) >= visibleSectorMask.size())
                {
                    continue;
                }

                if (visibleSectorMask[connectedSectorId] == 0)
                {
                    pendingSectorIds.push_back(connectedSectorId);
                }
            }
        };

        appendPortalConnectedSectors(sector.portalFaceIds);
        appendPortalConnectedSectors(sector.faceIds);
    }

    m_cachedVisibleSectorId = startSectorId;
    m_cachedVisibleDoorStateSignature = doorStateSignature;
    m_cachedVisibleSectorMask = visibleSectorMask;
    return visibleSectorMask;
}

bool IndoorDebugRenderer::isSectorVisible(int16_t sectorId, const std::vector<uint8_t> &visibleSectorMask) const
{
    if (visibleSectorMask.empty())
    {
        return true;
    }

    return sectorId >= 0
        && static_cast<size_t>(sectorId) < visibleSectorMask.size()
        && visibleSectorMask[sectorId] != 0;
}

bool IndoorDebugRenderer::isBatchVisible(
    const TexturedBatch &batch,
    const std::vector<uint8_t> &visibleSectorMask
) const
{
    if (visibleSectorMask.empty())
    {
        return true;
    }

    if (isSectorVisible(batch.sectorId, visibleSectorMask) || isSectorVisible(batch.backSectorId, visibleSectorMask))
    {
        return true;
    }

    return batch.sectorId < 0 && batch.backSectorId < 0;
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

    if (m_pSceneRuntime != nullptr && m_pSceneRuntime->advanceSimulation(deltaMilliseconds))
    {
        rebuildDerivedGeometryResources();
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
    const std::vector<uint8_t> visibleSectorMask = buildVisibleSectorMask(eye);

    InspectHit inspectHit = {};
    float mouseX = 0.0f;
    float mouseY = 0.0f;

    if (m_inspectMode && m_indoorMapData)
    {
        SDL_GetMouseState(&mouseX, &mouseY);

        if (m_gameplayMouseLookEnabled && !m_gameplayCursorMode)
        {
            mouseX = static_cast<float>(viewWidth) * 0.5f;
            mouseY = static_cast<float>(viewHeight) * 0.5f;
        }

        const float normalizedMouseX = ((mouseX / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
        const float normalizedMouseY = 1.0f - ((mouseY / static_cast<float>(viewHeight)) * 2.0f);
        float viewProjectionMatrix[16] = {};
        float inverseViewProjectionMatrix[16] = {};
        bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);
        bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);
        const bx::Vec3 rayOrigin = bx::mulH({normalizedMouseX, normalizedMouseY, 0.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayTarget = bx::mulH({normalizedMouseX, normalizedMouseY, 1.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayDirection = vecNormalize(vecSubtract(rayTarget, rayOrigin));
        const uint64_t inspectTick = SDL_GetTicks();
        constexpr uint64_t InspectRefreshIntervalMs = 16;
        const bool inspectViewChanged =
            !m_cachedInspectHitValid
            || m_cachedInspectGeometryRevision != m_inspectGeometryRevision
            || std::fabs(m_cachedInspectMouseX - mouseX) > 0.5f
            || std::fabs(m_cachedInspectMouseY - mouseY) > 0.5f
            || std::fabs(m_cachedInspectCameraX - eye.x) > 0.25f
            || std::fabs(m_cachedInspectCameraY - eye.y) > 0.25f
            || std::fabs(m_cachedInspectCameraZ - eye.z) > 0.25f
            || std::fabs(m_cachedInspectYawRadians - m_cameraYawRadians) > 0.0005f
            || std::fabs(m_cachedInspectPitchRadians - m_cameraPitchRadians) > 0.0005f;

        if (inspectViewChanged
            && (inspectTick - m_lastInspectUpdateTick >= InspectRefreshIntervalMs || !m_cachedInspectHitValid))
        {
            m_cachedInspectHit = inspectAtCursor(
                *m_indoorMapData,
                m_renderVertices,
                visibleSectorMask,
                rayOrigin,
                rayDirection);
            m_cachedInspectHitValid = true;
            m_cachedInspectMouseX = mouseX;
            m_cachedInspectMouseY = mouseY;
            m_cachedInspectCameraX = eye.x;
            m_cachedInspectCameraY = eye.y;
            m_cachedInspectCameraZ = eye.z;
            m_cachedInspectYawRadians = m_cameraYawRadians;
            m_cachedInspectPitchRadians = m_cameraPitchRadians;
            m_cachedInspectGeometryRevision = m_inspectGeometryRevision;
            m_lastInspectUpdateTick = inspectTick;
        }

        inspectHit = m_cachedInspectHit;

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
                m_cachedInspectHit = inspectAtCursor(
                    *m_indoorMapData,
                    m_renderVertices,
                    visibleSectorMask,
                    rayOrigin,
                    rayDirection);
                m_cachedInspectHitValid = true;
                m_cachedInspectMouseX = mouseX;
                m_cachedInspectMouseY = mouseY;
                m_cachedInspectCameraX = eye.x;
                m_cachedInspectCameraY = eye.y;
                m_cachedInspectCameraZ = eye.z;
                m_cachedInspectYawRadians = m_cameraYawRadians;
                m_cachedInspectPitchRadians = m_cameraPitchRadians;
                m_cachedInspectGeometryRevision = m_inspectGeometryRevision;
                m_lastInspectUpdateTick = inspectTick;
                inspectHit = m_cachedInspectHit;
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
            if (!bgfx::isValid(batch.vertexBufferHandle) || batch.frameTextureHandles.empty() || batch.vertexCount == 0)
            {
                continue;
            }

            if (!isBatchVisible(batch, visibleSectorMask))
            {
                continue;
            }

            const size_t frameIndex = frameIndexForAnimation(
                batch.frameLengthTicks,
                batch.animationLengthTicks,
                currentAnimationTicks());

            if (frameIndex >= batch.frameTextureHandles.size()
                || !bgfx::isValid(batch.frameTextureHandles[frameIndex]))
            {
                continue;
            }

            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, batch.vertexBufferHandle, 0, batch.vertexCount);
            bindTexture(
                0,
                m_textureSamplerHandle,
                batch.frameTextureHandles[frameIndex],
                TextureFilterProfile::BModel);
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
        renderDecorationBillboards(MainViewId, viewMatrix, eye, visibleSectorMask);
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
        renderActorPreviewBillboards(MainViewId, viewMatrix, eye, visibleSectorMask);
    }

    if (m_showSpriteObjects)
    {
        renderSpriteObjectBillboards(MainViewId, viewMatrix, eye, visibleSectorMask);
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
        "Modes: 1 filled=%s  2 wire=%s  3 portals=%s  4 sprites=%s  5 actors=%s  6 objs=%s  7 ents=%s  8 spawns=%s  9 mechs=%s  0 inspect=%s  F7 filter=%s  textured=%s",
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
        textureFilteringEnabled() ? "on" : "off",
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
        runtimeMapDeltaData() ? static_cast<unsigned>(runtimeMapDeltaData()->doors.size()) : 0u
    );
    if (m_inspectMode)
    {
        bgfx::dbgTextPrintf(0, 8, 0x0f, "Activate: LeftClick/E");

        if (inspectHit.hasHit)
        {
            const std::optional<ScriptedEventProgram> &localEventProgram =
                m_pSceneRuntime != nullptr ? m_pSceneRuntime->localEventProgram() : std::optional<ScriptedEventProgram>{};
            const std::optional<ScriptedEventProgram> &globalEventProgram =
                m_pSceneRuntime != nullptr ? m_pSceneRuntime->globalEventProgram() : std::optional<ScriptedEventProgram>{};

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
                    localEventProgram,
                    globalEventProgram
                );
                const std::string secondaryEventSummary = summarizeLinkedEvent(
                    inspectHit.eventIdSecondary,
                    m_houseTable,
                    localEventProgram,
                    globalEventProgram
                );
                const std::string primaryChestSummary = summarizeLinkedChests(
                    inspectHit.eventIdPrimary,
                    runtimeMapDeltaData(),
                    m_chestTable,
                    localEventProgram,
                    globalEventProgram
                );
                const std::string secondaryChestSummary = summarizeLinkedChests(
                    inspectHit.eventIdSecondary,
                    runtimeMapDeltaData(),
                    m_chestTable,
                    localEventProgram,
                    globalEventProgram
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
                    localEventProgram,
                    globalEventProgram
                );
                const std::string faceChestSummary = summarizeLinkedChests(
                    inspectHit.cogTriggered,
                    runtimeMapDeltaData(),
                    m_chestTable,
                    localEventProgram,
                    globalEventProgram
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
                    runtimeMapDeltaData(),
                    m_chestTable,
                    localEventProgram,
                    globalEventProgram
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

            if (const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();
                pEventRuntimeState != nullptr && pEventRuntimeState->lastActivationResult)
            {
                const uint16_t activationLine = inspectHit.kind == "mechanism" ? 13 : 12;
                bgfx::dbgTextPrintf(
                    0,
                    activationLine,
                    0x0f,
                    "Activate: %s",
                    pEventRuntimeState->lastActivationResult->c_str());

                if (!pEventRuntimeState->lastAffectedMechanismIds.empty())
                {
                    std::string mechanismsLine = "Affected mechs:";

                    for (uint32_t mechanismId : pEventRuntimeState->lastAffectedMechanismIds)
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

            if (const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();
                pEventRuntimeState != nullptr && pEventRuntimeState->lastActivationResult)
            {
                bgfx::dbgTextPrintf(0, 9, 0x0f, "Activate: %s", pEventRuntimeState->lastActivationResult->c_str());

                if (!pEventRuntimeState->lastAffectedMechanismIds.empty())
                {
                    std::string mechanismsLine = "Affected mechs:";

                    for (uint32_t mechanismId : pEventRuntimeState->lastAffectedMechanismIds)
                    {
                        mechanismsLine += " " + std::to_string(mechanismId);
                    }

                    bgfx::dbgTextPrintf(0, 10, 0x0f, "%s", mechanismsLine.c_str());
                }
            }
        }
    }
}

bool IndoorDebugRenderer::hasHudRenderResources() const
{
    return bgfx::isValid(m_texturedProgramHandle) && bgfx::isValid(m_textureSamplerHandle);
}

bgfx::ProgramHandle IndoorDebugRenderer::hudTexturedProgramHandle() const
{
    return m_texturedProgramHandle;
}

bgfx::UniformHandle IndoorDebugRenderer::hudTextureSamplerHandle() const
{
    return m_textureSamplerHandle;
}

void IndoorDebugRenderer::prepareHudView(int width, int height) const
{
    if (!hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }

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
}

void IndoorDebugRenderer::submitHudTextureQuad(
    bgfx::TextureHandle textureHandle,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    float u0,
    float v0,
    float u1,
    float v1,
    TextureFilterProfile filterProfile) const
{
    if (!hasHudRenderResources()
        || !bgfx::isValid(textureHandle)
        || quadWidth <= 0.0f
        || quadHeight <= 0.0f)
    {
        return;
    }

    bgfx::TransientVertexBuffer vertexBuffer = {};
    bgfx::TransientIndexBuffer indexBuffer = {};

    if (!bgfx::allocTransientBuffers(&vertexBuffer, TexturedVertex::ms_layout, 4, &indexBuffer, 6))
    {
        return;
    }

    TexturedVertex *pVertices = reinterpret_cast<TexturedVertex *>(vertexBuffer.data);
    pVertices[0] = {x, y, 0.0f, u0, v0};
    pVertices[1] = {x + quadWidth, y, 0.0f, u1, v0};
    pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1};
    pVertices[3] = {x, y + quadHeight, 0.0f, u0, v1};

    uint16_t *pIndices = reinterpret_cast<uint16_t *>(indexBuffer.data);
    pIndices[0] = 0;
    pIndices[1] = 1;
    pIndices[2] = 2;
    pIndices[3] = 0;
    pIndices[4] = 2;
    pIndices[5] = 3;

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &vertexBuffer);
    bgfx::setIndexBuffer(&indexBuffer);
    bindTexture(
        0,
        m_textureSamplerHandle,
        textureHandle,
        filterProfile,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(HudViewId, m_texturedProgramHandle);
}

void IndoorDebugRenderer::setGameplayMouseLookMode(bool enabled, bool cursorMode)
{
    m_gameplayMouseLookEnabled = enabled;
    m_gameplayCursorMode = cursorMode;
}

std::optional<IndoorDebugRenderer::GameplayActorPick>
IndoorDebugRenderer::gameplayActorPickAtCursor(
    int viewWidth,
    int viewHeight,
    float screenX,
    float screenY) const
{
    if (!m_isInitialized
        || !m_isRenderable
        || !m_indoorMapData
        || m_pSceneRuntime == nullptr
        || viewWidth <= 0
        || viewHeight <= 0)
    {
        return std::nullopt;
    }

    const float aspectRatio =
        static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    const bx::Vec3 eye = {
        m_cameraPositionX,
        m_cameraPositionY,
        m_cameraPositionZ
    };
    const bx::Vec3 at = {
        m_cameraPositionX + cosYaw * cosPitch,
        m_cameraPositionY - sinYaw * cosPitch,
        m_cameraPositionZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    float viewProjectionMatrix[16] = {};
    float inverseViewProjectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up);
    bx::mtxProj(
        projectionMatrix,
        60.0f,
        aspectRatio,
        0.1f,
        50000.0f,
        bgfx::getCaps()->homogeneousDepth
    );
    bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);
    bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);

    const float normalizedMouseX = ((screenX / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
    const float normalizedMouseY = 1.0f - ((screenY / static_cast<float>(viewHeight)) * 2.0f);
    const bx::Vec3 rayOrigin =
        bx::mulH({normalizedMouseX, normalizedMouseY, 0.0f}, inverseViewProjectionMatrix);
    const bx::Vec3 rayTarget =
        bx::mulH({normalizedMouseX, normalizedMouseY, 1.0f}, inverseViewProjectionMatrix);
    const bx::Vec3 rayDirection = vecNormalize(vecSubtract(rayTarget, rayOrigin));

    if (vecLength(rayDirection) <= InspectRayEpsilon)
    {
        return std::nullopt;
    }

    const std::vector<uint8_t> visibleSectorMask = buildVisibleSectorMask(eye);
    const InspectHit inspectHit =
        inspectAtCursor(*m_indoorMapData, m_renderVertices, visibleSectorMask, rayOrigin, rayDirection);

    if (!inspectHit.hasHit || inspectHit.kind != "actor")
    {
        return std::nullopt;
    }

    GameplayRuntimeActorState actorState = {};

    if (!m_pSceneRuntime->worldRuntime().actorRuntimeState(inspectHit.index, actorState))
    {
        return std::nullopt;
    }

    const float halfExtent = static_cast<float>(std::max<uint16_t>(actorState.radius, 32));
    const float actorHeight = static_cast<float>(std::max<uint16_t>(actorState.height, 96));
    const float minX = actorState.preciseX - halfExtent;
    const float maxX = actorState.preciseX + halfExtent;
    const float minY = actorState.preciseY - halfExtent;
    const float maxY = actorState.preciseY + halfExtent;
    const float minZ = actorState.preciseZ;
    const float maxZ = actorState.preciseZ + actorHeight;
    const std::array<bx::Vec3, 8> corners = {{
        {minX, minY, minZ},
        {maxX, minY, minZ},
        {minX, maxY, minZ},
        {maxX, maxY, minZ},
        {minX, minY, maxZ},
        {maxX, minY, maxZ},
        {minX, maxY, maxZ},
        {maxX, maxY, maxZ},
    }};

    bool hasProjectedPoint = false;
    float rectMinX = 0.0f;
    float rectMinY = 0.0f;
    float rectMaxX = 0.0f;
    float rectMaxY = 0.0f;

    for (const bx::Vec3 &corner : corners)
    {
        ProjectedPoint projected = {};

        if (!projectWorldPointToScreen(corner, viewWidth, viewHeight, viewProjectionMatrix, projected))
        {
            continue;
        }

        if (!hasProjectedPoint)
        {
            rectMinX = projected.x;
            rectMinY = projected.y;
            rectMaxX = projected.x;
            rectMaxY = projected.y;
            hasProjectedPoint = true;
            continue;
        }

        rectMinX = std::min(rectMinX, projected.x);
        rectMinY = std::min(rectMinY, projected.y);
        rectMaxX = std::max(rectMaxX, projected.x);
        rectMaxY = std::max(rectMaxY, projected.y);
    }

    if (!hasProjectedPoint)
    {
        return std::nullopt;
    }

    GameplayActorPick pick = {};
    pick.runtimeActorIndex = inspectHit.index;
    pick.sourceX = rectMinX;
    pick.sourceY = rectMinY;
    pick.sourceWidth = std::max(1.0f, rectMaxX - rectMinX);
    pick.sourceHeight = std::max(1.0f, rectMaxY - rectMinY);
    return pick;
}

void IndoorDebugRenderer::shutdown()
{
    m_indoorMapData.reset();
    m_renderVertices.clear();
    m_pSceneRuntime = nullptr;
    m_indoorTextureSet.reset();
    m_map.reset();
    m_monsterTable.reset();
    m_indoorDecorationBillboardSet.reset();
    m_indoorActorPreviewBillboardSet.reset();
    m_indoorSpriteObjectBillboardSet.reset();
    m_houseTable.reset();
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
    m_toggleTextureFilteringLatch = false;
    m_toggleInspectLatch = false;
    m_isRenderable = false;
    m_isInitialized = false;
}

const std::optional<MapDeltaData> &IndoorDebugRenderer::runtimeMapDeltaData() const
{
    static const std::optional<MapDeltaData> EmptyMapDeltaData = std::nullopt;
    return m_pSceneRuntime != nullptr ? m_pSceneRuntime->mapDeltaData() : EmptyMapDeltaData;
}

const std::optional<EventRuntimeState> &IndoorDebugRenderer::runtimeEventRuntimeStateStorage() const
{
    static const std::optional<EventRuntimeState> EmptyEventRuntimeState = std::nullopt;
    return m_pSceneRuntime != nullptr ? m_pSceneRuntime->eventRuntimeStateStorage() : EmptyEventRuntimeState;
}

EventRuntimeState *IndoorDebugRenderer::runtimeEventRuntimeState()
{
    return m_pSceneRuntime != nullptr ? m_pSceneRuntime->eventRuntimeState() : nullptr;
}

const EventRuntimeState *IndoorDebugRenderer::runtimeEventRuntimeState() const
{
    return m_pSceneRuntime != nullptr ? m_pSceneRuntime->eventRuntimeState() : nullptr;
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
        std::cerr
            << "IndoorDebugRenderer: loadProgram failed"
            << " vs=" << (pVertexShaderName != nullptr ? pVertexShaderName : "<null>")
            << " fs=" << (pFragmentShaderName != nullptr ? pFragmentShaderName : "<null>")
            << '\n';
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

bgfx::ShaderHandle IndoorDebugRenderer::loadShader(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        std::cerr
            << "IndoorDebugRenderer: loadShader could not resolve shader path for "
            << (pShaderName != nullptr ? pShaderName : "<null>")
            << '\n';
        return BGFX_INVALID_HANDLE;
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        std::cerr
            << "IndoorDebugRenderer: loadShader read empty shader file "
            << shaderPath.string()
            << '\n';
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createShader(bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size())));
}

void IndoorDebugRenderer::setCameraPosition(float x, float y, float z)
{
    m_cameraPositionX = x;
    m_cameraPositionY = y;
    m_cameraPositionZ = z;

    if (m_pSceneRuntime != nullptr)
    {
        m_pSceneRuntime->partyRuntime().teleportEyePosition(x, y, z);
    }
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
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask
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
    const auto resolveBillboardSpriteId = [this](const DecorationBillboard &billboard, bool &hidden)
    {
        hidden = false;

        const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

        if (!m_indoorDecorationBillboardSet || !eventRuntimeState.has_value())
        {
            return billboard.spriteId;
        }

        const auto overrideIterator =
            eventRuntimeState->spriteOverrides.find(static_cast<uint32_t>(billboard.entityIndex));

        if (overrideIterator == eventRuntimeState->spriteOverrides.end())
        {
            return billboard.spriteId;
        }

        hidden = overrideIterator->second.hidden;

        if (!overrideIterator->second.textureName.has_value() || overrideIterator->second.textureName->empty())
        {
            return billboard.spriteId;
        }

        if (const DecorationEntry *pDecoration =
                m_indoorDecorationBillboardSet->decorationTable.findByInternalName(*overrideIterator->second.textureName))
        {
            return pDecoration->spriteId;
        }

        if (const std::optional<uint16_t> spriteId =
                m_indoorDecorationBillboardSet->spriteFrameTable.findFrameIndexBySpriteName(
                    *overrideIterator->second.textureName))
        {
            return *spriteId;
        }

        return billboard.spriteId;
    };

    for (const DecorationBillboard &billboard : m_indoorDecorationBillboardSet->billboards)
    {
        bool hidden = false;
        const uint16_t spriteId = resolveBillboardSpriteId(billboard, hidden);

        if (hidden || spriteId == 0)
        {
            continue;
        }

        const uint32_t animationOffsetTicks =
            animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
        const SpriteFrameEntry *pFrame =
            m_indoorDecorationBillboardSet->spriteFrameTable.getFrame(spriteId, animationOffsetTicks);

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
        bindTexture(
            0,
            m_textureSamplerHandle,
            texture.textureHandle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
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
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask
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
        size_t actorIndex = static_cast<size_t>(-1);
        int x = 0;
        int y = 0;
        int z = 0;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::vector<RuntimeActorBillboard> runtimeBillboards =
        mapDeltaData && m_monsterTable
        ? buildRuntimeActorBillboards(*m_monsterTable, m_indoorActorPreviewBillboardSet->spriteFrameTable, *mapDeltaData)
        : std::vector<RuntimeActorBillboard>{};
    std::vector<BillboardDrawItem> drawItems;
    const bool useRuntimeBillboards = !runtimeBillboards.empty();
    drawItems.reserve(
        useRuntimeBillboards
        ? runtimeBillboards.size()
        : m_indoorActorPreviewBillboardSet->billboards.size());

    if (useRuntimeBillboards)
    {
        for (const RuntimeActorBillboard &billboard : runtimeBillboards)
        {
            if (!isSectorVisible(billboard.sectorId, visibleSectorMask))
            {
                continue;
            }

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
            const BillboardTextureHandle *pTexture =
                findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                continue;
            }

            const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
            const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
            const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;

            BillboardDrawItem drawItem = {};
            drawItem.actorIndex = billboard.actorIndex;
            drawItem.x = billboard.x;
            drawItem.y = billboard.y;
            drawItem.z = billboard.z;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            drawItems.push_back(drawItem);
        }
    }
    else
    {
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
            const BillboardTextureHandle *pTexture =
                findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                continue;
            }

            const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
            const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
            const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;

            BillboardDrawItem drawItem = {};
            drawItem.x = billboard.x;
            drawItem.y = billboard.y;
            drawItem.z = billboard.z;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            drawItems.push_back(drawItem);
        }
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
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            static_cast<float>(drawItem.x),
            static_cast<float>(drawItem.y),
            static_cast<float>(drawItem.z) + worldHeight * 0.5f
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
        bindTexture(
            0,
            m_textureSamplerHandle,
            texture.textureHandle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
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
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask
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
        int x = 0;
        int y = 0;
        int z = 0;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
    };

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::vector<RuntimeSpriteObjectBillboard> runtimeBillboards =
        mapDeltaData && m_objectTable
        ? buildRuntimeSpriteObjectBillboards(*m_objectTable, *mapDeltaData)
        : std::vector<RuntimeSpriteObjectBillboard>{};
    std::vector<BillboardDrawItem> drawItems;
    const bool useRuntimeBillboards = !runtimeBillboards.empty();
    drawItems.reserve(
        useRuntimeBillboards
        ? runtimeBillboards.size()
        : m_indoorSpriteObjectBillboardSet->billboards.size());

    if (useRuntimeBillboards)
    {
        for (const RuntimeSpriteObjectBillboard &billboard : runtimeBillboards)
        {
            if (!isSectorVisible(billboard.sectorId, visibleSectorMask))
            {
                continue;
            }

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
            drawItem.x = billboard.x;
            drawItem.y = billboard.y;
            drawItem.z = billboard.z;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            drawItems.push_back(drawItem);
        }
    }
    else
    {
        for (const SpriteObjectBillboard &billboard : m_indoorSpriteObjectBillboardSet->billboards)
        {
            if (!isSectorVisible(billboard.sectorId, visibleSectorMask))
            {
                continue;
            }

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
            drawItem.x = billboard.x;
            drawItem.y = billboard.y;
            drawItem.z = billboard.z;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            drawItems.push_back(drawItem);
        }
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
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = float(texture.width) * spriteScale;
        const float worldHeight = float(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            float(drawItem.x),
            float(drawItem.y),
            float(drawItem.z) + worldHeight * 0.5f
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
        bindTexture(
            0,
            m_textureSamplerHandle,
            texture.textureHandle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
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
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    return !pEventRuntimeState->textureOverrides.empty()
        || !pEventRuntimeState->facetSetMasks.empty()
        || !pEventRuntimeState->facetClearMasks.empty();
}

void IndoorDebugRenderer::rebuildMechanismBindings()
{
    m_mechanismBindings.clear();
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::optional<ScriptedEventProgram> &localEventProgram =
        m_pSceneRuntime != nullptr ? m_pSceneRuntime->localEventProgram() : std::optional<ScriptedEventProgram>{};
    const std::optional<ScriptedEventProgram> &globalEventProgram =
        m_pSceneRuntime != nullptr ? m_pSceneRuntime->globalEventProgram() : std::optional<ScriptedEventProgram>{};

    if (!mapDeltaData || !m_indoorMapData)
    {
        return;
    }

    m_mechanismBindings.resize(mapDeltaData->doors.size());

    for (size_t doorIndex = 0; doorIndex < mapDeltaData->doors.size(); ++doorIndex)
    {
        const MapDeltaDoor &door = mapDeltaData->doors[doorIndex];
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

            if (localEventProgram && localEventProgram->hasEvent(linkedFace.cogTriggered))
            {
                hasLinkedEvent = true;
            }
            else if (globalEventProgram && globalEventProgram->hasEvent(linkedFace.cogTriggered))
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
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (!mapDeltaData || pEventRuntimeState == nullptr || !m_indoorMapData)
    {
        return faceIndices;
    }

    std::vector<bool> seen(m_indoorMapData->faces.size(), false);

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator iterator =
            pEventRuntimeState->mechanisms.find(door.doorId);

        if (iterator == pEventRuntimeState->mechanisms.end() || !iterator->second.isMoving)
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
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

    for (size_t faceIndex = 0; faceIndex < m_indoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_indoorMapData->faces[faceIndex];
        const std::string textureName = resolveFaceTextureName(face, eventRuntimeState);

        if (face.isPortal || textureName.empty() || face.vertexIndices.size() < 3)
        {
            continue;
        }

        if (!isFaceVisible(faceIndex, face, eventRuntimeState))
        {
            continue;
        }

        const std::string normalizedTextureName = toLowerCopy(textureName);
        const int16_t sectorId =
            face.roomNumber < m_indoorMapData->sectors.size() ? static_cast<int16_t>(face.roomNumber) : int16_t(-1);
        const int16_t backSectorId =
            face.roomBehindNumber < m_indoorMapData->sectors.size()
                ? static_cast<int16_t>(face.roomBehindNumber)
                : int16_t(-1);
        const std::string batchKey = normalizedTextureName
            + "#" + std::to_string(sectorId)
            + "#" + std::to_string(backSectorId);
        size_t batchIndex = 0;
        const std::unordered_map<std::string, size_t>::const_iterator batchIterator =
            batchIndicesByTexture.find(batchKey);

        if (batchIterator == batchIndicesByTexture.end())
        {
            TexturedBatch batch = {};
            batch.textureName = normalizedTextureName;
            batch.sectorId = sectorId;
            batch.backSectorId = backSectorId;

            for (TexturedBatch &previousBatch : previousBatches)
            {
                if (previousBatch.textureName == normalizedTextureName
                    && previousBatch.sectorId == sectorId
                    && previousBatch.backSectorId == backSectorId)
                {
                    batch.vertexBufferHandle = previousBatch.vertexBufferHandle;
                    batch.vertexCapacity = previousBatch.vertexCapacity;
                    previousBatch.vertexBufferHandle = BGFX_INVALID_HANDLE;
                    break;
                }
            }

            const SurfaceAnimationSequence *pAnimationBinding =
                findTextureAnimationBinding(m_indoorTextureSet->animationBindings, textureName);
            SurfaceAnimationSequence animation = {};

            if (pAnimationBinding != nullptr)
            {
                animation = *pAnimationBinding;
            }
            else
            {
                SurfaceAnimationFrame frame = {};
                frame.textureName = textureName;
                animation.frames.push_back(std::move(frame));
            }

            batch.animationLengthTicks = animation.animationLengthTicks;

            for (const SurfaceAnimationFrame &frame : animation.frames)
            {
                const bgfx::TextureHandle *pTextureHandle = findIndoorTextureHandle(frame.textureName);

                if (pTextureHandle != nullptr)
                {
                    batch.frameTextureHandles.push_back(*pTextureHandle);
                    batch.frameLengthTicks.push_back(frame.frameLengthTicks);
                    continue;
                }

                const OutdoorBitmapTexture *pFrameTexture = nullptr;

                for (const OutdoorBitmapTexture &candidate : m_indoorTextureSet->textures)
                {
                    if (toLowerCopy(candidate.textureName) == toLowerCopy(frame.textureName))
                    {
                        pFrameTexture = &candidate;
                        break;
                    }
                }

                if (pFrameTexture == nullptr)
                {
                    continue;
                }

                const bgfx::TextureHandle textureHandle = createBgraTexture2D(
                    uint16_t(pFrameTexture->physicalWidth),
                    uint16_t(pFrameTexture->physicalHeight),
                    pFrameTexture->pixels.data(),
                    uint32_t(pFrameTexture->pixels.size()),
                    TextureFilterProfile::BModel
                );

                if (!bgfx::isValid(textureHandle))
                {
                    continue;
                }

                IndoorTextureHandle textureHandleEntry = {};
                textureHandleEntry.textureName = toLowerCopy(frame.textureName);
                textureHandleEntry.textureHandle = textureHandle;
                m_indoorTextureHandles.push_back(std::move(textureHandleEntry));
                batch.frameTextureHandles.push_back(textureHandle);
                batch.frameLengthTicks.push_back(frame.frameLengthTicks);
            }

            batchIndex = m_texturedBatches.size();
            batchIndicesByTexture[batchKey] = batchIndex;
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
        const std::vector<TexturedVertex> faceVertices = buildFaceTexturedVertices(
            *m_indoorMapData,
            m_renderVertices,
            *pTexture,
            faceIndex,
            runtimeMapDeltaData(),
            eventRuntimeState
        );
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
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

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
        const std::vector<TexturedVertex> faceVertices = buildFaceTexturedVertices(
            *m_indoorMapData,
            m_renderVertices,
            *pTexture,
            faceIndex,
            runtimeMapDeltaData(),
            eventRuntimeState
        );
        texturedBuildNanoseconds += SDL_GetTicksNS() - faceBuildBeginTickCount;

        if (faceVertices.size() != vertexCount)
        {
            std::cerr
                << "IndoorDebugRenderer: moving mechanism face rebuild changed vertex count"
                << " face=" << faceIndex
                << " batch=" << batchIndex
                << " old=" << vertexCount
                << " new=" << faceVertices.size()
                << '\n';
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
    return buildIndoorMechanismAdjustedVertices(
        indoorMapData,
        indoorMapDeltaData ? &indoorMapDeltaData.value() : nullptr,
        eventRuntimeState ? &eventRuntimeState.value() : nullptr);
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
        std::cerr << "IndoorDebugRenderer: rebuildDerivedGeometryResources has no indoor map data\n";
        return false;
    }

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

    m_renderVertices = buildMechanismAdjustedVertices(*m_indoorMapData, mapDeltaData, eventRuntimeState);

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return true;
    }

    const std::vector<TerrainVertex> wireframeVertices =
        buildWireframeVertices(*m_indoorMapData, m_renderVertices, eventRuntimeState);
    const std::vector<TerrainVertex> portalVertices = buildPortalVertices(*m_indoorMapData, m_renderVertices);
    const std::vector<TerrainVertex> doorMarkerVertices =
        mapDeltaData
            ? buildDoorMarkerVertices(m_renderVertices, *mapDeltaData, eventRuntimeState)
            : std::vector<TerrainVertex>();

    if (!updateDynamicVertexBuffer(
            m_wireframeVertexBufferHandle,
            m_wireframeVertexCapacity,
            wireframeVertices,
            TerrainVertex::ms_layout))
    {
        std::cerr << "IndoorDebugRenderer: failed to update wireframe vertex buffer\n";
        return false;
    }
    m_wireframeVertexCount = static_cast<uint32_t>(wireframeVertices.size());

    if (!updateDynamicVertexBuffer(
            m_portalVertexBufferHandle,
            m_portalVertexCapacity,
            portalVertices,
            TerrainVertex::ms_layout))
    {
        std::cerr << "IndoorDebugRenderer: failed to update portal vertex buffer\n";
        return false;
    }
    m_portalVertexCount = static_cast<uint32_t>(portalVertices.size());

    if (!updateDynamicVertexBuffer(
            m_doorMarkerVertexBufferHandle,
            m_doorMarkerVertexCapacity,
            doorMarkerVertices,
            TerrainVertex::ms_layout))
    {
        std::cerr << "IndoorDebugRenderer: failed to update door marker vertex buffer\n";
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
                std::cerr << "IndoorDebugRenderer: rebuildAllTexturedBatches failed\n";
                return false;
            }
        }
        else
        {
            uint64_t texturedBuildNanoseconds = 0;
            uint64_t uploadNanoseconds = 0;

            if (!updateMovingMechanismFaceVertices(texturedBuildNanoseconds, uploadNanoseconds))
            {
                std::cerr
                    << "IndoorDebugRenderer: updateMovingMechanismFaceVertices failed, rebuilding textured batches\n";

                texturedBuildNanoseconds = 0;

                if (!rebuildAllTexturedBatches(texturedBuildNanoseconds))
                {
                    std::cerr << "IndoorDebugRenderer: rebuildAllTexturedBatches failed after moving update failure\n";
                    return false;
                }
            }
        }
    }

    ++m_inspectGeometryRevision;
    m_cachedInspectHitValid = false;
    return true;
}

bool IndoorDebugRenderer::tryActivateInspectEvent(const InspectHit &inspectHit)
{
    if (!m_indoorMapData || m_pSceneRuntime == nullptr)
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

    if (!m_pSceneRuntime->activateEvent(eventId, inspectHit.kind, inspectHit.index))
    {
        return false;
    }

    if (!rebuildDerivedGeometryResources())
    {
        EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

        if (pEventRuntimeState != nullptr)
        {
            pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " execute failed";
        }

        return false;
    }

    return true;
}

std::vector<IndoorDebugRenderer::TexturedVertex> IndoorDebugRenderer::buildTexturedVertices(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &transformedVertices,
    const OutdoorBitmapTexture &texture,
    const std::vector<size_t> *pFaceIndices,
    const std::optional<MapDeltaData> &indoorMapDeltaData,
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
            buildFaceTexturedVertices(
                indoorMapData,
                transformedVertices,
                texture,
                faceIndex,
                indoorMapDeltaData,
                eventRuntimeState
            );

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
    const std::optional<MapDeltaData> &indoorMapDeltaData,
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

    const std::optional<MechanismFaceTextureState> mechanismFaceTextureState =
        findMechanismFaceTextureState(faceIndex, indoorMapDeltaData, eventRuntimeState);
    std::vector<float> projectedUs;
    std::vector<float> projectedVs;
    float projectedDeltaU = 0.0f;
    float projectedDeltaV = 0.0f;

    if (mechanismFaceTextureState)
    {
        const bx::Vec3 faceNormal = computeFaceNormal(transformedVertices, face);
        bx::Vec3 axisU = {0.0f, 0.0f, 0.0f};
        bx::Vec3 axisV = {0.0f, 0.0f, 0.0f};

        if (vecDot(faceNormal, faceNormal) <= 0.0001f || !calculateFaceTextureAxes(face, vecNormalize(faceNormal), axisU, axisV))
        {
            return vertices;
        }

        projectedUs.reserve(face.vertexIndices.size());
        projectedVs.reserve(face.vertexIndices.size());
        float minU = std::numeric_limits<float>::infinity();
        float minV = std::numeric_limits<float>::infinity();
        float maxU = -std::numeric_limits<float>::infinity();
        float maxV = -std::numeric_limits<float>::infinity();

        for (uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= transformedVertices.size())
            {
                return vertices;
            }

            const IndoorVertex &vertex = transformedVertices[vertexIndex];
            const bx::Vec3 point = {
                static_cast<float>(vertex.x),
                static_cast<float>(vertex.y),
                static_cast<float>(vertex.z)
            };
            const float pointU = vecDot(point, axisU);
            const float pointV = vecDot(point, axisV);
            projectedUs.push_back(pointU);
            projectedVs.push_back(pointV);
            minU = std::min(minU, pointU);
            minV = std::min(minV, pointV);
            maxU = std::max(maxU, pointU);
            maxV = std::max(maxV, pointV);
        }

        if (hasFaceAttribute(face.attributes, FaceAttribute::TextureAlignLeft))
        {
            projectedDeltaU -= minU;
        }
        else if (hasFaceAttribute(face.attributes, FaceAttribute::TextureAlignRight))
        {
            projectedDeltaU -= maxU + static_cast<float>(texture.width);
        }

        if (hasFaceAttribute(face.attributes, FaceAttribute::TextureAlignDown))
        {
            projectedDeltaV -= minV;
        }
        else if (hasFaceAttribute(face.attributes, FaceAttribute::TextureAlignBottom))
        {
            projectedDeltaV -= maxV + static_cast<float>(texture.height);
        }

        if (hasFaceAttribute(face.attributes, FaceAttribute::TextureMoveByDoor))
        {
            projectedDeltaU =
                -vecDot(mechanismFaceTextureState->direction, axisU) * mechanismFaceTextureState->distance;
            projectedDeltaV =
                -vecDot(mechanismFaceTextureState->direction, axisV) * mechanismFaceTextureState->distance;

            if (mechanismFaceTextureState->pDoor != nullptr)
            {
                if (mechanismFaceTextureState->faceOffset < mechanismFaceTextureState->pDoor->deltaUs.size())
                {
                    projectedDeltaU += static_cast<float>(
                        mechanismFaceTextureState->pDoor->deltaUs[mechanismFaceTextureState->faceOffset]
                    );
                }

                if (mechanismFaceTextureState->faceOffset < mechanismFaceTextureState->pDoor->deltaVs.size())
                {
                    projectedDeltaV += static_cast<float>(
                        mechanismFaceTextureState->pDoor->deltaVs[mechanismFaceTextureState->faceOffset]
                    );
                }
            }
        }
    }

    std::vector<std::array<size_t, 3>> triangleVertexOrders;

    if (!triangulateFaceProjected(transformedVertices, face, triangleVertexOrders))
    {
        for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
        {
            triangleVertexOrders.push_back({0, triangleIndex, triangleIndex + 1});
        }
    }

    for (const std::array<size_t, 3> &triangleVertexIndices : triangleVertexOrders)
    {
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

            if (mechanismFaceTextureState
                && faceVertexIndex < projectedUs.size()
                && faceVertexIndex < projectedVs.size())
            {
                texturedVertex.u = (projectedUs[faceVertexIndex] + projectedDeltaU) / static_cast<float>(texture.width);
                texturedVertex.v = (projectedVs[faceVertexIndex] + projectedDeltaV) / static_cast<float>(texture.height);
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

        const bx::Vec3 triangleEdge1 = {
            triangleVertices[1].x - triangleVertices[0].x,
            triangleVertices[1].y - triangleVertices[0].y,
            triangleVertices[1].z - triangleVertices[0].z
        };
        const bx::Vec3 triangleEdge2 = {
            triangleVertices[2].x - triangleVertices[0].x,
            triangleVertices[2].y - triangleVertices[0].y,
            triangleVertices[2].z - triangleVertices[0].z
        };
        const bx::Vec3 triangleNormal = vecCross(triangleEdge1, triangleEdge2);

        if (vecDot(triangleNormal, triangleNormal) <= 0.0001f)
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
    const std::vector<uint8_t> &visibleSectorMask,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection) const
{
    InspectHit bestHit = {};
    float bestDistance = std::numeric_limits<float>::max();
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = indoorMapData.faces[faceIndex];

        if (face.vertexIndices.size() < 3)
        {
            continue;
        }

        if (!isFaceVisible(faceIndex, face, eventRuntimeState))
        {
            continue;
        }

        if (!visibleSectorMask.empty()
            && !isSectorVisible(static_cast<int16_t>(face.roomNumber), visibleSectorMask)
            && !isSectorVisible(static_cast<int16_t>(face.roomBehindNumber), visibleSectorMask))
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

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

    if (mapDeltaData && m_monsterTable && m_indoorActorPreviewBillboardSet)
    {
        const std::vector<RuntimeActorBillboard> runtimeActors =
            buildRuntimeActorBillboards(*m_monsterTable, m_indoorActorPreviewBillboardSet->spriteFrameTable, *mapDeltaData);

        for (const RuntimeActorBillboard &actor : runtimeActors)
        {
            if (!isSectorVisible(actor.sectorId, visibleSectorMask))
            {
                continue;
            }

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
                bestHit.index = actor.actorIndex;
                bestHit.name = actor.actorName;
                bestHit.textureName.clear();
                bestHit.distance = distance;
                bestHit.isFriendly = actor.isFriendly;
                bestHit.spawnSummary.clear();
                bestHit.spawnDetail.clear();
            }
        }
    }

    if (mapDeltaData && m_objectTable)
    {
        const std::vector<RuntimeSpriteObjectBillboard> runtimeObjects =
            buildRuntimeSpriteObjectBillboards(*m_objectTable, *mapDeltaData);

        for (const RuntimeSpriteObjectBillboard &object : runtimeObjects)
        {
            if (!isSectorVisible(object.sectorId, visibleSectorMask))
            {
                continue;
            }

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
                bestHit.index = object.objectIndex;
                bestHit.name = object.objectName;
                bestHit.distance = distance;
                bestHit.objectDescriptionId = object.objectDescriptionId;
                bestHit.objectSpriteId = object.objectSpriteId;
                bestHit.attributes = object.attributes;
                bestHit.spellId = object.spellId;
            }
        }
    }

    if (mapDeltaData)
    {
        for (size_t doorIndex = 0; doorIndex < mapDeltaData->doors.size(); ++doorIndex)
        {
            const MapDeltaDoor &door = mapDeltaData->doors[doorIndex];

            if (!visibleSectorMask.empty())
            {
                bool sectorVisible = door.sectorIds.empty();

                for (uint16_t sectorId : door.sectorIds)
                {
                    if (isSectorVisible(static_cast<int16_t>(sectorId), visibleSectorMask))
                    {
                        sectorVisible = true;
                        break;
                    }
                }

                if (!sectorVisible)
                {
                    continue;
                }
            }

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
    const bool shouldRotateCamera = m_gameplayMouseLookEnabled && !m_gameplayCursorMode;

    if (shouldRotateCamera)
    {
        if (m_gameplayMouseLookEnabled)
        {
            float relativeMouseX = 0.0f;
            float relativeMouseY = 0.0f;
            SDL_GetRelativeMouseState(&relativeMouseX, &relativeMouseY);

            if (relativeMouseX != 0.0f || relativeMouseY != 0.0f)
            {
                m_cameraYawRadians -= relativeMouseX * mouseRotateSpeed;
                m_cameraPitchRadians -= relativeMouseY * mouseRotateSpeed;
            }
        }
        else if (m_isRotatingCamera)
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
    const bool jumpPressed = pKeyboardState[SDL_SCANCODE_X];
    const bool jumpRequested = jumpPressed && !m_jumpHeld;
    m_jumpHeld = jumpPressed;
    const float currentMoveSpeed = isFastMovePressed ? moveSpeed * fastMoveMultiplier : moveSpeed;
    float desiredVelocityX = 0.0f;
    float desiredVelocityY = 0.0f;

    if (pKeyboardState[SDL_SCANCODE_W])
    {
        desiredVelocityX += cosYaw * currentMoveSpeed;
        desiredVelocityY += -sinYaw * currentMoveSpeed;
    }

    if (pKeyboardState[SDL_SCANCODE_S])
    {
        desiredVelocityX -= cosYaw * currentMoveSpeed;
        desiredVelocityY -= -sinYaw * currentMoveSpeed;
    }

    if (pKeyboardState[SDL_SCANCODE_A])
    {
        desiredVelocityX -= right.x * currentMoveSpeed;
        desiredVelocityY -= right.y * currentMoveSpeed;
    }

    if (pKeyboardState[SDL_SCANCODE_D])
    {
        desiredVelocityX += right.x * currentMoveSpeed;
        desiredVelocityY += right.y * currentMoveSpeed;
    }

    if (m_pSceneRuntime != nullptr)
    {
        m_pSceneRuntime->partyRuntime().update(desiredVelocityX, desiredVelocityY, jumpRequested, deltaSeconds);
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        m_cameraPositionX = moveState.x;
        m_cameraPositionY = moveState.y;
        m_cameraPositionZ = moveState.eyeZ();
    }
    else
    {
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

    if (pKeyboardState[SDL_SCANCODE_F7])
    {
        if (!m_toggleTextureFilteringLatch)
        {
            toggleTextureFilteringEnabled();
            m_toggleTextureFilteringLatch = true;
        }
    }
    else
    {
        m_toggleTextureFilteringLatch = false;
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
