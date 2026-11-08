#include "game/gameplay/CorpseLootRuntime.h"
#include "engine/Localization.h"

#include "game/gameplay/ChestRuntime.h"

#include "game/audio/SoundIds.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameplayLootFilter.h"
#include "game/gameplay/GameplayWorldItemPolicy.h"
#include "game/items/InventoryBags.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cstdint>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
struct GoldHeapVisual
{
    uint8_t width = 1;
    uint8_t height = 1;
};

GoldHeapVisual classifyGoldHeapVisual(uint32_t goldAmount)
{
    if (goldAmount <= 200)
    {
        return {1, 1};
    }

    if (goldAmount <= 1000)
    {
        return {2, 1};
    }

    return {2, 1};
}

bool isWeaponLootItem(const ItemDefinition &item)
{
    return item.equipStat == "Weapon"
        || item.equipStat == "Weapon1or2"
        || item.equipStat == "Weapon2"
        || item.equipStat == "Missile";
}

bool isArmorLootItem(const ItemDefinition &item)
{
    return item.equipStat == "Armor";
}

bool isMiscLootItem(const ItemDefinition &item)
{
    return item.skillGroup == "Misc";
}

bool itemMatchesLootKind(const ItemDefinition &item, MonsterTable::LootItemKind kind)
{
    switch (kind)
    {
        case MonsterTable::LootItemKind::None:
            return false;

        case MonsterTable::LootItemKind::Any:
            return true;

        case MonsterTable::LootItemKind::Weapon:
            return isWeaponLootItem(item);

        case MonsterTable::LootItemKind::Armor:
            return isArmorLootItem(item);

        case MonsterTable::LootItemKind::Misc:
            return isMiscLootItem(item);

        case MonsterTable::LootItemKind::Gem:
            return item.equipStat == "Gem";

        case MonsterTable::LootItemKind::Ring:
            return item.equipStat == "Ring";

        case MonsterTable::LootItemKind::Amulet:
            return item.equipStat == "Amulet";

        case MonsterTable::LootItemKind::Boots:
            return item.equipStat == "Boots";

        case MonsterTable::LootItemKind::Helm:
            return item.equipStat == "Helm";

        case MonsterTable::LootItemKind::Belt:
            return item.equipStat == "Belt";

        case MonsterTable::LootItemKind::Cloak:
            return item.equipStat == "Cloak";

        case MonsterTable::LootItemKind::Gauntlets:
            return item.equipStat == "Gauntlets";

        case MonsterTable::LootItemKind::Shield:
            return item.equipStat == "Shield";

        case MonsterTable::LootItemKind::Wand:
            return item.equipStat == "WeaponW";

        case MonsterTable::LootItemKind::Ore:
            return item.equipStat == "Ore";

        case MonsterTable::LootItemKind::Scroll:
            return item.equipStat == "Sscroll";

        case MonsterTable::LootItemKind::Sword:
            return item.skillGroup == "Sword";

        case MonsterTable::LootItemKind::Dagger:
            return item.skillGroup == "Dagger";

        case MonsterTable::LootItemKind::Axe:
            return item.skillGroup == "Axe";

        case MonsterTable::LootItemKind::Spear:
            return item.skillGroup == "Spear";

        case MonsterTable::LootItemKind::Mace:
            return item.skillGroup == "Mace";

        case MonsterTable::LootItemKind::Club:
            return item.skillGroup == "Club";

        case MonsterTable::LootItemKind::Staff:
            return item.skillGroup == "Staff";

        case MonsterTable::LootItemKind::Bow:
            return item.skillGroup == "Bow";

        case MonsterTable::LootItemKind::Leather:
            return item.skillGroup == "Leather";

        case MonsterTable::LootItemKind::Chain:
            return item.skillGroup == "Chain";

        case MonsterTable::LootItemKind::Plate:
            return item.skillGroup == "Plate";
    }

    return false;
}

std::string foundItemStatusText(int goldAmount, const std::string &itemName)
{
    const std::string resolvedItemName = itemName.empty() ? Engine::tr("item") : itemName;

    if (goldAmount <= 0)
    {
        return Engine::tr("You found an item ({item})!", {{"item", resolvedItemName}});
    }

    return Engine::tr("You found {gold} gold and an item ({item})!",
        {{"gold", int64_t(goldAmount)}, {"item", resolvedItemName}});
}

