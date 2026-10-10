#pragma once

#include "engine/models/ModelAsset.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Engine
{
struct ModelLodView
{
    std::array<float, 3> camera = {};
    float focalPixels = 0;
    float orthographicPixelsPerUnit = 0;
    int shadowCascade = -1;
    bool enabled = true;
    int forcedLevel = -1;
    // A secondary view (a water reflection) picks levels from the current LOD hysteresis and crossfade state but
    // leaves that state to the main view.
    bool keepState = false;
};

inline float modelBoundsDiameter(const ModelBounds &bounds)
{
    if (!bounds.valid)
    {
        return 0;
    }
    float squared = 0;
    for (size_t axis = 0; axis < 3; ++axis)
    {
        const float extent = bounds.max[axis] - bounds.min[axis];
        squared += extent * extent;
    }
    return std::sqrt(squared);
}

inline float modelProjectedPixels(const ModelBounds &bounds, const std::array<float, 3> &camera, float focalPixels)
{
    if (!bounds.valid || focalPixels <= 0)
    {
        return 0;
    }
    float squared = 0;
    for (size_t axis = 0; axis < 3; ++axis)
    {
        const float delta = (bounds.min[axis] + bounds.max[axis]) * 0.5f - camera[axis];
        squared += delta * delta;
    }
    const float diameter = modelBoundsDiameter(bounds);
    return focalPixels * diameter / std::max(std::sqrt(squared) - diameter * 0.5f, 1.0f);
}

// Projected sizes (pixels) below which colour LODs 1..3 take over.
constexpr std::array<float, 3> ModelLodPixels = {500, 200, 80};
// Coarser switch sizes for static stand-ins (frozen corpses): one LOD step earlier than a live creature.
constexpr std::array<float, 3> ModelStandInLodPixels = {750, 300, 120};

inline uint32_t modelLodLevel(float pixels, uint32_t previous, uint32_t count, bool shadow = false,
    const std::array<float, 3> &colourThresholds = ModelLodPixels)
{
    if (count <= 1)
    {
        return 0;
    }
    count = std::min(count, 4u);
    // Shadow sizes are shadow-map texels: a 150-texel creature shadow keeps its silhouette with the 2k-triangle LOD.
    const std::array<float, 3> thresholds = shadow ? std::array<float, 3>{256, 192, 64} : colourThresholds;
    uint32_t level = std::min(previous, count - 1);
    // Ten percent hysteresis avoids switches while a creature hovers around a screen-size boundary.
    while (level + 1 < count && level < thresholds.size() && pixels < thresholds[level] * 0.9f)
    {
        ++level;
    }
    while (level > 0 && pixels > thresholds[level - 1] * 1.1f)
    {
        --level;
    }
    return level;
}
}
