#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class PotionMixingTable
{
public:
    struct PotionCombination
    {
        uint32_t resultItemId = 0;
        uint8_t failureDamageLevel = 0;
        bool noMix = false;
    };

    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);

    std::optional<PotionCombination> potionCombination(uint32_t heldItemId, uint32_t targetItemId) const;

private:
    static uint64_t key(uint32_t heldItemId, uint32_t targetItemId);

    std::unordered_map<uint64_t, PotionCombination> m_potionCombinations;
};
}
