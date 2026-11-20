# MM8 Ether Knight (`m604`, Ether Knight / Champion / Lord) reduction (2026-10-18)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) including its MM8 batch lessons; scripts copied
from `mm8_m492_reduce_claude/` (parent-transform fix, coincident-vertex handling, lod_check), the sword chain from
`mm6_natf_reduce_claude/` (kept parts, normals by angle). No Meshy credits. Not installed.

Sources: the installed `assets_source/worlds/mm8/models/mm8_m604.glb` and `mm8_m604_sword.glb`, identical to
`mm8_m604_claude/export/`; rollback copies `work/mm8_m604_source_pre_reduce.glb` and
`work/mm8_m604_sword_source_pre_reduce.glb`. No gate config in the creature project, so no shared gate run.
Shading is judged only from GLBs imported directly (`scripts/viewer_views.py`, `sword_views.py`); the welded
`source.blend` renders use `CLOSE_SMOOTH_SRC=1` (custom normals cleared) and compare geometry only. Plain smooth
normals: the installed body shades smooth.

## Body

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 11,114 | 5,553 | 2,743 | 1,350 |
| reduced | **8,332** | 4,151 | 2,048 | 1,020 |

Weld 8,486 -> 186 open edges; 6 coincident vertices with other weights (separated by `decimate_tex.py`). Limits
for the 1.87 m figure: p99 5.61 mm, max 28.05 mm. Four influences, as installed.

Regions (`scripts/face_bones.py`, `make_groups.py`):
- **Kept exactly (3,921 faces):** small pieces up to 80 faces (eyes, rivets, clasps, chain beads, belt studs), the
  right hand and fingers (fitted sword grip), the soles, the front/back tabard strips (outer cloth over a 1.5 mm
  red lining: at any cut the lining showed through), the belt band (its red studs smeared at 74 %) and the painted
  gold trims of the body piece found by base-colour hue (wavy back trims at 70 %).
- **Own budgets:** head 55 % (textured face unchanged from 70 %; clay slightly smoother at the nose), left hand
  50 %, mantle cloth 65 % (red lining blobs through the mantle at 55 %), mid-size pieces 70 % (gold knee pads,
  arm bands, back strips: in the shared cut they moved 5+ mm on the calves and upper arms in every frame).
- **Rest** (skin of thighs, shoulders and back, ~740 faces) takes the remaining budget; below ~67 % its error explodes
  (p99 13.7 mm at 75 % total with the gentler groups), which sets the floor of this model.

| run | head / lhand / cloth / mid | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| g1 (no trims/tabard/belt kept) | 70 / 50 / 70 / - | 74 % | 8,224 | 4.93 / 23.3 | 0.991 | 0.988 | lining through tabard, belt smeared |
| g3 | 65 / 50 / 65 / 80 | 80 % | 8,794 | 3.08 / 11.1 | 0.996 | 0.994 | pass |
| g4 | 55 / 50 / 55 / 70 | 74 % | 8,274 | 3.74 / 12.7 | 0.995 | 0.992 | lining through mantle |
| **g5** | **55 / 50 / 65 / 70** | **75 %** | **8,332** | **3.81 / 15.31** | **0.995** | **0.993** | **picked** |

Drift (`texture_drift.py r75`): 47 faces over 40, all large mantle faces; close-ups from every side match the source,
so no lock (one lock round, g6, kept 520 more cloth faces, raised p99 to 6.3 mm at the next step and moved the drift).
Sheets: `review/close/sheet_g1_tex.png` (the g1 faults), `sheet_g4_head.png`, `sheet_g4_body.png`,
`sheet_g5_cloth.png`.

Build: `export_cand.py` -> `swap_lod0.py` -> `build_lods.py` (the creature's ratios 0.5 / 0.25 / 0.125, 4
influences, with the vertices within 2 cm of every bounding extreme protected: unprotected, LOD3 lost 1 cm at the
crown and the back) -> `mm8_m604_claude/scripts/shrink_shadow_lods.py` -> `carry_variants.py`.
`work/lod_check_r75.json` (`REA_NODE=EtherKnight lod_check.py`): every LOD has the LOD0 bounds (height 1.849 m,
source 1.851), no face stretches in any clip; floor minimum per LOD equal to or above the source's own (the source
dips 2-7 mm in Death/Dead at its LODs).

## Sword

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 1,260 | 630 | 314 | 156 |
| reduced | **774** | 630 | 314 | 156 |

Parts: blade 756, grip 332, guard 172. `prop_parts.py sword c45 1:0.45,2:0.6` (grip kept exactly, blade 45 %, guard
60 %): max 0.013 % of the length (blade and guard were over-tessellated; 35 % rises to 0.31 %). Normals by angle at
20 degrees for every part (`PROP_NORMALS_ANGLE=20`): transferred normals smeared the faceted grip and pommel, 35
degrees made the faceted grip a smooth cylinder. LOD1-3 kept. `review/sword/sheet.png`, `sheet_normals2.png`.
The fitted grip is unchanged: grip faces and the right hand are kept exactly.

