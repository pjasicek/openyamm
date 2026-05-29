# MM6 Mechanics Audit Checklist

This is the broader MM6 mechanics checklist. It is separate from `MM6_MMERGE_DELTA_INVENTORY.md`, which tracks known
MMerge per-map deltas and is currently complete.

The goal here is to prove original-MM6/OpenEnroth-style gameplay behavior across shared engine systems. A row is
complete only when it has either focused unit coverage, scripted/headless MM6 coverage, or a documented source-driven
no-op.

## Reference Rules

- Use `reference/OpenEnroth-git/` for original engine behavior.
- Use `reference/mmext-scripts/Decompiled_Scripts/mm6/txt/` for readable MM6 event control-flow checks.
- Use `reference/mmerge_data_forus/` and `reference/mmmerge/` only as MMerge behavior/data references.
- Do not copy reference code. Convert behavior into OpenYAMM runtime APIs, data tables, or MM6 overlays.

## Status Legend

- `Proven`: covered by tests or inventory with explicit acceptance evidence.
- `Partial`: runtime support exists, but MM6-specific parity still needs broader comparison or headless scenarios.
- `Open`: not yet audited enough to claim parity.
- `Deferred`: known non-core/custom/presentation work that should not block original MM6 mechanics.

## Current High-Level State

| Area | Status | Evidence / notes |
| --- | --- | --- |
| MM6 world import, assets, map scripts | Partial | `MM6_WORLD_IMPORT_INVENTORY.md` records 66-map import/export status and validation gates. Re-run gates before claiming current full-world acceptance. |
| MM6 MMMerge map deltas | Proven | `MM6_MMERGE_DELTA_INVENTORY.md`; scripted and scene regression tests cover the active rows. |
| Shared mechanics runtime | Partial | Broad shared tests exist, but not every OE/MM6 edge case has an MM6-specific oracle. |
| Full MM6 playthrough parity | Open | Needs route-based headless/manual acceptance scenarios across early, mid, late game. |

## Priority Checklist

### P0: Must Prove Before Calling MM6 Mechanics Done

| Check | Status | Verification target |
| --- | --- | --- |
| Full MM6 map-load sweep across all 66 maps with assets, scene overlays, actors, sprites, sounds, transitions. | Partial | Add/refresh an automated headless sweep target and record zero missing terrain/actor/sprite/audio diagnostics. |
| Generated MM6 event scripts plus all `*_mmmerge.lua` overlays compile and bind without missing event ids. | Partial | Extend scripted-map compile sweep to every MM6 map overlay and generated map script. |
| MM6 core quest route smoke test: New Sorpigal to Hive ending, including council, crystals, VARN, Control Center, Hive. | Open | Headless route test or manual checklist with save checkpoints and expected QBits/items/maps. |
| MM6 world-specific table filtering: active engine tables contain all MM6-required rows without relying on unrelated world bootstrap rows. | Partial | `MM6_WORLD_IMPORT_INVENTORY.md` table-filtering rows; add table reference tests for map/event/house/monster/NPC reachability. |
| Save/load round trip for MM6-specific state: map vars, QBits, overlays, followers, reputations, active world, pending map state. | Partial | Existing save tests are shared; add MM6 save fixture after several MM6 quest milestones. |

### P1: Combat, Monsters, And AI

| Check | Status | Verification target |
| --- | --- | --- |
| Monster attack cadence, recovery, hit reaction, stun window, and actor-vs-actor fights match OE enough for weak mobs not to lock strong mobs forever. | Partial | Shared AI tests cover recovery/stun gates; add MM6/OE comparison scenarios for 2-3 weak monsters attacking one strong monster. |
| Monster melee/ranged attack dice, resistances, armor-class hit chance, damage types, and projectile dice. | Partial | Existing monster/projectile/table tests cover many shared paths; add MM6 monster roster samples from `MONSTERS.txt`. |
| Monster spells: heal, power cure, buffs, hostile spells, unsupported spell filtering. | Partial | Shared AI tests cover several spell paths; audit remaining MM6 monster spell ids against OE/MMerge tables. |
| Monster death behavior: experience, death sounds, drops, guaranteed carried items, artifact rules, reanimated/no-drop suppression. | Partial | Shared tests cover death drops and reanimated suppression; add MM6 late-game monster drop samples. |
| Indoor/outdoor actor collision and stuck recovery. | Partial | Existing movement/collision tests cover selected cases; add MM6 indoor bmodel/wall stuck scenarios from reported maps. |
| Peasant/friendly hostility, local monster relations, guard hostility, reputation/fine side effects. | Partial | MM6 overlays and reputation tests cover selected paths; add MM6 town aggression scenarios. |

