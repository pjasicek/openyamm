#include "editor/viewport/EditorOutdoorViewport.h"

#include "editor/model/Mm9ModelInstanceActorResolver.h"
#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/ImageAssetLoader.h"
#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MapIdentity.h"
#include "game/maps/TerrainTileData.h"
#include "game/mm9/Mm9DtxTexture.h"
#include "game/mm9/Mm9DatWorld.h"
#include "game/mm9/Mm9LightLayer.h"
#include "game/mm9/Mm9ObjectLayer.h"
#include "game/mm9/Mm9SoundLayer.h"
#include "game/mm9/Mm9SpawnLayer.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"

#include <imgui.h>
#include <bgfx/bgfx.h>
#include <bx/math.h>
#include <SDL3/SDL.h>
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <cfloat>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <set>
#include <unordered_map>
#include <utility>
#include <vector>

namespace OpenYAMM::Editor
{
namespace
{
constexpr bgfx::ViewId EditorSceneViewId = 0;
constexpr float CameraVerticalFovDegrees = 60.0f;
constexpr float CameraNearPlane = 32.0f;
constexpr float CameraFarPlane = 131072.0f;
constexpr float CameraMouseSensitivity = 0.0035f;
constexpr float CameraMoveSpeed = 9000.0f;
constexpr float IndoorCameraMoveSpeedMultiplier = 0.25f;
constexpr float CameraFastMoveSpeedMultiplier = 4.0f;
constexpr float CameraMinPitchRadians = -1.45f;
constexpr float CameraMaxPitchRadians = 1.45f;
constexpr float CameraFocusDurationSeconds = 0.22f;
constexpr float GizmoAxisWorldLength = 1024.0f;
constexpr float IndoorGizmoAxisWorldLength = 560.0f;
constexpr float IndoorGizmoScreenAxisLength = 86.0f;
constexpr float GizmoCenterPickRadiusPixels = 12.0f;
constexpr float GizmoAxisPickSlackPixels = 10.0f;
constexpr float GizmoZAxisPickSlackPixels = 18.0f;
constexpr float GizmoAxisEndpointPickRadiusPixels = 14.0f;
constexpr float IndoorGizmoAxisPickSlackPixels = 18.0f;
constexpr float IndoorGizmoAxisEndpointPickRadiusPixels = 18.0f;
constexpr float GizmoRotationPickSlackPixels = 12.0f;
constexpr float GizmoDragDeadzonePixels = 4.0f;
constexpr int GizmoRotationSegments = 32;
constexpr uint16_t DecorationDescDontDraw = 0x0002;
constexpr uint16_t LevelDecorationInvisible = 0x0020;
constexpr int TerrainTextureTileSize = 128;
constexpr int TerrainTextureAtlasColumns = 16;
constexpr const char *BuiltinTerrainClayMaterialName = "Builtin/TerrainClay";
constexpr const char *BuiltinObjectGridMaterialName = "Builtin/ObjectGrid";
constexpr const char *BuiltinErrorMissingAssetMaterialName = "Builtin/ErrorMissingAsset";

struct BitmapPixelsResult
{
    int width = 0;
    int height = 0;
    std::vector<uint8_t> pixels;
};

struct BitmapLoadCache
{
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> directoryEntriesByPath;
    std::unordered_map<std::string, std::optional<std::string>> bitmapPathByKey;
    std::unordered_map<std::string, std::optional<std::vector<uint8_t>>> binaryFilesByPath;
    std::unordered_map<std::string, std::optional<BitmapPixelsResult>> pixelsByKey;
    std::unordered_map<int16_t, std::optional<std::array<uint8_t, 256 * 3>>> actPalettesById;
};

struct IndoorEditorMechanismTextureState
{
    const Game::MapDeltaDoor *pDoor = nullptr;
    size_t faceOffset = 0;
    float distance = 0.0f;
    bx::Vec3 direction = {0.0f, 0.0f, 0.0f};
};

struct TerrainAtlasRegion
{
    float u0 = 0.0f;
    float v0 = 0.0f;
    float u1 = 0.0f;
    float v1 = 0.0f;
    bool isValid = false;
    bool hasAssignedTexture = false;
    bool hasMissingAsset = false;
};

struct TerrainAtlasData
{
    int width = 0;
    int height = 0;
    int tileSize = 0;
    std::vector<uint8_t> pixels;
    std::array<TerrainAtlasRegion, 256> tileRegions = {};
};

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

std::string trimWhitespaceCopy(const std::string &value)
{
    size_t begin = 0;
    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])))
    {
        ++begin;
    }

    size_t end = value.size();
    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

bool shouldRenderTerrainHeightmap(const EditorDocument &document)
{
    if (document.kind() != EditorDocument::Kind::Outdoor)
    {
        return false;
    }

    if (toLowerCopy(document.outdoorGeometry().worldId) == "mm9")
    {
        return false;
    }

    const std::string sceneVirtualPath = toLowerCopy(document.sceneVirtualPath());
    return sceneVirtualPath.find("worlds/mm9/maps") == std::string::npos;
}

bool isMm9ScriptedModelInstance(
    const EditorDocument &document,
    const Game::OutdoorSceneModelInstance &modelInstance,
    const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup)
{
    if (document.kind() != EditorDocument::Kind::Outdoor
        || toLowerCopy(document.outdoorGeometry().worldId) != "mm9")
    {
        return false;
    }

    if (canResolveMm9ModelInstanceActorSource(modelInstance, pActorSourceLookup))
    {
        return true;
    }

    return !modelInstance.sourceModel.empty() && toLowerCopy(modelInstance.sourceClass) != "prop";
}

bool endsWithCaseInsensitive(const std::string &value, const std::string &suffix)
{
    if (suffix.size() > value.size())
    {
        return false;
    }

    const size_t offset = value.size() - suffix.size();
    for (size_t index = 0; index < suffix.size(); ++index)
    {
        const char lhs = static_cast<char>(std::tolower(static_cast<unsigned char>(value[offset + index])));
        const char rhs = static_cast<char>(std::tolower(static_cast<unsigned char>(suffix[index])));
        if (lhs != rhs)
        {
            return false;
        }
    }

    return true;
}

std::string normalizeMm9VirtualTexturePath(std::string value)
{
    value = trimWhitespaceCopy(value);
    std::replace(value.begin(), value.end(), '\\', '/');

    while (!value.empty() && value.front() == '/')
    {
        value.erase(value.begin());
    }

    value = toLowerCopy(value);

    const std::string extractedSkinsPrefix = "mm9/extracted/skins/skins/";
    const std::string extractedTexturesPrefix = "mm9/extracted/textures/textures/";
    const std::string skinsPrefix = "skins/skins/";
    const std::string texturesPrefix = "textures/textures/";

    if (value.rfind(extractedSkinsPrefix, 0) == 0)
    {
        value = "skins/" + value.substr(extractedSkinsPrefix.size());
    }
    else if (value.rfind(extractedTexturesPrefix, 0) == 0)
    {
        value = "textures/" + value.substr(extractedTexturesPrefix.size());
    }
    else if (value.rfind(skinsPrefix, 0) == 0)
    {
        value = "skins/" + value.substr(skinsPrefix.size());
    }
    else if (value.rfind(texturesPrefix, 0) == 0)
    {
        value = "textures/" + value.substr(texturesPrefix.size());
    }

    return value;
}

std::vector<std::string> sourceSkinTexturePaths(const std::string &sourceSkin)
{
    std::vector<std::string> texturePaths;
    size_t begin = 0;

    while (begin <= sourceSkin.size())
    {
        const size_t separator = sourceSkin.find(';', begin);
        const size_t end = separator == std::string::npos ? sourceSkin.size() : separator;
        const std::string texturePath = normalizeMm9VirtualTexturePath(sourceSkin.substr(begin, end - begin));
        if (!texturePath.empty())
        {
            texturePaths.push_back(texturePath);
        }

        if (separator == std::string::npos)
        {
            break;
        }

        begin = separator + 1;
    }

    return texturePaths;
}

std::string mm9RuntimeAssetPathFromResolvedSourcePath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &sourceFamily,
    const std::string &resolvedSourcePath)
{
    const std::filesystem::path sourceRoot =
        assetFileSystem.getDevelopmentRoot()
        / "worlds"
        / assetFileSystem.getActiveWorldId()
        / "source"
        / sourceFamily;
    std::filesystem::path relativePath =
        std::filesystem::path(resolvedSourcePath).lexically_relative(sourceRoot);

    if (relativePath.empty() || relativePath.native().find("..") == 0)
    {
        relativePath = std::filesystem::path(resolvedSourcePath).filename();
    }

    std::string normalized = toLowerCopy(relativePath.generic_string());

    if (normalized.empty())
    {
        return {};
    }

    return (std::filesystem::path(sourceFamily) / normalized).generic_string();
}

std::string mm9GeneratedModelAssetPathFromResolvedSourceModel(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &resolvedSourcePath)
{
    std::filesystem::path assetPath =
        mm9RuntimeAssetPathFromResolvedSourcePath(assetFileSystem, "models", resolvedSourcePath);
    assetPath.replace_extension(".glb");
    return assetPath.generic_string();
}

std::string mm9RuntimeSkinAssetPathFromResolvedSourceSkin(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &resolvedSourcePath)
{
    return mm9RuntimeAssetPathFromResolvedSourcePath(assetFileSystem, "skins", resolvedSourcePath);
}

std::string virtualPathFileStem(std::string virtualPath)
{
    std::replace(virtualPath.begin(), virtualPath.end(), '\\', '/');

    const size_t separator = virtualPath.find_last_of('/');
    if (separator != std::string::npos)
    {
        virtualPath = virtualPath.substr(separator + 1);
    }

    const size_t extension = virtualPath.find_last_of('.');
    if (extension != std::string::npos)
    {
        virtualPath = virtualPath.substr(0, extension);
    }

    return toLowerCopy(virtualPath);
}

std::string virtualPathDirectory(std::string virtualPath)
{
    std::replace(virtualPath.begin(), virtualPath.end(), '\\', '/');

    const size_t separator = virtualPath.find_last_of('/');
    if (separator == std::string::npos)
    {
        return {};
    }

    return virtualPath.substr(0, separator);
}

std::string removeVirtualExtension(std::string virtualPath)
{
    std::replace(virtualPath.begin(), virtualPath.end(), '\\', '/');

    const size_t separator = virtualPath.find_last_of('/');
    const size_t extension = virtualPath.find_last_of('.');
    if (extension != std::string::npos && (separator == std::string::npos || extension > separator))
    {
        virtualPath.resize(extension);
    }

    return virtualPath;
}

void appendUniqueModelCandidate(std::vector<std::string> &candidates, const std::string &candidate)
{
    if (candidate.empty())
    {
        return;
    }

    if (std::find(candidates.begin(), candidates.end(), candidate) == candidates.end())
    {
        candidates.push_back(candidate);
    }
}

std::string normalizeMm9RegistryVirtualPath(std::string value)
{
    value = trimWhitespaceCopy(value);
    std::replace(value.begin(), value.end(), '\\', '/');

    while (!value.empty() && value.front() == '/')
    {
        value.erase(value.begin());
    }

    value = toLowerCopy(value);

    const std::string extractedModelsPrefix = "mm9/extracted/models/models/";
    const std::string extractedSkinsPrefix = "mm9/extracted/skins/skins/";
    const std::string modelsPrefix = "models/models/";
    const std::string skinsPrefix = "skins/skins/";

    if (value.rfind(extractedModelsPrefix, 0) == 0)
    {
        value = "models/" + value.substr(extractedModelsPrefix.size());
    }
    else if (value.rfind(extractedSkinsPrefix, 0) == 0)
    {
        value = "skins/" + value.substr(extractedSkinsPrefix.size());
    }
    else if (value.rfind(modelsPrefix, 0) == 0)
    {
        value = "models/" + value.substr(modelsPrefix.size());
    }
    else if (value.rfind(skinsPrefix, 0) == 0)
    {
        value = "skins/" + value.substr(skinsPrefix.size());
    }

    if (endsWithCaseInsensitive(value, ".png"))
    {
        value.resize(value.size() - 4);
        value += ".dtx";
    }

    return value;
}

std::vector<std::string> sourceSkinRegistryPaths(const std::string &sourceSkin)
{
    std::vector<std::string> skinPaths;
    size_t begin = 0;

    while (begin <= sourceSkin.size())
    {
        const size_t separator = sourceSkin.find(';', begin);
        const size_t end = separator == std::string::npos ? sourceSkin.size() : separator;
        const std::string skinPath = normalizeMm9RegistryVirtualPath(sourceSkin.substr(begin, end - begin));
        if (!skinPath.empty())
        {
            skinPaths.push_back(skinPath);
        }

        if (separator == std::string::npos)
        {
            break;
        }

        begin = separator + 1;
    }

    return skinPaths;
}

std::string mm9RegistryLookupKey(const std::string &sourceModel, const std::vector<std::string> &sourceSkinPaths)
{
    std::string key = normalizeMm9RegistryVirtualPath(sourceModel) + "|";
    for (size_t index = 0; index < sourceSkinPaths.size(); ++index)
    {
        if (index != 0)
        {
            key += ";";
        }
        key += sourceSkinPaths[index];
    }
    return key;
}

struct Mm9ModelRegistry
{
    std::unordered_map<std::string, std::string> modelAssetByVariantId;
    std::unordered_map<std::string, std::vector<std::string>> variantIdsBySourceModel;
    std::unordered_map<std::string, std::string> variantIdBySourceModelAndSkins;
};

struct ResolvedModelInstanceAsset
{
    std::string virtualPath;
    std::filesystem::path physicalPath;
};

YAML::Node yamlMapValue(const YAML::Node &node, const char *pKey)
{
    if (!node.IsDefined() || !node.IsMap())
    {
        return {};
    }

    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        if (iterator->first.IsScalar() && iterator->first.as<std::string>() == pKey)
        {
            return iterator->second;
        }
    }

    return {};
}

std::optional<Mm9ModelRegistry> loadMm9ModelRegistry(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::optional<std::string> registryText = assetFileSystem.readTextFile("models/model_registry.yml");
    if (!registryText)
    {
        return std::nullopt;
    }

    YAML::Node rootNode;
    try
    {
        rootNode = YAML::Load(*registryText);
    }
    catch (const std::exception &)
    {
        return std::nullopt;
    }

    Mm9ModelRegistry registry;

    const YAML::Node modelsNode = yamlMapValue(rootNode, "models");
    if (modelsNode.IsDefined() && modelsNode.IsSequence())
    {
        for (const YAML::Node &modelNode : modelsNode)
        {
            if (!modelNode.IsDefined() || !modelNode.IsMap())
            {
                continue;
            }

            const YAML::Node sourceModelNode = yamlMapValue(modelNode, "source_model");
            const YAML::Node modelIdNode = yamlMapValue(modelNode, "model_id");
            const YAML::Node modelAssetNode = yamlMapValue(modelNode, "model_asset");
            if (modelAssetNode.IsDefined() && modelAssetNode.IsScalar())
            {
                const std::string modelAsset = normalizeMm9RegistryVirtualPath(modelAssetNode.as<std::string>());
                registry.modelAssetByVariantId.emplace(modelAsset, modelAsset);

                if (modelIdNode.IsDefined() && modelIdNode.IsScalar())
                {
                    registry.modelAssetByVariantId.emplace(modelIdNode.as<std::string>(), modelAsset);
                }

                if (sourceModelNode.IsDefined() && sourceModelNode.IsScalar())
                {
                    const std::string modelKey =
                        modelIdNode.IsDefined() && modelIdNode.IsScalar()
                            ? modelIdNode.as<std::string>()
                            : modelAsset;
                    registry.variantIdsBySourceModel[normalizeMm9RegistryVirtualPath(sourceModelNode.as<std::string>())]
                        .push_back(modelKey);
                }
            }

            YAML::Node variantsNode = yamlMapValue(modelNode, "skin_bindings");
            if (!variantsNode.IsDefined() || !variantsNode.IsSequence())
            {
                variantsNode = yamlMapValue(modelNode, "variants");
            }
            if (!variantsNode.IsDefined() || !variantsNode.IsSequence())
            {
                continue;
            }

            for (const YAML::Node &variantNode : variantsNode)
            {
                if (!variantNode.IsDefined() || !variantNode.IsMap())
                {
                    continue;
                }

                const YAML::Node idNode = yamlMapValue(variantNode, "id");
                YAML::Node variantAssetNode = yamlMapValue(variantNode, "model_asset");
                if (!variantAssetNode.IsDefined())
                {
                    variantAssetNode = modelAssetNode;
                }
                if (!idNode.IsDefined()
                    || !idNode.IsScalar()
                    || !variantAssetNode.IsDefined()
                    || !variantAssetNode.IsScalar())
                {
                    continue;
                }

                const std::string variantId = idNode.as<std::string>();
                const std::string variantAsset = normalizeMm9RegistryVirtualPath(variantAssetNode.as<std::string>());
                registry.modelAssetByVariantId.emplace(
                    variantId,
                    variantAsset);

                if (sourceModelNode.IsDefined() && sourceModelNode.IsScalar())
                {
                    registry.variantIdsBySourceModel[normalizeMm9RegistryVirtualPath(sourceModelNode.as<std::string>())]
                        .push_back(variantId);
                }
            }
        }
    }

    const YAML::Node lookupNode = yamlMapValue(rootNode, "lookup");
    if (lookupNode.IsDefined() && lookupNode.IsMap())
    {
        const YAML::Node bySourceModelNode = yamlMapValue(lookupNode, "by_source_model");
        if (bySourceModelNode.IsDefined() && bySourceModelNode.IsMap())
        {
            for (const auto &entry : bySourceModelNode)
            {
                if (!entry.first.IsScalar())
                {
                    continue;
                }

                std::vector<std::string> variantIds;
                if (entry.second.IsScalar())
                {
                    const std::string modelAsset = normalizeMm9RegistryVirtualPath(entry.second.as<std::string>());
                    registry.modelAssetByVariantId.emplace(modelAsset, modelAsset);
                    variantIds.push_back(modelAsset);
                }
                else if (entry.second.IsSequence())
                {
                    for (const YAML::Node &variantNode : entry.second)
                    {
                        if (variantNode.IsScalar())
                        {
                            variantIds.push_back(variantNode.as<std::string>());
                        }
                    }
                }

                if (!variantIds.empty())
                {
                    const std::string sourceModel = normalizeMm9RegistryVirtualPath(entry.first.as<std::string>());
                    std::vector<std::string> &target = registry.variantIdsBySourceModel[sourceModel];
                    for (const std::string &variantId : variantIds)
                    {
                        if (std::find(target.begin(), target.end(), variantId) == target.end())
                        {
                            target.push_back(variantId);
                        }
                    }
                }
            }
        }

        const YAML::Node bySourceModelAndSkinsNode = yamlMapValue(lookupNode, "by_source_model_and_skins");
        if (bySourceModelAndSkinsNode.IsDefined() && bySourceModelAndSkinsNode.IsMap())
        {
            for (const auto &entry : bySourceModelAndSkinsNode)
            {
                if (entry.first.IsScalar() && entry.second.IsScalar())
                {
                    registry.variantIdBySourceModelAndSkins.emplace(
                        normalizeMm9RegistryVirtualPath(entry.first.as<std::string>()),
                        entry.second.as<std::string>());
                }
            }
        }
    }

    return registry;
}

void appendMm9RegistryModelCandidates(
    std::vector<std::string> &candidates,
    const Mm9ModelRegistry *pRegistry,
    const Game::OutdoorSceneModelInstance &modelInstance)
{
    if (pRegistry == nullptr)
    {
        return;
    }

    const std::string sourceModel = normalizeMm9RegistryVirtualPath(modelInstance.sourceModel);
    const std::vector<std::string> sourceSkins = sourceSkinRegistryPaths(modelInstance.sourceSkin);
    const std::string exactKey = mm9RegistryLookupKey(sourceModel, sourceSkins);

    const auto exactIt = pRegistry->variantIdBySourceModelAndSkins.find(exactKey);
    if (exactIt != pRegistry->variantIdBySourceModelAndSkins.end())
    {
        const auto assetIt = pRegistry->modelAssetByVariantId.find(exactIt->second);
        if (assetIt != pRegistry->modelAssetByVariantId.end())
        {
            appendUniqueModelCandidate(candidates, assetIt->second);
        }
    }

    const auto sourceIt = pRegistry->variantIdsBySourceModel.find(sourceModel);
    if (sourceIt == pRegistry->variantIdsBySourceModel.end())
    {
        return;
    }

    for (const std::string &variantId : sourceIt->second)
    {
        const auto assetIt = pRegistry->modelAssetByVariantId.find(variantId);
        if (assetIt != pRegistry->modelAssetByVariantId.end())
        {
            appendUniqueModelCandidate(candidates, assetIt->second);
        }
    }
}

std::optional<ResolvedModelInstanceAsset> resolveModelInstanceAsset(
    const Engine::AssetFileSystem &assetFileSystem,
    const Game::OutdoorSceneModelInstance &modelInstance,
    const std::vector<std::string> &sourceSkinPaths,
    const Mm9ModelRegistry *pModelRegistry,
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> *pRawObjectAssetStatuses)
{
    std::vector<std::string> candidates;

    appendMm9RegistryModelCandidates(candidates, pModelRegistry, modelInstance);

    if (pRawObjectAssetStatuses != nullptr)
    {
        for (const EditorMm9RawObjectAssetReferenceStatus &status : *pRawObjectAssetStatuses)
        {
            if (status.sourceObjectIndex != modelInstance.sourceObjectIndex
                || status.sourceFamily != "models"
                || !status.resolved
                || status.ambiguous
                || status.resolvedSourcePath.empty())
            {
                continue;
            }

            appendUniqueModelCandidate(
                candidates,
                mm9GeneratedModelAssetPathFromResolvedSourceModel(assetFileSystem, status.resolvedSourcePath));
        }
    }

    const std::string logicalModel =
        !sourceSkinPaths.empty() && !modelInstance.sourceModel.empty()
            ? modelInstance.sourceModel
            : (!modelInstance.modelAsset.empty() ? modelInstance.modelAsset : modelInstance.sourceModel);
    const std::string stem = virtualPathFileStem(logicalModel);
    const std::string logicalWithoutExtension = removeVirtualExtension(logicalModel);

    if (!logicalWithoutExtension.empty() && !stem.empty())
    {
        appendUniqueModelCandidate(candidates, logicalWithoutExtension + ".glb");
    }

    if (!stem.empty())
    {
        appendUniqueModelCandidate(candidates, "models/" + stem + ".glb");
    }

    appendUniqueModelCandidate(candidates, modelInstance.modelAsset);

    for (const std::string &candidate : candidates)
    {
        std::optional<std::filesystem::path> resolvedPath = assetFileSystem.resolvePhysicalPath(candidate);
        if (resolvedPath)
        {
            ResolvedModelInstanceAsset resolvedAsset = {};
            resolvedAsset.virtualPath = candidate;
            resolvedAsset.physicalPath = *resolvedPath;
            return resolvedAsset;
        }
    }

    return std::nullopt;
}

std::vector<std::string> sourceSkinTexturePathsForModelInstance(
    const Engine::AssetFileSystem &assetFileSystem,
    const Game::OutdoorSceneModelInstance &modelInstance,
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> *pRawObjectAssetStatuses)
{
    std::vector<std::string> texturePaths;

    if (pRawObjectAssetStatuses != nullptr)
    {
        for (const EditorMm9RawObjectAssetReferenceStatus &status : *pRawObjectAssetStatuses)
        {
            if (status.sourceObjectIndex != modelInstance.sourceObjectIndex
                || status.sourceFamily != "skins"
                || !status.resolved
                || status.ambiguous
                || status.resolvedSourcePath.empty())
            {
                continue;
            }

            appendUniqueModelCandidate(
                texturePaths,
                mm9RuntimeSkinAssetPathFromResolvedSourceSkin(assetFileSystem, status.resolvedSourcePath));
        }
    }

    for (const std::string &skinPath : sourceSkinTexturePaths(modelInstance.sourceSkin))
    {
        appendUniqueModelCandidate(texturePaths, skinPath);
    }

    return texturePaths;
}

std::vector<std::string> loadModelSidecarTexturePaths(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &modelAssetPath)
{
    std::vector<std::string> texturePaths;
    const std::string sidecarPath = removeVirtualExtension(modelAssetPath) + ".model.yml";

    const std::optional<std::string> sidecarText = assetFileSystem.readTextFile(sidecarPath);
    if (!sidecarText)
    {
        return texturePaths;
    }

    YAML::Node rootNode;
    try
    {
        rootNode = YAML::Load(*sidecarText);
    }
    catch (const std::exception &)
    {
        return texturePaths;
    }

    const YAML::Node materialsNode = yamlMapValue(rootNode, "materials");
    if (!materialsNode.IsDefined() || !materialsNode.IsSequence())
    {
        return texturePaths;
    }

    for (const YAML::Node &materialNode : materialsNode)
    {
        if (!materialNode.IsDefined() || !materialNode.IsMap())
        {
            continue;
        }

        const YAML::Node indexNode = yamlMapValue(materialNode, "index");
        const YAML::Node runtimeTextureNode = yamlMapValue(materialNode, "runtime_texture");
        const YAML::Node textureNode = yamlMapValue(materialNode, "texture");
        const YAML::Node previewTextureNode = yamlMapValue(materialNode, "preview_texture");
        if (!indexNode.IsDefined()
            || !indexNode.IsScalar())
        {
            continue;
        }

        size_t materialIndex = 0;
        std::string texturePath;
        try
        {
            materialIndex = indexNode.as<size_t>();
            if (runtimeTextureNode.IsDefined() && runtimeTextureNode.IsScalar())
            {
                texturePath = runtimeTextureNode.as<std::string>();
            }
            else if (textureNode.IsDefined() && textureNode.IsScalar())
            {
                texturePath = textureNode.as<std::string>();
            }
            else if (previewTextureNode.IsDefined() && previewTextureNode.IsScalar())
            {
                texturePath = previewTextureNode.as<std::string>();
            }
        }
        catch (const std::exception &)
        {
            continue;
        }

        if (texturePath.empty())
        {
            continue;
        }

        if (texturePaths.size() <= materialIndex)
        {
            texturePaths.resize(materialIndex + 1);
        }

        texturePaths[materialIndex] = normalizeMm9VirtualTexturePath(texturePath);
    }

    return texturePaths;
}

std::optional<size_t> importedMaterialIndexFromName(const std::string &materialName)
{
    const size_t bracketEnd = materialName.rfind(']');
    if (bracketEnd == materialName.size() - 1)
    {
        const size_t bracketBegin = materialName.rfind('[', bracketEnd);
        if (bracketBegin != std::string::npos && bracketBegin + 1 < bracketEnd)
        {
            size_t index = 0;
            for (size_t cursor = bracketBegin + 1; cursor < bracketEnd; ++cursor)
            {
                const char character = materialName[cursor];
                if (!std::isdigit(static_cast<unsigned char>(character)))
                {
                    return std::nullopt;
                }

                index = index * 10 + static_cast<size_t>(character - '0');
            }

            return index;
        }
    }

    const std::string generatedPrefix = "material_";
    if (materialName.rfind(generatedPrefix, 0) == 0 && materialName.size() > generatedPrefix.size())
    {
        size_t index = 0;
        for (size_t cursor = generatedPrefix.size(); cursor < materialName.size(); ++cursor)
        {
            const char character = materialName[cursor];
            if (!std::isdigit(static_cast<unsigned char>(character)))
            {
                return std::nullopt;
            }

            index = index * 10 + static_cast<size_t>(character - '0');
        }

        return index;
    }

    return std::nullopt;
}

bool hasTransparentPixels(const std::vector<uint8_t> &pixels)
{
    for (size_t offset = 3; offset < pixels.size(); offset += 4)
    {
        if (pixels[offset] < 255)
        {
            return true;
        }
    }

    return false;
}

std::optional<Engine::ImagePixelsBgra> loadMm9ModelTexturePixels(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &texturePath,
    Engine::BinaryAssetCache &binaryAssetCache)
{
    if (texturePath.empty())
    {
        return std::nullopt;
    }

    if (endsWithCaseInsensitive(texturePath, ".dtx"))
    {
        const std::optional<std::filesystem::path> resolvedPath =
            assetFileSystem.resolvePhysicalPath(texturePath);
        if (!resolvedPath)
        {
            return std::nullopt;
        }

        std::string errorMessage;
        const std::optional<Game::Mm9DtxTexture> texture =
            Game::loadMm9DtxTexture(*resolvedPath, errorMessage);
        if (!texture
            || texture->width == 0
            || texture->height == 0
            || texture->pixelsBgra.empty())
        {
            return std::nullopt;
        }

        Engine::ImagePixelsBgra pixels = {};
        pixels.width = static_cast<int>(texture->width);
        pixels.height = static_cast<int>(texture->height);
        pixels.pixels = texture->pixelsBgra;
        return pixels;
    }

    return Engine::loadImageAssetPixelsBgra(
        assetFileSystem,
        texturePath,
        binaryAssetCache);
}

std::optional<Engine::ImagePixelsBgra> loadModelSidecarTexturePixels(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &modelSidecarTexturePaths,
    const std::vector<std::string> &sourceSkinPaths,
    const std::string &materialName,
    Engine::BinaryAssetCache &binaryAssetCache)
{
    size_t textureIndex = 0;
    const std::optional<size_t> materialIndex = importedMaterialIndexFromName(materialName);
    if (materialIndex)
    {
        textureIndex = *materialIndex;
    }
    else if (modelSidecarTexturePaths.size() != 1 && sourceSkinPaths.size() != 1)
    {
        return std::nullopt;
    }

    if (textureIndex < sourceSkinPaths.size() && !sourceSkinPaths[textureIndex].empty())
    {
        return loadMm9ModelTexturePixels(
            assetFileSystem,
            sourceSkinPaths[textureIndex],
            binaryAssetCache);
    }

    if (textureIndex >= modelSidecarTexturePaths.size() || modelSidecarTexturePaths[textureIndex].empty())
    {
        return std::nullopt;
    }

    return loadMm9ModelTexturePixels(
        assetFileSystem,
        modelSidecarTexturePaths[textureIndex],
        binaryAssetCache);
}

int terrainTexturePhysicalTileSize(Engine::AssetScaleTier assetScaleTier)
{
    return TerrainTextureTileSize * Engine::assetScaleTierFactor(assetScaleTier);
}

std::optional<std::string> findBitmapPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    BitmapLoadCache &bitmapLoadCache)
{
    return Engine::findImageAssetPath(
        assetFileSystem,
        directoryPath,
        textureName,
        bitmapLoadCache.directoryEntriesByPath,
        bitmapLoadCache.bitmapPathByKey);
}

std::optional<std::string> findDirectoryEntryPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName,
    BitmapLoadCache &bitmapLoadCache)
{
    const auto directoryIt = bitmapLoadCache.directoryEntriesByPath.find(directoryPath);
    const std::unordered_map<std::string, std::string> *pEntries = nullptr;

    if (directoryIt != bitmapLoadCache.directoryEntriesByPath.end())
    {
        pEntries = &directoryIt->second;
    }
    else
    {
        std::vector<std::string> entries = assetFileSystem.enumerate(directoryPath);
        std::unordered_map<std::string, std::string> resolvedEntries;

        for (const std::string &entry : entries)
        {
            resolvedEntries.emplace(toLowerCopy(entry), directoryPath + "/" + entry);
        }

        pEntries = &bitmapLoadCache.directoryEntriesByPath.emplace(directoryPath, std::move(resolvedEntries)).first->second;
    }

    const auto resolvedIt = pEntries->find(toLowerCopy(fileName));

    if (resolvedIt == pEntries->end())
    {
        return std::nullopt;
    }

    return resolvedIt->second;
}

std::optional<std::array<uint8_t, 256 * 3>> loadActPalette(
    const Engine::AssetFileSystem &assetFileSystem,
    int16_t paletteId,
    BitmapLoadCache &bitmapLoadCache)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    const auto cachedIt = bitmapLoadCache.actPalettesById.find(paletteId);

    if (cachedIt != bitmapLoadCache.actPalettesById.end())
    {
        return cachedIt->second;
    }

    char paletteFileName[32] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));
    const std::optional<std::string> palettePath =
        findDirectoryEntryPath(assetFileSystem, "Data/bitmaps", paletteFileName, bitmapLoadCache);

    if (!palettePath)
    {
        bitmapLoadCache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    std::optional<std::vector<uint8_t>> paletteBytes;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(*palettePath);

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        paletteBytes = cachedFileIt->second;
    }
    else
    {
        paletteBytes = assetFileSystem.readBinaryFile(*palettePath);
        bitmapLoadCache.binaryFilesByPath[*palettePath] = paletteBytes;
    }

    if (!paletteBytes || paletteBytes->size() < 256 * 3)
    {
        bitmapLoadCache.actPalettesById[paletteId] = std::nullopt;
        return std::nullopt;
    }

    std::array<uint8_t, 256 * 3> palette = {};
    std::memcpy(palette.data(), paletteBytes->data(), palette.size());
    bitmapLoadCache.actPalettesById[paletteId] = palette;
    return palette;
}

std::optional<std::vector<uint8_t>> loadSpriteBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height,
    BitmapLoadCache &bitmapLoadCache)
{
    const std::string cacheKey =
        "sprite|" + toLowerCopy(textureName) + "|" + std::to_string(static_cast<int>(paletteId));
    const auto cachedPixelsIt = bitmapLoadCache.pixelsByKey.find(cacheKey);

    if (cachedPixelsIt != bitmapLoadCache.pixelsByKey.end())
    {
        if (!cachedPixelsIt->second)
        {
            return std::nullopt;
        }

        width = cachedPixelsIt->second->width;
        height = cachedPixelsIt->second->height;
        return cachedPixelsIt->second->pixels;
    }

    const std::optional<std::string> bitmapPath =
        Engine::findImageAssetPath(
            assetFileSystem,
            "Data/sprites",
            textureName,
            bitmapLoadCache.directoryEntriesByPath,
            bitmapLoadCache.bitmapPathByKey);

    if (!bitmapPath)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    std::optional<std::vector<uint8_t>> bitmapBytes;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(*bitmapPath);

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        bitmapBytes = cachedFileIt->second;
    }
    else
    {
        bitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);
        bitmapLoadCache.binaryFilesByPath[*bitmapPath] = bitmapBytes;
    }

    if (!bitmapBytes || bitmapBytes->empty())
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.overridePalette = loadActPalette(assetFileSystem, paletteId, bitmapLoadCache);
    decodeOptions.applyMagentaTransparencyKey = true;
    decodeOptions.applyTealTransparencyKey = true;

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, *bitmapPath, decodeOptions);

    if (!image)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    std::vector<uint8_t> pixels = image->pixels;
    bitmapLoadCache.pixelsByKey[cacheKey] = BitmapPixelsResult{width, height, pixels};
    return pixels;
}

std::optional<std::vector<uint8_t>> loadBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &textureName,
    int &width,
    int &height,
    bool forceTerrainTileSize,
    BitmapLoadCache &bitmapLoadCache)
{
    const int forcedTerrainTileSize =
        forceTerrainTileSize
            ? terrainTexturePhysicalTileSize(assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Terrain))
            : 0;
    const std::string cacheKey =
        directoryPath + "|" + toLowerCopy(textureName) + "|" + std::to_string(forcedTerrainTileSize);
    const auto cachedPixelsIt = bitmapLoadCache.pixelsByKey.find(cacheKey);

    if (cachedPixelsIt != bitmapLoadCache.pixelsByKey.end())
    {
        if (!cachedPixelsIt->second)
        {
            return std::nullopt;
        }

        width = cachedPixelsIt->second->width;
        height = cachedPixelsIt->second->height;
        return cachedPixelsIt->second->pixels;
    }

    const std::optional<std::string> bitmapPath = findBitmapPath(assetFileSystem, directoryPath, textureName, bitmapLoadCache);

    if (!bitmapPath)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    std::optional<std::vector<uint8_t>> bitmapBytes;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(*bitmapPath);

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        bitmapBytes = cachedFileIt->second;
    }
    else
    {
        bitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);
        bitmapLoadCache.binaryFilesByPath[*bitmapPath] = bitmapBytes;
    }

    if (!bitmapBytes || bitmapBytes->empty())
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, *bitmapPath);

    if (!image)
    {
        bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    std::vector<uint8_t> pixels = image->pixels;

    if (forceTerrainTileSize && (width != forcedTerrainTileSize || height != forcedTerrainTileSize))
    {
        pixels = Engine::scalePixelsNearestBgra(pixels, width, height, forcedTerrainTileSize, forcedTerrainTileSize);

        if (pixels.empty())
        {
            bitmapLoadCache.pixelsByKey[cacheKey] = std::nullopt;
            return std::nullopt;
        }

        width = forcedTerrainTileSize;
        height = forcedTerrainTileSize;
    }

    bitmapLoadCache.pixelsByKey[cacheKey] = BitmapPixelsResult{width, height, pixels};
    return pixels;
}

std::vector<std::string> outdoorBModelBitmapDirectoryCandidates(const Game::OutdoorMapData &outdoorMapData)
{
    std::vector<std::string> directories;
    const std::string worldId = Game::normalizeWorldId(outdoorMapData.worldId);

    if (!worldId.empty())
    {
        const std::string mapStem = Game::normalizeMapFileStem(outdoorMapData.fileName);
        if (!mapStem.empty())
        {
            directories.push_back("worlds/" + worldId + "/maps/" + mapStem + ".bitmaps");
        }
        directories.push_back("worlds/" + worldId + "/maps/bitmaps");
        directories.push_back("worlds/" + worldId + "/textures");
    }

    directories.push_back("Data/games/bitmaps");
    directories.push_back("Data/bitmaps");
    return directories;
}

std::optional<std::vector<uint8_t>> loadOutdoorBModelBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const Game::OutdoorMapData &outdoorMapData,
    const std::string &textureName,
    int &width,
    int &height,
    BitmapLoadCache &bitmapLoadCache)
{
    for (const std::string &directory : outdoorBModelBitmapDirectoryCandidates(outdoorMapData))
    {
        std::optional<std::vector<uint8_t>> pixels =
            loadBitmapPixelsBgra(
                assetFileSystem,
                directory,
                textureName,
                width,
                height,
                false,
                bitmapLoadCache);

        if (pixels && width > 0 && height > 0)
        {
            return pixels;
        }
    }

    return std::nullopt;
}

std::optional<std::vector<uint8_t>> loadTerrainBitmapPixelsBgra(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    int &width,
    int &height,
    BitmapLoadCache &bitmapLoadCache)
{
    std::optional<std::vector<uint8_t>> pixels =
        loadBitmapPixelsBgra(assetFileSystem, "terrain", textureName, width, height, true, bitmapLoadCache);

    if (pixels)
    {
        return pixels;
    }

    return loadBitmapPixelsBgra(assetFileSystem, "terrain_textures", textureName, width, height, true, bitmapLoadCache);
}

std::optional<TerrainAtlasData> buildTerrainAtlasData(
    const Engine::AssetFileSystem &assetFileSystem,
    const Game::OutdoorMapData &outdoorMapData,
    BitmapLoadCache &bitmapLoadCache)
{
    const std::optional<std::vector<std::string>> tileTextureNames =
        Game::loadTerrainTileTextureNames(assetFileSystem, outdoorMapData);

    if (!tileTextureNames)
    {
        return std::nullopt;
    }

    const int terrainTileSize = terrainTexturePhysicalTileSize(
        assetFileSystem.getAssetScaleTier(Engine::AssetScaleCategory::Terrain));
    TerrainAtlasData atlas = {};
    atlas.tileSize = terrainTileSize;
    atlas.width = TerrainTextureAtlasColumns * terrainTileSize;
    atlas.height = TerrainTextureAtlasColumns * terrainTileSize;
    atlas.pixels.resize(static_cast<size_t>(atlas.width * atlas.height * 4), 0);

    for (int tileIndex = 0; tileIndex < 256; ++tileIndex)
    {
        const std::string &textureName = (*tileTextureNames)[tileIndex];
        TerrainAtlasRegion &region = atlas.tileRegions[static_cast<size_t>(tileIndex)];

        if (textureName.empty() || textureName == "pending")
        {
            continue;
        }

        region.hasAssignedTexture = true;

        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> tilePixels =
            loadTerrainBitmapPixelsBgra(
                assetFileSystem,
                textureName,
                textureWidth,
                textureHeight,
                bitmapLoadCache);

        if (!tilePixels || textureWidth != terrainTileSize || textureHeight != terrainTileSize)
        {
            region.hasMissingAsset = true;
            continue;
        }

        const int atlasColumn = tileIndex % TerrainTextureAtlasColumns;
        const int atlasRow = tileIndex / TerrainTextureAtlasColumns;
        const int atlasX = atlasColumn * terrainTileSize;
        const int atlasY = atlasRow * terrainTileSize;

        for (int row = 0; row < terrainTileSize; ++row)
        {
            const size_t sourceOffset = static_cast<size_t>(row * terrainTileSize * 4);
            const size_t targetOffset = static_cast<size_t>(((atlasY + row) * atlas.width + atlasX) * 4);
            std::memcpy(
                atlas.pixels.data() + static_cast<ptrdiff_t>(targetOffset),
                tilePixels->data() + static_cast<ptrdiff_t>(sourceOffset),
                static_cast<size_t>(terrainTileSize * 4));
        }

        region.u0 = static_cast<float>(atlasX) / static_cast<float>(atlas.width);
        region.v0 = static_cast<float>(atlasY) / static_cast<float>(atlas.height);
        region.u1 = static_cast<float>(atlasX + terrainTileSize) / static_cast<float>(atlas.width);
        region.v1 = static_cast<float>(atlasY + terrainTileSize) / static_cast<float>(atlas.height);
        region.isValid = true;
    }

    return atlas;
}

std::filesystem::path getShaderPath(bgfx::RendererType::Enum rendererType, const char *pShaderName)
{
    const std::filesystem::path shaderRoot = OPENYAMM_BGFX_SHADER_DIR;

    if (rendererType == bgfx::RendererType::OpenGL)
    {
        return shaderRoot / "glsl" / (std::string(pShaderName) + ".bin");
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

std::filesystem::path resolvePhysicalPathRelativeToDocument(
    const EditorDocument &document,
    const std::string &pathText)
{
    if (pathText.empty())
    {
        return {};
    }

    std::filesystem::path path = pathText;

    if (path.is_absolute())
    {
        return path.lexically_normal();
    }

    return (document.scenePhysicalPath().parent_path() / path).lexically_normal();
}

std::optional<Engine::ImagePixelsBgra> loadPhysicalImagePixelsBgra(
    const std::filesystem::path &path,
    BitmapLoadCache &bitmapLoadCache)
{
    const std::string pathKey = path.generic_string();
    std::optional<std::vector<uint8_t>> imageBytes;
    const auto cachedFileIt = bitmapLoadCache.binaryFilesByPath.find(pathKey);

    if (cachedFileIt != bitmapLoadCache.binaryFilesByPath.end())
    {
        imageBytes = cachedFileIt->second;
    }
    else
    {
        imageBytes = readBinaryFile(path);
        if (imageBytes->empty())
        {
            imageBytes = std::nullopt;
        }

        bitmapLoadCache.binaryFilesByPath[pathKey] = imageBytes;
    }

    if (!imageBytes || imageBytes->empty())
    {
        return std::nullopt;
    }

    return Engine::decodeImagePixelsBgra(*imageBytes, pathKey);
}

std::vector<Game::Mm9DatModelRenderRole> buildMm9DatModelRenderRoles(
    const EditorMm9DatWorldSidecar &datWorld)
{
    std::vector<Game::Mm9DatModelRenderRole> roles;
    roles.reserve(datWorld.worldModels.size());

    for (const EditorMm9DatWorldModelSummary &model : datWorld.worldModels)
    {
        Game::Mm9DatModelRenderRole role = {};
        role.sourceModelIndex = model.sourceModelIndex;
        role.visible = model.roles.visible;
        role.terrain = model.roles.terrain;
        role.physicsBsp = model.roles.physicsBsp;
        role.visBsp = model.roles.visBsp;
        role.sky = model.roles.sky;
        role.water = model.roles.water;
        role.triggerOrVolume = model.roles.triggerOrVolume;
        role.movable = model.roles.movable;
        roles.push_back(role);
    }

    return roles;
}

bool shouldRenderMm9DatTriangle(const Game::Mm9DatRenderFilterEntry &filterEntry)
{
    const bool visual =
        (filterEntry.flags
            & (Game::Mm9DatRenderFilterVisual
                | Game::Mm9DatRenderFilterSky
                | Game::Mm9DatRenderFilterWater
                | Game::Mm9DatRenderFilterTerrain
                | Game::Mm9DatRenderFilterPhysics
                | Game::Mm9DatRenderFilterMovable)) != 0;
    const bool hiddenHelper =
        (filterEntry.flags
            & (Game::Mm9DatRenderFilterInvisible
                | Game::Mm9DatRenderFilterWaterVolume
                | Game::Mm9DatRenderFilterRail
                | Game::Mm9DatRenderFilterVisibility
                | Game::Mm9DatRenderFilterTrigger)) != 0;

    return visual && !hiddenHelper;
}

bool shouldIncludeMm9DatTriangleForSubset(
    const Game::Mm9DatRenderFilterEntry &filterEntry,
    EditorOutdoorViewport::Mm9DatWorldRenderSubset subset)
{
    switch (subset)
    {
    case EditorOutdoorViewport::Mm9DatWorldRenderSubset::Sky:
        return (filterEntry.flags & Game::Mm9DatRenderFilterSky) != 0;

    case EditorOutdoorViewport::Mm9DatWorldRenderSubset::Physics:
        return (filterEntry.flags & Game::Mm9DatRenderFilterPhysics) != 0;

    case EditorOutdoorViewport::Mm9DatWorldRenderSubset::Water:
        return (filterEntry.flags & Game::Mm9DatRenderFilterVisibleWater) != 0;

    case EditorOutdoorViewport::Mm9DatWorldRenderSubset::Visibility:
        return (filterEntry.flags & Game::Mm9DatRenderFilterVisibility) != 0;

    case EditorOutdoorViewport::Mm9DatWorldRenderSubset::Invisible:
        return (filterEntry.flags & Game::Mm9DatRenderFilterInvisible) != 0;

    case EditorOutdoorViewport::Mm9DatWorldRenderSubset::Helper:
        return (filterEntry.flags & Game::Mm9DatRenderFilterHelper) != 0;

    case EditorOutdoorViewport::Mm9DatWorldRenderSubset::Trigger:
        return (filterEntry.flags & Game::Mm9DatRenderFilterTrigger) != 0;

    case EditorOutdoorViewport::Mm9DatWorldRenderSubset::Default:
    default:
        return true;
    }
}

bool shouldRenderMm9DatTriangleForSubset(
    const Game::Mm9DatRenderFilterEntry &filterEntry,
    EditorOutdoorViewport::Mm9DatWorldRenderSubset subset)
{
    if (subset == EditorOutdoorViewport::Mm9DatWorldRenderSubset::Default)
    {
        return shouldRenderMm9DatTriangle(filterEntry);
    }

    return shouldIncludeMm9DatTriangleForSubset(filterEntry, subset);
}

const Game::Mm9EventBinding *findMm9ViewportEventBindingForObject(
    const Game::Mm9EventsData &events,
    const std::string &objectId)
{
    for (const Game::Mm9EventBinding &binding : events.bindings)
    {
        if (binding.objectId == objectId)
        {
            return &binding;
        }
    }

    return nullptr;
}

bool mm9ViewportVec3FromFloatVector(const std::vector<float> &values, Game::Mm9DatVec3 &result)
{
    if (values.size() < 3)
    {
        return false;
    }

    result = {values[0], values[1], values[2]};
    return true;
}

bool buildMm9ViewportPreviewMotion(
    const Game::Mm9EventMechanism &mechanism,
    const Game::Mm9EventBindingTarget &target,
    float progress,
    Game::Mm9DatMechanismPreviewMotion &motion)
{
    if (target.targetKind != "odm_bmodel" || !target.bmodelIndex.has_value())
    {
        return false;
    }

    motion = {};
    motion.sourceModelIndex = *target.bmodelIndex;
    motion.progress = std::clamp(progress, 0.0f, 1.0f);
    motion.hasLinearMotion =
        mechanism.linear.hasMoveDir
        && mechanism.linear.hasMoveDist
        && std::fabs(mechanism.linear.moveDistLt) > 0.0001f
        && mm9ViewportVec3FromFloatVector(mechanism.linear.moveDirLt, motion.moveDirLt);
    motion.moveDistLt = mechanism.linear.moveDistLt;
    motion.hasRotationMotion =
        mechanism.rotation.hasRotationPoint
        && mechanism.rotation.hasRotationAngles
        && mm9ViewportVec3FromFloatVector(mechanism.rotation.rotationPointLt, motion.rotationPointLt)
        && mm9ViewportVec3FromFloatVector(mechanism.rotation.rotationAnglesDeg, motion.rotationAnglesDeg);

    return motion.hasLinearMotion || motion.hasRotationMotion;
}

std::vector<Game::Mm9DatMechanismPreviewMotion> buildMm9ViewportPreviewMotions(
    const std::vector<EditorOutdoorViewport::Mm9MechanismPreviewCacheEntry> &mechanismPreviewCache,
    const std::unordered_map<size_t, float> &previewProgressByMechanismIndex)
{
    std::vector<size_t> mechanismIndices;
    mechanismIndices.reserve(previewProgressByMechanismIndex.size());

    for (const std::pair<const size_t, float> &previewEntry : previewProgressByMechanismIndex)
    {
        if (previewEntry.first < mechanismPreviewCache.size())
        {
            mechanismIndices.push_back(previewEntry.first);
        }
    }

    std::sort(mechanismIndices.begin(), mechanismIndices.end());

    std::vector<Game::Mm9DatMechanismPreviewMotion> motions;

    for (size_t mechanismIndex : mechanismIndices)
    {
        const EditorOutdoorViewport::Mm9MechanismPreviewCacheEntry &cacheEntry =
            mechanismPreviewCache[mechanismIndex];
        const float progress = previewProgressByMechanismIndex.at(mechanismIndex);

        for (const EditorOutdoorViewport::Mm9MechanismPreviewTargetCache &target : cacheEntry.targets)
        {
            if (!target.previewable)
            {
                continue;
            }

            Game::Mm9DatMechanismPreviewMotion motion = target.openMotion;
            motion.progress = std::clamp(progress, 0.0f, 1.0f);
            motions.push_back(motion);
        }
    }

    return motions;
}

Game::Mm9DatVec3 mm9LtToOpenYammViewportPoint(const Game::Mm9DatVec3 &value)
{
    return {value.x, value.z, value.y};
}

Game::Mm9DatVec3 mm9OpenYammToLtViewportPoint(const Game::Mm9DatVec3 &value)
{
    return {value.x, value.z, value.y};
}

Game::Mm9DatVec3 transformMm9ViewportPoint(
    const Game::Mm9DatVec3 &openYammPosition,
    const Game::Mm9DatMechanismPreviewMotion &motion)
{
    constexpr float Pi = 3.14159265358979323846f;
    Game::Mm9DatVec3 sourcePositionLt = mm9OpenYammToLtViewportPoint(openYammPosition);

    if (motion.hasLinearMotion && std::fabs(motion.moveDistLt) > 0.0001f)
    {
        sourcePositionLt.x += motion.moveDirLt.x * motion.moveDistLt * motion.progress;
        sourcePositionLt.y += motion.moveDirLt.y * motion.moveDistLt * motion.progress;
        sourcePositionLt.z += motion.moveDirLt.z * motion.moveDistLt * motion.progress;
    }

    if (motion.hasRotationMotion)
    {
        const Game::Mm9DatVec3 angles = {
            motion.rotationAnglesDeg.x * motion.progress * Pi / 180.0f,
            motion.rotationAnglesDeg.y * motion.progress * Pi / 180.0f,
            motion.rotationAnglesDeg.z * motion.progress * Pi / 180.0f,
        };
        Game::Mm9DatVec3 relative = {
            sourcePositionLt.x - motion.rotationPointLt.x,
            sourcePositionLt.y - motion.rotationPointLt.y,
            sourcePositionLt.z - motion.rotationPointLt.z,
        };

        if (std::fabs(angles.x) > 0.0001f)
        {
            const float angleSin = std::sin(angles.x);
            const float angleCos = std::cos(angles.x);
            relative = {
                relative.x,
                relative.y * angleCos - relative.z * angleSin,
                relative.y * angleSin + relative.z * angleCos,
            };
        }

        if (std::fabs(angles.y) > 0.0001f)
        {
            const float angleSin = std::sin(angles.y);
            const float angleCos = std::cos(angles.y);
            relative = {
                relative.x * angleCos + relative.z * angleSin,
                relative.y,
                -relative.x * angleSin + relative.z * angleCos,
            };
        }

        if (std::fabs(angles.z) > 0.0001f)
        {
            const float angleSin = std::sin(angles.z);
            const float angleCos = std::cos(angles.z);
            relative = {
                relative.x * angleCos - relative.y * angleSin,
                relative.x * angleSin + relative.y * angleCos,
                relative.z,
            };
        }

        sourcePositionLt = {
            motion.rotationPointLt.x + relative.x,
            motion.rotationPointLt.y + relative.y,
            motion.rotationPointLt.z + relative.z,
        };
    }

    return mm9LtToOpenYammViewportPoint(sourcePositionLt);
}

std::array<float, 16> mm9ViewportPreviewTransformForMotions(
    const std::vector<Game::Mm9DatMechanismPreviewMotion> &motions)
{
    const auto transformPoint =
        [&motions](const Game::Mm9DatVec3 &point) -> Game::Mm9DatVec3
    {
        Game::Mm9DatVec3 transformedPoint = point;

        for (const Game::Mm9DatMechanismPreviewMotion &motion : motions)
        {
            transformedPoint = transformMm9ViewportPoint(transformedPoint, motion);
        }

        return transformedPoint;
    };

    const Game::Mm9DatVec3 origin = transformPoint({0.0f, 0.0f, 0.0f});
    const Game::Mm9DatVec3 xAxis = transformPoint({1.0f, 0.0f, 0.0f});
    const Game::Mm9DatVec3 yAxis = transformPoint({0.0f, 1.0f, 0.0f});
    const Game::Mm9DatVec3 zAxis = transformPoint({0.0f, 0.0f, 1.0f});

    return {
        xAxis.x - origin.x, xAxis.y - origin.y, xAxis.z - origin.z, 0.0f,
        yAxis.x - origin.x, yAxis.y - origin.y, yAxis.z - origin.z, 0.0f,
        zAxis.x - origin.x, zAxis.y - origin.y, zAxis.z - origin.z, 0.0f,
        origin.x, origin.y, origin.z, 1.0f,
    };
}

std::unordered_map<size_t, std::array<float, 16>> mm9ViewportPreviewTransformsBySourceModelIndex(
    const std::vector<Game::Mm9DatMechanismPreviewMotion> &motions)
{
    std::unordered_map<size_t, std::vector<Game::Mm9DatMechanismPreviewMotion>> motionsBySourceModelIndex;

    for (const Game::Mm9DatMechanismPreviewMotion &motion : motions)
    {
        motionsBySourceModelIndex[motion.sourceModelIndex].push_back(motion);
    }

    std::unordered_map<size_t, std::array<float, 16>> transformsBySourceModelIndex;

    for (const auto &[sourceModelIndex, sourceModelMotions] : motionsBySourceModelIndex)
    {
        transformsBySourceModelIndex.emplace(
            sourceModelIndex,
            mm9ViewportPreviewTransformForMotions(sourceModelMotions));
    }

    return transformsBySourceModelIndex;
}

bx::Vec3 transformPointByMatrix(const float *pTransform, const bx::Vec3 &point)
{
    if (pTransform == nullptr)
    {
        return point;
    }

    return {
        point.x * pTransform[0] + point.y * pTransform[4] + point.z * pTransform[8] + pTransform[12],
        point.x * pTransform[1] + point.y * pTransform[5] + point.z * pTransform[9] + pTransform[13],
        point.x * pTransform[2] + point.y * pTransform[6] + point.z * pTransform[10] + pTransform[14],
    };
}

bx::Vec3 mm9DatTriangleNormal(const Game::Mm9DatRenderTriangle &triangle)
{
    const bx::Vec3 v0 = {
        triangle.vertices[0].x,
        triangle.vertices[0].y,
        triangle.vertices[0].z
    };
    const bx::Vec3 v1 = {
        triangle.vertices[1].x,
        triangle.vertices[1].y,
        triangle.vertices[1].z
    };
    const bx::Vec3 v2 = {
        triangle.vertices[2].x,
        triangle.vertices[2].y,
        triangle.vertices[2].z
    };
    const bx::Vec3 edgeA = {
        v1.x - v0.x,
        v1.y - v0.y,
        v1.z - v0.z
    };
    const bx::Vec3 edgeB = {
        v2.x - v0.x,
        v2.y - v0.y,
        v2.z - v0.z
    };
    const bx::Vec3 normal = {
        edgeA.y * edgeB.z - edgeA.z * edgeB.y,
        edgeA.z * edgeB.x - edgeA.x * edgeB.z,
        edgeA.x * edgeB.y - edgeA.y * edgeB.x
    };
    const float normalLength =
        std::sqrt(normal.x * normal.x + normal.y * normal.y + normal.z * normal.z);

    if (normalLength <= 0.0001f)
    {
        return {0.0f, 0.0f, 1.0f};
    }

    return {
        normal.x / normalLength,
        normal.y / normalLength,
        normal.z / normalLength
    };
}

void appendMm9DatTexturedTriangleVertices(
    const Game::Mm9DatRenderTriangle &triangle,
    int textureWidth,
    int textureHeight,
    std::vector<EditorOutdoorViewport::TexturedPreviewVertex> &vertices)
{
    const float uScale = textureWidth > 0 ? 1.0f / static_cast<float>(textureWidth) : 1.0f;
    const float vScale = textureHeight > 0 ? 1.0f / static_cast<float>(textureHeight) : 1.0f;

    for (const Game::Mm9DatRenderVertex &vertex : triangle.vertices)
    {
        vertices.push_back({
            vertex.x,
            vertex.y,
            vertex.z,
            vertex.uPixels * uScale,
            vertex.vPixels * vScale});
    }
}

void appendMm9DatProceduralTriangleVertices(
    const Game::Mm9DatRenderTriangle &triangle,
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> &vertices)
{
    const bx::Vec3 normal = mm9DatTriangleNormal(triangle);

    for (const Game::Mm9DatRenderVertex &vertex : triangle.vertices)
    {
        vertices.push_back({
            vertex.x,
            vertex.y,
            vertex.z,
            vertex.uPixels,
            vertex.vPixels,
            normal.x,
            normal.y,
            normal.z,
            0.0f});
    }
}

void appendTexturedVerticesAsMissingProcedural(
    const std::vector<EditorOutdoorViewport::TexturedPreviewVertex> &source,
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> &target)
{
    for (const EditorOutdoorViewport::TexturedPreviewVertex &vertex : source)
    {
        target.push_back({vertex.x, vertex.y, vertex.z, vertex.u, vertex.v, 0.0f, 0.0f, 1.0f, 0.0f});
    }
}

bgfx::ShaderHandle loadShader(const char *pShaderName)
{
    const std::filesystem::path shaderPath = getShaderPath(bgfx::getRendererType(), pShaderName);

    if (shaderPath.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::vector<uint8_t> shaderBytes = readBinaryFile(shaderPath);

    if (shaderBytes.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createShader(bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size())));
}

bgfx::ProgramHandle loadProgram(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadShader(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadShader(pFragmentShaderName);

    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
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

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

uint32_t heightColor(float normalizedHeight)
{
    const float clampedHeight = std::clamp(normalizedHeight, 0.0f, 1.0f);
    const uint8_t red = static_cast<uint8_t>(std::lround(56.0f + clampedHeight * 92.0f));
    const uint8_t green = static_cast<uint8_t>(std::lround(82.0f + clampedHeight * 110.0f));
    const uint8_t blue = static_cast<uint8_t>(std::lround(44.0f + clampedHeight * 56.0f));
    return makeAbgr(red, green, blue);
}

float squaredLength2(float x, float y)
{
    return x * x + y * y;
}

EditorBModelSourceTransform sourceTransformFromBModel(const Game::OutdoorBModel &bmodel)
{
    EditorBModelSourceTransform transform = {};

    if (bmodel.vertices.empty())
    {
        transform.originX = static_cast<float>(bmodel.boundingCenterX);
        transform.originY = static_cast<float>(bmodel.boundingCenterY);
        transform.originZ = static_cast<float>(bmodel.boundingCenterZ);
        return transform;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    transform.originX = (minX + maxX) * 0.5f;
    transform.originY = (minY + maxY) * 0.5f;
    transform.originZ = (minZ + maxZ) * 0.5f;
    return transform;
}

std::array<float, 3> rotateBasisVectorAroundAxis(
    const std::array<float, 3> &vector,
    const bx::Vec3 &axis,
    float angleRadians)
{
    const float axisLength = std::sqrt(axis.x * axis.x + axis.y * axis.y + axis.z * axis.z);

    if (axisLength <= 0.0001f)
    {
        return vector;
    }

    const bx::Vec3 normalizedAxis = {axis.x / axisLength, axis.y / axisLength, axis.z / axisLength};
    const float cosAngle = std::cos(angleRadians);
    const float sinAngle = std::sin(angleRadians);
    const float dotProduct =
        vector[0] * normalizedAxis.x
        + vector[1] * normalizedAxis.y
        + vector[2] * normalizedAxis.z;
    const bx::Vec3 crossProduct = {
        normalizedAxis.y * vector[2] - normalizedAxis.z * vector[1],
        normalizedAxis.z * vector[0] - normalizedAxis.x * vector[2],
        normalizedAxis.x * vector[1] - normalizedAxis.y * vector[0]
    };

    return {
        vector[0] * cosAngle + crossProduct.x * sinAngle + normalizedAxis.x * dotProduct * (1.0f - cosAngle),
        vector[1] * cosAngle + crossProduct.y * sinAngle + normalizedAxis.y * dotProduct * (1.0f - cosAngle),
        vector[2] * cosAngle + crossProduct.z * sinAngle + normalizedAxis.z * dotProduct * (1.0f - cosAngle)
    };
}

bx::Vec3 vecAdd(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

bx::Vec3 vecSubtract(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

bx::Vec3 vecScale(const bx::Vec3 &value, float scale)
{
    return {value.x * scale, value.y * scale, value.z * scale};
}

float vecDot(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

bx::Vec3 vecCross(const bx::Vec3 &left, const bx::Vec3 &right)
{
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x
    };
}

float vecLength(const bx::Vec3 &value)
{
    return std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
}

bx::Vec3 vecNormalize(const bx::Vec3 &value)
{
    const float length = vecLength(value);

    if (length <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {value.x / length, value.y / length, value.z / length};
}

bx::Vec3 vecLerp(const bx::Vec3 &start, const bx::Vec3 &end, float t)
{
    return {
        start.x + (end.x - start.x) * t,
        start.y + (end.y - start.y) * t,
        start.z + (end.z - start.z) * t
    };
}

float lerpFloat(float start, float end, float t)
{
    return start + (end - start) * t;
}

float easeOutCubic(float t)
{
    const float inverse = 1.0f - t;
    return 1.0f - inverse * inverse * inverse;
}

void recalculateOutdoorTileUsage(Game::OutdoorMapData &outdoorMapData)
{
    std::array<bool, 256> seenTiles = {};
    outdoorMapData.uniqueTileCount = 0;

    for (uint8_t tileId : outdoorMapData.tileMap)
    {
        if (!seenTiles[tileId])
        {
            seenTiles[tileId] = true;
            ++outdoorMapData.uniqueTileCount;
        }
    }
}

void recalculateOutdoorHeightRange(Game::OutdoorMapData &outdoorMapData)
{
    if (outdoorMapData.heightMap.empty())
    {
        outdoorMapData.minHeightSample = 0;
        outdoorMapData.maxHeightSample = 0;
        return;
    }

    const auto [minIt, maxIt] = std::minmax_element(outdoorMapData.heightMap.begin(), outdoorMapData.heightMap.end());
    outdoorMapData.minHeightSample = *minIt;
    outdoorMapData.maxHeightSample = *maxIt;
}

uint32_t terrainNoiseHash(int x, int y)
{
    uint32_t value = static_cast<uint32_t>(x) * 0x9e3779b9u;
    value ^= static_cast<uint32_t>(y) * 0x85ebca6bu;
    value ^= value >> 16;
    value *= 0x7feb352du;
    value ^= value >> 15;
    value *= 0x846ca68bu;
    value ^= value >> 16;
    return value;
}

float wrapAngleRadians(float angle)
{
    while (angle > bx::kPi)
    {
        angle -= bx::kPi2;
    }

    while (angle < -bx::kPi)
    {
        angle += bx::kPi2;
    }

    return angle;
}

float shortestAngleDelta(float from, float to)
{
    return wrapAngleRadians(to - from);
}

float bmodelRotationHandleRadius(const Game::OutdoorBModel &bmodel)
{
    const float rawRadius = std::max(static_cast<float>(bmodel.boundingRadius) * 1.15f, 768.0f);
    return std::clamp(rawRadius, 768.0f, 4096.0f);
}

void recomputeBModelBounds(Game::OutdoorBModel &bmodel)
{
    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    if (!std::isfinite(minX) || !std::isfinite(maxX))
    {
        return;
    }

    const float centerX = (minX + maxX) * 0.5f;
    const float centerY = (minY + maxY) * 0.5f;
    const float centerZ = (minZ + maxZ) * 0.5f;
    float maxRadiusSquared = 0.0f;

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float deltaX = static_cast<float>(vertex.x) - centerX;
        const float deltaY = static_cast<float>(vertex.y) - centerY;
        const float deltaZ = static_cast<float>(vertex.z) - centerZ;
        maxRadiusSquared = std::max(maxRadiusSquared, deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    }

    bmodel.minX = static_cast<int>(std::floor(minX));
    bmodel.minY = static_cast<int>(std::floor(minY));
    bmodel.minZ = static_cast<int>(std::floor(minZ));
    bmodel.maxX = static_cast<int>(std::ceil(maxX));
    bmodel.maxY = static_cast<int>(std::ceil(maxY));
    bmodel.maxZ = static_cast<int>(std::ceil(maxZ));
    bmodel.boundingCenterX = static_cast<int>(std::lround(centerX));
    bmodel.boundingCenterY = static_cast<int>(std::lround(centerY));
    bmodel.boundingCenterZ = static_cast<int>(std::lround(centerZ));
    bmodel.boundingRadius = static_cast<int>(std::ceil(std::sqrt(maxRadiusSquared)));
}

bool applyBModelYawRotation(
    Game::OutdoorBModel &bmodel,
    const std::vector<Game::OutdoorBModelVertex> &sourceVertices,
    float yawRadians)
{
    if (sourceVertices.empty() || sourceVertices.size() != bmodel.vertices.size())
    {
        return false;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : sourceVertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
    }

    if (!std::isfinite(minX) || !std::isfinite(maxX))
    {
        return false;
    }

    const float pivotX = (minX + maxX) * 0.5f;
    const float pivotY = (minY + maxY) * 0.5f;
    const float cosYaw = std::cos(yawRadians);
    const float sinYaw = std::sin(yawRadians);
    bool changed = false;

    for (size_t index = 0; index < sourceVertices.size(); ++index)
    {
        const Game::OutdoorBModelVertex &sourceVertex = sourceVertices[index];
        const float localX = static_cast<float>(sourceVertex.x) - pivotX;
        const float localY = static_cast<float>(sourceVertex.y) - pivotY;
        const float rotatedX = localX * cosYaw - localY * sinYaw;
        const float rotatedY = localX * sinYaw + localY * cosYaw;
        const int newX = static_cast<int>(std::lround(pivotX + rotatedX));
        const int newY = static_cast<int>(std::lround(pivotY + rotatedY));

        if (bmodel.vertices[index].x != newX || bmodel.vertices[index].y != newY)
        {
            changed = true;
        }

        bmodel.vertices[index].x = newX;
        bmodel.vertices[index].y = newY;
        bmodel.vertices[index].z = sourceVertex.z;
    }

    if (changed)
    {
        recomputeBModelBounds(bmodel);
    }

    return changed;
}

Game::OutdoorBModelVertex transformImportedPreviewVertex(
    const EditorBModelSourceTransform &transform,
    float localX,
    float localY,
    float localZ)
{
    Game::OutdoorBModelVertex vertex = {};
    const float worldX =
        transform.originX
        + localX * transform.basisX[0]
        + localY * transform.basisY[0]
        + localZ * transform.basisZ[0];
    const float worldY =
        transform.originY
        + localX * transform.basisX[1]
        + localY * transform.basisY[1]
        + localZ * transform.basisZ[1];
    const float worldZ =
        transform.originZ
        + localX * transform.basisX[2]
        + localY * transform.basisY[2]
        + localZ * transform.basisZ[2];
    vertex.x = static_cast<int>(std::lround(worldX));
    vertex.y = static_cast<int>(std::lround(worldY));
    vertex.z = static_cast<int>(std::lround(worldZ));
    return vertex;
}

void appendUniqueIndoorFaceIds(
    std::vector<uint16_t> &targetFaceIds,
    const std::vector<uint16_t> &sourceFaceIds)
{
    for (uint16_t faceId : sourceFaceIds)
    {
        if (std::find(targetFaceIds.begin(), targetFaceIds.end(), faceId) == targetFaceIds.end())
        {
            targetFaceIds.push_back(faceId);
        }
    }
}

std::vector<uint16_t> indoorSectorFaceIds(const Game::IndoorMapData &indoorMapData, uint16_t sectorId)
{
    if (sectorId >= indoorMapData.sectors.size())
    {
        return {};
    }

    const Game::IndoorSector &sector = indoorMapData.sectors[sectorId];
    std::vector<uint16_t> faceIds;
    faceIds.reserve(sector.faceIds.size() + sector.portalFaceIds.size());
    appendUniqueIndoorFaceIds(faceIds, sector.faceIds);
    appendUniqueIndoorFaceIds(faceIds, sector.portalFaceIds);
    return faceIds;
}

std::vector<uint16_t> connectedIndoorSectorIds(const Game::IndoorMapData &indoorMapData, uint16_t sectorId)
{
    if (sectorId >= indoorMapData.sectors.size())
    {
        return {};
    }

    const Game::IndoorSector &sector = indoorMapData.sectors[sectorId];
    std::vector<uint16_t> connectedSectorIds;

    const auto appendConnectedSector =
        [&](uint16_t connectedSectorId)
    {
        if (connectedSectorId >= indoorMapData.sectors.size())
        {
            return;
        }

        if (std::find(connectedSectorIds.begin(), connectedSectorIds.end(), connectedSectorId)
            == connectedSectorIds.end())
        {
            connectedSectorIds.push_back(connectedSectorId);
        }
    };

    const auto collectFromFaces =
        [&](const std::vector<uint16_t> &faceIds)
    {
        for (uint16_t faceId : faceIds)
        {
            if (faceId >= indoorMapData.faces.size())
            {
                continue;
            }

            const Game::IndoorFace &face = indoorMapData.faces[faceId];
            const bool isPortal = face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal);

            if (!isPortal)
            {
                continue;
            }

            if (face.roomNumber == sectorId)
            {
                appendConnectedSector(face.roomBehindNumber);
            }
            else if (face.roomBehindNumber == sectorId)
            {
                appendConnectedSector(face.roomNumber);
            }
        }
    };

    collectFromFaces(sector.portalFaceIds);
    collectFromFaces(sector.faceIds);
    return connectedSectorIds;
}

bool indoorSectorBoundsContainPoint(
    const Game::IndoorMapData &indoorMapData,
    uint16_t sectorId,
    const bx::Vec3 &point)
{
    if (sectorId >= indoorMapData.sectors.size())
    {
        return false;
    }

    const Game::IndoorSector &sector = indoorMapData.sectors[sectorId];
    return point.x >= static_cast<float>(sector.minX)
        && point.x <= static_cast<float>(sector.maxX)
        && point.y >= static_cast<float>(sector.minY)
        && point.y <= static_cast<float>(sector.maxY)
        && point.z >= static_cast<float>(sector.minZ)
        && point.z <= static_cast<float>(sector.maxZ);
}

bool indoorFaceMatchesRoomIsolation(
    const Game::IndoorFace &face,
    const std::optional<uint16_t> &isolatedRoomId)
{
    if (!isolatedRoomId.has_value())
    {
        return true;
    }

    return face.roomNumber == *isolatedRoomId || face.roomBehindNumber == *isolatedRoomId;
}

bool indoorGeometryKindHiddenByView(
    Game::IndoorFaceKind kind,
    bool showIndoorFloors,
    bool showIndoorCeilings)
{
    if (!showIndoorFloors && kind == Game::IndoorFaceKind::Floor)
    {
        return true;
    }

    if (!showIndoorCeilings && kind == Game::IndoorFaceKind::Ceiling)
    {
        return true;
    }

    return false;
}

bool indoorMarkerVisibleForIsolation(
    const Game::IndoorMapData &indoorMapData,
    const std::optional<uint16_t> &isolatedRoomId,
    const bx::Vec3 &point,
    std::optional<int16_t> sectorId = std::nullopt)
{
    if (!isolatedRoomId.has_value())
    {
        return true;
    }

    if (sectorId.has_value() && *sectorId >= 0)
    {
        return static_cast<uint16_t>(*sectorId) == *isolatedRoomId;
    }

    return indoorSectorBoundsContainPoint(indoorMapData, *isolatedRoomId, point);
}

bool isIndoorMovableSelectionKind(EditorSelectionKind kind)
{
    return kind == EditorSelectionKind::Entity
        || kind == EditorSelectionKind::Actor
        || kind == EditorSelectionKind::Spawn
        || kind == EditorSelectionKind::SpriteObject
        || kind == EditorSelectionKind::Light;
}

bool indoorDoorVisibleForIsolation(
    const Game::IndoorMapData &indoorMapData,
    const Game::MapDeltaDoor &door,
    const std::optional<uint16_t> &isolatedRoomId,
    const std::optional<bx::Vec3> &center)
{
    if (!isolatedRoomId.has_value())
    {
        return true;
    }

    for (uint16_t sectorId : door.sectorIds)
    {
        if (sectorId == *isolatedRoomId)
        {
            return true;
        }
    }

    for (uint16_t faceId : door.faceIds)
    {
        if (faceId >= indoorMapData.faces.size())
        {
            continue;
        }

        if (indoorFaceMatchesRoomIsolation(indoorMapData.faces[faceId], isolatedRoomId))
        {
            return true;
        }
    }

    return center.has_value() && indoorSectorBoundsContainPoint(indoorMapData, *isolatedRoomId, *center);
}

uint8_t classifyImportedPreviewPolygonType(const ImportedModel &importedModel, const ImportedModelFace &face)
{
    if (face.vertices.size() < 3)
    {
        return 0;
    }

    const ImportedModelPosition &a = importedModel.positions[face.vertices[0].positionIndex];
    const ImportedModelPosition &b = importedModel.positions[face.vertices[1].positionIndex];
    const ImportedModelPosition &c = importedModel.positions[face.vertices[2].positionIndex];
    const float abX = b.x - a.x;
    const float abY = b.y - a.y;
    const float abZ = b.z - a.z;
    const float acX = c.x - a.x;
    const float acY = c.y - a.y;
    const float acZ = c.z - a.z;
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    const float normalLength = std::sqrt(normalX * normalX + normalY * normalY + normalZ * normalZ);

    if (normalLength <= 0.0001f)
    {
        return 0;
    }

    const float normalZNormalized = std::fabs(normalZ / normalLength);

    if (normalZNormalized >= 0.85f)
    {
        return 0x3;
    }

    if (normalZNormalized >= 0.45f)
    {
        return 0x4;
    }

    return 0;
}

float previewFaceNormalZ(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return 0.0f;
    }

    const Game::OutdoorBModelVertex &a = vertices[face.vertexIndices[0]];
    const Game::OutdoorBModelVertex &b = vertices[face.vertexIndices[1]];
    const Game::OutdoorBModelVertex &c = vertices[face.vertexIndices[2]];
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    return abX * acY - abY * acX;
}

float previewFaceOutwardDot(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return 0.0f;
    }

    const Game::OutdoorBModelVertex &a = vertices[face.vertexIndices[0]];
    const Game::OutdoorBModelVertex &b = vertices[face.vertexIndices[1]];
    const Game::OutdoorBModelVertex &c = vertices[face.vertexIndices[2]];
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    float faceCenterX = 0.0f;
    float faceCenterY = 0.0f;
    float faceCenterZ = 0.0f;

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        faceCenterX += static_cast<float>(vertices[vertexIndex].x);
        faceCenterY += static_cast<float>(vertices[vertexIndex].y);
        faceCenterZ += static_cast<float>(vertices[vertexIndex].z);
    }

    const float invVertexCount = 1.0f / static_cast<float>(face.vertexIndices.size());
    faceCenterX *= invVertexCount;
    faceCenterY *= invVertexCount;
    faceCenterZ *= invVertexCount;
    return normalX * (faceCenterX - modelCenterX)
        + normalY * (faceCenterY - modelCenterY)
        + normalZ * (faceCenterZ - modelCenterZ);
}

void reversePreviewFaceWinding(Game::OutdoorBModelFace &face)
{
    std::reverse(face.vertexIndices.begin(), face.vertexIndices.end());
}

void orientImportedPreviewFaceWinding(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    const bool shouldReverse =
        (face.polygonType == 0x3 || face.polygonType == 0x4)
        ? (previewFaceNormalZ(vertices, face) < 0.0f)
        : (previewFaceOutwardDot(vertices, face, modelCenterX, modelCenterY, modelCenterZ) < 0.0f);

    if (shouldReverse)
    {
        reversePreviewFaceWinding(face);
    }
}

std::optional<Game::OutdoorBModel> buildImportedPreviewBModel(
    const ImportedModel &importedModel,
    float importScale,
    const Game::OutdoorBModel *pPlacementTemplate,
    const EditorBModelSourceTransform *pSourceTransform,
    const bx::Vec3 *pFloorPoint)
{
    if (importScale <= 0.0f || importedModel.positions.empty() || importedModel.faces.empty())
    {
        return std::nullopt;
    }

    Game::OutdoorBModel bmodel = {};
    std::vector<Game::OutdoorBModelVertex> importedVertices;
    importedVertices.reserve(importedModel.positions.size());
    float importedMinX = std::numeric_limits<float>::max();
    float importedMinY = std::numeric_limits<float>::max();
    float importedMinZ = std::numeric_limits<float>::max();
    float importedMaxX = std::numeric_limits<float>::lowest();
    float importedMaxY = std::numeric_limits<float>::lowest();
    float importedMaxZ = std::numeric_limits<float>::lowest();

    for (const ImportedModelPosition &position : importedModel.positions)
    {
        Game::OutdoorBModelVertex vertex = {};
        vertex.x = static_cast<int>(std::lround(position.x * importScale));
        vertex.y = static_cast<int>(std::lround(position.y * importScale));
        vertex.z = static_cast<int>(std::lround(position.z * importScale));
        importedVertices.push_back(vertex);
        importedMinX = std::min(importedMinX, static_cast<float>(vertex.x));
        importedMinY = std::min(importedMinY, static_cast<float>(vertex.y));
        importedMinZ = std::min(importedMinZ, static_cast<float>(vertex.z));
        importedMaxX = std::max(importedMaxX, static_cast<float>(vertex.x));
        importedMaxY = std::max(importedMaxY, static_cast<float>(vertex.y));
        importedMaxZ = std::max(importedMaxZ, static_cast<float>(vertex.z));
    }

    const float importedCenterX = (importedMinX + importedMaxX) * 0.5f;
    const float importedCenterY = (importedMinY + importedMaxY) * 0.5f;
    const float importedCenterZ = (importedMinZ + importedMaxZ) * 0.5f;
    EditorBModelSourceTransform sourceTransform = {};
    sourceTransform.originX = importedCenterX;
    sourceTransform.originY = importedCenterY;
    sourceTransform.originZ = importedCenterZ;

    if (pSourceTransform != nullptr)
    {
        sourceTransform = *pSourceTransform;
    }
    else if (pPlacementTemplate != nullptr)
    {
        sourceTransform = sourceTransformFromBModel(*pPlacementTemplate);

        if (!pPlacementTemplate->vertices.empty())
        {
            float templateMinZ = std::numeric_limits<float>::max();

            for (const Game::OutdoorBModelVertex &vertex : pPlacementTemplate->vertices)
            {
                templateMinZ = std::min(templateMinZ, static_cast<float>(vertex.z));
            }

            sourceTransform.originZ = templateMinZ + (importedCenterZ - importedMinZ);
        }
    }
    else if (pFloorPoint != nullptr)
    {
        sourceTransform.originX = pFloorPoint->x;
        sourceTransform.originY = pFloorPoint->y;
        sourceTransform.originZ = pFloorPoint->z + (importedCenterZ - importedMinZ);
    }

    for (Game::OutdoorBModelVertex &vertex : importedVertices)
    {
        const float localX = static_cast<float>(vertex.x) - importedCenterX;
        const float localY = static_cast<float>(vertex.y) - importedCenterY;
        const float localZ = static_cast<float>(vertex.z) - importedCenterZ;
        vertex = transformImportedPreviewVertex(sourceTransform, localX, localY, localZ);
    }

    bmodel.vertices = std::move(importedVertices);

    for (const ImportedModelFace &importedFace : importedModel.faces)
    {
        Game::OutdoorBModelFace face = {};
        face.polygonType = classifyImportedPreviewPolygonType(importedModel, importedFace);

        for (const ImportedModelFaceVertex &importedVertex : importedFace.vertices)
        {
            face.vertexIndices.push_back(static_cast<uint16_t>(importedVertex.positionIndex));
        }

        orientImportedPreviewFaceWinding(
            bmodel.vertices,
            face,
            sourceTransform.originX,
            sourceTransform.originY,
            sourceTransform.originZ);
        bmodel.faces.push_back(std::move(face));
    }

    recomputeBModelBounds(bmodel);
    return bmodel;
}

bool applyBModelAxisRotation(
    Game::OutdoorBModel &bmodel,
    const std::vector<Game::OutdoorBModelVertex> &sourceVertices,
    const bx::Vec3 &pivot,
    const bx::Vec3 &axis,
    float angleRadians)
{
    if (sourceVertices.empty() || sourceVertices.size() != bmodel.vertices.size())
    {
        return false;
    }

    const bx::Vec3 normalizedAxis = vecNormalize(axis);

    if (vecLength(normalizedAxis) <= 0.0001f)
    {
        return false;
    }

    const float cosAngle = std::cos(angleRadians);
    const float sinAngle = std::sin(angleRadians);
    bool changed = false;

    for (size_t index = 0; index < sourceVertices.size(); ++index)
    {
        const Game::OutdoorBModelVertex &sourceVertex = sourceVertices[index];
        const bx::Vec3 local = {
            static_cast<float>(sourceVertex.x) - pivot.x,
            static_cast<float>(sourceVertex.y) - pivot.y,
            static_cast<float>(sourceVertex.z) - pivot.z
        };
        const bx::Vec3 axisCrossLocal = vecCross(normalizedAxis, local);
        const float axisDotLocal = vecDot(normalizedAxis, local);
        const bx::Vec3 rotated = {
            local.x * cosAngle + axisCrossLocal.x * sinAngle + normalizedAxis.x * axisDotLocal * (1.0f - cosAngle),
            local.y * cosAngle + axisCrossLocal.y * sinAngle + normalizedAxis.y * axisDotLocal * (1.0f - cosAngle),
            local.z * cosAngle + axisCrossLocal.z * sinAngle + normalizedAxis.z * axisDotLocal * (1.0f - cosAngle)
        };
        const int newX = static_cast<int>(std::lround(pivot.x + rotated.x));
        const int newY = static_cast<int>(std::lround(pivot.y + rotated.y));
        const int newZ = static_cast<int>(std::lround(pivot.z + rotated.z));

        if (bmodel.vertices[index].x != newX || bmodel.vertices[index].y != newY || bmodel.vertices[index].z != newZ)
        {
            changed = true;
        }

        bmodel.vertices[index].x = newX;
        bmodel.vertices[index].y = newY;
        bmodel.vertices[index].z = newZ;
    }

    if (changed)
    {
        recomputeBModelBounds(bmodel);
    }

    return changed;
}

bool intersectRayPlane(
    const bx::Vec3 &rayOrigin,
    const bx::Vec3 &rayDirection,
    const bx::Vec3 &planePoint,
    const bx::Vec3 &planeNormal,
    bx::Vec3 &intersection)
{
    const float denominator = vecDot(rayDirection, planeNormal);

    if (std::fabs(denominator) <= 0.0001f)
    {
        return false;
    }

    const bx::Vec3 planeOffset = {
        planePoint.x - rayOrigin.x,
        planePoint.y - rayOrigin.y,
        planePoint.z - rayOrigin.z
    };
    const float distance = vecDot(planeOffset, planeNormal) / denominator;

    if (distance < 0.0f)
    {
        return false;
    }

    intersection = {
        rayOrigin.x + rayDirection.x * distance,
        rayOrigin.y + rayDirection.y * distance,
        rayOrigin.z + rayDirection.z * distance
    };
    return true;
}

float signedAngleAroundAxis(const bx::Vec3 &startVector, const bx::Vec3 &endVector, const bx::Vec3 &axis)
{
    const bx::Vec3 normalizedStart = vecNormalize(startVector);
    const bx::Vec3 normalizedEnd = vecNormalize(endVector);
    const bx::Vec3 normalizedAxis = vecNormalize(axis);
    const bx::Vec3 crossProduct = vecCross(normalizedStart, normalizedEnd);
    const float sine = vecDot(normalizedAxis, crossProduct);
    const float cosine = std::clamp(vecDot(normalizedStart, normalizedEnd), -1.0f, 1.0f);
    return std::atan2(sine, cosine);
}

std::optional<bx::Vec3> bmodelPlacementCenterForFloorPoint(
    const Game::OutdoorMapData &outdoorMapData,
    size_t bmodelIndex,
    const bx::Vec3 &floorPoint)
{
    if (bmodelIndex >= outdoorMapData.bmodels.size())
    {
        return std::nullopt;
    }

    const Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];
    float minZ = std::numeric_limits<float>::max();
    float centerX = 0.0f;
    float centerY = 0.0f;
    float centerZ = 0.0f;
    int vertexCount = 0;

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        centerX += static_cast<float>(vertex.x);
        centerY += static_cast<float>(vertex.y);
        centerZ += static_cast<float>(vertex.z);
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        ++vertexCount;
    }

    if (vertexCount == 0 || !std::isfinite(minZ))
    {
        return std::nullopt;
    }

    const float scale = 1.0f / static_cast<float>(vertexCount);
    centerX *= scale;
    centerY *= scale;
    centerZ *= scale;
    const float terrainZ = Game::sampleOutdoorTerrainHeight(outdoorMapData, floorPoint.x, floorPoint.y);
    const float baseOffsetZ = centerZ - minZ;
    return bx::Vec3{floorPoint.x, floorPoint.y, terrainZ + baseOffsetZ};
}

const char *placementKindLabel(EditorSelectionKind kind)
{
    switch (kind)
    {
    case EditorSelectionKind::Terrain:
        return "Terrain";

    case EditorSelectionKind::BModel:
        return "BModel";

    case EditorSelectionKind::InteractiveFace:
        return "Face";

    case EditorSelectionKind::Entity:
        return "Entity";

    case EditorSelectionKind::Spawn:
        return "Spawn";

    case EditorSelectionKind::Actor:
        return "Actor";

    case EditorSelectionKind::SpriteObject:
        return "Sprite Object";

    case EditorSelectionKind::ModelInstance:
        return "Model Instance";

    case EditorSelectionKind::Mm9ScriptedObject:
        return "MM9 Scripted Object";

    case EditorSelectionKind::Mm9WorldModel:
        return "DAT World Model";

    case EditorSelectionKind::Mm9DatPolygon:
        return "DAT Polygon";

    case EditorSelectionKind::Mm9MaterialTexture:
        return "DTX Texture";

    case EditorSelectionKind::Mm9RawObject:
        return "DAT Raw Object";

    case EditorSelectionKind::Mm9EventObject:
        return "MM9 Event Object";

    case EditorSelectionKind::Mm9Mechanism:
        return "MM9 Mechanism";

    case EditorSelectionKind::Mm9EventScript:
        return "MM9 Script";

    default:
        return "Select";
    }
}

size_t flattenTerrainCellIndex(int cellX, int cellY)
{
    return static_cast<size_t>(cellY) * Game::OutdoorMapData::TerrainWidth + static_cast<size_t>(cellX);
}

bx::Vec3 applySymmetricMatrix(
    const std::array<float, 6> &covariance,
    const bx::Vec3 &vector)
{
    const float xx = covariance[0];
    const float xy = covariance[1];
    const float xz = covariance[2];
    const float yy = covariance[3];
    const float yz = covariance[4];
    const float zz = covariance[5];
    return {
        xx * vector.x + xy * vector.y + xz * vector.z,
        xy * vector.x + yy * vector.y + yz * vector.z,
        xz * vector.x + yz * vector.y + zz * vector.z};
}

bx::Vec3 powerIterationAxis(
    const std::array<float, 6> &covariance,
    bx::Vec3 vector,
    const std::optional<bx::Vec3> &orthogonalTo)
{
    for (int iteration = 0; iteration < 10; ++iteration)
    {
        vector = applySymmetricMatrix(covariance, vector);

        if (orthogonalTo)
        {
            vector = vecSubtract(vector, vecScale(*orthogonalTo, vecDot(vector, *orthogonalTo)));
        }

        if (vecLength(vector) <= 0.0001f)
        {
            break;
        }

        vector = vecNormalize(vector);
    }

    if (vecLength(vector) <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return vecNormalize(vector);
}

void computeBModelLocalBasis(
    const Game::OutdoorBModel &bmodel,
    bx::Vec3 &xAxis,
    bx::Vec3 &yAxis,
    bx::Vec3 &zAxis)
{
    if (bmodel.vertices.size() < 3)
    {
        xAxis = {1.0f, 0.0f, 0.0f};
        yAxis = {0.0f, 1.0f, 0.0f};
        zAxis = {0.0f, 0.0f, 1.0f};
        return;
    }

    bx::Vec3 center = {0.0f, 0.0f, 0.0f};

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        center.x += static_cast<float>(vertex.x);
        center.y += static_cast<float>(vertex.y);
        center.z += static_cast<float>(vertex.z);
    }

    const float invCount = 1.0f / static_cast<float>(bmodel.vertices.size());
    center.x *= invCount;
    center.y *= invCount;
    center.z *= invCount;

    std::array<float, 6> covariance = {};

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float x = static_cast<float>(vertex.x) - center.x;
        const float y = static_cast<float>(vertex.y) - center.y;
        const float z = static_cast<float>(vertex.z) - center.z;
        covariance[0] += x * x;
        covariance[1] += x * y;
        covariance[2] += x * z;
        covariance[3] += y * y;
        covariance[4] += y * z;
        covariance[5] += z * z;
    }

    xAxis = powerIterationAxis(covariance, {1.0f, 0.37f, 0.21f}, std::nullopt);

    if (vecLength(xAxis) <= 0.0001f)
    {
        xAxis = {1.0f, 0.0f, 0.0f};
    }

    yAxis = powerIterationAxis(covariance, {0.19f, 1.0f, 0.41f}, xAxis);

    if (vecLength(yAxis) <= 0.0001f)
    {
        yAxis = std::fabs(xAxis.z) > 0.8f ? bx::Vec3{1.0f, 0.0f, 0.0f} : bx::Vec3{0.0f, 0.0f, 1.0f};
        yAxis = vecNormalize(vecSubtract(yAxis, vecScale(xAxis, vecDot(yAxis, xAxis))));
    }

    zAxis = vecNormalize(vecCross(xAxis, yAxis));

    if (vecLength(zAxis) <= 0.0001f)
    {
        zAxis = {0.0f, 0.0f, 1.0f};
    }

    yAxis = vecNormalize(vecCross(zAxis, xAxis));

    if (vecDot(zAxis, bx::Vec3{0.0f, 0.0f, 1.0f}) < 0.0f)
    {
        zAxis = vecScale(zAxis, -1.0f);
        yAxis = vecScale(yAxis, -1.0f);
    }
}

void computeTransformBasis(
    const EditorDocument &document,
    const EditorSelection &selection,
    EditorOutdoorViewport::TransformSpaceMode spaceMode,
    bx::Vec3 &xAxis,
    bx::Vec3 &yAxis,
    bx::Vec3 &zAxis)
{
    xAxis = {1.0f, 0.0f, 0.0f};
    yAxis = {0.0f, 1.0f, 0.0f};
    zAxis = {0.0f, 0.0f, 1.0f};

    if (spaceMode != EditorOutdoorViewport::TransformSpaceMode::Local
        || selection.kind != EditorSelectionKind::BModel
        || selection.index >= document.outdoorGeometry().bmodels.size())
    {
        return;
    }

    computeBModelLocalBasis(document.outdoorGeometry().bmodels[selection.index], xAxis, yAxis, zAxis);
}

template<class Callback>
void rasterizeTerrainLine(int startX, int startY, int endX, int endY, Callback callback)
{
    int currentX = startX;
    int currentY = startY;
    const int deltaX = std::abs(endX - startX);
    const int deltaY = std::abs(endY - startY);
    const int stepX = startX < endX ? 1 : -1;
    const int stepY = startY < endY ? 1 : -1;
    int error = deltaX - deltaY;

    while (true)
    {
        callback(currentX, currentY);

        if (currentX == endX && currentY == endY)
        {
            break;
        }

        const int doubleError = error * 2;

        if (doubleError > -deltaY)
        {
            error -= deltaY;
            currentX += stepX;
        }

        if (doubleError < deltaX)
        {
            error += deltaX;
            currentY += stepY;
        }
    }
}

template<class Callback>
void forEachTerrainBrushCell(int centerX, int centerY, int radius, Callback callback)
{
    const int effectiveRadius = std::max(radius, 0);

    for (int offsetY = -effectiveRadius; offsetY <= effectiveRadius; ++offsetY)
    {
        for (int offsetX = -effectiveRadius; offsetX <= effectiveRadius; ++offsetX)
        {
            const int targetX = centerX + offsetX;
            const int targetY = centerY + offsetY;

            if (targetX < 0
                || targetY < 0
                || targetX >= Game::OutdoorMapData::TerrainWidth
                || targetY >= Game::OutdoorMapData::TerrainHeight)
            {
                continue;
            }

            const float distance = std::sqrt(static_cast<float>(offsetX * offsetX + offsetY * offsetY));

            if (distance > static_cast<float>(effectiveRadius))
            {
                continue;
            }

            callback(targetX, targetY, distance, effectiveRadius);
        }
    }
}

float terrainFalloffWeight(float distance, int radius, EditorTerrainFalloffMode mode)
{
    if (radius <= 0)
    {
        return 1.0f;
    }

    const float normalized = std::clamp(distance / static_cast<float>(radius + 1), 0.0f, 1.0f);

    switch (mode)
    {
    case EditorTerrainFalloffMode::Flat:
        return 1.0f;

    case EditorTerrainFalloffMode::Smooth:
    {
        const float inverse = 1.0f - normalized;
        return inverse * inverse;
    }

    case EditorTerrainFalloffMode::Linear:
    default:
        return 1.0f - normalized;
    }
}

bool applyTerrainPaintBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    uint8_t tileId,
    int edgeNoise)
{
    bool mutated = false;
    const int clampedEdgeNoise = std::clamp(edgeNoise, 0, 100);
    const float edgeNoiseStrength = static_cast<float>(clampedEdgeNoise) / 100.0f;
    const float effectiveRadius = static_cast<float>(std::max(radius, 0));
    const float edgeBandWidth = effectiveRadius > 1.0f ? std::max(1.0f, effectiveRadius * 0.4f) : 0.0f;
    const float solidRadius = std::max(0.0f, effectiveRadius - edgeBandWidth);

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.tileMap.size())
            {
                return;
            }

            if (clampedEdgeNoise > 0 && effectiveRadius > 1.0f && distance > solidRadius)
            {
                const float normalizedEdge = std::clamp((distance - solidRadius) / edgeBandWidth, 0.0f, 1.0f);
                const uint32_t hash = terrainNoiseHash(targetX, targetY);
                const float noise = static_cast<float>(hash & 0xffffu) / 65535.0f;
                const float jitter = (noise * 2.0f - 1.0f) * edgeNoiseStrength * 0.35f;
                const float coverage = 1.0f - normalizedEdge;

                if (coverage + jitter < 0.5f)
                {
                    return;
                }
            }

            if (outdoorGeometry.tileMap[sampleIndex] == tileId)
            {
                return;
            }

            outdoorGeometry.tileMap[sampleIndex] = tileId;
            mutated = true;
        });

    if (mutated)
    {
        recalculateOutdoorTileUsage(outdoorGeometry);
    }

    return mutated;
}

bool applyTerrainPaintRectangle(
    Game::OutdoorMapData &outdoorGeometry,
    int startX,
    int startY,
    int endX,
    int endY,
    uint8_t tileId)
{
    const int minX = std::clamp(std::min(startX, endX), 0, Game::OutdoorMapData::TerrainWidth - 1);
    const int maxX = std::clamp(std::max(startX, endX), 0, Game::OutdoorMapData::TerrainWidth - 1);
    const int minY = std::clamp(std::min(startY, endY), 0, Game::OutdoorMapData::TerrainHeight - 1);
    const int maxY = std::clamp(std::max(startY, endY), 0, Game::OutdoorMapData::TerrainHeight - 1);
    bool mutated = false;

    for (int y = minY; y <= maxY; ++y)
    {
        for (int x = minX; x <= maxX; ++x)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(x, y);

            if (sampleIndex >= outdoorGeometry.tileMap.size() || outdoorGeometry.tileMap[sampleIndex] == tileId)
            {
                continue;
            }

            outdoorGeometry.tileMap[sampleIndex] = tileId;
            mutated = true;
        }
    }

    if (mutated)
    {
        recalculateOutdoorTileUsage(outdoorGeometry);
    }

    return mutated;
}

bool applyTerrainPaintFill(Game::OutdoorMapData &outdoorGeometry, int startX, int startY, uint8_t tileId)
{
    if (startX < 0
        || startY < 0
        || startX >= Game::OutdoorMapData::TerrainWidth
        || startY >= Game::OutdoorMapData::TerrainHeight)
    {
        return false;
    }

    const size_t startIndex = flattenTerrainCellIndex(startX, startY);

    if (startIndex >= outdoorGeometry.tileMap.size())
    {
        return false;
    }

    const uint8_t sourceTileId = outdoorGeometry.tileMap[startIndex];

    if (sourceTileId == tileId)
    {
        return false;
    }

    std::vector<std::pair<int, int>> stack;
    stack.push_back({startX, startY});

    while (!stack.empty())
    {
        const std::pair<int, int> current = stack.back();
        stack.pop_back();
        const int x = current.first;
        const int y = current.second;

        if (x < 0
            || y < 0
            || x >= Game::OutdoorMapData::TerrainWidth
            || y >= Game::OutdoorMapData::TerrainHeight)
        {
            continue;
        }

        const size_t sampleIndex = flattenTerrainCellIndex(x, y);

        if (sampleIndex >= outdoorGeometry.tileMap.size() || outdoorGeometry.tileMap[sampleIndex] != sourceTileId)
        {
            continue;
        }

        outdoorGeometry.tileMap[sampleIndex] = tileId;
        stack.push_back({x - 1, y});
        stack.push_back({x + 1, y});
        stack.push_back({x, y - 1});
        stack.push_back({x, y + 1});
    }

    recalculateOutdoorTileUsage(outdoorGeometry);
    return true;
}

bool applyTerrainSculptBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    int signedStrength,
    EditorTerrainFalloffMode falloffMode)
{
    bool mutated = false;

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int effectiveRadius)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                return;
            }

            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            int delta = static_cast<int>(std::round(static_cast<float>(signedStrength) * falloff));

            if (delta == 0)
            {
                delta = signedStrength > 0 ? 1 : -1;
            }

            const int currentHeight = outdoorGeometry.heightMap[sampleIndex];
            const int nextHeight = std::clamp(currentHeight + delta, 0, 255);

            if (nextHeight == currentHeight)
            {
                return;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        });

    return mutated;
}

bool applyTerrainFlattenBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    int strength,
    int targetHeight,
    EditorTerrainFalloffMode falloffMode)
{
    bool mutated = false;

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int effectiveRadius)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                return;
            }

            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            int maxDelta = static_cast<int>(std::round(static_cast<float>(strength) * falloff));

            if (maxDelta <= 0)
            {
                maxDelta = 1;
            }

            const int currentHeight = outdoorGeometry.heightMap[sampleIndex];
            const int deltaToTarget = targetHeight - currentHeight;

            if (deltaToTarget == 0)
            {
                return;
            }

            const int delta = std::clamp(deltaToTarget, -maxDelta, maxDelta);
            const int nextHeight = std::clamp(currentHeight + delta, 0, 255);

            if (nextHeight == currentHeight)
            {
                return;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        });

    return mutated;
}

bool applyTerrainSmoothBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    int strength,
    EditorTerrainFalloffMode falloffMode)
{
    const std::vector<uint8_t> sourceHeights = outdoorGeometry.heightMap;
    bool mutated = false;
    const int kernelRadius = radius >= 6 ? 2 : 1;

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int effectiveRadius)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                return;
            }

            int totalHeight = 0;
            int sampleCount = 0;

            for (int offsetY = -kernelRadius; offsetY <= kernelRadius; ++offsetY)
            {
                for (int offsetX = -kernelRadius; offsetX <= kernelRadius; ++offsetX)
                {
                    const int sampleX = targetX + offsetX;
                    const int sampleY = targetY + offsetY;

                    if (sampleX < 0
                        || sampleY < 0
                        || sampleX >= Game::OutdoorMapData::TerrainWidth
                        || sampleY >= Game::OutdoorMapData::TerrainHeight)
                    {
                        continue;
                    }

                    totalHeight += sourceHeights[flattenTerrainCellIndex(sampleX, sampleY)];
                    ++sampleCount;
                }
            }

            if (sampleCount <= 0)
            {
                return;
            }

            const float averageHeight = static_cast<float>(totalHeight) / static_cast<float>(sampleCount);
            const int currentHeight = sourceHeights[sampleIndex];
            const float deltaToAverage = averageHeight - static_cast<float>(currentHeight);

            if (std::fabs(deltaToAverage) <= 0.001f)
            {
                return;
            }

            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            const float blend = std::clamp((static_cast<float>(strength) / 8.0f) * falloff, 0.0f, 1.0f);
            int nextHeight = static_cast<int>(std::lround(
                static_cast<float>(currentHeight) + deltaToAverage * blend));

            if (nextHeight == currentHeight)
            {
                nextHeight = currentHeight + (deltaToAverage > 0.0f ? 1 : -1);
            }

            nextHeight = std::clamp(nextHeight, 0, 255);

            if (nextHeight == currentHeight)
            {
                return;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        });

    return mutated;
}

bool applyTerrainNoiseBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int centerX,
    int centerY,
    int radius,
    int strength,
    EditorTerrainFalloffMode falloffMode)
{
    bool mutated = false;

    forEachTerrainBrushCell(
        centerX,
        centerY,
        radius,
        [&](int targetX, int targetY, float distance, int effectiveRadius)
        {
            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                return;
            }

            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            const uint32_t hash = terrainNoiseHash(targetX, targetY);
            const float noise = (static_cast<float>(hash & 1023u) / 511.5f) - 1.0f;
            int delta = static_cast<int>(std::lround(noise * static_cast<float>(strength) * 0.5f * falloff));

            if (delta == 0 && falloff > 0.0f && std::fabs(noise) > 0.25f)
            {
                delta = noise > 0.0f ? 1 : -1;
            }

            if (delta == 0)
            {
                return;
            }

            const int currentHeight = outdoorGeometry.heightMap[sampleIndex];
            const int nextHeight = std::clamp(currentHeight + delta, 0, 255);

            if (nextHeight == currentHeight)
            {
                return;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        });

    return mutated;
}

float distanceToTerrainSegment(
    float pointX,
    float pointY,
    float startX,
    float startY,
    float endX,
    float endY,
    float &t)
{
    const float deltaX = endX - startX;
    const float deltaY = endY - startY;
    const float lengthSquared = deltaX * deltaX + deltaY * deltaY;

    if (lengthSquared <= 0.0001f)
    {
        t = 0.0f;
        const float offsetX = pointX - startX;
        const float offsetY = pointY - startY;
        return std::sqrt(offsetX * offsetX + offsetY * offsetY);
    }

    t = std::clamp(((pointX - startX) * deltaX + (pointY - startY) * deltaY) / lengthSquared, 0.0f, 1.0f);
    const float nearestX = startX + deltaX * t;
    const float nearestY = startY + deltaY * t;
    const float offsetX = pointX - nearestX;
    const float offsetY = pointY - nearestY;
    return std::sqrt(offsetX * offsetX + offsetY * offsetY);
}

bool applyTerrainRampBrush(
    Game::OutdoorMapData &outdoorGeometry,
    int startX,
    int startY,
    int endX,
    int endY,
    int startHeight,
    int endHeight,
    int radius,
    int strength,
    EditorTerrainFalloffMode falloffMode)
{
    const int effectiveRadius = std::max(radius, 1);
    const int minX = std::clamp(std::min(startX, endX) - effectiveRadius, 0, Game::OutdoorMapData::TerrainWidth - 1);
    const int maxX = std::clamp(std::max(startX, endX) + effectiveRadius, 0, Game::OutdoorMapData::TerrainWidth - 1);
    const int minY = std::clamp(std::min(startY, endY) - effectiveRadius, 0, Game::OutdoorMapData::TerrainHeight - 1);
    const int maxY = std::clamp(std::max(startY, endY) + effectiveRadius, 0, Game::OutdoorMapData::TerrainHeight - 1);
    bool mutated = false;

    for (int targetY = minY; targetY <= maxY; ++targetY)
    {
        for (int targetX = minX; targetX <= maxX; ++targetX)
        {
            float lineT = 0.0f;
            const float distance = distanceToTerrainSegment(
                static_cast<float>(targetX),
                static_cast<float>(targetY),
                static_cast<float>(startX),
                static_cast<float>(startY),
                static_cast<float>(endX),
                static_cast<float>(endY),
                lineT);

            if (distance > static_cast<float>(effectiveRadius))
            {
                continue;
            }

            const size_t sampleIndex = flattenTerrainCellIndex(targetX, targetY);

            if (sampleIndex >= outdoorGeometry.heightMap.size())
            {
                continue;
            }

            const int targetHeight = static_cast<int>(std::lround(lerpFloat(
                static_cast<float>(startHeight),
                static_cast<float>(endHeight),
                lineT)));
            const float falloff = terrainFalloffWeight(distance, effectiveRadius, falloffMode);
            int maxDelta = static_cast<int>(std::round(static_cast<float>(strength) * falloff));

            if (maxDelta <= 0)
            {
                maxDelta = 1;
            }

            const int currentHeight = outdoorGeometry.heightMap[sampleIndex];
            const int deltaToTarget = targetHeight - currentHeight;

            if (deltaToTarget == 0)
            {
                continue;
            }

            const int delta = std::clamp(deltaToTarget, -maxDelta, maxDelta);
            const int nextHeight = std::clamp(currentHeight + delta, 0, 255);

            if (nextHeight == currentHeight)
            {
                continue;
            }

            outdoorGeometry.heightMap[sampleIndex] = static_cast<uint8_t>(nextHeight);
            mutated = true;
        }
    }

    return mutated;
}

size_t flattenedOutdoorFaceIndex(const Game::OutdoorMapData &outdoorMapData, size_t bmodelIndex, size_t faceIndex)
{
    size_t flattenedIndex = 0;

    for (size_t index = 0; index < bmodelIndex && index < outdoorMapData.bmodels.size(); ++index)
    {
        flattenedIndex += outdoorMapData.bmodels[index].faces.size();
    }

    return flattenedIndex + faceIndex;
}

float distancePointToSegmentSquared(
    float pointX,
    float pointY,
    float startX,
    float startY,
    float endX,
    float endY)
{
    const float deltaX = endX - startX;
    const float deltaY = endY - startY;
    const float lengthSquared = squaredLength2(deltaX, deltaY);

    if (lengthSquared <= 0.0001f)
    {
        return squaredLength2(pointX - startX, pointY - startY);
    }

    const float t = std::clamp(
        ((pointX - startX) * deltaX + (pointY - startY) * deltaY) / lengthSquared,
        0.0f,
        1.0f);
    const float closestX = startX + deltaX * t;
    const float closestY = startY + deltaY * t;
    return squaredLength2(pointX - closestX, pointY - closestY);
}

struct ScreenPoint
{
    float x = 0.0f;
    float y = 0.0f;
};

bool isPointInsideScreenPolygon(float x, float y, const std::vector<ScreenPoint> &vertices)
{
    if (vertices.size() < 3)
    {
        return false;
    }

    bool isInside = false;
    size_t previousIndex = vertices.size() - 1;

    for (size_t currentIndex = 0; currentIndex < vertices.size(); ++currentIndex)
    {
        const ScreenPoint &currentVertex = vertices[currentIndex];
        const ScreenPoint &previousVertex = vertices[previousIndex];
        const bool intersects =
            ((currentVertex.y > y) != (previousVertex.y > y))
            && (x < (previousVertex.x - currentVertex.x) * (y - currentVertex.y)
                    / ((previousVertex.y - currentVertex.y) + 0.0001f)
                + currentVertex.x);

        if (intersects)
        {
            isInside = !isInside;
        }

        previousIndex = currentIndex;
    }

    return isInside;
}

bool isPointInsideOrNearScreenPolygon(float x, float y, const std::vector<ScreenPoint> &vertices, float slackPixels)
{
    if (isPointInsideScreenPolygon(x, y, vertices))
    {
        return true;
    }

    const float slackSquared = slackPixels * slackPixels;

    for (size_t index = 0; index < vertices.size(); ++index)
    {
        const size_t nextIndex = (index + 1) % vertices.size();

        if (distancePointToSegmentSquared(
                x,
                y,
                vertices[index].x,
                vertices[index].y,
                vertices[nextIndex].x,
                vertices[nextIndex].y) <= slackSquared)
        {
            return true;
        }
    }

    return false;
}

bx::Vec3 worldPointFromTerrainGrid(int gridX, int gridY, uint8_t heightSample)
{
    return {
        Game::outdoorGridCornerWorldX(gridX),
        Game::outdoorGridCornerWorldY(gridY),
        static_cast<float>(heightSample * Game::OutdoorMapData::TerrainHeightScale)
    };
}

bx::Vec3 worldPointFromLegacyPosition(int x, int y, int z)
{
    return {
        static_cast<float>(x),
        static_cast<float>(y),
        static_cast<float>(z)
    };
}

bool projectWorldPoint(
    const bx::Vec3 &worldPoint,
    const float *pViewProjectionMatrix,
    uint16_t viewportWidth,
    uint16_t viewportHeight,
    float &screenX,
    float &screenY,
    float &clipW)
{
    clipW =
        worldPoint.x * pViewProjectionMatrix[3]
        + worldPoint.y * pViewProjectionMatrix[7]
        + worldPoint.z * pViewProjectionMatrix[11]
        + pViewProjectionMatrix[15];

    if (clipW <= 0.0001f)
    {
        return false;
    }

    const float clipX =
        worldPoint.x * pViewProjectionMatrix[0]
        + worldPoint.y * pViewProjectionMatrix[4]
        + worldPoint.z * pViewProjectionMatrix[8]
        + pViewProjectionMatrix[12];
    const float clipY =
        worldPoint.x * pViewProjectionMatrix[1]
        + worldPoint.y * pViewProjectionMatrix[5]
        + worldPoint.z * pViewProjectionMatrix[9]
        + pViewProjectionMatrix[13];
    const float inverseW = 1.0f / clipW;
    const float ndcX = clipX * inverseW;
    const float ndcY = clipY * inverseW;

    if (ndcX < -1.25f || ndcX > 1.25f || ndcY < -1.25f || ndcY > 1.25f)
    {
        return false;
    }

    screenX = ((ndcX + 1.0f) * 0.5f) * static_cast<float>(viewportWidth);
    screenY = ((1.0f - ndcY) * 0.5f) * static_cast<float>(viewportHeight);
    return true;
}

bx::Vec3 safeTriangleNormal(
    const bx::Vec3 &first,
    const bx::Vec3 &second,
    const bx::Vec3 &third,
    const bx::Vec3 &fallback)
{
    const bx::Vec3 edgeA = vecSubtract(second, first);
    const bx::Vec3 edgeB = vecSubtract(third, first);
    const bx::Vec3 normal = vecCross(edgeA, edgeB);
    const float normalLength = vecLength(normal);

    if (normalLength <= 0.0001f)
    {
        return fallback;
    }

    return vecScale(normal, 1.0f / normalLength);
}

std::array<float, 2> proceduralPreviewUv(const bx::Vec3 &localPosition, const bx::Vec3 &normal)
{
    const float absX = std::abs(normal.x);
    const float absY = std::abs(normal.y);
    const float absZ = std::abs(normal.z);

    if (absZ >= absX && absZ >= absY)
    {
        return {localPosition.x, localPosition.y};
    }

    if (absX >= absY)
    {
        return {localPosition.y, localPosition.z};
    }

    return {localPosition.x, localPosition.z};
}

void appendProceduralTriangle(
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> &vertices,
    const bx::Vec3 &first,
    const bx::Vec3 &second,
    const bx::Vec3 &third,
    const bx::Vec3 &origin,
    const bx::Vec3 &fallbackNormal)
{
    const bx::Vec3 normal = safeTriangleNormal(first, second, third, fallbackNormal);
    const std::array<float, 2> uv0 = proceduralPreviewUv(vecSubtract(first, origin), normal);
    const std::array<float, 2> uv1 = proceduralPreviewUv(vecSubtract(second, origin), normal);
    const std::array<float, 2> uv2 = proceduralPreviewUv(vecSubtract(third, origin), normal);

    vertices.push_back({first.x, first.y, first.z, uv0[0], uv0[1], normal.x, normal.y, normal.z, 0.0f});
    vertices.push_back({second.x, second.y, second.z, uv1[0], uv1[1], normal.x, normal.y, normal.z, 0.0f});
    vertices.push_back({third.x, third.y, third.z, uv2[0], uv2[1], normal.x, normal.y, normal.z, 0.0f});
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildTerrainVertices(
    const Game::OutdoorMapData &outdoorMapData)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(Game::OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(Game::OutdoorMapData::TerrainHeight - 1)
        * 6);
    const bx::Vec3 terrainOrigin = {
        Game::outdoorGridCornerWorldX(0),
        Game::outdoorGridCornerWorldY(0),
        0.0f
    };
    const bx::Vec3 fallbackNormal = {0.0f, 0.0f, 1.0f};

    for (int gridY = 0; gridY < (Game::OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (Game::OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t topLeftIndex =
                static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex =
                static_cast<size_t>((gridY + 1) * Game::OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const bx::Vec3 topLeft = worldPointFromTerrainGrid(gridX, gridY, outdoorMapData.heightMap[topLeftIndex]);
            const bx::Vec3 topRight = worldPointFromTerrainGrid(gridX + 1, gridY, outdoorMapData.heightMap[topRightIndex]);
            const bx::Vec3 bottomLeft =
                worldPointFromTerrainGrid(gridX, gridY + 1, outdoorMapData.heightMap[bottomLeftIndex]);
            const bx::Vec3 bottomRight =
                worldPointFromTerrainGrid(gridX + 1, gridY + 1, outdoorMapData.heightMap[bottomRightIndex]);

            appendProceduralTriangle(vertices, topLeft, bottomLeft, topRight, terrainOrigin, fallbackNormal);
            appendProceduralTriangle(vertices, topRight, bottomLeft, bottomRight, terrainOrigin, fallbackNormal);
        }
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildTerrainErrorVertices(
    const Game::OutdoorMapData &outdoorMapData,
    const TerrainAtlasData &atlasData)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;
    const bx::Vec3 terrainOrigin = {
        Game::outdoorGridCornerWorldX(0),
        Game::outdoorGridCornerWorldY(0),
        0.0f
    };
    const bx::Vec3 fallbackNormal = {0.0f, 0.0f, 1.0f};

    for (int gridY = 0; gridY < (Game::OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (Game::OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex = static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const TerrainAtlasRegion &region = atlasData.tileRegions[static_cast<size_t>(rawTileId)];

            if (!region.hasMissingAsset)
            {
                continue;
            }

            const size_t topLeftIndex = tileMapIndex;
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * Game::OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const bx::Vec3 topLeft = worldPointFromTerrainGrid(gridX, gridY, outdoorMapData.heightMap[topLeftIndex]);
            const bx::Vec3 topRight = worldPointFromTerrainGrid(gridX + 1, gridY, outdoorMapData.heightMap[topRightIndex]);
            const bx::Vec3 bottomLeft =
                worldPointFromTerrainGrid(gridX, gridY + 1, outdoorMapData.heightMap[bottomLeftIndex]);
            const bx::Vec3 bottomRight =
                worldPointFromTerrainGrid(gridX + 1, gridY + 1, outdoorMapData.heightMap[bottomRightIndex]);

            appendProceduralTriangle(vertices, topLeft, bottomLeft, topRight, terrainOrigin, fallbackNormal);
            appendProceduralTriangle(vertices, topRight, bottomLeft, bottomRight, terrainOrigin, fallbackNormal);
        }
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::TexturedPreviewVertex> buildTexturedTerrainVertices(
    const Game::OutdoorMapData &outdoorMapData,
    const TerrainAtlasData &atlasData)
{
    std::vector<EditorOutdoorViewport::TexturedPreviewVertex> vertices;
    vertices.reserve(
        static_cast<size_t>(Game::OutdoorMapData::TerrainWidth - 1)
        * static_cast<size_t>(Game::OutdoorMapData::TerrainHeight - 1)
        * 6);

    for (int gridY = 0; gridY < (Game::OutdoorMapData::TerrainHeight - 1); ++gridY)
    {
        for (int gridX = 0; gridX < (Game::OutdoorMapData::TerrainWidth - 1); ++gridX)
        {
            const size_t tileMapIndex = static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
            const uint8_t rawTileId = outdoorMapData.tileMap[tileMapIndex];
            const TerrainAtlasRegion &region = atlasData.tileRegions[static_cast<size_t>(rawTileId)];

            if (!region.isValid)
            {
                continue;
            }

            const size_t topLeftIndex = tileMapIndex;
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex = static_cast<size_t>((gridY + 1) * Game::OutdoorMapData::TerrainWidth + gridX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;

            const bx::Vec3 topLeft = worldPointFromTerrainGrid(gridX, gridY, outdoorMapData.heightMap[topLeftIndex]);
            const bx::Vec3 topRight = worldPointFromTerrainGrid(gridX + 1, gridY, outdoorMapData.heightMap[topRightIndex]);
            const bx::Vec3 bottomLeft =
                worldPointFromTerrainGrid(gridX, gridY + 1, outdoorMapData.heightMap[bottomLeftIndex]);
            const bx::Vec3 bottomRight =
                worldPointFromTerrainGrid(gridX + 1, gridY + 1, outdoorMapData.heightMap[bottomRightIndex]);

            vertices.push_back({topLeft.x, topLeft.y, topLeft.z, region.u0, region.v0});
            vertices.push_back({bottomLeft.x, bottomLeft.y, bottomLeft.z, region.u0, region.v1});
            vertices.push_back({topRight.x, topRight.y, topRight.z, region.u1, region.v0});
            vertices.push_back({topRight.x, topRight.y, topRight.z, region.u1, region.v0});
            vertices.push_back({bottomLeft.x, bottomLeft.y, bottomLeft.z, region.u0, region.v1});
            vertices.push_back({bottomRight.x, bottomRight.y, bottomRight.z, region.u1, region.v1});
        }
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::PreviewVertex> buildBModelWireVertices(const Game::OutdoorMapData &outdoorMapData)
{
    std::vector<EditorOutdoorViewport::PreviewVertex> vertices;
    const uint32_t color = makeAbgr(255, 190, 96);

    for (const Game::OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const Game::OutdoorBModelFace &face : bmodel.faces)
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

                const bx::Vec3 start =
                    worldPointFromLegacyPosition(
                        bmodel.vertices[startIndex].x,
                        bmodel.vertices[startIndex].y,
                        bmodel.vertices[startIndex].z);
                const bx::Vec3 end =
                    worldPointFromLegacyPosition(
                        bmodel.vertices[endIndex].x,
                        bmodel.vertices[endIndex].y,
                        bmodel.vertices[endIndex].z);
                vertices.push_back({start.x, start.y, start.z, color});
                vertices.push_back({end.x, end.y, end.z, color});
            }
        }
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::TexturedPreviewVertex> buildTexturedBModelFaceVertices(
    const Game::OutdoorMapData &outdoorMapData,
    size_t bmodelIndex,
    size_t faceIndex,
    int textureWidth,
    int textureHeight)
{
    std::vector<EditorOutdoorViewport::TexturedPreviewVertex> vertices;

    if (textureWidth <= 0
        || textureHeight <= 0
        || bmodelIndex >= outdoorMapData.bmodels.size()
        || faceIndex >= outdoorMapData.bmodels[bmodelIndex].faces.size())
    {
        return vertices;
    }

    const Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];
    const Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];

    if (face.vertexIndices.size() < 3 || face.textureName.empty())
    {
        return vertices;
    }

    for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
    {
        const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
        EditorOutdoorViewport::TexturedPreviewVertex triangleVertices[3] = {};
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

            const bx::Vec3 worldVertex = Game::outdoorBModelVertexToWorld(bmodel.vertices[modelVertexIndex]);
            const float normalizedU =
                static_cast<float>(face.textureUs[localTriangleVertexIndex] + face.textureDeltaU)
                / static_cast<float>(textureWidth);
            const float normalizedV =
                static_cast<float>(face.textureVs[localTriangleVertexIndex] + face.textureDeltaV)
                / static_cast<float>(textureHeight);
            triangleVertices[triangleVertexSlot] =
                {worldVertex.x, worldVertex.y, worldVertex.z, normalizedU, normalizedV};
        }

        if (!isTriangleValid)
        {
            continue;
        }

        vertices.push_back(triangleVertices[0]);
        vertices.push_back(triangleVertices[1]);
        vertices.push_back(triangleVertices[2]);
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildProceduralBModelFaceVertices(
    const Game::OutdoorBModel &bmodel,
    size_t faceIndex,
    const bx::Vec3 &origin)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;

    if (faceIndex >= bmodel.faces.size())
    {
        return vertices;
    }

    const Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];

    if (face.vertexIndices.size() < 3)
    {
        return vertices;
    }

    const bx::Vec3 fallbackNormal = {0.0f, 0.0f, 1.0f};

    for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
    {
        const size_t localIndices[3] = {0, triangleIndex, triangleIndex + 1};
        bx::Vec3 triangleVertices[3] = {
            {0.0f, 0.0f, 0.0f},
            {0.0f, 0.0f, 0.0f},
            {0.0f, 0.0f, 0.0f}
        };
        bool isTriangleValid = true;

        for (size_t vertexSlot = 0; vertexSlot < 3; ++vertexSlot)
        {
            const uint16_t modelVertexIndex = face.vertexIndices[localIndices[vertexSlot]];

            if (modelVertexIndex >= bmodel.vertices.size())
            {
                isTriangleValid = false;
                break;
            }

            triangleVertices[vertexSlot] = Game::outdoorBModelVertexToWorld(bmodel.vertices[modelVertexIndex]);
        }

        if (!isTriangleValid)
        {
            continue;
        }

        appendProceduralTriangle(
            vertices,
            triangleVertices[0],
            triangleVertices[1],
            triangleVertices[2],
            origin,
            fallbackNormal);
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildProceduralBModelFaceVertices(
    const Game::OutdoorMapData &outdoorMapData,
    size_t bmodelIndex,
    size_t faceIndex,
    const bx::Vec3 &origin)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;

    if (bmodelIndex >= outdoorMapData.bmodels.size() || faceIndex >= outdoorMapData.bmodels[bmodelIndex].faces.size())
    {
        return vertices;
    }

    return buildProceduralBModelFaceVertices(outdoorMapData.bmodels[bmodelIndex], faceIndex, origin);
}

bx::Vec3 rotateByQuaternion(const bx::Vec3 &value, const std::array<float, 4> &quaternion)
{
    const bx::Vec3 q = {quaternion[0], quaternion[1], quaternion[2]};
    const float w = quaternion[3];
    const bx::Vec3 t = vecScale(vecCross(q, value), 2.0f);
    return vecAdd(vecAdd(value, vecScale(t, w)), vecCross(q, t));
}

bx::Vec3 transformModelInstancePosition(
    const ImportedModelPosition &position,
    const Game::OutdoorSceneModelInstance &modelInstance)
{
    bx::Vec3 local = {
        position.x * modelInstance.scale[0],
        position.z * modelInstance.scale[1],
        position.y * modelInstance.scale[2]
    };
    local = rotateByQuaternion(local, modelInstance.rotationQuat);
    return {
        local.x + static_cast<float>(modelInstance.x),
        local.y + static_cast<float>(modelInstance.y),
        local.z + static_cast<float>(modelInstance.z)
    };
}

bx::Vec3 modelInstanceSelectionCenter(const Game::OutdoorSceneModelInstance &modelInstance)
{
    const float radius = 128.0f
        * std::max({modelInstance.scale[0], modelInstance.scale[1], modelInstance.scale[2], 1.0f});
    return {
        static_cast<float>(modelInstance.x),
        static_cast<float>(modelInstance.y),
        static_cast<float>(modelInstance.z) + radius
    };
}

void appendModelInstancePlaceholder(
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> &vertices,
    const Game::OutdoorSceneModelInstance &modelInstance)
{
    const float radius = 128.0f
        * std::max({modelInstance.scale[0], modelInstance.scale[1], modelInstance.scale[2], 1.0f});
    const bx::Vec3 center = {
        static_cast<float>(modelInstance.x),
        static_cast<float>(modelInstance.y),
        static_cast<float>(modelInstance.z) + radius
    };
    const bx::Vec3 origin = center;
    const std::array<bx::Vec3, 8> corners = {
        bx::Vec3{center.x - radius, center.y - radius, center.z - radius},
        bx::Vec3{center.x + radius, center.y - radius, center.z - radius},
        bx::Vec3{center.x + radius, center.y + radius, center.z - radius},
        bx::Vec3{center.x - radius, center.y + radius, center.z - radius},
        bx::Vec3{center.x - radius, center.y - radius, center.z + radius},
        bx::Vec3{center.x + radius, center.y - radius, center.z + radius},
        bx::Vec3{center.x + radius, center.y + radius, center.z + radius},
        bx::Vec3{center.x - radius, center.y + radius, center.z + radius},
    };
    const int faces[12][3] = {
        {0, 2, 1}, {0, 3, 2},
        {4, 5, 6}, {4, 6, 7},
        {0, 1, 5}, {0, 5, 4},
        {1, 2, 6}, {1, 6, 5},
        {2, 3, 7}, {2, 7, 6},
        {3, 0, 4}, {3, 4, 7},
    };

    for (const int *pFace : faces)
    {
        appendProceduralTriangle(
            vertices,
            corners[static_cast<size_t>(pFace[0])],
            corners[static_cast<size_t>(pFace[1])],
            corners[static_cast<size_t>(pFace[2])],
            origin,
            {0.0f, 0.0f, 1.0f});
    }
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildModelInstanceVertices(
    const std::vector<ImportedModel> &models,
    const Game::OutdoorSceneModelInstance &modelInstance)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;
    const bx::Vec3 origin = {
        static_cast<float>(modelInstance.x),
        static_cast<float>(modelInstance.y),
        static_cast<float>(modelInstance.z)
    };

    for (const ImportedModel &model : models)
    {
        for (const ImportedModelFace &face : model.faces)
        {
            if (face.vertices.size() < 3)
            {
                continue;
            }

            for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertices.size(); ++triangleIndex)
            {
                const size_t localIndices[3] = {0, triangleIndex, triangleIndex + 1};
                bx::Vec3 triangleVertices[3] = {
                    {0.0f, 0.0f, 0.0f},
                    {0.0f, 0.0f, 0.0f},
                    {0.0f, 0.0f, 0.0f}
                };
                bool validTriangle = true;

                for (size_t vertexSlot = 0; vertexSlot < 3; ++vertexSlot)
                {
                    const size_t positionIndex = face.vertices[localIndices[vertexSlot]].positionIndex;

                    if (positionIndex >= model.positions.size())
                    {
                        validTriangle = false;
                        break;
                    }

                    triangleVertices[vertexSlot] =
                        transformModelInstancePosition(model.positions[positionIndex], modelInstance);
                }

                if (!validTriangle)
                {
                    continue;
                }

                appendProceduralTriangle(
                    vertices,
                    triangleVertices[0],
                    triangleVertices[1],
                    triangleVertices[2],
                    origin,
                    {0.0f, 0.0f, 1.0f});
            }
        }
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::TexturedPreviewVertex> buildTexturedModelInstanceVertices(
    const std::vector<ImportedModel> &models,
    const Game::OutdoorSceneModelInstance &modelInstance,
    const std::string &materialName)
{
    std::vector<EditorOutdoorViewport::TexturedPreviewVertex> vertices;

    for (const ImportedModel &model : models)
    {
        for (const ImportedModelFace &face : model.faces)
        {
            if (face.vertices.size() < 3 || face.materialName != materialName)
            {
                continue;
            }

            for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertices.size(); ++triangleIndex)
            {
                const size_t localIndices[3] = {0, triangleIndex, triangleIndex + 1};
                EditorOutdoorViewport::TexturedPreviewVertex triangleVertices[3] = {};
                bool validTriangle = true;

                for (size_t vertexSlot = 0; vertexSlot < 3; ++vertexSlot)
                {
                    const ImportedModelFaceVertex &faceVertex = face.vertices[localIndices[vertexSlot]];

                    if (faceVertex.positionIndex >= model.positions.size() || !faceVertex.hasUv)
                    {
                        validTriangle = false;
                        break;
                    }

                    const bx::Vec3 position =
                        transformModelInstancePosition(model.positions[faceVertex.positionIndex], modelInstance);
                    triangleVertices[vertexSlot] =
                        {position.x, position.y, position.z, faceVertex.u, faceVertex.v};
                }

                if (!validTriangle)
                {
                    continue;
                }

                vertices.push_back(triangleVertices[0]);
                vertices.push_back(triangleVertices[1]);
                vertices.push_back(triangleVertices[2]);
            }
        }
    }

    return vertices;
}

std::vector<uint8_t> makeMissingModelTexturePixels(int width, int height)
{
    std::vector<uint8_t> pixels;
    pixels.reserve(static_cast<size_t>(width * height * 4));

    for (int y = 0; y < height; ++y)
    {
        for (int x = 0; x < width; ++x)
        {
            const bool bright = ((x / 8) + (y / 8)) % 2 == 0;
            pixels.push_back(bright ? 224 : 48);
            pixels.push_back(bright ? 64 : 0);
            pixels.push_back(bright ? 224 : 48);
            pixels.push_back(255);
        }
    }

    return pixels;
}

std::vector<uint8_t> makeUntexturedModelTexturePixels(int width, int height)
{
    std::vector<uint8_t> pixels;
    pixels.reserve(static_cast<size_t>(width * height * 4));

    const int pixelCount = width * height;
    for (int pixelIndex = 0; pixelIndex < pixelCount; ++pixelIndex)
    {
        pixels.push_back(178);
        pixels.push_back(176);
        pixels.push_back(168);
        pixels.push_back(255);
    }

    return pixels;
}

bool calculateIndoorEditorFaceTextureAxes(
    const Game::IndoorFace &face,
    const bx::Vec3 &normal,
    bx::Vec3 &axisU,
    bx::Vec3 &axisV)
{
    if (face.facetType == 1)
    {
        axisU = {-normal.y, normal.x, 0.0f};
        axisV = {0.0f, 0.0f, -1.0f};
    }
    else if (face.facetType == 3 || face.facetType == 5)
    {
        axisU = {1.0f, 0.0f, 0.0f};
        axisV = {0.0f, -1.0f, 0.0f};
    }
    else if (face.facetType == 4 || face.facetType == 6)
    {
        if (std::abs(normal.z) < 0.70863342285f)
        {
            axisU = vecNormalize({-normal.y, normal.x, 0.0f});
            axisV = {0.0f, 0.0f, -1.0f};
        }
        else
        {
            axisU = {1.0f, 0.0f, 0.0f};
            axisV = {0.0f, -1.0f, 0.0f};
        }
    }
    else
    {
        return false;
    }

    if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::FlipNormalU))
    {
        axisU = {-axisU.x, -axisU.y, -axisU.z};
    }

    if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::FlipNormalV))
    {
        axisV = {-axisV.x, -axisV.y, -axisV.z};
    }

    return true;
}

float indoorEditorMechanismDistanceForState(
    const Game::MapDeltaDoor &door,
    uint16_t state,
    float timeSinceTriggeredMs)
{
    if (state == static_cast<uint16_t>(Game::EvtMechanismState::Open))
    {
        return 0.0f;
    }

    if (state == static_cast<uint16_t>(Game::EvtMechanismState::Closing))
    {
        const float closingDistance = timeSinceTriggeredMs * static_cast<float>(door.closeSpeed) / 1000.0f;
        return std::min(closingDistance, static_cast<float>(door.moveLength));
    }

    if (state == static_cast<uint16_t>(Game::EvtMechanismState::Opening))
    {
        const float openingDistance = timeSinceTriggeredMs * static_cast<float>(door.openSpeed) / 1000.0f;
        return std::max(0.0f, static_cast<float>(door.moveLength) - openingDistance);
    }

    if (state == static_cast<uint16_t>(Game::EvtMechanismState::Closed) || (door.attributes & 0x2) != 0)
    {
        return static_cast<float>(door.moveLength);
    }

    return 0.0f;
}

float resolveIndoorEditorMechanismDistance(
    const Game::MapDeltaDoor &baseDoor,
    const Game::EventRuntimeState *pEventRuntimeState)
{
    Game::MapDeltaDoor door = baseDoor;
    Game::RuntimeMechanismState runtimeMechanism = {};
    runtimeMechanism.state = door.state;
    runtimeMechanism.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
    runtimeMechanism.currentDistance =
        indoorEditorMechanismDistanceForState(door, runtimeMechanism.state, runtimeMechanism.timeSinceTriggeredMs);
    runtimeMechanism.isMoving =
        door.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening)
        || door.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing);

    if (pEventRuntimeState == nullptr)
    {
        return runtimeMechanism.currentDistance;
    }

    const std::unordered_map<uint32_t, Game::RuntimeMechanismState>::const_iterator mechanismIterator =
        pEventRuntimeState->mechanisms.find(door.doorId);

    if (mechanismIterator == pEventRuntimeState->mechanisms.end())
    {
        return runtimeMechanism.currentDistance;
    }

    return mechanismIterator->second.currentDistance;
}

std::optional<IndoorEditorMechanismTextureState> findIndoorEditorMechanismTextureState(
    size_t faceIndex,
    const Game::MapDeltaData *pIndoorMapDeltaData,
    const Game::EventRuntimeState *pEventRuntimeState)
{
    if (pIndoorMapDeltaData == nullptr)
    {
        return std::nullopt;
    }

    for (const Game::MapDeltaDoor &door : pIndoorMapDeltaData->doors)
    {
        for (size_t doorFaceIndex = 0; doorFaceIndex < door.faceIds.size(); ++doorFaceIndex)
        {
            if (door.faceIds[doorFaceIndex] != faceIndex)
            {
                continue;
            }

            IndoorEditorMechanismTextureState state = {};
            state.pDoor = &door;
            state.faceOffset = doorFaceIndex;
            state.distance = resolveIndoorEditorMechanismDistance(door, pEventRuntimeState);
            state.direction = {
                static_cast<float>(door.directionX) / 65536.0f,
                static_cast<float>(door.directionY) / 65536.0f,
                static_cast<float>(door.directionZ) / 65536.0f
            };
            return state;
        }
    }

    return std::nullopt;
}

std::vector<EditorOutdoorViewport::TexturedPreviewVertex> buildTexturedIndoorFaceVertices(
    const Game::IndoorMapData &indoorMapData,
    const std::vector<Game::IndoorVertex> &indoorVertices,
    size_t faceIndex,
    int textureWidth,
    int textureHeight,
    const Game::MapDeltaData *pIndoorMapDeltaData,
    const Game::EventRuntimeState *pEventRuntimeState)
{
    std::vector<EditorOutdoorViewport::TexturedPreviewVertex> vertices;

    if (textureWidth <= 0 || textureHeight <= 0 || faceIndex >= indoorMapData.faces.size())
    {
        return vertices;
    }

    const Game::IndoorFace &face = indoorMapData.faces[faceIndex];

    if (face.vertexIndices.size() < 3 || face.textureName.empty())
    {
        return vertices;
    }

    const std::optional<IndoorEditorMechanismTextureState> mechanismTextureState =
        findIndoorEditorMechanismTextureState(faceIndex, pIndoorMapDeltaData, pEventRuntimeState);
    const bool useGeometryTextureCoordinates = mechanismTextureState.has_value();
    std::vector<float> geometryUs;
    std::vector<float> geometryVs;
    float geometryDeltaU = 0.0f;
    float geometryDeltaV = 0.0f;

    if (useGeometryTextureCoordinates)
    {
        Game::IndoorFaceGeometryData geometry = {};

        if (!Game::buildIndoorFaceGeometry(indoorMapData, indoorVertices, faceIndex, geometry)
            || vecDot(geometry.normal, geometry.normal) <= 0.0001f)
        {
            return vertices;
        }

        bx::Vec3 axisU = {0.0f, 0.0f, 0.0f};
        bx::Vec3 axisV = {0.0f, 0.0f, 0.0f};

        if (!calculateIndoorEditorFaceTextureAxes(face, vecNormalize(geometry.normal), axisU, axisV))
        {
            return vertices;
        }

        geometryUs.reserve(face.vertexIndices.size());
        geometryVs.reserve(face.vertexIndices.size());
        float minU = std::numeric_limits<float>::infinity();
        float minV = std::numeric_limits<float>::infinity();
        float maxU = -std::numeric_limits<float>::infinity();
        float maxV = -std::numeric_limits<float>::infinity();

        for (uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= indoorVertices.size())
            {
                return vertices;
            }

            const Game::IndoorVertex &vertex = indoorVertices[vertexIndex];
            const bx::Vec3 point = {
                static_cast<float>(vertex.x),
                static_cast<float>(vertex.y),
                static_cast<float>(vertex.z)
            };
            const float pointU = vecDot(point, axisU);
            const float pointV = vecDot(point, axisV);
            geometryUs.push_back(pointU);
            geometryVs.push_back(pointV);
            minU = std::min(minU, pointU);
            minV = std::min(minV, pointV);
            maxU = std::max(maxU, pointU);
            maxV = std::max(maxV, pointV);
        }

        if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::TextureAlignLeft))
        {
            geometryDeltaU -= minU;
        }
        else if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::TextureAlignRight))
        {
            geometryDeltaU -= maxU + static_cast<float>(textureWidth);
        }

        if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::TextureAlignDown))
        {
            geometryDeltaV -= minV;
        }
        else if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::TextureAlignBottom))
        {
            geometryDeltaV -= maxV + static_cast<float>(textureHeight);
        }

        if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::TextureMoveByDoor))
        {
            geometryDeltaU = -vecDot(mechanismTextureState->direction, axisU) * mechanismTextureState->distance;
            geometryDeltaV = -vecDot(mechanismTextureState->direction, axisV) * mechanismTextureState->distance;

            if (mechanismTextureState->pDoor != nullptr)
            {
                if (mechanismTextureState->faceOffset < mechanismTextureState->pDoor->deltaUs.size())
                {
                    geometryDeltaU +=
                        static_cast<float>(mechanismTextureState->pDoor->deltaUs[mechanismTextureState->faceOffset]);
                }

                if (mechanismTextureState->faceOffset < mechanismTextureState->pDoor->deltaVs.size())
                {
                    geometryDeltaV +=
                        static_cast<float>(mechanismTextureState->pDoor->deltaVs[mechanismTextureState->faceOffset]);
                }
            }
        }
    }

    for (size_t triangleIndex = 1; triangleIndex + 1 < face.vertexIndices.size(); ++triangleIndex)
    {
        const size_t triangleVertexIndices[3] = {0, triangleIndex, triangleIndex + 1};
        EditorOutdoorViewport::TexturedPreviewVertex triangleVertices[3] = {};
        bool isTriangleValid = true;

        for (size_t triangleVertexSlot = 0; triangleVertexSlot < 3; ++triangleVertexSlot)
        {
            const size_t localTriangleVertexIndex = triangleVertexIndices[triangleVertexSlot];
            const uint16_t modelVertexIndex = face.vertexIndices[localTriangleVertexIndex];

            if (modelVertexIndex >= indoorVertices.size()
                || localTriangleVertexIndex >= face.textureUs.size()
                || localTriangleVertexIndex >= face.textureVs.size())
            {
                isTriangleValid = false;
                break;
            }

            const bx::Vec3 worldVertex = Game::indoorVertexToWorld(indoorVertices[modelVertexIndex]);
            float normalizedU = 0.0f;
            float normalizedV = 0.0f;

            if (useGeometryTextureCoordinates
                && localTriangleVertexIndex < geometryUs.size()
                && localTriangleVertexIndex < geometryVs.size())
            {
                normalizedU =
                    (geometryUs[localTriangleVertexIndex] + geometryDeltaU) / static_cast<float>(textureWidth);
                normalizedV =
                    (geometryVs[localTriangleVertexIndex] + geometryDeltaV) / static_cast<float>(textureHeight);
            }
            else
            {
                normalizedU =
                    static_cast<float>(face.textureUs[localTriangleVertexIndex] + face.textureDeltaU)
                    / static_cast<float>(textureWidth);
                normalizedV =
                    static_cast<float>(face.textureVs[localTriangleVertexIndex] + face.textureDeltaV)
                    / static_cast<float>(textureHeight);
            }

            triangleVertices[triangleVertexSlot] =
                {worldVertex.x, worldVertex.y, worldVertex.z, normalizedU, normalizedV};
        }

        if (!isTriangleValid)
        {
            continue;
        }

        vertices.push_back(triangleVertices[0]);
        vertices.push_back(triangleVertices[1]);
        vertices.push_back(triangleVertices[2]);
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> buildProceduralIndoorFaceVertices(
    const Game::IndoorMapData &indoorMapData,
    const std::vector<Game::IndoorVertex> &indoorVertices,
    size_t faceIndex,
    const bx::Vec3 &origin)
{
    std::vector<EditorOutdoorViewport::ProceduralPreviewVertex> vertices;
    Game::IndoorFaceGeometryData geometry = {};

    if (!Game::buildIndoorFaceGeometry(indoorMapData, indoorVertices, faceIndex, geometry)
        || geometry.vertices.size() < 3)
    {
        return vertices;
    }

    const bx::Vec3 fallbackNormal =
        vecDot(geometry.normal, geometry.normal) > 0.001f ? geometry.normal : bx::Vec3 {0.0f, 0.0f, 1.0f};

    for (size_t triangleIndex = 1; triangleIndex + 1 < geometry.vertices.size(); ++triangleIndex)
    {
        appendProceduralTriangle(
            vertices,
            geometry.vertices[0],
            geometry.vertices[triangleIndex],
            geometry.vertices[triangleIndex + 1],
            origin,
            fallbackNormal);
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::PreviewVertex> buildIndoorWireVertices(
    const Game::IndoorMapData &indoorMapData,
    const std::vector<Game::IndoorVertex> &indoorVertices,
    bool showIndoorFloors,
    bool showIndoorCeilings,
    const std::optional<uint16_t> &isolatedRoomId)
{
    std::vector<EditorOutdoorViewport::PreviewVertex> vertices;
    constexpr uint32_t IndoorWireColor = 0x9cb5c8ffu;

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoorMapData.faces[faceIndex];

        if (!indoorFaceMatchesRoomIsolation(face, isolatedRoomId))
        {
            continue;
        }

        Game::IndoorFaceGeometryData geometry = {};

        if (!Game::buildIndoorFaceGeometry(indoorMapData, indoorVertices, faceIndex, geometry)
            || geometry.vertices.size() < 2)
        {
            continue;
        }

        if (indoorGeometryKindHiddenByView(geometry.kind, showIndoorFloors, showIndoorCeilings))
        {
            continue;
        }

        for (size_t vertexIndex = 0; vertexIndex < geometry.vertices.size(); ++vertexIndex)
        {
            const bx::Vec3 &start = geometry.vertices[vertexIndex];
            const bx::Vec3 &end = geometry.vertices[(vertexIndex + 1) % geometry.vertices.size()];
            vertices.push_back({start.x, start.y, start.z, IndoorWireColor});
            vertices.push_back({end.x, end.y, end.z, IndoorWireColor});
        }
    }

    return vertices;
}

bool indoorFaceHiddenByCeilingView(
    const Game::IndoorMapData &indoorMapData,
    const std::vector<Game::IndoorVertex> &indoorVertices,
    size_t faceIndex,
    bool showIndoorFloors,
    bool showIndoorCeilings,
    const std::optional<uint16_t> &isolatedRoomId,
    Game::IndoorFaceGeometryCache *pGeometryCache = nullptr)
{
    if (faceIndex >= indoorMapData.faces.size())
    {
        return true;
    }

    const Game::IndoorFace &face = indoorMapData.faces[faceIndex];

    if (!indoorFaceMatchesRoomIsolation(face, isolatedRoomId))
    {
        return true;
    }

    if (showIndoorFloors && showIndoorCeilings)
    {
        return false;
    }

    Game::IndoorFaceGeometryData geometry = {};
    const Game::IndoorFaceGeometryData *pGeometry = nullptr;

    if (pGeometryCache != nullptr)
    {
        pGeometry = pGeometryCache->geometryForFace(indoorMapData, indoorVertices, faceIndex);
    }
    else if (Game::buildIndoorFaceGeometry(indoorMapData, indoorVertices, faceIndex, geometry))
    {
        pGeometry = &geometry;
    }

    if (pGeometry == nullptr)
    {
        return false;
    }

    return indoorGeometryKindHiddenByView(pGeometry->kind, showIndoorFloors, showIndoorCeilings);
}

float calculateMechanismPreviewDistance(
    const Game::MapDeltaDoor &door,
    const Game::RuntimeMechanismState &previewState)
{
    if (previewState.state == static_cast<uint16_t>(Game::EvtMechanismState::Open))
    {
        return 0.0f;
    }

    if (previewState.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing))
    {
        const float closingDistance =
            previewState.timeSinceTriggeredMs * static_cast<float>(door.closeSpeed) / 1000.0f;
        return std::min(closingDistance, static_cast<float>(door.moveLength));
    }

    if (previewState.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening))
    {
        const float openingDistance =
            previewState.timeSinceTriggeredMs * static_cast<float>(door.openSpeed) / 1000.0f;
        return std::max(0.0f, static_cast<float>(door.moveLength) - openingDistance);
    }

    if (previewState.state == static_cast<uint16_t>(Game::EvtMechanismState::Closed) || (door.attributes & 0x2) != 0)
    {
        return static_cast<float>(door.moveLength);
    }

    return 0.0f;
}

Game::RuntimeMechanismState buildMechanismPreviewState(const Game::MapDeltaDoor &door)
{
    Game::RuntimeMechanismState previewState = {};
    previewState.state = door.state;
    previewState.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
    previewState.currentDistance = calculateMechanismPreviewDistance(door, previewState);
    previewState.isMoving =
        door.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening)
        || door.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing);
    return previewState;
}

void advanceMechanismPreviewState(
    const Game::MapDeltaDoor &door,
    float deltaMilliseconds,
    Game::RuntimeMechanismState &previewState)
{
    if (!previewState.isMoving || deltaMilliseconds <= 0.0f)
    {
        return;
    }

    previewState.timeSinceTriggeredMs += deltaMilliseconds;
    previewState.currentDistance = calculateMechanismPreviewDistance(door, previewState);

    if (previewState.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing))
    {
        const float closedDistance =
            previewState.timeSinceTriggeredMs * static_cast<float>(door.closeSpeed) / 1000.0f;

        if (closedDistance >= static_cast<float>(door.moveLength))
        {
            previewState.state = static_cast<uint16_t>(Game::EvtMechanismState::Closed);
            previewState.timeSinceTriggeredMs = 0.0f;
            previewState.currentDistance = static_cast<float>(door.moveLength);
            previewState.isMoving = false;
        }
    }
    else if (previewState.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening))
    {
        const float openedDistance =
            previewState.timeSinceTriggeredMs * static_cast<float>(door.openSpeed) / 1000.0f;

        if (openedDistance >= static_cast<float>(door.moveLength))
        {
            previewState.state = static_cast<uint16_t>(Game::EvtMechanismState::Open);
            previewState.timeSinceTriggeredMs = 0.0f;
            previewState.currentDistance = 0.0f;
            previewState.isMoving = false;
        }
    }
    else
    {
        previewState.isMoving = false;
    }
}

bool indoorDoorContainsFace(const Game::MapDeltaDoor &door, uint16_t faceId)
{
    return std::find(door.faceIds.begin(), door.faceIds.end(), faceId) != door.faceIds.end();
}

void synchronizeIndoorDoorFaceArraySizes(Game::MapDeltaDoor &door)
{
    door.numFaces = static_cast<uint16_t>(door.faceIds.size());
    door.deltaUs.resize(door.faceIds.size(), 0);
    door.deltaVs.resize(door.faceIds.size(), 0);
}

bool addIndoorDoorFace(Game::MapDeltaDoor &door, uint16_t faceId)
{
    if (indoorDoorContainsFace(door, faceId))
    {
        return false;
    }

    synchronizeIndoorDoorFaceArraySizes(door);
    door.faceIds.push_back(faceId);
    door.deltaUs.push_back(0);
    door.deltaVs.push_back(0);
    door.numFaces = static_cast<uint16_t>(door.faceIds.size());
    return true;
}

bool removeIndoorDoorFace(Game::MapDeltaDoor &door, uint16_t faceId)
{
    const auto iterator = std::find(door.faceIds.begin(), door.faceIds.end(), faceId);

    if (iterator == door.faceIds.end())
    {
        return false;
    }

    const size_t offset = static_cast<size_t>(std::distance(door.faceIds.begin(), iterator));
    door.faceIds.erase(iterator);

    if (offset < door.deltaUs.size())
    {
        door.deltaUs.erase(door.deltaUs.begin() + static_cast<ptrdiff_t>(offset));
    }

    if (offset < door.deltaVs.size())
    {
        door.deltaVs.erase(door.deltaVs.begin() + static_cast<ptrdiff_t>(offset));
    }

    synchronizeIndoorDoorFaceArraySizes(door);
    return true;
}

bool intersectRayTriangle(
    const bx::Vec3 &origin,
    const bx::Vec3 &direction,
    const bx::Vec3 &a,
    const bx::Vec3 &b,
    const bx::Vec3 &c,
    float &distance)
{
    const bx::Vec3 edge1 = vecSubtract(b, a);
    const bx::Vec3 edge2 = vecSubtract(c, a);
    const bx::Vec3 p = vecCross(direction, edge2);
    const float determinant = vecDot(edge1, p);

    if (std::fabs(determinant) <= 0.00001f)
    {
        return false;
    }

    const float inverseDeterminant = 1.0f / determinant;
    const bx::Vec3 t = vecSubtract(origin, a);
    const float u = vecDot(t, p) * inverseDeterminant;

    if (u < 0.0f || u > 1.0f)
    {
        return false;
    }

    const bx::Vec3 q = vecCross(t, edge1);
    const float v = vecDot(direction, q) * inverseDeterminant;

    if (v < 0.0f || (u + v) > 1.0f)
    {
        return false;
    }

    distance = vecDot(edge2, q) * inverseDeterminant;
    return distance >= 0.0f;
}

void appendCrossMarker(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const bx::Vec3 &center,
    float halfExtent,
    float height,
    uint32_t color)
{
    vertices.push_back({center.x - halfExtent, center.y, center.z + height * 0.5f, color});
    vertices.push_back({center.x + halfExtent, center.y, center.z + height * 0.5f, color});
    vertices.push_back({center.x, center.y - halfExtent, center.z + height * 0.5f, color});
    vertices.push_back({center.x, center.y + halfExtent, center.z + height * 0.5f, color});
    vertices.push_back({center.x, center.y, center.z, color});
    vertices.push_back({center.x, center.y, center.z + height, color});
}

void appendLine(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const bx::Vec3 &start,
    const bx::Vec3 &end,
    uint32_t color)
{
    vertices.push_back({start.x, start.y, start.z, color});
    vertices.push_back({end.x, end.y, end.z, color});
}

void appendCircleMarker(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const bx::Vec3 &center,
    float radius,
    uint32_t color)
{
    constexpr int SegmentCount = 32;

    for (int segment = 0; segment < SegmentCount; ++segment)
    {
        const float angle0 = static_cast<float>(segment) * bx::kPi * 2.0f / static_cast<float>(SegmentCount);
        const float angle1 = static_cast<float>(segment + 1) * bx::kPi * 2.0f / static_cast<float>(SegmentCount);
        const bx::Vec3 point0 = {
            center.x + std::cos(angle0) * radius,
            center.y + std::sin(angle0) * radius,
            center.z
        };
        const bx::Vec3 point1 = {
            center.x + std::cos(angle1) * radius,
            center.y + std::sin(angle1) * radius,
            center.z
        };
        appendLine(vertices, point0, point1, color);
    }
}

void appendArrowHead(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const bx::Vec3 &start,
    const bx::Vec3 &end,
    float size,
    uint32_t color)
{
    const bx::Vec3 direction = vecSubtract(end, start);
    const float length = vecLength(direction);

    if (length <= 0.001f)
    {
        return;
    }

    const bx::Vec3 forward = vecScale(direction, 1.0f / length);
    bx::Vec3 side = vecCross(forward, {0.0f, 0.0f, 1.0f});

    if (vecLength(side) <= 0.001f)
    {
        side = vecCross(forward, {0.0f, 1.0f, 0.0f});
    }

    side = vecNormalize(side);
    const bx::Vec3 base = vecSubtract(end, vecScale(forward, size));
    const bx::Vec3 left = vecAdd(base, vecScale(side, size * 0.45f));
    const bx::Vec3 right = vecSubtract(base, vecScale(side, size * 0.45f));

    appendLine(vertices, end, left, color);
    appendLine(vertices, end, right, color);
}

void appendBoxMarker(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const bx::Vec3 &center,
    float halfExtent,
    uint32_t color)
{
    const bx::Vec3 p000 = {center.x - halfExtent, center.y - halfExtent, center.z - halfExtent};
    const bx::Vec3 p001 = {center.x - halfExtent, center.y - halfExtent, center.z + halfExtent};
    const bx::Vec3 p010 = {center.x - halfExtent, center.y + halfExtent, center.z - halfExtent};
    const bx::Vec3 p011 = {center.x - halfExtent, center.y + halfExtent, center.z + halfExtent};
    const bx::Vec3 p100 = {center.x + halfExtent, center.y - halfExtent, center.z - halfExtent};
    const bx::Vec3 p101 = {center.x + halfExtent, center.y - halfExtent, center.z + halfExtent};
    const bx::Vec3 p110 = {center.x + halfExtent, center.y + halfExtent, center.z - halfExtent};
    const bx::Vec3 p111 = {center.x + halfExtent, center.y + halfExtent, center.z + halfExtent};

    appendLine(vertices, p000, p001, color);
    appendLine(vertices, p000, p010, color);
    appendLine(vertices, p000, p100, color);
    appendLine(vertices, p001, p011, color);
    appendLine(vertices, p001, p101, color);
    appendLine(vertices, p010, p011, color);
    appendLine(vertices, p010, p110, color);
    appendLine(vertices, p100, p101, color);
    appendLine(vertices, p100, p110, color);
    appendLine(vertices, p111, p101, color);
    appendLine(vertices, p111, p110, color);
    appendLine(vertices, p111, p011, color);
}

void appendBoxMarker(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const bx::Vec3 &center,
    const bx::Vec3 &halfExtents,
    uint32_t color)
{
    const bx::Vec3 p000 = {center.x - halfExtents.x, center.y - halfExtents.y, center.z - halfExtents.z};
    const bx::Vec3 p001 = {center.x - halfExtents.x, center.y - halfExtents.y, center.z + halfExtents.z};
    const bx::Vec3 p010 = {center.x - halfExtents.x, center.y + halfExtents.y, center.z - halfExtents.z};
    const bx::Vec3 p011 = {center.x - halfExtents.x, center.y + halfExtents.y, center.z + halfExtents.z};
    const bx::Vec3 p100 = {center.x + halfExtents.x, center.y - halfExtents.y, center.z - halfExtents.z};
    const bx::Vec3 p101 = {center.x + halfExtents.x, center.y - halfExtents.y, center.z + halfExtents.z};
    const bx::Vec3 p110 = {center.x + halfExtents.x, center.y + halfExtents.y, center.z - halfExtents.z};
    const bx::Vec3 p111 = {center.x + halfExtents.x, center.y + halfExtents.y, center.z + halfExtents.z};

    appendLine(vertices, p000, p001, color);
    appendLine(vertices, p000, p010, color);
    appendLine(vertices, p000, p100, color);
    appendLine(vertices, p001, p011, color);
    appendLine(vertices, p001, p101, color);
    appendLine(vertices, p010, p011, color);
    appendLine(vertices, p010, p110, color);
    appendLine(vertices, p100, p101, color);
    appendLine(vertices, p100, p110, color);
    appendLine(vertices, p111, p101, color);
    appendLine(vertices, p111, p110, color);
    appendLine(vertices, p111, p011, color);
}

bool intersectRayAabbDistance(
    const bx::Vec3 &origin,
    const bx::Vec3 &direction,
    const bx::Vec3 &minPoint,
    const bx::Vec3 &maxPoint,
    float &distance)
{
    float tMin = 0.0f;
    float tMax = FLT_MAX;

    const float originValues[3] = {origin.x, origin.y, origin.z};
    const float directionValues[3] = {direction.x, direction.y, direction.z};
    const float minValues[3] = {minPoint.x, minPoint.y, minPoint.z};
    const float maxValues[3] = {maxPoint.x, maxPoint.y, maxPoint.z};

    for (size_t axis = 0; axis < 3; ++axis)
    {
        if (std::fabs(directionValues[axis]) <= 0.00001f)
        {
            if (originValues[axis] < minValues[axis] || originValues[axis] > maxValues[axis])
            {
                return false;
            }

            continue;
        }

        const float inverseDirection = 1.0f / directionValues[axis];
        float t0 = (minValues[axis] - originValues[axis]) * inverseDirection;
        float t1 = (maxValues[axis] - originValues[axis]) * inverseDirection;

        if (t0 > t1)
        {
            std::swap(t0, t1);
        }

        tMin = std::max(tMin, t0);
        tMax = std::min(tMax, t1);

        if (tMin > tMax)
        {
            return false;
        }
    }

    distance = tMin;
    return true;
}

bool pointInsideAabb(
    const bx::Vec3 &point,
    const bx::Vec3 &minPoint,
    const bx::Vec3 &maxPoint)
{
    return point.x >= minPoint.x && point.x <= maxPoint.x
        && point.y >= minPoint.y && point.y <= maxPoint.y
        && point.z >= minPoint.z && point.z <= maxPoint.z;
}

bool mm9DatMarkerHasLineOfSight(
    const EditorMm9DatWorldSidecar &datWorld,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &target)
{
    const bx::Vec3 toTarget = vecSubtract(target, cameraPosition);
    const float targetDistance = vecLength(toTarget);

    if (targetDistance <= 1.0f)
    {
        return true;
    }

    const bx::Vec3 direction = vecScale(toTarget, 1.0f / targetDistance);
    constexpr float StartSlack = 8.0f;
    constexpr float EndSlack = 16.0f;

    for (const EditorMm9DatWorldModelSummary &model : datWorld.worldModels)
    {
        if ((!model.roles.visible && !model.roles.terrain && !model.roles.movable)
            || model.roles.sky
            || model.roles.visBsp
            || model.roles.triggerOrVolume)
        {
            continue;
        }

        const bx::Vec3 rawMinPoint = {
            model.boundsMinLt.x * Game::Mm9DatToOpenYammScale,
            model.boundsMinLt.z * Game::Mm9DatToOpenYammScale,
            model.boundsMinLt.y * Game::Mm9DatToOpenYammScale
        };
        const bx::Vec3 rawMaxPoint = {
            model.boundsMaxLt.x * Game::Mm9DatToOpenYammScale,
            model.boundsMaxLt.z * Game::Mm9DatToOpenYammScale,
            model.boundsMaxLt.y * Game::Mm9DatToOpenYammScale
        };
        constexpr float BoundsSlack = 4.0f;
        const bx::Vec3 minPoint = {
            std::min(rawMinPoint.x, rawMaxPoint.x) - BoundsSlack,
            std::min(rawMinPoint.y, rawMaxPoint.y) - BoundsSlack,
            std::min(rawMinPoint.z, rawMaxPoint.z) - BoundsSlack
        };
        const bx::Vec3 maxPoint = {
            std::max(rawMinPoint.x, rawMaxPoint.x) + BoundsSlack,
            std::max(rawMinPoint.y, rawMaxPoint.y) + BoundsSlack,
            std::max(rawMinPoint.z, rawMaxPoint.z) + BoundsSlack
        };

        if (pointInsideAabb(target, minPoint, maxPoint))
        {
            continue;
        }

        float distance = 0.0f;

        if (!intersectRayAabbDistance(cameraPosition, direction, minPoint, maxPoint, distance))
        {
            continue;
        }

        if (distance > StartSlack && distance < targetDistance - EndSlack)
        {
            return false;
        }
    }

    return true;
}

bx::Vec3 mm9LtToOpenYamm(const EditorMm9Vec3 &value)
{
    return {
        value.x * Game::Mm9DatToOpenYammScale,
        value.z * Game::Mm9DatToOpenYammScale,
        value.y * Game::Mm9DatToOpenYammScale
    };
}

bx::Vec3 mm9DatVec3LtToOpenYamm(const Game::Mm9DatVec3 &value)
{
    return {
        value.x * Game::Mm9DatToOpenYammScale,
        value.z * Game::Mm9DatToOpenYammScale,
        value.y * Game::Mm9DatToOpenYammScale
    };
}

std::optional<size_t> mm9RawObjectSidecarIndexForSourceObject(
    const EditorMm9RawObjectsSidecar &rawObjects,
    size_t sourceObjectIndex)
{
    for (size_t rawObjectIndex = 0; rawObjectIndex < rawObjects.objects.size(); ++rawObjectIndex)
    {
        if (rawObjects.objects[rawObjectIndex].objectIndex == sourceObjectIndex)
        {
            return rawObjectIndex;
        }
    }

    return std::nullopt;
}

std::optional<bx::Vec3> mm9SourceObjectMarkerPosition(
    const EditorDocument &document,
    size_t sourceObjectIndex)
{
    for (const Game::Mm9Object &object : document.mm9ObjectLayer().objects)
    {
        if (object.sourceObjectIndex == sourceObjectIndex && object.hasPosition)
        {
            return mm9DatVec3LtToOpenYamm(object.positionLt);
        }
    }

    for (const Game::Mm9LightObject &light : document.mm9LightLayer().lights)
    {
        if (light.sourceObjectIndex == sourceObjectIndex && light.hasPosition)
        {
            return mm9DatVec3LtToOpenYamm(light.positionLt);
        }
    }

    for (const Game::Mm9SoundObject &sound : document.mm9SoundLayer().objects)
    {
        if (sound.sourceObjectIndex == sourceObjectIndex && (sound.hasSoundPosition || sound.hasPosition))
        {
            return mm9DatVec3LtToOpenYamm(sound.hasSoundPosition ? sound.soundPositionLt : sound.positionLt);
        }
    }

    for (const Game::Mm9SpawnObject &spawn : document.mm9SpawnLayer().objects)
    {
        if (spawn.sourceObjectIndex == sourceObjectIndex && spawn.hasPosition)
        {
            return mm9DatVec3LtToOpenYamm(spawn.positionLt);
        }
    }

    for (const Game::OutdoorSceneModelInstance &modelInstance : document.outdoorSceneData().modelInstances)
    {
        if (modelInstance.sourceObjectIndex == sourceObjectIndex)
        {
            return modelInstanceSelectionCenter(modelInstance);
        }
    }

    return std::nullopt;
}

std::vector<EditorOutdoorViewport::PreviewVertex> buildMm9DatUserPortalOverlayVertices(
    const EditorMm9DatWorldSidecar &datWorld)
{
    std::vector<EditorOutdoorViewport::PreviewVertex> vertices;
    vertices.reserve(datWorld.userPortals.size() * 24);
    constexpr uint32_t PortalColor = 0xFFFFD080u;

    for (const EditorMm9DatUserPortalSummary &portal : datWorld.userPortals)
    {
        const bx::Vec3 center = mm9LtToOpenYamm(portal.centerLt);
        const bx::Vec3 dims = mm9LtToOpenYamm(portal.dimsLt);
        const bx::Vec3 halfExtents = {
            std::max(std::abs(dims.x) * 0.5f, 16.0f),
            std::max(std::abs(dims.y) * 0.5f, 16.0f),
            std::max(std::abs(dims.z) * 0.5f, 16.0f)
        };

        appendBoxMarker(vertices, center, halfExtents, PortalColor);
    }

    return vertices;
}

std::vector<EditorOutdoorViewport::PreviewVertex> buildMm9DatWorldModelOverlayVertices(
    const EditorMm9DatWorldSidecar &datWorld)
{
    std::vector<EditorOutdoorViewport::PreviewVertex> vertices;
    vertices.reserve(datWorld.worldModels.size() * 24);
    constexpr uint32_t VisibleColor = 0xFF82E0A6u;
    constexpr uint32_t HelperColor = 0xFFE0C072u;
    constexpr uint32_t MovableColor = 0xFFFF9CE0u;

    for (const EditorMm9DatWorldModelSummary &model : datWorld.worldModels)
    {
        const bx::Vec3 minPoint = mm9LtToOpenYamm(model.boundsMinLt);
        const bx::Vec3 maxPoint = mm9LtToOpenYamm(model.boundsMaxLt);
        const bx::Vec3 center = {
            (minPoint.x + maxPoint.x) * 0.5f,
            (minPoint.y + maxPoint.y) * 0.5f,
            (minPoint.z + maxPoint.z) * 0.5f
        };
        const bx::Vec3 halfExtents = {
            std::max(std::abs(maxPoint.x - minPoint.x) * 0.5f, 16.0f),
            std::max(std::abs(maxPoint.y - minPoint.y) * 0.5f, 16.0f),
            std::max(std::abs(maxPoint.z - minPoint.z) * 0.5f, 16.0f)
        };
        const uint32_t color =
            model.roles.movable
                ? MovableColor
                : (model.roles.visible || model.roles.terrain ? VisibleColor : HelperColor);

        appendBoxMarker(vertices, center, halfExtents, color);
    }

    return vertices;
}

bool mm9DatWorldModelBounds(
    const EditorMm9DatWorldSidecar &datWorld,
    size_t sourceModelIndex,
    bx::Vec3 &center,
    bx::Vec3 &halfExtents)
{
    if (sourceModelIndex >= datWorld.worldModels.size())
    {
        return false;
    }

    const EditorMm9DatWorldModelSummary &model = datWorld.worldModels[sourceModelIndex];
    const bx::Vec3 minPoint = mm9LtToOpenYamm(model.boundsMinLt);
    const bx::Vec3 maxPoint = mm9LtToOpenYamm(model.boundsMaxLt);
    center = {
        (minPoint.x + maxPoint.x) * 0.5f,
        (minPoint.y + maxPoint.y) * 0.5f,
        (minPoint.z + maxPoint.z) * 0.5f
    };
    halfExtents = {
        std::max(std::abs(maxPoint.x - minPoint.x) * 0.5f, 16.0f),
        std::max(std::abs(maxPoint.y - minPoint.y) * 0.5f, 16.0f),
        std::max(std::abs(maxPoint.z - minPoint.z) * 0.5f, 16.0f)
    };
    return true;
}

void appendMm9DatTriangleEdges(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const Game::Mm9DatRenderTriangle &triangle,
    uint32_t color)
{
    const std::array<bx::Vec3, 3> points = {{
        {triangle.vertices[0].x, triangle.vertices[0].y, triangle.vertices[0].z},
        {triangle.vertices[1].x, triangle.vertices[1].y, triangle.vertices[1].z},
        {triangle.vertices[2].x, triangle.vertices[2].y, triangle.vertices[2].z}
    }};

    appendLine(vertices, points[0], points[1], color);
    appendLine(vertices, points[1], points[2], color);
    appendLine(vertices, points[2], points[0], color);
}

void appendMm9DatTriangleFill(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const Game::Mm9DatRenderTriangle &triangle,
    uint32_t color)
{
    for (const Game::Mm9DatRenderVertex &vertex : triangle.vertices)
    {
        vertices.push_back({vertex.x, vertex.y, vertex.z, color});
    }
}

void appendCollisionVolumeMarker(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const bx::Vec3 &baseCenter,
    float radius,
    float height,
    uint32_t color,
    uint32_t centerColor);

std::vector<EditorOutdoorViewport::PreviewVertex> buildMm9DatObjectOverlayVertices(
    const Game::Mm9ObjectLayer &objectLayer)
{
    std::vector<EditorOutdoorViewport::PreviewVertex> vertices;
    vertices.reserve(objectLayer.boundsEvidenceObjectCount * 24 + objectLayer.triggerVolumeCount * 6);
    constexpr uint32_t ObjectBoundsColor = 0xFF70D7FFu;
    constexpr uint32_t TriggerBoundsColor = 0xFFB36BFFu;
    constexpr uint32_t TriggerCenterColor = 0xFFFFFFFFu;

    for (const Game::Mm9Object &object : objectLayer.objects)
    {
        if (!object.hasPosition)
        {
            continue;
        }

        const bx::Vec3 center = mm9DatVec3LtToOpenYamm(object.positionLt);
        const uint32_t color = object.triggerVolume ? TriggerBoundsColor : ObjectBoundsColor;
        const float scale = object.hasScale ? std::max(std::abs(object.scale), 0.01f) : 1.0f;

        if (object.hasDims)
        {
            const bx::Vec3 dims = mm9DatVec3LtToOpenYamm(object.dimsLt);
            const bx::Vec3 halfExtents = {
                std::max(std::abs(dims.x) * 0.5f * scale, 16.0f),
                std::max(std::abs(dims.y) * 0.5f * scale, 16.0f),
                std::max(std::abs(dims.z) * 0.5f * scale, 16.0f)
            };
            appendBoxMarker(vertices, center, halfExtents, color);
            continue;
        }

        if (object.hasRadius)
        {
            const float radius = std::max(std::abs(object.radius) * Game::Mm9DatToOpenYammScale * scale, 16.0f);
            const float height =
                object.hasBoundsEvidence ? radius * 2.0f : 64.0f * Game::Mm9DatToOpenYammScale;
            appendCollisionVolumeMarker(vertices, center, radius, height, color, TriggerCenterColor);
            continue;
        }

        if (object.triggerVolume)
        {
            appendCrossMarker(vertices, center, 64.0f, 128.0f, TriggerCenterColor);
        }
    }

    return vertices;
}

void appendCollisionVolumeMarker(
    std::vector<EditorOutdoorViewport::PreviewVertex> &vertices,
    const bx::Vec3 &baseCenter,
    float radius,
    float height,
    uint32_t color,
    uint32_t centerColor)
{
    const float halfExtent = std::max(radius, 32.0f);
    const float volumeHeight = std::max(height, 64.0f);
    const float minX = baseCenter.x - halfExtent;
    const float maxX = baseCenter.x + halfExtent;
    const float minY = baseCenter.y - halfExtent;
    const float maxY = baseCenter.y + halfExtent;
    const float minZ = baseCenter.z;
    const float maxZ = baseCenter.z + volumeHeight;

    const bx::Vec3 bottom00 = {minX, minY, minZ};
    const bx::Vec3 bottom01 = {minX, maxY, minZ};
    const bx::Vec3 bottom10 = {maxX, minY, minZ};
    const bx::Vec3 bottom11 = {maxX, maxY, minZ};
    const bx::Vec3 top00 = {minX, minY, maxZ};
    const bx::Vec3 top01 = {minX, maxY, maxZ};
    const bx::Vec3 top10 = {maxX, minY, maxZ};
    const bx::Vec3 top11 = {maxX, maxY, maxZ};

    appendLine(vertices, bottom00, bottom01, color);
    appendLine(vertices, bottom01, bottom11, color);
    appendLine(vertices, bottom11, bottom10, color);
    appendLine(vertices, bottom10, bottom00, color);
    appendLine(vertices, top00, top01, color);
    appendLine(vertices, top01, top11, color);
    appendLine(vertices, top11, top10, color);
    appendLine(vertices, top10, top00, color);
    appendLine(vertices, bottom00, top00, color);
    appendLine(vertices, bottom01, top01, color);
    appendLine(vertices, bottom10, top10, color);
    appendLine(vertices, bottom11, top11, color);
    appendLine(vertices, baseCenter, {baseCenter.x, baseCenter.y, maxZ}, centerColor);
    appendLine(vertices, {minX, baseCenter.y, minZ}, {maxX, baseCenter.y, minZ}, centerColor);
    appendLine(vertices, {baseCenter.x, minY, minZ}, {baseCenter.x, maxY, minZ}, centerColor);
}

void drawMechanismOverlayLabel(
    ImDrawList *pDrawList,
    const ImVec2 &anchor,
    ImU32 color,
    const char *pLabel)
{
    const ImVec2 textSize = ImGui::CalcTextSize(pLabel);
    const ImVec2 padding = {6.0f, 3.0f};
    const ImVec2 min = {anchor.x + 10.0f, anchor.y - textSize.y - 10.0f};
    const ImVec2 max = {
        min.x + textSize.x + padding.x * 2.0f,
        min.y + textSize.y + padding.y * 2.0f};
    pDrawList->AddRectFilled(min, max, IM_COL32(18, 22, 26, 220), 4.0f);
    pDrawList->AddRect(min, max, IM_COL32(255, 255, 255, 36), 4.0f, 0, 1.0f);
    pDrawList->AddText({min.x + padding.x, min.y + padding.y}, color, pLabel);
}

void drawMechanismOverlayCircle(ImDrawList *pDrawList, const ImVec2 &center, float radius, ImU32 color)
{
    pDrawList->AddCircleFilled(center, radius + 3.0f, IM_COL32(0, 0, 0, 150), 20);
    pDrawList->AddCircle(center, radius, color, 20, 3.0f);
}

void drawMechanismOverlaySquare(ImDrawList *pDrawList, const ImVec2 &center, float radius, ImU32 color)
{
    const ImVec2 min = {center.x - radius, center.y - radius};
    const ImVec2 max = {center.x + radius, center.y + radius};
    pDrawList->AddRectFilled(
        {min.x - 3.0f, min.y - 3.0f},
        {max.x + 3.0f, max.y + 3.0f},
        IM_COL32(0, 0, 0, 150),
        4.0f);
    pDrawList->AddRect(min, max, color, 4.0f, 0, 3.0f);
}

void drawMechanismOverlayDiamond(ImDrawList *pDrawList, const ImVec2 &center, float radius, ImU32 color)
{
    const ImVec2 top = {center.x, center.y - radius};
    const ImVec2 right = {center.x + radius, center.y};
    const ImVec2 bottom = {center.x, center.y + radius};
    const ImVec2 left = {center.x - radius, center.y};
    pDrawList->AddQuadFilled(
        {top.x, top.y - 3.0f},
        {right.x + 3.0f, right.y},
        {bottom.x, bottom.y + 3.0f},
        {left.x - 3.0f, left.y},
        IM_COL32(0, 0, 0, 150));
    pDrawList->AddQuad(top, right, bottom, left, color, 3.0f);
}

void drawMechanismCenterHandle(
    ImDrawList *pDrawList,
    const ImVec2 &center,
    float radius,
    ImU32 ringColor,
    bool selected)
{
    const float outerRadius = radius + (selected ? 5.0f : 3.0f);
    pDrawList->AddCircleFilled(center, outerRadius, IM_COL32(0, 0, 0, 150), 24);
    pDrawList->AddCircleFilled(
        center,
        radius,
        selected ? IM_COL32(255, 255, 255, 52) : IM_COL32(24, 30, 36, 210),
        24);
    pDrawList->AddCircle(center, radius, ringColor, 24, selected ? 3.5f : 2.5f);
    pDrawList->AddCircleFilled(center, 3.0f, ringColor, 12);
}

void drawEditorCenterHandle(
    ImDrawList *pDrawList,
    const ImVec2 &center,
    float radius,
    ImU32 ringColor,
    bool selected)
{
    drawMechanismCenterHandle(pDrawList, center, radius, ringColor, selected);
}

void drawLightBulbCenterHandle(
    ImDrawList *pDrawList,
    const ImVec2 &center,
    float radius,
    ImU32 color,
    bool selected)
{
    const float outerRadius = radius + (selected ? 5.0f : 3.0f);
    pDrawList->AddCircleFilled(center, outerRadius, IM_COL32(0, 0, 0, 150), 24);
    pDrawList->AddCircleFilled(
        {center.x, center.y - radius * 0.18f},
        radius * 0.62f,
        selected ? IM_COL32(255, 255, 255, 64) : IM_COL32(24, 30, 36, 220),
        20);
    pDrawList->AddCircle({center.x, center.y - radius * 0.18f}, radius * 0.62f, color, 20, selected ? 3.0f : 2.2f);
    pDrawList->AddRectFilled(
        {center.x - radius * 0.35f, center.y + radius * 0.35f},
        {center.x + radius * 0.35f, center.y + radius * 0.78f},
        color,
        2.0f);
    pDrawList->AddLine(
        {center.x - radius * 0.45f, center.y + radius * 1.0f},
        {center.x + radius * 0.45f, center.y + radius * 1.0f},
        color,
        selected ? 3.0f : 2.0f);
}

void drawTranslateAxisOverlay(
    ImDrawList *pDrawList,
    const ImVec2 &origin,
    const ImVec2 &end,
    ImU32 color,
    const char *pLabel)
{
    const ImVec2 delta = {end.x - origin.x, end.y - origin.y};
    const float length = std::sqrt(delta.x * delta.x + delta.y * delta.y);

    if (length < 8.0f)
    {
        return;
    }

    const float inverseLength = 1.0f / length;
    const ImVec2 direction = {delta.x * inverseLength, delta.y * inverseLength};
    const ImVec2 normal = {-direction.y, direction.x};
    const ImVec2 start = {origin.x + direction.x * 15.0f, origin.y + direction.y * 15.0f};
    const ImVec2 arrowBase = {end.x - direction.x * 13.0f, end.y - direction.y * 13.0f};

    pDrawList->AddLine(start, end, IM_COL32(0, 0, 0, 180), 6.0f);
    pDrawList->AddLine(start, end, color, 3.5f);
    pDrawList->AddTriangleFilled(
        end,
        {arrowBase.x + normal.x * 6.0f, arrowBase.y + normal.y * 6.0f},
        {arrowBase.x - normal.x * 6.0f, arrowBase.y - normal.y * 6.0f},
        IM_COL32(0, 0, 0, 180));
    pDrawList->AddTriangleFilled(
        end,
        {arrowBase.x + normal.x * 4.5f, arrowBase.y + normal.y * 4.5f},
        {arrowBase.x - normal.x * 4.5f, arrowBase.y - normal.y * 4.5f},
        color);
    pDrawList->AddCircleFilled(end, 5.0f, IM_COL32(0, 0, 0, 180), 16);
    pDrawList->AddCircleFilled(end, 3.5f, color, 16);
    pDrawList->AddText(
        {end.x + direction.x * 8.0f - 3.0f, end.y + direction.y * 8.0f - 7.0f},
        color,
        pLabel);
}

std::optional<bx::Vec3> indoorFaceCenter(
    const Game::IndoorMapData &indoorMapData,
    const std::vector<Game::IndoorVertex> &indoorVertices,
    size_t faceId)
{
    if (faceId >= indoorMapData.faces.size())
    {
        return std::nullopt;
    }

    Game::IndoorFaceGeometryData geometry = {};

    if (!Game::buildIndoorFaceGeometry(indoorMapData, indoorVertices, faceId, geometry) || geometry.vertices.empty())
    {
        return std::nullopt;
    }

    bx::Vec3 center = {0.0f, 0.0f, 0.0f};

    for (const bx::Vec3 &vertex : geometry.vertices)
    {
        center.x += vertex.x;
        center.y += vertex.y;
        center.z += vertex.z;
    }

    const float inverseCount = 1.0f / static_cast<float>(geometry.vertices.size());
    center.x *= inverseCount;
    center.y *= inverseCount;
    center.z *= inverseCount;
    return center;
}

void assignIndoorEntityToSector(Game::IndoorMapData &indoorGeometry, size_t entityIndex)
{
    if (entityIndex >= indoorGeometry.entities.size())
    {
        return;
    }

    const uint16_t clampedEntityIndex = static_cast<uint16_t>(std::min<size_t>(entityIndex, 65535));

    for (Game::IndoorSector &sector : indoorGeometry.sectors)
    {
        sector.decorationIds.erase(
            std::remove(sector.decorationIds.begin(), sector.decorationIds.end(), clampedEntityIndex),
            sector.decorationIds.end());
    }

    const Game::IndoorEntity &entity = indoorGeometry.entities[entityIndex];
    Game::IndoorFaceGeometryCache geometryCache(indoorGeometry.faces.size());
    const std::optional<int16_t> sectorId = Game::findIndoorSectorForPoint(
        indoorGeometry,
        indoorGeometry.vertices,
        {
            static_cast<float>(entity.x),
            static_cast<float>(entity.y),
            static_cast<float>(entity.z)
        },
        &geometryCache);

    if (!sectorId.has_value() || *sectorId < 0 || static_cast<size_t>(*sectorId) >= indoorGeometry.sectors.size())
    {
        return;
    }

    std::vector<uint16_t> &decorationIds = indoorGeometry.sectors[static_cast<size_t>(*sectorId)].decorationIds;

    if (std::find(decorationIds.begin(), decorationIds.end(), clampedEntityIndex) == decorationIds.end())
    {
        decorationIds.push_back(clampedEntityIndex);
    }
}

std::optional<int16_t> findIndoorSectorIdForPoint(Game::IndoorMapData &indoorGeometry, int x, int y, int z)
{
    Game::IndoorFaceGeometryCache geometryCache(indoorGeometry.faces.size());
    return Game::findIndoorSectorForPoint(
        indoorGeometry,
        indoorGeometry.vertices,
        {static_cast<float>(x), static_cast<float>(y), static_cast<float>(z)},
        &geometryCache);
}

void assignIndoorLightToSector(Game::IndoorMapData &indoorGeometry, size_t lightIndex)
{
    if (lightIndex >= indoorGeometry.lights.size())
    {
        return;
    }

    const uint16_t clampedLightIndex = static_cast<uint16_t>(std::min<size_t>(lightIndex, 65535));

    for (Game::IndoorSector &sector : indoorGeometry.sectors)
    {
        sector.lightIds.erase(
            std::remove(sector.lightIds.begin(), sector.lightIds.end(), clampedLightIndex),
            sector.lightIds.end());
    }

    const Game::IndoorLight &light = indoorGeometry.lights[lightIndex];
    const std::optional<int16_t> sectorId = findIndoorSectorIdForPoint(
        indoorGeometry,
        static_cast<int>(light.x),
        static_cast<int>(light.y),
        static_cast<int>(light.z));

    if (!sectorId.has_value() || *sectorId < 0 || static_cast<size_t>(*sectorId) >= indoorGeometry.sectors.size())
    {
        return;
    }

    std::vector<uint16_t> &lightIds = indoorGeometry.sectors[static_cast<size_t>(*sectorId)].lightIds;

    if (std::find(lightIds.begin(), lightIds.end(), clampedLightIndex) == lightIds.end())
    {
        lightIds.push_back(clampedLightIndex);
    }
}

bool indoorMarkerHasLineOfSight(
    const Game::IndoorMapData &indoorMapData,
    const std::vector<Game::IndoorVertex> &indoorVertices,
    Game::IndoorFaceGeometryCache &geometryCache,
    const bx::Vec3 &cameraPosition,
    const bx::Vec3 &target,
    bool showIndoorFloors,
    bool showIndoorCeilings,
    const std::optional<uint16_t> &isolatedRoomId)
{
    const bx::Vec3 toTarget = vecSubtract(target, cameraPosition);
    const float targetDistance = vecLength(toTarget);

    if (targetDistance <= 1.0f)
    {
        return true;
    }

    const bx::Vec3 direction = vecScale(toTarget, 1.0f / targetDistance);
    constexpr float StartSlack = 8.0f;
    constexpr float EndSlack = 16.0f;
    constexpr float BoundsSlack = 4.0f;
    const float segmentMinX = std::min(cameraPosition.x, target.x) - BoundsSlack;
    const float segmentMaxX = std::max(cameraPosition.x, target.x) + BoundsSlack;
    const float segmentMinY = std::min(cameraPosition.y, target.y) - BoundsSlack;
    const float segmentMaxY = std::max(cameraPosition.y, target.y) + BoundsSlack;
    const float segmentMinZ = std::min(cameraPosition.z, target.z) - BoundsSlack;
    const float segmentMaxZ = std::max(cameraPosition.z, target.z) + BoundsSlack;

    for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoorMapData.faces[faceIndex];

        if (face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal))
        {
            continue;
        }

        if (indoorFaceHiddenByCeilingView(
                indoorMapData,
                indoorVertices,
                faceIndex,
                showIndoorFloors,
                showIndoorCeilings,
                isolatedRoomId,
                &geometryCache))
        {
            continue;
        }

        const Game::IndoorFaceGeometryData *pGeometry =
            geometryCache.geometryForFace(indoorMapData, indoorVertices, faceIndex);

        if (pGeometry == nullptr || pGeometry->vertices.size() < 3)
        {
            continue;
        }

        if (pGeometry->maxX < segmentMinX
            || pGeometry->minX > segmentMaxX
            || pGeometry->maxY < segmentMinY
            || pGeometry->minY > segmentMaxY
            || pGeometry->maxZ < segmentMinZ
            || pGeometry->minZ > segmentMaxZ)
        {
            continue;
        }

        for (size_t triangleIndex = 1; triangleIndex + 1 < pGeometry->vertices.size(); ++triangleIndex)
        {
            float distance = 0.0f;

            if (!intersectRayTriangle(
                    cameraPosition,
                    direction,
                    pGeometry->vertices[0],
                    pGeometry->vertices[triangleIndex],
                    pGeometry->vertices[triangleIndex + 1],
                    distance))
            {
                continue;
            }

            if (distance > StartSlack && distance < targetDistance - EndSlack)
            {
                return false;
            }
        }
    }

    return true;
}

float resolvedIndoorDoorDistance(
    const Game::MapDeltaDoor &door,
    const std::optional<Game::RuntimeMechanismState> &previewState)
{
    if (previewState.has_value())
    {
        return previewState->currentDistance;
    }

    Game::RuntimeMechanismState baseState = {};
    baseState.state = door.state;
    baseState.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
    baseState.currentDistance = calculateMechanismPreviewDistance(door, baseState);
    return baseState.currentDistance;
}
}

bgfx::VertexLayout EditorOutdoorViewport::PreviewVertex::ms_layout;
bgfx::VertexLayout EditorOutdoorViewport::TexturedPreviewVertex::ms_layout;
bgfx::VertexLayout EditorOutdoorViewport::ProceduralPreviewVertex::ms_layout;

EditorOutdoorViewport::EditorOutdoorViewport()
{
}

EditorOutdoorViewport::~EditorOutdoorViewport()
{
    shutdown();
}

void EditorOutdoorViewport::PreviewVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

void EditorOutdoorViewport::TexturedPreviewVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .end();
}

void EditorOutdoorViewport::ProceduralPreviewVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord1, 4, bgfx::AttribType::Float)
        .end();
}

void EditorOutdoorViewport::shutdown()
{
    if (m_shutdownComplete)
    {
        return;
    }

    m_shutdownComplete = true;
    destroyImportedModelPreview();
    destroyGeometryBuffers();
    destroyRenderTarget();

    for (auto &[textureName, texture] : m_entityBillboardTextures)
    {
        if (bgfx::isValid(texture.textureHandle))
        {
            bgfx::destroy(texture.textureHandle);
            texture.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_entityBillboardTextures.clear();
    m_cachedOutdoorTerrainGridKey.clear();
    m_cachedOutdoorTerrainGridVertices.clear();

    if (bgfx::isValid(m_programHandle))
    {
        bgfx::destroy(m_programHandle);
        m_programHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_texturedProgramHandle))
    {
        bgfx::destroy(m_texturedProgramHandle);
        m_texturedProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_proceduralPreviewProgramHandle))
    {
        bgfx::destroy(m_proceduralPreviewProgramHandle);
        m_proceduralPreviewProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_textureSamplerHandle))
    {
        bgfx::destroy(m_textureSamplerHandle);
        m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewColorAHandle))
    {
        bgfx::destroy(m_previewColorAHandle);
        m_previewColorAHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewColorBHandle))
    {
        bgfx::destroy(m_previewColorBHandle);
        m_previewColorBHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewColorCHandle))
    {
        bgfx::destroy(m_previewColorCHandle);
        m_previewColorCHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewColorDHandle))
    {
        bgfx::destroy(m_previewColorDHandle);
        m_previewColorDHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewParams0Handle))
    {
        bgfx::destroy(m_previewParams0Handle);
        m_previewParams0Handle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewParams1Handle))
    {
        bgfx::destroy(m_previewParams1Handle);
        m_previewParams1Handle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_previewObjectOriginHandle))
    {
        bgfx::destroy(m_previewObjectOriginHandle);
        m_previewObjectOriginHandle = BGFX_INVALID_HANDLE;
    }

    m_geometryKey.clear();
    m_cameraDocumentKey.clear();
    m_cameraInitializedForDocument = false;
}

void EditorOutdoorViewport::destroyImportedModelPreview()
{
    if (bgfx::isValid(m_importedModelPreviewBatch.vertexBufferHandle))
    {
        bgfx::destroy(m_importedModelPreviewBatch.vertexBufferHandle);
        m_importedModelPreviewBatch.vertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    m_importedModelPreviewBatch.vertexCount = 0;
    m_importedModelPreviewBatch.bmodelIndex = std::numeric_limits<size_t>::max();
    m_importedModelPreviewBatch.objectOrigin = {0.0f, 0.0f, 0.0f};
    m_importedModelPreviewKey.clear();
}

void EditorOutdoorViewport::updateAndRender(
    EditorSession &session,
    int viewportX,
    int viewportY,
    uint16_t viewportWidth,
    uint16_t viewportHeight,
    bool isHovered,
    bool isFocused,
    bool leftMouseClicked,
    bool leftMouseDown,
    float mouseX,
    float mouseY,
    float deltaSeconds)
{
    m_lastRenderSubmissionStats = {};
    m_viewportX = viewportX;
    m_viewportY = viewportY;
    m_viewportWidth = viewportWidth;
    m_viewportHeight = viewportHeight;
    m_isHovered = isHovered;
    m_isFocused = isFocused;
    m_lastMouseX = mouseX;
    m_lastMouseY = mouseY;

    ensureRenderTarget(viewportWidth, viewportHeight);

    if (bgfx::isValid(m_frameBufferHandle))
    {
        bgfx::setViewFrameBuffer(EditorSceneViewId, m_frameBufferHandle);
    }

    bgfx::setViewRect(EditorSceneViewId, 0, 0, m_renderWidth, m_renderHeight);
    bgfx::setViewClear(EditorSceneViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x2c2217ffu, 1.0f, 0);
    bgfx::touch(EditorSceneViewId);

    if (!session.hasDocument()
        || (session.document().kind() != EditorDocument::Kind::Outdoor
            && session.document().kind() != EditorDocument::Kind::Indoor
            && session.document().kind() != EditorDocument::Kind::Mm9Dat))
    {
        return;
    }

    m_lastRenderSubmissionStats.valid = true;
    m_lastRenderSubmissionStats.mm9DatDocument = session.document().kind() == EditorDocument::Kind::Mm9Dat;

    if (!ensureRenderResources())
    {
        return;
    }

    const EditorDocument &document = session.document();
    advanceIndoorMechanismPreview(document, deltaSeconds);
    ensureGeometryBuffers(session);
    refreshIndoorPreviewGeometryBuffers(document);
    updateCamera(document, isHovered, isFocused, deltaSeconds);

    const bx::Vec3 forward = {
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    };
    const bx::Vec3 at = {
        m_cameraPosition.x + forward.x,
        m_cameraPosition.y + forward.y,
        m_cameraPosition.z + forward.z
    };
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};

    bx::mtxLookAt(m_viewMatrix, m_cameraPosition, at, up, bx::Handedness::Right);
    float cameraFarPlane = CameraFarPlane;

    if (document.kind() == EditorDocument::Kind::Mm9Dat && document.hasMm9DatWorld())
    {
        const Game::Mm9DatCameraFrame cameraFrame =
            Game::frameMm9DatRenderBoundsCamera(document.mm9DatRenderBounds(), CameraVerticalFovDegrees);

        if (cameraFrame.valid)
        {
            cameraFarPlane = std::max(cameraFarPlane, cameraFrame.farPlane);
        }
    }

    bx::mtxProj(
        m_projectionMatrix,
        CameraVerticalFovDegrees,
        static_cast<float>(m_renderWidth) / static_cast<float>(std::max<uint16_t>(m_renderHeight, 1)),
        CameraNearPlane,
        cameraFarPlane,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right);
    bx::mtxMul(m_viewProjectionMatrix, m_viewMatrix, m_projectionMatrix);
    bgfx::setViewTransform(EditorSceneViewId, m_viewMatrix, m_projectionMatrix);
    ensureImportedModelPreview(session);

    if (ImGui::IsKeyPressed(ImGuiKey_Escape))
    {
        setPlacementKind(EditorSelectionKind::None);
    }

    if (isFocused && !ImGui::GetIO().WantTextInput)
    {
        if (ImGui::IsKeyPressed(ImGuiKey_W))
        {
            m_transformGizmoMode = TransformGizmoMode::Translate;
        }
        else if (ImGui::IsKeyPressed(ImGuiKey_R))
        {
            m_transformGizmoMode = TransformGizmoMode::Rotate;
        }
        else if (ImGui::IsKeyPressed(ImGuiKey_F))
        {
            focusSelection(document, session.selection());
        }
    }

    const bool isOutdoorDocument = document.kind() == EditorDocument::Kind::Outdoor;
    const bool isEditableLegacyWorldDocument =
        document.kind() == EditorDocument::Kind::Outdoor || document.kind() == EditorDocument::Kind::Indoor;
    const bool selectModeActive = m_placementKind == EditorSelectionKind::None;
    const bool startedGizmoDrag =
        isEditableLegacyWorldDocument && selectModeActive && tryBeginGizmoDrag(session, leftMouseClicked, mouseX, mouseY);
    const bool pickedBeforeEdit = !startedGizmoDrag && tryPick(session, leftMouseClicked, mouseX, mouseY);
    const bool selectedTerrainCell =
        !startedGizmoDrag
        && isOutdoorDocument
        && shouldRenderTerrainHeightmap(document)
        && trySelectTerrainCell(session, leftMouseClicked, mouseX, mouseY);
    const bool selectedInteractiveFace =
        !startedGizmoDrag
        && !selectedTerrainCell
        && isEditableLegacyWorldDocument
        && trySelectInteractiveFace(session, leftMouseClicked, mouseX, mouseY);
    const bool placedObject =
        !startedGizmoDrag
        && !selectedTerrainCell
        && !selectedInteractiveFace
        && !pickedBeforeEdit
        && isEditableLegacyWorldDocument
        && tryPlaceObject(session, leftMouseClicked, mouseX, mouseY);
    const bool consumedEditClick =
        startedGizmoDrag
        || pickedBeforeEdit
        || placedObject
        || selectedTerrainCell
        || selectedInteractiveFace;

    if (isEditableLegacyWorldDocument)
    {
        updateGizmoDrag(session, leftMouseDown, mouseX, mouseY);
    }

    if (!selectedTerrainCell
        && !selectedInteractiveFace
        && !placedObject
        && !consumedEditClick
        && (!isOutdoorDocument || m_activeGizmoDrag.mode == GizmoDragMode::None))
    {
        tryPick(session, leftMouseClicked, mouseX, mouseY);
    }

    submitStaticGeometry(session);
    submitEntityBillboardGeometry(session, document);
    submitMarkerGeometry(session, document, session.selection());
}

void EditorOutdoorViewport::renderOverlayUi(const EditorSession &session)
{
    if (session.hasDocument() && session.document().kind() == EditorDocument::Kind::Indoor)
    {
        std::string modeLabel = "INDOOR / SELECT";

        if (m_placementKind == EditorSelectionKind::InteractiveFace)
        {
            modeLabel = "INDOOR / FACE";
        }
        else if (m_placementKind == EditorSelectionKind::Actor)
        {
            modeLabel = "INDOOR / ACTOR PLACE";
        }
        else if (m_placementKind == EditorSelectionKind::Spawn)
        {
            modeLabel = "INDOOR / SPAWN PLACE";
        }
        else if (m_placementKind == EditorSelectionKind::Entity)
        {
            modeLabel = "INDOOR / DECORATION PLACE";
        }
        else if (m_placementKind == EditorSelectionKind::SpriteObject)
        {
            modeLabel = "INDOOR / OBJECT PLACE";
        }

        ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.95f, 0.87f, 0.76f, 1.0f));
        ImGui::TextUnformatted(modeLabel.c_str());
        ImGui::PopStyleColor();

        if (m_indoorDoorFaceEditMode != IndoorDoorFaceEditMode::None
            && m_indoorDoorFaceEditDoorIndex.has_value()
            && session.selection().kind == EditorSelectionKind::Door
            && session.selection().index == *m_indoorDoorFaceEditDoorIndex)
        {
            ImGui::TextDisabled(
                "%s",
                m_indoorDoorFaceEditMode == IndoorDoorFaceEditMode::Add
                    ? "LMB add face to mechanism  ·  F frame"
                    : "LMB remove face from mechanism  ·  F frame");
        }
        else if (m_placementKind == EditorSelectionKind::Actor
            || m_placementKind == EditorSelectionKind::Entity
            || m_placementKind == EditorSelectionKind::Spawn
            || m_placementKind == EditorSelectionKind::SpriteObject)
        {
            ImGui::TextDisabled("Move cursor  ·  LMB place  ·  Esc cancel");
        }
        else
        {
            ImGui::TextDisabled("LMB select  ·  RMB freelook  ·  F frame");
        }

        if (m_isolatedIndoorRoomId.has_value())
        {
            ImGui::TextDisabled(
                "Room %u isolated  ·  Floors %s  ·  Ceilings %s",
                static_cast<unsigned>(*m_isolatedIndoorRoomId),
                m_showIndoorFloors ? "on" : "off",
                m_showIndoorCeilings ? "on" : "off");
        }
        else if (!m_showIndoorFloors || !m_showIndoorCeilings)
        {
            ImGui::TextDisabled(
                "Floors %s  ·  Ceilings %s",
                m_showIndoorFloors ? "on" : "off",
                m_showIndoorCeilings ? "on" : "off");
        }

        if (m_indoorDoorFaceEditMode != IndoorDoorFaceEditMode::None
            && m_indoorDoorFaceEditDoorIndex.has_value()
            && session.selection().kind == EditorSelectionKind::Door
            && session.selection().index == *m_indoorDoorFaceEditDoorIndex)
        {
            const Game::IndoorSceneDoor &door =
                session.document().indoorSceneData().initialState.doors[*m_indoorDoorFaceEditDoorIndex];
            ImGui::Text(
                "Door %zu  ·  %s  ·  Faces %zu",
                *m_indoorDoorFaceEditDoorIndex,
                m_indoorDoorFaceEditMode == IndoorDoorFaceEditMode::Add ? "Add" : "Remove",
                door.door.faceIds.size());
        }
        else if (session.selection().kind == EditorSelectionKind::Door
            && session.selection().index < session.document().indoorSceneData().initialState.doors.size())
        {
            const Game::IndoorSceneDoor &door =
                session.document().indoorSceneData().initialState.doors[session.selection().index];
            uint16_t previewState = 0;
            float previewTimeSinceTriggeredMs = 0.0f;
            float currentDistance = 0.0f;
            bool isMoving = false;
            const bool hasPreview = tryGetIndoorMechanismPreview(
                session.document(),
                session.selection().index,
                previewState,
                previewTimeSinceTriggeredMs,
                currentDistance,
                isMoving);
            const float resolvedDistance =
                hasPreview
                    ? currentDistance
                    : resolvedIndoorDoorDistance(door.door, std::nullopt);
            ImGui::Text(
                "Door %zu  ·  Faces %zu  ·  Distance %.1f / %u%s",
                session.selection().index,
                door.door.faceIds.size(),
                resolvedDistance,
                door.door.moveLength,
                isMoving ? "  ·  Moving" : "");

            const std::optional<bx::Vec3> currentCenter = selectedWorldPosition(session.document(), session.selection());

            if (currentCenter)
            {
                const bx::Vec3 direction = {
                    static_cast<float>(door.door.directionX) / 65536.0f,
                    static_cast<float>(door.door.directionY) / 65536.0f,
                    static_cast<float>(door.door.directionZ) / 65536.0f};
                const bx::Vec3 currentOffset = vecScale(direction, resolvedDistance);
                const bx::Vec3 fullOffset = vecScale(direction, static_cast<float>(door.door.moveLength));
                const bx::Vec3 openCenter = {
                    currentCenter->x - currentOffset.x,
                    currentCenter->y - currentOffset.y,
                    currentCenter->z - currentOffset.z};
                const bx::Vec3 closedCenter = {
                    openCenter.x + fullOffset.x,
                    openCenter.y + fullOffset.y,
                    openCenter.z + fullOffset.z};

                float openX = 0.0f;
                float openY = 0.0f;
                float openW = 0.0f;
                float closedX = 0.0f;
                float closedY = 0.0f;
                float closedW = 0.0f;
                float currentX = 0.0f;
                float currentY = 0.0f;
                float currentW = 0.0f;
                const bool hasOpen = projectWorldPoint(
                    openCenter,
                    m_viewProjectionMatrix,
                    m_viewportWidth,
                    m_viewportHeight,
                    openX,
                    openY,
                    openW);
                const bool hasClosed = projectWorldPoint(
                    closedCenter,
                    m_viewProjectionMatrix,
                    m_viewportWidth,
                    m_viewportHeight,
                    closedX,
                    closedY,
                    closedW);
                const bool hasCurrent = projectWorldPoint(
                    *currentCenter,
                    m_viewProjectionMatrix,
                    m_viewportWidth,
                    m_viewportHeight,
                    currentX,
                    currentY,
                    currentW);

                if (hasOpen || hasClosed || hasCurrent)
                {
                    ImDrawList *pDrawList = ImGui::GetForegroundDrawList();
                    const ImU32 openColor = IM_COL32(102, 255, 140, 255);
                    const ImU32 closedColor = IM_COL32(255, 110, 110, 255);
                    const ImU32 currentColor = IM_COL32(255, 255, 255, 255);
                    const ImU32 pathColor = IM_COL32(255, 226, 110, 255);

                    const ImVec2 openPoint = {
                        static_cast<float>(m_viewportX) + openX,
                        static_cast<float>(m_viewportY) + openY};
                    const ImVec2 closedPoint = {
                        static_cast<float>(m_viewportX) + closedX,
                        static_cast<float>(m_viewportY) + closedY};
                    const ImVec2 currentPoint = {
                        static_cast<float>(m_viewportX) + currentX,
                        static_cast<float>(m_viewportY) + currentY};

                    if (hasOpen && hasClosed)
                    {
                        pDrawList->AddLine(openPoint, closedPoint, pathColor, 3.0f);
                        const ImVec2 directionScreen = {closedPoint.x - openPoint.x, closedPoint.y - openPoint.y};
                        const float directionLength =
                            std::sqrt(directionScreen.x * directionScreen.x + directionScreen.y * directionScreen.y);

                        if (directionLength > 8.0f)
                        {
                            const float inverseLength = 1.0f / directionLength;
                            const ImVec2 tangent = {
                                directionScreen.x * inverseLength,
                                directionScreen.y * inverseLength};
                            const ImVec2 normal = {-tangent.y, tangent.x};
                            const ImVec2 arrowBase = {
                                closedPoint.x - tangent.x * 16.0f,
                                closedPoint.y - tangent.y * 16.0f};
                            pDrawList->AddTriangleFilled(
                                closedPoint,
                                {arrowBase.x + normal.x * 6.0f, arrowBase.y + normal.y * 6.0f},
                                {arrowBase.x - normal.x * 6.0f, arrowBase.y - normal.y * 6.0f},
                                pathColor);
                        }
                    }

                    if (hasOpen)
                    {
                        drawMechanismOverlayCircle(pDrawList, openPoint, 10.0f, openColor);
                        drawMechanismOverlayLabel(pDrawList, openPoint, openColor, "OPEN");
                    }

                    if (hasClosed)
                    {
                        drawMechanismOverlaySquare(pDrawList, closedPoint, 10.0f, closedColor);
                        drawMechanismOverlayLabel(pDrawList, closedPoint, closedColor, "CLOSED");
                    }

                    if (hasCurrent)
                    {
                        drawMechanismOverlayDiamond(pDrawList, currentPoint, 11.0f, currentColor);
                        drawMechanismOverlayLabel(pDrawList, currentPoint, currentColor, "NOW");
                    }
                }
            }
        }
        else if (session.selection().kind == EditorSelectionKind::InteractiveFace)
        {
            const size_t selectedFaceCount =
                session.selectedInteractiveFaceIndices().empty() ? 1 : session.selectedInteractiveFaceIndices().size();
            const Game::IndoorMapData &indoorGeometry = session.document().indoorGeometry();

            if (session.selection().index < indoorGeometry.faces.size())
            {
                const Game::IndoorFace &selectedFace = indoorGeometry.faces[session.selection().index];
                uint32_t effectiveAttributes = selectedFace.attributes;

                for (const Game::IndoorSceneFaceAttributeOverride &overrideEntry :
                    session.document().indoorSceneData().initialState.faceAttributeOverrides)
                {
                    if (overrideEntry.faceIndex == session.selection().index && overrideEntry.legacyAttributes.has_value())
                    {
                        effectiveAttributes = *overrideEntry.legacyAttributes;
                        break;
                    }
                }

                const bool isPortal =
                    selectedFace.isPortal || Game::hasFaceAttribute(effectiveAttributes, Game::FaceAttribute::IsPortal);
                const std::vector<uint16_t> connectedRooms =
                    connectedIndoorSectorIds(indoorGeometry, selectedFace.roomNumber);

                if (isPortal)
                {
                    ImGui::Text(
                        "Face %zu  ·  Portal %u ↔ %u  ·  %zu selected",
                        session.selection().index,
                        static_cast<unsigned>(selectedFace.roomNumber),
                        static_cast<unsigned>(selectedFace.roomBehindNumber),
                        selectedFaceCount);
                }
                else if (!connectedRooms.empty())
                {
                    ImGui::Text(
                        "Face %zu  ·  Room %u  ·  Links %zu  ·  %zu selected",
                        session.selection().index,
                        static_cast<unsigned>(selectedFace.roomNumber),
                        connectedRooms.size(),
                        selectedFaceCount);
                }
                else
                {
                    ImGui::Text(
                        "Face %zu  ·  Room %u  ·  %zu selected",
                        session.selection().index,
                        static_cast<unsigned>(selectedFace.roomNumber),
                        selectedFaceCount);
                }
            }
            else
            {
                ImGui::Text("Face selection  ·  %zu selected", selectedFaceCount);
            }
        }
        else
        {
            ImGui::Text(
                "Actors %zu  ·  Objects %zu  ·  Doors %zu",
                session.document().indoorSceneData().initialState.actors.size(),
                session.document().indoorSceneData().initialState.spriteObjects.size(),
                session.document().indoorSceneData().initialState.doors.size());
        }

        {
            const Game::IndoorMapData &indoorGeometry = session.document().indoorGeometry();
            const Game::IndoorSceneData &sceneData = session.document().indoorSceneData();
            ImDrawList *pDrawList = ImGui::GetForegroundDrawList();
            const auto projectToOverlay =
                [this](const bx::Vec3 &point, ImVec2 &screenPoint)
            {
                float screenX = 0.0f;
                float screenY = 0.0f;
                float clipW = 0.0f;

                if (!projectWorldPoint(
                        point,
                        m_viewProjectionMatrix,
                        m_viewportWidth,
                        m_viewportHeight,
                        screenX,
                        screenY,
                        clipW))
                {
                    return false;
                }

                screenPoint = {
                    static_cast<float>(m_viewportX) + screenX,
                    static_cast<float>(m_viewportY) + screenY
                };
                return true;
            };
            const auto drawProjectedHandle =
                [this, pDrawList](
                    const bx::Vec3 &center,
                    ImU32 color,
                    bool selected,
                    bool lightBulb)
            {
                float screenX = 0.0f;
                float screenY = 0.0f;
                float clipW = 0.0f;

                if (!projectWorldPoint(
                        center,
                        m_viewProjectionMatrix,
                        m_viewportWidth,
                        m_viewportHeight,
                        screenX,
                        screenY,
                        clipW))
                {
                    return;
                }

                const ImVec2 handleCenter = {
                    static_cast<float>(m_viewportX) + screenX,
                    static_cast<float>(m_viewportY) + screenY};

                if (lightBulb)
                {
                    drawLightBulbCenterHandle(pDrawList, handleCenter, selected ? 12.0f : 10.0f, color, selected);
                    return;
                }

                drawEditorCenterHandle(pDrawList, handleCenter, selected ? 12.0f : 10.0f, color, selected);
            };

            for (const MarkerCandidate &candidate : m_markerCandidates)
            {
                const bool selected = session.selection().kind == candidate.selectionKind
                    && session.selection().index == candidate.selectionIndex;
                const uint8_t alpha = candidate.blockedByLineOfSight && !selected ? 96 : 255;

                if (candidate.selectionKind == EditorSelectionKind::Entity)
                {
                    drawProjectedHandle(candidate.worldPosition, IM_COL32(255, 214, 96, alpha), selected, false);
                    continue;
                }

                if (candidate.selectionKind == EditorSelectionKind::Light)
                {
                    if (candidate.selectionIndex >= indoorGeometry.lights.size())
                    {
                        continue;
                    }

                    const Game::IndoorLight &light = indoorGeometry.lights[candidate.selectionIndex];
                    const ImU32 color = selected
                        ? IM_COL32(255, 255, 255, 255)
                        : IM_COL32(
                            light.red == 0 ? 255 : light.red,
                            light.green == 0 ? 220 : light.green,
                            light.blue == 0 ? 96 : light.blue,
                            alpha);
                    drawProjectedHandle(candidate.worldPosition, color, selected, true);
                    continue;
                }

                if (candidate.selectionKind == EditorSelectionKind::Actor
                    || candidate.selectionKind == EditorSelectionKind::Spawn)
                {
                    if (candidate.selectionKind == EditorSelectionKind::Actor
                        && candidate.selectionIndex >= sceneData.initialState.actors.size())
                    {
                        continue;
                    }

                    if (candidate.selectionKind == EditorSelectionKind::Spawn
                        && candidate.selectionIndex >= indoorGeometry.spawns.size())
                    {
                        continue;
                    }

                    if (candidate.selectionKind == EditorSelectionKind::Actor)
                    {
                        drawProjectedHandle(candidate.worldPosition, IM_COL32(255, 96, 96, alpha), selected, false);
                    }
                    else
                    {
                        const Game::IndoorSpawn &spawn = indoorGeometry.spawns[candidate.selectionIndex];
                        drawProjectedHandle(
                            candidate.worldPosition,
                            spawn.typeId == 3 ? IM_COL32(255, 96, 220, alpha) : IM_COL32(96, 144, 255, alpha),
                            selected,
                            false);
                    }
                    continue;
                }

                if (candidate.selectionKind == EditorSelectionKind::Door)
                {
                    if (candidate.selectionIndex >= sceneData.initialState.doors.size())
                    {
                        continue;
                    }

                    drawProjectedHandle(candidate.worldPosition, IM_COL32(96, 255, 180, alpha), selected, false);
                    continue;
                }

                if (candidate.selectionKind == EditorSelectionKind::SpriteObject)
                {
                    if (candidate.selectionIndex >= sceneData.initialState.spriteObjects.size())
                    {
                        continue;
                    }

                    drawProjectedHandle(candidate.worldPosition, IM_COL32(64, 216, 208, alpha), selected, false);
                }
            }

            const EditorSelection selection = session.selection();
            const bool movableIndoorSelection =
                selection.kind == EditorSelectionKind::Entity
                || selection.kind == EditorSelectionKind::Actor
                || selection.kind == EditorSelectionKind::Spawn
                || selection.kind == EditorSelectionKind::SpriteObject
                || selection.kind == EditorSelectionKind::Light;

            if (movableIndoorSelection && m_transformGizmoMode == TransformGizmoMode::Translate)
            {
                const std::optional<bx::Vec3> selectedPosition =
                    selectedWorldPosition(session.document(), selection);

                if (selectedPosition)
                {
                    bx::Vec3 xAxisWorld = {1.0f, 0.0f, 0.0f};
                    bx::Vec3 yAxisWorld = {0.0f, 1.0f, 0.0f};
                    bx::Vec3 zAxisWorld = {0.0f, 0.0f, 1.0f};
                    computeTransformBasis(
                        session.document(),
                        selection,
                        m_transformSpaceMode,
                        xAxisWorld,
                        yAxisWorld,
                        zAxisWorld);

                    const bx::Vec3 xAxisEnd =
                        vecAdd(*selectedPosition, vecScale(xAxisWorld, IndoorGizmoAxisWorldLength));
                    const bx::Vec3 yAxisEnd =
                        vecAdd(*selectedPosition, vecScale(yAxisWorld, IndoorGizmoAxisWorldLength));
                    const bx::Vec3 zAxisEnd =
                        vecAdd(*selectedPosition, vecScale(zAxisWorld, IndoorGizmoAxisWorldLength));
                    ImVec2 origin = {};
                    ImVec2 xEnd = {};
                    ImVec2 yEnd = {};
                    ImVec2 zEnd = {};
                    const auto screenAxisEnd =
                        [&projectToOverlay, &origin](const bx::Vec3 &worldEnd, float fallbackX, float fallbackY)
                    {
                        ImVec2 projectedEnd = {};
                        float directionX = fallbackX;
                        float directionY = fallbackY;

                        if (projectToOverlay(worldEnd, projectedEnd))
                        {
                            const float deltaX = projectedEnd.x - origin.x;
                            const float deltaY = projectedEnd.y - origin.y;
                            const float length = std::sqrt(deltaX * deltaX + deltaY * deltaY);

                            if (length >= 8.0f)
                            {
                                directionX = deltaX / length;
                                directionY = deltaY / length;
                            }
                        }

                        return ImVec2{
                            origin.x + directionX * IndoorGizmoScreenAxisLength,
                            origin.y + directionY * IndoorGizmoScreenAxisLength
                        };
                    };

                    if (projectToOverlay(*selectedPosition, origin))
                    {
                        xEnd = screenAxisEnd(xAxisEnd, 1.0f, 0.0f);
                        yEnd = screenAxisEnd(yAxisEnd, 0.0f, 1.0f);
                        zEnd = screenAxisEnd(zAxisEnd, 0.0f, -1.0f);
                        drawTranslateAxisOverlay(pDrawList, origin, xEnd, IM_COL32(255, 96, 96, 255), "X");
                        drawTranslateAxisOverlay(pDrawList, origin, yEnd, IM_COL32(96, 255, 96, 255), "Y");
                        drawTranslateAxisOverlay(pDrawList, origin, zEnd, IM_COL32(96, 160, 255, 255), "Z");
                    }
                }
            }
        }

        return;
    }

    {
        ImDrawList *pDrawList = ImGui::GetForegroundDrawList();
        const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();
        const auto outdoorHandleVisualScale =
            [this](const bx::Vec3 &center)
        {
            const float distance = std::sqrt(
                squaredLength2(center.x - m_cameraPosition.x, center.y - m_cameraPosition.y)
                + (center.z - m_cameraPosition.z) * (center.z - m_cameraPosition.z));

            if (distance <= 3000.0f)
            {
                return 1.0f;
            }

            if (distance >= 18000.0f)
            {
                return 0.38f;
            }

            const float t = (distance - 3000.0f) / 15000.0f;
            return std::lerp(1.0f, 0.38f, std::clamp(t, 0.0f, 1.0f));
        };
        const auto outdoorHandleVisualAlpha =
            [this](const bx::Vec3 &center)
        {
            const float distance = std::sqrt(
                squaredLength2(center.x - m_cameraPosition.x, center.y - m_cameraPosition.y)
                + (center.z - m_cameraPosition.z) * (center.z - m_cameraPosition.z));

            if (distance <= 3000.0f)
            {
                return uint8_t(255);
            }

            if (distance >= 18000.0f)
            {
                return uint8_t(108);
            }

            const float t = (distance - 3000.0f) / 15000.0f;
            return static_cast<uint8_t>(std::lround(std::lerp(255.0f, 108.0f, std::clamp(t, 0.0f, 1.0f))));
        };
        const auto outdoorHandleRelevantForCurrentMode =
            [this](EditorSelectionKind kind)
        {
            if (m_placementKind == kind)
            {
                return true;
            }

            if (m_placementKind == EditorSelectionKind::None)
            {
                return kind == EditorSelectionKind::BModel
                    || kind == EditorSelectionKind::Entity
                    || kind == EditorSelectionKind::Spawn
                    || kind == EditorSelectionKind::Actor
                    || kind == EditorSelectionKind::SpriteObject
                    || kind == EditorSelectionKind::ModelInstance
                    || kind == EditorSelectionKind::Mm9ScriptedObject
                    || kind == EditorSelectionKind::Mm9Mechanism;
            }

            return false;
        };
        const auto drawProjectedHandle =
            [this, pDrawList](
                const bx::Vec3 &center,
                ImU32 color,
                bool selected,
                bool lightBulb,
                float scale)
        {
            float screenX = 0.0f;
            float screenY = 0.0f;
            float clipW = 0.0f;

            if (!projectWorldPoint(
                    center,
                    m_viewProjectionMatrix,
                    m_viewportWidth,
                    m_viewportHeight,
                    screenX,
                    screenY,
                    clipW))
            {
                return;
            }

            const ImVec2 handleCenter = {
                static_cast<float>(m_viewportX) + screenX,
                static_cast<float>(m_viewportY) + screenY};
            const float radius = std::max(4.0f, (selected ? 12.0f : 10.0f) * scale);

            if (!selected && radius <= 5.5f)
            {
                const float halfExtent = std::max(2.0f, radius * 0.5f);
                pDrawList->AddRectFilled(
                    {handleCenter.x - halfExtent - 1.0f, handleCenter.y - halfExtent - 1.0f},
                    {handleCenter.x + halfExtent + 1.0f, handleCenter.y + halfExtent + 1.0f},
                    IM_COL32(0, 0, 0, 112),
                    2.0f);
                pDrawList->AddRectFilled(
                    {handleCenter.x - halfExtent, handleCenter.y - halfExtent},
                    {handleCenter.x + halfExtent, handleCenter.y + halfExtent},
                    color,
                    2.0f);
                return;
            }

            if (lightBulb)
            {
                drawLightBulbCenterHandle(pDrawList, handleCenter, radius, color, selected);
                return;
            }

            drawEditorCenterHandle(pDrawList, handleCenter, radius, color, selected);
        };
        const bx::Vec3 forward = vecNormalize({
            std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
            std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
            std::sin(m_cameraPitchRadians)
        });
        const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
        const bx::Vec3 cameraRight = vecNormalize(vecCross(forward, worldUp));
        const bx::Vec3 cameraUp = vecNormalize(vecCross(cameraRight, forward));
        const auto drawBillboardEventOverlay =
            [this, pDrawList, cameraRight, cameraUp](
                const MarkerCandidate &candidate,
                ImU32 fillColor,
                ImU32 borderColor)
        {
            if (!candidate.hasBillboardBounds || !candidate.hasEventOverlay)
            {
                return;
            }

            const float halfWidth = candidate.billboardWorldWidth * 0.5f;
            const float halfHeight = candidate.billboardWorldHeight * 0.5f;
            const bx::Vec3 right = vecScale(cameraRight, halfWidth);
            const bx::Vec3 up = vecScale(cameraUp, halfHeight);
            const std::array<bx::Vec3, 4> corners = {{
                {
                    candidate.worldPosition.x - right.x - up.x,
                    candidate.worldPosition.y - right.y - up.y,
                    candidate.worldPosition.z - right.z - up.z
                },
                {
                    candidate.worldPosition.x - right.x + up.x,
                    candidate.worldPosition.y - right.y + up.y,
                    candidate.worldPosition.z - right.z + up.z
                },
                {
                    candidate.worldPosition.x + right.x + up.x,
                    candidate.worldPosition.y + right.y + up.y,
                    candidate.worldPosition.z + right.z + up.z
                },
                {
                    candidate.worldPosition.x + right.x - up.x,
                    candidate.worldPosition.y + right.y - up.y,
                    candidate.worldPosition.z + right.z - up.z
                }
            }};

            ImVec2 projectedCorners[4] = {};

            for (size_t cornerIndex = 0; cornerIndex < 4; ++cornerIndex)
            {
                float screenX = 0.0f;
                float screenY = 0.0f;
                float clipW = 0.0f;

                if (!projectWorldPoint(
                        corners[cornerIndex],
                        m_viewProjectionMatrix,
                        m_viewportWidth,
                        m_viewportHeight,
                        screenX,
                        screenY,
                        clipW))
                {
                    return;
                }

                projectedCorners[cornerIndex] = {
                    static_cast<float>(m_viewportX) + screenX,
                    static_cast<float>(m_viewportY) + screenY};
            }

            pDrawList->AddConvexPolyFilled(projectedCorners, 4, fillColor);
            pDrawList->AddPolyline(projectedCorners, 4, borderColor, ImDrawFlags_Closed, 1.5f);
        };

        for (const MarkerCandidate &candidate : m_markerCandidates)
        {
            const bool selected = session.selection().kind == candidate.selectionKind
                && session.selection().index == candidate.selectionIndex;
            const bool emphasized = selected || outdoorHandleRelevantForCurrentMode(candidate.selectionKind);
            float scale = outdoorHandleVisualScale(candidate.worldPosition);
            uint8_t alpha = outdoorHandleVisualAlpha(candidate.worldPosition);

            if (!emphasized)
            {
                scale *= 0.82f;
                alpha = static_cast<uint8_t>(std::max(48, static_cast<int>(alpha) * 55 / 100));
            }

            if (candidate.blockedByLineOfSight && !selected)
            {
                alpha = static_cast<uint8_t>(std::min(static_cast<int>(alpha), 96));
            }

            if (selected)
            {
                scale = std::max(scale, 1.0f);
                alpha = 255;
            }

            if (m_showEventMarkers && candidate.selectionKind == EditorSelectionKind::Entity && candidate.hasEventOverlay)
            {
                const bool hintOnly = candidate.hintOnlyEventOverlay;
                const uint8_t fillAlpha = static_cast<uint8_t>(std::max(
                    hintOnly ? 28 : 34,
                    static_cast<int>(alpha) * (hintOnly ? 24 : 32) / 100));
                const uint8_t borderAlpha = static_cast<uint8_t>(std::max(
                    hintOnly ? 92 : 112,
                    static_cast<int>(alpha) * (hintOnly ? 48 : 60) / 100));
                drawBillboardEventOverlay(
                    candidate,
                    hintOnly ? IM_COL32(112, 220, 208, fillAlpha) : IM_COL32(72, 220, 208, fillAlpha),
                    hintOnly ? IM_COL32(112, 220, 208, borderAlpha) : IM_COL32(72, 220, 208, borderAlpha));
            }

            if (candidate.selectionKind == EditorSelectionKind::Entity)
            {
                drawProjectedHandle(candidate.worldPosition, IM_COL32(255, 214, 96, alpha), selected, false, scale);
                continue;
            }

            if (candidate.selectionKind == EditorSelectionKind::BModel)
            {
                drawProjectedHandle(candidate.worldPosition, IM_COL32(208, 112, 255, alpha), selected, false, scale);
                continue;
            }

            if (candidate.selectionKind == EditorSelectionKind::ModelInstance)
            {
                drawProjectedHandle(candidate.worldPosition, IM_COL32(64, 224, 216, alpha), selected, false, scale);
                continue;
            }

            if (candidate.selectionKind == EditorSelectionKind::Mm9ScriptedObject)
            {
                drawProjectedHandle(candidate.worldPosition, IM_COL32(32, 238, 220, alpha), selected, false, scale);
                continue;
            }

            if (candidate.selectionKind == EditorSelectionKind::Mm9Mechanism)
            {
                const ImU32 mechanismHandleColor =
                    candidate.mm9MechanismPreviewable
                        ? IM_COL32(72, 255, 72, alpha)
                        : IM_COL32(214, 236, 72, alpha);
                drawProjectedHandle(candidate.worldPosition, mechanismHandleColor, selected, false, scale);
                continue;
            }

            if (candidate.selectionKind == EditorSelectionKind::Actor)
            {
                drawProjectedHandle(candidate.worldPosition, IM_COL32(255, 96, 96, alpha), selected, false, scale);
                continue;
            }

            if (candidate.selectionKind == EditorSelectionKind::Spawn)
            {
                if (candidate.selectionIndex >= sceneData.spawns.size())
                {
                    continue;
                }

                const Game::OutdoorSceneSpawn &spawn = sceneData.spawns[candidate.selectionIndex];
                drawProjectedHandle(
                    candidate.worldPosition,
                    spawn.spawn.typeId == 3 ? IM_COL32(255, 96, 220, alpha) : IM_COL32(96, 144, 255, alpha),
                    selected,
                    false,
                    scale);
                continue;
            }

            if (candidate.selectionKind == EditorSelectionKind::SpriteObject)
            {
                drawProjectedHandle(candidate.worldPosition, IM_COL32(64, 216, 208, alpha), selected, false, scale);
            }
        }

        const EditorSelection selection = session.selection();

        const bool useScreenSpaceTranslateGizmo =
            m_transformGizmoMode == TransformGizmoMode::Translate
            && (selection.kind == EditorSelectionKind::BModel
                || selection.kind == EditorSelectionKind::ModelInstance
                || selection.kind == EditorSelectionKind::Mm9ScriptedObject
                || isIndoorMovableSelectionKind(selection.kind));

        if (useScreenSpaceTranslateGizmo)
        {
            const std::optional<bx::Vec3> selectedPosition = selectedWorldPosition(session.document(), selection);

            if (selectedPosition)
            {
                const auto projectToOverlay =
                    [this](const bx::Vec3 &point, ImVec2 &screenPoint)
                {
                    float screenX = 0.0f;
                    float screenY = 0.0f;
                    float clipW = 0.0f;

                    if (!projectWorldPoint(
                            point,
                            m_viewProjectionMatrix,
                            m_viewportWidth,
                            m_viewportHeight,
                            screenX,
                            screenY,
                            clipW))
                    {
                        return false;
                    }

                    screenPoint = {
                        static_cast<float>(m_viewportX) + screenX,
                        static_cast<float>(m_viewportY) + screenY
                    };
                    return true;
                };

                bx::Vec3 xAxisWorld = {1.0f, 0.0f, 0.0f};
                bx::Vec3 yAxisWorld = {0.0f, 1.0f, 0.0f};
                bx::Vec3 zAxisWorld = {0.0f, 0.0f, 1.0f};
                computeTransformBasis(
                    session.document(),
                    selection,
                    m_transformSpaceMode,
                    xAxisWorld,
                    yAxisWorld,
                    zAxisWorld);

                const bx::Vec3 xAxisEnd =
                    vecAdd(*selectedPosition, vecScale(xAxisWorld, IndoorGizmoAxisWorldLength));
                const bx::Vec3 yAxisEnd =
                    vecAdd(*selectedPosition, vecScale(yAxisWorld, IndoorGizmoAxisWorldLength));
                const bx::Vec3 zAxisEnd =
                    vecAdd(*selectedPosition, vecScale(zAxisWorld, IndoorGizmoAxisWorldLength));
                ImVec2 origin = {};
                ImVec2 xEnd = {};
                ImVec2 yEnd = {};
                ImVec2 zEnd = {};
                const auto screenAxisEnd =
                    [&projectToOverlay, &origin](const bx::Vec3 &worldEnd, float fallbackX, float fallbackY)
                {
                    ImVec2 projectedEnd = {};
                    float directionX = fallbackX;
                    float directionY = fallbackY;

                    if (projectToOverlay(worldEnd, projectedEnd))
                    {
                        const float deltaX = projectedEnd.x - origin.x;
                        const float deltaY = projectedEnd.y - origin.y;
                        const float length = std::sqrt(deltaX * deltaX + deltaY * deltaY);

                        if (length >= 8.0f)
                        {
                            directionX = deltaX / length;
                            directionY = deltaY / length;
                        }
                    }

                    return ImVec2{
                        origin.x + directionX * IndoorGizmoScreenAxisLength,
                        origin.y + directionY * IndoorGizmoScreenAxisLength
                    };
                };

                if (projectToOverlay(*selectedPosition, origin))
                {
                    xEnd = screenAxisEnd(xAxisEnd, 1.0f, 0.0f);
                    yEnd = screenAxisEnd(yAxisEnd, 0.0f, 1.0f);
                    zEnd = screenAxisEnd(zAxisEnd, 0.0f, -1.0f);
                    drawTranslateAxisOverlay(pDrawList, origin, xEnd, IM_COL32(255, 96, 96, 255), "X");
                    drawTranslateAxisOverlay(pDrawList, origin, yEnd, IM_COL32(96, 255, 96, 255), "Y");
                    drawTranslateAxisOverlay(pDrawList, origin, zEnd, IM_COL32(96, 160, 255, 255), "Z");
                }
            }
        }
    }

    std::string modeLabel = placementKindLabel(m_placementKind);

    if (m_placementKind == EditorSelectionKind::Terrain)
    {
        modeLabel += session.terrainSculptEnabled() ? " / SCULPT" : " / PAINT";
    }
    else if (m_placementKind == EditorSelectionKind::BModel)
    {
        modeLabel = "BMODEL PLACE";
    }
    else if (m_placementKind == EditorSelectionKind::Entity)
    {
        modeLabel = "ENTITY PLACE";
    }
    else if (m_placementKind == EditorSelectionKind::Spawn)
    {
        modeLabel = "SPAWN PLACE";
    }
    else if (m_placementKind == EditorSelectionKind::Actor)
    {
        modeLabel = "ACTOR PLACE";
    }
    else if (m_placementKind == EditorSelectionKind::SpriteObject)
    {
        modeLabel = "OBJECT PLACE";
    }

    ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.95f, 0.87f, 0.76f, 1.0f));
    ImGui::Text(
        "%s  ·  %s  ·  %s",
        modeLabel.c_str(),
        m_transformGizmoMode == TransformGizmoMode::Rotate ? "Rotate" : "Move",
        m_transformSpaceMode == TransformSpaceMode::Local ? "Local" : "World");
    ImGui::PopStyleColor();

    if (m_placementKind == EditorSelectionKind::Terrain)
    {
        ImGui::TextDisabled(
            "%s",
            session.terrainSculptEnabled()
                ? "LMB sculpt  ·  drag  ·  Alt+LMB sample"
                : (session.terrainPaintEnabled() ? "LMB paint  ·  drag" : "LMB select cell  ·  Esc select"));
    }
    else
    {
        ImGui::TextDisabled(
            "%s",
            m_placementKind == EditorSelectionKind::BModel
                ? "Move cursor  ·  LMB place  ·  Esc cancel"
                : "RMB look  ·  WASD move  ·  F frame");
    }

    if (m_placementKind == EditorSelectionKind::Terrain)
    {
        if (session.terrainSculptEnabled())
        {
            const char *pFalloffLabel = "Linear";

            switch (session.terrainSculptFalloffMode())
            {
            case EditorTerrainFalloffMode::Flat:
                pFalloffLabel = "Flat";
                break;

            case EditorTerrainFalloffMode::Smooth:
                pFalloffLabel = "Smooth";
                break;

            case EditorTerrainFalloffMode::Linear:
            default:
                break;
            }

            ImGui::Text(
                "%s  ·  R %d  ·  S %d  ·  %s",
                session.terrainSculptMode() == EditorTerrainSculptMode::Lower
                    ? "lower"
                    : session.terrainSculptMode() == EditorTerrainSculptMode::Flatten
                        ? "flatten"
                        : session.terrainSculptMode() == EditorTerrainSculptMode::Smooth
                            ? "smooth"
                            : session.terrainSculptMode() == EditorTerrainSculptMode::Noise
                                ? "noise"
                                : session.terrainSculptMode() == EditorTerrainSculptMode::Ramp ? "ramp" : "raise",
                session.terrainSculptRadius(),
                session.terrainSculptStrength(),
                pFalloffLabel);
        }
        else
        {
            const char *pPaintModeLabel = "Brush";

            switch (session.terrainPaintMode())
            {
            case EditorTerrainPaintMode::Rectangle:
                pPaintModeLabel = "Rectangle";
                break;

            case EditorTerrainPaintMode::Fill:
                pPaintModeLabel = "Fill";
                break;

            case EditorTerrainPaintMode::Brush:
            default:
                break;
            }

            if (session.terrainPaintMode() == EditorTerrainPaintMode::Brush)
            {
                ImGui::Text(
                    "%s  ·  Tile %u  ·  R %d  ·  Edge %d",
                    pPaintModeLabel,
                    static_cast<unsigned>(session.terrainPaintTileId()),
                    session.terrainPaintRadius(),
                    session.terrainPaintEdgeNoise());
            }
            else
            {
                ImGui::Text(
                    "%s  ·  Tile %u  ·  R %d",
                    pPaintModeLabel,
                    static_cast<unsigned>(session.terrainPaintTileId()),
                    session.terrainPaintRadius());
            }
        }
    }
    else if (session.selection().kind == EditorSelectionKind::InteractiveFace)
    {
        const size_t selectedFaceCount =
            session.selectedInteractiveFaceIndices().empty() ? 1 : session.selectedInteractiveFaceIndices().size();
        ImGui::Text("Face selection  ·  %zu selected", selectedFaceCount);
    }
    else if (session.selection().kind == EditorSelectionKind::BModel)
    {
        ImGui::TextDisabled("Selected BModel %zu", session.selection().index);
    }
    else
    {
        ImGui::TextDisabled(
            "Preview %s%s",
            m_previewMaterialMode == PreviewMaterialMode::Clay
                ? "Clay"
                : m_previewMaterialMode == PreviewMaterialMode::Grid ? "Grid" : "Textured",
            m_forcePreviewOnSelectedOnly ? "  ·  Selected" : "");
    }
}

void EditorOutdoorViewport::setPlacementKind(EditorSelectionKind kind)
{
    m_placementKind = kind;

    if (kind != EditorSelectionKind::Entity)
    {
        m_pendingEntityPlacementPreview.reset();
    }

    if (kind != EditorSelectionKind::Actor)
    {
        m_pendingActorPlacementPreview.reset();
    }

    if (kind != EditorSelectionKind::Spawn)
    {
        m_pendingSpawnPlacementPreview.reset();
    }

    if (kind != EditorSelectionKind::SpriteObject)
    {
        m_pendingSpriteObjectPlacementPreview.reset();
    }
}

EditorSelectionKind EditorOutdoorViewport::placementKind() const
{
    return m_placementKind;
}

bool EditorOutdoorViewport::snapEnabled() const
{
    return m_snapEnabled;
}

void EditorOutdoorViewport::setSnapEnabled(bool enabled)
{
    m_snapEnabled = enabled;
}

int EditorOutdoorViewport::snapStep() const
{
    return m_snapStep;
}

void EditorOutdoorViewport::setSnapStep(int step)
{
    m_snapStep = std::max(step, 1);
}

bool EditorOutdoorViewport::showTerrainFill() const
{
    return m_showTerrainFill;
}

void EditorOutdoorViewport::setShowTerrainFill(bool enabled)
{
    m_showTerrainFill = enabled;
}

bool EditorOutdoorViewport::showTerrainGrid() const
{
    return m_showTerrainGrid;
}

void EditorOutdoorViewport::setShowTerrainGrid(bool enabled)
{
    m_showTerrainGrid = enabled;
}

EditorOutdoorViewport::PreviewMaterialMode EditorOutdoorViewport::previewMaterialMode() const
{
    return m_previewMaterialMode;
}

void EditorOutdoorViewport::setPreviewMaterialMode(PreviewMaterialMode mode)
{
    m_previewMaterialMode = mode;
}

bool EditorOutdoorViewport::forcePreviewOnSelectedOnly() const
{
    return m_forcePreviewOnSelectedOnly;
}

void EditorOutdoorViewport::setForcePreviewOnSelectedOnly(bool enabled)
{
    m_forcePreviewOnSelectedOnly = enabled;
}

bool EditorOutdoorViewport::showBModels() const
{
    return m_showBModels;
}

void EditorOutdoorViewport::setShowBModels(bool enabled)
{
    m_showBModels = enabled;
}

EditorOutdoorViewport::Mm9DatWorldRenderSubset EditorOutdoorViewport::mm9DatWorldRenderSubset() const
{
    return m_mm9DatWorldRenderSubset;
}

void EditorOutdoorViewport::setMm9DatWorldRenderSubset(Mm9DatWorldRenderSubset subset)
{
    if (m_mm9DatWorldRenderSubset == subset)
    {
        return;
    }

    m_mm9DatWorldRenderSubset = subset;
    m_geometryKey.clear();
}

bool EditorOutdoorViewport::showModelInstances() const
{
    return m_showModelInstances;
}

void EditorOutdoorViewport::setShowModelInstances(bool enabled)
{
    m_showModelInstances = enabled;
}

bool EditorOutdoorViewport::showMm9DatPortals() const
{
    return m_showMm9DatPortals;
}

void EditorOutdoorViewport::setShowMm9DatPortals(bool enabled)
{
    m_showMm9DatPortals = enabled;
}

bool EditorOutdoorViewport::showMm9WorldModelBounds() const
{
    return m_showMm9WorldModelBounds;
}

void EditorOutdoorViewport::setShowMm9WorldModelBounds(bool enabled)
{
    m_showMm9WorldModelBounds = enabled;
}

bool EditorOutdoorViewport::showMm9ObjectBounds() const
{
    return m_showMm9ObjectBounds;
}

void EditorOutdoorViewport::setShowMm9ObjectBounds(bool enabled)
{
    m_showMm9ObjectBounds = enabled;
}

bool EditorOutdoorViewport::showMm9AssetIssueMarkers() const
{
    return m_showMm9AssetIssueMarkers;
}

void EditorOutdoorViewport::setShowMm9AssetIssueMarkers(bool enabled)
{
    m_showMm9AssetIssueMarkers = enabled;
}

bool EditorOutdoorViewport::showIndoorPortals() const
{
    return m_showIndoorPortals;
}

void EditorOutdoorViewport::setShowIndoorPortals(bool enabled)
{
    m_showIndoorPortals = enabled;
}

bool EditorOutdoorViewport::showIndoorFloors() const
{
    return m_showIndoorFloors;
}

void EditorOutdoorViewport::setShowIndoorFloors(bool enabled)
{
    if (m_showIndoorFloors == enabled)
    {
        return;
    }

    m_showIndoorFloors = enabled;
    m_indoorPreviewGeometryBuffersDirty = true;
}

bool EditorOutdoorViewport::showIndoorCeilings() const
{
    return m_showIndoorCeilings;
}

void EditorOutdoorViewport::setShowIndoorCeilings(bool enabled)
{
    if (m_showIndoorCeilings == enabled)
    {
        return;
    }

    m_showIndoorCeilings = enabled;
    m_indoorPreviewGeometryBuffersDirty = true;
}

bool EditorOutdoorViewport::showIndoorGizmosEverywhere() const
{
    return m_showIndoorGizmosEverywhere;
}

void EditorOutdoorViewport::setShowIndoorGizmosEverywhere(bool enabled)
{
    m_showIndoorGizmosEverywhere = enabled;
}

std::optional<uint16_t> EditorOutdoorViewport::isolatedIndoorRoomId() const
{
    return m_isolatedIndoorRoomId;
}

void EditorOutdoorViewport::setIsolatedIndoorRoomId(std::optional<uint16_t> roomId)
{
    if (m_isolatedIndoorRoomId == roomId)
    {
        return;
    }

    m_isolatedIndoorRoomId = roomId;
    m_indoorPreviewGeometryBuffersDirty = true;
}

bool EditorOutdoorViewport::showBModelWireframe() const
{
    return m_showBModelWireframe;
}

void EditorOutdoorViewport::setShowBModelWireframe(bool enabled)
{
    m_showBModelWireframe = enabled;
}

const EditorOutdoorViewport::RenderSubmissionStats &EditorOutdoorViewport::lastRenderSubmissionStats() const
{
    return m_lastRenderSubmissionStats;
}

bool EditorOutdoorViewport::showEntities() const
{
    return m_showEntities;
}

void EditorOutdoorViewport::setShowEntities(bool enabled)
{
    m_showEntities = enabled;
}

bool EditorOutdoorViewport::showEntityBillboards() const
{
    return m_showEntityBillboards;
}

void EditorOutdoorViewport::setShowEntityBillboards(bool enabled)
{
    m_showEntityBillboards = enabled;
}

bool EditorOutdoorViewport::showSpawns() const
{
    return m_showSpawns;
}

void EditorOutdoorViewport::setShowSpawns(bool enabled)
{
    m_showSpawns = enabled;
}

bool EditorOutdoorViewport::showActors() const
{
    return m_showActors;
}

void EditorOutdoorViewport::setShowActors(bool enabled)
{
    m_showActors = enabled;
}

bool EditorOutdoorViewport::showActorBillboards() const
{
    return m_showActorBillboards;
}

void EditorOutdoorViewport::setShowActorBillboards(bool enabled)
{
    m_showActorBillboards = enabled;
}

bool EditorOutdoorViewport::showSpriteObjects() const
{
    return m_showSpriteObjects;
}

void EditorOutdoorViewport::setShowSpriteObjects(bool enabled)
{
    m_showSpriteObjects = enabled;
}

bool EditorOutdoorViewport::showSpawnActorBillboards() const
{
    return m_showSpawnActorBillboards;
}

void EditorOutdoorViewport::setShowSpawnActorBillboards(bool enabled)
{
    m_showSpawnActorBillboards = enabled;
}

bool EditorOutdoorViewport::showEventMarkers() const
{
    return m_showEventMarkers;
}

void EditorOutdoorViewport::setShowEventMarkers(bool enabled)
{
    m_showEventMarkers = enabled;
}

bool EditorOutdoorViewport::showChestLinks() const
{
    return m_showChestLinks;
}

void EditorOutdoorViewport::setShowChestLinks(bool enabled)
{
    m_showChestLinks = enabled;
}

void EditorOutdoorViewport::setImportedModelPreviewRequest(
    const std::optional<ImportedModelPreviewRequest> &request)
{
    m_importedModelPreviewRequest = request;

    if (!m_importedModelPreviewRequest)
    {
        destroyImportedModelPreview();
    }
}

EditorOutdoorViewport::TransformGizmoMode EditorOutdoorViewport::transformGizmoMode() const
{
    return m_transformGizmoMode;
}

void EditorOutdoorViewport::setTransformGizmoMode(TransformGizmoMode mode)
{
    m_transformGizmoMode = mode;
}

EditorOutdoorViewport::TransformSpaceMode EditorOutdoorViewport::transformSpaceMode() const
{
    return m_transformSpaceMode;
}

void EditorOutdoorViewport::setTransformSpaceMode(TransformSpaceMode mode)
{
    m_transformSpaceMode = mode;
}

void EditorOutdoorViewport::focusSelection(const EditorDocument &document, const EditorSelection &selection)
{
    const std::optional<bx::Vec3> focusPoint = selectedWorldPosition(document, selection);

    if (!focusPoint)
    {
        return;
    }

    const float focusDistance = 3072.0f;
    const bx::Vec3 targetPosition = {
        focusPoint->x - focusDistance * 0.45f,
        focusPoint->y - focusDistance * 0.95f,
        focusPoint->z + focusDistance * 0.40f
    };
    const bx::Vec3 toFocus = {
        focusPoint->x - targetPosition.x,
        focusPoint->y - targetPosition.y,
        focusPoint->z - targetPosition.z
    };
    const float planarLength = std::sqrt(toFocus.x * toFocus.x + toFocus.y * toFocus.y);
    const float targetYawRadians = std::atan2(toFocus.x, toFocus.y);
    const float targetPitchRadians = std::atan2(toFocus.z, std::max(planarLength, 0.001f));

    m_activeCameraFocus.active = true;
    m_activeCameraFocus.startPosition = m_cameraPosition;
    m_activeCameraFocus.targetPosition = targetPosition;
    m_activeCameraFocus.startYawRadians = m_cameraYawRadians;
    m_activeCameraFocus.targetYawRadians = targetYawRadians;
    m_activeCameraFocus.startPitchRadians = m_cameraPitchRadians;
    m_activeCameraFocus.targetPitchRadians = std::clamp(
        targetPitchRadians,
        CameraMinPitchRadians,
        CameraMaxPitchRadians);
    m_activeCameraFocus.progressSeconds = 0.0f;
    m_activeCameraFocus.durationSeconds = CameraFocusDurationSeconds;
}

void EditorOutdoorViewport::focusBModel(const EditorDocument &document, size_t bmodelIndex)
{
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    if (bmodelIndex >= outdoorGeometry.bmodels.size())
    {
        return;
    }

    const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float x = static_cast<float>(vertex.x);
        const float y = static_cast<float>(vertex.y);
        const float z = static_cast<float>(vertex.z);
        minX = std::min(minX, x);
        minY = std::min(minY, y);
        minZ = std::min(minZ, z);
        maxX = std::max(maxX, x);
        maxY = std::max(maxY, y);
        maxZ = std::max(maxZ, z);
    }

    if (!std::isfinite(minX) || !std::isfinite(maxX))
    {
        return;
    }

    const bx::Vec3 focusPoint = {
        (minX + maxX) * 0.5f,
        (minY + maxY) * 0.5f,
        (minZ + maxZ) * 0.5f
    };
    const float extentX = maxX - minX;
    const float extentY = maxY - minY;
    const float extentZ = maxZ - minZ;
    const float extent = std::max({extentX, extentY, extentZ, static_cast<float>(bmodel.boundingRadius)});
    const float focusDistance = std::max(extent * 2.2f, 3072.0f);
    const bx::Vec3 targetPosition = {
        focusPoint.x - focusDistance * 0.45f,
        focusPoint.y - focusDistance * 0.95f,
        focusPoint.z + focusDistance * 0.40f
    };
    const bx::Vec3 toFocus = {
        focusPoint.x - targetPosition.x,
        focusPoint.y - targetPosition.y,
        focusPoint.z - targetPosition.z
    };
    const float planarLength = std::sqrt(toFocus.x * toFocus.x + toFocus.y * toFocus.y);
    const float targetYawRadians = std::atan2(toFocus.x, toFocus.y);
    const float targetPitchRadians = std::atan2(toFocus.z, std::max(planarLength, 0.001f));

    m_activeCameraFocus.active = true;
    m_activeCameraFocus.startPosition = m_cameraPosition;
    m_activeCameraFocus.targetPosition = targetPosition;
    m_activeCameraFocus.startYawRadians = m_cameraYawRadians;
    m_activeCameraFocus.targetYawRadians = targetYawRadians;
    m_activeCameraFocus.startPitchRadians = m_cameraPitchRadians;
    m_activeCameraFocus.targetPitchRadians = std::clamp(
        targetPitchRadians,
        CameraMinPitchRadians,
        CameraMaxPitchRadians);
    m_activeCameraFocus.progressSeconds = 0.0f;
    m_activeCameraFocus.durationSeconds = CameraFocusDurationSeconds;
}

void EditorOutdoorViewport::previewIndoorMechanismOpen(const EditorDocument &document, size_t doorIndex)
{
    ensureIndoorMechanismPreviewDocument(document);

    if (document.kind() != EditorDocument::Kind::Indoor
        || doorIndex >= document.indoorSceneData().initialState.doors.size())
    {
        return;
    }

    Game::RuntimeMechanismState previewState = {};
    previewState.state = static_cast<uint16_t>(Game::EvtMechanismState::Open);
    previewState.currentDistance = 0.0f;
    previewState.isMoving = false;
    m_indoorMechanismPreviewOverrides[doorIndex] = previewState;
    invalidateIndoorMechanismPreview();
}

void EditorOutdoorViewport::previewIndoorMechanismClose(const EditorDocument &document, size_t doorIndex)
{
    ensureIndoorMechanismPreviewDocument(document);

    if (document.kind() != EditorDocument::Kind::Indoor
        || doorIndex >= document.indoorSceneData().initialState.doors.size())
    {
        return;
    }

    const Game::MapDeltaDoor &door = document.indoorSceneData().initialState.doors[doorIndex].door;
    Game::RuntimeMechanismState previewState = {};
    previewState.state = static_cast<uint16_t>(Game::EvtMechanismState::Closed);
    previewState.currentDistance = static_cast<float>(door.moveLength);
    previewState.isMoving = false;
    m_indoorMechanismPreviewOverrides[doorIndex] = previewState;
    invalidateIndoorMechanismPreview();
}

void EditorOutdoorViewport::previewIndoorMechanismSimulate(const EditorDocument &document, size_t doorIndex)
{
    ensureIndoorMechanismPreviewDocument(document);

    if (document.kind() != EditorDocument::Kind::Indoor
        || doorIndex >= document.indoorSceneData().initialState.doors.size())
    {
        return;
    }

    const Game::MapDeltaDoor &door = document.indoorSceneData().initialState.doors[doorIndex].door;
    const auto previewIterator = m_indoorMechanismPreviewOverrides.find(doorIndex);
    Game::RuntimeMechanismState previewState =
        previewIterator != m_indoorMechanismPreviewOverrides.end()
            ? previewIterator->second
            : buildMechanismPreviewState(door);

    if (previewState.state == static_cast<uint16_t>(Game::EvtMechanismState::Closed)
        || previewState.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing))
    {
        if (door.openSpeed == 0 || door.moveLength == 0)
        {
            previewIndoorMechanismOpen(document, doorIndex);
            return;
        }

        const float openDistance =
            std::max(0.0f, static_cast<float>(door.moveLength) - previewState.currentDistance);
        previewState.timeSinceTriggeredMs = openDistance * 1000.0f / static_cast<float>(door.openSpeed);
        previewState.state = static_cast<uint16_t>(Game::EvtMechanismState::Opening);
        previewState.isMoving = previewState.currentDistance > 0.0f;
    }
    else
    {
        if (door.closeSpeed == 0 || door.moveLength == 0)
        {
            previewIndoorMechanismClose(document, doorIndex);
            return;
        }

        previewState.timeSinceTriggeredMs =
            previewState.currentDistance * 1000.0f / static_cast<float>(door.closeSpeed);
        previewState.state = static_cast<uint16_t>(Game::EvtMechanismState::Closing);
        previewState.isMoving = previewState.currentDistance < static_cast<float>(door.moveLength);
    }

    previewState.currentDistance = calculateMechanismPreviewDistance(door, previewState);
    m_indoorMechanismPreviewOverrides[doorIndex] = previewState;
    invalidateIndoorMechanismPreview();
}

void EditorOutdoorViewport::setMm9MechanismPreviewProgress(
    const EditorDocument &document,
    size_t mechanismIndex,
    float progress)
{
    ensureMm9MechanismPreviewDocument(document);

    if (document.kind() != EditorDocument::Kind::Mm9Dat
        || !document.hasMm9DatLoadedSidecars()
        || mechanismIndex >= document.mm9DatLoadedSidecars().events.mechanisms.size())
    {
        return;
    }

    const float clampedProgress = std::clamp(progress, 0.0f, 1.0f);
    const std::unordered_map<size_t, float>::const_iterator previewIt =
        m_mm9MechanismPreviewProgressByIndex.find(mechanismIndex);

    if (previewIt != m_mm9MechanismPreviewProgressByIndex.end()
        && std::fabs(previewIt->second - clampedProgress) <= 0.0001f)
    {
        return;
    }

    m_mm9MechanismPreviewProgressByIndex[mechanismIndex] = clampedProgress;
}

void EditorOutdoorViewport::clearMm9MechanismPreview(const EditorDocument &document)
{
    ensureMm9MechanismPreviewDocument(document);

    if (document.kind() != EditorDocument::Kind::Mm9Dat)
    {
        return;
    }

    if (m_mm9MechanismPreviewProgressByIndex.empty())
    {
        return;
    }

    m_mm9MechanismPreviewProgressByIndex.clear();
}

bool EditorOutdoorViewport::tryGetMm9MechanismPreviewProgress(
    const EditorDocument &document,
    size_t mechanismIndex,
    float &progress) const
{
    if (document.kind() != EditorDocument::Kind::Mm9Dat
        || !document.hasMm9DatLoadedSidecars()
        || mechanismIndex >= document.mm9DatLoadedSidecars().events.mechanisms.size())
    {
        return false;
    }

    ensureMm9MechanismPreviewDocument(document);

    const std::unordered_map<size_t, float>::const_iterator previewIt =
        m_mm9MechanismPreviewProgressByIndex.find(mechanismIndex);

    if (previewIt == m_mm9MechanismPreviewProgressByIndex.end())
    {
        progress = 0.0f;
        return false;
    }

    progress = previewIt->second;
    return true;
}

void EditorOutdoorViewport::setIndoorMechanismPreviewState(
    const EditorDocument &document,
    size_t doorIndex,
    const Game::RuntimeMechanismState &state)
{
    ensureIndoorMechanismPreviewDocument(document);

    if (document.kind() != EditorDocument::Kind::Indoor
        || doorIndex >= document.indoorSceneData().initialState.doors.size())
    {
        return;
    }

    m_indoorMechanismPreviewOverrides[doorIndex] = state;
    invalidateIndoorMechanismPreview();
}

void EditorOutdoorViewport::clearIndoorMechanismPreview(const EditorDocument &document)
{
    ensureIndoorMechanismPreviewDocument(document);

    if (document.kind() != EditorDocument::Kind::Indoor)
    {
        return;
    }

    if (m_indoorMechanismPreviewOverrides.empty())
    {
        return;
    }

    m_indoorMechanismPreviewOverrides.clear();
    invalidateIndoorMechanismPreview();
}

bool EditorOutdoorViewport::tryGetIndoorMechanismPreview(
    const EditorDocument &document,
    size_t doorIndex,
    uint16_t &state,
    float &timeSinceTriggeredMs,
    float &distance,
    bool &isMoving) const
{
    if (document.kind() != EditorDocument::Kind::Indoor
        || doorIndex >= document.indoorSceneData().initialState.doors.size())
    {
        return false;
    }

    ensureIndoorMechanismPreviewDocument(document);
    const Game::MapDeltaDoor &door = document.indoorSceneData().initialState.doors[doorIndex].door;
    const auto previewIterator = m_indoorMechanismPreviewOverrides.find(doorIndex);
    const Game::RuntimeMechanismState previewState =
        previewIterator != m_indoorMechanismPreviewOverrides.end()
            ? previewIterator->second
            : buildMechanismPreviewState(door);
    state = previewState.state;
    timeSinceTriggeredMs = previewState.timeSinceTriggeredMs;
    distance = previewState.currentDistance;
    isMoving = previewState.isMoving;
    return true;
}

void EditorOutdoorViewport::setIndoorDoorFaceEditMode(
    IndoorDoorFaceEditMode mode,
    std::optional<size_t> doorIndex)
{
    m_indoorDoorFaceEditMode = mode;
    m_indoorDoorFaceEditDoorIndex = mode == IndoorDoorFaceEditMode::None ? std::nullopt : doorIndex;
}

EditorOutdoorViewport::IndoorDoorFaceEditMode EditorOutdoorViewport::indoorDoorFaceEditMode() const
{
    return m_indoorDoorFaceEditMode;
}

std::optional<size_t> EditorOutdoorViewport::indoorDoorFaceEditDoorIndex() const
{
    return m_indoorDoorFaceEditDoorIndex;
}

void EditorOutdoorViewport::ensureIndoorMechanismPreviewDocument(const EditorDocument &document) const
{
    if (document.kind() != EditorDocument::Kind::Indoor)
    {
        return;
    }

    const std::string documentKey = documentCameraKey(document);

    if (documentKey == m_indoorMechanismPreviewDocumentKey)
    {
        return;
    }

    m_indoorMechanismPreviewDocumentKey = documentKey;
    m_indoorMechanismPreviewOverrides.clear();
    m_indoorRenderVerticesKey.clear();
    m_indoorRenderVertices.clear();
    m_indoorFaceGeometryCacheKey.clear();
    m_indoorMarkerVisibilityKey.clear();
    m_indoorMarkerLineOfSightBlockedByKey.clear();
    m_indoorActorFloorSnapKey.clear();
    m_indoorActorFloorSnapZByKey.clear();
    const_cast<EditorOutdoorViewport *>(this)->m_indoorMechanismPreviewAccumulatorSeconds = 0.0f;
    const_cast<EditorOutdoorViewport *>(this)->m_indoorPreviewGeometryBuffersDirty = false;
}

void EditorOutdoorViewport::ensureMm9MechanismPreviewDocument(const EditorDocument &document) const
{
    if (document.kind() != EditorDocument::Kind::Mm9Dat)
    {
        return;
    }

    const std::string documentKey = documentCameraKey(document);

    if (documentKey == m_mm9MechanismPreviewDocumentKey)
    {
        return;
    }

    m_mm9MechanismPreviewDocumentKey = documentKey;
    m_mm9MechanismPreviewProgressByIndex.clear();
    m_mm9MechanismPreviewCacheKey.clear();
    m_mm9MechanismPreviewCache.clear();
}

const std::vector<EditorOutdoorViewport::Mm9MechanismPreviewCacheEntry> &
EditorOutdoorViewport::mm9MechanismPreviewCache(const EditorDocument &document) const
{
    static const std::vector<Mm9MechanismPreviewCacheEntry> emptyCache;

    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        m_mm9MechanismPreviewCacheKey.clear();
        m_mm9MechanismPreviewCache.clear();
        return emptyCache;
    }

    const std::string cacheKey = documentGeometryKey(document);
    if (cacheKey == m_mm9MechanismPreviewCacheKey)
    {
        return m_mm9MechanismPreviewCache;
    }

    const EditorMm9DatWorldSidecar &datWorld = document.mm9DatLoadedSidecars().datWorld;
    const Game::Mm9EventsData &events = document.mm9DatLoadedSidecars().events;
    m_mm9MechanismPreviewCache.clear();
    m_mm9MechanismPreviewCache.resize(events.mechanisms.size());

    for (size_t mechanismIndex = 0; mechanismIndex < events.mechanisms.size(); ++mechanismIndex)
    {
        const Game::Mm9EventMechanism &mechanism = events.mechanisms[mechanismIndex];
        Mm9MechanismPreviewCacheEntry &cacheEntry = m_mm9MechanismPreviewCache[mechanismIndex];

        if (mechanism.sourceObjectIndex >= 0)
        {
            cacheEntry.sourceMarkerPosition =
                mm9SourceObjectMarkerPosition(document, static_cast<size_t>(mechanism.sourceObjectIndex));
        }

        const Game::Mm9EventBinding *pBinding =
            findMm9ViewportEventBindingForObject(events, mechanism.objectId);
        if (pBinding == nullptr)
        {
            continue;
        }

        cacheEntry.targets.reserve(pBinding->targets.size());

        for (const Game::Mm9EventBindingTarget &target : pBinding->targets)
        {
            if (target.targetKind != "odm_bmodel" || !target.bmodelIndex.has_value())
            {
                continue;
            }

            Game::Mm9DatMechanismPreviewMotion motion = {};
            const bool targetPreviewable = buildMm9ViewportPreviewMotion(mechanism, target, 1.0f, motion);
            cacheEntry.previewable = cacheEntry.previewable || targetPreviewable;

            bx::Vec3 center = {0.0f, 0.0f, 0.0f};
            bx::Vec3 halfExtents = {0.0f, 0.0f, 0.0f};
            if (!mm9DatWorldModelBounds(datWorld, *target.bmodelIndex, center, halfExtents))
            {
                continue;
            }

            Mm9MechanismPreviewTargetCache targetCache = {};
            targetCache.sourceModelIndex = *target.bmodelIndex;
            targetCache.center = center;
            targetCache.halfExtents = halfExtents;
            targetCache.previewable = targetPreviewable;
            targetCache.openMotion = motion;
            cacheEntry.targets.push_back(targetCache);
        }
    }

    m_mm9MechanismPreviewCacheKey = cacheKey;
    return m_mm9MechanismPreviewCache;
}

void EditorOutdoorViewport::advanceIndoorMechanismPreview(const EditorDocument &document, float deltaSeconds)
{
    ensureIndoorMechanismPreviewDocument(document);

    if (document.kind() != EditorDocument::Kind::Indoor
        || deltaSeconds <= 0.0f
        || m_indoorMechanismPreviewOverrides.empty())
    {
        return;
    }

    m_indoorMechanismPreviewAccumulatorSeconds += deltaSeconds;
    constexpr float PreviewTickSeconds = 1.0f / 60.0f;

    if (m_indoorMechanismPreviewAccumulatorSeconds < PreviewTickSeconds)
    {
        return;
    }

    float tickSeconds = 0.0f;
    int tickCount = 0;

    while (m_indoorMechanismPreviewAccumulatorSeconds >= PreviewTickSeconds && tickCount < 4)
    {
        m_indoorMechanismPreviewAccumulatorSeconds -= PreviewTickSeconds;
        tickSeconds += PreviewTickSeconds;
        ++tickCount;
    }

    const Game::IndoorSceneData &sceneData = document.indoorSceneData();
    bool changed = false;

    for (auto &[doorIndex, previewState] : m_indoorMechanismPreviewOverrides)
    {
        if (doorIndex >= sceneData.initialState.doors.size() || !previewState.isMoving)
        {
            continue;
        }

        const Game::MapDeltaDoor &door = sceneData.initialState.doors[doorIndex].door;
        const uint16_t previousState = previewState.state;
        const float previousDistance = previewState.currentDistance;
        const bool wasMoving = previewState.isMoving;
        advanceMechanismPreviewState(door, tickSeconds * 1000.0f, previewState);

        if (previewState.state != previousState
            || std::fabs(previewState.currentDistance - previousDistance) > 0.001f
            || previewState.isMoving != wasMoving)
        {
            changed = true;
        }
    }

    if (changed)
    {
        invalidateIndoorMechanismPreview();
    }
}

void EditorOutdoorViewport::invalidateIndoorMechanismPreview()
{
    ++m_indoorMechanismPreviewRevision;
    m_indoorRenderVerticesKey.clear();
    m_indoorFaceGeometryCacheKey.clear();
    m_indoorMarkerVisibilityKey.clear();
    m_indoorMarkerLineOfSightBlockedByKey.clear();
    m_indoorActorFloorSnapKey.clear();
    m_indoorActorFloorSnapZByKey.clear();
    m_indoorPreviewGeometryBuffersDirty = true;
}

const std::vector<Game::IndoorVertex> &EditorOutdoorViewport::indoorRenderVertices(const EditorDocument &document) const
{
    ensureIndoorMechanismPreviewDocument(document);

    if (document.kind() != EditorDocument::Kind::Indoor)
    {
        static const std::vector<Game::IndoorVertex> emptyVertices;
        return emptyVertices;
    }

    const std::string verticesKey =
        documentGeometryKey(document) + "|preview=" + std::to_string(m_indoorMechanismPreviewRevision);

    if (verticesKey == m_indoorRenderVerticesKey)
    {
        return m_indoorRenderVertices;
    }

    const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
    const Game::IndoorSceneData &sceneData = document.indoorSceneData();
    Game::MapDeltaData previewMapDeltaData = {};
    previewMapDeltaData.doors.reserve(sceneData.initialState.doors.size());

    for (const Game::IndoorSceneDoor &door : sceneData.initialState.doors)
    {
        previewMapDeltaData.doors.push_back(door.door);
    }

    Game::normalizeIndoorDoorTextureDeltas(previewMapDeltaData, indoorGeometry);

    Game::EventRuntimeState previewRuntimeState = {};
    const Game::EventRuntimeState *pPreviewRuntimeState = nullptr;

    if (!m_indoorMechanismPreviewOverrides.empty())
    {
        pPreviewRuntimeState = &previewRuntimeState;

        for (const auto &[doorIndex, previewState] : m_indoorMechanismPreviewOverrides)
        {
            if (doorIndex >= sceneData.initialState.doors.size())
            {
                continue;
            }

            previewRuntimeState.mechanisms[sceneData.initialState.doors[doorIndex].door.doorId] = previewState;
        }
    }

    m_indoorRenderVertices =
        Game::buildIndoorMechanismAdjustedVertices(indoorGeometry, &previewMapDeltaData, pPreviewRuntimeState);
    m_indoorRenderVerticesKey = verticesKey;
    return m_indoorRenderVertices;
}

Game::IndoorFaceGeometryCache &EditorOutdoorViewport::indoorRenderFaceGeometryCache(
    const EditorDocument &document) const
{
    if (document.kind() != EditorDocument::Kind::Indoor)
    {
        static Game::IndoorFaceGeometryCache emptyCache;
        return emptyCache;
    }

    const std::string cacheKey =
        documentGeometryKey(document) + "|preview=" + std::to_string(m_indoorMechanismPreviewRevision);

    if (cacheKey != m_indoorFaceGeometryCacheKey)
    {
        m_indoorFaceGeometryCache.reset(document.indoorGeometry().faces.size());
        m_indoorFaceGeometryCacheKey = cacheKey;
    }

    return m_indoorFaceGeometryCache;
}

void EditorOutdoorViewport::refreshIndoorPreviewGeometryBuffers(const EditorDocument &document)
{
    if (!m_indoorPreviewGeometryBuffersDirty || document.kind() != EditorDocument::Kind::Indoor)
    {
        return;
    }

    const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
    const Game::IndoorSceneData &sceneData = document.indoorSceneData();
    const std::vector<Game::IndoorVertex> &indoorVertices = indoorRenderVertices(document);
    Game::MapDeltaData previewMapDeltaData = {};
    previewMapDeltaData.doors.reserve(sceneData.initialState.doors.size());

    for (const Game::IndoorSceneDoor &door : sceneData.initialState.doors)
    {
        previewMapDeltaData.doors.push_back(door.door);
    }

    Game::normalizeIndoorDoorTextureDeltas(previewMapDeltaData, indoorGeometry);

    Game::EventRuntimeState previewRuntimeState = {};
    const Game::EventRuntimeState *pPreviewRuntimeState = nullptr;

    if (!m_indoorMechanismPreviewOverrides.empty())
    {
        pPreviewRuntimeState = &previewRuntimeState;

        for (const auto &[doorIndex, previewState] : m_indoorMechanismPreviewOverrides)
        {
            if (doorIndex < sceneData.initialState.doors.size())
            {
                previewRuntimeState.mechanisms[sceneData.initialState.doors[doorIndex].door.doorId] = previewState;
            }
        }
    }

    const std::vector<PreviewVertex> wireVertices =
        buildIndoorWireVertices(
            indoorGeometry,
            indoorVertices,
            m_showIndoorFloors,
            m_showIndoorCeilings,
            m_isolatedIndoorRoomId);

    if (bgfx::isValid(m_bmodelWireVertexBufferHandle))
    {
        bgfx::destroy(m_bmodelWireVertexBufferHandle);
        m_bmodelWireVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_mm9DatPortalOverlayVertexBufferHandle))
    {
        bgfx::destroy(m_mm9DatPortalOverlayVertexBufferHandle);
        m_mm9DatPortalOverlayVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_mm9DatWorldModelOverlayVertexBufferHandle))
    {
        bgfx::destroy(m_mm9DatWorldModelOverlayVertexBufferHandle);
        m_mm9DatWorldModelOverlayVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_mm9DatObjectOverlayVertexBufferHandle))
    {
        bgfx::destroy(m_mm9DatObjectOverlayVertexBufferHandle);
        m_mm9DatObjectOverlayVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    m_bmodelWireVertexCount = 0;

    if (!wireVertices.empty())
    {
        m_bmodelWireVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(wireVertices.data(), static_cast<uint32_t>(wireVertices.size() * sizeof(PreviewVertex))),
            PreviewVertex::ms_layout);
        m_bmodelWireVertexCount = static_cast<uint32_t>(wireVertices.size());
    }

    std::unordered_map<std::string, std::vector<TexturedPreviewVertex>> texturedVerticesByKey;
    std::vector<ProceduralPreviewVertex> portalVertices;
    std::vector<ProceduralPreviewVertex> unassignedVertices;
    std::vector<ProceduralPreviewVertex> missingVertices;
    std::unordered_map<std::string, std::pair<int, int>> textureSizesByKey;

    for (const TexturedBatch &batch : m_bmodelTexturedBatches)
    {
        textureSizesByKey[batch.key] = {batch.textureWidth, batch.textureHeight};
    }

    for (size_t faceIndex = 0; faceIndex < indoorGeometry.faces.size(); ++faceIndex)
    {
        if (indoorFaceHiddenByCeilingView(
                indoorGeometry,
                indoorVertices,
                faceIndex,
                m_showIndoorFloors,
                m_showIndoorCeilings,
                m_isolatedIndoorRoomId))
        {
            continue;
        }

        const Game::IndoorFace &face = indoorGeometry.faces[faceIndex];
        const bx::Vec3 objectOrigin = {0.0f, 0.0f, 0.0f};
        const std::vector<ProceduralPreviewVertex> allFaceVertices =
            buildProceduralIndoorFaceVertices(indoorGeometry, indoorVertices, faceIndex, objectOrigin);

        if (face.isPortal)
        {
            portalVertices.insert(portalVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
            continue;
        }

        if (face.textureName.empty())
        {
            unassignedVertices.insert(unassignedVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
            continue;
        }

        const std::string textureKey = toLowerCopy(face.textureName);
        const auto sizeIt = textureSizesByKey.find(textureKey);

        if (sizeIt == textureSizesByKey.end() || sizeIt->second.first <= 0 || sizeIt->second.second <= 0)
        {
            missingVertices.insert(missingVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
            continue;
        }

        std::vector<TexturedPreviewVertex> faceVertices =
            buildTexturedIndoorFaceVertices(
                indoorGeometry,
                indoorVertices,
                faceIndex,
                sizeIt->second.first,
                sizeIt->second.second,
                &previewMapDeltaData,
                pPreviewRuntimeState);

        if (faceVertices.empty())
        {
            continue;
        }

        std::vector<TexturedPreviewVertex> &batchVertices = texturedVerticesByKey[textureKey];
        batchVertices.insert(batchVertices.end(), faceVertices.begin(), faceVertices.end());
    }

    const auto rebuildTexturedBatch =
        [](TexturedBatch &batch, const std::vector<TexturedPreviewVertex> &vertices)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
            batch.vertexBufferHandle = BGFX_INVALID_HANDLE;
        }

        batch.vertexCount = 0;

        if (vertices.empty())
        {
            return;
        }

        batch.vertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(TexturedPreviewVertex))),
            TexturedPreviewVertex::ms_layout);
        batch.vertexCount = bgfx::isValid(batch.vertexBufferHandle) ? static_cast<uint32_t>(vertices.size()) : 0;
    };

    const auto rebuildProceduralBatch =
        [](std::vector<ProceduralBatch> &batches, const char *pKey, const std::vector<ProceduralPreviewVertex> &vertices)
    {
        for (ProceduralBatch &batch : batches)
        {
            if (batch.key != pKey)
            {
                continue;
            }

            if (bgfx::isValid(batch.vertexBufferHandle))
            {
                bgfx::destroy(batch.vertexBufferHandle);
                batch.vertexBufferHandle = BGFX_INVALID_HANDLE;
            }

            batch.vertexCount = 0;

            if (!vertices.empty())
            {
                batch.vertexBufferHandle = bgfx::createVertexBuffer(
                    bgfx::copy(
                        vertices.data(),
                        static_cast<uint32_t>(vertices.size() * sizeof(ProceduralPreviewVertex))),
                    ProceduralPreviewVertex::ms_layout);
                batch.vertexCount =
                    bgfx::isValid(batch.vertexBufferHandle) ? static_cast<uint32_t>(vertices.size()) : 0;
            }

            return;
        }
    };

    for (TexturedBatch &batch : m_bmodelTexturedBatches)
    {
        const auto verticesIt = texturedVerticesByKey.find(batch.key);
        static const std::vector<TexturedPreviewVertex> emptyVertices;
        rebuildTexturedBatch(batch, verticesIt != texturedVerticesByKey.end() ? verticesIt->second : emptyVertices);
    }

    rebuildProceduralBatch(m_bmodelUnassignedBatches, "__unassigned__", unassignedVertices);
    rebuildProceduralBatch(m_bmodelMissingAssetBatches, "__missing__", missingVertices);
    rebuildProceduralBatch(m_indoorPortalBatches, "__portals__", portalVertices);
    m_indoorPreviewGeometryBuffersDirty = false;
}

const bx::Vec3 &EditorOutdoorViewport::cameraPosition() const
{
    return m_cameraPosition;
}

float EditorOutdoorViewport::cameraYawRadians() const
{
    return m_cameraYawRadians;
}

float EditorOutdoorViewport::cameraPitchRadians() const
{
    return m_cameraPitchRadians;
}

bgfx::TextureHandle EditorOutdoorViewport::viewportTextureHandle() const
{
    return m_colorTextureHandle;
}

bgfx::TextureHandle EditorOutdoorViewport::terrainTextureAtlasHandle() const
{
    return m_terrainTextureAtlasHandle;
}

bool EditorOutdoorViewport::tryGetTerrainTilePreviewUv(
    uint8_t tileId,
    float &u0,
    float &v0,
    float &u1,
    float &v1) const
{
    if (!m_terrainTilePreviewValid[static_cast<size_t>(tileId)])
    {
        return false;
    }

    const std::array<float, 4> &uvs = m_terrainTilePreviewUvs[static_cast<size_t>(tileId)];
    u0 = uvs[0];
    v0 = uvs[1];
    u1 = uvs[2];
    v1 = uvs[3];
    return true;
}

bool EditorOutdoorViewport::ensureRenderResources()
{
    if (bgfx::isValid(m_programHandle)
        && bgfx::isValid(m_texturedProgramHandle)
        && bgfx::isValid(m_proceduralPreviewProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && bgfx::isValid(m_previewColorAHandle)
        && bgfx::isValid(m_previewColorBHandle)
        && bgfx::isValid(m_previewColorCHandle)
        && bgfx::isValid(m_previewColorDHandle)
        && bgfx::isValid(m_previewParams0Handle)
        && bgfx::isValid(m_previewParams1Handle)
        && bgfx::isValid(m_previewObjectOriginHandle))
    {
        return true;
    }

    PreviewVertex::init();
    TexturedPreviewVertex::init();
    ProceduralPreviewVertex::init();
    m_programHandle = loadProgram("vs_cubes", "fs_cubes");
    m_texturedProgramHandle = loadProgram("vs_editor_textured", "fs_editor_textured");
    m_proceduralPreviewProgramHandle = loadProgram("vs_editor_preview_material", "fs_editor_preview_material");
    m_textureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);
    m_previewColorAHandle = bgfx::createUniform("u_previewColorA", bgfx::UniformType::Vec4);
    m_previewColorBHandle = bgfx::createUniform("u_previewColorB", bgfx::UniformType::Vec4);
    m_previewColorCHandle = bgfx::createUniform("u_previewColorC", bgfx::UniformType::Vec4);
    m_previewColorDHandle = bgfx::createUniform("u_previewColorD", bgfx::UniformType::Vec4);
    m_previewParams0Handle = bgfx::createUniform("u_previewParams0", bgfx::UniformType::Vec4);
    m_previewParams1Handle = bgfx::createUniform("u_previewParams1", bgfx::UniformType::Vec4);
    m_previewObjectOriginHandle = bgfx::createUniform("u_previewObjectOrigin", bgfx::UniformType::Vec4);
    return bgfx::isValid(m_programHandle)
        && bgfx::isValid(m_texturedProgramHandle)
        && bgfx::isValid(m_proceduralPreviewProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && bgfx::isValid(m_previewColorAHandle)
        && bgfx::isValid(m_previewColorBHandle)
        && bgfx::isValid(m_previewColorCHandle)
        && bgfx::isValid(m_previewColorDHandle)
        && bgfx::isValid(m_previewParams0Handle)
        && bgfx::isValid(m_previewParams1Handle)
        && bgfx::isValid(m_previewObjectOriginHandle);
}

void EditorOutdoorViewport::destroyGeometryBuffers()
{
    if (bgfx::isValid(m_terrainVertexBufferHandle))
    {
        bgfx::destroy(m_terrainVertexBufferHandle);
        m_terrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_bmodelWireVertexBufferHandle))
    {
        bgfx::destroy(m_bmodelWireVertexBufferHandle);
        m_bmodelWireVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainErrorVertexBufferHandle))
    {
        bgfx::destroy(m_terrainErrorVertexBufferHandle);
        m_terrainErrorVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_texturedTerrainVertexBufferHandle))
    {
        bgfx::destroy(m_texturedTerrainVertexBufferHandle);
        m_texturedTerrainVertexBufferHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_terrainTextureAtlasHandle))
    {
        bgfx::destroy(m_terrainTextureAtlasHandle);
        m_terrainTextureAtlasHandle = BGFX_INVALID_HANDLE;
    }

    m_terrainTilePreviewValid.fill(false);
    m_terrainTilePreviewUvs.fill({0.0f, 0.0f, 0.0f, 0.0f});

    for (TexturedBatch &batch : m_bmodelTexturedBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }

        if (bgfx::isValid(batch.textureHandle))
        {
            bgfx::destroy(batch.textureHandle);
        }
    }

    m_bmodelTexturedBatches.clear();

    for (TexturedBatch &batch : m_modelInstanceTexturedBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }

        if (bgfx::isValid(batch.textureHandle))
        {
            bgfx::destroy(batch.textureHandle);
        }
    }

    m_modelInstanceTexturedBatches.clear();

    for (ProceduralBatch &batch : m_bmodelAllFaceBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    for (ProceduralBatch &batch : m_indoorPortalBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    for (ProceduralBatch &batch : m_bmodelUnassignedBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    for (ProceduralBatch &batch : m_bmodelMissingAssetBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    for (ProceduralBatch &batch : m_modelInstanceBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    for (ProceduralBatch &batch : m_modelInstanceMissingBatches)
    {
        if (bgfx::isValid(batch.vertexBufferHandle))
        {
            bgfx::destroy(batch.vertexBufferHandle);
        }
    }

    m_bmodelAllFaceBatches.clear();
    m_indoorPortalBatches.clear();
    m_bmodelUnassignedBatches.clear();
    m_bmodelMissingAssetBatches.clear();
    m_modelInstanceBatches.clear();
    m_modelInstanceMissingBatches.clear();

    m_terrainVertexCount = 0;
    m_terrainErrorVertexCount = 0;
    m_texturedTerrainVertexCount = 0;
    m_bmodelWireVertexCount = 0;
    m_mm9DatPortalOverlayVertexCount = 0;
    m_mm9DatWorldModelOverlayVertexCount = 0;
    m_mm9DatObjectOverlayVertexCount = 0;
}

void EditorOutdoorViewport::ensureRenderTarget(uint16_t viewportWidth, uint16_t viewportHeight)
{
    const ImVec2 framebufferScale = ImGui::GetIO().DisplayFramebufferScale;
    const uint16_t renderWidth = static_cast<uint16_t>(std::max(
        1.0f,
        std::round(static_cast<float>(viewportWidth) * framebufferScale.x)));
    const uint16_t renderHeight = static_cast<uint16_t>(std::max(
        1.0f,
        std::round(static_cast<float>(viewportHeight) * framebufferScale.y)));

    if (bgfx::isValid(m_frameBufferHandle) && renderWidth == m_renderWidth && renderHeight == m_renderHeight)
    {
        return;
    }

    destroyRenderTarget();
    m_renderWidth = renderWidth;
    m_renderHeight = renderHeight;
    m_colorTextureHandle = bgfx::createTexture2D(
        renderWidth,
        renderHeight,
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_TEXTURE_RT | BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
    m_depthTextureHandle = bgfx::createTexture2D(
        renderWidth,
        renderHeight,
        false,
        1,
        bgfx::TextureFormat::D24S8,
        BGFX_TEXTURE_RT_WRITE_ONLY);

    if (!bgfx::isValid(m_colorTextureHandle) || !bgfx::isValid(m_depthTextureHandle))
    {
        destroyRenderTarget();
        return;
    }

    std::array<bgfx::Attachment, 2> attachments = {};
    attachments[0].init(m_colorTextureHandle);
    attachments[1].init(m_depthTextureHandle);
    m_frameBufferHandle = bgfx::createFrameBuffer(
        static_cast<uint8_t>(attachments.size()),
        attachments.data(),
        true);

    if (!bgfx::isValid(m_frameBufferHandle))
    {
        destroyRenderTarget();
    }
}

void EditorOutdoorViewport::destroyRenderTarget()
{
    if (bgfx::isValid(m_frameBufferHandle))
    {
        bgfx::destroy(m_frameBufferHandle);
        m_frameBufferHandle = BGFX_INVALID_HANDLE;
    }

    m_colorTextureHandle = BGFX_INVALID_HANDLE;
    m_depthTextureHandle = BGFX_INVALID_HANDLE;
}

void EditorOutdoorViewport::ensureGeometryBuffers(EditorSession &session)
{
    if (!session.hasDocument() || session.assetFileSystem() == nullptr)
    {
        return;
    }

    const EditorDocument &document = session.document();
    std::string geometryKey = documentGeometryKey(document);
    if (document.kind() == EditorDocument::Kind::Mm9Dat)
    {
        ensureMm9MechanismPreviewDocument(document);
    }

    if (geometryKey == m_geometryKey)
    {
        return;
    }

    destroyGeometryBuffers();
    m_geometryKey = geometryKey;
    const Engine::AssetFileSystem &assetFileSystem = *session.assetFileSystem();

    if (document.kind() == EditorDocument::Kind::Mm9Dat)
    {
        if (!document.hasMm9DatWorld())
        {
            return;
        }

        const Game::Mm9DatRenderMesh &renderMesh = document.mm9DatRenderMesh();
        if (renderMesh.triangles.empty())
        {
            return;
        }

        std::vector<Game::Mm9DatModelRenderRole> modelRoles;
        size_t portalOverlayCount = 0;

        if (document.hasMm9DatLoadedSidecars())
        {
            const EditorMm9DatWorldSidecar &datWorld = document.mm9DatLoadedSidecars().datWorld;
            modelRoles = buildMm9DatModelRenderRoles(datWorld);
            portalOverlayCount = datWorld.userPortals.size();
        }

        const Game::Mm9DatRenderFilterResult filterResult =
            Game::classifyMm9DatRenderMeshFilters(renderMesh, modelRoles, portalOverlayCount);
        std::vector<uint32_t> filterFlagsByTriangle(renderMesh.triangles.size(), Game::Mm9DatRenderFilterVisual);

        for (const Game::Mm9DatRenderFilterEntry &entry : filterResult.entries)
        {
            if (entry.triangleIndex < filterFlagsByTriangle.size())
            {
                filterFlagsByTriangle[entry.triangleIndex] = entry.flags;
            }
        }

        std::vector<const Game::Mm9DatRenderMaterialAssignment *> assignmentsByTriangle(
            renderMesh.triangles.size(),
            nullptr);

        for (const Game::Mm9DatRenderMaterialAssignment &assignment : document.mm9DatRenderMaterialAssignments())
        {
            if (assignment.triangleIndex < assignmentsByTriangle.size())
            {
                assignmentsByTriangle[assignment.triangleIndex] = &assignment;
            }
        }

        std::unordered_map<std::string, std::optional<Game::Mm9DtxTexture>> sourceTexturesByPath;
        const auto loadSourceDtxTexture =
            [&sourceTexturesByPath](const std::filesystem::path &sourcePath)
                -> const std::optional<Game::Mm9DtxTexture> &
        {
            const std::string sourcePathKey = sourcePath.generic_string();
            const auto cachedTextureIt = sourceTexturesByPath.find(sourcePathKey);

            if (cachedTextureIt != sourceTexturesByPath.end())
            {
                return cachedTextureIt->second;
            }

            std::string errorMessage;
            return sourceTexturesByPath.emplace(
                sourcePathKey,
                Game::loadMm9DtxTexture(sourcePath, errorMessage)).first->second;
        };
        std::unordered_map<std::string, std::vector<TexturedPreviewVertex>> texturedVerticesByBatchKey;
        std::unordered_map<std::string, std::string> sourceTexturePathByBatchKey;
        std::unordered_map<std::string, size_t> sourceModelIndexByTexturedBatchKey;
        std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> allVisualVerticesBySourceModel;
        std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> missingMaterialVerticesBySourceModel;

        for (size_t triangleIndex = 0; triangleIndex < renderMesh.triangles.size(); ++triangleIndex)
        {
            Game::Mm9DatRenderFilterEntry filterEntry = {};
            filterEntry.triangleIndex = triangleIndex;
            filterEntry.flags = filterFlagsByTriangle[triangleIndex];

            if (!shouldRenderMm9DatTriangleForSubset(filterEntry, m_mm9DatWorldRenderSubset))
            {
                continue;
            }

            const Game::Mm9DatRenderTriangle &triangle = renderMesh.triangles[triangleIndex];

            appendMm9DatProceduralTriangleVertices(
                triangle,
                allVisualVerticesBySourceModel[triangle.sourceModelIndex]);

            const Game::Mm9DatRenderMaterialAssignment *pAssignment = assignmentsByTriangle[triangleIndex];
            if (pAssignment == nullptr
                || !pAssignment->assigned
                || !pAssignment->sourceDtxResolved
                || pAssignment->resolvedSourcePath.empty())
            {
                appendMm9DatProceduralTriangleVertices(
                    triangle,
                    missingMaterialVerticesBySourceModel[triangle.sourceModelIndex]);
                continue;
            }

            const std::filesystem::path sourcePath =
                resolvePhysicalPathRelativeToDocument(document, pAssignment->resolvedSourcePath);
            const std::string sourcePathKey = sourcePath.generic_string();
            const std::optional<Game::Mm9DtxTexture> &sourceTexture =
                loadSourceDtxTexture(sourcePath);

            if (!sourceTexture
                || sourceTexture->width == 0
                || sourceTexture->height == 0
                || sourceTexture->pixelsBgra.empty())
            {
                appendMm9DatProceduralTriangleVertices(
                    triangle,
                    missingMaterialVerticesBySourceModel[triangle.sourceModelIndex]);
                continue;
            }

            const std::string texturedBatchKey =
                sourcePathKey + "|source_model=" + std::to_string(triangle.sourceModelIndex);
            sourceTexturePathByBatchKey.emplace(texturedBatchKey, sourcePathKey);
            sourceModelIndexByTexturedBatchKey.emplace(texturedBatchKey, triangle.sourceModelIndex);
            appendMm9DatTexturedTriangleVertices(
                triangle,
                sourceTexture->width,
                sourceTexture->height,
                texturedVerticesByBatchKey[texturedBatchKey]);
        }

        for (const auto &[sourceModelIndex, vertices] : allVisualVerticesBySourceModel)
        {
            if (vertices.empty())
            {
                continue;
            }

            ProceduralBatch batch = {};
            batch.vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    vertices.data(),
                    static_cast<uint32_t>(vertices.size() * sizeof(ProceduralPreviewVertex))),
                ProceduralPreviewVertex::ms_layout);
            batch.vertexCount = static_cast<uint32_t>(vertices.size());
            batch.bmodelIndex = sourceModelIndex;
            batch.key = "mm9_dat_visual_" + std::to_string(sourceModelIndex);

            if (bgfx::isValid(batch.vertexBufferHandle))
            {
                m_bmodelAllFaceBatches.push_back(batch);
            }
        }

        for (const auto &[texturedBatchKey, vertices] : texturedVerticesByBatchKey)
        {
            const auto sourceModelIt = sourceModelIndexByTexturedBatchKey.find(texturedBatchKey);
            const size_t sourceModelIndex =
                sourceModelIt != sourceModelIndexByTexturedBatchKey.end()
                    ? sourceModelIt->second
                    : std::numeric_limits<size_t>::max();
            const auto sourcePathIt = sourceTexturePathByBatchKey.find(texturedBatchKey);
            const std::string sourcePathKey =
                sourcePathIt != sourceTexturePathByBatchKey.end()
                    ? sourcePathIt->second
                    : std::string();
            const std::optional<Game::Mm9DtxTexture> *pSourceTexture = nullptr;

            if (!sourcePathKey.empty())
            {
                pSourceTexture = &loadSourceDtxTexture(sourcePathKey);
            }

            if (pSourceTexture == nullptr
                || !*pSourceTexture
                || (*pSourceTexture)->width == 0
                || (*pSourceTexture)->height == 0
                || (*pSourceTexture)->pixelsBgra.empty()
                || vertices.empty())
            {
                appendTexturedVerticesAsMissingProcedural(
                    vertices,
                    missingMaterialVerticesBySourceModel[sourceModelIndex]);
                continue;
            }

            const Game::Mm9DtxTexture &sourceTexture = **pSourceTexture;

            TexturedBatch batch = {};
            batch.vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(TexturedPreviewVertex))),
                TexturedPreviewVertex::ms_layout);
            batch.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(sourceTexture.width),
                static_cast<uint16_t>(sourceTexture.height),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT,
                bgfx::copy(
                    sourceTexture.pixelsBgra.data(),
                    static_cast<uint32_t>(sourceTexture.pixelsBgra.size())));
            batch.vertexCount = static_cast<uint32_t>(vertices.size());
            batch.bmodelIndex = sourceModelIndex;
            batch.key = sourcePathKey;
            batch.textureWidth = static_cast<int>(sourceTexture.width);
            batch.textureHeight = static_cast<int>(sourceTexture.height);
            batch.hasTransparentPixels = hasTransparentPixels(sourceTexture.pixelsBgra);

            if (bgfx::isValid(batch.vertexBufferHandle) && bgfx::isValid(batch.textureHandle))
            {
                m_bmodelTexturedBatches.push_back(batch);
            }
            else
            {
                if (bgfx::isValid(batch.vertexBufferHandle))
                {
                    bgfx::destroy(batch.vertexBufferHandle);
                }

                if (bgfx::isValid(batch.textureHandle))
                {
                    bgfx::destroy(batch.textureHandle);
                }

                appendTexturedVerticesAsMissingProcedural(
                    vertices,
                    missingMaterialVerticesBySourceModel[sourceModelIndex]);
            }
        }

        for (const auto &[sourceModelIndex, vertices] : missingMaterialVerticesBySourceModel)
        {
            if (vertices.empty())
            {
                continue;
            }

            ProceduralBatch batch = {};
            batch.vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    vertices.data(),
                    static_cast<uint32_t>(vertices.size() * sizeof(ProceduralPreviewVertex))),
                ProceduralPreviewVertex::ms_layout);
            batch.vertexCount = static_cast<uint32_t>(vertices.size());
            batch.bmodelIndex = sourceModelIndex;
            batch.key = "mm9_dat_missing_material_" + std::to_string(sourceModelIndex);

            if (bgfx::isValid(batch.vertexBufferHandle))
            {
                m_bmodelMissingAssetBatches.push_back(batch);
            }
        }

        if (document.hasMm9DatLoadedSidecars())
        {
            const std::vector<PreviewVertex> portalOverlayVertices =
                buildMm9DatUserPortalOverlayVertices(document.mm9DatLoadedSidecars().datWorld);
            const std::vector<PreviewVertex> worldModelOverlayVertices =
                buildMm9DatWorldModelOverlayVertices(document.mm9DatLoadedSidecars().datWorld);
            const std::vector<PreviewVertex> objectOverlayVertices =
                buildMm9DatObjectOverlayVertices(document.mm9ObjectLayer());

            if (!portalOverlayVertices.empty())
            {
                m_mm9DatPortalOverlayVertexBufferHandle = bgfx::createVertexBuffer(
                    bgfx::copy(
                        portalOverlayVertices.data(),
                        static_cast<uint32_t>(portalOverlayVertices.size() * sizeof(PreviewVertex))),
                    PreviewVertex::ms_layout);
                m_mm9DatPortalOverlayVertexCount =
                    bgfx::isValid(m_mm9DatPortalOverlayVertexBufferHandle)
                        ? static_cast<uint32_t>(portalOverlayVertices.size())
                        : 0;
            }

            if (!worldModelOverlayVertices.empty())
            {
                m_mm9DatWorldModelOverlayVertexBufferHandle = bgfx::createVertexBuffer(
                    bgfx::copy(
                        worldModelOverlayVertices.data(),
                        static_cast<uint32_t>(worldModelOverlayVertices.size() * sizeof(PreviewVertex))),
                    PreviewVertex::ms_layout);
                m_mm9DatWorldModelOverlayVertexCount =
                    bgfx::isValid(m_mm9DatWorldModelOverlayVertexBufferHandle)
                        ? static_cast<uint32_t>(worldModelOverlayVertices.size())
                        : 0;
            }

            if (!objectOverlayVertices.empty())
            {
                m_mm9DatObjectOverlayVertexBufferHandle = bgfx::createVertexBuffer(
                    bgfx::copy(
                        objectOverlayVertices.data(),
                        static_cast<uint32_t>(objectOverlayVertices.size() * sizeof(PreviewVertex))),
                    PreviewVertex::ms_layout);
                m_mm9DatObjectOverlayVertexCount =
                    bgfx::isValid(m_mm9DatObjectOverlayVertexBufferHandle)
                        ? static_cast<uint32_t>(objectOverlayVertices.size())
                        : 0;
            }
        }

        // Continue into the shared outdoor object-instance buffer path below. For MM9 DAT documents the DAT mesh above
        // remains the authoritative world geometry; the object-derived scene sidecar only contributes placed assets.
    }

    if (document.kind() == EditorDocument::Kind::Indoor)
    {
        const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
        const Game::IndoorSceneData &sceneData = document.indoorSceneData();
        const std::vector<Game::IndoorVertex> &indoorVertices = indoorRenderVertices(document);
        Game::MapDeltaData previewMapDeltaData = {};
        previewMapDeltaData.doors.reserve(sceneData.initialState.doors.size());

        for (const Game::IndoorSceneDoor &door : sceneData.initialState.doors)
        {
            previewMapDeltaData.doors.push_back(door.door);
        }

        Game::normalizeIndoorDoorTextureDeltas(previewMapDeltaData, indoorGeometry);

        Game::EventRuntimeState previewRuntimeState = {};
        const Game::EventRuntimeState *pPreviewRuntimeState = nullptr;

        if (!m_indoorMechanismPreviewOverrides.empty())
        {
            pPreviewRuntimeState = &previewRuntimeState;

            for (const auto &[doorIndex, previewState] : m_indoorMechanismPreviewOverrides)
            {
                if (doorIndex < sceneData.initialState.doors.size())
                {
                    previewRuntimeState.mechanisms[sceneData.initialState.doors[doorIndex].door.doorId] = previewState;
                }
            }
        }

        const std::vector<PreviewVertex> wireVertices =
            buildIndoorWireVertices(
                indoorGeometry,
                indoorVertices,
                m_showIndoorFloors,
                m_showIndoorCeilings,
                m_isolatedIndoorRoomId);

        if (!wireVertices.empty())
        {
            m_bmodelWireVertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    wireVertices.data(),
                    static_cast<uint32_t>(wireVertices.size() * sizeof(PreviewVertex))),
                PreviewVertex::ms_layout);
            m_bmodelWireVertexCount = static_cast<uint32_t>(wireVertices.size());
        }

        BitmapLoadCache bitmapLoadCache = {};
        std::unordered_map<std::string, std::vector<TexturedPreviewVertex>> batchVerticesByKey;
        std::unordered_map<std::string, std::vector<ProceduralPreviewVertex>> missingVerticesByKey;
        std::vector<ProceduralPreviewVertex> portalVertices;

        for (size_t faceIndex = 0; faceIndex < indoorGeometry.faces.size(); ++faceIndex)
        {
            if (indoorFaceHiddenByCeilingView(
                    indoorGeometry,
                    indoorVertices,
                    faceIndex,
                    m_showIndoorFloors,
                    m_showIndoorCeilings,
                    m_isolatedIndoorRoomId))
            {
                continue;
            }

            const Game::IndoorFace &face = indoorGeometry.faces[faceIndex];
            const bx::Vec3 objectOrigin = {0.0f, 0.0f, 0.0f};
            const std::vector<ProceduralPreviewVertex> allFaceVertices =
                buildProceduralIndoorFaceVertices(indoorGeometry, indoorVertices, faceIndex, objectOrigin);

            if (face.isPortal)
            {
                if (!allFaceVertices.empty())
                {
                    portalVertices.insert(portalVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
                }

                continue;
            }

            if (face.textureName.empty())
            {
                if (!allFaceVertices.empty())
                {
                    std::vector<ProceduralPreviewVertex> &missingVertices = missingVerticesByKey["__unassigned__"];
                    missingVertices.insert(missingVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
                }

                continue;
            }

            int textureWidth = 0;
            int textureHeight = 0;
            const std::optional<std::vector<uint8_t>> texturePixels =
                loadBitmapPixelsBgra(
                    assetFileSystem,
                    "Data/bitmaps",
                    face.textureName,
                    textureWidth,
                    textureHeight,
                    false,
                    bitmapLoadCache);

            if (!texturePixels || textureWidth <= 0 || textureHeight <= 0)
            {
                if (!allFaceVertices.empty())
                {
                    std::vector<ProceduralPreviewVertex> &missingVertices = missingVerticesByKey["__missing__"];
                    missingVertices.insert(missingVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
                }

                continue;
            }

            std::vector<TexturedPreviewVertex> faceVertices =
                buildTexturedIndoorFaceVertices(
                    indoorGeometry,
                    indoorVertices,
                    faceIndex,
                    textureWidth,
                    textureHeight,
                    &previewMapDeltaData,
                    pPreviewRuntimeState);

            if (faceVertices.empty())
            {
                continue;
            }

            std::vector<TexturedPreviewVertex> &batchVertices = batchVerticesByKey[toLowerCopy(face.textureName)];
            batchVertices.insert(batchVertices.end(), faceVertices.begin(), faceVertices.end());
        }

        for (const auto &[textureName, vertices] : batchVerticesByKey)
        {
            if (vertices.empty())
            {
                continue;
            }

            int textureWidth = 0;
            int textureHeight = 0;
            const std::optional<std::vector<uint8_t>> texturePixels =
                loadBitmapPixelsBgra(
                    assetFileSystem,
                    "Data/bitmaps",
                    textureName,
                    textureWidth,
                    textureHeight,
                    false,
                    bitmapLoadCache);

            if (!texturePixels || textureWidth <= 0 || textureHeight <= 0)
            {
                continue;
            }

            TexturedBatch batch = {};
            batch.vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(TexturedPreviewVertex))),
                TexturedPreviewVertex::ms_layout);
            batch.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(textureWidth),
                static_cast<uint16_t>(textureHeight),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT,
                bgfx::copy(texturePixels->data(), static_cast<uint32_t>(texturePixels->size())));
            batch.vertexCount = static_cast<uint32_t>(vertices.size());
            batch.key = textureName;
            batch.textureWidth = textureWidth;
            batch.textureHeight = textureHeight;

            if (bgfx::isValid(batch.vertexBufferHandle) && bgfx::isValid(batch.textureHandle))
            {
                m_bmodelTexturedBatches.push_back(batch);
            }
        }

        const auto appendProceduralBatch =
            [](const std::vector<ProceduralPreviewVertex> &vertices,
                const char *pKey,
                std::vector<EditorOutdoorViewport::ProceduralBatch> &targetBatches)
        {
            if (vertices.empty())
            {
                return;
            }

            EditorOutdoorViewport::ProceduralBatch batch = {};
            batch.vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    vertices.data(),
                    static_cast<uint32_t>(vertices.size() * sizeof(EditorOutdoorViewport::ProceduralPreviewVertex))),
                EditorOutdoorViewport::ProceduralPreviewVertex::ms_layout);
            batch.vertexCount = static_cast<uint32_t>(vertices.size());
            batch.key = pKey;

            if (bgfx::isValid(batch.vertexBufferHandle))
            {
                targetBatches.push_back(batch);
            }
        };

        if (const auto unassignedIt = missingVerticesByKey.find("__unassigned__"); unassignedIt != missingVerticesByKey.end())
        {
            appendProceduralBatch(unassignedIt->second, "__unassigned__", m_bmodelUnassignedBatches);
        }

        if (const auto missingIt = missingVerticesByKey.find("__missing__"); missingIt != missingVerticesByKey.end())
        {
            appendProceduralBatch(missingIt->second, "__missing__", m_bmodelMissingAssetBatches);
        }

        appendProceduralBatch(portalVertices, "__portals__", m_indoorPortalBatches);
        m_indoorPreviewGeometryBuffersDirty = false;

        return;
    }

    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const bool renderTerrainHeightmap = shouldRenderTerrainHeightmap(document);
    const std::vector<ProceduralPreviewVertex> terrainVertices =
        renderTerrainHeightmap ? buildTerrainVertices(outdoorGeometry) : std::vector<ProceduralPreviewVertex>{};
    const std::vector<PreviewVertex> bmodelWireVertices = buildBModelWireVertices(outdoorGeometry);

    if (!terrainVertices.empty())
    {
        m_terrainVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                terrainVertices.data(),
                static_cast<uint32_t>(terrainVertices.size() * sizeof(ProceduralPreviewVertex))),
            ProceduralPreviewVertex::ms_layout);
        m_terrainVertexCount = static_cast<uint32_t>(terrainVertices.size());
    }

    if (!bmodelWireVertices.empty())
    {
        m_bmodelWireVertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                bmodelWireVertices.data(),
                static_cast<uint32_t>(bmodelWireVertices.size() * sizeof(PreviewVertex))),
            PreviewVertex::ms_layout);
        m_bmodelWireVertexCount = static_cast<uint32_t>(bmodelWireVertices.size());
    }

    BitmapLoadCache bitmapLoadCache = {};
    const std::optional<TerrainAtlasData> atlasData =
        renderTerrainHeightmap
            ? buildTerrainAtlasData(assetFileSystem, outdoorGeometry, bitmapLoadCache)
            : std::optional<TerrainAtlasData>{};

    if (atlasData && !atlasData->pixels.empty())
    {
        for (size_t tileIndex = 0; tileIndex < atlasData->tileRegions.size(); ++tileIndex)
        {
            const TerrainAtlasRegion &region = atlasData->tileRegions[tileIndex];
            m_terrainTilePreviewValid[tileIndex] = region.isValid;
            m_terrainTilePreviewUvs[tileIndex] = {region.u0, region.v0, region.u1, region.v1};
        }

        const std::vector<TexturedPreviewVertex> texturedTerrainVertices =
            buildTexturedTerrainVertices(outdoorGeometry, *atlasData);

        if (!texturedTerrainVertices.empty())
        {
            m_texturedTerrainVertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    texturedTerrainVertices.data(),
                    static_cast<uint32_t>(texturedTerrainVertices.size() * sizeof(TexturedPreviewVertex))),
                TexturedPreviewVertex::ms_layout);
            m_texturedTerrainVertexCount = static_cast<uint32_t>(texturedTerrainVertices.size());
        }

        m_terrainTextureAtlasHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(atlasData->width),
            static_cast<uint16_t>(atlasData->height),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_U_CLAMP
                | BGFX_SAMPLER_V_CLAMP
                | BGFX_SAMPLER_MIN_POINT
                | BGFX_SAMPLER_MAG_POINT
                | BGFX_SAMPLER_MIP_POINT,
            bgfx::copy(atlasData->pixels.data(), static_cast<uint32_t>(atlasData->pixels.size())));

        const std::vector<ProceduralPreviewVertex> terrainErrorVertices =
            buildTerrainErrorVertices(outdoorGeometry, *atlasData);

        if (!terrainErrorVertices.empty())
        {
            m_terrainErrorVertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    terrainErrorVertices.data(),
                    static_cast<uint32_t>(terrainErrorVertices.size() * sizeof(ProceduralPreviewVertex))),
                ProceduralPreviewVertex::ms_layout);
            m_terrainErrorVertexCount = static_cast<uint32_t>(terrainErrorVertices.size());
        }
    }

    std::unordered_map<std::string, std::vector<TexturedPreviewVertex>> batchVerticesByKey;
    std::unordered_map<std::string, std::string> textureNameByBatchKey;
    std::unordered_map<std::string, size_t> bmodelIndexByBatchKey;
    std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> allFaceVerticesByBModel;
    std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> unassignedVerticesByBModel;
    std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> missingAssetVerticesByBModel;
    std::unordered_map<size_t, bx::Vec3> previewOriginByBModel;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
        const EditorBModelSourceTransform sourceTransform = sourceTransformFromBModel(bmodel);
        const bx::Vec3 previewOrigin = {
            sourceTransform.originX,
            sourceTransform.originY,
            sourceTransform.originZ
        };
        previewOriginByBModel.emplace(bmodelIndex, previewOrigin);

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            const Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];
            if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible))
            {
                continue;
            }

            std::vector<ProceduralPreviewVertex> allFaceVertices =
                buildProceduralBModelFaceVertices(outdoorGeometry, bmodelIndex, faceIndex, previewOrigin);

            if (!allFaceVertices.empty())
            {
                std::vector<ProceduralPreviewVertex> &allVertices = allFaceVerticesByBModel[bmodelIndex];

                if (allVertices.empty())
                {
                    allVertices.reserve(allFaceVertices.size() * 4);
                }

                allVertices.insert(allVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
            }

            if (face.textureName.empty())
            {
                std::vector<ProceduralPreviewVertex> &unassignedVertices = unassignedVerticesByBModel[bmodelIndex];

                if (unassignedVertices.empty())
                {
                    unassignedVertices.reserve(allFaceVertices.size() * 2);
                }

                unassignedVertices.insert(unassignedVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
                continue;
            }

            int textureWidth = 0;
            int textureHeight = 0;
            const std::optional<std::vector<uint8_t>> texturePixels =
                loadOutdoorBModelBitmapPixelsBgra(
                    assetFileSystem,
                    outdoorGeometry,
                    face.textureName,
                    textureWidth,
                    textureHeight,
                    bitmapLoadCache);

            if (!texturePixels || textureWidth <= 0 || textureHeight <= 0)
            {
                std::vector<ProceduralPreviewVertex> &missingVertices = missingAssetVerticesByBModel[bmodelIndex];

                if (missingVertices.empty())
                {
                    missingVertices.reserve(allFaceVertices.size() * 2);
                }

                missingVertices.insert(missingVertices.end(), allFaceVertices.begin(), allFaceVertices.end());
                continue;
            }

            std::vector<TexturedPreviewVertex> faceVertices =
                buildTexturedBModelFaceVertices(outdoorGeometry, bmodelIndex, faceIndex, textureWidth, textureHeight);

            if (faceVertices.empty())
            {
                continue;
            }

            const std::string textureKey = toLowerCopy(face.textureName);
            const std::string batchKey = textureKey + "|" + std::to_string(bmodelIndex);
            textureNameByBatchKey[batchKey] = textureKey;
            bmodelIndexByBatchKey[batchKey] = bmodelIndex;
            std::vector<TexturedPreviewVertex> &batchVertices = batchVerticesByKey[batchKey];

            if (batchVertices.empty())
            {
                batchVertices.reserve(faceVertices.size() * 4);
            }

            batchVertices.insert(batchVertices.end(), faceVertices.begin(), faceVertices.end());
        }
    }

    for (const auto &[batchKey, vertices] : batchVerticesByKey)
    {
        if (vertices.empty())
        {
            continue;
        }

        const auto textureNameIt = textureNameByBatchKey.find(batchKey);
        const auto bmodelIndexIt = bmodelIndexByBatchKey.find(batchKey);

        if (textureNameIt == textureNameByBatchKey.end() || bmodelIndexIt == bmodelIndexByBatchKey.end())
        {
            continue;
        }

        const std::string &textureName = textureNameIt->second;
        const size_t bmodelIndex = bmodelIndexIt->second;

        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> texturePixels =
            loadOutdoorBModelBitmapPixelsBgra(
                assetFileSystem,
                outdoorGeometry,
                textureName,
                textureWidth,
                textureHeight,
                bitmapLoadCache);

        if (!texturePixels || textureWidth <= 0 || textureHeight <= 0)
        {
            continue;
        }

        TexturedBatch batch = {};
        batch.vertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(vertices.data(), static_cast<uint32_t>(vertices.size() * sizeof(TexturedPreviewVertex))),
            TexturedPreviewVertex::ms_layout);
        batch.textureHandle = bgfx::createTexture2D(
            static_cast<uint16_t>(textureWidth),
            static_cast<uint16_t>(textureHeight),
            false,
            1,
            bgfx::TextureFormat::BGRA8,
            BGFX_SAMPLER_MIN_POINT
                | BGFX_SAMPLER_MAG_POINT
                | BGFX_SAMPLER_MIP_POINT,
            bgfx::copy(texturePixels->data(), static_cast<uint32_t>(texturePixels->size())));
        batch.vertexCount = static_cast<uint32_t>(vertices.size());
        batch.bmodelIndex = bmodelIndex;

        if (const auto originIt = previewOriginByBModel.find(bmodelIndex); originIt != previewOriginByBModel.end())
        {
            batch.objectOrigin = originIt->second;
        }

        if (bgfx::isValid(batch.vertexBufferHandle) && bgfx::isValid(batch.textureHandle))
        {
            m_bmodelTexturedBatches.push_back(batch);
        }
        else
        {
            if (bgfx::isValid(batch.vertexBufferHandle))
            {
                bgfx::destroy(batch.vertexBufferHandle);
            }

            if (bgfx::isValid(batch.textureHandle))
            {
                bgfx::destroy(batch.textureHandle);
            }
        }
    }

    const auto appendProceduralBatch =
        [](
            const std::unordered_map<size_t, std::vector<ProceduralPreviewVertex>> &verticesByBModel,
            const std::unordered_map<size_t, bx::Vec3> &originByBModel,
            std::vector<EditorOutdoorViewport::ProceduralBatch> &targetBatches)
    {
        for (const auto &[bmodelIndex, vertices] : verticesByBModel)
        {
            if (vertices.empty())
            {
                continue;
            }

            EditorOutdoorViewport::ProceduralBatch batch = {};
            batch.vertexBufferHandle = bgfx::createVertexBuffer(
                bgfx::copy(
                    vertices.data(),
                    static_cast<uint32_t>(vertices.size() * sizeof(EditorOutdoorViewport::ProceduralPreviewVertex))),
                EditorOutdoorViewport::ProceduralPreviewVertex::ms_layout);
            batch.vertexCount = static_cast<uint32_t>(vertices.size());
            batch.bmodelIndex = bmodelIndex;

            if (const auto originIt = originByBModel.find(bmodelIndex); originIt != originByBModel.end())
            {
                batch.objectOrigin = originIt->second;
            }

            if (bgfx::isValid(batch.vertexBufferHandle))
            {
                targetBatches.push_back(batch);
            }
        }
    };

    appendProceduralBatch(allFaceVerticesByBModel, previewOriginByBModel, m_bmodelAllFaceBatches);
    appendProceduralBatch(unassignedVerticesByBModel, previewOriginByBModel, m_bmodelUnassignedBatches);
    appendProceduralBatch(missingAssetVerticesByBModel, previewOriginByBModel, m_bmodelMissingAssetBatches);

    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();
    const std::optional<Mm9ModelRegistry> mm9ModelRegistry = loadMm9ModelRegistry(assetFileSystem);
    const Mm9ModelInstanceActorSourceLookup *pMm9ActorSourceLookup =
        cachedMm9ModelInstanceActorSourceLookup(assetFileSystem);
    std::unordered_map<std::string, std::vector<std::string>> modelSidecarTexturePathsByAsset;
    std::set<std::string> loggedModelWarnings;

    for (size_t modelInstanceIndex = 0; modelInstanceIndex < sceneData.modelInstances.size(); ++modelInstanceIndex)
    {
        const Game::OutdoorSceneModelInstance &modelInstance = sceneData.modelInstances[modelInstanceIndex];
        const Mm9ResolvedModelInstanceActorSource resolvedActorSource =
            resolveMm9ModelInstanceActorSource(
                modelInstance,
                pMm9ActorSourceLookup);
        Game::OutdoorSceneModelInstance resolvedModelInstance = modelInstance;
        resolvedModelInstance.sourceModel = resolvedActorSource.sourceModel;
        resolvedModelInstance.sourceSkin = resolvedActorSource.sourceSkin;
        std::vector<ProceduralPreviewVertex> vertices;
        const std::vector<EditorMm9RawObjectAssetReferenceStatus> *pRawObjectAssetStatuses =
            document.kind() == EditorDocument::Kind::Mm9Dat
                ? &document.mm9RawObjectAssetReferenceStatuses()
                : nullptr;
        const std::vector<std::string> modelSourceSkinPaths =
            sourceSkinTexturePathsForModelInstance(
                assetFileSystem,
                resolvedModelInstance,
                pRawObjectAssetStatuses);
        bool placeholder = false;
        std::optional<ResolvedModelInstanceAsset> modelAsset;

        modelAsset = resolveModelInstanceAsset(
            assetFileSystem,
            resolvedModelInstance,
            modelSourceSkinPaths,
            mm9ModelRegistry ? &*mm9ModelRegistry : nullptr,
            pRawObjectAssetStatuses);

        if (!modelAsset)
        {
            appendModelInstancePlaceholder(vertices, modelInstance);
            placeholder = true;

            const std::string warningKey = "missing:" + modelInstance.modelAsset;
            if (loggedModelWarnings.insert(warningKey).second)
            {
                session.logInfo(
                    "Warning: MM9 model instance asset is missing; showing placeholder: " + modelInstance.modelAsset);
            }
        }
        else
        {
            std::vector<ImportedModel> importedModels;
            std::string loadError;
            const auto cachedSidecarTexturePathsIt =
                modelSidecarTexturePathsByAsset.find(modelAsset->virtualPath);
            if (cachedSidecarTexturePathsIt == modelSidecarTexturePathsByAsset.end())
            {
                modelSidecarTexturePathsByAsset.emplace(
                    modelAsset->virtualPath,
                    loadModelSidecarTexturePaths(assetFileSystem, modelAsset->virtualPath));
            }
            const std::vector<std::string> &modelSidecarTexturePaths =
                modelSidecarTexturePathsByAsset.find(modelAsset->virtualPath)->second;

            if (loadImportedModelsFromFile(modelAsset->physicalPath, importedModels, loadError, false, false))
            {
                std::unordered_map<std::string, const ImportedModelMaterial *> materialByName;
                std::set<std::string> faceMaterialNames;

                for (const ImportedModel &importedModel : importedModels)
                {
                    for (const ImportedModelMaterial &material : importedModel.materials)
                    {
                        materialByName.emplace(material.name, &material);
                    }

                    for (const ImportedModelFace &face : importedModel.faces)
                    {
                        if (!face.materialName.empty())
                        {
                            faceMaterialNames.insert(face.materialName);
                        }
                    }
                }

                bool emittedTexturedBatch = false;

                for (const std::string &materialName : faceMaterialNames)
                {
                    const std::vector<TexturedPreviewVertex> texturedVertices =
                        buildTexturedModelInstanceVertices(importedModels, modelInstance, materialName);

                    if (texturedVertices.empty())
                    {
                        continue;
                    }

                    std::vector<uint8_t> texturePixels;
                    int textureWidth = 64;
                    int textureHeight = 64;
                    bool hasDecodedTexture = false;
                    bool textureHasTransparentPixels = false;
                    const auto materialIt = materialByName.find(materialName);

                    const std::optional<Engine::ImagePixelsBgra> sidecarTexture =
                        loadModelSidecarTexturePixels(
                            assetFileSystem,
                            modelSidecarTexturePaths,
                            modelSourceSkinPaths,
                            materialName,
                            bitmapLoadCache.binaryFilesByPath);

                    if (sidecarTexture
                        && sidecarTexture->width > 0
                        && sidecarTexture->height > 0
                        && !sidecarTexture->pixels.empty())
                    {
                        textureWidth = sidecarTexture->width;
                        textureHeight = sidecarTexture->height;
                        texturePixels = sidecarTexture->pixels;
                        hasDecodedTexture = true;
                        textureHasTransparentPixels = hasTransparentPixels(texturePixels);
                    }

                    if (!hasDecodedTexture && materialIt != materialByName.end() && materialIt->second != nullptr)
                    {
                        const ImportedModelMaterial &material = *materialIt->second;
                        const std::optional<Engine::ImagePixelsBgra> decodedTexture =
                            Engine::decodeImagePixelsBgra(
                                material.textureBytes,
                                material.textureLabel.empty() ? modelInstance.modelAsset : material.textureLabel);

                        if (decodedTexture
                            && decodedTexture->width > 0
                            && decodedTexture->height > 0
                            && !decodedTexture->pixels.empty())
                        {
                            textureWidth = decodedTexture->width;
                            textureHeight = decodedTexture->height;
                            texturePixels = decodedTexture->pixels;
                            hasDecodedTexture = true;
                            textureHasTransparentPixels = hasTransparentPixels(texturePixels);
                        }
                    }

                    if (!hasDecodedTexture)
                    {
                        const bool expectsTexture =
                            !modelSidecarTexturePaths.empty()
                            || !modelSourceSkinPaths.empty()
                            || (materialIt != materialByName.end()
                                && materialIt->second != nullptr
                                && (!materialIt->second->textureLabel.empty()
                                    || !materialIt->second->textureBytes.empty()));

                        if (expectsTexture)
                        {
                            texturePixels = makeMissingModelTexturePixels(textureWidth, textureHeight);
                            const std::string warningKey =
                                "texture:" + modelInstance.modelAsset + ":" + materialName;

                            if (loggedModelWarnings.insert(warningKey).second)
                            {
                                session.logInfo(
                                    "Warning: MM9 model instance texture is missing; showing placeholder texture: "
                                    + modelInstance.modelAsset + " material " + materialName);
                            }
                        }
                        else
                        {
                            texturePixels = makeUntexturedModelTexturePixels(textureWidth, textureHeight);
                            const std::string warningKey =
                                "untextured:" + modelInstance.modelAsset + ":" + materialName;

                            if (loggedModelWarnings.insert(warningKey).second)
                            {
                                session.logInfo(
                                    "Warning: MM9 model instance material has no texture binding; "
                                    "showing neutral material: "
                                    + modelInstance.modelAsset + " material " + materialName);
                            }
                        }
                    }

                    TexturedBatch batch = {};
                    batch.vertexBufferHandle = bgfx::createVertexBuffer(
                        bgfx::copy(
                            texturedVertices.data(),
                            static_cast<uint32_t>(texturedVertices.size() * sizeof(TexturedPreviewVertex))),
                        TexturedPreviewVertex::ms_layout);
                    batch.textureHandle = bgfx::createTexture2D(
                        static_cast<uint16_t>(textureWidth),
                        static_cast<uint16_t>(textureHeight),
                        false,
                        1,
                        bgfx::TextureFormat::BGRA8,
                        BGFX_SAMPLER_MIN_POINT
                            | BGFX_SAMPLER_MAG_POINT
                            | BGFX_SAMPLER_MIP_POINT,
                        bgfx::copy(texturePixels.data(), static_cast<uint32_t>(texturePixels.size())));
                    batch.vertexCount = static_cast<uint32_t>(texturedVertices.size());
                    batch.key = modelInstance.instanceId + "|" + materialName;
                    batch.objectOrigin = {
                        static_cast<float>(modelInstance.x),
                        static_cast<float>(modelInstance.y),
                        static_cast<float>(modelInstance.z)
                    };
                    batch.hasTransparentPixels = textureHasTransparentPixels;

                    if (bgfx::isValid(batch.vertexBufferHandle) && bgfx::isValid(batch.textureHandle))
                    {
                        m_modelInstanceTexturedBatches.push_back(batch);
                        emittedTexturedBatch = true;
                    }
                    else
                    {
                        if (bgfx::isValid(batch.vertexBufferHandle))
                        {
                            bgfx::destroy(batch.vertexBufferHandle);
                        }

                        if (bgfx::isValid(batch.textureHandle))
                        {
                            bgfx::destroy(batch.textureHandle);
                        }
                    }
                }

                if (!emittedTexturedBatch)
                {
                    vertices = buildModelInstanceVertices(importedModels, modelInstance);
                }
            }
            else
            {
                appendModelInstancePlaceholder(vertices, modelInstance);
                placeholder = true;

                const std::string warningKey = "load:" + modelInstance.modelAsset + ":" + loadError;
                if (loggedModelWarnings.insert(warningKey).second)
                {
                    session.logInfo(
                        "Warning: MM9 model instance asset could not be loaded; showing placeholder: "
                        + modelInstance.modelAsset + " (" + loadError + ")");
                }
            }
        }

        if (vertices.empty())
        {
            continue;
        }

        ProceduralBatch batch = {};
        batch.vertexBufferHandle = bgfx::createVertexBuffer(
            bgfx::copy(
                vertices.data(),
                static_cast<uint32_t>(vertices.size() * sizeof(ProceduralPreviewVertex))),
            ProceduralPreviewVertex::ms_layout);
        batch.vertexCount = static_cast<uint32_t>(vertices.size());
        batch.key = modelInstance.instanceId;
        batch.objectOrigin = {
            static_cast<float>(modelInstance.x),
            static_cast<float>(modelInstance.y),
            static_cast<float>(modelInstance.z)
        };

        if (!bgfx::isValid(batch.vertexBufferHandle))
        {
            continue;
        }

        if (!placeholder)
        {
            m_modelInstanceBatches.push_back(batch);
        }
        else
        {
            m_modelInstanceMissingBatches.push_back(batch);
        }
    }

}

void EditorOutdoorViewport::updateCamera(
    const EditorDocument &document,
    bool isHovered,
    bool isFocused,
    float deltaSeconds)
{
    const std::string cameraDocumentKey = documentCameraKey(document);

    if (cameraDocumentKey != m_cameraDocumentKey)
    {
        m_cameraDocumentKey = cameraDocumentKey;
        m_cameraInitializedForDocument = false;
        m_activeCameraFocus.active = false;
        m_activeGizmoDrag = {};
    }

    if (!m_cameraInitializedForDocument)
    {
        resetCameraToDocument(document);
    }

    if (m_activeCameraFocus.active)
    {
        m_activeCameraFocus.progressSeconds += deltaSeconds;
        const float normalizedT = std::clamp(
            m_activeCameraFocus.progressSeconds / std::max(m_activeCameraFocus.durationSeconds, 0.0001f),
            0.0f,
            1.0f);
        const float easedT = easeOutCubic(normalizedT);
        m_cameraPosition = vecLerp(m_activeCameraFocus.startPosition, m_activeCameraFocus.targetPosition, easedT);
        m_cameraYawRadians = wrapAngleRadians(
            m_activeCameraFocus.startYawRadians
            + shortestAngleDelta(m_activeCameraFocus.startYawRadians, m_activeCameraFocus.targetYawRadians) * easedT);
        m_cameraPitchRadians = lerpFloat(
            m_activeCameraFocus.startPitchRadians,
            m_activeCameraFocus.targetPitchRadians,
            easedT);

        if (normalizedT >= 1.0f)
        {
            m_activeCameraFocus.active = false;
        }
    }

    if (!isHovered && !isFocused)
    {
        return;
    }

    ImGuiIO &io = ImGui::GetIO();

    if (isHovered && ImGui::IsMouseDown(ImGuiMouseButton_Right))
    {
        m_activeCameraFocus.active = false;
        m_cameraYawRadians += io.MouseDelta.x * CameraMouseSensitivity;
        m_cameraPitchRadians -= io.MouseDelta.y * CameraMouseSensitivity;
        m_cameraPitchRadians = std::clamp(m_cameraPitchRadians, CameraMinPitchRadians, CameraMaxPitchRadians);
    }

    if (!ImGui::IsMouseDown(ImGuiMouseButton_Right))
    {
        return;
    }

    const float baseMoveSpeed =
        CameraMoveSpeed
        * (document.kind() == EditorDocument::Kind::Indoor ? IndoorCameraMoveSpeedMultiplier : 1.0f);
    const float moveSpeed =
        baseMoveSpeed
        * ((ImGui::IsKeyDown(ImGuiKey_LeftShift) || ImGui::IsKeyDown(ImGuiKey_RightShift))
               ? CameraFastMoveSpeedMultiplier
               : 1.0f)
        * deltaSeconds;
    const bx::Vec3 forward = {
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    };
    const bx::Vec3 right = {
        std::cos(m_cameraYawRadians),
        -std::sin(m_cameraYawRadians),
        0.0f
    };

    if (ImGui::IsKeyDown(ImGuiKey_W))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.x += forward.x * moveSpeed;
        m_cameraPosition.y += forward.y * moveSpeed;
        m_cameraPosition.z += forward.z * moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_S))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.x -= forward.x * moveSpeed;
        m_cameraPosition.y -= forward.y * moveSpeed;
        m_cameraPosition.z -= forward.z * moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_A))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.x -= right.x * moveSpeed;
        m_cameraPosition.y -= right.y * moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_D))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.x += right.x * moveSpeed;
        m_cameraPosition.y += right.y * moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_Q))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.z -= moveSpeed;
    }

    if (ImGui::IsKeyDown(ImGuiKey_E))
    {
        m_activeCameraFocus.active = false;
        m_cameraPosition.z += moveSpeed;
    }
}

void EditorOutdoorViewport::ensureImportedModelPreview(const EditorSession &session)
{
    if (!m_importedModelPreviewRequest || !session.hasDocument() || session.document().kind() != EditorDocument::Kind::Outdoor)
    {
        destroyImportedModelPreview();
        return;
    }

    const ImportedModelPreviewRequest &request = *m_importedModelPreviewRequest;
    const EditorDocument &document = session.document();
    const std::string trimmedPath = request.sourcePath;

    if (trimmedPath.empty() || request.importScale <= 0.0f)
    {
        destroyImportedModelPreview();
        return;
    }

    std::string placementKey = request.sourcePath
        + "|mesh=" + request.sourceMeshName
        + "|scale=" + std::to_string(request.importScale)
        + "|merge=" + std::to_string(request.mergeCoplanarFaces ? 1 : 0)
        + "|target=" + std::to_string(static_cast<int>(request.targetMode))
        + "|doc=" + documentGeometryKey(document);
    std::optional<Game::OutdoorBModel> previewBModel;

    if (request.targetMode == ImportedModelPreviewRequest::TargetMode::ReplaceSelectedBModel)
    {
        const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();

        if (request.bmodelIndex >= outdoorGeometry.bmodels.size())
        {
            destroyImportedModelPreview();
            return;
        }

        ImportedModel importedModel = {};
        std::string errorMessage;

        if (!loadImportedModelFromFile(
                std::filesystem::absolute(trimmedPath),
                importedModel,
                errorMessage,
                request.sourceMeshName,
                request.mergeCoplanarFaces))
        {
            destroyImportedModelPreview();
            return;
        }

        const Game::OutdoorBModel &placementTemplate = outdoorGeometry.bmodels[request.bmodelIndex];
        const std::optional<EditorBModelSourceTransform> sourceTransform =
            document.outdoorBModelSourceTransform(request.bmodelIndex);
        previewBModel = buildImportedPreviewBModel(
            importedModel,
            request.importScale,
            &placementTemplate,
            sourceTransform ? &*sourceTransform : nullptr,
            nullptr);
        placementKey += "|bmodel=" + std::to_string(request.bmodelIndex);
    }
    else
    {
        ImportedModel importedModel = {};
        std::string errorMessage;

        if (!loadImportedModelFromFile(
                std::filesystem::absolute(trimmedPath),
                importedModel,
                errorMessage,
                request.sourceMeshName,
                request.mergeCoplanarFaces))
        {
            destroyImportedModelPreview();
            return;
        }

        bx::Vec3 floorPoint = {0.0f, 0.0f, 0.0f};
        const float sampleMouseX =
            m_isHovered
            ? m_lastMouseX
            : static_cast<float>(m_viewportX) + static_cast<float>(m_viewportWidth) * 0.5f;
        const float sampleMouseY =
            m_isHovered
            ? m_lastMouseY
            : static_cast<float>(m_viewportY) + static_cast<float>(m_viewportHeight) * 0.5f;

        if (!sampleTerrainWorldPosition(document, sampleMouseX, sampleMouseY, floorPoint))
        {
            destroyImportedModelPreview();
            return;
        }

        if (m_snapEnabled)
        {
            const int snapStep = std::max(m_snapStep, 1);
            floorPoint.x =
                static_cast<float>(static_cast<int>(std::lround(floorPoint.x / static_cast<float>(snapStep))) * snapStep);
            floorPoint.y =
                static_cast<float>(static_cast<int>(std::lround(floorPoint.y / static_cast<float>(snapStep))) * snapStep);
            floorPoint.z =
                static_cast<float>(static_cast<int>(std::lround(floorPoint.z / static_cast<float>(snapStep))) * snapStep);
        }

        previewBModel = buildImportedPreviewBModel(importedModel, request.importScale, nullptr, nullptr, &floorPoint);
        placementKey += "|floor=" + std::to_string(static_cast<int>(std::lround(floorPoint.x)))
            + "," + std::to_string(static_cast<int>(std::lround(floorPoint.y)))
            + "," + std::to_string(static_cast<int>(std::lround(floorPoint.z)));
    }

    if (!previewBModel)
    {
        destroyImportedModelPreview();
        return;
    }

    if (placementKey == m_importedModelPreviewKey && bgfx::isValid(m_importedModelPreviewBatch.vertexBufferHandle))
    {
        return;
    }

    destroyImportedModelPreview();
    const bx::Vec3 previewOrigin = {
        static_cast<float>(previewBModel->boundingCenterX),
        static_cast<float>(previewBModel->boundingCenterY),
        static_cast<float>(previewBModel->boundingCenterZ)
    };
    std::vector<ProceduralPreviewVertex> previewVertices;

    for (size_t faceIndex = 0; faceIndex < previewBModel->faces.size(); ++faceIndex)
    {
        std::vector<ProceduralPreviewVertex> faceVertices =
            buildProceduralBModelFaceVertices(*previewBModel, faceIndex, previewOrigin);
        previewVertices.insert(previewVertices.end(), faceVertices.begin(), faceVertices.end());
    }

    if (previewVertices.empty())
    {
        return;
    }

    m_importedModelPreviewBatch.vertexBufferHandle = bgfx::createVertexBuffer(
        bgfx::copy(
            previewVertices.data(),
            static_cast<uint32_t>(previewVertices.size() * sizeof(ProceduralPreviewVertex))),
        ProceduralPreviewVertex::ms_layout);
    m_importedModelPreviewBatch.vertexCount = static_cast<uint32_t>(previewVertices.size());
    m_importedModelPreviewBatch.objectOrigin = previewOrigin;
    m_importedModelPreviewKey = placementKey;
}

void EditorOutdoorViewport::resetCameraToDocument(const EditorDocument &document)
{
    if (document.kind() == EditorDocument::Kind::Mm9Dat && document.hasMm9DatWorld())
    {
        const Game::Mm9DatCameraFrame cameraFrame =
            Game::frameMm9DatRenderBoundsCamera(document.mm9DatRenderBounds(), CameraVerticalFovDegrees);

        if (cameraFrame.valid)
        {
            m_cameraPosition = {
                cameraFrame.position.x,
                cameraFrame.position.y,
                cameraFrame.position.z
            };
            const bx::Vec3 toTarget = {
                cameraFrame.target.x - cameraFrame.position.x,
                cameraFrame.target.y - cameraFrame.position.y,
                cameraFrame.target.z - cameraFrame.position.z
            };
            const float planarLength = std::sqrt(toTarget.x * toTarget.x + toTarget.y * toTarget.y);
            m_cameraYawRadians = std::atan2(toTarget.x, toTarget.y);
            m_cameraPitchRadians = std::clamp(
                std::atan2(toTarget.z, std::max(planarLength, 0.001f)),
                CameraMinPitchRadians,
                CameraMaxPitchRadians);
            m_cameraInitializedForDocument = true;
            return;
        }
    }

    m_cameraPosition = {0.0f, 0.0f, 5000.0f};
    m_cameraYawRadians = -300.0f * bx::kPi / 180.0f;
    m_cameraPitchRadians = -0.35f;
    m_cameraInitializedForDocument = true;
}

bool EditorOutdoorViewport::tryPick(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!leftMouseClicked || !m_isHovered || !session.hasDocument() || m_placementKind != EditorSelectionKind::None)
    {
        return false;
    }

    const float localMouseX = mouseX - static_cast<float>(m_viewportX);
    const float localMouseY = mouseY - static_cast<float>(m_viewportY);
    const bx::Vec3 forward = vecNormalize({
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    });
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    const bx::Vec3 cameraRight = vecNormalize(vecCross(forward, worldUp));
    const bx::Vec3 cameraUp = vecNormalize(vecCross(cameraRight, forward));
    float bestScore = FLT_MAX;
    EditorSelectionKind bestKind = EditorSelectionKind::None;
    size_t bestIndex = 0;

    for (const MarkerCandidate &candidate : m_markerCandidates)
    {
        float projectedX = 0.0f;
        float projectedY = 0.0f;
        float clipW = 0.0f;

        if (!projectWorldPoint(
                candidate.worldPosition,
                m_viewProjectionMatrix,
                m_viewportWidth,
                m_viewportHeight,
                projectedX,
                projectedY,
                clipW))
        {
            continue;
        }

        bool hit = false;
        float score = FLT_MAX;

        if (candidate.hasBillboardBounds)
        {
            const float halfWidth = candidate.billboardWorldWidth * 0.5f;
            const float halfHeight = candidate.billboardWorldHeight * 0.5f;
            const bx::Vec3 right = vecScale(cameraRight, halfWidth);
            const bx::Vec3 up = vecScale(cameraUp, halfHeight);
            const std::array<bx::Vec3, 4> corners = {{
                {
                    candidate.worldPosition.x - right.x - up.x,
                    candidate.worldPosition.y - right.y - up.y,
                    candidate.worldPosition.z - right.z - up.z
                },
                {
                    candidate.worldPosition.x - right.x + up.x,
                    candidate.worldPosition.y - right.y + up.y,
                    candidate.worldPosition.z - right.z + up.z
                },
                {
                    candidate.worldPosition.x + right.x + up.x,
                    candidate.worldPosition.y + right.y + up.y,
                    candidate.worldPosition.z + right.z + up.z
                },
                {
                    candidate.worldPosition.x + right.x - up.x,
                    candidate.worldPosition.y + right.y - up.y,
                    candidate.worldPosition.z + right.z - up.z
                }
            }};

            float minX = FLT_MAX;
            float minY = FLT_MAX;
            float maxX = -FLT_MAX;
            float maxY = -FLT_MAX;
            bool validBounds = true;

            for (const bx::Vec3 &corner : corners)
            {
                float cornerX = 0.0f;
                float cornerY = 0.0f;
                float cornerW = 0.0f;

                if (!projectWorldPoint(
                        corner,
                        m_viewProjectionMatrix,
                        m_viewportWidth,
                        m_viewportHeight,
                        cornerX,
                        cornerY,
                        cornerW))
                {
                    validBounds = false;
                    break;
                }

                minX = std::min(minX, cornerX);
                minY = std::min(minY, cornerY);
                maxX = std::max(maxX, cornerX);
                maxY = std::max(maxY, cornerY);
            }

            if (validBounds)
            {
                constexpr float hitPaddingPixels = 4.0f;
                minX -= hitPaddingPixels;
                minY -= hitPaddingPixels;
                maxX += hitPaddingPixels;
                maxY += hitPaddingPixels;

                if (localMouseX >= minX && localMouseX <= maxX && localMouseY >= minY && localMouseY <= maxY)
                {
                    const float centerX = (minX + maxX) * 0.5f;
                    const float centerY = (minY + maxY) * 0.5f;
                    const float deltaX = centerX - localMouseX;
                    const float deltaY = centerY - localMouseY;
                    hit = true;
                    score = deltaX * deltaX + deltaY * deltaY + clipW * 0.01f;
                }
            }
        }

        if (!hit)
        {
            const float deltaX = projectedX - localMouseX;
            const float deltaY = projectedY - localMouseY;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY;
            const float threshold = candidate.pickRadiusPixels * candidate.pickRadiusPixels;

            if (distanceSquared > threshold)
            {
                continue;
            }

            hit = true;
            score = distanceSquared + clipW * 0.01f;
        }

        if (hit && score < bestScore)
        {
            bestScore = score;
            bestKind = candidate.selectionKind;
            bestIndex = candidate.selectionIndex;
        }
    }

    if (bestKind != EditorSelectionKind::None)
    {
        session.select(bestKind, bestIndex);
        return true;
    }

    if (session.document().kind() == EditorDocument::Kind::Indoor)
    {
        bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
        bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

        if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection))
        {
            return false;
        }

        const Game::IndoorMapData &indoorGeometry = session.document().indoorGeometry();
        const std::vector<Game::IndoorVertex> &indoorVertices = indoorRenderVertices(session.document());
        float bestDistance = std::numeric_limits<float>::max();
        size_t bestFaceIndex = std::numeric_limits<size_t>::max();

        for (size_t faceIndex = 0; faceIndex < indoorGeometry.faces.size(); ++faceIndex)
        {
            if (indoorFaceHiddenByCeilingView(
                    indoorGeometry,
                    indoorVertices,
                    faceIndex,
                    m_showIndoorFloors,
                    m_showIndoorCeilings,
                    m_isolatedIndoorRoomId))
            {
                continue;
            }

            Game::IndoorFaceGeometryData geometry = {};

            if (!Game::buildIndoorFaceGeometry(indoorGeometry, indoorVertices, faceIndex, geometry)
                || geometry.vertices.size() < 3)
            {
                continue;
            }

            for (size_t triangleIndex = 1; triangleIndex + 1 < geometry.vertices.size(); ++triangleIndex)
            {
                float distance = 0.0f;

                if (!intersectRayTriangle(
                        rayOrigin,
                        rayDirection,
                        geometry.vertices[0],
                        geometry.vertices[triangleIndex],
                        geometry.vertices[triangleIndex + 1],
                        distance))
                {
                    continue;
                }

                if (distance < bestDistance)
                {
                    bestDistance = distance;
                    bestFaceIndex = faceIndex;
                }
            }
        }

        if (bestFaceIndex != std::numeric_limits<size_t>::max())
        {
            session.select(EditorSelectionKind::InteractiveFace, bestFaceIndex);
            return true;
        }

        return false;
    }

    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection))
    {
        return false;
    }

    const EditorDocument &document = session.document();

    if (document.kind() == EditorDocument::Kind::Mm9Dat)
    {
        if (!document.hasMm9DatWorld())
        {
            return false;
        }

        const Game::Mm9DatPickRay ray = {
            {rayOrigin.x, rayOrigin.y, rayOrigin.z},
            {rayDirection.x, rayDirection.y, rayDirection.z}};
        const std::optional<Game::Mm9DatRenderMeshPickHit> hit =
            Game::pickMm9DatRenderMesh(document.mm9DatRenderMesh(), ray);

        if (hit)
        {
            session.select(EditorSelectionKind::Mm9DatPolygon, hit->triangleIndex);
            return true;
        }

        return false;
    }

    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const bx::Vec3 segmentEnd = {
        rayOrigin.x + rayDirection.x * CameraFarPlane,
        rayOrigin.y + rayDirection.y * CameraFarPlane,
        rayOrigin.z + rayDirection.z * CameraFarPlane
    };
    float bestIntersectionFactor = std::numeric_limits<float>::max();
    size_t bestBModelIndex = 0;
    bool foundBModelHit = false;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            Game::OutdoorFaceGeometryData geometry = {};

            if (!Game::buildOutdoorFaceGeometry(
                    bmodel,
                    bmodelIndex,
                    bmodel.faces[faceIndex],
                    faceIndex,
                    geometry,
                    true))
            {
                continue;
            }

            float intersectionFactor = 0.0f;
            bx::Vec3 intersectionPoint = {0.0f, 0.0f, 0.0f};

            if (!Game::intersectOutdoorSegmentWithFace(
                    geometry,
                    rayOrigin,
                    segmentEnd,
                    intersectionFactor,
                    intersectionPoint))
            {
                continue;
            }

            if (!foundBModelHit || intersectionFactor < bestIntersectionFactor)
            {
                bestIntersectionFactor = intersectionFactor;
                bestBModelIndex = bmodelIndex;
                foundBModelHit = true;
            }
        }
    }

    if (foundBModelHit)
    {
        session.select(EditorSelectionKind::BModel, bestBModelIndex);
        return true;
    }

    return false;
}

void EditorOutdoorViewport::finishTerrainStroke(EditorSession &session)
{
    if (m_activeTerrainPaint.active)
    {
        if (session.hasDocument()
            && session.terrainPaintEnabled()
            && session.terrainPaintMode() == EditorTerrainPaintMode::Rectangle
            && m_activeTerrainPaint.anchorCellX != std::numeric_limits<int>::min()
            && m_activeTerrainPaint.lastCellX != std::numeric_limits<int>::min())
        {
            Game::OutdoorMapData &outdoorGeometry = session.document().mutableOutdoorGeometry();

            if (applyTerrainPaintRectangle(
                    outdoorGeometry,
                    m_activeTerrainPaint.anchorCellX,
                    m_activeTerrainPaint.anchorCellY,
                    m_activeTerrainPaint.lastCellX,
                    m_activeTerrainPaint.lastCellY,
                    session.terrainPaintTileId()))
            {
                session.document().setDirty(true);
                session.document().touchSceneRevision();
                m_geometryKey.clear();
                m_activeTerrainPaint.mutated = true;
            }
        }

        if (m_activeTerrainPaint.mutated)
        {
            session.noteDocumentMutated({});
        }

        m_activeTerrainPaint = {};
    }

    if (m_activeTerrainSculpt.active)
    {
        if (session.hasDocument()
            && session.terrainSculptEnabled()
            && session.terrainSculptMode() == EditorTerrainSculptMode::Ramp
            && m_activeTerrainSculpt.anchorSampleX != std::numeric_limits<int>::min()
            && m_activeTerrainSculpt.lastSampleX != std::numeric_limits<int>::min())
        {
            Game::OutdoorMapData &outdoorGeometry = session.document().mutableOutdoorGeometry();
            const size_t endSampleIndex =
                flattenTerrainCellIndex(m_activeTerrainSculpt.lastSampleX, m_activeTerrainSculpt.lastSampleY);

            if (endSampleIndex < outdoorGeometry.heightMap.size()
                && applyTerrainRampBrush(
                    outdoorGeometry,
                    m_activeTerrainSculpt.anchorSampleX,
                    m_activeTerrainSculpt.anchorSampleY,
                    m_activeTerrainSculpt.lastSampleX,
                    m_activeTerrainSculpt.lastSampleY,
                    m_activeTerrainSculpt.anchorHeight,
                    outdoorGeometry.heightMap[endSampleIndex],
                    std::max(session.terrainSculptRadius(), 0),
                    std::max(session.terrainSculptStrength(), 1),
                    session.terrainSculptFalloffMode()))
            {
                recalculateOutdoorHeightRange(outdoorGeometry);
                session.document().setDirty(true);
                session.document().touchSceneRevision();
                m_geometryKey.clear();
                m_activeTerrainSculpt.mutated = true;
            }
        }

        if (m_activeTerrainSculpt.mutated)
        {
            session.noteDocumentMutated({});
        }

        m_activeTerrainSculpt = {};
    }
}

bool EditorOutdoorViewport::trySelectTerrainCell(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!m_isHovered || m_placementKind != EditorSelectionKind::Terrain || !session.hasDocument())
    {
        m_hoverTerrainValid = false;
        finishTerrainStroke(session);
        return false;
    }

    const ImGuiIO &io = ImGui::GetIO();
    const bool leftMouseDown = io.MouseDown[0];

    if (!leftMouseDown && (m_activeTerrainPaint.active || m_activeTerrainSculpt.active))
    {
        finishTerrainStroke(session);
    }

    bx::Vec3 worldPosition = {0.0f, 0.0f, 0.0f};

    if (!sampleTerrainWorldPosition(session.document(), mouseX, mouseY, worldPosition))
    {
        m_hoverTerrainValid = false;
        return false;
    }

    const int cellX = std::clamp(
        static_cast<int>(std::floor(Game::outdoorWorldToGridXFloat(worldPosition.x))),
        0,
        Game::OutdoorMapData::TerrainWidth - 1);
    const int cellY = std::clamp(
        static_cast<int>(std::floor(Game::outdoorWorldToGridYFloat(worldPosition.y))),
        0,
        Game::OutdoorMapData::TerrainHeight - 1);
    const int sampleX = std::clamp(
        static_cast<int>(std::round(Game::outdoorWorldToGridXFloat(worldPosition.x))),
        0,
        Game::OutdoorMapData::TerrainWidth - 1);
    const int sampleY = std::clamp(
        static_cast<int>(std::round(Game::outdoorWorldToGridYFloat(worldPosition.y))),
        0,
        Game::OutdoorMapData::TerrainHeight - 1);
    m_hoverTerrainValid = true;
    m_hoverTerrainCellX = cellX;
    m_hoverTerrainCellY = cellY;
    const size_t flatIndex = flattenTerrainCellIndex(cellX, cellY);

    const bool sculptEnabled = session.terrainSculptEnabled();
    const bool paintEnabled = session.terrainPaintEnabled() && !sculptEnabled;
    const EditorTerrainPaintMode paintMode = session.terrainPaintMode();
    Game::OutdoorMapData &outdoorGeometry = session.document().mutableOutdoorGeometry();

    if (io.KeyAlt
        && leftMouseClicked
        && sculptEnabled
        && session.terrainSculptMode() == EditorTerrainSculptMode::Flatten)
    {
        const size_t sampleIndex = flattenTerrainCellIndex(sampleX, sampleY);

        if (sampleIndex < outdoorGeometry.heightMap.size())
        {
            session.setTerrainFlattenTargetMode(EditorTerrainFlattenTargetMode::Sampled);
            session.setTerrainFlattenSampledTargetHeight(outdoorGeometry.heightMap[sampleIndex]);
            session.select(EditorSelectionKind::Terrain, flatIndex);
        }

        return true;
    }

    if ((!paintEnabled && !sculptEnabled) || !leftMouseDown)
    {
        if (leftMouseClicked)
        {
            session.select(EditorSelectionKind::Terrain, flatIndex);
        }

        return leftMouseClicked;
    }

    session.select(EditorSelectionKind::Terrain, flatIndex);

    if (paintEnabled && paintMode == EditorTerrainPaintMode::Fill)
    {
        if (!leftMouseClicked)
        {
            return true;
        }

        session.captureUndoSnapshot();

        if (applyTerrainPaintFill(outdoorGeometry, cellX, cellY, session.terrainPaintTileId()))
        {
            session.document().setDirty(true);
            session.document().touchSceneRevision();
            m_geometryKey.clear();
            session.noteDocumentMutated({});
        }

        return true;
    }

    if (sculptEnabled)
    {
        if (!m_activeTerrainSculpt.active)
        {
            if (!leftMouseClicked)
            {
                return true;
            }

            session.captureUndoSnapshot();
            m_activeTerrainSculpt.active = true;
            m_activeTerrainSculpt.anchorSampleX = sampleX;
            m_activeTerrainSculpt.anchorSampleY = sampleY;
            const size_t anchorSampleIndex = flattenTerrainCellIndex(sampleX, sampleY);
            m_activeTerrainSculpt.anchorHeight =
                anchorSampleIndex < outdoorGeometry.heightMap.size() ? outdoorGeometry.heightMap[anchorSampleIndex] : 0;
            m_activeTerrainSculpt.lastSampleX = std::numeric_limits<int>::min();
            m_activeTerrainSculpt.lastSampleY = std::numeric_limits<int>::min();
            m_activeTerrainSculpt.hasFlattenTargetHeight = false;
            m_activeTerrainSculpt.mutated = false;
        }

        if (sampleX == m_activeTerrainSculpt.lastSampleX && sampleY == m_activeTerrainSculpt.lastSampleY)
        {
            return true;
        }

        const int radius = std::max(session.terrainSculptRadius(), 0);
        const int strength = std::max(session.terrainSculptStrength(), 1);
        bool mutated = false;
        const EditorTerrainFalloffMode falloffMode = session.terrainSculptFalloffMode();
        const EditorTerrainSculptMode sculptMode = session.terrainSculptMode();

        if (sculptMode == EditorTerrainSculptMode::Flatten && !m_activeTerrainSculpt.hasFlattenTargetHeight)
        {
            if (session.terrainFlattenTargetMode() == EditorTerrainFlattenTargetMode::Numeric)
            {
                m_activeTerrainSculpt.flattenTargetHeight = session.terrainFlattenTargetHeight();
                m_activeTerrainSculpt.hasFlattenTargetHeight = true;
            }
            else if (session.hasTerrainFlattenSampledTarget())
            {
                m_activeTerrainSculpt.flattenTargetHeight = session.terrainFlattenTargetHeight();
                m_activeTerrainSculpt.hasFlattenTargetHeight = true;
            }
            else
            {
                const size_t flattenTargetIndex = flattenTerrainCellIndex(sampleX, sampleY);

                if (flattenTargetIndex < outdoorGeometry.heightMap.size())
                {
                    m_activeTerrainSculpt.flattenTargetHeight = outdoorGeometry.heightMap[flattenTargetIndex];
                    m_activeTerrainSculpt.hasFlattenTargetHeight = true;
                    session.setTerrainFlattenSampledTargetHeight(m_activeTerrainSculpt.flattenTargetHeight);
                }
            }
        }

        if (sculptMode == EditorTerrainSculptMode::Ramp)
        {
            m_activeTerrainSculpt.lastSampleX = sampleX;
            m_activeTerrainSculpt.lastSampleY = sampleY;
            return true;
        }

        if (m_activeTerrainSculpt.lastSampleX == std::numeric_limits<int>::min())
        {
            if (sculptMode == EditorTerrainSculptMode::Flatten)
            {
                mutated = applyTerrainFlattenBrush(
                    outdoorGeometry,
                    sampleX,
                    sampleY,
                    radius,
                    strength,
                    m_activeTerrainSculpt.flattenTargetHeight,
                    falloffMode);
            }
            else if (sculptMode == EditorTerrainSculptMode::Smooth)
            {
                mutated = applyTerrainSmoothBrush(
                    outdoorGeometry,
                    sampleX,
                    sampleY,
                    radius,
                    strength,
                    falloffMode);
            }
            else if (sculptMode == EditorTerrainSculptMode::Noise)
            {
                mutated = applyTerrainNoiseBrush(
                    outdoorGeometry,
                    sampleX,
                    sampleY,
                    radius,
                    strength,
                    falloffMode);
            }
            else
            {
                const int signedStrength = sculptMode == EditorTerrainSculptMode::Lower ? -strength : strength;
                mutated = applyTerrainSculptBrush(
                    outdoorGeometry,
                    sampleX,
                    sampleY,
                    radius,
                    signedStrength,
                    falloffMode);
            }
        }
        else
        {
            rasterizeTerrainLine(
                m_activeTerrainSculpt.lastSampleX,
                m_activeTerrainSculpt.lastSampleY,
                sampleX,
                sampleY,
                [&](int stepX, int stepY)
                {
                    if (sculptMode == EditorTerrainSculptMode::Flatten)
                    {
                        mutated = applyTerrainFlattenBrush(
                            outdoorGeometry,
                            stepX,
                            stepY,
                            radius,
                            strength,
                            m_activeTerrainSculpt.flattenTargetHeight,
                            falloffMode)
                            || mutated;
                    }
                    else if (sculptMode == EditorTerrainSculptMode::Smooth)
                    {
                        mutated = applyTerrainSmoothBrush(
                            outdoorGeometry,
                            stepX,
                            stepY,
                            radius,
                            strength,
                            falloffMode)
                            || mutated;
                    }
                    else if (sculptMode == EditorTerrainSculptMode::Noise)
                    {
                        mutated = applyTerrainNoiseBrush(
                            outdoorGeometry,
                            stepX,
                            stepY,
                            radius,
                            strength,
                            falloffMode)
                            || mutated;
                    }
                    else
                    {
                        const int signedStrength = sculptMode == EditorTerrainSculptMode::Lower ? -strength : strength;
                        mutated = applyTerrainSculptBrush(
                            outdoorGeometry,
                            stepX,
                            stepY,
                            radius,
                            signedStrength,
                            falloffMode)
                            || mutated;
                    }
                });
        }

        if (mutated)
        {
            recalculateOutdoorHeightRange(outdoorGeometry);
            session.document().setDirty(true);
            session.document().touchSceneRevision();
            m_geometryKey.clear();
            m_activeTerrainSculpt.mutated = true;
        }

        m_activeTerrainSculpt.lastSampleX = sampleX;
        m_activeTerrainSculpt.lastSampleY = sampleY;
        return true;
    }

    if (!m_activeTerrainPaint.active)
    {
        if (!leftMouseClicked)
        {
            return true;
        }

        session.captureUndoSnapshot();
        m_activeTerrainPaint.active = true;
        m_activeTerrainPaint.lastFlatIndex = std::numeric_limits<size_t>::max();
        m_activeTerrainPaint.anchorCellX = cellX;
        m_activeTerrainPaint.anchorCellY = cellY;
        m_activeTerrainPaint.lastCellX = cellX;
        m_activeTerrainPaint.lastCellY = cellY;
        m_activeTerrainPaint.mutated = false;
    }

    if (paintMode == EditorTerrainPaintMode::Rectangle)
    {
        m_activeTerrainPaint.lastCellX = cellX;
        m_activeTerrainPaint.lastCellY = cellY;
        return true;
    }

    const uint8_t tileId = session.terrainPaintTileId();
    const int brushRadius = std::max(session.terrainPaintRadius(), 0);
    bool mutated = false;

    if (paintMode == EditorTerrainPaintMode::Brush)
    {
        if (m_activeTerrainPaint.lastCellX == std::numeric_limits<int>::min())
        {
            mutated = applyTerrainPaintBrush(
                outdoorGeometry,
                cellX,
                cellY,
                brushRadius,
                tileId,
                session.terrainPaintEdgeNoise());
        }
        else
        {
            rasterizeTerrainLine(
                m_activeTerrainPaint.lastCellX,
                m_activeTerrainPaint.lastCellY,
                cellX,
                cellY,
                [&](int stepX, int stepY)
                {
                    mutated = applyTerrainPaintBrush(
                                  outdoorGeometry,
                                  stepX,
                                  stepY,
                                  brushRadius,
                                  tileId,
                                  session.terrainPaintEdgeNoise())
                        || mutated;
                });
        }
    }
    else
    {
        if (flatIndex < outdoorGeometry.tileMap.size() && outdoorGeometry.tileMap[flatIndex] != tileId)
        {
            outdoorGeometry.tileMap[flatIndex] = tileId;
            recalculateOutdoorTileUsage(outdoorGeometry);
            mutated = true;
        }
    }

    if (mutated)
    {
        session.document().setDirty(true);
        session.document().touchSceneRevision();
        m_geometryKey.clear();
        m_activeTerrainPaint.mutated = true;
    }

    m_activeTerrainPaint.lastFlatIndex = flatIndex;
    m_activeTerrainPaint.lastCellX = cellX;
    m_activeTerrainPaint.lastCellY = cellY;
    return true;
}

bool EditorOutdoorViewport::trySelectInteractiveFace(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!leftMouseClicked
        || !m_isHovered
        || m_placementKind != EditorSelectionKind::InteractiveFace
        || !session.hasDocument())
    {
        return false;
    }

    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection))
    {
        return false;
    }

    const EditorDocument &document = session.document();

    if (document.kind() == EditorDocument::Kind::Indoor)
    {
        const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
        const std::vector<Game::IndoorVertex> &indoorVertices = indoorRenderVertices(document);
        Game::IndoorFaceGeometryCache &facePickGeometryCache = indoorRenderFaceGeometryCache(document);
        float bestDistance = std::numeric_limits<float>::max();
        size_t bestFaceIndex = std::numeric_limits<size_t>::max();

        for (size_t faceIndex = 0; faceIndex < indoorGeometry.faces.size(); ++faceIndex)
        {
            if (indoorFaceHiddenByCeilingView(
                    indoorGeometry,
                    indoorVertices,
                    faceIndex,
                    m_showIndoorFloors,
                    m_showIndoorCeilings,
                    m_isolatedIndoorRoomId,
                    &facePickGeometryCache))
            {
                continue;
            }

            const Game::IndoorFaceGeometryData *pGeometry =
                facePickGeometryCache.geometryForFace(indoorGeometry, indoorVertices, faceIndex);

            if (pGeometry == nullptr || pGeometry->vertices.size() < 3)
            {
                continue;
            }

            for (size_t triangleIndex = 1; triangleIndex + 1 < pGeometry->vertices.size(); ++triangleIndex)
            {
                float distance = 0.0f;

                if (!intersectRayTriangle(
                        rayOrigin,
                        rayDirection,
                        pGeometry->vertices[0],
                        pGeometry->vertices[triangleIndex],
                        pGeometry->vertices[triangleIndex + 1],
                        distance))
                {
                    continue;
                }

                if (distance < bestDistance)
                {
                    bestDistance = distance;
                    bestFaceIndex = faceIndex;
                }
            }
        }

        if (bestFaceIndex == std::numeric_limits<size_t>::max())
        {
            return false;
        }

        if (m_indoorDoorFaceEditMode != IndoorDoorFaceEditMode::None
            && m_indoorDoorFaceEditDoorIndex.has_value()
            && session.selection().kind == EditorSelectionKind::Door
            && session.selection().index == *m_indoorDoorFaceEditDoorIndex)
        {
            Game::IndoorSceneData &sceneData = session.document().mutableIndoorSceneData();

            if (*m_indoorDoorFaceEditDoorIndex < sceneData.initialState.doors.size())
            {
                Game::MapDeltaDoor &door = sceneData.initialState.doors[*m_indoorDoorFaceEditDoorIndex].door;
                const uint16_t faceId = static_cast<uint16_t>(bestFaceIndex);
                const bool shouldMutate =
                    m_indoorDoorFaceEditMode == IndoorDoorFaceEditMode::Add
                        ? !indoorDoorContainsFace(door, faceId)
                        : indoorDoorContainsFace(door, faceId);

                if (shouldMutate)
                {
                    session.captureUndoSnapshot();
                    const bool mutated =
                        m_indoorDoorFaceEditMode == IndoorDoorFaceEditMode::Add
                            ? addIndoorDoorFace(door, faceId)
                            : removeIndoorDoorFace(door, faceId);

                    if (mutated)
                    {
                        session.noteDocumentMutated(
                            m_indoorDoorFaceEditMode == IndoorDoorFaceEditMode::Add
                                ? "Added mechanism face"
                                : "Removed mechanism face");
                    }
                }
            }

            return true;
        }

        session.replaceInteractiveFaceSelection(bestFaceIndex);
        return true;
    }

    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const bx::Vec3 segmentEnd = {
        rayOrigin.x + rayDirection.x * CameraFarPlane,
        rayOrigin.y + rayDirection.y * CameraFarPlane,
        rayOrigin.z + rayDirection.z * CameraFarPlane
    };

    struct FacePickCandidate
    {
        size_t bmodelIndex = 0;
        size_t faceIndex = 0;
        float score = std::numeric_limits<float>::max();
        float facingScore = -std::numeric_limits<float>::max();
        bool frontFacing = false;
    };

    std::vector<FacePickCandidate> pickCandidates;
    constexpr float FacePickDistanceEpsilon = 0.001f;
    constexpr float FacePickFacingEpsilon = 0.01f;
    constexpr float FaceFrontFacingThreshold = 0.05f;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            Game::OutdoorFaceGeometryData geometry = {};

            if (!Game::buildOutdoorFaceGeometry(
                    bmodel,
                    bmodelIndex,
                    bmodel.faces[faceIndex],
                    faceIndex,
                    geometry,
                    true))
            {
                continue;
            }

            float intersectionFactor = 0.0f;
            bx::Vec3 intersectionPoint = {0.0f, 0.0f, 0.0f};

            if (!Game::intersectOutdoorSegmentWithFace(
                    geometry,
                    rayOrigin,
                    segmentEnd,
                    intersectionFactor,
                    intersectionPoint))
            {
                continue;
            }

            const float facingScore = -(geometry.normal.x * rayDirection.x
                + geometry.normal.y * rayDirection.y
                + geometry.normal.z * rayDirection.z);
            pickCandidates.push_back({
                bmodelIndex,
                faceIndex,
                intersectionFactor,
                facingScore,
                facingScore > FaceFrontFacingThreshold});
        }
    }

    if (pickCandidates.empty())
    {
        const float localMouseX = mouseX - static_cast<float>(m_viewportX);
        const float localMouseY = mouseY - static_cast<float>(m_viewportY);

        for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
        {
            const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

            for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
            {
                Game::OutdoorFaceGeometryData geometry = {};

                if (!Game::buildOutdoorFaceGeometry(
                        bmodel,
                        bmodelIndex,
                        bmodel.faces[faceIndex],
                        faceIndex,
                        geometry,
                        true))
                {
                    continue;
                }

                std::vector<ScreenPoint> projectedVertices;
                projectedVertices.reserve(geometry.vertices.size());
                float accumulatedClipW = 0.0f;
                bool allProjected = true;

                for (const bx::Vec3 &vertex : geometry.vertices)
                {
                    float projectedX = 0.0f;
                    float projectedY = 0.0f;
                    float clipW = 0.0f;

                    if (!projectWorldPoint(
                            vertex,
                            m_viewProjectionMatrix,
                            m_viewportWidth,
                            m_viewportHeight,
                            projectedX,
                            projectedY,
                            clipW))
                    {
                        allProjected = false;
                        break;
                    }

                    projectedVertices.push_back({projectedX, projectedY});
                    accumulatedClipW += clipW;
                }

                if (!allProjected || !isPointInsideOrNearScreenPolygon(localMouseX, localMouseY, projectedVertices, 6.0f))
                {
                    continue;
                }

                const float averageClipW = accumulatedClipW / static_cast<float>(projectedVertices.size());
                const float facingScore = -(geometry.normal.x * rayDirection.x
                    + geometry.normal.y * rayDirection.y
                    + geometry.normal.z * rayDirection.z);
                pickCandidates.push_back({
                    bmodelIndex,
                    faceIndex,
                    averageClipW,
                    facingScore,
                    facingScore > FaceFrontFacingThreshold});
            }
        }

        if (pickCandidates.empty())
        {
            return false;
        }
    }

    const bool hasFrontFacingCandidate = std::any_of(
        pickCandidates.begin(),
        pickCandidates.end(),
        [](const FacePickCandidate &candidate)
        {
            return candidate.frontFacing;
        });

    std::erase_if(
        pickCandidates,
        [hasFrontFacingCandidate](const FacePickCandidate &candidate)
        {
            return hasFrontFacingCandidate && !candidate.frontFacing;
        });

    std::sort(
        pickCandidates.begin(),
        pickCandidates.end(),
        [](const FacePickCandidate &left, const FacePickCandidate &right)
        {
            if (std::fabs(left.score - right.score) > FacePickDistanceEpsilon)
            {
                return left.score < right.score;
            }

            if (std::fabs(left.facingScore - right.facingScore) > FacePickFacingEpsilon)
            {
                return left.facingScore > right.facingScore;
            }

            if (left.bmodelIndex != right.bmodelIndex)
            {
                return left.bmodelIndex < right.bmodelIndex;
            }

            return left.faceIndex < right.faceIndex;
        });

    std::vector<size_t> flatCandidates;
    flatCandidates.reserve(pickCandidates.size());

    for (const FacePickCandidate &candidate : pickCandidates)
    {
        flatCandidates.push_back(
            flattenedOutdoorFaceIndex(outdoorGeometry, candidate.bmodelIndex, candidate.faceIndex));
    }

    const bool samePickRegion =
        std::fabs(mouseX - m_lastFacePickMouseX) <= 10.0f
        && std::fabs(mouseY - m_lastFacePickMouseY) <= 10.0f
        && !ImGui::GetIO().KeyCtrl;

    size_t selectedCandidateIndex = 0;

    if (samePickRegion
        && session.selection().kind == EditorSelectionKind::InteractiveFace
        && !flatCandidates.empty())
    {
        const auto currentSelectionIterator = std::find(
            flatCandidates.begin(),
            flatCandidates.end(),
            session.selection().index);

        if (currentSelectionIterator != flatCandidates.end())
        {
            selectedCandidateIndex =
                (static_cast<size_t>(std::distance(flatCandidates.begin(), currentSelectionIterator)) + 1)
                % flatCandidates.size();
        }
    }

    m_lastFacePickMouseX = mouseX;
    m_lastFacePickMouseY = mouseY;
    m_lastFacePickCandidates = flatCandidates;
    m_lastFacePickCycleIndex = selectedCandidateIndex;
    const size_t flatIndex = flatCandidates[selectedCandidateIndex];

    if (ImGui::GetIO().KeyCtrl)
    {
        session.toggleInteractiveFaceSelection(flatIndex);
    }
    else
    {
        session.replaceInteractiveFaceSelection(flatIndex);
    }

    return true;
}

bool EditorOutdoorViewport::tryPlaceObject(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!m_isHovered || m_placementKind == EditorSelectionKind::None || !session.hasDocument())
    {
        m_pendingEntityPlacementPreview.reset();
        m_pendingActorPlacementPreview.reset();
        m_pendingSpawnPlacementPreview.reset();
        m_pendingSpriteObjectPlacementPreview.reset();
        return false;
    }

    if (m_placementKind != EditorSelectionKind::BModel
        && m_placementKind != EditorSelectionKind::SpriteObject
        && m_placementKind != EditorSelectionKind::Entity
        && m_placementKind != EditorSelectionKind::Actor
        && m_placementKind != EditorSelectionKind::Spawn
        && !leftMouseClicked)
    {
        m_pendingEntityPlacementPreview.reset();
        m_pendingActorPlacementPreview.reset();
        m_pendingSpawnPlacementPreview.reset();
        m_pendingSpriteObjectPlacementPreview.reset();
        return false;
    }

    bx::Vec3 worldPosition = {0.0f, 0.0f, 0.0f};

    const bool sampledWorldPosition =
        m_placementKind == EditorSelectionKind::BModel
            ? sampleTerrainWorldPosition(session.document(), mouseX, mouseY, worldPosition)
            : samplePlacementWorldPosition(session.document(), mouseX, mouseY, worldPosition);

    if (!sampledWorldPosition)
    {
        m_pendingEntityPlacementPreview.reset();
        m_pendingActorPlacementPreview.reset();
        m_pendingSpawnPlacementPreview.reset();
        m_pendingSpriteObjectPlacementPreview.reset();
        return false;
    }

    if (m_snapEnabled)
    {
        const int snapStep = std::max(m_snapStep, 1);
        const auto snapValue = [snapStep](float value)
        {
            return static_cast<float>(
                static_cast<int>(std::lround(value / static_cast<float>(snapStep))) * snapStep);
        };

        worldPosition.x = snapValue(worldPosition.x);
        worldPosition.y = snapValue(worldPosition.y);
        worldPosition.z = snapValue(worldPosition.z);
    }

    if (m_placementKind == EditorSelectionKind::BModel)
    {
        const EditorSelection selection = session.selection();

        if (selection.kind != EditorSelectionKind::BModel)
        {
            return false;
        }

        const std::optional<bx::Vec3> targetCenter =
            bmodelPlacementCenterForFloorPoint(session.document().outdoorGeometry(), selection.index, worldPosition);

        if (!targetCenter)
        {
            return false;
        }

        if (setSelectedWorldPosition(session, *targetCenter))
        {
            session.document().setDirty(true);
            session.document().touchSceneRevision();
            m_geometryKey.clear();
        }

        if (leftMouseClicked)
        {
            session.noteDocumentMutated("Placed imported bmodel");
            m_placementKind = EditorSelectionKind::None;
            return true;
        }

        return false;
    }

    if (m_placementKind == EditorSelectionKind::SpriteObject)
    {
        m_pendingSpriteObjectPlacementPreview = PendingSpriteObjectPlacementPreview{
            static_cast<int>(std::lround(worldPosition.x)),
            static_cast<int>(std::lround(worldPosition.y)),
            static_cast<int>(std::lround(worldPosition.z))
        };
    }
    else
    {
        m_pendingSpriteObjectPlacementPreview.reset();
    }

    if (m_placementKind == EditorSelectionKind::Entity)
    {
        m_pendingEntityPlacementPreview = PendingEntityPlacementPreview{
            static_cast<int>(std::lround(worldPosition.x)),
            static_cast<int>(std::lround(worldPosition.y)),
            static_cast<int>(std::lround(worldPosition.z))
        };
    }
    else
    {
        m_pendingEntityPlacementPreview.reset();
    }

    if (m_placementKind == EditorSelectionKind::Actor)
    {
        const int previewX = static_cast<int>(std::lround(worldPosition.x));
        const int previewY = static_cast<int>(std::lround(worldPosition.y));
        const int previewZ = snapIndoorActorZToFloor(
            session.document(),
            previewX,
            previewY,
            static_cast<int>(std::lround(worldPosition.z)));
        m_pendingActorPlacementPreview = PendingActorPlacementPreview{
            previewX,
            previewY,
            previewZ
        };
    }
    else
    {
        m_pendingActorPlacementPreview.reset();
    }

    if (m_placementKind == EditorSelectionKind::Spawn)
    {
        const int previewX = static_cast<int>(std::lround(worldPosition.x));
        const int previewY = static_cast<int>(std::lround(worldPosition.y));
        const int previewZ = snapIndoorActorZToFloor(
            session.document(),
            previewX,
            previewY,
            static_cast<int>(std::lround(worldPosition.z)));
        m_pendingSpawnPlacementPreview = PendingSpawnPlacementPreview{
            previewX,
            previewY,
            previewZ
        };
    }
    else
    {
        m_pendingSpawnPlacementPreview.reset();
    }

    if (!leftMouseClicked)
    {
        return false;
    }

    std::string errorMessage;

    if (!session.createOutdoorObject(
            m_placementKind,
            static_cast<int>(std::lround(worldPosition.x)),
            static_cast<int>(std::lround(worldPosition.y)),
            static_cast<int>(std::lround(worldPosition.z)),
            errorMessage))
    {
        session.logError(errorMessage);
        return false;
    }

    return true;
}

std::optional<bx::Vec3> EditorOutdoorViewport::selectedWorldPosition(
    const EditorDocument &document,
    const EditorSelection &selection) const
{
    if (document.kind() == EditorDocument::Kind::Indoor)
    {
        const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
        const Game::IndoorSceneData &sceneData = document.indoorSceneData();
        const std::vector<Game::IndoorVertex> &indoorVertices = indoorRenderVertices(document);

        switch (selection.kind)
        {
        case EditorSelectionKind::Entity:
            if (selection.index < indoorGeometry.entities.size())
            {
                const Game::IndoorEntity &entity = indoorGeometry.entities[selection.index];
                return bx::Vec3{static_cast<float>(entity.x), static_cast<float>(entity.y), static_cast<float>(entity.z)};
            }
            break;

        case EditorSelectionKind::Spawn:
            if (selection.index < indoorGeometry.spawns.size())
            {
                const Game::IndoorSpawn &spawn = indoorGeometry.spawns[selection.index];
                const int displayZ = snapIndoorActorZToFloor(document, spawn.x, spawn.y, spawn.z);
                return bx::Vec3{static_cast<float>(spawn.x), static_cast<float>(spawn.y), static_cast<float>(displayZ)};
            }
            break;

        case EditorSelectionKind::Actor:
            if (selection.index < sceneData.initialState.actors.size())
            {
                const Game::MapDeltaActor &actor = sceneData.initialState.actors[selection.index];
                const int displayZ = snapIndoorActorZToFloor(document, actor.x, actor.y, actor.z);
                return bx::Vec3{static_cast<float>(actor.x), static_cast<float>(actor.y), static_cast<float>(displayZ)};
            }
            break;

        case EditorSelectionKind::SpriteObject:
            if (selection.index < sceneData.initialState.spriteObjects.size())
            {
                const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[selection.index];
                return bx::Vec3{
                    static_cast<float>(spriteObject.x),
                    static_cast<float>(spriteObject.y),
                    static_cast<float>(spriteObject.z)};
            }
            break;

        case EditorSelectionKind::Light:
            if (selection.index < indoorGeometry.lights.size())
            {
                const Game::IndoorLight &light = indoorGeometry.lights[selection.index];
                return bx::Vec3{static_cast<float>(light.x), static_cast<float>(light.y), static_cast<float>(light.z)};
            }
            break;

        case EditorSelectionKind::Door:
            if (selection.index < sceneData.initialState.doors.size())
            {
                const Game::IndoorSceneDoor &door = sceneData.initialState.doors[selection.index];
                bx::Vec3 center = {0.0f, 0.0f, 0.0f};
                int count = 0;

                for (uint16_t vertexId : door.door.vertexIds)
                {
                    if (vertexId >= indoorVertices.size())
                    {
                        continue;
                    }

                    const bx::Vec3 worldVertex = Game::indoorVertexToWorld(indoorVertices[vertexId]);
                    center.x += worldVertex.x;
                    center.y += worldVertex.y;
                    center.z += worldVertex.z;
                    ++count;
                }

                if (count > 0)
                {
                    const float invCount = 1.0f / static_cast<float>(count);
                    center.x *= invCount;
                    center.y *= invCount;
                    center.z *= invCount;
                    return center;
                }

                for (uint16_t faceId : door.door.faceIds)
                {
                    const std::optional<bx::Vec3> faceCenter = indoorFaceCenter(indoorGeometry, indoorVertices, faceId);

                    if (!faceCenter)
                    {
                        continue;
                    }

                    center.x += faceCenter->x;
                    center.y += faceCenter->y;
                    center.z += faceCenter->z;
                    ++count;
                }

                if (count > 0)
                {
                    const float invCount = 1.0f / static_cast<float>(count);
                    center.x *= invCount;
                    center.y *= invCount;
                    center.z *= invCount;
                    return center;
                }

                for (uint16_t sectorId : door.door.sectorIds)
                {
                    if (sectorId >= indoorGeometry.sectors.size())
                    {
                        continue;
                    }

                    const Game::IndoorSector &sector = indoorGeometry.sectors[sectorId];
                    center.x += (static_cast<float>(sector.minX) + static_cast<float>(sector.maxX)) * 0.5f;
                    center.y += (static_cast<float>(sector.minY) + static_cast<float>(sector.maxY)) * 0.5f;
                    center.z += (static_cast<float>(sector.minZ) + static_cast<float>(sector.maxZ)) * 0.5f;
                    ++count;
                }

                if (count > 0)
                {
                    const float invCount = 1.0f / static_cast<float>(count);
                    center.x *= invCount;
                    center.y *= invCount;
                    center.z *= invCount;
                    return center;
                }
            }
            break;

        case EditorSelectionKind::InteractiveFace:
            if (selection.index < indoorGeometry.faces.size())
            {
                Game::IndoorFaceGeometryData geometry = {};

                if (Game::buildIndoorFaceGeometry(indoorGeometry, indoorVertices, selection.index, geometry)
                    && !geometry.vertices.empty())
                {
                    bx::Vec3 center = {0.0f, 0.0f, 0.0f};

                    for (const bx::Vec3 &vertex : geometry.vertices)
                    {
                        center.x += vertex.x;
                        center.y += vertex.y;
                        center.z += vertex.z;
                    }

                    const float invCount = 1.0f / static_cast<float>(geometry.vertices.size());
                    center.x *= invCount;
                    center.y *= invCount;
                    center.z *= invCount;
                    return center;
                }
            }
            break;

        default:
            break;
        }

        return std::nullopt;
    }

    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();

    switch (selection.kind)
    {
    case EditorSelectionKind::Entity:
        if (selection.index < sceneData.entities.size())
        {
            const Game::OutdoorEntity &entity = sceneData.entities[selection.index].entity;
            return bx::Vec3{static_cast<float>(entity.x), static_cast<float>(entity.y), static_cast<float>(entity.z)};
        }
        break;

    case EditorSelectionKind::Spawn:
        if (selection.index < sceneData.spawns.size())
        {
            const Game::OutdoorSpawn &spawn = sceneData.spawns[selection.index].spawn;
            return bx::Vec3{static_cast<float>(spawn.x), static_cast<float>(spawn.y), static_cast<float>(spawn.z)};
        }
        break;

    case EditorSelectionKind::Actor:
        if (selection.index < sceneData.initialState.actors.size())
        {
            const Game::MapDeltaActor &actor = sceneData.initialState.actors[selection.index];
            return bx::Vec3{static_cast<float>(actor.x), static_cast<float>(actor.y), static_cast<float>(actor.z)};
        }
        break;

    case EditorSelectionKind::SpriteObject:
        if (selection.index < sceneData.initialState.spriteObjects.size())
        {
            const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[selection.index];
            return bx::Vec3{
                static_cast<float>(spriteObject.x),
                static_cast<float>(spriteObject.y),
                static_cast<float>(spriteObject.z)};
        }
        break;

    case EditorSelectionKind::ModelInstance:
    case EditorSelectionKind::Mm9ScriptedObject:
        if (selection.index < sceneData.modelInstances.size())
        {
            const Game::OutdoorSceneModelInstance &modelInstance = sceneData.modelInstances[selection.index];
            return bx::Vec3{
                static_cast<float>(modelInstance.x),
                static_cast<float>(modelInstance.y),
                static_cast<float>(modelInstance.z)};
        }
        break;

    case EditorSelectionKind::Mm9WorldModel:
        if (document.kind() == EditorDocument::Kind::Mm9Dat
            && document.hasMm9DatLoadedSidecars()
            && selection.index < document.mm9DatLoadedSidecars().datWorld.worldModels.size())
        {
            const EditorMm9DatWorldModelSummary &model =
                document.mm9DatLoadedSidecars().datWorld.worldModels[selection.index];
            const bx::Vec3 minPoint = mm9LtToOpenYamm(model.boundsMinLt);
            const bx::Vec3 maxPoint = mm9LtToOpenYamm(model.boundsMaxLt);
            return bx::Vec3{
                (minPoint.x + maxPoint.x) * 0.5f,
                (minPoint.y + maxPoint.y) * 0.5f,
                (minPoint.z + maxPoint.z) * 0.5f};
        }
        break;

    case EditorSelectionKind::Mm9RawObject:
        if (document.kind() == EditorDocument::Kind::Mm9Dat
            && document.hasMm9DatLoadedSidecars()
            && selection.index < document.mm9DatLoadedSidecars().rawObjects.objects.size())
        {
            const size_t sourceObjectIndex =
                document.mm9DatLoadedSidecars().rawObjects.objects[selection.index].objectIndex;

            for (const Game::Mm9Object &object : document.mm9ObjectLayer().objects)
            {
                if (object.sourceObjectIndex == sourceObjectIndex && object.hasPosition)
                {
                    return mm9DatVec3LtToOpenYamm(object.positionLt);
                }
            }

            for (const Game::Mm9LightObject &light : document.mm9LightLayer().lights)
            {
                if (light.sourceObjectIndex == sourceObjectIndex && light.hasPosition)
                {
                    return mm9DatVec3LtToOpenYamm(light.positionLt);
                }
            }

            for (const Game::Mm9SoundObject &sound : document.mm9SoundLayer().objects)
            {
                if (sound.sourceObjectIndex == sourceObjectIndex && (sound.hasSoundPosition || sound.hasPosition))
                {
                    return mm9DatVec3LtToOpenYamm(sound.hasSoundPosition ? sound.soundPositionLt : sound.positionLt);
                }
            }

            for (const Game::Mm9SpawnObject &spawn : document.mm9SpawnLayer().objects)
            {
                if (spawn.sourceObjectIndex == sourceObjectIndex && spawn.hasPosition)
                {
                    return mm9DatVec3LtToOpenYamm(spawn.positionLt);
                }
            }
        }
        break;

    case EditorSelectionKind::Terrain:
    {
        int cellX = 0;
        int cellY = 0;

        if (decodeSelectedTerrainCell(selection, cellX, cellY)
            && cellX >= 0
            && cellY >= 0
            && cellX < (Game::OutdoorMapData::TerrainWidth - 1)
            && cellY < (Game::OutdoorMapData::TerrainHeight - 1))
        {
            const size_t topLeftIndex = static_cast<size_t>(cellY * Game::OutdoorMapData::TerrainWidth + cellX);
            const size_t topRightIndex = topLeftIndex + 1;
            const size_t bottomLeftIndex =
                static_cast<size_t>((cellY + 1) * Game::OutdoorMapData::TerrainWidth + cellX);
            const size_t bottomRightIndex = bottomLeftIndex + 1;
            const bx::Vec3 topLeft = worldPointFromTerrainGrid(cellX, cellY, outdoorGeometry.heightMap[topLeftIndex]);
            const bx::Vec3 topRight = worldPointFromTerrainGrid(cellX + 1, cellY, outdoorGeometry.heightMap[topRightIndex]);
            const bx::Vec3 bottomLeft =
                worldPointFromTerrainGrid(cellX, cellY + 1, outdoorGeometry.heightMap[bottomLeftIndex]);
            const bx::Vec3 bottomRight =
                worldPointFromTerrainGrid(cellX + 1, cellY + 1, outdoorGeometry.heightMap[bottomRightIndex]);

            return bx::Vec3{
                (topLeft.x + topRight.x + bottomLeft.x + bottomRight.x) * 0.25f,
                (topLeft.y + topRight.y + bottomLeft.y + bottomRight.y) * 0.25f,
                (topLeft.z + topRight.z + bottomLeft.z + bottomRight.z) * 0.25f};
        }

        break;
    }

    case EditorSelectionKind::BModel:
        if (selection.index < outdoorGeometry.bmodels.size())
        {
            const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[selection.index];
            float minX = std::numeric_limits<float>::max();
            float minY = std::numeric_limits<float>::max();
            float minZ = std::numeric_limits<float>::max();
            float maxX = std::numeric_limits<float>::lowest();
            float maxY = std::numeric_limits<float>::lowest();
            float maxZ = std::numeric_limits<float>::lowest();

            for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
            {
                minX = std::min(minX, static_cast<float>(vertex.x));
                minY = std::min(minY, static_cast<float>(vertex.y));
                minZ = std::min(minZ, static_cast<float>(vertex.z));
                maxX = std::max(maxX, static_cast<float>(vertex.x));
                maxY = std::max(maxY, static_cast<float>(vertex.y));
                maxZ = std::max(maxZ, static_cast<float>(vertex.z));
            }

            if (std::isfinite(minX) && std::isfinite(maxX))
            {
                return bx::Vec3{
                    (minX + maxX) * 0.5f,
                    (minY + maxY) * 0.5f,
                    (minZ + maxZ) * 0.5f};
            }
        }
        break;

    case EditorSelectionKind::InteractiveFace:
    {
        size_t bmodelIndex = 0;
        size_t faceIndex = 0;

        if (decodeSelectedInteractiveFace(document, selection, bmodelIndex, faceIndex)
            && bmodelIndex < outdoorGeometry.bmodels.size())
        {
            const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

            if (faceIndex < bmodel.faces.size())
            {
                const Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];
                bx::Vec3 center = {0.0f, 0.0f, 0.0f};
                int vertexCount = 0;

                for (size_t vertexIndex : face.vertexIndices)
                {
                    if (vertexIndex >= bmodel.vertices.size())
                    {
                        continue;
                    }

                    const Game::OutdoorBModelVertex &vertex = bmodel.vertices[vertexIndex];
                    center.x += static_cast<float>(vertex.x);
                    center.y += static_cast<float>(vertex.y);
                    center.z += static_cast<float>(vertex.z);
                    ++vertexCount;
                }

                if (vertexCount > 0)
                {
                    const float scale = 1.0f / static_cast<float>(vertexCount);
                    center.x *= scale;
                    center.y *= scale;
                    center.z *= scale;
                    return center;
                }
            }
        }

        break;
    }

    default:
        break;
    }

    return std::nullopt;
}

bool EditorOutdoorViewport::decodeSelectedTerrainCell(
    const EditorSelection &selection,
    int &cellX,
    int &cellY) const
{
    if (selection.kind != EditorSelectionKind::Terrain)
    {
        return false;
    }

    if (selection.index >= static_cast<size_t>(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight))
    {
        return false;
    }

    cellX = static_cast<int>(selection.index % Game::OutdoorMapData::TerrainWidth);
    cellY = static_cast<int>(selection.index / Game::OutdoorMapData::TerrainWidth);
    return true;
}

bool EditorOutdoorViewport::decodeSelectedInteractiveFace(
    const EditorDocument &document,
    const EditorSelection &selection,
    size_t &bmodelIndex,
    size_t &faceIndex) const
{
    if (selection.kind != EditorSelectionKind::InteractiveFace)
    {
        return false;
    }

    if (document.kind() == EditorDocument::Kind::Indoor)
    {
        if (selection.index >= document.indoorGeometry().faces.size())
        {
            return false;
        }

        bmodelIndex = 0;
        faceIndex = selection.index;
        return true;
    }

    size_t runningIndex = 0;

    for (size_t currentBModelIndex = 0; currentBModelIndex < document.outdoorGeometry().bmodels.size(); ++currentBModelIndex)
    {
        const size_t faceCount = document.outdoorGeometry().bmodels[currentBModelIndex].faces.size();

        if (selection.index < runningIndex + faceCount)
        {
            bmodelIndex = currentBModelIndex;
            faceIndex = selection.index - runningIndex;
            return true;
        }

        runningIndex += faceCount;
    }

    return false;
}

bool EditorOutdoorViewport::computeMouseRay(float mouseX, float mouseY, bx::Vec3 &origin, bx::Vec3 &direction) const
{
    const float localMouseX = mouseX - static_cast<float>(m_viewportX);
    const float localMouseY = mouseY - static_cast<float>(m_viewportY);
    const float normalizedX = (localMouseX / static_cast<float>(std::max<uint16_t>(m_viewportWidth, 1))) * 2.0f - 1.0f;
    const float normalizedY = 1.0f - (localMouseY / static_cast<float>(std::max<uint16_t>(m_viewportHeight, 1))) * 2.0f;
    const float aspect = static_cast<float>(m_renderWidth) / static_cast<float>(std::max<uint16_t>(m_renderHeight, 1));
    const float tanHalfFovY = std::tan((CameraVerticalFovDegrees * bx::kPi / 180.0f) * 0.5f);
    const float tanHalfFovX = tanHalfFovY * aspect;
    const bx::Vec3 forward = {
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    };
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    const bx::Vec3 right = vecNormalize(vecCross(forward, worldUp));
    const bx::Vec3 up = vecNormalize(vecCross(right, forward));

    origin = m_cameraPosition;
    direction = vecNormalize({
        forward.x + right.x * normalizedX * tanHalfFovX + up.x * normalizedY * tanHalfFovY,
        forward.y + right.y * normalizedX * tanHalfFovX + up.y * normalizedY * tanHalfFovY,
        forward.z + right.z * normalizedX * tanHalfFovX + up.z * normalizedY * tanHalfFovY
    });
    return vecLength(direction) > 0.0001f;
}

bool EditorOutdoorViewport::sampleTerrainWorldPosition(
    const EditorDocument &document,
    float mouseX,
    float mouseY,
    bx::Vec3 &worldPosition) const
{
    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection))
    {
        return false;
    }

    const Game::OutdoorMapData &outdoorMapData = document.outdoorGeometry();
    constexpr float MaxDistance = 200000.0f;
    constexpr float StepDistance = 1024.0f;
    bool havePreviousSample = false;
    float previousDistance = 0.0f;
    float previousDelta = 0.0f;

    for (float distance = CameraNearPlane; distance <= MaxDistance; distance += StepDistance)
    {
        const bx::Vec3 rayPoint = {
            rayOrigin.x + rayDirection.x * distance,
            rayOrigin.y + rayDirection.y * distance,
            rayOrigin.z + rayDirection.z * distance
        };
        const float terrainHeight = Game::sampleOutdoorTerrainHeight(outdoorMapData, rayPoint.x, rayPoint.y);
        const float delta = rayPoint.z - terrainHeight;

        if (havePreviousSample && previousDelta >= 0.0f && delta <= 0.0f)
        {
            float lowDistance = previousDistance;
            float highDistance = distance;

            for (int iteration = 0; iteration < 12; ++iteration)
            {
                const float midDistance = (lowDistance + highDistance) * 0.5f;
                const bx::Vec3 midPoint = {
                    rayOrigin.x + rayDirection.x * midDistance,
                    rayOrigin.y + rayDirection.y * midDistance,
                    rayOrigin.z + rayDirection.z * midDistance
                };
                const float midTerrainHeight = Game::sampleOutdoorTerrainHeight(outdoorMapData, midPoint.x, midPoint.y);
                const float midDelta = midPoint.z - midTerrainHeight;

                if (midDelta > 0.0f)
                {
                    lowDistance = midDistance;
                }
                else
                {
                    highDistance = midDistance;
                }
            }

            const float hitDistance = highDistance;
            const bx::Vec3 hitPoint = {
                rayOrigin.x + rayDirection.x * hitDistance,
                rayOrigin.y + rayDirection.y * hitDistance,
                rayOrigin.z + rayDirection.z * hitDistance
            };
            worldPosition = {
                hitPoint.x,
                hitPoint.y,
                Game::sampleOutdoorTerrainHeight(outdoorMapData, hitPoint.x, hitPoint.y)
            };
            return true;
        }

        previousDistance = distance;
        previousDelta = delta;
        havePreviousSample = true;
    }

    return false;
}

bool EditorOutdoorViewport::samplePlacementWorldPosition(
    const EditorDocument &document,
    float mouseX,
    float mouseY,
    bx::Vec3 &worldPosition) const
{
    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};

    if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection))
    {
        return false;
    }

    if (document.kind() == EditorDocument::Kind::Indoor)
    {
        const Game::IndoorMapData &indoorMapData = document.indoorGeometry();
        const std::vector<Game::IndoorVertex> &indoorVertices = indoorRenderVertices(document);
        constexpr float PlacementSurfaceOffset = 12.0f;
        float bestDistance = std::numeric_limits<float>::max();
        bx::Vec3 bestPoint = {0.0f, 0.0f, 0.0f};
        bool foundHit = false;
        const auto offsetFromPlacementSurface = [rayDirection](const bx::Vec3 &hitPoint, const bx::Vec3 &faceNormal)
        {
            if (vecLength(faceNormal) <= 0.0001f)
            {
                return hitPoint;
            }

            const bx::Vec3 normalizedNormal = vecNormalize(faceNormal);
            const bx::Vec3 offsetDirection =
                vecDot(normalizedNormal, rayDirection) > 0.0f
                    ? vecScale(normalizedNormal, -1.0f)
                    : normalizedNormal;
            return vecAdd(hitPoint, vecScale(offsetDirection, PlacementSurfaceOffset));
        };

        for (size_t faceIndex = 0; faceIndex < indoorMapData.faces.size(); ++faceIndex)
        {
            if (indoorFaceHiddenByCeilingView(
                    indoorMapData,
                    indoorVertices,
                    faceIndex,
                    m_showIndoorFloors,
                    m_showIndoorCeilings,
                    m_isolatedIndoorRoomId))
            {
                continue;
            }

            Game::IndoorFaceGeometryData geometry = {};

            if (!Game::buildIndoorFaceGeometry(indoorMapData, indoorVertices, faceIndex, geometry)
                || geometry.vertices.size() < 3)
            {
                continue;
            }

            for (size_t triangleIndex = 1; triangleIndex + 1 < geometry.vertices.size(); ++triangleIndex)
            {
                float hitDistance = 0.0f;

                if (!intersectRayTriangle(
                        rayOrigin,
                        rayDirection,
                        geometry.vertices[0],
                        geometry.vertices[triangleIndex],
                        geometry.vertices[triangleIndex + 1],
                        hitDistance))
                {
                    continue;
                }

                const bx::Vec3 hitPoint = {
                    rayOrigin.x + rayDirection.x * hitDistance,
                    rayOrigin.y + rayDirection.y * hitDistance,
                    rayOrigin.z + rayDirection.z * hitDistance
                };

                if (hitDistance < bestDistance)
                {
                    bestDistance = hitDistance;
                    bestPoint = offsetFromPlacementSurface(hitPoint, geometry.normal);
                    foundHit = true;
                }
            }
        }

        if (foundHit)
        {
            worldPosition = bestPoint;
            return true;
        }

        return false;
    }

    const Game::OutdoorMapData &outdoorMapData = document.outdoorGeometry();
    constexpr float MaxDistance = 200000.0f;
    constexpr float StepDistance = 512.0f;
    bool havePreviousSample = false;
    float previousDistance = 0.0f;
    float previousDelta = 0.0f;

    for (float distance = CameraNearPlane; distance <= MaxDistance; distance += StepDistance)
    {
        const bx::Vec3 rayPoint = {
            rayOrigin.x + rayDirection.x * distance,
            rayOrigin.y + rayDirection.y * distance,
            rayOrigin.z + rayDirection.z * distance
        };
        const float floorHeight =
            Game::sampleOutdoorPlacementFloorHeight(outdoorMapData, rayPoint.x, rayPoint.y, rayPoint.z);
        const float delta = rayPoint.z - floorHeight;

        if (havePreviousSample && previousDelta >= 0.0f && delta <= 0.0f)
        {
            float lowDistance = previousDistance;
            float highDistance = distance;

            for (int iteration = 0; iteration < 12; ++iteration)
            {
                const float midDistance = (lowDistance + highDistance) * 0.5f;
                const bx::Vec3 midPoint = {
                    rayOrigin.x + rayDirection.x * midDistance,
                    rayOrigin.y + rayDirection.y * midDistance,
                    rayOrigin.z + rayDirection.z * midDistance
                };
                const float midFloorHeight =
                    Game::sampleOutdoorPlacementFloorHeight(outdoorMapData, midPoint.x, midPoint.y, midPoint.z);
                const float midDelta = midPoint.z - midFloorHeight;

                if (midDelta > 0.0f)
                {
                    lowDistance = midDistance;
                }
                else
                {
                    highDistance = midDistance;
                }
            }

            const float hitDistance = highDistance;
            const bx::Vec3 hitPoint = {
                rayOrigin.x + rayDirection.x * hitDistance,
                rayOrigin.y + rayDirection.y * hitDistance,
                rayOrigin.z + rayDirection.z * hitDistance
            };
            worldPosition = {
                hitPoint.x,
                hitPoint.y,
                Game::sampleOutdoorPlacementFloorHeight(outdoorMapData, hitPoint.x, hitPoint.y, hitPoint.z)
            };
            return true;
        }

        previousDistance = distance;
        previousDelta = delta;
        havePreviousSample = true;
    }

    return false;
}

int EditorOutdoorViewport::snapIndoorActorZToFloor(const EditorDocument &document, int x, int y, int z) const
{
    if (document.kind() != EditorDocument::Kind::Indoor)
    {
        return z;
    }

    const std::string snapKey =
        documentGeometryKey(document) + "|preview=" + std::to_string(m_indoorMechanismPreviewRevision);

    if (snapKey != m_indoorActorFloorSnapKey)
    {
        m_indoorActorFloorSnapKey = snapKey;
        m_indoorActorFloorSnapZByKey.clear();
    }

    const auto quantizeCoordinate = [](int value)
    {
        return static_cast<uint64_t>(static_cast<uint16_t>(static_cast<int16_t>(value)));
    };
    const uint64_t positionKey =
        quantizeCoordinate(x)
        | (quantizeCoordinate(y) << 16)
        | (quantizeCoordinate(z) << 32);
    const auto cachedIterator = m_indoorActorFloorSnapZByKey.find(positionKey);

    if (cachedIterator != m_indoorActorFloorSnapZByKey.end())
    {
        return cachedIterator->second;
    }

    const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
    const std::vector<Game::IndoorVertex> &indoorVertices = indoorRenderVertices(document);
    Game::IndoorFaceGeometryCache &geometryCache = indoorRenderFaceGeometryCache(document);
    const std::optional<int16_t> sectorId = Game::findIndoorSectorForPoint(
        indoorGeometry,
        indoorVertices,
        {static_cast<float>(x), static_cast<float>(y), static_cast<float>(z)},
        &geometryCache);
    const Game::IndoorFloorSample floor = Game::sampleIndoorFloor(
        indoorGeometry,
        indoorVertices,
        static_cast<float>(x),
        static_cast<float>(y),
        static_cast<float>(z),
        131072.0f,
        0.0f,
        sectorId,
        nullptr,
        &geometryCache);

    if (!floor.hasFloor || floor.height <= static_cast<float>(z))
    {
        m_indoorActorFloorSnapZByKey.emplace(positionKey, z);
        return z;
    }

    const int snappedZ = static_cast<int>(std::lround(floor.height));
    m_indoorActorFloorSnapZByKey.emplace(positionKey, snappedZ);
    return snappedZ;
}

bool EditorOutdoorViewport::setSelectedWorldPosition(EditorSession &session, const bx::Vec3 &worldPosition)
{
    if (!session.hasDocument())
    {
        return false;
    }

    EditorDocument &document = session.document();
    int targetX = static_cast<int>(std::lround(worldPosition.x));
    int targetY = static_cast<int>(std::lround(worldPosition.y));
    int targetZ = static_cast<int>(std::lround(worldPosition.z));

    if (m_snapEnabled)
    {
        const int snapStep = std::max(m_snapStep, 1);
        const auto snapValue = [snapStep](int value)
        {
            return static_cast<int>(std::lround(static_cast<float>(value) / static_cast<float>(snapStep))) * snapStep;
        };

        targetX = snapValue(targetX);
        targetY = snapValue(targetY);
        targetZ = snapValue(targetZ);
    }

    bool changed = false;

    if (document.kind() == EditorDocument::Kind::Indoor)
    {
        Game::IndoorMapData &indoorGeometry = document.mutableIndoorGeometry();
        Game::IndoorSceneData &sceneData = document.mutableIndoorSceneData();

        switch (session.selection().kind)
        {
        case EditorSelectionKind::Entity:
            if (session.selection().index < indoorGeometry.entities.size())
            {
                Game::IndoorEntity &entity = indoorGeometry.entities[session.selection().index];
                changed = entity.x != targetX || entity.y != targetY || entity.z != targetZ;
                entity.x = targetX;
                entity.y = targetY;
                entity.z = targetZ;

                if (changed)
                {
                    assignIndoorEntityToSector(indoorGeometry, session.selection().index);
                    indoorGeometry.spriteCount = indoorGeometry.entities.size();
                }
            }
            break;

        case EditorSelectionKind::Spawn:
            if (session.selection().index < indoorGeometry.spawns.size())
            {
                Game::IndoorSpawn &spawn = indoorGeometry.spawns[session.selection().index];
                const int snappedTargetZ = snapIndoorActorZToFloor(document, targetX, targetY, targetZ);
                changed = spawn.x != targetX || spawn.y != targetY || spawn.z != snappedTargetZ;
                spawn.x = targetX;
                spawn.y = targetY;
                spawn.z = snappedTargetZ;
            }
            break;

        case EditorSelectionKind::Actor:
            if (session.selection().index < sceneData.initialState.actors.size())
            {
                Game::MapDeltaActor &actor = sceneData.initialState.actors[session.selection().index];
                const int snappedTargetZ = snapIndoorActorZToFloor(document, targetX, targetY, targetZ);
                changed = actor.x != targetX || actor.y != targetY || actor.z != snappedTargetZ;
                actor.x = targetX;
                actor.y = targetY;
                actor.z = snappedTargetZ;

                if (changed)
                {
                    const std::optional<int16_t> sectorId = findIndoorSectorIdForPoint(
                        indoorGeometry,
                        actor.x,
                        actor.y,
                        actor.z);
                    actor.sectorId = sectorId.value_or(-1);
                }
            }
            break;

        case EditorSelectionKind::SpriteObject:
            if (session.selection().index < sceneData.initialState.spriteObjects.size())
            {
                Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[session.selection().index];
                changed = spriteObject.x != targetX || spriteObject.y != targetY || spriteObject.z != targetZ;
                spriteObject.x = targetX;
                spriteObject.y = targetY;
                spriteObject.z = targetZ;

                if (changed)
                {
                    const std::optional<int16_t> sectorId = findIndoorSectorIdForPoint(
                        indoorGeometry,
                        spriteObject.x,
                        spriteObject.y,
                        spriteObject.z);
                    spriteObject.sectorId = sectorId.value_or(-1);
                }
            }
            break;

        case EditorSelectionKind::Light:
            if (session.selection().index < indoorGeometry.lights.size())
            {
                Game::IndoorLight &light = indoorGeometry.lights[session.selection().index];
                const int clampedX = std::clamp(
                    targetX,
                    static_cast<int>(std::numeric_limits<int16_t>::min()),
                    static_cast<int>(std::numeric_limits<int16_t>::max()));
                const int clampedY = std::clamp(
                    targetY,
                    static_cast<int>(std::numeric_limits<int16_t>::min()),
                    static_cast<int>(std::numeric_limits<int16_t>::max()));
                const int clampedZ = std::clamp(
                    targetZ,
                    static_cast<int>(std::numeric_limits<int16_t>::min()),
                    static_cast<int>(std::numeric_limits<int16_t>::max()));
                changed = light.x != clampedX || light.y != clampedY || light.z != clampedZ;
                light.x = static_cast<int16_t>(clampedX);
                light.y = static_cast<int16_t>(clampedY);
                light.z = static_cast<int16_t>(clampedZ);

                if (changed)
                {
                    assignIndoorLightToSector(indoorGeometry, session.selection().index);
                }
            }
            break;

        default:
            break;
        }

        return changed;
    }

    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();
    Game::OutdoorMapData &outdoorGeometry = document.mutableOutdoorGeometry();

    switch (session.selection().kind)
    {
    case EditorSelectionKind::Entity:
        if (session.selection().index < sceneData.entities.size())
        {
            Game::OutdoorEntity &entity = sceneData.entities[session.selection().index].entity;
            changed = entity.x != targetX || entity.y != targetY || entity.z != targetZ;
            entity.x = targetX;
            entity.y = targetY;
            entity.z = targetZ;
        }
        break;

    case EditorSelectionKind::Spawn:
        if (session.selection().index < sceneData.spawns.size())
        {
            Game::OutdoorSpawn &spawn = sceneData.spawns[session.selection().index].spawn;
            changed = spawn.x != targetX || spawn.y != targetY || spawn.z != targetZ;
            spawn.x = targetX;
            spawn.y = targetY;
            spawn.z = targetZ;
        }
        break;

    case EditorSelectionKind::Actor:
        if (session.selection().index < sceneData.initialState.actors.size())
        {
            Game::MapDeltaActor &actor = sceneData.initialState.actors[session.selection().index];
            changed = actor.x != targetX || actor.y != targetY || actor.z != targetZ;
            actor.x = targetX;
            actor.y = targetY;
            actor.z = targetZ;
        }
        break;

    case EditorSelectionKind::SpriteObject:
        if (session.selection().index < sceneData.initialState.spriteObjects.size())
        {
            Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[session.selection().index];
            changed = spriteObject.x != targetX || spriteObject.y != targetY || spriteObject.z != targetZ;
            spriteObject.x = targetX;
            spriteObject.y = targetY;
            spriteObject.z = targetZ;
        }
        break;

    case EditorSelectionKind::ModelInstance:
    case EditorSelectionKind::Mm9ScriptedObject:
        if (session.selection().index < sceneData.modelInstances.size())
        {
            Game::OutdoorSceneModelInstance &modelInstance = sceneData.modelInstances[session.selection().index];
            changed = modelInstance.x != targetX || modelInstance.y != targetY || modelInstance.z != targetZ;
            modelInstance.x = targetX;
            modelInstance.y = targetY;
            modelInstance.z = targetZ;
        }
        break;

    case EditorSelectionKind::BModel:
        if (session.selection().index < outdoorGeometry.bmodels.size())
        {
            const size_t bmodelIndex = session.selection().index;
            const std::optional<bx::Vec3> currentCenter = selectedWorldPosition(document, session.selection());

            if (!currentCenter)
            {
                break;
            }

            const int deltaX = targetX - static_cast<int>(std::lround(currentCenter->x));
            const int deltaY = targetY - static_cast<int>(std::lround(currentCenter->y));
            const int deltaZ = targetZ - static_cast<int>(std::lround(currentCenter->z));

            changed = deltaX != 0 || deltaY != 0 || deltaZ != 0;

            if (changed)
            {
                Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
                const bool trackSourceTransform =
                    document.outdoorBModelImportSource(bmodelIndex).has_value()
                    || document.outdoorBModelSourceTransform(bmodelIndex).has_value();
                EditorBModelSourceTransform sourceTransform =
                    document.outdoorBModelSourceTransform(bmodelIndex).value_or(sourceTransformFromBModel(bmodel));

                for (Game::OutdoorBModelVertex &vertex : bmodel.vertices)
                {
                    vertex.x += deltaX;
                    vertex.y += deltaY;
                    vertex.z += deltaZ;
                }

                bmodel.positionX += deltaX;
                bmodel.positionY += deltaY;
                bmodel.positionZ += deltaZ;
                bmodel.minX += deltaX;
                bmodel.minY += deltaY;
                bmodel.minZ += deltaZ;
                bmodel.maxX += deltaX;
                bmodel.maxY += deltaY;
                bmodel.maxZ += deltaZ;
                bmodel.boundingCenterX += deltaX;
                bmodel.boundingCenterY += deltaY;
                bmodel.boundingCenterZ += deltaZ;

                if (trackSourceTransform)
                {
                    sourceTransform.originX += static_cast<float>(deltaX);
                    sourceTransform.originY += static_cast<float>(deltaY);
                    sourceTransform.originZ += static_cast<float>(deltaZ);
                    document.setOutdoorBModelSourceTransform(bmodelIndex, sourceTransform);
                }

                m_geometryKey.clear();
            }
        }
        break;

    default:
        break;
    }

    return changed;
}

bool EditorOutdoorViewport::tryBeginGizmoDrag(
    EditorSession &session,
    bool leftMouseClicked,
    float mouseX,
    float mouseY)
{
    if (!leftMouseClicked || m_activeGizmoDrag.mode != GizmoDragMode::None || !session.hasDocument())
    {
        return false;
    }

    const EditorSelection selection = session.selection();
    const std::optional<bx::Vec3> selectedPosition = selectedWorldPosition(session.document(), selection);

    if (!selectedPosition)
    {
        return false;
    }

    float centerScreenX = 0.0f;
    float centerScreenY = 0.0f;
    float centerClipW = 0.0f;

    if (!projectWorldPoint(
            *selectedPosition,
            m_viewProjectionMatrix,
            m_viewportWidth,
            m_viewportHeight,
            centerScreenX,
            centerScreenY,
            centerClipW))
    {
        return false;
    }

    const float localMouseX = mouseX - static_cast<float>(m_viewportX);
    const float localMouseY = mouseY - static_cast<float>(m_viewportY);
    bx::Vec3 xAxisWorld = {1.0f, 0.0f, 0.0f};
    bx::Vec3 yAxisWorld = {0.0f, 1.0f, 0.0f};
    bx::Vec3 zAxisWorld = {0.0f, 0.0f, 1.0f};
    computeTransformBasis(session.document(), selection, m_transformSpaceMode, xAxisWorld, yAxisWorld, zAxisWorld);
    const bool useScreenSpaceTranslateGizmo =
        m_transformGizmoMode == TransformGizmoMode::Translate
        && (selection.kind == EditorSelectionKind::BModel
            || selection.kind == EditorSelectionKind::ModelInstance
            || selection.kind == EditorSelectionKind::Mm9ScriptedObject
            || isIndoorMovableSelectionKind(selection.kind));
    const float axisWorldLength = useScreenSpaceTranslateGizmo ? IndoorGizmoAxisWorldLength : GizmoAxisWorldLength;
    const bx::Vec3 xAxisPoint = vecAdd(*selectedPosition, vecScale(xAxisWorld, axisWorldLength));
    const bx::Vec3 yAxisPoint = vecAdd(*selectedPosition, vecScale(yAxisWorld, axisWorldLength));
    const bx::Vec3 zAxisPoint = vecAdd(*selectedPosition, vecScale(zAxisWorld, axisWorldLength));
    float xAxisScreenX = 0.0f;
    float xAxisScreenY = 0.0f;
    float yAxisScreenX = 0.0f;
    float yAxisScreenY = 0.0f;
    float zAxisScreenX = 0.0f;
    float zAxisScreenY = 0.0f;
    float axisClipW = 0.0f;
    bool hasXAxis = projectWorldPoint(
        xAxisPoint,
        m_viewProjectionMatrix,
        m_viewportWidth,
        m_viewportHeight,
        xAxisScreenX,
        xAxisScreenY,
        axisClipW);
    bool hasYAxis = projectWorldPoint(
        yAxisPoint,
        m_viewProjectionMatrix,
        m_viewportWidth,
        m_viewportHeight,
        yAxisScreenX,
        yAxisScreenY,
        axisClipW);
    bool hasZAxis = projectWorldPoint(
        zAxisPoint,
        m_viewProjectionMatrix,
        m_viewportWidth,
        m_viewportHeight,
        zAxisScreenX,
        zAxisScreenY,
        axisClipW);

    if (useScreenSpaceTranslateGizmo)
    {
        const auto fitIndoorAxisToScreen =
            [centerScreenX, centerScreenY](
                bool projected,
                float &axisScreenX,
                float &axisScreenY,
                float fallbackX,
                float fallbackY)
        {
            float directionX = fallbackX;
            float directionY = fallbackY;

            if (projected)
            {
                const float deltaX = axisScreenX - centerScreenX;
                const float deltaY = axisScreenY - centerScreenY;
                const float length = std::sqrt(deltaX * deltaX + deltaY * deltaY);

                if (length >= 8.0f)
                {
                    directionX = deltaX / length;
                    directionY = deltaY / length;
                }
            }

            axisScreenX = centerScreenX + directionX * IndoorGizmoScreenAxisLength;
            axisScreenY = centerScreenY + directionY * IndoorGizmoScreenAxisLength;
            return true;
        };

        hasXAxis = fitIndoorAxisToScreen(hasXAxis, xAxisScreenX, xAxisScreenY, 1.0f, 0.0f);
        hasYAxis = fitIndoorAxisToScreen(hasYAxis, yAxisScreenX, yAxisScreenY, 0.0f, 1.0f);
        hasZAxis = fitIndoorAxisToScreen(hasZAxis, zAxisScreenX, zAxisScreenY, 0.0f, -1.0f);
    }

    const bool useRotateGizmo =
        selection.kind == EditorSelectionKind::BModel && m_transformGizmoMode == TransformGizmoMode::Rotate;
    float rotateHandleRadiusWorld = 0.0f;
    float rotatePickDistanceSquared = std::numeric_limits<float>::max();
    GizmoDragMode rotateMode = GizmoDragMode::None;
    bx::Vec3 rotateAxisWorld = {0.0f, 0.0f, 1.0f};

    if (useRotateGizmo && selection.index < session.document().outdoorGeometry().bmodels.size())
    {
        const Game::OutdoorBModel &bmodel = session.document().outdoorGeometry().bmodels[selection.index];
        rotateHandleRadiusWorld = bmodelRotationHandleRadius(bmodel);
        const auto evaluateRotationRing =
            [this,
             localMouseX,
             localMouseY,
             selectedPosition,
             rotateHandleRadiusWorld](
                const bx::Vec3 &axis,
                GizmoDragMode candidateMode,
                float &bestDistanceSquared,
                GizmoDragMode &bestMode,
                bx::Vec3 &bestAxis)
        {
            std::vector<ScreenPoint> ringPoints;
            ringPoints.reserve(GizmoRotationSegments + 1);

            for (int segmentIndex = 0; segmentIndex <= GizmoRotationSegments; ++segmentIndex)
            {
                const float angle = (static_cast<float>(segmentIndex) / static_cast<float>(GizmoRotationSegments)) * bx::kPi2;
                bx::Vec3 ringPoint = *selectedPosition;

                if (std::fabs(axis.x) > 0.5f)
                {
                    ringPoint.y += std::cos(angle) * rotateHandleRadiusWorld;
                    ringPoint.z += std::sin(angle) * rotateHandleRadiusWorld;
                }
                else if (std::fabs(axis.y) > 0.5f)
                {
                    ringPoint.x += std::cos(angle) * rotateHandleRadiusWorld;
                    ringPoint.z += std::sin(angle) * rotateHandleRadiusWorld;
                }
                else
                {
                    ringPoint.x += std::cos(angle) * rotateHandleRadiusWorld;
                    ringPoint.y += std::sin(angle) * rotateHandleRadiusWorld;
                }

                float projectedX = 0.0f;
                float projectedY = 0.0f;
                float clipW = 0.0f;

                if (!projectWorldPoint(
                        ringPoint,
                        m_viewProjectionMatrix,
                        m_viewportWidth,
                        m_viewportHeight,
                        projectedX,
                        projectedY,
                        clipW))
                {
                    return;
                }

                ringPoints.push_back({projectedX, projectedY});
            }

            for (size_t index = 1; index < ringPoints.size(); ++index)
            {
                const float distanceSquared = distancePointToSegmentSquared(
                    localMouseX,
                    localMouseY,
                    ringPoints[index - 1].x,
                    ringPoints[index - 1].y,
                    ringPoints[index].x,
                    ringPoints[index].y);

                if (distanceSquared < bestDistanceSquared)
                {
                    bestDistanceSquared = distanceSquared;
                    bestMode = candidateMode;
                    bestAxis = axis;
                }
            }
        };

        evaluateRotationRing(xAxisWorld, GizmoDragMode::RotateX, rotatePickDistanceSquared, rotateMode, rotateAxisWorld);
        evaluateRotationRing(yAxisWorld, GizmoDragMode::RotateY, rotatePickDistanceSquared, rotateMode, rotateAxisWorld);
        evaluateRotationRing(zAxisWorld, GizmoDragMode::RotateZ, rotatePickDistanceSquared, rotateMode, rotateAxisWorld);
    }

    const float xAxisDistanceSquared = hasXAxis
        ? distancePointToSegmentSquared(
            localMouseX,
            localMouseY,
            centerScreenX,
            centerScreenY,
            xAxisScreenX,
            xAxisScreenY)
        : std::numeric_limits<float>::max();
    const float yAxisDistanceSquared = hasYAxis
        ? distancePointToSegmentSquared(
            localMouseX,
            localMouseY,
            centerScreenX,
            centerScreenY,
            yAxisScreenX,
            yAxisScreenY)
        : std::numeric_limits<float>::max();
    const float zAxisDistanceSquared = hasZAxis
        ? distancePointToSegmentSquared(
            localMouseX,
            localMouseY,
            centerScreenX,
            centerScreenY,
            zAxisScreenX,
            zAxisScreenY)
        : std::numeric_limits<float>::max();
    const float zAxisEndpointDistanceSquared =
        hasZAxis ? squaredLength2(localMouseX - zAxisScreenX, localMouseY - zAxisScreenY) : std::numeric_limits<float>::max();

    GizmoDragMode mode = GizmoDragMode::None;

    const float axisPickSlack = useScreenSpaceTranslateGizmo ? IndoorGizmoAxisPickSlackPixels : GizmoAxisPickSlackPixels;
    const float zAxisPickSlack = useScreenSpaceTranslateGizmo ? IndoorGizmoAxisPickSlackPixels : GizmoZAxisPickSlackPixels;
    const float endpointPickRadius =
        useScreenSpaceTranslateGizmo ? IndoorGizmoAxisEndpointPickRadiusPixels : GizmoAxisEndpointPickRadiusPixels;

    if (useRotateGizmo)
    {
        if (rotatePickDistanceSquared <= GizmoRotationPickSlackPixels * GizmoRotationPickSlackPixels)
        {
            mode = rotateMode;
        }
    }
    else if (hasZAxis
        && (zAxisDistanceSquared <= zAxisPickSlack * zAxisPickSlack
            || zAxisEndpointDistanceSquared
                <= endpointPickRadius * endpointPickRadius))
    {
        mode = GizmoDragMode::TranslateZ;
    }
    else if (!useScreenSpaceTranslateGizmo
        && squaredLength2(localMouseX - centerScreenX, localMouseY - centerScreenY)
        <= GizmoCenterPickRadiusPixels * GizmoCenterPickRadiusPixels)
    {
        mode = GizmoDragMode::TranslatePlaneXY;
    }
    else if (hasXAxis && xAxisDistanceSquared <= axisPickSlack * axisPickSlack)
    {
        mode = GizmoDragMode::TranslateX;
    }
    else if (hasYAxis && yAxisDistanceSquared <= axisPickSlack * axisPickSlack)
    {
        mode = GizmoDragMode::TranslateY;
    }

    if (mode == GizmoDragMode::None)
    {
        return false;
    }

    session.captureUndoSnapshot();
    m_activeGizmoDrag.mode = mode;
    m_activeGizmoDrag.selection = selection;
    m_activeGizmoDrag.startWorldPosition = *selectedPosition;
    m_activeGizmoDrag.startMouseX = localMouseX;
    m_activeGizmoDrag.startMouseY = localMouseY;
    m_activeGizmoDrag.startScreenX = centerScreenX;
    m_activeGizmoDrag.startScreenY = centerScreenY;
    m_activeGizmoDrag.xAxisScreenX = xAxisScreenX;
    m_activeGizmoDrag.xAxisScreenY = xAxisScreenY;
    m_activeGizmoDrag.yAxisScreenX = yAxisScreenX;
    m_activeGizmoDrag.yAxisScreenY = yAxisScreenY;
    m_activeGizmoDrag.zAxisScreenX = zAxisScreenX;
    m_activeGizmoDrag.zAxisScreenY = zAxisScreenY;
    m_activeGizmoDrag.axisWorldLength = axisWorldLength;
    m_activeGizmoDrag.xAxisWorld = xAxisWorld;
    m_activeGizmoDrag.yAxisWorld = yAxisWorld;
    m_activeGizmoDrag.zAxisWorld = zAxisWorld;
    m_activeGizmoDrag.rotateHandleRadiusWorld = rotateHandleRadiusWorld;
    m_activeGizmoDrag.rotateAxisWorld = rotateAxisWorld;
    m_activeGizmoDrag.startRotateVectorWorld = {1.0f, 0.0f, 0.0f};
    m_activeGizmoDrag.startBModelVertices.clear();
    m_activeGizmoDrag.hasStartSourceTransform = false;

    if ((mode == GizmoDragMode::RotateX
            || mode == GizmoDragMode::RotateY
            || mode == GizmoDragMode::RotateZ)
        && selection.kind == EditorSelectionKind::BModel
        && selection.index < session.document().outdoorGeometry().bmodels.size())
    {
        bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
        bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};
        bx::Vec3 intersection = {0.0f, 0.0f, 0.0f};

        if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection)
            || !intersectRayPlane(
                rayOrigin,
                rayDirection,
                *selectedPosition,
                rotateAxisWorld,
                intersection))
        {
            m_activeGizmoDrag = {};
            return false;
        }

        const bx::Vec3 rotateVector = {
            intersection.x - selectedPosition->x,
            intersection.y - selectedPosition->y,
            intersection.z - selectedPosition->z
        };

        if (vecLength(rotateVector) <= 1.0f)
        {
            m_activeGizmoDrag = {};
            return false;
        }

        m_activeGizmoDrag.startRotateVectorWorld = vecNormalize(rotateVector);
        m_activeGizmoDrag.startBModelVertices =
            session.document().outdoorGeometry().bmodels[selection.index].vertices;
        m_activeGizmoDrag.startSourceTransform =
            session.document().outdoorBModelSourceTransform(selection.index).value_or(
                sourceTransformFromBModel(session.document().outdoorGeometry().bmodels[selection.index]));
        m_activeGizmoDrag.hasStartSourceTransform =
            session.document().outdoorBModelImportSource(selection.index).has_value()
            || session.document().outdoorBModelSourceTransform(selection.index).has_value();
    }

    m_activeGizmoDrag.mutated = false;
    return true;
}

void EditorOutdoorViewport::updateGizmoDrag(
    EditorSession &session,
    bool leftMouseDown,
    float mouseX,
    float mouseY)
{
    if (m_activeGizmoDrag.mode == GizmoDragMode::None)
    {
        return;
    }

    if (!leftMouseDown)
    {
        if (m_activeGizmoDrag.mutated)
        {
            session.noteDocumentMutated({});
        }

        m_activeGizmoDrag = {};
        return;
    }

    if (session.selection().kind != m_activeGizmoDrag.selection.kind
        || session.selection().index != m_activeGizmoDrag.selection.index)
    {
        if (m_activeGizmoDrag.mutated)
        {
            session.noteDocumentMutated({});
        }

        m_activeGizmoDrag = {};
        return;
    }

    const float localMouseX = mouseX - static_cast<float>(m_viewportX);
    const float localMouseY = mouseY - static_cast<float>(m_viewportY);
    const float deltaMouseX = localMouseX - m_activeGizmoDrag.startMouseX;
    const float deltaMouseY = localMouseY - m_activeGizmoDrag.startMouseY;
    const bool translateDrag =
        m_activeGizmoDrag.mode == GizmoDragMode::TranslateX
        || m_activeGizmoDrag.mode == GizmoDragMode::TranslateY
        || m_activeGizmoDrag.mode == GizmoDragMode::TranslateZ
        || m_activeGizmoDrag.mode == GizmoDragMode::TranslatePlaneXY;

    if (translateDrag
        && !m_activeGizmoDrag.mutated
        && squaredLength2(deltaMouseX, deltaMouseY) < GizmoDragDeadzonePixels * GizmoDragDeadzonePixels)
    {
        return;
    }

    bx::Vec3 updatedPosition = m_activeGizmoDrag.startWorldPosition;

    switch (m_activeGizmoDrag.mode)
    {
    case GizmoDragMode::TranslateX:
    {
        const float axisScreenDeltaX = m_activeGizmoDrag.xAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float axisScreenDeltaY = m_activeGizmoDrag.xAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float axisScreenLengthSquared = squaredLength2(axisScreenDeltaX, axisScreenDeltaY);

        if (axisScreenLengthSquared > 0.0001f)
        {
            const float pixelProjection =
                (deltaMouseX * axisScreenDeltaX + deltaMouseY * axisScreenDeltaY)
                / std::sqrt(axisScreenLengthSquared);
            const float axisScreenLength = std::sqrt(axisScreenLengthSquared);
            updatedPosition = vecAdd(
                updatedPosition,
                vecScale(
                    m_activeGizmoDrag.xAxisWorld,
                    (pixelProjection / axisScreenLength) * m_activeGizmoDrag.axisWorldLength));
        }
        break;
    }

    case GizmoDragMode::TranslateY:
    {
        const float axisScreenDeltaX = m_activeGizmoDrag.yAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float axisScreenDeltaY = m_activeGizmoDrag.yAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float axisScreenLengthSquared = squaredLength2(axisScreenDeltaX, axisScreenDeltaY);

        if (axisScreenLengthSquared > 0.0001f)
        {
            const float pixelProjection =
                (deltaMouseX * axisScreenDeltaX + deltaMouseY * axisScreenDeltaY)
                / std::sqrt(axisScreenLengthSquared);
            const float axisScreenLength = std::sqrt(axisScreenLengthSquared);
            updatedPosition = vecAdd(
                updatedPosition,
                vecScale(
                    m_activeGizmoDrag.yAxisWorld,
                    (pixelProjection / axisScreenLength) * m_activeGizmoDrag.axisWorldLength));
        }
        break;
    }

    case GizmoDragMode::TranslateZ:
    {
        const float axisScreenDeltaX = m_activeGizmoDrag.zAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float axisScreenDeltaY = m_activeGizmoDrag.zAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float axisScreenLengthSquared = squaredLength2(axisScreenDeltaX, axisScreenDeltaY);

        if (axisScreenLengthSquared > 0.0001f)
        {
            const float pixelProjection =
                (deltaMouseX * axisScreenDeltaX + deltaMouseY * axisScreenDeltaY)
                / std::sqrt(axisScreenLengthSquared);
            const float axisScreenLength = std::sqrt(axisScreenLengthSquared);
            updatedPosition = vecAdd(
                updatedPosition,
                vecScale(
                    m_activeGizmoDrag.zAxisWorld,
                    (pixelProjection / axisScreenLength) * m_activeGizmoDrag.axisWorldLength));
        }
        break;
    }

    case GizmoDragMode::TranslatePlaneXY:
    {
        const float xScreenX = m_activeGizmoDrag.xAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float xScreenY = m_activeGizmoDrag.xAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float yScreenX = m_activeGizmoDrag.yAxisScreenX - m_activeGizmoDrag.startScreenX;
        const float yScreenY = m_activeGizmoDrag.yAxisScreenY - m_activeGizmoDrag.startScreenY;
        const float determinant = xScreenX * yScreenY - xScreenY * yScreenX;

        if (std::fabs(determinant) > 0.0001f)
        {
            const float invDeterminant = 1.0f / determinant;
            const float xCoeff = (deltaMouseX * yScreenY - deltaMouseY * yScreenX) * invDeterminant;
            const float yCoeff = (deltaMouseY * xScreenX - deltaMouseX * xScreenY) * invDeterminant;
            updatedPosition = vecAdd(
                updatedPosition,
                vecAdd(
                    vecScale(m_activeGizmoDrag.xAxisWorld, xCoeff * m_activeGizmoDrag.axisWorldLength),
                    vecScale(m_activeGizmoDrag.yAxisWorld, yCoeff * m_activeGizmoDrag.axisWorldLength)));
        }
        break;
    }

    case GizmoDragMode::RotateX:
    case GizmoDragMode::RotateY:
    case GizmoDragMode::RotateZ:
    {
        if (m_activeGizmoDrag.selection.kind == EditorSelectionKind::BModel
            && m_activeGizmoDrag.selection.index < session.document().mutableOutdoorGeometry().bmodels.size())
        {
            bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
            bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};
            bx::Vec3 intersection = {0.0f, 0.0f, 0.0f};

            if (!computeMouseRay(mouseX, mouseY, rayOrigin, rayDirection)
                || !intersectRayPlane(
                    rayOrigin,
                    rayDirection,
                    m_activeGizmoDrag.startWorldPosition,
                    m_activeGizmoDrag.rotateAxisWorld,
                    intersection))
            {
                return;
            }

            const bx::Vec3 currentRotateVector = {
                intersection.x - m_activeGizmoDrag.startWorldPosition.x,
                intersection.y - m_activeGizmoDrag.startWorldPosition.y,
                intersection.z - m_activeGizmoDrag.startWorldPosition.z
            };

            if (vecLength(currentRotateVector) <= 1.0f)
            {
                return;
            }

            const float deltaAngleRadians = signedAngleAroundAxis(
                m_activeGizmoDrag.startRotateVectorWorld,
                currentRotateVector,
                m_activeGizmoDrag.rotateAxisWorld);
            Game::OutdoorBModel &bmodel =
                session.document().mutableOutdoorGeometry().bmodels[m_activeGizmoDrag.selection.index];

            if (applyBModelAxisRotation(
                    bmodel,
                    m_activeGizmoDrag.startBModelVertices,
                    m_activeGizmoDrag.startWorldPosition,
                    m_activeGizmoDrag.rotateAxisWorld,
                    deltaAngleRadians))
            {
                if (m_activeGizmoDrag.hasStartSourceTransform)
                {
                    EditorBModelSourceTransform sourceTransform = m_activeGizmoDrag.startSourceTransform;
                    sourceTransform.basisX = rotateBasisVectorAroundAxis(
                        sourceTransform.basisX,
                        m_activeGizmoDrag.rotateAxisWorld,
                        deltaAngleRadians);
                    sourceTransform.basisY = rotateBasisVectorAroundAxis(
                        sourceTransform.basisY,
                        m_activeGizmoDrag.rotateAxisWorld,
                        deltaAngleRadians);
                    sourceTransform.basisZ = rotateBasisVectorAroundAxis(
                        sourceTransform.basisZ,
                        m_activeGizmoDrag.rotateAxisWorld,
                        deltaAngleRadians);
                    session.document().setOutdoorBModelSourceTransform(m_activeGizmoDrag.selection.index, sourceTransform);
                }

                session.document().setDirty(true);
                session.document().touchSceneRevision();
                m_geometryKey.clear();
                m_activeGizmoDrag.mutated = true;
            }
        }
        return;
    }

    case GizmoDragMode::None:
        break;
    }

    if (setSelectedWorldPosition(session, updatedPosition))
    {
        session.document().setDirty(true);
        m_activeGizmoDrag.mutated = true;
    }
}

void EditorOutdoorViewport::submitStaticGeometry(const EditorSession &session) const
{
    float transform[16] = {};
    bx::mtxIdentity(transform);
    const auto submitProceduralBatch =
        [this, &transform](
            const bgfx::VertexBufferHandle vertexBufferHandle,
            uint32_t vertexCount,
            const bx::Vec3 &objectOrigin,
            const ClayPreviewSettings &settings,
            bool depthEqual,
            bool blendAlpha = false,
            bool writeDepth = true,
            const float *pBatchTransform = nullptr) -> void
    {
        if (!bgfx::isValid(vertexBufferHandle)
            || vertexCount == 0
            || !bgfx::isValid(m_proceduralPreviewProgramHandle))
        {
            return;
        }

        const float *pTransform = pBatchTransform != nullptr ? pBatchTransform : transform;
        const bx::Vec3 transformedObjectOrigin = transformPointByMatrix(pBatchTransform, objectOrigin);
        const std::array<float, 4> params0 = {
            settings.slopeAccentStrength,
            settings.shadowStrength,
            settings.lightWrap,
            0.0f
        };
        const std::array<float, 4> params1 = {0.0f, 0.0f, 0.0f, 0.0f};
        const std::array<float, 4> previewOrigin = {
            transformedObjectOrigin.x,
            transformedObjectOrigin.y,
            transformedObjectOrigin.z,
            0.0f
        };
        bgfx::setUniform(m_previewColorAHandle, settings.baseColor.data());
        bgfx::setUniform(m_previewParams0Handle, params0.data());
        bgfx::setUniform(m_previewParams1Handle, params1.data());
        bgfx::setUniform(m_previewObjectOriginHandle, previewOrigin.data());
        bgfx::setTransform(pTransform);
        bgfx::setVertexBuffer(0, vertexBufferHandle);
        uint64_t state =
            BGFX_STATE_WRITE_RGB
            | BGFX_STATE_WRITE_A
            | (depthEqual ? BGFX_STATE_DEPTH_TEST_LEQUAL : BGFX_STATE_DEPTH_TEST_LESS)
            | BGFX_STATE_MSAA;

        if (writeDepth)
        {
            state |= BGFX_STATE_WRITE_Z;
        }

        if (blendAlpha)
        {
            state |= BGFX_STATE_BLEND_ALPHA;
        }

        bgfx::setState(
            state);
        bgfx::submit(EditorSceneViewId, m_proceduralPreviewProgramHandle);
    };
    const auto submitGridBatch =
        [this, &transform](
            const bgfx::VertexBufferHandle vertexBufferHandle,
            uint32_t vertexCount,
            const bx::Vec3 &objectOrigin,
            const GridPreviewSettings &settings,
            float materialMode,
            bool depthEqual,
            const float *pBatchTransform = nullptr) -> void
    {
        if (!bgfx::isValid(vertexBufferHandle)
            || vertexCount == 0
            || !bgfx::isValid(m_proceduralPreviewProgramHandle))
        {
            return;
        }

        const float *pTransform = pBatchTransform != nullptr ? pBatchTransform : transform;
        const bx::Vec3 transformedObjectOrigin = transformPointByMatrix(pBatchTransform, objectOrigin);
        const std::array<float, 4> params0 = {
            settings.cellSize,
            settings.majorInterval,
            settings.lineThickness,
            settings.majorLineThickness
        };
        const std::array<float, 4> params1 = {materialMode, 0.0f, 0.0f, 0.0f};
        const std::array<float, 4> previewOrigin = {
            transformedObjectOrigin.x,
            transformedObjectOrigin.y,
            transformedObjectOrigin.z,
            0.0f
        };
        bgfx::setUniform(m_previewColorAHandle, settings.baseColorA.data());
        bgfx::setUniform(m_previewColorBHandle, settings.baseColorB.data());
        bgfx::setUniform(m_previewColorCHandle, settings.minorLineColor.data());
        bgfx::setUniform(m_previewColorDHandle, settings.majorLineColor.data());
        bgfx::setUniform(m_previewParams0Handle, params0.data());
        bgfx::setUniform(m_previewParams1Handle, params1.data());
        bgfx::setUniform(m_previewObjectOriginHandle, previewOrigin.data());
        bgfx::setTransform(pTransform);
        bgfx::setVertexBuffer(0, vertexBufferHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | (depthEqual ? BGFX_STATE_DEPTH_TEST_LEQUAL : BGFX_STATE_DEPTH_TEST_LESS)
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_proceduralPreviewProgramHandle);
    };
    const auto submitModelInstanceBatches =
        [this, &transform, &submitGridBatch, &submitProceduralBatch]() -> void
    {
        if (!m_showModelInstances)
        {
            return;
        }

        for (const ProceduralBatch &batch : m_modelInstanceBatches)
        {
            if (!bgfx::isValid(batch.vertexBufferHandle)
                || batch.vertexCount == 0
                || !bgfx::isValid(m_proceduralPreviewProgramHandle))
            {
                continue;
            }

            if (m_previewMaterialMode == PreviewMaterialMode::Grid)
            {
                submitGridBatch(
                    batch.vertexBufferHandle,
                    batch.vertexCount,
                    batch.objectOrigin,
                    m_gridPreviewSettings,
                    1.0f,
                    false);
            }
            else
            {
                submitProceduralBatch(
                    batch.vertexBufferHandle,
                    batch.vertexCount,
                    batch.objectOrigin,
                    m_clayPreviewSettings,
                    false);
            }

            ++m_lastRenderSubmissionStats.modelInstanceProceduralSubmissions;
            m_lastRenderSubmissionStats.modelInstanceSubmittedVertices += batch.vertexCount;
        }

        if (bgfx::isValid(m_texturedProgramHandle) && bgfx::isValid(m_textureSamplerHandle))
        {
            for (const TexturedBatch &batch : m_modelInstanceTexturedBatches)
            {
                if (!bgfx::isValid(batch.vertexBufferHandle)
                    || !bgfx::isValid(batch.textureHandle)
                    || batch.vertexCount == 0)
                {
                    continue;
                }

                bgfx::setTransform(transform);
                bgfx::setVertexBuffer(0, batch.vertexBufferHandle);
                bgfx::setTexture(0, m_textureSamplerHandle, batch.textureHandle);
                uint64_t state =
                    BGFX_STATE_WRITE_RGB
                        | BGFX_STATE_WRITE_A
                        | BGFX_STATE_DEPTH_TEST_LESS
                        | BGFX_STATE_MSAA;
                if (batch.hasTransparentPixels)
                {
                    state |= BGFX_STATE_BLEND_ALPHA;
                }
                else
                {
                    state |= BGFX_STATE_WRITE_Z;
                }
                bgfx::setState(state);
                bgfx::submit(EditorSceneViewId, m_texturedProgramHandle);
                ++m_lastRenderSubmissionStats.modelInstanceTexturedSubmissions;
                m_lastRenderSubmissionStats.modelInstanceSubmittedVertices += batch.vertexCount;
            }
        }

        for (const ProceduralBatch &batch : m_modelInstanceMissingBatches)
        {
            if (!bgfx::isValid(batch.vertexBufferHandle)
                || batch.vertexCount == 0
                || !bgfx::isValid(m_proceduralPreviewProgramHandle))
            {
                continue;
            }

            submitGridBatch(
                batch.vertexBufferHandle,
                batch.vertexCount,
                batch.objectOrigin,
                m_errorPreviewSettings,
                2.0f,
                true);
            ++m_lastRenderSubmissionStats.modelInstanceMissingSubmissions;
            m_lastRenderSubmissionStats.modelInstanceSubmittedVertices += batch.vertexCount;
        }
    };

    if (session.document().kind() == EditorDocument::Kind::Mm9Dat)
    {
        const bool showDatWorld = m_showTerrainFill || m_showBModels;
        std::unordered_map<size_t, std::array<float, 16>> previewTransformsBySourceModelIndex;

        if (session.document().hasMm9DatLoadedSidecars())
        {
            const std::vector<Mm9MechanismPreviewCacheEntry> &mechanismPreviewCache =
                mm9MechanismPreviewCache(session.document());
            previewTransformsBySourceModelIndex =
                mm9ViewportPreviewTransformsBySourceModelIndex(
                    buildMm9ViewportPreviewMotions(
                        mechanismPreviewCache,
                        m_mm9MechanismPreviewProgressByIndex));
        }

        const auto previewTransformForMm9Batch =
            [&previewTransformsBySourceModelIndex](size_t bmodelIndex) -> const float *
        {
            if (bmodelIndex == std::numeric_limits<size_t>::max())
            {
                return nullptr;
            }

            const auto transformIt = previewTransformsBySourceModelIndex.find(bmodelIndex);
            return transformIt != previewTransformsBySourceModelIndex.end() ? transformIt->second.data() : nullptr;
        };

        if (!showDatWorld
            && m_modelInstanceBatches.empty()
            && m_modelInstanceTexturedBatches.empty()
            && m_modelInstanceMissingBatches.empty()
            && (!m_showMm9DatPortals || m_mm9DatPortalOverlayVertexCount == 0)
            && (!m_showMm9WorldModelBounds || m_mm9DatWorldModelOverlayVertexCount == 0)
            && (!m_showMm9ObjectBounds || m_mm9DatObjectOverlayVertexCount == 0))
        {
            return;
        }

        if (showDatWorld
            && m_previewMaterialMode == PreviewMaterialMode::Textured
            && bgfx::isValid(m_texturedProgramHandle)
            && bgfx::isValid(m_textureSamplerHandle))
        {
            for (const TexturedBatch &batch : m_bmodelTexturedBatches)
            {
                if (!bgfx::isValid(batch.vertexBufferHandle)
                    || !bgfx::isValid(batch.textureHandle)
                    || batch.vertexCount == 0)
                {
                    continue;
                }

                const float *pBatchTransform = previewTransformForMm9Batch(batch.bmodelIndex);
                bgfx::setTransform(pBatchTransform != nullptr ? pBatchTransform : transform);
                bgfx::setVertexBuffer(0, batch.vertexBufferHandle);
                bgfx::setTexture(0, m_textureSamplerHandle, batch.textureHandle);
                uint64_t state =
                    BGFX_STATE_WRITE_RGB
                        | BGFX_STATE_WRITE_A
                        | BGFX_STATE_DEPTH_TEST_LESS
                        | BGFX_STATE_MSAA;
                if (batch.hasTransparentPixels)
                {
                    state |= BGFX_STATE_BLEND_ALPHA;
                }
                else
                {
                    state |= BGFX_STATE_WRITE_Z;
                }
                bgfx::setState(state);
                bgfx::submit(EditorSceneViewId, m_texturedProgramHandle);
                ++m_lastRenderSubmissionStats.datWorldTexturedSubmissions;
                m_lastRenderSubmissionStats.datWorldSubmittedVertices += batch.vertexCount;
            }

            for (const ProceduralBatch &batch : m_bmodelMissingAssetBatches)
            {
                if (!bgfx::isValid(batch.vertexBufferHandle)
                    || batch.vertexCount == 0
                    || !bgfx::isValid(m_proceduralPreviewProgramHandle))
                {
                    continue;
                }

                submitGridBatch(
                    batch.vertexBufferHandle,
                    batch.vertexCount,
                    batch.objectOrigin,
                    m_errorPreviewSettings,
                    2.0f,
                    true,
                    previewTransformForMm9Batch(batch.bmodelIndex));
                ++m_lastRenderSubmissionStats.datWorldMissingMaterialSubmissions;
                m_lastRenderSubmissionStats.datWorldSubmittedVertices += batch.vertexCount;
            }
        }
        else if (showDatWorld)
        {
            for (const ProceduralBatch &batch : m_bmodelAllFaceBatches)
            {
                if (!bgfx::isValid(batch.vertexBufferHandle)
                    || batch.vertexCount == 0
                    || !bgfx::isValid(m_proceduralPreviewProgramHandle))
                {
                    continue;
                }

                const float *pBatchTransform = previewTransformForMm9Batch(batch.bmodelIndex);

                if (m_previewMaterialMode == PreviewMaterialMode::Grid)
                {
                    submitGridBatch(
                        batch.vertexBufferHandle,
                        batch.vertexCount,
                        batch.objectOrigin,
                        m_gridPreviewSettings,
                        1.0f,
                        false,
                        pBatchTransform);
                }
                else
                {
                    submitProceduralBatch(
                        batch.vertexBufferHandle,
                        batch.vertexCount,
                        batch.objectOrigin,
                        m_clayPreviewSettings,
                        false,
                        false,
                        true,
                        pBatchTransform);
                }

                ++m_lastRenderSubmissionStats.datWorldProceduralSubmissions;
                m_lastRenderSubmissionStats.datWorldSubmittedVertices += batch.vertexCount;
            }
        }

        submitModelInstanceBatches();

        if (m_showMm9DatPortals
            && bgfx::isValid(m_mm9DatPortalOverlayVertexBufferHandle)
            && m_mm9DatPortalOverlayVertexCount > 0
            && bgfx::isValid(m_programHandle))
        {
            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, m_mm9DatPortalOverlayVertexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_DEPTH_TEST_LEQUAL
                    | BGFX_STATE_PT_LINES
                    | BGFX_STATE_MSAA);
            bgfx::submit(EditorSceneViewId, m_programHandle);
            ++m_lastRenderSubmissionStats.mm9DatPortalOverlaySubmissions;
            m_lastRenderSubmissionStats.mm9DatPortalOverlayVertices += m_mm9DatPortalOverlayVertexCount;
        }

        if (m_showMm9WorldModelBounds
            && bgfx::isValid(m_mm9DatWorldModelOverlayVertexBufferHandle)
            && m_mm9DatWorldModelOverlayVertexCount > 0
            && bgfx::isValid(m_programHandle))
        {
            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, m_mm9DatWorldModelOverlayVertexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_DEPTH_TEST_LEQUAL
                    | BGFX_STATE_PT_LINES
                    | BGFX_STATE_MSAA);
            bgfx::submit(EditorSceneViewId, m_programHandle);
            ++m_lastRenderSubmissionStats.mm9DatWorldModelOverlaySubmissions;
            m_lastRenderSubmissionStats.mm9DatWorldModelOverlayVertices += m_mm9DatWorldModelOverlayVertexCount;
        }

        if (m_showMm9ObjectBounds
            && bgfx::isValid(m_mm9DatObjectOverlayVertexBufferHandle)
            && m_mm9DatObjectOverlayVertexCount > 0
            && bgfx::isValid(m_programHandle))
        {
            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, m_mm9DatObjectOverlayVertexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_DEPTH_TEST_LEQUAL
                    | BGFX_STATE_PT_LINES
                    | BGFX_STATE_MSAA);
            bgfx::submit(EditorSceneViewId, m_programHandle);
            ++m_lastRenderSubmissionStats.mm9DatObjectOverlaySubmissions;
            m_lastRenderSubmissionStats.mm9DatObjectOverlayVertices += m_mm9DatObjectOverlayVertexCount;
        }

        return;
    }

    if (session.document().kind() == EditorDocument::Kind::Indoor)
    {
        for (const TexturedBatch &batch : m_bmodelTexturedBatches)
        {
            if (!bgfx::isValid(batch.vertexBufferHandle) || !bgfx::isValid(batch.textureHandle) || batch.vertexCount == 0)
            {
                continue;
            }

            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, batch.vertexBufferHandle);
            bgfx::setTexture(0, m_textureSamplerHandle, batch.textureHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LESS
                    | BGFX_STATE_MSAA);
            bgfx::submit(EditorSceneViewId, m_texturedProgramHandle);
        }

        for (const ProceduralBatch &batch : m_bmodelUnassignedBatches)
        {
            submitGridBatch(
                batch.vertexBufferHandle,
                batch.vertexCount,
                batch.objectOrigin,
                m_gridPreviewSettings,
                1.0f,
                false);
        }

        for (const ProceduralBatch &batch : m_bmodelMissingAssetBatches)
        {
            submitGridBatch(
                batch.vertexBufferHandle,
                batch.vertexCount,
                batch.objectOrigin,
                m_errorPreviewSettings,
                2.0f,
                true);
        }

        if (m_showIndoorPortals)
        {
            for (const ProceduralBatch &batch : m_indoorPortalBatches)
            {
                submitProceduralBatch(
                    batch.vertexBufferHandle,
                    batch.vertexCount,
                    batch.objectOrigin,
                    m_indoorPortalPreviewSettings,
                    true,
                    true,
                    false);
            }
        }

        if (m_showBModelWireframe && bgfx::isValid(m_bmodelWireVertexBufferHandle) && m_bmodelWireVertexCount > 0)
        {
            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, m_bmodelWireVertexBufferHandle);
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LESS
                    | BGFX_STATE_PT_LINES
                    | BGFX_STATE_MSAA);
            bgfx::submit(EditorSceneViewId, m_programHandle);
        }

        return;
    }

    const bool renderTerrainHeightmap = shouldRenderTerrainHeightmap(session.document());
    const bool terrainUsesClay =
        m_previewMaterialMode == PreviewMaterialMode::Clay
        || !bgfx::isValid(m_texturedTerrainVertexBufferHandle)
        || !bgfx::isValid(m_terrainTextureAtlasHandle);
    std::optional<size_t> selectedBModelIndex;
    const EditorSelection &selection = session.selection();

    if (selection.kind == EditorSelectionKind::BModel)
    {
        selectedBModelIndex = selection.index;
    }
    else if (selection.kind == EditorSelectionKind::InteractiveFace)
    {
        size_t bmodelIndex = 0;
        size_t faceIndex = 0;

        if (decodeSelectedInteractiveFace(session.document(), selection, bmodelIndex, faceIndex))
        {
            selectedBModelIndex = bmodelIndex;
        }
    }

    const auto shouldForcePreviewForBModel =
        [this, &selectedBModelIndex](size_t bmodelIndex) -> bool
    {
        if (m_previewMaterialMode == PreviewMaterialMode::Textured || !m_forcePreviewOnSelectedOnly)
        {
            return false;
        }

        return selectedBModelIndex && *selectedBModelIndex == bmodelIndex;
    };

    if (renderTerrainHeightmap && m_showTerrainFill && terrainUsesClay && m_terrainVertexCount > 0)
    {
        submitProceduralBatch(
            m_terrainVertexBufferHandle,
            m_terrainVertexCount,
            {0.0f, 0.0f, 0.0f},
            m_clayPreviewSettings,
            false);
    }
    else if (renderTerrainHeightmap
        && m_showTerrainFill
        && bgfx::isValid(m_texturedTerrainVertexBufferHandle)
        && bgfx::isValid(m_terrainTextureAtlasHandle)
        && bgfx::isValid(m_texturedProgramHandle)
        && bgfx::isValid(m_textureSamplerHandle)
        && m_texturedTerrainVertexCount > 0)
    {
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, m_texturedTerrainVertexBufferHandle);
        bgfx::setTexture(0, m_textureSamplerHandle, m_terrainTextureAtlasHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_texturedProgramHandle);
    }
    else if (renderTerrainHeightmap && m_showTerrainFill && m_terrainVertexCount > 0)
    {
        submitProceduralBatch(
            m_terrainVertexBufferHandle,
            m_terrainVertexCount,
            {0.0f, 0.0f, 0.0f},
            m_clayPreviewSettings,
            false);
    }

    if (renderTerrainHeightmap && m_showTerrainFill && m_terrainErrorVertexCount > 0)
    {
        submitGridBatch(
            m_terrainErrorVertexBufferHandle,
            m_terrainErrorVertexCount,
            {0.0f, 0.0f, 0.0f},
            m_errorPreviewSettings,
            2.0f,
            true);
    }

    if (m_showBModels && bgfx::isValid(m_texturedProgramHandle) && bgfx::isValid(m_textureSamplerHandle))
    {
        for (const TexturedBatch &batch : m_bmodelTexturedBatches)
        {
            if (!bgfx::isValid(batch.vertexBufferHandle) || !bgfx::isValid(batch.textureHandle) || batch.vertexCount == 0)
            {
                continue;
            }

            if (shouldForcePreviewForBModel(batch.bmodelIndex))
            {
                continue;
            }

            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, batch.vertexBufferHandle);
            bgfx::setTexture(0, m_textureSamplerHandle, batch.textureHandle);
            uint64_t state =
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_DEPTH_TEST_LESS
                    | BGFX_STATE_MSAA;
            if (batch.hasTransparentPixels)
            {
                state |= BGFX_STATE_BLEND_ALPHA;
            }
            else
            {
                state |= BGFX_STATE_WRITE_Z;
            }
            bgfx::setState(state);
            bgfx::submit(EditorSceneViewId, m_texturedProgramHandle);
        }
    }

    if (bgfx::isValid(m_importedModelPreviewBatch.vertexBufferHandle) && m_importedModelPreviewBatch.vertexCount > 0)
    {
        if (m_previewMaterialMode == PreviewMaterialMode::Grid)
        {
            submitGridBatch(
                m_importedModelPreviewBatch.vertexBufferHandle,
                m_importedModelPreviewBatch.vertexCount,
                m_importedModelPreviewBatch.objectOrigin,
                m_gridPreviewSettings,
                1.0f,
                false);
        }
        else
        {
            submitProceduralBatch(
                m_importedModelPreviewBatch.vertexBufferHandle,
                m_importedModelPreviewBatch.vertexCount,
                m_importedModelPreviewBatch.objectOrigin,
                m_clayPreviewSettings,
                false);
        }
    }

    submitModelInstanceBatches();

    if (m_showBModels)
    {
        for (const ProceduralBatch &batch : m_bmodelAllFaceBatches)
        {
            if (!shouldForcePreviewForBModel(batch.bmodelIndex))
            {
                continue;
            }

            if (m_previewMaterialMode == PreviewMaterialMode::Clay)
            {
                submitProceduralBatch(
                    batch.vertexBufferHandle,
                    batch.vertexCount,
                    batch.objectOrigin,
                    m_clayPreviewSettings,
                    false);
            }
            else
            {
                submitGridBatch(
                    batch.vertexBufferHandle,
                    batch.vertexCount,
                    batch.objectOrigin,
                    m_gridPreviewSettings,
                    1.0f,
                    false);
            }
        }

        for (const ProceduralBatch &batch : m_bmodelUnassignedBatches)
        {
            if (shouldForcePreviewForBModel(batch.bmodelIndex))
            {
                continue;
            }

            submitGridBatch(
                batch.vertexBufferHandle,
                batch.vertexCount,
                batch.objectOrigin,
                m_gridPreviewSettings,
                1.0f,
                false);
        }

        for (const ProceduralBatch &batch : m_bmodelMissingAssetBatches)
        {
            submitGridBatch(
                batch.vertexBufferHandle,
                batch.vertexCount,
                batch.objectOrigin,
                m_errorPreviewSettings,
                2.0f,
                true);
        }
    }

    if (m_showBModelWireframe && bgfx::isValid(m_bmodelWireVertexBufferHandle) && m_bmodelWireVertexCount > 0)
    {
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, m_bmodelWireVertexBufferHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }
}

void EditorOutdoorViewport::submitEntityBillboardGeometry(
    const EditorSession &session,
    const EditorDocument &document) const
{
    const bool hasBillboardContent =
        (m_showEntities && m_showEntityBillboards)
        || (m_showActors && m_showActorBillboards)
        || (m_showSpawns && m_showSpawnActorBillboards)
        || m_pendingEntityPlacementPreview != std::nullopt
        || m_pendingActorPlacementPreview != std::nullopt
        || m_pendingSpawnPlacementPreview != std::nullopt
        || m_showSpriteObjects
        || m_pendingSpriteObjectPlacementPreview != std::nullopt;

    if (!hasBillboardContent
        || !bgfx::isValid(m_texturedProgramHandle)
        || !bgfx::isValid(m_textureSamplerHandle))
    {
        return;
    }

    if (document.kind() != EditorDocument::Kind::Indoor
        && document.kind() != EditorDocument::Kind::Outdoor)
    {
        return;
    }

    if (document.kind() == EditorDocument::Kind::Indoor
        && (!m_showEntities || !m_showEntityBillboards)
        && (!m_showActors || !m_showActorBillboards)
        && (!m_showSpawns || !m_showSpawnActorBillboards)
        && !m_showSpriteObjects
        && m_pendingEntityPlacementPreview == std::nullopt
        && m_pendingActorPlacementPreview == std::nullopt
        && m_pendingSpawnPlacementPreview == std::nullopt
        && m_pendingSpriteObjectPlacementPreview == std::nullopt)
    {
        return;
    }

    const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();

    if (pAssetFileSystem == nullptr)
    {
        return;
    }

    const uint32_t animationTicks = currentAnimationTicks();
    const bx::Vec3 forward = vecNormalize({
        std::sin(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::cos(m_cameraYawRadians) * std::cos(m_cameraPitchRadians),
        std::sin(m_cameraPitchRadians)
    });
    const bx::Vec3 worldUp = {0.0f, 0.0f, 1.0f};
    const bx::Vec3 cameraRight = vecNormalize(vecCross(forward, worldUp));
    const bx::Vec3 cameraUp = vecNormalize(vecCross(cameraRight, forward));

    struct BillboardDrawItem
    {
        const SpriteBillboardTexture *pTexture = nullptr;
        bx::Vec3 center = {0.0f, 0.0f, 0.0f};
        float worldWidth = 0.0f;
        float worldHeight = 0.0f;
        float cameraDepth = 0.0f;
        bool mirrored = false;
    };

    BitmapLoadCache bitmapLoadCache = {};
    const Game::SpriteFrameTable *pEntityBillboardSpriteFrameTable =
        ((m_showEntities && m_showEntityBillboards)
            || m_pendingEntityPlacementPreview != std::nullopt
            || m_showSpriteObjects
            || m_pendingSpriteObjectPlacementPreview != std::nullopt)
            ? session.entityBillboardSpriteFrameTable()
            : nullptr;
    const std::vector<EditorEntityBillboardPreview> *pEntityBillboardPreviews =
        (m_showEntities && m_showEntityBillboards) ? &session.entityBillboardPreviews() : nullptr;
    const Game::SpriteFrameTable *pActorBillboardSpriteFrameTable =
        ((m_showActors && m_showActorBillboards) || (m_showSpawns && m_showSpawnActorBillboards))
            ? session.actorBillboardSpriteFrameTable()
            : nullptr;
    const std::vector<EditorActorBillboardPreview> *pActorBillboardPreviews =
        pActorBillboardSpriteFrameTable != nullptr ? &session.actorBillboardPreviews() : nullptr;
    std::vector<BillboardDrawItem> drawItems;
    drawItems.reserve(
        (pEntityBillboardPreviews != nullptr ? pEntityBillboardPreviews->size() : 0u)
        + (pActorBillboardPreviews != nullptr ? pActorBillboardPreviews->size() : 0u)
        + (m_pendingEntityPlacementPreview ? 1u : 0u)
        + (m_pendingActorPlacementPreview ? 1u : 0u)
        + (m_pendingSpawnPlacementPreview ? 1u : 0u)
        + (m_pendingSpriteObjectPlacementPreview ? 1u : 0u));
    const auto ensureTexture =
        [this, pAssetFileSystem, &bitmapLoadCache](
            const std::string &textureName,
            int16_t paletteId) -> const SpriteBillboardTexture *
    {
        const SpriteBillboardTextureKey textureKey = {textureName, paletteId};
        const auto existingTextureIt = m_entityBillboardTextures.find(textureKey);

        if (existingTextureIt != m_entityBillboardTextures.end())
        {
            if (bgfx::isValid(existingTextureIt->second.textureHandle))
            {
                return &existingTextureIt->second;
            }

            return nullptr;
        }

        int textureWidth = 0;
        int textureHeight = 0;
        const std::optional<std::vector<uint8_t>> texturePixels =
            loadSpriteBitmapPixelsBgra(
                *pAssetFileSystem,
                textureName,
                paletteId,
                textureWidth,
                textureHeight,
                bitmapLoadCache);

        SpriteBillboardTexture texture = {};

        if (texturePixels && textureWidth > 0 && textureHeight > 0)
        {
            texture.textureHandle = bgfx::createTexture2D(
                static_cast<uint16_t>(textureWidth),
                static_cast<uint16_t>(textureHeight),
                false,
                1,
                bgfx::TextureFormat::BGRA8,
                BGFX_SAMPLER_U_CLAMP
                    | BGFX_SAMPLER_V_CLAMP
                    | BGFX_SAMPLER_MIN_POINT
                    | BGFX_SAMPLER_MAG_POINT
                    | BGFX_SAMPLER_MIP_POINT,
                bgfx::copy(texturePixels->data(), static_cast<uint32_t>(texturePixels->size())));
            texture.width = textureWidth;
            texture.height = textureHeight;
        }

        const auto inserted =
            m_entityBillboardTextures.emplace(textureKey, texture);
        return bgfx::isValid(inserted.first->second.textureHandle) ? &inserted.first->second : nullptr;
    };

    const auto appendSpriteObjectBillboard =
        [this, &session, &forward, &ensureTexture, &drawItems, pEntityBillboardSpriteFrameTable](
            uint16_t objectDescriptionId,
            uint16_t spriteId,
            int x,
            int y,
            int z,
            uint32_t animationTimeTicks)
    {
        const Game::ObjectEntry *pObjectEntry = session.objectTable().get(objectDescriptionId);

        if (pObjectEntry == nullptr || (pObjectEntry->flags & 0x0001) != 0 || spriteId == 0)
        {
            return;
        }

        if (pEntityBillboardSpriteFrameTable == nullptr)
        {
            return;
        }

        const float deltaX = static_cast<float>(x) - m_cameraPosition.x;
        const float deltaY = static_cast<float>(y) - m_cameraPosition.y;
        const float deltaZ = static_cast<float>(z) - m_cameraPosition.z;
        const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

        if (cameraDepth <= 0.1f)
        {
            return;
        }

        const Game::SpriteFrameEntry *pFrame =
            pEntityBillboardSpriteFrameTable->getFrame(spriteId, animationTimeTicks);

        if (pFrame == nullptr)
        {
            return;
        }

        const Game::ResolvedSpriteTexture resolvedTexture = Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
        const SpriteBillboardTexture *pTexture = ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

        if (pTexture == nullptr)
        {
            return;
        }

        const float spriteScale = std::max(pFrame->scale, 0.01f);
        BillboardDrawItem drawItem = {};
        drawItem.pTexture = pTexture;
        drawItem.center = {
            static_cast<float>(x),
            static_cast<float>(y),
            static_cast<float>(z) + static_cast<float>(pTexture->height) * spriteScale * 0.5f
        };
        drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
        drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
        drawItem.cameraDepth = cameraDepth;
        drawItem.mirrored = resolvedTexture.mirrored;
        drawItems.push_back(drawItem);
    };

    const auto appendActorPlacementBillboard =
        [this, &session, &forward, &ensureTexture, &drawItems](
            const Game::MapDeltaActor &actor,
            int x,
            int y,
            int z)
    {
        const std::optional<std::pair<std::string, int16_t>> texture =
            session.previewMonsterTexture(actor.monsterInfoId, actor.monsterId);

        if (!texture)
        {
            return;
        }

        const float deltaX = static_cast<float>(x) - m_cameraPosition.x;
        const float deltaY = static_cast<float>(y) - m_cameraPosition.y;
        const float deltaZ = static_cast<float>(z) - m_cameraPosition.z;
        const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

        if (cameraDepth <= 0.1f)
        {
            return;
        }

        const SpriteBillboardTexture *pTexture = ensureTexture(texture->first, texture->second);

        if (pTexture == nullptr || pTexture->height <= 0)
        {
            return;
        }

        const float worldHeight =
            actor.height > 0 ? static_cast<float>(actor.height) : static_cast<float>(pTexture->height);
        const float aspectRatio =
            static_cast<float>(pTexture->width) / static_cast<float>(pTexture->height);
        const float worldWidth = worldHeight * aspectRatio;
        BillboardDrawItem drawItem = {};
        drawItem.pTexture = pTexture;
        drawItem.center = {
            static_cast<float>(x),
            static_cast<float>(y),
            static_cast<float>(z) + worldHeight * 0.5f
        };
        drawItem.worldWidth = worldWidth;
        drawItem.worldHeight = worldHeight;
        drawItem.cameraDepth = cameraDepth;
        drawItems.push_back(drawItem);
    };

    const auto appendSpawnPlacementBillboard =
        [this, &session, &forward, &ensureTexture, &drawItems](
            const Game::OutdoorSpawn &spawn,
            int x,
            int y,
            int z)
    {
        std::optional<std::pair<std::string, int16_t>> texture;

        if (spawn.typeId == 3)
        {
            texture = session.previewSpawnMonsterTexture(spawn.typeId, spawn.index);
        }
        else if (spawn.typeId == 2)
        {
            texture = session.previewObjectTexture(spawn.index);
        }

        if (!texture)
        {
            return;
        }

        const float deltaX = static_cast<float>(x) - m_cameraPosition.x;
        const float deltaY = static_cast<float>(y) - m_cameraPosition.y;
        const float deltaZ = static_cast<float>(z) - m_cameraPosition.z;
        const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

        if (cameraDepth <= 0.1f)
        {
            return;
        }

        const SpriteBillboardTexture *pTexture = ensureTexture(texture->first, texture->second);

        if (pTexture == nullptr)
        {
            return;
        }

        const float scale = spawn.typeId == 3 ? 1.0f : 0.75f;
        BillboardDrawItem drawItem = {};
        drawItem.pTexture = pTexture;
        drawItem.center = {
            static_cast<float>(x),
            static_cast<float>(y),
            static_cast<float>(z) + static_cast<float>(pTexture->height) * scale * 0.5f
        };
        drawItem.worldWidth = static_cast<float>(pTexture->width) * scale;
        drawItem.worldHeight = static_cast<float>(pTexture->height) * scale;
        drawItem.cameraDepth = cameraDepth;
        drawItems.push_back(drawItem);
    };

    if (document.kind() == EditorDocument::Kind::Indoor)
    {
        const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
        const Game::IndoorSceneData &sceneData = document.indoorSceneData();
        const std::vector<Game::IndoorVertex> &indoorVertices = indoorRenderVertices(document);

        if (m_showEntities && m_showEntityBillboards)
        {
            if (pEntityBillboardSpriteFrameTable != nullptr && pEntityBillboardPreviews != nullptr)
            {
                for (const EditorEntityBillboardPreview &preview : *pEntityBillboardPreviews)
                {
                    if (preview.entityIndex >= indoorGeometry.entities.size())
                    {
                        continue;
                    }

                    const Game::IndoorEntity &entity = indoorGeometry.entities[preview.entityIndex];

                    if ((entity.aiAttributes & LevelDecorationInvisible) != 0
                        || (preview.flags & DecorationDescDontDraw) != 0
                        || preview.spriteId == 0)
                    {
                        continue;
                    }

                    const bx::Vec3 center = {
                        static_cast<float>(preview.x),
                        static_cast<float>(preview.y),
                        static_cast<float>(preview.z)};

                    if (!indoorMarkerVisibleForIsolation(indoorGeometry, m_isolatedIndoorRoomId, center))
                    {
                        continue;
                    }

                    const float deltaX = center.x - m_cameraPosition.x;
                    const float deltaY = center.y - m_cameraPosition.y;
                    const float deltaZ = center.z - m_cameraPosition.z;
                    const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

                    if (cameraDepth <= 0.1f)
                    {
                        continue;
                    }

                    const uint32_t animationOffsetTicks =
                        animationTicks + static_cast<uint32_t>(std::abs(preview.x + preview.y));
                    const Game::SpriteFrameEntry *pFrame =
                        pEntityBillboardSpriteFrameTable->getFrame(preview.spriteId, animationOffsetTicks);

                    if (pFrame == nullptr)
                    {
                        continue;
                    }

                    const float facingRadians = static_cast<float>(preview.facing) * bx::kPi / 180.0f;
                    const float angleToCamera = std::atan2(
                        static_cast<float>(preview.y) - m_cameraPosition.y,
                        static_cast<float>(preview.x) - m_cameraPosition.x);
                    const float octantAngle = facingRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
                    const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
                    const Game::ResolvedSpriteTexture resolvedTexture =
                        Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
                    const SpriteBillboardTexture *pTexture =
                        ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

                    if (pTexture == nullptr)
                    {
                        continue;
                    }

                    const float spriteScale = std::max(pFrame->scale, 0.01f);
                    BillboardDrawItem drawItem = {};
                    drawItem.pTexture = pTexture;
                    drawItem.center = {
                        center.x,
                        center.y,
                        center.z + static_cast<float>(pTexture->height) * spriteScale * 0.5f
                    };
                    drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                    drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                    drawItem.cameraDepth = cameraDepth;
                    drawItem.mirrored = resolvedTexture.mirrored;
                    drawItems.push_back(drawItem);
                }
            }
        }

        if (pActorBillboardSpriteFrameTable != nullptr && pActorBillboardPreviews != nullptr)
        {
            for (const EditorActorBillboardPreview &preview : *pActorBillboardPreviews)
            {
                const bool isActor = preview.source == EditorActorBillboardPreview::Source::Actor;

                if ((isActor && (!m_showActors || !m_showActorBillboards))
                    || (!isActor && (!m_showSpawns || !m_showSpawnActorBillboards)))
                {
                    continue;
                }

                const bx::Vec3 center = {
                    static_cast<float>(preview.x),
                    static_cast<float>(preview.y),
                    static_cast<float>(preview.z)};

                if (!indoorMarkerVisibleForIsolation(indoorGeometry, m_isolatedIndoorRoomId, center))
                {
                    continue;
                }

                const float deltaX = center.x - m_cameraPosition.x;
                const float deltaY = center.y - m_cameraPosition.y;
                const float deltaZ = center.z - m_cameraPosition.z;
                const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

                if (cameraDepth <= 0.1f)
                {
                    continue;
                }

                const Game::SpriteFrameEntry *pFrame =
                    pActorBillboardSpriteFrameTable->getFrame(preview.spriteFrameIndex, 0);

                if (pFrame == nullptr)
                {
                    continue;
                }

                const float angleToCamera = std::atan2(
                    static_cast<float>(preview.y) - m_cameraPosition.y,
                    static_cast<float>(preview.x) - m_cameraPosition.x);
                const float octantAngle = preview.yawRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
                const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
                const Game::ResolvedSpriteTexture resolvedTexture =
                    Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
                const SpriteBillboardTexture *pTexture =
                    ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

                if (pTexture == nullptr)
                {
                    continue;
                }

                const float spriteScale = std::max(pFrame->scale, 0.01f);
                BillboardDrawItem drawItem = {};
                drawItem.pTexture = pTexture;
                drawItem.center = {
                    center.x,
                    center.y,
                    center.z + static_cast<float>(pTexture->height) * spriteScale * 0.5f
                };
                drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                drawItem.cameraDepth = cameraDepth;
                drawItem.mirrored = resolvedTexture.mirrored;
                drawItems.push_back(drawItem);
            }
        }

        if (m_showSpriteObjects)
        {
            for (const Game::MapDeltaSpriteObject &spriteObject : sceneData.initialState.spriteObjects)
            {
                if (!indoorMarkerVisibleForIsolation(
                        indoorGeometry,
                        m_isolatedIndoorRoomId,
                        {
                            static_cast<float>(spriteObject.x),
                            static_cast<float>(spriteObject.y),
                            static_cast<float>(spriteObject.z)
                        },
                        spriteObject.sectorId))
                {
                    continue;
            }

                const uint16_t objectDescriptionId =
                    session.resolvedSpriteObjectObjectDescriptionId(spriteObject);
                const Game::ObjectEntry *pObjectEntry = session.objectTable().get(objectDescriptionId);
                const uint16_t spriteId = pObjectEntry != nullptr ? pObjectEntry->spriteId : spriteObject.spriteId;
                appendSpriteObjectBillboard(
                    objectDescriptionId,
                    spriteId,
                    spriteObject.x,
                    spriteObject.y,
                    spriteObject.z,
                    static_cast<uint32_t>(spriteObject.timeSinceCreated) * 8u);
            }
        }

        if (m_pendingEntityPlacementPreview)
        {
            const Game::DecorationEntry *pDecoration =
                session.decorationTable().get(session.pendingEntityDecorationListId());

            if (pDecoration != nullptr
                && pEntityBillboardSpriteFrameTable != nullptr
                && (pDecoration->flags & DecorationDescDontDraw) == 0
                && pDecoration->spriteId != 0)
            {
                const uint32_t animationOffsetTicks =
                    animationTicks
                    + static_cast<uint32_t>(
                        std::abs(m_pendingEntityPlacementPreview->x + m_pendingEntityPlacementPreview->y));
                const Game::SpriteFrameEntry *pFrame =
                    pEntityBillboardSpriteFrameTable->getFrame(pDecoration->spriteId, animationOffsetTicks);

                if (pFrame != nullptr)
                {
                    const Game::ResolvedSpriteTexture resolvedTexture =
                        Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
                    const SpriteBillboardTexture *pTexture =
                        ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

                    if (pTexture != nullptr)
                    {
                        const float deltaX =
                            static_cast<float>(m_pendingEntityPlacementPreview->x) - m_cameraPosition.x;
                        const float deltaY =
                            static_cast<float>(m_pendingEntityPlacementPreview->y) - m_cameraPosition.y;
                        const float deltaZ =
                            static_cast<float>(m_pendingEntityPlacementPreview->z) - m_cameraPosition.z;
                        const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

                        if (cameraDepth > 0.1f)
                        {
                            const float spriteScale = std::max(pFrame->scale, 0.01f);
                            BillboardDrawItem drawItem = {};
                            drawItem.pTexture = pTexture;
                            drawItem.center = {
                                static_cast<float>(m_pendingEntityPlacementPreview->x),
                                static_cast<float>(m_pendingEntityPlacementPreview->y),
                                static_cast<float>(m_pendingEntityPlacementPreview->z)
                                    + static_cast<float>(pTexture->height) * spriteScale * 0.5f
                            };
                            drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                            drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                            drawItem.cameraDepth = cameraDepth;
                            drawItem.mirrored = resolvedTexture.mirrored;
                            drawItems.push_back(drawItem);
                        }
                    }
                }
            }
        }

        if (m_pendingActorPlacementPreview)
        {
            appendActorPlacementBillboard(
                session.pendingActor(),
                m_pendingActorPlacementPreview->x,
                m_pendingActorPlacementPreview->y,
                m_pendingActorPlacementPreview->z);
        }

        if (m_pendingSpawnPlacementPreview)
        {
            appendSpawnPlacementBillboard(
                session.pendingSpawn(),
                m_pendingSpawnPlacementPreview->x,
                m_pendingSpawnPlacementPreview->y,
                m_pendingSpawnPlacementPreview->z);
        }

        if (m_pendingSpriteObjectPlacementPreview)
        {
            const Game::ObjectEntry *pObjectEntry =
                session.objectTable().get(session.pendingSpriteObjectDescriptionId());
            const uint16_t spriteId = pObjectEntry != nullptr ? pObjectEntry->spriteId : 0;
            appendSpriteObjectBillboard(
                session.pendingSpriteObjectDescriptionId(),
                spriteId,
                m_pendingSpriteObjectPlacementPreview->x,
                m_pendingSpriteObjectPlacementPreview->y,
                m_pendingSpriteObjectPlacementPreview->z,
                animationTicks);
        }
    }
    else
    {
        const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

        if (m_showEntities && m_showEntityBillboards)
        {
        if (pEntityBillboardSpriteFrameTable != nullptr && pEntityBillboardPreviews != nullptr)
        {
            for (const EditorEntityBillboardPreview &preview : *pEntityBillboardPreviews)
            {
                if (preview.entityIndex >= sceneData.entities.size())
                {
                    continue;
                }

                const Game::OutdoorEntity &entity = sceneData.entities[preview.entityIndex].entity;

                if ((entity.aiAttributes & LevelDecorationInvisible) != 0
                    || (preview.flags & DecorationDescDontDraw) != 0
                    || preview.spriteId == 0)
                {
                    continue;
                }

                const float deltaX = static_cast<float>(preview.x) - m_cameraPosition.x;
                const float deltaY = static_cast<float>(preview.y) - m_cameraPosition.y;
                const float deltaZ = static_cast<float>(preview.z) - m_cameraPosition.z;
                const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

                if (cameraDepth <= 0.1f)
                {
                    continue;
                }

                const uint32_t animationOffsetTicks =
                    animationTicks + static_cast<uint32_t>(std::abs(preview.x + preview.y));
                const Game::SpriteFrameEntry *pFrame =
                    pEntityBillboardSpriteFrameTable->getFrame(preview.spriteId, animationOffsetTicks);

                if (pFrame == nullptr)
                {
                    continue;
                }

                const float facingRadians = static_cast<float>(preview.facing) * bx::kPi / 180.0f;
                const float angleToCamera = std::atan2(
                    static_cast<float>(preview.y) - m_cameraPosition.y,
                    static_cast<float>(preview.x) - m_cameraPosition.x);
                const float octantAngle = facingRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
                const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
                const Game::ResolvedSpriteTexture resolvedTexture =
                    Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
                const SpriteBillboardTexture *pTexture =
                    ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

                if (pTexture == nullptr)
                {
                    continue;
                }

                const float spriteScale = std::max(pFrame->scale, 0.01f);
                BillboardDrawItem drawItem = {};
                drawItem.pTexture = pTexture;
                drawItem.center = {
                    static_cast<float>(preview.x),
                    static_cast<float>(preview.y),
                    static_cast<float>(preview.z) + static_cast<float>(pTexture->height) * spriteScale * 0.5f
                };
                drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                drawItem.cameraDepth = cameraDepth;
                drawItem.mirrored = resolvedTexture.mirrored;
                drawItems.push_back(drawItem);
            }
        }
        }

    if (m_pendingEntityPlacementPreview)
    {
        const Game::DecorationEntry *pDecoration =
            session.decorationTable().get(session.pendingEntityDecorationListId());

        if (pDecoration != nullptr
            && pEntityBillboardSpriteFrameTable != nullptr
            && (pDecoration->flags & DecorationDescDontDraw) == 0
            && pDecoration->spriteId != 0)
        {
            const float deltaX = static_cast<float>(m_pendingEntityPlacementPreview->x) - m_cameraPosition.x;
            const float deltaY = static_cast<float>(m_pendingEntityPlacementPreview->y) - m_cameraPosition.y;
            const float deltaZ = static_cast<float>(m_pendingEntityPlacementPreview->z) - m_cameraPosition.z;
            const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

            if (cameraDepth > 0.1f)
            {
                const uint32_t animationOffsetTicks =
                    animationTicks
                    + static_cast<uint32_t>(
                        std::abs(m_pendingEntityPlacementPreview->x + m_pendingEntityPlacementPreview->y));
                const Game::SpriteFrameEntry *pFrame =
                    pEntityBillboardSpriteFrameTable->getFrame(pDecoration->spriteId, animationOffsetTicks);

                if (pFrame != nullptr)
                {
                    const Game::ResolvedSpriteTexture resolvedTexture =
                        Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
                    const SpriteBillboardTexture *pTexture =
                        ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

                    if (pTexture != nullptr)
                    {
                        const float spriteScale = std::max(pFrame->scale, 0.01f);
                        BillboardDrawItem drawItem = {};
                        drawItem.pTexture = pTexture;
                        drawItem.center = {
                            static_cast<float>(m_pendingEntityPlacementPreview->x),
                            static_cast<float>(m_pendingEntityPlacementPreview->y),
                            static_cast<float>(m_pendingEntityPlacementPreview->z)
                                + static_cast<float>(pTexture->height) * spriteScale * 0.5f
                        };
                        drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
                        drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
                        drawItem.cameraDepth = cameraDepth;
                        drawItem.mirrored = resolvedTexture.mirrored;
                        drawItems.push_back(drawItem);
                    }
                }
            }
        }
    }

    if (pActorBillboardSpriteFrameTable != nullptr && pActorBillboardPreviews != nullptr)
    {
        for (const EditorActorBillboardPreview &preview : *pActorBillboardPreviews)
        {
            const bool isActor = preview.source == EditorActorBillboardPreview::Source::Actor;

            if ((isActor && (!m_showActors || !m_showActorBillboards))
                || (!isActor && (!m_showSpawns || !m_showSpawnActorBillboards)))
            {
                continue;
            }

            const float deltaX = static_cast<float>(preview.x) - m_cameraPosition.x;
            const float deltaY = static_cast<float>(preview.y) - m_cameraPosition.y;
            const float deltaZ = static_cast<float>(preview.z) - m_cameraPosition.z;
            const float cameraDepth = deltaX * forward.x + deltaY * forward.y + deltaZ * forward.z;

            if (cameraDepth <= 0.1f)
            {
                continue;
            }

            const Game::SpriteFrameEntry *pFrame =
                pActorBillboardSpriteFrameTable->getFrame(preview.spriteFrameIndex, 0);

            if (pFrame == nullptr)
            {
                continue;
            }

            const float angleToCamera = std::atan2(
                static_cast<float>(preview.y) - m_cameraPosition.y,
                static_cast<float>(preview.x) - m_cameraPosition.x);
            const float octantAngle = preview.yawRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
            const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
            const Game::ResolvedSpriteTexture resolvedTexture =
                Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
            const SpriteBillboardTexture *pTexture =
                ensureTexture(resolvedTexture.textureName, pFrame->paletteId);

            if (pTexture == nullptr)
            {
                continue;
            }

            const float spriteScale = std::max(pFrame->scale, 0.01f);
            BillboardDrawItem drawItem = {};
            drawItem.pTexture = pTexture;
            drawItem.center = {
                static_cast<float>(preview.x),
                static_cast<float>(preview.y),
                static_cast<float>(preview.z) + static_cast<float>(pTexture->height) * spriteScale * 0.5f
            };
            drawItem.worldWidth = static_cast<float>(pTexture->width) * spriteScale;
            drawItem.worldHeight = static_cast<float>(pTexture->height) * spriteScale;
            drawItem.cameraDepth = cameraDepth;
            drawItem.mirrored = resolvedTexture.mirrored;
            drawItems.push_back(drawItem);
        }
    }

    if (m_pendingActorPlacementPreview)
    {
        appendActorPlacementBillboard(
            session.pendingActor(),
            m_pendingActorPlacementPreview->x,
            m_pendingActorPlacementPreview->y,
            m_pendingActorPlacementPreview->z);
    }

    if (m_pendingSpawnPlacementPreview)
    {
        appendSpawnPlacementBillboard(
            session.pendingSpawn(),
            m_pendingSpawnPlacementPreview->x,
            m_pendingSpawnPlacementPreview->y,
            m_pendingSpawnPlacementPreview->z);
    }

    if (m_showSpriteObjects)
    {
        for (const Game::MapDeltaSpriteObject &spriteObject : sceneData.initialState.spriteObjects)
        {
            const uint16_t objectDescriptionId =
                session.resolvedSpriteObjectObjectDescriptionId(spriteObject);
            const Game::ObjectEntry *pObjectEntry = session.objectTable().get(objectDescriptionId);
            const uint16_t spriteId = pObjectEntry != nullptr ? pObjectEntry->spriteId : spriteObject.spriteId;
            appendSpriteObjectBillboard(
                objectDescriptionId,
                spriteId,
                spriteObject.x,
                spriteObject.y,
                spriteObject.z,
                static_cast<uint32_t>(spriteObject.timeSinceCreated) * 8u);
        }
    }

    if (m_pendingSpriteObjectPlacementPreview)
    {
        const Game::ObjectEntry *pObjectEntry =
            session.objectTable().get(session.pendingSpriteObjectDescriptionId());
        const uint16_t spriteId = pObjectEntry != nullptr ? pObjectEntry->spriteId : 0;
        appendSpriteObjectBillboard(
            session.pendingSpriteObjectDescriptionId(),
            spriteId,
            m_pendingSpriteObjectPlacementPreview->x,
            m_pendingSpriteObjectPlacementPreview->y,
            m_pendingSpriteObjectPlacementPreview->z,
            animationTicks);
    }
    }

    std::sort(drawItems.begin(), drawItems.end(), [](const BillboardDrawItem &left, const BillboardDrawItem &right)
    {
        return left.cameraDepth > right.cameraDepth;
    });

    for (const BillboardDrawItem &drawItem : drawItems)
    {
        if (drawItem.pTexture == nullptr || !bgfx::isValid(drawItem.pTexture->textureHandle))
        {
            continue;
        }

        if (bgfx::getAvailTransientVertexBuffer(6, TexturedPreviewVertex::ms_layout) < 6)
        {
            continue;
        }

        const float halfWidth = drawItem.worldWidth * 0.5f;
        const float halfHeight = drawItem.worldHeight * 0.5f;
        const bx::Vec3 right = vecScale(cameraRight, halfWidth);
        const bx::Vec3 up = vecScale(cameraUp, halfHeight);
        const bx::Vec3 bottomLeft = {
            drawItem.center.x - right.x - up.x,
            drawItem.center.y - right.y - up.y,
            drawItem.center.z - right.z - up.z
        };
        const bx::Vec3 topLeft = {
            drawItem.center.x - right.x + up.x,
            drawItem.center.y - right.y + up.y,
            drawItem.center.z - right.z + up.z
        };
        const bx::Vec3 topRight = {
            drawItem.center.x + right.x + up.x,
            drawItem.center.y + right.y + up.y,
            drawItem.center.z + right.z + up.z
        };
        const bx::Vec3 bottomRight = {
            drawItem.center.x + right.x - up.x,
            drawItem.center.y + right.y - up.y,
            drawItem.center.z + right.z - up.z
        };
        const float u0 = drawItem.mirrored ? 1.0f : 0.0f;
        const float u1 = drawItem.mirrored ? 0.0f : 1.0f;
        const std::array<TexturedPreviewVertex, 6> vertices = {{
            {bottomLeft.x, bottomLeft.y, bottomLeft.z, u0, 1.0f},
            {topLeft.x, topLeft.y, topLeft.z, u0, 0.0f},
            {topRight.x, topRight.y, topRight.z, u1, 0.0f},
            {bottomLeft.x, bottomLeft.y, bottomLeft.z, u0, 1.0f},
            {topRight.x, topRight.y, topRight.z, u1, 0.0f},
            {bottomRight.x, bottomRight.y, bottomRight.z, u1, 1.0f}
        }};

        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(&transientVertexBuffer, 6, TexturedPreviewVertex::ms_layout);
        std::memcpy(
            transientVertexBuffer.data,
            vertices.data(),
            static_cast<size_t>(vertices.size() * sizeof(TexturedPreviewVertex)));

        float transform[16] = {};
        bx::mtxIdentity(transform);
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, 6);
        bgfx::setTexture(0, m_textureSamplerHandle, drawItem.pTexture->textureHandle);
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_DEPTH_TEST_LEQUAL
                | BGFX_STATE_BLEND_ALPHA
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_texturedProgramHandle);
    }
}

void EditorOutdoorViewport::submitMarkerGeometry(
    const EditorSession &session,
    const EditorDocument &document,
    const EditorSelection &selection)
{
    std::vector<PreviewVertex> vertices;
    std::vector<PreviewVertex> fillVertices;
    std::vector<PreviewVertex> xrayVertices;
    std::vector<PreviewVertex> xrayFillVertices;
    size_t mm9DatSourceMarkerVertexCount = 0;
    size_t mm9DatAssetIssueMarkerVertexCount = 0;
    size_t mm9DatMechanismTargetMarkerVertexCount = 0;
    m_markerCandidates.clear();

    if (document.kind() == EditorDocument::Kind::Indoor)
    {
        const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
        const Game::IndoorSceneData &sceneData = document.indoorSceneData();
        const std::vector<Game::IndoorVertex> &indoorVertices = indoorRenderVertices(document);
        const uint32_t entityColor = makeAbgr(255, 208, 64);
        const uint32_t lightColor = makeAbgr(255, 192, 96);
        const uint32_t spawnColor = makeAbgr(96, 144, 255);
        const uint32_t actorSpawnColor = makeAbgr(255, 96, 220);
        const uint32_t actorColor = makeAbgr(255, 96, 96);
        const uint32_t spriteColor = makeAbgr(64, 216, 208);
        const uint32_t doorColor = makeAbgr(96, 255, 180);
        const uint32_t selectedColor = makeAbgr(255, 255, 255);
        const uint32_t faceSelectionColor = makeAbgr(255, 96, 255);
        const uint32_t faceSelectionFillColor = makeAbgrAlpha(255, 96, 255, 72);
        const uint32_t portalEdgeColor = makeAbgr(96, 232, 255);
        const uint32_t portalFillColor = makeAbgrAlpha(96, 232, 255, 38);
        const uint32_t isolatedRoomEdgeColor = makeAbgr(255, 214, 96);
        const uint32_t isolatedRoomFillColor = makeAbgrAlpha(255, 214, 96, 28);
        const uint32_t isolatedPortalEdgeColor = makeAbgr(128, 240, 255);
        const uint32_t isolatedPortalFillColor = makeAbgrAlpha(128, 240, 255, 54);
        Game::IndoorFaceGeometryCache &markerGeometryCache = indoorRenderFaceGeometryCache(document);
        char markerVisibilityKeyBuffer[256] = {};
        std::snprintf(
            markerVisibilityKeyBuffer,
            sizeof(markerVisibilityKeyBuffer),
            "%s|preview=%llu|camera=%.2f,%.2f,%.2f|floors=%d|ceilings=%d|room=%d",
            documentGeometryKey(document).c_str(),
            static_cast<unsigned long long>(m_indoorMechanismPreviewRevision),
            m_cameraPosition.x,
            m_cameraPosition.y,
            m_cameraPosition.z,
            m_showIndoorFloors ? 1 : 0,
            m_showIndoorCeilings ? 1 : 0,
            m_isolatedIndoorRoomId.has_value() ? static_cast<int>(*m_isolatedIndoorRoomId) : -1);
        const std::string markerVisibilityKey = markerVisibilityKeyBuffer;

        if (markerVisibilityKey != m_indoorMarkerVisibilityKey)
        {
            m_indoorMarkerVisibilityKey = markerVisibilityKey;
            m_indoorMarkerLineOfSightBlockedByKey.clear();
        }

        const auto appendIndoorFaceOverlayTo =
            [&](std::vector<PreviewVertex> &targetVertices,
                std::vector<PreviewVertex> &targetFillVertices,
                size_t faceId,
                uint32_t edgeColor,
                uint32_t fillColor,
                float edgeOffset,
                float fillOffset)
        {
            if (faceId >= indoorGeometry.faces.size())
            {
                return;
            }

            if (indoorFaceHiddenByCeilingView(
                    indoorGeometry,
                    indoorVertices,
                    faceId,
                    m_showIndoorFloors,
                    m_showIndoorCeilings,
                    m_isolatedIndoorRoomId,
                    &markerGeometryCache))
            {
                return;
            }

            const Game::IndoorFaceGeometryData *pGeometry =
                markerGeometryCache.geometryForFace(indoorGeometry, indoorVertices, faceId);

            if (pGeometry == nullptr || pGeometry->vertices.size() < 3)
            {
                return;
            }

            for (size_t vertexIndex = 0; vertexIndex < pGeometry->vertices.size(); ++vertexIndex)
            {
                const bx::Vec3 &start = pGeometry->vertices[vertexIndex];
                const bx::Vec3 &end = pGeometry->vertices[(vertexIndex + 1) % pGeometry->vertices.size()];
                targetVertices.push_back({start.x, start.y, start.z + edgeOffset, edgeColor});
                targetVertices.push_back({end.x, end.y, end.z + edgeOffset, edgeColor});
            }

            for (size_t vertexIndex = 1; vertexIndex + 1 < pGeometry->vertices.size(); ++vertexIndex)
            {
                targetFillVertices.push_back({
                    pGeometry->vertices[0].x,
                    pGeometry->vertices[0].y,
                    pGeometry->vertices[0].z + fillOffset,
                    fillColor});
                targetFillVertices.push_back({
                    pGeometry->vertices[vertexIndex].x,
                    pGeometry->vertices[vertexIndex].y,
                    pGeometry->vertices[vertexIndex].z + fillOffset,
                    fillColor});
                targetFillVertices.push_back({
                    pGeometry->vertices[vertexIndex + 1].x,
                    pGeometry->vertices[vertexIndex + 1].y,
                    pGeometry->vertices[vertexIndex + 1].z + fillOffset,
                    fillColor});
            }
        };
        const auto appendIndoorFaceOverlay =
            [&](size_t faceId, uint32_t edgeColor, uint32_t fillColor, float edgeOffset, float fillOffset)
        {
            appendIndoorFaceOverlayTo(
                xrayVertices,
                xrayFillVertices,
                faceId,
                edgeColor,
                fillColor,
                edgeOffset,
                fillOffset);
        };

        if (m_showIndoorPortals)
        {
            for (size_t faceId = 0; faceId < indoorGeometry.faces.size(); ++faceId)
            {
                const Game::IndoorFace &face = indoorGeometry.faces[faceId];

                if (!(face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal)))
                {
                    continue;
                }

                appendIndoorFaceOverlay(faceId, portalEdgeColor, portalFillColor, 1.5f, 0.5f);
            }
        }

        if (m_isolatedIndoorRoomId.has_value() && *m_isolatedIndoorRoomId < indoorGeometry.sectors.size())
        {
            for (uint16_t faceId : indoorSectorFaceIds(indoorGeometry, *m_isolatedIndoorRoomId))
            {
                const bool isPortalFace =
                    faceId < indoorGeometry.faces.size()
                    && (indoorGeometry.faces[faceId].isPortal
                        || Game::hasFaceAttribute(
                            indoorGeometry.faces[faceId].attributes,
                            Game::FaceAttribute::IsPortal));
                appendIndoorFaceOverlay(
                    faceId,
                    isPortalFace ? isolatedPortalEdgeColor : isolatedRoomEdgeColor,
                    isPortalFace ? isolatedPortalFillColor : isolatedRoomFillColor,
                    isPortalFace ? 2.5f : 2.0f,
                    isPortalFace ? 1.0f : 0.75f);
            }
        }

        if (m_showEventMarkers)
        {
            char eventOverlayKeyBuffer[384] = {};
            std::snprintf(
                eventOverlayKeyBuffer,
                sizeof(eventOverlayKeyBuffer),
                "%s|preview=%llu|floors=%d|ceilings=%d|room=%d|indoor_event_overlay",
                documentGeometryKey(document).c_str(),
                static_cast<unsigned long long>(m_indoorMechanismPreviewRevision),
                m_showIndoorFloors ? 1 : 0,
                m_showIndoorCeilings ? 1 : 0,
                m_isolatedIndoorRoomId.has_value() ? static_cast<int>(*m_isolatedIndoorRoomId) : -1);
            const std::string eventOverlayKey = eventOverlayKeyBuffer;

            if (eventOverlayKey != m_cachedIndoorEventOverlayKey)
            {
                const uint32_t explicitEventEdgeColor = makeAbgrAlpha(72, 220, 208, 192);
                const uint32_t explicitEventFillColor = makeAbgrAlpha(72, 220, 208, 82);
                const uint32_t hintOnlyEventEdgeColor = makeAbgrAlpha(112, 220, 208, 152);
                const uint32_t hintOnlyEventFillColor = makeAbgrAlpha(112, 220, 208, 58);

                m_cachedIndoorEventOverlayKey = eventOverlayKey;
                m_cachedIndoorEventOverlayVertices.clear();
                m_cachedIndoorEventOverlayFillVertices.clear();

                for (size_t faceId = 0; faceId < indoorGeometry.faces.size(); ++faceId)
                {
                    Game::IndoorFace effectiveFace = indoorGeometry.faces[faceId];

                    if (const Game::IndoorSceneFaceAttributeOverride *pOverride =
                            Game::findIndoorSceneFaceOverride(sceneData, faceId))
                    {
                        Game::applyIndoorSceneFaceOverride(*pOverride, effectiveFace);
                    }

                    if (effectiveFace.cogTriggered == 0)
                    {
                        continue;
                    }

                    const bool hintOnlyEvent = session.isHintOnlyEvent(effectiveFace.cogTriggered);
                    appendIndoorFaceOverlayTo(
                        m_cachedIndoorEventOverlayVertices,
                        m_cachedIndoorEventOverlayFillVertices,
                        faceId,
                        hintOnlyEvent ? hintOnlyEventEdgeColor : explicitEventEdgeColor,
                        hintOnlyEvent ? hintOnlyEventFillColor : explicitEventFillColor,
                        hintOnlyEvent ? 4.0f : 5.0f,
                        hintOnlyEvent ? 2.0f : 3.0f);
                }
            }

            xrayVertices.insert(
                xrayVertices.end(),
                m_cachedIndoorEventOverlayVertices.begin(),
                m_cachedIndoorEventOverlayVertices.end());
            xrayFillVertices.insert(
                xrayFillVertices.end(),
                m_cachedIndoorEventOverlayFillVertices.begin(),
                m_cachedIndoorEventOverlayFillVertices.end());
        }

        const auto markerLineOfSightBlocked = [&](const bx::Vec3 &center)
        {
            char centerKeyBuffer[96] = {};
            std::snprintf(
                centerKeyBuffer,
                sizeof(centerKeyBuffer),
                "%.2f,%.2f,%.2f",
                center.x,
                center.y,
                center.z);
            const std::string centerKey = centerKeyBuffer;
            const auto cachedIterator = m_indoorMarkerLineOfSightBlockedByKey.find(centerKey);

            if (cachedIterator != m_indoorMarkerLineOfSightBlockedByKey.end())
            {
                return cachedIterator->second;
            }

            const bool blocked = !indoorMarkerHasLineOfSight(
                indoorGeometry,
                indoorVertices,
                markerGeometryCache,
                m_cameraPosition,
                center,
                m_showIndoorFloors,
                m_showIndoorCeilings,
                m_isolatedIndoorRoomId);
            m_indoorMarkerLineOfSightBlockedByKey.emplace(centerKey, blocked);
            return blocked;
        };

        if (m_showEntities)
        {
            for (size_t entityIndex = 0; entityIndex < indoorGeometry.entities.size(); ++entityIndex)
            {
                const Game::IndoorEntity &entity = indoorGeometry.entities[entityIndex];
                const bx::Vec3 center = {
                    static_cast<float>(entity.x),
                    static_cast<float>(entity.y),
                    static_cast<float>(entity.z)};

                if (!indoorMarkerVisibleForIsolation(indoorGeometry, m_isolatedIndoorRoomId, center))
                {
                    continue;
                }

                const bool blockedByLineOfSight = markerLineOfSightBlocked(center);

                if (blockedByLineOfSight && !m_showIndoorGizmosEverywhere)
                {
                    continue;
                }

                const bool isSelected =
                    selection.kind == EditorSelectionKind::Entity && selection.index == entityIndex;

                MarkerCandidate candidate = {};
                candidate.selectionKind = EditorSelectionKind::Entity;
                candidate.selectionIndex = entityIndex;
                candidate.worldPosition = center;
                candidate.pickRadiusPixels = isSelected ? 32.0f : 26.0f;
                candidate.blockedByLineOfSight = blockedByLineOfSight;

                m_markerCandidates.push_back(candidate);
            }
        }

        for (size_t lightIndex = 0; lightIndex < indoorGeometry.lights.size(); ++lightIndex)
        {
            const Game::IndoorLight &light = indoorGeometry.lights[lightIndex];
            const bx::Vec3 center = {
                static_cast<float>(light.x),
                static_cast<float>(light.y),
                static_cast<float>(light.z)};

            if (!indoorMarkerVisibleForIsolation(indoorGeometry, m_isolatedIndoorRoomId, center))
            {
                continue;
            }

            const bool blockedByLineOfSight = markerLineOfSightBlocked(center);

            if (blockedByLineOfSight && !m_showIndoorGizmosEverywhere)
            {
                continue;
            }

            MarkerCandidate candidate = {};
            candidate.selectionKind = EditorSelectionKind::Light;
            candidate.selectionIndex = lightIndex;
            candidate.worldPosition = center;
            candidate.pickRadiusPixels = 28.0f;
            candidate.blockedByLineOfSight = blockedByLineOfSight;
            m_markerCandidates.push_back(candidate);
        }

        if (m_showSpawns)
        {
            for (size_t spawnIndex = 0; spawnIndex < indoorGeometry.spawns.size(); ++spawnIndex)
            {
                const Game::IndoorSpawn &spawn = indoorGeometry.spawns[spawnIndex];
                const int displayZ = snapIndoorActorZToFloor(document, spawn.x, spawn.y, spawn.z);
                const bx::Vec3 center = {
                    static_cast<float>(spawn.x),
                    static_cast<float>(spawn.y),
                    static_cast<float>(displayZ)};

                if (!indoorMarkerVisibleForIsolation(indoorGeometry, m_isolatedIndoorRoomId, center))
                {
                    continue;
                }

                const bool blockedByLineOfSight = markerLineOfSightBlocked(center);

                if (blockedByLineOfSight && !m_showIndoorGizmosEverywhere)
                {
                    continue;
                }

                const bool isSelected =
                    selection.kind == EditorSelectionKind::Spawn && selection.index == spawnIndex;

                MarkerCandidate candidate = {};
                candidate.selectionKind = EditorSelectionKind::Spawn;
                candidate.selectionIndex = spawnIndex;
                candidate.worldPosition = center;
                candidate.pickRadiusPixels = isSelected ? 34.0f : 28.0f;
                candidate.blockedByLineOfSight = blockedByLineOfSight;

                m_markerCandidates.push_back(candidate);
            }
        }

        if (m_pendingSpawnPlacementPreview)
        {
            const uint32_t pendingSpawnColor =
                session.pendingSpawn().typeId == 3 ? actorSpawnColor : spawnColor;
            const bx::Vec3 center = {
                static_cast<float>(m_pendingSpawnPlacementPreview->x),
                static_cast<float>(m_pendingSpawnPlacementPreview->y),
                static_cast<float>(m_pendingSpawnPlacementPreview->z)};
            appendCrossMarker(vertices, center, 64.0f, 128.0f, pendingSpawnColor);
        }

        if (m_showActors)
        {
            for (size_t actorIndex = 0; actorIndex < sceneData.initialState.actors.size(); ++actorIndex)
            {
                const Game::MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];
                const int displayZ = snapIndoorActorZToFloor(document, actor.x, actor.y, actor.z);
                const bx::Vec3 center = {
                    static_cast<float>(actor.x),
                    static_cast<float>(actor.y),
                    static_cast<float>(displayZ)};

                if (!indoorMarkerVisibleForIsolation(indoorGeometry, m_isolatedIndoorRoomId, center, actor.sectorId))
                {
                    continue;
                }

                const bool blockedByLineOfSight = markerLineOfSightBlocked(center);

                if (blockedByLineOfSight && !m_showIndoorGizmosEverywhere)
                {
                    continue;
                }

                MarkerCandidate candidate = {};
                candidate.selectionKind = EditorSelectionKind::Actor;
                candidate.selectionIndex = actorIndex;
                candidate.worldPosition = center;
                candidate.pickRadiusPixels = 28.0f;
                candidate.blockedByLineOfSight = blockedByLineOfSight;
                m_markerCandidates.push_back(candidate);
            }
        }

        if (m_showSpriteObjects)
        {
            for (size_t objectIndex = 0; objectIndex < sceneData.initialState.spriteObjects.size(); ++objectIndex)
            {
                const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[objectIndex];
                const bx::Vec3 center = {
                    static_cast<float>(spriteObject.x),
                    static_cast<float>(spriteObject.y),
                    static_cast<float>(spriteObject.z)};

                if (!indoorMarkerVisibleForIsolation(
                        indoorGeometry,
                        m_isolatedIndoorRoomId,
                        center,
                        spriteObject.sectorId))
                {
                    continue;
                }

                m_markerCandidates.push_back({EditorSelectionKind::SpriteObject, objectIndex, center, 18.0f});
            }
        }

        for (size_t doorIndex = 0; doorIndex < sceneData.initialState.doors.size(); ++doorIndex)
        {
            const std::optional<bx::Vec3> center = selectedWorldPosition(document, {EditorSelectionKind::Door, doorIndex});

            if (!indoorDoorVisibleForIsolation(
                    indoorGeometry,
                    sceneData.initialState.doors[doorIndex].door,
                    m_isolatedIndoorRoomId,
                    center))
            {
                continue;
            }

            if (center)
            {
                const bool blockedByLineOfSight = markerLineOfSightBlocked(*center);

                if (blockedByLineOfSight && !m_showIndoorGizmosEverywhere)
                {
                    continue;
                }

                MarkerCandidate candidate = {};
                candidate.selectionKind = EditorSelectionKind::Door;
                candidate.selectionIndex = doorIndex;
                candidate.worldPosition = *center;
                candidate.pickRadiusPixels = selection.kind == EditorSelectionKind::Door && selection.index == doorIndex
                    ? 44.0f
                    : 36.0f;
                candidate.blockedByLineOfSight = blockedByLineOfSight;
                m_markerCandidates.push_back(candidate);
            }
        }

        if (selection.kind == EditorSelectionKind::Door
            && selection.index < sceneData.initialState.doors.size())
        {
            const Game::MapDeltaDoor &door = sceneData.initialState.doors[selection.index].door;
            const std::optional<bx::Vec3> currentCenter = selectedWorldPosition(document, selection);
            uint16_t previewStateValue = 0;
            float previewTimeSinceTriggeredMs = 0.0f;
            float previewDistance = 0.0f;
            bool previewMoving = false;
            const bool hasPreviewState = tryGetIndoorMechanismPreview(
                document,
                selection.index,
                previewStateValue,
                previewTimeSinceTriggeredMs,
                previewDistance,
                previewMoving);
            std::optional<Game::RuntimeMechanismState> previewState;

            if (hasPreviewState)
            {
                previewState = Game::RuntimeMechanismState{};
                previewState->state = previewStateValue;
                previewState->timeSinceTriggeredMs = previewTimeSinceTriggeredMs;
                previewState->currentDistance = previewDistance;
                previewState->isMoving = previewMoving;
            }

            uint32_t linkedEdgeColor = makeAbgr(96, 255, 180);
            uint32_t linkedFillColor = makeAbgrAlpha(96, 255, 180, 52);
            const uint32_t faceLinkColor = makeAbgr(96, 255, 180);
            const uint32_t faceCenterColor = makeAbgr(144, 255, 208);

            if (m_indoorDoorFaceEditMode == IndoorDoorFaceEditMode::Add
                && m_indoorDoorFaceEditDoorIndex == selection.index)
            {
                linkedEdgeColor = makeAbgr(112, 255, 112);
                linkedFillColor = makeAbgrAlpha(112, 255, 112, 64);
            }
            else if (m_indoorDoorFaceEditMode == IndoorDoorFaceEditMode::Remove
                && m_indoorDoorFaceEditDoorIndex == selection.index)
            {
                linkedEdgeColor = makeAbgr(255, 112, 112);
                linkedFillColor = makeAbgrAlpha(255, 112, 112, 64);
            }

            for (uint16_t faceId : door.faceIds)
            {
                appendIndoorFaceOverlay(faceId, linkedEdgeColor, linkedFillColor, 5.0f, 3.0f);

                const std::optional<bx::Vec3> faceCenter = indoorFaceCenter(indoorGeometry, indoorVertices, faceId);

                if (!faceCenter)
                {
                    continue;
                }

                appendCrossMarker(xrayVertices, *faceCenter, 18.0f, 32.0f, faceCenterColor);

                if (currentCenter)
                {
                    appendLine(xrayVertices, *currentCenter, *faceCenter, faceLinkColor);
                }
            }
        }

        if (selection.kind == EditorSelectionKind::InteractiveFace
            && selection.index < indoorGeometry.faces.size())
        {
            const Game::IndoorFace &selectedFace = indoorGeometry.faces[selection.index];
            uint32_t effectiveAttributes = selectedFace.attributes;

            for (const Game::IndoorSceneFaceAttributeOverride &overrideEntry : sceneData.initialState.faceAttributeOverrides)
            {
                if (overrideEntry.faceIndex == selection.index && overrideEntry.legacyAttributes.has_value())
                {
                    effectiveAttributes = *overrideEntry.legacyAttributes;
                    break;
                }
            }

            const bool effectivePortal =
                selectedFace.isPortal || Game::hasFaceAttribute(effectiveAttributes, Game::FaceAttribute::IsPortal);
            const uint32_t roomEdgeColor = makeAbgr(255, 196, 96);
            const uint32_t roomFillColor = makeAbgrAlpha(255, 196, 96, 22);
            const uint32_t behindRoomEdgeColor = makeAbgr(96, 196, 255);
            const uint32_t behindRoomFillColor = makeAbgrAlpha(96, 196, 255, 18);

            for (uint16_t faceId : indoorSectorFaceIds(indoorGeometry, selectedFace.roomNumber))
            {
                appendIndoorFaceOverlay(faceId, roomEdgeColor, roomFillColor, 2.0f, 1.0f);
            }

            if (effectivePortal
                && selectedFace.roomBehindNumber != selectedFace.roomNumber
                && selectedFace.roomBehindNumber < indoorGeometry.sectors.size())
            {
                for (uint16_t faceId : indoorSectorFaceIds(indoorGeometry, selectedFace.roomBehindNumber))
                {
                    appendIndoorFaceOverlay(faceId, behindRoomEdgeColor, behindRoomFillColor, 1.0f, 0.0f);
                }
            }
        }

        if (selection.kind == EditorSelectionKind::InteractiveFace)
        {
            const uint32_t facePrimarySelectionColor = makeAbgr(255, 255, 255);
            const uint32_t facePrimarySelectionFillColor = makeAbgrAlpha(255, 240, 96, 84);

            for (size_t faceId : session.selectedInteractiveFaceIndices())
            {
                if (faceId >= indoorGeometry.faces.size())
                {
                    continue;
                }

                const uint32_t color =
                    selection.kind == EditorSelectionKind::InteractiveFace && selection.index == faceId
                        ? facePrimarySelectionColor
                        : faceSelectionColor;
                const uint32_t fillColor =
                    selection.kind == EditorSelectionKind::InteractiveFace && selection.index == faceId
                        ? facePrimarySelectionFillColor
                        : faceSelectionFillColor;
                appendIndoorFaceOverlay(faceId, color, fillColor, 4.0f, 2.0f);
            }
        }

        if (vertices.empty() && fillVertices.empty() && xrayVertices.empty() && xrayFillVertices.empty())
        {
            return;
        }

        if (!fillVertices.empty()
            && bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(fillVertices.size()), PreviewVertex::ms_layout)
                < fillVertices.size())
        {
            return;
        }

        if (!xrayFillVertices.empty()
            && bgfx::getAvailTransientVertexBuffer(
                    static_cast<uint32_t>(xrayFillVertices.size()),
                    PreviewVertex::ms_layout)
                < xrayFillVertices.size())
        {
            return;
        }

        if (!vertices.empty()
            && bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), PreviewVertex::ms_layout)
                < vertices.size())
        {
            return;
        }

        if (!xrayVertices.empty()
            && bgfx::getAvailTransientVertexBuffer(
                    static_cast<uint32_t>(xrayVertices.size()),
                    PreviewVertex::ms_layout)
                < xrayVertices.size())
        {
            return;
        }

        float transform[16] = {};
        bx::mtxIdentity(transform);

        if (!xrayFillVertices.empty())
        {
            bgfx::TransientVertexBuffer xrayFillVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &xrayFillVertexBuffer,
                static_cast<uint32_t>(xrayFillVertices.size()),
                PreviewVertex::ms_layout);
            std::memcpy(
                xrayFillVertexBuffer.data,
                xrayFillVertices.data(),
                xrayFillVertices.size() * sizeof(PreviewVertex));
            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, &xrayFillVertexBuffer, 0, static_cast<uint32_t>(xrayFillVertices.size()));
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_DEPTH_TEST_ALWAYS
                    | BGFX_STATE_BLEND_ALPHA
                    | BGFX_STATE_MSAA);
            bgfx::submit(EditorSceneViewId, m_programHandle);
        }

        if (!vertices.empty())
        {
            bgfx::TransientVertexBuffer transientVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &transientVertexBuffer,
                static_cast<uint32_t>(vertices.size()),
                PreviewVertex::ms_layout);
            std::memcpy(transientVertexBuffer.data, vertices.data(), vertices.size() * sizeof(PreviewVertex));
            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_WRITE_Z
                    | BGFX_STATE_DEPTH_TEST_LESS
                    | BGFX_STATE_PT_LINES
                    | BGFX_STATE_MSAA);
            bgfx::submit(EditorSceneViewId, m_programHandle);
        }

        if (!xrayVertices.empty())
        {
            bgfx::TransientVertexBuffer xrayVertexBuffer = {};
            bgfx::allocTransientVertexBuffer(
                &xrayVertexBuffer,
                static_cast<uint32_t>(xrayVertices.size()),
                PreviewVertex::ms_layout);
            std::memcpy(xrayVertexBuffer.data, xrayVertices.data(), xrayVertices.size() * sizeof(PreviewVertex));
            bgfx::setTransform(transform);
            bgfx::setVertexBuffer(0, &xrayVertexBuffer, 0, static_cast<uint32_t>(xrayVertices.size()));
            bgfx::setState(
                BGFX_STATE_WRITE_RGB
                    | BGFX_STATE_WRITE_A
                    | BGFX_STATE_DEPTH_TEST_ALWAYS
                    | BGFX_STATE_PT_LINES
                    | BGFX_STATE_MSAA);
            bgfx::submit(EditorSceneViewId, m_programHandle);
        }

        return;
    }

    const auto tryGetCachedBillboardSize =
        [this](const std::string &textureName, int16_t paletteId, float scale, float &worldWidth, float &worldHeight)
    {
        const SpriteBillboardTextureKey textureKey = {textureName, paletteId};
        const auto textureIt = m_entityBillboardTextures.find(textureKey);

        if (textureIt == m_entityBillboardTextures.end() || !bgfx::isValid(textureIt->second.textureHandle))
        {
            return false;
        }

        worldWidth = static_cast<float>(textureIt->second.width) * scale;
        worldHeight = static_cast<float>(textureIt->second.height) * scale;
        return worldWidth > 0.0f && worldHeight > 0.0f;
    };

    const bool mm9DatDocument = document.kind() == EditorDocument::Kind::Mm9Dat;
    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const std::vector<std::vector<uint16_t>> &effectiveFaceEvents = session.effectiveOutdoorFaceEvents();
    const std::vector<std::optional<uint16_t>> &defaultBModelEvents = session.derivedOutdoorBModelDefaultEvents();
    const uint32_t animationTicks = currentAnimationTicks();
    const Game::SpriteFrameTable *pEntitySpriteFrameTable =
        m_showEntities && m_showEntityBillboards ? session.entityBillboardSpriteFrameTable() : nullptr;
    const Game::SpriteFrameTable *pActorSpriteFrameTable =
        m_showActors && m_showActorBillboards ? session.actorBillboardSpriteFrameTable() : nullptr;
    std::vector<const EditorEntityBillboardPreview *> entityPreviewByIndex;
    std::vector<const EditorActorBillboardPreview *> actorPreviewByIndex;

    if (pEntitySpriteFrameTable != nullptr)
    {
        const std::vector<EditorEntityBillboardPreview> &entityBillboardPreviews = session.entityBillboardPreviews();
        entityPreviewByIndex.assign(sceneData.entities.size(), nullptr);

        for (const EditorEntityBillboardPreview &preview : entityBillboardPreviews)
        {
            if (preview.entityIndex < entityPreviewByIndex.size())
            {
                entityPreviewByIndex[preview.entityIndex] = &preview;
            }
        }
    }

    if (pActorSpriteFrameTable != nullptr)
    {
        const std::vector<EditorActorBillboardPreview> &actorBillboardPreviews = session.actorBillboardPreviews();
        actorPreviewByIndex.assign(sceneData.initialState.actors.size(), nullptr);

        for (const EditorActorBillboardPreview &preview : actorBillboardPreviews)
        {
            if (preview.source != EditorActorBillboardPreview::Source::Actor
                || preview.sourceIndex >= actorPreviewByIndex.size())
            {
                continue;
            }

            actorPreviewByIndex[preview.sourceIndex] = &preview;
        }
    }

    size_t outdoorMarkerCandidateReserve = 0;

    if (m_showEntities)
    {
        outdoorMarkerCandidateReserve += sceneData.entities.size();
    }

    if (m_showSpawns)
    {
        outdoorMarkerCandidateReserve += sceneData.spawns.size();

        if (mm9DatDocument)
        {
            outdoorMarkerCandidateReserve += document.mm9SpawnLayer().objects.size();
        }
    }

    if (m_showActors)
    {
        outdoorMarkerCandidateReserve += sceneData.initialState.actors.size();
    }

    if (m_showSpriteObjects)
    {
        outdoorMarkerCandidateReserve += sceneData.initialState.spriteObjects.size();
    }

    if (m_showEntities && mm9DatDocument)
    {
        outdoorMarkerCandidateReserve +=
            document.mm9LightLayer().lights.size() + document.mm9SoundLayer().objects.size();
    }

    if (m_showMm9ObjectBounds && mm9DatDocument)
    {
        outdoorMarkerCandidateReserve += document.mm9ObjectLayer().objects.size();
    }

    if (m_showMm9WorldModelBounds && mm9DatDocument && document.hasMm9DatLoadedSidecars())
    {
        outdoorMarkerCandidateReserve += document.mm9DatLoadedSidecars().datWorld.worldModels.size();
    }

    if (m_showMm9AssetIssueMarkers && mm9DatDocument)
    {
        outdoorMarkerCandidateReserve += document.mm9RawObjectAssetReferenceStatuses().size();
    }

    if (m_showEventMarkers && mm9DatDocument && document.hasMm9DatLoadedSidecars())
    {
        outdoorMarkerCandidateReserve += document.mm9DatLoadedSidecars().events.mechanisms.size();
    }

    if (outdoorMarkerCandidateReserve > 0)
    {
        m_markerCandidates.reserve(outdoorMarkerCandidateReserve);
    }

    const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();
    const std::string activeWorldId =
        pAssetFileSystem != nullptr ? Game::normalizeWorldId(pAssetFileSystem->getActiveWorldId()) : std::string();
    const bool mm9OutdoorDocument =
        Game::normalizeWorldId(outdoorGeometry.worldId) == "mm9"
        || activeWorldId == "mm9"
        || toLowerCopy(document.sceneVirtualPath()).find("worlds/mm9/") != std::string::npos;
    const std::string mm9MapId =
        mm9OutdoorDocument ? Game::normalizeMapFileStem(outdoorGeometry.fileName) : std::string();
    const Mm9ModelInstanceActorSourceLookup *pMm9ActorSourceLookup =
        pAssetFileSystem != nullptr
            ? cachedMm9ModelInstanceActorSourceLookup(*pAssetFileSystem)
            : nullptr;

    std::unordered_map<std::string, bool> mm9DatMarkerLineOfSightBlockedByKey;
    const auto applyMm9DatMarkerVisibility =
        [&](MarkerCandidate &candidate)
    {
        if (!mm9DatDocument || !document.hasMm9DatLoadedSidecars())
        {
            return;
        }

        char centerKeyBuffer[160] = {};
        std::snprintf(
            centerKeyBuffer,
            sizeof(centerKeyBuffer),
            "%.2f,%.2f,%.2f|%.2f,%.2f,%.2f",
            m_cameraPosition.x,
            m_cameraPosition.y,
            m_cameraPosition.z,
            candidate.worldPosition.x,
            candidate.worldPosition.y,
            candidate.worldPosition.z);
        const std::string centerKey = centerKeyBuffer;
        const auto cachedIterator = mm9DatMarkerLineOfSightBlockedByKey.find(centerKey);

        if (cachedIterator != mm9DatMarkerLineOfSightBlockedByKey.end())
        {
            candidate.blockedByLineOfSight = cachedIterator->second;
            return;
        }

        const bool blocked =
            !mm9DatMarkerHasLineOfSight(
                document.mm9DatLoadedSidecars().datWorld,
                m_cameraPosition,
                candidate.worldPosition);
        mm9DatMarkerLineOfSightBlockedByKey.emplace(centerKey, blocked);
        candidate.blockedByLineOfSight = blocked;
    };

    if (mm9DatDocument)
    {
        const EditorMm9RawObjectsSidecar &rawObjects = document.mm9DatLoadedSidecars().rawObjects;
        const auto appendRawObjectCandidate =
            [&](
                size_t sourceObjectIndex,
                const bx::Vec3 &center,
                float pickRadiusPixels,
                float billboardWorldWidth,
                float billboardWorldHeight)
        {
            const std::optional<size_t> rawObjectIndex =
                mm9RawObjectSidecarIndexForSourceObject(rawObjects, sourceObjectIndex);

            if (!rawObjectIndex)
            {
                return;
            }

            MarkerCandidate candidate = {};
            candidate.selectionKind = EditorSelectionKind::Mm9RawObject;
            candidate.selectionIndex = *rawObjectIndex;
            candidate.worldPosition = center;
            candidate.pickRadiusPixels = pickRadiusPixels;

            if (billboardWorldWidth > 0.0f && billboardWorldHeight > 0.0f)
            {
                candidate.hasBillboardBounds = true;
                candidate.billboardWorldWidth = billboardWorldWidth;
                candidate.billboardWorldHeight = billboardWorldHeight;
            }

            applyMm9DatMarkerVisibility(candidate);
            m_markerCandidates.push_back(candidate);
        };
        const auto chooseMm9SourceMarkerTarget =
            [&](size_t sourceObjectIndex) -> std::vector<PreviewVertex> &
        {
            const std::optional<size_t> rawObjectIndex =
                mm9RawObjectSidecarIndexForSourceObject(rawObjects, sourceObjectIndex);

            if (rawObjectIndex
                && selection.kind == EditorSelectionKind::Mm9RawObject
                && selection.index == *rawObjectIndex)
            {
                return xrayVertices;
            }

            return vertices;
        };

        if (m_showMm9WorldModelBounds)
        {
            const EditorMm9DatWorldSidecar &datWorld = document.mm9DatLoadedSidecars().datWorld;

            for (size_t worldModelIndex = 0; worldModelIndex < datWorld.worldModels.size(); ++worldModelIndex)
            {
                const EditorMm9DatWorldModelSummary &model = datWorld.worldModels[worldModelIndex];
                const bx::Vec3 minPoint = mm9LtToOpenYamm(model.boundsMinLt);
                const bx::Vec3 maxPoint = mm9LtToOpenYamm(model.boundsMaxLt);
                const bx::Vec3 center = {
                    (minPoint.x + maxPoint.x) * 0.5f,
                    (minPoint.y + maxPoint.y) * 0.5f,
                    (minPoint.z + maxPoint.z) * 0.5f
                };

                MarkerCandidate candidate = {};
                candidate.selectionKind = EditorSelectionKind::Mm9WorldModel;
                candidate.selectionIndex = worldModelIndex;
                candidate.worldPosition = center;
                candidate.pickRadiusPixels = model.roles.movable ? 30.0f : 22.0f;
                candidate.hasBillboardBounds = true;
                candidate.billboardWorldWidth =
                    std::max({std::abs(maxPoint.x - minPoint.x), std::abs(maxPoint.y - minPoint.y), 64.0f});
                candidate.billboardWorldHeight = std::max(std::abs(maxPoint.z - minPoint.z), 64.0f);
                applyMm9DatMarkerVisibility(candidate);
                m_markerCandidates.push_back(candidate);
            }
        }

        if (m_showMm9ObjectBounds)
        {
            for (const Game::Mm9Object &object : document.mm9ObjectLayer().objects)
            {
                if (!object.hasPosition || (!object.hasDims && !object.hasRadius && !object.triggerVolume))
                {
                    continue;
                }

                const bx::Vec3 center = mm9DatVec3LtToOpenYamm(object.positionLt);
                const float scale = object.hasScale ? std::max(std::abs(object.scale), 0.01f) : 1.0f;
                float billboardWorldWidth = 0.0f;
                float billboardWorldHeight = 0.0f;

                if (object.hasDims)
                {
                    const bx::Vec3 dims = mm9DatVec3LtToOpenYamm(object.dimsLt);
                    billboardWorldWidth =
                        std::max({std::abs(dims.x) * scale, std::abs(dims.y) * scale, 64.0f});
                    billboardWorldHeight = std::max(std::abs(dims.z) * scale, 64.0f);
                }
                else if (object.hasRadius)
                {
                    const float diameter =
                        std::max(std::abs(object.radius) * Game::Mm9DatToOpenYammScale * scale * 2.0f, 64.0f);
                    billboardWorldWidth = diameter;
                    billboardWorldHeight = diameter;
                }

                appendRawObjectCandidate(
                    object.sourceObjectIndex,
                    center,
                    object.triggerVolume ? 28.0f : 24.0f,
                    billboardWorldWidth,
                    billboardWorldHeight);
            }
        }

        if (m_showEntities)
        {
            const uint32_t lightColor = makeAbgr(255, 218, 96);
            const uint32_t lightCenterColor = makeAbgr(255, 255, 210);
            const uint32_t soundColor = makeAbgr(96, 196, 255);
            const uint32_t soundCenterColor = makeAbgr(204, 236, 255);

            for (const Game::Mm9LightObject &light : document.mm9LightLayer().lights)
            {
                if (!light.hasPosition)
                {
                    continue;
                }

                const bx::Vec3 center = mm9DatVec3LtToOpenYamm(light.positionLt);
                std::vector<PreviewVertex> &targetVertices = chooseMm9SourceMarkerTarget(light.sourceObjectIndex);
                const size_t beforeVertexCount = targetVertices.size();
                appendCrossMarker(targetVertices, center, 72.0f, 144.0f, lightCenterColor);

                if (light.hasLightRadius)
                {
                    const float radius =
                        std::max(std::abs(light.lightRadius) * Game::Mm9DatToOpenYammScale, 48.0f);
                    appendCollisionVolumeMarker(
                        targetVertices,
                        center,
                        radius,
                        radius * 2.0f,
                        lightColor,
                        lightCenterColor);
                }

                mm9DatSourceMarkerVertexCount += targetVertices.size() - beforeVertexCount;
                appendRawObjectCandidate(light.sourceObjectIndex, center, 24.0f, 0.0f, 0.0f);
            }

            for (const Game::Mm9SoundObject &sound : document.mm9SoundLayer().objects)
            {
                if (!sound.hasSoundPosition && !sound.hasPosition)
                {
                    continue;
                }

                const bx::Vec3 center =
                    mm9DatVec3LtToOpenYamm(sound.hasSoundPosition ? sound.soundPositionLt : sound.positionLt);
                std::vector<PreviewVertex> &targetVertices = chooseMm9SourceMarkerTarget(sound.sourceObjectIndex);
                const size_t beforeVertexCount = targetVertices.size();
                appendCrossMarker(targetVertices, center, 64.0f, 128.0f, soundCenterColor);

                if (sound.hasSoundRadius)
                {
                    const float radius =
                        std::max(std::abs(sound.soundRadius) * Game::Mm9DatToOpenYammScale, 48.0f);
                    appendCollisionVolumeMarker(
                        targetVertices,
                        center,
                        radius,
                        radius * 2.0f,
                        soundColor,
                        soundCenterColor);
                }

                mm9DatSourceMarkerVertexCount += targetVertices.size() - beforeVertexCount;
                appendRawObjectCandidate(sound.sourceObjectIndex, center, 22.0f, 0.0f, 0.0f);
            }
        }

        if (m_showSpawns)
        {
            const uint32_t spawnColor = makeAbgr(178, 128, 255);
            const uint32_t spawnVectorColor = makeAbgr(220, 192, 255);

            for (const Game::Mm9SpawnObject &spawn : document.mm9SpawnLayer().objects)
            {
                if (!spawn.hasPosition)
                {
                    continue;
                }

                const bx::Vec3 center = mm9DatVec3LtToOpenYamm(spawn.positionLt);
                std::vector<PreviewVertex> &targetVertices = chooseMm9SourceMarkerTarget(spawn.sourceObjectIndex);
                const size_t beforeVertexCount = targetVertices.size();
                appendCrossMarker(targetVertices, center, 72.0f, 144.0f, spawnColor);

                if (spawn.hasSpawnObjectVelocity)
                {
                    bx::Vec3 velocity = mm9DatVec3LtToOpenYamm(spawn.spawnObjectVelocityLt);
                    const float velocityLength = vecLength(velocity);

                    if (velocityLength > 0.001f)
                    {
                        const float maxLineLength = 384.0f;
                        const float lineScale = std::min(1.0f, maxLineLength / velocityLength);
                        const bx::Vec3 end = vecAdd(center, vecScale(velocity, lineScale));
                        appendLine(targetVertices, center, end, spawnVectorColor);
                    }
                }

                mm9DatSourceMarkerVertexCount += targetVertices.size() - beforeVertexCount;
                appendRawObjectCandidate(spawn.sourceObjectIndex, center, 26.0f, 0.0f, 0.0f);
            }
        }

        if (m_showMm9AssetIssueMarkers)
        {
            std::unordered_map<size_t, bool> assetIssueRequiredBySourceObject;

            for (const EditorMm9RawObjectAssetReferenceStatus &status :
                document.mm9RawObjectAssetReferenceStatuses())
            {
                if (status.resolved && !status.ambiguous)
                {
                    continue;
                }

                bool &hasRequiredIssue = assetIssueRequiredBySourceObject[status.sourceObjectIndex];
                hasRequiredIssue = hasRequiredIssue || status.required;
            }

            for (const std::pair<const size_t, bool> &issue : assetIssueRequiredBySourceObject)
            {
                const std::optional<bx::Vec3> position =
                    mm9SourceObjectMarkerPosition(document, issue.first);

                if (!position)
                {
                    continue;
                }

                std::vector<PreviewVertex> &targetVertices = chooseMm9SourceMarkerTarget(issue.first);
                const size_t beforeVertexCount = targetVertices.size();
                const uint32_t color = issue.second ? makeAbgr(255, 72, 72) : makeAbgr(255, 184, 72);
                appendCrossMarker(targetVertices, *position, 92.0f, 184.0f, color);
                mm9DatAssetIssueMarkerVertexCount += targetVertices.size() - beforeVertexCount;
                appendRawObjectCandidate(issue.first, *position, issue.second ? 32.0f : 28.0f, 0.0f, 0.0f);
            }
        }

        if (m_showEventMarkers)
        {
            const Game::Mm9EventsData &events = document.mm9DatLoadedSidecars().events;
            const std::vector<Mm9MechanismPreviewCacheEntry> &mechanismPreviewCache =
                mm9MechanismPreviewCache(document);
            const uint32_t previewableMechanismTargetColor = makeAbgr(96, 255, 180);
            const uint32_t previewableMechanismCircleColor = makeAbgr(96, 255, 120);
            const uint32_t inertMechanismTargetColor = makeAbgr(192, 224, 72);
            const uint32_t inertMechanismCircleColor = makeAbgr(216, 236, 80);
            const uint32_t mechanismMotionColor = makeAbgr(255, 96, 72);
            const uint32_t selectedMechanismColor = makeAbgr(255, 255, 255);
            const float mechanismCircleRadius = 112.0f;

            for (size_t mechanismIndex = 0; mechanismIndex < events.mechanisms.size(); ++mechanismIndex)
            {
                const Mm9MechanismPreviewCacheEntry *pCacheEntry =
                    mechanismIndex < mechanismPreviewCache.size()
                        ? &mechanismPreviewCache[mechanismIndex]
                        : nullptr;

                const bool selectedMechanism =
                    selection.kind == EditorSelectionKind::Mm9Mechanism
                    && selection.index == mechanismIndex;
                const bool previewableMechanism = pCacheEntry != nullptr && pCacheEntry->previewable;

                const uint32_t mechanismTargetColor =
                    previewableMechanism ? previewableMechanismTargetColor : inertMechanismTargetColor;
                const uint32_t mechanismCircleColor =
                    previewableMechanism ? previewableMechanismCircleColor : inertMechanismCircleColor;
                std::vector<PreviewVertex> &targetVertices = selectedMechanism ? xrayVertices : vertices;
                const std::optional<bx::Vec3> sourcePosition =
                    pCacheEntry != nullptr ? pCacheEntry->sourceMarkerPosition : std::nullopt;

                std::optional<bx::Vec3> mechanismMarkerPosition =
                    sourcePosition
                        ? std::optional<bx::Vec3>{{sourcePosition->x, sourcePosition->y, sourcePosition->z + 96.0f}}
                        : std::nullopt;
                const size_t beforeMechanismVertexCount = targetVertices.size();

                if (mechanismMarkerPosition)
                {
                    appendCircleMarker(
                        targetVertices,
                        *mechanismMarkerPosition,
                        mechanismCircleRadius,
                        selectedMechanism ? selectedMechanismColor : mechanismCircleColor);
                }

                if (pCacheEntry != nullptr)
                {
                    for (const Mm9MechanismPreviewTargetCache &target : pCacheEntry->targets)
                    {
                        const bx::Vec3 center = target.center;
                        const bx::Vec3 halfExtents = target.halfExtents;
                        const bool targetPreviewable = target.previewable;
                        const uint32_t targetMechanismColor =
                            targetPreviewable ? previewableMechanismTargetColor : inertMechanismTargetColor;
                        const uint32_t targetCircleColor =
                            targetPreviewable ? previewableMechanismCircleColor : inertMechanismCircleColor;

                        if (!mechanismMarkerPosition)
                        {
                            mechanismMarkerPosition = center;
                            appendCircleMarker(
                                targetVertices,
                                {center.x, center.y, center.z + halfExtents.z + 96.0f},
                                mechanismCircleRadius,
                                selectedMechanism ? selectedMechanismColor : mechanismCircleColor);
                        }

                        appendBoxMarker(
                            targetVertices,
                            center,
                            halfExtents,
                            selectedMechanism ? selectedMechanismColor : targetMechanismColor);
                        appendCircleMarker(
                            targetVertices,
                            center,
                            mechanismCircleRadius * 0.72f,
                            selectedMechanism ? selectedMechanismColor : targetCircleColor);

                        MarkerCandidate targetCandidate = {};
                        targetCandidate.selectionKind = EditorSelectionKind::Mm9Mechanism;
                        targetCandidate.selectionIndex = mechanismIndex;
                        targetCandidate.worldPosition = center;
                        targetCandidate.pickRadiusPixels = selectedMechanism ? 36.0f : 30.0f;
                        targetCandidate.mm9MechanismPreviewable = targetPreviewable;
                        applyMm9DatMarkerVisibility(targetCandidate);
                        m_markerCandidates.push_back(targetCandidate);

                        if (mechanismMarkerPosition)
                        {
                            appendLine(targetVertices, *mechanismMarkerPosition, center, targetMechanismColor);
                        }

                        if (targetPreviewable)
                        {
                            const bx::Vec3 pathStart = center;
                            bx::Vec3 previousPoint = pathStart;
                            constexpr int MotionPathSegments = 16;

                            for (int segment = 1; segment <= MotionPathSegments; ++segment)
                            {
                                Game::Mm9DatMechanismPreviewMotion segmentMotion = target.openMotion;
                                segmentMotion.progress =
                                    static_cast<float>(segment) / static_cast<float>(MotionPathSegments);
                                const Game::Mm9DatVec3 transformedPoint =
                                    transformMm9ViewportPoint(
                                        {pathStart.x, pathStart.y, pathStart.z},
                                        segmentMotion);
                                const bx::Vec3 currentPoint = {
                                    transformedPoint.x,
                                    transformedPoint.y,
                                    transformedPoint.z
                                };
                                appendLine(targetVertices, previousPoint, currentPoint, mechanismMotionColor);
                                previousPoint = currentPoint;
                            }

                            appendArrowHead(targetVertices, center, previousPoint, 96.0f, mechanismMotionColor);
                        }
                    }
                }

                mm9DatMechanismTargetMarkerVertexCount += targetVertices.size() - beforeMechanismVertexCount;

                if (mechanismMarkerPosition)
                {
                    MarkerCandidate candidate = {};
                    candidate.selectionKind = EditorSelectionKind::Mm9Mechanism;
                    candidate.selectionIndex = mechanismIndex;
                    candidate.worldPosition = *mechanismMarkerPosition;
                    candidate.pickRadiusPixels = 30.0f;
                    candidate.mm9MechanismPreviewable = previewableMechanism;
                    applyMm9DatMarkerVisibility(candidate);
                    m_markerCandidates.push_back(candidate);
                }
            }
        }

        if (selection.kind == EditorSelectionKind::Mm9DatPolygon
            && selection.index < document.mm9DatRenderMesh().triangles.size())
        {
            const Game::Mm9DatRenderMesh &renderMesh = document.mm9DatRenderMesh();
            const Game::Mm9DatRenderTriangle &selectedTriangle = renderMesh.triangles[selection.index];
            const uint32_t surfaceFillColor = makeAbgrAlpha(96, 196, 255, 40);
            const uint32_t polygonFillColor = makeAbgrAlpha(255, 240, 96, 78);
            const uint32_t polygonEdgeColor = makeAbgr(255, 255, 255);

            for (const Game::Mm9DatRenderTriangle &triangle : renderMesh.triangles)
            {
                if (triangle.sourceModelIndex != selectedTriangle.sourceModelIndex)
                {
                    continue;
                }

                if (triangle.sourceSurfaceIndex == selectedTriangle.sourceSurfaceIndex)
                {
                    appendMm9DatTriangleFill(xrayFillVertices, triangle, surfaceFillColor);
                }

                if (triangle.sourcePolyIndex == selectedTriangle.sourcePolyIndex)
                {
                    appendMm9DatTriangleFill(xrayFillVertices, triangle, polygonFillColor);
                    appendMm9DatTriangleEdges(xrayVertices, triangle, polygonEdgeColor);
                }
            }
        }
    }

    const auto appendTerrainCellOutline =
        [&vertices, &outdoorGeometry](int cellX, int cellY, float zOffset, uint32_t color)
    {
        if (cellX < 0
            || cellY < 0
            || cellX >= (Game::OutdoorMapData::TerrainWidth - 1)
            || cellY >= (Game::OutdoorMapData::TerrainHeight - 1))
        {
            return;
        }

        const size_t topLeftIndex = static_cast<size_t>(cellY * Game::OutdoorMapData::TerrainWidth + cellX);
        const size_t topRightIndex = topLeftIndex + 1;
        const size_t bottomLeftIndex = static_cast<size_t>((cellY + 1) * Game::OutdoorMapData::TerrainWidth + cellX);
        const size_t bottomRightIndex = bottomLeftIndex + 1;
        const bx::Vec3 topLeft = worldPointFromTerrainGrid(cellX, cellY, outdoorGeometry.heightMap[topLeftIndex]);
        const bx::Vec3 topRight = worldPointFromTerrainGrid(cellX + 1, cellY, outdoorGeometry.heightMap[topRightIndex]);
        const bx::Vec3 bottomLeft =
            worldPointFromTerrainGrid(cellX, cellY + 1, outdoorGeometry.heightMap[bottomLeftIndex]);
        const bx::Vec3 bottomRight =
            worldPointFromTerrainGrid(cellX + 1, cellY + 1, outdoorGeometry.heightMap[bottomRightIndex]);

        vertices.push_back({topLeft.x, topLeft.y, topLeft.z + zOffset, color});
        vertices.push_back({topRight.x, topRight.y, topRight.z + zOffset, color});
        vertices.push_back({topRight.x, topRight.y, topRight.z + zOffset, color});
        vertices.push_back({bottomRight.x, bottomRight.y, bottomRight.z + zOffset, color});
        vertices.push_back({bottomRight.x, bottomRight.y, bottomRight.z + zOffset, color});
        vertices.push_back({bottomLeft.x, bottomLeft.y, bottomLeft.z + zOffset, color});
        vertices.push_back({bottomLeft.x, bottomLeft.y, bottomLeft.z + zOffset, color});
        vertices.push_back({topLeft.x, topLeft.y, topLeft.z + zOffset, color});
    };
    const auto appendOutdoorFaceOverlay =
        [](std::vector<PreviewVertex> &targetVertices,
           std::vector<PreviewVertex> &targetFillVertices,
           const Game::OutdoorFaceGeometryData &geometry,
           uint32_t edgeColor,
           uint32_t fillColor,
           float edgeOffset,
           float fillOffset)
    {
        if (geometry.vertices.size() < 3)
        {
            return;
        }

        const bx::Vec3 edgeOffsetVector =
            geometry.hasPlane ? vecScale(geometry.normal, edgeOffset) : bx::Vec3{0.0f, 0.0f, edgeOffset};
        const bx::Vec3 fillOffsetVector =
            geometry.hasPlane ? vecScale(geometry.normal, fillOffset) : bx::Vec3{0.0f, 0.0f, fillOffset};
        const std::array<float, 2> sides = {{1.0f, -1.0f}};

        for (float side : sides)
        {
            const bx::Vec3 sideEdgeOffset = vecScale(edgeOffsetVector, side);
            const bx::Vec3 sideFillOffset = vecScale(fillOffsetVector, side);

            for (size_t vertexIndex = 0; vertexIndex < geometry.vertices.size(); ++vertexIndex)
            {
                const bx::Vec3 &start = geometry.vertices[vertexIndex];
                const bx::Vec3 &end = geometry.vertices[(vertexIndex + 1) % geometry.vertices.size()];
                targetVertices.push_back({
                    start.x + sideEdgeOffset.x,
                    start.y + sideEdgeOffset.y,
                    start.z + sideEdgeOffset.z,
                    edgeColor});
                targetVertices.push_back({
                    end.x + sideEdgeOffset.x,
                    end.y + sideEdgeOffset.y,
                    end.z + sideEdgeOffset.z,
                    edgeColor});
            }

            const bx::Vec3 &base = geometry.vertices[0];

            for (size_t vertexIndex = 1; vertexIndex + 1 < geometry.vertices.size(); ++vertexIndex)
            {
                const bx::Vec3 &middle = geometry.vertices[vertexIndex];
                const bx::Vec3 &end = geometry.vertices[vertexIndex + 1];
                targetFillVertices.push_back({
                    base.x + sideFillOffset.x,
                    base.y + sideFillOffset.y,
                    base.z + sideFillOffset.z,
                    fillColor});
                targetFillVertices.push_back({
                    middle.x + sideFillOffset.x,
                    middle.y + sideFillOffset.y,
                    middle.z + sideFillOffset.z,
                    fillColor});
                targetFillVertices.push_back({
                    end.x + sideFillOffset.x,
                    end.y + sideFillOffset.y,
                    end.z + sideFillOffset.z,
                    fillColor});
            }
        }
    };

    if (m_showTerrainGrid && shouldRenderTerrainHeightmap(document))
    {
        const std::string terrainGridKey = documentGeometryKey(document) + "|terrain_grid";

        if (terrainGridKey != m_cachedOutdoorTerrainGridKey)
        {
            const uint32_t terrainGridColor = makeAbgr(144, 164, 192);
            m_cachedOutdoorTerrainGridKey = terrainGridKey;
            m_cachedOutdoorTerrainGridVertices.clear();
            m_cachedOutdoorTerrainGridVertices.reserve(
                static_cast<size_t>(Game::OutdoorMapData::TerrainHeight)
                    * static_cast<size_t>(Game::OutdoorMapData::TerrainWidth - 1)
                    * 2u
                + static_cast<size_t>(Game::OutdoorMapData::TerrainWidth)
                    * static_cast<size_t>(Game::OutdoorMapData::TerrainHeight - 1)
                    * 2u);

            for (int gridY = 0; gridY < Game::OutdoorMapData::TerrainHeight; ++gridY)
            {
                for (int gridX = 0; gridX < (Game::OutdoorMapData::TerrainWidth - 1); ++gridX)
                {
                    const size_t startIndex = static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
                    const size_t endIndex = startIndex + 1;
                    const bx::Vec3 start =
                        worldPointFromTerrainGrid(gridX, gridY, outdoorGeometry.heightMap[startIndex]);
                    const bx::Vec3 end =
                        worldPointFromTerrainGrid(gridX + 1, gridY, outdoorGeometry.heightMap[endIndex]);
                    m_cachedOutdoorTerrainGridVertices.push_back({start.x, start.y, start.z + 4.0f, terrainGridColor});
                    m_cachedOutdoorTerrainGridVertices.push_back({end.x, end.y, end.z + 4.0f, terrainGridColor});
                }
            }

            for (int gridX = 0; gridX < Game::OutdoorMapData::TerrainWidth; ++gridX)
            {
                for (int gridY = 0; gridY < (Game::OutdoorMapData::TerrainHeight - 1); ++gridY)
                {
                    const size_t startIndex = static_cast<size_t>(gridY * Game::OutdoorMapData::TerrainWidth + gridX);
                    const size_t endIndex = startIndex + Game::OutdoorMapData::TerrainWidth;
                    const bx::Vec3 start =
                        worldPointFromTerrainGrid(gridX, gridY, outdoorGeometry.heightMap[startIndex]);
                    const bx::Vec3 end =
                        worldPointFromTerrainGrid(gridX, gridY + 1, outdoorGeometry.heightMap[endIndex]);
                    m_cachedOutdoorTerrainGridVertices.push_back({start.x, start.y, start.z + 4.0f, terrainGridColor});
                    m_cachedOutdoorTerrainGridVertices.push_back({end.x, end.y, end.z + 4.0f, terrainGridColor});
                }
            }
        }

        vertices.insert(
            vertices.end(),
            m_cachedOutdoorTerrainGridVertices.begin(),
            m_cachedOutdoorTerrainGridVertices.end());
    }

    if (m_showBModels)
    {
        for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
        {
            const std::optional<bx::Vec3> center =
                selectedWorldPosition(document, {EditorSelectionKind::BModel, bmodelIndex});

            if (!center)
            {
                continue;
            }

            MarkerCandidate candidate = {};
            candidate.selectionKind = EditorSelectionKind::BModel;
            candidate.selectionIndex = bmodelIndex;
            candidate.worldPosition = *center;
            candidate.pickRadiusPixels =
                selection.kind == EditorSelectionKind::BModel && selection.index == bmodelIndex ? 32.0f : 24.0f;
            m_markerCandidates.push_back(candidate);
        }
    }

    for (size_t modelInstanceIndex = 0; modelInstanceIndex < sceneData.modelInstances.size(); ++modelInstanceIndex)
    {
        const Game::OutdoorSceneModelInstance &modelInstance = sceneData.modelInstances[modelInstanceIndex];
        const bool scriptedObject =
            isMm9ScriptedModelInstance(
                document,
                modelInstance,
                pMm9ActorSourceLookup);
        MarkerCandidate candidate = {};
        candidate.selectionKind =
            scriptedObject ? EditorSelectionKind::Mm9ScriptedObject : EditorSelectionKind::ModelInstance;
        candidate.selectionIndex = modelInstanceIndex;
        candidate.worldPosition = modelInstanceSelectionCenter(modelInstance);
        candidate.pickRadiusPixels =
            selection.index == modelInstanceIndex
            && (selection.kind == EditorSelectionKind::ModelInstance
                || selection.kind == EditorSelectionKind::Mm9ScriptedObject)
                ? 34.0f
                : 26.0f;
        applyMm9DatMarkerVisibility(candidate);
        m_markerCandidates.push_back(candidate);

        if (scriptedObject)
        {
            int collisionRadius = 32;
            int collisionHeight = 128;
            int collisionVerticalOffset = 0;

            const bool selectedScriptedObject =
                selection.kind == EditorSelectionKind::Mm9ScriptedObject
                && selection.index == modelInstanceIndex;
            std::vector<PreviewVertex> &targetVertices =
                selectedScriptedObject ? xrayVertices : vertices;
            const uint32_t edgeColor =
                selectedScriptedObject ? makeAbgr(255, 255, 255) : makeAbgr(32, 238, 220);
            const uint32_t centerColor =
                selectedScriptedObject ? makeAbgr(32, 238, 220) : makeAbgr(180, 255, 252);
            const bx::Vec3 baseCenter = {
                static_cast<float>(modelInstance.x),
                static_cast<float>(modelInstance.y),
                static_cast<float>(modelInstance.z + collisionVerticalOffset)
            };

            appendCollisionVolumeMarker(
                targetVertices,
                baseCenter,
                static_cast<float>(collisionRadius),
                static_cast<float>(collisionHeight),
                edgeColor,
                centerColor);
        }
    }

    if (m_showEntities)
    {
        const uint32_t sceneLightColor = makeAbgr(255, 218, 96);
        const uint32_t sceneLightCenterColor = makeAbgr(255, 255, 210);

        for (const Game::OutdoorSceneLight &light : sceneData.lights)
        {
            const bx::Vec3 center = {
                static_cast<float>(light.x),
                static_cast<float>(light.y),
                static_cast<float>(light.z)
            };
            appendCrossMarker(vertices, center, 72.0f, 144.0f, sceneLightCenterColor);

            if (light.radius > 0)
            {
                const float radius = std::max(static_cast<float>(light.radius), 48.0f);
                appendCollisionVolumeMarker(
                    vertices,
                    center,
                    radius,
                    radius * 2.0f,
                    sceneLightColor,
                    sceneLightCenterColor);
            }
        }

        for (size_t entityIndex = 0; entityIndex < sceneData.entities.size(); ++entityIndex)
        {
            const Game::OutdoorSceneEntity &entity = sceneData.entities[entityIndex];
            const bx::Vec3 center =
                worldPointFromLegacyPosition(entity.entity.x, entity.entity.y, entity.entity.z);
            MarkerCandidate candidate = {};
            candidate.selectionKind = EditorSelectionKind::Entity;
            candidate.selectionIndex = entityIndex;
            candidate.worldPosition = {center.x, center.y, center.z + 96.0f};
            candidate.pickRadiusPixels = 18.0f;
            candidate.hasEventOverlay =
                entity.entity.eventIdPrimary != 0 || entity.entity.eventIdSecondary != 0;
            candidate.hintOnlyEventOverlay =
                candidate.hasEventOverlay
                && (entity.entity.eventIdPrimary == 0 || session.isHintOnlyEvent(entity.entity.eventIdPrimary))
                && (entity.entity.eventIdSecondary == 0 || session.isHintOnlyEvent(entity.entity.eventIdSecondary));

            if (m_showEntityBillboards)
            {
                const EditorEntityBillboardPreview *pPreview =
                    entityIndex < entityPreviewByIndex.size() ? entityPreviewByIndex[entityIndex] : nullptr;

                if (pEntitySpriteFrameTable != nullptr
                    && pPreview != nullptr
                    && pPreview->spriteId != 0
                    && (pPreview->flags & DecorationDescDontDraw) == 0)
                {
                    const uint32_t animationOffsetTicks =
                        animationTicks + static_cast<uint32_t>(std::abs(pPreview->x + pPreview->y));
                    const Game::SpriteFrameEntry *pFrame =
                        pEntitySpriteFrameTable->getFrame(pPreview->spriteId, animationOffsetTicks);

                    if (pFrame != nullptr)
                    {
                        const float facingRadians = static_cast<float>(pPreview->facing) * bx::kPi / 180.0f;
                        const float angleToCamera = std::atan2(
                            static_cast<float>(pPreview->y) - m_cameraPosition.y,
                            static_cast<float>(pPreview->x) - m_cameraPosition.x);
                        const float octantAngle = facingRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
                        const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
                        const Game::ResolvedSpriteTexture resolvedTexture =
                            Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
                        const float spriteScale = std::max(pFrame->scale, 0.01f);

                        if (tryGetCachedBillboardSize(
                                resolvedTexture.textureName,
                                pFrame->paletteId,
                                spriteScale,
                                candidate.billboardWorldWidth,
                                candidate.billboardWorldHeight))
                        {
                            candidate.hasBillboardBounds = true;
                        }
                    }
                }
            }

            m_markerCandidates.push_back(candidate);
        }
    }

    if (m_showSpawns)
    {
        const uint32_t spawnColor = makeAbgr(96, 144, 255);
        const uint32_t actorSpawnColor = makeAbgr(255, 96, 220);

        for (size_t spawnIndex = 0; spawnIndex < sceneData.spawns.size(); ++spawnIndex)
        {
            const Game::OutdoorSceneSpawn &spawn = sceneData.spawns[spawnIndex];
            const float halfExtent = static_cast<float>(std::max<uint16_t>(spawn.spawn.radius, 96));
            const bx::Vec3 center = {
                static_cast<float>(spawn.spawn.x),
                static_cast<float>(spawn.spawn.y),
                std::max(
                    static_cast<float>(spawn.spawn.z),
                    Game::sampleOutdoorTerrainHeight(
                        outdoorGeometry,
                        static_cast<float>(spawn.spawn.x),
                        static_cast<float>(spawn.spawn.y)))
                    + halfExtent
            };

            const uint32_t markerColor =
                spawn.spawn.typeId == 3 ? actorSpawnColor : spawnColor;

            const float spawnPickRadius =
                spawn.spawn.typeId == 3 ? 34.0f : 26.0f;
            m_markerCandidates.push_back({EditorSelectionKind::Spawn, spawnIndex, center, spawnPickRadius});
        }
    }

    if (m_pendingSpawnPlacementPreview)
    {
        const uint32_t spawnColor = makeAbgr(96, 144, 255);
        const uint32_t actorSpawnColor = makeAbgr(255, 96, 220);
        const uint32_t pendingSpawnColor =
            session.pendingSpawn().typeId == 3 ? actorSpawnColor : spawnColor;
        const float halfExtent = static_cast<float>(std::max<uint16_t>(session.pendingSpawn().radius, 96));
        const bx::Vec3 center = {
            static_cast<float>(m_pendingSpawnPlacementPreview->x),
            static_cast<float>(m_pendingSpawnPlacementPreview->y),
            static_cast<float>(m_pendingSpawnPlacementPreview->z) + halfExtent};
        appendCrossMarker(vertices, center, halfExtent, halfExtent * 2.0f, pendingSpawnColor);
    }

    if (m_showActors)
    {
        for (size_t actorIndex = 0; actorIndex < sceneData.initialState.actors.size(); ++actorIndex)
        {
            const Game::MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];
            const float halfExtent = static_cast<float>(std::max<uint16_t>(actor.radius, 96));
            const float height = static_cast<float>(std::max<uint16_t>(actor.height, 256));
            const bx::Vec3 center = worldPointFromLegacyPosition(actor.x, actor.y, actor.z);
            MarkerCandidate candidate = {};
            candidate.selectionKind = EditorSelectionKind::Actor;
            candidate.selectionIndex = actorIndex;
            candidate.worldPosition = {center.x, center.y, center.z + height * 0.5f};
            candidate.pickRadiusPixels = 28.0f;

            if (m_showActorBillboards)
            {
                const EditorActorBillboardPreview *pPreview =
                    actorIndex < actorPreviewByIndex.size() ? actorPreviewByIndex[actorIndex] : nullptr;

                if (pActorSpriteFrameTable != nullptr && pPreview != nullptr)
                {
                    const Game::SpriteFrameEntry *pFrame = pActorSpriteFrameTable->getFrame(pPreview->spriteFrameIndex, 0);

                    if (pFrame != nullptr)
                    {
                        const float angleToCamera = std::atan2(
                            static_cast<float>(pPreview->y) - m_cameraPosition.y,
                            static_cast<float>(pPreview->x) - m_cameraPosition.x);
                        const float octantAngle = pPreview->yawRadians - angleToCamera + bx::kPi + (bx::kPi / 8.0f);
                        const int octant = static_cast<int>(std::floor(octantAngle / (bx::kPi / 4.0f))) & 7;
                        const Game::ResolvedSpriteTexture resolvedTexture =
                            Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
                        const float spriteScale = std::max(pFrame->scale, 0.01f);

                        if (tryGetCachedBillboardSize(
                                resolvedTexture.textureName,
                                pFrame->paletteId,
                                spriteScale,
                                candidate.billboardWorldWidth,
                                candidate.billboardWorldHeight))
                        {
                            candidate.hasBillboardBounds = true;
                        }
                    }
                }
            }

            m_markerCandidates.push_back(candidate);
        }
    }

    if (m_showSpriteObjects)
    {
        for (size_t objectIndex = 0; objectIndex < sceneData.initialState.spriteObjects.size(); ++objectIndex)
        {
            const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[objectIndex];
            const bx::Vec3 center = worldPointFromLegacyPosition(spriteObject.x, spriteObject.y, spriteObject.z);
            MarkerCandidate candidate = {};
            candidate.selectionKind = EditorSelectionKind::SpriteObject;
            candidate.selectionIndex = objectIndex;
            candidate.worldPosition = {center.x, center.y, center.z + 72.0f};
            candidate.pickRadiusPixels = 18.0f;

            const uint16_t objectDescriptionId =
                session.resolvedSpriteObjectObjectDescriptionId(spriteObject);
            const Game::ObjectEntry *pObjectEntry = session.objectTable().get(objectDescriptionId);
            const uint16_t spriteId = pObjectEntry != nullptr ? pObjectEntry->spriteId : spriteObject.spriteId;
            if (m_showSpriteObjects && pEntitySpriteFrameTable != nullptr && spriteId != 0)
            {
                const Game::SpriteFrameEntry *pFrame =
                    pEntitySpriteFrameTable->getFrame(spriteId, static_cast<uint32_t>(spriteObject.timeSinceCreated) * 8u);

                if (pFrame != nullptr)
                {
                    const Game::ResolvedSpriteTexture resolvedTexture =
                        Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
                    const float spriteScale = std::max(pFrame->scale, 0.01f);

                    if (tryGetCachedBillboardSize(
                            resolvedTexture.textureName,
                            pFrame->paletteId,
                            spriteScale,
                            candidate.billboardWorldWidth,
                            candidate.billboardWorldHeight))
                    {
                        candidate.hasBillboardBounds = true;
                    }
                }
            }

            m_markerCandidates.push_back(candidate);
        }
    }

    if (selection.kind == EditorSelectionKind::Terrain)
    {
        int cellX = 0;
        int cellY = 0;

        if (decodeSelectedTerrainCell(selection, cellX, cellY)
            && cellX < (Game::OutdoorMapData::TerrainWidth - 1)
            && cellY < (Game::OutdoorMapData::TerrainHeight - 1))
        {
            const uint32_t terrainSelectionColor = makeAbgr(96, 255, 255);
            appendTerrainCellOutline(cellX, cellY, 16.0f, terrainSelectionColor);
        }
    }

    if (m_hoverTerrainValid && m_placementKind == EditorSelectionKind::Terrain)
    {
        uint32_t hoverColor = makeAbgr(255, 214, 96);

        if (session.terrainSculptEnabled())
        {
            switch (session.terrainSculptMode())
            {
            case EditorTerrainSculptMode::Flatten:
                hoverColor = makeAbgr(96, 220, 255);
                break;

            case EditorTerrainSculptMode::Smooth:
                hoverColor = makeAbgr(176, 216, 255);
                break;

            case EditorTerrainSculptMode::Noise:
                hoverColor = makeAbgr(220, 196, 120);
                break;

            case EditorTerrainSculptMode::Ramp:
                hoverColor = makeAbgr(196, 156, 255);
                break;

            case EditorTerrainSculptMode::Lower:
                hoverColor = makeAbgr(255, 140, 96);
                break;

            case EditorTerrainSculptMode::Raise:
            default:
                hoverColor = makeAbgr(144, 255, 112);
                break;
            }
        }

        const bool hoverMatchesSelection =
            selection.kind == EditorSelectionKind::Terrain
            && selection.index == flattenTerrainCellIndex(m_hoverTerrainCellX, m_hoverTerrainCellY);

        if (session.terrainSculptEnabled())
        {
            const int radius = std::max(session.terrainSculptRadius(), 0);

            if (session.terrainSculptMode() == EditorTerrainSculptMode::Ramp
                && m_activeTerrainSculpt.active
                && m_activeTerrainSculpt.anchorSampleX != std::numeric_limits<int>::min())
            {
                rasterizeTerrainLine(
                    m_activeTerrainSculpt.anchorSampleX,
                    m_activeTerrainSculpt.anchorSampleY,
                    m_hoverTerrainCellX,
                    m_hoverTerrainCellY,
                    [&](int stepX, int stepY)
                    {
                        forEachTerrainBrushCell(
                            stepX,
                            stepY,
                            radius,
                            [&](int targetX, int targetY, float, int)
                            {
                                appendTerrainCellOutline(targetX, targetY, 10.0f, hoverColor);
                            });
                    });
            }
            else
            {
                for (int offsetY = -radius; offsetY <= radius; ++offsetY)
                {
                    for (int offsetX = -radius; offsetX <= radius; ++offsetX)
                    {
                        const int targetX = m_hoverTerrainCellX + offsetX;
                        const int targetY = m_hoverTerrainCellY + offsetY;
                        const float distance = std::sqrt(static_cast<float>(offsetX * offsetX + offsetY * offsetY));

                        if (distance > static_cast<float>(radius))
                        {
                            continue;
                        }

                        appendTerrainCellOutline(targetX, targetY, 10.0f, hoverColor);
                    }
                }
            }
        }
        else if (session.terrainPaintEnabled() && session.terrainPaintMode() == EditorTerrainPaintMode::Rectangle)
        {
            const int startX = m_activeTerrainPaint.active ? m_activeTerrainPaint.anchorCellX : m_hoverTerrainCellX;
            const int startY = m_activeTerrainPaint.active ? m_activeTerrainPaint.anchorCellY : m_hoverTerrainCellY;
            const int minX = std::min(startX, m_hoverTerrainCellX);
            const int maxX = std::max(startX, m_hoverTerrainCellX);
            const int minY = std::min(startY, m_hoverTerrainCellY);
            const int maxY = std::max(startY, m_hoverTerrainCellY);

            for (int targetY = minY; targetY <= maxY; ++targetY)
            {
                for (int targetX = minX; targetX <= maxX; ++targetX)
                {
                    appendTerrainCellOutline(targetX, targetY, 10.0f, hoverColor);
                }
            }
        }
        else if (session.terrainPaintEnabled() && session.terrainPaintMode() == EditorTerrainPaintMode::Brush)
        {
            const int radius = std::max(session.terrainPaintRadius(), 0);

            forEachTerrainBrushCell(
                m_hoverTerrainCellX,
                m_hoverTerrainCellY,
                radius,
                [&](int targetX, int targetY, float, int)
                {
                    appendTerrainCellOutline(targetX, targetY, 10.0f, hoverColor);
                });
        }
        else if (!hoverMatchesSelection)
        {
            appendTerrainCellOutline(m_hoverTerrainCellX, m_hoverTerrainCellY, 10.0f, hoverColor);
        }
    }

    if (m_showEventMarkers)
    {
        const std::string eventOverlayKey = documentGeometryKey(document) + "|outdoor_event_overlay";

        if (eventOverlayKey != m_cachedOutdoorEventOverlayKey)
        {
            const uint32_t defaultEventEdgeColor = makeAbgrAlpha(72, 220, 208, 148);
            const uint32_t defaultEventFillColor = makeAbgrAlpha(72, 220, 208, 50);
            const uint32_t explicitEventEdgeColor = makeAbgrAlpha(72, 220, 208, 192);
            const uint32_t explicitEventFillColor = makeAbgrAlpha(72, 220, 208, 82);
            const uint32_t hintOnlyDefaultEventEdgeColor = makeAbgrAlpha(108, 212, 202, 124);
            const uint32_t hintOnlyDefaultEventFillColor = makeAbgrAlpha(108, 212, 202, 38);
            const uint32_t hintOnlyExplicitEventEdgeColor = makeAbgrAlpha(112, 220, 208, 152);
            const uint32_t hintOnlyExplicitEventFillColor = makeAbgrAlpha(112, 220, 208, 58);
            m_cachedOutdoorEventOverlayKey = eventOverlayKey;
            m_cachedOutdoorEventOverlayVertices.clear();
            m_cachedOutdoorEventOverlayFillVertices.clear();

            for (size_t bmodelIndex = 0; bmodelIndex < outdoorGeometry.bmodels.size(); ++bmodelIndex)
            {
                const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
                const std::optional<uint16_t> defaultEventId =
                    bmodelIndex < defaultBModelEvents.size() ? defaultBModelEvents[bmodelIndex] : std::nullopt;
                const std::vector<uint16_t> *pFaceEvents =
                    bmodelIndex < effectiveFaceEvents.size() ? &effectiveFaceEvents[bmodelIndex] : nullptr;
                const bool defaultEventHintOnly = defaultEventId && session.isHintOnlyEvent(*defaultEventId);

                if (defaultEventId)
                {
                    for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
                    {
                        Game::OutdoorFaceGeometryData geometry = {};

                        if (!Game::buildOutdoorFaceGeometry(
                                bmodel,
                                bmodelIndex,
                                bmodel.faces[faceIndex],
                                faceIndex,
                                geometry,
                                true))
                        {
                            continue;
                        }

                        appendOutdoorFaceOverlay(
                            m_cachedOutdoorEventOverlayVertices,
                            m_cachedOutdoorEventOverlayFillVertices,
                            geometry,
                            defaultEventHintOnly ? hintOnlyDefaultEventEdgeColor : defaultEventEdgeColor,
                            defaultEventHintOnly ? hintOnlyDefaultEventFillColor : defaultEventFillColor,
                            5.0f,
                            3.0f);
                    }
                }

                for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
                {
                    const uint16_t eventId =
                        pFaceEvents != nullptr && faceIndex < pFaceEvents->size() ? (*pFaceEvents)[faceIndex] : 0;

                    if (eventId == 0 || (defaultEventId && eventId == *defaultEventId))
                    {
                        continue;
                    }

                    Game::OutdoorFaceGeometryData geometry = {};

                    if (!Game::buildOutdoorFaceGeometry(
                            bmodel,
                            bmodelIndex,
                            bmodel.faces[faceIndex],
                            faceIndex,
                            geometry,
                            true)
                        || geometry.vertices.empty())
                    {
                        continue;
                    }

                    appendOutdoorFaceOverlay(
                        m_cachedOutdoorEventOverlayVertices,
                        m_cachedOutdoorEventOverlayFillVertices,
                        geometry,
                        session.isHintOnlyEvent(eventId) ? hintOnlyExplicitEventEdgeColor : explicitEventEdgeColor,
                        session.isHintOnlyEvent(eventId) ? hintOnlyExplicitEventFillColor : explicitEventFillColor,
                        8.0f,
                        6.0f);
                }
            }
        }

        vertices.insert(
            vertices.end(),
            m_cachedOutdoorEventOverlayVertices.begin(),
            m_cachedOutdoorEventOverlayVertices.end());
        fillVertices.insert(
            fillVertices.end(),
            m_cachedOutdoorEventOverlayFillVertices.begin(),
            m_cachedOutdoorEventOverlayFillVertices.end());
    }

    const uint32_t faceSelectionColor = makeAbgr(255, 96, 255);
    const uint32_t facePrimarySelectionColor = makeAbgr(255, 255, 255);
    const uint32_t faceSelectionFillColor = makeAbgrAlpha(255, 96, 255, 72);
    const uint32_t facePrimarySelectionFillColor = makeAbgrAlpha(255, 240, 96, 84);

    for (size_t flatIndex : session.selectedInteractiveFaceIndices())
    {
        size_t bmodelIndex = 0;
        size_t faceIndex = 0;

        if (decodeSelectedInteractiveFace(document, {EditorSelectionKind::InteractiveFace, flatIndex}, bmodelIndex, faceIndex))
        {
            Game::OutdoorFaceGeometryData geometry = {};

            if (Game::buildOutdoorFaceGeometry(
                    outdoorGeometry.bmodels[bmodelIndex],
                    bmodelIndex,
                    outdoorGeometry.bmodels[bmodelIndex].faces[faceIndex],
                    faceIndex,
                    geometry,
                    true))
            {
                const uint32_t color =
                    selection.kind == EditorSelectionKind::InteractiveFace && selection.index == flatIndex
                        ? facePrimarySelectionColor
                        : faceSelectionColor;
                const uint32_t fillColor =
                    selection.kind == EditorSelectionKind::InteractiveFace && selection.index == flatIndex
                        ? facePrimarySelectionFillColor
                        : faceSelectionFillColor;

                for (size_t vertexIndex = 0; vertexIndex < geometry.vertices.size(); ++vertexIndex)
                {
                    const bx::Vec3 &start = geometry.vertices[vertexIndex];
                    const bx::Vec3 &end = geometry.vertices[(vertexIndex + 1) % geometry.vertices.size()];
                    xrayVertices.push_back({start.x, start.y, start.z + 8.0f, color});
                    xrayVertices.push_back({end.x, end.y, end.z + 8.0f, color});
                }

                if (geometry.vertices.size() >= 3)
                {
                    const bx::Vec3 base = geometry.vertices[0];

                    for (size_t vertexIndex = 1; vertexIndex + 1 < geometry.vertices.size(); ++vertexIndex)
                    {
                        const bx::Vec3 &middle = geometry.vertices[vertexIndex];
                        const bx::Vec3 &end = geometry.vertices[vertexIndex + 1];
                        xrayFillVertices.push_back({base.x, base.y, base.z + 6.0f, fillColor});
                        xrayFillVertices.push_back({middle.x, middle.y, middle.z + 6.0f, fillColor});
                        xrayFillVertices.push_back({end.x, end.y, end.z + 6.0f, fillColor});
                    }
                }
            }
        }
    }

    if (m_showChestLinks && selection.kind == EditorSelectionKind::Chest)
    {
        const uint32_t chestLinkColor = makeAbgr(255, 176, 96);

        for (const EditorChestLink &link : session.findChestLinks(selection.index))
        {
            if (link.kind == EditorChestLink::Kind::Entity)
            {
                if (link.entityIndex >= sceneData.entities.size())
                {
                    continue;
                }

                const Game::OutdoorEntity &entity = sceneData.entities[link.entityIndex].entity;
                const bx::Vec3 center = worldPointFromLegacyPosition(entity.x, entity.y, entity.z);
                appendCrossMarker(vertices, {center.x, center.y, center.z + 256.0f}, 96.0f, 128.0f, chestLinkColor);
            }
            else if (link.bmodelIndex < outdoorGeometry.bmodels.size()
                && link.faceIndex < outdoorGeometry.bmodels[link.bmodelIndex].faces.size())
            {
                Game::OutdoorFaceGeometryData geometry = {};

                if (!Game::buildOutdoorFaceGeometry(
                        outdoorGeometry.bmodels[link.bmodelIndex],
                        link.bmodelIndex,
                        outdoorGeometry.bmodels[link.bmodelIndex].faces[link.faceIndex],
                        link.faceIndex,
                        geometry,
                        true))
                {
                    continue;
                }

                for (size_t vertexIndex = 0; vertexIndex < geometry.vertices.size(); ++vertexIndex)
                {
                    const bx::Vec3 &start = geometry.vertices[vertexIndex];
                    const bx::Vec3 &end = geometry.vertices[(vertexIndex + 1) % geometry.vertices.size()];
                    xrayVertices.push_back({start.x, start.y, start.z + 10.0f, chestLinkColor});
                    xrayVertices.push_back({end.x, end.y, end.z + 10.0f, chestLinkColor});
                }
            }
        }
    }

    if (selection.kind == EditorSelectionKind::BModel
        && selection.index < outdoorGeometry.bmodels.size()
        && m_transformGizmoMode == TransformGizmoMode::Rotate)
    {
        const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[selection.index];
        const std::optional<bx::Vec3> bmodelCenter = selectedWorldPosition(document, selection);

        if (bmodelCenter)
        {
            const float radius = bmodelRotationHandleRadius(bmodel);
            bx::Vec3 xAxisWorld = {1.0f, 0.0f, 0.0f};
            bx::Vec3 yAxisWorld = {0.0f, 1.0f, 0.0f};
            bx::Vec3 zAxisWorld = {0.0f, 0.0f, 1.0f};
            computeTransformBasis(document, selection, m_transformSpaceMode, xAxisWorld, yAxisWorld, zAxisWorld);
            const auto appendRotationRing =
                [&vertices, &bmodelCenter, radius](const bx::Vec3 &axis, uint32_t color)
            {
                for (int segmentIndex = 0; segmentIndex < GizmoRotationSegments; ++segmentIndex)
                {
                    const float angle0 =
                        (static_cast<float>(segmentIndex) / static_cast<float>(GizmoRotationSegments)) * bx::kPi2;
                    const float angle1 =
                        (static_cast<float>(segmentIndex + 1) / static_cast<float>(GizmoRotationSegments)) * bx::kPi2;
                    bx::Vec3 point0 = *bmodelCenter;
                    bx::Vec3 point1 = *bmodelCenter;

                    if (std::fabs(axis.x) > 0.5f)
                    {
                        point0.y += std::cos(angle0) * radius;
                        point0.z += std::sin(angle0) * radius;
                        point1.y += std::cos(angle1) * radius;
                        point1.z += std::sin(angle1) * radius;
                    }
                    else if (std::fabs(axis.y) > 0.5f)
                    {
                        point0.x += std::cos(angle0) * radius;
                        point0.z += std::sin(angle0) * radius;
                        point1.x += std::cos(angle1) * radius;
                        point1.z += std::sin(angle1) * radius;
                    }
                    else
                    {
                        point0.x += std::cos(angle0) * radius;
                        point0.y += std::sin(angle0) * radius;
                        point1.x += std::cos(angle1) * radius;
                        point1.y += std::sin(angle1) * radius;
                    }

                    vertices.push_back({point0.x, point0.y, point0.z, color});
                    vertices.push_back({point1.x, point1.y, point1.z, color});
                }
            };

            appendRotationRing(xAxisWorld, makeAbgr(255, 96, 96));
            appendRotationRing(yAxisWorld, makeAbgr(96, 255, 96));
            appendRotationRing(zAxisWorld, makeAbgr(96, 160, 255));
        }
    }

    if (const std::optional<bx::Vec3> selectedPosition = selectedWorldPosition(document, selection))
    {
        const bx::Vec3 center = *selectedPosition;
        const bool showTranslateGizmo =
            selection.kind != EditorSelectionKind::BModel || m_transformGizmoMode == TransformGizmoMode::Translate;
        const bool useScreenSpaceTranslateGizmo =
            m_transformGizmoMode == TransformGizmoMode::Translate
            && (selection.kind == EditorSelectionKind::BModel
                || selection.kind == EditorSelectionKind::ModelInstance
                || selection.kind == EditorSelectionKind::Mm9ScriptedObject
                || isIndoorMovableSelectionKind(selection.kind));
        bx::Vec3 xAxisWorld = {1.0f, 0.0f, 0.0f};
        bx::Vec3 yAxisWorld = {0.0f, 1.0f, 0.0f};
        bx::Vec3 zAxisWorld = {0.0f, 0.0f, 1.0f};
        computeTransformBasis(document, selection, m_transformSpaceMode, xAxisWorld, yAxisWorld, zAxisWorld);

        if (showTranslateGizmo && !useScreenSpaceTranslateGizmo)
        {
            const uint32_t xAxisColor = makeAbgr(255, 96, 96);
            const uint32_t yAxisColor = makeAbgr(96, 255, 96);
            const uint32_t zAxisColor = makeAbgr(96, 160, 255);
            const uint32_t planeColor = makeAbgr(255, 224, 96);
            const float axisLength = GizmoAxisWorldLength;
            const bx::Vec3 xAxisEnd = vecAdd(center, vecScale(xAxisWorld, axisLength));
            const bx::Vec3 yAxisEnd = vecAdd(center, vecScale(yAxisWorld, axisLength));
            const bx::Vec3 zAxisEnd = vecAdd(center, vecScale(zAxisWorld, axisLength));
            const float planeExtent = axisLength * 0.35f;
            const bx::Vec3 planeX = vecAdd(center, vecScale(xAxisWorld, planeExtent));
            const bx::Vec3 planeY = vecAdd(center, vecScale(yAxisWorld, planeExtent));
            const bx::Vec3 planeXY = vecAdd(planeX, vecScale(yAxisWorld, planeExtent));

            vertices.push_back({center.x, center.y, center.z, xAxisColor});
            vertices.push_back({xAxisEnd.x, xAxisEnd.y, xAxisEnd.z, xAxisColor});
            vertices.push_back({center.x, center.y, center.z, yAxisColor});
            vertices.push_back({yAxisEnd.x, yAxisEnd.y, yAxisEnd.z, yAxisColor});
            vertices.push_back({center.x, center.y, center.z, zAxisColor});
            vertices.push_back({zAxisEnd.x, zAxisEnd.y, zAxisEnd.z, zAxisColor});

            vertices.push_back({center.x, center.y, center.z, planeColor});
            vertices.push_back({planeX.x, planeX.y, planeX.z, planeColor});
            vertices.push_back({planeX.x, planeX.y, planeX.z, planeColor});
            vertices.push_back({planeXY.x, planeXY.y, planeXY.z, planeColor});
            vertices.push_back({planeXY.x, planeXY.y, planeXY.z, planeColor});
            vertices.push_back({planeY.x, planeY.y, planeY.z, planeColor});
            vertices.push_back({planeY.x, planeY.y, planeY.z, planeColor});
            vertices.push_back({center.x, center.y, center.z, planeColor});
            appendCrossMarker(vertices, center, 144.0f, 256.0f, makeAbgr(255, 255, 255));
        }
    }

    if (vertices.empty() && fillVertices.empty() && xrayVertices.empty() && xrayFillVertices.empty())
    {
        return;
    }

    if (!fillVertices.empty()
        && bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(fillVertices.size()), PreviewVertex::ms_layout)
            < fillVertices.size())
    {
        return;
    }

    if (!xrayFillVertices.empty()
        && bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(xrayFillVertices.size()),
                PreviewVertex::ms_layout)
            < xrayFillVertices.size())
    {
        return;
    }

    if (!vertices.empty()
        && bgfx::getAvailTransientVertexBuffer(static_cast<uint32_t>(vertices.size()), PreviewVertex::ms_layout)
            < vertices.size())
    {
        return;
    }

    if (!xrayVertices.empty()
        && bgfx::getAvailTransientVertexBuffer(
                static_cast<uint32_t>(xrayVertices.size()),
                PreviewVertex::ms_layout)
            < xrayVertices.size())
    {
        return;
    }

    float transform[16] = {};
    bx::mtxIdentity(transform);

    if (!fillVertices.empty())
    {
        bgfx::TransientVertexBuffer fillVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &fillVertexBuffer,
            static_cast<uint32_t>(fillVertices.size()),
            PreviewVertex::ms_layout);
        std::memcpy(fillVertexBuffer.data, fillVertices.data(), fillVertices.size() * sizeof(PreviewVertex));
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &fillVertexBuffer, 0, static_cast<uint32_t>(fillVertices.size()));
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_BLEND_ALPHA
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }

    if (!xrayFillVertices.empty())
    {
        bgfx::TransientVertexBuffer xrayFillVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &xrayFillVertexBuffer,
            static_cast<uint32_t>(xrayFillVertices.size()),
            PreviewVertex::ms_layout);
        std::memcpy(
            xrayFillVertexBuffer.data,
            xrayFillVertices.data(),
            xrayFillVertices.size() * sizeof(PreviewVertex));
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &xrayFillVertexBuffer, 0, static_cast<uint32_t>(xrayFillVertices.size()));
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_DEPTH_TEST_ALWAYS
                | BGFX_STATE_BLEND_ALPHA
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }

    if (!vertices.empty())
    {
        bgfx::TransientVertexBuffer transientVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &transientVertexBuffer,
            static_cast<uint32_t>(vertices.size()),
            PreviewVertex::ms_layout);
        std::memcpy(transientVertexBuffer.data, vertices.data(), vertices.size() * sizeof(PreviewVertex));
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &transientVertexBuffer, 0, static_cast<uint32_t>(vertices.size()));
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_WRITE_Z
                | BGFX_STATE_DEPTH_TEST_LESS
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }

    if (!xrayVertices.empty())
    {
        bgfx::TransientVertexBuffer xrayVertexBuffer = {};
        bgfx::allocTransientVertexBuffer(
            &xrayVertexBuffer,
            static_cast<uint32_t>(xrayVertices.size()),
            PreviewVertex::ms_layout);
        std::memcpy(xrayVertexBuffer.data, xrayVertices.data(), xrayVertices.size() * sizeof(PreviewVertex));
        bgfx::setTransform(transform);
        bgfx::setVertexBuffer(0, &xrayVertexBuffer, 0, static_cast<uint32_t>(xrayVertices.size()));
        bgfx::setState(
            BGFX_STATE_WRITE_RGB
                | BGFX_STATE_WRITE_A
                | BGFX_STATE_DEPTH_TEST_ALWAYS
                | BGFX_STATE_PT_LINES
                | BGFX_STATE_MSAA);
        bgfx::submit(EditorSceneViewId, m_programHandle);
    }

    if (mm9DatDocument && mm9DatSourceMarkerVertexCount != 0)
    {
        ++m_lastRenderSubmissionStats.mm9DatSourceMarkerSubmissions;
        m_lastRenderSubmissionStats.mm9DatSourceMarkerVertices +=
            static_cast<uint32_t>(mm9DatSourceMarkerVertexCount);
    }

    if (mm9DatDocument && mm9DatAssetIssueMarkerVertexCount != 0)
    {
        ++m_lastRenderSubmissionStats.mm9DatAssetIssueMarkerSubmissions;
        m_lastRenderSubmissionStats.mm9DatAssetIssueMarkerVertices +=
            static_cast<uint32_t>(mm9DatAssetIssueMarkerVertexCount);
    }

    if (mm9DatDocument && mm9DatMechanismTargetMarkerVertexCount != 0)
    {
        ++m_lastRenderSubmissionStats.mm9DatMechanismTargetMarkerSubmissions;
        m_lastRenderSubmissionStats.mm9DatMechanismTargetMarkerVertices +=
            static_cast<uint32_t>(mm9DatMechanismTargetMarkerVertexCount);
    }
}

std::string EditorOutdoorViewport::documentGeometryKey(const EditorDocument &document)
{
    return document.displayName()
        + "|"
        + document.sceneVirtualPath()
        + "|"
        + std::to_string(document.sceneRevision());
}

std::string EditorOutdoorViewport::documentCameraKey(const EditorDocument &document)
{
    return document.displayName() + "|" + document.sceneVirtualPath();
}
}