std::string corpseLootItemName(const GameplayChestItemState &item, const ItemTable *pItemTable)
{
    const ItemDefinition *pItemDefinition =
        pItemTable != nullptr ? pItemTable->get(item.itemId) : nullptr;

    return pItemDefinition != nullptr ? ItemRuntime::foundItemName(*pItemDefinition) : Engine::tr("item");
}

InventoryItem normalizedCorpseInventoryItem(const GameplayChestItemState &item)
{
    InventoryItem inventoryItem = item.item;

    if (inventoryItem.objectDescriptionId == 0)
    {
        inventoryItem.objectDescriptionId = item.itemId;
    }

    if (inventoryItem.quantity == 0)
    {
        inventoryItem.quantity = item.quantity;
    }

    if (inventoryItem.width == 0)
    {
        inventoryItem.width = item.width;
    }

    if (inventoryItem.height == 0)
    {
        inventoryItem.height = item.height;
    }

    return inventoryItem;
}

bool displaceHeldItemToWorld(
    IGameplayWorldRuntime &worldRuntime,
    GameplayUiController::HeldInventoryItemState &heldInventoryItem,
    const ItemTable *pItemTable)
{
    if (!heldInventoryItem.active)
    {
        return true;
    }

    const ItemDefinition *pItemDefinition = pItemTable != nullptr
        ? pItemTable->get(heldInventoryItem.item.objectDescriptionId)
        : nullptr;

    if (pItemDefinition != nullptr && !ItemRuntime::canDrop(*pItemDefinition))
    {
        return false;
    }

    std::optional<GameplayHeldItemDropRequest> dropRequest = worldRuntime.buildHeldItemDropRequest();

    if (!dropRequest)
    {
        return false;
    }

    dropRequest->item = heldInventoryItem.item;

    if (!worldRuntime.dropHeldItemToWorld(*dropRequest))
    {
        return false;
    }

    GAMEPLAY_DEBUG_TRACE(
        "held_item_changed active=false item_id=" + std::to_string(heldInventoryItem.item.objectDescriptionId)
        + " source=corpse_loot_drop");
    heldInventoryItem = {};
    return true;
}

void setHeldInventoryItem(
    GameplayUiController::HeldInventoryItemState &heldInventoryItem,
    const InventoryItem &item)
{
    GAMEPLAY_DEBUG_TRACE(
        "held_item_changed active=true item_id=" + std::to_string(item.objectDescriptionId)
        + " quantity=" + std::to_string(item.quantity)
        + " grid=(" + std::to_string(item.gridX) + "," + std::to_string(item.gridY) + ")"
        + " source=corpse_loot");
    heldInventoryItem.active = true;
    heldInventoryItem.item = item;
    heldInventoryItem.grabCellOffsetX = 0;
    heldInventoryItem.grabCellOffsetY = 0;
    heldInventoryItem.grabOffsetX = 0.0f;
    heldInventoryItem.grabOffsetY = 0.0f;
}
}

