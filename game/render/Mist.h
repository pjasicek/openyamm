#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
// A map's mist (scene `mist`, devdocs/MIST.md): layers that lie on a height and thin upward, and soft local
// volumes. Both are integrated along the view ray in the shaders that already fog (game/shaders/mist.sh), so no
// extra pass draws them. A map without the block has neither and its shaders skip the work.

// Layers a map may have (one per misty floor of a dungeon, or per height of an outdoor map).
constexpr size_t MaxMistLayers = 4;
// Volumes the shaders integrate per pixel; a map may place more, the nearest to the eye are drawn.
constexpr size_t MaxMistVolumes = 6;
// Vectors the mist adds after the sky's own in the shared u_skyFog uniform: two for the counts and the volumes'
// patches, three per layer, three per volume.
constexpr uint16_t MistUniformVectors = uint16_t(2 + 3 * MaxMistLayers + 3 * MaxMistVolumes);
using MistUniformValues = std::array<std::array<float, 4>, MistUniformVectors>;

struct MistLayer
{
    std::array<float, 3> color = {0.8f, 0.8f, 0.8f};   // display space, 0..1
    // World z at and below which the mist is densest.
    float baseHeight = 0.0f;
    // Height below the base over which the density falls to 37 %; negative: it stays at its densest all the way down.
    // A dungeon floor's mist takes a small depth, so the floors beneath it stay clear of it; outdoors a depth lets a
    // layer lie on a plateau without filling the valleys under it.
    float depth = -1.0f;
    // Height above the base over which the density falls to 37 %.
    float falloffHeight = 256.0f;
    // Distance through the densest mist that hides 63 % of what lies behind it.
    float visibility = 2048.0f;
    // The most of a pixel the mist may cover.
    float maxOpacity = 0.9f;
    // 0..1: how far drifting patches thin and thicken it.
    float noise = 0.35f;
    // World size of a patch, and its drift in world units per second.
    float noiseSize = 1536.0f;
    std::array<float, 2> drift = {14.0f, 6.0f};
    // The colour darkens with the map's light (outdoors the ambient light of the hour and weather).
    bool followsDaylight = true;
};

struct MistVolume
{
    std::array<float, 3> position = {};
    // Half extents of the ellipsoid; the density falls from the centre to nothing at its surface.
    std::array<float, 3> radius = {512.0f, 512.0f, 512.0f};
    std::array<float, 3> color = {0.8f, 0.8f, 0.8f};   // display space, 0..1
    // Distance through the centre's density that hides 63 % of what lies behind it.
    float visibility = 512.0f;
    float maxOpacity = 0.9f;
    float noise = 0.25f;
    bool followsDaylight = true;
};

struct MapMist
{
    // At most MaxMistLayers.
    std::vector<MistLayer> layers;
    std::vector<MistVolume> volumes;

    bool enabled() const
    {
        return !layers.empty() || !volumes.empty();
    }
};

// How fast a layer thins below its base, per unit of height (0: not at all).
inline float mistLayerDownwardRate(const MistLayer &layer)
{
    return layer.depth >= 0.0f ? 1.0f / std::max(layer.depth, 1.0f) : 0.0f;
}

// A layer's density at a height, 0..1 of its densest.
inline float mistLayerDensityAt(const MistLayer &layer, float z)
{
    const float height = z - layer.baseHeight;
    return std::exp(height >= 0.0f ? -height / std::max(layer.falloffHeight, 1.0f)
                                   : height * mistLayerDownwardRate(layer));
}

// The mean of exp(-u) between two values of u (the layers' integral along a ray, shader mistMeanDensity).
inline float mistMeanDensity(float from, float to)
{
    const float span = to - from;
    return std::abs(span) > 0.001f ? (std::exp(-from) - std::exp(-to)) / span : std::exp(-from);
}

