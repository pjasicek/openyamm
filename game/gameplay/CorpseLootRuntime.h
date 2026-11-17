#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/rules/CorpseLoot.h"
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
    int followerGoldShare = 0;
    std::string firstItemName;
    std::string statusText;
};

// Gold and the random item a monster carries: rolled at its death, or earlier when Telepathy reveals them. An item the
// rules' loot filter takes is turned into its gold.
GameplayCorpseViewState rollMonsterCarriedLoot(
    const std::string &title,
    const CorpseLoot &corpseLoot,
    const ItemTable *pItemTable,
    Party *pParty,
    const std::string &worldId);

// An item the rules add to a monster's loot besides the table's roll, as it lands in a corpse or on the ground.
InventoryItem corpseExtraInventoryItem(const CorpseLoot::ExtraItem &extra, const ItemTable &itemTable);

// Adds an actor's authored or event-given items; they take the place of a rolled random item.
void addGuaranteedCorpseItems(
    GameplayCorpseViewState &view,
    const ItemTable *pItemTable,
    const std::vector<uint32_t> &guaranteedItemIds);

GameplayCorpseViewState buildMonsterCorpseView(
    const std::string &title,
    const MonsterTable::LootPrototype &loot,
    const ItemTable *pItemTable,
    Party *pParty,
    const std::string &worldId,
    const std::vector<uint32_t> &guaranteedItemIds = {});

// Telepathy's status bar line: "(item), and N gold", "N gold", "(item)" or "Nothing here".
std::string telepathyLootStatusText(const GameplayCorpseViewState &loot, const ItemTable *pItemTable);

// A present view with no remaining items is the persistent equivalent of the legacy Removed actor state.
bool isConsumedCorpseView(const std::optional<GameplayCorpseViewState> &corpseView);

// Gold plus the value of each item (with its enchantments) left in a corpse; the loot satchel's tier follows it.
uint32_t corpseLootValue(const GameplayCorpseViewState &corpse, const ItemTable *pItemTable, const Party *pParty);

GameplayCorpseAutoLootResult autoLootActiveCorpseView(
    IGameplayWorldRuntime &worldRuntime,
    Party &party,
    const ItemTable *pItemTable,
    GameplayUiController::HeldInventoryItemState *pHeldInventoryItem = nullptr);

// Loots every satchel on the map into the party's bags (MAW's gather key on a completed map): all the gold, and each
// item that fits; the rest stays in its satchel. The result opens the loot summary.
GameplayUiController::LootSummaryOverlayState lootAllCorpses(IGameplayWorldRuntime &worldRuntime, Party &party);

// Takes the spotted ground items (WorldItemSpotter) into the summary of the same key press, through the loot filter:
// gold piles whole, kept items into the bags when they fit (else they stay where they lie), items it sells as their
// gold, and items it leaves on the ground stay there, no longer spotted.
void lootSpottedWorldItems(
    IGameplayWorldRuntime &worldRuntime,
    Party &party,
    GameplayUiController::LootSummaryOverlayState &summary);
}
