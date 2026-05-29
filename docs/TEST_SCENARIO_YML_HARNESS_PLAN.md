# Test Scenario YML Harness Plan

This plan defines a declarative headless scenario harness for proving that a world can be completed through normal
runtime systems. The first target is complete MM6 coverage: new-game flow, main story milestones, council gates,
Oracle/VARN/Control Center/Hive, bad ending behavior, and all original MM6 promotion quests. The same harness must be
usable for MM7 and MM8 by changing scenario data, aliases, and route files rather than adding world-specific runner
branches.

## Goals

- Prove that the game can be completed from a fresh party using reproducible headless scenarios.
- Exercise real OpenYAMM runtime systems: world mounting, map loading, events, NPC topics, houses, inventory, quest
  bits, awards, followers, time, save/load, and ending transitions.
- Keep long playthrough coverage practical by allowing explicit, audited shortcuts for grinding, walking, and combat
  when those systems are not the behavior under test.
- Produce machine-readable failure artifacts that identify the failed step, map, event/NPC/house target, expected
  state, actual state, and latest checkpoint.
- Make the scenario format reusable for MM6/MM7/MM8 and future worlds.

## Non-Goals

- This is not a renderer or pixel regression harness.
- This is not a full player-input TAS where the party physically walks every route.
- This does not replace focused unit tests for formulas, combat, AI, shops, alchemy, or individual event opcodes.
- This does not hide broken data behind fallback behavior. If a scenario exposes a stale id or missing table row, fix
  the authoritative data, event script, schema, or migration.

## Route Modes

The runner should support three explicit modes. Each scenario declares one mode, and every shortcut step must state its
reason.

- `faithful`: proves normal story flow through new-game flow, map loads, transitions, houses, NPC topics, events, and
  save/load. No direct state edits after party creation.
- `hybrid`: proves long routes without hours of grinding. It allows faithful operations plus explicit grants for
  levels, gold, travel unlocks, quest items, actor kills, and time jumps at named checkpoints.
- `unitized`: proves a focused event or mechanic. It can directly load maps, seed preconditions, execute events, and
  assert post-state.

The MM6 completion route should use `hybrid`: map/event/dialogue gates stay faithful, while walking, routine combat,
and grind are shortcut through audited driver steps.

## Proposed File Layout

```text
tests/scenarios/
  schema/
    test_scenario.schema.yml
    aliases.schema.yml
  mm6/
    aliases.yml
    party_presets.yml
    main_story.yml
    promotions.yml
    council.yml
    endings.yml
    mechanics_smoke.yml
  mm7/
    aliases.yml
    main_story.yml
    promotions.yml
  mm8/
    aliases.yml
    main_story.yml
    promotions.yml
```

The scenario files belong under `tests/scenarios/` because they are test definitions, not content shipped to players.
They may reference content ids from `assets_dev/engine/` and `assets_dev/worlds/*`, but must not create runtime content
there.

## CLI

Add two new app entry points:

```bash
./build/game/openyamm --headless-run-scenario tests/scenarios/mm6/main_story.yml
./build/game/openyamm --headless-run-scenario-suite tests/scenarios/mm6
```

Useful optional flags:

```bash
--scenario-filter tag=main_story
--scenario-filter id=mm6.main_story.oracle
--scenario-report-json /tmp/openyamm-scenario.json
--scenario-report-junit /tmp/openyamm-scenario.xml
--scenario-artifacts-dir /tmp/openyamm-scenario-artifacts
--scenario-stop-after-checkpoint council_complete
--scenario-start-from-checkpoint council_complete
--scenario-strict-shortcuts
```

## Runner Architecture

Build the harness as a shared headless test subsystem instead of adding more one-off diagnostics to
`HeadlessOutdoorDiagnostics.cpp`.

- `ScenarioYamlLoader`: parse YAML, validate schema, resolve includes, expand party presets, and preserve source line
  numbers.
- `ScenarioAliasRegistry`: resolve namespaced aliases for maps, qbits, awards, items, NPCs, houses, topics, classes,
  skills, and actor groups.
