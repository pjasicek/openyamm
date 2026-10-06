#pragma once

#include "engine/models/ModelInstance.h"
#include "engine/render/ModelEnvironment.h"
#include "engine/render/ModelLod.h"
#include "engine/render/ModelSunShadows.h"

#include <bgfx/bgfx.h>

#include <array>
#include <functional>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
struct ModelRenderLighting
{
    std::array<float, 3> lightDirection = {-0.35f, 0.55f, 0.76f};
    float ambient = 0.35f;
    float direct = 0.65f;
    std::array<float, 3> directColor = {1.0f, 1.0f, 1.0f};
    std::array<float, 3> ambientColor = {1.0f, 1.0f, 1.0f};
    std::array<float, 3> environmentColor = {};
    std::array<float, 48> pointPositions = {};
    std::array<float, 48> pointColors = {};
    uint32_t pointCount = 0;
    std::array<float, 4> fogColor = {};
    std::array<float, 4> fogDensities = {};
    std::array<float, 4> fogDistances = {1.0e9f, 1.0e9f, 1.0e9f, 0};
};

class ModelRenderer
{
public:
    bool initialize(bgfx::ProgramHandle programHandle, bgfx::ProgramHandle shadowProgramHandle = BGFX_INVALID_HANDLE);
    void shutdown(bool destroyGpu);
    void preload(const ModelInstanceSystem &instances);
    void beginFrame();
    void renderSunShadows(const ModelInstanceSystem &instances, uint16_t firstViewId,
        const std::array<float, 3> &cameraPosition, const std::array<float, 3> &lightDirection, bool enabled,
        int quality = 2, bool lods = true);
    bool hasSunShadowResources() const
    {
        return bgfx::isValid(m_shadowFramebuffers[0]);
    }
    void bindSunShadows() const;
    bool hasSunShadows() const
    {
        return m_shadowParams[0][0] > 0.5f;
    }
    void render(
        const ModelInstanceSystem &instances,
        uint16_t viewId,
        const std::array<float, 3> &cameraPosition,
        const ModelRenderLighting &lighting = {},
        const std::function<ModelRenderLighting(const ModelBounds &)> &lightingForBounds = {},
        const ModelSkyEnvironment *pSkyEnvironment = nullptr,
        const std::function<bool(const ModelBounds &)> &visibleBounds = {}, float focalPixels = 0,
        int forcedLod = -1);

private:
    struct PrimitiveResources
    {
        bgfx::VertexBufferHandle vertexBuffer = BGFX_INVALID_HANDLE;
        bgfx::VertexBufferHandle skinnedVertexBuffer = BGFX_INVALID_HANDLE;
        bgfx::IndexBufferHandle indexBuffer = BGFX_INVALID_HANDLE;
        uint32_t indexCount = 0;
        int materialIndex = -1;
        std::array<float, 3> center = {};
    };

    struct MeshResources
    {
        std::vector<PrimitiveResources> primitives;
    };

    struct AssetResources
    {
        struct Texture
        {
            int imageIndex = -1;
            int semantic = 0;
            uint8_t alphaCutoff = 0;
            bool mips = true;
            bgfx::TextureHandle handle = BGFX_INVALID_HANDLE;
        };
        struct MaterialTextures
        {
            bgfx::TextureHandle base = BGFX_INVALID_HANDLE;
            bgfx::TextureHandle normal = BGFX_INVALID_HANDLE;
            bgfx::TextureHandle metallicRoughness = BGFX_INVALID_HANDLE;
        };
        std::shared_ptr<const ModelAsset> asset;
        std::vector<Texture> textures;
        std::vector<MaterialTextures> materialTextures;
        std::vector<MeshResources> meshes;
    };

    struct Draw;

    const AssetResources *prepare(std::shared_ptr<const ModelAsset> asset);
    void pruneUnusedAssets();
    void destroy(AssetResources &resources);
    std::vector<Draw> collectDraws(const ModelInstanceSystem &instances,
        const std::function<bool(const ModelBounds &)> &visibleBounds, const ModelLodView &view = {});
    void destroyDeformedBuffers(bool destroyGpu);
    void bindSkin(const Draw &draw);
    bool bindGeometry(const Draw &draw);
    void submit(const Draw &draw, uint16_t viewId, const ModelRenderLighting &lighting);
    void submitNodeMarkers(const ModelPose &pose, uint16_t viewId) const;
    void destroySunShadows(bool destroyGpu);
    void prepareEnvironment(const ModelSkyEnvironment *pSkyEnvironment);
    void destroyEnvironment(bool destroyGpu);

    bgfx::ProgramHandle m_programHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_shadowProgramHandle = BGFX_INVALID_HANDLE;
    std::array<bgfx::TextureHandle, ModelSunShadowCascades> m_shadowTextures =
        {{BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE}};
    std::array<bgfx::FrameBufferHandle, ModelSunShadowCascades> m_shadowFramebuffers =
        {{BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE}};
    std::array<bgfx::UniformHandle, ModelSunShadowCascades> m_shadowSamplers =
        {{BGFX_INVALID_HANDLE, BGFX_INVALID_HANDLE}};
    bgfx::UniformHandle m_shadowMatricesUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_shadowParamsUniformHandle = BGFX_INVALID_HANDLE;
    std::array<ModelMatrix, ModelSunShadowCascades> m_shadowMatrices = {};
    std::array<std::array<float, 4>, 4> m_shadowParams = {};
    uint16_t m_shadowSize = 0;
    struct LodState
    {
        ModelInstanceHandle owner;
        uint32_t color = 0;
        std::array<uint32_t, 2> shadow = {};
    };
    std::unordered_map<const ModelMatrix *, LodState> m_lodStates;
    struct DeformedBuffer
    {
        ModelInstanceHandle owner;
        bgfx::DynamicVertexBufferHandle handle = BGFX_INVALID_HANDLE;
        uint32_t count = 0;
        uint64_t revision = 0;
    };
    std::unordered_map<const std::vector<ModelVertex> *, DeformedBuffer> m_deformedVertexBuffers;
    struct SkinPalette
    {
        ModelInstanceHandle owner;
        bgfx::TextureHandle texture = BGFX_INVALID_HANDLE;
        uint64_t revision = 0;
    };
    std::unordered_map<const ModelMatrix *, SkinPalette> m_skinPalettes;
    bgfx::UniformHandle m_skinSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_skinParamsHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_normalSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_metallicRoughnessSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_pbrUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_environmentSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_environmentBrdfSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_environmentUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_environmentTextureHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_environmentBrdfTextureHandle = BGFX_INVALID_HANDLE;
    std::string m_environmentKey;
    float m_environmentMaxLod = 0;
    bgfx::UniformHandle m_pointPositionsUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_pointColorsUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_surfaceUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_fogUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_cameraUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_outlineUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_materialUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_lightingUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_normalMatrixUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_whiteTextureHandle = BGFX_INVALID_HANDLE;
    std::unordered_map<const ModelAsset *, AssetResources> m_assets;
};
}
