#include "game/render/SkyRenderer.h"

#include "engine/AssetFileSystem.h"
#include "engine/BgfxContext.h"
#include "engine/ImageAssetLoader.h"
#include "game/render/RuntimeShader.h"
#include "game/render/TextureFiltering.h"

#include <bx/math.h>

#include <algorithm>
#include <cmath>
#include <iostream>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *SkyLibraryPath = "engine/rendering/sky/sky.yml";
constexpr const char *SkyTextureDirectory = "engine/rendering/sky/";
constexpr float DegreesToRadians = 3.14159265358979323846f / 180.0f;
// The distant sea's haze reaches 63% at this distance along the view ray (about two map half-widths).
constexpr float SeaHazeDistance = 40000.0f;
// Keeps the sea's distance finite for a camera at or just below sea level.
constexpr float MinimumSeaViewHeight = 64.0f;
// Cloud layers kept loaded beyond the current frame's (a weather fade plus recently used skies).
constexpr size_t MaxCachedCloudTextures = 4;

enum SkySampler : uint8_t
{
    CloudSampler0 = 0,
    RingSampler = 4,
    StarsSampler = 5,
    MoonSampler = 6,
};

std::array<float, 4> vec4(const SkyColor &color, float w)
{
    return {color[0], color[1], color[2], w};
}

float belowHorizonMode(SkyBelowHorizon mode)
{
    switch (mode)
    {
        case SkyBelowHorizon::Sky:
            return 1.0f;
        case SkyBelowHorizon::Flat:
            return 2.0f;
        case SkyBelowHorizon::Fog:
        default:
            return 0.0f;
    }
}
}

SkyFogUniformValues packSkyFogUniform(const SkyFrameState *pFrame, const SkySurroundings &surroundings)
{
    if (pFrame == nullptr)
    {
        return {};
    }

    const SkyFrameState &frame = *pFrame;
    const SkyColor &glow = frame.value(SkyValue::SunGlow);
    const float glowStrength = frame.scalar(SkyValue::SunGlowStrength);
    return {{
        vec4(frame.value(SkyValue::Zenith), frame.scalar(SkyValue::HorizonExponent)),
        vec4(frame.value(SkyValue::Horizon), frame.skyMix),
        {glow[0] * glowStrength, glow[1] * glowStrength, glow[2] * glowStrength,
            std::max(frame.scalar(SkyValue::SunGlowExponent), 0.5f)},
        {frame.sunDirection[0], frame.sunDirection[1], frame.sunDirection[2], frame.lightningFlash},
        {surroundings.mapEdge[0], surroundings.mapEdge[1], surroundings.mapEdge[2],
            std::clamp(frame.scalar(SkyValue::AerialHaze), 0.0f, 1.0f)},
        // Fog weather hides the distant sea along with the rest of the view.
        vec4(surroundings.seaColorDisplay, 1.0f - frame.fogAmount),
        {std::max(surroundings.camera[0], MinimumSeaViewHeight), SeaHazeDistance, surroundings.camera[1],
            surroundings.camera[2]},
        surroundings.seaSideWeights,
    }};
}

std::array<float, 3> skyEnvironmentTint(const SkyFrameState &frame)
{
    // Classic's noon reflection scale is 1; the Enhanced noon sky averages to about this luminance.
    constexpr float NoonSkyLuminance = 0.45f;
    const SkyColor &zenith = frame.value(SkyValue::Zenith);
    const SkyColor &horizon = frame.value(SkyValue::Horizon);
    std::array<float, 3> average = {};

    for (size_t channel = 0; channel < 3; ++channel)
    {
        average[channel] = 0.5f * (zenith[channel] + horizon[channel]);
    }

    const float luminance = 0.2126f * average[0] + 0.7152f * average[1] + 0.0722f * average[2];
    std::array<float, 3> tint = {};

    for (size_t channel = 0; channel < 3; ++channel)
    {
        // Keep some of the sky's hue without turning metal and skin fully blue at noon.
        tint[channel] = std::clamp((luminance + (average[channel] - luminance) * 0.6f) / NoonSkyLuminance, 0.0f, 2.0f);
    }

    return tint;
}

