#include "game/gameplay/GameplayWorldItemInteraction.h"

#include <algorithm>

namespace OpenYAMM::Game
{
GameplayWorldItemPickupDecision GameplayWorldItemInteraction::decidePickupDestination(
    const GameplayWorldItemPickupDecisionInput &input)
{
    GameplayWorldItemPickupDecision decision = {};

    if (input.isGold)
    {
        decision.destination = GameplayWorldItemPickupDestination::Gold;
        decision.goldAmount = static_cast<int>(std::max<uint32_t>(1u, input.goldAmount));
        return decision;
    }

    if (input.canStoreInInventory)
    {
        decision.destination = GameplayWorldItemPickupDestination::Inventory;
        return decision;
    }

    if (!input.heldItemActive)
    {
        decision.destination = GameplayWorldItemPickupDestination::HeldItem;
        return decision;
    }

    return decision;
}
} // namespace OpenYAMM::Game
