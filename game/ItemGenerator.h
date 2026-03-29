#pragma once

#include "game/Party.h"

#include <optional>
#include <random>

namespace OpenYAMM::Game
{
class ItemTable;

enum class ItemGenerationMode : uint8_t
{
    Generic = 0,
    Shop,
    MonsterLoot,
    ChestLoot,
};

struct ItemGenerationRequest
{
    int treasureLevel = 1;
    ItemGenerationMode mode = ItemGenerationMode::Generic;
};

class ItemGenerator
{
public:
    static InventoryItem makeInventoryItem(
        uint32_t itemId,
        const ItemTable &itemTable,
        ItemGenerationMode mode);
    static std::optional<uint32_t> chooseRandomBaseItem(
        const ItemTable &itemTable,
        int treasureLevel,
        std::mt19937 &rng);
};
}
