#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/tables/MonsterTable.h"
#include "game/ui/GameplayUiController.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class Party;

struct GameplayCorpseAutoLootResult
{
    bool lootedAny = false;
    bool blockedByInventory = false;
    bool empty = false;
    int goldAmount = 0;
    std::string firstItemName;
    std::string statusText;
};

GameplayCorpseViewState buildMonsterCorpseView(
    const std::string &title,
    const MonsterTable::LootPrototype &loot,
    const ItemTable *pItemTable,
    Party *pParty,
    const std::vector<uint32_t> &guaranteedItemIds = {});

// A present view with no remaining items is the persistent equivalent of the legacy Removed actor state.
bool isConsumedCorpseView(const std::optional<GameplayCorpseViewState> &corpseView);

// Gold plus the value of each item (with its enchantments) left in a corpse; the loot satchel's tier follows it.
uint32_t corpseLootValue(const GameplayCorpseViewState &corpse, const ItemTable *pItemTable, const Party *pParty);

GameplayCorpseAutoLootResult autoLootActiveCorpseView(
    IGameplayWorldRuntime &worldRuntime,
    Party &party,
    const ItemTable *pItemTable,
    GameplayUiController::HeldInventoryItemState *pHeldInventoryItem = nullptr);
}
