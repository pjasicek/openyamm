#include "game/indoor/IndoorRenderer.h"

#include "game/app/GameSession.h"
#include "game/data/ActorNameResolver.h"
#include "game/FaceEnums.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ParticleRenderer.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/render/TextureFiltering.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/SpriteObjectDefs.h"
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
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
bool hasMovingMechanism(const EventRuntimeState *pEventRuntimeState)
{
    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    for (const auto &entry : pEventRuntimeState->mechanisms)
    {
        const RuntimeMechanismState &mechanism = entry.second;

        if (mechanism.isMoving)
        {
            return true;
        }
    }

    return false;
}

int snapIndoorSpawnZToFloor(const IndoorMapData &indoorMapData, int x, int y, int z)
{
    IndoorFaceGeometryCache geometryCache(indoorMapData.faces.size());
    const std::optional<int16_t> sectorId = findIndoorSectorForPoint(
        indoorMapData,
        indoorMapData.vertices,
        {static_cast<float>(x), static_cast<float>(y), static_cast<float>(z)},
        &geometryCache);
    const IndoorFloorSample floor = sampleIndoorFloor(
        indoorMapData,
        indoorMapData.vertices,
        static_cast<float>(x),
        static_cast<float>(y),
        static_cast<float>(z),
        131072.0f,
        0.0f,
        sectorId,
        nullptr,
        &geometryCache);

    if (!floor.hasFloor || floor.height <= static_cast<float>(z))
    {
        return z;
    }

    return static_cast<int>(std::lround(floor.height));
}

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
constexpr size_t MaxIndoorShaderLights = 8;
constexpr float Pi = 3.14159265358979323846f;
constexpr float InspectRayEpsilon = 0.0001f;
constexpr float HoveredActorOutlineThicknessPixels = 2.0f;

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
    std::array<uint16_t, 8> actionSpriteFrameIndices = {};
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
    bool hasContainingItem = false;
    std::string objectName;
};

struct ProjectedPoint
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct IndoorBounds
{
    bx::Vec3 min = {0.0f, 0.0f, 0.0f};
    bx::Vec3 max = {0.0f, 0.0f, 0.0f};
    bool hasPoint = false;
};

IndoorBounds makeEmptyIndoorBounds()
{
    IndoorBounds bounds = {};
    bounds.min = {
        std::numeric_limits<float>::max(),
        std::numeric_limits<float>::max(),
        std::numeric_limits<float>::max()
    };
    bounds.max = {
        std::numeric_limits<float>::lowest(),
        std::numeric_limits<float>::lowest(),
        std::numeric_limits<float>::lowest()
    };
    return bounds;
}

void includeIndoorBoundsPoint(IndoorBounds &bounds, const IndoorVertex &vertex)
{
    bounds.min.x = std::min(bounds.min.x, static_cast<float>(vertex.x));
    bounds.min.y = std::min(bounds.min.y, static_cast<float>(vertex.y));
    bounds.min.z = std::min(bounds.min.z, static_cast<float>(vertex.z));
    bounds.max.x = std::max(bounds.max.x, static_cast<float>(vertex.x));
    bounds.max.y = std::max(bounds.max.y, static_cast<float>(vertex.y));
    bounds.max.z = std::max(bounds.max.z, static_cast<float>(vertex.z));
    bounds.hasPoint = true;
}

bool indoorBoundsOverlapWithSlack(const IndoorBounds &left, const IndoorBounds &right, float slack)
{
    if (!left.hasPoint || !right.hasPoint)
    {
        return false;
    }

    return left.max.x + slack >= right.min.x
        && left.min.x - slack <= right.max.x
        && left.max.y + slack >= right.min.y
        && left.min.y - slack <= right.max.y
        && left.max.z + slack >= right.min.z
        && left.min.z - slack <= right.max.z;
}

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

std::array<uint16_t, 8> buildRuntimeActorActionSpriteFrameIndices(
    const SpriteFrameTable &spriteFrameTable,
    const MonsterEntry *pMonsterEntry)
{
    std::array<uint16_t, 8> spriteFrameIndices = {};

    if (pMonsterEntry == nullptr)
    {
        return spriteFrameIndices;
    }

    for (size_t actionIndex = 0; actionIndex < spriteFrameIndices.size(); ++actionIndex)
    {
        const std::string &spriteName = pMonsterEntry->spriteNames[actionIndex];

        if (spriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            spriteFrameIndices[actionIndex] = *frameIndex;
        }
    }

    return spriteFrameIndices;
}

