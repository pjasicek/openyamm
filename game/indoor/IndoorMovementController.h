#pragma once

#include "game/indoor/IndoorGeometryUtils.h"

#include <cstddef>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorMoveState
{
    float x = 0.0f;
    float y = 0.0f;
    float footZ = 0.0f;
    float eyeHeight = 160.0f;
    float verticalVelocity = 0.0f;
    int16_t sectorId = -1;
    int16_t eyeSectorId = -1;
    size_t supportFaceIndex = static_cast<size_t>(-1);
    bool grounded = false;

    float eyeZ() const
    {
        return footZ + eyeHeight;
    }
};

struct IndoorBodyDimensions
{
    float radius = 37.0f;
    float height = 160.0f;
};

struct IndoorActorCollision
{
    size_t actorIndex = 0;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float radius = 0.0f;
    float height = 0.0f;
    bool reportActorContact = true;
};

enum class IndoorMoveBlockKind
{
    None,
    Wall,
    Actor,
    InvalidPosition
};

struct IndoorMoveDebugInfo
{
    bool wantedHorizontalMove = false;
    bool fullMoveSucceeded = false;
    bool wallSlideTried = false;
    bool wallSlideSucceeded = false;
    bool axisSlideSucceeded = false;
    IndoorMoveBlockKind primaryBlockKind = IndoorMoveBlockKind::None;
    size_t wallFaceIndex = static_cast<size_t>(-1);
    bx::Vec3 wallNormal = {0.0f, 0.0f, 0.0f};
    int16_t startSectorId = -1;
    int16_t startEyeSectorId = -1;
};

class IndoorMovementController
{
public:
    IndoorMovementController(
        const IndoorMapData &indoorMapData,
        const std::optional<MapDeltaData> *pMapDeltaData,
        const std::optional<EventRuntimeState> *pEventRuntimeState
    );

    IndoorMoveState initializeStateFromEyePosition(
        float x,
        float y,
        float eyeZ,
        const IndoorBodyDimensions &body
    ) const;
    IndoorMoveState resolveMove(
        const IndoorMoveState &state,
        const IndoorBodyDimensions &body,
        float desiredVelocityX,
        float desiredVelocityY,
        bool jumpRequested,
        float deltaSeconds,
        std::vector<size_t> *pContactedActorIndices = nullptr,
        std::optional<size_t> ignoredActorIndex = std::nullopt,
        bool blockActorSlide = false,
        IndoorMoveDebugInfo *pDebugInfo = nullptr
    ) const;
    void setActorColliders(const std::vector<IndoorActorCollision> &actorColliders);

private:
    IndoorFloorSample sampleSupportedFloor(
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
    ) const;
    IndoorFloorSample sampleSupportedFloorOnFace(
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
    ) const;
    IndoorFloorSample sampleApproximateSupportedFloor(
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
    ) const;
    struct RuntimeGeometryCache
    {
        bool valid = false;
        std::vector<uint32_t> doorStateSignature;
        std::vector<IndoorVertex> vertices;
        std::vector<uint8_t> nonBlockingMechanismFaceMask;
        std::vector<uint8_t> mechanismBlockingFaceMask;
        std::vector<uint8_t> collisionFaceMask;
        IndoorFaceGeometryCache geometryCache;
    };
    struct IndoorWallCollision
    {
        bool hit = false;
        bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
        size_t faceIndex = static_cast<size_t>(-1);
    };

    void refreshRuntimeGeometryCache() const;
    const RuntimeGeometryCache &runtimeGeometryCache() const;
    const std::vector<std::pair<float, float>> &supportProbeOffsets(float radius) const;
    const IndoorMapData *m_pIndoorMapData = nullptr;
    const std::optional<MapDeltaData> *m_pMapDeltaData = nullptr;
    const std::optional<EventRuntimeState> *m_pEventRuntimeState = nullptr;
    mutable RuntimeGeometryCache m_runtimeGeometryCache;
    mutable float m_cachedSupportProbeRadius = -1.0f;
    mutable std::vector<std::pair<float, float>> m_cachedSupportProbeOffsets;

    std::vector<uint8_t> buildNonBlockingMechanismFaceMask() const;
    std::vector<uint8_t> buildMechanismBlockingFaceMask() const;
    std::vector<uint8_t> buildCollisionFaceMask() const;
    bool collidesAtPosition(
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
    ) const;
    std::vector<int16_t> collectCollisionSectorIds(
        const std::vector<IndoorVertex> &vertices,
        IndoorFaceGeometryCache &geometryCache,
        float x,
        float y,
        float footZ,
        const IndoorBodyDimensions &body,
        std::optional<int16_t> primarySectorId,
        std::optional<int16_t> secondarySectorId
    ) const;
    bool collidesWithActors(
        float currentX,
        float currentY,
        float candidateX,
        float candidateY,
        float footZ,
        const IndoorBodyDimensions &body,
        std::vector<size_t> *pContactedActorIndices,
        std::optional<size_t> ignoredActorIndex,
        bool *pHitActor
    ) const;
    std::vector<IndoorActorCollision> m_actorColliders;
};
}
