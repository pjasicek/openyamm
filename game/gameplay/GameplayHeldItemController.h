#pragma once

#include "game/ui/GameplayUiController.h"

#include <cstddef>
#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class ItemTable;
class Party;
struct EventRuntimeState;

class GameplayHeldItemController
{
public:
    static void setHeldInventoryItem(
        GameplayUiController::HeldInventoryItemState &heldInventoryItem,
        const InventoryItem &item);
    static void clearHeldInventoryItem(GameplayUiController::HeldInventoryItemState &heldInventoryItem);

    static bool tryDisplaceHeldInventoryItem(
        GameplayScreenRuntime &runtime);
    static void applyGrantedEventItemsToHeldInventory(
        GameplayScreenRuntime &runtime,
        EventRuntimeState &eventRuntimeState,
        const ItemTable &itemTable);
    static bool tryAutoPlaceHeldInventoryItemOnPartyMember(
        GameplayUiController::HeldInventoryItemState &heldInventoryItem,
        Party &party,
        size_t memberIndex,
        std::string &failureStatus);
};
} // namespace OpenYAMM::Game
