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
        float renderDistance);

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
    static void ensureTerrainDecorations(OutdoorGameView &view, const OutdoorMapData &outdoorMapData);
    static void initializeAnimatedWaterTileState(
        OutdoorGameView &view,
        const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas);
    static void updateAnimatedWaterTileTexture(OutdoorGameView &view);
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
    static void applyOutdoorMaterialSunUniforms(OutdoorGameView &view);
    static void applyBModelMaterialUniforms(OutdoorGameView &view, uint16_t materialId);
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
