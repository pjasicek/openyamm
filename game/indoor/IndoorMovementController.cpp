#include "game/indoor/IndoorMovementController.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorCollisionPrimitives.h"

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
constexpr float MaximumStepUpFromCurrentFootZ = 128.0f;
constexpr float SlideFactor = 0.89263916f;
constexpr float GravityPerSecond = 960.0f;
constexpr float JumpVelocity = 420.0f;
constexpr float GroundSnapSlack = 8.0f;

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

    const bool wasValid = m_runtimeGeometryCache.valid;
    const std::vector<uint32_t> previousDoorStateSignature = m_runtimeGeometryCache.doorStateSignature;
    m_runtimeGeometryCache.vertices = buildIndoorMechanismAdjustedVertices(
        *m_pIndoorMapData,
        pMapDeltaData,
        pEventRuntimeState);
    // OE updates moved mechanism vertices in-place, then floor and wall collision use that current geometry.
    // Do not add open/closed masking here: platforms, stairs, plates, and doors all need their moved faces sampled.
    m_runtimeGeometryCache.nonBlockingMechanismFaceMask.clear();
    m_runtimeGeometryCache.mechanismBlockingFaceMask.clear();

    if (!wasValid)
    {
        m_runtimeGeometryCache.collisionFaceMask = buildCollisionFaceMask();
        m_runtimeGeometryCache.geometryCache.reset(m_pIndoorMapData->faces.size());
    }
    else if (pMapDeltaData != nullptr)
    {
        const bool canCompareDoorSignatures =
            previousDoorStateSignature.size() == doorStateSignature.size()
            && previousDoorStateSignature.size() == pMapDeltaData->doors.size() * 2;

        for (size_t doorIndex = 0; doorIndex < pMapDeltaData->doors.size(); ++doorIndex)
        {
            const MapDeltaDoor &door = pMapDeltaData->doors[doorIndex];
            const size_t signatureIndex = doorIndex * 2;
            const bool doorGeometryChanged =
                !canCompareDoorSignatures
                || previousDoorStateSignature[signatureIndex] != doorStateSignature[signatureIndex]
                || previousDoorStateSignature[signatureIndex + 1] != doorStateSignature[signatureIndex + 1];

            if (!doorGeometryChanged)
            {
                continue;
            }

            for (uint16_t faceId : door.faceIds)
            {
                m_runtimeGeometryCache.geometryCache.invalidateFace(faceId);
            }
        }
    }

    m_runtimeGeometryCache.doorStateSignature = doorStateSignature;
    m_runtimeGeometryCache.valid = true;
}

