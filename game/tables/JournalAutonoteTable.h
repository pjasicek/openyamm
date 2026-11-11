#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class JournalAutonoteCategory : uint8_t
{
    Potion = 0,
    Fountain,
    Obelisk,
    Seer,
    Misc,
    Trainer,
};

struct JournalAutonoteEntry
{
    uint32_t id = 0;
    std::string text;
    std::string owner;
    JournalAutonoteCategory category = JournalAutonoteCategory::Misc;
};

class JournalAutonoteTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<JournalAutonoteEntry> &entries() const;

private:
    std::vector<JournalAutonoteEntry> m_entries;
};
}
