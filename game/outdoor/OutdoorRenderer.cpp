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
#include "game/fx/ParticleRenderer.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorLightingRuntime.h"
#include "game/render/TextureFiltering.h"
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
#include <functional>
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
constexpr float SkyProjectionPitchOffsetRadians = Pi / 64.0f;
constexpr float SkyFogHorizonPixels = 39.0f;
constexpr int32_t MapWeatherFoggy = 1;
constexpr float OutdoorFxLightRefreshIntervalSeconds = 1.0f / 60.0f;
constexpr float OutdoorTerrainChunkWorldSize = 4096.0f;
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
constexpr float ArpgModeOccludingBModelFaceAlpha = 0.36f;
constexpr float OutdoorRayEpsilon = 0.0001f;

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

uint64_t outdoorBModelFaceEdgeKey(size_t bModelIndex, uint16_t vertexA, uint16_t vertexB)
{
    const uint16_t minVertex = std::min(vertexA, vertexB);
    const uint16_t maxVertex = std::max(vertexA, vertexB);
    const uint64_t bModelKey = static_cast<uint64_t>(static_cast<uint32_t>(bModelIndex));
    return (bModelKey << 32) | (static_cast<uint64_t>(minVertex) << 16) | static_cast<uint64_t>(maxVertex);
}

void appendUniqueIndex(std::vector<size_t> &indices, size_t index)
{
    if (std::find(indices.begin(), indices.end(), index) == indices.end())
    {
        indices.push_back(index);
    }
}