SkyRenderer::SkyRenderer()
{
    m_samplers.fill(BGFX_INVALID_HANDLE);
}

SkyRenderer::~SkyRenderer()
{
    if (Engine::BgfxContext::isBgfxInitialized())
    {
        shutdown();
    }
    else
    {
        abandonGpuResources();
    }
}

bool SkyRenderer::initialize(const Engine::AssetFileSystem &assets)
{
    shutdown();
    m_pAssets = &assets;
    const std::optional<std::string> yaml = assets.readTextFile(SkyLibraryPath);
    std::string error;

    if (!yaml || !m_library.loadFromYaml(*yaml, error))
    {
        std::cerr << "[AssetLoadWarning] kind=sky_presets path=" << SkyLibraryPath
                  << " error=" << (yaml ? error : std::string("missing")) << '\n';
        return false;
    }

    m_state.setLibrary(&m_library);
    m_program = loadRuntimeProgram("vs_sky", "fs_sky");
    m_upscaleProgram = loadRuntimeProgram("vs_sky", "fs_sky_upscale");
    m_imageSampler = bgfx::createUniform("s_skyImage", bgfx::UniformType::Sampler);
    m_upscaleUniform = bgfx::createUniform("u_skyUpscale", bgfx::UniformType::Vec4);
    m_fogUniform = bgfx::createUniform("u_skyFog", bgfx::UniformType::Vec4, SkyFogUniformVectors);
    m_rayUniform = bgfx::createUniform("u_skyRay", bgfx::UniformType::Mat4);
    m_paramsUniform = bgfx::createUniform("u_skyParams", bgfx::UniformType::Vec4, 8);
    m_cloudsUniform = bgfx::createUniform("u_skyClouds", bgfx::UniformType::Vec4, 8);
    const std::array<const char *, 7> samplerNames = {
        "s_skyCloud0", "s_skyCloud1", "s_skyCloud2", "s_skyCloud3", "s_skyRing", "s_skyStars", "s_skyMoon"};

    for (size_t index = 0; index < samplerNames.size(); ++index)
    {
        m_samplers[index] = bgfx::createUniform(samplerNames[index], bgfx::UniformType::Sampler);
    }

    const uint32_t empty = 0x00000000u;
    const uint32_t white = 0xffffffffu;
    m_emptyTexture = bgfx::createTexture2D(1, 1, false, 1, bgfx::TextureFormat::RGBA8, BGFX_SAMPLER_NONE,
        bgfx::copy(&empty, sizeof(empty)));
    m_moonFallbackTexture = bgfx::createTexture2D(1, 1, false, 1, bgfx::TextureFormat::RGBA8, BGFX_SAMPLER_NONE,
        bgfx::copy(&white, sizeof(white)));
    m_vertexLayout.begin().add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float).end();
    prepareEnvironmentSource(assets);

    if (!isReady())
    {
        std::cerr << "SkyRenderer: failed to create the sky program or uniforms\n";
        shutdown();
        return false;
    }

    return true;
}

