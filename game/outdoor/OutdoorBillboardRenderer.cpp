#include "game/outdoor/OutdoorBillboardRenderer.h"

#include "game/app/GameSession.h"
#include "game/data/GameDataRepository.h"
#include "game/fx/ParticleRecipes.h"
#include "game/fx/ParticleSystem.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorFogProfile.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/render/TextureFiltering.h"
#include "game/StringUtils.h"
#include "game/scene/OutdoorSceneRuntime.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <future>
#include <iostream>
#include <iterator>
#include <limits>
#include <optional>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float RuntimeProjectileRenderDistance = 12288.0f;
constexpr float RuntimeProjectileRenderDistanceSquared =
    RuntimeProjectileRenderDistance * RuntimeProjectileRenderDistance;
constexpr float DecorationBillboardRenderDistance = 16384.0f;
constexpr float DecorationBillboardRenderDistanceSquared =
    DecorationBillboardRenderDistance * DecorationBillboardRenderDistance;
constexpr float ActorBillboardRenderDistance = 16384.0f;
constexpr float ActorBillboardRenderDistanceSquared =
    ActorBillboardRenderDistance * ActorBillboardRenderDistance;
constexpr uint64_t RenderHitchLogThresholdNanoseconds = 16 * 1000 * 1000;
constexpr float BillboardNearDepth = 0.1f;
constexpr bool DebugProjectileDrawLogging = false;
constexpr uint64_t BillboardAlphaRenderState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA;
constexpr bool DebugActorRenderHitchLogging = false;
constexpr size_t PreloadDecodeWorkerCount = 4;
constexpr bool DebugSpritePreloadLogging = false;
constexpr uint64_t ColoredAlphaRenderState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ALPHA;
constexpr uint64_t ColoredAdditiveRenderState =
    BGFX_STATE_WRITE_RGB
    | BGFX_STATE_WRITE_A
    | BGFX_STATE_DEPTH_TEST_LEQUAL
    | BGFX_STATE_BLEND_ADD;
constexpr float BillboardAmbientLight = 0.85f;
constexpr float BillboardLightContributionScale = 0.7f;
constexpr const char *ContactShadowTextureName = "__contact_shadow_blob__";
constexpr float HoveredActorOutlineThicknessPixels = 2.0f;
constexpr float OutdoorFogNearOpacity = 0.04f;
constexpr float OutdoorFogStrongOpacity = 176.0f / 255.0f;

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

uint32_t makeTintedFogColor(
    uint8_t brightness,
    bool hasFogTint,
    uint8_t tintRed,
    uint8_t tintGreen,
    uint8_t tintBlue)
{
    if (!hasFogTint)
    {
        return makeAbgr(brightness, brightness, brightness);
    }

    const uint8_t red =
        static_cast<uint8_t>(std::clamp(std::lround(static_cast<float>(brightness) * tintRed / 255.0f), 0l, 255l));
    const uint8_t green =
        static_cast<uint8_t>(std::clamp(std::lround(static_cast<float>(brightness) * tintGreen / 255.0f), 0l, 255l));
    const uint8_t blue =
        static_cast<uint8_t>(std::clamp(std::lround(static_cast<float>(brightness) * tintBlue / 255.0f), 0l, 255l));
    return makeAbgr(red, green, blue);
}

struct SpriteTexturePreloadRequest
{
    std::string textureName;
    int16_t paletteId = 0;
    std::vector<uint8_t> bitmapBytes;
    std::optional<std::array<uint8_t, 256 * 3>> overridePalette;
};

struct DecodedSpriteTexture
{
    std::string textureName;
    int16_t paletteId = 0;
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};

uint32_t resolveHoveredActorOutlineColor(const OutdoorWorldRuntime::MapActorState &actor)
{
    if (actor.isDead)
    {
        return makeAbgr(255, 224, 64);
    }

    if (actor.hostileToParty)
    {
        return makeAbgr(255, 64, 64);
    }

    return makeAbgr(64, 255, 64);
}

uint32_t hoveredWorldItemOutlineColor()
{
    return makeAbgr(64, 128, 255);
}

uint32_t computeBillboardFogColorAbgr(const OutdoorWorldRuntime::AtmosphereState &atmosphereState)
{
    if (atmosphereState.isNight)
    {
        if (atmosphereState.hasFogTint)
        {
            return makeTintedFogColor(
                48,
                true,
                atmosphereState.fogTintRed,
                atmosphereState.fogTintGreen,
                atmosphereState.fogTintBlue);
        }

        return atmosphereState.redFog ? makeAbgr(48, 18, 18) : makeAbgr(31, 31, 31);
    }

    const int fogLevel = std::clamp(
        static_cast<int>(std::lround(
            (1.0f - atmosphereState.fogDensity) * 200.0f + atmosphereState.fogDensity * 31.0f)),
        0,
        255);
    const uint8_t red = static_cast<uint8_t>(fogLevel);

    if (atmosphereState.hasFogTint)
    {
        return makeTintedFogColor(
            red,
            true,
            atmosphereState.fogTintRed,
            atmosphereState.fogTintGreen,
            atmosphereState.fogTintBlue);
    }

    if (atmosphereState.redFog)
    {
        const uint8_t green =
            static_cast<uint8_t>(std::lround(static_cast<float>(fogLevel) * 0.35f));
        const uint8_t blue =
            static_cast<uint8_t>(std::lround(static_cast<float>(fogLevel) * 0.35f));
        return makeAbgr(red, green, blue);
    }

    return makeAbgr(red, red, red);
}

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgra(
    const std::vector<uint8_t> &bitmapBytes,
    const std::optional<std::array<uint8_t, 256 * 3>> &overridePalette,
    int &width,
    int &height)
{
    if (bitmapBytes.empty())
    {
        return std::nullopt;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes.data(), bitmapBytes.size());

    if (pIoStream == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return std::nullopt;
    }

    SDL_Palette *pBasePalette = SDL_GetSurfacePalette(pLoadedSurface);
    const bool canApplyPalette =
        overridePalette.has_value()
        && pLoadedSurface->format == SDL_PIXELFORMAT_INDEX8
        && pBasePalette != nullptr;

    if (canApplyPalette)
    {
        width = pLoadedSurface->w;
        height = pLoadedSurface->h;
        std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);

        for (int row = 0; row < height; ++row)
        {
            const uint8_t *pSourceRow = static_cast<const uint8_t *>(pLoadedSurface->pixels)
                + static_cast<ptrdiff_t>(row * pLoadedSurface->pitch);

            for (int column = 0; column < width; ++column)
            {
                const uint8_t paletteIndex = pSourceRow[column];
                const SDL_Color sourceColor =
                    paletteIndex < pBasePalette->ncolors
                        ? pBasePalette->colors[paletteIndex]
                        : SDL_Color{0, 0, 0, 255};
                const bool isZeroIndexKey = paletteIndex == 0;
                const bool isMagentaKey =
                    sourceColor.r >= 248 && sourceColor.g <= 8 && sourceColor.b >= 248;
                const bool isTealKey =
                    sourceColor.r <= 8 && sourceColor.g >= 248 && sourceColor.b >= 248;
                const size_t paletteOffset = static_cast<size_t>(paletteIndex) * 3;
                const size_t pixelOffset =
                    (static_cast<size_t>(row) * static_cast<size_t>(width) + static_cast<size_t>(column)) * 4;

                pixels[pixelOffset + 0] = (*overridePalette)[paletteOffset + 2];
                pixels[pixelOffset + 1] = (*overridePalette)[paletteOffset + 1];
                pixels[pixelOffset + 2] = (*overridePalette)[paletteOffset + 0];
                pixels[pixelOffset + 3] = (isZeroIndexKey || isMagentaKey || isTealKey) ? 0 : 255;
            }
        }

        SDL_DestroySurface(pLoadedSurface);
        return pixels;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return std::nullopt;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);

    for (int row = 0; row < height; ++row)
    {
        const uint8_t *pSourceRow = static_cast<const uint8_t *>(pConvertedSurface->pixels)
            + static_cast<ptrdiff_t>(row * pConvertedSurface->pitch);
        uint8_t *pTargetRow = pixels.data() + static_cast<size_t>(row) * static_cast<size_t>(width) * 4;
        std::memcpy(pTargetRow, pSourceRow, static_cast<size_t>(width) * 4);
    }

    for (size_t pixelOffset = 0; pixelOffset < pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = pixels[pixelOffset + 0];
        const uint8_t green = pixels[pixelOffset + 1];
        const uint8_t red = pixels[pixelOffset + 2];
        const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
        const bool isTealKey = red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isTealKey)
        {
            pixels[pixelOffset + 3] = 0;
        }
    }

    SDL_DestroySurface(pConvertedSurface);
    return pixels;
}

struct ProjectedBillboardRect
{
    float left = 0.0f;
    float right = 0.0f;
    float top = 0.0f;
    float bottom = 0.0f;
};

bool projectWorldPointToScreenForKeyboardCache(
    const bx::Vec3 &worldPoint,
    int viewWidth,
    int viewHeight,
    const float *pViewProjectionMatrix,
    float &screenX,
    float &screenY)
{
    const bx::Vec3 projectedPoint = bx::mulH(worldPoint, pViewProjectionMatrix);

    if (!std::isfinite(projectedPoint.x)
        || !std::isfinite(projectedPoint.y)
        || !std::isfinite(projectedPoint.z))
    {
        return false;
    }

    screenX = (projectedPoint.x * 0.5f + 0.5f) * static_cast<float>(viewWidth);
    screenY = (1.0f - (projectedPoint.y * 0.5f + 0.5f)) * static_cast<float>(viewHeight);
    return std::isfinite(screenX) && std::isfinite(screenY);
}

bool projectVisibleBillboardRect(
    const bx::Vec3 &center,
    const bx::Vec3 &right,
    const bx::Vec3 &up,
    int viewWidth,
    int viewHeight,
    const float *pViewProjectionMatrix,
    ProjectedBillboardRect &rect)
{
    const std::array<bx::Vec3, 4> corners = {{
        {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z},
        {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z},
        {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z},
        {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z}
    }};
    bool hasProjection = false;
    float minX = 0.0f;
    float maxX = 0.0f;
    float minY = 0.0f;
    float maxY = 0.0f;

    for (const bx::Vec3 &corner : corners)
    {
        float projectedX = 0.0f;
        float projectedY = 0.0f;

        if (!projectWorldPointToScreenForKeyboardCache(
                corner,
                viewWidth,
                viewHeight,
                pViewProjectionMatrix,
                projectedX,
                projectedY))
        {
            return false;
        }

        if (!hasProjection)
        {
            minX = projectedX;
            maxX = projectedX;
            minY = projectedY;
            maxY = projectedY;
            hasProjection = true;
            continue;
        }

        minX = std::min(minX, projectedX);
        maxX = std::max(maxX, projectedX);
        minY = std::min(minY, projectedY);
        maxY = std::max(maxY, projectedY);
    }

    if (!hasProjection)
    {
        return false;
    }

    rect.left = std::clamp(minX, 0.0f, static_cast<float>(viewWidth - 1));
    rect.right = std::clamp(maxX, 0.0f, static_cast<float>(viewWidth - 1));
    rect.top = std::clamp(minY, 0.0f, static_cast<float>(viewHeight - 1));
    rect.bottom = std::clamp(maxY, 0.0f, static_cast<float>(viewHeight - 1));
    return rect.right > rect.left && rect.bottom > rect.top;
}

void fillKeyboardInteractionSamplePoints(
    const ProjectedBillboardRect &rect,
    OutdoorGameView::KeyboardInteractionBillboardCandidate &candidate)
{
    candidate.samplePointCount = 0;
    const auto appendPoint =
        [&](float x, float y)
        {
            if (candidate.samplePointCount >= candidate.samplePoints.size())
            {
                return;
            }

            candidate.samplePoints[candidate.samplePointCount++] = {x, y};
        };

    const float centerX = (rect.left + rect.right) * 0.5f;
    const float centerY = (rect.top + rect.bottom) * 0.5f;
    appendPoint(centerX, centerY);
    appendPoint(rect.left, rect.top);
    appendPoint(rect.right, rect.top);
    appendPoint(rect.left, rect.bottom);
    appendPoint(rect.right, rect.bottom);
    appendPoint(centerX, rect.bottom);
}

uint32_t scaleAlpha(uint32_t colorAbgr, float alphaScale)
{
    const uint32_t clampedAlpha =
        static_cast<uint32_t>(std::lround(
            std::clamp(alphaScale, 0.0f, 1.0f) * static_cast<float>((colorAbgr >> 24) & 0xffu)));
    return (colorAbgr & 0x00ffffffu) | (clampedAlpha << 24);
}

float redChannel(uint32_t colorAbgr)
{
    return static_cast<float>(colorAbgr & 0xffu) / 255.0f;
}

float greenChannel(uint32_t colorAbgr)
{
    return static_cast<float>((colorAbgr >> 8) & 0xffu) / 255.0f;
}

float blueChannel(uint32_t colorAbgr)
{
    return static_cast<float>((colorAbgr >> 16) & 0xffu) / 255.0f;
}

float alphaChannel(uint32_t colorAbgr)
{
    return static_cast<float>((colorAbgr >> 24) & 0xffu) / 255.0f;
}

std::vector<uint8_t> buildContactShadowBlobPixels(int width, int height)
{
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4, 0);

    for (int y = 0; y < height; ++y)
    {
        for (int x = 0; x < width; ++x)
        {
            const float normalizedX = ((static_cast<float>(x) + 0.5f) / static_cast<float>(width)) * 2.0f - 1.0f;
            const float normalizedY = ((static_cast<float>(y) + 0.5f) / static_cast<float>(height)) * 2.0f - 1.0f;
            const float radialDistance = std::sqrt(normalizedX * normalizedX + normalizedY * normalizedY);
            const float alpha = 1.0f - std::clamp((radialDistance - 0.2f) / 0.8f, 0.0f, 1.0f);
            const size_t offset =
                (static_cast<size_t>(y) * static_cast<size_t>(width) + static_cast<size_t>(x)) * 4;
            pixels[offset + 0] = 0;
            pixels[offset + 1] = 0;
            pixels[offset + 2] = 0;
            pixels[offset + 3] = static_cast<uint8_t>(std::lround(alpha * alpha * 255.0f));
        }
    }

    return pixels;
}


} // namespace

