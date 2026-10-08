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
    // Light levels scale the displayed (sRGB) colour, as on world faces and sprites, instead of linear radiance.
    bool displaySpaceLighting = false;
    // Fraction of the ambient that arrives from keyDirection (unit, towards the light) instead of all around; 0 = off.
    std::array<float, 3> keyDirection = {};
    float keyFraction = 0.0f;
    std::array<float, 48> pointPositions = {};
    std::array<float, 48> pointColors = {};
    uint32_t pointCount = 0;
    std::array<float, 4> fogColor = {};
    std::array<float, 4> fogDensities = {};
    std::array<float, 4> fogDistances = {1.0e9f, 1.0e9f, 1.0e9f, 0};
};

// One placement of a static (unskinned, unanimated) model, such as a map decoration.
struct ModelStaticPlacement
{
    // Asset root to world.
    ModelMatrix matrix = {};
    // rgb multiplies the batch's ambient and sky reflection; a multiplies its sun.
    std::array<float, 4> light = {1.0f, 1.0f, 1.0f, 1.0f};
    // Nearby point lights as undirected diffuse light (linear rgb), as on sprites.
    std::array<float, 3> pointLight = {};
    // Hover outline colour (ABGR, 0 = none): an inflated unlit shell drawn behind the model's own pixels.
    uint32_t outlineColorAbgr = 0;
    bool visible = true;
};

// Colour LOD crossfade of one placement: both levels draw with complementary dither for ModelStaticFadeSeconds.
struct ModelStaticFade
{
    uint8_t from = 0;
    bool seen = false;
    float startSeconds = 0.0f;
};
constexpr float ModelStaticFadeSeconds = 0.3f;

// Every placement of one static model. The renderer culls each placement, picks its LOD and draws each primitive of
// each LOD once, instanced over the placements that use it.
struct ModelStaticGroup
{
    std::shared_ptr<const ModelAsset> asset;
    uint32_t variant = 0;
    // Colour LOD switch sizes; a foliage model can switch to its impostor earlier than a creature.
    std::array<float, 3> lodPixels = ModelLodPixels;
    std::vector<ModelStaticPlacement> placements;
    // World bounds per placement (placementBounds), including the wind sway; kept aligned with placements.
    std::vector<ModelBounds> bounds;
    // Renderer-owned LOD hysteresis per placement (colour, near and far shadow cascades) and colour crossfades.
    mutable std::vector<std::array<uint8_t, 3>> lodLevels;
    mutable std::vector<ModelStaticFade> fades;

    // World bounds of one placement of this group's model, including its wind sway.
    ModelBounds placementBounds(const ModelStaticPlacement &placement) const;
};

class ModelRenderer
{
public:
    bool initialize(bgfx::ProgramHandle programHandle, bgfx::ProgramHandle shadowProgramHandle = BGFX_INVALID_HANDLE);
    // Instanced programs for static groups (colour, sun shadow, and the discard-free colour pass of alpha-tested
    // materials after their depth prepass); without them renderStatic draws nothing.
    bool initializeStatic(bgfx::ProgramHandle programHandle, bgfx::ProgramHandle shadowProgramHandle,
        bgfx::ProgramHandle prepassedProgramHandle);
    void preloadStatic(const std::vector<ModelStaticGroup> &groups);
    void shutdown(bool destroyGpu);
    void preload(const ModelInstanceSystem &instances);
    void beginFrame();
    void renderSunShadows(const ModelInstanceSystem &instances, uint16_t firstViewId,
        const std::array<float, 3> &cameraPosition, const std::array<float, 3> &lightDirection, bool enabled,
        int quality = 2, bool lods = true, const std::vector<ModelStaticGroup> *pStaticGroups = nullptr,
        float timeSeconds = 0.0f);
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
        const std::function<ModelRenderLighting(ModelInstanceHandle, const ModelBounds &)> &lightingForBounds = {},
        const ModelSkyEnvironment *pSkyEnvironment = nullptr,
        const std::function<bool(const ModelBounds &)> &visibleBounds = {}, float focalPixels = 0,
        int forcedLod = -1, uint16_t transparentView = UINT16_MAX);
    // Static groups lit by `lighting` with an ambient of one (placements carry their own ambient) and no point lights.
    // Call before render() in a frame that draws both.
    void renderStatic(
        const std::vector<ModelStaticGroup> &groups,
        uint16_t viewId,
        const std::array<float, 3> &cameraPosition,
        const ModelRenderLighting &lighting,
        const ModelSkyEnvironment *pSkyEnvironment,
        const std::function<bool(const ModelBounds &)> &visibleBounds, float focalPixels, int forcedLod,
        float timeSeconds);

