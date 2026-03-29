#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct StandardItemEnchantEntry
{
    std::string statName;
    std::string suffix;
    std::array<int, 9> slotValues = {};
};

struct SpecialItemEnchantEntry
{
    std::string name;
    std::string suffix;
    std::array<int, 12> slotWeights = {};
    int value = 0;
    char rarityLevel = 0;
    std::string description;
};

class StandardItemEnchantTable
{
public:
    bool load(const std::vector<std::vector<std::string>> &rows);
    const std::vector<StandardItemEnchantEntry> &entries() const;

private:
    std::vector<StandardItemEnchantEntry> m_entries;
};

class SpecialItemEnchantTable
{
public:
    bool load(const std::vector<std::vector<std::string>> &rows);
    const std::vector<SpecialItemEnchantEntry> &entries() const;

private:
    std::vector<SpecialItemEnchantEntry> m_entries;
};
}
