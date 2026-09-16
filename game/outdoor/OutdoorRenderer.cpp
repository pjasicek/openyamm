#include "game/outdoor/OutdoorRenderer.h"

#include "game/app/GameSession.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/ui/GameplaySpellTargetingOverlayRenderer.h"
#include "game/outdoor/OutdoorBillboardRenderer.h"
#include "game/outdoor/OutdoorFogProfile.h"
#include "game/outdoor/OutdoorSunlight.h"
#include "game/fx/ParticleRenderer.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorLightingRuntime.h"
#include "game/outdoor/OutdoorMechanismRuntime.h"
#include "game/render/TextureFiltering.h"
#include "game/render/ViewFrustum.h"
#include "game/StringUtils.h"
#include "engine/ImageAssetLoader.h"

#include <bx/math.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <tuple>
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
constexpr float SkyProjectionPitchOffsetRadians = Pi / 64.0f;
constexpr float SkyFogHorizonPixels = 39.0f;
constexpr int32_t MapWeatherFoggy = 1;
constexpr float OutdoorFxLightRefreshIntervalSeconds = 1.0f / 60.0f;
constexpr float OutdoorTerrainChunkWorldSize = 4096.0f;

bool sameWorldFxLightEmitter(const WorldFxLightEmitter &left, const WorldFxLightEmitter &right)
{
    return left.x == right.x && left.y == right.y && left.z == right.z && left.radius == right.radius &&
           left.colorAbgr == right.colorAbgr && left.intensity == right.intensity && left.sectorId == right.sectorId &&
           left.kind == right.kind && left.stableId == right.stableId && left.important == right.important;
}

bool sameWorldFxLightEmitters(const std::vector<WorldFxLightEmitter> &left,
                              const std::vector<WorldFxLightEmitter> &right)
{
    if (left.size() != right.size())
    {
        return false;
    }

    for (size_t index = 0; index < left.size(); ++index)
    {
        if (!sameWorldFxLightEmitter(left[index], right[index]))
        {
            return false;
        }
    }

    return true;
}
constexpr float OutdoorUnderwaterTintOpacity = 0.28f;
constexpr uint8_t UnderwaterFogRed = 33;
constexpr uint8_t UnderwaterFogGreen = 142;
constexpr uint8_t UnderwaterFogBlue = 90;
constexpr size_t SpellAreaPreviewGridResolution = 24;
constexpr float SpellAreaPreviewRefreshIntervalSeconds = 1.0f / 30.0f;
constexpr float SpellAreaPreviewRetargetDistance = 72.0f;
constexpr float OutdoorWorldFogNearOpacity = 0.04f;
constexpr float OutdoorWorldFogStrongOpacity = 176.0f / 255.0f;
constexpr float OutdoorSkyFogNearOpacity = 0.02f;
constexpr float OutdoorSkyFogStrongOpacity = 208.0f / 255.0f;

bool outdoorActorIsPartyControlled(OutdoorWorldRuntime::ActorControlMode mode)
{
    switch (mode)
    {
    case OutdoorWorldRuntime::ActorControlMode::Charm:
    case OutdoorWorldRuntime::ActorControlMode::Enslaved:
    case OutdoorWorldRuntime::ActorControlMode::ControlUndead:
    case OutdoorWorldRuntime::ActorControlMode::Reanimated:
        return true;

    default:
        return false;
    }
}

