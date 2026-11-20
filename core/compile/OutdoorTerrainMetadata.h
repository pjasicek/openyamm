#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Editor
{
struct EditorOutdoorTerrainMetadata
{
    uint32_t version = 1;
    std::string mapFileName;
    std::vector<uint8_t> heightMap;
    std::vector<uint8_t> tileMap;
    std::vector<uint8_t> attributeMap;
};

std::string serializeOutdoorTerrainMetadata(const EditorOutdoorTerrainMetadata &metadata);

std::optional<EditorOutdoorTerrainMetadata> loadOutdoorTerrainMetadataFromText(
    const std::string &yamlText,
    std::string &errorMessage);

void normalizeOutdoorTerrainMetadata(
    EditorOutdoorTerrainMetadata &metadata,
    const std::string &mapFileName,
    const std::vector<uint8_t> &heightMap,
    const std::vector<uint8_t> &tileMap,
    const std::vector<uint8_t> &attributeMap);
}
