#pragma once

#include "game/app/GameSettings.h"
#include "game/outdoor/WeatherModel.h"
#include "game/render/WeatherRoofMap.h"

#include <bgfx/bgfx.h>

#include <array>
#include <functional>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
// Height of the surface rain lands on at (x, y), or nothing where it should not splash (water, off the map).
using WeatherGroundQuery = std::function<std::optional<float>(float x, float y)>;

// Everything the precipitation pass needs for one frame.
struct WeatherDrawFrame
{
    std::array<float, 3> camera = {};
    // Horizontal view direction, so splashes land where the player looks.
    std::array<float, 2> forward = {1.0f, 0.0f};
    WeatherGroundQuery groundHeight;
    float deltaSeconds = 0.0f;
    // Shown rain, snow and ash strength, 0-1; at most one is non-zero outside a short cross-fade.
    float rainLevel = 0.0f;
    float snowLevel = 0.0f;
    float ashLevel = 0.0f;
    // How snow and ash flakes look and fall (weather.yml flakes).
    WeatherFlakeLook snowLook = {};
    WeatherFlakeLook ashLook = {};
    // The rain's colour before the light (weather.yml rain_color).
    std::array<float, 3> rainColor = DefaultRainColor;
    float windX = 0.0f;
    float windY = 0.0f;
    // Light on rain and snow (day/night, sky tint, lightning flash), multiplying their own colours.
    std::array<float, 3> light = {1.0f, 1.0f, 1.0f};
    // World size of one screen pixel at unit view distance, so far drops stay at least a pixel wide.
    float pixelWorldSize = 0.001f;
    WeatherQuality quality = WeatherQuality::High;
    // The distant rain curtain; off under cover, where it would hang inside the room or tunnel.
    bool curtain = true;
};

// GPU rain, snow and ash: static buffers of seeded drops that wrap through camera-centred boxes, plus a distant rain
// curtain. The CPU only advances a fall offset per layer; no particles are simulated.
class WeatherRenderer
{
public:
    bool initialize();
    void shutdown();
    bool isReady() const;
    // Snaps the camera history so a teleport does not read as a fast camera move.
    void resetCamera();
    // Drawn into a transparent view after the world; depth-tested against the scene, no depth writes.
    void render(uint16_t viewId, const WeatherDrawFrame &frame);
    // Rain and snow fall only above the map's highest surfaces (WeatherRoofMap); none (the default, every outdoor
    // map): everywhere. Needs initialize(); false when the GPU cannot read the map in the vertex shader.
    bool setRoofMap(const WeatherRoofMap *pRoofMap);

private:
    struct Layer
    {
        std::array<float, 3> offset = {};
    };

    struct Splash
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float age = 0.0f;
        float random = 0.0f;
    };

    void updateSplashes(const WeatherDrawFrame &frame, float rainLevel, uint32_t maxSplashes);

    void advanceLayer(Layer &layer, const std::array<float, 3> &velocity, const std::array<float, 3> &box,
        float deltaSeconds) const;
    void submitDrops(uint16_t viewId, bgfx::ProgramHandle program, uint32_t count, uint64_t state) const;
    void submitFlakes(uint16_t viewId, const WeatherDrawFrame &frame, const WeatherFlakeLook &look, float level,
        const Layer &nearLayer, const Layer &farLayer, uint32_t nearCount, uint32_t farCount, uint64_t state);

    bgfx::VertexBufferHandle m_dropVertices = BGFX_INVALID_HANDLE;
    bgfx::IndexBufferHandle m_dropIndices = BGFX_INVALID_HANDLE;
    bgfx::VertexBufferHandle m_curtainVertices = BGFX_INVALID_HANDLE;
    bgfx::IndexBufferHandle m_curtainIndices = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_rainProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_snowProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_curtainProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_splashProgram = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_weatherUniform = BGFX_INVALID_HANDLE;
    // The roof map: its heights, the texture bound without one (1x1, nothing covered) and its placement
    // (origin xy, one over the extent zw; z 0 is no map).
    bgfx::TextureHandle m_roofTexture = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_noRoofTexture = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_roofSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_roofUniform = BGFX_INVALID_HANDLE;
    std::array<float, 4> m_roofPlacement = {};
    Layer m_rain;
    Layer m_farRain;
    Layer m_nearSnow;
    Layer m_farSnow;
    Layer m_nearAsh;
    Layer m_farAsh;
    float m_timeSeconds = 0.0f;
    float m_curtainPhase = 0.0f;
    bool m_hasCamera = false;
    std::array<float, 3> m_lastCamera = {};
    std::array<float, 3> m_cameraVelocity = {};
    std::vector<Splash> m_splashes;
    float m_splashAccumulator = 0.0f;
    uint64_t m_splashRandom = 0x73706c617368ull;
};
}
