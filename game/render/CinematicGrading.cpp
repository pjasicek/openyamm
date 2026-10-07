#include "game/render/CinematicGrading.h"
#include "game/render/RuntimeShader.h"
#include "game/render/WaterMath.h"
#include "engine/BgfxContext.h"

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
constexpr bgfx::ViewId GradingView = WorldGradingView;
constexpr uint16_t LutSize = 32;
struct ScreenVertex
{
    float x, y, z, u, v;
};

std::array<uint8_t, LutSize * LutSize * LutSize * 4> makeLut()
{
    std::array<uint8_t, LutSize * LutSize * LutSize * 4> pixels = {};
    for (uint16_t b = 0; b < LutSize; ++b)
    {
        for (uint16_t g = 0; g < LutSize; ++g)
        {
            for (uint16_t r = 0; r < LutSize; ++r)
            {
                std::array<float, 3> color = {float(r) / (LutSize - 1), float(g) / (LutSize - 1),
                    float(b) / (LutSize - 1)};
                // The existing world target is display-referred SDR, not scene-linear HDR.
                // Lift shadow/midtone detail while keeping black and white anchored. Work on
                // luminance so neutral stone stays neutral instead of gaining a split-tone tint.
                const float luminance = color[0] * 0.2126f + color[1] * 0.7152f + color[2] * 0.0722f;
                const float remaining = 1.0f - luminance;
                const float tone = luminance + 0.16f * luminance * remaining * remaining
                    - 0.06f * luminance * luminance * remaining;
                const float chroma = std::max({color[0], color[1], color[2]})
                    - std::min({color[0], color[1], color[2]});
                const float inverseChroma = 1.0f / std::max(chroma, 0.0001f);
                // Smooth hue weights mute orange roofs/earth more than red foliage. Greens and
                // blues receive smaller reductions; near-neutral colors fade out of the masks.
                const float orange = 4.0f * std::max(0.0f, color[0] - color[1])
                    * std::max(0.0f, color[1] - color[2]) * inverseChroma * inverseChroma;
                const float green = std::max(0.0f, color[1] - std::max(color[0], color[2])) * inverseChroma;
                const float blue = std::max(0.0f, color[2] - std::max(color[0], color[1])) * inverseChroma;
                const float hueWeight = std::min(chroma / 0.08f, 1.0f);
                const float saturation = 0.92f - hueWeight * (0.25f * orange + 0.10f * green + 0.08f * blue);
                for (float &channel : color)
                {
                    channel = tone + (channel - luminance) * saturation;
                }
                const size_t index = ((size_t(b) * LutSize + g) * LutSize + r) * 4;
                for (size_t c = 0; c < 3; ++c)
                {
                    pixels[index + c] = uint8_t(std::lround(std::clamp(color[c], 0.0f, 1.0f) * 255.0f));
                }
                pixels[index + 3] = 255;
            }
        }
    }
    return pixels;
}
}

bool CinematicGrading::initialize()
{
    if (bgfx::isValid(m_program))
    {
        return true;
    }
    m_program = loadRuntimeProgram("vs_cinematic_grading", "fs_cinematic_grading");
    m_sceneSampler = bgfx::createUniform("s_gradeScene", bgfx::UniformType::Sampler);
    m_lutSampler = bgfx::createUniform("s_gradeLut", bgfx::UniformType::Sampler);
    m_params = bgfx::createUniform("u_gradeParams", bgfx::UniformType::Vec4);
    const std::array<uint8_t, LutSize * LutSize * LutSize * 4> pixels = makeLut();
    m_lut = bgfx::createTexture3D(LutSize, LutSize, LutSize, false, bgfx::TextureFormat::RGBA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_SAMPLER_W_CLAMP,
        bgfx::copy(pixels.data(), uint32_t(pixels.size())));
    m_vertexLayout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
    return bgfx::isValid(m_program) && bgfx::isValid(m_lut) && bgfx::isValid(m_sceneSampler)
        && bgfx::isValid(m_lutSampler) && bgfx::isValid(m_params);
}