float secretFaceVertexValue(uint32_t attributes, int perceptionDifficulty = -1)
{
    if (!hasFaceAttribute(attributes, FaceAttribute::IsSecret))
    {
        return 0.0f;
    }

    return perceptionDifficulty >= 0 ? static_cast<float>(perceptionDifficulty + 2) : 1.0f;
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

uint32_t makeAbgrAlpha(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

uint32_t contextActionGeometryHighlightColor(float elapsedTime)
{
    const float pulse = 0.5f + 0.5f * std::sin(elapsedTime * 4.0f);
    const uint8_t alpha = static_cast<uint8_t>(std::clamp(std::lround(52.0f + pulse * 52.0f), 0l, 255l));
    return makeAbgrAlpha(56, 216, 255, alpha);
}

float contextHighlightVecLength(const bx::Vec3 &value)
{
    return std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
}

uint64_t averageNanoseconds(uint64_t totalNanoseconds, uint64_t count)
{
    return count == 0 ? 0 : totalNanoseconds / count;
}

uint64_t nanosecondsToMicroseconds(uint64_t nanoseconds)
{
    return nanoseconds / 1000;
}

bx::Vec3 contextHighlightVecNormalize(const bx::Vec3 &value)
{
    const float length = contextHighlightVecLength(value);

    if (length <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {value.x / length, value.y / length, value.z / length};
}

const GameplayWorldHit *selectedContextActionWorldHit(const GameplayContextActionState &state)
{
    if (!state.visible || state.primaryIndex >= state.actions.size())
    {
        return nullptr;
    }

    const GameplayWorldHit &hit = state.actions[state.primaryIndex].worldHit;
    return hit.hasHit ? &hit : nullptr;
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

bool outdoorFaceHasInvisibleAttribute(uint32_t attributes)
{
    return hasFaceAttribute(attributes, FaceAttribute::Invisible);
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

template <typename TexturedVertex>
OutdoorLightSelectionBounds boundsFromTexturedVertices(const std::vector<TexturedVertex> &vertices)
{
    OutdoorLightSelectionBounds bounds = {};

    if (vertices.empty())
    {
        return bounds;
    }

    bounds.min = {vertices.front().x, vertices.front().y, vertices.front().z};
    bounds.max = bounds.min;

    for (const TexturedVertex &vertex : vertices)
    {
        bounds.min.x = std::min(bounds.min.x, vertex.x);
        bounds.min.y = std::min(bounds.min.y, vertex.y);
        bounds.min.z = std::min(bounds.min.z, vertex.z);
        bounds.max.x = std::max(bounds.max.x, vertex.x);
        bounds.max.y = std::max(bounds.max.y, vertex.y);
        bounds.max.z = std::max(bounds.max.z, vertex.z);
    }

    bounds.valid = true;
    return bounds;
}

OutdoorLightSelectionBounds boundsFromBloodSplats(const OutdoorWorldRuntime &worldRuntime)
{
    OutdoorLightSelectionBounds bounds = {};

    const auto extendBounds =
        [&bounds](float x, float y, float z)
        {
            if (!bounds.valid)
            {
                bounds.min = {x, y, z};
                bounds.max = bounds.min;
                bounds.valid = true;
                return;
            }

            bounds.min.x = std::min(bounds.min.x, x);
            bounds.min.y = std::min(bounds.min.y, y);
            bounds.min.z = std::min(bounds.min.z, z);
            bounds.max.x = std::max(bounds.max.x, x);
            bounds.max.y = std::max(bounds.max.y, y);
            bounds.max.z = std::max(bounds.max.z, z);
        };

    for (size_t splatIndex = 0; splatIndex < worldRuntime.bloodSplatCount(); ++splatIndex)
    {
        const OutdoorWorldRuntime::BloodSplatState *pSplat = worldRuntime.bloodSplatState(splatIndex);

        if (pSplat == nullptr)
        {
            continue;
        }

        if (pSplat->vertices.empty())
        {
            const float radius = std::max(pSplat->radius, 1.0f);
            extendBounds(pSplat->x - radius, pSplat->y - radius, pSplat->z - radius);
            extendBounds(pSplat->x + radius, pSplat->y + radius, pSplat->z + radius);
            continue;
        }

        for (const OutdoorWorldRuntime::BloodSplatState::Vertex &vertex : pSplat->vertices)
        {
            extendBounds(vertex.x, vertex.y, vertex.z);
        }
    }

    return bounds;
}

uint32_t stableOutdoorTerrainChunkId(int32_t cellX, int32_t cellY)
{
    uint32_t hash = 2166136261u;
    hash ^= static_cast<uint32_t>(cellX);
    hash *= 16777619u;
    hash ^= static_cast<uint32_t>(cellY);
    hash *= 16777619u;
    return hash != 0 ? hash : 1u;
}

int32_t outdoorTerrainChunkCell(float value)
{
    return static_cast<int32_t>(std::floor(value / OutdoorTerrainChunkWorldSize));
}

OutdoorSelectedFxLights selectOutdoorFxLightsForBounds(
    const OutdoorLightingRuntime &lightingRuntime,
    LightingStats *pLightingStats,
    const bx::Vec3 &fallbackReferencePosition,
    const OutdoorLightSelectionBounds &bounds)
{
    const uint64_t selectionBeginTickCount = pLightingStats != nullptr ? SDL_GetTicksNS() : 0;
    const OutdoorSelectedFxLights lights = lightingRuntime.selectForBounds(fallbackReferencePosition, bounds);

    if (pLightingStats != nullptr)
    {
        ++pLightingStats->selectionCalls;
        const uint32_t sourceLightCount = lightingRuntime.sourceLightCount();
        pLightingStats->outdoorEmitterInputs += sourceLightCount;
        pLightingStats->outdoorEmitterFiltered += lights.filteredEmitterCount;
        pLightingStats->outdoorRankedCandidates += lights.rankedCandidateCount;
        pLightingStats->outdoorSelectedUniformLights += lights.lightCount;
        pLightingStats->inputLights += sourceLightCount;
        pLightingStats->inputDynamicLights += sourceLightCount;
        pLightingStats->clusteredFxLights += lightingRuntime.outputClusterLightCount();
        pLightingStats->outputLights += lights.lightCount;
        pLightingStats->outdoorUniformSelectionNanoseconds += SDL_GetTicksNS() - selectionBeginTickCount;
    }
    return lights;
}

void applyOutdoorFxLightUniformsForBounds(
    bgfx::UniformHandle positionsUniformHandle,
    bgfx::UniformHandle colorsUniformHandle,
    bgfx::UniformHandle paramsUniformHandle,
    const OutdoorLightingRuntime &lightingRuntime,
    LightingStats *pLightingStats,
    const bx::Vec3 &fallbackReferencePosition,
    const OutdoorLightSelectionBounds &bounds)
{
    if (!bgfx::isValid(positionsUniformHandle)
        || !bgfx::isValid(colorsUniformHandle)
        || !bgfx::isValid(paramsUniformHandle))
    {
        return;
    }

    const OutdoorSelectedFxLights lights =
        selectOutdoorFxLightsForBounds(lightingRuntime, pLightingStats, fallbackReferencePosition, bounds);
    bgfx::setUniform(positionsUniformHandle, lights.positions.data(), OutdoorSelectedFxLights::MaxLights);
    bgfx::setUniform(colorsUniformHandle, lights.colors.data(), OutdoorSelectedFxLights::MaxLights);
    bgfx::setUniform(paramsUniformHandle, lights.params.data());
    if (pLightingStats != nullptr)
    {
        ++pLightingStats->outdoorUniformApplications;
    }
}

void applySelectedOutdoorFxLightUniforms(
    bgfx::UniformHandle positionsUniformHandle,
    bgfx::UniformHandle colorsUniformHandle,
    bgfx::UniformHandle paramsUniformHandle,
    const OutdoorSelectedFxLights &lights)
{
    bgfx::setUniform(positionsUniformHandle, lights.positions.data(), OutdoorSelectedFxLights::MaxLights);
    bgfx::setUniform(colorsUniformHandle, lights.colors.data(), OutdoorSelectedFxLights::MaxLights);
    bgfx::setUniform(paramsUniformHandle, lights.params.data());
}

uint32_t computeOutdoorSkyTintAbgr(const OutdoorWorldRuntime &worldRuntime)
{
    const uint8_t brightness = outdoorClearDistanceFogBrightness(worldRuntime.gameMinutes());
    return makeAbgr(brightness, brightness, brightness);
}

uint32_t computeOutdoorSkyFogColorAbgr(const OutdoorWorldRuntime::AtmosphereState &atmosphereState)
{
    if (atmosphereState.hasAuthoredFogColor)
    {
        return makeAbgr(
            atmosphereState.authoredFogRed,
            atmosphereState.authoredFogGreen,
            atmosphereState.authoredFogBlue);
    }

    if (atmosphereState.underwater)
    {
        return makeAbgr(UnderwaterFogRed, UnderwaterFogGreen, UnderwaterFogBlue);
    }

    if ((atmosphereState.weatherFlags & MapWeatherFoggy) == 0)
    {
        return 0xff000000u;
    }

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
        static_cast<int>(std::lround((1.0f - atmosphereState.fogDensity) * 200.0f + atmosphereState.fogDensity * 31.0f)),
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
        const uint8_t green = static_cast<uint8_t>(std::lround(static_cast<float>(fogLevel) * 0.35f));
        const uint8_t blue = static_cast<uint8_t>(std::lround(static_cast<float>(fogLevel) * 0.35f));
        return makeAbgr(red, green, blue);
    }

    return makeAbgr(red, red, red);
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
    const std::filesystem::path configuredShaderRoot = OPENYAMM_BGFX_SHADER_DIR;
    std::string rendererDirectory;

    switch (rendererType)
    {
    case bgfx::RendererType::Direct3D11:
        rendererDirectory = "dxbc";
        break;

    case bgfx::RendererType::OpenGL:
        rendererDirectory = "glsl";
        break;

    case bgfx::RendererType::OpenGLES:
        rendererDirectory = "essl";
        break;

    default:
        return {};
    }

    const std::filesystem::path shaderName =
        std::filesystem::path(rendererDirectory) / (std::string(pShaderName) + ".bin");

    if (configuredShaderRoot.is_absolute())
    {
        return configuredShaderRoot / shaderName;
    }

    if (const char *pBasePath = SDL_GetBasePath())
    {
        const std::filesystem::path executableRoot = pBasePath;
        const std::filesystem::path packagedPath = executableRoot / configuredShaderRoot / shaderName;

        if (std::filesystem::exists(packagedPath))
        {
            return packagedPath;
        }

        const std::filesystem::path buildTreePath = executableRoot / ".." / configuredShaderRoot / shaderName;

        if (std::filesystem::exists(buildTreePath))
        {
            return buildTreePath;
        }

        return packagedPath;
    }

    return configuredShaderRoot / shaderName;
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

std::array<float, 4> outdoorFaceFlowInfo(
    const OutdoorBModelFace &face,
    int textureWidth,
    int textureHeight)
{
    constexpr float FlowPixelsPerSecond = 62.5f;
    std::array<float, 4> flowInfo = {0.0f, 0.0f, 0.0f, 0.0f};

    if (textureWidth <= 0 || textureHeight <= 0)
    {
        return flowInfo;
    }

    if (hasFaceAttribute(face.attributes, FaceAttribute::FlowDown))
    {
        flowInfo[1] = -FlowPixelsPerSecond / static_cast<float>(textureHeight);
    }
    else if (hasFaceAttribute(face.attributes, FaceAttribute::FlowUp))
    {
        flowInfo[1] = FlowPixelsPerSecond / static_cast<float>(textureHeight);
    }

    if (hasFaceAttribute(face.attributes, FaceAttribute::FlowRight))
    {
        flowInfo[0] = FlowPixelsPerSecond / static_cast<float>(textureWidth);
    }
    else if (hasFaceAttribute(face.attributes, FaceAttribute::FlowLeft))
    {
        flowInfo[0] = -FlowPixelsPerSecond / static_cast<float>(textureWidth);
    }

    flowInfo[2] = hasFaceAttribute(face.attributes, FaceAttribute::Lava) ? 1.0f : 0.0f;
    flowInfo[3] = hasFaceAttribute(face.attributes, FaceAttribute::Fluid) ? 1.0f : 0.0f;
    return flowInfo;
}

bool outdoorFaceHiddenByEventRuntime(
    uint32_t faceId,
    uint32_t baseAttributes,
    const MapDeltaData *pMapDeltaData,
    const EventRuntimeState *pEventRuntimeState)
{
    if (pMapDeltaData != nullptr
        && faceId < pMapDeltaData->faceAttributes.size())
    {
        return hasFaceAttribute(pMapDeltaData->faceAttributes[faceId], FaceAttribute::Invisible);
    }

    uint32_t attributes = baseAttributes;

    if (pEventRuntimeState != nullptr)
    {
        const auto setIt = pEventRuntimeState->facetSetMasks.find(faceId);

        if (setIt != pEventRuntimeState->facetSetMasks.end())
        {
            attributes |= setIt->second;
        }

        const auto clearIt = pEventRuntimeState->facetClearMasks.find(faceId);

        if (clearIt != pEventRuntimeState->facetClearMasks.end())
        {
            attributes &= ~clearIt->second;
        }
    }

    return hasFaceAttribute(attributes, FaceAttribute::Invisible);
}

uint64_t outdoorSurfaceVisualRevision(
    const MapDeltaData *pMapDeltaData,
    const EventRuntimeState *pEventRuntimeState)
{
    uint64_t revision = pMapDeltaData != nullptr ? pMapDeltaData->surfaceRevision : 0;

    if (pEventRuntimeState != nullptr
        && (!pEventRuntimeState->outdoorModelMechanisms.empty()
            || !pEventRuntimeState->textureOverrides.empty()
            || !pEventRuntimeState->outdoorModelFacetTextureOverrides.empty()
            || !pEventRuntimeState->facetSetMasks.empty()
            || !pEventRuntimeState->facetClearMasks.empty()))
    {
        revision ^= pEventRuntimeState->outdoorSurfaceRevision
            + 0x9e3779b97f4a7c15ull
            + (revision << 6)
            + (revision >> 2);
    }

    return revision;
}

const EventRuntimeState::OutdoorModelMechanismDefinition *outdoorModelMechanismDefinitionForBModel(
    const EventRuntimeState *pEventRuntimeState,
    size_t bModelIndex)
{
    if (pEventRuntimeState == nullptr || pEventRuntimeState->outdoorModelMechanisms.empty())
    {
        return nullptr;
    }

    for (const std::pair<const uint32_t, EventRuntimeState::OutdoorModelMechanismDefinition> &entry :
        pEventRuntimeState->outdoorModelMechanisms)
    {
        if (entry.second.bmodelIndex == bModelIndex)
        {
            return &entry.second;
        }
    }

    return nullptr;
}

bool outdoorBModelHasRuntimeMechanism(const EventRuntimeState *pEventRuntimeState, size_t bModelIndex)
{
    return outdoorModelMechanismDefinitionForBModel(pEventRuntimeState, bModelIndex) != nullptr;
}

bool outdoorBModelUsesRuntimeDraw(
    const EventRuntimeState *pEventRuntimeState,
    const OutdoorWorldRuntime *pOutdoorWorldRuntime,
    size_t bModelIndex)
{
    return outdoorBModelHasRuntimeMechanism(pEventRuntimeState, bModelIndex)
        || (pOutdoorWorldRuntime != nullptr
            && pOutdoorWorldRuntime->isOutdoorDestructibleBModel(bModelIndex));
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
            clampedFarClipDistance,
            0.0f};
        return parameters;
    }

    const uint32_t fogColorAbgr = computeOutdoorSkyTintAbgr(*pOutdoorWorldRuntime);
    parameters.color = {
        static_cast<float>(fogColorAbgr & 0xffu) / 255.0f,
        static_cast<float>((fogColorAbgr >> 8) & 0xffu) / 255.0f,
        static_cast<float>((fogColorAbgr >> 16) & 0xffu) / 255.0f,
        1.0f
    };

    if (pAtmosphereState != nullptr
        && (pAtmosphereState->weatherFlags & MapWeatherFoggy) != 0
        && pAtmosphereState->fogWeakDistance >= 0
        && pAtmosphereState->fogStrongDistance > pAtmosphereState->fogWeakDistance)
    {
        const OutdoorFogProfile fogProfile = pAtmosphereState->directFog
            ? buildOutdoorDirectFogProfile(
                pAtmosphereState->fogWeakDistance,
                pAtmosphereState->fogStrongDistance)
            : buildOutdoorFogProfile(
                pAtmosphereState->fogWeakDistance,
                pAtmosphereState->fogStrongDistance,
                clampedFarClipDistance,
                OutdoorWorldFogNearOpacity,
                OutdoorWorldFogStrongOpacity);
        const uint32_t fogColorAbgr = computeOutdoorSkyFogColorAbgr(*pAtmosphereState);
        parameters.color = {
            static_cast<float>(fogColorAbgr & 0xffu) / 255.0f,
            static_cast<float>((fogColorAbgr >> 8) & 0xffu) / 255.0f,
            static_cast<float>((fogColorAbgr >> 16) & 0xffu) / 255.0f,
            1.0f
        };
        parameters.densities = {fogProfile.nearOpacity, fogProfile.strongOpacity, 0.0f, 0.0f};
        parameters.densities[3] = pAtmosphereState->directFog ? 1.0f : 0.0f;
        if (pAtmosphereState->underwater)
        {
            parameters.densities[2] = OutdoorUnderwaterTintOpacity;
        }
        parameters.distances = {
            fogProfile.weakDistance,
            fogProfile.strongDistance,
            fogProfile.farDistance,
            0.0f
        };
        return parameters;
    }

    const OutdoorFogProfile clearFogProfile = buildOutdoorClearDistanceFogProfile(clampedFarClipDistance);
    parameters.densities = {clearFogProfile.nearOpacity, clearFogProfile.strongOpacity, 0.0f, 0.0f};
    parameters.distances = {
        clearFogProfile.weakDistance,
        clearFogProfile.strongDistance,
        clearFogProfile.farDistance,
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
            clampedRenderDistance,
            0.0f};
        return parameters;
    }

    const uint32_t fogColorAbgr = computeOutdoorSkyTintAbgr(*pOutdoorWorldRuntime);
    parameters.color = {
        static_cast<float>(fogColorAbgr & 0xffu) / 255.0f,
        static_cast<float>((fogColorAbgr >> 8) & 0xffu) / 255.0f,
        static_cast<float>((fogColorAbgr >> 16) & 0xffu) / 255.0f,
        1.0f
    };

    if (pAtmosphereState != nullptr
        && (pAtmosphereState->weatherFlags & MapWeatherFoggy) != 0
        && pAtmosphereState->fogWeakDistance >= 0
        && pAtmosphereState->fogStrongDistance > pAtmosphereState->fogWeakDistance)
    {
        const OutdoorFogProfile fogProfile = pAtmosphereState->directFog
            ? buildOutdoorDirectFogProfile(
                pAtmosphereState->fogWeakDistance,
                pAtmosphereState->fogStrongDistance)
            : buildOutdoorFogProfile(
                pAtmosphereState->fogWeakDistance,
                pAtmosphereState->fogStrongDistance,
                clampedRenderDistance,
                OutdoorSkyFogNearOpacity,
                OutdoorSkyFogStrongOpacity);
        const uint32_t fogColorAbgr = computeOutdoorSkyFogColorAbgr(*pAtmosphereState);
        parameters.color = {
            static_cast<float>(fogColorAbgr & 0xffu) / 255.0f,
            static_cast<float>((fogColorAbgr >> 8) & 0xffu) / 255.0f,
            static_cast<float>((fogColorAbgr >> 16) & 0xffu) / 255.0f,
            1.0f
        };
        parameters.densities = {fogProfile.nearOpacity, fogProfile.strongOpacity, 0.0f, 0.0f};
        parameters.densities[3] = pAtmosphereState->directFog ? 1.0f : 0.0f;
        if (pAtmosphereState->underwater)
        {
            parameters.densities[2] = OutdoorUnderwaterTintOpacity;
        }
        parameters.distances = {
            fogProfile.weakDistance,
            fogProfile.strongDistance,
            fogProfile.farDistance,
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
    bgfx::UniformHandle cameraPositionUniformHandle,
    const bx::Vec3 &cameraPosition,
    const OutdoorFogParameters &parameters)
{
    if (!bgfx::isValid(fogColorUniformHandle)
        || !bgfx::isValid(fogDensitiesUniformHandle)
        || !bgfx::isValid(fogDistancesUniformHandle)
        || !bgfx::isValid(cameraPositionUniformHandle))
    {
        return;
    }

    bgfx::setUniform(fogColorUniformHandle, parameters.color.data());
    bgfx::setUniform(fogDensitiesUniformHandle, parameters.densities.data());
    bgfx::setUniform(fogDistancesUniformHandle, parameters.distances.data());
    const std::array<float, 4> cameraPositionUniform = {
        cameraPosition.x,
        cameraPosition.y,
        cameraPosition.z,
        0.0f
    };
    bgfx::setUniform(cameraPositionUniformHandle, cameraPositionUniform.data());
}

} // namespace

void OutdoorRenderer::applyOutdoorSurfaceUniforms(OutdoorGameView &view)
{
    if (bgfx::isValid(view.m_bakedLightingUniformHandle))
    {
        const OutdoorLightingData &lighting = *view.m_pOutdoorMapData->lightingData;
        const OutdoorWorldRuntime::AtmosphereState &atmosphere = view.m_pOutdoorWorldRuntime->atmosphereState();
        const std::array<float, 4> weights = outdoorBakedLightingWeights(atmosphere);
        bgfx::setUniform(view.m_bakedLightingUniformHandle, weights.data());
        std::array<float, 4> bounds = lighting.terrainBounds;
        const OutdoorLightmapAtlasPage &page = lighting.atlasPages[lighting.terrainPageIndex];
        const float texelX = bounds[2] / std::max(float(page.width) - 1.0f, 1.0f);
        const float texelY = bounds[3] / std::max(float(page.height) - 1.0f, 1.0f);
        bounds[0] -= texelX * 0.5f;
        bounds[1] -= texelY * 0.5f;
        bounds[2] += texelX;
        bounds[3] += texelY;
        bgfx::setUniform(view.m_bakedTerrainBoundsUniformHandle, bounds.data());
    }

    if (bgfx::isValid(view.m_outdoorSunlightUniformHandle))
    {
        bgfx::setUniform(view.m_outdoorSunlightUniformHandle, view.m_outdoorSunlight.data());
    }

    if (!bgfx::isValid(view.m_secretPulseParamsUniformHandle))
    {
        return;
    }

    const bool secretFacesDetected =
        view.m_map.has_value()
        && view.m_pOutdoorPartyRuntime != nullptr
        && GameMechanics::partyDetectsSecretFaces(view.m_pOutdoorPartyRuntime->party(), view.m_map.value());
    const float partyPerception = view.m_pOutdoorPartyRuntime != nullptr
        ? static_cast<float>(GameMechanics::resolvePartyPerceptionValue(view.m_pOutdoorPartyRuntime->party()))
        : -1.0f;
    const std::array<float, 4> params = {
        secretFacesDetected ? 1.0f : 0.0f,
        view.m_elapsedTime,
        partyPerception,
        0.0f
    };
    bgfx::setUniform(view.m_secretPulseParamsUniformHandle, params.data());
}

void OutdoorRenderer::applyOutdoorFxLightUniforms(OutdoorGameView &view, const bx::Vec3 &cameraPosition)
{
    if (!bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle)
        || !bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle)
        || !bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle))
    {
        return;
    }

    LightingStats *pLightingStats = view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr;

    if (pLightingStats != nullptr)
    {
        ++pLightingStats->outdoorUniformApplications;
    }

    const bool refreshUniforms =
        view.m_lastOutdoorFxLightUniformUpdateElapsedTime < 0.0f
        || (view.m_elapsedTime - view.m_lastOutdoorFxLightUniformUpdateElapsedTime)
            >= OutdoorFxLightRefreshIntervalSeconds;

    if (refreshUniforms)
    {
        const uint64_t selectionBeginTickCount = pLightingStats != nullptr ? SDL_GetTicksNS() : 0;
        const OutdoorLightSelectionBounds globalBounds = {};
        const OutdoorSelectedFxLights lights =
            view.m_outdoorLightingRuntime.selectForBounds(cameraPosition, globalBounds);
        view.m_cachedOutdoorFxLightPositions = lights.positions;
        view.m_cachedOutdoorFxLightColors = lights.colors;
        view.m_cachedOutdoorFxLightParams = lights.params;
        view.m_lastOutdoorFxLightUniformUpdateElapsedTime = view.m_elapsedTime;

        if (pLightingStats != nullptr)
        {
            const uint32_t sourceLightCount = view.m_outdoorLightingRuntime.sourceLightCount();
            pLightingStats->outdoorEmitterInputs += sourceLightCount;
            pLightingStats->outdoorEmitterFiltered += lights.filteredEmitterCount;
            pLightingStats->outdoorRankedCandidates += lights.rankedCandidateCount;
            pLightingStats->outdoorSelectedUniformLights += lights.lightCount;
            ++pLightingStats->selectionCalls;
            pLightingStats->inputLights += sourceLightCount;
            pLightingStats->inputDynamicLights += sourceLightCount;
            pLightingStats->clusteredFxLights += view.m_outdoorLightingRuntime.outputClusterLightCount();
            pLightingStats->outputLights += lights.lightCount;
            pLightingStats->outdoorUniformSelectionNanoseconds += SDL_GetTicksNS() - selectionBeginTickCount;
        }
    }

    bgfx::setUniform(
        view.m_outdoorFxLightPositionsUniformHandle,
        view.m_cachedOutdoorFxLightPositions.data(),
        OutdoorSelectedFxLights::MaxLights);
    bgfx::setUniform(
        view.m_outdoorFxLightColorsUniformHandle,
        view.m_cachedOutdoorFxLightColors.data(),
        OutdoorSelectedFxLights::MaxLights);
    bgfx::setUniform(view.m_outdoorFxLightParamsUniformHandle, view.m_cachedOutdoorFxLightParams.data());

    if (view.m_gameSettings.performanceTrace
        && view.m_elapsedTime - view.m_lastOutdoorLightingStatsLogElapsedTime >= 2.0f)
    {
        const uint64_t performanceLogBeginTickCount = SDL_GetTicksNS();
        const LightingStats &stats = view.m_outdoorLightingStats;
        std::cout << "[OutdoorLightingPerf]"
                  << " input=" << stats.inputLights
                  << " dynamic=" << stats.inputDynamicLights
                  << " filtered=" << stats.outdoorEmitterFiltered
                  << " ranked=" << stats.outdoorRankedCandidates
                  << " selected=" << stats.outdoorSelectedUniformLights
                  << " output=" << stats.outputLights
                  << " uniform_apps=" << stats.outdoorUniformApplications
                  << " selection_calls=" << stats.selectionCalls
                  << " avg_scan_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      stats.outdoorEmitterScanNanoseconds,
                      stats.outdoorRankedCandidates + stats.outdoorEmitterFiltered))
                  << " avg_select_us=" << nanosecondsToMicroseconds(averageNanoseconds(
                      stats.outdoorUniformSelectionNanoseconds,
                      stats.selectionCalls))
                  << '\n';

        const OutdoorGameView::OutdoorSpriteRenderDiagnostics &spriteStats =
            view.m_outdoorSpriteRenderDiagnostics;
        std::cout << "[OutdoorSpritePerf]"
                  << " dec_items=" << spriteStats.decorationItems
                  << " dec_batch_submits=" << spriteStats.decorationBatchSubmits
                  << " dec_batched=" << spriteStats.decorationBatchedItems
                  << " dec_texture_groups=" << spriteStats.decorationTextureGroups
                  << " dec_submits=" << spriteStats.decorationSubmits
                  << " dec_outline_submits=" << spriteStats.decorationOutlineSubmits
                  << " dec_texture_switches=" << spriteStats.decorationTextureSwitches
                  << " actor_items=" << spriteStats.actorItems
                  << " actor_batch_submits=" << spriteStats.actorBatchSubmits
                  << " actor_batched=" << spriteStats.actorBatchedItems
                  << " actor_submits=" << spriteStats.actorSubmits
                  << " actor_outline_submits=" << spriteStats.actorOutlineSubmits
                  << " actor_texture_switches=" << spriteStats.actorTextureSwitches
                  << " combined_depth_slices=" << spriteStats.combinedDepthSlices
                  << " combined_slice_texture_groups=" << spriteStats.combinedDepthSliceTextureGroups
                  << " combined_slice_items=" << spriteStats.combinedDepthSliceItems
                  << " world_item_items=" << spriteStats.worldItemItems
                  << " world_item_batch_submits=" << spriteStats.worldItemBatchSubmits
                  << " world_item_batched=" << spriteStats.worldItemBatchedItems
                  << " world_item_submits=" << spriteStats.worldItemSubmits
                  << " world_item_outline_submits=" << spriteStats.worldItemOutlineSubmits
                  << " world_item_texture_switches=" << spriteStats.worldItemTextureSwitches
                  << " world_item_depth_slices=" << spriteStats.worldItemDepthSlices
                  << " world_item_slice_texture_groups=" << spriteStats.worldItemDepthSliceTextureGroups
                  << " world_item_slice_items=" << spriteStats.worldItemDepthSliceItems
                  << " projectile_items=" << spriteStats.runtimeProjectileItems
                  << " projectile_batch_submits=" << spriteStats.runtimeProjectileBatchSubmits
                  << " projectile_batched=" << spriteStats.runtimeProjectileBatchedItems
                  << " projectile_texture_groups=" << spriteStats.runtimeProjectileTextureGroups
                  << " static_obj_items=" << spriteStats.staticSpriteObjectItems
                  << " static_obj_batch_submits=" << spriteStats.staticSpriteObjectBatchSubmits
                  << " static_obj_batched=" << spriteStats.staticSpriteObjectBatchedItems
                  << " static_obj_submits=" << spriteStats.staticSpriteObjectSubmits
                  << " static_obj_texture_switches=" << spriteStats.staticSpriteObjectTextureSwitches
                  << " fx_glow_items=" << spriteStats.fxGlowItems
                  << " fx_glow_submits=" << spriteStats.fxGlowSubmits
                  << " fx_shadow_items=" << spriteStats.fxContactShadowItems
                  << " fx_shadow_submits=" << spriteStats.fxContactShadowSubmits
                  << '\n';
        resetLightingStats(view.m_outdoorLightingStats);
        view.m_outdoorSpriteRenderDiagnostics = {};
        view.m_lastOutdoorLightingStatsLogElapsedTime = view.m_elapsedTime;
        view.m_performanceTraceLogNanosecondsThisFrame += SDL_GetTicksNS() - performanceLogBeginTickCount;
    }
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
        const EventRuntimeState *pEventRuntimeState =
            view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
        const MapDeltaData *pMapDeltaData =
            view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
        view.m_resolvedBModelDrawGroupRevision = outdoorSurfaceVisualRevision(pMapDeltaData, pEventRuntimeState);
        return;
    }

    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const MapDeltaData *pMapDeltaData =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
    const uint64_t targetRevision = outdoorSurfaceVisualRevision(pMapDeltaData, pEventRuntimeState);
    const std::unordered_map<uint32_t, std::string> *pTextureOverrides =
        pEventRuntimeState != nullptr ? &pEventRuntimeState->textureOverrides : nullptr;
    const std::unordered_map<uint32_t, std::string> *pModelFacetTextureOverrides =
        pEventRuntimeState != nullptr ? &pEventRuntimeState->outdoorModelFacetTextureOverrides : nullptr;

    std::unordered_map<std::string, size_t> animationIndexByTextureName;
    animationIndexByTextureName.reserve(view.m_bmodelTextureAnimations.size());

    for (size_t animationIndex = 0; animationIndex < view.m_bmodelTextureAnimations.size(); ++animationIndex)
    {
        animationIndexByTextureName[view.m_bmodelTextureAnimations[animationIndex].textureName] = animationIndex;
    }

    struct ResolvedVertices
    {
        std::vector<OutdoorGameView::TexturedTerrainVertex> textured;
        std::vector<OutdoorGameView::LightmappedBModelVertex> lightmapped;
    };
    // Material animation and atlas page both define a static draw group.
    std::map<std::pair<size_t, uint16_t>, ResolvedVertices> verticesByMaterial;

    for (const OutdoorGameView::TexturedBModelBatch &batch : view.m_texturedBModelBatches)
    {
        if (outdoorBModelHasRuntimeMechanism(pEventRuntimeState, batch.bModelIndex))
        {
            continue;
        }

        if (outdoorFaceHiddenByEventRuntime(batch.faceId, batch.baseAttributes, pMapDeltaData, pEventRuntimeState))
        {
            continue;
        }

        size_t animationIndex = batch.defaultAnimationIndex;
        bool hasModelFacetOverride = false;

        if (pModelFacetTextureOverrides != nullptr)
        {
            const uint32_t overrideKey =
                EventRuntime::outdoorModelFacetTextureOverrideKey(batch.bModelIndex, batch.faceIndex);
            const auto overrideIterator = pModelFacetTextureOverrides->find(overrideKey);

            if (overrideIterator != pModelFacetTextureOverrides->end())
            {
                hasModelFacetOverride = true;
                const std::string normalizedOverrideTextureName = toLowerCopy(overrideIterator->second);
                const auto animationIterator = animationIndexByTextureName.find(normalizedOverrideTextureName);

                if (animationIterator == animationIndexByTextureName.end())
                {
                    continue;
                }

                animationIndex = animationIterator->second;
            }
        }

        if (!hasModelFacetOverride && pTextureOverrides != nullptr)
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

        if (animationIndex >= view.m_bmodelTextureAnimations.size())
        {
            continue;
        }

        const uint16_t lightmapPage = batch.lightmappedVertices.empty() ? 0xffff : batch.lightmapPageIndex;
        ResolvedVertices &resolved = verticesByMaterial[{animationIndex, lightmapPage}];
        std::vector<OutdoorGameView::TexturedTerrainVertex> &groupVertices = resolved.textured;
        uint32_t effectiveAttributes = batch.baseAttributes;

        if (pMapDeltaData != nullptr && batch.faceId < pMapDeltaData->faceAttributes.size())
        {
            effectiveAttributes = pMapDeltaData->faceAttributes[batch.faceId];
        }
        else if (pEventRuntimeState != nullptr)
        {
            const auto setIt = pEventRuntimeState->facetSetMasks.find(batch.faceId);

            if (setIt != pEventRuntimeState->facetSetMasks.end())
            {
                effectiveAttributes |= setIt->second;
            }

            const auto clearIt = pEventRuntimeState->facetClearMasks.find(batch.faceId);

            if (clearIt != pEventRuntimeState->facetClearMasks.end())
            {
                effectiveAttributes &= ~clearIt->second;
            }
        }

        float secretPulse = batch.vertices.empty() ? 0.0f : batch.vertices.front().secretPulse;
        int perceptionDifficulty = -1;
        std::array<float, 4> flowInfo = {0.0f, 0.0f, 0.0f, 0.0f};

        if (view.m_pOutdoorMapData
            && batch.bModelIndex < view.m_pOutdoorMapData->bmodels.size()
            && batch.faceIndex < view.m_pOutdoorMapData->bmodels[batch.bModelIndex].faces.size())
        {
            OutdoorBModelFace effectiveFace =
                view.m_pOutdoorMapData->bmodels[batch.bModelIndex].faces[batch.faceIndex];
            perceptionDifficulty = effectiveFace.perceptionDifficulty;
            effectiveFace.attributes = effectiveAttributes;
            flowInfo = outdoorFaceFlowInfo(effectiveFace, batch.textureWidth, batch.textureHeight);
        }

        secretPulse = secretFaceVertexValue(effectiveAttributes, perceptionDifficulty);

        const size_t oldSize = groupVertices.size();
        groupVertices.insert(groupVertices.end(), batch.vertices.begin(), batch.vertices.end());
        const std::optional<OutdoorBModelRuntimeTransformState> runtimeTransform =
            outdoorBModelRuntimeTransform(pEventRuntimeState, batch.bModelIndex);

        for (size_t vertexIndex = oldSize; vertexIndex < groupVertices.size(); ++vertexIndex)
        {
            const bx::Vec3 transformed = applyOutdoorBModelRuntimeTransform(
                runtimeTransform,
                {
                    groupVertices[vertexIndex].x,
                    groupVertices[vertexIndex].y,
                    groupVertices[vertexIndex].z
                });
            groupVertices[vertexIndex].x = transformed.x;
            groupVertices[vertexIndex].y = transformed.y;
            groupVertices[vertexIndex].z = transformed.z;
            groupVertices[vertexIndex].secretPulse = secretPulse;
            groupVertices[vertexIndex].flowUPerSecond = flowInfo[0];
            groupVertices[vertexIndex].flowVPerSecond = flowInfo[1];
            groupVertices[vertexIndex].lavaFlow = flowInfo[2];
            groupVertices[vertexIndex].fluidFlow = flowInfo[3];
        }

        // Keep the exact same resolved position, event attributes and flow on the lightmap layout.
        for (size_t index = 0; index < batch.lightmappedVertices.size(); ++index)
        {
            OutdoorGameView::LightmappedBModelVertex vertex = batch.lightmappedVertices[index];
            const OutdoorGameView::TexturedTerrainVertex &source = groupVertices[oldSize + index];
            vertex.x = source.x;
            vertex.y = source.y;
            vertex.z = source.z;
            vertex.secretPulse = source.secretPulse;
            vertex.flowUPerSecond = source.flowUPerSecond;
            vertex.flowVPerSecond = source.flowVPerSecond;
            vertex.lavaFlow = source.lavaFlow;
            vertex.fluidFlow = source.fluidFlow;
            resolved.lightmapped.push_back(vertex);
        }
    }

    view.m_resolvedBModelDrawGroups.reserve(verticesByMaterial.size());

    for (const auto &[material, resolved] : verticesByMaterial)
    {
        const std::vector<OutdoorGameView::TexturedTerrainVertex> &groupVertices = resolved.textured;
        if (groupVertices.empty())
        {
            continue;
        }

        const bool usesStaticLighting = !resolved.lightmapped.empty();
        const bgfx::Memory *pVertices = usesStaticLighting
            ? bgfx::copy(resolved.lightmapped.data(),
                uint32_t(resolved.lightmapped.size() * sizeof(OutdoorGameView::LightmappedBModelVertex)))
            : bgfx::copy(groupVertices.data(),
                uint32_t(groupVertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex)));
        const bgfx::VertexBufferHandle vertexBufferHandle = bgfx::createVertexBuffer(pVertices,
            usesStaticLighting ? OutdoorGameView::LightmappedBModelVertex::ms_layout
                               : OutdoorGameView::TexturedTerrainVertex::ms_layout);

        if (!bgfx::isValid(vertexBufferHandle))
        {
            continue;
        }

        OutdoorGameView::ResolvedBModelDrawGroup group = {};
        group.vertexBufferHandle = vertexBufferHandle;
        group.vertexCount = static_cast<uint32_t>(groupVertices.size());
        group.animationIndex = material.first;
        group.lightmapPageIndex = material.second;
        group.usesStaticLighting = usesStaticLighting;
        const OutdoorLightSelectionBounds bounds = boundsFromTexturedVertices(groupVertices);
        group.boundsMin = bounds.min;
        group.boundsMax = bounds.max;
        group.hasBounds = bounds.valid;
        view.m_resolvedBModelDrawGroups.push_back(group);
    }

    view.m_resolvedBModelDrawGroupRevision = targetRevision;
}

