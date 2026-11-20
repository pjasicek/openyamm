#pragma once

#include "game/maps/MapItemSourceData.h"
#include "game/party/CharacterRulesetState.h"

#include <cstddef>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class Party;
class ItemTable;
struct InventoryItem;

// Whether a scene's placed world item shows: every required quest bit set and no forbidden one.
bool worldItemPolicyAvailable(const MapWorldItemSource &source, const Party &party);
// Whether a shown placed world item may be taken: every pickup quest bit set (MM9's Kira's Shield before the quest).
bool worldItemPickupAllowed(const MapWorldItemSource &source, const Party &party);
// Whether the gather key may spot and take a placed world item (WorldItemSpotter): shown, takeable and without a
// pickup event, which waits for the party's own hand.
bool worldItemCollectable(const MapWorldItemSource &source, const Party &party);

// Where an item the party picked up or looted (ground, chest Take All, corpses) went, as Party::tryGrantInventoryItem
// gives it: the party's pouch for it (ItemRules::pouch; MAW's crafting materials, potions and reagents), else the
// bags of the member named.
struct StoredPickup
{
    size_t memberIndex = 0;
    std::optional<ItemPouch> pouch;
};
std::optional<StoredPickup> storePickedUpItem(Party &party, const InventoryItem &item, const ItemTable *pItemTable);
}
