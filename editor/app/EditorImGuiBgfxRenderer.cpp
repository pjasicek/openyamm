#include "editor/app/EditorImGuiBgfxRenderer.h"

#include <imgui.h>
#include <bgfx/embedded_shader.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <cstdint>

#include "vs_ocornut_imgui.bin.h"
#include "fs_ocornut_imgui.bin.h"

namespace OpenYAMM::Editor
{
namespace
{
constexpr bgfx::ViewId ImGuiViewId = 250;

static const std::array<bgfx::EmbeddedShader, 3> EmbeddedShaders = {{
    BGFX_EMBEDDED_SHADER(vs_ocornut_imgui),
    BGFX_EMBEDDED_SHADER(fs_ocornut_imgui),
    BGFX_EMBEDDED_SHADER_END()
}};
}

bgfx::VertexLayout EditorImGuiBgfxRenderer::createVertexLayout()
{
    bgfx::VertexLayout layout;
    layout.begin()
        .add(bgfx::Attrib::Position, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
    return layout;
}

bool EditorImGuiBgfxRenderer::initialize()
{
    if (m_initialized)
    {
        return true;
    }

    m_vertexLayout = createVertexLayout();

    const bgfx::RendererType::Enum rendererType = bgfx::getRendererType();
    const bgfx::ShaderHandle vertexShaderHandle =
        bgfx::createEmbeddedShader(EmbeddedShaders.data(), rendererType, "vs_ocornut_imgui");
    const bgfx::ShaderHandle fragmentShaderHandle =
        bgfx::createEmbeddedShader(EmbeddedShaders.data(), rendererType, "fs_ocornut_imgui");

    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        if (bgfx::isValid(vertexShaderHandle))
        {
            bgfx::destroy(vertexShaderHandle);
        }

        if (bgfx::isValid(fragmentShaderHandle))
        {
            bgfx::destroy(fragmentShaderHandle);
        }

        return false;
    }

    m_programHandle = bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
    m_textureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);

    if (!bgfx::isValid(m_programHandle) || !bgfx::isValid(m_textureSamplerHandle))
    {
        shutdown();
        return false;
    }

    ImGuiIO &io = ImGui::GetIO();
    unsigned char *pPixels = nullptr;
    int textureWidth = 0;
    int textureHeight = 0;
    io.Fonts->GetTexDataAsRGBA32(&pPixels, &textureWidth, &textureHeight);

    if (pPixels == nullptr || textureWidth <= 0 || textureHeight <= 0)
    {
        shutdown();
        return false;
    }

    m_fontTextureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(textureWidth),
        static_cast<uint16_t>(textureHeight),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        0,
        bgfx::copy(pPixels, static_cast<uint32_t>(textureWidth * textureHeight * 4)));

    if (!bgfx::isValid(m_fontTextureHandle))
    {
        shutdown();
        return false;
    }

    io.Fonts->SetTexID(static_cast<ImTextureID>(m_fontTextureHandle.idx + 1));
    io.BackendRendererName = "openyamm_imgui_bgfx";
    io.BackendFlags |= ImGuiBackendFlags_RendererHasVtxOffset;
    m_initialized = true;
    return true;
}

void EditorImGuiBgfxRenderer::shutdown()
{
    if (bgfx::isValid(m_fontTextureHandle))
    {
        bgfx::destroy(m_fontTextureHandle);
        m_fontTextureHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_textureSamplerHandle))
    {
        bgfx::destroy(m_textureSamplerHandle);
        m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_programHandle))
    {
        bgfx::destroy(m_programHandle);
        m_programHandle = BGFX_INVALID_HANDLE;
    }

    m_initialized = false;
}

void EditorImGuiBgfxRenderer::newFrame()
{
}