void OutdoorRenderer::destroyBModelWorldRenderChunks(OutdoorGameView &view)
{
    for (OutdoorGameView::BModelWorldRenderChunk &chunk : view.m_bmodelWorldRenderChunks)
    {
        for (OutdoorGameView::BModelWorldRenderGroup &group : chunk.groups)
        {
            if (bgfx::isValid(group.vertexBufferHandle))
            {
                bgfx::destroy(group.vertexBufferHandle);
                group.vertexBufferHandle = BGFX_INVALID_HANDLE;
            }
        }

        chunk.groups.clear();
        chunk.faces.clear();
    }

    view.m_bmodelWorldRenderChunks.clear();
    view.m_bmodelWorldRenderRevision = std::numeric_limits<uint64_t>::max();
}

void OutdoorRenderer::refreshBModelWorldRenderChunks(OutdoorGameView &view)
{
    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const MapDeltaData *pMapDeltaData =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
    const uint64_t targetRevision = outdoorSurfaceVisualRevision(pMapDeltaData, pEventRuntimeState);

    if (view.m_bmodelWorldRenderRevision == targetRevision)
    {
        return;
    }

    const auto effectiveAttributesForFace = [&](const OutdoorGameView::BModelWorldRenderFace &face)
    {
        uint32_t attributes = face.baseAttributes;

        if (pMapDeltaData != nullptr && face.faceId < pMapDeltaData->faceAttributes.size())
        {
            return pMapDeltaData->faceAttributes[face.faceId];
        }

        if (pEventRuntimeState != nullptr)
        {
            const auto setIt = pEventRuntimeState->facetSetMasks.find(face.faceId);
            if (setIt != pEventRuntimeState->facetSetMasks.end())
            {
                attributes |= setIt->second;
            }

            const auto clearIt = pEventRuntimeState->facetClearMasks.find(face.faceId);
            if (clearIt != pEventRuntimeState->facetClearMasks.end())
            {
                attributes &= ~clearIt->second;
            }
        }

        return attributes;
    };
    const auto animationIndexForName = [&](const std::string &textureName)
    {
        const std::string normalizedName = toLowerCopy(textureName);

        for (size_t animationIndex = 0; animationIndex < view.m_bmodelTextureAnimations.size(); ++animationIndex)
        {
            if (view.m_bmodelTextureAnimations[animationIndex].textureName == normalizedName)
            {
                return animationIndex;
            }
        }

        return static_cast<size_t>(-1);
    };
    const auto animationIndexForFace = [&](const OutdoorGameView::BModelWorldRenderFace &face)
    {
        if (pEventRuntimeState != nullptr)
        {
            const uint32_t overrideKey =
                EventRuntime::outdoorModelFacetTextureOverrideKey(face.bModelIndex, face.faceIndex);
            const auto modelOverrideIt =
                pEventRuntimeState->outdoorModelFacetTextureOverrides.find(overrideKey);

            if (modelOverrideIt != pEventRuntimeState->outdoorModelFacetTextureOverrides.end())
            {
                return animationIndexForName(modelOverrideIt->second);
            }

            const auto textureOverrideIt = pEventRuntimeState->textureOverrides.find(face.cogNumber);
            if (textureOverrideIt != pEventRuntimeState->textureOverrides.end())
            {
                return animationIndexForName(textureOverrideIt->second);
            }
        }

        return face.defaultAnimationIndex;
    };
    const auto visualSignatureForFace = [&](const OutdoorGameView::BModelWorldRenderFace &face)
    {
        const uint64_t attributes = effectiveAttributesForFace(face);
        const uint64_t animationIndex = animationIndexForFace(face);
        return (attributes << 32) ^ animationIndex;
    };

    for (OutdoorGameView::BModelWorldRenderChunk &chunk : view.m_bmodelWorldRenderChunks)
    {
        bool needsRebuild = chunk.groups.empty();

        for (const OutdoorGameView::BModelWorldRenderFace &face : chunk.faces)
        {
            if (face.visualSignature != visualSignatureForFace(face))
            {
                needsRebuild = true;
                break;
            }
        }

        if (!needsRebuild)
        {
            continue;
        }

        for (OutdoorGameView::BModelWorldRenderGroup &group : chunk.groups)
        {
            if (bgfx::isValid(group.vertexBufferHandle))
            {
                bgfx::destroy(group.vertexBufferHandle);
            }
        }
        chunk.groups.clear();
        chunk.hasBounds = false;

        std::map<std::pair<size_t, bool>, std::vector<OutdoorGameView::TexturedTerrainVertex>> verticesByMaterial;
        std::map<std::tuple<size_t, bool, uint16_t>,
            std::vector<OutdoorGameView::LightmappedBModelVertex>> lightmappedVerticesByMaterial;

        for (OutdoorGameView::BModelWorldRenderFace &face : chunk.faces)
        {
            const uint32_t effectiveAttributes = effectiveAttributesForFace(face);
            const size_t animationIndex = animationIndexForFace(face);
            face.visualSignature = (static_cast<uint64_t>(effectiveAttributes) << 32) ^ animationIndex;

            if (outdoorFaceHasInvisibleAttribute(effectiveAttributes)
                || animationIndex >= view.m_bmodelTextureAnimations.size()
                || view.m_pOutdoorMapData == nullptr)
            {
                continue;
            }

            std::vector<OutdoorGameView::TexturedTerrainVertex> vertices = buildTexturedBModelFaceVertices(
                *view.m_pOutdoorMapData,
                face.bModelIndex,
                face.faceIndex,
                face.textureWidth,
                face.textureHeight);
            const OutdoorBModelFace &sourceFace =
                view.m_pOutdoorMapData->bmodels[face.bModelIndex].faces[face.faceIndex];
            OutdoorBModelFace effectiveFace = sourceFace;
            effectiveFace.attributes = effectiveAttributes;
            const std::array<float, 4> flowInfo =
                outdoorFaceFlowInfo(effectiveFace, face.textureWidth, face.textureHeight);
            const float secretPulse = secretFaceVertexValue(effectiveAttributes, sourceFace.perceptionDifficulty);

            for (OutdoorGameView::TexturedTerrainVertex &vertex : vertices)
            {
                vertex.secretPulse = secretPulse;
                vertex.flowUPerSecond = flowInfo[0];
                vertex.flowVPerSecond = flowInfo[1];
                vertex.lavaFlow = flowInfo[2];
                vertex.fluidFlow = flowInfo[3];
            }

            if (face.usesStaticLighting)
            {
                std::vector<OutdoorGameView::LightmappedBModelVertex> lightmappedVertices =
                    buildLightmappedBModelFaceVertices(
                        *view.m_pOutdoorMapData, face.bModelIndex, face.faceIndex, vertices);
                std::vector<OutdoorGameView::LightmappedBModelVertex> &groupVertices =
                    lightmappedVerticesByMaterial[{animationIndex, face.translucent, face.lightmapPageIndex}];
                groupVertices.insert(
                    groupVertices.end(), lightmappedVertices.begin(), lightmappedVertices.end());
            }
            else
            {
                std::vector<OutdoorGameView::TexturedTerrainVertex> &groupVertices =
                    verticesByMaterial[{animationIndex, face.translucent}];
                groupVertices.insert(groupVertices.end(), vertices.begin(), vertices.end());
            }
        }

        for (const auto &[materialKey, vertices] : verticesByMaterial)
        {
            if (vertices.empty())
            {
                continue;
            }

            const bgfx::VertexBufferHandle vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    vertices.data(),
                    static_cast<uint32_t>(vertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex))),
                OutdoorGameView::TexturedTerrainVertex::ms_layout);

            if (!bgfx::isValid(vertexBufferHandle))
            {
                continue;
            }

            const OutdoorLightSelectionBounds bounds = boundsFromTexturedVertices(vertices);
            OutdoorGameView::BModelWorldRenderGroup group = {};
            group.vertexBufferHandle = vertexBufferHandle;
            group.vertexCount = static_cast<uint32_t>(vertices.size());
            group.animationIndex = materialKey.first;
            group.translucent = materialKey.second;
            group.boundsMin = bounds.min;
            group.boundsMax = bounds.max;
            group.hasBounds = bounds.valid;
            chunk.groups.push_back(group);

            if (!bounds.valid)
            {
                continue;
            }

            if (!chunk.hasBounds)
            {
                chunk.boundsMin = bounds.min;
                chunk.boundsMax = bounds.max;
                chunk.hasBounds = true;
            }
            else
            {
                chunk.boundsMin.x = std::min(chunk.boundsMin.x, bounds.min.x);
                chunk.boundsMin.y = std::min(chunk.boundsMin.y, bounds.min.y);
                chunk.boundsMin.z = std::min(chunk.boundsMin.z, bounds.min.z);
                chunk.boundsMax.x = std::max(chunk.boundsMax.x, bounds.max.x);
                chunk.boundsMax.y = std::max(chunk.boundsMax.y, bounds.max.y);
                chunk.boundsMax.z = std::max(chunk.boundsMax.z, bounds.max.z);
            }
        }

        for (const auto &[materialKey, vertices] : lightmappedVerticesByMaterial)
        {
            if (vertices.empty())
            {
                continue;
            }

            const bgfx::VertexBufferHandle vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    vertices.data(),
                    static_cast<uint32_t>(
                        vertices.size() * sizeof(OutdoorGameView::LightmappedBModelVertex))),
                OutdoorGameView::LightmappedBModelVertex::ms_layout);

            if (!bgfx::isValid(vertexBufferHandle))
            {
                continue;
            }

            const OutdoorLightSelectionBounds bounds = boundsFromTexturedVertices(vertices);
            OutdoorGameView::BModelWorldRenderGroup group = {};
            group.vertexBufferHandle = vertexBufferHandle;
            group.vertexCount = static_cast<uint32_t>(vertices.size());
            group.animationIndex = std::get<0>(materialKey);
            group.translucent = std::get<1>(materialKey);
            group.lightmapPageIndex = std::get<2>(materialKey);
            group.usesStaticLighting = true;
            group.boundsMin = bounds.min;
            group.boundsMax = bounds.max;
            group.hasBounds = bounds.valid;
            chunk.groups.push_back(group);

            if (!bounds.valid)
            {
                continue;
            }

            if (!chunk.hasBounds)
            {
                chunk.boundsMin = bounds.min;
                chunk.boundsMax = bounds.max;
                chunk.hasBounds = true;
            }
            else
            {
                chunk.boundsMin.x = std::min(chunk.boundsMin.x, bounds.min.x);
                chunk.boundsMin.y = std::min(chunk.boundsMin.y, bounds.min.y);
                chunk.boundsMin.z = std::min(chunk.boundsMin.z, bounds.min.z);
                chunk.boundsMax.x = std::max(chunk.boundsMax.x, bounds.max.x);
                chunk.boundsMax.y = std::max(chunk.boundsMax.y, bounds.max.y);
                chunk.boundsMax.z = std::max(chunk.boundsMax.z, bounds.max.z);
            }
        }
    }

    view.m_bmodelWorldRenderRevision = targetRevision;
}

bool OutdoorRenderer::buildBModelWorldRenderChunks(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const OutdoorBModelTextureSet &outdoorBModelTextureSet)
{
    destroyBModelWorldRenderChunks(view);

    if (!outdoorMapData.renderData)
    {
        return false;
    }

    std::unordered_map<std::string, size_t> animationIndexByTextureName;
    for (size_t animationIndex = 0; animationIndex < view.m_bmodelTextureAnimations.size(); ++animationIndex)
    {
        animationIndexByTextureName[view.m_bmodelTextureAnimations[animationIndex].textureName] = animationIndex;
    }

    std::vector<uint32_t> firstFaceIdByBModel(outdoorMapData.bmodels.size(), 0);
    uint32_t faceId = 0;
    for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
    {
        firstFaceIdByBModel[bModelIndex] = faceId;
        faceId += static_cast<uint32_t>(outdoorMapData.bmodels[bModelIndex].faces.size());
    }

    std::map<std::pair<int32_t, int32_t>, size_t> chunkIndexByCell;

    for (const OutdoorRenderFaceReference &reference : outdoorMapData.renderData->faces)
    {
        if (reference.dynamic)
        {
            continue;
        }

        const OutdoorBModelFace &sourceFace =
            outdoorMapData.bmodels[reference.bModelIndex].faces[reference.faceIndex];
        const OutdoorBitmapTexture *pTexture = findBitmapTexture(outdoorBModelTextureSet, sourceFace.textureName);
        if (pTexture == nullptr)
        {
            continue;
        }

        const std::string textureName = toLowerCopy(sourceFace.textureName);
        const auto animationIt = animationIndexByTextureName.find(textureName);
        if (animationIt == animationIndexByTextureName.end())
        {
            continue;
        }

        const std::pair<int32_t, int32_t> cell = {reference.cellX, reference.cellY};
        auto chunkIt = chunkIndexByCell.find(cell);
        if (chunkIt == chunkIndexByCell.end())
        {
            OutdoorGameView::BModelWorldRenderChunk chunk = {};
            chunk.cellX = reference.cellX;
            chunk.cellY = reference.cellY;
            view.m_bmodelWorldRenderChunks.push_back(std::move(chunk));
            chunkIt = chunkIndexByCell.emplace(cell, view.m_bmodelWorldRenderChunks.size() - 1).first;
        }

        OutdoorGameView::BModelWorldRenderFace face = {};
        face.faceId = firstFaceIdByBModel[reference.bModelIndex] + reference.faceIndex;
        face.cogNumber = sourceFace.cogNumber;
        face.baseAttributes = sourceFace.attributes;
        face.bModelIndex = reference.bModelIndex;
        face.faceIndex = reference.faceIndex;
        face.textureWidth = pTexture->width;
        face.textureHeight = pTexture->height;
        face.defaultAnimationIndex = animationIt->second;
        face.translucent = reference.translucent;
        if (outdoorMapData.lightingData)
        {
            const OutdoorBModelFaceLighting &lighting =
                outdoorMapData.lightingData->facesByBModel[reference.bModelIndex][reference.faceIndex];
            face.lightmapPageIndex = lighting.atlasPageIndex;
            face.usesStaticLighting = true;
        }
        view.m_bmodelWorldRenderChunks[chunkIt->second].faces.push_back(face);
    }

    refreshBModelWorldRenderChunks(view);
    return true;
}

void OutdoorRenderer::initializeAnimatedWaterTileState(
    OutdoorGameView &view,
    const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas)
{
    view.m_animatedWaterTerrainTiles.clear();
    view.m_lastAnimatedWaterAnimationTicks.reset();

    if (!outdoorTerrainTextureAtlas || outdoorTerrainTextureAtlas->animatedWaterTiles.empty())
    {
        return;
    }

    view.m_animatedWaterTerrainTiles.reserve(outdoorTerrainTextureAtlas->animatedWaterTiles.size());

    for (const OutdoorAnimatedWaterTileSource &source : outdoorTerrainTextureAtlas->animatedWaterTiles)
    {
        OutdoorGameView::AnimatedWaterTerrainTileState tileState = {};
        const int cellSize = outdoorTerrainTextureAtlas->tileSize + outdoorTerrainTextureAtlas->tilePadding * 2;
        const int column = std::lround(source.region.u0 * outdoorTerrainTextureAtlas->width) / cellSize;
        const int row = std::lround(source.region.v0 * outdoorTerrainTextureAtlas->height) / cellSize;
        tileState.layer = row * (outdoorTerrainTextureAtlas->width / cellSize) + column;
        tileState.frameMipLevels.reserve(source.framePixels.size());
        for (const std::vector<uint8_t> &pixels : source.framePixels)
        {
            const uint16_t tileSize = std::lround(std::sqrt(pixels.size() / 4.0));
            tileState.frameMipLevels.push_back(prepareBgraMipChain(tileSize, tileSize, pixels));
        }
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
    if (!bgfx::isValid(view.m_terrainTextureArrayHandle)
        || view.m_animatedWaterTerrainTiles.empty())
    {
        return;
    }

    const uint32_t animationTicks = static_cast<uint32_t>(std::lround(view.m_elapsedTime * 128.0f));

    if (view.m_lastAnimatedWaterAnimationTicks && *view.m_lastAnimatedWaterAnimationTicks == animationTicks)
    {
        return;
    }

    view.m_lastAnimatedWaterAnimationTicks = animationTicks;

    for (OutdoorGameView::AnimatedWaterTerrainTileState &tileState : view.m_animatedWaterTerrainTiles)
    {
        if (tileState.frameMipLevels.empty())
        {
            continue;
        }

        const size_t frameIndex = frameIndexForAnimation(
            tileState.frameLengthTicks,
            tileState.animationLengthTicks,
            animationTicks);

        if (frameIndex >= tileState.frameMipLevels.size() || frameIndex == tileState.currentFrameIndex)
        {
            continue;
        }

        updateBgraTextureArrayLayer(
            view.m_terrainTextureArrayHandle, tileState.layer, tileState.frameMipLevels[frameIndex]);

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
            topLeft.u = 0.0f;
            topLeft.v = 0.0f;

            OutdoorGameView::TexturedTerrainVertex topRight = {};
            topRight.x = outdoorGridCornerWorldX(gridX + 1);
            topRight.y = outdoorGridCornerWorldY(gridY);
            topRight.z = static_cast<float>(mapData.heightMap[topRightIndex] * OutdoorMapData::TerrainHeightScale);
            topRight.u = 1.0f;
            topRight.v = 0.0f;

            OutdoorGameView::TexturedTerrainVertex bottomLeft = {};
            bottomLeft.x = outdoorGridCornerWorldX(gridX);
            bottomLeft.y = outdoorGridCornerWorldY(gridY + 1);
            bottomLeft.z = static_cast<float>(mapData.heightMap[bottomLeftIndex] * OutdoorMapData::TerrainHeightScale);
            bottomLeft.u = 0.0f;
            bottomLeft.v = 1.0f;

            OutdoorGameView::TexturedTerrainVertex bottomRight = {};
            bottomRight.x = outdoorGridCornerWorldX(gridX + 1);
            bottomRight.y = outdoorGridCornerWorldY(gridY + 1);
            bottomRight.z = static_cast<float>(mapData.heightMap[bottomRightIndex] * OutdoorMapData::TerrainHeightScale);
            bottomRight.u = 1.0f;
            bottomRight.v = 1.0f;

            for (OutdoorGameView::TexturedTerrainVertex *pVertex :
                {&topLeft, &topRight, &bottomLeft, &bottomRight})
            {
                pVertex->flowUPerSecond = rawTileId;
                pVertex->secretPulse = region.isWater && !region.isTransitionOverlay ? -1.0f : 0.0f;
            }

            vertices.push_back(topLeft);
            vertices.push_back(bottomLeft);
            vertices.push_back(topRight);
            vertices.push_back(topRight);
            vertices.push_back(bottomLeft);
            vertices.push_back(bottomRight);
        }
    }

    // Match the rendered diagonal and cache one normal per triangle, as in the original terrain path.
    for (size_t index = 0; index + 2 < vertices.size(); index += 3)
    {
        const float x = (vertices[index].x + vertices[index + 1].x + vertices[index + 2].x) / 3.0f;
        const float y = (vertices[index].y + vertices[index + 1].y + vertices[index + 2].y) / 3.0f;
        const bx::Vec3 normal = sampleOutdoorRenderedTerrainNormal(mapData, x, y);
        for (size_t slot = 0; slot < 3; ++slot)
        {
            vertices[index + slot].normalX = normal.x;
            vertices[index + slot].normalY = normal.y;
            vertices[index + slot].normalZ = normal.z;
        }
    }

    return vertices;
}

void OutdoorRenderer::destroyTexturedTerrainChunks(OutdoorGameView &view)
{
    for (OutdoorGameView::TexturedTerrainChunk &chunk : view.m_texturedTerrainChunks)
    {
        if (bgfx::isValid(chunk.vertexBufferHandle))
        {
            bgfx::destroy(chunk.vertexBufferHandle);
            chunk.vertexBufferHandle = BGFX_INVALID_HANDLE;
        }
    }

    view.m_texturedTerrainChunks.clear();
}