## Retexture check

- **Texture set:** one material, merged 2080x1024 atlas (body half, head half), region mask with cloth (R) and
  lining (G) channels and three tier ramps. The reduction keeps the UVs; base colour, normal and metal-roughness
  images are byte-identical to the installed ones.
- **Tiers** (`review/tiers/sheet_body.png`, `sheet_motion.png`, `sheet_clay.png`; viewer GLBs rendered from file):
  face, chest, back, belt, both hands with the sword, legs, wind-up, strike and corpse match the installed model in
  all three tiers. Head and body skin read the same grey; the neck junction sits under the mantle collar. In clay
  the kept back trims show as faint ridges; under the texture they read as the gold trims.
- **Existing fault, fixed locally:** Meshy painted cloth green on body faces under the tabard and mantle and on two
  chest-chain pieces at the collar, outside the cloth mask, so tiers B and C showed green patches beside the purple /
  red tabard and green flecks at the collar (in the installed model too). `scripts/mask_fix.py` adds the green texels
  of the cloth pieces and of the 172 faces that are over 25 % unmasked green to the cloth channel (15,859 texels; base
  colour unchanged); `swap_mask.py` replaces only that image (every other buffer view and the JSON byte-identical).
  `review/tiers/sheet_maskfix.png`. Pre-fix export: `work/mm8_m604_r75_pre_maskfix.glb`.
- **Verdict:** no Meshy retexture needed (body or head half); 0 credits.

## Viewer

`review/viewer/` (built by `scripts/viewer_build.py`): installed (the creature project's own viewer files) and
reduced for each tier, the reduced files with the tier ramps baked and the reduced sword as a rigid skinned
primitive on the `Sword` joint. `run_creature_review.py check`: 48 switches, no console errors.
http://127.0.0.1:8912/level_generation/creatures/mm8_m604_reduce_claude/review/viewer/

## Attack retime (user review, 2026-10-18)

User: "attack itself like the slash is frames 39-52 or something, while 0-39 is a wind-up ... quicker wind-up and
slightly less frantic slash". `work/tip_cur.json` (sword-tip path at 60 Hz) showed why. The source cut (Mixamo
SwordAttackR6 with an added lead) lowers the guard for 0.65 s, raises the sword in 0.15 s, holds 0.1 s, then cuts a
full arc in 0.15 s (impact mid-arc at 0.9833 s, peak 125 m/s, a few viewer frames). After that comes a second fast
backhand across the front (1.2-1.4 s, ~20 m/s), which is what reads as the slash at viewer frames 39-52 (30 fps).

Engine timing (`game/fx/WorldFxSystem.cpp`, `actors.yml` events): the clip's [0, impact] spans the native action up
to the moment the hit applies (native attack `m605a`: 8 frames x 0.125 s = 1.0 s; impact marker 0.9833 s), and the
rest plays at its own speed as follow-through. The impact time therefore stays at **0.9833 s** and the clip length at
**1.7333 s**; `actors.yml` is unchanged. The native frames (`review/native_attack.png`) give the proportions: raise
2 frames, cut 2 (contact at the low cross), follow-through and recovery 3.

`scripts/retime_attack.py` rewrites only the Attack output values, keeping the 120 Hz key times:

| phase | new (s) | from the source |
|---|---|---|
| wind-up | 0.00-0.42 | eased pose blend guard -> cock (source 0 -> 0.82; the dip to the low left is skipped); legs see round 2 |
| held cock | 0.42-0.68 | source 0.82-0.90, slow drift (round 2) |
| slash | 0.68-1.12 | source 0.90-1.05, eased; impact stays at **0.9833** (blade crossing the front) |
| overshoot | 1.12-1.25 | source 1.05-1.067: the blade hangs past the cut, low right |
| recovery | 1.25-1.733 | eased pose blend to the clip's final pose; replaces the backhand |

- The pose blends apply to the upper body only. Blending the pelvis and legs dipped the feet 4 cm under the floor,
  so they follow the source through one monotone time warp and keep its planted stance.
- The exporter shares constant output accessors between clips. Those are skipped, so every other clip is
  byte-identical, and so are the GLB JSON, the first key and the last pose (loop and idle blend unchanged).

Checks: `review/attack/tip_path.png` plots tip speed against time and the top/front/side paths, old in blue, new in
orange. Peak tip speed drops from 125 to 42 m/s, and the slash spreads over 0.44 s instead of 0.15 s.

