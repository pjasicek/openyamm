#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorBillboardRenderer.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/gameplay/GameplayDialogContextBuilder.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayHeldItemController.h"
#include "game/app/GameSession.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/SpawnPreview.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/SpellIds.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MonsterTable.h"
#include "game/SpriteObjectDefs.h"
#include "game/StringUtils.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include <SDL3/SDL.h>
#include <bx/math.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr float InspectRayEpsilon = 0.0001f;
constexpr float Pi = 3.14159265358979323846f;
constexpr float CameraVerticalFovDegrees = 60.0f;
constexpr float DefaultOutdoorFarClip = 16192.0f;

bool pendingSpellAllowsDeadActorTarget(const GameSession &gameSession)
{
    const GameplayScreenState::PendingSpellTargetState &pendingSpellTarget =
        gameSession.gameplayScreenState().pendingSpellTarget();
    return pendingSpellTarget.active && isSpellId(pendingSpellTarget.spellId, SpellId::Reanimate);
}

constexpr float QuickCastForwardFallbackDistance = 8192.0f;
constexpr float BillboardSpatialCellSize = 2048.0f;
constexpr float InteractionEntityHalfExtent = 96.0f;
constexpr float InteractionEntityHeight = 192.0f;
constexpr float InteractionDecorationMinHalfExtent = 24.0f;
constexpr float InteractionDecorationMinHeight = 48.0f;
constexpr float InteractionActorMinHalfExtent = 32.0f;
constexpr float InteractionActorMinHeight = 96.0f;
constexpr float InteractionWorldItemMinHalfExtent = 20.0f;
constexpr float InteractionWorldItemMinHeight = 40.0f;
constexpr float InteractionSpriteObjectMinHalfExtent = 24.0f;
constexpr float InteractionSpriteObjectMinHeight = 48.0f;

bool outdoorFaceHasInvisibleAttribute(uint32_t attributes)
{
    return hasFaceAttribute(attributes, FaceAttribute::Invisible);
}

bool outdoorFaceHasHintAttribute(uint32_t attributes)
{
    return hasFaceAttribute(attributes, FaceAttribute::HasHint);
}

bool outdoorFaceHasClickableAttribute(uint32_t attributes)
{
    return hasFaceAttribute(attributes, FaceAttribute::Clickable);
}

bool outdoorFaceIsInteractionActivatable(uint32_t attributes, uint16_t eventId)
{
    return eventId != 0
        && outdoorFaceHasClickableAttribute(attributes)
        && !outdoorFaceHasHintAttribute(attributes)
        && !outdoorFaceHasInvisibleAttribute(attributes);
}

bool interactiveDecorationHidesWhenCleared(OutdoorGameView::InteractiveDecorationFamily family)
{
    return family == OutdoorGameView::InteractiveDecorationFamily::CampFire;
}

bool shouldUseHouseTradeItemReaction(
    const EventRuntimeState &eventRuntimeState,
    const std::optional<EventDialogAction> &action,
    int,
    const Party *pParty)
{
    if (!action.has_value()
        || (eventRuntimeState.grantedItems.empty() && eventRuntimeState.grantedItemIds.empty())
        || pParty == nullptr)
    {
        return false;
    }

    return true;
}

struct DirectInteractiveDecorationBindingSpec
{
    uint16_t baseEventId = 0;
    uint8_t eventCount = 0;
    uint8_t initialState = 0;
    bool useSeededInitialState = false;
    bool hideWhenCleared = false;
    OutdoorGameView::InteractiveDecorationFamily family = OutdoorGameView::InteractiveDecorationFamily::None;
};

uint16_t interactiveDecorationBaseEventId(OutdoorGameView::InteractiveDecorationFamily family);
uint8_t interactiveDecorationEventCount(OutdoorGameView::InteractiveDecorationFamily family);

std::string normalizeDecorationKey(const std::string &value)
{
    const std::string lowered = toLowerCopy(value);
    size_t begin = 0;

    while (begin < lowered.size() && std::isspace(static_cast<unsigned char>(lowered[begin])) != 0)
    {
        ++begin;
    }

    size_t end = lowered.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(lowered[end - 1])) != 0)
    {
        --end;
    }

    return lowered.substr(begin, end - begin);
}

bool decorationMatchesAnyKey(
    const std::vector<std::string> &keys,
    std::initializer_list<std::string_view> candidates)
{
    for (const std::string &key : keys)
    {
        for (std::string_view candidate : candidates)
        {
            if (key == candidate)
            {
                return true;
            }
        }
    }

    return false;
}

