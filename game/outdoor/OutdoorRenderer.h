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
        const std::string &textureName);
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
        const float *pViewMatrix);

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

    static void renderOutdoorDarknessOverlay(
        OutdoorGameView &view,
        uint16_t viewId,
        const bx::Vec3 &cameraPosition,
        const bx::Vec3 &cameraForward,
        const bx::Vec3 &cameraRight,
        const bx::Vec3 &cameraUp,
        float aspectRatio,
        float overlayAlpha,
        uint32_t overlayColorAbgr);

    static void renderActorCollisionOverlays(
        OutdoorGameView &view,
        uint16_t viewId,
        const bx::Vec3 &cameraPosition);

private:
    static void initializeAnimatedWaterTileState(
        OutdoorGameView &view,
        const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas);
    static void updateAnimatedWaterTileTexture(OutdoorGameView &view);
    static std::vector<OutdoorGameView::TerrainVertex> buildTerrainVertices(const OutdoorMapData &mapData);
    static std::vector<uint16_t> buildTerrainIndices();
    static std::vector<OutdoorGameView::TexturedTerrainVertex> buildTexturedTerrainVertices(
        const OutdoorMapData &mapData,
        const OutdoorTerrainTextureAtlas &textureAtlas);
    static std::vector<OutdoorGameView::TexturedTerrainVertex> buildTexturedBModelFaceVertices(
        const OutdoorMapData &mapData,
        size_t bModelIndex,
        size_t faceIndex,
        int textureWidth,
        int textureHeight);
    static std::vector<OutdoorGameView::TerrainVertex> buildFilledTerrainVertices(
        const OutdoorMapData &mapData,
        const std::optional<std::vector<uint32_t>> &tileColors);
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
    static void destroyResolvedBModelDrawGroups(OutdoorGameView &view);
    static void rebuildResolvedBModelDrawGroups(OutdoorGameView &view);
};
} // namespace OpenYAMM::Game
