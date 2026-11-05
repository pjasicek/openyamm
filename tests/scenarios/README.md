# Headless scenarios

`./build/game/openyamm --headless-run-scenario <scenario.yml>` runs a scenario; `--headless-validate-scenario` only
loads it. The loader is `game/scenario/ScenarioYamlLoader.cpp`, the runner `game/scenario/ScenarioRunner.cpp`.

## Unknown keys are errors (2026-10-23)

A scenario fails to load, naming the file, line, step and key, when a step uses:

- an unknown step type (`unknown scenario step 'teleport_party'`);
- a payload key its step does not know (`unknown spawn_actor key 'hostile' (known: ...)`);
- inside `assert`, an unknown assert key (`unknown assert key 'homing_endz'`), or an unknown key in the blocks checked
  field by field: `projectiles`, `homing_ends`, `party_health`, `charges`, `actor_visible`, `mechanism`,
  `runtime_event_variable`, `ruleset`; inside `wait_until.assert` anything but `mechanism`; in `press_action`'s `expect`
  anything but `dialogue_canceled` and in its `expect_before` anything but `dialog`.

Before this a key the runner did not read passed silently (a `homing_ends` check "passed" before it existed). The key
lists (`stepKeyTable`, `AssertKeys`, `AssertBlockKeys` in the loader) name the keys the runner reads, then, marked
"recorded:", the descriptive fields of recorded trace exports that the runner keeps but does not check (for example
`scene_kind`, `method`, `state_dump_party`, `new_game_started`). Every step may also carry `note`, `reason`,
`source_note` and `game_minutes`; `note`, `todo` and `trace_observation` steps take any keys. A `setup_shortcut` of an
unknown `kind` now fails when it runs (it was skipped).

When a runner check is added, add its key to the loader's lists in the same change.

Checks added with this rule: `assert: {gold: N}` (the party's gold), `assert: {mechanism: {...}}` (as
`assert_mechanism`), `press_action: {action: escape|cancel_dialog, expect: {dialogue_canceled: {...}}}`, and for the
charge modifier `charge_actor: {actor_index}` and `assert: {charges: {started, hits, misses, min_started, min_hits,
min_misses}}`, `right_click_portrait: {item_id, carrier_index, member_index, inventory, release, expect}` (right-clicks
a portrait with a pack item under the cursor through the live input path; a scroll's text must close on release, or with
`release: true`, the Modern gesture of pressing on the crosshair and releasing on the portrait, stay until a left click;
`mm8_right_click_portrait_item.yml`), and for rulesets `assert: {ruleset: {..., rolled_items_min, report_items}}` (how
many pack items the ruleset rolled, a loot rarity on the item; `report_items: true` prints every pack item with its
ruleset fields).

