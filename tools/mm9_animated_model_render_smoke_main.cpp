#include "engine/BgfxContext.h"
#include "game/mm9/Mm9DtxTexture.h"
#include "game/maps/Mm9EventsYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/mm9/Mm9AnimatedActorBinding.h"
#include "game/mm9/Mm9AnimatedActorVisual.h"
#include "game/mm9/Mm9AnimatedModelResolver.h"
#include "game/mm9/Mm9AnimatedModelSidecar.h"
#include "game/mm9/Mm9ScriptedObjectRuntime.h"
#include "game/render/AnimatedModelAsset.h"
#include "game/render/AnimatedModelRenderer.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{
constexpr uint16_t SmokeViewId = 0;
constexpr uint16_t SmokeBlitViewId = 1;
constexpr uint16_t SmokeWidth = 640;
constexpr uint16_t SmokeHeight = 480;

struct Arguments
{
    std::filesystem::path modelPath;
    std::filesystem::path sidecarPath;
    std::filesystem::path scenePath;
    std::filesystem::path eventsPath;
    std::filesystem::path registryPath;
    std::filesystem::path textureRoot = "assets_dev/worlds/mm9/source";
    std::string mapId = "guberland";
    std::string clipName = "stand";
    float timeSeconds = 0.5f;
    std::optional<size_t> objectIndex;
    bool requirePixels = false;
};

struct RenderSubject
{
    OpenYAMM::Game::AnimatedModelRenderPrep renderPrep;
    OpenYAMM::Game::AnimatedModelBounds bounds;
    OpenYAMM::Game::AnimatedModelMat4 modelToWorld;
    std::filesystem::path modelPath;
    std::string clipName;
    std::string mapId;
    std::string objectId;
    std::string sourceName;
    size_t sourceObjectIndex = 0;
    bool fromRuntimeBinding = false;
};

struct PixelStats
{
    uint8_t maxRed = 0;
    uint8_t maxGreen = 0;
    uint8_t maxBlue = 0;
    size_t litPixels = 0;
};

void printUsage()
{
    std::cerr
        << "usage: mm9_animated_model_render_smoke"
        << " --model <path.glb>"
        << " --sidecar <path.model.yml>"
        << " [--texture-root <assets_dev/worlds/mm9/source>]"
        << " [--clip <name>]"
        << " [--time-ms <ms>]"
        << "\n       mm9_animated_model_render_smoke"
        << " --scene <guberland.scene.yml>"
        << " --events <guberland.events.yml>"
        << " --registry <model_registry.yml>"
        << " [--map-id guberland]"
        << " [--object-index <source_object_index>]"
        << " [--texture-root <assets_dev/worlds/mm9/source>]"
        << " [--time-ms <ms>]"
        << " [--require-pixels]\n";
}

bool parseArguments(int argc, char **argv, Arguments &arguments)
{
    for (int index = 1; index < argc; ++index)
    {
        const std::string name = argv[index];
        const auto readValue =
            [argc, argv, &index, &name](std::string &value) -> bool
            {
                if (index + 1 >= argc)
                {
                    std::cerr << "missing value for " << name << '\n';
                    return false;
                }
                value = argv[++index];
                return true;
            };

        if (name == "--model")
        {
            std::string value;
            if (!readValue(value))
            {
                return false;
            }
            arguments.modelPath = value;
        }
        else if (name == "--sidecar")
        {
            std::string value;
            if (!readValue(value))
            {
                return false;
            }
            arguments.sidecarPath = value;
        }
        else if (name == "--clip")
        {
            if (!readValue(arguments.clipName))
            {
                return false;
            }
        }
        else if (name == "--texture-root")
        {
            std::string value;
            if (!readValue(value))
            {
                return false;
            }
            arguments.textureRoot = value;
        }
        else if (name == "--scene")
        {
            std::string value;
            if (!readValue(value))
            {
                return false;
            }
            arguments.scenePath = value;
        }
        else if (name == "--events")
        {
            std::string value;
            if (!readValue(value))
            {
                return false;
            }
            arguments.eventsPath = value;
        }
        else if (name == "--registry")
        {
            std::string value;
            if (!readValue(value))
            {
                return false;
            }
            arguments.registryPath = value;
        }
        else if (name == "--map-id")
        {
            if (!readValue(arguments.mapId))
            {
                return false;
            }
        }
        else if (name == "--object-index")
        {
            std::string value;
            if (!readValue(value))
            {
                return false;
            }
            arguments.objectIndex = static_cast<size_t>(std::stoull(value));
        }
        else if (name == "--time-ms")
        {
            std::string value;
            if (!readValue(value))
            {
                return false;
            }
            arguments.timeSeconds = std::stof(value) / 1000.0f;
        }
        else if (name == "--require-pixels")
        {
            arguments.requirePixels = true;
        }
        else
        {
            std::cerr << "unknown argument: " << name << '\n';
            return false;
        }
    }

    const bool directModelMode = !arguments.modelPath.empty() && !arguments.sidecarPath.empty();
    const bool runtimeBindingMode =
        !arguments.scenePath.empty() && !arguments.eventsPath.empty() && !arguments.registryPath.empty();
    return directModelMode != runtimeBindingMode;
}

