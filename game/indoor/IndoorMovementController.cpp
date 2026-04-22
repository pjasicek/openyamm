#include "game/indoor/IndoorMovementController.h"

#include "game/FaceEnums.h"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MaximumRise = 48.0f;
constexpr float MaximumDrop = 160.0f;
constexpr float SlideFactor = 0.75f;
constexpr float GravityPerSecond = 960.0f;
constexpr float JumpVelocity = 420.0f;
constexpr float GroundSnapSlack = 8.0f;

bool doorFaceUsesMovedVertex(const IndoorMapData &indoorMapData, const MapDeltaDoor &door, uint16_t faceId)
{
    if (faceId >= indoorMapData.faces.size() || door.vertexIds.empty())
    {
        return false;
    }

    const IndoorFace &face = indoorMapData.faces[faceId];

    for (uint16_t faceVertexId : face.vertexIndices)
    {
        if (std::find(door.vertexIds.begin(), door.vertexIds.end(), faceVertexId) != door.vertexIds.end())
        {
            return true;
        }
    }

    return false;
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

    return runtimeMechanism.isMoving
        ? EventRuntime::calculateMechanismDistance(door, runtimeMechanism)
        : runtimeMechanism.currentDistance;
}

std::vector<std::pair<float, float>> buildSupportProbeOffsets(float radius)
{
    const float effectiveRadius = std::max(8.0f, radius);
    const std::array<float, 7> normalizedOffsets = {
        -1.0f,
        -0.66666667f,
        -0.33333334f,
        0.0f,
        0.33333334f,
        0.66666667f,
        1.0f
    };
    std::vector<std::pair<float, float>> result;
    result.reserve(normalizedOffsets.size() * normalizedOffsets.size());

    for (float offsetY : normalizedOffsets)
    {
        for (float offsetX : normalizedOffsets)
        {
            if (offsetX == 0.0f && offsetY == 0.0f)
            {
                continue;
            }

            if (offsetX * offsetX + offsetY * offsetY > 1.0f)
            {
                continue;
            }

            result.emplace_back(offsetX * effectiveRadius, offsetY * effectiveRadius);
        }
    }

    return result;
}