void OutdoorBillboardRenderer::applyBillboardFogUniforms(OutdoorGameView &view, float renderDistance)
{
    if (!bgfx::isValid(view.m_outdoorFogColorUniformHandle)
        || !bgfx::isValid(view.m_outdoorFogDensitiesUniformHandle)
        || !bgfx::isValid(view.m_outdoorFogDistancesUniformHandle))
    {
        return;
    }

    const float clampedRenderDistance = std::max(renderDistance, 1.0f);
    float fogColor[4] = {0.0f, 0.0f, 0.0f, 1.0f};
    float fogDensities[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    float fogDistances[4] = {
        clampedRenderDistance,
        clampedRenderDistance,
        clampedRenderDistance,
        0.0f
    };

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        const OutdoorWorldRuntime::AtmosphereState &atmosphereState =
            view.m_pOutdoorWorldRuntime->atmosphereState();

        if ((atmosphereState.weatherFlags & 1) != 0
            && atmosphereState.fogWeakDistance >= 0
            && atmosphereState.fogStrongDistance > atmosphereState.fogWeakDistance)
        {
            const OutdoorFogProfile fogProfile = buildOutdoorFogProfile(
                atmosphereState.fogWeakDistance,
                atmosphereState.fogStrongDistance,
                clampedRenderDistance,
                OutdoorFogNearOpacity,
                OutdoorFogStrongOpacity);
            const uint32_t fogColorAbgr = computeBillboardFogColorAbgr(atmosphereState);
            fogColor[0] = static_cast<float>(fogColorAbgr & 0xffu) / 255.0f;
            fogColor[1] = static_cast<float>((fogColorAbgr >> 8) & 0xffu) / 255.0f;
            fogColor[2] = static_cast<float>((fogColorAbgr >> 16) & 0xffu) / 255.0f;
            fogDensities[0] = fogProfile.nearOpacity;
            fogDensities[1] = fogProfile.strongOpacity;
            fogDistances[0] = fogProfile.weakDistance;
            fogDistances[1] = fogProfile.strongDistance;
            fogDistances[2] = fogProfile.farDistance;
        }
    }

    bgfx::setUniform(view.m_outdoorFogColorUniformHandle, fogColor);
    bgfx::setUniform(view.m_outdoorFogDensitiesUniformHandle, fogDensities);
    bgfx::setUniform(view.m_outdoorFogDistancesUniformHandle, fogDistances);
}

void OutdoorBillboardRenderer::appendWorldQuadVertices(
    std::vector<OutdoorGameView::TerrainVertex> &vertices,
    const bx::Vec3 &center,
    const bx::Vec3 &right,
    const bx::Vec3 &up,
    uint32_t colorAbgr)
{
    vertices.push_back({center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, colorAbgr});
    vertices.push_back({center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, colorAbgr});
    vertices.push_back({center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, colorAbgr});
    vertices.push_back({center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, colorAbgr});
    vertices.push_back({center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, colorAbgr});
    vertices.push_back({center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, colorAbgr});
}

void OutdoorBillboardRenderer::submitColoredVertices(
    OutdoorGameView &view,
    uint16_t viewId,
    const std::vector<OutdoorGameView::TerrainVertex> &vertices,
    uint64_t renderState)
{
    if (vertices.empty() || !bgfx::isValid(view.m_programHandle))
    {
        return;
    }

    if (bgfx::getAvailTransientVertexBuffer(
            static_cast<uint32_t>(vertices.size()),
            OutdoorGameView::TerrainVertex::ms_layout) < vertices.size())
    {
        return;
    }

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(
        &transientVertexBuffer,
        static_cast<uint32_t>(vertices.size()),
        OutdoorGameView::TerrainVertex::ms_layout);
    std::memcpy(
        transientVertexBuffer.data,
        vertices.data(),
        static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::TerrainVertex)));

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
    bgfx::setState(renderState);
    bgfx::submit(viewId, view.m_programHandle);
}

void OutdoorBillboardRenderer::appendLitBillboardVertices(
    std::vector<OutdoorGameView::LitBillboardVertex> &vertices,
    const bx::Vec3 &center,
    const bx::Vec3 &right,
    const bx::Vec3 &up,
    float u0,
    float u1,
    uint32_t lightContributionAbgr)
{
    vertices.push_back(
        {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f,
         lightContributionAbgr});
    vertices.push_back(
        {center.x - right.x + up.x, center.y - right.y + up.y, center.z - right.z + up.z, u0, 0.0f,
         lightContributionAbgr});
    vertices.push_back(
        {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f,
         lightContributionAbgr});
    vertices.push_back(
        {center.x - right.x - up.x, center.y - right.y - up.y, center.z - right.z - up.z, u0, 1.0f,
         lightContributionAbgr});
    vertices.push_back(
        {center.x + right.x + up.x, center.y + right.y + up.y, center.z + right.z + up.z, u1, 0.0f,
         lightContributionAbgr});
    vertices.push_back(
        {center.x + right.x - up.x, center.y + right.y - up.y, center.z + right.z - up.z, u1, 1.0f,
         lightContributionAbgr});
}

void OutdoorBillboardRenderer::writeLitBillboardVertices(
    OutdoorGameView::LitBillboardVertex *pVertices,
    const bx::Vec3 &center,
    const bx::Vec3 &right,
    const bx::Vec3 &up,
    float u0,
    float u1,
    uint32_t lightContributionAbgr)
{
    pVertices[0] = {
        center.x - right.x - up.x,
        center.y - right.y - up.y,
        center.z - right.z - up.z,
        u0,
        1.0f,
        lightContributionAbgr};
    pVertices[1] = {
        center.x - right.x + up.x,
        center.y - right.y + up.y,
        center.z - right.z + up.z,
        u0,
        0.0f,
        lightContributionAbgr};
    pVertices[2] = {
        center.x + right.x + up.x,
        center.y + right.y + up.y,
        center.z + right.z + up.z,
        u1,
        0.0f,
        lightContributionAbgr};
    pVertices[3] = {
        center.x - right.x - up.x,
        center.y - right.y - up.y,
        center.z - right.z - up.z,
        u0,
        1.0f,
        lightContributionAbgr};
    pVertices[4] = {
        center.x + right.x + up.x,
        center.y + right.y + up.y,
        center.z + right.z + up.z,
        u1,
        0.0f,
        lightContributionAbgr};
    pVertices[5] = {
        center.x + right.x - up.x,
        center.y + right.y - up.y,
        center.z + right.z - up.z,
        u1,
        1.0f,
        lightContributionAbgr};
}

uint32_t OutdoorBillboardRenderer::computeBillboardLightContributionAbgr(
    const OutdoorGameView &view,
    float x,
    float y,
    float z)
{
    (void)view;
    (void)x;
    (void)y;
    (void)z;

    // Billboard lighting is intentionally ambient-only for now.
    // Terrain and textured bmodels still receive the shader-backed FX light contribution.
    return 0xff000000u;
}

std::optional<OutdoorGameView::InspectHit> OutdoorBillboardRenderer::resolveHoveredOutlineInspectHit(
    OutdoorGameView &view,
    const float *pViewMatrix)
{
    (void)pViewMatrix;

    if (view.m_cachedHoverInspectHitValid)
    {
        return view.m_cachedHoverInspectHit;
    }

    if (!view.m_gameSession.gameplayScreenState().pendingSpellTarget().active)
    {
        return std::nullopt;
    }

    return std::nullopt;
}

void OutdoorBillboardRenderer::applyBillboardAmbientUniform(OutdoorGameView &view)
{
    const float ambient[4] = {BillboardAmbientLight, BillboardAmbientLight, BillboardAmbientLight, 0.0f};
    bgfx::setUniform(view.m_outdoorBillboardAmbientUniformHandle, ambient);
}

void OutdoorBillboardRenderer::applyBillboardOverrideColorUniform(
    OutdoorGameView &view,
    uint32_t colorAbgr,
    float alpha)
{
    if (!bgfx::isValid(view.m_outdoorBillboardOverrideColorUniformHandle))
    {
        return;
    }

    const float overrideColor[4] = {
        redChannel(colorAbgr),
        greenChannel(colorAbgr),
        blueChannel(colorAbgr),
        alpha
    };
    bgfx::setUniform(view.m_outdoorBillboardOverrideColorUniformHandle, overrideColor);
}

void OutdoorBillboardRenderer::applyBillboardOutlineParamsUniform(
    OutdoorGameView &view,
    float texelWidth,
    float texelHeight,
    float thicknessPixels)
{
    if (!bgfx::isValid(view.m_outdoorBillboardOutlineParamsUniformHandle))
    {
        return;
    }

    const float outlineParams[4] = {texelWidth, texelHeight, thicknessPixels, 0.0f};
    bgfx::setUniform(view.m_outdoorBillboardOutlineParamsUniformHandle, outlineParams);
}

