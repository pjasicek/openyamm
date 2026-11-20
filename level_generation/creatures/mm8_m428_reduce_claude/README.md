# MM8 female Dark Elf peasant (`m428`, Dark Elf Pesant Female A/B/C) reduction (2026-10-19)

User: "perform the triangle reduction step on it". Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
with its MM8 batch lessons; template [`../mm8_m424_reduce_claude/`](../mm8_m424_reduce_claude/README.md) (the male
peasant). No retexture and no Meshy credits: the reduction keeps UVs, the 2080x1024 atlas, the region mask and the
tier ramps. User approved the 82 % step ("82% is OK"); installed 2026-10-19 and accepted the same day ("ok accepted").

Source: the installed `assets_source/worlds/mm8/models/mm8_m428.glb`, byte-identical to `../mm8_m428_claude/export/`
(after the right-hand dagger-fist fix), copied to `work/mm8_m428_source_pre_reduce.glb` (rollback source). One material
`M428_A` (B/C over `KHR_materials_variants`), node `M428`, 121 bones (64 dress), 4 influences, seven clips with the
cloth-simulated dress baked in. The dagger (`mm8_m424_dagger.glb`, the male's attachment) is unchanged and not part of
this build. Weld: 6,712 -> 1,034 open edges, no coincident vertices with other weights.

Scripts are the male's (`import_source`, `dump_mesh`, `dump_faces`, `decimate_tex`, `reduce_ladder`, `compare_ladder`,
`close_human`, `drift_lock`, `texture_drift`, `dark_slivers`, `export_cand`, `swap_lod0`, `build_lods`,
`carry_variants`, `lod_check`, `viewer_variants`), `err_lock.py` from `mm8_m444_reduce_claude/`, `group_views.py` from
`mm8_m456_reduce_claude/`. New here: `dump_vweights.py` (bone-family weight sums), `make_groups.py` (her regions),
`group_error.py` (surface error per region), `leg_poke.py` (hidden-leg poke-through), `point_close.py` (close-ups at
given points), `gate_blend.py` (a GLB as a blend for the production arm/hand gates), `viewer_manifest.py`.
`run_ladder.sh` uses the pymeshlab venv of an earlier session (`.../da4542c9-.../scratchpad/im_venv`).

## Regions (`make_groups.py`, `review/groups_sheet.png`)

The production build already cut everything but the head (`reduce_rigged.py`: dress/bodice/sleeves 61 %, hidden legs
37 %, hair 70 %, hands 83 %); only the face and neck above 1.44 m were still at Smart Topology density (median face
triangle 0.16 cm2 against 16 cm2 on the dress).

| label | faces | picked ratio |
|---|---:|---|
| 1 face and neck skin (main shell above 1.44 m) | 1,991 | 50 % |
| 2 hair piece (strand cards) | 998 | 80 % |
| palms and forearms of both hand pieces | 644 | 60 % |
| fingers (finger-dominant faces of both hands) | 756 | kept exactly |
| 5 hidden legs (shoes below 13 cm included) | 419 | kept exactly |
| 0 rest: bodice, sleeves, dress, underskirt | 1,986 (not kept) | remaining budget: 83 % |

Kept exactly (`work/keep_j.npy`, 4,327 faces): every piece up to 400 faces (eyes, mouth, fringe, the three lacing
pieces, belt, buckle, shoulder bands: 2,268), the fingers, the hidden legs and shoes, the sleeve-cuff ruffles that
`fix_cuffs.py` cut free (main-shell faces with an arm-weighted vertex below 1.15 m, one ring: 393), gold eyelets painted
on the bodice with one ring (122), and 2 cm patches around the 36 source vertices the e80 candidate missed by over
14 mm (`err_lock.py`, 187 faces: dress inner layers, hem side and back). The 18 cut bridge faces cannot come back: no
edge spans the 4.3 cm gap between ruffle and dress, and a collapse only merges an edge's own vertices.

