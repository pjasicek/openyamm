#include "game/content/ContentTableComposer.h"

#include "game/StringUtils.h"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t StandardPackageIdColumn = 17;
constexpr size_t StandardCanonicalIdColumn = 18;
constexpr size_t StandardSourceIdColumn = 19;

std::string trimmed(const std::string &value)
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

std::string cell(const std::vector<std::string> &row, size_t index)
{
    return index < row.size() ? trimmed(row[index]) : std::string();
}

std::optional<uint32_t> parseUnsigned(const std::string &value)
{
    const std::string normalized = trimmed(value);

    if (normalized.empty())
    {
        return std::nullopt;
    }

    for (char character : normalized)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return std::nullopt;
        }
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(normalized));
    }
    catch (...)
    {
        return std::nullopt;
    }
}

bool rangesOverlap(const ContentIdRangeDefinition &left, const ContentIdRangeDefinition &right)
{
    return left.begin <= right.end && right.begin <= left.end;
}

bool validateRanges(const std::vector<ItemTableContributionRows> &contributions, std::string &errorMessage)
{
    for (size_t leftIndex = 0; leftIndex < contributions.size(); ++leftIndex)
    {
        const ItemTableContributionRows &left = contributions[leftIndex];

        if (left.packageId.empty() || left.idRange.domain != "items" || left.idRange.begin == 0
            || left.idRange.begin > left.idRange.end || left.sourceIdColumn == left.canonicalIdColumn)
        {
            errorMessage = "invalid item contribution range for package '" + left.packageId + "'";
            return false;
        }

        for (size_t rightIndex = leftIndex + 1; rightIndex < contributions.size(); ++rightIndex)
        {
            const ItemTableContributionRows &right = contributions[rightIndex];

            if (rangesOverlap(left.idRange, right.idRange))
            {
                errorMessage = "overlapping item id ranges for packages '" + left.packageId + "' and '"
                    + right.packageId + "'";
                return false;
            }
        }
    }

    return true;
}
}

bool composeItemTableRows(
    const std::vector<std::vector<std::string>> &baseRows,
    const std::vector<ItemTableContributionRows> &contributions,
    std::vector<std::vector<std::string>> &composedRows,
    std::string &errorMessage)
{
    composedRows.clear();
    errorMessage.clear();

    if (!validateRanges(contributions, errorMessage))
    {
        return false;
    }

    std::unordered_map<uint32_t, std::string> itemOwners;
    std::unordered_set<std::string> canonicalIds;

    for (const std::vector<std::string> &row : baseRows)
    {
        const std::optional<uint32_t> itemId = parseUnsigned(cell(row, 0));

        if (itemId)
        {
            const std::pair<std::unordered_map<uint32_t, std::string>::iterator, bool> inserted =
                itemOwners.emplace(*itemId, "engine");

            if (!inserted.second)
            {
                errorMessage = "duplicate base item id " + std::to_string(*itemId);
                return false;
            }
        }

        composedRows.push_back(row);
    }

    std::vector<const ItemTableContributionRows *> sortedContributions;
    sortedContributions.reserve(contributions.size());

    for (const ItemTableContributionRows &contribution : contributions)
    {
        sortedContributions.push_back(&contribution);
    }

    std::sort(
        sortedContributions.begin(),
        sortedContributions.end(),
        [](const ItemTableContributionRows *pLeft, const ItemTableContributionRows *pRight)
        {
            return pLeft->packageId < pRight->packageId;
        });

    for (const ItemTableContributionRows *pContribution : sortedContributions)
    {
        for (const std::vector<std::string> &row : pContribution->rows)
        {
            const std::optional<uint32_t> itemId = parseUnsigned(cell(row, 0));

            if (!itemId)
            {
                continue;
            }

            if (*itemId < pContribution->idRange.begin || *itemId > pContribution->idRange.end)
            {
                errorMessage = "item id " + std::to_string(*itemId) + " is outside package '"
                    + pContribution->packageId + "' declared range";
                return false;
            }

            const std::pair<std::unordered_map<uint32_t, std::string>::iterator, bool> insertedItem =
                itemOwners.emplace(*itemId, pContribution->packageId);

            if (!insertedItem.second)
            {
                errorMessage = "item id " + std::to_string(*itemId) + " from package '"
                    + pContribution->packageId + "' collides with package '" + insertedItem.first->second + "'";
                return false;
            }

            const std::optional<uint32_t> sourceItemId = parseUnsigned(cell(row, pContribution->sourceIdColumn));
            const std::string canonicalId = cell(row, pContribution->canonicalIdColumn);
            const std::string expectedCanonicalPrefix = pContribution->packageId + ":item/";

            if (!sourceItemId || canonicalId.empty()
                || !toLowerCopy(canonicalId).starts_with(toLowerCopy(expectedCanonicalPrefix)))
            {
                errorMessage = "item id " + std::to_string(*itemId) + " from package '"
                    + pContribution->packageId + "' lacks valid source or canonical provenance";
                return false;
            }

            if (!canonicalIds.insert(toLowerCopy(canonicalId)).second)
            {
                errorMessage = "duplicate canonical item id '" + canonicalId + "'";
                return false;
            }

            std::vector<std::string> normalizedRow = row;
            normalizedRow.resize(std::max(normalizedRow.size(), StandardSourceIdColumn + 1));
            normalizedRow[StandardPackageIdColumn] = pContribution->packageId;
            normalizedRow[StandardCanonicalIdColumn] = canonicalId;
            normalizedRow[StandardSourceIdColumn] = std::to_string(*sourceItemId);
            composedRows.push_back(std::move(normalizedRow));
        }
    }

    return true;
}

