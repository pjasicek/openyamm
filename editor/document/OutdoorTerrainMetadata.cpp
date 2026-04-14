#include "editor/document/OutdoorTerrainMetadata.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>

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

std::string bytesToUpperHex(const std::vector<uint8_t> &bytes)
{
    static constexpr char HexDigits[] = "0123456789ABCDEF";

    std::string text;
    text.reserve(bytes.size() * 2);

    for (uint8_t value : bytes)
    {
        text.push_back(HexDigits[(value >> 4) & 0x0f]);
        text.push_back(HexDigits[value & 0x0f]);
    }

    return text;
}

bool upperHexToBytes(const std::string &text, std::vector<uint8_t> &bytes)
{
    bytes.clear();

    if ((text.size() % 2) != 0)
    {
        return false;
    }

    auto decodeNibble = [](char character) -> int
    {
        if (character >= '0' && character <= '9')
        {
            return character - '0';
        }

        if (character >= 'A' && character <= 'F')
        {
            return 10 + (character - 'A');
        }

        if (character >= 'a' && character <= 'f')
        {
            return 10 + (character - 'a');
        }

        return -1;
    };

    bytes.reserve(text.size() / 2);

    for (size_t index = 0; index < text.size(); index += 2)
    {
        const int highNibble = decodeNibble(text[index]);
        const int lowNibble = decodeNibble(text[index + 1]);

        if (highNibble < 0 || lowNibble < 0)
        {
            bytes.clear();
            return false;
        }

        bytes.push_back(static_cast<uint8_t>((highNibble << 4) | lowNibble));
    }

    return true;
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
        errorMessage = std::string("invalid terrain metadata field '") + pKey + "': " + exception.what();
        return false;
    }
}
}

std::string serializeOutdoorTerrainMetadata(const EditorOutdoorTerrainMetadata &metadata)
{
    YAML::Emitter emitter;
    emitter.SetIndent(2);
    emitter.SetMapFormat(YAML::Block);

    emitter << YAML::BeginMap;
    emitter << YAML::Key << "version" << YAML::Value << metadata.version;
    emitter << YAML::Key << "map_file" << YAML::Value << metadata.mapFileName;
    emitter << YAML::Key << "height_map_hex" << YAML::Value << bytesToUpperHex(metadata.heightMap);
    emitter << YAML::Key << "tile_map_hex" << YAML::Value << bytesToUpperHex(metadata.tileMap);
    emitter << YAML::Key << "attribute_map_hex" << YAML::Value << bytesToUpperHex(metadata.attributeMap);
    emitter << YAML::EndMap;

    std::string text = emitter.c_str();

    if (!text.empty() && text.back() != '\n')
    {
        text.push_back('\n');
    }

    return text;
}

std::optional<EditorOutdoorTerrainMetadata> loadOutdoorTerrainMetadataFromText(
    const std::string &yamlText,
    std::string &errorMessage)
{
    EditorOutdoorTerrainMetadata metadata = {};
    YAML::Node rootNode;

    try
    {
        rootNode = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse terrain metadata yaml: ") + exception.what();
        return std::nullopt;
    }

    if (!rootNode || !rootNode.IsMap())
    {
        errorMessage = "terrain metadata root must be a map";
        return std::nullopt;
    }

    std::string heightMapHex;
    std::string tileMapHex;
    std::string attributeMapHex;

    if (!readScalarNode(rootNode, "version", metadata.version, errorMessage)
        || !readScalarNode(rootNode, "map_file", metadata.mapFileName, errorMessage)
        || !readScalarNode(rootNode, "height_map_hex", heightMapHex, errorMessage)
        || !readScalarNode(rootNode, "tile_map_hex", tileMapHex, errorMessage)
        || !readScalarNode(rootNode, "attribute_map_hex", attributeMapHex, errorMessage))
    {
        return std::nullopt;
    }

    if (!upperHexToBytes(trimCopy(heightMapHex), metadata.heightMap))
    {
        errorMessage = "terrain metadata height_map_hex is invalid";
        return std::nullopt;
    }

    if (!upperHexToBytes(trimCopy(tileMapHex), metadata.tileMap))
    {
        errorMessage = "terrain metadata tile_map_hex is invalid";
        return std::nullopt;
    }

    if (!upperHexToBytes(trimCopy(attributeMapHex), metadata.attributeMap))
    {
        errorMessage = "terrain metadata attribute_map_hex is invalid";
        return std::nullopt;
    }

    return metadata;
}

void normalizeOutdoorTerrainMetadata(
    EditorOutdoorTerrainMetadata &metadata,
    const std::string &mapFileName,
    const std::vector<uint8_t> &heightMap,
    const std::vector<uint8_t> &tileMap,
    const std::vector<uint8_t> &attributeMap)
{
    metadata.version = 1;
    metadata.mapFileName = mapFileName;

    if (metadata.heightMap.size() != heightMap.size())
    {
        metadata.heightMap = heightMap;
    }

    if (metadata.tileMap.size() != tileMap.size())
    {
        metadata.tileMap = tileMap;
    }

    if (metadata.attributeMap.size() != attributeMap.size())
    {
        metadata.attributeMap = attributeMap;
    }
}
}
