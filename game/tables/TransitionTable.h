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
    // Rows of transition_map_texts.txt: a destination map whose entrance window shows another entry's text.
    bool loadMapTextsFromRows(const std::vector<std::vector<std::string>> &rows);
    const TransitionEntry *get(uint32_t id) const;
    const TransitionEntry *getForDestinationMap(const std::string &mapFileName) const;

private:
    std::unordered_map<uint32_t, TransitionEntry> m_entriesById;
    std::unordered_map<std::string, uint32_t> m_textIdsByMapFileName;
};
} // namespace OpenYAMM::Game
