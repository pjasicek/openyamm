#include "game/render/WaterRenderer.h"

#include "engine/AssetFileSystem.h"
#include "engine/BgfxContext.h"
#include "engine/ImageAssetLoader.h"
#include "game/render/RuntimeShader.h"
#include "game/indoor/IndoorLightingRuntime.h"
#include "game/render/TextureFiltering.h"
#include "game/render/ViewFrustum.h"
#include "game/render/WaterCoverage.h"
#include "game/render/WaterGeometry.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
bgfx::VertexLayout waterVertexLayout()
{
    bgfx::VertexLayout layout;
    layout.begin().add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Normal, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord1, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true).end();
    return layout;
}
}
bool WaterRenderer::initialize(const Engine::AssetFileSystem &assets, std::vector<WaterSurfaceGeometry> geometry,
    std::span<const std::vector<uint8_t>> coverageMasks, bool indoor)
{
    shutdown();
    if (geometry.empty() && indoor)
    {
        return true;
    }
    constexpr const char *pPath = "engine/rendering/water/water_nm.png";
    const std::optional<std::vector<uint8_t>> bytes = assets.readBinaryFile(pPath);
    const std::optional<Engine::ImagePixelsBgra> image = bytes
        ? Engine::decodeImagePixelsBgra(*bytes, pPath) : std::nullopt;
    if (!image)
    {
        std::cerr << "Cannot load water normal texture: " << pPath << '\n';
        return false;
    }
    m_indoor = indoor;
    if (!indoor)
    {
        const std::optional<std::string> sprites = assets.readTextFile("engine/rendering/water/sprites.yml");
        if (!sprites)
        {
            std::cerr << "Cannot load water sprite regions.\n";
            return false;
        }
        try
        {
            m_spriteWaterStrips = parseSpriteWaterStrips(*sprites);
        }
        catch (const std::exception &exception)
        {
            std::cerr << "Cannot load water sprite regions: " << exception.what() << '\n';
            return false;
        }
    }
    m_program = loadRuntimeProgram("vs_water", indoor ? "fs_indoor_water" : "fs_water");
    m_normalTexture = bgfx::createTexture2D(uint16_t(image->width), uint16_t(image->height), true, 1,
        bgraTextureUploadFormat(), BGFX_SAMPLER_NONE);
    updateBgraTextureArrayLayer(m_normalTexture, 0, uint16_t(image->width), uint16_t(image->height), image->pixels);
    const uint32_t empty = 0xff000000;
    m_emptyReflection = bgfx::createTexture2D(1, 1, false, 1, bgfx::TextureFormat::RGBA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP, bgfx::copy(&empty, sizeof(empty)));
    const uint16_t coverageSize = coverageMasks.empty() ? 1 : WaterCoverageSize;
    const size_t maskBytes = size_t(coverageSize) * coverageSize;
    std::vector<uint8_t> coverage(maskBytes * std::max(coverageMasks.size(), size_t(1)), 255);
    for (size_t layer = 0; layer < coverageMasks.size(); ++layer)
    {
        if (!coverageMasks[layer].empty())
        {
            if (coverageMasks[layer].size() != maskBytes)
            {
                std::cerr << "Invalid water coverage mask for terrain layer " << layer << '\n';
                shutdown();
                return false;
            }
            std::copy(coverageMasks[layer].begin(), coverageMasks[layer].end(), coverage.begin() + layer * maskBytes);
        }
    }
    m_coverageTexture = bgfx::createTexture2D(coverageSize, coverageSize, false,
        uint16_t(std::max(coverageMasks.size(), size_t(1))), bgfx::TextureFormat::R8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP,
        bgfx::copy(coverage.data(), uint32_t(coverage.size())));
    m_coverageSampler = bgfx::createUniform("s_texWaterCoverage", bgfx::UniformType::Sampler);
    m_normalSampler = bgfx::createUniform("s_waterNormal", bgfx::UniformType::Sampler);
    m_spriteSampler = bgfx::createUniform("s_waterSprite", bgfx::UniformType::Sampler);
    m_reflectionSampler = bgfx::createUniform("s_waterReflection", bgfx::UniformType::Sampler);
    m_params = bgfx::createUniform("u_waterParams", bgfx::UniformType::Vec4);
    m_sunDirection = bgfx::createUniform("u_waterSunDirection", bgfx::UniformType::Vec4);
    m_sunColor = bgfx::createUniform("u_waterSunColor", bgfx::UniformType::Vec4);
    m_skyColor = bgfx::createUniform("u_waterSkyColor", bgfx::UniformType::Vec4);
    m_reflectionMatrix = bgfx::createUniform("u_waterReflectionMatrix", bgfx::UniformType::Mat4);

    if (indoor)
    {
        m_cameraPosition = bgfx::createUniform("u_cameraPosition", bgfx::UniformType::Vec4);
        m_indoorLightPositions = bgfx::createUniform("u_indoorLightPositions", bgfx::UniformType::Vec4, 12);
        m_indoorLightColors = bgfx::createUniform("u_indoorLightColors", bgfx::UniformType::Vec4, 12);
        m_indoorLightParams = bgfx::createUniform("u_indoorLightParams", bgfx::UniformType::Vec4);
    }
    if (!updateGeometry(std::move(geometry)))
    {
        shutdown();
        return false;
    }
    if (!isReady())
    {
        std::cerr << "Cannot create water rendering resources.\n";
        shutdown();
        return false;
    }
    return true;
}