void OutdoorRenderer::buildTexturedTerrainChunks(
    OutdoorGameView &view,
    const std::vector<OutdoorGameView::TexturedTerrainVertex> &vertices)
{
    destroyTexturedTerrainChunks(view);

    if (vertices.empty())
    {
        return;
    }

    struct TerrainChunkBuildData
    {
        std::vector<OutdoorGameView::TexturedTerrainVertex> vertices;
        int32_t cellX = 0;
        int32_t cellY = 0;
    };

    std::unordered_map<uint64_t, TerrainChunkBuildData> chunkVerticesByKey;

    for (size_t triangleIndex = 0; triangleIndex + 2 < vertices.size(); triangleIndex += 3)
    {
        const OutdoorGameView::TexturedTerrainVertex &first = vertices[triangleIndex + 0];
        const OutdoorGameView::TexturedTerrainVertex &second = vertices[triangleIndex + 1];
        const OutdoorGameView::TexturedTerrainVertex &third = vertices[triangleIndex + 2];
        const float centerX = (first.x + second.x + third.x) / 3.0f;
        const float centerY = (first.y + second.y + third.y) / 3.0f;
        const int32_t cellX = outdoorTerrainChunkCell(centerX);
        const int32_t cellY = outdoorTerrainChunkCell(centerY);
        const uint64_t key =
            (static_cast<uint64_t>(static_cast<uint32_t>(cellX)) << 32)
            | static_cast<uint64_t>(static_cast<uint32_t>(cellY));
        TerrainChunkBuildData &chunkData = chunkVerticesByKey[key];
        chunkData.cellX = cellX;
        chunkData.cellY = cellY;
        std::vector<OutdoorGameView::TexturedTerrainVertex> &chunkVertices = chunkData.vertices;

        chunkVertices.push_back(first);
        chunkVertices.push_back(second);
        chunkVertices.push_back(third);
    }

    view.m_texturedTerrainChunks.reserve(chunkVerticesByKey.size());

    for (const std::pair<const uint64_t, TerrainChunkBuildData> &entry : chunkVerticesByKey)
    {
        const std::vector<OutdoorGameView::TexturedTerrainVertex> &chunkVertices = entry.second.vertices;

        if (chunkVertices.empty())
        {
            continue;
        }

        const bgfx::VertexBufferHandle vertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                chunkVertices.data(),
                static_cast<uint32_t>(chunkVertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex))),
            OutdoorGameView::TexturedTerrainVertex::ms_layout);

        if (!bgfx::isValid(vertexBufferHandle))
        {
            continue;
        }

        const OutdoorLightSelectionBounds bounds = boundsFromTexturedVertices(chunkVertices);
        OutdoorGameView::TexturedTerrainChunk chunk = {};
        chunk.vertexBufferHandle = vertexBufferHandle;
        chunk.vertexCount = static_cast<uint32_t>(chunkVertices.size());
        chunk.boundsMin = bounds.min;
        chunk.boundsMax = bounds.max;
        chunk.cellX = entry.second.cellX;
        chunk.cellY = entry.second.cellY;
        chunk.stableId = stableOutdoorTerrainChunkId(chunk.cellX, chunk.cellY);
        view.m_texturedTerrainChunks.push_back(chunk);
    }
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
    const std::array<float, 4> flowInfo = outdoorFaceFlowInfo(face, textureWidth, textureHeight);

    if (face.vertexIndices.size() < 3
        || face.textureName.empty())
    {
        return vertices;
    }

    bx::Vec3 normal = {0.0f, 0.0f, 0.0f};
    if (mapData.sceneProfile == OutdoorSceneProfile::ClassicOdm && !mapData.lightingData)
    {
        OutdoorFaceGeometryData geometry = {};
        if (!buildOutdoorFaceGeometry(bmodel, bModelIndex, face, faceIndex, geometry, true))
        {
            return vertices;
        }
        if (geometry.hasPlane)
        {
            normal = bx::normalize(geometry.normal);
        }
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
            vertex.normalX = normal.x;
            vertex.normalY = normal.y;
            vertex.normalZ = normal.z;
            vertex.u = normalizedU;
            vertex.v = normalizedV;
            vertex.secretPulse = secretFaceVertexValue(face.attributes, face.perceptionDifficulty);
            vertex.flowUPerSecond = flowInfo[0];
            vertex.flowVPerSecond = flowInfo[1];
            vertex.lavaFlow = flowInfo[2];
            vertex.fluidFlow = flowInfo[3];
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

std::vector<OutdoorGameView::LightmappedBModelVertex> OutdoorRenderer::buildLightmappedBModelFaceVertices(
    const OutdoorMapData &mapData,
    size_t bModelIndex,
    size_t faceIndex,
    const std::vector<OutdoorGameView::TexturedTerrainVertex> &vertices)
{
    std::vector<OutdoorGameView::LightmappedBModelVertex> result;

    if (!mapData.lightingData
        || bModelIndex >= mapData.lightingData->facesByBModel.size()
        || faceIndex >= mapData.lightingData->facesByBModel[bModelIndex].size())
    {
        return result;
    }

    const OutdoorBModelFaceLighting &lighting = mapData.lightingData->facesByBModel[bModelIndex][faceIndex];
    const OutdoorBModelFace &face = mapData.bmodels[bModelIndex].faces[faceIndex];
    const size_t triangleCount = face.vertexIndices.size() >= 3 ? face.vertexIndices.size() - 2 : 0;

    if ((mapData.lightingData->hasBakedSources() && !lighting.hasLightmap)
        || lighting.vertices.size() != face.vertexIndices.size() || vertices.size() != triangleCount * 3)
    {
        return result;
    }

    result.reserve(vertices.size());
    size_t sourceVertexIndex = 0;
    for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
    {
        const size_t localIndices[3] = {0, triangleIndex, triangleIndex + 1};

        for (size_t localIndex : localIndices)
        {
            const OutdoorGameView::TexturedTerrainVertex &source = vertices[sourceVertexIndex++];
            const OutdoorBModelLightingVertex &sourceLighting = lighting.vertices[localIndex];
            OutdoorGameView::LightmappedBModelVertex vertex = {};
            vertex.x = source.x;
            vertex.y = source.y;
            vertex.z = source.z;
            vertex.u = source.u;
            vertex.v = source.v;
            vertex.secretPulse = source.secretPulse;
            vertex.flowUPerSecond = source.flowUPerSecond;
            vertex.flowVPerSecond = source.flowVPerSecond;
            vertex.lavaFlow = source.lavaFlow;
            vertex.fluidFlow = source.fluidFlow;
            vertex.lightmapU = sourceLighting.u;
            vertex.lightmapV = sourceLighting.v;
            vertex.staticColorAbgr = sourceLighting.staticColorAbgr;
            result.push_back(vertex);
        }
    }

    return result;
}

std::vector<OutdoorGameView::TerrainVertex> OutdoorRenderer::buildFilledTerrainVertices(
    const OutdoorMapData &mapData,
    const std::optional<std::vector<uint32_t>> &tileColors,
    const OutdoorTerrainTextureAtlas *pTextureAtlas)
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
            if (pTextureAtlas != nullptr && pTextureAtlas->tileRegions[mapData.tileMap[topLeftIndex]].isValid)
            {
                // Textured cells own their color and depth, including holes in alpha-tested artwork.
                continue;
            }
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
            if (outdoorFaceHasInvisibleAttribute(face.attributes) || face.vertexIndices.size() < 2)
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
            if (outdoorFaceHasInvisibleAttribute(face.attributes) || face.vertexIndices.size() < 3)
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
        std::cerr << "Failed to create outdoor shaders: " << pVertexShaderName << " ("
                  << bgfx::isValid(vertexShaderHandle) << ") + " << pFragmentShaderName << " ("
                  << bgfx::isValid(fragmentShaderHandle) << ")\n";
        if (bgfx::isValid(vertexShaderHandle))
        {
            bgfx::destroy(vertexShaderHandle);
        }
        if (bgfx::isValid(fragmentShaderHandle))
        {
            bgfx::destroy(fragmentShaderHandle);
        }
        return bgfx::ProgramHandle{bgfx::kInvalidHandle};
    }

    const bgfx::ProgramHandle program = bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
    if (!bgfx::isValid(program))
    {
        std::cerr << "Failed to link outdoor shaders: " << pVertexShaderName << " + " << pFragmentShaderName << '\n';
    }
    return program;
}

void OutdoorRenderer::createBModelTextureBatches(
    OutdoorGameView &view,
    const OutdoorMapData &outdoorMapData,
    const std::optional<OutdoorBModelTextureSet> &outdoorBModelTextureSet)
{
    destroyResolvedBModelDrawGroups(view);
    destroyBModelWorldRenderChunks(view);

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

            const bgfx::TextureHandle textureHandle = createBgraTexture2D(
                uint16_t(pFrameTexture->physicalWidth),
                uint16_t(pFrameTexture->physicalHeight),
                pFrameTexture->pixels.data(),
                uint32_t(pFrameTexture->pixels.size()),
                TextureFilterProfile::BModel);

            if (!bgfx::isValid(textureHandle))
            {
                continue;
            }

            animationHandle.frameTextureHandles.push_back(textureHandle);
            animationHandle.frameLengthTicks.push_back(frame.frameLengthTicks);
            animationHandle.frameHasPartialAlphaPixels.push_back(pFrameTexture->hasPartialAlphaPixels);
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

    const bool bmodelWorld = outdoorMapData.sceneProfile == OutdoorSceneProfile::BModelWorld;
    std::unordered_map<uint64_t, bool> dynamicRenderFaces;

    if (bmodelWorld)
    {
        if (!buildBModelWorldRenderChunks(view, outdoorMapData, *outdoorBModelTextureSet))
        {
            std::cerr << "Failed to build BModel-world render chunks for " << outdoorMapData.fileName << '\n';
            return;
        }

        for (const OutdoorRenderFaceReference &reference : outdoorMapData.renderData->faces)
        {
            if (reference.dynamic)
            {
                dynamicRenderFaces.emplace(reference.sourceKey, reference.translucent);
            }
        }
    }

    uint32_t faceId = 0;

    for (size_t bModelIndex = 0; bModelIndex < outdoorMapData.bmodels.size(); ++bModelIndex)
    {
        const OutdoorBModel &bmodel = outdoorMapData.bmodels[bModelIndex];

        for (size_t localFaceIndex = 0; localFaceIndex < bmodel.faces.size(); ++localFaceIndex, ++faceId)
        {
            const OutdoorBModelFace &face = bmodel.faces[localFaceIndex];
            const uint64_t sourceKey = (static_cast<uint64_t>(bModelIndex) << 32) | localFaceIndex;

            const std::unordered_map<uint64_t, bool>::const_iterator dynamicRenderFaceIt =
                dynamicRenderFaces.find(sourceKey);
            if (bmodelWorld && dynamicRenderFaceIt == dynamicRenderFaces.end())
            {
                continue;
            }

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
            if (outdoorMapData.lightingData)
            {
                batch.lightmappedVertices = buildLightmappedBModelFaceVertices(
                    outdoorMapData, bModelIndex, localFaceIndex, texturedBModelVertices);
                batch.lightmapPageIndex =
                    outdoorMapData.lightingData->facesByBModel[bModelIndex][localFaceIndex].atlasPageIndex;
            }
            batch.faceId = faceId;
            batch.cogNumber = face.cogNumber;
            batch.baseAttributes = face.attributes;
            batch.bModelIndex = bModelIndex;
            batch.faceIndex = localFaceIndex;
            batch.textureWidth = pBaseTexture->width;
            batch.textureHeight = pBaseTexture->height;
            batch.textureName = toLowerCopy(face.textureName);
            const OutdoorLightSelectionBounds batchBounds = boundsFromTexturedVertices(batch.vertices);
            batch.boundsMin = batchBounds.min;
            batch.boundsMax = batchBounds.max;
            batch.hasBounds = batchBounds.valid;
            batch.translucent = bmodelWorld && dynamicRenderFaceIt->second;
            const auto animationIndexIterator = animationIndexByTextureName.find(batch.textureName);

            if (animationIndexIterator != animationIndexByTextureName.end())
            {
                batch.defaultAnimationIndex = animationIndexIterator->second;
            }

            view.m_texturedBModelBatches.push_back(std::move(batch));
        }
    }
}

