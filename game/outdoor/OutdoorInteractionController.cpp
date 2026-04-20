#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorBillboardRenderer.h"
#include "game/events/EvtEnums.h"
#include "game/gameplay/GameplayDialogContextBuilder.h"
#include "game/gameplay/GameplayDialogUiFlow.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/gameplay/GameMechanics.h"
#include "game/app/GameSession.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/SpawnPreview.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/tables/ItemTable.h"
#include "game/SpriteObjectDefs.h"
#include "game/StringUtils.h"
#include "game/scene/OutdoorSceneRuntime.h"
#include <SDL3/SDL.h>
#include <bx/math.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr float InspectRayEpsilon = 0.0001f;
constexpr float Pi = 3.14159265358979323846f;
constexpr float BillboardSpatialCellSize = 2048.0f;
constexpr float OeNearHoverDistance = 512.0f;
constexpr float OeActorHoverDistance = 8192.0f;
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
constexpr uint32_t KillSpeechChancePercent = 20;

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
    int initialGold,
    const Party *pParty)
{
    if (!action.has_value()
        || action->kind != EventDialogActionKind::NpcTopic
        || eventRuntimeState.dialogueState.hostHouseId == 0
        || (eventRuntimeState.grantedItems.empty() && eventRuntimeState.grantedItemIds.empty())
        || pParty == nullptr)
    {
        return false;
    }

    if (!eventRuntimeState.removedItemIds.empty())
    {
        return true;
    }

    return pParty->gold() < initialGold;
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

    const auto overrideIterator =
        pEventRuntimeState->spriteOverrides.find(static_cast<uint32_t>(billboard.entityIndex));

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
    GameplayDialogController::Callbacks callbacks = {};
    callbacks.playSpeechReaction =
        [&view](size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
        {
            view.playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
        };
    callbacks.playHouseSound =
        [&view](uint32_t soundId)
        {
            if (view.m_pGameAudioSystem != nullptr)
            {
                view.m_pGameAudioSystem->playSound(soundId, GameAudioSystem::PlaybackGroup::HouseSpeech);
            }
        };
    callbacks.playCommonSound =
        [&view](SoundId soundId)
        {
            if (view.m_pGameAudioSystem != nullptr)
            {
                view.m_pGameAudioSystem->playCommonSound(soundId, GameAudioSystem::PlaybackGroup::Ui);
            }
        };
    callbacks.requestTravelAutosave =
        [&view]()
        {
            if (!view.m_gameSession.canSaveGameToPath())
            {
                return;
            }

            std::string error;

            if (view.m_gameSession.saveGameToPath(view.m_autosavePath, "", {}, error))
            {
                view.refreshSaveGameSlots();
            }
        };
    callbacks.stopTravelAudio =
        [&view]()
        {
            if (view.m_pGameAudioSystem != nullptr)
            {
                view.m_pGameAudioSystem->stopAllPlayback();
            }
        };
    callbacks.cancelMapTransition =
        [&view]()
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
        };
    callbacks.executeNpcTopicEvent =
        [&view](uint16_t eventId, size_t &previousMessageCount)
        {
            return view.m_pOutdoorSceneRuntime != nullptr
                && view.m_pOutdoorSceneRuntime->executeEventById(
                    std::nullopt,
                    eventId,
                    std::nullopt,
                    previousMessageCount
                );
        };

    return buildGameplayDialogContext(
        view.m_gameplayUiController,
        eventRuntimeState,
        view.m_activeEventDialog,
        view.m_eventDialogSelectionIndex,
        view.m_pOutdoorPartyRuntime != nullptr ? &view.m_pOutdoorPartyRuntime->party() : nullptr,
        view.m_pOutdoorWorldRuntime,
        view.m_pOutdoorSceneRuntime != nullptr ? &view.m_pOutdoorSceneRuntime->globalEventProgram() : nullptr,
        &view.data().houseTable(),
        &view.data().classSkillTable(),
        &view.data().npcDialogTable(),
        view.m_map ? &*view.m_map : nullptr,
        &view.data().mapEntries(),
        &view.data().rosterTable(),
        &view.data().arcomageLibrary(),
        resolveGameplayHudScreenState(view.m_gameplayUiController, view.m_activeEventDialog, view.m_pOutdoorWorldRuntime)
            == GameplayHudScreenState::Dialogue,
        std::move(callbacks));
}

void OutdoorInteractionController::setHeldInventoryItem(
    GameplayUiController::HeldInventoryItemState &heldInventoryItem,
    const InventoryItem &item)
{
    heldInventoryItem.active = true;
    heldInventoryItem.item = item;
    heldInventoryItem.grabCellOffsetX = 0;
    heldInventoryItem.grabCellOffsetY = 0;
    heldInventoryItem.grabOffsetX = 0.0f;
    heldInventoryItem.grabOffsetY = 0.0f;
}

