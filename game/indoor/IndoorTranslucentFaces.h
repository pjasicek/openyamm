#pragma once

#include "game/indoor/IndoorMapData.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <vector>

namespace OpenYAMM::Game
{
// One translucent face's draw this frame (devdocs/INDOOR_TRANSLUCENT_FACES.md): its batch (one face per batch) and
// the squared distance from the eye to the face's centre.
struct IndoorTranslucentDraw
{
    size_t batchIndex = 0;
    float distanceSquared = 0.0f;
};

// Back to front: the farthest face first, equal distances in batch order, so the order is the same every frame.
inline void sortIndoorTranslucentDrawsBackToFront(std::vector<IndoorTranslucentDraw> &draws)
{
    std::sort(draws.begin(), draws.end(),
        [](const IndoorTranslucentDraw &left, const IndoorTranslucentDraw &right)
        {
            return left.distanceSquared != right.distanceSquared
                ? left.distanceSquared > right.distanceSquared
                : left.batchIndex < right.batchIndex;
        });
}

// Whether the eye sees the face: always for a two-sided face, else only from the side its plane normal faces (a face
// is planar, so one test decides for the whole face).
inline bool indoorTranslucentFaceVisibleFrom(
    const IndoorFaceTranslucency &translucency,
    const std::array<float, 3> &normal,
    const std::array<float, 3> &pointOnFace,
    const std::array<float, 3> &eye)
{
    if (translucency.twoSided)
    {
        return true;
    }
    float side = 0.0f;
    for (size_t axis = 0; axis < 3; ++axis)
    {
        side += normal[axis] * (eye[axis] - pointOnFace[axis]);
    }
    return side > 0.0f;
}
}