std::optional<OutdoorGameView::InteractiveDecorationFamily> classifyInteractiveDecorationFamily(
    const DecorationEntry &decoration,
    const std::string &instanceName)
{
    std::vector<std::string> keys;
    keys.reserve(3);

    const std::string hint = normalizeDecorationKey(decoration.hint);
    const std::string internalName = normalizeDecorationKey(decoration.internalName);
    const std::string normalizedInstanceName = normalizeDecorationKey(instanceName);

    if (!hint.empty())
    {
        keys.push_back(hint);
    }

    if (!internalName.empty() && std::find(keys.begin(), keys.end(), internalName) == keys.end())
    {
        keys.push_back(internalName);
    }

    if (!normalizedInstanceName.empty()
        && std::find(keys.begin(), keys.end(), normalizedInstanceName) == keys.end())
    {
        keys.push_back(normalizedInstanceName);
    }

    if (decorationMatchesAnyKey(keys, {"barrel", "dec03", "dec32"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::Barrel;
    }

    if (decorationMatchesAnyKey(keys, {"cauldron", "dec26"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::Cauldron;
    }

    if (decorationMatchesAnyKey(keys, {"trash heap", "trash pile", "dec01", "dec10", "dec23"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::TrashHeap;
    }

    if (decorationMatchesAnyKey(keys, {"campfire", "camp fire", "dec24", "dec25"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::CampFire;
    }

    if (decorationMatchesAnyKey(keys, {"keg", "cask", "dec21"}))
    {
        return OutdoorGameView::InteractiveDecorationFamily::Cask;
    }

    return std::nullopt;
}

std::optional<int> parseDecorationInternalNumber(const std::string &value)
{
    const std::string normalized = normalizeDecorationKey(value);

    if (normalized.size() < 4 || normalized[0] != 'd' || normalized[1] != 'e' || normalized[2] != 'c')
    {
        return std::nullopt;
    }

    int number = 0;

    for (size_t index = 3; index < normalized.size(); ++index)
    {
        const char character = normalized[index];

        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return std::nullopt;
        }

        number = number * 10 + (character - '0');
    }

    return number;
}

std::optional<int> resolveDecorationInternalNumber(
    const DecorationEntry &decoration,
    const std::string &instanceName)
{
    if (const std::optional<int> internalNumber = parseDecorationInternalNumber(decoration.internalName))
    {
        return internalNumber;
    }

    return parseDecorationInternalNumber(instanceName);
}

std::optional<DirectInteractiveDecorationBindingSpec> resolveDirectInteractiveDecorationBindingSpec(
    const DecorationEntry &decoration,
    const std::string &instanceName)
{
    const std::optional<OutdoorGameView::InteractiveDecorationFamily> family =
        classifyInteractiveDecorationFamily(decoration, instanceName);

    if (family)
    {
        const uint16_t baseEventId = interactiveDecorationBaseEventId(*family);
        const uint8_t eventCount = interactiveDecorationEventCount(*family);

        if (baseEventId == 0 || eventCount == 0)
        {
            return std::nullopt;
        }

        DirectInteractiveDecorationBindingSpec spec = {};
        spec.baseEventId = baseEventId;
        spec.eventCount = eventCount;
        spec.hideWhenCleared = interactiveDecorationHidesWhenCleared(*family);
        spec.family = *family;
        return spec;
    }

    const std::optional<int> internalNumber = resolveDecorationInternalNumber(decoration, instanceName);

    if (!internalNumber)
    {
        return std::nullopt;
    }

    DirectInteractiveDecorationBindingSpec spec = {};

    if (*internalNumber >= 44 && *internalNumber <= 55)
    {
        spec.baseEventId = 531;
        spec.eventCount = 12;
        spec.initialState = static_cast<uint8_t>(*internalNumber - 44);
        return spec;
    }

    if (*internalNumber >= 40 && *internalNumber <= 43)
    {
        spec.baseEventId = static_cast<uint16_t>(542 + (*internalNumber - 40) * 7);
        spec.eventCount = 7;
        spec.useSeededInitialState = true;
        return spec;
    }

    return std::nullopt;
}

uint16_t interactiveDecorationBaseEventId(OutdoorGameView::InteractiveDecorationFamily family)
{
    switch (family)
    {
        case OutdoorGameView::InteractiveDecorationFamily::Barrel:
            return 268;

        case OutdoorGameView::InteractiveDecorationFamily::Cauldron:
            return 276;

        case OutdoorGameView::InteractiveDecorationFamily::TrashHeap:
            return 281;

        case OutdoorGameView::InteractiveDecorationFamily::CampFire:
            return 285;

        case OutdoorGameView::InteractiveDecorationFamily::Cask:
            return 288;

        case OutdoorGameView::InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

uint8_t interactiveDecorationEventCount(OutdoorGameView::InteractiveDecorationFamily family)
{
    switch (family)
    {
        case OutdoorGameView::InteractiveDecorationFamily::Barrel:
            return 8;

        case OutdoorGameView::InteractiveDecorationFamily::Cauldron:
            return 5;

        case OutdoorGameView::InteractiveDecorationFamily::TrashHeap:
            return 4;

        case OutdoorGameView::InteractiveDecorationFamily::CampFire:
            return 2;

        case OutdoorGameView::InteractiveDecorationFamily::Cask:
            return 2;

        case OutdoorGameView::InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

uint32_t makeInteractiveDecorationSeed(const OutdoorEntity &entity, size_t entityIndex)
{
    uint32_t seed = static_cast<uint32_t>((entityIndex + 1u) * 2654435761u);
    seed ^= static_cast<uint32_t>(entity.decorationListId + 1u) * 2246822519u;
    seed ^= static_cast<uint32_t>(entity.x) * 3266489917u;
    seed ^= static_cast<uint32_t>(entity.y) * 668265263u;
    seed ^= static_cast<uint32_t>(entity.z + 1) * 374761393u;
    return seed;
}

uint8_t initialInteractiveDecorationState(
    OutdoorGameView::InteractiveDecorationFamily family,
    uint32_t seed)
{
    switch (family)
    {
        case OutdoorGameView::InteractiveDecorationFamily::Barrel:
            return static_cast<uint8_t>(1u + seed % 7u);

        case OutdoorGameView::InteractiveDecorationFamily::Cauldron:
            return static_cast<uint8_t>(1u + seed % 4u);

        case OutdoorGameView::InteractiveDecorationFamily::Cask:
            return 1;

        case OutdoorGameView::InteractiveDecorationFamily::TrashHeap:
        case OutdoorGameView::InteractiveDecorationFamily::CampFire:
        case OutdoorGameView::InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

std::string formatFoundItemStatusText(int goldAmount, const std::string &itemName)
{
    const std::string resolvedItemName = itemName.empty() ? "item" : itemName;

    if (goldAmount > 0)
    {
        return "You found " + std::to_string(goldAmount) + " gold and an item (" + resolvedItemName + ")!";
    }

    return "You found an item (" + resolvedItemName + ")!";
}

std::string formatFoundGoldStatusText(int goldAmount)
{
    return "You found " + std::to_string(std::max(0, goldAmount)) + " gold!";
}

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

bx::Vec3 vecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

float vecDot(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

bx::Vec3 vecCross(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
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

    const float inverseLength = 1.0f / vectorLength;
    return {vector.x * inverseLength, vector.y * inverseLength, vector.z * inverseLength};
}

struct ProjectedPoint
{
    float x = 0.0f;
    float y = 0.0f;
};

bool projectWorldPointToScreen(
    const bx::Vec3 &point,
    int viewWidth,
    int viewHeight,
    const float *pViewProjectionMatrix,
    ProjectedPoint &projectedPoint)
{
    const float x = point.x;
    const float y = point.y;
    const float z = point.z;
    const float clipX =
        x * pViewProjectionMatrix[0] + y * pViewProjectionMatrix[4] + z * pViewProjectionMatrix[8]
        + pViewProjectionMatrix[12];
    const float clipY =
        x * pViewProjectionMatrix[1] + y * pViewProjectionMatrix[5] + z * pViewProjectionMatrix[9]
        + pViewProjectionMatrix[13];
    const float clipW =
        x * pViewProjectionMatrix[3] + y * pViewProjectionMatrix[7] + z * pViewProjectionMatrix[11]
        + pViewProjectionMatrix[15];

    if (clipW <= InspectRayEpsilon)
    {
        return false;
    }

    const float inverseW = 1.0f / clipW;
    const float ndcX = clipX * inverseW;
    const float ndcY = clipY * inverseW;

    projectedPoint.x = ((ndcX + 1.0f) * 0.5f) * static_cast<float>(viewWidth);
    projectedPoint.y = ((1.0f - ndcY) * 0.5f) * static_cast<float>(viewHeight);
    return true;
}

bool intersectRayTriangle(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const bx::Vec3 &vertex0,
    const bx::Vec3 &vertex1,
    const bx::Vec3 &vertex2,
    float &distance);

std::optional<float> intersectOutdoorFaceRay(
    const OutdoorBModel &bModel,
    const OutdoorBModelFace &face,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection)
{
    std::optional<float> bestDistance;

    for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
    {
        const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
        bx::Vec3 triangleVertices[3] = {
            bx::Vec3 {0.0f, 0.0f, 0.0f},
            bx::Vec3 {0.0f, 0.0f, 0.0f},
            bx::Vec3 {0.0f, 0.0f, 0.0f}
        };
        bool validTriangle = true;

        for (size_t triangleVertexSlot = 0; triangleVertexSlot < 3; ++triangleVertexSlot)
        {
            const uint16_t vertexIndex = face.vertexIndices[triangleVertexIndices[triangleVertexSlot]];

            if (vertexIndex >= bModel.vertices.size())
            {
                validTriangle = false;
                break;
            }

            triangleVertices[triangleVertexSlot] = outdoorBModelVertexToWorld(bModel.vertices[vertexIndex]);
        }

        if (!validTriangle)
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

        if (distance <= InspectRayEpsilon)
        {
            continue;
        }

        if (!bestDistance.has_value() || distance < *bestDistance)
        {
            bestDistance = distance;
        }
    }

    return bestDistance;
}

float interactionDepthForInputMethod(
    const OutdoorGameView &view,
    OutdoorInteractionController::InteractionInputMethod inputMethod)
{
    const GameSettings &settings = view.settingsSnapshot();
    const int configuredDepth = inputMethod == OutdoorInteractionController::InteractionInputMethod::Keyboard
        ? settings.keyboardInteractionDepth
        : settings.mouseInteractionDepth;
    return static_cast<float>(std::clamp(configuredDepth, 32, 4096));
}

bool shouldSkipSpriteObjectInspectTarget(const SpriteObjectBillboard &object, const ObjectEntry *pObjectEntry)
{
    if (pObjectEntry == nullptr || object.objectDescriptionId == 0)
    {
        return true;
    }

    if ((object.attributes & (SpriteAttrTemporary | SpriteAttrMissile | SpriteAttrRemoved)) != 0)
    {
        return true;
    }

    if ((pObjectEntry->flags & (ObjectDescNoSprite
                                | ObjectDescNoCollision
                                | ObjectDescTemporary
                                | ObjectDescUnpickable
                                | ObjectDescTrailParticle
                                | ObjectDescTrailFire
                                | ObjectDescTrailLine)) != 0)
    {
        return true;
    }

    if (object.spellId != 0)
    {
        return true;
    }

    return false;
}

float resolveActorAabbBaseZ(
    const OutdoorMapData &outdoorMapData,
    const OutdoorWorldRuntime::MapActorState *pActorState,
    int actorX,
    int actorY,
    int actorZ,
    bool clampDeadActorToGround)
{
    if (!clampDeadActorToGround)
    {
        return static_cast<float>(actorZ);
    }

    if (pActorState != nullptr && pActorState->movementStateInitialized)
    {
        const OutdoorMoveState &movementState = pActorState->movementState;

        if (movementState.supportKind == OutdoorSupportKind::Terrain
            || movementState.supportKind == OutdoorSupportKind::BModelFace)
        {
            return movementState.footZ - 1.0f;
        }
    }

    return sampleOutdoorSupportFloorHeight(
        outdoorMapData,
        static_cast<float>(actorX),
        static_cast<float>(actorY),
        static_cast<float>(actorZ));
}

bool intersectRayTriangle(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const bx::Vec3 &vertex0,
    const bx::Vec3 &vertex1,
    const bx::Vec3 &vertex2,
    float &distance)
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
    float &distance)
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

std::optional<float> intersectOutdoorTerrainRay(
    const OutdoorMapData &outdoorMapData,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection)
{
    float closestDistance = std::numeric_limits<float>::max();
    bool hasIntersection = false;

    for (int gridY = 0; gridY < OutdoorMapData::TerrainHeight - 1; ++gridY)
    {
        for (int gridX = 0; gridX < OutdoorMapData::TerrainWidth - 1; ++gridX)
        {
            const size_t topLeftIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const size_t topRightIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + (gridX + 1));
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex =
                static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + (gridX + 1));

            const bx::Vec3 topLeft = {
                outdoorGridCornerWorldX(gridX),
                outdoorGridCornerWorldY(gridY),
                static_cast<float>(outdoorMapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale)
            };
            const bx::Vec3 topRight = {
                outdoorGridCornerWorldX(gridX + 1),
                outdoorGridCornerWorldY(gridY),
                static_cast<float>(outdoorMapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale)
            };
            const bx::Vec3 bottomLeft = {
                outdoorGridCornerWorldX(gridX),
                outdoorGridCornerWorldY(gridY + 1),
                static_cast<float>(outdoorMapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale)
            };
            const bx::Vec3 bottomRight = {
                outdoorGridCornerWorldX(gridX + 1),
                outdoorGridCornerWorldY(gridY + 1),
                static_cast<float>(outdoorMapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale)
            };

            float distance = 0.0f;

            if (intersectRayTriangle(rayOrigin, rayDirection, topLeft, bottomLeft, topRight, distance)
                && distance < closestDistance)
            {
                closestDistance = distance;
                hasIntersection = true;
            }

            if (intersectRayTriangle(rayOrigin, rayDirection, topRight, bottomLeft, bottomRight, distance)
                && distance < closestDistance)
            {
                closestDistance = distance;
                hasIntersection = true;
            }
        }
    }

    if (!hasIntersection)
    {
        return std::nullopt;
    }

    return closestDistance;
}

} // namespace

std::optional<size_t> OutdoorInteractionController::resolveSpellActionHoveredActorIndex(const OutdoorGameView &view)
{
    if (!view.m_cachedHoverInspectHitValid || view.m_cachedHoverInspectHit.kind != "actor")
    {
        return std::nullopt;
    }

    const std::optional<size_t> actorIndex =
        OutdoorInteractionController::resolveRuntimeActorIndexForInspectHit(view, view.m_cachedHoverInspectHit);

    if (!actorIndex || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    const OutdoorWorldRuntime::MapActorState *pActor = view.m_pOutdoorWorldRuntime->mapActorState(*actorIndex);

    if (pActor == nullptr
        || pActor->isDead
        || pActor->isInvisible
        || !pActor->hostileToParty
        || !pActor->hasDetectedParty)
    {
        return std::nullopt;
    }

    return actorIndex;
}

std::optional<size_t> OutdoorInteractionController::resolveClosestVisibleHostileActorIndex(
    const OutdoorGameView &view,
    float sourceX,
    float sourceY,
    float sourceZ)
{
    if (view.m_pOutdoorWorldRuntime == nullptr || view.m_lastRenderWidth <= 0 || view.m_lastRenderHeight <= 0)
    {
        return std::nullopt;
    }

    const uint16_t viewWidth = static_cast<uint16_t>(std::max(view.m_lastRenderWidth, 1));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(view.m_lastRenderHeight, 1));
    const float aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
    const float cameraYawRadians = view.effectiveCameraYawRadians();
    const float cameraPitchRadians = view.effectiveCameraPitchRadians();
    const float cosPitch = std::cos(cameraPitchRadians);
    const float sinPitch = std::sin(cameraPitchRadians);
    const float cosYaw = std::cos(cameraYawRadians);
    const float sinYaw = std::sin(cameraYawRadians);
    const bx::Vec3 eye = {
        view.m_cameraTargetX,
        view.m_cameraTargetY,
        view.m_cameraTargetZ
    };
    const bx::Vec3 at = {
        view.m_cameraTargetX + cosYaw * cosPitch,
        view.m_cameraTargetY + sinYaw * cosPitch,
        view.m_cameraTargetZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    float viewProjectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        CameraVerticalFovDegrees,
        aspectRatio,
        0.1f,
        200000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );
    bx::mtxMul(viewProjectionMatrix, viewMatrix, projectionMatrix);

    std::optional<size_t> nearestActorIndex;
    float nearestDistanceSquared = std::numeric_limits<float>::max();

    for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

        if (pActor == nullptr
            || pActor->isDead
            || pActor->isInvisible
            || !pActor->hostileToParty
            || !pActor->hasDetectedParty)
        {
            continue;
        }

        ProjectedPoint projected = {};
        const bx::Vec3 actorPoint = {
            pActor->preciseX,
            pActor->preciseY,
            pActor->preciseZ + std::max(48.0f, static_cast<float>(pActor->height) * 0.6f)
        };

        if (!projectWorldPointToScreen(
                actorPoint,
                view.m_lastRenderWidth,
                view.m_lastRenderHeight,
                viewProjectionMatrix,
                projected))
        {
            continue;
        }

        if (projected.x < 0.0f
            || projected.x > static_cast<float>(view.m_lastRenderWidth)
            || projected.y < 0.0f
            || projected.y > static_cast<float>(view.m_lastRenderHeight))
        {
            continue;
        }

        const float dx = pActor->preciseX - sourceX;
        const float dy = pActor->preciseY - sourceY;
        const float dz = pActor->preciseZ - sourceZ;
        const float distanceSquared = dx * dx + dy * dy + dz * dz;

        if (distanceSquared < nearestDistanceSquared)
        {
            nearestDistanceSquared = distanceSquared;
            nearestActorIndex = actorIndex;
        }
    }

    return nearestActorIndex;
}

std::optional<bx::Vec3> OutdoorInteractionController::resolveSpellActionActorTargetPoint(
    const OutdoorGameView &view,
    size_t actorIndex)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    const OutdoorWorldRuntime::MapActorState *pActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

    if (pActor == nullptr || pActor->isDead || pActor->isInvisible)
    {
        return std::nullopt;
    }

    return bx::Vec3 {
        pActor->preciseX,
        pActor->preciseY,
        pActor->preciseZ + std::max(48.0f, static_cast<float>(pActor->height) * 0.6f)
    };
}

bool OutdoorInteractionController::buildQuickCastInspectRayForScreenPoint(
    const OutdoorGameView &view,
    float screenX,
    float screenY,
    bx::Vec3 &rayOrigin,
    bx::Vec3 &rayDirection)
{
    const uint16_t viewWidth = static_cast<uint16_t>(std::max(view.m_lastRenderWidth, 1));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(view.m_lastRenderHeight, 1));

    if (viewWidth == 0 || viewHeight == 0)
    {
        return false;
    }

    const float aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
    const float cameraYawRadians = view.effectiveCameraYawRadians();
    const float cameraPitchRadians = view.effectiveCameraPitchRadians();
    const float cosPitch = std::cos(cameraPitchRadians);
    const float sinPitch = std::sin(cameraPitchRadians);
    const float cosYaw = std::cos(cameraYawRadians);
    const float sinYaw = std::sin(cameraYawRadians);
    const bx::Vec3 eye = {
        view.m_cameraTargetX,
        view.m_cameraTargetY,
        view.m_cameraTargetZ
    };
    const bx::Vec3 at = {
        view.m_cameraTargetX + cosYaw * cosPitch,
        view.m_cameraTargetY + sinYaw * cosPitch,
        view.m_cameraTargetZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        CameraVerticalFovDegrees,
        aspectRatio,
        0.1f,
        200000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );

    return OutdoorInteractionController::buildInspectRayForScreenPoint(
        screenX,
        screenY,
        viewWidth,
        viewHeight,
        viewMatrix,
        projectionMatrix,
        rayOrigin,
        rayDirection);
}

std::optional<bx::Vec3> OutdoorInteractionController::resolveQuickCastCursorTargetPoint(
    const OutdoorGameView &view,
    float cursorX,
    float cursorY)
{
    if (!view.m_outdoorMapData.has_value() || view.m_lastRenderWidth <= 0 || view.m_lastRenderHeight <= 0)
    {
        return std::nullopt;
    }

    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!buildQuickCastInspectRayForScreenPoint(view, cursorX, cursorY, rayOrigin, rayDirection))
    {
        return std::nullopt;
    }

    const uint16_t viewWidth = static_cast<uint16_t>(std::max(view.m_lastRenderWidth, 1));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(view.m_lastRenderHeight, 1));
    const float aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
    const float cameraYawRadians = view.effectiveCameraYawRadians();
    const float cameraPitchRadians = view.effectiveCameraPitchRadians();
    const float cosPitch = std::cos(cameraPitchRadians);
    const float sinPitch = std::sin(cameraPitchRadians);
    const float cosYaw = std::cos(cameraYawRadians);
    const float sinYaw = std::sin(cameraYawRadians);
    const bx::Vec3 eye = {
        view.m_cameraTargetX,
        view.m_cameraTargetY,
        view.m_cameraTargetZ
    };
    const bx::Vec3 at = {
        view.m_cameraTargetX + cosYaw * cosPitch,
        view.m_cameraTargetY + sinYaw * cosPitch,
        view.m_cameraTargetZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        CameraVerticalFovDegrees,
        aspectRatio,
        0.1f,
        200000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );

    const OutdoorGameView::InspectHit inspectHit = OutdoorInteractionController::inspectBModelFace(
        const_cast<OutdoorGameView &>(view),
        *view.m_outdoorMapData,
        rayOrigin,
        rayDirection,
        cursorX,
        cursorY,
        view.m_lastRenderWidth,
        view.m_lastRenderHeight,
        viewMatrix,
        projectionMatrix,
        OutdoorGameView::DecorationPickMode::Interaction);
    const std::optional<float> terrainDistance =
        intersectOutdoorTerrainRay(*view.m_outdoorMapData, rayOrigin, rayDirection);
    const std::optional<bx::Vec3> fallbackGroundTargetPoint =
        terrainDistance
            ? std::optional<bx::Vec3>(bx::Vec3 {
                rayOrigin.x + rayDirection.x * *terrainDistance,
                rayOrigin.y + rayDirection.y * *terrainDistance,
                rayOrigin.z + rayDirection.z * *terrainDistance
            })
            : std::nullopt;

    if (inspectHit.hasHit)
    {
        const GameplayWorldHit worldHit =
            OutdoorInteractionController::translateInspectHitToGameplayWorldHit(view, inspectHit);
        const std::optional<bx::Vec3> inspectTargetPoint =
            GameplaySpellActionController::resolveGroundTargetPointForWorldHit(
                worldHit,
                view.m_pOutdoorWorldRuntime,
                fallbackGroundTargetPoint);

        if (inspectTargetPoint)
        {
            return inspectTargetPoint;
        }
    }

    if (fallbackGroundTargetPoint)
    {
        return fallbackGroundTargetPoint;
    }

    return bx::Vec3 {
        rayOrigin.x + rayDirection.x * QuickCastForwardFallbackDistance,
        rayOrigin.y + rayDirection.y * QuickCastForwardFallbackDistance,
        rayOrigin.z + rayDirection.z * QuickCastForwardFallbackDistance
    };
}

OutdoorGameView::InspectHit OutdoorInteractionController::inspectHitFromGameplayWorldHit(
    const GameplayWorldHit &worldHit)
{
    OutdoorGameView::InspectHit inspectHit = {};

    if (!worldHit.hasHit)
    {
        return inspectHit;
    }

    inspectHit.hasHit = true;

    if (worldHit.kind == GameplayWorldHitKind::Actor && worldHit.actor)
    {
        const GameplayActorTargetHit &actorHit = *worldHit.actor;
        inspectHit.kind = "actor";
        inspectHit.name = actorHit.displayName;
        inspectHit.isFriendly = actorHit.isFriendly;
        inspectHit.npcId = actorHit.npcId;
        inspectHit.actorGroup = actorHit.actorGroup;
        inspectHit.distance = actorHit.distance;
        inspectHit.hitX = actorHit.hitPoint.x;
        inspectHit.hitY = actorHit.hitPoint.y;
        inspectHit.hitZ = actorHit.hitPoint.z;

        if (actorHit.actorIndex != GameplayInvalidWorldIndex)
        {
            inspectHit.runtimeActorIndex = actorHit.actorIndex;
            inspectHit.bModelIndex = actorHit.actorIndex;
        }

        return inspectHit;
    }

    if (worldHit.kind == GameplayWorldHitKind::WorldItem && worldHit.worldItem)
    {
        const GameplayWorldItemTargetHit &worldItemHit = *worldHit.worldItem;
        inspectHit.kind = "world_item";
        inspectHit.bModelIndex = worldItemHit.worldItemIndex;
        inspectHit.objectDescriptionId = worldItemHit.objectDescriptionId;
        inspectHit.objectSpriteId = worldItemHit.objectSpriteId;
        inspectHit.distance = worldItemHit.distance;
        inspectHit.hitX = worldItemHit.hitPoint.x;
        inspectHit.hitY = worldItemHit.hitPoint.y;
        inspectHit.hitZ = worldItemHit.hitPoint.z;
        return inspectHit;
    }

    if ((worldHit.kind == GameplayWorldHitKind::Chest || worldHit.kind == GameplayWorldHitKind::Corpse)
        && worldHit.container)
    {
        const GameplayContainerTargetHit &containerHit = *worldHit.container;
        inspectHit.kind =
            containerHit.sourceKind == GameplayWorldContainerSourceKind::Chest ? "chest" : "corpse";
        inspectHit.bModelIndex = containerHit.sourceIndex;
        inspectHit.distance = containerHit.distance;
        return inspectHit;
    }

    if (worldHit.kind == GameplayWorldHitKind::Object && worldHit.object)
    {
        const GameplayObjectTargetHit &objectHit = *worldHit.object;
        inspectHit.kind = "object";
        inspectHit.bModelIndex = objectHit.objectIndex;
        inspectHit.objectDescriptionId = objectHit.objectDescriptionId;
        inspectHit.objectSpriteId = objectHit.objectSpriteId;
        inspectHit.spellId = objectHit.spellId;
        inspectHit.distance = objectHit.distance;
        inspectHit.hitX = objectHit.hitPoint.x;
        inspectHit.hitY = objectHit.hitPoint.y;
        inspectHit.hitZ = objectHit.hitPoint.z;
        return inspectHit;
    }

    if (worldHit.kind == GameplayWorldHitKind::EventTarget && worldHit.eventTarget)
    {
        const GameplayEventTargetHit &eventTargetHit = *worldHit.eventTarget;
        inspectHit.bModelIndex = eventTargetHit.targetIndex;
        inspectHit.faceIndex = eventTargetHit.secondaryIndex;
        inspectHit.eventIdPrimary = eventTargetHit.eventIdPrimary;
        inspectHit.eventIdSecondary = eventTargetHit.eventIdSecondary;
        inspectHit.cogTriggeredNumber = eventTargetHit.triggeredEventId;
        inspectHit.cogTrigger = eventTargetHit.trigger;
        inspectHit.variablePrimary = eventTargetHit.variablePrimary;
        inspectHit.variableSecondary = eventTargetHit.variableSecondary;
        inspectHit.specialTrigger = eventTargetHit.specialTrigger;
        inspectHit.attributes = eventTargetHit.attributes;
        inspectHit.name = eventTargetHit.name;
        inspectHit.distance = eventTargetHit.distance;
        inspectHit.hitX = eventTargetHit.hitPoint.x;
        inspectHit.hitY = eventTargetHit.hitPoint.y;
        inspectHit.hitZ = eventTargetHit.hitPoint.z;

        if (eventTargetHit.targetKind == GameplayWorldEventTargetKind::Surface)
        {
            inspectHit.kind = "face";
        }
        else if (eventTargetHit.targetKind == GameplayWorldEventTargetKind::Entity)
        {
            inspectHit.kind = "entity";
        }
        else if (eventTargetHit.targetKind == GameplayWorldEventTargetKind::Decoration)
        {
            inspectHit.kind = "decoration";
        }
        else if (eventTargetHit.targetKind == GameplayWorldEventTargetKind::Spawn)
        {
            inspectHit.kind = "spawn";
        }
        else
        {
            inspectHit = {};
        }
    }

    return inspectHit;
}

bool OutdoorInteractionController::buildInspectRayForScreenPoint(
    float screenX,
    float screenY,
    int viewWidth,
    int viewHeight,
    const float *pViewMatrix,
    const float *pProjectionMatrix,
    bx::Vec3 &rayOrigin,
    bx::Vec3 &rayDirection)
{
    if (viewWidth <= 0 || viewHeight <= 0 || pViewMatrix == nullptr || pProjectionMatrix == nullptr)
    {
        return false;
    }

    const float normalizedX = ((screenX / static_cast<float>(viewWidth)) * 2.0f) - 1.0f;
    const float normalizedY = 1.0f - ((screenY / static_cast<float>(viewHeight)) * 2.0f);
    float viewProjectionMatrix[16] = {};
    float inverseViewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, pViewMatrix, pProjectionMatrix);
    bx::mtxInverse(inverseViewProjectionMatrix, viewProjectionMatrix);
    rayOrigin = bx::mulH({normalizedX, normalizedY, 0.0f}, inverseViewProjectionMatrix);
    const bx::Vec3 rayTarget = bx::mulH({normalizedX, normalizedY, 1.0f}, inverseViewProjectionMatrix);
    rayDirection = vecNormalize(vecSubtract(rayTarget, rayOrigin));
    return vecLength(rayDirection) > InspectRayEpsilon;
}

uint16_t OutdoorInteractionController::resolveDecorationBillboardSpriteId(
    const OutdoorGameView &view,
    const DecorationBillboard &billboard,
    bool &hidden)
{
    hidden = false;
    uint16_t spriteId = billboard.spriteId;

    if (!view.m_outdoorDecorationBillboardSet || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return spriteId;
    }

    const EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return spriteId;
    }

    const uint32_t overrideKey =
        billboard.eventIdPrimary != 0 ? billboard.eventIdPrimary : billboard.eventIdSecondary;

    if (overrideKey == 0)
    {
        return spriteId;
    }

    const auto overrideIterator = pEventRuntimeState->spriteOverrides.find(overrideKey);

    if (overrideIterator == pEventRuntimeState->spriteOverrides.end())
    {
        return spriteId;
    }

    hidden = overrideIterator->second.hidden;

    if (!overrideIterator->second.textureName.has_value() || overrideIterator->second.textureName->empty())
    {
        return spriteId;
    }

    if (const DecorationEntry *pDecoration =
            view.m_outdoorDecorationBillboardSet->decorationTable.findByInternalName(
                *overrideIterator->second.textureName))
    {
        return pDecoration->spriteId;
    }

    if (const std::optional<uint16_t> overrideSpriteId =
            view.m_outdoorDecorationBillboardSet->spriteFrameTable.findFrameIndexBySpriteName(
                *overrideIterator->second.textureName))
    {
        return *overrideSpriteId;
    }

    return spriteId;
}

void OutdoorInteractionController::rebuildInteractiveDecorationBindings(OutdoorGameView &view)
{
    view.m_interactiveDecorationBindings.clear();

    if (!view.m_outdoorMapData || !view.m_outdoorDecorationBillboardSet)
    {
        return;
    }

    const DecorationTable &decorationTable = view.m_outdoorDecorationBillboardSet->decorationTable;
    uint8_t decorVarIndex = 0;
    constexpr uint8_t MaxDecorationVarCount = 125;
    view.m_interactiveDecorationBindings.resize(view.m_outdoorMapData->entities.size());

    for (size_t entityIndex = 0; entityIndex < view.m_outdoorMapData->entities.size(); ++entityIndex)
    {
        const OutdoorEntity &entity = view.m_outdoorMapData->entities[entityIndex];

        if (entity.eventIdPrimary != 0 || entity.eventIdSecondary != 0)
        {
            continue;
        }

        const DecorationEntry *pDecoration = decorationTable.get(entity.decorationListId);

        if ((pDecoration == nullptr || pDecoration->spriteId == 0) && !entity.name.empty())
        {
            pDecoration = decorationTable.findByInternalName(entity.name);
        }

        if (pDecoration == nullptr)
        {
            continue;
        }

        const std::optional<DirectInteractiveDecorationBindingSpec> bindingSpec =
            resolveDirectInteractiveDecorationBindingSpec(*pDecoration, entity.name);

        if (!bindingSpec || decorVarIndex >= MaxDecorationVarCount)
        {
            continue;
        }

        OutdoorGameView::InteractiveDecorationBinding &binding = view.m_interactiveDecorationBindings[entityIndex];
        binding.active = true;
        binding.decorVarIndex = decorVarIndex++;
        binding.entityIndex = static_cast<uint16_t>(entityIndex);
        binding.baseEventId = bindingSpec->baseEventId;
        binding.eventCount = bindingSpec->eventCount;
        binding.initialState = bindingSpec->initialState;
        binding.useSeededInitialState = bindingSpec->useSeededInitialState;
        binding.hideWhenCleared = bindingSpec->hideWhenCleared;
        binding.family = bindingSpec->family;
    }
}

void OutdoorInteractionController::seedInteractiveDecorationRuntimeStateIfNeeded(OutdoorGameView &view)
{
    if (!view.m_outdoorMapData.has_value() || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    bool hasPersistedDecorationState = false;

    if (view.m_outdoorMapDeltaData.has_value())
    {
        for (uint8_t value : view.m_outdoorMapDeltaData->eventVariables.decorVars)
        {
            if (value != 0)
            {
                hasPersistedDecorationState = true;
                break;
            }
        }
    }

    if (hasPersistedDecorationState)
    {
        return;
    }

    for (uint8_t value : pEventRuntimeState->decorVars)
    {
        if (value != 0)
        {
            return;
        }
    }

    for (const OutdoorGameView::InteractiveDecorationBinding &binding : view.m_interactiveDecorationBindings)
    {
        if (!binding.active || binding.entityIndex >= view.m_outdoorMapData->entities.size())
        {
            continue;
        }

        const OutdoorEntity &entity = view.m_outdoorMapData->entities[binding.entityIndex];
        uint8_t initialState = binding.initialState;

        if (binding.useSeededInitialState)
        {
            initialState = static_cast<uint8_t>(makeInteractiveDecorationSeed(entity, binding.entityIndex) % binding.eventCount);
        }
        else if (binding.family != OutdoorGameView::InteractiveDecorationFamily::None)
        {
            initialState = initialInteractiveDecorationState(
                binding.family,
                makeInteractiveDecorationSeed(entity, binding.entityIndex));
        }

        if (initialState == 0)
        {
            continue;
        }

        pEventRuntimeState->decorVars[binding.decorVarIndex] = initialState;
    }
}

const OutdoorGameView::InteractiveDecorationBinding *OutdoorInteractionController::findInteractiveDecorationBindingForEntity(
    const OutdoorGameView &view,
    size_t entityIndex)
{
    if (entityIndex >= view.m_interactiveDecorationBindings.size())
    {
        return nullptr;
    }

    const OutdoorGameView::InteractiveDecorationBinding &binding = view.m_interactiveDecorationBindings[entityIndex];
    return binding.active ? &binding : nullptr;
}

bool OutdoorInteractionController::isInteractiveDecorationHidden(const OutdoorGameView &view, size_t entityIndex)
{
    const OutdoorGameView::InteractiveDecorationBinding *pBinding =
        findInteractiveDecorationBindingForEntity(view, entityIndex);

    if (pBinding == nullptr || !pBinding->hideWhenCleared || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return false;
    }

    const EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    return pEventRuntimeState->decorVars[pBinding->decorVarIndex] == pBinding->eventCount;
}

std::optional<uint16_t> OutdoorInteractionController::resolveInteractiveDecorationEventId(
    const OutdoorGameView &view,
    size_t entityIndex)
{
    const OutdoorGameView::InteractiveDecorationBinding *pBinding =
        findInteractiveDecorationBindingForEntity(view, entityIndex);

    if (pBinding == nullptr || pBinding->eventCount == 0 || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    const EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return std::nullopt;
    }

    uint8_t state = pEventRuntimeState->decorVars[pBinding->decorVarIndex];

    if (pBinding->hideWhenCleared && state == pBinding->eventCount)
    {
        return std::nullopt;
    }

    if (state >= pBinding->eventCount)
    {
        state = 0;
    }

    return static_cast<uint16_t>(pBinding->baseEventId + state);
}

std::optional<std::string> OutdoorInteractionController::resolveInteractiveDecorationHoverText(
    const OutdoorGameView &view,
    size_t entityIndex)
{
    const std::optional<uint16_t> eventId = resolveInteractiveDecorationEventId(view, entityIndex);

    if (!eventId)
    {
        return std::nullopt;
    }

    const std::optional<NpcDialogTable::ResolvedTopic> topic = view.data().npcDialogTable().getTopicById(*eventId);

    if (!topic || topic->topic.empty())
    {
        return std::nullopt;
    }

    return topic->topic;
}

GameplayDialogController::Context OutdoorInteractionController::createGameplayDialogContext(
    OutdoorGameView &view,
    EventRuntimeState &eventRuntimeState,
    const char *reason)
{
    (void)reason;
    GameplayScreenRuntime &screenRuntime = view.m_gameSession.gameplayScreenRuntime();

    return buildGameplayDialogContext(
        view.m_gameSession.gameplayUiController(),
        eventRuntimeState,
        screenRuntime.activeEventDialog(),
        screenRuntime.eventDialogSelectionIndex(),
        view.m_pOutdoorPartyRuntime != nullptr ? &view.m_pOutdoorPartyRuntime->party() : nullptr,
        view.m_pOutdoorWorldRuntime,
        view.m_pOutdoorSceneRuntime != nullptr ? &view.m_pOutdoorSceneRuntime->globalEventProgram() : nullptr,
        &view.data().houseTable(),
        &view.data().classSkillTable(),
        &view.data().npcDialogTable(),
        &view.data().transitionTable(),
        view.m_map ? &*view.m_map : nullptr,
        &view.data().mapEntries(),
        &view.data().rosterTable(),
        &view.data().arcomageLibrary(),
        resolveGameplayHudScreenState(
            view.m_gameSession.gameplayUiController(),
            screenRuntime.activeEventDialog(),
            view.m_pOutdoorWorldRuntime)
            == GameplayHudScreenState::Dialogue,
        &screenRuntime);
}

void OutdoorInteractionController::executeActiveDialogAction(OutdoorGameView &view)
{
    GameplayScreenRuntime &screenRuntime = view.m_gameSession.gameplayScreenRuntime();
    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    const std::optional<EventDialogAction> selectedAction =
        screenRuntime.activeEventDialog().isActive
            && screenRuntime.eventDialogSelectionIndex() < screenRuntime.activeEventDialog().actions.size()
        ? std::optional<EventDialogAction>(
            screenRuntime.activeEventDialog().actions[screenRuntime.eventDialogSelectionIndex()])
        : std::nullopt;
    Party *pParty = view.m_pOutdoorPartyRuntime != nullptr ? &view.m_pOutdoorPartyRuntime->party() : nullptr;
    const int initialGold = pParty != nullptr ? pParty->gold() : 0;
    screenRuntime.executeActiveDialogAction(
        [&view](EventRuntimeState &eventRuntimeState)
        {
            return createGameplayDialogContext(view, eventRuntimeState, "execute_active_dialog_action");
        },
        [&view, pEventRuntimeState, selectedAction, initialGold, pParty](const GameplayDialogController::Result &result)
        {
            (void)result;

            const bool useHouseTradeItemReaction =
                shouldUseHouseTradeItemReaction(*pEventRuntimeState, selectedAction, initialGold, pParty);

            if (useHouseTradeItemReaction)
            {
                if (pParty != nullptr)
                {
                    view.m_gameSession.gameplayScreenRuntime().triggerPortraitFaceAnimation(
                        pParty->activeMemberIndex(),
                        FaceAnimationId::ItemSold);
                }
            }

            OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(view);
        },
        [&view]()
        {
            OutdoorInteractionController::closeActiveEventDialog(view);
        },
        [&view](const GameplayDialogController::Result &result)
        {
            if (result.pendingInnRest.has_value())
            {
                view.m_gameSession.gameplayScreenRuntime().startInnRest(
                    view.innRestDurationMinutes(result.pendingInnRest->houseId));
            }
        },
        [&view](size_t previousMessageCount, bool allowNpcFallbackContent)
        {
            OutdoorInteractionController::presentPendingEventDialog(
                view,
                previousMessageCount,
                allowNpcFallbackContent);
        });
}



void OutdoorInteractionController::presentPendingEventDialog(
    OutdoorGameView &view,
    size_t previousMessageCount,
    bool allowNpcFallbackContent)
{
    GameplayScreenRuntime &screenRuntime = view.m_gameSession.gameplayScreenRuntime();

    screenRuntime.presentPendingEventDialog(
        previousMessageCount,
        allowNpcFallbackContent,
        [&view](EventRuntimeState &eventRuntimeState)
        {
            return createGameplayDialogContext(view, eventRuntimeState, "present_pending_event_dialog");
        },
        [&view](const GameplayDialogController::PresentPendingDialogResult &result)
        {
            if (!result.wasDialogAlreadyActive
                && (result.resolvedContext.kind == DialogueContextKind::NpcTalk
                    || result.resolvedContext.kind == DialogueContextKind::NpcNews)
                && result.resolvedContext.sourceId != 0
                && view.m_pOutdoorPartyRuntime != nullptr)
            {
                const size_t activeMemberIndex = view.m_pOutdoorPartyRuntime->party().activeMemberIndex();
                const int currentHour =
                    view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->currentHour() : -1;
                const SpeechId greetingSpeechId =
                    currentHour >= 0 && (currentHour < 5 || currentHour > 21)
                        ? SpeechId::HelloEvening
                        : SpeechId::HelloDay;
                view.m_gameSession.gameplayScreenRuntime().playSpeechReaction(activeMemberIndex, greetingSpeechId, true);
            }
        });
}



void OutdoorInteractionController::closeActiveEventDialog(OutdoorGameView &view)
{
    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState != nullptr)
    {
        pEventRuntimeState->grantedItems.clear();
        pEventRuntimeState->grantedItemIds.clear();
    }

    const uint32_t hostHouseId = view.m_gameSession.gameplayScreenRuntime().closeActiveEventDialog();

    if (hostHouseId != 0 && view.m_flipOnExitEnabled)
    {
        view.setCameraAngles(view.cameraYawRadians() + Pi, view.cameraPitchRadians());
    }
}

bool OutdoorInteractionController::requestTravelAutosave(OutdoorGameView &view)
{
    if (!view.m_gameSession.canSaveGameToPath())
    {
        return false;
    }

    std::string error;

    if (!view.m_gameSession.saveGameToPath(view.m_autosavePath, "", {}, error))
    {
        return false;
    }

    view.m_gameSession.gameplayScreenRuntime().refreshSaveGameOverlaySlots();
    return true;
}

void OutdoorInteractionController::cancelPendingMapTransition(OutdoorGameView &view)
{
    if (!view.m_map.has_value() || view.m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    const MapBounds &bounds = view.m_map->outdoorBounds;

    if (!bounds.enabled)
    {
        return;
    }

    constexpr float CancelClampInset = 1.0f;
    const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
    const float clampedX = std::clamp(
        moveState.x,
        static_cast<float>(bounds.minX) + CancelClampInset,
        static_cast<float>(bounds.maxX) - CancelClampInset);
    const float clampedY = std::clamp(
        moveState.y,
        static_cast<float>(bounds.minY) + CancelClampInset,
        static_cast<float>(bounds.maxY) - CancelClampInset);

    if (clampedX == moveState.x && clampedY == moveState.y)
    {
        return;
    }

    view.m_pOutdoorPartyRuntime->teleportTo(clampedX, clampedY, moveState.footZ);
    view.m_cameraTargetX = clampedX;
    view.m_cameraTargetY = clampedY;
    view.m_cameraTargetZ = moveState.footZ + view.m_cameraEyeHeight;
}

bool OutdoorInteractionController::executeNpcTopicEvent(
    OutdoorGameView &view,
    uint16_t eventId,
    size_t &previousMessageCount,
    std::optional<uint8_t> continueStep)
{
    return view.m_pOutdoorSceneRuntime != nullptr
        && view.m_pOutdoorSceneRuntime->executeNpcTopicEventById(eventId, previousMessageCount, continueStep);
}



std::optional<std::string> OutdoorInteractionController::resolveEventHintText(
    const OutdoorGameView &view,
    uint16_t eventId)
{
    if (eventId == 0)
    {
        return std::nullopt;
    }

    if (view.m_pOutdoorSceneRuntime != nullptr)
    {
        const std::optional<ScriptedEventProgram> &localEventProgram = view.m_pOutdoorSceneRuntime->localEventProgram();

        if (localEventProgram)
        {
            const std::optional<std::string> hint = localEventProgram->getHint(eventId);

            if (hint && !hint->empty())
            {
                return hint;
            }
        }

        const std::optional<ScriptedEventProgram> &globalEventProgram = view.m_pOutdoorSceneRuntime->globalEventProgram();

        if (globalEventProgram)
        {
            const std::optional<std::string> hint = globalEventProgram->getHint(eventId);

            if (hint && !hint->empty())
            {
                return hint;
            }
        }
    }

    return std::nullopt;
}



std::optional<std::string> OutdoorInteractionController::resolveEventTargetHoverStatusText(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (!inspectHit.hasHit)
    {
        return std::nullopt;
    }

    if (inspectHit.kind == "decoration")
    {
        if (!view.m_outdoorDecorationBillboardSet
            || inspectHit.bModelIndex >= view.m_outdoorDecorationBillboardSet->billboards.size())
        {
            return std::nullopt;
        }

        const DecorationBillboard &decoration =
            view.m_outdoorDecorationBillboardSet->billboards[inspectHit.bModelIndex];

        if (const std::optional<std::string> interactiveText =
                resolveInteractiveDecorationHoverText(view, decoration.entityIndex))
        {
            return interactiveText;
        }

        std::optional<uint16_t> directEventId;

        if (view.m_outdoorMapData && decoration.entityIndex < view.m_outdoorMapData->entities.size())
        {
            const OutdoorEntity &entity = view.m_outdoorMapData->entities[decoration.entityIndex];
            directEventId = entity.eventIdPrimary != 0 ? entity.eventIdPrimary : entity.eventIdSecondary;
        }

        if (directEventId)
        {
            const std::optional<std::string> directEventHint = resolveEventHintText(view, *directEventId);

            if (directEventHint && !directEventHint->empty())
            {
                return directEventHint;
            }
        }

        const DecorationEntry *pDecorationEntry =
            view.m_outdoorDecorationBillboardSet->decorationTable.get(decoration.decorationId);

        if ((pDecorationEntry == nullptr || pDecorationEntry->hint.empty()) && !decoration.name.empty())
        {
            pDecorationEntry =
                view.m_outdoorDecorationBillboardSet->decorationTable.findByInternalName(decoration.name);
        }

        if (pDecorationEntry != nullptr && !pDecorationEntry->hint.empty())
        {
            return pDecorationEntry->hint;
        }

        return std::nullopt;
    }

    if (inspectHit.kind == "entity")
    {
        if (const std::optional<std::string> interactiveText =
                resolveInteractiveDecorationHoverText(view, inspectHit.bModelIndex))
        {
            return interactiveText;
        }

        const std::optional<std::string> primaryHint = resolveEventHintText(view, inspectHit.eventIdPrimary);

        if (primaryHint && !primaryHint->empty())
        {
            return primaryHint;
        }

        return resolveEventHintText(view, inspectHit.eventIdSecondary);
    }

    if (inspectHit.kind == "face")
    {
        return resolveEventHintText(view, inspectHit.cogTriggeredNumber);
    }

    return std::nullopt;
}

GameplayWorldHit OutdoorInteractionController::translateInspectHitToGameplayWorldHit(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    GameplayWorldHit worldHit = {};

    if (!inspectHit.hasHit)
    {
        return worldHit;
    }

    const bx::Vec3 hitPoint = {inspectHit.hitX, inspectHit.hitY, inspectHit.hitZ};
    worldHit.hasHit = true;

    if (inspectHit.kind == "actor")
    {
        worldHit.kind = GameplayWorldHitKind::Actor;

        GameplayActorTargetHit actorHit = {};
        const std::optional<size_t> actorIndex = resolveRuntimeActorIndexForInspectHit(view, inspectHit);
        actorHit.actorIndex = actorIndex.value_or(GameplayInvalidWorldIndex);
        actorHit.displayName = inspectHit.name;
        actorHit.isFriendly = inspectHit.isFriendly;
        actorHit.npcId = inspectHit.npcId;
        actorHit.actorGroup = inspectHit.actorGroup;
        actorHit.hitPoint = hitPoint;
        actorHit.distance = inspectHit.distance;
        worldHit.actor = actorHit;
        return worldHit;
    }

    if (inspectHit.kind == "world_item")
    {
        worldHit.kind = GameplayWorldHitKind::WorldItem;

        GameplayWorldItemTargetHit worldItemHit = {};
        worldItemHit.worldItemIndex = inspectHit.bModelIndex;
        worldItemHit.objectDescriptionId = inspectHit.objectDescriptionId;
        worldItemHit.objectSpriteId = inspectHit.objectSpriteId;
        worldItemHit.hitPoint = hitPoint;
        worldItemHit.distance = inspectHit.distance;
        worldHit.worldItem = worldItemHit;
        return worldHit;
    }

    if (inspectHit.kind == "chest" || inspectHit.kind == "corpse")
    {
        const bool isChest = inspectHit.kind == "chest";
        worldHit.kind = isChest ? GameplayWorldHitKind::Chest : GameplayWorldHitKind::Corpse;

        GameplayContainerTargetHit containerHit = {};
        containerHit.sourceKind =
            isChest ? GameplayWorldContainerSourceKind::Chest : GameplayWorldContainerSourceKind::Corpse;
        containerHit.sourceIndex = inspectHit.bModelIndex;
        containerHit.distance = inspectHit.distance;
        worldHit.container = containerHit;
        return worldHit;
    }

    if (inspectHit.kind == "terrain")
    {
        worldHit.kind = GameplayWorldHitKind::Ground;

        GameplayGroundTargetHit groundHit = {};
        groundHit.worldPoint = hitPoint;
        groundHit.distance = inspectHit.distance;
        groundHit.isValid = true;
        worldHit.ground = groundHit;
        return worldHit;
    }

    if (inspectHit.kind == "object")
    {
        worldHit.kind = GameplayWorldHitKind::Object;

        GameplayObjectTargetHit objectHit = {};
        objectHit.objectIndex = inspectHit.bModelIndex;
        objectHit.objectDescriptionId = inspectHit.objectDescriptionId;
        objectHit.objectSpriteId = inspectHit.objectSpriteId;
        objectHit.spellId = inspectHit.spellId;
        objectHit.hitPoint = hitPoint;
        objectHit.distance = inspectHit.distance;
        worldHit.object = objectHit;
        return worldHit;
    }

    GameplayEventTargetHit eventTargetHit = {};
    eventTargetHit.targetIndex = inspectHit.bModelIndex;
    eventTargetHit.secondaryIndex = inspectHit.faceIndex;
    eventTargetHit.eventIdPrimary = inspectHit.eventIdPrimary;
    eventTargetHit.eventIdSecondary = inspectHit.eventIdSecondary;
    eventTargetHit.triggeredEventId = inspectHit.cogTriggeredNumber;
    eventTargetHit.trigger = inspectHit.cogTrigger;
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
    }
    else if (inspectHit.kind == "entity")
    {
        eventTargetHit.targetKind = GameplayWorldEventTargetKind::Entity;
    }
    else if (inspectHit.kind == "decoration")
    {
        eventTargetHit.targetKind = GameplayWorldEventTargetKind::Decoration;
    }
    else if (inspectHit.kind == "spawn")
    {
        eventTargetHit.targetKind = GameplayWorldEventTargetKind::Spawn;
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

GameplayHoverStatusPayload OutdoorInteractionController::resolveGameplayHoverStatusPayload(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    const GameplayWorldHit worldHit = translateInspectHitToGameplayWorldHit(view, inspectHit);

    GameplayHoverStatusPayload payload = {};
    payload.worldHit = worldHit;
    payload.eventTargetStatusText = resolveEventTargetHoverStatusText(view, inspectHit);
    return payload;
}

GameplayWorldHoverCacheState OutdoorInteractionController::worldHoverCacheState(const OutdoorGameView &view)
{
    return GameplayWorldHoverCacheState{
        .hasCachedHover = view.m_cachedHoverInspectHitValid,
        .lastUpdateNanoseconds = view.m_lastHoverInspectUpdateNanoseconds,
    };
}

void OutdoorInteractionController::clearWorldHover(OutdoorGameView &view)
{
    view.m_cachedHoverInspectHitValid = false;
    view.m_cachedHoverInspectHit = {};
}

GameplayWorldPickRequest OutdoorInteractionController::buildWorldPickRequest(
    const OutdoorGameView &view,
    const GameplayWorldPickRequestInput &input)
{
    const uint16_t viewWidth = static_cast<uint16_t>(std::max(input.screenWidth, 1));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(input.screenHeight, 1));
    const float aspectRatio = static_cast<float>(viewWidth) / static_cast<float>(viewHeight);
    const float cameraYawRadians = view.effectiveCameraYawRadians();
    const float cameraPitchRadians = view.effectiveCameraPitchRadians();
    const float cosPitch = std::cos(cameraPitchRadians);
    const float sinPitch = std::sin(cameraPitchRadians);
    const float cosYaw = std::cos(cameraYawRadians);
    const float sinYaw = std::sin(cameraYawRadians);
    const bx::Vec3 eye = {
        view.m_cameraTargetX,
        view.m_cameraTargetY,
        view.m_cameraTargetZ
    };
    const bx::Vec3 at = {
        view.m_cameraTargetX + cosYaw * cosPitch,
        view.m_cameraTargetY + sinYaw * cosPitch,
        view.m_cameraTargetZ + sinPitch
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};
    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};

    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        CameraVerticalFovDegrees,
        aspectRatio,
        0.1f,
        DefaultOutdoorFarClip,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right
    );

    GameplayWorldPickRequest pickRequest = {};
    pickRequest.screenX = input.screenX;
    pickRequest.screenY = input.screenY;
    pickRequest.viewWidth = viewWidth;
    pickRequest.viewHeight = viewHeight;
    pickRequest.eye = eye;
    std::copy(std::begin(viewMatrix), std::end(viewMatrix), pickRequest.viewMatrix.begin());
    std::copy(std::begin(projectionMatrix), std::end(projectionMatrix), pickRequest.projectionMatrix.begin());

    if (input.includeRay)
    {
        pickRequest.hasRay =
            buildInspectRayForScreenPoint(
                input.screenX,
                input.screenY,
                viewWidth,
                viewHeight,
                viewMatrix,
                projectionMatrix,
                pickRequest.rayOrigin,
                pickRequest.rayDirection);

        if (!pickRequest.hasRay)
        {
            pickRequest.rayOrigin = {0.0f, 0.0f, 0.0f};
            pickRequest.rayDirection = {0.0f, 0.0f, 0.0f};
        }
    }

    return pickRequest;
}

bool OutdoorInteractionController::worldInspectModeActive(const OutdoorGameView &view)
{
    return view.m_isInitialized && view.m_pOutdoorWorldRuntime != nullptr && view.m_outdoorMapData.has_value();
}

std::optional<GameplayHeldItemDropRequest> OutdoorInteractionController::buildHeldItemDropRequest(
    const OutdoorGameView &view)
{
    if (view.m_pOutdoorPartyRuntime == nullptr)
    {
        return std::nullopt;
    }

    const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
    return GameplayHeldItemDropRequest{
        .sourceX = moveState.x,
        .sourceY = moveState.y,
        .sourceZ = moveState.footZ + view.m_cameraEyeHeight,
        .yawRadians = view.m_cameraYawRadians,
    };
}

GameplayPartyAttackFrameInput OutdoorInteractionController::buildPartyAttackFrameInput(
    const OutdoorGameView &view,
    const GameplayWorldPickRequest &pickRequest)
{
    if (view.m_pOutdoorPartyRuntime == nullptr)
    {
        return {};
    }

    const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
    const float attackSourceX = moveState.x;
    const float attackSourceY = moveState.y;
    const float attackSourceZ = moveState.footZ + 96.0f;
    const float attackCameraYawRadians = view.effectiveCameraYawRadians();
    const float attackCameraPitchRadians = view.effectiveCameraPitchRadians();
    const float attackRightX = -std::sin(attackCameraYawRadians);
    const float attackRightY = std::cos(attackCameraYawRadians);

    GameplayPartyAttackFrameInput input = {};
    input.enabled = true;
    input.partyPosition =
        GameplayWorldPoint{
            .x = moveState.x,
            .y = moveState.y,
            .z = moveState.footZ,
        };
    input.rangedSource =
        GameplayWorldPoint{
            .x = attackSourceX,
            .y = attackSourceY,
            .z = attackSourceZ,
        };
    input.rangedRight =
        GameplayWorldPoint{
            .x = attackRightX,
            .y = attackRightY,
            .z = 0.0f,
        };
    input.defaultRangedTarget =
        GameplayWorldPoint{
            .x = attackSourceX + std::cos(attackCameraYawRadians) * 5120.0f,
            .y = attackSourceY + std::sin(attackCameraYawRadians) * 5120.0f,
            .z = attackSourceZ + std::sin(attackCameraPitchRadians) * 5120.0f,
        };
    input.hasRayRangedTarget = pickRequest.hasRay && vecLength(pickRequest.rayDirection) > InspectRayEpsilon;
    input.rayRangedTarget =
        GameplayWorldPoint{
            .x = pickRequest.rayOrigin.x + pickRequest.rayDirection.x * 5120.0f,
            .y = pickRequest.rayOrigin.y + pickRequest.rayDirection.y * 5120.0f,
            .z = pickRequest.rayOrigin.z + pickRequest.rayDirection.z * 5120.0f,
        };
    std::copy(
        pickRequest.viewMatrix.begin(),
        pickRequest.viewMatrix.end(),
        input.fallbackQuery.viewMatrix.begin());
    std::copy(
        pickRequest.projectionMatrix.begin(),
        pickRequest.projectionMatrix.end(),
        input.fallbackQuery.projectionMatrix.begin());
    return input;
}

GameplayHoverStatusPayload OutdoorInteractionController::readCachedWorldHover(OutdoorGameView &view)
{
    return resolveGameplayHoverStatusPayload(view, view.m_cachedHoverInspectHit);
}

GameplayHoverStatusPayload OutdoorInteractionController::refreshWorldHover(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const GameplayWorldHoverRequest &request)
{
    const auto inspectHoverPoint =
        [&view, &outdoorMapData](const GameplayWorldPickRequest &pickRequest, OutdoorGameView::InspectHit &inspectHit)
            -> bool
        {
            bx::Vec3 hoverRayOrigin = {0.0f, 0.0f, 0.0f};
            bx::Vec3 hoverRayDirection = {0.0f, 0.0f, 0.0f};

            if (!buildInspectRayForScreenPoint(
                    pickRequest.screenX,
                    pickRequest.screenY,
                    pickRequest.viewWidth,
                    pickRequest.viewHeight,
                    pickRequest.viewMatrix.data(),
                    pickRequest.projectionMatrix.data(),
                    hoverRayOrigin,
                    hoverRayDirection))
            {
                return false;
            }

            inspectHit = inspectBModelFace(
                view,
                outdoorMapData,
                hoverRayOrigin,
                hoverRayDirection,
                pickRequest.screenX,
                pickRequest.screenY,
                pickRequest.viewWidth,
                pickRequest.viewHeight,
                pickRequest.viewMatrix.data(),
                pickRequest.projectionMatrix.data(),
                OutdoorGameView::DecorationPickMode::HoverInfo);
            return true;
        };
    const auto prefersTargetOutline =
        [](const OutdoorGameView::InspectHit &inspectHit)
        {
            return inspectHit.hasHit && (inspectHit.kind == "actor" || inspectHit.kind == "world_item");
        };

    if (request.probeKind == GameplayWorldHoverProbeKind::PendingSpell)
    {
        OutdoorGameView::InspectHit primaryInspectHit = {};
        OutdoorGameView::InspectHit secondaryInspectHit = {};
        const bool hasPrimaryInspectHit = inspectHoverPoint(request.primaryPickRequest, primaryInspectHit);
        const bool hasSecondaryInspectHit =
            request.secondaryPickRequest
            && inspectHoverPoint(*request.secondaryPickRequest, secondaryInspectHit);

        if (prefersTargetOutline(secondaryInspectHit)
            && (!prefersTargetOutline(primaryInspectHit)
                || secondaryInspectHit.distance <= primaryInspectHit.distance))
        {
            view.m_cachedHoverInspectHit = secondaryInspectHit;
            view.m_cachedHoverInspectHitValid = hasSecondaryInspectHit;
        }
        else
        {
            view.m_cachedHoverInspectHit = primaryInspectHit;
            view.m_cachedHoverInspectHitValid = hasPrimaryInspectHit;
        }

        if (!hasPrimaryInspectHit && !hasSecondaryInspectHit)
        {
            clearWorldHover(view);
        }

        view.m_lastHoverInspectUpdateNanoseconds = request.updateTickNanoseconds;
        return resolveGameplayHoverStatusPayload(view, view.m_cachedHoverInspectHit);
    }

    view.m_cachedHoverInspectHit = inspectBModelFace(
        view,
        outdoorMapData,
        request.primaryPickRequest.rayOrigin,
        request.primaryPickRequest.rayDirection,
        request.primaryPickRequest.screenX,
        request.primaryPickRequest.screenY,
        request.primaryPickRequest.viewWidth,
        request.primaryPickRequest.viewHeight,
        request.primaryPickRequest.viewMatrix.data(),
        request.primaryPickRequest.projectionMatrix.data(),
        OutdoorGameView::DecorationPickMode::HoverInfo);
    view.m_cachedHoverInspectHitValid = true;
    view.m_lastHoverInspectUpdateNanoseconds = request.updateTickNanoseconds;
    return resolveGameplayHoverStatusPayload(view, view.m_cachedHoverInspectHit);
}

GameplayPendingSpellWorldTargetFacts OutdoorInteractionController::pickPendingSpellWorldTarget(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const GameplayWorldPickRequest &request)
{
    GameplayPendingSpellWorldTargetFacts targetFacts = {};
    OutdoorGameView::InspectHit inspectHit = {};
    std::optional<bx::Vec3> groundTargetPoint;
    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (buildInspectRayForScreenPoint(
            request.screenX,
            request.screenY,
            request.viewWidth,
            request.viewHeight,
            request.viewMatrix.data(),
            request.projectionMatrix.data(),
            rayOrigin,
            rayDirection))
    {
        inspectHit = inspectBModelFace(
            view,
            outdoorMapData,
            rayOrigin,
            rayDirection,
            request.screenX,
            request.screenY,
            request.viewWidth,
            request.viewHeight,
            request.viewMatrix.data(),
            request.projectionMatrix.data(),
            OutdoorGameView::DecorationPickMode::Interaction);

        const std::optional<float> terrainDistance =
            intersectOutdoorTerrainRay(outdoorMapData, rayOrigin, rayDirection);

        if (terrainDistance)
        {
            groundTargetPoint = bx::Vec3{
                rayOrigin.x + rayDirection.x * *terrainDistance,
                rayOrigin.y + rayDirection.y * *terrainDistance,
                rayOrigin.z + rayDirection.z * *terrainDistance
            };
        }
    }

    targetFacts.worldHit = translateInspectHitToGameplayWorldHit(view, inspectHit);
    targetFacts.fallbackGroundTargetPoint =
        groundTargetPoint ? groundTargetPoint : resolveSpellActionForwardGroundTargetPoint(view);
    return targetFacts;
}

GameplayWorldHit OutdoorInteractionController::pickKeyboardInteractionTarget(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const GameplayWorldPickRequest &request)
{
    OutdoorBillboardRenderer::prepareKeyboardInteractionBillboardCache(
        view,
        request.viewWidth,
        request.viewHeight,
        request.viewMatrix.data(),
        request.projectionMatrix.data(),
        request.eye);

    const OutdoorGameView::InspectHit inspectHit = pickKeyboardInteractionInspectHit(
        view,
        outdoorMapData,
        request.viewWidth,
        request.viewHeight,
        request.viewMatrix.data(),
        request.projectionMatrix.data());

    return translateInspectHitToGameplayWorldHit(view, inspectHit);
}

GameplayWorldHit OutdoorInteractionController::pickHeldItemWorldTarget(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const GameplayWorldPickRequest &request)
{
    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!buildInspectRayForScreenPoint(
            request.screenX,
            request.screenY,
            request.viewWidth,
            request.viewHeight,
            request.viewMatrix.data(),
            request.projectionMatrix.data(),
            rayOrigin,
            rayDirection))
    {
        return {};
    }

    const OutdoorGameView::InspectHit inspectHit = inspectBModelFace(
        view,
        outdoorMapData,
        rayOrigin,
        rayDirection,
        request.screenX,
        request.screenY,
        request.viewWidth,
        request.viewHeight,
        request.viewMatrix.data(),
        request.projectionMatrix.data(),
        OutdoorGameView::DecorationPickMode::Interaction,
        FacePickMode::InteractionActivatable);

    return translateInspectHitToGameplayWorldHit(view, inspectHit);
}

GameplayWorldHit OutdoorInteractionController::pickCurrentInteractionTarget(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const GameplayWorldPickRequest &request)
{
    bx::Vec3 rayOrigin = request.rayOrigin;
    bx::Vec3 rayDirection = request.rayDirection;

    if (!request.hasRay
        && !buildInspectRayForScreenPoint(
            request.screenX,
            request.screenY,
            request.viewWidth,
            request.viewHeight,
            request.viewMatrix.data(),
            request.projectionMatrix.data(),
            rayOrigin,
            rayDirection))
    {
        return {};
    }

    const OutdoorGameView::InspectHit inspectHit = inspectBModelFace(
        view,
        outdoorMapData,
        rayOrigin,
        rayDirection,
        request.screenX,
        request.screenY,
        request.viewWidth,
        request.viewHeight,
        request.viewMatrix.data(),
        request.projectionMatrix.data(),
        OutdoorGameView::DecorationPickMode::Interaction,
        FacePickMode::InteractionActivatable);

    return translateInspectHitToGameplayWorldHit(view, inspectHit);
}

std::optional<bx::Vec3> OutdoorInteractionController::resolveSpellActionForwardGroundTargetPoint(
    const OutdoorGameView &view)
{
    if (view.m_outdoorMapData.has_value())
    {
        const bx::Vec3 rayOrigin = {
            view.m_cameraTargetX,
            view.m_cameraTargetY,
            view.m_cameraTargetZ
        };
        const float cameraYawRadians = view.effectiveCameraYawRadians();
        const float cameraPitchRadians = view.effectiveCameraPitchRadians();
        const float cosPitch = std::cos(cameraPitchRadians);
        const bx::Vec3 rayDirection = {
            std::cos(cameraYawRadians) * cosPitch,
            std::sin(cameraYawRadians) * cosPitch,
            std::sin(cameraPitchRadians)
        };
        const std::optional<float> terrainDistance =
            intersectOutdoorTerrainRay(*view.m_outdoorMapData, rayOrigin, rayDirection);

        if (terrainDistance)
        {
            return bx::Vec3 {
                rayOrigin.x + rayDirection.x * *terrainDistance,
                rayOrigin.y + rayDirection.y * *terrainDistance,
                rayOrigin.z + rayDirection.z * *terrainDistance
            };
        }
    }

    return std::nullopt;
}

std::optional<size_t> OutdoorInteractionController::resolveRuntimeActorIndexForInspectHit(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind != "actor" || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    if (inspectHit.runtimeActorIndex != static_cast<size_t>(-1)
        && inspectHit.runtimeActorIndex < view.m_pOutdoorWorldRuntime->mapActorCount())
    {
        return inspectHit.runtimeActorIndex;
    }

    if (view.m_outdoorActorPreviewBillboardSet
        && inspectHit.bModelIndex < view.m_outdoorActorPreviewBillboardSet->billboards.size())
    {
        const ActorPreviewBillboard &billboard =
            view.m_outdoorActorPreviewBillboardSet->billboards[inspectHit.bModelIndex];

        if (billboard.runtimeActorIndex != static_cast<size_t>(-1))
        {
            return billboard.runtimeActorIndex;
        }
    }

    return inspectHit.bModelIndex < view.m_pOutdoorWorldRuntime->mapActorCount()
        ? std::optional<size_t>(inspectHit.bModelIndex)
        : std::nullopt;
}

bool OutdoorInteractionController::inspectHitTargetsLivingHostileActor(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind != "actor" || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return false;
    }

    const std::optional<size_t> runtimeActorIndex = resolveRuntimeActorIndexForInspectHit(view, inspectHit);

    if (!runtimeActorIndex)
    {
        return false;
    }

    const OutdoorWorldRuntime::MapActorState *pActorState =
        view.m_pOutdoorWorldRuntime->mapActorState(*runtimeActorIndex);

    return pActorState != nullptr && !pActorState->isDead && pActorState->hostileToParty;
}

