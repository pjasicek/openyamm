# MM9 Evil Sorcerer (`mm9_evilsorcerer`, tiers es_a / es_b / es_c) LOD0 reduction (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 26 of
"MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md), prio 1 (monster: the prio-1 relaxed keep set applies).
Lease `mm9reduce:evilsorcerer` (evilsorcerer-reduce-20261104). Route: [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
default route, no-retexture branch. No Meshy, no credits. **Status: fix-pass candidate h r47 ready for review, not installed (f r75 was installed and rolled back).**

Source: the installed `assets_source/worlds/mm9/models/mm9_evilsorcerer.glb` (= `../mm9_evilsorcerer_claude/export/mm9_evilsorcerer.glb`,
sha256 1e83b883acf1...), copied to `before/mm9_evilsorcerer.glb` (the rollback source). Candidate: `export/mm9_evilsorcerer.glb` (now h r47; f r75 kept as `work/f75_final.glb`)
(f r75 was sha256 e1328bf527b8...).

## Fix pass (2026-11-04 evening): chart-guarded h r47, ready for review — current candidate

The f r75 candidate below (MeshLab ladder) was installed and **rolled back**: 28 of its LOD0 faces left the painted UV charts
(`review/uv_audit_f75.json`: pauldron fronts/backs, backs of both hands, bracer, front panel, greave tops, shoes). The fix pass
uses the pose-aware half-edge collapse with the chart guard (`scripts/mpqem.py`, the Dwarf's copy: `MP_CHART=1`, every sample of
a new face's UV triangle must lie on the installed charts; texture guard on the three tier base colours taken from the installed
viewer GLBs, `tex_extract.py`; 5-D texture weight `MP_W5=4`). Every output corner is an installed vertex, so positions, UVs,
normals, joints and weights are exact. Same keep set and ratios as f (`work/keep_f.npy`), plus the panels in their own group at
0.7 and the panels' centre strip (|x| < 2.5 cm, the back panel's slit) kept exactly: without them the slit opened a dark notch
at knee height (`review/s_g50_panels_clay.png`).

`SETS=h MP_GROUPS=1:0.6,2:0.65,3:0.6,5:0.7,6:0.65 MP_W5=4 scripts/run_mp.sh h 0.5,0.47`, then `scripts/build_mp.sh mp_h_r47`
(-> `export_mp/mm9_evilsorcerer.glb`, copied to `export/mm9_evilsorcerer.glb`, sha256 5fe4843bf452):

| config | step | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---|---:|---|---|---|
| a (keep f, groups f) | r60 / r50 / r45 | 10,024 / 9,560 / 9,328 | 3.98/13.1, 5.03/20.3, 6.46/30.3 | 0.993 / 0.995 at r50 | r50 passes; dark crease/notch on the back panel at knee height |
| g (+ panels 0.7) | r50 / r45 / r40 | 9,776 / 9,598 / 9,428 | 5.11/20.3, 6.61/30.3, 9.88/31.6 | | r50 passes; the back-panel notch remains |
| **h (+ panel centre strip kept)** | r50 / **r47** | 9,888 / **9,782 (-26.7 %)** | 5.11/20.3, **5.75/21.5** | **0.993 / 0.994** | **r47 picked, lowest passing; clean** |

LODs 9,782 / 4,890 / 1,756 / 578 (installed 13,348 / 6,673 / 2,401 / 797), built by `build_lods_mp.py` (the Imp's, protected
points snapped to the imported vertices): soles, crown top, rest extremes and the Dead clip's floor contact within 4 mm
(`CORPSE_CLIPS=Dead LIE=0.004`: Death+Death2+Dead at 1 cm gave 690 points and stopped LOD3 at 1,647 triangles; Dead at 1 cm
left 11 stretched LOD2/3 faces). Every LOD 1.9825 m tall; lowest point Standing 0, Dead 0 at every LOD, Walking -1.41 cm and
Death2 -12 cm as installed; stretched faces LOD0 14 (installed 19), LOD1 9, LOD2 2, LOD3 0. Clips, skin, nodes, materials,
images and variants are the installed bytes (`same_parts.py`: ALL SAME).

