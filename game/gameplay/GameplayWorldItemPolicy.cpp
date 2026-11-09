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
            return party.hasQuestBit(qbit);
        });
    const bool hasForbiddenQBit = std::any_of(
        source.forbiddenQBits.begin(),
        source.forbiddenQBits.end(),
        [&party](uint32_t qbit)
        {
            return party.hasQuestBit(qbit);
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
            return party.hasQuestBit(qbit);
        });
}

std::optional<StoredPickup> storePickedUpItem(Party &party, const InventoryItem &item, const ItemTable *pItemTable)
{
    const ItemRules &rules = gameRulesFor(&party).items;
    const ItemDefinition *pDefinition = pItemTable != nullptr ? pItemTable->get(item.objectDescriptionId) : nullptr;
    const std::optional<BagTag> tag = pDefinition != nullptr ? rules.bagTag(*pDefinition) : std::nullopt;

    if (tag)
    {
        if (const std::optional<size_t> owner =
                InventoryBags::placeInTaggedBag(party, party.activeMemberIndex(), item, *tag, rules.bagCount(party)))
        {
            return StoredPickup{*owner, true};
        }
    }

    size_t recipient = 0;

    if (!party.tryGrantInventoryItem(item, &recipient))
    {
        return std::nullopt;
    }

    return StoredPickup{recipient, false};
}

std::string storedPickupOwnerSuffix(const Party &party, const StoredPickup &stored)
{
    const Character *pOwner = party.member(stored.memberIndex);
    return stored.taggedBag && stored.memberIndex != party.activeMemberIndex() && pOwner != nullptr
        ? " -- " + pOwner->name
        : "";
}
}
