#include "game/indoor/IndoorRenderer.h"

#include "engine/BgfxContext.h"
#include "game/arpg/ArpgModeCamera.h"
#include "game/app/GameSession.h"
#include "game/app/GameSettings.h"
#include "game/data/ActorNameResolver.h"
#include "game/events/EventRuntime.h"
#include "game/FaceEnums.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ParticleRenderer.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorPortalGraph.h"
#include "game/indoor/IndoorPortalVisibility.h"
#include "game/party/Party.h"
#include "game/render/TextureFiltering.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/SpriteObjectDefs.h"
#include "game/StringUtils.h"
#include "engine/ImageAssetLoader.h"

#include <bx/math.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <iterator>
#include <limits>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float IndoorCameraVerticalFovDegrees = 60.0f;
constexpr float IndoorSkyProjectionPitchOffsetRadians = 3.14159265358979323846f / 64.0f;
constexpr float IndoorSkyProjectionFarClipDistance = 50000.0f;
constexpr uint32_t IndoorLightSelectionCacheMaxAgeFrames = 180;
constexpr uint64_t IndoorBillboardDrawState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_WRITE_Z
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA;

uint32_t fnv1a32Update(uint32_t hash, const std::string &text)
{
    for (char character : text)
    {
        hash ^= static_cast<uint8_t>(character);
        hash *= 16777619u;
    }

    return hash;
}

uint32_t stableIndoorTexturedBatchId(
    const std::string &textureName,
    int16_t sectorId,
    int16_t backSectorId,
    size_t batchIndex)
{
    uint32_t hash = 2166136261u;
    hash = fnv1a32Update(hash, textureName);
    hash ^= static_cast<uint32_t>(static_cast<uint16_t>(sectorId)) + 0x9e3779b9u + (hash << 6) + (hash >> 2);
    hash ^= static_cast<uint32_t>(static_cast<uint16_t>(backSectorId)) + 0x85ebca6bu + (hash << 6) + (hash >> 2);
    hash ^= static_cast<uint32_t>(batchIndex) + 0xc2b2ae35u + (hash << 6) + (hash >> 2);
    return hash != 0 ? hash : 1u;
}

uint32_t indoorFaceEdgeKey(uint16_t vertexA, uint16_t vertexB)
{
    const uint16_t minVertex = std::min(vertexA, vertexB);
    const uint16_t maxVertex = std::max(vertexA, vertexB);
    return (static_cast<uint32_t>(minVertex) << 16) | static_cast<uint32_t>(maxVertex);
}

void appendUniqueIndex(std::vector<size_t> &indices, size_t index)
{
    if (std::find(indices.begin(), indices.end(), index) == indices.end())
    {
        indices.push_back(index);
    }
}

float secretFaceVertexFlag(uint32_t attributes)
{
    return hasFaceAttribute(attributes, FaceAttribute::IsSecret) ? 1.0f : 0.0f;
}

bool indoorFaceMarkedAsCeiling(const IndoorMapData &indoorMapData, size_t faceIndex, const IndoorFace &face)
{
    if (face.facetType == 5 || face.facetType == 6)
    {
        return true;
    }

    const auto sectorContainsCeilingFace =
        [&](uint16_t sectorId) -> bool
        {
            if (sectorId >= indoorMapData.sectors.size())
            {
                return false;
            }

            const std::vector<uint16_t> &ceilingFaceIds = indoorMapData.sectors[sectorId].ceilingFaceIds;
            return std::find(ceilingFaceIds.begin(), ceilingFaceIds.end(), faceIndex) != ceilingFaceIds.end();
        };

    return sectorContainsCeilingFace(face.roomNumber) || sectorContainsCeilingFace(face.roomBehindNumber);
}

bool indoorFaceMarkedAsFloor(const IndoorMapData &indoorMapData, size_t faceIndex, const IndoorFace &face)
{
    if (face.facetType == 3)
    {
        return true;
    }

    const auto sectorContainsFloorFace =
        [&](uint16_t sectorId) -> bool
        {
            if (sectorId >= indoorMapData.sectors.size())
            {
                return false;
            }

            const std::vector<uint16_t> &floorFaceIds = indoorMapData.sectors[sectorId].floorFaceIds;
            return std::find(floorFaceIds.begin(), floorFaceIds.end(), faceIndex) != floorFaceIds.end();
        };

    return sectorContainsFloorFace(face.roomNumber) || sectorContainsFloorFace(face.roomBehindNumber);
}

std::vector<uint8_t> buildIndoorCeilingFaceMask(const IndoorMapData &indoorMapData)
{
    std::vector<uint8_t> mask(indoorMapData.faces.size(), 0);

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = indoorMapData.faces[faceIndex];

        if (face.facetType == 5 || face.facetType == 6)
        {
            mask[faceIndex] = 1;
        }
    }

    for (const IndoorSector &sector : indoorMapData.sectors)
    {
        for (uint16_t faceId : sector.ceilingFaceIds)
        {
            if (faceId < mask.size())
            {
                mask[faceId] = 1;
            }
        }
    }

    return mask;
}

bool indoorFaceTouchesSector(const IndoorFace &face, int16_t sectorId)
{
    return sectorId >= 0
        && (face.roomNumber == static_cast<uint16_t>(sectorId)
            || face.roomBehindNumber == static_cast<uint16_t>(sectorId));
}

bool indoorContextActionTargetsChest(
    const std::optional<GameplayEventTargetContextActionMetadata> &metadata,
    const std::vector<uint32_t> &openedChestIds)
{
    return !openedChestIds.empty() || (metadata && metadata->kind == "open_chest");
}

bool indoorFaceSuppressedForArpgContextAction(
    const IndoorMapData &indoorMapData,
    size_t faceIndex,
    const IndoorFace &face,
    const std::optional<GameplayEventTargetContextActionMetadata> &metadata,
    const std::vector<uint32_t> &openedChestIds)
{
    if (indoorContextActionTargetsChest(metadata, openedChestIds))
    {
        return false;
    }

    if (metadata && !metadata->hidden)
    {
        return false;
    }

    return face.facetType == 3 || indoorFaceMarkedAsCeiling(indoorMapData, faceIndex, face);
}

bool indoorFaceSuppressedForContextAction(
    const IndoorMapData &indoorMapData,
    size_t faceIndex,
    const IndoorFace &face,
    const std::optional<GameplayEventTargetContextActionMetadata> &metadata,
    const std::vector<uint32_t> &openedChestIds)
{
    return indoorFaceSuppressedForArpgContextAction(indoorMapData, faceIndex, face, metadata, openedChestIds);
}

uint16_t indoorDoorRuntimeState(const MapDeltaDoor &door, const EventRuntimeState *pEventRuntimeState)
{
    if (pEventRuntimeState != nullptr)
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
            pEventRuntimeState->mechanisms.find(door.doorId);

        if (mechanismIterator != pEventRuntimeState->mechanisms.end())
        {
            return mechanismIterator->second.state;
        }
    }

    return door.state;
}

bool indoorDoorMechanismSuppressesArpgContextAction(
    const MapDeltaDoor &door,
    const EventRuntimeState *pEventRuntimeState)
{
    const uint16_t state = indoorDoorRuntimeState(door, pEventRuntimeState);

    return state == static_cast<uint16_t>(EvtMechanismState::Open)
        || state == static_cast<uint16_t>(EvtMechanismState::Opening);
}

bool indoorDoorMechanismSuppressedForContextAction(
    const MapDeltaDoor &door,
    const EventRuntimeState *pEventRuntimeState)
{
    return indoorDoorMechanismSuppressesArpgContextAction(door, pEventRuntimeState);
}

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
constexpr size_t MaxIndoorShaderLights = MaxIndoorDrawLights;
constexpr float Pi = 3.14159265358979323846f;
constexpr float InspectRayEpsilon = 0.0001f;
constexpr float KeyboardEventFaceScreenRadius = 384.0f;
constexpr float HoveredActorOutlineThicknessPixels = 2.0f;
constexpr float BillboardFrustumSlack = 8.0f;
constexpr float ArpgModeCameraMinDistance = 800.0f;
constexpr float ArpgModeCameraMaxDistance = 6400.0f;
constexpr float ArpgModeCameraWheelStep = 220.0f;
constexpr int ArpgModeIndoorHigherSectorCullMargin = 64;
constexpr uint32_t ArpgModeIndoorRenderVisibilityRefreshMs = 100;

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
    float heightScale = 1.0f;
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

bool sectorVisibleForRuntimeBillboard(int16_t sectorId, const std::vector<uint8_t> *pVisibleSectorMask)
{
    return pVisibleSectorMask == nullptr
        || pVisibleSectorMask->empty()
        || (sectorId >= 0
            && static_cast<size_t>(sectorId) < pVisibleSectorMask->size()
            && (*pVisibleSectorMask)[static_cast<size_t>(sectorId)] != 0);
}

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

bx::Vec3 vecAdd(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

bx::Vec3 vecScale(const bx::Vec3 &value, float scale)
{
    return {value.x * scale, value.y * scale, value.z * scale};
}

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

uint64_t averageNanoseconds(uint64_t totalNanoseconds, uint64_t count)
{
    return count != 0 ? totalNanoseconds / count : 0;
}

uint64_t nanosecondsToMicroseconds(uint64_t nanoseconds)
{
    return nanoseconds / 1000ULL;
}

float resolveMechanismDistance(
    const MapDeltaDoor &baseDoor,
    const std::optional<EventRuntimeState> &eventRuntimeState
);

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

uint16_t firstRuntimeActorSpriteFrameIndex(const std::array<uint16_t, 8> &actionSpriteFrameIndices)
{
    for (uint16_t frameIndex : actionSpriteFrameIndices)
    {
        if (frameIndex != 0)
        {
            return frameIndex;
        }
    }

    return 0;
}

bool spriteFrameIndexHasDirectionalTextures(const SpriteFrameTable &spriteFrameTable, uint16_t spriteFrameIndex)
{
    const SpriteFrameEntry *pFrame = spriteFrameTable.getFrame(spriteFrameIndex, 0);
    return pFrame != nullptr && !SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::Image1);
}

bool monsterEntryHasDirectionalArpgActionSprites(
    const SpriteFrameTable &spriteFrameTable,
    const std::array<uint16_t, 8> &actionSpriteFrameIndices)
{
    const size_t meleeAttackIndex = static_cast<size_t>(ActorAiAnimationState::AttackMelee);
    const size_t rangedAttackIndex = static_cast<size_t>(ActorAiAnimationState::AttackRanged);

    if (meleeAttackIndex < actionSpriteFrameIndices.size()
        && spriteFrameIndexHasDirectionalTextures(spriteFrameTable, actionSpriteFrameIndices[meleeAttackIndex]))
    {
        return true;
    }

    return rangedAttackIndex < actionSpriteFrameIndices.size()
        && spriteFrameIndexHasDirectionalTextures(spriteFrameTable, actionSpriteFrameIndices[rangedAttackIndex]);
}

const MonsterEntry *findArpgModeMonsterEntryByName(const MonsterTable &monsterTable, const std::string &internalName)
{
    if (internalName.empty())
    {
        return nullptr;
    }

    if (internalName == "m270")
    {
        return monsterTable.findByInternalName("Lich A");
    }

    return monsterTable.findByInternalName(internalName);
}

const MonsterEntry *resolveArpgModePlayerMonsterEntry(
    const MonsterTable &monsterTable,
    const GameSettings &settings,
    const SpriteFrameTable &spriteFrameTable)
{
    const std::array<std::string, 4> candidates = {
        "m270",
        settings.arpgModePlayerMonsterDescriptor,
        "Lich A",
        "Lich C",
    };
    const MonsterEntry *pFirstValidEntry = nullptr;

    for (const std::string &candidate : candidates)
    {
        const MonsterEntry *pMonsterEntry = findArpgModeMonsterEntryByName(monsterTable, candidate);

        if (pMonsterEntry == nullptr)
        {
            continue;
        }

        const std::array<uint16_t, 8> actionSpriteFrameIndices =
            buildRuntimeActorActionSpriteFrameIndices(spriteFrameTable, pMonsterEntry);

        if (firstRuntimeActorSpriteFrameIndex(actionSpriteFrameIndices) != 0)
        {
            if (pFirstValidEntry == nullptr)
            {
                pFirstValidEntry = pMonsterEntry;
            }

            if (monsterEntryHasDirectionalArpgActionSprites(spriteFrameTable, actionSpriteFrameIndices))
            {
                return pMonsterEntry;
            }
        }
    }

    return pFirstValidEntry;
}

uint16_t selectArpgModePlayerSpriteFrameIndex(
    float actionAnimationSeconds,
    bool actionAnimationIsCast,
    bool walkingAnimationActive,
    const std::array<uint16_t, 8> &actionSpriteFrameIndices)
{
    ActorAiAnimationState animation = ActorAiAnimationState::Standing;

    if (actionAnimationSeconds > 0.0f)
    {
        animation = actionAnimationIsCast ? ActorAiAnimationState::AttackRanged : ActorAiAnimationState::AttackMelee;
    }
    else if (walkingAnimationActive)
    {
        animation = ActorAiAnimationState::Walking;
    }

    const size_t actionIndex = static_cast<size_t>(animation);

    if (actionIndex < actionSpriteFrameIndices.size() && actionSpriteFrameIndices[actionIndex] != 0)
    {
        return actionSpriteFrameIndices[actionIndex];
    }

    const size_t standingIndex = static_cast<size_t>(ActorAiAnimationState::Standing);

    if (standingIndex < actionSpriteFrameIndices.size() && actionSpriteFrameIndices[standingIndex] != 0)
    {
        return actionSpriteFrameIndices[standingIndex];
    }

    return firstRuntimeActorSpriteFrameIndex(actionSpriteFrameIndices);
}

std::vector<RuntimeActorBillboard> buildRuntimeActorBillboards(
    const MonsterTable &monsterTable,
    const SpriteFrameTable &spriteFrameTable,
    const MapDeltaData &mapDeltaData,
    const IndoorWorldRuntime *pWorldRuntime = nullptr,
    const std::vector<uint8_t> *pVisibleSectorMask = nullptr
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
        const int16_t sectorId =
            pActorAiState != nullptr && pActorAiState->sectorId >= 0 ? pActorAiState->sectorId : actor.sectorId;

        if (!sectorVisibleForRuntimeBillboard(sectorId, pVisibleSectorMask))
        {
            continue;
        }

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
        billboard.sectorId = sectorId;
        billboard.radius = pActorAiState != nullptr ? pActorAiState->collisionRadius : actor.radius;
        billboard.height = pActorAiState != nullptr ? pActorAiState->collisionHeight : actor.height;
        billboard.spriteFrameIndex = spriteFrameIndex;
        billboard.actionSpriteFrameIndices = pActorAiState != nullptr
            ? pActorAiState->actionSpriteFrameIndices
            : buildRuntimeActorActionSpriteFrameIndices(spriteFrameTable, pMonsterEntry);
        if (pActorAiState != nullptr && pActorAiState->spellEffects.shrinkRemainingSeconds > 0.0f)
        {
            billboard.heightScale = std::clamp(pActorAiState->spellEffects.shrinkDamageMultiplier, 0.25f, 1.0f);
        }
        billboard.useStaticFrame = false;
        GameplayRuntimeActorState runtimeActorState = {};
        billboard.isFriendly =
            pWorldRuntime == nullptr
            || !pWorldRuntime->actorRuntimeState(actorIndex, runtimeActorState)
            || !runtimeActorState.hostileToParty;
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
    const MapDeltaData &mapDeltaData,
    const std::vector<uint8_t> *pVisibleSectorMask = nullptr
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

        if ((spriteObject.attributes & SpriteAttrRemoved) != 0)
        {
            continue;
        }

        if (!sectorVisibleForRuntimeBillboard(spriteObject.sectorId, pVisibleSectorMask))
        {
            continue;
        }

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

bx::Vec3 spriteFrameBillboardCenter(
    float x,
    float y,
    float z,
    const SpriteFrameEntry &frame,
    const bx::Vec3 &cameraUp,
    float worldHeight)
{
    if (SpriteFrameTable::hasFlag(frame.flags, SpriteFrameFlag::Center))
    {
        return {x, y, z};
    }

    return bottomAnchoredBillboardCenter(x, y, z, cameraUp, worldHeight);
}

bx::Vec3 transformIndoorPoint(const bx::Vec3 &point, const float *pMatrix)
{
    return {
        point.x * pMatrix[0] + point.y * pMatrix[4] + point.z * pMatrix[8] + pMatrix[12],
        point.x * pMatrix[1] + point.y * pMatrix[5] + point.z * pMatrix[9] + pMatrix[13],
        point.x * pMatrix[2] + point.y * pMatrix[6] + point.z * pMatrix[10] + pMatrix[14]
    };
}

float indoorPlaneDistance(const IndoorVisibilityPlane &plane, const bx::Vec3 &point)
{
    return vecDot(plane.normal, point) + plane.distance;
}

IndoorVisibilityPlane makeIndoorFrustumPlane(
    const bx::Vec3 &a,
    const bx::Vec3 &b,
    const bx::Vec3 &c,
    const bx::Vec3 &insidePoint)
{
    IndoorVisibilityPlane plane = {};
    plane.normal = vecNormalize(vecCross(vecSubtract(b, a), vecSubtract(c, a)));
    plane.distance = -vecDot(plane.normal, a);

    if (indoorPlaneDistance(plane, insidePoint) < 0.0f)
    {
        plane.normal = vecScale(plane.normal, -1.0f);
        plane.distance = -plane.distance;
    }

    return plane;
}

std::array<IndoorVisibilityPlane, 4> buildIndoorBillboardFrustumPlanes(
    const bx::Vec3 &cameraPosition,
    float yawRadians,
    float pitchRadians,
    float aspectRatio)
{
    const float cosPitch = std::cos(pitchRadians);
    const float sinPitch = std::sin(pitchRadians);
    const float cosYaw = std::cos(yawRadians);
    const float sinYaw = std::sin(yawRadians);
    const bx::Vec3 forward = vecNormalize({cosYaw * cosPitch, sinYaw * cosPitch, sinPitch});
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    bx::Vec3 right = vecNormalize(vecCross(forward, worldUp));

    if (vecLength(right) <= InspectRayEpsilon)
    {
        right = {0.0f, -1.0f, 0.0f};
    }

    const bx::Vec3 correctedUp = vecNormalize(vecCross(right, forward));
    constexpr float VerticalFovDegrees = 60.0f;
    const float halfHeight = std::tan((VerticalFovDegrees * Pi / 180.0f) * 0.5f);
    const float halfWidth = halfHeight * std::max(aspectRatio, 0.01f);
    const bx::Vec3 center = vecAdd(cameraPosition, forward);
    const bx::Vec3 rightOffset = vecScale(right, halfWidth);
    const bx::Vec3 upOffset = vecScale(correctedUp, halfHeight);
    const bx::Vec3 topLeft = vecAdd(vecSubtract(center, rightOffset), upOffset);
    const bx::Vec3 topRight = vecAdd(vecAdd(center, rightOffset), upOffset);
    const bx::Vec3 bottomLeft = vecSubtract(vecSubtract(center, rightOffset), upOffset);
    const bx::Vec3 bottomRight = vecSubtract(vecAdd(center, rightOffset), upOffset);
    const bx::Vec3 insidePoint = vecAdd(cameraPosition, forward);

    return {
        makeIndoorFrustumPlane(cameraPosition, topLeft, bottomLeft, insidePoint),
        makeIndoorFrustumPlane(cameraPosition, bottomRight, topRight, insidePoint),
        makeIndoorFrustumPlane(cameraPosition, topRight, topLeft, insidePoint),
        makeIndoorFrustumPlane(cameraPosition, bottomLeft, bottomRight, insidePoint)
    };
}

bool billboardSphereInFrustum(
    const bx::Vec3 &center,
    float radius,
    const std::array<IndoorVisibilityPlane, 4> &frustumPlanes)
{
    const float effectiveRadius = std::max(radius + BillboardFrustumSlack, 0.0f);

    for (const IndoorVisibilityPlane &plane : frustumPlanes)
    {
        if (indoorPlaneDistance(plane, center) < -effectiveRadius)
        {
            return false;
        }
    }

    return true;
}

bool sphereIntersectsIndoorVisibilityFrustum(
    const bx::Vec3 &center,
    float radius,
    const IndoorVisibilityFrustum &frustumPlanes)
{
    const float effectiveRadius = std::max(radius + BillboardFrustumSlack, 0.0f);

    for (const IndoorVisibilityPlane &plane : frustumPlanes)
    {
        if (indoorPlaneDistance(plane, center) < -effectiveRadius)
        {
            return false;
        }
    }

    return true;
}

bool sphereIntersectsVisibleSectorFrustums(
    int16_t sectorId,
    const bx::Vec3 &center,
    float radius,
    const std::vector<std::vector<IndoorVisibilityFrustum>> &visibleSectorFrustums)
{
    if (visibleSectorFrustums.empty())
    {
        return true;
    }

    if (sectorId < 0 || static_cast<size_t>(sectorId) >= visibleSectorFrustums.size())
    {
        return false;
    }

    const std::vector<IndoorVisibilityFrustum> &sectorFrustums =
        visibleSectorFrustums[static_cast<size_t>(sectorId)];

    for (const IndoorVisibilityFrustum &frustum : sectorFrustums)
    {
        if (sphereIntersectsIndoorVisibilityFrustum(center, radius, frustum))
        {
            return true;
        }
    }

    return false;
}

struct IndoorInteractiveDecorationBinding
{
    uint8_t decorVarIndex = 0;
    uint16_t baseEventId = 0;
    uint8_t eventCount = 0;
    bool hideWhenCleared = false;
};

constexpr uint8_t InvalidInteractiveDecorationDecorVarIndex = 0xff;
constexpr uint8_t MaxInteractiveDecorationDecorVarCount = 125;

void buildIndoorInteractiveDecorationBindingCaches(
    const IndoorMapData &indoorMapData,
    const DecorationBillboardSet *pBillboardSet,
    std::vector<uint8_t> &decorVarIndicesByEntity,
    std::vector<uint16_t> &baseEventIdsByEntity,
    std::vector<uint8_t> &eventCountsByEntity,
    std::vector<uint8_t> &hideWhenClearedByEntity)
{
    decorVarIndicesByEntity.assign(indoorMapData.entities.size(), InvalidInteractiveDecorationDecorVarIndex);
    baseEventIdsByEntity.assign(indoorMapData.entities.size(), 0);
    eventCountsByEntity.assign(indoorMapData.entities.size(), 0);
    hideWhenClearedByEntity.assign(indoorMapData.entities.size(), 0);

    if (pBillboardSet == nullptr)
    {
        return;
    }

    uint8_t decorVarIndex = 0;

    for (size_t entityIndex = 0; entityIndex < indoorMapData.entities.size(); ++entityIndex)
    {
        const IndoorEntity &entity = indoorMapData.entities[entityIndex];

        if (entity.scriptEventId() != 0)
        {
            continue;
        }

        const DecorationEntry *pDecoration = pBillboardSet->decorationTable.get(entity.decorationListId);

        if ((pDecoration == nullptr || pDecoration->spriteId == 0) && !entity.name.empty())
        {
            pDecoration = pBillboardSet->decorationTable.findByInternalName(entity.name);
        }

        if (pDecoration == nullptr)
        {
            continue;
        }

        const std::optional<InteractiveDecorationBindingSpec> bindingSpec =
            resolveInteractiveDecorationBindingSpec(*pDecoration, entity.name);

        if (!bindingSpec || decorVarIndex >= MaxInteractiveDecorationDecorVarCount)
        {
            continue;
        }

        decorVarIndicesByEntity[entityIndex] = decorVarIndex;
        baseEventIdsByEntity[entityIndex] = bindingSpec->baseEventId;
        eventCountsByEntity[entityIndex] = bindingSpec->eventCount;
        hideWhenClearedByEntity[entityIndex] = bindingSpec->hideWhenCleared ? 1 : 0;

        ++decorVarIndex;
    }
}

std::optional<IndoorInteractiveDecorationBinding> resolveIndoorInteractiveDecorationBinding(
    const std::vector<uint8_t> &decorVarIndicesByEntity,
    const std::vector<uint16_t> &baseEventIdsByEntity,
    const std::vector<uint8_t> &eventCountsByEntity,
    const std::vector<uint8_t> &hideWhenClearedByEntity,
    size_t targetEntityIndex)
{
    if (targetEntityIndex >= decorVarIndicesByEntity.size()
        || targetEntityIndex >= baseEventIdsByEntity.size()
        || targetEntityIndex >= eventCountsByEntity.size()
        || targetEntityIndex >= hideWhenClearedByEntity.size())
    {
        return std::nullopt;
    }

    const uint8_t decorVarIndex = decorVarIndicesByEntity[targetEntityIndex];

    if (decorVarIndex == InvalidInteractiveDecorationDecorVarIndex)
    {
        return std::nullopt;
    }

    IndoorInteractiveDecorationBinding binding = {};
    binding.decorVarIndex = decorVarIndex;
    binding.baseEventId = baseEventIdsByEntity[targetEntityIndex];
    binding.eventCount = eventCountsByEntity[targetEntityIndex];
    binding.hideWhenCleared = hideWhenClearedByEntity[targetEntityIndex] != 0;

    if (binding.baseEventId == 0 || binding.eventCount == 0)
    {
        return std::nullopt;
    }

    return binding;
}

std::optional<uint16_t> resolveIndoorInteractiveDecorationEventId(
    const EventRuntimeState &eventRuntimeState,
    const IndoorInteractiveDecorationBinding &binding)
{
    uint8_t state = eventRuntimeState.decorVars[binding.decorVarIndex];

    if (binding.hideWhenCleared && state == binding.eventCount)
    {
        return std::nullopt;
    }

    if (state >= binding.eventCount)
    {
        state = 0;
    }

    return static_cast<uint16_t>(binding.baseEventId + state);
}

uint16_t resolveIndoorEntityScriptEventId(const IndoorEntity &entity)
{
    return entity.scriptEventId();
}

uint16_t resolveIndoorEntityScriptEventId(uint16_t eventIdSecondary)
{
    return eventIdSecondary;
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

bool calculateFaceTextureAxes(
    const IndoorFace &face,
    const bx::Vec3 &normal,
    bx::Vec3 &axisU,
    bx::Vec3 &axisV
)
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

    return mechanismIterator->second.currentDistance;
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

std::optional<std::string> resolveIndoorEventHintText(
    const IndoorSceneRuntime *pSceneRuntime,
    uint16_t eventId)
{
    if (pSceneRuntime == nullptr || eventId == 0)
    {
        return std::nullopt;
    }

    const std::optional<ScriptedEventProgram> &localEventProgram = pSceneRuntime->localEventProgram();

    if (localEventProgram)
    {
        const std::optional<std::string> hint = localEventProgram->getHint(eventId);

        if (hint && !hint->empty())
        {
            return hint;
        }

        const std::optional<std::string> summary = localEventProgram->summarizeEvent(eventId);

        if (summary && !summary->empty())
        {
            return summary;
        }
    }

    const std::optional<ScriptedEventProgram> &globalEventProgram = pSceneRuntime->globalEventProgram();

    if (globalEventProgram)
    {
        const std::optional<std::string> hint = globalEventProgram->getHint(eventId);

        if (hint && !hint->empty())
        {
            return hint;
        }

        const std::optional<std::string> summary = globalEventProgram->summarizeEvent(eventId);

        if (summary && !summary->empty())
        {
            return summary;
        }
    }

    return std::nullopt;
}

std::optional<std::string> resolveIndoorLocalEventHintText(
    const IndoorSceneRuntime *pSceneRuntime,
    uint16_t eventId)
{
    if (pSceneRuntime == nullptr || eventId == 0)
    {
        return std::nullopt;
    }

    const std::optional<ScriptedEventProgram> &localEventProgram = pSceneRuntime->localEventProgram();

    if (!localEventProgram)
    {
        return std::nullopt;
    }

    const std::optional<std::string> hint = localEventProgram->getHint(eventId);

    if (hint && !hint->empty())
    {
        return hint;
    }

    const std::optional<std::string> summary = localEventProgram->summarizeEvent(eventId);

    if (summary && !summary->empty())
    {
        return summary;
    }

    return std::nullopt;
}

std::optional<std::string> resolveIndoorGlobalEventHintText(
    const IndoorSceneRuntime *pSceneRuntime,
    uint16_t eventId)
{
    if (pSceneRuntime == nullptr || eventId == 0)
    {
        return std::nullopt;
    }

    const std::optional<ScriptedEventProgram> &globalEventProgram = pSceneRuntime->globalEventProgram();

    if (!globalEventProgram)
    {
        return std::nullopt;
    }

    const std::optional<std::string> hint = globalEventProgram->getHint(eventId);

    if (hint && !hint->empty())
    {
        return hint;
    }

    const std::optional<std::string> summary = globalEventProgram->summarizeEvent(eventId);

    if (summary && !summary->empty())
    {
        return summary;
    }

    return std::nullopt;
}

std::vector<uint32_t> resolveIndoorOpenedChestIds(
    const IndoorSceneRuntime *pSceneRuntime,
    uint16_t eventId,
    bool allowGlobalFallback = true)
{
    if (pSceneRuntime == nullptr || eventId == 0)
    {
        return {};
    }

    const std::optional<ScriptedEventProgram> &localEventProgram = pSceneRuntime->localEventProgram();

    if (localEventProgram)
    {
        const std::vector<uint32_t> chestIds = localEventProgram->getOpenedChestIds(eventId);

        if (!chestIds.empty())
        {
            return chestIds;
        }
    }

    if (!allowGlobalFallback)
    {
        return {};
    }

    const std::optional<ScriptedEventProgram> &globalEventProgram = pSceneRuntime->globalEventProgram();
    return globalEventProgram ? globalEventProgram->getOpenedChestIds(eventId) : std::vector<uint32_t>{};
}

static GameplayEventTargetContextActionMetadata toGameplayContextActionMetadata(
    const ScriptedEventProgram::ContextActionMetadata &metadata)
{
    GameplayEventTargetContextActionMetadata gameplayMetadata = {};
    gameplayMetadata.kind = metadata.kind;
    gameplayMetadata.source = metadata.source;
    gameplayMetadata.houseId = metadata.houseId;
    gameplayMetadata.targetMap = metadata.targetMap;
    gameplayMetadata.targetName = metadata.targetName;
    gameplayMetadata.chestIds = metadata.chestIds;
    gameplayMetadata.hidden = metadata.hidden;
    return gameplayMetadata;
}

std::optional<GameplayEventTargetContextActionMetadata> resolveIndoorContextActionMetadata(
    const IndoorSceneRuntime *pSceneRuntime,
    uint16_t eventId,
    bool allowGlobalFallback = true)
{
    if (pSceneRuntime == nullptr || eventId == 0)
    {
        return std::nullopt;
    }

    const std::optional<ScriptedEventProgram> &localEventProgram = pSceneRuntime->localEventProgram();

    if (localEventProgram)
    {
        const std::optional<ScriptedEventProgram::ContextActionMetadata> metadata =
            localEventProgram->getContextActionMetadata(eventId);

        if (metadata)
        {
            return toGameplayContextActionMetadata(*metadata);
        }
    }

    if (!allowGlobalFallback)
    {
        return std::nullopt;
    }

    const std::optional<ScriptedEventProgram> &globalEventProgram = pSceneRuntime->globalEventProgram();
    if (!globalEventProgram)
    {
        return std::nullopt;
    }

    const std::optional<ScriptedEventProgram::ContextActionMetadata> metadata =
        globalEventProgram->getContextActionMetadata(eventId);

    if (!metadata)
    {
        return std::nullopt;
    }

    return toGameplayContextActionMetadata(*metadata);
}

bool indoorEventIsHintOnly(
    const IndoorSceneRuntime *pSceneRuntime,
    uint16_t eventId,
    bool allowGlobalFallback = true)
{
    if (pSceneRuntime == nullptr || eventId == 0)
    {
        return false;
    }

    const std::optional<ScriptedEventProgram> &localEventProgram = pSceneRuntime->localEventProgram();

    if (localEventProgram && localEventProgram->isHintOnlyEvent(eventId))
    {
        return true;
    }

    if (localEventProgram && localEventProgram->hasEvent(eventId))
    {
        return false;
    }

    if (!allowGlobalFallback)
    {
        return false;
    }

    const std::optional<ScriptedEventProgram> &globalEventProgram = pSceneRuntime->globalEventProgram();
    return globalEventProgram && globalEventProgram->isHintOnlyEvent(eventId);
}

bool indoorFaceIsInteractionActivatable(uint32_t attributes, uint16_t eventId)
{
    return eventId != 0
        && hasFaceAttribute(attributes, FaceAttribute::Clickable)
        && !hasFaceAttribute(attributes, FaceAttribute::HasHint)
        && !hasFaceAttribute(attributes, FaceAttribute::Invisible);
}

bool indoorFaceHasActualEvent(const IndoorSceneRuntime *pSceneRuntime, const IndoorFace &face)
{
    if (pSceneRuntime == nullptr || face.cogTriggered == 0)
    {
        return false;
    }

    const std::optional<ScriptedEventProgram> &localEventProgram = pSceneRuntime->localEventProgram();

    if (localEventProgram && localEventProgram->hasEvent(face.cogTriggered))
    {
        return true;
    }

    const std::optional<ScriptedEventProgram> &globalEventProgram = pSceneRuntime->globalEventProgram();
    return globalEventProgram && globalEventProgram->hasEvent(face.cogTriggered);
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

bool indoorFaceRayBoundsHit(
    const IndoorFace &face,
    const std::vector<IndoorVertex> &vertices,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    float bestDistance)
{
    bx::Vec3 minBounds = {
        std::numeric_limits<float>::max(),
        std::numeric_limits<float>::max(),
        std::numeric_limits<float>::max()
    };
    bx::Vec3 maxBounds = {
        -std::numeric_limits<float>::max(),
        -std::numeric_limits<float>::max(),
        -std::numeric_limits<float>::max()
    };

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            return false;
        }

        const IndoorVertex &vertex = vertices[vertexIndex];
        minBounds.x = std::min(minBounds.x, static_cast<float>(vertex.x));
        minBounds.y = std::min(minBounds.y, static_cast<float>(vertex.y));
        minBounds.z = std::min(minBounds.z, static_cast<float>(vertex.z));
        maxBounds.x = std::max(maxBounds.x, static_cast<float>(vertex.x));
        maxBounds.y = std::max(maxBounds.y, static_cast<float>(vertex.y));
        maxBounds.z = std::max(maxBounds.z, static_cast<float>(vertex.z));
    }

    constexpr float BoundsPadding = 1.0f;
    minBounds.x -= BoundsPadding;
    minBounds.y -= BoundsPadding;
    minBounds.z -= BoundsPadding;
    maxBounds.x += BoundsPadding;
    maxBounds.y += BoundsPadding;
    maxBounds.z += BoundsPadding;

    float boundsDistance = 0.0f;
    return intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, boundsDistance)
        && boundsDistance <= bestDistance;
}

