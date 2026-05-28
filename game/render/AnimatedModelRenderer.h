#pragma once

#include "game/render/AnimatedModelAsset.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <filesystem>
#include <vector>

namespace OpenYAMM::Game
{
struct AnimatedModelSkinnedVertex
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float normalX = 0.0f;
    float normalY = 0.0f;
    float normalZ = 1.0f;
    float u = 0.0f;
    float v = 0.0f;
    uint8_t joints[4] = {0, 0, 0, 0};
    float weights[4] = {0.0f, 0.0f, 0.0f, 0.0f};

    static void init();

    static bgfx::VertexLayout ms_layout;
};

struct AnimatedModelFogParameters
{
    std::array<float, 4> color = {0.0f, 0.0f, 0.0f, 1.0f};
    std::array<float, 4> densities = {0.0f, 0.0f, 0.0f, 0.0f};
    std::array<float, 4> distances = {1000000.0f, 1000001.0f, 1000002.0f, 0.0f};
};

struct AnimatedModelLightParameters
{
    std::array<float, 4> values = {0.78f, 0.78f, 0.78f, 0.32f};
};

class AnimatedModelRenderResources
{
public:
    void reset();
    void shutdown();

    bool isReady() const;

    bgfx::ProgramHandle skinnedProgramHandle() const;
    void setSkinnedProgramHandle(bgfx::ProgramHandle handle);

    bgfx::UniformHandle textureSamplerHandle() const;
    void setTextureSamplerHandle(bgfx::UniformHandle handle);

    bgfx::UniformHandle bonePaletteUniformHandle() const;
    void setBonePaletteUniformHandle(bgfx::UniformHandle handle);

    bgfx::UniformHandle lightParamsUniformHandle() const;
    void setLightParamsUniformHandle(bgfx::UniformHandle handle);

    bgfx::UniformHandle fogColorUniformHandle() const;
    void setFogColorUniformHandle(bgfx::UniformHandle handle);

    bgfx::UniformHandle fogDensitiesUniformHandle() const;
    void setFogDensitiesUniformHandle(bgfx::UniformHandle handle);

    bgfx::UniformHandle fogDistancesUniformHandle() const;
    void setFogDistancesUniformHandle(bgfx::UniformHandle handle);

private:
    bgfx::ProgramHandle m_skinnedProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_bonePaletteUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_lightParamsUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_fogColorUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_fogDensitiesUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_fogDistancesUniformHandle = BGFX_INVALID_HANDLE;
};

class AnimatedModelRenderer
{
public:
    static constexpr uint16_t MaxShaderBoneMatrices = 128;

    static void initializeResources(AnimatedModelRenderResources &resources);
    static void shutdownResources(AnimatedModelRenderResources &resources);

    static std::vector<AnimatedModelSkinnedVertex> buildSkinnedVertices(
        const AnimatedModelDrawItem &drawItem);

    static uint64_t renderStateForDrawItem(const AnimatedModelDrawItem &drawItem);

    static bool submitDrawItem(
        const AnimatedModelRenderResources &resources,
        uint16_t viewId,
        const AnimatedModelDrawItem &drawItem,
        const AnimatedModelMat4 &modelToWorld,
        bgfx::TextureHandle textureHandle,
        const AnimatedModelFogParameters *pFogParameters = nullptr,
        const AnimatedModelLightParameters *pLightParameters = nullptr);

private:
    static bgfx::ShaderHandle loadShader(const char *pShaderName);
    static bgfx::ProgramHandle loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName);
    static std::filesystem::path shaderRoot();
};
}
