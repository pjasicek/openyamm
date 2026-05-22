#include "game/indoor/IndoorMovementController.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorCollisionPrimitives.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MaximumRise = 50.0f;
constexpr float MaximumDrop = 160.0f;
constexpr float ActorLedgeDropGuardHeight = 100.0f;
constexpr float MaximumStepUpFromCurrentFootZ = 128.0f;
constexpr float MaximumUphillSlopeNormalZ = 0.70767211914f;
constexpr float SlideFactor = 0.89263916f;
constexpr float SteepFloorSlideHorizontalSpeed = 10.0f;
constexpr float SteepFloorSlideDownSpeed = 20.0f;
constexpr float GravityPerSecond = 960.0f;
constexpr float GroundSnapSlack = 8.0f;
constexpr float CylinderCollisionHorizontalEpsilon = 0.0001f;
constexpr float SteepFloorUphillEpsilon = 0.01f;
constexpr float IndoorMovementSubstepDistance = 24.0f;
constexpr int MaxIndoorMovementSubsteps = 64;
constexpr float WallOverlapRecoveryMinVelocity = 480.0f;

bool hasCylinderCollisionHorizontalComponent(float x, float y)
{
    return x * x + y * y > CylinderCollisionHorizontalEpsilon * CylinderCollisionHorizontalEpsilon;
}

int indoorMovementSubstepCount(
    const IndoorMoveState &state,
    float desiredVelocityX,
    float desiredVelocityY,
    bool jumpRequested,
    float deltaSeconds,
    float jumpVelocity
)
{
    const float horizontalVelocity =
        std::sqrt(desiredVelocityX * desiredVelocityX + desiredVelocityY * desiredVelocityY);
    const float horizontalDistance = horizontalVelocity * deltaSeconds;
    const float jumpSpeed = jumpRequested ? jumpVelocity : 0.0f;
    const float verticalSpeed = std::max(std::fabs(state.verticalVelocity), jumpSpeed);
    const float verticalDistance = verticalSpeed * deltaSeconds + GravityPerSecond * deltaSeconds * deltaSeconds;
    const float movementDistance = std::max(horizontalDistance, verticalDistance);

    if (movementDistance <= IndoorMovementSubstepDistance)
    {
        return 1;
    }

    const int substepCount = static_cast<int>(std::ceil(movementDistance / IndoorMovementSubstepDistance));
    return std::clamp(substepCount, 1, MaxIndoorMovementSubsteps);
}

const char *indoorTraceFaceKindName(IndoorFaceKind kind)
{
    switch (kind)
    {
        case IndoorFaceKind::Unknown:
            return "unknown";
        case IndoorFaceKind::Floor:
            return "floor";
        case IndoorFaceKind::Ceiling:
            return "ceiling";
        case IndoorFaceKind::Wall:
            return "wall";
    }

    return "unknown";
}

bool indoorFloorTooSteepForUphillStep(
    const IndoorMapData &indoorMapData,
    const MapDeltaData *pMapDeltaData,
    const IndoorFloorSample &floor,
    float currentFootZ
)
{
    if (!floor.hasFloor
        || floor.faceIndex >= indoorMapData.faces.size()
        || floor.normalZ <= 0.0f
        || floor.normalZ >= MaximumUphillSlopeNormalZ)
    {
        return false;
    }

    if (!floor.isWalkable)
    {
        return floor.height > currentFootZ + SteepFloorUphillEpsilon;
    }

    if (floor.height <= currentFootZ + GroundSnapSlack)
    {
        return false;
    }

    const IndoorFace &face = indoorMapData.faces[floor.faceIndex];
    const uint32_t attributes =
        pMapDeltaData != nullptr && floor.faceIndex < pMapDeltaData->faceAttributes.size()
            ? pMapDeltaData->faceAttributes[floor.faceIndex]
            : face.attributes;

    if (face.facetType == 4 && hasFaceAttribute(attributes, FaceAttribute::Invisible))
    {
        return false;
    }

    return true;
}

bool indoorFaceIsSteepFloorCollisionSurface(const IndoorFaceGeometryData &geometry)
{
    if (geometry.normal.z <= 0.0f || geometry.normal.z >= MaximumUphillSlopeNormalZ)
    {
        return false;
    }

    if (geometry.facetType == 4 && hasFaceAttribute(geometry.attributes, FaceAttribute::Invisible))
    {
        return false;
    }

    return geometry.facetType == 3 || geometry.facetType == 4 || geometry.kind == IndoorFaceKind::Floor;
}

bool indoorFaceBlocksAsWallOverlap(const IndoorFaceGeometryData &geometry, float footZ)
{
    if (geometry.kind != IndoorFaceKind::Wall
        || geometry.isPortal
        || hasFaceAttribute(geometry.attributes, FaceAttribute::Untouchable)
        || geometry.maxZ <= footZ + MaximumRise)
    {
        return false;
    }

    return !indoorFaceIsSteepFloorCollisionSurface(geometry);
}

bool indoorBodyStartsInsideSteepFloorSweepRadius(
    const IndoorFaceGeometryData &geometry,
    const IndoorBodyDimensions &body,
    float x,
    float y,
    float footZ
)
{
    if (!indoorFaceIsSteepFloorCollisionSurface(geometry) || geometry.vertices.empty())
    {
        return false;
    }

    const float lowHeightOffset = std::max(0.0f, body.radius);
    const float highHeightOffset = std::max(lowHeightOffset, body.height - body.radius);
    const float midHeightOffset = (lowHeightOffset + highHeightOffset) * 0.5f;
    const std::array<float, 3> heightOffsets = {{lowHeightOffset, midHeightOffset, highHeightOffset}};

    for (float heightOffset : heightOffsets)
    {
        const bx::Vec3 sphereCenter = {x, y, footZ + heightOffset};
        const bx::Vec3 delta = {
            sphereCenter.x - geometry.vertices.front().x,
            sphereCenter.y - geometry.vertices.front().y,
            sphereCenter.z - geometry.vertices.front().z
        };
        const float planeDistance =
            std::fabs(delta.x * geometry.normal.x + delta.y * geometry.normal.y + delta.z * geometry.normal.z);

        if (planeDistance <= body.radius + 0.5f)
        {
            return true;
        }
    }

    return false;
}

bx::Vec3 applySteepFloorCollisionResponse(
    const bx::Vec3 &step,
    const IndoorFaceGeometryData *pGeometry,
    float deltaSeconds
)
{
    if (pGeometry == nullptr || !indoorFaceIsSteepFloorCollisionSurface(*pGeometry))
    {
        return step;
    }

    bx::Vec3 response = step;

    if (response.z > 0.0f)
    {
        response.z = 0.0f;
    }

    response.x += pGeometry->normal.x * SteepFloorSlideHorizontalSpeed * deltaSeconds;
    response.y += pGeometry->normal.y * SteepFloorSlideHorizontalSpeed * deltaSeconds;
    response.z -= SteepFloorSlideDownSpeed * deltaSeconds;
    return response;
}

bool indoorFaceIsInvisibleSupportRamp(const IndoorFace &face, uint32_t attributes)
{
    return face.facetType == 4 && hasFaceAttribute(attributes, FaceAttribute::Invisible);
}

void appendUniqueFaceId(std::vector<uint16_t> &faceIds, uint16_t faceId)
{
    if (std::find(faceIds.begin(), faceIds.end(), faceId) == faceIds.end())
    {
        faceIds.push_back(faceId);
    }
}

void appendValidSectorId(const IndoorMapData &indoorMapData, std::vector<uint16_t> &sectorIds, uint16_t sectorId)
{
    if (sectorId >= indoorMapData.sectors.size())
    {
        return;
    }

    if (std::find(sectorIds.begin(), sectorIds.end(), sectorId) == sectorIds.end())
    {
        sectorIds.push_back(sectorId);
    }
}

IndoorFloorSample sampleInvisibleSupportFaceWithFootprint(
    const IndoorMapData &indoorMapData,
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    uint16_t faceId,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    float radius,
    const std::vector<uint8_t> *pFaceExclusionMask
)
{
    if (faceId >= indoorMapData.faces.size())
    {
        return {};
    }

    const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(indoorMapData, vertices, faceId);

    if (pGeometry == nullptr
        || pGeometry->kind != IndoorFaceKind::Floor
        || !pGeometry->isWalkable
        || !indoorFaceIsInvisibleSupportRamp(indoorMapData.faces[faceId], pGeometry->attributes))
    {
        return {};
    }

    const float probeRadius = std::max(radius, 0.0f);
    const float diagonalProbeRadius = probeRadius * 0.70710678f;
    const std::array<std::pair<float, float>, 9> probes = {{
        {0.0f, 0.0f},
        {probeRadius, 0.0f},
        {-probeRadius, 0.0f},
        {0.0f, probeRadius},
        {0.0f, -probeRadius},
        {diagonalProbeRadius, diagonalProbeRadius},
        {diagonalProbeRadius, -diagonalProbeRadius},
        {-diagonalProbeRadius, diagonalProbeRadius},
        {-diagonalProbeRadius, -diagonalProbeRadius},
    }};

    for (const std::pair<float, float> &probe : probes)
    {
        const IndoorFloorSample probeSample = sampleIndoorFloorOnFace(
            indoorMapData,
            vertices,
            faceId,
            x + probe.first,
            y + probe.second,
            z,
            maxRise,
            maxDrop,
            pFaceExclusionMask,
            &geometryCache);

        if (!probeSample.hasFloor)
        {
            continue;
        }

        const float centerHeight = calculateIndoorFaceHeight(*pGeometry, x, y);
        const float centerDelta = centerHeight - z;

        if (centerDelta > maxRise || centerDelta < -maxDrop)
        {
            continue;
        }

        IndoorFloorSample sample = probeSample;
        sample.height = centerHeight;
        sample.normalZ = pGeometry->normal.z;
        sample.sectorId = static_cast<int16_t>(pGeometry->sectorId);
        sample.faceIndex = faceId;
        return sample;
    }

    return {};
}

float resolveDoorDistance(
    const MapDeltaDoor &door,
    const std::optional<EventRuntimeState> *pEventRuntimeState
)
{
    RuntimeMechanismState runtimeMechanism = {};
    runtimeMechanism.state = door.state;
    runtimeMechanism.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
    runtimeMechanism.currentDistance = EventRuntime::calculateMechanismDistance(door, runtimeMechanism);
    runtimeMechanism.isMoving =
        door.state == static_cast<uint16_t>(EvtMechanismState::Opening)
        || door.state == static_cast<uint16_t>(EvtMechanismState::Closing);

    if (pEventRuntimeState != nullptr && pEventRuntimeState->has_value())
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator iterator =
            (*pEventRuntimeState)->mechanisms.find(door.doorId);

        if (iterator != (*pEventRuntimeState)->mechanisms.end())
        {
            runtimeMechanism = iterator->second;
        }
    }

    return runtimeMechanism.currentDistance;
}

bool shouldIgnoreExistingActorOverlap(
    float currentX,
    float currentY,
    const IndoorBodyDimensions &body,
    const IndoorActorCollision &collider,
    bool actorVsActor)
{
    if (!actorVsActor)
    {
        return false;
    }

    const float minimumDistance = body.radius + collider.radius;

    if (minimumDistance <= 0.0f)
    {
        return false;
    }

    const float currentDeltaX = currentX - collider.x;
    const float currentDeltaY = currentY - collider.y;
    const float currentDistanceSquared = currentDeltaX * currentDeltaX + currentDeltaY * currentDeltaY;
    const float minimumDistanceSquared = minimumDistance * minimumDistance;

    if (currentDistanceSquared >= minimumDistanceSquared)
    {
        return false;
    }

    return true;
}

IndoorSweptBody buildPrimitiveSweptBody(
    float x,
    float y,
    float footZ,
    const IndoorBodyDimensions &body
)
{
    IndoorSweptBody sweptBody = {};
    const float lowHeightOffset = std::max(0.0f, body.radius);
    const float highHeightOffset = std::max(lowHeightOffset, body.height - body.radius);

    sweptBody.lowSphere.center = {x, y, footZ + lowHeightOffset};
    sweptBody.lowSphere.radius = body.radius;
    sweptBody.lowSphere.heightOffset = lowHeightOffset;
    sweptBody.highSphere.center = {x, y, footZ + highHeightOffset};
    sweptBody.highSphere.radius = body.radius;
    sweptBody.highSphere.heightOffset = highHeightOffset;
    return sweptBody;
}

float movementDistance(float movementX, float movementY, float movementZ)
{
    return std::sqrt(movementX * movementX + movementY * movementY + movementZ * movementZ);
}

