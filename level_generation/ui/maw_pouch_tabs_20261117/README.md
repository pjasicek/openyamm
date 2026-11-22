# MAW: the Alchemy, Crafting and Quest tabs of the inventory

The user's request of 2026-11-17: the potion and hammer buttons of the inventory's top bar no longer tag a bag. Each
opens an endless tab of its own, and nothing of its kind lies anywhere else in a MAW game. It replaces the bag tags
of the [bag overview](../maw_bag_overview_20261025/README.md#bag-tags-gaps-h10) (DEVIATIONS 178, now 196). The same
day the user asked for the same for quest items ("the stuff which is worth 0 value"), with a shorter search field:
the key button after the potion.

Standard games have the Alchemy and Quest tabs too since 2026-11-22 (a player's request on Discord), under the
Gameplay setting **Party pouches**, on by default; see [Standard games](#standard-games-the-party-pouches-setting).

## What the player sees

| View | Capture |
|---|---|
| The four bags as before; no potions or reagents in them | [bags.jpg](bags.jpg) |
| The potion button: every potion, bottle and reagent of the party, one grid without dividers, a scrollbar at its right | [alchemy.jpg](alchemy.jpg) |
| Sort on the tab: bottles by kind and strength, then the reagents, rows closed up | [alchemy_sorted.jpg](alchemy_sorted.jpg) |
| Scrolled to the end; four free rows always follow the last item | [alchemy_scrolled.jpg](alchemy_scrolled.jpg) |
| A potion in hand over the tab: the cells it would take | [alchemy_holding.jpg](alchemy_holding.jpg) |
| The hammer button (Shift+B): the Workbench materials | [crafting.jpg](crafting.jpg) |
| An alchemist's Sell screen on the Alchemy tab: two potions sold | [shop_sell.jpg](shop_sell.jpg) |
| The key button after the potion; the tab buttons I-V and the shorter item search after it. A Lich Jar (it has a price) and a blaster (gear) stay in the bags | [quest_bags.jpg](quest_bags.jpg) |
| The key button: keys, letters and message scrolls worth nothing | [quest.jpg](quest.jpg) |
| Sort on the Quest tab | [quest_sorted.jpg](quest_sorted.jpg) |
| A shop's Sell screen on the Quest tab | [shop_quest.jpg](shop_quest.jpg) |

- A tab takes the bags' place: 28 cells wide (two bags side by side) and 18 rows high (two bags' worth) at the
  overview's cell size. It scrolls by the mouse wheel and by its scrollbar, and holds 240 rows.
- The pouches are the party's: every member's inventory shows the same three tabs, and the member whose inventory
  is open is the one who drinks, mixes, reads or sells from them.
- A quest item is whatever is worth nothing (Value 0 in the item table as the ruleset patches it) and is not worn or
  wielded: keys, letters, message scrolls, trophies, MM9's Misc quest items. Gear worth nothing (blasters, the
  Wetsuit, Snergle's Axe) stays with the gear, and a quest item with a price (a Lich Jar, a sealed letter worth
  gold, a recipe) stays in the bags.
- The key button took 26 units from the item search: the tab buttons I-V (a party of one) and the search start 26
  units further right.
- Such an item cannot lie elsewhere. Pickups, loot, purchases, event and quest gifts and mixing results go to its
  pouch; dropped on a bag (or on the other tab) it goes to its own pouch, with a status line; a tab refuses any other
  item ("Only potions, bottles and reagents go here").
- The tab's button again, the overview button or a bag button returns to the bags.
- Shops and chests have the same three buttons over the party's inventory (`ChestInventoryCraftingPouch`,
  `ChestInventoryAlchemyPouch`, `ChestInventoryQuestPouch`); a shop keeps the tab while it goes from Display to Sell
  or Identify.

## How it works

- `ItemRules::pouch(definition)` names an item's pouch (`ItemPouch::Crafting`: items 1041-1070; `Alchemy`: Equip Stat
  Bottle, Reagent or Herb; `Quest`: Value 0 and an Equip Stat that is no gear) and `hasPouches()` says whether the
  rules always have them (MAW; Standard only under the Party pouches setting, below).
- `Party` holds the three item lists (`pouchItems`, saved in its snapshot since save 192; the Quest list since 193).
  Every way into a member's bags asks `Party::pouchFor` first: `tryGrantItem`, `tryGrantInventoryItem*`,
  `grantItemToMember`, `tryAutoPlaceItemInMemberInventory` and `tryPlaceItemInMemberInventoryCell`.
- A pouch is addressed as a bag of any member (`InventoryBags::AlchemyPouchBag`, `CraftingPouchBag`, `QuestPouchBag`),
  so a `BagItemRef` names its items and `InventoryBags::placeInBag`, `takeFromBag`, `withBagOpen` and
  `refitChangedItem` work on it. While `withBagOpen` runs, the pouch is that member's open bag and the character's
  grid is the pouch's (`openBagGrid` in `Party.cpp`), which is how drinking, mixing, selling and identifying reuse the
  open bag's code.
