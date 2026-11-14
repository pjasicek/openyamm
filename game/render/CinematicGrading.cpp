#include "game/render/CinematicGrading.h"
#include "game/render/RuntimeShader.h"
#include "game/render/WaterMath.h"
#include "engine/BgfxContext.h"

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
constexpr bgfx::ViewId GradingView = WorldGradingView;
struct ScreenVertex
{
    float x, y, z, u, v;
};

// The sample count when the colour and depth targets can both be multisampled, else 0.
uint8_t supportedSamples(uint8_t samples, bgfx::TextureFormat::Enum depthFormat)
{
    constexpr uint16_t required = BGFX_CAPS_FORMAT_TEXTURE_FRAMEBUFFER_MSAA;
    const bgfx::Caps &caps = *bgfx::getCaps();
    return (caps.formats[bgfx::TextureFormat::RGBA8] & required) == required
        && (caps.formats[depthFormat] & required) == required ? samples : 0;
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
    m_params = bgfx::createUniform("u_gradeParams", bgfx::UniformType::Vec4);
    m_gradeBloomSampler = bgfx::createUniform("s_gradeBloom", bgfx::UniformType::Sampler);
    m_gradeBloom = bgfx::createUniform("u_gradeBloom", bgfx::UniformType::Vec4);
    const uint32_t black = 0;
    m_noBloom = bgfx::createTexture2D(1, 1, false, 1, bgfx::TextureFormat::RGBA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP, bgfx::copy(&black, sizeof(black)));
    m_vertexLayout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
    return bgfx::isValid(m_program) && bgfx::isValid(m_sceneSampler) && bgfx::isValid(m_params)
        && bgfx::isValid(m_gradeBloomSampler)
        && bgfx::isValid(m_gradeBloom) && bgfx::isValid(m_noBloom);
}

bool CinematicGrading::initializeAmbientOcclusion()
{
    if (bgfx::isValid(m_aoProgram))
    {
        return true;
    }
    m_aoDepthProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_ambient_occlusion_depth");
    m_aoProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_ambient_occlusion");
    m_aoBlurProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_ambient_occlusion_blur");
    m_aoCompositeProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_ambient_occlusion_composite");
    m_aoDepthMsaaProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_ambient_occlusion_depth_msaa");
    m_aoCompositeMsaaProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_ambient_occlusion_composite_msaa");
    m_depthSampler = bgfx::createUniform("s_aoDepth", bgfx::UniformType::Sampler);
    m_aoSampler = bgfx::createUniform("s_ao", bgfx::UniformType::Sampler);
    m_aoLinearDepthSampler = bgfx::createUniform("s_aoLinearDepth", bgfx::UniformType::Sampler);
    m_aoRay = bgfx::createUniform("u_aoRay", bgfx::UniformType::Vec4);
    m_aoInverseProjection = bgfx::createUniform("u_aoInverseProjection", bgfx::UniformType::Mat4);
    m_aoParams = bgfx::createUniform("u_aoParams", bgfx::UniformType::Vec4);
    m_aoDepthParams = bgfx::createUniform("u_aoDepthParams", bgfx::UniformType::Vec4);
    m_aoTexel = bgfx::createUniform("u_aoTexel", bgfx::UniformType::Vec4);
    return bgfx::isValid(m_aoDepthProgram) && bgfx::isValid(m_aoProgram) && bgfx::isValid(m_aoBlurProgram)
        && bgfx::isValid(m_aoCompositeProgram) && bgfx::isValid(m_aoDepthMsaaProgram)
        && bgfx::isValid(m_aoCompositeMsaaProgram) && bgfx::isValid(m_depthSampler) && bgfx::isValid(m_aoSampler)
        && bgfx::isValid(m_aoLinearDepthSampler) && bgfx::isValid(m_aoRay)
        && bgfx::isValid(m_aoInverseProjection) && bgfx::isValid(m_aoParams)
        && bgfx::isValid(m_aoDepthParams) && bgfx::isValid(m_aoTexel);
}

