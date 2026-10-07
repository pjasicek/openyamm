#pragma once

#include <bgfx/bgfx.h>

namespace OpenYAMM::Game
{
// Owns world post-processing targets; solid geometry precedes optional AO, transparencies and grading.
class CinematicGrading
{
public:
    bool begin(int width, int height, bool enabled, int strength, bool ambientOcclusion = false, int aoStrength = 35);
    void prepareWorldView(const float *pView, const float *pProjection);
    uint16_t transparentView(uint16_t worldView) const;
    void submit(bgfx::FrameBufferHandle target = BGFX_INVALID_HANDLE);
    void setOutputFrameBuffer(bgfx::FrameBufferHandle target);
    void resetViews();
    void shutdown();

private:
    bool initialize();
    bool resize(uint16_t width, uint16_t height, bool ambientOcclusion);
    bool initializeAmbientOcclusion();
    void destroyTargets();
    void submitAmbientOcclusion();

    bgfx::FrameBufferHandle m_frameBuffer = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_program = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_lut = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_sceneSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_lutSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_params = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_aoProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_aoBlurProgram = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_aoCompositeProgram = BGFX_INVALID_HANDLE;
    bgfx::FrameBufferHandle m_aoFrameBuffer = BGFX_INVALID_HANDLE;
    bgfx::FrameBufferHandle m_aoBlurFrameBuffer = BGFX_INVALID_HANDLE;
    bgfx::FrameBufferHandle m_aoCompositeFrameBuffer = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_depthSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_aoSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_aoProjection = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_aoInverseProjection = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_aoParams = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_aoDepthParams = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_aoTexel = BGFX_INVALID_HANDLE;
    float m_projection[16] = {};
    float m_inverseProjection[16] = {};
    bgfx::VertexLayout m_vertexLayout;
    bgfx::TransientVertexBuffer m_vertices = {};
    uint16_t m_width = 0;
    uint16_t m_height = 0;
    float m_strength = 0.0f;
    float m_aoStrength = 0.0f;
    bool m_aoTargets = false;
    bool m_aoActive = false;
    bool m_aoPrepared = false;
    bool m_aoUnsupportedLogged = false;
    bool m_active = false;
    bool m_failed = false;
};
}
