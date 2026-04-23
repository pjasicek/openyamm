#pragma once

#include "game/items/ItemGenerator.h"

#include <cstdint>
#include <functional>
#include <optional>

namespace OpenYAMM::Game
{
struct GameplayTreasureSpawnResult
{
    InventoryItem item = {};
    uint32_t goldAmount = 0;
    bool isGold = false;
};

std::optional<GameplayTreasureSpawnResult> generateTreasureSpawnItem(
    int spawnTreasureLevel,
    int mapTreasureLevel,
    uint32_t sessionSeed,
    int mapId,
    uint32_t spawnIndex,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    Party *pParty,
    const std::function<bool(const ItemDefinition &)> &filter = {});
}