std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName)
{
    const std::filesystem::path configuredShaderRoot = OPENYAMM_BGFX_SHADER_DIR;
    std::string rendererDirectory;

    switch (rendererType)
    {
    case bgfx::RendererType::Direct3D11:
        rendererDirectory = "dxbc";
        break;

    case bgfx::RendererType::OpenGL:
        rendererDirectory = "glsl";
        break;

    case bgfx::RendererType::OpenGLES:
        rendererDirectory = "essl";
        break;

    default:
        return {};
    }

    const std::filesystem::path shaderName =
        std::filesystem::path(rendererDirectory) / (std::string(pShaderName) + ".bin");

    if (configuredShaderRoot.is_absolute())
    {
        return configuredShaderRoot / shaderName;
    }

    if (const char *pBasePath = SDL_GetBasePath())
    {
        const std::filesystem::path executableRoot = pBasePath;
        const std::filesystem::path packagedPath = executableRoot / configuredShaderRoot / shaderName;

        if (std::filesystem::exists(packagedPath))
        {
            return packagedPath;
        }

        const std::filesystem::path buildTreePath = executableRoot / ".." / configuredShaderRoot / shaderName;

        if (std::filesystem::exists(buildTreePath))
        {
            return buildTreePath;
        }

        return packagedPath;
    }

    return configuredShaderRoot / shaderName;
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
    size_t faceIndex,
    const IndoorFace &face,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    if (!eventRuntimeState)
    {
        return face.textureName;
    }

    const uint32_t faceIndexCandidate =
        faceIndex <= static_cast<size_t>(std::numeric_limits<uint32_t>::max())
            ? static_cast<uint32_t>(faceIndex)
            : 0;
    const uint32_t cogCandidates[3] = {faceIndexCandidate, face.cogNumber, face.textureFrameTableCog};

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

std::array<float, 4> billboardAmbientUniform(
    const IndoorLightingFrame &lightingFrame,
    const bx::Vec3 &position,
    int16_t sectorId,
    LightingStats *pLightingStats)
{
    const uint64_t sampleBeginTickCount = pLightingStats != nullptr ? SDL_GetTicksNS() : 0;
    const std::array<float, 3> rgb =
        IndoorLightingRuntime::sampleLightingRgbForSectors(
            lightingFrame,
            position,
            sectorId,
            -1,
            pLightingStats);
    if (pLightingStats != nullptr)
    {
        pLightingStats->billboardSampleNanoseconds += SDL_GetTicksNS() - sampleBeginTickCount;
    }
    return {{rgb[0], rgb[1], rgb[2], 0.0f}};
}

std::array<float, 4> billboardLightingUniform(
    const IndoorLightingFrame &lightingFrame,
    const SpriteFrameEntry &frame,
    const bx::Vec3 &position,
    int16_t sectorId,
    LightingStats *pLightingStats)
{
    if (SpriteFrameTable::hasFlag(frame.flags, SpriteFrameFlag::Lit))
    {
        return {{1.0f, 1.0f, 1.0f, 0.0f}};
    }

    return billboardAmbientUniform(lightingFrame, position, sectorId, pLightingStats);
}

uint32_t resolveHoveredIndoorActorOutlineColor(
    const MapDeltaActor &actor,
    const IndoorWorldRuntime::MapActorAiState *pAiState)
{
    if (actor.hp <= 0 || (pAiState != nullptr && pAiState->motionState == ActorAiMotionState::Dead))
    {
        return makeAbgr(255, 224, 64);
    }

    if ((actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Aggressor)) != 0
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

uint32_t contextActionHighlightOutlineColor()
{
    return makeAbgr(56, 216, 255);
}

uint32_t makeAbgrAlpha(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

uint32_t contextActionGeometryHighlightColor(float elapsedTime)
{
    const float pulse = 0.5f + 0.5f * std::sin(elapsedTime * 4.0f);
    const uint8_t alpha = static_cast<uint8_t>(std::clamp(std::lround(52.0f + pulse * 52.0f), 0l, 255l));
    return makeAbgrAlpha(56, 216, 255, alpha);
}

const GameplayWorldHit *selectedContextActionWorldHit(const GameplayContextActionState *pState)
{
    if (pState == nullptr || !pState->visible || pState->primaryIndex >= pState->actions.size())
    {
        return nullptr;
    }

    const GameplayWorldHit &hit = pState->actions[pState->primaryIndex].worldHit;
    return hit.hasHit ? &hit : nullptr;
}

bool contextActionHighlightsActor(const GameplayWorldHit *pHit, size_t actorIndex)
{
    return pHit != nullptr
        && pHit->kind == GameplayWorldHitKind::Actor
        && pHit->actor.has_value()
        && pHit->actor->actorIndex == actorIndex;
}

bool contextActionHighlightsWorldItem(const GameplayWorldHit *pHit, size_t worldItemIndex)
{
    return pHit != nullptr
        && pHit->kind == GameplayWorldHitKind::WorldItem
        && pHit->worldItem.has_value()
        && pHit->worldItem->worldItemIndex == worldItemIndex;
}

bool contextActionHighlightsIndoorEntity(const GameplayWorldHit *pHit, size_t entityIndex)
{
    return pHit != nullptr
        && pHit->kind == GameplayWorldHitKind::EventTarget
        && pHit->eventTarget.has_value()
        && pHit->eventTarget->targetKind == GameplayWorldEventTargetKind::Entity
        && pHit->eventTarget->targetIndex == entityIndex;
}

std::string normalizeBillboardTextureName(const std::string &textureName)
{
    for (const char character : textureName)
    {
        if (std::isupper(static_cast<unsigned char>(character)) != 0)
        {
            return toLowerCopy(textureName);
        }
    }

    return textureName;
}

std::array<float, 4> indoorFaceFlowInfo(
    uint32_t effectiveAttributes,
    uint8_t facetType,
    int textureWidth,
    int textureHeight)
{
    constexpr float FlowPixelsPerSecond = 62.5f;
    constexpr float IndoorSkyTextureScale = 0.25f;
    constexpr float IndoorSkyScrollPixelsPerSecond = 1000.0f / 64.0f * IndoorSkyTextureScale;
    std::array<float, 4> flowInfo = {0.0f, 0.0f, 0.0f, 0.0f};

    if (textureWidth <= 0 || textureHeight <= 0)
    {
        return flowInfo;
    }

    if (hasFaceAttribute(effectiveAttributes, FaceAttribute::IndoorSky)
        && facetType != 3
        && facetType != 4)
    {
        flowInfo[0] = 1.0f / static_cast<float>(textureWidth);
        flowInfo[1] = 1.0f / static_cast<float>(textureHeight);
        flowInfo[3] = -2.0f;
        return flowInfo;
    }

    if (hasFaceAttribute(effectiveAttributes, FaceAttribute::FlowDown))
    {
        flowInfo[1] = -FlowPixelsPerSecond / static_cast<float>(textureHeight);
    }
    else if (hasFaceAttribute(effectiveAttributes, FaceAttribute::FlowUp))
    {
        flowInfo[1] = FlowPixelsPerSecond / static_cast<float>(textureHeight);
    }

    if (hasFaceAttribute(effectiveAttributes, FaceAttribute::FlowRight))
    {
        flowInfo[0] = FlowPixelsPerSecond / static_cast<float>(textureWidth);
    }
    else if (hasFaceAttribute(effectiveAttributes, FaceAttribute::FlowLeft))
    {
        flowInfo[0] = -FlowPixelsPerSecond / static_cast<float>(textureWidth);
    }

    flowInfo[2] = hasFaceAttribute(effectiveAttributes, FaceAttribute::Lava) ? 1.0f : 0.0f;
    flowInfo[3] = hasFaceAttribute(effectiveAttributes, FaceAttribute::Fluid) ? 1.0f : 0.0f;

    if (hasFaceAttribute(effectiveAttributes, FaceAttribute::IndoorSky))
    {
        flowInfo[0] += IndoorSkyScrollPixelsPerSecond / static_cast<float>(textureWidth);
        flowInfo[1] += IndoorSkyScrollPixelsPerSecond / static_cast<float>(textureHeight);
        flowInfo[3] = -1.0f;
    }

    return flowInfo;
}

float indoorFaceTextureCoordinateScale(uint32_t effectiveAttributes, uint8_t facetType)
{
    if (!hasFaceAttribute(effectiveAttributes, FaceAttribute::IndoorSky))
    {
        return 1.0f;
    }

    return (facetType == 3 || facetType == 4) ? 0.25f : 1.0f;
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
    , m_secretPulseParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_indoorFaceAlphaParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_indoorSkyParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_indoorSkyProjectionParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardAmbientUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardOverrideColorUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardOutlineParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardFogColorUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardFogDensitiesUniformHandle(BGFX_INVALID_HANDLE)
    , m_billboardFogDistancesUniformHandle(BGFX_INVALID_HANDLE)
    , m_elapsedTime(0.0f)
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
    m_ceilingFaceMask = buildIndoorCeilingFaceMask(indoorMapData);
    m_arpgModeOcclusionGeometryCache.reset(indoorMapData.faces.size());
    clearPortalVisibilityCaches();
    m_pSceneRuntime = &sceneRuntime;
    m_indoorPortalGraph = buildIndoorPortalGraph(
        indoorMapData,
        runtimeMapDeltaData() ? &runtimeMapDeltaData().value() : nullptr);
    m_neighboringSectorIds.assign(indoorMapData.sectors.size(), {});

    for (size_t sectorId = 0; sectorId < m_indoorPortalGraph->sectors.size(); ++sectorId)
    {
        if (sectorId <= std::numeric_limits<uint16_t>::max())
        {
            m_neighboringSectorIds[sectorId].push_back(static_cast<uint16_t>(sectorId));
        }

        for (uint16_t connectedSectorId : m_indoorPortalGraph->sectors[sectorId].connectedSectorIds)
        {
            m_neighboringSectorIds[sectorId].push_back(connectedSectorId);
        }
    }

    m_renderVertices = buildMechanismAdjustedVertices(
        indoorMapData,
        runtimeMapDeltaData(),
        runtimeEventRuntimeStateStorage());
    m_indoorTextureSet = indoorTextureSet;
    m_indoorDecorationBillboardSet = indoorDecorationBillboardSet;
    buildIndoorInteractiveDecorationBindingCaches(
        indoorMapData,
        m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr,
        m_indoorInteractiveDecorationDecorVarIndicesByEntity,
        m_indoorInteractiveDecorationBaseEventIdsByEntity,
        m_indoorInteractiveDecorationEventCountsByEntity,
        m_indoorInteractiveDecorationHideWhenClearedByEntity);
    m_indoorActorPreviewBillboardSet = indoorActorPreviewBillboardSet;
    m_indoorSpriteObjectBillboardSet = indoorSpriteObjectBillboardSet;
    rebuildIndoorRenderMemberships();
    m_indoorLightingRuntime.rebuildStaticCache(
        indoorMapData,
        m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr);
    m_chestTable = chestTable;
    m_houseTable = houseTable;
    rebuildMechanismBindings();

    if (m_pSceneRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        m_cameraPositionX = moveState.x;
        m_cameraPositionY = moveState.y;
        m_cameraPositionZ = moveState.eyeZ();
    }

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        m_isRenderable = true;
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
                registerBillboardTextureIndex(m_billboardTextureHandles.size() - 1);
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
                registerBillboardTextureIndex(m_billboardTextureHandles.size() - 1);
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
                registerBillboardTextureIndex(m_billboardTextureHandles.size() - 1);
            }
        }
    }

    m_faceCount = static_cast<uint32_t>(indoorMapData.faces.size());
    m_programHandle = loadProgram("vs_cubes", "fs_cubes");
    m_texturedProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_shadowmaps_texture");
    m_indoorLitProgramHandle = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_lit");
    m_billboardProgramHandle = loadProgram("vs_outdoor_billboard_lit", "fs_outdoor_billboard_lit");
    m_worldFxRenderResources.setParticleProgramHandle(loadProgram("vs_particle", "fs_particle"));
    m_worldFxRenderResources.setBeamProgramHandle(loadProgram("vs_beam", "fs_beam"));
    ParticleRenderer::initializeResources(m_worldFxRenderResources);
    m_textureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);
    m_indoorLightPositionsUniformHandle =
        bgfx::createUniform("u_indoorLightPositions", bgfx::UniformType::Vec4, MaxIndoorShaderLights);
    m_indoorLightColorsUniformHandle =
        bgfx::createUniform("u_indoorLightColors", bgfx::UniformType::Vec4, MaxIndoorShaderLights);
    m_indoorLightParamsUniformHandle = bgfx::createUniform("u_indoorLightParams", bgfx::UniformType::Vec4);
    m_secretPulseParamsUniformHandle = bgfx::createUniform("u_secretPulseParams", bgfx::UniformType::Vec4);
    m_indoorFaceAlphaParamsUniformHandle = bgfx::createUniform("u_indoorFaceAlphaParams", bgfx::UniformType::Vec4);
    m_indoorSkyParamsUniformHandle = bgfx::createUniform("u_indoorSkyParams", bgfx::UniformType::Vec4);
    m_indoorSkyProjectionParamsUniformHandle =
        bgfx::createUniform("u_indoorSkyProjectionParams", bgfx::UniformType::Vec4);
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
        || !bgfx::isValid(m_secretPulseParamsUniformHandle)
        || !bgfx::isValid(m_indoorFaceAlphaParamsUniformHandle)
        || !bgfx::isValid(m_indoorSkyParamsUniformHandle)
        || !bgfx::isValid(m_indoorSkyProjectionParamsUniformHandle)
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

    m_isRenderable = true;
    return true;
}

bool IndoorRenderer::isFaceVisible(
    size_t faceIndex,
    const IndoorFace &face,
    const std::optional<MapDeltaData> &indoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    const uint32_t effectiveAttributes =
        indoorMapDeltaData && faceIndex < indoorMapDeltaData->faceAttributes.size()
            ? indoorMapDeltaData->faceAttributes[faceIndex]
            : face.attributes;

    if (hasFaceAttribute(effectiveAttributes, FaceAttribute::Invisible))
    {
        return false;
    }

    return !faceHasInvisibleOverride(faceIndex, eventRuntimeState);
}

void IndoorRenderer::clearPortalVisibilityCaches() const
{
    m_renderPortalVisibilityCache.clear();
}

std::vector<uint8_t> IndoorRenderer::buildVisibleSectorMask(const bx::Vec3 &cameraPosition) const
{
    const bool collectDiagnostics = m_logIndoorPerformanceDiagnostics;
    const uint64_t totalBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;

    if (!m_indoorMapData || m_indoorMapData->sectors.empty())
    {
        return {};
    }

    int16_t startSectorId = -1;

    if (m_pSceneRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        const size_t sectorCount = m_indoorMapData->sectors.size();

        if (moveState.eyeSectorId >= 0 && static_cast<size_t>(moveState.eyeSectorId) < sectorCount)
        {
            startSectorId = moveState.eyeSectorId;
        }
        else if (moveState.sectorId >= 0 && static_cast<size_t>(moveState.sectorId) < sectorCount)
        {
            startSectorId = moveState.sectorId;
        }
    }

    if (startSectorId < 0)
    {
        clearPortalVisibilityCaches();
        return {};
    }

    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    PortalVisibilityCache &cache = m_renderPortalVisibilityCache;
    const float aspectRatio =
        m_lastRenderHeight > 0
        ? static_cast<float>(std::max(m_lastRenderWidth, 1)) / static_cast<float>(m_lastRenderHeight)
        : 1.0f;

    if (cache.valid
        && cache.sectorId == startSectorId
        && cache.visibleSectorMask.size() == m_indoorMapData->sectors.size()
        && cache.cameraX == cameraPosition.x
        && cache.cameraY == cameraPosition.y
        && cache.cameraZ == cameraPosition.z
        && cache.yawRadians == m_cameraYawRadians
        && cache.pitchRadians == m_cameraPitchRadians
        && cache.aspectRatio == aspectRatio)
    {
        if (collectDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.visibilityCalls;

            ++m_indoorPerformanceDiagnostics.visibilityCacheHits;
            m_indoorPerformanceDiagnostics.visibilityTotalNanoseconds +=
                SDL_GetTicksNS() - totalBeginTickCount;
        }

        return cache.visibleSectorMask;
    }

    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    IndoorPortalVisibilityInput input = {};
    input.pMapData = &m_indoorMapData.value();
    input.pPortalGraph = m_indoorPortalGraph ? &m_indoorPortalGraph.value() : nullptr;
    input.pVertices = &m_renderVertices;
    input.pPortalVertices = &m_indoorMapData->vertices;
    input.pMapDeltaData = mapDeltaData ? &mapDeltaData.value() : nullptr;
    input.pEventRuntimeState = &eventRuntimeState;
    input.cameraPosition = cameraPosition;
    input.cameraForward = {cosYaw * cosPitch, sinYaw * cosPitch, sinPitch};
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = 60.0f;
    input.aspectRatio = aspectRatio;
    input.startSectorId = startSectorId;

    const uint64_t visibilityBuildBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
    const IndoorPortalVisibilityResult visibility = buildIndoorPortalVisibility(input);

    if (collectDiagnostics)
    {
        ++m_indoorPerformanceDiagnostics.visibilityCalls;

        ++m_indoorPerformanceDiagnostics.visibilityBuilds;
        m_indoorPerformanceDiagnostics.visibilityBuildNanoseconds +=
            SDL_GetTicksNS() - visibilityBuildBeginTickCount;
        m_indoorPerformanceDiagnostics.visibilityTotalNanoseconds +=
            SDL_GetTicksNS() - totalBeginTickCount;
        m_indoorPerformanceDiagnostics.visibilityPortalCandidates += visibility.portalCandidateCount;
        m_indoorPerformanceDiagnostics.visibilityPortalsAccepted += visibility.acceptedPortalCount;
        m_indoorPerformanceDiagnostics.visibilityPortalsRejected += visibility.rejectedPortalCount;
    }

    cache.valid = true;
    cache.sectorId = startSectorId;
    cache.cameraX = cameraPosition.x;
    cache.cameraY = cameraPosition.y;
    cache.cameraZ = cameraPosition.z;
    cache.yawRadians = m_cameraYawRadians;
    cache.pitchRadians = m_cameraPitchRadians;
    cache.aspectRatio = aspectRatio;
    cache.visibleSectorMask = visibility.visibleSectorMask;
    cache.visibleSectorFrustums = visibility.frustumsBySector;
    cache.portalTraces = visibility.portalTraces;
    return cache.visibleSectorMask;
}

std::vector<uint8_t> IndoorRenderer::buildArpgModeRenderVisibleSectorMask(
    const std::vector<uint8_t> &cameraVisibleSectorMask) const
{
    if (!m_indoorMapData || m_indoorMapData->sectors.empty())
    {
        return cameraVisibleSectorMask;
    }

    int16_t startSectorId = -1;
    int16_t partySectorId = -1;
    int16_t eyeSectorId = -1;

    if (m_pSceneRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        const size_t sectorCount = m_indoorMapData->sectors.size();

        if (moveState.sectorId >= 0 && static_cast<size_t>(moveState.sectorId) < sectorCount)
        {
            partySectorId = moveState.sectorId;
        }

        if (moveState.eyeSectorId >= 0 && static_cast<size_t>(moveState.eyeSectorId) < sectorCount)
        {
            eyeSectorId = moveState.eyeSectorId;
        }

        if (moveState.eyeSectorId >= 0 && static_cast<size_t>(moveState.eyeSectorId) < sectorCount)
        {
            startSectorId = moveState.eyeSectorId;
        }
        else if (moveState.sectorId >= 0 && static_cast<size_t>(moveState.sectorId) < sectorCount)
        {
            startSectorId = moveState.sectorId;
        }
    }

    if (startSectorId < 0)
    {
        return cameraVisibleSectorMask;
    }

    const IndoorSector &startSector = m_indoorMapData->sectors[static_cast<size_t>(startSectorId)];
    const int higherSectorCullMinZ = static_cast<int>(startSector.maxZ) + ArpgModeIndoorHigherSectorCullMargin;
    std::vector<uint8_t> visibleSectorMask(m_indoorMapData->sectors.size(), 0);

    for (size_t sectorId = 0; sectorId < visibleSectorMask.size() && sectorId < cameraVisibleSectorMask.size();
         ++sectorId)
    {
        const IndoorSector &sector = m_indoorMapData->sectors[sectorId];

        if (cameraVisibleSectorMask[sectorId] != 0 && sector.minZ <= higherSectorCullMinZ)
        {
            visibleSectorMask[sectorId] = 1;
        }
    }

    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

    const auto appendSector =
        [&](int16_t sectorId)
        {
            if (sectorId < 0 || static_cast<size_t>(sectorId) >= visibleSectorMask.size())
            {
                return;
            }

            const IndoorSector &sector = m_indoorMapData->sectors[static_cast<size_t>(sectorId)];

            if (sector.minZ > higherSectorCullMinZ)
            {
                return;
            }

            visibleSectorMask[static_cast<size_t>(sectorId)] = 1;
        };

    const auto appendImmediatePortalNeighbors =
        [&](int16_t sectorId)
        {
            appendSector(sectorId);

            if (!m_indoorPortalGraph
                || sectorId < 0
                || static_cast<size_t>(sectorId) >= m_indoorPortalGraph->sectors.size())
            {
                return;
            }

            const IndoorSectorPortalCache &sectorPortalCache =
                m_indoorPortalGraph->sectors[static_cast<size_t>(sectorId)];

            for (size_t linkOffset = 0; linkOffset < sectorPortalCache.portalLinkIds.size(); ++linkOffset)
            {
                const uint16_t portalLinkId = sectorPortalCache.portalLinkIds[linkOffset];

                if (portalLinkId >= m_indoorPortalGraph->portals.size()
                    || linkOffset >= sectorPortalCache.connectedSectorIds.size())
                {
                    continue;
                }

                const IndoorPortalLink &portalLink = m_indoorPortalGraph->portals[portalLinkId];

                if (portalLink.faceId >= m_indoorMapData->faces.size())
                {
                    continue;
                }

                const IndoorFace &portalFace = m_indoorMapData->faces[portalLink.faceId];

                if (!isFaceVisible(portalLink.faceId, portalFace, mapDeltaData, eventRuntimeState))
                {
                    continue;
                }

                appendSector(static_cast<int16_t>(sectorPortalCache.connectedSectorIds[linkOffset]));
            }
        };

    appendImmediatePortalNeighbors(partySectorId);

    if (eyeSectorId != partySectorId)
    {
        appendImmediatePortalNeighbors(eyeSectorId);
    }

    return visibleSectorMask;
}

void IndoorRenderer::logIndoorVisibilityDiagnostics(
    const std::vector<uint8_t> &baseVisibleSectorMask,
    const std::vector<uint8_t> &renderVisibleSectorMask,
    uint32_t currentTick
) const
{
    constexpr uint32_t LogIntervalMs = 1000;

    if (currentTick - m_lastVisibilityDiagnosticsLogTick < LogIntervalMs
        || !m_indoorMapData
        || m_pSceneRuntime == nullptr)
    {
        return;
    }

    m_lastVisibilityDiagnosticsLogTick = currentTick;

    if (m_logIndoorVisibilityDiagnostics)
    {
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        const auto printMask = [](const std::vector<uint8_t> &mask)
        {
            std::cout << '[';
            bool first = true;

            for (size_t sectorId = 0; sectorId < mask.size(); ++sectorId)
            {
                if (mask[sectorId] == 0)
                {
                    continue;
                }

                if (!first)
                {
                    std::cout << ',';
                }

                std::cout << sectorId;
                first = false;
            }

            std::cout << ']';
        };
        const auto printSectorIds = [](const std::vector<int16_t> &sectorIds)
        {
            std::cout << '[';

            for (size_t index = 0; index < sectorIds.size(); ++index)
            {
                if (index != 0)
                {
                    std::cout << ',';
                }

                std::cout << sectorIds[index];
            }

            std::cout << ']';
        };
        const auto printNeighbors = [this](int16_t sectorId)
        {
            std::cout << '[';

            if (sectorId >= 0 && static_cast<size_t>(sectorId) < m_neighboringSectorIds.size())
            {
                const std::vector<uint16_t> &neighbors = m_neighboringSectorIds[sectorId];

                for (size_t index = 0; index < neighbors.size(); ++index)
                {
                    if (index > 0)
                    {
                        std::cout << ',';
                    }

                    std::cout << neighbors[index];
                }
            }

            std::cout << ']';
        };
        const PortalVisibilityCache &renderPortalCache = m_renderPortalVisibilityCache;

        std::cout << "[IndoorVisibility] party_sector=" << moveState.sectorId
                  << " eye_sector=" << moveState.eyeSectorId
                  << " base_visible=";
        printMask(baseVisibleSectorMask);
        std::cout << " render_visible=";
        printMask(renderVisibleSectorMask);
        std::cout << " adjacent_party=";
        printNeighbors(moveState.sectorId);
        std::cout << " adjacent_eye=";
        printNeighbors(moveState.eyeSectorId);
        std::cout << " seen_sectors=";
        printSectorIds(m_pSceneRuntime->worldRuntime().activatedIndoorSectorIds());
        std::cout << '\n';

        if (m_indoorPortalGraph)
        {
            std::vector<int16_t> portalDebugSectors;

            const auto appendPortalDebugSector = [&](int16_t sectorId)
            {
                if (sectorId < 0
                    || static_cast<size_t>(sectorId) >= m_indoorPortalGraph->sectors.size()
                    || std::find(portalDebugSectors.begin(), portalDebugSectors.end(), sectorId)
                        != portalDebugSectors.end())
                {
                    return;
                }

                portalDebugSectors.push_back(sectorId);
            };

            appendPortalDebugSector(moveState.sectorId);
            appendPortalDebugSector(moveState.eyeSectorId);

            for (const IndoorPortalVisibilityTrace &trace : renderPortalCache.portalTraces)
            {
                appendPortalDebugSector(trace.sourceSectorId);
            }

            for (int16_t sourceSectorId : portalDebugSectors)
            {
                const IndoorSectorPortalCache &sectorCache =
                    m_indoorPortalGraph->sectors[static_cast<size_t>(sourceSectorId)];

                if (sectorCache.portalLinkIds.empty())
                {
                    std::cout << "[IndoorVisibilityPortal] source=" << sourceSectorId
                              << " status=no_graph_portals\n";
                    continue;
                }

                for (uint16_t portalLinkId : sectorCache.portalLinkIds)
                {
                    if (portalLinkId >= m_indoorPortalGraph->portals.size())
                    {
                        std::cout << "[IndoorVisibilityPortal] source=" << sourceSectorId
                                  << " link=" << portalLinkId
                                  << " status=invalid_graph_link\n";
                        continue;
                    }

                    const IndoorPortalLink &portalLink = m_indoorPortalGraph->portals[portalLinkId];
                    const int16_t targetSectorId =
                        portalLink.sectorA == static_cast<uint16_t>(sourceSectorId)
                            ? static_cast<int16_t>(portalLink.sectorB)
                            : (portalLink.sectorB == static_cast<uint16_t>(sourceSectorId)
                                ? static_cast<int16_t>(portalLink.sectorA)
                                : static_cast<int16_t>(-1));
                    bool traceFound = false;

                    for (const IndoorPortalVisibilityTrace &trace : renderPortalCache.portalTraces)
                    {
                        if (trace.sourceSectorId != sourceSectorId || trace.faceId != portalLink.faceId)
                        {
                            continue;
                        }

                        traceFound = true;
                        std::cout << "[IndoorVisibilityPortal] source=" << sourceSectorId
                                  << " target=" << trace.targetSectorId
                                  << " face=" << trace.faceId
                                  << " link=" << trace.portalLinkId
                                  << " depth=" << trace.depth
                                  << " accepted=" << (trace.accepted ? 1 : 0)
                                  << " reason=" << trace.reason
                                  << '\n';
                    }

                    if (!traceFound)
                    {
                        std::cout << "[IndoorVisibilityPortal] source=" << sourceSectorId
                                  << " target=" << targetSectorId
                                  << " face=" << portalLink.faceId
                                  << " link=" << portalLinkId
                                  << " accepted=0"
                                  << " reason=not_run\n";
                    }
                }
            }
        }
    }

    const IndoorPerformanceDiagnostics diagnostics = m_indoorPerformanceDiagnostics;

    if (diagnostics.hasActivity())
    {
        const uint64_t measuredRenderNanoseconds =
            diagnostics.mechanismTotalNanoseconds
            + diagnostics.renderWorldFxNanoseconds
            + diagnostics.renderViewSetupNanoseconds
            + diagnostics.renderVisibilityNanoseconds
            + diagnostics.renderLightingNanoseconds
            + diagnostics.renderInspectNanoseconds
            + diagnostics.renderTexturedSubmitNanoseconds
            + diagnostics.renderBloodSplatsNanoseconds
            + diagnostics.renderDecorationNanoseconds
            + diagnostics.renderActorNanoseconds
            + diagnostics.renderSpriteObjectNanoseconds
            + diagnostics.renderParticleNanoseconds;
        const uint64_t untrackedRenderNanoseconds =
            diagnostics.renderTotalNanoseconds > measuredRenderNanoseconds
                ? diagnostics.renderTotalNanoseconds - measuredRenderNanoseconds
                : 0;
        const LightingStats &lightingStats = diagnostics.lightingStats;
        const uint64_t averageLightingSelectionNanoseconds = averageNanoseconds(
            lightingStats.selectionNanoseconds,
            lightingStats.selectionCalls);
        const uint64_t averageBillboardSampleNanoseconds = averageNanoseconds(
            lightingStats.billboardSampleNanoseconds,
            lightingStats.billboardSamples);

        std::cout << "[IndoorPerf]"
                  << " visibility_calls=" << diagnostics.visibilityCalls
                  << " visibility_cache_hits=" << diagnostics.visibilityCacheHits
                  << " visibility_builds=" << diagnostics.visibilityBuilds
                  << " avg_visibility_total_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.visibilityTotalNanoseconds,
                      diagnostics.visibilityCalls))
                  << " avg_visibility_build_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.visibilityBuildNanoseconds,
                      diagnostics.visibilityBuilds))
                  << " portal_candidates=" << diagnostics.visibilityPortalCandidates
                  << " portals_accepted=" << diagnostics.visibilityPortalsAccepted
                  << " portals_rejected=" << diagnostics.visibilityPortalsRejected
                  << " simulation_calls=" << diagnostics.simulationCalls
                  << " simulation_advanced=" << diagnostics.simulationAdvancedFrames
                  << " moving_frames=" << diagnostics.movingFrames
                  << " moving_update_failures=" << diagnostics.movingUpdateFailures
                  << " moving_full_rebuilds=" << diagnostics.movingFullRebuilds
                  << " moving_fallback_full_rebuilds=" << diagnostics.movingFallbackFullRebuilds
                  << " mechanism_settle_full_rebuilds=" << diagnostics.mechanismSettleFullRebuilds
                  << " avg_simulation_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.simulationNanoseconds,
                      diagnostics.simulationCalls))
                  << " avg_mechanism_probe_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.mechanismProbeNanoseconds,
                      diagnostics.simulationAdvancedFrames))
                  << " avg_moving_vertices_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.movingRenderVerticesNanoseconds,
                      diagnostics.movingFrames))
                  << " avg_moving_face_total_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.movingFaceTotalNanoseconds,
                      diagnostics.movingFrames))
                  << " avg_moving_face_build_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.movingFaceBuildNanoseconds,
                      diagnostics.movingFrames))
                  << " avg_moving_upload_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.movingFaceUploadNanoseconds,
                      diagnostics.movingFrames))
                  << " avg_full_rebuild_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.fullRebuildNanoseconds,
                      diagnostics.movingFullRebuilds))
                  << " avg_mechanism_total_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.mechanismTotalNanoseconds,
                      diagnostics.simulationAdvancedFrames))
                  << " updated_faces=" << diagnostics.movingUpdatedFaces
                  << " dirty_batches=" << diagnostics.movingDirtyBatches
                  << " render_frames=" << diagnostics.renderFrames
                  << " avg_render_total_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderTotalNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_render_untracked_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      untrackedRenderNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_world_fx_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderWorldFxNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_view_setup_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderViewSetupNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_visibility_phase_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderVisibilityNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_lighting_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderLightingNanoseconds,
                      diagnostics.renderFrames))
                  << " lighting_input=" << lightingStats.inputLights
                  << " lighting_static=" << lightingStats.inputStaticLights
                  << " lighting_dynamic=" << lightingStats.inputDynamicLights
                  << " lighting_clustered_fx=" << lightingStats.clusteredFxLights
                  << " lighting_visible_sectors=" << lightingStats.visibleSectors
                  << " lighting_selection_calls=" << lightingStats.selectionCalls
                  << " lighting_candidates=" << lightingStats.candidateEvaluations
                  << " lighting_max_candidates=" << lightingStats.maxCandidatesPerSelection
                  << " lighting_selected=" << lightingStats.selectedLights
                  << " lighting_output=" << lightingStats.outputLights
                  << " lighting_tail_omitted=" << lightingStats.omittedTailLights
                  << " lighting_billboard_samples=" << lightingStats.billboardSamples
                  << " avg_lighting_build_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      lightingStats.buildFrameNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_lighting_select_us=" << nanosecondsToMicroseconds(averageLightingSelectionNanoseconds)
                  << " avg_billboard_sample_us=" << nanosecondsToMicroseconds(averageBillboardSampleNanoseconds)
                  << " avg_inspect_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderInspectNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_textured_submit_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderTexturedSubmitNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_blood_splats_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderBloodSplatsNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_decoration_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderDecorationNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_actor_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderActorNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_sprite_object_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderSpriteObjectNanoseconds,
                      diagnostics.renderFrames))
                  << " avg_particle_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderParticleNanoseconds,
                      diagnostics.renderFrames))
                  << " textured_batches=" << diagnostics.renderTexturedBatches
                  << " textured_visible=" << diagnostics.renderVisibleTexturedBatches
                  << " textured_submitted=" << diagnostics.renderSubmittedTexturedBatches
                  << " textured_culled=" << diagnostics.renderCulledTexturedBatches
                  << " sprite_dec_items=" << diagnostics.renderDecorationSpriteItems
                  << " sprite_dec_submits=" << diagnostics.renderDecorationSpriteSubmits
                  << " sprite_dec_outline_submits=" << diagnostics.renderDecorationSpriteOutlineSubmits
                  << " sprite_dec_texture_switches=" << diagnostics.renderDecorationSpriteTextureSwitches
                  << " sprite_actor_items=" << diagnostics.renderActorSpriteItems
                  << " sprite_actor_submits=" << diagnostics.renderActorSpriteSubmits
                  << " sprite_actor_outline_submits=" << diagnostics.renderActorSpriteOutlineSubmits
                  << " sprite_actor_texture_switches=" << diagnostics.renderActorSpriteTextureSwitches
                  << " sprite_obj_items=" << diagnostics.renderSpriteObjectItems
                  << " sprite_obj_projectiles=" << diagnostics.renderSpriteObjectProjectiles
                  << " sprite_obj_impacts=" << diagnostics.renderSpriteObjectImpacts
                  << " sprite_obj_submits=" << diagnostics.renderSpriteObjectSubmits
                  << " sprite_obj_batch_submits=" << diagnostics.renderSpriteObjectBatchSubmits
                  << " sprite_obj_batched=" << diagnostics.renderSpriteObjectBatchedItems
                  << " sprite_obj_unbatched=" << diagnostics.renderSpriteObjectUnbatchedItems
                  << " sprite_obj_outline_submits=" << diagnostics.renderSpriteObjectOutlineSubmits
                  << " sprite_obj_texture_switches=" << diagnostics.renderSpriteObjectTextureSwitches
                  << '\n';

        m_indoorPerformanceDiagnostics = {};
    }

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