void OutdoorRenderer::ensureTerrainDecorations(OutdoorGameView &view, const OutdoorMapData &outdoorMapData)
{
    if (!view.m_gameSettings.terrainDecorations || view.m_terrainDecorationsInitializationAttempted ||
        !view.m_terrainDecorationTileNames || view.m_pAssetFileSystem == nullptr)
    {
        return;
    }

    // Absent/invalid map content is attempted once, never reloaded every frame. Retain resources while disabled.
    view.m_terrainDecorationsInitializationAttempted = true;
    std::string error;
    const std::optional<TerrainDecorationConfig> config =
        loadTerrainDecorationConfig(*view.m_pAssetFileSystem, outdoorMapData, error);
    if (!error.empty())
    {
        std::cerr << error << '\n';
    }
    if (!config)
    {
        return;
    }
    if ((bgfx::getCaps()->supported & BGFX_CAPS_INSTANCING) == 0)
    {
        std::cerr << "Terrain decorations require renderer instancing support.\n";
        return;
    }

    TerrainDecorationPlacement placement = scatterTerrainDecorations(
        outdoorMapData, *view.m_terrainDecorationTileNames, *config);
    if (!placement.instances.empty())
    {
        view.m_terrainDecorations.initialize(*view.m_pAssetFileSystem, *config, std::move(placement),
            loadProgramHandle("vs_terrain_decoration",
                outdoorMapData.lightingData && outdoorMapData.lightingData->hasBakedSources()
                    ? "fs_terrain_decoration_baked" : "fs_terrain_decoration"));
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
    if (outdoorMapData.lightingData)
    {
        OutdoorGameView::LightmappedBModelVertex::init();
    }

    OutdoorGameView::ForcePerspectiveVertex::init();
    constexpr bool renderTerrain = true;
    const bool bmodelWorld = outdoorMapData.sceneProfile == OutdoorSceneProfile::BModelWorld;
    const std::vector<OutdoorGameView::TerrainVertex> vertices = buildTerrainVertices(outdoorMapData);
    const std::vector<uint16_t> indices = buildTerrainIndices();
    std::vector<OutdoorGameView::TexturedTerrainVertex> texturedTerrainVertices;
    const std::vector<OutdoorGameView::TerrainVertex> filledTerrainVertices =
        renderTerrain
            ? buildFilledTerrainVertices(outdoorMapData, outdoorTileColors,
                                         outdoorTerrainTextureAtlas ? &*outdoorTerrainTextureAtlas : nullptr)
            : std::vector<OutdoorGameView::TerrainVertex>();
    const std::vector<OutdoorGameView::TerrainVertex> bmodelVertices =
        bmodelWorld ? std::vector<OutdoorGameView::TerrainVertex>() : buildBModelWireframeVertices(outdoorMapData);
    const std::vector<OutdoorGameView::TerrainVertex> bmodelCollisionVertices =
        bmodelWorld
            ? std::vector<OutdoorGameView::TerrainVertex>()
            : buildBModelCollisionFaceVertices(outdoorMapData);
    const std::vector<OutdoorGameView::TerrainVertex> entityMarkerVertices =
        buildEntityMarkerVertices(outdoorMapData);
    const std::vector<OutdoorGameView::TerrainVertex> spawnMarkerVertices =
        buildSpawnMarkerVertices(outdoorMapData);

    if (renderTerrain && outdoorTerrainTextureAtlas)
    {
        texturedTerrainVertices = buildTexturedTerrainVertices(outdoorMapData, *outdoorTerrainTextureAtlas);
        buildTexturedTerrainChunks(view, texturedTerrainVertices);
    }
    else
    {
        destroyTexturedTerrainChunks(view);
    }

    // Keep only material names so a console enable can build decorations without reloading the map/atlas.
    if (!outdoorMapData.noTerrain && outdoorTerrainTextureAtlas)
    {
        view.m_terrainDecorationTileNames = outdoorTerrainTextureAtlas->tileTextureNames;
    }
    ensureTerrainDecorations(view, outdoorMapData);

    initializeAnimatedWaterTileState(view, renderTerrain ? outdoorTerrainTextureAtlas : std::nullopt);

    if (renderTerrain && (vertices.empty() || indices.empty()))
    {
        std::cerr << "OutdoorGameView received empty terrain mesh.\n";
        return false;
    }

    if (renderTerrain)
    {
        view.m_vertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                vertices.data(),
                static_cast<uint32_t>(vertices.size() * sizeof(OutdoorGameView::TerrainVertex))),
            OutdoorGameView::TerrainVertex::ms_layout);

        view.m_indexBufferHandle = bgfx::createIndexBuffer(
            bgfx::copy(indices.data(), static_cast<uint32_t>(indices.size() * sizeof(uint16_t))));
    }

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
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (!outdoorFaceHasInvisibleAttribute(face.attributes))
            {
                ++view.m_bmodelFaceCount;
            }
        }
    }

    view.m_programHandle = loadProgramHandle("vs_cubes", "fs_cubes");
    view.m_screenTintProgramHandle = loadProgramHandle("vs_screen_color", "fs_cubes");
    view.m_texturedTerrainProgramHandle = loadProgramHandle("vs_shadowmaps_texture", "fs_shadowmaps_texture");
    view.m_spellAreaPreviewProgramHandle = loadProgramHandle("vs_spell_area_preview", "fs_spell_area_preview");
    view.m_outdoorLitBillboardProgramHandle =
        loadProgramHandle("vs_outdoor_billboard_lit", "fs_outdoor_billboard_lit");
    view.m_spriteAtlasCache.setProgram(loadProgramHandle("vs_outdoor_billboard_lit", "fs_sprite_atlas"));
    view.m_worldFxRenderResources.setParticleProgramHandle(loadProgramHandle("vs_particle", "fs_particle"));
    view.m_outdoorTerrainFogProgramHandle =
        loadProgramHandle("vs_outdoor_textured_fog",
            outdoorMapData.lightingData && outdoorMapData.lightingData->hasBakedSources()
                ? "fs_outdoor_terrain_baked" : "fs_outdoor_terrain_fog");
    view.m_outdoorTexturedFogProgramHandle =
        loadProgramHandle("vs_outdoor_textured_fog", "fs_outdoor_textured_fog");
    if (outdoorMapData.lightingData)
    {
        view.m_outdoorBModelLightmapProgramHandle =
            loadProgramHandle("vs_outdoor_bmodel_lightmap",
                outdoorMapData.lightingData->hasBakedSources()
                    ? "fs_outdoor_bmodel_baked" : "fs_outdoor_bmodel_lightmap");
    }

    view.m_outdoorForcePerspectiveProgramHandle =
        loadProgramHandle("vs_outdoor_force_perspective", "fs_outdoor_force_perspective");

    if (outdoorTerrainTextureAtlas && !outdoorTerrainTextureAtlas->pixels.empty())
    {
        const OutdoorTerrainTextureAtlas &atlas = *outdoorTerrainTextureAtlas;
        view.m_terrainTextureArrayHandle = bgfx::createTexture2D(
            atlas.tileSize, atlas.tileSize, true, 256, bgraTextureUploadFormat(),
            textureFilterSamplerFlags(TextureFilterProfile::Terrain) | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

        for (uint16_t layer = 0; layer < atlas.tileRegions.size(); ++layer)
        {
            const OutdoorTerrainAtlasRegion &region = atlas.tileRegions[layer];

            if (region.isValid)
            {
                updateBgraTextureArrayLayer(view.m_terrainTextureArrayHandle, layer, atlas.tileSize, atlas.tileSize,
                    extractAtlasRegionPixels(atlas, region));
            }
        }
    }

    if (outdoorMapData.lightingData)
    {
        view.m_bmodelLightmapTextureHandles.reserve(outdoorMapData.lightingData->atlasPages.size());
        for (const OutdoorLightmapAtlasPage &page : outdoorMapData.lightingData->atlasPages)
        {
            const bgfx::TextureHandle textureHandle = createBgraTexture2D(
                uint16_t(page.width),
                uint16_t(page.height),
                reinterpret_cast<const uint8_t *>(page.pixelsBgra.data()),
                uint32_t(page.pixelsBgra.size() * sizeof(uint32_t)),
                TextureFilterProfile::Lightmap,
                BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
            if (!bgfx::isValid(textureHandle))
            {
                std::cerr << "Failed to create MM9 lightmap atlas texture\n";
                return false;
            }
            view.m_bmodelLightmapTextureHandles.push_back(textureHandle);
        }

        constexpr uint32_t WhitePixel = 0xffffffff;
        view.m_bmodelWhiteLightmapTextureHandle = createBgraTexture2D(
            1,
            1,
            reinterpret_cast<const uint8_t *>(&WhitePixel),
            sizeof(WhitePixel),
            TextureFilterProfile::Lightmap,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
        if (!bgfx::isValid(view.m_bmodelWhiteLightmapTextureHandle))
        {
            std::cerr << "Failed to create MM9 fallback lightmap texture\n";
            return false;
        }
    }


    createBModelTextureBatches(view, outdoorMapData, outdoorBModelTextureSet);
    ensureBloodSplatTexture(view);

    return true;
}

const OutdoorGameView::SkyTextureHandle *OutdoorRenderer::ensureSkyTexture(
    OutdoorGameView &view,
    const std::string &textureName,
    bool warnOnCacheMiss)
{
    if (textureName.empty())
    {
        return nullptr;
    }

    const std::string normalizedTextureName = toLowerCopy(textureName);
    const auto cachedTextureIt = view.m_skyTextureIndexByName.find(normalizedTextureName);

    if (cachedTextureIt != view.m_skyTextureIndexByName.end()
        && cachedTextureIt->second < view.m_skyTextureHandles.size())
    {
        return &view.m_skyTextureHandles[cachedTextureIt->second];
    }

    const bool logCacheMiss =
        warnOnCacheMiss && view.m_runtimeSkyLoadWarningNames.insert(normalizedTextureName).second;
    const uint64_t loadBeginTickNanoseconds = logCacheMiss ? SDL_GetTicksNS() : 0;
    const auto logLoadResult = [&](const char *pResult, int width, int height)
    {
        if (!logCacheMiss)
        {
            return;
        }

        std::cerr << "[AssetLoadWarning] kind=sky phase=render scene=outdoor"
                  << " map=\"" << (view.m_map ? view.m_map->fileName : std::string()) << "\""
                  << " texture=\"" << normalizedTextureName << "\""
                  << " result=" << pResult
                  << " load_us=" << (SDL_GetTicksNS() - loadBeginTickNanoseconds) / 1000
                  << " size=" << width << 'x' << height
                  << '\n';
    };

    std::optional<std::string> bitmapPath = view.findCachedAssetPath("sky_textures", textureName + ".png");

    if (!bitmapPath)
    {
        bitmapPath = view.findCachedAssetPath("sky_textures", textureName + ".bmp");
    }

    if (!bitmapPath)
    {
        logLoadResult("failed", 0, 0);
        return nullptr;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = view.readCachedBinaryFile(*bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        logLoadResult("failed", 0, 0);
        return nullptr;
    }

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, *bitmapPath);

    if (!image)
    {
        logLoadResult("failed", 0, 0);
        return nullptr;
    }

    const int textureWidth = image->width;
    const int textureHeight = image->height;
    std::vector<uint8_t> pixels = image->pixels;

    OutdoorGameView::SkyTextureHandle textureHandle = {};
    textureHandle.textureName = normalizedTextureName;
    textureHandle.width = Engine::scalePhysicalPixelsToLogical(
        textureWidth,
        view.m_pAssetFileSystem != nullptr
            ? view.m_pAssetFileSystem->getAssetScaleTier(Engine::AssetScaleCategory::Sky)
            : Engine::AssetScaleTier::X1);
    textureHandle.height = Engine::scalePhysicalPixelsToLogical(
        textureHeight,
        view.m_pAssetFileSystem != nullptr
            ? view.m_pAssetFileSystem->getAssetScaleTier(Engine::AssetScaleCategory::Sky)
            : Engine::AssetScaleTier::X1);
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
    textureHandle.textureHandle = createBgraTexture2D(
        uint16_t(textureHandle.physicalWidth),
        uint16_t(textureHandle.physicalHeight),
        pixels.data(),
        uint32_t(pixels.size()),
        TextureFilterProfile::Sky);

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        logLoadResult("failed", textureWidth, textureHeight);
        return nullptr;
    }

    view.m_skyTextureHandles.push_back(std::move(textureHandle));
    view.m_skyTextureIndexByName[view.m_skyTextureHandles.back().textureName] = view.m_skyTextureHandles.size() - 1;
    logLoadResult("loaded", textureWidth, textureHeight);
    return &view.m_skyTextureHandles.back();
}

bgfx::TextureHandle OutdoorRenderer::ensureBloodSplatTexture(OutdoorGameView &view)
{
    if (bgfx::isValid(view.m_bloodSplatTextureHandle))
    {
        return view.m_bloodSplatTextureHandle;
    }

    std::optional<std::string> bitmapPath = view.findCachedAssetPath("Data/bitmaps", "hwsplat04.png");

    if (!bitmapPath)
    {
        bitmapPath = view.findCachedAssetPath("Data/bitmaps", "hwsplat04.bmp");
    }

    if (!bitmapPath)
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = view.readCachedBinaryFile(*bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, *bitmapPath);

    if (!image)
    {
        return BGFX_INVALID_HANDLE;
    }

    const int textureWidth = image->width;
    const int textureHeight = image->height;
    std::vector<uint8_t> pixels = image->pixels;

    for (size_t offset = 0; offset + 3 < pixels.size(); offset += 4)
    {
        const uint8_t intensity = std::max({pixels[offset + 0], pixels[offset + 1], pixels[offset + 2]});

        if (intensity == 0)
        {
            pixels[offset + 0] = 0;
            pixels[offset + 1] = 0;
            pixels[offset + 2] = 0;
            pixels[offset + 3] = 0;
            continue;
        }

        const float factor = static_cast<float>(intensity) / 255.0f;
        pixels[offset + 0] = static_cast<uint8_t>(std::lround(4.0f + 14.0f * factor));
        pixels[offset + 1] = static_cast<uint8_t>(std::lround(8.0f + 20.0f * factor));
        pixels[offset + 2] = static_cast<uint8_t>(std::lround(72.0f + 120.0f * factor));
        pixels[offset + 3] = intensity;
    }

    view.m_bloodSplatTextureHandle = createBgraTexture2D(
        uint16_t(textureWidth),
        uint16_t(textureHeight),
        pixels.data(),
        uint32_t(pixels.size()),
        TextureFilterProfile::BModel,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    return view.m_bloodSplatTextureHandle;
}

void OutdoorRenderer::ensureBloodSplatVertexBuffer(OutdoorGameView &view)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        if (bgfx::isValid(view.m_bloodSplatVertexBufferHandle))
        {
            bgfx::destroy(view.m_bloodSplatVertexBufferHandle);
            view.m_bloodSplatVertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        view.m_bloodSplatVertexCount = 0;
        view.m_bloodSplatVertexBufferRevision = std::numeric_limits<uint64_t>::max();
        return;
    }

    const uint64_t revision = view.m_pOutdoorWorldRuntime->bloodSplatRevision();

    if (view.m_bloodSplatVertexBufferRevision == revision)
    {
        return;
    }

    view.m_bloodSplatVertexBufferRevision = revision;

    if (bgfx::isValid(view.m_bloodSplatVertexBufferHandle))
    {
        bgfx::destroy(view.m_bloodSplatVertexBufferHandle);
        view.m_bloodSplatVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    view.m_bloodSplatVertexCount = 0;

    std::vector<OutdoorGameView::TexturedTerrainVertex> vertices;
    size_t totalVertexCount = 0;

    for (size_t splatIndex = 0; splatIndex < view.m_pOutdoorWorldRuntime->bloodSplatCount(); ++splatIndex)
    {
        const OutdoorWorldRuntime::BloodSplatState *pSplat = view.m_pOutdoorWorldRuntime->bloodSplatState(splatIndex);

        if (pSplat == nullptr || pSplat->vertices.empty())
        {
            continue;
        }

        totalVertexCount += pSplat->vertices.size();
    }

    if (totalVertexCount == 0)
    {
        return;
    }

    vertices.reserve(totalVertexCount);

    for (size_t splatIndex = 0; splatIndex < view.m_pOutdoorWorldRuntime->bloodSplatCount(); ++splatIndex)
    {
        const OutdoorWorldRuntime::BloodSplatState *pSplat = view.m_pOutdoorWorldRuntime->bloodSplatState(splatIndex);

        if (pSplat == nullptr || pSplat->vertices.empty())
        {
            continue;
        }

        for (const OutdoorWorldRuntime::BloodSplatState::Vertex &sourceVertex : pSplat->vertices)
        {
            OutdoorGameView::TexturedTerrainVertex vertex = {};
            vertex.x = sourceVertex.x;
            vertex.y = sourceVertex.y;
            vertex.z = sourceVertex.z;
            vertex.u = sourceVertex.u;
            vertex.v = sourceVertex.v;
            vertices.push_back(vertex);
        }
    }

    const bgfx::Memory *pVertexMemory = bgfx::copy(
        vertices.data(),
        static_cast<uint32_t>(vertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex)));
    view.m_bloodSplatVertexBufferHandle = bgfx::createVertexBuffer(
        pVertexMemory,
        OutdoorGameView::TexturedTerrainVertex::ms_layout);
    view.m_bloodSplatVertexCount = static_cast<uint32_t>(vertices.size());
}

void OutdoorRenderer::renderBloodSplats(
    OutdoorGameView &view,
    uint16_t viewId,
    const bx::Vec3 &cameraPosition,
    float farClipDistance,
    bool useLocalFxLighting)
{
    if (view.m_pOutdoorWorldRuntime == nullptr
        || !view.m_gameSettings.bloodSplats
        || !bgfx::isValid(view.m_outdoorTexturedFogProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || !bgfx::isValid(view.m_outdoorFogColorUniformHandle)
        || !bgfx::isValid(view.m_outdoorFogDensitiesUniformHandle)
        || !bgfx::isValid(view.m_outdoorFogDistancesUniformHandle)
        || !bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle)
        || !bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle)
        || !bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle)
        || !bgfx::isValid(view.m_secretPulseParamsUniformHandle))
    {
        return;
    }

    const bgfx::TextureHandle bloodSplatTextureHandle = ensureBloodSplatTexture(view);

    if (!bgfx::isValid(bloodSplatTextureHandle))
    {
        return;
    }

    ensureBloodSplatVertexBuffer(view);

    if (!bgfx::isValid(view.m_bloodSplatVertexBufferHandle) || view.m_bloodSplatVertexCount == 0)
    {
        return;
    }

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, view.m_bloodSplatVertexBufferHandle, 0, view.m_bloodSplatVertexCount);
    bindTexture(
        0,
        view.m_terrainTextureSamplerHandle,
        bloodSplatTextureHandle,
        TextureFilterProfile::BModel,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    if (useLocalFxLighting)
    {
        const OutdoorLightSelectionBounds bloodSplatBounds = boundsFromBloodSplats(*view.m_pOutdoorWorldRuntime);
        applyOutdoorFxLightUniformsForBounds(
            view.m_outdoorFxLightPositionsUniformHandle,
            view.m_outdoorFxLightColorsUniformHandle,
            view.m_outdoorFxLightParamsUniformHandle,
            view.m_outdoorLightingRuntime,
            view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr,
            cameraPosition,
            bloodSplatBounds);
    }
    else
    {
        applyOutdoorFxLightUniforms(view, cameraPosition);
    }
    const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState =
        view.m_pOutdoorWorldRuntime != nullptr ? &view.m_pOutdoorWorldRuntime->atmosphereState() : nullptr;
    const OutdoorFogParameters fogParameters =
        buildOutdoorWorldFogParameters(view.m_pOutdoorWorldRuntime, pAtmosphereState, farClipDistance);
    applyOutdoorFogUniforms(
        view.m_outdoorFogColorUniformHandle,
        view.m_outdoorFogDensitiesUniformHandle,
        view.m_outdoorFogDistancesUniformHandle,
        view.m_outdoorCameraPositionUniformHandle,
        cameraPosition,
        fogParameters);
    applyOutdoorSurfaceUniforms(view);
    bgfx::setState(
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_DEPTH_TEST_LEQUAL
        | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, view.m_outdoorTexturedFogProgramHandle);
}

void OutdoorRenderer::renderContextActionGeometryHighlight(OutdoorGameView &view, uint16_t viewId)
{
    if (!view.settingsSnapshot().contextActionPopup)
    {
        return;
    }

    const GameplayWorldHit *pHit =
        selectedContextActionWorldHit(view.m_gameSession.gameplayScreenRuntime().contextActionStateReadOnly());

    if (pHit == nullptr || !bgfx::isValid(view.m_programHandle))
    {
        return;
    }

    size_t highlightedBModelIndex = GameplayInvalidWorldIndex;
    size_t highlightedFaceIndex = GameplayInvalidWorldIndex;

    if (pHit->kind != GameplayWorldHitKind::EventTarget
        || !pHit->eventTarget.has_value()
        || pHit->eventTarget->targetKind != GameplayWorldEventTargetKind::Surface
        || pHit->eventTarget->targetIndex == GameplayInvalidWorldIndex
        || pHit->eventTarget->secondaryIndex == GameplayInvalidWorldIndex)
    {
        return;
    }

    highlightedBModelIndex = pHit->eventTarget->targetIndex;
    highlightedFaceIndex = pHit->eventTarget->secondaryIndex;

    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const MapDeltaData *pMapDeltaData =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
    const uint32_t color = contextActionGeometryHighlightColor(view.m_elapsedTime);
    std::vector<OutdoorGameView::TerrainVertex> highlightVertices;

    for (const OutdoorGameView::TexturedBModelBatch &batch : view.m_texturedBModelBatches)
    {
        if (batch.bModelIndex != highlightedBModelIndex
            || (highlightedFaceIndex != GameplayInvalidWorldIndex && batch.faceIndex != highlightedFaceIndex)
            || batch.vertices.empty()
            || outdoorFaceHiddenByEventRuntime(batch.faceId, batch.baseAttributes, pMapDeltaData, pEventRuntimeState))
        {
            continue;
        }

        const std::optional<OutdoorBModelRuntimeTransformState> runtimeTransform =
            outdoorBModelRuntimeTransform(pEventRuntimeState, batch.bModelIndex);
        bx::Vec3 normal = {0.0f, 0.0f, 0.0f};

        if (view.m_pOutdoorMapData
            && batch.bModelIndex < view.m_pOutdoorMapData->bmodels.size()
            && batch.faceIndex < view.m_pOutdoorMapData->bmodels[batch.bModelIndex].faces.size())
        {
            OutdoorFaceGeometryData geometry = {};
            const OutdoorBModel &bmodel = view.m_pOutdoorMapData->bmodels[batch.bModelIndex];
            const OutdoorBModelFace &face = bmodel.faces[batch.faceIndex];

            if (buildOutdoorFaceGeometry(bmodel, batch.bModelIndex, face, batch.faceIndex, geometry, true)
                && contextHighlightVecLength(geometry.normal) > 0.0001f)
            {
                normal = contextHighlightVecNormalize(geometry.normal);
            }
        }

        const bx::Vec3 offset = {normal.x * 1.5f, normal.y * 1.5f, normal.z * 1.5f};
        highlightVertices.reserve(batch.vertices.size());

        for (const OutdoorGameView::TexturedTerrainVertex &vertex : batch.vertices)
        {
            float transformedX = vertex.x;
            float transformedY = vertex.y;
            float transformedZ = vertex.z;
            const bx::Vec3 transformed = applyOutdoorBModelRuntimeTransform(
                runtimeTransform,
                {transformedX, transformedY, transformedZ});
            transformedX = transformed.x;
            transformedY = transformed.y;
            transformedZ = transformed.z;
            highlightVertices.push_back(
                {
                    transformedX + offset.x,
                    transformedY + offset.y,
                    transformedZ + offset.z,
                    color
                });
        }

        break;
    }

    if (highlightVertices.empty()
        || bgfx::getAvailTransientVertexBuffer(
            static_cast<uint32_t>(highlightVertices.size()),
            OutdoorGameView::TerrainVertex::ms_layout) < highlightVertices.size())
    {
        return;
    }

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(
        &transientVertexBuffer,
        static_cast<uint32_t>(highlightVertices.size()),
        OutdoorGameView::TerrainVertex::ms_layout);
    std::memcpy(
        transientVertexBuffer.data,
        highlightVertices.data(),
        highlightVertices.size() * sizeof(OutdoorGameView::TerrainVertex));

    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    bgfx::setTransform(modelMatrix);
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(highlightVertices.size()));
    bgfx::setState(
        BGFX_STATE_WRITE_RGB
        | BGFX_STATE_WRITE_A
        | BGFX_STATE_DEPTH_TEST_LEQUAL
        | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, view.m_programHandle);
}

void OutdoorRenderer::invalidateSkyResources(OutdoorGameView &view)
{
    for (OutdoorGameView::SkyTextureHandle &textureHandle : view.m_skyTextureHandles)
    {
        textureHandle.textureHandle = BGFX_INVALID_HANDLE;
    }

    view.m_skyTextureHandles.clear();
    view.m_skyTextureIndexByName.clear();
    view.m_runtimeSkyLoadWarningNames.clear();
}

void OutdoorRenderer::destroySkyResources(OutdoorGameView &view) {
  for (OutdoorGameView::SkyTextureHandle &textureHandle :
       view.m_skyTextureHandles) {
    if (bgfx::isValid(textureHandle.textureHandle)) {
      bgfx::destroy(textureHandle.textureHandle);
      textureHandle.textureHandle = BGFX_INVALID_HANDLE;
    }
  }

  invalidateSkyResources(view);
}

