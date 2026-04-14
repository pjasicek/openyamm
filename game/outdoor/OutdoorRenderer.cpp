#include "game/outdoor/OutdoorRenderer.h"

#include "game/outdoor/OutdoorBillboardRenderer.h"
#include "game/fx/ParticleRenderer.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t SkyViewId = 0;
constexpr uint16_t MainViewId = 1;
constexpr float Pi = 3.14159265358979323846f;
constexpr float CameraVerticalFovDegrees = 60.0f;
constexpr float ActorBillboardRenderDistance = 16384.0f;
constexpr float ActorBillboardRenderDistanceSquared =
    ActorBillboardRenderDistance * ActorBillboardRenderDistance;
constexpr float SkyProjectionPitchOffsetRadians = Pi / 64.0f;
constexpr float SkyFogHorizonPixels = 39.0f;
constexpr int32_t MapWeatherFoggy = 1;
constexpr size_t MaxOutdoorFxLights = 8;
constexpr float OutdoorFxLightRefreshIntervalSeconds = 1.0f / 60.0f;
constexpr float OutdoorFxLightingAmbient = 1.0f;
// OpenYAMM tuning: keep outdoor FX lights visibly readable against the current ambient baseline.
constexpr float OutdoorFxLightingScale = 1.6f;

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

uint32_t withAlpha(uint32_t abgr, uint8_t alpha)
{
    return (abgr & 0x00ffffffu) | (static_cast<uint32_t>(alpha) << 24);
}

float smoothstep(float edge0, float edge1, float value)
{
    if (edge0 == edge1)
    {
        return value < edge0 ? 0.0f : 1.0f;
    }

    const float t = std::clamp((value - edge0) / (edge1 - edge0), 0.0f, 1.0f);
    return t * t * (3.0f - 2.0f * t);
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

uint32_t computeOutdoorSkyTintAbgr(const OutdoorWorldRuntime &worldRuntime)
{
    const float minutesOfDay = std::fmod(std::max(worldRuntime.gameMinutes(), 0.0f), 1440.0f);

    if (minutesOfDay < 300.0f || minutesOfDay >= 1260.0f)
    {
        return makeAbgr(39, 39, 39);
    }

    const float daylightMinutes = minutesOfDay - 300.0f;
    const float mirroredDaylightMinutes = daylightMinutes >= 480.0f ? 960.0f - daylightMinutes : daylightMinutes;
    const int maxTerrainDimmingLevel = static_cast<int>(20.0f - mirroredDaylightMinutes / 480.0f * 20.0f);
    const int skyValue = std::clamp(255 - 8 * maxTerrainDimmingLevel, 0, 255);
    return makeAbgr(
        static_cast<uint8_t>(skyValue),
        static_cast<uint8_t>(skyValue),
        static_cast<uint8_t>(skyValue));
}

uint32_t computeOutdoorSkyFogColorAbgr(const OutdoorWorldRuntime::AtmosphereState &atmosphereState)
{
    if ((atmosphereState.weatherFlags & MapWeatherFoggy) == 0)
    {
        return 0xff000000u;
    }

    if (atmosphereState.isNight)
    {
        return makeAbgr(31, 31, 31);
    }

    const int fogLevel = std::clamp(
        static_cast<int>(std::lround((1.0f - atmosphereState.fogDensity) * 200.0f + atmosphereState.fogDensity * 31.0f)),
        0,
        255);
    return makeAbgr(
        static_cast<uint8_t>(fogLevel),
        static_cast<uint8_t>(fogLevel),
        static_cast<uint8_t>(fogLevel));
}

struct OutdoorSkyVertex
{
    float screenX = 0.0f;
    float screenY = 0.0f;
    float reciprocalW = 1.0f;
    float u = 0.0f;
    float v = 0.0f;
};

OutdoorSkyVertex computeOutdoorSkyVertex(
    float screenX,
    float screenY,
    float viewWidth,
    float viewHeight,
    float cameraZ,
    float cameraYawRadians,
    float cameraPitchRadians,
    float farClipDistance,
    float elapsedTimeSeconds,
    float textureWidth,
    float textureHeight)
{
    const float viewPlaneDistancePixels =
        (viewHeight * 0.5f) / std::tan((CameraVerticalFovDegrees * Pi / 180.0f) * 0.5f);
    const float viewportCenterX = viewWidth * 0.5f;
    const float viewportCenterY = viewHeight * 0.5f;
    const float horizonHeightOffset =
        (viewPlaneDistancePixels * cameraZ) / (viewPlaneDistancePixels + farClipDistance) + viewportCenterY;
    const float xDistance = (viewportCenterX - screenX) / viewPlaneDistancePixels;
    const float yDistance = (horizonHeightOffset - screenY) / viewPlaneDistancePixels;
    const float oeViewPitchRadians = -cameraPitchRadians;
    const float cosYaw = std::cos(cameraYawRadians);
    const float sinYaw = std::sin(cameraYawRadians);
    const float cosPitch = std::cos(oeViewPitchRadians);
    const float sinPitch = std::sin(oeViewPitchRadians);
    const float skyLeft =
        (-sinYaw * xDistance)
        + (cosYaw * sinPitch * yDistance)
        + (cosYaw * cosPitch);
    const float skyFront =
        (cosYaw * xDistance)
        + (sinYaw * sinPitch * yDistance)
        + (sinYaw * cosPitch);
    const float v18x = -std::sin((-oeViewPitchRadians + SkyProjectionPitchOffsetRadians));
    const float v18z = -std::cos(oeViewPitchRadians + SkyProjectionPitchOffsetRadians);
    float topProjection = v18x + v18z * yDistance;

    if (topProjection > -0.0000001f)
    {
        topProjection = -0.0000001f;
    }

    const float reciprocalW = -64.0f / topProjection;
    const float textureOffsetU = elapsedTimeSeconds + skyLeft * reciprocalW;
    const float textureOffsetV = elapsedTimeSeconds + skyFront * reciprocalW;
    return {
        screenX,
        screenY,
        reciprocalW,
        textureOffsetU / textureWidth,
        textureOffsetV / textureHeight
    };
}

struct OutdoorFogParameters
{
    std::array<float, 4> color = {0.0f, 0.0f, 0.0f, 1.0f};
    std::array<float, 4> densities = {0.0f, 0.0f, 0.0f, 0.0f};
    std::array<float, 4> distances = {1.0f, 1.0f, 2.0f, 0.0f};
};

std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName)
{
    std::filesystem::path shaderRoot = OPENYAMM_BGFX_SHADER_DIR;

    if (rendererType == bgfx::RendererType::OpenGL)
    {
        return shaderRoot / "glsl" / (std::string(pShaderName) + ".bin");
    }

    if (rendererType == bgfx::RendererType::Noop)
    {
        return {};
    }

    return {};
}

std::vector<uint8_t> readBinaryFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);

    if (!file)
    {
        return {};
    }

    return std::vector<uint8_t>(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
}

float resolveActorAabbBaseZ(
    const OutdoorMapData &outdoorMapData,
    const OutdoorWorldRuntime::MapActorState *pActorState,
    int actorX,
    int actorY,
    int actorZ,
    bool clampDeadActorToGround)
{
    if (!clampDeadActorToGround)
    {
        return static_cast<float>(actorZ);
    }

    if (pActorState != nullptr && pActorState->movementStateInitialized)
    {
        const OutdoorMoveState &movementState = pActorState->movementState;

        if (movementState.supportKind == OutdoorSupportKind::Terrain
            || movementState.supportKind == OutdoorSupportKind::BModelFace)
        {
            return movementState.footZ - 1.0f;
        }
    }

    return sampleOutdoorSupportFloorHeight(
        outdoorMapData,
        static_cast<float>(actorX),
        static_cast<float>(actorY),
        static_cast<float>(actorZ));
}

std::vector<uint8_t> extractAtlasRegionPixels(
    const OutdoorTerrainTextureAtlas &textureAtlas,
    const OutdoorTerrainAtlasRegion &region)
{
    if (!region.isValid || textureAtlas.tileSize <= 0 || textureAtlas.width <= 0 || textureAtlas.height <= 0)
    {
        return {};
    }

    const int atlasX = static_cast<int>(std::lround(region.u0 * static_cast<float>(textureAtlas.width)));
    const int atlasY = static_cast<int>(std::lround(region.v0 * static_cast<float>(textureAtlas.height)));
    std::vector<uint8_t> regionPixels(static_cast<size_t>(textureAtlas.tileSize * textureAtlas.tileSize * 4), 0);

    for (int row = 0; row < textureAtlas.tileSize; ++row)
    {
        const size_t sourceOffset = static_cast<size_t>(((atlasY + row) * textureAtlas.width + atlasX) * 4);
        const size_t targetOffset = static_cast<size_t>(row * textureAtlas.tileSize * 4);
        std::memcpy(
            regionPixels.data() + static_cast<ptrdiff_t>(targetOffset),
            textureAtlas.pixels.data() + static_cast<ptrdiff_t>(sourceOffset),
            static_cast<size_t>(textureAtlas.tileSize * 4)
        );
    }

    return regionPixels;
}

std::vector<uint8_t> compositeOverlayPixels(
    const std::vector<uint8_t> &basePixels,
    const std::vector<uint8_t> &overlayPixels)
{
    if (basePixels.size() != overlayPixels.size())
    {
        return basePixels;
    }

    std::vector<uint8_t> compositedPixels = basePixels;

    for (size_t offset = 0; offset + 3 < compositedPixels.size(); offset += 4)
    {
        const uint32_t sourceAlpha = overlayPixels[offset + 3];

        if (sourceAlpha == 0)
        {
            continue;
        }

        if (sourceAlpha >= 255)
        {
            compositedPixels[offset + 0] = overlayPixels[offset + 0];
            compositedPixels[offset + 1] = overlayPixels[offset + 1];
            compositedPixels[offset + 2] = overlayPixels[offset + 2];
            compositedPixels[offset + 3] = 255;
            continue;
        }

        const uint32_t inverseSourceAlpha = 255 - sourceAlpha;

        for (int channel = 0; channel < 3; ++channel)
        {
            const uint32_t source = overlayPixels[offset + static_cast<size_t>(channel)];
            const uint32_t destination = compositedPixels[offset + static_cast<size_t>(channel)];
            compositedPixels[offset + static_cast<size_t>(channel)] = static_cast<uint8_t>(
                (source * sourceAlpha + destination * inverseSourceAlpha + 127) / 255);
        }

        compositedPixels[offset + 3] = 255;
    }

    return compositedPixels;
}

const SurfaceAnimationSequence *findTextureAnimationBinding(
    const std::vector<std::pair<std::string, SurfaceAnimationSequence>> &bindings,
    const std::string &textureName)
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const auto &binding : bindings)
    {
        if (binding.first == normalizedTextureName)
        {
            return &binding.second;
        }
    }

    return nullptr;
}

const OutdoorBitmapTexture *findBitmapTexture(
    const OutdoorBModelTextureSet &textureSet,
    const std::string &textureName)
{
    const std::string normalizedTextureName = toLowerCopy(textureName);

    for (const OutdoorBitmapTexture &texture : textureSet.textures)
    {
        if (toLowerCopy(texture.textureName) == normalizedTextureName)
        {
            return &texture;
        }
    }

    return nullptr;
}