- `ScenarioRunner`: execute steps, fail fast, manage checkpoints, record timing, and record artifacts.
- `ScenarioWorldDriver`: wrap world mounting, new game, map load, transitions, houses, time, rest, and save/load.
- `ScenarioPartyDriver`: create party members, grant/remove items, set class/level/skills, and manage party state.
- `ScenarioEventDriver`: execute local/global events, NPC topics, house topics, map triggers, chests, and pickups.
- `ScenarioCombatDriver`: provide route shortcuts for actor kills and real simulation entry points for combat tests.
- `ScenarioAssertionEngine`: compare expected state against runtime state using aliases and detailed diagnostics.
- `ScenarioReport`: emit JSON/JUnit summaries, checkpoint paths, state diffs, and timing breakdowns.

The runner should reuse/refactor the existing headless regression helpers where possible:

- `game/app/main.cpp` already owns headless command dispatch.
- `game/outdoor/HeadlessOutdoorDiagnostics.cpp` already has `RegressionScenario`,
  `IndoorRegressionScenario`, scenario initialization, local event execution, and map-level regression cases.
- The first implementation step should extract the reusable pieces needed by the YAML runner into smaller test-driver
  classes, then leave the existing diagnostics using those classes.

## YAML Model

Top-level shape:

```yaml
id: mm6.main_story.full
title: MM6 main story completion
world: mm6
mode: hybrid
seed: 0x4d4d36
tags: [mm6, main_story, slow]

requires:
  maps: [oute3.odm, outc1.odm]
  capabilities: [new_game_flow, npc_topics, save_load, local_events]

party:
  preset: mm6_story_party

setup:
  - set_rng_seed: 0x4d4d36

steps:
  - new_game_flow:
      continent: enroth
      party: mm6_story_party

  - assert:
      map: oute3.odm
      qbit_set: [mm6.main.letter.show_to_potbello]
      inventory_any_member:
        - item: mm6.item.sulmans_letter

  - checkpoint: new_sorpigal_started

teardown:
  - assert_no_missing_assets: {}
```

Step execution rules:

- Steps are atomic. A failed step stops the scenario and writes a state snapshot.
- Every direct mutation step records a `reason`.
- Every shortcut that grants quest state must be followed by assertions for the state it claims to establish.
- Scenario files should prefer aliases over raw ids. Raw ids are allowed only inside alias files or when paired with a
  comment/source field.
- Each checkpoint writes a save, reloads it when `save_load` is enabled, and verifies a canonical state snapshot.

## Core Step Types

| Step | Meaning |
| --- | --- |
| `new_game_flow` | Drive the same continent and party creation path used by the app UI. |
| `load_map` | Load a map directly for setup or focused checks. |
| `transition` | Use a normal map transition, edge travel, town portal, Lloyd beacon, boat, stable, or house exit. |
| `enter_house` / `exit_house` | Enter or exit a house through runtime house APIs. |
| `talk_npc` | Enter an NPC dialogue and select a topic by alias. |
| `house_topic` | Select a house service/topic, such as train, donate, buy food, or travel. |
| `execute_event` | Execute a local or global event by alias/id for focused checks. |
| `loot_chest` | Materialize/open a chest and optionally take matching items. |
| `pickup_item` | Pick up a map sprite/object by alias or source item id. |
| `kill_actor` / `clear_actor_group` | Route shortcut for combat completion; records actor/group and reason. |
| `simulate_combat` | Real combat simulation for focused mechanics scenarios. |
| `grant_item` / `remove_item` | Direct item mutation with placement policy and reason. |
| `grant_gold` / `set_level` / `set_skill` / `set_class` | Direct party setup for route speed or promotion coverage. |
| `hire_npc` / `dismiss_npc` | Manage followers using the same follower systems used by dialogue/events. |
| `set_time` / `wait` / `rest` | Advance deterministic game time and process timers/refills. |
| `cast_spell` / `use_item` | Exercise spell and item-use systems. |
| `save_checkpoint` / `load_checkpoint` | Persist and restore scenario state. |
| `assert` | Validate expected runtime state. |

## High-Fidelity Command Vocabulary

The scenario format should expose readable commands, but each command must declare whether it drives real gameplay
entry points or performs setup. Route-proof files should prefer commands in the `gameplay` category. Commands in the
`shortcut` category are allowed only in `hybrid` or `unitized` mode and must include `reason`.