bool OutdoorInteractionController::tryDisplaceHeldInventoryItem(OutdoorGameView &view)
{
    if (!view.m_heldInventoryItem.active)
    {
        return true;
    }

    if (view.m_pOutdoorPartyRuntime == nullptr)
    {
        return false;
    }

    Party &party = view.m_pOutdoorPartyRuntime->party();

    if (party.tryGrantInventoryItem(view.m_heldInventoryItem.item))
    {
        view.m_heldInventoryItem = {};
        return true;
    }

    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        return false;
    }

    const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();

    if (!view.m_pOutdoorWorldRuntime->spawnWorldItem(
            view.m_heldInventoryItem.item,
            moveState.x,
            moveState.y,
            moveState.footZ + view.m_cameraEyeHeight,
            view.m_cameraYawRadians))
    {
        return false;
    }

    view.m_heldInventoryItem = {};
    return true;
}



void OutdoorInteractionController::executeActiveDialogAction(OutdoorGameView &view)
{
    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    const std::optional<EventDialogAction> selectedAction =
        view.m_activeEventDialog.isActive
            && view.m_eventDialogSelectionIndex < view.m_activeEventDialog.actions.size()
        ? std::optional<EventDialogAction>(view.m_activeEventDialog.actions[view.m_eventDialogSelectionIndex])
        : std::nullopt;
    Party *pParty = view.m_pOutdoorPartyRuntime != nullptr ? &view.m_pOutdoorPartyRuntime->party() : nullptr;
    const int initialGold = pParty != nullptr ? pParty->gold() : 0;
    GameplayDialogController::Context context = createGameplayDialogContext(view, *pEventRuntimeState, "execute_active_dialog_action");
    const GameplayDialogController::Result result = view.m_gameplayDialogController.executeActiveDialogAction(context);
    const bool useHouseTradeItemReaction =
        shouldUseHouseTradeItemReaction(*pEventRuntimeState, selectedAction, initialGold, pParty);

    if (useHouseTradeItemReaction)
    {
        pEventRuntimeState->portraitFxRequests.clear();

        if (pParty != nullptr)
        {
            view.triggerPortraitFaceAnimation(
                pParty->activeMemberIndex(),
                FaceAnimationId::ItemSold);
        }
    }

    OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(view);

    if (result.shouldCloseActiveDialog)
    {
        OutdoorInteractionController::closeActiveEventDialog(view);
    }

    if (result.pendingInnRest.has_value())
    {
        view.startInnRest(result.pendingInnRest->houseId);
    }

    if (result.shouldOpenPendingEventDialog)
    {
        OutdoorInteractionController::presentPendingEventDialog(
            view,
            result.previousMessageCount,
            result.allowNpcFallbackContent);
    }
}



void OutdoorInteractionController::presentPendingEventDialog(OutdoorGameView &view, size_t previousMessageCount, bool allowNpcFallbackContent)
{
    GameplayDialogUiFlowState state = {
        view.m_gameplayUiController,
        view.m_overlayInteractionState,
        view.m_gameplayDialogController,
        view.m_eventDialogSelectionIndex
    };
    GameplayDialogUiFlowPresentOptions options = {};
    options.suppressInitialAcceptIfActivationKeysHeld = true;
    ::OpenYAMM::Game::presentPendingEventDialog(
        state,
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr,
        [&view](EventRuntimeState &eventRuntimeState)
        {
            return createGameplayDialogContext(view, eventRuntimeState, "present_pending_event_dialog");
        },
        previousMessageCount,
        allowNpcFallbackContent,
        options,
        [&view](const GameplayDialogController::PresentPendingDialogResult &result)
        {
            std::cout << "Opened "
                      << (view.m_activeEventDialog.isHouseDialog ? "house" : "npc")
                      << " dialog for id=" << view.m_activeEventDialog.sourceId << '\n';

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
                view.playSpeechReaction(activeMemberIndex, greetingSpeechId, true);
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

    GameplayDialogUiFlowState state = {
        view.m_gameplayUiController,
        view.m_overlayInteractionState,
        view.m_gameplayDialogController,
        view.m_eventDialogSelectionIndex
    };
    ::OpenYAMM::Game::closeActiveEventDialog(
        state,
        pEventRuntimeState,
        [&view](uint32_t hostHouseId)
        {
            if (hostHouseId != 0 && view.m_flipOnExitEnabled)
            {
                view.setCameraAngles(view.cameraYawRadians() + Pi, view.cameraPitchRadians());
            }
        });
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



std::optional<std::string> OutdoorInteractionController::resolveHoverStatusBarText(const OutdoorGameView &view, const OutdoorGameView::InspectHit &inspectHit)
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

        const DecorationBillboard &decoration = view.m_outdoorDecorationBillboardSet->billboards[inspectHit.bModelIndex];

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
            pDecorationEntry = view.m_outdoorDecorationBillboardSet->decorationTable.findByInternalName(decoration.name);
        }

        if (pDecorationEntry != nullptr && !pDecorationEntry->hint.empty())
        {
            return pDecorationEntry->hint;
        }

        return std::nullopt;
    }

    if (inspectHit.kind == "entity")
    {
        if (inspectHit.distance > OeNearHoverDistance)
        {
            return std::nullopt;
        }

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
        if (inspectHit.distance > OeNearHoverDistance)
        {
            return std::nullopt;
        }

        return resolveEventHintText(view, inspectHit.cogTriggeredNumber);
    }

    if (inspectHit.kind == "actor")
    {
        if (inspectHit.distance > OeActorHoverDistance || inspectHit.name.empty())
        {
            return std::nullopt;
        }

        return inspectHit.name;
    }

    return std::nullopt;
}