size_t frameIndexForAnimation(
    const std::vector<uint32_t> &frameLengthTicks,
    uint32_t animationLengthTicks,
    uint32_t elapsedTicks)
{
    if (frameLengthTicks.empty() || frameLengthTicks.size() == 1 || animationLengthTicks == 0)
    {
        return 0;
    }

    uint32_t localTicks = elapsedTicks % animationLengthTicks;

    for (size_t frameIndex = 0; frameIndex < frameLengthTicks.size(); ++frameIndex)
    {
        const uint32_t length = frameLengthTicks[frameIndex];

        if (length == 0 || localTicks < length)
        {
            return frameIndex;
        }

        localTicks -= length;
    }

    return frameLengthTicks.size() - 1;
}

SurfaceAnimationSequence staticSurfaceAnimation(const std::string &textureName)
{
    SurfaceAnimationSequence animation = {};
    SurfaceAnimationFrame frame = {};
    frame.textureName = textureName;
    animation.frames.push_back(std::move(frame));
    return animation;
}

bool outdoorFaceHiddenByEventRuntime(
    uint32_t faceId,
    const EventRuntimeState *pEventRuntimeState)
{
    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    uint32_t mask = 0;
    const auto setIterator = pEventRuntimeState->facetSetMasks.find(faceId);

    if (setIterator != pEventRuntimeState->facetSetMasks.end())
    {
        mask |= setIterator->second;
    }

    const auto clearIterator = pEventRuntimeState->facetClearMasks.find(faceId);

    if (clearIterator != pEventRuntimeState->facetClearMasks.end())
    {
        mask &= ~clearIterator->second;
    }

    return (mask & static_cast<uint32_t>(EvtFaceAttribute::Invisible)) != 0;
}

OutdoorFogParameters buildOutdoorWorldFogParameters(
    const OutdoorWorldRuntime *pOutdoorWorldRuntime,
    const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState,
    float farClipDistance)
{
    OutdoorFogParameters parameters = {};
    const float clampedFarClipDistance = std::max(farClipDistance, 1.0f);

    if (pOutdoorWorldRuntime == nullptr)
    {
        parameters.distances = {
            clampedFarClipDistance,
            clampedFarClipDistance,
            clampedFarClipDistance + 1.0f,
            0.0f};
        return parameters;
    }

    const uint32_t skyTintAbgr = computeOutdoorSkyTintAbgr(*pOutdoorWorldRuntime);
    parameters.color = {
        static_cast<float>(skyTintAbgr & 0xffu) / 255.0f,
        static_cast<float>((skyTintAbgr >> 8) & 0xffu) / 255.0f,
        static_cast<float>((skyTintAbgr >> 16) & 0xffu) / 255.0f,
        1.0f
    };

    if (pAtmosphereState != nullptr
        && (pAtmosphereState->weatherFlags & MapWeatherFoggy) != 0
        && pAtmosphereState->fogWeakDistance > 0
        && pAtmosphereState->fogStrongDistance > 0)
    {
        const uint32_t fogColorAbgr = computeOutdoorSkyFogColorAbgr(*pAtmosphereState);
        parameters.color = {
            static_cast<float>(fogColorAbgr & 0xffu) / 255.0f,
            static_cast<float>((fogColorAbgr >> 8) & 0xffu) / 255.0f,
            static_cast<float>((fogColorAbgr >> 16) & 0xffu) / 255.0f,
            1.0f
        };
        parameters.densities = {0.25f, 0.85f, 0.0f, 0.0f};
        parameters.distances = {
            static_cast<float>(pAtmosphereState->fogWeakDistance),
            static_cast<float>(pAtmosphereState->fogStrongDistance),
            clampedFarClipDistance,
            0.0f
        };
        return parameters;
    }

    parameters.densities = {0.0f, 0.0f, 0.0f, 0.0f};
    parameters.distances = {
        clampedFarClipDistance,
        clampedFarClipDistance,
        clampedFarClipDistance,
        0.0f
    };
    return parameters;
}

OutdoorFogParameters buildOutdoorSkyFogParameters(
    const OutdoorWorldRuntime *pOutdoorWorldRuntime,
    const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState,
    float renderDistance)
{
    OutdoorFogParameters parameters = {};
    const float clampedRenderDistance = std::max(renderDistance, 1.0f);

    if (pOutdoorWorldRuntime == nullptr)
    {
        parameters.distances = {
            clampedRenderDistance,
            clampedRenderDistance,
            clampedRenderDistance + 1.0f,
            0.0f};
        return parameters;
    }

    const uint32_t skyTintAbgr = computeOutdoorSkyTintAbgr(*pOutdoorWorldRuntime);
    parameters.color = {
        static_cast<float>(skyTintAbgr & 0xffu) / 255.0f,
        static_cast<float>((skyTintAbgr >> 8) & 0xffu) / 255.0f,
        static_cast<float>((skyTintAbgr >> 16) & 0xffu) / 255.0f,
        1.0f
    };

    if (pAtmosphereState != nullptr
        && (pAtmosphereState->weatherFlags & MapWeatherFoggy) != 0
        && pAtmosphereState->fogWeakDistance > 0
        && pAtmosphereState->fogStrongDistance > 0)
    {
        const uint32_t fogColorAbgr = computeOutdoorSkyFogColorAbgr(*pAtmosphereState);
        parameters.color = {
            static_cast<float>(fogColorAbgr & 0xffu) / 255.0f,
            static_cast<float>((fogColorAbgr >> 8) & 0xffu) / 255.0f,
            static_cast<float>((fogColorAbgr >> 16) & 0xffu) / 255.0f,
            1.0f
        };
        parameters.densities = {0.25f, 0.85f, 0.0f, 0.0f};
        parameters.distances = {
            static_cast<float>(pAtmosphereState->fogWeakDistance),
            static_cast<float>(pAtmosphereState->fogStrongDistance),
            clampedRenderDistance,
            0.0f
        };
        return parameters;
    }

    parameters.densities = {0.0f, 0.0f, 0.0f, 0.0f};
    parameters.distances = {
        clampedRenderDistance,
        clampedRenderDistance,
        clampedRenderDistance,
        0.0f
    };
    return parameters;
}

void applyOutdoorFogUniforms(
    bgfx::UniformHandle fogColorUniformHandle,
    bgfx::UniformHandle fogDensitiesUniformHandle,
    bgfx::UniformHandle fogDistancesUniformHandle,
    const OutdoorFogParameters &parameters)
{
    if (!bgfx::isValid(fogColorUniformHandle)
        || !bgfx::isValid(fogDensitiesUniformHandle)
        || !bgfx::isValid(fogDistancesUniformHandle))
    {
        return;
    }

    bgfx::setUniform(fogColorUniformHandle, parameters.color.data());
    bgfx::setUniform(fogDensitiesUniformHandle, parameters.densities.data());
    bgfx::setUniform(fogDistancesUniformHandle, parameters.distances.data());
}

} // namespace

void OutdoorRenderer::applyOutdoorFxLightUniforms(OutdoorGameView &view, const bx::Vec3 &cameraPosition)
{
    if (!bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle)
        || !bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle)
        || !bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle))
    {
        return;
    }

    const bool refreshUniforms =
        view.m_lastOutdoorFxLightUniformUpdateElapsedTime < 0.0f
        || (view.m_elapsedTime - view.m_lastOutdoorFxLightUniformUpdateElapsedTime) >= OutdoorFxLightRefreshIntervalSeconds;

    if (refreshUniforms)
    {
        struct RankedLight
        {
            const OutdoorFxRuntime::LightEmitterState *pLight = nullptr;
            float score = 0.0f;
        };

        std::vector<RankedLight> rankedLights;
        rankedLights.reserve(view.m_outdoorFxRuntime.lightEmitters().size());

        for (const OutdoorFxRuntime::LightEmitterState &light : view.m_outdoorFxRuntime.lightEmitters())
        {
            if (light.radius <= 1.0f)
            {
                continue;
            }

            const float intensity = alphaChannel(light.colorAbgr);

            if (intensity <= 0.01f)
            {
                continue;
            }

            const bx::Vec3 toLight = {
                light.x - cameraPosition.x,
                light.y - cameraPosition.y,
                light.z - cameraPosition.z
            };
            const float distance = std::sqrt(bx::dot(toLight, toLight));
            const float score = (light.radius * intensity) / std::max(distance, 64.0f);
            rankedLights.push_back({&light, score});
        }

        std::sort(
            rankedLights.begin(),
            rankedLights.end(),
            [](const RankedLight &left, const RankedLight &right)
            {
                return left.score > right.score;
            });

        view.m_cachedOutdoorFxLightPositions.fill(0.0f);
        view.m_cachedOutdoorFxLightColors.fill(0.0f);
        uint32_t lightCount = 0;

        for (size_t index = 0; index < rankedLights.size() && lightCount < MaxOutdoorFxLights; ++index)
        {
            const OutdoorFxRuntime::LightEmitterState &light = *rankedLights[index].pLight;
            const size_t baseIndex = static_cast<size_t>(lightCount) * 4;

            view.m_cachedOutdoorFxLightPositions[baseIndex + 0] = light.x;
            view.m_cachedOutdoorFxLightPositions[baseIndex + 1] = light.y;
            view.m_cachedOutdoorFxLightPositions[baseIndex + 2] = light.z;
            view.m_cachedOutdoorFxLightPositions[baseIndex + 3] = light.radius;

            view.m_cachedOutdoorFxLightColors[baseIndex + 0] = redChannel(light.colorAbgr);
            view.m_cachedOutdoorFxLightColors[baseIndex + 1] = greenChannel(light.colorAbgr);
            view.m_cachedOutdoorFxLightColors[baseIndex + 2] = blueChannel(light.colorAbgr);
            view.m_cachedOutdoorFxLightColors[baseIndex + 3] = alphaChannel(light.colorAbgr);
            ++lightCount;
        }

        view.m_cachedOutdoorFxLightParams = {{
            static_cast<float>(lightCount),
            OutdoorFxLightingAmbient,
            OutdoorFxLightingScale,
            0.0f
        }};
        view.m_lastOutdoorFxLightUniformUpdateElapsedTime = view.m_elapsedTime;
    }

    bgfx::setUniform(
        view.m_outdoorFxLightPositionsUniformHandle,
        view.m_cachedOutdoorFxLightPositions.data(),
        MaxOutdoorFxLights);
    bgfx::setUniform(
        view.m_outdoorFxLightColorsUniformHandle,
        view.m_cachedOutdoorFxLightColors.data(),
        MaxOutdoorFxLights);
    bgfx::setUniform(view.m_outdoorFxLightParamsUniformHandle, view.m_cachedOutdoorFxLightParams.data());
}

