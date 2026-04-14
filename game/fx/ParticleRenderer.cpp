#include "game/fx/ParticleRenderer.h"

#include "game/fx/FxSharedTypes.h"
#include "game/fx/ParticleSystem.h"
#include "game/outdoor/OutdoorGameView.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *ParticleSoftBlobTextureName = "__particle_soft_blob__";
constexpr const char *ParticleSmokeTextureName = "__particle_smoke__";
constexpr const char *ParticleMistTextureName = "__particle_mist__";
constexpr const char *ParticleEmberTextureName = "__particle_ember__";
constexpr const char *ParticleSparkTextureName = "__particle_spark__";

constexpr uint64_t ParticleAlphaRenderState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA;

constexpr uint64_t ParticleAdditiveRenderState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ADD;

constexpr size_t ParticleMaterialCount = 5;
constexpr size_t ParticleBlendModeCount = 2;
constexpr float Pi = 3.14159265358979323846f;
constexpr float ParticleVerticalFovRadians = 60.0f * (Pi / 180.0f);
constexpr float ParticleTrailCullDistance = 12288.0f;
constexpr float ParticleImpactCullDistance = 12288.0f;
constexpr float ParticleDecorationCullDistance = 9830.4f;
constexpr float ParticleBuffCullDistance = 8192.0f;
constexpr float ParticleMiscCullDistance = 8192.0f;

uint8_t channelAt(uint32_t colorAbgr, int shift)
{
    return static_cast<uint8_t>((colorAbgr >> shift) & 0xffu);
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

uint32_t lerpColorAbgr(uint32_t startColorAbgr, uint32_t endColorAbgr, float t)
{
    const float clampedT = std::clamp(t, 0.0f, 1.0f);

    const auto lerpChannel =
        [clampedT](uint8_t startChannel, uint8_t endChannel)
        {
            return static_cast<uint8_t>(std::lround(
                static_cast<float>(startChannel)
                + (static_cast<float>(endChannel) - static_cast<float>(startChannel)) * clampedT));
        };

    return makeAbgr(
        lerpChannel(channelAt(startColorAbgr, 0), channelAt(endColorAbgr, 0)),
        lerpChannel(channelAt(startColorAbgr, 8), channelAt(endColorAbgr, 8)),
        lerpChannel(channelAt(startColorAbgr, 16), channelAt(endColorAbgr, 16)),
        lerpChannel(channelAt(startColorAbgr, 24), channelAt(endColorAbgr, 24)));
}

size_t materialIndex(FxParticleMaterial material)
{
    switch (material)
    {
    case FxParticleMaterial::SoftBlob:
        return 0;
    case FxParticleMaterial::Smoke:
        return 1;
    case FxParticleMaterial::Mist:
        return 2;
    case FxParticleMaterial::Ember:
        return 3;
    case FxParticleMaterial::Spark:
        return 4;
    }

    return 0;
}

size_t blendModeIndex(FxParticleBlendMode blendMode)
{
    switch (blendMode)
    {
    case FxParticleBlendMode::Alpha:
        return 0;
    case FxParticleBlendMode::Additive:
        return 1;
    }

    return 0;
}

size_t batchIndex(FxParticleMaterial material, FxParticleBlendMode blendMode)
{
    return materialIndex(material) * ParticleBlendModeCount + blendModeIndex(blendMode);
}

float particleCullDistance(FxParticleTag tag)
{
    switch (tag)
    {
    case FxParticleTag::Trail:
        return ParticleTrailCullDistance;
    case FxParticleTag::Impact:
        return ParticleImpactCullDistance;
    case FxParticleTag::DecorationEmitter:
        return ParticleDecorationCullDistance;
    case FxParticleTag::Buff:
        return ParticleBuffCullDistance;
    case FxParticleTag::Misc:
        return ParticleMiscCullDistance;
    }

    return ParticleMiscCullDistance;
}

const char *textureNameForMaterial(FxParticleMaterial material)
{
    switch (material)
    {
    case FxParticleMaterial::SoftBlob:
        return ParticleSoftBlobTextureName;
    case FxParticleMaterial::Smoke:
        return ParticleSmokeTextureName;
    case FxParticleMaterial::Mist:
        return ParticleMistTextureName;
    case FxParticleMaterial::Ember:
        return ParticleEmberTextureName;
    case FxParticleMaterial::Spark:
        return ParticleSparkTextureName;
    }

    return ParticleSoftBlobTextureName;
}

std::vector<uint8_t> buildRadialPixels(
    int width,
    int height,
    float exponent,
    float innerBias,
    float outerScale)
{
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4, 0);

    for (int y = 0; y < height; ++y)
    {
        for (int x = 0; x < width; ++x)
        {
            const float normalizedX = ((static_cast<float>(x) + 0.5f) / static_cast<float>(width)) * 2.0f - 1.0f;
            const float normalizedY = ((static_cast<float>(y) + 0.5f) / static_cast<float>(height)) * 2.0f - 1.0f;
            const float radialDistance = std::sqrt(normalizedX * normalizedX + normalizedY * normalizedY);
            const float baseAlpha = std::pow(
                std::max(0.0f, 1.0f - std::clamp(radialDistance * outerScale - innerBias, 0.0f, 1.0f)),
                exponent);
            const size_t offset =
                (static_cast<size_t>(y) * static_cast<size_t>(width) + static_cast<size_t>(x)) * 4;
            pixels[offset + 0] = 255;
            pixels[offset + 1] = 255;
            pixels[offset + 2] = 255;
            pixels[offset + 3] = static_cast<uint8_t>(std::lround(baseAlpha * 255.0f));
        }
    }

    return pixels;
}