void OutdoorBillboardRenderer::initializeBillboardResources(OutdoorGameView &view)
{
    if (view.findBillboardTexture(ContactShadowTextureName) == nullptr)
    {
        OutdoorGameView::BillboardTextureHandle shadowTexture = {};
        shadowTexture.textureName = ContactShadowTextureName;
        shadowTexture.paletteId = 0;
        shadowTexture.width = 64;
        shadowTexture.height = 64;
        shadowTexture.physicalWidth = 64;
        shadowTexture.physicalHeight = 64;
        const std::vector<uint8_t> pixels = buildContactShadowBlobPixels(64, 64);
        shadowTexture.textureHandle = createBgraTexture2D(
            64,
            64,
            pixels.data(),
            uint32_t(pixels.size()),
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

        if (bgfx::isValid(shadowTexture.textureHandle))
        {
            view.m_billboardTextureHandles.push_back(std::move(shadowTexture));
            view.m_billboardTextureIndexByPalette[0][ContactShadowTextureName] =
                view.m_billboardTextureHandles.size() - 1;
        }
    }

    if (view.m_outdoorDecorationBillboardSet)
    {
        view.m_decorationBitmapTextureIndexByName.clear();

        for (const OutdoorBitmapTexture &texture : view.m_outdoorDecorationBillboardSet->textures)
        {
            OutdoorGameView::BillboardTextureHandle billboardTexture = {};
            billboardTexture.textureName = toLowerCopy(texture.textureName);
            billboardTexture.paletteId = texture.paletteId;
            billboardTexture.width = texture.width;
            billboardTexture.height = texture.height;
            billboardTexture.physicalWidth = texture.physicalWidth;
            billboardTexture.physicalHeight = texture.physicalHeight;
            billboardTexture.textureHandle = createBgraTexture2D(
                uint16_t(texture.physicalWidth),
                uint16_t(texture.physicalHeight),
                texture.pixels.data(),
                uint32_t(texture.pixels.size()),
                TextureFilterProfile::Billboard,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

            if (bgfx::isValid(billboardTexture.textureHandle))
            {
                view.m_billboardTextureHandles.push_back(std::move(billboardTexture));
                view.m_billboardTextureIndexByPalette[texture.paletteId][view.m_billboardTextureHandles.back().textureName] =
                    view.m_billboardTextureHandles.size() - 1;
                view.m_decorationBitmapTextureIndexByName[toLowerCopy(texture.textureName)] =
                    &texture - view.m_outdoorDecorationBillboardSet->textures.data();
            }
        }
    }

    if (view.m_pOutdoorSceneRuntime != nullptr && view.m_pOutdoorSceneRuntime->localEventProgram())
    {
        queueEventSpellBillboardTextureWarmup(view, *view.m_pOutdoorSceneRuntime->localEventProgram());
    }

    if (view.m_pOutdoorSceneRuntime != nullptr && view.m_pOutdoorSceneRuntime->globalEventProgram())
    {
        queueEventSpellBillboardTextureWarmup(view, *view.m_pOutdoorSceneRuntime->globalEventProgram());
    }

    queueRuntimeActorBillboardTextureWarmup(view);
    preloadPendingSpriteFrameWarmupsParallel(view);

    if (!view.m_outdoorSpriteObjectBillboardSet)
    {
        return;
    }

    for (const OutdoorBitmapTexture &texture : view.m_outdoorSpriteObjectBillboardSet->textures)
    {
        if (view.findBillboardTexture(texture.textureName, texture.paletteId) != nullptr)
        {
            continue;
        }

        OutdoorGameView::BillboardTextureHandle billboardTexture = {};
        billboardTexture.textureName = toLowerCopy(texture.textureName);
        billboardTexture.paletteId = texture.paletteId;
        billboardTexture.width = texture.width;
        billboardTexture.height = texture.height;
        billboardTexture.physicalWidth = texture.physicalWidth;
        billboardTexture.physicalHeight = texture.physicalHeight;
        billboardTexture.textureHandle = createBgraTexture2D(
            uint16_t(texture.physicalWidth),
            uint16_t(texture.physicalHeight),
            texture.pixels.data(),
            uint32_t(texture.pixels.size()),
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

        if (bgfx::isValid(billboardTexture.textureHandle))
        {
            view.m_billboardTextureHandles.push_back(std::move(billboardTexture));
            view.m_billboardTextureIndexByPalette[texture.paletteId][view.m_billboardTextureHandles.back().textureName] =
                view.m_billboardTextureHandles.size() - 1;
        }
    }

}

void OutdoorBillboardRenderer::prepareKeyboardInteractionBillboardCache(
    OutdoorGameView &view,
    int viewWidth,
    int viewHeight,
    const float *pViewMatrix,
    const float *pProjectionMatrix,
    const bx::Vec3 &cameraPosition)
{
    view.m_keyboardInteractionBillboardCandidates.clear();

    if (viewWidth <= 0
        || viewHeight <= 0
        || pViewMatrix == nullptr
        || pProjectionMatrix == nullptr)
    {
        return;
    }

    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, pViewMatrix, pProjectionMatrix);

    const float cosPitch = std::cos(view.m_cameraPitchRadians);
    const bx::Vec3 cameraForward = {
        std::cos(view.m_cameraYawRadians) * cosPitch,
        std::sin(view.m_cameraYawRadians) * cosPitch,
        std::sin(view.m_cameraPitchRadians)
    };
    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const uint32_t animationTimeTicks = currentAnimationTicks();

    view.m_keyboardInteractionBillboardCandidates.reserve(
        (view.m_outdoorDecorationBillboardSet ? view.m_outdoorDecorationBillboardSet->billboards.size() : 0)
        + (view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapActorCount() : 0)
        + (view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->worldItemCount() : 0)
        + (view.m_outdoorSpriteObjectBillboardSet ? view.m_outdoorSpriteObjectBillboardSet->billboards.size() : 0));

    const auto appendCandidate =
        [&view](OutdoorGameView::KeyboardInteractionBillboardCandidate &&candidate)
        {
            if (candidate.samplePointCount == 0)
            {
                return;
            }

            view.m_keyboardInteractionBillboardCandidates.push_back(std::move(candidate));
        };

    if (view.m_outdoorDecorationBillboardSet)
    {
        for (size_t decorationIndex = 0; decorationIndex < view.m_outdoorDecorationBillboardSet->billboards.size(); ++decorationIndex)
        {
            const DecorationBillboard &billboard = view.m_outdoorDecorationBillboardSet->billboards[decorationIndex];

            if (OutdoorInteractionController::isInteractiveDecorationHidden(view, billboard.entityIndex))
            {
                continue;
            }

            bool hidden = false;
            const uint16_t spriteId =
                OutdoorInteractionController::resolveDecorationBillboardSpriteId(view, billboard, hidden);

            if (hidden || spriteId == 0)
            {
                continue;
            }

            std::optional<uint16_t> directEventId;

            if (view.m_outdoorMapData && billboard.entityIndex < view.m_outdoorMapData->entities.size())
            {
                const OutdoorEntity &entity = view.m_outdoorMapData->entities[billboard.entityIndex];
                directEventId = entity.eventIdPrimary != 0 ? entity.eventIdPrimary : entity.eventIdSecondary;
            }

            if (!directEventId.has_value()
                && !OutdoorInteractionController::resolveInteractiveDecorationEventId(view, billboard.entityIndex).has_value())
            {
                continue;
            }

            const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
            const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
            const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            const float cameraDepth = deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;

            if (distanceSquared > DecorationBillboardRenderDistanceSquared || cameraDepth <= BillboardNearDepth)
            {
                continue;
            }

            const uint32_t animationOffsetTicks =
                animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
            const SpriteFrameEntry *pFrame =
                view.m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(spriteId, animationOffsetTicks);

            if (pFrame == nullptr)
            {
                continue;
            }

            const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
            const float angleToCamera = std::atan2(
                static_cast<float>(billboard.y) - cameraPosition.y,
                static_cast<float>(billboard.x) - cameraPosition.x);
            const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const OutdoorGameView::BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                continue;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const float halfWidth = worldWidth * 0.5f;
            const bx::Vec3 center = {
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z) + worldHeight * 0.5f
            };
            const bx::Vec3 right = {
                cameraRight.x * halfWidth,
                cameraRight.y * halfWidth,
                cameraRight.z * halfWidth
            };
            const bx::Vec3 up = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            ProjectedBillboardRect rect = {};

            if (!projectVisibleBillboardRect(
                    center,
                    right,
                    up,
                    viewWidth,
                    viewHeight,
                    viewProjectionMatrix,
                    rect))
            {
                continue;
            }

            OutdoorGameView::KeyboardInteractionBillboardCandidate candidate = {};
            candidate.inspectHit.hasHit = true;
            candidate.inspectHit.kind = "decoration";
            candidate.inspectHit.bModelIndex = decorationIndex;
            candidate.inspectHit.name = billboard.name;
            candidate.inspectHit.decorationId = billboard.decorationId;
            candidate.inspectHit.distance = cameraDepth;

            if (view.m_outdoorMapData && billboard.entityIndex < view.m_outdoorMapData->entities.size())
            {
                const OutdoorEntity &entity = view.m_outdoorMapData->entities[billboard.entityIndex];
                candidate.inspectHit.eventIdPrimary = entity.eventIdPrimary;
                candidate.inspectHit.eventIdSecondary = entity.eventIdSecondary;
            }

            candidate.cameraDepth = cameraDepth;
            fillKeyboardInteractionSamplePoints(rect, candidate);
            appendCandidate(std::move(candidate));
        }
    }

    if (view.m_pOutdoorWorldRuntime != nullptr && view.m_outdoorActorPreviewBillboardSet)
    {
        struct ActorPreviewLookup
        {
            size_t billboardIndex = static_cast<size_t>(-1);
            const ActorPreviewBillboard *pBillboard = nullptr;
        };

        std::unordered_map<size_t, ActorPreviewLookup> previewByRuntimeActorIndex;
        previewByRuntimeActorIndex.reserve(view.m_outdoorActorPreviewBillboardSet->billboards.size());

        for (size_t billboardIndex = 0; billboardIndex < view.m_outdoorActorPreviewBillboardSet->billboards.size(); ++billboardIndex)
        {
            const ActorPreviewBillboard &billboard = view.m_outdoorActorPreviewBillboardSet->billboards[billboardIndex];

            if (billboard.runtimeActorIndex == static_cast<size_t>(-1))
            {
                continue;
            }

            previewByRuntimeActorIndex.try_emplace(
                billboard.runtimeActorIndex,
                ActorPreviewLookup {billboardIndex, &billboard});
        }

        for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            const OutdoorWorldRuntime::MapActorState *pActorState = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pActorState == nullptr || pActorState->isInvisible)
            {
                continue;
            }

            uint16_t spriteFrameIndex = pActorState->spriteFrameIndex;
            const size_t animationIndex = static_cast<size_t>(pActorState->animation);

            if (animationIndex < pActorState->actionSpriteFrameIndices.size()
                && pActorState->actionSpriteFrameIndices[animationIndex] != 0)
            {
                spriteFrameIndex = pActorState->actionSpriteFrameIndices[animationIndex];
            }

            const uint32_t frameTimeTicks = pActorState->useStaticSpriteFrame
                ? 0u
                : static_cast<uint32_t>(std::max(0.0f, pActorState->animationTimeTicks));
            const SpriteFrameEntry *pFrame =
                view.m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, frameTimeTicks);

            if (pFrame == nullptr)
            {
                continue;
            }

            const float deltaX = static_cast<float>(pActorState->x) - cameraPosition.x;
            const float deltaY = static_cast<float>(pActorState->y) - cameraPosition.y;
            const float deltaZ = static_cast<float>(pActorState->z) - cameraPosition.z;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            const float cameraDepth = deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;

            if (distanceSquared > ActorBillboardRenderDistanceSquared || cameraDepth <= BillboardNearDepth)
            {
                continue;
            }

            const float angleToCamera = std::atan2(
                static_cast<float>(pActorState->y) - cameraPosition.y,
                static_cast<float>(pActorState->x) - cameraPosition.x);
            const float octantAngle = pActorState->yawRadians - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const OutdoorGameView::BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                continue;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const float halfWidth = worldWidth * 0.5f;
            const bx::Vec3 center = {
                static_cast<float>(pActorState->x),
                static_cast<float>(pActorState->y),
                static_cast<float>(pActorState->z) + worldHeight * 0.5f
            };
            const bx::Vec3 right = {
                cameraRight.x * halfWidth,
                cameraRight.y * halfWidth,
                cameraRight.z * halfWidth
            };
            const bx::Vec3 up = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            ProjectedBillboardRect rect = {};

            if (!projectVisibleBillboardRect(
                    center,
                    right,
                    up,
                    viewWidth,
                    viewHeight,
                    viewProjectionMatrix,
                    rect))
            {
                continue;
            }

            OutdoorGameView::KeyboardInteractionBillboardCandidate candidate = {};
            candidate.inspectHit.hasHit = true;
            candidate.inspectHit.kind = "actor";
            candidate.inspectHit.isFriendly = !pActorState->hostileToParty;
            candidate.inspectHit.runtimeActorIndex = actorIndex;
            const auto previewIterator = previewByRuntimeActorIndex.find(actorIndex);
            if (previewIterator != previewByRuntimeActorIndex.end())
            {
                candidate.inspectHit.bModelIndex = previewIterator->second.billboardIndex;
                candidate.inspectHit.name = !previewIterator->second.pBillboard->actorName.empty()
                    ? previewIterator->second.pBillboard->actorName
                    : pActorState->displayName;
                candidate.inspectHit.npcId = previewIterator->second.pBillboard->npcId;
                candidate.inspectHit.actorGroup = previewIterator->second.pBillboard->group;
            }
            else
            {
                candidate.inspectHit.bModelIndex = actorIndex;
                candidate.inspectHit.name = pActorState->displayName;
                candidate.inspectHit.npcId = 0;
                candidate.inspectHit.actorGroup = pActorState->group;
            }
            candidate.inspectHit.distance = cameraDepth;
            candidate.cameraDepth = cameraDepth;
            fillKeyboardInteractionSamplePoints(rect, candidate);
            appendCandidate(std::move(candidate));
        }
    }

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        const SpriteFrameTable *pSpriteFrameTable = nullptr;

        if (view.m_outdoorSpriteObjectBillboardSet)
        {
            pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
        }
        else if (view.m_outdoorActorPreviewBillboardSet)
        {
            pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
        }

        if (pSpriteFrameTable != nullptr)
        {
            for (size_t worldItemIndex = 0; worldItemIndex < view.m_pOutdoorWorldRuntime->worldItemCount(); ++worldItemIndex)
            {
                const OutdoorWorldRuntime::WorldItemState *pWorldItem =
                    view.m_pOutdoorWorldRuntime->worldItemState(worldItemIndex);

                if (pWorldItem == nullptr)
                {
                    continue;
                }

                uint16_t spriteFrameIndex = pWorldItem->objectSpriteFrameIndex;

                if (spriteFrameIndex == 0 && !pWorldItem->objectSpriteName.empty())
                {
                    const std::optional<uint16_t> spriteFrameIndexByName =
                        pSpriteFrameTable->findFrameIndexBySpriteName(pWorldItem->objectSpriteName);

                    if (spriteFrameIndexByName)
                    {
                        spriteFrameIndex = *spriteFrameIndexByName;
                    }
                }

                if (spriteFrameIndex == 0)
                {
                    spriteFrameIndex = pWorldItem->objectSpriteId;
                }

                if (spriteFrameIndex == 0)
                {
                    continue;
                }

                const SpriteFrameEntry *pFrame =
                    pSpriteFrameTable->getFrame(spriteFrameIndex, pWorldItem->timeSinceCreatedTicks);

                if (pFrame == nullptr)
                {
                    continue;
                }

                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
                const OutdoorGameView::BillboardTextureHandle *pTexture =
                    ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

                if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
                {
                    continue;
                }

                const float deltaX = pWorldItem->x - cameraPosition.x;
                const float deltaY = pWorldItem->y - cameraPosition.y;
                const float deltaZ = pWorldItem->z - cameraPosition.z;
                const float cameraDepth =
                    deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;

                if (cameraDepth <= BillboardNearDepth)
                {
                    continue;
                }

                const float spriteScale = std::max(pFrame->scale, 0.01f);
                const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                const float halfWidth = worldWidth * 0.5f;
                const bx::Vec3 center = {
                    pWorldItem->x,
                    pWorldItem->y,
                    pWorldItem->z + worldHeight * 0.5f
                };
                const bx::Vec3 right = {
                    cameraRight.x * halfWidth,
                    cameraRight.y * halfWidth,
                    cameraRight.z * halfWidth
                };
                const bx::Vec3 up = {
                    cameraUp.x * worldHeight * 0.5f,
                    cameraUp.y * worldHeight * 0.5f,
                    cameraUp.z * worldHeight * 0.5f
                };
                ProjectedBillboardRect rect = {};

                if (!projectVisibleBillboardRect(
                        center,
                        right,
                        up,
                        viewWidth,
                        viewHeight,
                        viewProjectionMatrix,
                        rect))
                {
                    continue;
                }

                OutdoorGameView::KeyboardInteractionBillboardCandidate candidate = {};
                candidate.inspectHit.hasHit = true;
                candidate.inspectHit.kind = "world_item";
                candidate.inspectHit.bModelIndex = worldItemIndex;
                candidate.inspectHit.name = pWorldItem->objectName;
                candidate.inspectHit.objectDescriptionId = pWorldItem->objectDescriptionId;
                candidate.inspectHit.objectSpriteId = pWorldItem->objectSpriteId;
                candidate.inspectHit.attributes = pWorldItem->attributes;
                candidate.inspectHit.distance = cameraDepth;
                candidate.cameraDepth = cameraDepth;
                fillKeyboardInteractionSamplePoints(rect, candidate);
                appendCandidate(std::move(candidate));
            }
        }
    }

    std::sort(
        view.m_keyboardInteractionBillboardCandidates.begin(),
        view.m_keyboardInteractionBillboardCandidates.end(),
        [](const OutdoorGameView::KeyboardInteractionBillboardCandidate &left,
           const OutdoorGameView::KeyboardInteractionBillboardCandidate &right)
        {
            return left.cameraDepth < right.cameraDepth;
        });
}

void OutdoorBillboardRenderer::queueEventSpellBillboardTextureWarmup(
    OutdoorGameView &view,
    const ScriptedEventProgram &eventProgram)
{
    const SpellTable &spellTable = view.data().spellTable();
    const ObjectTable &objectTable = view.data().objectTable();

    auto queueSpellObjectSpriteFrame =
        [&view, &objectTable](int objectId)
        {
            if (objectId <= 0)
            {
                return;
            }

            const std::optional<uint16_t> descriptionId =
                objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(objectId));

            if (!descriptionId)
            {
                return;
            }

            const ObjectEntry *pObjectEntry = objectTable.get(*descriptionId);

            if (pObjectEntry == nullptr)
            {
                return;
            }

            if (pObjectEntry->spriteId != 0)
            {
                view.queueSpriteFrameWarmup(pObjectEntry->spriteId);
                return;
            }

            if (pObjectEntry->spriteName.empty())
            {
                return;
            }

            const SpriteFrameTable *pSpriteFrameTable = nullptr;

            if (view.m_outdoorSpriteObjectBillboardSet)
            {
                pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
            }
            else if (view.m_outdoorActorPreviewBillboardSet)
            {
                pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
            }

            if (pSpriteFrameTable == nullptr)
            {
                return;
            }

            const std::optional<uint16_t> spriteFrameIndex =
                pSpriteFrameTable->findFrameIndexBySpriteName(pObjectEntry->spriteName);

            if (spriteFrameIndex)
            {
                view.queueSpriteFrameWarmup(*spriteFrameIndex);
            }
        };

    for (uint32_t spellId : eventProgram.castSpellIds())
    {
        const SpellEntry *pSpellEntry = spellTable.findById(static_cast<int>(spellId));

        if (pSpellEntry == nullptr)
        {
            continue;
        }

        queueSpellObjectSpriteFrame(pSpellEntry->displayObjectId);
        queueSpellObjectSpriteFrame(pSpellEntry->impactDisplayObjectId);
    }
}

