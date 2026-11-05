#pragma once

#include "engine/models/ModelInstance.h"
#include "engine/render/LightGrid.h"
#include "engine/render/ModelEnvironment.h"
#include "engine/render/ModelLod.h"
#include "engine/render/ModelSunShadows.h"

#include <bgfx/bgfx.h>

#include <array>
#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace OpenYAMM::Engine
{
// Vectors in the shared u_skyFog uniform (game/shaders/sky_common.sh).
constexpr uint16_t ModelSkyFogVectors = 8;

struct ModelRenderLighting
{
    std::array<float, 3> lightDirection = {-0.35f, 0.55f, 0.76f};
    float ambient = 0.35f;
    float direct = 0.65f;
    std::array<float, 3> directColor = {1.0f, 1.0f, 1.0f};
    std::array<float, 3> ambientColor = {1.0f, 1.0f, 1.0f};
    // Sky reflection strength as a multiple of the ambient light (ambientColor x ambient), per channel.
    std::array<float, 3> environmentScale = {};
    // Light levels scale the displayed (sRGB) colour, as on world faces and sprites, instead of linear radiance.
    bool displaySpaceLighting = false;
    // Fraction of the ambient that arrives from keyDirection (unit, towards the light) instead of all around; 0 = off.
    std::array<float, 3> keyDirection = {};
    float keyFraction = 0.0f;
    std::array<float, 48> pointPositions = {};
    std::array<float, 48> pointColors = {};
    uint32_t pointCount = 0;
    // The point lights add only their specular highlight: the placement's own light (ModelStaticPlacement::light)
    // already holds their diffuse share, as on the sprites indoor decorations replace.
    bool pointSpecularOnly = false;
    // The view's clustered light grid: when set (and outside reflection passes), point lights come from it and the
    // pointPositions/pointColors list is not used.
    const LightGridTextures *pLightGrid = nullptr;
    // Per model: its indoor sector, so it takes only the grid lights that reach its room (-1: any light).
    int16_t sector = -1;
    std::array<float, 4> fogColor = {};
    std::array<float, 4> fogDensities = {};
    std::array<float, 4> fogDistances = {1.0e9f, 1.0e9f, 1.0e9f, 0};
    // Shared sky colour for fog (u_skyFog); all zero keeps the flat fogColor.
    std::array<std::array<float, 4>, ModelSkyFogVectors> skyFog = {};
    // MM9's fixed-function model lighting (indoor scene model_lighting, devdocs/INDOOR_MODEL_LIGHTING.md) instead of
    // the PBR path: the texel times min(1, light) in display space, light = ambient (ambientColor x ambient x the
    // placement light) + each point light's colour x intensity x fixedPointScale x (1 - d^2/r^2) x max(0, N.L), with
    // mesh normals; no key light, specular, reflection, sun or edge darkening.
    bool fixedFunctionLighting = false;
    float fixedPointScale = 1.0f;
};

// The colour programs of materials with an emissive texture (fs_model_emissive), one per vertex program: single draws
// (vs_model), instanced creatures (vs_model_skinned_instanced) and static placements (vs_model_instanced).
struct ModelEmissivePrograms
{
    bgfx::ProgramHandle single = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle skinnedInstanced = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle staticInstanced = BGFX_INVALID_HANDLE;
};

// Key light direction (unit, towards the light) from above, in front of and left of the camera, like the painted light
// on the original sprites; viewForward is the camera's unit look direction. Used with ModelRenderLighting::keyFraction.
std::array<float, 3> spriteKeyLightDirection(const std::array<float, 3> &viewForward);

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
    // Fixed colour LOD (an attachment follows its carrier's level); -1 picks the level by projected size.
    int32_t colorLevel = -1;
    // Fraction of pixels drawn (screen-door dissolve of a sinking corpse or an appearing prop); below 1 it replaces the
    // LOD crossfade of this placement.
    float coverage = 1.0f;
    // Its indoor sector, so it takes only the grid lights that reach its room (-1: any light).
    int16_t sector = -1;
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
    // Placements smaller on screen than this are not drawn in colour views (ground items far away); 0 draws all.
    float minimumPixels = 0.0f;
    std::vector<ModelStaticPlacement> placements;
    // World bounds per placement (placementBounds), including the wind sway; kept aligned with placements.
    std::vector<ModelBounds> bounds;
    // Renderer-owned LOD hysteresis per placement (colour, then each shadow cascade) and colour crossfades.
    mutable std::vector<std::array<uint8_t, 1 + ModelSunShadowCascades>> lodLevels;
    mutable std::vector<ModelStaticFade> fades;

    // World bounds of one placement of this group's model, including its wind sway.
    ModelBounds placementBounds(const ModelStaticPlacement &placement) const;
};

