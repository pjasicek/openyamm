# Xeen lanes: rules every lane follows

The lanes of [ROADMAP.md](../ROADMAP.md) §3. Each lane has its own file here (`A1.md` … `A8.md`, `S.md`): its
ownership, its current phase's work, what it waits on, and its log. The lane keeps its file current; the orchestrator
(`xeen-o`, the session `openyamm-c3`) reads it to plan and to restart a lane in a fresh session.

## Every start

1. Read [ROADMAP.md](../ROADMAP.md) (all of it once; later §3, §5 for your content, §6 for your phase, §8),
   [STATUS.md](../STATUS.md), this file and your lane file.
2. Read the documents your lane file names before you change anything.
3. Before you start a map, read every entry of [DECISIONS.md](../DECISIONS.md) that names it or its towns, and the
   planned town file of that map (`source/towns/<map>.yml`) for the doors you must draw.

## Rules

- **Own files only.** Your lane file says what you own. Anything else: put a request in your report (below); the
  orchestrator relays it. Never edit another lane's files, `devdocs/xeen/STATUS.md`, `ROADMAP.md`,
  `assets_dev/worlds/xeen/world.yml` or `source/maps.yml` (the orchestrator's; A1 may add `tableContributions`
  entries to world.yml).
- **Git:** never `git add`, `commit`, `stash`, `restore --staged` or `reset`. The world folder
  `assets_dev/worlds/xeen/` is git-ignored; tracked files you change (briefs, tools, engine) stay unstaged. Before
  you edit a tracked file, look at `git diff <file>`: other work may have uncommitted changes in it; keep them and
  keep your own diff small.
- **Builds:** only A1 builds. Everyone else uses the binaries A1 names in STATUS.md ("Engine" section, merge points):
  `build-xeen/game/openyamm` and `openyamm-studio/build-xeen/oymap` once they exist, until then `build/game/openyamm`
  and `openyamm-studio/build/oymap`, read-only. Never run `cmake`, `make`, `build.sh` or any build.
- **No Vulkan builds or runs.**
- **Game runs:**
  - `--isolated <unique name>`, started minimised (the wrappers do it);
  - at most two game processes per lane at once;
  - wait on the exact PID (`kill -0`), never `pgrep -f`;
  - use absolute paths for screenshot output;
  - headless scenarios are preferred where they suffice.

  See AGENTS.md, "Native Game Visual Checks".
- **Resources:**
  - At most two worker processes in any analysis, with a memory cap.
  - Scratch roots: **copy** `assets_dev/worlds/xeen/data_tables/*` (copy-and-rename), never hard-link them: a
    hard-linked table takes the generator's writes into the root (A4, 2026-11-20).
  - The disk is 95 % full (about 180 GB free): use hard-link copies (`cp -al`) of asset roots, never full copies;
    delete your own scratch output when it is no longer needed (`ls` first, literal paths).
- **Generated files are never edited by hand:** `assets_dev/worlds/xeen/data_tables/*` (the generators),
  `events/maps/<stem>.lua` (the studio build), anything headed as generated.
- **No stand-ins in anything you call done.** If a row, model, house or quest is missing, ask its owner and mark the
  item blocked.
- **Codex** (images: textures, portraits, boards, HD masters): one `codex exec` worker per image, raw returns kept,
  as `level_generation/textures_xeen/README.md` and `level_generation/textures_x4/PLAYBOOK.md` describe. Texture
  budget: ROADMAP §5.2. Register every new texture in `source/textures.yml` through A6.
- **Textures through `xtex.py`:** one `gen` per texture project at a time (`--project DIR` keeps each lane's own
  project); two runs on one project overwrite each other's `state.json`.