### Session And Flow

- `new_game_flow`: select world/continent and create the party through the same flow used by the app.
- `load_map`: load a map as a setup operation or checkpoint resume operation.
- `save_checkpoint`: save current state, record canonical snapshot, and optionally reload/compare.
- `load_checkpoint`: restore a named scenario checkpoint.
- `assert_no_missing_assets`: fail if touched maps report missing sprites, textures, sounds, videos, events, NPC topics,
  houses, or item rows.

### Pose And Movement

- `set_pose`: place the party at exact coordinates/facing through the normal party/world state. This is a fast route
  positioning helper, not a proof of walking.
- `move_to`: alias for `set_pose` when used in route files. It should still validate map id, floor/sector, and party
  collision position.
- `face`: set party direction/look angle or face a named target.
- `walk_path`: advance the normal movement input loop through waypoints. Use only when proving collision, navigation,
  trigger volumes, or "can physically reach this" behavior.
- `transition`: trigger map/house/edge transition through normal gameplay when the transition is the behavior being
  tested.
- `travel`: use stable, boat, town portal, Lloyd's Beacon, Dimension Door, or scripted travel through the same runtime
  path as gameplay.

Example:

```yaml
- set_pose:
    map: 6d10.blv
    x: 1200
    y: -340
    z: 128
    direction: 512
    look_angle: 0

- press_action: { action: interact }
```

### Input Primitives

- `press_action`: press one gameplay action for one simulated frame, such as `interact`, `attack`, `cast_quick_spell`,
  `rest`, `open_inventory`, `open_spellbook`, `open_map`, `escape`, or `confirm`.
- `hold_action`: hold a movement/action binding for simulated runtime seconds.
- `release_action`: release a held binding.
- `input_frame`: provide a full input state for one fixed timestep.
- `click_ui`: click a UI element by stable id when the behavior under test is UI routing.
- `select_ui`: select a menu/list/button by stable id, topic alias, or visible text id.
- `type_text`: enter text into the focused UI field, mainly for character creation names or save names.

These are the lowest-level commands. Helper commands such as `interact_at` should lower to these primitives.

### Interaction Helpers

- `interact_at`: set/load pose, face target if provided, press the normal interact action, then wait for the expected
  interaction state.
- `interact_target`: interact with the current or named target from the current pose.
- `open_chest_at`: helper for `set_pose` plus normal interact; verifies chest id/state rather than directly opening it.
- `pickup_at`: helper for `set_pose` plus normal interact/pickup path.
- `use_fountain_at`: helper for `set_pose` plus normal interact; useful for promotion fountains, wells, and shrines.
- `press_mechanism_at`: helper for buttons/levers/faces; uses normal interact and then mechanism assertions.
- `enter_door_at`: helper for a door/transition face; uses normal interact/transition.

Helpers may include `target` for diagnostics, but the final operation should be the real gameplay interaction:

```yaml
- interact_at:
    target: mm6.fountain.magic
    pose: { map: outc2.odm, x: 1234, y: 5678, z: 90, direction: 512, look_angle: 0 }
    expect:
      status_text: mm6.text.fountain_magic
```

### Runtime Time

- `advance_runtime`: tick the normal game update loop for simulated seconds with a fixed timestep. No wall-clock sleep.
- `wait_until`: tick the normal update loop until an assertion becomes true or a runtime timeout expires.
- `wait_frames`: tick a fixed number of frames for one-frame delayed effects.
- `assert_runtime_elapsed`: diagnostic assertion for timer-driven mechanics.

Use runtime time for doors, lifts, traps, projectiles, delayed scripts, animation state, and combat recovery:

```yaml
- press_mechanism_at:
    target: mm6.mechanism.entry_gate_button
    pose: { map: 6d10.blv, x: 1200, y: -340, z: 128, direction: 512, look_angle: 0 }

- wait_until:
    timeout_runtime_seconds: 3.0
    assert:
      mechanism: { id: mm6.mechanism.entry_gate, state: open, passable: true }
```

### Calendar And Rest Time

