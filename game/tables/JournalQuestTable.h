#pragma once

#include <cstdint>
#include <vector>
#include <string>

namespace OpenYAMM::Game
{
struct JournalQuestEntry
{
    uint32_t qbitId = 0;
    std::string text;
    std::string notes;
    std::string owner;
};

class JournalQuestTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<JournalQuestEntry> &entries() const;
    bool hasQuestText(uint32_t qbitId) const;

private:
    std::vector<JournalQuestEntry> m_entries;
};
}
