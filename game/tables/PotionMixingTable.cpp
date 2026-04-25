#include "game/tables/PotionMixingTable.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t FirstMixablePotionItemId = 222;
constexpr uint32_t LastMixablePotionItemId = 271;
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

bool isPotionId(uint32_t itemId)
{
    return itemId >= FirstMixablePotionItemId && itemId <= LastMixablePotionItemId;
}
}

bool PotionMixingTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_potionCombinations.clear();

    for (const std::vector<std::string> &row : rows)
    {
        uint32_t rowItemId = 0;

        if (row.empty() || !parseUnsigned(row[0], rowItemId) || !isPotionId(rowItemId))
        {
            continue;
        }

        for (uint32_t targetItemId = FirstMixablePotionItemId;
             targetItemId <= LastMixablePotionItemId;
             ++targetItemId)
        {
            const size_t columnIndex = PotionMatrixFirstColumn + targetItemId - FirstMixablePotionItemId;

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