std::vector<RuntimeActorBillboard> buildRuntimeActorBillboards(
    const MonsterTable &monsterTable,
    const SpriteFrameTable &spriteFrameTable,
    const MapDeltaData &mapDeltaData,
    const IndoorWorldRuntime *pWorldRuntime = nullptr
)
{
    std::vector<RuntimeActorBillboard> billboards;
    billboards.reserve(mapDeltaData.actors.size());

    for (size_t actorIndex = 0; actorIndex < mapDeltaData.actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = mapDeltaData.actors[actorIndex];

        if ((actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
        {
            continue;
        }

        const IndoorWorldRuntime::MapActorAiState *pActorAiState =
            pWorldRuntime != nullptr ? pWorldRuntime->mapActorAiState(actorIndex) : nullptr;
        const MonsterEntry *pMonsterEntry =
            pActorAiState == nullptr ? resolveRuntimeMonsterEntry(monsterTable, actor) : nullptr;
        const uint16_t spriteFrameIndex = pActorAiState != nullptr
            ? pActorAiState->spriteFrameIndex
            : resolveRuntimeActorSpriteFrameIndex(spriteFrameTable, actor, pMonsterEntry);

        if (spriteFrameIndex == 0)
        {
            continue;
        }

        RuntimeActorBillboard billboard = {};
        billboard.actorIndex = actorIndex;
        billboard.x = pActorAiState != nullptr ? int(std::lround(pActorAiState->preciseX)) : actor.x;
        billboard.y = pActorAiState != nullptr ? int(std::lround(pActorAiState->preciseY)) : actor.y;
        billboard.z = pActorAiState != nullptr ? int(std::lround(pActorAiState->preciseZ)) : actor.z;
        billboard.sectorId = actor.sectorId;
        billboard.radius = pActorAiState != nullptr ? pActorAiState->collisionRadius : actor.radius;
        billboard.height = pActorAiState != nullptr ? pActorAiState->collisionHeight : actor.height;
        billboard.spriteFrameIndex = spriteFrameIndex;
        billboard.actionSpriteFrameIndices = pActorAiState != nullptr
            ? pActorAiState->actionSpriteFrameIndices
            : buildRuntimeActorActionSpriteFrameIndices(spriteFrameTable, pMonsterEntry);
        billboard.useStaticFrame = false;
        billboard.isFriendly = (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) == 0;
        billboard.actorName = pActorAiState != nullptr
            ? pActorAiState->displayName
            : resolveMapDeltaActorName(monsterTable, actor);
        billboards.push_back(std::move(billboard));
    }

    return billboards;
}

std::vector<RuntimeSpriteObjectBillboard> buildRuntimeSpriteObjectBillboards(
    const ObjectTable &objectTable,
    const ItemTable *pItemTable,
    const MapDeltaData &mapDeltaData
)
{
    std::vector<RuntimeSpriteObjectBillboard> billboards;
    billboards.reserve(mapDeltaData.spriteObjects.size());

    for (size_t objectIndex = 0; objectIndex < mapDeltaData.spriteObjects.size(); ++objectIndex)
    {
        const MapDeltaSpriteObject &spriteObject = mapDeltaData.spriteObjects[objectIndex];
        uint16_t resolvedObjectDescriptionId = spriteObject.objectDescriptionId;
        const uint32_t containedItemId = spriteObjectContainedItemId(spriteObject.rawContainingItem);
        const ItemDefinition *pContainedItemDefinition =
            containedItemId != 0 && pItemTable != nullptr ? pItemTable->get(containedItemId) : nullptr;

        if (pContainedItemDefinition != nullptr && pContainedItemDefinition->spriteIndex != 0)
        {
            const std::optional<uint16_t> containedObjectDescriptionId =
                objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pContainedItemDefinition->spriteIndex));

            if (containedObjectDescriptionId)
            {
                resolvedObjectDescriptionId = *containedObjectDescriptionId;
            }
        }

        const ObjectEntry *pObjectEntry = objectTable.get(resolvedObjectDescriptionId);

        if (pObjectEntry == nullptr || (pObjectEntry->flags & ObjectDescNoSprite) != 0 || pObjectEntry->spriteId == 0)
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
        billboard.objectDescriptionId = resolvedObjectDescriptionId;
        billboard.objectSpriteId = pObjectEntry->spriteId;
        billboard.attributes = spriteObject.attributes;
        billboard.spellId = spriteObject.spellId;
        billboard.timeSinceCreatedTicks = uint32_t(spriteObject.timeSinceCreated) * 8;
        billboard.hasContainingItem =
            hasContainingItemPayload(spriteObject.rawContainingItem)
            && (pObjectEntry->flags & ObjectDescUnpickable) == 0;
        billboard.objectName = pContainedItemDefinition != nullptr && !pContainedItemDefinition->name.empty()
            ? pContainedItemDefinition->name
            : pObjectEntry->internalName;
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

bx::Vec3 bottomAnchoredBillboardCenter(float x, float y, float z, const bx::Vec3 &cameraUp, float worldHeight)
{
    const float halfHeight = worldHeight * 0.5f;

    return {
        x + cameraUp.x * halfHeight,
        y + cameraUp.y * halfHeight,
        z + cameraUp.z * halfHeight
    };
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

float redChannel(uint32_t colorAbgr)
{
    return static_cast<float>(colorAbgr & 0xffu) / 255.0f;
}

float greenChannel(uint32_t colorAbgr)
{
    return static_cast<float>((colorAbgr >> 8) & 0xffu) / 255.0f;
}

float blueChannel(uint32_t colorAbgr)
{
    return static_cast<float>((colorAbgr >> 16) & 0xffu) / 255.0f;
}

float alphaChannel(uint32_t colorAbgr)
{
    return static_cast<float>((colorAbgr >> 24) & 0xffu) / 255.0f;
}

float indoorShaderLightKindWeight(IndoorRenderLightKind kind)
{
    switch (kind)
    {
    case IndoorRenderLightKind::Fx:
        return 12.0f;
    case IndoorRenderLightKind::Torch:
        return 10.0f;
    case IndoorRenderLightKind::Decoration:
        return 8.0f;
    case IndoorRenderLightKind::Static:
        return 1.0f;
    }

    return 1.0f;
}

float indoorShaderLightScore(const IndoorRenderLight &light, const bx::Vec3 &cameraPosition)
{
    const float dx = light.position.x - cameraPosition.x;
    const float dy = light.position.y - cameraPosition.y;
    const float dz = light.position.z - cameraPosition.z;
    const float distance = std::max(std::sqrt(dx * dx + dy * dy + dz * dz), 1.0f);
    return light.radius * light.intensity * indoorShaderLightKindWeight(light.kind) / distance;
}

void fillIndoorLightUniformArrays(
    const IndoorLightingFrame &lightingFrame,
    const bx::Vec3 &cameraPosition,
    std::array<float, MaxIndoorShaderLights * 4> &positions,
    std::array<float, MaxIndoorShaderLights * 4> &colors,
    std::array<float, 4> &params)
{
    positions.fill(0.0f);
    colors.fill(0.0f);

    std::vector<IndoorRenderLight> shaderLights = lightingFrame.lights;
    std::sort(
        shaderLights.begin(),
        shaderLights.end(),
        [&cameraPosition](const IndoorRenderLight &left, const IndoorRenderLight &right)
        {
            return indoorShaderLightScore(left, cameraPosition) > indoorShaderLightScore(right, cameraPosition);
        });

    const size_t lightCount = std::min(shaderLights.size(), MaxIndoorShaderLights);

    for (size_t index = 0; index < lightCount; ++index)
    {
        const IndoorRenderLight &light = shaderLights[index];
        const size_t base = index * 4;
        positions[base + 0] = light.position.x;
        positions[base + 1] = light.position.y;
        positions[base + 2] = light.position.z;
        positions[base + 3] = light.radius;
        colors[base + 0] = redChannel(light.colorAbgr);
        colors[base + 1] = greenChannel(light.colorAbgr);
        colors[base + 2] = blueChannel(light.colorAbgr);
        colors[base + 3] = alphaChannel(light.colorAbgr) * light.intensity;
    }

    params = {{
        static_cast<float>(lightCount),
        lightingFrame.ambient,
        1.35f,
        0.0f
    }};
}

std::array<float, 4> billboardAmbientUniform(
    const IndoorLightingFrame &lightingFrame,
    const bx::Vec3 &position)
{
    const std::array<float, 3> rgb = IndoorLightingRuntime::sampleLightingRgb(lightingFrame, position);
    return {{rgb[0], rgb[1], rgb[2], 0.0f}};
}

std::array<float, 4> billboardLightingUniform(
    const IndoorLightingFrame &lightingFrame,
    const SpriteFrameEntry &frame,
    const bx::Vec3 &position)
{
    if (SpriteFrameTable::hasFlag(frame.flags, SpriteFrameFlag::Lit))
    {
        return {{1.0f, 1.0f, 1.0f, 0.0f}};
    }

    return billboardAmbientUniform(lightingFrame, position);
}

uint32_t resolveHoveredIndoorActorOutlineColor(
    const MapDeltaActor &actor,
    const IndoorWorldRuntime::MapActorAiState *pAiState)
{
    if (actor.hp <= 0 || (pAiState != nullptr && pAiState->motionState == ActorAiMotionState::Dead))
    {
        return makeAbgr(255, 224, 64);
    }

    if ((actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) != 0
        || (pAiState != nullptr && pAiState->hostileToParty))
    {
        return makeAbgr(255, 64, 64);
    }

    return makeAbgr(64, 255, 64);
}

uint32_t hoveredIndoorWorldItemOutlineColor()
{
    return makeAbgr(64, 128, 255);
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

    return eventRuntimeState->hasFacetInvisibleOverride(static_cast<uint32_t>(faceIndex));
}
}

bgfx::VertexLayout IndoorRenderer::TerrainVertex::ms_layout;
bgfx::VertexLayout IndoorRenderer::TexturedVertex::ms_layout;
bgfx::VertexLayout IndoorRenderer::LitBillboardVertex::ms_layout;

IndoorRenderer::IndoorRenderer()
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
    , m_indoorLitProgramHandle(BGFX_INVALID_HANDLE)
    , m_billboardProgramHandle(BGFX_INVALID_HANDLE)
    , m_bloodSplatVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_bloodSplatTextureHandle(BGFX_INVALID_HANDLE)
    , m_textureSamplerHandle(BGFX_INVALID_HANDLE)
    , m_indoorLightPositionsUniformHandle(BGFX_INVALID_HANDLE)
    , m_indoorLightColorsUniformHandle(BGFX_INVALID_HANDLE)
    , m_indoorLightParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardAmbientUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardOverrideColorUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardOutlineParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardFogColorUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardFogDensitiesUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardFogDistancesUniformHandle(BGFX_INVALID_HANDLE)
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
    , m_isRotatingCamera(false)
    , m_lastMouseX(0.0f)
    , m_lastMouseY(0.0f)
    , m_activateInspectLatch(false)
    , m_jumpHeld(false)
{
}

IndoorRenderer::~IndoorRenderer()
{
    shutdown();
}

bool IndoorRenderer::initialize(
    const Engine::AssetFileSystem *pAssetFileSystem,
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
    const ItemTable &itemTable,
    const ChestTable &chestTable,
    const HouseTable &houseTable
)
{
    shutdown();
    m_isInitialized = true;
    m_pAssetFileSystem = pAssetFileSystem;
    m_map = map;
    m_assetScaleTier = assetScaleTier;
    m_monsterTable = monsterTable;
    m_objectTable = objectTable;
    m_pItemTable = &itemTable;
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
    LitBillboardVertex::init();

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
            std::cerr << "IndoorRenderer: failed to create entity marker vertex buffer\n";
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
            std::cerr << "IndoorRenderer: failed to create spawn marker vertex buffer\n";
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
            billboardTexture.pixels = texture.pixels;
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
            billboardTexture.pixels = texture.pixels;
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
            billboardTexture.pixels = texture.pixels;
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
    m_indoorLitProgramHandle = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_lit");
    m_billboardProgramHandle = loadProgram("vs_outdoor_billboard_lit", "fs_outdoor_billboard_lit");
    m_worldFxRenderResources.setParticleProgramHandle(loadProgram("vs_particle", "fs_particle"));
    ParticleRenderer::initializeResources(m_worldFxRenderResources);
    m_textureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);
    m_indoorLightPositionsUniformHandle =
        bgfx::createUniform("u_indoorLightPositions", bgfx::UniformType::Vec4, MaxIndoorShaderLights);
    m_indoorLightColorsUniformHandle =
        bgfx::createUniform("u_indoorLightColors", bgfx::UniformType::Vec4, MaxIndoorShaderLights);
    m_indoorLightParamsUniformHandle = bgfx::createUniform("u_indoorLightParams", bgfx::UniformType::Vec4);
    m_billboardAmbientUniformHandle = bgfx::createUniform("u_billboardAmbient", bgfx::UniformType::Vec4);
    m_billboardOverrideColorUniformHandle =
        bgfx::createUniform("u_billboardOverrideColor", bgfx::UniformType::Vec4);
    m_billboardOutlineParamsUniformHandle =
        bgfx::createUniform("u_billboardOutlineParams", bgfx::UniformType::Vec4);
    m_billboardFogColorUniformHandle = bgfx::createUniform("u_fogColor", bgfx::UniformType::Vec4);
    m_billboardFogDensitiesUniformHandle = bgfx::createUniform("u_fogDensities", bgfx::UniformType::Vec4);
    m_billboardFogDistancesUniformHandle = bgfx::createUniform("u_fogDistances", bgfx::UniformType::Vec4);

    if (!bgfx::isValid(m_programHandle))
    {
        std::cerr << "IndoorRenderer: failed to create debug program handle\n";
        shutdown();
        return false;
    }

    if (!bgfx::isValid(m_texturedProgramHandle))
    {
        std::cerr << "IndoorRenderer: failed to create textured program handle\n";
        shutdown();
        return false;
    }

    if (!bgfx::isValid(m_indoorLitProgramHandle))
    {
        std::cerr << "IndoorRenderer: failed to create indoor lit program handle\n";
        shutdown();
        return false;
    }

    if (!bgfx::isValid(m_billboardProgramHandle))
    {
        std::cerr << "IndoorRenderer: failed to create billboard program handle\n";
        shutdown();
        return false;
    }

    if (!m_worldFxRenderResources.isReady()
        || !bgfx::isValid(m_textureSamplerHandle)
        || !bgfx::isValid(m_indoorLightPositionsUniformHandle)
        || !bgfx::isValid(m_indoorLightColorsUniformHandle)
        || !bgfx::isValid(m_indoorLightParamsUniformHandle)
        || !bgfx::isValid(m_billboardAmbientUniformHandle)
        || !bgfx::isValid(m_billboardOverrideColorUniformHandle)
        || !bgfx::isValid(m_billboardOutlineParamsUniformHandle)
        || !bgfx::isValid(m_billboardFogColorUniformHandle)
        || !bgfx::isValid(m_billboardFogDensitiesUniformHandle)
        || !bgfx::isValid(m_billboardFogDistancesUniformHandle))
    {
        std::cerr << "IndoorRenderer: failed to create billboard uniforms\n";
        shutdown();
        return false;
    }

    if (!rebuildDerivedGeometryResources())
    {
        std::cerr << "IndoorRenderer: failed to rebuild derived geometry resources during initialize\n";
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

bool IndoorRenderer::isFaceVisible(
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

std::vector<uint8_t> IndoorRenderer::buildVisibleSectorMask(const bx::Vec3 &cameraPosition) const
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

bool IndoorRenderer::isSectorVisible(int16_t sectorId, const std::vector<uint8_t> &visibleSectorMask) const
{
    if (visibleSectorMask.empty())
    {
        return true;
    }

    return sectorId >= 0
        && static_cast<size_t>(sectorId) < visibleSectorMask.size()
        && visibleSectorMask[sectorId] != 0;
}

bool IndoorRenderer::isBatchVisible(
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

std::vector<int16_t> IndoorRenderer::visibleIndoorMapRevealSectorIds(int16_t sectorId, int16_t eyeSectorId) const
{
    std::vector<int16_t> sectorIds;

    if (!m_indoorMapData)
    {
        return sectorIds;
    }

    const auto appendSectorId = [&](int16_t candidateSectorId)
    {
        if (candidateSectorId < 0 || static_cast<size_t>(candidateSectorId) >= m_indoorMapData->sectors.size())
        {
            return;
        }

        if (std::find(sectorIds.begin(), sectorIds.end(), candidateSectorId) != sectorIds.end())
        {
            return;
        }

        sectorIds.push_back(candidateSectorId);
    };

    appendSectorId(sectorId);
    appendSectorId(eyeSectorId);

    if (sectorIds.empty() || m_lastRenderWidth <= 0 || m_lastRenderHeight <= 0 || m_renderVertices.empty())
    {
        return sectorIds;
    }

    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    const bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
    const bx::Vec3 at = {
        m_cameraPositionX + cosYaw * cosPitch,
        m_cameraPositionY + sinYaw * cosPitch,
        m_cameraPositionZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    float viewProjectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        60.0f,
        static_cast<float>(m_lastRenderWidth) / static_cast<float>(m_lastRenderHeight),
        0.1f,
        50000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );
    bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);

    const auto faceBounds = [&](const IndoorFace &face) -> IndoorBounds
    {
        IndoorBounds bounds = makeEmptyIndoorBounds();

        for (uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= m_renderVertices.size())
            {
                continue;
            }

            const IndoorVertex &vertex = m_renderVertices[vertexIndex];
            includeIndoorBoundsPoint(bounds, vertex);
        }

        return bounds;
    };

    const auto doorBounds = [&](const MapDeltaDoor &door) -> IndoorBounds
    {
        IndoorBounds bounds = makeEmptyIndoorBounds();

        for (uint16_t vertexIndex : door.vertexIds)
        {
            if (vertexIndex >= m_renderVertices.size())
            {
                continue;
            }

            const IndoorVertex &vertex = m_renderVertices[vertexIndex];
            includeIndoorBoundsPoint(bounds, vertex);
        }

        return bounds;
    };

    const auto portalBlockedByClosedDoor = [&](const IndoorFace &portalFace) -> bool
    {
        const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

        if (!mapDeltaData)
        {
            return false;
        }

        const IndoorBounds portalBounds = faceBounds(portalFace);

        if (!portalBounds.hasPoint)
        {
            return false;
        }

        const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

        for (const MapDeltaDoor &door : mapDeltaData->doors)
        {
            if (resolveMechanismDistance(door, eventRuntimeState) <= 1.0f)
            {
                continue;
            }

            constexpr float DoorPortalRevealSlack = 64.0f;
            const IndoorBounds currentDoorBounds = doorBounds(door);

            if (indoorBoundsOverlapWithSlack(currentDoorBounds, portalBounds, DoorPortalRevealSlack))
            {
                return true;
            }
        }

        return false;
    };

    const auto portalFaceOnScreen = [&](uint16_t faceId) -> bool
    {
        if (faceId >= m_indoorMapData->faces.size())
        {
            return false;
        }

        const IndoorFace &face = m_indoorMapData->faces[faceId];

        if (!face.isPortal
            || face.vertexIndices.empty()
            || !isFaceVisible(faceId, face, runtimeEventRuntimeStateStorage()))
        {
            return false;
        }

        if (portalBlockedByClosedDoor(face))
        {
            return false;
        }

        float minX = std::numeric_limits<float>::max();
        float minY = std::numeric_limits<float>::max();
        float maxX = std::numeric_limits<float>::lowest();
        float maxY = std::numeric_limits<float>::lowest();
        bool hasProjectedVertex = false;

        for (uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= m_renderVertices.size())
            {
                continue;
            }

            const IndoorVertex &vertex = m_renderVertices[vertexIndex];
            ProjectedPoint projected = {};

            if (!projectWorldPointToScreen(
                bx::Vec3{static_cast<float>(vertex.x), static_cast<float>(vertex.y), static_cast<float>(vertex.z)},
                m_lastRenderWidth,
                m_lastRenderHeight,
                viewProjectionMatrix,
                projected))
            {
                continue;
            }

            hasProjectedVertex = true;
            minX = std::min(minX, projected.x);
            minY = std::min(minY, projected.y);
            maxX = std::max(maxX, projected.x);
            maxY = std::max(maxY, projected.y);
        }

        if (!hasProjectedVertex)
        {
            return false;
        }

        constexpr float ScreenMargin = 2.0f;
        return maxX >= -ScreenMargin
            && maxY >= -ScreenMargin
            && minX <= static_cast<float>(m_lastRenderWidth) + ScreenMargin
            && minY <= static_cast<float>(m_lastRenderHeight) + ScreenMargin;
    };

    const auto appendVisiblePortalNeighbor = [&](int16_t baseSectorId, uint16_t faceId)
    {
        if (baseSectorId < 0
            || static_cast<size_t>(baseSectorId) >= m_indoorMapData->sectors.size()
            || faceId >= m_indoorMapData->faces.size()
            || !portalFaceOnScreen(faceId))
        {
            return;
        }

        const IndoorFace &face = m_indoorMapData->faces[faceId];
        int16_t connectedSectorId = -1;

        if (face.roomNumber == static_cast<uint16_t>(baseSectorId))
        {
            connectedSectorId = static_cast<int16_t>(face.roomBehindNumber);
        }
        else if (face.roomBehindNumber == static_cast<uint16_t>(baseSectorId))
        {
            connectedSectorId = static_cast<int16_t>(face.roomNumber);
        }

        appendSectorId(connectedSectorId);
    };

    const size_t baseSectorCount = sectorIds.size();

    for (size_t index = 0; index < baseSectorCount; ++index)
    {
        const int16_t baseSectorId = sectorIds[index];
        const IndoorSector &sector = m_indoorMapData->sectors[baseSectorId];

        for (uint16_t faceId : sector.portalFaceIds)
        {
            appendVisiblePortalNeighbor(baseSectorId, faceId);
        }

        for (uint16_t faceId : sector.faceIds)
        {
            appendVisiblePortalNeighbor(baseSectorId, faceId);
        }
    }

    return sectorIds;
}

void IndoorRenderer::render(
    int width,
    int height,
    GameSession &gameSession,
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput)
{
    if (!m_isInitialized)
    {
        return;
    }

    const uint16_t viewWidth = static_cast<uint16_t>(std::max(width, 1));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(height, 1));
    m_lastRenderWidth = viewWidth;
    m_lastRenderHeight = viewHeight;
    bgfx::setViewRect(MainViewId, 0, 0, viewWidth, viewHeight);

    if (!m_isRenderable)
    {
        bgfx::touch(MainViewId);
        return;
    }

    const float deltaMilliseconds = deltaSeconds * 1000.0f;

    if (allowWorldInput && m_pSceneRuntime != nullptr && m_pSceneRuntime->advanceSimulation(deltaMilliseconds))
    {
        const bool mechanismsStillMoving = hasMovingMechanism(runtimeEventRuntimeState());

        if (mechanismsStillMoving)
        {
            updateMovingMechanismGeometryResources();
        }
        else
        {
            rebuildDerivedGeometryResources();
        }
    }

    m_worldFxSystem.setShadowsEnabled(gameSession.gameplayScreenRuntime().settingsSnapshot().shadows);
    m_worldFxSystem.updateParticles(deltaSeconds, m_gameplayCursorMode);

    if (!m_gameplayCursorMode)
    {
        m_worldFxSystem.clearSpatialFx();
        m_worldFxSystem.syncProjectileFx(gameSession, deltaSeconds, true);
    }

    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);

    const bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
    const bx::Vec3 at = {
        m_cameraPositionX + cosYaw * cosPitch,
        m_cameraPositionY + sinYaw * cosPitch,
        m_cameraPositionZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};

    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        60.0f,
        static_cast<float>(viewWidth) / static_cast<float>(viewHeight),
        0.1f,
        50000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );

    bgfx::setViewTransform(MainViewId, viewMatrix, projectionMatrix);
    bgfx::touch(MainViewId);
    const std::vector<uint8_t> visibleSectorMask = buildVisibleSectorMask(eye);
    const GameSettings &settings = gameSession.gameplayScreenRuntime().settingsSnapshot();
    IndoorLightingFrameInput lightingInput = {};
    lightingInput.pMapData = m_indoorMapData ? &m_indoorMapData.value() : nullptr;
    lightingInput.pEventRuntimeState = runtimeEventRuntimeState();
    lightingInput.pDecorationBillboardSet =
        m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr;
    lightingInput.pWorldFxSystem = &m_worldFxSystem;
    lightingInput.pParty = m_pSceneRuntime != nullptr ? &m_pSceneRuntime->partyRuntime().party() : nullptr;
    lightingInput.pVisibleSectorMask = &visibleSectorMask;
    lightingInput.cameraPosition = eye;
    lightingInput.coloredLights = settings.coloredLights;
    const IndoorLightingFrame lightingFrame = m_indoorLightingRuntime.buildFrame(lightingInput);
    std::array<float, MaxIndoorShaderLights * 4> indoorLightPositions = {};
    std::array<float, MaxIndoorShaderLights * 4> indoorLightColors = {};
    std::array<float, 4> indoorLightParams = {};
    fillIndoorLightUniformArrays(lightingFrame, eye, indoorLightPositions, indoorLightColors, indoorLightParams);

    InspectHit inspectHit = {};
    float mouseX = input.pointerX;
    float mouseY = input.pointerY;

    if (m_indoorMapData)
    {
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
        GameplayWorldPickRequest inspectPickRequest = {};
        inspectPickRequest.screenX = mouseX;
        inspectPickRequest.screenY = mouseY;
        inspectPickRequest.viewWidth = viewWidth;
        inspectPickRequest.viewHeight = viewHeight;
        inspectPickRequest.rayOrigin = rayOrigin;
        inspectPickRequest.rayDirection = rayDirection;
        inspectPickRequest.eye = eye;
        inspectPickRequest.hasRay = vecLength(rayDirection) > InspectRayEpsilon;
        std::copy(std::begin(viewMatrix), std::end(viewMatrix), inspectPickRequest.viewMatrix.begin());
        std::copy(std::begin(projectionMatrix), std::end(projectionMatrix), inspectPickRequest.projectionMatrix.begin());

        const uint64_t inspectTick = SDL_GetTicks();
        constexpr uint64_t InspectRefreshIntervalMs = 33;
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

        const auto updateCachedInspectHit =
            [&]() -> const InspectHit &
            {
                m_cachedInspectHit = inspectAtCursor(
                    *m_indoorMapData,
                    m_renderVertices,
                    visibleSectorMask,
                    rayOrigin,
                    rayDirection,
                    &inspectPickRequest);
                m_cachedInspectHitValid = true;
                m_cachedGameplayWorldPickRequest = inspectPickRequest;
                m_cachedInspectMouseX = mouseX;
                m_cachedInspectMouseY = mouseY;
                m_cachedInspectCameraX = eye.x;
                m_cachedInspectCameraY = eye.y;
                m_cachedInspectCameraZ = eye.z;
                m_cachedInspectYawRadians = m_cameraYawRadians;
                m_cachedInspectPitchRadians = m_cameraPitchRadians;
                m_cachedInspectGeometryRevision = m_inspectGeometryRevision;
                m_lastInspectUpdateTick = inspectTick;
                return m_cachedInspectHit;
            };

        if (inspectViewChanged
            && (inspectTick - m_lastInspectUpdateTick >= InspectRefreshIntervalMs || !m_cachedInspectHitValid))
        {
            updateCachedInspectHit();
        }

        inspectHit = m_cachedInspectHit;

        const bool isActivationPressed =
            input.isScancodeHeld(SDL_SCANCODE_E)
            && !input.rightMouseButton.held;
        const bool isLeftMousePressed = input.leftMouseButton.held;

        if ((isActivationPressed || isLeftMousePressed) && !m_activateInspectLatch)
        {
            if (inspectViewChanged)
            {
                inspectHit = updateCachedInspectHit();
            }

            if (tryActivateInspectEvent(inspectHit))
            {
                inspectHit = updateCachedInspectHit();
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

    if (bgfx::isValid(m_indoorLitProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && bgfx::isValid(m_indoorLightPositionsUniformHandle)
        && bgfx::isValid(m_indoorLightColorsUniformHandle)
        && bgfx::isValid(m_indoorLightParamsUniformHandle))
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
            bgfx::setUniform(
                m_indoorLightPositionsUniformHandle,
                indoorLightPositions.data(),
                MaxIndoorShaderLights);
            bgfx::setUniform(
                m_indoorLightColorsUniformHandle,
                indoorLightColors.data(),
                MaxIndoorShaderLights);
            bgfx::setUniform(m_indoorLightParamsUniformHandle, indoorLightParams.data());
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_BLEND_ALPHA
            );
            bgfx::submit(MainViewId, m_indoorLitProgramHandle);
        }
    }

    if (settings.bloodSplats)
    {
        renderBloodSplats(
            MainViewId,
            indoorLightPositions,
            indoorLightColors,
            indoorLightParams);
    }

    renderDecorationBillboards(MainViewId, viewMatrix, eye, visibleSectorMask, lightingFrame);
    renderActorPreviewBillboards(MainViewId, viewMatrix, eye, visibleSectorMask, lightingFrame);
    renderSpriteObjectBillboards(MainViewId, viewMatrix, eye, visibleSectorMask, lightingFrame);

    ParticleRenderer::renderParticles(
        m_worldFxRenderResources,
        m_worldFxSystem.particles(),
        MainViewId,
        viewMatrix,
        eye,
        static_cast<float>(viewWidth) / static_cast<float>(viewHeight));
}

bool IndoorRenderer::hasHudRenderResources() const
{
    return bgfx::isValid(m_texturedProgramHandle) && bgfx::isValid(m_textureSamplerHandle);
}

WorldFxSystem &IndoorRenderer::worldFxSystem()
{
    return m_worldFxSystem;
}

const WorldFxSystem &IndoorRenderer::worldFxSystem() const
{
    return m_worldFxSystem;
}

bgfx::ProgramHandle IndoorRenderer::hudTexturedProgramHandle() const
{
    return m_texturedProgramHandle;
}

bgfx::UniformHandle IndoorRenderer::hudTextureSamplerHandle() const
{
    return m_textureSamplerHandle;
}

void IndoorRenderer::prepareHudView(int width, int height) const
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