float boundsRadius(const OpenYAMM::Game::AnimatedModelBounds &bounds)
{
    if (!bounds.valid)
    {
        return 1.0f;
    }

    const float dx = bounds.max.x - bounds.min.x;
    const float dy = bounds.max.y - bounds.min.y;
    const float dz = bounds.max.z - bounds.min.z;
    return std::max(std::sqrt(dx * dx + dy * dy + dz * dz) * 0.5f, 1.0f);
}

bx::Vec3 boundsCenter(const OpenYAMM::Game::AnimatedModelBounds &bounds)
{
    if (!bounds.valid)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {
        (bounds.min.x + bounds.max.x) * 0.5f,
        (bounds.min.y + bounds.max.y) * 0.5f,
        (bounds.min.z + bounds.max.z) * 0.5f};
}

OpenYAMM::Game::AnimatedModelVec3 transformPoint(
    const OpenYAMM::Game::AnimatedModelMat4 &matrix,
    const OpenYAMM::Game::AnimatedModelVec3 &point)
{
    return {
        matrix.values[0] * point.x + matrix.values[4] * point.y
            + matrix.values[8] * point.z + matrix.values[12],
        matrix.values[1] * point.x + matrix.values[5] * point.y
            + matrix.values[9] * point.z + matrix.values[13],
        matrix.values[2] * point.x + matrix.values[6] * point.y
            + matrix.values[10] * point.z + matrix.values[14]};
}

void expandBounds(
    OpenYAMM::Game::AnimatedModelBounds &bounds,
    const OpenYAMM::Game::AnimatedModelVec3 &point)
{
    if (!bounds.valid)
    {
        bounds.min = point;
        bounds.max = point;
        bounds.valid = true;
        return;
    }

    bounds.min.x = std::min(bounds.min.x, point.x);
    bounds.min.y = std::min(bounds.min.y, point.y);
    bounds.min.z = std::min(bounds.min.z, point.z);
    bounds.max.x = std::max(bounds.max.x, point.x);
    bounds.max.y = std::max(bounds.max.y, point.y);
    bounds.max.z = std::max(bounds.max.z, point.z);
}

OpenYAMM::Game::AnimatedModelBounds computeSkinnedBounds(
    const OpenYAMM::Game::AnimatedModelRenderPrep &renderPrep,
    const OpenYAMM::Game::AnimatedModelBounds &fallbackBounds)
{
    OpenYAMM::Game::AnimatedModelBounds bounds = {};
    for (const OpenYAMM::Game::AnimatedModelDrawItem &drawItem : renderPrep.drawItems)
    {
        for (const OpenYAMM::Game::AnimatedModelVertex &vertex : drawItem.vertices)
        {
            OpenYAMM::Game::AnimatedModelVec3 skinned = {};
            bool hasWeight = false;
            for (size_t slot = 0; slot < vertex.weights.size(); ++slot)
            {
                if (vertex.weights[slot] <= 0.0f || vertex.joints[slot] >= drawItem.bonePalette.size())
                {
                    continue;
                }

                const OpenYAMM::Game::AnimatedModelVec3 transformed =
                    transformPoint(drawItem.bonePalette[vertex.joints[slot]], vertex.position);
                skinned.x += transformed.x * vertex.weights[slot];
                skinned.y += transformed.y * vertex.weights[slot];
                skinned.z += transformed.z * vertex.weights[slot];
                hasWeight = true;
            }

            expandBounds(bounds, hasWeight ? skinned : vertex.position);
        }
    }

    return bounds.valid ? bounds : fallbackBounds;
}

OpenYAMM::Game::AnimatedModelMat4 identityMatrix()
{
    OpenYAMM::Game::AnimatedModelMat4 matrix = {};
    matrix.values[0] = 1.0f;
    matrix.values[5] = 1.0f;
    matrix.values[10] = 1.0f;
    matrix.values[15] = 1.0f;
    return matrix;
}