float secretFaceVertexFlag(uint32_t attributes)
{
    return hasFaceAttribute(attributes, FaceAttribute::IsSecret) ? 1.0f : 0.0f;
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

bx::Vec3 outdoorRendererVecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

bx::Vec3 outdoorRendererVecCross(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
}

float outdoorRendererVecDot(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

float outdoorRendererVecLength(const bx::Vec3 &value)
{
    return std::sqrt(outdoorRendererVecDot(value, value));
}

bool intersectOutdoorRendererRayTriangle(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const bx::Vec3 &vertex0,
    const bx::Vec3 &vertex1,
    const bx::Vec3 &vertex2,
    float &distance)
{
    const bx::Vec3 edge1 = outdoorRendererVecSubtract(vertex1, vertex0);
    const bx::Vec3 edge2 = outdoorRendererVecSubtract(vertex2, vertex0);
    const bx::Vec3 pVector = outdoorRendererVecCross(rayDirection, edge2);
    const float determinant = outdoorRendererVecDot(edge1, pVector);

    if (std::fabs(determinant) <= OutdoorRayEpsilon)
    {
        return false;
    }

    const float inverseDeterminant = 1.0f / determinant;
    const bx::Vec3 tVector = outdoorRendererVecSubtract(rayOrigin, vertex0);
    const float barycentricU = outdoorRendererVecDot(tVector, pVector) * inverseDeterminant;

    if (barycentricU < 0.0f || barycentricU > 1.0f)
    {
        return false;
    }

    const bx::Vec3 qVector = outdoorRendererVecCross(tVector, edge1);
    const float barycentricV = outdoorRendererVecDot(rayDirection, qVector) * inverseDeterminant;

    if (barycentricV < 0.0f || barycentricU + barycentricV > 1.0f)
    {
        return false;
    }

    distance = outdoorRendererVecDot(edge2, qVector) * inverseDeterminant;
    return distance > OutdoorRayEpsilon;
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

    const uint64_t selectionBeginTickCount = pLightingStats != nullptr ? SDL_GetTicksNS() : 0;
    const OutdoorSelectedFxLights lights = lightingRuntime.selectForBounds(fallbackReferencePosition, bounds);

    bgfx::setUniform(positionsUniformHandle, lights.positions.data(), OutdoorSelectedFxLights::MaxLights);
    bgfx::setUniform(colorsUniformHandle, lights.colors.data(), OutdoorSelectedFxLights::MaxLights);
    bgfx::setUniform(paramsUniformHandle, lights.params.data());

    if (pLightingStats != nullptr)
    {
        ++pLightingStats->outdoorUniformApplications;
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
}

uint32_t computeOutdoorSkyTintAbgr(const OutdoorWorldRuntime &worldRuntime)
{
    const uint8_t brightness = outdoorClearDistanceFogBrightness(worldRuntime.gameMinutes());
    return makeAbgr(brightness, brightness, brightness);
}

uint32_t computeOutdoorSkyFogColorAbgr(const OutdoorWorldRuntime::AtmosphereState &atmosphereState)
{
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

std::vector<uint8_t> downsampleBgraRegion(const std::vector<uint8_t> &sourcePixels, int sourceWidth, int sourceHeight)
{
    if (sourceWidth <= 0
        || sourceHeight <= 0
        || sourcePixels.size() < static_cast<size_t>(sourceWidth * sourceHeight * 4))
    {
        return {};
    }

    const int targetWidth = std::max(1, (sourceWidth + 1) / 2);
    const int targetHeight = std::max(1, (sourceHeight + 1) / 2);
    std::vector<uint8_t> targetPixels(static_cast<size_t>(targetWidth * targetHeight * 4), 0);

    for (int targetY = 0; targetY < targetHeight; ++targetY)
    {
        for (int targetX = 0; targetX < targetWidth; ++targetX)
        {
            uint32_t blue = 0;
            uint32_t green = 0;
            uint32_t red = 0;
            uint32_t alpha = 0;
            uint32_t sampleCount = 0;

            for (int offsetY = 0; offsetY < 2; ++offsetY)
            {
                const int sourceY = targetY * 2 + offsetY;

                if (sourceY >= sourceHeight)
                {
                    continue;
                }

                for (int offsetX = 0; offsetX < 2; ++offsetX)
                {
                    const int sourceX = targetX * 2 + offsetX;

                    if (sourceX >= sourceWidth)
                    {
                        continue;
                    }

                    const size_t sourceOffset = static_cast<size_t>((sourceY * sourceWidth + sourceX) * 4);

                    blue += sourcePixels[sourceOffset + 0];
                    green += sourcePixels[sourceOffset + 1];
                    red += sourcePixels[sourceOffset + 2];
                    alpha += sourcePixels[sourceOffset + 3];
                    ++sampleCount;
                }
            }

            if (sampleCount == 0)
            {
                continue;
            }

            const size_t targetOffset = static_cast<size_t>((targetY * targetWidth + targetX) * 4);
            targetPixels[targetOffset + 0] = static_cast<uint8_t>((blue + sampleCount / 2) / sampleCount);
            targetPixels[targetOffset + 1] = static_cast<uint8_t>((green + sampleCount / 2) / sampleCount);
            targetPixels[targetOffset + 2] = static_cast<uint8_t>((red + sampleCount / 2) / sampleCount);
            targetPixels[targetOffset + 3] = static_cast<uint8_t>((alpha + sampleCount / 2) / sampleCount);
        }
    }

    return targetPixels;
}

std::vector<TerrainTextureAtlasMipPixels> buildTerrainAtlasMipPixels(
    const std::vector<uint8_t> &atlasPixels,
    int atlasWidth,
    int atlasHeight)
{
    std::vector<TerrainTextureAtlasMipPixels> mipPixels;

    if (atlasWidth <= 0
        || atlasHeight <= 0
        || atlasPixels.size() < static_cast<size_t>(atlasWidth * atlasHeight * 4))
    {
        return mipPixels;
    }

    TerrainTextureAtlasMipPixels baseMip = {};
    baseMip.width = atlasWidth;
    baseMip.height = atlasHeight;
    baseMip.pixels = atlasPixels;
    mipPixels.push_back(std::move(baseMip));

    while (mipPixels.back().width > 1 || mipPixels.back().height > 1)
    {
        const TerrainTextureAtlasMipPixels &previousMip = mipPixels.back();
        TerrainTextureAtlasMipPixels nextMip = {};
        nextMip.width = std::max(1, (previousMip.width + 1) / 2);
        nextMip.height = std::max(1, (previousMip.height + 1) / 2);
        nextMip.pixels = downsampleBgraRegion(previousMip.pixels, previousMip.width, previousMip.height);

        if (nextMip.pixels.empty())
        {
            break;
        }

        mipPixels.push_back(std::move(nextMip));
    }

    return mipPixels;
}

void updateTerrainAtlasTileTexture(
    bgfx::TextureHandle textureHandle,
    std::vector<TerrainTextureAtlasMipPixels> &atlasMipPixels,
    int atlasWidth,
    int atlasHeight,
    uint16_t innerAtlasX,
    uint16_t innerAtlasY,
    int tileSize,
    int tilePadding,
    const std::vector<uint8_t> &tilePixels)
{
    if (!bgfx::isValid(textureHandle)
        || atlasWidth <= 0
        || atlasHeight <= 0
        || tileSize <= 0
        || tilePadding < 0
        || atlasMipPixels.empty()
        || atlasMipPixels.front().width != atlasWidth
        || atlasMipPixels.front().height != atlasHeight
        || atlasMipPixels.front().pixels.size() < static_cast<size_t>(atlasWidth * atlasHeight * 4)
        || tilePixels.size() < static_cast<size_t>(tileSize * tileSize * 4))
    {
        return;
    }

    const int paddedTileSize = tileSize + tilePadding * 2;
    std::vector<uint8_t> paddedPixels(static_cast<size_t>(paddedTileSize * paddedTileSize * 4), 0);

    for (int paddedY = 0; paddedY < paddedTileSize; ++paddedY)
    {
        const int sourceY = std::clamp(paddedY - tilePadding, 0, tileSize - 1);

        for (int paddedX = 0; paddedX < paddedTileSize; ++paddedX)
        {
            const int sourceX = std::clamp(paddedX - tilePadding, 0, tileSize - 1);
            const size_t sourceOffset = static_cast<size_t>((sourceY * tileSize + sourceX) * 4);
            const size_t targetOffset = static_cast<size_t>((paddedY * paddedTileSize + paddedX) * 4);
            std::memcpy(
                paddedPixels.data() + static_cast<ptrdiff_t>(targetOffset),
                tilePixels.data() + static_cast<ptrdiff_t>(sourceOffset),
                4);
        }
    }

    const int atlasX = innerAtlasX - tilePadding;
    const int atlasY = innerAtlasY - tilePadding;
    TerrainTextureAtlasMipPixels &baseMip = atlasMipPixels.front();

    for (int paddedY = 0; paddedY < paddedTileSize; ++paddedY)
    {
        const int targetY = atlasY + paddedY;

        if (targetY < 0 || targetY >= atlasHeight)
        {
            continue;
        }

        for (int paddedX = 0; paddedX < paddedTileSize; ++paddedX)
        {
            const int targetX = atlasX + paddedX;

            if (targetX < 0 || targetX >= atlasWidth)
            {
                continue;
            }

            const size_t sourceOffset = static_cast<size_t>((paddedY * paddedTileSize + paddedX) * 4);
            const size_t targetOffset = static_cast<size_t>((targetY * atlasWidth + targetX) * 4);
            std::memcpy(
                baseMip.pixels.data() + static_cast<ptrdiff_t>(targetOffset),
                paddedPixels.data() + static_cast<ptrdiff_t>(sourceOffset),
                4);
        }
    }

    for (uint8_t mipLevel = 0; mipLevel < atlasMipPixels.size(); ++mipLevel)
    {
        const int mipScale = 1 << mipLevel;
        TerrainTextureAtlasMipPixels &targetMip = atlasMipPixels[mipLevel];
        const int mipX0 = atlasX / mipScale;
        const int mipY0 = atlasY / mipScale;
        const int mipX1 = std::min(targetMip.width, (atlasX + paddedTileSize + mipScale - 1) / mipScale);
        const int mipY1 = std::min(targetMip.height, (atlasY + paddedTileSize + mipScale - 1) / mipScale);
        const int updateWidth = std::max(1, mipX1 - mipX0);
        const int updateHeight = std::max(1, mipY1 - mipY0);
        std::vector<uint8_t> updatePixels(static_cast<size_t>(updateWidth * updateHeight * 4), 0);

        if (mipLevel == 0)
        {
            updatePixels = paddedPixels;
        }
        else
        {
            const TerrainTextureAtlasMipPixels &sourceMip = atlasMipPixels[mipLevel - 1];

            for (int targetY = 0; targetY < updateHeight; ++targetY)
            {
                const int mipY = mipY0 + targetY;

                for (int targetX = 0; targetX < updateWidth; ++targetX)
                {
                    const int mipX = mipX0 + targetX;
                    uint32_t blue = 0;
                    uint32_t green = 0;
                    uint32_t red = 0;
                    uint32_t alpha = 0;
                    uint32_t sampleCount = 0;

                    for (int offsetY = 0; offsetY < 2; ++offsetY)
                    {
                        const int sourceY = mipY * 2 + offsetY;

                        if (sourceY >= sourceMip.height)
                        {
                            continue;
                        }

                        for (int offsetX = 0; offsetX < 2; ++offsetX)
                        {
                            const int sourceX = mipX * 2 + offsetX;

                            if (sourceX >= sourceMip.width)
                            {
                                continue;
                            }

                            const size_t sourceOffset =
                                static_cast<size_t>((sourceY * sourceMip.width + sourceX) * 4);
                            blue += sourceMip.pixels[sourceOffset + 0];
                            green += sourceMip.pixels[sourceOffset + 1];
                            red += sourceMip.pixels[sourceOffset + 2];
                            alpha += sourceMip.pixels[sourceOffset + 3];
                            ++sampleCount;
                        }
                    }

                    if (sampleCount == 0)
                    {
                        continue;
                    }

                    const size_t updateOffset = static_cast<size_t>((targetY * updateWidth + targetX) * 4);
                    updatePixels[updateOffset + 0] = static_cast<uint8_t>((blue + sampleCount / 2) / sampleCount);
                    updatePixels[updateOffset + 1] = static_cast<uint8_t>((green + sampleCount / 2) / sampleCount);
                    updatePixels[updateOffset + 2] = static_cast<uint8_t>((red + sampleCount / 2) / sampleCount);
                    updatePixels[updateOffset + 3] = static_cast<uint8_t>((alpha + sampleCount / 2) / sampleCount);
                }
            }

            for (int targetY = 0; targetY < updateHeight; ++targetY)
            {
                const size_t sourceOffset = static_cast<size_t>(targetY * updateWidth * 4);
                const size_t targetOffset =
                    static_cast<size_t>(((mipY0 + targetY) * targetMip.width + mipX0) * 4);
                std::memcpy(
                    targetMip.pixels.data() + static_cast<ptrdiff_t>(targetOffset),
                    updatePixels.data() + static_cast<ptrdiff_t>(sourceOffset),
                    static_cast<size_t>(updateWidth * 4));
            }
        }

        bgfx::updateTexture2D(
            textureHandle,
            0,
            mipLevel,
            static_cast<uint16_t>(mipX0),
            static_cast<uint16_t>(mipY0),
            static_cast<uint16_t>(updateWidth),
            static_cast<uint16_t>(updateHeight),
            copyBgraTextureUploadMemory(updatePixels.data(), static_cast<uint32_t>(updatePixels.size())));

        if (targetMip.width == 1 && targetMip.height == 1)
        {
            break;
        }
    }
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

std::array<float, 3> outdoorBModelRuntimeOffset(
    const EventRuntimeState *pEventRuntimeState,
    size_t bModelIndex)
{
    if (pEventRuntimeState == nullptr)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    if (pEventRuntimeState->outdoorModelMechanisms.empty())
    {
        return {0.0f, 0.0f, 0.0f};
    }

    for (const std::pair<const uint32_t, EventRuntimeState::OutdoorModelMechanismDefinition> &entry :
        pEventRuntimeState->outdoorModelMechanisms)
    {
        const EventRuntimeState::OutdoorModelMechanismDefinition &definition = entry.second;

        if (definition.bmodelIndex != bModelIndex)
        {
            continue;
        }

        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator mechanismIterator =
            pEventRuntimeState->mechanisms.find(entry.first);

        if (mechanismIterator == pEventRuntimeState->mechanisms.end())
        {
            continue;
        }

        const RuntimeMechanismState &mechanism = mechanismIterator->second;
        const float moveTimeMs = std::max(1.0f, static_cast<float>(definition.moveTimeMs));
        float fraction = definition.closed ? 0.0f : 1.0f;

        if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Open))
        {
            fraction = 1.0f;
        }
        else if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closed))
        {
            fraction = 0.0f;
        }
        else if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
        {
            fraction = std::clamp(mechanism.timeSinceTriggeredMs / moveTimeMs, 0.0f, 1.0f);
        }
        else if (mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
        {
            fraction = 1.0f - std::clamp(mechanism.timeSinceTriggeredMs / moveTimeMs, 0.0f, 1.0f);
        }

        return {
            static_cast<float>(definition.dx) * fraction,
            static_cast<float>(definition.dy) * fraction,
            static_cast<float>(definition.dz) * fraction
        };
    }

    return {0.0f, 0.0f, 0.0f};
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
        const OutdoorFogProfile fogProfile = buildOutdoorFogProfile(
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
        const OutdoorFogProfile fogProfile = buildOutdoorFogProfile(
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

void OutdoorRenderer::applySecretPulseUniforms(OutdoorGameView &view)
{
    if (!bgfx::isValid(view.m_secretPulseParamsUniformHandle))
    {
        return;
    }

    const bool secretFacesDetected =
        view.m_map.has_value()
        && view.m_pOutdoorPartyRuntime != nullptr
        && GameMechanics::partyDetectsSecretFaces(view.m_pOutdoorPartyRuntime->party(), view.m_map.value());
    const std::array<float, 4> params = {
        secretFacesDetected ? 1.0f : 0.0f,
        view.m_elapsedTime,
        0.0f,
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
    }
}

bool OutdoorRenderer::makeOutdoorBModelOcclusionRay(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &point,
    BModelOcclusionRay &ray)
{
    const bx::Vec3 toPoint = outdoorRendererVecSubtract(point, rayOrigin);
    const float pointDistance = outdoorRendererVecLength(toPoint);

    if (pointDistance <= OutdoorRayEpsilon)
    {
        return false;
    }

    constexpr float BoundsPadding = 16.0f;
    ray = {};
    ray.origin = rayOrigin;
    ray.point = point;
    ray.direction = {
        toPoint.x / pointDistance,
        toPoint.y / pointDistance,
        toPoint.z / pointDistance
    };
    ray.distance = pointDistance;
    ray.minX = std::min(rayOrigin.x, point.x) - BoundsPadding;
    ray.maxX = std::max(rayOrigin.x, point.x) + BoundsPadding;
    ray.minY = std::min(rayOrigin.y, point.y) - BoundsPadding;
    ray.maxY = std::max(rayOrigin.y, point.y) + BoundsPadding;
    ray.minZ = std::min(rayOrigin.z, point.z) - BoundsPadding;
    ray.maxZ = std::max(rayOrigin.z, point.z) + BoundsPadding;
    return true;
}

void OutdoorRenderer::updateTexturedBModelBatchBounds(OutdoorGameView::TexturedBModelBatch &batch)
{
    batch.hasBounds = false;

    if (batch.vertices.empty())
    {
        return;
    }

    batch.boundsMin = {batch.vertices.front().x, batch.vertices.front().y, batch.vertices.front().z};
    batch.boundsMax = batch.boundsMin;

    for (const OutdoorGameView::TexturedTerrainVertex &vertex : batch.vertices)
    {
        batch.boundsMin.x = std::min(batch.boundsMin.x, vertex.x);
        batch.boundsMax.x = std::max(batch.boundsMax.x, vertex.x);
        batch.boundsMin.y = std::min(batch.boundsMin.y, vertex.y);
        batch.boundsMax.y = std::max(batch.boundsMax.y, vertex.y);
        batch.boundsMin.z = std::min(batch.boundsMin.z, vertex.z);
        batch.boundsMax.z = std::max(batch.boundsMax.z, vertex.z);
    }

    batch.hasBounds = true;
}

bool OutdoorRenderer::outdoorBModelBatchOccludesPoint(
    const OutdoorGameView::TexturedBModelBatch &batch,
    const EventRuntimeState *pEventRuntimeState,
    const BModelOcclusionRay &ray)
{
    if (!batch.hasBounds || batch.vertices.size() < 3)
    {
        return false;
    }

    const std::array<float, 3> bmodelOffset = outdoorBModelRuntimeOffset(pEventRuntimeState, batch.bModelIndex);
    const float minX = batch.boundsMin.x + bmodelOffset[0];
    const float maxX = batch.boundsMax.x + bmodelOffset[0];
    const float minY = batch.boundsMin.y + bmodelOffset[1];
    const float maxY = batch.boundsMax.y + bmodelOffset[1];
    const float minZ = batch.boundsMin.z + bmodelOffset[2];
    const float maxZ = batch.boundsMax.z + bmodelOffset[2];

    if (maxX < ray.minX
        || minX > ray.maxX
        || maxY < ray.minY
        || minY > ray.maxY
        || maxZ < ray.minZ
        || minZ > ray.maxZ)
    {
        return false;
    }

    for (size_t vertexIndex = 0; vertexIndex + 2 < batch.vertices.size(); vertexIndex += 3)
    {
        const OutdoorGameView::TexturedTerrainVertex &vertex0 = batch.vertices[vertexIndex];
        const OutdoorGameView::TexturedTerrainVertex &vertex1 = batch.vertices[vertexIndex + 1];
        const OutdoorGameView::TexturedTerrainVertex &vertex2 = batch.vertices[vertexIndex + 2];
        const bx::Vec3 triangleVertex0 = {
            vertex0.x + bmodelOffset[0],
            vertex0.y + bmodelOffset[1],
            vertex0.z + bmodelOffset[2]
        };
        const bx::Vec3 triangleVertex1 = {
            vertex1.x + bmodelOffset[0],
            vertex1.y + bmodelOffset[1],
            vertex1.z + bmodelOffset[2]
        };
        const bx::Vec3 triangleVertex2 = {
            vertex2.x + bmodelOffset[0],
            vertex2.y + bmodelOffset[1],
            vertex2.z + bmodelOffset[2]
        };
        float distance = 0.0f;

        if (intersectOutdoorRendererRayTriangle(
                ray.origin,
                ray.direction,
                triangleVertex0,
                triangleVertex1,
                triangleVertex2,
                distance)
            && distance > 16.0f
            && distance + 8.0f < ray.distance)
        {
            return true;
        }
    }

    return false;
}

void OutdoorRenderer::destroyResolvedBModelDrawGroupVector(
    std::vector<OutdoorGameView::ResolvedBModelDrawGroup> &groups)
{
    for (OutdoorGameView::ResolvedBModelDrawGroup &group : groups)
    {
        if (bgfx::isValid(group.vertexBufferHandle))
        {
            bgfx::destroy(group.vertexBufferHandle);
            group.vertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        group.vertexCount = 0;
        group.animationIndex = static_cast<size_t>(-1);
    }

    groups.clear();
}

uint64_t outdoorBModelOcclusionMaskHash(const std::vector<uint8_t> &mask)
{
    uint64_t hash = 1469598103934665603ull;

    for (uint8_t value : mask)
    {
        hash ^= static_cast<uint64_t>(value);
        hash *= 1099511628211ull;
    }

    hash ^= static_cast<uint64_t>(mask.size());
    hash *= 1099511628211ull;
    return hash;
}

void OutdoorRenderer::rebuildResolvedBModelDrawGroupVector(
    OutdoorGameView &view,
    std::vector<OutdoorGameView::ResolvedBModelDrawGroup> &drawGroups,
    const std::vector<uint8_t> *pSkipBatchMask)
{
    destroyResolvedBModelDrawGroupVector(drawGroups);

    if (view.m_texturedBModelBatches.empty() || view.m_bmodelTextureAnimations.empty())
    {
        return;
    }

    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const MapDeltaData *pMapDeltaData =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
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

    std::vector<std::vector<OutdoorGameView::TexturedTerrainVertex>> verticesByAnimationIndex(
        view.m_bmodelTextureAnimations.size());
    std::vector<OutdoorLightSelectionBounds> boundsByAnimationIndex(view.m_bmodelTextureAnimations.size());

    for (size_t batchIndex = 0; batchIndex < view.m_texturedBModelBatches.size(); ++batchIndex)
    {
        if (pSkipBatchMask != nullptr
            && batchIndex < pSkipBatchMask->size()
            && (*pSkipBatchMask)[batchIndex] != 0)
        {
            continue;
        }

        const OutdoorGameView::TexturedBModelBatch &batch = view.m_texturedBModelBatches[batchIndex];

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

        if (animationIndex >= verticesByAnimationIndex.size())
        {
            continue;
        }

        std::vector<OutdoorGameView::TexturedTerrainVertex> &groupVertices = verticesByAnimationIndex[animationIndex];
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

        if (view.m_outdoorMapData
            && batch.bModelIndex < view.m_outdoorMapData->bmodels.size()
            && batch.faceIndex < view.m_outdoorMapData->bmodels[batch.bModelIndex].faces.size())
        {
            OutdoorBModelFace effectiveFace =
                view.m_outdoorMapData->bmodels[batch.bModelIndex].faces[batch.faceIndex];
            effectiveFace.attributes = effectiveAttributes;
            flowInfo = outdoorFaceFlowInfo(effectiveFace, batch.textureWidth, batch.textureHeight);
        }

        const float secretPulse = secretFaceVertexFlag(effectiveAttributes);
        const size_t oldSize = groupVertices.size();
        groupVertices.insert(groupVertices.end(), batch.vertices.begin(), batch.vertices.end());
        const std::array<float, 3> bmodelOffset =
            outdoorBModelRuntimeOffset(pEventRuntimeState, batch.bModelIndex);

        for (size_t vertexIndex = oldSize; vertexIndex < groupVertices.size(); ++vertexIndex)
        {
            groupVertices[vertexIndex].x += bmodelOffset[0];
            groupVertices[vertexIndex].y += bmodelOffset[1];
            groupVertices[vertexIndex].z += bmodelOffset[2];
            groupVertices[vertexIndex].secretPulse = secretPulse;
            groupVertices[vertexIndex].flowUPerSecond = flowInfo[0];
            groupVertices[vertexIndex].flowVPerSecond = flowInfo[1];
            groupVertices[vertexIndex].lavaFlow = flowInfo[2];
            groupVertices[vertexIndex].fluidFlow = flowInfo[3];
        }

        boundsByAnimationIndex[animationIndex] = boundsFromTexturedVertices(groupVertices);
    }

    drawGroups.reserve(view.m_bmodelTextureAnimations.size());

    for (size_t animationIndex = 0; animationIndex < verticesByAnimationIndex.size(); ++animationIndex)
    {
        const std::vector<OutdoorGameView::TexturedTerrainVertex> &groupVertices =
            verticesByAnimationIndex[animationIndex];

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
        group.boundsMin = boundsByAnimationIndex[animationIndex].min;
        group.boundsMax = boundsByAnimationIndex[animationIndex].max;
        group.hasBounds = boundsByAnimationIndex[animationIndex].valid;
        drawGroups.push_back(group);
    }
}

void OutdoorRenderer::destroyResolvedBModelDrawGroups(OutdoorGameView &view)
{
    destroyResolvedBModelDrawGroupVector(view.m_resolvedBModelDrawGroups);
    view.m_resolvedBModelDrawGroups.clear();
    view.m_resolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();
    destroyResolvedBModelDrawGroupVector(view.m_arpgModeResolvedBModelDrawGroups);
    view.m_arpgModeResolvedBModelDrawGroups.clear();
    view.m_arpgModeResolvedBModelDrawGroupRevision = std::numeric_limits<uint64_t>::max();
    view.m_arpgModeResolvedBModelOcclusionHash = 0;
    view.m_arpgModeBModelBatchNeighbors.clear();
}

void OutdoorRenderer::rebuildResolvedBModelDrawGroups(OutdoorGameView &view)
{
    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
    const MapDeltaData *pMapDeltaData =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
    const uint64_t targetRevision = outdoorSurfaceVisualRevision(pMapDeltaData, pEventRuntimeState);
    rebuildResolvedBModelDrawGroupVector(view, view.m_resolvedBModelDrawGroups, nullptr);
    view.m_resolvedBModelDrawGroupRevision = targetRevision;
}

void OutdoorRenderer::initializeAnimatedWaterTileState(
    OutdoorGameView &view,
    const std::optional<OutdoorTerrainTextureAtlas> &outdoorTerrainTextureAtlas)
{
    view.m_animatedWaterTerrainTiles.clear();
    view.m_lastAnimatedWaterAnimationTicks.reset();
    view.m_terrainTextureAtlasMipPixels.clear();
    view.m_terrainTextureAtlasWidth = 0;
    view.m_terrainTextureAtlasHeight = 0;

    if (!outdoorTerrainTextureAtlas || outdoorTerrainTextureAtlas->animatedWaterTiles.empty())
    {
        return;
    }

    view.m_terrainTextureAtlasWidth = outdoorTerrainTextureAtlas->width;
    view.m_terrainTextureAtlasHeight = outdoorTerrainTextureAtlas->height;
    view.m_terrainTextureAtlasMipPixels = buildTerrainAtlasMipPixels(
        outdoorTerrainTextureAtlas->pixels,
        outdoorTerrainTextureAtlas->width,
        outdoorTerrainTextureAtlas->height);
    view.m_animatedWaterTerrainTiles.reserve(outdoorTerrainTextureAtlas->animatedWaterTiles.size());

    for (const OutdoorAnimatedWaterTileSource &source : outdoorTerrainTextureAtlas->animatedWaterTiles)
    {
        OutdoorGameView::AnimatedWaterTerrainTileState tileState = {};
        tileState.region = source.region;
        tileState.tilePadding = outdoorTerrainTextureAtlas->tilePadding;
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
    if (!bgfx::isValid(view.m_terrainTextureAtlasHandle)
        || view.m_animatedWaterTerrainTiles.empty()
        || view.m_terrainTextureAtlasMipPixels.empty()
        || view.m_terrainTextureAtlasWidth <= 0
        || view.m_terrainTextureAtlasHeight <= 0)
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

        const int atlasWidth = view.m_terrainTextureAtlasWidth;
        const int atlasHeight = view.m_terrainTextureAtlasHeight;

        if (atlasWidth <= 0 || atlasHeight <= 0)
        {
            continue;
        }

        const uint16_t atlasX = static_cast<uint16_t>(
            std::lround(tileState.region.u0 * static_cast<float>(atlasWidth)));
        const uint16_t atlasY = static_cast<uint16_t>(
            std::lround(tileState.region.v0 * static_cast<float>(atlasHeight)));

        updateTerrainAtlasTileTexture(
            view.m_terrainTextureAtlasHandle,
            view.m_terrainTextureAtlasMipPixels,
            view.m_terrainTextureAtlasWidth,
            view.m_terrainTextureAtlasHeight,
            atlasX,
            atlasY,
            tileSize,
            tileState.tilePadding,
            framePixels);

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

            if (region.isWater && !region.isTransitionOverlay)
            {
                for (OutdoorGameView::TexturedTerrainVertex *pVertex :
                    {&topLeft, &topRight, &bottomLeft, &bottomRight})
                {
                    pVertex->secretPulse = -1.0f;
                    pVertex->flowUPerSecond = region.u0;
                    pVertex->flowVPerSecond = region.v0;
                    pVertex->lavaFlow = region.u1;
                    pVertex->fluidFlow = region.v1;
                }
            }

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
            vertex.secretPulse = secretFaceVertexFlag(face.attributes);
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
    std::unordered_map<uint64_t, std::vector<size_t>> batchIndicesByEdge;

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
            updateTexturedBModelBatchBounds(batch);
            batch.faceId = faceId;
            batch.cogNumber = face.cogNumber;
            batch.baseAttributes = face.attributes;
            batch.bModelIndex = bModelIndex;
            batch.faceIndex = localFaceIndex;
            batch.polygonType = face.polygonType;
            batch.textureWidth = pBaseTexture->width;
            batch.textureHeight = pBaseTexture->height;
            batch.textureName = toLowerCopy(face.textureName);
            const OutdoorLightSelectionBounds batchBounds = boundsFromTexturedVertices(batch.vertices);
            batch.boundsMin = batchBounds.min;
            batch.boundsMax = batchBounds.max;
            batch.hasBounds = batchBounds.valid;
            const auto animationIndexIterator = animationIndexByTextureName.find(batch.textureName);

            if (animationIndexIterator != animationIndexByTextureName.end())
            {
                batch.defaultAnimationIndex = animationIndexIterator->second;
            }

            const size_t batchIndex = view.m_texturedBModelBatches.size();
            for (size_t vertexIndex = 0; vertexIndex < face.vertexIndices.size(); ++vertexIndex)
            {
                const uint16_t vertexA = face.vertexIndices[vertexIndex];
                const uint16_t vertexB = face.vertexIndices[(vertexIndex + 1) % face.vertexIndices.size()];
                batchIndicesByEdge[outdoorBModelFaceEdgeKey(bModelIndex, vertexA, vertexB)].push_back(batchIndex);
            }

            view.m_texturedBModelBatches.push_back(std::move(batch));
        }
    }

    view.m_arpgModeBModelBatchNeighbors.clear();
    view.m_arpgModeBModelBatchNeighbors.resize(view.m_texturedBModelBatches.size());

    for (const std::pair<const uint64_t, std::vector<size_t>> &entry : batchIndicesByEdge)
    {
        const std::vector<size_t> &edgeBatchIndices = entry.second;

        if (edgeBatchIndices.size() < 2)
        {
            continue;
        }

        for (size_t sourceBatchIndex : edgeBatchIndices)
        {
            for (size_t targetBatchIndex : edgeBatchIndices)
            {
                if (sourceBatchIndex != targetBatchIndex
                    && sourceBatchIndex < view.m_arpgModeBModelBatchNeighbors.size())
                {
                    appendUniqueIndex(view.m_arpgModeBModelBatchNeighbors[sourceBatchIndex], targetBatchIndex);
                }
            }
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
        buildTexturedTerrainChunks(view, texturedTerrainVertices);
    }
    else
    {
        destroyTexturedTerrainChunks(view);
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
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            if (!outdoorFaceHasInvisibleAttribute(face.attributes))
            {
                ++view.m_bmodelFaceCount;
            }
        }
    }

    view.m_programHandle = loadProgramHandle("vs_cubes", "fs_cubes");
    view.m_texturedTerrainProgramHandle = loadProgramHandle("vs_shadowmaps_texture", "fs_shadowmaps_texture");
    view.m_spellAreaPreviewProgramHandle = loadProgramHandle("vs_spell_area_preview", "fs_spell_area_preview");
    view.m_outdoorLitBillboardProgramHandle =
        loadProgramHandle("vs_outdoor_billboard_lit", "fs_outdoor_billboard_lit");
    view.m_worldFxRenderResources.setParticleProgramHandle(loadProgramHandle("vs_particle", "fs_particle"));
    view.m_worldFxRenderResources.setBeamProgramHandle(loadProgramHandle("vs_beam", "fs_beam"));
    view.m_outdoorTexturedFogProgramHandle =
        loadProgramHandle("vs_outdoor_textured_fog", "fs_outdoor_textured_fog");
    view.m_outdoorForcePerspectiveProgramHandle =
        loadProgramHandle("vs_outdoor_force_perspective", "fs_outdoor_force_perspective");

    if (outdoorTerrainTextureAtlas && !outdoorTerrainTextureAtlas->pixels.empty())
    {
        view.m_terrainTextureAtlasHandle = createBgraTexture2D(
            uint16_t(outdoorTerrainTextureAtlas->width),
            uint16_t(outdoorTerrainTextureAtlas->height),
            outdoorTerrainTextureAtlas->pixels.data(),
            uint32_t(outdoorTerrainTextureAtlas->pixels.size()),
            TextureFilterProfile::Terrain,
            BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
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

    std::optional<std::string> bitmapPath = view.findCachedAssetPath("sky_textures", textureName + ".png");

    if (!bitmapPath)
    {
        bitmapPath = view.findCachedAssetPath("sky_textures", textureName + ".bmp");
    }

    if (!bitmapPath)
    {
        return nullptr;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = view.readCachedBinaryFile(*bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return nullptr;
    }

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, *bitmapPath);

    if (!image)
    {
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
        return nullptr;
    }

    view.m_skyTextureHandles.push_back(std::move(textureHandle));
    view.m_skyTextureIndexByName[view.m_skyTextureHandles.back().textureName] = view.m_skyTextureHandles.size() - 1;
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
        || !bgfx::isValid(view.m_secretPulseParamsUniformHandle)
        || !bgfx::isValid(view.m_outdoorFaceAlphaParamsUniformHandle))
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
        fogParameters);
    applySecretPulseUniforms(view);
    const std::array<float, 4> faceAlphaParams = {1.0f, 0.0f, 0.0f, 0.0f};
    bgfx::setUniform(view.m_outdoorFaceAlphaParamsUniformHandle, faceAlphaParams.data());
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

        const std::array<float, 3> bmodelOffset =
            outdoorBModelRuntimeOffset(pEventRuntimeState, batch.bModelIndex);
        bx::Vec3 normal = {0.0f, 0.0f, 0.0f};

        if (view.m_outdoorMapData
            && batch.bModelIndex < view.m_outdoorMapData->bmodels.size()
            && batch.faceIndex < view.m_outdoorMapData->bmodels[batch.bModelIndex].faces.size())
        {
            OutdoorFaceGeometryData geometry = {};
            const OutdoorBModel &bmodel = view.m_outdoorMapData->bmodels[batch.bModelIndex];
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
            highlightVertices.push_back(
                {
                    vertex.x + bmodelOffset[0] + offset.x,
                    vertex.y + bmodelOffset[1] + offset.y,
                    vertex.z + bmodelOffset[2] + offset.z,
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
    const auto applyOutdoorFaceAlphaUniform =
        [&view](float alpha)
        {
            const std::array<float, 4> params = {alpha, 0.0f, 0.0f, 0.0f};
            bgfx::setUniform(view.m_outdoorFaceAlphaParamsUniformHandle, params.data());
        };
    std::function<void()> submitArpgModeTranslucentOccludingBModelFaces = []() {};
    view.m_outdoorLightingRuntime.build(view.m_worldFxSystem);
    const bool useLocalFxLighting =
        view.m_outdoorLightingRuntime.outputClusterLightCount() > OutdoorSelectedFxLights::MaxLights;

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
            && bgfx::isValid(view.m_outdoorTexturedFogProgramHandle)
            && bgfx::isValid(view.m_terrainTextureAtlasHandle)
            && bgfx::isValid(view.m_terrainTextureSamplerHandle)
            && bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle)
            && bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle)
            && bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle)
            && bgfx::isValid(view.m_secretPulseParamsUniformHandle)
            && bgfx::isValid(view.m_outdoorFaceAlphaParamsUniformHandle))
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

                    bgfx::setVertexBuffer(0, chunk.vertexBufferHandle, 0, chunk.vertexCount);
                    bindTexture(
                        0,
                        view.m_terrainTextureSamplerHandle,
                        view.m_terrainTextureAtlasHandle,
                        TextureFilterProfile::Terrain,
                        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                    OutdoorLightSelectionBounds chunkBounds = {};
                    chunkBounds.min = chunk.boundsMin;
                    chunkBounds.max = chunk.boundsMax;
                    chunkBounds.valid = true;
                    applyOutdoorFxLightUniformsForBounds(
                        view.m_outdoorFxLightPositionsUniformHandle,
                        view.m_outdoorFxLightColorsUniformHandle,
                        view.m_outdoorFxLightParamsUniformHandle,
                        view.m_outdoorLightingRuntime,
                        view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr,
                        cameraPosition,
                        chunkBounds);
                    applyOutdoorFogUniforms(
                        view.m_outdoorFogColorUniformHandle,
                        view.m_outdoorFogDensitiesUniformHandle,
                        view.m_outdoorFogDistancesUniformHandle,
                        worldFogParameters);
                    applySecretPulseUniforms(view);
                    applyOutdoorFaceAlphaUniform(1.0f);
                    bgfx::setState(
                        BGFX_STATE_WRITE_RGB
                        | BGFX_STATE_WRITE_A
                        | BGFX_STATE_WRITE_Z
                        | BGFX_STATE_DEPTH_TEST_LEQUAL
                    );
                    bgfx::submit(MainViewId, view.m_outdoorTexturedFogProgramHandle);
                }
            }
            else if (bgfx::isValid(view.m_texturedTerrainVertexBufferHandle))
            {
                bgfx::setVertexBuffer(0, view.m_texturedTerrainVertexBufferHandle);
                bindTexture(
                    0,
                    view.m_terrainTextureSamplerHandle,
                    view.m_terrainTextureAtlasHandle,
                    TextureFilterProfile::Terrain,
                    BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                applyOutdoorFxLightUniforms(view, cameraPosition);
                applyOutdoorFogUniforms(
                    view.m_outdoorFogColorUniformHandle,
                    view.m_outdoorFogDensitiesUniformHandle,
                    view.m_outdoorFogDistancesUniformHandle,
                    worldFogParameters);
                applySecretPulseUniforms(view);
                applyOutdoorFaceAlphaUniform(1.0f);
                bgfx::setState(
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LEQUAL
                );
                bgfx::submit(MainViewId, view.m_outdoorTexturedFogProgramHandle);
            }
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

    const auto submitTexturedBModelBatch =
        [&](const OutdoorGameView::TexturedBModelBatch &batch,
            const EventRuntimeState *pEventRuntimeState,
            const MapDeltaData *pMapDeltaData,
            float alpha,
            bool writeDepth)
        {
            if (batch.vertices.empty())
            {
                return;
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
                    const std::string normalizedOverrideTextureName = toLowerCopy(modelFacetOverrideIt->second);
                    animationIndex = static_cast<size_t>(-1);

                    for (size_t candidateIndex = 0; candidateIndex < view.m_bmodelTextureAnimations.size();
                         ++candidateIndex)
                    {
                        if (view.m_bmodelTextureAnimations[candidateIndex].textureName == normalizedOverrideTextureName)
                        {
                            animationIndex = candidateIndex;
                            break;
                        }
                    }
                }

                if (!hasModelFacetOverride)
                {
                    const auto textureOverrideIt = pEventRuntimeState->textureOverrides.find(batch.cogNumber);

                    if (textureOverrideIt != pEventRuntimeState->textureOverrides.end())
                    {
                        const std::string normalizedOverrideTextureName = toLowerCopy(textureOverrideIt->second);
                        animationIndex = static_cast<size_t>(-1);

                        for (size_t candidateIndex = 0; candidateIndex < view.m_bmodelTextureAnimations.size();
                             ++candidateIndex)
                        {
                            if (view.m_bmodelTextureAnimations[candidateIndex].textureName
                                == normalizedOverrideTextureName)
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
                return;
            }

            const OutdoorGameView::BModelTextureAnimationHandle &animation =
                view.m_bmodelTextureAnimations[animationIndex];

            if (animation.frameTextureHandles.empty())
            {
                return;
            }

            const size_t frameIndex = frameIndexForAnimation(
                animation.frameLengthTicks,
                animation.animationLengthTicks,
                static_cast<uint32_t>(std::lround(view.m_elapsedTime * 128.0f)));

            if (frameIndex >= animation.frameTextureHandles.size()
                || !bgfx::isValid(animation.frameTextureHandles[frameIndex]))
            {
                return;
            }

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

            if (view.m_outdoorMapData
                && batch.bModelIndex < view.m_outdoorMapData->bmodels.size()
                && batch.faceIndex < view.m_outdoorMapData->bmodels[batch.bModelIndex].faces.size())
            {
                OutdoorBModelFace effectiveFace =
                    view.m_outdoorMapData->bmodels[batch.bModelIndex].faces[batch.faceIndex];
                effectiveFace.attributes = effectiveAttributes;
                flowInfo = outdoorFaceFlowInfo(effectiveFace, batch.textureWidth, batch.textureHeight);
            }

            const float secretPulse = secretFaceVertexFlag(effectiveAttributes);
            const std::array<float, 3> bmodelOffset =
                outdoorBModelRuntimeOffset(pEventRuntimeState, batch.bModelIndex);
            std::vector<OutdoorGameView::TexturedTerrainVertex> vertices = batch.vertices;

            for (OutdoorGameView::TexturedTerrainVertex &vertex : vertices)
            {
                vertex.x += bmodelOffset[0];
                vertex.y += bmodelOffset[1];
                vertex.z += bmodelOffset[2];
                vertex.secretPulse = secretPulse;
                vertex.flowUPerSecond = flowInfo[0];
                vertex.flowVPerSecond = flowInfo[1];
                vertex.lavaFlow = flowInfo[2];
                vertex.fluidFlow = flowInfo[3];
            }

            const uint32_t vertexCount = static_cast<uint32_t>(vertices.size());

            if (bgfx::getAvailTransientVertexBuffer(
                    vertexCount,
                    OutdoorGameView::TexturedTerrainVertex::ms_layout) < vertexCount)
            {
                return;
            }

            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                vertexCount,
                OutdoorGameView::TexturedTerrainVertex::ms_layout);
            std::memcpy(
                transientVertexBuffer.data,
                vertices.data(),
                vertices.size() * sizeof(OutdoorGameView::TexturedTerrainVertex));

            bgfx::setTransform(modelMatrix);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, vertexCount);
            bindTexture(
                0,
                view.m_terrainTextureSamplerHandle,
                animation.frameTextureHandles[frameIndex],
                TextureFilterProfile::BModel);
            if (useLocalFxLighting)
            {
                const OutdoorLightSelectionBounds batchBounds = boundsFromTexturedVertices(vertices);
                applyOutdoorFxLightUniformsForBounds(
                    view.m_outdoorFxLightPositionsUniformHandle,
                    view.m_outdoorFxLightColorsUniformHandle,
                    view.m_outdoorFxLightParamsUniformHandle,
                    view.m_outdoorLightingRuntime,
                    view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr,
                    cameraPosition,
                    batchBounds);
            }
            else
            {
                applyOutdoorFxLightUniforms(view, cameraPosition);
            }
            applyOutdoorFogUniforms(
                view.m_outdoorFogColorUniformHandle,
                view.m_outdoorFogDensitiesUniformHandle,
                view.m_outdoorFogDistancesUniformHandle,
                worldFogParameters);
            applySecretPulseUniforms(view);
            applyOutdoorFaceAlphaUniform(alpha);

            uint64_t renderState =
                BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_DEPTH_TEST_LEQUAL;

            if (writeDepth)
            {
                renderState |= BGFX_STATE_WRITE_Z;
            }

            if (alpha < 0.999f)
            {
                renderState |= BGFX_STATE_BLEND_ALPHA;
            }

            bgfx::setState(renderState);
            bgfx::submit(MainViewId, view.m_outdoorTexturedFogProgramHandle);
        };

    const auto submitResolvedBModelDrawGroups =
        [&](const std::vector<OutdoorGameView::ResolvedBModelDrawGroup> &drawGroups)
        {
            for (const OutdoorGameView::ResolvedBModelDrawGroup &group : drawGroups)
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
                bindTexture(
                    0,
                    view.m_terrainTextureSamplerHandle,
                    animation.frameTextureHandles[frameIndex],
                    TextureFilterProfile::BModel);
                if (useLocalFxLighting)
                {
                    OutdoorLightSelectionBounds groupBounds = {};
                    groupBounds.min = group.boundsMin;
                    groupBounds.max = group.boundsMax;
                    groupBounds.valid = group.hasBounds;
                    applyOutdoorFxLightUniformsForBounds(
                        view.m_outdoorFxLightPositionsUniformHandle,
                        view.m_outdoorFxLightColorsUniformHandle,
                        view.m_outdoorFxLightParamsUniformHandle,
                        view.m_outdoorLightingRuntime,
                        view.m_gameSettings.performanceTrace ? &view.m_outdoorLightingStats : nullptr,
                        cameraPosition,
                        groupBounds);
                }
                else
                {
                    applyOutdoorFxLightUniforms(view, cameraPosition);
                }
                applyOutdoorFogUniforms(
                    view.m_outdoorFogColorUniformHandle,
                    view.m_outdoorFogDensitiesUniformHandle,
                    view.m_outdoorFogDistancesUniformHandle,
                    worldFogParameters);
                applySecretPulseUniforms(view);
                applyOutdoorFaceAlphaUniform(1.0f);
                bgfx::setState(
                    BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LEQUAL
                );
                bgfx::submit(MainViewId, view.m_outdoorTexturedFogProgramHandle);
            }
        };

    {
        if (view.m_showBModels
            && bgfx::isValid(view.m_bmodelVertexBufferHandle)
            && view.m_bmodelLineVertexCount > 0)
        {
            const EventRuntimeState *pEventRuntimeState =
                view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;
            const MapDeltaData *pMapDeltaData =
                view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->mapDeltaData() : nullptr;
            const uint64_t targetRevision = outdoorSurfaceVisualRevision(pMapDeltaData, pEventRuntimeState);
            const bool arpgModeOccludingBModelFaces =
                view.arpgModeEnabled()
                && view.m_pOutdoorPartyRuntime != nullptr
                && view.m_outdoorMapData.has_value();

            if (bgfx::isValid(view.m_outdoorTexturedFogProgramHandle)
                && bgfx::isValid(view.m_terrainTextureSamplerHandle)
                && bgfx::isValid(view.m_outdoorFxLightPositionsUniformHandle)
                && bgfx::isValid(view.m_outdoorFxLightColorsUniformHandle)
                && bgfx::isValid(view.m_outdoorFxLightParamsUniformHandle)
                && bgfx::isValid(view.m_secretPulseParamsUniformHandle)
                && bgfx::isValid(view.m_outdoorFaceAlphaParamsUniformHandle))
            {
                std::vector<uint8_t> arpgModeOccludingBModelBatchMask;
                bool arpgModeHasOccludingBModelBatch = false;

                if (arpgModeOccludingBModelFaces)
                {
                    arpgModeOccludingBModelBatchMask.assign(view.m_texturedBModelBatches.size(), 0);
                    std::vector<size_t> arpgModeDirectOccludingBModelBatchIndices;
                    const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
                    const std::array<bx::Vec3, 3> puppetSamples = {{
                        {moveState.x, moveState.y, moveState.footZ + 72.0f},
                        {moveState.x, moveState.y, moveState.footZ + 128.0f},
                        {moveState.x, moveState.y, moveState.footZ + 192.0f}
                    }};
                    std::array<BModelOcclusionRay, 3> occlusionRays = {};
                    size_t occlusionRayCount = 0;

                    for (const bx::Vec3 &sample : puppetSamples)
                    {
                        BModelOcclusionRay ray = {};

                        if (makeOutdoorBModelOcclusionRay(cameraPosition, sample, ray))
                        {
                            occlusionRays[occlusionRayCount] = ray;
                            ++occlusionRayCount;
                        }
                    }

                    for (size_t batchIndex = 0; batchIndex < view.m_texturedBModelBatches.size(); ++batchIndex)
                    {
                        const OutdoorGameView::TexturedBModelBatch &batch = view.m_texturedBModelBatches[batchIndex];

                        if (batch.vertices.empty()
                            || outdoorFaceHiddenByEventRuntime(
                                batch.faceId,
                                batch.baseAttributes,
                                pMapDeltaData,
                                pEventRuntimeState))
                        {
                            continue;
                        }

                        for (size_t rayIndex = 0; rayIndex < occlusionRayCount; ++rayIndex)
                        {
                            if (outdoorBModelBatchOccludesPoint(
                                    batch,
                                    pEventRuntimeState,
                                    occlusionRays[rayIndex]))
                            {
                                arpgModeOccludingBModelBatchMask[batchIndex] = 1;
                                arpgModeDirectOccludingBModelBatchIndices.push_back(batchIndex);
                                arpgModeHasOccludingBModelBatch = true;
                                break;
                            }
                        }
                    }

                    for (size_t batchIndex : arpgModeDirectOccludingBModelBatchIndices)
                    {
                        if (batchIndex >= view.m_arpgModeBModelBatchNeighbors.size())
                        {
                            continue;
                        }

                        for (size_t neighborBatchIndex : view.m_arpgModeBModelBatchNeighbors[batchIndex])
                        {
                            if (neighborBatchIndex >= arpgModeOccludingBModelBatchMask.size()
                                || neighborBatchIndex >= view.m_texturedBModelBatches.size())
                            {
                                continue;
                            }

                            const OutdoorGameView::TexturedBModelBatch &neighborBatch =
                                view.m_texturedBModelBatches[neighborBatchIndex];

                            if (neighborBatch.vertices.empty()
                                || outdoorFaceHiddenByEventRuntime(
                                    neighborBatch.faceId,
                                    neighborBatch.baseAttributes,
                                    pMapDeltaData,
                                    pEventRuntimeState))
                            {
                                continue;
                            }

                            arpgModeOccludingBModelBatchMask[neighborBatchIndex] = 1;
                            arpgModeHasOccludingBModelBatch = true;
                        }
                    }
                }

                if (arpgModeOccludingBModelFaces && arpgModeHasOccludingBModelBatch)
                {
                    const uint64_t occlusionHash = outdoorBModelOcclusionMaskHash(arpgModeOccludingBModelBatchMask);

                    if (view.m_arpgModeResolvedBModelDrawGroupRevision != targetRevision
                        || view.m_arpgModeResolvedBModelOcclusionHash != occlusionHash)
                    {
                        rebuildResolvedBModelDrawGroupVector(
                            view,
                            view.m_arpgModeResolvedBModelDrawGroups,
                            &arpgModeOccludingBModelBatchMask);
                        view.m_arpgModeResolvedBModelDrawGroupRevision = targetRevision;
                        view.m_arpgModeResolvedBModelOcclusionHash = occlusionHash;
                    }

                    submitResolvedBModelDrawGroups(view.m_arpgModeResolvedBModelDrawGroups);
                }
                else
                {
                    if (view.m_resolvedBModelDrawGroupRevision != targetRevision)
                    {
                        rebuildResolvedBModelDrawGroups(view);
                    }

                    submitResolvedBModelDrawGroups(view.m_resolvedBModelDrawGroups);
                }

                for (size_t batchIndex = 0; batchIndex < view.m_texturedBModelBatches.size(); ++batchIndex)
                {
                    const OutdoorGameView::TexturedBModelBatch &batch = view.m_texturedBModelBatches[batchIndex];

                    if (!outdoorBModelHasRuntimeMechanism(pEventRuntimeState, batch.bModelIndex)
                        || batch.vertices.empty()
                        || (!arpgModeOccludingBModelBatchMask.empty()
                            && arpgModeOccludingBModelBatchMask[batchIndex] != 0)
                        || outdoorFaceHiddenByEventRuntime(
                            batch.faceId,
                            batch.baseAttributes,
                            pMapDeltaData,
                            pEventRuntimeState))
                    {
                        continue;
                    }

                    submitTexturedBModelBatch(batch, pEventRuntimeState, pMapDeltaData, 1.0f, true);
                }

                if (arpgModeHasOccludingBModelBatch)
                {
                    submitArpgModeTranslucentOccludingBModelFaces =
                        [&, pEventRuntimeState, pMapDeltaData, arpgModeOccludingBModelBatchMask]()
                        {
                            for (size_t batchIndex = 0;
                                 batchIndex < arpgModeOccludingBModelBatchMask.size()
                                    && batchIndex < view.m_texturedBModelBatches.size();
                                 ++batchIndex)
                            {
                                if (arpgModeOccludingBModelBatchMask[batchIndex] == 0)
                                {
                                    continue;
                                }

                                const OutdoorGameView::TexturedBModelBatch &batch =
                                    view.m_texturedBModelBatches[batchIndex];

                                if (batch.vertices.empty()
                                    || outdoorFaceHiddenByEventRuntime(
                                        batch.faceId,
                                        batch.baseAttributes,
                                        pMapDeltaData,
                                        pEventRuntimeState))
                                {
                                    continue;
                                }

                                submitTexturedBModelBatch(
                                    batch,
                                    pEventRuntimeState,
                                    pMapDeltaData,
                                    ArpgModeOccludingBModelFaceAlpha,
                                    false);
                            }
                        };
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

    renderBloodSplats(view, MainViewId, cameraPosition, farClipDistance, useLocalFxLighting);
    renderContextActionGeometryHighlight(view, MainViewId);

    if (view.m_gameSettings.shadows && (view.m_showSpriteObjects || view.m_showActors))
    {
        OutdoorBillboardRenderer::renderFxContactShadows(view, MainViewId);
    }

    if (view.m_showSpriteObjects)
    {
        OutdoorBillboardRenderer::renderRuntimeWorldItems(view, MainViewId, pViewMatrix, cameraPosition);
        OutdoorBillboardRenderer::renderRuntimeProjectiles(view, MainViewId, pViewMatrix, cameraPosition);
        OutdoorBillboardRenderer::renderSpriteObjectBillboards(view, MainViewId, pViewMatrix, cameraPosition);
    }

    if (view.m_showActors || view.m_showDecorationBillboards)
    {
        OutdoorBillboardRenderer::renderActorPreviewBillboards(view, MainViewId, pViewMatrix, cameraPosition);

        if (view.m_showActors && view.m_showActorCollisionBoxes)
        {
            renderActorCollisionOverlays(view, MainViewId, cameraPosition);
        }
    }

    if (view.m_showSpriteObjects || view.m_showActors || view.m_showDecorationBillboards)
    {
        OutdoorBillboardRenderer::renderFxGlowBillboards(view, MainViewId, pViewMatrix);
    }

    submitArpgModeTranslucentOccludingBModelFaces();

    renderPendingSpellAreaPreview(view, MainViewId);

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

    ParticleRenderer::renderBeams(
        view.m_worldFxRenderResources,
        view.m_worldFxSystem.beams(),
        MainViewId,
        pViewMatrix,
        cameraPosition);

    if (view.m_showSpriteObjects || view.m_showActors || view.m_showDecorationBillboards)
    {
        ParticleRenderer::renderParticles(
            view.m_worldFxRenderResources,
            view.m_worldFxSystem.particles(),
            MainViewId,
            pViewMatrix,
            cameraPosition,
            aspectRatio);
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

    if (pAtmosphereState != nullptr && pAtmosphereState->gameplayOverlayAlpha > 0.001f)
    {
        renderOutdoorDarknessOverlay(
            view,
            MainViewId,
            cameraPosition,
            cameraForward,
            cameraRight,
            cameraUp,
            aspectRatio,
            pAtmosphereState->gameplayOverlayAlpha,
            pAtmosphereState->gameplayOverlayColorAbgr);
    }
}

void OutdoorRenderer::renderPendingSpellAreaPreview(OutdoorGameView &view, uint16_t viewId)
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
        view.m_pOutdoorWorldRuntime->spellActionGroundTargetPoint(pInputFrame->pointerX, pInputFrame->pointerY);

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
                            view.m_outdoorMapData.has_value()
                                ? sampleOutdoorRenderedTerrainHeight(*view.m_outdoorMapData, x, y)
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
            bindTexture(
                0,
                view.m_terrainTextureSamplerHandle,
                view.m_forcePerspectiveSolidTextureHandle,
                TextureFilterProfile::Ui);
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