void SkyRenderer::shutdown()
{
    for (auto &entry : m_textures)
    {
        if (bgfx::isValid(entry.second))
        {
            bgfx::destroy(entry.second);
        }
    }

    m_textures.clear();
    m_cloudTextureNames.clear();

    for (bgfx::TextureHandle *pTexture : {&m_emptyTexture, &m_moonFallbackTexture})
    {
        if (bgfx::isValid(*pTexture))
        {
            bgfx::destroy(*pTexture);
            *pTexture = BGFX_INVALID_HANDLE;
        }
    }

    for (bgfx::UniformHandle *pUniform : {&m_fogUniform, &m_rayUniform, &m_paramsUniform, &m_cloudsUniform,
             &m_imageSampler, &m_upscaleUniform})
    {
        if (bgfx::isValid(*pUniform))
        {
            bgfx::destroy(*pUniform);
            *pUniform = BGFX_INVALID_HANDLE;
        }
    }

    if (bgfx::isValid(m_imageFrameBuffer))
    {
        bgfx::destroy(m_imageFrameBuffer);
        m_imageFrameBuffer = BGFX_INVALID_HANDLE;
    }

    m_imageWidth = 0;
    m_imageHeight = 0;

    if (bgfx::isValid(m_upscaleProgram))
    {
        bgfx::destroy(m_upscaleProgram);
        m_upscaleProgram = BGFX_INVALID_HANDLE;
    }

    for (bgfx::UniformHandle &sampler : m_samplers)
    {
        if (bgfx::isValid(sampler))
        {
            bgfx::destroy(sampler);
            sampler = BGFX_INVALID_HANDLE;
        }
    }

    if (bgfx::isValid(m_program))
    {
        bgfx::destroy(m_program);
        m_program = BGFX_INVALID_HANDLE;
    }

    m_state.setLibrary(nullptr);
    m_library = {};
    m_pAssets = nullptr;
    m_environmentPixels.clear();
    m_environmentSize = 0;
}

void SkyRenderer::abandonGpuResources()
{
    m_textures.clear();
    m_cloudTextureNames.clear();
    m_emptyTexture = BGFX_INVALID_HANDLE;
    m_moonFallbackTexture = BGFX_INVALID_HANDLE;
    m_fogUniform = BGFX_INVALID_HANDLE;
    m_rayUniform = BGFX_INVALID_HANDLE;
    m_paramsUniform = BGFX_INVALID_HANDLE;
    m_cloudsUniform = BGFX_INVALID_HANDLE;
    m_samplers.fill(BGFX_INVALID_HANDLE);
    m_program = BGFX_INVALID_HANDLE;
    m_upscaleProgram = BGFX_INVALID_HANDLE;
    m_imageSampler = BGFX_INVALID_HANDLE;
    m_upscaleUniform = BGFX_INVALID_HANDLE;
    m_imageFrameBuffer = BGFX_INVALID_HANDLE;
    m_imageWidth = 0;
    m_imageHeight = 0;
    m_state.setLibrary(nullptr);
    m_library = {};
    m_pAssets = nullptr;
    m_environmentPixels.clear();
    m_environmentSize = 0;
}

bool SkyRenderer::isReady() const
{
    return bgfx::isValid(m_program) && bgfx::isValid(m_fogUniform) && bgfx::isValid(m_rayUniform)
        && bgfx::isValid(m_paramsUniform) && bgfx::isValid(m_cloudsUniform) && bgfx::isValid(m_emptyTexture)
        && bgfx::isValid(m_moonFallbackTexture)
        && std::all_of(m_samplers.begin(), m_samplers.end(),
            [](bgfx::UniformHandle sampler) { return bgfx::isValid(sampler); })
        && !m_library.empty();
}

SkyStateModel &SkyRenderer::state()
{
    return m_state;
}

const SkyFrameState &SkyRenderer::frame() const
{
    return m_state.frame();
}

const SkyPresetLibrary &SkyRenderer::library() const
{
    return m_library;
}

std::optional<Engine::ModelSkyEnvironment> SkyRenderer::environmentSource() const
{
    if (m_environmentSize == 0)
    {
        return std::nullopt;
    }

    return Engine::ModelSkyEnvironment{"enhanced-sky", m_environmentSize, m_environmentSize,
        float(m_environmentSize), float(m_environmentSize), m_environmentPixels};
}