std::vector<uint8_t> buildSmokePixels(int width, int height)
{
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4, 0);

    for (int y = 0; y < height; ++y)
    {
        for (int x = 0; x < width; ++x)
        {
            const float normalizedX = ((static_cast<float>(x) + 0.5f) / static_cast<float>(width)) * 2.0f - 1.0f;
            const float normalizedY = ((static_cast<float>(y) + 0.5f) / static_cast<float>(height)) * 2.0f - 1.0f;
            const float radialDistance = std::sqrt(normalizedX * normalizedX + normalizedY * normalizedY);
            const float lobeA = std::sin((normalizedX + 0.35f) * 4.7f) * 0.08f;
            const float lobeB = std::cos((normalizedY - 0.18f) * 5.1f) * 0.07f;
            const float alpha = std::pow(
                std::max(0.0f, 1.0f - std::clamp(radialDistance * 1.1f + lobeA + lobeB, 0.0f, 1.0f)),
                1.8f);
            const size_t offset =
                (static_cast<size_t>(y) * static_cast<size_t>(width) + static_cast<size_t>(x)) * 4;
            pixels[offset + 0] = 255;
            pixels[offset + 1] = 255;
            pixels[offset + 2] = 255;
            pixels[offset + 3] = static_cast<uint8_t>(std::lround(alpha * 255.0f));
        }
    }

    return pixels;
}

std::vector<uint8_t> buildSparkPixels(int width, int height)
{
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4, 0);

    for (int y = 0; y < height; ++y)
    {
        for (int x = 0; x < width; ++x)
        {
            const float normalizedX = ((static_cast<float>(x) + 0.5f) / static_cast<float>(width)) * 2.0f - 1.0f;
            const float normalizedY = ((static_cast<float>(y) + 0.5f) / static_cast<float>(height)) * 2.0f - 1.0f;
            const float streakAlpha = std::max(0.0f, 1.0f - std::abs(normalizedX));
            const float coreAlpha = std::max(0.0f, 1.0f - std::abs(normalizedY) * 3.6f);
            const float alpha = std::pow(streakAlpha, 1.3f) * std::pow(coreAlpha, 2.1f);
            const size_t offset =
                (static_cast<size_t>(y) * static_cast<size_t>(width) + static_cast<size_t>(x)) * 4;
            pixels[offset + 0] = 255;
            pixels[offset + 1] = 255;
            pixels[offset + 2] = 255;
            pixels[offset + 3] = static_cast<uint8_t>(std::lround(alpha * 255.0f));
        }
    }

    return pixels;
}

bx::Vec3 normalizeOrFallback(const bx::Vec3 &value, const bx::Vec3 &fallback)
{
    const float lengthSquared = bx::dot(value, value);

    if (lengthSquared <= 0.000001f)
    {
        return fallback;
    }

    return bx::mul(value, 1.0f / std::sqrt(lengthSquared));
}

