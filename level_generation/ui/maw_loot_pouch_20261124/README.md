# The new loot pouch

The user's request of 2026-11-24, from a player's wish: "a bag where all new unidentified items go to and I can pick
which ones I want to keep ... others sort themselves to trash". After a map is cleared the loot no longer spills
over four tabs of bags: it waits in one endless tab, the player keeps what they want by moving it to a bag or a
member, and sells the rest in one go. The inventory's gold and food were tightened to make room for the button.

It is the fourth of the party's pouches (see [the Alchemy, Crafting and Quest tabs](../maw_pouch_tabs_20261117/README.md)),
with one difference: it has no kind of its own. It takes any item that has no other pouch, and such items leave it for
a bag freely. Built for MAW; Standard games have it too since the same day (user: "lets make it also for standard
mmmerge", default on).

## What the player sees

| View | Capture |
|---|---|
| A cleared map's gather key: potions, reagents and materials go to their pouches, the gear to the new loot pouch | [00-loot-summary.jpg](00-loot-summary.jpg) |
| The bags afterwards: only the starting kit | [01-bags.jpg](01-bags.jpg) |
| The leather pouch button, the first of the pouch buttons: the looted gear | [02-loot-tab.jpg](02-loot-tab.jpg), [03-loot-tab-hover.jpg](03-loot-tab-hover.jpg) |
| A shop's Sell screen on the loot pouch's tab | [s03-sell-loot-tab.jpg](s03-sell-loot-tab.jpg) |
| Sell trash there: every item of the tab picked, an unidentified one too | [s04-sell-trash-picked.jpg](s04-sell-trash-picked.jpg) |
| Sold: "Sold 9 items for 6400 gold.", the tab empty | [s05-sold.jpg](s05-sold.jpg) |
| Standard (Party pouches on): leather pouch, potion and key, packed against the tabs' end with no gap for the hammer | [std01-bags.jpg](std01-bags.jpg), [std02-loot-tab.jpg](std02-loot-tab.jpg) |

- What the party picks up or loots goes to the tab: the ground (a click or the gather key), a chest's Take All,
  corpses and the gather key's sweep of a cleared map. A potion, reagent, material or quest item still goes to its own
  pouch. Event and quest gifts, purchases and an item picked up by hand from a chest's grid go where they went before.
- The tab is the party's, the same for every member. Drag an item to a bag or a portrait to keep it; drop any item
  without a pouch of its own on the tab to put it back.
- On a shop's Sell screen, Sell trash while the loot pouch's tab shows picks every item of the tab the shop buys, identified or
  not (any shop that buys buys every item with a value). Clicking an item takes it out of the pick or puts it back, as
  for the ordinary Sell trash; on the bags, Sell trash picks by the rules as before.
- Settings → Gameplay → Inventory → **New loot pouch** (`[gameplay] loot_pouch`, on by default). Off, loot goes to the
  bags again; the tab stays while it holds something (in Standard; in MAW always) and keeps what it holds. Under
  Standard the Party pouches setting's sorting leaves the loot pouch alone, and Sell trash is offered in shops while
  the party has the loot pouch (on the bags it picks nothing by itself there: Standard has no loot filter; click
  items to add them).
- The top bar of the character screen: the gold and food are 28 units narrower (left-aligned numbers after their
  icons); the overview and bag buttons start 28 units further left, then four pouch slots, and the tab buttons I-V and
  the item search sit where they were. The slots (`CharacterInventoryPouch1-4`, `ChestInventoryPouch1-4` over a
  shop's or chest's party inventory) show, left to right, the leather pouch, hammer, potion and key (user: "make it the first button
  there"); the pouches the party has are packed against the last slot (`GameplayHudOverlaySupport::pouchButtons`), so
  Standard's missing hammer leaves no gap.

## The button's icon

The button showed a "?" at first. On the user's go-ahead (same day) it is the game's Leather Pouch (`pouch1`, item
2050), like the hammer, potion and key of the other pouches: MAW calls corpse loot satchels, and the buckled bag
reads at button size where "?" read as "unidentified" or "help". Source
`assets_source/engine/icons_x2/obsidian_bag_tag_loot.png` (the item icon fitted to 64 px), cooked by
`tools/cook_ui_textures.py` (desktop and android).

## Shift: which items are unidentified

The same day the user asked for the item state tints while Shift is held on the character screen: unidentified items
blue (the tint an unidentified item in hand or worn already had), broken items red (as they always are there),
everything else as usual. It works in every ruleset, on the bags, the overview, every pouch tab and the paperdoll.
The key is the rebindable **Show unidentified items** (`show_item_states`, Left Shift; Controls → Party & books).

| Without Shift | With Shift |
|---|---|
| [t01-loot-tab.jpg](t01-loot-tab.jpg) | [t02-loot-tab-shift.jpg](t02-loot-tab-shift.jpg): the blue ones are unidentified; the bow is identified |

`tour_shift_tints.yml` makes these captures (`key_down: Left Shift`).

## How it works

- `ItemPouch::Loot` (`InventoryBags::LootPouchBag`, 243). `ItemRules::pouch` never names it, so `Party::pouchFor`
  never sends an item there; `InventoryBags::isKindPouchBag` is the test for the three pouches that take only their own
  kind (`Party::tryPlaceItemInMemberInventoryCell`, `InventoryBags::previewPlaceInBag`).
- `storePickedUpItem` (every pickup and loot path) calls `Party::tryGrantLootItem`: the loot pouch when
  `Party::lootGoesToPouch` (the setting and an item without a pouch), else
  `tryGrantInventoryItem` as before. `GameApplication` sets the setting on the session's parties and on the map
  scene's party.
- `HouseServiceRuntime::findLootPouchTrash` is the pick on the tab; `trySellTrash` sells it through
  `InventoryBags::withBagOpen` like any pick.
- Saves: version 202 writes the loot pouch after the waiting given items; older saves have none. Character files and
  co-op characters carry it, as they carry the other party pouches.
- Scenarios run with the setting off, so their loot stays in the bags.

## Checks

- Unit tests: `./build/tests/openyamm_unit_tests --test-case='*loot pouch*'` (routing with the setting off and on, in
  and out by hand, Sell trash on the tab, Standard, the save round trip), and the older-save tests of
  `RulesetTests.cpp`.
- The captures (MAW, MM8, Dagger Wound, `actor kill` and the gather key for the loot):
  `SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated lootpouch --world mm8 --map out01.odm --ruleset maw
  --warmup 0 --seconds 45 --set video.window_mode=windowed --set video.resolution=1600x900
  --set debug.menu_input_tour_path=$PWD/level_generation/ui/maw_loot_pouch_20261124/tour_inventory.yml`
  (and `tour_shop.yml`, `tour_shift_tints.yml`; `tour_standard.yml` without `--ruleset maw`).

## Left

- The new texts are untranslated in every language until the next `tools/l10n.py extract` and `update`.
- A pick made on the tab names its items as the active member's; choosing another member while picking unlights them
  (the sale still sells them).
