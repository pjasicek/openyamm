#include "game/items/ItemEquipPosTable.h"

#include <cctype>
#include <cstdlib>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
std::string trimCopy(const std::string &value)
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

bool parseUnsigned(const std::string &text, uint32_t &value)
{
    const std::string trimmed = trimCopy(text);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(trimmed.c_str(), &pEnd, 10);

    if (pEnd == trimmed.c_str() || *pEnd != '\0')
    {
        return false;
    }

    value = static_cast<uint32_t>(parsed);
    return true;
}

bool parseSigned(const std::string &text, int &value)
{
    const std::string trimmed = trimCopy(text);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const long parsed = std::strtol(trimmed.c_str(), &pEnd, 10);

    if (pEnd == trimmed.c_str() || *pEnd != '\0')
    {
        return false;
    }

    value = static_cast<int>(parsed);
    return true;
}

std::string getCell(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return {};
    }

    return trimCopy(row[index]);
}
}

bool ItemEquipPosTable::load(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 12)
        {
            continue;
        }

        uint32_t rowId = 0;
        uint32_t itemId = 0;

        if (!parseUnsigned(getCell(row, 0), rowId) || !parseUnsigned(getCell(row, 1), itemId) || itemId == 0)
        {
            continue;
        }

        static_cast<void>(rowId);

        ItemEquipPosEntry entry = {};
        entry.itemId = itemId;

        for (size_t dollTypeId = 0; dollTypeId < 4; ++dollTypeId)
        {
            int x = 0;
            int y = 0;
            parseSigned(getCell(row, 4 + dollTypeId * 2), x);

            if (parseSigned(getCell(row, 5 + dollTypeId * 2), y))
            {
                y = -y;
            }

            entry.xByDollType[dollTypeId] = x;
            entry.yByDollType[dollTypeId] = y;
        }

        entry.xByDollType[4] = 0;
        entry.yByDollType[4] = 0;
        m_entries[itemId] = entry;
    }

    return !m_entries.empty();
}

const ItemEquipPosEntry *ItemEquipPosTable::get(uint32_t itemId) const
{
    const std::unordered_map<uint32_t, ItemEquipPosEntry>::const_iterator it = m_entries.find(itemId);
    return it != m_entries.end() ? &it->second : nullptr;
}
}
