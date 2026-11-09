# MM9 Mummy (`mm9_mummy`, Canopic / Embalmed / Petrified) reduction: candidate e r48 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 monster,
relaxed keep set), ledger row 66 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:mummy` (owner
mummy-reduce-20261104). Source: the installed `assets_source/worlds/mm9/models/mm9_mummy.glb` (sha256 529f6652cc7b, identical to
`../mm9_mummy_claude/export/mm9_mummy.glb`), copied to `before/` (the rollback source). No Meshy, no credits, no repaint.
**Not installed.** `../mm9_mummy_claude/` was only read.

| | LOD0 | body `Mummy` (skin, hands, strips) | head `MummyHead` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 9,397 | 6,190 (main 4,460, hands 1,346, strips 384) | 3,207 | 4,697 | 1,691 | 563 |
| **e r48 (`export/mm9_mummy.glb`, sha256 19ba37ced678)** | **6,781 (-27.8 %)** | 3,574 (main 2,382, hands 808, strips 384) | 3,207 (exact) | 3,568 | 1,363 | 592 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only the
body's index buffer changed). Clips, skin, nodes, materials, `KHR_materials_variants` (carried to every LOD and shadow primitive),
all 14 images: byte-identical (`scripts/same_clips.py`). The whole head set (face, hood, eyes) is the installed primitive; the
two-sided band, thigh and arm strips are the installed triangles (`scripts/face_exact.py`: 0 missing or changed). The face diff
sheets are black on the head in every tier and view.

## Keep set (`scripts/make_sets.py`; measured first: 39.9 % protected, so ~15 % was reachable)
- **Exact:** the head set (face 2,505 by position: centroid z > -0.01 below y 1.805 or z > 0.07; eyes 116; hood 586, kept whole
  after ladder b cut its crown 3 mm, `review/hood_crop_b40.png`), the strips (384: the band is a rope solve on its own bones, the
  thigh and arm strips lie 5.5 mm on the skin), soles (272), the neck seam (body and head faces within 2 cm of the hood's lower rim).
- **Cut:** hands 0.6 (every finger kept: pose-aware collapse over the finger bones), body skin at the ladder ratio.

## Route: `scripts/mpqem.py` (Lesser Demon copy of the Highwayman's pose-aware half-edge collapse, 475 poses = every clip at 10 Hz)
Seam slides on body and hands (`MP_SEAM_GROUPS`), the Zombie's per-tier texture guard on the three tier base colours, texture
weight 4 (`MP_W5`), and two guards added here after the first builds:
- **stretch guard** (`MP_ANISO=1.6`): a new face may not stretch the texture more anisotropically than max(1.6, the face it replaces);
- **chart guard** (`MP_CHART=1`): every sample of a new face's UV triangle must lie on the installed charts. Builds b40/c40/d40 had
  204 faces reaching into gutters or other islands (`scripts/uv_escape.py`), visible as a smeared chevron on the Embalmed forearm
  (`review/zoom_forearm_c40.png`); the 7-sample texture guard and the stretch guard missed it. e r48: 3 faces at 1-2 % (the
  2-texel dilation), the chevron gone (`review/zoom_forearm_e48.png`).

## Ladders (limits for 1.815 m: p99 <= 5.45 mm, max <= 27.2 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | step | LOD0 | p99 / max mm | IoU / SSIM | result |
|---|---|---|---:|---|---|---|
| a | hands .65, hood .8 | r70 / r62 / r55 | 7,663 / 7,345 / 7,065 | 2.60/10.7, 3.06/10.7, 3.41/13.8 | .995/.997 at r55 | pass |
| b | hands .6, hood .7, W5 4 | r48 / r40 / r33 | 6,689 / 6,369 / 6,089 | 4.10/15.8, 5.12/20.1, 6.01/27.0 | .989/.994 at r40 | pass / pass / fail; built b40: hood crown 3 mm lower, forearm chevron |
| c, d | b + hood kept (d: + stretch guard) | r40 | 6,461 | 5.11 / 20.1, 5.05 / 20.1 | .990/.994 | pass; chevron still there |
| **e** | **d + chart guard** | **r48** / r40 | **6,781** / 6,461 | **4.50 / 19.3** (Resurrect:3), 5.98/27.0 | **.991 / .996** | **pass, picked** / fail |

## Gates, installed -> e r48 (`scripts/gates.sh`: the Mummy's own gate scripts; `review/gates_before/`, `review/gates_e48/`)
- Collapse face-frames 15,609 -> 7,935; worst-frame region counts equal or lower in every clip except Resurrect (script) knee_L 2 -> 4.
- Arm/hand (`--outer-only --exact` on the runtime GLB for both files): equal or better everywhere; finger stretch max equal except
  Resurrect R 1.41 -> 1.46. (On the runtime GLB the right hand reads 5-6 cm in most clips in both files: the band is pinned on that
  forearm. The creature ran this gate on its strip-less skin.)
- **Strip gate bug:** the creature's `strip_gate.py` stacks the head primitive's triangles onto the body's vertex array (~80 garbage
  "leg" faces); on the reduced vertex order they read 10 cm through-the-leg hits. `scripts/strip_gate_dense.py` uses the body
  primitive only (SPACING=0: the original four samples per face; SPACING=0.006 adds samples on large faces). Fixed, band through
  thigh/calf: AttackMelee/Ranged 1/42 1.0 -> 1/42 1.1 cm, Hit2 3/49 0.6 -> 1/49 0.4, Death 2/53 0.4 -> 0, Coffin 1.4 -> 1.3,
  Resurrect 5/177 1.1 -> 10/177 1.0, Death2 0 -> 1/66 0.7 cm. Band through torso (the installed fault: band tip pinned on the
  forearm crossing the chest): AttackMelee/Ranged 7/42 5.9 -> 6/42 6.1 cm, AttackMelee2 5/37 9.4 -> 5/37 10.0 (the 10 cm search
  bound), Wakeup2 13 -> 1 frames, Death2 18 -> 7 frames, Resurrect 4 -> 3. The dense variant agrees (legs equal).
- Detached: the same three shallow/lift readings. Bone lengths: the same 4 thigh stretch rows. Winding 0. Flat shading 0.00 / 0.00.
  Texture quality: body stretch p90 1.11 -> 1.15, atlas 55.8 -> 55.7 %, head unchanged. UV anisotropy faces > 3: 65 -> 65.
- Jitter and orientation gates read bones only; the clips are byte-identical, so they were not rerun.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`: the tool's LOD build with protected soles, crown
  and corpse points snapped to the import, per-material ratios body 0.55/0.22/0.10, head 0.5/0.18/0.06): top 1.8447 m at every LOD
  (installed LOD3 1.8524), floor 0.0 cm in Standing, Dead, Dead2 at every LOD (installed LOD3 Standing +1.0, Dead +1.1 cm), no face
  stretched over 20x in any clip at any LOD. With the default ratios the band folded 7 cm under the floor at LOD3 in Death (b40);
  the body's LOD3 budget fixed it.