bool applyTableCellOverrides(
    std::vector<std::vector<std::string>> &rows,
    const std::vector<std::vector<std::string>> &patchRows,
    size_t keyColumn,
    size_t headerRow,
    std::string &errorMessage)
{
    errorMessage.clear();

    if (patchRows.empty() || cell(patchRows[0], 0) != "key" || cell(patchRows[0], 1) != "column"
        || cell(patchRows[0], 2) != "value")
    {
        errorMessage = "override patch must start with a key, column, value header";
        return false;
    }

    // Keys are matched after trimming, like the table parsers read them. Repeated keys only fail when patched.
    std::unordered_map<std::string, size_t> rowIndexByKey;
    std::unordered_set<std::string> repeatedKeys;

    const bool rowNumberKeys = keyColumn == RowNumberKeyColumn;

    for (size_t rowIndex = 0; rowIndex < rows.size() && !rowNumberKeys; ++rowIndex)
    {
        const std::string key = cell(rows[rowIndex], keyColumn);

        if (rowIndex != headerRow && !key.empty() && !rowIndexByKey.emplace(key, rowIndex).second)
        {
            repeatedKeys.insert(key);
        }
    }

    std::unordered_map<std::string, size_t> columnIndexByName;
    const std::vector<std::string> header = headerRow < rows.size() ? rows[headerRow] : std::vector<std::string>();

    for (size_t columnIndex = 0; columnIndex < header.size(); ++columnIndex)
    {
        const std::string name = cell(header, columnIndex);

        if (!name.empty() && !columnIndexByName.emplace(name, columnIndex).second)
        {
            columnIndexByName[name] = SIZE_MAX;
        }
    }

    std::unordered_set<std::string> patchedCells;

    for (size_t patchIndex = 1; patchIndex < patchRows.size(); ++patchIndex)
    {
        const std::vector<std::string> &patch = patchRows[patchIndex];
        const std::string key = cell(patch, 0);
        const std::string column = cell(patch, 1);
        const std::string line = "override line " + std::to_string(patchIndex + 1);

        if (key.empty() && column.empty())
        {
            continue;
        }

        std::optional<size_t> rowIndex;

        if (rowNumberKeys)
        {
            rowIndex = parseUnsigned(key);

            if (rowIndex && *rowIndex >= rows.size())
            {
                rows.resize(*rowIndex + 1);
            }
        }
        else if (const auto rowIt = rowIndexByKey.find(key);
                 rowIt != rowIndexByKey.end() && !repeatedKeys.contains(key))
        {
            rowIndex = rowIt->second;
        }

        if (!rowIndex || *rowIndex == headerRow)
        {
            errorMessage = line + ": key '" + key + "' must match exactly one row";
            return false;
        }

        std::optional<size_t> columnIndex;

        if (column.starts_with('#'))
        {
            columnIndex = parseUnsigned(column.substr(1));
        }
        else if (const auto columnIt = columnIndexByName.find(column);
                 columnIt != columnIndexByName.end() && columnIt->second != SIZE_MAX)
        {
            columnIndex = columnIt->second;
        }

        if (!columnIndex || *columnIndex == keyColumn)
        {
            errorMessage = line + ": column '" + column + "' is unknown, repeated in the header, or the key column";
            return false;
        }

        if (!patchedCells.insert(key + '\t' + std::to_string(*columnIndex)).second)
        {
            errorMessage = line + ": cell '" + key + "', '" + column + "' is patched twice";
            return false;
        }

        std::vector<std::string> &row = rows[*rowIndex];
        row.resize(std::max(row.size(), *columnIndex + 1));
        row[*columnIndex] = patch.size() > 2 ? patch[2] : std::string();
    }

    return true;
}

