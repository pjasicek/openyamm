# Overnight dungeon agent brief (2026-10-30)

You build **one** MM9 dungeon as a native BLV, unattended: the user is asleep, nobody answers questions. The
orchestrator (the session that started you) gives you the map name. Decide what you can, write down what you could not,
and keep going until your map meets the definition of done or you have failed twice seriously.

## Read first
1. `level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md` in full: you follow it step by step.
2. `devdocs/mm9_rework/PLAN.md`, `devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md`, `devdocs/mm9_rework/README.md`.
3. The finished maps as references: `level_generation/projects/mm9r_chasmofthedead/` and `mm9r_beethoven/` (fullest
   records), `mm9r_drangheimprison/` (NPCs and quests by RUDE dialogue), plus `mm9r_templeofhonk`, `mm9r_lichlab`,
   `mm9r_anskramkeep`. Copy their scripts' structure (convert.py, make_scenarios.py, make_tour.py) and adapt.
4. Your map's row in `devdocs/mm9_rework/INVENTORY.md` (size, monsters, chests, doors, exits, content).
5. Background notes, read by path: `/home/pjasicek/.claude-pjasicek/projects/-home-pjasicek-github-OpenYAMM/memory/`
   `mm9-visual-properties.md`, `tmp-not-durable.md`, `safe-deletes.md`, `never-kill-parent-pids.md`,
   `headless-set-args.md`, `build-race-stale-objects.md`, `hesper-decoration-placement.md`.

## Definition of done
- `level_generation/projects/mm9r_<map>/` with a README in the finished maps' format (quality gates with numbers), and a
  matching props project `level_generation/props/mm9_<map>_claude/`.
- In the review root `output/mm9_rework/assets_dev`: BLV, scene, Lua, minimap line map, fresh bake.
- Every MM9 scripted object is a native event citing its `.scr`, or listed as unmatched with the reason.
- Review sheets (MM9 original | native, ≥ 20 eye-level views; lighting original | unbaked | baked) that **you have
  looked at yourself** (Read the PNGs). Do not report success from numbers alone; list what you did not check.

## Learned the hard way (on top of the playbook)
- **Reference shots** with `--set video.view_distance=unlimited`, or our own fade reads as mist.
- **Hue** from MM9's DAT lightmaps, not from the old-import column: `mm9r_common/hue_vs_lightmaps.py`. Do not
  desaturate because a sheet looks saturated; ours has come out less coloured than MM9.
- **Real clicks** in scenarios for doors, levers, chests and quests. Rotating doors use `motion: rotate`; ladders are
  real ladders.
- **Monster reach:** audit "cut off" findings are tested in game with a plain-floor control, in and out of sight, and
  reported per region as real or false. Bodies carry MM9's sizes (ABC extents × Scale × 2.56), not a stand-in's radius.
- **Thin walls:** check `work/dropped_faces.json` for thin partitions and turn on `thin_walls` where it restores a real
  wall, or a cow walks through it. Animals are not `immobile`.
- **Flames:** use the props pipeline as fixed on 2026-10-30 (`card` mode, seat on the head), and look at a flame from
  the side in game.
- **Flooded spaces:** diving is not built. Use a wading floor as Beethoven did, keep the conversion reversible, note it.
- **Missing monster art:** untextured or stand-in actors are fine; another session is building them.
- **Brightness: calibrate against MM9's own DAT lightmaps, not the reference capture** (user decision 2026-10-30 22:30, after the orchestrator rule of 22:25,
  replacing the 22:04 rule). The "MM9 original" capture is the old import drawn by our outdoor renderer and is far too
  bright and grey: a real MM9 screenshot of Verhoffin Ruins' spawn measures luma 62, RGB (68,63,45), against the capture's
  94 and a lightmap-matched bake's 56, (62,56,41) (`devdocs/mm9_rework/overnight/mm9_real_vs_ours_verhoffinruins_spawn.jpg`).
  Match each zone's mean and hue to the DAT lightmaps × texture (`mm9r_common/hue_vs_lightmaps.py`; Verhoffin Ruins'
  README has the method and numbers), keep MM9's dark rooms dark, and report the capture ratio only as information.
  Document a capture-matched alternative only if you think it is needed. `tools/lighting/stale_bakes.py` must not list
  the map.
- **How MM9 draws light (proven from its renderer, `devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`):** walls are
  texture × lightmap **×1** (no ×2, no gamma, no brightness term), so match the stored lightmap texels without a
  multiplier. On top of that MM9 adds dynamic lights (`Fire` objects, flickering candles) additively; where a room has
  them, real screenshots come out brighter than the lightmaps (Klusos House 1.2-1.37×, Verhoffin 1.1×). Real
  screenshots in `devdocs/mm9_rework/overnight/real_mm9/` outrank the math: if your map has any, find each shot's
  spot, capture the same view and calibrate to it. Props/models in MM9 are lit by world `AmbientLight` + nearby lights at
  full colour (no BrightScale, no shadows) + a flat `ModelAdd` 30/255: they read brighter and warmer than the walls.
  An engine mode for that is being prepared; until then use the sector-minimum-light workaround below.
- **No pitch-black rooms.** MM9 carries a player light (`PlayerLightOn` in WorldInfo) that our engine does not have, so
  rooms whose lightmaps are near zero rendered pitch black in Dark Passageway. Give such rooms a floor so no baked view
  is under about luma 10-12, document it as the player-light stand-in with the setting that reverts it.
