#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct ReadableScrollEntry
{
    uint32_t itemId = 0;
    std::string text;
    std::string location;
    std::string itemName;
};

class ReadableScrollTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const ReadableScrollEntry *get(uint32_t itemId) const;

private:
    std::unordered_map<uint32_t, ReadableScrollEntry> m_entriesByItemId;
};
}
