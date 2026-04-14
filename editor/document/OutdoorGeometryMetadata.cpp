#include "editor/document/OutdoorGeometryMetadata.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdio>
#include <cmath>
#include <unordered_set>

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

std::string sanitizeMapStem(const std::string &mapFileName)
{
    std::string stem = mapFileName;
    const size_t extensionOffset = stem.find_last_of('.');

    if (extensionOffset != std::string::npos)
    {
        stem.resize(extensionOffset);
    }

    std::string result;
    result.reserve(stem.size());

    for (char character : stem)
    {
        if (std::isalnum(static_cast<unsigned char>(character)) != 0)
        {
            result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
        }
        else
        {
            result.push_back('_');
        }
    }

    if (result.empty())
    {
        return "map";
    }

    return result;
}

std::string defaultGeometryId(const std::string &mapFileName, size_t bmodelIndex)
{
    char buffer[128] = {};
    std::snprintf(
        buffer,
        sizeof(buffer),
        "%s_bmodel_%04zu",
        sanitizeMapStem(mapFileName).c_str(),
        bmodelIndex);
    return buffer;
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
        errorMessage = std::string("invalid geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

bool readFloatArrayNode(
    const YAML::Node &node,
    const char *pKey,
    std::array<float, 3> &value,
    std::string &errorMessage)
{
    const YAML::Node childNode = node[pKey];

    if (!childNode)
    {
        return true;
    }

    if (!childNode.IsSequence() || childNode.size() != 3)
    {
        errorMessage = std::string("invalid geometry metadata field '") + pKey + "': expected 3-element sequence";
        return false;
    }

    try
    {
        value[0] = childNode[0].as<float>();
        value[1] = childNode[1].as<float>();
        value[2] = childNode[2].as<float>();
        return true;
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("invalid geometry metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}

void emitFloatArray(YAML::Emitter &emitter, const std::array<float, 3> &value)
{
    emitter << YAML::Flow << YAML::BeginSeq << value[0] << value[1] << value[2] << YAML::EndSeq;
}

bool isFiniteBasisVector(const std::array<float, 3> &value)
{
    return std::isfinite(value[0]) && std::isfinite(value[1]) && std::isfinite(value[2]);
}

bool isIdentitySourceTransform(const EditorBModelSourceTransform &transform)
{
    constexpr float Epsilon = 0.0001f;
    return std::fabs(transform.originX) <= Epsilon
        && std::fabs(transform.originY) <= Epsilon
        && std::fabs(transform.originZ) <= Epsilon
        && std::fabs(transform.basisX[0] - 1.0f) <= Epsilon
        && std::fabs(transform.basisX[1]) <= Epsilon
        && std::fabs(transform.basisX[2]) <= Epsilon
        && std::fabs(transform.basisY[0]) <= Epsilon
        && std::fabs(transform.basisY[1] - 1.0f) <= Epsilon
        && std::fabs(transform.basisY[2]) <= Epsilon
        && std::fabs(transform.basisZ[0]) <= Epsilon
        && std::fabs(transform.basisZ[1]) <= Epsilon
        && std::fabs(transform.basisZ[2] - 1.0f) <= Epsilon;
}
}

std::string serializeOutdoorGeometryMetadata(const EditorOutdoorGeometryMetadata &metadata)
{
    YAML::Emitter emitter;
    emitter.SetIndent(2);
    emitter.SetSeqFormat(YAML::Block);
    emitter.SetMapFormat(YAML::Block);

    emitter << YAML::BeginMap;
    emitter << YAML::Key << "version" << YAML::Value << metadata.version;
    emitter << YAML::Key << "map_file" << YAML::Value << metadata.mapFileName;
    emitter << YAML::Key << "bmodels" << YAML::Value << YAML::BeginSeq;

    for (const EditorOutdoorGeometryMetadataEntry &entry : metadata.bmodels)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "geometry_id" << YAML::Value << entry.geometryId;
        emitter << YAML::Key << "runtime_bmodel_index" << YAML::Value << entry.runtimeBModelIndex;

        if (!entry.importSource.sourcePath.empty()
            || !entry.importSource.sourceMeshName.empty()
            || !entry.importSource.defaultTextureName.empty())
        {
            emitter << YAML::Key << "source" << YAML::Value << YAML::BeginMap;
            emitter << YAML::Key << "asset_path" << YAML::Value << entry.importSource.sourcePath;

            if (!entry.importSource.sourceMeshName.empty())
            {
                emitter << YAML::Key << "mesh_name" << YAML::Value << entry.importSource.sourceMeshName;
            }

            emitter << YAML::Key << "scale" << YAML::Value << entry.importSource.importScale;
            emitter << YAML::EndMap;

            emitter << YAML::Key << "materials" << YAML::Value << YAML::BeginMap;
            emitter << YAML::Key << "default_texture" << YAML::Value << entry.importSource.defaultTextureName;
            emitter << YAML::EndMap;
        }

        if (entry.sourceTransform && (!entry.importSource.sourcePath.empty() || !isIdentitySourceTransform(*entry.sourceTransform)))
        {
            emitter << YAML::Key << "transform" << YAML::Value << YAML::BeginMap;
            emitter << YAML::Key << "origin" << YAML::Value;
            emitFloatArray(emitter, {entry.sourceTransform->originX, entry.sourceTransform->originY, entry.sourceTransform->originZ});
            emitter << YAML::Key << "basis_x" << YAML::Value;
            emitFloatArray(emitter, entry.sourceTransform->basisX);
            emitter << YAML::Key << "basis_y" << YAML::Value;
            emitFloatArray(emitter, entry.sourceTransform->basisY);
            emitter << YAML::Key << "basis_z" << YAML::Value;
            emitFloatArray(emitter, entry.sourceTransform->basisZ);
            emitter << YAML::EndMap;
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

std::optional<EditorOutdoorGeometryMetadata> loadOutdoorGeometryMetadataFromText(
    const std::string &yamlText,
    std::string &errorMessage)
{
    EditorOutdoorGeometryMetadata metadata = {};
    YAML::Node rootNode;

    try
    {
        rootNode = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse geometry metadata yaml: ") + exception.what();
        return std::nullopt;
    }

    if (!rootNode || !rootNode.IsMap())
    {
        errorMessage = "geometry metadata root must be a map";
        return std::nullopt;
    }

    if (!readScalarNode(rootNode, "version", metadata.version, errorMessage)
        || !readScalarNode(rootNode, "map_file", metadata.mapFileName, errorMessage))
    {
        return std::nullopt;
    }

    const YAML::Node bmodelsNode = rootNode["bmodels"];

    if (bmodelsNode)
    {
        if (!bmodelsNode.IsSequence())
        {
            errorMessage = "geometry metadata bmodels must be a sequence";
            return std::nullopt;
        }

        metadata.bmodels.reserve(bmodelsNode.size());

        for (const YAML::Node &entryNode : bmodelsNode)
        {
            if (!entryNode.IsMap())
            {
                errorMessage = "geometry metadata bmodel entry must be a map";
                return std::nullopt;
            }

            EditorOutdoorGeometryMetadataEntry entry = {};

            if (!readScalarNode(entryNode, "geometry_id", entry.geometryId, errorMessage)
                || !readScalarNode(entryNode, "runtime_bmodel_index", entry.runtimeBModelIndex, errorMessage))
            {
                return std::nullopt;
            }

            const YAML::Node sourceNode = entryNode["source"];

            if (sourceNode)
            {
                if (!sourceNode.IsMap())
                {
                    errorMessage = "geometry metadata source must be a map";
                    return std::nullopt;
                }

                if (!readScalarNode(sourceNode, "asset_path", entry.importSource.sourcePath, errorMessage)
                    || !readScalarNode(sourceNode, "mesh_name", entry.importSource.sourceMeshName, errorMessage)
                    || !readScalarNode(sourceNode, "scale", entry.importSource.importScale, errorMessage))
                {
                    return std::nullopt;
                }
            }

            const YAML::Node materialsNode = entryNode["materials"];

            if (materialsNode)
            {
                if (!materialsNode.IsMap())
                {
                    errorMessage = "geometry metadata materials must be a map";
                    return std::nullopt;
                }

                if (!readScalarNode(
                        materialsNode,
                        "default_texture",
                        entry.importSource.defaultTextureName,
                        errorMessage))
                {
                    return std::nullopt;
                }
            }

            const YAML::Node transformNode = entryNode["transform"];

            if (transformNode)
            {
                if (!transformNode.IsMap())
                {
                    errorMessage = "geometry metadata transform must be a map";
                    return std::nullopt;
                }

                EditorBModelSourceTransform transform = {};
                std::array<float, 3> origin = {0.0f, 0.0f, 0.0f};

                if (!readFloatArrayNode(transformNode, "origin", origin, errorMessage)
                    || !readFloatArrayNode(transformNode, "basis_x", transform.basisX, errorMessage)
                    || !readFloatArrayNode(transformNode, "basis_y", transform.basisY, errorMessage)
                    || !readFloatArrayNode(transformNode, "basis_z", transform.basisZ, errorMessage))
                {
                    return std::nullopt;
                }

                transform.originX = origin[0];
                transform.originY = origin[1];
                transform.originZ = origin[2];
                entry.sourceTransform = transform;
            }

            metadata.bmodels.push_back(std::move(entry));
        }
    }

    return metadata;
}

void normalizeOutdoorGeometryMetadata(
    EditorOutdoorGeometryMetadata &metadata,
    const std::string &mapFileName,
    size_t bmodelCount)
{
    metadata.version = 1;
    metadata.mapFileName = mapFileName;

    std::vector<EditorOutdoorGeometryMetadataEntry> normalizedEntries;
    normalizedEntries.resize(bmodelCount);
    std::vector<bool> hasEntry(bmodelCount, false);

    for (const EditorOutdoorGeometryMetadataEntry &entry : metadata.bmodels)
    {
        if (entry.runtimeBModelIndex >= bmodelCount || hasEntry[entry.runtimeBModelIndex])
        {
            continue;
        }

        normalizedEntries[entry.runtimeBModelIndex] = entry;
        hasEntry[entry.runtimeBModelIndex] = true;
    }

    for (size_t index = 0; index < normalizedEntries.size(); ++index)
    {
        normalizedEntries[index].runtimeBModelIndex = index;
        normalizedEntries[index].importSource.sourcePath =
            trimCopy(normalizedEntries[index].importSource.sourcePath);
        normalizedEntries[index].importSource.sourceMeshName =
            trimCopy(normalizedEntries[index].importSource.sourceMeshName);
        normalizedEntries[index].importSource.defaultTextureName =
            trimCopy(normalizedEntries[index].importSource.defaultTextureName);

        if (normalizedEntries[index].importSource.importScale <= 0.0f)
        {
            normalizedEntries[index].importSource.importScale = 1.0f;
        }

        if (normalizedEntries[index].sourceTransform)
        {
            EditorBModelSourceTransform &transform = *normalizedEntries[index].sourceTransform;

            if (!std::isfinite(transform.originX)
                || !std::isfinite(transform.originY)
                || !std::isfinite(transform.originZ)
                || !isFiniteBasisVector(transform.basisX)
                || !isFiniteBasisVector(transform.basisY)
                || !isFiniteBasisVector(transform.basisZ))
            {
                normalizedEntries[index].sourceTransform = std::nullopt;
            }
        }
    }

    std::unordered_set<std::string> seenGeometryIds;

    for (size_t index = 0; index < normalizedEntries.size(); ++index)
    {
        std::string geometryId = trimCopy(normalizedEntries[index].geometryId);
        std::string normalizedId = toLowerCopy(geometryId);

        if (geometryId.empty() || normalizedId.empty() || seenGeometryIds.contains(normalizedId))
        {
            size_t suffix = 0;

            do
            {
                geometryId = defaultGeometryId(mapFileName, index);

                if (suffix > 0)
                {
                    geometryId += "_" + std::to_string(suffix);
                }

                normalizedId = toLowerCopy(geometryId);
                ++suffix;
            }
            while (seenGeometryIds.contains(normalizedId));
        }

        normalizedEntries[index].geometryId = geometryId;
        seenGeometryIds.insert(normalizedId);
    }

    metadata.bmodels = std::move(normalizedEntries);
}
}
