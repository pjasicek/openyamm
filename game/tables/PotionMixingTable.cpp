#include "game/tables/PotionMixingTable.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t PotionMatrixHeaderItemId = 220;
constexpr size_t PotionMatrixFirstColumn = 7;

std::string trimCopy(const std::string &text)
{
    size_t begin = 0;

    while (begin < text.size() && std::isspace(static_cast<unsigned char>(text[begin])))
    {
        ++begin;
    }

    size_t end = text.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(text[end - 1])))
    {
        --end;
    }

    return text.substr(begin, end - begin);
}

bool parseUnsigned(const std::string &text, uint32_t &value)
{
    const std::string trimmed = trimCopy(text);

    if (trimmed.empty())
    {
        return false;
    }

    for (char character : trimmed)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return false;
        }
    }

    value = static_cast<uint32_t>(std::strtoul(trimmed.c_str(), nullptr, 10));
    return true;
}

std::vector<std::pair<size_t, uint32_t>> matrixTargetColumnsFromRows(
    const std::vector<std::vector<std::string>> &rows)
{
    for (const std::vector<std::string> &row : rows)
    {
        uint32_t rowItemId = 0;

        if (!row.empty() && parseUnsigned(row[0], rowItemId) && rowItemId == PotionMatrixHeaderItemId)
        {
            std::vector<std::pair<size_t, uint32_t>> targetColumns;

            for (size_t columnIndex = PotionMatrixFirstColumn; columnIndex < row.size(); ++columnIndex)
            {
                uint32_t targetItemId = 0;

                if (parseUnsigned(row[columnIndex], targetItemId))
                {
                    targetColumns.push_back({columnIndex, targetItemId});
                }
            }

            return targetColumns;
        }
    }

    return {};
}
}

bool PotionMixingTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_potionCombinations.clear();

    const std::vector<std::pair<size_t, uint32_t>> targetColumns = matrixTargetColumnsFromRows(rows);

    if (targetColumns.empty())
    {
        return false;
    }

    std::vector<uint32_t> targetItemIds;
    targetItemIds.reserve(targetColumns.size());

    for (const std::pair<size_t, uint32_t> &targetColumn : targetColumns)
    {
        targetItemIds.push_back(targetColumn.second);
    }

    const size_t maxMatrixColumnIndex = targetColumns.back().first;

    for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
    {
        std::vector<std::string> row = rows[rowIndex];
        uint32_t rowItemId = 0;

        if (row.empty()
            || !parseUnsigned(row[0], rowItemId)
            || std::find(targetItemIds.begin(), targetItemIds.end(), rowItemId) == targetItemIds.end())
        {
            continue;
        }

        while (row.size() <= maxMatrixColumnIndex
            && rowIndex + 1 < rows.size()
            && !rows[rowIndex + 1].empty()
            && !parseUnsigned(rows[rowIndex + 1][0], rowItemId))
        {
            const std::vector<std::string> &continuationRow = rows[rowIndex + 1];

            for (size_t columnIndex = 1; columnIndex < continuationRow.size(); ++columnIndex)
            {
                row.push_back(continuationRow[columnIndex]);
            }

            ++rowIndex;
        }

        for (const std::pair<size_t, uint32_t> &targetColumn : targetColumns)
        {
            const size_t columnIndex = targetColumn.first;
            const uint32_t targetItemId = targetColumn.second;

            if (columnIndex >= row.size())
            {
                return false;
            }

            const std::string cell = trimCopy(row[columnIndex]);
            PotionCombination combination = {};

            if (cell == "no" || cell == "No" || cell == "NO")
            {
                combination.noMix = true;
            }
            else if (!cell.empty() && (cell[0] == 'E' || cell[0] == 'e'))
            {
                uint32_t damageLevel = 0;

                if (!parseUnsigned(cell.substr(1), damageLevel))
                {
                    return false;
                }

                combination.failureDamageLevel = static_cast<uint8_t>(std::min<uint32_t>(damageLevel, 255));
            }
            else
            {
                uint32_t resultItemId = 0;

                if (!parseUnsigned(cell, resultItemId))
                {
                    return false;
                }

                combination.resultItemId = resultItemId;
            }

            m_potionCombinations[key(rowItemId, targetItemId)] = combination;
        }
    }

    return !m_potionCombinations.empty();
}

size_t PotionMixingTable::combinationCount() const
{
    return m_potionCombinations.size();
}

std::vector<std::pair<uint32_t, uint32_t>> PotionMixingTable::brewingPairs() const
{
    std::vector<std::pair<uint32_t, uint32_t>> pairs;

    for (const auto &[pairKey, combination] : m_potionCombinations)
    {
        if (!combination.noMix && combination.resultItemId != 0 && combination.failureDamageLevel == 0)
        {
            pairs.push_back({uint32_t(pairKey >> 32), uint32_t(pairKey & 0xffffffffu)});
        }
    }

    std::sort(pairs.begin(), pairs.end());
    return pairs;
}

std::optional<PotionMixingTable::PotionCombination> PotionMixingTable::potionCombination(
    uint32_t heldItemId,
    uint32_t targetItemId) const
{
    const auto found = m_potionCombinations.find(key(heldItemId, targetItemId));
    return found != m_potionCombinations.end()
        ? std::optional<PotionCombination>(found->second)
        : std::nullopt;
}

uint64_t PotionMixingTable::key(uint32_t heldItemId, uint32_t targetItemId)
{
    return (static_cast<uint64_t>(heldItemId) << 32) | static_cast<uint64_t>(targetItemId);
}
}