void OutdoorRenderer::renderWorldPasses(OutdoorGameView &view, uint16_t viewWidth, uint16_t viewHeight,
                                        float aspectRatio, float farClipDistance,
                                        const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState,
                                        const bx::Vec3 &cameraPosition, const bx::Vec3 &cameraForward,
                                        const bx::Vec3 &cameraRight, const bx::Vec3 &cameraUp, const float *pViewMatrix,
                                        const float *pProjectionMatrix)
{
    const ViewFrustum frustum(pViewMatrix, pProjectionMatrix, bgfx::getCaps()->homogeneousDepth);
    float modelMatrix[16] = {};
    bx::mtxIdentity(modelMatrix);
    const uint32_t identityTransform = bgfx::setTransform(modelMatrix);
    const OutdoorFogParameters worldFogParameters =
        buildOutdoorWorldFogParameters(view.m_pOutdoorWorldRuntime, pAtmosphereState, farClipDistance);
    const OutdoorLightingData *pLightingData = view.m_pOutdoorMapData != nullptr && view.m_pOutdoorMapData->lightingData
                                                   ? &*view.m_pOutdoorMapData->lightingData
                                                   : nullptr;
    view.m_outdoorSunlight = view.m_pOutdoorMapData != nullptr && pAtmosphereState != nullptr
        ? buildOutdoorSunlight(*view.m_pOutdoorMapData, *pAtmosphereState)
        : std::array<float, 4>{0.0f, 0.0f, 0.0f, 1.0f};
    const std::vector<WorldFxLightEmitter> &dynamicLightEmitters = view.m_worldFxSystem.lightEmitters();
    const bool lightingInputsChanged =
        !view.m_outdoorLightingRuntimesInitialized || view.m_pCachedOutdoorLightingData != pLightingData ||
        !sameWorldFxLightEmitters(view.m_cachedOutdoorDynamicLightEmitters, dynamicLightEmitters);

    if (lightingInputsChanged)
    {
        view.m_cachedOutdoorDynamicLightEmitters = dynamicLightEmitters;
        view.m_pCachedOutdoorLightingData = pLightingData;
        view.m_outdoorBModelLightingRuntime.build(dynamicLightEmitters);

        if (pLightingData != nullptr)
        {
            std::vector<WorldFxLightEmitter> objectLightEmitters = dynamicLightEmitters;
            objectLightEmitters.reserve(objectLightEmitters.size() + pLightingData->authoredLights.size());

            for (const OutdoorAuthoredLight &source : pLightingData->authoredLights)
            {
                if (!source.lightsObjects() || source.globalObjectLight() || source.radius <= 1.0f)
                {
                    continue;
                }

                WorldFxLightEmitter emitter = {};
                emitter.x = source.position[0];
                emitter.y = source.position[1];
                emitter.z = source.position[2];
                emitter.radius = source.radius;
                emitter.colorAbgr = source.effectiveColorAbgr;
                emitter.kind = RenderLightKind::Static;
                emitter.stableId = 0x90000000u ^ source.sourceObjectIndex;
                objectLightEmitters.push_back(emitter);
            }

            view.m_outdoorLightingRuntime.build(objectLightEmitters);
        }
        else
        {
            view.m_outdoorLightingRuntime.build(dynamicLightEmitters);
        }

        view.m_outdoorLightingRuntimesInitialized = true;
    }
    const bool useLocalFxLighting =
        (pLightingData != nullptr && !pLightingData->hasBakedSources()) ||
        view.m_outdoorLightingRuntime.outputClusterLightCount() > OutdoorSelectedFxLights::MaxLights;
    const OutdoorLightingRuntime &bModelLightingRuntime =
        pLightingData != nullptr ? view.m_outdoorBModelLightingRuntime : view.m_outdoorLightingRuntime;
    const bool useLocalBModelFxLighting =
        bModelLightingRuntime.outputClusterLightCount() > OutdoorSelectedFxLights::MaxLights;
    const OutdoorSelectedFxLights globalBModelLights = !useLocalBModelFxLighting
        ? bModelLightingRuntime.selectForBounds(cameraPosition, OutdoorLightSelectionBounds{})
        : OutdoorSelectedFxLights{};

    const bool renderSky =
        pAtmosphereState != nullptr &&
        (view.m_pOutdoorMapData == nullptr || view.m_pOutdoorMapData->locationType == OutdoorLocationType::Exterior ||
         !view.m_pOutdoorMapData->skyTexture.empty());

    if (renderSky)
    {
        renderOutdoorSky(view, SkyViewId, viewWidth, viewHeight, cameraPosition, cameraForward, cameraRight, cameraUp,
                         farClipDistance);
    }

    // MainView is sequential. Establish shared surface state on the first
    // actual surface draw, including when terrain or buildings are hidden.
    bool worldSurfaceUniformsApplied = false;
    const auto ensureWorldSurfaceUniforms = [&]()
    {
        if (!worldSurfaceUniformsApplied)
        {
            applyOutdoorFogUniforms(
                view.m_outdoorFogColorUniformHandle, view.m_outdoorFogDensitiesUniformHandle,
                view.m_outdoorFogDistancesUniformHandle, view.m_outdoorCameraPositionUniformHandle,
                cameraPosition, worldFogParameters);
            applyOutdoorSurfaceUniforms(view);
            worldSurfaceUniformsApplied = true;
        }
    };
    bool globalBModelLightsApplied = false;
    const auto ensureGlobalBModelLights = [&]()
    {
        if (!globalBModelLightsApplied)
        {
            applySelectedOutdoorFxLightUniforms(
                view.m_outdoorFxLightPositionsUniformHandle, view.m_outdoorFxLightColorsUniformHandle,
                view.m_outdoorFxLightParamsUniformHandle, globalBModelLights);
            globalBModelLightsApplied = true;
        }
    };

    {
        bgfx::setTransform(identityTransform);

        const bool showTerrain = view.m_showFilledTerrain;
        const bool showFilledTerrain =
            showTerrain && !(view.m_pOutdoorMapData != nullptr && view.m_pOutdoorMapData->noTerrain);

        if (showFilledTerrain && bgfx::isValid(view.m_filledTerrainVertexBufferHandle))
        {
            bgfx::setVertexBuffer(0, view.m_filledTerrainVertexBufferHandle);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z | BGFX_STATE_DEPTH_TEST_LESS);
            bgfx::submit(MainViewId, view.m_programHandle);
        }

        if (showTerrain && !(view.m_pOutdoorMapData != nullptr && view.m_pOutdoorMapData->noTerrain) &&
            bgfx::isValid(view.m_outdoorTerrainFogProgramHandle) && bgfx::isValid(view.m_terrainTextureArrayHandle) &&
            bgfx::isValid(view.m_terrainTextureSamplerHandle) &&
            bgfx::isValid(view.m_terrainWaterSamplerHandle) &&
            bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle) &&
            bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle) &&
            bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle) &&
            bgfx::isValid(view.m_secretPulseParamsUniformHandle))
        {
            updateAnimatedWaterTileTexture(view);

            if (useLocalFxLighting && !view.m_texturedTerrainChunks.empty())
            {
                for (const OutdoorGameView::TexturedTerrainChunk &chunk : view.m_texturedTerrainChunks)
                {
                    if (!bgfx::isValid(chunk.vertexBufferHandle) || chunk.vertexCount == 0)
                    {
                        continue;
                    }

                    ensureWorldSurfaceUniforms();
                    bgfx::setVertexBuffer(0, chunk.vertexBufferHandle, 0, chunk.vertexCount);
                    bindTexture(0, view.m_terrainTextureSamplerHandle, view.m_terrainTextureArrayHandle,
                                TextureFilterProfile::Terrain, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                    bindTexture(1, view.m_terrainWaterSamplerHandle, view.m_terrainTextureArrayHandle,
                                TextureFilterProfile::Terrain);
                    OutdoorLightSelectionBounds chunkBounds = {};
                    chunkBounds.min = chunk.boundsMin;
                    chunkBounds.max = chunk.boundsMax;
                    chunkBounds.valid = true;
                    applyOutdoorFxLightUniformsForBounds(
                        view.m_outdoorFxLightPositionsUniformHandle, view.m_outdoorFxLightColorsUniformHandle,
                        view.m_outdoorFxLightParamsUniformHandle, view.m_outdoorLightingRuntime,
                        view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr, cameraPosition,
                        chunkBounds);

                    if (view.m_pOutdoorMapData->lightingData
                        && view.m_pOutdoorMapData->lightingData->hasBakedSources())
                    {
                        const uint32_t page = view.m_pOutdoorMapData->lightingData->terrainPageIndex;
                        bindTexture(2, view.m_bmodelLightmapSamplerHandle, view.m_bmodelLightmapTextureHandles[page],
                            TextureFilterProfile::Lightmap);
                        bindTexture(3, view.m_bakedSkySamplerHandle, view.m_bmodelLightmapTextureHandles[page + 1],
                            TextureFilterProfile::Lightmap);
                    }
                    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z |
                                   BGFX_STATE_DEPTH_TEST_LEQUAL);
                    bgfx::submit(MainViewId, view.m_outdoorTerrainFogProgramHandle);
                }
            }
            else if (bgfx::isValid(view.m_texturedTerrainVertexBufferHandle))
            {
                ensureWorldSurfaceUniforms();
                bgfx::setVertexBuffer(0, view.m_texturedTerrainVertexBufferHandle);
                bindTexture(0, view.m_terrainTextureSamplerHandle, view.m_terrainTextureArrayHandle,
                            TextureFilterProfile::Terrain, BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                bindTexture(1, view.m_terrainWaterSamplerHandle, view.m_terrainTextureArrayHandle,
                            TextureFilterProfile::Terrain);
                applyOutdoorFxLightUniforms(view, cameraPosition);

                if (view.m_pOutdoorMapData->lightingData
                    && view.m_pOutdoorMapData->lightingData->hasBakedSources())
                {
                    const uint32_t page = view.m_pOutdoorMapData->lightingData->terrainPageIndex;
                    bindTexture(2, view.m_bmodelLightmapSamplerHandle, view.m_bmodelLightmapTextureHandles[page],
                        TextureFilterProfile::Lightmap);
                    bindTexture(3, view.m_bakedSkySamplerHandle, view.m_bmodelLightmapTextureHandles[page + 1],
                        TextureFilterProfile::Lightmap);
                }
                bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z |
                               BGFX_STATE_DEPTH_TEST_LEQUAL);
                bgfx::submit(MainViewId, view.m_outdoorTerrainFogProgramHandle);
            }
        }

        if (showFilledTerrain && view.m_gameSettings.terrainDecorations)
        {
            ensureTerrainDecorations(view, *view.m_pOutdoorMapData);
            const bool viewChanged = view.m_terrainDecorations.setView(
                cameraPosition, cameraForward, cameraRight, cameraUp, aspectRatio, bx::toRad(CameraVerticalFovDegrees));
            const uint64_t now = SDL_GetTicksNS();
            const uint32_t lightCount = view.m_outdoorLightingRuntime.sourceLightCount();
            // Refresh stationary-camera visibility/lighting at 20 Hz. Camera and light-count changes are immediate.
            // Wind, fog and actual draws still update every frame.
            if (viewChanged || now - view.m_terrainDecorationRefreshTick >= 50000000ULL ||
                lightCount != view.m_terrainDecorationLightCount)
            {
                view.m_terrainDecorationBatches.clear();
                for (const TerrainDecorationPatch &patch : view.m_terrainDecorations.patches())
                {
                    if (!view.m_terrainDecorations.visible(patch))
                    {
                        continue;
                    }
                    OutdoorLightSelectionBounds bounds = {};
                    bounds.min = {patch.min[0], patch.min[1], patch.min[2]};
                    bounds.max = {patch.max[0], patch.max[1], patch.max[2]};
                    bounds.valid = true;
                    const OutdoorSelectedFxLights lights = selectOutdoorFxLightsForBounds(
                        view.m_outdoorLightingRuntime,
                        view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr,
                        cameraPosition, bounds);
                    // Only merge contiguous visible ranges with exactly the same mesh and light uniforms.
                    if (!view.m_terrainDecorationBatches.empty() && TerrainDecorationRenderer::canMerge(
                            view.m_terrainDecorationBatches.back().range, view.m_terrainDecorationBatches.back().lights,
                            patch, lights))
                    {
                        view.m_terrainDecorationBatches.back().range.count += patch.count;
                    }
                    else
                    {
                        view.m_terrainDecorationBatches.push_back({patch, lights});
                    }
                }
                view.m_terrainDecorationRefreshTick = now;
                view.m_terrainDecorationLightCount = lightCount;
            }
            for (const OutdoorGameView::TerrainDecorationBatch &batch : view.m_terrainDecorationBatches)
            {
                if (bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle) &&
                    bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle) &&
                    bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle))
                {
                    applySelectedOutdoorFxLightUniforms(view.m_outdoorFxLightPositionsUniformHandle,
                        view.m_outdoorFxLightColorsUniformHandle, view.m_outdoorFxLightParamsUniformHandle, batch.lights);
                    if (view.m_gameSettings.performanceTrace)
                    {
                        ++view.m_outdoorLightingStats.outdoorUniformApplications;
                    }
                }

                if (view.m_pOutdoorMapData->lightingData
                    && view.m_pOutdoorMapData->lightingData->hasBakedSources())
                {
                    const uint32_t page = view.m_pOutdoorMapData->lightingData->terrainPageIndex;
                    bindTexture(2, view.m_bmodelLightmapSamplerHandle, view.m_bmodelLightmapTextureHandles[page],
                        TextureFilterProfile::Lightmap);
                    bindTexture(3, view.m_bakedSkySamplerHandle, view.m_bmodelLightmapTextureHandles[page + 1],
                        TextureFilterProfile::Lightmap);
                }
                ensureWorldSurfaceUniforms();
                view.m_terrainDecorations.submit(MainViewId, batch.range, view.m_elapsedTime);
            }
        }

        if (view.m_showTerrainWireframe)
        {
            bgfx::setTransform(identityTransform);
            bgfx::setVertexBuffer(0, view.m_vertexBufferHandle);
            bgfx::setIndexBuffer(view.m_indexBufferHandle);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z | BGFX_STATE_DEPTH_TEST_LESS |
                           BGFX_STATE_PT_LINES);
            bgfx::submit(MainViewId, view.m_programHandle);
        }
    }

    {
        const bool bmodelWorld = view.m_pOutdoorMapData != nullptr &&
                                 view.m_pOutdoorMapData->sceneProfile == OutdoorSceneProfile::BModelWorld;
        const bool hasBModelRenderResources =
            bmodelWorld ? (!view.m_bmodelWorldRenderChunks.empty() || !view.m_texturedBModelBatches.empty())
                        : (bgfx::isValid(view.m_bmodelVertexBufferHandle) && view.m_bmodelLineVertexCount > 0);

        if (view.m_showBModels && hasBModelRenderResources)
        {
            const EventRuntimeState *pEventRuntimeState =
                view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
            const MapDeltaData *pMapDeltaData =
                view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
            const uint64_t targetRevision = outdoorSurfaceVisualRevision(pMapDeltaData, pEventRuntimeState);

            if (bgfx::isValid(view.m_outdoorTexturedFogProgramHandle) &&
                bgfx::isValid(view.m_terrainTextureSamplerHandle) &&
                bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle) &&
                bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle) &&
                bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle) &&
                bgfx::isValid(view.m_secretPulseParamsUniformHandle))
            {
                const size_t bmodelRenderPassCount = bmodelWorld ? 2 : 1;
                for (size_t renderPass = 0; renderPass < bmodelRenderPassCount; ++renderPass)
                {
                    const bool translucentPass = renderPass == 1;

                    if (bmodelWorld)
                    {
                        refreshBModelWorldRenderChunks(view);
                    }
                    else if (view.m_resolvedBModelDrawGroupRevision != targetRevision)
                    {
                        rebuildResolvedBModelDrawGroups(view);
                    }

                    if (bmodelWorld)
                    {
                        const float verticalTangent = std::tan(CameraVerticalFovDegrees * Pi / 360.0f);
                        const float horizontalTangent = verticalTangent * aspectRatio;
                        const auto chunkVisible = [&](const OutdoorGameView::BModelWorldRenderChunk &chunk) {
                            if (!chunk.hasBounds)
                            {
                                return false;
                            }

                            const bx::Vec3 center = {(chunk.boundsMin.x + chunk.boundsMax.x) * 0.5f,
                                                     (chunk.boundsMin.y + chunk.boundsMax.y) * 0.5f,
                                                     (chunk.boundsMin.z + chunk.boundsMax.z) * 0.5f};
                            const bx::Vec3 extents = {(chunk.boundsMax.x - chunk.boundsMin.x) * 0.5f,
                                                      (chunk.boundsMax.y - chunk.boundsMin.y) * 0.5f,
                                                      (chunk.boundsMax.z - chunk.boundsMin.z) * 0.5f};
                            const float radius =
                                std::sqrt(extents.x * extents.x + extents.y * extents.y + extents.z * extents.z);
                            const bx::Vec3 cameraToCenter = {center.x - cameraPosition.x, center.y - cameraPosition.y,
                                                             center.z - cameraPosition.z};
                            const float depth = bx::dot(cameraToCenter, cameraForward);
                            const float horizontal = std::abs(bx::dot(cameraToCenter, cameraRight));
                            const float vertical = std::abs(bx::dot(cameraToCenter, cameraUp));
                            const float distanceSquared = bx::dot(cameraToCenter, cameraToCenter);
                            const float maximumDistance = farClipDistance + radius;

                            return depth + radius >= 0.0f && depth - radius <= farClipDistance &&
                                   horizontal <= std::max(depth, 0.0f) * horizontalTangent + radius &&
                                   vertical <= std::max(depth, 0.0f) * verticalTangent + radius &&
                                   distanceSquared <= maximumDistance * maximumDistance;
                        };

                        for (const OutdoorGameView::BModelWorldRenderChunk &chunk : view.m_bmodelWorldRenderChunks)
                        {
                            if (!chunkVisible(chunk))
                            {
                                continue;
                            }

                            for (const OutdoorGameView::BModelWorldRenderGroup &group : chunk.groups)
                            {
                                if (!bgfx::isValid(group.vertexBufferHandle) || group.vertexCount == 0 ||
                                    group.animationIndex >= view.m_bmodelTextureAnimations.size() ||
                                    group.translucent != translucentPass)
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
                                    animation.frameLengthTicks, animation.animationLengthTicks,
                                    static_cast<uint32_t>(std::lround(view.m_elapsedTime * 128.0f)));
                                if (frameIndex >= animation.frameTextureHandles.size() ||
                                    !bgfx::isValid(animation.frameTextureHandles[frameIndex]))
                                {
                                    continue;
                                }

                                ensureWorldSurfaceUniforms();
                                if (!useLocalBModelFxLighting)
                                {
                                    ensureGlobalBModelLights();
                                }
                                bgfx::setTransform(identityTransform);
                                bgfx::setVertexBuffer(0, group.vertexBufferHandle, 0, group.vertexCount);
                                bindTexture(0, view.m_terrainTextureSamplerHandle,
                                            animation.frameTextureHandles[frameIndex], TextureFilterProfile::BModel);
                                if (group.usesStaticLighting)
                                {
                                    const bgfx::TextureHandle lightmapTexture =
                                        group.lightmapPageIndex < view.m_bmodelLightmapTextureHandles.size()
                                            ? view.m_bmodelLightmapTextureHandles[group.lightmapPageIndex]
                                            : view.m_bmodelWhiteLightmapTextureHandle;
                                    bindTexture(1, view.m_bmodelLightmapSamplerHandle, lightmapTexture,
                                                TextureFilterProfile::Lightmap);
                                    if (view.m_pOutdoorMapData->lightingData->hasBakedSources())
                                    {
                                        bindTexture(3, view.m_bakedSkySamplerHandle,
                                            view.m_bmodelLightmapTextureHandles[group.lightmapPageIndex + 1],
                                            TextureFilterProfile::Lightmap);
                                    }
                                }
                                if (useLocalBModelFxLighting)
                                {
                                    OutdoorLightSelectionBounds groupBounds = {};
                                    groupBounds.min = group.boundsMin;
                                    groupBounds.max = group.boundsMax;
                                    groupBounds.valid = group.hasBounds;
                                    applyOutdoorFxLightUniformsForBounds(
                                        view.m_outdoorFxLightPositionsUniformHandle,
                                        view.m_outdoorFxLightColorsUniformHandle,
                                        view.m_outdoorFxLightParamsUniformHandle, bModelLightingRuntime,
                                        view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr,
                                        cameraPosition, groupBounds);
                                }

                                uint64_t state =
                                    BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_DEPTH_TEST_LEQUAL;
                                if (group.translucent)
                                {
                                    state |= BGFX_STATE_BLEND_ALPHA;
                                }
                                else
                                {
                                    state |= BGFX_STATE_WRITE_Z;
                                }
                                bgfx::setState(state);
                                bgfx::submit(MainViewId,
                                             group.usesStaticLighting ? view.m_outdoorBModelLightmapProgramHandle
                                                                      : view.m_outdoorTexturedFogProgramHandle,
                                             0, BGFX_DISCARD_ALL);
                            }
                        }
                    }

                    if (!bmodelWorld)
                    {
                        for (const OutdoorGameView::ResolvedBModelDrawGroup &group : view.m_resolvedBModelDrawGroups)
                        {
                            if (!bgfx::isValid(group.vertexBufferHandle) || group.vertexCount == 0 ||
                                group.animationIndex >= view.m_bmodelTextureAnimations.size())
                            {
                                continue;
                            }

                            if (group.hasBounds && !frustum.intersectsBounds(group.boundsMin, group.boundsMax))
                            {
                                continue;
                            }

                            const OutdoorGameView::BModelTextureAnimationHandle &animation =
                                view.m_bmodelTextureAnimations[group.animationIndex];

                            if (animation.frameTextureHandles.empty())
                            {
                                continue;
                            }

                            const size_t frameIndex =
                                frameIndexForAnimation(animation.frameLengthTicks, animation.animationLengthTicks,
                                                       static_cast<uint32_t>(std::lround(view.m_elapsedTime * 128.0f)));

                            if (frameIndex >= animation.frameTextureHandles.size() ||
                                !bgfx::isValid(animation.frameTextureHandles[frameIndex]))
                            {
                                continue;
                            }

                            ensureWorldSurfaceUniforms();
                            if (!useLocalBModelFxLighting)
                            {
                                ensureGlobalBModelLights();
                            }
                            bgfx::setTransform(identityTransform);
                            bgfx::setVertexBuffer(0, group.vertexBufferHandle, 0, group.vertexCount);
                            bindTexture(0, view.m_terrainTextureSamplerHandle,
                                        animation.frameTextureHandles[frameIndex], TextureFilterProfile::BModel);
                            if (group.usesStaticLighting)
                            {
                                const bgfx::TextureHandle lightmapTexture =
                                    group.lightmapPageIndex < view.m_bmodelLightmapTextureHandles.size()
                                        ? view.m_bmodelLightmapTextureHandles[group.lightmapPageIndex]
                                        : view.m_bmodelWhiteLightmapTextureHandle;
                                bindTexture(1, view.m_bmodelLightmapSamplerHandle,
                                    lightmapTexture, TextureFilterProfile::Lightmap);
                                if (view.m_pOutdoorMapData->lightingData->hasBakedSources())
                                {
                                    bindTexture(3, view.m_bakedSkySamplerHandle,
                                        view.m_bmodelLightmapTextureHandles[group.lightmapPageIndex + 1],
                                        TextureFilterProfile::Lightmap);
                                }
                            }
                            if (useLocalBModelFxLighting)
                            {
                                OutdoorLightSelectionBounds groupBounds = {};
                                groupBounds.min = group.boundsMin;
                                groupBounds.max = group.boundsMax;
                                groupBounds.valid = group.hasBounds;
                                applyOutdoorFxLightUniformsForBounds(
                                    view.m_outdoorFxLightPositionsUniformHandle,
                                    view.m_outdoorFxLightColorsUniformHandle, view.m_outdoorFxLightParamsUniformHandle,
                                    bModelLightingRuntime,
                                    view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr,
                                    cameraPosition, groupBounds);
                            }

                            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z |
                                           BGFX_STATE_DEPTH_TEST_LEQUAL);
                            bgfx::submit(MainViewId, group.usesStaticLighting
                                ? view.m_outdoorBModelLightmapProgramHandle : view.m_outdoorTexturedFogProgramHandle);
                        }
                    }

                    for (const OutdoorGameView::TexturedBModelBatch &batch : view.m_texturedBModelBatches)
                    {
                        if (!outdoorBModelUsesRuntimeDraw(
                                pEventRuntimeState, view.m_pOutdoorWorldRuntime, batch.bModelIndex) ||
                            batch.vertices.empty() || (bmodelWorld && batch.translucent != translucentPass) ||
                            outdoorFaceHiddenByEventRuntime(batch.faceId, batch.baseAttributes, pMapDeltaData,
                                                            pEventRuntimeState))
                        {
                            continue;
                        }

                        size_t animationIndex = batch.defaultAnimationIndex;
                        bool hasModelFacetOverride = false;

                        if (pEventRuntimeState != nullptr)
                        {
                            const uint32_t overrideKey =
                                EventRuntime::outdoorModelFacetTextureOverrideKey(batch.bModelIndex, batch.faceIndex);
                            const auto modelFacetOverrideIt =
                                pEventRuntimeState->outdoorModelFacetTextureOverrides.find(overrideKey);

                            if (modelFacetOverrideIt != pEventRuntimeState->outdoorModelFacetTextureOverrides.end())
                            {
                                hasModelFacetOverride = true;
                                const std::string normalizedOverrideTextureName =
                                    toLowerCopy(modelFacetOverrideIt->second);
                                animationIndex = static_cast<size_t>(-1);

                                for (size_t candidateIndex = 0; candidateIndex < view.m_bmodelTextureAnimations.size();
                                     ++candidateIndex)
                                {
                                    if (view.m_bmodelTextureAnimations[candidateIndex].textureName ==
                                        normalizedOverrideTextureName)
                                    {
                                        animationIndex = candidateIndex;
                                        break;
                                    }
                                }
                            }

                            if (!hasModelFacetOverride)
                            {
                                const auto textureOverrideIt =
                                    pEventRuntimeState->textureOverrides.find(batch.cogNumber);

                                if (textureOverrideIt != pEventRuntimeState->textureOverrides.end())
                                {
                                    const std::string normalizedOverrideTextureName =
                                        toLowerCopy(textureOverrideIt->second);
                                    animationIndex = static_cast<size_t>(-1);

                                    for (size_t candidateIndex = 0;
                                         candidateIndex < view.m_bmodelTextureAnimations.size(); ++candidateIndex)
                                    {
                                        if (view.m_bmodelTextureAnimations[candidateIndex].textureName ==
                                            normalizedOverrideTextureName)
                                        {
                                            animationIndex = candidateIndex;
                                            break;
                                        }
                                    }
                                }
                            }
                        }

                        if (animationIndex >= view.m_bmodelTextureAnimations.size())
                        {
                            continue;
                        }

                        const OutdoorGameView::BModelTextureAnimationHandle &animation =
                            view.m_bmodelTextureAnimations[animationIndex];

                        if (animation.frameTextureHandles.empty())
                        {
                            continue;
                        }

                        const size_t frameIndex =
                            frameIndexForAnimation(animation.frameLengthTicks, animation.animationLengthTicks,
                                                   static_cast<uint32_t>(std::lround(view.m_elapsedTime * 128.0f)));

                        if (frameIndex >= animation.frameTextureHandles.size() ||
                            !bgfx::isValid(animation.frameTextureHandles[frameIndex]))
                        {
                            continue;
                        }
                        const bool blendPartialAlpha =
                            bmodelWorld ? batch.translucent
                                        : (frameIndex < animation.frameHasPartialAlphaPixels.size() &&
                                           animation.frameHasPartialAlphaPixels[frameIndex]);

                        uint32_t effectiveAttributes = batch.baseAttributes;

                        if (pMapDeltaData != nullptr && batch.faceId < pMapDeltaData->faceAttributes.size())
                        {
                            effectiveAttributes = pMapDeltaData->faceAttributes[batch.faceId];
                        }
                        else if (pEventRuntimeState != nullptr)
                        {
                            const auto setIt = pEventRuntimeState->facetSetMasks.find(batch.faceId);

                            if (setIt != pEventRuntimeState->facetSetMasks.end())
                            {
                                effectiveAttributes |= setIt->second;
                            }

                            const auto clearIt = pEventRuntimeState->facetClearMasks.find(batch.faceId);

                            if (clearIt != pEventRuntimeState->facetClearMasks.end())
                            {
                                effectiveAttributes &= ~clearIt->second;
                            }
                        }

                        std::array<float, 4> flowInfo = {0.0f, 0.0f, 0.0f, 0.0f};
                        int perceptionDifficulty = -1;

                        if (view.m_pOutdoorMapData && batch.bModelIndex < view.m_pOutdoorMapData->bmodels.size() &&
                            batch.faceIndex < view.m_pOutdoorMapData->bmodels[batch.bModelIndex].faces.size())
                        {
                            OutdoorBModelFace effectiveFace =
                                view.m_pOutdoorMapData->bmodels[batch.bModelIndex].faces[batch.faceIndex];
                            perceptionDifficulty = effectiveFace.perceptionDifficulty;
                            effectiveFace.attributes = effectiveAttributes;
                            flowInfo = outdoorFaceFlowInfo(effectiveFace, batch.textureWidth, batch.textureHeight);
                        }

                        const float secretPulse = secretFaceVertexValue(effectiveAttributes, perceptionDifficulty);
                        const std::optional<OutdoorBModelRuntimeTransformState> runtimeTransform =
                            outdoorBModelRuntimeTransform(pEventRuntimeState, batch.bModelIndex);
                        std::vector<OutdoorGameView::TexturedTerrainVertex> vertices = batch.vertices;
                        std::vector<OutdoorGameView::LightmappedBModelVertex> lightmappedVertices =
                            batch.lightmappedVertices;

                        // A runtime batch contains one face. Rotate its normal once, without moving its origin.
                        bx::Vec3 transformedNormal = {0.0f, 0.0f, 0.0f};
                        if (runtimeTransform && !vertices.empty())
                        {
                            OutdoorBModelTransform normalTransform = runtimeTransform->transform;
                            normalTransform.translationX = 0.0f;
                            normalTransform.translationY = 0.0f;
                            normalTransform.translationZ = 0.0f;
                            normalTransform.pivotX = 0.0f;
                            normalTransform.pivotY = 0.0f;
                            normalTransform.pivotZ = 0.0f;
                            transformedNormal = transformOutdoorBModelPoint(
                                {vertices.front().normalX, vertices.front().normalY, vertices.front().normalZ},
                                normalTransform, runtimeTransform->fraction);
                        }
                        for (OutdoorGameView::TexturedTerrainVertex &vertex : vertices)
                        {
                            if (runtimeTransform)
                            {
                                vertex.normalX = transformedNormal.x;
                                vertex.normalY = transformedNormal.y;
                                vertex.normalZ = transformedNormal.z;
                            }
                            const bx::Vec3 transformed =
                                applyOutdoorBModelRuntimeTransform(runtimeTransform, {vertex.x, vertex.y, vertex.z});
                            vertex.x = transformed.x;
                            vertex.y = transformed.y;
                            vertex.z = transformed.z;
                            vertex.secretPulse = secretPulse;
                            vertex.flowUPerSecond = flowInfo[0];
                            vertex.flowVPerSecond = flowInfo[1];
                            vertex.lavaFlow = flowInfo[2];
                            vertex.fluidFlow = flowInfo[3];
                        }

                        for (OutdoorGameView::LightmappedBModelVertex &vertex : lightmappedVertices)
                        {
                            const bx::Vec3 transformed =
                                applyOutdoorBModelRuntimeTransform(runtimeTransform, {vertex.x, vertex.y, vertex.z});
                            vertex.x = transformed.x;
                            vertex.y = transformed.y;
                            vertex.z = transformed.z;
                            vertex.secretPulse = secretPulse;
                            vertex.flowUPerSecond = flowInfo[0];
                            vertex.flowVPerSecond = flowInfo[1];
                            vertex.lavaFlow = flowInfo[2];
                            vertex.fluidFlow = flowInfo[3];
                        }

                        const uint32_t vertexCount = static_cast<uint32_t>(vertices.size());
                        const bool usesStaticLighting = !lightmappedVertices.empty();
                        const bgfx::VertexLayout &vertexLayout =
                            usesStaticLighting ? OutdoorGameView::LightmappedBModelVertex::ms_layout
                                               : OutdoorGameView::TexturedTerrainVertex::ms_layout;

                        if (bgfx::getAvailTransientVertexBuffer(vertexCount, vertexLayout) < vertexCount)
                        {
                            continue;
                        }

                        bgfx::TransientVertexBuffer transientVertexBuffer = {};
                        bgfx::allocTransientVertexBuffer(&transientVertexBuffer, vertexCount, vertexLayout);
                        if (usesStaticLighting)
                        {
                            std::memcpy(transientVertexBuffer.data, lightmappedVertices.data(),
                                        lightmappedVertices.size() * sizeof(OutdoorGameView::LightmappedBModelVertex));
                        }
                        else
                        {
                            std::memcpy(transientVertexBuffer.data, vertices.data(),
                                        vertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex));
                        }

                        ensureWorldSurfaceUniforms();
                        if (!useLocalBModelFxLighting)
                        {
                            ensureGlobalBModelLights();
                        }
                        bgfx::setTransform(identityTransform);
                        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, vertexCount);
                        bindTexture(0, view.m_terrainTextureSamplerHandle, animation.frameTextureHandles[frameIndex],
                                    TextureFilterProfile::BModel);
                        if (usesStaticLighting)
                        {
                            const bgfx::TextureHandle lightmapTexture =
                                batch.lightmapPageIndex < view.m_bmodelLightmapTextureHandles.size()
                                    ? view.m_bmodelLightmapTextureHandles[batch.lightmapPageIndex]
                                    : view.m_bmodelWhiteLightmapTextureHandle;
                            bindTexture(1, view.m_bmodelLightmapSamplerHandle, lightmapTexture,
                                        TextureFilterProfile::Lightmap);
                            if (view.m_pOutdoorMapData->lightingData->hasBakedSources())
                            {
                                bindTexture(3, view.m_bakedSkySamplerHandle,
                                    view.m_bmodelLightmapTextureHandles[batch.lightmapPageIndex + 1],
                                    TextureFilterProfile::Lightmap);
                            }
                        }
                        if (useLocalBModelFxLighting)
                        {
                            const OutdoorLightSelectionBounds batchBounds = boundsFromTexturedVertices(vertices);
                            applyOutdoorFxLightUniformsForBounds(
                                view.m_outdoorFxLightPositionsUniformHandle, view.m_outdoorFxLightColorsUniformHandle,
                                view.m_outdoorFxLightParamsUniformHandle, bModelLightingRuntime,
                                view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr,
                                cameraPosition, batchBounds);
                        }

                        uint64_t state = BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_DEPTH_TEST_LEQUAL;
                        if (!bmodelWorld || !batch.translucent)
                        {
                            state |= BGFX_STATE_WRITE_Z;
                        }
                        if (blendPartialAlpha)
                        {
                            state |= BGFX_STATE_BLEND_ALPHA;
                        }
                        bgfx::setState(state);
                        bgfx::submit(MainViewId,
                                     usesStaticLighting ? view.m_outdoorBModelLightmapProgramHandle
                                                        : view.m_outdoorTexturedFogProgramHandle,
                                     0, BGFX_DISCARD_ALL);
                    }
                }
            }

            if (view.m_showBModelWireframe)
            {
                bgfx::setTransform(identityTransform);
                bgfx::setVertexBuffer(0, view.m_bmodelVertexBufferHandle, 0, view.m_bmodelLineVertexCount);
                bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z |
                               BGFX_STATE_DEPTH_TEST_LESS | BGFX_STATE_PT_LINES);
                bgfx::submit(MainViewId, view.m_programHandle);
            }
        }

        if (view.m_showBModelCollisionFaces && bgfx::isValid(view.m_bmodelCollisionVertexBufferHandle) &&
            view.m_bmodelCollisionVertexCount > 0)
        {
            bgfx::setTransform(identityTransform);
            bgfx::setVertexBuffer(0, view.m_bmodelCollisionVertexBufferHandle, 0, view.m_bmodelCollisionVertexCount);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z | BGFX_STATE_DEPTH_TEST_LESS |
                           BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(MainViewId, view.m_programHandle);
        }
    }

    if (view.m_showEntities && bgfx::isValid(view.m_entityMarkerVertexBufferHandle) &&
        view.m_entityMarkerVertexCount > 0)
    {
        bgfx::setTransform(identityTransform);
        bgfx::setVertexBuffer(0, view.m_entityMarkerVertexBufferHandle, 0, view.m_entityMarkerVertexCount);
        bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z | BGFX_STATE_DEPTH_TEST_LEQUAL |
                       BGFX_STATE_PT_LINES);
        bgfx::submit(MainViewId, view.m_programHandle);
    }

    renderBloodSplats(view, MainViewId, cameraPosition, farClipDistance, useLocalFxLighting);
    renderContextActionGeometryHighlight(view, MainViewId);

    if (view.m_gameSettings.shadows && (view.m_showSpriteObjects || view.m_showActors))
    {
        OutdoorBillboardRenderer::renderFxContactShadows(view, MainViewId);
    }

    if (view.m_showSpriteObjects)
    {
        OutdoorBillboardRenderer::renderRuntimeWorldItems(view, MainViewId, pViewMatrix, cameraPosition, frustum);
        OutdoorBillboardRenderer::renderRuntimeProjectiles(view, MainViewId, pViewMatrix, cameraPosition);
        OutdoorBillboardRenderer::renderSpriteObjectBillboards(view, MainViewId, pViewMatrix, cameraPosition);
    }

    if (view.m_showActors || view.m_showDecorationBillboards)
    {
        OutdoorBillboardRenderer::renderActorPreviewBillboards(view, MainViewId, pViewMatrix, cameraPosition, frustum);

        if (view.m_showActors && view.m_showActorCollisionBoxes)
        {
            renderActorCollisionOverlays(view, MainViewId, cameraPosition);
        }
    }

    if (view.m_showSpriteObjects || view.m_showActors || view.m_showDecorationBillboards)
    {
        OutdoorBillboardRenderer::renderFxGlowBillboards(view, MainViewId, pViewMatrix);
        OutdoorBillboardRenderer::renderFxSegmentProjectiles(view, MainViewId, pViewMatrix);
    }

    renderPendingSpellAreaPreview(view, MainViewId, cameraPosition);

    {
        if (view.m_showSpawns && bgfx::isValid(view.m_spawnMarkerVertexBufferHandle) &&
            view.m_spawnMarkerVertexCount > 0)
        {
            bgfx::setTransform(identityTransform);
            bgfx::setVertexBuffer(0, view.m_spawnMarkerVertexBufferHandle, 0, view.m_spawnMarkerVertexCount);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_WRITE_Z |
                           BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_PT_LINES);
            bgfx::submit(MainViewId, view.m_programHandle);
        }
    }

    if (view.m_showSpriteObjects || view.m_showActors || view.m_showDecorationBillboards)
    {
        ParticleRenderer::renderParticles(view.m_worldFxRenderResources, view.m_worldFxSystem.particles(), MainViewId,
                                          pViewMatrix, cameraPosition, aspectRatio);
    }

    if (pAtmosphereState != nullptr && pAtmosphereState->gameplayOverlayAlpha > 0.001f)
    {
        renderOutdoorGameplayOverlay(
            view, MainViewId, pAtmosphereState->gameplayOverlayAlpha, pAtmosphereState->gameplayOverlayColorAbgr);
    }
}