void IndoorRenderer::submitHudTextureQuad(
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

void IndoorRenderer::setGameplayMouseLookMode(bool enabled, bool cursorMode)
{
    m_gameplayMouseLookEnabled = enabled;
    m_gameplayCursorMode = cursorMode;
}

std::optional<IndoorRenderer::GameplayActorPick>
IndoorRenderer::gameplayActorPickAtCursor(
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
        m_cameraPositionY + sinYaw * cosPitch,
        m_cameraPositionZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    float viewProjectionMatrix[16] = {};
    float inverseViewProjectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        60.0f,
        aspectRatio,
        0.1f,
        50000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
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
    std::optional<GameplayActorPick> billboardPick;
    float bestBillboardDistance = std::numeric_limits<float>::max();

    if (runtimeMapDeltaData() && m_monsterTable && m_indoorActorPreviewBillboardSet)
    {
        const bx::Vec3 cameraRight = {viewMatrix[0], viewMatrix[4], viewMatrix[8]};
        const bx::Vec3 cameraUp = {viewMatrix[1], viewMatrix[5], viewMatrix[9]};
        const std::vector<RuntimeActorBillboard> runtimeActors =
            buildRuntimeActorBillboards(
                *m_monsterTable,
                m_indoorActorPreviewBillboardSet->spriteFrameTable,
                *runtimeMapDeltaData(),
                m_pSceneRuntime != nullptr ? &m_pSceneRuntime->worldRuntime() : nullptr);

        for (const RuntimeActorBillboard &actor : runtimeActors)
        {
            if (!isSectorVisible(actor.sectorId, visibleSectorMask))
            {
                continue;
            }

            const IndoorWorldRuntime::MapActorAiState *pActorAiState =
                m_pSceneRuntime->worldRuntime().mapActorAiState(actor.actorIndex);
            uint16_t spriteFrameIndex = actor.spriteFrameIndex;
            uint32_t frameTimeTicks = actor.useStaticFrame ? 0U : currentAnimationTicks();

            if (pActorAiState != nullptr)
            {
                const size_t animationIndex = static_cast<size_t>(pActorAiState->animationState);

                if (animationIndex < actor.actionSpriteFrameIndices.size()
                    && actor.actionSpriteFrameIndices[animationIndex] != 0)
                {
                    spriteFrameIndex = actor.actionSpriteFrameIndices[animationIndex];
                }

                frameTimeTicks = static_cast<uint32_t>(std::max(0.0f, pActorAiState->animationTimeTicks));
            }

            const SpriteFrameEntry *pFrame =
                m_indoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, frameTimeTicks);

            if (pFrame == nullptr)
            {
                continue;
            }

            const float angleToCamera = std::atan2(
                static_cast<float>(actor.y) - m_cameraPositionY,
                static_cast<float>(actor.x) - m_cameraPositionX);
            const float actorYawRadians = pActorAiState != nullptr ? pActorAiState->yawRadians : 0.0f;
            const float octantAngle = actorYawRadians - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || pTexture->width <= 0 || pTexture->height <= 0)
            {
                continue;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const float halfWidth = worldWidth * 0.5f;
            const bx::Vec3 center = bottomAnchoredBillboardCenter(
                static_cast<float>(actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(actor.z),
                cameraUp,
                worldHeight);
            const bx::Vec3 right = {
                cameraRight.x * halfWidth,
                cameraRight.y * halfWidth,
                cameraRight.z * halfWidth
            };
            const bx::Vec3 billboardUp = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            const bx::Vec3 topLeft = {
                center.x - right.x + billboardUp.x,
                center.y - right.y + billboardUp.y,
                center.z - right.z + billboardUp.z
            };
            const bx::Vec3 topRight = {
                center.x + right.x + billboardUp.x,
                center.y + right.y + billboardUp.y,
                center.z + right.z + billboardUp.z
            };
            const bx::Vec3 bottomLeft = {
                center.x - right.x - billboardUp.x,
                center.y - right.y - billboardUp.y,
                center.z - right.z - billboardUp.z
            };
            const bx::Vec3 bottomRight = {
                center.x + right.x - billboardUp.x,
                center.y + right.y - billboardUp.y,
                center.z + right.z - billboardUp.z
            };
            ProjectedPoint projectedTopLeft = {};
            ProjectedPoint projectedTopRight = {};
            ProjectedPoint projectedBottomLeft = {};
            ProjectedPoint projectedBottomRight = {};

            if (!projectWorldPointToScreen(topLeft, viewWidth, viewHeight, viewProjectionMatrix, projectedTopLeft)
                || !projectWorldPointToScreen(topRight, viewWidth, viewHeight, viewProjectionMatrix, projectedTopRight)
                || !projectWorldPointToScreen(bottomLeft, viewWidth, viewHeight, viewProjectionMatrix, projectedBottomLeft)
                || !projectWorldPointToScreen(bottomRight, viewWidth, viewHeight, viewProjectionMatrix, projectedBottomRight))
            {
                continue;
            }

            const float left = std::min(
                std::min(projectedTopLeft.x, projectedTopRight.x),
                std::min(projectedBottomLeft.x, projectedBottomRight.x));
            const float rightEdge = std::max(
                std::max(projectedTopLeft.x, projectedTopRight.x),
                std::max(projectedBottomLeft.x, projectedBottomRight.x));
            const float top = std::min(
                std::min(projectedTopLeft.y, projectedTopRight.y),
                std::min(projectedBottomLeft.y, projectedBottomRight.y));
            const float bottom = std::max(
                std::max(projectedTopLeft.y, projectedTopRight.y),
                std::max(projectedBottomLeft.y, projectedBottomRight.y));

            if (screenX < left || screenX > rightEdge || screenY < top || screenY > bottom)
            {
                continue;
            }

            const float screenWidthPixels = rightEdge - left;
            const float screenHeightPixels = bottom - top;

            if (screenWidthPixels <= 0.0f || screenHeightPixels <= 0.0f)
            {
                continue;
            }

            float normalizedU = (screenX - left) / screenWidthPixels;
            const float normalizedV = (screenY - top) / screenHeightPixels;

            if (resolvedTexture.mirrored)
            {
                normalizedU = 1.0f - normalizedU;
            }

            if (pTexture->physicalWidth > 0 && pTexture->physicalHeight > 0 && !pTexture->pixels.empty())
            {
                const int pixelX = std::clamp(
                    static_cast<int>(std::floor(normalizedU * static_cast<float>(pTexture->physicalWidth))),
                    0,
                    pTexture->physicalWidth - 1);
                const int pixelY = std::clamp(
                    static_cast<int>(std::floor(normalizedV * static_cast<float>(pTexture->physicalHeight))),
                    0,
                    pTexture->physicalHeight - 1);
                const size_t pixelOffset = static_cast<size_t>((pixelY * pTexture->physicalWidth + pixelX) * 4);

                if (pixelOffset + 3 >= pTexture->pixels.size() || pTexture->pixels[pixelOffset + 3] == 0)
                {
                    continue;
                }
            }

            const bx::Vec3 planeNormal = {
                -cameraRight.y * cameraUp.z + cameraRight.z * cameraUp.y,
                -cameraRight.z * cameraUp.x + cameraRight.x * cameraUp.z,
                -cameraRight.x * cameraUp.y + cameraRight.y * cameraUp.x
            };
            const float denominator = vecDot(rayDirection, planeNormal);

            if (std::fabs(denominator) <= InspectRayEpsilon)
            {
                continue;
            }

            const float distance = vecDot(vecSubtract(center, rayOrigin), planeNormal) / denominator;

            if (distance <= InspectRayEpsilon || distance >= bestBillboardDistance)
            {
                continue;
            }

            bestBillboardDistance = distance;
            billboardPick = GameplayActorPick{
                .runtimeActorIndex = actor.actorIndex,
                .sourceX = left,
                .sourceY = top,
                .sourceWidth = screenWidthPixels,
                .sourceHeight = screenHeightPixels,
            };
        }
    }

    if (billboardPick)
    {
        return billboardPick;
    }

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

GameplayWorldPickRequest IndoorRenderer::buildGameplayWorldPickRequest(
    const GameplayWorldPickRequestInput &input) const
{
    const int viewWidth = std::max(input.screenWidth, 1);
    const int viewHeight = std::max(input.screenHeight, 1);
    const float aspectRatio = float(viewWidth) / float(viewHeight);
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
        m_cameraPositionY + sinYaw * cosPitch,
        m_cameraPositionZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};

    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        60.0f,
        aspectRatio,
        0.1f,
        50000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );

    GameplayWorldPickRequest request = {};
    request.screenX = input.screenX;
    request.screenY = input.screenY;
    request.viewWidth = viewWidth;
    request.viewHeight = viewHeight;
    request.eye = eye;
    std::copy(std::begin(viewMatrix), std::end(viewMatrix), request.viewMatrix.begin());
    std::copy(std::begin(projectionMatrix), std::end(projectionMatrix), request.projectionMatrix.begin());

    if (input.includeRay)
    {
        const float normalizedMouseX = ((input.screenX / float(viewWidth)) * 2.0f) - 1.0f;
        const float normalizedMouseY = 1.0f - ((input.screenY / float(viewHeight)) * 2.0f);
        float viewProjectionMatrix[16] = {};
        float inverseViewProjectionMatrix[16] = {};
        bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);
        bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);
        request.rayOrigin = bx::mulH({normalizedMouseX, normalizedMouseY, 0.0f}, inverseViewProjectionMatrix);
        const bx::Vec3 rayTarget = bx::mulH({normalizedMouseX, normalizedMouseY, 1.0f}, inverseViewProjectionMatrix);
        request.rayDirection = vecNormalize(vecSubtract(rayTarget, request.rayOrigin));
        request.hasRay = vecLength(request.rayDirection) > InspectRayEpsilon;
    }

    return request;
}

std::optional<IndoorRenderer::InspectHit> IndoorRenderer::inspectGameplayWorldHit(
    const GameplayWorldPickRequest &request) const
{
    if (!m_isInitialized
        || !m_isRenderable
        || !m_indoorMapData
        || request.viewWidth <= 0
        || request.viewHeight <= 0)
    {
        return std::nullopt;
    }

    GameplayWorldPickRequest rayRequest = request;

    if (!rayRequest.hasRay)
    {
        const GameplayWorldPickRequestInput input = {
            .screenX = request.screenX,
            .screenY = request.screenY,
            .screenWidth = request.viewWidth,
            .screenHeight = request.viewHeight,
            .includeRay = true,
        };
        rayRequest = buildGameplayWorldPickRequest(input);
    }

    if (!rayRequest.hasRay || vecLength(rayRequest.rayDirection) <= InspectRayEpsilon)
    {
        return std::nullopt;
    }

    const std::vector<uint8_t> visibleSectorMask = buildVisibleSectorMask(rayRequest.eye);
    return inspectAtCursor(
        *m_indoorMapData,
        m_renderVertices,
        visibleSectorMask,
        rayRequest.rayOrigin,
        rayRequest.rayDirection,
        &rayRequest);
}

GameplayWorldHit IndoorRenderer::translateInspectHitToGameplayWorldHit(
    const InspectHit &inspectHit,
    const GameplayWorldPickRequest &request) const
{
    GameplayWorldHit worldHit = {};

    if (!inspectHit.hasHit)
    {
        return worldHit;
    }

    const bx::Vec3 hitPoint = {
        request.rayOrigin.x + request.rayDirection.x * inspectHit.distance,
        request.rayOrigin.y + request.rayDirection.y * inspectHit.distance,
        request.rayOrigin.z + request.rayDirection.z * inspectHit.distance
    };
    worldHit.hasHit = true;

    if (inspectHit.kind == "actor")
    {
        worldHit.kind = GameplayWorldHitKind::Actor;

        GameplayActorTargetHit actorHit = {};
        actorHit.actorIndex = inspectHit.index;
        actorHit.displayName = inspectHit.name;
        actorHit.isFriendly = inspectHit.isFriendly;
        actorHit.hitPoint = hitPoint;
        actorHit.distance = inspectHit.distance;
        worldHit.actor = actorHit;
        return worldHit;
    }

    if (inspectHit.kind == "object")
    {
        if (inspectHit.hasContainingItem)
        {
            worldHit.kind = GameplayWorldHitKind::WorldItem;

            GameplayWorldItemTargetHit worldItemHit = {};
            worldItemHit.worldItemIndex = inspectHit.index;
            worldItemHit.objectDescriptionId = inspectHit.objectDescriptionId;
            worldItemHit.objectSpriteId = inspectHit.objectSpriteId;
            worldItemHit.hitPoint = hitPoint;
            worldItemHit.distance = inspectHit.distance;
            worldHit.worldItem = worldItemHit;
            return worldHit;
        }

        worldHit.kind = GameplayWorldHitKind::Object;

        GameplayObjectTargetHit objectHit = {};
        objectHit.objectIndex = inspectHit.index;
        objectHit.objectDescriptionId = inspectHit.objectDescriptionId;
        objectHit.objectSpriteId = inspectHit.objectSpriteId;
        objectHit.spellId = inspectHit.spellId;
        objectHit.hitPoint = hitPoint;
        objectHit.distance = inspectHit.distance;
        worldHit.object = objectHit;
        return worldHit;
    }

    GameplayEventTargetHit eventTargetHit = {};
    eventTargetHit.targetIndex = inspectHit.index;
    eventTargetHit.eventIdPrimary = inspectHit.eventIdPrimary;
    eventTargetHit.eventIdSecondary = inspectHit.eventIdSecondary;
    eventTargetHit.triggeredEventId = inspectHit.cogTriggered;
    eventTargetHit.trigger = inspectHit.cogTriggerType;
    eventTargetHit.variablePrimary = inspectHit.variablePrimary;
    eventTargetHit.variableSecondary = inspectHit.variableSecondary;
    eventTargetHit.specialTrigger = inspectHit.specialTrigger;
    eventTargetHit.attributes = inspectHit.attributes;
    eventTargetHit.name = inspectHit.name;
    eventTargetHit.hitPoint = hitPoint;
    eventTargetHit.distance = inspectHit.distance;

    if (inspectHit.kind == "face")
    {
        eventTargetHit.targetKind = GameplayWorldEventTargetKind::Surface;
        eventTargetHit.secondaryIndex = inspectHit.index;
    }
    else if (inspectHit.kind == "entity")
    {
        eventTargetHit.targetKind = GameplayWorldEventTargetKind::Entity;
    }
    else if (inspectHit.kind == "spawn")
    {
        eventTargetHit.targetKind = GameplayWorldEventTargetKind::Spawn;
    }
    else if (inspectHit.kind == "mechanism")
    {
        eventTargetHit.targetKind = GameplayWorldEventTargetKind::Object;
        eventTargetHit.triggeredEventId = inspectHit.mechanismLinkedEventId != 0
            ? inspectHit.mechanismLinkedEventId
            : static_cast<uint16_t>(inspectHit.doorId);
    }
    else
    {
        worldHit.hasHit = false;
        worldHit.kind = GameplayWorldHitKind::None;
        return worldHit;
    }

    worldHit.kind = GameplayWorldHitKind::EventTarget;
    worldHit.eventTarget = eventTargetHit;
    return worldHit;
}

GameplayWorldHit IndoorRenderer::pickGameplayWorldHit(const GameplayWorldPickRequest &request) const
{
    const std::optional<InspectHit> inspectHit = inspectGameplayWorldHit(request);

    if (!inspectHit)
    {
        return {};
    }

    GameplayWorldPickRequest rayRequest = request;

    if (!rayRequest.hasRay)
    {
        const GameplayWorldPickRequestInput input = {
            .screenX = request.screenX,
            .screenY = request.screenY,
            .screenWidth = request.viewWidth,
            .screenHeight = request.viewHeight,
            .includeRay = true,
        };
        rayRequest = buildGameplayWorldPickRequest(input);
    }

    return translateInspectHitToGameplayWorldHit(*inspectHit, rayRequest);
}

GameplayWorldHit IndoorRenderer::pickKeyboardGameplayWorldHit(const GameplayWorldPickRequest &request) const
{
    GameplayWorldPickRequest rayRequest = request;

    if (!rayRequest.hasRay)
    {
        const GameplayWorldPickRequestInput input = {
            .screenX = request.screenX,
            .screenY = request.screenY,
            .screenWidth = request.viewWidth,
            .screenHeight = request.viewHeight,
            .includeRay = true,
        };
        rayRequest = buildGameplayWorldPickRequest(input);
    }

    const auto isSelectableHit =
        [this](const GameplayWorldHit &hit) -> bool
        {
            return m_pSceneRuntime != nullptr
                && m_pSceneRuntime->worldRuntime().canActivateWorldHit(hit, GameplayInteractionMethod::Keyboard);
        };

    const GameplayWorldHit directHit = pickGameplayWorldHit(rayRequest);

    if (isSelectableHit(directHit))
    {
        return directHit;
    }

    if (!m_isInitialized
        || !m_isRenderable
        || !m_indoorMapData
        || rayRequest.viewWidth <= 0
        || rayRequest.viewHeight <= 0)
    {
        return {};
    }

    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, rayRequest.viewMatrix.data(), rayRequest.projectionMatrix.data());

    struct KeyboardCandidate
    {
        float screenX = 0.0f;
        float screenY = 0.0f;
        float score = 0.0f;
        bool hasWorldHit = false;
        GameplayWorldHit worldHit = {};
    };

    std::vector<KeyboardCandidate> candidates;
    const std::vector<uint8_t> visibleSectorMask = buildVisibleSectorMask(rayRequest.eye);

    const auto levelBlocksWorldPoint =
        [&](const bx::Vec3 &worldPoint) -> bool
        {
            const bx::Vec3 toPoint = vecSubtract(worldPoint, rayRequest.eye);
            const float pointDistance = vecLength(toPoint);

            if (pointDistance <= InspectRayEpsilon)
            {
                return false;
            }

            const bx::Vec3 rayDirection = vecNormalize(toPoint);

            for (size_t faceIndex = 0; faceIndex < m_indoorMapData->faces.size(); ++faceIndex)
            {
                const IndoorFace &face = m_indoorMapData->faces[faceIndex];

                if (face.vertexIndices.size() < 3
                    || face.isPortal
                    || hasFaceAttribute(face.attributes, FaceAttribute::IsPortal)
                    || !isFaceVisible(faceIndex, face, runtimeEventRuntimeStateStorage())
                    || (!visibleSectorMask.empty()
                        && !isSectorVisible(static_cast<int16_t>(face.roomNumber), visibleSectorMask)
                        && !isSectorVisible(static_cast<int16_t>(face.roomBehindNumber), visibleSectorMask)))
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

                        if (vertexIndex >= m_renderVertices.size())
                        {
                            isTriangleValid = false;
                            break;
                        }

                        const IndoorVertex &vertex = m_renderVertices[vertexIndex];
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
                            rayRequest.eye,
                            rayDirection,
                            triangleVertices[0],
                            triangleVertices[1],
                            triangleVertices[2],
                            distance)
                        && distance > InspectRayEpsilon
                        && distance + 1.0f < pointDistance)
                    {
                        return true;
                    }
                }
            }

            return false;
        };

    const auto appendProjectedCandidate =
        [&](const bx::Vec3 &worldPoint, float screenRadius)
        {
            ProjectedPoint projected = {};

            if (!projectWorldPointToScreen(
                    worldPoint,
                    rayRequest.viewWidth,
                    rayRequest.viewHeight,
                    viewProjectionMatrix,
                    projected))
            {
                return;
            }

            if (projected.x < 0.0f
                || projected.x > static_cast<float>(rayRequest.viewWidth)
                || projected.y < 0.0f
                || projected.y > static_cast<float>(rayRequest.viewHeight))
            {
                return;
            }

            const float deltaX = projected.x - rayRequest.screenX;
            const float deltaY = projected.y - rayRequest.screenY;
            const float screenDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY);

            if (screenRadius >= 0.0f && screenDistance > screenRadius)
            {
                return;
            }

            const float worldDistance = vecLength(vecSubtract(worldPoint, rayRequest.eye));
            candidates.push_back(KeyboardCandidate{
                .screenX = projected.x,
                .screenY = projected.y,
                .score = screenDistance * 4.0f + worldDistance,
            });
        };

    const auto appendProjectedWorldHitCandidate =
        [&](const bx::Vec3 &worldPoint, GameplayWorldHit worldHit)
        {
            if (!isSelectableHit(worldHit))
            {
                return;
            }

            ProjectedPoint projected = {};

            if (!projectWorldPointToScreen(
                    worldPoint,
                    rayRequest.viewWidth,
                    rayRequest.viewHeight,
                    viewProjectionMatrix,
                    projected))
            {
                return;
            }

            if (projected.x < 0.0f
                || projected.x > static_cast<float>(rayRequest.viewWidth)
                || projected.y < 0.0f
                || projected.y > static_cast<float>(rayRequest.viewHeight)
                || levelBlocksWorldPoint(worldPoint))
            {
                return;
            }

            const float deltaX = projected.x - rayRequest.screenX;
            const float deltaY = projected.y - rayRequest.screenY;
            const float screenDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY);
            const float worldDistance = vecLength(vecSubtract(worldPoint, rayRequest.eye));

            candidates.push_back(KeyboardCandidate{
                .screenX = projected.x,
                .screenY = projected.y,
                .score = screenDistance * 4.0f + worldDistance,
                .hasWorldHit = true,
                .worldHit = worldHit,
            });
        };

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

    if (mapDeltaData && m_monsterTable && m_indoorActorPreviewBillboardSet)
    {
        const std::vector<RuntimeActorBillboard> runtimeActors =
            buildRuntimeActorBillboards(
                *m_monsterTable,
                m_indoorActorPreviewBillboardSet->spriteFrameTable,
                *mapDeltaData,
                m_pSceneRuntime != nullptr ? &m_pSceneRuntime->worldRuntime() : nullptr);

        for (const RuntimeActorBillboard &actor : runtimeActors)
        {
            if (!isSectorVisible(actor.sectorId, visibleSectorMask))
            {
                continue;
            }

            const bx::Vec3 hitPoint = {
                static_cast<float>(actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(actor.z) + static_cast<float>(std::max<uint16_t>(actor.height, 96)) * 0.5f
            };
            GameplayActorTargetHit actorHit = {};
            actorHit.actorIndex = actor.actorIndex;
            actorHit.displayName = actor.actorName;
            actorHit.isFriendly = actor.isFriendly;
            actorHit.hitPoint = hitPoint;
            actorHit.distance = vecLength(vecSubtract(hitPoint, rayRequest.eye));

            GameplayWorldHit worldHit = {};
            worldHit.hasHit = true;
            worldHit.kind = GameplayWorldHitKind::Actor;
            worldHit.actor = actorHit;
            appendProjectedWorldHitCandidate(hitPoint, worldHit);
        }
    }

    if (mapDeltaData && m_objectTable)
    {
        const std::vector<RuntimeSpriteObjectBillboard> runtimeObjects =
            buildRuntimeSpriteObjectBillboards(*m_objectTable, m_pItemTable, *mapDeltaData);

        for (const RuntimeSpriteObjectBillboard &object : runtimeObjects)
        {
            if (!object.hasContainingItem)
            {
                continue;
            }

            if (!isSectorVisible(object.sectorId, visibleSectorMask))
            {
                continue;
            }

            const bx::Vec3 hitPoint = {
                static_cast<float>(object.x),
                static_cast<float>(object.y),
                static_cast<float>(object.z) + static_cast<float>(std::max<int16_t>(object.height, 64)) * 0.5f
            };
            GameplayWorldItemTargetHit worldItemHit = {};
            worldItemHit.worldItemIndex = object.objectIndex;
            worldItemHit.objectDescriptionId = object.objectDescriptionId;
            worldItemHit.objectSpriteId = object.objectSpriteId;
            worldItemHit.hitPoint = hitPoint;
            worldItemHit.distance = vecLength(vecSubtract(hitPoint, rayRequest.eye));

            GameplayWorldHit worldHit = {};
            worldHit.hasHit = true;
            worldHit.kind = GameplayWorldHitKind::WorldItem;
            worldHit.worldItem = worldItemHit;
            appendProjectedWorldHitCandidate(hitPoint, worldHit);
        }
    }

    for (size_t faceIndex = 0; faceIndex < m_indoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_indoorMapData->faces[faceIndex];

        if (face.vertexIndices.empty()
            || (face.cogTriggered == 0 && face.cogNumber == 0)
            || !isFaceVisible(faceIndex, face, runtimeEventRuntimeStateStorage())
            || (!visibleSectorMask.empty()
                && !isSectorVisible(static_cast<int16_t>(face.roomNumber), visibleSectorMask)
                && !isSectorVisible(static_cast<int16_t>(face.roomBehindNumber), visibleSectorMask)))
        {
            continue;
        }

        bx::Vec3 center = {0.0f, 0.0f, 0.0f};
        uint32_t validVertexCount = 0;

        for (uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= m_renderVertices.size())
            {
                continue;
            }

            const IndoorVertex &vertex = m_renderVertices[vertexIndex];
            center.x += static_cast<float>(vertex.x);
            center.y += static_cast<float>(vertex.y);
            center.z += static_cast<float>(vertex.z);
            ++validVertexCount;
        }

        if (validVertexCount == 0)
        {
            continue;
        }

        center.x /= static_cast<float>(validVertexCount);
        center.y /= static_cast<float>(validVertexCount);
        center.z /= static_cast<float>(validVertexCount);
        appendProjectedCandidate(center, 128.0f);
    }

    if (m_indoorMapData)
    {
        for (const IndoorEntity &entity : m_indoorMapData->entities)
        {
            appendProjectedCandidate(
                {
                    static_cast<float>(entity.x),
                    static_cast<float>(entity.y),
                    static_cast<float>(entity.z) + 32.0f
                },
                96.0f);
        }
    }

    if (mapDeltaData)
    {
        for (size_t doorIndex = 0; doorIndex < mapDeltaData->doors.size(); ++doorIndex)
        {
            const MapDeltaDoor &door = mapDeltaData->doors[doorIndex];

            if (door.vertexIds.empty()
                || (doorIndex < m_mechanismBindings.size()
                    && m_mechanismBindings[doorIndex].linkedEventId == 0
                    && door.doorId == 0))
            {
                continue;
            }

            bx::Vec3 center = {0.0f, 0.0f, 0.0f};
            uint32_t validVertexCount = 0;

            for (uint16_t vertexId : door.vertexIds)
            {
                if (vertexId >= m_renderVertices.size())
                {
                    continue;
                }

                const IndoorVertex &vertex = m_renderVertices[vertexId];
                center.x += static_cast<float>(vertex.x);
                center.y += static_cast<float>(vertex.y);
                center.z += static_cast<float>(vertex.z);
                ++validVertexCount;
            }

            if (validVertexCount == 0)
            {
                continue;
            }

            center.x /= static_cast<float>(validVertexCount);
            center.y /= static_cast<float>(validVertexCount);
            center.z /= static_cast<float>(validVertexCount);
            appendProjectedCandidate(center, 128.0f);
        }
    }

    std::sort(
        candidates.begin(),
        candidates.end(),
        [](const KeyboardCandidate &left, const KeyboardCandidate &right)
        {
            return left.score < right.score;
        });

    constexpr size_t MaxKeyboardCandidateProbes = 16;
    const size_t candidateProbeCount = std::min(candidates.size(), MaxKeyboardCandidateProbes);

    for (size_t candidateIndex = 0; candidateIndex < candidateProbeCount; ++candidateIndex)
    {
        const KeyboardCandidate &candidate = candidates[candidateIndex];

        if (candidate.hasWorldHit)
        {
            if (isSelectableHit(candidate.worldHit))
            {
                return candidate.worldHit;
            }

            continue;
        }

        const GameplayWorldPickRequest candidateRequest =
            buildGameplayWorldPickRequest(
                GameplayWorldPickRequestInput{
                    .screenX = candidate.screenX,
                    .screenY = candidate.screenY,
                    .screenWidth = rayRequest.viewWidth,
                    .screenHeight = rayRequest.viewHeight,
                    .includeRay = true,
                });
        const GameplayWorldHit candidateHit = pickGameplayWorldHit(candidateRequest);

        if (isSelectableHit(candidateHit))
        {
            return candidateHit;
        }
    }

    return directHit;
}