void OutdoorInteractionController::handleDialogueCloseRequest(OutdoorGameView &view)
{
    view.m_gameSession.gameplayScreenRuntime().handleDialogueCloseRequest();
}



void OutdoorInteractionController::openDebugNpcDialogue(OutdoorGameView &view, uint32_t npcId)
{
    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr || npcId == 0)
    {
        return;
    }

    GameplayDialogController::Context context = createGameplayDialogContext(view, *pEventRuntimeState, "open_debug_npc_dialogue");
    const GameplayDialogController::Result result =
        view.m_gameSession.gameplayDialogController().openNpcDialogue(context, npcId);
    pEventRuntimeState->lastActivationResult = "debug npc " + std::to_string(npcId) + " engaged";

    if (result.shouldOpenPendingEventDialog)
    {
        OutdoorInteractionController::presentPendingEventDialog(view, result.previousMessageCount, result.allowNpcFallbackContent);
    }
}

void OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(OutdoorGameView &view)
{
    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr
        || (pEventRuntimeState->grantedItems.empty() && pEventRuntimeState->grantedItemIds.empty())
        || view.m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    view.syncCursorToGameplayCrosshair();

    GameplayHeldItemController::applyGrantedEventItemsToHeldInventory(
        view.m_gameSession.gameplayScreenRuntime(),
        *pEventRuntimeState,
        view.data().itemTable());
}



