#include "game/gameplay/GameplayHeldItemController.h"

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/party/Party.h"
#include "game/tables/ItemTable.h"

#include <optional>

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
    GameplayScreenRuntime &runtime)
{
    GameplayUiController::HeldInventoryItemState &heldInventoryItem = runtime.heldInventoryItem();

    if (!heldInventoryItem.active)
    {
        return true;
    }

    Party *pParty = runtime.party();

    if (pParty != nullptr && pParty->tryGrantInventoryItem(heldInventoryItem.item))
    {
        clearHeldInventoryItem(heldInventoryItem);
        return true;
    }

    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return false;
    }

    std::optional<GameplayHeldItemDropRequest> dropRequest = pWorldRuntime->buildHeldItemDropRequest();

    if (!dropRequest)
    {
        return false;
    }

    dropRequest->item = heldInventoryItem.item;

    if (!pWorldRuntime->dropHeldItemToWorld(*dropRequest))
    {
        return false;
    }

    clearHeldInventoryItem(heldInventoryItem);
    return true;
}

void GameplayHeldItemController::applyGrantedEventItemsToHeldInventory(
    GameplayScreenRuntime &runtime,
    EventRuntimeState &eventRuntimeState,
    const ItemTable &itemTable)
{
    if (eventRuntimeState.grantedItems.empty() && eventRuntimeState.grantedItemIds.empty())
    {
        return;
    }

    if (runtime.party() == nullptr)
    {
        return;
    }

    GameplayUiController::HeldInventoryItemState &heldInventoryItem = runtime.heldInventoryItem();

    for (const InventoryItem &item : eventRuntimeState.grantedItems)
    {
        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        if (!tryDisplaceHeldInventoryItem(runtime))
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

        if (!tryDisplaceHeldInventoryItem(runtime))
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
        failureStatus = party.lastStatus().empty() || party.lastStatus() == "inventory full"
            ? "Pack is Full!"
            : party.lastStatus();
        return false;
    }

    clearHeldInventoryItem(heldInventoryItem);
    return true;
}
} // namespace OpenYAMM::Game
