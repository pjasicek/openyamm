# Brief: rebuild MM6 PeasantF1 (`mm6_pfem`) — worker of stream `rebuild` (2026-11-11)

You are the worker the `rebuild` agent hands one model to. Do this model completely, then report. Read first, in order:
1. `../../README.md` (audit), `../COMMON.md` (leases, install, checks, limits), `../REBUILD.md` (route; **PeasantF1 history**),
   `../LEDGER_rebuild.md` (incl. "Guard pilot findings").
2. The Guard pilot project `level_generation/creatures/mm6_gua_rebuild_claude/README.md` and its `scripts/` (your template for
   helpers: `B.sh` (Blender runner under the lease, `TOKEN=` env), `look.sh`/`look.py` (workbench strips), `dump_uv.py`,
   `bake_ao_gua.py`, `compose_gua.py`, `viewer_gua.py` (viewer GLBs per tier: LOD0 only, ramps baked, attachment merged),
   `viewer_manifest.py`, `shadow_tiny_parts.py`, `blow_time.py`, `prune_hidden.py`, `build_runtime.sh`).
3. `level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md` (arm and hand gate), `CLAUDE_CREATURE_TEXTURES.md`,
   `claude_shared/TEXTURE_QUALITY_PASS.md`, `../../../GAME_ASSET_MODELLING_GUIDELINES.md`.
4. The PeasantF1 history: `mm6_pfem_claude/README.md` (v3, installed), `mm6_pfem_v4_claude/README.md` (rejected),
   `mm6_peasants_fix_claude/README.md` (arm fixes, reverted). Donor projects on the MM9 PeasantFemale skeleton (FHP, 73
   joints, skirt chains, peasantfemale clip library): `mm9_yrsa_claude/` (README + `v2/scripts/`: fit_rig, graft_hands,
   head_split, arm_hand_gate, hand_rest, jitter_gate, floor ops) and `mm9_peasantf1_claude/`, `mm9_peasantf8_claude/`
   (clips_pf.py, sources `source/mm9_lib`, skirt lining, tweak scripts).

## What the user has said (binding)
- v3 (installed `mm6_pfem.glb`): "the body is good, face is terrible", "hands are terrible, especially in standing";
  "no attack needed".
- v4 rejected for heavy hair and heavy far LODs; its rounds also asked: no pale skin, no graft lines at the neck, no clay
  or smudged skin, head in proportion, arms not too thin, symmetric body, a more subtle fidget.
- Three arm-fix rounds ended in "revert the female to original one".
So: keep the v3 body's look and proportions, light hairstyle (her braid as in v3), light far LODs. Give her a good face
and good five-finger hands with a natural, relaxed Standing hand pose (not clasped). Her attack slot may stay a
restrained gesture (native peasants reuse the walk) and must not push hands into the skirt.

## Route (decided by the `rebuild` agent; deviate only with a recorded reason)
- Lease: `python3 tools/creature_workspace.py claim --project level_generation/creatures/mm6_pfem_rebuild_claude
  --identity mm6:pfem --owner rebuild --state creature_3d_progress.json --budget 85`; release when installed and checked.
  Back up `assets_source/worlds/mm6/models/mm6_pfem.glb` (+ any attachment) and the PeasantF1 A/B / Peasantf1 C blocks of
  `assets_dev/worlds/mm6/models/actors.yml` (monsters 595-597) to `work/before_rebuild/` first.
- **Body = the v3 body** (the user's "the body is good"): take the installed v3 LOD0 mesh (and, if they meet the texture
  targets, its UVs/paint: the audit measured atlas 64.4 %, fragments 7.2 %) as the source geometry, NOT a new Meshy body,
  unless the v3 mesh cannot be fitted. Keep her proportions; scale to the MM9 PeasantFemale height for the fit, then set
  `actors.yml` scale so her in-game standing height equals today's (old scale x old/new standing height, as the Guard).