bool CinematicGrading::initializeReflections()
{
    if (bgfx::isValid(m_reflectionColorProgram))
    {
        return true;
    }
    m_reflectionColorProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_reflection_history_color");
    m_reflectionPositionProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_reflection_history_position");
    m_reflectionPositionMsaaProgram =
        loadRuntimeProgram("vs_cinematic_grading", "fs_reflection_history_position_msaa");
    m_reflectionSceneSampler = bgfx::createUniform("s_reflectionScene", bgfx::UniformType::Sampler);
    m_reflectionInverseView = bgfx::createUniform("u_reflectionInverseView", bgfx::UniformType::Mat4);
    m_reflectionHistoryCamera = bgfx::createUniform("u_reflectionHistoryCamera", bgfx::UniformType::Vec4);
    return bgfx::isValid(m_reflectionColorProgram) && bgfx::isValid(m_reflectionPositionProgram)
        && bgfx::isValid(m_reflectionPositionMsaaProgram) && bgfx::isValid(m_reflectionSceneSampler)
        && bgfx::isValid(m_reflectionInverseView) && bgfx::isValid(m_reflectionHistoryCamera);
}

bool CinematicGrading::initializeBloom()
{
    if (bgfx::isValid(m_bloomBlurProgram))
    {
        return true;
    }
    m_bloomDownsampleProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_bloom_downsample");
    m_bloomBlurProgram = loadRuntimeProgram("vs_cinematic_grading", "fs_bloom_blur");
    m_bloomSourceSampler = bgfx::createUniform("s_bloomSource", bgfx::UniformType::Sampler);
    m_bloomTexel = bgfx::createUniform("u_bloomTexel", bgfx::UniformType::Vec4);
    return bgfx::isValid(m_bloomDownsampleProgram) && bgfx::isValid(m_bloomBlurProgram)
        && bgfx::isValid(m_bloomSourceSampler) && bgfx::isValid(m_bloomTexel);
}

bool CinematicGrading::createBloomTargets()
{
    // The glow shares the world's depth attachment and sample count, so emitters drawn into it are hidden where the
    // world is in front of them.
    const uint64_t flags = BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP;
    const uint64_t msaa = m_samples == 4 ? BGFX_TEXTURE_RT_MSAA_X4 : m_samples == 2 ? BGFX_TEXTURE_RT_MSAA_X2 : 0;
    m_glowColor = bgfx::createTexture2D(m_width, m_height, false, 1, bgfx::TextureFormat::RGBA8,
        msaa != 0 ? (flags & ~BGFX_TEXTURE_RT_MASK) | msaa : flags);
    if (!bgfx::isValid(m_glowColor))
    {
        return false;
    }
    const bgfx::TextureHandle attachments[] = {m_glowColor, bgfx::getTexture(m_frameBuffer, 1)};
    m_glowFrameBuffer = bgfx::createFrameBuffer(2, attachments, false);
    const uint16_t halfWidth = uint16_t((m_width + 1) / 2);
    const uint16_t halfHeight = uint16_t((m_height + 1) / 2);
    for (bgfx::FrameBufferHandle &target : m_bloomFrameBuffers)
    {
        target = bgfx::createFrameBuffer(halfWidth, halfHeight, bgfx::TextureFormat::RGBA8, flags);
    }
    return bgfx::isValid(m_glowFrameBuffer) && bgfx::isValid(m_bloomFrameBuffers[0])
        && bgfx::isValid(m_bloomFrameBuffers[1]);
}

void CinematicGrading::destroyBloomTargets()
{
    for (bgfx::FrameBufferHandle *pHandle : {&m_glowFrameBuffer, &m_bloomFrameBuffers[0], &m_bloomFrameBuffers[1]})
    {
        if (bgfx::isValid(*pHandle))
        {
            bgfx::destroy(*pHandle);
        }
        *pHandle = BGFX_INVALID_HANDLE;
    }
    if (bgfx::isValid(m_glowColor))
    {
        bgfx::destroy(m_glowColor);
    }
    m_glowColor = BGFX_INVALID_HANDLE;
}

void CinematicGrading::destroyTargets()
{
    destroyBloomTargets();
    for (bgfx::FrameBufferHandle *pHandle : {&m_reflectionColorFrameBuffer, &m_reflectionPositionFrameBuffer})
    {
        if (bgfx::isValid(*pHandle))
        {
            bgfx::destroy(*pHandle);
        }
        *pHandle = BGFX_INVALID_HANDLE;
    }
    m_reflectionTargets = false;
    m_reflectionHistoryValid = false;
    // The composite shares the scene's colour attachment without owning it.
    for (bgfx::FrameBufferHandle handle : {m_aoCompositeFrameBuffer, m_aoBlurFrameBuffer,
        m_aoFrameBuffer, m_aoDepthFrameBuffer, m_frameBuffer})
    {
        if (bgfx::isValid(handle))
        {
            bgfx::destroy(handle);
        }
    }
    m_aoCompositeFrameBuffer = BGFX_INVALID_HANDLE;
    m_aoBlurFrameBuffer = BGFX_INVALID_HANDLE;
    m_aoFrameBuffer = BGFX_INVALID_HANDLE;
    m_aoDepthFrameBuffer = BGFX_INVALID_HANDLE;
    m_frameBuffer = BGFX_INVALID_HANDLE;
    m_width = 0;
    m_height = 0;
    m_samples = 0;
    m_aoTargets = false;
    m_aoMsaaDepth = false;
}