OpenYAMM::Game::AnimatedModelMat4 multiplyMatrix(
    const OpenYAMM::Game::AnimatedModelMat4 &a,
    const OpenYAMM::Game::AnimatedModelMat4 &b)
{
    OpenYAMM::Game::AnimatedModelMat4 result = {};
    result.values.fill(0.0f);

    for (size_t column = 0; column < 4; ++column)
    {
        for (size_t row = 0; row < 4; ++row)
        {
            for (size_t index = 0; index < 4; ++index)
            {
                result.values[column * 4 + row] +=
                    a.values[index * 4 + row] * b.values[column * 4 + index];
            }
        }
    }

    return result;
}

OpenYAMM::Game::AnimatedModelBounds transformBounds(
    const OpenYAMM::Game::AnimatedModelMat4 &matrix,
    const OpenYAMM::Game::AnimatedModelBounds &bounds)
{
    OpenYAMM::Game::AnimatedModelBounds result = {};
    if (!bounds.valid)
    {
        return result;
    }

    const float xs[2] = {bounds.min.x, bounds.max.x};
    const float ys[2] = {bounds.min.y, bounds.max.y};
    const float zs[2] = {bounds.min.z, bounds.max.z};
    for (const float x : xs)
    {
        for (const float y : ys)
        {
            for (const float z : zs)
            {
                expandBounds(result, transformPoint(matrix, {x, y, z}));
            }
        }
    }

    return result;
}

PixelStats bgraPixelStats(const std::vector<uint8_t> &pixels)
{
    PixelStats stats = {};
    for (size_t index = 0; index + 3 < pixels.size(); index += 4)
    {
        const uint8_t blue = pixels[index + 0];
        const uint8_t green = pixels[index + 1];
        const uint8_t red = pixels[index + 2];
        const uint8_t alpha = pixels[index + 3];
        stats.maxRed = std::max(stats.maxRed, red);
        stats.maxGreen = std::max(stats.maxGreen, green);
        stats.maxBlue = std::max(stats.maxBlue, blue);
        if (alpha != 0 && (red > 4 || green > 4 || blue > 4))
        {
            ++stats.litPixels;
        }
    }

    return stats;
}

PixelStats screenshotPixelStats(const OpenYAMM::Engine::BgfxContext::ScreenshotCapture &capture)
{
    return bgraPixelStats(capture.bgraPixels);
}

bgfx::TextureHandle createWhiteTexture()
{
    const uint8_t pixels[4] = {255, 255, 255, 255};
    return bgfx::createTexture2D(
        1,
        1,
        false,
        1,
        bgfx::TextureFormat::RGBA8,
        0,
        bgfx::copy(pixels, sizeof(pixels)));
}

std::optional<std::string> readTextFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    if (!file)
    {
        return std::nullopt;
    }

    std::ostringstream stream;
    stream << file.rdbuf();
    return stream.str();
}

std::string lowerCopy(const std::string &value)
{
    std::string output = value;
    std::transform(output.begin(), output.end(), output.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return output;
}

std::vector<std::string> splitTextureRef(const std::string &textureRef)
{
    std::string normalized = textureRef;
    std::replace(normalized.begin(), normalized.end(), '\\', '/');
    while (!normalized.empty() && normalized.front() == '/')
    {
        normalized.erase(normalized.begin());
    }

    std::vector<std::string> components;
    size_t cursor = 0;
    while (cursor < normalized.size())
    {
        const size_t separator = normalized.find('/', cursor);
        const size_t end = separator == std::string::npos ? normalized.size() : separator;
        if (end > cursor)
        {
            components.push_back(normalized.substr(cursor, end - cursor));
        }
        if (separator == std::string::npos)
        {
            break;
        }
        cursor = separator + 1;
    }
    return components;
}

std::optional<std::filesystem::path> resolveCaseInsensitivePath(
    const std::filesystem::path &root,
    const std::string &textureRef)
{
    std::filesystem::path current = root;
    if (!std::filesystem::exists(current))
    {
        return std::nullopt;
    }

    for (const std::string &component : splitTextureRef(textureRef))
    {
        const std::string componentKey = lowerCopy(component);
        bool found = false;
        for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(current))
        {
            if (lowerCopy(entry.path().filename().string()) == componentKey)
            {
                current = entry.path();
                found = true;
                break;
            }
        }
        if (!found)
        {
            return std::nullopt;
        }
    }

    return current;
}