const IndoorMovementController::RuntimeGeometryCache &IndoorMovementController::runtimeGeometryCache() const
{
    refreshRuntimeGeometryCache();
    return m_runtimeGeometryCache;
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
    (void)body;

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
        state.supportFaceIndex != static_cast<size_t>(-1)
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
        effectiveCurrentFloor.hasFloor && state.footZ <= effectiveCurrentFloor.height + GroundSnapSlack;
    float candidateFootZ = state.footZ;
    float candidateVerticalVelocity = state.verticalVelocity;
    bool candidateGrounded = state.grounded && supportedByCurrentFloor;
    bool fullMoveBlockedByActor = false;
    IndoorWallCollision fullMoveWallCollision = {};

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

        if (floor.hasFloor
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
                positionVerticalVelocity <= 0.0f
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
            &geometryCache,
            false);
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
                pHitActor))
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

    auto selectNearestActorBodyHit =
        [&](const IndoorMoveState &moveState, const bx::Vec3 &direction, float distance)
        -> std::optional<SweptCollisionHit>
    {
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

    const float stepZ = candidateFootZ - state.footZ;
    IndoorMoveState iterativeState = state;
    bx::Vec3 remainingStep = {stepX, stepY, stepZ};
    float iterativeVerticalVelocity = candidateVerticalVelocity;
    bool sweptFaceHit = false;
    bool sweptFailed = false;
    constexpr int MaxSweptIterations = 4;

    const auto projectStepAfterFaceHit =
        [&](
            const bx::Vec3 &step,
            const SweptCollisionHit &hit,
            const IndoorMoveState &advancedState) -> bx::Vec3
    {
        if (hit.type != SweptCollisionHitType::Face)
        {
            return projectIndoorVelocityAlongPlane(
                step,
                hit.normal,
                hit.type == SweptCollisionHitType::Floor ? 1.0f : SlideFactor);
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
            return projectIndoorVelocityAlongPlane(step, hit.normal, SlideFactor);
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
        const bx::Vec3 slideDirection =
            normalizeVec(subtractVec(projectedDestination, slidePlaneOrigin));

        if (lengthVec(slideDirection) <= 0.0001f)
        {
            return projectIndoorVelocityAlongPlane(step, hit.normal, SlideFactor);
        }

        const float projectedStepDistance = dotVec(step, slideDirection);

        if (std::fabs(projectedStepDistance) <= 0.0001f)
        {
            return {0.0f, 0.0f, 0.0f};
        }

        return scaleVec(slideDirection, projectedStepDistance * SlideFactor);
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

            return stationaryState;
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

            return iterativeState;
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

            if (pFace->kind == IndoorFaceKind::Floor && pFace->isWalkable && remainingStep.z >= -0.0001f)
            {
                continue;
            }

            if (pFace->kind == IndoorFaceKind::Wall && pFace->maxZ <= iterativeState.footZ + MaximumRise)
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
        }

        if (actorBodyHit
            && (!nearestHit || actorBodyHit->adjustedMoveDistance < nearestHit->adjustedMoveDistance))
        {
            nearestHit = actorBodyHit;
        }

        if (decorationBodyHit
            && (!nearestHit || decorationBodyHit->adjustedMoveDistance < nearestHit->adjustedMoveDistance))
        {
            nearestHit = decorationBodyHit;
        }

        if (spriteObjectBodyHit
            && (!nearestHit || spriteObjectBodyHit->adjustedMoveDistance < nearestHit->adjustedMoveDistance))
        {
            nearestHit = spriteObjectBodyHit;
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

                return targetState;
            }

            fullMoveBlockedByActor = hitActor;
            fullMoveWallCollision = wallCollision;
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

        iterativeState = advancedState;

        if (sweptRequest.blockActorSlide
            && (nearestHit->type == SweptCollisionHitType::Actor
                || nearestHit->type == SweptCollisionHitType::Party))
        {
            return iterativeState;
        }

        const float consumedDistance = std::clamp(nearestHit->moveDistance, 0.0f, remainingDistance);
        const float leftoverDistance = std::max(0.0f, remainingDistance - consumedDistance);

        if (leftoverDistance <= 0.0001f)
        {
            if (pDebugInfo != nullptr)
            {
                pDebugInfo->collisionResponseSucceeded = true;
            }

            return iterativeState;
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
            remainingStep = projectStepAfterFaceHit(leftoverStep, *nearestHit, advancedState);
        }
        else
        {
            remainingStep = projectIndoorVelocityAlongPlane(leftoverStep, nearestHit->normal, responseDamping);
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

        return iterativeState;
    }

    writePrimaryBlockDebug();
    return iterativeState;
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
        if (pGeometry == nullptr
            || pGeometry->kind != IndoorFaceKind::Wall
            || pGeometry->isPortal
            || hasFaceAttribute(pGeometry->attributes, FaceAttribute::Untouchable)
            || pGeometry->maxZ <= footZ + MaximumRise
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
    std::vector<uint16_t> sectorFaceIds;

    if (useSectorFilteredFaces)
    {
        const bool useCollisionFaceMask = pCollisionFaceMask != nullptr && !pCollisionFaceMask->empty();
        const auto appendFaceIds = [&sectorFaceIds](const std::vector<uint16_t> &faceIds)
        {
            for (uint16_t faceId : faceIds)
            {
                sectorFaceIds.push_back(faceId);
            }
        };

        for (int16_t sectorId : collisionSectorIds)
        {
            if (sectorId < 0 || static_cast<size_t>(sectorId) >= m_pIndoorMapData->sectors.size())
            {
                continue;
            }

            const IndoorSector &sector = m_pIndoorMapData->sectors[sectorId];
            appendFaceIds(sector.floorFaceIds);
            appendFaceIds(sector.wallFaceIds);
            appendFaceIds(sector.ceilingFaceIds);

            if (useCollisionFaceMask)
            {
                appendFaceIds(sector.cylinderFaceIds);
            }
        }

        candidates.reserve(sectorFaceIds.size());
    }
    else
    {
        candidates.reserve(m_pIndoorMapData->faces.size());
    }

    const auto appendCandidateFace = [&](size_t faceIndex)
    {
        if (faceIndex >= m_pIndoorMapData->faces.size())
        {
            return;
        }

        if (pCollisionFaceMask != nullptr
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
        sweepOptions.pCollisionFaceMask = pCollisionFaceMask;
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
        for (uint16_t faceId : sectorFaceIds)
        {
            appendCandidateFace(faceId);
        }
    }
    else
    {
        for (size_t faceIndex = 0; faceIndex < m_pIndoorMapData->faces.size(); ++faceIndex)
        {
            appendCandidateFace(faceIndex);
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

        if (pContactedActorIndices != nullptr
            && collider.reportActorContact
            && std::find(
                pContactedActorIndices->begin(),
                pContactedActorIndices->end(),
                collider.actorIndex) == pContactedActorIndices->end())
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