GameplayWorldHoverCacheState IndoorRenderer::gameplayWorldHoverCacheState() const
{
    return GameplayWorldHoverCacheState{
        .hasCachedHover = m_cachedInspectHitValid && m_cachedGameplayWorldPickRequest.hasRay,
        .lastUpdateNanoseconds = m_lastInspectUpdateTick * 1000000ULL,
    };
}

GameplayHoverStatusPayload IndoorRenderer::refreshGameplayWorldHover(const GameplayWorldHoverRequest &request)
{
    GameplayHoverStatusPayload payload = {};
    GameplayWorldPickRequest pickRequest = request.primaryPickRequest;

    if (!pickRequest.hasRay)
    {
        pickRequest = buildGameplayWorldPickRequest(
            GameplayWorldPickRequestInput{
                .screenX = pickRequest.screenX,
                .screenY = pickRequest.screenY,
                .screenWidth = pickRequest.viewWidth,
                .screenHeight = pickRequest.viewHeight,
                .includeRay = true,
            });
    }

    std::optional<InspectHit> inspectHit = inspectGameplayWorldHit(pickRequest);

    if (request.probeKind == GameplayWorldHoverProbeKind::PendingSpell
        && request.secondaryPickRequest
        && (!inspectHit || !inspectHit->hasHit))
    {
        pickRequest = *request.secondaryPickRequest;

        if (!pickRequest.hasRay)
        {
            pickRequest = buildGameplayWorldPickRequest(
                GameplayWorldPickRequestInput{
                    .screenX = pickRequest.screenX,
                    .screenY = pickRequest.screenY,
                    .screenWidth = pickRequest.viewWidth,
                    .screenHeight = pickRequest.viewHeight,
                    .includeRay = true,
                });
        }

        inspectHit = inspectGameplayWorldHit(pickRequest);
    }

    if (inspectHit)
    {
        m_cachedInspectHit = *inspectHit;
        m_cachedInspectHitValid = true;
        m_cachedGameplayWorldPickRequest = pickRequest;
        m_lastInspectUpdateTick = request.updateTickNanoseconds / 1000000ULL;
        payload.worldHit = pickGameplayWorldHit(pickRequest);
    }
    else
    {
        clearGameplayWorldHover();
    }

    return payload;
}

GameplayHoverStatusPayload IndoorRenderer::readCachedGameplayWorldHover() const
{
    GameplayHoverStatusPayload payload = {};

    if (!m_cachedInspectHitValid || !m_cachedGameplayWorldPickRequest.hasRay)
    {
        return payload;
    }

    payload.worldHit = translateInspectHitToGameplayWorldHit(m_cachedInspectHit, m_cachedGameplayWorldPickRequest);
    return payload;
}

void IndoorRenderer::clearGameplayWorldHover()
{
    m_cachedInspectHit = {};
    m_cachedInspectHitValid = false;
    m_cachedGameplayWorldPickRequest = {};
}

std::optional<size_t> IndoorRenderer::gameplayHoveredActorIndex() const
{
    if (!m_cachedInspectHitValid || m_cachedInspectHit.kind != "actor")
    {
        return std::nullopt;
    }

    return m_cachedInspectHit.index;
}

std::optional<size_t> IndoorRenderer::gameplayClosestVisibleHostileActorIndex() const
{
    if (!m_isInitialized
        || !m_isRenderable
        || m_pSceneRuntime == nullptr
        || m_lastRenderWidth <= 0
        || m_lastRenderHeight <= 0)
    {
        return std::nullopt;
    }

    const float aspectRatio = float(m_lastRenderWidth) / float(m_lastRenderHeight);
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
        m_cameraPositionY + sinYaw * cosPitch,
        m_cameraPositionZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    float viewProjectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        60.0f,
        aspectRatio,
        0.1f,
        50000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );
    bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);

    std::optional<size_t> nearestActorIndex;
    float nearestDistanceSquared = std::numeric_limits<float>::max();
    IGameplayWorldRuntime &worldRuntime = m_pSceneRuntime->worldRuntime();

    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!worldRuntime.actorRuntimeState(actorIndex, actorState)
            || actorState.isDead
            || actorState.isInvisible
            || !actorState.hostileToParty
            || !actorState.hasDetectedParty)
        {
            continue;
        }

        const bx::Vec3 actorPoint = {
            actorState.preciseX,
            actorState.preciseY,
            actorState.preciseZ + std::max(48.0f, float(actorState.height) * 0.6f)
        };
        ProjectedPoint projected = {};

        if (!projectWorldPointToScreen(
                actorPoint,
                m_lastRenderWidth,
                m_lastRenderHeight,
                viewProjectionMatrix,
                projected))
        {
            continue;
        }

        if (projected.x < 0.0f
            || projected.x > float(m_lastRenderWidth)
            || projected.y < 0.0f
            || projected.y > float(m_lastRenderHeight))
        {
            continue;
        }

        const float deltaX = actorState.preciseX - eye.x;
        const float deltaY = actorState.preciseY - eye.y;
        const float deltaZ = actorState.preciseZ - eye.z;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

        if (distanceSquared < nearestDistanceSquared)
        {
            nearestDistanceSquared = distanceSquared;
            nearestActorIndex = actorIndex;
        }
    }

    return nearestActorIndex;
}

std::optional<bx::Vec3> IndoorRenderer::gameplayActorTargetPoint(size_t actorIndex) const
{
    if (m_pSceneRuntime == nullptr)
    {
        return std::nullopt;
    }

    GameplayRuntimeActorState actorState = {};

    if (!m_pSceneRuntime->worldRuntime().actorRuntimeState(actorIndex, actorState)
        || actorState.isDead
        || actorState.isInvisible)
    {
        return std::nullopt;
    }

    return bx::Vec3 {
        actorState.preciseX,
        actorState.preciseY,
        actorState.preciseZ + std::max(48.0f, float(actorState.height) * 0.6f)
    };
}

std::optional<bx::Vec3> IndoorRenderer::gameplayGroundTargetPoint(float screenX, float screenY) const
{
    if (m_lastRenderWidth <= 0 || m_lastRenderHeight <= 0)
    {
        return std::nullopt;
    }

    const GameplayWorldPickRequest request = buildGameplayWorldPickRequest(
        GameplayWorldPickRequestInput{
            .screenX = screenX,
            .screenY = screenY,
            .screenWidth = m_lastRenderWidth,
            .screenHeight = m_lastRenderHeight,
            .includeRay = true,
        });

    if (!request.hasRay)
    {
        return std::nullopt;
    }

    const GameplayWorldHit worldHit = pickGameplayWorldHit(request);

    if (worldHit.kind == GameplayWorldHitKind::Actor && worldHit.actor)
    {
        const std::optional<bx::Vec3> actorTargetPoint =
            gameplayActorTargetPoint(worldHit.actor->actorIndex);

        if (actorTargetPoint)
        {
            return actorTargetPoint;
        }

        return worldHit.actor->hitPoint;
    }

    if (worldHit.ground && worldHit.ground->isValid)
    {
        return worldHit.ground->worldPoint;
    }

    if (worldHit.worldItem)
    {
        return worldHit.worldItem->hitPoint;
    }

    if (worldHit.eventTarget)
    {
        return worldHit.eventTarget->hitPoint;
    }

    if (worldHit.object)
    {
        return worldHit.object->hitPoint;
    }

    constexpr float ForwardFallbackDistance = 4096.0f;
    return bx::Vec3 {
        request.rayOrigin.x + request.rayDirection.x * ForwardFallbackDistance,
        request.rayOrigin.y + request.rayDirection.y * ForwardFallbackDistance,
        request.rayOrigin.z + request.rayDirection.z * ForwardFallbackDistance
    };
}

float IndoorRenderer::cameraYawRadians() const
{
    return m_cameraYawRadians;
}

float IndoorRenderer::cameraPitchRadians() const
{
    return m_cameraPitchRadians;
}

std::optional<IndoorRenderer::InspectHit> IndoorRenderer::inspectHitFromGameplayWorldHit(
    const GameplayWorldHit &hit) const
{
    if (!hit.hasHit || hit.kind != GameplayWorldHitKind::EventTarget || !hit.eventTarget)
    {
        return std::nullopt;
    }

    InspectHit inspectHit = {};
    const GameplayEventTargetHit &eventTarget = *hit.eventTarget;
    inspectHit.hasHit = true;
    inspectHit.index = eventTarget.targetIndex;
    inspectHit.name = eventTarget.name;
    inspectHit.distance = eventTarget.distance;
    inspectHit.eventIdPrimary = eventTarget.eventIdPrimary;
    inspectHit.eventIdSecondary = eventTarget.eventIdSecondary;
    inspectHit.cogTriggered = eventTarget.triggeredEventId;
    inspectHit.cogTriggerType = eventTarget.trigger;
    inspectHit.variablePrimary = eventTarget.variablePrimary;
    inspectHit.variableSecondary = eventTarget.variableSecondary;
    inspectHit.specialTrigger = eventTarget.specialTrigger;
    inspectHit.attributes = eventTarget.attributes;

    if (eventTarget.targetKind == GameplayWorldEventTargetKind::Surface)
    {
        inspectHit.kind = "face";
    }
    else if (eventTarget.targetKind == GameplayWorldEventTargetKind::Entity)
    {
        inspectHit.kind = "entity";
    }
    else if (eventTarget.targetKind == GameplayWorldEventTargetKind::Spawn)
    {
        inspectHit.kind = "spawn";
    }
    else if (eventTarget.targetKind == GameplayWorldEventTargetKind::Object)
    {
        inspectHit.kind = "mechanism";
        inspectHit.doorId = eventTarget.triggeredEventId;
        inspectHit.mechanismLinkedEventId = eventTarget.triggeredEventId;
    }
    else
    {
        return std::nullopt;
    }

    return inspectHit;
}

bool IndoorRenderer::canActivateGameplayWorldHit(const GameplayWorldHit &hit) const
{
    const std::optional<InspectHit> inspectHit = inspectHitFromGameplayWorldHit(hit);

    if (!inspectHit)
    {
        return false;
    }

    if (inspectHit->kind == "entity")
    {
        return inspectHit->eventIdPrimary != 0 || inspectHit->eventIdSecondary != 0;
    }

    if (inspectHit->kind == "face")
    {
        return inspectHit->cogTriggered != 0;
    }

    if (inspectHit->kind == "mechanism")
    {
        return inspectHit->mechanismLinkedEventId != 0 || inspectHit->doorId != 0;
    }

    return false;
}

bool IndoorRenderer::activateGameplayWorldHit(const GameplayWorldHit &hit)
{
    const std::optional<InspectHit> inspectHit = inspectHitFromGameplayWorldHit(hit);

    if (!inspectHit)
    {
        return false;
    }

    return tryActivateInspectEvent(*inspectHit);
}

void IndoorRenderer::shutdown()
{
    m_indoorMapData.reset();
    m_renderVertices.clear();
    m_pSceneRuntime = nullptr;
    m_pAssetFileSystem = nullptr;
    m_pItemTable = nullptr;
    m_spriteLoadCache = {};
    m_indoorTextureSet.reset();
    m_map.reset();
    m_monsterTable.reset();
    m_objectTable.reset();
    m_indoorDecorationBillboardSet.reset();
    m_indoorActorPreviewBillboardSet.reset();
    m_indoorSpriteObjectBillboardSet.reset();
    m_houseTable.reset();
    m_mechanismBindings.clear();
    m_worldFxSystem.reset();
    ParticleRenderer::shutdownResources(m_worldFxRenderResources);

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

    if (bgfx::isValid(m_indoorLitProgramHandle))
    {
        bgfx::destroy(m_indoorLitProgramHandle);
        m_indoorLitProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_billboardProgramHandle))
    {
        bgfx::destroy(m_billboardProgramHandle);
        m_billboardProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_bloodSplatVertexBufferHandle))
    {
        bgfx::destroy(m_bloodSplatVertexBufferHandle);
        m_bloodSplatVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_bloodSplatTextureHandle))
    {
        bgfx::destroy(m_bloodSplatTextureHandle);
        m_bloodSplatTextureHandle = BGFX_INVALID_HANDLE;
    }

    m_bloodSplatVertexCount = 0;
    m_bloodSplatVertexBufferRevision = std::numeric_limits<uint64_t>::max();

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

    if (bgfx::isValid(m_indoorLightPositionsUniformHandle))
    {
        bgfx::destroy(m_indoorLightPositionsUniformHandle);
        m_indoorLightPositionsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_indoorLightColorsUniformHandle))
    {
        bgfx::destroy(m_indoorLightColorsUniformHandle);
        m_indoorLightColorsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_indoorLightParamsUniformHandle))
    {
        bgfx::destroy(m_indoorLightParamsUniformHandle);
        m_indoorLightParamsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_billboardAmbientUniformHandle))
    {
        bgfx::destroy(m_billboardAmbientUniformHandle);
        m_billboardAmbientUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_billboardOverrideColorUniformHandle))
    {
        bgfx::destroy(m_billboardOverrideColorUniformHandle);
        m_billboardOverrideColorUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_billboardOutlineParamsUniformHandle))
    {
        bgfx::destroy(m_billboardOutlineParamsUniformHandle);
        m_billboardOutlineParamsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_billboardFogColorUniformHandle))
    {
        bgfx::destroy(m_billboardFogColorUniformHandle);
        m_billboardFogColorUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_billboardFogDensitiesUniformHandle))
    {
        bgfx::destroy(m_billboardFogDensitiesUniformHandle);
        m_billboardFogDensitiesUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_billboardFogDistancesUniformHandle))
    {
        bgfx::destroy(m_billboardFogDistancesUniformHandle);
        m_billboardFogDistancesUniformHandle = BGFX_INVALID_HANDLE;
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
    m_isRenderable = false;
    m_isInitialized = false;
}