std::vector<uint8_t> bgraToRgba(const std::vector<uint8_t> &pixelsBgra)
{
    std::vector<uint8_t> pixelsRgba = pixelsBgra;
    for (size_t index = 0; index + 3 < pixelsRgba.size(); index += 4)
    {
        std::swap(pixelsRgba[index + 0], pixelsRgba[index + 2]);
    }
    return pixelsRgba;
}

std::optional<bgfx::TextureHandle> loadTextureHandle(
    const std::filesystem::path &textureRoot,
    const std::string &textureRef,
    std::string &errorMessage)
{
    const std::optional<std::filesystem::path> texturePath =
        resolveCaseInsensitivePath(textureRoot, textureRef);
    if (!texturePath)
    {
        errorMessage = "could not resolve texture: " + textureRef;
        return std::nullopt;
    }

    std::optional<OpenYAMM::Game::Mm9DtxTexture> texture =
        OpenYAMM::Game::loadMm9DtxTexture(*texturePath, errorMessage);
    if (!texture)
    {
        errorMessage = "could not decode texture " + texturePath->string() + ": " + errorMessage;
        return std::nullopt;
    }

    const std::vector<uint8_t> pixelsRgba = bgraToRgba(texture->pixelsBgra);
    return bgfx::createTexture2D(
        static_cast<uint16_t>(texture->width),
        static_cast<uint16_t>(texture->height),
        false,
        1,
        bgfx::TextureFormat::RGBA8,
        0,
        bgfx::copy(pixelsRgba.data(), static_cast<uint32_t>(pixelsRgba.size())));
}

OpenYAMM::Game::AnimatedModelMat4 fitBoundsToClipMatrix(
    const OpenYAMM::Game::AnimatedModelBounds &bounds)
{
    OpenYAMM::Game::AnimatedModelMat4 matrix = {};
    const bx::Vec3 center = boundsCenter(bounds);
    const float dx = bounds.valid ? bounds.max.x - bounds.min.x : 1.0f;
    const float dy = bounds.valid ? bounds.max.y - bounds.min.y : 1.0f;
    const float dz = bounds.valid ? bounds.max.z - bounds.min.z : 1.0f;
    const float scale = 1.6f / std::max(std::max(std::max(dx, dy), dz), 1.0f);
    matrix.values[0] = scale;
    matrix.values[5] = scale;
    matrix.values[10] = scale;
    matrix.values[12] = -center.x * scale;
    matrix.values[13] = -center.y * scale;
    matrix.values[14] = -center.z * scale;
    matrix.values[15] = 1.0f;
    return matrix;
}

std::optional<OpenYAMM::Game::AnimatedModelAsset> loadModelWithSidecar(
    const std::filesystem::path &modelPath,
    const std::filesystem::path &sidecarPath,
    std::string &errorMessage)
{
    std::optional<OpenYAMM::Game::AnimatedModelAsset> asset =
        OpenYAMM::Game::loadAnimatedModelAsset(modelPath, errorMessage);
    if (!asset)
    {
        return std::nullopt;
    }

    std::optional<OpenYAMM::Game::Mm9AnimatedModelSidecar> sidecar =
        OpenYAMM::Game::loadMm9AnimatedModelSidecar(sidecarPath, errorMessage);
    if (!sidecar)
    {
        return std::nullopt;
    }

    OpenYAMM::Game::mergeMm9AnimatedModelSidecar(*sidecar, *asset);
    if (asset->hasErrors())
    {
        errorMessage = "model validation failed";
        return std::nullopt;
    }

    return asset;
}

std::optional<RenderSubject> buildDirectModelSubject(
    const Arguments &arguments,
    std::string &errorMessage)
{
    std::optional<OpenYAMM::Game::AnimatedModelAsset> asset =
        loadModelWithSidecar(arguments.modelPath, arguments.sidecarPath, errorMessage);
    if (!asset)
    {
        return std::nullopt;
    }

    const OpenYAMM::Game::AnimatedModelClip *pClip = asset->findClip(arguments.clipName);
    if (pClip == nullptr)
    {
        errorMessage = "clip not found: " + arguments.clipName;
        return std::nullopt;
    }

    const OpenYAMM::Game::AnimatedModelPose pose =
        OpenYAMM::Game::sampleAnimatedModelPose(*asset, pClip, arguments.timeSeconds, true);
    const OpenYAMM::Game::AnimatedModelRenderPrep renderPrep =
        OpenYAMM::Game::buildAnimatedModelRenderPrep(
            *asset,
            pose,
            OpenYAMM::Game::AnimatedModelRenderer::MaxShaderBoneMatrices);
    if (!renderPrep.diagnostics.empty() || renderPrep.drawItems.empty())
    {
        errorMessage = "render prep failed";
        return std::nullopt;
    }

    return RenderSubject{
        .renderPrep = renderPrep,
        .bounds = computeSkinnedBounds(renderPrep, asset->bounds),
        .modelToWorld = identityMatrix(),
        .modelPath = arguments.modelPath,
        .clipName = pClip->name,
    };
}

