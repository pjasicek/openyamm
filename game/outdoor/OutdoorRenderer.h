#pragma once

#include "game/maps/MapAssetLoader.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorWorldRuntime.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ViewFrustum;
class OutdoorRenderer
{
public:
    static void destroySunReceiverResources(OutdoorGameView &view);
    static bool initializeWorldRenderResources(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const std::optional<std::vector<uint32_t>> &outdoorTileColors,
        const std::optional<OutdoorTerrainTiles> &outdoorTerrainTiles,
        const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet);
    static void invalidateSkyResources(OutdoorGameView &view);
    static void destroySkyResources(OutdoorGameView &view);
    // Sets u_skyFog for the following fog shaders (zero, i.e. flat fog, without an enhanced sky frame).
    static void applySkyFogUniform(const OutdoorGameView &view);
    // Loads the map's decoration models once (also on the first world pass); without them decorations are sprites.
    static void ensureDecorationModels(OutdoorGameView &view);

    static void renderWorldPasses(
        OutdoorGameView &view,
        uint16_t viewWidth,
        uint16_t viewHeight,
        float aspectRatio,
        float farClipDistance,
        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState,
        const bx::Vec3 &cameraPosition,
        const bx::Vec3 &cameraForward,
        const bx::Vec3 &cameraRight,
        const bx::Vec3 &cameraUp,
        const float *pViewMatrix,
        const float *pProjectionMatrix);

    static void renderOutdoorGameplayOverlay(
        OutdoorGameView &view,
        uint16_t viewId,
        float overlayAlpha,
        uint32_t overlayColorAbgr);

