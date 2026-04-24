#pragma once

#include "game/indoor/IndoorGeometryUtils.h"

#include <cstddef>
#include <cstdint>
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

struct IndoorCylinderCollision
{
    size_t sourceIndex = 0;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float radius = 0.0f;
    float height = 0.0f;
};

enum class IndoorMoveBlockKind
{
    None,
    Wall,
    Actor,
    Party,
    InvalidPosition
};

struct IndoorMoveDebugInfo
{
    bool wantedHorizontalMove = false;
    bool fullMoveSucceeded = false;
    bool collisionResponseTried = false;
    bool collisionResponseSucceeded = false;
    IndoorMoveBlockKind primaryBlockKind = IndoorMoveBlockKind::None;
    size_t hitFaceIndex = static_cast<size_t>(-1);
    bx::Vec3 hitNormal = {0.0f, 0.0f, 0.0f};
    bx::Vec3 hitPoint = {0.0f, 0.0f, 0.0f};
    bx::Vec3 responseStep = {0.0f, 0.0f, 0.0f};
    float hitMoveDistance = 0.0f;
    float hitAdjustedMoveDistance = 0.0f;
    float hitHeightOffset = 0.0f;
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
    void updateActorColliderPosition(size_t actorIndex, float x, float y, float z);
    void setDecorationColliders(const std::vector<IndoorCylinderCollision> &decorationColliders);
    void setSpriteObjectColliders(const std::vector<IndoorCylinderCollision> &spriteObjectColliders);

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
    enum class SweptCollisionHitType : uint8_t
    {
        None,
        Face,
        Portal,
        Floor,
        Ceiling,
        Actor,
        Party,
        Decoration,
        SpriteObject,
        InvalidPosition
    };
    struct SweptCollisionSphere
    {
        bx::Vec3 center = {0.0f, 0.0f, 0.0f};
        float radius = 0.0f;
        float heightOffset = 0.0f;
    };
    struct SweptCollisionBody
    {
        SweptCollisionSphere lowSphere;
        SweptCollisionSphere highSphere;
        float radius = 0.0f;
        float height = 0.0f;
    };
    struct SweptCollisionRequest
    {
        IndoorMoveState startState = {};
        IndoorBodyDimensions body = {};
        bx::Vec3 velocity = {0.0f, 0.0f, 0.0f};
        float deltaSeconds = 0.0f;
        bool jumpRequested = false;
        bool blockActorSlide = false;
        std::optional<size_t> ignoredActorIndex = std::nullopt;
    };
    struct SweptCollisionState
    {
        bx::Vec3 position = {0.0f, 0.0f, 0.0f};
        bx::Vec3 velocity = {0.0f, 0.0f, 0.0f};
        bx::Vec3 direction = {0.0f, 0.0f, 0.0f};
        float moveDistance = 0.0f;
        float adjustedMoveDistance = 0.0f;
        SweptCollisionBody body;
        int16_t sectorId = -1;
        int16_t eyeSectorId = -1;
        size_t supportFaceIndex = static_cast<size_t>(-1);
        bool grounded = false;
    };
    struct SweptCollisionHit
    {
        SweptCollisionHitType type = SweptCollisionHitType::None;
        bool boundaryHit = false;
        size_t faceIndex = static_cast<size_t>(-1);
        size_t colliderIndex = static_cast<size_t>(-1);
        size_t actorIndex = static_cast<size_t>(-1);
        bx::Vec3 point = {0.0f, 0.0f, 0.0f};
        bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
        float heightOffset = 0.0f;
        float moveDistance = 0.0f;
        float adjustedMoveDistance = 0.0f;
        int16_t sectorId = -1;
        int16_t targetSectorId = -1;
    };
    struct SweptCollisionResult
    {
        IndoorMoveState finalState = {};
        SweptCollisionHit primaryHit;
        std::vector<size_t> contactedActorIndices;
        bool movementBlocked = false;
        bool sectorChanged = false;
    };

    void refreshRuntimeGeometryCache() const;
    const RuntimeGeometryCache &runtimeGeometryCache() const;
    const IndoorMapData *m_pIndoorMapData = nullptr;
    const std::optional<MapDeltaData> *m_pMapDeltaData = nullptr;
    const std::optional<EventRuntimeState> *m_pEventRuntimeState = nullptr;
    mutable RuntimeGeometryCache m_runtimeGeometryCache;

    std::vector<uint8_t> buildCollisionFaceMask() const;
    SweptCollisionRequest buildSweptCollisionRequest(
        const IndoorMoveState &state,
        const IndoorBodyDimensions &body,
        float desiredVelocityX,
        float desiredVelocityY,
        bool jumpRequested,
        float deltaSeconds,
        std::optional<size_t> ignoredActorIndex,
        bool blockActorSlide
    ) const;
    SweptCollisionBody buildSweptCollisionBody(
        const IndoorMoveState &state,
        const IndoorBodyDimensions &body
    ) const;
    SweptCollisionState buildSweptCollisionState(const SweptCollisionRequest &request) const;
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
    std::vector<int16_t> collectSweptCollisionSectorIds(
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
    ) const;
    std::vector<const IndoorFaceGeometryData *> collectSweptCollisionFaceCandidates(
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
    std::vector<IndoorCylinderCollision> m_decorationColliders;
    std::vector<IndoorCylinderCollision> m_spriteObjectColliders;
};
}