**UV audit (`review/uv_audit.json`): 0 escaping LOD0 faces in every primitive.** LOD1-3 (Blender's decimate, as installed):
LOD1 Up 133 / Low 33 / Head 54 against the installed 89 / 16 / 42; LOD2 109 / 60 / 67 against 125 / 52 / 61; LOD3 64 / 24 / 50
against 75 / 29 / 53.

Gates (`review/gates_before/` vs `review/gates_h47/`):
- panel gate: Death front 6/58 4.2 cm -> 0; Death2 back 5/73 2.2 cm both; all other clips 0 both;
- arm/hand `--outer-only --exact`: Fidget2 L 4.5 -> 4.3, R 3.9 -> 3.7 cm; AttackRanged L 2.0 -> 1.6, R 1.4 -> 1.6; AttackRanged2/
  Resurrect L 3.9 both, R 1.5 both (forearm 1.2 -> 1.3); Hit R forearm 0 -> 1.0 cm; the rest equal or lower; finger stretch 2.36 both;
- arm/hand sample test (the creature README's setting): Walking L 0 -> 6.0 (4 frames), BackpedalRun L 0 -> 6.0 (4), Backpedal L
  5.7 (1) -> 6.0 (8), Hit R 0 -> 3.6 (1): the same artefact as f75 (fingertips over the unchanged hip flaps read behind a
  centroid sample of a larger trouser face; the exact test reads 0 and the walk close-up shows the same fingers);
- collapse face-frames lower in every clip (Standing 1,513 -> 1,403, Death 1,368 -> 1,140); worst-frame regions +1/+2 at hip L,
  knee R (Running, AttackRanged2, Death) and elbow R (Fidget2);
- detached parts: the installed five (hip flaps, crown piece 3.6 -> 3.3 cm) + the right pauldron 0.75 cm in 2/861 poses (Death2);
- winding 0, flat shading 0.01 / 0.01 / 0.00, texture quality equal to installed (atlas 58.5 / 55.7 / 60.3 %, stretch p90
  1.09 / 1.15 / 1.16).

Viewer: installed and h47, every tier, all 18 clips (`run_creature_review.py check`: 108 switches, 0 failed, no console errors).
Sheets read: `review/sheet_escapes1_tex_h47.png` (pauldron fronts and backs), `review/sheet_escapes2_tex_h47.png` (hands, back
and palm side), `review/sheet_escapes3_tex_h47.png` (front panel, bracer back, greave tops, shoes) — where f75 escaped, every tier;
`review/sheet_faces_h47.png` (face diff black in every tier and view), `review/sheet_tiers_tex_h47.png`,
`review/sheet_details_clay_h47.png`, `review/sheet_body1_clay_h47.png`, `review/sheet_body2_clay_h47.png`,
`review/s_h47_panels_clay.png`. Seen and left: the clay chest shows a slightly sharper fold under the collar V and the pauldron
rim a little more faceted; the textured renders show no difference there.

# Earlier candidate (rolled back): f r75, MeshLab ladder

## Result

| | LOD0 | Up set | Low set | head set | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 13,348 | 4,850 | 4,916 | 3,582 | 6,673 | 2,401 | 797 |
| **reduced (f r75)** | **10,010 (-25.0 %)** | 3,466 | 3,554 | 2,990 | 5,003 | 1,799 | 592 |

Clips, images, materials, textures, samplers, skin and inverse binds, nodes (sockets), `KHR_materials_variants` and the
per-tier head images are byte for byte the installed file's (`scripts/same_parts.py`: ALL SAME); every LOD and shadow
primitive carries the variant mappings. Only geometry changed. Normals: every candidate vertex that is a source vertex
takes the installed normal byte for byte; new vertices take the creature's own build rule (`fix_normals.py --selftest`:
the rule reproduces the installed normals within 0.02 deg). LOD1-3 rebuilt the creature's way (`build_actor_lods` ratios
0.5 / 0.18 / 0.06, 4 influences, skeleton warrior's shadow shrink, its fix_winding) with the soles and the crown top locked
(`scripts/build_lods.py`): unlocked, LOD3 stood 6 mm off the floor.

## What is kept, what is cut (`scripts/make_groups.py`, config f)

Parts come from the creature's own part map (`scripts/parts_map.py`: `../mm9_evilsorcerer_claude/work/uv_tex.npz`, every
GLB face matched at 1e-7 m). Protected share: 4,681 of 13,348 faces (35 %) kept exactly.
- **Kept exactly:** the face skin (head-part faces at the face texel density, 1,795: `uv_es.py` gave the face 1.7x and the
  helmet's back neck guard 0.55x, so `texel_ratio.npy` separates them) and both eyes (118); the neck seam (torso and yoke
  faces within 3 cm of the closed neck under the jaw, 146); soles (266); wrists (hand faces with Forearm weight plus the
  open rim and one ring, 108); all finger phalanges 2-3 (474); the crown jewel piece (48); belt and buckle (716) and both
  hip-flap pairs (480); panel faces within 4 cm of a flap and the panels' side rim strips; bracer faces within 4 cm of a hand.