void OutdoorRenderer::destroyResolvedBModelDrawGroups(OutdoorGameView &view)
{
    for (OutdoorGameView::ResolvedBModelDrawGroup &group : view.m_resolvedBModelDrawGroups)
    {
        if (bgfx::isValid(group.vertexBufferHandle))
        {
            bgfx::destroy(group.vertexBufferHandle);
            group.vertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        group.vertexCount = 0;
        group.animationIndex = static_cast<size_t>(-1);
    }

    view.m_resolvedBModelDrawGroups.clear();
    view.m_resolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();
}

void OutdoorRenderer::rebuildResolvedBModelDrawGroups(OutdoorGameView &view)
{
    destroyResolvedBModelDrawGroups(view);

    if (view.m_texturedBModelBatches.empty() || view.m_bmodelTextureAnimations.empty())
    {
        view.m_resolvedBModelDrawGroupRevision =
            view.m_pOutdoorWorldRuntime != nullptr && view.m_pOutdoorWorldRuntime->eventRuntimeState() != nullptr
                ? view.m_pOutdoorWorldRuntime->eventRuntimeState()->outdoorSurfaceRevision
                : 0;
        return;
    }

    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const uint64_t targetRevision = pEventRuntimeState != nullptr ? pEventRuntimeState->outdoorSurfaceRevision : 0;
    const std::unordered_map<uint32_t, std::string> *pTextureOverrides =
        pEventRuntimeState != nullptr ? &pEventRuntimeState->textureOverrides : nullptr;

    std::unordered_map<std::string, size_t> animationIndexByTextureName;
    animationIndexByTextureName.reserve(view.m_bmodelTextureAnimations.size());

    for (size_t animationIndex = 0; animationIndex < view.m_bmodelTextureAnimations.size(); ++animationIndex)
    {
        animationIndexByTextureName[view.m_bmodelTextureAnimations[animationIndex].textureName] = animationIndex;
    }

    std::vector<std::vector<OutdoorGameView::TexturedTerrainVertex>> verticesByAnimationIndex(
        view.m_bmodelTextureAnimations.size());

    for (const OutdoorGameView::TexturedBModelBatch &batch : view.m_texturedBModelBatches)
    {
        if (outdoorFaceHiddenByEventRuntime(batch.faceId, pEventRuntimeState))
        {
            continue;
        }

        size_t animationIndex = batch.defaultAnimationIndex;

        if (pTextureOverrides != nullptr)
        {
            const auto overrideIterator = pTextureOverrides->find(batch.cogNumber);

            if (overrideIterator != pTextureOverrides->end())
            {
                const std::string normalizedOverrideTextureName = toLowerCopy(overrideIterator->second);
                const auto animationIterator = animationIndexByTextureName.find(normalizedOverrideTextureName);

                if (animationIterator == animationIndexByTextureName.end())
                {
                    continue;
                }

                animationIndex = animationIterator->second;
            }
        }

        if (animationIndex >= verticesByAnimationIndex.size())
        {
            continue;
        }

        std::vector<OutdoorGameView::TexturedTerrainVertex> &groupVertices = verticesByAnimationIndex[animationIndex];
        groupVertices.insert(groupVertices.end(), batch.vertices.begin(), batch.vertices.end());
    }

    view.m_resolvedBModelDrawGroups.reserve(view.m_bmodelTextureAnimations.size());

    for (size_t animationIndex = 0; animationIndex < verticesByAnimationIndex.size(); ++animationIndex)
    {
        const std::vector<OutdoorGameView::TexturedTerrainVertex> &groupVertices = verticesByAnimationIndex[animationIndex];

        if (groupVertices.empty())
        {
            continue;
        }

        const bgfx::VertexBufferHandle vertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                groupVertices.data(),
                static_cast<uint32_t>(groupVertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex))),
            OutdoorGameView::TexturedTerrainVertex::ms_layout);

        if (!bgfx::isValid(vertexBufferHandle))
        {
            continue;
        }

        OutdoorGameView::ResolvedBModelDrawGroup group = {};
        group.vertexBufferHandle = vertexBufferHandle;
        group.vertexCount = static_cast<uint32_t>(groupVertices.size());
        group.animationIndex = animationIndex;
        view.m_resolvedBModelDrawGroups.push_back(group);
    }

    view.m_resolvedBModelDrawGroupRevision = targetRevision;
}

void OutdoorRenderer::initializeAnimatedWaterTileState(
    OutdoorGameView &view,
    const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas)
{
    view.m_animatedWaterTerrainTiles.clear();

    if (!outdoorTerrainTextureAtlas || outdoorTerrainTextureAtlas->animatedWaterTiles.empty())
    {
        return;
    }

    view.m_animatedWaterTerrainTiles.reserve(outdoorTerrainTextureAtlas->animatedWaterTiles.size());

    for (const OutdoorAnimatedWaterTileSource &source : outdoorTerrainTextureAtlas->animatedWaterTiles)
    {
        OutdoorGameView::AnimatedWaterTerrainTileState tileState = {};
        tileState.region = source.region;
        tileState.framePixels = source.framePixels;
        tileState.animationLengthTicks = source.animation.animationLengthTicks;
        tileState.currentFrameIndex = source.currentFrameIndex;

        for (const SurfaceAnimationFrame &frame : source.animation.frames)
        {
            tileState.frameLengthTicks.push_back(frame.frameLengthTicks);
        }

        view.m_animatedWaterTerrainTiles.push_back(std::move(tileState));
    }
}

void OutdoorRenderer::updateAnimatedWaterTileTexture(OutdoorGameView &view)
{
    if (!bgfx::isValid(view.m_terrainTextureAtlasHandle) || view.m_animatedWaterTerrainTiles.empty())
    {
        return;
    }

    const uint32_t animationTicks = static_cast<uint32_t>(std::lround(view.m_elapsedTime * 128.0f));

    for (OutdoorGameView::AnimatedWaterTerrainTileState &tileState : view.m_animatedWaterTerrainTiles)
    {
        if (tileState.framePixels.empty())
        {
            continue;
        }

        const size_t frameIndex = frameIndexForAnimation(
            tileState.frameLengthTicks,
            tileState.animationLengthTicks,
            animationTicks);

        if (frameIndex >= tileState.framePixels.size() || frameIndex == tileState.currentFrameIndex)
        {
            continue;
        }

        const std::vector<uint8_t> &framePixels = tileState.framePixels[frameIndex];
        const int tileSize = static_cast<int>(std::lround(std::sqrt(framePixels.size() / 4.0)));

        const float regionWidth = tileState.region.u1 - tileState.region.u0;
        const float regionHeight = tileState.region.v1 - tileState.region.v0;

        if (tileSize <= 0 || regionWidth <= 0.0f || regionHeight <= 0.0f)
        {
            continue;
        }

        const int atlasWidth = static_cast<int>(std::lround(static_cast<float>(tileSize) / regionWidth));
        const int atlasHeight = static_cast<int>(std::lround(static_cast<float>(tileSize) / regionHeight));

        if (atlasWidth <= 0 || atlasHeight <= 0)
        {
            continue;
        }

        const uint16_t atlasX = static_cast<uint16_t>(std::lround(tileState.region.u0 * static_cast<float>(atlasWidth)));
        const uint16_t atlasY = static_cast<uint16_t>(std::lround(tileState.region.v0 * static_cast<float>(atlasHeight)));

        bgfx::updateTexture2D(
            view.m_terrainTextureAtlasHandle,
            0,
            0,
            atlasX,
            atlasY,
            static_cast<uint16_t>(tileSize),
            static_cast<uint16_t>(tileSize),
            bgfx::copy(
                framePixels.data(),
                static_cast<uint32_t>(framePixels.size())));

        tileState.currentFrameIndex = frameIndex;
    }
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildTerrainVertices(const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    vertices.reserve(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight);

    const float minHeight = static_cast<float>(mapData.minHeightSample);
    const float maxHeight = static_cast<float>(mapData.maxHeightSample);
    const float heightRange = std::max(maxHeight - minHeight, 1.0f);

    for (int gridY = 0; gridY < OutdoorMapData::TerrainHeight; ++gridY)
    {
        for (int gridX = 0; gridX < OutdoorMapData::TerrainWidth; ++gridX)
        {
            const size_t sampleIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const float heightSample = static_cast<float>(mapData.heightMap[sampleIndex]);
            const float normalizedHeight = (heightSample - minHeight) / heightRange;
            OutdoorGameView::TerrainVertex vertex = {};
            vertex.x = outdoorGridCornerWorldX(gridX);
            vertex.y = outdoorGridCornerWorldY(gridY);
            vertex.z = heightSample * static_cast<float>(OutdoorMapData::TerrainHeightScale);
            vertex.abgr = makeAbgr(
                static_cast<uint8_t>(32.0f + normalizedHeight * 96.0f),
                static_cast<uint8_t>(96.0f + normalizedHeight * 159.0f),
                static_cast<uint8_t>(32.0f + (1.0f - normalizedHeight) * 48.0f));
            vertices.push_back(vertex);
        }
    }

    return vertices;
}

std::vector<uint16_t> OutdoorRenderer::buildTerrainIndices()
{
    std::vector<uint16_t> indices;
    indices.reserve((OutdoorMapData::TerrainWidth - 1) * (OutdoorMapData::TerrainHeight - 1) * 8);

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const uint16_t topLeft = static_cast<uint16_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint16_t topRight = static_cast<uint16_t>(topLeft + 1);
            const uint16_t bottomLeft = static_cast<uint16_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const uint16_t bottomRight = static_cast<uint16_t>(bottomLeft + 1);

            indices.push_back(topLeft);
            indices.push_back(topRight);
            indices.push_back(topRight);
            indices.push_back(bottomRight);
            indices.push_back(bottomRight);
            indices.push_back(bottomLeft);
            indices.push_back(bottomLeft);
            indices.push_back(topLeft);
        }
    }

    return indices;
}