void OutdoorBillboardRenderer::queueRuntimeActorBillboardTextureWarmup(OutdoorGameView &view)
{
    if (view.m_pOutdoorWorldRuntime == nullptr || !view.m_outdoorActorPreviewBillboardSet)
    {
        return;
    }

    const size_t actorCount = view.m_pOutdoorWorldRuntime->mapActorCount();

    if (view.m_runtimeActorBillboardTexturesQueuedCount == 0 && actorCount > 0)
    {
        std::vector<size_t> actorIndices(actorCount);

        for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
        {
            actorIndices[actorIndex] = actorIndex;
        }

        std::sort(
            actorIndices.begin(),
            actorIndices.end(),
            [&view](size_t left, size_t right)
            {
                const OutdoorWorldRuntime::MapActorState *pLeft = view.m_pOutdoorWorldRuntime->mapActorState(left);
                const OutdoorWorldRuntime::MapActorState *pRight = view.m_pOutdoorWorldRuntime->mapActorState(right);

                if (pLeft == nullptr || pRight == nullptr)
                {
                    return left < right;
                }

                const float leftDeltaX = static_cast<float>(pLeft->x) - view.m_cameraTargetX;
                const float leftDeltaY = static_cast<float>(pLeft->y) - view.m_cameraTargetY;
                const float leftDistanceSquared = leftDeltaX * leftDeltaX + leftDeltaY * leftDeltaY;
                const float rightDeltaX = static_cast<float>(pRight->x) - view.m_cameraTargetX;
                const float rightDeltaY = static_cast<float>(pRight->y) - view.m_cameraTargetY;
                const float rightDistanceSquared = rightDeltaX * rightDeltaX + rightDeltaY * rightDeltaY;
                return leftDistanceSquared < rightDistanceSquared;
            });

        for (size_t actorIndex : actorIndices)
        {
            const OutdoorWorldRuntime::MapActorState *pActorState = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pActorState == nullptr)
            {
                continue;
            }

            view.queueSpriteFrameWarmup(pActorState->spriteFrameIndex);

            for (uint16_t actionSpriteFrameIndex : pActorState->actionSpriteFrameIndices)
            {
                view.queueSpriteFrameWarmup(actionSpriteFrameIndex);
            }
        }

        view.m_runtimeActorBillboardTexturesQueuedCount = actorCount;
        return;
    }

    for (size_t actorIndex = view.m_runtimeActorBillboardTexturesQueuedCount; actorIndex < actorCount; ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActorState = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

        if (pActorState == nullptr)
        {
            continue;
        }

        view.queueSpriteFrameWarmup(pActorState->spriteFrameIndex);

        for (uint16_t actionSpriteFrameIndex : pActorState->actionSpriteFrameIndices)
        {
            view.queueSpriteFrameWarmup(actionSpriteFrameIndex);
        }
    }

    view.m_runtimeActorBillboardTexturesQueuedCount = actorCount;
}

void OutdoorBillboardRenderer::preloadPendingSpriteFrameWarmupsParallel(OutdoorGameView &view)
{
    if (view.m_pendingSpriteFrameWarmups.empty() || view.m_pAssetFileSystem == nullptr)
    {
        return;
    }

    const Engine::AssetScaleTier assetScaleTier = view.m_pAssetFileSystem->getAssetScaleTier();
    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }
    else if (view.m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    std::vector<SpriteTexturePreloadRequest> preloadRequests;
    std::unordered_map<int16_t, std::unordered_map<std::string, size_t>> requestIndexByPaletteAndName;
    std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> paletteCache;
    const uint64_t preloadStartTickCount = SDL_GetTicksNS();

    auto queueTextureRequest =
        [&view, &preloadRequests, &requestIndexByPaletteAndName, &paletteCache](
            const std::string &textureName,
            int16_t paletteId)
        {
            if (textureName.empty() || view.findBillboardTexture(textureName, paletteId) != nullptr)
            {
                return;
            }

            const std::string normalizedTextureName = toLowerCopy(textureName);

            if (requestIndexByPaletteAndName[paletteId].contains(normalizedTextureName))
            {
                return;
            }

            const std::optional<std::string> spritePath =
                view.findCachedAssetPath("Data/sprites", normalizedTextureName + ".bmp");

            if (!spritePath)
            {
                if (DebugSpritePreloadLogging)
                {
                    std::cout << "Preload sprite skipped texture=\"" << normalizedTextureName
                              << "\" palette=" << paletteId
                              << " reason=missing_bitmap\n";
                }
                return;
            }

            const std::optional<std::vector<uint8_t>> bitmapBytes = view.readCachedBinaryFile(*spritePath);

            if (!bitmapBytes || bitmapBytes->empty())
            {
                if (DebugSpritePreloadLogging)
                {
                    std::cout << "Preload sprite skipped texture=\"" << normalizedTextureName
                              << "\" palette=" << paletteId
                              << " reason=empty_bitmap\n";
                }
                return;
            }

            SpriteTexturePreloadRequest request = {};
            request.textureName = normalizedTextureName;
            request.paletteId = paletteId;
            request.bitmapBytes = *bitmapBytes;

            if (!paletteCache.contains(paletteId))
            {
                paletteCache[paletteId] = view.loadCachedActPalette(paletteId);
            }

            request.overridePalette = paletteCache[paletteId];
            requestIndexByPaletteAndName[paletteId][normalizedTextureName] = preloadRequests.size();
            preloadRequests.push_back(std::move(request));
        };

    for (uint16_t spriteFrameIndex : view.m_pendingSpriteFrameWarmups)
    {
        if (spriteFrameIndex == 0)
        {
            continue;
        }

        size_t frameIndex = spriteFrameIndex;

        while (frameIndex <= std::numeric_limits<uint16_t>::max())
        {
            const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(static_cast<uint16_t>(frameIndex), 0);

            if (pFrame == nullptr)
            {
                break;
            }

            for (int octant = 0; octant < 8; ++octant)
            {
                const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
                queueTextureRequest(resolvedTexture.textureName, pFrame->paletteId);
            }

            if (!SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::HasMore))
            {
                break;
            }

            ++frameIndex;
        }
    }

    if (preloadRequests.empty())
    {
        view.m_pendingSpriteFrameWarmups.clear();
        view.m_nextPendingSpriteFrameWarmupIndex = 0;
        return;
    }

    if (DebugSpritePreloadLogging)
    {
        std::cout << "Preloading sprite textures: requests=" << preloadRequests.size()
                  << " workers=" << std::min(PreloadDecodeWorkerCount, preloadRequests.size())
                  << '\n';
    }

    const size_t workerCount = std::min(PreloadDecodeWorkerCount, preloadRequests.size());
    std::vector<std::future<std::vector<DecodedSpriteTexture>>> futures;
    futures.reserve(workerCount);

    for (size_t workerIndex = 0; workerIndex < workerCount; ++workerIndex)
    {
        futures.push_back(std::async(
            std::launch::async,
            [workerIndex, workerCount, &preloadRequests]()
            {
                std::vector<DecodedSpriteTexture> decodedTextures;

                for (size_t requestIndex = workerIndex; requestIndex < preloadRequests.size(); requestIndex += workerCount)
                {
                    const SpriteTexturePreloadRequest &request = preloadRequests[requestIndex];
                    int textureWidth = 0;
                    int textureHeight = 0;
                    const std::optional<std::vector<uint8_t>> pixels = loadSpriteBitmapPixelsBgra(
                        request.bitmapBytes,
                        request.overridePalette,
                        textureWidth,
                        textureHeight);

                    if (!pixels || textureWidth <= 0 || textureHeight <= 0)
                    {
                        continue;
                    }

                    DecodedSpriteTexture decodedTexture = {};
                    decodedTexture.textureName = request.textureName;
                    decodedTexture.paletteId = request.paletteId;
                    decodedTexture.width = textureWidth;
                    decodedTexture.height = textureHeight;
                    decodedTexture.pixels = *pixels;
                    decodedTextures.push_back(std::move(decodedTexture));
                }

                return decodedTextures;
            }));
    }

    std::vector<DecodedSpriteTexture> decodedTextures;

    for (std::future<std::vector<DecodedSpriteTexture>> &future : futures)
    {
        std::vector<DecodedSpriteTexture> workerTextures = future.get();
        decodedTextures.insert(
            decodedTextures.end(),
            std::make_move_iterator(workerTextures.begin()),
            std::make_move_iterator(workerTextures.end()));
    }

    size_t uploadedCount = 0;

    for (DecodedSpriteTexture &decodedTexture : decodedTextures)
    {
        if (view.findBillboardTexture(decodedTexture.textureName, decodedTexture.paletteId) != nullptr)
        {
            continue;
        }

        OutdoorGameView::BillboardTextureHandle billboardTexture = {};
        billboardTexture.textureName = decodedTexture.textureName;
        billboardTexture.paletteId = decodedTexture.paletteId;
        billboardTexture.width = Engine::scalePhysicalPixelsToLogical(decodedTexture.width, assetScaleTier);
        billboardTexture.height = Engine::scalePhysicalPixelsToLogical(decodedTexture.height, assetScaleTier);
        billboardTexture.physicalWidth = decodedTexture.width;
        billboardTexture.physicalHeight = decodedTexture.height;
        billboardTexture.textureHandle = createBgraTexture2D(
            uint16_t(decodedTexture.width),
            uint16_t(decodedTexture.height),
            decodedTexture.pixels.data(),
            uint32_t(decodedTexture.pixels.size()),
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

        if (!bgfx::isValid(billboardTexture.textureHandle))
        {
            if (DebugSpritePreloadLogging)
            {
                std::cout << "Preload sprite failed texture=\"" << decodedTexture.textureName
                          << "\" palette=" << decodedTexture.paletteId
                          << " reason=create_texture\n";
            }
            continue;
        }

        if (DebugSpritePreloadLogging)
        {
            std::cout << "Preloaded sprite texture=\"" << decodedTexture.textureName
                      << "\" palette=" << decodedTexture.paletteId
                      << " size=" << decodedTexture.width << "x" << decodedTexture.height
                      << '\n';
        }

        view.m_billboardTextureHandles.push_back(std::move(billboardTexture));
        view.m_billboardTextureIndexByPalette[decodedTexture.paletteId][view.m_billboardTextureHandles.back().textureName] =
            view.m_billboardTextureHandles.size() - 1;
        ++uploadedCount;
    }

    const uint64_t preloadElapsedNanoseconds = SDL_GetTicksNS() - preloadStartTickCount;

    if (DebugSpritePreloadLogging)
    {
        std::cout << "Sprite preload complete uploaded=" << uploadedCount
                  << " elapsed_ms=" << static_cast<double>(preloadElapsedNanoseconds) / 1000000.0
                  << '\n';
    }

    view.m_pendingSpriteFrameWarmups.clear();
    view.m_nextPendingSpriteFrameWarmupIndex = 0;
}

void OutdoorBillboardRenderer::processPendingSpriteFrameWarmups(OutdoorGameView &view, size_t maxSpriteFrames)
{
    if (maxSpriteFrames == 0)
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }
    else if (view.m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    size_t processedCount = 0;

    while (processedCount < maxSpriteFrames
        && view.m_nextPendingSpriteFrameWarmupIndex < view.m_pendingSpriteFrameWarmups.size())
    {
        view.preloadSpriteFrameTextures(
            *pSpriteFrameTable,
            view.m_pendingSpriteFrameWarmups[view.m_nextPendingSpriteFrameWarmupIndex]);
        ++view.m_nextPendingSpriteFrameWarmupIndex;
        ++processedCount;
    }

    if (view.m_nextPendingSpriteFrameWarmupIndex >= view.m_pendingSpriteFrameWarmups.size())
    {
        view.m_pendingSpriteFrameWarmups.clear();
        view.m_nextPendingSpriteFrameWarmupIndex = 0;
    }
}