bool IndoorRenderer::isRenderSectorVisible(int16_t sectorId, const std::vector<uint8_t> &visibleSectorMask) const
{
    if (visibleSectorMask.empty()
        || sectorId < 0
        || static_cast<size_t>(sectorId) >= visibleSectorMask.size())
    {
        return true;
    }

    return visibleSectorMask[sectorId] != 0;
}

bool IndoorRenderer::isTexturedBatchVisible(
    const TexturedBatch &batch,
    const std::vector<uint8_t> &visibleSectorMask
) const
{
    if (visibleSectorMask.empty())
    {
        return true;
    }

    bool hasKnownSector = false;

    if (batch.sectorId >= 0 && static_cast<size_t>(batch.sectorId) < visibleSectorMask.size())
    {
        hasKnownSector = true;

        if (visibleSectorMask[batch.sectorId] != 0)
        {
            return true;
        }
    }

    if (batch.backSectorId >= 0 && static_cast<size_t>(batch.backSectorId) < visibleSectorMask.size())
    {
        hasKnownSector = true;

        if (visibleSectorMask[batch.backSectorId] != 0)
        {
            return true;
        }
    }

    return !hasKnownSector;
}

bool IndoorRenderer::isCeilingFace(size_t faceIndex, const IndoorFace &face) const
{
    if (faceIndex < m_ceilingFaceMask.size())
    {
        return m_ceilingFaceMask[faceIndex] != 0;
    }

    return m_indoorMapData && indoorFaceMarkedAsCeiling(*m_indoorMapData, faceIndex, face);
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
    const bx::Vec3 viewForward = {cosYaw * cosPitch, sinYaw * cosPitch, sinPitch};
    const bx::Vec3 at = {
        m_cameraPositionX + viewForward.x,
        m_cameraPositionY + viewForward.y,
        m_cameraPositionZ + viewForward.z
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
            || !isFaceVisible(faceId, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage()))
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

    const PortalVisibilityCache &renderPortalCache = m_renderPortalVisibilityCache;

    for (const IndoorPortalVisibilityTrace &trace : renderPortalCache.portalTraces)
    {
        if (!trace.accepted || !portalFaceOnScreen(trace.faceId))
        {
            continue;
        }

        appendSectorId(trace.targetSectorId);
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
    bgfx::setViewMode(MainViewId, bgfx::ViewMode::Sequential);
    bgfx::setViewClear(MainViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x000000ffu, 1.0f, 0);

    if (!m_isRenderable)
    {
        bgfx::touch(MainViewId);
        return;
    }

    const GameSettings &settings = gameSession.gameplayScreenRuntime().settingsSnapshot();
    const bool arpgMode =
        settings.arpgModeEnabled && !gameSession.gameplayScreenState().arpgModeFirstPersonUseMode();
    m_logIndoorVisibilityDiagnostics = settings.logIndoorVisibility;
    m_logIndoorPerformanceDiagnostics = settings.performanceTrace;
    const bool collectRenderDiagnostics = m_logIndoorPerformanceDiagnostics;
    const uint64_t renderBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;

    if (collectRenderDiagnostics)
    {
        ++m_indoorPerformanceDiagnostics.renderFrames;
    }

    const bool geometryToggleHeld = input.isScancodeHeld(SDL_SCANCODE_F8);

    if (geometryToggleHeld && !m_indoorGeometryRenderingToggleHeld)
    {
        m_indoorGeometryRenderingDisabled = !m_indoorGeometryRenderingDisabled;
        std::cout << "Indoor geometry rendering "
                  << (m_indoorGeometryRenderingDisabled ? "disabled" : "enabled")
                  << " by F8\n";
    }

    m_indoorGeometryRenderingToggleHeld = geometryToggleHeld;

    const float deltaMilliseconds = deltaSeconds * 1000.0f;
    m_elapsedTime += std::max(deltaSeconds, 0.0f);

    if (allowWorldInput && m_pSceneRuntime != nullptr && !gameSession.turnBasedCombatRuntime().active())
    {
        const bool collectDiagnostics = m_logIndoorPerformanceDiagnostics;
        const uint64_t mechanismBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
        const uint64_t simulationBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
        const bool simulationAdvanced = m_pSceneRuntime->advanceSimulation(deltaMilliseconds);

        if (collectDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.simulationCalls;
            m_indoorPerformanceDiagnostics.simulationNanoseconds += SDL_GetTicksNS() - simulationBeginTickCount;
        }

        if (simulationAdvanced)
        {
            if (collectDiagnostics)
            {
                ++m_indoorPerformanceDiagnostics.simulationAdvancedFrames;
            }

            const uint64_t mechanismProbeBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
            const bool mechanismsStillMoving = hasMovingMechanism(runtimeEventRuntimeState());

            if (collectDiagnostics)
            {
                m_indoorPerformanceDiagnostics.mechanismProbeNanoseconds +=
                    SDL_GetTicksNS() - mechanismProbeBeginTickCount;
            }

            if (mechanismsStillMoving)
            {
                if (collectDiagnostics)
                {
                    ++m_indoorPerformanceDiagnostics.movingFrames;
                }

                if (!updateMovingMechanismGeometryResources() && collectDiagnostics)
                {
                    ++m_indoorPerformanceDiagnostics.movingUpdateFailures;
                }
            }
            else
            {
                const uint64_t rebuildBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
                rebuildDerivedGeometryResources();

                if (collectDiagnostics)
                {
                    ++m_indoorPerformanceDiagnostics.movingFullRebuilds;
                    ++m_indoorPerformanceDiagnostics.mechanismSettleFullRebuilds;
                    m_indoorPerformanceDiagnostics.fullRebuildNanoseconds +=
                        SDL_GetTicksNS() - rebuildBeginTickCount;
                }
            }

            if (collectDiagnostics)
            {
                m_indoorPerformanceDiagnostics.mechanismTotalNanoseconds +=
                    SDL_GetTicksNS() - mechanismBeginTickCount;
            }
        }
    }

    const uint64_t worldFxBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;

    m_worldFxSystem.setShadowsEnabled(settings.shadows);
    m_worldFxSystem.updateParticles(deltaSeconds, m_gameplayCursorMode);
    if (!m_gameplayCursorMode)
    {
        m_worldFxSystem.clearSpatialFx();
        m_worldFxSystem.syncProjectileFx(gameSession, deltaSeconds, true);
    }

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderWorldFxNanoseconds += SDL_GetTicksNS() - worldFxBeginTickCount;
    }

    const uint64_t viewSetupBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    const float cosPitch = std::cos(m_cameraPitchRadians);
    const float sinPitch = std::sin(m_cameraPitchRadians);
    const float cosYaw = std::cos(m_cameraYawRadians);
    const float sinYaw = std::sin(m_cameraYawRadians);
    bx::Vec3 viewForward = {cosYaw * cosPitch, sinYaw * cosPitch, sinPitch};
    bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
    bx::Vec3 at = {
        m_cameraPositionX + viewForward.x,
        m_cameraPositionY + viewForward.y,
        m_cameraPositionZ + viewForward.z
    };
    bx::Vec3 up = {0.0f, 0.0f, 1.0f};

    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};

    if (arpgMode && m_pSceneRuntime != nullptr)
    {
        m_arpgModeCameraActive = true;
        m_arpgModeCameraFovDegrees = settings.arpgModeCameraFovDegrees;

        if (!m_arpgModeCameraDistanceInitialized)
        {
            m_arpgModeCameraDistance = settings.arpgModeCameraDistance;
            m_arpgModeCameraDistanceInitialized = true;
        }

        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        const ArpgModeCameraFrame cameraFrame =
            buildArpgModeCameraFrame(
                ArpgModeCameraInput{
                    .target = {
                        moveState.x,
                        moveState.y,
                        moveState.footZ + settings.arpgModeCameraTargetHeight,
                    },
                    .yawRadians = degreesToRadians(settings.arpgModeCameraYawDegrees),
                    .pitchRadians = degreesToRadians(settings.arpgModeCameraPitchDegrees),
                    .distance = m_arpgModeCameraDistance,
                    .fovDegrees = settings.arpgModeCameraFovDegrees,
                    .aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight),
                    .nearClip = 0.1f,
                    .farClip = 50000.0f,
                    .homogeneousDepth = bgfx::getCaps()->homogeneousDepth,
                });

        eye = cameraFrame.eye;
        at = cameraFrame.at;
        up = cameraFrame.up;
        viewForward = cameraFrame.forward;
        std::copy(cameraFrame.viewMatrix.begin(), cameraFrame.viewMatrix.end(), viewMatrix);
        std::copy(cameraFrame.projectionMatrix.begin(), cameraFrame.projectionMatrix.end(), projectionMatrix);
        m_arpgModeViewMatrix = cameraFrame.viewMatrix;
        m_arpgModeProjectionMatrix = cameraFrame.projectionMatrix;
        m_arpgModeCameraMatricesValid = true;
        m_cameraPositionX = eye.x;
        m_cameraPositionY = eye.y;
        m_cameraPositionZ = eye.z;
        m_cameraYawRadians = degreesToRadians(settings.arpgModeCameraYawDegrees);
        m_cameraPitchRadians = degreesToRadians(settings.arpgModeCameraPitchDegrees);
    }
    else
    {
        m_arpgModeCameraActive = false;
        m_arpgModeCameraMatricesValid = false;
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
    }

    bgfx::setViewTransform(MainViewId, viewMatrix, projectionMatrix);
    bgfx::touch(MainViewId);

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderViewSetupNanoseconds += SDL_GetTicksNS() - viewSetupBeginTickCount;
    }

    const uint64_t visibilityBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    std::vector<uint8_t> cameraVisibleSectorMask;
    std::vector<uint8_t> renderVisibleSectorMask;

    if (arpgMode && m_pSceneRuntime != nullptr && m_indoorMapData)
    {
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        const uint32_t visibilityTick = SDL_GetTicks();
        const bool refreshArpgRenderVisibility =
            !m_arpgModeRenderVisibilityCacheValid
            || m_arpgModeCameraVisibleSectorMaskCache.size() != m_indoorMapData->sectors.size()
            || m_arpgModeRenderVisibleSectorMaskCache.size() != m_indoorMapData->sectors.size()
            || m_arpgModeRenderVisibilityCacheSectorId != moveState.sectorId
            || m_arpgModeRenderVisibilityCacheEyeSectorId != moveState.eyeSectorId
            || visibilityTick - m_arpgModeRenderVisibilityCacheTick >= ArpgModeIndoorRenderVisibilityRefreshMs;

        if (refreshArpgRenderVisibility)
        {
            m_arpgModeCameraVisibleSectorMaskCache = buildVisibleSectorMask(eye);
            m_arpgModeRenderVisibleSectorMaskCache =
                buildArpgModeRenderVisibleSectorMask(m_arpgModeCameraVisibleSectorMaskCache);
            m_arpgModeRenderVisibilityCacheValid = true;
            m_arpgModeRenderVisibilityCacheTick = visibilityTick;
            m_arpgModeRenderVisibilityCacheSectorId = moveState.sectorId;
            m_arpgModeRenderVisibilityCacheEyeSectorId = moveState.eyeSectorId;
        }

        cameraVisibleSectorMask = m_arpgModeCameraVisibleSectorMaskCache;
        renderVisibleSectorMask = m_arpgModeRenderVisibleSectorMaskCache;
    }
    else
    {
        cameraVisibleSectorMask = buildVisibleSectorMask(eye);
        renderVisibleSectorMask = cameraVisibleSectorMask;
        m_arpgModeRenderVisibilityCacheValid = false;
    }

    const std::vector<uint8_t> &baseVisibleSectorMask = cameraVisibleSectorMask;
    const std::vector<std::vector<IndoorVisibilityFrustum>> emptyVisibleSectorFrustums;
    const std::vector<std::vector<IndoorVisibilityFrustum>> &renderVisibleSectorFrustums =
        arpgMode ? emptyVisibleSectorFrustums : m_renderPortalVisibilityCache.visibleSectorFrustums;

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderVisibilityNanoseconds += SDL_GetTicksNS() - visibilityBeginTickCount;
    }

    LightingStats *pLightingStats =
        collectRenderDiagnostics ? &m_indoorPerformanceDiagnostics.lightingStats : nullptr;
    const uint64_t lightingBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    IndoorLightingFrameInput lightingInput = {};
    lightingInput.pMapData = m_indoorMapData ? &m_indoorMapData.value() : nullptr;
    lightingInput.pEventRuntimeState = runtimeEventRuntimeState();
    lightingInput.pDecorationBillboardSet =
        m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr;
    lightingInput.pWorldFxSystem = &m_worldFxSystem;
    lightingInput.pParty = m_pSceneRuntime != nullptr ? &m_pSceneRuntime->partyRuntime().party() : nullptr;
    lightingInput.pVisibleSectorMask = &renderVisibleSectorMask;
    lightingInput.pVisibleSectorFrustums = &renderVisibleSectorFrustums;
    lightingInput.cameraPosition = eye;
    if (arpgMode && m_pSceneRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        lightingInput.torchPosition = {moveState.x, moveState.y, moveState.eyeZ()};
        lightingInput.hasTorchPosition = true;
    }
    lightingInput.coloredLights = settings.coloredLights;
    const IndoorLightingFrame lightingFrame = m_indoorLightingRuntime.buildFrame(lightingInput);
    if (pLightingStats != nullptr)
    {
        const uint32_t dynamicLightInputCount =
            lightingFrame.sourceFxLightCount != 0
                ? lightingFrame.sourceFxLightCount
                : static_cast<uint32_t>(lightingFrame.fxLightIndices.size());
        const uint32_t staticLightInputCount =
            lightingFrame.lights.size() >= lightingFrame.fxLightIndices.size()
                ? static_cast<uint32_t>(lightingFrame.lights.size() - lightingFrame.fxLightIndices.size())
                : 0u;
        pLightingStats->buildFrameNanoseconds += SDL_GetTicksNS() - lightingBeginTickCount;
        pLightingStats->inputLights += staticLightInputCount + dynamicLightInputCount;
        pLightingStats->inputDynamicLights += dynamicLightInputCount;
        pLightingStats->inputStaticLights += staticLightInputCount;
        pLightingStats->clusteredFxLights += lightingFrame.clusteredFxLightCount;
        pLightingStats->visibleSectors += static_cast<uint32_t>(
            std::count(renderVisibleSectorMask.begin(), renderVisibleSectorMask.end(), static_cast<uint8_t>(1)));
    }

    const uint64_t defaultSelectionBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    const IndoorDrawLightSet defaultLightSet =
        IndoorLightingRuntime::selectDrawLightSetForPoint(lightingFrame, eye, viewForward, pLightingStats);
    if (pLightingStats != nullptr)
    {
        pLightingStats->selectionNanoseconds += SDL_GetTicksNS() - defaultSelectionBeginTickCount;
        pLightingStats->outputLights += static_cast<uint32_t>(defaultLightSet.lightCount);
    }

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderLightingNanoseconds += SDL_GetTicksNS() - lightingBeginTickCount;
    }

    const uint64_t inspectBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
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
                const std::vector<uint8_t> interactionVisibleSectorMask = buildVisibleSectorMask(eye);
                m_cachedInspectHit = inspectAtCursor(
                    *m_indoorMapData,
                    m_renderVertices,
                    interactionVisibleSectorMask,
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
    }

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderInspectNanoseconds += SDL_GetTicksNS() - inspectBeginTickCount;
    }

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    ++m_indoorLightingSelectionFrame;
    const auto drawLightSetForBatch =
        [&](const TexturedBatch &batch) -> IndoorDrawLightSet
        {
            IndoorLightSelectionBounds bounds = {};
            bounds.min = batch.boundsMin;
            bounds.max = batch.boundsMax;
            bounds.valid = batch.hasBounds;
            const CachedIndoorLightSelection *pCachedSelection = nullptr;
            const auto cacheIterator = m_indoorLightingSelectionCache.find(batch.stableId);

            if (cacheIterator != m_indoorLightingSelectionCache.end())
            {
                pCachedSelection = &cacheIterator->second;
            }

            const uint64_t selectionBeginTickCount = pLightingStats != nullptr ? SDL_GetTicksNS() : 0;
            IndoorDrawLightSet lightSet = IndoorLightingRuntime::selectDrawLightSetForBounds(
                lightingFrame,
                eye,
                viewForward,
                batch.sectorId,
                batch.backSectorId,
                bounds,
                pLightingStats,
                pCachedSelection != nullptr ? &pCachedSelection->history : nullptr);

            if (pLightingStats != nullptr)
            {
                pLightingStats->selectionNanoseconds += SDL_GetTicksNS() - selectionBeginTickCount;
                pLightingStats->outputLights += static_cast<uint32_t>(lightSet.lightCount);
            }

            if (batch.stableId != 0)
            {
                CachedIndoorLightSelection &cachedSelection = m_indoorLightingSelectionCache[batch.stableId];
                cachedSelection.history.lightCount = lightSet.lightCount;
                cachedSelection.lastSeenFrame = m_indoorLightingSelectionFrame;

                for (size_t index = 0; index < MaxIndoorDrawLights; ++index)
                {
                    cachedSelection.history.lightStableIds[index] =
                        index < lightSet.lightCount ? lightSet.stableIds[index] : 0u;
                }
            }

            return lightSet;
        };

    const uint64_t texturedSubmitBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    uint64_t texturedBatchCount = 0;
    uint64_t visibleTexturedBatchCount = 0;
    uint64_t submittedTexturedBatchCount = 0;
    uint64_t culledTexturedBatchCount = 0;
    constexpr float ArpgModeOccludingFaceAlpha = 0.36f;
    const bool secretFacesDetected =
        m_map.has_value()
        && m_pSceneRuntime != nullptr
        && GameMechanics::partyDetectsSecretFaces(m_pSceneRuntime->partyRuntime().party(), m_map.value());
    const std::array<float, 4> secretPulseParams = {
        secretFacesDetected ? 1.0f : 0.0f,
        m_elapsedTime,
        0.0f,
        0.0f
    };
    std::vector<std::vector<std::pair<uint32_t, uint32_t>>> arpgModeOccludingBatchRanges;
    std::function<void()> submitArpgModeTranslucentOccludingFaces = []() {};
    std::function<void(
        const TexturedBatch &,
        size_t,
        uint32_t,
        uint32_t,
        const IndoorDrawLightSet &,
        const std::array<float, 4> &,
        float,
        bool)> submitTexturedBatchRange;

    if (!m_indoorGeometryRenderingDisabled
        && bgfx::isValid(m_indoorLitProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && bgfx::isValid(m_indoorLightPositionsUniformHandle)
        && bgfx::isValid(m_indoorLightColorsUniformHandle)
        && bgfx::isValid(m_indoorLightParamsUniformHandle)
        && bgfx::isValid(m_secretPulseParamsUniformHandle)
        && bgfx::isValid(m_indoorFaceAlphaParamsUniformHandle)
        && bgfx::isValid(m_indoorSkyParamsUniformHandle)
        && bgfx::isValid(m_indoorSkyProjectionParamsUniformHandle))
    {
        std::vector<uint8_t> arpgModeOccludingFaceMask;

        if (arpgMode
            && m_indoorMapData
            && m_pSceneRuntime != nullptr
            && !m_texturedBatches.empty()
            && m_faceBatchIndices.size() == m_indoorMapData->faces.size())
        {
            arpgModeOccludingFaceMask.assign(m_indoorMapData->faces.size(), 0);
            std::vector<size_t> arpgModeDirectOccludingFaceIndices;
            const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
            m_arpgModeOcclusionGeometryCache.setAttributeOverrides(mapDeltaData ? &*mapDeltaData : nullptr);
            const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
            const std::array<bx::Vec3, 3> puppetSamples = {{
                {moveState.x, moveState.y, moveState.footZ + 72.0f},
                {moveState.x, moveState.y, moveState.footZ + 128.0f},
                {moveState.x, moveState.y, moveState.footZ + 192.0f}
            }};

            for (const bx::Vec3 &sample : puppetSamples)
            {
                const bx::Vec3 toSample = vecSubtract(sample, eye);
                const float sampleDistance = vecLength(toSample);

                if (sampleDistance <= InspectRayEpsilon)
                {
                    continue;
                }

                const bx::Vec3 rayDirection = vecScale(toSample, 1.0f / sampleDistance);
                constexpr float OcclusionBoundsPadding = 16.0f;
                const bx::Vec3 segmentMin = {
                    std::min(eye.x, sample.x) - OcclusionBoundsPadding,
                    std::min(eye.y, sample.y) - OcclusionBoundsPadding,
                    std::min(eye.z, sample.z) - OcclusionBoundsPadding
                };
                const bx::Vec3 segmentMax = {
                    std::max(eye.x, sample.x) + OcclusionBoundsPadding,
                    std::max(eye.y, sample.y) + OcclusionBoundsPadding,
                    std::max(eye.z, sample.z) + OcclusionBoundsPadding
                };

                for (const ArpgModeOccludingFaceCandidate &candidate : m_arpgModeOccludingFaceCandidates)
                {
                    const size_t faceIndex = candidate.faceIndex;

                    if (arpgModeOccludingFaceMask[faceIndex] != 0)
                    {
                        continue;
                    }

                    if ((!isRenderSectorVisible(candidate.sectorId, renderVisibleSectorMask)
                            && !isRenderSectorVisible(candidate.backSectorId, renderVisibleSectorMask))
                        || candidate.boundsMax.x < segmentMin.x
                        || candidate.boundsMin.x > segmentMax.x
                        || candidate.boundsMax.y < segmentMin.y
                        || candidate.boundsMin.y > segmentMax.y
                        || candidate.boundsMax.z < segmentMin.z
                        || candidate.boundsMin.z > segmentMax.z)
                    {
                        continue;
                    }

                    const IndoorFace &face = m_indoorMapData->faces[faceIndex];

                    if (!isFaceVisible(faceIndex, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage()))
                    {
                        continue;
                    }

                    const IndoorFaceGeometryData *pGeometry =
                        m_arpgModeOcclusionGeometryCache.geometryForFace(*m_indoorMapData, m_renderVertices, faceIndex);

                    if (pGeometry == nullptr || pGeometry->vertices.size() < 3)
                    {
                        continue;
                    }

                    for (size_t triangleIndex = 1; triangleIndex + 1 < pGeometry->vertices.size(); ++triangleIndex)
                    {
                        float distance = 0.0f;

                        if (intersectRayTriangle(
                                eye,
                                rayDirection,
                                pGeometry->vertices[0],
                                pGeometry->vertices[triangleIndex],
                                pGeometry->vertices[triangleIndex + 1],
                                distance)
                            && distance > 16.0f
                            && distance + 8.0f < sampleDistance)
                        {
                            arpgModeOccludingFaceMask[faceIndex] = 1;
                            arpgModeDirectOccludingFaceIndices.push_back(faceIndex);
                            break;
                        }
                    }
                }
            }

            for (size_t faceIndex : arpgModeDirectOccludingFaceIndices)
            {
                if (faceIndex >= m_arpgModeOccludingFaceNeighbors.size())
                {
                    continue;
                }

                for (size_t neighborFaceIndex : m_arpgModeOccludingFaceNeighbors[faceIndex])
                {
                    if (neighborFaceIndex >= arpgModeOccludingFaceMask.size()
                        || neighborFaceIndex >= m_indoorMapData->faces.size())
                    {
                        continue;
                    }

                    const IndoorFace &neighborFace = m_indoorMapData->faces[neighborFaceIndex];

                    if (indoorFaceMarkedAsFloor(*m_indoorMapData, neighborFaceIndex, neighborFace))
                    {
                        continue;
                    }

                    if (!isFaceVisible(
                            neighborFaceIndex,
                            neighborFace,
                            runtimeMapDeltaData(),
                            runtimeEventRuntimeStateStorage()))
                    {
                        continue;
                    }

                    arpgModeOccludingFaceMask[neighborFaceIndex] = 1;
                }
            }

            arpgModeOccludingBatchRanges.resize(m_texturedBatches.size());

            for (size_t faceIndex = 0; faceIndex < arpgModeOccludingFaceMask.size(); ++faceIndex)
            {
                if (arpgModeOccludingFaceMask[faceIndex] == 0
                    || faceIndex >= m_faceBatchIndices.size()
                    || faceIndex >= m_faceVertexOffsets.size()
                    || faceIndex >= m_faceVertexCounts.size())
                {
                    continue;
                }

                const int32_t batchIndex = m_faceBatchIndices[faceIndex];

                if (batchIndex < 0 || static_cast<size_t>(batchIndex) >= arpgModeOccludingBatchRanges.size())
                {
                    continue;
                }

                const uint32_t vertexCount = m_faceVertexCounts[faceIndex];

                if (vertexCount == 0)
                {
                    continue;
                }

                arpgModeOccludingBatchRanges[static_cast<size_t>(batchIndex)].push_back(
                    {m_faceVertexOffsets[faceIndex], vertexCount});
            }

            for (std::vector<std::pair<uint32_t, uint32_t>> &ranges : arpgModeOccludingBatchRanges)
            {
                std::sort(ranges.begin(), ranges.end());
            }
        }

        submitTexturedBatchRange =
            [&](const TexturedBatch &batch,
                size_t frameIndex,
                uint32_t vertexOffset,
                uint32_t vertexCount,
                const IndoorDrawLightSet &batchLightSet,
                const std::array<float, 4> &batchSecretPulseParams,
                float alpha,
                bool writeDepth)
            {
                if (vertexCount == 0)
                {
                    return;
                }

                bgfx::setTransform(modelMatrix);
                bgfx::setVertexBuffer(0, batch.vertexBufferHandle, vertexOffset, vertexCount);
                bindTexture(
                    0,
                    m_textureSamplerHandle,
                    batch.frameTextureHandles[frameIndex],
                    TextureFilterProfile::BModel);
                bgfx::setUniform(
                    m_indoorLightPositionsUniformHandle,
                    batchLightSet.positions.data(),
                    MaxIndoorShaderLights);
                bgfx::setUniform(
                    m_indoorLightColorsUniformHandle,
                    batchLightSet.colors.data(),
                    MaxIndoorShaderLights);
                bgfx::setUniform(m_indoorLightParamsUniformHandle, batchLightSet.params.data());
                bgfx::setUniform(m_secretPulseParamsUniformHandle, batchSecretPulseParams.data());
                const std::array<float, 4> faceAlphaParams = {alpha, 0.0f, 0.0f, 0.0f};
                bgfx::setUniform(m_indoorFaceAlphaParamsUniformHandle, faceAlphaParams.data());
                const std::array<float, 4> indoorSkyParams = {
                    batchSecretPulseParams[2],
                    batchSecretPulseParams[3],
                    m_cameraYawRadians,
                    m_cameraPitchRadians
                };
                bgfx::setUniform(m_indoorSkyParamsUniformHandle, indoorSkyParams.data());
                const float viewPlaneDistancePixels =
                    (static_cast<float>(viewHeight) * 0.5f)
                    / std::tan((IndoorCameraVerticalFovDegrees * Pi / 180.0f) * 0.5f);
                const float horizonHeightOffset =
                    (viewPlaneDistancePixels * eye.z)
                    / (viewPlaneDistancePixels + IndoorSkyProjectionFarClipDistance)
                    + static_cast<float>(viewHeight) * 0.5f;
                const std::array<float, 4> indoorSkyProjectionParams = {
                    static_cast<float>(viewWidth) * 0.5f,
                    horizonHeightOffset,
                    1.0f / viewPlaneDistancePixels,
                    IndoorSkyProjectionPitchOffsetRadians
                };
                bgfx::setUniform(m_indoorSkyProjectionParamsUniformHandle, indoorSkyProjectionParams.data());

                uint64_t state =
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_DEPTH_TEST_LEQUAL;

                if (writeDepth)
                {
                    state |= BGFX_STATE_WRITE_Z;
                }

                if (alpha < 0.999f)
                {
                    state |= BGFX_STATE_BLEND_ALPHA;
                }

                bgfx::setState(state);
                bgfx::submit(MainViewId, m_indoorLitProgramHandle);
            };

        for (size_t batchIndex = 0; batchIndex < m_texturedBatches.size(); ++batchIndex)
        {
            const TexturedBatch &batch = m_texturedBatches[batchIndex];
            ++texturedBatchCount;

            if (arpgMode && batch.ceiling)
            {
                ++culledTexturedBatchCount;
                continue;
            }

            if (!isTexturedBatchVisible(batch, renderVisibleSectorMask))
            {
                ++culledTexturedBatchCount;
                continue;
            }

            ++visibleTexturedBatchCount;

            if (!bgfx::isValid(batch.vertexBufferHandle) || batch.frameTextureHandles.empty() || batch.vertexCount == 0)
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

            const IndoorDrawLightSet batchLightSet = drawLightSetForBatch(batch);
            std::array<float, 4> batchSecretPulseParams = secretPulseParams;

            if (batch.textureWidth > 0 && batch.textureHeight > 0)
            {
                batchSecretPulseParams[2] =
                    -eye.x * 0.25f / static_cast<float>(batch.textureWidth);
                batchSecretPulseParams[3] =
                    eye.y * 0.25f / static_cast<float>(batch.textureHeight);
            }

            const std::vector<std::pair<uint32_t, uint32_t>> *pOccludingRanges =
                batchIndex < arpgModeOccludingBatchRanges.size()
                    ? &arpgModeOccludingBatchRanges[batchIndex]
                    : nullptr;

            if (pOccludingRanges == nullptr || pOccludingRanges->empty())
            {
                submitTexturedBatchRange(
                    batch,
                    frameIndex,
                    0,
                    batch.vertexCount,
                    batchLightSet,
                    batchSecretPulseParams,
                    1.0f,
                    true);
            }
            else
            {
                uint32_t cursor = 0;

                for (const std::pair<uint32_t, uint32_t> &range : *pOccludingRanges)
                {
                    const uint32_t rangeBegin = std::min(range.first, batch.vertexCount);
                    const uint32_t rangeEnd = std::min(range.first + range.second, batch.vertexCount);

                    if (cursor < rangeBegin)
                    {
                        submitTexturedBatchRange(
                            batch,
                            frameIndex,
                            cursor,
                            rangeBegin - cursor,
                            batchLightSet,
                            batchSecretPulseParams,
                            1.0f,
                            true);
                    }

                    cursor = std::max(cursor, rangeEnd);
                }

                if (cursor < batch.vertexCount)
                {
                    submitTexturedBatchRange(
                        batch,
                        frameIndex,
                        cursor,
                        batch.vertexCount - cursor,
                        batchLightSet,
                        batchSecretPulseParams,
                        1.0f,
                        true);
                }
            }

            ++submittedTexturedBatchCount;
        }

        submitArpgModeTranslucentOccludingFaces =
            [&]()
            {
                for (size_t batchIndex = 0; batchIndex < arpgModeOccludingBatchRanges.size(); ++batchIndex)
                {
                    const std::vector<std::pair<uint32_t, uint32_t>> &ranges =
                        arpgModeOccludingBatchRanges[batchIndex];

                    if (ranges.empty() || batchIndex >= m_texturedBatches.size())
                    {
                        continue;
                    }

                    const TexturedBatch &batch = m_texturedBatches[batchIndex];

                    if (!isTexturedBatchVisible(batch, renderVisibleSectorMask)
                        || !bgfx::isValid(batch.vertexBufferHandle)
                        || batch.frameTextureHandles.empty()
                        || batch.vertexCount == 0)
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

                    const IndoorDrawLightSet batchLightSet = drawLightSetForBatch(batch);
                    std::array<float, 4> batchSecretPulseParams = secretPulseParams;

                    if (batch.textureWidth > 0 && batch.textureHeight > 0)
                    {
                        batchSecretPulseParams[2] =
                            -eye.x * 0.25f / static_cast<float>(batch.textureWidth);
                        batchSecretPulseParams[3] =
                            eye.y * 0.25f / static_cast<float>(batch.textureHeight);
                    }

                    for (const std::pair<uint32_t, uint32_t> &range : ranges)
                    {
                        if (range.first >= batch.vertexCount)
                        {
                            continue;
                        }

                        submitTexturedBatchRange(
                            batch,
                            frameIndex,
                            range.first,
                            std::min(range.second, batch.vertexCount - range.first),
                            batchLightSet,
                            batchSecretPulseParams,
                            ArpgModeOccludingFaceAlpha,
                            false);
                    }
                }
            };

        for (std::unordered_map<uint32_t, CachedIndoorLightSelection>::iterator it =
                m_indoorLightingSelectionCache.begin();
            it != m_indoorLightingSelectionCache.end();)
        {
            if (m_indoorLightingSelectionFrame - it->second.lastSeenFrame > IndoorLightSelectionCacheMaxAgeFrames)
            {
                it = m_indoorLightingSelectionCache.erase(it);
            }
            else
            {
                ++it;
            }
        }
    }

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderTexturedSubmitNanoseconds +=
            SDL_GetTicksNS() - texturedSubmitBeginTickCount;
        m_indoorPerformanceDiagnostics.renderTexturedBatches += texturedBatchCount;
        m_indoorPerformanceDiagnostics.renderVisibleTexturedBatches += visibleTexturedBatchCount;
        m_indoorPerformanceDiagnostics.renderSubmittedTexturedBatches += submittedTexturedBatchCount;
        m_indoorPerformanceDiagnostics.renderCulledTexturedBatches += culledTexturedBatchCount;
    }

    const uint64_t bloodSplatsBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;

    if (!m_indoorGeometryRenderingDisabled && settings.bloodSplats)
    {
        renderBloodSplats(
            MainViewId,
            defaultLightSet);
    }

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderBloodSplatsNanoseconds += SDL_GetTicksNS() - bloodSplatsBeginTickCount;
    }

    const GameplayContextActionState *pContextActionState = nullptr;
    if (settings.contextActionPopup)
    {
        pContextActionState = &gameSession.gameplayScreenRuntime().contextActionStateReadOnly();
    }
    renderContextActionGeometryHighlight(MainViewId, pContextActionState, arpgMode);

    const uint64_t decorationBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    renderDecorationBillboards(
        MainViewId,
        viewMatrix,
        eye,
        renderVisibleSectorMask,
        renderVisibleSectorFrustums,
        lightingFrame,
        pContextActionState,
        pLightingStats);

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderDecorationNanoseconds += SDL_GetTicksNS() - decorationBeginTickCount;
    }

    const uint64_t spriteObjectBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    renderSpriteObjectBillboards(
        MainViewId,
        viewMatrix,
        eye,
        renderVisibleSectorMask,
        renderVisibleSectorFrustums,
        lightingFrame,
        settings.spriteOutline,
        pContextActionState,
        pLightingStats);

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderSpriteObjectNanoseconds +=
            SDL_GetTicksNS() - spriteObjectBeginTickCount;
    }

    const uint64_t actorBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    renderActorPreviewBillboards(
        MainViewId,
        viewMatrix,
        eye,
        renderVisibleSectorMask,
        renderVisibleSectorFrustums,
        lightingFrame,
        settings.spriteOutline,
        pContextActionState,
        arpgMode ? &settings : nullptr,
        pLightingStats);

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderActorNanoseconds += SDL_GetTicksNS() - actorBeginTickCount;
    }

    submitArpgModeTranslucentOccludingFaces();

    const uint64_t particlesBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    ParticleRenderer::renderBeams(
        m_worldFxRenderResources,
        m_worldFxSystem.beams(),
        MainViewId,
        viewMatrix,
        eye);
    ParticleRenderer::renderParticles(
        m_worldFxRenderResources,
        m_worldFxSystem.particles(),
        MainViewId,
        viewMatrix,
        eye,
        static_cast<float>(viewWidth) / static_cast<float>(viewHeight));

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderParticleNanoseconds += SDL_GetTicksNS() - particlesBeginTickCount;
        m_indoorPerformanceDiagnostics.renderTotalNanoseconds += SDL_GetTicksNS() - renderBeginTickCount;

        if (m_logIndoorVisibilityDiagnostics || m_logIndoorPerformanceDiagnostics)
        {
            logIndoorVisibilityDiagnostics(baseVisibleSectorMask, renderVisibleSectorMask, SDL_GetTicks());
        }
    }
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
    pVertices[0] = {x, y, 0.0f, u0, v0, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    pVertices[1] = {x + quadWidth, y, 0.0f, u1, v0, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    pVertices[2] = {x + quadWidth, y + quadHeight, 0.0f, u1, v1, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    pVertices[3] = {x, y + quadHeight, 0.0f, u0, v1, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};

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
    const bx::Vec3 eye = {
        m_cameraPositionX,
        m_cameraPositionY,
        m_cameraPositionZ
    };
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};

    if (m_arpgModeCameraActive && m_arpgModeCameraMatricesValid)
    {
        std::copy(m_arpgModeViewMatrix.begin(), m_arpgModeViewMatrix.end(), viewMatrix);
        std::copy(m_arpgModeProjectionMatrix.begin(), m_arpgModeProjectionMatrix.end(), projectionMatrix);
    }
    else
    {
        const float cosPitch = std::cos(m_cameraPitchRadians);
        const float sinPitch = std::sin(m_cameraPitchRadians);
        const float cosYaw = std::cos(m_cameraYawRadians);
        const float sinYaw = std::sin(m_cameraYawRadians);
        const bx::Vec3 at = {
            m_cameraPositionX + cosYaw * cosPitch,
            m_cameraPositionY + sinYaw * cosPitch,
            m_cameraPositionZ + sinPitch
        };
        const bx::Vec3 up = {0.0f, 0.0f, 1.0f};

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
    }

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
            worldItemHit.displayName = inspectHit.name;
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
    const std::optional<std::string> eventTargetStatusText = resolveEventTargetHoverStatusText(inspectHit);
    eventTargetHit.name =
        eventTargetStatusText && !eventTargetStatusText->empty() ? *eventTargetStatusText : inspectHit.name;
    eventTargetHit.hitPoint = hitPoint;
    eventTargetHit.distance = inspectHit.distance;
    const uint16_t eventId = inspectHitEventId(inspectHit);
    const bool allowGlobalEventMetadata = inspectHit.kind == "entity";
    eventTargetHit.openedChestIds =
        resolveIndoorOpenedChestIds(m_pSceneRuntime, eventId, allowGlobalEventMetadata);
    eventTargetHit.contextActionMetadata =
        resolveIndoorContextActionMetadata(m_pSceneRuntime, eventId, allowGlobalEventMetadata);
    eventTargetHit.hintOnlyEvent = indoorEventIsHintOnly(m_pSceneRuntime, eventId, allowGlobalEventMetadata);

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
        eventTargetHit.targetKind = GameplayWorldEventTargetKind::Mechanism;
        eventTargetHit.triggeredEventId = inspectHit.mechanismLinkedEventId;
        eventTargetHit.secondaryIndex = inspectHit.mechanismFaceIndex;
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

uint16_t IndoorRenderer::inspectHitEventId(const InspectHit &inspectHit) const
{
    if (inspectHit.kind == "entity")
    {
        const uint16_t directEventId = resolveIndoorEntityScriptEventId(inspectHit.eventIdSecondary);

        if (directEventId != 0)
        {
            return directEventId;
        }

        const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

        if (!m_indoorMapData || pEventRuntimeState == nullptr)
        {
            return 0;
        }

        const std::optional<IndoorInteractiveDecorationBinding> binding =
            resolveIndoorInteractiveDecorationBinding(
                m_indoorInteractiveDecorationDecorVarIndicesByEntity,
                m_indoorInteractiveDecorationBaseEventIdsByEntity,
                m_indoorInteractiveDecorationEventCountsByEntity,
                m_indoorInteractiveDecorationHideWhenClearedByEntity,
                inspectHit.index);

        if (!binding)
        {
            return 0;
        }

        const std::optional<uint16_t> eventId =
            resolveIndoorInteractiveDecorationEventId(*pEventRuntimeState, *binding);

        return eventId.value_or(0);
    }

    if (inspectHit.kind == "face")
    {
        return inspectHit.cogTriggered;
    }

    if (inspectHit.kind == "mechanism")
    {
        return inspectHit.mechanismLinkedEventId;
    }

    return 0;
}

std::optional<std::string> IndoorRenderer::resolveEntityDecorationHoverStatusText(
    const InspectHit &inspectHit) const
{
    if (inspectHit.kind != "entity" || !m_indoorDecorationBillboardSet)
    {
        return std::nullopt;
    }

    const DecorationEntry *pDecoration =
        m_indoorDecorationBillboardSet->decorationTable.get(inspectHit.decorationListId);

    if ((pDecoration == nullptr || pDecoration->hint.empty()) && !inspectHit.name.empty())
    {
        pDecoration = m_indoorDecorationBillboardSet->decorationTable.findByInternalName(inspectHit.name);
    }

    if (pDecoration != nullptr && !pDecoration->hint.empty())
    {
        return pDecoration->hint;
    }

    return std::nullopt;
}

std::optional<std::string> IndoorRenderer::resolveEventTargetHoverStatusText(const InspectHit &inspectHit) const
{
    if (inspectHit.kind == "entity")
    {
        const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

        if (pEventRuntimeState != nullptr)
        {
            const std::optional<IndoorInteractiveDecorationBinding> binding =
                resolveIndoorInteractiveDecorationBinding(
                    m_indoorInteractiveDecorationDecorVarIndicesByEntity,
                    m_indoorInteractiveDecorationBaseEventIdsByEntity,
                    m_indoorInteractiveDecorationEventCountsByEntity,
                    m_indoorInteractiveDecorationHideWhenClearedByEntity,
                    inspectHit.index);

            if (binding)
            {
                const std::optional<uint16_t> eventId =
                    resolveIndoorInteractiveDecorationEventId(*pEventRuntimeState, *binding);

                if (eventId)
                {
                    const std::optional<std::string> eventHint =
                        resolveIndoorGlobalEventHintText(m_pSceneRuntime, *eventId);

                    if (eventHint && !eventHint->empty())
                    {
                        return eventHint;
                    }
                }
            }
        }

        const uint16_t directEventId = resolveIndoorEntityScriptEventId(inspectHit.eventIdSecondary);

        if (directEventId != 0)
        {
            const std::optional<std::string> directHint =
                resolveIndoorLocalEventHintText(m_pSceneRuntime, directEventId);

            if (directHint && !directHint->empty())
            {
                return directHint;
            }
        }

        const std::optional<std::string> decorationHint =
            resolveEntityDecorationHoverStatusText(inspectHit);

        if (decorationHint && !decorationHint->empty())
        {
            return decorationHint;
        }
    }

    return resolveIndoorLocalEventHintText(m_pSceneRuntime, inspectHitEventId(inspectHit));
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
                    || indoorFaceMarkedAsCeiling(*m_indoorMapData, faceIndex, face)
                    || hasFaceAttribute(face.attributes, FaceAttribute::IsPortal)
                    || !isFaceVisible(faceIndex, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage())
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
        [&](const bx::Vec3 &worldPoint, GameplayWorldHit worldHit, float screenRadius)
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

            if (screenRadius >= 0.0f && screenDistance > screenRadius)
            {
                return;
            }

            const float worldDistance = vecLength(vecSubtract(worldPoint, rayRequest.eye));

            candidates.push_back(KeyboardCandidate{
                .screenX = projected.x,
                .screenY = projected.y,
                .score = screenDistance * 4.0f + worldDistance,
                .hasWorldHit = true,
                .worldHit = worldHit,
            });
        };

    const auto eventWorldHit =
        [&](const InspectHit &inspectHit, const bx::Vec3 &hitPoint) -> GameplayWorldHit
        {
            GameplayWorldHit hit = {};

            if (!inspectHit.hasHit)
            {
                return hit;
            }

            const uint16_t eventId = inspectHitEventId(inspectHit);
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
            const std::optional<std::string> eventTargetStatusText = resolveEventTargetHoverStatusText(inspectHit);
            eventTargetHit.name =
                eventTargetStatusText && !eventTargetStatusText->empty() ? *eventTargetStatusText : inspectHit.name;
            eventTargetHit.hitPoint = hitPoint;
            eventTargetHit.distance = vecLength(vecSubtract(hitPoint, rayRequest.eye));
            eventTargetHit.openedChestIds = resolveIndoorOpenedChestIds(m_pSceneRuntime, eventId);
            eventTargetHit.contextActionMetadata = resolveIndoorContextActionMetadata(m_pSceneRuntime, eventId);
            eventTargetHit.hintOnlyEvent = indoorEventIsHintOnly(m_pSceneRuntime, eventId);

            if (inspectHit.kind == "face")
            {
                eventTargetHit.targetKind = GameplayWorldEventTargetKind::Surface;
                eventTargetHit.secondaryIndex = inspectHit.index;
            }
            else if (inspectHit.kind == "entity")
            {
                eventTargetHit.targetKind = GameplayWorldEventTargetKind::Entity;
            }
            else if (inspectHit.kind == "mechanism")
            {
                eventTargetHit.targetKind = GameplayWorldEventTargetKind::Mechanism;
                eventTargetHit.triggeredEventId = inspectHit.mechanismLinkedEventId;
                eventTargetHit.secondaryIndex = inspectHit.mechanismFaceIndex;
            }
            else
            {
                return hit;
            }

            hit.hasHit = true;
            hit.kind = GameplayWorldHitKind::EventTarget;
            hit.eventTarget = eventTargetHit;
            return hit;
        };

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

    if (mapDeltaData
        && m_monsterTable
        && m_indoorActorPreviewBillboardSet
        && !rayRequest.ignoreActors)
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
            appendProjectedWorldHitCandidate(hitPoint, worldHit, -1.0f);
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
            worldItemHit.displayName = object.objectName;
            worldItemHit.objectDescriptionId = object.objectDescriptionId;
            worldItemHit.objectSpriteId = object.objectSpriteId;
            worldItemHit.hitPoint = hitPoint;
            worldItemHit.distance = vecLength(vecSubtract(hitPoint, rayRequest.eye));

            GameplayWorldHit worldHit = {};
            worldHit.hasHit = true;
            worldHit.kind = GameplayWorldHitKind::WorldItem;
            worldHit.worldItem = worldItemHit;
            appendProjectedWorldHitCandidate(hitPoint, worldHit, -1.0f);
        }
    }

    for (size_t faceIndex = 0; faceIndex < m_indoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_indoorMapData->faces[faceIndex];

        if (face.vertexIndices.empty()
            || (face.cogTriggered == 0 && face.cogNumber == 0)
            || isCeilingFace(faceIndex, face)
            || !indoorFaceHasActualEvent(m_pSceneRuntime, face)
            || !isFaceVisible(faceIndex, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage())
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

        const std::optional<std::string> faceHint =
            resolveIndoorLocalEventHintText(m_pSceneRuntime, face.cogTriggered);
        const std::optional<GameplayEventTargetContextActionMetadata> metadata =
            resolveIndoorContextActionMetadata(m_pSceneRuntime, face.cogTriggered, false);
        const std::vector<uint32_t> openedChestIds =
            resolveIndoorOpenedChestIds(m_pSceneRuntime, face.cogTriggered, false);

        GameplayEventTargetHit eventTargetHit = {};
        eventTargetHit.targetKind = GameplayWorldEventTargetKind::Surface;
        eventTargetHit.targetIndex = faceIndex;
        eventTargetHit.secondaryIndex = faceIndex;
        eventTargetHit.triggeredEventId = face.cogTriggered;
        eventTargetHit.trigger = face.cogTriggerType;
        eventTargetHit.attributes =
            mapDeltaData && faceIndex < mapDeltaData->faceAttributes.size()
                ? mapDeltaData->faceAttributes[faceIndex]
                : face.attributes;
        eventTargetHit.name = faceHint.value_or("");
        eventTargetHit.openedChestIds = openedChestIds;
        eventTargetHit.contextActionMetadata = metadata;
        eventTargetHit.hintOnlyEvent = indoorEventIsHintOnly(m_pSceneRuntime, face.cogTriggered, false);
        eventTargetHit.hitPoint = center;
        eventTargetHit.distance = vecLength(vecSubtract(center, rayRequest.eye));

        GameplayWorldHit worldHit = {};
        worldHit.hasHit = true;
        worldHit.kind = GameplayWorldHitKind::EventTarget;
        worldHit.eventTarget = eventTargetHit;

        if (indoorFaceSuppressedForArpgContextAction(
                *m_indoorMapData,
                faceIndex,
                face,
                eventTargetHit.contextActionMetadata,
                eventTargetHit.openedChestIds))
        {
            continue;
        }

        appendProjectedWorldHitCandidate(center, worldHit, KeyboardEventFaceScreenRadius);
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
                || doorIndex >= m_mechanismBindings.size()
                || m_mechanismBindings[doorIndex].linkedEventId == 0)
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

            size_t mechanismFaceIndex = GameplayInvalidWorldIndex;

            for (uint16_t faceId : door.faceIds)
            {
                if (faceId >= m_indoorMapData->faces.size())
                {
                    continue;
                }

                const IndoorFace &face = m_indoorMapData->faces[faceId];

                if (indoorFaceHasActualEvent(m_pSceneRuntime, face)
                    && isFaceVisible(faceId, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage()))
                {
                    mechanismFaceIndex = faceId;
                    break;
                }
            }

            const MechanismBinding &binding = m_mechanismBindings[doorIndex];
            GameplayEventTargetHit eventTargetHit = {};
            eventTargetHit.targetKind = GameplayWorldEventTargetKind::Mechanism;
            eventTargetHit.targetIndex = doorIndex;
            eventTargetHit.secondaryIndex = mechanismFaceIndex;
            eventTargetHit.triggeredEventId = binding.linkedEventId;
            eventTargetHit.name = binding.linkedEventSummary;
            eventTargetHit.hitPoint = center;
            eventTargetHit.distance = vecLength(vecSubtract(center, rayRequest.eye));
            eventTargetHit.contextActionMetadata =
                resolveIndoorContextActionMetadata(m_pSceneRuntime, binding.linkedEventId, false);
            eventTargetHit.hintOnlyEvent = indoorEventIsHintOnly(m_pSceneRuntime, binding.linkedEventId, false);

            GameplayWorldHit worldHit = {};
            worldHit.hasHit = true;
            worldHit.kind = GameplayWorldHitKind::EventTarget;
            worldHit.eventTarget = eventTargetHit;
            appendProjectedWorldHitCandidate(center, worldHit, KeyboardEventFaceScreenRadius);
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

        GameplayWorldPickRequest candidateRequest =
            buildGameplayWorldPickRequest(
                GameplayWorldPickRequestInput{
                    .screenX = candidate.screenX,
                    .screenY = candidate.screenY,
                    .screenWidth = rayRequest.viewWidth,
                    .screenHeight = rayRequest.viewHeight,
                    .includeRay = true,
                });
        candidateRequest.ignoreActors = rayRequest.ignoreActors;
        const GameplayWorldHit candidateHit = pickGameplayWorldHit(candidateRequest);

        if (isSelectableHit(candidateHit))
        {
            return candidateHit;
        }
    }

    return directHit;
}

