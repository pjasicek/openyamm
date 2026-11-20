#include "game/fx/TalkPortraitFrame.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
// A talk portrait's framing, in head heights: half its width, the chest below the head and the room above it.
constexpr float TalkPortraitHalfWidth = 0.75f;
constexpr float TalkPortraitChest = 0.6f;
constexpr float TalkPortraitCrown = 0.12f;
}

std::vector<std::array<float, 3>> talkPortraitHeadAndShoulders(const std::vector<std::array<float, 3>> &headPoints,
    float pivotZ)
{
    std::array<float, 3> minimum = headPoints.front();
    std::array<float, 3> maximum = headPoints.front();
    for (const std::array<float, 3> &point : headPoints)
    {
        for (size_t axis = 0; axis < 3; ++axis)
        {
            minimum[axis] = std::min(minimum[axis], point[axis]);
            maximum[axis] = std::max(maximum[axis], point[axis]);
        }
    }
    const float base = std::clamp(pivotZ, minimum[2], maximum[2]);
    const float headHeight = std::max(1.0f, maximum[2] - base);
    const float centreX = (minimum[0] + maximum[0]) * 0.5f;
    const float centreY = (minimum[1] + maximum[1]) * 0.5f;
    const float halfWidth = TalkPortraitHalfWidth * headHeight;
    const float bottom = base - TalkPortraitChest * headHeight;
    const float top = maximum[2] + TalkPortraitCrown * headHeight;
    std::vector<std::array<float, 3>> corners;
    for (int corner = 0; corner < 8; ++corner)
    {
        corners.push_back({centreX + ((corner & 1) ? halfWidth : -halfWidth),
            centreY + ((corner & 2) ? halfWidth : -halfWidth), (corner & 4) ? top : bottom});
    }
    return corners;
}

std::vector<std::array<float, 3>> talkPortraitStaticFigureFrame(const std::vector<std::array<float, 3>> &points)
{
    if (points.empty())
    {
        return {};
    }
    float lowest = points.front()[2];
    float highest = points.front()[2];
    for (const std::array<float, 3> &point : points)
    {
        lowest = std::min(lowest, point[2]);
        highest = std::max(highest, point[2]);
    }
    const float pivotZ = highest - TalkPortraitStaticHeadShare * (highest - lowest);
    std::vector<std::array<float, 3>> head;
    for (const std::array<float, 3> &point : points)
    {
        if (point[2] >= pivotZ)
        {
            head.push_back(point);
        }
    }
    return talkPortraitHeadAndShoulders(head, pivotZ);
}
}