void OutdoorRenderer::renderPendingSpellAreaPreview(
    OutdoorGameView &view,
    uint16_t viewId,
    const bx::Vec3 &cameraPosition)
{
    const GameplayScreenState::PendingSpellTargetState &pendingSpellCast =
        view.m_gameSession.gameplayScreenState().pendingSpellTarget();

    if (view.m_pOutdoorWorldRuntime == nullptr
        || !pendingSpellCast.active)
    {
        return;
    }

    const std::optional<GameplaySpellTargetingOverlayRenderer::AreaMarkerVisualPolicy> markerPolicy =
        GameplaySpellTargetingOverlayRenderer::resolveAreaMarkerVisualPolicy(pendingSpellCast);

    if (!markerPolicy)
    {
        return;
    }

    const float previewRadius = markerPolicy->radius;
    const uint32_t previewColor = markerPolicy->ringColorAbgr;

    const GameplayInputFrame *pInputFrame = view.m_gameSession.currentGameplayInputFrame();

    if (pInputFrame == nullptr)
    {
        return;
    }

    const std::optional<bx::Vec3> targetPoint =
        pendingSpellCast.hasSelectedGroundTargetPoint
            ? std::optional<bx::Vec3>(bx::Vec3{
                pendingSpellCast.selectedGroundTargetX,
                pendingSpellCast.selectedGroundTargetY,
                pendingSpellCast.selectedGroundTargetZ})
            : view.m_pOutdoorWorldRuntime->spellActionGroundTargetPoint(
                pInputFrame->pointerX,
                pInputFrame->pointerY);

    if (!targetPoint)
    {
        return;
    }

    constexpr size_t RingSegments = 64;
    constexpr float PreviewHeightOffset = 6.0f;
    const float pulse = 0.5f + 0.5f * std::sin(view.m_elapsedTime * 5.0f);
    const float slowPulse = 0.5f + 0.5f * std::sin(view.m_elapsedTime * 2.4f);
    const float innerRingRadius = previewRadius * (0.70f + pulse * 0.05f);
    const float tickLength = std::max(18.0f, previewRadius * 0.08f);
    const float glowBandHalfWidth = std::max(18.0f, previewRadius * 0.03f);
    const float mainBandHalfWidth = std::max(6.0f, previewRadius * 0.010f);
    const float innerBandHalfWidth = std::max(8.0f, previewRadius * 0.015f);
    const float animatedArcHalfWidth = std::max(8.0f, previewRadius * 0.012f);
    const uint32_t glowInnerColor = withAlpha(previewColor, static_cast<uint8_t>(86 + std::lround(24.0f * slowPulse)));
    const uint32_t glowOuterColor = withAlpha(previewColor, 0);
    const uint32_t mainInnerColor = withAlpha(previewColor, static_cast<uint8_t>(230 + std::lround(20.0f * pulse)));
    const uint32_t mainOuterColor = withAlpha(previewColor, static_cast<uint8_t>(92 + std::lround(24.0f * pulse)));
    const uint32_t innerColor = withAlpha(previewColor, static_cast<uint8_t>(168 + std::lround(52.0f * pulse)));
    const uint32_t innerFadeColor = withAlpha(previewColor, static_cast<uint8_t>(18 + std::lround(10.0f * pulse)));
    const uint32_t tickColor = withAlpha(previewColor, 240);
    const uint32_t arcColor = withAlpha(previewColor, static_cast<uint8_t>(176 + std::lround(48.0f * slowPulse)));

    if (bgfx::isValid(view.m_spellAreaPreviewProgramHandle)
        && bgfx::isValid(view.m_spellAreaPreviewParams0UniformHandle)
        && bgfx::isValid(view.m_spellAreaPreviewParams1UniformHandle)
        && bgfx::isValid(view.m_spellAreaPreviewColorAUniformHandle)
        && bgfx::isValid(view.m_spellAreaPreviewColorBUniformHandle))
    {
        const auto buildSpellAreaPreviewVertices =
            [&view, &targetPoint, previewRadius, PreviewHeightOffset]() -> std::vector<OutdoorGameView::TexturedTerrainVertex>
            {
                std::vector<OutdoorGameView::TexturedTerrainVertex> texturedVertices;
                texturedVertices.reserve(SpellAreaPreviewGridResolution * SpellAreaPreviewGridResolution * 12);
                const float fullDiameter = previewRadius * 2.0f;
                const float cellSize = fullDiameter / static_cast<float>(SpellAreaPreviewGridResolution);
                const float cellHalfSize = cellSize * 0.5f;

                const auto samplePreviewWorldPoint =
                    [&view, &targetPoint, PreviewHeightOffset](float x, float y) -> bx::Vec3
                    {
                        const float terrainZ =
                            view.m_pOutdoorMapData != nullptr
                                ? sampleOutdoorRenderedTerrainHeight(*view.m_pOutdoorMapData, x, y)
                                : targetPoint->z;
                        const float supportZ = view.m_pOutdoorWorldRuntime->sampleSupportFloorHeight(
                            x,
                            y,
                            targetPoint->z + 1024.0f,
                            2048.0f,
                            24.0f);
                        const float z = std::max(terrainZ, supportZ);
                        return {x, y, z + PreviewHeightOffset + 1.0f};
                    };

                const auto appendVertex =
                    [&texturedVertices](const bx::Vec3 &position, float u, float v)
                    {
                        OutdoorGameView::TexturedTerrainVertex vertex = {};
                        vertex.x = position.x;
                        vertex.y = position.y;
                        vertex.z = position.z;
                        vertex.u = u;
                        vertex.v = v;
                        texturedVertices.push_back(vertex);
                    };

                for (size_t yIndex = 0; yIndex < SpellAreaPreviewGridResolution; ++yIndex)
                {
                    const float v0 = static_cast<float>(yIndex) / static_cast<float>(SpellAreaPreviewGridResolution);
                    const float v1 = static_cast<float>(yIndex + 1) / static_cast<float>(SpellAreaPreviewGridResolution);
                    const float localY0 = (v0 - 0.5f) * previewRadius * 2.0f;
                    const float localY1 = (v1 - 0.5f) * previewRadius * 2.0f;

                    for (size_t xIndex = 0; xIndex < SpellAreaPreviewGridResolution; ++xIndex)
                    {
                        const float u0 = static_cast<float>(xIndex) / static_cast<float>(SpellAreaPreviewGridResolution);
                        const float u1 = static_cast<float>(xIndex + 1) / static_cast<float>(SpellAreaPreviewGridResolution);
                        const float localX0 = (u0 - 0.5f) * previewRadius * 2.0f;
                        const float localX1 = (u1 - 0.5f) * previewRadius * 2.0f;
                        const float localCenterX = (localX0 + localX1) * 0.5f;
                        const float localCenterY = (localY0 + localY1) * 0.5f;
                        const float nearestX = std::max(std::abs(localCenterX) - cellHalfSize, 0.0f);
                        const float nearestY = std::max(std::abs(localCenterY) - cellHalfSize, 0.0f);

                        if (nearestX * nearestX + nearestY * nearestY > previewRadius * previewRadius)
                        {
                            continue;
                        }

                        const bx::Vec3 topLeft =
                            samplePreviewWorldPoint(targetPoint->x + localX0, targetPoint->y + localY0);
                        const bx::Vec3 topRight =
                            samplePreviewWorldPoint(targetPoint->x + localX1, targetPoint->y + localY0);
                        const bx::Vec3 bottomLeft =
                            samplePreviewWorldPoint(targetPoint->x + localX0, targetPoint->y + localY1);
                        const bx::Vec3 bottomRight =
                            samplePreviewWorldPoint(targetPoint->x + localX1, targetPoint->y + localY1);
                        const float centerU = (u0 + u1) * 0.5f;
                        const float centerV = (v0 + v1) * 0.5f;
                        const bx::Vec3 center =
                            samplePreviewWorldPoint(targetPoint->x + localCenterX, targetPoint->y + localCenterY);

                        appendVertex(topLeft, u0, v0);
                        appendVertex(topRight, u1, v0);
                        appendVertex(center, centerU, centerV);

                        appendVertex(topRight, u1, v0);
                        appendVertex(bottomRight, u1, v1);
                        appendVertex(center, centerU, centerV);

                        appendVertex(bottomRight, u1, v1);
                        appendVertex(bottomLeft, u0, v1);
                        appendVertex(center, centerU, centerV);

                        appendVertex(bottomLeft, u0, v1);
                        appendVertex(topLeft, u0, v0);
                        appendVertex(center, centerU, centerV);
                    }
                }

                return texturedVertices;
            };
        const float deltaX = targetPoint->x - view.m_spellAreaPreviewCache.targetX;
        const float deltaY = targetPoint->y - view.m_spellAreaPreviewCache.targetY;
        const float deltaZ = targetPoint->z - view.m_spellAreaPreviewCache.targetZ;
        const float retargetDistanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        const bool needsRefresh =
            !view.m_spellAreaPreviewCache.valid
            || view.m_spellAreaPreviewCache.spellId != markerPolicy->spellId
            || std::abs(view.m_spellAreaPreviewCache.radius - previewRadius) > 0.01f
            || retargetDistanceSquared >= SpellAreaPreviewRetargetDistance * SpellAreaPreviewRetargetDistance;
        const bool refreshAllowed =
            !view.m_spellAreaPreviewCache.valid
            || view.m_elapsedTime - view.m_spellAreaPreviewCache.lastRefreshElapsedTime
                >= SpellAreaPreviewRefreshIntervalSeconds;

        if (needsRefresh && refreshAllowed)
        {
            view.m_spellAreaPreviewCache.vertices = buildSpellAreaPreviewVertices();
            view.m_spellAreaPreviewCache.valid = !view.m_spellAreaPreviewCache.vertices.empty();
            view.m_spellAreaPreviewCache.spellId = markerPolicy->spellId;
            view.m_spellAreaPreviewCache.targetX = targetPoint->x;
            view.m_spellAreaPreviewCache.targetY = targetPoint->y;
            view.m_spellAreaPreviewCache.targetZ = targetPoint->z;
            view.m_spellAreaPreviewCache.radius = previewRadius;
            view.m_spellAreaPreviewCache.lastRefreshElapsedTime = view.m_elapsedTime;
        }

        const std::vector<OutdoorGameView::TexturedTerrainVertex> &texturedVertices =
            view.m_spellAreaPreviewCache.vertices;

        if (!texturedVertices.empty()
            && bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(texturedVertices.size()),
                OutdoorGameView::TexturedTerrainVertex::ms_layout) >= texturedVertices.size())
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(texturedVertices.size()),
                OutdoorGameView::TexturedTerrainVertex::ms_layout);
            std::memcpy(
                transientVertexBuffer.data,
                texturedVertices.data(),
                static_cast<size_t>(
                    texturedVertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex)));

            const uint32_t baseColorAbgr = markerPolicy->baseColorAbgr;
            const uint32_t accentColorAbgr = markerPolicy->accentColorAbgr;
            const std::array<float, 4> params0 = {
                view.m_elapsedTime,
                markerPolicy->shaderSpeed,
                0.86f,
                0.0f
            };
            const std::array<float, 4> params1 = {
                markerPolicy->shaderFrequency,
                markerPolicy->shaderPrimaryBandWidth,
                markerPolicy->shaderSecondaryBandWidth,
                0.0f
            };
            const std::array<float, 4> colorA = {
                redChannel(baseColorAbgr),
                greenChannel(baseColorAbgr),
                blueChannel(baseColorAbgr),
                1.0f
            };
            const std::array<float, 4> colorB = {
                redChannel(accentColorAbgr),
                greenChannel(accentColorAbgr),
                blueChannel(accentColorAbgr),
                1.0f
            };

            float modelMatrix[16] = {};
            bx::mtxIdentity(modelMatrix);
            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(texturedVertices.size()));
            const OutdoorWorldRuntime::AtmosphereState *pAtmosphereState =
                view.m_pOutdoorWorldRuntime != nullptr ? &view.m_pOutdoorWorldRuntime->atmosphereState() : nullptr;
            const float fogDistance =
                pAtmosphereState != nullptr ? pAtmosphereState->visibilityDistance : 200000.0f;
            const OutdoorFogParameters fogParameters =
                buildOutdoorWorldFogParameters(view.m_pOutdoorWorldRuntime, pAtmosphereState, fogDistance);
            applyOutdoorFogUniforms(
                view.m_outdoorFogColorUniformHandle,
                view.m_outdoorFogDensitiesUniformHandle,
                view.m_outdoorFogDistancesUniformHandle,
                view.m_outdoorCameraPositionUniformHandle,
                cameraPosition,
                fogParameters);
            bgfx::setUniform(view.m_spellAreaPreviewParams0UniformHandle, params0.data());
            bgfx::setUniform(view.m_spellAreaPreviewParams1UniformHandle, params1.data());
            bgfx::setUniform(view.m_spellAreaPreviewColorAUniformHandle, colorA.data());
            bgfx::setUniform(view.m_spellAreaPreviewColorBUniformHandle, colorB.data());
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(viewId, view.m_spellAreaPreviewProgramHandle);
            return;
        }
    }

    std::vector<OutdoorGameView::TerrainVertex> vertices;
    vertices.reserve(RingSegments * 36);

    const auto samplePreviewPoint =
        [&](float angleRadians, float radius) -> bx::Vec3
        {
            const float x = targetPoint->x + std::cos(angleRadians) * radius;
            const float y = targetPoint->y + std::sin(angleRadians) * radius;
            const float z = view.m_pOutdoorWorldRuntime->sampleSupportFloorHeight(
                x,
                y,
                targetPoint->z + 1024.0f,
                2048.0f,
                24.0f);
            return {x, y, z + PreviewHeightOffset};
        };

    const auto appendBandSegment =
        [&vertices](
            const bx::Vec3 &inner0,
            const bx::Vec3 &outer0,
            const bx::Vec3 &inner1,
            const bx::Vec3 &outer1,
            uint32_t innerColor0,
            uint32_t outerColor0,
            uint32_t innerColor1,
            uint32_t outerColor1)
        {
            vertices.push_back({inner0.x, inner0.y, inner0.z, innerColor0});
            vertices.push_back({outer0.x, outer0.y, outer0.z, outerColor0});
            vertices.push_back({inner1.x, inner1.y, inner1.z, innerColor1});

            vertices.push_back({inner1.x, inner1.y, inner1.z, innerColor1});
            vertices.push_back({outer0.x, outer0.y, outer0.z, outerColor0});
            vertices.push_back({outer1.x, outer1.y, outer1.z, outerColor1});
        };

    const auto appendRingBand =
        [&](float radiusInner, float radiusOuter, uint32_t innerColorBand, uint32_t outerColorBand, size_t step)
        {
            for (size_t segmentIndex = 0; segmentIndex < RingSegments; segmentIndex += step)
            {
                const float angle0 = 2.0f * Pi * static_cast<float>(segmentIndex) / static_cast<float>(RingSegments);
                const float angle1 = 2.0f * Pi * static_cast<float>(segmentIndex + step) / static_cast<float>(RingSegments);
                appendBandSegment(
                    samplePreviewPoint(angle0, radiusInner),
                    samplePreviewPoint(angle0, radiusOuter),
                    samplePreviewPoint(angle1, radiusInner),
                    samplePreviewPoint(angle1, radiusOuter),
                    innerColorBand,
                    outerColorBand,
                    innerColorBand,
                    outerColorBand);
            }
        };

    appendRingBand(
        previewRadius - glowBandHalfWidth,
        previewRadius + glowBandHalfWidth * 1.35f,
        glowInnerColor,
        glowOuterColor,
        1);

    appendRingBand(
        previewRadius - mainBandHalfWidth,
        previewRadius + mainBandHalfWidth,
        mainInnerColor,
        mainOuterColor,
        1);

    for (size_t segmentIndex = 0; segmentIndex < RingSegments; segmentIndex += 2)
    {
        const float angle0 = 2.0f * Pi * static_cast<float>(segmentIndex) / static_cast<float>(RingSegments);
        const float angle1 = 2.0f * Pi * static_cast<float>(segmentIndex + 1) / static_cast<float>(RingSegments);
        appendBandSegment(
            samplePreviewPoint(angle0, innerRingRadius - innerBandHalfWidth),
            samplePreviewPoint(angle0, innerRingRadius + innerBandHalfWidth),
            samplePreviewPoint(angle1, innerRingRadius - innerBandHalfWidth),
            samplePreviewPoint(angle1, innerRingRadius + innerBandHalfWidth),
            innerColor,
            innerFadeColor,
            innerColor,
            innerFadeColor);
    }

    constexpr size_t TickCount = 8;

    for (size_t tickIndex = 0; tickIndex < TickCount; ++tickIndex)
    {
        const float angle = 2.0f * Pi * static_cast<float>(tickIndex) / static_cast<float>(TickCount);
        const float angleWidth = Pi / 192.0f;
        appendBandSegment(
            samplePreviewPoint(angle - angleWidth, previewRadius - tickLength),
            samplePreviewPoint(angle + angleWidth, previewRadius),
            samplePreviewPoint(angle + angleWidth, previewRadius - tickLength),
            samplePreviewPoint(angle + angleWidth * 2.0f, previewRadius),
            tickColor,
            withAlpha(tickColor, 0),
            tickColor,
            withAlpha(tickColor, 0));
    }

    constexpr size_t AnimatedArcCount = 3;
    constexpr size_t AnimatedArcSpanSegments = 7;
    const float animatedPhase = view.m_elapsedTime * 0.65f;

    for (size_t arcIndex = 0; arcIndex < AnimatedArcCount; ++arcIndex)
    {
        const float arcCenterAngle = animatedPhase + 2.0f * Pi * static_cast<float>(arcIndex) / static_cast<float>(AnimatedArcCount);
        const int centerSegment = static_cast<int>(std::floor(
            arcCenterAngle / (2.0f * Pi) * static_cast<float>(RingSegments)));

        for (size_t localSegment = 0; localSegment < AnimatedArcSpanSegments; ++localSegment)
        {
            const int segmentIndex = (centerSegment + static_cast<int>(localSegment)) % static_cast<int>(RingSegments);
            const int nextSegmentIndex = (segmentIndex + 1) % static_cast<int>(RingSegments);
            const float age = static_cast<float>(localSegment) / static_cast<float>(AnimatedArcSpanSegments);
            const float fade = 1.0f - smoothstep(0.0f, 1.0f, age);
            const uint8_t alpha = static_cast<uint8_t>(std::lround(220.0f * fade));
            const uint32_t arcInnerColor = withAlpha(arcColor, alpha);
            const uint32_t arcOuterColor = withAlpha(arcColor, static_cast<uint8_t>(std::lround(64.0f * fade)));
            const float angle0 = 2.0f * Pi * static_cast<float>(segmentIndex) / static_cast<float>(RingSegments);
            const float angle1 = 2.0f * Pi * static_cast<float>(nextSegmentIndex) / static_cast<float>(RingSegments);

            appendBandSegment(
                samplePreviewPoint(angle0, previewRadius - animatedArcHalfWidth),
                samplePreviewPoint(angle0, previewRadius + animatedArcHalfWidth),
                samplePreviewPoint(angle1, previewRadius - animatedArcHalfWidth),
                samplePreviewPoint(angle1, previewRadius + animatedArcHalfWidth),
                arcInnerColor,
                arcOuterColor,
                arcInnerColor,
                arcOuterColor);
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
        | BGFX_STATE_DEPTH_TEST_LEQUAL
        | BGFX_STATE_BLEND_ALPHA
    );
    bgfx::submit(viewId, view.m_programHandle);
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
    if (pAtmosphereState == nullptr)
    {
        return;
    }

    const OutdoorGameView::SkyTextureHandle *pTexture = ensureSkyTexture(view, pAtmosphereState->skyTextureName);

    if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle) || viewWidth == 0 || viewHeight == 0)
    {
        return;
    }

    if (!bgfx::isValid(view.m_forcePerspectiveSolidTextureHandle))
    {
        const uint32_t whitePixel = 0xffffffffu;
        view.m_forcePerspectiveSolidTextureHandle = bgfx::createTexture2D(
            1,
            1,
            false,
            1,
            bgraTextureUploadFormat(),
            BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT,
            copyBgraTextureUploadMemory(reinterpret_cast<const uint8_t *>(&whitePixel), sizeof(whitePixel)));
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

    const float skyLeftX = 0.0f;
    const float skyRightX = static_cast<float>(viewWidth);
    // Keep cloud size and drift independent of the selected sky asset resolution.
    const OutdoorSkyVertex topLeft = computeOutdoorSkyVertex(
        skyLeftX,
        0.0f,
        static_cast<float>(viewWidth),
        static_cast<float>(viewHeight),
        cameraPosition.z,
        cameraYawRadians,
        cameraPitchRadians,
        renderDistance,
        view.m_elapsedTime,
        static_cast<float>(pTexture->width),
        static_cast<float>(pTexture->height));
    const OutdoorSkyVertex bottomLeft = computeOutdoorSkyVertex(
        skyLeftX,
        skyBottomY,
        static_cast<float>(viewWidth),
        static_cast<float>(viewHeight),
        cameraPosition.z,
        cameraYawRadians,
        cameraPitchRadians,
        renderDistance,
        view.m_elapsedTime,
        static_cast<float>(pTexture->width),
        static_cast<float>(pTexture->height));
    const OutdoorSkyVertex bottomRight = computeOutdoorSkyVertex(
        skyRightX,
        skyBottomY,
        static_cast<float>(viewWidth),
        static_cast<float>(viewHeight),
        cameraPosition.z,
        cameraYawRadians,
        cameraPitchRadians,
        renderDistance,
        view.m_elapsedTime,
        static_cast<float>(pTexture->width),
        static_cast<float>(pTexture->height));
    const OutdoorSkyVertex topRight = computeOutdoorSkyVertex(
        skyRightX,
        0.0f,
        static_cast<float>(viewWidth),
        static_cast<float>(viewHeight),
        cameraPosition.z,
        cameraYawRadians,
        cameraPitchRadians,
        renderDistance,
        view.m_elapsedTime,
        static_cast<float>(pTexture->width),
        static_cast<float>(pTexture->height));
    const uint32_t skyTintAbgr =
        view.m_pOutdoorWorldRuntime != nullptr ? computeOutdoorSkyTintAbgr(*view.m_pOutdoorWorldRuntime) : 0xffffffffu;
    view.m_cachedSkyVertices[0] = {
        topLeft.screenX,
        topLeft.screenY,
        1.0f,
        topLeft.u,
        topLeft.v,
        1.0f,
        renderDistance,
        topLeft.reciprocalW,
        skyTintAbgr};
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
        topLeft.screenX,
        topLeft.screenY,
        1.0f,
        topLeft.u,
        topLeft.v,
        1.0f,
        renderDistance,
        topLeft.reciprocalW,
        skyTintAbgr};
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
        topRight.screenX,
        topRight.screenY,
        1.0f,
        topRight.u,
        topRight.v,
        1.0f,
        renderDistance,
        topRight.reciprocalW,
        skyTintAbgr};

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
    bindTexture(
        0,
        view.m_terrainTextureSamplerHandle,
        pTexture->textureHandle,
        TextureFilterProfile::Sky);
    applyOutdoorFogUniforms(
        view.m_outdoorFogColorUniformHandle,
        view.m_outdoorFogDensitiesUniformHandle,
        view.m_outdoorFogDistancesUniformHandle,
        view.m_outdoorCameraPositionUniformHandle,
        cameraPosition,
        skyFogParameters);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, view.m_outdoorForcePerspectiveProgramHandle);

    if (bgfx::isValid(view.m_forcePerspectiveSolidTextureHandle))
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
                skyRightX,
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
                skyRightX,
                lowerSkyTopY,
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[5] = {
                skyRightX,
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
                skyRightX,
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
                skyRightX,
                static_cast<float>(viewHeight),
                1.0f,
                0.5f,
                0.5f,
                1.0f,
                renderDistance,
                1.0f,
                opaqueSkyTintAbgr};
            pVertices[subSkyOffset + 5] = {
                skyRightX,
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
            bindTexture(
                0,
                view.m_terrainTextureSamplerHandle,
                view.m_forcePerspectiveSolidTextureHandle,
                TextureFilterProfile::Ui);
            applyOutdoorFogUniforms(
                view.m_outdoorFogColorUniformHandle,
                view.m_outdoorFogDensitiesUniformHandle,
                view.m_outdoorFogDistancesUniformHandle,
                view.m_outdoorCameraPositionUniformHandle,
                cameraPosition,
                skyFogParameters);
            bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
            bgfx::submit(viewId, view.m_outdoorForcePerspectiveProgramHandle);
        }
    }
}