- `advance_game_time`: advance calendar time through the game-time system.
- `set_calendar_time`: set exact date/hour for deterministic timed gates, with `reason`.
- `rest`: use the normal rest command, including food, danger checks, healing, and timer progression.
- `wait_calendar_until`: advance game time until a date/hour condition, such as full moon or solstice.
- `process_timers`: process map/global timers after a time jump when the scenario needs explicit control.

Use calendar time for travel days, Nicolai/circus waits, refills, solstice/full-moon promotions, shop restock, and
quest timers.

### Dialogue, NPCs, And Houses

- `talk_npc`: interact with an NPC through normal dialogue entry.
- `select_topic`: choose an NPC topic by alias, topic id, or expected text id.
- `assert_dialogue`: assert active NPC, available topics, selected text id, or refusal text.
- `enter_house`: enter a house through a normal transition or as a focused setup operation.
- `house_topic`: select a house service/topic through the house UI.
- `exit_house`: leave the house through the normal exit path and assert destination.
- `hire_npc`: hire a follower through dialogue/service when testing follower behavior.
- `dismiss_npc`: dismiss a follower through the normal UI/dialogue path when available.

### Inventory, Equipment, Items, And Spells

- `open_inventory`: open inventory through UI/input path.
- `move_item`: move an item through normal inventory placement rules.
- `equip_item`: equip through normal equipment rules.
- `unequip_item`: unequip through normal inventory rules.
- `use_item`: use scrolls, potions, books, quest items, or wands through normal item-use code.
- `cast_spell`: cast a spell through spellbook/quick-spell command path, with target/pose when needed.
- `learn_skill`: learn a skill through a trainer/guild/house topic when the learning path is under test.
- `train_level`: train through the normal training house flow.
- `buy_item` / `sell_item` / `identify_item` / `repair_item`: use normal shop flows.
- `donate` / `heal_at_temple`: use normal temple flows.

### Combat And Actors

- `attack`: press the normal attack action for one or more simulated frames.
- `cast_at_actor`: cast through normal spell targeting.
- `simulate_combat`: run real combat simulation for a bounded runtime budget and expected outcome.
- `wait_actor_state`: tick runtime until an actor reaches alive/dead/hostile/stunned/recovered state.
- `assert_actor`: assert actor position, health, AI state, hostility, item drop, or death state.
- `kill_actor`: shortcut for route progress only; must include `reason`.
- `clear_actor_group`: shortcut for route progress only; must include `reason` and expected post-state.

Main story scenarios should use `kill_actor` or `clear_actor_group` only when combat itself is already covered by a
focused scenario or is out of scope for the route.

### Mechanisms, Geometry, And Map State

- `assert_face`: assert visibility, passability, texture, event id, or trigger state for a map face.
- `assert_mechanism`: assert door/lift/button/lever state, openness, movement, and collision/passability.
- `assert_chest`: assert chest opened/closed, trap state, and contents.
- `assert_sprite`: assert sprite/object visibility, pickup state, and item identity.
- `assert_map_var`: assert map-local variable state.
- `assert_transition`: assert transition prompt, destination map, house id, and coordinates.
- `assert_collision`: assert party/actor is not stuck, or that a path/door is passable after a mechanism changes.

### Setup Shortcuts

- `grant_item`, `remove_item`, `grant_gold`, `set_food`, `set_level`, `set_experience`, `set_skill`, `set_class`,
  `set_condition`, `clear_condition`, `set_qbit`, `clear_qbit`, `set_award`, `clear_award`, `set_follower`,
  `set_map_var`, `set_actor_state`.
- These are never high-fidelity proof commands. They are setup shortcuts only.
- Any setup shortcut in `hybrid` mode must include `reason` and should be followed by assertions.
- Story completion artifacts such as final awards, class promotions, and main quest qbits should come from real
  events/dialogue, not setup shortcuts.

## Preferred Scenario Style

Use the highest-fidelity command that keeps the test focused:

1. For story gates, use `set_pose` or `travel`, then `press_action: interact`, `select_topic`, and assertions.
2. For map mechanisms, use `press_mechanism_at`, `advance_runtime` or `wait_until`, then mechanism/collision
   assertions.
3. For houses and NPCs, enter through normal transitions where practical, then use normal topic/service selection.
4. For long movement and routine combat, use shortcuts in the main route, but cover representative movement/combat in
   focused scenarios.