private:
    struct PrimitiveResources
    {
        bgfx::VertexBufferHandle vertexBuffer = BGFX_INVALID_HANDLE;
        bgfx::VertexBufferHandle skinnedVertexBuffer = BGFX_INVALID_HANDLE;
        bgfx::IndexBufferHandle indexBuffer = BGFX_INVALID_HANDLE;
        uint32_t indexCount = 0;
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
            // Non-zero: the handle belongs to m_sharedTextures under this key.
            uint64_t sharedKey = 0;
        };
        struct MaterialTextures
        {
            bgfx::TextureHandle base = BGFX_INVALID_HANDLE;
            bgfx::TextureHandle normal = BGFX_INVALID_HANDLE;
            bgfx::TextureHandle metallicRoughness = BGFX_INVALID_HANDLE;
            bgfx::TextureHandle regionMask = BGFX_INVALID_HANDLE;
            // One row per colour region, 16 sRGB stops each; invalid when the material has no colour regions.
            bgfx::TextureHandle regionRamps = BGFX_INVALID_HANDLE;
        };
        std::shared_ptr<const ModelAsset> asset;
        std::vector<Texture> textures;
        std::vector<MaterialTextures> materialTextures;
        std::vector<MeshResources> meshes;
        // Rest-pose node matrices and model height (up extent) for static placement.
        std::vector<ModelMatrix> restMatrices;
        float height = 0.0f;
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
    // Placements of one static group node that share a LOD mesh in one view.
    struct StaticBatch
    {
        const ModelStaticGroup *pGroup = nullptr;
        const AssetResources *pResources = nullptr;
        uint32_t nodeIndex = 0;
        uint32_t meshIndex = 0;
        uint32_t level = 0;
        std::vector<uint32_t> placements;
        // Crossfade per placement (shader convention: 0 none, (0, 1) appearing, (1, 2) leaving); colour pass only.
        std::vector<float> fades;
    };
    std::vector<StaticBatch> collectStaticBatches(const std::vector<ModelStaticGroup> &groups,
        const std::function<bool(const ModelBounds &)> &visibleBounds, const ModelLodView &view, float timeSeconds);
    // Placement instance data for one LOD mesh of a static group; false when the frame's instance memory is used up.
    bool allocateStaticInstances(const StaticBatch &batch, const ModelMatrix &nodeMatrix,
        bgfx::InstanceDataBuffer &buffer) const;
    void bindStaticMaterial(const AssetResources &resources, const ModelMaterial &material, int materialIndex,
        float timeSeconds, bool shadow);
    void bindColorRegions(const ModelMaterial &material, const AssetResources::MaterialTextures &textures) const;
    void submitNodeMarkers(const ModelPose &pose, uint16_t viewId) const;
    void destroySunShadows(bool destroyGpu);
    void prepareEnvironment(const ModelSkyEnvironment *pSkyEnvironment);
    void destroyEnvironment(bool destroyGpu);

    bgfx::ProgramHandle m_programHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_shadowProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_staticProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_staticShadowProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_staticPrepassedProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_staticUniformHandle = BGFX_INVALID_HANDLE;
    // The environment cube stays alive while static groups draw this frame, even without creature models.
    bool m_staticDrawn = false;
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
    // Last colour-pass submit: consecutive draws of one instance in one sequential view reuse its lighting uniforms.
    struct LastSubmit
    {
        uint16_t viewId = UINT16_MAX;
        ModelInstanceHandle instance;
        const ModelRenderLighting *pLighting = nullptr;
    };
    LastSubmit m_lastSubmit;
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
    bgfx::UniformHandle m_regionUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_regionMaskSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_regionRampSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_lightingUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_normalMatrixUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_whiteTextureHandle = BGFX_INVALID_HANDLE;
    std::unordered_map<const ModelAsset *, AssetResources> m_assets;
    // Identical images uploaded once across assets (decorations embed the same bark and leaf maps), by content and
    // upload settings; the last asset using one destroys it.
    struct SharedTexture
    {
        bgfx::TextureHandle handle = BGFX_INVALID_HANDLE;
        uint32_t references = 0;
    };
    std::unordered_map<uint64_t, SharedTexture> m_sharedTextures;
};
}