## Ladder (limits for the 1.70 m height: p99 5.1 mm, max 25.5 mm)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a: face 70, hands 60, legs 55, dress takes the cut | 80 / 77 / 74 / 72 % | 7,954 / 7,656 / 7,358 / 7,160 | 6.4 / 27.5 ... 16.2 / 75.7 | 0.992-0.958 | 0.992-0.976 | fail |
| b: face 60, hands 55, legs 50, dress ~90 % | 83 / 81 / 79 % | 8,252 / 8,052 / 7,854 | 3.42 / 28.3, 4.44 / 28.3, 5.60 / 28.3 | 0.999-0.993 | 0.997-0.994 | fail (legs) |
| c: face 55, hair 80, hands 50, legs 75 | 79 / 78 / 77 / 76 % | 7,856 ... 7,556 | 3.21 / 18.6 (79), then max 25.95 | 0.996-0.992 | 0.996-0.994 | 79 passes; hands: thumb and fist blocky |
| d: c with hair kept | 81 / 80 / 79 % | 8,054 / 7,954 / 7,856 | 3.11 / 18.6 (81), then max 25.95 | 0.996-0.994 | 0.996-0.995 | 81 passes |
| e: face 60, hair 80, fingers 75, palms 55, legs kept | 82 ... 78 % | 8,152 ... 7,754 | max 25.95 from 82 | 0.995-0.990 | 0.995-0.991 | fail |
| f: e + error lock | 82 / 81 / 80 / 79 % | 8,152 ... 7,854 | 3.51 / 18.5 (82) | 0.994-0.991 | 0.995-0.991 | 82 passes |
| g: f with face 50, hair 75 | 81 / 80 / 79 / 78 % | 8,054 ... 7,754 | 3.84 / 18.5 (79) | 0.996-0.993 | 0.996-0.993 | 79 passes; dark specks in the back hair, left thumb pointed |
| h: f with hair and all fingers kept, face 60 | 84 ... 81 % | 8,352 ... 8,054 | 4.81 / 27.5 at 84 | 0.993-0.987 | 0.993-0.988 | fail: everything left falls on the dress |
| i: face 50, hair 80, right fingers kept, left 80, palms 55 | 82 / 81 / 80 / 79 % | 8,154 ... 7,856 | 3.63 / 18.5 (81) | 0.995-0.993 | 0.996-0.993 | 81 passes; left thumb still pointed |
| **j: face 50, hair 80, all fingers kept, palms 60** | **82 %** | **8,154** | **3.62 / 18.5** | **0.994** | **0.995** | **picked** |
| j | 83 / 81 % | 8,254 / 8,056 | 2.93 / 18.5, 4.42 / 27.5 | 0.994 / 0.993 | 0.996 / 0.994 | 83 passes, 81 fails |

- **The dress is the floor.** `group_error.py`: at a uniform cut of the rest to
  70 % its p99 is 9.6 mm (sleeves 7.6, bodice 5.2, upper and lower skirt 10.9 / 10.2); it was already cut to 61 % in
  production and its 16 cm2 triangles lose the folds and layers at any further cut. It holds the limits only at about
  83 % with the error-lock patches, so the dress, bodice and sleeves carry only a small part of the cut, not most of it
  as planned. The face (p99 1.2-1.5 mm at 50-70 %), the hair at 80 % and the palms carry it.
- **Hidden legs are kept.** At 50-75 % they carried p99 6.7-13.6 mm (they were already cut to 37 %), and the saving was
  100-200 triangles. Kept exactly, they deform exactly as installed.
- **Hands:** at 50 % the free hand's thumb became a spike and the dagger fist went blocky (`review/close/sheet_c_body.png`);
  at 75-80 % the thumb tip was still pointed (`sheet_g_hands.png`, `sheet_i_hands.png`). With every finger face kept
  and palms/forearms at 60 % the fist, the grip and the free hand match (`sheet_before_after.png`).
- **Hair:** 75 % showed dark specks on the back of the head (`sheet_g_head.png`); 80 % matches.
- **Face at 50 %:** textured, eyes, lips, nose and ears match the source in every view; in clay the lips and nostrils
  are slightly softer (`sheet_i_head.png`).
- **Texture checks (r82):** `texture_drift.py`: 2 faces over 40 (7.4 cm2, hem side). `dark_slivers.py`: 74 faces with
  2+ of 48 darker samples, 11 with 8+; close-ups at the eight worst spots (`review/close/sheet_j_slivers.png`) render
  the same as the source.
- **Dress in motion** (`review/close/sheet_j_motion.png`, `sheet_j_motion_clay.png`): Running frames 3/9/15 from behind
  and the side, the front split in Running 3/15 and Walking 6, the Death fall at 16/24 and Dead from above and the side
  match the source.
- **Leg poke-through** (`leg_poke.py`, every 2nd frame of every clip, four views, `work/leg_poke_Cand_82.json`):
  visible hidden-leg pixels 2,182 against the source's 2,164 (shoes under the hem and the falling poses); no view is
  worse by more than 5 px.

## Build