GameplayCorpseViewState rollMonsterCarriedLoot(
    const std::string &title,
    const CorpseLoot &corpseLoot,
    const ItemTable *pItemTable,
    Party *pParty,
    const std::string &worldId)
{
    GameplayCorpseViewState view = {};
    view.title = title;
    const MonsterTable::LootPrototype &loot = corpseLoot.loot;

    static thread_local std::mt19937 freeRng(std::random_device{}());
    std::mt19937 seededRng;

    if (corpseLoot.seed)
    {
        std::seed_seq sequence{uint32_t(*corpseLoot.seed), uint32_t(*corpseLoot.seed >> 32)};
        seededRng.seed(sequence);
    }

    std::mt19937 &rng = corpseLoot.seed ? seededRng : freeRng;

    if (loot.goldDiceRolls > 0 && loot.goldDiceSides > 0)
    {
        GameplayChestItemState goldItem = {};
        goldItem.isGold = true;
        goldItem.goldRollCount = loot.goldDiceRolls;

        for (int roll = 0; roll < loot.goldDiceRolls; ++roll)
        {
            goldItem.goldAmount += uint32_t(std::uniform_int_distribution<int>(1, loot.goldDiceSides)(rng));
        }

        if (goldItem.goldAmount > 0)
        {
            const GoldHeapVisual goldVisual = classifyGoldHeapVisual(goldItem.goldAmount);
            goldItem.width = goldVisual.width;
            goldItem.height = goldVisual.height;
            view.items.push_back(goldItem);
        }
    }

    const StandardItemEnchantTable *pStandardItemEnchantTable =
        pParty != nullptr ? pParty->standardItemEnchantTable() : nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable =
        pParty != nullptr ? pParty->specialItemEnchantTable() : nullptr;

    if (loot.itemChance > 0
        && loot.itemLevel > 0
        && std::uniform_int_distribution<int>(0, 99)(rng) < loot.itemChance)
    {
        const std::optional<InventoryItem> generatedItem =
            pItemTable != nullptr && pStandardItemEnchantTable != nullptr && pSpecialItemEnchantTable != nullptr
            ? ItemGenerator::generateRandomInventoryItem(
                *pItemTable,
                *pStandardItemEnchantTable,
                *pSpecialItemEnchantTable,
                ItemGenerationRequest{
                    .treasureLevel = loot.itemLevel,
                    .mode = ItemGenerationMode::MonsterLoot,
                    .worldId = worldId,
                    .dropLevel = corpseLoot.dropLevel,
                    .boss = corpseLoot.boss,
                    .omnipotent = corpseLoot.omnipotent,
                },
                pParty,
                rng,
                [kind = loot.itemKind](const ItemDefinition &entry)
                {
                    return itemMatchesLootKind(entry, kind);
                })
            : std::nullopt;

        std::optional<InventoryItem> droppedItem = generatedItem;
        const ItemDefinition *pGeneratedDefinition =
            droppedItem && pItemTable != nullptr ? pItemTable->get(droppedItem->objectDescriptionId) : nullptr;
        const FilteredLoot filtered = pGeneratedDefinition != nullptr
            ? filterDroppedLoot(
                  *droppedItem, *pGeneratedDefinition, pParty, pStandardItemEnchantTable, pSpecialItemEnchantTable)
            : FilteredLoot{};

        if (filtered.verdict == LootFilterVerdict::Gold)
        {
            // The filtered drop is added to the corpse's gold.
            const int filteredGold = int(filtered.gold);
            auto goldIt = std::find_if(
                view.items.begin(),
                view.items.end(),
                [](const GameplayChestItemState &item)
                {
                    return item.isGold;
                });

            if (goldIt == view.items.end())
            {
                GameplayChestItemState goldItem = {};
                goldItem.isGold = true;
                view.items.push_back(goldItem);
                goldIt = view.items.end() - 1;
            }

            goldIt->goldAmount += uint32_t(std::max(1, filteredGold));
            const GoldHeapVisual goldVisual = classifyGoldHeapVisual(goldIt->goldAmount);
            goldIt->width = goldVisual.width;
            goldIt->height = goldVisual.height;
        }
        else if (droppedItem && droppedItem->objectDescriptionId != 0)
        {
            GameplayChestItemState item = {};
            item.item = *droppedItem;
            item.itemId = item.item.objectDescriptionId;
            item.quantity = item.item.quantity;
            view.items.push_back(item);
        }
    }

    for (const CorpseLoot::ExtraItem &extra : corpseLoot.extraItems)
    {
        if (pItemTable == nullptr || pItemTable->get(extra.itemId) == nullptr)
        {
            continue;
        }

        GameplayChestItemState item = {};
        item.item = corpseExtraInventoryItem(extra, *pItemTable);
        item.itemId = item.item.objectDescriptionId;
        item.quantity = item.item.quantity;
        view.items.push_back(item);
    }

    return view;
}