### P1: Party Combat, Conditions, And Spells

| Check | Status | Verification target |
| --- | --- | --- |
| Physical attack formulas: recovery, hit chance, weapon damage, ranged/bow requirements, dragon breath where applicable. | Partial | Shared character/combat tests exist; add OE-derived MM6 class/skill/weapon samples. |
| Spell costs, recovery, mastery gates, indoor/outdoor gates, scroll/wand overrides. | Partial | Spell regression tests cover many shared paths; audit every MM6 spell school row against OE behavior. |
| Damage spells: projectile/area/direct targeting, resist/immunity behavior, line of sight, visible-creature selection. | Partial | Existing tests cover representative spells; add MM6 dungeon/outdoor spell smoke cases. |
| Buff/debuff spells: Bless, Haste, Shield, Slow, Stun, Fear, Control Undead, Dispel, recharge, Lloyd's Beacon. | Partial | Several paths are covered; remaining audit should compare formulas/durations to OE. |
| Conditions: poison/disease severities, weak/cursed/afraid/asleep/paralyzed/dead/stoned/eradicated, cure spells, temple healing. | Partial | Event condition tests exist; add MM6 condition acquisition/cure matrix. |
| Party death/defeat and continent death-map behavior. | Partial | Shared death-map support exists; add MM6-specific death-map and Hive bad-ending checks. |

### P1: Items, Inventory, Equipment, And Alchemy

| Check | Status | Verification target |
| --- | --- | --- |
| Inventory placement, swapping, held item, cross-member moves, full inventory behavior. | Proven | `PartyRegressionTests.cpp` inventory grid coverage. |
| MM6 item use: spellbooks, scrolls, potions, readable items, horseshoes, quest items, key items. | Partial | Shared item-use tests exist; add MM6 quest-item use matrix. |
| Equipment rules: skill requirements, class restrictions, race/artifact restrictions, two-hand/shield/bow/offhand behavior. | Partial | Existing equip tests cover important restrictions; add MM6 item table samples. |
| Enchantments, charges, recharge, breakage, repair, identify, value calculation. | Partial | Existing tests cover identify/repair/recharge/pricing; compare MM6 shop/skill edge cases to OE. |
| Alchemy/reagent/potion mixing, black/white potion effects, explosions, empty bottle returns. | Proven for core shared behavior | `GameplayRuleRegressionTests.cpp` covers reagent/potion mixing and explosions; add MM6-specific item-id spot checks if new ids appear. |
| Chest materialization, random loot, trap damage/disarm, fixed item ownership. | Partial | Chest tests cover shared behavior and selected MM6 Dagger Wound chests; expand to VARN/Hive/key late-game chests. |

### P1: Houses, NPCs, Services, And Economy

| Check | Status | Verification target |
| --- | --- | --- |
| MM6 house data: enter text, exit destinations, house movies/sounds, open hours, service availability. | Partial | House tests cover merged tables and MM6 transports; add representative MM6 service houses per region. |
| Shops: stock generation, standard/special stock, buy/sell/identify/repair, stealing, reputation bans/fines. | Partial | Shared shop and stealing tests exist; add MM6 shop levels and exact OE price samples. |
| Training: level caps, cost, merchant discounts, active member handling, skill point awards. | Partial | Shared training tests exist; add MM6 trainer samples. |
| Guilds: membership, spellbook stock, skill learning, class/quest gating. | Partial | MM6 guild membership topics are tested; add stock and skill gating samples for each guild type. |
| Temples: heal/cure/revive, donation buffs, reputation gates, condition coverage. | Partial | Donation/reputation tests exist; add MM6 temple service matrix. |
| NPC followers: rescue followers, hire/fire, house movement, profession bonuses, food/gold/service modifiers. | Partial | MM6 rescue followers and shared follower bonuses are tested; add MM6-specific profession list audit. |
| Generic NPC news/topics, teacher autonotes, awards/history/autonotes. | Partial | Shared merged topic/autonote tests exist; add MM6 area news and teacher note samples. |