std::vector<OutdoorGameView::TexturedTerrainVertex> OutdoorRenderer::buildTexturedTerrainVertices(
    const OutdoorMapData &mapData,
    const OutdoorTerrainTextureAtlas &textureAtlas)
{
    std::vector<OutdoorGameView::TexturedTerrainVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1)
        * 6);

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = mapData.tileMap[tileMapIndex];
            const OutdoorTerrainAtlasRegion &region = textureAtlas.tileRegions[static_cast<size_t>(rawTileId)];

            if (!region.isValid)
            {
                continue;
            }

            const size_t topLeftIndex = tileMapIndex;
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;

            OutdoorGameView::TexturedTerrainVertex topLeft = {};
            topLeft.x = outdoorGridCornerWorldX(gridX);
            topLeft.y = outdoorGridCornerWorldY(gridY);
            topLeft.z = static_cast<float>(mapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale);
            topLeft.u = region.u0;
            topLeft.v = region.v0;

            OutdoorGameView::TexturedTerrainVertex topRight = {};
            topRight.x = outdoorGridCornerWorldX(gridX + 1);
            topRight.y = outdoorGridCornerWorldY(gridY);
            topRight.z = static_cast<float>(mapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale);
            topRight.u = region.u1;
            topRight.v = region.v0;

            OutdoorGameView::TexturedTerrainVertex bottomLeft = {};
            bottomLeft.x = outdoorGridCornerWorldX(gridX);
            bottomLeft.y = outdoorGridCornerWorldY(gridY + 1);
            bottomLeft.z = static_cast<float>(mapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale);
            bottomLeft.u = region.u0;
            bottomLeft.v = region.v1;

            OutdoorGameView::TexturedTerrainVertex bottomRight = {};
            bottomRight.x = outdoorGridCornerWorldX(gridX + 1);
            bottomRight.y = outdoorGridCornerWorldY(gridY + 1);
            bottomRight.z = static_cast<float>(mapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale);
            bottomRight.u = region.u1;
            bottomRight.v = region.v1;

            vertices.push_back(topLeft);
            vertices.push_back(bottomLeft);
            vertices.push_back(topRight);
            vertices.push_back(topRight);
            vertices.push_back(bottomLeft);
            vertices.push_back(bottomRight);
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TexturedTerrainVertex> OutdoorRenderer::buildTexturedBModelFaceVertices(
    const OutdoorMapData &mapData,
    size_t bModelIndex,
    size_t faceIndex,
    int textureWidth,
    int textureHeight)
{
    std::vector<OutdoorGameView::TexturedTerrainVertex> vertices;

    if (textureWidth <= 0
        || textureHeight <= 0
        || bModelIndex >= mapData.bmodels.size()
        || faceIndex >= mapData.bmodels[bModelIndex].faces.size())
    {
        return vertices;
    }

    const OutdoorBModel &bmodel = mapData.bmodels[bModelIndex];
    const OutdoorBModelFace &face = bmodel.faces[faceIndex];

    if (face.vertexIndices.size() < 3 || face.textureName.empty())
    {
        return vertices;
    }

    for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
    {
        const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
        OutdoorGameView::TexturedTerrainVertex triangleVertices[3] = {};
        bool isTriangleValid = true;

        for (size_t triangleVertexSlot = 0; triangleVertexSlot < 3; ++triangleVertexSlot)
        {
            const size_t localTriangleVertexIndex = triangleVertexIndices[triangleVertexSlot];
            const uint16_t modelVertexIndex = face.vertexIndices[localTriangleVertexIndex];

            if (modelVertexIndex >= bmodel.vertices.size()
                || localTriangleVertexIndex >= face.textureUs.size()
                || localTriangleVertexIndex >= face.textureVs.size())
            {
                isTriangleValid = false;
                break;
            }

            const bx::Vec3 worldVertex = outdoorBModelVertexToWorld(bmodel.vertices[modelVertexIndex]);
            const float normalizedU =
                static_cast<float>(face.textureUs[localTriangleVertexIndex] + face.textureDeltaU)
                / static_cast<float>(textureWidth);
            const float normalizedV =
                static_cast<float>(face.textureVs[localTriangleVertexIndex] + face.textureDeltaV)
                / static_cast<float>(textureHeight);

            OutdoorGameView::TexturedTerrainVertex vertex = {};
            vertex.x = worldVertex.x;
            vertex.y = worldVertex.y;
            vertex.z = worldVertex.z;
            vertex.u = normalizedU;
            vertex.v = normalizedV;
            triangleVertices[triangleVertexSlot] = vertex;
        }

        if (!isTriangleValid)
        {
            continue;
        }

        for (const OutdoorGameView::TexturedTerrainVertex &vertex : triangleVertices)
        {
            vertices.push_back(vertex);
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildFilledTerrainVertices(
    const OutdoorMapData &mapData,
    const std::optional<std::vector<uint32_t>> &tileColors)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(OutdoorMapData::TerrainHeight - 1)
        * 6);

    const uint32_t fallbackColor = 0xff707070u;

    for (int gridY = 0; gridY < (OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t topLeftIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const size_t tileColorIndex = static_cast<size_t>(gridY * (OutdoorMapData::TerrainWidth - 1) + gridX);
            const uint32_t tileColor = tileColors ? (*tileColors)[tileColorIndex] : fallbackColor;

            OutdoorGameView::TerrainVertex topLeft = {};
            topLeft.x = outdoorGridCornerWorldX(gridX);
            topLeft.y = outdoorGridCornerWorldY(gridY);
            topLeft.z = static_cast<float>(mapData.heightMap[topLeftIndex] * OutdoorMapData::TerrainHeightScale);
            topLeft.abgr = tileColor;

            OutdoorGameView::TerrainVertex topRight = {};
            topRight.x = outdoorGridCornerWorldX(gridX + 1);
            topRight.y = outdoorGridCornerWorldY(gridY);
            topRight.z = static_cast<float>(mapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale);
            topRight.abgr = tileColor;

            OutdoorGameView::TerrainVertex bottomLeft = {};
            bottomLeft.x = outdoorGridCornerWorldX(gridX);
            bottomLeft.y = outdoorGridCornerWorldY(gridY + 1);
            bottomLeft.z =
                static_cast<float>(mapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale);
            bottomLeft.abgr = tileColor;

            OutdoorGameView::TerrainVertex bottomRight = {};
            bottomRight.x = outdoorGridCornerWorldX(gridX + 1);
            bottomRight.y = outdoorGridCornerWorldY(gridY + 1);
            bottomRight.z =
                static_cast<float>(mapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale);
            bottomRight.abgr = tileColor;

            vertices.push_back(topLeft);
            vertices.push_back(bottomLeft);
            vertices.push_back(topRight);
            vertices.push_back(topRight);
            vertices.push_back(bottomLeft);
            vertices.push_back(bottomRight);
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildBModelWireframeVertices(
    const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const uint32_t lineColor = makeAbgr(255, 192, 96);

    for (const OutdoorBModel &bmodel : mapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.vertexIndices.size() < 2)
            {
                continue;
            }

            for (size_t vertexIndex = 0; vertexIndex < face.vertexIndices.size(); ++vertexIndex)
            {
                const uint16_t startIndex = face.vertexIndices[vertexIndex];
                const uint16_t endIndex = face.vertexIndices[(vertexIndex + 1) % face.vertexIndices.size()];

                if (startIndex >= bmodel.vertices.size() || endIndex >= bmodel.vertices.size())
                {
                    continue;
                }

                const bx::Vec3 startVertex = outdoorBModelVertexToWorld(bmodel.vertices[startIndex]);
                const bx::Vec3 endVertex = outdoorBModelVertexToWorld(bmodel.vertices[endIndex]);

                OutdoorGameView::TerrainVertex lineStart = {};
                lineStart.x = startVertex.x;
                lineStart.y = startVertex.y;
                lineStart.z = startVertex.z;
                lineStart.abgr = lineColor;
                vertices.push_back(lineStart);

                OutdoorGameView::TerrainVertex lineEnd = {};
                lineEnd.x = endVertex.x;
                lineEnd.y = endVertex.y;
                lineEnd.z = endVertex.z;
                lineEnd.abgr = lineColor;
                vertices.push_back(lineEnd);
            }
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildBModelCollisionFaceVertices(
    const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const uint32_t walkableColor = 0x6600ff00u;
    const uint32_t blockingColor = 0x66ff0000u;

    for (const OutdoorBModel &bModel : mapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bModel.faces)
        {
            if (face.vertexIndices.size() < 3)
            {
                continue;
            }

            std::vector<bx::Vec3> polygonVertices;
            polygonVertices.reserve(face.vertexIndices.size());

            for (uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex >= bModel.vertices.size())
                {
                    polygonVertices.clear();
                    break;
                }

                polygonVertices.push_back(outdoorBModelVertexToWorld(bModel.vertices[vertexIndex]));
            }

            if (polygonVertices.size() < 3)
            {
                continue;
            }

            const uint32_t color = isOutdoorWalkablePolygonType(face.polygonType) ? walkableColor : blockingColor;

            for (size_t triangleIndex = 1; triangleIndex + 1 < polygonVertices.size(); ++triangleIndex)
            {
                const bx::Vec3 &vertex0 = polygonVertices[0];
                const bx::Vec3 &vertex1 = polygonVertices[triangleIndex];
                const bx::Vec3 &vertex2 = polygonVertices[triangleIndex + 1];

                vertices.push_back({vertex0.x, vertex0.y, vertex0.z, color});
                vertices.push_back({vertex1.x, vertex1.y, vertex1.z, color});
                vertices.push_back({vertex2.x, vertex2.y, vertex2.z, color});
            }
        }
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildEntityMarkerVertices(
    const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const uint32_t color = makeAbgr(255, 208, 64);
    const float halfExtent = 96.0f;
    const float height = 192.0f;
    vertices.reserve(mapData.entities.size() * 6);

    for (const OutdoorEntity &entity : mapData.entities)
    {
        const float centerX = static_cast<float>(entity.x);
        const float centerY = static_cast<float>(entity.y);
        const float baseZ = static_cast<float>(entity.z);

        vertices.push_back({centerX - halfExtent, centerY, baseZ + height * 0.5f, color});
        vertices.push_back({centerX + halfExtent, centerY, baseZ + height * 0.5f, color});
        vertices.push_back({centerX, centerY - halfExtent, baseZ + height * 0.5f, color});
        vertices.push_back({centerX, centerY + halfExtent, baseZ + height * 0.5f, color});
        vertices.push_back({centerX, centerY, baseZ, color});
        vertices.push_back({centerX, centerY, baseZ + height, color});
    }

    return vertices;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildSpawnMarkerVertices(
    const OutdoorMapData &mapData)
{
    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const uint32_t color = makeAbgr(96, 192, 255);
    vertices.reserve(mapData.spawns.size() * 6);

    for (const OutdoorSpawn &spawn : mapData.spawns)
    {
        const float centerX = static_cast<float>(spawn.x);
        const float centerY = static_cast<float>(spawn.y);
        const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.radius, 64));
        const float groundHeight = sampleOutdoorTerrainHeight(
            mapData,
            static_cast<float>(spawn.x),
            static_cast<float>(spawn.y));
        const int groundedZ = std::max(spawn.z, static_cast<int>(std::lround(groundHeight)));
        const float centerZ = static_cast<float>(groundedZ) + halfExtent;

        vertices.push_back({centerX - halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX + halfExtent, centerY, centerZ, color});
        vertices.push_back({centerX, centerY - halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY + halfExtent, centerZ, color});
        vertices.push_back({centerX, centerY, centerZ - halfExtent, color});
        vertices.push_back({centerX, centerY, centerZ + halfExtent, color});
    }

    return vertices;
}

bgfx::ShaderHandle OutdoorRenderer::loadShaderHandle(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        return bgfx::ShaderHandle{bgfx::kInvalidHandle};
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        std::cerr << "Failed to read shader: " << shaderPath << '\n';
        return bgfx::ShaderHandle{bgfx::kInvalidHandle};
    }

    const bgfx::Memory *pShaderMemory = bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size()));
    return bgfx::createShader(pShaderMemory);
}

bgfx::ProgramHandle OutdoorRenderer::loadProgramHandle(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadShaderHandle(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadShaderHandle(pFragmentShaderName);

    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        return bgfx::ProgramHandle{bgfx::kInvalidHandle};
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

void OutdoorRenderer::createBModelTextureBatches(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet)
{
    destroyResolvedBModelDrawGroups(view);

    if (!outdoorBModelTextureSet)
    {
        return;
    }

    for (const OutdoorBitmapTexture &texture : outdoorBModelTextureSet->textures)
    {
        OutdoorGameView::BModelTextureAnimationHandle animationHandle = {};
        animationHandle.textureName = toLowerCopy(texture.textureName);

        const SurfaceAnimationSequence *pAnimation =
            findTextureAnimationBinding(outdoorBModelTextureSet->animationBindings, texture.textureName);
        const SurfaceAnimationSequence animation =
            pAnimation != nullptr ? *pAnimation : staticSurfaceAnimation(texture.textureName);
        animationHandle.animationLengthTicks = animation.animationLengthTicks;

        for (const SurfaceAnimationFrame &frame : animation.frames)
        {
            const OutdoorBitmapTexture *pFrameTexture = findBitmapTexture(*outdoorBModelTextureSet, frame.textureName);

            if (pFrameTexture == nullptr)
            {
                continue;
            }

            const bgfx::TextureHandle textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(pFrameTexture->physicalWidth),
                static_cast<uint16_t>(pFrameTexture->physicalHeight),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
                bgfx::copy(pFrameTexture->pixels.data(), static_cast<uint32_t>(pFrameTexture->pixels.size())));

            if (!bgfx::isValid(textureHandle))
            {
                continue;
            }

            animationHandle.frameTextureHandles.push_back(textureHandle);
            animationHandle.frameLengthTicks.push_back(frame.frameLengthTicks);
        }

        if (!animationHandle.frameTextureHandles.empty())
        {
            view.m_bmodelTextureAnimations.push_back(std::move(animationHandle));
        }
    }

    std::unordered_map<std::string, size_t> animationIndexByTextureName;
    animationIndexByTextureName.reserve(view.m_bmodelTextureAnimations.size());

    for (size_t animationIndex = 0; animationIndex < view.m_bmodelTextureAnimations.size(); ++animationIndex)
    {
        animationIndexByTextureName[view.m_bmodelTextureAnimations[animationIndex].textureName] = animationIndex;
    }

    uint32_t faceId = 0;

    for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bmodel = outdoorMapData.bmodels[bModelIndex];

        for (size_t localFaceIndex = 0; localFaceIndex < bmodel.faces.size(); ++localFaceIndex, ++faceId)
        {
            const OutdoorBModelFace &face = bmodel.faces[localFaceIndex];

            if (face.textureName.empty())
            {
                continue;
            }

            const OutdoorBitmapTexture *pBaseTexture =
                findBitmapTexture(*outdoorBModelTextureSet, face.textureName);

            if (pBaseTexture == nullptr)
            {
                continue;
            }

            const std::vector<OutdoorGameView::TexturedTerrainVertex> texturedBModelVertices =
                buildTexturedBModelFaceVertices(
                    outdoorMapData,
                    bModelIndex,
                    localFaceIndex,
                    pBaseTexture->width,
                    pBaseTexture->height);

            if (texturedBModelVertices.empty())
            {
                continue;
            }

            OutdoorGameView::TexturedBModelBatch batch = {};
            batch.vertices = texturedBModelVertices;
            batch.faceId = faceId;
            batch.cogNumber = face.cogNumber;
            batch.textureName = toLowerCopy(face.textureName);
            const auto animationIndexIterator = animationIndexByTextureName.find(batch.textureName);

            if (animationIndexIterator != animationIndexByTextureName.end())
            {
                batch.defaultAnimationIndex = animationIndexIterator->second;
            }

            view.m_texturedBModelBatches.push_back(std::move(batch));
        }
    }
}

bool OutdoorRenderer::initializeWorldRenderResources(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint32_t>> &outdoorTileColors,
    const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas,
    const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet)
{
    OutdoorGameView::TerrainVertex::init();
    OutdoorGameView::TexturedTerrainVertex::init();
    OutdoorGameView::LitBillboardVertex::init();
    OutdoorGameView::ForcePerspectiveVertex::init();
    const std::vector<OutdoorGameView::TerrainVertex> vertices = buildTerrainVertices(outdoorMapData);
    const std::vector<uint16_t> indices = buildTerrainIndices();
    std::vector<OutdoorGameView::TexturedTerrainVertex> texturedTerrainVertices;
    const std::vector<OutdoorGameView::TerrainVertex> filledTerrainVertices = buildFilledTerrainVertices(
        outdoorMapData,
        outdoorTileColors);
    const std::vector<OutdoorGameView::TerrainVertex> bmodelVertices = buildBModelWireframeVertices(outdoorMapData);
    const std::vector<OutdoorGameView::TerrainVertex> bmodelCollisionVertices = buildBModelCollisionFaceVertices(
        outdoorMapData);
    const std::vector<OutdoorGameView::TerrainVertex> entityMarkerVertices =
        buildEntityMarkerVertices(outdoorMapData);
    const std::vector<OutdoorGameView::TerrainVertex> spawnMarkerVertices =
        buildSpawnMarkerVertices(outdoorMapData);

    if (outdoorTerrainTextureAtlas)
    {
        texturedTerrainVertices = buildTexturedTerrainVertices(outdoorMapData, *outdoorTerrainTextureAtlas);
    }

    initializeAnimatedWaterTileState(view, outdoorTerrainTextureAtlas);

    if (vertices.empty() || indices.empty())
    {
        std::cerr << "OutdoorGameView received empty terrain mesh.\n";
        return false;
    }

    view.m_vertexBufferHandle = bgfx::createVertexBuffer(
        bgfx::copy(
            vertices.data(),
            static_cast<uint32_t>(vertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
        OutdoorGameView::TerrainVertex::ms_layout);

    view.m_indexBufferHandle = bgfx::createIndexBuffer(
        bgfx::copy(indices.data(), static_cast<uint32_t>(indices.size() * sizeof(uint16_t))));

    if (!texturedTerrainVertices.empty())
    {
        view.m_texturedTerrainVertexBufferHandle = bgfx::createDynamicVertexBuffer(
            bgfx::copy(
                texturedTerrainVertices.data(),
                static_cast<uint32_t>(
                    texturedTerrainVertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex))),
            OutdoorGameView::TexturedTerrainVertex::ms_layout,
            BGFX_BUFFER_NONE);
    }

    if (!filledTerrainVertices.empty())
    {
        view.m_filledTerrainVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                filledTerrainVertices.data(),
                static_cast<uint32_t>(
                    filledTerrainVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
    }

    if (!bmodelVertices.empty())
    {
        view.m_bmodelVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                bmodelVertices.data(),
                static_cast<uint32_t>(bmodelVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
        view.m_bmodelLineVertexCount = static_cast<uint32_t>(bmodelVertices.size());
    }

    if (!bmodelCollisionVertices.empty())
    {
        view.m_bmodelCollisionVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                bmodelCollisionVertices.data(),
                static_cast<uint32_t>(
                    bmodelCollisionVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
        view.m_bmodelCollisionVertexCount = static_cast<uint32_t>(bmodelCollisionVertices.size());
    }

    if (!entityMarkerVertices.empty())
    {
        view.m_entityMarkerVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                entityMarkerVertices.data(),
                static_cast<uint32_t>(
                    entityMarkerVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
        view.m_entityMarkerVertexCount = static_cast<uint32_t>(entityMarkerVertices.size());
    }

    if (!spawnMarkerVertices.empty())
    {
        view.m_spawnMarkerVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                spawnMarkerVertices.data(),
                static_cast<uint32_t>(
                    spawnMarkerVertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);
        view.m_spawnMarkerVertexCount = static_cast<uint32_t>(spawnMarkerVertices.size());
    }

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        view.m_bmodelFaceCount += static_cast<uint32_t>(bmodel.faces.size());
    }

    view.m_programHandle = loadProgramHandle("vs_cubes", "fs_cubes");
    view.m_texturedTerrainProgramHandle = loadProgramHandle("vs_shadowmaps_texture", "fs_shadowmaps_texture");
    view.m_outdoorLitBillboardProgramHandle =
        loadProgramHandle("vs_outdoor_billboard_lit", "fs_outdoor_billboard_lit");
    view.m_particleProgramHandle = loadProgramHandle("vs_particle", "fs_particle");
    view.m_outdoorTexturedFogProgramHandle =
        loadProgramHandle("vs_outdoor_textured_fog", "fs_outdoor_textured_fog");
    view.m_outdoorForcePerspectiveProgramHandle =
        loadProgramHandle("vs_outdoor_force_perspective", "fs_outdoor_force_perspective");

    if (outdoorTerrainTextureAtlas && !outdoorTerrainTextureAtlas->pixels.empty())
    {
        view.m_terrainTextureAtlasHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(outdoorTerrainTextureAtlas->width),
            static_cast<uint16_t>(outdoorTerrainTextureAtlas->height),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_U_CLAMP
                | BGFX_SAMPLER_V_CLAMP
                | BGFX_SAMPLER_MIN_POINT
                | BGFX_SAMPLER_MAG_POINT
                | BGFX_TEXTURE_BLIT_DST);

        if (bgfx::isValid(view.m_terrainTextureAtlasHandle))
        {
            bgfx::updateTexture2D(
                view.m_terrainTextureAtlasHandle,
                0,
                0,
                0,
                0,
                static_cast<uint16_t>(outdoorTerrainTextureAtlas->width),
                static_cast<uint16_t>(outdoorTerrainTextureAtlas->height),
                bgfx::copy(
                    outdoorTerrainTextureAtlas->pixels.data(),
                    static_cast<uint32_t>(outdoorTerrainTextureAtlas->pixels.size())));
        }
    }

    createBModelTextureBatches(view, outdoorMapData, outdoorBModelTextureSet);

    return true;
}

const OutdoorGameView::SkyTextureHandle *OutdoorRenderer::ensureSkyTexture(
    OutdoorGameView &view,
    const std::string &textureName)
{
    if (textureName.empty())
    {
        return nullptr;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName);
    const auto cachedTextureIt = view.m_skyTextureIndexByName.find(normalizedTextureName);

    if (cachedTextureIt != view.m_skyTextureIndexByName.end() && cachedTextureIt->second < view.m_skyTextureHandles.size())
    {
        return &view.m_skyTextureHandles[cachedTextureIt->second];
    }

    const std::optional<std::string> bitmapPath = view.findCachedAssetPath("Data/bitmaps", textureName + ".bmp");

    if (!bitmapPath)
    {
        return nullptr;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = view.readCachedBinaryFile(*bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return nullptr;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return nullptr;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return nullptr;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return nullptr;
    }

    const int textureWidth = pConvertedSurface->w;
    const int textureHeight = pConvertedSurface->h;
    const size_t pixelCount = static_cast<size_t>(textureWidth) * static_cast<size_t>(textureHeight) * 4;
    std::vector<uint8_t> pixels(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);
    SDL_DestroySurface(pConvertedSurface);

    OutdoorGameView::SkyTextureHandle textureHandle = {};
    textureHandle.textureName = normalizedTextureName;
    textureHandle.width = Engine::scalePhysicalPixelsToLogical(
        textureWidth,
        view.m_pAssetFileSystem != nullptr ? view.m_pAssetFileSystem->getAssetScaleTier() : Engine::AssetScaleTier::X1);
    textureHandle.height = Engine::scalePhysicalPixelsToLogical(
        textureHeight,
        view.m_pAssetFileSystem != nullptr ? view.m_pAssetFileSystem->getAssetScaleTier() : Engine::AssetScaleTier::X1);
    textureHandle.physicalWidth = textureWidth;
    textureHandle.physicalHeight = textureHeight;
    textureHandle.bgraPixels = pixels;
    {
        const int sampleRowCount = std::max(1, std::min(textureHeight, 8));
        uint64_t blueSum = 0;
        uint64_t greenSum = 0;
        uint64_t redSum = 0;
        uint64_t sampleCount = 0;

        for (int row = textureHeight - sampleRowCount; row < textureHeight; ++row)
        {
            for (int column = 0; column < textureWidth; ++column)
            {
                const size_t pixelIndex = static_cast<size_t>((row * textureWidth + column) * 4);
                blueSum += pixels[pixelIndex + 0];
                greenSum += pixels[pixelIndex + 1];
                redSum += pixels[pixelIndex + 2];
                ++sampleCount;
            }
        }

        if (sampleCount > 0)
        {
            const uint8_t red = static_cast<uint8_t>(redSum / sampleCount);
            const uint8_t green = static_cast<uint8_t>(greenSum / sampleCount);
            const uint8_t blue = static_cast<uint8_t>(blueSum / sampleCount);
            textureHandle.horizonColorAbgr = makeAbgr(red, green, blue);
        }
    }
    textureHandle.textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(textureHandle.physicalWidth),
        static_cast<uint16_t>(textureHandle.physicalHeight),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
        bgfx::copy(pixels.data(), static_cast<uint32_t>(pixels.size())));

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        return nullptr;
    }

    view.m_skyTextureHandles.push_back(std::move(textureHandle));
    view.m_skyTextureIndexByName[view.m_skyTextureHandles.back().textureName] = view.m_skyTextureHandles.size() - 1;
    return &view.m_skyTextureHandles.back();
}

void OutdoorRenderer::invalidateSkyResources(OutdoorGameView &view)
{
    for (OutdoorGameView::SkyTextureHandle &textureHandle : view.m_skyTextureHandles)
    {
        textureHandle.textureHandle = BGFX_INVALID_HANDLE;
    }

    view.m_skyTextureHandles.clear();
    view.m_skyTextureIndexByName.clear();
}

void OutdoorRenderer::destroySkyResources(OutdoorGameView &view)
{
    for (OutdoorGameView::SkyTextureHandle &textureHandle : view.m_skyTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    invalidateSkyResources(view);
}

void OutdoorRenderer::renderWorldPasses(
    OutdoorGameView &view,
    uint16_t viewWidth,
    uint16_t viewHeight,
    float aspectRatio,
    float farClipDistance,
    const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &cameraForward,
    const bx::Vec3 &cameraRight,
    const bx::Vec3 &cameraUp,
    const float *pViewMatrix)
{
    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    const OutdoorFogParameters worldFogParameters = buildOutdoorWorldFogParameters(
        view.m_pOutdoorWorldRuntime,
        pAtmosphereState,
        farClipDistance);

    if (pAtmosphereState != nullptr)
    {
        renderOutdoorSky(
            view,
            SkyViewId,
            viewWidth,
            viewHeight,
            cameraPosition,
            cameraForward,
            cameraRight,
            cameraUp,
            farClipDistance);
    }

    {
        bgfx::setTransform(modelMatrix);

        if (view.m_showFilledTerrain && bgfx::isValid(view.m_filledTerrainVertexBufferHandle))
        {
            bgfx::setVertexBuffer(0, view.m_filledTerrainVertexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
            );
            bgfx::submit(MainViewId, view.m_programHandle);
        }

        if (view.m_showFilledTerrain
            && bgfx::isValid(view.m_texturedTerrainVertexBufferHandle)
            && bgfx::isValid(view.m_outdoorTexturedFogProgramHandle)
            && bgfx::isValid(view.m_terrainTextureAtlasHandle)
            && bgfx::isValid(view.m_terrainTextureSamplerHandle)
            && bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle)
            && bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle)
            && bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle))
        {
            updateAnimatedWaterTileTexture(view);

            bgfx::setVertexBuffer(0, view.m_texturedTerrainVertexBufferHandle);
            bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, view.m_terrainTextureAtlasHandle);
            applyOutdoorFxLightUniforms(view, cameraPosition);
            applyOutdoorFogUniforms(
                view.m_outdoorFogColorUniformHandle,
                view.m_outdoorFogDensitiesUniformHandle,
                view.m_outdoorFogDistancesUniformHandle,
                worldFogParameters);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LEQUAL
            );
            bgfx::submit(MainViewId, view.m_outdoorTexturedFogProgramHandle);
        }

        if (view.m_showTerrainWireframe)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, view.m_vertexBufferHandle);
            bgfx::setIndexBuffer(view.m_indexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_PT_LINES
            );
            bgfx::submit(MainViewId, view.m_programHandle);
        }
    }

    {
        if (view.m_showBModels
            && bgfx::isValid(view.m_bmodelVertexBufferHandle)
            && view.m_bmodelLineVertexCount > 0)
        {
            const EventRuntimeState *pEventRuntimeState =
                view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
            const uint64_t targetRevision = pEventRuntimeState != nullptr ? pEventRuntimeState->outdoorSurfaceRevision : 0;

            if (bgfx::isValid(view.m_outdoorTexturedFogProgramHandle)
                && bgfx::isValid(view.m_terrainTextureSamplerHandle)
                && bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle)
                && bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle)
                && bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle))
            {
                if (view.m_resolvedBModelDrawGroupRevision != targetRevision)
                {
                    rebuildResolvedBModelDrawGroups(view);
                }

                for (const OutdoorGameView::ResolvedBModelDrawGroup &group : view.m_resolvedBModelDrawGroups)
                {
                    if (!bgfx::isValid(group.vertexBufferHandle)
                        || group.vertexCount == 0
                        || group.animationIndex >= view.m_bmodelTextureAnimations.size())
                    {
                        continue;
                    }

                    const OutdoorGameView::BModelTextureAnimationHandle &animation =
                        view.m_bmodelTextureAnimations[group.animationIndex];

                    if (animation.frameTextureHandles.empty())
                    {
                        continue;
                    }

                    const size_t frameIndex = frameIndexForAnimation(
                        animation.frameLengthTicks,
                        animation.animationLengthTicks,
                        static_cast<uint32_t>(std::lround(view.m_elapsedTime * 128.0f)));

                    if (frameIndex >= animation.frameTextureHandles.size()
                        || !bgfx::isValid(animation.frameTextureHandles[frameIndex]))
                    {
                        continue;
                    }

                    bgfx::setTransform(modelMatrix);
                    bgfx::setVertexBuffer(0, group.vertexBufferHandle, 0, group.vertexCount);
                    bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, animation.frameTextureHandles[frameIndex]);
                    applyOutdoorFxLightUniforms(view, cameraPosition);
                    applyOutdoorFogUniforms(
                        view.m_outdoorFogColorUniformHandle,
                        view.m_outdoorFogDensitiesUniformHandle,
                        view.m_outdoorFogDistancesUniformHandle,
                        worldFogParameters);
                    bgfx::setState(
                        BGFX_STATE_WRITE_RGB
                        | BGFX_STATE_WRITE_A
                        | BGFX_STATE_WRITE_Z
                        | BGFX_STATE_DEPTH_TEST_LEQUAL
                    );
                    bgfx::submit(MainViewId, view.m_outdoorTexturedFogProgramHandle);
                }
            }

            if (view.m_showBModelWireframe)
            {
                bgfx::setTransform(modelMatrix);
                bgfx::setVertexBuffer(0, view.m_bmodelVertexBufferHandle, 0, view.m_bmodelLineVertexCount);
                bgfx::setState(
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LESS
                    | BGFX_STATE_PT_LINES
                );
                bgfx::submit(MainViewId, view.m_programHandle);
            }
        }

        if (view.m_showBModelCollisionFaces
            && bgfx::isValid(view.m_bmodelCollisionVertexBufferHandle)
            && view.m_bmodelCollisionVertexCount > 0)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(
                0,
                view.m_bmodelCollisionVertexBufferHandle,
                0,
                view.m_bmodelCollisionVertexCount);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_BLEND_ALPHA
            );
            bgfx::submit(MainViewId, view.m_programHandle);
        }
    }

    if (view.m_showEntities
        && bgfx::isValid(view.m_entityMarkerVertexBufferHandle)
        && view.m_entityMarkerVertexCount > 0)
    {
        bgfx::setTransform(modelMatrix);
        bgfx::setVertexBuffer(0, view.m_entityMarkerVertexBufferHandle, 0, view.m_entityMarkerVertexCount);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | BGFX_STATE_WRITE_Z
            | BGFX_STATE_DEPTH_TEST_LEQUAL
            | BGFX_STATE_PT_LINES
        );
        bgfx::submit(MainViewId, view.m_programHandle);
    }

    if (view.m_showSpriteObjects || view.m_showActors)
    {
        OutdoorBillboardRenderer::renderFxContactShadows(view, MainViewId);
    }

    if (view.m_showActors || view.m_showDecorationBillboards)
    {
        OutdoorBillboardRenderer::renderActorPreviewBillboards(view, MainViewId, pViewMatrix, cameraPosition);

        if (view.m_showActors && view.m_showActorCollisionBoxes)
        {
            renderActorCollisionOverlays(view, MainViewId, cameraPosition);
        }
    }

    if (view.m_showSpriteObjects)
    {
        OutdoorBillboardRenderer::renderRuntimeWorldItems(view, MainViewId, pViewMatrix, cameraPosition);
        OutdoorBillboardRenderer::renderRuntimeProjectiles(view, MainViewId, pViewMatrix, cameraPosition);
        OutdoorBillboardRenderer::renderSpriteObjectBillboards(view, MainViewId, pViewMatrix, cameraPosition);
    }

    if (view.m_showSpriteObjects || view.m_showActors || view.m_showDecorationBillboards)
    {
        OutdoorBillboardRenderer::renderFxGlowBillboards(view, MainViewId, pViewMatrix);
    }

    {
        if (view.m_showSpawns
            && bgfx::isValid(view.m_spawnMarkerVertexBufferHandle)
            && view.m_spawnMarkerVertexCount > 0)
        {
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, view.m_spawnMarkerVertexBufferHandle, 0, view.m_spawnMarkerVertexCount);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_PT_LINES
            );
            bgfx::submit(MainViewId, view.m_programHandle);
        }
    }

    if (view.m_showSpriteObjects || view.m_showActors || view.m_showDecorationBillboards)
    {
        ParticleRenderer::renderParticles(view, MainViewId, pViewMatrix, cameraPosition, aspectRatio);
    }

    if (pAtmosphereState != nullptr && pAtmosphereState->darknessOverlayAlpha > 0.001f)
    {
        renderOutdoorDarknessOverlay(
            view,
            MainViewId,
            cameraPosition,
            cameraForward,
            cameraRight,
            cameraUp,
            aspectRatio,
            pAtmosphereState->darknessOverlayAlpha,
            pAtmosphereState->darknessOverlayColorAbgr);
    }
}