bool CinematicGrading::resize(uint16_t width, uint16_t height, bool ambientOcclusion, bool reflections,
    uint8_t samples)
{
    if (bgfx::isValid(m_frameBuffer) && width == m_width && height == m_height && ambientOcclusion == m_aoTargets
        && reflections == m_reflectionTargets && samples == m_samples)
    {
        return true;
    }
    // AO and reflections both read the world depth.
    const bool sampledDepth = ambientOcclusion || reflections;
    destroyTargets();
    const uint64_t flags = BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP;
    const uint64_t pointFlags = flags | BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT;
    // Multisampled attachments are resolved when the view moves on, so sampling them (the presentation pass, the AO
    // depth reads on OpenGL ES, see begin) sees one value per pixel. Without AO the depth is never sampled.
    const uint64_t msaa = samples == 4 ? BGFX_TEXTURE_RT_MSAA_X4 : samples == 2 ? BGFX_TEXTURE_RT_MSAA_X2 : 0;
    const uint64_t colorFlags = msaa != 0 ? (flags & ~BGFX_TEXTURE_RT_MASK) | msaa : flags;
    // Desktop OpenGL samples a multisampled depth directly (its first sample), which saves resolving it with a depth
    // blit each time a view leaves the world target (after the opaque world, after the transparencies, after the
    // glow: about 0.1 ms per frame at 1600x900 with 4x MSAA).
    const bool msaaDepth = sampledDepth && msaa != 0 && bgfx::getRendererType() == bgfx::RendererType::OpenGL;
    const uint64_t depthFlags = !sampledDepth ? BGFX_TEXTURE_RT_WRITE_ONLY | msaa
        : msaa != 0 ? (pointFlags & ~BGFX_TEXTURE_RT_MASK) | msaa | (msaaDepth ? BGFX_TEXTURE_MSAA_SAMPLE : 0)
        : pointFlags;
    const bgfx::TextureHandle attachments[] = {
        bgfx::createTexture2D(width, height, false, 1, bgfx::TextureFormat::RGBA8, colorFlags),
        bgfx::createTexture2D(width, height, false, 1,
            sampledDepth ? bgfx::TextureFormat::D32F : bgfx::TextureFormat::D24S8, depthFlags)
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
        m_aoDepthFrameBuffer = bgfx::createFrameBuffer(halfWidth, halfHeight, bgfx::TextureFormat::R32F, pointFlags);
        m_aoFrameBuffer = bgfx::createFrameBuffer(halfWidth, halfHeight, bgfx::TextureFormat::RG16F, pointFlags);
        m_aoBlurFrameBuffer = bgfx::createFrameBuffer(halfWidth, halfHeight, bgfx::TextureFormat::RG16F, pointFlags);
        // Detach depth while sampling it in the composite (avoids framebuffer feedback).
        m_aoCompositeFrameBuffer = bgfx::createFrameBuffer(1, attachments, false);
        if (!bgfx::isValid(m_aoDepthFrameBuffer) || !bgfx::isValid(m_aoFrameBuffer)
            || !bgfx::isValid(m_aoBlurFrameBuffer)
            || !bgfx::isValid(m_aoCompositeFrameBuffer))
        {
            destroyTargets();
            return false;
        }
    }
    if (reflections)
    {
        const uint16_t halfWidth = uint16_t((width + 1) / 2);
        const uint16_t halfHeight = uint16_t((height + 1) / 2);
        m_reflectionColorFrameBuffer = bgfx::createFrameBuffer(halfWidth, halfHeight, bgfx::TextureFormat::RGBA8,
            flags);
        m_reflectionPositionFrameBuffer = bgfx::createFrameBuffer(halfWidth, halfHeight,
            bgfx::TextureFormat::RGBA16F, pointFlags);
        if (!bgfx::isValid(m_reflectionColorFrameBuffer) || !bgfx::isValid(m_reflectionPositionFrameBuffer))
        {
            destroyTargets();
            return false;
        }
    }
    m_width = width;
    m_height = height;
    m_samples = samples;
    m_aoTargets = ambientOcclusion;
    m_reflectionTargets = reflections;
    m_aoMsaaDepth = msaaDepth;
    return bgfx::isValid(m_frameBuffer);
}

