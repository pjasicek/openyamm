# MM8 Dark Dwarf (`m632`, Dark Dwarf A/B/C) reduction (2026-10-19)

User: "Pick these for next reduction batch" (MM8 batch 2 of openyamm-f6: m556, m632, m488, m608, m496). Default route
of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed rebuilding, so the
installed textures, three palette variants (`KHR_materials_variants`) and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m632.glb`, byte-identical to
`../mm8_m632_claude/export/mm8_m632.glb` (attack revision `m632_v5_fast_aim`; the `assets_dev` runtime copy was cooked
from it on 2026-10-18 16:33, eight clips), copied to `work/mm8_m632_source_pre_reduce.glb` (rollback source). One
material per tier (`Dwarf_A/B/C`, merged 2080x1024 head/body atlas, head set u > 0.5), node `DarkDwarf`, 59 bones,
**8 influences** (the creature's README: limiting to 4 moved late-death skin by 16 mm), so the ladder, export and LODs
all keep 8 (`REA_INFLUENCES=8`). The crossbow (`mm8_m632_crossbow.glb`, 556 triangles) is unchanged and not part of
this build. Scripts start from `../mm8_m412_reduce_claude/scripts/` (the m624 parent-before-transform fix, per-region
helpers); the viewer is the creature's own eight-influence `review.js`.

## Regions and keep sets (`m632_groups.py`, `patch_keep.py`, `drift_lock.py`)

Weld 6,825 -> 955 open edges; 2 coincident vertices with other weights (no split seam). The body is 70 separate
pieces; the main skin piece (2,299 faces) is closed at the head (its only open loops are at the waist, under the belt
and cuirass), so there is no scalp opening under the helmet (the pirate's temple hole cannot happen here).

| label | faces | ratio (pick) |
|---|---:|---|
| 1 face and neck skin (head-set faces of the main piece) | 1,299 | 60 % |
| 2 beard (front piece and two side strands) | 798 | 65 % |
| 3 helmet dome | 300 | 85 % |
| 4 helmet horns | 448 | 35 % (curve points protected in the LODs) |
| 5 braid and rear hair | 888 | 78 % |
| 6 spiked pauldrons, 7 upper-arm sleeves, 8 trousers/mail skirt, 9 boots | 440 / 360 / 758 / 438 | 94.5 / 88.5 / 94.5 / 94.5 % |
| 10 arm skin, 11 torso skin (main piece) | 419 / 581 | 94.5 % |
| 0 rest (cuirass plate) | 199 | free |

Kept exactly (`work/keep_lock.npy`, 3,417 faces): both hands and fingers (1,086; the crossbow's trigger and support
grips are fitted to them), small pieces of up to 100 faces (1,604: eyes, pauldron spikes, studs, buckle, bracer
rings, belt pieces), the soles (193, faces below 6 cm), 4 cm patches (mirrored) around the right knee front and four
torso/back-of-neck points that failed every step (`rest_points.py`), and one drift-lock round (254 faces, from e r81).

**The body was already lean.** Per-region error of the first ladders (`region_error.py`, source vertex -> candidate
surface over every third frame): at 85 % the pauldrons, boots, sleeves, trousers, arm and torso skin already had
p95 5-7 mm (limit p99 4.2 mm), while the face (p95 1.1 mm), horns (2.3 mm) and beard (2.7 mm) had slack. The cut
therefore sits almost entirely in the face, horns, beard, hair and helmet.

## Ladder (limits for the 1.401 m height: p99 4.20 mm, max 21.0 mm)

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 9,579 | | | |
| a: hands, small, soles kept; face 75, beard 70, helmet 60, horns 70, hair 70, rest free | 80 % | 7,659 | 6.92 / 29.1 | 0.993 | fail: the free rest starves (arm skin) |
| b: + every region its own ratio (rest 85-90 %) | 85 % | 7,977 | 4.11 / 22.0 | 0.996 | fail (knee-front point) |
| c: + knee patches, arm/torso skin groups | 84 % | 8,139 | 4.55 / 25.6 | 0.996 | fail (back-of-neck points) |
| d: + torso patches | 85 % | 8,215 | 4.11 / 17.2 | 0.996 | pass, body regions over p95 |
| e: face 50, beard 60, horns 50, body regions 95 % | 81 % | 7,859 | 3.49 / 16.4 | 0.997 | pass |
| f: same, stronger | 79 % | 7,631 | 3.93 / 16.4 | 0.997 | pass; face 35 % |
| g = e + one drift lock | 82 % | 7,981 | 3.57 / 16.4 | 0.997 | pass; mouth creases at face 42.5 % |
| h: face 60, beard 70, horns 42.5 | 86 % | 8,301 | 3.32 / 16.4 | 0.997 | pass |
| **i: face 60, beard 65, horns 35, hair 78, helmet 85** | **85 %** | **8,183** | 3.55 / 16.4 | 0.997 | **pick** (SSIM 0.989) |

Face close-ups (`review/close/sheet_face.png`: h86 / g82; `sheet_hi.png`: source / h86 / i85) decided the face
ratio: at 42.5 % creases appeared around the mouth and cheeks; at 60 % the face matches. Horns at 35 % keep their
curve at full detail. Texture drift at the pick (`texture_drift.py r85`): 4 faces over 40 (12.9 cm2, each under
3 cm2 except one 48 cm2 face on the cuirass at a colour difference of 22), not visible. Normals are plain smooth (no
`REA_NORMALS=transfer`); judge shading from `review/glbclose/` (straight from the GLBs), not from `review/close/`
(welded `source.blend`, scrambled custom normals).

## Build

`export_cand.py` (Cand_85 of `work/ladder_i.blend`, 8 influences) -> `swap_lod0.py` (`work/i85_lod0.glb`) ->
`horn_points.py r85`, `floor_points.py` -> **`build_export.sh`**: `build_lods.py` (the creature's builder settings:
0.5 / 0.25 / 0.125, 8 influences, horn tips and sole ends protected, plus 24 horn curve points (reduced LOD3 horns
otherwise came out straight) and 24 Dead/Death floor contacts (reduced LOD3 corpse otherwise lay 2 cm above the
floor)) -> `clamp_lod_uv.py` (the same 0.0014 LOD1 UV overshoot the creature build clamps) -> `compact_glb.py` ->
`carry_variants.py` (variants on all 7 LOD/shadow primitives) -> `smooth_walk_bob.py` (sigma 5) -> `fix_clips.py`
(source-animation fixes below) -> `check_winding.py` (0 inverted closed parts): `export/mm8_m632.glb`, 8.6 MB
(installed 8.8 MB), 8 clips.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 9,579 | 4,787 | 2,365 | 1,169 |
| reduced | 8,183 | 4,089 | 2,018 | 993 |

`work/lod_check_{src,r85fix}.json`: every LOD keeps the 1.40 m height; no face stretches over 20x in any frame of
any clip (installed LOD3: one face in Death/Dead); all LODs within 2.7 mm of the floor in every clip (Death now
-1.5 mm at LOD0, was -14.6 mm; Dead within 1 mm at every LOD). `review/lods/sheet.png`: installed / reduced per LOD,
standing, aim and helmet close-up (horn curves kept at LOD3).

Checks not applicable: the creature has no shared gate config (`gates.json`); its own arm, finger and grip checks
depend on the hands, which are kept exactly (geometry), and the animation fixes keep both hands' world poses on the
crossbow (left hand 0.0 mm in Walking; Hit retimes body and crossbow together; Attack and Death change no arm).

**Re-export note:** the source-animation fixes live only in this export. A re-export from `../mm8_m632_claude/`
(its master still has the old Walking, Attack end, Hit and Death) or a new `swap_lod0.py` brings the pops back unless
`scripts/build_export.sh` (which runs `smooth_walk_bob.py` and `fix_clips.py`) is run again.

## Review

- GLB close-ups, installed / reduced (crossbow attached): `review/glbclose/sheet_head.png` (face, helmet, horns,
  braid), `sheet_body.png` (both crossbow hands, arm, torso, belt, back, boots), `sheet_poses.png` (aim, aim arms,
  run, death), `sheet_magenta.png` (magenta background: no see-through gaps in either).
- Viewer: `review/viewer/` (installed vs 85 % with the animation fixes, three palettes, crossbow attached and animated
  on both, eight-influence skinning; manifest sha256 and `?v=` updated). `python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m632_reduce_claude
  check`: 48 switches, no console errors.

## Source-animation fixes (round 2, coordinator request; `smooth_walk_bob.py`, `fix_clips.py`)

Found by `clip_scan.py` and `bone_velocity.py` (viewer frame = time x 48). Only the listed channels change; Dead,
Fidget, Running and Standing are byte-identical, and so is every other channel of the fixed clips (checked).
- **Walking bob** (`smooth_walk_bob.py`, sigma 5 on the 120 Hz keys): the pelvis dipped 0.7 cm at frames 3-4 while
  rising, the half-cycles peaked at 77.4 and 78.9 cm and it dropped 1.9 cm/frame at frames 32-33. Now two even bobs,
  pelvis 74.1-77.5 cm (range 3.4 cm, was 5.9 cm across all keys), largest step 0.82 cm/frame (was 1.87). Ankles and
  foot rotations unchanged (0.000 mm). Sigma 7 flattened it to 2.5 cm.
- **Walking left elbow** (frames 5, 14, 24, 39): the elbow swivelled about 4 degrees within one key pair (B_L_UpperArm
  4.4 degrees/key, neighbours 0.4-0.8; elbow 15-33 mm/frame) while the hand stayed on the grip. B_L_UpperArm smoothed
  around each spike, turned back about the shoulder so the wrist path is exact, B_L_Hand re-solved (hand world pose
  error 0.0 mm). Largest step now 0.78 degrees/key, elbow travel at most 12 mm/frame.
- **Attack end** (frame 74): both knees swivelled 2 cm into the loop-out pose in the last two keys (thigh/calf/foot
  3-5 degrees/key, feet still). The knee plane now eases into the final plane over the last 0.15 s (two-bone IK on
  thighs, calves and feet; ankles and foot rotations unchanged, the last key exact; knee at most 4 mm/key).
- **Hit recovery** (frame 24): the motion stopped dead at 0.5 s. Everything after 0.35 s is retimed with a Hermite
  curve that reaches the same final pose at 0.6 s with zero velocity (all animated channels, crossbow included).
  Largest head step 0.67 cm/frame (was 1.29 into the stop).
- **Death floor** (frame 36): the right foot went 1.46 cm under the floor between keys while the body falls. B_Pelvis
  is lifted by a short Gaussian (1.5 cm, sigma 30 ms, around 0.758 s); lowest point now -0.34 cm (viewer frames).
- **Left as is**: the crossbow stock passes through the beard strands at full draw (Attack aim; the installed model
  has it too).

Review: `review/walk/walk_bob_plot.png` (head/pelvis height and left elbow travel per frame, installed grey / fixed
blue), `review/walk/filmstrip_attack_hit.png` (side view, Attack frames 66-74 and Hit 18-29, before / after).

## Status

Installed 2026-10-19 after user review ("dark dwarf ok"), with the clip fixes, via `tools/install_model.py --world mm8`; crossbow unchanged; actor regression `mm8_dark_dwarf_actor_models_keep_tiers_crossbow_and_native_roles` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install (from the repository root): `python3 tools/install_model.py --world mm8
level_generation/creatures/mm8_m632_reduce_claude/export/mm8_m632.glb`, then
`OPENYAMM_REGRESSION_FILTER=mm8_dark_dwarf_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_dark_dwarf_actor_models_keep_tiers_crossbow_and_native_roles`) and add the ledger row.
Rollback: `python3 tools/install_model.py --world mm8
level_generation/creatures/mm8_m632_reduce_claude/work/mm8_m632_source_pre_reduce.glb`.

Reproduce: `REA_GLB=<abs path of the rollback source> REA_NODE=DarkDwarf blender -b -P scripts/import_source.py` ->
`dump_mesh.py`, `dump_groups.py`, `dump_faces.py` -> `m632_groups.py` -> `patch_keep.py work/keep_base.npy
work/keep_p.npy -0.1555,-0.1711,0.3805 -0.1102,-0.1522,0.3816 -0.0356,-0.0572,0.4369` -> `patch_keep.py work/keep_p.npy
work/keep_p2.npy 0.0881,0.1362,1.0192 0.0777,0.1814,0.9278 0.1625,-0.0523,1.0053 -0.1144,0.1023,0.6181
-0.135,0.0966,1.0381` -> `group_ladder.sh e work/keep_p2.npy "<e ratios>" 0.8,1.0,1.15` -> `texture_drift.py r81`
(`work/basecolor.png` from the GLB) -> `drift_lock.py work/keep_p2.npy work/keep_lock.npy r81` ->
`group_ladder.sh i work/keep_lock.npy "1:0.6,2:0.65,3:0.85,4:0.35,5:0.78,6:0.945,7:0.885,8:0.945,9:0.945,10:0.945,11:0.945" 1.0`
-> `close_ladder.py`, `close_sheet.py`, `region_error.py`, `texture_drift.py r85` -> build as above (`build_export.sh`) ->
`lod_check.py` (REA_NODE=DarkDwarf), `lod_views.py`, `viewer_variants.py <glb> <tag> <crossbow.glb>:Crossbow`,
`viewer_manifest.py`, `glb_close.py`, `glb_sheet.py`, `clip_scan.py`, `bone_velocity.py`, `plot_walk.py
work/mm8_m632_r85_pre_clipfix.glb export/mm8_m632.glb`, `filmstrip.py` + `film_sheet.py`.

## Head bob (2026-10-22)

The installed source of `mm8_m632` now carries walk/run clips reshaped by [head_bob_claude](../head_bob_claude/README.md)
(`bob_fix.py`: pelvis bob rescaled or evened, legs solved to the original foot paths). `export/` holds the pre-bob GLB:
after a rebuild here, rerun `head_bob_claude/run_jobs.py --only mm8_m632` on the new export (copy it to
`head_bob_claude/work/mm8/` first) before installing.


## Gait rollout (2026-10-31)

Package [h21](../gait_rollout_20261031/h21/README.md) appended new in-place locomotion clips to the installed source
`assets_source/worlds/mm8/models/mm8_m632.glb` (existing clips, meshes, skins and materials byte-identical): `Walk2` (2Hand-Crossbow-Walk, 0.76 s, stride 1.4009) bound as walking and `Sprint` (Unarmed-Sprint, 0.53 s, 3.1509) for MAW's chase; `Running` stays the run.
Bindings are in `../gait_rollout_20261031/h21/bindings.yml` (applied by the rollout coordinator). Rebuild:
`level_generation/creatures/gait_rollout_20261031/h21/scripts/rebuild.sh m632` (from `h21/work/mm8_m632_pre_gait.glb`,
the pre-gait source), then `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h21/export/mm8_m632.glb --world mm8 --name mm8_m632.glb`. A far-LOD repair,
head-bob or reduction rerun on this model must re-graft these clips: copy its new source over the pre-gait copy and
rerun the rebuild (or graft them with `claude_shared/graft_clips.py`).