const OutdoorBitmapTexture *OutdoorInteractionController::findDecorationBillboardTexture(
    const OutdoorGameView &view,
    const std::string &textureName)
{
    if (!view.m_outdoorDecorationBillboardSet)
    {
        return nullptr;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName);
    const auto it = view.m_decorationBitmapTextureIndexByName.find(normalizedTextureName);

    if (it == view.m_decorationBitmapTextureIndexByName.end())
    {
        return nullptr;
    }

    if (it->second >= view.m_outdoorDecorationBillboardSet->textures.size())
    {
        return nullptr;
    }

    return &view.m_outdoorDecorationBillboardSet->textures[it->second];
}



const OutdoorBitmapTexture *OutdoorInteractionController::findActorBillboardTexture(
    const OutdoorGameView &view,
    const std::string &textureName,
    int16_t paletteId)
{
    if (!view.m_outdoorActorPreviewBillboardSet)
    {
        return nullptr;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const OutdoorBitmapTexture &texture : view.m_outdoorActorPreviewBillboardSet->textures)
    {
        if (texture.textureName == normalizedTextureName && texture.paletteId == paletteId)
        {
            return &texture;
        }
    }

    return nullptr;
}



bool OutdoorInteractionController::hitTestDecorationBillboard(
    OutdoorGameView &view,
    const DecorationBillboard &billboard,
    uint16_t spriteId,
    const OutdoorGameView::BillboardTextureHandle &texture,
    bool mirrored,
    float mouseX,
    float mouseY,
    int viewWidth,
    int viewHeight,
    const float *pViewMatrix,
    const float *pProjectionMatrix,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    float &distance)
{
    if (texture.width <= 0 || texture.height <= 0 || viewWidth <= 0 || viewHeight <= 0)
    {
        return false;
    }

    const uint32_t animationOffsetTicks =
        currentAnimationTicks() + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
    const SpriteFrameEntry *pFrame =
        view.m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(spriteId, animationOffsetTicks);

    if (pFrame == nullptr)
    {
        return false;
    }

    int bitmapWidth = 0;
    int bitmapHeight = 0;
    std::vector<uint8_t> bitmapPixels;
    const OutdoorBitmapTexture *pBitmapTexture = findDecorationBillboardTexture(view, texture.textureName);

    if (pBitmapTexture != nullptr
        && pBitmapTexture->physicalWidth > 0
        && pBitmapTexture->physicalHeight > 0
        && !pBitmapTexture->pixels.empty())
    {
        bitmapWidth = pBitmapTexture->physicalWidth;
        bitmapHeight = pBitmapTexture->physicalHeight;
        bitmapPixels = pBitmapTexture->pixels;
    }
    else
    {
        const std::optional<std::vector<uint8_t>> loadedPixels =
            view.loadSpriteBitmapPixelsBgraCached(texture.textureName, pFrame->paletteId, bitmapWidth, bitmapHeight);

        if (!loadedPixels || bitmapWidth <= 0 || bitmapHeight <= 0)
        {
            return false;
        }

        bitmapPixels = *loadedPixels;
    }

    const float spriteScale = std::max(pFrame->scale, 0.01f);
    const float worldWidth = static_cast<float>(texture.width) * spriteScale;
    const float worldHeight = static_cast<float>(texture.height) * spriteScale;
    const float halfWidth = worldWidth * 0.5f;
    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const bx::Vec3 center = {
        static_cast<float>(billboard.x),
        static_cast<float>(billboard.y),
        static_cast<float>(billboard.z) + worldHeight * 0.5f
    };
    const bx::Vec3 right = {
        cameraRight.x * halfWidth,
        cameraRight.y * halfWidth,
        cameraRight.z * halfWidth
    };
    const bx::Vec3 up = {
        cameraUp.x * worldHeight * 0.5f,
        cameraUp.y * worldHeight * 0.5f,
        cameraUp.z * worldHeight * 0.5f
    };
    const bx::Vec3 topLeft = {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z};
    const bx::Vec3 topRight = {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z};
    const bx::Vec3 bottomLeft = {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z};
    const bx::Vec3 bottomRight = {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z};

    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, pViewMatrix, pProjectionMatrix);
    ProjectedPoint projectedTopLeft = {};
    ProjectedPoint projectedTopRight = {};
    ProjectedPoint projectedBottomLeft = {};
    ProjectedPoint projectedBottomRight = {};

    if (!projectWorldPointToScreen(topLeft, viewWidth, viewHeight, viewProjectionMatrix, projectedTopLeft)
        || !projectWorldPointToScreen(topRight, viewWidth, viewHeight, viewProjectionMatrix, projectedTopRight)
        || !projectWorldPointToScreen(bottomLeft, viewWidth, viewHeight, viewProjectionMatrix, projectedBottomLeft)
        || !projectWorldPointToScreen(bottomRight, viewWidth, viewHeight, viewProjectionMatrix, projectedBottomRight))
    {
        return false;
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
    const float screenWidthPixels = rightEdge - left;
    const float screenHeightPixels = bottom - top;

    if (mouseX < left || mouseX > rightEdge || mouseY < top || mouseY > bottom)
    {
        return false;
    }

    if (screenWidthPixels >= 5.0f && screenHeightPixels >= 5.0f)
    {
        float normalizedU = (mouseX - left) / screenWidthPixels;
        const float normalizedV = (mouseY - top) / screenHeightPixels;

        if (mirrored)
        {
            normalizedU = 1.0f - normalizedU;
        }

        const int pixelX = std::clamp(
            static_cast<int>(std::floor(normalizedU * static_cast<float>(bitmapWidth))),
            0,
            bitmapWidth - 1);
        const int pixelY = std::clamp(
            static_cast<int>(std::floor(normalizedV * static_cast<float>(bitmapHeight))),
            0,
            bitmapHeight - 1);
        const size_t pixelOffset = static_cast<size_t>((pixelY * bitmapWidth + pixelX) * 4);

        if (pixelOffset + 3 >= bitmapPixels.size() || bitmapPixels[pixelOffset + 3] == 0)
        {
            return false;
        }
    }

    const bx::Vec3 planeNormal = {-cameraRight.y * cameraUp.z + cameraRight.z * cameraUp.y,
                                  -cameraRight.z * cameraUp.x + cameraRight.x * cameraUp.z,
                                  -cameraRight.x * cameraUp.y + cameraRight.y * cameraUp.x};
    const float denominator = vecDot(rayDirection, planeNormal);

    if (std::fabs(denominator) <= InspectRayEpsilon)
    {
        return false;
    }

    distance = vecDot(vecSubtract(center, rayOrigin), planeNormal) / denominator;
    return distance > InspectRayEpsilon;
}



