#include "game/tables/TransitionTable.h"

#include <algorithm>
#include <cctype>
#include <cstddef>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
uint32_t parseUnsigned(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(value));
    }
    catch (...)
    {
        return 0;
    }
}

std::string getCell(const std::vector<std::string> &row, size_t index)
{
    return index < row.size() ? row[index] : "";
}

std::string lowerCopy(std::string value)
{
    std::transform(value.begin(), value.end(), value.begin(),
        [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
    return value;
}
} // namespace

bool TransitionTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entriesById.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const uint32_t id = parseUnsigned(getCell(row, 0));

        if (id == 0)
        {
            continue;
        }

        TransitionEntry entry = {};
        entry.id = id;
        entry.description = getCell(row, 1);
        entry.title = getCell(row, 2);
        m_entriesById[id] = std::move(entry);
    }

    return !m_entriesById.empty();
}

bool TransitionTable::loadMapTextsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_textIdsByMapFileName.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const std::string mapFileName = lowerCopy(getCell(row, 0));
        const uint32_t id = parseUnsigned(getCell(row, 1));

        if (mapFileName.empty() || id == 0)
        {
            continue;
        }

        if (get(id) == nullptr)
        {
            return false;
        }

        m_textIdsByMapFileName[mapFileName] = id;
    }

    return true;
}

const TransitionEntry *TransitionTable::getForDestinationMap(const std::string &mapFileName) const
{
    const std::unordered_map<std::string, uint32_t>::const_iterator it =
        m_textIdsByMapFileName.find(lowerCopy(mapFileName));
    return it != m_textIdsByMapFileName.end() ? get(it->second) : nullptr;
}

const TransitionEntry *TransitionTable::get(uint32_t id) const
{
    const std::unordered_map<uint32_t, TransitionEntry>::const_iterator it = m_entriesById.find(id);
    return it != m_entriesById.end() ? &it->second : nullptr;
}
} // namespace OpenYAMM::Game
