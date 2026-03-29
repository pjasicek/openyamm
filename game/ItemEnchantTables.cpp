#include "game/ItemEnchantTables.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
std::string trimCopy(const std::string &value)
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

std::string getCell(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return {};
    }

    return trimCopy(row[index]);
}

int parseInt(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    try
    {
        return std::stoi(value);
    }
    catch (...)
    {
        return 0;
    }
}
}

bool StandardItemEnchantTable::load(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const std::string statName = getCell(row, 0);
        const std::string suffix = getCell(row, 1);

        if (statName.empty() || suffix.empty() || statName == "Bonus Stat")
        {
            continue;
        }

        StandardItemEnchantEntry entry = {};
        entry.statName = statName;
        entry.suffix = suffix;

        for (size_t index = 0; index < entry.slotValues.size(); ++index)
        {
            entry.slotValues[index] = parseInt(getCell(row, 2 + index));
        }

        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<StandardItemEnchantEntry> &StandardItemEnchantTable::entries() const
{
    return m_entries;
}

bool SpecialItemEnchantTable::load(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const std::string name = getCell(row, 0);
        const std::string suffix = getCell(row, 1);

        if (name.empty() || suffix.empty() || name == "Bonus Stat")
        {
            continue;
        }

        SpecialItemEnchantEntry entry = {};
        entry.name = name;
        entry.suffix = suffix;

        for (size_t index = 0; index < entry.slotWeights.size(); ++index)
        {
            entry.slotWeights[index] = parseInt(getCell(row, 2 + index));
        }

        entry.value = parseInt(getCell(row, 14));
        const std::string rarityText = getCell(row, 15);
        entry.rarityLevel = rarityText.empty() ? 0 : rarityText[0];
        entry.description = getCell(row, 16);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<SpecialItemEnchantEntry> &SpecialItemEnchantTable::entries() const
{
    return m_entries;
}

}