bool OutdoorInteractionController::hitTestActorBillboard(
    const OutdoorGameView &view,
    const OutdoorWorldRuntime::MapActorState *pRuntimeActor,
    int actorX,
    int actorY,
    int actorZ,
    uint16_t actorHeight,
    uint16_t sourceBillboardHeight,
    uint16_t spriteFrameIndex,
    const std::array<uint16_t, 8> &actionSpriteFrameIndices,
    bool useStaticFrame,
    float mouseX,
    float mouseY,
    int viewWidth,
    int viewHeight,
    const float *pViewMatrix,
    const float *pProjectionMatrix,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    float &distance,
    bool &usedBillboardHit)
{
    usedBillboardHit = false;

    if (!view.m_outdoorActorPreviewBillboardSet
        || spriteFrameIndex == 0
        || viewWidth <= 0
        || viewHeight <= 0
        || pViewMatrix == nullptr
        || pProjectionMatrix == nullptr)
    {
        return false;
    }

    const float heightScale =
        pRuntimeActor != nullptr && sourceBillboardHeight > 0
            ? static_cast<float>(actorHeight) / static_cast<float>(sourceBillboardHeight)
            : 1.0f;
    uint32_t frameTimeTicks = useStaticFrame ? 0U : currentAnimationTicks();

    if (pRuntimeActor != nullptr)
    {
        const size_t animationIndex = static_cast<size_t>(pRuntimeActor->animation);

        if (animationIndex < actionSpriteFrameIndices.size() && actionSpriteFrameIndices[animationIndex] != 0)
        {
            spriteFrameIndex = actionSpriteFrameIndices[animationIndex];
        }

        frameTimeTicks = static_cast<uint32_t>(std::max(0.0f, pRuntimeActor->animationTimeTicks));
    }

    const SpriteFrameEntry *pFrame = view.m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(
        spriteFrameIndex,
        frameTimeTicks);

    if (pFrame == nullptr)
    {
        return false;
    }

    const bx::Vec3 cameraPosition = {
        view.m_cameraTargetX,
        view.m_cameraTargetY,
        view.m_cameraTargetZ
    };
    const float angleToCamera = std::atan2(
        static_cast<float>(actorY) - cameraPosition.y,
        static_cast<float>(actorX) - cameraPosition.x);
    const float actorYaw = pRuntimeActor != nullptr ? pRuntimeActor->yawRadians : 0.0f;
    const float octantAngle = actorYaw - angleToCamera + Pi + (Pi / 8.0f);
    const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
    const OutdoorBitmapTexture *pBitmapTexture =
        findActorBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

    if (pBitmapTexture == nullptr || pBitmapTexture->width <= 0 || pBitmapTexture->height <= 0
        || pBitmapTexture->physicalWidth <= 0 || pBitmapTexture->physicalHeight <= 0
        || pBitmapTexture->pixels.empty())
    {
        return false;
    }

    usedBillboardHit = true;

    const float spriteScale = std::max(pFrame->scale * heightScale, 0.01f);
    const float worldWidth = static_cast<float>(pBitmapTexture->width) * spriteScale;
    const float worldHeight = static_cast<float>(pBitmapTexture->height) * spriteScale;
    const float halfWidth = worldWidth * 0.5f;
    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const bx::Vec3 center = {
        static_cast<float>(actorX),
        static_cast<float>(actorY),
        static_cast<float>(actorZ) + worldHeight * 0.5f
    };
    const bx::Vec3 right = {
        cameraRight.x * halfWidth,
        cameraRight.y * halfWidth,
        cameraRight.z * halfWidth
    };
    const bx::Vec3 up = {
        cameraUp.x * worldHeight * 0.5f,
        cameraUp.y * worldHeight * 0.5f,
        cameraUp.z * worldHeight * 0.5f
    };
    const bx::Vec3 topLeft = {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z};
    const bx::Vec3 topRight = {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z};
    const bx::Vec3 bottomLeft = {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z};
    const bx::Vec3 bottomRight = {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z};

    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, pViewMatrix, pProjectionMatrix);
    ProjectedPoint projectedTopLeft = {};
    ProjectedPoint projectedTopRight = {};
    ProjectedPoint projectedBottomLeft = {};
    ProjectedPoint projectedBottomRight = {};

    if (!projectWorldPointToScreen(topLeft, viewWidth, viewHeight, viewProjectionMatrix, projectedTopLeft)
        || !projectWorldPointToScreen(topRight, viewWidth, viewHeight, viewProjectionMatrix, projectedTopRight)
        || !projectWorldPointToScreen(bottomLeft, viewWidth, viewHeight, viewProjectionMatrix, projectedBottomLeft)
        || !projectWorldPointToScreen(bottomRight, viewWidth, viewHeight, viewProjectionMatrix, projectedBottomRight))
    {
        return false;
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
    const float screenWidthPixels = rightEdge - left;
    const float screenHeightPixels = bottom - top;

    if (mouseX < left || mouseX > rightEdge || mouseY < top || mouseY > bottom)
    {
        return false;
    }

    if (screenWidthPixels >= 5.0f && screenHeightPixels >= 5.0f)
    {
        float normalizedU = (mouseX - left) / screenWidthPixels;
        const float normalizedV = (mouseY - top) / screenHeightPixels;

        if (resolvedTexture.mirrored)
        {
            normalizedU = 1.0f - normalizedU;
        }

        const int pixelX = std::clamp(
            static_cast<int>(std::floor(normalizedU * static_cast<float>(pBitmapTexture->physicalWidth))),
            0,
            pBitmapTexture->physicalWidth - 1);
        const int pixelY = std::clamp(
            static_cast<int>(std::floor(normalizedV * static_cast<float>(pBitmapTexture->physicalHeight))),
            0,
            pBitmapTexture->physicalHeight - 1);
        const size_t pixelOffset = static_cast<size_t>(
            (pixelY * pBitmapTexture->physicalWidth + pixelX) * 4);

        if (pixelOffset + 3 >= pBitmapTexture->pixels.size() || pBitmapTexture->pixels[pixelOffset + 3] == 0)
        {
            return false;
        }
    }

    const bx::Vec3 planeNormal = {-cameraRight.y * cameraUp.z + cameraRight.z * cameraUp.y,
                                  -cameraRight.z * cameraUp.x + cameraRight.x * cameraUp.z,
                                  -cameraRight.x * cameraUp.y + cameraRight.y * cameraUp.x};
    const float denominator = vecDot(rayDirection, planeNormal);

    if (std::fabs(denominator) <= InspectRayEpsilon)
    {
        return false;
    }

    distance = vecDot(vecSubtract(center, rayOrigin), planeNormal) / denominator;
    return distance > InspectRayEpsilon;
}



const OutdoorWorldRuntime::MapActorState *OutdoorInteractionController::runtimeActorStateForBillboard(
    const OutdoorGameView &view,
    const ActorPreviewBillboard &billboard
)
{
    if (view.m_pOutdoorWorldRuntime == nullptr || billboard.source != ActorPreviewSource::Companion)
    {
        return nullptr;
    }

    if (billboard.runtimeActorIndex == static_cast<size_t>(-1))
    {
        return nullptr;
    }

    return view.m_pOutdoorWorldRuntime->mapActorState(billboard.runtimeActorIndex);
}

const ActorPreviewBillboard *OutdoorInteractionController::findActorPreviewBillboardForRuntimeActorIndex(
    const OutdoorGameView &view,
    size_t runtimeActorIndex,
    size_t *pBillboardIndex)
{
    if (!view.m_outdoorActorPreviewBillboardSet)
    {
        return nullptr;
    }

    for (size_t billboardIndex = 0; billboardIndex < view.m_outdoorActorPreviewBillboardSet->billboards.size();
         ++billboardIndex)
    {
        const ActorPreviewBillboard &billboard = view.m_outdoorActorPreviewBillboardSet->billboards[billboardIndex];

        if (billboard.runtimeActorIndex != runtimeActorIndex)
        {
            continue;
        }

        if (pBillboardIndex != nullptr)
        {
            *pBillboardIndex = billboardIndex;
        }

        return &billboard;
    }

    return nullptr;
}