- **Skies:** Cloudside maps use the shipped presets; Darkside ODMs `xeendark1` (the failing-sun stages `xeendark2`,
  `xeendark3` are set by A3's Lua by qbit); sky maps `xeencloud`; D7 `xeenroads`; P3 the `xeen_plane_earth` preset
  (`assets_dev/worlds/xeen/rendering/sky/sky.yml`, A6).
- **Model sources** of the world go where `tools/install_model.py` puts them, `assets_source/worlds/xeen/`; the
  submodule's local exclude keeps them out of git status.
- **Text:** short lines in the voice of WORLD_DESIGN §1; distances in game units; English source text.
- **Props and dressing** (the user, 2026-11-20):
  - No prop may block a door, a doorway, a passage or the walking line between them.
  - Barrels, sacks, crates and the like stand near the walls or in the corners. Barrels usually come in pairs; only
    storerooms hold clumps.
  - The references are the storeroom of Warlord's Fortress (MM6 `6d16.blv`) and Castle Harmondale (MM7 `7d29.blv`)
    for the normal case. The same holds outdoors: by a house's wall, never in front of its door.
  - The measured numbers (distance from the wall, pair and clump frequency, clearance round doors) are in
    [DRESSING.md](../formats/DRESSING.md). `oymap audit --world xeen` checks them (decision D-7): every error is
    fixed; a warning (set pieces such as hearths, altars, trees, vats) is fixed or kept with one line under
    "Dressing exceptions" in the map's NOTES.md. Run the audit before reporting a map done.
- **Lights and light fixtures** (the user, 2026-11-20): ceiling-hung lamps hang from a ceiling, wall lamps and sconces
  sit on a wall (never in mid-air, a doorway or on a moving leaf), floor fixtures stand on the floor, and no light sits
  inside geometry. A1's light-placement check in `oymap audit` enforces it once it ships; every dungeon lane runs it and
  fixes every error before calling a map done.
- **Double doors** (the user, 2026-11-20): a wide door that reads as double-winged (a castle gate, a dungeon entrance,
  great hall doors) is built as two leaves, each with its own wing picture (mirrored for the other side), opening
  apart; never one leaf showing a single wing, and never a single-wing picture tiled across the whole opening. Pick a
  door texture made for the opening's width; A1's door check in `oymap audit` flags tiled and half-door faults once it
  ships, and every map lane fixes them before calling a map done.
- **Texture fit** (the user, 2026-11-20): a texture with a motif meant to appear once (a window, a door, a sign, a
  picture, a set-piece panel) is placed once per face, whole, and never tiled along a wall; a band or frieze tiles only
  along its seamless axis; wall tiles are seamless where they repeat; a window or panel set into a wall has a
  background that matches the wall around it (same stone, same colour), or it gets a frame or trim between them. A1's
  tiling check in `oymap audit` flags these once it ships; every map lane fixes the errors before calling a map done.
- **Entrance names:** an entrance inside a map is named after the map it is entered from (`entrance:d1_hatch`,
  `entrance:x5_south`); a door names it with `arrival: entrance:<id>` (D-37).
- **Open sky indoors on the Darkside:** `open_sky` names a preset (`preset: xeen_darkside_day`), never the texture
  alias `xeendark1`, which falls back to a clear blue noon sky (A7, DD-13). Before regenerating a map, diff the written
  L4 against `.oymap/last`: hand edits since the last generator run would be lost.
- **Sub-agents:** at most two of your own at a time, one folder or one concern each, never two on one file; give
  each a self-contained brief and keep its results in your lane's files.
- **Never copy code** from OpenEnroth or mm_mapview2 (AGENTS.md).

## MAW reserves (2026-11-21, D-84)

- After rebuilding an **indoor** Xeen map, run `python3 tools/maw/xeen_pack_reserve.py <stem>` and then
  `python3 tools/maw/xeen_balance.py --check` (MAW's extra monsters for that dungeon, `rulesets/maw/maps/<stem>_zz_maw.scene.yml`,
  go stale with any rebuild). Outdoor maps and spawn-point dungeons have none. Lane MX owns the tool; say in your report
  when you ran it.

## Map checks added 2026-11-22 (the user's feedback, F2/F12/F14)

Before calling a map done, besides `oymap audit --world xeen`: `python3 tools/xeen/check_exits.py` (exits are the black
MM7/MM8 exit face unless on its SPECIAL list), `python3 tools/xeen/check_drops.py <map.blv>` (no floor the party can
drop to and not walk back from without spells), `python3 tools/xeen/door_check.py` (outdoor doors: no half-door alone,
centred on their steps; `--sketch` for cave mouths), and the D-85/D-87 distance checker of the map's lane. After any map install: `python3 tools/xeen/key_npcs.py --write`
(the unkillable-NPC list goes by actor index) and `python3 tools/xeen/check_actor_heights.py`.
Outdoor maps with a walled town, castle or yard (F19, D-92): `python3 tools/xeen/wall_check.py <stem>` (closed
circuits, wall ends in water/cliff/towers, flush joints; `towns.py --strict` runs it) and `tools/xeen/house_signs.py`
(every service signed by kind); a new walled place goes into `tools/xeen/town_walls.yml`.
Indoor maps with sky faces (F21, D-97): `python3 tools/xeen/check_open_sky.py <key>`: every sector under sky is listed
as deliberately open in `tools/xeen/open_sky.yml` (its kind and the brief's reason), a wall walk or battlements opens
on a side (a parapet over a courtyard, or its outer wall drawn as sky over a parapet), a skylight stays a hole in a
roof; an enclosed room or corridor has a ceiling.

## Design questions

The user does not answer design questions (2026-11-20). Put each one in your report under `DECIDE:`; the orchestrator
gives it to a new Opus decider agent with the context, records the answer in [DECISIONS.md](../DECISIONS.md) and
relays it. Until it comes back, carry on with work that does not depend on it, or take the cheaper-to-reverse option
and say so.

## When to stop and report

Stop and report when:
- your current list is done;
- you are blocked on another lane (do not wait idle);
- your context is getting long.

Update your lane file's "State" and "Log" first. Your final message is your report, in this shape:

```text
DONE: <items that met their definition of done, each with its STATUS.md line>
STATE: <one paragraph: where the lane stands>
REQUESTS: <to lane X: what, why, which file>   (one line each)
DECIDE: <design questions: what to decide, the options, your evidence, what depends on it>   (may be empty)
USER: <things the user should look at when playing; not questions>   (may be empty)
NEXT: <what you will do when resumed>
```

The orchestrator updates STATUS.md, relays requests and resumes you.

## Memory (2026-11-22, after the PC locked up)

At 10:19 on 2026-11-22 RAM (121 GB) and swap filled and the PC had to be power-cycled: MM9 conversions, two C++
builds and game runs overlapped. Every lane runs its heavy jobs through `tools/heavy.sh <cap GB> <command...>` (waits
for the cap plus a 24 GB reserve, kills the job alone over its cap; see AGENTS.md "Heavy jobs and memory"):
- A1 builds: `tools/heavy.sh 24 cmake --build build-xeen --target openyamm -j16` (never -j25 any more).
- Bakes: `tools/heavy.sh 16 flock output/xeen_locks/bake.lock <bake>` (scripts that take bake.lock themselves:
  `tools/heavy.sh 16 <script>`).
- oymap builds/installs: cap 8. Game runs, scenarios, playthrough runners: cap 6 each, still at most two at once.
- The orchestrator runs at most three agents with heavy jobs at once.
