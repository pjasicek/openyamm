#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct SpellEntry
{
    int id = 0;
    std::string name;
    std::string normalizedName;
    int effectSoundId = 0;
    int displayObjectId = 0;
    int impactDisplayObjectId = 0;
};

class SpellTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const SpellEntry *findById(int id) const;
    const SpellEntry *findByName(const std::string &name) const;

private:
    std::vector<SpellEntry> m_entries;
    std::unordered_map<int, size_t> m_entryIndexById;
    std::unordered_map<std::string, size_t> m_entryIndexByNormalizedName;
};
}