void OutdoorInteractionController::buildDecorationBillboardSpatialIndex(OutdoorGameView &view)
{
    view.m_decorationBillboardGridCells.clear();
    view.m_decorationBillboardGridMinX = 0.0f;
    view.m_decorationBillboardGridMinY = 0.0f;
    view.m_decorationBillboardGridWidth = 0;
    view.m_decorationBillboardGridHeight = 0;

    if (!view.m_outdoorDecorationBillboardSet || view.m_outdoorDecorationBillboardSet->billboards.empty())
    {
        return;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();

    for (const DecorationBillboard &billboard : view.m_outdoorDecorationBillboardSet->billboards)
    {
        const float x = static_cast<float>(billboard.x);
        const float y = static_cast<float>(billboard.y);
        minX = std::min(minX, x);
        minY = std::min(minY, y);
        maxX = std::max(maxX, x);
        maxY = std::max(maxY, y);
    }

    view.m_decorationBillboardGridMinX = minX;
    view.m_decorationBillboardGridMinY = minY;
    view.m_decorationBillboardGridWidth =
        static_cast<size_t>(std::floor((maxX - minX) / BillboardSpatialCellSize)) + 1;
    view.m_decorationBillboardGridHeight =
        static_cast<size_t>(std::floor((maxY - minY) / BillboardSpatialCellSize)) + 1;
    view.m_decorationBillboardGridCells.assign(view.m_decorationBillboardGridWidth * view.m_decorationBillboardGridHeight, {});

    for (size_t billboardIndex = 0; billboardIndex < view.m_outdoorDecorationBillboardSet->billboards.size(); ++billboardIndex)
    {
        const DecorationBillboard &billboard = view.m_outdoorDecorationBillboardSet->billboards[billboardIndex];
        const float x = static_cast<float>(billboard.x);
        const float y = static_cast<float>(billboard.y);
        const size_t cellX = std::min(
            static_cast<size_t>(std::max(0.0f, std::floor((x - minX) / BillboardSpatialCellSize))),
            view.m_decorationBillboardGridWidth - 1);
        const size_t cellY = std::min(
            static_cast<size_t>(std::max(0.0f, std::floor((y - minY) / BillboardSpatialCellSize))),
            view.m_decorationBillboardGridHeight - 1);
        view.m_decorationBillboardGridCells[cellY * view.m_decorationBillboardGridWidth + cellX].push_back(billboardIndex);
    }
}



void OutdoorInteractionController::collectDecorationBillboardCandidates(
    const OutdoorGameView &view,
    float minX,
    float minY,
    float maxX,
    float maxY,
    std::vector<size_t> &indices)
{
    indices.clear();

    if (view.m_decorationBillboardGridCells.empty() || view.m_decorationBillboardGridWidth == 0 || view.m_decorationBillboardGridHeight == 0)
    {
        return;
    }

    const int startCellX = std::clamp(
        static_cast<int>(std::floor((minX - view.m_decorationBillboardGridMinX) / BillboardSpatialCellSize)),
        0,
        static_cast<int>(view.m_decorationBillboardGridWidth) - 1);
    const int endCellX = std::clamp(
        static_cast<int>(std::floor((maxX - view.m_decorationBillboardGridMinX) / BillboardSpatialCellSize)),
        0,
        static_cast<int>(view.m_decorationBillboardGridWidth) - 1);
    const int startCellY = std::clamp(
        static_cast<int>(std::floor((minY - view.m_decorationBillboardGridMinY) / BillboardSpatialCellSize)),
        0,
        static_cast<int>(view.m_decorationBillboardGridHeight) - 1);
    const int endCellY = std::clamp(
        static_cast<int>(std::floor((maxY - view.m_decorationBillboardGridMinY) / BillboardSpatialCellSize)),
        0,
        static_cast<int>(view.m_decorationBillboardGridHeight) - 1);

    for (int cellY = startCellY; cellY <= endCellY; ++cellY)
    {
        for (int cellX = startCellX; cellX <= endCellX; ++cellX)
        {
            const std::vector<size_t> &cell =
                view.m_decorationBillboardGridCells[static_cast<size_t>(cellY) * view.m_decorationBillboardGridWidth
                    + static_cast<size_t>(cellX)];
            indices.insert(indices.end(), cell.begin(), cell.end());
        }
    }
}



OutdoorGameView::InspectHit OutdoorInteractionController::inspectBModelFace(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    float mouseX,
    float mouseY,
    int viewWidth,
    int viewHeight,
    const float *pViewMatrix,
    const float *pProjectionMatrix,
    OutdoorGameView::DecorationPickMode decorationPickMode,
    FacePickMode facePickMode)
{
    OutdoorGameView::InspectHit bestHit = {};
    bestHit.distance = std::numeric_limits<float>::max();

    if (vecLength(rayDirection) <= InspectRayEpsilon)
    {
        return {};
    }

    const float terrainBlockDistance =
        intersectOutdoorTerrainRay(outdoorMapData, rayOrigin, rayDirection).value_or(std::numeric_limits<float>::max());
    const float terrainDistanceEpsilon = 1.0f;
    const bool allowDecorationBillboardHit =
        pViewMatrix != nullptr
        && pProjectionMatrix != nullptr
        && viewWidth > 0
        && viewHeight > 0;

    auto isVisibleInspectDistance =
        [&](float distance)
        {
            return distance <= terrainBlockDistance + terrainDistanceEpsilon;
        };

    auto isDirectEventEntity =
        [](const OutdoorEntity &entity)
        {
            return entity.eventIdPrimary != 0 || entity.eventIdSecondary != 0;
        };

    auto bestHitIsPassiveEntity =
        [&](const OutdoorGameView::InspectHit &inspectHit)
        {
            return inspectHit.kind == "entity"
                && inspectHit.eventIdPrimary == 0
                && inspectHit.eventIdSecondary == 0;
        };

    auto bestHitIsPassiveSpawn =
        [&](const OutdoorGameView::InspectHit &inspectHit)
        {
            return inspectHit.kind == "spawn";
        };

    auto bestHitIsPassiveObject =
        [&](const OutdoorGameView::InspectHit &inspectHit)
        {
            return inspectHit.kind == "object";
        };

    const MapDeltaData *pMapDeltaData =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
    size_t flattenedFaceIndex = 0;

    for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bModel = outdoorMapData.bmodels[bModelIndex];

        for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
        {
            const OutdoorBModelFace &face = bModel.faces[faceIndex];
            const uint32_t effectiveAttributes =
                pMapDeltaData != nullptr && flattenedFaceIndex < pMapDeltaData->faceAttributes.size()
                    ? pMapDeltaData->faceAttributes[flattenedFaceIndex]
                    : face.attributes;
            ++flattenedFaceIndex;

            if (outdoorFaceHasInvisibleAttribute(effectiveAttributes) || face.vertexIndices.size() < 3)
            {
                continue;
            }

            if (facePickMode == FacePickMode::InteractionActivatable
                && !outdoorFaceIsInteractionActivatable(effectiveAttributes, face.cogTriggeredNumber))
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

                if (!isVisibleInspectDistance(distance))
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
                    bestHit.attributes = effectiveAttributes;
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

        if (isInteractiveDecorationHidden(view, entityIndex))
        {
            continue;
        }

        if (!isDirectEventEntity(entity))
        {
            continue;
        }

        const float halfExtent = InteractionEntityHalfExtent;
        float distance = 0.0f;

        const bx::Vec3 minBounds = {
            static_cast<float>(entity.x) - halfExtent,
            static_cast<float>(entity.y) - halfExtent,
            static_cast<float>(entity.z)
        };
        const bx::Vec3 maxBounds = {
            static_cast<float>(entity.x) + halfExtent,
            static_cast<float>(entity.y) + halfExtent,
            static_cast<float>(entity.z) + InteractionEntityHeight
        };

        if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
            && isVisibleInspectDistance(distance)
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

    if (view.m_outdoorDecorationBillboardSet)
    {
        std::vector<size_t> candidateBillboardIndices;
        const float maxDecorationInspectDistance = std::min(terrainBlockDistance, 8192.0f);
        const bx::Vec3 inspectEnd = {
            rayOrigin.x + rayDirection.x * maxDecorationInspectDistance,
            rayOrigin.y + rayDirection.y * maxDecorationInspectDistance,
            rayOrigin.z + rayDirection.z * maxDecorationInspectDistance
        };
        const float candidatePadding = BillboardSpatialCellSize;

        collectDecorationBillboardCandidates(view, 
            std::min(rayOrigin.x, inspectEnd.x) - candidatePadding,
            std::min(rayOrigin.y, inspectEnd.y) - candidatePadding,
            std::max(rayOrigin.x, inspectEnd.x) + candidatePadding,
            std::max(rayOrigin.y, inspectEnd.y) + candidatePadding,
            candidateBillboardIndices);

        const uint32_t animationTimeTicks = currentAnimationTicks();
        const auto resolveDecorationBillboardVisual = [&view](const DecorationBillboard &billboard, bool &hidden)
        {
            hidden = false;
            uint16_t spriteId = billboard.spriteId;

            if (!view.m_outdoorDecorationBillboardSet || view.m_pOutdoorWorldRuntime == nullptr)
            {
                return spriteId;
            }

            const EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState();

            if (pEventRuntimeState == nullptr)
            {
                return spriteId;
            }

            const uint32_t overrideKey =
                billboard.eventIdPrimary != 0 ? billboard.eventIdPrimary : billboard.eventIdSecondary;

            if (overrideKey == 0)
            {
                return spriteId;
            }

            const auto overrideIterator = pEventRuntimeState->spriteOverrides.find(overrideKey);

            if (overrideIterator == pEventRuntimeState->spriteOverrides.end())
            {
                return spriteId;
            }

            hidden = overrideIterator->second.hidden;

            if (!overrideIterator->second.textureName.has_value() || overrideIterator->second.textureName->empty())
            {
                return spriteId;
            }

            if (const DecorationEntry *pDecoration =
                    view.m_outdoorDecorationBillboardSet->decorationTable.findByInternalName(
                        *overrideIterator->second.textureName))
            {
                return pDecoration->spriteId;
            }

            if (const std::optional<uint16_t> overrideSpriteId =
                    view.m_outdoorDecorationBillboardSet->spriteFrameTable.findFrameIndexBySpriteName(
                        *overrideIterator->second.textureName))
            {
                return *overrideSpriteId;
            }

            return spriteId;
        };

        for (size_t decorationIndex : candidateBillboardIndices)
        {
            const DecorationBillboard &decoration = view.m_outdoorDecorationBillboardSet->billboards[decorationIndex];
            bool hidden = false;
            const uint16_t spriteId = resolveDecorationBillboardVisual(decoration, hidden);

            if (isInteractiveDecorationHidden(view, decoration.entityIndex) || hidden)
            {
                continue;
            }

            const std::optional<uint16_t> interactiveEventId =
                resolveInteractiveDecorationEventId(view, decoration.entityIndex);
            std::optional<uint16_t> directEventId;

            if (view.m_outdoorMapData && decoration.entityIndex < view.m_outdoorMapData->entities.size())
            {
                const OutdoorEntity &entity = view.m_outdoorMapData->entities[decoration.entityIndex];
                directEventId = entity.eventIdPrimary != 0 ? entity.eventIdPrimary : entity.eventIdSecondary;
            }
            const bool interactiveDecoration = interactiveEventId.has_value() || directEventId.has_value();
            const DecorationEntry *pDecorationEntry =
                view.m_outdoorDecorationBillboardSet->decorationTable.get(decoration.decorationId);

            if ((pDecorationEntry == nullptr || pDecorationEntry->hint.empty()) && !decoration.name.empty())
            {
                pDecorationEntry = view.m_outdoorDecorationBillboardSet->decorationTable.findByInternalName(decoration.name);
            }

            const bool hasHint = pDecorationEntry != nullptr && !pDecorationEntry->hint.empty();

            if (decorationPickMode == OutdoorGameView::DecorationPickMode::Interaction && !interactiveDecoration)
            {
                continue;
            }

            if (decorationPickMode == OutdoorGameView::DecorationPickMode::HoverInfo && !interactiveDecoration && !hasHint)
            {
                continue;
            }

            const float broadPhaseHalfExtent =
                std::max(InteractionDecorationMinHalfExtent, static_cast<float>(std::max(decoration.radius, int16_t(0))));
            const float broadPhaseHeight =
                std::max(InteractionDecorationMinHeight, static_cast<float>(std::max(decoration.height, uint16_t(0))));
            float distance = 0.0f;
            bool hasBillboardHit = false;

            if (allowDecorationBillboardHit
                && spriteId != 0
                && isVisibleInspectDistance(maxDecorationInspectDistance))
            {
                const uint32_t animationOffsetTicks =
                    animationTimeTicks + static_cast<uint32_t>(std::abs(decoration.x + decoration.y));
                const SpriteFrameEntry *pFrame =
                    view.m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(spriteId, animationOffsetTicks);

                if (pFrame != nullptr)
                {
                    const bx::Vec3 cameraPosition = {
                        view.m_cameraTargetX,
                        view.m_cameraTargetY,
                        view.m_cameraTargetZ
                    };
                    const float facingRadians = static_cast<float>(decoration.facing) * Pi / 180.0f;
                    const float angleToCamera = std::atan2(
                        static_cast<float>(decoration.y) - cameraPosition.y,
                        static_cast<float>(decoration.x) - cameraPosition.x
                    );
                    const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
                    const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
                    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
                    const OutdoorGameView::BillboardTextureHandle *pTexture = view.findBillboardTexture(resolvedTexture.textureName);

                    if (pTexture != nullptr && bgfx::isValid(pTexture->textureHandle))
                    {
                        const float spriteScale = std::max(pFrame->scale, 0.01f);
                        const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                        const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                        const float expandedHalfExtent = std::max(broadPhaseHalfExtent, worldWidth * 0.5f);
                        const float expandedHeight = std::max(broadPhaseHeight, worldHeight);
                        const bx::Vec3 minBounds = {
                            static_cast<float>(decoration.x) - expandedHalfExtent,
                            static_cast<float>(decoration.y) - expandedHalfExtent,
                            static_cast<float>(decoration.z)
                        };
                        const bx::Vec3 maxBounds = {
                            static_cast<float>(decoration.x) + expandedHalfExtent,
                            static_cast<float>(decoration.y) + expandedHalfExtent,
                            static_cast<float>(decoration.z) + expandedHeight
                        };

                        if (!intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                            || !isVisibleInspectDistance(distance))
                        {
                            continue;
                        }

                        hasBillboardHit = hitTestDecorationBillboard(view, 
                            decoration,
                            spriteId,
                            *pTexture,
                            resolvedTexture.mirrored,
                            mouseX,
                            mouseY,
                            viewWidth,
                            viewHeight,
                            pViewMatrix,
                            pProjectionMatrix,
                            rayOrigin,
                            rayDirection,
                            distance);
                    }
                }
            }

            if (hasBillboardHit
                && isVisibleInspectDistance(distance)
                && (!bestHit.hasHit
                    || distance < bestHit.distance
                    || bestHitIsPassiveEntity(bestHit)
                    || bestHitIsPassiveSpawn(bestHit)
                    || bestHitIsPassiveObject(bestHit)))
            {
                bestHit.hasHit = true;
                bestHit.kind = "decoration";
                bestHit.bModelIndex = decorationIndex;
                bestHit.name = decoration.name;
                bestHit.distance = distance;
                bestHit.decorationId = decoration.decorationId;

                if (view.m_outdoorMapData && decoration.entityIndex < view.m_outdoorMapData->entities.size())
                {
                    const OutdoorEntity &entity = view.m_outdoorMapData->entities[decoration.entityIndex];
                    bestHit.eventIdPrimary = entity.eventIdPrimary;
                    bestHit.eventIdSecondary = entity.eventIdSecondary;
                }
            }
        }
    }

    std::vector<bool> coveredRuntimeActors;

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        coveredRuntimeActors.assign(view.m_pOutdoorWorldRuntime->mapActorCount(), false);
    }

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        for (size_t actorIndex = 0; actorIndex < view.m_outdoorActorPreviewBillboardSet->billboards.size(); ++actorIndex)
        {
            const ActorPreviewBillboard &actor = view.m_outdoorActorPreviewBillboardSet->billboards[actorIndex];

            if (actor.source != ActorPreviewSource::Companion)
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pActorState = runtimeActorStateForBillboard(view, actor);

            if (pActorState != nullptr && actor.runtimeActorIndex < coveredRuntimeActors.size())
            {
                coveredRuntimeActors[actor.runtimeActorIndex] = true;
            }

            if (view.m_gameSession.gameplayScreenState().pendingSpellTarget().active
                && !pendingSpellAllowsDeadActorTarget(view.m_gameSession)
                && pActorState != nullptr
                && pActorState->isDead)
            {
                continue;
            }

            if (pActorState != nullptr && pActorState->isInvisible)
            {
                continue;
            }

            const int actorX = pActorState != nullptr ? pActorState->x : actor.x;
            const int actorY = pActorState != nullptr ? pActorState->y : actor.y;
            const int actorZ = pActorState != nullptr ? pActorState->z : actor.z;
            const uint16_t actorRadius = pActorState != nullptr ? pActorState->radius : actor.radius;
            const uint16_t actorHeight = pActorState != nullptr ? pActorState->height : actor.height;
            const float actorBaseZ = resolveActorAabbBaseZ(
                outdoorMapData,
                pActorState,
                actorX,
                actorY,
                actorZ,
                pActorState != nullptr && pActorState->isDead);
            const float halfExtent = std::max(InteractionActorMinHalfExtent, static_cast<float>(actorRadius));
            const float height = std::max(InteractionActorMinHeight, static_cast<float>(actorHeight));
            float distance = 0.0f;
            const bx::Vec3 minBounds = {
                static_cast<float>(actorX) - halfExtent,
                static_cast<float>(actorY) - halfExtent,
                actorBaseZ
            };
            const bx::Vec3 maxBounds = {
                static_cast<float>(actorX) + halfExtent,
                static_cast<float>(actorY) + halfExtent,
                actorBaseZ + height
            };

            bool hasActorHit = false;
            bool usedBillboardHit = false;
            float billboardDistance = 0.0f;

            const bool hasBillboardHit =
                allowDecorationBillboardHit
                && hitTestActorBillboard(view, 
                    pActorState,
                    actorX,
                    actorY,
                    actorZ,
                    actorHeight,
                    actor.height,
                    actor.spriteFrameIndex,
                    actor.actionSpriteFrameIndices,
                    actor.useStaticFrame,
                    mouseX,
                    mouseY,
                    viewWidth,
                    viewHeight,
                    pViewMatrix,
                    pProjectionMatrix,
                    rayOrigin,
                    rayDirection,
                    billboardDistance,
                    usedBillboardHit);

            if (hasBillboardHit && isVisibleInspectDistance(billboardDistance))
            {
                distance = billboardDistance;
                hasActorHit = true;
            }
            else if (!usedBillboardHit
                     && intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                     && isVisibleInspectDistance(distance))
            {
                hasActorHit = true;
            }

            if (hasActorHit && (!bestHit.hasHit || distance < bestHit.distance))
            {
                size_t previewBillboardIndex = actorIndex;
                const ActorPreviewBillboard *pPreviewBillboard =
                    actor.runtimeActorIndex != static_cast<size_t>(-1)
                        ? findActorPreviewBillboardForRuntimeActorIndex(view, actor.runtimeActorIndex, &previewBillboardIndex)
                        : nullptr;
                bestHit.hasHit = true;
                bestHit.kind = "actor";
                bestHit.bModelIndex = pPreviewBillboard != nullptr ? previewBillboardIndex : actorIndex;
                bestHit.faceIndex = 0;
                bestHit.name = pPreviewBillboard != nullptr && !pPreviewBillboard->actorName.empty()
                    ? pPreviewBillboard->actorName
                    : actor.actorName;
                bestHit.distance = distance;
                bestHit.isFriendly = actor.isFriendly;
                bestHit.npcId = pPreviewBillboard != nullptr ? pPreviewBillboard->npcId : actor.npcId;
                bestHit.actorGroup = pPreviewBillboard != nullptr ? pPreviewBillboard->group : actor.group;
                bestHit.runtimeActorIndex = actor.runtimeActorIndex != static_cast<size_t>(-1)
                    ? actor.runtimeActorIndex
                    : actorIndex;

                if (view.m_map)
                {
                    const SpawnPreview preview =
                        SpawnPreviewResolver::describe(
                            *view.m_map,
                            &view.data().monsterTable(),
                            actor.typeId,
                            actor.index,
                            actor.attributes,
                            actor.group
                        );
                    bestHit.spawnSummary = preview.summary;
                    bestHit.spawnDetail = preview.detail;
                }

                if (pActorState != nullptr)
                {
                    bestHit.isFriendly = !pActorState->hostileToParty;
                }
            }
        }
    }

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            if (actorIndex < coveredRuntimeActors.size() && coveredRuntimeActors[actorIndex])
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pActorState = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pActorState == nullptr || pActorState->isInvisible)
            {
                continue;
            }

            if (view.m_gameSession.gameplayScreenState().pendingSpellTarget().active
                && !pendingSpellAllowsDeadActorTarget(view.m_gameSession)
                && pActorState->isDead)
            {
                continue;
            }

            const float halfExtent = std::max(InteractionActorMinHalfExtent, static_cast<float>(pActorState->radius));
            const float height = std::max(InteractionActorMinHeight, static_cast<float>(pActorState->height));
            const float actorBaseZ = resolveActorAabbBaseZ(
                outdoorMapData,
                pActorState,
                pActorState->x,
                pActorState->y,
                pActorState->z,
                pActorState->isDead);
            float distance = 0.0f;
            const bx::Vec3 minBounds = {
                static_cast<float>(pActorState->x) - halfExtent,
                static_cast<float>(pActorState->y) - halfExtent,
                actorBaseZ
            };
            const bx::Vec3 maxBounds = {
                static_cast<float>(pActorState->x) + halfExtent,
                static_cast<float>(pActorState->y) + halfExtent,
                actorBaseZ + height
            };

            bool hasActorHit = false;
            bool usedBillboardHit = false;
            float billboardDistance = 0.0f;

            const bool hasBillboardHit =
                allowDecorationBillboardHit
                && hitTestActorBillboard(view, 
                    pActorState,
                    pActorState->x,
                    pActorState->y,
                    pActorState->z,
                    pActorState->height,
                    pActorState->height,
                    pActorState->spriteFrameIndex,
                    pActorState->actionSpriteFrameIndices,
                    pActorState->useStaticSpriteFrame,
                    mouseX,
                    mouseY,
                    viewWidth,
                    viewHeight,
                    pViewMatrix,
                    pProjectionMatrix,
                    rayOrigin,
                    rayDirection,
                    billboardDistance,
                    usedBillboardHit);

            if (hasBillboardHit && isVisibleInspectDistance(billboardDistance))
            {
                distance = billboardDistance;
                hasActorHit = true;
            }
            else if (!usedBillboardHit
                     && intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                     && isVisibleInspectDistance(distance))
            {
                hasActorHit = true;
            }

            if (hasActorHit && (!bestHit.hasHit || distance < bestHit.distance))
            {
                size_t previewBillboardIndex = actorIndex;
                const ActorPreviewBillboard *pPreviewBillboard =
                    findActorPreviewBillboardForRuntimeActorIndex(view, actorIndex, &previewBillboardIndex);
                bestHit.hasHit = true;
                bestHit.kind = "actor";
                bestHit.bModelIndex = pPreviewBillboard != nullptr ? previewBillboardIndex : actorIndex;
                bestHit.faceIndex = 0;
                bestHit.name = pPreviewBillboard != nullptr && !pPreviewBillboard->actorName.empty()
                    ? pPreviewBillboard->actorName
                    : pActorState->displayName;
                bestHit.distance = distance;
                bestHit.isFriendly = !pActorState->hostileToParty;
                bestHit.npcId = pPreviewBillboard != nullptr ? pPreviewBillboard->npcId : 0;
                bestHit.actorGroup = pPreviewBillboard != nullptr ? pPreviewBillboard->group : pActorState->group;
                bestHit.runtimeActorIndex = actorIndex;
                bestHit.spawnSummary.clear();
                bestHit.spawnDetail.clear();
            }
        }
    }

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        for (size_t worldItemIndex = 0; worldItemIndex < view.m_pOutdoorWorldRuntime->worldItemCount(); ++worldItemIndex)
        {
            const OutdoorWorldRuntime::WorldItemState *pWorldItem =
                view.m_pOutdoorWorldRuntime->worldItemState(worldItemIndex);

            if (pWorldItem == nullptr)
            {
                continue;
            }

            const float halfExtent =
                std::max(InteractionWorldItemMinHalfExtent, static_cast<float>(pWorldItem->radius));
            const float height =
                std::max(InteractionWorldItemMinHeight, static_cast<float>(pWorldItem->height));
            float distance = 0.0f;
            const bx::Vec3 minBounds = {
                pWorldItem->x - halfExtent,
                pWorldItem->y - halfExtent,
                pWorldItem->z
            };
            const bx::Vec3 maxBounds = {
                pWorldItem->x + halfExtent,
                pWorldItem->y + halfExtent,
                pWorldItem->z + height
            };

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                && isVisibleInspectDistance(distance)
                && (!bestHit.hasHit
                    || distance < bestHit.distance
                    || bestHitIsPassiveEntity(bestHit)
                    || bestHitIsPassiveSpawn(bestHit)
                    || bestHitIsPassiveObject(bestHit)))
            {
                bestHit.hasHit = true;
                bestHit.kind = "world_item";
                bestHit.bModelIndex = worldItemIndex;
                bestHit.name = pWorldItem->objectName;
                bestHit.distance = distance;
                bestHit.objectDescriptionId = pWorldItem->objectDescriptionId;
                bestHit.objectSpriteId = pWorldItem->objectSpriteId;
                bestHit.attributes = pWorldItem->attributes;
                bestHit.spellId = 0;
            }
        }
    }

    if (view.m_outdoorSpriteObjectBillboardSet)
    {
        for (size_t objectIndex = 0; objectIndex < view.m_outdoorSpriteObjectBillboardSet->billboards.size(); ++objectIndex)
        {
            const SpriteObjectBillboard &object = view.m_outdoorSpriteObjectBillboardSet->billboards[objectIndex];
            const ObjectEntry *pObjectEntry = view.data().objectTable().get(object.objectDescriptionId);

            if (shouldSkipSpriteObjectInspectTarget(object, pObjectEntry))
            {
                continue;
            }

            const float halfExtent = std::max(InteractionSpriteObjectMinHalfExtent, static_cast<float>(object.radius));
            const float height = std::max(InteractionSpriteObjectMinHeight, static_cast<float>(object.height));
            float distance = 0.0f;
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

            if (intersectRayAabb(rayOrigin, rayDirection, minBounds, maxBounds, distance)
                && isVisibleInspectDistance(distance)
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

    if (!bestHit.hasHit && terrainBlockDistance < std::numeric_limits<float>::max())
    {
        bestHit.hasHit = true;
        bestHit.kind = "terrain";
        bestHit.name = "terrain";
        bestHit.distance = terrainBlockDistance;
    }

    if (bestHit.hasHit && bestHit.distance < std::numeric_limits<float>::max())
    {
        bestHit.hitX = rayOrigin.x + rayDirection.x * bestHit.distance;
        bestHit.hitY = rayOrigin.y + rayDirection.y * bestHit.distance;
        bestHit.hitZ = rayOrigin.z + rayDirection.z * bestHit.distance;
    }

    return bestHit;
}

OutdoorGameView::InspectHit OutdoorInteractionController::pickKeyboardInteractionInspectHit(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    int viewWidth,
    int viewHeight,
    const float *pViewMatrix,
    const float *pProjectionMatrix)
{
    OutdoorGameView::InspectHit bestHit = {};
    bestHit.distance = std::numeric_limits<float>::max();

    if (viewWidth <= 0 || viewHeight <= 0 || pViewMatrix == nullptr || pProjectionMatrix == nullptr)
    {
        return {};
    }

    const auto nearestLevelGeometryDistance =
        [&](const bx::Vec3 &rayOrigin, const bx::Vec3 &rayDirection, float maxDistance) -> float
        {
            float bestDistance = maxDistance;

            if (const std::optional<float> terrainDistance =
                    intersectOutdoorTerrainRay(outdoorMapData, rayOrigin, rayDirection))
            {
                bestDistance = std::min(bestDistance, *terrainDistance);
            }

            const bx::Vec3 inspectEnd = {
                rayOrigin.x + rayDirection.x * maxDistance,
                rayOrigin.y + rayDirection.y * maxDistance,
                rayOrigin.z + rayDirection.z * maxDistance
            };
            std::vector<size_t> candidateFaceIndices;

            if (view.m_pOutdoorWorldRuntime != nullptr)
            {
                constexpr float FaceCandidatePadding = 16.0f;
                view.m_pOutdoorWorldRuntime->collectOutdoorFaceCandidates(
                    std::min(rayOrigin.x, inspectEnd.x) - FaceCandidatePadding,
                    std::min(rayOrigin.y, inspectEnd.y) - FaceCandidatePadding,
                    std::max(rayOrigin.x, inspectEnd.x) + FaceCandidatePadding,
                    std::max(rayOrigin.y, inspectEnd.y) + FaceCandidatePadding,
                    candidateFaceIndices);
            }
            if (view.m_pOutdoorWorldRuntime != nullptr)
            {
                for (size_t candidateFaceIndex : candidateFaceIndices)
                {
                    const OutdoorFaceGeometryData *pFaceGeometry =
                        view.m_pOutdoorWorldRuntime->outdoorFace(candidateFaceIndex);

                    if (pFaceGeometry == nullptr
                        || !pFaceGeometry->hasPlane
                        || pFaceGeometry->isWalkable
                        || outdoorFaceHasInvisibleAttribute(pFaceGeometry->attributes))
                    {
                        continue;
                    }

                    if (inspectEnd.x < pFaceGeometry->minX - 16.0f && rayOrigin.x < pFaceGeometry->minX - 16.0f)
                    {
                        continue;
                    }

                    if (inspectEnd.x > pFaceGeometry->maxX + 16.0f && rayOrigin.x > pFaceGeometry->maxX + 16.0f)
                    {
                        continue;
                    }

                    if (inspectEnd.y < pFaceGeometry->minY - 16.0f && rayOrigin.y < pFaceGeometry->minY - 16.0f)
                    {
                        continue;
                    }

                    if (inspectEnd.y > pFaceGeometry->maxY + 16.0f && rayOrigin.y > pFaceGeometry->maxY + 16.0f)
                    {
                        continue;
                    }

                    float factor = 0.0f;
                    bx::Vec3 point = {0.0f, 0.0f, 0.0f};

                    if (!intersectOutdoorSegmentWithFace(*pFaceGeometry, rayOrigin, inspectEnd, factor, point))
                    {
                        continue;
                    }

                    const float distance = maxDistance * factor;
                    bestDistance = std::min(bestDistance, distance);
                }
            }
            else
            {
                for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
                {
                    const OutdoorBModel &bModel = outdoorMapData.bmodels[bModelIndex];

                    for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
                    {
                        const OutdoorBModelFace &face = bModel.faces[faceIndex];

                        if (outdoorFaceHasInvisibleAttribute(face.attributes) || face.vertexIndices.size() < 3)
                        {
                            continue;
                        }

                        const std::optional<float> faceDistance =
                            intersectOutdoorFaceRay(bModel, face, rayOrigin, rayDirection);

                        if (faceDistance)
                        {
                            bestDistance = std::min(bestDistance, *faceDistance);
                        }
                    }
                }
            }

            return bestDistance;
        };
    const auto tryUpdateBestHit =
        [&bestHit](const OutdoorGameView::InspectHit &hit)
        {
            if (!hit.hasHit)
            {
                return;
            }

            if (!bestHit.hasHit || hit.distance < bestHit.distance)
            {
                bestHit = hit;
            }
        };
    const auto tryResolveVisibleKeyboardBillboardHit =
        [&](const OutdoorGameView::KeyboardInteractionBillboardCandidate &candidate) -> std::optional<OutdoorGameView::InspectHit>
        {
            constexpr float GeometryDistanceEpsilon = 1.0f;

            if (!candidate.inspectHit.hasHit
                || !canActivateInteractionInspectEvent(view, candidate.inspectHit, InteractionInputMethod::Keyboard))
            {
                return std::nullopt;
            }

            for (size_t sampleIndex = 0; sampleIndex < candidate.samplePointCount; ++sampleIndex)
            {
                const OutdoorGameView::KeyboardInteractionSamplePoint &samplePoint =
                    candidate.samplePoints[sampleIndex];
                bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
                bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

                if (!OutdoorInteractionController::buildInspectRayForScreenPoint(
                        samplePoint.x,
                        samplePoint.y,
                        viewWidth,
                        viewHeight,
                        pViewMatrix,
                        pProjectionMatrix,
                        rayOrigin,
                        rayDirection))
                {
                    continue;
                }

                if (candidate.inspectHit.kind == "actor" && view.m_pOutdoorWorldRuntime != nullptr)
                {
                    const size_t runtimeActorIndex = candidate.inspectHit.runtimeActorIndex;
                    const OutdoorWorldRuntime::MapActorState *pActorState =
                        runtimeActorIndex != static_cast<size_t>(-1)
                            ? view.m_pOutdoorWorldRuntime->mapActorState(runtimeActorIndex)
                            : nullptr;

                    if (pActorState == nullptr || pActorState->isInvisible)
                    {
                        continue;
                    }
                }

                if (candidate.inspectHit.kind == "decoration")
                {
                    if (!view.m_outdoorDecorationBillboardSet
                        || candidate.inspectHit.bModelIndex >= view.m_outdoorDecorationBillboardSet->billboards.size())
                    {
                        continue;
                    }

                    const DecorationBillboard &decoration =
                        view.m_outdoorDecorationBillboardSet->billboards[candidate.inspectHit.bModelIndex];
                    bool hidden = false;

                    if (OutdoorInteractionController::resolveDecorationBillboardSpriteId(view, decoration, hidden) == 0
                        || hidden)
                    {
                        continue;
                    }
                }

                const float candidateDistance = candidate.cameraDepth;

                if (candidateDistance <= InspectRayEpsilon)
                {
                    continue;
                }

                const float blockingDistance = nearestLevelGeometryDistance(rayOrigin, rayDirection, candidateDistance);

                if (blockingDistance + GeometryDistanceEpsilon < candidateDistance)
                {
                    continue;
                }

                OutdoorGameView::InspectHit resolvedHit = candidate.inspectHit;
                resolvedHit.distance = candidateDistance;
                resolvedHit.hitX = rayOrigin.x + rayDirection.x * candidateDistance;
                resolvedHit.hitY = rayOrigin.y + rayDirection.y * candidateDistance;
                resolvedHit.hitZ = rayOrigin.z + rayDirection.z * candidateDistance;
                return resolvedHit;
            }

            return std::nullopt;
        };

    for (const OutdoorGameView::KeyboardInteractionBillboardCandidate &candidate :
         view.m_keyboardInteractionBillboardCandidates)
    {
        if (bestHit.hasHit && candidate.cameraDepth > bestHit.distance + 1.0f)
        {
            break;
        }

        const std::optional<OutdoorGameView::InspectHit> resolvedHit =
            tryResolveVisibleKeyboardBillboardHit(candidate);

        if (resolvedHit)
        {
            tryUpdateBestHit(*resolvedHit);
        }
    }

    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, pViewMatrix, pProjectionMatrix);

    for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bModel = outdoorMapData.bmodels[bModelIndex];

        for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
        {
            const OutdoorBModelFace &face = bModel.faces[faceIndex];

            if (!outdoorFaceIsInteractionActivatable(face.attributes, face.cogTriggeredNumber)
                || face.vertexIndices.size() < 3)
            {
                continue;
            }

            float minX = 0.0f;
            float minY = 0.0f;
            float maxX = 0.0f;
            float maxY = 0.0f;
            bool hasProjectedVertex = false;

            for (uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex >= bModel.vertices.size())
                {
                    continue;
                }

                ProjectedPoint projected = {};

                if (!projectWorldPointToScreen(
                        outdoorBModelVertexToWorld(bModel.vertices[vertexIndex]),
                        viewWidth,
                        viewHeight,
                        viewProjectionMatrix,
                        projected))
                {
                    continue;
                }

                if (!hasProjectedVertex)
                {
                    minX = projected.x;
                    maxX = projected.x;
                    minY = projected.y;
                    maxY = projected.y;
                    hasProjectedVertex = true;
                    continue;
                }

                minX = std::min(minX, projected.x);
                maxX = std::max(maxX, projected.x);
                minY = std::min(minY, projected.y);
                maxY = std::max(maxY, projected.y);
            }

            if (!hasProjectedVertex
                || maxX < 0.0f
                || maxY < 0.0f
                || minX > static_cast<float>(viewWidth)
                || minY > static_cast<float>(viewHeight))
            {
                continue;
            }

            const float screenX = std::clamp((minX + maxX) * 0.5f, 0.0f, static_cast<float>(viewWidth));
            const float screenY = std::clamp((minY + maxY) * 0.5f, 0.0f, static_cast<float>(viewHeight));
            bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
            bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

            if (!OutdoorInteractionController::buildInspectRayForScreenPoint(
                    screenX,
                    screenY,
                    viewWidth,
                    viewHeight,
                    pViewMatrix,
                    pProjectionMatrix,
                    rayOrigin,
                    rayDirection))
            {
                continue;
            }

            const std::optional<float> faceDistance = intersectOutdoorFaceRay(bModel, face, rayOrigin, rayDirection);

            if (!faceDistance.has_value())
            {
                continue;
            }

            const float blockingDistance = nearestLevelGeometryDistance(rayOrigin, rayDirection, *faceDistance);

            if (blockingDistance + 1.0f < *faceDistance)
            {
                continue;
            }

            OutdoorGameView::InspectHit hit = {};
            hit.hasHit = true;
            hit.kind = "face";
            hit.bModelIndex = bModelIndex;
            hit.faceIndex = faceIndex;
            hit.textureName = face.textureName;
            hit.distance = *faceDistance;
            hit.attributes = face.attributes;
            hit.bitmapIndex = face.bitmapIndex;
            hit.cogNumber = face.cogNumber;
            hit.cogTriggeredNumber = face.cogTriggeredNumber;
            hit.cogTrigger = face.cogTrigger;
            hit.polygonType = face.polygonType;
            hit.shade = face.shade;
            hit.visibility = face.visibility;
            hit.hitX = rayOrigin.x + rayDirection.x * *faceDistance;
            hit.hitY = rayOrigin.y + rayDirection.y * *faceDistance;
            hit.hitZ = rayOrigin.z + rayDirection.z * *faceDistance;

            if (!canActivateInteractionInspectEvent(view, hit, InteractionInputMethod::Keyboard))
            {
                continue;
            }

            tryUpdateBestHit(hit);
        }
    }

    return bestHit;
}

