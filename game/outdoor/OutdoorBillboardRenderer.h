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
    static void renderSpriteObjectBillboards(
        OutdoorGameView &view,
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition);
};
} // namespace OpenYAMM::Game