- **Rig and clips = MM9 PeasantFemale** (`mm9_peasantf1_claude/source/...`, library `source/mm9_lib`): joints translated,
  rest rotations kept (Yrsa route). Map: Standing stand1, Walking Walk, Running run, Fidget = a subtle MM9 fidget,
  Hit Wince1, Death Die1, Dead; attack slots = a restrained gesture (e.g. a Conv clip or the Fidget), hands clear of the skirt.
  Skirt: MM9 skirt chains with the dress weights carried over (Yrsa); braid on MM9's braid/ponytail chains if present.
- **Hands**: MPFB five-finger grafts with 15 finger bones per side (`graft_hands.py`; run Blender with
  `BLENDER_USER_EXTENSIONS=$HOME/.config/blender/5.2/extensions` — snap Blender is 5.3, MPFB lives in the 5.2 dir).
  Female macro, "arms not too thin". Relaxed natural curl; check the hand frame with `probe_mitten.py`-style probing
  (Guard pilot: palm from the MM9 mitten curl; `thumb_side_ok` is unreliable). Hands must look right in Standing.
- **Face**: separate 1K head set from a head-only Meshy retexture at 4K (10 cr) using the gated head turnaround in
  `mm6_pfem_claude/references_head/` (step 0 masters already exist: reuse; do not send Meshy native or x2 frames).
  If the v3 head geometry is the problem (check close-ups), use project-and-bake per CLAUDE_CREATURE_TEXTURES.md.
  Skin tone continuous across the neck (no pale skin, no graft line); compare with v3 at identical cameras.
- **Textures**: if the v3 body paint is kept, keep its tiers/ramps; otherwise uv_atlas + 4K paint + gentle grade per the
  texture quality pass. Tiers = region mask + ramps from palettes (v3's ramps).
- **LODs**: light far LODs (v4 was rejected for heavy ones): build_actor_lods ratios, check LOD2/3 counts against v3's.
- **Gait**: run `claude_shared/postprocess/gait_gate.py --world mm6 --model mm6_pfem.glb --candidate <export>`; peasants
  flee at a run pace. If MM9's walk/run miss the window, use the `clips_mm9.py` role option `gain` from
  `mm6_gua_rebuild_claude/scripts/clips_mm9.py` (leg rotations scaled about the clip mean) — the h06 library composer
  breaks on MM9 rest frames.

## Checks (all, as COMMON.md): winding 0; install via tools/install_model.py; `motion_audit.py` + `../rebuild_measure.py`
(record attack ratio — gesture, so low is expected — worst region beyond Standing, hand inside %); floor_audit; gait;
the actors regression (`OPENYAMM_REGRESSION_FILTER=mm6_mm7_mm8_actor_models_build_every_binding ./build/game/openyamm
--world mm6 --headless-run-regression-suite actors`; no game build needed); `run_creature_review.py check` (0 errors;
remember to refresh the manifest after rebuilding viewer GLBs: hashes); arm and hand gate on every clip; jitter gate;
viewer shots with `claude_shared/texpass_viewer_shots.py` (before = installed v3, after = new, identical cameras,
every tier; include face close-ups front/3-4 and both hands in Standing) -> `review/sheet_before_after.png`; in game
outdoor + indoor per the playbook test spots (`./tools/run_game.sh --isolated ...`, tour like
`mm6_gua_rebuild_claude/review/ingame_out.yml`, monster ids 595/596/597) -> sheets. Look at every sheet yourself.

## Limits
Meshy only via `tools/run_creature_meshy.sh` (balance before each job), cap 85 credits for this model; one heavy job at a
time (eight agents share the machine), Blender `-t 4`, at most two Blender processes; no Blender MCP tools; no git
add/commit/stash/reset; never edit assets_dev in place (actors.yml: read-modify-write to a temp file + os.replace, touch
only the PeasantF1 blocks); never kill processes you did not start; do not ask the user anything.

## Deliverables
Project `level_generation/creatures/mm6_pfem_rebuild_claude/` with README (route, numbers, sheets, deviations, revert
command); ledger row in `../LEDGER_rebuild.md` (mark `in progress (rebuild)` at claim, `done` at release); lease released.
Final message to the `rebuild` agent: route + donor, triangles LOD0-3, texture numbers, attack ratio, worst region,
credits, before/after sheet path, revert command, open points, and what the user should look at first.
If something is a real blocker, write `BLOCKED: <question>` in the ledger, release the lease and report.