For MAW's content (phase 8): `execute_event: {id}` runs a map or global event; `assert: {actor_count: {name, monster_id,
boss, min, max}}` counts living actors; `grant_item: {..., dimension_map: {map_id, affixes, active, power}}` gives a
dimension map; `ruleset_banks: {..., completed_maps: [file names], dimension_quest_done}` sets MAW state; and
`assert: {ruleset: {dimension_run: {map, power, affix_count, completed, min_family_actors} | {map, none: true},
dimension_quest: {tier, given, cleared, done}}}` checks dimension maps. `use_item` follows a travelling item's move.
`console: {line, expect_contains}` runs a debug console line in the game as typed and fails on a console error or
when the output lacks the text (`rulesets/maw_test_parties.yml` loads every MAW test party with `testparty apply`).

For MAW's combat (GAPS.md): `party_attack: {actor_index, member_index, count, conditions: [weak, ...], record,
ratio_to, damage_ratio: [min, max], applied_ratio, recovery_ratio: [min, max], min_hit_rate, max_hit_rate, min_average,
max_average, attack_spell, min_weapon_attacks, max_weapon_attacks, report}` runs a member's real attacks on an actor,
healed after each blow, and compares the average damage and recovery with a recorded run (`attack_spell` sets the
member's attack spell for the run and lets the attack cast it; the weapon-attack bounds count swings and shots, which a
spell cast is not: `maw_assassin_attack_spell.yml`); `spawn_actor: {monster_id, near_party: true}` summons beside the party;
`damage_actor: {..., expect: refused}` passes when the hit does nothing; and a scenario's ruleset takes
`friendly_fire: true` (or the option id `friendlyfire`) so hits on townsfolk count. A ruleset also takes `bow_disabled: true`
(or the option ids `nobow` and `bow`, also for `set_ruleset`), MAW's Bow preference, which `assert: {ruleset: {...,
bow_disabled}}` checks; `assert: {projectiles: {source: party, ...}}` counts the party's live missiles instead of
the actors' (`maw_bow_disabled.yml`).

For spells and auras: `cast_spell: {member_index, spell_id, skill, mastery: 1-4, actor_index, target_member, scroll,
expect}` casts through the party's spell system with full mana and no recovery (skill and mastery set the spell's
school first; `scroll: true` reads it from a scroll at that power instead), and projectiles fly on with
`advance_runtime`; `assert: {actor_count: {..., shrunk: bool, hurt: bool}}` also filters by Shrinking Ray and by
missing HP; `assert: {buff: {spell_id, present, member_index}}` checks a party or member buff the spell set, and
`assert: {condition: {name, present, member_index}}` a member's condition by its `party_attack` name (any member
without an index; `mm7/emerald_island_cast_off_rest.yml`).
`party_charge: {actor_index, status, advance_seconds, min_moved}` runs the Knight Charge action at the actor: `status`
is the line the rules must give ("none" without a charge), then the run advances and the party must have moved at
least `min_moved` units (`maw_knight_charge.yml`). `assert: {actor_count: {..., hostile: bool}}` also filters by
hostility to the party; `assert: {ruleset: {map_cleared: bool, map_slain_min: N}}` checks the current map's MAW
clear state and slain count since its last refill; `assert: {dimension_door: {pending, without_quest}}` checks a
pending Dimension Door (MAW's town pedestals open it without the Cross Continents quest). Event scripts can test
`evt.CheckMonstersKilled(ActorKillCheck.Hostile, 0, 0, false)`: every actor but the party's summons and allies
(`maw_endless_arena_level.yml`). `setup_shortcut: {kind: set_global_var, name, value}` sets a named global event
variable (MM7's cross-continent vars are `MMerge.CrossContinents.<name>`). `spawn_actor: {..., party_ally: true}`
summons the monsters as a party spell's summons, fighting for the party (an outdoor summon is Enslaved, an indoor one
ally 999); `setup_shortcut: {kind: set_experience, value, member_index}` sets a member's experience, or every
member's without an index; with `assert: {runtime_event_variable: {id: 13, member_index, value | min}}` this checks
kill experience (`maw_ally_kills.yml`, `standard_ally_kills.yml`). `assert: {dialog: {text_contains}}` checks a piece
of the open dialog's text and `assert: {journal_map_note: {map, id, text, present}}` a journal map pin
(`maw_bounty.yml`). `press_action: {action, seconds}` also takes any key binding by its settings name (`attack`,
`cast_ready`, `follower_1`, ...), held for one frame by default, and `setup_shortcut: {kind: hire_follower, id}` hires
an NPC as a follower (`follower_keys.yml`). `assert: {quick_item_ring: {open, member_index}}` checks the potion
radial's ring and `assert: {quick_item_popup: {kind, member_index}}` the basebar's potion or scroll popup
(`potion_slot_keys.yml`). Each run saves into its own temporary folder (`openyamm_scenario_saves/<id>-<random>`),
removed when it ends, so parallel runs of one scenario do not share saves.

For loads that must fail: `save_game: {name, required_package_schema: {package, schema}}` rewrites the save to need a
content package schema the game does not have, and `load_game: {name, expect_failure: true}` passes only when the
load is refused, leaving the game in progress (`cross_ruleset_load_failure.yml`, audit STD3-1). `save_game: {name,
block_with_directory: true, expect_failure: true}` puts a folder where the save file would go, so the write fails and
the step passes only then; `assert: {food: N}` checks the party's food (`maw_save_food_refund.yml`).
`assert: {game_hour: N}` checks the clock's hour of the day, 0-23 (`mm7/stone_city_inn_rest.yml`).
`quick_load: {save, expect: loaded | warned, expect_status}` presses the quick load key (F10) once with a scenario save
as the quicksave, from a scratch working folder so the real `saves/quicksave.oysav` is never read
(`maw_quick_load_warning.yml`).
Scenarios read the local `settings.ini` but always run with the Immortal cheat off, so a `party_health` check gives the
same answer on every machine (`mm6/abandoned_temple_cage_trap.yml`).

For swimming (scene `water_volumes`, devdocs/INDOOR_OPEN_SKY.md "Swimming"): `assert: {water: {state, eye_under,
breath_min, breath_max, drowning_ticks_min, drowning_ticks_max, foot_z_min, foot_z_max}}` checks the party's water
state (`dry`, `wading`, `falling`, `bed`, `submerged`, `surface`, `surface_jump`), its breath (1 full, 1 with the eye
out), the drowning ticks taken on this map and its feet's height; the swim keys are `movement_segment`'s `jump`,
`fly_up`, `fly_down` with the pitch from `start` (Verhoffin Ruins' `scenario_swim.yml`).

For monster AI (AI arenas, [mm9/ai/README.md](mm9/ai/README.md)): `ai_arena: {path, log}` sets an arena up (the map's
actors hidden, the arena's monsters spawned, the party placed, the decision trace on), `assert: {ai_trace:
{actor_index | arena_monster, decision | event, target, min_count, max_count, within_seconds, after, before, report}}`
counts decision trace lines and `ai_trace_dump: {actor_index | arena_monster, decisions_only, last}` prints them.
