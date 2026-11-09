# MM9 Green Man (`mm9_greenman`, row 266) reduction: candidate b r60 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (relaxed keep set,
face exact; prio-3 unique reduced after the user's "do all", 2026-11-05), ledger row 39 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Lease `mm9reduce:greenman` (owner greenman-reduce-20261105); the creature's own `mm9:greenman` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_greenman.glb` (sha256 72e57b0e741c, identical to `../mm9_greenman_claude/export/mm9_gm.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_greenman_claude/` was only read.

| | LOD0 | body shell | head shell (face) | leaf cards | hands | staff | crown branches | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,490 | 2,428 | 1,417 | 5,799 | 1,399 | 820 | 627 | 5,556 | 1,823 | 696 |
| **b r60 (`export/mm9_greenman.glb` = `export/mm9_greenman_b60.glb`, sha256 b03a26be5aa2)** | **10,630 (-14.9 %)** | 1,566 | 1,417 | 5,799 | 911 | 498 | 439 | 4,649 | 1,493 | 837 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (9), skin, nodes, materials, all 6 images: byte-identical (`same_clips.py`). Head shell (face, eyes, lips,
neck seam) and every leaf card: every installed triangle present exactly (`scripts/kept_exact.py`: 1,417 + 5,799 of 5,799).

## Measured first: protected share
`scripts/survey.py` + `scripts/classify.py` (components by position-welded connectivity, class by size, joint and paint): the body
shell (one component, 2,428, already cut 15.5k -> 9.6k at the build), the head shell (1,417: face, neck, scalp), 553 leaf cards
(5,799: closed 2-100 face shells of the hood, beard, mantle and kilt; no interior vertex to remove without moving a leaf edge, the
Rooster's lesson), the two MPFB hands with forearm stubs (1,399), the staff (820, 100 % Bone01) and the crown branches + wrist bark
(627). Protected with set b: 62.3 % (head shell + leaves 57.8 %, soles 170, neck 60, wrist rim 46, hand-graft junction 124,
fingertips 57, staff grip 105); -15 % needed 40 % of the 4,709 free faces.

Keep set (`scripts/make_sets_gm.py`, set b, SOLE=0.006): head shell and all leaf cards whole; body faces within 1.5 cm of the head
shell (neck seam) and of the hands (forearm rim on the hand stub), soles within 6 mm of the floor; hand faces dominated by a Forearm
joint (graft junction); fingertips (8 mm round each distal end, every finger); staff faces within 3 cm of the posed R hand in 9
frames of six clips (grip contact). No glow/emissive parts or used sockets on this model. Groups: hands 0.6 (seam slides, every
finger kept), staff 0.55, crown branches 0.7, body shell at the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Sigmund/PeasantF3 copy)
Scored over 176 poses (every clip at 10 Hz) plus the 5-D position+UV rest quadric (texture weight `MP_W5=4`); texture guard on both
base colours; the Mummy's chart guard at 12 subdivisions (`MP_CHART=1`) and the audit's own chart test inside each collapse
(`MP_AUDIT=1`). No linings on this model.

## Ladders (limits for 2.48 m: p99 <= 7.44 mm, max <= 37.2 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,b}.png`)
| ladder | change | step | LOD0 | p99 / max mm (worst) | result |
|---|---|---|---:|---|---|
| a | hands .65, staff .4, branches .6, SOLE 12 mm | r70 / r60 / r50 | 10,770 / 10,564 / 10,360 | 5.76/26.1, 6.95/31.1, 9.20/36.0 | pass / pass / fail; staff 0.4 carried most of the error (`err_by_bone.py`: Bone01 0.37 % of samples > 5 mm, worst 11 mm) |
| **b** | **hands .6, staff .55, branches .7, SOLE 6 mm** | **r60** / r55 / r50 | **10,630** / 10,524 / 10,416 | **6.83 / 31.1 (Running:12)**, 8.07/36.0, 10.2/51.7 | **PASS, picked** (IoU .9841, SSIM .9849) / fail / fail |
Two ladders used. r60 is the deepest passing step; the error is spread over the body shell (Spine, thighs, calves), none on the face.

## Gates, installed -> b r60 (the creature's own gates, `scripts/gates.sh`; `review/gates_before/`, `review/gates_b60/`)
- UV chart audit (`reduction_uv_audit.py`, `review/uv_audit_b60.json`): **0 LOD0 escaping faces** in both primitives. LOD1-3
  (rebuilt) 117/72, 75/103, 39/11 against the installed LODs' own 93/68, 89/98, 11/12.
- Arm/hand (`--outer-only --exclude-joints Bone01`): 0 frames > 1 cm in every clip both hands except Fidget2 L 6.0 cm (64 f, the
  beard stroke, installed the same); frame-0 L 2.0 -> 1.4 cm in AttackMelee/Hit/Death; finger stretch maxima equal (4.45 Fidget2).
