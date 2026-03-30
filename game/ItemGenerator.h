#pragma once

#include "game/Party.h"

#include <functional>
#include <optional>
#include <random>

namespace OpenYAMM::Game
{
class ItemTable;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
struct ItemDefinition;

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
    static std::optional<InventoryItem> generateRandomInventoryItem(
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const ItemGenerationRequest &request,
        std::mt19937 &rng,
        const std::function<bool(const ItemDefinition &)> &filter = {});
    static std::optional<uint32_t> chooseRandomBaseItem(
        const ItemTable &itemTable,
        int treasureLevel,
        std::mt19937 &rng,
        const std::function<bool(const ItemDefinition &)> &filter = {});
};
}
