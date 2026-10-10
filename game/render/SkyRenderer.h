#pragma once

#include "engine/render/ModelEnvironment.h"
#include "game/render/SkyState.h"

#include <bgfx/bgfx.h>

#include <array>
#include <optional>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
constexpr uint16_t SkyFogUniformVectors = 8;
// u_skyFog values shared by the sky pass and every outdoor fog blend (see game/shaders/sky_common.sh).
using SkyFogUniformValues = std::array<std::array<float, 4>, SkyFogUniformVectors>;

// The world around the sky: the terrain square whose edge fades into the distance, and open sea beyond it.
struct SkySurroundings
{
    // Half size (0 = no edge fade), centre x and centre y of the terrain square.
    std::array<float, 3> mapEdge = {};
    // Lit water colour of the sea past the edge, display space (the water shader's base colour).
    std::array<float, 3> seaColorDisplay = {};
    // Sea past each side, west (-X), east (+X), south (-Y), north (+Y): 0 = none (land or no terrain), 1 = open sea.
    std::array<float, 4> seaSideWeights = {};
    // Camera position: height above the sea, and x, y relative to the terrain square's centre.
    std::array<float, 3> camera = {};
};

// Packs the shared sky-fog uniform; a null frame gives the Classic (flat fog) values.
SkyFogUniformValues packSkyFogUniform(const SkyFrameState *pFrame, const SkySurroundings &surroundings = {});

// Linear sky-reflection colour for 3D models (1 = Classic noon), from the sky's zenith and horizon.
std::array<float, 3> skyEnvironmentTint(const SkyFrameState &frame);

// Owns the Enhanced sky: presets, per-frame state, textures and the full-screen sky pass.
class SkyRenderer
{
public:
    SkyRenderer();
    SkyRenderer(const SkyRenderer &) = delete;
    SkyRenderer &operator=(const SkyRenderer &) = delete;
    ~SkyRenderer();

    bool initialize(const Engine::AssetFileSystem &assets);
    void shutdown();
    // Drops handles without destroying them, for when the bgfx context is already gone.
    void abandonGpuResources();
    bool isReady() const;

    SkyStateModel &state();
    const SkyFrameState &frame() const;
    const SkyPresetLibrary &library() const;
    // A neutral cloud pattern for the 3D-model reflection environment; skyEnvironmentTint colours it per frame.
    std::optional<Engine::ModelSkyEnvironment> environmentSource() const;

    // Sets u_skyFog for the following draws; pass nullptr for Classic flat fog.
    void applyFogUniform(const SkyFrameState *pFrame, const SkySurroundings &surroundings = {}) const;
    // Draws the sky into viewId with the view and projection used for the world in that view.
    void render(uint16_t viewId, const float *pView, const float *pProjection, const SkySurroundings &surroundings);
    // Renders the sky at scale x the target size in imageViewId, then upscales it into viewId. The sky is mostly
    // smooth gradient and cloud, so a reduced resolution keeps its look on mobile GPUs at a fraction of the cost.
    void renderScaled(uint16_t viewId, uint16_t imageViewId, uint16_t width, uint16_t height, float scale,
        const float *pView, const float *pProjection, const SkySurroundings &surroundings);

private:
    bgfx::TextureHandle texture(const std::string &name, bool mipmaps);
    void releaseUnusedCloudTextures(const SkyFrameState &frame);
    void prepareEnvironmentSource(const Engine::AssetFileSystem &assets);

    const Engine::AssetFileSystem *m_pAssets = nullptr;
    SkyPresetLibrary m_library;
    SkyStateModel m_state;
    bgfx::ProgramHandle m_program = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_upscaleProgram = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_imageSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_upscaleUniform = BGFX_INVALID_HANDLE;
    bgfx::FrameBufferHandle m_imageFrameBuffer = BGFX_INVALID_HANDLE;
    uint16_t m_imageWidth = 0;
    uint16_t m_imageHeight = 0;
    bgfx::UniformHandle m_fogUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_rayUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_paramsUniform = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_cloudsUniform = BGFX_INVALID_HANDLE;
    std::array<bgfx::UniformHandle, 7> m_samplers;
    bgfx::TextureHandle m_emptyTexture = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_moonFallbackTexture = BGFX_INVALID_HANDLE;
    std::unordered_map<std::string, bgfx::TextureHandle> m_textures;
    // Loaded cloud layers (the large mipmapped textures), released when the weather moves on.
    std::unordered_set<std::string> m_cloudTextureNames;
    std::vector<uint8_t> m_environmentPixels;
    uint16_t m_environmentSize = 0;
    bgfx::VertexLayout m_vertexLayout;
};
}