`export_cand.py` (`REA_CAND=Cand_82 REA_NODE=M428`, `work/ladder_j.blend`) -> `swap_lod0.py
work/mm8_m428_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M428` -> `blender -b --factory-startup -P
build_lods.py` (the creature's own `build_actor_lods` defaults 0.5 / 0.18 / 0.06, 4 influences; protected points:
LOD0 vertices within 1 cm of the floor in any Death/Dead frame and the top 5 mm of the crown, 110 points) ->
`../mm8_m428_claude/scripts/shrink_shadow_lods.py work/pick_lods.glb export/mm8_m428.glb` (production shadow shrink)
-> `carry_variants.py export/mm8_m428.glb` (7 LOD/shadow primitives): `export/mm8_m428.glb`, 6.8 MB (installed 7.1 MB).
Plain smooth normals, as the installed source shades.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 9,946 | 4,972 | 1,786 | 595 |
| reduced | **8,154** | 4,077 | 1,466 | 487 |

## Checks

- **`lod_check.py`** (REA_NODE=M428; `work/lod_check_{src,r82}.json`): every reduced LOD keeps the 1.7003 m height
  (installed LOD3 1.6936, LOD2 1.7017). No face stretches over 20x in any frame of any clip at any LOD (none installed
  either). Lowest point per clip: LOD0/1 as installed (Death -62.9 mm, Dead -62.7, Running -24.5, Walking -1.0, the rest
  0.0); LOD2/3 Running -6.5 mm (installed -20.5 / -17.9) and Standing/Fidget/Hit 0.0 (installed LOD3 floated 16 mm). The
  Death/Dead dip below the floor (-63 mm) and Running (-25 mm) are in the installed LOD0 too (the clip, not the
  reduction). LOD3 width 0.779 m against 0.827 (installed LOD3 0.807): the A-pose fingertips are 2.4 cm shorter per side.
- **Arm and hand gate** (production `g4_weights.py` and `g5_hand_stretch.py` on `gate_blend.py` blends of the GLBs,
  every 2nd frame of every clip; `work/g4_{src,r82}.log`, `work/g5_*.log`, `work/g4_gate_*.json`): arm stretch p99 at
  most **1.96** (source 1.96; per clip 1.54-1.96 against 1.55-1.96), max 3.44 as the source. Hand edges at most 1.68x
  (source 1.74x).
- **`check_winding.py`:** 0 inverted closed parts.
- **Unchanged:** clips, skeleton, `Dagger` bone, images, region mask and ramps, the three variants on all colour and
  shadow meshes.

## Install and regressions

- `python3 tools/install_model.py level_generation/creatures/mm8_m428_reduce_claude/export/mm8_m428.glb --world mm8`
  (source sha256 `7eb675ad...cfb5`; the cooked runtime copy was rewritten).
- The regression `mm8_dark_elf_female_peasant_actor_models_keep_native_roles` checks three reduced LODs and the dagger
  bone, not triangle counts, so `HeadlessOutdoorDiagnostics.cpp` needed no change; `cmake --build build --target
  openyamm -j25` was up to date.
- `OPENYAMM_REGRESSION_FILTER=mm8_dark_elf_female ./build/game/openyamm --headless-run-regression-suite actors`: 1
  passed (`review/regressions/female.log`); `OPENYAMM_REGRESSION_FILTER=mm8_ ...`: **56 passed, 0 failed**
  (`review/regressions/mm8_actors.log`).
- In game (`./tools/run_game.sh --isolated m428-reduce-out`, `out01.odm`, the production camera and tour
  `review/ingame/out_models.yml`, debug.actor_models): all three tiers spawn with the dagger, hit, dying and dead
  (`review/ingame/out_models/`); `review/ingame/compare_installed_reduced.png` puts the production run's shots beside
  them (installed left). 108 outdoor actors, none missing.

## Viewers

- Reduction viewer `review/viewer/` (installed r100 vs r82 for each tier, ramps baked by `viewer_variants.py`, native
  anchors from the production manifest):
  <http://127.0.0.1:8912/level_generation/creatures/mm8_m428_reduce_claude/review/viewer/>. `check_viewer.mjs ... 60`:
  42 switches, no console errors.
- Production viewer `../mm8_m428_claude/review/viewer/` now shows the reduced LOD0. Its `viewer_tiers.py` bakes the
  pre-merge body texture into `export/mm8_m428_runtime_lod0.glb` (separate body and head materials), which a merged-atlas
  file cannot feed, so the tier GLBs were written by this project's `viewer_variants.py` from the reduced
  `work/pick_lod0.glb` (`VIEWER_OUT=../mm8_m428_claude/review/viewer viewer_variants.py work/pick_lod0.glb ""`) and
  the production `viewer_manifest.py` ran unchanged (it reads only clip lengths from the runtime LOD0, which are the
  same). The production export was not changed. The previous viewer files are in `work/prod_viewer_pre_reduce/`.
  `check_viewer.mjs`: 21 switches, no console errors.