bool CinematicGrading::initializeAmbientOcclusion()
{
    if (bgfx::isValid(m_aoProgram))
    {
        return true;
    }
    m_aoProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_ambient_occlusion");
    m_aoBlurProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_ambient_occlusion_blur");
    m_aoCompositeProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_ambient_occlusion_composite");
    m_depthSampler = bgfx::createUniform("s_aoDepth", bgfx::UniformType::Sampler);
    m_aoSampler = bgfx::createUniform("s_ao", bgfx::UniformType::Sampler);
    m_aoProjection = bgfx::createUniform("u_aoProjection", bgfx::UniformType::Mat4);
    m_aoInverseProjection = bgfx::createUniform("u_aoInverseProjection", bgfx::UniformType::Mat4);
    m_aoParams = bgfx::createUniform("u_aoParams", bgfx::UniformType::Vec4);
    m_aoDepthParams = bgfx::createUniform("u_aoDepthParams", bgfx::UniformType::Vec4);
    m_aoTexel = bgfx::createUniform("u_aoTexel", bgfx::UniformType::Vec4);
    return bgfx::isValid(m_aoProgram) && bgfx::isValid(m_aoBlurProgram) && bgfx::isValid(m_aoCompositeProgram)
        && bgfx::isValid(m_depthSampler) && bgfx::isValid(m_aoSampler) && bgfx::isValid(m_aoProjection)
        && bgfx::isValid(m_aoInverseProjection) && bgfx::isValid(m_aoParams)
        && bgfx::isValid(m_aoDepthParams) && bgfx::isValid(m_aoTexel);
}

void CinematicGrading::destroyTargets()
{
    // The composite shares the scene's colour attachment without owning it.
    for (bgfx::FrameBufferHandle handle : {m_aoCompositeFrameBuffer, m_aoBlurFrameBuffer,
        m_aoFrameBuffer, m_frameBuffer})
    {
        if (bgfx::isValid(handle))
        {
            bgfx::destroy(handle);
        }
    }
    m_aoCompositeFrameBuffer = BGFX_INVALID_HANDLE;
    m_aoBlurFrameBuffer = BGFX_INVALID_HANDLE;
    m_aoFrameBuffer = BGFX_INVALID_HANDLE;
    m_frameBuffer = BGFX_INVALID_HANDLE;
    m_width = 0;
    m_height = 0;
    m_aoTargets = false;
}

bool CinematicGrading::resize(uint16_t width, uint16_t height, bool ambientOcclusion)
{
    if (bgfx::isValid(m_frameBuffer) && width == m_width && height == m_height && ambientOcclusion == m_aoTargets)
    {
        return true;
    }
    destroyTargets();
    const uint64_t flags = BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP;
    const uint64_t pointFlags = flags | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT;
    const bgfx::TextureHandle attachments[] = {
        bgfx::createTexture2D(width, height, false, 1, bgfx::TextureFormat::RGBA8, flags),
        bgfx::createTexture2D(width, height, false, 1,
            ambientOcclusion ? bgfx::TextureFormat::D32F : bgfx::TextureFormat::D24S8,
            ambientOcclusion ? pointFlags : BGFX_TEXTURE_RT_WRITE_ONLY)
    };
    if (!bgfx::isValid(attachments[0]) || !bgfx::isValid(attachments[1]))
    {
        for (bgfx::TextureHandle texture : attachments)
        {
            if (bgfx::isValid(texture))
            {
                bgfx::destroy(texture);
            }
        }
        return false;
    }
    m_frameBuffer = bgfx::createFrameBuffer(2, attachments, true);
    if (ambientOcclusion)
    {
        const uint16_t halfWidth = uint16_t((width + 1) / 2);
        const uint16_t halfHeight = uint16_t((height + 1) / 2);
        m_aoFrameBuffer = bgfx::createFrameBuffer(halfWidth, halfHeight, bgfx::TextureFormat::RG16F, pointFlags);
        m_aoBlurFrameBuffer = bgfx::createFrameBuffer(halfWidth, halfHeight, bgfx::TextureFormat::RG16F, pointFlags);
        // Detach depth while sampling it in the composite (avoids framebuffer feedback).
        m_aoCompositeFrameBuffer = bgfx::createFrameBuffer(1, attachments, false);
        if (!bgfx::isValid(m_aoFrameBuffer) || !bgfx::isValid(m_aoBlurFrameBuffer)
            || !bgfx::isValid(m_aoCompositeFrameBuffer))
        {
            destroyTargets();
            return false;
        }
    }
    m_width = width;
    m_height = height;
    m_aoTargets = ambientOcclusion;
    return bgfx::isValid(m_frameBuffer);
}

