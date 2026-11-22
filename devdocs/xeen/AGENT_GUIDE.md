# Xeen: guide for an agent starting work

The single entry point for an agent that arrives fresh to work on the World of Xeen. It says what Xeen is, where
everything lives, how to do the common jobs, and the rules. It links out for depth. Current as of 2026-11-22
(after the v3.0 release). Read AGENTS.md first; its rules apply here too.

## 1. What Xeen is and where it stands

- Xeen is the fifth world (id `xeen`). It tells the story of Might and Magic IV and V (Clouds and Darkside of Xeen,
  and their joint ending) on **new** MM6–MM8-style maps, with MM6–MM8 rules, items and power curve.
- It shipped in v3.0 as **"Xeen (alpha)"**: first card on the new-game screen, caption "Begin in Vertigo". It also
  plays under the MAW ruleset ([devdocs/maw/XEEN_SUPPORT.md](../maw/XEEN_SUPPORT.md)).
- **82 maps are built and installed**, every door between them is open:
  - 13 outdoor maps (ODM): X1–X7 on Cloudside, D1–D6 on Darkside;
  - 69 indoor maps (BLV): the sky maps X8, X9, D7; the elemental planes P1–P4; the finale P5; the dungeons XD-01–XD-27
    (Cloudside), DD-01–DD-26 (Darkside, DD-10 and DD-11 split A/B/C) and FD-01–FD-04 (Act VI, both faces).
- The main story (M1–M42 in six acts), the side quests and the promotions are playable from a new game to the ending.
  All three test sets pass, normal and `--reload` (§5.6).
- Design: [WORLD_DESIGN.md](WORLD_DESIGN.md), [QUESTS.md](QUESTS.md), [MAPS.md](MAPS.md),
  [MONSTERS_AND_ITEMS.md](MONSTERS_AND_ITEMS.md). The plan and the "map is done" list: [ROADMAP.md](ROADMAP.md) §5.1.
  Latest state: the top of [STATUS.md](STATUS.md) and the Log of [ORCHESTRATOR_SESSION4.md](ORCHESTRATOR_SESSION4.md).

### What is still alpha or open

Small polish left at the v3.0 release (ORCHESTRATOR_SESSION4.md, "A3 41st done", and the late Log):

- Villagers still to place: XD-17 Shangri-La, D7 Olympus; D2's sprite townsfolk type; DD-25's dwarf by a door.
- Q-C1: the Autumn and Winter Druids keep their own topic labels (no journal line).
- XD-15 (the Sphinx): a stair waypoint in its generated tests. FD-02 (the Southern Sphinx): its library wall still
  draws pale.
