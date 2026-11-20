# MM9 Fish (`mm9_fish`) reduction: candidate b38 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md), ledger row 106 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Leases `mm9reduce:fish` and `mm9:fish` (owner fish-reduce-20261105, both released;
the stale `claude-mouse-fish` lease had been released by the orchestrator). Source: the installed
`assets_source/worlds/mm9/models/mm9_fish.glb` (sha256 33dd3d4006b2, identical to `../mm9_fish_claude/export/mm9_fish.glb`, the
2026-11-04 swimmer re-export), copied to `before/` (the rollback source). `../mm9_fish_claude/` was only read. No Meshy, no
credits, no repaint. **Not installed.**

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 5,558 | 2,778 | 998 | 332 |
| **b38 (`export/cand_b_r38/mm9_fish.glb`, sha256 4a3c3925e885)** | **4,300 (-22.6 %)** | 2,150 | 772 | 360 |

Every LOD0 vertex is an installed vertex (half-edge collapse, index buffer swap): positions, normals, UVs, joints and weights are
the installed bytes. Clips (7, with the +0.4096 m swimmer lift), skin, nodes, both materials (fins MASK 0.5) and all 4 images are
byte-identical (`same_clips.py`). Only the body primitive changed: 4,110 -> 2,852; the fin primitive (1,448) is untouched.

## Measured first (`scripts/animal_sets.py` + `scripts/fish_head.py`, `work/survey_a.txt`)
The body was decimated at the build (`reduce_body.py 3600`): flank, back and belly 6-8 mm edges, the head 2-4 mm, eye lenses
two 256-face pieces, fins 14 leaves (7 pairs of sheets 0.8 mm apart, 9.6 mm grid, alpha cut-outs). The head is mostly weighted to
`XCENTER` (`Xmouth`/`Xjaw` carry only the lips), so it is cut by position: the gill cover's rear edge lies at z = 0.088-0.095 m
(`review/fish_head_cut_tex.png`, side raster with lines at z 0.07-0.10). Set a: every body face with a vertex in front of
z = 0.085 + 1 ring (eyes, mouth, jaw, cheek, gill cover and its edge), the eye lenses, Xmouth/Xjaw skin + 2 rings, and **every fin
leaf whole** (rays and edges exact; the paired sheets would separate if cut independently): exact 3,530 = **63.5 %**, free 2,028
(flank, back, belly, tail stalk behind the gills); -15 % (834 tris) needed **41 %** of the free faces. The orchestrator's ~50 %
estimate let the fins move; with them whole the share is higher, but the free body is a smooth 6 mm surface, so a ladder ran.

## Ladders (set a, `scripts/mpqem.py`: the goose's pose-aware half-edge collapse over all 7 clips at 10 Hz, chart guard, texture
guard on the base colour; limits for the fish's 0.338 m length p99 <= 1.01 mm, max <= 5.07 mm; `work/selection_{a,b}.json`,
`review/ladder_sheet_{a,b}.png`)
| ladder | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---:|---|---|---|
| a | r62 / r56 / r50 | 4,786 / 4,666 / 4,544 | 0.24/0.79, 0.28/0.97, 0.33/1.17 (Hit:6) | .9979 / .9995 at r50 | pass / pass / pass |
| b | r44 / **r38** / r32 | 4,422 / **4,300** / 4,178 | 0.40/1.18, **0.49/1.70 (Hit:6)**, 0.68/2.16 (Hit:6) | .9966 / .9992 at r38 | pass / **PASS, picked** / pass |
r38 was picked over the lowest passing r32 (-24.8 %) because it also passes the stricter limit taken from the fish's height
(0.19 m: p99 0.58, max 2.9 mm), which r32 does not (p99 0.68). Two ladders used.