bool WaterRenderer::updateGeometry(std::vector<WaterSurfaceGeometry> geometry, bool buildings)
{
    for (const Surface &surface : m_surfaces)
    {
        if (surface.building == buildings && bgfx::isValid(surface.buffer))
        {
            bgfx::destroy(surface.buffer);
        }
    }
    std::erase_if(m_surfaces, [buildings](const Surface &surface) { return surface.building == buildings; });
    m_reflectionUpdates = {};
    const bgfx::VertexLayout layout = waterVertexLayout();
    for (WaterSurfaceGeometry &source : geometry)
    {
        if (source.vertices.empty())
        {
            continue;
        }
        Surface surface;
        surface.building = buildings;
        surface.height = source.height;
        surface.planar = source.planar;
        surface.sectorId = source.sectorId;
        surface.backSectorId = source.backSectorId;
        surface.vertexCount = uint32_t(source.vertices.size());
        surface.patches = std::move(source.patches);
        surface.buffer = bgfx::createVertexBuffer(
            bgfx::copy(source.vertices.data(), uint32_t(source.vertices.size() * sizeof(WaterVertex))), layout);
        m_surfaces.push_back(std::move(surface));
    }
    return std::all_of(m_surfaces.begin(), m_surfaces.end(), [](const Surface &surface)
        { return bgfx::isValid(surface.buffer); });
}

bool WaterRenderer::isReady() const
{
    return bgfx::isValid(m_program) && bgfx::isValid(m_normalTexture)
        && bgfx::isValid(m_coverageTexture) && bgfx::isValid(m_coverageSampler)
        && bgfx::isValid(m_emptyReflection) && bgfx::isValid(m_normalSampler) && bgfx::isValid(m_spriteSampler)
        && bgfx::isValid(m_reflectionSampler)
        && bgfx::isValid(m_params) && bgfx::isValid(m_sunDirection)
        && bgfx::isValid(m_sunColor) && bgfx::isValid(m_skyColor) && bgfx::isValid(m_reflectionMatrix)
        && (!m_indoor || (bgfx::isValid(m_cameraPosition) && bgfx::isValid(m_indoorLightPositions)
            && bgfx::isValid(m_indoorLightColors) && bgfx::isValid(m_indoorLightParams)))
        && std::all_of(m_surfaces.begin(), m_surfaces.end(), [](const Surface &surface)
            { return bgfx::isValid(surface.buffer); });
}

bool WaterRenderer::resizeReflection(size_t index, uint16_t size)
{
    Reflection &target = m_reflections[index];
    if (m_reflectionSizes[index] == size)
    {
        return bgfx::isValid(target.frameBuffer);
    }
    if (bgfx::isValid(target.frameBuffer))
    {
        bgfx::destroy(target.frameBuffer);
        target.frameBuffer = BGFX_INVALID_HANDLE;
        target.texture = BGFX_INVALID_HANDLE;
    }
    m_reflectionSizes[index] = size;
    target.size = size;
    const bgfx::TextureHandle attachments[] = {
        bgfx::createTexture2D(size, size, false, 1, bgfx::TextureFormat::RGBA8,
            BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP),
        bgfx::createTexture2D(size, size, false, 1, bgfx::TextureFormat::D24S8, BGFX_TEXTURE_RT_WRITE_ONLY)
    };
    if (!bgfx::isValid(attachments[0]) || !bgfx::isValid(attachments[1]))
    {
        for (bgfx::TextureHandle attachment : attachments)
        {
            if (bgfx::isValid(attachment))
            {
                bgfx::destroy(attachment);
            }
        }
        std::cerr << "Cannot allocate " << size << "-pixel water reflection textures.\n";
        return false;
    }
    target.frameBuffer = bgfx::createFrameBuffer(2, attachments, true);
    if (!bgfx::isValid(target.frameBuffer))
    {
        for (bgfx::TextureHandle attachment : attachments)
        {
            bgfx::destroy(attachment);
        }
        std::cerr << "Cannot create water reflection framebuffer.\n";
        return false;
    }
    target.texture = attachments[0];
    return true;
}