InventoryItem corpseExtraInventoryItem(const CorpseLoot::ExtraItem &extra, const ItemTable &itemTable)
{
    InventoryItem item = ItemGenerator::makeInventoryItem(extra.itemId, itemTable, ItemGenerationMode::MonsterLoot);
    item.rulesetFields.craftState = extra.craftState;
    item.rulesetFields.dropLevel = extra.dropLevel;
    item.standardEnchantPower = extra.potionPower > 0 ? extra.potionPower : item.standardEnchantPower;

    if (extra.rulesetFields)
    {
        item.rulesetFields = *extra.rulesetFields;
    }

    return item;
}

void addGuaranteedCorpseItems(
    GameplayCorpseViewState &view,
    const ItemTable *pItemTable,
    const std::vector<uint32_t> &guaranteedItemIds)
{
    const bool hasGuaranteedItems =
        std::any_of(
            guaranteedItemIds.begin(),
            guaranteedItemIds.end(),
            [](uint32_t itemId)
            {
                return itemId != 0;
            });

    if (!hasGuaranteedItems || pItemTable == nullptr)
    {
        return;
    }

    std::erase_if(
        view.items,
        [](const GameplayChestItemState &item)
        {
            return !item.isGold;
        });

    static thread_local std::mt19937 rng(std::random_device{}());

    for (uint32_t guaranteedItemId : guaranteedItemIds)
    {
        if (guaranteedItemId == 0)
        {
            continue;
        }

        InventoryItem inventoryItem =
            ItemGenerator::makeInventoryItem(guaranteedItemId, *pItemTable, ItemGenerationMode::MonsterLoot);
        ItemGenerator::assignMonsterPotionPower(inventoryItem, *pItemTable, rng);

        if (inventoryItem.objectDescriptionId != 0)
        {
            GameplayChestItemState item = {};
            item.item = inventoryItem;
            item.itemId = inventoryItem.objectDescriptionId;
            item.quantity = inventoryItem.quantity;
            item.width = inventoryItem.width;
            item.height = inventoryItem.height;
            view.items.push_back(item);
        }
    }
}

GameplayCorpseViewState buildMonsterCorpseView(
    const std::string &title,
    const MonsterTable::LootPrototype &loot,
    const ItemTable *pItemTable,
    Party *pParty,
    const std::string &worldId,
    const std::vector<uint32_t> &guaranteedItemIds)
{
    GameplayCorpseViewState view = rollMonsterCarriedLoot(title, CorpseLoot{loot}, pItemTable, pParty, worldId);
    addGuaranteedCorpseItems(view, pItemTable, guaranteedItemIds);
    return view;
}

std::string telepathyLootStatusText(const GameplayCorpseViewState &loot, const ItemTable *pItemTable)
{
    uint32_t goldAmount = 0;
    std::string itemName;

    for (const GameplayChestItemState &item : loot.items)
    {
        if (item.isGold)
        {
            goldAmount += item.goldAmount;
        }
        else if (itemName.empty())
        {
            itemName = corpseLootItemName(item, pItemTable);
        }
    }

    if (itemName.empty())
    {
        return goldAmount > 0 ? Engine::tr("{gold} gold", {{"gold", int64_t(goldAmount)}}) : Engine::tr("Nothing here");
    }

    return goldAmount > 0 ? Engine::tr("({item}), and {gold} gold", {{"item", itemName}, {"gold", int64_t(goldAmount)}})
                          : Engine::tr("({item})", {{"item", itemName}});
}

bool isConsumedCorpseView(const std::optional<GameplayCorpseViewState> &corpseView)
{
    return corpseView.has_value() && corpseView->items.empty();
}

uint32_t corpseLootValue(const GameplayCorpseViewState &corpse, const ItemTable *pItemTable, const Party *pParty)
{
    uint32_t value = 0;
    for (const GameplayChestItemState &item : corpse.items)
    {
        value += uint32_t(std::max(0, chestItemValue(item, pItemTable,
            pParty != nullptr ? pParty->standardItemEnchantTable() : nullptr,
            pParty != nullptr ? pParty->specialItemEnchantTable() : nullptr)));
    }
    return value;
}

