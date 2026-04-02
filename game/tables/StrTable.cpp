#include "game/tables/StrTable.h"

#include <string>
#include <vector>

namespace OpenYAMM::Game
{
bool StrTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    m_entries.clear();

    std::string content(bytes.begin(), bytes.end());
    size_t position = 0;

    while (position <= content.size())
    {
        size_t lineEnd = content.find('\n', position);

        if (lineEnd == std::string::npos)
        {
            lineEnd = content.size();
        }

        std::string line = content.substr(position, lineEnd - position);

        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        m_entries.push_back(std::move(line));

        if (lineEnd == content.size())
        {
            break;
        }

        position = lineEnd + 1;
    }

    return true;
}

const std::vector<std::string> &StrTable::getEntries() const
{
    return m_entries;
}

std::optional<std::string> StrTable::get(size_t index) const
{
    if (index >= m_entries.size())
    {
        return std::nullopt;
    }

    return m_entries[index];
}
}