void CinematicGrading::resetViews()
{
    if (!Engine::BgfxContext::isBgfxInitialized())
    {
        return;
    }
    constexpr std::array<uint16_t, WorldGradingView + 1> order = worldRenderViewOrder(false);
    bgfx::setViewOrder(0, uint16_t(order.size()), order.data());
    if (!m_active)
    {
        return;
    }
    bgfx::setViewFrameBuffer(0, BGFX_INVALID_HANDLE);
    bgfx::setViewFrameBuffer(1, BGFX_INVALID_HANDLE);
    bgfx::setViewFrameBuffer(GradingView, BGFX_INVALID_HANDLE);
    if (m_aoActive)
    {
        for (uint16_t view = AmbientOcclusionView; view <= WorldTransparentView; ++view)
        {
            bgfx::setViewFrameBuffer(view, BGFX_INVALID_HANDLE);
        }
    }
    m_active = false;
    m_aoActive = false;
    m_aoPrepared = false;
}

bool CinematicGrading::begin(int width, int height, bool enabled, int strength, bool ambientOcclusion, int aoStrength)
{
    const bool grading = enabled && strength > 0;
    bool ao = ambientOcclusion && aoStrength > 0;
    if ((!grading && !ao) || width <= 0 || height <= 0 || m_failed
        || bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        if (!grading && !ao && bgfx::isValid(m_frameBuffer))
        {
            destroyTargets();
        }
        return false;
    }
    if (ao)
    {
        constexpr uint16_t required = BGFX_CAPS_FORMAT_TEXTURE_2D | BGFX_CAPS_FORMAT_TEXTURE_FRAMEBUFFER;
        const bgfx::Caps &caps = *bgfx::getCaps();
        ao = (caps.formats[bgfx::TextureFormat::D32F] & required) == required
            && (caps.formats[bgfx::TextureFormat::RG16F] & required) == required;
        if (!ao && !m_aoUnsupportedLogged)
        {
            std::cerr << "Ambient occlusion unavailable: sampled D32F and RG16F render targets are required.\n";
            m_aoUnsupportedLogged = true;
        }
        if (!ao && !grading)
        {
            destroyTargets();
            return false;
        }
    }
    if (!initialize() || (ao && !initializeAmbientOcclusion()) || !resize(uint16_t(width), uint16_t(height), ao))
    {
        shutdown();
        m_failed = true;
        std::cerr << "World post-processing could not allocate its shaders or render targets.\n";
        return false;
    }
    if (bgfx::getAvailTransientVertexBuffer(3, m_vertexLayout) != 3)
    {
        return false;
    }
    bgfx::allocTransientVertexBuffer(&m_vertices, 3, m_vertexLayout);
    const bool flip = bgfx::getCaps()->originBottomLeft;
    const ScreenVertex vertices[] = {
        {-1.0f, 1.0f, 0.0f, 0.0f, flip ? 1.0f : 0.0f},
        {3.0f, 1.0f, 0.0f, 2.0f, flip ? 1.0f : 0.0f},
        {-1.0f, -3.0f, 0.0f, 0.0f, flip ? -1.0f : 2.0f}
    };
    std::memcpy(m_vertices.data, vertices, sizeof(vertices));
    const std::array<uint16_t, WorldGradingView + 1> order = worldRenderViewOrder(true, ao);
    bgfx::setViewOrder(0, uint16_t(order.size()), order.data());
    bgfx::setViewFrameBuffer(0, m_frameBuffer);
    bgfx::setViewFrameBuffer(1, m_frameBuffer);
    // 70% reproduces the reference grade; higher values extend the same color adjustment.
    m_strength = grading ? float(std::clamp(strength, 0, 100)) / 70.0f : 0.0f;
    m_aoStrength = float(std::clamp(aoStrength, 0, 100)) / 100.0f;
    m_aoActive = ao;
    m_aoPrepared = false;
    m_active = true;
    return true;
}