- Item checks and removals of events and quests (`Party::inventoryItemCount`, `removeItem`, `removeItemFromMember`,
  the event item replacement, Lua's `evt.PartyMemberHasItem`) count the pouches for the party and for a named member.
  An item with an effect on the whole party while carried (`CarriedPartyEffect`, MM9's Fizbin of Misfortune) works
  from a pouch and from any bag, and a save lists the packages of the items in its pouches and other bags. The Workbench
  (`CraftingRuntime`, `AlchemyBenchRuntime`), the potion quick-slots, upkeep potions and battle orders walk them with
  `InventoryBags::carriedBags`.
- The view is a slot of the bag overview (`InventoryBagOverview::pouchSlot`, with `columns`, `rows` and `firstRow`),
  so it uses the overview's pointer targets, click handling and drop preview. Its state is
  `InventoryPouchViewState` (the tab shown, each pouch's first row, the scrollbar drag) on the character screen and on
  a shop's or chest's inventory.
- `InventoryBags::sortPouch` sorts a pouch; the bags' sorts no longer know tags.
- Saves: version 192 writes the pouches and drops the bag tags (read and ignored in older saves); version 193 adds
  the Quest pouch. A save before 193 moves its items when loaded (`Party::gatherPouchItems` in `GameSession`); a
  party seeded before its rules were set and a member who joins do the same.
- The buttons' icons are the game's Massive Hammer, Cure Wounds potion and Prison Key (turned 40 degrees), cooked as
  `obsidian_bag_tag_crafting`, `obsidian_bag_tag_alchemy` and `obsidian_bag_tag_quest` (sources in
  assets_source/engine/icons_x2, `tools/cook_ui_textures.py`).

## Standard games: the Party pouches setting

- Settings → Gameplay → Inventory → Party pouches (`[gameplay] party_pouches`, `GameSettings::partyPouches`, on by
  default) gives a Standard game the Alchemy and Quest tabs with MAW's rules for what goes in them
  (`ItemRules::alchemyOrQuestPouch`, which MAW's `pouch` uses too). There is no Crafting tab: Standard has no
  Workbench materials. MAW always has all three and ignores the setting.
- `Party::partyPouches` is the setting where it has effect: a ruleset without pouches, in a game of one player. A
  co-op session keeps its own rule (only the quest pouch, the world's), so the alchemy pouch empties into the bags
  while it lasts.
- `Party::sortPouchItems` moves the items when the setting or the shared world changes: a pouch the party no longer
  keeps empties into the bags (what finds no room stays in it, and its tab stays while it holds something), then
  `gatherPouchItems` takes the pouch items out of the bags. `GameSession::setPartyPouches` runs it for the local party
  from `GameApplication::applyCurrentSettingsToActiveRuntime`, so a change in Settings, a loaded save and an entered
  map all get the setting's pouches. The saves need nothing new: the pouches have been in every save since 192/193.
- Scenarios run with the setting off, so Standard's scenarios keep their items in the bags. Unit test:
  `--test-case='*party pouches*'`.
- Captures (Standard, mm8, the setting on, `tour_standard.yml` run as the tours below without `--ruleset maw`):
  [the bag without potions or keys](standard_bags.jpg), [the Alchemy tab](standard_alchemy.jpg),
  [the Quest tab](standard_quest.jpg), [a potion mixed on the tab](standard_mixed.jpg).

## Checks

- Unit tests: `./build/tests/openyamm_unit_tests --test-case='*pouch*'` (routing, quest counts and removals, the
  migration, sorting, the save round trip, what the Quest pouch takes, a carried party effect from it), and the
  older-save tests of `RulesetTests.cpp` (a save of version 192 with its two pouches among them).
- Scenarios: `tests/scenarios/rulesets/maw_potions.yml`, `maw_crafting.yml`, `maw_mm7_smoke.yml`, `maw_mm8_smoke.yml`
  (their `use_item` and `craft` steps find pouch items).
- The captures: `SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated pouch --world mm8 --map out01.odm --ruleset maw
  --warmup 0 --seconds 60 --set video.window_mode=windowed --set video.resolution=1600x900
  --set debug.menu_input_tour_path=$PWD/level_generation/ui/maw_pouch_tabs_20261117/tour_inventory.yml` (and
  `tour_shop.yml`, `tour_quest.yml`).

## Left

- Android shows the tabs at the same half-size cells as on desktop; nothing was tuned for touch.
- A held item over a shop's or chest's tab keeps its full size and has no drop preview there.
- The fifteen new texts are in the templates and untranslated in every language.
- MAW's quest-bound items with a price (`mawQuestBoundItems`, which a shop refuses until their quest is done) and
  MM9's items flagged `Quest` with a price are not quest items by this rule.