### P1: Map Events, Quests, Travel, And Time

| Check | Status | Verification target |
| --- | --- | --- |
| MM6 generated EVT parity for all maps against GrayFace readable scripts. | Partial | No unsupported opcode export is documented; still needs systematic per-map semantic sampling. |
| MM6 `*_mmmerge.lua` overlays. | Proven | `MM6_MMERGE_DELTA_INVENTORY.md` plus scripted regression coverage. |
| Outdoor edge travel, stables, boats, direct house exits, town portal unlocks, Dimension Door. | Partial | Transport/town-portal tests cover active paths; add MM6 route matrix across all continents/regions. |
| Rest, food cost, time passage, timers, refill/respawn, map reload behavior. | Partial | Shared rest/refill hooks exist; add MM6 shrine/fountain/refill/timer samples. |
| Weather, snow/rain/fog/sky, terrain footstep sounds, water/lava/burn/transition tiles. | Partial | Terrain/scene tests cover selected MM6 tiles and footstep overrides; add outdoor visual/audio sweep. |
| Quest bits, autonotes, history, awards, reputation, bounty/fine/prison terms. | Partial | Shared tests cover reputation and several QBit paths; add MM6 mainline and sidequest state snapshots. |

### P2: Presentation, Audio, And UI Feedback

| Check | Status | Verification target |
| --- | --- | --- |
| Character speech/face reactions for combat, conditions, shops, houses, events, spell failure/success. | Partial | `MMERGE_REACTION_RUNTIME_INVENTORY.md` tracks remaining reaction causes; add MM6-specific voice samples. |
| Monster/world/house audio resolution under active MM6 world. | Partial | Sound catalog tests exist; add MM6 map/house/monster playback sweep. |
| Cutscenes and event movies: intro, council, Archibald, good/bad endings, restore/main-menu behavior. | Partial | Hive bad/good ending script tests exist; add app-level event movie completion test if a harness exists. |
| UI layout and text for MM6 houses, transitions, prompts, spellbook, inventory, character sheet, reputation/fame labels. | Partial | Many shared UI data tests exist; add MM6 textual prompt/transition snapshot tests. |
| Minimap/autonotes/map reveal/loading screens. | Open | Needs specific MM6 route and asset checks. |

### Deferred / Not Blocking Original MM6 Mechanics

| Check | Status | Notes |
| --- | --- | --- |
| Full CrossContinents final quest and Saving Goobers content. | Deferred | Custom MMerge content, not original MM6 parity. |
| MMerge convenience UI extras not present in original MM6. | Deferred | Treat separately from original mechanics. |
| Cosmetic-only per-continent presentation tweaks. | Deferred | Do after mechanics unless a missing asset blocks gameplay. |

## Suggested Audit Order

1. Run the validation gates from `MM6_WORLD_IMPORT_INVENTORY.md` and record current results here.
2. Add a 66-map generated script/overlay compile test if it does not already cover every MM6 map.
3. Build an MM6 main-quest route smoke test with checkpoints: New Sorpigal, Castle Ironfist council path, Free Haven
   council, Kriegspire, VARN, Control Center, Hive good ending, Hive bad ending.
4. Add focused OE comparison tests for the riskiest shared mechanics:
   monster-vs-monster recovery/stun, spell durations/damage, shop prices, temple services, traps/chests, and rest/refill.
5. After each pass, mark rows `Proven` only when the behavior is covered by a test or a reproducible headless/manual
   checklist with source references.

## Current Verification Commands

These commands passed after the latest MM6 delta work:

```text
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests
```

The full unit suite passed with 557 test cases and 43605 assertions at the time this checklist was created.
