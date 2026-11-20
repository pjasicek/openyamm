# Loot filter and progress: study, 25 October 2026

Browser study for two of MAW's H.6 pieces ([GAPS](../../../devdocs/maw/GAPS.md) H.6, §11 D.16: "each with its own
study"). Potion quick-slots have their own study (`maw_potion_radial_20261025/`). Nothing here is wired into the
game.

Open [index.html](index.html) directly; the buttons at the top switch between the two. `?view=filter|progress&export=1`
gives the captures in [previews/](previews/). Both are drawn over 1600x900 native captures (a MAW game, the Journal).

## A · Loot filter

MAW has one switch, "Loot filter: off / Common / … / Primordial": a monster or chest drop at or below that rarity
becomes gold (40 % of its value). Legendary and Celestial items cannot be told apart, nothing says what was filtered,
and an item type cannot be kept (ITEMS.md §1.14, ITEMS_DATA.md 16).

The proposal (revised 2026-10-25 after the user asked for presets, "like FilterBlade's strictness levels", that help
without overwhelming) opens on **presets**; rules are one click further for those who want them. It is reached from
Settings: a "Loot filter" row (MAW games only) shows the preset and opens this as a large window over the screen.

**A · Presets** (the window's first view):
- **Strictness**: Off, Soft, Regular (the default), Strict, Very strict, Custom, each with one line of what it does and
  a four-step strictness marker.
- **What it filters**: a grid of rarity against weapons, armour and jewellery, the only items with a rarity (the MAW
  author's feedback, 2026-10-25), saying keep, gold, or "gold if 20+ levels below". The level cells make a preset scale with the
  party: an item turns into gold only once its level is that far below the party's, so a preset filters little early
  and more as the party outgrows its gear, and never needs re-choosing.
- **Items without rarity**: checkmarks for wands, scrolls, potions, reagents and gems, "turn into gold" or not; each
  preset sets them (Strict: scrolls; Very strict: wands and scrolls) and the player can flip them.
- **Always kept**: legendary, Celestial and set items, artifacts, quest items and spellbooks, stated once.
- **Filtered items**: turn into gold (MAW), or stay on the ground greyed (no rarity glow, still pickable).
- **Your last 50 drops with this filter**: how many the chosen preset would have turned into gold and for how much,
  from this game's own drops, so a preset can be tried before it is chosen.

![Loot filter presets](previews/filter.png)

**A2 · Custom rules** ("Customize rules…" or the Custom preset): the preset as an ordered rule list, checked from the
top, first fit decides. A rule names a rarity ceiling, item types and optionally an item level below the party's;
▲▼ move it, ✕ removes it. The first row, "Legendary, Celestial or artifact → Keep", can be switched off but not moved;
the last, "Everything else", only changes its action. Recent drops show which rule decided each.

![Loot filter rules](previews/advanced.png)

## B · Progress (a fifth Journal tab)

**User decision, 2026-10-25: approved as shown.**

MAW keeps its progression state scattered over the minimap plate, town hall texts and popups. The proposal gathers it
in the Journal, under a fifth tab after Notes (the tabs get slightly shorter to fit). A key (unbound by default) opens
it directly. MAW games only; Standard keeps four tabs.

- **Header**: difficulty, progression mode, total level, challenge mode (and Beyond Madness's death count).
- **Continents**: one card each with the monster level band, the levels banked there and the maps cleared; clicking a
  card lists its maps.
- **Maps**: All / Cleared / In progress / Not visited; each row the map's level, a completion bar in the minimap
  plate's colours (green cleared since the last refill, yellow half, red started, empty not visited) and its resets.
- **Map details**: level with the resets' share, state, the completion reward, resets, time to the next refill, and
  what the town hall offers (a reset).
- **Footer**: the dimension quest tier, dimension runs cleared, the current run, bounties claimed.

![Progress](previews/progress.png)

## Open questions

- Loot filter: are the five presets and their thresholds right (Regular is MAW's filter at Uncommon plus the level
  rule)?
- Loot filter: are the rarity groups and the kinds without rarity right?

## Native

**B · Progress** is native since 2026-10-25, in MAW games only (Standard keeps four tabs).

- The Journal shows five shorter tabs (`JournalTabs5*` in `journal.yml`: 72 tall every 79.5 instead of 80 every
  97); the fifth, Progress, has its own icon, the study's emblem (a red-enamel heater shield with a brass rim and a
  gold rising line) rendered at the other icons' size by [native/make_progress_icon.py](native/make_progress_icon.py)
  (`assets_source/engine/icons_x2/obsidian_journal_icon_progress.png`, cooked by `tools/cook_ui_textures.py`).
- The page (`JournalProgressPage`, drawn by `game/ui/GameplayJournalProgress.cpp`) keeps the study's layout and
  colours: the mode line (difficulty, progression, total level, challenge mode, Beyond Madness's deaths), a card per
  continent (monster level band, levels banked there, maps whose completion reward was paid, a bar), the filters, the
  continent's maps by level (14 rows, the wheel scrolls; a bar in the plate's colours; resets), the details of the map
  under the pointer or the one clicked, and the footer (dimension quest, runs cleared, current run, bounties claimed
  and their gold). It opens on the continent and map the party is on.
- The data comes from `MawMonsterRules::progressSummary` (`game/rules/maw/MawProgress.cpp`), built when the tab opens:
  the maps MAW lists in its level bands that have monsters of their own; a map's level is the mean of its own B-tier
  families' levels at the current banks, and its resets' share is the difference without them. New in save 124:
  each map the party leaves keeps its slain and counted monsters and the day it was loaded
  (`MawGameState::mapVisits`, so "refills in N days" counts as the map's refill does), and the game counts the
  dimension runs cleared and the bounties claimed. Older saves start them at 0.
- The key **Open Progress** (MAW group, unbound) opens the Journal on the tab.

![Progress](native/maw_progress.jpg)
![Another continent](native/maw_progress_antagarich.jpg)
![Standard: four tabs](native/standard_journal.jpg)

**Refinement, 2026-10-25 (user feedback on the first capture):** the page's text is larger and upright (Alegreya
SemiBold, the enemy labels' face; titles stay Fondamento), map names and values in ivory, labels lighter. The bars'
tracks are lighter so they read as bars at 0 %; a map not visited keeps a dimmer track with no fill, and the
continents' bars are brass. Each map row has a column of flags with a legend under the list and their names on hover:
cleared since its refill (check), the town hall offers a reset (arrow), refilled (amber
ring: cleared once, its monsters back), completion reward waiting (coin), this month's bounty target (skull) and an
open dimension run (portal); the details list the shown map's flags by name. 13 rows show at once. The user dropped
a first "you are here" flag: the tab opens on the party's map, selected and scrolled to.

![Progress with flags](native/maw_progress_flags.jpg)
![A flag's name on hover](native/maw_progress_hover.jpg)

## Native loot filter

**A · Loot filter presets** are native since 2026-10-25, in MAW games only (DEVIATIONS 17 and 179, GAPS H.6). The
custom rules (A2) come next; the Custom preset is shown, not yet choosable.

- Settings, Rules: the **Loot filter** row shows the preset and opens the window over the menu
  (`game/ui/screens/MainMenuLootFilter.cpp`). Its choices edit the settings draft, so Revert and Apply Changes work as
  for every other row; Done or Escape returns to Settings.
- Its small text uses the Progress tab's Alegreya SemiBold instead of Lucida, larger, for small resolutions (user,
  2026-10-25); headings and preset names stay Fondamento.
- The window keeps the study's layout: the presets with their line and strictness marker, the rarity grid (cells from
  `lootFilterCellText`; the note names the preset's own level gap), the kinds without rarity, the always-kept line, gold
  or "stay on the ground, greyed", and the chosen preset tried on this session's last 50 drops.
- The rules are `game/rules/LootFilter.h`: a preset per group says the highest rarity turned into gold and the gap below
  the party's mean level at which the next one goes too (Soft 30, the others 20 or 30 as in the study). MAW describes a
  drop with `MawItemRules::lootFilterFacts`: its group or kind by Equip Stat, its rarity (a placed item MAW never rolled
  ranks as Common plus one per enchantment), its drop level, and whether it is always kept (legendary, Celestial,
  artifact or relic); spellbooks, quest items and letters are none of the filter's.
- Every corpse and chest drop goes through `filterDroppedLoot` (`game/gameplay/GameplayLootFilter.cpp`): gold joins the
  corpse's or chest's gold with the combat log line "Filtered: <rarity> <item> -> N gold" (it wraps in the panel, shows
  under All only and has no damage steps); a drop left on the ground keeps a mark (`ItemRulesetFields::lootFiltered`)
  that draws its rarity glow grey until it is taken. Each drop joins the session's recent drops (not saved).
- Save 126 stores the preset, the kinds and the ground choice (and the mark). Older saves take the preset nearest their
  rarity (Off stays Off; Common: Soft; Uncommon: Regular; Rare: Strict; Epic and above: Very strict); new MAW games start
  on Regular. Scenario `rulesets/maw_loot_filter.yml` sets Very strict, kills ten Swift bosses and finds the loot lines,
  then plays the same with Off.

![The window with the heavier text, Strict chosen](native/loot_filter_strict.jpg)
![The window over Settings, Very strict tried on three drops (before the font change)](native/loot_filter_very_strict.jpg)
![Filtered drops stay on the ground, greyed](native/loot_filter_ground.jpg)
![An older save with MAW's filter off opens on Off](native/loot_filter_migrated_off.jpg)
![The Settings row, the change waiting for Apply](native/loot_filter_settings_row.jpg)
![The combat log's loot lines](native/loot_filter_combat_log.jpg)