- `check_open_sky.py` has no rule for parapet height yet (D-101 sets 160–224).
- DD-25: a `sgearth` feature-border warning. `texture_classes.py`: a full rerun drifts from the committed classes.
- The promotion chain was last run normal only on the final maps, not `--reload`.
- Translations: `assets_dev/languages/zh-cn/text/xeen.po` is nearly complete (the translators', 2026-11-22); the other
  six languages have no Xeen text yet.
- Optional choices nobody has ruled on: Yog dying with the Sardaj on D1's war route; DD-19's return point on D3.

Before you start on any of these, read the owning lane's file (§6) for its newest State and Next.

## 2. Where everything lives

| What | Where |
| --- | --- |
| The world package (committed since v3.0) | `assets_dev/worlds/xeen/`: `world.yml`, `maps/`, `events/`, `data_tables/`, `models/`, `textures_x2/`, `audio/`, `music/` … |
| Authoring sources of the tables | `assets_dev/worlds/xeen/source/` (never mounted, never packaged): `maps.yml`, `map_rows.yml`, `monsters.yml`, `items.yml`, `towns/`, `npcs/`, `quests/`, `entrances.yml`, `textures.yml` |
| Generated tables | `assets_dev/worlds/xeen/data_tables/*`, `relations.yml`, `modifiers.yml`, `events/common/xeen_quests.lua`: written by `tools/xeen/build_world.py` (§5.4) |
| Hand-written world Lua | `assets_dev/worlds/xeen/events/common/xeen_common.lua` |
| Generated map Lua | `assets_dev/worlds/xeen/events/maps/<stem>.lua`: written by `oymap build`; change the map project, never this file |
| Generated unkillable-NPC list | `events/common/xeen_key_npcs.lua`: written by `tools/xeen/key_npcs.py --write` |
| MAW in Xeen | `assets_dev/engine/rulesets/maw/worlds/xeen/` (`balance.yml` …); tools `tools/maw/xeen_balance.py`, `tools/maw/xeen_pack_reserve.py`; lane [MX](lanes/MX.md) |
| Map projects (Map Studio briefs) | `devdocs/xeen/briefs/<key>/L1`–`L4`; L4 is the buildable project (`project.yml`, `plan.yml`, `rooms.yml`/`objects.yml`/`wiring.yml` indoors, `sketch.yml` outdoors, `playtest*.yml`, `NOTES.md`, `ids.lock.yml`) |
| Map generators | `level_generation/projects/xeen/<key>/` (each map's `gen.py` writes its L4). Per-map regenerate commands: [level_generation/projects/xeen/README.md](../../level_generation/projects/xeen/README.md). The old `output/studio_cal/<key>/tools/` folders are symlinks to them |
| World tools and checks | `tools/xeen/` (read each script's docstring; the checks are listed in §5.1) |
| Lighting bake profiles | indoor `tools/lighting/baked_indoors/profiles/xeen_<key>.yml`; outdoor: the `profile` key of the installed `maps/<stem>.bake.json` is the profile it was baked with |
| 3D model sources | `assets_source/worlds/xeen/` (the `assets_source` submodule, **not** in this repository's history); runtime copies in `assets_dev/worlds/xeen/models/`. Creature projects: `level_generation/creatures/xeen_*_claude/` |
| Textures | generated with Codex through `level_generation/textures_xeen/xtex.py` ([README](../../level_generation/textures_xeen/README.md)); every new one is registered in `source/textures.yml` |
| Sounds | `level_generation/sounds/xeen_20261120/` (`install.py`, `install.yml`); ids 62000–63999; [AUDIO.md](AUDIO.md) |
| Music | eight own themes, tracks 92001–92008 in `assets_dev/worlds/xeen/music/`, plus MM6–MM8 tracks by number; [MUSIC.md](MUSIC.md) |
| Tests | main chain `tests/playthrough/xeen/`, promotions `tests/playthrough/xeen/promotions/`, side quests `tests/scenarios/xeen/side_quests/`, focused scenarios `tests/scenarios/xeen/` |
| Player guide website | `tools/xeen_site/` ([README](../../tools/xeen_site/README.md)), lane [G](lanes/G.md) |
| Decisions | [DECISIONS.md](DECISIONS.md) (D-n by deciders, U-n by the user) and `reviews/D<n>_DECISION.md` |
| User feedback | `reviews/USER_FEEDBACK_20261121.md` (families F1–F23 with their Results) |

Formats: [TOWNS_FORMAT.md](formats/TOWNS_FORMAT.md), [QUESTS_FORMAT.md](formats/QUESTS_FORMAT.md),
[DRESSING.md](formats/DRESSING.md), [DOORS.md](formats/DOORS.md), [LIGHTS.md](formats/LIGHTS.md),
[TEXTURE_FIT.md](formats/TEXTURE_FIT.md). Map Studio: `openyamm-studio/README.md`,
[REBUILD_PROCEDURE.md](../map_studio/REBUILD_PROCEDURE.md),
[OUTDOOR_REBUILD_PROCEDURE.md](../map_studio/OUTDOOR_REBUILD_PROCEDURE.md), [TOWN_FEEL.md](../map_studio/TOWN_FEEL.md).

### Id ranges

From `world.yml` `idRanges` (the build refuses an id outside them or used twice):

| Domain | Range | Domain | Range |
| --- | --- | --- | --- |
| qbits | 110000–119999 | houses | 4001–4999 |
| items | 12000–12999 | NPCs | 4001–5999 |
| monsters | 11000–11999 | NPC topics | 40000–49999 |
| objects | 22000–22999 | autonotes | 4001–4999 |
| vendors | 31000–31999 | awards | 401–499 |
| decorations | 4001–4999 | transport, roster | 401–499 each |
| sounds | 62000–63999 | maps (map_stats) | 9101–9199 |
| placed monster names | 401–499 | entrance lines (trans) | 5001–5999 |

Inside those, qbits and topics go by blocks per quest (QUESTS_FORMAT.md §3), houses and NPCs by blocks per map
(TOWNS_FORMAT.md §2). An id once used is never renumbered or reused.

## 3. Binaries

- Build the game and the studio yourself only when you are working alone. In a multi-agent run only lane A1 builds
  (§6). Never build or run Vulkan.
- Game: `tools/heavy.sh 24 cmake --build build --target openyamm -j16` (never -j25 now).
  Studio: `tools/heavy.sh 24 openyamm-studio/build.sh` (writes `openyamm-studio/build/oymap`).
- The program built into separate trees, `build-xeen/game/openyamm` and `openyamm-studio/build-xeen/oymap`, so other
  sessions' builds of `build/` never changed its binaries mid-run. The Xeen runners default to `build-xeen`. If you
  use `build/`, pass `--game build/game/openyamm` to the test runners, `--binary` to `tools/run_game.sh`, or set
  `OPENYAMM_GAME_BINARY`.
- After pulling other people's header changes, a sudden crash can be a stale build: touch the changed header and
  rebuild.

## 4. Rules

### Memory, builds and runs

- Several sessions share one PC. Run every heavy job through `tools/heavy.sh <cap GB> <command...>`. Caps: C++ build
  24 (`-j16`), Blender bake 16, oymap build/install 8, a game run, scenario or playthrough runner 6, a Python tool 4.
  At most three agents with heavy jobs at once.
- One lighting bake at a time in the whole program: `tools/heavy.sh 16 flock output/xeen_locks/bake.lock <bake>`.
- One agent per map: hold `flock output/xeen_locks/<stem>.lock` (e.g. `xeen_x1.lock`) around the whole edit, build,
  install, bake and test of that map. Keep it short.
- Game runs: `--isolated <unique name>` (the wrappers start the game minimised), prefixed `SDL_AUDIODRIVER=dummy`, at
  most two of your own at once. Wait on the exact PID (`kill -0 <pid>`); never `pgrep -f` (it matches your own
  command line and never ends). Headless scenarios are preferred where they are enough.
- Scratch goes under `output/<your folder>/`, never `/tmp` (RAM-backed). The disk is nearly full: use hard-link copies
  (`cp -al`), delete your own scratch when done, `ls` first and literal paths only.

### Git and shared files

- Never `git add`, `commit`, `stash`, `reset` or `restore --staged` unless the user asks. The user commits.
- Other sessions edit the same checkout. Before editing a tracked file, read `git diff <file>` and keep their changes;
  make targeted edits only, never whole-file restores. Never delete other people's files.
- Generated files are never edited by hand: `data_tables/*`, `xeen_quests.lua`, `xeen_key_npcs.lua`,
  `events/maps/<stem>.lua`, and any file headed as generated. Change the source or generator and regenerate.
- An L4 is written by its generator: edit `gen.py`, not the YAML. Before regenerating, diff the L4 against its
  `.oymap/last` copy: a hand edit made since the last generator run would be lost.

### Content rules from the user

- **No riddles the game does not answer.** A password, riddle or syllable puzzle stays only when the game gives the
  answer plainly before it is needed (a scroll, note, sign or person on the way). Otherwise it becomes a key, a
  mechanism, a fight or a found item. Keys must be findable (a chest, a visible item, a named boss), never on an
  unnamed monster. Yes/No offers are fine. `oymap audit` lists where each question's answer is met.
- **Town feel first.** An outdoor map is judged by its town: asymmetric layout, paths that follow the houses, one or
  two house styles, services placed sensibly (armour beside weapons, the tavern near the edge), small hills, monsters
  guarding something, enough props, a pedestal, wandering villagers (D-96). Measure against the shipped towns:
  `python3 openyamm-studio/calibration/town_feel.py <map.odm> --world xeen` ([TOWN_FEEL.md](../map_studio/TOWN_FEEL.md)).
- **MM6–MM8 conventions, simple but fun.** Rooms with a job at MM sizes; one texture family per area from a shipped
  map whose purpose fits; props against walls, never blocking a door or path ([lanes/README.md](lanes/README.md),
  "Rules", for dressing, lights, double doors and texture fit).
- **No stand-ins** in anything you call done. If a row, model, house or quest is missing, name its owner and mark the
  item blocked.
- Text: short lines in the voice of WORLD_DESIGN §1, English source. Short original MM4/MM5 lines may be quoted.
- Spending: Meshy and ElevenLabs only within what the user approved for the work (lane files S and AU record it); ask
  the user before any new kind of spending.

### Decisions

- Before you start a map or a town, read every DECISIONS.md row that names it, and its town file
  (`source/towns/<map>.yml`).
- **Design questions do not go to the user.** Give each one to a new, read-only "decider" agent with a self-contained
  brief: the question, the options, your evidence (files, measurements, captures), the user's rulings that bear on it
  (README's decisions, DECISIONS.md, `devdocs/map_studio/HANDOFF_LEAD.md` §2 and §5), and what each option costs.
  It answers DECISION / WHY / WHO ACTS / REVERSIBLE plus a one-line SUMMARY ROW. Meanwhile carry on, or take the
  option that is cheaper to undo. Tell the user which rulings were least certain.
- Record each answer as the next row of the DECISIONS.md table (the next number is **D-102**: `| D-102 | <date> |
  <question> | <decision> | <who acts> |`), with the decider's full answer in `reviews/D102_DECISION.md`. A user's own
  ruling is a U-n row (next U-12).
- Risky or irreversible steps, commits and new spending still need the user.

## 5. Workflows

### 5.1 Change a map

1. Take the map's lock. Read its `NOTES.md`, its DECISIONS rows and its lane file's Log.
2. Edit the generator `level_generation/projects/xeen/<key>/gen.py` (or a shared kit in `tools/xeen/`, such as
   `kit_pieces.py`, `house_doors.py`, `cave_shape.py`, when the change belongs to every map of its kind).
3. Regenerate the L4 and build it with the map's commands in
   [level_generation/projects/xeen/README.md](../../level_generation/projects/xeen/README.md). Underneath they run
   `oymap fmt`, `oymap validate --assets assets_dev`, `oymap record --author agent:<you> --label <what>` and
   `tools/heavy.sh 8 oymap build <L4> --assets assets_dev --out <scratch build>`.
4. Install into a private hard-link root first and check there: `cp -al assets_dev output/<you>/root`, then
   `oymap install <L4> --build <build> --root output/<you>/root`.
5. Run the checks on the built map and fix every error:
   - `oymap audit <root>/worlds/xeen/maps/<stem>.<blv|odm> --world xeen --assets <root> --reach --solve`
     (dressing, lights, doors, texture fit, chests, entrances: errors are fixed; a kept warning gets one line under
     "exceptions" in NOTES.md);
   - indoor: `tools/xeen/check_exits.py <key>`, `check_drops.py <map.blv>`, `check_open_sky.py <key>`,
     `check_identity.py <key>`;
   - outdoor: `door_check.py <stem>`, `wall_check.py <stem>` (walled places), `empty_zones.py --check`,
     `check_props_support.py`, `town_feel.py` for a town, the map's D-85/D-87 arrival-distance check if it has one;
   - `python3 tools/xeen/towns.py --strict` and `house_signs.py` when houses changed.
6. Run the map's playtests (`L4/playtest*.yml`) from the root: dungeons 4 of 4, outdoor maps 2 of 2, and
   `playtest_hostility.yml`:
   `SDL_AUDIODRIVER=dummy tools/heavy.sh 6 build/game/openyamm --asset-root <root> --world xeen --map <stem>.blv
   --user-data output/<you>/ud --headless-run-scenario <L4>/playtest.yml --scenario-no-color`.
7. Look at your own screenshots (§5.7) of what you changed and fix what looks wrong.
8. Install into `assets_dev` (`oymap install <L4> --build <build> --root assets_dev`: Xeen owns its rows, so the
   studio writes only the map's files) and bake **straight after**, under the bake lock (install before bake, never
   the other way):
   - indoor: `blender --background --factory-startup --python-exit-code 1 --python tools/lighting/bake_indoor.py --
     --profile tools/lighting/baked_indoors/profiles/xeen_<key>.yml --output <scratch> --assets assets_dev
     --game-binary <game> --sources assets_source`, then copy `<stem>.lighting` and `<stem>.bake.json` beside the map
     ([INDOOR_BAKED_LIGHTING.md](../INDOOR_BAKED_LIGHTING.md));
   - outdoor: `tools/lighting/bake_outdoor.py` the same way ([its README](../../tools/lighting/baked_outdoors/README.md)),
     then the terrain weights (`python3 tools/terrain_materials.py weights --world xeen --map <stem>.odm`,
     [README](../../level_generation/terrain/materials/README.md));
   - the lanes' scripts do these steps with the locks and `tools/heavy.sh`: outdoor
     `level_generation/projects/xeen/common/install/a6_install_baked.sh` (or A5's `a5_install_baked.sh`)
     `<stem> <L4> <build> level_generation/projects/xeen/<key>/bake_profile.json`; indoor
     `INSTALL=1 level_generation/projects/xeen/common/install/a8_rebuild.sh <key>`, then
     `flock output/xeen_locks/bake.lock level_generation/projects/xeen/common/bake/a8_bake.sh <key> assets_dev`
     ([README, "Install and bake"](../../level_generation/projects/xeen/README.md#install-and-bake)).
9. After any install: `python3 tools/xeen/key_npcs.py --write`, `python3 tools/xeen/check_actor_heights.py`,
   `python3 tools/lighting/stale_bakes.py --check` (0). Indoor maps also:
   `python3 tools/maw/xeen_pack_reserve.py <stem>` and `python3 tools/maw/xeen_balance.py --check`.
10. If monsters or chests changed: `python3 tools/xeen/balance.py` (every act within 15 % of its kill-XP budget).
11. Rerun the story segments that cross the map (§5.6). A rebuilt map resets its saved state when a checkpoint enters
    it ([SAVED_MAP_STATE_IDENTITY.md](../SAVED_MAP_STATE_IDENTITY.md)); the runner prints STALE lines for that.
12. Write NOTES.md (what changed, measurements, exceptions) and the lane file's Log.
13. When the user should judge it, give them a play copy: a hard-link root with the map installed and the command
    `./tools/run_game.sh --isolated <name> --world xeen --map <stem> --assets "$PWD/output/studio_play/<name>_root"
    --visible --seconds 0`. List it in `output/studio_play/PLAY.md`. The user judges maps by playing them.

### 5.2 Fix a fault the user reported

1. Capture the user's exact pose first (§5.7) and look at the image. Keep every reported pose in a tour YAML in your
   scratch folder.
2. Trace the fault to its source: the studio (vocabulary, build defaults, audit), a shared kit in `tools/xeen/`, the
   common Lua, the data, or the engine. The reported spot is only the example.
3. Fix it there, for **every** site of its kind in the world, and add a check that keeps it fixed (an audit rule, a
   `tools/xeen/` check, a build refusal or a test). Do not patch only the one map.
4. Rebuild every affected map as in §5.1, under its lock, one at a time.
5. Capture the user's poses again from `assets_dev` and look at each image before calling it fixed.
6. Report the cause, the fix, every site found and what happened to it, the new check, and before/after captures
   (the shape is in [briefs/FEEDBACK_FIX_RULES.md](briefs/FEEDBACK_FIX_RULES.md)).

### 5.3 Quests, NPCs, towns, villagers, journal

- **A quest**: one file `source/quests/<id>.yml` (QUESTS_FORMAT.md §4): topics, conditions, effects, journal line,
  hooks. A map wires a hook by name (`XeenQuests.hook("<quest>.<name>")`); the hook table is
  `data_tables/quest_hooks.yml`. Journal lines, autonotes and awards come from the quest files too.
- **An NPC's talk** that belongs to no quest: `source/npcs/<map>.yml`; flavour lines `source/npcs/flavour/<map>.yml`.
  At most five topics show per NPC.
- **A town, house, resident, teacher, shop, transport**: `source/towns/<map>.yml` (TOWNS_FORMAT.md). Every house has a
  door on its map and every door a house.
- **Villagers**: palettes and counts in `source/towns/villagers.yml`; spots by
  `python3 tools/xeen/villagers.py --place <MAP>` (TOWNS_FORMAT.md §6).
- **Monsters, items, map rows**: `source/monsters.yml`, `items.yml`, `treasure.yml`, `map_rows.yml`; `maps.yml` is
  the registry.
- Then regenerate the tables (§5.4) and run `python3 tools/xeen/quests.py` (0 errors) and
  `python3 tools/xeen/quest_stub.py` (the stub Lua run). A new or changed hook needs its map rebuilt (§5.1). Rerun
  the playthrough segments or side quest that use it (§5.6); update the segments your change breaks.

### 5.4 Rebuild the world tables

- `python3 tools/xeen/build_world.py --check` first. It must show nothing but your change.
- Then `python3 tools/xeen/build_world.py` (everything) or `--only <module>` (`gen_monsters`, `gen_items`, `gen_maps`,
  `gen_quests`, `gen_towns`). It takes `assets_dev/worlds/xeen/.build_world.lock` and writes nothing on any error.
- End with `--check` at 0 differ.

### 5.5 Text and translations

- New player-visible text is English, in whole sentences. Lua passes whole sentences to `evt` functions.
- Do not run `tools/l10n.py` for ordinary changes. Before a release: `python3 tools/l10n.py extract`, then
  `update` ([LOCALIZATION.md](../LOCALIZATION.md)). Xeen's domain is `xeen` (`languages/<lang>/text/xeen.po`).

### 5.6 Run the tests

The story runs are long checks, not routine tests (AGENTS.md). Run the affected segments after a change that can
break a story, and all of them before a release. Each through `tools/heavy.sh 6`, at most two at once.

| Set | Command | Size |
| --- | --- | --- |
| Main story | `python3 tests/playthrough/xeen/run.py [NN ...] [--reload] [--game <bin>]` | 52 segments, new game to the ending |
| Promotions | `python3 tests/playthrough/xeen/promotions/run.py --start` (copies the main run's checkpoints), then `[NN ...] [--reload]` | 41 segments |
| Side quests | `python3 tests/scenarios/xeen/side_quests/run.py [q-c20 ...] [--reload]` | 71 scenarios, each from a new game |
| Focused | `build/game/openyamm --headless-run-scenario tests/scenarios/xeen/<file>.yml` | hooks, travel, shops … |
| Quest stub | `python3 tools/xeen/quest_stub.py` | no game run |
| Regression set | `tools/xeen/regressions.sh [game] [unit tests]` | MM6–MM9 start, travel, save/load, release scenarios |

- `--reload` saves and loads back after every settling step. A segment fails when a member ends Dead, Eradicated,
  Petrified, Paralyzed or Unconscious (D-82, the PARTY line).
- Checkpoints (`output/playthrough/xeen/checkpoints/`) are git-ignored. Run a segment alone only when the checkpoint
  before it exists and is newer than the maps it enters.
- The release scenarios (`tests/scenarios/release/scenarios.txt`) are the only ones in CI. Never add Xeen story runs
  there.
- How segments are written and debugged: [tests/playthrough/PLAYBOOK.md](../../tests/playthrough/PLAYBOOK.md) and
  each set's README.

### 5.7 Take a screenshot at a pose

```sh
SDL_AUDIODRIVER=dummy tools/heavy.sh 6 ./tools/run_game.sh --isolated xd05_gate --world xeen --map xeen_xd05.blv \
  --position X Y Z --yaw-radians YAW --pitch-degrees PITCH --warmup 5 --seconds 12 \
  --set debug.screenshot_path=$PWD/output/<you>/xd05_gate.png --set debug.screenshot_delay_seconds=4
```

For many poses in one boot use a tour (`--set debug.screenshot_tour_path=/abs/tour.yml`; AGENTS.md "Native Game
Visual Checks", [tools/RUN_GAME.md](../../tools/RUN_GAME.md)). Use absolute output paths. To start from a save, pass
`--save <file>`. Then open the image and look at it.

## 6. How a multi-agent run is organised

Most of Xeen was built by one orchestrator session and many lane agents working in parallel. Run it the same way for
anything larger than one map.

- **Orchestrator.** Plans, starts lane agents in the background, relays requests between them, sends design
  questions to deciders and review rows to a Reviewer agent, keeps STATUS.md and DECISIONS.md, and owns `world.yml`
  and `source/maps.yml` (world.yml edits under `flock output/studio_cal/a5/locks/terrain.lock`). It never commits.
  How it runs: [HANDOFF_ORCHESTRATOR4.md](HANDOFF_ORCHESTRATOR4.md) §2 and §6, then
  [HANDOFF_ORCHESTRATOR.md](HANDOFF_ORCHESTRATOR.md) §1, §2, §5.
- **Lanes.** Each owns a set of files: A1 engine, studio and builds; A2 data and balance; A3 quests and the tests;
  A4 towns, services, travel; A5/A6 outdoor maps (A6 also art direction); A7/A8 dungeons; S 3D models; AU audio;
  G the guide website; MX MAW in Xeen; P packaging. Each keeps `lanes/<lane>.md` (Owns, Read first, State, Next,
  Log): a new session of that lane reads it first and updates it before it stops.
- **Rules every lane follows**: [lanes/README.md](lanes/README.md). Own files only; anything else goes as a request in
  the report. Reports have the shape DONE / STATE / REQUESTS / DECIDE / USER / NEXT.
- **Merge points.** Only A1 builds. Other lanes send engine or studio changes as exact specs (files, functions,
  behaviour, MM6–MM9 impact, the test). A1 batches them into a numbered merge point, builds, runs
  `tools/xeen/regressions.sh`, names any MM6–MM9 behaviour change, and releases the binaries.
- **Locks.** Per map `output/xeen_locks/<stem>.lock`; bakes `output/xeen_locks/bake.lock`; world tables
  `assets_dev/worlds/xeen/.build_world.lock` (taken by build_world.py itself).
- **Sizes.** A lane session lasts about 200–350k tokens; start a fresh one when its context grows long. A lane may run
  at most two sub-agents of its own, which may not fork further.

## 7. Before you stop

- `python3 tools/xeen/build_world.py --check` 0 differ; `python3 tools/lighting/stale_bakes.py --check` 0;
  `python3 tools/xeen/quests.py` 0 errors.
- Your map's checks and tests pass; NOTES.md and the lane file's Log say what you did.
- Report what the user should look at, which rulings were uncertain, and what is left. Leave every change unstaged.
