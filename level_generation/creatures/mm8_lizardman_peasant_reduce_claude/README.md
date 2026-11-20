# MM8 Lizardman Peasant (`mm8_lizardman_peasant`, Peasant A) reduction (2026-10-18)

User: "pick 5 more to do" (MM8 triangle-reduction batch 2, coordinated with sessions openyamm-f9, openyamm-f6 and
openyamm-b4). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part
needed rebuilding, so the installed textures, the `m400_a` variant and its region ramp stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_lizardman_peasant.glb`, byte-identical to the delivery of
`../mm8_m400/3d_20261006/claude_20261015/` (`delivery/delivery.json` hash); the runtime copy has the same six clips
(not stale). It is copied to `work/mm8_lizardman_peasant_source_pre_reduce.glb` (rollback source). One merged
body + head atlas material (`Lizardman_A`, 2080x1024), one `Lizardman_Body` node, 40 bones, eight influences.
Scripts are copied from `../mm8_m624_reduce_claude/scripts/` (fixed parenting order in `reduce_ladder.py`).

Weld 15,561 -> 288 open edges (unchanged by every step); no coincident vertices with other weights, no two-sided
sheets, one connected piece (plus a 17-face piece kept exactly). Limits for the 1.70 m height: p99 5.10 mm,
max 25.5 mm. `run_ladder.sh` takes `REA_INFLUENCES` (default 8 here) and `REA_HEIGHT_M` (default 1.70).

## Why only 25 %

The creature's own build already reduced the body once (head, hands, feet and apron were protected), and its body
atlas is split into hundreds of small islands, so most vertices sit on texture seams. A uniform cut fails at 70 %.
`scripts/region_error.py` (per-vertex error over every clip, by dominant bone) put the maximum on the jagged ivory
fringes: calves (z 0.22-0.36 m), below the arm bands (z 1.26-1.30 m) and the neck collar. They are spikes of the one
welded surface, and every collapse rounds their points (28.8 mm at the right calf already at rest).

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 10,995 | | | |
| uniform | 80 % | 8,795 | 4.08 / 18.14 | 0.992 | pass |
| uniform | 75 % | 8,245 | 4.84 / 28.76 | 0.989 | fail (max, calf fringe) |
| uniform | 70 % | 7,695 | 5.58 / 28.76 | 0.985 | fail |
| hands kept | 75 % | 8,245 | 5.44 / 28.76 | 0.988 | fail: the rest absorbs the cut |
| fringes + hands kept, head 80 % | 70 % | 7,695 | 7.45 / 24.75 | 0.982 | fail; 60 % collapses (p99 18.7) |
| **fringes kept** | **75 %** | **8,245** | 4.60 / 16.48 | 0.989 | **pick** (lowest passing step) |
| fringes kept | 70 % | 7,695 | 5.42 / 16.48 | 0.986 | fail (p99) |

Keep set (`fringe_keep.py`, 1,616 faces): ivory faces (`color_class.py`, base-colour class per face) at the calves,
below the arm bands and at the neck, plus the small piece. Head and hands are in the shared cut: protecting either
pushed the body past the limits, and at 75 % the snout, teeth, fins and four-digit hands render unchanged.
Texture drift (`texture_drift.py r75`): 7 faces over 40, 21.5 cm2 in all; no drift lock.

Close-ups straight from the GLBs (`glb_close.py`, own normals; installed / reduced, textured then clay):
`review/glbclose/sheet_src_r75.png`. Textured views match. The installed GLB carries custom normals with hard
creases (`sharp_face`); the reduced mesh is smooth-shaded, which shows in clay only.
Never `REA_NORMALS=transfer` (the welded `source.blend` scrambles custom normals).

## Build and LODs

`export_cand.py` (Cand_75, 8 influences) -> `swap_lod0.py` -> `build_lods.py` -> the creature's
`shrink_shadow_lods.py` -> `carry_variants.py` -> `keep_far_lods.py`: `export/mm8_lizardman_peasant.glb`, 10.1 MB
(installed 10.9 MB), six clips byte-identical, `m400_a` variant on all 8 colour/shadow meshes, 0 inverted closed parts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,995 | 5,495 | 2,744 | 2,417 |
| reduced | 8,245 | 4,120 | 2,744 (installed) | 2,417 (installed) |

- The creature's ratios are 0.5 / 0.25 / 0.125, but Blender's collapse stalls at about 2,360 triangles on this atlas
  (the installed LOD3 stalled at 2,417 for the same reason). Rebuilt LOD2/3 came out at 2,716 / 2,450, no lighter
  than installed, and looked worse: LOD3 lost 5.5 cm of height (head fin tips, 1.644 m); with the fin tips protected
  the collapsed fins became one wide sheet over the head. `keep_far_lods.py` keeps the installed LOD2/3 and their
  shadows (same skin, joints and material) and compacts the buffer.
- LOD1 is rebuilt at 0.5 with the 44 fin-tip vertices (above 1.64 m) as protected contacts.

`work/lod_check_{src,r75}.json`: every LOD keeps the 1.70 m height; no face stretches over 20x in any frame of any
clip; lowest point -2.2 mm at LOD0 and -3.9 mm at LOD1 (installed -0.4 / -2.1 mm; LOD2/3 unchanged, -24.1 / -8.3 mm).
`review/lods/sheet.png`: installed / reduced, LOD0-3, three-quarter, front, Fidget hand at the snout, feet.

Viewer: `review/viewer/` (installed vs 75 %); `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_lizardman_peasant_reduce_claude check`: 12 clip switches, no console errors.

## Attack versus the native sprite

No mismatch. The native descriptor's melee and ranged attack slots both use the walking art (`m401w`), and the 3D
model binds both to Walk (`../mm8_m400/3d_20261006/claude_20261015/delivery/clips.json`). The separate `m400aa`-`ag`
poses in `../mm8_m400/trimmed_2x/` are unused by the native descriptor.

## Standing v2 (2026-10-18)

User review of the viewer: "the standing anim also like he should do something? atleast like breath", with the near
(right) arm traced: in v1 it hung with a 48-degree elbow bend close to the tunic while the left hand reached forward.
Standing is now a 4.0 s idle authored in the creature master
(`../mm8_m400/3d_20261006/claude_20261015/scripts/standing_idle.py`, after `polish_motion.py`): both arms re-posed
like the native `m400sa` frames (hanging slightly forward and out, elbows 145-153 deg, hands beside the front of the
thighs), two breaths (chest extension, clavicle lift, neck counter), one weight shift (pelvis 28 mm side to side with
roll and yaw, spine counter-roll, legs re-solved so both feet stay exactly planted: 0.0 mm foot travel), slow head
drift, a slight lagged arm swing and elbow flex. No library clip: the stored idles are upright humans, this body is
hunched (playbook: author Standing from the creature's own pose when library idles do not fit). Hit/Fidget/Death
carry the same arm correction where they ease from/to Standing (in full on bones the clip holds still, Fidget's left
arm), so no arm pops at the crossfades; their mid-clip motion is unchanged.

The reduced export is the previous one (`work/standing_v1/mm8_lizardman_peasant.glb`) with only Standing, Hit,
Fidget and Death replaced (`export_clips.py` -> `scripts/transplant_anims.py`): meshes, LODs, skins, materials,
images, nodes and the Walk/Corpse clips are byte-identical. The export route reproduced the old clips exactly
(max difference 0) before the new ones were exported.

Checks (`scripts/arm_gate.py`, `review/standing_v2/arm_gate_v{1,2}.txt`): Standing has no arm skin inside the torso
(one right claw tip 37-46 mm from the tunic shell flags on 2 frames: open-shell false positive, see
`review/standing_v2/master_clay/hands_compare.png`), clearance 26 mm right / 61 mm left, wrist swing 17/26 deg,
forearm twist 10-21 deg, lowest point 0.0 mm, loop closes exactly. Hit/Death arm penetration (49/95 and 85/73
vertices in recoil and collapse) and Walk's (53/40) are the same in v1 and unchanged. `lod_check.py` on the new
export: no stretched faces at any LOD, floor values identical to the previous export. Winding: 0 inverted.
Sheets: `review/standing_v2/sheet_old_vs_new.png` (installed static vs v2 at 0/1/2/3 s, six views),
`review/standing_v2/sheet_arms.png`. Viewer: installed (old 0.125 s Standing) vs reduced with Standing v2;
`review/viewer/review.js` accepts a per-model clip length (`clip_durations`) for that; check: 12 switches, no errors.

Install note: the actor regression `mm8_lizardman_peasant_actor_model_keeps_native_roles` expects Standing at
0.125 s (`game/outdoor/HeadlessOutdoorDiagnostics.cpp`, clip table); change it to 4.0 s with the install.

## Status

Installed 2026-10-18 after user review (reduction, then Standing v2: "lizardman peasant good") with `tools/install_model.py --world mm8 export/mm8_lizardman_peasant.glb`. The regression's expected Standing duration moved from 0.125 to 4.0 s (`game/outdoor/HeadlessOutdoorDiagnostics.cpp`).
`OPENYAMM_REGRESSION_FILTER=mm8_lizardman_peasant_actor_model ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_lizardman_peasant_actor_model_keeps_native_roles` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_lizardman_peasant_source_pre_reduce.glb` with `tools/install_model.py --world mm8` and set the regression's Standing duration back to 0.125 s.

Reproduce: `import_source.py` (REA_NODE=Lizardman_Body, REA_GLB=the rollback source) -> `REA_PROTECT=Head,headfront,head_end
dump_mesh.py`, `dump_groups.py` -> `small_pieces.py` -> `liz_sets.py` -> `color_classes.py` ->
`fringe_keep.py work/keep_small.npy work/keep_fr.npy` -> `REA_PIECE_WEIGHTS=0 REA_KEEP_FACES=work/keep_fr.npy
run_ladder.sh fr 0.80,0.75,0.70,0.65` -> `region_error.py`, `texture_drift.py r75` -> build as above ->
`REA_NODE=Lizardman_Body lod_check.py`, `lod_views.py`, `glb_close.py`, `glb_sheet.py`, `viewer_variants.py`,
`viewer_manifest.py`.