GameplayWorldHit IndoorRenderer::pickForwardGameplayWorldHit(float depth) const
{
    if (!m_isInitialized
        || !m_isRenderable
        || !m_indoorMapData
        || m_pSceneRuntime == nullptr)
    {
        return {};
    }

    const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
    const float yawRadians = arpgModeGameplayYawRadians();
    const bx::Vec3 rayDirection = vecNormalize({std::cos(yawRadians), std::sin(yawRadians), 0.0f});

    if (vecLength(rayDirection) <= InspectRayEpsilon)
    {
        return {};
    }

    const bx::Vec3 rayOrigin = {moveState.x, moveState.y, moveState.eyeZ()};
    const bx::Vec3 at = {
        rayOrigin.x + rayDirection.x,
        rayOrigin.y + rayDirection.y,
        rayOrigin.z + rayDirection.z
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    const int viewWidth = m_lastRenderWidth > 0 ? m_lastRenderWidth : 1280;
    const int viewHeight = m_lastRenderHeight > 0 ? m_lastRenderHeight : 720;
    const float aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};

    bx::mtxLookAt(viewMatrix, rayOrigin, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        60.0f,
        aspectRatio,
        0.1f,
        50000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right);

    GameplayWorldPickRequest request = {};
    request.screenX = static_cast<float>(viewWidth) * 0.5f;
    request.screenY = static_cast<float>(viewHeight) * 0.5f;
    request.viewWidth = viewWidth;
    request.viewHeight = viewHeight;
    request.eye = rayOrigin;
    request.rayOrigin = rayOrigin;
    request.rayDirection = rayDirection;
    request.hasRay = true;
    std::copy(std::begin(viewMatrix), std::end(viewMatrix), request.viewMatrix.begin());
    std::copy(std::begin(projectionMatrix), std::end(projectionMatrix), request.projectionMatrix.begin());

    GameplayWorldHit hit = pickKeyboardGameplayWorldHit(request);

    if (!hit.hasHit || depth <= 0.0f)
    {
        return hit;
    }

    std::optional<bx::Vec3> hitPoint;

    if (hit.actor)
    {
        hitPoint = hit.actor->hitPoint;
    }
    else if (hit.worldItem)
    {
        hitPoint = hit.worldItem->hitPoint;
    }
    else if (hit.eventTarget)
    {
        hitPoint = hit.eventTarget->hitPoint;
    }
    else if (hit.object)
    {
        hitPoint = hit.object->hitPoint;
    }
    else if (hit.ground && hit.ground->isValid)
    {
        hitPoint = hit.ground->worldPoint;
    }

    if (!hitPoint)
    {
        return {};
    }

    const bx::Vec3 partyPoint = {moveState.x, moveState.y, moveState.footZ};
    const bx::Vec3 delta = vecSubtract(*hitPoint, partyPoint);
    const float distanceSquared = delta.x * delta.x + delta.y * delta.y + delta.z * delta.z;

    if (distanceSquared > depth * depth)
    {
        return {};
    }

    return hit;
}

bool IndoorRenderer::arpgModeGameplayWorldHitHasLineOfSight(const GameplayWorldHit &hit) const
{
    if (!m_isInitialized
        || !m_isRenderable
        || !m_indoorMapData
        || m_pSceneRuntime == nullptr
        || !hit.hasHit)
    {
        return false;
    }

    std::optional<bx::Vec3> hitPoint;

    if (hit.actor)
    {
        hitPoint = hit.actor->hitPoint;
    }
    else if (hit.worldItem)
    {
        hitPoint = hit.worldItem->hitPoint;
    }
    else if (hit.eventTarget)
    {
        hitPoint = hit.eventTarget->hitPoint;
    }
    else if (hit.object)
    {
        hitPoint = hit.object->hitPoint;
    }
    else if (hit.ground && hit.ground->isValid)
    {
        hitPoint = hit.ground->worldPoint;
    }

    if (!hitPoint)
    {
        return false;
    }

    std::vector<uint8_t> ignoredFaces(m_indoorMapData->faces.size(), 0);

    if (hit.eventTarget)
    {
        const GameplayEventTargetHit &eventTarget = *hit.eventTarget;

        if (eventTarget.targetKind == GameplayWorldEventTargetKind::Surface)
        {
            const size_t faceIndex =
                eventTarget.secondaryIndex != GameplayInvalidWorldIndex
                    ? eventTarget.secondaryIndex
                    : eventTarget.targetIndex;

            if (faceIndex < ignoredFaces.size())
            {
                ignoredFaces[faceIndex] = 1;
            }
        }
        else if (eventTarget.targetKind == GameplayWorldEventTargetKind::Mechanism)
        {
            const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
            const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
            const int16_t partySectorId = moveState.eyeSectorId >= 0 ? moveState.eyeSectorId : moveState.sectorId;

            if (eventTarget.secondaryIndex != GameplayInvalidWorldIndex)
            {
                if (eventTarget.secondaryIndex >= m_indoorMapData->faces.size()
                    || !indoorFaceTouchesSector(m_indoorMapData->faces[eventTarget.secondaryIndex], partySectorId))
                {
                    return false;
                }

                if (eventTarget.secondaryIndex < ignoredFaces.size())
                {
                    ignoredFaces[eventTarget.secondaryIndex] = 1;
                }
            }
            else if (mapDeltaData && eventTarget.targetIndex < mapDeltaData->doors.size())
            {
                bool doorTouchesPartySector = false;

                for (uint16_t faceId : mapDeltaData->doors[eventTarget.targetIndex].faceIds)
                {
                    if (faceId < m_indoorMapData->faces.size()
                        && indoorFaceTouchesSector(m_indoorMapData->faces[faceId], partySectorId))
                    {
                        doorTouchesPartySector = true;
                    }

                    if (faceId < ignoredFaces.size())
                    {
                        ignoredFaces[faceId] = 1;
                    }
                }

                if (!doorTouchesPartySector)
                {
                    return false;
                }
            }
        }
    }

    const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
    const bx::Vec3 rayOrigin = {moveState.x, moveState.y, moveState.eyeZ()};
    const bx::Vec3 toPoint = vecSubtract(*hitPoint, rayOrigin);
    const float pointDistance = vecLength(toPoint);

    if (pointDistance <= InspectRayEpsilon)
    {
        return true;
    }

    const bx::Vec3 rayDirection = vecScale(toPoint, 1.0f / pointDistance);
    const std::vector<uint8_t> visibleSectorMask = buildVisibleSectorMask(rayOrigin);

    for (size_t faceIndex = 0; faceIndex < m_indoorMapData->faces.size(); ++faceIndex)
    {
        if (ignoredFaces[faceIndex] != 0)
        {
            continue;
        }

        const IndoorFace &face = m_indoorMapData->faces[faceIndex];

        if (face.vertexIndices.size() < 3
            || face.isPortal
            || isCeilingFace(faceIndex, face)
            || hasFaceAttribute(face.attributes, FaceAttribute::IsPortal)
            || !isFaceVisible(faceIndex, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage())
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
                    rayOrigin,
                    rayDirection,
                    triangleVertices[0],
                    triangleVertices[1],
                    triangleVertices[2],
                    distance)
                && distance > InspectRayEpsilon
                && distance + 1.0f < pointDistance)
            {
                return false;
            }
        }
    }

    return true;
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
        payload.worldHit = translateInspectHitToGameplayWorldHit(*inspectHit, pickRequest);
        payload.eventTargetStatusText = resolveEventTargetHoverStatusText(*inspectHit);
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
    payload.eventTargetStatusText = resolveEventTargetHoverStatusText(m_cachedInspectHit);
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

    if (m_arpgModeCameraActive && m_pSceneRuntime != nullptr)
    {
        const float planeZ = m_pSceneRuntime->worldRuntime().partyFootZ() + 96.0f;

        if (std::fabs(request.rayDirection.z) > InspectRayEpsilon)
        {
            const float planeDistance = (planeZ - request.rayOrigin.z) / request.rayDirection.z;

            if (planeDistance > InspectRayEpsilon)
            {
                return bx::Vec3{
                    request.rayOrigin.x + request.rayDirection.x * planeDistance,
                    request.rayOrigin.y + request.rayDirection.y * planeDistance,
                    planeZ
                };
            }
        }

        const float horizontalLengthSquared =
            request.rayDirection.x * request.rayDirection.x + request.rayDirection.y * request.rayDirection.y;

        if (horizontalLengthSquared > InspectRayEpsilon * InspectRayEpsilon)
        {
            const float horizontalLength = std::sqrt(horizontalLengthSquared);
            constexpr float ForwardFallbackDistance = 4096.0f;
            return bx::Vec3{
                request.rayOrigin.x + request.rayDirection.x / horizontalLength * ForwardFallbackDistance,
                request.rayOrigin.y + request.rayDirection.y / horizontalLength * ForwardFallbackDistance,
                planeZ
            };
        }
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

std::optional<bx::Vec3> IndoorRenderer::gameplayCursorPlaneTargetPoint(
    float screenX,
    float screenY,
    float planeZ,
    float fallbackDistance) const
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

    if (std::fabs(request.rayDirection.z) > InspectRayEpsilon)
    {
        const float planeDistance = (planeZ - request.rayOrigin.z) / request.rayDirection.z;

        if (planeDistance > InspectRayEpsilon)
        {
            return bx::Vec3{
                request.rayOrigin.x + request.rayDirection.x * planeDistance,
                request.rayOrigin.y + request.rayDirection.y * planeDistance,
                planeZ
            };
        }
    }

    const float horizontalLengthSquared =
        request.rayDirection.x * request.rayDirection.x + request.rayDirection.y * request.rayDirection.y;

    if (horizontalLengthSquared <= InspectRayEpsilon * InspectRayEpsilon)
    {
        return std::nullopt;
    }

    const float horizontalLength = std::sqrt(horizontalLengthSquared);
    return bx::Vec3{
        request.rayOrigin.x + request.rayDirection.x / horizontalLength * fallbackDistance,
        request.rayOrigin.y + request.rayDirection.y / horizontalLength * fallbackDistance,
        planeZ
    };
}