const OutdoorGameView::BillboardTextureHandle *OutdoorBillboardRenderer::ensureSpriteBillboardTexture(
    OutdoorGameView &view,
    const std::string &textureName,
    int16_t paletteId)
{
    const OutdoorGameView::BillboardTextureHandle *pExistingTexture = view.findBillboardTexture(textureName, paletteId);

    if (pExistingTexture != nullptr)
    {
        return pExistingTexture;
    }

    if (view.m_pAssetFileSystem == nullptr)
    {
        return nullptr;
    }

    int textureWidth = 0;
    int textureHeight = 0;
    const std::optional<std::vector<uint8_t>> pixels =
        view.loadSpriteBitmapPixelsBgraCached(textureName, paletteId, textureWidth, textureHeight);

    if (!pixels || textureWidth <= 0 || textureHeight <= 0)
    {
        return nullptr;
    }

    OutdoorGameView::BillboardTextureHandle billboardTexture = {};
    billboardTexture.textureName = toLowerCopy(textureName);
    billboardTexture.paletteId = paletteId;
    billboardTexture.width = Engine::scalePhysicalPixelsToLogical(textureWidth, view.m_pAssetFileSystem->getAssetScaleTier());
    billboardTexture.height =
        Engine::scalePhysicalPixelsToLogical(textureHeight, view.m_pAssetFileSystem->getAssetScaleTier());
    billboardTexture.physicalWidth = textureWidth;
    billboardTexture.physicalHeight = textureHeight;
    billboardTexture.textureHandle = createBgraTexture2D(
        uint16_t(textureWidth),
        uint16_t(textureHeight),
        pixels->data(),
        uint32_t(pixels->size()),
        TextureFilterProfile::Billboard,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    if (!bgfx::isValid(billboardTexture.textureHandle))
    {
        return nullptr;
    }

    view.m_billboardTextureHandles.push_back(std::move(billboardTexture));
    view.m_billboardTextureIndexByPalette[paletteId][view.m_billboardTextureHandles.back().textureName] =
        view.m_billboardTextureHandles.size() - 1;
    return &view.m_billboardTextureHandles.back();
}

void OutdoorBillboardRenderer::invalidateRenderAssets(OutdoorGameView &view)
{
    for (OutdoorGameView::BillboardTextureHandle &textureHandle : view.m_billboardTextureHandles)
    {
        textureHandle.textureHandle = BGFX_INVALID_HANDLE;
    }

    view.m_billboardTextureHandles.clear();
    view.m_billboardTextureIndexByPalette.clear();
    view.m_spriteLoadCache.directoryAssetPathsByPath.clear();
    view.m_spriteLoadCache.assetPathByKey.clear();
    view.m_spriteLoadCache.binaryFilesByPath.clear();
    view.m_spriteLoadCache.actPalettesById.clear();
    view.m_pendingSpriteFrameWarmups.clear();
    view.m_queuedSpriteFrameWarmups.clear();
    view.m_nextPendingSpriteFrameWarmupIndex = 0;
    view.m_runtimeActorBillboardTexturesQueuedCount = 0;
}

void OutdoorBillboardRenderer::destroyRenderAssets(OutdoorGameView &view)
{
    for (OutdoorGameView::BillboardTextureHandle &textureHandle : view.m_billboardTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    invalidateRenderAssets(view);
}

void OutdoorBillboardRenderer::renderDecorationBillboards(
    OutdoorGameView &view,
    uint16_t viewId,
    uint16_t viewWidth,
    uint16_t viewHeight,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    (void)viewWidth;
    (void)viewHeight;

    if (!view.m_outdoorDecorationBillboardSet
        || !bgfx::isValid(view.m_outdoorLitBillboardProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOverrideColorUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOutlineParamsUniformHandle))
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const float cosPitch = std::cos(view.m_cameraPitchRadians);
    const bx::Vec3 cameraForward = {
        std::cos(view.m_cameraYawRadians) * cosPitch,
        std::sin(view.m_cameraYawRadians) * cosPitch,
        std::sin(view.m_cameraPitchRadians)
    };
    applyBillboardFogUniforms(view, DecorationBillboardRenderDistance);
    const uint32_t animationTimeTicks = currentAnimationTicks();

    struct BillboardDrawItem
    {
        const DecorationBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
        uint32_t lightContributionAbgr = 0xff000000u;
    };
    const auto resolveBillboardVisual = [&view](const DecorationBillboard &billboard, bool &hidden)
    {
        hidden = false;
        uint16_t spriteId = billboard.spriteId;

        if (!view.m_outdoorDecorationBillboardSet || view.m_pOutdoorWorldRuntime == nullptr)
        {
            return spriteId;
        }

        const EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState();

        if (pEventRuntimeState == nullptr)
        {
            return spriteId;
        }

        const uint32_t overrideKey =
            billboard.eventIdPrimary != 0 ? billboard.eventIdPrimary : billboard.eventIdSecondary;

        if (overrideKey == 0)
        {
            return spriteId;
        }

        const auto overrideIterator = pEventRuntimeState->spriteOverrides.find(overrideKey);

        if (overrideIterator == pEventRuntimeState->spriteOverrides.end())
        {
            return spriteId;
        }

        hidden = overrideIterator->second.hidden;

        if (!overrideIterator->second.textureName.has_value() || overrideIterator->second.textureName->empty())
        {
            return spriteId;
        }

        if (const DecorationEntry *pDecoration =
                view.m_outdoorDecorationBillboardSet->decorationTable.findByInternalName(
                    *overrideIterator->second.textureName))
        {
            return pDecoration->spriteId;
        }

        if (const std::optional<uint16_t> overrideSpriteId =
                view.m_outdoorDecorationBillboardSet->spriteFrameTable.findFrameIndexBySpriteName(
                    *overrideIterator->second.textureName))
        {
            return *overrideSpriteId;
        }

        return spriteId;
    };

    std::vector<size_t> candidateBillboardIndices;
    OutdoorInteractionController::collectDecorationBillboardCandidates(view, 
        cameraPosition.x - DecorationBillboardRenderDistance,
        cameraPosition.y - DecorationBillboardRenderDistance,
        cameraPosition.x + DecorationBillboardRenderDistance,
        cameraPosition.y + DecorationBillboardRenderDistance,
        candidateBillboardIndices);

    if (candidateBillboardIndices.empty())
    {
        return;
    }

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(candidateBillboardIndices.size());

    for (size_t billboardIndex : candidateBillboardIndices)
    {
        const DecorationBillboard &billboard = view.m_outdoorDecorationBillboardSet->billboards[billboardIndex];
        bool hidden = false;
        const uint16_t spriteId = resolveBillboardVisual(billboard, hidden);

        if (OutdoorInteractionController::isInteractiveDecorationHidden(view, billboard.entityIndex)
            || hidden
            || spriteId == 0)
        {
            continue;
        }

        const float baseX = static_cast<float>(billboard.x);
        const float baseY = static_cast<float>(billboard.y);
        const float baseZ = static_cast<float>(billboard.z);
        const float deltaX = baseX - cameraPosition.x;
        const float deltaY = baseY - cameraPosition.y;
        const float deltaZ = baseZ - cameraPosition.z;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

        if (distanceSquared > DecorationBillboardRenderDistanceSquared)
        {
            continue;
        }

        if (deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z <= BillboardNearDepth)
        {
            continue;
        }

        const uint32_t animationOffsetTicks =
            animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
        const SpriteFrameEntry *pFrame =
            view.m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(spriteId, animationOffsetTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
        const float angleToCamera = std::atan2(
            static_cast<float>(billboard.y) - cameraPosition.y,
            static_cast<float>(billboard.x) - cameraPosition.x);
        const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
        const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
        const OutdoorGameView::BillboardTextureHandle *pTexture =
            ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle) || pTexture->width <= 0 || pTexture->height <= 0)
        {
            continue;
        }

        BillboardDrawItem drawItem = {};
        drawItem.pBillboard = &billboard;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.distanceSquared = distanceSquared;
        drawItems.push_back(drawItem);
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            const uint16_t leftTextureId = left.pTexture != nullptr ? left.pTexture->textureHandle.idx : 0;
            const uint16_t rightTextureId = right.pTexture != nullptr ? right.pTexture->textureHandle.idx : 0;

            if (leftTextureId != rightTextureId)
            {
                return leftTextureId < rightTextureId;
            }

            return left.distanceSquared > right.distanceSquared;
        });

    size_t groupBegin = 0;

    while (groupBegin < drawItems.size())
    {
        const OutdoorGameView::BillboardTextureHandle *pTexture = drawItems[groupBegin].pTexture;

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            ++groupBegin;
            continue;
        }

        size_t groupEnd = groupBegin + 1;

        while (groupEnd < drawItems.size() && drawItems[groupEnd].pTexture == pTexture)
        {
            ++groupEnd;
        }

        const uint32_t vertexCount = static_cast<uint32_t>((groupEnd - groupBegin) * 6);

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, OutdoorGameView::LitBillboardVertex::ms_layout) < vertexCount)
        {
            groupBegin = groupEnd;
            continue;
        }

        std::vector<OutdoorGameView::LitBillboardVertex> vertices;
        vertices.reserve(static_cast<size_t>(vertexCount));

        for (size_t index = groupBegin; index < groupEnd; ++index)
        {
            const BillboardDrawItem &drawItem = drawItems[index];
            const DecorationBillboard &billboard = *drawItem.pBillboard;
            const SpriteFrameEntry &frame = *drawItem.pFrame;
            const float spriteScale = std::max(frame.scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const float halfWidth = worldWidth * 0.5f;
            const bx::Vec3 center = {
                static_cast<float>(billboard.x),
                static_cast<float>(billboard.y),
                static_cast<float>(billboard.z) + worldHeight * 0.5f
            };
            const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
            const bx::Vec3 up = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
            const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
            const uint32_t lightContributionAbgr =
                computeBillboardLightContributionAbgr(
                    view,
                    static_cast<float>(billboard.x),
                    static_cast<float>(billboard.y),
                    static_cast<float>(billboard.z) + worldHeight * 0.5f);
            appendLitBillboardVertices(
                vertices,
                center,
                right,
                up,
                u0,
                u1,
                lightContributionAbgr);
        }

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            vertexCount,
            OutdoorGameView::LitBillboardVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::LitBillboardVertex)));

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, vertexCount);
        bindTexture(
            0,
            view.m_terrainTextureSamplerHandle,
            pTexture->textureHandle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        applyBillboardAmbientUniform(view);
        applyBillboardOverrideColorUniform(view, 0, 0.0f);
        applyBillboardOutlineParamsUniform(view, 0.0f, 0.0f, 0.0f);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_outdoorLitBillboardProgramHandle);

        groupBegin = groupEnd;
    }
}