- **Own ratios:** neck guard (flap) 0.6, crown 0.65, palm/back of hand and proximal phalanges 0.6, rigid plates
  (pauldrons, bracers, greaves, boots) 0.65.
- **Rest** (torso, trousers, yokes, shoes, panel walls): the ladder's remaining budget.

## Ladder (REA_HEIGHT_M 1.973: p99 <= 5.92 mm, max <= 29.6 mm; textured, UV-barycentric weights, exact source weights)

| config | change | step | LOD0 | p99 / max mm | IoU / SSIM | verdict |
|---|---|---|---:|---|---|---|
| a | face, eyes, neck, soles, wrists, fingers kept; flap 0.7, crown 0.75, hand 0.65 | r82 .. r66 | 10,942 .. 8,806 | 2.02/21.6 .. 4.60/28.2 | 0.992 / 0.994 at r66 | all pass; r70 rejected on GLB clay: belt lumpy with a torn lower rim, flap teeth through the flattened panel tops, a dark slot in a flap, bracer rim off the wrist (`review/s_a70_det_clay.png`) |
| b | + belt, buckle, flaps, panel near flaps, bracer near hands kept | r80 .. r68 | 10,676 .. 9,074 | 4.56/27.8 at r72 | 0.992 / 0.994 | r72 rejected: panel walls (thin closed slabs, < 6 mm) crossed at the hem teeth, the back slit and the edges: dark wedges (`review/s_b72_panels_clay.png`) |
| c | + panel rim strips kept | r76 / r72 | 10,142 / 9,608 | 4.23/27.8, 5.24/30.3 | | r72 fails (max) |
| d | c + plates 0.65, fingers 0.8, crown 0.65, flap 0.6, hand 0.6 | r74 | 9,874 | 4.18 / 27.8 | 0.994 / 0.995 | pass and clean on sheets; dropped: arm/hand gate fingertips into the flaps in Walking/Backpedal (sample test) |
| e | d + error lock (posed misses > 14 mm, 3 cm) | r74 / r72 | 9,874 / 9,606 | 5.50/18.9, 7.13/26.5 | | the lock moved the error (playbook), dropped |
| **f** | **d with fingers kept exactly** | r76 / **r75** / r74 | 10,142 / **10,010** / 9,876 | 3.88/27.8, **4.10/27.8**, 4.37/29.7 | **0.994 / 0.995** at r75 | **r75 picked: lowest passing step** |

The max error of every config sits in the crotch of the trousers (Running, R XhalfThigh), hidden between the legs under
both panels; the installed mesh already folds there (collapse gate groin counts).

## Gates (installed -> reduced, both run here with the creature's own scripts: `scripts/gates.sh`, `review/gates_before/`, `review/gates_f75/`)