5. For timed quests, use calendar commands, not wall-clock waits.
6. For any helper command, the runner implementation should lower to the same gameplay method that the party/player
   uses unless the command is explicitly marked as a setup shortcut.

## Assertions

The first implementation should support these assertion families:

- Current world, map, house, party position, and facing.
- QBits, autonotes, history bits, awards, reputation, fame, bounty, and prison state.
- Inventory contains/does not contain item, item count, item owner, equipped state, mouse item, and full-inventory
  handling.
- Gold, bank gold, food, time, date, and active timers.
- Party member class, promotion tier, level, experience, skills, conditions, spellbook, and face/speech reaction if
  available.
- Follower roster, follower house movement, rescued NPC state, and follower topic availability.
- NPC topic availability, selected dialogue text id, house service availability, and house exit destination.
- Map vars, local event vars, chest opened state, face/decor/sprite hidden state, actor alive/dead/hostile state, and
  actor group state.
- Save/load equivalence for canonical party/world/event state.
- Ending state: movie request, main-menu transition, destroyed-world bad-ending route, or good-ending completion.
- Missing asset/script diagnostics: no missing actor sprites, terrain textures, event ids, NPC topics, item ids, house
  rows, or sound/video references for maps touched by the scenario.

## Alias Registry

Each world gets an alias file generated from current data tables and manually curated route names:

```yaml
qbits:
  mm6.main.letter.show_to_potbello: { raw: 81, source: mm6 GLOBAL.txt event 46 }
  mm6.main.letter.deliver_to_wilbur: { raw: 82, source: mm6 new-game letter flow }
  mm6.oracle.memory_alpha: { raw: 162, source: mm6 GLOBAL.txt event 73 }

awards:
  mm6.council.kilburn_shield: { raw: 2 }
  mm6.main.hive_destroyed: { raw: 36 }

items:
  mm6.item.control_cube: { raw: 456 }
  mm6.item.crystal_of_terrax: { raw: 457 }
  mm6.item.ritual_of_the_void: { raw: 544 }
```

Implementation requirements:

- Generate an initial `aliases.yml` from active OpenYAMM tables, `quests.txt`, `awards.txt`, item tables, NPC topics,
  house tables, and map stats.
- Cross-check generated aliases against `reference/mmext-scripts/Decompiled_Scripts/mm6/txt/` during authoring.
- Store raw ids as import aliases, not global truth. Scenarios use canonical namespaced aliases.
- Allow route-specific aliases such as `mm6.route.council_ready` that expand to multiple qbit/award assertions.

## Shortcut Policy

Shortcuts are necessary for a practical proof suite, but they must be visible and bounded.

Allowed in `hybrid` mode:

- Grant gold, food, levels, skills, and spellbooks at named checkpoints.
- Directly travel to a map when the scenario is not testing the travel mechanism.
- Kill or clear actors when the scenario is not testing combat.
- Grant quest items only when the route already proved the acquisition path in another focused scenario, or when the
  step explicitly states that the item acquisition is out of scope for that file.
- Set time/date for promotions and timed gates, then trigger the normal event.

Not allowed:

- Setting final qbits/awards/classes without running the NPC/event that grants them.
- Skipping a gate without asserting the blocked behavior somewhere in the suite.
- Hiding missing rows/assets with fallback defaults.

## MM6 Suite Structure

### P0 Smoke

`tests/scenarios/mm6/main_story.yml` should be the main acceptance route. It proves the game can reach both endings from
a clean party through the required story gates.

Required checkpoints:

- `new_sorpigal_started`: Enroth/MM6 selected, party spawned in New Sorpigal, Sulman's letter state exists.
- `letter_delivered`: letter path through New Sorpigal/Castle Ironfist works and reward state is correct.
- `council_quests_started`: council lords expose expected topics and initial qbits.
- `council_quests_complete`: awards 2, 3, 4, 5, 6, 7, and 32 are set through event/NPC turn-ins.
- `oracle_opened`: High Council/Oracle access is granted after council requirements.
- `memory_crystals_restored`: Alpha/Beta/Delta/Epsilon crystals are restored and qbits 162-165 are resolved.
- `control_cube_returned`: VARN Control Cube item 456 is accepted and Control Center access is granted.
- `blaster_ready`: Blaster skill/weapons are available through the Control Center path.
- `hive_entered`: Hive access, Hive Sanctum key, and late-game map/event hooks work.
- `good_ending`: reactor/queen/Ritual of the Void path grants award 36 and returns through good-ending flow.
- `bad_ending`: destruction failure route exits to main menu through the bad-ending/destroyed-world flow.

