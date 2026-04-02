#include "game/tables/ReadableScrollTable.h"

#include <string>

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
}

bool ReadableScrollTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entriesByItemId.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const uint32_t itemId = parseUnsigned(getCell(row, 0));

        if (itemId == 0)
        {
            continue;
        }

        ReadableScrollEntry entry = {};
        entry.itemId = itemId;
        entry.text = getCell(row, 1);
        entry.location = getCell(row, 2);
        entry.itemName = getCell(row, 3);
        m_entriesByItemId[itemId] = std::move(entry);
    }

    return !m_entriesByItemId.empty();
}

const ReadableScrollEntry *ReadableScrollTable::get(uint32_t itemId) const
{
    const std::unordered_map<uint32_t, ReadableScrollEntry>::const_iterator it = m_entriesByItemId.find(itemId);
    return it != m_entriesByItemId.end() ? &it->second : nullptr;
}
}
