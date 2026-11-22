#include "game/gameplay/GameplayHeldItemController.h"
#include "engine/Localization.h"

#include "game/audio/SoundIds.h"
#include "game/events/EventRuntime.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/ItemRules.h"
#include "game/tables/ItemTable.h"

#include <optional>
#include <string>
#include <utility>
#include <vector>

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

std::string eventGrantedItemStatusName(const InventoryItem &item, const ItemTable &itemTable)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    return pItemDefinition != nullptr ? ItemRuntime::foundItemName(*pItemDefinition) : "item";
}

void notifyEventGrantedItemReceived(
    GameplayScreenRuntime &runtime,
    const InventoryItem &item,
    const ItemTable &itemTable)
{
    Party *pParty = runtime.party();

    if (pParty != nullptr)
    {
        pParty->requestSound(SoundId::Gold);
    }

    runtime.setStatusBarEvent(Engine::tr("You found something ({item})!",
        {{"item", eventGrantedItemStatusName(item, itemTable)}}));
}
// Drops item before the party as a player's drop does (the originals throw a displaced cursor item so too); false when
// the item may not lie on the ground or the world cannot take it.
bool throwItemToWorld(GameplayScreenRuntime &runtime, const InventoryItem &item)
{
    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();
    const ItemTable *pItemTable = runtime.itemTable();
    const ItemDefinition *pItemDefinition = pItemTable != nullptr ? pItemTable->get(item.objectDescriptionId) : nullptr;
    const bool droppable =
        pItemDefinition == nullptr || gameRulesFor(runtime.partyReadOnly()).items.canDropToWorld(item, *pItemDefinition);

    if (pWorldRuntime == nullptr || !droppable)
    {
        return false;
    }

    std::optional<GameplayHeldItemDropRequest> dropRequest = pWorldRuntime->buildHeldItemDropRequest();

    if (!dropRequest)
    {
        return false;
    }

    dropRequest->item = item;
    return pWorldRuntime->dropHeldItemToWorld(*dropRequest);
}
} // namespace

void GameplayHeldItemController::setHeldInventoryItem(
    GameplayUiController::HeldInventoryItemState &heldInventoryItem,
    const InventoryItem &item)
{
    GAMEPLAY_DEBUG_TRACE(
        "held_item_changed active=true item_id=" + std::to_string(item.objectDescriptionId)
        + " quantity=" + std::to_string(item.quantity)
        + " grid=(" + std::to_string(item.gridX) + "," + std::to_string(item.gridY) + ")"
        + " source=held_controller");
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
    if (heldInventoryItem.active)
    {
        GAMEPLAY_DEBUG_TRACE(
            "held_item_changed active=false item_id=" + std::to_string(heldInventoryItem.item.objectDescriptionId)
            + " source=held_controller");
    }

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
        GAMEPLAY_DEBUG_TRACE(
            "item_received destination=inventory source=held_displace item_id="
            + std::to_string(heldInventoryItem.item.objectDescriptionId)
            + gameplayDebugTraceItemSummary(heldInventoryItem.item.objectDescriptionId, runtime.itemTable()));
        clearHeldInventoryItem(heldInventoryItem);
        pParty->clearHeldItemForQueries();
        return true;
    }

    if (!throwItemToWorld(runtime, heldInventoryItem.item))
    {
        return false;
    }

    GAMEPLAY_DEBUG_TRACE(
        "item_received destination=world source=held_displace item_id="
        + std::to_string(heldInventoryItem.item.objectDescriptionId)
        + gameplayDebugTraceItemSummary(heldInventoryItem.item.objectDescriptionId, runtime.itemTable()));
    clearHeldInventoryItem(heldInventoryItem);
    if (pParty != nullptr)
    {
        pParty->clearHeldItemForQueries();
    }
    return true;
}