void WaterRenderer::prepare(const ViewFrustum &frustum, const bx::Vec3 &camera, const float *pView,
    const float *pProjection, bool reflectionsEnabled, uint16_t size, float seconds,
    uint64_t visualRevision, bool buildings, std::span<const uint8_t> visibleSectors, int16_t reflectionSectorId,
    bool billboards)
{
    m_camera = camera;
    m_reflectionCount = 0;
    for (Surface &surface : m_surfaces)
    {
        surface.visible = false;
        surface.reflection = -1;
        surface.distanceSquared = std::numeric_limits<float>::max();
        if ((surface.building && !buildings)
            || !indoorGeometrySectorsVisible(visibleSectors, surface.sectorId, surface.backSectorId))
        {
            continue;
        }
        for (const std::array<bx::Vec3, 2> &patch : surface.patches)
        {
            if (!frustum.intersectsBounds(patch[0], patch[1]))
            {
                continue;
            }
            surface.visible = true;
            const bx::Vec3 closest = {
                std::clamp(camera.x, patch[0].x, patch[1].x),
                std::clamp(camera.y, patch[0].y, patch[1].y),
                std::clamp(camera.z, patch[0].z, patch[1].z)
            };
            const bx::Vec3 delta = bx::sub(camera, closest);
            surface.distanceSquared = std::min(surface.distanceSquared, bx::dot(delta, delta));
        }
    }
    if (!reflectionsEnabled)
    {
        return;
    }
    // A fixed two-plane budget bounds work on maps with water at many elevations.
    // Remaining surfaces use the sky response, just like sloped/nonplanar water.
    for (size_t index = 0; index < MaxWaterReflections; ++index)
    {
        Surface *pNearest = nullptr;
        for (Surface &surface : m_surfaces)
        {
            if (surface.visible && surface.planar && surface.reflection < 0 && camera.z > surface.height
                && (pNearest == nullptr || surface.distanceSquared < pNearest->distanceSquared))
            {
                pNearest = &surface;
            }
        }
        if (pNearest == nullptr)
        {
            break;
        }
        Reflection &target = m_reflections[index];
        const int16_t startSectorId = reflectionSectorId >= 0 ? reflectionSectorId : pNearest->sectorId;
        const bool sectorChanged = target.sectorId != startSectorId;
        target.sectorId = startSectorId;
        target.height = pNearest->height;
        if (sectorChanged)
        {
            m_reflectionUpdates[index] = {};
        }
        const bx::Vec3 reflectedCamera = reflectWaterPoint(camera, target.height);
        target.skyView = uint16_t(FirstWaterReflectionView + index * 2);
        target.worldView = target.skyView + 1;
        float reflectedView[16];
        float captureProjection[16];
        float captureViewProjection[16];
        waterReflectionView(reflectedView, pView, target.height);
        const uint16_t captureSize = m_indoor
            ? waterReflectionCaptureSize(size, bgfx::getCaps()->limits.maxTextureSize) : size;
        const float captureScale = float(captureSize) / size;
        if (m_indoor)
        {
            waterReflectionCaptureProjection(captureProjection, pProjection, captureScale,
                bgfx::getCaps()->homogeneousDepth);
        }
        else
        {
            std::copy_n(pProjection, 16, captureProjection);
        }
        bx::mtxMul(captureViewProjection, reflectedView, captureProjection);
        const WaterReflectionScissor scissor =
            waterReflectionScissor(captureViewProjection, reflectedCamera, captureSize);
        if (scissor.width == 0 || scissor.height == 0)
        {
            break;
        }
        const bool viewCovered = m_indoor && !sectorChanged && target.size == captureSize
            && target.projectionScale == captureScale
            && target.camera.x == reflectedCamera.x && target.camera.y == reflectedCamera.y
            && target.camera.z == reflectedCamera.z
            && std::equal(target.sourceProjection.begin(), target.sourceProjection.end(), pProjection)
            && waterReflectionViewCovered(target.view.data(), target.projection.data(), reflectedView,
                pProjection, captureSize, bgfx::getCaps()->homogeneousDepth);
        if (!resizeReflection(index, captureSize))
        {
            break;
        }
        for (Surface &surface : m_surfaces)
        {
            if (surface.visible && surface.planar && surface.height == target.height
                && (reflectionSectorId >= 0 || surface.sectorId == target.sectorId))
            {
                surface.reflection = int(index);
            }
        }
        ++m_reflectionCount;
        target.update = m_reflectionUpdates[index].prepare(captureViewProjection, target.height, captureSize,
            seconds, visualRevision, buildings, viewCovered, billboards);
        if (!target.update)
        {
            continue;
        }
        // Retain the matrix belonging to the texture when reusing a rotated view.
        // Installing the current matrix over an old capture would make reflections slide.
        target.camera = reflectedCamera;
        target.projectionScale = captureScale;
        std::copy_n(reflectedView, 16, target.view.begin());
        std::copy_n(captureProjection, 16, target.projection.begin());
        std::copy_n(pProjection, 16, target.sourceProjection.begin());
        std::copy_n(captureViewProjection, 16, target.viewProjection.begin());
        bgfx::setViewFrameBuffer(target.skyView, target.frameBuffer);
        bgfx::setViewFrameBuffer(target.worldView, target.frameBuffer);
        bgfx::setViewRect(target.skyView, 0, 0, captureSize, captureSize);
        bgfx::setViewRect(target.worldView, 0, 0, captureSize, captureSize);
        bgfx::setViewScissor(target.skyView, scissor.x, scissor.y, scissor.width, scissor.height);
        bgfx::setViewScissor(target.worldView, scissor.x, scissor.y, scissor.width, scissor.height);
        bgfx::setViewClear(target.skyView, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH,
            m_indoor ? 0x000000ff : 0x405060ff, 1.0f);
        // The sky never writes depth; its initial clear also prepares the world pass.
        bgfx::setViewClear(target.worldView, BGFX_CLEAR_NONE);
        bgfx::setViewMode(target.worldView, bgfx::ViewMode::Sequential);
        bgfx::setViewTransform(target.worldView, target.view.data(), target.projection.data());
        bgfx::touch(target.skyView);
        bgfx::touch(target.worldView);
    }
}