std::optional<RenderSubject> buildRuntimeBindingSubject(
    const Arguments &arguments,
    std::string &errorMessage)
{
    const std::optional<std::string> sceneText = readTextFile(arguments.scenePath);
    if (!sceneText)
    {
        errorMessage = "could not read scene: " + arguments.scenePath.string();
        return std::nullopt;
    }

    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<OpenYAMM::Game::OutdoorSceneData> sceneData =
        sceneLoader.loadFromText(*sceneText, errorMessage);
    if (!sceneData)
    {
        return std::nullopt;
    }

    const std::optional<std::string> eventsText = readTextFile(arguments.eventsPath);
    if (!eventsText)
    {
        errorMessage = "could not read events: " + arguments.eventsPath.string();
        return std::nullopt;
    }

    OpenYAMM::Game::Mm9EventsYmlLoader eventsLoader = {};
    const std::optional<OpenYAMM::Game::Mm9EventsData> eventsData =
        eventsLoader.loadFromText(*eventsText, errorMessage);
    if (!eventsData)
    {
        return std::nullopt;
    }

    OpenYAMM::Game::Mm9ScriptedObjectRuntime objectRuntime = {};
    if (!objectRuntime.initialize(arguments.mapId, *sceneData, &*eventsData))
    {
        errorMessage = "could not initialize MM9 scripted object runtime";
        return std::nullopt;
    }

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    if (!resolver.loadRegistry(arguments.registryPath, errorMessage))
    {
        return std::nullopt;
    }

    std::unordered_map<std::string, OpenYAMM::Game::AnimatedModelAsset> assetCache;
    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> allDiagnostics;
    for (const OpenYAMM::Game::Mm9ScriptedObject &object : objectRuntime.objects())
    {
        if (!object.visible || object.sourceModel.empty())
        {
            continue;
        }
        if (arguments.objectIndex.has_value() && object.sourceObjectIndex != *arguments.objectIndex)
        {
            continue;
        }

        std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
        const std::optional<OpenYAMM::Game::Mm9AnimatedActorResolvedSource> resolved =
            OpenYAMM::Game::resolveMm9AnimatedActorVisualSource(object, resolver, diagnostics);
        allDiagnostics.insert(allDiagnostics.end(), diagnostics.begin(), diagnostics.end());
        if (!resolved)
        {
            continue;
        }

        const std::string assetKey = resolved->resolution.modelAssetPath.generic_string();
        auto assetIterator = assetCache.find(assetKey);
        if (assetIterator == assetCache.end())
        {
            std::optional<OpenYAMM::Game::AnimatedModelAsset> loadedAsset =
                loadModelWithSidecar(
                    resolved->resolution.modelAssetPath,
                    resolved->resolution.modelSidecarPath,
                    errorMessage);
            if (!loadedAsset)
            {
                return std::nullopt;
            }
            assetIterator = assetCache.emplace(assetKey, std::move(*loadedAsset)).first;
        }

        OpenYAMM::Game::Mm9AnimatedActorVisual visual = {};
        if (!OpenYAMM::Game::initializeMm9AnimatedActorVisual(
                resolved->source,
                resolved->resolution,
                assetIterator->second,
                visual))
        {
            allDiagnostics.insert(allDiagnostics.end(), visual.diagnostics.begin(), visual.diagnostics.end());
            continue;
        }

        OpenYAMM::Game::updateMm9AnimatedActorVisual(visual, assetIterator->second, arguments.timeSeconds);
        const OpenYAMM::Game::AnimatedModelBounds localBounds =
            computeSkinnedBounds(visual.renderPrepCache, assetIterator->second.bounds);
        const OpenYAMM::Game::AnimatedModelBounds worldBounds =
            transformBounds(visual.modelToWorld, localBounds);

        return RenderSubject{
            .renderPrep = visual.renderPrepCache,
            .bounds = worldBounds.valid ? worldBounds : localBounds,
            .modelToWorld = visual.modelToWorld,
            .modelPath = resolved->resolution.modelAssetPath,
            .clipName = visual.currentClipName,
            .mapId = visual.mapId,
            .objectId = visual.objectId,
            .sourceName = visual.sourceName,
            .sourceObjectIndex = visual.sourceObjectIndex,
            .fromRuntimeBinding = true,
        };
    }

    for (const OpenYAMM::Game::AnimatedModelDiagnostic &diagnostic : allDiagnostics)
    {
        if (diagnostic.error)
        {
            std::cerr << diagnostic.message << '\n';
        }
    }
    errorMessage = arguments.objectIndex.has_value()
        ? "no renderable MM9 scripted object found for source_object_index " + std::to_string(*arguments.objectIndex)
        : "no renderable MM9 scripted object found";
    return std::nullopt;
}

