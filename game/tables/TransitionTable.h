#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct TransitionEntry
{
    uint32_t id = 0;
    std::string description;
    std::string title;
};

class TransitionTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const TransitionEntry *get(uint32_t id) const;

private:
    std::unordered_map<uint32_t, TransitionEntry> m_entriesById;
};
} // namespace OpenYAMM::Game
