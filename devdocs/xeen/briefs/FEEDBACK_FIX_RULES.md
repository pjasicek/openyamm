# Rules for the feedback-fix agents (fourth orchestrator, 2026-11-21 night)

You are one of several agents fixing families of the user's play feedback
([reviews/USER_FEEDBACK_20261121.md](../reviews/USER_FEEDBACK_20261121.md)) at the same time. Read that file first.

**The user's rule:** fix each family **structurally**: at its source (generator, kit, common Lua, data, engine), then on
**every** site of its kind in the Xeen world, plus a check that keeps it fixed (audit rule, build-time refusal, test).
The reported spot is only the example. Report the full list of sites you found and what happened to each.

Read before working: [lanes/README.md](../lanes/README.md) (all lane rules apply), the lane files of the lanes whose
files you touch (`lanes/<lane>.md`, State and tools), [DECISIONS.md](../DECISIONS.md) rows on your topic.

## Ownership and coordination

- You act for the lanes that own what you change (the brief names them). Append a short dated block to each such lane
  file (`lanes/<lane>.md`, Log) saying what you changed, so the lane's next session knows.
- **Per-map lock:** hold `flock output/xeen_locks/<stem>.lock <command>` (e.g. `xeen_x1`) around editing a map's
  generator, building, installing, baking and testing it. Other agents may be waiting on the same map: keep the lock
  short (do the whole edit-build-install-bake-test for that map, then release).
- **Bakes:** run every lighting bake under `flock output/xeen_locks/bake.lock` (one bake at a time in the program).
  Install before bake, never after. `python3 tools/lighting/stale_bakes.py --check` 0 when you stop.
- After rebuilding an **indoor** map: `python3 tools/maw/xeen_pack_reserve.py <stem>` and
  `python3 tools/maw/xeen_balance.py --check` (MAW reserves).
- After any outdoor rebuild: the map's D-85/D-87 checker if it has one (`output/studio_cal/x2/tools/check_d85.py`,
  `output/studio_cal/a6/s31/d85.py`).
- Generated files are never edited by hand (`assets_dev/worlds/xeen/data_tables/*`, `events/maps/<stem>.lua` from the
  studio build): change the generator (`tools/xeen/build_world.py` modules, the map's `gen.py`) and regenerate
  (`build_world.py --only <module>`, a write only when `--check` shows nothing but your change).
- `assets_dev/worlds/xeen/world.yml` and `source/maps.yml` are the orchestrator's: put needed edits in REQUESTS.
- **Engine / Map Studio code:** only A1 builds. If your family needs C++ (game or `openyamm-studio/`), do not build:
  write an exact spec (files, functions, behaviour, MM6–MM9 impact, the test) in your report under REQUESTS to A1;
  the orchestrator batches them into the next merge point. Do the data/Lua/generator part yourself.
- Binaries: game `build-xeen/game/openyamm` (merge point 38, 39 may land while you work: A1 is adding mirror
  reflections), oymap `openyamm-studio/build-xeen/oymap`.

## Runs and resources

- Game runs `--isolated <unique name>`, minimised, prefixed `SDL_AUDIODRIVER=dummy`; at most **two** game processes of
  yours at once; wait on exact PIDs (`kill -0 <pid>`), never `pgrep -f`. Engine-native screenshots for before/after
  (`--set debug.screenshot_path=/abs/path.png` or a tour, AGENTS.md "Native Game Visual Checks").
- Scratch under `output/xeen_fb/<your family id>/`, never /tmp. The disk is ~99 % full: delete your own superseded
  scratch and old bake folders (`ls` first, literal paths). Never write into a hard-linked root's files.
- Never `git add/commit/stash/reset/restore`; `git diff <file>` before editing a tracked file; targeted edits only
  (other sessions share the checkout).
- Sub-agents: at most two, they may not fork. Design questions that are not obvious → DECIDE in your report (take the
  cheaper-to-reverse option meanwhile). Wait quietly on long runs; report once.
- Stop at about 300k tokens; say exactly where you stopped.

## Report

Append your family's result under "Results" in `reviews/USER_FEEDBACK_20261121.md` (a short section: cause, the fix at
the source, sites found and fixed, the check added, before/after capture paths). Final message:
DONE / STATE / SITES (count found, fixed, left with reason) / REQUESTS / DECIDE / USER / NEXT.