bx::Vec3 movementDirection(float movementX, float movementY, float movementZ)
{
    const float distance = movementDistance(movementX, movementY, movementZ);

    if (distance <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {movementX / distance, movementY / distance, movementZ / distance};
}

float dotVec(const bx::Vec3 &lhs, const bx::Vec3 &rhs)
{
    return lhs.x * rhs.x + lhs.y * rhs.y + lhs.z * rhs.z;
}

bx::Vec3 addVec(const bx::Vec3 &lhs, const bx::Vec3 &rhs)
{
    return {lhs.x + rhs.x, lhs.y + rhs.y, lhs.z + rhs.z};
}

bx::Vec3 subtractVec(const bx::Vec3 &lhs, const bx::Vec3 &rhs)
{
    return {lhs.x - rhs.x, lhs.y - rhs.y, lhs.z - rhs.z};
}

bx::Vec3 scaleVec(const bx::Vec3 &value, float scale)
{
    return {value.x * scale, value.y * scale, value.z * scale};
}

float lengthVec(const bx::Vec3 &value)
{
    return std::sqrt(dotVec(value, value));
}

bx::Vec3 normalizeVec(const bx::Vec3 &value)
{
    const float length = lengthVec(value);

    if (length <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return scaleVec(value, 1.0f / length);
}

}

IndoorMovementController::IndoorMovementController(
    const IndoorMapData &indoorMapData,
    const std::optional<MapDeltaData> *pMapDeltaData,
    const std::optional<EventRuntimeState> *pEventRuntimeState
)
    : m_pIndoorMapData(&indoorMapData)
    , m_pMapDeltaData(pMapDeltaData)
    , m_pEventRuntimeState(pEventRuntimeState)
{
}

void IndoorMovementController::setActorColliders(const std::vector<IndoorActorCollision> &actorColliders)
{
    m_actorColliders = actorColliders;
}

void IndoorMovementController::updateActorColliderPosition(size_t actorIndex, int16_t sectorId, float x, float y, float z)
{
    for (IndoorActorCollision &collider : m_actorColliders)
    {
        if (collider.actorIndex != actorIndex)
        {
            continue;
        }

        collider.sectorId = sectorId;
        collider.x = x;
        collider.y = y;
        collider.z = z;
        return;
    }
}

void IndoorMovementController::setDecorationColliders(const std::vector<IndoorCylinderCollision> &decorationColliders)
{
    m_decorationColliders = decorationColliders;
}

void IndoorMovementController::setSpriteObjectColliders(
    const std::vector<IndoorCylinderCollision> &spriteObjectColliders)
{
    m_spriteObjectColliders = spriteObjectColliders;
}

void IndoorMovementController::invalidateRuntimeGeometryCache()
{
    m_runtimeGeometryCache = {};
}

void IndoorMovementController::applyMechanismGeometryUpdate(const std::vector<uint32_t> &changedDoorIds)
{
    if (!m_runtimeGeometryCache.valid
        || m_pMapDeltaData == nullptr
        || !m_pMapDeltaData->has_value()
        || changedDoorIds.empty())
    {
        return;
    }

    const std::vector<MapDeltaDoor> &doors = (*m_pMapDeltaData)->doors;

    for (uint32_t changedDoorId : changedDoorIds)
    {
        const std::vector<MapDeltaDoor>::const_iterator doorIterator =
            std::find_if(
                doors.begin(),
                doors.end(),
                [changedDoorId](const MapDeltaDoor &door)
                {
                    return door.doorId == changedDoorId;
                });

        if (doorIterator == doors.end())
        {
            continue;
        }

        const MapDeltaDoor &door = *doorIterator;
        const float distance = resolveDoorDistance(door, m_pEventRuntimeState);
        applyIndoorMechanismDoorToVertices(door, distance, m_runtimeGeometryCache.vertices);

        for (uint16_t faceId : door.faceIds)
        {
            m_runtimeGeometryCache.geometryCache.invalidateFace(faceId);
        }
    }
}

void IndoorMovementController::refreshRuntimeGeometryCache() const
{
    if (m_pIndoorMapData == nullptr)
    {
        return;
    }

    const MapDeltaData *pMapDeltaData =
        m_pMapDeltaData != nullptr && m_pMapDeltaData->has_value() ? &m_pMapDeltaData->value() : nullptr;
    const uint64_t surfaceRevision = pMapDeltaData != nullptr ? pMapDeltaData->surfaceRevision : 0;

    if (m_runtimeGeometryCache.valid && m_runtimeGeometryCache.surfaceRevision == surfaceRevision)
    {
        return;
    }

    const EventRuntimeState *pEventRuntimeState =
        m_pEventRuntimeState != nullptr && m_pEventRuntimeState->has_value() ? &m_pEventRuntimeState->value() : nullptr;

    const bool wasValid = m_runtimeGeometryCache.valid;
    const uint64_t previousSurfaceRevision = m_runtimeGeometryCache.surfaceRevision;
    const bool supportFaceIdsNeedRefresh =
        !wasValid
        || previousSurfaceRevision != surfaceRevision;
    m_runtimeGeometryCache.vertices = buildIndoorMechanismAdjustedVertices(
        *m_pIndoorMapData,
        pMapDeltaData,
        pEventRuntimeState);
    // OE updates moved mechanism vertices in-place, then floor and wall collision use that current geometry.
    // Do not add open/closed masking here: platforms, stairs, plates, and doors all need their moved faces sampled.
    m_runtimeGeometryCache.nonBlockingMechanismFaceMask.clear();
    m_runtimeGeometryCache.mechanismBlockingFaceMask.clear();
    if (supportFaceIdsNeedRefresh)
    {
        m_runtimeGeometryCache.mechanismSupportFaceIds.clear();
        m_runtimeGeometryCache.sectorMechanismSupportFaceIds.clear();
        m_runtimeGeometryCache.invisibleSupportRampFaceIds.clear();
    }

    if (!wasValid || previousSurfaceRevision != surfaceRevision)
    {
        m_runtimeGeometryCache.collisionFaceMask = buildCollisionFaceMask();
        m_runtimeGeometryCache.geometryCache.reset(m_pIndoorMapData->faces.size());
    }

    m_runtimeGeometryCache.surfaceRevision = surfaceRevision;
    m_runtimeGeometryCache.geometryCache.setAttributeOverrides(pMapDeltaData);

    if (supportFaceIdsNeedRefresh && pMapDeltaData != nullptr)
    {
        std::vector<uint8_t> seenMechanismSupportFaces(m_pIndoorMapData->faces.size(), 0);
        const std::vector<std::vector<uint16_t>> neighboringSectorIds =
            buildNeighboringIndoorSectorIds(*m_pIndoorMapData);
        m_runtimeGeometryCache.sectorMechanismSupportFaceIds.assign(m_pIndoorMapData->sectors.size(), {});

        for (const MapDeltaDoor &door : pMapDeltaData->doors)
        {
            if (!indoorDoorCarriesPartySupport(door))
            {
                continue;
            }

            for (uint16_t faceId : door.faceIds)
            {
                if (faceId >= seenMechanismSupportFaces.size() || seenMechanismSupportFaces[faceId] != 0)
                {
                    continue;
                }

                seenMechanismSupportFaces[faceId] = 1;
                const IndoorFaceGeometryData *pGeometry =
                    m_runtimeGeometryCache.geometryCache.geometryForFace(
                        *m_pIndoorMapData,
                        m_runtimeGeometryCache.vertices,
                        faceId);

                if (pGeometry != nullptr && pGeometry->kind == IndoorFaceKind::Floor && pGeometry->isWalkable)
                {
                    m_runtimeGeometryCache.mechanismSupportFaceIds.push_back(faceId);

                    std::vector<uint16_t> faceSectorIds;
                    appendValidSectorId(*m_pIndoorMapData, faceSectorIds, pGeometry->sectorId);
                    appendValidSectorId(*m_pIndoorMapData, faceSectorIds, pGeometry->backSectorId);

                    for (uint16_t faceSectorId : faceSectorIds)
                    {
                        if (faceSectorId >= neighboringSectorIds.size())
                        {
                            continue;
                        }

                        for (uint16_t nearbySectorId : neighboringSectorIds[faceSectorId])
                        {
                            if (nearbySectorId < m_runtimeGeometryCache.sectorMechanismSupportFaceIds.size())
                            {
                                appendUniqueFaceId(
                                    m_runtimeGeometryCache.sectorMechanismSupportFaceIds[nearbySectorId],
                                    faceId);
                            }
                        }
                    }
                }
            }
        }
    }

    if (supportFaceIdsNeedRefresh)
    {
        for (size_t faceId = 0; faceId < m_pIndoorMapData->faces.size(); ++faceId)
        {
            const IndoorFaceGeometryData *pGeometry =
                m_runtimeGeometryCache.geometryCache.geometryForFace(
                    *m_pIndoorMapData,
                    m_runtimeGeometryCache.vertices,
                    faceId);

            if (pGeometry == nullptr
                || pGeometry->kind != IndoorFaceKind::Floor
                || !pGeometry->isWalkable
                || !indoorFaceIsInvisibleSupportRamp(m_pIndoorMapData->faces[faceId], pGeometry->attributes)
                || faceId > std::numeric_limits<uint16_t>::max())
            {
                continue;
            }

            m_runtimeGeometryCache.invisibleSupportRampFaceIds.push_back(static_cast<uint16_t>(faceId));
        }
    }

    m_runtimeGeometryCache.valid = true;
}

const IndoorMovementController::RuntimeGeometryCache &IndoorMovementController::runtimeGeometryCache() const
{
    refreshRuntimeGeometryCache();
    return m_runtimeGeometryCache;
}

bool IndoorMovementController::supportFaceIsBurning(size_t faceIndex) const
{
    if (m_pIndoorMapData == nullptr || faceIndex >= m_pIndoorMapData->faces.size())
    {
        return false;
    }

    const IndoorFace &face = m_pIndoorMapData->faces[faceIndex];
    const MapDeltaData *pMapDeltaData =
        m_pMapDeltaData != nullptr && m_pMapDeltaData->has_value() ? &m_pMapDeltaData->value() : nullptr;
    const uint32_t attributes =
        pMapDeltaData != nullptr && faceIndex < pMapDeltaData->faceAttributes.size()
            ? pMapDeltaData->faceAttributes[faceIndex]
            : face.attributes;

    if (hasFaceAttribute(attributes, FaceAttribute::Lava))
    {
        return true;
    }

    const std::string textureName = toLowerCopy(face.textureName);
    return textureName == "lava"
        || textureName == "lavtyl"
        || textureName == "lavatyl"
        || textureName.starts_with("lava");
}

IndoorMovementController::SweptCollisionRequest IndoorMovementController::buildSweptCollisionRequest(
    const IndoorMoveState &state,
    const IndoorBodyDimensions &body,
    float desiredVelocityX,
    float desiredVelocityY,
    bool jumpRequested,
    float deltaSeconds,
    std::optional<size_t> ignoredActorIndex,
    bool blockActorSlide
) const
{
    SweptCollisionRequest request = {};
    request.startState = state;
    request.body = body;
    request.velocity = {desiredVelocityX, desiredVelocityY, state.verticalVelocity};
    request.deltaSeconds = deltaSeconds;
    request.jumpRequested = jumpRequested;
    request.ignoredActorIndex = ignoredActorIndex;
    request.blockActorSlide = blockActorSlide;
    return request;
}

IndoorMovementController::SweptCollisionBody IndoorMovementController::buildSweptCollisionBody(
    const IndoorMoveState &state,
    const IndoorBodyDimensions &body
) const
{
    SweptCollisionBody collisionBody = {};
    const float lowHeightOffset = std::max(0.0f, body.radius);
    const float highHeightOffset = std::max(lowHeightOffset, body.height - body.radius);

    collisionBody.radius = body.radius;
    collisionBody.height = body.height;
    collisionBody.lowSphere.center = {state.x, state.y, state.footZ + lowHeightOffset};
    collisionBody.lowSphere.radius = body.radius;
    collisionBody.lowSphere.heightOffset = lowHeightOffset;
    collisionBody.highSphere.center = {state.x, state.y, state.footZ + highHeightOffset};
    collisionBody.highSphere.radius = body.radius;
    collisionBody.highSphere.heightOffset = highHeightOffset;
    return collisionBody;
}

IndoorMovementController::SweptCollisionState IndoorMovementController::buildSweptCollisionState(
    const SweptCollisionRequest &request
) const
{
    SweptCollisionState state = {};
    const float moveX = request.velocity.x * request.deltaSeconds;
    const float moveY = request.velocity.y * request.deltaSeconds;
    const float moveZ = request.velocity.z * request.deltaSeconds;
    const float moveDistance = std::sqrt(moveX * moveX + moveY * moveY + moveZ * moveZ);

    state.position = {
        request.startState.x,
        request.startState.y,
        request.startState.footZ
    };
    state.velocity = request.velocity;
    state.moveDistance = moveDistance;
    state.adjustedMoveDistance = moveDistance;
    state.body = buildSweptCollisionBody(request.startState, request.body);
    state.sectorId = request.startState.sectorId;
    state.eyeSectorId = request.startState.eyeSectorId;
    state.supportFaceIndex = request.startState.supportFaceIndex;
    state.grounded = request.startState.grounded;

    if (moveDistance > 0.0001f)
    {
        state.direction = {
            moveX / moveDistance,
            moveY / moveDistance,
            moveZ / moveDistance
        };
    }

    return state;
}

IndoorFloorSample IndoorMovementController::sampleSupportedFloor(
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    const IndoorBodyDimensions &body,
    std::optional<int16_t> preferredSectorId,
    const std::vector<uint8_t> *pFaceExclusionMask
) const
{
    if (m_pIndoorMapData == nullptr)
    {
        return {};
    }

    IndoorFloorSample bestSample = sampleIndoorFloor(
        *m_pIndoorMapData,
        vertices,
        x,
        y,
        z,
        maxRise,
        maxDrop,
        preferredSectorId,
        pFaceExclusionMask,
        &geometryCache);

    auto evaluateMechanismSupportFace = [&](uint16_t faceId)
    {
        const IndoorFloorSample candidate = sampleIndoorFloorOnFace(
            *m_pIndoorMapData,
            vertices,
            faceId,
            x,
            y,
            z,
            maxRise,
            maxDrop,
            pFaceExclusionMask,
            &geometryCache);

        if (!candidate.hasFloor)
        {
            return;
        }

        if (!bestSample.hasFloor || candidate.height >= bestSample.height - GroundSnapSlack)
        {
            bestSample = candidate;
        }
    };

    std::array<int16_t, 3> mechanismSupportSectorIds = {{-1, -1, -1}};
    size_t mechanismSupportSectorIdCount = 0;
    const auto appendMechanismSupportSectorId = [&](std::optional<int16_t> sectorId)
    {
        if (!sectorId
            || *sectorId < 0
            || static_cast<size_t>(*sectorId) >= m_runtimeGeometryCache.sectorMechanismSupportFaceIds.size())
        {
            return;
        }

        for (size_t index = 0; index < mechanismSupportSectorIdCount; ++index)
        {
            if (mechanismSupportSectorIds[index] == *sectorId)
            {
                return;
            }
        }

        mechanismSupportSectorIds[mechanismSupportSectorIdCount++] = *sectorId;
    };

    appendMechanismSupportSectorId(preferredSectorId);

    if (bestSample.hasFloor)
    {
        appendMechanismSupportSectorId(bestSample.sectorId);
    }

    if (mechanismSupportSectorIdCount == 0)
    {
        const std::optional<int16_t> resolvedSectorId =
            findIndoorSectorForPoint(*m_pIndoorMapData, vertices, {x, y, z}, &geometryCache);
        appendMechanismSupportSectorId(resolvedSectorId);
    }

    if (mechanismSupportSectorIdCount > 0)
    {
        for (size_t sectorIdIndex = 0; sectorIdIndex < mechanismSupportSectorIdCount; ++sectorIdIndex)
        {
            const int16_t sectorId = mechanismSupportSectorIds[sectorIdIndex];

            for (uint16_t faceId : m_runtimeGeometryCache.sectorMechanismSupportFaceIds[sectorId])
            {
                evaluateMechanismSupportFace(faceId);
            }
        }
    }
    else
    {
        for (uint16_t faceId : m_runtimeGeometryCache.mechanismSupportFaceIds)
        {
            evaluateMechanismSupportFace(faceId);
        }
    }

    for (uint16_t faceId : m_runtimeGeometryCache.invisibleSupportRampFaceIds)
    {
        const IndoorFloorSample candidate = sampleInvisibleSupportFaceWithFootprint(
            *m_pIndoorMapData,
            vertices,
            geometryCache,
            faceId,
            x,
            y,
            z,
            maxRise,
            maxDrop,
            body.radius,
            pFaceExclusionMask);

        if (!candidate.hasFloor)
        {
            continue;
        }

        if (!bestSample.hasFloor || candidate.height >= bestSample.height - GroundSnapSlack)
        {
            bestSample = candidate;
        }
    }

    return bestSample;
}

IndoorFloorSample IndoorMovementController::sampleSupportedFloorOnFace(
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    size_t faceIndex,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    const IndoorBodyDimensions &body,
    const std::vector<uint8_t> *pFaceExclusionMask
) const
{
    (void)body;

    if (m_pIndoorMapData == nullptr)
    {
        return {};
    }

    IndoorFloorSample bestSample = sampleIndoorFloorOnFace(
        *m_pIndoorMapData,
        vertices,
        faceIndex,
        x,
        y,
        z,
        maxRise,
        maxDrop,
        pFaceExclusionMask,
        &geometryCache);

    return bestSample;
}

IndoorFloorSample IndoorMovementController::sampleApproximateSupportedFloor(
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    float x,
    float y,
    float z,
    float maxRise,
    float maxDrop,
    const IndoorBodyDimensions &body,
    std::optional<int16_t> preferredSectorId,
    size_t preferredFaceIndex,
    const std::vector<uint8_t> *pFaceExclusionMask
) const
{
    const std::array<std::tuple<float, float, float>, 5> probes = {{
        {-2.0f, 0.0f, 40.0f},
        {2.0f, 0.0f, 40.0f},
        {0.0f, -2.0f, 40.0f},
        {0.0f, 2.0f, 40.0f},
        {0.0f, 0.0f, 140.0f},
    }};

    IndoorFloorSample bestSample = {};

    for (const std::tuple<float, float, float> &probe : probes)
    {
        const float probeX = x + std::get<0>(probe);
        const float probeY = y + std::get<1>(probe);
        const float probeZ = z + std::get<2>(probe);
        IndoorFloorSample candidate = sampleSupportedFloor(
            vertices,
            geometryCache,
            probeX,
            probeY,
            probeZ,
            maxRise,
            maxDrop,
            body,
            preferredSectorId,
            pFaceExclusionMask);

        if (preferredFaceIndex != static_cast<size_t>(-1))
        {
            IndoorFloorSample preferredCandidate = sampleSupportedFloorOnFace(
                vertices,
                geometryCache,
                preferredFaceIndex,
                probeX,
                probeY,
                probeZ,
                maxRise,
                maxDrop,
                body,
                pFaceExclusionMask);

            if (preferredCandidate.hasFloor
                && (!candidate.hasFloor || preferredCandidate.height >= candidate.height - GroundSnapSlack))
            {
                candidate = preferredCandidate;
            }
        }

        if (!candidate.hasFloor)
        {
            continue;
        }

        if (!bestSample.hasFloor || candidate.height > bestSample.height)
        {
            bestSample = candidate;
        }
    }

    return bestSample;
}

IndoorMoveState IndoorMovementController::initializeStateFromEyePosition(
    float x,
    float y,
    float eyeZ,
    const IndoorBodyDimensions &body
) const
{
    IndoorMoveState state = {};
    state.x = x;
    state.y = y;
    state.eyeHeight = body.height;
    state.footZ = eyeZ - body.height;
    state.fallStartZ = state.footZ;

    if (m_pIndoorMapData == nullptr)
    {
        return state;
    }

    const RuntimeGeometryCache &runtimeCache = runtimeGeometryCache();
    IndoorFaceGeometryCache &geometryCache = m_runtimeGeometryCache.geometryCache;
    const std::vector<IndoorVertex> &vertices = runtimeCache.vertices;
    const std::vector<uint8_t> &nonBlockingMechanismFaceMask = runtimeCache.nonBlockingMechanismFaceMask;
    const std::vector<uint8_t> &mechanismBlockingFaceMask = runtimeCache.mechanismBlockingFaceMask;
    const std::vector<uint8_t> &collisionFaceMask = runtimeCache.collisionFaceMask;

    auto buildGroundedState = [&](float candidateX, float candidateY, float candidateEyeZ) -> std::optional<IndoorMoveState>
    {
        IndoorFloorSample floor = sampleSupportedFloor(
            vertices,
            geometryCache,
            candidateX,
            candidateY,
            candidateEyeZ - body.height,
            MaximumRise,
            body.height + 1024.0f,
            body,
            std::nullopt,
            &nonBlockingMechanismFaceMask);

        if (!floor.hasFloor)
        {
            floor = sampleSupportedFloor(
                vertices,
                geometryCache,
                candidateX,
                candidateY,
                candidateEyeZ,
                body.height + MaximumRise,
                body.height + 1024.0f,
                body,
                std::nullopt,
                &nonBlockingMechanismFaceMask);
        }

        if (!floor.hasFloor)
        {
            floor = sampleSupportedFloor(
                vertices,
                geometryCache,
                candidateX,
                candidateY,
                candidateEyeZ - body.height * 0.5f,
                body.height,
                body.height + 1024.0f,
                body,
                std::nullopt,
                &nonBlockingMechanismFaceMask);
        }

        if (!floor.hasFloor)
        {
            floor = sampleApproximateSupportedFloor(
                vertices,
                geometryCache,
                candidateX,
                candidateY,
                candidateEyeZ - body.height,
                MaximumRise,
                body.height + 1024.0f,
                body,
                std::nullopt,
                static_cast<size_t>(-1),
                &nonBlockingMechanismFaceMask);
        }

        if (!floor.hasFloor)
        {
            return std::nullopt;
        }

        IndoorMoveState candidateState = {};
        candidateState.x = candidateX;
        candidateState.y = candidateY;
        candidateState.eyeHeight = body.height;
        candidateState.footZ = floor.height;
        candidateState.sectorId = floor.sectorId;
        candidateState.eyeSectorId = floor.sectorId;
        candidateState.supportFaceIndex = floor.faceIndex;
        candidateState.grounded = true;
        candidateState.fallStartZ = candidateState.footZ;
        return candidateState;
    };

    auto tryInitializeState = [&](float candidateX, float candidateY, float candidateEyeZ) -> std::optional<IndoorMoveState>
    {
        IndoorMoveState candidateState = {};
        candidateState.x = candidateX;
        candidateState.y = candidateY;
        candidateState.eyeHeight = body.height;
        candidateState.footZ = candidateEyeZ - body.height;
        candidateState.fallStartZ = candidateState.footZ;

        IndoorFloorSample floor = sampleSupportedFloor(
            vertices,
            geometryCache,
            candidateX,
            candidateY,
            candidateState.footZ,
            MaximumRise,
            MaximumDrop,
            body,
            std::nullopt,
            &nonBlockingMechanismFaceMask);

        if (!floor.hasFloor)
        {
            floor = sampleApproximateSupportedFloor(
                vertices,
                geometryCache,
                candidateX,
                candidateY,
                candidateEyeZ - body.height,
                MaximumRise,
                MaximumDrop,
                body,
                std::nullopt,
                static_cast<size_t>(-1),
                &nonBlockingMechanismFaceMask);
        }

        if (floor.hasFloor)
        {
            candidateState.footZ = floor.height;
            candidateState.sectorId = floor.sectorId;
            candidateState.eyeSectorId = floor.sectorId;
            candidateState.supportFaceIndex = floor.faceIndex;
            candidateState.grounded = true;
            candidateState.fallStartZ = candidateState.footZ;
        }
        else
        {
            const std::optional<int16_t> sectorId =
                findIndoorSectorForPoint(
                    *m_pIndoorMapData,
                    vertices,
                    {candidateX, candidateY, candidateEyeZ},
                    &geometryCache,
                    false);
            candidateState.sectorId = sectorId.value_or(-1);
            candidateState.eyeSectorId = candidateState.sectorId;
        }

        const bool collides = collidesAtPosition(
                vertices,
                geometryCache,
                candidateState.x,
                candidateState.y,
                candidateState.footZ,
                body,
                &collisionFaceMask,
                &mechanismBlockingFaceMask,
                candidateState.sectorId >= 0 ? std::optional<int16_t>(candidateState.sectorId) : std::nullopt,
                candidateState.eyeSectorId >= 0 ? std::optional<int16_t>(candidateState.eyeSectorId) : std::nullopt,
                candidateState.supportFaceIndex,
                0.0f,
                0.0f,
                nullptr);

        if (collides)
        {
            return std::nullopt;
        }

        return candidateState;
    };

    if (const std::optional<IndoorMoveState> exactState = tryInitializeState(x, y, eyeZ))
    {
        return *exactState;
    }

    if (const std::optional<IndoorMoveState> groundedState = buildGroundedState(x, y, eyeZ))
    {
        return *groundedState;
    }

    return state;
}

IndoorMoveState IndoorMovementController::resolveMove(
    const IndoorMoveState &state,
    const IndoorBodyDimensions &body,
    float desiredVelocityX,
    float desiredVelocityY,
    bool jumpRequested,
    float deltaSeconds,
    std::vector<size_t> *pContactedActorIndices,
    std::optional<size_t> ignoredActorIndex,
    bool blockActorSlide,
    IndoorMoveDebugInfo *pDebugInfo,
    bool flyingActive,
    bool ignoreActorCollisions,
    float jumpVelocity,
    float jumpLift,
    bool lockVerticalPosition,
    bool preventGroundActorLedgeDrop
) const
{
    if (m_pIndoorMapData == nullptr || deltaSeconds <= 0.0f)
    {
        return state;
    }

    const int substepCount = indoorMovementSubstepCount(
        state,
        desiredVelocityX,
        desiredVelocityY,
        jumpRequested,
        deltaSeconds,
        jumpVelocity);

    if (substepCount <= 1)
    {
        return resolveMoveSingleStep(
            state,
            body,
            desiredVelocityX,
            desiredVelocityY,
            jumpRequested,
            deltaSeconds,
            pContactedActorIndices,
            ignoredActorIndex,
            blockActorSlide,
            pDebugInfo,
            flyingActive,
            ignoreActorCollisions,
            jumpVelocity,
            jumpLift,
            lockVerticalPosition,
            preventGroundActorLedgeDrop);
    }

    const RuntimeGeometryCache &runtimeCache = runtimeGeometryCache();
    IndoorFaceGeometryCache &geometryCache = m_runtimeGeometryCache.geometryCache;
    const float preflightEyeZ =
        state.eyeZ() + state.verticalVelocity * deltaSeconds + (jumpRequested ? jumpVelocity * deltaSeconds : 0.0f);
    const std::optional<int16_t> preflightEyeSectorId = findIndoorSectorForPoint(
        *m_pIndoorMapData,
        runtimeCache.vertices,
        {state.x + desiredVelocityX * deltaSeconds, state.y + desiredVelocityY * deltaSeconds, preflightEyeZ},
        &geometryCache,
        false);

    if (!preflightEyeSectorId)
    {
        return resolveMoveSingleStep(
            state,
            body,
            desiredVelocityX,
            desiredVelocityY,
            jumpRequested,
            deltaSeconds,
            pContactedActorIndices,
            ignoredActorIndex,
            blockActorSlide,
            pDebugInfo,
            flyingActive,
            ignoreActorCollisions,
            jumpVelocity,
            jumpLift,
            lockVerticalPosition,
            preventGroundActorLedgeDrop);
    }

    IndoorMoveState currentState = state;
    IndoorMoveDebugInfo stepDebug = {};
    const float substepDeltaSeconds = deltaSeconds / static_cast<float>(substepCount);
    float maxLandingFallDistance = 0.0f;

    for (int substepIndex = 0; substepIndex < substepCount; ++substepIndex)
    {
        const bool substepJumpRequested = jumpRequested && substepIndex == 0;
        currentState = resolveMoveSingleStep(
            currentState,
            body,
            desiredVelocityX,
            desiredVelocityY,
            substepJumpRequested,
            substepDeltaSeconds,
            pContactedActorIndices,
            ignoredActorIndex,
            blockActorSlide,
            &stepDebug,
            flyingActive,
            ignoreActorCollisions,
            jumpVelocity,
            jumpLift,
            lockVerticalPosition,
            preventGroundActorLedgeDrop);

        if (currentState.landedThisFrame)
        {
            maxLandingFallDistance = std::max(maxLandingFallDistance, currentState.fallDistance);
        }

        if (blockActorSlide
            && (stepDebug.primaryBlockKind == IndoorMoveBlockKind::Actor
                || stepDebug.primaryBlockKind == IndoorMoveBlockKind::Party))
        {
            break;
        }
    }

    if (pDebugInfo != nullptr)
    {
        *pDebugInfo = stepDebug;
    }

    if (maxLandingFallDistance > 0.0f)
    {
        currentState.landedThisFrame = true;
        currentState.fallDistance = maxLandingFallDistance;
    }

    return currentState;
}

IndoorMoveState IndoorMovementController::resolveFlyingActorMove(
    const IndoorMoveState &state,
    const IndoorBodyDimensions &body,
    float desiredVelocityX,
    float desiredVelocityY,
    float deltaSeconds,
    std::vector<size_t> *pContactedActorIndices,
    std::optional<size_t> ignoredActorIndex,
    bool blockActorSlide,
    IndoorMoveDebugInfo *pHorizontalDebugInfo,
    IndoorMoveDebugInfo *pVerticalDebugInfo,
    bool ignoreActorCollisions
) const
{
    if (pVerticalDebugInfo != nullptr)
    {
        *pVerticalDebugInfo = {};
    }

    IndoorMoveState horizontalState = state;
    const float savedVerticalVelocity = state.verticalVelocity;
    horizontalState.verticalVelocity = 0.0f;

    IndoorMoveState resolvedState =
        resolveMove(
            horizontalState,
            body,
            desiredVelocityX,
            desiredVelocityY,
            false,
            deltaSeconds,
            pContactedActorIndices,
            ignoredActorIndex,
            blockActorSlide,
            pHorizontalDebugInfo,
            true,
            ignoreActorCollisions,
            420.0f,
            1.0f,
            true);

    if (resolvedState.footZ > state.footZ)
    {
        return resolvedState;
    }

    resolvedState.verticalVelocity = savedVerticalVelocity;
    return resolveMove(
        resolvedState,
        body,
        0.0f,
        0.0f,
        false,
        deltaSeconds,
        pContactedActorIndices,
        ignoredActorIndex,
        blockActorSlide,
        pVerticalDebugInfo,
        true,
        ignoreActorCollisions);
}

IndoorMoveState IndoorMovementController::resolveMoveSingleStep(
    const IndoorMoveState &state,
    const IndoorBodyDimensions &body,
    float desiredVelocityX,
    float desiredVelocityY,
    bool jumpRequested,
    float deltaSeconds,
    std::vector<size_t> *pContactedActorIndices,
    std::optional<size_t> ignoredActorIndex,
    bool blockActorSlide,
    IndoorMoveDebugInfo *pDebugInfo,
    bool flyingActive,
    bool ignoreActorCollisions,
    float jumpVelocity,
    float jumpLift,
    bool lockVerticalPosition,
    bool preventGroundActorLedgeDrop
) const
{
    if (m_pIndoorMapData == nullptr || deltaSeconds <= 0.0f)
    {
        return state;
    }

    const RuntimeGeometryCache &runtimeCache = runtimeGeometryCache();
    IndoorFaceGeometryCache &geometryCache = m_runtimeGeometryCache.geometryCache;
    const std::vector<IndoorVertex> &vertices = runtimeCache.vertices;
    const std::vector<uint8_t> &nonBlockingMechanismFaceMask = runtimeCache.nonBlockingMechanismFaceMask;
    const std::vector<uint8_t> &mechanismBlockingFaceMask = runtimeCache.mechanismBlockingFaceMask;
    const std::vector<uint8_t> &collisionFaceMask = runtimeCache.collisionFaceMask;
    const MapDeltaData *pMapDeltaData =
        m_pMapDeltaData != nullptr && m_pMapDeltaData->has_value() ? &m_pMapDeltaData->value() : nullptr;

    const SweptCollisionRequest sweptRequest = buildSweptCollisionRequest(
        state,
        body,
        desiredVelocityX,
        desiredVelocityY,
        jumpRequested,
        deltaSeconds,
        ignoredActorIndex,
        blockActorSlide);
    const SweptCollisionState sweptState = buildSweptCollisionState(sweptRequest);
    IndoorMoveState resolved = state;
    const float stepX = sweptState.velocity.x * sweptRequest.deltaSeconds;
    const float stepY = sweptState.velocity.y * sweptRequest.deltaSeconds;
    const bool flying = flyingActive && !jumpRequested;
    const bool wasAirborne = !state.grounded;
    const float stepFallStartZ = wasAirborne ? std::max(state.fallStartZ, state.footZ) : state.footZ;
    const std::optional<int16_t> preferredSectorId =
        state.sectorId >= 0 ? std::optional<int16_t>(state.sectorId) : std::nullopt;
    const IndoorFloorSample currentFloor = sampleSupportedFloor(
        vertices,
        geometryCache,
        state.x,
        state.y,
        state.footZ,
        MaximumRise,
        body.height + 1024.0f,
        body,
        preferredSectorId,
        &nonBlockingMechanismFaceMask);
    const IndoorFloorSample preferredCurrentFloor =
        state.grounded && state.supportFaceIndex != static_cast<size_t>(-1)
        ? sampleSupportedFloorOnFace(
            vertices,
            geometryCache,
            state.supportFaceIndex,
            state.x,
            state.y,
            state.footZ,
            MaximumRise,
            body.height + 1024.0f,
            body,
            &nonBlockingMechanismFaceMask)
        : IndoorFloorSample{};
    const IndoorFloorSample effectiveCurrentFloor =
        preferredCurrentFloor.hasFloor
        && (!currentFloor.hasFloor || preferredCurrentFloor.height >= currentFloor.height - GroundSnapSlack)
        ? preferredCurrentFloor
        : currentFloor;
    const bool supportedByCurrentFloor =
        !flying && effectiveCurrentFloor.hasFloor && state.footZ <= effectiveCurrentFloor.height + GroundSnapSlack;
    float candidateFootZ = state.footZ;
    float candidateVerticalVelocity = state.verticalVelocity;
    bool candidateGrounded = !flying && state.grounded && supportedByCurrentFloor;
    bool fullMoveBlockedByActor = false;
    IndoorWallCollision fullMoveWallCollision = {};

    const auto finalizeFallState = [&](IndoorMoveState result) -> IndoorMoveState
    {
        result.landedThisFrame = false;
        result.fallDistance = 0.0f;

        if (flying || lockVerticalPosition)
        {
            result.fallStartZ = result.footZ;
            return result;
        }

        if (result.grounded)
        {
            if (wasAirborne && result.footZ < stepFallStartZ)
            {
                result.landedThisFrame = true;
                result.fallDistance = stepFallStartZ - result.footZ;
            }

            result.fallStartZ = result.footZ;
            return result;
        }

        result.fallStartZ = wasAirborne ? std::max(stepFallStartZ, result.footZ) : result.footZ;
        return result;
    };

    const auto appendContactedActorIndex = [&](size_t actorIndex)
    {
        if (pContactedActorIndices == nullptr)
        {
            return;
        }

        if (std::find(pContactedActorIndices->begin(), pContactedActorIndices->end(), actorIndex)
            == pContactedActorIndices->end())
        {
            pContactedActorIndices->push_back(actorIndex);
        }
    };

    if (pDebugInfo != nullptr)
    {
        *pDebugInfo = {};
        pDebugInfo->wantedHorizontalMove = stepX * stepX + stepY * stepY > 0.0001f;
        pDebugInfo->startSectorId = state.sectorId;
        pDebugInfo->startEyeSectorId = state.eyeSectorId;
    }

    if (candidateGrounded)
    {
        candidateFootZ = effectiveCurrentFloor.height;
        candidateVerticalVelocity = 0.0f;

        if (sweptRequest.jumpRequested)
        {
            candidateGrounded = false;
            candidateVerticalVelocity = jumpVelocity;
            candidateFootZ += jumpLift;
        }
    }

    if (!candidateGrounded && !flying)
    {
        candidateVerticalVelocity -= GravityPerSecond * deltaSeconds;
        candidateFootZ += candidateVerticalVelocity * deltaSeconds;
    }
    else if (flying)
    {
        candidateFootZ += candidateVerticalVelocity * deltaSeconds;
    }

    auto tryResolvePosition =
        [&](
            float currentX,
            float currentY,
            float candidateX,
            float candidateY,
            float positionFootZ,
            float positionVerticalVelocity,
            IndoorMoveState &candidateState,
            bool testFaceCollision,
            bool *pHitActor,
            IndoorWallCollision *pWallCollision) -> bool
    {
        IndoorFloorSample floor = sampleSupportedFloor(
            vertices,
            geometryCache,
            candidateX,
            candidateY,
            positionFootZ,
            MaximumRise,
            body.height + 1024.0f,
            body,
            preferredSectorId,
            &nonBlockingMechanismFaceMask);
        const IndoorFloorSample preferredFloor =
            state.grounded && state.supportFaceIndex != static_cast<size_t>(-1)
            ? sampleSupportedFloorOnFace(
                vertices,
                geometryCache,
                state.supportFaceIndex,
                candidateX,
                candidateY,
                positionFootZ,
                MaximumRise,
                body.height + 1024.0f,
                body,
                &nonBlockingMechanismFaceMask)
            : IndoorFloorSample{};
        IndoorFloorSample approximateFloor = {};

        if (preferredFloor.hasFloor
            && (!floor.hasFloor || preferredFloor.height >= floor.height - GroundSnapSlack))
        {
            floor = preferredFloor;
        }

        if (!floor.hasFloor && state.grounded && !sweptRequest.jumpRequested)
        {
            approximateFloor = sampleApproximateSupportedFloor(
                vertices,
                geometryCache,
                candidateX,
                candidateY,
                positionFootZ,
                MaximumRise,
                body.height + 1024.0f,
                body,
                preferredSectorId,
                state.supportFaceIndex,
                &nonBlockingMechanismFaceMask);
            floor = approximateFloor;
        }

        const float movementX = candidateX - currentX;
        const float movementY = candidateY - currentY;
        const float movementLength = std::sqrt(movementX * movementX + movementY * movementY);
        IndoorFloorSample leadingFootprintFloor = {};
        const bool guardGroundActorAgainstLedgeDrop =
            preventGroundActorLedgeDrop
            && state.grounded
            && !flying
            && !sweptRequest.jumpRequested
            && movementLength > 0.0001f;
        const auto floorDropsBelowActorLedgeGuard =
            [&state](const IndoorFloorSample &sample) -> bool
        {
            return !sample.hasFloor || sample.height < state.footZ - ActorLedgeDropGuardHeight;
        };

        if (guardGroundActorAgainstLedgeDrop && floorDropsBelowActorLedgeGuard(floor))
        {
            return false;
        }

        if (state.grounded
            && !flying
            && !sweptRequest.jumpRequested
            && movementLength > 0.0001f)
        {
            const float probeX = candidateX + movementX / movementLength * body.radius;
            const float probeY = candidateY + movementY / movementLength * body.radius;
            leadingFootprintFloor = sampleSupportedFloor(
                vertices,
                geometryCache,
                probeX,
                probeY,
                positionFootZ,
                MaximumRise,
                body.height + 1024.0f,
                body,
                preferredSectorId,
                &nonBlockingMechanismFaceMask);

            if (guardGroundActorAgainstLedgeDrop && floorDropsBelowActorLedgeGuard(leadingFootprintFloor))
            {
                return false;
            }

            if (floor.hasFloor
                && floor.faceIndex == state.supportFaceIndex
                && leadingFootprintFloor.hasFloor
                && leadingFootprintFloor.faceIndex != floor.faceIndex
                && !indoorFloorTooSteepForUphillStep(
                    *m_pIndoorMapData,
                    pMapDeltaData,
                    leadingFootprintFloor,
                    state.footZ)
                && leadingFootprintFloor.height <= state.footZ + MaximumStepUpFromCurrentFootZ)
            {
                floor = leadingFootprintFloor;
            }
        }

        if (floor.hasFloor
            && !flying
            && !sweptRequest.jumpRequested
            && indoorFloorTooSteepForUphillStep(*m_pIndoorMapData, pMapDeltaData, floor, state.footZ))
        {
            if (leadingFootprintFloor.hasFloor)
            {
                if (leadingFootprintFloor.faceIndex != floor.faceIndex
                    && !indoorFloorTooSteepForUphillStep(
                        *m_pIndoorMapData,
                        pMapDeltaData,
                        leadingFootprintFloor,
                        state.footZ)
                    && leadingFootprintFloor.height <= state.footZ + MaximumStepUpFromCurrentFootZ)
                {
                    floor = leadingFootprintFloor;
                }
            }
        }

        if (floor.hasFloor
            && !flying
            && !sweptRequest.jumpRequested
            && indoorFloorTooSteepForUphillStep(*m_pIndoorMapData, pMapDeltaData, floor, state.footZ))
        {
            return false;
        }

        if (floor.hasFloor
            && !flying
            && !sweptRequest.jumpRequested
            && floor.height > state.footZ + MaximumStepUpFromCurrentFootZ)
        {
            return false;
        }

        float resolvedFootZ = positionFootZ;
        float resolvedVerticalVelocity = positionVerticalVelocity;
        bool resolvedGrounded = false;

        if (floor.hasFloor)
        {
            const bool closeEnoughToSnapToFloor =
                positionFootZ <= floor.height + GroundSnapSlack
                && positionFootZ >= floor.height - MaximumDrop;
            const bool shouldSnapToFloor =
                !flying
                && positionVerticalVelocity <= 0.0f
                && closeEnoughToSnapToFloor
                && (state.grounded || positionFootZ <= floor.height + GroundSnapSlack);

            if (shouldSnapToFloor)
            {
                resolvedFootZ = floor.height;
                resolvedVerticalVelocity = 0.0f;
                resolvedGrounded = true;
            }
        }

        IndoorCeilingSample ceiling = sampleIndoorCeiling(
            *m_pIndoorMapData,
            vertices,
            candidateX,
            candidateY,
            resolvedFootZ,
            floor.hasFloor && floor.sectorId >= 0 ? std::optional<int16_t>(floor.sectorId) : preferredSectorId,
            &nonBlockingMechanismFaceMask,
            &geometryCache);

        if (ceiling.hasCeiling && !flying && resolvedFootZ + body.height > ceiling.height - 1.0f)
        {
            resolvedFootZ = ceiling.height - body.height - 1.0f;
            resolvedVerticalVelocity = std::min(resolvedVerticalVelocity, 0.0f);
        }

        if (floor.hasFloor && !flying && resolvedFootZ < floor.height)
        {
            if (ceiling.hasCeiling)
            {
                return false;
            }

            resolvedFootZ = floor.height;
            resolvedVerticalVelocity = 0.0f;
            resolvedGrounded = !flying;
        }

        const float resolvedEyeZ = resolvedFootZ + body.height;
        const std::optional<int16_t> eyeSectorId = findIndoorSectorForPoint(
            *m_pIndoorMapData,
            vertices,
            {candidateX, candidateY, resolvedEyeZ},
            &geometryCache,
            false);
        if (!eyeSectorId)
        {
            return false;
        }

        const std::optional<int16_t> floorSectorId =
            floor.hasFloor && floor.sectorId >= 0 ? std::optional<int16_t>(floor.sectorId) : std::nullopt;
        const std::optional<int16_t> fallbackSectorId =
            state.sectorId >= 0 ? std::optional<int16_t>(state.sectorId) : std::nullopt;
        const std::optional<int16_t> primarySectorId =
            floorSectorId ? floorSectorId : (eyeSectorId ? eyeSectorId : fallbackSectorId);

        if (testFaceCollision
            && collidesAtPosition(
                vertices,
                geometryCache,
                candidateX,
                candidateY,
                resolvedFootZ,
                body,
                &collisionFaceMask,
                &mechanismBlockingFaceMask,
                primarySectorId,
                eyeSectorId,
                state.grounded ? state.supportFaceIndex : static_cast<size_t>(-1),
                candidateX - currentX,
                candidateY - currentY,
                pWallCollision))
        {
            return false;
        }

        if (collidesWithActors(
                currentX,
                currentY,
                candidateX,
                candidateY,
                resolvedFootZ,
                body,
                pContactedActorIndices,
                sweptRequest.ignoredActorIndex,
                ignoreActorCollisions,
                pHitActor))
        {
            return false;
        }

        candidateState.x = candidateX;
        candidateState.y = candidateY;
        candidateState.footZ = resolvedFootZ;
        candidateState.verticalVelocity = resolvedVerticalVelocity;
        candidateState.sectorId = floor.hasFloor ? floor.sectorId : eyeSectorId.value_or(state.sectorId);
        candidateState.eyeSectorId = *eyeSectorId;
        candidateState.supportFaceIndex =
            floor.hasFloor && resolvedGrounded ? floor.faceIndex : static_cast<size_t>(-1);
        candidateState.grounded = resolvedGrounded;

        return true;
    };

    auto writePrimaryBlockDebug = [&]()
    {
        if (pDebugInfo == nullptr)
        {
            return;
        }

        if (fullMoveBlockedByActor)
        {
            pDebugInfo->primaryBlockKind = IndoorMoveBlockKind::Actor;
        }
        else if (fullMoveWallCollision.hit)
        {
            pDebugInfo->primaryBlockKind = IndoorMoveBlockKind::Wall;
            pDebugInfo->hitFaceIndex = fullMoveWallCollision.faceIndex;
            pDebugInfo->hitNormal = fullMoveWallCollision.normal;
        }
        else
        {
            pDebugInfo->primaryBlockKind = IndoorMoveBlockKind::InvalidPosition;
        }
    };

    const auto findCurrentWallOverlap = [&](const IndoorMoveState &moveState) -> IndoorWallCollision
    {
        IndoorWallCollision bestOverlap = {};
        float bestPenetration = -1.0f;
        const std::vector<const IndoorFaceGeometryData *> candidateFaces = collectSweptCollisionFaceCandidates(
            vertices,
            geometryCache,
            moveState.x,
            moveState.y,
            moveState.footZ,
            body,
            0.0f,
            0.0f,
            0.0f,
            &collisionFaceMask,
            &mechanismBlockingFaceMask,
            moveState.sectorId >= 0 ? std::optional<int16_t>(moveState.sectorId) : std::nullopt,
            moveState.eyeSectorId >= 0 ? std::optional<int16_t>(moveState.eyeSectorId) : std::nullopt);

        for (const IndoorFaceGeometryData *pGeometry : candidateFaces)
        {
            if (pGeometry == nullptr
                || !indoorFaceBlocksAsWallOverlap(*pGeometry, moveState.footZ)
                || (moveState.grounded
                    && pGeometry->faceIndex == moveState.supportFaceIndex
                    && indoorFaceIsSteepFloorCollisionSurface(*pGeometry))
                || !isIndoorCylinderBlockedByFace(*pGeometry, moveState.x, moveState.y, moveState.footZ, body.radius, body.height))
            {
                continue;
            }

            const bx::Vec3 bodyCenter = {
                moveState.x,
                moveState.y,
                moveState.footZ + std::min(body.height * 0.5f, std::max(body.radius, 1.0f))
            };
            const float planeDistance =
                std::fabs(dotVec(subtractVec(bodyCenter, pGeometry->vertices.front()), pGeometry->normal));
            const float penetration = body.radius - planeDistance;

            if (!bestOverlap.hit || penetration > bestPenetration)
            {
                bestOverlap.hit = true;
                bestOverlap.normal = pGeometry->normal;
                bestOverlap.faceIndex = pGeometry->faceIndex;
                bestPenetration = penetration;
            }
        }

        return bestOverlap;
    };

    if (!state.grounded
        && state.supportFaceIndex != static_cast<size_t>(-1)
        && std::fabs(state.verticalVelocity) >= WallOverlapRecoveryMinVelocity)
    {
        const IndoorWallCollision overlap = findCurrentWallOverlap(state);
        const bx::Vec3 horizontalNormal = normalizeVec({overlap.normal.x, overlap.normal.y, 0.0f});

        if (overlap.hit && lengthVec(horizontalNormal) > 0.0001f)
        {
            constexpr std::array<float, 5> RecoveryDistances = {{4.0f, 8.0f, 16.0f, 32.0f, 48.0f}};

            for (float directionSign : {1.0f, -1.0f})
            {
                for (float distance : RecoveryDistances)
                {
                    IndoorMoveState recoveredState = {};

                    if (tryResolvePosition(
                            state.x,
                            state.y,
                            state.x + horizontalNormal.x * directionSign * distance,
                            state.y + horizontalNormal.y * directionSign * distance,
                            state.footZ,
                            0.0f,
                            recoveredState,
                            true,
                            nullptr,
                            nullptr))
                    {
                        if (pDebugInfo != nullptr)
                        {
                            pDebugInfo->collisionResponseTried = true;
                            pDebugInfo->collisionResponseSucceeded = true;
                            pDebugInfo->primaryBlockKind = IndoorMoveBlockKind::Wall;
                            pDebugInfo->hitFaceIndex = overlap.faceIndex;
                            pDebugInfo->hitNormal = overlap.normal;
                            pDebugInfo->responseStep = {
                                recoveredState.x - state.x,
                                recoveredState.y - state.y,
                                recoveredState.footZ - state.footZ
                            };
                        }

                        return finalizeFallState(recoveredState);
                    }
                }
            }
        }
    }

    auto selectNearestActorBodyHit =
        [&](const IndoorMoveState &moveState, const bx::Vec3 &direction, float distance)
        -> std::optional<SweptCollisionHit>
    {
        if (!hasCylinderCollisionHorizontalComponent(direction.x, direction.y))
        {
            return std::nullopt;
        }

        std::optional<SweptCollisionHit> bestHit;
        const IndoorSweptBody contactSweptBody =
            buildPrimitiveSweptBody(moveState.x, moveState.y, moveState.footZ, body);

        for (size_t colliderIndex = 0; colliderIndex < m_actorColliders.size(); ++colliderIndex)
        {
            const IndoorActorCollision &collider = m_actorColliders[colliderIndex];

            if (sweptRequest.ignoredActorIndex.has_value()
                && collider.actorIndex == *sweptRequest.ignoredActorIndex)
            {
                continue;
            }

            if (ignoreActorCollisions && collider.reportActorContact)
            {
                continue;
            }

            if (collider.sectorId >= 0
                && collider.sectorId != moveState.sectorId
                && collider.sectorId != moveState.eyeSectorId)
            {
                continue;
            }

            IndoorSweptCylinder cylinder = {};
            cylinder.baseCenter = {collider.x, collider.y, collider.z};
            cylinder.radius = collider.radius;
            cylinder.height = collider.height;

            const std::optional<IndoorSweptCylinderHit> cylinderHit =
                sweepIndoorBodyAgainstCylinder(contactSweptBody, direction, distance, cylinder);

            if (!cylinderHit)
            {
                continue;
            }

            const bool actorVsActor =
                sweptRequest.ignoredActorIndex.has_value() && collider.reportActorContact;
            if (shouldIgnoreExistingActorOverlap(
                    moveState.x,
                    moveState.y,
                    body,
                    collider,
                    actorVsActor))
            {
                continue;
            }

            if (collider.reportActorContact)
            {
                appendContactedActorIndex(collider.actorIndex);
            }

            if (bestHit && cylinderHit->adjustedMoveDistance >= bestHit->adjustedMoveDistance)
            {
                continue;
            }

            SweptCollisionHit hit = {};
            hit.type = collider.reportActorContact ? SweptCollisionHitType::Actor : SweptCollisionHitType::Party;
            hit.colliderIndex = colliderIndex;
            hit.actorIndex = collider.actorIndex;
            hit.point = cylinderHit->point;
            hit.normal = cylinderHit->normal;
            hit.heightOffset = cylinderHit->heightOffset;
            hit.moveDistance = cylinderHit->moveDistance;
            hit.adjustedMoveDistance = cylinderHit->adjustedMoveDistance;
            bestHit = hit;
        }

        return bestHit;
    };
    auto selectNearestCylinderBodyHit =
        [&](
            const IndoorMoveState &moveState,
            const bx::Vec3 &direction,
            float distance,
            const std::vector<IndoorCylinderCollision> &colliders,
            SweptCollisionHitType hitType)
        -> std::optional<SweptCollisionHit>
    {
        if (!hasCylinderCollisionHorizontalComponent(direction.x, direction.y))
        {
            return std::nullopt;
        }

        std::optional<SweptCollisionHit> bestHit;
        const IndoorSweptBody sweptBody = buildPrimitiveSweptBody(moveState.x, moveState.y, moveState.footZ, body);

        for (size_t colliderIndex = 0; colliderIndex < colliders.size(); ++colliderIndex)
        {
            const IndoorCylinderCollision &collider = colliders[colliderIndex];

            if (collider.sectorId >= 0
                && collider.sectorId != moveState.sectorId
                && collider.sectorId != moveState.eyeSectorId)
            {
                continue;
            }

            IndoorSweptCylinder cylinder = {};
            cylinder.baseCenter = {collider.x, collider.y, collider.z};
            cylinder.radius = collider.radius;
            cylinder.height = collider.height;

            const std::optional<IndoorSweptCylinderHit> cylinderHit =
                sweepIndoorBodyAgainstCylinder(sweptBody, direction, distance, cylinder);

            if (!cylinderHit)
            {
                continue;
            }

            if (bestHit && cylinderHit->adjustedMoveDistance >= bestHit->adjustedMoveDistance)
            {
                continue;
            }

            SweptCollisionHit hit = {};
            hit.type = hitType;
            hit.colliderIndex = colliderIndex;
            hit.point = cylinderHit->point;
            hit.normal = cylinderHit->normal;
            hit.heightOffset = cylinderHit->heightOffset;
            hit.moveDistance = cylinderHit->moveDistance;
            hit.adjustedMoveDistance = cylinderHit->adjustedMoveDistance;
            bestHit = hit;
        }

        return bestHit;
    };

    if (lockVerticalPosition)
    {
        candidateFootZ = state.footZ;
        candidateVerticalVelocity = 0.0f;
    }

    const auto lockVerticalStep =
        [lockVerticalPosition](
            const bx::Vec3 &step,
            const IndoorFaceGeometryData *pGeometry = nullptr) -> bx::Vec3
    {
        if (!lockVerticalPosition
            || step.z <= 0.0f
            || (pGeometry != nullptr && !indoorFaceIsSteepFloorCollisionSurface(*pGeometry)))
        {
            return step;
        }

        return {step.x, step.y, 0.0f};
    };

    const float stepZ = candidateFootZ - state.footZ;
    IndoorMoveState iterativeState = state;
    bx::Vec3 remainingStep = lockVerticalStep({stepX, stepY, stepZ});
    float iterativeVerticalVelocity = candidateVerticalVelocity;
    bool sweptFaceHit = false;
    bool sweptFailed = false;
    constexpr int MaxSweptIterations = 8;

    const auto projectStepAfterFaceHit =
        [&](
            const bx::Vec3 &step,
            const SweptCollisionHit &hit,
            const IndoorMoveState &advancedState,
            const IndoorFaceGeometryData *pHitGeometry) -> bx::Vec3
    {
        if (hit.type != SweptCollisionHitType::Face)
        {
            const bx::Vec3 responseStep = projectIndoorVelocityAlongPlane(
                step,
                hit.normal,
                hit.type == SweptCollisionHitType::Floor ? 1.0f : SlideFactor);
            return lockVerticalStep(responseStep);
        }

        const bx::Vec3 slidePlaneOrigin = {
            hit.point.x,
            hit.point.y,
            hit.point.z - hit.heightOffset
        };
        const bx::Vec3 adjustedLowSphereCenter = {
            advancedState.x,
            advancedState.y,
            advancedState.footZ + body.radius
        };
        const bx::Vec3 slidePlaneNormal =
            normalizeVec(subtractVec(adjustedLowSphereCenter, slidePlaneOrigin));

        if (lengthVec(slidePlaneNormal) <= 0.0001f)
        {
            const bx::Vec3 responseStep = projectIndoorVelocityAlongPlane(step, hit.normal, SlideFactor);
            return lockVerticalStep(
                applySteepFloorCollisionResponse(responseStep, pHitGeometry, deltaSeconds),
                pHitGeometry);
        }

        const bx::Vec3 intendedLowSphereCenter = {
            advancedState.x + step.x,
            advancedState.y + step.y,
            advancedState.footZ + body.radius + step.z
        };
        const float destinationPlaneDistance =
            dotVec(subtractVec(intendedLowSphereCenter, slidePlaneOrigin), slidePlaneNormal);
        const bx::Vec3 projectedDestination =
            subtractVec(intendedLowSphereCenter, scaleVec(slidePlaneNormal, destinationPlaneDistance));
        bx::Vec3 slideDirection =
            normalizeVec(subtractVec(projectedDestination, slidePlaneOrigin));

        if (lengthVec(slideDirection) <= 0.0001f)
        {
            const bx::Vec3 responseStep = projectIndoorVelocityAlongPlane(step, hit.normal, SlideFactor);
            return lockVerticalStep(
                applySteepFloorCollisionResponse(responseStep, pHitGeometry, deltaSeconds),
                pHitGeometry);
        }

        if (pHitGeometry != nullptr
            && indoorFaceIsSteepFloorCollisionSurface(*pHitGeometry)
            && slideDirection.z > 0.0f)
        {
            const bx::Vec3 horizontalSlideDirection = normalizeVec({slideDirection.x, slideDirection.y, 0.0f});

            if (lengthVec(horizontalSlideDirection) > 0.0001f)
            {
                slideDirection = horizontalSlideDirection;
            }
        }

        const float projectedStepDistance = dotVec(step, slideDirection);

        if (std::fabs(projectedStepDistance) <= 0.0001f)
        {
            return {0.0f, 0.0f, 0.0f};
        }

        const bx::Vec3 responseStep = scaleVec(slideDirection, projectedStepDistance * SlideFactor);
        return lockVerticalStep(
            applySteepFloorCollisionResponse(responseStep, pHitGeometry, deltaSeconds),
            pHitGeometry);
    };

    if (movementDistance(remainingStep.x, remainingStep.y, remainingStep.z) <= 0.0001f)
    {
        IndoorMoveState stationaryState = {};

        if (tryResolvePosition(
                state.x,
                state.y,
                state.x,
                state.y,
                candidateFootZ,
                candidateVerticalVelocity,
                stationaryState,
                false,
                nullptr,
                nullptr))
        {
            if (pDebugInfo != nullptr)
            {
                pDebugInfo->fullMoveSucceeded = true;
            }

            return finalizeFallState(stationaryState);
        }

        return state;
    }

    for (int iteration = 0; iteration < MaxSweptIterations; ++iteration)
    {
        const float remainingDistance = movementDistance(remainingStep.x, remainingStep.y, remainingStep.z);

        if (remainingDistance <= 0.0001f)
        {
            if (pDebugInfo != nullptr && sweptFaceHit)
            {
                pDebugInfo->collisionResponseSucceeded = true;
            }

            return finalizeFallState(iterativeState);
        }

        const bx::Vec3 remainingDirection =
            movementDirection(remainingStep.x, remainingStep.y, remainingStep.z);
        const std::vector<const IndoorFaceGeometryData *> candidateFaces = collectSweptCollisionFaceCandidates(
            vertices,
            geometryCache,
            iterativeState.x,
            iterativeState.y,
            iterativeState.footZ,
            body,
            remainingStep.x,
            remainingStep.y,
            remainingStep.z,
            &collisionFaceMask,
            &mechanismBlockingFaceMask,
            iterativeState.sectorId >= 0 ? std::optional<int16_t>(iterativeState.sectorId) : std::nullopt,
            iterativeState.eyeSectorId >= 0 ? std::optional<int16_t>(iterativeState.eyeSectorId) : std::nullopt);
        std::vector<const IndoorFaceGeometryData *> responseFaceCandidates;
        responseFaceCandidates.reserve(candidateFaces.size());

        for (const IndoorFaceGeometryData *pFace : candidateFaces)
        {
            if (pFace == nullptr)
            {
                continue;
            }

            if (pFace->kind == IndoorFaceKind::Wall && pFace->maxZ <= iterativeState.footZ + MaximumRise)
            {
                continue;
            }

            if (iterativeState.grounded
                && pFace->faceIndex == iterativeState.supportFaceIndex
                && (pFace->kind == IndoorFaceKind::Floor || indoorFaceIsSteepFloorCollisionSurface(*pFace)))
            {
                continue;
            }

            if (indoorBodyStartsInsideSteepFloorSweepRadius(
                    *pFace,
                    body,
                    iterativeState.x,
                    iterativeState.y,
                    iterativeState.footZ))
            {
                continue;
            }

            responseFaceCandidates.push_back(pFace);
        }

        IndoorFaceSweepOptions sweepOptions = {};
        sweepOptions.pCollisionFaceMask = &collisionFaceMask;
        sweepOptions.pMechanismBlockingFaceMask = &mechanismBlockingFaceMask;
        sweepOptions.includePortalFaces = false;
        const std::optional<IndoorSweptFaceHit> faceHit = selectNearestIndoorFaceHit(
            buildPrimitiveSweptBody(iterativeState.x, iterativeState.y, iterativeState.footZ, body),
            remainingDirection,
            remainingDistance,
            responseFaceCandidates,
            sweepOptions);
        const std::optional<SweptCollisionHit> actorBodyHit =
            selectNearestActorBodyHit(iterativeState, remainingDirection, remainingDistance);
        const std::optional<SweptCollisionHit> decorationBodyHit =
            selectNearestCylinderBodyHit(
                iterativeState,
                remainingDirection,
                remainingDistance,
                m_decorationColliders,
                SweptCollisionHitType::Decoration);
        const std::optional<SweptCollisionHit> spriteObjectBodyHit =
            selectNearestCylinderBodyHit(
                iterativeState,
                remainingDirection,
                remainingDistance,
                m_spriteObjectColliders,
                SweptCollisionHitType::SpriteObject);
        std::optional<SweptCollisionHit> nearestHit;
        const IndoorFaceGeometryData *pNearestHitGeometry = nullptr;

        if (faceHit)
        {
            const IndoorFaceGeometryData *pHitGeometry =
                geometryCache.geometryForFace(*m_pIndoorMapData, vertices, faceHit->faceIndex);
            SweptCollisionHit hit = {};
            hit.type =
                pHitGeometry != nullptr && pHitGeometry->kind == IndoorFaceKind::Floor
                ? SweptCollisionHitType::Floor
                : pHitGeometry != nullptr && pHitGeometry->kind == IndoorFaceKind::Ceiling
                    ? SweptCollisionHitType::Ceiling
                    : SweptCollisionHitType::Face;
            hit.boundaryHit = faceHit->boundaryHit;
            hit.faceIndex = faceHit->faceIndex;
            hit.point = faceHit->point;
            hit.normal = faceHit->normal;
            hit.heightOffset = faceHit->heightOffset;
            hit.moveDistance = faceHit->moveDistance;
            hit.adjustedMoveDistance = faceHit->adjustedMoveDistance;
            nearestHit = hit;
            pNearestHitGeometry = pHitGeometry;
        }

        if (actorBodyHit
            && (!nearestHit || actorBodyHit->adjustedMoveDistance < nearestHit->adjustedMoveDistance))
        {
            nearestHit = actorBodyHit;
            pNearestHitGeometry = nullptr;
        }

        if (decorationBodyHit
            && (!nearestHit || decorationBodyHit->adjustedMoveDistance < nearestHit->adjustedMoveDistance))
        {
            nearestHit = decorationBodyHit;
            pNearestHitGeometry = nullptr;
        }

        if (spriteObjectBodyHit
            && (!nearestHit || spriteObjectBodyHit->adjustedMoveDistance < nearestHit->adjustedMoveDistance))
        {
            nearestHit = spriteObjectBodyHit;
            pNearestHitGeometry = nullptr;
        }

        if (!nearestHit)
        {
            const float targetX = iterativeState.x + remainingStep.x;
            const float targetY = iterativeState.y + remainingStep.y;
            const float targetFootZ = iterativeState.footZ + remainingStep.z;
            bool hitActor = false;
            IndoorWallCollision wallCollision = {};
            IndoorMoveState targetState = {};

            if (tryResolvePosition(
                    iterativeState.x,
                    iterativeState.y,
                    targetX,
                    targetY,
                    targetFootZ,
                    iterativeVerticalVelocity,
                    targetState,
                    true,
                    &hitActor,
                    &wallCollision))
            {
                if (pDebugInfo != nullptr)
                {
                    pDebugInfo->fullMoveSucceeded = !sweptFaceHit;
                    pDebugInfo->collisionResponseSucceeded = sweptFaceHit;
                }

                return finalizeFallState(targetState);
            }

            fullMoveBlockedByActor = hitActor;
            fullMoveWallCollision = wallCollision;

            if (fullMoveWallCollision.hit && !fullMoveBlockedByActor)
            {
                const IndoorFaceGeometryData *pWallGeometry =
                    geometryCache.geometryForFace(*m_pIndoorMapData, vertices, fullMoveWallCollision.faceIndex);
                const bx::Vec3 projectedSlideStep =
                    projectIndoorVelocityAlongPlane(remainingStep, fullMoveWallCollision.normal, SlideFactor);
                const bx::Vec3 slideStep = lockVerticalStep(
                    applySteepFloorCollisionResponse(projectedSlideStep, pWallGeometry, deltaSeconds),
                    pWallGeometry);

                if (movementDistance(slideStep.x, slideStep.y, slideStep.z) > 0.0001f)
                {
                    IndoorMoveState slideState = {};

                    if (tryResolvePosition(
                            iterativeState.x,
                            iterativeState.y,
                            iterativeState.x + slideStep.x,
                            iterativeState.y + slideStep.y,
                            iterativeState.footZ + slideStep.z,
                            iterativeVerticalVelocity,
                            slideState,
                            true,
                            nullptr,
                            nullptr))
                    {
                        if (pDebugInfo != nullptr)
                        {
                            pDebugInfo->fullMoveSucceeded = false;
                            pDebugInfo->collisionResponseTried = true;
                            pDebugInfo->collisionResponseSucceeded = true;
                            pDebugInfo->primaryBlockKind = IndoorMoveBlockKind::Wall;
                            pDebugInfo->hitFaceIndex = fullMoveWallCollision.faceIndex;
                            pDebugInfo->hitNormal = fullMoveWallCollision.normal;
                            pDebugInfo->responseStep = slideStep;
                        }

                        return finalizeFallState(slideState);
                    }
                }
            }

            sweptFailed = true;
            break;
        }

        sweptFaceHit =
            sweptFaceHit
            || nearestHit->type == SweptCollisionHitType::Face
            || nearestHit->type == SweptCollisionHitType::Floor
            || nearestHit->type == SweptCollisionHitType::Ceiling;

        if (pDebugInfo != nullptr)
        {
            pDebugInfo->collisionResponseTried = true;
            pDebugInfo->primaryBlockKind =
                nearestHit->type == SweptCollisionHitType::Party
                ? IndoorMoveBlockKind::Party
                : nearestHit->type == SweptCollisionHitType::Actor
                    ? IndoorMoveBlockKind::Actor
                    : IndoorMoveBlockKind::Wall;
            pDebugInfo->hitFaceIndex = nearestHit->faceIndex;
            pDebugInfo->hitNormal = nearestHit->normal;
            pDebugInfo->hitPoint = nearestHit->point;
            pDebugInfo->hitMoveDistance = nearestHit->moveDistance;
            pDebugInfo->hitAdjustedMoveDistance = nearestHit->adjustedMoveDistance;
            pDebugInfo->hitHeightOffset = nearestHit->heightOffset;
        }

        if (nearestHit->type == SweptCollisionHitType::Floor && iterativeVerticalVelocity < 0.0f)
        {
            iterativeVerticalVelocity = 0.0f;
        }
        else if (nearestHit->type == SweptCollisionHitType::Ceiling && iterativeVerticalVelocity > 0.0f)
        {
            iterativeVerticalVelocity = 0.0f;
        }

        const float advanceDistance = std::clamp(nearestHit->adjustedMoveDistance, 0.0f, remainingDistance);
        const float advancedX = iterativeState.x + remainingDirection.x * advanceDistance;
        const float advancedY = iterativeState.y + remainingDirection.y * advanceDistance;
        const float advancedFootZ = iterativeState.footZ + remainingDirection.z * advanceDistance;
        IndoorMoveState advancedState = {};

        if (!tryResolvePosition(
                iterativeState.x,
                iterativeState.y,
                advancedX,
                advancedY,
                advancedFootZ,
                iterativeVerticalVelocity,
                advancedState,
                false,
                nullptr,
                nullptr))
        {
            sweptFailed = true;
            break;
        }

        if (nearestHit->type == SweptCollisionHitType::Floor
            && nearestHit->boundaryHit
            && pNearestHitGeometry != nullptr
            && !pNearestHitGeometry->vertices.empty()
            && !sweptRequest.jumpRequested)
        {
            const float stepFloorZ = pNearestHitGeometry->vertices.front().z;
            const float stepDelta = stepFloorZ - iterativeState.footZ;

            if (pNearestHitGeometry->normal.z >= MaximumUphillSlopeNormalZ
                && stepDelta >= GroundSnapSlack
                && stepDelta < MaximumStepUpFromCurrentFootZ)
            {
                advancedState.footZ = stepFloorZ;
                advancedState.verticalVelocity = 0.0f;
                advancedState.grounded = true;
                advancedState.supportFaceIndex = nearestHit->faceIndex;
                advancedState.sectorId = static_cast<int16_t>(pNearestHitGeometry->sectorId);
                advancedState.eyeSectorId = advancedState.sectorId;
                iterativeVerticalVelocity = 0.0f;
                nearestHit->normal = pNearestHitGeometry->normal;
            }
        }

        iterativeState = advancedState;

        if (sweptRequest.blockActorSlide
            && (nearestHit->type == SweptCollisionHitType::Actor
                || nearestHit->type == SweptCollisionHitType::Party))
        {
            return finalizeFallState(iterativeState);
        }

        const float consumedDistance = std::clamp(nearestHit->moveDistance, 0.0f, remainingDistance);
        const float leftoverDistance = std::max(0.0f, remainingDistance - consumedDistance);

        if (leftoverDistance <= 0.0001f)
        {
            if (pDebugInfo != nullptr)
            {
                pDebugInfo->collisionResponseSucceeded = true;
            }

            return finalizeFallState(iterativeState);
        }

        const bx::Vec3 leftoverStep = {
            remainingDirection.x * leftoverDistance,
            remainingDirection.y * leftoverDistance,
            remainingDirection.z * leftoverDistance
        };
        const float responseDamping =
            nearestHit->type == SweptCollisionHitType::Floor ? 1.0f : SlideFactor;

        if (nearestHit->type == SweptCollisionHitType::Face && nearestHit->boundaryHit)
        {
            remainingStep = projectStepAfterFaceHit(leftoverStep, *nearestHit, advancedState, pNearestHitGeometry);
        }
        else
        {
            const bx::Vec3 responseStep =
                projectIndoorVelocityAlongPlane(leftoverStep, nearestHit->normal, responseDamping);
            remainingStep =
                lockVerticalStep(
                    applySteepFloorCollisionResponse(responseStep, pNearestHitGeometry, deltaSeconds),
                    pNearestHitGeometry);
        }

        if (pDebugInfo != nullptr)
        {
            pDebugInfo->responseStep = remainingStep;
        }
    }

    if (!sweptFailed && sweptFaceHit)
    {
        if (pDebugInfo != nullptr)
        {
            pDebugInfo->collisionResponseSucceeded = true;
        }

        return finalizeFallState(iterativeState);
    }

    writePrimaryBlockDebug();
    return finalizeFallState(iterativeState);
}

IndoorCollisionTraceInfo IndoorMovementController::traceCollisionIssues(
    const IndoorMoveState &start,
    const IndoorMoveState &end,
    const IndoorBodyDimensions &body
) const
{
    IndoorCollisionTraceInfo trace = {};

    if (m_pIndoorMapData == nullptr)
    {
        return trace;
    }

    const float moveX = end.x - start.x;
    const float moveY = end.y - start.y;
    const float moveZ = end.footZ - start.footZ;
    const float moveDistance = movementDistance(moveX, moveY, moveZ);
    trace.sectorChanged = start.sectorId != end.sectorId || start.eyeSectorId != end.eyeSectorId;
    trace.supportLost = start.grounded && !end.grounded && end.supportFaceIndex == static_cast<size_t>(-1);
    trace.suddenDrop = start.grounded && !end.grounded && start.footZ - end.footZ > MaximumDrop * 0.5f;

    if (moveDistance <= 0.0001f)
    {
        return trace;
    }

    const RuntimeGeometryCache &runtimeCache = runtimeGeometryCache();
    IndoorFaceGeometryCache &geometryCache = m_runtimeGeometryCache.geometryCache;
    const std::vector<IndoorVertex> &vertices = runtimeCache.vertices;
    const std::vector<uint8_t> &collisionFaceMask = runtimeCache.collisionFaceMask;
    const std::vector<uint8_t> &mechanismBlockingFaceMask = runtimeCache.mechanismBlockingFaceMask;
    const std::optional<int16_t> startSector =
        start.sectorId >= 0 ? std::optional<int16_t>(start.sectorId) : std::nullopt;
    const std::optional<int16_t> startEyeSector =
        start.eyeSectorId >= 0 ? std::optional<int16_t>(start.eyeSectorId) : std::nullopt;
    const bx::Vec3 direction = movementDirection(moveX, moveY, moveZ);
    const IndoorSweptBody sweptBody = buildPrimitiveSweptBody(start.x, start.y, start.footZ, body);
    const std::vector<const IndoorFaceGeometryData *> candidates = collectSweptCollisionFaceCandidates(
        vertices,
        geometryCache,
        start.x,
        start.y,
        start.footZ,
        body,
        moveX,
        moveY,
        moveZ,
        &collisionFaceMask,
        &mechanismBlockingFaceMask,
        startSector,
        startEyeSector);
    std::vector<const IndoorFaceGeometryData *> blockingWallCandidates;
    blockingWallCandidates.reserve(candidates.size());

    for (const IndoorFaceGeometryData *pGeometry : candidates)
    {
        if (pGeometry == nullptr
            || !indoorFaceBlocksAsWallOverlap(*pGeometry, std::min(start.footZ, end.footZ)))
        {
            continue;
        }

        blockingWallCandidates.push_back(pGeometry);
    }

    IndoorFaceSweepOptions sweepOptions = {};
    sweepOptions.pCollisionFaceMask = &collisionFaceMask;
    sweepOptions.pMechanismBlockingFaceMask = &mechanismBlockingFaceMask;
    sweepOptions.includePortalFaces = false;

    const std::optional<IndoorSweptFaceHit> wallHit =
        selectNearestIndoorFaceHit(sweptBody, direction, moveDistance, blockingWallCandidates, sweepOptions);

    if (wallHit && wallHit->adjustedMoveDistance <= moveDistance + 0.5f)
    {
        trace.crossedBlockingFace = true;
        trace.blockingFaceIndex = wallHit->faceIndex;
        trace.blockingFaceNormal = wallHit->normal;
        trace.blockingFacePoint = wallHit->point;
        trace.blockingFaceMoveDistance = wallHit->moveDistance;
        trace.blockingFaceAdjustedMoveDistance = wallHit->adjustedMoveDistance;
    }

    if (trace.sectorChanged)
    {
        std::vector<uint16_t> portalFaceIds;

        const auto appendPortalFaces = [this, &portalFaceIds](int16_t sectorId)
        {
            if (sectorId < 0 || static_cast<size_t>(sectorId) >= m_pIndoorMapData->sectors.size())
            {
                return;
            }

            for (uint16_t faceIndex : m_pIndoorMapData->sectors[sectorId].portalFaceIds)
            {
                if (std::find(portalFaceIds.begin(), portalFaceIds.end(), faceIndex) == portalFaceIds.end())
                {
                    portalFaceIds.push_back(faceIndex);
                }
            }
        };

        appendPortalFaces(start.sectorId);
        appendPortalFaces(start.eyeSectorId);
        appendPortalFaces(end.sectorId);
        appendPortalFaces(end.eyeSectorId);

        for (uint16_t faceIndex : portalFaceIds)
        {
            const IndoorFaceGeometryData *pGeometry =
                geometryCache.geometryForFace(*m_pIndoorMapData, vertices, faceIndex);

            if (pGeometry == nullptr)
            {
                continue;
            }

            if (indoorSweptBodyTouchesPortalFace(sweptBody, direction, moveDistance, *pGeometry))
            {
                trace.sectorTransitionTouchedPortal = true;
                trace.portalFaceIndex = faceIndex;
                break;
            }
        }
    }

    return trace;
}

std::string IndoorMovementController::buildCollisionTraceProbeDetails(
    const IndoorMoveState &start,
    const IndoorMoveState &end,
    const IndoorBodyDimensions &body
) const
{
    if (m_pIndoorMapData == nullptr)
    {
        return {};
    }

    const RuntimeGeometryCache &runtimeCache = runtimeGeometryCache();
    IndoorFaceGeometryCache &geometryCache = m_runtimeGeometryCache.geometryCache;
    const std::vector<IndoorVertex> &vertices = runtimeCache.vertices;
    const std::vector<uint8_t> &nonBlockingMechanismFaceMask = runtimeCache.nonBlockingMechanismFaceMask;
    const std::vector<uint8_t> &collisionFaceMask = runtimeCache.collisionFaceMask;
    const std::vector<uint8_t> &mechanismBlockingFaceMask = runtimeCache.mechanismBlockingFaceMask;
    const float moveX = end.x - start.x;
    const float moveY = end.y - start.y;
    const float moveZ = end.footZ - start.footZ;
    const float moveDistance = movementDistance(moveX, moveY, moveZ);
    const bx::Vec3 direction =
        moveDistance > 0.0001f ? movementDirection(moveX, moveY, moveZ) : bx::Vec3{0.0f, 0.0f, 0.0f};
    const IndoorSweptBody sweptBody = buildPrimitiveSweptBody(start.x, start.y, start.footZ, body);
    const IndoorSweptBodyBounds sweptBounds = buildIndoorSweptBodyBounds(sweptBody, direction, moveDistance);
    const std::optional<int16_t> startSector =
        start.sectorId >= 0 ? std::optional<int16_t>(start.sectorId) : std::nullopt;
    const std::optional<int16_t> startEyeSector =
        start.eyeSectorId >= 0 ? std::optional<int16_t>(start.eyeSectorId) : std::nullopt;
    const std::vector<int16_t> sweptSectorIds = collectSweptCollisionSectorIds(
        vertices,
        geometryCache,
        start.x,
        start.y,
        start.footZ,
        body,
        moveX,
        moveY,
        moveZ,
        startSector,
        startEyeSector);
    const IndoorFloorSample startFloor = sampleSupportedFloor(
        vertices,
        geometryCache,
        start.x,
        start.y,
        start.footZ,
        MaximumRise,
        body.height + 1024.0f,
        body,
        startSector,
        &nonBlockingMechanismFaceMask);
    const IndoorFloorSample endFloor = sampleSupportedFloor(
        vertices,
        geometryCache,
        end.x,
        end.y,
        end.footZ,
        MaximumRise,
        body.height + 1024.0f,
        body,
        end.sectorId >= 0 ? std::optional<int16_t>(end.sectorId) : std::nullopt,
        &nonBlockingMechanismFaceMask);
    const bx::Vec3 endBodyCenter = {
        end.x,
        end.y,
        end.footZ + std::min(body.height * 0.5f, std::max(body.radius, 1.0f))
    };

    struct ProbeFace
    {
        const IndoorFaceGeometryData *pGeometry = nullptr;
        std::optional<IndoorSweptFaceHit> sweepHit;
        float planeDistance = 0.0f;
        bool boundsTouch = false;
        bool blockedAtEnd = false;
        bool portalTouch = false;
        bool relevantSector = false;
        bool supportFace = false;
        int priority = 0;
    };

    const auto sectorIsRelevant =
        [&sweptSectorIds, &start, &end](uint16_t sectorId) -> bool
        {
            const int16_t signedSectorId = static_cast<int16_t>(sectorId);

            if (signedSectorId == start.sectorId
                || signedSectorId == start.eyeSectorId
                || signedSectorId == end.sectorId
                || signedSectorId == end.eyeSectorId)
            {
                return true;
            }

            return std::find(sweptSectorIds.begin(), sweptSectorIds.end(), signedSectorId) != sweptSectorIds.end();
        };

    IndoorFaceSweepOptions sweepOptions = {};
    sweepOptions.pCollisionFaceMask = &collisionFaceMask;
    sweepOptions.pMechanismBlockingFaceMask = &mechanismBlockingFaceMask;
    sweepOptions.includePortalFaces = true;

    std::vector<ProbeFace> probeFaces;
    probeFaces.reserve(32);

    for (size_t faceIndex = 0; faceIndex < m_pIndoorMapData->faces.size(); ++faceIndex)
    {
        const IndoorFaceGeometryData *pGeometry =
            geometryCache.geometryForFace(*m_pIndoorMapData, vertices, faceIndex);

        if (pGeometry == nullptr || pGeometry->vertices.empty())
        {
            continue;
        }

        const bool relevantSector =
            sectorIsRelevant(pGeometry->sectorId)
            || sectorIsRelevant(pGeometry->backSectorId);
        const bool supportFace =
            faceIndex == start.supportFaceIndex
            || faceIndex == end.supportFaceIndex
            || (startFloor.hasFloor && faceIndex == startFloor.faceIndex)
            || (endFloor.hasFloor && faceIndex == endFloor.faceIndex);
        const bool boundsTouch = indoorSweptBodyBoundsTouchFace(sweptBounds, *pGeometry, body.radius + 48.0f);
        const bool blockedAtEnd =
            indoorFaceBlocksAsWallOverlap(*pGeometry, end.footZ)
            && isIndoorCylinderBlockedByFace(*pGeometry, end.x, end.y, end.footZ, body.radius, body.height);
        const bool portalTouch =
            pGeometry->isPortal
            && moveDistance > 0.0001f
            && indoorSweptBodyTouchesPortalFace(sweptBody, direction, moveDistance, *pGeometry);
        std::optional<IndoorSweptFaceHit> sweepHit;

        if (moveDistance > 0.0001f
            && boundsTouch
            && canSweepAgainstIndoorFace(*pGeometry, sweepOptions))
        {
            sweepHit = sweepIndoorBodyAgainstFace(sweptBody, direction, moveDistance, *pGeometry, sweepOptions);
        }

        if (!supportFace && !blockedAtEnd && !portalTouch && !sweepHit && !(relevantSector && boundsTouch))
        {
            continue;
        }

        ProbeFace face = {};
        face.pGeometry = pGeometry;
        face.sweepHit = sweepHit;
        face.boundsTouch = boundsTouch;
        face.blockedAtEnd = blockedAtEnd;
        face.portalTouch = portalTouch;
        face.relevantSector = relevantSector;
        face.supportFace = supportFace;
        face.planeDistance = std::fabs(dotVec(subtractVec(endBodyCenter, pGeometry->vertices.front()), pGeometry->normal));
        face.priority =
            sweepHit || blockedAtEnd || portalTouch
                ? 0
                : supportFace
                    ? 1
                    : relevantSector && boundsTouch
                        ? 2
                        : relevantSector
                            ? 3
                            : 4;
        probeFaces.push_back(face);
    }

    std::sort(
        probeFaces.begin(),
        probeFaces.end(),
        [](const ProbeFace &left, const ProbeFace &right)
        {
            if (left.priority != right.priority)
            {
                return left.priority < right.priority;
            }

            return left.planeDistance < right.planeDistance;
        });

    std::ostringstream out;
    out << " trace_swept_sectors=\"";

    for (size_t index = 0; index < sweptSectorIds.size(); ++index)
    {
        if (index > 0)
        {
            out << ",";
        }

        out << sweptSectorIds[index];
    }

    out << "\""
        << " trace_start_floor_has=" << (startFloor.hasFloor ? "true" : "false")
        << " trace_start_floor=" << startFloor.faceIndex
        << " trace_start_floor_sector=" << startFloor.sectorId
        << " trace_start_floor_height=" << startFloor.height
        << " trace_start_floor_normal_z=" << startFloor.normalZ
        << " trace_end_floor_has=" << (endFloor.hasFloor ? "true" : "false")
        << " trace_end_floor=" << endFloor.faceIndex
        << " trace_end_floor_sector=" << endFloor.sectorId
        << " trace_end_floor_height=" << endFloor.height
        << " trace_end_floor_normal_z=" << endFloor.normalZ
        << " trace_near_faces=\"";

    constexpr size_t MaxProbeFaces = 18;
    const size_t faceCount = std::min(MaxProbeFaces, probeFaces.size());

    for (size_t index = 0; index < faceCount; ++index)
    {
        const ProbeFace &face = probeFaces[index];
        const IndoorFaceGeometryData &geometry = *face.pGeometry;

        if (index > 0)
        {
            out << ";";
        }

        out << geometry.faceIndex
            << ":kind=" << indoorTraceFaceKindName(geometry.kind)
            << ":portal=" << (geometry.isPortal ? "true" : "false")
            << ":facet=" << static_cast<int>(geometry.facetType)
            << ":sector=" << geometry.sectorId
            << ":back=" << geometry.backSectorId
            << ":normal=(" << geometry.normal.x << "," << geometry.normal.y << "," << geometry.normal.z << ")"
            << ":bounds=(" << geometry.minX << "," << geometry.minY << "," << geometry.minZ
            << ")-(" << geometry.maxX << "," << geometry.maxY << "," << geometry.maxZ << ")"
            << ":dist=" << face.planeDistance
            << ":bounds_touch=" << (face.boundsTouch ? "true" : "false")
            << ":blocked_end=" << (face.blockedAtEnd ? "true" : "false")
            << ":portal_touch=" << (face.portalTouch ? "true" : "false")
            << ":support=" << (face.supportFace ? "true" : "false")
            << ":relevant_sector=" << (face.relevantSector ? "true" : "false");

        if (face.sweepHit)
        {
            out << ":sweep_hit=true"
                << ":hit_move=" << face.sweepHit->moveDistance
                << ":hit_adjusted=" << face.sweepHit->adjustedMoveDistance
                << ":hit_point=(" << face.sweepHit->point.x
                << "," << face.sweepHit->point.y
                << "," << face.sweepHit->point.z << ")"
                << ":hit_height_offset=" << face.sweepHit->heightOffset
                << ":boundary=" << (face.sweepHit->boundaryHit ? "true" : "false");
        }
        else
        {
            out << ":sweep_hit=false";
        }
    }

    out << "\"";
    return out.str();
}

bool IndoorMovementController::collidesAtPosition(
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    float x,
    float y,
    float footZ,
    const IndoorBodyDimensions &body,
    const std::vector<uint8_t> *pCollisionFaceMask,
    const std::vector<uint8_t> *pMechanismBlockingFaceMask,
    std::optional<int16_t> primarySectorId,
    std::optional<int16_t> secondarySectorId,
    size_t ignoredSupportFaceIndex,
    float movementX,
    float movementY,
    IndoorWallCollision *pWallCollision
) const
{
    if (m_pIndoorMapData == nullptr)
    {
        return false;
    }

    const std::vector<const IndoorFaceGeometryData *> candidateFaces = collectSweptCollisionFaceCandidates(
        vertices,
        geometryCache,
        x - movementX,
        y - movementY,
        footZ,
        body,
        movementX,
        movementY,
        0.0f,
        pCollisionFaceMask,
        pMechanismBlockingFaceMask,
        primarySectorId,
        secondarySectorId);
    IndoorWallCollision bestWallCollision = {};
    float bestWallScore = -1.0f;
    const float movementLength = std::sqrt(movementX * movementX + movementY * movementY);

    for (const IndoorFaceGeometryData *pGeometry : candidateFaces)
    {
        if (pGeometry != nullptr
            && pGeometry->faceIndex == ignoredSupportFaceIndex
            && (pGeometry->kind == IndoorFaceKind::Floor || indoorFaceIsSteepFloorCollisionSurface(*pGeometry)))
        {
            continue;
        }

        if (pGeometry == nullptr
            || !indoorFaceBlocksAsWallOverlap(*pGeometry, footZ)
            || !isIndoorCylinderBlockedByFace(*pGeometry, x, y, footZ, body.radius, body.height))
        {
            continue;
        }

        const bx::Vec3 oldCenter = {
            x - movementX,
            y - movementY,
            footZ + std::min(body.height * 0.5f, std::max(body.radius, 1.0f))
        };
        const bx::Vec3 newCenter = {
            x,
            y,
            footZ + std::min(body.height * 0.5f, std::max(body.radius, 1.0f))
        };
        const float oldSignedDistance =
            dotVec(subtractVec(oldCenter, pGeometry->vertices.front()), pGeometry->normal);
        const float newSignedDistance =
            dotVec(subtractVec(newCenter, pGeometry->vertices.front()), pGeometry->normal);
        const float oldDistance = std::abs(oldSignedDistance);
        const float newDistance = std::abs(newSignedDistance);
        const bool startedInsideWallRadius = oldDistance <= body.radius + 0.5f;
        const bool stayedOnSameSide =
            oldSignedDistance == 0.0f
            || newSignedDistance == 0.0f
            || (oldSignedDistance > 0.0f) == (newSignedDistance > 0.0f);
        const bool didNotMoveTowardWall = newDistance >= oldDistance - 0.5f;

        if (startedInsideWallRadius && stayedOnSameSide && didNotMoveTowardWall)
        {
            continue;
        }

        if (pWallCollision == nullptr)
        {
            return true;
        }

        bx::Vec3 hitNormal = {
            pGeometry->normal.x,
            pGeometry->normal.y,
            0.0f
        };
        const float hitNormalLength = std::sqrt(hitNormal.x * hitNormal.x + hitNormal.y * hitNormal.y);
        float score = 1.0f;

        if (movementLength > 0.0001f && hitNormalLength > 0.0001f)
        {
            hitNormal.x /= hitNormalLength;
            hitNormal.y /= hitNormalLength;
            score = std::abs(movementX * hitNormal.x + movementY * hitNormal.y) / movementLength;
        }

        if (!bestWallCollision.hit || score > bestWallScore)
        {
            bestWallCollision.hit = true;
            bestWallCollision.normal = pGeometry->normal;
            bestWallCollision.faceIndex = pGeometry->faceIndex;
            bestWallScore = score;
        }
    }

    if (bestWallCollision.hit && pWallCollision != nullptr)
    {
        *pWallCollision = bestWallCollision;
        return true;
    }

    return false;
}

std::vector<int16_t> IndoorMovementController::collectSweptCollisionSectorIds(
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    float startX,
    float startY,
    float startFootZ,
    const IndoorBodyDimensions &body,
    float movementX,
    float movementY,
    float movementZ,
    std::optional<int16_t> primarySectorId,
    std::optional<int16_t> secondarySectorId
) const
{
    std::vector<int16_t> sectorIds;

    if (m_pIndoorMapData == nullptr)
    {
        return sectorIds;
    }

    const auto appendSectorId = [&](int16_t sectorId)
    {
        if (sectorId < 0 || static_cast<size_t>(sectorId) >= m_pIndoorMapData->sectors.size())
        {
            return;
        }

        if (std::find(sectorIds.begin(), sectorIds.end(), sectorId) != sectorIds.end())
        {
            return;
        }

        sectorIds.push_back(sectorId);
    };
    const IndoorSweptBody sweptBody = buildPrimitiveSweptBody(startX, startY, startFootZ, body);
    const bx::Vec3 direction = movementDirection(movementX, movementY, movementZ);
    const float distance = movementDistance(movementX, movementY, movementZ);
    const auto appendPortalAdjacentSectors = [&](int16_t sectorId)
    {
        if (sectorId < 0 || static_cast<size_t>(sectorId) >= m_pIndoorMapData->sectors.size())
        {
            return;
        }

        const IndoorSector &sector = m_pIndoorMapData->sectors[sectorId];

        for (uint16_t faceId : sector.portalFaceIds)
        {
            const IndoorFaceGeometryData *pGeometry =
                geometryCache.geometryForFace(*m_pIndoorMapData, vertices, faceId);

            if (pGeometry == nullptr || !indoorSweptBodyTouchesPortalFace(sweptBody, direction, distance, *pGeometry))
            {
                continue;
            }

            if (pGeometry->sectorId == static_cast<uint16_t>(sectorId))
            {
                appendSectorId(static_cast<int16_t>(pGeometry->backSectorId));
            }
            else if (pGeometry->backSectorId == static_cast<uint16_t>(sectorId))
            {
                appendSectorId(static_cast<int16_t>(pGeometry->sectorId));
            }
        }
    };

    if (primarySectorId)
    {
        appendSectorId(*primarySectorId);
    }

    if (secondarySectorId)
    {
        appendSectorId(*secondarySectorId);
    }

    const size_t baseSectorCount = sectorIds.size();

    for (size_t index = 0; index < baseSectorCount; ++index)
    {
        appendPortalAdjacentSectors(sectorIds[index]);
    }

    return sectorIds;
}

std::vector<const IndoorFaceGeometryData *> IndoorMovementController::collectSweptCollisionFaceCandidates(
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    float startX,
    float startY,
    float startFootZ,
    const IndoorBodyDimensions &body,
    float movementX,
    float movementY,
    float movementZ,
    const std::vector<uint8_t> *pCollisionFaceMask,
    const std::vector<uint8_t> *pMechanismBlockingFaceMask,
    std::optional<int16_t> primarySectorId,
    std::optional<int16_t> secondarySectorId
) const
{
    std::vector<const IndoorFaceGeometryData *> candidates;

    if (m_pIndoorMapData == nullptr)
    {
        return candidates;
    }

    const std::vector<int16_t> collisionSectorIds = collectSweptCollisionSectorIds(
        vertices,
        geometryCache,
        startX,
        startY,
        startFootZ,
        body,
        movementX,
        movementY,
        movementZ,
        primarySectorId,
        secondarySectorId);
    const IndoorSweptBody sweptBody = buildPrimitiveSweptBody(startX, startY, startFootZ, body);
    const bx::Vec3 sweepDirection = movementDirection(movementX, movementY, movementZ);
    const float sweepDistance = movementDistance(movementX, movementY, movementZ);
    const IndoorSweptBodyBounds sweptBounds =
        buildIndoorSweptBodyBounds(sweptBody, sweepDirection, sweepDistance);
    const auto sectorIsRelevant = [&collisionSectorIds](uint16_t sectorId) -> bool
    {
        return std::find(collisionSectorIds.begin(), collisionSectorIds.end(), static_cast<int16_t>(sectorId))
            != collisionSectorIds.end();
    };

    const bool useSectorFilteredFaces = !collisionSectorIds.empty();
    struct SectorFaceCandidate
    {
        uint16_t faceIndex = 0;
        bool requireCollisionMask = false;
    };

    std::vector<SectorFaceCandidate> sectorFaceIds;

    if (useSectorFilteredFaces)
    {
        const bool useCollisionFaceMask = pCollisionFaceMask != nullptr && !pCollisionFaceMask->empty();
        const auto appendFaceIds = [&sectorFaceIds](
            const std::vector<uint16_t> &faceIds,
            bool requireCollisionMask)
        {
            for (uint16_t faceId : faceIds)
            {
                sectorFaceIds.push_back({faceId, requireCollisionMask});
            }
        };

        for (int16_t sectorId : collisionSectorIds)
        {
            if (sectorId < 0 || static_cast<size_t>(sectorId) >= m_pIndoorMapData->sectors.size())
            {
                continue;
            }

            const IndoorSector &sector = m_pIndoorMapData->sectors[sectorId];
            appendFaceIds(sector.floorFaceIds, false);
            appendFaceIds(sector.wallFaceIds, false);
            appendFaceIds(sector.ceilingFaceIds, false);

            if (useCollisionFaceMask)
            {
                appendFaceIds(sector.cylinderFaceIds, true);
            }
        }

        candidates.reserve(sectorFaceIds.size());
    }
    else
    {
        candidates.reserve(m_pIndoorMapData->faces.size());
    }

    uint32_t candidateVisitStamp = 0;
    if (useSectorFilteredFaces)
    {
        const size_t faceCount = m_pIndoorMapData->faces.size();
        if (m_candidateFaceVisitStamps.size() != faceCount)
        {
            m_candidateFaceVisitStamps.assign(faceCount, 0);
            m_candidateFaceVisitStamp = 1;
        }

        ++m_candidateFaceVisitStamp;
        if (m_candidateFaceVisitStamp == 0)
        {
            std::fill(m_candidateFaceVisitStamps.begin(), m_candidateFaceVisitStamps.end(), 0);
            m_candidateFaceVisitStamp = 1;
        }

        candidateVisitStamp = m_candidateFaceVisitStamp;
    }

    const auto appendCandidateFace = [&](size_t faceIndex, bool requireCollisionMask)
    {
        if (faceIndex >= m_pIndoorMapData->faces.size())
        {
            return;
        }

        if (requireCollisionMask
            && pCollisionFaceMask != nullptr
            && !pCollisionFaceMask->empty()
            && (faceIndex >= pCollisionFaceMask->size() || (*pCollisionFaceMask)[faceIndex] == 0))
        {
            return;
        }

        if (pMechanismBlockingFaceMask != nullptr
            && faceIndex < pMechanismBlockingFaceMask->size()
            && (*pMechanismBlockingFaceMask)[faceIndex] == 0)
        {
            return;
        }

        if (useSectorFilteredFaces)
        {
            if (m_candidateFaceVisitStamps[faceIndex] == candidateVisitStamp)
            {
                return;
            }

            m_candidateFaceVisitStamps[faceIndex] = candidateVisitStamp;
        }

        const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(
            *m_pIndoorMapData,
            vertices,
            faceIndex);

        if (pGeometry == nullptr
            || (!collisionSectorIds.empty()
                && !sectorIsRelevant(pGeometry->sectorId)
                && !sectorIsRelevant(pGeometry->backSectorId)))
        {
            return;
        }

        IndoorFaceSweepOptions sweepOptions = {};
        sweepOptions.pCollisionFaceMask = requireCollisionMask ? pCollisionFaceMask : nullptr;
        sweepOptions.pMechanismBlockingFaceMask = pMechanismBlockingFaceMask;
        sweepOptions.includePortalFaces = false;

        if (!canSweepAgainstIndoorFace(*pGeometry, sweepOptions)
            || !indoorSweptBodyBoundsTouchFace(sweptBounds, *pGeometry))
        {
            return;
        }

        candidates.push_back(pGeometry);
    };

    if (useSectorFilteredFaces)
    {
        for (const SectorFaceCandidate &candidate : sectorFaceIds)
        {
            if (candidate.requireCollisionMask)
            {
                continue;
            }

            appendCandidateFace(candidate.faceIndex, candidate.requireCollisionMask);
        }

        for (const SectorFaceCandidate &candidate : sectorFaceIds)
        {
            if (!candidate.requireCollisionMask)
            {
                continue;
            }

            appendCandidateFace(candidate.faceIndex, candidate.requireCollisionMask);
        }
    }
    else
    {
        for (size_t faceIndex = 0; faceIndex < m_pIndoorMapData->faces.size(); ++faceIndex)
        {
            appendCandidateFace(faceIndex, false);
        }
    }

    return candidates;
}

bool IndoorMovementController::collidesWithActors(
    float currentX,
    float currentY,
    float candidateX,
    float candidateY,
    float footZ,
    const IndoorBodyDimensions &body,
    std::vector<size_t> *pContactedActorIndices,
    std::optional<size_t> ignoredActorIndex,
    bool ignoreActorCollisions,
    bool *pHitActor
) const
{
    if (!hasCylinderCollisionHorizontalComponent(candidateX - currentX, candidateY - currentY))
    {
        return false;
    }

    const float bodyMinZ = footZ;
    const float bodyMaxZ = footZ + body.height;

    for (const IndoorActorCollision &collider : m_actorColliders)
    {
        if (ignoredActorIndex.has_value() && collider.actorIndex == *ignoredActorIndex)
        {
            continue;
        }

        if (ignoreActorCollisions && collider.reportActorContact)
        {
            continue;
        }

        if (bodyMaxZ < collider.z || bodyMinZ > collider.z + collider.height)
        {
            continue;
        }

        const float minimumDistance = body.radius + collider.radius;

        if (minimumDistance <= 0.0f)
        {
            continue;
        }

        const float candidateDeltaX = candidateX - collider.x;
        const float candidateDeltaY = candidateY - collider.y;
        const float candidateDistanceSquared =
            candidateDeltaX * candidateDeltaX + candidateDeltaY * candidateDeltaY;

        if (candidateDistanceSquared >= minimumDistance * minimumDistance)
        {
            continue;
        }

        const float currentDeltaX = currentX - collider.x;
        const float currentDeltaY = currentY - collider.y;
        const float currentDistanceSquared = currentDeltaX * currentDeltaX + currentDeltaY * currentDeltaY;

        const bool actorVsActor = ignoredActorIndex.has_value() && collider.reportActorContact;

        if (shouldIgnoreExistingActorOverlap(
                currentX,
                currentY,
                body,
                collider,
                actorVsActor))
        {
            continue;
        }

        if (pContactedActorIndices != nullptr
            && collider.reportActorContact
            && std::find(
                pContactedActorIndices->begin(),
                pContactedActorIndices->end(),
                collider.actorIndex) == pContactedActorIndices->end())
        {
            pContactedActorIndices->push_back(collider.actorIndex);
        }

        if (candidateDistanceSquared > currentDistanceSquared + 1.0f)
        {
            continue;
        }

        if (pHitActor != nullptr)
        {
            *pHitActor = true;
        }

        return true;
    }

    return false;
}

std::vector<uint8_t> IndoorMovementController::buildCollisionFaceMask() const
{
    std::vector<uint8_t> result;

    if (m_pIndoorMapData == nullptr)
    {
        return result;
    }

    result.assign(m_pIndoorMapData->faces.size(), 0);
    bool hasExplicitCollisionFaces = false;

    for (const IndoorSector &sector : m_pIndoorMapData->sectors)
    {
        for (uint16_t faceId : sector.cylinderFaceIds)
        {
            if (faceId >= result.size())
            {
                continue;
            }

            result[faceId] = 1;
            hasExplicitCollisionFaces = true;
        }
    }

    if (!hasExplicitCollisionFaces)
    {
        result.clear();
    }

    return result;
}
}