bool IndoorRenderer::projectArpgModeWorldPointToScreen(
    const bx::Vec3 &worldPoint,
    int width,
    int height,
    float &screenX,
    float &screenY) const
{
    if (!m_arpgModeCameraActive || !m_arpgModeCameraMatricesValid || width <= 0 || height <= 0)
    {
        return false;
    }

    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, m_arpgModeViewMatrix.data(), m_arpgModeProjectionMatrix.data());

    ProjectedPoint projected = {};

    if (!projectWorldPointToScreen(worldPoint, width, height, viewProjectionMatrix, projected))
    {
        return false;
    }

    screenX = projected.x;
    screenY = projected.y;
    return true;
}

GameplayWorldHit IndoorRenderer::pickNearbyGameplayWorldHit(float radius) const
{
    if (!m_isInitialized || !m_isRenderable || !m_indoorMapData || m_pSceneRuntime == nullptr || radius <= 0.0f)
    {
        return {};
    }

    const IndoorWorldRuntime &worldRuntime = m_pSceneRuntime->worldRuntime();
    const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
    const bx::Vec3 partyPoint = {moveState.x, moveState.y, moveState.footZ};
    const bx::Vec3 partyEye = {moveState.x, moveState.y, moveState.eyeZ()};
    const int16_t partySectorId = moveState.eyeSectorId >= 0 ? moveState.eyeSectorId : moveState.sectorId;
    const float radiusSquared = radius * radius;
    const std::vector<uint8_t> visibleSectorMask = buildVisibleSectorMask(partyEye);
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    GameplayWorldHit bestHit = {};
    float bestScore = std::numeric_limits<float>::max();

    const auto distanceSquaredFromParty =
        [&](const bx::Vec3 &point) -> float
        {
            const float deltaX = point.x - partyPoint.x;
            const float deltaY = point.y - partyPoint.y;
            const float deltaZ = point.z - partyPoint.z;
            return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        };

    const auto tryUpdateBestHit =
        [&](GameplayWorldHit hit, const bx::Vec3 &hitPoint, float priority)
        {
            if (!hit.hasHit)
            {
                return;
            }

            const float distanceSquared = distanceSquaredFromParty(hitPoint);

            if (distanceSquared > radiusSquared)
            {
                return;
            }

            if (!worldRuntime.canActivateWorldHit(hit, GameplayInteractionMethod::Keyboard))
            {
                return;
            }

            const float score = distanceSquared + priority;

            if (score < bestScore)
            {
                bestScore = score;
                bestHit = std::move(hit);
            }
        };

    const auto eventWorldHit =
        [&](const InspectHit &inspectHit, const bx::Vec3 &hitPoint) -> GameplayWorldHit
        {
            GameplayWorldHit hit = {};

            if (!inspectHit.hasHit)
            {
                return hit;
            }

            const uint16_t eventId = inspectHitEventId(inspectHit);
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
            const std::optional<std::string> eventTargetStatusText = resolveEventTargetHoverStatusText(inspectHit);
            eventTargetHit.name =
                eventTargetStatusText && !eventTargetStatusText->empty() ? *eventTargetStatusText : inspectHit.name;
            eventTargetHit.hitPoint = hitPoint;
            eventTargetHit.distance = std::sqrt(distanceSquaredFromParty(hitPoint));
            eventTargetHit.openedChestIds = resolveIndoorOpenedChestIds(m_pSceneRuntime, eventId);
            eventTargetHit.contextActionMetadata = resolveIndoorContextActionMetadata(m_pSceneRuntime, eventId);
            eventTargetHit.hintOnlyEvent = indoorEventIsHintOnly(m_pSceneRuntime, eventId);

            if (inspectHit.kind == "face")
            {
                eventTargetHit.targetKind = GameplayWorldEventTargetKind::Surface;
                eventTargetHit.secondaryIndex = inspectHit.index;
            }
            else if (inspectHit.kind == "entity")
            {
                eventTargetHit.targetKind = GameplayWorldEventTargetKind::Entity;
            }
            else if (inspectHit.kind == "mechanism")
            {
                eventTargetHit.targetKind = GameplayWorldEventTargetKind::Mechanism;
                eventTargetHit.triggeredEventId = inspectHit.mechanismLinkedEventId;
                eventTargetHit.secondaryIndex = inspectHit.mechanismFaceIndex;
            }
            else
            {
                return hit;
            }

            hit.hasHit = true;
            hit.kind = GameplayWorldHitKind::EventTarget;
            hit.eventTarget = eventTargetHit;
            return hit;
        };

    if (mapDeltaData
        && m_monsterTable
        && m_indoorActorPreviewBillboardSet)
    {
        const std::vector<RuntimeActorBillboard> runtimeActors =
            buildRuntimeActorBillboards(
                *m_monsterTable,
                m_indoorActorPreviewBillboardSet->spriteFrameTable,
                *mapDeltaData,
                &worldRuntime,
                &visibleSectorMask);

        for (const RuntimeActorBillboard &actor : runtimeActors)
        {
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
            actorHit.distance = std::sqrt(distanceSquaredFromParty(hitPoint));

            GameplayWorldHit hit = {};
            hit.hasHit = true;
            hit.kind = GameplayWorldHitKind::Actor;
            hit.actor = actorHit;
            tryUpdateBestHit(std::move(hit), hitPoint, 4.0f);
        }
    }

    if (mapDeltaData && m_objectTable)
    {
        const std::vector<RuntimeSpriteObjectBillboard> runtimeObjects =
            buildRuntimeSpriteObjectBillboards(*m_objectTable, m_pItemTable, *mapDeltaData, &visibleSectorMask);

        for (const RuntimeSpriteObjectBillboard &object : runtimeObjects)
        {
            if (!object.hasContainingItem)
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
            worldItemHit.displayName = object.objectName;
            worldItemHit.objectDescriptionId = object.objectDescriptionId;
            worldItemHit.objectSpriteId = object.objectSpriteId;
            worldItemHit.hitPoint = hitPoint;
            worldItemHit.distance = std::sqrt(distanceSquaredFromParty(hitPoint));

            GameplayWorldHit hit = {};
            hit.hasHit = true;
            hit.kind = GameplayWorldHitKind::WorldItem;
            hit.worldItem = worldItemHit;
            tryUpdateBestHit(std::move(hit), hitPoint, 2.0f);
        }
    }

    for (size_t faceIndex = 0; faceIndex < m_indoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_indoorMapData->faces[faceIndex];

        if (face.vertexIndices.empty()
            || (face.cogTriggered == 0 && face.cogNumber == 0)
            || !isFaceVisible(faceIndex, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage())
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

        const uint32_t effectiveAttributes =
            mapDeltaData && faceIndex < mapDeltaData->faceAttributes.size()
                ? mapDeltaData->faceAttributes[faceIndex]
                : face.attributes;
        InspectHit inspectHit = {};
        inspectHit.hasHit = true;
        inspectHit.kind = "face";
        inspectHit.index = faceIndex;
        inspectHit.textureName = face.textureName;
        inspectHit.distance = std::sqrt(distanceSquaredFromParty(center));
        inspectHit.attributes = effectiveAttributes;
        inspectHit.cogNumber = face.cogNumber;
        inspectHit.cogTriggered = face.cogTriggered;
        inspectHit.cogTriggerType = face.cogTriggerType;
        inspectHit.roomNumber = face.roomNumber;
        inspectHit.roomBehindNumber = face.roomBehindNumber;
        inspectHit.facetType = face.facetType;
        inspectHit.isPortal = face.isPortal;
        GameplayWorldHit candidateHit = eventWorldHit(inspectHit, center);

        if (candidateHit.eventTarget
            && indoorFaceSuppressedForArpgContextAction(
                *m_indoorMapData,
                faceIndex,
                face,
                candidateHit.eventTarget->contextActionMetadata,
                candidateHit.eventTarget->openedChestIds))
        {
            continue;
        }

        tryUpdateBestHit(candidateHit, center, 32.0f);
    }

    if (m_indoorMapData)
    {
        for (size_t entityIndex = 0; entityIndex < m_indoorMapData->entities.size(); ++entityIndex)
        {
            const IndoorEntity &entity = m_indoorMapData->entities[entityIndex];
            const bx::Vec3 center = {
                static_cast<float>(entity.x),
                static_cast<float>(entity.y),
                static_cast<float>(entity.z) + 32.0f
            };

            InspectHit inspectHit = {};
            inspectHit.hasHit = true;
            inspectHit.kind = "entity";
            inspectHit.index = entityIndex;
            inspectHit.name = entity.name;
            inspectHit.distance = std::sqrt(distanceSquaredFromParty(center));
            inspectHit.decorationListId = entity.decorationListId;
            inspectHit.eventIdPrimary = entity.eventIdPrimary;
            inspectHit.eventIdSecondary = entity.eventIdSecondary;
            inspectHit.variablePrimary = entity.variablePrimary;
            inspectHit.variableSecondary = entity.variableSecondary;
            inspectHit.specialTrigger = entity.specialTrigger;
            tryUpdateBestHit(eventWorldHit(inspectHit, center), center, 16.0f);
        }
    }

    if (mapDeltaData)
    {
        for (size_t doorIndex = 0; doorIndex < mapDeltaData->doors.size(); ++doorIndex)
        {
            const MapDeltaDoor &door = mapDeltaData->doors[doorIndex];

            if (door.faceIds.empty()
                || doorIndex >= m_mechanismBindings.size()
                || m_mechanismBindings[doorIndex].linkedEventId == 0
                || indoorDoorMechanismSuppressesArpgContextAction(door, runtimeEventRuntimeState()))
            {
                continue;
            }

            bx::Vec3 center = {0.0f, 0.0f, 0.0f};
            size_t selectedFaceIndex = GameplayInvalidWorldIndex;
            float selectedFaceDistanceSquared = std::numeric_limits<float>::max();

            for (uint16_t faceId : door.faceIds)
            {
                if (faceId >= m_indoorMapData->faces.size())
                {
                    continue;
                }

                const IndoorFace &face = m_indoorMapData->faces[faceId];

                if (face.vertexIndices.empty()
                    || face.facetType == 3
                    || isCeilingFace(faceId, face)
                    || !indoorFaceHasActualEvent(m_pSceneRuntime, face)
                    || !indoorFaceTouchesSector(face, partySectorId)
                    || !isFaceVisible(faceId, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage()))
                {
                    continue;
                }

                bx::Vec3 faceCenter = {0.0f, 0.0f, 0.0f};
                uint32_t validVertexCount = 0;

                for (uint16_t vertexId : face.vertexIndices)
                {
                    if (vertexId >= m_renderVertices.size())
                    {
                        continue;
                    }

                    const IndoorVertex &vertex = m_renderVertices[vertexId];
                    faceCenter.x += static_cast<float>(vertex.x);
                    faceCenter.y += static_cast<float>(vertex.y);
                    faceCenter.z += static_cast<float>(vertex.z);
                    ++validVertexCount;
                }

                if (validVertexCount == 0)
                {
                    continue;
                }

                faceCenter.x /= static_cast<float>(validVertexCount);
                faceCenter.y /= static_cast<float>(validVertexCount);
                faceCenter.z /= static_cast<float>(validVertexCount);

                const float distanceSquared = distanceSquaredFromParty(faceCenter);

                if (distanceSquared < selectedFaceDistanceSquared)
                {
                    selectedFaceDistanceSquared = distanceSquared;
                    selectedFaceIndex = faceId;
                    center = faceCenter;
                }
            }

            if (selectedFaceIndex == GameplayInvalidWorldIndex)
            {
                continue;
            }

            InspectHit inspectHit = {};
            inspectHit.hasHit = true;
            inspectHit.kind = "mechanism";
            inspectHit.index = doorIndex;
            inspectHit.distance = std::sqrt(distanceSquaredFromParty(center));
            inspectHit.doorAttributes = door.attributes;
            inspectHit.doorId = door.doorId;
            inspectHit.doorState = door.state;
            inspectHit.mechanismFaceIndex = selectedFaceIndex;
            const MechanismBinding &binding = m_mechanismBindings[doorIndex];
            inspectHit.mechanismLinkedEventId = binding.linkedEventId;
            inspectHit.mechanismFaceSummary = binding.faceSummary;
            inspectHit.mechanismLinkedEventSummary = binding.linkedEventSummary;
            tryUpdateBestHit(eventWorldHit(inspectHit, center), center, 0.0f);
        }
    }

    return bestHit;
}

float IndoorRenderer::cameraYawRadians() const
{
    return m_cameraYawRadians;
}

float IndoorRenderer::cameraPitchRadians() const
{
    return m_cameraPitchRadians;
}

float IndoorRenderer::arpgModeGameplayYawRadians() const
{
    return m_arpgModeCameraActive ? m_arpgModeGameplayYawRadians : m_cameraYawRadians;
}

void IndoorRenderer::setArpgModeGameplayYawRadians(float yawRadians)
{
    if (!m_arpgModeCameraActive)
    {
        return;
    }

    m_arpgModeGameplayYawRadians = yawRadians;
}

void IndoorRenderer::playArpgModePartyActionAnimation(float animationSeconds, bool spellCast)
{
    if (!m_arpgModeCameraActive)
    {
        return;
    }

    const float durationSeconds = std::max(animationSeconds, 0.05f);
    m_arpgModeActionAnimationSeconds = durationSeconds;
    m_arpgModeActionAnimationDurationSeconds = durationSeconds;
    m_arpgModeActionAnimationElapsedSeconds = 0.0f;
    m_arpgModeActionAnimationIsCast = spellCast;
}

void IndoorRenderer::sustainArpgModePartyActionAnimation(float animationSeconds, bool spellCast)
{
    if (!m_arpgModeCameraActive)
    {
        return;
    }

    const float durationSeconds = std::max(animationSeconds, 0.05f);

    if (m_arpgModeActionAnimationSeconds <= 0.0f || m_arpgModeActionAnimationIsCast != spellCast)
    {
        playArpgModePartyActionAnimation(durationSeconds, spellCast);
        return;
    }

    if (m_arpgModeActionAnimationDurationSeconds <= 0.0f
        || m_arpgModeActionAnimationElapsedSeconds >= m_arpgModeActionAnimationDurationSeconds)
    {
        m_arpgModeActionAnimationElapsedSeconds = 0.0f;
    }

    m_arpgModeActionAnimationSeconds = std::max(m_arpgModeActionAnimationSeconds, durationSeconds);
    m_arpgModeActionAnimationDurationSeconds = std::max(m_arpgModeActionAnimationDurationSeconds, durationSeconds);
    m_arpgModeActionAnimationIsCast = spellCast;
}

void IndoorRenderer::cancelArpgModePartyActionAnimation()
{
    m_arpgModeActionAnimationSeconds = 0.0f;
    m_arpgModeActionAnimationDurationSeconds = 0.0f;
    m_arpgModeActionAnimationElapsedSeconds = 0.0f;
    m_arpgModeActionAnimationIsCast = false;
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
    else if (eventTarget.targetKind == GameplayWorldEventTargetKind::Mechanism)
    {
        inspectHit.kind = "mechanism";
        inspectHit.mechanismLinkedEventId = eventTarget.triggeredEventId;
        inspectHit.mechanismFaceIndex = eventTarget.secondaryIndex;
    }
    else if (eventTarget.targetKind == GameplayWorldEventTargetKind::Object)
    {
        return std::nullopt;
    }
    else
    {
        return std::nullopt;
    }

    return inspectHit;
}

bool IndoorRenderer::canActivateGameplayWorldHit(const GameplayWorldHit &hit) const
{
    if (hit.kind == GameplayWorldHitKind::EventTarget && hit.eventTarget)
    {
        const GameplayEventTargetHit &eventTarget = *hit.eventTarget;

        if (eventTarget.targetKind == GameplayWorldEventTargetKind::Surface)
        {
            if (!m_indoorMapData)
            {
                return false;
            }

            const size_t faceIndex =
                eventTarget.secondaryIndex != GameplayInvalidWorldIndex
                    ? eventTarget.secondaryIndex
                    : eventTarget.targetIndex;

            if (faceIndex >= m_indoorMapData->faces.size())
            {
                return false;
            }

            const IndoorFace &face = m_indoorMapData->faces[faceIndex];

            if (!indoorFaceHasActualEvent(m_pSceneRuntime, face)
                || !isFaceVisible(faceIndex, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage())
                || indoorFaceSuppressedForContextAction(
                    *m_indoorMapData,
                    faceIndex,
                    face,
                    eventTarget.contextActionMetadata,
                    eventTarget.openedChestIds))
            {
                return false;
            }

            if (!eventTarget.openedChestIds.empty()
                || (eventTarget.contextActionMetadata && !eventTarget.contextActionMetadata->hidden))
            {
                return true;
            }

            const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
            const uint32_t effectiveAttributes =
                mapDeltaData && faceIndex < mapDeltaData->faceAttributes.size()
                    ? mapDeltaData->faceAttributes[faceIndex]
                    : face.attributes;

            return indoorFaceIsInteractionActivatable(effectiveAttributes, eventTarget.triggeredEventId);
        }

        if (eventTarget.targetKind == GameplayWorldEventTargetKind::Mechanism && eventTarget.triggeredEventId != 0)
        {
            const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

            if (mapDeltaData
                && eventTarget.targetIndex < mapDeltaData->doors.size()
                && indoorDoorMechanismSuppressedForContextAction(
                    mapDeltaData->doors[eventTarget.targetIndex],
                    runtimeEventRuntimeState()))
            {
                return false;
            }

            return true;
        }
    }

    const std::optional<InspectHit> inspectHit = inspectHitFromGameplayWorldHit(hit);

    if (!inspectHit)
    {
        return false;
    }

    if (inspectHit->kind == "entity")
    {
        return inspectHitEventId(*inspectHit) != 0;
    }

    if (inspectHit->kind == "face")
    {
        return indoorFaceIsInteractionActivatable(inspectHit->attributes, inspectHit->cogTriggered);
    }

    if (inspectHit->kind == "mechanism")
    {
        return inspectHitEventId(*inspectHit) != 0;
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
    m_indoorPortalGraph.reset();
    m_indoorLightingRuntime.clearStaticCache();
    m_renderVertices.clear();
    m_neighboringSectorIds.clear();
    m_arpgModeRenderVisibilityCacheValid = false;
    m_arpgModeCameraVisibleSectorMaskCache.clear();
    m_arpgModeRenderVisibleSectorMaskCache.clear();
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
    m_indoorInteractiveDecorationDecorVarIndicesByEntity.clear();
    m_indoorInteractiveDecorationBaseEventIdsByEntity.clear();
    m_indoorInteractiveDecorationEventCountsByEntity.clear();
    m_indoorInteractiveDecorationHideWhenClearedByEntity.clear();
    m_decorationBillboardIndicesBySector.clear();
    m_staticSpriteObjectBillboardIndicesBySector.clear();
    m_houseTable.reset();
    m_mechanismBindings.clear();
    m_lastVisibilityDiagnosticsLogTick = 0;
    m_indoorGeometryRenderingDisabled = false;
    m_indoorGeometryRenderingToggleHeld = false;
    m_ceilingFaceMask.clear();
    m_arpgModeOccludingFaceCandidates.clear();
    m_arpgModeOccludingFaceNeighbors.clear();
    m_arpgModeOcclusionGeometryCache.reset(0);
    clearPortalVisibilityCaches();
    m_worldFxSystem.reset();

    if (!Engine::BgfxContext::isBgfxInitialized())
    {
        m_worldFxRenderResources.reset();
        m_programHandle = BGFX_INVALID_HANDLE;
        m_texturedProgramHandle = BGFX_INVALID_HANDLE;
        m_indoorLitProgramHandle = BGFX_INVALID_HANDLE;
        m_billboardProgramHandle = BGFX_INVALID_HANDLE;
        m_bloodSplatVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_bloodSplatTextureHandle = BGFX_INVALID_HANDLE;
        m_entityMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_portalVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_spawnMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_doorMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_textureSamplerHandle = BGFX_INVALID_HANDLE;
        m_indoorLightPositionsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorLightColorsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorLightParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_secretPulseParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorFaceAlphaParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorSkyParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorSkyProjectionParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardAmbientUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardOverrideColorUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardOutlineParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardFogColorUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardFogDensitiesUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardFogDistancesUniformHandle = BGFX_INVALID_HANDLE;
        m_wireframeVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_billboardTextureHandles.clear();
        m_billboardTextureIndexByKey.clear();
        m_indoorTextureHandles.clear();
        m_texturedBatches.clear();
        m_indoorLightingSelectionCache.clear();
        m_indoorLightingSelectionFrame = 0;
        m_faceBatchIndices.clear();
        m_texturedBatchVisualRevision = std::numeric_limits<uint64_t>::max();
        m_elapsedTime = 0.0f;
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
        return;
    }

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

    if (bgfx::isValid(m_secretPulseParamsUniformHandle))
    {
        bgfx::destroy(m_secretPulseParamsUniformHandle);
        m_secretPulseParamsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_indoorFaceAlphaParamsUniformHandle))
    {
        bgfx::destroy(m_indoorFaceAlphaParamsUniformHandle);
        m_indoorFaceAlphaParamsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_indoorSkyParamsUniformHandle))
    {
        bgfx::destroy(m_indoorSkyParamsUniformHandle);
        m_indoorSkyParamsUniformHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_indoorSkyProjectionParamsUniformHandle))
    {
        bgfx::destroy(m_indoorSkyProjectionParamsUniformHandle);
        m_indoorSkyProjectionParamsUniformHandle = BGFX_INVALID_HANDLE;
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
    m_billboardTextureIndexByKey.clear();

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

void IndoorRenderer::rebuildIndoorRenderMemberships()
{
    const size_t sectorCount = m_indoorMapData ? m_indoorMapData->sectors.size() : 0;
    m_decorationBillboardIndicesBySector.assign(sectorCount, {});
    m_staticSpriteObjectBillboardIndicesBySector.assign(sectorCount, {});

    if (m_indoorDecorationBillboardSet)
    {
        for (size_t billboardIndex = 0;
             billboardIndex < m_indoorDecorationBillboardSet->billboards.size();
             ++billboardIndex)
        {
            const DecorationBillboard &billboard = m_indoorDecorationBillboardSet->billboards[billboardIndex];

            if (billboard.sectorId >= 0 && static_cast<size_t>(billboard.sectorId) < sectorCount)
            {
                m_decorationBillboardIndicesBySector[static_cast<size_t>(billboard.sectorId)].push_back(
                    billboardIndex);
            }
        }
    }

    if (m_indoorSpriteObjectBillboardSet)
    {
        for (size_t billboardIndex = 0;
             billboardIndex < m_indoorSpriteObjectBillboardSet->billboards.size();
             ++billboardIndex)
        {
            const SpriteObjectBillboard &billboard = m_indoorSpriteObjectBillboardSet->billboards[billboardIndex];

            if (billboard.sectorId >= 0 && static_cast<size_t>(billboard.sectorId) < sectorCount)
            {
                m_staticSpriteObjectBillboardIndicesBySector[static_cast<size_t>(billboard.sectorId)].push_back(
                    billboardIndex);
            }
        }
    }
}

void IndoorRenderer::rebuildArpgModeOccludingFaceCandidates()
{
    m_arpgModeOccludingFaceCandidates.clear();
    m_arpgModeOccludingFaceNeighbors.clear();

    if (!m_indoorMapData
        || m_faceBatchIndices.size() != m_indoorMapData->faces.size()
        || m_faceVertexCounts.size() != m_indoorMapData->faces.size())
    {
        return;
    }

    m_arpgModeOccludingFaceCandidates.reserve(m_indoorMapData->faces.size());
    m_arpgModeOccludingFaceNeighbors.resize(m_indoorMapData->faces.size());
    std::unordered_map<uint32_t, std::vector<size_t>> faceIndicesByEdge;
    faceIndicesByEdge.reserve(m_indoorMapData->faces.size() * 2);

    for (size_t faceIndex = 0; faceIndex < m_indoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_indoorMapData->faces[faceIndex];

        if (face.vertexIndices.size() < 3
            || isCeilingFace(faceIndex, face)
            || faceIndex >= m_faceBatchIndices.size()
            || m_faceBatchIndices[faceIndex] < 0
            || m_faceVertexCounts[faceIndex] == 0)
        {
            continue;
        }

        ArpgModeOccludingFaceCandidate candidate = {};
        candidate.faceIndex = faceIndex;
        candidate.sectorId =
            face.roomNumber < m_indoorMapData->sectors.size() ? static_cast<int16_t>(face.roomNumber) : int16_t(-1);
        candidate.backSectorId =
            face.roomBehindNumber < m_indoorMapData->sectors.size()
                ? static_cast<int16_t>(face.roomBehindNumber)
                : int16_t(-1);

        bool hasBounds = false;

        for (uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= m_renderVertices.size())
            {
                continue;
            }

            const IndoorVertex &vertex = m_renderVertices[vertexIndex];
            const bx::Vec3 point = {
                static_cast<float>(vertex.x),
                static_cast<float>(vertex.y),
                static_cast<float>(vertex.z)
            };

            if (!hasBounds)
            {
                candidate.boundsMin = point;
                candidate.boundsMax = point;
                hasBounds = true;
            }
            else
            {
                candidate.boundsMin.x = std::min(candidate.boundsMin.x, point.x);
                candidate.boundsMin.y = std::min(candidate.boundsMin.y, point.y);
                candidate.boundsMin.z = std::min(candidate.boundsMin.z, point.z);
                candidate.boundsMax.x = std::max(candidate.boundsMax.x, point.x);
                candidate.boundsMax.y = std::max(candidate.boundsMax.y, point.y);
                candidate.boundsMax.z = std::max(candidate.boundsMax.z, point.z);
            }
        }

        if (hasBounds)
        {
            m_arpgModeOccludingFaceCandidates.push_back(candidate);

            for (size_t vertexIndex = 0; vertexIndex < face.vertexIndices.size(); ++vertexIndex)
            {
                const uint16_t vertexA = face.vertexIndices[vertexIndex];
                const uint16_t vertexB = face.vertexIndices[(vertexIndex + 1) % face.vertexIndices.size()];
                faceIndicesByEdge[indoorFaceEdgeKey(vertexA, vertexB)].push_back(faceIndex);
            }
        }
    }

    for (const std::pair<const uint32_t, std::vector<size_t>> &entry : faceIndicesByEdge)
    {
        const std::vector<size_t> &edgeFaceIndices = entry.second;

        if (edgeFaceIndices.size() < 2)
        {
            continue;
        }

        for (size_t sourceFaceIndex : edgeFaceIndices)
        {
            for (size_t targetFaceIndex : edgeFaceIndices)
            {
                if (sourceFaceIndex != targetFaceIndex
                    && sourceFaceIndex < m_arpgModeOccludingFaceNeighbors.size())
                {
                    appendUniqueIndex(m_arpgModeOccludingFaceNeighbors[sourceFaceIndex], targetFaceIndex);
                }
            }
        }
    }
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
        .add(bgfx::Attrib::TexCoord1, 4, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord2, 1, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord3, 4, bgfx::AttribType::Float)
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

void IndoorRenderer::setCameraAngles(float yawRadians, float pitchRadians)
{
    m_cameraYawRadians = yawRadians;
    m_cameraPitchRadians = pitchRadians;

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

const IndoorRenderer::BillboardTextureHandle *IndoorRenderer::findBillboardTexture(
    const std::string &textureName,
    int16_t paletteId
) const
{
    const BillboardTextureLookupKey textureKey = makeBillboardTextureLookupKey(textureName, paletteId);
    const auto textureIterator = m_billboardTextureIndexByKey.find(textureKey);

    if (textureIterator == m_billboardTextureIndexByKey.end()
        || textureIterator->second >= m_billboardTextureHandles.size())
    {
        return nullptr;
    }

    return &m_billboardTextureHandles[textureIterator->second];
}

IndoorRenderer::BillboardTextureLookupKey IndoorRenderer::makeBillboardTextureLookupKey(
    const std::string &textureName,
    int16_t paletteId)
{
    BillboardTextureLookupKey key = {};
    key.textureName = normalizeBillboardTextureName(textureName);
    key.paletteId = paletteId;

    return key;
}

void IndoorRenderer::registerBillboardTextureIndex(size_t textureIndex)
{
    if (textureIndex >= m_billboardTextureHandles.size())
    {
        return;
    }

    const BillboardTextureHandle &texture = m_billboardTextureHandles[textureIndex];
    m_billboardTextureIndexByKey[makeBillboardTextureLookupKey(texture.textureName, texture.paletteId)] = textureIndex;
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
            textureHeight,
            m_map.has_value() ? m_map->worldId : std::string());

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
    registerBillboardTextureIndex(m_billboardTextureHandles.size() - 1);
    return &m_billboardTextureHandles.back();
}

bgfx::TextureHandle IndoorRenderer::ensureBloodSplatTexture()
{
    if (bgfx::isValid(m_bloodSplatTextureHandle))
    {
        return m_bloodSplatTextureHandle;
    }

    std::optional<std::string> bitmapPath =
        GameplayHudCommon::findCachedAssetPath(
            m_pAssetFileSystem,
            m_spriteLoadCache,
            "Data/bitmaps",
            "hwsplat04.png");

    if (!bitmapPath)
    {
        bitmapPath =
            GameplayHudCommon::findCachedAssetPath(
                m_pAssetFileSystem,
                m_spriteLoadCache,
                "Data/bitmaps",
                "hwsplat04.bmp");
    }

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

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, *bitmapPath);

    if (!image)
    {
        return BGFX_INVALID_HANDLE;
    }

    const int textureWidth = image->width;
    const int textureHeight = image->height;
    std::vector<uint8_t> pixels = image->pixels;

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
    const IndoorDrawLightSet &lightSet)
{
    if (m_pSceneRuntime == nullptr
        || !bgfx::isValid(m_indoorLitProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle)
        || !bgfx::isValid(m_indoorLightPositionsUniformHandle)
        || !bgfx::isValid(m_indoorLightColorsUniformHandle)
        || !bgfx::isValid(m_indoorLightParamsUniformHandle)
        || !bgfx::isValid(m_secretPulseParamsUniformHandle)
        || !bgfx::isValid(m_indoorFaceAlphaParamsUniformHandle)
        || !bgfx::isValid(m_indoorSkyParamsUniformHandle)
        || !bgfx::isValid(m_indoorSkyProjectionParamsUniformHandle)
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
    bgfx::setUniform(m_indoorLightPositionsUniformHandle, lightSet.positions.data(), MaxIndoorShaderLights);
    bgfx::setUniform(m_indoorLightColorsUniformHandle, lightSet.colors.data(), MaxIndoorShaderLights);
    bgfx::setUniform(m_indoorLightParamsUniformHandle, lightSet.params.data());
    const std::array<float, 4> secretPulseParams = {0.0f, m_elapsedTime, 0.0f, 0.0f};
    bgfx::setUniform(m_secretPulseParamsUniformHandle, secretPulseParams.data());
    const std::array<float, 4> faceAlphaParams = {1.0f, 0.0f, 0.0f, 0.0f};
    bgfx::setUniform(m_indoorFaceAlphaParamsUniformHandle, faceAlphaParams.data());
    const std::array<float, 4> indoorSkyParams = {0.0f, 0.0f, m_cameraYawRadians, m_cameraPitchRadians};
    bgfx::setUniform(m_indoorSkyParamsUniformHandle, indoorSkyParams.data());
    const std::array<float, 4> indoorSkyProjectionParams = {0.0f, 0.0f, 1.0f, IndoorSkyProjectionPitchOffsetRadians};
    bgfx::setUniform(m_indoorSkyProjectionParamsUniformHandle, indoorSkyProjectionParams.data());
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
    const std::vector<std::vector<IndoorVisibilityFrustum>> &visibleSectorFrustums,
    const IndoorLightingFrame &lightingFrame,
    const GameplayContextActionState *pContextActionState,
    LightingStats *pLightingStats
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
    float billboardModelMatrix[16] = {};
    bx::mtxInverse(billboardModelMatrix, pViewMatrix);
    const float aspectRatio =
        m_lastRenderHeight > 0
        ? static_cast<float>(std::max(m_lastRenderWidth, 1)) / static_cast<float>(m_lastRenderHeight)
        : 1.0f;
    const std::array<IndoorVisibilityPlane, 4> frustumPlanes =
        buildIndoorBillboardFrustumPlanes(cameraPosition, m_cameraYawRadians, m_cameraPitchRadians, aspectRatio);
    const uint32_t animationTimeTicks = currentAnimationTicks();

    struct BillboardDrawItem
    {
        const DecorationBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        bool hovered = false;
        uint32_t hoveredOutlineColorAbgr = 0;
        float distanceSquared = 0.0f;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(m_indoorDecorationBillboardSet->billboards.size());
    const GameplayWorldHit *pContextActionHit = selectedContextActionWorldHit(pContextActionState);
    const auto resolveBillboardSpriteId = [this](const DecorationBillboard &billboard, bool &hidden)
    {
        hidden = false;

        const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

        if (!m_indoorDecorationBillboardSet || !eventRuntimeState.has_value())
        {
            return billboard.spriteId;
        }

        const uint32_t overrideKey = billboard.spriteOverrideKey();
        const auto overrideIterator = eventRuntimeState->spriteOverrides.find(overrideKey);

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

    const auto appendDecorationBillboardDrawItem =
        [&](const DecorationBillboard &billboard)
    {
        if (!isRenderSectorVisible(billboard.sectorId, visibleSectorMask))
        {
            return;
        }

        bool hidden = false;
        const uint16_t spriteId = resolveBillboardSpriteId(billboard, hidden);

        if (hidden || spriteId == 0)
        {
            return;
        }

        const uint32_t animationOffsetTicks =
            animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
        const SpriteFrameEntry *pFrame =
            m_indoorDecorationBillboardSet->spriteFrameTable.getFrame(spriteId, animationOffsetTicks);

        if (pFrame == nullptr)
        {
            return;
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
            return;
        }

        const float spriteScale = std::max(pFrame->scale, 0.01f);
        const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
        const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
        const bx::Vec3 center = {
            static_cast<float>(billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z) + worldHeight * 0.5f
        };
        const float radius = std::sqrt((worldWidth * 0.5f) * (worldWidth * 0.5f)
            + (worldHeight * 0.5f) * (worldHeight * 0.5f));

        if (!billboardSphereInFrustum(center, radius, frustumPlanes))
        {
            return;
        }

        if (!sphereIntersectsVisibleSectorFrustums(billboard.sectorId, center, radius, visibleSectorFrustums))
        {
            return;
        }

        const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
        const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
        const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;

        BillboardDrawItem drawItem = {};
        drawItem.pBillboard = &billboard;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.hovered = contextActionHighlightsIndoorEntity(pContextActionHit, billboard.entityIndex);
        drawItem.hoveredOutlineColorAbgr = drawItem.hovered ? contextActionHighlightOutlineColor() : 0;
        drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        drawItems.push_back(drawItem);
    };

    if (!m_decorationBillboardIndicesBySector.empty())
    {
        for (size_t sectorId = 0; sectorId < m_decorationBillboardIndicesBySector.size(); ++sectorId)
        {
            if (!isRenderSectorVisible(static_cast<int16_t>(sectorId), visibleSectorMask))
            {
                continue;
            }

            for (size_t billboardIndex : m_decorationBillboardIndicesBySector[sectorId])
            {
                if (billboardIndex < m_indoorDecorationBillboardSet->billboards.size())
                {
                    appendDecorationBillboardDrawItem(m_indoorDecorationBillboardSet->billboards[billboardIndex]);
                }
            }
        }
    }
    else
    {
        for (const DecorationBillboard &billboard : m_indoorDecorationBillboardSet->billboards)
        {
            appendDecorationBillboardDrawItem(billboard);
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

    if (m_logIndoorPerformanceDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderDecorationSpriteItems += drawItems.size();

        const BillboardTextureHandle *pLastTexture = nullptr;
        for (const BillboardDrawItem &drawItem : drawItems)
        {
            if (drawItem.pTexture != pLastTexture)
            {
                ++m_indoorPerformanceDiagnostics.renderDecorationSpriteTextureSwitches;
                pLastTexture = drawItem.pTexture;
            }
        }
    }

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const DecorationBillboard &billboard = *drawItem.pBillboard;
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
        const bx::Vec3 viewCenter = transformIndoorPoint(center, pViewMatrix);
        const bx::Vec3 right = {halfWidth, 0.0f, 0.0f};
        const bx::Vec3 up = {0.0f, worldHeight * 0.5f, 0.0f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
        const uint32_t vertexColorAbgr = makeAbgr(0, 0, 0);
        const std::array<float, 4> ambient =
            billboardLightingUniform(lightingFrame, frame, center, billboard.sectorId, pLightingStats);
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
            const bx::Vec3 outlineRight = {outlinedHalfWidth, 0.0f, 0.0f};
            const bx::Vec3 outlineUp = {0.0f, outlinedHalfHeight, 0.0f};
            const float outlineU0 = drawItem.mirrored ? 1.0f + paddingU : -paddingU;
            const float outlineU1 = drawItem.mirrored ? -paddingU : 1.0f + paddingU;
            const float outlineVTop = -paddingV;
            const float outlineVBottom = 1.0f + paddingV;
            std::array<LitBillboardVertex, 6> outlineVertices = {{
                {
                    viewCenter.x - outlineRight.x - outlineUp.x,
                    viewCenter.y - outlineRight.y - outlineUp.y,
                    viewCenter.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    viewCenter.x - outlineRight.x + outlineUp.x,
                    viewCenter.y - outlineRight.y + outlineUp.y,
                    viewCenter.z - outlineRight.z + outlineUp.z,
                    outlineU0,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    viewCenter.x + outlineRight.x + outlineUp.x,
                    viewCenter.y + outlineRight.y + outlineUp.y,
                    viewCenter.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    viewCenter.x - outlineRight.x - outlineUp.x,
                    viewCenter.y - outlineRight.y - outlineUp.y,
                    viewCenter.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    viewCenter.x + outlineRight.x + outlineUp.x,
                    viewCenter.y + outlineRight.y + outlineUp.y,
                    viewCenter.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    viewCenter.x + outlineRight.x - outlineUp.x,
                    viewCenter.y + outlineRight.y - outlineUp.y,
                    viewCenter.z + outlineRight.z - outlineUp.z,
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
                std::memcpy(modelMatrix, billboardModelMatrix, sizeof(modelMatrix));
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
                    IndoorBillboardDrawState);
                bgfx::submit(viewId, m_billboardProgramHandle);

                if (m_logIndoorPerformanceDiagnostics)
                {
                    ++m_indoorPerformanceDiagnostics.renderDecorationSpriteOutlineSubmits;
                }
            }
        }

        std::array<LitBillboardVertex, 6> vertices = {{
            {
                viewCenter.x - right.x - up.x,
                viewCenter.y - right.y - up.y,
                viewCenter.z - right.z - up.z,
                u0,
                1.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x - right.x + up.x,
                viewCenter.y - right.y + up.y,
                viewCenter.z - right.z + up.z,
                u0,
                0.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x + right.x + up.x,
                viewCenter.y + right.y + up.y,
                viewCenter.z + right.z + up.z,
                u1,
                0.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x - right.x - up.x,
                viewCenter.y - right.y - up.y,
                viewCenter.z - right.z - up.z,
                u0,
                1.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x + right.x + up.x,
                viewCenter.y + right.y + up.y,
                viewCenter.z + right.z + up.z,
                u1,
                0.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x + right.x - up.x,
                viewCenter.y + right.y - up.y,
                viewCenter.z + right.z - up.z,
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
        std::memcpy(modelMatrix, billboardModelMatrix, sizeof(modelMatrix));
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
            IndoorBillboardDrawState
        );
        bgfx::submit(viewId, m_billboardProgramHandle);

        if (m_logIndoorPerformanceDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.renderDecorationSpriteSubmits;
        }
    }
}

void IndoorRenderer::renderActorPreviewBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask,
    const std::vector<std::vector<IndoorVisibilityFrustum>> &visibleSectorFrustums,
    const IndoorLightingFrame &lightingFrame,
    bool spriteOutlineEnabled,
    const GameplayContextActionState *pContextActionState,
    const GameSettings *pSettings,
    LightingStats *pLightingStats
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
    float billboardModelMatrix[16] = {};
    bx::mtxInverse(billboardModelMatrix, pViewMatrix);
    const float aspectRatio =
        m_lastRenderHeight > 0
        ? static_cast<float>(std::max(m_lastRenderWidth, 1)) / static_cast<float>(m_lastRenderHeight)
        : 1.0f;
    const std::array<IndoorVisibilityPlane, 4> frustumPlanes =
        buildIndoorBillboardFrustumPlanes(cameraPosition, m_cameraYawRadians, m_cameraPitchRadians, aspectRatio);
    const uint32_t animationTimeTicks = currentAnimationTicks();

    struct BillboardDrawItem
    {
        size_t actorIndex = static_cast<size_t>(-1);
        int x = 0;
        int y = 0;
        int z = 0;
        int16_t sectorId = -1;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        bool hovered = false;
        uint32_t hoveredOutlineColorAbgr = 0;
        float heightScale = 1.0f;
        bool arpgPlayerPuppet = false;
        float distanceSquared = 0.0f;
        bool hasHealthBar = false;
        float healthRatio = 1.0f;
        float healthBarZ = 0.0f;
        float healthBarScale = 1.0f;
    };

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::optional<size_t> hoveredActorIndex =
        m_cachedInspectHitValid && m_cachedInspectHit.kind == "actor"
        ? std::optional<size_t>(m_cachedInspectHit.index)
        : std::nullopt;
    const GameplayWorldHit *pContextActionHit = selectedContextActionWorldHit(pContextActionState);
    const std::vector<RuntimeActorBillboard> runtimeBillboards =
        mapDeltaData && m_monsterTable
        ? buildRuntimeActorBillboards(
            *m_monsterTable,
            m_indoorActorPreviewBillboardSet->spriteFrameTable,
            *mapDeltaData,
            m_pSceneRuntime != nullptr ? &m_pSceneRuntime->worldRuntime() : nullptr,
            &visibleSectorMask)
        : std::vector<RuntimeActorBillboard>{};
    std::vector<BillboardDrawItem> drawItems;
    const bool useRuntimeBillboards = mapDeltaData.has_value() && m_pSceneRuntime != nullptr;
    drawItems.reserve(
        useRuntimeBillboards
        ? runtimeBillboards.size()
        : m_indoorActorPreviewBillboardSet->billboards.size());

    if (useRuntimeBillboards)
    {
        for (const RuntimeActorBillboard &billboard : runtimeBillboards)
        {
            if (!isRenderSectorVisible(billboard.sectorId, visibleSectorMask))
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

            const float spriteScale = std::max(pFrame->scale * billboard.heightScale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const bx::Vec3 center = bottomAnchoredBillboardCenter(
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z),
                cameraUp,
                worldHeight);
            const float radius = std::sqrt((worldWidth * 0.5f) * (worldWidth * 0.5f)
                + (worldHeight * 0.5f) * (worldHeight * 0.5f));

            if (!billboardSphereInFrustum(center, radius, frustumPlanes))
            {
                continue;
            }

            if (!sphereIntersectsVisibleSectorFrustums(billboard.sectorId, center, radius, visibleSectorFrustums))
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
            drawItem.sectorId = billboard.sectorId;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            const bool contextHighlighted = contextActionHighlightsActor(pContextActionHit, billboard.actorIndex);
            drawItem.hovered =
                contextHighlighted
                || (spriteOutlineEnabled && hoveredActorIndex && *hoveredActorIndex == billboard.actorIndex);
            drawItem.heightScale = billboard.heightScale;
            if (drawItem.hovered && mapDeltaData && billboard.actorIndex < mapDeltaData->actors.size())
            {
                drawItem.hoveredOutlineColorAbgr =
                    contextHighlighted
                        ? contextActionHighlightOutlineColor()
                        : resolveHoveredIndoorActorOutlineColor(
                            mapDeltaData->actors[billboard.actorIndex],
                            pActorAiState);
            }
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

            if (pActorAiState != nullptr
                && pActorAiState->hostileToParty
                && mapDeltaData
                && billboard.actorIndex < mapDeltaData->actors.size()
                && mapDeltaData->actors[billboard.actorIndex].hp > 0)
            {
                GameplayActorInspectState inspectState = {};
                const bool hasInspectState =
                    m_pSceneRuntime != nullptr
                    && m_pSceneRuntime->worldRuntime().actorInspectState(
                        billboard.actorIndex,
                        0,
                        inspectState);
                const int maxHp = hasInspectState && inspectState.maxHp > 0
                    ? inspectState.maxHp
                    : static_cast<int>(mapDeltaData->actors[billboard.actorIndex].hp);
                const int currentHp = hasInspectState
                    ? inspectState.currentHp
                    : static_cast<int>(mapDeltaData->actors[billboard.actorIndex].hp);

                if (maxHp > 0)
                {
                    drawItem.hasHealthBar = true;
                    drawItem.healthRatio =
                        std::clamp(
                            static_cast<float>(currentHp) / static_cast<float>(maxHp),
                            0.0f,
                            1.0f);
                    drawItem.healthBarScale = 1.0f;
                }
            }

            drawItem.healthBarZ = drawItem.z + worldHeight + 26.0f * drawItem.heightScale;
            drawItems.push_back(drawItem);
        }

        if (pSettings != nullptr
            && pSettings->arpgModeEnabled
            && m_pSceneRuntime != nullptr
            && m_monsterTable)
        {
            const MonsterEntry *pMonsterEntry = resolveArpgModePlayerMonsterEntry(
                *m_monsterTable,
                *pSettings,
                m_indoorActorPreviewBillboardSet->spriteFrameTable);

            if (pMonsterEntry != nullptr)
            {
                const std::array<uint16_t, 8> actionSpriteFrameIndices =
                    buildRuntimeActorActionSpriteFrameIndices(
                        m_indoorActorPreviewBillboardSet->spriteFrameTable,
                        pMonsterEntry);
                const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
                const bool walkingAnimationActive = m_arpgModeHasMoveDestination && moveState.grounded;
                const uint16_t spriteFrameIndex =
                    selectArpgModePlayerSpriteFrameIndex(
                        m_arpgModeActionAnimationSeconds,
                        m_arpgModeActionAnimationIsCast,
                        walkingAnimationActive,
                        actionSpriteFrameIndices);
                uint32_t frameTimeTicks = animationTimeTicks;

                if (m_arpgModeActionAnimationSeconds > 0.0f
                    && m_arpgModeActionAnimationDurationSeconds > 0.0f)
                {
                    const SpriteFrameEntry *pFirstFrame =
                        m_indoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, 0);

                    if (pFirstFrame != nullptr && pFirstFrame->animationLengthTicks > 0)
                    {
                        const float progress =
                            std::clamp(
                                m_arpgModeActionAnimationElapsedSeconds / m_arpgModeActionAnimationDurationSeconds,
                                0.0f,
                                1.0f);
                        frameTimeTicks =
                            static_cast<uint32_t>(
                                std::floor(progress * static_cast<float>(pFirstFrame->animationLengthTicks - 1)));
                    }
                }

                const SpriteFrameEntry *pFrame =
                    m_indoorActorPreviewBillboardSet->spriteFrameTable.getFrame(
                        spriteFrameIndex,
                        frameTimeTicks);

                if (pFrame != nullptr)
                {
                    const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
                    const float angleToCamera = std::atan2(
                        moveState.y - cameraPosition.y,
                        moveState.x - cameraPosition.x);
                    const float octantAngle = m_arpgModeGameplayYawRadians - angleToCamera + Pi + (Pi / 8.0f);
                    const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
                    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
                    const BillboardTextureHandle *pTexture =
                        ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

                    if (pTexture != nullptr && bgfx::isValid(pTexture->textureHandle))
                    {
                        const int16_t sectorId =
                            moveState.eyeSectorId >= 0 ? moveState.eyeSectorId : moveState.sectorId;
                        constexpr float PlayerPuppetHeightScale = 1.25f;
                        const float spriteScale = std::max(pFrame->scale * PlayerPuppetHeightScale, 0.01f);
                        const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                        const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                        const bx::Vec3 center = bottomAnchoredBillboardCenter(
                            moveState.x,
                            moveState.y,
                            moveState.footZ,
                            cameraUp,
                            worldHeight);
                        const float radius = std::sqrt((worldWidth * 0.5f) * (worldWidth * 0.5f)
                            + (worldHeight * 0.5f) * (worldHeight * 0.5f));

                        if (billboardSphereInFrustum(center, radius, frustumPlanes)
                            && sphereIntersectsVisibleSectorFrustums(sectorId, center, radius, visibleSectorFrustums))
                        {
                            const float deltaX = moveState.x - cameraPosition.x;
                            const float deltaY = moveState.y - cameraPosition.y;
                            const float deltaZ = moveState.footZ - cameraPosition.z;

                            BillboardDrawItem drawItem = {};
                            drawItem.x = static_cast<int>(std::lround(moveState.x));
                            drawItem.y = static_cast<int>(std::lround(moveState.y));
                            drawItem.z = static_cast<int>(std::lround(moveState.footZ));
                            drawItem.sectorId = sectorId;
                            drawItem.pFrame = pFrame;
                            drawItem.pTexture = pTexture;
                            drawItem.mirrored = resolvedTexture.mirrored;
                            drawItem.heightScale = PlayerPuppetHeightScale;
                            drawItem.arpgPlayerPuppet = true;
                            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

                            const Party &party = m_pSceneRuntime->partyRuntime().party();
                            const Character *pMember = party.activeMember();

                            if (pMember != nullptr)
                            {
                                const int maximumHealth = Party::effectiveMaximumHealth(*pMember);

                                if (maximumHealth > 0)
                                {
                                    drawItem.hasHealthBar = true;
                                    drawItem.healthRatio =
                                        static_cast<float>(std::clamp(pMember->health, 0, maximumHealth))
                                        / static_cast<float>(maximumHealth);
                                    drawItem.healthBarScale = PlayerPuppetHeightScale;
                                }
                            }

                            drawItem.healthBarZ =
                                drawItem.z + worldHeight + 26.0f * drawItem.heightScale;
                            drawItems.push_back(drawItem);
                        }
                    }
                }
            }
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

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const bx::Vec3 center = bottomAnchoredBillboardCenter(
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z),
                cameraUp,
                worldHeight);
            const float radius = std::sqrt((worldWidth * 0.5f) * (worldWidth * 0.5f)
                + (worldHeight * 0.5f) * (worldHeight * 0.5f));

            if (!billboardSphereInFrustum(center, radius, frustumPlanes))
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

    if (m_logIndoorPerformanceDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderActorSpriteItems += drawItems.size();

        const BillboardTextureHandle *pLastTexture = nullptr;
        for (const BillboardDrawItem &drawItem : drawItems)
        {
            if (drawItem.pTexture != pLastTexture)
            {
                ++m_indoorPerformanceDiagnostics.renderActorSpriteTextureSwitches;
                pLastTexture = drawItem.pTexture;
            }
        }
    }

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale * drawItem.heightScale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = bottomAnchoredBillboardCenter(
            static_cast<float>(drawItem.x),
            static_cast<float>(drawItem.y),
            static_cast<float>(drawItem.z),
            cameraUp,
            worldHeight);
        const bx::Vec3 viewCenter = transformIndoorPoint(center, pViewMatrix);
        const bx::Vec3 right = {halfWidth, 0.0f, 0.0f};
        const bx::Vec3 up = {0.0f, worldHeight * 0.5f, 0.0f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
        const uint32_t vertexColorAbgr = makeAbgr(0, 0, 0);
        const std::array<float, 4> ambient =
            billboardLightingUniform(lightingFrame, frame, center, drawItem.sectorId, pLightingStats);
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
            const bx::Vec3 outlineRight = {outlinedHalfWidth, 0.0f, 0.0f};
            const bx::Vec3 outlineUp = {0.0f, outlinedHalfHeight, 0.0f};
            const float outlineU0 = drawItem.mirrored ? 1.0f + paddingU : -paddingU;
            const float outlineU1 = drawItem.mirrored ? -paddingU : 1.0f + paddingU;
            const float outlineVTop = -paddingV;
            const float outlineVBottom = 1.0f + paddingV;
            std::array<LitBillboardVertex, 6> outlineVertices = {{
                {
                    viewCenter.x - outlineRight.x - outlineUp.x,
                    viewCenter.y - outlineRight.y - outlineUp.y,
                    viewCenter.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    viewCenter.x - outlineRight.x + outlineUp.x,
                    viewCenter.y - outlineRight.y + outlineUp.y,
                    viewCenter.z - outlineRight.z + outlineUp.z,
                    outlineU0,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    viewCenter.x + outlineRight.x + outlineUp.x,
                    viewCenter.y + outlineRight.y + outlineUp.y,
                    viewCenter.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    viewCenter.x - outlineRight.x - outlineUp.x,
                    viewCenter.y - outlineRight.y - outlineUp.y,
                    viewCenter.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    viewCenter.x + outlineRight.x + outlineUp.x,
                    viewCenter.y + outlineRight.y + outlineUp.y,
                    viewCenter.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    viewCenter.x + outlineRight.x - outlineUp.x,
                    viewCenter.y + outlineRight.y - outlineUp.y,
                    viewCenter.z + outlineRight.z - outlineUp.z,
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
                std::memcpy(modelMatrix, billboardModelMatrix, sizeof(modelMatrix));
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
                uint64_t state =
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_BLEND_ALPHA;

                if (drawItem.arpgPlayerPuppet)
                {
                    state |= BGFX_STATE_DEPTH_TEST_ALWAYS;
                }
                else
                {
                    state |= BGFX_STATE_WRITE_Z | BGFX_STATE_DEPTH_TEST_LEQUAL;
                }

                bgfx::setState(state);
                bgfx::submit(viewId, m_billboardProgramHandle);

                if (m_logIndoorPerformanceDiagnostics)
                {
                    ++m_indoorPerformanceDiagnostics.renderActorSpriteOutlineSubmits;
                }
            }
        }

        std::array<LitBillboardVertex, 6> vertices = {};
        vertices[0] = {
            viewCenter.x - right.x - up.x,
            viewCenter.y - right.y - up.y,
            viewCenter.z - right.z - up.z,
            u0,
            1.0f,
            vertexColorAbgr
        };
        vertices[1] = {
            viewCenter.x - right.x + up.x,
            viewCenter.y - right.y + up.y,
            viewCenter.z - right.z + up.z,
            u0,
            0.0f,
            vertexColorAbgr
        };
        vertices[2] = {
            viewCenter.x + right.x + up.x,
            viewCenter.y + right.y + up.y,
            viewCenter.z + right.z + up.z,
            u1,
            0.0f,
            vertexColorAbgr
        };
        vertices[3] = vertices[0];
        vertices[4] = vertices[2];
        vertices[5] = {
            viewCenter.x + right.x - up.x,
            viewCenter.y + right.y - up.y,
            viewCenter.z + right.z - up.z,
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
        std::memcpy(modelMatrix, billboardModelMatrix, sizeof(modelMatrix));
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
        uint64_t state =
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_BLEND_ALPHA;

        if (drawItem.arpgPlayerPuppet)
        {
            state |= BGFX_STATE_DEPTH_TEST_ALWAYS;
        }
        else
        {
            state |= BGFX_STATE_WRITE_Z | BGFX_STATE_DEPTH_TEST_LEQUAL;
        }

        bgfx::setState(state);
        bgfx::submit(viewId, m_billboardProgramHandle);

        if (m_logIndoorPerformanceDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.renderActorSpriteSubmits;
        }
    }

    const auto appendWorldQuadVertices =
        [](std::vector<TerrainVertex> &vertices,
            const bx::Vec3 &center,
            const bx::Vec3 &right,
            const bx::Vec3 &up,
            uint32_t colorAbgr)
        {
            vertices.push_back(
                {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, colorAbgr});
            vertices.push_back(
                {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, colorAbgr});
            vertices.push_back(
                {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, colorAbgr});
            vertices.push_back(
                {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, colorAbgr});
            vertices.push_back(
                {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, colorAbgr});
            vertices.push_back(
                {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, colorAbgr});
        };

    std::vector<TerrainVertex> healthBarVertices;
    std::vector<TerrainVertex> arpgPlayerHealthBarVertices;

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        if (!drawItem.hasHealthBar)
        {
            continue;
        }

        std::vector<TerrainVertex> &targetHealthBarVertices =
            drawItem.arpgPlayerPuppet ? arpgPlayerHealthBarVertices : healthBarVertices;
        const float barScale = std::max(0.65f, drawItem.healthBarScale);
        const float barWidth = 92.0f * barScale;
        const float barHeight = 11.0f * barScale;
        const bx::Vec3 center = {
            static_cast<float>(drawItem.x),
            static_cast<float>(drawItem.y),
            drawItem.healthBarZ
        };
        const bx::Vec3 shadowCenter = {
            center.x - cameraUp.x * 3.0f * barScale,
            center.y - cameraUp.y * 3.0f * barScale,
            center.z - cameraUp.z * 3.0f * barScale
        };
        const bx::Vec3 frameRight = {
            cameraRight.x * barWidth * 0.5f,
            cameraRight.y * barWidth * 0.5f,
            cameraRight.z * barWidth * 0.5f
        };
        const bx::Vec3 frameUp = {
            cameraUp.x * barHeight * 0.5f,
            cameraUp.y * barHeight * 0.5f,
            cameraUp.z * barHeight * 0.5f
        };
        appendWorldQuadVertices(
            targetHealthBarVertices,
            shadowCenter,
            frameRight,
            frameUp,
            makeAbgrAlpha(0, 0, 0, 150));
        appendWorldQuadVertices(
            targetHealthBarVertices,
            center,
            frameRight,
            frameUp,
            makeAbgrAlpha(18, 12, 10, 230));

        const float innerWidth = std::max(2.0f, barWidth - 6.0f * barScale);
        const float innerHeight = std::max(2.0f, barHeight - 4.0f * barScale);
        const float fillWidth = std::max(1.0f, innerWidth * drawItem.healthRatio);
        const float fillOffset = (innerWidth - fillWidth) * 0.5f;
        const bx::Vec3 fillCenter = {
            center.x - cameraRight.x * fillOffset,
            center.y - cameraRight.y * fillOffset,
            center.z - cameraRight.z * fillOffset
        };
        const bx::Vec3 fillRight = {
            cameraRight.x * fillWidth * 0.5f,
            cameraRight.y * fillWidth * 0.5f,
            cameraRight.z * fillWidth * 0.5f
        };
        const bx::Vec3 fillUp = {
            cameraUp.x * innerHeight * 0.5f,
            cameraUp.y * innerHeight * 0.5f,
            cameraUp.z * innerHeight * 0.5f
        };
        appendWorldQuadVertices(
            targetHealthBarVertices,
            fillCenter,
            fillRight,
            fillUp,
            makeAbgrAlpha(177, 25, 28, 245));

        const bx::Vec3 glossCenter = {
            fillCenter.x + cameraUp.x * innerHeight * 0.22f,
            fillCenter.y + cameraUp.y * innerHeight * 0.22f,
            fillCenter.z + cameraUp.z * innerHeight * 0.22f
        };
        const bx::Vec3 glossUp = {
            cameraUp.x * innerHeight * 0.16f,
            cameraUp.y * innerHeight * 0.16f,
            cameraUp.z * innerHeight * 0.16f
        };
        appendWorldQuadVertices(
            targetHealthBarVertices,
            glossCenter,
            fillRight,
            glossUp,
            makeAbgrAlpha(255, 108, 82, 155));
    }

    const auto submitHealthBarVertices =
        [&](const std::vector<TerrainVertex> &vertices, uint64_t depthState)
        {
            if (vertices.empty()
                || !bgfx::isValid(m_programHandle)
                || bgfx::getAvailTransientVertexBuffer(
                    static_cast<uint32_t>(vertices.size()),
                    TerrainVertex::ms_layout) < vertices.size())
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(vertices.size()),
                TerrainVertex::ms_layout);
            std::memcpy(
                transientVertexBuffer.data,
                vertices.data(),
                vertices.size() * sizeof(TerrainVertex));

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | depthState
                | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(viewId, m_programHandle);
        };

    submitHealthBarVertices(healthBarVertices, BGFX_STATE_DEPTH_TEST_LEQUAL);
    submitHealthBarVertices(arpgPlayerHealthBarVertices, BGFX_STATE_DEPTH_TEST_ALWAYS);
}

void IndoorRenderer::renderSpriteObjectBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask,
    const std::vector<std::vector<IndoorVisibilityFrustum>> &visibleSectorFrustums,
    const IndoorLightingFrame &lightingFrame,
    bool spriteOutlineEnabled,
    const GameplayContextActionState *pContextActionState,
    LightingStats *pLightingStats
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

    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    float billboardModelMatrix[16] = {};
    bx::mtxInverse(billboardModelMatrix, pViewMatrix);
    const float aspectRatio =
        m_lastRenderHeight > 0
        ? static_cast<float>(std::max(m_lastRenderWidth, 1)) / static_cast<float>(m_lastRenderHeight)
        : 1.0f;
    const std::array<IndoorVisibilityPlane, 4> frustumPlanes =
        buildIndoorBillboardFrustumPlanes(cameraPosition, m_cameraYawRadians, m_cameraPitchRadians, aspectRatio);
    const auto spriteBillboardVisible =
        [&frustumPlanes, &visibleSectorFrustums](int16_t sectorId, float x, float y, float z,
            const SpriteFrameEntry &frame,
            const BillboardTextureHandle &texture) -> bool
        {
            if (texture.width <= 0 || texture.height <= 0)
            {
                return false;
            }

            const float spriteScale = std::max(frame.scale, 0.01f);
            const float worldWidth = static_cast<float>(texture.width) * spriteScale;
            const float worldHeight = static_cast<float>(texture.height) * spriteScale;
            const bool centerAnchored = SpriteFrameTable::hasFlag(frame.flags, SpriteFrameFlag::Center);
            const bx::Vec3 center = {
                x,
                y,
                centerAnchored ? z : z + worldHeight * 0.5f
            };
            const float radius = std::sqrt((worldWidth * 0.5f) * (worldWidth * 0.5f)
                + (worldHeight * 0.5f) * (worldHeight * 0.5f));
            return billboardSphereInFrustum(center, radius, frustumPlanes)
                && sphereIntersectsVisibleSectorFrustums(sectorId, center, radius, visibleSectorFrustums);
        };

    struct BillboardDrawItem
    {
        size_t objectIndex = static_cast<size_t>(-1);
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        int16_t sectorId = -1;
        const SpriteFrameEntry *pFrame = nullptr;
        const BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        bool hovered = false;
        bool projectile = false;
        bool impact = false;
        uint32_t hoveredOutlineColorAbgr = 0;
        float distanceSquared = 0.0f;
    };

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::vector<RuntimeSpriteObjectBillboard> runtimeBillboards =
        mapDeltaData && m_objectTable
        ? buildRuntimeSpriteObjectBillboards(*m_objectTable, m_pItemTable, *mapDeltaData, &visibleSectorMask)
        : std::vector<RuntimeSpriteObjectBillboard>{};
    std::vector<BillboardDrawItem> drawItems;
    const bool useRuntimeBillboards = mapDeltaData.has_value() && m_pSceneRuntime != nullptr;
    const size_t staticBillboardCount =
        m_indoorSpriteObjectBillboardSet ? m_indoorSpriteObjectBillboardSet->billboards.size() : 0;
    const std::optional<size_t> hoveredWorldItemIndex =
        m_cachedInspectHitValid && m_cachedInspectHit.kind == "object" && m_cachedInspectHit.hasContainingItem
        ? std::optional<size_t>(m_cachedInspectHit.index)
        : std::nullopt;
    const GameplayWorldHit *pContextActionHit = selectedContextActionWorldHit(pContextActionState);
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
            float velocityX,
            float velocityY,
            int16_t sectorId,
            uint32_t timeTicks,
            bool forceLog = false,
            bool impact = false)
        {
            uint16_t spriteFrameIndex = cachedSpriteFrameIndex;
            const char *pResolutionSource = cachedSpriteFrameIndex != 0 ? "cached" : "none";

            if (spriteFrameIndex == 0 && !spriteName.empty())
            {
                const std::optional<uint16_t> spriteFrameIndexByName =
                    pSpriteFrameTable->findFrameIndexBySpriteName(spriteName);

                if (spriteFrameIndexByName)
                {
                    spriteFrameIndex = *spriteFrameIndexByName;
                    pResolutionSource = "name";
                }
            }

            if (spriteFrameIndex == 0)
            {
                spriteFrameIndex = spriteId;
                pResolutionSource = "id";
            }

            if (spriteFrameIndex == 0)
            {
                if (forceLog)
                {
                    std::cout << "Indoor projectile draw skipped"
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " reason=no_frame_index\n";
                }
                return;
            }

            const SpriteFrameEntry *pFrame =
                pSpriteFrameTable->getFrame(spriteFrameIndex, timeTicks);

            if (pFrame == nullptr)
            {
                if (forceLog)
                {
                    std::cout << "Indoor projectile draw skipped"
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " frameIndex=" << spriteFrameIndex
                              << " source=" << pResolutionSource
                              << " reason=frame_missing\n";
                }
                return;
            }

            const float velocityLengthSquared = velocityX * velocityX + velocityY * velocityY;
            int octant = 0;

            if (velocityLengthSquared > 0.000001f)
            {
                const float angleToCamera = std::atan2(y - cameraPosition.y, x - cameraPosition.x);
                const float projectileYawRadians = std::atan2(velocityY, velocityX);
                const float octantAngle = projectileYawRadians - angleToCamera + Pi + (Pi / 8.0f);
                octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            }

            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                if (forceLog)
                {
                    std::cout << "Indoor projectile draw skipped"
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " frameIndex=" << spriteFrameIndex
                              << " source=" << pResolutionSource
                              << " texture=\"" << resolvedTexture.textureName << "\""
                              << " palette=" << pFrame->paletteId
                              << " reason=texture_missing\n";
                }
                return;
            }

            if (!spriteBillboardVisible(sectorId, x, y, z, *pFrame, *pTexture))
            {
                if (forceLog)
                {
                    std::cout << "Indoor projectile draw skipped"
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " frameIndex=" << spriteFrameIndex
                              << " source=" << pResolutionSource
                              << " pos=(" << x << ", " << y << ", " << z << ")"
                              << " reason=not_visible\n";
                }
                return;
            }

            if (forceLog)
            {
                std::cout << "Indoor projectile draw"
                          << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                          << " spriteId=" << spriteId
                          << " frameIndex=" << spriteFrameIndex
                          << " source=" << pResolutionSource
                          << " texture=\"" << resolvedTexture.textureName << "\""
                          << " palette=" << pFrame->paletteId
                          << " texSize=(" << pTexture->width << ", " << pTexture->height << ")"
                          << " pos=(" << x << ", " << y << ", " << z << ")"
                          << " sectorId=" << sectorId
                          << " ageTicks=" << timeTicks
                          << '\n';
            }

            const float deltaX = x - cameraPosition.x;
            const float deltaY = y - cameraPosition.y;
            const float deltaZ = z - cameraPosition.z;

            BillboardDrawItem drawItem = {};
            drawItem.x = x;
            drawItem.y = y;
            drawItem.z = z;
            drawItem.sectorId = sectorId;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.projectile = !impact;
            drawItem.impact = impact;
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            drawItems.push_back(drawItem);
        };

    if (useRuntimeBillboards)
    {
        for (const RuntimeSpriteObjectBillboard &billboard : runtimeBillboards)
        {
            if (!isRenderSectorVisible(billboard.sectorId, visibleSectorMask))
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

            if (!spriteBillboardVisible(
                    billboard.sectorId,
                    static_cast<float>(billboard.x),
                    static_cast<float>(billboard.y),
                    static_cast<float>(billboard.z),
                    *pFrame,
                    *pTexture))
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
            drawItem.sectorId = billboard.sectorId;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            const bool contextHighlighted =
                contextActionHighlightsWorldItem(pContextActionHit, billboard.objectIndex);
            drawItem.hovered =
                contextHighlighted
                || (spriteOutlineEnabled && hoveredWorldItemIndex && *hoveredWorldItemIndex == billboard.objectIndex);
            drawItem.hoveredOutlineColorAbgr =
                drawItem.hovered
                    ? (contextHighlighted ? contextActionHighlightOutlineColor() : hoveredIndoorWorldItemOutlineColor())
                    : 0;
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            drawItems.push_back(drawItem);
        }
    }
    else
    {
        if (m_indoorSpriteObjectBillboardSet)
        {
            const auto appendStaticSpriteObjectDrawItem =
                [&](const SpriteObjectBillboard &billboard)
            {
                if (!isRenderSectorVisible(billboard.sectorId, visibleSectorMask))
                {
                    return;
                }

                const SpriteFrameEntry *pFrame =
                    pSpriteFrameTable->getFrame(
                        billboard.objectSpriteId,
                        billboard.timeSinceCreatedTicks
                    );

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

                if (!spriteBillboardVisible(
                        billboard.sectorId,
                        static_cast<float>(billboard.x),
                        static_cast<float>(billboard.y),
                        static_cast<float>(billboard.z),
                        *pFrame,
                        *pTexture))
                {
                    return;
                }

                const float deltaX = float(billboard.x) - cameraPosition.x;
                const float deltaY = float(billboard.y) - cameraPosition.y;
                const float deltaZ = float(billboard.z) - cameraPosition.z;

                BillboardDrawItem drawItem = {};
                drawItem.x = static_cast<float>(billboard.x);
                drawItem.y = static_cast<float>(billboard.y);
                drawItem.z = static_cast<float>(billboard.z);
                drawItem.sectorId = billboard.sectorId;
                drawItem.pFrame = pFrame;
                drawItem.pTexture = pTexture;
                drawItem.mirrored = resolvedTexture.mirrored;
                drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
                drawItems.push_back(drawItem);
            };

            if (!m_staticSpriteObjectBillboardIndicesBySector.empty())
            {
                for (size_t sectorId = 0; sectorId < m_staticSpriteObjectBillboardIndicesBySector.size(); ++sectorId)
                {
                    if (!isRenderSectorVisible(static_cast<int16_t>(sectorId), visibleSectorMask))
                    {
                        continue;
                    }

                    for (size_t billboardIndex : m_staticSpriteObjectBillboardIndicesBySector[sectorId])
                    {
                        if (billboardIndex < m_indoorSpriteObjectBillboardSet->billboards.size())
                        {
                            appendStaticSpriteObjectDrawItem(
                                m_indoorSpriteObjectBillboardSet->billboards[billboardIndex]);
                        }
                    }
                }
            }
            else
            {
                for (const SpriteObjectBillboard &billboard : m_indoorSpriteObjectBillboardSet->billboards)
                {
                    appendStaticSpriteObjectDrawItem(billboard);
                }
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
                projectile.velocityX,
                projectile.velocityY,
                projectile.sectorId,
                projectile.timeSinceCreatedTicks);
        }

        for (const GameplayProjectileImpactPresentationState &impact : impacts)
        {
            const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
                impact.sourceSpellId,
                impact.sourceObjectName,
                impact.sourceObjectSpriteName,
                impact.sourceObjectFlags);

            if (FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe)
                && !FxRecipes::projectileRecipeShowsImpactBillboard(recipe))
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
                0.0f,
                0.0f,
                impact.sectorId,
                impact.freezeAnimation ? 0u : impact.timeSinceCreatedTicks,
                impact.objectName.find("Trap") != std::string::npos,
                true);
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

    if (m_logIndoorPerformanceDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderSpriteObjectItems += drawItems.size();

        const BillboardTextureHandle *pLastTexture = nullptr;
        for (const BillboardDrawItem &drawItem : drawItems)
        {
            if (drawItem.projectile)
            {
                ++m_indoorPerformanceDiagnostics.renderSpriteObjectProjectiles;
            }

            if (drawItem.impact)
            {
                ++m_indoorPerformanceDiagnostics.renderSpriteObjectImpacts;
            }

            if (drawItem.pTexture != pLastTexture)
            {
                ++m_indoorPerformanceDiagnostics.renderSpriteObjectTextureSwitches;
                pLastTexture = drawItem.pTexture;
            }
        }
    }

    struct LitSpriteObjectBillboardBatch
    {
        const BillboardTextureHandle *pTexture = nullptr;
        std::vector<LitBillboardVertex> vertices;
    };

    LitSpriteObjectBillboardBatch litBillboardBatch = {};
    litBillboardBatch.vertices.reserve(drawItems.size() * 6);

    const float litAmbient[4] = {1.0f, 1.0f, 1.0f, 0.0f};
    const float clearOverrideColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    const float clearOutlineParams[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    const float fogColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    const float fogDensities[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    const float fogDistances[4] = {4096.0f, 4096.0f, 4096.0f, 0.0f};

    const auto flushLitBillboardBatch =
        [&]()
        {
            if (litBillboardBatch.pTexture == nullptr || litBillboardBatch.vertices.empty())
            {
                litBillboardBatch.vertices.clear();
                litBillboardBatch.pTexture = nullptr;
                return;
            }

            if (bgfx::getAvailTransientVertexBuffer(
                    static_cast<uint32_t>(litBillboardBatch.vertices.size()),
                    LitBillboardVertex::ms_layout) >= litBillboardBatch.vertices.size())
            {
                bgfx::TransientVertexBuffer transientVertexBuffer = {};
                bgfx::allocTransientVertexBuffer(
                    &transientVertexBuffer,
                    static_cast<uint32_t>(litBillboardBatch.vertices.size()),
                    LitBillboardVertex::ms_layout);
                std::memcpy(
                    transientVertexBuffer.data,
                    litBillboardBatch.vertices.data(),
                    static_cast<size_t>(litBillboardBatch.vertices.size() * sizeof(LitBillboardVertex)));

                float modelMatrix[16] = {};
                std::memcpy(modelMatrix, billboardModelMatrix, sizeof(modelMatrix));
                bgfx::setTransform(modelMatrix);
                bgfx::setVertexBuffer(
                    0,
                    &transientVertexBuffer,
                    0,
                    static_cast<uint32_t>(litBillboardBatch.vertices.size()));
                bindTexture(
                    0,
                    m_textureSamplerHandle,
                    litBillboardBatch.pTexture->textureHandle,
                    TextureFilterProfile::Billboard,
                    BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                bgfx::setUniform(m_billboardAmbientUniformHandle, litAmbient);
                bgfx::setUniform(m_billboardOverrideColorUniformHandle, clearOverrideColor);
                bgfx::setUniform(m_billboardOutlineParamsUniformHandle, clearOutlineParams);
                bgfx::setUniform(m_billboardFogColorUniformHandle, fogColor);
                bgfx::setUniform(m_billboardFogDensitiesUniformHandle, fogDensities);
                bgfx::setUniform(m_billboardFogDistancesUniformHandle, fogDistances);
                bgfx::setState(IndoorBillboardDrawState);
                bgfx::submit(viewId, m_billboardProgramHandle);

                if (m_logIndoorPerformanceDiagnostics)
                {
                    ++m_indoorPerformanceDiagnostics.renderSpriteObjectBatchSubmits;
                    m_indoorPerformanceDiagnostics.renderSpriteObjectBatchedItems +=
                        litBillboardBatch.vertices.size() / 6;
                }
            }

            litBillboardBatch.vertices.clear();
            litBillboardBatch.pTexture = nullptr;
        };

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = float(texture.width) * spriteScale;
        const float worldHeight = float(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = spriteFrameBillboardCenter(
            drawItem.x,
            drawItem.y,
            drawItem.z,
            frame,
            cameraUp,
            worldHeight);
        const bx::Vec3 viewCenter = transformIndoorPoint(center, pViewMatrix);
        const bx::Vec3 right = {halfWidth, 0.0f, 0.0f};
        const bx::Vec3 up = {0.0f, worldHeight * 0.5f, 0.0f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        if (drawItem.hovered)
        {
            flushLitBillboardBatch();

            const float paddingU = HoveredActorOutlineThicknessPixels / static_cast<float>(texture.width);
            const float paddingV = HoveredActorOutlineThicknessPixels / static_cast<float>(texture.height);
            const float outlinedHalfWidth =
                (static_cast<float>(texture.width) * spriteScale
                    + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale) * 0.5f;
            const float outlinedHalfHeight =
                (static_cast<float>(texture.height) * spriteScale
                    + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale) * 0.5f;
            const bx::Vec3 outlineRight = {outlinedHalfWidth, 0.0f, 0.0f};
            const bx::Vec3 outlineUp = {0.0f, outlinedHalfHeight, 0.0f};
            const float outlineU0 = drawItem.mirrored ? 1.0f + paddingU : -paddingU;
            const float outlineU1 = drawItem.mirrored ? -paddingU : 1.0f + paddingU;
            const float outlineVTop = -paddingV;
            const float outlineVBottom = 1.0f + paddingV;
            const uint32_t vertexColorAbgr = makeAbgr(0, 0, 0);
            std::array<LitBillboardVertex, 6> outlineVertices = {{
                {
                    viewCenter.x - outlineRight.x - outlineUp.x,
                    viewCenter.y - outlineRight.y - outlineUp.y,
                    viewCenter.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    viewCenter.x - outlineRight.x + outlineUp.x,
                    viewCenter.y - outlineRight.y + outlineUp.y,
                    viewCenter.z - outlineRight.z + outlineUp.z,
                    outlineU0,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    viewCenter.x + outlineRight.x + outlineUp.x,
                    viewCenter.y + outlineRight.y + outlineUp.y,
                    viewCenter.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    viewCenter.x - outlineRight.x - outlineUp.x,
                    viewCenter.y - outlineRight.y - outlineUp.y,
                    viewCenter.z - outlineRight.z - outlineUp.z,
                    outlineU0,
                    outlineVBottom,
                    vertexColorAbgr
                },
                {
                    viewCenter.x + outlineRight.x + outlineUp.x,
                    viewCenter.y + outlineRight.y + outlineUp.y,
                    viewCenter.z + outlineRight.z + outlineUp.z,
                    outlineU1,
                    outlineVTop,
                    vertexColorAbgr
                },
                {
                    viewCenter.x + outlineRight.x - outlineUp.x,
                    viewCenter.y + outlineRight.y - outlineUp.y,
                    viewCenter.z + outlineRight.z - outlineUp.z,
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
                std::memcpy(outlineModelMatrix, billboardModelMatrix, sizeof(outlineModelMatrix));
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
                    IndoorBillboardDrawState);
                bgfx::submit(viewId, m_billboardProgramHandle);

                if (m_logIndoorPerformanceDiagnostics)
                {
                    ++m_indoorPerformanceDiagnostics.renderSpriteObjectOutlineSubmits;
                }
            }
        }

        const uint32_t vertexColorAbgr = makeAbgr(0, 0, 0);
        std::array<LitBillboardVertex, 6> vertices = {{
            {
                viewCenter.x - right.x - up.x,
                viewCenter.y - right.y - up.y,
                viewCenter.z - right.z - up.z,
                u0,
                1.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x - right.x + up.x,
                viewCenter.y - right.y + up.y,
                viewCenter.z - right.z + up.z,
                u0,
                0.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x + right.x + up.x,
                viewCenter.y + right.y + up.y,
                viewCenter.z + right.z + up.z,
                u1,
                0.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x - right.x - up.x,
                viewCenter.y - right.y - up.y,
                viewCenter.z - right.z - up.z,
                u0,
                1.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x + right.x + up.x,
                viewCenter.y + right.y + up.y,
                viewCenter.z + right.z + up.z,
                u1,
                0.0f,
                vertexColorAbgr
            },
            {
                viewCenter.x + right.x - up.x,
                viewCenter.y + right.y - up.y,
                viewCenter.z + right.z - up.z,
                u1,
                1.0f,
                vertexColorAbgr
            }
        }};

        const bool batchableLitBillboard =
            !drawItem.hovered && SpriteFrameTable::hasFlag(frame.flags, SpriteFrameFlag::Lit);

        if (batchableLitBillboard)
        {
            if (litBillboardBatch.pTexture != &texture)
            {
                flushLitBillboardBatch();
                litBillboardBatch.pTexture = &texture;
            }

            litBillboardBatch.vertices.insert(
                litBillboardBatch.vertices.end(),
                vertices.begin(),
                vertices.end());
            continue;
        }

        flushLitBillboardBatch();

        const std::array<float, 4> ambient =
            billboardLightingUniform(lightingFrame, frame, center, drawItem.sectorId, pLightingStats);

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
        std::memcpy(modelMatrix, billboardModelMatrix, sizeof(modelMatrix));
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
            IndoorBillboardDrawState
        );
        bgfx::submit(viewId, m_billboardProgramHandle);

        if (m_logIndoorPerformanceDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.renderSpriteObjectSubmits;
            ++m_indoorPerformanceDiagnostics.renderSpriteObjectUnbatchedItems;
        }
    }

    flushLitBillboardBatch();
}

void IndoorRenderer::renderContextActionGeometryHighlight(
    uint16_t viewId,
    const GameplayContextActionState *pContextActionState,
    bool arpgMode)
{
    const GameplayWorldHit *pHit = selectedContextActionWorldHit(pContextActionState);

    if (pHit == nullptr
        || pHit->kind != GameplayWorldHitKind::EventTarget
        || !pHit->eventTarget.has_value()
        || !m_indoorMapData
        || !bgfx::isValid(m_programHandle))
    {
        return;
    }

    std::vector<size_t> faceIndices;
    const GameplayEventTargetHit &eventTarget = *pHit->eventTarget;

    if (eventTarget.targetKind == GameplayWorldEventTargetKind::Surface
        && eventTarget.secondaryIndex != GameplayInvalidWorldIndex)
    {
        faceIndices.push_back(eventTarget.secondaryIndex);
    }
    else if (eventTarget.targetKind == GameplayWorldEventTargetKind::Mechanism)
    {
        const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

        if (eventTarget.secondaryIndex != GameplayInvalidWorldIndex
            && eventTarget.secondaryIndex < m_indoorMapData->faces.size())
        {
            faceIndices.push_back(eventTarget.secondaryIndex);
        }
        else if (mapDeltaData && eventTarget.targetIndex < mapDeltaData->doors.size())
        {
            const MapDeltaDoor &door = mapDeltaData->doors[eventTarget.targetIndex];

            if (indoorDoorMechanismSuppressedForContextAction(door, runtimeEventRuntimeState()))
            {
                return;
            }

            for (uint16_t faceId : door.faceIds)
            {
                faceIndices.push_back(faceId);
            }
        }
    }

    if (faceIndices.empty())
    {
        return;
    }

    const uint32_t color = contextActionGeometryHighlightColor(m_elapsedTime);
    std::vector<TerrainVertex> highlightVertices;
    highlightVertices.reserve(faceIndices.size() * 12);
    IndoorFaceGeometryCache geometryCache(m_indoorMapData->faces.size());
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    geometryCache.setAttributeOverrides(mapDeltaData ? &*mapDeltaData : nullptr);

    for (size_t faceIndex : faceIndices)
    {
        if (faceIndex >= m_indoorMapData->faces.size())
        {
            continue;
        }

        const IndoorFace &face = m_indoorMapData->faces[faceIndex];

        if (!indoorFaceHasActualEvent(m_pSceneRuntime, face))
        {
            continue;
        }

        if (eventTarget.targetKind == GameplayWorldEventTargetKind::Mechanism)
        {
            if (face.facetType == 3 || indoorFaceMarkedAsCeiling(*m_indoorMapData, faceIndex, face))
            {
                continue;
            }
        }
        else if (indoorFaceSuppressedForContextAction(
                *m_indoorMapData,
                faceIndex,
                face,
                eventTarget.contextActionMetadata,
                eventTarget.openedChestIds))
        {
            continue;
        }

        const IndoorFaceGeometryData *pGeometry =
            geometryCache.geometryForFace(*m_indoorMapData, m_renderVertices, faceIndex);

        if (pGeometry == nullptr || pGeometry->vertices.size() < 3)
        {
            continue;
        }

        const bx::Vec3 normal = vecLength(pGeometry->normal) > 0.0001f
            ? vecNormalize(pGeometry->normal)
            : bx::Vec3{0.0f, 0.0f, 0.0f};
        const bx::Vec3 offset = {normal.x * 1.5f, normal.y * 1.5f, normal.z * 1.5f};

        for (size_t triangleIndex = 1; triangleIndex + 1 < pGeometry->vertices.size(); ++triangleIndex)
        {
            const bx::Vec3 triangleVertices[3] = {
                pGeometry->vertices[0],
                pGeometry->vertices[triangleIndex],
                pGeometry->vertices[triangleIndex + 1]
            };

            for (const bx::Vec3 &vertex : triangleVertices)
            {
                highlightVertices.push_back(
                    {vertex.x + offset.x, vertex.y + offset.y, vertex.z + offset.z, color});
            }
        }
    }

    if (highlightVertices.empty()
        || bgfx::getAvailTransientVertexBuffer(
            static_cast<uint32_t>(highlightVertices.size()),
            TerrainVertex::ms_layout) < highlightVertices.size())
    {
        return;
    }

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(
        &transientVertexBuffer,
        static_cast<uint32_t>(highlightVertices.size()),
        TerrainVertex::ms_layout);
    std::memcpy(
        transientVertexBuffer.data,
        highlightVertices.data(),
        highlightVertices.size() * sizeof(TerrainVertex));

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(highlightVertices.size()));
    bgfx::setState(
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_DEPTH_TEST_LEQUAL
        | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, m_programHandle);
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
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    uint64_t revision = mapDeltaData ? mapDeltaData->surfaceRevision : 0;

    if (pEventRuntimeState != nullptr)
    {
        revision ^= pEventRuntimeState->outdoorSurfaceRevision + 0x9e3779b97f4a7c15ull + (revision << 6) + (revision >> 2);
    }

    return revision;
}

void IndoorRenderer::rebuildTexturedBatchBounds(TexturedBatch &batch)
{
    batch.hasBounds = false;

    if (batch.vertices.empty())
    {
        batch.boundsMin = {0.0f, 0.0f, 0.0f};
        batch.boundsMax = {0.0f, 0.0f, 0.0f};
        return;
    }

    batch.boundsMin = {
        std::numeric_limits<float>::infinity(),
        std::numeric_limits<float>::infinity(),
        std::numeric_limits<float>::infinity()
    };
    batch.boundsMax = {
        -std::numeric_limits<float>::infinity(),
        -std::numeric_limits<float>::infinity(),
        -std::numeric_limits<float>::infinity()
    };

    for (const TexturedVertex &vertex : batch.vertices)
    {
        batch.boundsMin.x = std::min(batch.boundsMin.x, vertex.x);
        batch.boundsMin.y = std::min(batch.boundsMin.y, vertex.y);
        batch.boundsMin.z = std::min(batch.boundsMin.z, vertex.z);
        batch.boundsMax.x = std::max(batch.boundsMax.x, vertex.x);
        batch.boundsMax.y = std::max(batch.boundsMax.y, vertex.y);
        batch.boundsMax.z = std::max(batch.boundsMax.z, vertex.z);
    }

    batch.hasBounds = true;
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
        m_indoorLightingSelectionCache.clear();
        m_faceBatchIndices.clear();
        m_faceVertexOffsets.clear();
        m_faceVertexCounts.clear();
        m_arpgModeOccludingFaceCandidates.clear();
        m_arpgModeOccludingFaceNeighbors.clear();
        m_texturedBatchVisualRevision = currentTexturedBatchVisualRevision();
        return true;
    }

    std::vector<TexturedBatch> previousBatches = std::move(m_texturedBatches);
    m_texturedBatches.clear();
    m_indoorLightingSelectionCache.clear();
    m_faceBatchIndices.assign(m_indoorMapData->faces.size(), -1);
    m_faceVertexOffsets.assign(m_indoorMapData->faces.size(), 0);
    m_faceVertexCounts.assign(m_indoorMapData->faces.size(), 0);

    std::unordered_map<std::string, size_t> batchIndicesByTexture;
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

    for (size_t faceIndex = 0; faceIndex < m_indoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_indoorMapData->faces[faceIndex];
        const std::string textureName = resolveFaceTextureName(faceIndex, face, eventRuntimeState);

        if (face.isPortal || textureName.empty() || face.vertexIndices.size() < 3)
        {
            continue;
        }

        if (!isFaceVisible(faceIndex, face, runtimeMapDeltaData(), eventRuntimeState))
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
        const bool ceilingFace = isCeilingFace(faceIndex, face);
        const std::string batchKey = normalizedTextureName
            + "#" + std::to_string(sectorId)
            + "#" + std::to_string(backSectorId)
            + "#" + (ceilingFace ? "ceiling" : "nonceiling");
        size_t batchIndex = 0;
        const std::unordered_map<std::string, size_t>::const_iterator batchIterator =
            batchIndicesByTexture.find(batchKey);

        if (batchIterator == batchIndicesByTexture.end())
        {
            TexturedBatch batch = {};
            batch.textureName = normalizedTextureName;
            batch.sectorId = sectorId;
            batch.backSectorId = backSectorId;
            batch.ceiling = ceilingFace;

            for (TexturedBatch &previousBatch : previousBatches)
            {
                if (previousBatch.textureName == normalizedTextureName
                    && previousBatch.sectorId == sectorId
                    && previousBatch.backSectorId == backSectorId
                    && previousBatch.ceiling == ceilingFace)
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
            batch.stableId = stableIndoorTexturedBatchId(
                batch.textureName,
                batch.sectorId,
                batch.backSectorId,
                batchIndex);
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

        TexturedBatch &batch = m_texturedBatches[batchIndex];
        batch.textureWidth = pTexture->width;
        batch.textureHeight = pTexture->height;

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

        m_faceBatchIndices[faceIndex] = static_cast<int32_t>(batchIndex);
        m_faceVertexOffsets[faceIndex] = static_cast<uint32_t>(batch.vertices.size());
        m_faceVertexCounts[faceIndex] = static_cast<uint32_t>(faceVertices.size());
        batch.vertices.insert(batch.vertices.end(), faceVertices.begin(), faceVertices.end());
    }

    for (TexturedBatch &batch : m_texturedBatches)
    {
        batch.vertexCount = static_cast<uint32_t>(batch.vertices.size());
        rebuildTexturedBatchBounds(batch);

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
    rebuildArpgModeOccludingFaceCandidates();
    return true;
}

bool IndoorRenderer::updateMovingMechanismFaceVertices(
    uint64_t &texturedBuildNanoseconds,
    uint64_t &uploadNanoseconds,
    size_t *pUpdatedFaceCount,
    size_t *pDirtyBatchCount
)
{
    const std::vector<size_t> faceIndices = collectMovingMechanismFaceIndices();
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();
    std::vector<uint8_t> dirtyBatchBounds(m_texturedBatches.size(), 0);
    size_t updatedFaceCount = 0;

    for (size_t faceIndex : faceIndices)
    {
        if (faceIndex >= m_faceBatchIndices.size())
        {
            continue;
        }

        const int32_t batchIndex = m_faceBatchIndices[faceIndex];

        if (batchIndex < 0 || static_cast<size_t>(batchIndex) >= m_texturedBatches.size())
        {
            if (faceIndex >= m_indoorMapData->faces.size())
            {
                continue;
            }

            const IndoorFace &face = m_indoorMapData->faces[faceIndex];
            const std::string textureName = resolveFaceTextureName(faceIndex, face, eventRuntimeState);

            if (face.isPortal || textureName.empty() || face.vertexIndices.size() < 3)
            {
                continue;
            }

            const std::string normalizedTextureName = toLowerCopy(textureName);
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

            if (!faceVertices.empty())
            {
                return false;
            }

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
        dirtyBatchBounds[static_cast<size_t>(batchIndex)] = 1;
        ++updatedFaceCount;

        const uint64_t uploadBeginTickCount = SDL_GetTicksNS();
        bgfx::update(
            batch.vertexBufferHandle,
            vertexOffset,
            bgfx::copy(faceVertices.data(), static_cast<uint32_t>(faceVertices.size() * sizeof(TexturedVertex)))
        );
        uploadNanoseconds += SDL_GetTicksNS() - uploadBeginTickCount;
    }

    size_t dirtyBatchCount = 0;

    for (size_t batchIndex = 0; batchIndex < dirtyBatchBounds.size(); ++batchIndex)
    {
        if (dirtyBatchBounds[batchIndex] != 0)
        {
            ++dirtyBatchCount;
            rebuildTexturedBatchBounds(m_texturedBatches[batchIndex]);
        }
    }

    if (pUpdatedFaceCount != nullptr)
    {
        *pUpdatedFaceCount = updatedFaceCount;
    }

    if (pDirtyBatchCount != nullptr)
    {
        *pDirtyBatchCount = dirtyBatchCount;
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
    m_indoorLightingSelectionCache.clear();
    m_indoorLightingSelectionFrame = 0;
    m_faceBatchIndices.clear();
    m_faceVertexOffsets.clear();
    m_faceVertexCounts.clear();
    m_arpgModeOccludingFaceCandidates.clear();
    m_arpgModeOccludingFaceNeighbors.clear();
    m_arpgModeOcclusionGeometryCache.reset(0);
    m_arpgModeRenderVisibilityCacheValid = false;
    m_arpgModeCameraVisibleSectorMaskCache.clear();
    m_arpgModeRenderVisibleSectorMaskCache.clear();
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
    m_arpgModeOcclusionGeometryCache.reset(m_indoorMapData->faces.size());
    m_arpgModeRenderVisibilityCacheValid = false;

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return true;
    }

    const std::vector<TerrainVertex> wireframeVertices =
        buildWireframeVertices(*m_indoorMapData, m_renderVertices, mapDeltaData, eventRuntimeState);
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

    const bool collectDiagnostics = m_logIndoorPerformanceDiagnostics;
    const uint64_t renderVerticesBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;

    if (!updateMovingMechanismRenderVertices())
    {
        return false;
    }
    m_arpgModeOcclusionGeometryCache.reset(m_indoorMapData->faces.size());
    m_arpgModeRenderVisibilityCacheValid = false;

    if (collectDiagnostics)
    {
        m_indoorPerformanceDiagnostics.movingRenderVerticesNanoseconds +=
            SDL_GetTicksNS() - renderVerticesBeginTickCount;
    }

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        ++m_inspectGeometryRevision;
        m_cachedInspectHitValid = false;
        return true;
    }

    if (!m_indoorTextureSet || texturedBatchesNeedFullRebuild())
    {
        const uint64_t rebuildBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
        const bool rebuilt = rebuildDerivedGeometryResources();

        if (collectDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.movingFullRebuilds;
            ++m_indoorPerformanceDiagnostics.movingFallbackFullRebuilds;
            m_indoorPerformanceDiagnostics.fullRebuildNanoseconds +=
                SDL_GetTicksNS() - rebuildBeginTickCount;
        }

        return rebuilt;
    }

    uint64_t texturedBuildNanoseconds = 0;
    uint64_t uploadNanoseconds = 0;
    size_t updatedFaceCount = 0;
    size_t dirtyBatchCount = 0;
    const uint64_t faceUpdateBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;

    if (!updateMovingMechanismFaceVertices(
            texturedBuildNanoseconds,
            uploadNanoseconds,
            &updatedFaceCount,
            &dirtyBatchCount))
    {
        const uint64_t rebuildBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
        const bool rebuilt = rebuildDerivedGeometryResources();

        if (collectDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.movingFullRebuilds;
            ++m_indoorPerformanceDiagnostics.movingFallbackFullRebuilds;
            m_indoorPerformanceDiagnostics.fullRebuildNanoseconds +=
                SDL_GetTicksNS() - rebuildBeginTickCount;
        }

        return rebuilt;
    }

    if (collectDiagnostics)
    {
        m_indoorPerformanceDiagnostics.movingFaceTotalNanoseconds +=
            SDL_GetTicksNS() - faceUpdateBeginTickCount;
        m_indoorPerformanceDiagnostics.movingFaceBuildNanoseconds += texturedBuildNanoseconds;
        m_indoorPerformanceDiagnostics.movingFaceUploadNanoseconds += uploadNanoseconds;
        m_indoorPerformanceDiagnostics.movingUpdatedFaces += updatedFaceCount;
        m_indoorPerformanceDiagnostics.movingDirtyBatches += dirtyBatchCount;
    }

    if (updatedFaceCount != 0)
    {
        rebuildArpgModeOccludingFaceCandidates();
    }

    ++m_inspectGeometryRevision;
    m_cachedInspectHitValid = false;
    return true;
}

bool IndoorRenderer::updateMovingMechanismRenderVertices()
{
    if (!m_indoorMapData)
    {
        return false;
    }

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (m_renderVertices.size() != m_indoorMapData->vertices.size())
    {
        m_renderVertices = buildIndoorMechanismAdjustedVertices(
            *m_indoorMapData,
            mapDeltaData ? &mapDeltaData.value() : nullptr,
            pEventRuntimeState);
        return true;
    }

    if (!mapDeltaData || pEventRuntimeState == nullptr)
    {
        return true;
    }

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
            pEventRuntimeState->mechanisms.find(door.doorId);

        if (mechanismIterator == pEventRuntimeState->mechanisms.end() || !mechanismIterator->second.isMoving)
        {
            continue;
        }

        const size_t movableVertexCount = std::min(
            door.vertexIds.size(),
            std::min(door.xOffsets.size(), std::min(door.yOffsets.size(), door.zOffsets.size()))
        );

        if (movableVertexCount == 0)
        {
            continue;
        }

        const float distance = mechanismIterator->second.currentDistance;
        const float directionX = static_cast<float>(door.directionX) / 65536.0f;
        const float directionY = static_cast<float>(door.directionY) / 65536.0f;
        const float directionZ = static_cast<float>(door.directionZ) / 65536.0f;

        for (size_t vertexOffsetIndex = 0; vertexOffsetIndex < movableVertexCount; ++vertexOffsetIndex)
        {
            const uint16_t vertexId = door.vertexIds[vertexOffsetIndex];

            if (vertexId >= m_renderVertices.size())
            {
                continue;
            }

            IndoorVertex &vertex = m_renderVertices[vertexId];
            vertex.x = static_cast<int>(std::lround(
                static_cast<float>(door.xOffsets[vertexOffsetIndex]) + directionX * distance));
            vertex.y = static_cast<int>(std::lround(
                static_cast<float>(door.yOffsets[vertexOffsetIndex]) + directionY * distance));
            vertex.z = static_cast<int>(std::lround(
                static_cast<float>(door.zOffsets[vertexOffsetIndex]) + directionZ * distance));
        }
    }

    return true;
}

bool IndoorRenderer::tryActivateInspectEvent(const InspectHit &inspectHit)
{
    if (!m_indoorMapData || m_pSceneRuntime == nullptr)
    {
        return false;
    }

    if (inspectHit.kind == "face"
        && !indoorFaceIsInteractionActivatable(inspectHit.attributes, inspectHit.cogTriggered))
    {
        EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

        if (pEventRuntimeState != nullptr)
        {
            pEventRuntimeState->lastActivationResult = "face target is hover-only or non-clickable";
        }

        return false;
    }

    std::optional<EventRuntimeState::ActiveDecorationContext> decorationContext;
    const uint16_t eventId = inspectHitEventId(inspectHit);

    if (inspectHit.kind == "entity"
        && resolveIndoorEntityScriptEventId(inspectHit.eventIdSecondary) == 0
        && m_indoorMapData)
    {
        const std::optional<IndoorInteractiveDecorationBinding> binding =
            resolveIndoorInteractiveDecorationBinding(
                m_indoorInteractiveDecorationDecorVarIndicesByEntity,
                m_indoorInteractiveDecorationBaseEventIdsByEntity,
                m_indoorInteractiveDecorationEventCountsByEntity,
                m_indoorInteractiveDecorationHideWhenClearedByEntity,
                inspectHit.index);

        if (binding && eventId != 0)
        {
            EventRuntimeState::ActiveDecorationContext context = {};
            context.decorVarIndex = binding->decorVarIndex;
            context.baseEventId = binding->baseEventId;
            context.currentEventId = eventId;
            context.eventCount = binding->eventCount;
            context.hideWhenCleared = binding->hideWhenCleared;
            decorationContext = context;
        }
    }

    if (eventId == 0)
    {
        EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

        if (pEventRuntimeState != nullptr)
        {
            pEventRuntimeState->lastActivationResult = "no activatable event on hovered target";
        }

        return false;
    }

    if (!m_pSceneRuntime->activateEvent(eventId, inspectHit.kind, inspectHit.index, decorationContext))
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
    const uint32_t effectiveAttributes =
        indoorMapDeltaData && faceIndex < indoorMapDeltaData->faceAttributes.size()
            ? indoorMapDeltaData->faceAttributes[faceIndex]
            : face.attributes;
    const std::string effectiveTextureName = resolveFaceTextureName(faceIndex, face, eventRuntimeState);

    if (face.isPortal || effectiveTextureName.empty() || face.vertexIndices.size() < 3)
    {
        return vertices;
    }

    if (!isFaceVisible(faceIndex, face, indoorMapDeltaData, eventRuntimeState))
    {
        return vertices;
    }

    if (toLowerCopy(effectiveTextureName) != toLowerCopy(texture.textureName))
    {
        return vertices;
    }

    const bx::Vec3 faceNormal = computeFaceNormal(transformedVertices, face);
    const std::array<float, 4> flowInfo =
        indoorFaceFlowInfo(effectiveAttributes, face.facetType, texture.width, texture.height);
    const float textureCoordinateScale = indoorFaceTextureCoordinateScale(effectiveAttributes, face.facetType);

    const std::optional<MechanismFaceTextureState> mechanismFaceTextureState =
        findMechanismFaceTextureState(faceIndex, indoorMapDeltaData, eventRuntimeState);
    const bool useGeometryTextureCoordinates = mechanismFaceTextureState.has_value();
    std::vector<float> geometryUs;
    std::vector<float> geometryVs;
    float geometryDeltaU = 0.0f;
    float geometryDeltaV = 0.0f;

    if (useGeometryTextureCoordinates)
    {
        bx::Vec3 axisU = {0.0f, 0.0f, 0.0f};
        bx::Vec3 axisV = {0.0f, 0.0f, 0.0f};

        if (vecDot(faceNormal, faceNormal) <= 0.0001f
            || !calculateFaceTextureAxes(face, vecNormalize(faceNormal), axisU, axisV))
        {
            return vertices;
        }

        geometryUs.reserve(face.vertexIndices.size());
        geometryVs.reserve(face.vertexIndices.size());
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
            geometryUs.push_back(pointU);
            geometryVs.push_back(pointV);
            minU = std::min(minU, pointU);
            minV = std::min(minV, pointV);
            maxU = std::max(maxU, pointU);
            maxV = std::max(maxV, pointV);
        }

        if (hasFaceAttribute(face.attributes, FaceAttribute::TextureAlignLeft))
        {
            geometryDeltaU -= minU;
        }
        else if (hasFaceAttribute(face.attributes, FaceAttribute::TextureAlignRight))
        {
            geometryDeltaU -= maxU + static_cast<float>(texture.width);
        }

        if (hasFaceAttribute(face.attributes, FaceAttribute::TextureAlignDown))
        {
            geometryDeltaV -= minV;
        }
        else if (hasFaceAttribute(face.attributes, FaceAttribute::TextureAlignBottom))
        {
            geometryDeltaV -= maxV + static_cast<float>(texture.height);
        }

        if (mechanismFaceTextureState && hasFaceAttribute(face.attributes, FaceAttribute::TextureMoveByDoor))
        {
            geometryDeltaU = -vecDot(mechanismFaceTextureState->direction, axisU) * mechanismFaceTextureState->distance;
            geometryDeltaV = -vecDot(mechanismFaceTextureState->direction, axisV) * mechanismFaceTextureState->distance;

            if (mechanismFaceTextureState->pDoor != nullptr)
            {
                if (mechanismFaceTextureState->faceOffset < mechanismFaceTextureState->pDoor->deltaUs.size())
                {
                    geometryDeltaU += static_cast<float>(
                        mechanismFaceTextureState->pDoor->deltaUs[mechanismFaceTextureState->faceOffset]);
                }

                if (mechanismFaceTextureState->faceOffset < mechanismFaceTextureState->pDoor->deltaVs.size())
                {
                    geometryDeltaV += static_cast<float>(
                        mechanismFaceTextureState->pDoor->deltaVs[mechanismFaceTextureState->faceOffset]);
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
        const auto faceVerticesAreAdjacent =
            [&face](size_t first, size_t second) -> bool
            {
                const size_t vertexCount = face.vertexIndices.size();
                return (first + 1) % vertexCount == second || (second + 1) % vertexCount == first;
            };
        float boundaryEdgeMask = 0.0f;

        if (faceVerticesAreAdjacent(triangleVertexIndices[1], triangleVertexIndices[2]))
        {
            boundaryEdgeMask += 1.0f;
        }

        if (faceVerticesAreAdjacent(triangleVertexIndices[2], triangleVertexIndices[0]))
        {
            boundaryEdgeMask += 2.0f;
        }

        if (faceVerticesAreAdjacent(triangleVertexIndices[0], triangleVertexIndices[1]))
        {
            boundaryEdgeMask += 4.0f;
        }

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
            texturedVertex.secretPulse = secretFaceVertexFlag(effectiveAttributes);
            texturedVertex.barycentric0 = triangleVertexSlot == 0 ? 1.0f : 0.0f;
            texturedVertex.barycentric1 = triangleVertexSlot == 1 ? 1.0f : 0.0f;
            texturedVertex.barycentric2 = triangleVertexSlot == 2 ? 1.0f : 0.0f;
            texturedVertex.boundaryEdgeMask = boundaryEdgeMask;
            texturedVertex.flowUPerSecond = flowInfo[0];
            texturedVertex.flowVPerSecond = flowInfo[1];
            texturedVertex.lavaFlow = flowInfo[2];
            texturedVertex.fluidFlow = flowInfo[3];

            if (useGeometryTextureCoordinates
                && faceVertexIndex < geometryUs.size()
                && faceVertexIndex < geometryVs.size())
            {
                texturedVertex.u =
                    (geometryUs[faceVertexIndex] + geometryDeltaU)
                    * textureCoordinateScale
                    / static_cast<float>(texture.width);
                texturedVertex.v =
                    (geometryVs[faceVertexIndex] + geometryDeltaV)
                    * textureCoordinateScale
                    / static_cast<float>(texture.height);
            }
            else
            {
                texturedVertex.u =
                    static_cast<float>(face.textureDeltaU + face.textureUs[faceVertexIndex])
                    * textureCoordinateScale
                    / static_cast<float>(texture.width);
                texturedVertex.v =
                    static_cast<float>(face.textureDeltaV + face.textureVs[faceVertexIndex])
                    * textureCoordinateScale
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
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = indoorMapData.faces[faceIndex];

        if (face.vertexIndices.size() < 3)
        {
            continue;
        }

        const uint32_t effectiveAttributes =
            mapDeltaData && faceIndex < mapDeltaData->faceAttributes.size()
                ? mapDeltaData->faceAttributes[faceIndex]
                : face.attributes;

        if (face.isPortal || hasFaceAttribute(effectiveAttributes, FaceAttribute::IsPortal))
        {
            continue;
        }

        if (m_arpgModeCameraActive && isCeilingFace(faceIndex, face))
        {
            continue;
        }

        if (!visibleSectorMask.empty()
            && !isSectorVisible(static_cast<int16_t>(face.roomNumber), visibleSectorMask)
            && !isSectorVisible(static_cast<int16_t>(face.roomBehindNumber), visibleSectorMask))
        {
            continue;
        }

        if (hasFaceAttribute(effectiveAttributes, FaceAttribute::Invisible)
            || !isFaceVisible(faceIndex, face, mapDeltaData, eventRuntimeState))
        {
            continue;
        }

        if (!indoorFaceRayBoundsHit(face, vertices, rayOrigin, rayDirection, bestDistance))
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
                bestHit.attributes = effectiveAttributes;
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

    if (m_indoorDecorationBillboardSet)
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
        const uint32_t animationTimeTicks = currentAnimationTicks();

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

        const auto resolveDecorationBillboardSpriteId =
            [this, &eventRuntimeState](const DecorationBillboard &billboard, bool &hidden)
            {
                hidden = false;

                if (!m_indoorDecorationBillboardSet || !eventRuntimeState.has_value())
                {
                    return billboard.spriteId;
                }

                const uint32_t overrideKey = billboard.spriteOverrideKey();
                const auto overrideIterator = eventRuntimeState->spriteOverrides.find(overrideKey);

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
                        m_indoorDecorationBillboardSet->decorationTable.findByInternalName(
                            *overrideIterator->second.textureName))
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

        const auto decorationHasInteraction =
            [this, &eventRuntimeState](const DecorationBillboard &billboard)
            {
                if (billboard.eventIdSecondary != 0)
                {
                    return true;
                }

                if (!eventRuntimeState.has_value())
                {
                    return false;
                }

                return resolveIndoorInteractiveDecorationBinding(
                    m_indoorInteractiveDecorationDecorVarIndicesByEntity,
                    m_indoorInteractiveDecorationBaseEventIdsByEntity,
                    m_indoorInteractiveDecorationEventCountsByEntity,
                    m_indoorInteractiveDecorationHideWhenClearedByEntity,
                    billboard.entityIndex).has_value();
            };

        const auto decorationHasHint =
            [this](const DecorationBillboard &billboard)
            {
                const DecorationEntry *pDecoration =
                    m_indoorDecorationBillboardSet->decorationTable.get(billboard.decorationId);

                if ((pDecoration == nullptr || pDecoration->hint.empty()) && !billboard.name.empty())
                {
                    pDecoration = m_indoorDecorationBillboardSet->decorationTable.findByInternalName(billboard.name);
                }

                return pDecoration != nullptr && !pDecoration->hint.empty();
            };

        for (const DecorationBillboard &billboard : m_indoorDecorationBillboardSet->billboards)
        {
            if (!isRenderSectorVisible(billboard.sectorId, visibleSectorMask))
            {
                continue;
            }

            if (!decorationHasInteraction(billboard) && !decorationHasHint(billboard))
            {
                continue;
            }

            bool hidden = false;
            const uint16_t spriteId = resolveDecorationBillboardSpriteId(billboard, hidden);

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
                static_cast<float>(billboard.y) - m_cameraPositionY,
                static_cast<float>(billboard.x) - m_cameraPositionX);
            const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName);

            if (pTexture == nullptr || pTexture->width <= 0 || pTexture->height <= 0)
            {
                continue;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const bx::Vec3 center = {
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z) + worldHeight * 0.5f
            };
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

            if (distance <= InspectRayEpsilon
                || (distance >= bestDistance && (bestHit.kind != "face" || distance > bestDistance + 8.0f)))
            {
                continue;
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
                continue;
            }

            float normalizedU = (localX + halfWidth) / worldWidth;
            const float normalizedV = (halfHeight - localY) / worldHeight;

            if (resolvedTexture.mirrored)
            {
                normalizedU = 1.0f - normalizedU;
            }

            if (!isOpaqueBillboardPixel(*pTexture, normalizedU, normalizedV))
            {
                continue;
            }

            bestDistance = distance;
            bestHit.hasHit = true;
            bestHit.kind = "entity";
            bestHit.index = billboard.entityIndex;
            bestHit.name = billboard.name;
            bestHit.textureName.clear();
            bestHit.distance = distance;
            bestHit.decorationListId = billboard.decorationId;
            bestHit.eventIdPrimary = billboard.eventIdPrimary;
            bestHit.eventIdSecondary = billboard.eventIdSecondary;
            bestHit.variablePrimary = 0;
            bestHit.variableSecondary = 0;
            bestHit.specialTrigger = 0;

            if (billboard.entityIndex < indoorMapData.entities.size())
            {
                const IndoorEntity &entity = indoorMapData.entities[billboard.entityIndex];
                bestHit.name = entity.name;
                bestHit.decorationListId = entity.decorationListId;
                bestHit.eventIdPrimary = entity.eventIdPrimary;
                bestHit.eventIdSecondary = entity.eventIdSecondary;
                bestHit.variablePrimary = entity.variablePrimary;
                bestHit.variableSecondary = entity.variableSecondary;
                bestHit.specialTrigger = entity.specialTrigger;
            }
        }
    }

    if (mapDeltaData
        && m_monsterTable
        && m_indoorActorPreviewBillboardSet
        && (pPickRequest == nullptr || !pPickRequest->ignoreActors))
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
            const float actorHalfExtent = static_cast<float>(std::max<uint16_t>(actor.radius, 32));
            const float actorHeight = static_cast<float>(std::max<uint16_t>(actor.height, 96));
            const bx::Vec3 actorCenter = {
                static_cast<float>(actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(actor.z) + actorHeight * 0.5f
            };
            const float actorProjection = vecDot(vecSubtract(actorCenter, rayOrigin), rayDirection);
            const float actorBoundsRadius =
                std::sqrt(actorHalfExtent * actorHalfExtent * 2.0f + actorHeight * actorHeight * 0.25f);

            if (actorProjection + actorBoundsRadius <= InspectRayEpsilon
                || actorProjection - actorBoundsRadius >= bestDistance)
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

                    if (!visibleSectorMask.empty()
                        && !isSectorVisible(static_cast<int16_t>(face.roomNumber), visibleSectorMask)
                        && !isSectorVisible(static_cast<int16_t>(face.roomBehindNumber), visibleSectorMask))
                    {
                        continue;
                    }

                    if (!isFaceVisible(faceIndex, face, mapDeltaData, eventRuntimeState))
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

    if (mapDeltaData && !objectLoopSelectedWorldItem && !bestHit.hasHit)
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
    const std::optional<MapDeltaData> &mapDeltaData,
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

        if (!isFaceVisible(faceIndex, face, mapDeltaData, eventRuntimeState))
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
    bool allowWorldInput,
    const GameSettings &settings,
    bool arpgModeFirstPersonUseMode)
{
    if (updateArpgModeWorldMovement(input, deltaSeconds, allowWorldInput, settings, arpgModeFirstPersonUseMode))
    {
        return;
    }

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

bool IndoorRenderer::updateArpgModeWorldMovement(
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput,
    const GameSettings &settings,
    bool arpgModeFirstPersonUseMode)
{
    if (!settings.arpgModeEnabled || m_pSceneRuntime == nullptr)
    {
        m_arpgModeCameraActive = false;
        m_arpgModeCameraMatricesValid = false;
        m_arpgModeFirstPersonUseModeActive = false;
        return false;
    }

    if (arpgModeFirstPersonUseMode)
    {
        if (!m_arpgModeFirstPersonUseModeActive)
        {
            m_arpgModeHasMoveDestination = false;
            m_cameraYawRadians = m_arpgModeGameplayYawRadians;
            m_cameraPitchRadians = 0.0f;
            m_isRotatingCamera = false;
            m_cachedInspectHitValid = false;
        }

        m_arpgModeFirstPersonUseModeActive = true;
        m_arpgModeCameraActive = false;
        m_arpgModeCameraMatricesValid = false;
        return false;
    }

    m_arpgModeFirstPersonUseModeActive = false;
    m_arpgModeCameraActive = true;
    m_arpgModeCameraFovDegrees = settings.arpgModeCameraFovDegrees;
    IndoorPartyRuntime &partyRuntime = m_pSceneRuntime->partyRuntime();
    const IndoorWorldRuntime &worldRuntime = m_pSceneRuntime->worldRuntime();
    IndoorMoveState moveState = partyRuntime.movementState();

    if (!m_arpgModeCameraDistanceInitialized)
    {
        m_arpgModeCameraDistance = settings.arpgModeCameraDistance;
        m_arpgModeCameraDistanceInitialized = true;
    }

    if (input.mouseWheelDelta != 0.0f)
    {
        m_arpgModeCameraDistance =
            std::clamp(
                m_arpgModeCameraDistance - input.mouseWheelDelta * ArpgModeCameraWheelStep,
                ArpgModeCameraMinDistance,
                ArpgModeCameraMaxDistance);
    }

    if (allowWorldInput && input.rightMouseButton.held && m_lastRenderWidth > 0 && m_lastRenderHeight > 0)
    {
        const GameplayWorldPickRequest pickRequest =
            buildGameplayWorldPickRequest(
                GameplayWorldPickRequestInput{
                    .screenX = input.pointerX,
                    .screenY = input.pointerY,
                    .screenWidth = m_lastRenderWidth,
                    .screenHeight = m_lastRenderHeight,
                    .includeRay = true,
                });

        if (pickRequest.hasRay)
        {
            const GameplayWorldHit hit = pickGameplayWorldHit(pickRequest);
            std::optional<bx::Vec3> target;

            if (hit.actor)
            {
                target = hit.actor->hitPoint;
            }
            else if (hit.ground && hit.ground->isValid)
            {
                target = hit.ground->worldPoint;
            }
            else if (hit.eventTarget)
            {
                target = hit.eventTarget->hitPoint;
            }
            else if (hit.object)
            {
                target = hit.object->hitPoint;
            }
            else
            {
                target = bx::Vec3{
                    moveState.x + pickRequest.rayDirection.x * 512.0f,
                    moveState.y + pickRequest.rayDirection.y * 512.0f,
                    moveState.footZ
                };
            }

            if (target)
            {
                const float deltaX = target->x - moveState.x;
                const float deltaY = target->y - moveState.y;

                if (deltaX * deltaX + deltaY * deltaY > InspectRayEpsilon * InspectRayEpsilon)
                {
                    m_arpgModeGameplayYawRadians = std::atan2(deltaY, deltaX);
                }
            }
        }
    }

    if (allowWorldInput && input.leftMouseButton.held && m_lastRenderWidth > 0 && m_lastRenderHeight > 0)
    {
        std::optional<bx::Vec3> destination;
        const GameplayWorldPickRequest pickRequest =
            buildGameplayWorldPickRequest(
                GameplayWorldPickRequestInput{
                    .screenX = input.pointerX,
                    .screenY = input.pointerY,
                    .screenWidth = m_lastRenderWidth,
                    .screenHeight = m_lastRenderHeight,
                    .includeRay = true,
                });

        if (pickRequest.hasRay)
        {
            if (std::fabs(pickRequest.rayDirection.z) > InspectRayEpsilon)
            {
                const float planeDistance =
                    (moveState.footZ - pickRequest.rayOrigin.z) / pickRequest.rayDirection.z;

                if (planeDistance > InspectRayEpsilon)
                {
                    destination =
                        bx::Vec3{
                            pickRequest.rayOrigin.x + pickRequest.rayDirection.x * planeDistance,
                            pickRequest.rayOrigin.y + pickRequest.rayDirection.y * planeDistance,
                            moveState.footZ
                        };
                }
            }

            if (!destination)
            {
                const float horizontalLengthSquared =
                    pickRequest.rayDirection.x * pickRequest.rayDirection.x
                    + pickRequest.rayDirection.y * pickRequest.rayDirection.y;

                if (horizontalLengthSquared > InspectRayEpsilon * InspectRayEpsilon)
                {
                    const float inverseHorizontalLength = 1.0f / std::sqrt(horizontalLengthSquared);
                    constexpr float DirectionFallbackDistance = 1024.0f;
                    destination =
                        bx::Vec3{
                            moveState.x
                                + pickRequest.rayDirection.x * inverseHorizontalLength * DirectionFallbackDistance,
                            moveState.y
                                + pickRequest.rayDirection.y * inverseHorizontalLength * DirectionFallbackDistance,
                            moveState.footZ
                        };
                }
            }
        }

        if (destination)
        {
            m_arpgModeHasMoveDestination = true;
            m_arpgModeMoveDestinationX = destination->x;
            m_arpgModeMoveDestinationY = destination->y;
            m_arpgModeMoveDestinationZ = destination->z;
        }
        else if (input.leftMouseButton.pressed)
        {
            m_arpgModeHasMoveDestination = false;
        }
    }

    float desiredVelocityX = 0.0f;
    float desiredVelocityY = 0.0f;
    const bool actionAnimationActive = m_arpgModeActionAnimationSeconds > 0.0f;
    const bool jumpPressed = input.action(KeyboardAction::Jump).held;
    const bool jumpRequested = allowWorldInput && !actionAnimationActive && jumpPressed && !m_jumpHeld;
    m_jumpHeld = jumpPressed;

    if (allowWorldInput && !actionAnimationActive && m_arpgModeHasMoveDestination)
    {
        const float deltaX = m_arpgModeMoveDestinationX - moveState.x;
        const float deltaY = m_arpgModeMoveDestinationY - moveState.y;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY;
        const float stopRadius = std::max(4.0f, settings.arpgModeClickStopRadius);

        if (distanceSquared <= stopRadius * stopRadius)
        {
            m_arpgModeHasMoveDestination = false;
        }
        else
        {
            constexpr float BaseWalkSpeed = 384.0f;
            const float distance = std::sqrt(distanceSquared);
            const float moveSpeed =
                BaseWalkSpeed
                * 2.0f
                * std::clamp(settings.arpgModeMoveSpeedMultiplier, 0.1f, 10.0f);
            m_arpgModeGameplayYawRadians = std::atan2(deltaY, deltaX);
            desiredVelocityX = deltaX / distance * moveSpeed;
            desiredVelocityY = deltaY / distance * moveSpeed;
        }
    }

    if (worldRuntime.scenarioPartyActorCollisionEnabled())
    {
        partyRuntime.setActorColliders(worldRuntime.actorMovementCollidersForPartyMovement());
    }
    else
    {
        const std::vector<IndoorActorCollision> noActorColliders;
        partyRuntime.setActorColliders(noActorColliders);
    }

    partyRuntime.setDecorationColliders(worldRuntime.decorationMovementColliders());
    partyRuntime.setSpriteObjectColliders(worldRuntime.spriteObjectMovementColliders());
    partyRuntime.setMovementSpeedMultiplier(1.0f);
    partyRuntime.update(desiredVelocityX, desiredVelocityY, jumpRequested, true, deltaSeconds);
    moveState = partyRuntime.movementState();

    if (m_arpgModeActionAnimationSeconds > 0.0f)
    {
        m_arpgModeActionAnimationElapsedSeconds += std::max(0.0f, deltaSeconds);
        m_arpgModeActionAnimationSeconds =
            std::max(0.0f, m_arpgModeActionAnimationSeconds - std::max(0.0f, deltaSeconds));
    }
    else
    {
        m_arpgModeActionAnimationDurationSeconds = 0.0f;
        m_arpgModeActionAnimationElapsedSeconds = 0.0f;
    }

    const bx::Vec3 target = {
        moveState.x,
        moveState.y,
        moveState.footZ + settings.arpgModeCameraTargetHeight
    };
    const ArpgModeCameraFrame cameraFrame =
        buildArpgModeCameraFrame(
            ArpgModeCameraInput{
                .target = target,
                .yawRadians = degreesToRadians(settings.arpgModeCameraYawDegrees),
                .pitchRadians = degreesToRadians(settings.arpgModeCameraPitchDegrees),
                .distance = m_arpgModeCameraDistance,
                .fovDegrees = settings.arpgModeCameraFovDegrees,
                .aspectRatio =
                    m_lastRenderHeight > 0
                        ? static_cast<float>(std::max(m_lastRenderWidth, 1)) / static_cast<float>(m_lastRenderHeight)
                        : 1.0f,
                .nearClip = 0.1f,
                .farClip = 50000.0f,
                .homogeneousDepth = bgfx::getCaps()->homogeneousDepth,
            });

    m_cameraPositionX = cameraFrame.eye.x;
    m_cameraPositionY = cameraFrame.eye.y;
    m_cameraPositionZ = cameraFrame.eye.z;
    m_arpgModeViewMatrix = cameraFrame.viewMatrix;
    m_arpgModeProjectionMatrix = cameraFrame.projectionMatrix;
    m_arpgModeCameraMatricesValid = true;
    m_cameraYawRadians = degreesToRadians(settings.arpgModeCameraYawDegrees);
    m_cameraPitchRadians = degreesToRadians(settings.arpgModeCameraPitchDegrees);
    m_cachedInspectHitValid = false;
    return true;
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
    if (!input.turnBasedMovementStep)
    {
        deltaSeconds = std::min(deltaSeconds, 0.05f);
    }

    const bool *pKeyboardState = input.keyboardState();

    const float walkSpeed = 384.0f;
    const float runForwardMultiplier = 2.0f;
    const float indoorStrafeMultiplier = 0.5f;
    const float turboMultiplier = 12.0f;
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
    const bool runWalkModifier =
        pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT];
    const bool turboPressed =
        pKeyboardState[SDL_SCANCODE_LCTRL] || pKeyboardState[SDL_SCANCODE_RCTRL];
    const bool jumpPressed = input.action(KeyboardAction::Jump).held;
    const bool jumpRequested = allowWorldInput && jumpPressed && !m_jumpHeld;
    m_jumpHeld = jumpPressed;
    const bool standardControls = !m_gameplayMouseLookEnabled;
    const bool leftPressed = input.action(KeyboardAction::Left).held;
    const bool rightPressed = input.action(KeyboardAction::Right).held;
    const bool strafeLeftPressed = !standardControls && leftPressed;
    const bool strafeRightPressed = !standardControls && rightPressed;
    const float keyboardYawSpeed = 1.75f;
    float desiredVelocityX = 0.0f;
    float desiredVelocityY = 0.0f;

    if (allowWorldInput && standardControls)
    {
        if (leftPressed)
        {
            m_cameraYawRadians += keyboardYawSpeed * deltaSeconds;
        }

        if (rightPressed)
        {
            m_cameraYawRadians -= keyboardYawSpeed * deltaSeconds;
        }
    }

    if (m_pSceneRuntime != nullptr)
    {
        IndoorPartyRuntime &partyRuntime = m_pSceneRuntime->partyRuntime();
        const IndoorWorldRuntime &worldRuntime = m_pSceneRuntime->worldRuntime();
        const bool running =
            runWalkModifier ? !partyRuntime.alwaysRunEnabled() : partyRuntime.alwaysRunEnabled();
        const float turboScale = turboPressed ? turboMultiplier : 1.0f;
        const float runScale = running ? runForwardMultiplier : 1.0f;
        const float forwardMoveSpeed = walkSpeed * runScale * turboScale;
        const float backwardMoveSpeed = walkSpeed * turboScale;
        const float strafeMoveSpeed = walkSpeed * indoorStrafeMultiplier * runScale * turboScale;

        if (allowWorldInput && input.action(KeyboardAction::Forward).held)
        {
            desiredVelocityX += cosYaw * forwardMoveSpeed;
            desiredVelocityY += sinYaw * forwardMoveSpeed;
        }

        if (allowWorldInput && input.action(KeyboardAction::Backward).held)
        {
            desiredVelocityX -= cosYaw * backwardMoveSpeed;
            desiredVelocityY -= sinYaw * backwardMoveSpeed;
        }

        if (allowWorldInput && strafeLeftPressed)
        {
            desiredVelocityX -= right.x * strafeMoveSpeed;
            desiredVelocityY -= right.y * strafeMoveSpeed;
        }

        if (allowWorldInput && strafeRightPressed)
        {
            desiredVelocityX += right.x * strafeMoveSpeed;
            desiredVelocityY += right.y * strafeMoveSpeed;
        }

        if (worldRuntime.scenarioPartyActorCollisionEnabled())
        {
            partyRuntime.setActorColliders(worldRuntime.actorMovementCollidersForPartyMovement());
        }
        else
        {
            const std::vector<IndoorActorCollision> noActorColliders;
            partyRuntime.setActorColliders(noActorColliders);
        }
        partyRuntime.setDecorationColliders(worldRuntime.decorationMovementColliders());
        partyRuntime.setSpriteObjectColliders(worldRuntime.spriteObjectMovementColliders());
        partyRuntime.update(
            desiredVelocityX,
            desiredVelocityY,
            jumpRequested,
            running,
            deltaSeconds,
            input.turnBasedMovementStep);
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        m_cameraPositionX = moveState.x;
        m_cameraPositionY = moveState.y;
        m_cameraPositionZ = moveState.eyeZ();
    }
    else
    {
        const float currentMoveSpeed = walkSpeed * (turboPressed ? turboMultiplier : 1.5f);

        if (allowWorldInput && input.action(KeyboardAction::Forward).held)
        {
            m_cameraPositionX += forward.x * currentMoveSpeed * deltaSeconds;
            m_cameraPositionY += forward.y * currentMoveSpeed * deltaSeconds;
            m_cameraPositionZ += forward.z * currentMoveSpeed * deltaSeconds;
        }

        if (allowWorldInput && input.action(KeyboardAction::Backward).held)
        {
            m_cameraPositionX -= forward.x * currentMoveSpeed * deltaSeconds;
            m_cameraPositionY -= forward.y * currentMoveSpeed * deltaSeconds;
            m_cameraPositionZ -= forward.z * currentMoveSpeed * deltaSeconds;
        }

        if (allowWorldInput && strafeLeftPressed)
        {
            m_cameraPositionX -= right.x * currentMoveSpeed * deltaSeconds;
            m_cameraPositionY -= right.y * currentMoveSpeed * deltaSeconds;
        }

        if (allowWorldInput && strafeRightPressed)
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
