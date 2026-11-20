# A party of one's bag tabs, 4 November 2026

A player request: under MAW a party of one has five inventory tabs, as in MAW, not one. The user agreed on
2026-11-04 to five tabs of **four** bags (MAW has five tabs of five; "4 bags are enough"), so each tab is the
[bag overview](../maw_bag_overview_20261025/README.md) of 2026-10-25 unchanged. A party keeps four bags a member.

[mockup_top_bar_tabs.jpg](mockup_top_bar_tabs.jpg) is the mockup the user approved: the I-V buttons after the bag tag
buttons, the item search narrowed after them.

## In game

Native 1600×900 captures of a player's MAW save (a party of one in Free Haven) with `debug.menu_input_tour_path`.

| View | Capture |
|---|---|
| Tab I, the overview of bags 1-4 as before | [tab1.jpg](tab1.jpg) |
| Tab II selected, the pointer on IV: "Tab IV (Shift+4)" | [tab2_hover_tab4.jpg](tab2_hover_tab4.jpg) |
| A scroll picked up in tab I, tab II's button clicked while holding it, dropped in tab II's first bag | [scroll_moved_to_tab2.jpg](scroll_moved_to_tab2.jpg) |
| Tab I again: the scroll is gone from it | [back_to_tab1.jpg](back_to_tab1.jpg) |

## How it works

- `MawItemRules::bagCount` is 20 for a party of one and 4 otherwise; `InventoryBags::TabBags` is 4 and
  `tabCount(bagCount)` the number of tabs. The open bag (`CharacterRulesetState::currentBag`) decides the tab, so
  nothing new is saved.
- The overview, the 1-4 buttons and keys, and a chest's or shop's bag buttons (`ChestInventoryBag1-4`) show and open
  the bags of the open bag's tab (`InventoryBagOverview::firstBag`; `slot()` takes the bag and places it by
  `bag % 4`). While an overview shows, each member's open bag is the first of their tab.
- `CharacterInventoryTab1-5` (`character.yml`) and Shift+1-5 open the same bag of another tab, as MAW keeps it
  (zzMaw-MultiBag.lua:153-157; `GameplayPartyOverlayInputController::openBagTab`). The keys work on the inventory
  page and in chests and shops; the buttons are only on the inventory page. The item search starts after the
  buttons while they show (`GameplayHudOverlaySupport::inventorySearchBox`).
- Status and hover lines name a bag "tab II, bag 3" (`InventoryBagOverview::bagName`).
- Shift+Sort sorts the four bags of the open tab, as MAW's sort of a tab (zzMaw-Item-Sorter.lua sortMultibag);
  Ctrl+Shift sorts every member's open tab.
- When a second member joins, the tabs go: the member's open bag, if past bag 4, closes to bag 1, and tabs II-V keep
  their items until the member is alone again (MAW keeps them too). Event and quest item checks still see them.
  Before, every bag past the count fell at the party's feet each frame; now only what an old save could not fit
  does (`InventoryBags::OverflowBag`, `takeOverflow`).
- Tests: `tests/MawContentUiTests.cpp` ("A party of one's tabs: Shift+Sort sorts the open tab, and the other tabs wait
  while the party is bigger", and the bag count and save-fitting cases).
