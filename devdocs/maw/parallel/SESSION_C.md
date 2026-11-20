# Session C: alchemy, content and interface

Read [README.md](README.md) first: the shared rules, your build directory (`build-c`), the files to claim, your
numbers (DEVIATIONS 130-159, SaveVersion 110) and how to reach the coordinator.

## Your rows

Work P2 first, then P3. Rows already `done` are context only.

**§7 Alchemy and crafting**: A4.5-A4.8, A4.9 (partly done 2026-10-24: names "Potion Deleted in MAW" for 264-289 and
291-299, "This potion has been removed" notes and `item182` art for 252-261 are in `content/items_patch.txt`; left:
Austerity's "Potion Deleted in Austerity" names for 232-237, 252-256, 261-263 while that mode is on, and MAW's
Alchemy Master/GM skill descriptions), L7.1-L7.5. A4.4's water-monster note: check how our corpses of the nine
water monsters behave before changing anything. L7.6 is "no port".

**§8 Content and maps**: N8.1-N8.4, L8.1 (dev 57), L8.2 (dev 60). Map behaviour goes in event overlays or the
ruleset's `events/`, never in generated Lua (`-- generated from legacy EVT/STR`); see AGENTS.md.

**§9 Interface**: P2 H.1 multibag, H.2 monster inspect panel; P3 H.3-H.8, E.6. Also **L4.5** from §2: the
Power/Vitality comparison in item popups, the M/R/S and Vitality labels on the stats screen and the leech block
(MAW: `Scripts/Modules/MawCore/Tooltip.lua:590-665`, `Scripts/General/zzMaw-Stats.lua:269-291, 425-445,
1160-1180`; our `powerAndVitality` in `MawCombatRules.cpp` is the calcPowerVitality counterpart, ask before
exposing it), and a loot-odds page.

## Where things are

- Rules: `game/rules/PotionRules.h`, `CraftingRules.h`, `ItemRules.h` (popup lines: `inspectLines`,
  `enchantDescription`, which take the viewer); MAW: `MawPotionRules.*`, `MawCraftingRules.*`, `MawCraftingData.*`.
- UI: `game/ui/` (popups in `GameplayPartyOverlayRenderer.cpp`, the Workbench in `GameplayCraftingBenchView.*`),
  layouts in `assets_dev/engine/ui/gameplay/*.yml`. The approved designs are in AGENTS.md (Obsidian HUD, Carved
  Obsidian overlays and menus): keep to them and screenshot every change (engine-native capture,
  `debug.menu_input_tour_path` for scripted UI tours, 1600x900 canvas coordinates).
- Specs: `devdocs/maw/CRAFTING.md`, `CRAFTING_BENCH_DESIGN.md`, `SKILLS_SPELLS_ALCHEMY.md`, `MAPS_CONTENT.md`,
  `data/potion_effects.yml`, `potion_recipes.yml`, `crafting_items.yml`, `map_overlays.yml`.
- MAW: `Scripts/General/zzAlchemy.lua` (AL), `zzMaw-MultiBag.lua`, `zzMaw-Item-Sorter.lua`,
  `Scripts/Modules/MawCore/Tooltip.lua`, `Scripts/General/NPCMercenaries.lua`.

## Expected overlaps

- The monster inspect panel (H.2) reads MAW's monster numbers (`MawMonsterRules`, the coordinator's area) and
  mitigation (`MawCombatRules`): add read-only accessors through a claim.
- The multibag (H.1) changes inventory storage and therefore saves: plan the save format with the coordinator before
  you write it (SaveVersion 110 is yours).
- New key bindings: keyboard settings YAML; Android controls follow the approved Android layout in AGENTS.md, ask
  before adding any.