void EditorImGuiBgfxRenderer::renderDrawData(const ImDrawData *pDrawData)
{
    if (!m_initialized || pDrawData == nullptr)
    {
        return;
    }

    const int framebufferWidth =
        static_cast<int>(pDrawData->DisplaySize.x * pDrawData->FramebufferScale.x);
    const int framebufferHeight =
        static_cast<int>(pDrawData->DisplaySize.y * pDrawData->FramebufferScale.y);

    if (framebufferWidth <= 0 || framebufferHeight <= 0)
    {
        return;
    }

    const bgfx::Caps *pCaps = bgfx::getCaps();
    float projectionMatrix[16];
    bx::mtxOrtho(
        projectionMatrix,
        pDrawData->DisplayPos.x,
        pDrawData->DisplayPos.x + pDrawData->DisplaySize.x,
        pDrawData->DisplayPos.y + pDrawData->DisplaySize.y,
        pDrawData->DisplayPos.y,
        0.0f,
        1000.0f,
        0.0f,
        pCaps->homogeneousDepth);

    bgfx::setViewName(ImGuiViewId, "EditorImGui");
    bgfx::setViewMode(ImGuiViewId, bgfx::ViewMode::Sequential);
    bgfx::setViewRect(
        ImGuiViewId,
        0,
        0,
        static_cast<uint16_t>(framebufferWidth),
        static_cast<uint16_t>(framebufferHeight));
    bgfx::setViewTransform(ImGuiViewId, nullptr, projectionMatrix);
    bgfx::touch(ImGuiViewId);

    for (int commandListIndex = 0; commandListIndex < pDrawData->CmdListsCount; ++commandListIndex)
    {
        const ImDrawList *pDrawList = pDrawData->CmdLists[commandListIndex];
        const uint32_t vertexCount = static_cast<uint32_t>(pDrawList->VtxBuffer.size());
        const uint32_t indexCount = static_cast<uint32_t>(pDrawList->IdxBuffer.size());

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, m_vertexLayout) < vertexCount
            || bgfx::getAvailTransientIndexBuffer(indexCount, sizeof(ImDrawIdx) == 4) < indexCount)
        {
            break;
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::TransientIndexBuffer transientIndexBuffer = {};
        bgfx::allocTransientVertexBuffer(&transientVertexBuffer, vertexCount, m_vertexLayout);
        bgfx::allocTransientIndexBuffer(&transientIndexBuffer, indexCount, sizeof(ImDrawIdx) == 4);

        std::memcpy(transientVertexBuffer.data, pDrawList->VtxBuffer.Data, vertexCount * sizeof(ImDrawVert));
        std::memcpy(transientIndexBuffer.data, pDrawList->IdxBuffer.Data, indexCount * sizeof(ImDrawIdx));

        bgfx::Encoder *pEncoder = bgfx::begin();

        for (const ImDrawCmd &drawCommand : pDrawList->CmdBuffer)
        {
            if (drawCommand.UserCallback != nullptr)
            {
                drawCommand.UserCallback(pDrawList, &drawCommand);
                continue;
            }

            if (drawCommand.ElemCount == 0)
            {
                continue;
            }

            ImVec4 clipRect = drawCommand.ClipRect;
            clipRect.x = (clipRect.x - pDrawData->DisplayPos.x) * pDrawData->FramebufferScale.x;
            clipRect.y = (clipRect.y - pDrawData->DisplayPos.y) * pDrawData->FramebufferScale.y;
            clipRect.z = (clipRect.z - pDrawData->DisplayPos.x) * pDrawData->FramebufferScale.x;
            clipRect.w = (clipRect.w - pDrawData->DisplayPos.y) * pDrawData->FramebufferScale.y;

            if (clipRect.x >= framebufferWidth || clipRect.y >= framebufferHeight || clipRect.z <= 0.0f
                || clipRect.w <= 0.0f)
            {
                continue;
            }

            const uint16_t scissorX = static_cast<uint16_t>(std::max(clipRect.x, 0.0f));
            const uint16_t scissorY = static_cast<uint16_t>(std::max(clipRect.y, 0.0f));
            const uint16_t scissorWidth =
                static_cast<uint16_t>(std::max(clipRect.z - static_cast<float>(scissorX), 0.0f));
            const uint16_t scissorHeight =
                static_cast<uint16_t>(std::max(clipRect.w - static_cast<float>(scissorY), 0.0f));

            if (scissorWidth == 0 || scissorHeight == 0)
            {
                continue;
            }

            bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
            textureHandle.idx = m_fontTextureHandle.idx;

            const ImTextureID textureId = drawCommand.GetTexID();

            if (textureId != ImTextureID_Invalid)
            {
                const uint16_t handleIndex = static_cast<uint16_t>(static_cast<uintptr_t>(textureId) - 1);
                textureHandle.idx = handleIndex;
            }

            pEncoder->setScissor(scissorX, scissorY, scissorWidth, scissorHeight);
            pEncoder->setState(
                BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_MSAA
                | BGFX_STATE_BLEND_FUNC(BGFX_STATE_BLEND_SRC_ALPHA, BGFX_STATE_BLEND_INV_SRC_ALPHA));
            pEncoder->setTexture(0, m_textureSamplerHandle, textureHandle);
            pEncoder->setVertexBuffer(
                0,
                &transientVertexBuffer,
                static_cast<uint32_t>(drawCommand.VtxOffset),
                vertexCount - static_cast<uint32_t>(drawCommand.VtxOffset));
            pEncoder->setIndexBuffer(
                &transientIndexBuffer,
                static_cast<uint32_t>(drawCommand.IdxOffset),
                static_cast<uint32_t>(drawCommand.ElemCount));
            pEncoder->submit(ImGuiViewId, m_programHandle);
        }

        bgfx::end(pEncoder);
    }
}
}