GameplayCorpseAutoLootResult autoLootActiveCorpseView(
    IGameplayWorldRuntime &worldRuntime,
    Party &party,
    const ItemTable *pItemTable,
    GameplayUiController::HeldInventoryItemState *pHeldInventoryItem)
{
    GameplayCorpseAutoLootResult result = {};

    while (const GameplayCorpseViewState *pCorpseView = worldRuntime.activeCorpseView())
    {
        if (pCorpseView->items.empty())
        {
            break;
        }

        const GameplayChestItemState &item = pCorpseView->items.front();

        if (item.isGold)
        {
            GameplayChestItemState removedItem = {};

            if (!worldRuntime.takeActiveCorpseItem(0, removedItem))
            {
                break;
            }

            const FoundGold foundGold = resolveFoundGold(removedItem.goldAmount, worldRuntime.eventRuntimeState(), &party);
            party.addGold(static_cast<int>(foundGold.partyAmount), GoldReason::LootCorpse);
            result.goldAmount += static_cast<int>(foundGold.amount);
            result.followerGoldShare += static_cast<int>(foundGold.followerShare);
            result.lootedAny = result.lootedAny || foundGold.amount > 0;
            GAMEPLAY_DEBUG_TRACE(
                "gold_received destination=party source=corpse"
                " corpse_index=" + std::to_string(pCorpseView->sourceIndex)
                + " amount=" + std::to_string(foundGold.partyAmount));
            continue;
        }

        const InventoryItem inventoryItem = normalizedCorpseInventoryItem(item);
        const std::string itemName = corpseLootItemName(item, pItemTable);

        if (const std::optional<StoredPickup> stored = storePickedUpItem(party, inventoryItem, pItemTable))
        {
            GameplayChestItemState removedItem = {};

            if (!worldRuntime.takeActiveCorpseItem(0, removedItem))
            {
                break;
            }

            GAMEPLAY_DEBUG_TRACE(
                "item_received destination=inventory source=corpse item_id="
                + std::to_string(inventoryItem.objectDescriptionId)
                + gameplayDebugTraceItemSummary(inventoryItem.objectDescriptionId, pItemTable)
                + " corpse_index=" + std::to_string(pCorpseView->sourceIndex)
                + " loot_item_index=0"
                + " member_index=" + std::to_string(stored->memberIndex));

            if (result.firstItemName.empty())
            {
                result.firstItemName = itemName;
            }

            result.lootedAny = true;
            continue;
        }

        if (pHeldInventoryItem != nullptr
            && displaceHeldItemToWorld(worldRuntime, *pHeldInventoryItem, pItemTable))
        {
            GameplayChestItemState removedItem = {};

            if (!worldRuntime.takeActiveCorpseItem(0, removedItem))
            {
                break;
            }

            setHeldInventoryItem(*pHeldInventoryItem, normalizedCorpseInventoryItem(removedItem));
            party.setHeldItemForQueries(pHeldInventoryItem->item);
            GAMEPLAY_DEBUG_TRACE(
                "item_received destination=held source=corpse item_id="
                + std::to_string(pHeldInventoryItem->item.objectDescriptionId)
                + gameplayDebugTraceItemSummary(pHeldInventoryItem->item.objectDescriptionId, pItemTable)
                + " corpse_index=" + std::to_string(pCorpseView->sourceIndex)
                + " loot_item_index=0");

            if (result.firstItemName.empty())
            {
                result.firstItemName = itemName;
            }

            result.lootedAny = true;
            result.blockedByInventory = true;
            break;
        }

        result.blockedByInventory = true;
        break;
    }

    // Gold pickups already queue this sound through Party::addGold.
    if (result.lootedAny && result.goldAmount == 0)
    {
        party.requestSound(SoundId::Gold);
    }

    if (!result.firstItemName.empty())
    {
        result.statusText = foundItemStatusText(result.goldAmount, result.firstItemName);
    }
    else if (result.goldAmount > 0)
    {
        FoundGold foundGold = {};
        foundGold.amount = static_cast<uint32_t>(result.goldAmount);
        foundGold.followerShare = static_cast<uint32_t>(result.followerGoldShare);
        result.statusText = foundGoldStatusText(foundGold);
    }
    else if (result.blockedByInventory)
    {
        result.statusText = party.lastStatus().empty() || party.lastStatus() == "inventory full"
            ? Engine::tr("Pack is Full!")
            : party.lastStatus();
    }
    else
    {
        result.empty = true;
    }

    worldRuntime.closeActiveCorpseView();
    return result;
}

