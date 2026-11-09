# Playthrough playbook

How to build a repeatable, headless "a player can do this" run of a story, a quest line or any multi-map scenario,
and how to use it to find bugs. Written from the MM9 main-story playthrough (`tests/playthrough/mm9/`, 2026-11-08),
which goes from a new game to the game's completion in about 60 segments; the method is not MM9-specific.

## 1. What it is and what it proves

A playthrough is a chain of ordinary headless scenarios (**segments**). Each loads the checkpoint save the previous
one wrote, plays one leg of the story as a player would, asserts what that leg must produce (quest bits, items, map
state, the map it ends on) and saves its own checkpoint. `run.py` runs them in order, stops at the first failure and
writes a report with the evidence (dialogue lines picked, games won, where the party walked and got stuck, enemies
cleared, ISSUE lines).

It proves that the story can be finished with the game's own rules: real dialogue lines, real event clicks, real
walking through dungeons, real map transitions, real saves. It does **not** test combat or balance (the party is
immortal and enemies near it die).

It is a long check, not a routine test: it is not in CI (CI plays only `tests/scenarios/release/scenarios.txt`) and
is not run for ordinary changes. Run it when asked, before a release, or after a change that can break a story
(converter changes, map rebuilds, event, dialogue, item or map-transition code, save format, the scenario runner), and
then only the affected segments (`run.py NN`). Side quests and promotion quests follow the same method as standalone
scenarios (`tests/scenarios/mm9/side_quests/`, with their own `run.py`).

    python3 tests/playthrough/mm9/run.py              # all segments, stops at the first failure
    python3 tests/playthrough/mm9/run.py 51 52        # some segments (their starting checkpoints must exist)
    python3 tests/playthrough/mm9/run.py --reload     # also save and load back after every settling step

Outputs (git-ignored): `output/playthrough/<world>/checkpoints/NN_<name>.oysav`, `logs/NN_<name>.log`, `report.md`;
the reload mode writes under `output/playthrough/<world>/reload/`.

## 2. Rules of the run

These are the user's rules for the MM9 run; keep them unless a new playthrough is told otherwise.