bool appendTableRows(
    std::vector<std::vector<std::string>> &rows,
    const std::vector<std::vector<std::string>> &appendedRows,
    size_t keyColumn,
    size_t headerRow,
    std::string &errorMessage)
{
    errorMessage.clear();
    std::unordered_set<std::string> keys;

    for (size_t rowIndex = 0; rowIndex < rows.size() && keyColumn != RowNumberKeyColumn; ++rowIndex)
    {
        if (rowIndex != headerRow)
        {
            keys.insert(cell(rows[rowIndex], keyColumn));
        }
    }

    for (size_t appendedIndex = 0; appendedIndex < appendedRows.size(); ++appendedIndex)
    {
        const std::vector<std::string> &row = appendedRows[appendedIndex];
        const std::string key = keyColumn != RowNumberKeyColumn ? cell(row, keyColumn) : std::string();

        if (!key.empty() && !keys.insert(key).second)
        {
            errorMessage = "appended row " + std::to_string(appendedIndex + 1) + ": key '" + key + "' already exists";
            return false;
        }

        rows.push_back(row);
    }

    return true;
}

bool appendTableColumns(
    std::vector<std::vector<std::string>> &rows,
    const std::vector<std::vector<std::string>> &appendedColumns,
    size_t keyColumn,
    size_t headerRow,
    std::string &errorMessage)
{
    errorMessage.clear();

    if (appendedColumns.empty() || headerRow >= rows.size() || keyColumn == RowNumberKeyColumn)
    {
        errorMessage = "appended columns need a header row and a key column";
        return false;
    }

    const std::vector<std::string> &names = appendedColumns.front();
    const size_t count = names.size() > keyColumn ? names.size() - 1 : 0;
    const size_t width = rows[headerRow].size();
    std::unordered_set<std::string> header;

    for (const std::string &name : rows[headerRow])
    {
        header.insert(name);
    }

    for (size_t index = 0; index < names.size(); ++index)
    {
        if (index != keyColumn && header.contains(names[index]))
        {
            errorMessage = "appended column '" + names[index] + "' already exists";
            return false;
        }
    }

    std::unordered_map<std::string, const std::vector<std::string> *> valuesByKey;

    for (size_t index = 1; index < appendedColumns.size(); ++index)
    {
        const std::vector<std::string> &row = appendedColumns[index];

        if (row.size() > names.size() || !valuesByKey.emplace(cell(row, keyColumn), &row).second)
        {
            errorMessage = "appended column row " + std::to_string(index + 1) + " is too long or repeats its key";
            return false;
        }
    }

    const auto values = [&](const std::vector<std::string> *pSource)
    {
        std::vector<std::string> added;

        for (size_t index = 0; index < names.size(); ++index)
        {
            if (index != keyColumn)
            {
                added.push_back(pSource != nullptr ? cell(*pSource, index) : std::string());
            }
        }

        return added;
    };
    size_t matched = 0;

    for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
    {
        std::vector<std::string> &row = rows[rowIndex];
        const std::vector<std::string> *pSource = nullptr;

        if (rowIndex == headerRow)
        {
            pSource = &names;
        }
        else if (const auto found = valuesByKey.find(cell(row, keyColumn)); found != valuesByKey.end())
        {
            pSource = found->second;
            ++matched;
        }

        // New columns go right after the header's; a cell past the header has no column to keep it (audit DAT-6).
        if (std::any_of(row.begin() + std::ptrdiff_t(std::min(row.size(), width)), row.end(),
                [](const std::string &value) { return !value.empty(); }))
        {
            errorMessage = "row " + std::to_string(rowIndex + 1) + " has cells past the header";
            return false;
        }

        row.resize(width);
        const std::vector<std::string> added = values(pSource);
        row.insert(row.end(), added.begin(), added.end());
    }

    if (matched != valuesByKey.size())
    {
        errorMessage = "appended columns name a key the table does not have";
        return false;
    }

    return true;
}

