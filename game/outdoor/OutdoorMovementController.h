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
};

struct OutdoorBodyDimensions
{
    float radius = 37.0f;
    float height = 192.0f;
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
    OutdoorMoveState resolveMove(
        const OutdoorMoveState &state,
        float desiredVelocityX,
        float desiredVelocityY,
        bool jumpRequested,
        bool flyDownRequested,
        bool flyingActive,
        bool waterWalkActive,
        float jumpVelocity,
        float flyVerticalSpeed,
        float deltaSeconds,
        std::vector<size_t> *pContactedActorIndices = nullptr
    ) const;
    OutdoorMoveState resolveMoveForBody(
        const OutdoorMoveState &state,
        const OutdoorBodyDimensions &body,
        float desiredVelocityX,
        float desiredVelocityY,
        bool jumpRequested,
        bool flyDownRequested,
        bool flyingActive,
        bool waterWalkActive,
        float jumpVelocity,
        float flyVerticalSpeed,
        float deltaSeconds,
        std::vector<size_t> *pContactedActorIndices = nullptr,
        const std::optional<OutdoorIgnoredActorCollider> &ignoredActorCollider = std::nullopt
    ) const;
    OutdoorMoveState resolveOutdoorActorMove(
        const OutdoorMoveState &state,
        const OutdoorBodyDimensions &body,
        float desiredVelocityX,
        float desiredVelocityY,
        float verticalVelocity,
        bool flyingActive,
        float deltaSeconds,
        const std::optional<OutdoorIgnoredActorCollider> &ignoredActorCollider = std::nullopt
    ) const;
    std::optional<MapBoundaryEdge> detectBoundaryBlock(
        const OutdoorMoveState &previousState,
        const OutdoorMoveState &currentState,
        float desiredVelocityX,
        float desiredVelocityY) const;
    void setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders);

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
    std::vector<OutdoorActorCollision> m_actorColliders;
    std::vector<OutdoorSpriteObjectCollision> m_spriteObjectColliders;
    std::vector<std::vector<size_t>> m_spriteObjectGridCells;
    float m_spriteObjectGridMinX = 0.0f;
    float m_spriteObjectGridMinY = 0.0f;
    size_t m_spriteObjectGridWidth = 0;
    size_t m_spriteObjectGridHeight = 0;
    std::optional<MapBounds> m_mapBounds;

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
