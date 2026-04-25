#include "game/maps/TerrainTileData.h"

#include "engine/TextTable.h"

#include <algorithm>
#include <cctype>
#include <charconv>
#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
std::string trimAsciiWhitespace(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
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

std::optional<int> resolveTerrainDescriptorIndex(const OutdoorMapData &outdoorMapData, int tileIndex)
{
    // Legacy outdoor local tile ids are laid out as:
    // [0..90) direct/global ids
    // [90..126) tileset #1
    // [126..162) tileset #2
    // [162..198) tileset #3
    // [198..234) tileset #4 (road)
    // [234..256) invalid/pending
    if (tileIndex < 90)
    {
        return tileIndex;
    }

    if (tileIndex >= 234)
    {
        return std::nullopt;
    }

    const int tilesetIndex = (tileIndex - 90) / 36;
    const int tilesetOffset = (tileIndex - 90) % 36;
    return static_cast<int>(outdoorMapData.tileSetLookupIndices[tilesetIndex]) + tilesetOffset;
}

uint16_t parseUnsigned16(const std::string &value)
{
    const std::string trimmedValue = trimAsciiWhitespace(value);

    if (trimmedValue.empty())
    {
        return 0;
    }

    unsigned int parsedValue = 0;
    const int base = trimmedValue.starts_with("0x") || trimmedValue.starts_with("0X") ? 16 : 10;
    const char *pBegin = trimmedValue.data() + (base == 16 ? 2 : 0);
    const char *pEnd = trimmedValue.data() + trimmedValue.size();
    const std::from_chars_result result = std::from_chars(pBegin, pEnd, parsedValue, base);

    if (result.ec != std::errc() || result.ptr != pEnd)
    {
        return 0;
    }

    return static_cast<uint16_t>(parsedValue);
}
} // namespace

std::string terrainTileDataPath(uint8_t masterTile)
{
    if (masterTile == 1)
    {
        return "Data/data_tables/terrain_tile_data_2.txt";
    }

    if (masterTile == 2)
    {
        return "Data/data_tables/terrain_tile_data_3.txt";
    }

    return "Data/data_tables/terrain_tile_data.txt";
}

std::optional<std::vector<TerrainTileDescriptor>> loadTerrainTileDescriptors(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData)
{
    const std::optional<std::string> tableContents =
        assetFileSystem.readTextFile(terrainTileDataPath(outdoorMapData.masterTile));

    if (!tableContents)
    {
        std::cout << "Terrain tile data load failed for " << outdoorMapData.fileName
                  << ": missing table " << terrainTileDataPath(outdoorMapData.masterTile) << '\n';
        return std::nullopt;
    }

    const std::optional<Engine::TextTable> parsedTable = Engine::TextTable::parseTabSeparated(*tableContents);

    if (!parsedTable)
    {
        std::cout << "Terrain tile data parse failed for " << outdoorMapData.fileName
                  << ": " << terrainTileDataPath(outdoorMapData.masterTile) << '\n';
        return std::nullopt;
    }

    std::vector<TerrainTileDescriptor> descriptors;
    descriptors.reserve(parsedTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        const std::vector<std::string> &row = parsedTable->getRow(rowIndex);

        if (row.size() < 7)
        {
            continue;
        }

        if (rowIndex == 0 && toLowerCopy(trimAsciiWhitespace(row[0])) == "index")
        {
            continue;
        }

        TerrainTileDescriptor descriptor = {};
        descriptor.textureName = toLowerCopy(trimAsciiWhitespace(row[1]));

        if (descriptor.textureName.empty())
        {
            descriptor.textureName = "pending";
        }

        descriptor.tileset = parseUnsigned16(row[4]);
        descriptor.variant = parseUnsigned16(row[5]);
        descriptor.flags = parseUnsigned16(row[6]);
        descriptors.push_back(std::move(descriptor));
    }

    if (descriptors.empty())
    {
        std::cout << "Terrain tile data empty for " << outdoorMapData.fileName
                  << ": " << terrainTileDataPath(outdoorMapData.masterTile) << '\n';
        return std::nullopt;
    }

    std::vector<TerrainTileDescriptor> tileDescriptors(256);

    for (int tileIndex = 0; tileIndex < 256; ++tileIndex)
    {
        const std::optional<int> descriptorIndex = resolveTerrainDescriptorIndex(outdoorMapData, tileIndex);

        if (!descriptorIndex)
        {
            tileDescriptors[tileIndex].textureName = "pending";
            continue;
        }

        if (*descriptorIndex < 0 || *descriptorIndex >= static_cast<int>(descriptors.size()))
        {
            std::cout << "Terrain tile data descriptor index out of range for " << outdoorMapData.fileName
                      << ": tile=" << tileIndex
                      << " descriptor=" << *descriptorIndex
                      << " rows=" << descriptors.size()
                      << " master_tile=" << static_cast<int>(outdoorMapData.masterTile) << '\n';
            return std::nullopt;
        }

        tileDescriptors[tileIndex] = descriptors[*descriptorIndex];
    }

    return tileDescriptors;
}

std::optional<std::vector<std::string>> loadTerrainTileTextureNames(
    const Engine::AssetFileSystem &assetFileSystem,
    const OutdoorMapData &outdoorMapData)
{
    const std::optional<std::vector<TerrainTileDescriptor>> tileDescriptors =
        loadTerrainTileDescriptors(assetFileSystem, outdoorMapData);

    if (!tileDescriptors)
    {
        return std::nullopt;
    }

    std::vector<std::string> tileTextureNames(256);

    for (size_t tileIndex = 0; tileIndex < tileDescriptors->size(); ++tileIndex)
    {
        tileTextureNames[tileIndex] = (*tileDescriptors)[tileIndex].textureName;
    }

    return tileTextureNames;
}

bool applyTerrainTileDescriptorAttributes(
    const Engine::AssetFileSystem &assetFileSystem,
    OutdoorMapData &outdoorMapData)
{
    const std::optional<std::vector<TerrainTileDescriptor>> tileDescriptors =
        loadTerrainTileDescriptors(assetFileSystem, outdoorMapData);

    if (!tileDescriptors)
    {
        return false;
    }

    if (outdoorMapData.attributeMap.size()
        != static_cast<size_t>(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight))
    {
        outdoorMapData.attributeMap.assign(
            static_cast<size_t>(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight),
            0);
    }

    if (outdoorMapData.tileMap.size()
        < static_cast<size_t>(OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight))
    {
        return false;
    }

    for (int gridY = 0; gridY < OutdoorMapData::TerrainHeight - 1; ++gridY)
    {
        for (int gridX = 0; gridX < OutdoorMapData::TerrainWidth - 1; ++gridX)
        {
            const size_t cellIndex = static_cast<size_t>(gridY * OutdoorMapData::TerrainWidth + gridX);
            const uint8_t tileId = outdoorMapData.tileMap[cellIndex];
            const TerrainTileDescriptor &descriptor = (*tileDescriptors)[tileId];

            outdoorMapData.attributeMap[cellIndex] =
                static_cast<uint8_t>(outdoorMapData.attributeMap[cellIndex] | (descriptor.flags & 0x0003));
        }
    }

    return true;
}
} // namespace OpenYAMM::Game
