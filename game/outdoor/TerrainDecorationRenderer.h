#pragma once

#include "game/outdoor/TerrainDecorationData.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

namespace OpenYAMM::Game
{
struct OutdoorSelectedFxLights;

class TerrainDecorationRenderer
{
public:
    static constexpr size_t MaxTuftLayers = 16;

    // Takes ownership of both programs, including on initialization failure.
    bool initialize(const Engine::AssetFileSystem &assets, const TerrainDecorationConfig &config,
                    TerrainDecorationPlacement placement, bgfx::ProgramHandle program,
                    bgfx::ProgramHandle shadowProgram);
    void shutdown(bool destroyResources);
    const std::vector<TerrainDecorationPatch> &patches() const
    {
        return m_patches;
    }
    // Returns true when culling must be refreshed for a changed camera or projection.
    bool setView(const bx::Vec3 &camera, const bx::Vec3 &forward, const bx::Vec3 &right, const bx::Vec3 &up,
                 float aspect, float verticalFovRadians);
    bool visible(const TerrainDecorationPatch &patch) const;
    void submit(uint16_t viewId, const TerrainDecorationPatch &patch, float elapsedTime, bool sunShadows);
    static bool canMerge(const TerrainDecorationPatch &batch, const OutdoorSelectedFxLights &batchLights,
                         const TerrainDecorationPatch &next, const OutdoorSelectedFxLights &nextLights);

private:
    std::vector<TerrainDecorationPatch> m_patches;
    bgfx::ProgramHandle m_program = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_shadowProgram = BGFX_INVALID_HANDLE;
    bgfx::VertexBufferHandle m_instances = BGFX_INVALID_HANDLE;
    // Two crossed cards whose corners are slots of their tuft layer's cutout (vertex x = slot, y = card).
    bgfx::VertexBufferHandle m_grassMesh = BGFX_INVALID_HANDLE;
    bgfx::IndexBufferHandle m_grassIndices = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_cutoutUniform = BGFX_INVALID_HANDLE;
    // Cutout texture coordinates of each atlas layer, two vertices per vec4.
    std::array<std::array<float, 4>, MaxTuftLayers * TerrainDecorationCutoutVertices / 2> m_cutouts = {};
    bgfx::VertexBufferHandle m_stoneMesh = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_texture = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_sampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_params = BGFX_INVALID_HANDLE;
    float m_distance = 2048.0f;
    bx::Vec3 m_camera = {0.0f, 0.0f, 0.0f};
    bx::Vec3 m_forward = {0.0f, 0.0f, 0.0f};
    bx::Vec3 m_right = {0.0f, 0.0f, 0.0f};
    bx::Vec3 m_up = {0.0f, 0.0f, 0.0f};
    bool m_viewValid = false;
    float m_aspect = 0.0f;
    float m_verticalFov = 0.0f;
    float m_tanX = 0.0f;
    float m_tanY = 0.0f;
    float m_radiusScaleX = 0.0f;
    float m_radiusScaleY = 0.0f;
};
} // namespace OpenYAMM::Game
