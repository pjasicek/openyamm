#pragma once

#include "game/render/CinematicGrading.h"

#include <bgfx/bgfx.h>

namespace OpenYAMM::Game
{
// The screen-space reflection inputs of the surface material shaders (surface_material.sh): the previous frame's
// reflection history (CinematicGrading::ReflectionHistory) at samplers 9 and 10 with its view, or the off switch.
class SurfaceReflectionBinding
{
public:
    bool create();
    // destroyGpu false forgets the handles (the bgfx context is already gone).
    void destroy(bool destroyGpu = true);
    // Binds the history for the next draw; a null history turns tracing off and binds a 1x1 placeholder, since
    // backends need every declared sampler bound.
    void bind(const CinematicGrading::ReflectionHistory *pHistory) const;

private:
    bgfx::UniformHandle m_colorSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_positionSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_viewProjection = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_camera = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_switch = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_placeholder = BGFX_INVALID_HANDLE;
};
}
