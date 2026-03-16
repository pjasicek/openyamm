#pragma once

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
    struct FaceGeometry
    {
        size_t bModelIndex = 0;
        size_t faceIndex = 0;
        uint8_t polygonType = 0;
        uint32_t attributes = 0;
        bool isWalkable = false;
        bool slopeTooSteep = false;
        bool hasPlane = false;
        float minX = 0.0f;
        float maxX = 0.0f;
        float minY = 0.0f;
        float maxY = 0.0f;
        float minZ = 0.0f;
        float maxZ = 0.0f;
        bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
        std::vector<bx::Vec3> vertices;
    };

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
    std::vector<FaceGeometry> m_faces;

    void buildFaceCache();
};
}