- Staff grip (`--only-joints Bone01`): 2.1-2.6 -> 2.1-2.5 cm in every clip (frames equal or fewer).
- Jitter vs the pre-floor clips: 2 fails both (the installed Death shoulder skin 50.4/20.8 -> 50.2/22.0 mm/f2). Against the grounded
  Death: 0 -> 1 (Death R shoulder skin 2.1 mm/f2): a p95 over a smaller vertex set; every surviving vertex has the installed
  trajectory, so no vertex moves differently.
- Detached (`--fps 6`): 71 -> 70 parts, > 1 cm 16 -> 20, > 2 cm 6 -> 6, worst 3.02 cm both (the bind-pose scrap). The four new ones are
  1-triangle Meshy scraps and one 15-triangle leaf, 1.2-1.7 cm in single frames of Fidget/Fidget2/Running/Hit (the body surface under
  them was cut). (The fps-10 run was dropped: the installed run ended without output.)
- See-through (`scripts/see_through.sh`, the creature's r3 sampling: 5 clips, every 8th frame, 16 views, 3 mm px; hole max px):
  torso 81 -> 90, sleeve L 75 -> 78, sleeve R 74 -> 79, trousers L 24 -> 24, R 14 -> 13, head 100 -> 100, staff/boots/collar 0: the
  same leaf-edge slivers seen edge-on, same frames and views (`review/st_torso_pair.png`).
- Flat shading 0.02 both; winding 0 inverted (LODs through the creature's `fix_winding.py`: 2 thin leaf parts turned outward);
  bone lengths: the same 2 (MM9's own Fidget hip slide); texture quality body 55.1 % / stretch p90 1.18 -> 1.20, head set 49.4 % /
  4.94 (was 5.01).
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{before,b60}.json`), snap-fixed builder
  `scripts/build_lods.py` (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown tip and corpse contact protected, 59 points mapped
  of 59): height 3.777 m (staff top) at every LOD; every clip's lowest point at LOD1-3 equal to LOD0 (installed LOD3 had lost the feet
  and stood 19 cm above the floor in Standing, 41 cm in Running); stretched faces equal (LOD0 53-119 per clip both, the uv-sliver rows).
  LOD3 has 837 triangles (installed 696) because the feet are kept.

## Review
Viewer (installed and reduced, all 9 clips; `run_creature_review.py check`: 18 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_greenman_reduce_claude/review/viewer/
Sheets read (full size): `review/sheet_face_b60.png` (front close-up, 3/4, true profile, low 3/4, party), `review/sheet_face_diff_b60.png`
(face black in all five; differences only on the crown branches and the staff), `review/crop_branch_f0.png`, `review/crop_staff_f1.png`
(bark at full size), `review/sheet_body_b60.png` (Standing front/3-4/back, Walking, Fidget, Death), `review/close_b60_c0_c2_c1_c3.png`
(R hand on the staff, L hand, wrist vines), `review/close_b60_c4_c12_c5_c8.png` (chest and mantle leaves, shoulder, hood from behind,
crown), `review/close_b60_c6_c7_c9_c11.png` (kilt front/back, lower staff with the painted leg leaf), `review/close_b60_c10_c13_c14.png`
(staff top, Running, face close-up), `review/ladder_sheet_{a,b}.png`, `review/st_torso_pair.png`.
Look at: the crown branches and the staff at close range (bark a touch flatter in places, same silhouette), the fingers (0.6), the
torso under the mantle in motion.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_greenman_reduce_claude/before/mm9_greenman.glb REA_NODE=GreenMan $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/survey.py; $G scripts/classify.py
SOLE=0.006 $G scripts/make_sets_gm.py b
MP_CHART=1 MP_AUDIT=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=b MP_GROUPS=1:0.6,2:0.55,3:0.7 scripts/run_mp.sh b 0.6,0.55,0.5
scripts/build_mp.sh mp_b_r60 export/mm9_greenman_b60.glb   # swap_mp -> build_lods (snapped) -> shrink_shadow_lods -> drop_lod_slivers -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_greenman_b60.glb before/mm9_greenman.glb --json review/uv_audit_b60.json
scripts/gates.sh export/mm9_greenman_b60.glb b60; scripts/see_through.sh export/mm9_greenman_b60.glb b60; $G scripts/kept_exact.py export/mm9_greenman_b60.glb
REA_NODE=GreenMan $BL -P scripts/lod_check.py -- $PWD/export/mm9_greenman_b60.glb b60
$G scripts/make_viewer_manifest.py <rev> "inst=Installed=before/mm9_greenman.glb" "red=Reduced=export/mm9_greenman_b60.glb"
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py b60; $G scripts/face_diff_sheet.py b60
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_greenman.glb` (0), `tools/install_model.py export/mm9_greenman.glb
--world mm9 --name mm9_greenman.glb`, the `mm9_actor_models_build_every_binding` regression, the floor audit (`floor_audit.py --world
mm9 --match 'MM9 266*'`), and add to `../mm9_greenman_claude/README.md`: "LOD0 reduced post-install on <date> by
`mm9_greenman_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_greenman.glb`.

## Not checked
In game (not installed; Frosgard still places the stand-in 451); binding regression and floor audit (after install); motion at normal
speed by eye (frames, gates and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the detached audit at 10 fps.
