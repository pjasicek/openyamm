#include "game/fx/EffectRenderer.h"

#include "engine/AssetFileSystem.h"
#include "engine/BgfxContext.h"
#include "engine/ParallelFor.h"
#include "engine/render/CookedTexture.h"
#include "game/fx/EffectSystem.h"
#include "game/fx/EffectViewFade.h"
#include "game/fx/WorldFxRenderResources.h"
#include "game/fx/import/EffectResourceLibrary.h"
#include "game/render/RuntimeShader.h"
#include "game/render/TextureFiltering.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <algorithm>
#include <cmath>
#include <cstring>
#include <exception>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint64_t AlphaRenderState =
    BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_BLEND_ALPHA | BGFX_STATE_MSAA;
constexpr uint64_t AdditiveRenderState =
    BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_BLEND_ADD | BGFX_STATE_MSAA;
constexpr uint64_t MultiplyRenderState = BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A |
    BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_BLEND_FUNC(BGFX_STATE_BLEND_DST_COLOR, BGFX_STATE_BLEND_ZERO)
    | BGFX_STATE_MSAA;
constexpr float CullDistance = 12000.0f;
// The texture cache key prefix of sprites kept without the transparent-edge bleed (EffectRenderer::prepareAtlas).
constexpr std::string_view RawTexelsKeyPrefix = "raw-texels:";
// Consecutive ribbon samples closer than this are merged (the live head right after a sample is left behind).
constexpr float RibbonMinimumSegment = 0.5f;

struct RibbonVertex
{
    float x;
    float y;
    float z;
    float u;
    float v;
    float phase;
    float unused;
    uint32_t abgr;
};

struct DrawParticle
{
    std::array<float, 3> position = {};
    std::array<float, 4> color = {};
    float scale = 1.0f;
    float stretchU = 1.0f;
    float stretchV = 1.0f;
    float roll = 0.0f;
    float spriteAnimationSeconds = 0.0f;
    EffectBlendMode blendMode = EffectBlendMode::Alpha;
    // False for MM9's additive sprites: light without the texture's alpha (EffectSpriteDefinition).
    bool additiveTextureAlpha = true;
    EffectSpriteAlignment alignment = EffectSpriteAlignment::CameraFacing;
    std::array<float, 3> planeRight = {1.0f, 0.0f, 0.0f};
    std::array<float, 3> planeUp = {0.0f, 0.0f, 1.0f};
    const EffectRenderer::Texture *pTexture = nullptr;
    // The frame's rectangle in its sprite's atlas: u0, v0, u1, v1.
    std::array<float, 4> uv = {0.0f, 0.0f, 1.0f, 1.0f};
    float logicalWidth = 0.0f;
    float logicalHeight = 0.0f;
    float depth = 0.0f;
};

uint8_t colorChannel(float value)
{
    return static_cast<uint8_t>(std::lround(std::clamp(value, 0.0f, 1.0f) * 255.0f));
}

uint32_t particleColor(const DrawParticle &particle)
{
    return static_cast<uint32_t>(colorChannel(particle.color[0])) |
        (static_cast<uint32_t>(colorChannel(particle.color[1])) << 8) |
        (static_cast<uint32_t>(colorChannel(particle.color[2])) << 16) |
        (static_cast<uint32_t>(colorChannel(particle.color[3])) << 24);
}

uint64_t renderState(EffectBlendMode blendMode)
{
    switch (blendMode)
    {
    case EffectBlendMode::Alpha:
        return AlphaRenderState;
    case EffectBlendMode::Additive:
        return AdditiveRenderState;
    case EffectBlendMode::Multiply:
        return MultiplyRenderState;
    }
    return AlphaRenderState;
}

bx::Vec3 normalizedOrFallback(const bx::Vec3 &value, const bx::Vec3 &fallback)
{
    const float lengthSquared = bx::dot(value, value);
    return lengthSquared > 1.0e-12f ? bx::mul(value, 1.0f / std::sqrt(lengthSquared)) : fallback;
}

