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
(`mm7/barrow_downs_teleporting_chest.yml`); with `facing` (the game's direction units: 0 east, 512 north, as an
arrival's facing) also that it faces within `facing_within` (default 64) of it.

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
`assert: {ruleset: {dimension_run: {map, power, affix_count, completed, inside, min_family_actors} | {map, none: true},
dimension_quest: {tier, given, cleared, done}}}` checks dimension maps: the open rift wherever the party is, and
`inside` whether the party stands in it (the same map file is then the rift, not the map itself). `use_item` follows a
travelling item's move, also for an item that is kept (the Dimensional Portal, 1071); `load_map` leads to the map
itself.
`equip_item: {item_id, member_index, slot}` wears an item the party already carries (any member's pack, the wearer's
first) on the member in the slot (`main_hand`, `armor`, ...) under the game's wearing rules, as dropped on the paperdoll;
what the slot held goes to the packs (`xeen/equip_carried_item.yml`).
`console: {line, expect_contains}` (and `expect_refusal: <text>`: the line must fail, saying that) runs a debug
console line in the game as typed and fails on a console error or
when the output lacks the text (`rulesets/maw_test_parties.yml` loads every MAW test party with `testparty apply`).

For MAW's combat (GAPS.md): `party_attack: {actor_index, member_index, count, conditions: [weak, ...], record,
ratio_to, damage_ratio: [min, max], applied_ratio, recovery_ratio: [min, max], min_hit_rate, max_hit_rate, min_average,
max_average, attack_spell, min_weapon_attacks, max_weapon_attacks, report}` runs a member's real attacks on an actor,
healed after each blow, and compares the average damage and recovery with a recorded run (`attack_spell` sets the
member's attack spell for the run and lets the attack cast it; the weapon-attack bounds count swings and shots, which a
spell cast is not: `maw_assassin_attack_spell.yml`); `spawn_actor: {monster_id, near_party: true}` summons beside the party;
`damage_actor: {..., expect: refused}` passes when the hit does nothing (`all: true, spare: N` kills every actor but
the first N, for a map left almost cleared: `maw_dimension_map_repeat.yml`); and a scenario's ruleset takes
`friendly_fire: true` (or the option id `friendlyfire`) so hits on townsfolk count. A ruleset also takes `bow_disabled: true`
(or the option ids `nobow` and `bow`, also for `set_ruleset`), MAW's Bow preference, which `assert: {ruleset: {...,
bow_disabled}}` checks; `assert: {projectiles: {source: party, ...}}` counts the party's live missiles instead of
the actors' (`maw_bow_disabled.yml`).
`new_game_flow: {ruleset: "standard:solo"}` is a solo run under Standard rules (a party of one, as the New Game
screen's Solo run row starts it); `"standard"` alone is the default.
A `new_game_flow` party member may carry `battle_orders: {fallback: weapon|hold, orders: [...]}`
(devdocs/BATTLE_ORDERS.md): each order is `{spell: <table name>}`, `{melee: true}`, `{shoot: true}` or, for a MAW
solo run, `{talent: <talents.yml id>}` with optional
`distance: [min, max]`, `ally_hp_below` and `keep_sp` (percent), `place: anywhere|indoors|outdoors` and `enabled`; an
optional `upkeep: [...]` beside `orders` is the member's upkeep list, spell orders that may also carry `renew_below`
(game minutes), and potion orders `{potion: <item id>, stock: <drinks>, brew_power, bottle: strongest|weakest}`. They
are saved with the party.

For spells and auras: `cast_spell: {member_index, spell_id, skill, mastery: 1-4, actor_index, target_member,
target_point, scroll, expect}` casts through the party's spell system with full mana and no recovery (skill and mastery
set the spell's school first; `scroll: true` reads it from a scroll at that power instead; `target_point: [x, y, z]` is
the ground point of a spell cast at the ground, Meteor Shower or Starburst: `mm9/open_air_spells.yml`;
`telekinesis_chest: <index>` is the chest Telekinesis is aimed at: `coop/net_guest_telekinesis.yml`), and projectiles fly on with
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
of the open dialog's text; `assert: {dialog: {adventurers_inn: true|false}}` whether the Adventurer's Inn's roster (or a character viewed from it) is open, which `press_action: {action: escape}` and `play_lua` `close()` close as its Exit button does (`xeen/inn_roster_close.yml`). `advance_runtime: {seconds, present_dialogs: true}` opens a dialogue that a world event
queued during the step (an MM9 FoundPlayer greeting) as the game's frame does, which then stops the world; without it
a queued dialogue stays queued (`mm9/found_player_bootcamp.yml`). `assert: {journal_map_note: {map, id, text,
present}}` checks a journal map pin (`maw_bounty.yml`). `press_action: {action, seconds}` also takes any key
binding by its settings name (`attack`, `cast_ready`, `follower_1`, ...), held for one frame by default; a move within
the map that a step asks for while it is held (a plate's teleport) happens in that frame, as in the game, and the held
key walks on from there (a move to another map waits for a step that follows map moves); `movement_segment` stops
steering the camera toward `expect_stop`'s facing once an event has moved the party (`xeen/dd17_belt_forward_held.yml`);
and `setup_shortcut: {kind: hire_follower, id}` hires
an NPC as a follower (`follower_keys.yml`). `assert: {quick_item_ring: {open, member_index}}` checks the potion
radial's ring and `assert: {quick_item_popup: {kind, member_index}}` the basebar's potion or scroll popup
(`potion_slot_keys.yml`). `debug_launch: {startup_console_file: <path>}` runs a start-of-map console file as the
game does for `debug.startup_console_file`, and `debug_launch: {exit_pose: true, expect_contains: [...]}` writes the
exit pose file of `debug.exit_pose_path` into the run's folder and checks its text (`debug/play_here.yml`, the Map
Studio's Play here). Each run saves into its own temporary folder (`openyamm_scenario_saves/<id>-<random>`),
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
(`evt.SummonMonstersById`, `evt.SetActorTarget` ...), and the world then takes its changes as after a map event (hostility, `evt.SetMonsterRelation` rows); a Lua error fails the step (`mm9/ai/lua_summon.yml`, `mm7/monster_relation_stays_with_map.yml`). The console
`destructible <id> state` reports a scene destructible's hp and whether it stands (`mm9/destructibles/`).

Long story and quest runs are not routine tests: `mm9/side_quests/` (one scenario per MM9 side quest, its own
`run.py`) and the chained `tests/playthrough/` segments take minutes each, so do not sweep them with the other
scenarios; run them only as the [Playthrough playbook](../playthrough/PLAYBOOK.md) says (when asked, before a release,
after a change that can break a story, and then only the affected ones).

For playthroughs ([MM9 playthrough](../playthrough/mm9/README.md)): `walk_to: {x, y, z | to, via: [[x, y, z] | pose],
radius, z_tolerance, timeout_seconds, clear_hostiles, clear_height, expect_map, plan, node_limit, close_dialogs, expect:
arrived|dialog}` walks the party there with the movement keys on a route from the monsters' indoor path map (when stuck
it aims further, jumps, steps aside, clicks what is ahead and plans again; it fails, naming the spot, after twelve tries
in one place) and prints its trail (`WALK` lines); a dialogue an event opens on the way (an exit's prompt) ends it,
which `expect: dialog` wants. `clear_hostiles: {radius, height, min}` kills the party's enemies near it: within `radius` across the ground and `height` above or below the party's feet (default indoors 384, less than a storey, so monsters on the floors above and below live, unless the radius is 5,000 or more: a map clear, every storey; outdoors the radius); `walk_to`'s `clear_height` and Lua's `clear_hostiles(radius, height)` take the same height, and `open_door`'s clear (1,500) uses the default. `heal_at_temple: {house, min}` buys the temple's Heal (house `house`, its prices) for every member it can treat, each selected in turn as at the counter, and prints a `HEAL` line each; it fails below `min` treated (`playthrough_tools/heal_at_temple.yml`): a segment whose party came out of its fights Weak or Petrified heals it before going on (the party stands at the temple's door in the segment's walk; the step does not walk there). `play_lua: {source,
max_seconds}` runs a player's reasoning in Lua: `click(event_id)`, `wait(seconds)`, `status()` (the status lines shown since
its last call, in this step or an earlier one: a `walk_to`'s step plate, a move within the map), `qbit(id)`, `journal_quest(qbit)` (the text of the quest note the journal shows under that qbit, nil when it shows none), `has_item(item_id)`, `ground_items(item_id)` (how many lie in the map, falling ones included), `mapvar(name)` (a number reads the numbered variable a Map Studio map uses, `MapVar(n)`: its project's ids.lock.yml `map_vars` give the numbers), `held()` (the item on the cursor, 0: none), `stow()` (puts the cursor item into the packs, the active member's first, as
a player does; false when it fits nobody),
`item_count(item_id)` (in the packs), `pack_items()` (every pack item), `discard(item_id)` (drops one from the packs),
`door_state(id)` (open, closed, opening, closing), `take_chest()` (the open chest's Take All), `close()` (Escape),
`classes()` (the members' class names, space-separated), `party()` (for a log line: the selected member's index and
each member's name, actual Might and condition bits), `experience(index)` (a member's, from 0), `conditions(index)` (a member's condition names,
space-separated), `gold()`,
`remember(key, value)` and `recall(key)` (a value kept for the later `play_lua` steps of the run, such as the classes,
experience or gold before a reward; nil when never remembered), `clear_hostiles(radius[, height])` (kills the party's enemies
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
fails unless the party takes hold within 3 s and lets go at the other end (`CLIMB` lines). `pick_up: {item_id, reach, gained}`
takes an item lying in the map: within `reach` (default 400) of the party's eye, the camera turned at it, the use key;
the item must reach the party (`PICKUP` lines).

For cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md): `advance_runtime: {seconds, follow_map_move: true}` carries
out a map move an event of the step asked for (a cinematic's last event, an exit), as the game's frame does; without
it the move stays pending for later steps (`assert: {map_transition_requested: ...}`). `console: cinematic list`,
`cinematic play <id>` and `cinematic skip` drive and check a cinematic (`mm9r_isleofashes_blv/cinematic_*.yml`).

Scene and cinematics overlays on shipped maps (an overlay's ladders, actors and floor items;
`<stem>_<name>.cinematics.yml` merged by id; saves of a map made with and without an overlay): `scene_overlays/`,
whose overlays sit in its own test mount (`scene_overlays/mount/`, passed with `--extra-mount`), never in `assets_dev`.
Run them with `tests/scenarios/scene_overlays/run.sh`, which passes the mount where a scenario needs it and runs the
three save scenarios in order, in one user-data folder.

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
`press_action: combat` toggles turn-based mode, `turn_based_turns: {count, max_seconds, game_speed}` plays turns through
the input path (Pass whenever the party may; a turn counts when it reaches its movement phase; `game_speed` multiplies
each 1/30 s frame as fast mode and the turn-based speed settings do), and `assert: {turn_based:
{active, stage, front_member, actor_index, actor_queued, actor_effect, effect_min, effect_max, report}}` checks the turn
engine (`front_member` is the member the queue waits for, or `none`; `actor_effect: slow | stun | paralyze | fear |
control` with `effect_min`/`effect_max` checks the remaining seconds of a monster's effect, control being its charm,
berserk or enslavement, and `actor_index` may be `last`; `report` prints the queue).
`assert: {member_points: {member_index, spell_points_min, spell_points_max, health_min, health_max}}` checks a member's
points, `setup_shortcut: {kind: set_member_points, member_index, health, spell_points}` sets them, and `buff` takes
`remaining_min`/`remaining_max` in game seconds. The driver applies a completed turn's game time after each gameplay
update, as the game's frame does. The `turn_based/` scenarios guard the audit's fixed findings and are part of the
release list.

## A party down fails a playthrough step (D-82, 2026-11-21)

A scenario tagged `playthrough` or `side_quest` fails at any step (except `party_defeat`) after which no member can
act (all Dead, Eradicated, Petrified, Paralyzed or Unconscious: `Party::hasActableMember`, the game's defeat rule in
`GameApplication::shouldTriggerPartyDefeat`). Headless runs never run the defeat themselves, so before this a story
went on with a party the game would already have defeated. The failure names the step and each member's conditions:
`PARTY DOWN after step 12 (the game would run its defeat here): member 0 Dead | member 1 Paralyzed | ...`. Other
scenarios, among them those that test a defeat, are not checked.

## Co-op scenarios (2026-11-19)

`coop/` holds the scenarios for several players in one game with no network (slice D of
`devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md`, "Two players as built"). They are not in the release list.
The local player is player 0; the console adds the others.

- `console: {line: "coop on"}` starts a session and `coop add [dx dy]` adds a player with a copy of the local party
  beside it. `coop pose <p> x y z` places a player, `coop damage <p> <amount>` hurts every member, `coop mark <p>`
  notes its hit points for a later `coop check <p> hp_lost`, `coop remove <p>` takes the player out and `coop show`
  lists everyone (a player in the air by Fly is marked `flying`) and a waiting travel proposal.
- `coop check <p> <hp|max_hp|hurt|xp|gold|food|down|day|auras|quest_items|bag_items> <op> <value>` fails the step
  when the comparison does not hold (`day` is the game day counted from the start, the same for every player;
  `auras` the number of auras the ruleset keeps for that party; `quest_items` what lies in the world's quest pouch
  as that party sees it; `bag_items` what lies in its members' open bags).
- `coop net` ends each other player's line with the member of its party that stands for it and the party's gear
  tier ("member 2 gear 3"), then the last thing its body showed doing ("action 3 cast": the count of its actions
  and melee, shot or cast). `coop avatar [member]` picks the member of the game's own party the others see (1 the
  first), or says who it is.
- `coop propose <map file>` proposes a trip to the other players as an exit taken would; the vote's window is then
  answered with `select_topic: {match_label: "Travel"}` and the like (a host's needs
  `advance_runtime: {present_dialogs: true}` first). `coop sync [player]` gathers the players for a test.
- `coop stepout` (a guest's game) leaves for its own game with the seat kept, `coop stepback` joins that session
  again where the game can by itself (a scenario joins again with `coop_join`, which takes the seat as well), and
  `coop away` says what this game is away from, or how many seats a host keeps.
- `coop chest <p> [show|take|close]` reports the chest that player has open, takes everything from it or closes it.
- `coop vote <p> yes|no` answers a travel proposal, `coop vote force` forces it and `coop return <p>` brings a
  downed player back.
- Steps for another player: `party_attack: {player}` (with `kill: true` the step ends on the kill and the target is
  not healed between blows), `cast_spell: {player, target_player}` (`target_player` names whose character
  `target_member` is), `lua_event: {player, source}` and `spawn_actor: {near_player}`.
- A scripted move out of a dungeon opens the transition prompt, in a single-player game too, so a travel vote is
  tested from an outdoor map.
- `coop dialog <p> [<choice>|close]` shows the dialogue the host keeps for that player, makes a choice by its place
  or closes it. `coop rest [<p> yes|no]` shows the rest that is asked or answers it for a player; the console's own
  `rest heal <minutes>` asks. `coop shop [buy <slot>]` shows the stock screen the local player has open and buys.

Two games in one scenario (slice E, "The replica as built"): the step `coop_guest: {}` makes a second game in the
same process, and a step with the key `game: guest` beside its kind runs in that game (its own new game, console,
asserts, casts). `coop_join: {expect: joined}` lets the first game host and the second join it through the real
messages. From then on every frame of one game is a frame of the other. `coop net` in either game reports the
connection and the traffic. The `net_*.yml` scenarios are the examples.

- `coop_join: {expect: joined, character: <name>}` joins with the character file of that name
  (`saves/characters/<name>.oychar` in the run's user data folder) and not with the guest game's own character. The
  console's `coop character save <name>` writes such a file from the game in progress, `coop character` lists the
  files and `coop character write` writes a joined guest's file now (`net_character_file.yml`).
- `coop say <words>` says a line to the other players, `coop ping [x y z]` points them at a place and `coop chat`
  lists what was said and what is pointed at (`net_chat_and_ping.yml`).
- `coop keep <name> [replace]` in a guest's game saves a copy of the host's whole world with the guest's character
  as `saves/<name>.oysav`; `load_game: {path: saves/<name>.oysav}` loads it (`net_world_copy.yml`).
- `coop_network: {delay_ms, jitter_ms, loss_permille, seed}` (a host step, after `coop_guest`) makes the line between
  the two games bad both ways, from then on and for a join that follows: everything is late by `delay_ms` and up to
  `jitter_ms` more; what must arrive still does, in order; of the messages where only the newest counts (where
  monsters, missiles and players are) `loss_permille` in a thousand are lost and an overtaken one is dropped. An empty
  map makes the line good again (`net_bad_line.yml`).
- `tools/coop_bad_line/run.sh [delay_ms] [jitter_ms] [loss_permille]` runs every `net_*.yml` over such a line (a copy
  of each gets the step). The scenarios' waits are written for a good line, so much more than 100 ms each way fails
  them for being late.
