#pragma once

#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorSectorFaceGrid.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
inline constexpr float IndoorActorMaxDropHeight = 100.0f;
// A path planner's drop for monsters that follow down ledges of any height (scene `actor_movement: {drops: follow}`).
inline constexpr float IndoorActorFollowDropHeight = 65536.0f;
// The gravity resolveMove applies by default (monsters; the party passes its own).
inline constexpr float IndoorActorGravityPerSecond = 960.0f;

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
    bool landedThisFrame = false;
    float fallStartZ = 0.0f;
    float fallDistance = 0.0f;
    // Runtime only: movement steps an airborne body that found no recovery position waits before searching again.
    uint8_t stuckRecoveryCooldownSteps = 0;

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
    int16_t sectorId = -1;
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
    int16_t sectorId = -1;
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

enum class IndoorMoveInvalidPositionReason
{
    None,
    ActorLedgeDrop,
    LeadingActorLedgeDrop,
    SteepFloor,
    StepUpTooHigh,
    CeilingFloorCrush,
    MissingEyeSector,
    FaceCollision,
    ActorCollision,
    UnsupportedStepUp
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
    IndoorMoveInvalidPositionReason invalidPositionReason = IndoorMoveInvalidPositionReason::None;
    bx::Vec3 invalidCandidatePosition = {0.0f, 0.0f, 0.0f};
    bool invalidFloorHas = false;
    size_t invalidFloorFaceIndex = static_cast<size_t>(-1);
    int16_t invalidFloorSectorId = -1;
    float invalidFloorHeight = 0.0f;
    float invalidFloorNormalZ = 0.0f;
    bool invalidLeadingFloorHas = false;
    size_t invalidLeadingFloorFaceIndex = static_cast<size_t>(-1);
    int16_t invalidLeadingFloorSectorId = -1;
    float invalidLeadingFloorHeight = 0.0f;
    float invalidLeadingFloorNormalZ = 0.0f;
    bool invalidCeilingHas = false;
    float invalidCeilingHeight = 0.0f;
    int16_t invalidEyeSectorId = -1;
};

struct IndoorCollisionTraceInfo
{
    bool crossedBlockingFace = false;
    size_t blockingFaceIndex = static_cast<size_t>(-1);
    bx::Vec3 blockingFaceNormal = {0.0f, 0.0f, 0.0f};
    bx::Vec3 blockingFacePoint = {0.0f, 0.0f, 0.0f};
    float blockingFaceMoveDistance = 0.0f;
    float blockingFaceAdjustedMoveDistance = 0.0f;
    bool sectorChanged = false;
    bool sectorTransitionTouchedPortal = false;
    size_t portalFaceIndex = static_cast<size_t>(-1);
    bool supportLost = false;
    bool suddenDrop = false;
};