bool OutdoorInteractionController::tryActivateActorInspectEvent(
    OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind != "actor")
    {
        return false;
    }

    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (!view.m_outdoorMapData || pEventRuntimeState == nullptr)
    {
        return false;
    }

    uint16_t eventId = 0;

    if (inspectHit.kind == "actor" && view.m_pOutdoorWorldRuntime != nullptr)
    {
        const std::optional<size_t> runtimeActorIndex = resolveRuntimeActorIndexForInspectHit(view, inspectHit);

        if (runtimeActorIndex)
        {
            const OutdoorWorldRuntime::MapActorState *pActorState =
                view.m_pOutdoorWorldRuntime->mapActorState(*runtimeActorIndex);

            if (pActorState != nullptr && pActorState->isDead)
            {
                if (!view.m_pOutdoorWorldRuntime->openMapActorCorpseView(*runtimeActorIndex))
                {
                    view.setStatusBarEvent("Nothing here");
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " empty";
                    return true;
                }

                GameplayCorpseAutoLootResult lootResult = autoLootActiveCorpseView(
                    *view.m_pOutdoorWorldRuntime,
                    view.m_pOutdoorPartyRuntime->party(),
                    &view.data().itemTable(),
                    &view.heldInventoryItem());

                if (!lootResult.statusText.empty())
                {
                    view.setStatusBarEvent(lootResult.statusText);
                }

                if (lootResult.lootedAny && !lootResult.firstItemName.empty())
                {
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " auto-looted item";
                }
                else if (lootResult.lootedAny)
                {
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " auto-looted gold";
                }
                else if (lootResult.blockedByInventory)
                {
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " blocked by inventory";
                }
                else
                {
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " empty";
                }

                return lootResult.lootedAny || lootResult.blockedByInventory || lootResult.empty;
            }
        }
    }

    auto faceTalkingActor =
        [&view, &inspectHit]()
        {
            if (view.m_pOutdoorWorldRuntime == nullptr || view.m_pOutdoorPartyRuntime == nullptr)
            {
                return;
            }

            const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();

            if (inspectHit.kind != "actor")
            {
                return;
            }

            const std::optional<size_t> runtimeActorIndex = resolveRuntimeActorIndexForInspectHit(view, inspectHit);

            if (runtimeActorIndex)
            {
                view.m_pOutdoorWorldRuntime->notifyPartyContactWithMapActor(
                    *runtimeActorIndex,
                    moveState.x,
                    moveState.y,
                    moveState.footZ);
            }
        };

    if (inspectHit.kind == "actor" && inspectHit.npcId > 0)
    {
        if (inspectHitTargetsLivingHostileActor(view, inspectHit))
        {
            pEventRuntimeState->lastActivationResult = "hostile npc dialogue blocked";
            return false;
        }

        faceTalkingActor();
        GameplayDialogController::Context context =
            createGameplayDialogContext(view, *pEventRuntimeState, "activate_actor_npc_dialog");
        const GameplayDialogController::Result result =
            view.m_gameSession.gameplayDialogController().openNpcDialogue(
                context,
                static_cast<uint32_t>(inspectHit.npcId));
        pEventRuntimeState->lastActivationResult = "npc " + std::to_string(inspectHit.npcId) + " engaged";

        if (result.shouldOpenPendingEventDialog)
        {
            OutdoorInteractionController::presentPendingEventDialog(
                view,
                result.previousMessageCount,
                result.allowNpcFallbackContent);
        }

        return true;
    }

    if (inspectHit.kind == "actor")
    {
        if (inspectHitTargetsLivingHostileActor(view, inspectHit))
        {
            pEventRuntimeState->lastActivationResult = "hostile actor dialogue blocked";
            return false;
        }

        const std::optional<GenericActorDialogResolution> resolution = resolveGenericActorDialog(
            view.m_map ? view.m_map->fileName : std::string(),
            inspectHit.name,
            inspectHit.actorGroup,
            *pEventRuntimeState,
            view.data().npcDialogTable()
        );

        if (resolution)
        {
            const std::optional<std::string> newsText = view.data().npcDialogTable().getNewsText(resolution->newsId);

            if (!newsText || newsText->empty())
            {
                return false;
            }

            faceTalkingActor();
            GameplayDialogController::Context context =
                createGameplayDialogContext(view, *pEventRuntimeState, "activate_actor_news_dialog");
            const GameplayDialogController::Result result = view.m_gameSession.gameplayDialogController().openNpcNews(
                context,
                resolution->npcId,
                resolution->newsId,
                inspectHit.name,
                *newsText);
            pEventRuntimeState->lastActivationResult =
                "npc news group " + std::to_string(inspectHit.actorGroup) + " engaged";

            if (result.shouldOpenPendingEventDialog)
            {
                OutdoorInteractionController::presentPendingEventDialog(
                    view,
                    result.previousMessageCount,
                    result.allowNpcFallbackContent);
            }

            return true;
        }
    }

    return false;
}