### MM6 Main Story Route Inventory

The scenario suite should cover these route segments. Exact map/event ids should be encoded in `aliases.yml` and
verified against the readable MM6 scripts during scenario authoring.

- New game and letter: select Enroth/MM6, create party, assert New Sorpigal start, Sulman's letter, and letter qbits.
- Potbello/Wilbur letter chain: show/deliver the letter through normal topics; assert reward, qbits, and topic changes.
- Nicolai edge case: take Nicolai, allow kidnap/circus flow, prove Kilburn turn-in refusal while he is missing, then
  recover him.
- Lord Kilburn's Shield: acquire/turn in shield; assert council award 2 and related topic state.
- Hourglass of Time: acquire/turn in hourglass; assert award 3 and quest item removal.
- Devil's Outpost: start Osric quest, acquire Devil Plans item 506, turn in; assert award 4 and qbit 113 cleared.
- Prince of Thieves: capture/turn in Prince of Thieves path; assert award 5 and follower/actor state.
- Stable prices: set all nine stable agreements through normal events or a focused stable scenario; assert award 6.
- End Winter: start Erik quest, resolve Hermit/weather path, turn in; assert award 7 and qbit 120 cleared.
- Slicker Silvertongue: prove Wilbur refusal/cure/traitor chain, Letter from Zenofex item 502, and award 32.
- High Council unlock: assert all council awards allow Oracle access and set the expected Oracle/council state.
- Memory crystals: acquire Alpha 550, Beta 551, Delta 552, Epsilon 553, restore them, and assert qbits 162-165.
- VARN: acquire Control Cube item 456, return it, assert qbit 166 cleared, and assert Control Center access.
- Control Center: learn/use Blaster skill, acquire Blaster/Blaster Rifle as required, assert sci-fi hooks and exit.
- Archibald/Ritual: prove the Archibald/Tanir's Bell/Third Eye/Ritual chain needed for the good ending.
- Hive good ending: enter Hive, acquire Hive Sanctum Key item 570 if needed, keep Ritual item 544, assert award 36.
- Hive bad ending: trigger the bad-ending route without correct containment/escape state; assert main-menu transition.

### MM6 Promotion Suite

`tests/scenarios/mm6/promotions.yml` should cover every original MM6 promotion family. Use party presets that include at
least one matching base class and at least one non-matching class so real and honorary award branches are both tested.

- Paladin -> Crusader: `GLOBAL.txt` events 13-14, qbit 88. Rescue Melody Silver follower 11, return to Wilbur,
  promote Paladin to Crusader, award 8; non-Paladins get award 9.
- Crusader -> Hero: `GLOBAL.txt` events 15-16, qbit 89. Acquire Dragon Claw item 455 from Longfang path, return to
  Wilbur, promote Crusader to Hero, award 10; honorary award 11.
- Cleric -> Priest: `GLOBAL.txt` events 35-36, qbit 105. Hire Stonecutter/Carpenter, repair Temple Stone, set qbit 106
  through normal event, return to Anthony, award 20; honorary award 21.
- Priest -> High Priest: `GLOBAL.txt` events 37-38, qbit 107. Acquire Sacred Chalice item 434, place it in the repaired
  temple to set qbit 108, return to Anthony, award 22; honorary award 23.
- Sorcerer -> Wizard: `GLOBAL.txt` events 55-58, qbit 111. Drink Fountain of Magic through map event, return to Albert,
  promote Sorcerer to Wizard, award 12; honorary award 13.
- Wizard -> Arch Mage: `GLOBAL.txt` events 59-60, qbit 112. Acquire Crystal of Terrax item 457, return to Albert,
  promote Wizard to Arch Mage, award 14; honorary award 15.
- Knight -> Cavalier: `GLOBAL.txt` events 65-69, qbit 114. Get nomination from Chadwick Blackpoole, return to Osric,
  promote Knight to Cavalier, award 16; honorary award 17.
