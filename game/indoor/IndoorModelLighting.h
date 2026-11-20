#pragma once

#include <algorithm>
#include <array>

namespace OpenYAMM::Game
{
// A map's model lighting (scene `model_lighting`, devdocs/INDOOR_MODEL_LIGHTING.md): MM9's lighting of its .abc
// models for the map's decorations (3D models and sprites) and actors, instead of the room ambient and BLV light the
// native maps use. Disabled on every map without the scene block, which then renders exactly as before.
//
// Per point, in 0..1 (MM9's 0..255 / 255):
//   light = min(1, ambient + add + sum of colour * lightScale * (1 - d^2/r^2) * max(0, N.L) over its lights)
// The colour is the BLV light's own (at the strength a map light carries, IndoorLightingRuntime::mapLightStrength),
// so lightScale 1 gives MM9's raw LightColor where the converter wrote it unscaled.
struct IndoorModelLighting
{
    bool enabled = false;
    std::array<float, 3> ambient = {0.0f, 0.0f, 0.0f};   // MM9's WorldInfo AmbientLight
    std::array<float, 3> add = {30.0f / 255.0f, 30.0f / 255.0f, 30.0f / 255.0f};   // MM9's ModelAdd
    float lightScale = 1.0f;
};

// MM9's per-vertex light falloff, 1 - d^2/r^2 (0 at and past the radius).
inline float indoorModelLightFalloff(float distanceSquared, float radius)
{
    if (radius <= 0.0f)
    {
        return 0.0f;
    }
    return std::max(1.0f - distanceSquared / (radius * radius), 0.0f);
}

// The light of a point lit by `lights` (the sum of colour * lightScale * falloff * N.L, unclamped): the model base
// (ambient + add) plus those lights, clamped to 1 per channel as MM9 clamps at 255.
inline std::array<float, 3> indoorModelLight(const IndoorModelLighting &lighting, const std::array<float, 3> &lights)
{
    std::array<float, 3> rgb = {};
    for (size_t channel = 0; channel < 3; ++channel)
    {
        rgb[channel] = std::clamp(lighting.ambient[channel] + lighting.add[channel] + lights[channel], 0.0f, 1.0f);
    }
    return rgb;
}
}
