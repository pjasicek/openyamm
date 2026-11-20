# Brief: rebuild MM6 Thief (`mm6_thf`, BThief A/B/C) — worker of stream `rebuild` (2026-11-11)

You are the worker the `rebuild` agent hands one model to. Do this model completely, then report. Read first, in order:
1. `../../README.md` (audit), `../COMMON.md` (leases, install, checks, limits), `../REBUILD.md` (route),
   `../LEDGER_rebuild.md` (incl. "Guard pilot findings").
2. The Guard pilot project `level_generation/creatures/mm6_gua_rebuild_claude/README.md` and its `scripts/` (your template for
   helpers: `B.sh` (Blender runner under the lease, `TOKEN=` env), `look.sh`/`look.py` (workbench strips), `dump_uv.py`,
   `bake_ao_gua.py`, `compose_gua.py`, `viewer_gua.py` (viewer GLBs per tier: LOD0 only, ramps baked, attachment merged),
   `viewer_manifest.py`, `shadow_tiny_parts.py`, `blow_time.py`, `prune_hidden.py`, `build_runtime.sh`).
3. `level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md` (arm and hand gate), `CLAUDE_CREATURE_TEXTURES.md`,
   `claude_shared/TEXTURE_QUALITY_PASS.md`, `../../../GAME_ASSET_MODELLING_GUIDELINES.md`.
4. History: `mm6_thf_claude/README.md` (installed: Meshy auto-rig, mitten hands, cloak verlet chains, dagger),
   `mm6_thf_reduce_claude/`, `mm6_thf_gait_h01_claude/`; the audit's rows for mm6_thf (atlas 15.6 %, cloak tears in Sprint,
   hands = mittens). Donor: `mm9_highwayman_claude/` (MM9 HIGHWAYMAN + its child FIGHTERBASE clips: walk, run, Rattack1,
   Hattack1-3, wince, die, taunt; `merge_child.py`; dagger/sword joints `Ybasedagger`, `Ybasesword`; README fully).
   Also `mm6_pfem_rebuild_claude/README.md` once it exists (the previous worker's notes).
## What is known
Thief = MM6 BThief A/B/C (monsters 637-639), binding block in `assets_dev/worlds/mm6/models/actors.yml` (scale 108.68,
walk Walk2, run Jog, sprint Sprint, impact 0.403). Must change: Meshy auto-rig, mitten hands, cloak tearing in Sprint,
texture atlas 15.6 %. Keep the MM6 identity from the HD masters in `mm6_thf_claude/` (reuse gated masters; never send Meshy
native or x2 frames). Quality bar: the MM9 Highwayman.
## Route
- Lease identity `mm6:thf`, project `level_generation/creatures/mm6_thf_rebuild_claude/`, budget 85; backups to
  `work/before_rebuild/` first.
- Mesh from the MM6 HD masters: reuse the old project's gated masters and, if usable, its Smart Topology (0 credits);
  else a new Smart Topology (5 cr) from `references_hd/00_three_quarter.png`. Cloak: as a separate garment on dense
  chains or MM9's own cloth joints if the highwayman has them; it must not tear in any bound clip (motion_audit cloth).
- Skeleton and clips: MM9 HIGHWAYMAN + FIGHTERBASE (Bip01 with Spine3 — NOT the Guard's skeleton). Dagger on the MM9
  weapon joint (re-seat the approved MM6 dagger mesh like `place_halberd.py`, or keep it in the body as the old model
  did). Attack: an energetic FIGHTERBASE/Highwayman melee (Hattack*), ranged/throw from Rattack1 if the native thief
  throws; impact from MM9's events, re-timed to the native length where distinct.
- Hands: MPFB grafts with 15 finger bones per side; fist solved round the dagger grip (Guard: `finish_gua.py`,
  `rotate_hand.py` if the knuckle line is far off the grip).
- Textures: uv_atlas + 4K body paint (10) + 4K head-only paint for a 1K head set (10), gentle grade, tiers as the old
  ramps (region mask + palette ramps).
- Gait: walk/run/sprint must pass `gait_gate.py`; use the `gain` role option when MM9's clips miss the window.
## Checks (all, as COMMON.md): winding 0; install via tools/install_model.py; `motion_audit.py` + `../rebuild_measure.py`
(record attack ratio — gesture, so low is expected — worst region beyond Standing, hand inside %); floor_audit; gait;
the actors regression (`OPENYAMM_REGRESSION_FILTER=mm6_mm7_mm8_actor_models_build_every_binding ./build/game/openyamm
--world mm6 --headless-run-regression-suite actors`; no game build needed); `run_creature_review.py check` (0 errors;
remember to refresh the manifest after rebuilding viewer GLBs: hashes); arm and hand gate on every clip; jitter gate;
viewer shots with `claude_shared/texpass_viewer_shots.py` (before = the installed model, after = new, identical cameras,
every tier; include face close-ups front/3-4 and both hands in Standing) -> `review/sheet_before_after.png`; in game
outdoor + indoor per the playbook test spots (`./tools/run_game.sh --isolated ...`, tour like
`mm6_gua_rebuild_claude/review/ingame_out.yml`, monster ids 637/638/639) -> sheets. Look at every sheet yourself.

## Limits
Meshy only via `tools/run_creature_meshy.sh` (balance before each job), cap 85 credits for this model; one heavy job at a
time (eight agents share the machine), Blender `-t 4`, at most two Blender processes; no Blender MCP tools; no git
add/commit/stash/reset; never edit assets_dev in place (actors.yml: read-modify-write to a temp file + os.replace, touch
only this model's blocks); never kill processes you did not start; do not ask the user anything.

## Deliverables
Project `level_generation/creatures/mm6_thf_rebuild_claude/` with README (route, numbers, sheets, deviations, revert
command); ledger row in `../LEDGER_rebuild.md` (mark `in progress (rebuild)` at claim, `done` at release); lease released.
Final message to the `rebuild` agent: route + donor, triangles LOD0-3, texture numbers, attack ratio, worst region,
credits, before/after sheet path, revert command, open points, and what the user should look at first.
If something is a real blocker, write `BLOCKED: <question>` in the ledger, release the lease and report.
