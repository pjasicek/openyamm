#pragma once

#include "game/OutdoorGeometryUtils.h"
#include "game/OutdoorMapData.h"

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorMoveState
{
    float x = 0.0f;
    float y = 0.0f;
    float footZ = 0.0f;
    float verticalVelocity = 0.0f;
};

class OutdoorMovementController
{
public:
    explicit OutdoorMovementController(const OutdoorMapData &outdoorMapData);

    OutdoorMoveState initializeState(float x, float y, float footZHint) const;
    OutdoorMoveState resolveMove(
        const OutdoorMoveState &state,
        float desiredVelocityX,
        float desiredVelocityY,
        float deltaSeconds
    ) const;

private:
    const OutdoorMapData *m_pOutdoorMapData;
    std::vector<OutdoorFaceGeometryData> m_faces;

    void buildFaceCache();
};
}