- Cavalier -> Champion: `GLOBAL.txt` events 70-71, qbit 115. Defeat Warlord/acquire Discharge Papers item 508, return
  to Osric, promote Cavalier to Champion, award 18; honorary award 19.
- Druid -> Great Druid: `GLOBAL.txt` events 82-83 and 365, qbit 118. Set equinox/solstice time, trigger Ceremony of
  the Sun, promote Druid to Great Druid, award 24; honorary award 25.
- Great Druid -> Arch Druid: `GLOBAL.txt` events 84-85 and 366, qbit 119. Set full-moon midnight, trigger Ceremony of
  the Moon, promote Great Druid to Arch Druid, award 26; honorary award 27.
- Archer -> Battle Mage: `GLOBAL.txt` events 91-92, qbit 121. Acquire Dragon Tower Keys item 486, return to Erik,
  promote Archer to Battle Mage, award 28; honorary award 29.
- Battle Mage -> Warrior Mage: `GLOBAL.txt` events 93 and 100, qbit 122. Reset all Dragon Towers, assert qbits 156-161,
  return to Erik, award 30; honorary award 31.

Promotion assertions for every row:

- Initial topic is available only after the expected prerequisite.
- Refusal path works before the quest requirement is satisfied.
- Completion event clears the active quest qbit.
- Required quest item/follower is consumed or removed when the original event does so.
- Matching party member class changes to the promoted class.
- Non-matching member receives the honorary award and does not change class.
- Reputation, gold, and experience changes match the event contract where applicable.
- Save/load after completion preserves class, awards, qbits, topic changes, and followers.

## MM6 Focused Milestone Files

The full route can be long. Each major segment should also have a smaller scenario file that starts from a fixture
checkpoint and proves the segment in isolation:

```text
tests/scenarios/mm6/council.yml
tests/scenarios/mm6/oracle.yml
tests/scenarios/mm6/varn_control_center.yml
tests/scenarios/mm6/hive_endings.yml
tests/scenarios/mm6/promotions.yml
tests/scenarios/mm6/travel.yml
tests/scenarios/mm6/save_load.yml
```

These files let CI run a fast shard when one area changes, while the full route remains a nightly or manual gate.

## Save/Load Checkpoint Contract

Every scenario checkpoint should record:

- World id, map id, house id if any, coordinates, facing, and game time.
- Party roster, classes, levels, skills, conditions, inventory, equipment, gold, bank, food, and spellbooks.
- QBits, awards, autonotes, history, reputation, active followers, and NPC topic overrides.
- Current map vars, chest states, hidden decorations/sprites/faces, actor alive/dead/hostile state for touched maps.
- Active timers/refill state and pending transition/ending state.

The runner should save, reload into a fresh app/session, and compare a canonical snapshot. Differences must print a
small structured diff, not a full dump by default.

## Reports And Artifacts

On failure, write:

- `scenario-report.json`: scenario id, seed, mode, failed step, source file/line, elapsed time.
- `state-before.yml` and `state-after.yml` for the failed step.
- `latest-checkpoint.sav` or equivalent save artifact.
- `map-diagnostics.txt` for missing assets, missing events, missing topics, and load warnings.
- Optional `route-timings.csv` for map load and event timing.

Reports should mark failures as:

- `schema_error`
- `alias_resolution_error`
- `runtime_error`
- `assertion_failure`
- `missing_asset`
- `missing_script_binding`
- `timeout`

## Performance Expectations

The harness should avoid turning a proof route into a development bottleneck.

| Tier | Scope | Target |
| --- | --- | --- |
| P0 fast | New-game smoke, one council gate, one promotion, one save/load, one ending stub. | Less than 60 seconds. |
| P1 route shard | One major MM6 segment, such as council or promotions. | 1-5 minutes. |
| P2 full MM6 proof | Main story plus all promotions/checkpoints. | Nightly/manual; 10-30 minutes initially. |
| P3 exhaustive | Full route plus broad mechanics matrix and map sweeps. | Manual or scheduled long run. |

Keep scenarios shardable by file and by tag. Do not require the full route to run after every small code change.

## Implementation Phases

### Phase 1: Schema And Loader

