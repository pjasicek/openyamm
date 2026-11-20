# Map Studio: handoff to the next lead session (2026-11-15, evening)

Written by the outgoing lead (session `openyamm-ce`) for a new Claude session taking over the Map Studio. Read this
first, then `S5.md` (the record of S5 and S6, newest at the end), `S5_BROWSER_EDITOR.md` (the S5 design baseline and
the user's decisions at its end), `S6_PLAN.md`, `S7_PLAN.md`, `FOR_THE_USER.md` (what waits on the user) and
`openyamm-studio/README.md`. `HANDOFF.md` holds the older history (S3, S4); its Status block is superseded by this file.

## 1. What the studio is, and where it stands

`openyamm-studio/` (untracked, its own CMake project) is the map authoring tool: a C++ core (`oymap` CLI, `oymap
serve`, a wasm build), a Node host (`host/src/`), a browser editor (`web/`, TypeScript, React 19, Base UI, three.js
0.186.1, Vite) and an MCP server for agents. Projects are YAML folders (`devdocs/map_studio/briefs/*/L4` for the
rebuilds of shipped maps, `devdocs/xeen/briefs/*/L4` for the new Xeen maps, `openyamm-studio/examples/`).

Milestones (PLAN.md section 12):
- S0-S4: done. Rebuilds within bands: New Sorpigal 93.5, Ravenshore 92.2, Shadowspire 92.1, Harmondale 90.2, Castle
  Ironfist 93.9 (fresh), Erathia 91.4 (fresh, 89.5 without `heights.nodes`); indoor rebuilds 97 %+. Xeen: XD-01..05
  and X1 Vertigo Meadows built (Vertigo through six passes; the user: "much better").
- S5 (browser editor): done in scripted runs. S5-0 spikes, S5a1-a5, S5b1, S5b2, S5c (hosted, built and tested only
  against a local origin; NOT deployed). Record in S5.md.
- S6 (MM9 extras): studio side done (overlay scene projects, destructibles, water volumes, ladders incl. leaning,
  sounds, cinematics, named mods studio side, MCP App viewer, open-air BLVs, mod methods, world view, lighting bakes
  as jobs, overlay tools). Not done: "a mod switched off in the game" (needs game change G3), terrain for new open-air
  BLVs (needs a core rasteriser). Record at the end of S5.md.
- S7 (consolidation): DONE 19:50, uncommitted (record in `S7_PLAN.md`'s record section and below in section 3):
  `openyamm_core` around the 44 shared sources in place (objects byte-equal to the reference, desktop and Android
  arm64), `core/compile/` (`openyamm_core_compile`, not in the default build), cgltf vendored from bgfx's exact copy,
  five CI sparse checkouts, the 18 outdoor callers on `oymap build-map`, docs and AGENTS.md, the MM9 rebuild scripts,
  `editor/` deleted, the engine's `assets_editor_dev` rule moved into `core/compile/EditorDocument.cpp`.

The studio is mature for agents (they built every map with it); the human editor is complete on paper and proven by
Playwright-driven runs, but the user has not used it himself yet. The outgoing lead's recommendation stands: the most
useful next step is the user trying it for 15-30 minutes on a scratch copy; his reactions become the next work.

Start it: `openyamm-studio/build/oymap studio` (prints `http://127.0.0.1:8765/#token=...`; add `--mount
output/studio_play/xeen_root` for Xeen textures). Agents: `openyamm-studio/build/oymap mcp`.

## 2. The user's standing decisions and preferences

- He judges by playing; give run commands (`output/studio_play/PLAY.md`). Lessons from his walks become studio and
  procedure fixes for every map, never one-map patches (memory `studio-feedback-generalise`).
- An outdoor map is judged by its town's feel (`TOWN_FEEL.md`, `calibration/town_feel.py`); measure against shipped
  maps, never invent. Pictures beside originals for every building (`calibration/building_shots.py`).
- No riddles the game does not answer; MM6-8 style (combat, mechanisms, loot); one texture family per area.
- S5 decisions (end of S5_BROWSER_EDITOR.md): separate Studio download, hosted page on its own origin later (deploy
  needs his explicit word: not given); bounded marked sculpt patches by default, a person may mark land hand-made;
  Base UI; hand authors and mixed agent/person work are first-class; the person-edit mark protects hand work.
- S7: approved; shared sources stay in place (CMake only); the old editor's GUI-only features may go; the S7 agent
  updates the local MM9 rebuild scripts.
- Xeen design decisions of 2026-11-14 are in `devdocs/xeen/README.md`; the design documents follow them;
  `devdocs/xeen/CHANGES_FOR_BUILT_MAPS.md` lists what the built maps must change.
- Game changes always go to him first (G1-G5 below are waiting). Commits are his (other sessions cut releases: 2.4 and
  2.5 already include the studio's game changes and records).

## 3. State at handover (no agents running)

- **S7 finished (19:50), nothing staged or committed.** Checks: indoor source packages 66/66 and outdoor 42/42 (33 build,
  9 fail identically in both routes) byte-identical old route against new; the 22 studio projects identical; native vs
  wasm 22/22; the 44 core objects byte-equal (Android: 43, `CgltfImplementation` equal without debug info); unit tests,
  release scenarios 12/12, MM9 scenarios and the MM6-8 suites' failure lists match the reference (known reference
  failures: Hesper missiles, the mercenary test when run with others, `bootcamp_museum_fight.arena.yml`); no source
  compiled twice; load medians within the reference spread. Not done: the Android APK (needs the release keystore
  password) and a desktop load-time run with the renderer. The commit needs `openyamm-studio/` too (the repointed
  callers and docs depend on it). File list: `FOR_THE_USER.md` item 17. Left in `build/`: a cached
  `OPENYAMM_BUILD_EDITOR=ON` entry, old `build/editor/` and `openyamm_indoor_source_tests` binaries;
  `.openyamm-editor.ini` (the user's old editor settings) shows untracked and can go;
  `openyamm-studio/tests/build_map_parity.sh` reports 4 of 11 from stale `land_v1` fingerprints (predates S7).
- **Not yet merged into `openyamm-studio/build/`:** the S6 leftovers (built in `build-s4`, 411 unit cases), and S7's
  edits to the studio's own CMake. Rebuild `build/` and run section 4's checks first thing.

## 4. How the lead merges and checks

Agents build only in `openyamm-studio/build-s4` / `build-wasm-s4`; the lead merges by rebuilding `build/`:
```
cp openyamm-studio/build/oymap output/studio_lead/oymap_before_mergeNN
cmake --build openyamm-studio/build -j 10 && openyamm-studio/build/oymap_tests
mkdir -p output/studio_lead/mergeNN   # copy check.sh and play.sh from merge34, s/merge34/mergeNN/
output/studio_lead/mergeNN/check.sh   # shapes, slice, rewire, every project's playtests (4 of 4 indoor, 2 of 2 outdoor)
```
Last merge: 34 (S6 studio side, 408 unit cases; all 25 playtests pass, Temple of the Moon's flake fixed after it).
Also per batch: `openyamm-studio/tests/s5_checks.sh` (catalogue, contract native/wasm/worker, host tests, Vitest, lint),
`tests/native_vs_wasm.sh` (22/22), 22 projects byte-identical old binary against new.

Pitfalls seen: another session rebuilding `build/game/openyamm` mid-check (failures saying "No such file" or a stale
binary refusing an asset key): rebuild through the lane and rerun; release sessions (openyamm-03, openyamm-57) ask to
pause tracked edits and for SHIP/HOLD lists: answer and wait for their "done"; subagents cannot write report files
(the harness refuses): have them put the full report in their final message and save it yourself.

## 5. Rules (from AGENTS.md, CLAUDE.md and the user)

Never `git add/commit/stash/restore --staged/reset` unless he asks; no Vulkan builds; never copy OpenEnroth or
mm_mapview2 code; `assets_dev` files are hard links: never edit in place (write a new file and rename); game builds
only through the lane `flock -x level_generation/projects/mm9r_common/locks/cmake_build.lock cmake --build build
--target openyamm -j25`; game runs via `SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated <unique> ...`; `rm` only
with literal paths, after `ls`, as its own command; wait on exact PIDs, never `pgrep -f`; no Claude attribution in
commits; agents build only in `build-s4`/`build-fix`, never `openyamm-studio/build/`; never `npm install` outside a
folder with its own package.json; MM9 map Lua is converter-generated (AGENTS.md); deployments, uploads and other
outward actions need his explicit word. Up to 8 agents at a time are fine with him.

## 6. Waiting on the user (FOR_THE_USER.md)

- G1-G5 (item 16): game changes for S6 (G3 named mods in the game is S6's last exit criterion); plus two helpful
  ones: ladder stepping movable out of `IndoorPartyRuntime` (so the browser's walk climbs), bakes honouring
  `--extra-mount`.
- The hosted deploy (item 14): the studio into the repository, an origin, a publishing step, the download's default
  origin.
- Optional hands-on checks: walk and pin in the browser, a room wing and a town block by hand.

## 7. Open studio work (no decision needed)

- After S7: merge the S6 leftovers; rerun every check.
- Missed hosted budgets (S5c): Chrome's first open (lazy wasm compile), indoor commit p95 in the browser, outdoor 3D
  after a commit, the 2.98 MB core download.
- Terrain for new open-air BLVs (a core rasteriser, see S5.md "S6 leftovers").
- Code list `rounds/NEXT_CODE_BATCH.md` items 20-23 and the rebuilds' missing words (Erathia round two's: walls
  leaning outward, half-hip roofs, tent doors, recesses open at a corner, cut-corner platforms; Castle Ironfist's door
  sills, an outside ramp, several boards on one post).
- Two dead words found by the read record: `kerb_width` on Erathia's viaduct, `facing` on a doorway in mm6_outd3.
- Xeen: the next stage (more maps) follows the design documents and CHANGES_FOR_BUILT_MAPS.md once the user wants it.
- Housekeeping: deletable scratch (`output/s5_spikes/` 7.4 GB, `openyamm-studio/s5c_work/install20_tree` 8.5 GB,
  `output/studio_s6/cmp22_*`); three `host.mjs mcp` processes of unknown owner left alone.

## 8. Update by the next lead (2026-11-16 morning)

Done since this handoff: game changes G1-G5 (S5.md "S6's game changes G1-G5"; checked against a frozen post-S7 game in
`output/studio_lead/g/`, with `oldnew.sh`, `play.sh`, `scen.sh`, `load_ab.sh` there for reuse); S8, the open studio work
(`S8_PLAN.md`, merges 35-39, every workstream's record); the five next Xeen maps (`devdocs/xeen/ACT2_BUILD.md`), installed
in `output/studio_play/xeen_root` with 36/36 playtests. Waiting on the user: FOR_THE_USER.md items 17-19 (the commits of
S7 and G1-G5, the game changes found during S8 and the Xeen maps). Last merge: 39.
