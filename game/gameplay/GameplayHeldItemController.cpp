#include "game/gameplay/GameplayHeldItemController.h"

#include "game/events/EventRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/party/Party.h"
#include "game/tables/ItemTable.h"

namespace OpenYAMM::Game
{
namespace
{
void forceEventGrantedItemIdentificationState(InventoryItem &item, const ItemTable &itemTable)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition != nullptr && ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        item.identified = false;
    }
}
} // namespace

void GameplayHeldItemController::setHeldInventoryItem(
    GameplayUiController::HeldInventoryItemState &heldInventoryItem,
    const InventoryItem &item)
{
    heldInventoryItem.active = true;
    heldInventoryItem.item = item;
    heldInventoryItem.grabCellOffsetX = 0;
    heldInventoryItem.grabCellOffsetY = 0;
    heldInventoryItem.grabOffsetX = 0.0f;
    heldInventoryItem.grabOffsetY = 0.0f;
}

void GameplayHeldItemController::clearHeldInventoryItem(
    GameplayUiController::HeldInventoryItemState &heldInventoryItem)
{
    heldInventoryItem = {};
}

bool GameplayHeldItemController::tryDisplaceHeldInventoryItem(
    GameplayUiController::HeldInventoryItemState &heldInventoryItem,
    Party *pParty,
    const DropHeldItemCallback &dropHeldItem)
{
    if (!heldInventoryItem.active)
    {
        return true;
    }

    if (pParty != nullptr && pParty->tryGrantInventoryItem(heldInventoryItem.item))
    {
        clearHeldInventoryItem(heldInventoryItem);
        return true;
    }

    if (!dropHeldItem || !dropHeldItem(heldInventoryItem.item))
    {
        return false;
    }

    clearHeldInventoryItem(heldInventoryItem);
    return true;
}

void GameplayHeldItemController::applyGrantedEventItemsToHeldInventory(
    GameplayUiController::HeldInventoryItemState &heldInventoryItem,
    Party *pParty,
    EventRuntimeState &eventRuntimeState,
    const ItemTable &itemTable,
    const DropHeldItemCallback &dropHeldItem)
{
    if (eventRuntimeState.grantedItems.empty() && eventRuntimeState.grantedItemIds.empty())
    {
        return;
    }

    for (const InventoryItem &item : eventRuntimeState.grantedItems)
    {
        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        if (!tryDisplaceHeldInventoryItem(heldInventoryItem, pParty, dropHeldItem))
        {
            continue;
        }

        InventoryItem grantedItem = item;
        forceEventGrantedItemIdentificationState(grantedItem, itemTable);
        setHeldInventoryItem(heldInventoryItem, grantedItem);
    }

    for (uint32_t itemId : eventRuntimeState.grantedItemIds)
    {
        if (itemId == 0)
        {
            continue;
        }

        if (!tryDisplaceHeldInventoryItem(heldInventoryItem, pParty, dropHeldItem))
        {
            continue;
        }

        InventoryItem item = ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::Generic);
        forceEventGrantedItemIdentificationState(item, itemTable);
        setHeldInventoryItem(heldInventoryItem, item);
    }

    eventRuntimeState.grantedItems.clear();
    eventRuntimeState.grantedItemIds.clear();
}

bool GameplayHeldItemController::tryAutoPlaceHeldInventoryItemOnPartyMember(
    GameplayUiController::HeldInventoryItemState &heldInventoryItem,
    Party &party,
    size_t memberIndex,
    std::string &failureStatus)
{
    failureStatus.clear();

    if (!heldInventoryItem.active)
    {
        return false;
    }

    if (!party.tryAutoPlaceItemInMemberInventory(memberIndex, heldInventoryItem.item))
    {
        failureStatus = party.lastStatus().empty() ? "Inventory full" : party.lastStatus();
        return false;
    }

    clearHeldInventoryItem(heldInventoryItem);
    return true;
}
} // namespace OpenYAMM::Game