## Review
Viewer (installed and reduced, every tier, all 23 clips; `run_creature_review.py check`: 138 switches, 0 failed, 0 console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_mummy_reduce_claude/review/viewer/ (`inst_a/b/c`, `red_a/b/c`).
Sheets read: `review/sheet_face_diff_e48_{a,b}.png` (front close-up, 3/4, profile, low 3/4, party; installed | e48 | diff x4: head
black), `review/sheet_body_e48_c.png`, `review/close_e48_a_1.png` (hands, AttackMelee hand, hips front/back),
`review/close_e48_b_2.png` (Walking hips, foot, chest, back, Death), `review/zoom_forearm_e48.png`; earlier builds
`review/sheet_face_diff_b40.png`, `review/hood_crop_b40.png`, `review/close_c40_{a_1,b_1,c_2}.png`, `review/zoom_forearm_c40.png`,
`review/ladder_sheet_{a,b}.png`. Written, not read: `sheet_face_diff_e48_c.png`, `sheet_body_e48_{a,b}.png`, `close_e48_{a_2,b_1,c_1,c_2}.png`.
Look at: the bandage stripes on the larger body faces (shading on the linen normal map differs a little in the diff, not side by
side), the hands at 60 %, the ankles in profile.

## Build
`scripts/reproduce.sh` (import_source -> dump_mesh -> tex_extract -> make_sets a -> run_mp.sh e 0.48 -> build_mp.sh: swap_mp ->
build_lods -> the Skeleton Warrior's shrink_shadow_lods (as the creature's rebuild.sh) -> carry_variants -> check_winding).
Gates: `scripts/gates.sh export/mm9_mummy.glb <tag>` plus `strip_gate_dense.py`; LODs: `REA_NODE=Mummy blender -b -P
scripts/lod_check.py -- <glb> <label>`, `lod_summary.py`, `lod_low.py`, `lod_stretch.py`; texture: `uv_escape.py`, `uv_stretch.py`;
viewer: `viewer_tiers.py <glb> <inst|red>`, `make_viewer_manifest.py`, `shots.sh`, `close_shots.sh`, `shot_sheets.py`,
`face_diff_sheet.py`, `pair_sheet.py`.

Install (on the OK only): `check_winding.py export/mm9_mummy.glb` (0), `python3 tools/install_model.py
level_generation/creatures/mm9_mummy_reduce_claude/export/mm9_mummy.glb --world mm9`, the `mm9_actor_models_build_every_binding`
regression, `floor_audit.py --match 'MM9 Mummy*'`, the ledger row, and the line in `../mm9_mummy_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_mummy_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_mummy.glb`.

## Not checked
In game (not installed; the binding regression and floor audit read the installed file); motion at normal speed (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); every close sheet of every tier (listed above).