void CinematicGrading::resetViews()
{
    if (!Engine::BgfxContext::isBgfxInitialized())
    {
        return;
    }
    constexpr std::array<uint16_t, FirstPersonViewModelView + 1> order = worldRenderViewOrder(false);
    bgfx::setViewOrder(0, uint16_t(order.size()), order.data());
    if (!m_active)
    {
        return;
    }
    bgfx::setViewFrameBuffer(0, BGFX_INVALID_HANDLE);
    bgfx::setViewFrameBuffer(1, BGFX_INVALID_HANDLE);
    bgfx::setViewFrameBuffer(GradingView, BGFX_INVALID_HANDLE);
    if (m_bloomActive)
    {
        for (uint16_t view = WorldGlowView; view <= BloomBlurVerticalView; ++view)
        {
            bgfx::setViewFrameBuffer(view, BGFX_INVALID_HANDLE);
        }
    }
    if (m_aoActive)
    {
        for (uint16_t view = AmbientOcclusionDepthView; view <= WorldTransparentView; ++view)
        {
            bgfx::setViewFrameBuffer(view, BGFX_INVALID_HANDLE);
        }
    }
    if (m_reflectionActive)
    {
        bgfx::setViewFrameBuffer(ReflectionHistoryColorView, BGFX_INVALID_HANDLE);
        bgfx::setViewFrameBuffer(ReflectionHistoryPositionView, BGFX_INVALID_HANDLE);
    }
    m_active = false;
    m_aoActive = false;
    m_reflectionActive = false;
    m_reflectionPrepared = false;
    m_aoPrepared = false;
    m_bloomActive = false;
    m_alphaToCoverage = false;
}

