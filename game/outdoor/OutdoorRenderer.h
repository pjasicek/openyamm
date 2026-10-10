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
class OutdoorRenderer
{
public:
    static void destroySunReceiverResources(OutdoorGameView &view);
    static bool initializeWorldRenderResources(
        OutdoorGameView &view,
        const OutdoorMapData &outdoorMapData,
        const std::optional<std::vector<uint32_t>> &outdoorTileColors,
        const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas,
        const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet);
    static const OutdoorGameView::SkyTextureHandle *ensureSkyTexture(
        OutdoorGameView &view,
        const std::string &textureName,
        bool warnOnCacheMiss = true);
    static void invalidateSkyResources(OutdoorGameView &view);
    static void destroySkyResources(OutdoorGameView &view);
    // Sets u_skyFog for the following fog shaders (zero, i.e. flat fog, for Classic).
    static void applySkyFogUniform(const OutdoorGameView &view);

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

    static void renderOutdoorSky(
        OutdoorGameView &view,
        uint16_t viewId,
        uint16_t viewWidth,
        uint16_t viewHeight,
        const bx::Vec3 &cameraPosition,
        const bx::Vec3 &cameraForward,
        const bx::Vec3 &cameraRight,
        const bx::Vec3 &cameraUp,
        float renderDistance,
        bool reflection = false);

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
    static bool initializeWaterResources(OutdoorGameView &view,
        const std::vector<OutdoorGameView::TexturedTerrainVertex> &vertices,
        const OutdoorTerrainTextureAtlas &atlas);
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
    // A creature's lighting: baked probes (sampled at most a few creatures per frame), nearby lights and sky.
    static Engine::ModelRenderLighting creatureModelLighting(OutdoorGameView &view, const ModelSceneLighting &scene,
        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState, const OutdoorLightingData *pLightingData,
        Engine::ModelInstanceHandle instance, const Engine::ModelBounds &modelBounds, uint32_t &modelProbeSamples);
    // Whether a resolved bmodel group has a texture to draw this frame, and which animation frame (arrayed groups and
    // arrayed materials are single-frame).
    static bool resolvedBModelGroupFrame(const OutdoorGameView &view,
        const OutdoorGameView::ResolvedBModelDrawGroup &group, uint32_t elapsedTicks, size_t &frameIndex);
    static void submitResolvedBModelDrawGroup(OutdoorGameView &view,
        const OutdoorGameView::ResolvedBModelDrawGroup &group, uint16_t viewId, size_t frameIndex, uint32_t transform);
    static void ensureTerrainDecorations(OutdoorGameView &view, const OutdoorMapData &outdoorMapData);
    static void ensureDecorationModels(OutdoorGameView &view);
    // Event visibility and light of each decoration-model placement for this frame. Baked probes are sampled once.
    static void updateDecorationModels(OutdoorGameView &view, const OutdoorLightingData *pBakedLighting,
        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState);
    static void initializeAnimatedWaterTileState(
        OutdoorGameView &view,
        const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas);
    static void updateAnimatedWaterTileTexture(OutdoorGameView &view, bool enhancedWater);
    static std::vector<OutdoorGameView::TerrainVertex> buildTerrainVertices(const OutdoorMapData &mapData);
    static std::vector<uint16_t> buildTerrainIndices();
    static std::vector<OutdoorGameView::TexturedTerrainVertex> buildTexturedTerrainVertices(
        const OutdoorMapData &mapData,
        const OutdoorTerrainTextureAtlas &textureAtlas);
    static void destroyTexturedTerrainChunks(OutdoorGameView &view);
    static void buildTexturedTerrainChunks(
        OutdoorGameView &view,
        const std::vector<OutdoorGameView::TexturedTerrainVertex> &vertices);
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
        const OutdoorTerrainTextureAtlas *pTextureAtlas);
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
    static void ensureSunShadowPrograms(OutdoorGameView &view);
    static void applyOutdoorFxLightUniforms(OutdoorGameView &view, const bx::Vec3 &cameraPosition);
    static void destroyResolvedBModelDrawGroups(OutdoorGameView &view);
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
