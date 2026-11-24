#include "game/gameplay/GameplayWorldItemPolicy.h"
#include "engine/Localization.h"

#include "game/items/InventoryBags.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/ItemRules.h"
#include "game/tables/ItemTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
bool worldItemPolicyAvailable(const MapWorldItemSource &source, const Party &party)
{
    const bool hasRequiredQBits = std::all_of(
        source.requiredQBits.begin(),
        source.requiredQBits.end(),
        [&party](uint32_t qbit)
        {
            return party.campaign().hasQuestBit(qbit);
        });
    const bool hasForbiddenQBit = std::any_of(
        source.forbiddenQBits.begin(),
        source.forbiddenQBits.end(),
        [&party](uint32_t qbit)
        {
            return party.campaign().hasQuestBit(qbit);
        });
    return hasRequiredQBits && !hasForbiddenQBit;
}

bool worldItemPickupAllowed(const MapWorldItemSource &source, const Party &party)
{
    return std::all_of(
        source.pickupQBits.begin(),
        source.pickupQBits.end(),
        [&party](uint32_t qbit)
        {
            return party.campaign().hasQuestBit(qbit);
        });
}

bool worldItemCollectable(const MapWorldItemSource &source, const Party &party)
{
    return source.pickupEvent == 0 && worldItemPolicyAvailable(source, party) && worldItemPickupAllowed(source, party);
}

std::optional<StoredPickup> storePickedUpItem(Party &party, const InventoryItem &item, const ItemTable *)
{
    StoredPickup stored;

    if (!party.tryGrantLootItem(item, &stored.memberIndex, &stored.pouch))
    {
        return std::nullopt;
    }

    return stored;
}
}