void SkyRenderer::prepareEnvironmentSource(const Engine::AssetFileSystem &assets)
{
    // A grey cumulus pattern: bright cloud over a slightly darker sky, coloured later by skyEnvironmentTint.
    constexpr uint16_t Size = 64;
    const std::string path = std::string(SkyTextureDirectory) + "clouds_cumulus.png";
    const std::optional<std::vector<uint8_t>> bytes = assets.readBinaryFile(path);
    const std::optional<Engine::ImagePixelsBgra> image =
        bytes ? Engine::decodeImagePixelsBgra(*bytes, path) : std::nullopt;
    m_environmentPixels.assign(size_t(Size) * Size * 4, 0);
    m_environmentSize = Size;

    for (uint16_t row = 0; row < Size; ++row)
    {
        for (uint16_t column = 0; column < Size; ++column)
        {
            float density = 0.5f;

            if (image && image->width > 0 && image->height > 0)
            {
                const size_t sourceX = size_t(column) * size_t(image->width) / Size;
                const size_t sourceY = size_t(row) * size_t(image->height) / Size;
                density = float(image->pixels[(sourceY * size_t(image->width) + sourceX) * 4 + 2]) / 255.0f;
            }

            const uint8_t grey = uint8_t(std::lround(255.0f * (0.62f + 0.38f * std::clamp((density - 0.55f) * 3.0f,
                0.0f, 1.0f))));
            uint8_t *pPixel = &m_environmentPixels[(size_t(row) * Size + column) * 4];
            pPixel[0] = grey;
            pPixel[1] = grey;
            pPixel[2] = grey;
            pPixel[3] = 255;
        }
    }
}

void SkyRenderer::applyFogUniform(const SkyFrameState *pFrame, const SkySurroundings &surroundings) const
{
    if (!bgfx::isValid(m_fogUniform))
    {
        return;
    }

    const SkyFogUniformValues values = packSkyFogUniform(pFrame, surroundings);
    bgfx::setUniform(m_fogUniform, values.data(), SkyFogUniformVectors);
}

bgfx::TextureHandle SkyRenderer::texture(const std::string &name, bool mipmaps)
{
    if (name.empty() || m_pAssets == nullptr)
    {
        return BGFX_INVALID_HANDLE;
    }

    const auto cached = m_textures.find(name);

    if (cached != m_textures.end())
    {
        return cached->second;
    }

    bgfx::TextureHandle handle = BGFX_INVALID_HANDLE;
    const std::string path = SkyTextureDirectory + name + ".png";
    const std::optional<std::vector<uint8_t>> bytes = m_pAssets->readBinaryFile(path);
    const std::optional<Engine::ImagePixelsBgra> image =
        bytes ? Engine::decodeImagePixelsBgra(*bytes, path) : std::nullopt;

    if (image && image->width > 0 && image->height > 0)
    {
        const uint32_t pixelBytes = static_cast<uint32_t>(image->pixels.size());

        if (mipmaps)
        {
            handle = createBgraTexture2D(uint16_t(image->width), uint16_t(image->height), image->pixels.data(),
                pixelBytes, TextureFilterProfile::Sky, BGFX_TEXTURE_NONE,
                BgraTexturePixelPreparation::AlreadyPrepared);
        }
        else
        {
            // Panoramas wrap around atan2 seams, where mip selection would draw a visible line.
            handle = bgfx::createTexture2D(uint16_t(image->width), uint16_t(image->height), false, 1,
                bgraTextureUploadFormat(), BGFX_SAMPLER_V_CLAMP,
                copyBgraTextureUploadMemory(image->pixels.data(), pixelBytes));
        }
    }

    if (!bgfx::isValid(handle))
    {
        std::cerr << "[AssetLoadWarning] kind=sky_texture path=" << path << " (drawn without it)\n";
    }

    m_textures.emplace(name, handle);

    if (mipmaps && bgfx::isValid(handle))
    {
        m_cloudTextureNames.insert(name);
    }

    return handle;
}

