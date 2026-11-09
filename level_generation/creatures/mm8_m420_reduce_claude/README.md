# MM8 Pirate Mage (`m420`, Pirate Mage A/B/C and Wimpy Pirate Mage A/B/C) reduction (2026-10-19)

User: "OK do these ones" (MM8 reduction batch of openyamm-b4: m420, m416, m500, m508, m480). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed rebuilding, so the installed
textures, six palette variants (`KHR_materials_variants`) and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m420.glb`, byte-identical to
`../mm8_m420_claude/export/mm8_m420.glb` (revision m420_coat_skin_v8; the `assets_dev` runtime copy was cooked from it
at the same time, nine clips), copied to `work/mm8_m420_source_pre_reduce.glb` (rollback source). One material per
tier (`PirateMage_A/B/C`, twice: the Wimpy tiers repeat the names), merged 2080x1024 head/body atlas (head set
u > 0.5), node `PirateMage`, 58 bones, 4 influences. The cobra staff (`mm8_m420_staff.glb`, 1,800 triangles) is
unchanged and not part of this build. Scripts are copied from `../mm8_m412_reduce_claude/scripts/` (the sibling
Pirate Warrior: parent-before-transform fix, per-region helpers), with the production project's
`preserve_peg_lods.py` and `shrink_shadow_lods.py`.

## Keep sets and regions (`make_groups.py`)

Weld 6,944 -> 696 open edges; 2 coincident vertices with other weights (no split seam). 22 connected pieces.

| label | faces | ratio |
|---|---:|---|
| face skin (head-skin piece, front, above 1.45 m) | 1,560 | 70 % |
| neck, ears, scalp (rest of the head-skin piece) | 744 | 50 % |
| hair mass | 800 | 55 % |
| beard (two head-set pieces over 180 faces) | 498 | 65 % |
| left (open) hand and fingers | 1,505 | 50 % |
| rest: coat, shirt, breeches, stocking, shoe | 6,901 | remaining budget |

Kept exactly (`work/keep_d.npy`, 3,972 faces):
- the staff fist (`B_R_Hand` / `B_R_Finger*` dominant faces, 1,601), so the fitted staff grip does not change;
- small pieces of up to 180 faces (1,444): eyes, brows, two small beard strands, both cuffs, the sash, the shoe
  buckle and **the wooden peg** (160 faces; the production build keeps it whole at every LOD, see Build);
- the soles (faces below 6 cm, 361);
- the hair/skin border: faces of the hair and the head-skin piece within 1.2 cm of the hair's open rim (643), so the
  hairline does not move against the skin (the sibling m412 had a hole at the temple where its bandanna rim and the
  open scalp moved apart). Here the head skin is closed: its only open loop is at the neck, so no scalp opening can
  show through the hair;
- a 4 cm patch at the crotch seam of the breeches and at the left armpit, both sides (59 faces, `patch_keep.py`):
  the first ladder failed every step there (47 mm at `Running:0`, the breeches' crotch seam where the thighs part);
- one drift-lock round (121 faces, from ladder c at 72 %).

## Ladder (limits for the 1.684 m height: p99 5.05 mm, max 25.3 mm)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 12,008 | | | | |
| a: fist, small, soles, border kept; face 75, neck 60, hair 60, beard 70, left hand 60 | 75 % | 9,004 | 4.41 / 47.5 | 0.990 | 0.994 | fail (crotch) |
| b = a + crotch/armpit patch | 75 % | 9,004 | 4.39 / 23.0 | 0.993 | 0.994 | pass |
| b | 70 % | 8,404 | 6.29 / 35.1 | 0.988 | 0.990 | fail |
| c = b; face 70, neck 50, hair 55, beard 65, left hand 50 | 72 % | 8,640 | 4.93 / 23.0 | 0.993 | 0.994 | pass; drift 10 faces over 40 (36 cm2) |
| c | 70 % | 8,400 | 5.56 / 35.1 | 0.992 | 0.992 | fail |
| d = c + one drift lock | **73 %** | **8,762** | 5.02 / 23.0 | 0.994 | 0.994 | **pick**; drift 5 faces over 40 (2.8 cm2) |
| d | 72 % | 8,642 | 5.36 / 23.0 | 0.993 | 0.994 | fail (p99) |

The lock moves the p99 slightly (the locked faces push the cut elsewhere); d73 keeps the texture as the source
(`texture_drift.py r73`: the largest drift over 40 was a 15 cm2 hair face at the back of the head in c72) and passes.

## Checks

- **Close-ups straight from the GLBs** (`glb_close.py`, each file's own normals; installed top, reduced bottom):
  `review/glbclose/sheet_a_tex.png` / `sheet_a_clay.png` (head front, three-quarter, side, back, right, both temples,
  top, chin, staff fist), `sheet_b_tex.png` / `sheet_b_clay.png` (left hand, torso, sash, back, legs, peg, shoe,
  crotch, Running, Attack, Death), `sheet_hands.png` (both hands at the Cast release, front and back). Face, beard,
  hair, hairline, coat trims, cuffs, buttons, peg and shoe match; the left hand at 50 % keeps every finger (the nail
  bumps are softer).
- **Hands** (`../mm8_m420_claude/scripts/g5_hand_stretch.py` on blends imported from the GLBs, `glb_to_blend.py`;
  all eight roles): right (staff fist, kept) 2.11x in every role, as installed; left at most 1.89x (installed 2.44x
  in Running), every other role equal or lower.
- **LODs** (`lod_check.py`, `work/lod_check_{src,d73}.json`): no face stretches over 20x in any frame of any clip at
  any LOD. Lowest point: LOD0/1 dip 0.8 / 1.0 mm below the floor in Death (installed +1.0 to +2.0 mm), every other
  clip and LOD as installed or higher. Rest height 1.702 / 1.702 / 1.699 / 1.697 m (installed 1.700 / 1.700 / 1.701 /
  1.700). `review/lods/sheet.png`: installed / reduced for each LOD, standing three-quarter, Attack, Running.
- `check_winding.py`: 0 inverted closed parts.
- **Walking height jump** (`walk_heights.py`, `work/walk_src.json`; the Pirate Warrior's walk showed one): nothing
  at viewer frames 14-16 (head moves 4 mm per frame at most). The installed Walking clip does rise 7.3 cm in two
  frames at viewer frames 36-38 (head 1.356 -> 1.384 -> 1.429 m, pelvis the same), when the peg lifts off. That is in
  the source clip; the reduction changes no clip. Not fixed here.

## Build

`export_cand.py` (`REA_CAND=Cand_73 REA_NODE=PirateMage`, `work/ladder_d.blend`, 4 influences, smooth normals) ->
`swap_lod0.py ... PirateMage` (`work/d73_lod0.glb`) -> `blender -b -P build_lods.py` (tools/build_actor_lods.py,
0.5 / 0.25 / 0.125) -> `preserve_peg_lods.py` (the production step: the 160-face peg replaces its collapsed copy in
LOD1-3 and their shadows) -> `shrink_shadow_lods.py` (production copy) -> `carry_variants.py` (also points LOD
primitives back at material 0: the builder matches materials by name and took the Wimpy tier's same-named
`PirateMage_A`, index 3) -> `compact_glb.py`: `export/mm8_m420.glb`, 7.1 MB (installed 7.5 MB), 9 clips, 6 variants on
all 8 colour/shadow primitives.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,008 | 6,082 | 3,128 | 1,644 |
| reduced (73 %) | 8,762 | 4,462 | 2,317 | 1,239 |

Viewer: `review/viewer/` (installed vs reduced for the six tiers, revision reduce-1; ramps baked by
`viewer_variants.py`, manifest by `viewer_manifest.py` with sha256 and `?v=`),
<http://127.0.0.1:8912/level_generation/creatures/mm8_m420_reduce_claude/review/viewer/>;
`node level_generation/creatures/claude_shared/check_viewer.mjs <url> 180`: 108 model/clip switches, no console errors.

## Status

Installed 2026-10-19 (user: "pirate mage ok") after `check_winding.py` (0 inverted closed parts); the regression below
passes and the row is in the ledger. Commands used (from the repository root): `python3 tools/install_model.py
level_generation/creatures/mm8_m420_reduce_claude/export/mm8_m420.glb --world mm8`, then
`OPENYAMM_REGRESSION_FILTER=mm8_pirate_mage_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_pirate_mage_actor_models_keep_palettes_staff_cast_and_simulation`) and add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). The staff stays as installed; bindings and scale are unchanged.
Rollback: `python3 tools/install_model.py level_generation/creatures/mm8_m420_reduce_claude/work/mm8_m420_source_pre_reduce.glb --world mm8 --name mm8_m420.glb`.

Reproduce: `REA_GLB=<rollback source> REA_NODE=PirateMage import_source.py` -> `dump_mesh.py` -> `dump_faces.py` ->
`make_groups.py` -> `patch_keep.py work/keep_base.npy work/keep_b.npy 0.002,-0.035,0.729 0.002,-0.065,0.782
0.002,-0.005,0.773 0.268,0.110,1.196` -> `REA_KEEP_FACES=work/keep_b.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.7,2:0.5,3:0.55,4:0.65,5:0.5 run_ladder.sh c 0.72` -> `texture_drift.py r72` ->
`drift_lock.py work/keep_b.npy work/keep_d.npy r72` -> same ratios `run_ladder.sh d 0.73` -> build as above ->
`lod_check.py`, `lod_views.py`, `glb_close.py`, `glb_to_blend.py` + `g5_hand_stretch.py`, `walk_heights.py`, viewer.

## Walk2 and Jog (2026-10-21)

`export/mm8_m420.glb` now also carries `Walk2` (humanoid-set Staff-Walk-Slow-WithStaff, 1.6 s) and `Jog` (Mixamo Jogging, 0.85 s), appended by
[../mm8_pirates_gait_claude](../mm8_pirates_gait_claude/README.md) so every tier walks and chases inside the gait
window (the old Running is a sprint that crawled in game). Existing clips, meshes, LODs and variants are byte-identical;
the pre-gait export is kept as `work/mm8_m420_pre_gait.glb` (rollback: `tools/install_model.py` it with
`--name mm8_m420.glb --world mm8`). Installed 2026-10-21; bindings not changed here. Gate values for every descriptor:
`walking: Walk2`, `run: Jog`, `stride_length: 1.2486`, `run_stride_length: 1.3514`; window residual on Pirate Mage A wandering ×0.64 and Wimpy Pirate Mage C ×1.61 / ×1.58 (wander speeds span 0.50–1.26 m/s). Playback:
[../mm8_m420_gait_claude](../mm8_m420_gait_claude/README.md).

## Head bob (2026-10-22)

The installed source of `mm8_m420` now carries walk/run clips reshaped by [head_bob_claude](../head_bob_claude/README.md)
(`bob_fix.py`: pelvis bob rescaled or evened, legs solved to the original foot paths). `export/` holds the pre-bob GLB:
after a rebuild here, rerun `head_bob_claude/run_jobs.py --only mm8_m420` on the new export (copy it to
`head_bob_claude/work/mm8/` first) before installing.

## Gait rollout (2026-10-31)

The installed source `assets_source/worlds/mm8/models/mm8_m420.glb` now also carries `WalkSlow` (Staff-Walk-Slow-WithStaff, 1.80 s, stride 1.0729: tier A's wandering) and `Walk3` (the same source, 1.25 s, stride 1.4342: B/C's chase, Wimpy C's wandering); peg leg kept rigid, grounding evened between the peg and the shoe.
Appended by [package h17](../gait_rollout_20261031/h17/README.md) on the installed source (existing clips, meshes, LODs
and variants byte-identical); pre-gait copy and rollback: `../gait_rollout_20261031/h17/work/mm8_m420_pre_gait.glb`.
Bindings are in `../gait_rollout_20261031/h17/bindings.yml` (applied by the rollout coordinator). Rebuild:
`../gait_rollout_20261031/h17/scripts/rebuild.sh m420`. A far-LOD repair, head-bob or reduction rerun that rewrites
this source must re-graft these clips (copy the new source over the pre-gait copy and rebuild, or
`claude_shared/graft_clips.py`).
