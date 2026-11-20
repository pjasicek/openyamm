# MM9 Bigfoot (`mm9_bigfoot`, Bigfoot / Sasquatch / Yeti) reduction: candidate d55 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 64 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:bigfoot` (owner bigfoot-reduce-20261104); the
creature's own `mm9:bigfoot` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_bigfoot.glb` (r9, sha256
1169fc94eae5, identical to `../mm9_bigfoot_claude/export/mm9_bigfoot.glb`), copied to `before/` (the rollback source). No Meshy,
no credits, no repaint. **Not installed.** `../mm9_bigfoot_claude/` was only read (its gates and the viewer page are used from there).

| | LOD0 | body (Bigfoot_A) | head (BigfootHead_A) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed r9 | 9,442 | 5,784 | 3,658 | 4,720 | 1,698 | 565 |
| **d55 (`export/mm9_bigfoot.glb`, sha256 20f87ed66c09)** | **7,320 (-22.5 %)** | 3,898 | 3,422 | 3,660 | 1,461 | 601 |

Every vertex of the candidate is an installed vertex: positions, normals, UVs, joints and weights are the installed bytes (only
index buffers changed). Clips (19), skin, nodes, materials (with region masks and ramps), `KHR_materials_variants` and all 9
images: byte-identical (`scripts/same_clips.py`). The face skin, eyes, ears, the neck seam and the r9 neck rim are the installed
triangles.

