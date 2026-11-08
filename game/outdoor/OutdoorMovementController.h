#pragma once

#include "game/outdoor/OutdoorCollisionData.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/tables/MapStats.h"

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <optional>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// Sweeps a sphere from position along a unit direction by up to currentMoveDistance against an outdoor face (its plane,
// then its edges and corners). On contact, moveDistance is the distance to it and collisionPoint the contact. A
// one-sided face only stops a sphere moving against its normal.
bool collideSphereWithFace(
    const OutdoorFaceGeometryData &geometry,
    const bx::Vec3 &position,
    float radius,
    const bx::Vec3 &direction,
    float currentMoveDistance,
    bool doubleSidedFace,
    float &moveDistance,
    bx::Vec3 &collisionPoint
);

enum class OutdoorSupportKind
{
    None,
    Terrain,
    BModelFace,
};

struct OutdoorMoveState
{
    float x = 0.0f;
    float y = 0.0f;
    float footZ = 0.0f;
    float verticalVelocity = 0.0f;
    OutdoorSupportKind supportKind = OutdoorSupportKind::None;
    size_t supportBModelIndex = 0;
    size_t supportFaceIndex = 0;
    bool supportIsFluid = false;
    bool supportOnWater = false;
    bool supportOnBurning = false;
    bool airborne = false;
    bool landedThisFrame = false;
    float fallStartZ = 0.0f;
    float fallDistance = 0.0f;

    // Deep water that drowns the party and stops its jumps: water terrain only. Fluid BModel floors (fountains,
    // pools before dungeon entrances) are shallow: they splash but never drown, as in the original games.
    bool supportOnDeepWater() const
    {
        return supportOnWater && supportKind == OutdoorSupportKind::Terrain;
    }
};

struct OutdoorBodyDimensions
{
    float radius = 37.0f;
    float height = 192.0f;
    float maxStepHeight = 128.0f;
};

struct OutdoorMoveFloorDebugInfo
{
    bool hasFloor = false;
    float height = 0.0f;
    float normalZ = 1.0f;
    bool fromBModel = false;
    bool isFluid = false;
    size_t bModelIndex = 0;
    size_t faceIndex = 0;
};

struct OutdoorMoveDebugInfo
{
    float startX = 0.0f;
    float startY = 0.0f;
    float startZ = 0.0f;
    float endX = 0.0f;
    float endY = 0.0f;
    float endZ = 0.0f;
    float requestedVelocityX = 0.0f;
    float requestedVelocityY = 0.0f;
    float requestedVelocityZ = 0.0f;
    float inputVelocityZBeforeCollision = 0.0f;
    float outputVelocityZ = 0.0f;
    bool flyingActive = false;
    bool jumpRequested = false;
    bool flyUpRequested = false;
    bool flyDownRequested = false;
    bool wasAirborne = false;
    bool partyNotTouchingFloor = false;
    bool partyCloseToGround = false;
    bool partyOnSteepBModel = false;
    bool slopeSlideActive = false;
    bool horizontalPassRaisedZ = false;
    bool verticalPassRan = false;
    float horizontalPassStartZ = 0.0f;
    float horizontalPassEndZ = 0.0f;
    float verticalPassStartZ = 0.0f;
    float verticalPassEndZ = 0.0f;
    int collisionAttempts = 0;
    int lastCollisionPass = 0;
    int lastHitKind = 0;
    size_t lastHitBModelIndex = 0;
    size_t lastHitFaceIndex = 0;
    size_t lastHitColliderIndex = 0;
    uint8_t lastHitPolygonType = 0;
    float lastHitFloorHeight = 0.0f;
    float lastHitMoveDistance = 0.0f;
    float lastHitAdjustedMoveDistance = 0.0f;
    float lastHitHeightOffset = 0.0f;
    bx::Vec3 lastHitPoint = {0.0f, 0.0f, 0.0f};
    bx::Vec3 lastHitNormal = {0.0f, 0.0f, 0.0f};
    bx::Vec3 lastPassStart = {0.0f, 0.0f, 0.0f};
    bx::Vec3 lastPassInputVelocity = {0.0f, 0.0f, 0.0f};
    bx::Vec3 lastPassNewLow = {0.0f, 0.0f, 0.0f};
    bx::Vec3 lastPassOutputVelocity = {0.0f, 0.0f, 0.0f};
    OutdoorMoveFloorDebugInfo currentFloor = {};
    OutdoorMoveFloorDebugInfo lastAllNewFloor = {};
    OutdoorMoveFloorDebugInfo lastXAdvanceFloor = {};
    OutdoorMoveFloorDebugInfo lastYAdvanceFloor = {};
    OutdoorMoveFloorDebugInfo steppedBModelFloor = {};
    OutdoorMoveFloorDebugInfo finalFloor = {};
};

struct OutdoorIgnoredActorCollider
{
    OutdoorActorCollisionSource source = OutdoorActorCollisionSource::MapDelta;
    size_t sourceIndex = 0;
};

class OutdoorMovementController
{
public:
    OutdoorMovementController(
        const OutdoorMapData &outdoorMapData,
        const std::optional<std::vector<uint8_t>> &outdoorLandMask,
        const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
        const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
        const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet
    );
    OutdoorMovementController(
        const OutdoorMapData &outdoorMapData,
        const std::optional<MapBounds> &mapBounds,
        const std::optional<std::vector<uint8_t>> &outdoorLandMask,
        const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
        const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
        const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet
    );

