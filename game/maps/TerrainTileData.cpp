#include "game/maps/TerrainTileData.h"

#include "engine/TextTable.h"

#include <algorithm>
#include <cctype>
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

std::optional<std::vector<std::string>> loadTerrainTileTextureNames(
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

    std::vector<std::string> descriptorNames;
    descriptorNames.reserve(parsedTable->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        const std::vector<std::string> &row = parsedTable->getRow(rowIndex);

        if (row.size() < 2)
        {
            continue;
        }

        if (rowIndex == 0 && toLowerCopy(trimAsciiWhitespace(row[0])) == "index")
        {
            continue;
        }

        std::string textureName = toLowerCopy(trimAsciiWhitespace(row[1]));

        if (textureName.empty())
        {
            textureName = "pending";
        }

        descriptorNames.push_back(std::move(textureName));
    }

    if (descriptorNames.empty())
    {
        std::cout << "Terrain tile data empty for " << outdoorMapData.fileName
                  << ": " << terrainTileDataPath(outdoorMapData.masterTile) << '\n';
        return std::nullopt;
    }

    std::vector<std::string> tileTextureNames(256);

    for (int tileIndex = 0; tileIndex < 256; ++tileIndex)
    {
        const std::optional<int> descriptorIndex = resolveTerrainDescriptorIndex(outdoorMapData, tileIndex);

        if (!descriptorIndex)
        {
            tileTextureNames[tileIndex] = "pending";
            continue;
        }

        if (*descriptorIndex < 0 || *descriptorIndex >= static_cast<int>(descriptorNames.size()))
        {
            std::cout << "Terrain tile data descriptor index out of range for " << outdoorMapData.fileName
                      << ": tile=" << tileIndex
                      << " descriptor=" << *descriptorIndex
                      << " rows=" << descriptorNames.size()
                      << " master_tile=" << static_cast<int>(outdoorMapData.masterTile) << '\n';
            return std::nullopt;
        }

        tileTextureNames[tileIndex] = descriptorNames[*descriptorIndex];
    }

    return tileTextureNames;
}
} // namespace OpenYAMM::Game