## Candidate build (`scripts/build_cand.sh b_r38`, run with `PROT_PRIMS=0 TIP_BONES=Xtail,Xmouth EXT_BONES=Xjaw`)
`swap_mp.py` -> the fish's own runtime chain: `set_extras.py --opaque-fins` -> `build_lods.py` (snap-fixed builder, the tool's
0.5/0.18/0.06; protected: body soles and top within 2 mm, the Xtail and Xmouth tip vertices, Xjaw extremes, mesh extremes, front-
and rear-most vertex in 8 height bands, corpse contact of Death/Dead: 111 points, body primitive only) -> `shrink_shadow_lods.py`
-> `strip_shadow_fins.py` -> `set_extras.py` (fins MASK). A first build protecting fin points too (183 points) pushed LOD2/LOD3 fin
collapses off their charts (LOD2 fins 82 escaping against the installed 2), so fin points are not protected, as installed.
- UV chart audit (hard gate, `review/uv_audit_b_r38.json`): **LOD0 0 escaping** (body and fins); LOD1/2/3 78+0 / 58+2 / 24+79
  against the installed 79+0 / 92+2 / 40+76 (Blender decimate's own baseline).
- LODs (`review/lod_table_b38.txt`, every frame of every clip): top, width and depth unchanged at every LOD; lowest point per clip
  identical to the installed at every LOD (LOD3 sits 0.5 cm higher than LOD0 in the living clips, exactly as the installed LOD3);
  stretched faces 0. LOD3 is 360 against the installed 332 (the protected points keep 28 more).

## Gates (`scripts/gates.sh`, `review/gates_before/`, `review/gates_b38/`, `review/gates_compare_b38.txt`)
- Floor / lowest point (`extra_clip_gates.py`, swimmer: no foot contact): floor min/max per frame identical in all 7 clips (living
  39.2-40.4 cm, Death -0.0/39.8, Dead -0.0); edge ratio p1/p99/max identical in every clip; bone ratio identical; body-in-body 0.
- Jitter p99 (mm/f2) +1.5 to +7.6 % (Walking 9.12 -> 9.81, Running 17.54 -> 18.66, Hit 49.01 -> 50.70). A sample change:
  `review/jitter_subset_b38.txt` shows the maximum over vertices identical in every clip (Hit 68.05, Running 24.55) and every
  candidate vertex moving exactly like its installed vertex (difference 0); the removed vertices were quiet flank vertices.
- Folds (`fold_measure.py`): folded face-frames 451 -> 416 (Xbody 61 -> 33); over-threshold 812 -> 804.
- Detached 0 (17 components); fin roots still shallow only in Hit as installed (pectorals identical, caudal lobes 4.9/4.6 -> 4.5/3.8
  mm buried). Flat shading 0.01 = 0.01 (fins 0.76 by design); texture quality unchanged (stretch p90 1.08 -> 1.09); winding 0.
- Head orientation gate not re-run: clips and the head vertices are byte-identical.

## Review
Viewer (installed and reduced, 7 clips; a copy of the fish viewer with the focus raised by the swimmer lift and frustum culling off,
so the corpse on the floor is not culled by the lifted rest bounds):
http://127.0.0.1:8912/level_generation/creatures/mm9_fish_reduce_claude/review/viewer/
`run_creature_review.py check`: 14 switches (2 models x 7 clips), 0 failed, 0 console errors.
Sheets read at full size: `review/sheet_face_b38.png` (front close-up, 3/4, true profile, low 3/4, party; installed over reduced;
`review/face_diff_b38.txt`: the only differing pixels are the nape and back behind the head, `review/shots/diff_a_f0.png`; the
head itself is identical), `review/sheet_body_b38_a.png` (Standing front/3-4/back, Walking 3/4, Running side; its Death column
predates the culling fix), `review/sheet_close_b38_a1.png` (flank left, flank right, back and dorsal root from above),
`review/sheet_close_b38_a2.png` (belly and pelvic/anal roots from below, tail stalk in Fidget, nape and gill edge from above-front),
`review/sheet_close_b38_a3.png` (Death end, Dead from above). No visible change at party distance or in the close-ups. Look at, at
close range: the lower outline of the tail stalk in Fidget (`c4x0`: a little straighter) and the back's outline behind the head in
the front view.

## Rerun (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G="../claude_shared/gltf_venv/bin/python -W ignore"
REA_GLB=level_generation/creatures/mm9_fish_reduce_claude/before/mm9_fish.glb REA_NODE=Fish $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py before/mm9_fish.glb
$G scripts/fish_head.py before/mm9_fish.glb 0.085 1
HEAD_BONES=Xmouth,Xjaw FOOT_BONES= SOLE=0 KEEP_PRIMS=FishFin EXTRAS=head $G scripts/animal_sets.py before/mm9_fish.glb Fish a
GLB=mm9_fish.glb NODE=Fish SETS=a REA_HEIGHT_M=0.338 MP_GROUPS= scripts/run_mp.sh a 0.62,0.56,0.50   # and b 0.44,0.38,0.32
PROT_PRIMS=0 TIP_BONES=Xtail,Xmouth EXT_BONES=Xjaw scripts/build_cand.sh b_r38
scripts/gates.sh before/mm9_fish.glb before; scripts/gates.sh export/cand_b_r38/mm9_fish.glb b38; python3 scripts/gate_compare.py b38
REA_NODE=Fish $BL -P scripts/lod_check.py -- $PWD/before/mm9_fish.glb installed   # and the candidate as b38; python3 scripts/lod_table.py installed b38
python3 scripts/make_viewer_manifest.py fish_reduce_b38_20261105 "inst_a=Installed 5,558=before/mm9_fish.glb" "red_a=Reduced b38 4,300=export/cand_b_r38/mm9_fish.glb"
scripts/shots.sh; $G scripts/shot_sheets.py b38; python3 scripts/close_sheet.py b38 a c0 c1 c2
```
After an install, `../mm9_fish_claude/README.md` needs the line "LOD0 reduced post-install on <date> by `mm9_fish_reduce_claude`;
a rebuild from this project must re-run that reduction".
