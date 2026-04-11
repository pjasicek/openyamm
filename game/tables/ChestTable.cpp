#include "game/tables/ChestTable.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <limits>
#include <sstream>
#include <string>

namespace OpenYAMM::Game
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

std::string buildTextureName(int16_t textureId)
{
    if (textureId <= 0)
    {
        return {};
    }

    std::ostringstream stream;
    stream << "chest";

    if (textureId < 10)
    {
        stream << '0';
    }

    stream << textureId;
    return stream.str();
}

bool parseIntCell(const std::vector<std::string> &row, size_t index, int &value)
{
    if (index >= row.size())
    {
        return false;
    }

    const std::string trimmed = trimCopy(row[index]);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const long parsed = std::strtol(trimmed.c_str(), &pEnd, 0);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    if (parsed < std::numeric_limits<int>::min() || parsed > std::numeric_limits<int>::max())
    {
        return false;
    }

    value = static_cast<int>(parsed);
    return true;
}
}

bool ChestTable::loadRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty())
        {
            continue;
        }

        const std::string idText = trimCopy(row[0]);

        if (idText.empty() || !std::isdigit(static_cast<unsigned char>(idText[0])))
        {
            continue;
        }

        int chestTypeId = 0;

        if (!parseIntCell(row, 0, chestTypeId) || chestTypeId < 0)
        {
            return false;
        }

        if (static_cast<size_t>(chestTypeId) != m_entries.size())
        {
            return false;
        }

        int width = 0;
        int height = 0;
        int textureId = 0;
        int gridOffsetX = 0;
        int gridOffsetY = 0;
        int gridWidth = 0;
        int gridHeight = 0;

        if (!parseIntCell(row, 2, width)
            || !parseIntCell(row, 3, height)
            || !parseIntCell(row, 4, textureId)
            || !parseIntCell(row, 6, gridOffsetX)
            || !parseIntCell(row, 7, gridOffsetY)
            || !parseIntCell(row, 8, gridWidth)
            || !parseIntCell(row, 9, gridHeight))
        {
            return false;
        }

        ChestEntry entry = {};
        entry.name = row.size() > 1 ? trimCopy(row[1]) : std::string();
        entry.width = static_cast<uint8_t>(std::max(0, width));
        entry.height = static_cast<uint8_t>(std::max(0, height));
        entry.textureId = static_cast<int16_t>(textureId);
        entry.textureName = row.size() > 5 && !trimCopy(row[5]).empty()
            ? trimCopy(row[5])
            : buildTextureName(entry.textureId);
        entry.gridOffsetX = static_cast<int16_t>(gridOffsetX);
        entry.gridOffsetY = static_cast<int16_t>(gridOffsetY);
        entry.gridWidth = static_cast<uint8_t>(std::max(0, gridWidth));
        entry.gridHeight = static_cast<uint8_t>(std::max(0, gridHeight));
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const ChestEntry *ChestTable::get(uint16_t chestTypeId) const
{
    if (chestTypeId >= m_entries.size())
    {
        return nullptr;
    }

    return &m_entries[chestTypeId];
}

const std::vector<ChestEntry> &ChestTable::getEntries() const
{
    return m_entries;
}
}
