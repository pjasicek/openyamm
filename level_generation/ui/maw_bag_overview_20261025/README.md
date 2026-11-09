# Bag overview, 25 October 2026

The multibag inventory as the user redesigned it (it replaces the [compact bag view](../maw_compact_bags_20261024/README.md)
and its tabs): four bags a character, all four at once at about half size, and the 1-4 buttons to zoom one. Native
1600×900 captures from desktop runs in the user's settings (MAW Nightmare, the hints-and-rarity study party).

| View | Capture |
|---|---|
| The overview, the default: the four bags two by two at about half size, a bronze divider between them | [overview.jpg](native/overview.jpg) |
| An item held over bag 4 shrinks to the bag's size; green where it fits | [drag_over_bag4.jpg](native/drag_over_bag4.jpg) |
| Red where it would cross the divider: an item never lies in two bags | [blocked_at_divider.jpg](native/blocked_at_divider.jpg) |
| Dropped in bag 4 | [dropped_in_bag4.jpg](native/dropped_in_bag4.jpg) |
| The 4 button (or the 4 key): bag 4 at full size, its button selected | [bag4_zoomed.jpg](native/bag4_zoomed.jpg) |
| The overview button (the two by two icon), or 4 again: back to the four bags | [back_to_overview.jpg](native/back_to_overview.jpg) |
| A shop's Sell grid shows the active member's open bag, with the 1-4 buttons above it | [shop_sell_bag1.jpg](native/shop_sell_bag1.jpg) |
| Its 2 button opens bag 2 | [shop_sell_bag2.jpg](native/shop_sell_bag2.jpg) |
| The 3 key opens bag 3 there and selects no party member | [shop_sell_key3.jpg](native/shop_sell_key3.jpg) |

## How it works

- `ItemRules::bagCount` is 4 under MAW (MAW has five, and 25 for a party of one; DEVIATIONS 141). Since 2026-11-04 a
  party of one has five tabs of four, each shown as this overview ([solo tabs](../maw_solo_bag_tabs_20261104/README.md)).
  Saves from before version 121 fit their bags into four when loaded (`InventoryBags::fitIntoBagCount`): items of the
  bags past the fourth go to the first free place of the owner's bags, then of another member's; what fits nowhere
  falls at the party's feet once the world runs (`GameplayScreenController`, a status line says how many).
- `game/ui/InventoryBagOverview.h` lays the four grids out in `CharacterInventoryGrid`: square cells as large as two
  grids and the divider allow, so the overview fills the inventory area. The renderer and the input share it.
- The drop preview runs the drop on a copy of the bag (`InventoryBags::previewPlaceInBag`) at the cell the click would
  use (`InventoryBagOverview::dropCell`); a cell that would put the item past the bag's edge shows red, so nothing
  crosses a divider.
- `CharacterScreenState::inventoryBagZoomed` (not saved) says when a bag fills the grid. `CharacterInventoryBag1-4`
  zoom; the zoomed bag's button again, or `CharacterInventoryBagOverview`, returns. The overview has no open-bag frame
  (user request): the open bag is the one Sort, quests and the shop use, and its button shows it when zoomed.
- Shops and chests: `ChestInventoryBag1-4` (`chest.yml`) above the party inventory of a shop or chest transfer, and on
  a chest's own screen (the bag that takes what is moved out); they open the active member's bag
  (`GameplayPartyOverlayInputController::partyBagButtonsShown`). The chest's own screen was not captured: the debug
  console's `event` command does not open a chest view.
- Keys: the Bag 1-4 actions (`bag_1`-`bag_4`, default 1-4, MAW group, inventory context) on the inventory page and in
  a shop or chest. By default they act with Shift and the numbers alone select a party member, as in MAW
  (zzMaw-MultiBag.lua:3-25); the Controls setting Number keys (`controls.bag_number_keys`: `member` or `bag`) swaps
  them, and a party of one opens bags without Shift either way (2026-10-27; the 2026-10-25 version had only the
  swapped keys). The settings let these four take the number keys 1-5 that other actions may not.
- Right-click inspects any bag's items; the other actions work on the open bag. A spell that picks an inventory item
  shows the open bag at full size. Android shows one bag at full size (half-size cells are too small to touch); its
  1-4 buttons open the bags.

## Bag tags (GAPS H.10)

Two toggles after the 1-4 buttons tag the open bag (the zoomed one, or in the overview the one opened last; their hover
line names it): the hammer makes it a crafting bag (MAW's, zzzMaw_CraftingBag.lua; Shift+B too), the potion an alchemy
bag (ours, DEVIATIONS 178). A toggle is selected while the open bag carries its tag.

| View | Capture |
|---|---|
| Shift+B on bag 2: "Lys's bag 2 is now a crafting bag", the hammer selected, a small hammer in the corner of the 2 button | [tag_bag2_crafting_shift_b.jpg](native/tag_bag2_crafting_shift_b.jpg) |
| The potion button on bag 4: "Lys's bag 4 is now an alchemy bag" | [tag_bag4_alchemy.jpg](native/tag_bag4_alchemy.jpg) |
| The overview: the tags in each bag's bottom right corner, the place a bag fills last | [tags_overview.jpg](native/tags_overview.jpg) |
| A shop's Sell grid: the same marks on its bag buttons | [tags_shop_sell.jpg](native/tags_shop_sell.jpg) |

- A ground item the party picks up goes to a bag tagged for it (`ItemRules::bagTag`: MAW's crafting items 1041-1070;
  potions, bottles and reagents by Equip Stat Bottle or Reagent): the picker's bags first, then every other member's in
  party order, each where the item fits first; else the inventory as before. Another member's bag adds " -- <name>"
  to "You found an item (...)!". Every ground pickup goes through `storePickedUpItem` (GameplayWorldItemPolicy).
- The tags are a bit per bag in `CharacterRulesetState::craftingBags` and `alchemyBags` (save version 123). The icons
  are the game's Massive Hammer and Cure Wounds potion, cropped and cooked as `obsidian_bag_tag_crafting` and
  `obsidian_bag_tag_alchemy` (sources in assets_source/engine/icons_x2).