const std::optional<MapDeltaData> &IndoorRenderer::runtimeMapDeltaData() const
{
    static const std::optional<MapDeltaData> EmptyMapDeltaData = std::nullopt;
    return m_pSceneRuntime != nullptr ? m_pSceneRuntime->mapDeltaData() : EmptyMapDeltaData;
}

const std::optional<EventRuntimeState> &IndoorRenderer::runtimeEventRuntimeStateStorage() const
{
    static const std::optional<EventRuntimeState> EmptyEventRuntimeState = std::nullopt;
    return m_pSceneRuntime != nullptr ? m_pSceneRuntime->eventRuntimeStateStorage() : EmptyEventRuntimeState;
}

EventRuntimeState *IndoorRenderer::runtimeEventRuntimeState()
{
    return m_pSceneRuntime != nullptr ? m_pSceneRuntime->eventRuntimeState() : nullptr;
}

const EventRuntimeState *IndoorRenderer::runtimeEventRuntimeState() const
{
    return m_pSceneRuntime != nullptr ? m_pSceneRuntime->eventRuntimeState() : nullptr;
}

void IndoorRenderer::TerrainVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

void IndoorRenderer::TexturedVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
}

void IndoorRenderer::LitBillboardVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

bgfx::ProgramHandle IndoorRenderer::loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadShader(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadShader(pFragmentShaderName);

    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        std::cerr
            << "IndoorRenderer: loadProgram failed"
            << " vs=" << (pVertexShaderName != nullptr ? pVertexShaderName : "<null>")
            << " fs=" << (pFragmentShaderName != nullptr ? pFragmentShaderName : "<null>")
            << '\n';
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

bgfx::ShaderHandle IndoorRenderer::loadShader(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        std::cerr
            << "IndoorRenderer: loadShader could not resolve shader path for "
            << (pShaderName != nullptr ? pShaderName : "<null>")
            << '\n';
        return BGFX_INVALID_HANDLE;
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        std::cerr
            << "IndoorRenderer: loadShader read empty shader file "
            << shaderPath.string()
            << '\n';
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createShader(bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size())));
}

void IndoorRenderer::setCameraPosition(float x, float y, float z)
{
    m_cameraPositionX = x;
    m_cameraPositionY = y;
    m_cameraPositionZ = z;

    if (m_pSceneRuntime != nullptr)
    {
        m_pSceneRuntime->partyRuntime().teleportEyePosition(x, y, z);
    }
}

const IndoorRenderer::BillboardTextureHandle *IndoorRenderer::findBillboardTexture(
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

const IndoorRenderer::BillboardTextureHandle *IndoorRenderer::ensureSpriteBillboardTexture(
    const std::string &textureName,
    int16_t paletteId)
{
    const BillboardTextureHandle *pExistingTexture = findBillboardTexture(textureName, paletteId);

    if (pExistingTexture != nullptr)
    {
        return pExistingTexture;
    }

    int textureWidth = 0;
    int textureHeight = 0;
    const std::optional<std::vector<uint8_t>> pixels =
        GameplayHudCommon::loadSpriteBitmapPixelsBgraCached(
            m_pAssetFileSystem,
            m_spriteLoadCache,
            textureName,
            paletteId,
            textureWidth,
            textureHeight);

    if (!pixels || textureWidth <= 0 || textureHeight <= 0)
    {
        return nullptr;
    }

    BillboardTextureHandle billboardTexture = {};
    billboardTexture.textureName = toLowerCopy(textureName);
    billboardTexture.paletteId = paletteId;
    billboardTexture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, m_assetScaleTier);
    billboardTexture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, m_assetScaleTier);
    billboardTexture.physicalWidth = textureWidth;
    billboardTexture.physicalHeight = textureHeight;
    billboardTexture.pixels = *pixels;
    billboardTexture.textureHandle = createBgraTexture2D(
        uint16_t(textureWidth),
        uint16_t(textureHeight),
        pixels->data(),
        uint32_t(pixels->size()),
        TextureFilterProfile::Billboard,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    if (!bgfx::isValid(billboardTexture.textureHandle))
    {
        return nullptr;
    }

    m_billboardTextureHandles.push_back(std::move(billboardTexture));
    return &m_billboardTextureHandles.back();
}

bgfx::TextureHandle IndoorRenderer::ensureBloodSplatTexture()
{
    if (bgfx::isValid(m_bloodSplatTextureHandle))
    {
        return m_bloodSplatTextureHandle;
    }

    const std::optional<std::string> bitmapPath =
        GameplayHudCommon::findCachedAssetPath(
            m_pAssetFileSystem,
            m_spriteLoadCache,
            "Data/bitmaps",
            "hwsplat04.bmp");

    if (!bitmapPath)
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes =
        GameplayHudCommon::readCachedBinaryFile(m_pAssetFileSystem, m_spriteLoadCache, *bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return BGFX_INVALID_HANDLE;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return BGFX_INVALID_HANDLE;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return BGFX_INVALID_HANDLE;
    }

    const int textureWidth = pConvertedSurface->w;
    const int textureHeight = pConvertedSurface->h;
    const size_t pixelCount = size_t(textureWidth) * size_t(textureHeight) * 4;
    std::vector<uint8_t> pixels(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);
    SDL_DestroySurface(pConvertedSurface);

    for (size_t offset = 0; offset + 3 < pixels.size(); offset += 4)
    {
        const uint8_t intensity = std::max({pixels[offset + 0], pixels[offset + 1], pixels[offset + 2]});

        if (intensity == 0)
        {
            pixels[offset + 0] = 0;
            pixels[offset + 1] = 0;
            pixels[offset + 2] = 0;
            pixels[offset + 3] = 0;
            continue;
        }

        const float factor = static_cast<float>(intensity) / 255.0f;
        pixels[offset + 0] = static_cast<uint8_t>(std::lround(4.0f + 14.0f * factor));
        pixels[offset + 1] = static_cast<uint8_t>(std::lround(8.0f + 20.0f * factor));
        pixels[offset + 2] = static_cast<uint8_t>(std::lround(72.0f + 120.0f * factor));
        pixels[offset + 3] = intensity;
    }

    m_bloodSplatTextureHandle = createBgraTexture2D(
        uint16_t(textureWidth),
        uint16_t(textureHeight),
        pixels.data(),
        uint32_t(pixels.size()),
        TextureFilterProfile::BModel,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    return m_bloodSplatTextureHandle;
}

void IndoorRenderer::ensureBloodSplatVertexBuffer()
{
    if (m_pSceneRuntime == nullptr)
    {
        if (bgfx::isValid(m_bloodSplatVertexBufferHandle))
        {
            bgfx::destroy(m_bloodSplatVertexBufferHandle);
            m_bloodSplatVertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        m_bloodSplatVertexCount = 0;
        m_bloodSplatVertexBufferRevision = std::numeric_limits<uint64_t>::max();
        return;
    }

    const IndoorWorldRuntime &worldRuntime = m_pSceneRuntime->worldRuntime();
    const uint64_t revision = worldRuntime.bloodSplatRevision();

    if (m_bloodSplatVertexBufferRevision == revision)
    {
        return;
    }

    m_bloodSplatVertexBufferRevision = revision;

    if (bgfx::isValid(m_bloodSplatVertexBufferHandle))
    {
        bgfx::destroy(m_bloodSplatVertexBufferHandle);
        m_bloodSplatVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    m_bloodSplatVertexCount = 0;
    size_t totalVertexCount = 0;

    for (size_t splatIndex = 0; splatIndex < worldRuntime.bloodSplatCount(); ++splatIndex)
    {
        const IndoorWorldRuntime::BloodSplatState *pSplat = worldRuntime.bloodSplatState(splatIndex);

        if (pSplat != nullptr)
        {
            totalVertexCount += pSplat->vertices.size();
        }
    }

    if (totalVertexCount == 0)
    {
        return;
    }

    std::vector<TexturedVertex> vertices;
    vertices.reserve(totalVertexCount);

    for (size_t splatIndex = 0; splatIndex < worldRuntime.bloodSplatCount(); ++splatIndex)
    {
        const IndoorWorldRuntime::BloodSplatState *pSplat = worldRuntime.bloodSplatState(splatIndex);

        if (pSplat == nullptr || pSplat->vertices.empty())
        {
            continue;
        }

        for (const IndoorWorldRuntime::BloodSplatState::Vertex &sourceVertex : pSplat->vertices)
        {
            TexturedVertex vertex = {};
            vertex.x = sourceVertex.x;
            vertex.y = sourceVertex.y;
            vertex.z = sourceVertex.z;
            vertex.u = sourceVertex.u;
            vertex.v = sourceVertex.v;
            vertices.push_back(vertex);
        }
    }

    const bgfx::Memory *pVertexMemory = bgfx::copy(
        vertices.data(),
        uint32_t(vertices.size() * sizeof(TexturedVertex)));
    m_bloodSplatVertexBufferHandle = bgfx::createVertexBuffer(pVertexMemory, TexturedVertex::ms_layout);
    m_bloodSplatVertexCount = uint32_t(vertices.size());
}

void IndoorRenderer::renderBloodSplats(
    uint16_t viewId,
    const std::array<float, 32> &indoorLightPositions,
    const std::array<float, 32> &indoorLightColors,
    const std::array<float, 4> &indoorLightParams)
{
    if (m_pSceneRuntime == nullptr
        || !bgfx::isValid(m_indoorLitProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle)
        || !bgfx::isValid(m_indoorLightPositionsUniformHandle)
        || !bgfx::isValid(m_indoorLightColorsUniformHandle)
        || !bgfx::isValid(m_indoorLightParamsUniformHandle)
        || m_pSceneRuntime->worldRuntime().bloodSplatCount() == 0)
    {
        return;
    }

    const bgfx::TextureHandle textureHandle = ensureBloodSplatTexture();

    if (!bgfx::isValid(textureHandle))
    {
        return;
    }

    ensureBloodSplatVertexBuffer();

    if (!bgfx::isValid(m_bloodSplatVertexBufferHandle) || m_bloodSplatVertexCount == 0)
    {
        return;
    }

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, m_bloodSplatVertexBufferHandle, 0, m_bloodSplatVertexCount);
    bindTexture(
        0,
        m_textureSamplerHandle,
        textureHandle,
        TextureFilterProfile::BModel,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setUniform(m_indoorLightPositionsUniformHandle, indoorLightPositions.data(), MaxIndoorShaderLights);
    bgfx::setUniform(m_indoorLightColorsUniformHandle, indoorLightColors.data(), MaxIndoorShaderLights);
    bgfx::setUniform(m_indoorLightParamsUniformHandle, indoorLightParams.data());
    bgfx::setState(
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_WRITE_Z
        | BGFX_STATE_DEPTH_TEST_LEQUAL
        | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, m_indoorLitProgramHandle);
}

void IndoorRenderer::renderDecorationBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask,
    const IndoorLightingFrame &lightingFrame
)
{
    if (!m_indoorDecorationBillboardSet
        || !bgfx::isValid(m_billboardProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle)
        || !bgfx::isValid(m_billboardAmbientUniformHandle)
        || !bgfx::isValid(m_billboardOverrideColorUniformHandle)
        || !bgfx::isValid(m_billboardOutlineParamsUniformHandle)
        || !bgfx::isValid(m_billboardFogColorUniformHandle)
        || !bgfx::isValid(m_billboardFogDensitiesUniformHandle)
        || !bgfx::isValid(m_billboardFogDistancesUniformHandle))
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

        if (pTexture == nullptr
            || !bgfx::isValid(pTexture->textureHandle)
            || pTexture->width <= 0
            || pTexture->height <= 0)
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
        const bx::Vec3 up = {
            cameraUp.x * worldHeight * 0.5f,
            cameraUp.y * worldHeight * 0.5f,
            cameraUp.z * worldHeight * 0.5f
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
        const uint32_t vertexColorAbgr = makeAbgr(0, 0, 0);
        const std::array<float, 4> ambient = billboardLightingUniform(lightingFrame, frame, center);
        const float clearOverrideColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float clearOutlineParams[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogDensities[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogDistances[4] = {4096.0f, 4096.0f, 4096.0f, 0.0f};
        std::array<LitBillboardVertex, 6> vertices = {};
        vertices[0] = {
            center.x - right.x - up.x,
            center.y - right.y - up.y,
            center.z - right.z - up.z,
            u0,
            1.0f,
            vertexColorAbgr
        };
        vertices[1] = {
            center.x - right.x + up.x,
            center.y - right.y + up.y,
            center.z - right.z + up.z,
            u0,
            0.0f,
            vertexColorAbgr
        };
        vertices[2] = {
            center.x + right.x + up.x,
            center.y + right.y + up.y,
            center.z + right.z + up.z,
            u1,
            0.0f,
            vertexColorAbgr
        };
        vertices[3] = vertices[0];
        vertices[4] = vertices[2];
        vertices[5] = {
            center.x + right.x - up.x,
            center.y + right.y - up.y,
            center.z + right.z - up.z,
            u1,
            1.0f,
            vertexColorAbgr
        };

        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), LitBillboardVertex::ms_layout)
            < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            LitBillboardVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(LitBillboardVertex))
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
        bgfx::setUniform(m_billboardAmbientUniformHandle, ambient.data());
        bgfx::setUniform(m_billboardOverrideColorUniformHandle, clearOverrideColor);
        bgfx::setUniform(m_billboardOutlineParamsUniformHandle, clearOutlineParams);
        bgfx::setUniform(m_billboardFogColorUniformHandle, fogColor);
        bgfx::setUniform(m_billboardFogDensitiesUniformHandle, fogDensities);
        bgfx::setUniform(m_billboardFogDistancesUniformHandle, fogDistances);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(viewId, m_billboardProgramHandle);
    }
}

void IndoorRenderer::renderActorPreviewBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask,
    const IndoorLightingFrame &lightingFrame
)
{
    if (!m_indoorActorPreviewBillboardSet
        || !bgfx::isValid(m_billboardProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle)
        || !bgfx::isValid(m_billboardAmbientUniformHandle)
        || !bgfx::isValid(m_billboardOverrideColorUniformHandle)
        || !bgfx::isValid(m_billboardOutlineParamsUniformHandle)
        || !bgfx::isValid(m_billboardFogColorUniformHandle)
        || !bgfx::isValid(m_billboardFogDensitiesUniformHandle)
        || !bgfx::isValid(m_billboardFogDistancesUniformHandle))
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
        bool hovered = false;
        uint32_t hoveredOutlineColorAbgr = 0;
        float distanceSquared = 0.0f;
    };

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::optional<size_t> hoveredActorIndex =
        m_cachedInspectHitValid && m_cachedInspectHit.kind == "actor"
        ? std::optional<size_t>(m_cachedInspectHit.index)
        : std::nullopt;
    const std::vector<RuntimeActorBillboard> runtimeBillboards =
        mapDeltaData && m_monsterTable
        ? buildRuntimeActorBillboards(
            *m_monsterTable,
            m_indoorActorPreviewBillboardSet->spriteFrameTable,
            *mapDeltaData,
            m_pSceneRuntime != nullptr ? &m_pSceneRuntime->worldRuntime() : nullptr)
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

            const IndoorWorldRuntime::MapActorAiState *pActorAiState =
                m_pSceneRuntime != nullptr
                    ? m_pSceneRuntime->worldRuntime().mapActorAiState(billboard.actorIndex)
                    : nullptr;
            uint16_t spriteFrameIndex = billboard.spriteFrameIndex;
            uint32_t frameTimeTicks = billboard.useStaticFrame ? 0U : animationTimeTicks;

            if (pActorAiState != nullptr)
            {
                const size_t animationIndex = static_cast<size_t>(pActorAiState->animationState);

                if (animationIndex < billboard.actionSpriteFrameIndices.size()
                    && billboard.actionSpriteFrameIndices[animationIndex] != 0)
                {
                    spriteFrameIndex = billboard.actionSpriteFrameIndices[animationIndex];
                }

                frameTimeTicks = static_cast<uint32_t>(std::max(0.0f, pActorAiState->animationTimeTicks));
            }

            const SpriteFrameEntry *pFrame =
                m_indoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, frameTimeTicks);

            if (pFrame == nullptr)
            {
                continue;
            }

            const float angleToCamera = std::atan2(
                static_cast<float>(billboard.y) - cameraPosition.y,
                static_cast<float>(billboard.x) - cameraPosition.x
            );
            const float actorYawRadians = pActorAiState != nullptr ? pActorAiState->yawRadians : 0.0f;
            const float octantAngle = actorYawRadians - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

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
            drawItem.hovered = hoveredActorIndex && *hoveredActorIndex == billboard.actorIndex;
            if (drawItem.hovered && mapDeltaData && billboard.actorIndex < mapDeltaData->actors.size())
            {
                drawItem.hoveredOutlineColorAbgr =
                    resolveHoveredIndoorActorOutlineColor(
                        mapDeltaData->actors[billboard.actorIndex],
                        pActorAiState);
            }
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
                ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

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
        const bx::Vec3 center = bottomAnchoredBillboardCenter(
            static_cast<float>(drawItem.x),
            static_cast<float>(drawItem.y),
            static_cast<float>(drawItem.z),
            cameraUp,
            worldHeight);
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {
            cameraUp.x * worldHeight * 0.5f,
            cameraUp.y * worldHeight * 0.5f,
            cameraUp.z * worldHeight * 0.5f
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
        const uint32_t vertexColorAbgr = makeAbgr(0, 0, 0);
        const std::array<float, 4> ambient = billboardLightingUniform(lightingFrame, frame, center);
        const float clearOverrideColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float clearOutlineParams[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogDensities[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogDistances[4] = {4096.0f, 4096.0f, 4096.0f, 0.0f};

        if (drawItem.hovered)
        {
            const float paddingU = HoveredActorOutlineThicknessPixels / static_cast<float>(texture.width);
            const float paddingV = HoveredActorOutlineThicknessPixels / static_cast<float>(texture.height);
            const float outlinedHalfWidth =
                (static_cast<float>(texture.width) * spriteScale
                    + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale) * 0.5f;
            const float outlinedHalfHeight =
                (static_cast<float>(texture.height) * spriteScale
                    + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale) * 0.5f;
            const bx::Vec3 outlineRight = {
                cameraRight.x * outlinedHalfWidth,
                cameraRight.y * outlinedHalfWidth,
                cameraRight.z * outlinedHalfWidth
            };
            const bx::Vec3 outlineUp = {
                cameraUp.x * outlinedHalfHeight,
                cameraUp.y * outlinedHalfHeight,
                cameraUp.z * outlinedHalfHeight
            };
            const float outlineU0 = drawItem.mirrored ? 1.0f + paddingU : -paddingU;
            const float outlineU1 = drawItem.mirrored ? -paddingU : 1.0f + paddingU;
            const float outlineVTop = -paddingV;
            const float outlineVBottom = 1.0f + paddingV;
            std::array<LitBillboardVertex, 6> outlineVertices = {{
                {
                    center.x - outlineRight.x - outlineUp.x,
                    center.y - outlineRight.y - outlineUp.y,
                    center.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    center.x - outlineRight.x + outlineUp.x,
                    center.y - outlineRight.y + outlineUp.y,
                    center.z - outlineRight.z + outlineUp.z,
                    outlineU0,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    center.x + outlineRight.x + outlineUp.x,
                    center.y + outlineRight.y + outlineUp.y,
                    center.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    center.x - outlineRight.x - outlineUp.x,
                    center.y - outlineRight.y - outlineUp.y,
                    center.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    center.x + outlineRight.x + outlineUp.x,
                    center.y + outlineRight.y + outlineUp.y,
                    center.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    center.x + outlineRight.x - outlineUp.x,
                    center.y + outlineRight.y - outlineUp.y,
                    center.z + outlineRight.z - outlineUp.z,
                    outlineU1,
                    outlineVBottom,
                    vertexColorAbgr
                }
            }};

            if (bgfx::getAvailTransientVertexBuffer(
                    static_cast<uint32_t>(outlineVertices.size()),
                    LitBillboardVertex::ms_layout) >= outlineVertices.size())
            {
                bgfx::TransientVertexBuffer outlineTransientVertexBuffer = {};
                bgfx::allocTransientVertexBuffer(
                    &outlineTransientVertexBuffer,
                    static_cast<uint32_t>(outlineVertices.size()),
                    LitBillboardVertex::ms_layout);
                std::memcpy(
                    outlineTransientVertexBuffer.data,
                    outlineVertices.data(),
                    static_cast<size_t>(outlineVertices.size() * sizeof(LitBillboardVertex)));

                const float overrideColor[4] = {
                    redChannel(drawItem.hoveredOutlineColorAbgr),
                    greenChannel(drawItem.hoveredOutlineColorAbgr),
                    blueChannel(drawItem.hoveredOutlineColorAbgr),
                    1.0f
                };
                const float outlineParams[4] = {
                    1.0f / static_cast<float>(texture.width),
                    1.0f / static_cast<float>(texture.height),
                    HoveredActorOutlineThicknessPixels,
                    1.0f
                };
                float modelMatrix[16] = {};
                bx::mtxIdentity(modelMatrix);
                bgfx::setTransform(modelMatrix);
                bgfx::setVertexBuffer(
                    0,
                    &outlineTransientVertexBuffer,
                    0,
                    static_cast<uint32_t>(outlineVertices.size()));
                bindTexture(
                    0,
                    m_textureSamplerHandle,
                    texture.textureHandle,
                    TextureFilterProfile::Billboard,
                    BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                bgfx::setUniform(m_billboardAmbientUniformHandle, ambient.data());
                bgfx::setUniform(m_billboardOverrideColorUniformHandle, overrideColor);
                bgfx::setUniform(m_billboardOutlineParamsUniformHandle, outlineParams);
                bgfx::setUniform(m_billboardFogColorUniformHandle, fogColor);
                bgfx::setUniform(m_billboardFogDensitiesUniformHandle, fogDensities);
                bgfx::setUniform(m_billboardFogDistancesUniformHandle, fogDistances);
                bgfx::setState(
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LEQUAL
                    | BGFX_STATE_BLEND_ALPHA);
                bgfx::submit(viewId, m_billboardProgramHandle);
            }
        }

        std::array<LitBillboardVertex, 6> vertices = {};
        vertices[0] = {
            center.x - right.x - up.x,
            center.y - right.y - up.y,
            center.z - right.z - up.z,
            u0,
            1.0f,
            vertexColorAbgr
        };
        vertices[1] = {
            center.x - right.x + up.x,
            center.y - right.y + up.y,
            center.z - right.z + up.z,
            u0,
            0.0f,
            vertexColorAbgr
        };
        vertices[2] = {
            center.x + right.x + up.x,
            center.y + right.y + up.y,
            center.z + right.z + up.z,
            u1,
            0.0f,
            vertexColorAbgr
        };
        vertices[3] = vertices[0];
        vertices[4] = vertices[2];
        vertices[5] = {
            center.x + right.x - up.x,
            center.y + right.y - up.y,
            center.z + right.z - up.z,
            u1,
            1.0f,
            vertexColorAbgr
        };

        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), LitBillboardVertex::ms_layout)
            < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            LitBillboardVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(LitBillboardVertex))
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
        bgfx::setUniform(m_billboardAmbientUniformHandle, ambient.data());
        bgfx::setUniform(m_billboardOverrideColorUniformHandle, clearOverrideColor);
        bgfx::setUniform(m_billboardOutlineParamsUniformHandle, clearOutlineParams);
        bgfx::setUniform(m_billboardFogColorUniformHandle, fogColor);
        bgfx::setUniform(m_billboardFogDensitiesUniformHandle, fogDensities);
        bgfx::setUniform(m_billboardFogDistancesUniformHandle, fogDistances);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(viewId, m_billboardProgramHandle);
    }
}