void CinematicGrading::prepareWorldView(const float *pView, const float *pProjection)
{
    if (!m_aoActive)
    {
        return;
    }
    std::copy_n(pProjection, 16, m_projection);
    bx::mtxInverse(m_inverseProjection, pProjection);
    bgfx::setViewName(WorldTransparentView, "World sprites and effects after AO");
    bgfx::setViewFrameBuffer(WorldTransparentView, m_frameBuffer);
    bgfx::setViewRect(WorldTransparentView, 0, 0, m_width, m_height);
    bgfx::setViewClear(WorldTransparentView, BGFX_CLEAR_NONE);
    bgfx::setViewMode(WorldTransparentView, bgfx::ViewMode::Sequential);
    bgfx::setViewTransform(WorldTransparentView, pView, pProjection);
    m_aoPrepared = true;
}

uint16_t CinematicGrading::transparentView(uint16_t worldView) const
{
    return m_aoActive ? WorldTransparentView : worldView;
}

void CinematicGrading::submitAmbientOcclusion()
{
    const uint16_t halfWidth = uint16_t((m_width + 1) / 2);
    const uint16_t halfHeight = uint16_t((m_height + 1) / 2);
    const bgfx::Caps &caps = *bgfx::getCaps();
    const float depthParams[] = {caps.homogeneousDepth ? 2.0f : 1.0f,
        caps.homogeneousDepth ? -1.0f : 0.0f, caps.originBottomLeft ? 1.0f : -1.0f, 0.0f};
    const float texel[] = {1.0f / m_width, 1.0f / m_height, 1.0f / halfWidth, 1.0f / halfHeight};
    // Short radius supplements baked illumination; distant geometry does not need contact shading.
    const float params[] = {36.0f, 0.12f, m_aoStrength, 4096.0f};
    const bgfx::FrameBufferHandle targets[] = {m_aoFrameBuffer, m_aoBlurFrameBuffer, m_aoCompositeFrameBuffer};
    const bgfx::ProgramHandle programs[] = {m_aoProgram, m_aoBlurProgram, m_aoCompositeProgram};
    const char *names[] = {"SSAO half resolution", "SSAO depth-aware filter", "SSAO composite"};
    for (size_t pass = 0; pass < 3; ++pass)
    {
        const uint16_t view = uint16_t(AmbientOcclusionView + pass);
        bgfx::setViewName(view, names[pass]);
        bgfx::setViewFrameBuffer(view, targets[pass]);
        bgfx::setViewRect(view, 0, 0, pass == 2 ? m_width : halfWidth, pass == 2 ? m_height : halfHeight);
        bgfx::setViewClear(view, BGFX_CLEAR_NONE);
        bgfx::setUniform(m_aoProjection, m_projection);
        bgfx::setUniform(m_aoInverseProjection, m_inverseProjection);
        bgfx::setUniform(m_aoDepthParams, depthParams);
        bgfx::setUniform(m_aoParams, params);
        bgfx::setUniform(m_aoTexel, texel);
        bgfx::setTexture(0, m_depthSampler, bgfx::getTexture(m_frameBuffer, 1));
        if (pass != 0)
        {
            bgfx::setTexture(1, m_aoSampler, bgfx::getTexture(pass == 1 ? m_aoFrameBuffer : m_aoBlurFrameBuffer));
        }
        bgfx::setVertexBuffer(0, &m_vertices);
        const uint64_t state = BGFX_STATE_WRITE_RGB | (pass == 2
            ? BGFX_STATE_BLEND_FUNC(BGFX_STATE_BLEND_ZERO, BGFX_STATE_BLEND_SRC_COLOR) : BGFX_STATE_WRITE_A);
        bgfx::setState(state);
        bgfx::submit(view, programs[pass]);
    }
}