void OutdoorRenderer::renderOutdoorSky(
    OutdoorGameView &view,
    uint16_t viewId,
    uint16_t viewWidth,
    uint16_t viewHeight,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &cameraForward,
    const bx::Vec3 &cameraRight,
    const bx::Vec3 &cameraUp,
    float renderDistance)
{
    (void)cameraRight;
    (void)cameraUp;

    if (!bgfx::isValid(view.m_outdoorForcePerspectiveProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle))
    {
        return;
    }

    const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState =
        view.m_pOutdoorWorldRuntime != nullptr ? &view.m_pOutdoorWorldRuntime->atmosphereState() : nullptr;
    const bool hasAtmosphericFog =
        pAtmosphereState != nullptr
        && (pAtmosphereState->weatherFlags & MapWeatherFoggy) != 0
        && pAtmosphereState->fogWeakDistance > 0
        && pAtmosphereState->fogStrongDistance > 0;

    if (pAtmosphereState == nullptr)
    {
        return;
    }

    const OutdoorGameView::SkyTextureHandle *pTexture = ensureSkyTexture(view, pAtmosphereState->skyTextureName);

    if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle) || viewWidth == 0 || viewHeight == 0)
    {
        return;
    }

    if (hasAtmosphericFog && !bgfx::isValid(view.m_forcePerspectiveSolidTextureHandle))
    {
        const uint32_t whitePixel = 0xffffffffu;
        view.m_forcePerspectiveSolidTextureHandle = bgfx::createTexture2D(
            1,
            1,
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
            bgfx::copy(&whitePixel, sizeof(whitePixel)));
    }

    const uint32_t vertexCount = 6;
    const float cameraPitchRadians =
        std::atan2(cameraForward.z, std::sqrt(cameraForward.x * cameraForward.x + cameraForward.y * cameraForward.y));
    const float cameraYawRadians = std::atan2(cameraForward.y, cameraForward.x);
    const float viewPlaneDistancePixels =
        (static_cast<float>(viewHeight) * 0.5f) / std::tan((CameraVerticalFovDegrees * Pi / 180.0f) * 0.5f);
    const float viewportCenterY = static_cast<float>(viewHeight) * 0.5f;
    const float oeViewPitchRadians = -cameraPitchRadians;
    const float depthToFarClip = std::cos(oeViewPitchRadians) * renderDistance;
    const float heightToFarClip = std::sin(oeViewPitchRadians) * renderDistance;
    float skyBottomY = static_cast<float>(viewHeight);

    if (depthToFarClip > 0.0001f)
    {
        skyBottomY =
            viewportCenterY
            - viewPlaneDistancePixels / depthToFarClip * (heightToFarClip - cameraPosition.z)
            + 1.0f;
    }
    skyBottomY = std::clamp(skyBottomY, 1.0f, static_cast<float>(viewHeight));

    if (!bgfx::isValid(view.m_skyVertexBufferHandle))
    {
        view.m_skyVertexBufferHandle = bgfx::createDynamicVertexBuffer(
            vertexCount,
            OutdoorGameView::ForcePerspectiveVertex::ms_layout,
            BGFX_BUFFER_NONE
        );
    }

    const OutdoorFogParameters skyFogParameters =
        buildOutdoorSkyFogParameters(view.m_pOutdoorWorldRuntime, pAtmosphereState, renderDistance);

    if (!bgfx::isValid(view.m_skyVertexBufferHandle))
    {
        return;
    }

    if (view.m_cachedSkyVertices.size() != vertexCount)
    {
        view.m_cachedSkyVertices.resize(vertexCount);
    }

    const OutdoorSkyVertex topLeft = computeOutdoorSkyVertex(
        0.0f,
        0.0f,
        static_cast<float>(viewWidth),
        static_cast<float>(viewHeight),
        cameraPosition.z,
        cameraYawRadians,
        cameraPitchRadians,
        renderDistance,
        view.m_elapsedTime,
        static_cast<float>(pTexture->physicalWidth),
        static_cast<float>(pTexture->physicalHeight));
    const OutdoorSkyVertex bottomLeft = computeOutdoorSkyVertex(
        0.0f,
        skyBottomY,
        static_cast<float>(viewWidth),
        static_cast<float>(viewHeight),
        cameraPosition.z,
        cameraYawRadians,
        cameraPitchRadians,
        renderDistance,
        view.m_elapsedTime,
        static_cast<float>(pTexture->physicalWidth),
        static_cast<float>(pTexture->physicalHeight));
    const OutdoorSkyVertex bottomRight = computeOutdoorSkyVertex(
        static_cast<float>(viewWidth - 1),
        skyBottomY,
        static_cast<float>(viewWidth),
        static_cast<float>(viewHeight),
        cameraPosition.z,
        cameraYawRadians,
        cameraPitchRadians,
        renderDistance,
        view.m_elapsedTime,
        static_cast<float>(pTexture->physicalWidth),
        static_cast<float>(pTexture->physicalHeight));
    const OutdoorSkyVertex topRight = computeOutdoorSkyVertex(
        static_cast<float>(viewWidth - 1),
        0.0f,
        static_cast<float>(viewWidth),
        static_cast<float>(viewHeight),
        cameraPosition.z,
        cameraYawRadians,
        cameraPitchRadians,
        renderDistance,
        view.m_elapsedTime,
        static_cast<float>(pTexture->physicalWidth),
        static_cast<float>(pTexture->physicalHeight));
    const uint32_t skyTintAbgr =
        view.m_pOutdoorWorldRuntime != nullptr ? computeOutdoorSkyTintAbgr(*view.m_pOutdoorWorldRuntime) : 0xffffffffu;
    view.m_cachedSkyVertices[0] = {
        topLeft.screenX, topLeft.screenY, 1.0f, topLeft.u, topLeft.v, 1.0f, renderDistance, topLeft.reciprocalW, skyTintAbgr};
    view.m_cachedSkyVertices[1] = {
        bottomLeft.screenX,
        bottomLeft.screenY,
        1.0f,
        bottomLeft.u,
        bottomLeft.v,
        1.0f,
        renderDistance,
        bottomLeft.reciprocalW,
        skyTintAbgr};
    view.m_cachedSkyVertices[2] = {
        bottomRight.screenX,
        bottomRight.screenY,
        1.0f,
        bottomRight.u,
        bottomRight.v,
        1.0f,
        renderDistance,
        bottomRight.reciprocalW,
        skyTintAbgr
    };
    view.m_cachedSkyVertices[3] = {
        topLeft.screenX, topLeft.screenY, 1.0f, topLeft.u, topLeft.v, 1.0f, renderDistance, topLeft.reciprocalW, skyTintAbgr};
    view.m_cachedSkyVertices[4] = {
        bottomRight.screenX,
        bottomRight.screenY,
        1.0f,
        bottomRight.u,
        bottomRight.v,
        1.0f,
        renderDistance,
        bottomRight.reciprocalW,
        skyTintAbgr
    };
    view.m_cachedSkyVertices[5] = {
        topRight.screenX, topRight.screenY, 1.0f, topRight.u, topRight.v, 1.0f, renderDistance, topRight.reciprocalW, skyTintAbgr};

    bgfx::update(
        view.m_skyVertexBufferHandle,
        0,
        bgfx::copy(
            view.m_cachedSkyVertices.data(),
            static_cast<uint32_t>(
                view.m_cachedSkyVertices.size() * sizeof(OutdoorGameView::ForcePerspectiveVertex))
        )
    );
    view.m_lastSkyUpdateElapsedTime = view.m_elapsedTime;
    view.m_cachedSkyTextureName = pTexture->textureName;

    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(viewWidth),
        static_cast<float>(viewHeight),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth
    );
    bgfx::setViewTransform(viewId, nullptr, projectionMatrix);

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, view.m_skyVertexBufferHandle, 0, vertexCount);
    bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, pTexture->textureHandle);
    applyOutdoorFogUniforms(
        view.m_outdoorFogColorUniformHandle,
        view.m_outdoorFogDensitiesUniformHandle,
        view.m_outdoorFogDistancesUniformHandle,
        skyFogParameters);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, view.m_outdoorForcePerspectiveProgramHandle);

    if (hasAtmosphericFog && bgfx::isValid(view.m_forcePerspectiveSolidTextureHandle))
    {
        const float lowerSkyTopY = std::max(skyBottomY - SkyFogHorizonPixels, 0.0f);
        const uint32_t transparentSkyTintAbgr = withAlpha(skyTintAbgr, 0);
        const uint32_t opaqueSkyTintAbgr = withAlpha(skyTintAbgr, 255);
        const uint32_t lowerSkyVertexCount = 12u;

        if (bgfx::getAvailTransientVertexBuffer(lowerSkyVertexCount, OutdoorGameView::ForcePerspectiveVertex::ms_layout)
            >= lowerSkyVertexCount)
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                lowerSkyVertexCount,
                OutdoorGameView::ForcePerspectiveVertex::ms_layout);
            OutdoorGameView::ForcePerspectiveVertex *pVertices =
                reinterpret_cast<OutdoorGameView::ForcePerspectiveVertex *>(transientVertexBuffer.data);

            pVertices[0] = {
                0.0f,
                0.0f,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                transparentSkyTintAbgr};
            pVertices[1] = {
                0.0f,
                lowerSkyTopY,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[2] = {
                static_cast<float>(viewWidth - 1),
                lowerSkyTopY,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[3] = {
                0.0f,
                0.0f,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                transparentSkyTintAbgr};
            pVertices[4] = {
                static_cast<float>(viewWidth - 1),
                lowerSkyTopY,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[5] = {
                static_cast<float>(viewWidth - 1),
                0.0f,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                transparentSkyTintAbgr};

            const uint32_t subSkyOffset = 6u;
            pVertices[subSkyOffset + 0] = {
                0.0f,
                lowerSkyTopY,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[subSkyOffset + 1] = {
                0.0f,
                static_cast<float>(viewHeight),
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[subSkyOffset + 2] = {
                static_cast<float>(viewWidth - 1),
                static_cast<float>(viewHeight),
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[subSkyOffset + 3] = {
                0.0f,
                lowerSkyTopY,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[subSkyOffset + 4] = {
                static_cast<float>(viewWidth - 1),
                static_cast<float>(viewHeight),
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[subSkyOffset + 5] = {
                static_cast<float>(viewWidth - 1),
                lowerSkyTopY,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};

            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, lowerSkyVertexCount);
            bgfx::setTexture(0, view.m_terrainTextureSamplerHandle, view.m_forcePerspectiveSolidTextureHandle);
            applyOutdoorFogUniforms(
                view.m_outdoorFogColorUniformHandle,
                view.m_outdoorFogDensitiesUniformHandle,
                view.m_outdoorFogDistancesUniformHandle,
                skyFogParameters);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(viewId, view.m_outdoorForcePerspectiveProgramHandle);
        }
    }
}

void OutdoorRenderer::renderOutdoorDarknessOverlay(
    OutdoorGameView &view,
    uint16_t viewId,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &cameraForward,
    const bx::Vec3 &cameraRight,
    const bx::Vec3 &cameraUp,
    float aspectRatio,
    float overlayAlpha,
    uint32_t overlayColorAbgr)
{
    if (!bgfx::isValid(view.m_programHandle) || overlayAlpha <= 0.0f)
    {
        return;
    }

    const float planeDistance = 1.0f;
    const float planeHalfHeight = std::tan(bx::toRad(CameraVerticalFovDegrees * 0.5f)) * planeDistance;
    const float planeHalfWidth = planeHalfHeight * std::max(aspectRatio, 0.1f);
    const bx::Vec3 overlayCenter = {
        cameraPosition.x + cameraForward.x * planeDistance,
        cameraPosition.y + cameraForward.y * planeDistance,
        cameraPosition.z + cameraForward.z * planeDistance
    };
    const bx::Vec3 planeRight = {
        cameraRight.x * planeHalfWidth,
        cameraRight.y * planeHalfWidth,
        cameraRight.z * planeHalfWidth
    };
    const bx::Vec3 planeUp = {
        cameraUp.x * planeHalfHeight,
        cameraUp.y * planeHalfHeight,
        cameraUp.z * planeHalfHeight
    };
    const uint8_t alpha = static_cast<uint8_t>(std::clamp(std::lround(overlayAlpha * 255.0f), 0l, 255l));
    const uint32_t abgr = (overlayColorAbgr & 0x00ffffffu) | (static_cast<uint32_t>(alpha) << 24);
    const std::array<OutdoorGameView::TerrainVertex, 6> vertices = {{
        {overlayCenter.x - planeRight.x + planeUp.x, overlayCenter.y - planeRight.y + planeUp.y, overlayCenter.z - planeRight.z + planeUp.z, abgr},
        {overlayCenter.x - planeRight.x - planeUp.x, overlayCenter.y - planeRight.y - planeUp.y, overlayCenter.z - planeRight.z - planeUp.z, abgr},
        {overlayCenter.x + planeRight.x - planeUp.x, overlayCenter.y + planeRight.y - planeUp.y, overlayCenter.z + planeRight.z - planeUp.z, abgr},
        {overlayCenter.x - planeRight.x + planeUp.x, overlayCenter.y - planeRight.y + planeUp.y, overlayCenter.z - planeRight.z + planeUp.z, abgr},
        {overlayCenter.x + planeRight.x - planeUp.x, overlayCenter.y + planeRight.y - planeUp.y, overlayCenter.z + planeRight.z - planeUp.z, abgr},
        {overlayCenter.x + planeRight.x + planeUp.x, overlayCenter.y + planeRight.y + planeUp.y, overlayCenter.z + planeRight.z + planeUp.z, abgr}
    }};

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, OutdoorGameView::TerrainVertex::ms_layout);
    std::memcpy(transientVertexBuffer.data, vertices.data(), sizeof(vertices));

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, 6);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, view.m_programHandle);
}

void OutdoorRenderer::renderActorCollisionOverlays(
    OutdoorGameView &view,
    uint16_t viewId,
    const bx::Vec3 &cameraPosition)
{
    if (!view.m_showActorCollisionBoxes
        || (!view.m_outdoorActorPreviewBillboardSet && view.m_pOutdoorWorldRuntime == nullptr))
    {
        return;
    }

    std::vector<OutdoorGameView::TerrainVertex> vertices;
    const size_t billboardCount =
        view.m_outdoorActorPreviewBillboardSet ? view.m_outdoorActorPreviewBillboardSet->billboards.size() : 0;
    const size_t runtimeActorCount =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapActorCount() : 0;
    vertices.reserve((billboardCount + runtimeActorCount) * 24);
    std::vector<bool> coveredRuntimeActors;

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        coveredRuntimeActors.assign(view.m_pOutdoorWorldRuntime->mapActorCount(), false);
    }

    const auto appendLine =
        [&vertices](const bx::Vec3 &start, const bx::Vec3 &end, uint32_t color)
        {
            vertices.push_back({start.x, start.y, start.z, color});
            vertices.push_back({end.x, end.y, end.z, color});
        };

    const auto appendActorOverlay =
        [&view, &appendLine](
            int actorX,
            int actorY,
            int actorZ,
            uint16_t actorRadius,
            uint16_t actorHeight,
            bool isDead,
            bool hostileToParty)
        {
            const uint32_t color = hostileToParty ? 0xff6060ffu : 0xff60ff60u;
            const uint32_t centerColor = 0xff40ffffu;
            const float halfExtent = static_cast<float>(std::max<uint16_t>(actorRadius, 32));
            const float height = static_cast<float>(std::max<uint16_t>(actorHeight, 64));
            const float minX = static_cast<float>(actorX) - halfExtent;
            const float maxX = static_cast<float>(actorX) + halfExtent;
            const float minY = static_cast<float>(actorY) - halfExtent;
            const float maxY = static_cast<float>(actorY) + halfExtent;
            const float minZ = view.m_outdoorMapData.has_value()
                ? resolveActorAabbBaseZ(
                    *view.m_outdoorMapData,
                    nullptr,
                    actorX,
                    actorY,
                    actorZ,
                    isDead)
                : static_cast<float>(actorZ);
            const float maxZ = minZ + height;

            const bx::Vec3 bottom00 = {minX, minY, minZ};
            const bx::Vec3 bottom01 = {minX, maxY, minZ};
            const bx::Vec3 bottom10 = {maxX, minY, minZ};
            const bx::Vec3 bottom11 = {maxX, maxY, minZ};
            const bx::Vec3 top00 = {minX, minY, maxZ};
            const bx::Vec3 top01 = {minX, maxY, maxZ};
            const bx::Vec3 top10 = {maxX, minY, maxZ};
            const bx::Vec3 top11 = {maxX, maxY, maxZ};

            appendLine(bottom00, bottom01, color);
            appendLine(bottom01, bottom11, color);
            appendLine(bottom11, bottom10, color);
            appendLine(bottom10, bottom00, color);
            appendLine(top00, top01, color);
            appendLine(top01, top11, color);
            appendLine(top11, top10, color);
            appendLine(top10, top00, color);
            appendLine(bottom00, top00, color);
            appendLine(bottom01, top01, color);
            appendLine(bottom10, top10, color);
            appendLine(bottom11, top11, color);
            appendLine(
                {static_cast<float>(actorX), static_cast<float>(actorY), minZ},
                {static_cast<float>(actorX), static_cast<float>(actorY), maxZ},
                centerColor);
            appendLine(
                {minX, static_cast<float>(actorY), minZ},
                {maxX, static_cast<float>(actorY), minZ},
                centerColor);
            appendLine(
                {static_cast<float>(actorX), minY, minZ},
                {static_cast<float>(actorX), maxY, minZ},
                centerColor);
        };

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        for (const ActorPreviewBillboard &billboard : view.m_outdoorActorPreviewBillboardSet->billboards)
        {
            if (billboard.source != ActorPreviewSource::Companion)
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = OutdoorInteractionController::runtimeActorStateForBillboard(view, billboard);

            if (pRuntimeActor != nullptr && billboard.runtimeActorIndex < coveredRuntimeActors.size())
            {
                coveredRuntimeActors[billboard.runtimeActorIndex] = true;
            }

            if (pRuntimeActor != nullptr && pRuntimeActor->isInvisible)
            {
                continue;
            }

            const float overlayDeltaX =
                static_cast<float>(pRuntimeActor != nullptr ? pRuntimeActor->x : billboard.x) - cameraPosition.x;
            const float overlayDeltaY =
                static_cast<float>(pRuntimeActor != nullptr ? pRuntimeActor->y : billboard.y) - cameraPosition.y;
            const float overlayDeltaZ =
                static_cast<float>(pRuntimeActor != nullptr ? pRuntimeActor->z : billboard.z) - cameraPosition.z;
            const float overlayDistanceSquared =
                overlayDeltaX * overlayDeltaX + overlayDeltaY * overlayDeltaY + overlayDeltaZ * overlayDeltaZ;

            if (overlayDistanceSquared > ActorBillboardRenderDistanceSquared)
            {
                continue;
            }

            appendActorOverlay(
                pRuntimeActor != nullptr ? pRuntimeActor->x : billboard.x,
                pRuntimeActor != nullptr ? pRuntimeActor->y : billboard.y,
                pRuntimeActor != nullptr ? pRuntimeActor->z : billboard.z,
                pRuntimeActor != nullptr ? pRuntimeActor->radius : billboard.radius,
                pRuntimeActor != nullptr ? pRuntimeActor->height : billboard.height,
                pRuntimeActor != nullptr ? pRuntimeActor->isDead : false,
                pRuntimeActor != nullptr ? pRuntimeActor->hostileToParty : !billboard.isFriendly);
        }
    }

    if (view.m_pOutdoorWorldRuntime != nullptr)
    {
        for (size_t actorIndex = 0; actorIndex < view.m_pOutdoorWorldRuntime->mapActorCount(); ++actorIndex)
        {
            if (actorIndex < coveredRuntimeActors.size() && coveredRuntimeActors[actorIndex])
            {
                continue;
            }

            const OutdoorWorldRuntime::MapActorState *pRuntimeActor = view.m_pOutdoorWorldRuntime->mapActorState(actorIndex);

            if (pRuntimeActor == nullptr || pRuntimeActor->isInvisible)
            {
                continue;
            }

            const float overlayDeltaX = static_cast<float>(pRuntimeActor->x) - cameraPosition.x;
            const float overlayDeltaY = static_cast<float>(pRuntimeActor->y) - cameraPosition.y;
            const float overlayDeltaZ = static_cast<float>(pRuntimeActor->z) - cameraPosition.z;
            const float overlayDistanceSquared =
                overlayDeltaX * overlayDeltaX + overlayDeltaY * overlayDeltaY + overlayDeltaZ * overlayDeltaZ;

            if (overlayDistanceSquared > ActorBillboardRenderDistanceSquared)
            {
                continue;
            }

            appendActorOverlay(
                pRuntimeActor->x,
                pRuntimeActor->y,
                pRuntimeActor->z,
                pRuntimeActor->radius,
                pRuntimeActor->height,
                pRuntimeActor->isDead,
                pRuntimeActor->hostileToParty);
        }
    }

    if (vertices.empty())
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
        OutdoorGameView::TerrainVertex::ms_layout
    );
    std::memcpy(
        transientVertexBuffer.data,
        vertices.data(),
        static_cast<size_t>(vertices.size() * sizeof(OutdoorGameView::TerrainVertex))
    );

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
    bgfx::setState(
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_WRITE_Z
        | BGFX_STATE_DEPTH_TEST_LEQUAL
        | BGFX_STATE_PT_LINES
        | BGFX_STATE_LINEAA
    );
    bgfx::submit(viewId, view.m_programHandle);
}

} // namespace OpenYAMM::Game