void OutdoorInteractionController::handleDialogueCloseRequest(OutdoorGameView &view)
{
    if (view.m_houseBankState.inputActive())
    {
        OutdoorInteractionController::returnToHouseBankMainDialog(view);
        return;
    }

    if (view.m_inventoryNestedOverlay.active
        && resolveGameplayHudScreenState(view.m_gameplayUiController, view.m_activeEventDialog, view.m_pOutdoorWorldRuntime)
               == GameplayHudScreenState::Dialogue)
    {
        view.closeInventoryNestedOverlay();
        return;
    }

    if (view.m_houseShopOverlay.active)
    {
        view.closeHouseShopOverlay();
        return;
    }

    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        OutdoorInteractionController::closeActiveEventDialog(view);
        view.m_overlayInteractionState.activateInspectLatch = true;
        return;
    }

    GameplayDialogController::Context context = createGameplayDialogContext(view, *pEventRuntimeState, "handle_dialogue_close_request");
    const GameplayDialogController::CloseDialogRequestResult result =
        view.m_gameplayDialogController.handleDialogueCloseRequest(context);

    if (result.shouldOpenPendingEventDialog)
    {
        OutdoorInteractionController::presentPendingEventDialog(view, result.previousMessageCount, result.allowNpcFallbackContent);
    }
    else if (result.shouldCloseActiveDialog)
    {
        OutdoorInteractionController::closeActiveEventDialog(view);
        view.m_overlayInteractionState.activateInspectLatch = true;
    }
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
    const GameplayDialogController::Result result = view.m_gameplayDialogController.openNpcDialogue(context, npcId);
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

    const ItemTable &itemTable = view.data().itemTable();

    for (const InventoryItem &item : pEventRuntimeState->grantedItems)
    {
        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        if (!OutdoorInteractionController::tryDisplaceHeldInventoryItem(view))
        {
            continue;
        }

        OutdoorInteractionController::setHeldInventoryItem(view.m_heldInventoryItem, item);
    }

    for (uint32_t itemId : pEventRuntimeState->grantedItemIds)
    {
        if (itemId == 0)
        {
            continue;
        }

        if (!OutdoorInteractionController::tryDisplaceHeldInventoryItem(view))
        {
            continue;
        }

        const InventoryItem item =
            ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::Generic);
        OutdoorInteractionController::setHeldInventoryItem(view.m_heldInventoryItem, item);
    }

    pEventRuntimeState->grantedItems.clear();
    pEventRuntimeState->grantedItemIds.clear();
}



void OutdoorInteractionController::refreshHouseBankInputDialog(OutdoorGameView &view)
{
    GameplayDialogUiFlowState state = {
        view.m_gameplayUiController,
        view.m_overlayInteractionState,
        view.m_gameplayDialogController,
        view.m_eventDialogSelectionIndex
    };
    ::OpenYAMM::Game::refreshHouseBankInputDialog(
        state,
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr,
        [&view](EventRuntimeState &eventRuntimeState)
        {
            return createGameplayDialogContext(view, eventRuntimeState, "refresh_house_bank_input_dialog");
        },
        (SDL_GetTicks() / 500u) % 2u == 0u);
}



void OutdoorInteractionController::returnToHouseBankMainDialog(OutdoorGameView &view)
{
    GameplayDialogUiFlowState state = {
        view.m_gameplayUiController,
        view.m_overlayInteractionState,
        view.m_gameplayDialogController,
        view.m_eventDialogSelectionIndex
    };
    const GameplayDialogController::Result result = ::OpenYAMM::Game::returnToHouseBankMainDialog(
        state,
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr,
        [&view](EventRuntimeState &eventRuntimeState)
        {
            return createGameplayDialogContext(view, eventRuntimeState, "return_to_house_bank_main_dialog");
        });

    if (result.shouldOpenPendingEventDialog)
    {
        OutdoorInteractionController::presentPendingEventDialog(
            view,
            result.previousMessageCount,
            result.allowNpcFallbackContent);
    }
}



