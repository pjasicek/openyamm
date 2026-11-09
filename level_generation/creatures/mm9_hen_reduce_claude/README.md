# MM9 Hen (`mm9_hen`) reduction: candidate b78 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md), ledger row 99 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:hen` (owner hen-reduce-20261105, released); `mm9:hen` was free.
Source: the installed `assets_source/worlds/mm9/models/mm9_hen.glb` (sha256 08e6bd2f559b, identical to
`../mm9_hen_claude/export/mm9_hen.glb`), copied to `before/` (the rollback source). `../mm9_hen_claude/` was only read.
No Meshy, no credits, no repaint. **Not installed.**

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 6,053 | 3,019 | 1,079 | 357 |
| **b78 (`export/cand_b_r78/mm9_hen.glb`, sha256 823db68d7af7)** | **5,141 (-15.1 %)** | 2,565 | 921 | 350 |

Every LOD0 vertex is an installed vertex (half-edge collapse, index buffer swap): positions, normals, UVs, joints and weights are
the installed bytes. Clips (13), skin, nodes, the material (with its specular/metallic extras) and all 3 images are
byte-identical (`same_clips.py`). One skin, no tiers.

## Measured first (`scripts/animal_sets.py`, `work/survey_a.txt`)
The body was decimated at the build (`reduce_body.py 0.3 0.3 0.5`, head x2 texel density): main body 4,127 faces (median edge
15 mm, head 8 mm), three closed tail tufts on XtailA (578 + 578 + 414), eyes (2 x 118), wattles (2 x 54), a 12-face piece.
| set | exact | share | free | -15 % (908 tris) needs |
|---|---|---:|---:|---:|
| a: every separate piece, head-weighted skin (Xhead, Xbeak, beaknode > 0.5: skull, eyes, beak, comb, wattles) + 2 rings, feet + 1 ring, soles 2 cm | 3,495 | 57.7 % | 2,558 | 35 % |
| **b: as a but the three tail tufts free** (head pieces stay exact through their Xhead weight) | 1,913 | **31.6 %** | 4,140 | **22 %** |

## Ladder (set b, `scripts/mpqem.py`: the Ram/Dog pose-aware half-edge collapse over all 13 clips at 10 Hz, chart guard 12,
texture guard on the base colour; limits for the 0.579 m GLB height p99 <= 1.74 mm, max <= 8.69 mm; `work/selection_b.json`,
`review/ladder_sheet_b.png`)
| step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---:|---|---|---|
| r82 | 5,307 (-12.3 %) | 1.49 / 3.30 (Hit2:15) | .9982 / .9966 | pass |
| **r78** | **5,141 (-15.1 %)** | **1.69 / 4.77 (Fidget2:9)** | .9978 / .9962 | **PASS, picked** |
| r74 | 4,977 (-17.8 %) | 1.84 / 4.77 | .9974 / .9957 | fail (p99) |
Cut by part: main body 4,127 -> 3,813, tail tufts 1,570 -> 974 (578 -> 360, 414 -> 254). One ladder used.