void OutdoorBillboardRenderer::renderActorPreviewBillboards(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    if (!view.m_outdoorActorPreviewBillboardSet && !view.m_outdoorDecorationBillboardSet)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    const float cosPitch = std::cos(view.m_cameraPitchRadians);
    const bx::Vec3 cameraForward = {
        std::cos(view.m_cameraYawRadians) * cosPitch,
        std::sin(view.m_cameraYawRadians) * cosPitch,
        std::sin(view.m_cameraPitchRadians)
    };
    const uint32_t animationTimeTicks = currentAnimationTicks();
    const uint64_t actorRenderStartTickCount = SDL_GetTicksNS();
    uint64_t gatherStageNanoseconds = 0;
    uint64_t placeholderStageNanoseconds = 0;
    uint64_t sortStageNanoseconds = 0;
    uint64_t submitStageNanoseconds = 0;
    size_t textureGroupCount = 0;
    size_t ensuredTextureLoadCount = 0;

    struct BillboardDrawItem
    {
        const SpriteFrameEntry *pFrame = nullptr;
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        bool hovered = false;
        uint32_t hoveredOutlineColorAbgr = 0;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float heightScale = 1.0f;
        float distanceSquared = 0.0f;
        float cameraDepth = 0.0f;
        uint32_t lightContributionAbgr = 0xff000000u;
    };

    thread_local std::vector<BillboardDrawItem> drawItems;
    drawItems.clear();
    size_t drawItemReserveCount = 0;

    if (view.m_outdoorDecorationBillboardSet)
    {
        drawItemReserveCount += view.m_outdoorDecorationBillboardSet->billboards.size();
    }

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        drawItemReserveCount += view.m_outdoorActorPreviewBillboardSet->billboards.size();
    }

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        drawItemReserveCount += view.m_pOutdoorWorldRuntime->mapActorCount();
    }

    drawItems.reserve(drawItemReserveCount);
    const auto resolveDecorationBillboardSpriteId = [&view](const DecorationBillboard &billboard, bool &hidden)
    {
        hidden = false;
        uint16_t spriteId = billboard.spriteId;

        if (!view.m_outdoorDecorationBillboardSet || view.m_pOutdoorWorldRuntime == nullptr)
        {
            return spriteId;
        }

        const EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState();

        if (pEventRuntimeState == nullptr)
        {
            return spriteId;
        }

        const uint32_t overrideKey =
            billboard.eventIdPrimary != 0 ? billboard.eventIdPrimary : billboard.eventIdSecondary;

        if (overrideKey == 0)
        {
            return spriteId;
        }

        const auto overrideIterator = pEventRuntimeState->spriteOverrides.find(overrideKey);

        if (overrideIterator == pEventRuntimeState->spriteOverrides.end())
        {
            return spriteId;
        }

        hidden = overrideIterator->second.hidden;

        if (!overrideIterator->second.textureName.has_value() || overrideIterator->second.textureName->empty())
        {
            return spriteId;
        }

        if (const DecorationEntry *pDecoration =
                view.m_outdoorDecorationBillboardSet->decorationTable.findByInternalName(
                    *overrideIterator->second.textureName))
        {
            return pDecoration->spriteId;
        }

        if (const std::optional<uint16_t> overrideSpriteId =
                view.m_outdoorDecorationBillboardSet->spriteFrameTable.findFrameIndexBySpriteName(
                    *overrideIterator->second.textureName))
        {
            return *overrideSpriteId;
        }

        return spriteId;
    };

    thread_local std::vector<OutdoorGameView::TerrainVertex> placeholderVertices;
    placeholderVertices.clear();

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        placeholderVertices.reserve(view.m_outdoorActorPreviewBillboardSet->billboards.size() * 6);
    }

    const std::optional<OutdoorGameView::InspectHit> hoveredInspectHit =
        resolveHoveredOutlineInspectHit(view, pViewMatrix);
    std::optional<size_t> hoveredRuntimeActorIndex;

    if (hoveredInspectHit && hoveredInspectHit->kind == "actor")
    {
        hoveredRuntimeActorIndex =
            OutdoorInteractionController::resolveRuntimeActorIndexForInspectHit(view, *hoveredInspectHit);
    }

    thread_local std::vector<bool> coveredRuntimeActors;
    coveredRuntimeActors.clear();

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        coveredRuntimeActors.assign(view.m_pOutdoorWorldRuntime->mapActorCount(), false);
    }

    auto appendActorDrawItem =
        [&](const OutdoorWorldRuntime::MapActorState *pRuntimeActor,
            std::optional<size_t> runtimeActorIndex,
            int actorX,
            int actorY,
            int actorZ,
            uint16_t actorRadius,
            uint16_t actorHeight,
            uint16_t sourceBillboardHeight,
            uint16_t spriteFrameIndex,
            const std::array<uint16_t, 8> &actionSpriteFrameIndices,
            bool useStaticFrame)
        {
            if (pRuntimeActor != nullptr && pRuntimeActor->isInvisible)
            {
                return;
            }

            const float deltaX = static_cast<float>(actorX) - cameraPosition.x;
            const float deltaY = static_cast<float>(actorY) - cameraPosition.y;
            const float deltaZ = static_cast<float>(actorZ) - cameraPosition.z;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

            if (distanceSquared > ActorBillboardRenderDistanceSquared)
            {
                return;
            }

            if (deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z <= BillboardNearDepth)
            {
                return;
            }

            uint32_t frameTimeTicks = useStaticFrame ? 0U : animationTimeTicks;

            if (pRuntimeActor != nullptr)
            {
                const size_t animationIndex = static_cast<size_t>(pRuntimeActor->animation);

                if (animationIndex < actionSpriteFrameIndices.size() && actionSpriteFrameIndices[animationIndex] != 0)
                {
                    spriteFrameIndex = actionSpriteFrameIndices[animationIndex];
                }

                frameTimeTicks = static_cast<uint32_t>(std::max(0.0f, pRuntimeActor->animationTimeTicks));
            }

            const SpriteFrameEntry *pFrame =
                view.m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, frameTimeTicks);

            if (pFrame == nullptr)
            {
                const float markerHalfSize =
                    std::max(48.0f, static_cast<float>(std::max(actorRadius, static_cast<uint16_t>(48))));
                const float baseX = static_cast<float>(actorX);
                const float baseY = static_cast<float>(actorY);
                const float baseZ = static_cast<float>(actorZ) + 96.0f;
                const uint32_t markerColor = 0xff3030ff;

                placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX, baseY - markerHalfSize, baseZ, markerColor});
                placeholderVertices.push_back({baseX, baseY + markerHalfSize, baseZ, markerColor});
                return;
            }

            const float angleToCamera = std::atan2(
                static_cast<float>(actorY) - cameraPosition.y,
                static_cast<float>(actorX) - cameraPosition.x);
            const float actorYaw = pRuntimeActor != nullptr ? pRuntimeActor->yawRadians : 0.0f;
            const float octantAngle = actorYaw - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const OutdoorGameView::BillboardTextureHandle *pExistingTexture =
                view.findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);
            const OutdoorGameView::BillboardTextureHandle *pTexture =
                pExistingTexture != nullptr
                    ? pExistingTexture
                    : ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

            if (pExistingTexture == nullptr && pTexture != nullptr)
            {
                ++ensuredTextureLoadCount;
            }

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                const float markerHalfSize =
                    std::max(48.0f, static_cast<float>(std::max(actorRadius, static_cast<uint16_t>(48))));
                const float baseX = static_cast<float>(actorX);
                const float baseY = static_cast<float>(actorY);
                const float baseZ = static_cast<float>(actorZ) + 96.0f;
                const uint32_t markerColor = 0xff3030ff;

                placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX + markerHalfSize, baseY, baseZ - markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX - markerHalfSize, baseY, baseZ + markerHalfSize, markerColor});
                placeholderVertices.push_back({baseX, baseY - markerHalfSize, baseZ, markerColor});
                placeholderVertices.push_back({baseX, baseY + markerHalfSize, baseZ, markerColor});
                return;
            }

            BillboardDrawItem drawItem = {};
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.hovered =
                runtimeActorIndex.has_value()
                && hoveredRuntimeActorIndex.has_value()
                && *runtimeActorIndex == *hoveredRuntimeActorIndex;
            drawItem.hoveredOutlineColorAbgr =
                drawItem.hovered && pRuntimeActor != nullptr
                    ? resolveHoveredActorOutlineColor(*pRuntimeActor)
                    : 0;
            drawItem.x = static_cast<float>(actorX);
            drawItem.y = static_cast<float>(actorY);
            drawItem.z = static_cast<float>(actorZ);
            drawItem.heightScale =
                pRuntimeActor != nullptr && sourceBillboardHeight > 0
                    ? static_cast<float>(actorHeight) / static_cast<float>(sourceBillboardHeight)
                    : 1.0f;
            if (pRuntimeActor != nullptr && pRuntimeActor->shrinkRemainingSeconds > 0.0f)
            {
                drawItem.heightScale *= std::clamp(pRuntimeActor->shrinkDamageMultiplier, 0.25f, 1.0f);
            }
            drawItem.distanceSquared = distanceSquared;
            drawItem.cameraDepth = deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;
            const float previewScale = std::max(pFrame->scale * drawItem.heightScale, 0.01f);
            drawItem.lightContributionAbgr = computeBillboardLightContributionAbgr(
                view,
                drawItem.x,
                drawItem.y,
                drawItem.z + static_cast<float>(pTexture->height) * previewScale * 0.5f);
            drawItems.push_back(drawItem);
        };

    if (view.m_showDecorationBillboards && view.m_outdoorDecorationBillboardSet)
    {
        for (const DecorationBillboard &billboard : view.m_outdoorDecorationBillboardSet->billboards)
        {
            bool hidden = false;
            const uint16_t spriteId =
                OutdoorInteractionController::resolveDecorationBillboardSpriteId(view, billboard, hidden);

            if (OutdoorInteractionController::isInteractiveDecorationHidden(view, billboard.entityIndex)
                || hidden
                || spriteId == 0)
            {
                continue;
            }

            const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
            const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
            const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
            const float cameraDepth = deltaX * cameraForward.x + deltaY * cameraForward.y + deltaZ * cameraForward.z;

            if (distanceSquared > DecorationBillboardRenderDistanceSquared || cameraDepth <= BillboardNearDepth)
            {
                continue;
            }

            const uint32_t animationOffsetTicks =
                animationTimeTicks + static_cast<uint32_t>(std::abs(billboard.x + billboard.y));
            const SpriteFrameEntry *pFrame =
                view.m_outdoorDecorationBillboardSet->spriteFrameTable.getFrame(spriteId, animationOffsetTicks);

            if (pFrame == nullptr)
            {
                continue;
            }

            const float facingRadians = static_cast<float>(billboard.facing) * Pi / 180.0f;
            const float angleToCamera = std::atan2(
                static_cast<float>(billboard.y) - cameraPosition.y,
                static_cast<float>(billboard.x) - cameraPosition.x);
            const float octantAngle = facingRadians - angleToCamera + Pi + (Pi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (Pi / 4.0f))) & 7;
            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, octant);
            const OutdoorGameView::BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                continue;
            }

            BillboardDrawItem drawItem = {};
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.x = static_cast<float>(billboard.x);
            drawItem.y = static_cast<float>(billboard.y);
            drawItem.z = static_cast<float>(billboard.z);
            drawItem.heightScale = 1.0f;
            drawItem.distanceSquared = distanceSquared;
            drawItem.cameraDepth = cameraDepth;
            drawItem.lightContributionAbgr = computeBillboardLightContributionAbgr(
                view,
                drawItem.x,
                drawItem.y,
                drawItem.z + static_cast<float>(pTexture->height) * std::max(pFrame->scale, 0.01f) * 0.5f);
            drawItems.push_back(drawItem);
        }
    }

    if (view.m_showActors && view.m_outdoorActorPreviewBillboardSet)
    {
        for (size_t billboardIndex = 0; billboardIndex < view.m_outdoorActorPreviewBillboardSet->billboards.size(); ++billboardIndex)
        {
            const ActorPreviewBillboard &billboard = view.m_outdoorActorPreviewBillboardSet->billboards[billboardIndex];

            if (billboard.source != ActorPreviewSource::Companion)
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = OutdoorInteractionController::runtimeActorStateForBillboard(view, billboard);
            const int actorX = pRuntimeActor != nullptr ? pRuntimeActor->x : billboard.x;
            const int actorY = pRuntimeActor != nullptr ? pRuntimeActor->y : billboard.y;
            const int actorZ = pRuntimeActor != nullptr ? pRuntimeActor->z : billboard.z;
            const uint16_t actorRadius = pRuntimeActor != nullptr ? pRuntimeActor->radius : billboard.radius;
            const uint16_t actorHeight = pRuntimeActor != nullptr ? pRuntimeActor->height : billboard.height;

            if (pRuntimeActor != nullptr && billboard.runtimeActorIndex < coveredRuntimeActors.size())
            {
                coveredRuntimeActors[billboard.runtimeActorIndex] = true;
            }

            appendActorDrawItem(
                pRuntimeActor,
                pRuntimeActor != nullptr ? std::optional<size_t>(billboard.runtimeActorIndex) : std::nullopt,
                actorX,
                actorY,
                actorZ,
                actorRadius,
                actorHeight,
                billboard.height,
                billboard.spriteFrameIndex,
                billboard.actionSpriteFrameIndices,
                billboard.useStaticFrame);
        }
    }

    if (view.m_showActors && view.m_pOutdoorWorldRuntime != nullptr)
    {
        for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            if (actorIndex < coveredRuntimeActors.size() && coveredRuntimeActors[actorIndex])
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pRuntimeActor == nullptr)
            {
                continue;
            }

            appendActorDrawItem(
                pRuntimeActor,
                actorIndex,
                pRuntimeActor->x,
                pRuntimeActor->y,
                pRuntimeActor->z,
                pRuntimeActor->radius,
                pRuntimeActor->height,
                pRuntimeActor->height,
                pRuntimeActor->spriteFrameIndex,
                pRuntimeActor->actionSpriteFrameIndices,
                pRuntimeActor->useStaticSpriteFrame);
        }
    }

    gatherStageNanoseconds += SDL_GetTicksNS() - actorRenderStartTickCount;

    if (!placeholderVertices.empty())
    {
        const uint64_t placeholderStageStartTickCount = SDL_GetTicksNS();

        if (bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(placeholderVertices.size()),
                OutdoorGameView::TerrainVertex::ms_layout) >= placeholderVertices.size())
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(placeholderVertices.size()),
                OutdoorGameView::TerrainVertex::ms_layout);
            std::memcpy(
                transientVertexBuffer.data,
                placeholderVertices.data(),
                static_cast<size_t>(placeholderVertices.size() * sizeof(OutdoorGameView::TerrainVertex)));

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(placeholderVertices.size()));
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_LINEAA
                | BGFX_STATE_DEPTH_TEST_LEQUAL);
            bgfx::submit(viewId, view.m_programHandle);
        }

        placeholderStageNanoseconds += SDL_GetTicksNS() - placeholderStageStartTickCount;
    }

    if (!bgfx::isValid(view.m_outdoorLitBillboardProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOverrideColorUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOutlineParamsUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardAmbientUniformHandle))
    {
        const uint64_t totalActorRenderNanoseconds = SDL_GetTicksNS() - actorRenderStartTickCount;

        if (DebugActorRenderHitchLogging && totalActorRenderNanoseconds >= RenderHitchLogThresholdNanoseconds)
        {
            std::cout << "Actor render hitch: total_ms="
                      << static_cast<double>(totalActorRenderNanoseconds) / 1000000.0
                      << " gather_ms=" << static_cast<double>(gatherStageNanoseconds) / 1000000.0
                      << " placeholder_ms=" << static_cast<double>(placeholderStageNanoseconds) / 1000000.0
                      << " sort_ms=" << static_cast<double>(sortStageNanoseconds) / 1000000.0
                      << " submit_ms=" << static_cast<double>(submitStageNanoseconds) / 1000000.0
                      << " draw_items=" << drawItems.size()
                      << " placeholder_vertices=" << placeholderVertices.size()
                      << " texture_groups=" << textureGroupCount
                      << " ensured_loads=" << ensuredTextureLoadCount
                      << '\n';
        }

        return;
    }

    const uint64_t sortStageStartTickCount = SDL_GetTicksNS();
    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            if (left.cameraDepth != right.cameraDepth)
            {
                return left.cameraDepth > right.cameraDepth;
            }

            return left.distanceSquared > right.distanceSquared;
        });
    sortStageNanoseconds += SDL_GetTicksNS() - sortStageStartTickCount;

    const uint32_t vertexCount = 6;
    applyBillboardFogUniforms(view, ActorBillboardRenderDistance);

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const OutdoorGameView::BillboardTextureHandle *pTexture = drawItem.pTexture;

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, OutdoorGameView::LitBillboardVertex::ms_layout) < vertexCount)
        {
            continue;
        }

        ++textureGroupCount;

        const uint64_t submitStageStartTickCount = SDL_GetTicksNS();
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const float spriteScale = std::max(frame.scale * drawItem.heightScale, 0.01f);
        const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
        const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {drawItem.x, drawItem.y, drawItem.z + worldHeight * 0.5f};
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {
            cameraUp.x * worldHeight * 0.5f,
            cameraUp.y * worldHeight * 0.5f,
            cameraUp.z * worldHeight * 0.5f
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        if (drawItem.hovered)
        {
            const float paddingU = HoveredActorOutlineThicknessPixels / static_cast<float>(pTexture->width);
            const float paddingV = HoveredActorOutlineThicknessPixels / static_cast<float>(pTexture->height);
            const float outlinedHalfWidth =
                (static_cast<float>(pTexture->width) * spriteScale + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale)
                * 0.5f;
            const float outlinedHalfHeight =
                (static_cast<float>(pTexture->height) * spriteScale + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale)
                * 0.5f;
            const bx::Vec3 outlineRight = {
                cameraRight.x * outlinedHalfWidth,
                cameraRight.y * outlinedHalfWidth,
                cameraRight.z * outlinedHalfWidth
            };
            const bx::Vec3 outlineUp = {
                cameraUp.x * outlinedHalfHeight,
                cameraUp.y * outlinedHalfHeight,
                cameraUp.z * outlinedHalfHeight
            };
            const float outlineU0 = drawItem.mirrored ? 1.0f + paddingU : -paddingU;
            const float outlineU1 = drawItem.mirrored ? -paddingU : 1.0f + paddingU;
            const float outlineVTop = -paddingV;
            const float outlineVBottom = 1.0f + paddingV;
            std::array<OutdoorGameView::LitBillboardVertex, 6> outlineVertices = {};
            outlineVertices[0] = {
                center.x - outlineRight.x - outlineUp.x,
                center.y - outlineRight.y - outlineUp.y,
                center.z - outlineRight.z - outlineUp.z,
                outlineU0,
                outlineVBottom,
                drawItem.lightContributionAbgr};
            outlineVertices[1] = {
                center.x - outlineRight.x + outlineUp.x,
                center.y - outlineRight.y + outlineUp.y,
                center.z - outlineRight.z + outlineUp.z,
                outlineU0,
                outlineVTop,
                drawItem.lightContributionAbgr};
            outlineVertices[2] = {
                center.x + outlineRight.x + outlineUp.x,
                center.y + outlineRight.y + outlineUp.y,
                center.z + outlineRight.z + outlineUp.z,
                outlineU1,
                outlineVTop,
                drawItem.lightContributionAbgr};
            outlineVertices[3] = outlineVertices[0];
            outlineVertices[4] = outlineVertices[2];
            outlineVertices[5] = {
                center.x + outlineRight.x - outlineUp.x,
                center.y + outlineRight.y - outlineUp.y,
                center.z + outlineRight.z - outlineUp.z,
                outlineU1,
                outlineVBottom,
                drawItem.lightContributionAbgr};

            if (bgfx::getAvailTransientVertexBuffer(vertexCount, OutdoorGameView::LitBillboardVertex::ms_layout)
                >= vertexCount)
            {
                bgfx::TransientVertexBuffer outlineTransientVertexBuffer = {};
                bgfx::allocTransientVertexBuffer(
                    &outlineTransientVertexBuffer,
                    vertexCount,
                    OutdoorGameView::LitBillboardVertex::ms_layout);
                std::memcpy(
                    outlineTransientVertexBuffer.data,
                    outlineVertices.data(),
                    static_cast<size_t>(outlineVertices.size() * sizeof(OutdoorGameView::LitBillboardVertex)));

                float outlineModelMatrix[16] = {};
                bx::mtxIdentity(outlineModelMatrix);
                bgfx::setTransform(outlineModelMatrix);
                bgfx::setVertexBuffer(0, &outlineTransientVertexBuffer, 0, vertexCount);
                bindTexture(
                    0,
                    view.m_terrainTextureSamplerHandle,
                    pTexture->textureHandle,
                    TextureFilterProfile::Billboard,
                    BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                applyBillboardAmbientUniform(view);
                applyBillboardOverrideColorUniform(view, drawItem.hoveredOutlineColorAbgr, 1.0f);
                applyBillboardOutlineParamsUniform(
                    view,
                    1.0f / static_cast<float>(pTexture->width),
                    1.0f / static_cast<float>(pTexture->height),
                    HoveredActorOutlineThicknessPixels);
                bgfx::setState(BillboardAlphaRenderState);
                bgfx::submit(viewId, view.m_outdoorLitBillboardProgramHandle);
            }
        }

        std::array<OutdoorGameView::LitBillboardVertex, 6> vertices = {};
        writeLitBillboardVertices(
            vertices.data(),
            center,
            right,
            up,
            u0,
            u1,
            drawItem.lightContributionAbgr);

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            vertexCount,
            OutdoorGameView::LitBillboardVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::LitBillboardVertex)));

        float modelMatrix[16] = {};
        bx::mtxIdentity(modelMatrix);
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, vertexCount);
        bindTexture(
            0,
            view.m_terrainTextureSamplerHandle,
            pTexture->textureHandle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        applyBillboardAmbientUniform(view);
        applyBillboardOverrideColorUniform(view, 0, 0.0f);
        applyBillboardOutlineParamsUniform(view, 0.0f, 0.0f, 0.0f);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_outdoorLitBillboardProgramHandle);
        submitStageNanoseconds += SDL_GetTicksNS() - submitStageStartTickCount;
    }

    const uint64_t totalActorRenderNanoseconds = SDL_GetTicksNS() - actorRenderStartTickCount;

    if (DebugActorRenderHitchLogging && totalActorRenderNanoseconds >= RenderHitchLogThresholdNanoseconds)
    {
        std::cout << "Actor render hitch: total_ms="
                  << static_cast<double>(totalActorRenderNanoseconds) / 1000000.0
                  << " gather_ms=" << static_cast<double>(gatherStageNanoseconds) / 1000000.0
                  << " placeholder_ms=" << static_cast<double>(placeholderStageNanoseconds) / 1000000.0
                  << " sort_ms=" << static_cast<double>(sortStageNanoseconds) / 1000000.0
                  << " submit_ms=" << static_cast<double>(submitStageNanoseconds) / 1000000.0
                  << " draw_items=" << drawItems.size()
                  << " placeholder_vertices=" << placeholderVertices.size()
                  << " texture_groups=" << textureGroupCount
                  << " ensured_loads=" << ensuredTextureLoadCount
                  << '\n';
    }
}

