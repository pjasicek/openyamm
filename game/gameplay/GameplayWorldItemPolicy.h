#pragma once

#include "game/maps/MapItemSourceData.h"

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

// Where an item the party picked up or looted (ground, chest Take All, corpses) went: a member's bag tagged for it
// (ItemRules::bagTag, MAW's crafting bag), else the inventory as Party::tryGrantInventoryItem gives it.
struct StoredPickup
{
    size_t memberIndex = 0;
    bool taggedBag = false;
};
std::optional<StoredPickup> storePickedUpItem(Party &party, const InventoryItem &item, const ItemTable *pItemTable);
// " -- <name>" when a tagged bag of a member other than the active one took the item (zzzMaw_CraftingBag.lua:240-245).
std::string storedPickupOwnerSuffix(const Party &party, const StoredPickup &stored);
}
