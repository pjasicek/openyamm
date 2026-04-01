#pragma once

#include <bgfx/bgfx.h>
#include <bx/math.h>

namespace OpenYAMM::Game
{
class OutdoorGameView;

class OutdoorBillboardRenderer
{
public:
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