`scripts/attack_gates.py` on the tier-A viewer GLBs, old vs new:
- no blade, forearm or hand inside the body in either clip;
- hand edge stretch R 2.25x and L 1.87x, unchanged and under 2.4x;
- mantle and tabard edge stretch 2.32x (old 2.35x);
- lowest body point -2.0 mm, at the source's slash stance, which the faster old arc stepped over at 60 Hz;
- right-finger rotations constant (0.04 deg) and the Sword joint constant relative to the hand, so the grip stays fitted.

`lod_check.py` on the new export: every LOD's lowest Attack point is -1.2 mm, with no stretched faces.

Playback sheets: `review/attack/sheet_normal.png` (every 1/12 s) and `sheet_half.png` (every 1/24 s), old above new.
The previous export is kept at `work/mm8_m604_r75_pre_attack2.glb`. The viewer shows installed / reduced with the old
attack / reduced with the new attack (`*_r75a2.glb`, the r75 viewer files passed through `retime_attack.py`) per tier,
opening on the new Attack. `run_creature_review.py check`: 72 switches, no console errors.

### Round 2: smoothed wind-up (2026-10-19)

User: "transition frames attack 13-16 too fast and abrupt, no?" The viewer counts frames at 48 fps (its frame-rate
selector), so frames 13-16 are 0.27-0.33 s. `scripts/bone_velocity.py` (per-bone local angular velocity from the GLB
keys) shows where it came from. The source legs and pelvis stand still until 0.667 s and then start a stance shift
at full speed within one key (pelvis ~975 deg/s, left thigh ~1,100 deg/s; the splice of the added lead). Round 1's
leg time warp squeezed this to 1,600-1,700 deg/s at 0.29-0.32 s, while the upper body moved smoothly.

Changes in `retime_attack.py`; the slash, impact and end pose are unchanged:
- **Legs and pelvis, wind-up:** they follow the source path by arc length (summed lower-body joint rotation; pelvis
  translation 1 cm = 1 deg) at smootherstep speed over 0-0.52 s, so the stance shift overlaps the whole upper-body
  wind-up and settles into the cocked stance (source 0.82).
- **Low-pass:** arc length smooths the summed motion, but the source switches abruptly from a slow sway to a
  thigh-only burst, so the legs are also low-passed over 0-0.62 s (Gaussian sigma 0.06 s, tapered to the window
  ends).
- **Upper body:** the wind-up ends on the settled cock pose (source 0.82, after the raise decelerates) at 0.42 s
  instead of mid-deceleration (source 0.80). The hold drifts slowly into the slash: a Hermite segment from slope 0.1
  to the slash warp's slope at 0.68 s.
- **Recovery legs:** they use the same arc-length timing (1.25-1.733 s). Peak leg bone speed drops from 786 to
  657 deg/s and frame-to-frame jerk from 1,134 to 490.
- **Floor:** averaging leg rotations dipped the feet 1.7 cm. `floor_measure.py` + `floor_lift.py` lift the pelvis
  by the measured dip (at most 16.4 mm, 64 keys around 0.2 s; the pelvis parent is an identity Rig), back to
  -0.5 mm.

Result over 0.15-0.68 s, the largest peaks:
- right upper arm 610 deg/s (the eased wind-up blend, as round 1);
- right thigh 486 deg/s at 0.63 s, the source's own step into the slash;
- left thigh 433 deg/s, against 1,682 in round 1;
- pelvis 367 deg/s, against 1,486.

Tip speed peak 42 m/s and the tip path from 0.68 to 1.12 s are identical to round 1 (0.0 mm).

Checks (`attack_gates.py`, tier-A viewer GLB, imported as is):
- no blade, forearm or hand contacts;
- hand stretch R 2.25x / L 1.87x;
- cloth 2.32x;
- lowest body point -2.0 mm at the source's slash stance (0.88 s);
- grip constant (Sword joint and finger channels).

`lod_check.py`: every LOD's lowest Attack point is -1.2 mm, with no stretched faces. Other clips, the GLB JSON, the
first key and the last pose are byte-identical or equal.

Evidence:
- `review/attack/velocity.png`: per-bone angular velocity and tip/hand speed, round 1 in blue vs round 2 in orange,
  with frames 13-16 shaded;
- `review/attack/strip_8_22.png`: viewer frames 8-22 at every frame, round 1 above, round 2 below. The stance shift
  now spreads over frames 10-17 instead of snapping between frames 13 and 15.

Round 1 export: `work/mm8_m604_r75_attack_round1.glb`; its viewer files are in `work/a2_viewer/`. The viewer shows
installed / reduced with the old attack / reduced with the round-2 attack (`*_r75a3.glb`: the r75 viewer files
through `retime_attack.py` and `floor_lift.py` with `work/floor_a3.json`). Check: 72 switches, no console errors.

### Round 3: smooth hold into the slash (2026-10-19)

