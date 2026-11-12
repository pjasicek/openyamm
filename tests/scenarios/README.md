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

`assert: {chest_view: {open, chest_id}}` checks whether a chest's loot screen is open now, and
`assert: {party_position: {x, y, radius, z_min, z_max}}` that the party stands within `radius` (default 64) of a point
(`mm7/barrow_downs_teleporting_chest.yml`).

`interact_actor: {actor_index, activated: false}` passes only when the actor refuses the use (no dialogue, no event):
an MM9 dog (`mm9/animal_no_street_npc_dialogue.yml`).

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
A `new_game_flow` party member may carry `battle_orders: {fallback: weapon|hold, orders: [...]}`
(devdocs/BATTLE_ORDERS.md): each order is `{spell: <table name>}`, `{melee: true}` or `{shoot: true}` with optional
`distance: [min, max]`, `ally_hp_below` and `keep_sp` (percent), `place: anywhere|indoors|outdoors` and `enabled`; an
optional `upkeep: [...]` beside `orders` is the member's upkeep list, spell orders that may also carry `renew_below`
(game minutes). They are saved with the party.

For spells and auras: `cast_spell: {member_index, spell_id, skill, mastery: 1-4, actor_index, target_member,
target_point, scroll, expect}` casts through the party's spell system with full mana and no recovery (skill and mastery
set the spell's school first; `scroll: true` reads it from a scroll at that power instead; `target_point: [x, y, z]` is
the ground point of a spell cast at the ground, Meteor Shower or Starburst: `mm9/open_air_spells.yml`), and projectiles fly on with
`advance_runtime`; `assert: {actor_count: {..., shrunk: bool, hurt: bool}}` also filters by Shrinking Ray and by
missing HP; `assert: {buff: {spell_id, present, member_index}}` checks a party or member buff the spell set, and
`assert: {condition: {name, present, member_index}}` a member's condition by its `party_attack` name (any member
without an index; `mm7/emerald_island_cast_off_rest.yml`).
`party_charge: {actor_index, status, advance_seconds, min_moved}` runs the Knight Charge action at the actor: `status`
is the line the rules must give ("none" without a charge), then the run advances and the party must have moved at
least `min_moved` units (`maw_knight_charge.yml`). `assert: {actor_count: {..., hostile: bool}}` also filters by
hostility to the party, and `near: [x, y, radius]` by where the actors stand
(`mm8/mad_necromancers_lab_entry_aggro.yml`); `assert: {ruleset: {map_cleared: bool, map_slain_min: N}}` checks the
current map's MAW clear state and slain count since its last refill; `assert: {dimension_door: {pending}}` checks a
pending Dimension Door (the towns' dimensional travel pedestals, `dimensional_travel_pedestals.yml`). Event scripts can test
`evt.CheckMonstersKilled(ActorKillCheck.Hostile, 0, 0, false)`: every actor but the party's summons and allies
(`maw_endless_arena_level.yml`). `setup_shortcut: {kind: set_global_var, name, value}` sets a named global event
variable (MM7's cross-continent vars are `MMerge.CrossContinents.<name>`). `spawn_actor: {..., party_ally: true}`
summons the monsters as a party spell's summons, fighting for the party (an outdoor summon is Enslaved, an indoor one
ally 999); `setup_shortcut: {kind: set_experience, value, member_index}` sets a member's experience, or every
member's without an index; with `assert: {runtime_event_variable: {id: 13, member_index, value | min}}` this checks
kill experience (`maw_ally_kills.yml`, `standard_ally_kills.yml`). `assert: {dialog: {text_contains}}` checks a piece
of the open dialog's text. `advance_runtime: {seconds, present_dialogs: true}` opens a dialogue that a world event
queued during the step (an MM9 FoundPlayer greeting) as the game's frame does, which then stops the world; without it
a queued dialogue stays queued (`mm9/found_player_bootcamp.yml`). `assert: {journal_map_note: {map, id, text,
present}}` checks a journal map pin (`maw_bounty.yml`). `press_action: {action, seconds}` also takes any key
binding by its settings name (`attack`, `cast_ready`, `follower_1`, ...), held for one frame by default, and `setup_shortcut: {kind: hire_follower, id}` hires
an NPC as a follower (`follower_keys.yml`). `assert: {quick_item_ring: {open, member_index}}` checks the potion
radial's ring and `assert: {quick_item_popup: {kind, member_index}}` the basebar's potion or scroll popup
(`potion_slot_keys.yml`). Each run saves into its own temporary folder (`openyamm_scenario_saves/<id>-<random>`),
removed when it ends, so parallel runs of one scenario do not share saves.

For loads that must fail: `save_game: {name, required_package_schema: {package, schema}}` rewrites the save to need a
content package schema the game does not have, and `load_game: {name, expect_failure: true}` passes only when the
load is refused, leaving the game in progress (`cross_ruleset_load_failure.yml`, audit STD3-1). `save_game: {name,
block_with_directory: true, expect_failure: true}` puts a folder where the save file would go, so the write fails and
the step passes only then; `assert: {food: N}` checks the party's food (`maw_save_food_refund.yml`).
`save_game: {name, rebuilt_maps: [6d01.blv, ...]}` rewrites the save as if those maps were rebuilt after it (their
saved states record another layout identity), so loading it resets them (`release/rebuilt_map_save.yml`,
[saved map states](../../devdocs/SAVED_MAP_STATE_IDENTITY.md)).
`assert: {game_hour: N}` checks the clock's hour of the day, 0-23 (`mm7/stone_city_inn_rest.yml`).
`quick_load: {save, expect: loaded | warned, expect_status}` presses the quick load key (F10) once with a scenario save
as the quicksave, from a scratch working folder so the real `saves/quicksave.oysav` is never read
(`maw_quick_load_warning.yml`).
Scenarios read the local `settings.ini` but always run with the Immortal cheat off, so a `party_health` check gives the
same answer on every machine (`mm6/abandoned_temple_cage_trap.yml`).

`lua_event: {source}` runs the scenario's own Lua as an event of the current map, after the map's event support
(`evt.SummonMonstersById`, `evt.SetActorTarget` ...); a Lua error fails the step (`mm9/ai/lua_summon.yml`). The console
`destructible <id> state` reports a scene destructible's hp and whether it stands (`mm9/destructibles/`).

Long story and quest runs are not routine tests: `mm9/side_quests/` (one scenario per MM9 side quest, its own
`run.py`) and the chained `tests/playthrough/` segments take minutes each, so do not sweep them with the other
scenarios; run them only as the [Playthrough playbook](../playthrough/PLAYBOOK.md) says (when asked, before a release,
after a change that can break a story, and then only the affected ones).

For playthroughs ([MM9 playthrough](../playthrough/mm9/README.md)): `walk_to: {x, y, z | to, via: [[x, y, z] | pose],
radius, z_tolerance, timeout_seconds, clear_hostiles, expect_map, plan, node_limit, close_dialogs, expect:
arrived|dialog}` walks the party there with the movement keys on a route from the monsters' indoor path map (when stuck
it aims further, jumps, steps aside, clicks what is ahead and plans again; it fails, naming the spot, after twelve tries
in one place) and prints its trail (`WALK` lines); a dialogue an event opens on the way (an exit's prompt) ends it,
which `expect: dialog` wants. `clear_hostiles: {radius, min}` kills the party's enemies near it. `play_lua: {source,
max_seconds}` runs a player's reasoning in Lua: `click(event_id)`, `wait(seconds)`, `status()` (the status lines since
the last call), `qbit(id)`, `has_item(item_id)`, `mapvar(name)`, `held()` (the item on the cursor, 0: none), `stow()` (puts the cursor item into the packs, the active member's first, as
a player does; false when it fits nobody),
`item_count(item_id)` (in the packs), `pack_items()` (every pack item), `discard(item_id)` (drops one from the packs),
`door_state(id)` (open, closed, opening, closing), `take_chest()` (the open chest's Take All), `close()` (Escape),
`classes()` (the members' class names, space-separated), `party()` (for a log line: the selected member's index and
each member's name, actual Might and condition bits), `experience(index)` (a member's, from 0), `conditions(index)` (a member's condition names,
space-separated), `gold()`,
`remember(key, value)` and `recall(key)` (a value kept for the later `play_lua` steps of the run, such as the classes,
experience or gold before a reward; nil when never remembered), `clear_hostiles(radius)` (kills the party's enemies
near it, returns how many), `log(text)`. Two helpers are written in Lua over these: `open_door(event_id, door_id)`
waits until a door stops moving (a click on a moving door does nothing; monsters open some doors and many close by
themselves), clicks it if it is shut and waits until it stands open, killing enemies in its swing meanwhile;
`loot_chest(event_id)` opens a chest and takes all, clicking again when a trap the party cannot disarm went off and
left it shut.
`party_defeat: {wait_seconds, knock_out, expect_map, expect_game_over}` waits until nobody can act (`knock_out`: every
member falls at once), then runs the game's defeat and respawn; a defeat the world counts as lost (world.yml
`partyDeath` `when`, MM9's game over) loads nothing headless (never the player's autosave), prints `DEFEAT game over`
and passes only with `expect_game_over: true` (`mm9/defeat_arslegard_rule.yml`). `walk_to` goes on after a teleport
on the same map (a move over 512 in one frame, or a same-map move event) from the route point nearest to where the
party landed, so via points on the pad and the arrival as the target walk through a teleporter; when a friendly actor
holds the party up it goes round it, waits for it or backs off instead of counting the spot as stuck. `setup_shortcut: {kind: immortal, value}` is the Immortal cheat for the
run only. `save_game: {name, path}` keeps the save at a path (relative to the working folder) after the run.
`select_topic: {match_label}` without `action_id` picks the line by its text (exactly, else the one containing it) and,
when missing, lists the lines offered. `climb: {ladder, down, timeout_seconds}` walks to a scene ladder's foot (down:
its top exit, which needs `grab_at_top`), faces it and climbs with the movement keys through the game's ladder rules; it
fails unless the party takes hold within 3 s and lets go at the other end (`CLIMB` lines). `pick_up: {item_id, reach}`
takes an item lying in the map: within `reach` (default 400) of the party's eye, the camera turned at it, the use key;
the item must reach the party (`PICKUP` lines).

For cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md): `advance_runtime: {seconds, follow_map_move: true}` carries
out a map move an event of the step asked for (a cinematic's last event, an exit), as the game's frame does; without
it the move stays pending for later steps (`assert: {map_transition_requested: ...}`). `console: cinematic list`,
`cinematic play <id>` and `cinematic skip` drive and check a cinematic (`mm9r_isleofashes_blv/cinematic_*.yml`).

For swimming (scene `water_volumes`, devdocs/INDOOR_OPEN_SKY.md "Swimming"): `assert: {water: {state, eye_under,
breath_min, breath_max, drowning_ticks_min, drowning_ticks_max, foot_z_min, foot_z_max}}` checks the party's water
state (`dry`, `wading`, `falling`, `bed`, `submerged`, `surface`, `surface_jump`), its breath (1 full, 1 with the eye
out), the drowning ticks taken on this map and its feet's height; the swim keys are `movement_segment`'s `jump`,
`fly_up`, `fly_down` with the pitch from `start` (Verhoffin Ruins' `scenario_swim.yml`).

For monster AI (AI arenas, [mm9/ai/README.md](mm9/ai/README.md)): `ai_arena: {path, log}` sets an arena up (the map's
actors hidden, the arena's monsters spawned, the party placed, the decision trace on), `assert: {ai_trace:
{actor_index | arena_monster, decision | event, target, min_count, max_count, within_seconds, after, before, report}}`
(`decision` one name or a list, any of which matches; `target` a whole target such as `actor:12` or its kind, `actor`)
counts decision trace lines and `ai_trace_dump: {actor_index | arena_monster, decisions_only, last}` prints them.

For turn-based combat ([TURN_BASED_COMBAT_AUDIT.md](../../devdocs/TURN_BASED_COMBAT_AUDIT.md), `turn_based/`):
`press_action: combat` toggles turn-based mode, `turn_based_turns: {count, max_seconds}` plays turns through the input
path (Pass whenever the party may; a turn counts when it reaches its movement phase), and `assert: {turn_based:
{active, stage, front_member, actor_index, actor_queued, actor_effect, effect_min, effect_max, report}}` checks the turn
engine (`front_member` is the member the queue waits for, or `none`; `actor_effect: slow | stun | paralyze` with
`effect_min`/`effect_max` checks the remaining seconds of a monster's effect; `report` prints the queue).
`assert: {member_points: {member_index, spell_points_min, spell_points_max, health_min, health_max}}` checks a member's
points, `setup_shortcut: {kind: set_member_points, member_index, health, spell_points}` sets them, and `buff` takes
`remaining_min`/`remaining_max` in game seconds. The driver applies a completed turn's game time after each gameplay
update, as the game's frame does. The `turn_based/` scenarios guard the audit's fixed findings and are part of the
release list.