class ModelRenderer
{
public:
    // skinnedInstancedProgramHandle (optional) draws skinned creatures without point lights or outlines instanced,
    // one draw per primitive and material for all of them.
    bool initialize(bgfx::ProgramHandle programHandle, bgfx::ProgramHandle shadowProgramHandle = BGFX_INVALID_HANDLE,
        bgfx::ProgramHandle skinnedInstancedProgramHandle = BGFX_INVALID_HANDLE);
    // Instanced programs for static groups (colour, sun shadow, and the discard-free colour pass of alpha-tested
    // materials after their depth prepass); without them renderStatic draws nothing.
    bool initializeStatic(bgfx::ProgramHandle programHandle, bgfx::ProgramHandle shadowProgramHandle,
        bgfx::ProgramHandle prepassedProgramHandle);
    void preloadStatic(const std::vector<ModelStaticGroup> &groups);
    // The ALPHA_TO_COVERAGE program of the static foliage depth prepass (vs_model_instanced, fs_model_coverage),
    // loaded the first time anti-aliasing is on; takes ownership, also of an invalid handle (no further attempt).
    void setStaticCoverageProgram(bgfx::ProgramHandle programHandle);
    bool staticCoverageProgramAttempted() const
    {
        return m_staticCoverageProgramAttempted;
    }
    // Per frame, before the world's renderStatic: its views draw into a multisampled target with alpha to coverage,
    // so the foliage depth prepass writes coverage instead of discarding.
    void setAlphaToCoverage(bool enabled)
    {
        m_alphaToCoverage = enabled;
    }
    // Profiling switch: draw static groups without their alpha-tested (foliage) materials.
    void setStaticFoliageVisible(bool visible)
    {
        m_staticFoliageVisible = visible;
    }
    // Bloom (CinematicGrading::glowView): emitters (static glow and flame cards and emissive surfaces, creature
    // materials with "bloom") draw again into this view, writing only their glow; UINT16_MAX for none.
    void setGlowView(uint16_t view)
    {
        m_glowView = view;
        m_glowDrawn = false;
    }
    // Loads the emissive-texture programs the first time a model with an emissive texture is prepared, so models
    // without one cost nothing. Without a loader, or when loading fails, emissive textures emit nothing.
    void setEmissiveProgramLoader(std::function<ModelEmissivePrograms()> loader)
    {
        m_emissiveProgramLoader = std::move(loader);
    }
    // Loads the energy shield shell program (vs_model_shield, fs_model_shield) the first time an instance with a
    // shield shell (ModelInstanceSystem::setShieldShell) draws, so scenes without shields cost nothing.
    void setShieldShellProgramLoader(std::function<bgfx::ProgramHandle()> loader)
    {
        m_shieldShellProgramLoader = std::move(loader);
    }
    // Whether an emitter drew into the glow view since setGlowView (the bloom chain is skipped otherwise).
    bool glowDrawn() const
    {
        return m_glowDrawn;
    }
    // Profiling switch: draw every skinned creature with its own draws instead of instanced.
    void setSkinnedInstancing(bool enabled)
    {
        m_skinnedInstancing = enabled;
    }
    // The dark contour shell around creature materials (drawsContour); off by default.
    void setCreatureContour(bool enabled)
    {
        m_creatureContour = enabled;
    }
    void shutdown(bool destroyGpu);
    void preload(const ModelInstanceSystem &instances);
    void beginFrame();
    // Draws each cascade into its tile of the shadow atlas (views firstViewId onwards). worldCasters submits world
    // geometry (the terrain) into a cascade's view, for the bounds its predicate accepts; such casters mark
    // themselves as terrain by a zero alpha.
    void renderSunShadows(const ModelInstanceSystem &instances, uint16_t firstViewId,
        const ModelSunShadowCamera &camera, const std::array<float, 3> &lightDirection, bool enabled,
        int quality = 2, bool lods = true, const std::vector<ModelStaticGroup> *pStaticGroups = nullptr,
        float timeSeconds = 0.0f,
        const std::function<void(uint16_t, const std::function<bool(const ModelBounds &)> &)> &worldCasters = {});
    bool hasSunShadowResources() const
    {
        return bgfx::isValid(m_shadowFramebuffer);
    }
    // The draw's light grid uniform and textures (mode 0 without one).
    void bindLightGrid(const ModelRenderLighting &lighting) const;
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
        int forcedLod = -1, float timeSeconds = 0.0f, uint16_t transparentView = UINT16_MAX);
    // Static groups lit by `lighting` with an ambient of one (placements carry their own ambient) and no point lights.
    // Call before render() in a frame that draws both. Blended parts (fountain streams, flame cards) go to
    // transparentView when given, a view drawn after the creatures, so a creature behind them is not drawn over them;
    // blending writes no depth.
    void renderStatic(
        const std::vector<ModelStaticGroup> &groups,
        uint16_t viewId,
        const std::array<float, 3> &cameraPosition,
        const ModelRenderLighting &lighting,
        const ModelSkyEnvironment *pSkyEnvironment,
        const std::function<bool(const ModelBounds &)> &visibleBounds, float focalPixels, int forcedLod,
        float timeSeconds, uint16_t transparentView = UINT16_MAX);
    // One instance alone, at full detail and with its attachments, into viewId: a UI portrait such as the actor
    // inspect preview. It draws whether or not the instance is visible to the world passes (a portrait instance stays
    // hidden from them), without sun shadows, hover outline or a change of sky environment, and leaves the world
    // views' LOD and attachment state untouched. The caller sets viewId's frame buffer and transform; the view should
    // be sequential, as the draws share uniforms set once.
    void renderPortrait(const ModelInstanceSystem &instances, ModelInstanceHandle handle, uint16_t viewId,
        const std::array<float, 3> &cameraPosition, const ModelRenderLighting &lighting);
    // Water reflection of the static groups and creatures, drawn into viewId from the reflected camera. The main
    // view's LOD state stays untouched; nothing is culled (the mirrored view flips winding) and there are no hover
    // outlines or foliage prepass. The caller sets u_worldClipPlane, which fs_model clips against.
    void renderReflection(const ModelInstanceSystem &instances, const std::vector<ModelStaticGroup> &staticGroups,
        uint16_t viewId, const std::array<float, 3> &cameraPosition, const ModelRenderLighting &staticLighting,
        const ModelRenderLighting &lighting,
        const std::function<ModelRenderLighting(ModelInstanceHandle, const ModelBounds &)> &lightingForBounds,
        const ModelSkyEnvironment *pSkyEnvironment, const std::function<bool(const ModelBounds &)> &visibleBounds,
        float focalPixels, float timeSeconds);

