#include "game/render/SurfaceReflectionBinding.h"

#include <array>

namespace OpenYAMM::Game
{
bool SurfaceReflectionBinding::create()
{
    m_colorSampler = bgfx::createUniform("s_reflectionColor", bgfx::UniformType::Sampler);
    m_positionSampler = bgfx::createUniform("s_reflectionPosition", bgfx::UniformType::Sampler);
    m_viewProjection = bgfx::createUniform("u_reflectionViewProjection", bgfx::UniformType::Mat4);
    m_camera = bgfx::createUniform("u_reflectionCamera", bgfx::UniformType::Vec4);
    m_switch = bgfx::createUniform("u_surfaceReflection", bgfx::UniformType::Vec4);
    const uint32_t black = 0;
    m_placeholder = bgfx::createTexture2D(1, 1, false, 1, bgfx::TextureFormat::RGBA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP, bgfx::copy(&black, sizeof(black)));
    return bgfx::isValid(m_colorSampler) && bgfx::isValid(m_positionSampler) && bgfx::isValid(m_viewProjection)
        && bgfx::isValid(m_camera) && bgfx::isValid(m_switch) && bgfx::isValid(m_placeholder);
}

void SurfaceReflectionBinding::destroy(bool destroyGpu)
{
    for (bgfx::UniformHandle *pHandle : {&m_colorSampler, &m_positionSampler, &m_viewProjection, &m_camera, &m_switch})
    {
        if (destroyGpu && bgfx::isValid(*pHandle))
        {
            bgfx::destroy(*pHandle);
        }
        *pHandle = BGFX_INVALID_HANDLE;
    }
    if (destroyGpu && bgfx::isValid(m_placeholder))
    {
        bgfx::destroy(m_placeholder);
    }
    m_placeholder = BGFX_INVALID_HANDLE;
}

void SurfaceReflectionBinding::bind(const CinematicGrading::ReflectionHistory *pHistory) const
{
    if (!bgfx::isValid(m_switch))
    {
        return;
    }
    const std::array<float, 4> enabled = {pHistory != nullptr ? 1.0f : 0.0f, 0.0f, 0.0f, 0.0f};
    bgfx::setUniform(m_switch, enabled.data());
    if (pHistory == nullptr)
    {
        bgfx::setTexture(9, m_colorSampler, m_placeholder);
        bgfx::setTexture(10, m_positionSampler, m_placeholder);
        return;
    }
    bgfx::setUniform(m_viewProjection, pHistory->viewProjection);
    bgfx::setUniform(m_camera, pHistory->camera);
    bgfx::setTexture(9, m_colorSampler, pHistory->color,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setTexture(10, m_positionSampler, pHistory->position,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT);
}
}
