#include "game/items/QuickItemSlots.h"

#include "game/items/InventoryBags.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/Party.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/PotionEffectTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace QuickItemSlots
{
bool canHold(
    const InventoryItem &item,
    const ItemTable &itemTable,
    const MergedPotionSettingTable *pPotionSettingTable,
    const MergedReagentSettingTable *pReagentSettingTable)
{
    const InventoryItemUseAction action =
        InventoryItemUseRuntime::classifyItemUse(item, itemTable, pPotionSettingTable, pReagentSettingTable);
    return action == InventoryItemUseAction::ConsumePotion || action == InventoryItemUseAction::CastScroll;
}

std::optional<Location> findItem(const Character &character, const QuickItemSlot &slot, int bagCount)
{
    if (slot.itemId == 0)
    {
        return std::nullopt;
    }

    std::optional<Location> found;
    uint16_t foundPower = 0;

    for (int bag = 0; bag < std::max(1, bagCount); ++bag)
    {
        for (const InventoryItem &item : InventoryBags::itemsInBag(character, uint8_t(bag)))
        {
            if (item.objectDescriptionId != slot.itemId)
            {
                continue;
            }

            const bool better = !found
                || (slot.bottleRule == QuickItemBottleRule::Weakest ? item.standardEnchantPower < foundPower
                                                                    : item.standardEnchantPower > foundPower);

            if (better)
            {
                found = Location{uint8_t(bag), item.gridX, item.gridY};
                foundPower = item.standardEnchantPower;
            }
        }
    }

    return found;
}

std::optional<PartyLocation> findPartyItem(
    const Party &party,
    size_t ownerIndex,
    const QuickItemSlot &slot,
    int bagCount)
{
    const std::vector<Character> &members = party.members();

    if (ownerIndex < members.size())
    {
        if (const std::optional<Location> own = findItem(members[ownerIndex], slot, bagCount))
        {
            return PartyLocation{ownerIndex, *own};
        }
    }

    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        if (memberIndex == ownerIndex)
        {
            continue;
        }

        if (const std::optional<Location> other = findItem(members[memberIndex], slot, bagCount))
        {
            return PartyLocation{memberIndex, *other};
        }
    }

    return std::nullopt;
}

size_t countPartyItems(const Party &party, const QuickItemSlot &slot, int bagCount)
{
    size_t count = 0;

    for (const Character &member : party.members())
    {
        count += countItems(member, slot, bagCount);
    }

    return count;
}

std::vector<PartyItemKind> partyItemKinds(
    const Party &party,
    const ItemTable &itemTable,
    const MergedPotionSettingTable *pPotionSettingTable,
    const MergedReagentSettingTable *pReagentSettingTable,
    int bagCount)
{
    std::vector<PartyItemKind> kinds;
    const std::vector<Character> &members = party.members();

    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        for (int bag = 0; bag < std::max(1, bagCount); ++bag)
        {
            for (const InventoryItem &item : InventoryBags::itemsInBag(members[memberIndex], uint8_t(bag)))
            {
                const InventoryItemUseAction action = InventoryItemUseRuntime::classifyItemUse(
                    item, itemTable, pPotionSettingTable, pReagentSettingTable);

                if (action != InventoryItemUseAction::ConsumePotion && action != InventoryItemUseAction::CastScroll)
                {
                    continue;
                }

                // A potion poured on items (Recharge Item, Harden Item) has nothing to drink.
                if (action == InventoryItemUseAction::ConsumePotion && pPotionSettingTable != nullptr)
                {
                    const PotionDefinition *pPotion = pPotionSettingTable->effects().find(item.objectDescriptionId);

                    if (pPotion == nullptr || pPotion->effects.empty())
                    {
                        continue;
                    }
                }

                auto kind = std::find_if(kinds.begin(), kinds.end(), [&item](const PartyItemKind &candidate)
                    {
                        return candidate.itemId == item.objectDescriptionId
                            && candidate.power == item.standardEnchantPower;
                    });

                if (kind == kinds.end())
                {
                    PartyItemKind added;
                    added.itemId = item.objectDescriptionId;
                    added.power = item.standardEnchantPower;
                    added.scroll = action == InventoryItemUseAction::CastScroll;
                    kinds.push_back(added);
                    kind = kinds.end() - 1;
                }

                ++kind->count;

                if (std::find(kind->carriers.begin(), kind->carriers.end(), memberIndex) == kind->carriers.end())
                {
                    kind->carriers.push_back(memberIndex);
                }
            }
        }
    }

    return kinds;
}

std::optional<PartyLocation> findPartyItemOfPower(
    const Party &party,
    size_t preferredIndex,
    uint32_t itemId,
    uint16_t power,
    int bagCount)
{
    const std::vector<Character> &members = party.members();
    const auto findIn = [&](size_t memberIndex) -> std::optional<PartyLocation>
    {
        for (int bag = 0; bag < std::max(1, bagCount); ++bag)
        {
            for (const InventoryItem &item : InventoryBags::itemsInBag(members[memberIndex], uint8_t(bag)))
            {
                if (item.objectDescriptionId == itemId && item.standardEnchantPower == power)
                {
                    return PartyLocation{memberIndex, Location{uint8_t(bag), item.gridX, item.gridY}};
                }
            }
        }

        return std::nullopt;
    };

    if (preferredIndex < members.size())
    {
        if (const std::optional<PartyLocation> own = findIn(preferredIndex))
        {
            return own;
        }
    }

    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        if (memberIndex != preferredIndex)
        {
            if (const std::optional<PartyLocation> other = findIn(memberIndex))
            {
                return other;
            }
        }
    }

    return std::nullopt;
}

size_t countItems(const Character &character, const QuickItemSlot &slot, int bagCount)
{
    if (slot.itemId == 0)
    {
        return 0;
    }

    size_t count = 0;

    for (int bag = 0; bag < std::max(1, bagCount); ++bag)
    {
        const std::vector<InventoryItem> &items = InventoryBags::itemsInBag(character, uint8_t(bag));
        count += size_t(std::count_if(items.begin(), items.end(),
            [&slot](const InventoryItem &item) { return item.objectDescriptionId == slot.itemId; }));
    }

    return count;
}
}
}
