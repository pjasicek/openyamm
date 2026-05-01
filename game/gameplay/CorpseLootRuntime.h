#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/tables/MonsterTable.h"
#include "game/ui/GameplayUiController.h"

#include <cstdint>
#include <string>

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
    uint32_t guaranteedItemId = 0);

GameplayCorpseAutoLootResult autoLootActiveCorpseView(
    IGameplayWorldRuntime &worldRuntime,
    Party &party,
    const ItemTable *pItemTable,
    GameplayUiController::HeldInventoryItemState *pHeldInventoryItem = nullptr);
}