- **Prop lighting (revised 01:38):** set `map: {model_lighting: true}` (MM9's model lighting, `devdocs/INDOOR_MODEL_LIGHTING.md`)
  when no light of your map is over the four-per-point cap (`work/lights.json`: no "a floor point already under four
  lights"); Thjorad Mine shows it keeps props x0.7-1.2 of MM9 where the old path draws some black. If capped fill lights
  exist, compare both paths on a few props (Thjorad's `work/model_lighting_props.txt` method) and keep the better; with
  BrightScale pre-multiplied into BLV colours, set `light_scale`.
- **Decorations under the bake:** check that props are not drawn much darker than the walls around them. The engine
  subtracts a frame ambient from decoration light (Inventa Storca README: black tables in rooms lit by bake-only
  DirLights far from BLV lights); the map workaround is sector minimum light 31 (`map.ambient`) with `ambient_scale`
  raised to keep the bake. Report what you see.
- **Old-map `_authored` files:** if the old map has `worlds/mm9/maps/<stem>_authored.scene.yml` or
  `events/maps/<stem>_authored.lua`, remove them from the review root in your convert.py (the shared `OLD_SIDECARS`
  misses them; Thjorad Mine's README). They break the load or replace your Lua.
- **Water must still read as water.** A wading surface keeps MM9's visible blue surface (brush Alpha × texture alpha), not
  a near-invisible tint over the bed.
  `tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev --check` must not list the map.
- **Bakes:** run every Cycles bake through `level_generation/projects/mm9r_common/bake_slot.sh <command>` (two slots,
  16 threads each; it waits for a free slot). Never run Cycles outside it.
- A special map may not fit the route (no geometry, a cutscene stage): if so, write why in the README and your status
  file and stop.

## Shared resources (other map agents run at the same time, up to five)
- **C++ builds belong to the orchestrator.** Do not run `cmake`. `build/game/openyamm`,
  `build/tools/mm9_compile_indoor_source` and `openyamm_indoor_source_tests` are built. If your map needs a small
  engine fix (shared path, with a unit test, no change to MM6–MM8 behaviour), make the source edit and the test, then
  finish your turn with a final message starting `BUILD REQUEST:` naming the targets and the tests to run. The
  orchestrator builds, runs `openyamm_unit_tests` and the `indoor` regression suite, and resumes you with the result.
  Anything larger, or anything changing how MM6–MM8 play: write it down in your README, do not make it.
- **The shared converter** `level_generation/projects/mm9r_common/dungeon/`: changes are minimal and opt-in (default
  off). One agent at a time: claim it with `mkdir level_generation/projects/mm9r_common/locks/converter_edit.d` (fails
  if held: then put your change in your map's `convert.py` hooks, or wait and retry later), write your map name into
  `converter_edit.d/owner`, and release it with `rm level_generation/projects/mm9r_common/locks/converter_edit.d/owner`
  then `rmdir level_generation/projects/mm9r_common/locks/converter_edit.d`. Before releasing, prove the Lich Lab
  result is unchanged: `python3 level_generation/projects/mm9r_lichlab/convert.py --plan --scratch <dir>` before and
  after your change, outputs identical. Note the change in the playbook's package-changes text and in your README.
- Decoration rows, sprites and `worlds/mm9/models/indoor_decorations.yml`: only inside
  `flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock`, as the playbook says. Check
  `assets_source/engine/models/` before naming a prop model; reuse existing `mm9_deco_*` models.
- Review-root tables: `tables.update_tables` takes `locks/review_tables.lock`.

## Rules for this repository
- Never run `git add`, `commit`, `stash`, `reset` or `restore --staged`. Never push.
- No Vulkan builds. No Android cooks.
- Safe deletes: `ls` first, then `rm` with literal paths in its own command. Never shell variables or wildcards in an
  `rm`, never anything under `/dev`.
  A project hook (`.claude/hooks/guard_rm.py`, 2026-10-31) refuses such an `rm`, `xargs rm` and pattern `find` deletes.
- Never kill a process you did not start; verify the PID first. Killing a parent PID once took down every session.
- Wait on your own game run's exact PID (`kill -0 <pid>`), never on `pgrep -f`.
- Keep what must survive in the repo (your project's `work/`), not `/tmp` or a scratchpad: a reboot wipes them.
- `assets_dev` files are hard-linked into `output/`: temp file + rename only. Install models with
  `tools/install_model.py`, never by copying; run `check_winding.py` first.
- Do not edit Lua files headed `-- generated from legacy EVT/STR`.
- Do not change MM6–MM8 worlds' data, or anything under `assets_dev/engine` except decoration models and bindings as
  the playbook says. Decoration rows go in the MM9 world's range under its lock. No ODM work.
- **No sound (user, 2026-10-30 22:15):** every desktop game run starts with `SDL_AUDIODRIVER=dummy` in front, e.g.
  `SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated ...` (headless scenarios already use the dummy driver).
- Game runs: `./tools/run_game.sh --isolated <unique name, prefixed with your map> ...` with
  `--assets "$PWD/output/mm9_rework/assets_dev"`; runs overlap, do not wait for others. Headless:
  `./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" --headless-run-scenario <yml> ...`; never put
  `--set` before `--headless-run-scenario`.
- Meshy is not needed: props are MM9's own models. Skins are plain Lanczos ×4, no Real-ESRGAN.

## Your status file
Keep `devdocs/mm9_rework/overnight/status/<map>.md` current (the orchestrator reads it on every wake-up; you may be
resumed after a restart, so it must say where you are): phase, last step done, next step, blockers. When finished,
put there: faces, rooms, portal faces, movers, lights, decorations, chests, monsters (actors), scenarios (pass/fail
each), brightness (MM9 mean / ours, views off by > 10 %), unmatched scripted objects, sheet paths, what was not checked.
Your final message to the orchestrator repeats that summary, starting `DONE <map>` or `FAILED <map>` (with why).
