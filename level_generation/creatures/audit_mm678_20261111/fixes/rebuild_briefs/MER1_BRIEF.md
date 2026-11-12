# Brief: rebuild MM6 Merchant (`mm6_mer1`, Merchant A/B/C, club) — worker of stream `rebuild` (2026-11-11)

You are the worker the `rebuild` agent hands one model to. Do this model completely, then report. Read first, in order:
1. `../../README.md` (audit), `../COMMON.md` (leases, install, checks, limits), `../REBUILD.md` (route),
   `../LEDGER_rebuild.md` (incl. "Guard pilot findings").
2. The Guard pilot project `level_generation/creatures/mm6_gua_rebuild_claude/README.md` and its `scripts/` (your template for
   helpers: `B.sh` (Blender runner under the lease, `TOKEN=` env), `look.sh`/`look.py` (workbench strips), `dump_uv.py`,
   `bake_ao_gua.py`, `compose_gua.py`, `viewer_gua.py` (viewer GLBs per tier: LOD0 only, ramps baked, attachment merged),
   `viewer_manifest.py`, `shadow_tiny_parts.py`, `blow_time.py`, `prune_hidden.py`, `build_runtime.sh`).
3. `level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md` (arm and hand gate), `CLAUDE_CREATURE_TEXTURES.md`,
   `claude_shared/TEXTURE_QUALITY_PASS.md`, `../../../GAME_ASSET_MODELLING_GUIDELINES.md`.
4. History: `mm6_mer1_codex/` (installed Codex build on QA hold: club grip gaps up to 75 mm, body penetration 64 mm,
   coat hem findings, "hands noted as odd"), `mm6_mer1_reduce_claude/`, `mm6_mer1_gait_h05_claude/`; audit: atlas 13.9 %,
   bland attack (ratio 0.42). Donors: MM9 PEASANTMALE or NOBLEMAN body clips (look for `mm9_peasantm*_claude`,
   `mm9_nobleman*_claude` or the MM9 male library, `glbs_mm9.txt` in the audit folder), club attack from FIGHTERBASE
   (`mm9_highwayman_claude/`) or TRELLBORG. Read the Thief worker's `mm6_thf_rebuild_claude/README.md` too.
## What is known
Merchant = MM6 Merchant A/B/C (monsters 577-579), block in `assets_dev/worlds/mm6/models/actors.yml` (scale 103.94,
z_offset, walk Walking, run Jog, impact 0.882; club attachment `mm6_mer1_club.glb`). Keep the MM6 identity from the
gated HD masters of the old project (reuse; never native/x2 frames to Meshy).
## Route
- Lease identity `mm6:mer1`, project `level_generation/creatures/mm6_mer1_rebuild_claude/`, budget 85; backups first.
- Mesh: old gated masters + Smart Topology if usable (0-5 cr). A coat/robe hem: dense chains or MM9 skirt-style hinges,
  no tearing in any bound clip; club grip gaps ≤ ~5 mm (solve the fist round the handle), no club-body penetration.
- Skeleton and clips: an MM9 male civilian body (PEASANTMALE/NOBLEMAN) for idle, walk, run, hit, death; an energetic club
  attack — if the civilian skeleton has no attack, take one from a skeleton with the same joint names (check names!) or
  record the reason and use the playbook's library route for the attack. Target attack ratio about 1.0 (was 0.42).
- Hands MPFB grafts, textures uv_atlas + 4K paints + head set, gentle grade, tiers as the old ramps; gait gate as above.
## Checks (all, as COMMON.md): winding 0; install via tools/install_model.py; `motion_audit.py` + `../rebuild_measure.py`
(record attack ratio — gesture, so low is expected — worst region beyond Standing, hand inside %); floor_audit; gait;
the actors regression (`OPENYAMM_REGRESSION_FILTER=mm6_mm7_mm8_actor_models_build_every_binding ./build/game/openyamm
--world mm6 --headless-run-regression-suite actors`; no game build needed); `run_creature_review.py check` (0 errors;
remember to refresh the manifest after rebuilding viewer GLBs: hashes); arm and hand gate on every clip; jitter gate;
viewer shots with `claude_shared/texpass_viewer_shots.py` (before = the installed model, after = new, identical cameras,
every tier; include face close-ups front/3-4 and both hands in Standing) -> `review/sheet_before_after.png`; in game
outdoor + indoor per the playbook test spots (`./tools/run_game.sh --isolated ...`, tour like
`mm6_gua_rebuild_claude/review/ingame_out.yml`, monster ids 577/578/579) -> sheets. Look at every sheet yourself.

## Limits
Meshy only via `tools/run_creature_meshy.sh` (balance before each job), cap 85 credits for this model; one heavy job at a
time (eight agents share the machine), Blender `-t 4`, at most two Blender processes; no Blender MCP tools; no git
add/commit/stash/reset; never edit assets_dev in place (actors.yml: read-modify-write to a temp file + os.replace, touch
only this model's blocks); never kill processes you did not start; do not ask the user anything.

## Deliverables
Project `level_generation/creatures/mm6_mer1_rebuild_claude/` with README (route, numbers, sheets, deviations, revert
command); ledger row in `../LEDGER_rebuild.md` (mark `in progress (rebuild)` at claim, `done` at release); lease released.
Final message to the `rebuild` agent: route + donor, triangles LOD0-3, texture numbers, attack ratio, worst region,
credits, before/after sheet path, revert command, open points, and what the user should look at first.
If something is a real blocker, write `BLOCKED: <question>` in the ledger, release the lease and report.