void GameplayHeldItemController::applyGrantedEventItemsToHeldInventory(
    GameplayScreenRuntime &runtime,
    EventRuntimeState &eventRuntimeState,
    const ItemTable &itemTable)
{
    if (runtime.party() == nullptr)
    {
        return;
    }

    if (eventRuntimeState.grantedItems.empty()
        && eventRuntimeState.grantedItemIds.empty()
        && !eventRuntimeState.clearHeldItemRequest
        && eventRuntimeState.takenHeldItemId == 0
        && runtime.party()->waitingGivenItems().empty())
    {
        return;
    }

    GameplayUiController::HeldInventoryItemState &heldInventoryItem = runtime.heldInventoryItem();

    // An item the event took from the cursor (EventRuntimeState::takenHeldItemId).
    if (eventRuntimeState.takenHeldItemId != 0)
    {
        if (heldInventoryItem.active && heldInventoryItem.item.objectDescriptionId == eventRuntimeState.takenHeldItemId)
        {
            clearHeldInventoryItem(heldInventoryItem);
            runtime.party()->clearHeldItemForQueries();
        }

        eventRuntimeState.takenHeldItemId = 0;
    }

    if (eventRuntimeState.clearHeldItemRequest)
    {
        clearHeldInventoryItem(heldInventoryItem);
        runtime.party()->clearHeldItemForQueries();
        eventRuntimeState.clearHeldItemRequest = false;
    }

    // A given item comes to the cursor, and the item held there goes to the packs or, when they are full, falls before
    // the party (as in MM6-MM8). When the held item can go nowhere (it may not be dropped), the given item goes to the
    // packs or to the ground itself; when it cannot either, it waits with the party (Party::waitingGivenItems, saved
    // with it) for a later frame (a pack slot freed, the held item put away). Nothing an event gives or the party
    // holds is lost.
    const auto receiveGrantedItem =
        [&runtime, &itemTable, &heldInventoryItem](InventoryItem grantedItem)
        {
            Party *pParty = runtime.party();
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
            size_t recipientMemberIndex = 0;

            if (pParty->tryGrantInventoryItem(grantedItem, &recipientMemberIndex))
            {
                notifyEventGrantedItemReceived(runtime, grantedItem, itemTable);
                GAMEPLAY_DEBUG_TRACE(
                    "item_received destination=inventory source=event item_id="
                    + std::to_string(grantedItem.objectDescriptionId)
                    + gameplayDebugTraceItemSummary(grantedItem.objectDescriptionId, &itemTable)
                    + " member_index=" + std::to_string(recipientMemberIndex));
                return true;
            }
#endif

            if (GameplayHeldItemController::tryDisplaceHeldInventoryItem(runtime))
            {
                GameplayHeldItemController::setHeldInventoryItem(heldInventoryItem, grantedItem);
                pParty->setHeldItemForQueries(grantedItem);
                notifyEventGrantedItemReceived(runtime, grantedItem, itemTable);
                GAMEPLAY_DEBUG_TRACE(
                    "item_received destination=held source=event item_id="
                    + std::to_string(grantedItem.objectDescriptionId)
                    + gameplayDebugTraceItemSummary(grantedItem.objectDescriptionId, &itemTable));
                return true;
            }

            std::string destination;

            if (pParty->tryGrantInventoryItem(grantedItem))
            {
                destination = "inventory";
            }
            else if (throwItemToWorld(runtime, grantedItem))
            {
                destination = "world";
            }
            else
            {
                return false;
            }

            notifyEventGrantedItemReceived(runtime, grantedItem, itemTable);
            GAMEPLAY_DEBUG_TRACE(
                "item_received destination=" + destination + " source=event_held_kept item_id="
                + std::to_string(grantedItem.objectDescriptionId)
                + gameplayDebugTraceItemSummary(grantedItem.objectDescriptionId, &itemTable));
            return true;
        };

    // The items that waited first, then the new ones.
    std::vector<InventoryItem> givenItems = std::move(runtime.party()->waitingGivenItems());
    runtime.party()->waitingGivenItems().clear();
    givenItems.insert(givenItems.end(), eventRuntimeState.grantedItems.begin(), eventRuntimeState.grantedItems.end());
    eventRuntimeState.grantedItems.clear();
    std::vector<InventoryItem> waitingItems;

    for (InventoryItem item : givenItems)
    {
        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        forceEventGrantedItemIdentificationState(item, itemTable);

        if (!receiveGrantedItem(item))
        {
            waitingItems.push_back(std::move(item));
        }
    }

    for (uint32_t itemId : eventRuntimeState.grantedItemIds)
    {
        if (itemId == 0)
        {
            continue;
        }

        InventoryItem item = ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::Generic);
        // A fixed item that an event gives comes identified, as in the originals (OY-182).
        item.identified = true;
        forceEventGrantedItemIdentificationState(item, itemTable);

        if (!receiveGrantedItem(item))
        {
            waitingItems.push_back(std::move(item));
        }
    }

    runtime.party()->waitingGivenItems() = std::move(waitingItems);
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
            ? Engine::tr("Pack is Full!")
            : party.lastStatus();
        return false;
    }

    clearHeldInventoryItem(heldInventoryItem);
    party.clearHeldItemForQueries();
    return true;
}
} // namespace OpenYAMM::Game