void CinematicGrading::submit(bgfx::FrameBufferHandle target)
{
    if (!m_active)
    {
        return;
    }
    if (m_aoActive && m_aoPrepared)
    {
        submitAmbientOcclusion();
    }
    bgfx::setViewName(GradingView, m_strength > 0.0f ? "Cinematic grading" : "World presentation");
    bgfx::setViewFrameBuffer(GradingView, target);
    bgfx::setViewRect(GradingView, 0, 0, m_width, m_height);
    bgfx::setViewClear(GradingView, BGFX_CLEAR_NONE);
    const float params[4] = {m_strength, float(LutSize - 1) / LutSize, 0.5f / LutSize, 0.0f};
    bgfx::setUniform(m_params, params);
    bgfx::setTexture(0, m_sceneSampler, bgfx::getTexture(m_frameBuffer));
    bgfx::setTexture(1, m_lutSampler, m_lut);
    bgfx::setVertexBuffer(0, &m_vertices);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A);
    bgfx::submit(GradingView, m_program);
}

void CinematicGrading::setOutputFrameBuffer(bgfx::FrameBufferHandle target)
{
    if (m_active)
    {
        bgfx::setViewFrameBuffer(GradingView, target);
    }
    else
    {
        bgfx::setViewFrameBuffer(0, target);
        bgfx::setViewFrameBuffer(1, target);
    }
}

void CinematicGrading::shutdown()
{
    resetViews();
    destroyTargets();
    for (bgfx::ProgramHandle handle : {m_aoProgram, m_aoBlurProgram, m_aoCompositeProgram})
    {
        if (bgfx::isValid(handle))
        {
            bgfx::destroy(handle);
        }
    }
    for (bgfx::UniformHandle handle : {m_depthSampler, m_aoSampler, m_aoProjection, m_aoInverseProjection,
        m_aoParams, m_aoDepthParams, m_aoTexel})
    {
        if (bgfx::isValid(handle))
        {
            bgfx::destroy(handle);
        }
    }
    m_aoProgram = BGFX_INVALID_HANDLE;
    m_aoBlurProgram = BGFX_INVALID_HANDLE;
    m_aoCompositeProgram = BGFX_INVALID_HANDLE;
    m_depthSampler = BGFX_INVALID_HANDLE;
    m_aoSampler = BGFX_INVALID_HANDLE;
    m_aoProjection = BGFX_INVALID_HANDLE;
    m_aoInverseProjection = BGFX_INVALID_HANDLE;
    m_aoParams = BGFX_INVALID_HANDLE;
    m_aoDepthParams = BGFX_INVALID_HANDLE;
    m_aoTexel = BGFX_INVALID_HANDLE;
    if (bgfx::isValid(m_program))
    {
        bgfx::destroy(m_program);
    }
    if (bgfx::isValid(m_lut))
    {
        bgfx::destroy(m_lut);
    }
    if (bgfx::isValid(m_sceneSampler))
    {
        bgfx::destroy(m_sceneSampler);
    }
    if (bgfx::isValid(m_lutSampler))
    {
        bgfx::destroy(m_lutSampler);
    }
    if (bgfx::isValid(m_params))
    {
        bgfx::destroy(m_params);
    }
    m_frameBuffer = BGFX_INVALID_HANDLE;
    m_program = BGFX_INVALID_HANDLE;
    m_lut = BGFX_INVALID_HANDLE;
    m_sceneSampler = BGFX_INVALID_HANDLE;
    m_lutSampler = BGFX_INVALID_HANDLE;
    m_params = BGFX_INVALID_HANDLE;
    m_width = 0;
    m_height = 0;
    m_failed = false;
}
}
