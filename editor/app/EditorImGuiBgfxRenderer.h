#pragma once

#include <bgfx/bgfx.h>

struct ImDrawData;

namespace OpenYAMM::Editor
{
class EditorImGuiBgfxRenderer
{
public:
    bool initialize();
    void shutdown();
    void newFrame();
    void renderDrawData(const ImDrawData *pDrawData);

private:
    static bgfx::VertexLayout createVertexLayout();

    bgfx::ProgramHandle m_programHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    bgfx::VertexLayout m_vertexLayout;
    bgfx::TextureHandle m_fontTextureHandle = BGFX_INVALID_HANDLE;
    bool m_initialized = false;
};
}
