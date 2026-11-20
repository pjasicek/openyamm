#include "game/content/WorldDecorations.h"

#include "engine/AssetFileSystem.h"
#include "engine/TextTable.h"
#include "game/StringUtils.h"

#include <cctype>
#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// The largest decoration number: decoration_list_id is 16-bit.
constexpr uint32_t MaxDecorationNumber = uint32_t(std::numeric_limits<uint16_t>::max()) + 1;

std::string trimmedCell(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return {};
    }

    const std::string &value = row[index];
    size_t begin = 0;
    size_t end = value.size();

    while (begin < end && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

// The row's decoration number; none for header and comment lines.
std::optional<uint32_t> decorationNumber(const std::vector<std::string> &row)
{
    const std::string cell = trimmedCell(row, 0);

    if (cell.empty() || cell.size() > 9)
    {
        return std::nullopt;
    }

    for (const char character : cell)
    {
        if (std::isdigit(static_cast<unsigned char>(character)) == 0)
        {
            return std::nullopt;
        }
    }

    return uint32_t(std::stoul(cell));
}

bool readTableRows(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    std::vector<std::vector<std::string>> &rows,
    std::string &errorMessage)
{
    const std::optional<std::string> contents = assetFileSystem.readTextFile(virtualPath);

    if (!contents)
    {
        errorMessage = "could not read " + virtualPath;
        return false;
    }

    const std::optional<Engine::TextTable> table = Engine::TextTable::parseTabSeparated(*contents);

    if (!table)
    {
        errorMessage = "could not parse " + virtualPath;
        return false;
    }

    rows.clear();
    rows.reserve(table->getRowCount());

    for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
    {
        rows.push_back(table->getRow(rowIndex));
    }

    return true;
}
}

bool composeDecorationTableRows(
    const std::vector<std::vector<std::string>> &engineRows,
    const WorldDecorationRows *pWorldRows,
    std::vector<std::vector<std::string>> &composedRows,
    std::string &errorMessage)
{
    errorMessage.clear();
    composedRows = engineRows;

    if (pWorldRows == nullptr)
    {
        return true;
    }

    uint32_t engineLastNumber = 0;
    std::unordered_set<std::string> names;

    for (const std::vector<std::string> &row : engineRows)
    {
        if (const std::optional<uint32_t> number = decorationNumber(row))
        {
            engineLastNumber = std::max(engineLastNumber, *number);
            const std::string name = toLowerCopy(trimmedCell(row, 1));

            if (!name.empty())
            {
                names.insert(name);
            }
        }
    }

    const std::string owner = "world '" + pWorldRows->packageId + "' decorations";
    const ContentIdRangeDefinition &range = pWorldRows->idRange;

    if (range.begin <= engineLastNumber || range.begin > range.end || range.end > MaxDecorationNumber)
    {
        errorMessage = owner + " range " + std::to_string(range.begin) + "-" + std::to_string(range.end)
            + " must start past the engine's last decoration (" + std::to_string(engineLastNumber)
            + ") and end by " + std::to_string(MaxDecorationNumber);
        return false;
    }

    uint32_t previousNumber = 0;

    for (const std::vector<std::string> &row : pWorldRows->rows)
    {
        const std::optional<uint32_t> number = decorationNumber(row);

        if (!number)
        {
            continue;
        }

        const std::string name = toLowerCopy(trimmedCell(row, 1));
        const std::string label = owner + " row " + std::to_string(*number) + " (" + name + ")";

        if (*number < range.begin || *number > range.end)
        {
            errorMessage = label + " is outside the world's range " + std::to_string(range.begin) + "-"
                + std::to_string(range.end);
            return false;
        }

        if (*number <= previousNumber)
        {
            errorMessage = label + " repeats or comes before row " + std::to_string(previousNumber)
                + ": rows must be in increasing order";
            return false;
        }

        if (name.empty() || !names.insert(name).second)
        {
            errorMessage = label + (name.empty() ? " has no name" : " repeats a decoration name in use");
            return false;
        }

        previousNumber = *number;
        composedRows.push_back(row);
    }

    return true;
}

bool loadDecorationTableRows(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<std::vector<std::string>> &rows,
    std::string &errorMessage)
{
    rows.clear();
    errorMessage.clear();
    std::vector<std::vector<std::string>> engineRows;

    if (!readTableRows(assetFileSystem, EngineDecorationTablePath, engineRows, errorMessage))
    {
        return false;
    }

    std::string manifestError;
    const WorldManifest manifest =
        loadActiveWorldManifestOrDefault(assetFileSystem, assetFileSystem.getActiveWorldId(), manifestError);

    if (!manifestError.empty())
    {
        errorMessage = "world.yml: " + manifestError;
        return false;
    }

    std::optional<WorldDecorationRows> worldRows;

    for (const TableContributionDefinition &contribution : manifest.tableContributions)
    {
        if (contribution.table != DecorationContributionTable)
        {
            continue;
        }

        const ContentIdRangeDefinition *pRange = manifest.findIdRange(contribution.idDomain);

        if (worldRows || contribution.mode != TableContributionMode::Append || pRange == nullptr)
        {
            errorMessage = "world '" + manifest.id
                + "' needs one decorations contribution, mode append, with a declared id range";
            return false;
        }

        worldRows = WorldDecorationRows{manifest.id, *pRange, {}};

        if (!readTableRows(
                assetFileSystem, "worlds/" + manifest.id + "/" + contribution.path, worldRows->rows, errorMessage))
        {
            return false;
        }
    }

    return composeDecorationTableRows(engineRows, worldRows ? &*worldRows : nullptr, rows, errorMessage);
}

bool appendWorldDecorationSpriteFrames(
    const Engine::AssetFileSystem &assetFileSystem,
    SpriteFrameTable &spriteFrameTable,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::string path =
        "worlds/" + assetFileSystem.getActiveWorldId() + "/rendering/sprite_frame_data_world_decorations.yml";
    const std::optional<std::string> contents = assetFileSystem.readTextFile(path);

    if (!contents)
    {
        return true;
    }

    std::string loadError;

    if (!spriteFrameTable.loadFromYaml(*contents, loadError, true))
    {
        errorMessage = path + ": " + loadError;
        return false;
    }

    return true;
}
}