    OutdoorMoveState initializeState(float x, float y, float footZHint) const;
    OutdoorMoveState initializeStateForBody(
        float x,
        float y,
        float footZHint,
        float bodyRadius) const;
    // The party placed at a point (a map arrival, a teleport): a model floor up to stepUp above the feet, which the
    // body would otherwise stand inside, holds it, as the stairs under the Castle of Air's door do (OY-392).
    OutdoorMoveState initializePartyArrivalState(
        float x,
        float y,
        float footZHint,
        float bodyRadius,
        float stepUp,
        bool keepHeight = false) const;
    OutdoorMoveState initializeActorStateForBody(
        float x,
        float y,
        float footZHint,
        float bodyRadius) const;
    OutdoorMoveState initializeActorStateForBodyPreservingZ(
        float x,
        float y,
        float footZHint,
        float bodyRadius) const;
    OutdoorMoveState resolveMove(
        const OutdoorMoveState &state,
        float desiredVelocityX,
        float desiredVelocityY,
        float desiredVelocityZ,
        bool jumpRequested,
        bool flyUpRequested,
        bool flyDownRequested,
        bool flyingActive,
        bool waterWalkActive,
        float jumpVelocity,
        float flyVerticalSpeed,
        float maxFlightHeight,
        float deltaSeconds,
        std::vector<size_t> *pContactedActorIndices = nullptr,
        float jumpLift = 1.0f,
        OutdoorMoveDebugInfo *pDebugInfo = nullptr
    ) const;
    OutdoorMoveState resolveMoveForBody(
        const OutdoorMoveState &state,
        const OutdoorBodyDimensions &body,
        float desiredVelocityX,
        float desiredVelocityY,
        float desiredVelocityZ,
        bool jumpRequested,
        bool flyUpRequested,
        bool flyDownRequested,
        bool flyingActive,
        bool waterWalkActive,
        float jumpVelocity,
        float flyVerticalSpeed,
        float maxFlightHeight,
        float deltaSeconds,
        std::vector<size_t> *pContactedActorIndices = nullptr,
        const std::optional<OutdoorIgnoredActorCollider> &ignoredActorCollider = std::nullopt,
        float jumpLift = 1.0f,
        OutdoorMoveDebugInfo *pDebugInfo = nullptr
    ) const;
    OutdoorMoveState resolveOutdoorActorMove(
        const OutdoorMoveState &state,
        const OutdoorBodyDimensions &body,
        float desiredVelocityX,
        float desiredVelocityY,
        float verticalVelocity,
        bool flyingActive,
        float deltaSeconds,
        std::vector<size_t> *pContactedActorIndices = nullptr,
        const std::optional<OutdoorIgnoredActorCollider> &ignoredActorCollider = std::nullopt,
        bx::Vec3 *pResolvedVelocity = nullptr,
        bool *pResolvedVelocityUpdatesYaw = nullptr
    ) const;
    std::optional<MapBoundaryEdge> detectBoundaryBlock(
        const OutdoorMoveState &previousState,
        const OutdoorMoveState &currentState,
        float desiredVelocityX,
        float desiredVelocityY) const;
    bool hasNonFluidBModelActorSupport(
        const OutdoorMoveState &state,
        float bodyRadius,
        float x,
        float y,
        float z,
        float maxFloorRise) const;
    void setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders);
    // Per map entity: decorations that are hidden now (hiddenDecorationEntities) and so do not collide.
    void setHiddenDecorationEntities(const std::vector<bool> &hiddenEntities);
    void setFaceAttributes(size_t bModelIndex, size_t faceIndex, uint32_t attributes);
    void updateFaceGeometries(const std::vector<OutdoorFaceGeometryData> &geometries);

private:
    const OutdoorMapData *m_pOutdoorMapData;
    std::optional<std::vector<uint8_t>> m_outdoorLandMask;
    std::vector<OutdoorFaceGeometryData> m_faces;
    std::vector<std::vector<size_t>> m_faceGridCells;
    std::unordered_map<uint64_t, size_t> m_faceIndexById;
    mutable std::vector<uint32_t> m_faceGridVisitMarks;
    mutable uint32_t m_faceGridVisitGeneration = 1;
    float m_faceGridMinX = 0.0f;
    float m_faceGridMinY = 0.0f;
    size_t m_faceGridWidth = 0;
    size_t m_faceGridHeight = 0;
    std::vector<OutdoorDecorationCollision> m_decorationColliders;
    std::vector<bool> m_hiddenDecorationEntities;
    std::vector<OutdoorActorCollision> m_actorColliders;
    std::vector<OutdoorSpriteObjectCollision> m_spriteObjectColliders;
    std::vector<std::vector<size_t>> m_spriteObjectGridCells;
    float m_spriteObjectGridMinX = 0.0f;
    float m_spriteObjectGridMinY = 0.0f;
    size_t m_spriteObjectGridWidth = 0;
    size_t m_spriteObjectGridHeight = 0;
    std::optional<MapBounds> m_mapBounds;

    OutdoorMoveState initializeStateForBody(
        float x,
        float y,
        float footZHint,
        float bodyRadius,
        bool actorConditionalBModelSupport,
        bool preserveFootZ,
        float arrivalStepUp = 0.0f) const;
    void buildFaceCache();
    void buildFaceSpatialIndex();
    void buildDecorationColliderCache(const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet);
    void buildActorColliderCache(const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet);
    void buildSpriteObjectColliderCache(const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectSet);
    void clampPositionToBounds(float bodyRadius, float &x, float &y) const;
    void collectFaceCandidates(float minX, float minY, float maxX, float maxY, std::vector<size_t> &faceIndices) const;
    void collectSpriteObjectCandidates(float minX, float minY, float maxX, float maxY, std::vector<size_t> &indices) const;
    const OutdoorFaceGeometryData *findFaceGeometry(size_t bModelIndex, size_t faceIndex) const;
};
}