// The volumes drawn for an eye position: indices of the nearest (by the distance to their surface) and the share of
// its density each keeps. With more volumes than the shaders take, a volume fades out as it nears the distance of the
// first one left out, so none appears or vanishes at full strength.
inline std::vector<std::pair<size_t, float>> selectMistVolumes(const std::vector<MistVolume> &volumes,
    const std::array<float, 3> &eye)
{
    std::vector<std::pair<float, size_t>> ranked;
    ranked.reserve(volumes.size());
    for (size_t index = 0; index < volumes.size(); ++index)
    {
        const MistVolume &volume = volumes[index];
        const float dx = volume.position[0] - eye[0];
        const float dy = volume.position[1] - eye[1];
        const float dz = volume.position[2] - eye[2];
        const float reach = std::max({volume.radius[0], volume.radius[1], volume.radius[2]});
        ranked.emplace_back(std::max(std::sqrt(dx * dx + dy * dy + dz * dz) - reach, 0.0f), index);
    }
    std::sort(ranked.begin(), ranked.end());

    std::vector<std::pair<size_t, float>> selected;
    const size_t count = std::min(ranked.size(), MaxMistVolumes);
    const float cutDistance = ranked.size() > MaxMistVolumes ? ranked[MaxMistVolumes].first : 0.0f;
    for (size_t rank = 0; rank < count; ++rank)
    {
        float share = 1.0f;
        if (cutDistance > 0.0f)
        {
            share = std::clamp((cutDistance - ranked[rank].first) / (cutDistance * 0.25f), 0.0f, 1.0f);
        }
        selected.emplace_back(ranked[rank].second, share);
    }
    return selected;
}

// The mist block of u_skyFog for one frame (game/shaders/mist.sh reads it from vector SkyFogVectors on):
// [0] layer count, volume count; [1] the volumes' patches: 1 / patch size, drift offset x, y;
// per layer: colour, most it covers; base height, 1 / falloff height, density per unit, noise; 1 / depth (0: none),
// 1 / patch size, drift offset x, y;
// per volume: centre, density per unit; 1 / radius, most it covers; colour, noise.
// `light` scales the colours of the parts that follow the daylight (1 = unchanged); `seconds` moves the patches;
// `strength` scales every density (the player's video.mist_strength, 1 = as authored).
inline MistUniformValues packMistUniform(const MapMist &mist, const std::array<float, 3> &eye, float seconds,
    const std::array<float, 3> &light = {1.0f, 1.0f, 1.0f}, float strength = 1.0f)
{
    MistUniformValues values = {};
    if (!mist.enabled() || strength <= 0.0f)
    {
        return values;
    }

    // The drift offset in patches, wrapped so it stays precise however long the game runs.
    const auto patches = [seconds](const MistLayer &layer) -> std::array<float, 3>
    {
        const float patchSize = std::max(layer.noiseSize, 1.0f);
        return {1.0f / patchSize, std::fmod(layer.drift[0] * seconds / patchSize, 256.0f),
            std::fmod(layer.drift[1] * seconds / patchSize, 256.0f)};
    };
    const size_t layerCount = std::min(mist.layers.size(), MaxMistLayers);
    const std::vector<std::pair<size_t, float>> selected = selectMistVolumes(mist.volumes, eye);
    // Volumes drift with the map's first layer, or as a layer does by default.
    const std::array<float, 3> volumePatches = patches(layerCount > 0 ? mist.layers.front() : MistLayer{});
    values[0] = {float(layerCount), float(selected.size()), 0.0f, 0.0f};
    values[1] = {volumePatches[0], volumePatches[1], volumePatches[2], 0.0f};

    for (size_t index = 0; index < layerCount; ++index)
    {
        const MistLayer &layer = mist.layers[index];
        const std::array<float, 3> scale = layer.followsDaylight ? light : std::array<float, 3>{1.0f, 1.0f, 1.0f};
        const std::array<float, 3> layerPatches = patches(layer);
        const size_t base = 2 + index * 3;
        values[base] = {layer.color[0] * scale[0], layer.color[1] * scale[1], layer.color[2] * scale[2],
            std::clamp(layer.maxOpacity, 0.0f, 1.0f)};
        values[base + 1] = {layer.baseHeight, 1.0f / std::max(layer.falloffHeight, 1.0f),
            strength / std::max(layer.visibility, 1.0f), std::clamp(layer.noise, 0.0f, 1.0f)};
        values[base + 2] = {mistLayerDownwardRate(layer), layerPatches[0], layerPatches[1], layerPatches[2]};
    }

    for (size_t slot = 0; slot < selected.size(); ++slot)
    {
        const MistVolume &volume = mist.volumes[selected[slot].first];
        const std::array<float, 3> scale = volume.followsDaylight ? light : std::array<float, 3>{1.0f, 1.0f, 1.0f};
        const size_t base = 2 + MaxMistLayers * 3 + slot * 3;
        values[base] = {volume.position[0], volume.position[1], volume.position[2],
            strength * selected[slot].second / std::max(volume.visibility, 1.0f)};
        values[base + 1] = {1.0f / std::max(volume.radius[0], 1.0f), 1.0f / std::max(volume.radius[1], 1.0f),
            1.0f / std::max(volume.radius[2], 1.0f), std::clamp(volume.maxOpacity, 0.0f, 1.0f)};
        values[base + 2] = {volume.color[0] * scale[0], volume.color[1] * scale[1], volume.color[2] * scale[2],
            std::clamp(volume.noise, 0.0f, 1.0f)};
    }
    return values;
}

