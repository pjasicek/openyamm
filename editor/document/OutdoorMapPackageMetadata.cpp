#include "editor/document/OutdoorMapPackageMetadata.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iomanip>
#include <sstream>

namespace OpenYAMM::Editor
{
namespace
{
std::optional<std::string> requireScalarString(
    const YAML::Node &node,
    const char *pKey,
    std::string &errorMessage)
{
    const YAML::Node value = node[pKey];

    if (!value || !value.IsScalar())
    {
        errorMessage = std::string("field must be a scalar: ") + pKey;
        return std::nullopt;
    }

    return value.as<std::string>();
}

std::optional<std::string> optionalScalarString(const YAML::Node &node, const char *pKey, std::string &errorMessage)
{
    const YAML::Node value = node[pKey];

    if (!value)
    {
        return std::nullopt;
    }

    if (!value.IsScalar())
    {
        errorMessage = std::string("field must be a scalar: ") + pKey;
        return std::nullopt;
    }

    return value.as<std::string>();
}

std::optional<int> optionalScalarInt(const YAML::Node &node, const char *pKey, std::string &errorMessage)
{
    const YAML::Node value = node[pKey];

    if (!value)
    {
        return std::nullopt;
    }

    if (!value.IsScalar())
    {
        errorMessage = std::string("field must be a scalar: ") + pKey;
        return std::nullopt;
    }

    try
    {
        return value.as<int>();
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = exception.what();
        return std::nullopt;
    }
}

std::optional<bool> optionalScalarBool(const YAML::Node &node, const char *pKey, std::string &errorMessage)
{
    const YAML::Node value = node[pKey];

    if (!value)
    {
        return std::nullopt;
    }

    if (!value.IsScalar())
    {
        errorMessage = std::string("field must be a scalar: ") + pKey;
        return std::nullopt;
    }

    try
    {
        return value.as<bool>();
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = exception.what();
        return std::nullopt;
    }
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;
    std::transform(result.begin(), result.end(), result.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return result;
}

void fnv1aAppend(uint64_t &hash, const std::string &text)
{
    for (unsigned char character : text)
    {
        hash ^= character;
        hash *= 1099511628211ull;
    }
}

void emitMapBounds(YAML::Emitter &emitter, const Game::MapBounds &bounds)
{
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "enabled" << YAML::Value << bounds.enabled;
    emitter << YAML::Key << "min_x" << YAML::Value << bounds.minX;
    emitter << YAML::Key << "max_x" << YAML::Value << bounds.maxX;
    emitter << YAML::Key << "min_y" << YAML::Value << bounds.minY;
    emitter << YAML::Key << "max_y" << YAML::Value << bounds.maxY;
    emitter << YAML::EndMap;
}

void emitMapEdgeTransition(YAML::Emitter &emitter, const Game::MapEdgeTransition &transition)
{
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "map_file" << YAML::Value << transition.destinationMapFileName;
    emitter << YAML::Key << "travel_days" << YAML::Value << transition.travelDays;

    if (transition.directionDegrees.has_value())
    {
        emitter << YAML::Key << "heading_degrees" << YAML::Value << *transition.directionDegrees;
    }

    emitter << YAML::Key << "use_map_start_position" << YAML::Value << transition.useMapStartPosition;

    if (transition.arrivalX.has_value() && transition.arrivalY.has_value() && transition.arrivalZ.has_value())
    {
        emitter << YAML::Key << "arrival" << YAML::Value;
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "x" << YAML::Value << *transition.arrivalX;
        emitter << YAML::Key << "y" << YAML::Value << *transition.arrivalY;
        emitter << YAML::Key << "z" << YAML::Value << *transition.arrivalZ;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndMap;
}

std::optional<Game::MapBounds> optionalMapBounds(const YAML::Node &node, const char *pKey, std::string &errorMessage)
{
    const YAML::Node value = node[pKey];

    if (!value)
    {
        return std::nullopt;
    }

    if (!value.IsMap())
    {
        errorMessage = std::string("field must be a mapping: ") + pKey;
        return std::nullopt;
    }

    Game::MapBounds bounds = {};

    if (const std::optional<bool> enabled = optionalScalarBool(value, "enabled", errorMessage))
    {
        bounds.enabled = *enabled;
    }

    if (const std::optional<int> minX = optionalScalarInt(value, "min_x", errorMessage))
    {
        bounds.minX = *minX;
    }

    if (const std::optional<int> maxX = optionalScalarInt(value, "max_x", errorMessage))
    {
        bounds.maxX = *maxX;
    }

    if (const std::optional<int> minY = optionalScalarInt(value, "min_y", errorMessage))
    {
        bounds.minY = *minY;
    }

    if (const std::optional<int> maxY = optionalScalarInt(value, "max_y", errorMessage))
    {
        bounds.maxY = *maxY;
    }

    return bounds;
}

std::optional<Game::MapEdgeTransition> optionalMapEdgeTransition(
    const YAML::Node &node,
    const char *pKey,
    std::string &errorMessage)
{
    const YAML::Node value = node[pKey];

    if (!value)
    {
        return std::nullopt;
    }

    if (!value.IsMap())
    {
        errorMessage = std::string("field must be a mapping: ") + pKey;
        return std::nullopt;
    }

    const std::optional<std::string> destinationMapFileName = optionalScalarString(value, "map_file", errorMessage);

    if (!destinationMapFileName)
    {
        return std::nullopt;
    }

    Game::MapEdgeTransition transition = {};
    transition.destinationMapFileName = *destinationMapFileName;

    if (const std::optional<int> travelDays = optionalScalarInt(value, "travel_days", errorMessage))
    {
        transition.travelDays = *travelDays;
    }

    if (const std::optional<int> headingDegrees = optionalScalarInt(value, "heading_degrees", errorMessage))
    {
        transition.directionDegrees = *headingDegrees;
    }

    if (const std::optional<bool> useMapStartPosition =
            optionalScalarBool(value, "use_map_start_position", errorMessage))
    {
        transition.useMapStartPosition = *useMapStartPosition;
    }

    const YAML::Node arrival = value["arrival"];

    if (arrival)
    {
        if (!arrival.IsMap())
        {
            errorMessage = std::string("field must be a mapping: ") + pKey + ".arrival";
            return std::nullopt;
        }

        const std::optional<int> arrivalX = optionalScalarInt(arrival, "x", errorMessage);
        const std::optional<int> arrivalY = optionalScalarInt(arrival, "y", errorMessage);
        const std::optional<int> arrivalZ = optionalScalarInt(arrival, "z", errorMessage);

        if (!arrivalX || !arrivalY || !arrivalZ)
        {
            return std::nullopt;
        }

        transition.arrivalX = *arrivalX;
        transition.arrivalY = *arrivalY;
        transition.arrivalZ = *arrivalZ;
        transition.useMapStartPosition = false;
    }

    return transition;
}
}

std::string serializeOutdoorMapPackageSourceFields(const EditorOutdoorMapPackageMetadata &metadata)
{
    YAML::Emitter emitter;
    emitter.SetIndent(2);
    emitter.SetSeqFormat(YAML::Block);
    emitter.SetMapFormat(YAML::Block);

    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << metadata.version;
    emitter << YAML::Key << "kind" << YAML::Value << "outdoor_map_package";
    emitter << YAML::Key << "package_id" << YAML::Value << metadata.packageId;
    emitter << YAML::Key << "display_name" << YAML::Value << metadata.displayName;
    emitter << YAML::Key << "map_file" << YAML::Value << metadata.mapFileName;
    emitter << YAML::Key << "scene_file" << YAML::Value << metadata.sceneFile;
    emitter << YAML::Key << "geometry_metadata_file" << YAML::Value << metadata.geometryMetadataFile;
    emitter << YAML::Key << "terrain_metadata_file" << YAML::Value << metadata.terrainMetadataFile;
    emitter << YAML::Key << "script_module" << YAML::Value << metadata.scriptModule;
    emitter << YAML::Key << "map_stats_id" << YAML::Value << metadata.mapStatsId;
    emitter << YAML::Key << "redbook_track" << YAML::Value << metadata.redbookTrack;
    emitter << YAML::Key << "environment_name" << YAML::Value << metadata.environmentName;
    emitter << YAML::Key << "is_top_level_area" << YAML::Value << metadata.isTopLevelArea;
    emitter << YAML::Key << "outdoor_bounds" << YAML::Value;
    emitMapBounds(emitter, metadata.outdoorBounds);

    if (metadata.northTransition.has_value())
    {
        emitter << YAML::Key << "north_transition" << YAML::Value;
        emitMapEdgeTransition(emitter, *metadata.northTransition);
    }

    if (metadata.southTransition.has_value())
    {
        emitter << YAML::Key << "south_transition" << YAML::Value;
        emitMapEdgeTransition(emitter, *metadata.southTransition);
    }

    if (metadata.eastTransition.has_value())
    {
        emitter << YAML::Key << "east_transition" << YAML::Value;
        emitMapEdgeTransition(emitter, *metadata.eastTransition);
    }

    if (metadata.westTransition.has_value())
    {
        emitter << YAML::Key << "west_transition" << YAML::Value;
        emitMapEdgeTransition(emitter, *metadata.westTransition);
    }

    emitter << YAML::EndMap;
    return emitter.c_str();
}

std::string serializeOutdoorMapPackageMetadata(const EditorOutdoorMapPackageMetadata &metadata)
{
    YAML::Emitter emitter;
    emitter.SetIndent(2);
    emitter.SetSeqFormat(YAML::Block);
    emitter.SetMapFormat(YAML::Block);

    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << metadata.version;
    emitter << YAML::Key << "kind" << YAML::Value << "outdoor_map_package";
    emitter << YAML::Key << "package_id" << YAML::Value << metadata.packageId;
    emitter << YAML::Key << "display_name" << YAML::Value << metadata.displayName;
    emitter << YAML::Key << "map_file" << YAML::Value << metadata.mapFileName;
    emitter << YAML::Key << "scene_file" << YAML::Value << metadata.sceneFile;
    emitter << YAML::Key << "geometry_metadata_file" << YAML::Value << metadata.geometryMetadataFile;
    emitter << YAML::Key << "terrain_metadata_file" << YAML::Value << metadata.terrainMetadataFile;
    emitter << YAML::Key << "script_module" << YAML::Value << metadata.scriptModule;
    emitter << YAML::Key << "map_stats_id" << YAML::Value << metadata.mapStatsId;
    emitter << YAML::Key << "redbook_track" << YAML::Value << metadata.redbookTrack;
    emitter << YAML::Key << "environment_name" << YAML::Value << metadata.environmentName;
    emitter << YAML::Key << "is_top_level_area" << YAML::Value << metadata.isTopLevelArea;
    emitter << YAML::Key << "outdoor_bounds" << YAML::Value;
    emitMapBounds(emitter, metadata.outdoorBounds);

    if (metadata.northTransition.has_value())
    {
        emitter << YAML::Key << "north_transition" << YAML::Value;
        emitMapEdgeTransition(emitter, *metadata.northTransition);
    }

    if (metadata.southTransition.has_value())
    {
        emitter << YAML::Key << "south_transition" << YAML::Value;
        emitMapEdgeTransition(emitter, *metadata.southTransition);
    }

    if (metadata.eastTransition.has_value())
    {
        emitter << YAML::Key << "east_transition" << YAML::Value;
        emitMapEdgeTransition(emitter, *metadata.eastTransition);
    }

    if (metadata.westTransition.has_value())
    {
        emitter << YAML::Key << "west_transition" << YAML::Value;
        emitMapEdgeTransition(emitter, *metadata.westTransition);
    }

    emitter << YAML::Key << "source_fingerprint" << YAML::Value << metadata.sourceFingerprint;
    emitter << YAML::Key << "built_source_fingerprint" << YAML::Value << metadata.builtSourceFingerprint;
    emitter << YAML::EndMap;
    return emitter.c_str();
}

std::optional<EditorOutdoorMapPackageMetadata> loadOutdoorMapPackageMetadataFromText(
    const std::string &yamlText,
    std::string &errorMessage)
{
    YAML::Node root;

    try
    {
        root = YAML::Load(yamlText);
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = exception.what();
        return std::nullopt;
    }

    if (!root || !root.IsMap())
    {
        errorMessage = "outdoor map package root must be a mapping";
        return std::nullopt;
    }

    EditorOutdoorMapPackageMetadata metadata = {};

    if (const YAML::Node formatVersion = root["format_version"]; formatVersion && formatVersion.IsScalar())
    {
        metadata.version = formatVersion.as<uint32_t>();
    }

    const std::optional<std::string> kind = requireScalarString(root, "kind", errorMessage);

    if (!kind)
    {
        return std::nullopt;
    }

    if (*kind != "outdoor_map_package")
    {
        errorMessage = "unexpected outdoor map package kind: " + *kind;
        return std::nullopt;
    }

    const std::optional<std::string> packageId = optionalScalarString(root, "package_id", errorMessage);
    const std::optional<std::string> displayName = optionalScalarString(root, "display_name", errorMessage);
    const std::optional<std::string> mapFileName = requireScalarString(root, "map_file", errorMessage);
    const std::optional<std::string> sceneFile = requireScalarString(root, "scene_file", errorMessage);
    const std::optional<std::string> geometryMetadataFile =
        requireScalarString(root, "geometry_metadata_file", errorMessage);
    const std::optional<std::string> terrainMetadataFile =
        requireScalarString(root, "terrain_metadata_file", errorMessage);
    const std::optional<std::string> scriptModule =
        optionalScalarString(root, "script_module", errorMessage);
    const std::optional<int> mapStatsId = optionalScalarInt(root, "map_stats_id", errorMessage);
    const std::optional<int> redbookTrack = optionalScalarInt(root, "redbook_track", errorMessage);
    const std::optional<std::string> environmentName =
        optionalScalarString(root, "environment_name", errorMessage);
    const std::optional<bool> isTopLevelArea = optionalScalarBool(root, "is_top_level_area", errorMessage);
    const std::optional<Game::MapBounds> outdoorBounds = optionalMapBounds(root, "outdoor_bounds", errorMessage);
    const std::optional<Game::MapEdgeTransition> northTransition =
        optionalMapEdgeTransition(root, "north_transition", errorMessage);
    const std::optional<Game::MapEdgeTransition> southTransition =
        optionalMapEdgeTransition(root, "south_transition", errorMessage);
    const std::optional<Game::MapEdgeTransition> eastTransition =
        optionalMapEdgeTransition(root, "east_transition", errorMessage);
    const std::optional<Game::MapEdgeTransition> westTransition =
        optionalMapEdgeTransition(root, "west_transition", errorMessage);
    const std::optional<std::string> sourceFingerprint =
        optionalScalarString(root, "source_fingerprint", errorMessage);
    const std::optional<std::string> builtSourceFingerprint =
        optionalScalarString(root, "built_source_fingerprint", errorMessage);

    if (!mapFileName || !sceneFile || !geometryMetadataFile || !terrainMetadataFile)
    {
        return std::nullopt;
    }

    metadata.mapFileName = *mapFileName;
    metadata.sceneFile = *sceneFile;
    metadata.geometryMetadataFile = *geometryMetadataFile;
    metadata.terrainMetadataFile = *terrainMetadataFile;
    metadata.scriptModule = scriptModule.value_or(std::string());
    metadata.mapStatsId = mapStatsId.value_or(0);
    metadata.redbookTrack = redbookTrack.value_or(0);
    metadata.environmentName = environmentName.value_or(std::string());
    metadata.isTopLevelArea = isTopLevelArea.value_or(true);
    metadata.outdoorBounds = outdoorBounds.value_or(Game::MapBounds());
    metadata.northTransition = northTransition;
    metadata.southTransition = southTransition;
    metadata.eastTransition = eastTransition;
    metadata.westTransition = westTransition;
    metadata.packageId = packageId.value_or(std::string());
    metadata.displayName = displayName.value_or(std::string());
    metadata.sourceFingerprint = sourceFingerprint.value_or(std::string());
    metadata.builtSourceFingerprint = builtSourceFingerprint.value_or(std::string());
    return metadata;
}

std::string deriveOutdoorMapPackageId(const std::string &mapFileName)
{
    return toLowerCopy(std::filesystem::path(mapFileName).stem().string());
}

std::string deriveOutdoorMapPackageDisplayName(const std::string &mapFileName)
{
    return std::filesystem::path(mapFileName).stem().string();
}

std::string computeOutdoorMapPackageSourceFingerprint(
    const std::string &sceneText,
    const std::string &geometryMetadataText,
    const std::string &terrainMetadataText,
    const std::string &packageSourceText)
{
    uint64_t hash = 14695981039346656037ull;
    fnv1aAppend(hash, "scene:");
    fnv1aAppend(hash, sceneText);
    fnv1aAppend(hash, "|geometry:");
    fnv1aAppend(hash, geometryMetadataText);
    fnv1aAppend(hash, "|terrain:");
    fnv1aAppend(hash, terrainMetadataText);
    fnv1aAppend(hash, "|package:");
    fnv1aAppend(hash, packageSourceText);

    std::ostringstream stream;
    stream << std::uppercase << std::hex << std::setw(16) << std::setfill('0') << hash;
    return stream.str();
}

void normalizeOutdoorMapPackageMetadata(
    EditorOutdoorMapPackageMetadata &metadata,
    const std::string &packageId,
    const std::string &displayName,
    const std::string &mapFileName,
    const std::string &sceneFile,
    const std::string &geometryMetadataFile,
    const std::string &terrainMetadataFile,
    const std::string &scriptModule,
    const std::string &sourceFingerprint,
    const std::string &builtSourceFingerprint)
{
    metadata.version = 1;

    if (metadata.packageId.empty())
    {
        metadata.packageId = packageId;
    }

    if (metadata.displayName.empty())
    {
        metadata.displayName = displayName;
    }

    if (metadata.mapFileName.empty())
    {
        metadata.mapFileName = mapFileName;
    }

    if (metadata.sceneFile.empty())
    {
        metadata.sceneFile = sceneFile;
    }

    if (metadata.geometryMetadataFile.empty())
    {
        metadata.geometryMetadataFile = geometryMetadataFile;
    }

    if (metadata.terrainMetadataFile.empty())
    {
        metadata.terrainMetadataFile = terrainMetadataFile;
    }

    if (metadata.scriptModule.empty())
    {
        metadata.scriptModule = scriptModule;
    }

    if (metadata.environmentName.empty())
    {
        metadata.environmentName = "FOREST";
    }

    if (!metadata.outdoorBounds.enabled)
    {
        metadata.outdoorBounds.enabled = true;
        metadata.outdoorBounds.minX = -23143;
        metadata.outdoorBounds.maxX = 23143;
        metadata.outdoorBounds.minY = -23143;
        metadata.outdoorBounds.maxY = 23143;
    }

    if (metadata.redbookTrack <= 0)
    {
        metadata.redbookTrack = 4;
    }

    if (metadata.sourceFingerprint.empty())
    {
        metadata.sourceFingerprint = sourceFingerprint;
    }

    if (metadata.builtSourceFingerprint.empty())
    {
        metadata.builtSourceFingerprint = builtSourceFingerprint;
    }
}

}