## Candidate build (`scripts/build_cand.sh b_r78`)
`swap_mp.py` -> `build_lods.py` (the snap-fixed builder, the tool's 0.5/0.18/0.06; protected: soles within 2 mm, top within
4 mm, the tip vertex of each tail and toe bone, ankle extremes, mesh extremes, the front- and rear-most vertex in 8 height bands,
corpse contact of Death/Death2/Dead: 75 points, worst snap 6e-8 m) -> the hen's own `shrink_shadow_lods.py` and
`drop_lod_slivers.py`. The first build (248 protected points) left LOD3 at 684; the band rule was added after a build without it
put a LOD3 chest vertex 2 cm in front of LOD0 (Death2 sank 2.5 cm). Clips unchanged, so the floor pass is not re-run.
- UV chart audit (hard gate, `review/uv_audit_b_r78.json`): **LOD0 0 escaping**; LOD1/2/3 207/203/75 against the installed
  174/213/102 (Blender decimate's own baseline).
- LODs (`review/lod_table_b78.txt`, every frame of every clip): top 0.579 m and width at every LOD; LOD0's lowest point identical to
  the installed in all 13 clips; LOD1/LOD2 now follow LOD0 within 0.05 cm (installed LOD2 floated up to 0.25 cm, LOD3 up to 0.8 cm);
  LOD3 follows LOD0 in 12 clips, Death2 -0.73 cm against LOD0's -0.38 (installed LOD3 -0.23). Stretched faces 0 at every LOD.

## Gates (`scripts/gates.sh`, `review/gates_before/`, `review/gates_b78/`, `review/gates_compare_b78.txt`)
- Foot floor contact (`extra_clip_gates.py`, all 13 clips): floor min/max per frame identical in every clip (Standing 0.0/0.0,
  Walking -0.0/0.6, Running -0.0/4.8, Death2 -0.4/21.6 cm); lowest point per clip identical (`gates.py`).
- Jitter p99 (mm/f2) within -1 to +3 % (Running 172.0 -> 175.7, Fidget3 80.4 -> 82.7, Death2 102.8 -> 102.4); bone ratio identical.
- Body-in-body pairs lower in 12 clips (Dead 36 -> 31, Sit 67 -> 63), Death2 21 -> 22.
- Edge ratio: min/max equal (Walking max 2.12 -> 2.09, Hit2 2.33 -> 2.17), p99 +0.01-0.04 (larger faces).
- Neck/head and feet folds (`region_gate.py`): identical in every clip.
- Detached 0 (9 components); tail-tuft root lift equal (1.74 -> 1.73, 1.44 -> 1.57, 1.78 -> 1.71 cm); flat shading 0.00;
  texture quality atlas 60.6 % unchanged, stretch p90 1.11 -> 1.12; winding 0. No arms, hands, held props or see-through fix.

## Review
Viewer (installed and reduced, 13 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_hen_reduce_claude/review/viewer/
`run_creature_review.py check`: 26 switches (2 models x 13 clips), 0 failed, 0 console errors.
Sheets read at full size: `review/sheet_face_b78.png` (front close-up, 3/4, true profile, low 3/4, party; installed over reduced;
face box diff 0.00 % in the four close-ups, `review/face_diff_b78.txt`; the max 207 is the viewer label), `review/sheet_body_b78_a.png`
(Standing front/3-4/back, Walking, Running, Death), `review/sheet_close_b78_a1.png` (breast/neck side, neck from above-front,
wing and flank, belly from below), `review/sheet_close_b78_a2.png` (back and tail from the rear-above, tail tuft side in Fidget,
feet). No visible change at party distance. Look at: the tail tufts from the rear-above at close range (`a2` r0: the lobes are a
little softer) and the wing edge in `a1` w0.

## Rerun (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G="../claude_shared/gltf_venv/bin/python -W ignore"
export HEAD_BONES=Xhead,Xbeak,beaknode FOOT_BONES=Xfoot,Xtoe,Xtoe01,Xtoe02,Xfoot01,Xtoe03,Xtoe04,Xtoe05,Xtoepiv,Xtoepiv01,Xtoepiv02,Xtoepiv03,Xtoepiv04,Xtoepiv05
REA_GLB=level_generation/creatures/mm9_hen_reduce_claude/before/mm9_hen.glb REA_NODE=Hen $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py before/mm9_hen.glb; SMALL_FREE=1 $G scripts/animal_sets.py before/mm9_hen.glb Hen b
GLB=mm9_hen.glb NODE=Hen SETS=b REA_HEIGHT_M=0.579 MP_GROUPS= scripts/run_mp.sh b 0.82,0.78,0.74
scripts/build_cand.sh b_r78
scripts/gates.sh before/mm9_hen.glb before; scripts/gates.sh export/cand_b_r78/mm9_hen.glb b78; python3 scripts/gate_compare.py b78
REA_NODE=Hen $BL -P scripts/lod_check.py -- $PWD/before/mm9_hen.glb installed   # and the candidate as b78; python3 scripts/lod_table.py installed b78
python3 scripts/make_viewer_manifest.py b78 "inst_a=Installed (6,053)=before/mm9_hen.glb" "red_a=Reduced b78 (5,141)=export/cand_b_r78/mm9_hen.glb"
scripts/shots.sh; python3 scripts/shot_sheets.py b78; python3 scripts/close_sheet.py b78 a n0 n1 w0 u0   # and r0 t0 h0
```
Install (orchestrator, after the pre-screen): `check_winding.py export/cand_b_r78/mm9_hen.glb` (0), copy it to
`export/mm9_hen.glb`, `tools/install_model.py export/mm9_hen.glb --world mm9`, the `mm9_actor_models_build_every_binding`
regression, `floor_audit.py --world mm9`, and add to `../mm9_hen_claude/README.md`: "LOD0 reduced post-install on <date> by
`mm9_hen_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_hen.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (stills, gates and
the viewer check only); LOD1-3 and shadow meshes by eye (numbers only); the head-angle and gait gates of the creature project
(they read only the clips, which are byte-identical); indoor light; Android.