namespace
{
// How many items each member's bags hold, to find where a granted item went.
std::vector<std::vector<size_t>> memberBagSizes(const Party &party, int bagCount)
{
    std::vector<std::vector<size_t>> sizes(party.members().size());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        for (int bag = 0; bag < bagCount; ++bag)
        {
            sizes[memberIndex].push_back(InventoryBags::itemsInBag(party.members()[memberIndex], uint8_t(bag)).size());
        }
    }

    return sizes;
}

// The bag of the recipient that gained an item, and the cell of that item: a placed item ends its bag's list.
GameplayUiController::LootedItemPlace grantedItemPlace(
    const Party &party,
    size_t recipientIndex,
    int bagCount,
    const std::vector<std::vector<size_t>> &bagSizesBefore)
{
    GameplayUiController::LootedItemPlace place = {};
    place.memberIndex = recipientIndex;

    if (recipientIndex >= party.members().size() || recipientIndex >= bagSizesBefore.size())
    {
        return place;
    }

    const Character &recipient = party.members()[recipientIndex];

    for (int bag = 0; bag < bagCount && size_t(bag) < bagSizesBefore[recipientIndex].size(); ++bag)
    {
        const std::vector<InventoryItem> &items = InventoryBags::itemsInBag(recipient, uint8_t(bag));

        if (items.size() > bagSizesBefore[recipientIndex][size_t(bag)])
        {
            place.bag = uint8_t(bag);
            place.gridX = items.back().gridX;
            place.gridY = items.back().gridY;
            break;
        }
    }

    return place;
}
}

GameplayUiController::LootSummaryOverlayState lootAllCorpses(IGameplayWorldRuntime &worldRuntime, Party &party)
{
    GameplayUiController::LootSummaryOverlayState summary = {};
    const int bagCount = party.rules().items.bagCount(party);
    // Added once after the sweep: each addGold queues the gold sound.
    int partyGold = 0;

    for (size_t actorIndex : worldRuntime.lootableCorpseActorIndices())
    {
        if (!worldRuntime.openActorCorpseView(actorIndex))
        {
            continue;
        }

        ++summary.satchelCount;
        size_t itemIndex = 0;

        // Taking a satchel's last item closes its view.
        for (const GameplayCorpseViewState *pView = worldRuntime.activeCorpseView();
             pView != nullptr && itemIndex < pView->items.size();
             pView = worldRuntime.activeCorpseView())
        {
            const GameplayChestItemState &item = pView->items[itemIndex];
            GameplayChestItemState taken = {};

            if (item.isGold)
            {
                if (!worldRuntime.takeActiveCorpseItem(itemIndex, taken))
                {
                    break;
                }

                const FoundGold foundGold = resolveFoundGold(taken.goldAmount, worldRuntime.eventRuntimeState(), &party);
                partyGold += static_cast<int>(foundGold.partyAmount);
                summary.goldAmount += static_cast<int>(foundGold.amount);
                summary.followerGoldShare += static_cast<int>(foundGold.followerShare);
                continue;
            }

            const InventoryItem inventoryItem = normalizedCorpseInventoryItem(item);
            const std::vector<std::vector<size_t>> bagSizes = memberBagSizes(party, bagCount);
            const std::optional<StoredPickup> stored = storePickedUpItem(party, inventoryItem, party.itemTable());

            if (!stored)
            {
                summary.leftItems.push_back(inventoryItem);
                ++itemIndex;
                continue;
            }

            if (!worldRuntime.takeActiveCorpseItem(itemIndex, taken))
            {
                break;
            }

            summary.takenItems.push_back(inventoryItem);
            summary.takenItemPlaces.push_back(grantedItemPlace(party, stored->memberIndex, bagCount, bagSizes));
        }

        worldRuntime.closeActiveCorpseView();
    }

    if (partyGold > 0)
    {
        party.addGold(partyGold, GoldReason::LootCorpse);
    }
    else if (!summary.takenItems.empty())
    {
        party.requestSound(SoundId::Gold);
    }

    summary.active = summary.satchelCount > 0;
    return summary;
}
}