std::vector<uint32_t> buildDoorStateSignature(
    const std::optional<MapDeltaData> *pMapDeltaData,
    const std::optional<EventRuntimeState> *pEventRuntimeState)
{
    std::vector<uint32_t> signature;

    if (pMapDeltaData == nullptr || !pMapDeltaData->has_value())
    {
        return signature;
    }

    const std::vector<MapDeltaDoor> &doors = (*pMapDeltaData)->doors;
    signature.reserve(doors.size() * 2);

    for (const MapDeltaDoor &door : doors)
    {
        const float distance = resolveDoorDistance(door, pEventRuntimeState);
        signature.push_back(door.doorId);
        signature.push_back(std::bit_cast<uint32_t>(distance));
    }

    return signature;
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

void IndoorMovementController::refreshRuntimeGeometryCache() const
{
    if (m_pIndoorMapData == nullptr)
    {
        return;
    }

    const std::vector<uint32_t> doorStateSignature = buildDoorStateSignature(m_pMapDeltaData, m_pEventRuntimeState);

    if (m_runtimeGeometryCache.valid && m_runtimeGeometryCache.doorStateSignature == doorStateSignature)
    {
        return;
    }

    const MapDeltaData *pMapDeltaData =
        m_pMapDeltaData != nullptr && m_pMapDeltaData->has_value() ? &m_pMapDeltaData->value() : nullptr;
    const EventRuntimeState *pEventRuntimeState =
        m_pEventRuntimeState != nullptr && m_pEventRuntimeState->has_value() ? &m_pEventRuntimeState->value() : nullptr;

    m_runtimeGeometryCache.vertices = buildIndoorMechanismAdjustedVertices(
        *m_pIndoorMapData,
        pMapDeltaData,
        pEventRuntimeState);
    m_runtimeGeometryCache.nonBlockingMechanismFaceMask = buildNonBlockingMechanismFaceMask();
    m_runtimeGeometryCache.mechanismBlockingFaceMask = buildMechanismBlockingFaceMask();
    m_runtimeGeometryCache.collisionFaceMask = buildCollisionFaceMask();
    m_runtimeGeometryCache.geometryCache.reset(m_pIndoorMapData->faces.size());
    m_runtimeGeometryCache.doorStateSignature = doorStateSignature;
    m_runtimeGeometryCache.valid = true;
}

const IndoorMovementController::RuntimeGeometryCache &IndoorMovementController::runtimeGeometryCache() const
{
    refreshRuntimeGeometryCache();
    return m_runtimeGeometryCache;
}

const std::vector<std::pair<float, float>> &IndoorMovementController::supportProbeOffsets(float radius) const
{
    if (m_cachedSupportProbeRadius < 0.0f || std::fabs(m_cachedSupportProbeRadius - radius) > 0.001f)
    {
        m_cachedSupportProbeRadius = radius;
        m_cachedSupportProbeOffsets = buildSupportProbeOffsets(radius);
    }

    return m_cachedSupportProbeOffsets;
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

    for (const std::pair<float, float> &offset : supportProbeOffsets(body.radius))
    {
        IndoorFloorSample candidate = sampleIndoorFloor(
            *m_pIndoorMapData,
            vertices,
            x + offset.first,
            y + offset.second,
            z,
            maxRise,
            maxDrop,
            preferredSectorId,
            pFaceExclusionMask,
            &geometryCache);

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

    for (const std::pair<float, float> &offset : supportProbeOffsets(body.radius))
    {
        IndoorFloorSample candidate = sampleIndoorFloorOnFace(
            *m_pIndoorMapData,
            vertices,
            faceIndex,
            x + offset.first,
            y + offset.second,
            z,
            maxRise,
            maxDrop,
            pFaceExclusionMask,
            &geometryCache);

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
        return candidateState;
    };

    auto tryInitializeState = [&](float candidateX, float candidateY, float candidateEyeZ) -> std::optional<IndoorMoveState>
    {
        IndoorMoveState candidateState = {};
        candidateState.x = candidateX;
        candidateState.y = candidateY;
        candidateState.eyeHeight = body.height;
        candidateState.footZ = candidateEyeZ - body.height;

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
        }
        else
        {
            const std::optional<int16_t> sectorId =
                findIndoorSectorForPoint(*m_pIndoorMapData, vertices, {candidateX, candidateY, candidateEyeZ}, &geometryCache);
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
    IndoorMoveDebugInfo *pDebugInfo
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

    IndoorMoveState resolved = state;
    const float stepX = desiredVelocityX * deltaSeconds;
    const float stepY = desiredVelocityY * deltaSeconds;
    const std::optional<int16_t> preferredSectorId =
        state.sectorId >= 0 ? std::optional<int16_t>(state.sectorId) : std::nullopt;
    const IndoorFloorSample currentFloor = sampleSupportedFloor(
        vertices,
        geometryCache,
        state.x,
        state.y,
        state.footZ,
        body.height + MaximumRise,
        body.height + 1024.0f,
        body,
        preferredSectorId,
        &nonBlockingMechanismFaceMask);
    const IndoorFloorSample preferredCurrentFloor =
        state.supportFaceIndex != static_cast<size_t>(-1)
        ? sampleSupportedFloorOnFace(
            vertices,
            geometryCache,
            state.supportFaceIndex,
            state.x,
            state.y,
            state.footZ,
            body.height + MaximumRise,
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
        effectiveCurrentFloor.hasFloor && state.footZ <= effectiveCurrentFloor.height + GroundSnapSlack;
    float candidateFootZ = state.footZ;
    float candidateVerticalVelocity = state.verticalVelocity;
    bool candidateGrounded = state.grounded && supportedByCurrentFloor;
    bool fullMoveBlockedByActor = false;
    IndoorWallCollision fullMoveWallCollision = {};

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

        if (jumpRequested)
        {
            candidateGrounded = false;
            candidateVerticalVelocity = JumpVelocity;
            candidateFootZ += 1.0f;
        }
    }

    if (!candidateGrounded)
    {
        candidateVerticalVelocity -= GravityPerSecond * deltaSeconds;
        candidateFootZ += candidateVerticalVelocity * deltaSeconds;
    }

    auto tryResolvePosition =
        [&](
            float candidateX,
            float candidateY,
            IndoorMoveState &candidateState,
            bool *pHitActor,
            IndoorWallCollision *pWallCollision) -> bool
    {
        IndoorFloorSample floor = sampleSupportedFloor(
            vertices,
            geometryCache,
            candidateX,
            candidateY,
            candidateFootZ,
            body.height + MaximumRise,
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
                candidateFootZ,
                body.height + MaximumRise,
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

        if (!floor.hasFloor && state.grounded && !jumpRequested)
        {
            approximateFloor = sampleApproximateSupportedFloor(
                vertices,
                geometryCache,
                candidateX,
                candidateY,
                candidateFootZ,
                body.height + MaximumRise,
                body.height + 1024.0f,
                body,
                preferredSectorId,
                state.supportFaceIndex,
                &nonBlockingMechanismFaceMask);
            floor = approximateFloor;
        }

        float resolvedFootZ = candidateFootZ;
        float resolvedVerticalVelocity = candidateVerticalVelocity;
        bool resolvedGrounded = false;

        if (floor.hasFloor)
        {
            const bool shouldSnapToFloor =
                (state.grounded && !jumpRequested && candidateVerticalVelocity <= 0.0f)
                || (candidateVerticalVelocity <= 0.0f && candidateFootZ <= floor.height + GroundSnapSlack);

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
            resolvedFootZ + body.height,
            floor.hasFloor && floor.sectorId >= 0 ? std::optional<int16_t>(floor.sectorId) : preferredSectorId,
            &nonBlockingMechanismFaceMask,
            &geometryCache);

        if (ceiling.hasCeiling && resolvedFootZ + body.height > ceiling.height - 1.0f)
        {
            resolvedFootZ = ceiling.height - body.height - 1.0f;
            resolvedVerticalVelocity = std::min(resolvedVerticalVelocity, 0.0f);
        }

        if (floor.hasFloor && resolvedFootZ < floor.height)
        {
            resolvedFootZ = floor.height;
            resolvedVerticalVelocity = 0.0f;
            resolvedGrounded = true;
        }

        const float resolvedEyeZ = resolvedFootZ + body.height;
        const std::optional<int16_t> eyeSectorId = findIndoorSectorForPoint(
            *m_pIndoorMapData,
            vertices,
            {candidateX, candidateY, resolvedEyeZ},
            &geometryCache);
        const std::optional<int16_t> floorSectorId =
            floor.hasFloor && floor.sectorId >= 0 ? std::optional<int16_t>(floor.sectorId) : std::nullopt;
        const std::optional<int16_t> fallbackSectorId =
            state.sectorId >= 0 ? std::optional<int16_t>(state.sectorId) : std::nullopt;
        const std::optional<int16_t> primarySectorId =
            floorSectorId ? floorSectorId : (eyeSectorId ? eyeSectorId : fallbackSectorId);

        if (collidesAtPosition(
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
                candidateX - state.x,
                candidateY - state.y,
                pWallCollision))
        {
            return false;
        }

        if (collidesWithActors(
                state.x,
                state.y,
                candidateX,
                candidateY,
                resolvedFootZ,
                body,
                pContactedActorIndices,
                ignoredActorIndex,
                pHitActor))
        {
            return false;
        }

        const bool stateWasSpatiallyValid =
            state.grounded || state.sectorId >= 0 || state.eyeSectorId >= 0;

        if (stateWasSpatiallyValid && !resolvedGrounded && !floor.hasFloor && !eyeSectorId.has_value())
        {
            return false;
        }

        candidateState.x = candidateX;
        candidateState.y = candidateY;
        candidateState.footZ = resolvedFootZ;
        candidateState.verticalVelocity = resolvedVerticalVelocity;
        candidateState.sectorId = floor.hasFloor ? floor.sectorId : eyeSectorId.value_or(state.sectorId);
        candidateState.eyeSectorId = eyeSectorId.value_or(candidateState.sectorId);
        candidateState.supportFaceIndex = floor.hasFloor ? floor.faceIndex : static_cast<size_t>(-1);
        candidateState.grounded = resolvedGrounded;

        return true;
    };

    if (tryResolvePosition(state.x + stepX, state.y + stepY, resolved, &fullMoveBlockedByActor, &fullMoveWallCollision))
    {
        if (pDebugInfo != nullptr)
        {
            pDebugInfo->fullMoveSucceeded = true;
        }

        return resolved;
    }

    if (pDebugInfo != nullptr)
    {
        if (fullMoveBlockedByActor)
        {
            pDebugInfo->primaryBlockKind = IndoorMoveBlockKind::Actor;
        }
        else if (fullMoveWallCollision.hit)
        {
            pDebugInfo->primaryBlockKind = IndoorMoveBlockKind::Wall;
            pDebugInfo->wallFaceIndex = fullMoveWallCollision.faceIndex;
            pDebugInfo->wallNormal = fullMoveWallCollision.normal;
        }
        else
        {
            pDebugInfo->primaryBlockKind = IndoorMoveBlockKind::InvalidPosition;
        }
    }

    if (blockActorSlide && fullMoveBlockedByActor)
    {
        return state;
    }

    float wallSlideStepX = stepX;
    float wallSlideStepY = stepY;
    IndoorWallCollision wallSlideCollision = fullMoveWallCollision;

    for (int attempt = 0; attempt < 3 && wallSlideCollision.hit; ++attempt)
    {
        bx::Vec3 slideNormal = {
            wallSlideCollision.normal.x,
            wallSlideCollision.normal.y,
            0.0f
        };
        const float slideNormalLength =
            std::sqrt(slideNormal.x * slideNormal.x + slideNormal.y * slideNormal.y);

        if (slideNormalLength > 0.0001f)
        {
            slideNormal.x /= slideNormalLength;
            slideNormal.y /= slideNormalLength;
            const float stepIntoNormal = wallSlideStepX * slideNormal.x + wallSlideStepY * slideNormal.y;
            wallSlideStepX -= slideNormal.x * stepIntoNormal;
            wallSlideStepY -= slideNormal.y * stepIntoNormal;

            if (pDebugInfo != nullptr)
            {
                pDebugInfo->wallSlideTried = true;
            }

            if (wallSlideStepX * wallSlideStepX + wallSlideStepY * wallSlideStepY <= 0.0001f)
            {
                break;
            }

            bool slideBlockedByActor = false;
            wallSlideCollision = {};

            if (tryResolvePosition(
                    state.x + wallSlideStepX,
                    state.y + wallSlideStepY,
                    resolved,
                    &slideBlockedByActor,
                    &wallSlideCollision))
            {
                if (pDebugInfo != nullptr)
                {
                    pDebugInfo->wallSlideSucceeded = true;
                }

                return resolved;
            }

            if (blockActorSlide && slideBlockedByActor)
            {
                return state;
            }
        }
    }

    const float slideX = state.x + stepX * SlideFactor;
    const float slideY = state.y + stepY * SlideFactor;

    if (std::fabs(stepX) >= std::fabs(stepY))
    {
        if (tryResolvePosition(slideX, state.y, resolved, nullptr, nullptr))
        {
            if (pDebugInfo != nullptr)
            {
                pDebugInfo->axisSlideSucceeded = true;
            }

            return resolved;
        }

        if (tryResolvePosition(state.x, slideY, resolved, nullptr, nullptr))
        {
            if (pDebugInfo != nullptr)
            {
                pDebugInfo->axisSlideSucceeded = true;
            }

            return resolved;
        }
    }
    else
    {
        if (tryResolvePosition(state.x, slideY, resolved, nullptr, nullptr))
        {
            if (pDebugInfo != nullptr)
            {
                pDebugInfo->axisSlideSucceeded = true;
            }

            return resolved;
        }

        if (tryResolvePosition(slideX, state.y, resolved, nullptr, nullptr))
        {
            if (pDebugInfo != nullptr)
            {
                pDebugInfo->axisSlideSucceeded = true;
            }

            return resolved;
        }
    }

    return state;
}

std::vector<uint8_t> IndoorMovementController::buildNonBlockingMechanismFaceMask() const
{
    std::vector<uint8_t> result;

    if (m_pIndoorMapData == nullptr)
    {
        return result;
    }

    result.assign(m_pIndoorMapData->faces.size(), 0);

    if (m_pMapDeltaData == nullptr || !m_pMapDeltaData->has_value())
    {
        return result;
    }

    for (const MapDeltaDoor &door : (*m_pMapDeltaData)->doors)
    {
        if (resolveDoorDistance(door, m_pEventRuntimeState) > 1.0f)
        {
            continue;
        }

        for (uint16_t faceId : door.faceIds)
        {
            if (faceId < result.size() && doorFaceUsesMovedVertex(*m_pIndoorMapData, door, faceId))
            {
                result[faceId] = 1;
            }
        }
    }

    return result;
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
    float movementX,
    float movementY,
    IndoorWallCollision *pWallCollision
) const
{
    if (m_pIndoorMapData == nullptr)
    {
        return false;
    }

    const std::vector<int16_t> collisionSectorIds = collectCollisionSectorIds(
        vertices,
        geometryCache,
        x,
        y,
        footZ,
        body,
        primarySectorId,
        secondarySectorId);
    const auto sectorIsRelevant = [&collisionSectorIds](uint16_t sectorId) -> bool
    {
        return std::find(collisionSectorIds.begin(), collisionSectorIds.end(), static_cast<int16_t>(sectorId))
            != collisionSectorIds.end();
    };
    IndoorWallCollision bestWallCollision = {};
    float bestWallScore = -1.0f;
    const float movementLength = std::sqrt(movementX * movementX + movementY * movementY);

    for (size_t faceIndex = 0; faceIndex < m_pIndoorMapData->faces.size(); ++faceIndex)
    {
        if (pCollisionFaceMask != nullptr
            && !pCollisionFaceMask->empty()
            && (faceIndex >= pCollisionFaceMask->size() || (*pCollisionFaceMask)[faceIndex] == 0))
        {
            continue;
        }

        if (pMechanismBlockingFaceMask != nullptr
            && faceIndex < pMechanismBlockingFaceMask->size()
            && (*pMechanismBlockingFaceMask)[faceIndex] == 0)
        {
            continue;
        }

        const IndoorFaceGeometryData *pGeometry = geometryCache.geometryForFace(
            *m_pIndoorMapData,
            vertices,
            faceIndex);

        if (pGeometry == nullptr
            || (!collisionSectorIds.empty()
                && !sectorIsRelevant(pGeometry->sectorId)
                && !sectorIsRelevant(pGeometry->backSectorId))
            || pGeometry->kind != IndoorFaceKind::Wall
            || pGeometry->isPortal
            || hasFaceAttribute(pGeometry->attributes, FaceAttribute::Untouchable)
            || pGeometry->maxZ <= footZ + MaximumRise
            || !isIndoorCylinderBlockedByFace(*pGeometry, x, y, footZ, body.radius, body.height))
        {
            continue;
        }

        if (pWallCollision == nullptr)
        {
            return true;
        }

        bx::Vec3 wallNormal = {
            pGeometry->normal.x,
            pGeometry->normal.y,
            0.0f
        };
        const float wallNormalLength = std::sqrt(wallNormal.x * wallNormal.x + wallNormal.y * wallNormal.y);
        float score = 1.0f;

        if (movementLength > 0.0001f && wallNormalLength > 0.0001f)
        {
            wallNormal.x /= wallNormalLength;
            wallNormal.y /= wallNormalLength;
            score = std::abs(movementX * wallNormal.x + movementY * wallNormal.y) / movementLength;
        }

        if (!bestWallCollision.hit || score > bestWallScore)
        {
            bestWallCollision.hit = true;
            bestWallCollision.normal = pGeometry->normal;
            bestWallCollision.faceIndex = faceIndex;
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

std::vector<int16_t> IndoorMovementController::collectCollisionSectorIds(
    const std::vector<IndoorVertex> &vertices,
    IndoorFaceGeometryCache &geometryCache,
    float x,
    float y,
    float footZ,
    const IndoorBodyDimensions &body,
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
    const auto portalIntersectsBody = [&](const IndoorFaceGeometryData &geometry) -> bool
    {
        return x + body.radius >= geometry.minX
            && x - body.radius <= geometry.maxX
            && y + body.radius >= geometry.minY
            && y - body.radius <= geometry.maxY
            && footZ + body.height >= geometry.minZ
            && footZ <= geometry.maxZ;
    };
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

            if (pGeometry == nullptr || !portalIntersectsBody(*pGeometry))
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

bool IndoorMovementController::collidesWithActors(
    float currentX,
    float currentY,
    float candidateX,
    float candidateY,
    float footZ,
    const IndoorBodyDimensions &body,
    std::vector<size_t> *pContactedActorIndices,
    std::optional<size_t> ignoredActorIndex,
    bool *pHitActor
) const
{
    const float bodyMinZ = footZ;
    const float bodyMaxZ = footZ + body.height;

    for (const IndoorActorCollision &collider : m_actorColliders)
    {
        if (ignoredActorIndex.has_value() && collider.actorIndex == *ignoredActorIndex)
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

        if (candidateDistanceSquared > currentDistanceSquared + 1.0f)
        {
            continue;
        }

        if (pContactedActorIndices != nullptr && collider.reportActorContact)
        {
            pContactedActorIndices->push_back(collider.actorIndex);
        }

        if (pHitActor != nullptr)
        {
            *pHitActor = true;
        }

        return true;
    }

    return false;
}

std::vector<uint8_t> IndoorMovementController::buildMechanismBlockingFaceMask() const
{
    std::vector<uint8_t> result;

    if (m_pIndoorMapData == nullptr)
    {
        return result;
    }

    result.assign(m_pIndoorMapData->faces.size(), 1);

    if (m_pMapDeltaData == nullptr || !m_pMapDeltaData->has_value())
    {
        return result;
    }

    for (const MapDeltaDoor &door : (*m_pMapDeltaData)->doors)
    {
        const uint8_t blocksMovement = resolveDoorDistance(door, m_pEventRuntimeState) > 1.0f ? 1 : 0;

        for (uint16_t faceId : door.faceIds)
        {
            if (faceId < result.size() && doorFaceUsesMovedVertex(*m_pIndoorMapData, door, faceId))
            {
                result[faceId] = blocksMovement;
            }
        }
    }

    return result;
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
