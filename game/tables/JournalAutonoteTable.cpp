#include "game/tables/JournalAutonoteTable.h"

#include "game/StringUtils.h"

#include <algorithm>
#include <cstdlib>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t AutoNoteVariableTag = 0x00E1u;

std::string getCell(const std::vector<std::string> &row, size_t index)
{
    return index < row.size() ? row[index] : "";
}

JournalAutonoteCategory parseCategory(const std::string &value)
{
    const std::string normalized = toLowerCopy(value);

    if (normalized == "potion")
    {
        return JournalAutonoteCategory::Potion;
    }

    if (normalized == "stat")
    {
        return JournalAutonoteCategory::Fountain;
    }

    if (normalized == "obelisk")
    {
        return JournalAutonoteCategory::Obelisk;
    }

    if (normalized == "seer")
    {
        return JournalAutonoteCategory::Seer;
    }

    if (normalized == "teacher")
    {
        return JournalAutonoteCategory::Trainer;
    }

    return JournalAutonoteCategory::Misc;
}
}

bool JournalAutonoteTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty() || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }

        char *pEnd = nullptr;
        const unsigned long parsedId = std::strtoul(row[0].c_str(), &pEnd, 10);

        if (pEnd == row[0].c_str() || *pEnd != '\0')
        {
            continue;
        }

        JournalAutonoteEntry entry = {};
        entry.noteBit = (static_cast<uint32_t>(parsedId) << 16) | AutoNoteVariableTag;
        entry.text = getCell(row, 1);
        entry.category = parseCategory(getCell(row, 2));

        if (entry.text.empty())
        {
            continue;
        }

        m_entries.push_back(std::move(entry));
    }

    std::sort(
        m_entries.begin(),
        m_entries.end(),
        [](const JournalAutonoteEntry &left, const JournalAutonoteEntry &right)
        {
            return left.noteBit < right.noteBit;
        });

    return !m_entries.empty();
}

const std::vector<JournalAutonoteEntry> &JournalAutonoteTable::entries() const
{
    return m_entries;
}
}