void OutdoorBillboardRenderer::renderRuntimeWorldItems(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    if (!bgfx::isValid(view.m_outdoorLitBillboardProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOverrideColorUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOutlineParamsUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardAmbientUniformHandle))
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (view.m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }
    else if (view.m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    applyBillboardFogUniforms(view, ActorBillboardRenderDistance);

    struct BillboardDrawItem
    {
        const OutdoorWorldRuntime::WorldItemState *pWorldItem = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        bool hovered = false;
        uint32_t hoveredOutlineColorAbgr = 0;
        float distanceSquared = 0.0f;
        uint32_t lightContributionAbgr = 0xff000000u;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(view.m_pOutdoorWorldRuntime->worldItemCount());
    const std::optional<OutdoorGameView::InspectHit> hoveredInspectHit =
        resolveHoveredOutlineInspectHit(view, pViewMatrix);
    std::optional<size_t> hoveredWorldItemIndex;

    if (hoveredInspectHit && hoveredInspectHit->kind == "world_item")
    {
        hoveredWorldItemIndex = hoveredInspectHit->bModelIndex;
    }

    for (size_t worldItemIndex = 0; worldItemIndex < view.m_pOutdoorWorldRuntime->worldItemCount(); ++worldItemIndex)
    {
        const OutdoorWorldRuntime::WorldItemState *pWorldItem = view.m_pOutdoorWorldRuntime->worldItemState(worldItemIndex);

        if (pWorldItem == nullptr)
        {
            continue;
        }

        uint16_t spriteFrameIndex = pWorldItem->objectSpriteFrameIndex;

        if (spriteFrameIndex == 0 && !pWorldItem->objectSpriteName.empty())
        {
            const std::optional<uint16_t> spriteFrameIndexByName =
                pSpriteFrameTable->findFrameIndexBySpriteName(pWorldItem->objectSpriteName);

            if (spriteFrameIndexByName)
            {
                spriteFrameIndex = *spriteFrameIndexByName;
            }
        }

        if (spriteFrameIndex == 0)
        {
            spriteFrameIndex = pWorldItem->objectSpriteId;
        }

        if (spriteFrameIndex == 0)
        {
            continue;
        }

        const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteFrameIndex, pWorldItem->timeSinceCreatedTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const OutdoorGameView::BillboardTextureHandle *pTexture =
            ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        const float deltaX = pWorldItem->x - cameraPosition.x;
        const float deltaY = pWorldItem->y - cameraPosition.y;
        const float deltaZ = pWorldItem->z - cameraPosition.z;

        BillboardDrawItem drawItem = {};
        drawItem.pWorldItem = pWorldItem;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.hovered = hoveredWorldItemIndex.has_value() && *hoveredWorldItemIndex == worldItemIndex;
        drawItem.hoveredOutlineColorAbgr = drawItem.hovered ? hoveredWorldItemOutlineColor() : 0;
        drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        drawItem.lightContributionAbgr = computeBillboardLightContributionAbgr(
            view,
            pWorldItem->x,
            pWorldItem->y,
            pWorldItem->z + static_cast<float>(pTexture->height) * std::max(pFrame->scale, 0.01f) * 0.5f);
        drawItems.push_back(drawItem);
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            return left.distanceSquared > right.distanceSquared;
        });

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const OutdoorWorldRuntime::WorldItemState &worldItem = *drawItem.pWorldItem;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const OutdoorGameView::BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {worldItem.x, worldItem.y, worldItem.z + worldHeight * 0.5f};
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {
            cameraUp.x * worldHeight * 0.5f,
            cameraUp.y * worldHeight * 0.5f,
            cameraUp.z * worldHeight * 0.5f
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        if (drawItem.hovered)
        {
            const float paddingU = HoveredActorOutlineThicknessPixels / static_cast<float>(texture.width);
            const float paddingV = HoveredActorOutlineThicknessPixels / static_cast<float>(texture.height);
            const float outlinedHalfWidth =
                (static_cast<float>(texture.width) * spriteScale + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale)
                * 0.5f;
            const float outlinedHalfHeight =
                (static_cast<float>(texture.height) * spriteScale + HoveredActorOutlineThicknessPixels * 2.0f * spriteScale)
                * 0.5f;
            const bx::Vec3 outlineRight = {
                cameraRight.x * outlinedHalfWidth,
                cameraRight.y * outlinedHalfWidth,
                cameraRight.z * outlinedHalfWidth
            };
            const bx::Vec3 outlineUp = {
                cameraUp.x * outlinedHalfHeight,
                cameraUp.y * outlinedHalfHeight,
                cameraUp.z * outlinedHalfHeight
            };
            const float outlineU0 = drawItem.mirrored ? 1.0f + paddingU : -paddingU;
            const float outlineU1 = drawItem.mirrored ? -paddingU : 1.0f + paddingU;
            const float outlineVTop = -paddingV;
            const float outlineVBottom = 1.0f + paddingV;
            std::array<OutdoorGameView::LitBillboardVertex, 6> outlineVertices = {};
            outlineVertices[0] = {
                center.x - outlineRight.x - outlineUp.x,
                center.y - outlineRight.y - outlineUp.y,
                center.z - outlineRight.z - outlineUp.z,
                outlineU0,
                outlineVBottom,
                drawItem.lightContributionAbgr};
            outlineVertices[1] = {
                center.x - outlineRight.x + outlineUp.x,
                center.y - outlineRight.y + outlineUp.y,
                center.z - outlineRight.z + outlineUp.z,
                outlineU0,
                outlineVTop,
                drawItem.lightContributionAbgr};
            outlineVertices[2] = {
                center.x + outlineRight.x + outlineUp.x,
                center.y + outlineRight.y + outlineUp.y,
                center.z + outlineRight.z + outlineUp.z,
                outlineU1,
                outlineVTop,
                drawItem.lightContributionAbgr};
            outlineVertices[3] = outlineVertices[0];
            outlineVertices[4] = outlineVertices[2];
            outlineVertices[5] = {
                center.x + outlineRight.x - outlineUp.x,
                center.y + outlineRight.y - outlineUp.y,
                center.z + outlineRight.z - outlineUp.z,
                outlineU1,
                outlineVBottom,
                drawItem.lightContributionAbgr};

            if (bgfx::getAvailTransientVertexBuffer(
                    static_cast<uint32_t>(outlineVertices.size()),
                    OutdoorGameView::LitBillboardVertex::ms_layout) >= outlineVertices.size())
            {
                bgfx::TransientVertexBuffer outlineTransientVertexBuffer = {};
                bgfx::allocTransientVertexBuffer(
                    &outlineTransientVertexBuffer,
                    static_cast<uint32_t>(outlineVertices.size()),
                    OutdoorGameView::LitBillboardVertex::ms_layout);
                std::memcpy(
                    outlineTransientVertexBuffer.data,
                    outlineVertices.data(),
                    static_cast<size_t>(outlineVertices.size() * sizeof(OutdoorGameView::LitBillboardVertex)));

                float outlineModelMatrix[16] = {};
                bx::mtxIdentity(outlineModelMatrix);
                bgfx::setTransform(outlineModelMatrix);
                bgfx::setVertexBuffer(
                    0,
                    &outlineTransientVertexBuffer,
                    0,
                    static_cast<uint32_t>(outlineVertices.size()));
                bindTexture(
                    0,
                    view.m_terrainTextureSamplerHandle,
                    texture.textureHandle,
                    TextureFilterProfile::Billboard,
                    BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                applyBillboardAmbientUniform(view);
                applyBillboardOverrideColorUniform(view, drawItem.hoveredOutlineColorAbgr, 1.0f);
                applyBillboardOutlineParamsUniform(
                    view,
                    1.0f / static_cast<float>(texture.width),
                    1.0f / static_cast<float>(texture.height),
                    HoveredActorOutlineThicknessPixels);
                bgfx::setState(BillboardAlphaRenderState);
                bgfx::submit(viewId, view.m_outdoorLitBillboardProgramHandle);
            }
        }

        std::array<OutdoorGameView::LitBillboardVertex, 6> vertices = {};
        writeLitBillboardVertices(
            vertices.data(),
            center,
            right,
            up,
            u0,
            u1,
            drawItem.lightContributionAbgr);

        if (bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(vertices.size()),
                OutdoorGameView::LitBillboardVertex::ms_layout) < vertices.size())
        {
            continue;
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
        bindTexture(
            0,
            view.m_terrainTextureSamplerHandle,
            texture.textureHandle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        applyBillboardAmbientUniform(view);
        applyBillboardOverrideColorUniform(view, 0, 0.0f);
        applyBillboardOutlineParamsUniform(view, 0.0f, 0.0f, 0.0f);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_outdoorLitBillboardProgramHandle);
    }
}

void OutdoorBillboardRenderer::renderRuntimeProjectiles(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    if (!bgfx::isValid(view.m_outdoorLitBillboardProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOverrideColorUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOutlineParamsUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardAmbientUniformHandle))
    {
        return;
    }

    const SpriteFrameTable *pSpriteFrameTable = nullptr;

    if (view.m_outdoorSpriteObjectBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable;
    }
    else if (view.m_outdoorActorPreviewBillboardSet)
    {
        pSpriteFrameTable = &view.m_outdoorActorPreviewBillboardSet->spriteFrameTable;
    }

    if (pSpriteFrameTable == nullptr)
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    applyBillboardFogUniforms(view, RuntimeProjectileRenderDistance);

    struct BillboardDrawItem
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        const SpriteFrameEntry *pFrame = nullptr;
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
        uint32_t lightContributionAbgr = 0xff000000u;
    };

    std::vector<BillboardDrawItem> drawItems;
    const std::vector<GameplayProjectilePresentationState> &projectiles =
        view.m_gameSession.gameplayFxService().activeProjectilePresentationStates();
    const std::vector<GameplayProjectileImpactPresentationState> &impacts =
        view.m_gameSession.gameplayFxService().activeProjectileImpactPresentationStates();
    drawItems.reserve(
        projectiles.size()
        + impacts.size()
        + view.m_pOutdoorWorldRuntime->fireSpikeTrapCount());

    auto appendRuntimeDrawItem =
        [&](uint32_t runtimeId,
            const char *kind,
            float x,
            float y,
            float z,
            uint16_t cachedSpriteFrameIndex,
            uint16_t spriteId,
            const std::string &spriteName,
            uint32_t timeTicks)
        {
            uint16_t spriteFrameIndex = cachedSpriteFrameIndex;
            const bool shouldLog = DebugProjectileDrawLogging && timeTicks <= 16;
            const char *pResolutionSource = cachedSpriteFrameIndex != 0 ? "cached" : "none";
            const float deltaX = x - cameraPosition.x;
            const float deltaY = y - cameraPosition.y;
            const float deltaZ = z - cameraPosition.z;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;

            if (distanceSquared > RuntimeProjectileRenderDistanceSquared)
            {
                return;
            }

            if (spriteFrameIndex == 0 && !spriteName.empty())
            {
                const std::optional<uint16_t> spriteFrameIndexByName =
                    pSpriteFrameTable->findFrameIndexBySpriteName(spriteName);

                if (spriteFrameIndexByName)
                {
                    spriteFrameIndex = *spriteFrameIndexByName;
                    pResolutionSource = "name";
                }
            }

            if (spriteFrameIndex == 0)
            {
                spriteFrameIndex = spriteId;
                pResolutionSource = "id";
            }

            if (spriteFrameIndex == 0)
            {
                if (shouldLog)
                {
                    std::cout << "Projectile draw skipped kind=" << kind
                              << " id=" << runtimeId
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " reason=no_frame_index\n";
                }
                return;
            }

            const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteFrameIndex, timeTicks);

            if (pFrame == nullptr)
            {
                if (shouldLog)
                {
                    std::cout << "Projectile draw skipped kind=" << kind
                              << " id=" << runtimeId
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " frameIndex=" << spriteFrameIndex
                              << " source=" << pResolutionSource
                              << " reason=frame_missing\n";
                }
                return;
            }

            const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
            const OutdoorGameView::BillboardTextureHandle *pTexture =
                ensureSpriteBillboardTexture(view, resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                if (shouldLog)
                {
                    std::cout << "Projectile draw skipped kind=" << kind
                              << " id=" << runtimeId
                              << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                              << " spriteId=" << spriteId
                              << " frameIndex=" << spriteFrameIndex
                              << " source=" << pResolutionSource
                              << " texture=\"" << resolvedTexture.textureName << "\""
                              << " palette=" << pFrame->paletteId
                              << " reason=texture_missing\n";
                }
                return;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const bool centerAnchored = SpriteFrameTable::hasFlag(pFrame->flags, SpriteFrameFlag::Center);

            if (shouldLog)
            {
                std::cout << "Projectile draw kind=" << kind
                          << " id=" << runtimeId
                          << " sprite=\"" << (spriteName.empty() ? "<none>" : spriteName) << "\""
                          << " spriteId=" << spriteId
                          << " frameIndex=" << spriteFrameIndex
                          << " source=" << pResolutionSource
                          << " texture=\"" << resolvedTexture.textureName << "\""
                          << " palette=" << pFrame->paletteId
                          << " texSize=(" << pTexture->width << ", " << pTexture->height << ")"
                          << " scale=" << spriteScale
                          << " worldSize=(" << worldWidth << ", " << worldHeight << ")"
                          << " pos=(" << x << ", " << y << ", " << z << ")"
                          << " ageTicks=" << timeTicks
                          << '\n';
            }

            BillboardDrawItem drawItem = {};
            drawItem.x = x;
            drawItem.y = y;
            drawItem.z = z;
            drawItem.pFrame = pFrame;
            drawItem.pTexture = pTexture;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItem.distanceSquared = distanceSquared;
            drawItem.lightContributionAbgr = computeBillboardLightContributionAbgr(
                view,
                x,
                y,
                centerAnchored ? z : z + worldHeight * 0.5f);
            drawItems.push_back(drawItem);
        };

    for (const GameplayProjectilePresentationState &projectile : projectiles)
    {
        appendRuntimeDrawItem(
            projectile.projectileId,
            "projectile",
            projectile.x,
            projectile.y,
            projectile.z,
            projectile.objectSpriteFrameIndex,
            projectile.objectSpriteId,
            projectile.objectSpriteName,
            projectile.timeSinceCreatedTicks);
    }

    for (const GameplayProjectileImpactPresentationState &impact : impacts)
    {
        const FxRecipes::ProjectileRecipe recipe = FxRecipes::classifyProjectileRecipe(
            impact.sourceSpellId,
            impact.sourceObjectName,
            impact.sourceObjectSpriteName,
            impact.sourceObjectFlags);

        if (FxRecipes::projectileRecipeUsesDedicatedImpactFx(recipe))
        {
            continue;
        }

        appendRuntimeDrawItem(
            impact.effectId,
            "impact",
            impact.x,
            impact.y,
            impact.z,
            impact.objectSpriteFrameIndex,
            impact.objectSpriteId,
            impact.objectSpriteName,
            impact.freezeAnimation ? 0u : impact.timeSinceCreatedTicks);
    }

    for (size_t trapIndex = 0; trapIndex < view.m_pOutdoorWorldRuntime->fireSpikeTrapCount(); ++trapIndex)
    {
        const OutdoorWorldRuntime::FireSpikeTrapState *pTrap = view.m_pOutdoorWorldRuntime->fireSpikeTrapState(trapIndex);

        if (pTrap == nullptr)
        {
            continue;
        }

        appendRuntimeDrawItem(
            pTrap->trapId,
            "fire_spike",
            pTrap->x,
            pTrap->y,
            pTrap->z,
            pTrap->objectSpriteFrameIndex,
            pTrap->objectSpriteId,
            pTrap->objectSpriteName,
            pTrap->timeSinceCreatedTicks);
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            const uint16_t leftTextureId = left.pTexture != nullptr ? left.pTexture->textureHandle.idx : 0;
            const uint16_t rightTextureId = right.pTexture != nullptr ? right.pTexture->textureHandle.idx : 0;

            if (leftTextureId != rightTextureId)
            {
                return leftTextureId < rightTextureId;
            }

            return left.distanceSquared > right.distanceSquared;
        });

    size_t groupBegin = 0;

    while (groupBegin < drawItems.size())
    {
        const OutdoorGameView::BillboardTextureHandle *pTexture = drawItems[groupBegin].pTexture;

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            ++groupBegin;
            continue;
        }

        size_t groupEnd = groupBegin + 1;

        while (groupEnd < drawItems.size() && drawItems[groupEnd].pTexture == pTexture)
        {
            ++groupEnd;
        }

        const uint32_t vertexCount = static_cast<uint32_t>((groupEnd - groupBegin) * 6);

        if (bgfx::getAvailTransientVertexBuffer(vertexCount, OutdoorGameView::LitBillboardVertex::ms_layout) < vertexCount)
        {
            groupBegin = groupEnd;
            continue;
        }

        std::vector<OutdoorGameView::LitBillboardVertex> vertices;
        vertices.reserve(static_cast<size_t>(vertexCount));

        for (size_t index = groupBegin; index < groupEnd; ++index)
        {
            const BillboardDrawItem &drawItem = drawItems[index];
            const SpriteFrameEntry &frame = *drawItem.pFrame;
            const float spriteScale = std::max(frame.scale, 0.01f);
            const float worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            const float worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            const float halfWidth = worldWidth * 0.5f;
            const bool centerAnchored = SpriteFrameTable::hasFlag(frame.flags, SpriteFrameFlag::Center);
            const bx::Vec3 center = {
                drawItem.x,
                drawItem.y,
                centerAnchored ? drawItem.z : drawItem.z + worldHeight * 0.5f
            };
            const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
            const bx::Vec3 up = {
                cameraUp.x * worldHeight * 0.5f,
                cameraUp.y * worldHeight * 0.5f,
                cameraUp.z * worldHeight * 0.5f
            };
            const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
            const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

            appendLitBillboardVertices(
                vertices,
                center,
                right,
                up,
                u0,
                u1,
                drawItem.lightContributionAbgr);
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
        bindTexture(
            0,
            view.m_terrainTextureSamplerHandle,
            pTexture->textureHandle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        applyBillboardAmbientUniform(view);
        applyBillboardOverrideColorUniform(view, 0, 0.0f);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_outdoorLitBillboardProgramHandle);

        groupBegin = groupEnd;
    }
}