void OutdoorInteractionController::confirmHouseBankInput(OutdoorGameView &view)
{
    GameplayDialogUiFlowState state = {
        view.m_gameplayUiController,
        view.m_overlayInteractionState,
        view.m_gameplayDialogController,
        view.m_eventDialogSelectionIndex
    };
    const GameplayDialogController::Result result = ::OpenYAMM::Game::confirmHouseBankInput(
        state,
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr,
        [&view](EventRuntimeState &eventRuntimeState)
        {
            return createGameplayDialogContext(view, eventRuntimeState, "confirm_house_bank_input");
        });

    if (result.shouldOpenPendingEventDialog)
    {
        OutdoorInteractionController::presentPendingEventDialog(view, result.previousMessageCount, result.allowNpcFallbackContent);
    }
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

            if (facePickMode == FacePickMode::InteractionActivatable
                && !outdoorFaceIsInteractionActivatable(face.attributes, face.cogTriggeredNumber))
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

            const auto overrideIterator =
                pEventRuntimeState->spriteOverrides.find(static_cast<uint32_t>(billboard.entityIndex));

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

            if (view.m_pendingSpellCast.active && pActorState != nullptr && pActorState->isDead)
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

            if (view.m_pendingSpellCast.active && pActorState->isDead)
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

bool OutdoorInteractionController::tryActivateInspectEvent(OutdoorGameView &view, const OutdoorGameView::InspectHit &inspectHit)
{
    std::cout << "tryActivateInspectEvent: kind=" << inspectHit.kind
              << " index=" << inspectHit.bModelIndex
              << " name=" << inspectHit.name
              << " npc=" << inspectHit.npcId
              << " group=" << inspectHit.actorGroup
              << " dist=" << inspectHit.distance
              << '\n';

    if (inspectHit.kind == "world_item")
    {
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
            view.setStatusBarEvent("Picked up " + std::to_string(goldAmount) + " gold");

            if (EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState())
            {
                pEventRuntimeState->lastActivationResult =
                    "picked up " + std::to_string(goldAmount) + " gold";
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
            view.playSpeechReaction(recipientMemberIndex, SpeechId::FoundItem, true);
            view.setStatusBarEvent("Picked up " + itemName);

            if (EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState())
            {
                pEventRuntimeState->lastActivationResult = "picked up " + itemName;
            }

            return true;
        }

        if (!view.m_heldInventoryItem.active)
        {
            OutdoorWorldRuntime::WorldItemState worldItem = {};

            if (!view.m_pOutdoorWorldRuntime->takeWorldItem(inspectHit.bModelIndex, worldItem))
            {
                return false;
            }

            view.m_heldInventoryItem.active = true;
            view.m_heldInventoryItem.item = worldItem.item;
            view.m_heldInventoryItem.grabCellOffsetX = 0;
            view.m_heldInventoryItem.grabCellOffsetY = 0;
            view.m_heldInventoryItem.grabOffsetX = 0.0f;
            view.m_heldInventoryItem.grabOffsetY = 0.0f;
            view.m_pOutdoorPartyRuntime->party().requestSound(SoundId::Gold);
            view.playSpeechReaction(view.m_pOutdoorPartyRuntime->party().activeMemberIndex(), SpeechId::FoundItem, true);
            view.setStatusBarEvent("Picked up " + itemName);

            if (EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState())
            {
                pEventRuntimeState->lastActivationResult = "picked up " + itemName + " into hand";
            }

            return true;
        }

        return false;
    }

    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (!view.m_outdoorMapData || pEventRuntimeState == nullptr)
    {
        std::cout << "Outdoor inspect activation ignored: runtime not available\n";
        return false;
    }

    uint16_t eventId = 0;

    if (inspectHit.kind == "actor" && view.m_pOutdoorWorldRuntime != nullptr)
    {
        const std::optional<size_t> runtimeActorIndex = view.resolveRuntimeActorIndexForInspectHit(inspectHit);

        if (runtimeActorIndex)
        {
            const OutdoorWorldRuntime::MapActorState *pActorState =
                view.m_pOutdoorWorldRuntime->mapActorState(*runtimeActorIndex);

            std::cout << "Actor activation target: runtime=" << *runtimeActorIndex
                      << " name=" << inspectHit.name
                      << " dead=" << (pActorState != nullptr && pActorState->isDead ? "yes" : "no")
                      << " invisible=" << (pActorState != nullptr && pActorState->isInvisible ? "yes" : "no")
                      << " hp=" << (pActorState != nullptr ? pActorState->currentHp : -1)
                      << " ai=" << (pActorState != nullptr ? static_cast<int>(pActorState->aiState) : -1)
                      << '\n';

            if (pActorState != nullptr && pActorState->isDead)
            {
                if (!view.m_pOutdoorWorldRuntime->openMapActorCorpseView(*runtimeActorIndex))
                {
                    std::cout << "Corpse activation: runtime=" << *runtimeActorIndex
                              << " corpse_view=missing\n";
                    view.setStatusBarEvent("Nothing here");
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " empty";
                    return true;
                }

                const OutdoorWorldRuntime::CorpseViewState *pOpenedCorpseView =
                    view.m_pOutdoorWorldRuntime->activeCorpseView();
                std::cout << "Corpse activation: runtime=" << *runtimeActorIndex
                          << " corpse_view=open"
                          << " entries=" << (pOpenedCorpseView != nullptr ? pOpenedCorpseView->items.size() : 0)
                          << " title=" << (pOpenedCorpseView != nullptr ? pOpenedCorpseView->title : std::string("-"))
                          << '\n';

                int lootedGoldAmount = 0;
                std::string firstLootedItemName;
                bool lootedAny = false;
                bool blockedByInventory = false;

                while (const OutdoorWorldRuntime::CorpseViewState *pCorpseView = view.m_pOutdoorWorldRuntime->activeCorpseView())
                {
                    if (pCorpseView->items.empty())
                    {
                        break;
                    }

                    const OutdoorWorldRuntime::ChestItemState &item = pCorpseView->items.front();

                    if (item.isGold)
                    {
                        OutdoorWorldRuntime::ChestItemState removedItem = {};

                        if (!view.m_pOutdoorWorldRuntime->takeActiveCorpseItem(0, removedItem))
                        {
                            break;
                        }

                        const int goldAmount = static_cast<int>(removedItem.goldAmount);
                        view.m_pOutdoorPartyRuntime->party().addGold(goldAmount);
                        lootedGoldAmount += goldAmount;
                        lootedAny = lootedAny || goldAmount > 0;
                        continue;
                    }

                    const ItemDefinition *pItemDefinition = view.data().itemTable().get(item.itemId);
                    const std::string itemName =
                        pItemDefinition != nullptr
                        ? (!pItemDefinition->unidentifiedName.empty()
                            && pItemDefinition->unidentifiedName != "0"
                            && pItemDefinition->unidentifiedName != "N / A"
                            ? pItemDefinition->unidentifiedName
                            : pItemDefinition->name)
                        : "item";

                    if (view.m_pOutdoorPartyRuntime->party().tryGrantItem(item.itemId, item.quantity))
                    {
                        OutdoorWorldRuntime::ChestItemState removedItem = {};

                        if (!view.m_pOutdoorWorldRuntime->takeActiveCorpseItem(0, removedItem))
                        {
                            break;
                        }

                        if (firstLootedItemName.empty())
                        {
                            firstLootedItemName = itemName;
                        }

                        lootedAny = true;
                        continue;
                    }

                    if (!view.m_heldInventoryItem.active)
                    {
                        OutdoorWorldRuntime::ChestItemState removedItem = {};

                        if (!view.m_pOutdoorWorldRuntime->takeActiveCorpseItem(0, removedItem))
                        {
                            break;
                        }

                        view.m_heldInventoryItem.active = true;
                        view.m_heldInventoryItem.item = {};
                        view.m_heldInventoryItem.item.objectDescriptionId = removedItem.itemId;
                        view.m_heldInventoryItem.item.quantity = removedItem.quantity;
                        view.m_heldInventoryItem.item.width = removedItem.width;
                        view.m_heldInventoryItem.item.height = removedItem.height;
                        view.m_heldInventoryItem.item.gridX = removedItem.gridX;
                        view.m_heldInventoryItem.item.gridY = removedItem.gridY;
                        view.m_heldInventoryItem.grabCellOffsetX = 0;
                        view.m_heldInventoryItem.grabCellOffsetY = 0;
                        view.m_heldInventoryItem.grabOffsetX = 0.0f;
                        view.m_heldInventoryItem.grabOffsetY = 0.0f;

                        if (firstLootedItemName.empty())
                        {
                            firstLootedItemName = itemName;
                        }

                        lootedAny = true;
                        blockedByInventory = true;
                        break;
                    }

                    blockedByInventory = true;
                    break;
                }

                if (!firstLootedItemName.empty())
                {
                    view.setStatusBarEvent(formatFoundItemStatusText(lootedGoldAmount, firstLootedItemName));
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " auto-looted item";
                }
                else if (lootedGoldAmount > 0)
                {
                    view.setStatusBarEvent(formatFoundGoldStatusText(lootedGoldAmount));
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " auto-looted gold";
                }
                else if (blockedByInventory)
                {
                    const std::string partyStatus = view.m_pOutdoorPartyRuntime->party().lastStatus();
                    view.setStatusBarEvent(partyStatus.empty() ? "Pack is Full!" : partyStatus);
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " blocked by inventory";
                }
                else
                {
                    view.setStatusBarEvent("Nothing here");
                    pEventRuntimeState->lastActivationResult =
                        "corpse " + std::to_string(*runtimeActorIndex) + " empty";
                }

                std::cout << "Looting corpse for actor=" << *runtimeActorIndex
                          << " gold=" << lootedGoldAmount
                          << " item=" << (firstLootedItemName.empty() ? "-" : firstLootedItemName)
                          << " blocked=" << (blockedByInventory ? "yes" : "no") << '\n';
                return lootedAny || blockedByInventory;
            }

            std::cout << "Actor activation fallback: runtime=" << *runtimeActorIndex
                      << " dead=no"
                      << " npc=" << inspectHit.npcId
                      << " group=" << inspectHit.actorGroup
                      << '\n';
        }
        else
        {
            std::cout << "Actor activation fallback: runtime unresolved"
                      << " npc=" << inspectHit.npcId
                      << " group=" << inspectHit.actorGroup
                      << '\n';
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

            const std::optional<size_t> runtimeActorIndex = view.resolveRuntimeActorIndexForInspectHit(inspectHit);

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
        faceTalkingActor();
        GameplayDialogController::Context context =
            createGameplayDialogContext(view, *pEventRuntimeState, "activate_actor_npc_dialog");
        const GameplayDialogController::Result result =
            view.m_gameplayDialogController.openNpcDialogue(context, static_cast<uint32_t>(inspectHit.npcId));
        pEventRuntimeState->lastActivationResult = "npc " + std::to_string(inspectHit.npcId) + " engaged";

        if (result.shouldOpenPendingEventDialog)
        {
            OutdoorInteractionController::presentPendingEventDialog(view, result.previousMessageCount, result.allowNpcFallbackContent);
        }

        std::cout << "Opening direct NPC dialog for npc=" << inspectHit.npcId << '\n';
        return true;
    }

    if (inspectHit.kind == "actor")
    {
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
                std::cout << "Actor generic dialog fallback: resolution found but no news text\n";
                return false;
            }

            faceTalkingActor();
            GameplayDialogController::Context context =
                createGameplayDialogContext(view, *pEventRuntimeState, "activate_actor_news_dialog");
            const GameplayDialogController::Result result = view.m_gameplayDialogController.openNpcNews(
                context,
                resolution->npcId,
                resolution->newsId,
                inspectHit.name,
                *newsText);
            pEventRuntimeState->lastActivationResult =
                "npc news group " + std::to_string(inspectHit.actorGroup) + " engaged";

            if (result.shouldOpenPendingEventDialog)
            {
                OutdoorInteractionController::presentPendingEventDialog(view, result.previousMessageCount, result.allowNpcFallbackContent);
            }

            std::cout << "Opening generic NPC news for actor group=" << inspectHit.actorGroup
                      << " npc=" << resolution->npcId
                      << " news=" << resolution->newsId << '\n';
            return true;
        }

        std::cout << "Actor generic dialog fallback: no resolution\n";
    }

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
            std::cout << "Outdoor inspect activation ignored: face is not interaction-activatable\n";
            return false;
        }

        eventId = inspectHit.cogTriggeredNumber;
    }
    else
    {
        pEventRuntimeState->lastActivationResult = "no activatable event on hovered target";
        std::cout << "Outdoor inspect activation ignored: unsupported target kind '"
                  << inspectHit.kind << "'\n";
        return false;
    }

    if (eventId == 0)
    {
        pEventRuntimeState->lastActivationResult = "no event on hovered target";
        std::cout << "Outdoor inspect activation ignored: target has no event id\n";
        return false;
    }

    std::cout << "Activating outdoor event " << eventId
              << " from " << inspectHit.kind
              << " index=" << inspectHit.bModelIndex << '\n';

    size_t previousMessageCount = 0;

    const bool executed = view.m_pOutdoorSceneRuntime != nullptr
        && view.m_pOutdoorSceneRuntime->executeEventById(
            view.m_pOutdoorSceneRuntime->localEventProgram(),
            eventId,
            decorationContext,
            previousMessageCount
        );

    if (!executed)
    {
        pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        std::cout << "Outdoor event " << eventId << " unresolved\n";
        return false;
    }

    for (const std::string &statusMessage : pEventRuntimeState->statusMessages)
    {
        view.setStatusBarEvent(statusMessage);
    }
    pEventRuntimeState->statusMessages.clear();
    OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(view);

    OutdoorInteractionController::presentPendingEventDialog(view, previousMessageCount, true);

    pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    std::cout << "Outdoor event " << eventId << " executed\n";
    return true;
}