void IndoorRenderer::renderSpriteObjectBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask,
    const IndoorLightingFrame &lightingFrame
)
{
    if (!bgfx::isValid(m_billboardProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle)
        || !bgfx::isValid(m_billboardAmbientUniformHandle)
        || !bgfx::isValid(m_billboardOverrideColorUniformHandle)
        || !bgfx::isValid(m_billboardOutlineParamsUniformHandle)
        || !bgfx::isValid(m_billboardFogColorUniformHandle)
        || !bgfx::isValid(m_billboardFogDensitiesUniformHandle)
        || !bgfx::isValid(m_billboardFogDistancesUniformHandle))
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (m_indoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &m_indoorSpriteObjectBillboardSet->spriteFrameTable;
    }
    else if (m_indoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &m_indoorActorPreviewBillboardSet->spriteFrameTable;
    }
    else if (m_indoorDecorationBillboardSet)
    {
        pSpriteFrameTable = &m_indoorDecorationBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};

    struct BillboardDrawItem
    {
        size_t objectIndex = static_cast<size_t>(-1);
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        bool hovered = false;
        uint32_t hoveredOutlineColorAbgr = 0;
        float distanceSquared = 0.0f;
    };

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::vector<RuntimeSpriteObjectBillboard> runtimeBillboards =
        mapDeltaData && m_objectTable
        ? buildRuntimeSpriteObjectBillboards(*m_objectTable, m_pItemTable, *mapDeltaData)
        : std::vector<RuntimeSpriteObjectBillboard>{};
    std::vector<BillboardDrawItem> drawItems;
    const bool useRuntimeBillboards = !runtimeBillboards.empty();
    const size_t staticBillboardCount =
        m_indoorSpriteObjectBillboardSet ? m_indoorSpriteObjectBillboardSet->billboards.size() : 0;
    const std::optional<size_t> hoveredWorldItemIndex =
        m_cachedInspectHitValid && m_cachedInspectHit.kind == "object" && m_cachedInspectHit.hasContainingItem
        ? std::optional<size_t>(m_cachedInspectHit.index)
        : std::nullopt;
    drawItems.reserve(
        useRuntimeBillboards
        ? runtimeBillboards.size()
        : staticBillboardCount);
    auto appendProjectileDrawItem =
        [&](uint16_t cachedSpriteFrameIndex,
            uint16_t spriteId,
            const std::string &spriteName,
            float x,
            float y,
            float z,
            uint32_t timeTicks)
        {
            uint16_t spriteFrameIndex = cachedSpriteFrameIndex;

            if (spriteFrameIndex == 0 && !spriteName.empty())
            {
                const std::optional<uint16_t> spriteFrameIndexByName =
                    pSpriteFrameTable->findFrameIndexBySpriteName(spriteName);

                if (spriteFrameIndexByName)
                {
                    spriteFrameIndex = *spriteFrameIndexByName;
                }
            }

            if (spriteFrameIndex == 0)
            {
                spriteFrameIndex = spriteId;
            }

            if (spriteFrameIndex == 0)
            {
                return;
            }

            const SpriteFrameEntry *pFrame =
                pSpriteFrameTable->getFrame(spriteFrameIndex, timeTicks);

            if (pFrame == nullptr)
            {
                return;
            }

            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
            const BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                return;
            }

            const float deltaX = x - cameraPosition.x;
            const float deltaY = y - cameraPosition.y;
            const float deltaZ = z - cameraPosition.z;

            BillboardDrawItem drawItem = {};
            drawItem.x = x;
            drawItem.y = y;
            drawItem.z = z;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            drawItems.push_back(drawItem);
        };

    if (useRuntimeBillboards)
    {
        for (const RuntimeSpriteObjectBillboard &billboard : runtimeBillboards)
        {
            if (!isSectorVisible(billboard.sectorId, visibleSectorMask))
            {
                continue;
            }

            const SpriteFrameEntry *pFrame =
                pSpriteFrameTable->getFrame(
                    billboard.objectSpriteId,
                    billboard.timeSinceCreatedTicks
                );

            if (pFrame == nullptr)
            {
                continue;
            }

            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
            const BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                continue;
            }

            const float deltaX = float(billboard.x) - cameraPosition.x;
            const float deltaY = float(billboard.y) - cameraPosition.y;
            const float deltaZ = float(billboard.z) - cameraPosition.z;

            BillboardDrawItem drawItem = {};
            drawItem.objectIndex = billboard.objectIndex;
            drawItem.x = static_cast<float>(billboard.x);
            drawItem.y = static_cast<float>(billboard.y);
            drawItem.z = static_cast<float>(billboard.z);
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.hovered = hoveredWorldItemIndex && *hoveredWorldItemIndex == billboard.objectIndex;
            drawItem.hoveredOutlineColorAbgr =
                drawItem.hovered ? hoveredIndoorWorldItemOutlineColor() : 0;
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            drawItems.push_back(drawItem);
        }
    }
    else
    {
        if (m_indoorSpriteObjectBillboardSet)
        {
            for (const SpriteObjectBillboard &billboard : m_indoorSpriteObjectBillboardSet->billboards)
            {
                if (!isSectorVisible(billboard.sectorId, visibleSectorMask))
                {
                    continue;
                }

                const SpriteFrameEntry *pFrame =
                    pSpriteFrameTable->getFrame(
                        billboard.objectSpriteId,
                        billboard.timeSinceCreatedTicks
                    );

                if (pFrame == nullptr)
                {
                    continue;
                }

                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
                const BillboardTextureHandle *pTexture =
                    ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

                if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
                {
                    continue;
                }

                const float deltaX = float(billboard.x) - cameraPosition.x;
                const float deltaY = float(billboard.y) - cameraPosition.y;
                const float deltaZ = float(billboard.z) - cameraPosition.z;

                BillboardDrawItem drawItem = {};
                drawItem.x = static_cast<float>(billboard.x);
                drawItem.y = static_cast<float>(billboard.y);
                drawItem.z = static_cast<float>(billboard.z);
                drawItem.pFrame = pFrame;
                drawItem.pTexture = pTexture;
                drawItem.mirrored = resolvedTexture.mirrored;
                drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
                drawItems.push_back(drawItem);
            }
        }
    }

    if (m_pSceneRuntime != nullptr)
    {
        std::vector<GameplayProjectilePresentationState> projectiles;
        std::vector<GameplayProjectileImpactPresentationState> impacts;
        m_pSceneRuntime->worldRuntime().collectProjectilePresentationState(projectiles, impacts);

        for (const GameplayProjectilePresentationState &projectile : projectiles)
        {
            appendProjectileDrawItem(
                projectile.objectSpriteFrameIndex,
                projectile.objectSpriteId,
                projectile.objectSpriteName,
                projectile.x,
                projectile.y,
                projectile.z,
                projectile.timeSinceCreatedTicks);
        }

        for (const GameplayProjectileImpactPresentationState &impact : impacts)
        {
            const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
                impact.sourceSpellId,
                impact.sourceObjectName,
                impact.sourceObjectSpriteName,
                impact.sourceObjectFlags);

            if (FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe))
            {
                continue;
            }

            appendProjectileDrawItem(
                impact.objectSpriteFrameIndex,
                impact.objectSpriteId,
                impact.objectSpriteName,
                impact.x,
                impact.y,
                impact.z,
                impact.freezeAnimation ? 0u : impact.timeSinceCreatedTicks);
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

    const bool needsDepthPrepass =
        std::any_of(
            drawItems.begin(),
            drawItems.end(),
            [](const BillboardDrawItem &drawItem)
            {
                return drawItem.hovered;
            });

    if (needsDepthPrepass)
    {
        const float prepassAmbient[4] = {1.0f, 1.0f, 1.0f, 0.0f};
        const float prepassOverrideColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float prepassOutlineParams[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float prepassFogColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float prepassFogDensities[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float prepassFogDistances[4] = {4096.0f, 4096.0f, 4096.0f, 0.0f};

        for (const BillboardDrawItem &drawItem : drawItems)
        {
            const SpriteFrameEntry &frame = *drawItem.pFrame;
            const BillboardTextureHandle &texture = *drawItem.pTexture;
            const float spriteScale = std::max(frame.scale, 0.01f);
            const float worldWidth = float(texture.width) * spriteScale;
            const float worldHeight = float(texture.height) * spriteScale;
            const float halfWidth = worldWidth * 0.5f;
            const bx::Vec3 center = {
                drawItem.x,
                drawItem.y,
                drawItem.z + worldHeight * 0.5f
            };
            const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
            const bx::Vec3 up = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
            const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
            const uint32_t vertexColorAbgr = makeAbgr(0, 0, 0);
            std::array<LitBillboardVertex, 6> prepassVertices = {{
                {
                    center.x - right.x - up.x,
                    center.y - right.y - up.y,
                    center.z - right.z - up.z,
                    u0,
                    1.0f,
                    vertexColorAbgr
                },
                {
                    center.x - right.x + up.x,
                    center.y - right.y + up.y,
                    center.z - right.z + up.z,
                    u0,
                    0.0f,
                    vertexColorAbgr
                },
                {
                    center.x + right.x + up.x,
                    center.y + right.y + up.y,
                    center.z + right.z + up.z,
                    u1,
                    0.0f,
                    vertexColorAbgr
                },
                {
                    center.x - right.x - up.x,
                    center.y - right.y - up.y,
                    center.z - right.z - up.z,
                    u0,
                    1.0f,
                    vertexColorAbgr
                },
                {
                    center.x + right.x + up.x,
                    center.y + right.y + up.y,
                    center.z + right.z + up.z,
                    u1,
                    0.0f,
                    vertexColorAbgr
                },
                {
                    center.x + right.x - up.x,
                    center.y + right.y - up.y,
                    center.z + right.z - up.z,
                    u1,
                    1.0f,
                    vertexColorAbgr
                }
            }};

            if (bgfx::getAvailTransientVertexBuffer(
                    static_cast<uint32_t>(prepassVertices.size()),
                    LitBillboardVertex::ms_layout) < prepassVertices.size())
            {
                continue;
            }

            bgfx::TransientVertexBuffer prepassTransientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &prepassTransientVertexBuffer,
                static_cast<uint32_t>(prepassVertices.size()),
                LitBillboardVertex::ms_layout
            );
            std::memcpy(
                prepassTransientVertexBuffer.data,
                prepassVertices.data(),
                static_cast<size_t>(prepassVertices.size() * sizeof(LitBillboardVertex))
            );

            float prepassModelMatrix[16] = {};
            bx::mtxIdentity(prepassModelMatrix);
            bgfx::setTransform(prepassModelMatrix);
            bgfx::setVertexBuffer(
                0,
                &prepassTransientVertexBuffer,
                0,
                static_cast<uint32_t>(prepassVertices.size()));
            bindTexture(
                0,
                m_textureSamplerHandle,
                texture.textureHandle,
                TextureFilterProfile::Billboard,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
            bgfx::setUniform(m_billboardAmbientUniformHandle, prepassAmbient);
            bgfx::setUniform(m_billboardOverrideColorUniformHandle, prepassOverrideColor);
            bgfx::setUniform(m_billboardOutlineParamsUniformHandle, prepassOutlineParams);
            bgfx::setUniform(m_billboardFogColorUniformHandle, prepassFogColor);
            bgfx::setUniform(m_billboardFogDensitiesUniformHandle, prepassFogDensities);
            bgfx::setUniform(m_billboardFogDistancesUniformHandle, prepassFogDistances);
            bgfx::setState(
                BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_BLEND_ALPHA
            );
            bgfx::submit(viewId, m_billboardProgramHandle);
        }
    }

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = float(texture.width) * spriteScale;
        const float worldHeight = float(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            drawItem.x,
            drawItem.y,
            drawItem.z + worldHeight * 0.5f
        };
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {
            cameraUp.x * worldHeight * 0.5f,
            cameraUp.y * worldHeight * 0.5f,
            cameraUp.z * worldHeight * 0.5f
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        if (drawItem.hovered)
        {
            const float paddingU = HoveredActorOutlineThicknessPixels / static_cast<float>(texture.width);
            const float paddingV = HoveredActorOutlineThicknessPixels / static_cast<float>(texture.height);
            const float outlinedHalfWidth =
                (static_cast<float>(texture.width) * spriteScale
                    + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale) * 0.5f;
            const float outlinedHalfHeight =
                (static_cast<float>(texture.height) * spriteScale
                    + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale) * 0.5f;
            const bx::Vec3 outlineRight = {
                cameraRight.x * outlinedHalfWidth,
                cameraRight.y * outlinedHalfWidth,
                cameraRight.z * outlinedHalfWidth
            };
            const bx::Vec3 outlineUp = {
                cameraUp.x * outlinedHalfHeight,
                cameraUp.y * outlinedHalfHeight,
                cameraUp.z * outlinedHalfHeight
            };
            const float outlineU0 = drawItem.mirrored ? 1.0f + paddingU : -paddingU;
            const float outlineU1 = drawItem.mirrored ? -paddingU : 1.0f + paddingU;
            const float outlineVTop = -paddingV;
            const float outlineVBottom = 1.0f + paddingV;
            const uint32_t vertexColorAbgr = makeAbgr(0, 0, 0);
            std::array<LitBillboardVertex, 6> outlineVertices = {{
                {
                    center.x - outlineRight.x - outlineUp.x,
                    center.y - outlineRight.y - outlineUp.y,
                    center.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    center.x - outlineRight.x + outlineUp.x,
                    center.y - outlineRight.y + outlineUp.y,
                    center.z - outlineRight.z + outlineUp.z,
                    outlineU0,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    center.x + outlineRight.x + outlineUp.x,
                    center.y + outlineRight.y + outlineUp.y,
                    center.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    center.x - outlineRight.x - outlineUp.x,
                    center.y - outlineRight.y - outlineUp.y,
                    center.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    center.x + outlineRight.x + outlineUp.x,
                    center.y + outlineRight.y + outlineUp.y,
                    center.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    center.x + outlineRight.x - outlineUp.x,
                    center.y + outlineRight.y - outlineUp.y,
                    center.z + outlineRight.z - outlineUp.z,
                    outlineU1,
                    outlineVBottom,
                    vertexColorAbgr
                }
            }};

            if (bgfx::getAvailTransientVertexBuffer(
                    static_cast<uint32_t>(outlineVertices.size()),
                    LitBillboardVertex::ms_layout) >= outlineVertices.size())
            {
                bgfx::TransientVertexBuffer outlineTransientVertexBuffer = {};
                bgfx::allocTransientVertexBuffer(
                    &outlineTransientVertexBuffer,
                    static_cast<uint32_t>(outlineVertices.size()),
                    LitBillboardVertex::ms_layout);
                std::memcpy(
                    outlineTransientVertexBuffer.data,
                    outlineVertices.data(),
                    static_cast<size_t>(outlineVertices.size() * sizeof(LitBillboardVertex)));

                const float ambient[4] = {1.0f, 1.0f, 1.0f, 0.0f};
                const float overrideColor[4] = {
                    redChannel(drawItem.hoveredOutlineColorAbgr),
                    greenChannel(drawItem.hoveredOutlineColorAbgr),
                    blueChannel(drawItem.hoveredOutlineColorAbgr),
                    1.0f
                };
                const float outlineParams[4] = {
                    1.0f / static_cast<float>(texture.width),
                    1.0f / static_cast<float>(texture.height),
                    HoveredActorOutlineThicknessPixels,
                    1.0f
                };
                const float fogColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
                const float fogDensities[4] = {0.0f, 0.0f, 0.0f, 0.0f};
                const float fogDistances[4] = {4096.0f, 4096.0f, 4096.0f, 0.0f};
                float outlineModelMatrix[16] = {};
                bx::mtxIdentity(outlineModelMatrix);
                bgfx::setTransform(outlineModelMatrix);
                bgfx::setVertexBuffer(
                    0,
                    &outlineTransientVertexBuffer,
                    0,
                    static_cast<uint32_t>(outlineVertices.size()));
                bindTexture(
                    0,
                    m_textureSamplerHandle,
                    texture.textureHandle,
                    TextureFilterProfile::Billboard,
                    BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                bgfx::setUniform(m_billboardAmbientUniformHandle, ambient);
                bgfx::setUniform(m_billboardOverrideColorUniformHandle, overrideColor);
                bgfx::setUniform(m_billboardOutlineParamsUniformHandle, outlineParams);
                bgfx::setUniform(m_billboardFogColorUniformHandle, fogColor);
                bgfx::setUniform(m_billboardFogDensitiesUniformHandle, fogDensities);
                bgfx::setUniform(m_billboardFogDistancesUniformHandle, fogDistances);
                bgfx::setState(
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_DEPTH_TEST_LEQUAL
                    | BGFX_STATE_BLEND_ALPHA);
                bgfx::submit(viewId, m_billboardProgramHandle);
            }
        }

        const uint32_t vertexColorAbgr = makeAbgr(0, 0, 0);
        const std::array<float, 4> ambient = billboardLightingUniform(lightingFrame, frame, center);
        const float clearOverrideColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float clearOutlineParams[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogDensities[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogDistances[4] = {4096.0f, 4096.0f, 4096.0f, 0.0f};
        std::array<LitBillboardVertex, 6> vertices = {{
            {
                center.x - right.x - up.x,
                center.y - right.y - up.y,
                center.z - right.z - up.z,
                u0,
                1.0f,
                vertexColorAbgr
            },
            {
                center.x - right.x + up.x,
                center.y - right.y + up.y,
                center.z - right.z + up.z,
                u0,
                0.0f,
                vertexColorAbgr
            },
            {
                center.x + right.x + up.x,
                center.y + right.y + up.y,
                center.z + right.z + up.z,
                u1,
                0.0f,
                vertexColorAbgr
            },
            {
                center.x - right.x - up.x,
                center.y - right.y - up.y,
                center.z - right.z - up.z,
                u0,
                1.0f,
                vertexColorAbgr
            },
            {
                center.x + right.x + up.x,
                center.y + right.y + up.y,
                center.z + right.z + up.z,
                u1,
                0.0f,
                vertexColorAbgr
            },
            {
                center.x + right.x - up.x,
                center.y + right.y - up.y,
                center.z + right.z - up.z,
                u1,
                1.0f,
                vertexColorAbgr
            }
        }};

        if (bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), LitBillboardVertex::ms_layout)
            < vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            LitBillboardVertex::ms_layout
        );
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(LitBillboardVertex))
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
        bgfx::setUniform(m_billboardAmbientUniformHandle, ambient.data());
        bgfx::setUniform(m_billboardOverrideColorUniformHandle, clearOverrideColor);
        bgfx::setUniform(m_billboardOutlineParamsUniformHandle, clearOutlineParams);
        bgfx::setUniform(m_billboardFogColorUniformHandle, fogColor);
        bgfx::setUniform(m_billboardFogDensitiesUniformHandle, fogDensities);
        bgfx::setUniform(m_billboardFogDistancesUniformHandle, fogDistances);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA
        );
        bgfx::submit(viewId, m_billboardProgramHandle);
    }
}

