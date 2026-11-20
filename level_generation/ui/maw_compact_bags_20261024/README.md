# Compact bag view, 24 October 2026

Superseded on 25 October 2026 by the user's [bag overview](../maw_bag_overview_20261025/README.md): four bags, all
shown at once, and no tabs. This page records the earlier view.

The multibag inventory's second view, approved for native work by the user (GAPS H.1a). The browser mock it follows was
made in another session's scratchpad and is not kept here; these are native 1600×900 captures from desktop runs (MAW
Nightmare, the hints-and-rarity study party).

| View | Capture |
|---|---|
| The default view: the open bag at full size; the grid button left of the bag buttons switches | [full_view.jpg](native/full_view.jpg) |
| The compact view: the open tab's five bags at a third of their size, 3 + 2, each with its title, used cells and "+"; the open bag in gold; the legend in the sixth slot | [compact_view.jpg](native/compact_view.jpg) |
| An item held over a compact bag shrinks to that bag's size | [drag_over_bag3.jpg](native/drag_over_bag3.jpg) |
| Dropped there, it lies in bag 3 while bag 1 stays open | [dropped_in_bag3.jpg](native/dropped_in_bag3.jpg) |
| Bag 3's "+": the default view with bag 3 open | [bag3_opened_with_plus.jpg](native/bag3_opened_with_plus.jpg) |
| A party of one: the same view with the tabs I-V, whose line the legend adds | [compact_view_solo.jpg](native/compact_view_solo.jpg) |
| Placement preview under a held item (user request, same day): green where it fits | [preview_free.jpg](native/preview_free.jpg) |
| Gold, with the replaced item outlined, where it would swap | [preview_swap.jpg](native/preview_swap.jpg) |
| Red where it cannot go (here it would stick out of the bag) | [preview_blocked.jpg](native/preview_blocked.jpg) |

## How it works

- `InventoryBags::placeInBag` and `takeFromBag` put items into and take them out of any bag of a character, through the
  open bag's own placement (a drop on an item swaps them); the open bag stays open. `itemsInBag` and `itemInBagAt` read
  any bag.
- `InventoryBags::BagsPerTab` (5) and `BagTabs` (5) are the bag count; MAW's `bagCount` and every bag button, key and
  tab read them. Six bags per tab would fill the legend's slot (`InventoryCompactBags::HasLegend`); the bag buttons
  are layout elements, so a sixth needs a `CharacterInventoryBag6`.
- The placement preview runs the drop itself on a copy of the bag (`InventoryBags::previewPlaceInBag`), at the cell
  the click would use (`InventoryCompactBags::dropCell`, shared with the input), so what it shows is what happens.
- The legend wraps to its slot at the scale its label draws with (pixel fonts snap it) and its lines share the slot's
  height, so nothing is cut.
- `game/ui/InventoryCompactBags.h` lays the slots out inside `CharacterInventoryGrid`; the renderer and the input
  controller share it. `GameplayHudOverlaySupport::compactBagViewActive` says when the view shows.
- The choice is the `gameplay.compact_bags` setting, saved when the button switches it; a bag's "+" turns it off.
- Right-click: the open bag's items have every action (inspect, identify and the rest, a held item used on an item);
  the other bags' items are inspected only, as those actions work on the open bag. Sorting works on the open bag as
  before (Sort, Shift, Ctrl). A spell that picks an inventory item shows the open bag at full size while it picks.
- Desktop only: on Android a third of the grid is too small to touch, so the button is hidden and the setting
  ignored. Rulesets with one bag (Standard) show no button.
