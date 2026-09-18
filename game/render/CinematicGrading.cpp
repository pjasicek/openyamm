#include "game/render/CinematicGrading.h"
#include "game/render/RuntimeShader.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
constexpr bgfx::ViewId GradingView = 249;
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

bool CinematicGrading::resize(uint16_t width, uint16_t height)
{
    if (bgfx::isValid(m_frameBuffer) && width == m_width && height == m_height)
    {
        return true;
    }
    if (bgfx::isValid(m_frameBuffer))
    {
        bgfx::destroy(m_frameBuffer);
        m_frameBuffer = BGFX_INVALID_HANDLE;
    }
    const uint64_t flags = BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP;
    const bgfx::TextureHandle attachments[] = {
        bgfx::createTexture2D(width, height, false, 1, bgfx::TextureFormat::RGBA8, flags),
        bgfx::createTexture2D(width, height, false, 1, bgfx::TextureFormat::D24S8, BGFX_TEXTURE_RT_WRITE_ONLY)
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
    m_width = width;
    m_height = height;
    return bgfx::isValid(m_frameBuffer);
}

void CinematicGrading::resetViews()
{
    if (!m_active)
    {
        return;
    }
    bgfx::setViewFrameBuffer(0, BGFX_INVALID_HANDLE);
    bgfx::setViewFrameBuffer(1, BGFX_INVALID_HANDLE);
    bgfx::setViewOrder(0, GradingView + 1);
    m_active = false;
}

bool CinematicGrading::begin(int width, int height, bool enabled, int strength)
{
    if (!enabled || strength <= 0 || width <= 0 || height <= 0 || m_failed
        || bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return false;
    }
    if (!initialize() || !resize(uint16_t(width), uint16_t(height)))
    {
        shutdown();
        m_failed = true;
        std::cerr << "Cinematic grading could not allocate its shaders or render targets.\n";
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
    std::array<bgfx::ViewId, GradingView + 1> order = {};
    order[0] = 0;
    order[1] = 1;
    order[2] = GradingView;
    for (bgfx::ViewId i = 3; i <= GradingView; ++i)
    {
        order[i] = i - 1;
    }
    bgfx::setViewOrder(0, uint16_t(order.size()), order.data());
    bgfx::setViewFrameBuffer(0, m_frameBuffer);
    bgfx::setViewFrameBuffer(1, m_frameBuffer);
    // 70% reproduces the reference grade; higher values extend the same color adjustment.
    m_strength = float(std::clamp(strength, 0, 100)) / 70.0f;
    m_active = true;
    return true;
}

void CinematicGrading::submit()
{
    if (!m_active)
    {
        return;
    }
    bgfx::setViewName(GradingView, "Cinematic grading");
    bgfx::setViewFrameBuffer(GradingView, BGFX_INVALID_HANDLE);
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

void CinematicGrading::shutdown()
{
    resetViews();
    if (bgfx::isValid(m_frameBuffer))
    {
        bgfx::destroy(m_frameBuffer);
    }
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