User: "frames attack 29-30-31-32-... like mainly between 28-29 (like 28 ok, 29 shift to slightly different
"stance"?) is strange?" Viewer frames 28-32 are 0.58-0.67 s, the hold before the slash. Two causes
(`bone_velocity.py`):
- **Source keys:** the 120 Hz keys are a linear resampling of 30 Hz Mixamo keys, so each source key is a sudden speed
  change. The hold plays source 0.82-0.90 s about three times slower, and the 0.867 s key landed on frame 28.8: the
  spine jumped from 81 to 316 deg/s and the right upper arm from 82 to 130 deg/s within one key.
- **Legs:** the leg low-pass ended at 0.62 s, so the source's step into the slash stance came back at full speed
  (thighs 99 -> 486 deg/s at frame 30).

Changes in `retime_attack.py`:
- **Spline sampling:** the upper body samples the source through a velocity-continuous spline (modified Akima over
  the 30 Hz keys, no overshoot on still stretches) up to source 0.90 s, the slash start. That is a key, so both
  samplers meet there. The slash and recovery keep glTF lerp.
- **Legs:** they stay on lerp (a spline floated both feet 1 cm in the slash step). Their low-pass window now runs to
  0.76 s, through the hold.
- **Upper-body low-pass:** sigma 0.03 s over 0.36-0.74 s, tapered at both ends.
- **Floor:** re-measured to 0.80 s (`work/floor_a4.json`); the pelvis lift is still at most 16.4 mm.

Results over viewer frames 19-40:
- the worst frame-to-frame bone speed change drops from 523 to 191 deg/s;
- thighs peak 178 deg/s in the hold, against 486;
- the spine ramps 116 -> 188 -> 271 -> 334 deg/s, where round 2 jumped from 81 to 316.

The sword-tip path from 0.76 s on is identical to round 2 (max 0.4 mm, 0.0 mm at the 0.9833 s impact), with the same
peak of 42 m/s. Gates (`attack_gates.py`, tier A) match round 2:
- no contacts;
- hand stretch R 2.25x / L 1.87x;
- cloth 2.32x;
- lowest body point -2.0 mm at 0.88 s.

`lod_check.py`: Attack minimum -1.2 mm on every LOD, no stretched faces. `review/attack/strip_22_36.png` shows viewer
frames 22-36, round 2 above round 3. The round 2 export is kept at `work/mm8_m604_r75_attack_round2.glb` and its viewer
files at `work/a3_viewer/`. The viewer shows installed / round 2 (`*_r75a3.glb`) / round 3 (`*_r75a4.glb`, the r75
viewer files through `retime_attack.py` and `floor_lift.py` with `work/floor_a4.json`), opening on round 3.
Check: 72 switches, no console errors. `check_winding.py`: 0 inverted closed parts.

## Status

Installed 2026-10-19 (user: "OK good", after attack round 3). `check_winding.py`: 0 inverted closed parts (body and
sword). Installed both with `tools/install_model.py ... --world mm8`;
`OPENYAMM_REGRESSION_FILTER=mm8_ether_knight ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_ether_knight_actor_models_keep_tiers_sword_and_simulation` passes (`review/regression.log`). Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m604_source_pre_reduce.glb` and
`work/mm8_m604_sword_source_pre_reduce.glb` the same way. No in-game captures were taken.

Reproduce: `import_source.py` (REA_NODE=EtherKnight) -> `dump_mesh.py` -> `face_bones.py` -> `make_groups.py` ->
`REA_KEEP_FACES=work/keep.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.55,2:0.5,3:0.65,4:0.7 run_ladder.sh g5
0.765,0.75` -> build as above -> `mask_fix.py`, `swap_mask.py` -> `retime_attack.py` -> `floor_measure.py` (T 0.80) + `floor_lift.py`; sword: `prop_dump.py -- sword`, `prop_parts.py`,
`PROP_NORMALS_ANGLE=20 prop_build.py -- sword:c45` (from a copy of the npz without `nkept`), `prop_swap_glb.py`.

## Gait rollout (2026-10-31, package h18)

New in-place locomotion clips appended to the installed source (every existing clip, mesh, skin and material
byte-identical): `Walk2` (Relax-Walk-Forward, 1.00 s, stride 1.6253), `Jog` (Unarmed-Run-Forward, 0.73 s, 2.3136) and `Sprint` (Unarmed-Sprint, 0.62 s, 3.5859). Arms, hands and props come from this model's own fitted clips. Built, gated and installed in
[../gait_rollout_20261031/h18/](../gait_rollout_20261031/h18/README.md); bindings for the coordinator in its
`bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h18/scripts/rebuild.sh m604`; rollback:
install `../gait_rollout_20261031/h18/work/mm8_m604_pre_gait.glb`. A far-LOD repair, head-bob, floor-fix or reduction
rerun on this model must re-graft these clips (copy the new source over the pre-gait copy and rebuild).