const bgfx::TextureHandle *IndoorRenderer::findIndoorTextureHandle(const std::string &textureName) const
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

uint64_t IndoorRenderer::currentTexturedBatchVisualRevision() const
{
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return 0;
    }

    return pEventRuntimeState->outdoorSurfaceRevision;
}

bool IndoorRenderer::texturedBatchesNeedFullRebuild() const
{
    return m_texturedBatches.empty() || m_texturedBatchVisualRevision != currentTexturedBatchVisualRevision();
}

void IndoorRenderer::rebuildMechanismBindings()
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

std::vector<size_t> IndoorRenderer::collectMovingMechanismFaceIndices() const
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

bool IndoorRenderer::rebuildAllTexturedBatches(uint64_t &texturedBuildNanoseconds)
{
    if (!m_indoorTextureSet || !m_indoorMapData)
    {
        m_texturedBatches.clear();
        m_faceBatchIndices.clear();
        m_faceVertexOffsets.clear();
        m_faceVertexCounts.clear();
        m_texturedBatchVisualRevision = currentTexturedBatchVisualRevision();
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

    m_texturedBatchVisualRevision = currentTexturedBatchVisualRevision();
    return true;
}

bool IndoorRenderer::updateMovingMechanismFaceVertices(
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
                << "IndoorRenderer: moving mechanism face rebuild changed vertex count"
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

std::vector<IndoorVertex> IndoorRenderer::buildMechanismAdjustedVertices(
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

void IndoorRenderer::destroyDerivedGeometryResources()
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

void IndoorRenderer::destroyIndoorTextureHandles()
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

bool IndoorRenderer::rebuildDerivedGeometryResources()
{
    if (!m_indoorMapData)
    {
        std::cerr << "IndoorRenderer: rebuildDerivedGeometryResources has no indoor map data\n";
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
        std::cerr << "IndoorRenderer: failed to update wireframe vertex buffer\n";
        return false;
    }
    m_wireframeVertexCount = static_cast<uint32_t>(wireframeVertices.size());

    if (!updateDynamicVertexBuffer(
            m_portalVertexBufferHandle,
            m_portalVertexCapacity,
            portalVertices,
            TerrainVertex::ms_layout))
    {
        std::cerr << "IndoorRenderer: failed to update portal vertex buffer\n";
        return false;
    }
    m_portalVertexCount = static_cast<uint32_t>(portalVertices.size());

    if (!updateDynamicVertexBuffer(
            m_doorMarkerVertexBufferHandle,
            m_doorMarkerVertexCapacity,
            doorMarkerVertices,
            TerrainVertex::ms_layout))
    {
        std::cerr << "IndoorRenderer: failed to update door marker vertex buffer\n";
        return false;
    }
    m_doorMarkerVertexCount = static_cast<uint32_t>(doorMarkerVertices.size());

    if (m_indoorTextureSet)
    {
        if (texturedBatchesNeedFullRebuild())
        {
            uint64_t texturedBuildNanoseconds = 0;
            if (!rebuildAllTexturedBatches(texturedBuildNanoseconds))
            {
                std::cerr << "IndoorRenderer: rebuildAllTexturedBatches failed\n";
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
                    << "IndoorRenderer: updateMovingMechanismFaceVertices failed, rebuilding textured batches\n";

                texturedBuildNanoseconds = 0;

                if (!rebuildAllTexturedBatches(texturedBuildNanoseconds))
                {
                    std::cerr << "IndoorRenderer: rebuildAllTexturedBatches failed after moving update failure\n";
                    return false;
                }
            }
        }
    }

    ++m_inspectGeometryRevision;
    m_cachedInspectHitValid = false;
    return true;
}

bool IndoorRenderer::updateMovingMechanismGeometryResources()
{
    if (!m_indoorMapData)
    {
        return false;
    }

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();
    m_renderVertices = buildMechanismAdjustedVertices(*m_indoorMapData, mapDeltaData, eventRuntimeState);

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        ++m_inspectGeometryRevision;
        m_cachedInspectHitValid = false;
        return true;
    }

    if (!m_indoorTextureSet || texturedBatchesNeedFullRebuild())
    {
        return rebuildDerivedGeometryResources();
    }

    uint64_t texturedBuildNanoseconds = 0;
    uint64_t uploadNanoseconds = 0;

    if (!updateMovingMechanismFaceVertices(texturedBuildNanoseconds, uploadNanoseconds))
    {
        return rebuildDerivedGeometryResources();
    }

    ++m_inspectGeometryRevision;
    m_cachedInspectHitValid = false;
    return true;
}

bool IndoorRenderer::tryActivateInspectEvent(const InspectHit &inspectHit)
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

std::vector<IndoorRenderer::TexturedVertex> IndoorRenderer::buildTexturedVertices(
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

std::vector<IndoorRenderer::TexturedVertex> IndoorRenderer::buildFaceTexturedVertices(
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

std::vector<IndoorRenderer::TerrainVertex> IndoorRenderer::buildEntityMarkerVertices(
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

std::vector<IndoorRenderer::TerrainVertex> IndoorRenderer::buildSpawnMarkerVertices(
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
        const float centerZ =
            static_cast<float>(snapIndoorSpawnZToFloor(indoorMapData, spawn.x, spawn.y, spawn.z)) + halfExtent;

        vertices.push_back({centerX - halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX + halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX, centerY - halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY + halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY, centerZ - halfExtent, color});
        vertices.push_back({centerX, centerY, centerZ + halfExtent, color});
    }

    return vertices;
}

std::vector<IndoorRenderer::TerrainVertex> IndoorRenderer::buildDoorMarkerVertices(
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

IndoorRenderer::InspectHit IndoorRenderer::inspectAtCursor(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const std::vector<uint8_t> &visibleSectorMask,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const GameplayWorldPickRequest *pPickRequest) const
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

        if (face.isPortal || hasFaceAttribute(face.attributes, FaceAttribute::IsPortal))
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

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

    if (mapDeltaData && m_monsterTable && m_indoorActorPreviewBillboardSet)
    {
        const float cosPitch = std::cos(m_cameraPitchRadians);
        const float sinPitch = std::sin(m_cameraPitchRadians);
        const float cosYaw = std::cos(m_cameraYawRadians);
        const float sinYaw = std::sin(m_cameraYawRadians);
        const bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
        const bx::Vec3 at = {
            m_cameraPositionX + cosYaw * cosPitch,
            m_cameraPositionY + sinYaw * cosPitch,
            m_cameraPositionZ + sinPitch
        };
        const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
        float viewMatrix[16] = {};
        bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
        const bx::Vec3 cameraRight = {viewMatrix[0], viewMatrix[4], viewMatrix[8]};
        const bx::Vec3 cameraUp = {viewMatrix[1], viewMatrix[5], viewMatrix[9]};
        const auto isOpaqueBillboardPixel =
            [](const BillboardTextureHandle &texture, float normalizedU, float normalizedV) -> bool
            {
                if (texture.physicalWidth <= 0
                    || texture.physicalHeight <= 0
                    || texture.pixels.empty())
                {
                    return true;
                }

                const int pixelX = std::clamp(
                    static_cast<int>(std::floor(normalizedU * float(texture.physicalWidth))),
                    0,
                    texture.physicalWidth - 1);
                const int pixelY = std::clamp(
                    static_cast<int>(std::floor(normalizedV * float(texture.physicalHeight))),
                    0,
                    texture.physicalHeight - 1);
                const size_t pixelOffset = static_cast<size_t>((pixelY * texture.physicalWidth + pixelX) * 4);
                return pixelOffset + 3 < texture.pixels.size() && texture.pixels[pixelOffset + 3] != 0;
            };

        const auto hitTestActorBillboard =
            [&](const RuntimeActorBillboard &actor, float &distance, bool &billboardTested) -> bool
            {
                billboardTested = false;
                const IndoorWorldRuntime::MapActorAiState *pActorAiState =
                    m_pSceneRuntime != nullptr
                        ? m_pSceneRuntime->worldRuntime().mapActorAiState(actor.actorIndex)
                        : nullptr;
                uint16_t spriteFrameIndex = actor.spriteFrameIndex;
                uint32_t frameTimeTicks = actor.useStaticFrame ? 0U : currentAnimationTicks();

                if (pActorAiState != nullptr)
                {
                    const size_t animationIndex = static_cast<size_t>(pActorAiState->animationState);

                    if (animationIndex < actor.actionSpriteFrameIndices.size()
                        && actor.actionSpriteFrameIndices[animationIndex] != 0)
                    {
                        spriteFrameIndex = actor.actionSpriteFrameIndices[animationIndex];
                    }

                    frameTimeTicks = static_cast<uint32_t>(std::max(0.0f, pActorAiState->animationTimeTicks));
                }

                const SpriteFrameEntry *pFrame =
                    m_indoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, frameTimeTicks);

                if (pFrame == nullptr)
                {
                    return false;
                }

                const float angleToCamera = std::atan2(
                    static_cast<float>(actor.y) - m_cameraPositionY,
                    static_cast<float>(actor.x) - m_cameraPositionX);
                const float actorYawRadians = pActorAiState != nullptr ? pActorAiState->yawRadians : 0.0f;
                const float octantAngle = actorYawRadians - angleToCamera + Pi + (Pi / 8.0f);
                const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
                const BillboardTextureHandle *pTexture =
                    findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

                if (pTexture == nullptr || pTexture->width <= 0 || pTexture->height <= 0)
                {
                    return false;
                }

                billboardTested = true;
                const float spriteScale = std::max(pFrame->scale, 0.01f);
                const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                const bx::Vec3 center = bottomAnchoredBillboardCenter(
                    static_cast<float>(actor.x),
                    static_cast<float>(actor.y),
                    static_cast<float>(actor.z),
                    cameraUp,
                    worldHeight);
                const bx::Vec3 planeNormal = {
                    -cameraRight.y * cameraUp.z + cameraRight.z * cameraUp.y,
                    -cameraRight.z * cameraUp.x + cameraRight.x * cameraUp.z,
                    -cameraRight.x * cameraUp.y + cameraRight.y * cameraUp.x
                };
                const float denominator = vecDot(rayDirection, planeNormal);

                if (std::fabs(denominator) <= InspectRayEpsilon)
                {
                    return false;
                }

                distance = vecDot(vecSubtract(center, rayOrigin), planeNormal) / denominator;

                if (distance <= InspectRayEpsilon)
                {
                    return false;
                }

                const bx::Vec3 hitPoint = {
                    rayOrigin.x + rayDirection.x * distance,
                    rayOrigin.y + rayDirection.y * distance,
                    rayOrigin.z + rayDirection.z * distance
                };
                const bx::Vec3 localDelta = vecSubtract(hitPoint, center);
                const float localX = vecDot(localDelta, cameraRight);
                const float localY = vecDot(localDelta, cameraUp);
                const float halfWidth = worldWidth * 0.5f;
                const float halfHeight = worldHeight * 0.5f;

                if (std::fabs(localX) > halfWidth || std::fabs(localY) > halfHeight)
                {
                    return false;
                }

                float normalizedU = (localX + halfWidth) / worldWidth;
                const float normalizedV = (halfHeight - localY) / worldHeight;

                if (resolvedTexture.mirrored)
                {
                    normalizedU = 1.0f - normalizedU;
                }

                return isOpaqueBillboardPixel(*pTexture, normalizedU, normalizedV);
            };

        const std::vector<RuntimeActorBillboard> runtimeActors =
            buildRuntimeActorBillboards(
                *m_monsterTable,
                m_indoorActorPreviewBillboardSet->spriteFrameTable,
                *mapDeltaData,
                m_pSceneRuntime != nullptr ? &m_pSceneRuntime->worldRuntime() : nullptr);

        for (const RuntimeActorBillboard &actor : runtimeActors)
        {
            if (!isSectorVisible(actor.sectorId, visibleSectorMask))
            {
                continue;
            }

            float distance = 0.0f;
            bool billboardTested = false;
            const bool usedBillboardHit = hitTestActorBillboard(actor, distance, billboardTested);

            if (usedBillboardHit && distance < bestDistance)
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
                continue;
            }

            if (billboardTested)
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
            buildRuntimeSpriteObjectBillboards(*m_objectTable, m_pItemTable, *mapDeltaData);
        const SpriteFrameTable *pSpriteFrameTable = nullptr;

        if (m_indoorSpriteObjectBillboardSet)
        {
            pSpriteFrameTable = &m_indoorSpriteObjectBillboardSet->spriteFrameTable;
        }
        else if (m_indoorActorPreviewBillboardSet)
        {
            pSpriteFrameTable = &m_indoorActorPreviewBillboardSet->spriteFrameTable;
        }
        else if (m_indoorDecorationBillboardSet)
        {
            pSpriteFrameTable = &m_indoorDecorationBillboardSet->spriteFrameTable;
        }

        const float cosPitch = std::cos(m_cameraPitchRadians);
        const float sinPitch = std::sin(m_cameraPitchRadians);
        const float cosYaw = std::cos(m_cameraYawRadians);
        const float sinYaw = std::sin(m_cameraYawRadians);
        const bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
        const bx::Vec3 at = {
            m_cameraPositionX + cosYaw * cosPitch,
            m_cameraPositionY + sinYaw * cosPitch,
            m_cameraPositionZ + sinPitch
        };
        const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
        float viewMatrix[16] = {};
        bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
        const bx::Vec3 cameraRight = {viewMatrix[0], viewMatrix[4], viewMatrix[8]};
        const bx::Vec3 cameraUp = {viewMatrix[1], viewMatrix[5], viewMatrix[9]};
        float pickViewProjectionMatrix[16] = {};
        const bool hasScreenPickRequest =
            pPickRequest != nullptr
            && pPickRequest->viewWidth > 0
            && pPickRequest->viewHeight > 0;

        if (hasScreenPickRequest)
        {
            bx::mtxMul(
                pickViewProjectionMatrix,
                pPickRequest->viewMatrix.data(),
                pPickRequest->projectionMatrix.data());
        }
        float inversePickViewProjectionMatrix[16] = {};

        if (hasScreenPickRequest)
        {
            bx::mtxInverse(inversePickViewProjectionMatrix, pickViewProjectionMatrix);
        }

        const auto isOpaqueBillboardPixel =
            [](const BillboardTextureHandle &texture, float normalizedU, float normalizedV) -> bool
            {
                if (texture.physicalWidth <= 0
                    || texture.physicalHeight <= 0
                    || texture.pixels.empty())
                {
                    return true;
                }

                const int pixelX = std::clamp(
                    static_cast<int>(std::floor(normalizedU * static_cast<float>(texture.physicalWidth))),
                    0,
                    texture.physicalWidth - 1);
                const int pixelY = std::clamp(
                    static_cast<int>(std::floor(normalizedV * static_cast<float>(texture.physicalHeight))),
                    0,
                    texture.physicalHeight - 1);
                const size_t pixelOffset = static_cast<size_t>((pixelY * texture.physicalWidth + pixelX) * 4);
                return pixelOffset + 3 < texture.pixels.size() && texture.pixels[pixelOffset + 3] != 0;
            };

        const auto nearestFaceDistanceForRay =
            [&](const bx::Vec3 &sampleRayOrigin, const bx::Vec3 &sampleRayDirection) -> std::optional<float>
            {
                std::optional<float> nearestDistance;

                for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
                {
                    const IndoorFace &face = indoorMapData.faces[faceIndex];

                    if (face.vertexIndices.size() < 3)
                    {
                        continue;
                    }

                    if (face.isPortal || hasFaceAttribute(face.attributes, FaceAttribute::IsPortal))
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

                        float faceDistance = 0.0f;

                        if (intersectRayTriangle(
                                sampleRayOrigin,
                                sampleRayDirection,
                                triangleVertices[0],
                                triangleVertices[1],
                                triangleVertices[2],
                                faceDistance)
                            && faceDistance > InspectRayEpsilon
                            && (!nearestDistance || faceDistance < *nearestDistance))
                        {
                            nearestDistance = faceDistance;
                        }
                    }
                }

                return nearestDistance;
            };

        const auto doesLevelMissBillboardSample =
            [&](float screenX, float screenY, const bx::Vec3 &center, const bx::Vec3 &planeNormal) -> bool
            {
                if (!hasScreenPickRequest || pPickRequest == nullptr)
                {
                    return true;
                }

                const float normalizedX = ((screenX / static_cast<float>(pPickRequest->viewWidth)) * 2.0f) - 1.0f;
                const float normalizedY = 1.0f - ((screenY / static_cast<float>(pPickRequest->viewHeight)) * 2.0f);
                const bx::Vec3 sampleRayOrigin =
                    bx::mulH({normalizedX, normalizedY, 0.0f}, inversePickViewProjectionMatrix);
                const bx::Vec3 sampleRayTarget =
                    bx::mulH({normalizedX, normalizedY, 1.0f}, inversePickViewProjectionMatrix);
                const bx::Vec3 sampleRayDirection = vecNormalize(vecSubtract(sampleRayTarget, sampleRayOrigin));

                if (vecLength(sampleRayDirection) <= InspectRayEpsilon)
                {
                    return false;
                }

                const float denominator = vecDot(sampleRayDirection, planeNormal);

                if (std::fabs(denominator) <= InspectRayEpsilon)
                {
                    return false;
                }

                const float billboardDistance =
                    vecDot(vecSubtract(center, sampleRayOrigin), planeNormal) / denominator;

                if (billboardDistance <= InspectRayEpsilon)
                {
                    return false;
                }

                const std::optional<float> nearestFaceDistance =
                    nearestFaceDistanceForRay(sampleRayOrigin, sampleRayDirection);

                return !nearestFaceDistance || *nearestFaceDistance > billboardDistance + 1.0f;
            };

        const auto applyObjectHit =
            [&](const RuntimeSpriteObjectBillboard &object, float distance)
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
                bestHit.hasContainingItem = object.hasContainingItem;
            };

        const auto hitTestSpriteObjectBillboard =
            [&](
                const RuntimeSpriteObjectBillboard &object,
                float &distance,
                bool &billboardTested) -> bool
            {
                billboardTested = false;

                if (pSpriteFrameTable == nullptr)
                {
                    return false;
                }

                const SpriteFrameEntry *pFrame =
                    pSpriteFrameTable->getFrame(object.objectSpriteId, object.timeSinceCreatedTicks);

                if (pFrame == nullptr)
                {
                    return false;
                }

                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
                const BillboardTextureHandle *pTexture =
                    findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

                if (pTexture == nullptr || pTexture->width <= 0 || pTexture->height <= 0)
                {
                    return false;
                }

                billboardTested = true;
                const float spriteScale = std::max(pFrame->scale, 0.01f);
                const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                const bx::Vec3 center = {
                    static_cast<float>(object.x),
                    static_cast<float>(object.y),
                    static_cast<float>(object.z) + worldHeight * 0.5f
                };
                const bx::Vec3 planeNormal = {
                    -cameraRight.y * cameraUp.z + cameraRight.z * cameraUp.y,
                    -cameraRight.z * cameraUp.x + cameraRight.x * cameraUp.z,
                    -cameraRight.x * cameraUp.y + cameraRight.y * cameraUp.x
                };
                const float denominator = vecDot(rayDirection, planeNormal);

                if (std::fabs(denominator) <= InspectRayEpsilon)
                {
                    return false;
                }

                distance = vecDot(vecSubtract(center, rayOrigin), planeNormal) / denominator;

                if (distance <= InspectRayEpsilon)
                {
                    return false;
                }

                if (hasScreenPickRequest)
                {
                    const float halfWidth = worldWidth * 0.5f;
                    const float halfHeight = worldHeight * 0.5f;
                    const bx::Vec3 right = {
                        cameraRight.x * halfWidth,
                        cameraRight.y * halfWidth,
                        cameraRight.z * halfWidth
                    };
                    const bx::Vec3 upVector = {
                        cameraUp.x * halfHeight,
                        cameraUp.y * halfHeight,
                        cameraUp.z * halfHeight
                    };
                    const bx::Vec3 corners[4] = {
                        {
                            center.x - right.x - upVector.x,
                            center.y - right.y - upVector.y,
                            center.z - right.z - upVector.z
                        },
                        {
                            center.x + right.x - upVector.x,
                            center.y + right.y - upVector.y,
                            center.z + right.z - upVector.z
                        },
                        {
                            center.x + right.x + upVector.x,
                            center.y + right.y + upVector.y,
                            center.z + right.z + upVector.z
                        },
                        {
                            center.x - right.x + upVector.x,
                            center.y - right.y + upVector.y,
                            center.z - right.z + upVector.z
                        }
                    };
                    ProjectedPoint projected = {};
                    float minX = std::numeric_limits<float>::max();
                    float minY = std::numeric_limits<float>::max();
                    float maxX = -std::numeric_limits<float>::max();
                    float maxY = -std::numeric_limits<float>::max();
                    bool allCornersProjected = true;

                    for (const bx::Vec3 &corner : corners)
                    {
                        if (!projectWorldPointToScreen(
                                corner,
                                pPickRequest->viewWidth,
                                pPickRequest->viewHeight,
                                pickViewProjectionMatrix,
                                projected))
                        {
                            allCornersProjected = false;
                            break;
                        }

                        minX = std::min(minX, projected.x);
                        minY = std::min(minY, projected.y);
                        maxX = std::max(maxX, projected.x);
                        maxY = std::max(maxY, projected.y);
                    }

                    if (allCornersProjected)
                    {
                        const float visibleMinX = std::clamp(minX, 0.0f, static_cast<float>(pPickRequest->viewWidth - 1));
                        const float visibleMinY = std::clamp(minY, 0.0f, static_cast<float>(pPickRequest->viewHeight - 1));
                        const float visibleMaxX = std::clamp(maxX, 0.0f, static_cast<float>(pPickRequest->viewWidth - 1));
                        const float visibleMaxY = std::clamp(maxY, 0.0f, static_cast<float>(pPickRequest->viewHeight - 1));
                        const float paddedMinX = minX - 1.5f;
                        const float paddedMinY = minY - 1.5f;
                        const float paddedMaxX = maxX + 1.5f;
                        const float paddedMaxY = maxY + 1.5f;

                        if (pPickRequest->screenX < paddedMinX
                            || pPickRequest->screenX > paddedMaxX
                            || pPickRequest->screenY < paddedMinY
                            || pPickRequest->screenY > paddedMaxY)
                        {
                            return false;
                        }

                        const float screenWidth = maxX - minX;
                        const float screenHeight = maxY - minY;

                        if (std::fabs(screenWidth) < 5.0f || std::fabs(screenHeight) < 5.0f)
                        {
                            return true;
                        }

                        float normalizedU = (pPickRequest->screenX - minX) / screenWidth;
                        const float normalizedV = (pPickRequest->screenY - minY) / screenHeight;

                        if (resolvedTexture.mirrored)
                        {
                            normalizedU = 1.0f - normalizedU;
                        }

                        const bool isOpaque = isOpaqueBillboardPixel(*pTexture, normalizedU, normalizedV);

                        if (!isOpaque)
                        {
                            return false;
                        }

                        if (object.hasContainingItem)
                        {
                            return true;
                        }

                        const bool cursorMissesLevel = doesLevelMissBillboardSample(
                            pPickRequest->screenX,
                            pPickRequest->screenY,
                            center,
                            planeNormal);
                        const bool centerMissesLevel = doesLevelMissBillboardSample(
                            (visibleMinX + visibleMaxX) * 0.5f,
                            (visibleMinY + visibleMaxY) * 0.5f,
                            center,
                            planeNormal);
                        const bool topLeftMissesLevel =
                            doesLevelMissBillboardSample(visibleMinX, visibleMinY, center, planeNormal);
                        const bool bottomLeftMissesLevel =
                            doesLevelMissBillboardSample(visibleMinX, visibleMaxY, center, planeNormal);
                        const bool topRightMissesLevel =
                            doesLevelMissBillboardSample(visibleMaxX, visibleMinY, center, planeNormal);
                        const bool bottomRightMissesLevel =
                            doesLevelMissBillboardSample(visibleMaxX, visibleMaxY, center, planeNormal);
                        const bool bottomCenterMissesLevel =
                            doesLevelMissBillboardSample(
                                (visibleMinX + visibleMaxX) * 0.5f,
                                visibleMaxY,
                                center,
                                planeNormal);

                        if (!cursorMissesLevel
                            && !centerMissesLevel
                            && !topLeftMissesLevel
                            && !bottomLeftMissesLevel
                            && !topRightMissesLevel
                            && !bottomRightMissesLevel
                            && !bottomCenterMissesLevel)
                        {
                            return false;
                        }

                        return true;
                    }
                }

                const bx::Vec3 hitPoint = {
                    rayOrigin.x + rayDirection.x * distance,
                    rayOrigin.y + rayDirection.y * distance,
                    rayOrigin.z + rayDirection.z * distance
                };
                const bx::Vec3 localDelta = vecSubtract(hitPoint, center);
                const float localX = vecDot(localDelta, cameraRight);
                const float localY = vecDot(localDelta, cameraUp);
                const float halfWidth = worldWidth * 0.5f;
                const float halfHeight = worldHeight * 0.5f;

                if (std::fabs(localX) > halfWidth || std::fabs(localY) > halfHeight)
                {
                    return false;
                }

                float normalizedU = (localX + halfWidth) / worldWidth;
                const float normalizedV = (halfHeight - localY) / worldHeight;

                if (resolvedTexture.mirrored)
                {
                    normalizedU = 1.0f - normalizedU;
                }

                return isOpaqueBillboardPixel(*pTexture, normalizedU, normalizedV);
            };

        for (const RuntimeSpriteObjectBillboard &object : runtimeObjects)
        {
            if (!isSectorVisible(object.sectorId, visibleSectorMask))
            {
                continue;
            }

            float distance = 0.0f;
            bool billboardTested = false;
            const bool usedBillboardHit = hitTestSpriteObjectBillboard(object, distance, billboardTested);

            if (usedBillboardHit
                && (distance < bestDistance || (object.hasContainingItem && bestHit.kind == "face")))
            {
                applyObjectHit(object, distance);
                continue;
            }

            if (object.hasContainingItem)
            {
                continue;
            }

            if (billboardTested)
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

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance) && distance < bestDistance)
            {
                applyObjectHit(object, distance);
            }
        }
    }

    const bool objectLoopSelectedWorldItem = bestHit.kind == "object" && bestHit.hasContainingItem;

    if (mapDeltaData && !objectLoopSelectedWorldItem)
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