void OutdoorBillboardRenderer::renderFxContactShadows(
    OutdoorGameView &view,
    uint16_t viewId)
{
    if (!bgfx::isValid(view.m_outdoorLitBillboardProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOverrideColorUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOutlineParamsUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardAmbientUniformHandle))
    {
        return;
    }

    const std::vector<WorldFxContactShadow> &shadows = view.m_worldFxSystem.contactShadows();

    if (shadows.empty())
    {
        return;
    }

    const OutdoorGameView::BillboardTextureHandle *pShadowTexture = view.findBillboardTexture(ContactShadowTextureName);

    if (pShadowTexture == nullptr)
    {
        return;
    }

    applyBillboardFogUniforms(view, ActorBillboardRenderDistance);

    std::vector<OutdoorGameView::LitBillboardVertex> vertices;
    vertices.reserve(shadows.size() * 6);

    for (const WorldFxContactShadow &shadow : shadows)
    {
        const bx::Vec3 center = {shadow.x, shadow.y, shadow.z};
        const bx::Vec3 right = {shadow.radius, 0.0f, 0.0f};
        const bx::Vec3 up = {0.0f, shadow.radius, 0.0f};
        appendLitBillboardVertices(vertices, center, right, up, 0.0f, 1.0f, shadow.colorAbgr);
    }

    if (vertices.empty())
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
    bindTexture(
        0,
        view.m_terrainTextureSamplerHandle,
        pShadowTexture->textureHandle,
        TextureFilterProfile::Billboard,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    applyBillboardAmbientUniform(view);
    applyBillboardOverrideColorUniform(view, 0, 0.0f);
    applyBillboardOutlineParamsUniform(view, 0.0f, 0.0f, 0.0f);
    bgfx::setState(BillboardAlphaRenderState);
    bgfx::submit(viewId, view.m_outdoorLitBillboardProgramHandle);
}

void OutdoorBillboardRenderer::renderFxGlowBillboards(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix)
{
    const std::vector<WorldFxGlowBillboard> &glowBillboards = view.m_worldFxSystem.glowBillboards();

    if (glowBillboards.empty())
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    vertices.reserve(glowBillboards.size() * 6);

    for (const WorldFxGlowBillboard &glow : glowBillboards)
    {
        if (!glow.renderVisibleBillboard)
        {
            continue;
        }

        const bx::Vec3 center = {glow.x, glow.y, glow.z};
        const bx::Vec3 right = {
            cameraRight.x * glow.radius,
            cameraRight.y * glow.radius,
            cameraRight.z * glow.radius
        };
        const bx::Vec3 up = {
            cameraUp.x * glow.radius,
            cameraUp.y * glow.radius,
            cameraUp.z * glow.radius
        };
        appendWorldQuadVertices(vertices, center, right, up, glow.colorAbgr);
    }

    submitColoredVertices(view, viewId, vertices, ColoredAdditiveRenderState);
}

void OutdoorBillboardRenderer::renderSpriteObjectBillboards(
    OutdoorGameView &view,
    uint16_t viewId,
    const float *pViewMatrix,
    const bx::Vec3 &cameraPosition)
{
    if (!view.m_outdoorSpriteObjectBillboardSet)
    {
        return;
    }

    if (!bgfx::isValid(view.m_outdoorLitBillboardProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOverrideColorUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardOutlineParamsUniformHandle)
        || !bgfx::isValid(view.m_outdoorBillboardAmbientUniformHandle))
    {
        return;
    }

    const bx::Vec3 cameraRight = {pViewMatrix[0], pViewMatrix[4], pViewMatrix[8]};
    const bx::Vec3 cameraUp = {pViewMatrix[1], pViewMatrix[5], pViewMatrix[9]};
    applyBillboardFogUniforms(view, ActorBillboardRenderDistance);

    struct BillboardDrawItem
    {
        const SpriteObjectBillboard *pBillboard = nullptr;
        const SpriteFrameEntry *pFrame = nullptr;
        const OutdoorGameView::BillboardTextureHandle *pTexture = nullptr;
        bool mirrored = false;
        float distanceSquared = 0.0f;
        uint32_t lightContributionAbgr = 0xff000000u;
    };

    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(view.m_outdoorSpriteObjectBillboardSet->billboards.size());

    for (const SpriteObjectBillboard &billboard : view.m_outdoorSpriteObjectBillboardSet->billboards)
    {
        const SpriteFrameEntry *pFrame =
            view.m_outdoorSpriteObjectBillboardSet->spriteFrameTable.getFrame(
                billboard.objectSpriteId,
                billboard.timeSinceCreatedTicks);

        if (pFrame == nullptr)
        {
            continue;
        }

        const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
        const OutdoorGameView::BillboardTextureHandle *pTexture = view.findBillboardTexture(resolvedTexture.textureName);

        if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
        {
            continue;
        }

        const float deltaX = static_cast<float>(billboard.x) - cameraPosition.x;
        const float deltaY = static_cast<float>(billboard.y) - cameraPosition.y;
        const float deltaZ = static_cast<float>(billboard.z) - cameraPosition.z;

        BillboardDrawItem drawItem = {};
        drawItem.pBillboard = &billboard;
        drawItem.pFrame = pFrame;
        drawItem.pTexture = pTexture;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItem.distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        drawItem.lightContributionAbgr = computeBillboardLightContributionAbgr(
            view,
            static_cast<float>(billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z) + static_cast<float>(pTexture->height) * std::max(pFrame->scale, 0.01f) * 0.5f);
        drawItems.push_back(drawItem);
    }

    std::sort(
        drawItems.begin(),
        drawItems.end(),
        [](const BillboardDrawItem &left, const BillboardDrawItem &right)
        {
            return left.distanceSquared > right.distanceSquared;
        });

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        const SpriteObjectBillboard &billboard = *drawItem.pBillboard;
        const SpriteFrameEntry &frame = *drawItem.pFrame;
        const OutdoorGameView::BillboardTextureHandle &texture = *drawItem.pTexture;
        const float spriteScale = std::max(frame.scale, 0.01f);
        const float worldWidth = static_cast<float>(texture.width) * spriteScale;
        const float worldHeight = static_cast<float>(texture.height) * spriteScale;
        const float halfWidth = worldWidth * 0.5f;
        const bx::Vec3 center = {
            static_cast<float>(billboard.x),
            static_cast<float>(billboard.y),
            static_cast<float>(billboard.z) + worldHeight * 0.5f
        };
        const bx::Vec3 right = {cameraRight.x * halfWidth, cameraRight.y * halfWidth, cameraRight.z * halfWidth};
        const bx::Vec3 up = {cameraUp.x * worldHeight * 0.5f, cameraUp.y * worldHeight * 0.5f, cameraUp.z * worldHeight * 0.5f};
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;

        std::array<OutdoorGameView::LitBillboardVertex, 6> vertices = {};
        writeLitBillboardVertices(
            vertices.data(),
            center,
            right,
            up,
            u0,
            u1,
            drawItem.lightContributionAbgr);

        if (bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(vertices.size()),
                OutdoorGameView::LitBillboardVertex::ms_layout) < vertices.size())
        {
            continue;
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
        bindTexture(
            0,
            view.m_terrainTextureSamplerHandle,
            texture.textureHandle,
            TextureFilterProfile::Billboard,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        applyBillboardAmbientUniform(view);
        applyBillboardOverrideColorUniform(view, 0, 0.0f);
        applyBillboardOutlineParamsUniform(view, 0.0f, 0.0f, 0.0f);
        bgfx::setState(BillboardAlphaRenderState);
        bgfx::submit(viewId, view.m_outdoorLitBillboardProgramHandle);
    }
}

} // namespace OpenYAMM::Game