bool shouldRenderParticle(
    const FxParticleState &particle,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &cameraForward,
    const bx::Vec3 &cameraRight,
    const bx::Vec3 &cameraUp,
    float aspectRatio)
{
    const bx::Vec3 toParticle = {
        particle.x - cameraPosition.x,
        particle.y - cameraPosition.y,
        particle.z - cameraPosition.z
    };
    const float cullDistance = particleCullDistance(particle.tag);
    const float distanceSquared = bx::dot(toParticle, toParticle);

    if (distanceSquared > cullDistance * cullDistance)
    {
        return false;
    }

    const float maxSize = std::max(particle.size, particle.endSize) * std::max(1.0f, particle.stretch);
    const float radiusPadding = std::max(8.0f, maxSize * 2.5f);
    const float depth = bx::dot(toParticle, cameraForward);

    if (depth < -radiusPadding)
    {
        return false;
    }

    const float verticalHalfFovTangent = std::tan(ParticleVerticalFovRadians * 0.5f);
    const float horizontalHalfFovTangent = verticalHalfFovTangent * std::max(aspectRatio, 1.0f);
    const float clampedDepth = std::max(depth, 0.0f);
    const float horizontalDistance = std::abs(bx::dot(toParticle, cameraRight));
    const float verticalDistance = std::abs(bx::dot(toParticle, cameraUp));
    const float frustumPaddingScale = particle.tag == FxParticleTag::DecorationEmitter ? 1.35f : 1.15f;
    const float horizontalLimit = (clampedDepth * horizontalHalfFovTangent + radiusPadding) * frustumPaddingScale;
    const float verticalLimit = (clampedDepth * verticalHalfFovTangent + radiusPadding) * frustumPaddingScale;

    if (horizontalDistance > horizontalLimit || verticalDistance > verticalLimit)
    {
        return false;
    }

    return true;
}
}

void ParticleRenderer::initializeResources(OutdoorGameView &view)
{
    auto ensureParticleTexture =
        [&view](const char *pTextureName, int width, int height, const std::vector<uint8_t> &pixels)
        {
            if (view.findBillboardTexture(pTextureName) != nullptr)
            {
                return;
            }

            OutdoorGameView::BillboardTextureHandle particleTexture = {};
            particleTexture.textureName = pTextureName;
            particleTexture.paletteId = 0;
            particleTexture.width = width;
            particleTexture.height = height;
            particleTexture.physicalWidth = width;
            particleTexture.physicalHeight = height;
            particleTexture.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(width),
                static_cast<uint16_t>(height),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP,
                bgfx::copy(pixels.data(), static_cast<uint32_t>(pixels.size())));

            if (bgfx::isValid(particleTexture.textureHandle))
            {
                view.m_billboardTextureHandles.push_back(std::move(particleTexture));
                view.m_billboardTextureIndexByPalette[0][pTextureName] =
                    view.m_billboardTextureHandles.size() - 1;
            }
        };

    ensureParticleTexture(ParticleSoftBlobTextureName, 64, 64, buildRadialPixels(64, 64, 2.6f, 0.0f, 1.0f));
    ensureParticleTexture(ParticleSmokeTextureName, 64, 64, buildSmokePixels(64, 64));
    ensureParticleTexture(ParticleMistTextureName, 64, 64, buildRadialPixels(64, 64, 1.6f, 0.15f, 0.9f));
    ensureParticleTexture(ParticleEmberTextureName, 32, 32, buildRadialPixels(32, 32, 3.0f, -0.1f, 1.3f));
    ensureParticleTexture(ParticleSparkTextureName, 64, 32, buildSparkPixels(64, 32));

    for (size_t material = 0; material < ParticleMaterialCount; ++material)
    {
        const OutdoorGameView::BillboardTextureHandle *pTexture =
            view.findBillboardTexture(textureNameForMaterial(static_cast<FxParticleMaterial>(material)));
        view.m_particleTextureHandleIndices[material] =
            pTexture != nullptr ? pTexture->textureHandle.idx : bgfx::kInvalidHandle;
    }
}