bool OutdoorInteractionController::canActivateInspectEvent(const OutdoorGameView &view, const OutdoorGameView::InspectHit &inspectHit)
{
    if (inspectHit.kind == "world_item")
    {
        return !view.m_heldInventoryItem.active;
    }

    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (!view.m_outdoorMapData || pEventRuntimeState == nullptr)
    {
        return false;
    }

    if (inspectHit.kind == "actor")
    {
        if (view.m_pOutdoorWorldRuntime != nullptr)
        {
            const std::optional<size_t> runtimeActorIndex = view.resolveRuntimeActorIndexForInspectHit(inspectHit);

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
            return true;
        }

        return resolveGenericActorDialog(
            view.m_map ? view.m_map->fileName : std::string(),
            inspectHit.name,
            inspectHit.actorGroup,
            *pEventRuntimeState,
            view.data().npcDialogTable()
        ).has_value();
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



bool OutdoorInteractionController::tryTriggerLocalEventById(OutdoorGameView &view, uint16_t eventId)
{
    EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr || eventId == 0)
    {
        return false;
    }

    std::cout << "Triggering local outdoor event " << eventId << " from hotkey\n";

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
        std::cout << "Outdoor hotkey event " << eventId << " unresolved\n";
        return false;
    }

    for (const std::string &statusMessage : pEventRuntimeState->statusMessages)
    {
        view.setStatusBarEvent(statusMessage);
    }
    pEventRuntimeState->statusMessages.clear();
    OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(view);

    OutdoorInteractionController::presentPendingEventDialog(view, previousMessageCount, true);
    pEventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    std::cout << "Outdoor hotkey event " << eventId << " executed\n";
    return true;
}



