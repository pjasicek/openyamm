#pragma once

#include "game/app/GameSettings.h"

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
    // Shown rain and snow strength, 0-1; at most one is non-zero outside a short cross-fade.
    float rainLevel = 0.0f;
    float snowLevel = 0.0f;
    float windX = 0.0f;
    float windY = 0.0f;
    // Light on rain and snow (day/night, sky tint, lightning flash), multiplying their own colours.
    std::array<float, 3> light = {1.0f, 1.0f, 1.0f};
    // World size of one screen pixel at unit view distance, so far drops stay at least a pixel wide.
    float pixelWorldSize = 0.001f;
    WeatherQuality quality = WeatherQuality::High;
};

// GPU rain and snow: static buffers of seeded drops that wrap through camera-centred boxes, plus a distant rain
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

    bgfx::VertexBufferHandle m_dropVertices = BGFX_INVALID_HANDLE;
    bgfx::IndexBufferHandle m_dropIndices = BGFX_INVALID_HANDLE;
    bgfx::VertexBufferHandle m_curtainVertices = BGFX_INVALID_HANDLE;
    bgfx::IndexBufferHandle m_curtainIndices = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_rainProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_snowProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_curtainProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_splashProgram = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_weatherUniform = BGFX_INVALID_HANDLE;
    Layer m_rain;
    Layer m_farRain;
    Layer m_nearSnow;
    Layer m_farSnow;
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