std::span<const WaterRenderer::Reflection> WaterRenderer::reflections() const
{
    return {m_reflections.data(), m_reflectionCount};
}

void WaterRenderer::bindCoverage(uint8_t stage) const
{
    if (bgfx::isValid(m_coverageTexture))
    {
        bgfx::setTexture(stage, m_coverageSampler, m_coverageTexture);
    }
}

void WaterRenderer::render(uint16_t viewId, float seconds,
    const std::array<float, 4> &sunDirection, const std::array<float, 4> &sunColor,
    const std::array<float, 4> &skyColor, float rainIntensity, const WaterRippleRuntime *pRipples,
    const Reflection *pReflection)
{
    prepareRippleResources(pRipples);
    const std::array<float, 4> timedSunDirection = {sunDirection[0], sunDirection[1], sunDirection[2], seconds};
    for (const Surface &surface : m_surfaces)
    {
        if (pReflection != nullptr)
        {
            // Reflect flowing faces without sampling the target currently being written.
            const ViewFrustum frustum(pReflection->view.data(), pReflection->projection.data(),
                bgfx::getCaps()->homogeneousDepth);
            if (!surface.building || surface.planar
                || !std::any_of(surface.patches.begin(), surface.patches.end(), [&](const auto &patch)
                    { return patch[1].z >= pReflection->height && frustum.intersectsBounds(patch[0], patch[1]); }))
            {
                continue;
            }
        }
        else if (!surface.visible)
        {
            continue;
        }
        bgfx::setUniform(m_sunDirection, timedSunDirection.data());
        bgfx::setUniform(m_sunColor, sunColor.data());
        bgfx::setUniform(m_skyColor, skyColor.data());
        submitSurface(surface, viewId, seconds, rainIntensity, pRipples);
    }
}