private:
    struct PrimitiveResources
    {
        bgfx::VertexBufferHandle vertexBuffer = BGFX_INVALID_HANDLE;
        bgfx::VertexBufferHandle skinnedVertexBuffer = BGFX_INVALID_HANDLE;
        bgfx::IndexBufferHandle indexBuffer = BGFX_INVALID_HANDLE;
        uint32_t indexCount = 0;
        std::array<float, 3> center = {};
        // Skin joint index carrying most of the weight: a blended skin sorts by where this joint carries `center`.
        int anchorJoint = -1;
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
            bgfx::TextureHandle burnMap = BGFX_INVALID_HANDLE;
            // Only while the emissive programs are loaded (ensureEmissivePrograms).
            bgfx::TextureHandle emissive = BGFX_INVALID_HANDLE;
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
    // Model textures read and decoded on the load workers, by shared texture key, for prepare to upload.
    struct PreparedTextures;

    // Decodes every texture these assets need that is not resident yet, in parallel (preloads only).
    PreparedTextures prepareTextures(const std::vector<std::shared_ptr<const ModelAsset>> &assets) const;
    const AssetResources *prepare(std::shared_ptr<const ModelAsset> asset, PreparedTextures *pPrepared = nullptr);
    void pruneUnusedAssets();
    void destroy(AssetResources &resources);
    // The draws of one LOD mesh at a node of a posed instance.
    void appendMeshDraws(std::vector<Draw> &draws, const ModelAsset &asset, const AssetResources &resources,
        const ModelPose &pose, size_t nodeIndex, uint32_t meshIndex, uint32_t variant, uint32_t outlineColorAbgr,
        ModelInstanceHandle handle) const;
    std::vector<Draw> collectDraws(const ModelInstanceSystem &instances,
        const std::function<bool(const ModelBounds &)> &visibleBounds, const ModelLodView &view = {});
    void destroyDeformedBuffers(bool destroyGpu);
    void bindSkin(const Draw &draw);
    // Texture scroll of a creature material (openyamm_uv_scroll) at m_creatureTimeSeconds, for vs_model's u_modelScroll.
    void bindTextureScroll(const ModelMaterial &material);
    // Face culling of a colour draw; none in a reflection pass.
    uint64_t colorCullState(const ModelMaterial &material, const ModelMatrix &matrix) const;
    // The draw's first row in the shared joint palette, allocated and refreshed for its pose (may grow the palette).
    uint32_t jointPaletteRow(const Draw &draw);
    void releaseJointRows(uint32_t row, uint32_t rows);
    // Opaque creature passes: one shaded pass (small creatures, water reflections), or a depth-only pass followed by
    // a shaded pass that tests equal depth, so each pixel is lit once (see render()).
    enum class OpaquePass
    {
        Shaded,
        Depth,
        AfterDepth,
    };
    // One instanced draw: the creatures sharing a primitive, material and winding, with their instance data.
    struct SkinnedRun
    {
        const Draw *pDraw = nullptr;
        bgfx::InstanceDataBuffer buffer = {};
        bool prepassed = false;
    };
    // Groups the instanced draws into runs; draws that no longer fit the frame's instance memory go to leftover.
    std::vector<SkinnedRun> prepareInstancedSkinned(const std::vector<Draw> &draws, std::vector<Draw> &leftover);
    // depthPass: the depth prepass of the prepassed runs; otherwise every run's shaded draw.
    void submitInstancedSkinned(const std::vector<SkinnedRun> &runs, const ModelRenderLighting &shared,
        uint16_t viewId, bool depthPass);
    // Loads the emissive programs once (setEmissiveProgramLoader); true when they are available.
    bool ensureEmissivePrograms();
    // u_modelSurface: the emission (scaled, e.g. by a creature's pulse; none for an emissive texture without its
    // program) and the normal map scale (-1 without one).
    std::array<float, 4> surfaceUniform(const ModelMaterial &material, const AssetResources::MaterialTextures &textures,
        float emissionScale) const;
    // The emissive variant of a colour program for a material that samples an emissive texture, else the program.
    bgfx::ProgramHandle colorProgram(const AssetResources::MaterialTextures &textures, bgfx::ProgramHandle program,
        bgfx::ProgramHandle emissiveProgram) const;
    void bindEmissiveTexture(const ModelMaterial &material, const AssetResources::MaterialTextures &textures) const;
    // A creature (skinned) material that draws its emission into the bloom glow view in this pass ("bloom").
    bool creatureGlows(const ModelMaterial &material, const AssetResources::MaterialTextures &textures) const;
    // The glow submission of the colour draw just submitted with BGFX_DISCARD_NONE (its geometry and bindings still
    // set); keepBindings for a contour shell after it.
    void submitCreatureGlow(bgfx::ProgramHandle program, const ModelMaterial &material, const ModelMatrix &cullMatrix,
        bool keepBindings);
    // Creature materials (edge darkening) outside a reflection pass draw a dark contour shell after the body.
    bool drawsContour(const ModelMaterial &material) const;
    // The contour shell of the body just submitted with BGFX_DISCARD_NONE (its geometry and bindings still set).
    void submitContour(uint16_t viewId, bgfx::ProgramHandle program, const ModelMatrix &cullMatrix);
    // Rebuilds m_attachmentGroups from the instances' attachments at their nodes' current matrices, plus each
    // instance's static stand-in (ModelInstanceSystem::setStaticStandIn) at its root transform, kept while the
    // instances' stand-in revision is unchanged. With visibleBounds,
    // a carrier whose motion bounds (padded by its attachments' reach) are outside the view is skipped without
    // evaluating its pose.
    void collectAttachments(const ModelInstanceSystem &instances,
        const std::function<bool(const ModelBounds &)> &visibleBounds = {});
    bool bindGeometry(const Draw &draw);
    void submit(const Draw &draw, uint16_t viewId, const ModelRenderLighting &lighting,
        OpaquePass pass = OpaquePass::Shaded);
    // The additive fire standing in for a burning draw's freshly burnt surface (ModelBurn::fireWidth).
    void submitBurnFire(const Draw &draw, uint16_t viewId);
    // The energy shield shell over a draw (ModelShieldShell), additive after the scene's opaque and blended parts,
    // and its glow into the bloom view.
    void submitShieldShell(const Draw &draw, uint16_t viewId, const std::array<float, 3> &cameraPosition);
    bool ensureShieldShellProgram();
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
    // renderStatic after its environment: the static groups' draws.
    void submitStatic(const std::vector<ModelStaticGroup> &groups, uint16_t viewId,
        const std::array<float, 3> &cameraPosition, const ModelRenderLighting &lighting,
        const std::function<bool(const ModelBounds &)> &visibleBounds, float focalPixels, int forcedLod,
        float timeSeconds, uint16_t transparentView);
    std::vector<StaticBatch> collectStaticBatches(const std::vector<ModelStaticGroup> &groups,
        const std::function<bool(const ModelBounds &)> &visibleBounds, const ModelLodView &view, float timeSeconds);
    // Placement instance data for one LOD mesh of a static group; false when the frame's instance memory is used up.
    bool allocateStaticInstances(const StaticBatch &batch, const ModelMatrix &nodeMatrix,
        bgfx::InstanceDataBuffer &buffer) const;
    // pCardPivot: the primitive's centre (mesh space) for a card billboard ("openyamm_billboard": "card").
    // emissionScale: a creature's pulse (instanced creatures; static placements pulse in vs_model_instanced).
    void bindStaticMaterial(const AssetResources &resources, const ModelMaterial &material, int materialIndex,
        float timeSeconds, bool shadow, const std::array<float, 3> *pCardPivot = nullptr, float emissionScale = 1.0f);
    void bindColorRegions(const ModelMaterial &material, const AssetResources::MaterialTextures &textures) const;
    // u_modelBurn and the burn map for every fs_model/fs_model_shadow draw: off without a burn (uniforms persist
    // between draws). fire: the additive pass over the burnt surface instead of the burning surface itself.
    void bindBurn(const ModelBurn *pBurn, const ModelMaterial &material,
        const AssetResources::MaterialTextures &textures, bool fire = false) const;
    void submitNodeMarkers(const ModelPose &pose, uint16_t viewId) const;
    void destroySunShadows(bool destroyGpu);
    void prepareEnvironment(const ModelSkyEnvironment *pSkyEnvironment);
    void destroyEnvironment(bool destroyGpu);

    bgfx::ProgramHandle m_programHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_shadowProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_staticProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_staticShadowProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_staticPrepassedProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_staticCoverageProgramHandle = BGFX_INVALID_HANDLE;
    bool m_staticCoverageProgramAttempted = false;
    bool m_alphaToCoverage = false;
    bgfx::UniformHandle m_staticUniformHandle = BGFX_INVALID_HANDLE;
    // The environment cube stays alive while static groups draw this frame, even without creature models.
    bool m_staticDrawn = false;
    bool m_staticFoliageVisible = true;
    bool m_skinnedInstancing = true;
    bool m_creatureContour = false;
    // Set while renderReflection draws.
    bool m_reflectionPass = false;
    // Set while renderPortrait draws: creatures do not glow into the world's bloom view.
    bool m_portraitPass = false;
    // Clock of scrolling creature textures, from the latest render(); portraits keep the world's.
    float m_creatureTimeSeconds = 0.0f;
    // All cascades side by side in one atlas, so receivers need one sampler.
    bgfx::TextureHandle m_shadowTexture = BGFX_INVALID_HANDLE;
    bgfx::FrameBufferHandle m_shadowFramebuffer = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_shadowSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_shadowMatricesUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_shadowParamsUniformHandle = BGFX_INVALID_HANDLE;
    std::array<ModelMatrix, ModelSunShadowCascades> m_shadowMatrices = {};
    std::array<std::array<float, 4>, 4> m_shadowParams = {};
    uint16_t m_shadowSize = 0;
    struct LodState
    {
        ModelInstanceHandle owner;
        uint32_t color = 0;
        std::array<uint32_t, ModelSunShadowCascades> shadow = {};
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
    // Joint matrices of every skinned node in one RGBA32F texture (model_skin.sh): 128 joints per 512-texel row; a
    // skin keeps its rows while its instance lives and re-uploads them only when its pose changes.
    struct JointSlot
    {
        ModelInstanceHandle owner;
        uint32_t row = 0;
        uint32_t rows = 0;
        uint64_t revision = 0;
    };
    std::unordered_map<const ModelMatrix *, JointSlot> m_jointSlots;
    std::vector<uint8_t> m_jointRowsUsed;
    bgfx::TextureHandle m_jointPalette = BGFX_INVALID_HANDLE;
    // Counts palette reallocations (each resets every slot's upload).
    uint32_t m_jointPaletteGeneration = 0;
    bgfx::ProgramHandle m_skinnedInstancedProgramHandle = BGFX_INVALID_HANDLE;
    // Emissive-texture programs and their sampler, created on first use (ensureEmissivePrograms).
    std::function<ModelEmissivePrograms()> m_emissiveProgramLoader;
    std::function<bgfx::ProgramHandle()> m_shieldShellProgramLoader;
    bool m_shieldShellProgramAttempted = false;
    bgfx::ProgramHandle m_shieldShellProgram = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_shieldShellUniformHandle = BGFX_INVALID_HANDLE;
    bool m_emissiveProgramsAttempted = false;
    ModelEmissivePrograms m_emissivePrograms;
    bgfx::UniformHandle m_emissiveSamplerHandle = BGFX_INVALID_HANDLE;
    // Attachments drawn as static groups (one per model and variant), with each placement's carrier alongside; a
    // carrier keeps its LOD hysteresis and crossfade across frames. Colour LOD level per carrier from the last colour
    // pass (by instance index).
    std::vector<ModelStaticGroup> m_attachmentGroups;
    std::vector<std::vector<ModelInstanceHandle>> m_attachmentOwners;
    // Per attachment group: it holds static stand-ins (corpses) rather than carried items.
    std::vector<bool> m_attachmentStandIns;
    // The stand-in groups at the front of m_attachmentGroups, valid while these instances' stand-in revision holds.
    const ModelInstanceSystem *m_pStandInInstances = nullptr;
    uint64_t m_standInRevision = 0;
    size_t m_standInGroupCount = 0;
    std::unordered_map<uint32_t, uint32_t> m_instanceColorLevels;
    // Per carrier (by instance index): the farthest its attachments reach from their nodes, from its last placement.
    struct AttachmentReach
    {
        uint32_t generation = 0;
        float reach = 0.0f;
    };
    std::unordered_map<uint32_t, AttachmentReach> m_attachmentReach;
    // Attachment crossfades run on their own clock (seconds since this origin).
    double m_attachmentClockOrigin = double(std::chrono::duration<double>(
        std::chrono::steady_clock::now().time_since_epoch()).count());
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
    bgfx::UniformHandle m_scrollUniformHandle = BGFX_INVALID_HANDLE;
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
    LightGridBinding m_lightGridBinding;
    bgfx::UniformHandle m_sectorUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_glowUniformHandle = BGFX_INVALID_HANDLE;
    uint16_t m_glowView = UINT16_MAX;
    bool m_glowDrawn = false;
    bgfx::UniformHandle m_surfaceUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_fogUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_skyFogUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_cameraUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_outlineUniformHandle = BGFX_INVALID_HANDLE;
    // u_modelEdge.x: the material's edge darkening (fs_model.sc).
    bgfx::UniformHandle m_edgeUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_materialUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_regionUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_regionMaskSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_regionRampSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_burnUniformHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_burnSamplerHandle = BGFX_INVALID_HANDLE;
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