## Measured first: protected share
39.9 % of LOD0 is exact (`scripts/bf_sets.py d foot`; `review/classes_a.png`, `review/head_mask_view.png` show the regions).
Head (one wrapped shell + two eyes): eyes (160), the face skin (head region mask B, grown 2 rings: 1,832), the ears (box
|x| > 0.15, y 2.245-2.42, z 0.28-0.38 in glTF rest, grown 2 rings: 702, includes some hood round them), faces with no region (41),
the neck seam (head faces within 3 cm of a body vertex: 180) and the r9 neck rim (mask alpha: 448). Body (one skin with the MPFB
hands zipped at the wrists): neck seam (116), soles (within 1.2 cm of the floor: 246), the hand-graft junction (2 rings round the
hand/arm border: 404) and every face a `Foot_h` helper weights >= 0.4 (208, set d).
Free: hood (head mask R, sides and back of the skull) 376 at 0.7, crown (head mask G, the Yeti's blue stripes) 487 at 0.75, hands
1,370 at 0.7 (every finger kept: the collapse only removes vertices), feet (body mask B off the hands) 499 at 0.7, the rest of the
body 2,941 at the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Lesser Demon's copy with seam slides available)
Scored over every clip at 10 Hz plus a position+UV rest quadric; only removes vertices. Texture guard per collapse in every tier:
tier A = region mask (body: the mask's R is 1 everywhere, so the guard image is (alpha = saddle, G = chest, B = hands/feet);
head: R hood, G crown, B face), B = shared base colour, C = the Yeti's colour (`scripts/tex_extract.py`). The alpha guard changed
no collapse at r55 (identical index buffers, the saddle edge is soft). Seam slides were not needed: every group reached its target.
No linings on this body.

## Ladders (Blender-measured height 2.537 m: p99 <= 7.61 mm, max <= 38 mm; `review/ladder_sheet_{a,b,c,d}.png`)
| set | change | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | hands/hood/feet 0.7, crown 0.75 | r55 / r50 / r45 | 7,226 / 7,068 / 6,912 | 7.46/23.5, 9.24/27.6, 10.95/38.6 | .994/.995 | pass / fail / fail |
| b | a + saddle in the guard | r60 / r55 / r50 | 7,384 / 7,226 / 7,068 | 6.15/22.7, 7.46/23.5, 9.24/27.6 | .994/.995 | pass / pass / fail; b55 built: collapse ankle_R 1 -> 3 (Hit2), 2 -> 3 (Hit) |
| c | b + shoulder skin + `Foot_h` faces | r55 / r50 | 7,504 / 7,378 | 7.22/29.8, 9.27/29.8 | .994/.996 | pass / fail; c55 built: jitter equal, but collapse elbows 0 -> 3 (Fidget2, Taunt), AttackMelee shoulder_R 11 -> 13 |
| **d** | b + `Foot_h` faces | **r55** | **7,320** | **7.51/29.8 (Running:3)** | **.994/.995** | **PASS, picked** |

## Gates, installed -> d55 (Bigfoot's own gates, `scripts/gates.sh`; `review/gates_before/`, `review/gates_d55/`, `review/gates_compare_d55.txt`)
- Collapse (`collapse_gate.py`): face-frames 8,540 -> 5,110, lower or equal in every clip but Hit (122 -> 128). Worst-frame counts
  up by one face: Taunt wrist_L 0 -> 1, Hit torso 1 -> 2; exposed wrist_L 3 -> 4 in the gait clips (Walking, WalkFidget, Backpedal,
  BackpedalRun, Running) and Running knee_L 5 -> 6. The ankle rises of b55 are gone with the `Foot_h` keep.
- Arm/hand (`NOCLOTH=1 --outer-only --exact`): 0 frames over 1 cm in every clip, both files; worst 0.8 -> 0.7 cm (AttackMelee2 /
  AttackRanged R). Finger stretch max in the gait clips 2.37-2.75 -> 1.31-1.36 (the installed knuckle faces that stretched are
  gone); p99 1.11 -> 1.12 at rest.
- Jitter (vs `../mm9_bigfoot_claude/work/bf_ref_clips.glb`): strict 27 -> 26 fails (Taunt R passes now), relative 20 -> 20.
  Shoulder-skin excess rose in Taunt L (2.62 -> 3.21 mm/f2), Hit R (4.30 -> 5.24) and Hit2 L relative (2.86 -> 3.47), fell in
  most others. Clips are byte-identical and every kept vertex skins exactly as installed: the statistic is the p95 over the
  shoulder vertices, and the reduced set is a subset (109 -> 82 per side). `scripts/shoulder_subset.py`
  (`review/shoulder_subset_d55.txt`): the vertex maximum never rises (Taunt L 141.04 = 141.04, Hit R 355.65 = 355.65, Hit2 L
  216.35 = 216.35 mm/f2). A sample-set change, not new motion. Set c kept the shoulder skin and made jitter identical, but cost
  184 triangles and moved collapse into the elbows, so it was not picked.
- Detached 0 (3 components), bone lengths 0 stretching, winding 0, flat shading 0.00 / 0.00, texture quality: atlas and density
  unchanged, body stretch p90 1.07 -> 1.09, head 1.14 -> 1.14.
- LODs (`scripts/lod_check.py`, every frame of every clip; `review/lod_table_d55.txt`), built by `scripts/build_lods.py`
  (tools/build_actor_lods.py, ratios 0.5 / 0.2 / 0.075, 4 influences; protected: soles, the top, corpse contact of Death/Death2/Dead
  within 4 cm, foot extremes and both primitives' rest extremes, each point **snapped to the nearest imported vertex** first: 158
  of 158 mapped, worst offset 3.1e-6 m). Stretched faces 0 at every LOD (as installed). Top 2.561 m at every LOD (installed
  2.563 / 2.563 / 2.562 / 2.567: the crown's top vertex went in the 0.75 cut, 2 mm). Floor: LOD0 identical per clip; LOD1-3
  equal or closer to the floor than installed (LOD3 Standing -0.29 -> 0.00 cm, Death -2.08 -> -0.16, Running -2.07 -> -1.15);
  where LOD1/2 sit lower than installed it is by at most 0.07 cm and onto LOD0's own value (AttackMelee -0.01 -> -0.05, Taunt
  -0.02 -> -0.04, LOD1 Backpedal -0.38 -> -0.45), plus LOD2 LyingDown +0.30 -> -0.17 cm (installed floated, now touches).

## Review
Viewer (installed and reduced per tier, 19 clips):
http://127.0.0.1:8912/level_generation/creatures/mm9_bigfoot_reduce_claude/review/viewer/
`run_creature_review.py check`: 114 switches (6 models x 19 clips), 0 failed, 0 console errors.
Sheets read (full size): `review/sheet_face_d55.png` (front close-up, 3/4, true profile, low 3/4, party; every tier, installed over
reduced), `review/sheet_face_diff_d55.png` (|installed - reduced| x4: face, eyes, ears and neck black in every tier and view; only
the shoulders, chest and the crown's edge differ), `review/sheet_body_d55_{a,b,c}.png` (Standing front/3-4/back, Walking,
AttackMelee, Death), `review/upper_d55_{a,b,c}_{1,2,3}.png` (hood and crown from behind, side-back and above; chest, back with the
Sasquatch saddle, shoulder profile; AttackMelee and Taunt nape; both hands), `review/close_d55_{a,c}_{1,2}.png` (arms, belly side,
hands, feet, AttackMelee back, Walking legs, Fidget2 hands; `k5` Death2 head framed empty in both), `review/crown_profile_c_d55.png`
(Yeti crown stripes at full size: unchanged), `review/classes_a.png`, `review/head_mask_view.png`, `review/ladder_sheet_{a,d}.png`.
No visible change found. Look at: the belly and flank outline in profile (slightly more faceted at close range, `close_d55_a_1`
k1), the Yeti crown stripes (0.75) and the hands (0.7). The viewer's own framings sit low on this 2.56 m body (the `body` focus
crops the head; `k5` frames empty space), so `scripts/upper_shots.sh` frames the upper body on bones instead.
Pre-existing, not caused by the reduction: an orange eye-like fleck painted high on the Yeti's crown behind the stripes (both files,
`review/crown_profile_c_d55.png`).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_bigfoot_reduce_claude/before/mm9_bigfoot.glb REA_NODE=Bigfoot $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py
$G scripts/bone_keep.py foot 'Foot_h$' 0.4
$G scripts/bf_sets.py d foot; $G scripts/class_view.py d; $G scripts/head_mask_view.py
SETS=d MP_GROUPS=1:0.7,2:0.7,3:0.7,4:0.75 scripts/run_mp.sh d 0.55     # mpqem -> reduce_ladder (error over every clip) -> compare
LIE=0.04 SOLE=0.012 scripts/build_mp.sh mp_d_r55 export/mm9_bigfoot_d55.glb; cp export/mm9_bigfoot_d55.glb export/mm9_bigfoot.glb
scripts/gates.sh export/mm9_bigfoot.glb d55; python3 scripts/bf_gate_compare.py d55
REA_NODE=Bigfoot $BL -P scripts/lod_check.py -- $PWD/export/mm9_bigfoot.glb d55; python3 scripts/lod_table.py installed d55
$G scripts/viewer_tiers.py before/mm9_bigfoot.glb inst; $G scripts/viewer_tiers.py export/mm9_bigfoot.glb red   # then make_viewer_manifest.py
scripts/shots.sh; python3 scripts/shot_sheets.py d55; python3 scripts/face_diff_sheet.py d55; scripts/close_shots.sh; scripts/upper_shots.sh
```
`run_mp.sh`'s `REA_HEIGHT_M` default is 2.537 (Blender's dimension of the imported rest mesh; the GLB stands 2.563 m, so the
limits are slightly stricter than the GLB height would give).
Install (on the user's OK only): `check_winding.py export/mm9_bigfoot.glb` (0), `tools/install_model.py export/mm9_bigfoot.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, `floor_audit.py --world mm9 --match 'MM9 Bigfoot*'`, and add to
`../mm9_bigfoot_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_bigfoot_reduce_claude`; a rebuild from this project
must re-run that reduction". Rollback: `before/mm9_bigfoot.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the Sasquatch (tier B) close shots (face, body and upper sheets
only); the orientation, handedness and stride gates (they read only the clips, which are byte-identical); indoor light; Android.
`export/mm9_bigfoot_b55.glb` and `_c55.glb` are superseded candidates (gates in `review/gates_b55/`, `review/gates_c55/`;
`review/gates_compare_{b55,c55}.txt`). Several scripts in `scripts/` are copies from the Gezzampt/Troglodyte/Highwayman projects
that this route did not use (`gezz`-specific helpers were adapted or left unused: `make_sets.py`, `glb_parts.py`, `grip_contact.py`).