void writeQuad(
    std::vector<WorldFxParticleVertex> &vertices,
    const DrawParticle &particle,
    const bx::Vec3 &cameraRight,
    const bx::Vec3 &cameraUp,
    const bx::Vec3 &cameraForward,
    const bx::Vec3 &cameraPosition)
{
    const bx::Vec3 center = {particle.position[0], particle.position[1], particle.position[2]};
    bx::Vec3 rightDirection = particle.alignment == EffectSpriteAlignment::WorldPlane
        ? normalizedOrFallback(
            {particle.planeRight[0], particle.planeRight[1], particle.planeRight[2]},
            cameraRight)
        : cameraRight;
    bx::Vec3 upDirection = particle.alignment == EffectSpriteAlignment::WorldPlane
        ? normalizedOrFallback({particle.planeUp[0], particle.planeUp[1], particle.planeUp[2]}, cameraUp)
        : cameraUp;
    float stretchU = particle.stretchU;
    if (particle.alignment == EffectSpriteAlignment::Velocity)
    {
        // Lay the width along the travel direction as it moves on screen, with perspective: a sprite flying away
        // off to one side moves towards the view centre, not along its direction flattened onto the screen. The
        // on-screen rate of a unit step is (d.r - x d.f, d.u - y d.f) at screen position (x, y) = (p.r, p.u) / p.f;
        // the streak lengthens with it and shortens to round seen head-on.
        const bx::Vec3 direction = normalizedOrFallback(
            {particle.planeRight[0], particle.planeRight[1], particle.planeRight[2]},
            cameraRight);
        const bx::Vec3 relative = bx::sub(center, cameraPosition);
        const float depth = std::max(bx::dot(relative, cameraForward), 1.0f);
        const float alongView = bx::dot(direction, cameraForward);
        const float screenX = bx::dot(direction, cameraRight) - bx::dot(relative, cameraRight) / depth * alongView;
        const float screenY = bx::dot(direction, cameraUp) - bx::dot(relative, cameraUp) / depth * alongView;
        const float onScreenLength = std::sqrt(screenX * screenX + screenY * screenY);
        if (onScreenLength > 1.0e-3f)
        {
            rightDirection = bx::add(
                bx::mul(cameraRight, screenX / onScreenLength),
                bx::mul(cameraUp, screenY / onScreenLength));
            upDirection = normalizedOrFallback(bx::cross(cameraForward, rightDirection), cameraUp);
        }
        stretchU = 1.0f + (particle.stretchU - 1.0f) * std::min(1.0f, onScreenLength);
    }
    else if (particle.roll != 0.0f)
    {
        const float cosine = std::cos(particle.roll);
        const float sine = std::sin(particle.roll);
        const bx::Vec3 rolledRight = bx::add(bx::mul(rightDirection, cosine), bx::mul(upDirection, sine));
        upDirection = bx::sub(bx::mul(upDirection, cosine), bx::mul(rightDirection, sine));
        rightDirection = rolledRight;
    }
    const bx::Vec3 right = bx::mul(
        rightDirection,
        particle.logicalWidth * particle.scale * stretchU * 0.5f);
    const bx::Vec3 up = bx::mul(
        upDirection,
        particle.logicalHeight * particle.scale * particle.stretchV * 0.5f);
    const uint32_t color = particleColor(particle);
    const auto [u0, v0, u1, v1] = particle.uv;
    vertices.push_back({center.x - right.x - up.x, center.y - right.y - up.y,
        center.z - right.z - up.z, u0, v1, color});
    vertices.push_back({center.x - right.x + up.x, center.y - right.y + up.y,
        center.z - right.z + up.z, u0, v0, color});
    vertices.push_back({center.x + right.x + up.x, center.y + right.y + up.y,
        center.z + right.z + up.z, u1, v0, color});
    vertices.push_back(vertices[vertices.size() - 3]);
    vertices.push_back(vertices[vertices.size() - 2]);
    vertices.push_back({center.x + right.x - up.x, center.y + right.y - up.y,
        center.z + right.z - up.z, u1, v1, color});
}