bool OutdoorInteractionController::tryActivateWorldItemInspectEvent(
    OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind != "world_item")
    {
        return false;
    }

    if (view.m_pOutdoorWorldRuntime == nullptr || view.m_pOutdoorPartyRuntime == nullptr)
    {
        return false;
    }

    const OutdoorWorldRuntime::WorldItemState *pWorldItem =
        view.m_pOutdoorWorldRuntime->worldItemState(inspectHit.bModelIndex);

    if (pWorldItem == nullptr)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = view.data().itemTable().get(pWorldItem->item.objectDescriptionId);
    const std::string itemName =
        pItemDefinition != nullptr && !pItemDefinition->name.empty() ? pItemDefinition->name : "item";

    if (pWorldItem->isGold)
    {
        OutdoorWorldRuntime::WorldItemState worldItem = {};

        if (!view.m_pOutdoorWorldRuntime->takeWorldItem(inspectHit.bModelIndex, worldItem))
        {
            return false;
        }

        const int goldAmount = static_cast<int>(std::max<uint32_t>(1u, worldItem.goldAmount));
        view.m_pOutdoorPartyRuntime->party().addGold(goldAmount);
        view.setStatusBarEvent(formatFoundGoldStatusText(goldAmount));

        if (EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState())
        {
            pEventRuntimeState->lastActivationResult = "picked up " + std::to_string(goldAmount) + " gold";
        }

        return true;
    }

    size_t recipientMemberIndex = 0;

    if (view.m_pOutdoorPartyRuntime->party().tryGrantInventoryItem(pWorldItem->item, &recipientMemberIndex))
    {
        OutdoorWorldRuntime::WorldItemState worldItem = {};

        if (!view.m_pOutdoorWorldRuntime->takeWorldItem(inspectHit.bModelIndex, worldItem))
        {
            return false;
        }

        view.m_pOutdoorPartyRuntime->party().requestSound(SoundId::Gold);
        view.m_gameSession.gameplayScreenRuntime().playSpeechReaction(
            recipientMemberIndex,
            SpeechId::FoundItem,
            true);
        view.setStatusBarEvent(formatFoundItemStatusText(0, itemName));

        if (EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState())
        {
            pEventRuntimeState->lastActivationResult = "picked up " + itemName;
        }

        return true;
    }

    GameplayUiController::HeldInventoryItemState &heldInventoryItem = view.heldInventoryItem();

    if (!heldInventoryItem.active)
    {
        OutdoorWorldRuntime::WorldItemState worldItem = {};

        if (!view.m_pOutdoorWorldRuntime->takeWorldItem(inspectHit.bModelIndex, worldItem))
        {
            return false;
        }

        GameplayHeldItemController::setHeldInventoryItem(heldInventoryItem, worldItem.item);
        view.m_pOutdoorPartyRuntime->party().requestSound(SoundId::Gold);
        view.m_gameSession.gameplayScreenRuntime().playSpeechReaction(
            view.m_pOutdoorPartyRuntime->party().activeMemberIndex(),
            SpeechId::FoundItem,
            true);
        view.setStatusBarEvent(formatFoundItemStatusText(0, itemName));

        if (EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState())
        {
            pEventRuntimeState->lastActivationResult = "picked up " + itemName + " into hand";
        }

        return true;
    }

    return false;
}

bool OutdoorInteractionController::tryActivateContainerInspectEvent(
    OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind != "chest" && inspectHit.kind != "corpse")
    {
        return false;
    }

    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState != nullptr)
    {
        pEventRuntimeState->lastActivationResult = "no activatable event on hovered target";
    }

    return false;
}

bool OutdoorInteractionController::tryActivateEventTargetInspectEvent(
    OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (!view.m_outdoorMapData || pEventRuntimeState == nullptr)
    {
        return false;
    }

    uint16_t eventId = 0;

    std::optional<EventRuntimeState::ActiveDecorationContext> decorationContext;

    if (inspectHit.kind == "decoration")
    {
        if (!view.m_outdoorDecorationBillboardSet
            || inspectHit.bModelIndex >= view.m_outdoorDecorationBillboardSet->billboards.size())
        {
            pEventRuntimeState->lastActivationResult = "invalid decoration target";
            return false;
        }

        const DecorationBillboard &decoration = view.m_outdoorDecorationBillboardSet->billboards[inspectHit.bModelIndex];
        const OutdoorGameView::InteractiveDecorationBinding *pBinding =
            findInteractiveDecorationBindingForEntity(view, decoration.entityIndex);

        if (pBinding != nullptr)
        {
            const std::optional<uint16_t> interactiveEventId =
                resolveInteractiveDecorationEventId(view, decoration.entityIndex);

            if (interactiveEventId)
            {
                eventId = *interactiveEventId;
                EventRuntimeState::ActiveDecorationContext context = {};
                context.decorVarIndex = pBinding->decorVarIndex;
                context.baseEventId = pBinding->baseEventId;
                context.currentEventId = *interactiveEventId;
                context.eventCount = pBinding->eventCount;
                context.hideWhenCleared = pBinding->hideWhenCleared;
                decorationContext = context;
            }
        }

        if (eventId == 0)
        {
            eventId = inspectHit.eventIdPrimary != 0 ? inspectHit.eventIdPrimary : inspectHit.eventIdSecondary;
        }
    }
    else if (inspectHit.kind == "entity")
    {
        eventId = inspectHit.eventIdPrimary != 0 ? inspectHit.eventIdPrimary : inspectHit.eventIdSecondary;

        if (eventId == 0)
        {
            const OutdoorGameView::InteractiveDecorationBinding *pBinding =
                findInteractiveDecorationBindingForEntity(view, inspectHit.bModelIndex);

            if (pBinding != nullptr)
            {
                const std::optional<uint16_t> interactiveEventId =
                    resolveInteractiveDecorationEventId(view, inspectHit.bModelIndex);

                if (interactiveEventId)
                {
                    eventId = *interactiveEventId;
                    EventRuntimeState::ActiveDecorationContext context = {};
                    context.decorVarIndex = pBinding->decorVarIndex;
                    context.baseEventId = pBinding->baseEventId;
                    context.currentEventId = *interactiveEventId;
                    context.eventCount = pBinding->eventCount;
                    context.hideWhenCleared = pBinding->hideWhenCleared;
                    decorationContext = context;
                }
            }
        }
    }
    else if (inspectHit.kind == "face")
    {
        if (!outdoorFaceIsInteractionActivatable(inspectHit.attributes, inspectHit.cogTriggeredNumber))
        {
            pEventRuntimeState->lastActivationResult = "face target is hover-only or non-clickable";
            return false;
        }

        eventId = inspectHit.cogTriggeredNumber;
    }
    else
    {
        pEventRuntimeState->lastActivationResult = "no activatable event on hovered target";
        return false;
    }

    if (eventId == 0)
    {
        pEventRuntimeState->lastActivationResult = "no event on hovered target";
        return false;
    }

    size_t previousMessageCount = 0;

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        view.m_pOutdoorWorldRuntime->setPendingEventSourcePoint(GameplayWorldPoint{
            .x = inspectHit.hitX,
            .y = inspectHit.hitY,
            .z = inspectHit.hitZ,
        });
    }

    const bool executed = view.m_pOutdoorSceneRuntime != nullptr
        && view.m_pOutdoorSceneRuntime->executeEventById(
            view.m_pOutdoorSceneRuntime->localEventProgram(),
            eventId,
            decorationContext,
            previousMessageCount
        );

    if (!executed)
    {
        if (view.m_pOutdoorWorldRuntime != nullptr)
        {
            view.m_pOutdoorWorldRuntime->setPendingEventSourcePoint(std::nullopt);
        }

        pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        return false;
    }

    promotePendingMapMoveToTransitionDialog(*pEventRuntimeState);

    for (const std::string &statusMessage : pEventRuntimeState->statusMessages)
    {
        view.setStatusBarEvent(statusMessage);
    }
    pEventRuntimeState->statusMessages.clear();
    OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(view);

    OutdoorInteractionController::presentPendingEventDialog(view, previousMessageCount, true);

    pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    return true;
}

bool OutdoorInteractionController::tryActivateInspectEvent(
    OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind == "world_item")
    {
        return tryActivateWorldItemInspectEvent(view, inspectHit);
    }

    if (inspectHit.kind == "actor")
    {
        return tryActivateActorInspectEvent(view, inspectHit);
    }

    if (inspectHit.kind == "chest" || inspectHit.kind == "corpse")
    {
        return tryActivateContainerInspectEvent(view, inspectHit);
    }

    return tryActivateEventTargetInspectEvent(view, inspectHit);
}



bool OutdoorInteractionController::canActivateInspectEvent(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind == "world_item")
    {
        return canActivateWorldItemInspectEvent(view, inspectHit);
    }

    if (inspectHit.kind == "actor")
    {
        return canActivateActorInspectEvent(view, inspectHit);
    }

    if (inspectHit.kind == "chest" || inspectHit.kind == "corpse")
    {
        return canActivateContainerInspectEvent(view, inspectHit);
    }

    return canActivateEventTargetInspectEvent(view, inspectHit);
}

bool OutdoorInteractionController::canActivateActorInspectEvent(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind != "actor")
    {
        return false;
    }

    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (!view.m_outdoorMapData || pEventRuntimeState == nullptr)
    {
        return false;
    }

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        const std::optional<size_t> runtimeActorIndex = resolveRuntimeActorIndexForInspectHit(view, inspectHit);

        if (runtimeActorIndex)
        {
            const OutdoorWorldRuntime::MapActorState *pActorState =
                view.m_pOutdoorWorldRuntime->mapActorState(*runtimeActorIndex);

            if (pActorState != nullptr && pActorState->isDead)
            {
                return true;
            }
        }
    }

    if (inspectHit.npcId > 0)
    {
        return !inspectHitTargetsLivingHostileActor(view, inspectHit);
    }

    if (inspectHitTargetsLivingHostileActor(view, inspectHit))
    {
        return false;
    }

    return resolveGenericActorDialog(
        view.m_map ? view.m_map->fileName : std::string(),
        inspectHit.name,
        inspectHit.actorGroup,
        *pEventRuntimeState,
        view.data().npcDialogTable()
    ).has_value();
}

bool OutdoorInteractionController::canActivateWorldItemInspectEvent(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind != "world_item")
    {
        return false;
    }

    return !view.heldInventoryItem().active;
}

bool OutdoorInteractionController::canActivateContainerInspectEvent(
    const OutdoorGameView &,
    const OutdoorGameView::InspectHit &)
{
    return false;
}

bool OutdoorInteractionController::canActivateEventTargetInspectEvent(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit)
{
    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (!view.m_outdoorMapData || pEventRuntimeState == nullptr)
    {
        return false;
    }

    if (inspectHit.kind == "entity")
    {
        if (inspectHit.eventIdPrimary != 0 || inspectHit.eventIdSecondary != 0)
        {
            return true;
        }

        return findInteractiveDecorationBindingForEntity(view, inspectHit.bModelIndex) != nullptr
            && resolveInteractiveDecorationEventId(view, inspectHit.bModelIndex).has_value();
    }

    if (inspectHit.kind == "decoration")
    {
        if (!view.m_outdoorDecorationBillboardSet
            || inspectHit.bModelIndex >= view.m_outdoorDecorationBillboardSet->billboards.size())
        {
            return false;
        }

        const DecorationBillboard &decoration = view.m_outdoorDecorationBillboardSet->billboards[inspectHit.bModelIndex];
        if (view.m_outdoorMapData && decoration.entityIndex < view.m_outdoorMapData->entities.size())
        {
            const OutdoorEntity &entity = view.m_outdoorMapData->entities[decoration.entityIndex];

            if (entity.eventIdPrimary != 0 || entity.eventIdSecondary != 0)
            {
                return true;
            }
        }

        return findInteractiveDecorationBindingForEntity(view, decoration.entityIndex) != nullptr
            && resolveInteractiveDecorationEventId(view, decoration.entityIndex).has_value();
    }

    if (inspectHit.kind == "face")
    {
        return outdoorFaceIsInteractionActivatable(inspectHit.attributes, inspectHit.cogTriggeredNumber);
    }

    return false;
}

bool OutdoorInteractionController::isInteractionInspectHitInRange(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit,
    InteractionInputMethod inputMethod)
{
    if (!inspectHit.hasHit)
    {
        return false;
    }

    return inspectHit.distance < interactionDepthForInputMethod(view, inputMethod);
}

bool OutdoorInteractionController::canActivateInteractionInspectEvent(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit,
    InteractionInputMethod inputMethod)
{
    return canActivateInspectEvent(view, inspectHit)
        && isInteractionInspectHitInRange(view, inspectHit, inputMethod);
}

bool OutdoorInteractionController::canActivateInteractionActorInspectEvent(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit,
    InteractionInputMethod inputMethod)
{
    return canActivateActorInspectEvent(view, inspectHit)
        && isInteractionInspectHitInRange(view, inspectHit, inputMethod);
}

bool OutdoorInteractionController::canActivateInteractionWorldItemInspectEvent(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit,
    InteractionInputMethod inputMethod)
{
    return canActivateWorldItemInspectEvent(view, inspectHit)
        && isInteractionInspectHitInRange(view, inspectHit, inputMethod);
}

bool OutdoorInteractionController::canActivateInteractionContainerInspectEvent(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit,
    InteractionInputMethod inputMethod)
{
    return canActivateContainerInspectEvent(view, inspectHit)
        && isInteractionInspectHitInRange(view, inspectHit, inputMethod);
}

bool OutdoorInteractionController::canActivateInteractionEventTargetInspectEvent(
    const OutdoorGameView &view,
    const OutdoorGameView::InspectHit &inspectHit,
    InteractionInputMethod inputMethod)
{
    return canActivateEventTargetInspectEvent(view, inspectHit)
        && isInteractionInspectHitInRange(view, inspectHit, inputMethod);
}

bool OutdoorInteractionController::canDispatchWorldActivation(
    const OutdoorGameView &view,
    const GameplayWorldHit &worldHit,
    InteractionInputMethod inputMethod)
{
    if (!worldHit.hasHit)
    {
        return false;
    }

    const OutdoorGameView::InspectHit inspectHit = inspectHitFromGameplayWorldHit(worldHit);

    if (worldHit.kind == GameplayWorldHitKind::Actor)
    {
        return canActivateInteractionActorInspectEvent(view, inspectHit, inputMethod);
    }

    if (worldHit.kind == GameplayWorldHitKind::WorldItem)
    {
        return canActivateInteractionWorldItemInspectEvent(view, inspectHit, inputMethod);
    }

    if (worldHit.kind == GameplayWorldHitKind::Chest || worldHit.kind == GameplayWorldHitKind::Corpse)
    {
        return canActivateInteractionContainerInspectEvent(view, inspectHit, inputMethod);
    }

    if (worldHit.kind == GameplayWorldHitKind::EventTarget)
    {
        return canActivateInteractionEventTargetInspectEvent(view, inspectHit, inputMethod);
    }

    return canActivateInteractionInspectEvent(view, inspectHit, inputMethod);
}

bool OutdoorInteractionController::dispatchWorldActivation(
    OutdoorGameView &view,
    const GameplayWorldHit &worldHit)
{
    if (!worldHit.hasHit)
    {
        return false;
    }

    const OutdoorGameView::InspectHit inspectHit = inspectHitFromGameplayWorldHit(worldHit);

    if (worldHit.kind == GameplayWorldHitKind::Actor)
    {
        return tryActivateActorInspectEvent(view, inspectHit);
    }

    if (worldHit.kind == GameplayWorldHitKind::WorldItem)
    {
        return tryActivateWorldItemInspectEvent(view, inspectHit);
    }

    if (worldHit.kind == GameplayWorldHitKind::Chest || worldHit.kind == GameplayWorldHitKind::Corpse)
    {
        return tryActivateContainerInspectEvent(view, inspectHit);
    }

    if (worldHit.kind == GameplayWorldHitKind::EventTarget)
    {
        return tryActivateEventTargetInspectEvent(view, inspectHit);
    }

    return tryActivateInspectEvent(view, inspectHit);
}

bool OutdoorInteractionController::tryTriggerLocalEventById(OutdoorGameView &view, uint16_t eventId)
{
    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr || eventId == 0)
    {
        return false;
    }

    size_t previousMessageCount = 0;
    const bool executed = view.m_pOutdoorSceneRuntime != nullptr
        && view.m_pOutdoorSceneRuntime->executeEventById(
            view.m_pOutdoorSceneRuntime->localEventProgram(),
            eventId,
            std::nullopt,
            previousMessageCount
        );

    if (!executed)
    {
        pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        return false;
    }

    promotePendingMapMoveToTransitionDialog(*pEventRuntimeState);

    for (const std::string &statusMessage : pEventRuntimeState->statusMessages)
    {
        view.setStatusBarEvent(statusMessage);
    }
    pEventRuntimeState->statusMessages.clear();
    OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(view);

    OutdoorInteractionController::presentPendingEventDialog(view, previousMessageCount, true);
    pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    return true;
}

} // namespace OpenYAMM::Game