void WaterRenderer::renderIndoor(uint16_t viewId, float seconds, const IndoorLightingFrame &lighting,
    const bx::Vec3 &camera, const bx::Vec3 &forward, const WaterRippleRuntime *pRipples,
    const Reflection *pReflection, std::span<const uint8_t> visibleSectors)
{
    prepareRippleResources(pRipples);
    const std::array<float, 4> eye = {camera.x, camera.y, camera.z, 0.0f};
    for (const Surface &surface : m_surfaces)
    {
        if (pReflection != nullptr)
        {
            const ViewFrustum frustum(pReflection->view.data(), pReflection->projection.data(),
                bgfx::getCaps()->homogeneousDepth);
            if (surface.planar || !indoorGeometrySectorsVisible(visibleSectors, surface.sectorId, surface.backSectorId)
                || !std::any_of(surface.patches.begin(), surface.patches.end(), [&](const auto &patch)
                    { return patch[1].z >= pReflection->height && frustum.intersectsBounds(patch[0], patch[1]); }))
            {
                continue;
            }
        }
        else if (!surface.visible)
        {
            continue;
        }
        const IndoorLightSelectionBounds bounds = {surface.patches.front()[0], surface.patches.front()[1], true};
        const IndoorDrawLightSet lights = IndoorLightingRuntime::selectDrawLightSetForBounds(
            lighting, camera, forward, surface.sectorId, surface.backSectorId, bounds);
        bgfx::setUniform(m_cameraPosition, eye.data());
        bgfx::setUniform(m_indoorLightPositions, lights.positions.data(), 12);
        bgfx::setUniform(m_indoorLightColors, lights.colors.data(), 12);
        bgfx::setUniform(m_indoorLightParams, lights.params.data());
        submitSurface(surface, viewId, seconds, 0.0f, pRipples);
    }
}

void WaterRenderer::renderBillboard(uint16_t viewId, std::span<const WaterVertex> vertices,
    bgfx::TextureHandle sprite, float seconds,
    const std::array<float, 4> &sunDirection, const std::array<float, 4> &sunColor,
    const std::array<float, 4> &skyColor, float rainIntensity)
{
    const bgfx::VertexLayout layout = waterVertexLayout();
    if (vertices.empty() || !isReady()
        || bgfx::getAvailTransientVertexBuffer(uint32_t(vertices.size()), layout) < vertices.size())
    {
        return;
    }
    bgfx::TransientVertexBuffer buffer;
    bgfx::allocTransientVertexBuffer(&buffer, uint32_t(vertices.size()), layout);
    std::memcpy(buffer.data, vertices.data(), vertices.size_bytes());
    float identity[16];
    bx::mtxIdentity(identity);
    const std::array<float, 4> params = {std::fmod(seconds, 1000.0f), 0.0f, 1.0f, rainIntensity};
    const std::array<float, 4> timedSunDirection = {sunDirection[0], sunDirection[1], sunDirection[2], seconds};
    bgfx::setTransform(identity);
    bgfx::setUniform(m_params, params.data());
    bgfx::setUniform(m_sunDirection, timedSunDirection.data());
    bgfx::setUniform(m_sunColor, sunColor.data());
    bgfx::setUniform(m_skyColor, skyColor.data());
    bgfx::setUniform(m_reflectionMatrix, identity);
    bgfx::setTexture(0, m_spriteSampler, sprite, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setTexture(1, m_normalSampler, m_normalTexture);
    bgfx::setTexture(2, m_reflectionSampler, m_emptyReflection);
    bindCoverage(3);
    bgfx::setVertexBuffer(0, &buffer);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z
        | BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, m_program);
}

void WaterRenderer::appendBillboardGeometry(std::vector<WaterVertex> &vertices, const std::string &textureName,
    const BillboardQuad &quad, bool mirrored) const
{
    const auto strips = m_spriteWaterStrips.find(textureName);
    if (strips != m_spriteWaterStrips.end())
    {
        const std::vector<WaterVertex> water = buildSpriteWaterGeometry(quad, strips->second, mirrored);
        vertices.insert(vertices.end(), water.begin(), water.end());
    }
}

void WaterRenderer::prepareRippleResources(const WaterRippleRuntime *pRipples)
{
    if (pRipples != nullptr && pRipples->enabled() && !bgfx::isValid(m_rippleProgram)
        && std::any_of(m_surfaces.begin(), m_surfaces.end(), [](const Surface &surface) { return surface.visible; }))
    {
        m_rippleProgram = loadRuntimeProgram("vs_water", m_indoor ? "fs_indoor_water_ripples" : "fs_water_ripples");
        m_rippleRings = bgfx::createUniform("u_waterRippleRings", bgfx::UniformType::Vec4, MaxDrawWaterRipples);
        m_rippleParams = bgfx::createUniform("u_waterRippleParams", bgfx::UniformType::Vec4);
    }
}

