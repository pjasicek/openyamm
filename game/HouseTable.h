#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct HouseEntry
{
    uint32_t id = 0;
    std::string name;
};

class HouseTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    std::optional<std::string> getName(uint32_t houseId) const;

private:
    std::unordered_map<uint32_t, HouseEntry> m_entries;
};
}