bool CinematicGrading::begin(int width, int height, bool enabled, int strength, bool ambientOcclusion, int aoStrength,
    int sharpening, int antialiasing, bool bloom, int bloomStrength, bool reflections)
{
    const bool grading = enabled && strength > 0;
    const bool sharpen = sharpening > 0;
    bool ao = ambientOcclusion && aoStrength > 0;
    bool reflect = reflections;
    bool glow = bloom && bloomStrength > 0;
    uint8_t samples = antialiasing >= 4 ? 4 : antialiasing >= 2 ? 2 : 0;
#if defined(__ANDROID__)
    // Android renders without multisampling or ambient occlusion, and its menu offers neither: a phone crashed at the
    // highest video settings, which enable both.
    ao = false;
    reflect = false;
    samples = 0;
#endif
    m_alphaToCoverage = false;
    m_bloomActive = false;
    m_glowDrawn = false;
    m_reflectionActive = false;
    m_reflectionPrepared = false;
    if ((!grading && !sharpen && !ao && !glow && !reflect && samples == 0) || width <= 0 || height <= 0 || m_failed
        || bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        if (!grading && !sharpen && !ao && !glow && !reflect && samples == 0 && bgfx::isValid(m_frameBuffer))
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
            && (caps.formats[bgfx::TextureFormat::R32F] & required) == required
            && (caps.formats[bgfx::TextureFormat::RG16F] & required) == required;
        if (!ao && !m_aoUnsupportedLogged)
        {
            std::cerr << "Ambient occlusion unavailable: sampled D32F, R32F and RG16F render targets are required.\n";
            m_aoUnsupportedLogged = true;
        }
    }
    if (reflect)
    {
        constexpr uint16_t required = BGFX_CAPS_FORMAT_TEXTURE_2D | BGFX_CAPS_FORMAT_TEXTURE_FRAMEBUFFER;
        const bgfx::Caps &caps = *bgfx::getCaps();
        reflect = (caps.formats[bgfx::TextureFormat::D32F] & required) == required
            && (caps.formats[bgfx::TextureFormat::RGBA16F] & required) == required;
        if (!reflect && !m_reflectionUnsupportedLogged)
        {
            std::cerr << "Surface reflections unavailable: sampled D32F and RGBA16F render targets are required.\n";
            m_reflectionUnsupportedLogged = true;
        }
    }
    if (samples > 0)
    {
        // AO samples the depth: desktop OpenGL reads the first sample of the multisampled depth (resize), OpenGL ES
        // resolves it with a blit (allowed by cmake/patches/bgfx-gl-msaa-depth-resolve.patch); others resolve colour
        // only, so anti-aliasing takes priority.
        const bgfx::RendererType::Enum renderer = bgfx::getRendererType();
        const bool depthResolve = renderer == bgfx::RendererType::OpenGL || renderer == bgfx::RendererType::OpenGLES;
        if ((ao || reflect) && !depthResolve && supportedSamples(samples, bgfx::TextureFormat::D24S8) > 0)
        {
            ao = false;
            reflect = false;
            if (!m_aoMsaaLogged)
            {
                std::cerr << "Ambient occlusion and surface reflections are off while anti-aliasing is on: this "
                             "renderer cannot resolve multisampled depth.\n";
                m_aoMsaaLogged = true;
            }
        }
        samples = supportedSamples(samples, ao || reflect ? bgfx::TextureFormat::D32F : bgfx::TextureFormat::D24S8);
        if (samples == 0 && !m_msaaUnsupportedLogged)
        {
            std::cerr << "Anti-aliasing unavailable: multisampled RGBA8 and depth render targets are required.\n";
            m_msaaUnsupportedLogged = true;
        }
    }
    if (!ao && !grading && !sharpen && !glow && !reflect && samples == 0)
    {
        destroyTargets();
        return false;
    }
    if (!initialize() || ((ao || reflect) && !initializeAmbientOcclusion()) || (reflect && !initializeReflections())
        || !resize(uint16_t(width), uint16_t(height), ao, reflect, samples))
    {
        shutdown();
        m_failed = true;
        std::cerr << "World post-processing could not allocate its shaders or render targets.\n";
        return false;
    }
    if (glow && (!initializeBloom() || (!bgfx::isValid(m_glowFrameBuffer) && !createBloomTargets())))
    {
        // Bloom needs a second colour target sharing the world depth; without it the rest of the frame stays.
        destroyBloomTargets();
        glow = false;
        if (!m_bloomUnsupportedLogged)
        {
            std::cerr << "Bloom unavailable: the glow render targets could not be created.\n";
            m_bloomUnsupportedLogged = true;
        }
    }
    else if (!glow && bgfx::isValid(m_glowFrameBuffer))
    {
        destroyBloomTargets();
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
    const std::array<uint16_t, FirstPersonViewModelView + 1> order = worldRenderViewOrder(true, ao, glow, reflect);
    bgfx::setViewOrder(0, uint16_t(order.size()), order.data());
    bgfx::setViewFrameBuffer(0, m_frameBuffer);
    bgfx::setViewFrameBuffer(1, m_frameBuffer);
    // 70% reproduces the reference grade; higher values extend the same color adjustment.
    m_strength = grading ? float(std::clamp(strength, 0, 100)) / 70.0f : 0.0f;
    m_aoStrength = float(std::clamp(aoStrength, 0, 100)) / 100.0f;
    m_sharpening = float(std::clamp(sharpening, 0, 100)) / 100.0f;
    m_aoActive = ao;
    m_aoPrepared = false;
    m_reflectionActive = reflect;
    m_bloomActive = glow;
    // 50 % matches the approved mock-up's glow.
    m_bloomStrength = glow ? float(std::clamp(bloomStrength, 0, 100)) / 50.0f : 0.0f;
    m_active = true;
    m_alphaToCoverage = samples > 1 && (bgfx::getCaps()->supported & BGFX_CAPS_ALPHA_TO_COVERAGE) != 0;
    if (samples != m_loggedSamples)
    {
        if (samples > 0)
        {
            std::cout << "Anti-aliasing: " << int(samples) << "x MSAA, alpha to coverage "
                      << (m_alphaToCoverage ? "on" : "unsupported (cut-outs stay alpha tested)") << ".\n";
        }
        m_loggedSamples = samples;
    }
    return true;
}

void CinematicGrading::prepareWorldView(const float *pView, const float *pProjection)
{
    if (m_bloomActive)
    {
        bgfx::setViewName(WorldGlowView, "Bloom glow");
        bgfx::setViewFrameBuffer(WorldGlowView, m_glowFrameBuffer);
        bgfx::setViewRect(WorldGlowView, 0, 0, m_width, m_height);
        bgfx::setViewClear(WorldGlowView, BGFX_CLEAR_COLOR, 0x00000000);
        bgfx::setViewMode(WorldGlowView, bgfx::ViewMode::Sequential);
        bgfx::setViewTransform(WorldGlowView, pView, pProjection);
    }
    if (!m_aoActive && !m_reflectionActive)
    {
        return;
    }
    bx::mtxInverse(m_inverseProjection, pProjection);
    if (m_reflectionActive)
    {
        bx::mtxInverse(m_inverseView, pView);
        bx::mtxMul(m_frameViewProjection, pView, pProjection);
        m_frameCamera[0] = m_inverseView[12];
        m_frameCamera[1] = m_inverseView[13];
        m_frameCamera[2] = m_inverseView[14];
        m_frameCamera[3] = bgfx::getCaps()->originBottomLeft ? 1.0f : -1.0f;
        m_reflectionPrepared = true;
    }
    if (!m_aoActive)
    {
        return;
    }
    // Clip w is pProjection[11] * view z, so view xy = distance * (ndc * ray.xy + ray.zw).
    m_ray[0] = 1.0f / pProjection[0];
    m_ray[1] = 1.0f / pProjection[5];
    m_ray[2] = -pProjection[8] / (pProjection[11] * pProjection[0]);
    m_ray[3] = -pProjection[9] / (pProjection[11] * pProjection[5]);
    bgfx::setViewName(WorldTransparentView, "World transparencies after AO");
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
    const bgfx::FrameBufferHandle targets[] = {m_aoDepthFrameBuffer, m_aoFrameBuffer, m_aoBlurFrameBuffer,
        m_aoCompositeFrameBuffer};
    const bgfx::ProgramHandle programs[] = {m_aoMsaaDepth ? m_aoDepthMsaaProgram : m_aoDepthProgram, m_aoProgram,
        m_aoBlurProgram, m_aoMsaaDepth ? m_aoCompositeMsaaProgram : m_aoCompositeProgram};
    const char *names[] = {"SSAO linear depth", "SSAO half resolution", "SSAO depth-aware filter", "SSAO composite"};
    for (size_t pass = 0; pass < 4; ++pass)
    {
        const uint16_t view = uint16_t(AmbientOcclusionDepthView + pass);
        const bool composite = pass == 3;
        bgfx::setViewName(view, names[pass]);
        bgfx::setViewFrameBuffer(view, targets[pass]);
        bgfx::setViewRect(view, 0, 0, composite ? m_width : halfWidth, composite ? m_height : halfHeight);
        bgfx::setViewClear(view, BGFX_CLEAR_NONE);
        bgfx::setUniform(m_aoRay, m_ray);
        bgfx::setUniform(m_aoInverseProjection, m_inverseProjection);
        bgfx::setUniform(m_aoDepthParams, depthParams);
        bgfx::setUniform(m_aoParams, params);
        bgfx::setUniform(m_aoTexel, texel);
        if (pass == 0 || composite)
        {
            bgfx::setTexture(0, m_depthSampler, bgfx::getTexture(m_frameBuffer, 1));
        }
        if (pass == 1)
        {
            bgfx::setTexture(1, m_aoLinearDepthSampler, bgfx::getTexture(m_aoDepthFrameBuffer));
        }
        else if (pass != 0)
        {
            bgfx::setTexture(1, m_aoSampler, bgfx::getTexture(pass == 2 ? m_aoFrameBuffer : m_aoBlurFrameBuffer));
        }
        bgfx::setVertexBuffer(0, &m_vertices);
        const uint64_t state = BGFX_STATE_WRITE_RGB | (composite
            ? BGFX_STATE_BLEND_FUNC(BGFX_STATE_BLEND_ZERO, BGFX_STATE_BLEND_SRC_COLOR) : BGFX_STATE_WRITE_A);
        bgfx::setState(state);
        bgfx::submit(view, programs[pass]);
    }
}

void CinematicGrading::submitReflectionHistory()
{
    const uint16_t halfWidth = uint16_t((m_width + 1) / 2);
    const uint16_t halfHeight = uint16_t((m_height + 1) / 2);
    bgfx::setViewName(ReflectionHistoryColorView, "Reflection history colour");
    bgfx::setViewFrameBuffer(ReflectionHistoryColorView, m_reflectionColorFrameBuffer);
    bgfx::setViewRect(ReflectionHistoryColorView, 0, 0, halfWidth, halfHeight);
    bgfx::setViewClear(ReflectionHistoryColorView, BGFX_CLEAR_NONE);
    bgfx::setTexture(0, m_reflectionSceneSampler, bgfx::getTexture(m_frameBuffer));
    bgfx::setVertexBuffer(0, &m_vertices);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A);
    bgfx::submit(ReflectionHistoryColorView, m_reflectionColorProgram);

    const bgfx::Caps &caps = *bgfx::getCaps();
    const float depthParams[] = {caps.homogeneousDepth ? 2.0f : 1.0f,
        caps.homogeneousDepth ? -1.0f : 0.0f, caps.originBottomLeft ? 1.0f : -1.0f, 0.0f};
    const float texel[] = {1.0f / m_width, 1.0f / m_height, 1.0f / halfWidth, 1.0f / halfHeight};
    bgfx::setViewName(ReflectionHistoryPositionView, "Reflection history positions");
    bgfx::setViewFrameBuffer(ReflectionHistoryPositionView, m_reflectionPositionFrameBuffer);
    bgfx::setViewRect(ReflectionHistoryPositionView, 0, 0, halfWidth, halfHeight);
    bgfx::setViewClear(ReflectionHistoryPositionView, BGFX_CLEAR_NONE);
    bgfx::setUniform(m_aoInverseProjection, m_inverseProjection);
    bgfx::setUniform(m_aoDepthParams, depthParams);
    bgfx::setUniform(m_aoTexel, texel);
    bgfx::setUniform(m_reflectionInverseView, m_inverseView);
    bgfx::setUniform(m_reflectionHistoryCamera, m_frameCamera);
    bgfx::setTexture(0, m_depthSampler, bgfx::getTexture(m_frameBuffer, 1));
    bgfx::setVertexBuffer(0, &m_vertices);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A);
    bgfx::submit(ReflectionHistoryPositionView, m_aoMsaaDepth ? m_reflectionPositionMsaaProgram
                                                              : m_reflectionPositionProgram);

    // The next frame's faces trace this frame's world as it was seen now.
    m_reflectionHistory.color = bgfx::getTexture(m_reflectionColorFrameBuffer);
    m_reflectionHistory.position = bgfx::getTexture(m_reflectionPositionFrameBuffer);
    std::memcpy(m_reflectionHistory.viewProjection, m_frameViewProjection, sizeof(m_frameViewProjection));
    std::memcpy(m_reflectionHistory.camera, m_frameCamera, sizeof(m_frameCamera));
    m_reflectionHistoryValid = true;
}