- Add `tests/scenarios/schema/test_scenario.schema.yml`.
- Implement YAML parsing with source location tracking.
- Add `--headless-run-scenario` command that loads and validates a file, then prints a dry-run step list.
- Add unit tests for schema validation and alias resolution.

### Phase 2: Driver Extraction

- Extract reusable map/event/party helpers from existing headless diagnostics.
- Add `ScenarioWorldDriver`, `ScenarioPartyDriver`, and `ScenarioEventDriver`.
- Support `load_map`, `execute_event`, `assert`, and checkpoints for a minimal scenario.

### Phase 3: Alias Generation

- Add a tool or headless command that generates `tests/scenarios/mm6/aliases.generated.yml` from active tables.
- Add a curated `aliases.yml` that includes route-friendly names and imports/generated references.
- Validate that aliases used by scenarios resolve against mounted world/base data.

### Phase 4: MM6 P0 Smoke

- Implement `new_game_flow`.
- Prove Enroth selection, MM6 party creation, New Sorpigal start, Sulman's letter, and first save/load checkpoint.
- Add a small local/global event scenario using existing MM6 route data.

### Phase 5: MM6 Council Route

- Implement NPC topic driver, follower driver, inventory placement, direct travel shortcut, and refusal assertions.
- Write `council.yml` covering the six lord tasks plus Slicker Silvertongue.
- Assert the full council-ready state before Oracle access.

### Phase 6: Oracle, VARN, Control Center, Hive

- Implement needed chest/pickup/actor-clear shortcuts and ending assertions.
- Write `oracle.yml`, `varn_control_center.yml`, and `hive_endings.yml`.
- Add good-ending and bad-ending app-level assertions, including the bad-ending return to main menu.

### Phase 7: Promotions

- Write `promotions.yml` covering all twelve MM6 promotion steps.
- Add party presets for mixed real/honorary class coverage.
- Add refusal-before-completion checks for each promotion family.

### Phase 8: Full Route Assembly

- Compose the segment files into `main_story.yml`.
- Add checkpoint resume support so failures late in the route do not require rerunning the whole scenario during local
  debugging.
- Add JSON/JUnit reports and CI-friendly exit codes.

### Phase 9: MM7/MM8 Reuse

- Add MM7/MM8 alias generation.
- Port the scenario structure: `main_story.yml`, `promotions.yml`, `endings.yml`, `travel.yml`.
- Add world-specific route data only in YAML/aliases. Runner code should remain shared unless the runtime lacks a
  world hook.

## Acceptance Criteria For Calling MM6 Proven

- `--headless-run-scenario-suite tests/scenarios/mm6 --scenario-filter tier=P0` passes from a clean build.
- `main_story.yml` reaches the good ending and the bad ending from declared checkpoints.
- `promotions.yml` passes all original MM6 promotion families, including real and honorary branches.
- Every touched checkpoint survives save/load equivalence.
- The suite reports zero missing maps, event ids, NPC topics, house rows, item aliases, actor sprites, and required
  textures for maps touched by the scenarios.
- `MM6_MECHANICS_AUDIT_CHECKLIST.md` can mark the full MM6 playthrough and promotion-route rows as proven with links
  to these scenario files and their verification command.

## First Scenario Slice To Implement

Start with a narrow vertical slice:

```yaml
id: mm6.smoke.new_game_letter
world: mm6
mode: faithful
seed: 0x4d4d36
tags: [mm6, p0, smoke]

party:
  preset: mm6_story_party

steps:
  - new_game_flow:
      continent: enroth
      party: mm6_story_party

  - assert:
      map: oute3.odm
      inventory_any_member:
        - item: mm6.item.sulmans_letter
      qbit_set:
        - mm6.main.letter.show_to_potbello

  - save_checkpoint: new_sorpigal_started

  - talk_npc:
      npc: mm6.npc.andover_potbello
      topic: mm6.topic.letter

  - assert:
      qbit_clear:
        - mm6.main.letter.show_to_potbello
      qbit_set:
        - mm6.main.letter.deliver_to_wilbur
```

This first slice proves the harness can drive normal app flow, resolve aliases, execute dialogue, assert qbits/items,
and save/load a checkpoint. After that works, the council and promotion files can be built incrementally.
