#pragma once

#include "game/app/KeyboardBindings.h"

#include <SDL3/SDL_scancode.h>

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
struct GameplayInputFrame;
enum class BagTag : uint8_t;
class GameplayScreenRuntime;

class GameplayPartyOverlayInputController
{
public:
    static void handleUtilitySpellOverlayInput(
        GameplayScreenRuntime &context,
        const GameplayInputFrame &input);
    static void handleSpellbookOverlayInput(
        GameplayScreenRuntime &context,
        const GameplayInputFrame &input);
    static void handleCharacterOverlayInput(
        GameplayScreenRuntime &context,
        const GameplayInputFrame &input);
    // The skill the action switches on or off on the open skills page (MAW's Cover, P, and Mana Shield, M) when the
    // party member shown has it; while it does, its key's other uses (Adventurer's Inn, map) wait.
    static std::optional<std::string> skillSwitchForAction(GameplayScreenRuntime &context, KeyboardAction action);
    // Opens the Workbench (alchemy and crafting) on the open inventory, as its button does; false while an item is
    // held, which it says.
    static bool openWorkbench(GameplayScreenRuntime &context);
    // MAW's multibag keys (the Bag 1-4 actions, zzMaw-MultiBag.lua:38-67) for bag `bag` (0-3) of the open bag's tab: on
    // the inventory page the bag zooms (again, back to the overview); in a shop's or chest's inventory as
    // openNestedInventoryBag. True when the key acted there, so it does not also select a party member.
    static bool openBagForKey(GameplayScreenRuntime &context, int bag);
    // Whether the inventory page, a chest or a shop's or chest's party inventory has tabs now (a party of one with more
    // than four bags, InventoryBags::TabBags): their buttons and Shift+1-5.
    static bool bagTabsShown(const GameplayScreenRuntime &context);
    // A tab's button or Shift and its number (zzMaw-MultiBag.lua:11-14): the same bag of tab `tab` (0-based) opens.
    // True when it acted.
    static bool openBagTab(GameplayScreenRuntime &context, int tab);
    // A bag's button or key over a chest's or shop's party inventory: the active member's bag opens. A shop zooms it
    // from its bag overview, and the zoomed bag's button or key goes back to the overview.
    static void openNestedInventoryBag(GameplayScreenRuntime &context, int bag);
    // While a bag overview shows (the inventory page's or a shop's), every member's first bag of the open tab is the
    // open one, so what is put into a member fills the bags in order.
    static void openFirstBagsInOverview(GameplayScreenRuntime &context);
    // Whether a chest or a shop's or chest's party inventory shows the bag buttons (ChestInventoryBag1-4) now.
    static bool partyBagButtonsShown(const GameplayScreenRuntime &context);
    // Whether the bag keys act now: several bags, and a chest, a shop's or chest's inventory or the inventory page.
    static bool bagKeysActive(const GameplayScreenRuntime &context);
    // Whether the bag keys act only with Shift held, so that the numbers alone select a member: MAW's way and the
    // default of the bag_number_keys setting, in a party of more than one (zzMaw-MultiBag.lua:3-25).
    static bool bagKeysNeedShift(const GameplayScreenRuntime &context);
    // Tags or untags the open bag of the member the inventory page shows (the zoomed bag, or in the overview the bag
    // opened last) as a crafting or alchemy bag (zzzMaw_CraftingBag.lua:30-47), with a status line. False, with
    // nothing changed, off the inventory page or with a single bag.
    static bool toggleBagTag(GameplayScreenRuntime &context, BagTag tag);
};
} // namespace OpenYAMM::Game