void WaterRenderer::submitSurface(const Surface &surface, uint16_t viewId, float seconds, float rainIntensity,
    const WaterRippleRuntime *pRipples)
{
    const bool reflected = surface.reflection >= 0;
    // Every wave speed is an integer multiple of 1/1000; wrapping here keeps phase continuous.
    const float reflectionScale = reflected ? 1.0f / m_reflections[size_t(surface.reflection)].projectionScale : 0.0f;
    const std::array<float, 4> params = {m_indoor ? seconds : std::fmod(seconds, 1000.0f),
        reflectionScale,
        bgfx::getCaps()->originBottomLeft ? 1.0f : -1.0f, rainIntensity};
    bgfx::setUniform(m_params, params.data());
    float identity[16];
    bx::mtxIdentity(identity);
    bgfx::setTransform(identity);
    bgfx::setUniform(m_reflectionMatrix, reflected
        ? m_reflections[size_t(surface.reflection)].viewProjection.data() : identity);
    bgfx::setTexture(0, m_spriteSampler, m_emptyReflection);
    bgfx::setTexture(1, m_normalSampler, m_normalTexture);
    bgfx::setTexture(2, m_reflectionSampler, reflected
        ? m_reflections[size_t(surface.reflection)].texture : m_emptyReflection);
    bindCoverage(3);
    bgfx::setVertexBuffer(0, surface.buffer, 0, surface.vertexCount);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z
        | BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_BLEND_ALPHA);
    WaterRippleDrawSet ripples;
    if (surface.planar && pRipples != nullptr && pRipples->enabled() && !pRipples->ripples().empty())
    {
        ripples = pRipples->select(m_camera, surface.height, surface.patches, surface.sectorId, surface.backSectorId);
    }
    if (ripples.count != 0)
    {
        const std::array<float, 4> params = {float(ripples.count), 0.0f, 0.0f, 0.0f};
        bgfx::setUniform(m_rippleRings, ripples.rings.data(), MaxDrawWaterRipples);
        bgfx::setUniform(m_rippleParams, params.data());
        bgfx::submit(viewId, m_rippleProgram);
    }
    else
    {
        bgfx::submit(viewId, m_program);
    }
}

void WaterRenderer::shutdown()
{
    m_spriteWaterStrips.clear();
    const bool rendererAvailable = Engine::BgfxContext::isBgfxInitialized();
    for (Surface &surface : m_surfaces)
    {
        if (rendererAvailable && bgfx::isValid(surface.buffer))
        {
            bgfx::destroy(surface.buffer);
        }
    }
    m_surfaces.clear();
    for (Reflection &target : m_reflections)
    {
        if (rendererAvailable && bgfx::isValid(target.frameBuffer))
        {
            bgfx::destroy(target.frameBuffer);
        }
        target = {};
    }
    m_reflectionSizes = {};
    m_reflectionUpdates = {};
    m_reflectionCount = 0;
    if (rendererAvailable && bgfx::isValid(m_rippleProgram))
    {
        bgfx::destroy(m_rippleProgram);
    }
    m_rippleProgram = BGFX_INVALID_HANDLE;
    if (bgfx::isValid(m_program))
    {
        if (rendererAvailable)
        {
            bgfx::destroy(m_program);
        }
        m_program = BGFX_INVALID_HANDLE;
    }
    for (bgfx::TextureHandle *pTexture : {&m_normalTexture, &m_emptyReflection, &m_coverageTexture})
    {
        if (bgfx::isValid(*pTexture))
        {
            if (rendererAvailable)
            {
                bgfx::destroy(*pTexture);
            }
            *pTexture = BGFX_INVALID_HANDLE;
        }
    }
    for (bgfx::UniformHandle *pUniform : {&m_normalSampler, &m_spriteSampler, &m_reflectionSampler,
        &m_coverageSampler, &m_params, &m_sunDirection, &m_sunColor, &m_skyColor, &m_reflectionMatrix,
        &m_cameraPosition, &m_indoorLightPositions, &m_indoorLightColors, &m_indoorLightParams,
        &m_rippleRings, &m_rippleParams})
    {
        if (bgfx::isValid(*pUniform))
        {
            if (rendererAvailable)
            {
                bgfx::destroy(*pUniform);
            }
            *pUniform = BGFX_INVALID_HANDLE;
        }
    }
}
}