const CinematicGrading::ReflectionHistory *CinematicGrading::reflectionHistory() const
{
    return m_reflectionActive && m_reflectionHistoryValid ? &m_reflectionHistory : nullptr;
}

void CinematicGrading::submitBloom()
{
    const uint16_t halfWidth = uint16_t((m_width + 1) / 2);
    const uint16_t halfHeight = uint16_t((m_height + 1) / 2);
    // Downsample the glow, then blur it horizontally and vertically at half resolution.
    const bgfx::TextureHandle sources[] = {m_glowColor, bgfx::getTexture(m_bloomFrameBuffers[0]),
        bgfx::getTexture(m_bloomFrameBuffers[1])};
    const bgfx::FrameBufferHandle targets[] = {m_bloomFrameBuffers[0], m_bloomFrameBuffers[1], m_bloomFrameBuffers[0]};
    const float texels[3][4] = {{1.0f / m_width, 1.0f / m_height, 0.0f, 0.0f}, {1.0f / halfWidth, 0.0f, 0.0f, 0.0f},
        {0.0f, 1.0f / halfHeight, 0.0f, 0.0f}};
    const char *names[] = {"Bloom downsample", "Bloom blur horizontal", "Bloom blur vertical"};
    for (size_t pass = 0; pass < 3; ++pass)
    {
        const uint16_t view = uint16_t(BloomDownsampleView + pass);
        bgfx::setViewName(view, names[pass]);
        bgfx::setViewFrameBuffer(view, targets[pass]);
        bgfx::setViewRect(view, 0, 0, halfWidth, halfHeight);
        bgfx::setViewClear(view, BGFX_CLEAR_NONE);
        bgfx::setUniform(m_bloomTexel, texels[pass]);
        bgfx::setTexture(0, m_bloomSourceSampler, sources[pass]);
        bgfx::setVertexBuffer(0, &m_vertices);
        bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A);
        bgfx::submit(view, pass == 0 ? m_bloomDownsampleProgram : m_bloomBlurProgram);
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
    // Without a glow draw this frame the glow view does not even clear: skip the chain and the composite.
    const bool bloom = m_bloomActive && m_glowDrawn;
    if (bloom)
    {
        submitBloom();
    }
    const bool filtered = m_strength > 0.0f || m_sharpening > 0.0f || bloom;
    bgfx::setViewName(GradingView, filtered ? "Cinematic grading" : "World presentation");
    bgfx::setViewFrameBuffer(GradingView, target);
    bgfx::setViewRect(GradingView, 0, 0, m_width, m_height);
    bgfx::setViewClear(GradingView, BGFX_CLEAR_NONE);
    const float params[4] = {m_strength, 0.0f, 0.0f, m_sharpening};
    bgfx::setUniform(m_params, params);
    bgfx::setTexture(0, m_sceneSampler, bgfx::getTexture(m_frameBuffer));
    const float bloomValues[4] = {bloom ? m_bloomStrength : 0.0f, 0.0f, 0.0f, 0.0f};
    bgfx::setUniform(m_gradeBloom, bloomValues);
    bgfx::setTexture(2, m_gradeBloomSampler, bloom ? bgfx::getTexture(m_bloomFrameBuffers[0]) : m_noBloom);
    bgfx::setVertexBuffer(0, &m_vertices);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A);
    bgfx::submit(GradingView, m_program);
    if (m_reflectionActive && m_reflectionPrepared)
    {
        submitReflectionHistory();
    }
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
    for (bgfx::ProgramHandle handle : {m_aoDepthProgram, m_aoProgram, m_aoBlurProgram, m_aoCompositeProgram,
             m_aoDepthMsaaProgram, m_aoCompositeMsaaProgram, m_bloomDownsampleProgram, m_bloomBlurProgram,
             m_reflectionColorProgram, m_reflectionPositionProgram, m_reflectionPositionMsaaProgram})
    {
        if (bgfx::isValid(handle))
        {
            bgfx::destroy(handle);
        }
    }
    for (bgfx::UniformHandle handle : {m_depthSampler, m_aoSampler, m_aoLinearDepthSampler, m_aoRay,
        m_aoInverseProjection, m_aoParams, m_aoDepthParams, m_aoTexel, m_bloomSourceSampler, m_bloomTexel,
        m_gradeBloomSampler, m_gradeBloom, m_reflectionSceneSampler, m_reflectionInverseView,
        m_reflectionHistoryCamera})
    {
        if (bgfx::isValid(handle))
        {
            bgfx::destroy(handle);
        }
    }
    m_aoDepthProgram = BGFX_INVALID_HANDLE;
    m_aoProgram = BGFX_INVALID_HANDLE;
    m_aoBlurProgram = BGFX_INVALID_HANDLE;
    m_aoCompositeProgram = BGFX_INVALID_HANDLE;
    m_aoDepthMsaaProgram = BGFX_INVALID_HANDLE;
    m_aoCompositeMsaaProgram = BGFX_INVALID_HANDLE;
    m_depthSampler = BGFX_INVALID_HANDLE;
    m_aoSampler = BGFX_INVALID_HANDLE;
    m_aoLinearDepthSampler = BGFX_INVALID_HANDLE;
    m_aoRay = BGFX_INVALID_HANDLE;
    m_aoInverseProjection = BGFX_INVALID_HANDLE;
    m_aoParams = BGFX_INVALID_HANDLE;
    m_aoDepthParams = BGFX_INVALID_HANDLE;
    m_aoTexel = BGFX_INVALID_HANDLE;
    m_bloomDownsampleProgram = BGFX_INVALID_HANDLE;
    m_bloomBlurProgram = BGFX_INVALID_HANDLE;
    m_reflectionColorProgram = BGFX_INVALID_HANDLE;
    m_reflectionPositionProgram = BGFX_INVALID_HANDLE;
    m_reflectionPositionMsaaProgram = BGFX_INVALID_HANDLE;
    m_reflectionSceneSampler = BGFX_INVALID_HANDLE;
    m_reflectionInverseView = BGFX_INVALID_HANDLE;
    m_reflectionHistoryCamera = BGFX_INVALID_HANDLE;
    m_bloomSourceSampler = BGFX_INVALID_HANDLE;
    m_bloomTexel = BGFX_INVALID_HANDLE;
    m_gradeBloomSampler = BGFX_INVALID_HANDLE;
    m_gradeBloom = BGFX_INVALID_HANDLE;
    if (bgfx::isValid(m_noBloom))
    {
        bgfx::destroy(m_noBloom);
    }
    m_noBloom = BGFX_INVALID_HANDLE;
    if (bgfx::isValid(m_program))
    {
        bgfx::destroy(m_program);
    }
    if (bgfx::isValid(m_sceneSampler))
    {
        bgfx::destroy(m_sceneSampler);
    }
    if (bgfx::isValid(m_params))
    {
        bgfx::destroy(m_params);
    }
    m_frameBuffer = BGFX_INVALID_HANDLE;
    m_program = BGFX_INVALID_HANDLE;
    m_sceneSampler = BGFX_INVALID_HANDLE;
    m_params = BGFX_INVALID_HANDLE;
    m_width = 0;
    m_height = 0;
    m_failed = false;
}
}
