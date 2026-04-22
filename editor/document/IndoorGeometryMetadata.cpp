#include "editor/document/IndoorGeometryMetadata.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
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

template <typename ValueType>
bool readScalarNode(
    const YAML::Node &node,
    const char *pKey,
    ValueType &value,
    std::string &errorMessage)
{
    const YAML::Node childNode = node[pKey];

    if (!childNode)
    {
        return true;
    }

    try
    {
        value = childNode.as<ValueType>();
        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

bool readStringSequenceNode(
    const YAML::Node &node,
    const char *pKey,
    std::vector<std::string> &values,
    std::string &errorMessage)
{
    const YAML::Node childNode = node[pKey];

    if (!childNode)
    {
        return true;
    }

    if (!childNode.IsSequence())
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': expected sequence";
        return false;
    }

    try
    {
        values.clear();
        values.reserve(childNode.size());

        for (const YAML::Node &valueNode : childNode)
        {
            values.push_back(valueNode.as<std::string>());
        }

        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

bool readSizeSequenceNode(
    const YAML::Node &node,
    const char *pKey,
    std::vector<size_t> &values,
    std::string &errorMessage)
{
    const YAML::Node childNode = node[pKey];

    if (!childNode)
    {
        return true;
    }

    if (!childNode.IsSequence())
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': expected sequence";
        return false;
    }

    try
    {
        values.clear();
        values.reserve(childNode.size());

        for (const YAML::Node &valueNode : childNode)
        {
            values.push_back(valueNode.as<size_t>());
        }

        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

bool readOptionalSizeNode(
    const YAML::Node &node,
    const char *pKey,
    std::optional<size_t> &value,
    std::string &errorMessage)
{
    const YAML::Node childNode = node[pKey];

    if (!childNode)
    {
        return true;
    }

    try
    {
        value = childNode.as<size_t>();
        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

bool readOptionalFloatNode(
    const YAML::Node &node,
    const char *pKey,
    std::optional<float> &value,
    std::string &errorMessage)
{
    const YAML::Node childNode = node[pKey];

    if (!childNode)
    {
        return true;
    }

    try
    {
        value = childNode.as<float>();
        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

bool readOptionalUInt32Node(
    const YAML::Node &node,
    const char *pKey,
    std::optional<uint32_t> &value,
    std::string &errorMessage)
{
    const YAML::Node childNode = node[pKey];

    if (!childNode)
    {
        return true;
    }

    try
    {
        value = childNode.as<uint32_t>();
        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

bool readOptionalFloatArrayNode(
    const YAML::Node &node,
    const char *pKey,
    std::optional<std::array<float, 3>> &value,
    std::string &errorMessage)
{
    const YAML::Node childNode = node[pKey];

    if (!childNode)
    {
        return true;
    }

    if (!childNode.IsSequence() || childNode.size() != 3)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey
            + "': expected 3-element sequence";
        return false;
    }

    try
    {
        value = {childNode[0].as<float>(), childNode[1].as<float>(), childNode[2].as<float>()};
        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

bool readColorArrayNode(
    const YAML::Node &node,
    const char *pKey,
    std::array<uint8_t, 3> &value,
    std::string &errorMessage)
{
    const YAML::Node childNode = node[pKey];

    if (!childNode)
    {
        return true;
    }

    if (!childNode.IsSequence() || childNode.size() != 3)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey
            + "': expected 3-element sequence";
        return false;
    }

    try
    {
        for (size_t index = 0; index < value.size(); ++index)
        {
            const int channel = childNode[index].as<int>();

            if (channel < 0 || channel > 255)
            {
                errorMessage = std::string("invalid indoor geometry metadata field '") + pKey
                    + "': color channels must be 0..255";
                return false;
            }

            value[index] = static_cast<uint8_t>(channel);
        }

        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("invalid indoor geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

void emitStringSequence(YAML::Emitter &emitter, const std::vector<std::string> &values)
{
    emitter << YAML::Flow << YAML::BeginSeq;

    for (const std::string &value : values)
    {
        emitter << value;
    }

    emitter << YAML::EndSeq;
}

void emitSizeSequence(YAML::Emitter &emitter, const std::vector<size_t> &values)
{
    emitter << YAML::Flow << YAML::BeginSeq;

    for (size_t value : values)
    {
        emitter << value;
    }

    emitter << YAML::EndSeq;
}

void emitFloatArray(YAML::Emitter &emitter, const std::array<float, 3> &values)
{
    emitter << YAML::Flow << YAML::BeginSeq << values[0] << values[1] << values[2] << YAML::EndSeq;
}

void emitColorArray(YAML::Emitter &emitter, const std::array<uint8_t, 3> &values)
{
    emitter << YAML::Flow << YAML::BeginSeq
            << static_cast<int>(values[0])
            << static_cast<int>(values[1])
            << static_cast<int>(values[2])
            << YAML::EndSeq;
}

void normalizeStringList(std::vector<std::string> &values)
{
    for (std::string &value : values)
    {
        value = trimCopy(value);
    }

    values.erase(
        std::remove_if(values.begin(), values.end(), [](const std::string &value)
        {
            return value.empty();
        }),
        values.end());
}

bool isFiniteVector(const std::array<float, 3> &values)
{
    return std::isfinite(values[0]) && std::isfinite(values[1]) && std::isfinite(values[2]);
}

bool hasDuplicateValue(const std::vector<size_t> &values)
{
    std::unordered_set<size_t> seenValues;

    for (size_t value : values)
    {
        if (!seenValues.insert(value).second)
        {
            return true;
        }
    }

    return false;
}
}

std::string serializeIndoorGeometryMetadata(const EditorIndoorGeometryMetadata &metadata)
{
    YAML::Emitter emitter;
    emitter.SetIndent(2);
    emitter.SetSeqFormat(YAML::Block);
    emitter.SetMapFormat(YAML::Block);

    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << metadata.version;
    emitter << YAML::Key << "kind" << YAML::Value << "indoor_geometry";
    emitter << YAML::Key << "map_file" << YAML::Value << metadata.mapFileName;

    emitter << YAML::Key << "source" << YAML::Value << YAML::BeginMap;

    if (!metadata.source.authoringFile.empty())
    {
        emitter << YAML::Key << "authoring_file" << YAML::Value << metadata.source.authoringFile;
    }

    emitter << YAML::Key << "asset_path" << YAML::Value << metadata.source.assetPath;

    if (!metadata.source.rootNodeName.empty())
    {
        emitter << YAML::Key << "root_node" << YAML::Value << metadata.source.rootNodeName;
    }

    emitter << YAML::Key << "coordinate_system" << YAML::Value << metadata.source.coordinateSystem;
    emitter << YAML::Key << "unit_scale" << YAML::Value << metadata.source.unitScale;

    emitter << YAML::Key << "import" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "source_format" << YAML::Value << metadata.importSettings.sourceFormat;
    emitter << YAML::Key << "merge_vertices_epsilon" << YAML::Value << metadata.importSettings.mergeVerticesEpsilon;
    emitter << YAML::Key << "triangulate_ngons" << YAML::Value << metadata.importSettings.triangulateNgons;
    emitter << YAML::Key << "generate_bsp" << YAML::Value << metadata.importSettings.generateBsp;
    emitter << YAML::Key << "generate_outlines" << YAML::Value << metadata.importSettings.generateOutlines;
    emitter << YAML::Key << "generate_portals" << YAML::Value << metadata.importSettings.generatePortals;
    emitter << YAML::EndMap;

    emitter << YAML::EndMap;

    emitter << YAML::Key << "materials" << YAML::Value << YAML::BeginSeq;

    for (const EditorIndoorGeometryMaterialMetadata &material : metadata.materials)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "id" << YAML::Value << material.id;
        emitter << YAML::Key << "source_material" << YAML::Value << material.sourceMaterial;
        emitter << YAML::Key << "texture" << YAML::Value << material.texture;

        if (!material.flags.empty())
        {
            emitter << YAML::Key << "flags" << YAML::Value;
            emitStringSequence(emitter, material.flags);
        }

        if (!material.facetType.empty())
        {
            emitter << YAML::Key << "facet_type" << YAML::Value << material.facetType;
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;

    emitter << YAML::Key << "rooms" << YAML::Value << YAML::BeginSeq;

    for (const EditorIndoorGeometryRoomMetadata &room : metadata.rooms)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "id" << YAML::Value << (room.id.empty() ? std::to_string(room.roomId) : room.id);
        emitter << YAML::Key << "name" << YAML::Value << room.name;

        if (!room.sourceNodeNames.empty())
        {
            emitter << YAML::Key << "source_nodes" << YAML::Value;
            emitStringSequence(emitter, room.sourceNodeNames);
        }

        if (room.runtimeSectorIndex)
        {
            emitter << YAML::Key << "runtime_sector_index" << YAML::Value << *room.runtimeSectorIndex;
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "portals" << YAML::Value << YAML::BeginSeq;

    for (const EditorIndoorGeometryPortalMetadata &portal : metadata.portals)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "id" << YAML::Value
                << (portal.id.empty() ? std::to_string(portal.portalId) : portal.id);
        emitter << YAML::Key << "name" << YAML::Value << portal.name;
        emitter << YAML::Key << "front_room" << YAML::Value
                << (portal.frontRoom.empty() ? std::to_string(portal.frontRoomId) : portal.frontRoom);
        emitter << YAML::Key << "back_room" << YAML::Value
                << (portal.backRoom.empty() ? std::to_string(portal.backRoomId) : portal.backRoom);

        if (!portal.sourceNodeName.empty())
        {
            emitter << YAML::Key << "source_node" << YAML::Value << portal.sourceNodeName;
        }

        if (portal.runtimeFaceIndex)
        {
            emitter << YAML::Key << "runtime_face_index" << YAML::Value << *portal.runtimeFaceIndex;
        }

        if (!portal.flags.empty())
        {
            emitter << YAML::Key << "flags" << YAML::Value;
            emitStringSequence(emitter, portal.flags);
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "surfaces" << YAML::Value << YAML::BeginSeq;

    for (const EditorIndoorGeometrySurfaceMetadata &surface : metadata.surfaces)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "id" << YAML::Value << surface.id;
        emitter << YAML::Key << "source_node" << YAML::Value << surface.sourceNodeName;

        if (!surface.materialId.empty())
        {
            emitter << YAML::Key << "material" << YAML::Value << surface.materialId;
        }

        if (!surface.flags.empty())
        {
            emitter << YAML::Key << "flags" << YAML::Value;
            emitStringSequence(emitter, surface.flags);
        }

        if (surface.trigger)
        {
            emitter << YAML::Key << "trigger" << YAML::Value << YAML::BeginMap;
            emitter << YAML::Key << "event_id" << YAML::Value << surface.trigger->eventId;
            emitter << YAML::Key << "type" << YAML::Value << surface.trigger->type;
            emitter << YAML::EndMap;
        }

        if (surface.runtimeFaceIndex)
        {
            emitter << YAML::Key << "runtime_face_index" << YAML::Value << *surface.runtimeFaceIndex;
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "mechanisms" << YAML::Value << YAML::BeginSeq;

    for (const EditorIndoorGeometryMechanismMetadata &mechanism : metadata.mechanisms)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "id" << YAML::Value
                << (mechanism.id.empty() ? std::to_string(mechanism.mechanismId) : mechanism.id);
        emitter << YAML::Key << "name" << YAML::Value << mechanism.name;

        if (!mechanism.kind.empty())
        {
            emitter << YAML::Key << "kind" << YAML::Value << mechanism.kind;
        }

        if (!mechanism.sourceNodeNames.empty())
        {
            emitter << YAML::Key << "source_nodes" << YAML::Value;
            emitStringSequence(emitter, mechanism.sourceNodeNames);
        }

        if (!mechanism.triggerSurfaceIds.empty())
        {
            emitter << YAML::Key << "trigger_surfaces" << YAML::Value;
            emitStringSequence(emitter, mechanism.triggerSurfaceIds);
        }

        if (mechanism.runtimeDoorIndex)
        {
            emitter << YAML::Key << "runtime_door_index" << YAML::Value << *mechanism.runtimeDoorIndex;
        }

        if (mechanism.doorId
            || !mechanism.initialState.empty()
            || mechanism.moveAxis
            || mechanism.moveLength
            || mechanism.moveDistance
            || mechanism.openSpeed
            || mechanism.closeSpeed)
        {
            emitter << YAML::Key << "door" << YAML::Value << YAML::BeginMap;

            if (mechanism.doorId)
            {
                emitter << YAML::Key << "door_id" << YAML::Value << *mechanism.doorId;
            }

            if (!mechanism.initialState.empty())
            {
                emitter << YAML::Key << "initial_state" << YAML::Value << mechanism.initialState;
            }

            if (mechanism.moveAxis)
            {
                emitter << YAML::Key << "direction" << YAML::Value;
                emitFloatArray(emitter, *mechanism.moveAxis);
            }

            if (mechanism.moveLength)
            {
                emitter << YAML::Key << "move_length" << YAML::Value << *mechanism.moveLength;
            }
            else if (mechanism.moveDistance)
            {
                emitter << YAML::Key << "move_length" << YAML::Value << *mechanism.moveDistance;
            }

            if (mechanism.openSpeed)
            {
                emitter << YAML::Key << "open_speed" << YAML::Value << *mechanism.openSpeed;
            }

            if (mechanism.closeSpeed)
            {
                emitter << YAML::Key << "close_speed" << YAML::Value << *mechanism.closeSpeed;
            }

            emitter << YAML::EndMap;
        }

        if (!mechanism.affectedFaceIndices.empty())
        {
            emitter << YAML::Key << "affected_face_indices" << YAML::Value;
            emitSizeSequence(emitter, mechanism.affectedFaceIndices);
        }

        if (!mechanism.affectedVertexIndices.empty())
        {
            emitter << YAML::Key << "affected_vertex_indices" << YAML::Value;
            emitSizeSequence(emitter, mechanism.affectedVertexIndices);
        }

        if (!mechanism.triggerFaceIndices.empty())
        {
            emitter << YAML::Key << "trigger_face_indices" << YAML::Value;
            emitSizeSequence(emitter, mechanism.triggerFaceIndices);
        }

        if (mechanism.moveAxis)
        {
            emitter << YAML::Key << "move_axis" << YAML::Value;
            emitFloatArray(emitter, *mechanism.moveAxis);
        }

        if (mechanism.moveDistance)
        {
            emitter << YAML::Key << "move_distance" << YAML::Value << *mechanism.moveDistance;
        }

        if (mechanism.openSpeed)
        {
            emitter << YAML::Key << "open_speed" << YAML::Value << *mechanism.openSpeed;
        }

        if (mechanism.closeSpeed)
        {
            emitter << YAML::Key << "close_speed" << YAML::Value << *mechanism.closeSpeed;
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "entities" << YAML::Value << YAML::BeginSeq;

    for (const EditorIndoorGeometryEntityMetadata &entity : metadata.entities)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "id" << YAML::Value << entity.id;
        emitter << YAML::Key << "kind" << YAML::Value << entity.kind;
        emitter << YAML::Key << "source_node" << YAML::Value << entity.sourceNodeName;
        emitter << YAML::Key << "decoration_list_id" << YAML::Value << entity.decorationListId;
        emitter << YAML::Key << "event_id_primary" << YAML::Value << entity.eventIdPrimary;
        emitter << YAML::Key << "event_id_secondary" << YAML::Value << entity.eventIdSecondary;

        if (entity.runtimeEntityIndex)
        {
            emitter << YAML::Key << "runtime_entity_index" << YAML::Value << *entity.runtimeEntityIndex;
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "lights" << YAML::Value << YAML::BeginSeq;

    for (const EditorIndoorGeometryLightMetadata &light : metadata.lights)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "id" << YAML::Value << light.id;
        emitter << YAML::Key << "source_node" << YAML::Value << light.sourceNodeName;
        emitter << YAML::Key << "color" << YAML::Value;
        emitColorArray(emitter, light.color);
        emitter << YAML::Key << "radius" << YAML::Value << light.radius;
        emitter << YAML::Key << "brightness" << YAML::Value << light.brightness;
        emitter << YAML::Key << "type" << YAML::Value << light.type;

        if (light.runtimeLightIndex)
        {
            emitter << YAML::Key << "runtime_light_index" << YAML::Value << *light.runtimeLightIndex;
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "spawns" << YAML::Value << YAML::BeginSeq;

    for (const EditorIndoorGeometrySpawnMetadata &spawn : metadata.spawns)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "id" << YAML::Value << spawn.id;
        emitter << YAML::Key << "source_node" << YAML::Value << spawn.sourceNodeName;
        emitter << YAML::Key << "type_id" << YAML::Value << spawn.typeId;
        emitter << YAML::Key << "index" << YAML::Value << spawn.index;
        emitter << YAML::Key << "radius" << YAML::Value << spawn.radius;
        emitter << YAML::Key << "group" << YAML::Value << spawn.group;

        if (spawn.runtimeSpawnIndex)
        {
            emitter << YAML::Key << "runtime_spawn_index" << YAML::Value << *spawn.runtimeSpawnIndex;
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;

    std::string text = emitter.c_str();

    if (!text.empty() && text.back() != '\n')
    {
        text.push_back('\n');
    }

    return text;
}

std::optional<EditorIndoorGeometryMetadata> loadIndoorGeometryMetadataFromText(
    const std::string &yamlText,
    std::string &errorMessage)
{
    EditorIndoorGeometryMetadata metadata = {};
    YAML::Node rootNode;

    try
    {
        rootNode = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse indoor geometry metadata yaml: ") + exception.what();
        return std::nullopt;
    }

    if (!rootNode || !rootNode.IsMap())
    {
        errorMessage = "indoor geometry metadata root must be a map";
        return std::nullopt;
    }

    std::string kind;

    if (!readScalarNode(rootNode, "format_version", metadata.version, errorMessage)
        || !readScalarNode(rootNode, "version", metadata.version, errorMessage)
        || !readScalarNode(rootNode, "kind", kind, errorMessage)
        || !readScalarNode(rootNode, "map_file", metadata.mapFileName, errorMessage))
    {
        return std::nullopt;
    }

    if (!kind.empty() && kind != "indoor_geometry")
    {
        errorMessage = "geometry metadata kind must be indoor_geometry";
        return std::nullopt;
    }

    const YAML::Node sourceNode = rootNode["source"];

    if (sourceNode)
    {
        if (!sourceNode.IsMap())
        {
            errorMessage = "indoor geometry metadata source must be a map";
            return std::nullopt;
        }

        float legacyScale = 0.0f;

        if (!readScalarNode(sourceNode, "authoring_file", metadata.source.authoringFile, errorMessage)
            || !readScalarNode(sourceNode, "asset_path", metadata.source.assetPath, errorMessage)
            || !readScalarNode(sourceNode, "root_node", metadata.source.rootNodeName, errorMessage)
            || !readScalarNode(sourceNode, "unit_scale", metadata.source.unitScale, errorMessage)
            || !readScalarNode(sourceNode, "scale", legacyScale, errorMessage)
            || !readScalarNode(sourceNode, "coordinate_system", metadata.source.coordinateSystem, errorMessage))
        {
            return std::nullopt;
        }

        if (!sourceNode["unit_scale"] && legacyScale > 0.0f)
        {
            metadata.source.unitScale = legacyScale;
        }

        const YAML::Node importNode = sourceNode["import"];

        if (importNode)
        {
            if (!importNode.IsMap())
            {
                errorMessage = "indoor geometry metadata source.import must be a map";
                return std::nullopt;
            }

            if (!readScalarNode(importNode, "source_format", metadata.importSettings.sourceFormat, errorMessage)
                || !readScalarNode(
                    importNode,
                    "merge_vertices_epsilon",
                    metadata.importSettings.mergeVerticesEpsilon,
                    errorMessage)
                || !readScalarNode(
                    importNode,
                    "triangulate_ngons",
                    metadata.importSettings.triangulateNgons,
                    errorMessage)
                || !readScalarNode(importNode, "generate_bsp", metadata.importSettings.generateBsp, errorMessage)
                || !readScalarNode(
                    importNode,
                    "generate_outlines",
                    metadata.importSettings.generateOutlines,
                    errorMessage)
                || !readScalarNode(
                    importNode,
                    "generate_portals",
                    metadata.importSettings.generatePortals,
                    errorMessage))
            {
                return std::nullopt;
            }
        }
    }

    const YAML::Node materialsNode = rootNode["materials"];

    if (materialsNode)
    {
        if (!materialsNode.IsSequence())
        {
            errorMessage = "indoor geometry metadata materials must be a sequence";
            return std::nullopt;
        }

        metadata.materials.reserve(materialsNode.size());

        for (const YAML::Node &materialNode : materialsNode)
        {
            if (!materialNode.IsMap())
            {
                errorMessage = "indoor geometry metadata material entry must be a map";
                return std::nullopt;
            }

            EditorIndoorGeometryMaterialMetadata material = {};

            if (!readScalarNode(materialNode, "id", material.id, errorMessage)
                || !readScalarNode(materialNode, "source_material", material.sourceMaterial, errorMessage)
                || !readScalarNode(materialNode, "texture", material.texture, errorMessage)
                || !readStringSequenceNode(materialNode, "flags", material.flags, errorMessage)
                || !readScalarNode(materialNode, "facet_type", material.facetType, errorMessage))
            {
                return std::nullopt;
            }

            metadata.materials.push_back(std::move(material));
        }
    }

    const YAML::Node roomsNode = rootNode["rooms"];

    if (roomsNode)
    {
        if (!roomsNode.IsSequence())
        {
            errorMessage = "indoor geometry metadata rooms must be a sequence";
            return std::nullopt;
        }

        metadata.rooms.reserve(roomsNode.size());

        for (const YAML::Node &roomNode : roomsNode)
        {
            if (!roomNode.IsMap())
            {
                errorMessage = "indoor geometry metadata room entry must be a map";
                return std::nullopt;
            }

            EditorIndoorGeometryRoomMetadata room = {};

            if (!readScalarNode(roomNode, "id", room.id, errorMessage)
                || !readScalarNode(roomNode, "room_id", room.roomId, errorMessage)
                || !readScalarNode(roomNode, "name", room.name, errorMessage)
                || !readStringSequenceNode(roomNode, "source_nodes", room.sourceNodeNames, errorMessage)
                || !readOptionalSizeNode(roomNode, "runtime_sector_index", room.runtimeSectorIndex, errorMessage))
            {
                return std::nullopt;
            }

            metadata.rooms.push_back(std::move(room));
        }
    }

    const YAML::Node portalsNode = rootNode["portals"];

    if (portalsNode)
    {
        if (!portalsNode.IsSequence())
        {
            errorMessage = "indoor geometry metadata portals must be a sequence";
            return std::nullopt;
        }

        metadata.portals.reserve(portalsNode.size());

        for (const YAML::Node &portalNode : portalsNode)
        {
            if (!portalNode.IsMap())
            {
                errorMessage = "indoor geometry metadata portal entry must be a map";
                return std::nullopt;
            }

            EditorIndoorGeometryPortalMetadata portal = {};

            if (!readScalarNode(portalNode, "id", portal.id, errorMessage)
                || !readScalarNode(portalNode, "portal_id", portal.portalId, errorMessage)
                || !readScalarNode(portalNode, "name", portal.name, errorMessage)
                || !readScalarNode(portalNode, "front_room", portal.frontRoom, errorMessage)
                || !readScalarNode(portalNode, "back_room", portal.backRoom, errorMessage)
                || !readScalarNode(portalNode, "front_room_id", portal.frontRoomId, errorMessage)
                || !readScalarNode(portalNode, "back_room_id", portal.backRoomId, errorMessage)
                || !readScalarNode(portalNode, "source_node", portal.sourceNodeName, errorMessage)
                || !readStringSequenceNode(portalNode, "flags", portal.flags, errorMessage)
                || !readOptionalSizeNode(portalNode, "runtime_face_index", portal.runtimeFaceIndex, errorMessage))
            {
                return std::nullopt;
            }

            metadata.portals.push_back(std::move(portal));
        }
    }

    const YAML::Node surfacesNode = rootNode["surfaces"];

    if (surfacesNode)
    {
        if (!surfacesNode.IsSequence())
        {
            errorMessage = "indoor geometry metadata surfaces must be a sequence";
            return std::nullopt;
        }

        metadata.surfaces.reserve(surfacesNode.size());

        for (const YAML::Node &surfaceNode : surfacesNode)
        {
            if (!surfaceNode.IsMap())
            {
                errorMessage = "indoor geometry metadata surface entry must be a map";
                return std::nullopt;
            }

            EditorIndoorGeometrySurfaceMetadata surface = {};

            if (!readScalarNode(surfaceNode, "id", surface.id, errorMessage)
                || !readScalarNode(surfaceNode, "source_node", surface.sourceNodeName, errorMessage)
                || !readScalarNode(surfaceNode, "material", surface.materialId, errorMessage)
                || !readStringSequenceNode(surfaceNode, "flags", surface.flags, errorMessage)
                || !readOptionalSizeNode(surfaceNode, "runtime_face_index", surface.runtimeFaceIndex, errorMessage))
            {
                return std::nullopt;
            }

            const YAML::Node triggerNode = surfaceNode["trigger"];

            if (triggerNode)
            {
                if (!triggerNode.IsMap())
                {
                    errorMessage = "indoor geometry metadata surface trigger must be a map";
                    return std::nullopt;
                }

                EditorIndoorGeometrySurfaceTriggerMetadata trigger = {};

                if (!readScalarNode(triggerNode, "event_id", trigger.eventId, errorMessage)
                    || !readScalarNode(triggerNode, "type", trigger.type, errorMessage))
                {
                    return std::nullopt;
                }

                surface.trigger = trigger;
            }

            metadata.surfaces.push_back(std::move(surface));
        }
    }

    const YAML::Node mechanismsNode = rootNode["mechanisms"];

    if (mechanismsNode)
    {
        if (!mechanismsNode.IsSequence())
        {
            errorMessage = "indoor geometry metadata mechanisms must be a sequence";
            return std::nullopt;
        }

        metadata.mechanisms.reserve(mechanismsNode.size());

        for (const YAML::Node &mechanismNode : mechanismsNode)
        {
            if (!mechanismNode.IsMap())
            {
                errorMessage = "indoor geometry metadata mechanism entry must be a map";
                return std::nullopt;
            }

            EditorIndoorGeometryMechanismMetadata mechanism = {};

            if (!readScalarNode(mechanismNode, "id", mechanism.id, errorMessage)
                || !readScalarNode(mechanismNode, "mechanism_id", mechanism.mechanismId, errorMessage)
                || !readScalarNode(mechanismNode, "name", mechanism.name, errorMessage)
                || !readScalarNode(mechanismNode, "kind", mechanism.kind, errorMessage)
                || !readStringSequenceNode(mechanismNode, "source_nodes", mechanism.sourceNodeNames, errorMessage)
                || !readStringSequenceNode(
                    mechanismNode,
                    "moving_nodes",
                    mechanism.sourceNodeNames,
                    errorMessage)
                || !readStringSequenceNode(
                    mechanismNode,
                    "trigger_surfaces",
                    mechanism.triggerSurfaceIds,
                    errorMessage)
                || !readOptionalSizeNode(
                    mechanismNode,
                    "runtime_door_index",
                    mechanism.runtimeDoorIndex,
                    errorMessage)
                || !readSizeSequenceNode(
                    mechanismNode,
                    "affected_face_indices",
                    mechanism.affectedFaceIndices,
                    errorMessage)
                || !readSizeSequenceNode(
                    mechanismNode,
                    "affected_vertex_indices",
                    mechanism.affectedVertexIndices,
                    errorMessage)
                || !readSizeSequenceNode(
                    mechanismNode,
                    "trigger_face_indices",
                    mechanism.triggerFaceIndices,
                    errorMessage)
                || !readOptionalFloatArrayNode(mechanismNode, "move_axis", mechanism.moveAxis, errorMessage)
                || !readOptionalFloatNode(mechanismNode, "move_distance", mechanism.moveDistance, errorMessage)
                || !readOptionalFloatNode(mechanismNode, "open_speed", mechanism.openSpeed, errorMessage)
                || !readOptionalFloatNode(mechanismNode, "close_speed", mechanism.closeSpeed, errorMessage))
            {
                return std::nullopt;
            }

            const YAML::Node doorNode = mechanismNode["door"];

            if (doorNode)
            {
                if (!doorNode.IsMap())
                {
                    errorMessage = "indoor geometry metadata mechanism door must be a map";
                    return std::nullopt;
                }

                if (!readOptionalUInt32Node(doorNode, "door_id", mechanism.doorId, errorMessage)
                    || !readScalarNode(doorNode, "initial_state", mechanism.initialState, errorMessage)
                    || !readOptionalFloatArrayNode(doorNode, "direction", mechanism.moveAxis, errorMessage)
                    || !readOptionalUInt32Node(doorNode, "move_length", mechanism.moveLength, errorMessage)
                    || !readOptionalFloatNode(doorNode, "open_speed", mechanism.openSpeed, errorMessage)
                    || !readOptionalFloatNode(doorNode, "close_speed", mechanism.closeSpeed, errorMessage))
                {
                    return std::nullopt;
                }
            }

            metadata.mechanisms.push_back(std::move(mechanism));
        }
    }

    const YAML::Node entitiesNode = rootNode["entities"];

    if (entitiesNode)
    {
        if (!entitiesNode.IsSequence())
        {
            errorMessage = "indoor geometry metadata entities must be a sequence";
            return std::nullopt;
        }

        metadata.entities.reserve(entitiesNode.size());

        for (const YAML::Node &entityNode : entitiesNode)
        {
            if (!entityNode.IsMap())
            {
                errorMessage = "indoor geometry metadata entity entry must be a map";
                return std::nullopt;
            }

            EditorIndoorGeometryEntityMetadata entity = {};

            if (!readScalarNode(entityNode, "id", entity.id, errorMessage)
                || !readScalarNode(entityNode, "kind", entity.kind, errorMessage)
                || !readScalarNode(entityNode, "source_node", entity.sourceNodeName, errorMessage)
                || !readScalarNode(entityNode, "decoration_list_id", entity.decorationListId, errorMessage)
                || !readScalarNode(entityNode, "event_id_primary", entity.eventIdPrimary, errorMessage)
                || !readScalarNode(entityNode, "event_id_secondary", entity.eventIdSecondary, errorMessage)
                || !readOptionalSizeNode(entityNode, "runtime_entity_index", entity.runtimeEntityIndex, errorMessage))
            {
                return std::nullopt;
            }

            metadata.entities.push_back(std::move(entity));
        }
    }

    const YAML::Node lightsNode = rootNode["lights"];

    if (lightsNode)
    {
        if (!lightsNode.IsSequence())
        {
            errorMessage = "indoor geometry metadata lights must be a sequence";
            return std::nullopt;
        }

        metadata.lights.reserve(lightsNode.size());

        for (const YAML::Node &lightNode : lightsNode)
        {
            if (!lightNode.IsMap())
            {
                errorMessage = "indoor geometry metadata light entry must be a map";
                return std::nullopt;
            }

            EditorIndoorGeometryLightMetadata light = {};

            if (!readScalarNode(lightNode, "id", light.id, errorMessage)
                || !readScalarNode(lightNode, "source_node", light.sourceNodeName, errorMessage)
                || !readColorArrayNode(lightNode, "color", light.color, errorMessage)
                || !readScalarNode(lightNode, "radius", light.radius, errorMessage)
                || !readScalarNode(lightNode, "brightness", light.brightness, errorMessage)
                || !readScalarNode(lightNode, "type", light.type, errorMessage)
                || !readOptionalSizeNode(lightNode, "runtime_light_index", light.runtimeLightIndex, errorMessage))
            {
                return std::nullopt;
            }

            metadata.lights.push_back(std::move(light));
        }
    }

    const YAML::Node spawnsNode = rootNode["spawns"];

    if (spawnsNode)
    {
        if (!spawnsNode.IsSequence())
        {
            errorMessage = "indoor geometry metadata spawns must be a sequence";
            return std::nullopt;
        }

        metadata.spawns.reserve(spawnsNode.size());

        for (const YAML::Node &spawnNode : spawnsNode)
        {
            if (!spawnNode.IsMap())
            {
                errorMessage = "indoor geometry metadata spawn entry must be a map";
                return std::nullopt;
            }

            EditorIndoorGeometrySpawnMetadata spawn = {};

            if (!readScalarNode(spawnNode, "id", spawn.id, errorMessage)
                || !readScalarNode(spawnNode, "source_node", spawn.sourceNodeName, errorMessage)
                || !readScalarNode(spawnNode, "type_id", spawn.typeId, errorMessage)
                || !readScalarNode(spawnNode, "index", spawn.index, errorMessage)
                || !readScalarNode(spawnNode, "radius", spawn.radius, errorMessage)
                || !readScalarNode(spawnNode, "group", spawn.group, errorMessage)
                || !readOptionalSizeNode(spawnNode, "runtime_spawn_index", spawn.runtimeSpawnIndex, errorMessage))
            {
                return std::nullopt;
            }

            metadata.spawns.push_back(std::move(spawn));
        }
    }

    normalizeIndoorGeometryMetadata(metadata, metadata.mapFileName);
    return metadata;
}

void normalizeIndoorGeometryMetadata(EditorIndoorGeometryMetadata &metadata, const std::string &mapFileName)
{
    metadata.version = 2;
    metadata.mapFileName = mapFileName;
    metadata.source.authoringFile = trimCopy(metadata.source.authoringFile);
    metadata.source.assetPath = trimCopy(metadata.source.assetPath);
    metadata.source.rootNodeName = trimCopy(metadata.source.rootNodeName);
    metadata.source.coordinateSystem = trimCopy(metadata.source.coordinateSystem);
    metadata.importSettings.sourceFormat = trimCopy(metadata.importSettings.sourceFormat);

    if (metadata.source.coordinateSystem.empty())
    {
        metadata.source.coordinateSystem = "blender_z_up";
    }

    if (!std::isfinite(metadata.source.unitScale) || metadata.source.unitScale <= 0.0f)
    {
        metadata.source.unitScale = 128.0f;
    }

    if (!std::isfinite(metadata.importSettings.mergeVerticesEpsilon)
        || metadata.importSettings.mergeVerticesEpsilon < 0.0f)
    {
        metadata.importSettings.mergeVerticesEpsilon = 0.01f;
    }

    if (metadata.importSettings.sourceFormat.empty())
    {
        metadata.importSettings.sourceFormat = "glb";
    }

    for (EditorIndoorGeometryMaterialMetadata &material : metadata.materials)
    {
        material.id = trimCopy(material.id);
        material.sourceMaterial = trimCopy(material.sourceMaterial);
        material.texture = trimCopy(material.texture);
        material.facetType = trimCopy(material.facetType);
        normalizeStringList(material.flags);
    }

    for (EditorIndoorGeometryRoomMetadata &room : metadata.rooms)
    {
        room.id = trimCopy(room.id);

        if (room.id.empty() && room.roomId != 0)
        {
            room.id = std::to_string(room.roomId);
        }

        room.name = trimCopy(room.name);
        normalizeStringList(room.sourceNodeNames);
    }

    for (EditorIndoorGeometryPortalMetadata &portal : metadata.portals)
    {
        portal.id = trimCopy(portal.id);

        if (portal.id.empty() && portal.portalId != 0)
        {
            portal.id = std::to_string(portal.portalId);
        }

        portal.name = trimCopy(portal.name);
        portal.frontRoom = trimCopy(portal.frontRoom);
        portal.backRoom = trimCopy(portal.backRoom);
        portal.sourceNodeName = trimCopy(portal.sourceNodeName);
        normalizeStringList(portal.flags);
    }

    for (EditorIndoorGeometrySurfaceMetadata &surface : metadata.surfaces)
    {
        surface.id = trimCopy(surface.id);
        surface.sourceNodeName = trimCopy(surface.sourceNodeName);
        surface.materialId = trimCopy(surface.materialId);
        normalizeStringList(surface.flags);

        if (surface.trigger)
        {
            surface.trigger->type = trimCopy(surface.trigger->type);
        }
    }

    for (EditorIndoorGeometryMechanismMetadata &mechanism : metadata.mechanisms)
    {
        mechanism.id = trimCopy(mechanism.id);

        if (mechanism.id.empty() && mechanism.mechanismId != 0)
        {
            mechanism.id = std::to_string(mechanism.mechanismId);
        }

        mechanism.name = trimCopy(mechanism.name);
        mechanism.kind = trimCopy(mechanism.kind);
        mechanism.initialState = trimCopy(mechanism.initialState);
        normalizeStringList(mechanism.sourceNodeNames);
        normalizeStringList(mechanism.triggerSurfaceIds);

        if (mechanism.moveAxis && !isFiniteVector(*mechanism.moveAxis))
        {
            mechanism.moveAxis = std::nullopt;
        }

        if (mechanism.moveDistance && !std::isfinite(*mechanism.moveDistance))
        {
            mechanism.moveDistance = std::nullopt;
        }

        if (mechanism.openSpeed && !std::isfinite(*mechanism.openSpeed))
        {
            mechanism.openSpeed = std::nullopt;
        }

        if (mechanism.closeSpeed && !std::isfinite(*mechanism.closeSpeed))
        {
            mechanism.closeSpeed = std::nullopt;
        }
    }

    for (EditorIndoorGeometryEntityMetadata &entity : metadata.entities)
    {
        entity.id = trimCopy(entity.id);
        entity.kind = trimCopy(entity.kind);
        entity.sourceNodeName = trimCopy(entity.sourceNodeName);
    }

    for (EditorIndoorGeometryLightMetadata &light : metadata.lights)
    {
        light.id = trimCopy(light.id);
        light.sourceNodeName = trimCopy(light.sourceNodeName);
        light.type = trimCopy(light.type);
    }

    for (EditorIndoorGeometrySpawnMetadata &spawn : metadata.spawns)
    {
        spawn.id = trimCopy(spawn.id);
        spawn.sourceNodeName = trimCopy(spawn.sourceNodeName);
    }
}

bool isIndoorGeometryMetadataEmpty(const EditorIndoorGeometryMetadata &metadata)
{
    return metadata.source.assetPath.empty()
        && metadata.source.authoringFile.empty()
        && metadata.source.rootNodeName.empty()
        && metadata.materials.empty()
        && metadata.rooms.empty()
        && metadata.portals.empty()
        && metadata.surfaces.empty()
        && metadata.mechanisms.empty()
        && metadata.entities.empty()
        && metadata.lights.empty()
        && metadata.spawns.empty();
}

std::vector<std::string> validateIndoorGeometryMetadata(
    const EditorIndoorGeometryMetadata &metadata,
    const Game::IndoorMapData &indoorGeometry)
{
    std::vector<std::string> issues;

    if (metadata.source.unitScale <= 0.0f || !std::isfinite(metadata.source.unitScale))
    {
        issues.push_back("Indoor geometry source unit scale must be greater than zero.");
    }

    if (trimCopy(metadata.source.assetPath).empty())
    {
        issues.push_back("Indoor geometry source asset path is empty.");
    }

    std::unordered_set<std::string> materialIds;

    for (const EditorIndoorGeometryMaterialMetadata &material : metadata.materials)
    {
        if (material.id.empty())
        {
            issues.push_back("Indoor source material has an empty id.");
            continue;
        }

        if (!materialIds.insert(material.id).second)
        {
            issues.push_back("Indoor source material '" + material.id + "' is duplicated.");
        }
    }

    std::unordered_set<std::string> roomIds;

    for (const EditorIndoorGeometryRoomMetadata &room : metadata.rooms)
    {
        const std::string roomId = room.id.empty() ? std::to_string(room.roomId) : room.id;

        if (roomId.empty() || roomId == "0")
        {
            issues.push_back("Indoor source room has an empty id.");
            continue;
        }

        if (!roomIds.insert(roomId).second)
        {
            issues.push_back("Indoor source room '" + roomId + "' is duplicated.");
        }

        if (room.sourceNodeNames.empty())
        {
            issues.push_back("Indoor source room '" + roomId + "' has no source nodes.");
        }

        if (room.runtimeSectorIndex && *room.runtimeSectorIndex >= indoorGeometry.sectors.size())
        {
            issues.push_back("Indoor source room '" + roomId + "' sector index is out of range.");
        }
    }

    std::unordered_set<std::string> portalIds;

    for (const EditorIndoorGeometryPortalMetadata &portal : metadata.portals)
    {
        const std::string portalId = portal.id.empty() ? std::to_string(portal.portalId) : portal.id;
        const std::string frontRoom = portal.frontRoom.empty() ? std::to_string(portal.frontRoomId) : portal.frontRoom;
        const std::string backRoom = portal.backRoom.empty() ? std::to_string(portal.backRoomId) : portal.backRoom;

        if (portalId.empty() || portalId == "0")
        {
            issues.push_back("Indoor source portal has an empty id.");
            continue;
        }

        if (!portalIds.insert(portalId).second)
        {
            issues.push_back("Indoor source portal '" + portalId + "' is duplicated.");
        }

        if (portal.sourceNodeName.empty())
        {
            issues.push_back("Indoor source portal '" + portalId + "' has no source node.");
        }

        if (frontRoom.empty() || frontRoom == "0")
        {
            issues.push_back("Indoor source portal '" + portalId + "' front room is empty.");
        }
        else if (!roomIds.empty() && !roomIds.contains(frontRoom))
        {
            issues.push_back("Indoor source portal '" + portalId + "' front room is unknown.");
        }

        if (backRoom.empty() || backRoom == "0")
        {
            issues.push_back("Indoor source portal '" + portalId + "' back room is empty.");
        }
        else if (!roomIds.empty() && !roomIds.contains(backRoom))
        {
            issues.push_back("Indoor source portal '" + portalId + "' back room is unknown.");
        }

        if (!frontRoom.empty() && frontRoom == backRoom)
        {
            issues.push_back("Indoor source portal '" + portalId + "' connects the same room on both sides.");
        }

        if (portal.runtimeFaceIndex && *portal.runtimeFaceIndex >= indoorGeometry.faces.size())
        {
            issues.push_back(
                "Indoor source portal '" + portalId + "' face index is out of range.");
        }
        else if (portal.runtimeFaceIndex && !indoorGeometry.faces[*portal.runtimeFaceIndex].isPortal)
        {
            issues.push_back(
                "Indoor source portal '" + portalId + "' references a non-portal face.");
        }
    }

    std::unordered_set<std::string> surfaceIds;

    for (const EditorIndoorGeometrySurfaceMetadata &surface : metadata.surfaces)
    {
        if (surface.id.empty())
        {
            issues.push_back("Indoor source surface has an empty id.");
            continue;
        }

        if (!surfaceIds.insert(surface.id).second)
        {
            issues.push_back("Indoor source surface '" + surface.id + "' is duplicated.");
        }

        if (surface.sourceNodeName.empty())
        {
            issues.push_back("Indoor source surface '" + surface.id + "' has no source node.");
        }

        if (!surface.materialId.empty() && !materialIds.empty() && !materialIds.contains(surface.materialId))
        {
            issues.push_back("Indoor source surface '" + surface.id + "' material is unknown.");
        }

        if (surface.trigger && surface.trigger->eventId == 0)
        {
            issues.push_back("Indoor source surface '" + surface.id + "' trigger has no event id.");
        }

        if (surface.runtimeFaceIndex && *surface.runtimeFaceIndex >= indoorGeometry.faces.size())
        {
            issues.push_back("Indoor source surface '" + surface.id + "' face index is out of range.");
        }
    }

    std::unordered_set<std::string> mechanismIds;

    for (const EditorIndoorGeometryMechanismMetadata &mechanism : metadata.mechanisms)
    {
        const std::string mechanismId = mechanism.id.empty() ? std::to_string(mechanism.mechanismId) : mechanism.id;

        if (mechanismId.empty() || mechanismId == "0")
        {
            issues.push_back("Indoor source mechanism has an empty id.");
            continue;
        }

        if (!mechanismIds.insert(mechanismId).second)
        {
            issues.push_back("Indoor source mechanism '" + mechanismId + "' is duplicated.");
        }

        if (mechanism.kind.empty())
        {
            issues.push_back("Indoor source mechanism '" + mechanismId + "' has no kind.");
        }

        if (mechanism.sourceNodeNames.empty())
        {
            issues.push_back("Indoor source mechanism '" + mechanismId + "' has no source nodes.");
        }

        if (mechanism.moveLength.value_or(0) == 0 && mechanism.moveDistance.value_or(0.0f) == 0.0f)
        {
            issues.push_back("Indoor source mechanism '" + mechanismId + "' has no movement distance.");
        }

        if (mechanism.runtimeDoorIndex && *mechanism.runtimeDoorIndex >= indoorGeometry.doorCount)
        {
            issues.push_back(
                "Indoor source mechanism '" + mechanismId + "' door index is out of range.");
        }

        for (const std::string &surfaceId : mechanism.triggerSurfaceIds)
        {
            if (!surfaceIds.empty() && !surfaceIds.contains(surfaceId))
            {
                issues.push_back(
                    "Indoor source mechanism '" + mechanismId + "' trigger surface is unknown.");
                break;
            }
        }

        for (size_t faceIndex : mechanism.affectedFaceIndices)
        {
            if (faceIndex >= indoorGeometry.faces.size())
            {
                issues.push_back(
                    "Indoor source mechanism '" + mechanismId + "'"
                    + " affected face index is out of range.");
                break;
            }
        }

        for (size_t vertexIndex : mechanism.affectedVertexIndices)
        {
            if (vertexIndex >= indoorGeometry.vertices.size())
            {
                issues.push_back(
                    "Indoor source mechanism '" + mechanismId + "'"
                    + " affected vertex index is out of range.");
                break;
            }
        }

        for (size_t faceIndex : mechanism.triggerFaceIndices)
        {
            if (faceIndex >= indoorGeometry.faces.size())
            {
                issues.push_back(
                    "Indoor source mechanism '" + mechanismId + "'"
                    + " trigger face index is out of range.");
                break;
            }
        }

        if (hasDuplicateValue(mechanism.affectedFaceIndices))
        {
            issues.push_back(
                "Indoor source mechanism '" + mechanismId + "'"
                + " has duplicate affected faces.");
        }

        if (hasDuplicateValue(mechanism.affectedVertexIndices))
        {
            issues.push_back(
                "Indoor source mechanism '" + mechanismId + "'"
                + " has duplicate affected vertices.");
        }

        if (hasDuplicateValue(mechanism.triggerFaceIndices))
        {
            issues.push_back(
                "Indoor source mechanism '" + mechanismId + "'"
                + " has duplicate trigger faces.");
        }
    }

    std::unordered_set<std::string> entityIds;

    for (const EditorIndoorGeometryEntityMetadata &entity : metadata.entities)
    {
        if (entity.id.empty())
        {
            issues.push_back("Indoor source entity has an empty id.");
            continue;
        }

        if (!entityIds.insert(entity.id).second)
        {
            issues.push_back("Indoor source entity '" + entity.id + "' is duplicated.");
        }

        if (entity.sourceNodeName.empty())
        {
            issues.push_back("Indoor source entity '" + entity.id + "' has no source node.");
        }

        if (entity.kind == "decoration" && entity.decorationListId == 0)
        {
            issues.push_back("Indoor source entity '" + entity.id + "' decoration list id is not set.");
        }

        if (entity.runtimeEntityIndex && *entity.runtimeEntityIndex >= indoorGeometry.entities.size())
        {
            issues.push_back("Indoor source entity '" + entity.id + "' runtime entity index is out of range.");
        }
    }

    std::unordered_set<std::string> lightIds;

    for (const EditorIndoorGeometryLightMetadata &light : metadata.lights)
    {
        if (light.id.empty())
        {
            issues.push_back("Indoor source light has an empty id.");
            continue;
        }

        if (!lightIds.insert(light.id).second)
        {
            issues.push_back("Indoor source light '" + light.id + "' is duplicated.");
        }

        if (light.sourceNodeName.empty())
        {
            issues.push_back("Indoor source light '" + light.id + "' has no source node.");
        }

        if (light.radius <= 0)
        {
            issues.push_back("Indoor source light '" + light.id + "' radius must be greater than zero.");
        }

        if (light.brightness <= 0)
        {
            issues.push_back("Indoor source light '" + light.id + "' brightness must be greater than zero.");
        }

        if (light.runtimeLightIndex && *light.runtimeLightIndex >= indoorGeometry.lights.size())
        {
            issues.push_back("Indoor source light '" + light.id + "' runtime light index is out of range.");
        }
    }

    std::unordered_set<std::string> spawnIds;

    for (const EditorIndoorGeometrySpawnMetadata &spawn : metadata.spawns)
    {
        if (spawn.id.empty())
        {
            issues.push_back("Indoor source spawn has an empty id.");
            continue;
        }

        if (!spawnIds.insert(spawn.id).second)
        {
            issues.push_back("Indoor source spawn '" + spawn.id + "' is duplicated.");
        }

        if (spawn.sourceNodeName.empty())
        {
            issues.push_back("Indoor source spawn '" + spawn.id + "' has no source node.");
        }

        if (spawn.typeId == 0 && spawn.index == 0)
        {
            issues.push_back("Indoor source spawn '" + spawn.id + "' type/index is not set.");
        }

        if (spawn.runtimeSpawnIndex && *spawn.runtimeSpawnIndex >= indoorGeometry.spawns.size())
        {
            issues.push_back("Indoor source spawn '" + spawn.id + "' runtime spawn index is out of range.");
        }
    }

    return issues;
}
}