// How much of the view a layer hides between two points, without its patches (the shader's layer term; for tests
// and tuning): the density falls off above the base and, with a depth, below it.
inline float mistLayerCover(const MistLayer &layer, const std::array<float, 3> &eye, const std::array<float, 3> &point)
{
    const float dx = point[0] - eye[0];
    const float dy = point[1] - eye[1];
    const float dz = point[2] - eye[2];
    const float distance = std::sqrt(dx * dx + dy * dy + dz * dz);
    const float upRate = 1.0f / std::max(layer.falloffHeight, 1.0f);
    const float downRate = mistLayerDownwardRate(layer);
    const float eyeHeight = eye[2] - layer.baseHeight;
    const float pointHeight = point[2] - layer.baseHeight;
    const auto scaled = [upRate, downRate](float height)
    {
        return height >= 0.0f ? height * upRate : -height * downRate;
    };
    float average = 0.0f;
    if (eyeHeight * pointHeight >= 0.0f)
    {
        average = mistMeanDensity(scaled(eyeHeight), scaled(pointHeight));
    }
    else
    {
        // The way crosses the base: the part on the eye's side, then the part on the point's.
        const float crossing = eyeHeight / (eyeHeight - pointHeight);
        average = crossing * mistMeanDensity(scaled(eyeHeight), 0.0f)
            + (1.0f - crossing) * mistMeanDensity(0.0f, scaled(pointHeight));
    }
    const float depth = distance * average / std::max(layer.visibility, 1.0f);
    return std::min(1.0f - std::exp(-depth), std::clamp(layer.maxOpacity, 0.0f, 1.0f));
}

// How much of the view one volume hides between two points, without its patches (the shader's volume term).
inline float mistVolumeCover(const MistVolume &volume, const std::array<float, 3> &eye,
    const std::array<float, 3> &point)
{
    std::array<float, 3> origin = {};
    std::array<float, 3> step = {};
    float distanceSquared = 0.0f;
    for (size_t axis = 0; axis < 3; ++axis)
    {
        const float inverseRadius = 1.0f / std::max(volume.radius[axis], 1.0f);
        origin[axis] = (eye[axis] - volume.position[axis]) * inverseRadius;
        step[axis] = (point[axis] - eye[axis]) * inverseRadius;
        distanceSquared += (point[axis] - eye[axis]) * (point[axis] - eye[axis]);
    }
    const float a = step[0] * step[0] + step[1] * step[1] + step[2] * step[2];
    const float b = 2.0f * (origin[0] * step[0] + origin[1] * step[1] + origin[2] * step[2]);
    const float c = origin[0] * origin[0] + origin[1] * origin[1] + origin[2] * origin[2] - 1.0f;
    const float discriminant = b * b - 4.0f * a * c;
    if (a < 1.0e-12f || discriminant <= 0.0f)
    {
        return 0.0f;
    }
    const float root = std::sqrt(discriminant);
    const float enter = std::max((-b - root) / (2.0f * a), 0.0f);
    const float leave = std::min((-b + root) / (2.0f * a), 1.0f);
    if (leave <= enter)
    {
        return 0.0f;
    }
    // The density is 1 - r^2 of the unit sphere: -(a t^2 + b t + c) along the ray.
    const auto integral = [a, b, c](float t) { return -(a * t * t * t / 3.0f + b * t * t * 0.5f + c * t); };
    const float depth = std::sqrt(distanceSquared) * (integral(leave) - integral(enter))
        / std::max(volume.visibility, 1.0f);
    return std::min(1.0f - std::exp(-depth), std::clamp(volume.maxOpacity, 0.0f, 1.0f));
}
}
