#include "game/render/RuntimeShader.h"
#include "engine/Localization.h"
#include "game/rules/GameRules.h"
#include "game/render/CinematicGrading.h"
#include "game/indoor/IndoorRenderer.h"
#include "game/indoor/IndoorBakedLighting.h"
#include "game/indoor/IndoorTranslucentFaces.h"
#include "game/render/WaterGeometry.h"
#include "game/render/ViewFrustum.h"
#include "game/render/WaterBillboardReflection.h"

#include "engine/BgfxContext.h"
#include "engine/ParallelFor.h"
#include "game/app/GameSession.h"
#include "game/data/ActorNameResolver.h"
#include "game/events/EventRuntime.h"
#include "game/FaceEnums.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ParticleRenderer.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/items/ItemRuntime.h"
#include "game/items/WorldItemShape.h"
#include "game/indoor/IndoorPortalGraph.h"
#include "game/indoor/IndoorPortalVisibility.h"
#include "game/indoor/IndoorRenderRevision.h"
#include "game/render/BillboardGeometry.h"
#include "game/render/CombatActorHealthBarPolicy.h"
#include "game/ui/EnemyHealthBarRenderer.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/render/QuestMarkerGeometry.h"
#include "game/render/SkyRenderer.h"
#include "game/render/SurfaceTextureGradients.h"
#include "game/render/TextureFiltering.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/SpriteObjectDefs.h"
#include "game/StringUtils.h"
#include "engine/ImageAssetLoader.h"

#include <bx/math.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <functional>
#include <array>
#include <bit>
#include <cctype>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <numeric>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// The weather sound with the camera under cover on an open-sky map (a house, a tunnel): muffled, as through walls.
constexpr float CoveredWeatherAudibility = 0.3f;
constexpr float IndoorCameraVerticalFovDegrees = 60.0f;

// u_indoorBakedDaylight[3] (fs_indoor_textured_lit.sc): the ambient level, the ambient's and the sun's scales; [0].w
// is set per draw (1 when the page has a daylight page).
std::array<float, 12> packIndoorBakedDaylight(const IndoorBakedDaylightScale &scale)
{
    std::array<float, 12> values = {};
    for (size_t channel = 0; channel < 3; ++channel)
    {
        values[channel] = scale.ambientLevel[channel];
        values[4 + channel] = scale.ambientScale[channel];
        values[8 + channel] = scale.sunScale[channel];
    }
    return values;
}
// Share of the ambient that reaches 3D models as a directional key light (fs_model.sc).
constexpr float IndoorModelKeyFraction = 0.6f;
// Decorations stand in for flat, painted sprites: a softer key light keeps them close to the sprite's even look.
constexpr float IndoorDecorationKeyFraction = 0.35f;
// Scale of the sprite light a decoration model receives. A model's visible surface averages well below one of its
// light (faces turning from the camera and the key light, Fresnel, baked vertex occlusion) where a painted sprite
// shows all of it; measured against the sprites they replace (dungeon_content_20261009), this makes the models
// display about as bright as their sprites.
constexpr float IndoorDecorationExposure = 1.8f;
// Share of the creatures' environment reflection that decoration models get. The room environment (dark floor, lit
// walls, tinted by the nearby lights) replaced a flat white cube, under which glossy props (iron torches) read as
// white glints at more than 0.1.
constexpr float IndoorDecorationReflection = 0.3f;
// Surface materials of BLV faces (devdocs/SURFACE_MATERIALS_PLAN.md): the distance at which their parallax has faded
// out, and the strengths of their highlights and room reflection.
constexpr float IndoorSurfaceParallaxDistance = 1600.0f;
constexpr float IndoorSurfaceHighlightStrength = 1.0f;
constexpr float IndoorSurfaceReflectionStrength = 1.0f;
// Far end of the clustered light grid's depth slices; lights fade out over its last 15 %.
constexpr float IndoorLightGridFarDistance = 4096.0f;
// Distance from the camera within which lights give decoration models their specular highlights (map units).
constexpr float IndoorDecorationHighlightReach = 2048.0f;
// One legacy map unit separates distant walls without clipping tight ceilings (4 units clips Kriegspire/Korbu).
constexpr float IndoorCameraNearClipDistance = 1.0f;
constexpr float IndoorCameraFarClipDistance = 50000.0f;
// An outdoor map's default view distance (OutdoorGameView DefaultOutdoorFarClip), for the outdoor view.
constexpr float IndoorOutdoorViewDefaultDistance = 16192.0f;
constexpr float IndoorSkyProjectionPitchOffsetRadians = 3.14159265358979323846f / 64.0f;
constexpr float IndoorSkyProjectionFarClipDistance = 50000.0f;
constexpr int IndoorBakedStaticLightSubdivisionMaxDepth = 16;
constexpr float IndoorBillboardStaticLightingSampleIntervalSeconds = 0.05f;
constexpr uint64_t IndoorBillboardDrawState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_WRITE_Z
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA;
constexpr uint64_t IndoorBillboardOverlayDrawState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA;

// The vertex's secret-pulse slot: 1 for a secret face, plus 2 for a face of the scene's `opaque_faces`
// (fs_indoor_textured_lit.sc).
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

bool indoorContextActionTargetsChest(
    const std::optional<GameplayEventTargetContextActionMetadata> &metadata,
    const std::vector<uint32_t> &openedChestIds)
{
    return !openedChestIds.empty() || (metadata && metadata->kind == "open_chest");
}

bool indoorFaceSuppressedForContextAction(
    const IndoorMapData &indoorMapData,
    size_t faceIndex,
    const IndoorFace &face,
    uint32_t attributes,
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

    if (face.facetType == 3 && hasFaceAttribute(attributes, FaceAttribute::Clickable) && face.cogTriggered != 0)
    {
        return false;
    }

    return face.facetType == 3 || indoorFaceMarkedAsCeiling(indoorMapData, faceIndex, face);
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

bool indoorDoorMechanismSuppressedForContextAction(
    const MapDeltaDoor &door,
    const EventRuntimeState *pEventRuntimeState)
{
    const uint16_t state = indoorDoorRuntimeState(door, pEventRuntimeState);

    return state == static_cast<uint16_t>(EvtMechanismState::Open)
        || state == static_cast<uint16_t>(EvtMechanismState::Opening);
}

bool hasMovingMechanism(const EventRuntimeState *pEventRuntimeState)
{
    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    for (const auto &entry : pEventRuntimeState->mechanisms)
    {
        if (mechanismFacesMoving(entry.second))
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
// The fog of a map whose only fog is a water volume's, outside the volume: farther than anything is drawn.
constexpr float IndoorWaterNoFogDistance = 1.0e8f;
// How much of MM9's light scale the screen takes under water (design decision 4: 0.6, to be matched to a capture).
constexpr float IndoorWaterTintStrength = 0.6f;
constexpr size_t MaxIndoorShaderLights = MaxIndoorDrawLights;
constexpr float Pi = 3.14159265358979323846f;
constexpr float InspectRayEpsilon = 0.0001f;
constexpr float KeyboardEventFaceScreenRadius = 384.0f;
constexpr float HoveredActorOutlineThicknessPixels = 2.0f;
constexpr float BillboardFrustumSlack = 8.0f;

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
    uint32_t objectKey = 0;
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
    uint32_t containedItemId = 0;
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

bx::Vec3 vecAdd(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

bx::Vec3 vecScale(const bx::Vec3 &value, float scale)
{
    return {value.x * scale, value.y * scale, value.z * scale};
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
    const MonsterEntry *pMonsterEntry = monsterTable.findByDisplayEntryId(actor.monsterInfoId);
    return pMonsterEntry != nullptr ? pMonsterEntry : monsterTable.findById(actor.monsterId);
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

std::optional<RuntimeActorBillboard> buildRuntimeActorBillboard(
    const MonsterTable &monsterTable,
    const SpriteFrameTable &spriteFrameTable,
    const MapDeltaData &mapDeltaData,
    size_t actorIndex,
    const IndoorWorldRuntime *pWorldRuntime = nullptr,
    const std::vector<uint8_t> *pVisibleSectorMask = nullptr
)
{
    if (actorIndex >= mapDeltaData.actors.size())
    {
        return std::nullopt;
    }

    const MapDeltaActor &actor = mapDeltaData.actors[actorIndex];

    if ((actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
    {
        return std::nullopt;
    }

    const IndoorWorldRuntime::MapActorAiState *pActorAiState =
        pWorldRuntime != nullptr ? pWorldRuntime->mapActorAiState(actorIndex) : nullptr;
    const int16_t sectorId =
        pActorAiState != nullptr && pActorAiState->sectorId >= 0 ? pActorAiState->sectorId : actor.sectorId;

    if (!sectorVisibleForRuntimeBillboard(sectorId, pVisibleSectorMask))
    {
        return std::nullopt;
    }

    const MonsterEntry *pMonsterEntry =
        pActorAiState == nullptr ? resolveRuntimeMonsterEntry(monsterTable, actor) : nullptr;
    const uint16_t spriteFrameIndex = pActorAiState != nullptr
        ? pActorAiState->spriteFrameIndex
        : resolveRuntimeActorSpriteFrameIndex(spriteFrameTable, actor, pMonsterEntry);

    if (spriteFrameIndex == 0)
    {
        return std::nullopt;
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

    billboard.heightScale *= boundGameRules().monsters.actorDrawScale(actor.rulesetFacts, true);
    billboard.useStaticFrame = false;
    GameplayRuntimeActorState runtimeActorState = {};
    billboard.isFriendly =
        pWorldRuntime == nullptr
        || !pWorldRuntime->actorRuntimeState(actorIndex, runtimeActorState)
        || !runtimeActorState.hostileToParty;
    billboard.actorName = pActorAiState != nullptr
        ? pActorAiState->displayName
        : resolveMapDeltaActorName(monsterTable, actor);
    return billboard;
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
        std::optional<RuntimeActorBillboard> billboard = buildRuntimeActorBillboard(
            monsterTable,
            spriteFrameTable,
            mapDeltaData,
            actorIndex,
            pWorldRuntime,
            pVisibleSectorMask);
        if (billboard)
        {
            billboards.push_back(std::move(*billboard));
        }
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
        billboard.objectKey = spriteObject.objectKey;
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
        billboard.hasContainingItem = spriteObject.semanticLootContainer
            || (hasContainingItemPayload(spriteObject.rawContainingItem)
                && (pObjectEntry->flags & ObjectDescUnpickable) == 0);
        billboard.containedItemId =
            billboard.hasContainingItem && !spriteObject.semanticLootContainer ? containedItemId : 0;
        const bool containedItemIdentified =
            spriteObject.rawContainingItem.size() > 0x08 && (spriteObject.rawContainingItem[0x08] & 0x01) != 0;

        if (pContainedItemDefinition != nullptr
            && !containedItemIdentified
            && ItemRuntime::requiresIdentification(*pContainedItemDefinition))
        {
            billboard.objectName = ItemRuntime::foundItemName(*pContainedItemDefinition);
        }
        else
        {
            billboard.objectName = pContainedItemDefinition != nullptr && !pContainedItemDefinition->name.empty()
                ? pContainedItemDefinition->name
                : pObjectEntry->internalName;
        }
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
    bool fixedEvent = false;
};

constexpr uint8_t InvalidInteractiveDecorationDecorVarIndex = 0xff;
constexpr uint8_t MaxInteractiveDecorationDecorVarCount = 125;

void buildIndoorInteractiveDecorationBindingCaches(
    const IndoorMapData &indoorMapData,
    const DecorationBillboardSet *pBillboardSet,
    std::vector<uint8_t> &decorVarIndicesByEntity,
    std::vector<uint16_t> &baseEventIdsByEntity,
    std::vector<uint8_t> &eventCountsByEntity,
    std::vector<uint8_t> &hideWhenClearedByEntity,
    std::vector<uint8_t> &fixedEventByEntity)
{
    decorVarIndicesByEntity.assign(indoorMapData.entities.size(), InvalidInteractiveDecorationDecorVarIndex);
    baseEventIdsByEntity.assign(indoorMapData.entities.size(), 0);
    eventCountsByEntity.assign(indoorMapData.entities.size(), 0);
    hideWhenClearedByEntity.assign(indoorMapData.entities.size(), 0);
    fixedEventByEntity.assign(indoorMapData.entities.size(), 0);

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

        const DecorationLookupResult decoration =
            pBillboardSet->decorationTable.resolveMapDecoration(entity.decorationListId, entity.name);
        const DecorationEntry *pDecoration = decoration.pEntry;

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
        fixedEventByEntity[entityIndex] = bindingSpec->fixedEvent ? 1 : 0;

        ++decorVarIndex;
    }
}

std::optional<IndoorInteractiveDecorationBinding> resolveIndoorInteractiveDecorationBinding(
    const std::vector<uint8_t> &decorVarIndicesByEntity,
    const std::vector<uint16_t> &baseEventIdsByEntity,
    const std::vector<uint8_t> &eventCountsByEntity,
    const std::vector<uint8_t> &hideWhenClearedByEntity,
    const std::vector<uint8_t> &fixedEventByEntity,
    size_t targetEntityIndex)
{
    if (targetEntityIndex >= decorVarIndicesByEntity.size()
        || targetEntityIndex >= baseEventIdsByEntity.size()
        || targetEntityIndex >= eventCountsByEntity.size()
        || targetEntityIndex >= hideWhenClearedByEntity.size()
        || targetEntityIndex >= fixedEventByEntity.size())
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
    binding.fixedEvent = fixedEventByEntity[targetEntityIndex] != 0;

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
    return interactiveDecorationEventId(
        eventRuntimeState.decorVars[binding.decorVarIndex],
        binding.baseEventId, binding.eventCount, binding.hideWhenCleared, binding.fixedEvent);
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

// Whether a door-moved face draws its stored texels instead of the original engines' geometric door mapping
// (indoorMoverFaceKeepsStoredTexels): every vertex moves with the door, so the texels move with the face, and its
// texels in the BLV's vertex pose are not that mapping. Faces that stretch keep the geometric mapping; many MM6-MM8
// frames store stale texels.
bool mechanismFaceKeepsStoredTexels(
    const IndoorMapData &indoorMapData,
    const IndoorFace &face,
    const MapDeltaDoor &door
)
{
    if (face.textureUs.size() < face.vertexIndices.size() || face.textureVs.size() < face.vertexIndices.size())
    {
        return false;
    }

    // A rotating or spinning mover (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md) always turns its stored texels
    // with it.
    if (const IndoorMoverDefinition *pMover = findIndoorMoverDefinition(indoorMapData, door.doorId);
        pMover != nullptr && (pMover->rotation || pMover->spin))
    {
        return true;
    }

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= indoorMapData.vertices.size()
            || std::find(door.vertexIds.begin(), door.vertexIds.end(), vertexIndex) == door.vertexIds.end())
        {
            return false;
        }
    }

    const bx::Vec3 normal = computeFaceNormal(indoorMapData.vertices, face);
    bx::Vec3 axisU = {0.0f, 0.0f, 0.0f};
    bx::Vec3 axisV = {0.0f, 0.0f, 0.0f};

    if (vecDot(normal, normal) <= 0.0001f || !calculateFaceTextureAxes(face, vecNormalize(normal), axisU, axisV))
    {
        return false;
    }

    std::vector<IndoorProjectedFacePoint> geometryTexels;
    std::vector<IndoorProjectedFacePoint> storedTexels;
    geometryTexels.reserve(face.vertexIndices.size());
    storedTexels.reserve(face.vertexIndices.size());

    for (size_t faceVertexIndex = 0; faceVertexIndex < face.vertexIndices.size(); ++faceVertexIndex)
    {
        const IndoorVertex &vertex = indoorMapData.vertices[face.vertexIndices[faceVertexIndex]];
        const bx::Vec3 point = {float(vertex.x), float(vertex.y), float(vertex.z)};
        geometryTexels.push_back({vecDot(point, axisU), vecDot(point, axisV)});
        storedTexels.push_back({
            float(face.textureDeltaU + face.textureUs[faceVertexIndex]),
            float(face.textureDeltaV + face.textureVs[faceVertexIndex])
        });
    }

    return indoorMoverFaceKeepsStoredTexels(geometryTexels, storedTexels);
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

    return localEventProgram && localEventProgram->hasEvent(face.cogTriggered);
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

    // evt.SetTexture swaps one face named by its index (MMerge's MM6 maps), or every face of a cog number, as MM7's
    // and MM8's SetTexture (the face extra's sCogNumber); cog 0 names no face.
    const uint32_t keys[2] = {
        faceIndex < 0x80000000u ? EventRuntime::indoorFaceReferenceKey(static_cast<uint32_t>(faceIndex)) : 0,
        face.cogNumber};

    for (uint32_t key : keys)
    {
        if (key == 0)
        {
            continue;
        }

        const std::unordered_map<uint32_t, std::string>::const_iterator iterator =
            eventRuntimeState->textureOverrides.find(key);

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

// Colour of the room environment models reflect: neutral, pulled 40 % toward the intensity-weighted colour of the
// lights near the camera, then scaled to unit luminance (the ambient sets the brightness). The light colour is
// normalized by its brightest channel, so a saturated light tints without growing brighter.
std::array<float, 3> indoorRoomEnvironmentTint(const IndoorDrawLightSet &lights)
{
    std::array<float, 3> sum = {};
    for (size_t light = 0; light < lights.lightCount; ++light)
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            sum[channel] += lights.colors[light * 4 + channel] * lights.colors[light * 4 + 3];
        }
    }
    const float peak = std::max({sum[0], sum[1], sum[2]});
    if (peak <= 0.0001f)
    {
        return {1.0f, 1.0f, 1.0f};
    }
    std::array<float, 3> tint;
    for (size_t channel = 0; channel < 3; ++channel)
    {
        tint[channel] = 0.6f + 0.4f * sum[channel] / peak;
    }
    const float luminance = tint[0] * 0.2126f + tint[1] * 0.7152f + tint[2] * 0.0722f;
    for (float &channel : tint)
    {
        channel /= luminance;
    }
    return tint;
}

uint64_t billboardLightingCacheKey(uint16_t category, uint64_t index)
{
    return (static_cast<uint64_t>(category) << 48) | (index & 0x0000ffffffffffffull);
}

// The vertex's static light: rgb at half scale (the shader doubles it); alpha 255 less the open air's lights' share of
// it (openAirRgb's luminance over rgb's, 0 on every map without daylight), which fs_indoor_textured_lit.sc scales by
// the hour (indoorVertexLight).
uint32_t encodeBakedLightAbgr(const std::array<float, 3> &rgb, const std::array<float, 3> &openAirRgb)
{
    const auto encode = [](float value) -> uint8_t
    {
        return static_cast<uint8_t>(std::clamp(static_cast<int>(std::lround(value * 0.5f * 255.0f)), 0, 255));
    };
    const auto luminance = [](const std::array<float, 3> &value)
    {
        return 0.2126f * value[0] + 0.7152f * value[1] + 0.0722f * value[2];
    };
    const float total = luminance(rgb);
    const float openAirShare = total > 0.0001f ? std::clamp(luminance(openAirRgb) / total, 0.0f, 1.0f) : 0.0f;
    const uint32_t alpha = uint32_t(std::clamp(static_cast<int>(std::lround((1.0f - openAirShare) * 255.0f)), 0, 255));

    return (makeAbgr(encode(rgb[0]), encode(rgb[1]), encode(rgb[2])) & 0x00ffffffu) | alpha << 24;
}

std::vector<uint8_t> bakedStaticLightEnabledStates(
    const IndoorMapData &indoorMapData,
    const EventRuntimeState *pEventRuntimeState,
    const DecorationBillboardSet *pBillboardSet)
{
    std::vector<uint8_t> enabledStates(indoorMapData.lights.size(), 0);

    for (size_t lightId = 0; lightId < indoorMapData.lights.size(); ++lightId)
    {
        const IndoorLight &light = indoorMapData.lights[lightId];
        enabledStates[lightId] =
            light.radius > 0
                && IndoorLightingRuntime::isBlvLightEnabledByState(
                    static_cast<uint32_t>(light.attributes),
                    pEventRuntimeState,
                    lightId)
                    ? 1
                    : 0;
    }

    if (pBillboardSet != nullptr)
    {
        for (const DecorationBillboard &billboard : pBillboardSet->billboards)
        {
            enabledStates.push_back(bakedStaticLightSourceForDecoration(
                *pBillboardSet, billboard, pEventRuntimeState, false).has_value() ? 1 : 0);
        }
    }

    return enabledStates;
}

bool bakedStaticLightAffectsPoint(const BakedStaticLightSource &source, const bx::Vec3 &point)
{
    const float dx = source.position.x - point.x;
    const float dy = source.position.y - point.y;
    const float dz = source.position.z - point.z;
    return dx * dx + dy * dy + dz * dz <= source.radius * source.radius;
}

// Scene `static_lights: {sides: front}` (IndoorMapData::staticLightsFrontOnly): how far behind a face's plane a
// static light may stand and still light the face (a lamp's light set just into the wall it hangs on).
constexpr float IndoorStaticLightBehindTolerance = 24.0f;

// A face's plane for that test: a point on the face and its unit normal (the side it is drawn from).
struct StaticLightFacePlane
{
    bx::Vec3 point = {0.0f, 0.0f, 0.0f};
    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
};

// The face's plane, or none when the map lights both sides or the face has no area (no test).
std::optional<StaticLightFacePlane> staticLightFacePlane(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    const IndoorFace &face)
{
    if (!indoorMapData.staticLightsFrontOnly || face.vertexIndices.empty()
        || face.vertexIndices.front() >= vertices.size())
    {
        return std::nullopt;
    }
    const bx::Vec3 normal = computeFaceNormal(vertices, face);
    if (vecDot(normal, normal) <= 0.0001f)
    {
        return std::nullopt;
    }
    return StaticLightFacePlane{indoorVertexToWorld(vertices[face.vertexIndices.front()]), vecNormalize(normal)};
}

bool staticLightBehindFace(const BakedStaticLightSource &source, const StaticLightFacePlane &plane)
{
    return vecDot(vecSubtract(source.position, plane.point), plane.normal) < -IndoorStaticLightBehindTolerance;
}

void accumulateBakedLightContribution(
    std::array<float, 3> &rgb,
    const bx::Vec3 &lightPosition,
    float radius,
    uint8_t red,
    uint8_t green,
    uint8_t blue,
    float alpha,
    bool coloredLights,
    const bx::Vec3 &position)
{
    if (radius <= 0.0f || alpha <= 0.0f)
    {
        return;
    }

    const float dx = lightPosition.x - position.x;
    const float dy = lightPosition.y - position.y;
    const float dz = lightPosition.z - position.z;
    const float distanceSquared = dx * dx + dy * dy + dz * dz;
    const float radiusSquared = radius * radius;

    if (distanceSquared > radiusSquared)
    {
        return;
    }

    float attenuation = 1.0f - std::clamp(distanceSquared / radiusSquared, 0.0f, 1.0f);
    attenuation *= attenuation;
    attenuation *= IndoorBakedStaticLightScale * alpha;
    if (coloredLights)
    {
        rgb[0] += (static_cast<float>(red) / 255.0f) * attenuation;
        rgb[1] += (static_cast<float>(green) / 255.0f) * attenuation;
        rgb[2] += (static_cast<float>(blue) / 255.0f) * attenuation;
    }
    else
    {
        const float brightness =
            (static_cast<float>(red) * 0.299f
                + static_cast<float>(green) * 0.587f
                + static_cast<float>(blue) * 0.114f)
            / 255.0f;
        rgb[0] += brightness * attenuation;
        rgb[1] += brightness * attenuation;
        rgb[2] += brightness * attenuation;
    }
}

uint32_t bakedStaticLightAbgrForPoint(
    const std::vector<BakedStaticLightSource> &bakedStaticLightSources,
    bool coloredLights,
    float ambient,
    const bx::Vec3 &position)
{
    std::array<float, 3> rgb = {ambient, ambient, ambient};
    std::array<float, 3> openAirRgb = {0.0f, 0.0f, 0.0f};

    for (const BakedStaticLightSource &source : bakedStaticLightSources)
    {
        std::array<float, 3> &target = source.openAir ? openAirRgb : rgb;
        accumulateBakedLightContribution(
            target,
            source.position,
            source.radius,
            source.red,
            source.green,
            source.blue,
            source.alpha,
            coloredLights,
            position);
    }

    for (size_t channel = 0; channel < 3; ++channel)
    {
        rgb[channel] += openAirRgb[channel];
    }
    return encodeBakedLightAbgr(rgb, openAirRgb);
}

float pointAabbDistanceSquared(
    const bx::Vec3 &point,
    const bx::Vec3 &minBounds,
    const bx::Vec3 &maxBounds)
{
    const float clampedX = std::clamp(point.x, minBounds.x, maxBounds.x);
    const float clampedY = std::clamp(point.y, minBounds.y, maxBounds.y);
    const float clampedZ = std::clamp(point.z, minBounds.z, maxBounds.z);
    const float dx = point.x - clampedX;
    const float dy = point.y - clampedY;
    const float dz = point.z - clampedZ;
    return dx * dx + dy * dy + dz * dz;
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

IndoorRenderer::TexturedVertex IndoorRenderer::interpolateTexturedVertex(
    const TexturedVertex &first,
    const TexturedVertex &second)
{
    TexturedVertex result = {};
    result.x = (first.x + second.x) * 0.5f;
    result.y = (first.y + second.y) * 0.5f;
    result.z = (first.z + second.z) * 0.5f;
    result.u = (first.u + second.u) * 0.5f;
    result.v = (first.v + second.v) * 0.5f;
    result.secretPulse = (first.secretPulse + second.secretPulse) * 0.5f;
    result.barycentric0 = (first.barycentric0 + second.barycentric0) * 0.5f;
    result.barycentric1 = (first.barycentric1 + second.barycentric1) * 0.5f;
    result.barycentric2 = (first.barycentric2 + second.barycentric2) * 0.5f;
    result.boundaryEdgeMask = (first.boundaryEdgeMask + second.boundaryEdgeMask) * 0.5f;
    result.flowUPerSecond = (first.flowUPerSecond + second.flowUPerSecond) * 0.5f;
    result.flowVPerSecond = (first.flowVPerSecond + second.flowVPerSecond) * 0.5f;
    result.lavaFlow = (first.lavaFlow + second.lavaFlow) * 0.5f;
    result.fluidFlow = (first.fluidFlow + second.fluidFlow) * 0.5f;
    result.gradientU = first.gradientU;
    result.gradientV = first.gradientV;
    return result;
}

void IndoorRenderer::setBillboardFog()
{
    const std::array<float, 4> color = indoorFogColorUniform(m_frameFog);
    const std::array<float, 4> densities = indoorFogDensitiesUniform(m_frameFog);
    const std::array<float, 4> distances = indoorFogDistancesUniform(m_frameFog);
    setBillboardFogColor(color.data());
    bgfx::setUniform(m_billboardFogDensitiesUniformHandle, densities.data());
    bgfx::setUniform(m_billboardFogDistancesUniformHandle, distances.data());
}

void IndoorRenderer::setBillboardFogColor(const float *pFogColor)
{
    bgfx::setUniform(m_billboardFogColorUniformHandle, pFogColor);
    applySceneSkyFog();
}

void IndoorRenderer::applySceneSkyFog()
{
    if (bgfx::isValid(m_skyFogUniformHandle))
    {
        // Flat fog, or the outdoor view's sky haze; the map's mist with either.
        bgfx::setUniform(m_skyFogUniformHandle, m_openSky.outdoorView ? m_outdoorSkyFog.data() : m_flatSkyFog.data(),
            SkyFogUniformVectors);
    }
}

void IndoorRenderer::refreshBakedStaticLight(
    const std::vector<BakedStaticLightSource> &bakedStaticLightSources,
    bool coloredLights,
    float ambient,
    TexturedVertex &vertex)
{
    vertex.bakedLightAbgr =
        bakedStaticLightAbgrForPoint(
            bakedStaticLightSources,
            coloredLights,
            ambient,
            {vertex.x, vertex.y, vertex.z});
}

void IndoorRenderer::appendBakedStaticLightSubdividedTriangle(
    TexturedFaceMesh &mesh,
    std::unordered_map<uint64_t, uint32_t> &vertexIndices,
    const std::vector<BakedStaticLightSource> &bakedStaticLightSources,
    const std::vector<BakedStaticLightSource> &bakedStaticLightSubdivisionSources,
    bool coloredLights,
    float ambient,
    const TexturedVertex (&triangleVertices)[3],
    const std::array<bx::Vec3, 3> &subdivisionPositions,
    int depth)
{
    const bx::Vec3 edge01 = bx::sub(subdivisionPositions[0], subdivisionPositions[1]);
    const bx::Vec3 edge12 = bx::sub(subdivisionPositions[1], subdivisionPositions[2]);
    const bx::Vec3 edge20 = bx::sub(subdivisionPositions[2], subdivisionPositions[0]);
    const float edgeSquared01 = bx::dot(edge01, edge01);
    const float edgeSquared12 = bx::dot(edge12, edge12);
    const float edgeSquared20 = bx::dot(edge20, edge20);
    const float maxEdgeSquared = std::max(edgeSquared01, std::max(edgeSquared12, edgeSquared20));
    const float subdivisionEdgeSquared =
        IndoorBakedStaticLightSubdivisionMinEdgeLength * IndoorBakedStaticLightSubdivisionMinEdgeLength;

    if (depth >= IndoorBakedStaticLightSubdivisionMaxDepth
        || maxEdgeSquared <= subdivisionEdgeSquared
        || !indoorBakedStaticLightNeedsSubdivision(
            bakedStaticLightSubdivisionSources,
            subdivisionPositions))
    {
        for (const TexturedVertex &vertex : triangleVertices)
        {
            // Dyadic split weights sum to one, so two components identify a vertex within this original triangle.
            const uint64_t key = (uint64_t(std::bit_cast<uint32_t>(vertex.barycentric0)) << 32)
                | std::bit_cast<uint32_t>(vertex.barycentric1);
            const uint32_t nextIndex = static_cast<uint32_t>(mesh.vertices.size());
            const auto [iterator, inserted] = vertexIndices.try_emplace(key, nextIndex);
            if (inserted)
            {
                mesh.vertices.push_back(vertex);
            }
            mesh.indices.push_back(iterator->second);
        }
        return;
    }

    size_t firstIndex = 0;
    size_t secondIndex = 1;
    size_t thirdIndex = 2;

    if (edgeSquared12 >= edgeSquared01 && edgeSquared12 >= edgeSquared20)
    {
        firstIndex = 1;
        secondIndex = 2;
        thirdIndex = 0;
    }
    else if (edgeSquared20 >= edgeSquared01 && edgeSquared20 >= edgeSquared12)
    {
        firstIndex = 2;
        secondIndex = 0;
        thirdIndex = 1;
    }

    TexturedVertex midpoint = interpolateTexturedVertex(triangleVertices[firstIndex], triangleVertices[secondIndex]);
    refreshBakedStaticLight(
        bakedStaticLightSources,
        coloredLights,
        ambient,
        midpoint);

    TexturedVertex firstChild[3] = {
        triangleVertices[firstIndex],
        midpoint,
        triangleVertices[thirdIndex]
    };
    TexturedVertex secondChild[3] = {
        midpoint,
        triangleVertices[secondIndex],
        triangleVertices[thirdIndex]
    };
    const bx::Vec3 subdivisionMidpoint = bx::mul(
        bx::add(subdivisionPositions[firstIndex], subdivisionPositions[secondIndex]), 0.5f);
    const std::array<bx::Vec3, 3> firstSubdivisionPositions = {
        subdivisionPositions[firstIndex], subdivisionMidpoint, subdivisionPositions[thirdIndex]
    };
    const std::array<bx::Vec3, 3> secondSubdivisionPositions = {
        subdivisionMidpoint, subdivisionPositions[secondIndex], subdivisionPositions[thirdIndex]
    };

    appendBakedStaticLightSubdividedTriangle(
        mesh,
        vertexIndices,
        bakedStaticLightSources,
        bakedStaticLightSubdivisionSources,
        coloredLights,
        ambient,
        firstChild,
        firstSubdivisionPositions,
        depth + 1);
    appendBakedStaticLightSubdividedTriangle(
        mesh,
        vertexIndices,
        bakedStaticLightSources,
        bakedStaticLightSubdivisionSources,
        coloredLights,
        ambient,
        secondChild,
        secondSubdivisionPositions,
        depth + 1);
}

bgfx::VertexLayout IndoorRenderer::TerrainVertex::ms_layout;
bgfx::VertexLayout IndoorRenderer::TexturedVertex::ms_layout;
bgfx::VertexLayout IndoorRenderer::LitBillboardVertex::ms_layout;
bgfx::VertexLayout IndoorRenderer::LightmapUvVertex::ms_layout;

std::array<float, 3> IndoorRenderer::cachedBillboardStaticDetailLighting(
    const IndoorLightingFrame &lightingFrame,
    const bx::Vec3 &position,
    int16_t sectorId,
    uint64_t cacheKey,
    LightingStats *pLightingStats)
{
    if (cacheKey == 0)
    {
        return IndoorLightingRuntime::sampleLightingRgbForSectors(
            lightingFrame,
            position,
            sectorId,
            -1,
            pLightingStats,
            IndoorLightingSampleFilter::StaticDetailOnly);
    }

    BillboardLightingCacheEntry &entry = m_billboardLightingCache[cacheKey];
    const bool refresh =
        !entry.valid
        || entry.lightRevision != lightingFrame.indoorLightRevision
        || entry.coloredLights != lightingFrame.coloredLights
        || entry.sectorId != sectorId
        || entry.sampleClockSeconds < 0.0f
        || m_elapsedTime < entry.sampleClockSeconds
        || m_elapsedTime - entry.sampleClockSeconds >= IndoorBillboardStaticLightingSampleIntervalSeconds;

    if (refresh)
    {
        entry.staticDetailRgb =
            IndoorLightingRuntime::sampleLightingRgbForSectors(
                lightingFrame,
                position,
                sectorId,
                -1,
                pLightingStats,
                IndoorLightingSampleFilter::StaticDetailOnly);
        entry.position = position;
        entry.sampleClockSeconds = m_elapsedTime;
        entry.lightRevision = lightingFrame.indoorLightRevision;
        entry.sectorId = sectorId;
        entry.coloredLights = lightingFrame.coloredLights;
        entry.valid = true;
    }

    return entry.staticDetailRgb;
}

std::array<float, 4> IndoorRenderer::billboardLightingUniform(
    const IndoorLightingFrame &lightingFrame,
    const SpriteFrameEntry &frame,
    const bx::Vec3 &position,
    int16_t sectorId,
    uint64_t cacheKey,
    LightingStats *pLightingStats)
{
    if (SpriteFrameTable::hasFlag(frame.flags, SpriteFrameFlag::Lit))
    {
        return {{1.0f, 1.0f, 1.0f, 0.0f}};
    }

    if (m_modelLighting.enabled)
    {
        // MM9's model light (scene model_lighting): a sprite faces the camera, so its lights arrive without N.L.
        const std::array<float, 3> rgb = indoorModelLight(m_modelLighting,
            IndoorLightingRuntime::sampleModelLightRgb(lightingFrame, position, m_modelLighting.lightScale));
        return {{rgb[0], rgb[1], rgb[2], 0.0f}};
    }

    const uint64_t sampleBeginTickCount = pLightingStats != nullptr ? SDL_GetTicksNS() : 0;
    const std::array<float, 3> staticDetailRgb =
        cachedBillboardStaticDetailLighting(lightingFrame, position, sectorId, cacheKey, pLightingStats);
    const std::array<float, 3> dynamicRgb =
        IndoorLightingRuntime::sampleLightingRgbForSectors(
            lightingFrame,
            position,
            sectorId,
            -1,
            pLightingStats,
            IndoorLightingSampleFilter::DynamicOnly);
    if (pLightingStats != nullptr)
    {
        pLightingStats->billboardSampleNanoseconds += SDL_GetTicksNS() - sampleBeginTickCount;
    }

    // Both samples hold the room light once; a sector open to the sky takes its own daylight out again, every other
    // the frame's ambient (as always).
    const float sampledAmbient = indoorDaylightSector(m_daylight, sectorId)
        ? IndoorLightingRuntime::sectorAmbient(lightingFrame, sectorId) : lightingFrame.ambient;
    const std::array<float, 3> rgb = {{
        std::clamp(staticDetailRgb[0] + dynamicRgb[0] - sampledAmbient, 0.0f, 2.0f),
        std::clamp(staticDetailRgb[1] + dynamicRgb[1] - sampledAmbient, 0.0f, 2.0f),
        std::clamp(staticDetailRgb[2] + dynamicRgb[2] - sampledAmbient, 0.0f, 2.0f)
    }};
    return {{rgb[0], rgb[1], rgb[2], 0.0f}};
}

IndoorRenderer::IndoorRenderer(SpriteAtlasCache &spriteAtlasCache, NativeSpriteTextureCache &nativeSpriteCache)
    : m_isInitialized(false)
    , m_spriteAtlasCache(spriteAtlasCache)
    , m_nativeSpriteCache(nativeSpriteCache)
    , m_isRenderable(false)
    , m_pIndoorMapData(nullptr)
    , m_wireframeVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_portalVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_entityMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_spawnMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_doorMarkerVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_programHandle(BGFX_INVALID_HANDLE)
    , m_texturedProgramHandle(BGFX_INVALID_HANDLE)
    , m_hudTintedProgramHandle(BGFX_INVALID_HANDLE)
    , m_indoorLitProgramHandle(BGFX_INVALID_HANDLE)
    , m_billboardProgramHandle(BGFX_INVALID_HANDLE)
    , m_bloodSplatVertexBufferHandle(BGFX_INVALID_HANDLE)
    , m_bloodSplatTextureHandle(BGFX_INVALID_HANDLE)
    , m_textureSamplerHandle(BGFX_INVALID_HANDLE)
    , m_hudTintUniformHandle(BGFX_INVALID_HANDLE)
    , m_indoorLightPositionsUniformHandle(BGFX_INVALID_HANDLE)
    , m_indoorLightColorsUniformHandle(BGFX_INVALID_HANDLE)
    , m_indoorLightParamsUniformHandle(BGFX_INVALID_HANDLE)
    , m_secretPulseParamsUniformHandle(BGFX_INVALID_HANDLE)
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
    if (pAssetFileSystem != nullptr)
    {
        std::string error;
        if (!m_worldFxSystem.loadNamedEffectLibrary(
                *pAssetFileSystem,
                "engine/effects/library.yml",
                "engine/effects/resource_bindings.yml",
                error))
        {
            std::cerr << "Failed to load shared effect library: " << error << '\n';
            return false;
        }
        if (!m_worldFxSystem.loadProjectileModels(*pAssetFileSystem, error)
            || !m_worldFxSystem.loadItemModels(*pAssetFileSystem, error))
        {
            std::cerr << "Failed to load projectile or item models: " << error << '\n';
            return false;
        }
    }
    m_map = map;
    m_assetScaleTier = assetScaleTier;
    m_monsterTable = monsterTable;
    m_objectTable = objectTable;
    m_pItemTable = &itemTable;
    m_pIndoorMapData = &indoorMapData;
    // A resting item model lies on the floor under its footprint; a point whose floor is far from the item's height
    // (past a ledge) does not support it.
    m_worldFxSystem.setItemGroundSampler(
        [this](float x, float y, float z) -> std::optional<float>
        {
            constexpr float SupportBand = 24.0f;
            if (m_pIndoorMapData == nullptr)
            {
                return std::nullopt;
            }
            const IndoorFloorSample floor =
                sampleIndoorFloor(*m_pIndoorMapData, m_renderVertices, x, y, z, SupportBand, SupportBand);
            return floor.hasFloor ? std::optional<float>(floor.height) : std::nullopt;
        });
    m_billboardLightingCache.clear();
    m_modelSectorCache.clear();
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
        m_indoorInteractiveDecorationHideWhenClearedByEntity,
        m_indoorInteractiveDecorationFixedEventByEntity);
    if (pAssetFileSystem != nullptr && m_indoorDecorationBillboardSet)
    {
        std::string error;
        // A wall-mounted model (torch bracket) hangs on the nearest wall of its sector or the sectors beside it.
        const DecorationModelSet::WallFinder wallFinder =
            [this](const DecorationBillboard &billboard, float height)
            {
                return findIndoorDecorationWall(*m_pIndoorMapData, billboard.x, billboard.y, billboard.z, height);
            };
        if (!m_decorationModels.load(*pAssetFileSystem, map.worldId, map.fileName, *m_indoorDecorationBillboardSet,
                error, wallFinder))
        {
            std::cerr << "IndoorRenderer: decoration models failed to load: " << error << '\n';
            m_decorationModels.clear();
        }
    }
    m_indoorActorPreviewBillboardSet = indoorActorPreviewBillboardSet;
    m_indoorSpriteObjectBillboardSet = indoorSpriteObjectBillboardSet;
    rebuildIndoorRenderMemberships();
    m_indoorLightingRuntime.rebuildStaticCache(
        indoorMapData,
        m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr,
        runtimeEventRuntimeState());
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
    LightmapUvVertex::init();
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
            if (restoreBillboardTexture(texture.textureName, texture.paletteId, texture.resourceIdentity) != nullptr)
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
            billboardTexture.opacityMask.assignFromBgra(
                texture.pixels,
                texture.physicalWidth,
                texture.physicalHeight);
            billboardTexture.textureHandle = createBgraTexture2D(
                uint16_t(texture.physicalWidth),
                uint16_t(texture.physicalHeight),
                texture.pixels.data(),
                uint32_t(texture.pixels.size()),
                TextureFilterProfile::Billboard,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP,
                texture.pixelsPreparedForUpload
                    ? BgraTexturePixelPreparation::AlreadyPrepared
                    : BgraTexturePixelPreparation::Required
            );

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                m_nativeSpriteCache.retain(billboardTexture, texture.resourceIdentity);
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

            if (restoreBillboardTexture(texture.textureName, texture.paletteId, texture.resourceIdentity) != nullptr)
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
            billboardTexture.opacityMask.assignFromBgra(
                texture.pixels,
                texture.physicalWidth,
                texture.physicalHeight);
            billboardTexture.textureHandle = createBgraTexture2D(
                uint16_t(texture.physicalWidth),
                uint16_t(texture.physicalHeight),
                texture.pixels.data(),
                uint32_t(texture.pixels.size()),
                TextureFilterProfile::Billboard,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP,
                texture.pixelsPreparedForUpload
                    ? BgraTexturePixelPreparation::AlreadyPrepared
                    : BgraTexturePixelPreparation::Required
            );

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                m_nativeSpriteCache.retain(billboardTexture, texture.resourceIdentity);
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

            if (restoreBillboardTexture(texture.textureName, texture.paletteId, texture.resourceIdentity) != nullptr)
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
            billboardTexture.opacityMask.assignFromBgra(
                texture.pixels,
                texture.physicalWidth,
                texture.physicalHeight);
            billboardTexture.textureHandle = createBgraTexture2D(
                uint16_t(texture.physicalWidth),
                uint16_t(texture.physicalHeight),
                texture.pixels.data(),
                uint32_t(texture.pixels.size()),
                TextureFilterProfile::Billboard,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP,
                texture.pixelsPreparedForUpload
                    ? BgraTexturePixelPreparation::AlreadyPrepared
                    : BgraTexturePixelPreparation::Required
            );

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                m_nativeSpriteCache.retain(billboardTexture, texture.resourceIdentity);
                m_billboardTextureHandles.push_back(std::move(billboardTexture));
                registerBillboardTextureIndex(m_billboardTextureHandles.size() - 1);
            }
        }
    }

    if (m_indoorDecorationBillboardSet)
    {
        std::vector<OutdoorBitmapTexture>().swap(m_indoorDecorationBillboardSet->textures);
    }

    if (m_indoorActorPreviewBillboardSet)
    {
        std::vector<OutdoorBitmapTexture>().swap(m_indoorActorPreviewBillboardSet->textures);
    }

    if (m_indoorSpriteObjectBillboardSet)
    {
        std::vector<OutdoorBitmapTexture>().swap(m_indoorSpriteObjectBillboardSet->textures);
    }

    m_faceCount = static_cast<uint32_t>(indoorMapData.faces.size());
    m_programHandle = loadProgram("vs_cubes", "fs_cubes");
    m_texturedProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_shadowmaps_texture");
    m_hudTintedProgramHandle = loadProgram("vs_shadowmaps_texture", "fs_menu_tint");
    m_indoorLitProgramHandle = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_lit");
    // Surface materials (devdocs/SURFACE_MATERIALS_PLAN.md), only for a map loaded with their maps.
    const bool surfaceMaterials = indoorTextureSet && hasSurfaceMaterialMaps(indoorTextureSet->textures);
    if (surfaceMaterials)
    {
        m_indoorLitMaterialProgramHandle =
            loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_lit_materials");
    }
    // Baked lighting (devdocs/INDOOR_BAKED_LIGHTING.md), only for a map that has it: its lightmap pages, decoded once.
    if (indoorMapData.bakedLighting)
    {
        m_indoorBakedProgramHandle = loadProgram("vs_indoor_textured_baked", "fs_indoor_textured_baked");
        if (surfaceMaterials)
        {
            m_indoorBakedMaterialProgramHandle =
                loadProgram("vs_indoor_textured_baked", "fs_indoor_textured_baked_materials");
        }
        m_lightmapSamplerHandle = bgfx::createUniform("s_texLightmap", bgfx::UniformType::Sampler);
        m_daylightmapSamplerHandle = bgfx::createUniform("s_texDaylightmap", bgfx::UniformType::Sampler);
        m_indoorBakedDaylightUniformHandle = bgfx::createUniform("u_indoorBakedDaylight", bgfx::UniformType::Vec4, 3);
        bool pagesCreated = true;
        const auto createPages = [this, &pagesCreated](const std::vector<IndoorBakedLightingPage> &pages,
            std::vector<bgfx::TextureHandle> &handles)
        {
            for (const IndoorBakedLightingPage &page : pages)
            {
                const std::vector<uint32_t> pixels = page.decodePixels();
                const bgfx::TextureHandle handle = createBgraTexture2D(uint16_t(page.width), uint16_t(page.height),
                    reinterpret_cast<const uint8_t *>(pixels.data()), uint32_t(pixels.size() * sizeof(uint32_t)),
                    TextureFilterProfile::Lightmap, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                pagesCreated = pagesCreated && bgfx::isValid(handle);
                handles.push_back(handle);
            }
        };
        createPages(indoorMapData.bakedLighting->pages, m_lightmapTextureHandles);
        createPages(indoorMapData.bakedLighting->daylightPages, m_daylightmapTextureHandles);
        if (!pagesCreated || !bgfx::isValid(m_indoorBakedProgramHandle)
            || (surfaceMaterials && !bgfx::isValid(m_indoorBakedMaterialProgramHandle))
            || !bgfx::isValid(m_lightmapSamplerHandle) || !bgfx::isValid(m_daylightmapSamplerHandle)
            || !bgfx::isValid(m_indoorBakedDaylightUniformHandle))
        {
            std::cerr << "IndoorRenderer: baked lighting unavailable, drawing the map vertex-lit\n";
            destroyBakedLightingResources();
        }
    }
    m_bakedLightingActive = !m_lightmapTextureHandles.empty();
    // Translucent faces (devdocs/INDOOR_TRANSLUCENT_FACES.md), only for a map that has them.
    if (!indoorMapData.translucentFaces.empty())
    {
        m_indoorTranslucentProgramHandle = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_translucent");
        if (indoorMapData.bakedLighting)
        {
            m_indoorBakedTranslucentProgramHandle =
                loadProgram("vs_indoor_textured_baked", "fs_indoor_textured_baked_translucent");
        }
        m_indoorTranslucencyUniformHandle = bgfx::createUniform("u_indoorTranslucency", bgfx::UniformType::Vec4);
    }
    // Scene water volumes (devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md): the screen tint under water, only for a
    // map that has them.
    if (!indoorMapData.waterVolumes.empty())
    {
        m_waterTintProgramHandle = loadProgram("vs_screen_color", "fs_cubes");
    }
    m_modelLighting = indoorMapData.modelLighting;
    m_openSky = indoorMapData.openSky;
    // The sectors open to the sky: those holding sky faces (an outdoor region's open-air room). Weather shows there.
    m_openSkySectors.clear();
    if (m_openSky.enabled)
    {
        for (const IndoorFace &face : indoorMapData.faces)
        {
            if (hasFaceAttribute(face.attributes, FaceAttribute::IndoorSky))
            {
                if (face.roomNumber >= m_openSkySectors.size())
                {
                    m_openSkySectors.resize(size_t(face.roomNumber) + 1, 0);
                }
                m_openSkySectors[face.roomNumber] = 1;
            }
        }
    }
    m_openSkyWeather.configure(std::nullopt);
    m_holeViewApplied = false;
    m_lastSkyStateElapsedTime = -1.0f;
    // Scene fog (devdocs/INDOOR_FOG.md), only for a map that has it: the face programs' fog variants.
    m_fog = indoorMapData.fog;
    if (m_openSky.enabled && m_openSky.outdoorView)
    {
        // The outdoor view's haze replaces the scene fog (devdocs/INDOOR_OPEN_SKY.md "Outdoor view"); the faces draw
        // it with the fog programs.
        m_fog = {};
        m_fog.enabled = true;
    }
    // A water volume's own fog (MM9 FogEnable) on a map without one: the fog programs, with a fog too far to show.
    if (!m_fog.enabled
        && std::any_of(indoorMapData.waterVolumes.begin(), indoorMapData.waterVolumes.end(),
            [](const IndoorWaterVolume &volume) { return volume.fog.enabled; }))
    {
        m_fog.enabled = true;
        m_fog.nearDistance = IndoorWaterNoFogDistance;
        m_fog.farDistance = IndoorWaterNoFogDistance * 2.0f;
    }
    // Scene mist (devdocs/MIST.md) is drawn by the fog programs too: on a map without fog, with a fog too far to show.
    m_mist = indoorMapData.mist;
    m_frameSurroundings = {};
    m_flatSkyFog = {};
    if (!m_fog.enabled && m_mist.enabled())
    {
        m_fog.enabled = true;
        m_fog.nearDistance = IndoorWaterNoFogDistance;
        m_fog.farDistance = IndoorWaterNoFogDistance * 2.0f;
    }
    m_frameFog = m_fog;
    m_lastFrameFog = m_fog;
    m_scriptedFogRevision = 0;
    m_outdoorViewDistance = 0.0f;
    m_outdoorSkyFog = {};
    // Scene daylight (devdocs/INDOOR_OPEN_SKY.md "Daylight"): the sectors open to the sky take the sun and sky light.
    m_daylight = indoorMapData.daylight;
    m_frameDaylight = {};
    m_frameOpenAirLightScale = 1.0f;
    // A map without daylight draws a daylight page as baked (all scales 1).
    m_frameBakedDaylight = packIndoorBakedDaylight({});
    if (m_fog.enabled)
    {
        if (!bgfx::isValid(m_indoorFogModeUniformHandle))
        {
            m_indoorFogModeUniformHandle = bgfx::createUniform("u_indoorFogMode", bgfx::UniformType::Vec4);
            m_indoorFogLightUniformHandle = bgfx::createUniform("u_indoorFogLight", bgfx::UniformType::Vec4);
        }
        m_indoorFogProgramHandles[0] = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_lit_fog");
        if (surfaceMaterials)
        {
            m_indoorFogProgramHandles[1] =
                loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_lit_materials_fog");
        }
        m_indoorFogProgramHandles[2] = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_translucent_fog");
        if (indoorMapData.bakedLighting)
        {
            m_indoorFogProgramHandles[3] = loadProgram("vs_indoor_textured_baked", "fs_indoor_textured_baked_fog");
            if (surfaceMaterials)
            {
                m_indoorFogProgramHandles[4] =
                    loadProgram("vs_indoor_textured_baked", "fs_indoor_textured_baked_materials_fog");
            }
            m_indoorFogProgramHandles[5] =
                loadProgram("vs_indoor_textured_baked", "fs_indoor_textured_baked_translucent_fog");
        }
    }
    if (indoorMapData.terrain && pAssetFileSystem != nullptr)
    {
        std::string terrainError;
        if (!initializeTerrain(*pAssetFileSystem, map.worldId, indoorMapData, terrainError))
        {
            std::cerr << "IndoorRenderer: terrain drawn textured: " << terrainError << '\n';
            destroyTerrainResources();
        }
    }
    m_billboardProgramHandle = loadProgram("vs_outdoor_billboard_lit", "fs_outdoor_billboard_lit");
    if (!m_spriteAtlasCache.hasProgram())
    {
        m_spriteAtlasCache.setProgram(loadProgram("vs_outdoor_billboard_lit", "fs_sprite_atlas"));
        m_spriteAtlasCache.setOutlineProgram(loadProgram("vs_outdoor_billboard_lit", "fs_sprite_outline"));
    }
    m_worldFxRenderResources.setParticleProgramHandle(loadProgram("vs_particle", "fs_particle"));
    ParticleRenderer::initializeResources(m_worldFxRenderResources);
    if (!m_modelRenderer.initialize(loadProgram("vs_model", "fs_model"), BGFX_INVALID_HANDLE,
            loadProgram("vs_model_skinned_instanced", "fs_model")))
    {
        std::cerr << "IndoorRenderer: failed to initialize model renderer\n";
        shutdown();
        return false;
    }
    // Static instancing draws carried attachments (staves, weapons) indoors.
    if (!m_modelRenderer.initializeStatic(loadProgram("vs_model_instanced", "fs_model"),
            loadProgram("vs_model_shadow_instanced", "fs_model_shadow"),
            loadProgram("vs_model_instanced", "fs_model_prepassed")))
    {
        std::cerr << "IndoorRenderer: model attachments require renderer instancing support\n";
    }
    // Emissive-texture variants of the colour programs, loaded only when a model with an emissive texture appears.
    m_modelRenderer.setEmissiveProgramLoader([]()
    {
        return Engine::ModelEmissivePrograms{loadProgram("vs_model", "fs_model_emissive"),
            loadProgram("vs_model_skinned_instanced", "fs_model_emissive"),
            loadProgram("vs_model_instanced", "fs_model_emissive")};
    });
    m_modelRenderer.setShieldShellProgramLoader([]()
    {
        return loadProgram("vs_model_shield", "fs_model_shield");
    });
    m_textureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);
    m_hudTintUniformHandle = bgfx::createUniform("u_menuTint", bgfx::UniformType::Vec4);
    m_indoorLightPositionsUniformHandle =
        bgfx::createUniform("u_indoorLightPositions", bgfx::UniformType::Vec4, MaxIndoorShaderLights);
    m_indoorLightColorsUniformHandle =
        bgfx::createUniform("u_indoorLightColors", bgfx::UniformType::Vec4, MaxIndoorShaderLights);
    m_indoorLightParamsUniformHandle = bgfx::createUniform("u_indoorLightParams", bgfx::UniformType::Vec4);
    m_surfaceNormalSamplerHandle = bgfx::createUniform("s_surfaceNormal", bgfx::UniformType::Sampler);
    m_surfaceDetailSamplerHandle = bgfx::createUniform("s_surfaceDetail", bgfx::UniformType::Sampler);
    m_surfaceMaterialUniformHandle = bgfx::createUniform("u_surfaceMaterial", bgfx::UniformType::Vec4);
    if (!m_surfaceReflectionBinding.create())
    {
        std::cerr << "IndoorRenderer: failed to create the surface reflection binding\n";
    }
    m_indoorFaceGridUniformHandle = bgfx::createUniform("u_indoorFaceGrid", bgfx::UniformType::Vec4);
    m_indoorDaylightUniformHandle = bgfx::createUniform("u_indoorDaylight", bgfx::UniformType::Vec4, 3);
    const bool lightGridCreated = m_lightGridBinding.create();
    m_worldClipPlaneUniform = bgfx::createUniform("u_worldClipPlane", bgfx::UniformType::Vec4);
    m_secretPulseParamsUniformHandle = bgfx::createUniform("u_secretPulseParams", bgfx::UniformType::Vec4);
    m_indoorSkyParamsUniformHandle = bgfx::createUniform("u_indoorSkyParams", bgfx::UniformType::Vec4);
    m_indoorSkyProjectionParamsUniformHandle =
        bgfx::createUniform("u_indoorSkyProjectionParams", bgfx::UniformType::Vec4);
    m_billboardAmbientUniformHandle = bgfx::createUniform("u_billboardAmbient", bgfx::UniformType::Vec4);
    m_billboardOverrideColorUniformHandle =
        bgfx::createUniform("u_billboardOverrideColor", bgfx::UniformType::Vec4);
    m_billboardOutlineParamsUniformHandle =
        bgfx::createUniform("u_billboardOutlineParams", bgfx::UniformType::Vec4);
    m_billboardFogColorUniformHandle = bgfx::createUniform("u_fogColor", bgfx::UniformType::Vec4);
    m_skyFogUniformHandle = bgfx::createUniform("u_skyFog", bgfx::UniformType::Vec4, SkyFogUniformVectors);
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
        || (surfaceMaterials && !bgfx::isValid(m_indoorLitMaterialProgramHandle))
        || !bgfx::isValid(m_surfaceNormalSamplerHandle)
        || !bgfx::isValid(m_surfaceDetailSamplerHandle)
        || !bgfx::isValid(m_surfaceMaterialUniformHandle)
        || !bgfx::isValid(m_indoorFaceGridUniformHandle)
        || !lightGridCreated
        || !bgfx::isValid(m_secretPulseParamsUniformHandle)
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

    ensureBloodSplatTexture();

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

    preloadAtlasAnimations();

    m_isRenderable = true;
    return true;
}

void IndoorRenderer::preloadAtlasAnimations()
{
    if (m_pAssetFileSystem != nullptr && m_indoorActorPreviewBillboardSet && m_monsterTable
        && m_pSceneRuntime != nullptr)
    {
        const SpriteFrameTable &frames = m_indoorActorPreviewBillboardSet->spriteFrameTable;
        const auto preloadActor = [&](const auto &actor)
        {
            m_spriteAtlasCache.preload(*m_pAssetFileSystem, frames, actor.spriteFrameIndex);
            for (uint16_t actionFrame : actor.actionSpriteFrameIndices)
            {
                m_spriteAtlasCache.preload(*m_pAssetFileSystem, frames, actionFrame);
            }
        };
        // A model draws a bound monster: none of its sprites is needed.
        if (runtimeMapDeltaData())
        {
            for (const RuntimeActorBillboard &actor : buildRuntimeActorBillboards(
                *m_monsterTable, frames, *runtimeMapDeltaData(), &m_pSceneRuntime->worldRuntime()))
            {
                const IndoorWorldRuntime::MapActorAiState *pActorAiState =
                    m_pSceneRuntime->worldRuntime().mapActorAiState(actor.actorIndex);
                if (pActorAiState == nullptr || !m_indoorActorPreviewBillboardSet->drawsModel(pActorAiState->monsterId))
                {
                    preloadActor(actor);
                }
            }
        }
        else
        {
            for (const ActorPreviewBillboard &actor : m_indoorActorPreviewBillboardSet->billboards)
            {
                if (!actor.modelled)
                {
                    preloadActor(actor);
                }
            }
        }
    }
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

    if (!m_pIndoorMapData || m_pIndoorMapData->sectors.empty())
    {
        return {};
    }

    int16_t startSectorId = m_viewSectorOverride >= 0 && size_t(m_viewSectorOverride) < m_pIndoorMapData->sectors.size()
        ? m_viewSectorOverride : -1;

    if (startSectorId < 0 && m_pSceneRuntime != nullptr)
    {
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        const size_t sectorCount = m_pIndoorMapData->sectors.size();

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
        && !m_portalDebug.rebuildEveryFrame
        && cache.sectorId == startSectorId
        && cache.visibleSectorMask.size() == m_pIndoorMapData->sectors.size()
        && cache.cameraX == cameraPosition.x
        && cache.cameraY == cameraPosition.y
        && cache.cameraZ == cameraPosition.z
        && cache.yawRadians == m_cameraYawRadians
        && cache.pitchRadians == m_cameraPitchRadians
        && cache.aspectRatio == aspectRatio
        && cache.viewportHeight == m_lastRenderHeight
        && cache.maxDistance == m_outdoorViewDistance)
    {
        if (collectDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.visibilityCalls;

            ++m_indoorPerformanceDiagnostics.visibilityCacheHits;
            m_indoorPerformanceDiagnostics.visibilityTotalNanoseconds +=
                SDL_GetTicksNS() - totalBeginTickCount;
        }

        cache.rebuilt = false;
        return cache.visibleSectorMask;
    }

    const float cosPitch = std::cos(viewPitchRadians());
    const float sinPitch = std::sin(viewPitchRadians());
    const float cosYaw = std::cos(viewYawRadians());
    const float sinYaw = std::sin(viewYawRadians());
    IndoorPortalVisibilityInput input = {};
    input.pMapData = m_pIndoorMapData;
    input.pPortalGraph = m_indoorPortalGraph ? &m_indoorPortalGraph.value() : nullptr;
    input.pVertices = &m_renderVertices;
    input.pMapDeltaData = mapDeltaData ? &mapDeltaData.value() : nullptr;
    input.pEventRuntimeState = &eventRuntimeState;
    input.cameraPosition = cameraPosition;
    input.cameraForward = {cosYaw * cosPitch, sinYaw * cosPitch, sinPitch};
    input.cameraUp = {0.0f, 0.0f, 1.0f};
    input.verticalFovDegrees = m_viewVerticalFovDegrees;
    input.aspectRatio = aspectRatio;
    input.viewportHeight = m_lastRenderHeight;
    input.maxDistance = m_outdoorViewDistance;
    input.nearPortalReach = m_pIndoorMapData->portalNearReach;
    input.startSectorId = startSectorId;
    input.collectPortalTraces = m_logIndoorVisibilityDiagnostics;

    const bool portalDebug = m_portalDebug.active();
    const uint64_t visibilityBuildBeginTickCount = collectDiagnostics || portalDebug ? SDL_GetTicksNS() : 0;
    IndoorPortalVisibilityResult visibility = buildIndoorPortalVisibility(input);
    cache.buildNanoseconds = portalDebug ? SDL_GetTicksNS() - visibilityBuildBeginTickCount : 0;
    if (m_portalDebug.cullingOff && static_cast<size_t>(startSectorId) < visibility.frustumsBySector.size())
    {
        const std::vector<IndoorVisibilityFrustum> rootFrustums = visibility.frustumsBySector[startSectorId];
        visibility.visibleSectorMask.assign(visibility.visibleSectorMask.size(), 1);
        for (std::vector<IndoorVisibilityFrustum> &frustums : visibility.frustumsBySector)
        {
            frustums = rootFrustums;
        }
    }

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
    cache.rebuilt = true;
    cache.portalCandidateCount = visibility.portalCandidateCount;
    cache.acceptedPortalCount = visibility.acceptedPortalCount;
    cache.directionRejectedPortalCount = visibility.directionRejectedPortalCount;
    cache.clippedPortalRejectedCount = visibility.clippedPortalRejectedCount;
    cache.rejectedPortalCount = visibility.rejectedPortalCount;
    cache.acceptedPortals.clear();
    cache.nodeSectorIds.clear();
    if (portalDebug)
    {
        cache.acceptedPortals = visibility.acceptedPortals;
        for (const IndoorVisibilityNode &node : visibility.nodes)
        {
            cache.nodeSectorIds.push_back(node.sectorId);
        }
    }
    cache.sectorId = startSectorId;
    cache.cameraX = cameraPosition.x;
    cache.cameraY = cameraPosition.y;
    cache.cameraZ = cameraPosition.z;
    cache.yawRadians = m_cameraYawRadians;
    cache.pitchRadians = m_cameraPitchRadians;
    cache.aspectRatio = aspectRatio;
    cache.viewportHeight = m_lastRenderHeight;
    cache.maxDistance = m_outdoorViewDistance;
    // MM8 records discovery from the ordinary portal render traversal. Opaque walls/doors do not
    // start a separate visibility pass. Changing only the view frustums cannot reveal new sector faces.
    if (cache.visibleSectorMask != visibility.visibleSectorMask)
    {
        cache.mapRevealSectorIds.clear();
        for (size_t sectorIndex = 0; sectorIndex < visibility.visibleSectorMask.size(); ++sectorIndex)
        {
            if (visibility.visibleSectorMask[sectorIndex] != 0)
            {
                cache.mapRevealSectorIds.push_back(static_cast<int16_t>(sectorIndex));
            }
        }
        ++m_indoorMapRevealRevision;
    }
    cache.visibleSectorMask = visibility.visibleSectorMask;
    cache.visibleSectorFrustums = visibility.frustumsBySector;
    if (m_logIndoorVisibilityDiagnostics)
    {
        cache.portalTraces = visibility.portalTraces;
    }
    else
    {
        cache.portalTraces.clear();
    }
    return cache.visibleSectorMask;
}

void IndoorRenderer::logIndoorVisibilityDiagnostics(
    const std::vector<uint8_t> &baseVisibleSectorMask,
    const std::vector<uint8_t> &renderVisibleSectorMask,
    uint32_t currentTick
) const
{
    constexpr uint32_t LogIntervalMs = 1000;

    if (currentTick - m_lastVisibilityDiagnosticsLogTick < LogIntervalMs
        || !m_pIndoorMapData
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
            + diagnostics.renderBakedLightingRefreshNanoseconds
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
                  << " baked_lighting_refreshes=" << diagnostics.renderBakedLightingRefreshes
                  << " avg_baked_lighting_refresh_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      diagnostics.renderBakedLightingRefreshNanoseconds,
                      diagnostics.renderBakedLightingRefreshes))
                  << " baked_lighting_refreshed_vertices="
                  << diagnostics.renderBakedLightingRefreshedVertices
                  << " baked_lighting_uploaded_batches="
                  << diagnostics.renderBakedLightingUploadedBatches
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

const std::vector<int16_t> &IndoorRenderer::visibleIndoorMapRevealSectorIds() const
{
    return m_renderPortalVisibilityCache.mapRevealSectorIds;
}

uint64_t IndoorRenderer::indoorMapRevealRevision() const
{
    return m_indoorMapRevealRevision;
}

void IndoorRenderer::render(
    int width,
    int height,
    GameSession &gameSession,
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput,
    bool allowWorldSimulation,
    bool preparingResources)
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
    bgfx::setViewClear(MainViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, m_holeViewApplied ? 0xff00ffffu : 0x000000ffu,
        1.0f, 0);

    if (!m_isRenderable)
    {
        bgfx::touch(MainViewId);
        return;
    }

    // A playing cinematic draws the frame from its camera (devdocs/mm9_rework/MM9_CUTSCENES.md): its eye, angles and
    // field of view stand in for the party's for this render and are put back at its end; the party keeps its own.
    const CinematicRuntime &cinematic = gameSession.cinematicRuntime();
    m_viewShakeYawRadians = cinematic.shake().yawRadians();
    m_viewShakePitchRadians = cinematic.shake().pitchRadians();
    struct CinematicViewRestore
    {
        IndoorRenderer &renderer;
        std::optional<std::array<float, 5>> saved;

        ~CinematicViewRestore()
        {
            if (saved)
            {
                renderer.m_cameraPositionX = (*saved)[0];
                renderer.m_cameraPositionY = (*saved)[1];
                renderer.m_cameraPositionZ = (*saved)[2];
                renderer.m_cameraYawRadians = (*saved)[3];
                renderer.m_cameraPitchRadians = (*saved)[4];
                renderer.m_viewVerticalFovDegrees = IndoorCameraVerticalFovDegrees;
            }

            renderer.m_viewSectorOverride = -1;
        }
    } cinematicViewRestore{*this, std::nullopt};

    if (const std::optional<CinematicCameraView> &view = cinematic.cameraView())
    {
        cinematicViewRestore.saved = std::array<float, 5>{
            m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ, m_cameraYawRadians, m_cameraPitchRadians};
        m_cameraPositionX = view->eye.x;
        m_cameraPositionY = view->eye.y;
        m_cameraPositionZ = view->eye.z;
        m_cameraYawRadians = view->yawRadians;
        m_cameraPitchRadians = view->pitchRadians;
        m_viewVerticalFovDegrees = view->verticalFovDegrees.value_or(IndoorCameraVerticalFovDegrees);

        // The portal walk starts in the camera's own sector, not the party's (looked up again when the eye moves).
        if (m_pIndoorMapData != nullptr
            && (m_viewSectorOverride < 0 || m_viewSectorEye[0] != view->eye.x || m_viewSectorEye[1] != view->eye.y
                || m_viewSectorEye[2] != view->eye.z))
        {
            m_viewSectorEye = {view->eye.x, view->eye.y, view->eye.z};
            m_viewSectorOverride = findIndoorSectorForPoint(*m_pIndoorMapData, m_renderVertices,
                bx::Vec3{view->eye.x, view->eye.y, view->eye.z}).value_or(-1);
        }
    }

    const GameSettings &settings = gameSession.gameplayScreenRuntime().settingsSnapshot();
    if (settings.indoorHoleView && !m_holeViewApplied && m_pIndoorMapData != nullptr)
    {
        // The hole view (tools/indoor_hole_sweep.py): sky faces draw as faces again (a batch rebuild), no sky pass,
        // fog or view distance, and the clear colour is magenta: what shows magenta is covered by no face.
        m_holeViewApplied = true;
        m_openSky = {};
        m_fog = {};
        m_frameFog = {};
        m_texturedBatchGeometryRevision = std::numeric_limits<uint64_t>::max();
    }
    // The outdoor view's distance: the player's view distance setting as an outdoor map takes it (default 16 192,
    // OutdoorGameView) times the scene's view_distance_scale.
    m_outdoorViewDistance = m_openSky.enabled && m_openSky.outdoorView
        ? resolveViewDistanceSetting(settings.viewDistance, IndoorOutdoorViewDefaultDistance)
            * m_openSky.viewDistanceScale
        : 0.0f;
    m_worldFxSystem.waterRipples().setEnabled(
        settings.waterMovementRipples && m_waterRenderer.isReady());
    m_logIndoorVisibilityDiagnostics = settings.logIndoorVisibility;
    m_logIndoorPerformanceDiagnostics = settings.performanceTrace;
    const bool bakedStaticColorModeChanged = m_bakedStaticColoredLights != settings.coloredLights;
    m_bakedStaticColoredLights = settings.coloredLights;
    const bool collectRenderDiagnostics = m_logIndoorPerformanceDiagnostics;
    const uint64_t renderBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    // The portal debug view's CPU split (IndoorRendererPortalDebug.cpp): one flag test per frame while it is off.
    const bool portalDebug = m_portalDebug.active();
    const auto portalDebugTicks = [portalDebug]() { return portalDebug ? SDL_GetTicksNS() : uint64_t(0); };
    const uint64_t portalDebugBeginTicks = portalDebugTicks();

    if (collectRenderDiagnostics)
    {
        ++m_indoorPerformanceDiagnostics.renderFrames;
    }

    const float deltaMilliseconds = deltaSeconds * 1000.0f;
    m_elapsedTime += std::max(deltaSeconds, 0.0f);

    if (allowWorldSimulation && m_pSceneRuntime != nullptr)
    {
        // Turn-based mode and a held world (setWorldTimeHeld) freeze game time, but doors and lifts keep moving.
        const bool gameTimeFrozen = gameSession.turnBasedCombatRuntime().active() || m_worldTimeHeld;
        const bool collectDiagnostics = m_logIndoorPerformanceDiagnostics;
        const uint64_t mechanismBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
        const uint64_t simulationBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
        const EventRuntimeState *pPreviousEventRuntimeState = runtimeEventRuntimeState();
        const std::unordered_map<uint32_t, RuntimeMechanismState> previousMechanisms =
            pPreviousEventRuntimeState != nullptr
                ? pPreviousEventRuntimeState->mechanisms
                : std::unordered_map<uint32_t, RuntimeMechanismState>();
        const bool simulationAdvanced = gameTimeFrozen
            ? m_pSceneRuntime->advanceMechanisms(deltaMilliseconds)
            : m_pSceneRuntime->advanceSimulation(deltaMilliseconds);

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

            const std::vector<uint32_t> changedDoorIds = collectChangedMechanismDoorIds(previousMechanisms);

            if (mechanismsStillMoving)
            {
                if (collectDiagnostics)
                {
                    ++m_indoorPerformanceDiagnostics.movingFrames;
                }

                uint64_t texturedBuildNanoseconds = 0;
                uint64_t uploadNanoseconds = 0;

                if (!updateMechanismGeometryResourcesForDoorIds(
                        changedDoorIds,
                        texturedBuildNanoseconds,
                        uploadNanoseconds)
                    && collectDiagnostics)
                {
                    ++m_indoorPerformanceDiagnostics.movingUpdateFailures;
                }
            }
            else
            {
                if (!changedDoorIds.empty())
                {
                    uint64_t texturedBuildNanoseconds = 0;
                    uint64_t uploadNanoseconds = 0;

                    if (!updateMechanismGeometryResourcesForDoorIds(
                            changedDoorIds,
                            texturedBuildNanoseconds,
                            uploadNanoseconds)
                        && collectDiagnostics)
                    {
                        ++m_indoorPerformanceDiagnostics.movingUpdateFailures;
                    }
                }
            }

            if (collectDiagnostics)
            {
                m_indoorPerformanceDiagnostics.mechanismTotalNanoseconds +=
                    SDL_GetTicksNS() - mechanismBeginTickCount;
            }
            // A surface change made by the simulation (a destructible broken) is caught up below: in place, else
            // rebuilt.
        }
    }

    // Baked lighting follows `[video] lightmaps`: switching it rebuilds the batches once, lightmapped or vertex-lit.
    const bool bakedLightingWanted =
        settings.lightmaps && m_pIndoorMapData != nullptr && !m_lightmapTextureHandles.empty();
    if (bakedLightingWanted != m_bakedLightingActive)
    {
        m_bakedLightingActive = bakedLightingWanted;
        m_texturedBatchGeometryRevision = std::numeric_limits<uint64_t>::max();
    }

    // A surface change (evt.SetTexture, a face hidden by a destructible, a click or the console) shows at once:
    // changed face bits in place where they can be, else a rebuild.
    if (bgfx::getRendererType() != bgfx::RendererType::Noop
        && m_indoorTextureSet
        && m_texturedBatchGeometryRevision != currentTexturedBatchGeometryRevision()
        && !updateFaceAttributeChanges()
        && !rebuildDerivedGeometryResources())
    {
        std::cerr << "IndoorRenderer: failed to rebuild after a surface change\n";
    }

    if (bgfx::getRendererType() != bgfx::RendererType::Noop
        && m_indoorTextureSet
        && !texturedBatchesNeedFullRebuild()
        && (bakedStaticColorModeChanged
            || m_bakedStaticLightRevision != currentBakedStaticLightRevision()))
    {
        const uint64_t refreshBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
        size_t refreshedVertexCount = 0;
        size_t uploadedBatchCount = 0;

        if (!refreshBakedStaticLighting(
                bakedStaticColorModeChanged,
                refreshedVertexCount,
                uploadedBatchCount))
        {
            std::cerr << "IndoorRenderer: failed to refresh baked static lighting\n";
        }

        if (collectRenderDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.renderBakedLightingRefreshes;
            m_indoorPerformanceDiagnostics.renderBakedLightingRefreshNanoseconds +=
                SDL_GetTicksNS() - refreshBeginTickCount;
            m_indoorPerformanceDiagnostics.renderBakedLightingRefreshedVertices += refreshedVertexCount;
            m_indoorPerformanceDiagnostics.renderBakedLightingUploadedBatches += uploadedBatchCount;
        }
    }

    const uint64_t worldFxBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;

    m_worldFxSystem.setShadowsEnabled(settings.shadows);
    const GameplayInputFrame *pGameplayInputFrame = gameSession.currentGameplayInputFrame();
    const bool rightMouseInspectPauseActive =
        pGameplayInputFrame != nullptr
        && pGameplayInputFrame->rightMouseButton.held;
    const bool worldFxPaused = m_gameplayCursorMode || rightMouseInspectPauseActive;
    m_worldFxSystem.updateParticles(deltaSeconds, worldFxPaused);
    if (!m_gameplayCursorMode)
    {
        m_worldFxSystem.clearSpatialFx();
        m_worldFxSystem.syncProjectileFx(gameSession, rightMouseInspectPauseActive ? 0.0f : deltaSeconds, true);
    }

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderWorldFxNanoseconds += SDL_GetTicksNS() - worldFxBeginTickCount;
    }

    if (preparingResources && m_pAssetFileSystem != nullptr)
    {
        preloadAtlasAnimations();
        m_modelRenderer.preload(m_worldFxSystem.models());
        m_modelRenderer.preloadStatic(m_decorationModels.groups());
        m_effectRenderer.preload(m_worldFxSystem.namedEffects(), m_worldFxSystem.namedEffectResources(),
            *m_pAssetFileSystem, m_worldFxSystem.projectileEffectSpriteResources());
    }

    const uint64_t viewSetupBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    const float cosPitch = std::cos(viewPitchRadians());
    const float sinPitch = std::sin(viewPitchRadians());
    const float cosYaw = std::cos(viewYawRadians());
    const float sinYaw = std::sin(viewYawRadians());
    const bx::Vec3 viewForward = {cosYaw * cosPitch, sinYaw * cosPitch, sinPitch};

    const bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
    const bx::Vec3 at = {
        m_cameraPositionX + viewForward.x,
        m_cameraPositionY + viewForward.y,
        m_cameraPositionZ + viewForward.z
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};

    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        m_viewVerticalFovDegrees,
        static_cast<float>(viewWidth) / static_cast<float>(viewHeight),
        IndoorCameraNearClipDistance,
        cameraFarClipDistance(),
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );

    if (m_pPostProcessing != nullptr)
    {
        m_pPostProcessing->prepareWorldView(viewMatrix, projectionMatrix);
    }
    // Bloom: emitters (models, additive particles and effects) also draw into the glow view.
    const uint16_t glowView = m_pPostProcessing != nullptr ? m_pPostProcessing->glowView() : UINT16_MAX;
    m_modelRenderer.setGlowView(glowView);
    m_worldFxRenderResources.setGlowView(glowView);
    const uint16_t transparentView = m_pPostProcessing != nullptr
        ? m_pPostProcessing->transparentView(MainViewId) : MainViewId;
    // Multisampled world target: decoration foliage writes alpha to coverage in its depth prepass (program loaded the
    // first time anti-aliasing is on).
    const bool alphaToCoverage = m_pPostProcessing != nullptr && m_pPostProcessing->alphaToCoverage();
    if (alphaToCoverage && !m_modelRenderer.staticCoverageProgramAttempted())
    {
        m_modelRenderer.setStaticCoverageProgram(loadProgram("vs_model_instanced", "fs_model_coverage"));
    }
    m_modelRenderer.setAlphaToCoverage(alphaToCoverage);
    bgfx::setViewTransform(MainViewId, viewMatrix, projectionMatrix);
    bgfx::touch(MainViewId);
    if (portalDebug || m_portalDebugPassViewsBound)
    {
        preparePortalDebugPassViews(viewWidth, viewHeight, viewMatrix, projectionMatrix);
    }
    // The views of the passes: the ordinary ones, or each pass's own while `portals gpu` times them.
    const uint16_t decorationView = portalDebugPassView(IndoorDebugPass::Decorations, transparentView);
    const uint16_t decorationSolidView = portalDebugPassView(IndoorDebugPass::Decorations, MainViewId);
    const uint16_t actorView = portalDebugPassView(IndoorDebugPass::Actors, transparentView);
    const uint16_t actorSolidView = portalDebugPassView(IndoorDebugPass::Actors, MainViewId);
    const uint16_t openSkyView = portalDebugPassView(IndoorDebugPass::OpenSky, MainViewId);
    const uint16_t translucentView = portalDebugPassView(IndoorDebugPass::Translucent, transparentView);

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderViewSetupNanoseconds += SDL_GetTicksNS() - viewSetupBeginTickCount;
    }

    if (m_waterGeometryDirty)
    {
        updateWaterGeometry();
    }
    const bool enhancedWater = m_waterRenderer.isReady();

    const uint64_t visibilityBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    const uint64_t portalDebugVisibilityTicks = portalDebugTicks();
    const std::vector<uint8_t> renderVisibleSectorMask = buildVisibleSectorMask(eye);
    if (portalDebug)
    {
        m_portalDebugStats.cpuVisibilityNanoseconds = SDL_GetTicksNS() - portalDebugVisibilityTicks;
        m_portalDebugStats.visibilityRebuilt = m_renderPortalVisibilityCache.rebuilt;
    }
    const std::vector<uint8_t> &baseVisibleSectorMask = renderVisibleSectorMask;
    const std::vector<std::vector<IndoorVisibilityFrustum>> &renderVisibleSectorFrustums =
        m_renderPortalVisibilityCache.visibleSectorFrustums;

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderVisibilityNanoseconds += SDL_GetTicksNS() - visibilityBeginTickCount;
    }

    LightingStats *pLightingStats =
        collectRenderDiagnostics ? &m_indoorPerformanceDiagnostics.lightingStats : nullptr;
    const uint64_t lightingBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    const uint64_t portalDebugLightingTicks = portalDebugTicks();
    IndoorLightingFrameInput lightingInput = {};
    lightingInput.pMapData = m_pIndoorMapData;
    lightingInput.pEventRuntimeState = runtimeEventRuntimeState();
    lightingInput.pDecorationBillboardSet =
        m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr;
    lightingInput.pWorldFxSystem = &m_worldFxSystem;
    lightingInput.pParty = m_pSceneRuntime != nullptr ? &m_pSceneRuntime->partyRuntime().party() : nullptr;
    lightingInput.pVisibleSectorMask = &renderVisibleSectorMask;
    lightingInput.pVisibleSectorFrustums = &renderVisibleSectorFrustums;
    lightingInput.cameraPosition = eye;
    lightingInput.coloredLights = settings.coloredLights;
    lightingInput.warmTorchLight = settings.warmTorchLight;
    lightingInput.fxClusterThreshold =
        settings.lightGrid == LightGridQuality::Low ? FxLightClusterThresholdLow : FxLightClusterThresholdHigh;
    lightingInput.lightsIgnoreReach = m_modelLighting.enabled;
    lightingInput.timeSeconds = m_elapsedTime;
    m_mistSetting = settings.mist;
    m_mistStrengthSetting = float(settings.mistStrength) / 100.0f;
    updateFrameDaylightAndFog();
    lightingInput.openAirLightScale = m_frameOpenAirLightScale;
    // The water fogs as the faces do this frame: a copy taken when the water was built missed the outdoor view's haze
    // (made each frame from the sky and the view distance) and drew the Isle of Ashes' sea black.
    m_waterRenderer.setIndoorFog(m_frameFog);
    IndoorLightingFrame lightingFrame = m_indoorLightingRuntime.buildFrame(lightingInput);
    applyDaylightToLightingFrame(lightingFrame);
    // With baked lighting, actors, decorations and items (still lit by the light grid) take the bake's room light as
    // their ambient, so they match the lightmapped walls around them.
    if (m_bakedLightingActive)
    {
        for (size_t sectorId = 0; sectorId < lightingFrame.sectorAmbient.size(); ++sectorId)
        {
            if (const std::optional<float> ambient = m_pIndoorMapData->bakedLighting->actorAmbient(sectorId))
            {
                lightingFrame.sectorAmbient[sectorId] = *ambient;
            }
        }
    }
    m_surfaceMaterialsEnabled = settings.surfaceMaterials;
    m_terrainAntiTiling = settings.terrainAntiTiling;
    m_terrainGrassShown = settings.terrainDecorations;
    m_surfaceParallaxEnabled = settings.surfaceParallax;
    m_surfaceReflectionsEnabled = settings.surfaceReflections;
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

    if (enhancedWater)
    {
        const uint64_t revision = m_inspectGeometryRevision * 1099511628211ULL
            + lightingFrame.indoorLightRevision;
        m_waterRenderer.prepare(ViewFrustum(viewMatrix, projectionMatrix, bgfx::getCaps()->homogeneousDepth),
            eye, viewMatrix, projectionMatrix, settings.waterReflections,
            uint16_t(std::clamp(settings.waterReflectionSize, 128, 2048)), m_elapsedTime,
            revision, settings.coloredLights, renderVisibleSectorMask,
            m_renderPortalVisibilityCache.valid ? m_renderPortalVisibilityCache.sectorId : int16_t(-1),
            settings.waterSpriteReflections);
        renderWaterReflections(viewForward, lightingInput, viewWidth, viewHeight, settings.waterSpriteReflections);
    }

    const std::array<float, 4> noClipping = {};
    bgfx::setUniform(m_worldClipPlaneUniform, noClipping.data());

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
    if (portalDebug)
    {
        m_portalDebugStats.cpuLightingNanoseconds = SDL_GetTicksNS() - portalDebugLightingTicks;
    }

    const uint64_t inspectBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    InspectHit inspectHit = {};
    float mouseX = input.pointerX;
    float mouseY = input.pointerY;

    if (m_pIndoorMapData)
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
                    *m_pIndoorMapData,
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
    // Every light of the frame, binned into the view's clustered grid: BLV faces take their dynamic lights from it,
    // models their point lights. The profiling switch `render light_grid off` leaves it empty.
    {
        const Engine::LightGridConfig gridConfig = settings.lightGrid == LightGridQuality::Low
            ? Engine::LightGridConfig::low(IndoorLightGridFarDistance)
            : Engine::LightGridConfig::high(IndoorLightGridFarDistance);
        const uint64_t gridBeginTickCount = pLightingStats != nullptr ? SDL_GetTicksNS() : 0;
        m_lightGrid.upload(Engine::buildLightGrid(gridConfig, settings.lightGridEnabled
                ? IndoorLightingRuntime::gridLights(lightingFrame) : std::vector<Engine::LightGridLight>{},
            viewMatrix, projectionMatrix, {eye.x, eye.y, eye.z}));
        if (pLightingStats != nullptr)
        {
            pLightingStats->selectionNanoseconds += SDL_GetTicksNS() - gridBeginTickCount;
        }
    }
    const uint64_t texturedSubmitBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    const uint64_t portalDebugFacesTicks = portalDebugTicks();
    uint64_t texturedBatchCount = 0;
    uint64_t visibleTexturedBatchCount = 0;
    uint64_t submittedTexturedBatchCount = 0;
    uint64_t culledTexturedBatchCount = 0;

    if (bgfx::isValid(m_indoorLitProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && bgfx::isValid(m_indoorLightPositionsUniformHandle)
        && bgfx::isValid(m_indoorLightColorsUniformHandle)
        && bgfx::isValid(m_indoorLightParamsUniformHandle)
        && bgfx::isValid(m_secretPulseParamsUniformHandle)
        && bgfx::isValid(m_indoorSkyParamsUniformHandle)
        && bgfx::isValid(m_indoorSkyProjectionParamsUniformHandle))
    {
        const bool secretFacesDetected =
            m_map.has_value()
            && m_pSceneRuntime != nullptr
            && GameMechanics::partyDetectsSecretFaces(m_pSceneRuntime->partyRuntime().party(), m_map.value());

        // The visible opaque batches, drawn merged by group (translucent faces draw later, sorted; liquids with the
        // enhanced water are the water renderer's).
        m_mainViewDrawnBatches.assign(m_texturedBatches.size(), 0);
        for (size_t batchIndex = 0; batchIndex < m_texturedBatches.size(); ++batchIndex)
        {
            const TexturedBatch &batch = m_texturedBatches[batchIndex];
            ++texturedBatchCount;

            if (!indoorGeometrySectorsVisible(renderVisibleSectorMask, batch.sectorId, batch.backSectorId))
            {
                ++culledTexturedBatchCount;
                continue;
            }

            ++visibleTexturedBatchCount;
            m_mainViewDrawnBatches[batchIndex] =
                (enhancedWater && batch.waterColorAbgr != 0) || batch.translucent ? 0 : 1;
        }
        submittedTexturedBatchCount =
            submitMainViewFaces(m_mainViewDrawnBatches, viewWidth, viewHeight, secretFacesDetected);
    }

    if (portalDebug)
    {
        m_portalDebugStats.cpuFacesNanoseconds = SDL_GetTicksNS() - portalDebugFacesTicks;
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

    // With the eye under water every liquid is drawn after the open sky, so the world above shows through the
    // surface from below (MM9's surface is a see-through sprite), the opaque deep sea included.
    const bool eyeUnderWater =
        m_pSceneRuntime != nullptr && m_pSceneRuntime->partyRuntime().eyeWaterVolume() != nullptr;
    if (enhancedWater && !eyeUnderWater)
    {
        applySceneSkyFog();
        m_waterRenderer.renderIndoor(transparentView, m_elapsedTime, lightingFrame, eye, viewForward,
            settings.waterMovementRipples ? &m_worldFxSystem.waterRipples() : nullptr, nullptr, {},
            WaterSurfaceSet::Opaque);
    }

    const uint64_t bloodSplatsBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;

    if (settings.bloodSplats)
    {
        renderBloodSplats(
            transparentView,
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
    renderContextActionGeometryHighlight(transparentView, pContextActionState);

    const uint64_t decorationBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    uint64_t portalDebugSplitTicks = portalDebugTicks();
    renderDecorationBillboards(
        decorationView,
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
    if (portalDebug)
    {
        m_portalDebugStats.cpuDecorationsNanoseconds = SDL_GetTicksNS() - portalDebugSplitTicks;
        portalDebugSplitTicks = SDL_GetTicksNS();
    }

    const uint64_t actorBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    renderActorPreviewBillboards(
        actorView,
        viewMatrix,
        projectionMatrix,
        eye,
        renderVisibleSectorMask,
        lightingFrame,
        settings.spriteOutline,
        pContextActionState,
        &gameSession,
        &settings,
        pLightingStats);

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderActorNanoseconds += SDL_GetTicksNS() - actorBeginTickCount;
    }
    if (portalDebug)
    {
        m_portalDebugStats.cpuActorsNanoseconds = SDL_GetTicksNS() - portalDebugSplitTicks;
    }

    const uint64_t modelBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    m_modelRenderer.beginFrame();
    // The lights near the camera (torches, braziers, map lights): decoration highlights, and the colour that tints the
    // room environment models reflect.
    const IndoorLightSelectionBounds highlightBounds = {
        {eye.x - IndoorDecorationHighlightReach, eye.y - IndoorDecorationHighlightReach,
            eye.z - IndoorDecorationHighlightReach},
        {eye.x + IndoorDecorationHighlightReach, eye.y + IndoorDecorationHighlightReach,
            eye.z + IndoorDecorationHighlightReach}, true};
    const IndoorDrawLightSet highlights = IndoorLightingRuntime::selectDrawLightSetForBounds(
        lightingFrame, eye, viewForward, -1, -1, highlightBounds, pLightingStats, true);
    const std::array<float, 3> roomTint = indoorRoomEnvironmentTint(highlights);
    Engine::ModelRenderLighting modelLighting;
    modelLighting.ambient = lightingFrame.ambient;
    modelLighting.direct = 0.0f;
    modelLighting.environmentScale = roomTint;
    modelLighting.displaySpaceLighting = true;
    modelLighting.pLightGrid = &m_lightGrid;
    modelLighting.keyDirection = Engine::spriteKeyLightDirection({viewForward.x, viewForward.y, viewForward.z});
    modelLighting.keyFraction = IndoorModelKeyFraction;
    if (m_fog.enabled)
    {
        modelLighting.fogColor = indoorFogColorUniform(m_frameFog);
        modelLighting.fogDensities = indoorFogDensitiesUniform(m_frameFog);
        modelLighting.fogDistances = indoorFogDistancesUniform(m_frameFog);
        modelLighting.skyFog = m_openSky.outdoorView ? m_outdoorSkyFog : m_flatSkyFog;
    }
    if (m_modelLighting.enabled)
    {
        // MM9's model lighting (scene model_lighting) for creatures and decorations: the ambient and ModelAdd as the
        // base, the grid lights per pixel at their BLV colour.
        modelLighting.fixedFunctionLighting = true;
        modelLighting.fixedPointScale = m_modelLighting.lightScale / IndoorLightingRuntime::mapLightStrength();
        modelLighting.ambient = 1.0f;
        modelLighting.ambientColor = indoorModelLight(m_modelLighting, {0.0f, 0.0f, 0.0f});
    }
    if (m_pSceneRuntime != nullptr && runtimeMapDeltaData())
    {
        // Like actor sprites, actor models draw only in the sectors the portals reveal.
        const IndoorWorldRuntime &worldRuntime = m_pSceneRuntime->worldRuntime();
        const MapDeltaData &mapDeltaData = *runtimeMapDeltaData();
        m_worldFxSystem.setActorModelVisibility([&](size_t actorIndex)
        {
            const IndoorWorldRuntime::MapActorAiState *pActorAiState = worldRuntime.mapActorAiState(actorIndex);
            const int16_t sectorId = pActorAiState != nullptr && pActorAiState->sectorId >= 0
                ? pActorAiState->sectorId
                : actorIndex < mapDeltaData.actors.size() ? mapDeltaData.actors[actorIndex].sectorId : -1;
            return sectorVisibleForRuntimeBillboard(sectorId, &renderVisibleSectorMask);
        });
        m_worldFxSystem.setObjectModelVisibility([&](int16_t sectorId)
        {
            return sectorVisibleForRuntimeBillboard(sectorId, &renderVisibleSectorMask);
        });
    }
    bool modelGeometryCacheReady = false;
    const auto modelSector = [&](Engine::ModelInstanceHandle handle, const bx::Vec3 &center)
    {
        // A model is resampled after its centre moves a little.
        constexpr float ResampleDistanceSquared = 16.0f * 16.0f;
        if (handle.index >= m_modelSectorCache.size())
        {
            m_modelSectorCache.resize(handle.index + 1);
        }
        ModelSectorCacheEntry &entry = m_modelSectorCache[handle.index];
        const bx::Vec3 offset = bx::sub(center, entry.center);
        if (!entry.valid || entry.generation != handle.generation || bx::dot(offset, offset) > ResampleDistanceSquared)
        {
            if (!modelGeometryCacheReady)
            {
                // The world's face grid, so a lookup tests the faces near the model, not every face of its sector
                // (a region's open air is one sector of 27 000 faces, and every moving monster looks up each frame).
                m_modelSectorGeometryCache.reset(m_pIndoorMapData->faces.size());
                m_modelSectorGeometryCache.setSectorFaceGrid(
                    m_pSceneRuntime != nullptr ? m_pSceneRuntime->worldRuntime().sectorFaceGrid() : nullptr);
                modelGeometryCacheReady = true;
            }
            entry.generation = handle.generation;
            entry.center = center;
            entry.sectorId = findIndoorSectorForPoint(
                *m_pIndoorMapData, m_renderVertices, center, &m_modelSectorGeometryCache).value_or(-1);
            entry.valid = true;
        }
        return entry.sectorId;
    };
    const ViewFrustum modelFrustum(viewMatrix, projectionMatrix, bgfx::getCaps()->homogeneousDepth);
    const float modelFocalPixels = settings.modelLods ? std::abs(projectionMatrix[5]) * viewHeight * 0.5f : 0.0f;
    portalDebugSplitTicks = portalDebugTicks();
    if (!m_decorationModels.empty())
    {
        // Each placement's ambient carries the light its sprite would receive (updateDecorationModels); the key
        // light shapes it as it shapes the creatures.
        updateDecorationModels(renderVisibleSectorMask, lightingFrame, pContextActionState, pLightingStats);
        Engine::ModelRenderLighting decorationLighting = modelLighting;
        if (m_modelLighting.enabled)
        {
            // MM9's model lighting: each placement's light is the base, the grid lights add with N.L.
            decorationLighting.ambientColor = {1.0f, 1.0f, 1.0f};
        }
        else
        {
            decorationLighting.keyFraction = IndoorDecorationKeyFraction;
            decorationLighting.ambient = IndoorDecorationExposure;
            // The reflection is ambient x environmentScale (the room environment, tinted); a creature's is the frame
            // ambient.
            const float sheen = lightingFrame.ambient * IndoorDecorationReflection / IndoorDecorationExposure;
            decorationLighting.environmentScale = {sheen * roomTint[0], sheen * roomTint[1], sheen * roomTint[2]};
            // Highlights from the view's lights (the grid; the nearest 12 where a view has none): only the specular
            // lobe, since each placement's light already carries their diffuse share.
            decorationLighting.pointPositions = highlights.positions;
            decorationLighting.pointColors = highlights.colors;
            decorationLighting.pointCount = uint32_t(highlights.lightCount);
            decorationLighting.pointSpecularOnly = true;
            applyDaylightSun(decorationLighting, 1.0f);
        }
        m_modelRenderer.renderStatic(m_decorationModels.groups(), decorationSolidView, {eye.x, eye.y, eye.z},
            decorationLighting, nullptr,
            [&](const Engine::ModelBounds &bounds)
            {
                return modelFrustum.intersectsBounds({bounds.min[0], bounds.min[1], bounds.min[2]},
                    {bounds.max[0], bounds.max[1], bounds.max[2]});
            }, modelFocalPixels, settings.modelLodOverride, float(SDL_GetTicks()) * 0.001f, decorationView);
    }
    // The low bushes placed with the terrain's grass (TerrainBushSet), lit as the decorations in the open sky without
    // highlights (foliage has no specular to take from the lights).
    if (!m_terrainBushes.empty() && settings.terrainDecorations)
    {
        updateTerrainBushes(eye);
        Engine::ModelRenderLighting bushLighting = modelLighting;
        bushLighting.keyFraction = IndoorDecorationKeyFraction;
        bushLighting.ambient = IndoorDecorationExposure;
        applyDaylightSun(bushLighting, 1.0f);
        m_modelRenderer.renderStatic(m_terrainBushes.groups(), decorationSolidView, {eye.x, eye.y, eye.z},
            bushLighting, nullptr,
            [&](const Engine::ModelBounds &bounds)
            {
                return modelFrustum.intersectsBounds({bounds.min[0], bounds.min[1], bounds.min[2]},
                    {bounds.max[0], bounds.max[1], bounds.max[2]});
            }, modelFocalPixels, settings.modelLodOverride, float(SDL_GetTicks()) * 0.001f, decorationView);
    }
    if (portalDebug)
    {
        m_portalDebugStats.cpuDecorationsNanoseconds += SDL_GetTicksNS() - portalDebugSplitTicks;
        portalDebugSplitTicks = SDL_GetTicksNS();
    }
    m_modelRenderer.render(
        m_worldFxSystem.models(),
        actorSolidView,
        {eye.x, eye.y, eye.z},
        modelLighting,
        // Creatures read their point lights from the grid; per model only their room: its ambient and the grid
        // lights that reach it. Both are instance data, so creatures still draw instanced.
        [&](Engine::ModelInstanceHandle handle, const Engine::ModelBounds &bounds)
        {
            Engine::ModelRenderLighting lighting = modelLighting;
            if (m_pIndoorMapData != nullptr)
            {
                lighting.sector = modelSector(handle, {(bounds.min[0] + bounds.max[0]) * 0.5f,
                    (bounds.min[1] + bounds.max[1]) * 0.5f, (bounds.min[2] + bounds.max[2]) * 0.5f});
                if (!m_modelLighting.enabled)
                {
                    lighting.ambient = IndoorLightingRuntime::sectorAmbient(lightingFrame, lighting.sector);
                    if (indoorDaylightSector(m_daylight, lighting.sector))
                    {
                        // In the open air: the daylight's ambient all round and its sun by direction.
                        lighting.ambient = indoorDaylightModelAmbient(m_frameDaylight);
                        applyDaylightSun(lighting, 1.0f);
                    }
                }
            }
            return lighting;
        }, nullptr,
        [&](const Engine::ModelBounds &bounds)
        {
            return modelFrustum.intersectsBounds({bounds.min[0], bounds.min[1], bounds.min[2]},
                {bounds.max[0], bounds.max[1], bounds.max[2]});
        }, modelFocalPixels, settings.modelLodOverride, float(SDL_GetTicks()) * 0.001f, actorView);
    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderParticleNanoseconds += SDL_GetTicksNS() - modelBeginTickCount;
    }
    if (portalDebug)
    {
        m_portalDebugStats.cpuActorsNanoseconds += SDL_GetTicksNS() - portalDebugSplitTicks;
        portalDebugSplitTicks = SDL_GetTicksNS();
    }

    // Grass over the terrain (scene `terrain: {grass}`), before the sky shades the uncovered pixels.
    if (settings.terrainDecorations && !m_grassConfigPath.empty())
    {
        renderTerrainGrass(MainViewId, eye, viewForward, projectionMatrix,
            float(viewWidth) / float(std::max<int>(viewHeight, 1)));
    }

    // The weather over the open sky (scene `sky: {weather}`). Rain and snow fall wherever the roof map leaves the sky
    // open, so they show through doors and windows but never under a roof; the camera under one (a house, a tunnel)
    // hears the storm muffled, under water not at all. Without a roof map (a GPU without vertex texture reads) the
    // weather shows only with the camera in a sector open to the sky.
    const int16_t weatherEyeSector = m_renderPortalVisibilityCache.valid ? m_renderPortalVisibilityCache.sectorId : -1;
    const bool weatherEyeUnderWater =
        m_pSceneRuntime != nullptr && m_pSceneRuntime->partyRuntime().eyeWaterVolume() != nullptr;
    const bool weatherEyeSectorOpen = weatherEyeSector >= 0 && size_t(weatherEyeSector) < m_openSkySectors.size()
        && m_openSkySectors[size_t(weatherEyeSector)] != 0;
    const bool weatherRoofMap = m_openSkyWeather.hasRoofMap();
    const bool weatherEyeCovered =
        weatherRoofMap ? m_openSkyWeather.covers(eye.x, eye.y, eye.z) : !weatherEyeSectorOpen;
    const bool weatherShown = m_openSkyWeather.active() && !weatherEyeUnderWater
        && (weatherRoofMap || weatherEyeSectorOpen);
    if (m_openSkyWeather.active())
    {
        const double weatherGameMinutes =
            m_pSceneRuntime != nullptr ? m_pSceneRuntime->worldRuntime().gameMinutes() : 9.0 * 60.0;
        const float weatherAudibility = weatherEyeUnderWater ? 0.0f
            : weatherEyeCovered ? CoveredWeatherAudibility : 1.0f;
        m_openSkyWeather.update(weatherGameMinutes, m_elapsedTime, m_pWeatherAudio, weatherAudibility);
        m_waterRenderer.setRainRings(settings.rainRipples ? m_openSkyWeather.rainRings() : 0.0f,
            settings.weatherQuality == WeatherQuality::High ? 2 : 1);
    }

    // The open sky shades only the pixels the solid scene left uncovered, before anything blends over them.
    renderOpenSky(openSkyView, viewMatrix, projectionMatrix);
    if (portalDebug)
    {
        m_portalDebugStats.cpuOpenSkyNanoseconds = SDL_GetTicksNS() - portalDebugSplitTicks;
        portalDebugSplitTicks = SDL_GetTicksNS();
    }

    // See-through liquids (liquids.yml opacity) blend over the completed solid scene: their bed, and the creatures and
    // models standing in them, show through.
    if (enhancedWater)
    {
        applySceneSkyFog();
        m_waterRenderer.renderIndoor(translucentView, m_elapsedTime, lightingFrame, eye, viewForward,
            settings.waterMovementRipples ? &m_worldFxSystem.waterRipples() : nullptr, nullptr, {},
            eyeUnderWater ? WaterSurfaceSet::All : WaterSurfaceSet::SeeThrough);
    }

    // Translucent faces (window glass) blend over the solid scene, before the spells, particles and effects.
    if (m_pIndoorMapData != nullptr && !m_pIndoorMapData->translucentFaces.empty())
    {
        const bool secretFacesDetected = m_map.has_value() && m_pSceneRuntime != nullptr
            && GameMechanics::partyDetectsSecretFaces(m_pSceneRuntime->partyRuntime().party(), m_map.value());
        renderTranslucentFaces(translucentView, eye, renderVisibleSectorMask, viewWidth, viewHeight,
            secretFacesDetected);
    }

    // Spell billboards blend with the completed solid scene, including creatures and models.
    const uint64_t spriteObjectBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    renderSpriteObjectBillboards(
        translucentView,
        viewMatrix,
        eye,
        renderVisibleSectorMask,
        lightingFrame,
        settings.spriteOutline,
        pContextActionState,
        pLightingStats);

    if (collectRenderDiagnostics)
    {
        m_indoorPerformanceDiagnostics.renderSpriteObjectNanoseconds +=
            SDL_GetTicksNS() - spriteObjectBeginTickCount;
    }

    const uint64_t particlesBeginTickCount = collectRenderDiagnostics ? SDL_GetTicksNS() : 0;
    renderFxSegmentProjectiles(translucentView, viewMatrix);
    if (settings.mist && settings.mistWisps && m_mist.enabled())
    {
        // The mist's wisps near the eye (devdocs/MIST.md "Wisps").
        m_mistWisps.update(m_mist, {eye.x, eye.y, eye.z}, m_elapsedTime, m_frameMistLight, m_worldFxSystem.particles());
    }
    ParticleRenderer::renderParticles(
        m_worldFxRenderResources,
        m_worldFxSystem.particles(),
        translucentView,
        viewMatrix,
        eye,
        static_cast<float>(viewWidth) / static_cast<float>(viewHeight),
        m_worldFxSystem.glowBillboards());
    if (m_pAssetFileSystem != nullptr)
    {
        m_effectRenderer.render(
            m_worldFxRenderResources,
            m_worldFxSystem.namedEffects(),
            m_worldFxSystem.namedEffectResources(),
            *m_pAssetFileSystem,
            translucentView,
            viewMatrix,
            eye);
    }
    m_shieldDomeRenderer.render(translucentView, m_worldFxSystem.shieldDomes(), eye,
        m_worldFxSystem.shieldDomeTimeSeconds());
    if (weatherShown)
    {
        // No splashes yet: the indoor floor query is not wired to the weather (WeatherGroundQuery left empty).
        m_openSkyWeather.render(translucentView, {eye.x, eye.y, eye.z}, m_cameraYawRadians, projectionMatrix,
            viewHeight, m_skyRenderer.isReady() ? &m_skyRenderer.frame() : nullptr, settings.weatherQuality, {},
            weatherEyeCovered, m_frameFog.enabled ? &m_frameFog.color : nullptr);
    }
    renderWaterTint(translucentView);
    // A cinematic draws no health bars (the HUD is hidden).
    if (!cinematic.takesOverView())
    {
        EnemyHealthBarRenderer::render(gameSession.gameplayScreenRuntime(), m_pendingEnemyHealthBars, translucentView,
            eye, viewMatrix, projectionMatrix, m_lastRenderHeight);
    }
    m_pendingEnemyHealthBars.clear();
    if (m_pPostProcessing != nullptr && (m_modelRenderer.glowDrawn() || m_worldFxRenderResources.glowDrawn()))
    {
        m_pPostProcessing->markGlowDrawn();
    }

    if (portalDebug)
    {
        m_portalDebugStats.cpuTranslucentNanoseconds = SDL_GetTicksNS() - portalDebugSplitTicks;
        m_portalDebugStats.cpuTotalNanoseconds = SDL_GetTicksNS() - portalDebugBeginTicks;
        collectPortalDebugStats(renderVisibleSectorMask, viewMatrix, projectionMatrix, eye);
        renderPortalDebugOverlay(translucentView, renderVisibleSectorMask);
    }

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

bool IndoorRenderer::isWaterSupportFace(size_t faceIndex) const
{
    if (faceIndex >= m_faceBatchIndices.size())
    {
        return false;
    }
    const int32_t batchIndex = m_faceBatchIndices[faceIndex];
    return batchIndex >= 0 && size_t(batchIndex) < m_texturedBatches.size()
        && m_texturedBatches[size_t(batchIndex)].waterColorAbgr != 0;
}

WorldFxSystem &IndoorRenderer::worldFxSystem()
{
    return m_worldFxSystem;
}

const WorldFxSystem &IndoorRenderer::worldFxSystem() const
{
    return m_worldFxSystem;
}

std::optional<DecorationPortraitModel> IndoorRenderer::decorationPortraitModel(uint32_t spriteOverrideKey) const
{
    return m_indoorDecorationBillboardSet
        ? m_decorationModels.portraitModel(m_indoorDecorationBillboardSet->billboards, spriteOverrideKey)
        : std::nullopt;
}

bool IndoorRenderer::ensureMonsterVisualResources(int16_t monsterId)
{
    if (m_pAssetFileSystem == nullptr || !m_monsterTable || monsterId <= 0)
    {
        return false;
    }

    if (!m_indoorActorPreviewBillboardSet)
    {
        m_indoorActorPreviewBillboardSet.emplace();
    }

    return ensureMonsterSpriteFramesLoaded(
        *m_pAssetFileSystem,
        *m_monsterTable,
        monsterId,
        m_indoorActorPreviewBillboardSet->spriteFrameTable,
        m_indoorActorPreviewBillboardSet->actorModels.get());
}

const SpriteFrameTable *IndoorRenderer::actorSpriteFrameTable() const
{
    return m_indoorActorPreviewBillboardSet ? &m_indoorActorPreviewBillboardSet->spriteFrameTable : nullptr;
}

const EffectRenderer::Diagnostics &IndoorRenderer::effectRenderDiagnostics() const
{
    return m_effectRenderer.diagnostics();
}

bgfx::ProgramHandle IndoorRenderer::hudTexturedProgramHandle() const
{
    return m_texturedProgramHandle;
}

bgfx::UniformHandle IndoorRenderer::hudTextureSamplerHandle() const
{
    return m_textureSamplerHandle;
}

bgfx::ProgramHandle IndoorRenderer::hudTintedProgramHandle() const
{
    return m_hudTintedProgramHandle;
}

bgfx::UniformHandle IndoorRenderer::hudTintUniformHandle() const
{
    return m_hudTintUniformHandle;
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
        || !m_pIndoorMapData
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
        IndoorCameraNearClipDistance,
        cameraFarClipDistance(),
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
            const IndoorWorldRuntime::MapActorAiState *pActorAiState =
                m_pSceneRuntime->worldRuntime().mapActorAiState(actor.actorIndex);

            // A model actor has no sprite; the inspect ray below picks its model.
            if (!isSectorVisible(actor.sectorId, visibleSectorMask) || m_worldFxSystem.hasActorModel(actor.actorIndex)
                || (pActorAiState != nullptr && m_indoorActorPreviewBillboardSet->drawsModel(pActorAiState->monsterId)))
            {
                continue;
            }

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
            const bx::Vec3 center = spriteBillboardCenter(
                static_cast<float>(actor.x),
                static_cast<float>(actor.y),
                static_cast<float>(actor.z),
                cameraRight, cameraUp, *pTexture, spriteScale, resolvedTexture.mirrored);
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

            if (!pTexture->opacityMask.isOpaqueNormalized(normalizedU, normalizedV))
            {
                continue;
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
        inspectAtCursor(*m_pIndoorMapData, m_renderVertices, visibleSectorMask, rayOrigin, rayDirection);

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
    const float cosPitch = std::cos(viewPitchRadians());
    const float sinPitch = std::sin(viewPitchRadians());
    const float cosYaw = std::cos(viewYawRadians());
    const float sinYaw = std::sin(viewYawRadians());
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
        IndoorCameraNearClipDistance,
        cameraFarClipDistance(),
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
        || !m_pIndoorMapData
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
        *m_pIndoorMapData,
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
            if (inspectHit.containedItemId != 0 && m_pItemTable != nullptr
                && !m_pItemTable->hasGroundModel(inspectHit.containedItemId))
            {
                worldItemHit.missingGroundModelItemId = inspectHit.containedItemId;
            }
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
    const std::optional<uint16_t> interactiveEventId = resolveInteractiveDecorationHitEventId(inspectHit);
    const uint16_t eventId = inspectHitEventId(inspectHit);
    eventTargetHit.nameEventId = interactiveEventId.value_or(eventId);
    eventTargetHit.nameEventIsLocal = !interactiveEventId;
    eventTargetHit.hitPoint = hitPoint;
    eventTargetHit.distance = inspectHit.distance;
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

        if (!m_pIndoorMapData || pEventRuntimeState == nullptr)
        {
            return 0;
        }

        const std::optional<IndoorInteractiveDecorationBinding> binding =
            resolveIndoorInteractiveDecorationBinding(
                m_indoorInteractiveDecorationDecorVarIndicesByEntity,
                m_indoorInteractiveDecorationBaseEventIdsByEntity,
                m_indoorInteractiveDecorationEventCountsByEntity,
                m_indoorInteractiveDecorationHideWhenClearedByEntity,
                m_indoorInteractiveDecorationFixedEventByEntity,
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

    const DecorationLookupResult decoration =
        m_indoorDecorationBillboardSet->decorationTable.resolveMapDecoration(
            inspectHit.decorationListId,
            inspectHit.name);
    const DecorationEntry *pDecoration = decoration.pEntry;

    if (pDecoration != nullptr && !pDecoration->hint.empty())
    {
        return Engine::localize(pDecoration->hint);
    }

    return std::nullopt;
}

std::optional<uint16_t> IndoorRenderer::resolveInteractiveDecorationHitEventId(const InspectHit &inspectHit) const
{
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (inspectHit.kind != "entity" || pEventRuntimeState == nullptr)
    {
        return std::nullopt;
    }

    const std::optional<IndoorInteractiveDecorationBinding> binding =
        resolveIndoorInteractiveDecorationBinding(
            m_indoorInteractiveDecorationDecorVarIndicesByEntity,
            m_indoorInteractiveDecorationBaseEventIdsByEntity,
            m_indoorInteractiveDecorationEventCountsByEntity,
            m_indoorInteractiveDecorationHideWhenClearedByEntity,
            m_indoorInteractiveDecorationFixedEventByEntity,
            inspectHit.index);

    return binding ? resolveIndoorInteractiveDecorationEventId(*pEventRuntimeState, *binding) : std::nullopt;
}

std::optional<std::string> IndoorRenderer::resolveEventTargetHoverStatusText(const InspectHit &inspectHit) const
{
    if (inspectHit.kind == "entity")
    {
        if (const std::optional<uint16_t> eventId = resolveInteractiveDecorationHitEventId(inspectHit))
        {
            const std::optional<std::string> eventHint = resolveIndoorGlobalEventHintText(m_pSceneRuntime, *eventId);

            if (eventHint && !eventHint->empty())
            {
                return eventHint;
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

    if (!m_isInitialized
        || !m_isRenderable
        || !m_pIndoorMapData
        || rayRequest.viewWidth <= 0
        || rayRequest.viewHeight <= 0)
    {
        return {};
    }

    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, rayRequest.viewMatrix.data(), rayRequest.projectionMatrix.data());

    // The usable target nearest the crosshair, weighed by how far it is: the crosshair hit itself is tried first by
    // GameplayInteractionController::pickKeyboardUseTarget.
    float bestScore = std::numeric_limits<float>::max();
    GameplayWorldHit bestHit = {};
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

            for (size_t faceIndex = 0; faceIndex < m_pIndoorMapData->faces.size(); ++faceIndex)
            {
                const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];

                if (face.vertexIndices.size() < 3
                    || face.isPortal
                    || indoorFaceMarkedAsCeiling(*m_pIndoorMapData, faceIndex, face)
                    || hasFaceAttribute(face.attributes, FaceAttribute::IsPortal)
                    || indoorFacePassesPicks(*m_pIndoorMapData, faceIndex, face.cogTriggered, face.attributes)
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
            const float score = screenDistance * 4.0f + worldDistance;

            // The line-of-sight test walks every face, so it runs only for a candidate that would win.
            if (score >= bestScore || levelBlocksWorldPoint(worldPoint))
            {
                return;
            }

            bestScore = score;
            bestHit = std::move(worldHit);
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
            if (object.containedItemId != 0 && m_pItemTable != nullptr
                && !m_pItemTable->hasGroundModel(object.containedItemId))
            {
                worldItemHit.missingGroundModelItemId = object.containedItemId;
            }

            GameplayWorldHit worldHit = {};
            worldHit.hasHit = true;
            worldHit.kind = GameplayWorldHitKind::WorldItem;
            worldHit.worldItem = worldItemHit;
            appendProjectedWorldHitCandidate(hitPoint, worldHit, -1.0f);
        }
    }

    for (size_t faceIndex = 0; faceIndex < m_pIndoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];

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
        appendProjectedWorldHitCandidate(center, worldHit, KeyboardEventFaceScreenRadius);
    }

    // Decorations with an event (sacks, barrels, chests, torches that toggle) anywhere on screen, as the original
    // scans every visible billboard. Their middle is the point tested for line of sight.
    if (m_indoorDecorationBillboardSet)
    {
        for (const DecorationBillboard &billboard : m_indoorDecorationBillboardSet->billboards)
        {
            if (billboard.entityIndex >= m_pIndoorMapData->entities.size()
                || !isRenderSectorVisible(billboard.sectorId, visibleSectorMask))
            {
                continue;
            }

            bool hidden = false;

            if (resolveDecorationBillboardSpriteId(billboard, hidden) == 0 || hidden)
            {
                continue;
            }

            const IndoorEntity &entity = m_pIndoorMapData->entities[billboard.entityIndex];
            const bx::Vec3 center = {
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z) + static_cast<float>(std::max<uint16_t>(billboard.height, 32)) * 0.5f
            };
            const bx::Vec3 toCenter = vecSubtract(center, rayRequest.eye);
            const float centerDistance = vecLength(toCenter);

            if (centerDistance <= InspectRayEpsilon)
            {
                continue;
            }

            InspectHit inspectHit = {};
            inspectHit.hasHit = true;
            inspectHit.kind = "entity";
            inspectHit.index = billboard.entityIndex;
            inspectHit.name = entity.name;
            inspectHit.distance = centerDistance;
            inspectHit.decorationListId = entity.decorationListId;
            inspectHit.eventIdPrimary = entity.eventIdPrimary;
            inspectHit.eventIdSecondary = entity.eventIdSecondary;
            inspectHit.variablePrimary = entity.variablePrimary;
            inspectHit.variableSecondary = entity.variableSecondary;
            inspectHit.specialTrigger = entity.specialTrigger;

            GameplayWorldPickRequest centerRequest = rayRequest;
            centerRequest.rayOrigin = rayRequest.eye;
            centerRequest.rayDirection = vecNormalize(toCenter);
            appendProjectedWorldHitCandidate(
                center, translateInspectHitToGameplayWorldHit(inspectHit, centerRequest), -1.0f);
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
                if (faceId >= m_pIndoorMapData->faces.size())
                {
                    continue;
                }

                const IndoorFace &face = m_pIndoorMapData->faces[faceId];

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

    return bestHit;
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

bool IndoorRenderer::projectGameplayWorldPointToScreen(
    const bx::Vec3 &point,
    int viewWidth,
    int viewHeight,
    float &screenX,
    float &screenY) const
{
    viewWidth = std::max(viewWidth, 1);
    viewHeight = std::max(viewHeight, 1);

    const float aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
    const float cosYaw = std::cos(viewYawRadians());
    const float sinYaw = std::sin(viewYawRadians());
    const float cosPitch = std::cos(viewPitchRadians());
    const float sinPitch = std::sin(viewPitchRadians());
    const bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
    const bx::Vec3 at = {
        eye.x + cosYaw * cosPitch,
        eye.y + sinYaw * cosPitch,
        eye.z + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    float viewProjectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        IndoorCameraVerticalFovDegrees,
        aspectRatio,
        IndoorCameraNearClipDistance,
        cameraFarClipDistance(),
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right);
    bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);

    ProjectedPoint projected = {};

    if (!projectWorldPointToScreen(point, viewWidth, viewHeight, viewProjectionMatrix, projected))
    {
        return false;
    }

    screenX = projected.x;
    screenY = projected.y;
    return true;
}

std::optional<size_t> IndoorRenderer::gameplayHoveredActorIndex() const
{
    if (!m_cachedInspectHitValid || m_cachedInspectHit.kind != "actor")
    {
        return std::nullopt;
    }

    return m_cachedInspectHit.index;
}

std::vector<size_t> IndoorRenderer::gameplayVisibleHostileActorIndices() const
{
    if (!m_isInitialized
        || !m_isRenderable
        || m_pSceneRuntime == nullptr
        || m_lastRenderWidth <= 0
        || m_lastRenderHeight <= 0)
    {
        return {};
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
        IndoorCameraNearClipDistance,
        cameraFarClipDistance(),
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );
    bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);

    std::vector<std::pair<float, size_t>> visible;
    IGameplayWorldRuntime &worldRuntime = m_pSceneRuntime->worldRuntime();

    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!worldRuntime.actorRuntimeState(actorIndex, actorState)
            || actorState.isDead
            || actorState.isInvisible
            || !actorState.hostileToParty)
        {
            continue;
        }

        const bx::Vec3 actorPoint = {
            actorState.preciseX,
            actorState.preciseY,
            actorState.preciseZ + actorState.targetHeight
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

        if (!m_pSceneRuntime->worldRuntime().partyAttackActorHasLineOfSight(actorIndex))
        {
            continue;
        }

        const float deltaX = actorState.preciseX - eye.x;
        const float deltaY = actorState.preciseY - eye.y;
        const float deltaZ = actorState.preciseZ - eye.z;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

        visible.emplace_back(distanceSquared, actorIndex);
    }

    std::sort(visible.begin(), visible.end());
    std::vector<size_t> actorIndices;
    actorIndices.reserve(visible.size());

    for (const auto &[distanceSquared, actorIndex] : visible)
    {
        actorIndices.push_back(actorIndex);
    }

    return actorIndices;
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
        actorState.preciseZ + actorState.targetHeight
    };
}

std::optional<bx::Vec3> IndoorRenderer::gameplayActorNearestOpaquePoint(
    size_t actorIndex,
    const GameplayPartyAttackFallbackQuery &query) const
{
    if (query.viewWidth <= 0
        || query.viewHeight <= 0
        || !m_monsterTable
        || !m_indoorActorPreviewBillboardSet
        || m_pSceneRuntime == nullptr
        || !runtimeMapDeltaData())
    {
        return std::nullopt;
    }

    // A model presents the actor: where the line from the camera to its bounds' centre enters them.
    if (m_worldFxSystem.hasActorModel(actorIndex))
    {
        const Engine::ModelBounds *pBounds = m_worldFxSystem.actorModelBounds(actorIndex);
        if (pBounds == nullptr || !pBounds->valid)
        {
            return std::nullopt;
        }
        const bx::Vec3 origin = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
        const bx::Vec3 minBounds = {pBounds->min[0], pBounds->min[1], pBounds->min[2]};
        const bx::Vec3 maxBounds = {pBounds->max[0], pBounds->max[1], pBounds->max[2]};
        const bx::Vec3 toCenter = bx::sub(bx::mul(bx::add(minBounds, maxBounds), 0.5f), origin);
        const float length = bx::length(toCenter);
        float distance = 0.0f;
        if (length <= 0.0f
            || !intersectRayAabb(origin, bx::mul(toCenter, 1.0f / length), minBounds, maxBounds, distance))
        {
            return std::nullopt;
        }
        return bx::mad(toCenter, distance / length, origin);
    }

    const std::optional<RuntimeActorBillboard> actor = buildRuntimeActorBillboard(
        *m_monsterTable,
        m_indoorActorPreviewBillboardSet->spriteFrameTable,
        *runtimeMapDeltaData(),
        actorIndex,
        &m_pSceneRuntime->worldRuntime());
    if (!actor)
    {
        return std::nullopt;
    }

    const IndoorWorldRuntime::MapActorAiState *pActorAiState =
        m_pSceneRuntime->worldRuntime().mapActorAiState(actorIndex);
    uint16_t spriteFrameIndex = actor->spriteFrameIndex;
    uint32_t frameTimeTicks = actor->useStaticFrame ? 0U : currentAnimationTicks();
    if (pActorAiState != nullptr)
    {
        const size_t animationIndex = static_cast<size_t>(pActorAiState->animationState);
        if (animationIndex < actor->actionSpriteFrameIndices.size()
            && actor->actionSpriteFrameIndices[animationIndex] != 0)
        {
            spriteFrameIndex = actor->actionSpriteFrameIndices[animationIndex];
        }
        frameTimeTicks = static_cast<uint32_t>(std::max(0.0f, pActorAiState->animationTimeTicks));
    }

    const SpriteFrameEntry *pFrame =
        m_indoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, frameTimeTicks);
    if (pFrame == nullptr)
    {
        return std::nullopt;
    }

    const float angleToCamera = std::atan2(
        static_cast<float>(actor->y) - m_cameraPositionY,
        static_cast<float>(actor->x) - m_cameraPositionX);
    const float actorYawRadians = pActorAiState != nullptr ? pActorAiState->yawRadians : 0.0f;
    const float octantAngle = actorYawRadians - angleToCamera + Pi + (Pi / 8.0f);
    const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
    const BillboardTextureHandle *pTexture = findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);
    if (pTexture == nullptr || pTexture->width <= 0.0f || pTexture->height <= 0.0f)
    {
        return std::nullopt;
    }

    const float spriteScale = std::max(pFrame->scale * actor->heightScale, 0.01f);
    const float worldWidth = pTexture->width * spriteScale;
    const float worldHeight = pTexture->height * spriteScale;
    const bx::Vec3 cameraRight = {
        query.viewMatrix[0],
        query.viewMatrix[4],
        query.viewMatrix[8],
    };
    const bx::Vec3 cameraUp = {
        query.viewMatrix[1],
        query.viewMatrix[5],
        query.viewMatrix[9],
    };
    const BillboardQuad quad = billboardQuad(
        spriteBillboardCenter(
            static_cast<float>(actor->x),
            static_cast<float>(actor->y),
            static_cast<float>(actor->z),
            cameraRight,
            cameraUp,
            *pTexture,
            spriteScale,
            resolvedTexture.mirrored),
        cameraRight,
        cameraUp,
        worldWidth,
        worldHeight);
    const bx::Vec3 topLeft = bx::add(bx::sub(quad.center, quad.right), quad.up);
    const bx::Vec3 topRight = bx::add(bx::add(quad.center, quad.right), quad.up);
    const bx::Vec3 bottomLeft = bx::sub(bx::sub(quad.center, quad.right), quad.up);
    const bx::Vec3 bottomRight = bx::sub(bx::add(quad.center, quad.right), quad.up);
    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, query.viewMatrix.data(), query.projectionMatrix.data());
    ProjectedPoint projectedTopLeft = {};
    ProjectedPoint projectedTopRight = {};
    ProjectedPoint projectedBottomLeft = {};
    ProjectedPoint projectedBottomRight = {};

    if (!projectWorldPointToScreen(
            topLeft, query.viewWidth, query.viewHeight, viewProjectionMatrix, projectedTopLeft)
        || !projectWorldPointToScreen(
            topRight, query.viewWidth, query.viewHeight, viewProjectionMatrix, projectedTopRight)
        || !projectWorldPointToScreen(
            bottomLeft, query.viewWidth, query.viewHeight, viewProjectionMatrix, projectedBottomLeft)
        || !projectWorldPointToScreen(
            bottomRight, query.viewWidth, query.viewHeight, viewProjectionMatrix, projectedBottomRight))
    {
        return std::nullopt;
    }

    const float left = std::min(
        std::min(projectedTopLeft.x, projectedTopRight.x),
        std::min(projectedBottomLeft.x, projectedBottomRight.x));
    const float right = std::max(
        std::max(projectedTopLeft.x, projectedTopRight.x),
        std::max(projectedBottomLeft.x, projectedBottomRight.x));
    const float top = std::min(
        std::min(projectedTopLeft.y, projectedTopRight.y),
        std::min(projectedBottomLeft.y, projectedBottomRight.y));
    const float bottom = std::max(
        std::max(projectedTopLeft.y, projectedTopRight.y),
        std::max(projectedBottomLeft.y, projectedBottomRight.y));
    if (right <= left || bottom <= top)
    {
        return std::nullopt;
    }

    return nearestOpaqueBillboardPoint(
        quad,
        pTexture->opacityMask,
        resolvedTexture.mirrored,
        (query.screenX - left) / (right - left),
        (query.screenY - top) / (bottom - top));
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

float IndoorRenderer::viewAspectRatio() const
{
    return m_lastRenderWidth > 0 && m_lastRenderHeight > 0
        ? static_cast<float>(m_lastRenderWidth) / static_cast<float>(m_lastRenderHeight)
        : 4.0f / 3.0f;
}

float IndoorRenderer::viewYawRadians() const
{
    return m_viewShakeYawRadians + (m_pSceneRuntime != nullptr
        ? m_cameraYawRadians + m_pSceneRuntime->worldRuntime().actorHitFeedback().cameraKickYawRadians()
        : m_cameraYawRadians);
}

float IndoorRenderer::viewPitchRadians() const
{
    return m_viewShakePitchRadians + (m_pSceneRuntime != nullptr
        ? m_cameraPitchRadians + m_pSceneRuntime->worldRuntime().actorHitFeedback().cameraKickPitchRadians()
        : m_cameraPitchRadians);
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
            if (!m_pIndoorMapData)
            {
                return false;
            }

            const size_t faceIndex =
                eventTarget.secondaryIndex != GameplayInvalidWorldIndex
                    ? eventTarget.secondaryIndex
                    : eventTarget.targetIndex;

            if (faceIndex >= m_pIndoorMapData->faces.size())
            {
                return false;
            }

            const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];
            const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
            const uint32_t effectiveAttributes =
                mapDeltaData && faceIndex < mapDeltaData->faceAttributes.size()
                    ? mapDeltaData->faceAttributes[faceIndex]
                    : face.attributes;

            if (!indoorFaceHasActualEvent(m_pSceneRuntime, face)
                || !isFaceVisible(faceIndex, face, runtimeMapDeltaData(), runtimeEventRuntimeStateStorage())
                || indoorFaceSuppressedForContextAction(
                    *m_pIndoorMapData,
                    faceIndex,
                    face,
                    effectiveAttributes,
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
        return inspectHitEventId(*inspectHit) != 0
            || (m_pIndoorMapData && m_indoorDecorationBillboardSet && runtimeEventRuntimeState() != nullptr
                && indoorDecorationLightToggleTarget(*m_pIndoorMapData,
                    m_indoorDecorationBillboardSet->decorationTable, inspectHit->index,
                    runtimeEventRuntimeState()) != nullptr);
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

void IndoorRenderer::setOpenSkyWeather(const std::optional<OutdoorWeatherProfile> &profile,
    GameAudioSystem *pAudioSystem)
{
    m_pWeatherAudio = pAudioSystem;
    m_openSkyWeather.configure(m_openSky.enabled ? profile : std::nullopt);

    // Rain and snow stop at the map's roofs, bridges and the ground over its tunnels (WeatherRoofMap).
    if (m_openSkyWeather.active() && m_pIndoorMapData != nullptr)
    {
        m_openSkyWeather.setRoofMap(buildIndoorWeatherRoofMap(*m_pIndoorMapData));
    }
}

void IndoorRenderer::renderOpenSky(uint16_t viewId, const float *pViewMatrix, const float *pProjectionMatrix)
{
    if (!m_openSky.enabled || m_pAssetFileSystem == nullptr)
    {
        return;
    }

    if (!m_skyRenderer.isReady())
    {
        if (m_skyRendererInitializeAttempted)
        {
            return;
        }

        m_skyRendererInitializeAttempted = true;

        if (!m_skyRenderer.initialize(*m_pAssetFileSystem))
        {
            return;
        }
    }

    SkyInputs inputs = {};
    if (m_pSceneRuntime != nullptr)
    {
        inputs.gameMinutes = m_pSceneRuntime->worldRuntime().gameMinutes();
    }
    inputs.weatherSkyName = m_openSky.skyTexture;
    inputs.forcedPreset = m_openSky.preset;
    inputs.mapFileName = m_map ? m_map->fileName : std::string();
    // MM9's sky in fog (scene fog `sky`): the sky drawn in this frame's fog colour.
    inputs.fogCover = indoorFogSkyCover(m_frameFog);
    inputs.fogCoverDisplay = m_frameFog.color;
    m_openSkyWeather.applyToSky(inputs);
    const float deltaSeconds = m_lastSkyStateElapsedTime >= 0.0f
        ? std::max(m_elapsedTime - m_lastSkyStateElapsedTime, 0.0f) : 0.0f;
    m_lastSkyStateElapsedTime = m_elapsedTime;
    m_skyRenderer.state().update(inputs, deltaSeconds);
    m_skyRenderer.render(viewId, pViewMatrix, pProjectionMatrix, m_frameSurroundings, true);

    // The sky pass set the shared sky-fog uniform; the indoor billboards and effects keep their flat fog (the
    // outdoor view's sky haze).
    applySceneSkyFog();
}

void IndoorRenderer::shutdown()
{
    if (Engine::BgfxContext::isBgfxInitialized())
    {
        m_skyRenderer.shutdown();
    }
    else
    {
        m_skyRenderer.abandonGpuResources();
    }
    m_skyRendererInitializeAttempted = false;
    m_openSkyWeather.shutdown(m_pWeatherAudio, Engine::BgfxContext::isBgfxInitialized());
    m_waterRenderer.shutdown();
    m_waterResourcesInitialized = false;
    m_waterGeometryDirty = true;
    if (Engine::BgfxContext::isBgfxInitialized() && bgfx::isValid(m_worldClipPlaneUniform))
    {
        bgfx::destroy(m_worldClipPlaneUniform);
    }
    m_worldClipPlaneUniform = BGFX_INVALID_HANDLE;
    m_effectRenderer.shutdown(Engine::BgfxContext::isBgfxInitialized());
    m_shieldDomeRenderer.shutdown(Engine::BgfxContext::isBgfxInitialized());
    m_modelRenderer.shutdown(Engine::BgfxContext::isBgfxInitialized());
    if (Engine::BgfxContext::isBgfxInitialized())
    {
        m_lightGrid.destroy();
    }
    m_lightGridBinding.destroy(Engine::BgfxContext::isBgfxInitialized());
    m_pIndoorMapData = nullptr;
    m_indoorPortalGraph.reset();
    m_indoorLightingRuntime.clearStaticCache();
    m_billboardLightingCache.clear();
    m_modelSectorCache.clear();
    m_renderVertices.clear();
    m_neighboringSectorIds.clear();
    m_pSceneRuntime = nullptr;
    m_pAssetFileSystem = nullptr;
    m_pItemTable = nullptr;
    m_spriteLoadCache = {};
    m_runtimeBillboardLoadWarningKeys.clear();
    m_indoorTextureSet.reset();
    m_missingSwapTextureNames.clear();
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
    m_indoorInteractiveDecorationFixedEventByEntity.clear();
    m_decorationBillboardIndicesBySector.clear();
    m_decorationModels.clear();
    m_staticSpriteObjectBillboardIndicesBySector.clear();
    m_houseTable.reset();
    m_mechanismBindings.clear();
    m_lastVisibilityDiagnosticsLogTick = 0;
    clearPortalVisibilityCaches();
    m_worldFxSystem.reset();

    if (!Engine::BgfxContext::isBgfxInitialized())
    {
        m_worldFxRenderResources.reset();
        m_programHandle = BGFX_INVALID_HANDLE;
        m_texturedProgramHandle = BGFX_INVALID_HANDLE;
        m_hudTintedProgramHandle = BGFX_INVALID_HANDLE;
        m_indoorLitProgramHandle = BGFX_INVALID_HANDLE;
        m_billboardProgramHandle = BGFX_INVALID_HANDLE;
        m_bloodSplatVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_bloodSplatTextureHandle = BGFX_INVALID_HANDLE;
        m_entityMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_portalVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_spawnMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_doorMarkerVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_textureSamplerHandle = BGFX_INVALID_HANDLE;
        m_hudTintUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorLightPositionsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorLightColorsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorLightParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorLitMaterialProgramHandle = BGFX_INVALID_HANDLE;
        m_indoorBakedProgramHandle = BGFX_INVALID_HANDLE;
        m_indoorBakedMaterialProgramHandle = BGFX_INVALID_HANDLE;
        m_lightmapSamplerHandle = BGFX_INVALID_HANDLE;
        m_lightmapTextureHandles.clear();
        m_daylightmapSamplerHandle = BGFX_INVALID_HANDLE;
        m_daylightmapTextureHandles.clear();
        m_indoorBakedDaylightUniformHandle = BGFX_INVALID_HANDLE;
        m_surfaceNormalSamplerHandle = BGFX_INVALID_HANDLE;
        m_surfaceDetailSamplerHandle = BGFX_INVALID_HANDLE;
        m_surfaceMaterialUniformHandle = BGFX_INVALID_HANDLE;
        m_surfaceReflectionBinding.destroy(false);
        m_indoorFaceGridUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorDaylightUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorFogModeUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorFogLightUniformHandle = BGFX_INVALID_HANDLE;
        m_secretPulseParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorSkyParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_indoorSkyProjectionParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardAmbientUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardOverrideColorUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardOutlineParamsUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardFogColorUniformHandle = BGFX_INVALID_HANDLE;
        m_skyFogUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardFogDensitiesUniformHandle = BGFX_INVALID_HANDLE;
        m_billboardFogDistancesUniformHandle = BGFX_INVALID_HANDLE;
        m_wireframeVertexBufferHandle = BGFX_INVALID_HANDLE;
        m_billboardTextureHandles.clear();
        m_billboardTextureIndexByKey.clear();
        m_indoorTextureHandles.clear();
        m_texturedBatches.clear();
        m_texturedDrawGroups.clear();
        m_faceDrawPlan.clear();
        m_faceDrawBounds.clear();
        m_faceDrawGrid.clear();
        m_mergedFaceIndexBufferHandle = BGFX_INVALID_HANDLE;
        m_faceBatchIndices.clear();
        m_faceSubdivisionTriangles.clear();
        m_texturedBatchGeometryRevision = std::numeric_limits<uint64_t>::max();
        m_bakedStaticLightRevision = std::numeric_limits<uint64_t>::max();
        m_bakedStaticLightEnabledStates.clear();
        m_bakedSectorAmbientLevels.clear();
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

    if (bgfx::isValid(m_hudTintedProgramHandle))
    {
        bgfx::destroy(m_hudTintedProgramHandle);
        m_hudTintedProgramHandle = BGFX_INVALID_HANDLE;
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

    if (bgfx::isValid(m_hudTintUniformHandle))
    {
        bgfx::destroy(m_hudTintUniformHandle);
        m_hudTintUniformHandle = BGFX_INVALID_HANDLE;
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

    if (bgfx::isValid(m_indoorLitMaterialProgramHandle))
    {
        bgfx::destroy(m_indoorLitMaterialProgramHandle);
        m_indoorLitMaterialProgramHandle = BGFX_INVALID_HANDLE;
    }

    destroyBakedLightingResources();
    destroyTerrainResources();

    for (bgfx::ProgramHandle &handle : m_indoorFogProgramHandles)
    {
        if (bgfx::isValid(handle))
        {
            bgfx::destroy(handle);
            handle = BGFX_INVALID_HANDLE;
        }
    }

    for (bgfx::ProgramHandle *pHandle : {&m_indoorTranslucentProgramHandle, &m_indoorBakedTranslucentProgramHandle,
        &m_waterTintProgramHandle})
    {
        if (bgfx::isValid(*pHandle))
        {
            bgfx::destroy(*pHandle);
            *pHandle = BGFX_INVALID_HANDLE;
        }
    }

    for (bgfx::UniformHandle *pHandle : {&m_surfaceNormalSamplerHandle, &m_surfaceDetailSamplerHandle,
        &m_surfaceMaterialUniformHandle, &m_indoorTranslucencyUniformHandle})
    {
        if (bgfx::isValid(*pHandle))
        {
            bgfx::destroy(*pHandle);
            *pHandle = BGFX_INVALID_HANDLE;
        }
    }
    m_surfaceReflectionBinding.destroy();

    if (bgfx::isValid(m_indoorFaceGridUniformHandle))
    {
        bgfx::destroy(m_indoorFaceGridUniformHandle);
        m_indoorFaceGridUniformHandle = BGFX_INVALID_HANDLE;
    }

    for (bgfx::UniformHandle *pHandle : {&m_indoorDaylightUniformHandle, &m_indoorFogModeUniformHandle,
        &m_indoorFogLightUniformHandle})
    {
        if (bgfx::isValid(*pHandle))
        {
            bgfx::destroy(*pHandle);
            *pHandle = BGFX_INVALID_HANDLE;
        }
    }

    if (bgfx::isValid(m_secretPulseParamsUniformHandle))
    {
        bgfx::destroy(m_secretPulseParamsUniformHandle);
        m_secretPulseParamsUniformHandle = BGFX_INVALID_HANDLE;
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

    if (bgfx::isValid(m_skyFogUniformHandle))
    {
        bgfx::destroy(m_skyFogUniformHandle);
        m_skyFogUniformHandle = BGFX_INVALID_HANDLE;
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
        if (!textureHandle.atlas && !textureHandle.retained && bgfx::isValid(textureHandle.textureHandle))
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
    const size_t sectorCount = m_pIndoorMapData ? m_pIndoorMapData->sectors.size() : 0;
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

void IndoorRenderer::TerrainVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

void IndoorRenderer::LightmapUvVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::TexCoord4, 2, bgfx::AttribType::Float)
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
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .add(bgfx::Attrib::Tangent, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Bitangent, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord6, 3, bgfx::AttribType::Float)
        .end();
}

void IndoorRenderer::LitBillboardVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .add(bgfx::Attrib::TexCoord2, 1, bgfx::AttribType::Float)
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

void IndoorRenderer::setWorldTimeHeld(bool held)
{
    m_worldTimeHeld = held;
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

const IndoorRenderer::BillboardTextureHandle *IndoorRenderer::restoreBillboardTexture(
    const std::string &name, int16_t palette, const std::string &resourceIdentity)
{
    const SpriteBillboardTexture *pCached = m_nativeSpriteCache.find(name, palette, resourceIdentity);
    if (pCached == nullptr)
    {
        return nullptr;
    }
    m_billboardTextureHandles.push_back(*pCached);
    registerBillboardTextureIndex(m_billboardTextureHandles.size() - 1);
    return &m_billboardTextureHandles.back();
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

    if (const SpriteBillboardTexture *pCached = restoreBillboardTexture(textureName, paletteId))
    {
        return pCached;
    }

    if (textureName.starts_with("atlas:"))
    {
        BillboardTextureHandle texture;
        if (m_pAssetFileSystem != nullptr)
        {
            m_spriteAtlasCache.preloadPackage(*m_pAssetFileSystem, textureName);
        }
        if (m_pAssetFileSystem == nullptr || !m_spriteAtlasCache.load(*m_pAssetFileSystem, textureName, paletteId, texture))
        {
            return nullptr;
        }
        m_billboardTextureHandles.push_back(std::move(texture));
        registerBillboardTextureIndex(m_billboardTextureHandles.size() - 1);
        return &m_billboardTextureHandles.back();
    }

    const BillboardTextureLookupKey warningKey = makeBillboardTextureLookupKey(textureName, paletteId);
    const bool logCacheMiss = m_runtimeBillboardLoadWarningKeys.insert(warningKey).second;
    const uint64_t loadBeginTickNanoseconds = logCacheMiss ? SDL_GetTicksNS() : 0;
    const auto logLoadResult = [&](const char *pResult, int width, int height)
    {
        if (!logCacheMiss)
        {
            return;
        }

        std::cerr << "[AssetLoadWarning] kind=sprite phase=render scene=indoor"
                  << " map=\"" << (m_map ? m_map->fileName : std::string()) << "\""
                  << " texture=\"" << warningKey.textureName << "\""
                  << " palette=" << paletteId
                  << " result=" << pResult
                  << " load_us=" << (SDL_GetTicksNS() - loadBeginTickNanoseconds) / 1000
                  << " size=" << width << 'x' << height
                  << '\n';
    };

    int textureWidth = 0;
    int textureHeight = 0;
    const std::optional<std::vector<uint8_t>> pixels = GameplayHudCommon::loadSpriteBitmapPixelsBgraCached(
        m_pAssetFileSystem,
        m_spriteLoadCache,
        textureName,
        paletteId,
        textureWidth,
        textureHeight,
        m_map.has_value() ? m_map->worldId : std::string());

    if (!pixels || textureWidth <= 0 || textureHeight <= 0)
    {
        logLoadResult("failed", textureWidth, textureHeight);
        return nullptr;
    }

    BillboardTextureHandle billboardTexture = {};
    billboardTexture.textureName = toLowerCopy(textureName);
    billboardTexture.paletteId = paletteId;
    billboardTexture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, m_assetScaleTier);
    billboardTexture.height = Engine::scalePhysicalPixelsToLogical(textureHeight, m_assetScaleTier);
    billboardTexture.physicalWidth = textureWidth;
    billboardTexture.physicalHeight = textureHeight;
    billboardTexture.opacityMask.assignFromBgra(*pixels, textureWidth, textureHeight);
    billboardTexture.textureHandle = createBgraTexture2D(
        uint16_t(textureWidth),
        uint16_t(textureHeight),
        pixels->data(),
        uint32_t(pixels->size()),
        TextureFilterProfile::Billboard,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    if (!bgfx::isValid(billboardTexture.textureHandle))
    {
        logLoadResult("failed", textureWidth, textureHeight);
        return nullptr;
    }

    m_nativeSpriteCache.retain(billboardTexture);
    m_billboardTextureHandles.push_back(std::move(billboardTexture));
    registerBillboardTextureIndex(m_billboardTextureHandles.size() - 1);
    logLoadResult("loaded", textureWidth, textureHeight);
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
    const std::array<float, 4> noFaceGrid = {0.0f, -1.0f, -1.0f, 0.0f};
    bgfx::setUniform(m_indoorFaceGridUniformHandle, noFaceGrid.data());
    setFaceDaylight(false);
    m_lightGridBinding.bind(nullptr, Engine::LightGridModeFull);
    const std::array<float, 4> secretPulseParams = {0.0f, m_elapsedTime, 0.0f, 0.0f};
    bgfx::setUniform(m_secretPulseParamsUniformHandle, secretPulseParams.data());
    const std::array<float, 4> indoorSkyParams = {0.0f, 0.0f, m_cameraYawRadians, m_cameraPitchRadians};
    bgfx::setUniform(m_indoorSkyParamsUniformHandle, indoorSkyParams.data());
    const std::array<float, 4> indoorSkyProjectionParams = {0.0f, 0.0f, 1.0f, IndoorSkyProjectionPitchOffsetRadians};
    bgfx::setUniform(m_indoorSkyProjectionParamsUniformHandle, indoorSkyProjectionParams.data());
    bgfx::setState(
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_DEPTH_TEST_LEQUAL
        | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    if (m_fog.enabled)
    {
        setFaceFog();
        bgfx::submit(viewId, m_indoorFogProgramHandles[0]);
        return;
    }
    bgfx::submit(viewId, m_indoorLitProgramHandle);
}

uint16_t IndoorRenderer::resolveDecorationBillboardSpriteId(const DecorationBillboard &billboard, bool &hidden) const
{
    hidden = false;

    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

    if (!m_indoorDecorationBillboardSet || !eventRuntimeState.has_value())
    {
        return billboard.spriteId;
    }

    const std::optional<IndoorInteractiveDecorationBinding> binding =
        resolveIndoorInteractiveDecorationBinding(
            m_indoorInteractiveDecorationDecorVarIndicesByEntity,
            m_indoorInteractiveDecorationBaseEventIdsByEntity,
            m_indoorInteractiveDecorationEventCountsByEntity,
            m_indoorInteractiveDecorationHideWhenClearedByEntity,
            m_indoorInteractiveDecorationFixedEventByEntity,
            billboard.entityIndex);

    if (binding
        && interactiveDecorationIsCleared(
            eventRuntimeState->decorVars[binding->decorVarIndex],
            binding->eventCount,
            binding->hideWhenCleared))
    {
        hidden = true;
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
}

void IndoorRenderer::updateDecorationModels(const std::vector<uint8_t> &visibleSectorMask,
    const IndoorLightingFrame &lightingFrame, const GameplayContextActionState *pContextActionState,
    LightingStats *pLightingStats)
{
    if (m_decorationModels.empty() || !m_indoorDecorationBillboardSet)
    {
        return;
    }
    const std::vector<DecorationBillboard> &billboards = m_indoorDecorationBillboardSet->billboards;
    // The sprite each decoration shows now selects its model; sectors the portal walk did not reach hide theirs.
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();
    m_decorationModels.update(billboards, [&](size_t index, bool &hidden, int &state)
    {
        const DecorationBillboard &billboard = billboards[index];
        const uint16_t sprite = resolveDecorationBillboardSpriteId(billboard, hidden);
        hidden = hidden || !isRenderSectorVisible(billboard.sectorId, visibleSectorMask);
        const std::optional<IndoorInteractiveDecorationBinding> binding = eventRuntimeState
            ? resolveIndoorInteractiveDecorationBinding(
                m_indoorInteractiveDecorationDecorVarIndicesByEntity,
                m_indoorInteractiveDecorationBaseEventIdsByEntity,
                m_indoorInteractiveDecorationEventCountsByEntity,
                m_indoorInteractiveDecorationHideWhenClearedByEntity,
                m_indoorInteractiveDecorationFixedEventByEntity,
                billboard.entityIndex)
            : std::nullopt;
        state = binding ? eventRuntimeState->decorVars[binding->decorVarIndex] : -1;
        return sprite;
    });
    m_decorationModels.animate(float(SDL_GetTicks()) * 0.001f);
    if (eventRuntimeState && !eventRuntimeState->decorationAims.empty())
    {
        m_decorationModels.poseAimed(billboards, [&eventRuntimeState](uint32_t key, float &yawRadians, float &back,
            std::array<float, 3> &offset)
        {
            const auto aim = eventRuntimeState->decorationAims.find(key);
            if (aim == eventRuntimeState->decorationAims.end())
            {
                return false;
            }
            yawRadians = aim->second.currentRadians;
            back = aim->second.back();
            offset = aim->second.offset;
            return true;
        });
    }
    // Animated decorations: their parts, whole moving models and skinned copies (evt.PlayDecorationClip, idle clips).
    const EventRuntimeState *pClipEvents = eventRuntimeState ? &*eventRuntimeState : nullptr;
    const DecorationModelSet::PartClip decorationClip =
        [pClipEvents](uint32_t key, std::string &clipName, float &seconds, bool &loop)
    {
        return decorationClipFor(pClipEvents, key, clipName, seconds, loop);
    };
    const float decorationSeconds = float(SDL_GetTicks()) * 0.001f;
    if (pClipEvents != nullptr && !pClipEvents->decorationUses.empty())
    {
        m_decorationModels.noteUses(billboards, [pClipEvents](uint32_t key)
        {
            const auto found = pClipEvents->decorationUses.find(key);
            return found != pClipEvents->decorationUses.end() ? found->second : 0u;
        }, decorationSeconds);
    }
    m_decorationModels.poseParts(billboards, decorationClip, decorationSeconds);
    m_decorationModels.poseInstances(billboards, decorationClip, decorationSeconds, m_worldFxSystem.models());
    const GameplayWorldHit *pContextActionHit = selectedContextActionWorldHit(pContextActionState);
    std::vector<Engine::ModelStaticGroup> &groups = m_decorationModels.groups();
    for (size_t group = 0; group < groups.size(); ++group)
    {
        Engine::ModelStaticGroup &placements = groups[group];
        const std::vector<size_t> &billboardIndices = m_decorationModels.billboardIndices(group);
        for (size_t index = 0; index < placements.placements.size(); ++index)
        {
            Engine::ModelStaticPlacement &placement = placements.placements[index];
            if (!placement.visible)
            {
                continue;
            }
            const DecorationBillboard &billboard = billboards[billboardIndices[index]];
            placement.outlineColorAbgr = contextActionHighlightsIndoorEntity(pContextActionHit, billboard.entityIndex)
                && !m_decorationModels.overlayGroup(group) ? contextActionHighlightOutlineColor() : 0;
            // The light the sprite would receive, as the placement's ambient: a model is as bright as the sprite it
            // replaces (a self-lit flame sprite, such as a torch, at exactly one).
            const Engine::ModelBounds &bounds = placements.bounds[index];
            const bx::Vec3 center = {(bounds.min[0] + bounds.max[0]) * 0.5f, (bounds.min[1] + bounds.max[1]) * 0.5f,
                (bounds.min[2] + bounds.max[2]) * 0.5f};
            bool hidden = false;
            const SpriteFrameEntry *pFrame = m_indoorDecorationBillboardSet->spriteFrameTable.getFrame(
                resolveDecorationBillboardSpriteId(billboard, hidden), 0);
            std::array<float, 4> light = {1.0f, 1.0f, 1.0f, 0.0f};
            if (pFrame != nullptr && m_modelLighting.enabled)
            {
                // MM9's model base (ambient and ModelAdd); the shader adds the lights per pixel with N.L.
                if (!SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::Lit))
                {
                    const std::array<float, 3> base = indoorModelLight(m_modelLighting, {0.0f, 0.0f, 0.0f});
                    light = {base[0], base[1], base[2], 0.0f};
                }
            }
            else if (pFrame != nullptr)
            {
                light = billboardLightingUniform(lightingFrame, *pFrame, center, billboard.sectorId,
                    billboardLightingCacheKey(1, billboard.entityIndex), pLightingStats);
                if (indoorDaylightSector(m_daylight, billboard.sectorId)
                    && !SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::Lit))
                {
                    // In the open air the model takes the sun by direction (renderDecorationModels' batch sun), so
                    // its own light keeps only the ambient share of the room light (and the nearby lights). It is
                    // lit as the faces around it are, without the decorations' exposure (which matches a model to
                    // the sprite it replaces in a dark room; in daylight it pushed sunlit greens to lime): the batch
                    // ambient's IndoorDecorationExposure is divided out here, its sun takes none.
                    const float ambient = indoorDaylightModelAmbient(m_frameDaylight);
                    const float sunShare = indoorDaylightRoomLight(m_frameDaylight) - ambient;
                    for (size_t channel = 0; channel < 3; ++channel)
                    {
                        light[channel] = std::max(light[channel] - sunShare, ambient) / IndoorDecorationExposure;
                    }
                    light[3] = 1.0f;
                }
            }
            placement.light = {light[0], light[1], light[2], light[3]};
            placement.sector = billboard.sectorId;
            placement.pointLight = {};
        }
    }
}

void IndoorRenderer::renderDecorationBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask,
    const std::vector<std::vector<IndoorVisibilityFrustum>> &visibleSectorFrustums,
    const IndoorLightingFrame &lightingFrame,
    const GameplayContextActionState *pContextActionState,
    LightingStats *pLightingStats,
    const WaterRenderer::Reflection *pReflection
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
    std::optional<ViewFrustum> reflectionFrustum;
    if (pReflection != nullptr)
    {
        reflectionFrustum.emplace(pReflection->view.data(), pReflection->projection.data(),
            bgfx::getCaps()->homogeneousDepth);
    }
    const std::array<float, 4> clip = pReflection != nullptr
        ? std::array<float, 4>{0.0f, 0.0f, 1.0f, -pReflection->height} : std::array<float, 4>{};
    bgfx::setUniform(m_worldClipPlaneUniform, clip.data());
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
        uint64_t lightingCacheKey = 0;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(m_indoorDecorationBillboardSet->billboards.size());
    const GameplayWorldHit *pContextActionHit = selectedContextActionWorldHit(pContextActionState);
    const auto appendDecorationBillboardDrawItem =
        [&](const DecorationBillboard &billboard)
    {
        if (!isRenderSectorVisible(billboard.sectorId, visibleSectorMask))
        {
            return;
        }

        const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
        const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
        const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;
        if (pReflection != nullptr
            && waterBillboardFade(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ) == 0.0f)
        {
            return;
        }

        bool hidden = false;
        const uint16_t spriteId = resolveDecorationBillboardSpriteId(billboard, hidden);

        // A 3D model draws this decoration (updateDecorationModels).
        if (hidden || spriteId == 0 || m_decorationModels.modelsSprite(spriteId))
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
        const BillboardTextureHandle *pTexture =
            findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

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

        const bool visible = pReflection != nullptr
            ? waterBillboardVisible(billboardQuad(center, cameraRight, cameraUp, worldWidth, worldHeight),
                *reflectionFrustum, pReflection->height)
            : billboardSphereInFrustum(center, radius, frustumPlanes);
        if (!visible)
        {
            return;
        }

        if (!sphereIntersectsVisibleSectorFrustums(billboard.sectorId, center, radius, visibleSectorFrustums))
        {
            return;
        }

        BillboardDrawItem drawItem = {};
        drawItem.pBillboard = &billboard;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.hovered = contextActionHighlightsIndoorEntity(pContextActionHit, billboard.entityIndex);
        drawItem.hoveredOutlineColorAbgr = drawItem.hovered ? contextActionHighlightOutlineColor() : 0;
        drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        drawItem.lightingCacheKey = billboardLightingCacheKey(1, billboard.entityIndex);
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

    if (pReflection != nullptr)
    {
        limitWaterBillboards(drawItems, MaxWaterBillboards / 2);
    }
    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            return left.distanceSquared > right.distanceSquared;
        }
    );

    if (pReflection == nullptr && m_logIndoorPerformanceDiagnostics)
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
        const uint32_t vertexColorAbgr = pReflection != nullptr
            ? waterBillboardColor(makeAbgr(0, 0, 0), drawItem.distanceSquared) : makeAbgr(0, 0, 0);
        const std::array<float, 4> ambient =
            billboardLightingUniform(
                lightingFrame,
                frame,
                center,
                billboard.sectorId,
                drawItem.lightingCacheKey,
                pLightingStats);
        const float clearOverrideColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float clearOutlineParams[4] = {0.0f, 0.0f, 0.0f, 0.0f};

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
                setBillboardFog();
                bgfx::setState(
                    IndoorBillboardDrawState);
                bgfx::submit(viewId, m_billboardProgramHandle);

                if (pReflection == nullptr && m_logIndoorPerformanceDiagnostics)
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
        setBillboardFog();
        bgfx::setState(
            IndoorBillboardDrawState
        );
        bgfx::submit(viewId, m_billboardProgramHandle);

        if (pReflection == nullptr && m_logIndoorPerformanceDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.renderDecorationSpriteSubmits;
        }
    }
}

void IndoorRenderer::renderActorPreviewBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const float *pProjectionMatrix,
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask,
    const IndoorLightingFrame &lightingFrame,
    bool spriteOutlineEnabled,
    const GameplayContextActionState *pContextActionState,
    const GameSession *pGameSession,
    const GameSettings *pSettings,
    LightingStats *pLightingStats,
    const WaterRenderer::Reflection *pReflection
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
    std::optional<ViewFrustum> reflectionFrustum;
    if (pReflection != nullptr)
    {
        reflectionFrustum.emplace(pReflection->view.data(), pReflection->projection.data(),
            bgfx::getCaps()->homogeneousDepth);
    }
    const std::array<float, 4> clip = pReflection != nullptr
        ? std::array<float, 4>{0.0f, 0.0f, 1.0f, -pReflection->height} : std::array<float, 4>{};
    bgfx::setUniform(m_worldClipPlaneUniform, clip.data());
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
        float distanceSquared = 0.0f;
        float hitFlash = 0.0f;
        bool hasHealthBar = false;
        bool healthBarFocused = false;
        bool healthBarAttacking = false;
        uint16_t healthBarStandingFrame = 0;
        float questMarkerZ = 0.0f;
        uint64_t lightingCacheKey = 0;
        // A model presents the actor: no sprite, health bar at questMarkerZ.
        bool modelActor = false;
    };

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::optional<size_t> hoveredActorIndex =
        m_cachedInspectHitValid && m_cachedInspectHit.kind == "actor"
        ? std::optional<size_t>(m_cachedInspectHit.index)
        : std::nullopt;
    const GameplayWorldHit *pContextActionHit = selectedContextActionWorldHit(pContextActionState);
    const bool renderCombatActorHealthBars = pReflection == nullptr && pGameSession != nullptr
        && pSettings != nullptr && pSettings->enemyHealthBarMode != "off"
        && pGameSession->gameplayScreenRuntime().currentHudScreenState() == GameplayHudScreenState::Gameplay;
    CombatActorHealthBarRuntime *pHealthBars = renderCombatActorHealthBars
        ? &pGameSession->gameplayScreenRuntime().enemyHealthBars() : nullptr;
    const std::optional<size_t> pointedActor = pContextActionHit != nullptr
        && pContextActionHit->kind == GameplayWorldHitKind::Actor
        && pContextActionHit->actor.has_value()
        ? std::optional<size_t>(pContextActionHit->actor->actorIndex) : hoveredActorIndex;
    const std::optional<size_t> focusedActor = pHealthBars != nullptr ? pHealthBars->focus(pointedActor) : std::nullopt;
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
    CombatActorHealthBarSelection healthBarSelection = {};
    const bool useRuntimeBillboards = mapDeltaData.has_value() && m_pSceneRuntime != nullptr;
    // Offers a hostile actor in view a health bar.
    const auto considerActorHealthBar =
        [&](BillboardDrawItem &drawItem, const IndoorWorldRuntime::MapActorAiState *pActorAiState)
        {
            const size_t actorIndex = drawItem.actorIndex;
            if (!renderCombatActorHealthBars
                || pActorAiState == nullptr
                || !pActorAiState->hostileToParty
                || !mapDeltaData
                || actorIndex >= mapDeltaData->actors.size()
                || mapDeltaData->actors[actorIndex].hp <= 0)
            {
                return;
            }
            const bool attacking = pActorAiState->hasDetectedParty
                && (pActorAiState->motionState == ActorAiMotionState::Pursuing
                    || pActorAiState->motionState == ActorAiMotionState::Attacking);
            if (drawItem.distanceSquared <= MaximumCombatActorHealthBarDistanceSquared)
            {
                pHealthBars->observeActivity(actorIndex, attacking);
            }
            considerCombatActorHealthBarCandidate(healthBarSelection,
                {drawItems.size(), drawItem.distanceSquared, actorIndex, focusedActor == actorIndex,
                    attacking || pHealthBars->inCombat(actorIndex)}, pSettings->enemyHealthBarMode);
            drawItem.healthBarAttacking = attacking;
        };
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

            const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
            const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
            const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;
            if (pReflection != nullptr
                && waterBillboardFade(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ) == 0.0f)
            {
                continue;
            }

            const IndoorWorldRuntime::MapActorAiState *pActorAiState =
                m_pSceneRuntime != nullptr
                    ? m_pSceneRuntime->worldRuntime().mapActorAiState(billboard.actorIndex)
                    : nullptr;
            const bool contextHighlighted = contextActionHighlightsActor(pContextActionHit, billboard.actorIndex);
            const bool hovered =
                contextHighlighted
                || (spriteOutlineEnabled && hoveredActorIndex && *hoveredActorIndex == billboard.actorIndex);
            const uint32_t hoveredOutlineColorAbgr =
                hovered && mapDeltaData && billboard.actorIndex < mapDeltaData->actors.size()
                    ? (contextHighlighted
                        ? contextActionHighlightOutlineColor()
                        : resolveHoveredIndoorActorOutlineColor(
                            mapDeltaData->actors[billboard.actorIndex],
                            pActorAiState))
                    : 0;

            // A model presents this actor (or will, from the next model sync) and no sprite is resolved: the draw item
            // carries the hover outline to the model and anchors the health bar and quest marker at its standing top.
            if (m_worldFxSystem.hasActorModel(billboard.actorIndex)
                || (pActorAiState != nullptr && m_indoorActorPreviewBillboardSet->drawsModel(pActorAiState->monsterId)))
            {
                if (pReflection != nullptr)
                {
                    continue;
                }

                const float standingTop = m_worldFxSystem.actorModelStandingTop(billboard.actorIndex)
                    .value_or(static_cast<float>(billboard.height));
                const bx::Vec3 center = {
                    static_cast<float>(billboard.x),
                    static_cast<float>(billboard.y),
                    static_cast<float>(billboard.z) + standingTop * 0.5f};
                const float halfHeight = standingTop * 0.5f;
                const float radius = std::hypot(static_cast<float>(billboard.radius), halfHeight);

                if (!billboardSphereInFrustum(center, radius, frustumPlanes))
                {
                    continue;
                }

                BillboardDrawItem drawItem = {};
                drawItem.modelActor = true;
                drawItem.actorIndex = billboard.actorIndex;
                drawItem.x = billboard.x;
                drawItem.y = billboard.y;
                drawItem.z = billboard.z - int(std::lround(m_worldFxSystem.actorCorpseSinkDepth(billboard.actorIndex)));
                drawItem.sectorId = billboard.sectorId;
                drawItem.hovered = hovered;
                drawItem.hoveredOutlineColorAbgr = hoveredOutlineColorAbgr;
                drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
                drawItem.questMarkerZ = static_cast<float>(drawItem.z) + standingTop;
                considerActorHealthBar(drawItem, pActorAiState);
                drawItems.push_back(drawItem);
                continue;
            }

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
            const bx::Vec3 center = spriteBillboardCenter(
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z),
                cameraRight, cameraUp, *pTexture, spriteScale, resolvedTexture.mirrored);
            const float radius = std::sqrt((worldWidth * 0.5f) * (worldWidth * 0.5f)
                + (worldHeight * 0.5f) * (worldHeight * 0.5f));

            const bool visible = pReflection != nullptr
                ? waterBillboardVisible(billboardQuad(center, cameraRight, cameraUp, worldWidth, worldHeight),
                    *reflectionFrustum, pReflection->height)
                : billboardSphereInFrustum(center, radius, frustumPlanes);
            if (!visible)
            {
                continue;
            }

            BillboardDrawItem drawItem = {};
            drawItem.actorIndex = billboard.actorIndex;
            drawItem.x = billboard.x;
            drawItem.y = billboard.y;
            // A slain creature's sprite sinks into the floor before its loot satchel appears.
            drawItem.z = billboard.z - int(std::lround(m_worldFxSystem.actorCorpseSinkDepth(billboard.actorIndex)));
            drawItem.sectorId = billboard.sectorId;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.hovered = hovered;
            drawItem.hoveredOutlineColorAbgr = hoveredOutlineColorAbgr;
            drawItem.heightScale = billboard.heightScale;
            drawItem.lightingCacheKey = billboardLightingCacheKey(2, billboard.actorIndex);
            drawItem.hitFlash = m_pSceneRuntime != nullptr
                ? m_pSceneRuntime->worldRuntime().actorHitFeedback().flashAmount(billboard.actorIndex) : 0.0f;
            drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            considerActorHealthBar(drawItem, pActorAiState);

            drawItem.healthBarStandingFrame = billboard.actionSpriteFrameIndices[0] != 0
                ? billboard.actionSpriteFrameIndices[0] : billboard.spriteFrameIndex;
            drawItem.questMarkerZ = drawItem.z + pTexture->offsetY * spriteScale
                + worldHeight * (1.0f - pTexture->opacityMask.opaqueTopNormalized());
            drawItems.push_back(drawItem);
        }
    }
    else
    {
        for (const ActorPreviewBillboard &billboard : m_indoorActorPreviewBillboardSet->billboards)
        {
            const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
            const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
            const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;
            if (pReflection != nullptr
                && waterBillboardFade(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ) == 0.0f)
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
                ensureSpriteBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                continue;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const bx::Vec3 center = spriteBillboardCenter(
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z),
                cameraRight, cameraUp, *pTexture, spriteScale, resolvedTexture.mirrored);
            const float radius = std::sqrt((worldWidth * 0.5f) * (worldWidth * 0.5f)
                + (worldHeight * 0.5f) * (worldHeight * 0.5f));

            const bool visible = pReflection != nullptr
                ? waterBillboardVisible(billboardQuad(center, cameraRight, cameraUp, worldWidth, worldHeight),
                    *reflectionFrustum, pReflection->height)
                : billboardSphereInFrustum(center, radius, frustumPlanes);
            if (!visible)
            {
                continue;
            }

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

    for (size_t index = 0; index < healthBarSelection.count; ++index)
    {
        const CombatActorHealthBarCandidate &candidate = healthBarSelection.candidates[index];
        drawItems[candidate.drawItemIndex].hasHealthBar = true;
        drawItems[candidate.drawItemIndex].healthBarFocused = candidate.focused;
    }

    if (pReflection != nullptr)
    {
        limitWaterBillboards(drawItems, MaxWaterBillboards / 2);
    }
    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            return left.distanceSquared > right.distanceSquared;
        }
    );

    if (pReflection == nullptr && m_logIndoorPerformanceDiagnostics)
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
        if (drawItem.modelActor)
        {
            if (pReflection == nullptr)
            {
                m_worldFxSystem.setActorModelOutline(drawItem.actorIndex, drawItem.hoveredOutlineColorAbgr);
            }
            continue;
        }
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale * drawItem.heightScale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = spriteBillboardCenter(
            static_cast<float>(drawItem.x),
            static_cast<float>(drawItem.y),
            static_cast<float>(drawItem.z),
            cameraRight, cameraUp, texture, spriteScale, drawItem.mirrored);
        const bx::Vec3 viewCenter = transformIndoorPoint(center, pViewMatrix);
        const bx::Vec3 right = {halfWidth, 0.0f, 0.0f};
        const bx::Vec3 up = {0.0f, worldHeight * 0.5f, 0.0f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
        const uint32_t vertexColorAbgr = pReflection != nullptr
            ? waterBillboardColor(makeAbgr(0, 0, 0), drawItem.distanceSquared) : makeAbgr(0, 0, 0);
        const std::array<float, 4> ambient =
            billboardLightingUniform(
                lightingFrame,
                frame,
                center,
                drawItem.sectorId,
                drawItem.lightingCacheKey,
                pLightingStats);
        const float clearOverrideColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float clearOutlineParams[4] = {0.0f, 0.0f, 0.0f, 0.0f};

        if (drawItem.hovered)
        {
            const float outlinePadding = spriteOutlineWorldPadding(texture, spriteScale, viewCenter.z,
                pProjectionMatrix[5], m_lastRenderHeight);
            const float paddingU = outlinePadding / worldWidth;
            const float paddingV = outlinePadding / worldHeight;
            const float outlinedHalfWidth = worldWidth * 0.5f + outlinePadding;
            const float outlinedHalfHeight = worldHeight * 0.5f + outlinePadding;
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
                setBillboardFog();
                // Test world depth without letting soft outline pixels block the coplanar body draw.
                bgfx::setState(texture.atlas
                    ? IndoorBillboardDrawState & ~BGFX_STATE_WRITE_Z : IndoorBillboardDrawState);
                bgfx::submit(viewId, m_spriteAtlasCache.bindOutline(texture, m_billboardProgramHandle));

                if (pReflection == nullptr && m_logIndoorPerformanceDiagnostics)
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
            vertexColorAbgr,
            drawItem.hitFlash
        };
        vertices[1] = {
            viewCenter.x - right.x + up.x,
            viewCenter.y - right.y + up.y,
            viewCenter.z - right.z + up.z,
            u0,
            0.0f,
            vertexColorAbgr,
            drawItem.hitFlash
        };
        vertices[2] = {
            viewCenter.x + right.x + up.x,
            viewCenter.y + right.y + up.y,
            viewCenter.z + right.z + up.z,
            u1,
            0.0f,
            vertexColorAbgr,
            drawItem.hitFlash
        };
        vertices[3] = vertices[0];
        vertices[4] = vertices[2];
        vertices[5] = {
            viewCenter.x + right.x - up.x,
            viewCenter.y + right.y - up.y,
            viewCenter.z + right.z - up.z,
            u1,
            1.0f,
            vertexColorAbgr,
            drawItem.hitFlash
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
        setBillboardFog();
        bgfx::setState(
            IndoorBillboardDrawState
        );
        bgfx::submit(viewId, m_spriteAtlasCache.bind(texture, m_billboardProgramHandle));

        if (pReflection == nullptr && m_logIndoorPerformanceDiagnostics)
        {
            ++m_indoorPerformanceDiagnostics.renderActorSpriteSubmits;
        }
    }

    if (pReflection != nullptr)
    {
        return;
    }
    for (const BillboardDrawItem &item : drawItems)
    {
        if (item.hasHealthBar && pGameSession != nullptr && item.modelActor)
        {
            m_pendingEnemyHealthBars.push_back({item.actorIndex, {float(item.x), float(item.y), float(item.z)},
                {float(item.x), float(item.y), item.questMarkerZ + 26.0f}, item.distanceSquared,
                item.healthBarFocused, item.healthBarAttacking});
        }
        else if (item.hasHealthBar && pGameSession != nullptr)
        {
            const SpriteFrameEntry *pStandingFrame =
                m_indoorActorPreviewBillboardSet->spriteFrameTable.getFrame(item.healthBarStandingFrame, 0);
            if (pStandingFrame == nullptr)
            {
                continue;
            }
            const ResolvedSpriteTexture standing = SpriteFrameTable::resolveTexture(*pStandingFrame, 0);
            const BillboardTextureHandle *pStandingTexture =
                ensureSpriteBillboardTexture(standing.textureName, pStandingFrame->paletteId);
            if (pStandingTexture == nullptr)
            {
                continue;
            }
            const float standingTop = pStandingTexture->offsetY + pStandingTexture->height
                * (1.0f - pStandingTexture->opacityMask.opaqueTopNormalized());
            const float anchorZ = item.z + (standingTop * pStandingFrame->scale + 26.0f) * item.heightScale;
            m_pendingEnemyHealthBars.push_back({item.actorIndex, {float(item.x), float(item.y), float(item.z)},
                {float(item.x), float(item.y), anchorZ}, item.distanceSquared,
                item.healthBarFocused, item.healthBarAttacking});
        }
    }

    struct QuestMarkerBatch
    {
        Mm9QuestMarkerState state = Mm9QuestMarkerState::None;
        const BillboardTextureHandle *pTexture = nullptr;
        std::vector<LitBillboardVertex> vertices;
    };

    std::array<QuestMarkerBatch, 4> questMarkerBatches = {{
        {Mm9QuestMarkerState::Available},
        {Mm9QuestMarkerState::InProgress},
        {Mm9QuestMarkerState::Ready},
        {Mm9QuestMarkerState::Trainer},
    }};

    const bool hasVisibleQuestMarker =
        pGameSession != nullptr
        && pSettings != nullptr
        && pSettings->questMarkers
        && std::any_of(
            drawItems.begin(),
            drawItems.end(),
            [pGameSession](const BillboardDrawItem &drawItem)
            {
                return questMarkerAlpha(std::sqrt(drawItem.distanceSquared)) > 0
                    && !questMarkerTextureName(pGameSession->questMarkerForActor(drawItem.actorIndex)).empty();
            });

    if (hasVisibleQuestMarker)
    {
        ensureSpriteBillboardTexture("quest_marker_exclamation", 0);
        ensureSpriteBillboardTexture("quest_marker_question", 0);
        ensureSpriteBillboardTexture("trainer_marker_book", 0);

        for (QuestMarkerBatch &batch : questMarkerBatches)
        {
            batch.pTexture = findBillboardTexture(std::string(questMarkerTextureName(batch.state)), 0);
        }

        for (const BillboardDrawItem &drawItem : drawItems)
        {
            const Mm9QuestMarkerState markerState = pGameSession->questMarkerForActor(drawItem.actorIndex);
            const float distance = std::sqrt(drawItem.distanceSquared);
            const uint8_t alpha = questMarkerAlpha(distance);
            const auto batchIterator = std::find_if(
                questMarkerBatches.begin(),
                questMarkerBatches.end(),
                [markerState](const QuestMarkerBatch &batch)
                {
                    return batch.state == markerState;
                });

            if (alpha == 0
                || batchIterator == questMarkerBatches.end()
                || batchIterator->pTexture == nullptr
                || !bgfx::isValid(batchIterator->pTexture->textureHandle))
            {
                continue;
            }

            const float scale = questMarkerWorldScale(distance);
            const float halfExtent = questMarkerHalfExtent(scale);
            const bx::Vec3 origin = {
                static_cast<float>(drawItem.x),
                static_cast<float>(drawItem.y),
                drawItem.questMarkerZ + questMarkerOriginOffset(scale),
            };
            const bx::Vec3 center = transformIndoorPoint(origin, pViewMatrix);
            const bx::Vec3 right = {halfExtent, 0.0f, 0.0f};
            const bx::Vec3 up = {0.0f, halfExtent, 0.0f};
            std::vector<LitBillboardVertex> &vertices = batchIterator->vertices;
            const uint32_t vertexColorAbgr = makeAbgrAlpha(0, 0, 0, alpha);
            vertices.push_back(
                {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, 0.0f, 1.0f,
                 vertexColorAbgr});
            vertices.push_back(
                {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, 0.0f, 0.0f,
                 vertexColorAbgr});
            vertices.push_back(
                {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, 1.0f, 0.0f,
                 vertexColorAbgr});
            vertices.push_back(vertices[vertices.size() - 3]);
            vertices.push_back(vertices[vertices.size() - 2]);
            vertices.push_back(
                {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, 1.0f, 1.0f,
                 vertexColorAbgr});
        }
    }

    for (const QuestMarkerBatch &batch : questMarkerBatches)
    {
        if (batch.pTexture == nullptr
            || batch.vertices.empty()
            || bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(batch.vertices.size()),
                LitBillboardVertex::ms_layout) < batch.vertices.size())
        {
            continue;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(batch.vertices.size()),
            LitBillboardVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            batch.vertices.data(),
            batch.vertices.size() * sizeof(LitBillboardVertex));

        const uint32_t colorAbgr = questMarkerColorAbgr(batch.state, 255);
        const float ambient[4] = {
            redChannel(colorAbgr),
            greenChannel(colorAbgr),
            blueChannel(colorAbgr),
            1.0f,
        };
        const float clearUniform[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        const float fogDistances[4] = {4096.0f, 4096.0f, 4096.0f, 0.0f};
        bgfx::setTransform(billboardModelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(batch.vertices.size()));
        bindTexture(
            0,
            m_textureSamplerHandle,
            batch.pTexture->textureHandle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        bgfx::setUniform(m_billboardAmbientUniformHandle, ambient);
        bgfx::setUniform(m_billboardOverrideColorUniformHandle, clearUniform);
        bgfx::setUniform(m_billboardOutlineParamsUniformHandle, clearUniform);
        setBillboardFogColor(clearUniform);
        bgfx::setUniform(m_billboardFogDensitiesUniformHandle, clearUniform);
        bgfx::setUniform(m_billboardFogDistancesUniformHandle, fogDistances);
        bgfx::setState(IndoorBillboardOverlayDrawState);
        bgfx::submit(viewId, m_billboardProgramHandle);
    }
}

void IndoorRenderer::renderFxSegmentProjectiles(uint16_t viewId, const float *pViewMatrix)
{
    const std::vector<WorldFxSegmentProjectile> &segments = m_worldFxSystem.segmentProjectiles();

    if (segments.empty() || !bgfx::isValid(m_programHandle))
    {
        return;
    }

    const bx::Vec3 cameraForward = {pViewMatrix[2], pViewMatrix[6], pViewMatrix[10]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    std::vector<TerrainVertex> vertices;
    vertices.reserve(segments.size() * 6);

    for (const WorldFxSegmentProjectile &segment : segments)
    {
        const bx::Vec3 start = {segment.startX, segment.startY, segment.startZ};
        const bx::Vec3 end = {segment.endX, segment.endY, segment.endZ};
        const bx::Vec3 delta = {end.x - start.x, end.y - start.y, end.z - start.z};
        const float deltaLength = std::sqrt(delta.x * delta.x + delta.y * delta.y + delta.z * delta.z);

        if (deltaLength <= 0.001f)
        {
            continue;
        }

        const bx::Vec3 direction = {delta.x / deltaLength, delta.y / deltaLength, delta.z / deltaLength};
        bx::Vec3 side = {
            direction.y * cameraForward.z - direction.z * cameraForward.y,
            direction.z * cameraForward.x - direction.x * cameraForward.z,
            direction.x * cameraForward.y - direction.y * cameraForward.x
        };
        float sideLength = std::sqrt(side.x * side.x + side.y * side.y + side.z * side.z);

        if (sideLength <= 0.001f)
        {
            side = cameraUp;
            sideLength = std::sqrt(side.x * side.x + side.y * side.y + side.z * side.z);
        }

        const float halfWidth = segment.width * 0.5f / std::max(sideLength, 0.001f);
        side.x *= halfWidth;
        side.y *= halfWidth;
        side.z *= halfWidth;

        vertices.push_back({start.x - side.x, start.y - side.y, start.z - side.z, segment.colorAbgr});
        vertices.push_back({start.x + side.x, start.y + side.y, start.z + side.z, segment.colorAbgr});
        vertices.push_back({end.x + side.x, end.y + side.y, end.z + side.z, segment.colorAbgr});
        vertices.push_back({start.x - side.x, start.y - side.y, start.z - side.z, segment.colorAbgr});
        vertices.push_back({end.x + side.x, end.y + side.y, end.z + side.z, segment.colorAbgr});
        vertices.push_back({end.x - side.x, end.y - side.y, end.z - side.z, segment.colorAbgr});
    }

    if (vertices.empty()
        || bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), TerrainVertex::ms_layout)
            < vertices.size())
    {
        return;
    }

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(
        &transientVertexBuffer,
        static_cast<uint32_t>(vertices.size()),
        TerrainVertex::ms_layout);
    std::memcpy(transientVertexBuffer.data, vertices.data(), vertices.size() * sizeof(TerrainVertex));

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
    bgfx::setState(
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_DEPTH_TEST_LEQUAL
        | BGFX_STATE_BLEND_ADD | BGFX_STATE_MSAA);
    bgfx::submit(viewId, m_programHandle);
}

void IndoorRenderer::renderSpriteObjectBillboards(
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition,
    const std::vector<uint8_t> &visibleSectorMask,
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
    const bx::Vec3 cameraForward = {-pViewMatrix[2], -pViewMatrix[6], -pViewMatrix[10]};
    float billboardModelMatrix[16] = {};
    bx::mtxInverse(billboardModelMatrix, pViewMatrix);
    const float aspectRatio =
        m_lastRenderHeight > 0
        ? static_cast<float>(std::max(m_lastRenderWidth, 1)) / static_cast<float>(m_lastRenderHeight)
        : 1.0f;
    const std::array<IndoorVisibilityPlane, 4> frustumPlanes =
        buildIndoorBillboardFrustumPlanes(cameraPosition, m_cameraYawRadians, m_cameraPitchRadians, aspectRatio);
    const auto spriteBillboardVisible =
        [&frustumPlanes](float x, float y, float z,
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
            return billboardSphereInFrustum(center, radius, frustumPlanes);
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
        float cameraDepth = 0.0f;
        uint64_t lightingCacheKey = 0;
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

            if (!spriteBillboardVisible(x, y, z, *pFrame, *pTexture))
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
            drawItem.cameraDepth = deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;
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

            // Every item on the ground is a model (the placeholder when it has none): it takes the hover outline, and
            // no sprite is drawn.
            if (billboard.containedItemId != 0)
            {
                const bool contextHighlighted =
                    contextActionHighlightsWorldItem(pContextActionHit, billboard.objectIndex);
                const bool hovered = contextHighlighted
                    || (spriteOutlineEnabled && hoveredWorldItemIndex
                        && *hoveredWorldItemIndex == billboard.objectIndex);
                m_worldFxSystem.setItemModelOutline(billboard.objectKey, hovered
                    ? (contextHighlighted ? contextActionHighlightOutlineColor() : hoveredIndoorWorldItemOutlineColor())
                    : 0);
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
            drawItem.cameraDepth = deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;
            drawItem.lightingCacheKey = billboardLightingCacheKey(3, billboard.objectIndex);
            drawItems.push_back(drawItem);
        }
    }
    else
    {
        if (m_indoorSpriteObjectBillboardSet)
        {
            const auto appendStaticSpriteObjectDrawItem =
                [&](const SpriteObjectBillboard &billboard, size_t billboardIndex)
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
                drawItem.cameraDepth = deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;
                drawItem.lightingCacheKey = billboardLightingCacheKey(4, billboardIndex);
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
                                m_indoorSpriteObjectBillboardSet->billboards[billboardIndex],
                                billboardIndex);
                        }
                    }
                }
            }
            else
            {
                for (size_t billboardIndex = 0;
                    billboardIndex < m_indoorSpriteObjectBillboardSet->billboards.size();
                    ++billboardIndex)
                {
                    appendStaticSpriteObjectDrawItem(
                        m_indoorSpriteObjectBillboardSet->billboards[billboardIndex],
                        billboardIndex);
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
            if (!m_worldFxSystem.projectileShowsNativeSprite(projectile))
            {
                continue;
            }

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
            if (!m_worldFxSystem.projectileImpactShowsNativeSprite(impact))
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
            return left.cameraDepth > right.cameraDepth;
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
        uint64_t drawState = IndoorBillboardDrawState;
        std::vector<LitBillboardVertex> vertices;
    };

    LitSpriteObjectBillboardBatch litBillboardBatch = {};
    litBillboardBatch.vertices.reserve(drawItems.size() * 6);

    const float litAmbient[4] = {1.0f, 1.0f, 1.0f, 0.0f};
    const float clearOverrideColor[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    const float clearOutlineParams[4] = {0.0f, 0.0f, 0.0f, 0.0f};

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
                setBillboardFog();
                bgfx::setState(litBillboardBatch.drawState | BGFX_STATE_MSAA);
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
        const uint64_t drawState = drawItem.projectile || drawItem.impact
            ? IndoorBillboardOverlayDrawState : IndoorBillboardDrawState;
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
                setBillboardFog();
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
            if (litBillboardBatch.pTexture != &texture || litBillboardBatch.drawState != drawState)
            {
                flushLitBillboardBatch();
                litBillboardBatch.pTexture = &texture;
                litBillboardBatch.drawState = drawState;
            }

            litBillboardBatch.vertices.insert(
                litBillboardBatch.vertices.end(),
                vertices.begin(),
                vertices.end());
            continue;
        }

        flushLitBillboardBatch();

        const std::array<float, 4> ambient =
            billboardLightingUniform(
                lightingFrame,
                frame,
                center,
                drawItem.sectorId,
                drawItem.lightingCacheKey,
                pLightingStats);

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
        setBillboardFog();
        bgfx::setState(drawState | BGFX_STATE_MSAA);
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
    const GameplayContextActionState *pContextActionState)
{
    const GameplayWorldHit *pHit = selectedContextActionWorldHit(pContextActionState);

    if (pHit == nullptr
        || pHit->kind != GameplayWorldHitKind::EventTarget
        || !pHit->eventTarget.has_value()
        || !m_pIndoorMapData
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
            && eventTarget.secondaryIndex < m_pIndoorMapData->faces.size())
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
    IndoorFaceGeometryCache geometryCache(m_pIndoorMapData->faces.size());
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    geometryCache.setAttributeOverrides(mapDeltaData ? &*mapDeltaData : nullptr);

    for (size_t faceIndex : faceIndices)
    {
        if (faceIndex >= m_pIndoorMapData->faces.size())
        {
            continue;
        }

        const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];

        if (!indoorFaceHasActualEvent(m_pSceneRuntime, face))
        {
            continue;
        }

        if (eventTarget.targetKind == GameplayWorldEventTargetKind::Mechanism)
        {
            if (face.facetType == 3 || indoorFaceMarkedAsCeiling(*m_pIndoorMapData, faceIndex, face))
            {
                continue;
            }
        }
        else if (indoorFaceSuppressedForContextAction(
                *m_pIndoorMapData,
                faceIndex,
                face,
                eventTarget.attributes,
                eventTarget.contextActionMetadata,
                eventTarget.openedChestIds))
        {
            continue;
        }

        const IndoorFaceGeometryData *pGeometry =
            geometryCache.geometryForFace(*m_pIndoorMapData, m_renderVertices, faceIndex);

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
        | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
    bgfx::submit(viewId, m_programHandle);
}

const IndoorRenderer::IndoorTextureHandle *IndoorRenderer::findIndoorTextureHandle(
    const std::string &textureName) const
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const IndoorTextureHandle &textureHandle : m_indoorTextureHandles)
    {
        if (textureHandle.textureName == normalizedTextureName && bgfx::isValid(textureHandle.textureHandle))
        {
            return &textureHandle;
        }
    }

    return nullptr;
}

uint64_t IndoorRenderer::currentTexturedBatchGeometryRevision() const
{
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    return indoorRenderRevisions(
        mapDeltaData ? mapDeltaData->surfaceRevision : 0,
        pEventRuntimeState != nullptr ? pEventRuntimeState->outdoorSurfaceRevision : 0,
        pEventRuntimeState != nullptr ? pEventRuntimeState->indoorLightRevision : 0).texturedBatchGeometry;
}

// What the textured batches read from the event state: texture overrides and the facet masks the map delta did not
// take. Order-independent, so a revision bump that changed none of it (evt.SetFacetBit applied to the map delta)
// leaves it equal.
uint64_t IndoorRenderer::currentEventSurfaceSignature() const
{
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return 0;
    }

    const auto mix = [](uint64_t kind, uint64_t key, uint64_t value)
    {
        uint64_t hash = (kind * 0x9e3779b97f4a7c15ull) ^ (key * 0xc2b2ae3d27d4eb4full) ^ (value * 0x165667b19e3779f9ull);
        hash ^= hash >> 31;
        hash *= 0xbf58476d1ce4e5b9ull;
        hash ^= hash >> 29;
        return hash;
    };
    uint64_t signature = pEventRuntimeState->textureOverrides.size() * 3 + pEventRuntimeState->facetSetMasks.size() * 5
        + pEventRuntimeState->facetClearMasks.size() * 7;

    for (const auto &[cogNumber, textureName] : pEventRuntimeState->textureOverrides)
    {
        signature += mix(1, cogNumber, std::hash<std::string>{}(textureName));
    }

    for (const auto &[cogNumber, mask] : pEventRuntimeState->facetSetMasks)
    {
        signature += mix(2, cogNumber, mask);
    }

    for (const auto &[cogNumber, mask] : pEventRuntimeState->facetClearMasks)
    {
        signature += mix(3, cogNumber, mask);
    }

    return signature;
}

uint64_t IndoorRenderer::currentBakedStaticLightRevision() const
{
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();
    return indoorRenderRevisions(
        0,
        0,
        pEventRuntimeState != nullptr ? pEventRuntimeState->indoorLightRevision : 0).bakedStaticLighting;
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
    return m_texturedBatches.empty()
        || m_texturedBatchGeometryRevision != currentTexturedBatchGeometryRevision();
}

void IndoorRenderer::rebuildMechanismBindings()
{
    m_mechanismBindings.clear();
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::optional<ScriptedEventProgram> &localEventProgram =
        m_pSceneRuntime != nullptr ? m_pSceneRuntime->localEventProgram() : std::optional<ScriptedEventProgram>{};
    const std::optional<ScriptedEventProgram> &globalEventProgram =
        m_pSceneRuntime != nullptr ? m_pSceneRuntime->globalEventProgram() : std::optional<ScriptedEventProgram>{};

    if (!mapDeltaData || !m_pIndoorMapData)
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
            if (faceId >= m_pIndoorMapData->faces.size())
            {
                continue;
            }

            if (shownFaceCount < 6)
            {
                faceSummary += " " + std::to_string(faceId);
            }

            ++shownFaceCount;

            const IndoorFace &linkedFace = m_pIndoorMapData->faces[faceId];

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

    if (!mapDeltaData || pEventRuntimeState == nullptr || !m_pIndoorMapData)
    {
        return faceIndices;
    }

    std::vector<bool> seen(m_pIndoorMapData->faces.size(), false);

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

std::vector<uint32_t> IndoorRenderer::collectChangedMechanismDoorIds(
    const std::unordered_map<uint32_t, RuntimeMechanismState> &previousMechanisms) const
{
    std::vector<uint32_t> doorIds;
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (!mapDeltaData || pEventRuntimeState == nullptr)
    {
        return doorIds;
    }

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        RuntimeMechanismState baseMechanism = {};
        baseMechanism.state = door.state;
        baseMechanism.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
        baseMechanism.currentDistance = EventRuntime::calculateMechanismDistance(door, baseMechanism);

        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator previousIterator =
            previousMechanisms.find(door.doorId);
        const RuntimeMechanismState &previousMechanism =
            previousIterator != previousMechanisms.end() ? previousIterator->second : baseMechanism;

        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator currentIterator =
            pEventRuntimeState->mechanisms.find(door.doorId);
        const RuntimeMechanismState &currentMechanism =
            currentIterator != pEventRuntimeState->mechanisms.end() ? currentIterator->second : baseMechanism;

        if (mechanismPoseDiffers(currentMechanism, previousMechanism)
            || mechanismFacesMoving(currentMechanism) != mechanismFacesMoving(previousMechanism))
        {
            doorIds.push_back(door.doorId);
        }
    }

    return doorIds;
}

std::vector<size_t> IndoorRenderer::collectMechanismFaceIndicesForDoorIds(
    const std::vector<uint32_t> &doorIds) const
{
    std::vector<size_t> faceIndices;
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

    if (!mapDeltaData || !m_pIndoorMapData || doorIds.empty())
    {
        return faceIndices;
    }

    std::vector<bool> seen(m_pIndoorMapData->faces.size(), false);

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        if (std::find(doorIds.begin(), doorIds.end(), door.doorId) == doorIds.end())
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

std::vector<uint8_t> IndoorRenderer::collectMechanismFaceMask() const
{
    std::vector<uint8_t> faceMask;
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();

    if (!mapDeltaData || !m_pIndoorMapData)
    {
        return faceMask;
    }

    faceMask.assign(m_pIndoorMapData->faces.size(), 0);

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        for (uint16_t faceId : door.faceIds)
        {
            if (faceId < faceMask.size())
            {
                faceMask[faceId] = 1;
            }
        }
    }

    return faceMask;
}

bool IndoorRenderer::updateWaterGeometry()
{
    std::vector<WaterSurfaceGeometry> geometry;
    for (size_t batchIndex = 0; batchIndex < m_texturedBatches.size(); ++batchIndex)
    {
        const TexturedBatch &batch = m_texturedBatches[batchIndex];
        if (batch.waterColorAbgr == 0)
        {
            continue;
        }
        std::vector<WaterVertex> vertices;
        vertices.reserve(batch.indices.size());
        for (size_t index = 0; index + 2 < batch.indices.size(); index += 3)
        {
            std::array<bx::Vec3, 3> positions = {
                bx::Vec3{0.0f, 0.0f, 0.0f}, bx::Vec3{0.0f, 0.0f, 0.0f}, bx::Vec3{0.0f, 0.0f, 0.0f}};
            std::array<std::array<float, 2>, 3> uvs = {};
            for (size_t corner = 0; corner < 3; ++corner)
            {
                const TexturedVertex &vertex = batch.vertices[batch.indices[index + corner]];
                positions[corner] = {vertex.x, vertex.y, vertex.z};
                uvs[corner] = {vertex.u, vertex.v};
            }
            const TexturedVertex &first = batch.vertices[batch.indices[index]];
            const std::array<float, 2> flow =
                waterFaceFlow(positions, uvs, first.flowUPerSecond, first.flowVPerSecond);
            for (const bx::Vec3 &position : positions)
            {
                vertices.push_back({position.x, position.y, position.z, 0.0f, 0.0f, 1.0f,
                    flow[0], flow[1], 0.0f, 0.0f, batch.waterColorAbgr, liquidShaderValue(batch.liquid)});
            }
        }
        std::vector<WaterSurfaceGeometry> surfaces =
            buildWaterFaceGeometry(vertices, batch.sectorId, batch.backSectorId);
        for (WaterSurfaceGeometry &surface : surfaces)
        {
            geometry.push_back(std::move(surface));
        }
    }
    bool success = true;
    if (m_waterResourcesInitialized)
    {
        success = m_waterRenderer.updateGeometry(std::move(geometry));
    }
    else if (!geometry.empty() && m_pAssetFileSystem != nullptr)
    {
        m_waterRenderer.setIndoorFog(m_frameFog);
        success = m_waterRenderer.initialize(*m_pAssetFileSystem, std::move(geometry), {}, true);
        m_waterResourcesInitialized = success;
    }
    m_waterGeometryDirty = false;
    return success;
}

void IndoorRenderer::renderWaterReflections(const bx::Vec3 &forward,
    const IndoorLightingFrameInput &lightingInput, int width, int height, bool billboards)
{
    if (m_pIndoorMapData == nullptr)
    {
        return;
    }
    const bx::Vec3 reflectedForward = {forward.x, forward.y, -forward.z};
    for (const WaterRenderer::Reflection &reflection : m_waterRenderer.reflections())
    {
        if (!reflection.update)
        {
            continue;
        }
        // Reflections use their own portal query. They must never reveal the map or mark actors as seen.
        IndoorPortalVisibilityInput visibilityInput = {};
        visibilityInput.pMapData = m_pIndoorMapData;
        visibilityInput.pPortalGraph = m_indoorPortalGraph ? &m_indoorPortalGraph.value() : nullptr;
        visibilityInput.pVertices = &m_renderVertices;
        visibilityInput.pMapDeltaData = runtimeMapDeltaData() ? &runtimeMapDeltaData().value() : nullptr;
        visibilityInput.pEventRuntimeState = &runtimeEventRuntimeStateStorage();
        visibilityInput.cameraPosition = reflection.camera;
        visibilityInput.cameraForward = reflectedForward;
        visibilityInput.cameraUp = {0.0f, 0.0f, -1.0f};
        visibilityInput.startSectorId = reflection.sectorId;
        visibilityInput.collectPortalTraces = false;
        visibilityInput.verticalFovDegrees = 2.0f * std::atan(1.0f / reflection.projection[5]) * 180.0f / Pi;
        visibilityInput.aspectRatio = float(width) / float(height);
        visibilityInput.viewportHeight = reflection.size;
        const IndoorPortalVisibilityResult visibility = buildIndoorPortalVisibility(visibilityInput);
        IndoorLightingFrameInput reflectedLightingInput = lightingInput;
        reflectedLightingInput.cameraPosition = reflection.camera;
        reflectedLightingInput.pVisibleSectorMask = &visibility.visibleSectorMask;
        reflectedLightingInput.pVisibleSectorFrustums = &visibility.frustumsBySector;
        const IndoorLightingFrame lighting = m_indoorLightingRuntime.buildFrame(reflectedLightingInput);
        const ViewFrustum frustum(reflection.view.data(), reflection.projection.data(),
            bgfx::getCaps()->homogeneousDepth);
        const std::array<float, 4> clip = {0.0f, 0.0f, 1.0f, -reflection.height};
        // A map open to the sky reflects its sky where the reflected view meets no face (the capture clears black,
        // which drew the Isle of Ashes' sea black wherever it mirrored the sky). The sky state is the last frame's.
        if (m_openSky.enabled && m_skyRenderer.isReady())
        {
            m_skyRenderer.render(reflection.skyView, reflection.view.data(), reflection.projection.data(),
                m_frameSurroundings);
            applySceneSkyFog();
        }
        for (size_t batchIndex = 0; batchIndex < m_texturedBatches.size(); ++batchIndex)
        {
            const TexturedBatch &batch = m_texturedBatches[batchIndex];
            // Water reflections leave out the translucent faces (they would need their own sorted pass).
            if (batch.waterColorAbgr != 0 || batch.translucent
                || !indoorGeometrySectorsVisible(visibility.visibleSectorMask, batch.sectorId, batch.backSectorId)
                || (batch.hasBounds && (batch.boundsMax.z < reflection.height
                    || !frustum.intersectsBounds(batch.boundsMin, batch.boundsMax))))
            {
                continue;
            }
            const IndoorLightSelectionBounds bounds = {batch.boundsMin, batch.boundsMax, batch.hasBounds};
            IndoorDrawLightSet lights = IndoorLightingRuntime::selectDrawLightSetForBounds(
                lighting, reflection.camera, reflectedForward, batch.sectorId, batch.backSectorId,
                bounds, nullptr, false);
            // The room ambient is in the vertices; keep only the omitted lights' share.
            for (size_t channel = 1; channel < 4; ++channel)
            {
                lights.params[channel] = std::max(lights.params[channel] - lighting.ambient, 0.0f);
            }
            submitTexturedBatch(batchIndex, reflection.worldView, lights, nullptr, reflection.camera,
                m_cameraYawRadians, -m_cameraPitchRadians, width, height, false, clip,
                reflection.projectionScale);
        }
        bgfx::setUniform(m_worldClipPlaneUniform, clip.data());
        applySceneSkyFog();
        m_waterRenderer.renderIndoor(reflection.worldView, m_elapsedTime, lighting,
            reflection.camera, reflectedForward, nullptr, &reflection, visibility.visibleSectorMask);
        if (billboards)
        {
            float billboardView[16];
            waterReflectionView(billboardView, reflection.view.data(), reflection.height);
            renderDecorationBillboards(reflection.worldView, billboardView, reflection.camera,
                visibility.visibleSectorMask, visibility.frustumsBySector, lighting, nullptr, nullptr, &reflection);
            if (!m_decorationModels.empty())
            {
                // 3D decorations as lit in the main view (their placements keep last frame's light and visibility),
                // clipped at the water plane.
                Engine::ModelRenderLighting decorationLighting;
                decorationLighting.ambient = 1.0f;
                decorationLighting.direct = 0.0f;
                const float sheen = lighting.ambient * IndoorDecorationReflection;
                decorationLighting.environmentScale = {sheen, sheen, sheen};
                decorationLighting.displaySpaceLighting = true;
                // MM9's model lighting: the placements' base only (a reflection pass has no light grid).
                decorationLighting.fixedFunctionLighting = m_modelLighting.enabled;
                static const Engine::ModelInstanceSystem NoModels;
                const ViewFrustum modelFrustum(reflection.view.data(), reflection.projection.data(),
                    bgfx::getCaps()->homogeneousDepth);
                m_modelRenderer.renderReflection(NoModels, m_decorationModels.groups(), reflection.worldView,
                    {reflection.camera.x, reflection.camera.y, reflection.camera.z}, decorationLighting,
                    decorationLighting, {}, nullptr,
                    [&](const Engine::ModelBounds &bounds)
                    {
                        return bounds.max[2] >= reflection.height && modelFrustum.intersectsBounds(
                            {bounds.min[0], bounds.min[1], bounds.min[2]},
                            {bounds.max[0], bounds.max[1], bounds.max[2]});
                    }, std::abs(reflection.projection[5]) * float(reflection.size) * 0.5f,
                    float(SDL_GetTicks()) * 0.001f);
            }
            renderActorPreviewBillboards(reflection.worldView, billboardView, reflection.projection.data(), reflection.camera,
                visibility.visibleSectorMask, lighting, false, nullptr, nullptr, nullptr, nullptr, &reflection);
        }
    }
}

bool IndoorRenderer::submitTexturedBatch(size_t batchIndex, uint16_t viewId,
    const IndoorDrawLightSet &lights, const Engine::LightGridTextures *pLightGrid, const bx::Vec3 &eye, float yaw,
    float pitch, int width, int height, bool secretFacesDetected, const std::array<float, 4> &clipPlane,
    float projectionScale)
{
    if (batchIndex >= m_texturedBatches.size() || m_texturedBatches[batchIndex].drawGroup >= m_texturedDrawGroups.size())
    {
        return false;
    }
    const TexturedBatch &batch = m_texturedBatches[batchIndex];
    const IndoorFaceIndexRange range = m_faceDrawPlan.batchRange(uint32_t(batchIndex));
    const IndoorFaceGroupDraw draw = {batch.drawGroup, false, range.firstIndex, range.indexCount};
    return submitTexturedFaces(m_texturedDrawGroups[batch.drawGroup], draw, batch.translucent ? &batch : nullptr,
        viewId, lights, pLightGrid, eye, yaw, pitch, width, height, secretFacesDetected, clipPlane, false,
        projectionScale);
}

size_t IndoorRenderer::submitMainViewFaces(const std::vector<uint8_t> &drawnBatches, int width, int height,
    bool secretFacesDetected)
{
    if (m_faceDrawPlan.update(drawnBatches) && !m_faceDrawPlan.mergedIndices().empty())
    {
        const std::vector<uint32_t> &merged = m_faceDrawPlan.mergedIndices();
        if (!bgfx::isValid(m_mergedFaceIndexBufferHandle))
        {
            m_mergedFaceIndexBufferHandle = bgfx::createDynamicIndexBuffer(
                uint32_t(merged.size()), BGFX_BUFFER_INDEX32 | BGFX_BUFFER_ALLOW_RESIZE);
        }
        if (bgfx::isValid(m_mergedFaceIndexBufferHandle))
        {
            bgfx::update(m_mergedFaceIndexBufferHandle, 0,
                bgfx::copy(merged.data(), uint32_t(merged.size() * sizeof(uint32_t))));
        }
    }
    // The faces' room ambient is baked into their vertices and their dynamic lights come from the grid, so the light
    // set adds nothing.
    const IndoorDrawLightSet faceAmbient = {};
    const bx::Vec3 eye = {m_cameraPositionX, m_cameraPositionY, m_cameraPositionZ};
    // The view draws in submission order, so the terrain's depth is in place before anything is shaded.
    const bool terrainDepthWritten = bgfx::isValid(m_indoorTerrainDepthProgramHandle);
    if (terrainDepthWritten)
    {
        for (const IndoorFaceGroupDraw &draw : m_faceDrawPlan.draws())
        {
            if (draw.group >= m_texturedDrawGroups.size() || !m_texturedDrawGroups[draw.group].terrain
                || !drawableFaceFrame(m_texturedDrawGroups[draw.group], draw))
            {
                continue;
            }
            const TexturedDrawGroup &group = m_texturedDrawGroups[draw.group];
            float modelMatrix[16];
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, group.vertexBufferHandle, 0, group.vertexCount);
            if (draw.merged)
            {
                bgfx::setIndexBuffer(m_mergedFaceIndexBufferHandle, draw.firstIndex, draw.indexCount);
            }
            else
            {
                bgfx::setIndexBuffer(group.indexBufferHandle, draw.firstIndex, draw.indexCount);
            }
            bgfx::setState(BGFX_STATE_WRITE_Z | BGFX_STATE_DEPTH_TEST_LESS | BGFX_STATE_MSAA);
            bgfx::submit(MainViewId, m_indoorTerrainDepthProgramHandle);
        }
    }
    size_t submitted = 0;
    for (const IndoorFaceGroupDraw &draw : m_faceDrawPlan.draws())
    {
        if (draw.group < m_texturedDrawGroups.size()
            && submitTexturedFaces(m_texturedDrawGroups[draw.group], draw, nullptr, MainViewId, faceAmbient,
                &m_lightGrid, eye, m_cameraYawRadians, m_cameraPitchRadians, width, height, secretFacesDetected,
                {0.0f, 0.0f, 0.0f, 0.0f}, terrainDepthWritten))
        {
            ++submitted;
        }
    }
    return submitted;
}

std::optional<size_t> IndoorRenderer::drawableFaceFrame(const TexturedDrawGroup &group,
    const IndoorFaceGroupDraw &draw) const
{
    const bool indicesValid =
        draw.merged ? bgfx::isValid(m_mergedFaceIndexBufferHandle) : bgfx::isValid(group.indexBufferHandle);
    if (!bgfx::isValid(group.vertexBufferHandle) || group.frameTextureHandles.empty() || group.vertexCount == 0
        || draw.indexCount == 0 || !indicesValid)
    {
        return std::nullopt;
    }
    const size_t frameIndex =
        frameIndexForAnimation(group.frameLengthTicks, group.animationLengthTicks, currentAnimationTicks());
    if (frameIndex >= group.frameTextureHandles.size() || !bgfx::isValid(group.frameTextureHandles[frameIndex]))
    {
        return std::nullopt;
    }
    return frameIndex;
}

bool IndoorRenderer::submitTexturedFaces(const TexturedDrawGroup &group, const IndoorFaceGroupDraw &draw,
    const TexturedBatch *pTranslucentBatch, uint16_t viewId, const IndoorDrawLightSet &lights,
    const Engine::LightGridTextures *pLightGrid, const bx::Vec3 &eye, float yaw, float pitch, int width, int height,
    bool secretFacesDetected, const std::array<float, 4> &clipPlane, bool terrainDepthWritten, float projectionScale)
{
    const std::array<float, 4> secretPulseParams = {secretFacesDetected ? 1.0f : 0.0f, m_elapsedTime, 0.0f, 0.0f};
    const std::optional<size_t> drawableFrame = drawableFaceFrame(group, draw);
    if (!drawableFrame)
    {
        return false;
    }
    const size_t frameIndex = *drawableFrame;

    float modelMatrix[16];
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setUniform(m_worldClipPlaneUniform, clipPlane.data());
    bgfx::setVertexBuffer(0, group.vertexBufferHandle, 0, group.vertexCount);
    const int32_t lightmapPage = group.key.lightmapPage;
    const bool lightmapped = lightmapPage >= 0 && bgfx::isValid(group.lightmapUvBufferHandle)
        && size_t(lightmapPage) < m_lightmapTextureHandles.size();
    if (lightmapped)
    {
        bgfx::setVertexBuffer(1, group.lightmapUvBufferHandle, 0, group.vertexCount);
        bindTexture(1, m_lightmapSamplerHandle, m_lightmapTextureHandles[size_t(lightmapPage)],
            TextureFilterProfile::Lightmap, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        // The page's daylight share (a version 2 bake); without one the shader skips it (u_indoorBakedDaylight[0].w
        // 0) and the sampler takes the page itself, so no stage is left unbound.
        const bool daylightPage = size_t(lightmapPage) < m_daylightmapTextureHandles.size();
        bindTexture(2, m_daylightmapSamplerHandle,
            daylightPage ? m_daylightmapTextureHandles[size_t(lightmapPage)]
                         : m_lightmapTextureHandles[size_t(lightmapPage)],
            TextureFilterProfile::Lightmap, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        std::array<float, 12> bakedDaylight = m_frameBakedDaylight;
        bakedDaylight[3] = daylightPage ? 1.0f : 0.0f;
        bgfx::setUniform(m_indoorBakedDaylightUniformHandle, bakedDaylight.data(), 3);
    }
    if (draw.merged)
    {
        bgfx::setIndexBuffer(m_mergedFaceIndexBufferHandle, draw.firstIndex, draw.indexCount);
    }
    else
    {
        bgfx::setIndexBuffer(group.indexBufferHandle, draw.firstIndex, draw.indexCount);
    }
    bindTexture(
        0,
        m_textureSamplerHandle,
        group.frameTextureHandles[frameIndex],
        TextureFilterProfile::BModel);
    bgfx::setUniform(
        m_indoorLightPositionsUniformHandle,
        lights.positions.data(),
        MaxIndoorShaderLights);
    bgfx::setUniform(
        m_indoorLightColorsUniformHandle,
        lights.colors.data(),
        MaxIndoorShaderLights);
    bgfx::setUniform(m_indoorLightParamsUniformHandle, lights.params.data());
    const bool gridLit = pLightGrid != nullptr && pLightGrid->lightCount() > 0;
    // The faces' sectors, which the grid's lights test, are in their vertices.
    const std::array<float, 4> faceGrid = {gridLit ? 1.0f : 0.0f, 0.0f, 0.0f, 0.0f};
    bgfx::setUniform(m_indoorFaceGridUniformHandle, faceGrid.data());
    // The faces that take it are marked in their vertices.
    setFaceDaylight(m_daylight.enabled);
    m_lightGridBinding.bind(gridLit ? pLightGrid : nullptr, Engine::LightGridModeFull);
    std::array<float, 4> batchSecretPulseParams = secretPulseParams;

    if (group.textureWidth > 0 && group.textureHeight > 0)
    {
        batchSecretPulseParams[2] =
            -eye.x * 0.25f / static_cast<float>(group.textureWidth);
        batchSecretPulseParams[3] =
            eye.y * 0.25f / static_cast<float>(group.textureHeight);
    }

    bgfx::setUniform(m_secretPulseParamsUniformHandle, batchSecretPulseParams.data());
    const std::array<float, 4> indoorSkyParams = {
        batchSecretPulseParams[2],
        batchSecretPulseParams[3],
        yaw,
        pitch
    };
    bgfx::setUniform(m_indoorSkyParamsUniformHandle, indoorSkyParams.data());
    const float viewPlaneDistancePixels =
        (static_cast<float>(height) * 0.5f)
        / (std::tan((m_viewVerticalFovDegrees * Pi / 180.0f) * 0.5f) * projectionScale);
    const float horizonHeightOffset =
        (viewPlaneDistancePixels * eye.z)
        / (viewPlaneDistancePixels + IndoorSkyProjectionFarClipDistance)
        + static_cast<float>(height) * 0.5f;
    const std::array<float, 4> indoorSkyProjectionParams = {
        static_cast<float>(width) * 0.5f,
        horizonHeightOffset,
        1.0f / viewPlaneDistancePixels,
        IndoorSkyProjectionPitchOffsetRadians
    };
    bgfx::setUniform(m_indoorSkyProjectionParamsUniformHandle, indoorSkyProjectionParams.data());
    if (m_fog.enabled)
    {
        setFaceFog();
    }
    if (pTranslucentBatch != nullptr)
    {
        // Depth tested against the opaque scene, not written: the faces behind it stay visible through it.
        const bgfx::ProgramHandle program = m_fog.enabled
            ? m_indoorFogProgramHandles[lightmapped ? 5 : 2]
            : lightmapped ? m_indoorBakedTranslucentProgramHandle : m_indoorTranslucentProgramHandle;
        if (!bgfx::isValid(program) || !bgfx::isValid(m_indoorTranslucencyUniformHandle))
        {
            bgfx::discard();
            return false;
        }
        const IndoorFaceTranslucency &faceTranslucency = pTranslucentBatch->translucency;
        const std::array<float, 4> translucency = {faceTranslucency.tint[0], faceTranslucency.tint[1],
            faceTranslucency.tint[2], faceTranslucency.opacity};
        bgfx::setUniform(m_indoorTranslucencyUniformHandle, translucency.data());
        bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA);
        bgfx::submit(viewId, program);
        return true;
    }

    bgfx::setState(
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_WRITE_Z
        | BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_MSAA);

    if (group.terrain)
    {
        if (terrainDepthWritten)
        {
            // Its depth is already in the view (submitMainViewFaces): only the nearest terrain surface is shaded.
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_MSAA);
        }
        // Stages 8, 9, 10 and 14 (the light grid keeps 11); no specular highlight on the indoor lighting.
        m_terrainMaterials.bind(m_terrainAntiTiling, 0.0f);
        // Stage 12: the grass's colour where its tufts have thinned out, as on the outdoor terrain.
        const bool foliage = m_terrainGrassShown && m_terrainGrassReady && bgfx::isValid(m_terrainGrass.foliageMap());
        bgfx::setTexture(12, m_terrainFoliageSampler, foliage ? m_terrainGrass.foliageMap() : m_noTerrainFoliage,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        const std::array<float, 8> foliageParams = foliage ? m_terrainGrass.foliageParams()
            : std::array<float, 8>{0.0f, 1.0f, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f};
        bgfx::setUniform(m_terrainFoliageUniform, foliageParams.data(), 2);
        if (group.key.singleMaterialTerrain)
        {
            bgfx::submit(viewId,
                m_fog.enabled ? m_indoorTerrainSingleFogProgramHandle : m_indoorTerrainSingleProgramHandle);
            return true;
        }
        bgfx::submit(viewId, m_fog.enabled ? m_indoorTerrainFogProgramHandle : m_indoorTerrainProgramHandle);
        return true;
    }
    if (m_surfaceMaterialsEnabled && bgfx::isValid(group.materialNormal))
    {
        bindTexture(7, m_surfaceNormalSamplerHandle, group.materialNormal, TextureFilterProfile::BModel);
        bindTexture(8, m_surfaceDetailSamplerHandle, group.materialDetail, TextureFilterProfile::BModel);
        // Glass is lit from outside at any hour; parallax only in the main view (reflections are small and blurred).
        const float parallax = m_surfaceParallaxEnabled && viewId == MainViewId ? IndoorSurfaceParallaxDistance : 0.0f;
        const std::array<float, 4> material = {
            parallax, 1.0f, IndoorSurfaceHighlightStrength, IndoorSurfaceReflectionStrength};
        bgfx::setUniform(m_surfaceMaterialUniformHandle, material.data());
        // Screen-space reflections trace the previous main view, so only main-view draws use them.
        m_surfaceReflectionBinding.bind(viewId == MainViewId && m_surfaceReflectionsEnabled
            && m_pPostProcessing != nullptr ? m_pPostProcessing->reflectionHistory() : nullptr);
        bgfx::submit(viewId, m_fog.enabled ? m_indoorFogProgramHandles[lightmapped ? 4 : 1]
            : lightmapped ? m_indoorBakedMaterialProgramHandle : m_indoorLitMaterialProgramHandle);
        return true;
    }
    bgfx::submit(viewId, m_fog.enabled ? m_indoorFogProgramHandles[lightmapped ? 3 : 0]
        : lightmapped ? m_indoorBakedProgramHandle : m_indoorLitProgramHandle);
    return true;
}

float IndoorRenderer::cameraFarClipDistance() const
{
    return m_outdoorViewDistance > 0.0f ? m_outdoorViewDistance : IndoorCameraFarClipDistance;
}

void IndoorRenderer::setFaceFog()
{
    const std::array<float, 4> color = indoorFogColorUniform(m_frameFog);
    const std::array<float, 4> distances = indoorFogDistancesUniform(m_frameFog);
    if (bgfx::isValid(m_indoorFogModeUniformHandle) && bgfx::isValid(m_indoorFogLightUniformHandle))
    {
        const std::array<float, 4> mode = indoorFogModeUniform(m_frameFog);
        const std::array<float, 4> light = indoorFogLightUniform(m_frameFog);
        bgfx::setUniform(m_indoorFogModeUniformHandle, mode.data());
        bgfx::setUniform(m_indoorFogLightUniformHandle, light.data());
    }
    bgfx::setUniform(m_billboardFogColorUniformHandle, color.data());
    bgfx::setUniform(m_billboardFogDistancesUniformHandle, distances.data());
    if ((m_openSky.outdoorView || m_mist.enabled()) && bgfx::isValid(m_skyFogUniformHandle))
    {
        bgfx::setUniform(m_skyFogUniformHandle, m_openSky.outdoorView ? m_outdoorSkyFog.data() : m_flatSkyFog.data(),
            SkyFogUniformVectors);
    }
}

void IndoorRenderer::renderWaterTint(uint16_t viewId)
{
    if (!bgfx::isValid(m_waterTintProgramHandle) || m_pSceneRuntime == nullptr
        || bgfx::getAvailTransientVertexBuffer(6, TerrainVertex::ms_layout) < 6)
    {
        return;
    }

    const IndoorWaterVolume *pVolume = m_pSceneRuntime->partyRuntime().eyeWaterVolume();

    if (pVolume == nullptr)
    {
        return;
    }

    // MM9 scales the scene's light by the liquid's colour while the head is inside (cshell 0x100ab8a0); here the
    // frame is multiplied by mix(1, tint, strength).
    uint32_t abgr = 0xff000000u;

    for (size_t channel = 0; channel < 3; ++channel)
    {
        const float scale = 1.0f + (pVolume->tint[channel] - 1.0f) * IndoorWaterTintStrength;
        const uint32_t value = static_cast<uint32_t>(std::clamp(std::lround(scale * 255.0f), 0l, 255l));
        abgr |= value << (8 * channel);
    }

    const std::array<TerrainVertex, 6> vertices = {{
        {-1.0f, 1.0f, 0.5f, abgr},
        {-1.0f, -1.0f, 0.5f, abgr},
        {1.0f, -1.0f, 0.5f, abgr},
        {-1.0f, 1.0f, 0.5f, abgr},
        {1.0f, -1.0f, 0.5f, abgr},
        {1.0f, 1.0f, 0.5f, abgr}
    }};
    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TerrainVertex::ms_layout);
    std::memcpy(transientVertexBuffer.data, vertices.data(), sizeof(vertices));
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, 6);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_BLEND_FUNC(BGFX_STATE_BLEND_DST_COLOR, BGFX_STATE_BLEND_ZERO));
    bgfx::submit(viewId, m_waterTintProgramHandle);
}

void IndoorRenderer::applyScriptedFog()
{
    const EventRuntimeState *pState = runtimeEventRuntimeState();

    // The fog programs are loaded only for a map with a scene fog or the outdoor view (or a water volume's fog).
    if (pState == nullptr || !m_fog.enabled)
    {
        return;
    }

    const EventRuntimeState::ScriptedFog &scripted = pState->scriptedFog;

    if (scripted.revision != m_scriptedFogRevision)
    {
        m_scriptedFogRevision = scripted.revision;
        m_scriptedFogFrom = m_lastFrameFog;
        m_scriptedFogStartSeconds = m_elapsedTime;
        m_scriptedFogSeconds = scripted.seconds;
    }

    if (m_scriptedFogRevision == 0)
    {
        return;
    }

    IndoorFog target = m_frameFog;

    if (scripted.active)
    {
        target.enabled = true;
        target.color = scripted.color;
        target.nearDistance = scripted.nearDistance;
        target.farDistance = scripted.farDistance;
        target.sky = scripted.sky;
        target.hasNight = false;
    }

    const float amount = m_scriptedFogSeconds > 0.0f
        ? std::clamp((m_elapsedTime - m_scriptedFogStartSeconds) / m_scriptedFogSeconds, 0.0f, 1.0f)
        : 1.0f;
    m_frameFog = amount >= 1.0f ? target : indoorFogBlend(m_scriptedFogFrom, target, amount);
}

void IndoorRenderer::updateFrameDaylightAndFog()
{
    const float gameMinutes = m_pSceneRuntime != nullptr ? m_pSceneRuntime->worldRuntime().gameMinutes() : 9.0f * 60.0f;
    if (!m_mistSetting)
    {
        m_frameSurroundings.mist = {};
        m_flatSkyFog = {};
    }
    else if (m_mist.enabled())
    {
        // Under a scene daylight the mist darkens with the open air's light, as a fog that follows it does.
        const std::array<float, 3> light = m_daylight.enabled ? indoorDaylightFogScale(m_daylight, gameMinutes)
                                                              : std::array<float, 3>{1.0f, 1.0f, 1.0f};
        m_frameMistLight = light;
        m_frameSurroundings.mist = packMistUniform(m_mist, cameraPosition(), m_elapsedTime, light, m_mistStrengthSetting);
        m_flatSkyFog = packSkyFogUniform(nullptr, m_frameSurroundings);
    }
    if (m_fog.enabled)
    {
        m_frameFog = indoorFogAt(m_fog, skyNightAmount(gameMinutes));
        if (m_fog.followsDaylight && m_daylight.enabled)
        {
            const std::array<float, 3> scale = indoorDaylightFogScale(m_daylight, gameMinutes);
            for (size_t channel = 0; channel < 3; ++channel)
            {
                m_frameFog.color[channel] *= scale[channel];
            }
        }
    }
    if (m_openSky.outdoorView)
    {
        // An outdoor map's fog in clear weather (OutdoorGameView: its own fade over the last eighth of the view
        // distance), into the sky's flat fog colour; the faces, models and billboards add the sky's haze and its
        // colour in their direction from u_skyFog (sky_common.sh skyFogRatio, skyFogDisplayColor).
        m_frameFog = {};
        m_frameFog.enabled = true;
        m_frameFog.nearDistance = m_outdoorViewDistance * 0.875f;
        m_frameFog.farDistance = m_outdoorViewDistance;
        // A fog day (weather.yml fog chances) closes the fade in; the sky hazes with it (applyToSky).
        if (const WeatherOpenSkyFog &dayFog = m_openSkyWeather.fog(); dayFog.foggy)
        {
            m_frameFog.nearDistance = std::min(m_frameFog.nearDistance, dayFog.nearDistance);
            m_frameFog.farDistance = std::max(std::min(m_frameFog.farDistance, dayFog.farDistance),
                m_frameFog.nearDistance + 1.0f);
        }
        m_outdoorSkyFog = m_flatSkyFog;
        if (m_skyRenderer.isReady() && !m_skyRenderer.state().frame().presetName.empty())
        {
            const SkyFrameState &sky = m_skyRenderer.state().frame();
            m_frameFog.color = {sky.fogFlatDisplay[0], sky.fogFlatDisplay[1], sky.fogFlatDisplay[2]};
            m_outdoorSkyFog = packSkyFogUniform(&sky, m_frameSurroundings);
        }
    }
    applyScriptedFog();
    m_lastFrameFog = m_frameFog;
    // Under water the eye takes its volume's fog, if it has one (MM9: the volume's FogEnable), else the map's.
    if (m_fog.enabled && m_pSceneRuntime != nullptr)
    {
        if (const IndoorWaterVolume *pVolume = m_pSceneRuntime->partyRuntime().eyeWaterVolume();
            pVolume != nullptr && pVolume->fog.enabled)
        {
            m_frameFog = pVolume->fog;
            m_frameFog.lithtech = m_fog.lithtech;
        }
    }
    if (!m_daylight.enabled)
    {
        return;
    }

    m_frameDaylight = evaluateIndoorDaylight(m_daylight, gameMinutes);
    // The sky's hue as the outdoor bake takes it (OutdoorGameView::bakedLightingColors): half the sun disc's colour
    // and the ambient tint. The sky state is the last drawn frame's (renderOpenSky runs after the faces).
    if (m_skyRenderer.isReady() && !m_skyRenderer.state().frame().presetName.empty())
    {
        const SkyFrameState &sky = m_skyRenderer.state().frame();
        const SkyColor &disc = sky.value(SkyValue::SunDisc);
        tintIndoorDaylight(m_frameDaylight, {0.5f + 0.5f * disc[0], 0.5f + 0.5f * disc[1], 0.5f + 0.5f * disc[2]},
            sky.value(SkyValue::AmbientTint));
    }
    // Never darker than the darkest classic room (the minimum sector ambient).
    const float minimumAmbient = IndoorLightingRuntime::ambientFromMinAmbientLightLevel(31);
    for (float &channel : m_frameDaylight.ambient)
    {
        channel = std::max(channel, minimumAmbient);
    }
    // The lightmaps' daylight pages follow the same light (devdocs/INDOOR_BAKED_LIGHTING.md "Daylight pages").
    m_frameBakedDaylight =
        packIndoorBakedDaylight(indoorBakedDaylightScale(m_daylight, m_frameDaylight, minimumAmbient));
    // MM9's open-air lights in the static vertex light follow the sun (devdocs/INDOOR_OPEN_SKY.md "Daylight").
    m_frameOpenAirLightScale = indoorOpenAirLightScale(m_daylight, m_frameDaylight);
}

void IndoorRenderer::applyDaylightToLightingFrame(IndoorLightingFrame &lightingFrame) const
{
    if (!m_daylight.enabled)
    {
        return;
    }
    const float roomLight = indoorDaylightRoomLight(m_frameDaylight);
    for (size_t sectorId = 0; sectorId < lightingFrame.sectorAmbient.size(); ++sectorId)
    {
        if (indoorDaylightSector(m_daylight, int(sectorId)))
        {
            lightingFrame.sectorAmbient[sectorId] = roomLight;
        }
    }
}

void IndoorRenderer::applyDaylightSun(Engine::ModelRenderLighting &lighting, float exposure) const
{
    // The open air's sun on models (scene daylight, devdocs/INDOOR_OPEN_SKY.md "Daylight"): its direction and colour
    // as the faces take it, times the exposure the batch gives its ambient. Placements and creatures outside the open
    // air take none (decorations: their light's alpha 0; creatures: no call).
    if (!m_daylight.enabled)
    {
        return;
    }
    lighting.lightDirection = m_frameDaylight.sunDirection;
    lighting.direct = 1.0f;
    for (size_t channel = 0; channel < 3; ++channel)
    {
        lighting.directColor[channel] = m_frameDaylight.sun[channel] * exposure;
    }
}

void IndoorRenderer::setFaceDaylight(bool daylit)
{
    if (!bgfx::isValid(m_indoorDaylightUniformHandle))
    {
        return;
    }
    std::array<float, 12> values = {};
    // [0].w: the open air's lights' scale on the static vertex light (indoorVertexLight in the shader), 1: as baked.
    values[3] = 1.0f;
    if (daylit)
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            values[channel] = m_frameDaylight.ambient[channel];
            values[4 + channel] = m_frameDaylight.sun[channel];
            values[8 + channel] = m_frameDaylight.sunDirection[channel];
        }
        values[3] = m_frameOpenAirLightScale;
        values[11] = m_frameDaylight.sunGain;
    }
    bgfx::setUniform(m_indoorDaylightUniformHandle, values.data(), 3);
}

void IndoorRenderer::renderTranslucentFaces(uint16_t viewId, const bx::Vec3 &eye,
    const std::vector<uint8_t> &visibleSectorMask, int width, int height, bool secretFacesDetected)
{
    std::vector<IndoorTranslucentDraw> draws;
    const std::array<float, 3> eyePoint = {eye.x, eye.y, eye.z};
    for (size_t batchIndex = 0; batchIndex < m_texturedBatches.size(); ++batchIndex)
    {
        const TexturedBatch &batch = m_texturedBatches[batchIndex];
        // A face at opacity 0 (an invisible hit shell) would blend nothing and writes no depth, so it costs a draw
        // for no pixel; it stays a face for clicks and hits.
        if (!batch.translucent || batch.translucency.opacity <= 0.0f || batch.vertices.empty() || !batch.hasBounds
            || !indoorGeometrySectorsVisible(visibleSectorMask, batch.sectorId, batch.backSectorId))
        {
            continue;
        }
        const TexturedVertex &corner = batch.vertices.front();
        if (!indoorTranslucentFaceVisibleFrom(batch.translucency, batch.faceNormal, {corner.x, corner.y, corner.z},
                eyePoint))
        {
            continue;
        }
        const bx::Vec3 centre = bx::mul(bx::add(batch.boundsMin, batch.boundsMax), 0.5f);
        const bx::Vec3 offset = bx::sub(centre, eye);
        draws.push_back({batchIndex, bx::dot(offset, offset)});
    }
    sortIndoorTranslucentDrawsBackToFront(draws);
    const IndoorDrawLightSet faceAmbient = {};
    for (const IndoorTranslucentDraw &draw : draws)
    {
        submitTexturedBatch(draw.batchIndex, viewId, faceAmbient, &m_lightGrid, eye,
            m_cameraYawRadians, m_cameraPitchRadians, width, height, secretFacesDetected, {0.0f, 0.0f, 0.0f, 0.0f});
    }
}

namespace
{
// Whether a liquid's surface lies over the point (MM9's sea over its seabed): no plants grow there, and the ground
// along it is lush.
bool indoorLiquidOver(const IndoorMapData &map, float x, float y, float z)
{
    for (const IndoorWaterVolume &volume : map.waterVolumes)
    {
        for (const IndoorWaterPiece &piece : volume.pieces)
        {
            if (z < piece.top && indoorWaterPieceContains(piece, x, y))
            {
                return true;
            }
        }
    }
    return false;
}
}

bool IndoorRenderer::initializeTerrain(const Engine::AssetFileSystem &assets, const std::string &worldId,
    const IndoorMapData &indoorMapData, std::string &error)
{
    destroyTerrainResources();
    const IndoorTerrain &terrain = *indoorMapData.terrain;
    if ((bgfx::getCaps()->supported & BGFX_CAPS_TEXTURE_2D_ARRAY) == 0)
    {
        error = "terrain materials require texture array support";
        return false;
    }
    const std::string directory = "worlds/" + worldId + "/terrain_materials/";
    const std::string path = directory + terrain.materials;
    const std::optional<std::string> text = assets.readTextFile(path);
    if (!text)
    {
        error = "missing " + path;
        return false;
    }
    const std::optional<OutdoorTerrainMaterialConfig> config = parseTerrainMaterialConfig(*text, directory, path, error);
    if (!config)
    {
        return false;
    }
    TerrainMaterialSources sources;
    std::vector<std::function<void(std::string &)>> tasks;
    if (!TerrainMaterialSet::appendLoadTasks(assets, *config, sources, tasks, error))
    {
        return false;
    }
    std::vector<std::string> errors(tasks.size());
    Engine::parallelFor(tasks.size(), [&tasks, &errors](size_t index)
    {
        try
        {
            tasks[index](errors[index]);
        }
        catch (const std::exception &exception)
        {
            errors[index] = exception.what();
        }
    });
    for (const std::string &taskError : errors)
    {
        if (!taskError.empty())
        {
            error = taskError;
            return false;
        }
    }
    if (!TerrainMaterialSet::validateSources(sources, error) || !m_terrainMaterials.create(sources, *config, error))
    {
        return false;
    }
    m_terrainFaceMask.assign(indoorMapData.faces.size(), 0);
    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const std::string name = toLowerCopy(indoorMapData.faces[faceIndex].textureName);
        if (std::binary_search(terrain.textureNames.begin(), terrain.textureNames.end(), name)
            && !std::binary_search(terrain.excludedFaces.begin(), terrain.excludedFaces.end(), uint32_t(faceIndex)))
        {
            m_terrainFaceMask[faceIndex] = 1;
        }
    }
    m_terrainSurface.build(indoorMapData, m_renderVertices, m_terrainFaceMask);
    m_terrainMeadow = buildTerrainSurfaceMeadow(terrainSurfaceTriangles(), [&indoorMapData](float x, float y, float z)
    {
        return indoorLiquidOver(indoorMapData, x, y, z);
    });
    // The weight bits serve only the single-material split.
    markSingleMaterialTerrainFaces(indoorMapData, *config);
    m_terrainMaterials.releaseWeightLayers();
    // The grass's density: the weights of the layers with a meadow strength (grass, grass patches), times it.
    m_grassConfigPath = terrain.grass;
    m_grassDensity.clear();
    m_grassDensitySize = 0;
    if (!m_grassConfigPath.empty() && !sources.weightLevels[0].empty())
    {
        const size_t texels = sources.weightLevels[0].front().size() / 4;
        m_grassDensitySize = int(std::lround(std::sqrt(double(texels))));
        std::vector<float> density(texels, 0.0f);
        for (size_t layer = 0; layer < config->layers.size() && layer < 8; ++layer)
        {
            const float meadow = config->layers[layer].meadow;
            const std::vector<std::vector<uint8_t>> &levels = sources.weightLevels[layer / 4];
            if (meadow <= 0.0f || levels.empty() || levels.front().size() != texels * 4)
            {
                continue;
            }
            for (size_t texel = 0; texel < texels; ++texel)
            {
                density[texel] += float(levels.front()[texel * 4 + layer % 4]) / 255.0f * meadow;
            }
        }
        m_grassDensity.resize(texels);
        for (size_t texel = 0; texel < texels; ++texel)
        {
            m_grassDensity[texel] = uint8_t(std::lround(std::clamp(density[texel], 0.0f, 1.0f) * 255.0f));
        }
    }
    m_terrainFoliageSampler = bgfx::createUniform("s_terrainFoliage", bgfx::UniformType::Sampler);
    m_terrainFoliageUniform = bgfx::createUniform("u_terrainFoliage", bgfx::UniformType::Vec4, 2);
    const std::array<uint8_t, 4> noFoliage = {};
    m_noTerrainFoliage = bgfx::createTexture2D(1, 1, false, 1, bgfx::TextureFormat::RGBA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP, bgfx::copy(noFoliage.data(), sizeof(noFoliage)));
    m_indoorTerrainProgramHandle = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_terrain");
    m_indoorTerrainFogProgramHandle = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_terrain_fog");
    m_indoorTerrainSingleProgramHandle = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_terrain_single");
    m_indoorTerrainSingleFogProgramHandle =
        loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_terrain_single_fog");
    // Optional: without it the terrain is shaded where each of its triangles passes the depth test, as before.
    m_indoorTerrainDepthProgramHandle = loadProgram("vs_indoor_textured_lit", "fs_indoor_textured_depth");
    if (!bgfx::isValid(m_indoorTerrainProgramHandle) || !bgfx::isValid(m_indoorTerrainFogProgramHandle)
        || !bgfx::isValid(m_indoorTerrainSingleProgramHandle) || !bgfx::isValid(m_indoorTerrainSingleFogProgramHandle))
    {
        error = "terrain programs are unavailable";
        return false;
    }
    return true;
}

void IndoorRenderer::destroyTerrainResources()
{
    m_terrainGrass.shutdown(Engine::BgfxContext::isBgfxInitialized());
    m_terrainBushes.clear();
    m_terrainMeadow = {};
    for (bgfx::UniformHandle *pHandle : {&m_grassSunlightUniform, &m_grassFxLightParamsUniform,
             &m_grassCameraPositionUniform, &m_terrainFoliageSampler, &m_terrainFoliageUniform})
    {
        if (bgfx::isValid(*pHandle) && Engine::BgfxContext::isBgfxInitialized())
        {
            bgfx::destroy(*pHandle);
        }
        *pHandle = BGFX_INVALID_HANDLE;
    }
    if (bgfx::isValid(m_noTerrainFoliage) && Engine::BgfxContext::isBgfxInitialized())
    {
        bgfx::destroy(m_noTerrainFoliage);
    }
    m_noTerrainFoliage = BGFX_INVALID_HANDLE;
    m_terrainGrassAttempted = false;
    m_terrainGrassReady = false;
    m_grassConfigPath.clear();
    m_grassDensity.clear();
    m_grassDensitySize = 0;
    m_terrainMaterials.destroy();
    m_terrainSurface.clear();
    m_terrainFaceMask.clear();
    for (bgfx::ProgramHandle *pHandle : {&m_indoorTerrainProgramHandle, &m_indoorTerrainFogProgramHandle,
             &m_indoorTerrainSingleProgramHandle, &m_indoorTerrainSingleFogProgramHandle,
             &m_indoorTerrainDepthProgramHandle})
    {
        if (bgfx::isValid(*pHandle))
        {
            bgfx::destroy(*pHandle);
            *pHandle = BGFX_INVALID_HANDLE;
        }
    }
}

void IndoorRenderer::markSingleMaterialTerrainFaces(const IndoorMapData &indoorMapData,
    const OutdoorTerrainMaterialConfig &config)
{
    const std::vector<uint8_t> &weightLayers = m_terrainMaterials.weightLayers();
    const int weightSize = m_terrainMaterials.weightSize();
    if (weightSize <= 0 || weightLayers.size() != size_t(weightSize) * size_t(weightSize))
    {
        return;
    }
    // The weights cover the 65 536-unit map frame from its north-west corner (the shader's mapUv); a texel's centre
    // is at half a texel, and the coarser weight mips reach two texels further.
    constexpr int MipMargin = 2;
    const float texelsPerUnit = float(weightSize) / 65536.0f;
    const auto texelRange = [&](float low, float high)
    {
        const int first = int(std::floor(low * texelsPerUnit - 0.5f)) - MipMargin;
        const int last = int(std::floor(high * texelsPerUnit - 0.5f)) + 1 + MipMargin;
        return std::pair<int, int>(std::clamp(first, 0, weightSize - 1), std::clamp(last, 0, weightSize - 1));
    };
    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = indoorMapData.faces[faceIndex];
        if (m_terrainFaceMask[faceIndex] == 0 || face.vertexIndices.size() < 3)
        {
            continue;
        }
        float minimumX = std::numeric_limits<float>::max();
        float minimumY = std::numeric_limits<float>::max();
        float maximumX = std::numeric_limits<float>::lowest();
        float maximumY = std::numeric_limits<float>::lowest();
        float steepness = 0.0f;
        bool valid = true;
        for (uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= m_renderVertices.size())
            {
                valid = false;
                break;
            }
            const IndoorVertex &vertex = m_renderVertices[vertexIndex];
            const bx::Vec3 point = {float(vertex.x), float(vertex.y), float(vertex.z)};
            minimumX = std::min(minimumX, point.x);
            minimumY = std::min(minimumY, point.y);
            maximumX = std::max(maximumX, point.x);
            maximumY = std::max(maximumY, point.y);
            // The vertices carry it and the triangles interpolate it, so its maximum bounds the face's.
            steepness = std::max(steepness, m_terrainSurface.steepnessAt(point));
        }
        if (!valid)
        {
            continue;
        }
        // Columns run east from x = -32768, rows south from y = +32768.
        const auto [firstColumn, lastColumn] = texelRange(minimumX + 32768.0f, maximumX + 32768.0f);
        const auto [firstRow, lastRow] = texelRange(32768.0f - maximumY, 32768.0f - minimumY);
        uint8_t layers = 0;
        for (int row = firstRow; row <= lastRow; ++row)
        {
            for (int column = firstColumn; column <= lastColumn; ++column)
            {
                layers |= weightLayers[size_t(row) * size_t(weightSize) + size_t(column)];
            }
        }
        // The shader's macro noise raises the steepness by 0.1 at most.
        if (config.slopeLayer >= 0 && steepness + 0.1f > config.slopeStart)
        {
            layers |= uint8_t(1u << config.slopeLayer);
        }
        if (std::popcount(layers) == 1)
        {
            m_terrainFaceMask[faceIndex] = SingleMaterialTerrainFace;
        }
    }
}

std::vector<TerrainDecorationSurfaceTriangle> IndoorRenderer::terrainSurfaceTriangles() const
{
    std::vector<TerrainDecorationSurfaceTriangle> triangles;
    if (m_pIndoorMapData == nullptr)
    {
        return triangles;
    }
    const IndoorMapData &map = *m_pIndoorMapData;
    for (size_t faceIndex = 0; faceIndex < map.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = map.faces[faceIndex];
        if (!isTerrainFace(faceIndex) || face.vertexIndices.size() < 3)
        {
            continue;
        }
        std::vector<std::array<float, 3>> points;
        for (uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex < m_renderVertices.size())
            {
                const IndoorVertex &vertex = m_renderVertices[vertexIndex];
                points.push_back({float(vertex.x), float(vertex.y), float(vertex.z)});
            }
        }
        if (points.size() < 3)
        {
            continue;
        }
        bx::Vec3 centre = {0.0f, 0.0f, 0.0f};
        for (const std::array<float, 3> &point : points)
        {
            centre = {centre.x + point[0], centre.y + point[1], centre.z + point[2]};
        }
        centre = bx::mul(centre, 1.0f / float(points.size()));
        const bx::Vec3 normal = m_terrainSurface.normalAt(centre, m_terrainSurface.faceNormal(faceIndex));
        for (size_t k = 1; k + 1 < points.size(); ++k)
        {
            triangles.push_back({{points[0], points[k], points[k + 1]}, {normal.x, normal.y, normal.z}});
        }
    }
    return triangles;
}

void IndoorRenderer::ensureTerrainGrass()
{
    if (m_terrainGrassAttempted || m_grassConfigPath.empty() || m_grassDensitySize <= 0 || m_pAssetFileSystem == nullptr
        || m_pIndoorMapData == nullptr)
    {
        return;
    }
    // A missing or broken file is reported once, not retried every frame.
    m_terrainGrassAttempted = true;
    if ((bgfx::getCaps()->supported & BGFX_CAPS_INSTANCING) == 0)
    {
        std::cerr << "Terrain grass requires renderer instancing support.\n";
        return;
    }
    std::string error;
    const std::optional<TerrainDecorationConfig> config =
        loadTerrainDecorationConfigFile(*m_pAssetFileSystem, m_grassConfigPath, error);
    if (!config)
    {
        std::cerr << "Terrain grass unavailable (" << m_grassConfigPath << "): "
                  << (error.empty() ? "missing file" : error) << '\n';
        return;
    }
    TerrainDecorationSurface surface;
    surface.ground = terrainSurfaceTriangles();
    // Every other drawn face is an obstacle the plants keep clear of and grow uncut beside: walls, buildings, docks.
    const IndoorMapData &map = *m_pIndoorMapData;
    for (size_t faceIndex = 0; faceIndex < map.faces.size(); ++faceIndex)
    {
        const IndoorFace &face = map.faces[faceIndex];
        if (isTerrainFace(faceIndex) || face.isPortal || face.vertexIndices.size() < 3
            || hasFaceAttribute(face.attributes, FaceAttribute::Invisible)
            || indoorFaceShowsOpenSky(m_openSky, face.attributes))
        {
            continue;
        }
        const auto point = [this](uint16_t vertexIndex)
        {
            const IndoorVertex &vertex = m_renderVertices[vertexIndex];
            return std::array<float, 3>{float(vertex.x), float(vertex.y), float(vertex.z)};
        };
        if (std::any_of(face.vertexIndices.begin(), face.vertexIndices.end(),
                [this](uint16_t vertexIndex) { return vertexIndex >= m_renderVertices.size(); }))
        {
            continue;
        }
        for (size_t k = 1; k + 1 < face.vertexIndices.size(); ++k)
        {
            surface.obstacles.push_back({point(face.vertexIndices[0]), point(face.vertexIndices[k]),
                point(face.vertexIndices[k + 1])});
        }
    }
    if (m_indoorDecorationBillboardSet)
    {
        for (const DecorationBillboard &billboard : m_indoorDecorationBillboardSet->billboards)
        {
            surface.entities.push_back({billboard.name, {float(billboard.x), float(billboard.y), float(billboard.z)}});
        }
    }
    // The density between weight texel centres (the 65 536-unit map frame from its north-west corner).
    const int size = m_grassDensitySize;
    const std::vector<uint8_t> &grid = m_grassDensity;
    const auto density = [size, &grid](float x, float y)
    {
        const float u = (x + 32768.0f) / 65536.0f * float(size) - 0.5f;
        const float v = (32768.0f - y) / 65536.0f * float(size) - 0.5f;
        const int u0 = std::clamp(int(std::floor(u)), 0, size - 1);
        const int v0 = std::clamp(int(std::floor(v)), 0, size - 1);
        const int u1 = std::min(u0 + 1, size - 1);
        const int v1 = std::min(v0 + 1, size - 1);
        const float fu = std::clamp(u - float(u0), 0.0f, 1.0f);
        const float fv = std::clamp(v - float(v0), 0.0f, 1.0f);
        const auto at = [&](int cu, int cv) { return float(grid[size_t(cv) * size_t(size) + size_t(cu)]) / 255.0f; };
        return (at(u0, v0) * (1.0f - fu) + at(u1, v0) * fu) * (1.0f - fv)
            + (at(u0, v1) * (1.0f - fu) + at(u1, v1) * fu) * fv;
    };
    surface.density = density;
    surface.underWater = [&map](float x, float y, float z)
    {
        return indoorLiquidOver(map, x, y, z);
    };
    surface.pMeadow = &m_terrainMeadow;
    TerrainDecorationPlacement placement = scatterTerrainDecorationsOnSurface(surface, *config);
    std::string bushError;
    if (!m_terrainBushes.load(*m_pAssetFileSystem, config->bushes, placement.bushes, bushError))
    {
        std::cerr << "Terrain bushes unavailable: " << bushError << '\n';
    }
    m_modelRenderer.preloadStatic(m_terrainBushes.groups());
    const size_t bushes = placement.bushes.size();
    if (placement.instances.empty())
    {
        return;
    }
    const size_t tufts = placement.instances.size();
    m_grassSunlightUniform = bgfx::createUniform("u_outdoorSunlight", bgfx::UniformType::Vec4);
    m_grassFxLightParamsUniform = bgfx::createUniform("u_fxLightParams", bgfx::UniformType::Vec4);
    m_grassCameraPositionUniform = bgfx::createUniform("u_cameraPosition", bgfx::UniformType::Vec4);
    m_terrainGrassReady = m_terrainGrass.initialize(*m_pAssetFileSystem, *config, std::move(placement),
        loadProgram("vs_terrain_decoration", "fs_terrain_decoration"),
        loadProgram("vs_terrain_decoration", "fs_terrain_decoration_shadow"));
    std::cout << "Terrain grass: " << tufts << " tufts, " << bushes << " bushes from " << m_grassConfigPath << '\n';
}

void IndoorRenderer::updateTerrainBushes(const bx::Vec3 &eye)
{
    m_terrainBushes.updateFade({eye.x, eye.y, eye.z});
    // A decoration's light in the open sky (updateDecorationModels): the ambient share, the batch's exposure divided
    // out; the sun comes from the batch (applyDaylightSun).
    const float ambient = (m_daylight.enabled ? indoorDaylightModelAmbient(m_frameDaylight) : 1.0f)
        / IndoorDecorationExposure;
    const float sun = m_daylight.enabled ? 1.0f : 0.0f;
    for (Engine::ModelStaticGroup &group : m_terrainBushes.groups())
    {
        for (Engine::ModelStaticPlacement &placement : group.placements)
        {
            placement.light = {ambient, ambient, ambient, sun};
        }
    }
}

void IndoorRenderer::renderTerrainGrass(uint16_t viewId, const bx::Vec3 &eye, const bx::Vec3 &forward,
    const float *pProjectionMatrix, float aspect)
{
    ensureTerrainGrass();
    if (!m_terrainGrassReady)
    {
        return;
    }
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    const bx::Vec3 right = bx::normalize(bx::cross(forward, worldUp));
    const bx::Vec3 up = bx::cross(right, forward);
    const float verticalFov = 2.0f * std::atan(1.0f / std::max(std::abs(pProjectionMatrix[5]), 0.0001f));
    m_terrainGrass.setView(eye, forward, right, up, aspect, verticalFov);
    m_terrainGrassDraws.clear();
    m_terrainGrass.collectDraws(m_terrainGrassDraws);
    if (m_terrainGrassDraws.empty())
    {
        return;
    }
    // Lit as one brightness (the outdoor grass shader takes no colour) that follows the flat terrain under it through
    // the day: the outdoor grass's noon light (OutdoorGrassNoonLight, the shader's cap) times the terrain's light now
    // over its light at noon. The terrain's light: the faces' daylight, min(ambient + sun x min(1, gain x N.L), 1)
    // with N up, and the terrain's mean vertex light with its open-air share by the hour, at most 2 as the faces'.
    // It goes in as the shader's ambient with no sun direction: through the sun term the gain multiplied the sun's
    // strength, so the grass sat at the cap until dusk while the ground darkened through the afternoon (Sturmford at
    // 18:10: three times the ground). No effect lights; the scene's fog or the sky haze.
    constexpr float OutdoorGrassNoonLight = 0.85f;
    const auto luma = [](const std::array<float, 3> &rgb)
    {
        return 0.2126f * rgb[0] + 0.7152f * rgb[1] + 0.0722f * rgb[2];
    };
    const auto terrainLight = [this, &luma](const IndoorDaylightLight &light, float openAirLightScale)
    {
        const float facing = std::clamp(light.sunDirection[2] * light.sunGain, 0.0f, 1.0f);
        const float daylight = std::min(luma(light.ambient) + luma(light.sun) * facing, 1.0f);
        return std::min(daylight + m_terrainLampLight + m_terrainOpenAirLight * openAirLightScale, 2.0f);
    };
    const float noonLight = terrainLight(evaluateIndoorDaylight(m_daylight, 12.0f * 60.0f), 1.0f);
    const float brightness = noonLight > 0.001f
        ? OutdoorGrassNoonLight * terrainLight(m_frameDaylight, m_frameOpenAirLightScale) / noonLight
        : OutdoorGrassNoonLight;
    const std::array<float, 4> sunlight = {0.0f, 0.0f, 0.0f, brightness};
    const std::array<float, 4> fxLightParams = {0.0f, 1.0f, 1.0f, 0.0f};
    const std::array<float, 4> camera = {eye.x, eye.y, eye.z, 0.0f};
    for (const TerrainDecorationPatch &patch : m_terrainGrassDraws)
    {
        bgfx::setUniform(m_grassSunlightUniform, sunlight.data());
        bgfx::setUniform(m_grassFxLightParamsUniform, fxLightParams.data());
        bgfx::setUniform(m_grassCameraPositionUniform, camera.data());
        setBillboardFog();
        m_terrainGrass.submit(viewId, patch, m_elapsedTime, false, false);
    }
}

void IndoorRenderer::applyTerrainVertices(size_t faceIndex, std::vector<TexturedVertex> &vertices) const
{
    const bx::Vec3 faceNormal = m_terrainSurface.faceNormal(faceIndex);
    for (TexturedVertex &vertex : vertices)
    {
        const bx::Vec3 point = {vertex.x, vertex.y, vertex.z};
        const bx::Vec3 normal = m_terrainSurface.normalAt(point, faceNormal);
        vertex.u = m_terrainSurface.steepnessAt(point);
        vertex.v = m_terrainMeadow.sample(vertex.x, vertex.y);
        vertex.gradientU = {normal.x, normal.y, normal.z};
    }
}

void IndoorRenderer::destroyBakedLightingResources()
{
    for (std::vector<bgfx::TextureHandle> *pHandles : {&m_lightmapTextureHandles, &m_daylightmapTextureHandles})
    {
        for (bgfx::TextureHandle handle : *pHandles)
        {
            if (bgfx::isValid(handle))
            {
                bgfx::destroy(handle);
            }
        }
        pHandles->clear();
    }
    for (bgfx::ProgramHandle *pHandle : {&m_indoorBakedProgramHandle, &m_indoorBakedMaterialProgramHandle})
    {
        if (bgfx::isValid(*pHandle))
        {
            bgfx::destroy(*pHandle);
            *pHandle = BGFX_INVALID_HANDLE;
        }
    }
    for (bgfx::UniformHandle *pHandle :
        {&m_lightmapSamplerHandle, &m_daylightmapSamplerHandle, &m_indoorBakedDaylightUniformHandle})
    {
        if (bgfx::isValid(*pHandle))
        {
            bgfx::destroy(*pHandle);
            *pHandle = BGFX_INVALID_HANDLE;
        }
    }
    m_bakedLightingActive = false;
}

void IndoorRenderer::ensureIndoorSwapTexture(const std::string &textureName)
{
    if (!m_indoorTextureSet || textureName.empty() || m_pAssetFileSystem == nullptr)
    {
        return;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const OutdoorBitmapTexture &texture : m_indoorTextureSet->textures)
    {
        if (toLowerCopy(texture.textureName) == normalizedTextureName)
        {
            return;
        }
    }

    if (m_missingSwapTextureNames.contains(normalizedTextureName))
    {
        return;
    }

    std::optional<OutdoorBitmapTexture> texture;

    try
    {
        texture = loadSurfaceTexture(*m_pAssetFileSystem, normalizedTextureName);
    }
    catch (const std::exception &exception)
    {
        std::cerr << "IndoorRenderer: swapped-in texture " << normalizedTextureName << ": " << exception.what()
                  << '\n';
    }

    if (!texture)
    {
        std::cerr << "IndoorRenderer: swapped-in texture " << normalizedTextureName << " not found\n";
        m_missingSwapTextureNames.insert(normalizedTextureName);
        return;
    }

    m_indoorTextureSet->textures.push_back(std::move(*texture));
}

IndoorRenderer::TexturedDrawGroup IndoorRenderer::createTexturedDrawGroup(const IndoorFaceDrawGroupKey &key,
    const std::string &textureName, std::vector<TexturedDrawGroup> &previousGroups)
{
    TexturedDrawGroup group = {};
    group.key = key;
    // The last build's buffer of the same group, refilled in place when its size is unchanged.
    for (TexturedDrawGroup &previousGroup : previousGroups)
    {
        if (previousGroup.key == key)
        {
            group.vertexBufferHandle = previousGroup.vertexBufferHandle;
            group.vertexCapacity = previousGroup.vertexCapacity;
            previousGroup.vertexBufferHandle = BGFX_INVALID_HANDLE;
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

    group.animationLengthTicks = animation.animationLengthTicks;

    for (const SurfaceAnimationFrame &frame : animation.frames)
    {
        const IndoorTextureHandle *pTextureHandle = findIndoorTextureHandle(frame.textureName);
        const bool singleFrame = animation.frames.size() == 1;

        if (pTextureHandle != nullptr)
        {
            group.frameTextureHandles.push_back(pTextureHandle->textureHandle);
            group.frameLengthTicks.push_back(frame.frameLengthTicks);
            if (singleFrame)
            {
                group.materialNormal = pTextureHandle->materialNormal;
                group.materialDetail = pTextureHandle->materialDetail;
            }
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

        const bgfx::TextureHandle textureHandle = createSurfaceTexture2D(
            uint16_t(pFrameTexture->physicalWidth),
            uint16_t(pFrameTexture->physicalHeight),
            pFrameTexture->pixels,
            pFrameTexture->cookedTexture.get(),
            TextureFilterProfile::BModel
        );

        if (!bgfx::isValid(textureHandle))
        {
            continue;
        }

        IndoorTextureHandle textureHandleEntry = {};
        textureHandleEntry.textureName = toLowerCopy(frame.textureName);
        textureHandleEntry.textureHandle = textureHandle;
        if (pFrameTexture->materialNormal != nullptr)
        {
            textureHandleEntry.materialNormal =
                createCookedTexture2D(*pFrameTexture->materialNormal, TextureFilterProfile::BModel);
            textureHandleEntry.materialDetail =
                createCookedTexture2D(*pFrameTexture->materialDetail, TextureFilterProfile::BModel);
        }
        if (singleFrame)
        {
            group.materialNormal = textureHandleEntry.materialNormal;
            group.materialDetail = textureHandleEntry.materialDetail;
        }
        m_indoorTextureHandles.push_back(std::move(textureHandleEntry));
        group.frameTextureHandles.push_back(textureHandle);
        group.frameLengthTicks.push_back(frame.frameLengthTicks);
    }
    return group;
}

void IndoorRenderer::addFaceDrawConflicts(std::span<const size_t> faceIndices)
{
    // Faces meet at one depth only where they touch: within the slack of each other's plane (the depth buffer's
    // precision far off), inside the other's polygon by more than the inset. The grid is the plan in cells.
    constexpr float Slack = 1.0f;
    constexpr float EdgeInset = 0.01f;
    constexpr float CellSize = 512.0f;
    const auto cellRange = [](float low, float high)
    {
        return std::pair<int32_t, int32_t>{int32_t(std::floor((low - Slack) / CellSize)),
            int32_t(std::floor((high + Slack) / CellSize))};
    };
    const auto cellKey = [](int32_t x, int32_t y)
    {
        return (uint64_t(uint32_t(x)) << 32) | uint32_t(y);
    };
    // The faces' new bounds, each entered in its cells. A moved face leaves the cells of its previous bounds first:
    // movers update every frame, and stale entries would pile up in the cells and slow each later frame.
    std::vector<size_t> faces;
    for (size_t faceIndex : faceIndices)
    {
        if (faceIndex >= m_faceDrawBounds.size() || faceIndex >= m_faceBatchIndices.size()
            || m_faceBatchIndices[faceIndex] < 0)
        {
            continue;
        }
        const TexturedBatch &batch = m_texturedBatches[size_t(m_faceBatchIndices[faceIndex])];
        const uint32_t offset = m_faceVertexOffsets[faceIndex];
        const uint32_t count = m_faceVertexCounts[faceIndex];
        // Translucent faces draw later, sorted on their own.
        if (batch.translucent || count == 0 || offset + count > batch.vertices.size())
        {
            continue;
        }
        FaceDrawBounds &bounds = m_faceDrawBounds[faceIndex];
        if (bounds.valid)
        {
            const auto [oldFirstX, oldLastX] = cellRange(bounds.min.x, bounds.max.x);
            const auto [oldFirstY, oldLastY] = cellRange(bounds.min.y, bounds.max.y);
            for (int32_t x = oldFirstX; x <= oldLastX; ++x)
            {
                for (int32_t y = oldFirstY; y <= oldLastY; ++y)
                {
                    const auto cell = m_faceDrawGrid.find(cellKey(x, y));
                    if (cell != m_faceDrawGrid.end())
                    {
                        std::erase(cell->second, uint32_t(faceIndex));
                    }
                }
            }
        }
        bounds.min = {batch.vertices[offset].x, batch.vertices[offset].y, batch.vertices[offset].z};
        bounds.max = bounds.min;
        for (uint32_t vertex = offset + 1; vertex < offset + count; ++vertex)
        {
            const TexturedVertex &point = batch.vertices[vertex];
            bounds.min = {std::min(bounds.min.x, point.x), std::min(bounds.min.y, point.y),
                std::min(bounds.min.z, point.z)};
            bounds.max = {std::max(bounds.max.x, point.x), std::max(bounds.max.y, point.y),
                std::max(bounds.max.z, point.z)};
        }
        std::vector<IndoorFacePoint> polygon;
        for (uint16_t vertexIndex : m_pIndoorMapData->faces[faceIndex].vertexIndices)
        {
            if (vertexIndex < m_renderVertices.size())
            {
                const IndoorVertex &vertex = m_renderVertices[vertexIndex];
                polygon.push_back({float(vertex.x), float(vertex.y), float(vertex.z)});
            }
        }
        bounds.shape = makeIndoorFaceShape(polygon);
        bounds.valid = true;
        const auto [firstX, lastX] = cellRange(bounds.min.x, bounds.max.x);
        const auto [firstY, lastY] = cellRange(bounds.min.y, bounds.max.y);
        for (int32_t x = firstX; x <= lastX; ++x)
        {
            for (int32_t y = firstY; y <= lastY; ++y)
            {
                m_faceDrawGrid[cellKey(x, y)].push_back(uint32_t(faceIndex));
            }
        }
        faces.push_back(faceIndex);
    }
    // Close in their bounds, and covering the same pixels at one depth (IndoorFaceDrawGroups.h).
    const auto touch = [&](size_t first, size_t second)
    {
        const FaceDrawBounds &a = m_faceDrawBounds[first];
        const FaceDrawBounds &b = m_faceDrawBounds[second];
        return a.min.x <= b.max.x + Slack && b.min.x <= a.max.x + Slack
            && a.min.y <= b.max.y + Slack && b.min.y <= a.max.y + Slack
            && a.min.z <= b.max.z + Slack && b.min.z <= a.max.z + Slack
            && indoorFacesMeetAtOneDepth(a.shape, b.shape, Slack, EdgeInset);
    };
    // Each pair once: a face's cells may share several faces with it, and two new faces meet from both sides.
    std::vector<uint8_t> isNew(m_faceDrawBounds.size(), 0);
    for (size_t faceIndex : faces)
    {
        isNew[faceIndex] = 1;
    }
    std::vector<uint32_t> seen(m_faceDrawBounds.size(), UINT32_MAX);
    for (size_t faceIndex : faces)
    {
        const FaceDrawBounds &bounds = m_faceDrawBounds[faceIndex];
        const uint32_t batch = uint32_t(m_faceBatchIndices[faceIndex]);
        const auto [firstX, lastX] = cellRange(bounds.min.x, bounds.max.x);
        const auto [firstY, lastY] = cellRange(bounds.min.y, bounds.max.y);
        for (int32_t x = firstX; x <= lastX; ++x)
        {
            for (int32_t y = firstY; y <= lastY; ++y)
            {
                for (uint32_t other : m_faceDrawGrid[cellKey(x, y)])
                {
                    if (seen[other] == uint32_t(faceIndex) || (isNew[other] != 0 && other <= faceIndex))
                    {
                        continue;
                    }
                    seen[other] = uint32_t(faceIndex);
                    const uint32_t otherBatch = uint32_t(m_faceBatchIndices[other]);
                    if (otherBatch != batch && m_faceDrawBounds[other].valid
                        && !m_faceDrawPlan.hasConflict(batch, otherBatch) && touch(faceIndex, other))
                    {
                        m_faceDrawPlan.addConflict(batch, otherBatch);
                    }
                }
            }
        }
    }
}

void IndoorRenderer::destroyTexturedDrawGroups(std::vector<TexturedDrawGroup> &groups)
{
    for (TexturedDrawGroup &group : groups)
    {
        if (bgfx::isValid(group.vertexBufferHandle))
        {
            bgfx::destroy(group.vertexBufferHandle);
        }
        if (bgfx::isValid(group.indexBufferHandle))
        {
            bgfx::destroy(group.indexBufferHandle);
        }
        if (bgfx::isValid(group.lightmapUvBufferHandle))
        {
            bgfx::destroy(group.lightmapUvBufferHandle);
        }
    }
    groups.clear();
}

bool IndoorRenderer::rebuildAllTexturedBatches(uint64_t &texturedBuildNanoseconds)
{
    m_waterGeometryDirty = true;
    if (!m_indoorTextureSet || !m_pIndoorMapData)
    {
        destroyTexturedDrawGroups(m_texturedDrawGroups);
        m_texturedBatches.clear();
        m_faceDrawPlan.clear();
        m_faceDrawBounds.clear();
        m_faceDrawGrid.clear();
        m_faceBatchIndices.clear();
        m_faceVertexOffsets.clear();
        m_faceVertexCounts.clear();
        m_faceSubdivisionTriangles.clear();
        m_texturedBatchGeometryRevision = currentTexturedBatchGeometryRevision();
        m_bakedStaticLightRevision = currentBakedStaticLightRevision();
        m_bakedStaticLightEnabledStates =
            m_pIndoorMapData
                ? bakedStaticLightEnabledStates(*m_pIndoorMapData, runtimeEventRuntimeState(),
                    m_indoorDecorationBillboardSet ? &*m_indoorDecorationBillboardSet : nullptr)
                : std::vector<uint8_t>();
        m_bakedSectorAmbientLevels = bakedSectorAmbientLevels();
        return true;
    }

    std::vector<TexturedDrawGroup> previousGroups = std::move(m_texturedDrawGroups);
    m_texturedDrawGroups.clear();
    m_texturedBatches.clear();
    m_faceDrawPlan.clear();
    m_faceDrawBounds.clear();
    m_faceDrawGrid.clear();
    m_faceBatchIndices.assign(m_pIndoorMapData->faces.size(), -1);
    m_faceVertexOffsets.assign(m_pIndoorMapData->faces.size(), 0);
    m_faceVertexCounts.assign(m_pIndoorMapData->faces.size(), 0);
    m_faceSubdivisionTriangles.assign(m_pIndoorMapData->faces.size(), {});

    std::unordered_map<std::string, size_t> batchIndicesByTexture;
    std::unordered_map<IndoorFaceDrawGroupKey, size_t, IndoorFaceDrawGroupKeyHash> groupIndicesByKey;
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();
    const std::vector<uint8_t> mechanismFaceMask = collectMechanismFaceMask();
    rebuildBakedStaticLightReach();
    const std::vector<BakedStaticLightSource> bakedStaticLightSources =
        buildBakedStaticLightSources(
            *m_pIndoorMapData,
            eventRuntimeState ? &eventRuntimeState.value() : nullptr,
            m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr,
            false);
    const std::vector<BakedStaticLightSource> bakedStaticLightSubdivisionSources =
        buildBakedStaticLightSources(
            *m_pIndoorMapData,
            eventRuntimeState ? &eventRuntimeState.value() : nullptr,
            m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr,
            true);

    // A texture an event swaps onto faces (evt.SetTexture) that no face of the map uses is loaded now, before the
    // pointers below into the texture set are taken.
    if (eventRuntimeState)
    {
        for (const auto &[cogNumber, overrideTextureName] : eventRuntimeState->textureOverrides)
        {
            ensureIndoorSwapTexture(overrideTextureName);
        }
    }

    const std::vector<BakedStaticLightSource> noStaticLightSources;
    std::unordered_map<std::string, const OutdoorBitmapTexture *> texturesByName;
    for (const OutdoorBitmapTexture &texture : m_indoorTextureSet->textures)
    {
        texturesByName.emplace(texture.textureName, &texture);
    }

    // The rotating movers' faces carry their stored pose's lightmap through the swing (empty without such movers).
    const std::vector<std::optional<IndoorRigidMotion>> rotatingFaceMotions = buildIndoorRotatingFaceMotions(
        *m_pIndoorMapData,
        runtimeMapDeltaData() ? &*runtimeMapDeltaData() : nullptr,
        eventRuntimeState ? &eventRuntimeState.value() : nullptr);

    double terrainLampLight = 0.0;
    double terrainOpenAirLight = 0.0;
    size_t terrainVertexCount = 0;
    for (size_t faceIndex = 0; faceIndex < m_pIndoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];
        const std::string textureName = resolveFaceTextureName(faceIndex, face, eventRuntimeState);
        // A translucent face (devdocs/INDOOR_TRANSLUCENT_FACES.md) may be a portal; a map without any skips the lookup.
        const IndoorFaceTranslucency *pTranslucency = findIndoorFaceTranslucency(*m_pIndoorMapData, faceIndex);

        if ((face.isPortal && pTranslucency == nullptr) || textureName.empty() || face.vertexIndices.size() < 3)
        {
            continue;
        }

        if (!isFaceVisible(faceIndex, face, runtimeMapDeltaData(), eventRuntimeState))
        {
            continue;
        }

        const std::string normalizedTextureName = toLowerCopy(textureName);
        const int16_t sectorId =
            face.roomNumber < m_pIndoorMapData->sectors.size() ? static_cast<int16_t>(face.roomNumber) : int16_t(-1);
        const int16_t backSectorId =
            face.roomBehindNumber < m_pIndoorMapData->sectors.size()
                ? static_cast<int16_t>(face.roomBehindNumber)
                : int16_t(-1);
        uint32_t waterColorAbgr = 0;
        LiquidKind liquid = LiquidKind::None;
        const uint32_t attributes = runtimeMapDeltaData() && faceIndex < runtimeMapDeltaData()->faceAttributes.size()
            ? runtimeMapDeltaData()->faceAttributes[faceIndex] : face.attributes;
        // An open-sky map's sky faces are not drawn: the sky pass shows behind them (renderOpenSky).
        if (indoorFaceShowsOpenSky(m_openSky, attributes))
        {
            continue;
        }
        const auto materialTexture = texturesByName.find(normalizedTextureName);
        if (materialTexture != texturesByName.end() && materialTexture->second->waterColorAbgr != 0)
        {
            liquid = faceLiquidKind(attributes, materialTexture->second->liquid);
            waterColorAbgr = liquid != LiquidKind::None ? materialTexture->second->waterColorAbgr : 0;
        }
        // A lightmapped face batches with the faces of its page; every other face (and every face of a map without
        // baked lighting) takes page -1, as before. A door-moved face is lightmapped only when the bake has it (in the
        // BLV's stored pose) and it moves rigidly: its lightmap UVs are offset back to that pose.
        const bool mechanismFace = faceIndex < mechanismFaceMask.size() && mechanismFaceMask[faceIndex] != 0;
        const IndoorBakedFaceLightmap faceLightmap = IndoorBakedLighting::faceLightmap(
            m_pIndoorMapData->bakedLighting.get(), m_bakedLightingActive, faceIndex, face, mechanismFace,
            m_renderVertices, m_pIndoorMapData->vertices,
            faceIndex < rotatingFaceMotions.size() && rotatingFaceMotions[faceIndex]
                ? &*rotatingFaceMotions[faceIndex] : nullptr);
        // Terrain faces take the smooth daylight, not their lightmap (devdocs/INDOOR_OPEN_SKY.md "Terrain").
        const bool terrainFace = isTerrainFace(faceIndex);
        const bool singleMaterialTerrain = isSingleMaterialTerrainFace(faceIndex);
        const int32_t lightmapPage = terrainFace ? -1 : faceLightmap.page;
        // A translucent face is a batch of its own, sorted with the others each frame.
        const std::string batchKey = (pTranslucency != nullptr ? "T" + std::to_string(faceIndex) : std::string())
            + "#" + std::to_string(lightmapPage) + "#" + normalizedTextureName
            + "#" + std::to_string(sectorId)
            + "#" + std::to_string(backSectorId)
            + "#" + std::to_string(waterColorAbgr)
            + (singleMaterialTerrain ? "#S" : "");
        size_t batchIndex = 0;
        const std::unordered_map<std::string, size_t>::const_iterator batchIterator =
            batchIndicesByTexture.find(batchKey);

        if (batchIterator == batchIndicesByTexture.end())
        {
            TexturedBatch batch = {};
            batch.textureName = normalizedTextureName;
            batch.sectorId = sectorId;
            batch.backSectorId = backSectorId;
            batch.waterColorAbgr = waterColorAbgr;
            batch.liquid = liquid;
            batch.lightmapPage = lightmapPage;
            batch.daylit = indoorDaylightSector(m_daylight, sectorId);
            if (pTranslucency != nullptr)
            {
                batch.translucent = true;
                batch.translucency = *pTranslucency;
                IndoorFaceGeometryData geometry = {};
                if (buildIndoorFaceGeometry(*m_pIndoorMapData, m_renderVertices, faceIndex, geometry))
                {
                    batch.faceNormal = {geometry.normal.x, geometry.normal.y, geometry.normal.z};
                }
            }

            // Its draw group: the batches of every sector with the same draw state (a translucent face alone).
            const IndoorFaceDrawGroupKey groupKey = {normalizedTextureName, lightmapPage, waterColorAbgr,
                pTranslucency != nullptr ? int32_t(faceIndex) : -1, singleMaterialTerrain};
            const auto groupIterator = groupIndicesByKey.find(groupKey);
            if (groupIterator != groupIndicesByKey.end())
            {
                batch.drawGroup = uint32_t(groupIterator->second);
            }
            else
            {
                batch.drawGroup = uint32_t(m_texturedDrawGroups.size());
                groupIndicesByKey.emplace(groupKey, m_texturedDrawGroups.size());
                m_texturedDrawGroups.push_back(createTexturedDrawGroup(groupKey, textureName, previousGroups));
            }
            m_texturedDrawGroups[batch.drawGroup].terrain = terrainFace;

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

        TexturedBatch &batch = m_texturedBatches[batchIndex];
        TexturedDrawGroup &group = m_texturedDrawGroups[batch.drawGroup];
        group.textureWidth = pTexture->width;
        group.textureHeight = pTexture->height;
        const bool useBaseSubdivisionGeometry = mechanismFace;

        const uint64_t faceBuildBeginTickCount = SDL_GetTicksNS();
        TexturedFaceMesh faceMesh = buildFaceTexturedMesh(
            *m_pIndoorMapData,
            m_renderVertices,
            *pTexture,
            faceIndex,
            runtimeMapDeltaData(),
            eventRuntimeState,
            m_bakedStaticColoredLights,
            m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr,
            // A lightmapped face takes no static vertex light (nor its subdivision): its lightmap has it.
            lightmapPage >= 0 ? &noStaticLightSources : &bakedStaticLightSources,
            lightmapPage >= 0 ? &noStaticLightSources : &bakedStaticLightSubdivisionSources,
            useBaseSubdivisionGeometry,
            {},
            {},
            m_bakedStaticLightReach
        );
        texturedBuildNanoseconds += SDL_GetTicksNS() - faceBuildBeginTickCount;

        if (faceMesh.vertices.empty())
        {
            continue;
        }
        for (TexturedVertex &vertex : faceMesh.vertices)
        {
            vertex.daylight = batch.daylit ? 1.0f : 0.0f;
        }
        if (terrainFace)
        {
            applyTerrainVertices(faceIndex, faceMesh.vertices);
            // The terrain's vertex light for its grass (renderTerrainGrass): the doubled bake's luminance, as the shader
            // takes it, split into the lamps' share and the open air's lights' (alpha: 1 less their share).
            for (const TexturedVertex &vertex : faceMesh.vertices)
            {
                const uint32_t abgr = vertex.bakedLightAbgr;
                const float light = 2.0f / 255.0f
                    * (0.2126f * float(abgr & 0xffu) + 0.7152f * float((abgr >> 8) & 0xffu)
                        + 0.0722f * float((abgr >> 16) & 0xffu));
                const float openAirShare = 1.0f - float(abgr >> 24) / 255.0f;
                terrainLampLight += light * (1.0f - openAirShare);
                terrainOpenAirLight += light * openAirShare;
                ++terrainVertexCount;
            }
        }

        m_faceBatchIndices[faceIndex] = static_cast<int32_t>(batchIndex);
        m_faceVertexOffsets[faceIndex] = static_cast<uint32_t>(batch.vertices.size());
        m_faceVertexCounts[faceIndex] = static_cast<uint32_t>(faceMesh.vertices.size());
        const uint32_t vertexOffset = static_cast<uint32_t>(batch.vertices.size());
        for (uint32_t index : faceMesh.indices)
        {
            batch.indices.push_back(vertexOffset + index);
        }
        batch.vertices.insert(batch.vertices.end(), faceMesh.vertices.begin(), faceMesh.vertices.end());
        if (batch.lightmapPage >= 0)
        {
            const IndoorBakedLightingFace &bakedFace = m_pIndoorMapData->bakedLighting->faces[faceIndex];
            for (const TexturedVertex &vertex : faceMesh.vertices)
            {
                batch.lightmapUvs.push_back(faceLightmap.uvAt(bakedFace, vertex.x, vertex.y, vertex.z));
            }
        }
        if (useBaseSubdivisionGeometry)
        {
            m_faceSubdivisionTriangles[faceIndex] = std::move(faceMesh.triangles);
        }
    }

    m_terrainLampLight = terrainVertexCount > 0 ? float(terrainLampLight / double(terrainVertexCount)) : 0.0f;
    m_terrainOpenAirLight = terrainVertexCount > 0 ? float(terrainOpenAirLight / double(terrainVertexCount)) : 0.0f;

    // Each group's batches, one after another in its vertex buffer and index list.
    std::vector<std::vector<TexturedVertex>> groupVertices(m_texturedDrawGroups.size());
    std::vector<std::vector<std::array<float, 2>>> groupLightmapUvs(m_texturedDrawGroups.size());
    for (size_t batchIndex = 0; batchIndex < m_texturedBatches.size(); ++batchIndex)
    {
        TexturedBatch &batch = m_texturedBatches[batchIndex];
        batch.vertexCount = static_cast<uint32_t>(batch.vertices.size());
        batch.indexCount = static_cast<uint32_t>(batch.indices.size());
        rebuildTexturedBatchBounds(batch);
        std::vector<TexturedVertex> &vertices = groupVertices[batch.drawGroup];
        batch.groupVertexOffset = uint32_t(vertices.size());
        m_faceDrawPlan.addBatch(batch.drawGroup, uint32_t(batchIndex), batch.indices, batch.groupVertexOffset);
        vertices.insert(vertices.end(), batch.vertices.begin(), batch.vertices.end());
        if (batch.lightmapPage >= 0)
        {
            std::vector<std::array<float, 2>> &uvs = groupLightmapUvs[batch.drawGroup];
            uvs.insert(uvs.end(), batch.lightmapUvs.begin(), batch.lightmapUvs.end());
            std::vector<std::array<float, 2>>().swap(batch.lightmapUvs);
        }
        // The group has the indices; a liquid batch keeps its own for its water surfaces.
        if (batch.waterColorAbgr == 0)
        {
            std::vector<uint32_t>().swap(batch.indices);
        }
    }

    for (size_t groupIndex = 0; groupIndex < m_texturedDrawGroups.size(); ++groupIndex)
    {
        TexturedDrawGroup &group = m_texturedDrawGroups[groupIndex];
        const std::vector<TexturedVertex> &vertices = groupVertices[groupIndex];
        group.vertexCount = uint32_t(vertices.size());
        if (!updateDynamicVertexBuffer(group.vertexBufferHandle, group.vertexCapacity, vertices,
                TexturedVertex::ms_layout))
        {
            return false;
        }
        if (vertices.empty())
        {
            continue;
        }
        const std::vector<uint32_t> &indices = m_faceDrawPlan.groupIndices(uint32_t(groupIndex));
        group.indexBufferHandle = bgfx::createIndexBuffer(
            bgfx::copy(indices.data(), uint32_t(indices.size() * sizeof(uint32_t))), BGFX_BUFFER_INDEX32);
        if (!bgfx::isValid(group.indexBufferHandle))
        {
            return false;
        }
        if (group.key.lightmapPage >= 0)
        {
            const std::vector<std::array<float, 2>> &uvs = groupLightmapUvs[groupIndex];
            group.lightmapUvBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(uvs.data(), uint32_t(uvs.size() * sizeof(uvs[0]))), LightmapUvVertex::ms_layout);
            if (!bgfx::isValid(group.lightmapUvBufferHandle))
            {
                return false;
            }
        }
    }

    destroyTexturedDrawGroups(previousGroups);
    m_faceDrawBounds.assign(m_pIndoorMapData->faces.size(), {});
    m_faceDrawGrid.clear();
    std::vector<size_t> allFaces(m_pIndoorMapData->faces.size());
    std::iota(allFaces.begin(), allFaces.end(), size_t(0));
    addFaceDrawConflicts(allFaces);

    m_texturedBatchGeometryRevision = currentTexturedBatchGeometryRevision();
    {
        const std::optional<MapDeltaData> &builtDelta = runtimeMapDeltaData();
        const EventRuntimeState *pBuiltEvents = runtimeEventRuntimeState();
        m_builtFaceAttributes = builtDelta ? builtDelta->faceAttributes : std::vector<uint32_t>{};
        m_builtMapSurfaceRevision = builtDelta ? builtDelta->surfaceRevision : 0;
        m_builtEventSurfaceRevision = pBuiltEvents != nullptr ? pBuiltEvents->outdoorSurfaceRevision : 0;
        m_builtEventSurfaceSignature = currentEventSurfaceSignature();
    }
    m_bakedStaticLightRevision = currentBakedStaticLightRevision();
    m_bakedStaticLightEnabledStates =
        bakedStaticLightEnabledStates(*m_pIndoorMapData, runtimeEventRuntimeState(),
            m_indoorDecorationBillboardSet ? &*m_indoorDecorationBillboardSet : nullptr);
    m_bakedSectorAmbientLevels = bakedSectorAmbientLevels();
    return true;
}

std::vector<int16_t> IndoorRenderer::bakedSectorAmbientLevels() const
{
    std::vector<int16_t> levels(m_pIndoorMapData ? m_pIndoorMapData->sectors.size() : 0);
    for (size_t sectorId = 0; sectorId < levels.size(); ++sectorId)
    {
        levels[sectorId] =
            int16_t(IndoorLightingRuntime::sectorAmbientLevel(*m_pIndoorMapData, runtimeEventRuntimeState(), sectorId));
    }
    return levels;
}

void IndoorRenderer::rebuildBakedStaticLightReach()
{
    m_bakedStaticLightReach.clear();
    if (!m_pIndoorMapData)
    {
        return;
    }
    const IndoorMapData &mapData = *m_pIndoorMapData;
    const IndoorLightReach &reach = m_indoorLightingRuntime.lightReach();
    const size_t billboardCount =
        m_indoorDecorationBillboardSet ? m_indoorDecorationBillboardSet->billboards.size() : 0;
    m_bakedStaticLightReach.resize(mapData.lights.size() + billboardCount);
    std::vector<int16_t> reached;
    for (size_t lightId = 0; lightId < mapData.lights.size(); ++lightId)
    {
        // From the sector the light stands in (MM6 maps list most lights in most sectors).
        const BakedStaticLightSource source = bakedStaticLightSourceForIndoorLight(mapData, lightId);
        const int16_t sector = m_indoorLightingRuntime.mapLightSector(lightId);
        reach.reach(std::span<const int16_t>(&sector, 1), source.position, source.radius, reached);
        m_bakedStaticLightReach[lightId].assign(reached);
    }
    for (size_t index = 0; index < billboardCount; ++index)
    {
        const DecorationBillboard &billboard = m_indoorDecorationBillboardSet->billboards[index];
        // At the larger radius of its two toggle states, like the subdivision.
        if (const std::optional<BakedStaticLightSource> source = bakedStaticLightSourceForDecoration(
                *m_indoorDecorationBillboardSet, billboard, runtimeEventRuntimeState(), true))
        {
            reach.reach(std::span<const int16_t>(&billboard.sectorId, 1), source->position, source->radius, reached);
            m_bakedStaticLightReach[mapData.lights.size() + index].assign(reached);
        }
    }
}

bool IndoorRenderer::refreshBakedStaticLighting(
    bool refreshAllVertices,
    size_t &refreshedVertexCount,
    size_t &uploadedBatchCount)
{
    refreshedVertexCount = 0;
    uploadedBatchCount = 0;

    if (!m_pIndoorMapData)
    {
        return false;
    }

    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();
    std::vector<uint8_t> enabledStates =
        bakedStaticLightEnabledStates(*m_pIndoorMapData, pEventRuntimeState,
            m_indoorDecorationBillboardSet ? &*m_indoorDecorationBillboardSet : nullptr);
    std::vector<BakedStaticLightSource> changedLightSources;
    // Rooms whose ambient an event changed (evt.SetSectorAmbient) re-bake every vertex.
    std::vector<int16_t> sectorAmbientLevels = bakedSectorAmbientLevels();
    const bool ambientChanged = sectorAmbientLevels != m_bakedSectorAmbientLevels;
    const auto batchAmbientChanged = [&](const TexturedBatch &batch)
    {
        return ambientChanged && batch.sectorId >= 0 && size_t(batch.sectorId) < sectorAmbientLevels.size()
            && (size_t(batch.sectorId) >= m_bakedSectorAmbientLevels.size()
                || sectorAmbientLevels[size_t(batch.sectorId)] != m_bakedSectorAmbientLevels[size_t(batch.sectorId)]);
    };

    if (enabledStates.size() != m_bakedStaticLightEnabledStates.size())
    {
        refreshAllVertices = true;
    }
    else if (!refreshAllVertices)
    {
        for (size_t lightId = 0; lightId < enabledStates.size(); ++lightId)
        {
            if (enabledStates[lightId] == m_bakedStaticLightEnabledStates[lightId])
            {
                continue;
            }

            if (lightId < m_pIndoorMapData->lights.size())
            {
                changedLightSources.push_back(bakedStaticLightSourceForIndoorLight(*m_pIndoorMapData, lightId));
            }
            else if (m_indoorDecorationBillboardSet)
            {
                auto source = bakedStaticLightSourceForDecoration(*m_indoorDecorationBillboardSet,
                    m_indoorDecorationBillboardSet->billboards[lightId - m_pIndoorMapData->lights.size()],
                    pEventRuntimeState, true);
                if (source)
                {
                    source->sourceId = uint32_t(lightId);
                    changedLightSources.push_back(*source);
                }
            }
        }
    }

    if (!refreshAllVertices && changedLightSources.empty() && !ambientChanged)
    {
        m_bakedStaticLightEnabledStates = std::move(enabledStates);
        m_bakedStaticLightRevision = currentBakedStaticLightRevision();
        return true;
    }

    const std::vector<BakedStaticLightSource> activeLightSources =
        buildBakedStaticLightSources(
            *m_pIndoorMapData,
            pEventRuntimeState,
            m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr,
            false);

    // A light bakes into a batch only when it reaches one of the batch's sectors (its faces share them).
    const auto reachesBatch = [this](const BakedStaticLightSource &source, const TexturedBatch &batch)
    {
        if (source.sourceId >= m_bakedStaticLightReach.size())
        {
            return true;
        }
        return m_bakedStaticLightReach[source.sourceId].reachesReceiver(batch.sectorId, batch.backSectorId);
    };
    // `static_lights: {sides: front}`: the faces of each batch, whose vertex ranges take their own lights.
    std::vector<std::vector<size_t>> facesByBatch;
    if (m_pIndoorMapData->staticLightsFrontOnly)
    {
        facesByBatch.resize(m_texturedBatches.size());
        for (size_t faceIndex = 0; faceIndex < m_faceBatchIndices.size() && faceIndex < m_pIndoorMapData->faces.size();
            ++faceIndex)
        {
            const int32_t batchIndex = m_faceBatchIndices[faceIndex];
            if (batchIndex >= 0 && size_t(batchIndex) < facesByBatch.size())
            {
                facesByBatch[size_t(batchIndex)].push_back(faceIndex);
            }
        }
    }
    for (size_t batchIndex = 0; batchIndex < m_texturedBatches.size(); ++batchIndex)
    {
        TexturedBatch &batch = m_texturedBatches[batchIndex];
        // A lightmapped batch's static light is its lightmap, which no event changes.
        if (batch.lightmapPage >= 0)
        {
            continue;
        }
        // A sector open to the sky takes its ambient from the daylight (u_indoorDaylight), not the vertex bake.
        const float ambient = indoorDaylightSector(m_pIndoorMapData->daylight, batch.sectorId) ? 0.0f
            : batch.sectorId >= 0 && size_t(batch.sectorId) < sectorAmbientLevels.size()
            ? IndoorLightingRuntime::ambientFromMinAmbientLightLevel(sectorAmbientLevels[size_t(batch.sectorId)])
            : IndoorLightingRuntime::ambientFromMinAmbientLightLevel(0);
        const bool refreshBatchVertices = refreshAllVertices || batchAmbientChanged(batch);
        if (!refreshBatchVertices && batch.hasBounds)
        {
            bool batchAffectedByChangedLight = false;

            for (const BakedStaticLightSource &source : changedLightSources)
            {
                if (reachesBatch(source, batch) && pointAabbDistanceSquared(source.position, batch.boundsMin,
                        batch.boundsMax) <= source.radius * source.radius)
                {
                    batchAffectedByChangedLight = true;
                    break;
                }
            }

            if (!batchAffectedByChangedLight)
            {
                continue;
            }
        }

        const std::vector<BakedStaticLightSource> *pBatchActiveLightSources = &activeLightSources;
        std::vector<BakedStaticLightSource> batchActiveLightSources;

        if (batch.hasBounds)
        {
            batchActiveLightSources.reserve(activeLightSources.size());

            for (const BakedStaticLightSource &source : activeLightSources)
            {
                if (reachesBatch(source, batch) && pointAabbDistanceSquared(source.position, batch.boundsMin,
                        batch.boundsMax) <= source.radius * source.radius)
                {
                    batchActiveLightSources.push_back(source);
                }
            }

            pBatchActiveLightSources = &batchActiveLightSources;
        }
        else
        {
            for (const BakedStaticLightSource &source : activeLightSources)
            {
                if (reachesBatch(source, batch))
                {
                    batchActiveLightSources.push_back(source);
                }
            }
            pBatchActiveLightSources = &batchActiveLightSources;
        }

        bool batchChanged = false;
        // `static_lights: {sides: front}`: each face of the batch drops the lights behind it, as at build.
        std::vector<const std::vector<BakedStaticLightSource> *> vertexSources;
        std::vector<std::vector<BakedStaticLightSource>> faceSources;
        if (m_pIndoorMapData->staticLightsFrontOnly && batchIndex < facesByBatch.size())
        {
            vertexSources.assign(batch.vertices.size(), pBatchActiveLightSources);
            faceSources.reserve(facesByBatch[batchIndex].size());
            for (const size_t faceIndex : facesByBatch[batchIndex])
            {
                const std::optional<StaticLightFacePlane> plane =
                    staticLightFacePlane(*m_pIndoorMapData, m_renderVertices, m_pIndoorMapData->faces[faceIndex]);
                if (!plane)
                {
                    continue;
                }
                std::vector<BakedStaticLightSource> &sources = faceSources.emplace_back();
                for (const BakedStaticLightSource &source : *pBatchActiveLightSources)
                {
                    if (!staticLightBehindFace(source, *plane))
                    {
                        sources.push_back(source);
                    }
                }
                const size_t end = std::min<size_t>(
                    size_t(m_faceVertexOffsets[faceIndex]) + m_faceVertexCounts[faceIndex], vertexSources.size());
                for (size_t vertexIndex = m_faceVertexOffsets[faceIndex]; vertexIndex < end; ++vertexIndex)
                {
                    vertexSources[vertexIndex] = &sources;
                }
            }
        }

        for (size_t vertexIndex = 0; vertexIndex < batch.vertices.size(); ++vertexIndex)
        {
            TexturedVertex &vertex = batch.vertices[vertexIndex];
            if (!refreshBatchVertices)
            {
                const bx::Vec3 position = {vertex.x, vertex.y, vertex.z};
                bool affectedByChangedLight = false;

                for (const BakedStaticLightSource &source : changedLightSources)
                {
                    if (bakedStaticLightAffectsPoint(source, position))
                    {
                        affectedByChangedLight = true;
                        break;
                    }
                }

                if (!affectedByChangedLight)
                {
                    continue;
                }
            }

            ++refreshedVertexCount;
            const uint32_t bakedLightAbgr =
                bakedStaticLightAbgrForPoint(
                    vertexSources.empty() ? *pBatchActiveLightSources : *vertexSources[vertexIndex],
                    m_bakedStaticColoredLights,
                    ambient,
                    {vertex.x, vertex.y, vertex.z});

            if (vertex.bakedLightAbgr != bakedLightAbgr)
            {
                vertex.bakedLightAbgr = bakedLightAbgr;
                batchChanged = true;
            }
        }

        if (!batchChanged)
        {
            continue;
        }

        if (batch.drawGroup >= m_texturedDrawGroups.size()
            || !bgfx::isValid(m_texturedDrawGroups[batch.drawGroup].vertexBufferHandle))
        {
            return false;
        }

        bgfx::update(
            m_texturedDrawGroups[batch.drawGroup].vertexBufferHandle,
            batch.groupVertexOffset,
            bgfx::copy(
                batch.vertices.data(),
                static_cast<uint32_t>(batch.vertices.size() * sizeof(TexturedVertex))));
        ++uploadedBatchCount;
    }

    m_bakedStaticLightEnabledStates = std::move(enabledStates);
    m_bakedSectorAmbientLevels = std::move(sectorAmbientLevels);
    m_bakedStaticLightRevision = currentBakedStaticLightRevision();
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
    return updateMechanismFaceVertices(
        faceIndices,
        texturedBuildNanoseconds,
        uploadNanoseconds,
        pUpdatedFaceCount,
        pDirtyBatchCount);
}

bool IndoorRenderer::updateFaceAttributeChanges()
{
    constexpr size_t MaxChangedFaces = 512;
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (!m_pIndoorMapData || !mapDeltaData || m_texturedBatches.empty()
        || m_builtFaceAttributes.size() != mapDeltaData->faceAttributes.size())
    {
        return false;
    }

    // An event's surface change counts only when it changed what the batches read from the events: evt.SetFacetBit
    // bumps the event revision too, though its bits went into the map delta (a destructible's destroyed event hiding
    // a hint face rebuilt every batch of Sturmford, about 200 ms).
    const uint64_t eventSurfaceRevision = pEventRuntimeState != nullptr ? pEventRuntimeState->outdoorSurfaceRevision : 0;
    const bool eventSurfaceChanged = eventSurfaceRevision != m_builtEventSurfaceRevision;

    // Neither revision moved: a full rebuild was asked for (baked lighting switched).
    if (!eventSurfaceChanged && mapDeltaData->surfaceRevision == m_builtMapSurfaceRevision)
    {
        return false;
    }

    if (eventSurfaceChanged && currentEventSurfaceSignature() != m_builtEventSurfaceSignature)
    {
        return false;
    }

    std::vector<size_t> changedFaces;
    // The party's exploration marks faces seen as it goes (the map's reveal, no surface revision); nothing drawn
    // depends on it, and counting it made every break after a walk rebuild every batch.
    constexpr uint32_t UndrawnAttributes = faceAttributeBit(FaceAttribute::SeenByParty);

    for (size_t faceIndex = 0; faceIndex < m_builtFaceAttributes.size(); ++faceIndex)
    {
        if (((m_builtFaceAttributes[faceIndex] ^ mapDeltaData->faceAttributes[faceIndex]) & ~UndrawnAttributes) != 0)
        {
            changedFaces.push_back(faceIndex);

            if (changedFaces.size() > MaxChangedFaces)
            {
                return false;
            }
        }
    }

    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();
    std::vector<size_t> shownFaces;

    for (size_t faceIndex : changedFaces)
    {
        const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];
        const uint32_t before = m_builtFaceAttributes[faceIndex];
        const uint32_t after = mapDeltaData->faceAttributes[faceIndex];

        // A face turning into or out of an open-sky face changes what draws it: rebuild.
        if (indoorFaceShowsOpenSky(m_openSky, before) != indoorFaceShowsOpenSky(m_openSky, after))
        {
            return false;
        }

        const bool visible = isFaceVisible(faceIndex, face, mapDeltaData, eventRuntimeState);
        const int32_t batchIndex = faceIndex < m_faceBatchIndices.size() ? m_faceBatchIndices[faceIndex] : -1;

        if (batchIndex < 0)
        {
            if (visible)
            {
                return false;           // shown for the first time: it has no place in the batches yet
            }

            continue;
        }

        if (visible)
        {
            shownFaces.push_back(faceIndex);
            continue;
        }

        // Hidden: its triangles collapse onto one point (the draw keeps the face's place for when it shows again).
        TexturedBatch &batch = m_texturedBatches[static_cast<size_t>(batchIndex)];
        const uint32_t vertexOffset = m_faceVertexOffsets[faceIndex];
        const uint32_t vertexCount = m_faceVertexCounts[faceIndex];

        if (vertexCount == 0 || vertexOffset + vertexCount > batch.vertices.size())
        {
            continue;
        }

        std::vector<TexturedVertex> collapsed(
            batch.vertices.begin() + vertexOffset, batch.vertices.begin() + vertexOffset + vertexCount);

        for (TexturedVertex &vertex : collapsed)
        {
            vertex.x = collapsed.front().x;
            vertex.y = collapsed.front().y;
            vertex.z = collapsed.front().z;
        }

        bgfx::update(
            m_texturedDrawGroups[batch.drawGroup].vertexBufferHandle,
            batch.groupVertexOffset + vertexOffset,
            bgfx::copy(collapsed.data(), static_cast<uint32_t>(collapsed.size() * sizeof(TexturedVertex))));

        if (batch.waterColorAbgr != 0)
        {
            m_waterGeometryDirty = true;
        }
    }

    // Shown (again) or otherwise changed: rebuilt in place as a moving door's faces are.
    uint64_t buildNanoseconds = 0;
    uint64_t uploadNanoseconds = 0;

    if (!shownFaces.empty()
        && !updateMechanismFaceVertices(shownFaces, buildNanoseconds, uploadNanoseconds, nullptr, nullptr))
    {
        return false;
    }

    for (size_t faceIndex : changedFaces)
    {
        m_builtFaceAttributes[faceIndex] = mapDeltaData->faceAttributes[faceIndex];
    }

    m_builtMapSurfaceRevision = mapDeltaData->surfaceRevision;
    m_builtEventSurfaceRevision = eventSurfaceRevision;
    m_texturedBatchGeometryRevision = currentTexturedBatchGeometryRevision();
    return true;
}

bool IndoorRenderer::updateMechanismFaceVertices(
    const std::vector<size_t> &faceIndices,
    uint64_t &texturedBuildNanoseconds,
    uint64_t &uploadNanoseconds,
    size_t *pUpdatedFaceCount,
    size_t *pDirtyBatchCount
)
{
    if (!m_pIndoorMapData || !m_indoorTextureSet)
    {
        return false;
    }

    if (faceIndices.empty())
    {
        if (pUpdatedFaceCount != nullptr)
        {
            *pUpdatedFaceCount = 0;
        }

        if (pDirtyBatchCount != nullptr)
        {
            *pDirtyBatchCount = 0;
        }

        return true;
    }

    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();
    const std::vector<BakedStaticLightSource> bakedStaticLightSources =
        buildBakedStaticLightSources(
            *m_pIndoorMapData,
            eventRuntimeState ? &eventRuntimeState.value() : nullptr,
            m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr,
            false);
    // A lightmapped mover face takes no static vertex light: its lightmap (stored-pose UVs) moves with it.
    const std::vector<BakedStaticLightSource> noStaticLightSources;
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
            if (faceIndex >= m_pIndoorMapData->faces.size())
            {
                continue;
            }

            const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];
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
            const TexturedFaceMesh faceMesh = buildFaceTexturedMesh(
                *m_pIndoorMapData,
                m_renderVertices,
                *pTexture,
                faceIndex,
                runtimeMapDeltaData(),
                eventRuntimeState,
                m_bakedStaticColoredLights,
                m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr,
                &bakedStaticLightSources,
                nullptr,
                true,
                {},
                {},
                m_bakedStaticLightReach
            );
            texturedBuildNanoseconds += SDL_GetTicksNS() - faceBuildBeginTickCount;

            if (!faceMesh.vertices.empty())
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
        TexturedFaceMesh faceMesh = buildFaceTexturedMesh(
            *m_pIndoorMapData,
            m_renderVertices,
            *pTexture,
            faceIndex,
            runtimeMapDeltaData(),
            eventRuntimeState,
            m_bakedStaticColoredLights,
            m_indoorDecorationBillboardSet ? &m_indoorDecorationBillboardSet.value() : nullptr,
            batch.lightmapPage >= 0 ? &noStaticLightSources : &bakedStaticLightSources,
            nullptr,
            true,
            std::span<const TexturedVertex>(batch.vertices).subspan(vertexOffset, vertexCount),
            m_faceSubdivisionTriangles[faceIndex],
            m_bakedStaticLightReach
        );
        texturedBuildNanoseconds += SDL_GetTicksNS() - faceBuildBeginTickCount;

        if (faceMesh.vertices.size() != vertexCount)
        {
            std::cerr
                << "IndoorRenderer: moving mechanism face rebuild changed vertex count"
                << " face=" << faceIndex
                << " batch=" << batchIndex
                << " old=" << vertexCount
                << " new=" << faceMesh.vertices.size()
                << '\n';
            return false;
        }

        for (TexturedVertex &vertex : faceMesh.vertices)
        {
            vertex.daylight = batch.daylit ? 1.0f : 0.0f;
        }
        if (isTerrainFace(faceIndex))
        {
            applyTerrainVertices(faceIndex, faceMesh.vertices);
        }
        std::copy(faceMesh.vertices.begin(), faceMesh.vertices.end(), batch.vertices.begin() + vertexOffset);
        dirtyBatchBounds[static_cast<size_t>(batchIndex)] = 1;
        if (batch.translucent)
        {
            // A pane on a rotating mover turns: its one-sided test follows the face.
            const bx::Vec3 normal = computeFaceNormal(m_renderVertices, m_pIndoorMapData->faces[faceIndex]);
            if (vecDot(normal, normal) > 0.0001f)
            {
                const bx::Vec3 unitNormal = vecNormalize(normal);
                batch.faceNormal = {unitNormal.x, unitNormal.y, unitNormal.z};
            }
        }
        if (batch.waterColorAbgr != 0)
        {
            m_waterGeometryDirty = true;
        }
        ++updatedFaceCount;

        const uint64_t uploadBeginTickCount = SDL_GetTicksNS();
        bgfx::update(
            m_texturedDrawGroups[batch.drawGroup].vertexBufferHandle,
            batch.groupVertexOffset + vertexOffset,
            bgfx::copy(faceMesh.vertices.data(), static_cast<uint32_t>(faceMesh.vertices.size() * sizeof(TexturedVertex)))
        );
        uploadNanoseconds += SDL_GetTicksNS() - uploadBeginTickCount;
    }

    // A moved face may now touch faces it did not: those keep their draw order too.
    addFaceDrawConflicts(faceIndices);

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
    m_waterGeometryDirty = true;
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

    destroyTexturedDrawGroups(m_texturedDrawGroups);
    if (bgfx::isValid(m_mergedFaceIndexBufferHandle))
    {
        bgfx::destroy(m_mergedFaceIndexBufferHandle);
        m_mergedFaceIndexBufferHandle = BGFX_INVALID_HANDLE;
    }
    m_texturedBatches.clear();
    m_faceDrawPlan.clear();
    m_faceDrawBounds.clear();
    m_faceDrawGrid.clear();
    m_faceBatchIndices.clear();
    m_faceVertexOffsets.clear();
    m_faceVertexCounts.clear();
    m_faceSubdivisionTriangles.clear();
    m_texturedBatchGeometryRevision = std::numeric_limits<uint64_t>::max();
    m_bakedStaticLightRevision = std::numeric_limits<uint64_t>::max();
    m_bakedStaticLightEnabledStates.clear();
    m_bakedSectorAmbientLevels.clear();
}

void IndoorRenderer::destroyIndoorTextureHandles()
{
    for (IndoorTextureHandle &textureHandle : m_indoorTextureHandles)
    {
        for (bgfx::TextureHandle handle :
            {textureHandle.textureHandle, textureHandle.materialNormal, textureHandle.materialDetail})
        {
            if (bgfx::isValid(handle))
            {
                bgfx::destroy(handle);
            }
        }
    }

    m_indoorTextureHandles.clear();
}

bool IndoorRenderer::rebuildDerivedGeometryResources()
{
    if (!m_pIndoorMapData)
    {
        std::cerr << "IndoorRenderer: rebuildDerivedGeometryResources has no indoor map data\n";
        return false;
    }

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const std::optional<EventRuntimeState> &eventRuntimeState = runtimeEventRuntimeStateStorage();

    m_renderVertices = buildMechanismAdjustedVertices(*m_pIndoorMapData, mapDeltaData, eventRuntimeState);

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return true;
    }

    const std::vector<TerrainVertex> wireframeVertices =
        buildWireframeVertices(*m_pIndoorMapData, m_renderVertices, mapDeltaData, eventRuntimeState);
    const std::vector<TerrainVertex> portalVertices = buildPortalVertices(*m_pIndoorMapData, m_renderVertices);
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
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (!mapDeltaData || pEventRuntimeState == nullptr)
    {
        return false;
    }

    std::vector<uint32_t> doorIds;

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
            pEventRuntimeState->mechanisms.find(door.doorId);

        if (mechanismIterator != pEventRuntimeState->mechanisms.end() && mechanismIterator->second.isMoving)
        {
            doorIds.push_back(door.doorId);
        }
    }

    uint64_t texturedBuildNanoseconds = 0;
    uint64_t uploadNanoseconds = 0;
    return updateMechanismGeometryResourcesForDoorIds(doorIds, texturedBuildNanoseconds, uploadNanoseconds);
}

bool IndoorRenderer::updateMechanismGeometryResourcesForDoorIds(
    const std::vector<uint32_t> &doorIds,
    uint64_t &texturedBuildNanoseconds,
    uint64_t &uploadNanoseconds,
    size_t *pUpdatedFaceCount,
    size_t *pDirtyBatchCount)
{
    if (!m_pIndoorMapData)
    {
        return false;
    }

    if (doorIds.empty())
    {
        return true;
    }

    const bool collectDiagnostics = m_logIndoorPerformanceDiagnostics;
    const uint64_t renderVerticesBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;

    if (!updateMechanismRenderVerticesForDoorIds(doorIds))
    {
        return false;
    }

    if (collectDiagnostics)
    {
        m_indoorPerformanceDiagnostics.movingRenderVerticesNanoseconds +=
            SDL_GetTicksNS() - renderVerticesBeginTickCount;
    }

    if (bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        clearPortalVisibilityCaches();
        ++m_inspectGeometryRevision;
        m_cachedInspectHitValid = false;
        return true;
    }

    // Face bits changed with the move (a destructible broke and its event opened a door): in place where they can be.
    if (!m_indoorTextureSet || (texturedBatchesNeedFullRebuild() && !updateFaceAttributeChanges()))
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

    size_t updatedFaceCount = 0;
    size_t dirtyBatchCount = 0;
    size_t *pActualUpdatedFaceCount = pUpdatedFaceCount != nullptr ? pUpdatedFaceCount : &updatedFaceCount;
    size_t *pActualDirtyBatchCount = pDirtyBatchCount != nullptr ? pDirtyBatchCount : &dirtyBatchCount;
    const uint64_t faceUpdateBeginTickCount = collectDiagnostics ? SDL_GetTicksNS() : 0;
    const std::vector<size_t> faceIndices = collectMechanismFaceIndicesForDoorIds(doorIds);

    if (!updateMechanismFaceVertices(
            faceIndices,
            texturedBuildNanoseconds,
            uploadNanoseconds,
            pActualUpdatedFaceCount,
            pActualDirtyBatchCount))
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
        m_indoorPerformanceDiagnostics.movingUpdatedFaces += *pActualUpdatedFaceCount;
        m_indoorPerformanceDiagnostics.movingDirtyBatches += *pActualDirtyBatchCount;
    }

    clearPortalVisibilityCaches();
    ++m_inspectGeometryRevision;
    m_cachedInspectHitValid = false;
    return true;
}

bool IndoorRenderer::updateMovingMechanismRenderVertices()
{
    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (!mapDeltaData || pEventRuntimeState == nullptr)
    {
        return false;
    }

    std::vector<uint32_t> doorIds;

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
            pEventRuntimeState->mechanisms.find(door.doorId);

        if (mechanismIterator != pEventRuntimeState->mechanisms.end() && mechanismFacesMoving(mechanismIterator->second))
        {
            doorIds.push_back(door.doorId);
        }
    }

    return updateMechanismRenderVerticesForDoorIds(doorIds);
}

bool IndoorRenderer::updateMechanismRenderVerticesForDoorIds(const std::vector<uint32_t> &doorIds)
{
    if (!m_pIndoorMapData)
    {
        return false;
    }

    const std::optional<MapDeltaData> &mapDeltaData = runtimeMapDeltaData();
    const EventRuntimeState *pEventRuntimeState = runtimeEventRuntimeState();

    if (m_renderVertices.size() != m_pIndoorMapData->vertices.size())
    {
        m_renderVertices = buildIndoorMechanismAdjustedVertices(
            *m_pIndoorMapData,
            mapDeltaData ? &mapDeltaData.value() : nullptr,
            pEventRuntimeState);
        return true;
    }

    if (!mapDeltaData || pEventRuntimeState == nullptr || doorIds.empty())
    {
        return true;
    }

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        if (std::find(doorIds.begin(), doorIds.end(), door.doorId) == doorIds.end())
        {
            continue;
        }

        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
            pEventRuntimeState->mechanisms.find(door.doorId);
        RuntimeMechanismState baseMechanism = {};
        baseMechanism.state = door.state;
        baseMechanism.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
        baseMechanism.currentDistance = EventRuntime::calculateMechanismDistance(door, baseMechanism);

        const RuntimeMechanismState &mechanism =
            mechanismIterator != pEventRuntimeState->mechanisms.end() ? mechanismIterator->second : baseMechanism;
        applyIndoorMechanismDoorToVertices(
            door,
            findIndoorMoverDefinition(*m_pIndoorMapData, door.doorId),
            mechanism.currentDistance,
            mechanism.rotationDirection,
            m_renderVertices,
            mechanism.spinDegrees);
    }

    return true;
}

bool IndoorRenderer::tryActivateInspectEvent(const InspectHit &inspectHit)
{
    if (!m_pIndoorMapData || m_pSceneRuntime == nullptr)
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
        && m_pIndoorMapData)
    {
        const std::optional<IndoorInteractiveDecorationBinding> binding =
            resolveIndoorInteractiveDecorationBinding(
                m_indoorInteractiveDecorationDecorVarIndicesByEntity,
                m_indoorInteractiveDecorationBaseEventIdsByEntity,
                m_indoorInteractiveDecorationEventCountsByEntity,
                m_indoorInteractiveDecorationHideWhenClearedByEntity,
                m_indoorInteractiveDecorationFixedEventByEntity,
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

    if (eventId == 0 && inspectHit.kind != "entity")
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

IndoorRenderer::TexturedFaceMesh IndoorRenderer::buildFaceTexturedMesh(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &transformedVertices,
    const OutdoorBitmapTexture &texture,
    size_t faceIndex,
    const std::optional<MapDeltaData> &indoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    bool coloredLights,
    const DecorationBillboardSet *pDecorationBillboardSet,
    const std::vector<BakedStaticLightSource> *pBakedStaticLightSources,
    const std::vector<BakedStaticLightSource> *pBakedStaticLightSubdivisionSources,
    bool useBaseSubdivisionGeometry,
    std::span<const TexturedVertex> subdivisionTemplate,
    std::span<const TexturedFaceTriangle> triangleTemplate,
    std::span<const IndoorLightReachList> sourceReach
)
{
    TexturedFaceMesh mesh;

    if (faceIndex >= indoorMapData.faces.size())
    {
        return mesh;
    }

    const IndoorFace &face = indoorMapData.faces[faceIndex];
    const uint32_t effectiveAttributes =
        indoorMapDeltaData && faceIndex < indoorMapDeltaData->faceAttributes.size()
            ? indoorMapDeltaData->faceAttributes[faceIndex]
            : face.attributes;
    const std::string effectiveTextureName = resolveFaceTextureName(faceIndex, face, eventRuntimeState);

    if (face.isPortal || effectiveTextureName.empty() || face.vertexIndices.size() < 3)
    {
        return mesh;
    }

    if (!isFaceVisible(faceIndex, face, indoorMapDeltaData, eventRuntimeState))
    {
        return mesh;
    }

    if (toLowerCopy(effectiveTextureName) != toLowerCopy(texture.textureName))
    {
        return mesh;
    }

    std::vector<BakedStaticLightSource> localBakedStaticLightSources;
    std::vector<BakedStaticLightSource> localBakedStaticLightSubdivisionSources;

    if (pBakedStaticLightSources == nullptr)
    {
        localBakedStaticLightSources =
            buildBakedStaticLightSources(
                indoorMapData,
                eventRuntimeState ? &eventRuntimeState.value() : nullptr,
                pDecorationBillboardSet,
                false);
        pBakedStaticLightSources = &localBakedStaticLightSources;
    }

    if (pBakedStaticLightSubdivisionSources == nullptr && triangleTemplate.empty())
    {
        localBakedStaticLightSubdivisionSources =
            buildBakedStaticLightSources(
                indoorMapData,
                eventRuntimeState ? &eventRuntimeState.value() : nullptr,
                pDecorationBillboardSet,
                true);
        pBakedStaticLightSubdivisionSources = &localBakedStaticLightSubdivisionSources;
    }

    if (pBakedStaticLightSubdivisionSources == nullptr)
    {
        pBakedStaticLightSubdivisionSources = &localBakedStaticLightSubdivisionSources;
    }

    // A face's descendants stay inside its bounds. Cull unrelated sources once before sampling or subdivision.
    bx::Vec3 faceMin = {
        std::numeric_limits<float>::infinity(),
        std::numeric_limits<float>::infinity(),
        std::numeric_limits<float>::infinity()
    };
    bx::Vec3 faceMax = {-faceMin.x, -faceMin.y, -faceMin.z};
    bx::Vec3 subdivisionMin = faceMin;
    bx::Vec3 subdivisionMax = faceMax;
    // Door-linked walls can deform. Their base geometry fixes triangulation and the split tree throughout motion.
    const std::vector<IndoorVertex> &subdivisionVertices =
        useBaseSubdivisionGeometry ? indoorMapData.vertices : transformedVertices;
    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= transformedVertices.size() || vertexIndex >= subdivisionVertices.size())
        {
            return mesh;
        }

        const IndoorVertex &vertex = transformedVertices[vertexIndex];
        faceMin.x = std::min(faceMin.x, static_cast<float>(vertex.x));
        faceMin.y = std::min(faceMin.y, static_cast<float>(vertex.y));
        faceMin.z = std::min(faceMin.z, static_cast<float>(vertex.z));
        faceMax.x = std::max(faceMax.x, static_cast<float>(vertex.x));
        faceMax.y = std::max(faceMax.y, static_cast<float>(vertex.y));
        faceMax.z = std::max(faceMax.z, static_cast<float>(vertex.z));
        const bx::Vec3 subdivisionPosition = indoorVertexToWorld(subdivisionVertices[vertexIndex]);
        subdivisionMin = bx::min(subdivisionMin, subdivisionPosition);
        subdivisionMax = bx::max(subdivisionMax, subdivisionPosition);
    }

    // 2 in the vertex's secret-pulse slot (1 marks a secret face): the scene's `opaque_faces` ignore the texture's alpha.
    const float opaqueFlag = isIndoorFaceOpaque(indoorMapData, faceIndex) ? 2.0f : 0.0f;
    // The receiving room: only lights that reach the face's sectors through portals bake into it (no light through
    // the walls between rooms), and its own ambient.
    const int16_t faceSector =
        face.roomNumber < indoorMapData.sectors.size() ? int16_t(face.roomNumber) : int16_t(-1);
    const int16_t faceBackSector =
        face.roomBehindNumber < indoorMapData.sectors.size() ? int16_t(face.roomBehindNumber) : int16_t(-1);
    // A sector open to the sky takes its ambient from the daylight (u_indoorDaylight), not the vertex bake.
    const float faceAmbient = indoorDaylightSector(indoorMapData.daylight, faceSector) ? 0.0f
        : faceSector >= 0
        ? IndoorLightingRuntime::ambientFromMinAmbientLightLevel(IndoorLightingRuntime::sectorAmbientLevel(
            indoorMapData, eventRuntimeState ? &*eventRuntimeState : nullptr, size_t(faceSector)))
        : IndoorLightingRuntime::ambientFromMinAmbientLightLevel(0);
    const std::optional<StaticLightFacePlane> frontPlane =
        staticLightFacePlane(indoorMapData, transformedVertices, face);
    const auto sourcesForFace = [&](const std::vector<BakedStaticLightSource> &sources,
        const bx::Vec3 &minBounds, const bx::Vec3 &maxBounds)
    {
        std::vector<BakedStaticLightSource> result;
        for (const BakedStaticLightSource &source : sources)
        {
            if (source.radius > 0.0f
                && pointAabbDistanceSquared(source.position, minBounds, maxBounds) <= source.radius * source.radius
                && (source.sourceId >= sourceReach.size()
                    || sourceReach[source.sourceId].reachesReceiver(faceSector, faceBackSector))
                && !(frontPlane && staticLightBehindFace(source, *frontPlane)))
            {
                result.push_back(source);
            }
        }
        return result;
    };
    const std::vector<BakedStaticLightSource> faceBakedStaticLightSources =
        sourcesForFace(*pBakedStaticLightSources, faceMin, faceMax);
    const std::vector<BakedStaticLightSource> faceBakedStaticLightSubdivisionSources =
        sourcesForFace(*pBakedStaticLightSubdivisionSources, subdivisionMin, subdivisionMax);
    pBakedStaticLightSources = &faceBakedStaticLightSources;
    pBakedStaticLightSubdivisionSources = &faceBakedStaticLightSubdivisionSources;

    bx::Vec3 faceNormal = computeFaceNormal(transformedVertices, face);
    if (useBaseSubdivisionGeometry && vecDot(faceNormal, faceNormal) <= 0.0001f && face.planeNormal)
    {
        // A closed door's side face can collapse to an edge. Retain its authored plane and vertices for reopening.
        faceNormal = {
            static_cast<float>((*face.planeNormal)[0]),
            static_cast<float>((*face.planeNormal)[1]),
            static_cast<float>((*face.planeNormal)[2])
        };
    }
    const std::array<float, 4> flowInfo =
        indoorFaceFlowInfo(effectiveAttributes, face.facetType, texture.width, texture.height);
    const float textureCoordinateScale = indoorFaceTextureCoordinateScale(effectiveAttributes, face.facetType);

    const std::optional<MechanismFaceTextureState> mechanismFaceTextureState =
        findMechanismFaceTextureState(faceIndex, indoorMapDeltaData, eventRuntimeState);
    const bool useGeometryTextureCoordinates =
        mechanismFaceTextureState
        && !mechanismFaceKeepsStoredTexels(indoorMapData, face, *mechanismFaceTextureState->pDoor);
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
            return mesh;
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
                return mesh;
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

    if (!triangleTemplate.empty())
    {
        for (const TexturedFaceTriangle &triangle : triangleTemplate)
        {
            triangleVertexOrders.push_back(triangle.faceVertexIndices);
        }
    }
    else if (!triangulateFaceProjected(subdivisionVertices, face, triangleVertexOrders))
    {
        for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
        {
            triangleVertexOrders.push_back({0, triangleIndex, triangleIndex + 1});
        }
    }

    for (size_t triangleIndex = 0; triangleIndex < triangleVertexOrders.size(); ++triangleIndex)
    {
        const std::array<size_t, 3> &triangleVertexIndices = triangleVertexOrders[triangleIndex];
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
            texturedVertex.secretPulse = secretFaceVertexFlag(effectiveAttributes) + opaqueFlag;
            texturedVertex.barycentric0 = triangleVertexSlot == 0 ? 1.0f : 0.0f;
            texturedVertex.barycentric1 = triangleVertexSlot == 1 ? 1.0f : 0.0f;
            texturedVertex.barycentric2 = triangleVertexSlot == 2 ? 1.0f : 0.0f;
            texturedVertex.boundaryEdgeMask = boundaryEdgeMask;
            texturedVertex.flowUPerSecond = flowInfo[0];
            texturedVertex.flowVPerSecond = flowInfo[1];
            texturedVertex.lavaFlow = flowInfo[2];
            texturedVertex.fluidFlow = flowInfo[3];
            texturedVertex.bakedLightAbgr =
                bakedStaticLightAbgrForPoint(
                    *pBakedStaticLightSources,
                    coloredLights,
                    faceAmbient,
                    {texturedVertex.x, texturedVertex.y, texturedVertex.z});

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
        std::array<float, 3> gradientU = {};
        std::array<float, 3> gradientV = {};
        surfaceTextureGradients(
            {bx::Vec3{triangleVertices[0].x, triangleVertices[0].y, triangleVertices[0].z},
                bx::Vec3{triangleVertices[1].x, triangleVertices[1].y, triangleVertices[1].z},
                bx::Vec3{triangleVertices[2].x, triangleVertices[2].y, triangleVertices[2].z}},
            {{{triangleVertices[0].u, triangleVertices[0].v}, {triangleVertices[1].u, triangleVertices[1].v},
                {triangleVertices[2].u, triangleVertices[2].v}}},
            gradientU, gradientV);
        for (TexturedVertex &triangleVertex : triangleVertices)
        {
            triangleVertex.gradientU = gradientU;
            triangleVertex.gradientV = gradientV;
        }

        std::array<bx::Vec3, 3> subdivisionPositions = {
            bx::Vec3{0.0f, 0.0f, 0.0f}, bx::Vec3{0.0f, 0.0f, 0.0f}, bx::Vec3{0.0f, 0.0f, 0.0f}
        };
        for (size_t slot = 0; slot < 3; ++slot)
        {
            subdivisionPositions[slot] =
                indoorVertexToWorld(subdivisionVertices[face.vertexIndices[triangleVertexIndices[slot]]]);
        }
        const bx::Vec3 triangleEdge1 = bx::sub(subdivisionPositions[1], subdivisionPositions[0]);
        const bx::Vec3 triangleEdge2 = bx::sub(subdivisionPositions[2], subdivisionPositions[0]);
        const bx::Vec3 triangleNormal = vecCross(triangleEdge1, triangleEdge2);

        if (!useBaseSubdivisionGeometry && vecDot(triangleNormal, triangleNormal) <= 0.0001f)
        {
            continue;
        }

        TexturedFaceTriangle triangle = {};
        triangle.faceVertexIndices = triangleVertexIndices;
        triangle.vertexOffset = static_cast<uint32_t>(mesh.vertices.size());
        if (!triangleTemplate.empty())
        {
            // Reuse the split weights during motion; light curvature and topology were already baked at map load.
            const TexturedFaceTriangle &previousTriangle = triangleTemplate[triangleIndex];
            const std::span<const TexturedVertex> previousVertices =
                subdivisionTemplate.subspan(previousTriangle.vertexOffset, previousTriangle.vertexCount);
            for (const TexturedVertex &previousVertex : previousVertices)
            {
                TexturedVertex vertex = previousVertex;
                const float first = vertex.barycentric0;
                const float second = vertex.barycentric1;
                const float third = vertex.barycentric2;
                const TexturedVertex &a = triangleVertices[0];
                const TexturedVertex &b = triangleVertices[1];
                const TexturedVertex &c = triangleVertices[2];
                vertex.x = a.x * first + b.x * second + c.x * third;
                vertex.y = a.y * first + b.y * second + c.y * third;
                vertex.z = a.z * first + b.z * second + c.z * third;
                vertex.u = a.u * first + b.u * second + c.u * third;
                vertex.v = a.v * first + b.v * second + c.v * third;
                vertex.secretPulse = a.secretPulse;
                vertex.boundaryEdgeMask = a.boundaryEdgeMask;
                vertex.flowUPerSecond = a.flowUPerSecond;
                vertex.flowVPerSecond = a.flowVPerSecond;
                vertex.lavaFlow = a.lavaFlow;
                vertex.fluidFlow = a.fluidFlow;
                vertex.gradientU = a.gradientU;
                vertex.gradientV = a.gradientV;
                refreshBakedStaticLight(*pBakedStaticLightSources, coloredLights, faceAmbient, vertex);
                mesh.vertices.push_back(vertex);
            }
        }
        else
        {
            std::unordered_map<uint64_t, uint32_t> vertexIndices;
            appendBakedStaticLightSubdividedTriangle(
                mesh,
                vertexIndices,
                *pBakedStaticLightSources,
                *pBakedStaticLightSubdivisionSources,
                coloredLights,
                faceAmbient,
                triangleVertices,
                subdivisionPositions,
                0);
        }
        triangle.vertexCount = static_cast<uint32_t>(mesh.vertices.size()) - triangle.vertexOffset;
        mesh.triangles.push_back(triangle);
    }

    // The face's sector and back sector, for the dynamic lights' portal reach (the batches of a draw group mix them).
    const std::array<float, 2> sectors = {
        face.roomNumber < indoorMapData.sectors.size() ? float(face.roomNumber) : -1.0f,
        face.roomBehindNumber < indoorMapData.sectors.size() ? float(face.roomBehindNumber) : -1.0f};
    for (TexturedVertex &vertex : mesh.vertices)
    {
        vertex.sectors = sectors;
    }
    return mesh;
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

        if (face.isPortal || hasFaceAttribute(effectiveAttributes, FaceAttribute::IsPortal)
            || indoorFacePassesPicks(indoorMapData, faceIndex, face.cogTriggered, effectiveAttributes))
        {
            continue;
        }

        // a standing destructible's invisible hit box takes blows (MM9 RayHit)
        if ((hasFaceAttribute(effectiveAttributes, FaceAttribute::Invisible)
                || !isFaceVisible(faceIndex, face, mapDeltaData, eventRuntimeState))
            && !indoorDestructibleHitFace(*m_pIndoorMapData, faceIndex, effectiveAttributes))
        {
            continue;
        }

        if (!visibleSectorMask.empty()
            && !isSectorVisible(static_cast<int16_t>(face.roomNumber), visibleSectorMask)
            && !isSectorVisible(static_cast<int16_t>(face.roomBehindNumber), visibleSectorMask))
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

    // Entities drawn by a 3D decoration model pick through its triangles below, not this coarse box.
    std::vector<uint8_t> entityHasModel(indoorMapData.entities.size(), 0);
    if (m_indoorDecorationBillboardSet && !m_decorationModels.empty())
    {
        const std::vector<DecorationBillboard> &billboards = m_indoorDecorationBillboardSet->billboards;
        for (size_t index = 0; index < billboards.size(); ++index)
        {
            if (billboards[index].entityIndex < entityHasModel.size() && m_decorationModels.drawsBillboard(index))
            {
                entityHasModel[billboards[index].entityIndex] = 1;
            }
        }
    }

    for (size_t entityIndex = 0; entityIndex < indoorMapData.entities.size(); ++entityIndex)
    {
        const IndoorEntity &entity = indoorMapData.entities[entityIndex];
        if (entityHasModel[entityIndex] != 0)
        {
            continue;
        }
        const std::optional<IndoorInteractiveDecorationBinding> binding =
            eventRuntimeState
                ? resolveIndoorInteractiveDecorationBinding(
                    m_indoorInteractiveDecorationDecorVarIndicesByEntity,
                    m_indoorInteractiveDecorationBaseEventIdsByEntity,
                    m_indoorInteractiveDecorationEventCountsByEntity,
                    m_indoorInteractiveDecorationHideWhenClearedByEntity,
                    m_indoorInteractiveDecorationFixedEventByEntity,
                    entityIndex)
                : std::nullopt;

        if (binding
            && interactiveDecorationIsCleared(
                eventRuntimeState->decorVars[binding->decorVarIndex],
                binding->eventCount,
                binding->hideWhenCleared))
        {
            continue;
        }

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
                return texture.opacityMask.isOpaqueNormalized(normalizedU, normalizedV);
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

                if (m_pIndoorMapData && m_indoorDecorationBillboardSet
                    && indoorDecorationLightToggleTarget(*m_pIndoorMapData,
                        m_indoorDecorationBillboardSet->decorationTable, billboard.entityIndex,
                        &*eventRuntimeState) != nullptr)
                {
                    return true;
                }

                return resolveIndoorInteractiveDecorationBinding(
                    m_indoorInteractiveDecorationDecorVarIndicesByEntity,
                    m_indoorInteractiveDecorationBaseEventIdsByEntity,
                    m_indoorInteractiveDecorationEventCountsByEntity,
                    m_indoorInteractiveDecorationHideWhenClearedByEntity,
                    m_indoorInteractiveDecorationFixedEventByEntity,
                    billboard.entityIndex).has_value();
            };

        const auto decorationHasHint =
            [this](const DecorationBillboard &billboard)
            {
                const DecorationLookupResult decoration =
                    m_indoorDecorationBillboardSet->decorationTable.resolveMapDecoration(
                        billboard.decorationId,
                        billboard.name);
                const DecorationEntry *pDecoration = decoration.pEntry;

                return pDecoration != nullptr && !pDecoration->hint.empty();
            };

        // The sprite's opaque pixels under the ray, on its camera-facing plane.
        const auto decorationSpriteHit =
            [&](const DecorationBillboard &billboard, uint16_t spriteId, float &distance) -> bool
            {
                const uint32_t animationOffsetTicks =
                    animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
                const SpriteFrameEntry *pFrame =
                    m_indoorDecorationBillboardSet->spriteFrameTable.getFrame(spriteId, animationOffsetTicks);

                if (pFrame == nullptr)
                {
                    return false;
                }

                const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
                const float angleToCamera = std::atan2(
                    static_cast<float>(billboard.y) - m_cameraPositionY,
                    static_cast<float>(billboard.x) - m_cameraPositionX);
                const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
                const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
                const BillboardTextureHandle *pTexture =
                    findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);

                if (pTexture == nullptr || pTexture->width <= 0 || pTexture->height <= 0)
                {
                    return false;
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
                    return false;
                }

                distance = vecDot(vecSubtract(center, rayOrigin), planeNormal) / denominator;

                if (distance <= InspectRayEpsilon
                    || (distance >= bestDistance && (bestHit.kind != "face" || distance > bestDistance + 8.0f)))
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

                if (!isOpaqueBillboardPixel(*pTexture, normalizedU, normalizedV))
                {
                    return false;
                }

                return true;
            };

        for (size_t billboardIndex = 0; billboardIndex < m_indoorDecorationBillboardSet->billboards.size();
             ++billboardIndex)
        {
            const DecorationBillboard &billboard = m_indoorDecorationBillboardSet->billboards[billboardIndex];
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

            float distance = 0.0f;
            if (m_decorationModels.drawsBillboard(billboardIndex))
            {
                // The model's own triangles, as precise as the sprite's opaque pixels were.
                if (!m_decorationModels.raycast(billboardIndex, {rayOrigin.x, rayOrigin.y, rayOrigin.z},
                        {rayDirection.x, rayDirection.y, rayDirection.z}, distance)
                    || distance <= InspectRayEpsilon
                    || (distance >= bestDistance && (bestHit.kind != "face" || distance > bestDistance + 8.0f)))
                {
                    continue;
                }
            }
            else if (!decorationSpriteHit(billboard, spriteId, distance))
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
                return texture.opacityMask.isOpaqueNormalized(normalizedU, normalizedV);
            };

        const auto hitTestActorBillboard =
            [&](const RuntimeActorBillboard &actor, float &distance, bool &billboardTested) -> bool
            {
                billboardTested = false;
                // A model or loot satchel owns picking; an empty one (a sunk corpse without loot) is not picked.
                const Engine::ModelBounds *pBounds = m_worldFxSystem.actorModelCullingBounds(actor.actorIndex);
                if (pBounds != nullptr)
                {
                    billboardTested = true;
                    if (!pBounds->valid || !intersectRayAabb(rayOrigin, rayDirection,
                        {pBounds->min[0], pBounds->min[1], pBounds->min[2]},
                        {pBounds->max[0], pBounds->max[1], pBounds->max[2]}, distance))
                    {
                        return false;
                    }
                    pBounds = m_worldFxSystem.actorModelPoseBounds(actor.actorIndex);
                    if (!pBounds->valid || !intersectRayAabb(rayOrigin, rayDirection,
                        {pBounds->min[0], pBounds->min[1], pBounds->min[2]},
                        {pBounds->max[0], pBounds->max[1], pBounds->max[2]}, distance))
                    {
                        return false;
                    }
                    // The boxes only gate the triangle test: a click between a wing and the body misses.
                    const std::optional<float> modelDistance = m_worldFxSystem.actorModelPickRay(actor.actorIndex,
                        {rayOrigin.x, rayOrigin.y, rayOrigin.z}, {rayDirection.x, rayDirection.y, rayDirection.z});
                    if (!modelDistance)
                    {
                        return false;
                    }
                    distance = *modelDistance;
                    return true;
                }

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
                const bx::Vec3 center = spriteBillboardCenter(
                    static_cast<float>(actor.x),
                    static_cast<float>(actor.y),
                    static_cast<float>(actor.z),
                    cameraRight, cameraUp, *pTexture, spriteScale, resolvedTexture.mirrored);
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
                return texture.opacityMask.isOpaqueNormalized(normalizedU, normalizedV);
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

                    if (!isFaceVisible(faceIndex, face, mapDeltaData, eventRuntimeState))
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
                bestHit.containedItemId = object.containedItemId;
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

            if (object.containedItemId != 0 && m_pItemTable != nullptr)
            {
                // An item is its model: the model's box, turned as it lies (GROUND_ITEMS_3D_BEHAVIOUR.md section 5), or
                // as its authored pose turns it (a placed item leaning on a wall).
                const std::optional<MapDeltaData> &deltaForPose = runtimeMapDeltaData();
                const std::optional<std::array<float, 3>> pose =
                    deltaForPose && object.objectIndex < deltaForPose->spriteObjects.size()
                        ? deltaForPose->spriteObjects[object.objectIndex].semanticPose
                        : std::nullopt;
                const std::optional<float> itemDistance = pose
                    ? intersectPosedWorldItemPickBox(
                        m_pItemTable->groundModel(object.containedItemId),
                        WorldItemPose{(*pose)[0], (*pose)[1], (*pose)[2]},
                        {float(object.x), float(object.y), float(object.z)},
                        {rayOrigin.x, rayOrigin.y, rayOrigin.z},
                        {rayDirection.x, rayDirection.y, rayDirection.z})
                    : intersectWorldItemPickBox(
                        m_pItemTable->groundModel(object.containedItemId),
                        worldItemYawRadians(object.objectKey),
                        {float(object.x), float(object.y), float(object.z)},
                        {rayOrigin.x, rayOrigin.y, rayOrigin.z},
                        {rayDirection.x, rayDirection.y, rayDirection.z});

                if (itemDistance && (*itemDistance < bestDistance || bestHit.kind == "face"))
                {
                    applyObjectHit(object, *itemDistance);
                }

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
    if (!input.turnBasedMovementStep)
    {
        deltaSeconds = std::min(deltaSeconds, 0.05f);
    }

    const float cameraDeltaSeconds = std::min(input.cameraDeltaSeconds.value_or(deltaSeconds), 0.05f);
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
    const bool turboPressed = input.turboMovementHeld();
    const bool jumpPressed = input.action(KeyboardAction::Jump).held;
    // A held jump key jumps again on landing, as the original's continuous trigger does (OY-219); on a ladder or in
    // water only a fresh press acts (letting go of the ladder, swimming up).
    const IndoorPartyRuntime *pJumpPartyRuntime =
        m_pSceneRuntime != nullptr ? &m_pSceneRuntime->partyRuntime() : nullptr;
    const bool jumpHeldOnGround = m_jumpHeld && pJumpPartyRuntime != nullptr
        && pJumpPartyRuntime->movementState().grounded && !pJumpPartyRuntime->climbingLadder()
        && !pJumpPartyRuntime->swimming();
    const bool jumpRequested = allowWorldInput && jumpPressed && (!m_jumpHeld || jumpHeldOnGround);
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
            m_cameraYawRadians += keyboardYawSpeed * cameraDeltaSeconds;
        }

        if (rightPressed)
        {
            m_cameraYawRadians -= keyboardYawSpeed * cameraDeltaSeconds;
        }
    }

    // Keyboard look, like outdoors; positive pitch looks up.
    if (allowWorldInput)
    {
        const float keyboardPitchSpeed = 1.25f;

        if (input.action(KeyboardAction::LookUp).held)
        {
            m_cameraPitchRadians += keyboardPitchSpeed * cameraDeltaSeconds;
        }

        if (input.action(KeyboardAction::LookDown).held)
        {
            m_cameraPitchRadians -= keyboardPitchSpeed * cameraDeltaSeconds;
        }

        if (input.action(KeyboardAction::CenterView).held)
        {
            m_cameraPitchRadians *= std::max(0.0f, 1.0f - cameraDeltaSeconds * 8.0f);
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
        const float inputSpeedScale = std::clamp(input.movementSpeedScale, 0.0f, 1.0f);
        const float forwardMoveSpeed = walkSpeed * runScale * turboScale * inputSpeedScale;
        const float backwardMoveSpeed = walkSpeed * turboScale * inputSpeedScale;
        const float strafeMoveSpeed =
            walkSpeed * indoorStrafeMultiplier * runScale * turboScale * inputSpeedScale;

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
        partyRuntime.setLadderVerticalInput(!allowWorldInput
            ? 0
            : int(input.action(KeyboardAction::FlyUp).held) - int(input.action(KeyboardAction::FlyDown).held));
        // Swimming (scene water volumes): forward along the look direction, Jump or Fly Up up, Fly Down down.
        IndoorSwimInput swimInput = {};
        if (allowWorldInput)
        {
            swimInput.forward = float(input.action(KeyboardAction::Forward).held)
                - float(input.action(KeyboardAction::Backward).held);
            swimInput.strafe = float(strafeRightPressed) - float(strafeLeftPressed);
            swimInput.vertical = int(jumpPressed || input.action(KeyboardAction::FlyUp).held)
                - int(input.action(KeyboardAction::FlyDown).held);
        }
        swimInput.yawRadians = m_cameraYawRadians;
        swimInput.pitchRadians = std::clamp(m_cameraPitchRadians, -1.55f, 1.55f);
        swimInput.speedScale = turboScale * inputSpeedScale;
        partyRuntime.setSwimInput(swimInput);
        const bool runningMovement =
            running
            && allowWorldInput
            && (input.action(KeyboardAction::Forward).held || strafeLeftPressed || strafeRightPressed);
        partyRuntime.update(
            desiredVelocityX,
            desiredVelocityY,
            jumpRequested,
            runningMovement,
            deltaSeconds,
            input.turnBasedMovementStep,
            input.turnBasedPhysicsStep);
        const IndoorMoveState &moveState = m_pSceneRuntime->partyRuntime().movementState();
        m_cameraPositionX = moveState.x;
        m_cameraPositionY = moveState.y;
        m_cameraPositionZ = moveState.eyeZ();
    }
    else
    {
        const float inputSpeedScale = std::clamp(input.movementSpeedScale, 0.0f, 1.0f);
        const float currentMoveSpeed =
            walkSpeed * (turboPressed ? turboMultiplier : 1.5f) * inputSpeedScale;

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
