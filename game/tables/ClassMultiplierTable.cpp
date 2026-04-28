#include "game/tables/ClassMultiplierTable.h"

#include "game/party/SkillData.h"
#include "game/StringUtils.h"

#include <cctype>
#include <cstdlib>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
std::string trimCopy(const std::string &text)
{
    size_t begin = 0;

    while (begin < text.size() && std::isspace(static_cast<unsigned char>(text[begin])) != 0)
    {
        ++begin;
    }

    size_t end = text.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(text[end - 1])) != 0)
    {
        --end;
    }

    return text.substr(begin, end - begin);
}

bool parseInteger(const std::string &text, int &value)
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

ClassManaMode parseManaMode(const std::string &text)
{
    const std::string mode = toLowerCopy(trimCopy(text));

    if (mode == "intellect" || mode == "intelligence")
    {
        return ClassManaMode::Intellect;
    }

    if (mode == "personality")
    {
        return ClassManaMode::Personality;
    }

    if (mode == "mixed")
    {
        return ClassManaMode::Mixed;
    }

    if (mode == "level")
    {
        return ClassManaMode::Level;
    }

    return ClassManaMode::None;
}
}

bool ClassMultiplierTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    if (rows.size() < 2)
    {
        return false;
    }

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 6)
        {
            continue;
        }

        const std::string className = canonicalClassName(row[0]);

        if (className.empty())
        {
            continue;
        }

        ClassMultiplierEntry entry = {};
        entry.className = className;
        entry.manaMode = parseManaMode(row[5]);

        if (!parseInteger(row[1], entry.baseHealth)
            || !parseInteger(row[2], entry.healthPerLevel)
            || !parseInteger(row[3], entry.baseMana)
            || !parseInteger(row[4], entry.manaPerLevel))
        {
            continue;
        }

        m_entries[className] = std::move(entry);
    }

    return !m_entries.empty();
}

const ClassMultiplierEntry *ClassMultiplierTable::get(const std::string &className) const
{
    const std::unordered_map<std::string, ClassMultiplierEntry>::const_iterator it =
        m_entries.find(canonicalClassName(className));

    if (it == m_entries.end())
    {
        return nullptr;
    }

    return &it->second;
}

const std::unordered_map<std::string, ClassMultiplierEntry> &ClassMultiplierTable::entries() const
{
    return m_entries;
}
}