void SkyRenderer::releaseUnusedCloudTextures(const SkyFrameState &frame)
{
    if (m_cloudTextureNames.size() <= MaxCachedCloudTextures)
    {
        return;
    }

    for (auto nameIt = m_cloudTextureNames.begin(); nameIt != m_cloudTextureNames.end();)
    {
        const bool used = std::any_of(frame.clouds.begin(), frame.clouds.end(),
            [&nameIt](const SkyCloudLayerState &cloud) { return cloud.texture == *nameIt; });

        if (used)
        {
            ++nameIt;
            continue;
        }

        // bgfx defers the destroy until frames already submitted with this texture have rendered.
        const auto textureIt = m_textures.find(*nameIt);
        bgfx::destroy(textureIt->second);
        m_textures.erase(textureIt);
        nameIt = m_cloudTextureNames.erase(nameIt);
    }
}

void SkyRenderer::render(
    uint16_t viewId, const float *pView, const float *pProjection, const SkySurroundings &surroundings)
{
    const SkyFrameState &frame = m_state.frame();

    if (!isReady() || !frame.drawSky || pView == nullptr || pProjection == nullptr
        || bgfx::getAvailTransientVertexBuffer(3, m_vertexLayout) < 3)
    {
        return;
    }

    float viewRotation[16];
    std::copy_n(pView, 16, viewRotation);
    viewRotation[12] = 0.0f;
    viewRotation[13] = 0.0f;
    viewRotation[14] = 0.0f;
    float viewProjection[16];
    float ray[16];
    bx::mtxMul(viewProjection, viewRotation, pProjection);
    bx::mtxInverse(ray, viewProjection);

    const float poleElevation = frame.stars.poleElevationDegrees * DegreesToRadians;
    const std::array<std::array<float, 4>, 8> params = {{
        vec4(frame.value(SkyValue::SunDisc), std::cos(frame.sunDiscDegrees * 0.5f * DegreesToRadians)),
        {frame.moonDirection[0], frame.moonDirection[1], frame.moonDirection[2],
            std::cos(frame.moonDiscDegrees * 0.5f * DegreesToRadians)},
        {frame.moonPhase, frame.scalar(SkyValue::MoonVisibility), frame.scalar(SkyValue::Stars),
            frame.starRotationRadians},
        vec4(frame.value(SkyValue::CloudLit), belowHorizonMode(frame.belowHorizon)),
        vec4(frame.value(SkyValue::CloudShadow), frame.scalar(SkyValue::SunDiscVisibility)),
        {frame.horizonRing.opacity, frame.horizonRing.height, frame.stars.brightness, frame.stars.density},
        vec4(frame.fogFlatDisplay, frame.fogAmount),
        {0.0f, std::cos(poleElevation), std::sin(poleElevation), 0.0f},
    }};
    std::array<std::array<float, 4>, 8> clouds = {};
    releaseUnusedCloudTextures(frame);

    for (size_t layer = 0; layer < MaxSkyCloudLayers; ++layer)
    {
        bgfx::TextureHandle cloudTexture = m_emptyTexture;

        if (layer < frame.clouds.size())
        {
            const SkyCloudLayerState &cloud = frame.clouds[layer];
            const bgfx::TextureHandle loaded = texture(cloud.texture, true);

            if (bgfx::isValid(loaded))
            {
                cloudTexture = loaded;
                clouds[layer * 2] = {cloud.scale, cloud.coverage, cloud.softness, cloud.opacity};
                clouds[layer * 2 + 1] = {cloud.offset[0], cloud.offset[1], cloud.curvature, cloud.color ? 1.0f : 0.0f};
            }
        }

        bindTexture(uint8_t(CloudSampler0 + layer), m_samplers[CloudSampler0 + layer], cloudTexture,
            TextureFilterProfile::Sky);
    }

    const bgfx::TextureHandle ring = texture(frame.horizonRing.texture, false);
    const bgfx::TextureHandle stars = texture(frame.stars.texture, false);
    const bgfx::TextureHandle moon = texture("moon", false);
    bgfx::setTexture(RingSampler, m_samplers[RingSampler], bgfx::isValid(ring) ? ring : m_emptyTexture);
    bgfx::setTexture(StarsSampler, m_samplers[StarsSampler], bgfx::isValid(stars) ? stars : m_emptyTexture);
    bgfx::setTexture(MoonSampler, m_samplers[MoonSampler], bgfx::isValid(moon) ? moon : m_moonFallbackTexture,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    applyFogUniform(&frame, surroundings);
    bgfx::setUniform(m_rayUniform, ray);
    bgfx::setUniform(m_paramsUniform, params.data(), uint16_t(params.size()));
    bgfx::setUniform(m_cloudsUniform, clouds.data(), uint16_t(clouds.size()));

    bgfx::TransientVertexBuffer vertices;
    bgfx::allocTransientVertexBuffer(&vertices, 3, m_vertexLayout);
    float *pVertices = reinterpret_cast<float *>(vertices.data);
    const std::array<float, 9> triangle = {-1.0f, -1.0f, 0.0f, 3.0f, -1.0f, 0.0f, -1.0f, 3.0f, 0.0f};
    std::copy(triangle.begin(), triangle.end(), pVertices);
    bgfx::setVertexBuffer(0, &vertices);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A);
    bgfx::submit(viewId, m_program);
}