    static void renderActorCollisionOverlays(
        OutdoorGameView &view,
        uint16_t viewId,
        const bx::Vec3 &cameraPosition);

private:
    static bool initializeWaterResources(OutdoorGameView &view, const OutdoorMapData &mapData,
        const OutdoorTerrainTiles &terrainTiles);
    static void renderWaterReflections(OutdoorGameView &view, const float *pProjection,
        const bx::Vec3 &cameraPosition, const bx::Vec3 &cameraForward, const bx::Vec3 &cameraRight,
        const bx::Vec3 &cameraUp, float farClipDistance, const OutdoorLightingRuntime &bModelLighting,
        const OutdoorSelectedFxLights &globalBModelLights, bool useLocalBModelLighting);
    // Shared lighting of the frame's 3D models: creatures (per-model terms from creatureModelLighting) and decoration
    // placements (which carry their own ambient light and sun visibility).
    struct ModelSceneLighting
    {
        Engine::ModelRenderLighting creatures;
        Engine::ModelRenderLighting decorations;
        std::optional<Engine::ModelSkyEnvironment> sky;
        // Linear multiplier of the sky reflection, per channel.
        std::array<float, 3> skyTint = {1.0f, 1.0f, 1.0f};
    };
    static ModelSceneLighting modelSceneLighting(OutdoorGameView &view,
        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState, const OutdoorLightingData *pLightingData,
        float farClipDistance);
    // A creature's lighting: baked probes (sampled at most a few creatures per frame), sky and, without the view's
    // light grid (water reflections), its nearby lights.
    static Engine::ModelRenderLighting creatureModelLighting(OutdoorGameView &view, const ModelSceneLighting &scene,
        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState, const OutdoorLightingData *pLightingData,
        Engine::ModelInstanceHandle instance, const Engine::ModelBounds &modelBounds, uint32_t &modelProbeSamples,
        bool selectPointLights);
    // The light on a model at the eye (the first-person view model's): creatureModelLighting's at that point, with its
    // own probe cache and the nearest lights as a list.
    static Engine::ModelRenderLighting eyeModelLighting(OutdoorGameView &view, const ModelSceneLighting &scene,
        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState, const OutdoorLightingData *pLightingData,
        const std::array<float, 3> &eye);
    // Whether a resolved bmodel group has a texture to draw this frame, and which animation frame (arrayed groups and
    // arrayed materials are single-frame).
    static bool resolvedBModelGroupFrame(const OutdoorGameView &view,
        const OutdoorGameView::ResolvedBModelDrawGroup &group, uint32_t elapsedTicks, size_t &frameIndex);
    // The view's light grid for a world surface draw: its dynamic lights in the main camera's views; other cameras
    // (water reflections) and surfaces without it bind none and take their uniform list.
    static void bindLightGrid(OutdoorGameView &view, bool mainCamera);
    static void submitResolvedBModelDrawGroup(OutdoorGameView &view,
        const OutdoorGameView::ResolvedBModelDrawGroup &group, uint16_t viewId, size_t frameIndex, uint32_t transform);
    // Binds a lightmapped group's (or a runtime batch's) surface material maps and their uniforms; false when it
    // draws without them (none, animated, or the setting is off). `arrayIndex` >= 0: the faces' size array (layers
    // per vertex); else the animation's own maps.
    static bool bindSurfaceMaterial(OutdoorGameView &view, int32_t arrayIndex, uint16_t lightmapPageIndex,
        const OutdoorGameView::BModelTextureAnimationHandle *pAnimation, size_t frameIndex, uint16_t viewId);
    static void ensureTerrainDecorations(OutdoorGameView &view, const OutdoorMapData &outdoorMapData);
    // Builds the map's terrain from its materials once; false (with the error printed) when they cannot load.
    static bool ensureTerrainMaterials(OutdoorGameView &view);
    // Draws the terrain's visible chunks into viewId; openWater also draws water cells without a seabed. A water
    // reflection draws every triangle with one material and no anti-tiling: blends and detail are lost in its ripples.
    // The main view's dynamic lights come from the light grid, a reflection's from the shared uniform list.
    static void submitTerrainMaterials(OutdoorGameView &view, uint16_t viewId, const ViewFrustum &frustum,
        const bx::Vec3 &cameraPosition, bool openWater, bool sunShadows, bool reflection);
    // Light (baked probes, as decoration models) and distance fade of the low bushes placed with the grass.
    static void updateTerrainBushes(OutdoorGameView &view, const OutdoorLightingData *pBakedLighting,
        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState, const std::array<float, 3> &camera);
    // Event visibility and light of each decoration-model placement for this frame. Baked probes are sampled once.
    static void updateDecorationModels(OutdoorGameView &view, const OutdoorLightingData *pBakedLighting,
        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState);
    static std::vector<OutdoorGameView::TerrainVertex> buildTerrainVertices(const OutdoorMapData &mapData);
    static std::vector<uint16_t> buildTerrainIndices();
    // Two triangles per liquid cell (the native corners), for the liquid renderer's terrain surfaces.
    static std::vector<OutdoorGameView::TexturedTerrainVertex> buildTerrainLiquidVertices(
        const OutdoorMapData &mapData,
        const OutdoorTerrainTiles &terrainTiles);
    static std::vector<OutdoorGameView::TexturedTerrainVertex> buildTexturedBModelFaceVertices(
        const OutdoorMapData &mapData,
        size_t bModelIndex,
        size_t faceIndex,
        int textureWidth,
        int textureHeight,
        bool useLightmaps);
    static std::vector<OutdoorGameView::LightmappedBModelVertex> buildLightmappedBModelFaceVertices(
        const OutdoorMapData &mapData,
        size_t bModelIndex,
        size_t faceIndex,
        const std::vector<OutdoorGameView::TexturedTerrainVertex> &vertices);
    static std::vector<OutdoorGameView::TerrainVertex> buildFilledTerrainVertices(
        const OutdoorMapData &mapData,
        const std::optional<std::vector<uint32_t>> &tileColors,
        const OutdoorTerrainTiles *pTerrainTiles);
    static std::vector<OutdoorGameView::TerrainVertex> buildBModelWireframeVertices(const OutdoorMapData &mapData);
    static std::vector<OutdoorGameView::TerrainVertex> buildBModelCollisionFaceVertices(
        const OutdoorMapData &mapData);
    static std::vector<OutdoorGameView::TerrainVertex> buildEntityMarkerVertices(const OutdoorMapData &mapData);
    static std::vector<OutdoorGameView::TerrainVertex> buildSpawnMarkerVertices(const OutdoorMapData &mapData);
    static bgfx::ShaderHandle loadShaderHandle(const char *pShaderName);
    static bgfx::ProgramHandle loadProgramHandle(const char *pVertexShaderName, const char *pFragmentShaderName);
    static void createBModelTextureBatches(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet);
    static void applyOutdoorSurfaceUniforms(OutdoorGameView &view);
    // Advances the Enhanced sky state for this frame; Classic leaves it inactive.
    static void updateEnhancedSky(OutdoorGameView &view, const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState);
    static void updateWeather(OutdoorGameView &view, const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState);
    static void renderWeather(OutdoorGameView &view, uint16_t viewId,
        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState, const bx::Vec3 &cameraPosition,
        const float *pProjectionMatrix, uint16_t viewHeight);
    static void bindBakedSunShadows(OutdoorGameView &view, uint32_t sunPageIndex);
    // The bake's direct-only sun page for a sun page index (decoded on first use); invalid for pre-v5 bakes.
    static bgfx::TextureHandle bakedSunDirectTexture(OutdoorGameView &view, uint32_t sunPageIndex);
    static void ensureSunShadowPrograms(OutdoorGameView &view);
    // The alpha-to-coverage variants of the grass and foliage-prepass programs, loaded the first time anti-aliasing is
    // on; returns whether this frame's world target takes alpha to coverage.
    static bool ensureAlphaToCoveragePrograms(OutdoorGameView &view);
    static void applyOutdoorFxLightUniforms(OutdoorGameView &view, const bx::Vec3 &cameraPosition);
    static void destroyResolvedBModelDrawGroups(OutdoorGameView &view);
    // Loads the textures events swap onto faces (evt.SetTexture) that no face of the map uses, as 2D textures.
    static void ensureSwapTextures(OutdoorGameView &view, const EventRuntimeState *pEventRuntimeState);
    static void rebuildResolvedBModelDrawGroups(OutdoorGameView &view);
    static void destroyBModelWorldRenderChunks(OutdoorGameView &view);
    static bool buildBModelWorldRenderChunks(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const OutdoorBModelTextureSet &outdoorBModelTextureSet);
    static void refreshBModelWorldRenderChunks(OutdoorGameView &view);
    static bgfx::TextureHandle ensureBloodSplatTexture(OutdoorGameView &view);
    static void ensureBloodSplatVertexBuffer(OutdoorGameView &view);
    static void renderBloodSplats(
        OutdoorGameView &view,
        uint16_t viewId,
        const bx::Vec3 &cameraPosition,
        float farClipDistance,
        bool useLocalFxLighting);
    static void renderContextActionGeometryHighlight(OutdoorGameView &view, uint16_t viewId);
    static void renderPendingSpellAreaPreview(OutdoorGameView &view, uint16_t viewId, const bx::Vec3 &cameraPosition);
};
} // namespace OpenYAMM::Game
