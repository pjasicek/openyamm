#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct JournalHistoryEntry
{
    uint32_t id = 0;
    std::string text;
    std::string timeToken;
    std::string pageTitle;
};

class JournalHistoryTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<JournalHistoryEntry> &entries() const;
    const JournalHistoryEntry *get(uint32_t id) const;

private:
    std::vector<JournalHistoryEntry> m_entries;
};
}