void configureView()
{
    float view[16] = {};
    float projection[16] = {};
    bx::mtxIdentity(view);
    bx::mtxIdentity(projection);

    bgfx::setViewRect(SmokeViewId, 0, 0, SmokeWidth, SmokeHeight);
    bgfx::setViewClear(SmokeViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x000000ff, 1.0f, 0);
    bgfx::setViewTransform(SmokeViewId, view, projection);
    bgfx::touch(SmokeViewId);
}

bool ensureVideoDriver(bool requirePixels)
{
    SDL_Environment *pEnvironment = SDL_GetEnvironment();
    if (pEnvironment == nullptr)
    {
        return false;
    }

    const char *pConfiguredDriver = SDL_GetEnvironmentVariable(pEnvironment, "SDL_VIDEODRIVER");
    if (pConfiguredDriver == nullptr || pConfiguredDriver[0] == '\0')
    {
        const char *pDriverName = requirePixels ? "offscreen" : "dummy";
        return SDL_SetEnvironmentVariable(pEnvironment, "SDL_VIDEODRIVER", pDriverName, false);
    }

    return true;
}

bool setVideoDriver(const char *pDriverName)
{
    SDL_Environment *pEnvironment = SDL_GetEnvironment();
    return pEnvironment != nullptr
        && SDL_SetEnvironmentVariable(pEnvironment, "SDL_VIDEODRIVER", pDriverName, true);
}

SDL_Window *createSmokeWindow(bool hidden)
{
    return SDL_CreateWindow(
        "MM9 Animated Model Render Smoke",
        SmokeWidth,
        SmokeHeight,
        hidden ? SDL_WINDOW_HIDDEN : 0);
}
}