void SkyRenderer::renderScaled(uint16_t viewId, uint16_t imageViewId, uint16_t width, uint16_t height, float scale,
    const float *pView, const float *pProjection, const SkySurroundings &surroundings)
{
    const uint16_t imageWidth = uint16_t(std::max(1.0f, std::round(float(width) * scale)));
    const uint16_t imageHeight = uint16_t(std::max(1.0f, std::round(float(height) * scale)));

    if (!bgfx::isValid(m_upscaleProgram) || !bgfx::isValid(m_imageSampler) || !bgfx::isValid(m_upscaleUniform)
        || scale >= 0.999f)
    {
        render(viewId, pView, pProjection, surroundings);
        return;
    }

    if (!bgfx::isValid(m_imageFrameBuffer) || imageWidth != m_imageWidth || imageHeight != m_imageHeight)
    {
        if (bgfx::isValid(m_imageFrameBuffer))
        {
            bgfx::destroy(m_imageFrameBuffer);
        }

        m_imageFrameBuffer = bgfx::createFrameBuffer(imageWidth, imageHeight, bgfx::TextureFormat::RGBA8,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        m_imageWidth = imageWidth;
        m_imageHeight = imageHeight;
    }

    if (!bgfx::isValid(m_imageFrameBuffer) || bgfx::getAvailTransientVertexBuffer(3, m_vertexLayout) < 3)
    {
        render(viewId, pView, pProjection, surroundings);
        return;
    }

    bgfx::setViewFrameBuffer(imageViewId, m_imageFrameBuffer);
    bgfx::setViewRect(imageViewId, 0, 0, imageWidth, imageHeight);
    bgfx::setViewClear(imageViewId, BGFX_CLEAR_NONE);
    render(imageViewId, pView, pProjection, surroundings);

    bgfx::TransientVertexBuffer vertices;

    if (bgfx::getAvailTransientVertexBuffer(3, m_vertexLayout) < 3)
    {
        return;
    }

    bgfx::allocTransientVertexBuffer(&vertices, 3, m_vertexLayout);
    const std::array<float, 9> triangle = {-1.0f, -1.0f, 0.0f, 3.0f, -1.0f, 0.0f, -1.0f, 3.0f, 0.0f};
    std::copy(triangle.begin(), triangle.end(), reinterpret_cast<float *>(vertices.data));
    const std::array<float, 4> upscale = {bgfx::getCaps()->originBottomLeft ? 1.0f : 0.0f, 0.0f, 0.0f, 0.0f};
    bgfx::setUniform(m_upscaleUniform, upscale.data());
    bgfx::setTexture(0, m_imageSampler, bgfx::getTexture(m_imageFrameBuffer),
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setVertexBuffer(0, &vertices);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A);
    bgfx::submit(viewId, m_upscaleProgram);
}
}
