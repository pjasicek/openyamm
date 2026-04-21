#pragma once

#include "game/ui/GameplayUiController.h"

#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>

namespace OpenYAMM::Game
{
class ItemTable;
class Party;
struct EventRuntimeState;

class GameplayHeldItemController
{
public:
    using DropHeldItemCallback = std::function<bool(const InventoryItem &item)>;

    static void setHeldInventoryItem(
        GameplayUiController::HeldInventoryItemState &heldInventoryItem,
        const InventoryItem &item);
    static void clearHeldInventoryItem(GameplayUiController::HeldInventoryItemState &heldInventoryItem);

    static bool tryDisplaceHeldInventoryItem(
        GameplayUiController::HeldInventoryItemState &heldInventoryItem,
        Party *pParty,
        const DropHeldItemCallback &dropHeldItem);
    static void applyGrantedEventItemsToHeldInventory(
        GameplayUiController::HeldInventoryItemState &heldInventoryItem,
        Party *pParty,
        EventRuntimeState &eventRuntimeState,
        const ItemTable &itemTable,
        const DropHeldItemCallback &dropHeldItem);
    static bool tryAutoPlaceHeldInventoryItemOnPartyMember(
        GameplayUiController::HeldInventoryItemState &heldInventoryItem,
        Party &party,
        size_t memberIndex,
        std::string &failureStatus);
};
} // namespace OpenYAMM::Game