void submitBatch(
    WorldFxRenderResources &resources,
    const EffectRenderer::Texture &texture,
    const std::vector<WorldFxParticleVertex> &vertices,
    EffectBlendMode blendMode,
    bool additiveTextureAlpha,
    uint16_t viewId)
{
    if (vertices.empty() ||
        bgfx::getAvailTransientVertexBuffer(
            static_cast<uint32_t>(vertices.size()),
            WorldFxParticleVertex::ms_layout) < vertices.size())
    {
        return;
    }
    bgfx::TransientVertexBuffer vertexBuffer = {};
    bgfx::allocTransientVertexBuffer(
        &vertexBuffer,
        static_cast<uint32_t>(vertices.size()),
        WorldFxParticleVertex::ms_layout);
    std::memcpy(vertexBuffer.data, vertices.data(), vertices.size() * sizeof(WorldFxParticleVertex));
    const float particleParams[4] = {
        blendMode == EffectBlendMode::Additive ? 1.0f : 0.0f,
        additiveTextureAlpha ? 0.0f : 1.0f,
        0.0f,
        0.0f,
    };
    float identity[16] = {};
    bx::mtxIdentity(identity);
    bgfx::setTransform(identity);
    bgfx::setVertexBuffer(0, &vertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
    bindTexture(
        0,
        resources.textureSamplerHandle(),
        texture.handle,
        TextureFilterProfile::Billboard,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    bgfx::setUniform(resources.particleParamsUniformHandle(), particleParams);
    bgfx::setState(renderState(blendMode));
    // Additive sprites are light: they also draw into the bloom glow, with the same bindings. MM9's do not: LithTech
    // had no bloom, and its blurred glow turned their small crisp cores into wide soft blobs.
    const bool glow = blendMode == EffectBlendMode::Additive && additiveTextureAlpha
        && resources.glowView() != UINT16_MAX;
    bgfx::submit(viewId, resources.particleProgramHandle(), 0, glow ? BGFX_DISCARD_NONE : BGFX_DISCARD_ALL);
    if (glow)
    {
        bgfx::setState(renderState(blendMode));
        bgfx::submit(resources.glowView(), resources.particleProgramHandle());
        resources.markGlowDrawn();
    }
}
}

void EffectRenderer::render(
    WorldFxRenderResources &resources,
    const EffectSystem &effects,
    const EffectResourceLibrary &effectResources,
    const Engine::AssetFileSystem &assetFileSystem,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    m_diagnostics = {};
    m_diagnostics.sourceParticles = effects.particles().size();
    m_diagnostics.sourceFixedSprites = effects.fixedSprites().size();
    const auto recordTextureMemory = [this]()
    {
        m_diagnostics.loadedTextures = m_pTextureCache->textures.size();
        m_diagnostics.estimatedTextureBytes = 0;
        for (const auto &[path, texture] : m_pTextureCache->textures)
        {
            (void)path;
            m_diagnostics.estimatedTextureBytes +=
                static_cast<size_t>(texture.width) * static_cast<size_t>(texture.height) * 4u * 4u / 3u;
        }
    };
    if (!resources.isReady() ||
        (effects.particles().empty() && effects.fixedSprites().empty() && effects.ribbons().empty()))
    {
        recordTextureMemory();
        return;
    }
    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const bx::Vec3 cameraForward = bx::mul(bx::cross(cameraRight, cameraUp), -1.0f);
    renderRibbons(resources, effects, effectResources, assetFileSystem, viewId, cameraPosition, cameraForward);
    std::vector<DrawParticle> draws;
    draws.reserve(effects.particles().size() + effects.fixedSprites().size());
    // Particles of one emitter come in a row, so remembering the last sprite saves most atlas lookups.
    std::string_view lastSpriteResource;
    bool lastRawTexels = false;
    const SpriteAtlas *pLastAtlas = nullptr;
    const auto addDraw = [&](std::string_view spriteResource,
                             const std::array<float, 3> &position,
                             const std::array<float, 4> &color,
                             float scale,
                             float stretchU,
                             float stretchV,
                             float roll,
                             float spriteAnimationSeconds,
                             EffectBlendMode blendMode,
                             bool additiveTextureAlpha,
                             EffectSpriteAlignment alignment,
                             const std::array<float, 3> &planeRight,
                             const std::array<float, 3> &planeUp)
    {
        const bool rawTexels = blendMode == EffectBlendMode::Additive && !additiveTextureAlpha;
        if (pLastAtlas == nullptr || spriteResource != lastSpriteResource || rawTexels != lastRawTexels)
        {
            pLastAtlas = loadAtlas(effectResources, assetFileSystem, spriteResource, rawTexels);
            lastSpriteResource = spriteResource;
            lastRawTexels = rawTexels;
        }
        if (pLastAtlas == nullptr)
        {
            return;
        }
        const SpriteAtlas &atlas = *pLastAtlas;
        const bx::Vec3 offset = {
            position[0] - cameraPosition.x,
            position[1] - cameraPosition.y,
            position[2] - cameraPosition.z,
        };
        const float distanceSquared = bx::dot(offset, offset);
        const float depth = bx::dot(offset, cameraForward);
        if (distanceSquared > CullDistance * CullDistance || depth <= 0.0f)
        {
            return;
        }
        const float halfSize = 0.5f * scale
            * std::max(atlas.logicalWidth * std::abs(stretchU), atlas.logicalHeight * std::abs(stretchV));
        const float viewFade = effectViewFade(depth, halfSize);
        if (viewFade <= 0.001f)
        {
            return;
        }
        // A fading multiply sprite tends to white, which leaves the scene unchanged; MM9's additive light ignores
        // opacity, so it fades by its colour.
        std::array<float, 4> fadedColor = color;
        if (blendMode == EffectBlendMode::Multiply)
        {
            for (size_t channel = 0; channel < 3; ++channel)
            {
                fadedColor[channel] = 1.0f + (color[channel] - 1.0f) * viewFade;
            }
        }
        else if (rawTexels)
        {
            for (size_t channel = 0; channel < 3; ++channel)
            {
                fadedColor[channel] *= viewFade;
            }
        }
        else
        {
            fadedColor[3] *= viewFade;
        }
        const size_t frameIndex = static_cast<size_t>(
            spriteAnimationSeconds * static_cast<float>(atlas.framesPerSecond)) % atlas.frameUvs.size();
        draws.push_back({
            .position = position,
            .color = fadedColor,
            .scale = scale,
            .stretchU = stretchU,
            .stretchV = stretchV,
            .roll = roll,
            .spriteAnimationSeconds = spriteAnimationSeconds,
            .blendMode = blendMode,
            .additiveTextureAlpha = !rawTexels,
            .alignment = alignment,
            .planeRight = planeRight,
            .planeUp = planeUp,
            .pTexture = atlas.pTexture,
            .uv = atlas.frameUvs[frameIndex],
            .logicalWidth = atlas.logicalWidth,
            .logicalHeight = atlas.logicalHeight,
            .depth = depth,
        });
        m_diagnostics.worldQuadArea += static_cast<double>(atlas.logicalWidth) * atlas.logicalHeight
            * scale * scale * std::abs(stretchU * stretchV);
    };
    for (const EffectParticle &particle : effects.particles())
    {
        addDraw(
            particle.spriteResource,
            particle.position,
            particle.color,
            particle.scale,
            particle.stretchU,
            particle.stretchV,
            particle.roll,
            particle.spriteAnimationSeconds,
            particle.blendMode,
            particle.additiveTextureAlpha,
            particle.alignment,
            particle.planeRight,
            particle.planeUp);
    }
    for (const EffectFixedSprite &sprite : effects.fixedSprites())
    {
        addDraw(
            sprite.spriteResource,
            sprite.position,
            sprite.color,
            sprite.scale,
            sprite.stretchU,
            sprite.stretchV,
            0.0f,
            sprite.spriteAnimationSeconds,
            sprite.blendMode,
            sprite.additiveTextureAlpha,
            sprite.alignment,
            sprite.planeRight,
            sprite.planeUp);
    }
    // Alpha and multiply sprites draw back to front. Additive light does not depend on order, so additive sprites
    // draw after them grouped by texture, one batch per texture however they interleave in depth.
    const std::vector<DrawParticle>::iterator additiveBegin = std::stable_partition(
        draws.begin(),
        draws.end(),
        [](const DrawParticle &draw)
        {
            return draw.blendMode != EffectBlendMode::Additive;
        });
    std::stable_sort(
        draws.begin(),
        additiveBegin,
        [](const DrawParticle &left, const DrawParticle &right)
        {
            return left.depth > right.depth;
        });
    std::stable_sort(
        additiveBegin,
        draws.end(),
        [](const DrawParticle &left, const DrawParticle &right)
        {
            return left.pTexture->handle.idx < right.pTexture->handle.idx;
        });

    std::vector<WorldFxParticleVertex> vertices;
    m_diagnostics.visibleQuads = draws.size();
    size_t drawIndex = 0;
    while (drawIndex < draws.size())
    {
        const DrawParticle &first = draws[drawIndex];
        vertices.clear();
        size_t batchEnd = drawIndex;
        while (batchEnd < draws.size() && draws[batchEnd].pTexture == first.pTexture &&
            draws[batchEnd].blendMode == first.blendMode &&
            draws[batchEnd].additiveTextureAlpha == first.additiveTextureAlpha)
        {
            writeQuad(vertices, draws[batchEnd], cameraRight, cameraUp, cameraForward, cameraPosition);
            ++batchEnd;
        }
        submitBatch(resources, *first.pTexture, vertices, first.blendMode, first.additiveTextureAlpha, viewId);
        ++m_diagnostics.drawCalls;
        drawIndex = batchEnd;
    }
    m_diagnostics.textureSwitches = m_diagnostics.drawCalls;
    recordTextureMemory();
}

void EffectRenderer::shutdown(bool destroyGpu)
{
    if (destroyGpu && Engine::BgfxContext::isBgfxInitialized())
    {
        for (bgfx::UniformHandle uniform : {m_ribbonParamsUniform, m_ribbonScrollUniform})
        {
            if (bgfx::isValid(uniform))
            {
                bgfx::destroy(uniform);
            }
        }
        if (bgfx::isValid(m_ribbonProgram))
        {
            bgfx::destroy(m_ribbonProgram);
        }
        // A shared cache is destroyed by the last renderer that still holds it.
        if (m_pTextureCache.use_count() == 1)
        {
            for (const auto &[path, texture] : m_pTextureCache->textures)
            {
                if (bgfx::isValid(texture.handle))
                {
                    bgfx::destroy(texture.handle);
                }
            }
        }
    }
    m_pTextureCache = std::make_shared<TextureCache>();
    m_diagnostics = {};
    m_ribbonProgram = BGFX_INVALID_HANDLE;
    m_ribbonParamsUniform = BGFX_INVALID_HANDLE;
    m_ribbonScrollUniform = BGFX_INVALID_HANDLE;
    m_ribbonProgramAttempted = false;
}

bool EffectRenderer::initializeRibbonProgram()
{
    m_ribbonProgramAttempted = true;
    m_ribbonLayout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord1, 4, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
    m_ribbonProgram = loadRuntimeProgram("vs_effect_ribbon", "fs_effect_ribbon");
    m_ribbonParamsUniform = bgfx::createUniform("u_ribbonParams", bgfx::UniformType::Vec4);
    m_ribbonScrollUniform = bgfx::createUniform("u_ribbonScroll", bgfx::UniformType::Vec4);
    if (!bgfx::isValid(m_ribbonProgram))
    {
        std::cerr << "Effect ribbon rendering unavailable (vs/fs_effect_ribbon)\n";
        return false;
    }
    return true;
}

// Each ribbon is a camera-facing strip: every sample is widened sideways, perpendicular to both the path and the
// view ray, so the strip shows its full width from any angle except straight along the path.
void EffectRenderer::renderRibbons(
    WorldFxRenderResources &resources,
    const EffectSystem &effects,
    const EffectResourceLibrary &effectResources,
    const Engine::AssetFileSystem &assetFileSystem,
    uint16_t viewId,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &cameraForward)
{
    if (effects.ribbons().empty() ||
        (!bgfx::isValid(m_ribbonProgram) && (m_ribbonProgramAttempted || !initializeRibbonProgram())))
    {
        return;
    }
    std::vector<const EffectRibbonPoint *> points;
    std::vector<RibbonVertex> vertices;
    for (const EffectRibbon &ribbon : effects.ribbons())
    {
        points.clear();
        bool visible = false;
        for (const EffectRibbonPoint &point : ribbon.points)
        {
            const bx::Vec3 position = {point.position[0], point.position[1], point.position[2]};
            if (!points.empty())
            {
                const EffectRibbonPoint &previous = *points.back();
                const bx::Vec3 delta = bx::sub(
                    position,
                    {previous.position[0], previous.position[1], previous.position[2]});
                if (bx::dot(delta, delta) < RibbonMinimumSegment * RibbonMinimumSegment)
                {
                    points.back() = &point;
                    continue;
                }
            }
            const bx::Vec3 offset = bx::sub(position, cameraPosition);
            visible = visible || (bx::dot(offset, offset) < CullDistance * CullDistance &&
                bx::dot(offset, cameraForward) > 0.0f);
            points.push_back(&point);
        }
        const EffectSpriteResource *pSprite = effectResources.findSprite(ribbon.settings().spriteResource);
        if (points.size() < 2 || !visible || pSprite == nullptr || pSprite->framePaths.empty())
        {
            continue;
        }
        const Texture *pTexture = loadTexture(assetFileSystem, pSprite->framePaths.front());
        if (pTexture == nullptr)
        {
            continue;
        }
        const EffectRibbonDefinition &settings = ribbon.settings();
        const float textureLength = settings.textureLength * ribbon.scale;
        vertices.clear();
        for (size_t index = 0; index < points.size(); ++index)
        {
            const EffectRibbonPoint &point = *points[index];
            const EffectRibbonPoint &before = *points[index == 0 ? 0 : index - 1];
            const EffectRibbonPoint &after = *points[std::min(index + 1, points.size() - 1)];
            const bx::Vec3 position = {point.position[0], point.position[1], point.position[2]};
            const bx::Vec3 tangent = normalizedOrFallback(
                {after.position[0] - before.position[0], after.position[1] - before.position[1],
                    after.position[2] - before.position[2]},
                cameraForward);
            const bx::Vec3 side = normalizedOrFallback(
                bx::cross(tangent, bx::sub(cameraPosition, position)),
                {0.0f, 0.0f, 1.0f});
            const bx::Vec3 center = bx::add(position, bx::mul(side, point.jitterOffset));
            const bx::Vec3 halfWidth = bx::mul(side, point.width * 0.5f);
            const uint32_t color = static_cast<uint32_t>(colorChannel(point.color[0])) |
                (static_cast<uint32_t>(colorChannel(point.color[1])) << 8) |
                (static_cast<uint32_t>(colorChannel(point.color[2])) << 16) |
                (static_cast<uint32_t>(colorChannel(point.color[3])) << 24);
            const float u = point.distance / textureLength;
            const bx::Vec3 left = bx::sub(center, halfWidth);
            const bx::Vec3 right = bx::add(center, halfWidth);
            if (index > 0)
            {
                // Two triangles from the previous pair (the last two vertices) to this pair.
                const RibbonVertex previousLeft = vertices[vertices.size() - 2];
                const RibbonVertex previousRight = vertices[vertices.size() - 1];
                vertices.resize(vertices.size() - 2);
                const RibbonVertex currentLeft = {left.x, left.y, left.z, u, 0.0f, point.phase, 0.0f, color};
                const RibbonVertex currentRight = {right.x, right.y, right.z, u, 1.0f, point.phase, 0.0f, color};
                for (const RibbonVertex &vertex :
                     {previousLeft, previousRight, currentRight, previousLeft, currentRight, currentLeft})
                {
                    vertices.push_back(vertex);
                }
            }
            // Keep this pair at the end as the next segment's start.
            vertices.push_back({left.x, left.y, left.z, u, 0.0f, point.phase, 0.0f, color});
            vertices.push_back({right.x, right.y, right.z, u, 1.0f, point.phase, 0.0f, color});
        }
        vertices.resize(vertices.size() - 2);
        const uint32_t vertexCount = static_cast<uint32_t>(vertices.size());
        if (vertexCount == 0 || bgfx::getAvailTransientVertexBuffer(vertexCount, m_ribbonLayout) < vertexCount)
        {
            continue;
        }
        bgfx::TransientVertexBuffer vertexBuffer = {};
        bgfx::allocTransientVertexBuffer(&vertexBuffer, vertexCount, m_ribbonLayout);
        std::memcpy(vertexBuffer.data, vertices.data(), vertices.size() * sizeof(RibbonVertex));
        const bool additive = settings.blendMode == EffectBlendMode::Additive;
        const float params[4] = {settings.erosion, settings.core, additive ? 1.0f : 0.0f, settings.fill};
        const float scroll = ribbon.elapsedSeconds * settings.scrollSpeed;
        // The second noise layer drifts more slowly, so the two layers slide through each other.
        const float scrollOffsets[4] = {scroll, scroll * 0.43f + 0.37f, 0.0f, 0.0f};
        float identity[16] = {};
        bx::mtxIdentity(identity);
        bgfx::setTransform(identity);
        bgfx::setVertexBuffer(0, &vertexBuffer, 0, vertexCount);
        bindTexture(
            0,
            resources.textureSamplerHandle(),
            pTexture->handle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_V_CLAMP);
        bgfx::setUniform(m_ribbonParamsUniform, params);
        bgfx::setUniform(m_ribbonScrollUniform, scrollOffsets);
        bgfx::setState(renderState(settings.blendMode));
        const bool glow = additive && resources.glowView() != UINT16_MAX;
        bgfx::submit(viewId, m_ribbonProgram, 0, glow ? BGFX_DISCARD_NONE : BGFX_DISCARD_ALL);
        if (glow)
        {
            bgfx::setState(renderState(settings.blendMode));
            bgfx::submit(resources.glowView(), m_ribbonProgram);
            resources.markGlowDrawn();
        }
        ++m_diagnostics.visibleRibbons;
        ++m_diagnostics.drawCalls;
    }
}

const EffectRenderer::Diagnostics &EffectRenderer::diagnostics() const
{
    return m_diagnostics;
}

struct EffectRenderer::PreparedAtlas
{
    std::string id;
    // Remembered without a texture: an unknown sprite, or one without frames.
    bool known = false;
    uint32_t framesPerSecond = 0;
    float logicalWidth = 0.0f;
    float logicalHeight = 0.0f;
    // A cooked sprite's blocks, packed and edge-bled by tools/cook_effect_textures.py.
    std::optional<Engine::CookedTexture> cooked;
    // A single frame is a texture shared under its path; several are packed into one atlas here.
    std::string singleFramePath;
    PreparedBgraTexture pixels;
    int width = 0;
    int height = 0;
    std::vector<std::array<float, 4>> frameUvs;
    std::string error;
    // A cooked atlas that is missing, corrupt or wrongly prepared is an error, never a fallback.
    std::exception_ptr fatal;
};

void EffectRenderer::preload(const EffectSystem &effects, const EffectResourceLibrary &effectResources,
    const Engine::AssetFileSystem &assetFileSystem, const std::vector<std::string> &extraSpriteResources)
{
    std::vector<std::string> ids;
    for (const std::vector<std::string> &list : {effects.activeSpriteResources(), extraSpriteResources})
    {
        for (const std::string &id : list)
        {
            if (!m_pTextureCache->atlases.contains(id) && std::find(ids.begin(), ids.end(), id) == ids.end())
            {
                ids.push_back(id);
            }
        }
    }
    // Decoded, packed and edge-bled on the load workers, then uploaded here in order.
    std::vector<PreparedAtlas> prepared(ids.size());
    Engine::parallelFor(ids.size(), [&](size_t index)
    {
        prepared[index] = prepareAtlas(effectResources, assetFileSystem, ids[index]);
    });
    for (PreparedAtlas &atlas : prepared)
    {
        finishAtlas(atlas);
    }
}

void EffectRenderer::shareTextureCache(const EffectRenderer &other)
{
    m_pTextureCache = other.m_pTextureCache;
}

const EffectRenderer::Texture *EffectRenderer::loadTexture(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &path)
{
    const auto existing = m_pTextureCache->textures.find(path);
    if (existing != m_pTextureCache->textures.end())
    {
        return &existing->second;
    }
    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::loadImageAssetPixelsBgra(assetFileSystem, path, m_pTextureCache->binaryAssets);
    if (!image)
    {
        return nullptr;
    }
    Texture texture;
    texture.width = image->width;
    texture.height = image->height;
    texture.handle = createBgraTexture2D(
        static_cast<uint16_t>(image->width),
        static_cast<uint16_t>(image->height),
        image->pixels.data(),
        static_cast<uint32_t>(image->pixels.size()),
        TextureFilterProfile::Billboard,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    if (!bgfx::isValid(texture.handle))
    {
        return nullptr;
    }
    return &m_pTextureCache->textures.emplace(path, texture).first->second;
}

EffectRenderer::PreparedAtlas EffectRenderer::prepareAtlas(
    const EffectResourceLibrary &effectResources,
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &spriteResource,
    bool rawTexels)
{
    PreparedAtlas prepared;
    prepared.id = rawTexels ? std::string(RawTexelsKeyPrefix) + spriteResource : spriteResource;
    const EffectSpriteResource *pSprite = effectResources.findSprite(spriteResource);
    if (pSprite == nullptr || (pSprite->framePaths.empty() && pSprite->atlasPath.empty()))
    {
        return prepared;
    }
    prepared.known = true;
    prepared.framesPerSecond = pSprite->framesPerSecond;
    prepared.logicalWidth = static_cast<float>(pSprite->logicalWidth);
    prepared.logicalHeight = static_cast<float>(pSprite->logicalHeight);
    // Without the texture's alpha in additive light, a bled colour in transparent texels would glow. (A cooked atlas
    // is bled when cooked and draws as it is.)
    const BgraTexturePixelPreparation pixelPreparation = rawTexels
        ? BgraTexturePixelPreparation::AlreadyPrepared : BgraTexturePixelPreparation::Required;
    if (!pSprite->atlasPath.empty())
    {
        // A cooked sprite's atlas uploads as stored (BC7 or ASTC blocks, packed and edge-bled as the PNG path packs
        // and bleeds at load).
        const EffectSpriteResource &sprite = *pSprite;
        try
        {
            const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(sprite.atlasPath);
            if (!bytes || bytes->empty())
            {
                throw std::runtime_error("Cannot read cooked effect atlas " + sprite.atlasPath);
            }
            Engine::CookedTexture cooked;
            try
            {
                cooked = Engine::decodeCookedTexture(*bytes);
            }
            catch (const std::exception &exception)
            {
                throw std::runtime_error("Cannot load cooked effect atlas " + sprite.atlasPath + ": "
                    + exception.what());
            }
            const uint32_t columns = std::min(sprite.atlasColumns, sprite.frameCount);
            const uint32_t rows = (sprite.frameCount + sprite.atlasColumns - 1) / sprite.atlasColumns;
            if (cooked.semantic != Engine::ImageMipSemantic::Linear || cooked.alphaCutoff != 0 || cooked.levels != 1
                || cooked.width != columns * sprite.frameWidth || cooked.height != rows * sprite.frameHeight)
            {
                throw std::runtime_error("Cooked effect atlas " + sprite.atlasPath
                    + " does not match its sprite descriptor; run tools/cook_effect_textures.py");
            }
            // A half-texel inset keeps bilinear filtering inside each cell, as for atlases packed at load.
            const float width = static_cast<float>(cooked.width);
            const float height = static_cast<float>(cooked.height);
            for (uint32_t index = 0; index < sprite.frameCount; ++index)
            {
                const float cellX = static_cast<float>(index % sprite.atlasColumns * sprite.frameWidth);
                const float cellY = static_cast<float>(index / sprite.atlasColumns * sprite.frameHeight);
                prepared.frameUvs.push_back({
                    (cellX + 0.5f) / width,
                    (cellY + 0.5f) / height,
                    (cellX + static_cast<float>(sprite.frameWidth) - 0.5f) / width,
                    (cellY + static_cast<float>(sprite.frameHeight) - 0.5f) / height,
                });
            }
            prepared.width = cooked.width;
            prepared.height = cooked.height;
            prepared.cooked = std::move(cooked);
        }
        catch (...)
        {
            prepared.fatal = std::current_exception();
        }
        return prepared;
    }
    Engine::BinaryAssetCache binaryAssets;
    if (pSprite->framePaths.size() == 1)
    {
        const std::string &framePath = pSprite->framePaths.front();
        prepared.singleFramePath = rawTexels ? std::string(RawTexelsKeyPrefix) + framePath : framePath;
        const std::optional<Engine::ImagePixelsBgra> image =
            Engine::loadImageAssetPixelsBgra(assetFileSystem, framePath, binaryAssets);
        if (image)
        {
            prepared.width = image->width;
            prepared.height = image->height;
            prepared.pixels = prepareBgraTexture2D(static_cast<uint16_t>(image->width),
                static_cast<uint16_t>(image->height), image->pixels.data(),
                static_cast<uint32_t>(image->pixels.size()), TextureFilterProfile::Billboard, pixelPreparation);
        }
        prepared.frameUvs = {{0.0f, 0.0f, 1.0f, 1.0f}};
        return prepared;
    }
    std::vector<Engine::ImagePixelsBgra> frames;
    frames.reserve(pSprite->framePaths.size());
    for (const std::string &path : pSprite->framePaths)
    {
        std::optional<Engine::ImagePixelsBgra> image =
            Engine::loadImageAssetPixelsBgra(assetFileSystem, path, binaryAssets);
        if (!image || (!frames.empty() && (image->width != frames.front().width ||
            image->height != frames.front().height)))
        {
            prepared.error = "Effect sprite " + spriteResource + ": frames must load and share one size";
            return prepared;
        }
        frames.push_back(std::move(*image));
    }
    // A near-square grid of cells; a half-texel inset keeps bilinear filtering inside each cell.
    const int frameWidth = frames.front().width;
    const int frameHeight = frames.front().height;
    const int columns = static_cast<int>(std::ceil(std::sqrt(static_cast<float>(frames.size()))));
    const int rows = (static_cast<int>(frames.size()) + columns - 1) / columns;
    const int width = frameWidth * columns;
    const int height = frameHeight * rows;
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * height * 4, 0);
    for (size_t index = 0; index < frames.size(); ++index)
    {
        const int cellX = static_cast<int>(index) % columns * frameWidth;
        const int cellY = static_cast<int>(index) / columns * frameHeight;
        for (int row = 0; row < frameHeight; ++row)
        {
            std::memcpy(
                pixels.data() + (static_cast<size_t>(cellY + row) * width + cellX) * 4,
                frames[index].pixels.data() + static_cast<size_t>(row) * frameWidth * 4,
                static_cast<size_t>(frameWidth) * 4);
        }
        prepared.frameUvs.push_back({
            (cellX + 0.5f) / width,
            (cellY + 0.5f) / height,
            (cellX + frameWidth - 0.5f) / width,
            (cellY + frameHeight - 0.5f) / height,
        });
    }
    prepared.width = width;
    prepared.height = height;
    prepared.pixels = prepareBgraTexture2D(static_cast<uint16_t>(width), static_cast<uint16_t>(height),
        pixels.data(), static_cast<uint32_t>(pixels.size()), TextureFilterProfile::Billboard, pixelPreparation);
    return prepared;
}

const EffectRenderer::SpriteAtlas *EffectRenderer::finishAtlas(PreparedAtlas &prepared)
{
    // A failed sprite is remembered too (without a texture), so it is not retried every frame.
    SpriteAtlas &atlas = m_pTextureCache->atlases[prepared.id];
    if (!prepared.known)
    {
        return nullptr;
    }
    atlas.framesPerSecond = prepared.framesPerSecond;
    atlas.logicalWidth = prepared.logicalWidth;
    atlas.logicalHeight = prepared.logicalHeight;
    if (prepared.fatal)
    {
        std::rethrow_exception(prepared.fatal);
    }
    if (!prepared.error.empty())
    {
        std::cerr << prepared.error << '\n';
        return nullptr;
    }
    constexpr uint64_t ClampFlags = BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP;
    if (!prepared.singleFramePath.empty())
    {
        if (const auto existing = m_pTextureCache->textures.find(prepared.singleFramePath);
            existing != m_pTextureCache->textures.end())
        {
            atlas.pTexture = &existing->second;
        }
        else if (!prepared.pixels.levels.empty())
        {
            Texture texture;
            texture.width = prepared.width;
            texture.height = prepared.height;
            texture.handle = createPreparedBgraTexture2D(prepared.pixels, TextureFilterProfile::Billboard, ClampFlags);
            if (bgfx::isValid(texture.handle))
            {
                atlas.pTexture = &m_pTextureCache->textures.emplace(prepared.singleFramePath, texture).first->second;
            }
        }
        atlas.frameUvs = prepared.frameUvs;
        return atlas.pTexture != nullptr ? &atlas : nullptr;
    }
    Texture texture;
    texture.width = prepared.width;
    texture.height = prepared.height;
    texture.handle = prepared.cooked
        ? createCookedTexture2D(*prepared.cooked, TextureFilterProfile::Billboard, ClampFlags)
        : createPreparedBgraTexture2D(prepared.pixels, TextureFilterProfile::Billboard, ClampFlags);
    if (!bgfx::isValid(texture.handle))
    {
        return nullptr;
    }
    atlas.frameUvs = prepared.frameUvs;
    atlas.pTexture = &m_pTextureCache->textures.emplace("atlas:" + prepared.id, texture).first->second;
    return &atlas;
}

const EffectRenderer::SpriteAtlas *EffectRenderer::loadAtlas(
    const EffectResourceLibrary &effectResources,
    const Engine::AssetFileSystem &assetFileSystem,
    std::string_view spriteResource,
    bool rawTexels)
{
    const std::string rawKey =
        rawTexels ? std::string(RawTexelsKeyPrefix) + std::string(spriteResource) : std::string();
    const auto existing = m_pTextureCache->atlases.find(rawTexels ? std::string_view(rawKey) : spriteResource);
    if (existing != m_pTextureCache->atlases.end())
    {
        return existing->second.pTexture != nullptr ? &existing->second : nullptr;
    }
    PreparedAtlas prepared = prepareAtlas(effectResources, assetFileSystem, std::string(spriteResource), rawTexels);
    return finishAtlas(prepared);
}
}