int main(int argc, char **argv)
{
    Arguments arguments = {};
    if (!parseArguments(argc, argv, arguments))
    {
        printUsage();
        return 2;
    }

    std::string errorMessage;
    const bool runtimeBindingMode = arguments.modelPath.empty();
    std::optional<RenderSubject> subject = runtimeBindingMode
        ? buildRuntimeBindingSubject(arguments, errorMessage)
        : buildDirectModelSubject(arguments, errorMessage);
    if (!subject)
    {
        std::cerr << errorMessage << '\n';
        return 1;
    }

    if (!ensureVideoDriver(arguments.requirePixels) || !SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS))
    {
        std::cerr << "SDL_Init failed: " << SDL_GetError() << '\n';
        return 1;
    }

    SDL_Window *pWindow = createSmokeWindow(!arguments.requirePixels);
    if (pWindow == nullptr)
    {
        std::cerr << "SDL_CreateWindow failed: " << SDL_GetError() << '\n';
        SDL_Quit();
        return 1;
    }

    OpenYAMM::Engine::BgfxContext bgfxContext;
    if (!bgfxContext.initialize(pWindow, SmokeWidth, SmokeHeight, false))
    {
        SDL_DestroyWindow(pWindow);
        SDL_Quit();

        if (!setVideoDriver("dummy") || !SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS))
        {
            std::cerr << "SDL dummy fallback failed: " << SDL_GetError() << '\n';
            return 1;
        }

        pWindow = createSmokeWindow(!arguments.requirePixels);
        if (pWindow == nullptr)
        {
            std::cerr << "SDL dummy window fallback failed: " << SDL_GetError() << '\n';
            SDL_Quit();
            return 1;
        }

        if (!bgfxContext.initialize(pWindow, SmokeWidth, SmokeHeight, false))
        {
            SDL_DestroyWindow(pWindow);
            SDL_Quit();
            return 1;
        }
    }

    OpenYAMM::Game::AnimatedModelRenderResources resources;
    OpenYAMM::Game::AnimatedModelRenderer::initializeResources(resources);
    const bgfx::TextureHandle whiteTexture = createWhiteTexture();
    std::map<std::string, bgfx::TextureHandle> textureHandles;
    bgfx::TextureHandle renderTargetTexture = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle renderDepthTexture = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle readbackTexture = BGFX_INVALID_HANDLE;
    bgfx::FrameBufferHandle renderFrameBuffer = BGFX_INVALID_HANDLE;
    if (arguments.requirePixels)
    {
        renderTargetTexture = bgfx::createTexture2D(
            SmokeWidth,
            SmokeHeight,
            false,
            1,
            bgfx::TextureFormat::RGBA8,
            BGFX_TEXTURE_RT);
        if (bgfx::isValid(renderTargetTexture))
        {
            renderDepthTexture = bgfx::createTexture2D(
                SmokeWidth,
                SmokeHeight,
                false,
                1,
                bgfx::TextureFormat::D24S8,
                BGFX_TEXTURE_RT);
        }
        if (bgfx::isValid(renderTargetTexture) && bgfx::isValid(renderDepthTexture))
        {
            bgfx::TextureHandle attachments[2] = {renderTargetTexture, renderDepthTexture};
            renderFrameBuffer = bgfx::createFrameBuffer(2, attachments, false);
        }

        if ((bgfx::getCaps()->supported & BGFX_CAPS_TEXTURE_BLIT) != 0)
        {
            readbackTexture = bgfx::createTexture2D(
                SmokeWidth,
                SmokeHeight,
                false,
                1,
                bgfx::TextureFormat::RGBA8,
                BGFX_TEXTURE_BLIT_DST | BGFX_TEXTURE_READ_BACK);
        }
    }
    bgfx::frame();
    configureView();
    if (bgfx::isValid(renderFrameBuffer))
    {
        bgfx::setViewFrameBuffer(SmokeViewId, renderFrameBuffer);
    }

    const OpenYAMM::Game::AnimatedModelMat4 fitToClip = fitBoundsToClipMatrix(subject->bounds);
    const OpenYAMM::Game::AnimatedModelMat4 modelToWorld = subject->fromRuntimeBinding
        ? multiplyMatrix(fitToClip, subject->modelToWorld)
        : fitToClip;
    size_t submittedDraws = 0;
    for (const OpenYAMM::Game::AnimatedModelDrawItem &drawItem : subject->renderPrep.drawItems)
    {
        bgfx::TextureHandle textureHandle = whiteTexture;
        if (!drawItem.texture.empty())
        {
            auto textureIterator = textureHandles.find(drawItem.texture);
            if (textureIterator == textureHandles.end())
            {
                std::optional<bgfx::TextureHandle> loadedTexture =
                    loadTextureHandle(arguments.textureRoot, drawItem.texture, errorMessage);
                if (!loadedTexture)
                {
                    std::cerr << errorMessage << '\n';
                    bgfx::destroy(whiteTexture);
                    resources.shutdown();
                    bgfxContext.shutdown();
                    SDL_DestroyWindow(pWindow);
                    SDL_Quit();
                    return 1;
                }
                textureIterator =
                    textureHandles.emplace(drawItem.texture, *loadedTexture).first;
            }
            textureHandle = textureIterator->second;
        }

        if (OpenYAMM::Game::AnimatedModelRenderer::submitDrawItem(
                resources,
                SmokeViewId,
                drawItem,
                modelToWorld,
                textureHandle))
        {
            ++submittedDraws;
        }
    }

    const bgfx::RendererType::Enum rendererType = bgfxContext.getRendererType();
    std::optional<OpenYAMM::Engine::BgfxContext::ScreenshotCapture> screenshot;
    PixelStats pixelStats = {};
    bool usedReadbackTexture = false;
    if (bgfx::isValid(renderTargetTexture) && bgfx::isValid(readbackTexture))
    {
        bgfx::frame();
        bgfx::blit(SmokeBlitViewId, readbackTexture, 0, 0, renderTargetTexture);
        std::vector<uint8_t> readbackPixels(static_cast<size_t>(SmokeWidth) * SmokeHeight * 4);
        bgfx::readTexture(readbackTexture, readbackPixels.data());
        for (int frameIndex = 0; frameIndex < 6; ++frameIndex)
        {
            bgfx::frame();
        }
        pixelStats = bgraPixelStats(readbackPixels);
        usedReadbackTexture = true;
    }
    else
    {
        const std::string screenshotToken = "mm9_animated_model_render_smoke";
        bgfx::requestScreenShot(BGFX_INVALID_HANDLE, screenshotToken.c_str());
        bgfx::frame();
        bgfx::frame();
        bgfx::frame();

        screenshot = OpenYAMM::Engine::BgfxContext::consumeScreenshot(screenshotToken);
        pixelStats = screenshot.has_value() ? screenshotPixelStats(*screenshot) : PixelStats{};
    }
    const bool renderedPixels = pixelStats.litPixels > 0;

    if (submittedDraws == 0)
    {
        std::cerr << "no animated model draw items were submitted\n";
        bgfx::destroy(whiteTexture);
        resources.shutdown();
        bgfxContext.shutdown();
        SDL_DestroyWindow(pWindow);
        SDL_Quit();
        return 1;
    }

    if (arguments.requirePixels && rendererType == bgfx::RendererType::Noop)
    {
        std::cerr << "animated model pixel verification requires a non-Noop bgfx renderer\n";
        bgfx::destroy(whiteTexture);
        resources.shutdown();
        bgfxContext.shutdown();
        SDL_DestroyWindow(pWindow);
        SDL_Quit();
        return 1;
    }

    if (arguments.requirePixels && rendererType != bgfx::RendererType::Noop && !renderedPixels)
    {
        std::cerr
            << "animated model pixel buffer did not contain lit pixels"
            << " source=" << (usedReadbackTexture ? "readback_texture" : "screenshot")
            << " captured=" << (usedReadbackTexture || screenshot.has_value() ? "yes" : "no")
            << " max_rgb=(" << static_cast<uint32_t>(pixelStats.maxRed)
            << "," << static_cast<uint32_t>(pixelStats.maxGreen)
            << "," << static_cast<uint32_t>(pixelStats.maxBlue) << ")"
            << " lit_pixels=" << pixelStats.litPixels
            << '\n';
        bgfx::destroy(whiteTexture);
        resources.shutdown();
        bgfxContext.shutdown();
        SDL_DestroyWindow(pWindow);
        SDL_Quit();
        return 1;
    }

    std::cout << "render_smoke.model: " << subject->modelPath.string() << '\n';
    std::cout << "render_smoke.clip: " << subject->clipName << '\n';
    if (subject->fromRuntimeBinding)
    {
        std::cout << "render_smoke.runtime_binding: yes\n";
        std::cout << "render_smoke.map_id: " << subject->mapId << '\n';
        std::cout << "render_smoke.object_id: " << subject->objectId << '\n';
        std::cout << "render_smoke.source_object_index: " << subject->sourceObjectIndex << '\n';
        std::cout << "render_smoke.source_name: " << subject->sourceName << '\n';
    }
    else
    {
        std::cout << "render_smoke.runtime_binding: no\n";
    }
    std::cout << "render_smoke.video_driver: " << SDL_GetCurrentVideoDriver() << '\n';
    std::cout << "render_smoke.renderer: " << bgfx::getRendererName(rendererType) << '\n';
    std::cout << "render_smoke.draw_items: " << subject->renderPrep.drawItems.size() << '\n';
    std::cout << "render_smoke.submitted_draws: " << submittedDraws << '\n';
    std::cout << "render_smoke.loaded_textures: " << textureHandles.size() << '\n';
    std::cout
        << "render_smoke.pixel_source: "
        << (usedReadbackTexture ? "readback_texture" : "screenshot")
        << '\n';
    std::cout << "render_smoke.screenshot: " << (screenshot.has_value() ? "captured" : "unavailable") << '\n';
    std::cout << "render_smoke.lit_pixels: " << pixelStats.litPixels << '\n';
    std::cout
        << "render_smoke.max_rgb: "
        << static_cast<uint32_t>(pixelStats.maxRed) << ' '
        << static_cast<uint32_t>(pixelStats.maxGreen) << ' '
        << static_cast<uint32_t>(pixelStats.maxBlue) << '\n';

    for (const auto &entry : textureHandles)
    {
        if (bgfx::isValid(entry.second))
        {
            bgfx::destroy(entry.second);
        }
    }
    if (bgfx::isValid(renderFrameBuffer))
    {
        bgfx::destroy(renderFrameBuffer);
    }
    if (bgfx::isValid(renderTargetTexture))
    {
        bgfx::destroy(renderTargetTexture);
    }
    if (bgfx::isValid(renderDepthTexture))
    {
        bgfx::destroy(renderDepthTexture);
    }
    if (bgfx::isValid(readbackTexture))
    {
        bgfx::destroy(readbackTexture);
    }
    bgfx::destroy(whiteTexture);
    resources.shutdown();
    bgfxContext.shutdown();
    SDL_DestroyWindow(pWindow);
    SDL_Quit();
    return 0;
}
