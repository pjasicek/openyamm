#pragma once

#include "game/events/ScriptedEventProgram.h"
#include "game/outdoor/OutdoorGameView.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <cstddef>
#include <string>

namespace OpenYAMM::Game
{
class OutdoorBillboardRenderer
{
public:
    static void initializeBillboardResources(OutdoorGameView &view);
    static void queueEventSpellBillboardTextureWarmup(OutdoorGameView &view, const ScriptedEventProgram &eventProgram);
    static void queueRuntimeActorBillboardTextureWarmup(OutdoorGameView &view);
    static void preloadPendingSpriteFrameWarmupsParallel(OutdoorGameView &view);
    static void processPendingSpriteFrameWarmups(OutdoorGameView &view, size_t maxSpriteFrames);
    static const OutdoorGameView::BillboardTextureHandle *ensureSpriteBillboardTexture(
        OutdoorGameView &view,
        const std::string &textureName,
        int16_t paletteId);
    static void invalidateRenderAssets(OutdoorGameView &view);
    static void destroyRenderAssets(OutdoorGameView &view);
    static void renderDecorationBillboards(
        OutdoorGameView &view,
        uint16_t viewId,
        uint16_t viewWidth,
        uint16_t viewHeight,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition);
    static void renderActorPreviewBillboards(
        OutdoorGameView &view,
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition);
    static void renderRuntimeWorldItems(
        OutdoorGameView &view,
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition);
    static void renderRuntimeProjectiles(
        OutdoorGameView &view,
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition);
    static void renderFxContactShadows(
        OutdoorGameView &view,
        uint16_t viewId);
    static void renderFxGlowBillboards(
        OutdoorGameView &view,
        uint16_t viewId,
        const float *pViewMatrix);
    static void renderSpriteObjectBillboards(
        OutdoorGameView &view,
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition);

private:
    static void appendWorldQuadVertices(
        std::vector<OutdoorGameView::TerrainVertex> &vertices,
        const bx::Vec3 &center,
        const bx::Vec3 &right,
        const bx::Vec3 &up,
        uint32_t colorAbgr);
    static void submitColoredVertices(
        OutdoorGameView &view,
        uint16_t viewId,
        const std::vector<OutdoorGameView::TerrainVertex> &vertices,
        uint64_t renderState);
    static void appendLitBillboardVertices(
        std::vector<OutdoorGameView::LitBillboardVertex> &vertices,
        const bx::Vec3 &center,
        const bx::Vec3 &right,
        const bx::Vec3 &up,
        float u0,
        float u1,
        uint32_t lightContributionAbgr);
    static void writeLitBillboardVertices(
        OutdoorGameView::LitBillboardVertex *pVertices,
        const bx::Vec3 &center,
        const bx::Vec3 &right,
        const bx::Vec3 &up,
        float u0,
        float u1,
        uint32_t lightContributionAbgr);
    static uint32_t computeBillboardLightContributionAbgr(
        const OutdoorGameView &view,
        float x,
        float y,
        float z);
    static void applyBillboardAmbientUniform(OutdoorGameView &view);
};
} // namespace OpenYAMM::Game