| gate | installed | reduced f75 |
|---|---|---|
| panel gate (legs/flaps through panels, 48 fps) | all clips 0 except Death front 6/58 4.2 cm, back 1/58 0.2; Death2 back 5/73 2.2 | all clips 0 except Death front 1/58 1.6 cm, back 2/58 0.3; Death2 back 4/73 2.0 |
| arm/hand `--outer-only --exact` (cm, frames > 1 cm) | Fidget2 L 4.5 (53) R 3.9 (47); AttackRanged2/Resurrect L 3.9 (4); Death R 1.9 (8); AttackRanged L 2.0 (2) | Fidget2 L 4.6 (53) R 3.7 (47); AttackRanged2/Resurrect L 3.9 (4); Death R 1.9 (7); AttackRanged L 1.2 (2); **Death L 0.3 -> 3.2 (2 frames)**; the rest 0 or lower |
| arm/hand `--outer-only` (sample test, the creature's README setting) | Backpedal L 5.7 (1); Fidget2 L 4.9 R 4.0; Death R 2.6 (9) | **Walking L 5.9 (2), BackpedalRun L 5.9 (2), Backpedal L 5.8 (4), Hit R 4.3 (1), Death R 5.4 (11), Fidget2 R 6.0**: a fingertip near a hip flap (kept exactly) read behind a centroid sample of a now larger trouser face; the exact test reads 0 there and the renders show the same fingers over the flap |
| finger stretch max | 2.36 | 1.96 (fewer stretched palm edges) |
| collapse face-frames (Standing / AttackRanged / Death) | 1,513 / 1,737 / 1,368 | 593 / 1,146 / 877; every region's worst frame equal or lower except elbows (Running L 2 -> 5, Fidget2 R 0 -> 3, AttackRanged L 0 -> 3): the elbow close-ups look smoother, no visible collapse (`review/sheet_gate_spots_clay_f75.png`) |
| detached parts (default 30 fps, full report) | 5 flagged: the hip flaps (152/861, 210/861 poses, up to 11 cm, MM9's flap swing), crown piece 3.6 cm 1 pose, flap 1.1 cm 1 pose | the same five (crown piece 3.4 cm) + bracer R 0.8 cm in 2/861 poses (Fidget2) |
| winding, flat shading | 0; 0.01 / 0.01 / 0.00 | 0; 0.01 / 0.01 / 0.00 |
| texture quality Up / Low / head: atlas, stretch p90 | 58.5 %, 1.07 / 55.7 %, 1.13 / 60.3 %, 1.16 | 57.6 %, 1.14 / 55.3 %, 1.18 / 60.2 %, 1.19 (UV-keeping collapse) |
| LOD heights (LOD0-3), stretched faces | 1.9827 m; LOD0 19 face-clips | 1.9833 m every LOD; LOD0 17, LOD1 10, LOD2/3 0 |
| floor (lowest point, cm) Standing / Walking / Death / Dead | 0 / -1.41 / -0.03 / 0 (LOD3 Dead -0.19) | LOD0 identical; LOD3 Dead +0.45 (far LOD corpse 4.5 mm up) |
| jitter, orient, bone lengths | | not rerun: clips byte for byte the installed ones (`same_parts.py`) |

## Review
- Viewer (installed and reduced, every tier, all 18 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_evilsorcerer_reduce_claude/review/viewer/
  (`run_creature_review.py check`: 108 switches, 0 failed, no console errors).
- Sheets (read): `review/sheet_faces_f75.png` (front close-up, 3/4, profile, low 3/4, party; every tier; installed | reduced |
  diff x8: the face is black in every diff, differences only on the plates, crown and neck guard), `review/sheet_tiers_tex_f75.png`,
  `review/sheet_details_clay_f75.png` (belt, panels, hems, corpse panels, flaps, bracer), `review/sheet_body_clay_f75.png`,
  `review/sheet_poses_clay_f75.png`, `review/sheet_gate_spots_clay_f75.png`; rejected steps: `review/s_a70_*.png`, `review/s_b72_*.png`.

## Install (not run; on the user's OK)
`check_winding.py export/mm9_evilsorcerer.glb` (0), `tools/install_model.py export/mm9_evilsorcerer.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, `floor_audit.py --world mm9 --match 'MM9 Evil*'`, then add to
`../mm9_evilsorcerer_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_evilsorcerer_reduce_claude`; a rebuild
from this project must re-run that reduction". Rollback: `before/mm9_evilsorcerer.glb`.

## Reproduce (project folder)
`REA_GLB=level_generation/creatures/mm9_evilsorcerer_reduce_claude/before/mm9_evilsorcerer.glb REA_NODE=Sorcerer`:
`find_doubles.py` (0), `import_source.py`, `dump_mesh.py`, `dump_faces.py`, `dump_weights.py`, `parts_map.py`, texel ratio
(`work/texel_ratio.npy`, sqrt(UV area / 3D area) per face), `THIN=0.006 thin_faces.py` -> `work/thin_0.006.npy`,
`KEEP_PARTS=belt,buckle,flapF,flapB PANEL_NEAR=0.04 BRACER_NEAR=0.04 PANEL_RIM=0 PLATE_RATIO=0.65 CROWN_RATIO=0.65 FLAP_RATIO=0.6 HAND_RATIO=0.6 make_groups.py`,
`REA_HEIGHT_M=1.973 REA_WEIGHTS=component REA_KEEP_FACES=work/keep_f.npy REA_GROUPS=work/groups_f.npy REA_GROUP_RATIOS=1:0.6,2:0.65,3:0.6,6:0.65 run_ladder.sh f 0.76,0.75,0.74`,
`build_export.sh f r75 final`, `viewer_tiers.py`, `glb_close.py`, `face_sheet.py`, `pair_sheet.py`, `lod_check.py`, `gates.sh`,
`make_viewer_manifest.py`.
