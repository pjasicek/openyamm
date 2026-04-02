#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct SpellFxEntry
{
    uint32_t spellId = 0;
    std::string spellName;
    std::string animationName;
};

class SpellFxTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const SpellFxEntry *findBySpellId(uint32_t spellId) const;

private:
    std::vector<SpellFxEntry> m_entries;
    std::unordered_map<uint32_t, size_t> m_entryIndexBySpellId;
};
}