std::vector<IndoorRenderer::TerrainVertex> IndoorRenderer::buildWireframeVertices(
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

std::vector<IndoorRenderer::TerrainVertex> IndoorRenderer::buildPortalVertices(
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

void IndoorRenderer::updateWorldMovement(
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput)
{
    updateCameraFromInput(input, deltaSeconds, allowWorldInput);

    if (!allowWorldInput || input.mouseWheelDelta == 0.0f)
    {
        return;
    }

    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    const bx::Vec3 forward = {cosYaw * cosPitch, sinYaw * cosPitch, sinPitch};
    const float wheelMoveSpeed = 300.0f;
    m_cameraPositionX += forward.x * input.mouseWheelDelta * wheelMoveSpeed;
    m_cameraPositionY += forward.y * input.mouseWheelDelta * wheelMoveSpeed;
    m_cameraPositionZ += forward.z * input.mouseWheelDelta * wheelMoveSpeed;
}

void IndoorRenderer::updateCameraFromInput(
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput)
{
    const float displayDeltaSeconds = std::max(deltaSeconds, 0.000001f);
    const float instantaneousFramesPerSecond = 1.0f / displayDeltaSeconds;
    m_framesPerSecond = (m_framesPerSecond == 0.0f)
        ? instantaneousFramesPerSecond
        : (m_framesPerSecond * 0.9f + instantaneousFramesPerSecond * 0.1f);
    deltaSeconds = std::min(deltaSeconds, 0.05f);

    const bool *pKeyboardState = input.keyboardState();

    const float moveSpeed = 320.0f;
    const float fastMoveMultiplier = 4.0f;
    const float mouseRotateSpeed = 0.0045f;
    const float mouseX = input.pointerX;
    const float mouseY = input.pointerY;
    const bool shouldRotateCamera = allowWorldInput && m_gameplayMouseLookEnabled && !m_gameplayCursorMode;

    if (shouldRotateCamera)
    {
        if (m_gameplayMouseLookEnabled)
        {
            const float relativeMouseX = input.relativeMouseX;
            const float relativeMouseY = input.relativeMouseY;

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
    const bx::Vec3 forward = {cosYaw * cosPitch, sinYaw * cosPitch, sinPitch};
    const bx::Vec3 right = {sinYaw, -cosYaw, 0.0f};
    const bool isFastMovePressed =
        pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    const bool jumpPressed = pKeyboardState[SDL_SCANCODE_X];
    const bool jumpRequested = allowWorldInput && jumpPressed && !m_jumpHeld;
    m_jumpHeld = jumpPressed;
    const float currentMoveSpeed = isFastMovePressed ? moveSpeed * fastMoveMultiplier : moveSpeed;
    float desiredVelocityX = 0.0f;
    float desiredVelocityY = 0.0f;

    if (allowWorldInput && pKeyboardState[SDL_SCANCODE_W])
    {
        desiredVelocityX += cosYaw * currentMoveSpeed;
        desiredVelocityY += sinYaw * currentMoveSpeed;
    }

    if (allowWorldInput && pKeyboardState[SDL_SCANCODE_S])
    {
        desiredVelocityX -= cosYaw * currentMoveSpeed;
        desiredVelocityY -= sinYaw * currentMoveSpeed;
    }

    if (allowWorldInput && pKeyboardState[SDL_SCANCODE_A])
    {
        desiredVelocityX -= right.x * currentMoveSpeed;
        desiredVelocityY -= right.y * currentMoveSpeed;
    }

    if (allowWorldInput && pKeyboardState[SDL_SCANCODE_D])
    {
        desiredVelocityX += right.x * currentMoveSpeed;
        desiredVelocityY += right.y * currentMoveSpeed;
    }

    if (m_pSceneRuntime != nullptr)
    {
        IndoorPartyRuntime &partyRuntime = m_pSceneRuntime->partyRuntime();
        const IndoorWorldRuntime &worldRuntime = m_pSceneRuntime->worldRuntime();
        partyRuntime.setActorColliders(worldRuntime.actorMovementCollidersForPartyMovement());
        partyRuntime.setDecorationColliders(worldRuntime.decorationMovementColliders());
        partyRuntime.setSpriteObjectColliders(worldRuntime.spriteObjectMovementColliders());
        partyRuntime.update(desiredVelocityX, desiredVelocityY, jumpRequested, deltaSeconds);
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        m_cameraPositionX = moveState.x;
        m_cameraPositionY = moveState.y;
        m_cameraPositionZ = moveState.eyeZ();
    }
    else
    {
        if (allowWorldInput && pKeyboardState[SDL_SCANCODE_W])
        {
            m_cameraPositionX += forward.x * currentMoveSpeed * deltaSeconds;
            m_cameraPositionY += forward.y * currentMoveSpeed * deltaSeconds;
            m_cameraPositionZ += forward.z * currentMoveSpeed * deltaSeconds;
        }

        if (allowWorldInput && pKeyboardState[SDL_SCANCODE_S])
        {
            m_cameraPositionX -= forward.x * currentMoveSpeed * deltaSeconds;
            m_cameraPositionY -= forward.y * currentMoveSpeed * deltaSeconds;
            m_cameraPositionZ -= forward.z * currentMoveSpeed * deltaSeconds;
        }

        if (allowWorldInput && pKeyboardState[SDL_SCANCODE_A])
        {
            m_cameraPositionX -= right.x * currentMoveSpeed * deltaSeconds;
            m_cameraPositionY -= right.y * currentMoveSpeed * deltaSeconds;
        }

        if (allowWorldInput && pKeyboardState[SDL_SCANCODE_D])
        {
            m_cameraPositionX += right.x * currentMoveSpeed * deltaSeconds;
            m_cameraPositionY += right.y * currentMoveSpeed * deltaSeconds;
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
}
}
