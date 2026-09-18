#pragma once

#include <bgfx/bgfx.h>

namespace OpenYAMM::Game
{
// World views 0/1 are composed before HUD view 2. Owns only the grading resources.
class CinematicGrading
{
public:
    bool begin(int width, int height, bool enabled, int strength);
    void submit();
    void resetViews();
    void shutdown();

private:
    bool initialize();
    bool resize(uint16_t width, uint16_t height);

    bgfx::FrameBufferHandle m_frameBuffer = BGFX_INVALID_HANDLE;
    bgfx::ProgramHandle m_program = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_lut = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_sceneSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_lutSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_params = BGFX_INVALID_HANDLE;
    bgfx::VertexLayout m_vertexLayout;
    bgfx::TransientVertexBuffer m_vertices = {};
    uint16_t m_width = 0;
    uint16_t m_height = 0;
    float m_strength = 0.0f;
    bool m_active = false;
    bool m_failed = false;
};
}
