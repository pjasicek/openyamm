# Overnight run: MM9 dungeons (BLV)

You are the orchestrator of an unattended overnight run. The user is asleep, so nobody can answer questions. Make the decisions you
can, and write down the ones you could not. Keep going until the queue is finished or a stop condition below is reached. Spawn background
subagents; do not build maps yourself. This session may be resumed at any time, so everything you need lives in files.

**On every start or wake-up:** read the ledger `devdocs/mm9_rework/overnight/dungeons_ledger.md` (create it on the first run), check which agents are alive
with ListAgents, look at each project's README and `work/` state, and carry on without redoing finished work.

## Scope
Build the remaining MM9 dungeons as native BLVs in the review root `output/mm9_rework/assets_dev`, one agent per map, **at most 5 at once**, each following
`level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md` in full. Read it and `devdocs/mm9_rework/PLAN.md`, `MM9_VISUAL_PROPERTIES.md` and `devdocs/mm9_rework/README.md` first.
The six finished maps are references: `mm9r_chasmofthedead` and `mm9r_beethoven` have the fullest records, `mm9r_drangheimprison` the NPC and quest route.

Queue, in order:
1. `verhoffinruins`  2. `bathhouse`  3. `ruinedtemple`  4. `klusoshouse`  5. `inventastorca`  6. `dookscastle`  7. `traininghall`  8. `tasaracademy`
9. `lindisfarnemonastery`  10. `thjoradmine`  11. `yanmirsfort`  12. `darkpassageway`  13. `1000terrors`  14. `connectingtunnels`  15. `dungeonofsecrets`
16. `hallofthegods`  17. `thearena`  18. `dragonstadium`  19. `greatgate`

Sizes and monsters are in `devdocs/mm9_rework/INVENTORY.md`. A special map such as `greatgate` or `hallofthegods` may not fit the route; if so, record why and go on.

## Definition of done for a map
A project in `level_generation/projects/mm9r_<map>/` with a README in the format of the finished maps, and a matching props project. In the review root: BLV, scene, Lua, minimap line map, fresh bake.
Each MM9 scripted object is either a native event citing its `.scr` or listed as unmatched with the reason.

Put these in every agent's prompt, on top of the playbook (all learned the hard way):
- **Reference shots** with `--set video.view_distance=unlimited`, or our own fade reads as mist.
- **Hue** from MM9's DAT lightmaps, not from the old-import column: `mm9r_common/hue_vs_lightmaps.py`. Do not desaturate because a sheet looks saturated; ours has come out less coloured than MM9.
- **Real clicks** in scenarios for doors, levers, chests and quests. Rotating doors use `motion: rotate`; ladders are real ladders.
- **Monster reach:** audit "cut off" findings are tested in game with a plain-floor control, in and out of sight, and reported per region as real or false. Bodies carry MM9's sizes, not a stand-in's radius.
- **Thin walls:** check `work/dropped_faces.json` for thin partitions and turn on `thin_walls` where it restores a real wall, or a cow walks through it. Animals are not `immobile`.
- **Flames:** use the props pipeline as fixed on 2026-10-30 (`card` mode, seat on the head), and look at a flame from the side in game.
- **Flooded spaces:** diving is not built. Use a wading floor as Beethoven did, keep the conversion reversible, and note it.
- **Missing monster art:** untextured or stand-in actors are fine; another session is building them.
- **Mean brightness** within about 10 % of MM9 where possible; list views that are not. `tools/lighting/stale_bakes.py` must not list the map.
- **Bakes:** run every Cycles bake through `level_generation/projects/mm9r_common/bake_slot.sh <command>`, at most two at once: each takes 16 of the 32 threads.
- **Look at your own sheets.** Reports list what was not checked. Do not report success from numbers alone. You read each map's compare sheet yourself before marking it done.

## Shared code
- The dungeon converter in `mm9r_common/dungeon/` is shared. Changes are minimal and opt-in, default off, with the Lich Lab `--plan` result unchanged. One agent changes it at a time, under a flock you choose and record in the ledger.
- This session owns `build/`: `cmake --build build --target openyamm -j25`. One build at a time. If you see layout crashes after an edit, touch the header and rebuild.
- Small engine fixes are allowed when a map needs them, in the shared path, with a test, without changing MM6–MM8 behaviour. Anything larger, or any change to how MM6–MM8 plays, is written down and not made.
  After engine changes run `openyamm_unit_tests` and the `indoor` regression suite with `--user-data <private folder>`. Five `indoor` cases were failing on 2026-10-30; check `devdocs/REGRESSION_DIAGNOSIS_20261030.md` for the current state and do not add to them.
- Do not change MM6–MM8 worlds' data, or anything under `assets_dev/engine` except decoration models and bindings as the playbook says. Decoration rows go in the MM9 world's range under its lock.
- Do not start ODM work; the user wants to calibrate those.

## Rules for this repository (other accounts do not have these)
- Never run `git add`, `commit`, `stash`, `reset` or `restore --staged`. Never push.
- No Vulkan builds. Android cooks only when the user asks.
- Safe deletes: `ls` first, then `rm` with literal paths in its own command. Never shell variables or wildcards, never anything under `/dev`.
- Never kill a process you did not start; verify the PID first. Killing a parent PID once took down every session.
- Wait on your own game run's exact PID (`kill -0 <pid>`), never on `pgrep -f`.
- Keep what must survive in the repo: a reboot wipes `/tmp` and the scratchpad.
- `assets_dev` files are hard-linked into `output/`: temp file + rename only. Install models with `tools/install_model.py`, never by copying. Run `check_winding.py` first.
- Do not edit Lua files headed `-- generated from legacy EVT/STR`.
- Game runs: `./tools/run_game.sh --isolated <unique name> ...`, with `--assets "$PWD/output/mm9_rework/assets_dev"`; they may overlap. Never put `--set` before `--headless-run-scenario`.
- Meshy is not needed for dungeons: props are MM9's own models. Skins are plain Lanczos ×4, no Real-ESRGAN. Codex x4 comes later.
- Useful background, read by path: `/home/pjasicek/.claude-pjasicek/projects/-home-pjasicek-github-OpenYAMM/memory/` (`mm9-visual-properties.md`, `tmp-not-durable.md`, `safe-deletes.md`,
  `never-kill-parent-pids.md`, `headless-set-args.md`, `build-race-stale-objects.md`, `hesper-decoration-placement.md`).

## Bookkeeping
After each map, update the ledger: faces, rooms, movers, monsters, scenarios, brightness, unmatched items, sheet paths, what was not checked. Update the Dungeons line in `devdocs/mm9_rework/STATUS.md`.

## Stop conditions
A map that fails after two serious attempts is recorded and skipped. When the queue is done, let running agents finish, and write a section "Morning report" at the top of the ledger:
maps ready to play with the command for each, failures and why, engine changes made, anything broken. Then end.