bool composeKeyedAppendTableRows(
    const std::vector<std::vector<std::string>> &baseRows,
    const std::vector<KeyedTableContributionRows> &contributions,
    std::vector<std::vector<std::string>> &composedRows,
    std::string &errorMessage,
    size_t baseIdColumn)
{
    composedRows.clear();
    errorMessage.clear();

    std::unordered_map<uint32_t, std::string> rowOwners;

    for (const std::vector<std::string> &row : baseRows)
    {
        const std::optional<uint32_t> rowId = parseUnsigned(cell(row, baseIdColumn));

        if (rowId && !rowOwners.emplace(*rowId, "engine").second)
        {
            errorMessage = "duplicate base row id " + std::to_string(*rowId);
            return false;
        }

        composedRows.push_back(row);
    }

    std::vector<const KeyedTableContributionRows *> sortedContributions;
    sortedContributions.reserve(contributions.size());

    for (const KeyedTableContributionRows &contribution : contributions)
    {
        if (contribution.packageId.empty() || contribution.idRange.begin == 0
            || contribution.idRange.begin > contribution.idRange.end)
        {
            errorMessage = "invalid keyed table contribution range for package '" + contribution.packageId + "'";
            return false;
        }

        sortedContributions.push_back(&contribution);
    }

    std::sort(
        sortedContributions.begin(),
        sortedContributions.end(),
        [](const KeyedTableContributionRows *pLeft, const KeyedTableContributionRows *pRight)
        {
            return pLeft->packageId < pRight->packageId;
        });

    for (size_t leftIndex = 0; leftIndex < sortedContributions.size(); ++leftIndex)
    {
        for (size_t rightIndex = leftIndex + 1; rightIndex < sortedContributions.size(); ++rightIndex)
        {
            if (rangesOverlap(
                sortedContributions[leftIndex]->idRange,
                sortedContributions[rightIndex]->idRange))
            {
                errorMessage = "overlapping keyed table id ranges for packages '"
                    + sortedContributions[leftIndex]->packageId + "' and '"
                    + sortedContributions[rightIndex]->packageId + "'";
                return false;
            }
        }
    }

    for (const KeyedTableContributionRows *pContribution : sortedContributions)
    {
        for (const std::vector<std::string> &row : pContribution->rows)
        {
            const std::optional<uint32_t> rowId = parseUnsigned(cell(row, pContribution->idColumn));

            if (!rowId)
            {
                continue;
            }

            if (*rowId < pContribution->idRange.begin || *rowId > pContribution->idRange.end)
            {
                errorMessage = "row id " + std::to_string(*rowId) + " is outside package '"
                    + pContribution->packageId + "' declared range";
                return false;
            }

            const std::pair<std::unordered_map<uint32_t, std::string>::iterator, bool> inserted =
                rowOwners.emplace(*rowId, pContribution->packageId);

            if (!inserted.second)
            {
                errorMessage = "row id " + std::to_string(*rowId) + " from package '"
                    + pContribution->packageId + "' collides with package '" + inserted.first->second + "'";
                return false;
            }

            composedRows.push_back(row);
        }
    }

    return true;
}
}
