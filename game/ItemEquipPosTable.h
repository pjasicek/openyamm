#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct ItemEquipPosEntry
{
    uint32_t itemId = 0;
    std::array<int, 5> xByDollType = {};
    std::array<int, 5> yByDollType = {};
};

class ItemEquipPosTable
{
public:
    bool load(const std::vector<std::vector<std::string>> &rows);
    const ItemEquipPosEntry *get(uint32_t itemId) const;

private:
    std::unordered_map<uint32_t, ItemEquipPosEntry> m_entries;
};
}