- **Immortal party** (`setup_shortcut: {kind: immortal}` after every load; settings.ini is not written) and **enemies
  near the party die** (`walk_to`'s `clear_hostiles`, the `clear_hostiles` step).
- **Outdoors and in cities the party may be placed** (`set_pose`, `travel`) beside each person, game or exit.
  **Exits are still entered** by walking into them and confirming their prompt.
- **Dungeons are walked** (`walk_to`, ladders with `climb`): no `set_pose` inside a dungeon. A jump a player must
  make is a `movement_segment` hop with `jump: true`, logged (`play_lua: {source: 'log("JUMP ...")'}`).
- **Talk by the line a player reads** (`select_topic: {match_label: "..."}`), never by row index.
- **Puzzles and games are played** by `play_lua` scripts that decide only from what a player sees: status lines,
  boards, which goose is up, the cursor, door states. `mapvar` is for checks and for what is visible on screen.
- **Items on the ground are picked up** (`pick_up`), chests looted with Take All (`play_lua` `take_chest()`).
- **Every workaround is logged**: `log("ISSUE ...")` for a game problem the run steps around, `log("BLOCKER ...")`
  for one the run cannot pass without a cheat (and then the cheat right after it). The report shows them; a clean run
  has none.
- **A fixed bug never stays worked around**: when a BLOCKER or ISSUE is fixed, the segment goes back to the natural
  path (the crouch slot in segment 55 was a logged `set_pose` until the converter raised its ceiling).

## 3. The runner steps it uses

All are documented in `tests/scenarios/README.md` (loader: `game/scenario/ScenarioYamlLoader.cpp`, runner:
`ScenarioRunner.cpp`, driver: `ScenarioRuntimeDriver.cpp`).

| Step | What it does |
| --- | --- |
| `walk_to: {x, y, z \| to, via, radius, z_tolerance, timeout_seconds, clear_hostiles, expect_map, plan, node_limit, close_dialogs, expect: arrived\|dialog}` | Walks with the Forward key along a route from the monsters' indoor path map (`plan: false`: straight at each via point). Steers at a point about 96 ahead on the route. When stuck: aim further (400), jump, step left, step right, click what is straight ahead (a door, a lever, rubble; never a person), plan again; fails after 12 tries at one spot, naming it. Prints a `WALK` trail. A dialogue an event opens on the way ends the walk (`expect: dialog` wants that: an exit's prompt). |
| `climb: {ladder, down, timeout_seconds}` | Walks to a scene ladder's foot (down: its top exit; needs `grab_at_top`), faces it and climbs with the movement keys through the game's ladder rules; fails unless the party takes hold within 3 s and lets go at the other end. |
| `pick_up: {item_id, reach}` | Takes an item lying in the map: fails when the party's eye is further than `reach` (default 400) — walk closer —, turns the camera at it, presses the use key through the game's pick, checks the item reached the party. |
| `play_lua: {source, max_seconds}` | A player's reasoning in Lua: `click(event)` (closes a talk that popped up first), `wait(s)`, `status()` (status lines since the last call), `qbit(id)`, `has_item(id)`, `item_count(id)`, `pack_items()`, `held()` (cursor item), `party()` (selected member, Mights, conditions), `mapvar(name)`, `door_state(id)`, `take_chest()`, `close()`, `discard(id)` (drop a spare item to make room), `clear_hostiles(radius)`, `log(text)`; helpers `open_door(event, door)` (waits for a self-closing or monster-opened door to stop, clicks it if shut, waits until open) and `loot_chest(event)` (clicks again after a trap goes off). |
| `party_defeat: {knock_out, wait_seconds, expect_map, expect_game_over}` | The game's own defeat and respawn (its movie skipped); `knock_out: true` downs the party at once; a world's game over (MM9's rule) needs `expect_game_over: true`. |
| `reload: {expect_blocked}` | Saves and loads straight back, then dismisses what greets the party on arrival; skipped (logged) while a player could not save (a dialogue, a chest, a map that forbids saving such as an arena). `expect_blocked: "text"` fails unless it is refused for that reason. `run.py --reload` inserts it. |
| `clear_hostiles: {radius, min}` | Kills the party's enemies near it through the normal damage path. |
| `setup_shortcut: {kind: immortal, value}` | The Immortal cheat for this run only. |
| `save_game: {name, path}` / `load_game: {path}` | Checkpoints that outlive the run. |
| `select_topic: {match_label}` | Picks a dialogue line by its text (exact, else the one line containing it); a miss lists the lines offered. |
| `travel: {map, days}` | A boat trip or overland journey (outdoor shortcut), its days passed as the game's travel passes them (the party rests on the road: `applyTravelDaysSideEffects`). Keeps the cursor item, as a real map move does. |
| `new_game_flow: {...}` | Starts a new game (party creation as the game does it). |

Plus the existing steps: `set_pose`, `interact_actor`, `press_interact`, `press_action: {action: cancel_dialog}`,
`advance_runtime: {seconds, present_dialogs, follow_map_move}`, `movement_segment`, `assert`, `console`, `lua_event`.

## 4. How to build a new playthrough (or extend one)

### 4.1 Split the story into segments

One segment per coherent leg (a town's quest giver, a dungeon, a trip and its talk), 2-120 s of run time. Leave gaps
in the numbering (01, 03, 05 …; or blocks per chapter: 01-19, 20-34, 35-50, 51-61 in MM9) so later inserts need no
renumbering. A segment whose start state you need before the earlier chapters exist may load a user's save
(`00_after_council.oysav` was the user's save until segments 01-50 existed).

### 4.2 Research first: a prep sheet per block

Before writing YAML, research each block into `tests/playthrough/<world>/prep/NN_MM_<name>.md`. Per step:

- the map file and how the party gets there (exit trigger box and prompt, travel, start point);
- each person: actor index, name, position, the exact dialogue lines in order, what each line and the talk's close
  (its exit hook) set;
- each prop to click: event id, position, the status text a player sees, the handler's logic (`file:line`);
- triggers and plates (polled boxes or face triggers), teleporters (walk-in boxes: put the last via point on the line
  from the arrival through the box, target the arrival), doors (auto-close times), ladders, movers;
- the keys/qbits and items each step sets, for asserts;
- dungeon walk routes with via points where the planner fails (§6), and every traversal risk with coordinates;
- the guide's errors (a walkthrough or guide is never fully reliable: the map scripts are the truth for the build;
  online walkthroughs show what the original expected). Compass words follow the map the player sees, not raw
  coordinates: MM9's outdoor maps (`flip_u` in `worlds/mm9/ui/maps/catalog.yml`) show +y at the bottom and +x at the
  left, so "north" there is -y; reading +y as north turned every outdoor direction in the first prep notes around;
- suspected bugs with `file:line`.

Research blocks are independent, so they run in parallel (§7); validate claims with discovery scenarios
(`load_map` + `console: {line: "qbit set N"}` for prerequisites, or a nearby checkpoint).

### 4.3 Write and run each segment

Header comment (what leg, the guide section, how it is played), then: `load_game`, `setup_shortcut: immortal`, an
`assert` of the starting state, the leg, the asserts of what it produced, `save_game` with a `path`. Keep every
workaround and every non-obvious choice explained in a comment next to it.

Each segment must pass `run.py NN` **twice** (determinism) and `run.py --reload NN` **once**.

### 4.4 The save-and-load run

`--reload` runs copies of the segments with a `reload` after every assert, walk, scripted play, travel and defeat
(not where a dialogue goes on), on their own checkpoints. A failure only there is a save/load bug until shown
otherwise. Expect two legitimate kinds of difference and handle them as a player would, not by bending asserts:

- **Greetings come again** after a load (an NPC's found-player talk): the reload dismisses what greets on arrival,
  and `click()` closes a talk that pops up later.
- **Random draws differ** after a load (prize draws, codes): the scripted player must cope with any draw (loop until
  won, drop spare prizes so packs do not fill).

## 5. Triage: what a failure is

Work out which of four things failed before changing anything:

1. **A game bug** (the player would hit it too): fix it at its source. MM9 map scripts and scenes are
   converter-generated: change the converter, build into a scratch folder, diff so the installed file changes only by
   your fix, install into `assets_dev` and the map's review root, run `check_mm9_map_lua.py` (AGENTS.md "MM9 map
   Lua"). Engine bugs: fix in shared code with a regression scenario or unit test. Add a regression scenario under
   `tests/scenarios/<world>/` that does not depend on playthrough checkpoints (they are git-ignored).
2. **A runner gap** (the harness cannot do what a player does: a step, a frame's work the game does and the headless
   frame did not): fix the runner, mirroring the game's own code path, and document it in `tests/scenarios/README.md`.
3. **A test flake** (timing, a route that only works with one draw): make the segment play as a player would (wait
   for a door, aim at the thing, walk closer), never loosen an assert.
4. **Someone else's change** (other sessions rebuild maps and edit the engine in the same tree): check timestamps
   (`ls -la --time-style=+%H:%M`), `git diff` of the file, `check_mm9_map_lua.py`; ask the session (`ListAgents`,
   `SendMessage`) before restoring anything; adapt the segment if their change is intended.

### Debugging techniques that worked

- **Bisect a segment**: generate a probe that runs the segment's steps up to the failure with a `play_lua` print
  after every step (`has_item`, `held()`, `qbit`, `mapvar`, `door_state`), and compare the run with and without a
  reload. This found the cursor item lost on map moves (the item vanished after a `travel`), the swim memory lost on
  load, and the full packs.
- **Read the walk's stuck lines**: they name the waypoint, the nearest actor, whether world input is blocked and
  whether a dialogue is pending; "nothing to click ahead" next to a door means a seam or a closed leaf.
- **Compare game paths**: when headless and the game differ, find what the game's frame does that the headless frame
  does not (presenting granted items, presenting queued dialogues, setting up the view on a respawn) and do it in
  the driver.
- **Use the game's own functions** for everything a player does (Take All, defeat, map moves, picks), never a
  shortcut that skips their side effects.

## 6. Pitfalls met in the MM9 run (check these first)

- **Talk exit hooks**: a talk whose exit opens the next talk or a travel prompt must show it (fixed in the engine:
  `endMm9RudeTalk`); a talk a script opens outside a click must name its speaker (`MM9.openRude(id, actor)`) or its
  exit never runs (audit: `devdocs/mm9_rework/MM9_SPEAKERLESS_TALKS.md`).
- **The cursor**: event-given items land on the cursor; a map move used to lose it (fixed:
  `loadCurrentSessionMapKeepingHeldItem`); an item taken by a script comes from the cursor when no pack has it
  (fixed: `takenHeldItemId`). Full packs push a new item's predecessor off the cursor onto the ground.
- **Saved state**: the indoor party's swim memory was not saved (fixed, save version 166); a rotating floor trap
  mid-swing loads the party elsewhere (open).
- **Double doors**: their leaves can get out of step; a click toggles each leaf (open engine bug); wait until both
  are shut, then click.
- **Doors that close by themselves** (5-15 s): click right before walking through, never from inside a leaf's arc.
- **Teleporter crystals / walk-in boxes**: `walk_to` goes on from the route point nearest to where a same-map
  teleport put the party (2026-11-09; before that it kept steering at its old goal): put via points on the pad (with a
  small `radius`, so it does not turn off before the pad) and the arrival as the target.
- **Friendly actors in the way** (wandering guards, townsfolk): `walk_to` goes round them, waits or backs off
  (2026-11-09); no hand-tuned waits.
- **Defeats** follow the world's rule: MM9 wakes a defeated party in Arslegard only with keys 97 and 29 and either
  without 98 or with 100 (world.yml `partyDeath` `when`); otherwise it is a game over (`expect_game_over: true`).
- **Arrival is on x/y** unless `z_tolerance` is given; give it on stacked levels and after drops, or follow with a
  short `advance_runtime`.
- **Planner traps**: the monsters' path map can route off a ledge into a pit, across a gap the party cannot jump, or
  not at all on outdoor-sized BLV regions; spell those legs out with `via` points and `plan: false`.
- **Ladders**: `walk_to` does not take them; the `climb` step does (by the scene ladder's id). Most ladders cannot be
  taken from their tops (no `grab_at_top`): the way down is a drop through the hole beside them.
- **Unkillable or wandering actors in corridors** (Njam, idle flyers, NPCs on narrow paths): wait them out as a
  player would, or walk round them.
- **Exits ask**: most region exits open an "OK / Close" prompt; select "OK", then `advance_runtime` with
  `follow_map_move: true`.
- **The engine's state as the party moves through dialogues**: `advance_runtime` without `present_dialogs` leaves
  queued talks pending; a pending talk blocks clicks.
- **Days awake**: every dawn passed without a rest weakens the party, cuts its HP and after three days may madden or
  kill a member (MM9 has no food); the Immortal cheat keeps the HP, not the conditions. Until 2026-11-09 `travel`
  passed its days awake, and the main run's party came out of Chapter II Dead at 1 HP. Dead members still talk and
  walk but cannot attack or be selected: check `conditions(i)` before combat, and heal at a temple.
- **The cursor**: an item on the cursor stops attacks; `stow()` puts it into the packs, as a player does.
- **World items** (MM9's placed pickups since 2026-11-08) replaced click events; check the scene's `world_items`
  when a click gives nothing.

## 7. Running it with agents

The MM9 run was built by one coordinating session and several subagents:

- **Research in parallel, writing in sequence.** Each block's research agent works from `load_map` and console qbits
  and writes its prep sheet; writing has to wait for the previous block's last checkpoint, so the coordinator
  messages each agent to start writing when it exists.
- **Brief every agent fully**: the rules (§2), the steps (§3), the files to read (README, the latest segments, the
  prep format), its segment numbers and checkpoint names, what to verify (twice normal, once reload), what it may
  change (its own segments and prep sheet; converters per the AGENTS.md rule; never C++ unless told), and how to
  report (pass/fail and times, last checkpoint and party state, bugs, decisions for the user).
- **Memory**: at most one game or analysis process per agent, custom analysis under
  `prlimit --as=12000000000`, `free -g` before heavy work. A 12-worker analysis pool once took 85 GB and the OOM
  killer took the user's desktop apps and the session.
- **Shared tree**: other sessions edit the engine and rebuild maps while a playthrough runs. A build that fails in
  someone else's file is theirs: retry until it compiles; a binary built while a header changed mid-build can crash
  (rebuild). Tell the owner about a breakage with a precise repro instead of editing their file.
- **Decisions belong to the user**: an engine mechanic versus a converter deviation (the crouch slot), MM9-faithful
  versus forgiving (the Crona Kiga, the drawbridge chains), what MM9 did when unsure (check its scripts in
  `mm9/extracted/SCRIPTS`, its manual `mm9/game/MANUAL.PDF`, walkthroughs).

## 8. Another world or quest

The steps are world-neutral. For MM6-MM8:

- dialogues are houses and NPC topics: `select_topic: {match_label}` works on them too;
- outdoor maps are ODMs: `walk_to` goes straight (no path map outdoors), which is fine where placing is allowed;
- map Lua there is exported from EVT (regenerate with `tools/regenerate_lua_events.sh`, never edit it by hand);
- the save-and-load run applies unchanged.

For a single quest or a regression of one dungeon, one segment that loads a fitting save (or starts with
`new_game_flow` plus console qbits) and walks the dungeon is often enough; keep it under `tests/scenarios/` if it
does not need a checkpoint chain.

## 9. What the MM9 run found (2026-11-08)

As a measure of what this catches: talk exit hooks dropping the next dialogue (Skraelos, the Questioner), scripted
talks without a speaker (the Confession's Jarls, Yrsa's errand, Frosgard's bank hatch), a cursor item lost on every
map move, a quest item taken from the packs but not the cursor, the swim memory lost on load, the Dark Passageway's
crouch-only slot (raised), the Tomb's sequence-break gates and blocking flyers, Frosgard's Tamur hidden after a
reload (a soft-lock), Tryygva's wrong clan key, the double doors' leaves, the rotating trap after a load, and several
runner gaps. The README (`tests/playthrough/mm9/README.md`) and the prep sheets hold the details.