// The original MM8 party movement (0x472e86) has no steepness test on indoor faces: an in-between (type 4) slope of
// any angle answers a push with its normal and is climbed. Actors (0x46fb6d) keep the steep-floor slide.
enum class IndoorSlopeRule : uint8_t
{
    Actor,
    Party
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
    // A body held in the air at a point (a ladder taken at its top): its rooms there, or none when the point is outside
    // the map or the body would stand in a face.
    std::optional<IndoorMoveState> airborneStateAt(
        float x,
        float y,
        float footZ,
        const IndoorBodyDimensions &body
    ) const;
    // Whether a floor lies under the point (x, y) from maxRise above z to maxDrop below it: the point alone, no footprint.
    bool hasFloorAt(float x, float y, float z, float maxRise, float maxDrop) const;
    const IndoorMapData *indoorMapData() const
    {
        return m_pIndoorMapData;
    }
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
        IndoorMoveDebugInfo *pDebugInfo = nullptr,
        bool flyingActive = false,
        bool ignoreActorCollisions = false,
        float jumpVelocity = 480.0f,
        float jumpLift = 0.0f,
        bool lockVerticalPosition = false,
        bool preventGroundActorLedgeDrop = false,
        bool allowUnsupportedPathRecovery = false,
        bool allowBlockedWallRecovery = false,
        bool requireWalkableSupport = false,
        float gravityPerSecond = IndoorActorGravityPerSecond
    ) const;
    IndoorMoveState resolveFlyingActorMove(
        const IndoorMoveState &state,
        const IndoorBodyDimensions &body,
        float desiredVelocityX,
        float desiredVelocityY,
        float deltaSeconds,
        std::vector<size_t> *pContactedActorIndices = nullptr,
        std::optional<size_t> ignoredActorIndex = std::nullopt,
        bool blockActorSlide = false,
        IndoorMoveDebugInfo *pHorizontalDebugInfo = nullptr,
        IndoorMoveDebugInfo *pVerticalDebugInfo = nullptr,
        bool ignoreActorCollisions = false
    ) const;
    IndoorCollisionTraceInfo traceCollisionIssues(
        const IndoorMoveState &start,
        const IndoorMoveState &end,
        const IndoorBodyDimensions &body
    ) const;
    std::string buildCollisionTraceProbeDetails(
        const IndoorMoveState &start,
        const IndoorMoveState &end,
        const IndoorBodyDimensions &body
    ) const;
    void setSlopeRule(IndoorSlopeRule slopeRule);
    // The monsters' controller: the scene's monster-only walls (IndoorMapData::actorBarrierFaceIds) block its moves.
    void setBlockedByActorBarriers(bool blocked);
    void setActorColliders(const std::vector<IndoorActorCollision> &actorColliders);
    void updateActorColliderPosition(size_t actorIndex, int16_t sectorId, float x, float y, float z);
    void setDecorationColliders(const std::vector<IndoorCylinderCollision> &decorationColliders);
    void setSpriteObjectColliders(const std::vector<IndoorCylinderCollision> &spriteObjectColliders);
    void invalidateRuntimeGeometryCache();
    void applyMechanismGeometryUpdate(const std::vector<uint32_t> &changedDoorIds);
    bool supportFaceIsBurning(size_t faceIndex) const;
    // The map's vertices with the doors where they stand now (water volumes bound to a mover follow them).
    const std::vector<IndoorVertex> &runtimeVertices() const
    {
        return runtimeGeometryCache().vertices;
    }
    IndoorMoveState resolveGroundedSupportState(
        const IndoorMoveState &state,
        const IndoorBodyDimensions &body
    ) const;

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
    IndoorFloorSample sampleCurrentSupportFloor(
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
        std::vector<IndoorVertex> vertices;
        std::vector<uint8_t> nonBlockingMechanismFaceMask;
        std::vector<uint8_t> mechanismBlockingFaceMask;
        std::vector<uint8_t> actorSupportFaceMask;
        std::vector<uint8_t> collisionFaceMask;
        // The scene's monster-only walls, for a controller blocked by them; empty otherwise.
        std::vector<uint8_t> actorBarrierFaceMask;
        std::vector<uint16_t> mechanismSupportFaceIds;
        std::vector<std::vector<uint16_t>> sectorMechanismSupportFaceIds;
        std::vector<uint16_t> invisibleSupportRampFaceIds;
        IndoorFaceGeometryCache geometryCache;
        // Narrows floor queries to the faces near a point (attached to geometryCache by refreshRuntimeGeometryCache):
        // a region's open air is one sector of 25 000 floors (devdocs/mm9_rework/BLV_GEOMETRY_COSTS.md, E2).
        IndoorSectorFaceGrid sectorFaceGrid;
        // Each face's place in its sectors' floor, wall and ceiling lists (sector, position): the grid's candidates
        // are taken in the order the sector lists give, so ties between equally near faces go the same way.
        std::vector<std::vector<std::pair<int16_t, uint32_t>>> faceSectorListRanks;
        // Kept when the cache is invalidated: the grid until the door layout changes, the ranks for good.
        bool sectorFaceGridBuilt = false;
        uint64_t sectorFaceGridDoorSignature = 0;
        bool faceSectorListRanksBuilt = false;
        uint64_t surfaceRevision = 0;
        // Every face's attributes the masks and support lists were built with (the delta's, else the map's).
        std::vector<uint32_t> faceAttributes;
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
        bool allowUnsupportedPathRecovery = false;
        bool allowBlockedWallRecovery = false;
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
    // Face bits changed and no face moved: the masks and support lists redo the changed faces alone.
    void refreshChangedFaceAttributes(const MapDeltaData &mapDeltaData) const;
    void rebuildMechanismSupportFaceIds(const MapDeltaData &mapDeltaData) const;
    bool faceIsCachedInvisibleSupportRamp(size_t faceId, const MapDeltaData *pMapDeltaData) const;
    bool faceExcludedFromActorSupport(size_t faceId) const;
    uint32_t effectiveFaceAttributes(size_t faceId, const MapDeltaData *pMapDeltaData) const;
    const RuntimeGeometryCache &runtimeGeometryCache() const;
    // A grounded body that stands still or heads onto a flat tread its footprint overlaps keeps standing on it.
    IndoorMoveState holdFootprintSupport(
        const IndoorMoveState &start,
        const IndoorMoveState &resolved,
        const IndoorBodyDimensions &body,
        bool requireWalkableSupport
    ) const;
    const IndoorMapData *m_pIndoorMapData = nullptr;
    const std::optional<MapDeltaData> *m_pMapDeltaData = nullptr;
    const std::optional<EventRuntimeState> *m_pEventRuntimeState = nullptr;
    mutable RuntimeGeometryCache m_runtimeGeometryCache;

    std::vector<uint8_t> buildCollisionFaceMask() const;
    // The runtime cache's monster-only wall mask, or null when this controller has none.
    const std::vector<uint8_t> *actorBarrierFaceMask() const;
    SweptCollisionRequest buildSweptCollisionRequest(
        const IndoorMoveState &state,
        const IndoorBodyDimensions &body,
        float desiredVelocityX,
        float desiredVelocityY,
        bool jumpRequested,
        float deltaSeconds,
        std::optional<size_t> ignoredActorIndex,
        bool blockActorSlide,
        bool allowUnsupportedPathRecovery,
        bool allowBlockedWallRecovery
    ) const;
    SweptCollisionBody buildSweptCollisionBody(
        const IndoorMoveState &state,
        const IndoorBodyDimensions &body
    ) const;
    SweptCollisionState buildSweptCollisionState(const SweptCollisionRequest &request) const;
    IndoorMoveState resolveMoveSingleStep(
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
        bool preventGroundActorLedgeDrop,
        bool allowUnsupportedPathRecovery,
        bool allowBlockedWallRecovery,
        bool requireWalkableSupport,
        float gravityPerSecond
    ) const;
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
        size_t ignoredSupportFaceIndex,
        size_t ignoredOverlapFaceIndex,
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
        bool ignoreActorCollisions,
        bool *pHitActor
    ) const;
    IndoorSlopeRule m_slopeRule = IndoorSlopeRule::Actor;
    bool m_blockedByActorBarriers = false;
    std::vector<IndoorActorCollision> m_actorColliders;
    std::vector<IndoorCylinderCollision> m_decorationColliders;
    std::vector<IndoorCylinderCollision> m_spriteObjectColliders;
    mutable std::vector<uint32_t> m_candidateFaceVisitStamps;
    mutable uint32_t m_candidateFaceVisitStamp = 1;
};
}