void ParticleRenderer::renderParticles(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition,
    float aspectRatio)
{
    if (!bgfx::isValid(view.m_particleProgramHandle) || !bgfx::isValid(view.m_terrainTextureSamplerHandle))
    {
        return;
    }

    const std::vector<FxParticleState> &particles = view.m_particleSystem.particles();

    if (particles.empty())
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const bx::Vec3 cameraForward =
        normalizeOrFallback(bx::mul(bx::cross(cameraRight, cameraUp), -1.0f), {0.0f, 0.0f, 1.0f});
    std::array<std::vector<OutdoorGameView::LitBillboardVertex>, ParticleMaterialCount * ParticleBlendModeCount>
        &batches = view.m_particleVertexBatches;
    std::vector<const FxParticleState *> visibleParticles;
    visibleParticles.reserve(particles.size());
    auto writeParticleQuad =
        [](OutdoorGameView::LitBillboardVertex *pVertices,
           const bx::Vec3 &center,
           const bx::Vec3 &right,
           const bx::Vec3 &up,
           uint32_t colorAbgr)
        {
            pVertices[0] = {
                center.x - right.x - up.x,
                center.y - right.y - up.y,
                center.z - right.z - up.z,
                0.0f,
                1.0f,
                colorAbgr
            };
            pVertices[1] = {
                center.x - right.x + up.x,
                center.y - right.y + up.y,
                center.z - right.z + up.z,
                0.0f,
                0.0f,
                colorAbgr
            };
            pVertices[2] = {
                center.x + right.x + up.x,
                center.y + right.y + up.y,
                center.z + right.z + up.z,
                1.0f,
                0.0f,
                colorAbgr
            };
            pVertices[3] = pVertices[0];
            pVertices[4] = pVertices[2];
            pVertices[5] = {
                center.x + right.x - up.x,
                center.y + right.y - up.y,
                center.z + right.z - up.z,
                1.0f,
                1.0f,
                colorAbgr
            };
        };

    std::array<size_t, ParticleMaterialCount * ParticleBlendModeCount> batchVertexCounts = {};
    std::array<size_t, ParticleMaterialCount * ParticleBlendModeCount> batchWriteOffsets = {};

    for (const FxParticleState &particle : particles)
    {
        if (!shouldRenderParticle(particle, cameraPosition, cameraForward, cameraRight, cameraUp, aspectRatio))
        {
            continue;
        }

        visibleParticles.push_back(&particle);
        batchVertexCounts[batchIndex(particle.material, particle.blendMode)] += 6;
    }

    bool hasVisibleParticles = false;

    for (size_t batchIndexValue = 0; batchIndexValue < batches.size(); ++batchIndexValue)
    {
        std::vector<OutdoorGameView::LitBillboardVertex> &batch = batches[batchIndexValue];
        const size_t batchVertexCount = batchVertexCounts[batchIndexValue];

        if (batch.capacity() < batchVertexCount)
        {
            batch.reserve(batchVertexCount);
        }

        batch.resize(batchVertexCount);
        hasVisibleParticles = hasVisibleParticles || batchVertexCount > 0;
    }

    if (!hasVisibleParticles)
    {
        return;
    }

    for (const FxParticleState *pParticle : visibleParticles)
    {
        const FxParticleState &particle = *pParticle;

        const float lifetimeSeconds = std::max(0.001f, particle.lifetimeSeconds);
        const float normalizedAge = std::clamp(particle.ageSeconds / lifetimeSeconds, 0.0f, 1.0f);
        const float fadeOutAlpha = (1.0f - normalizedAge) * (1.0f - normalizedAge);
        const float fadeInAlpha =
            particle.fadeInSeconds > 0.0001f
                ? std::clamp(particle.ageSeconds / particle.fadeInSeconds, 0.0f, 1.0f)
                : 1.0f;
        const float fadeAlpha = fadeOutAlpha * fadeInAlpha;
        const uint32_t colorAbgr = lerpColorAbgr(particle.startColorAbgr, particle.endColorAbgr, normalizedAge);
        const uint8_t fadedAlpha = static_cast<uint8_t>(
            std::lround(static_cast<float>(channelAt(colorAbgr, 24)) * std::clamp(fadeAlpha, 0.0f, 1.0f)));
        const uint32_t finalColorAbgr =
            (colorAbgr & 0x00ffffffu) | (static_cast<uint32_t>(fadedAlpha) << 24);

        if (fadedAlpha == 0)
        {
            continue;
        }

        const float currentSize = particle.size + (particle.endSize - particle.size) * normalizedAge;
        const float halfWidth = currentSize * 0.5f;
        const bx::Vec3 center = {particle.x, particle.y, particle.z};

        bx::Vec3 right = {0.0f, 0.0f, 0.0f};
        bx::Vec3 up = {0.0f, 0.0f, 0.0f};

        if (particle.alignment == FxParticleAlignment::VelocityStretched)
        {
            const float screenVelocityX =
                particle.velocityX * cameraRight.x
                + particle.velocityY * cameraRight.y
                + particle.velocityZ * cameraRight.z;
            const float screenVelocityY =
                particle.velocityX * cameraUp.x + particle.velocityY * cameraUp.y + particle.velocityZ * cameraUp.z;
            const bx::Vec3 majorAxis = normalizeOrFallback(
                {
                    cameraRight.x * screenVelocityX + cameraUp.x * screenVelocityY,
                    cameraRight.y * screenVelocityX + cameraUp.y * screenVelocityY,
                    cameraRight.z * screenVelocityX + cameraUp.z * screenVelocityY
                },
                cameraRight);
            const bx::Vec3 minorAxis = normalizeOrFallback(bx::cross(majorAxis, cameraForward), cameraUp);
            right = bx::mul(majorAxis, halfWidth * std::max(1.0f, particle.stretch));
            up = bx::mul(minorAxis, halfWidth);
        }
        else if (particle.alignment == FxParticleAlignment::GroundAligned)
        {
            const float sine = std::sin(particle.rotationRadians);
            const float cosine = std::cos(particle.rotationRadians);
            right = {cosine * halfWidth, sine * halfWidth, 0.0f};
            up = {-sine * halfWidth, cosine * halfWidth, 0.0f};
        }
        else
        {
            const float sine = std::sin(particle.rotationRadians);
            const float cosine = std::cos(particle.rotationRadians);
            right = {
                (cameraRight.x * cosine + cameraUp.x * sine) * halfWidth,
                (cameraRight.y * cosine + cameraUp.y * sine) * halfWidth,
                (cameraRight.z * cosine + cameraUp.z * sine) * halfWidth
            };
            up = {
                (-cameraRight.x * sine + cameraUp.x * cosine) * halfWidth,
                (-cameraRight.y * sine + cameraUp.y * cosine) * halfWidth,
                (-cameraRight.z * sine + cameraUp.z * cosine) * halfWidth
            };
        }

        const size_t particleBatchIndex = batchIndex(particle.material, particle.blendMode);
        std::vector<OutdoorGameView::LitBillboardVertex> &batch = batches[particleBatchIndex];
        OutdoorGameView::LitBillboardVertex *pWrite =
            batch.data() + batchWriteOffsets[particleBatchIndex];
        writeParticleQuad(pWrite, center, right, up, finalColorAbgr);
        batchWriteOffsets[particleBatchIndex] += 6;
    }

    auto submitParticleBatch =
        [&](const std::vector<OutdoorGameView::LitBillboardVertex> &vertices, uint64_t renderState, size_t material)
        {
            bgfx::TextureHandle textureHandle = {view.m_particleTextureHandleIndices[material]};

            if (vertices.empty() || !bgfx::isValid(textureHandle))
            {
                return;
            }

            if (bgfx::getAvailTransientVertexBuffer(
                    static_cast<uint32_t>(vertices.size()),
                    OutdoorGameView::LitBillboardVertex::ms_layout) < vertices.size())
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(vertices.size()),
                OutdoorGameView::LitBillboardVertex::ms_layout);
            std::memcpy(
                transientVertexBuffer.data,
                vertices.data(),
                static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::LitBillboardVertex)));

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
            bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, textureHandle);
            bgfx::setState(renderState);
            bgfx::submit(viewId, view.m_particleProgramHandle);
        };

    for (size_t material = 0; material < ParticleMaterialCount; ++material)
    {
        submitParticleBatch(
            batches[batchIndex(static_cast<FxParticleMaterial>(material), FxParticleBlendMode::Alpha)],
            ParticleAlphaRenderState,
            material);
        submitParticleBatch(
            batches[batchIndex(static_cast<FxParticleMaterial>(material), FxParticleBlendMode::Additive)],
            ParticleAdditiveRenderState,
            material);
    }
}
}
