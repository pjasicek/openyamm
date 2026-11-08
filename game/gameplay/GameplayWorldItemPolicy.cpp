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
    const bool hasRequiredItems = std::all_of(
        source.requiredItems.begin(),
        source.requiredItems.end(),
        [&party](uint32_t itemId)
        {
            return party.hasItemAnywhere(itemId);
        });
    const bool hasForbiddenItem = std::any_of(
        source.forbiddenItems.begin(),
        source.forbiddenItems.end(),
        [&party](uint32_t itemId)
        {
            return party.hasItemAnywhere(itemId);
        });
    return hasRequiredQBits && !hasForbiddenQBit && hasRequiredItems && !hasForbiddenItem;
}

bool applyWorldItemPolicyActions(
    const MapWorldItemSource &source,
    const InventoryItem &randomPoolItem,
    Party &party,
    const ItemTable &itemTable)
{
    if (!worldItemPolicyAvailable(source, party) || !source.onPickupEvent.empty())
    {
        return false;
    }

    const Party::Snapshot previousParty = party.snapshot();
    for (uint32_t itemId : source.takeItems)
    {
        if (!party.removeItem(itemId))
        {
            party.restoreSnapshot(previousParty);
            return false;
        }
    }

    if (!source.randomItemPool.empty())
    {
        if (randomPoolItem.objectDescriptionId == 0 || !party.tryGrantInventoryItem(randomPoolItem))
        {
            party.restoreSnapshot(previousParty);
            return false;
        }
    }
    else
    {
        for (const MapWorldItemGrant &grant : source.grantItems)
        {
            InventoryItem item = ItemGenerator::makeInventoryItem(
                grant.itemId,
                itemTable,
                ItemGenerationMode::Generic);
            item.quantity = grant.quantity;
            if (!party.tryGrantInventoryItem(item))
            {
                party.restoreSnapshot(previousParty);
                return false;
            }
        }
    }

    for (uint32_t qbit : source.setQBits)
    {
        party.setQuestBit(qbit, true);
    }
    for (uint32_t qbit : source.clearQBits)
    {
        party.setQuestBit(qbit, false);
    }
    return true;
}

std::string formatWorldItemPickupStatusText(const InventoryItem &item, const ItemTable &itemTable)
{
    const ItemDefinition *pDefinition = itemTable.get(item.objectDescriptionId);
    const std::string itemName = pDefinition != nullptr ? ItemRuntime::foundItemName(*pDefinition) : Engine::tr("item");
    return Engine::tr("You found an item ({item})!", {{"item", itemName}});
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
