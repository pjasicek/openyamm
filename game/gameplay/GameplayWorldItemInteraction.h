#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
enum class GameplayWorldItemPickupDestination
{
    None,
    Gold,
    Inventory,
    HeldItem,
};

struct GameplayWorldItemPickupDecisionInput
{
    bool isGold = false;
    uint32_t goldAmount = 0;
    bool canStoreInInventory = false;
    bool heldItemActive = false;
};

struct GameplayWorldItemPickupDecision
{
    GameplayWorldItemPickupDestination destination = GameplayWorldItemPickupDestination::None;
    int goldAmount = 0;
};

class GameplayWorldItemInteraction
{
public:
    static GameplayWorldItemPickupDecision decidePickupDestination(
        const GameplayWorldItemPickupDecisionInput &input);
};
} // namespace OpenYAMM::Game