void OutdoorRenderer::renderOutdoorGameplayOverlay(
    OutdoorGameView &view,
    uint16_t viewId,
    float overlayAlpha,
    uint32_t overlayColorAbgr)
{
    if (!bgfx::isValid(view.m_screenTintProgramHandle) || overlayAlpha <= 0.0f
        || bgfx::getAvailTransientVertexBuffer(6, OutdoorGameView::TerrainVertex::ms_layout) < 6)
    {
        return;
    }

    const uint8_t alpha = static_cast<uint8_t>(std::clamp(std::lround(overlayAlpha * 255.0f), 0l, 255l));
    const uint32_t abgr = (overlayColorAbgr & 0x00ffffffu) | (static_cast<uint32_t>(alpha) << 24);
    const std::array<OutdoorGameView::TerrainVertex, 6> vertices = {{
        {-1.0f,  1.0f, 0.5f, abgr},
        {-1.0f, -1.0f, 0.5f, abgr},
        { 1.0f, -1.0f, 0.5f, abgr},
        {-1.0f,  1.0f, 0.5f, abgr},
        { 1.0f, -1.0f, 0.5f, abgr},
        { 1.0f,  1.0f, 0.5f, abgr}
    }};

    bgfx::TransientVertexBuffer transientVertexBuffer = {};
    bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, OutdoorGameView::TerrainVertex::ms_layout);
    std::memcpy(transientVertexBuffer.data, vertices.data(), sizeof(vertices));
    bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, 6);
    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
    bgfx::submit(viewId, view.m_screenTintProgramHandle);
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
            const float minZ = view.m_pOutdoorMapData != nullptr
                ? resolveActorAabbBaseZ(
                    *view.m_pOutdoorMapData,
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

            if (overlayDistanceSquared > view.m_viewDistanceCache.actorBillboardDistanceSquared)
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
                pRuntimeActor != nullptr
                    ? pRuntimeActor->hostileToParty && !outdoorActorIsPartyControlled(pRuntimeActor->controlMode)
                    : !billboard.isFriendly);
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

            if (overlayDistanceSquared > view.m_viewDistanceCache.actorBillboardDistanceSquared)
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
                pRuntimeActor->hostileToParty && !outdoorActorIsPartyControlled(pRuntimeActor->controlMode));
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