void OutdoorInteractionController::applyPendingCombatEvents(OutdoorGameView &view)
{
    if (view.m_pOutdoorWorldRuntime == nullptr || view.m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    for (const OutdoorWorldRuntime::CombatEvent &event : view.m_pOutdoorWorldRuntime->pendingCombatEvents())
    {
        if (event.type == OutdoorWorldRuntime::CombatEvent::Type::PartyProjectileActorImpact)
        {
            const Character *pSourceMember = view.m_pOutdoorPartyRuntime->party().member(event.sourcePartyMemberIndex);
            const OutdoorWorldRuntime::MapActorState *pTargetActor = nullptr;
            std::string sourceName = pSourceMember != nullptr && !pSourceMember->name.empty()
                ? pSourceMember->name
                : "party";
            std::string targetName = "monster";

            for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
            {
                const OutdoorWorldRuntime::MapActorState *pActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

                if (pActor != nullptr && pActor->actorId == event.targetActorId)
                {
                    pTargetActor = pActor;
                    targetName = pActor->displayName;
                    break;
                }
            }

            if (!event.hit)
            {
                view.triggerPortraitFaceAnimation(event.sourcePartyMemberIndex, FaceAnimationId::AttackMiss);
                view.playSpeechReaction(event.sourcePartyMemberIndex, SpeechId::AttackMiss, false);
                view.showCombatStatusBarEvent(sourceName + " misses " + targetName);
            }
            else if (event.killed)
            {
                view.triggerPortraitFaceAnimation(event.sourcePartyMemberIndex, FaceAnimationId::AttackHit);
                SpeechId speechId = SpeechId::AttackHit;

                if ((currentAnimationTicks() + event.targetActorId) % 100u < KillSpeechChancePercent)
                {
                    speechId = pTargetActor != nullptr && pTargetActor->maxHp >= 100
                        ? SpeechId::KillStrongEnemy
                        : SpeechId::KillWeakEnemy;
                }

                view.playSpeechReaction(event.sourcePartyMemberIndex, speechId, false);
                if (event.spellId > 0)
                {
                    view.showCombatStatusBarEvent(
                        sourceName + " deals " + std::to_string(event.damage) + " damage killing " + targetName);
                }
                else
                {
                    view.showCombatStatusBarEvent(
                        sourceName + " inflicts " + std::to_string(event.damage) + " points killing " + targetName);
                }
            }
            else
            {
                view.triggerPortraitFaceAnimation(event.sourcePartyMemberIndex, FaceAnimationId::AttackHit);
                view.playSpeechReaction(event.sourcePartyMemberIndex, SpeechId::AttackHit, false);
                if (event.spellId > 0)
                {
                    view.showCombatStatusBarEvent(
                        sourceName + " deals " + std::to_string(event.damage) + " damage to " + targetName);
                }
                else
                {
                    view.showCombatStatusBarEvent(
                        sourceName + " shoots " + targetName + " for " + std::to_string(event.damage) + " points");
                }
            }

            if (event.hit
                && event.damage > 0
                && event.spellId == 0
                && pSourceMember != nullptr
                && pSourceMember->vampiricHealFraction > 0.0f)
            {
                view.m_pOutdoorPartyRuntime->party().healMember(
                    event.sourcePartyMemberIndex,
                    std::max(1, static_cast<int>(std::round(
                        static_cast<float>(event.damage) * pSourceMember->vampiricHealFraction))));
            }

            continue;
        }

        if (event.type != OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact
            && event.type != OutdoorWorldRuntime::CombatEvent::Type::PartyProjectileImpact)
        {
            continue;
        }

        std::string sourceName = "monster";
        uint32_t sourceAttackPreferences = 0;

        for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            const OutdoorWorldRuntime::MapActorState *pActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pActor != nullptr && pActor->actorId == event.sourceId)
            {
                sourceName = pActor->displayName;

                if (const MonsterTable::MonsterStatsEntry *pStats =
                        view.data().monsterTable().findStatsById(pActor->monsterId))
                {
                    sourceAttackPreferences = pStats->attackPreferences;
                }

                break;
            }
        }

        if (event.sourceId == std::numeric_limits<uint32_t>::max())
        {
            sourceName = event.spellId > 0 ? "event spell" : "event";
        }

        const std::string status = event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact
            ? sourceName + " hit party for " + std::to_string(event.damage)
            : sourceName
                + (event.spellId > 0 ? " spell hit party for " : " projectile hit party for ")
                + std::to_string(event.damage);

        Party &party = view.m_pOutdoorPartyRuntime->party();
        std::optional<size_t> targetMemberIndex = std::nullopt;

        if (!event.affectsAllParty)
        {
            targetMemberIndex = party.chooseMonsterAttackTarget(
                sourceAttackPreferences,
                event.sourceId ^ static_cast<uint32_t>(event.damage) ^ static_cast<uint32_t>(event.spellId));
        }

        Character *pTargetMember =
            targetMemberIndex ? view.m_pOutdoorPartyRuntime->party().member(*targetMemberIndex) : nullptr;
        const bool ignorePhysicalDamage =
            pTargetMember != nullptr
            && pTargetMember->physicalDamageImmune
            && (event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact || event.spellId == 0);

        if (ignorePhysicalDamage)
        {
            view.showCombatStatusBarEvent("Mistform ignores physical damage");
            continue;
        }

        const bool isPhysicalProjectile =
            event.type == OutdoorWorldRuntime::CombatEvent::Type::PartyProjectileImpact && event.spellId == 0;
        const auto adjustedDamageForMember =
            [event, isPhysicalProjectile](const Character &member) -> int
            {
                if (isPhysicalProjectile && member.halfMissileDamage)
                {
                    return std::max(1, (event.damage + 1) / 2);
                }

        return event.damage;
            };
        bool damagedParty = false;
        std::vector<size_t> damagedMemberIndices;

        if (event.affectsAllParty)
        {
            bool wroteStatus = false;

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                Character *pMember = party.member(memberIndex);

                if (pMember == nullptr || pMember->health <= 0)
                {
                    continue;
                }

                if (pMember->physicalDamageImmune
                    && (event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact || event.spellId == 0))
                {
                    continue;
                }

                const bool applied = party.applyDamageToMember(
                    memberIndex,
                    adjustedDamageForMember(*pMember),
                    wroteStatus ? "" : status);
                damagedParty = applied || damagedParty;

                if (applied)
                {
                    damagedMemberIndices.push_back(memberIndex);
                }
                wroteStatus = wroteStatus || damagedParty;
            }
        }
        else
        {
            const int adjustedDamage =
                pTargetMember != nullptr ? adjustedDamageForMember(*pTargetMember) : event.damage;
            damagedParty = targetMemberIndex ? party.applyDamageToMember(*targetMemberIndex, adjustedDamage, status) : false;

            if (damagedParty && targetMemberIndex.has_value())
            {
                damagedMemberIndices.push_back(*targetMemberIndex);
            }
        }

        if (damagedParty)
        {
            // We intentionally keep physical projectiles on the same armor-impact path as melee hits.
            if (event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact || isPhysicalProjectile)
            {
                for (size_t memberIndex : damagedMemberIndices)
                {
                    party.requestDamageImpactSoundForMember(memberIndex);
                }
            }

            if (event.affectsAllParty)
            {
                view.triggerPortraitFaceAnimationForAllLivingMembers(FaceAnimationId::DamagedParty);
            }
            else
            {
                view.triggerPortraitFaceAnimation(*targetMemberIndex, FaceAnimationId::Damaged);
            }

            std::cout << "Party damaged source=" << sourceName
                      << " damage=" << event.damage
                      << " kind="
                      << (event.type == OutdoorWorldRuntime::CombatEvent::Type::MonsterMeleeImpact
                              ? "melee"
                              : (event.spellId > 0 ? "spell" : "projectile"))
                      << '\n';
        }
    }

    view.m_pOutdoorWorldRuntime->clearPendingCombatEvents();
}



} // namespace OpenYAMM::Game