## Known deviations

- The cut is 82 %, not the ~70 % of the male: the dress, already cut to 61 % in production, fails the limits below
  about 83 % of its own faces, so it carries little of the cut; the face, hair and palms carry it.
- The hidden legs are not reduced (see above).
- In clay the face's lips and nostrils are slightly softer at 50 %; textured they read the same.
- LOD3 fingertips are about 2.4 cm shorter per side.
- Death/Dead dip about 6 cm below the floor at every LOD, as installed.

## Rollback and reproduction

Rollback: `python3 tools/install_model.py level_generation/creatures/mm8_m428_reduce_claude/work/mm8_m428_source_pre_reduce.glb
--world mm8 --name mm8_m428.glb`, and copy `work/prod_viewer_pre_reduce/*` back into the production viewer.

Reproduce (from this folder): `REA_NODE=M428 REA_GLB=level_generation/creatures/mm8_m428_reduce_claude/work/mm8_m428_source_pre_reduce.glb
blender -b -P scripts/import_source.py` -> `dump_mesh.py`, `dump_faces.py`, `dump_vweights.py` -> `python3
scripts/make_groups.py` (keep_a) and `REA_CUT_HAIR=1 make_groups.py` (keep_c); groups_e = groups with the
non-finger faces of labels 3/4 as 6; keep_e = keep_c + label 5 -> `REA_KEEP_FACES=work/keep_e.npy
REA_GROUPS=work/groups_e.npy REA_GROUP_RATIOS=1:0.6,2:0.8,3:0.75,4:0.75,6:0.55 run_ladder.sh e 0.82,0.80,0.79,0.78` ->
`REA_CAND=Cand_80 REA_ERR_MM=14 REA_LOCK_R=0.02 err_lock.py -- work/keep_e.npy work/keep_f.npy` (on ladder_e) ->
keep_j = keep_f + labels 3 and 4 of groups_e -> `REA_KEEP_FACES=work/keep_j.npy REA_GROUPS=work/groups_e.npy
REA_GROUP_RATIOS=1:0.5,2:0.8,6:0.6 run_ladder.sh j 0.83,0.82,0.81` -> checks (`close_human.py`, `close_sheet.py`,
`texture_drift.py r82`, `dark_slivers.py r82`, `point_close.py`, `leg_poke.py`) -> build as above -> `lod_check.py`,
`gate_blend.py` + production `g4_weights.py` / `g5_hand_stretch.py` -> `viewer_variants.py` (r100, r82) +
`viewer_manifest.py r82 9946 8154`.

## Rebuilt with new carry clips (2026-10-19)

The production project changed the dagger-arm carry (Standing, Walking, Running and the blends of Hit, Death, Fidget;
`../mm8_m428_claude/README.md`, "Dagger arm beside the body"). The same reduced geometry (`work/cand_export.glb`) was
swapped into the new production export by `../mm8_m428_claude/scripts/build_reduced.py` (swap_lod0 -> build_lods ->
shrink_shadow_lods -> carry_variants, as in Build); LOD counts unchanged. check_winding 0, installed, focused
regression and MM8 actors 56/56 pass, viewer tiers rewritten from `work/pick_lod0.glb`. `work/mm8_m428_source_pre_reduce.glb`
stays the rollback to the unreduced model with the previous carry.

## Floor fix — 2026-10-21

`--lift-joints Death Dead --ground-death Death Dead`: the skirt strips Dress_08..11 went up to 0.063 m under the floor in the corpse and late Death; each strip now bends at its top joint (at most 9 degrees) so it lies on the floor. Death ends in the Dead pose (0.06 world units). Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m428.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.

## Gait rollout (2026-10-31, package h18)

New in-place locomotion clips appended to the installed source (every existing clip, mesh, skin and material
byte-identical): `Walk2` (Relax-Walk-Forward, 1.05 s, stride 1.2143, dress simulated with a numpy port of `dress_sim.py`: her 1.18 u/s wandering played `Walking` at x0.61; `Walking` stays her run, walk-as-run at Froude 0.61). Arms, hands and props come from this model's own fitted clips. Built, gated and installed in
[../gait_rollout_20261031/h18/](../gait_rollout_20261031/h18/README.md); bindings for the coordinator in its
`bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h18/scripts/rebuild.sh m428`; rollback:
install `../gait_rollout_20261031/h18/work/mm8_m428_pre_gait.glb`. A far-LOD repair, head-bob, floor-fix or reduction
rerun on this model must re-graft these clips (copy the new source over the pre-gait copy and rebuild).
