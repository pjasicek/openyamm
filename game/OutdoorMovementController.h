#pragma once

#include "game/OutdoorCollisionData.h"
#include "game/OutdoorGeometryUtils.h"
#include "game/OutdoorMapData.h"

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <optional>
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

    OutdoorMoveState initializeState(float x, float y, float footZHint) const;
    OutdoorMoveState resolveMove(
        const OutdoorMoveState &state,
        float desiredVelocityX,
        float desiredVelocityY,
        bool jumpRequested,
        bool flyDownRequested,
        bool flyingActive,
        float jumpVelocity,
        float flyVerticalSpeed,
        float deltaSeconds,
        std::vector<size_t> *pContactedActorIndices = nullptr
    ) const;
    void setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders);

private:
    const OutdoorMapData *m_pOutdoorMapData;
    std::optional<std::vector<uint8_t>> m_outdoorLandMask;
    std::vector<OutdoorFaceGeometryData> m_faces;
    std::vector<OutdoorDecorationCollision> m_decorationColliders;
    std::vector<OutdoorActorCollision> m_actorColliders;
    std::vector<OutdoorSpriteObjectCollision> m_spriteObjectColliders;

    void buildFaceCache();
    void buildDecorationColliderCache(const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet);
    void buildActorColliderCache(const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet);
    void buildSpriteObjectColliderCache(const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectSet);
};
}
