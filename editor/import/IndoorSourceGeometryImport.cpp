#include "editor/import/IndoorSourceGeometryImport.h"

#include "editor/import/ObjModelImport.h"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <optional>
#include <unordered_set>
#include <utility>

namespace OpenYAMM::Editor
{
namespace
{
std::string trimCopy(const std::string &value)
{
    const auto begin = std::find_if_not(value.begin(), value.end(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    });
    const auto end = std::find_if_not(value.rbegin(), value.rend(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    }).base();

    if (begin >= end)
    {
        return {};
    }

    return std::string(begin, end);
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

std::string sourceNodeNameFromModelName(const std::string &modelName)
{
    const size_t separator = modelName.find(" :: ");

    if (separator == std::string::npos)
    {
        return trimCopy(modelName);
    }

    return trimCopy(modelName.substr(0, separator));
}

std::string stripIndexedMaterialSuffix(const std::string &materialName)
{
    const std::string trimmed = trimCopy(materialName);
    const size_t bracketOffset = trimmed.rfind(" [");

    if (bracketOffset == std::string::npos || trimmed.back() != ']')
    {
        return trimmed;
    }

    return trimCopy(trimmed.substr(0, bracketOffset));
}

std::string sanitizeId(const std::string &value)
{
    std::string result;
    bool lastWasSeparator = false;

    for (char character : trimCopy(value))
    {
        const unsigned char byte = static_cast<unsigned char>(character);

        if (std::isalnum(byte) != 0)
        {
            result.push_back(static_cast<char>(std::tolower(byte)));
            lastWasSeparator = false;
        }
        else if (!lastWasSeparator)
        {
            result.push_back('_');
            lastWasSeparator = true;
        }
    }

    while (!result.empty() && result.back() == '_')
    {
        result.pop_back();
    }

    while (!result.empty() && result.front() == '_')
    {
        result.erase(result.begin());
    }

    return result.empty() ? "unnamed" : result;
}

bool startsWithInsensitive(const std::string &value, const std::string &prefix)
{
    if (value.size() < prefix.size())
    {
        return false;
    }

    return toLowerCopy(value.substr(0, prefix.size())) == toLowerCopy(prefix);
}

std::string stripPrefix(const std::string &value, const std::string &prefix)
{
    if (!startsWithInsensitive(value, prefix))
    {
        return value;
    }

    return value.substr(prefix.size());
}

std::string displayNameFromId(const std::string &id)
{
    std::string result = id;

    for (char &character : result)
    {
        if (character == '_')
        {
            character = ' ';
        }
    }

    return result;
}

std::string makeUniqueId(std::unordered_set<std::string> &seenIds, const std::string &baseId)
{
    std::string id = sanitizeId(baseId);

    if (seenIds.insert(id).second)
    {
        return id;
    }

    for (size_t suffix = 2; suffix < 100000; ++suffix)
    {
        const std::string candidate = id + "_" + std::to_string(suffix);

        if (seenIds.insert(candidate).second)
        {
            return candidate;
        }
    }

    return id;
}

std::string extensionWithoutDot(const std::filesystem::path &path)
{
    std::string extension = toLowerCopy(path.extension().string());

    if (!extension.empty() && extension.front() == '.')
    {
        extension.erase(extension.begin());
    }

    return extension.empty() ? "unknown" : extension;
}

std::string defaultTextureFromImportedMaterial(const ImportedModelMaterial &material)
{
    const std::string textureLabel = trimCopy(material.textureLabel);

    if (!textureLabel.empty())
    {
        return textureLabel;
    }

    return stripIndexedMaterialSuffix(material.name);
}

void appendMaterials(
    const std::vector<ImportedModel> &models,
    EditorIndoorGeometryMetadata &metadata)
{
    std::unordered_set<std::string> seenMaterialNames;
    std::unordered_set<std::string> seenMaterialIds;

    for (const ImportedModel &model : models)
    {
        for (const ImportedModelMaterial &importedMaterial : model.materials)
        {
            const std::string sourceMaterial = stripIndexedMaterialSuffix(importedMaterial.name);

            if (sourceMaterial.empty() || !seenMaterialNames.insert(toLowerCopy(importedMaterial.name)).second)
            {
                continue;
            }

            EditorIndoorGeometryMaterialMetadata material = {};
            material.id = makeUniqueId(seenMaterialIds, sourceMaterial);
            material.sourceMaterial = sourceMaterial;
            material.texture = defaultTextureFromImportedMaterial(importedMaterial);
            metadata.materials.push_back(std::move(material));
        }
    }
}

std::string materialIdForFace(
    const EditorIndoorGeometryMetadata &metadata,
    const ImportedModel &model)
{
    if (model.faces.empty())
    {
        return {};
    }

    const std::string sourceMaterial = stripIndexedMaterialSuffix(model.faces.front().materialName);

    for (const EditorIndoorGeometryMaterialMetadata &material : metadata.materials)
    {
        if (toLowerCopy(material.sourceMaterial) == toLowerCopy(sourceMaterial))
        {
            return material.id;
        }
    }

    return {};
}

void inferPortalRooms(
    const std::string &portalSuffix,
    std::string &frontRoom,
    std::string &backRoom)
{
    const size_t separator = portalSuffix.find('_');

    if (separator == std::string::npos)
    {
        return;
    }

    frontRoom = "room_" + sanitizeId(portalSuffix.substr(0, separator));
    backRoom = "room_" + sanitizeId(portalSuffix.substr(separator + 1));
}

std::string inferMechanismKind(const std::string &suffix)
{
    const std::string lowerSuffix = toLowerCopy(suffix);

    if (lowerSuffix.find("gate") != std::string::npos || lowerSuffix.find("door") != std::string::npos)
    {
        return "sliding_door";
    }

    if (lowerSuffix.find("lift") != std::string::npos || lowerSuffix.find("platform") != std::string::npos)
    {
        return "platform";
    }

    return "mechanism";
}

std::optional<uint32_t> trailingNumber(const std::string &value)
{
    const std::string trimmed = trimCopy(value);
    size_t begin = trimmed.size();

    while (begin > 0 && std::isdigit(static_cast<unsigned char>(trimmed[begin - 1])) != 0)
    {
        --begin;
    }

    if (begin == trimmed.size())
    {
        return std::nullopt;
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(trimmed.substr(begin)));
    }
    catch (...)
    {
        return std::nullopt;
    }
}

void appendImportedModelMetadata(
    const ImportedModel &model,
    EditorIndoorGeometryMetadata &metadata,
    IndoorSourceGeometryImportResult &result,
    std::unordered_set<std::string> &seenRoomIds,
    std::unordered_set<std::string> &seenPortalIds,
    std::unordered_set<std::string> &seenSurfaceIds,
    std::unordered_set<std::string> &seenMechanismIds,
    std::unordered_set<std::string> &seenEntityIds,
    std::unordered_set<std::string> &seenLightIds,
    std::unordered_set<std::string> &seenSpawnIds)
{
    const std::string sourceNode = sourceNodeNameFromModelName(model.name);
    const std::string lowerNode = toLowerCopy(sourceNode);

    if (startsWithInsensitive(lowerNode, "room_"))
    {
        const std::string suffix = stripPrefix(sourceNode, "ROOM_");
        const std::string roomId = makeUniqueId(seenRoomIds, "room_" + sanitizeId(suffix));
        EditorIndoorGeometryRoomMetadata room = {};
        room.id = roomId;
        room.name = displayNameFromId(sanitizeId(suffix));
        room.sourceNodeNames.push_back(sourceNode);
        metadata.rooms.push_back(std::move(room));
        return;
    }

    if (startsWithInsensitive(lowerNode, "portal_"))
    {
        const std::string suffix = stripPrefix(sourceNode, "PORTAL_");
        EditorIndoorGeometryPortalMetadata portal = {};
        portal.id = makeUniqueId(seenPortalIds, "portal_" + sanitizeId(suffix));
        portal.name = displayNameFromId(sanitizeId(suffix));
        portal.sourceNodeName = sourceNode;
        inferPortalRooms(suffix, portal.frontRoom, portal.backRoom);
        metadata.portals.push_back(std::move(portal));
        return;
    }

    if (startsWithInsensitive(lowerNode, "trigger_"))
    {
        const std::string suffix = stripPrefix(sourceNode, "TRIGGER_");
        EditorIndoorGeometrySurfaceMetadata surface = {};
        surface.id = makeUniqueId(seenSurfaceIds, sanitizeId(suffix));
        surface.sourceNodeName = sourceNode;
        surface.materialId = materialIdForFace(metadata, model);
        surface.flags.push_back("clickable");
        surface.trigger = EditorIndoorGeometrySurfaceTriggerMetadata{};
        surface.trigger->type = "door";
        metadata.surfaces.push_back(std::move(surface));
        return;
    }

    if (startsWithInsensitive(lowerNode, "mech_"))
    {
        const std::string suffix = stripPrefix(sourceNode, "MECH_");
        EditorIndoorGeometryMechanismMetadata mechanism = {};
        mechanism.id = makeUniqueId(seenMechanismIds, sanitizeId(suffix));
        mechanism.name = displayNameFromId(sanitizeId(suffix));
        mechanism.kind = inferMechanismKind(suffix);
        mechanism.sourceNodeNames.push_back(sourceNode);
        mechanism.initialState = "closed";
        mechanism.doorId = trailingNumber(suffix);
        metadata.mechanisms.push_back(std::move(mechanism));
        return;
    }

    if (startsWithInsensitive(lowerNode, "decor_"))
    {
        const std::string suffix = stripPrefix(sourceNode, "DECOR_");
        EditorIndoorGeometryEntityMetadata entity = {};
        entity.id = makeUniqueId(seenEntityIds, sanitizeId(suffix));
        entity.kind = "decoration";
        entity.sourceNodeName = sourceNode;
        metadata.entities.push_back(std::move(entity));
        return;
    }

    if (startsWithInsensitive(lowerNode, "light_"))
    {
        const std::string suffix = stripPrefix(sourceNode, "LIGHT_");
        EditorIndoorGeometryLightMetadata light = {};
        light.id = makeUniqueId(seenLightIds, sanitizeId(suffix));
        light.sourceNodeName = sourceNode;
        metadata.lights.push_back(std::move(light));
        return;
    }

    if (startsWithInsensitive(lowerNode, "spawn_"))
    {
        const std::string suffix = stripPrefix(sourceNode, "SPAWN_");
        EditorIndoorGeometrySpawnMetadata spawn = {};
        spawn.id = makeUniqueId(seenSpawnIds, sanitizeId(suffix));
        spawn.sourceNodeName = sourceNode;
        metadata.spawns.push_back(std::move(spawn));
        return;
    }

    ++result.unclassifiedMeshCount;
    result.warnings.push_back("Unclassified indoor source mesh/node: " + sourceNode);
}
}

bool importIndoorSourceGeometryMetadataFromModel(
    const std::filesystem::path &sourcePath,
    const std::string &mapFileName,
    IndoorSourceGeometryImportResult &result,
    std::string &errorMessage)
{
    result = {};
    const std::filesystem::path absoluteSourcePath = std::filesystem::absolute(sourcePath);
    std::vector<ImportedModel> models;

    if (!loadImportedModelsFromFile(absoluteSourcePath, models, errorMessage, false))
    {
        return false;
    }

    result.importedMeshCount = models.size();
    result.metadata.version = 2;
    result.metadata.mapFileName = mapFileName;
    result.metadata.source.assetPath = absoluteSourcePath.string();
    result.metadata.source.coordinateSystem = "blender_z_up";
    result.metadata.source.unitScale = 128.0f;
    result.metadata.importSettings.sourceFormat = extensionWithoutDot(absoluteSourcePath);
    result.metadata.importSettings.mergeVerticesEpsilon = 0.01f;
    result.metadata.importSettings.triangulateNgons = true;
    result.metadata.importSettings.generateBsp = true;
    result.metadata.importSettings.generateOutlines = true;
    result.metadata.importSettings.generatePortals = true;

    appendMaterials(models, result.metadata);

    std::unordered_set<std::string> seenRoomIds;
    std::unordered_set<std::string> seenPortalIds;
    std::unordered_set<std::string> seenSurfaceIds;
    std::unordered_set<std::string> seenMechanismIds;
    std::unordered_set<std::string> seenEntityIds;
    std::unordered_set<std::string> seenLightIds;
    std::unordered_set<std::string> seenSpawnIds;

    for (const ImportedModel &model : models)
    {
        appendImportedModelMetadata(
            model,
            result.metadata,
            result,
            seenRoomIds,
            seenPortalIds,
            seenSurfaceIds,
            seenMechanismIds,
            seenEntityIds,
            seenLightIds,
            seenSpawnIds);
    }

    normalizeIndoorGeometryMetadata(result.metadata, mapFileName);
    return true;
}
}
