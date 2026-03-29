#pragma once

#include "engine/AssetFileSystem.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct ItemDefinition
{
    uint32_t itemId = 0;
    std::string iconName;
    std::string iconVirtualPath;
    std::string name;
    int value = 0;
    std::string equipStat;
    std::string skillGroup;
    std::string mod1;
    std::string mod2;
    int material = 0;
    std::string idRepSt;
    int identifyRepairDifficulty = 0;
    std::string unidentifiedName;
    uint16_t spriteIndex = 0;
    int varA = 0;
    int varB = 0;
    int equipX = 0;
    int equipY = 0;
    std::string notes;
    uint8_t inventoryWidth = 1;
    uint8_t inventoryHeight = 1;
    std::array<int, 6> randomTreasureWeights = {};
};

class ItemTable
{
public:
    bool load(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::vector<std::vector<std::string>> &itemRows,
        const std::vector<std::vector<std::string>> &randomItemRows
    );
    const ItemDefinition *get(uint32_t itemId) const;
    const std::vector<ItemDefinition> &entries() const;

private:
    std::vector<ItemDefinition> m_entries;
};
}
