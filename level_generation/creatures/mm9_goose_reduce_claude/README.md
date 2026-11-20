# MM9 Goose (`mm9_goose`) reduction: candidate a54 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md), ledger row 105 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:goose` (owner goose-reduce-20261105, released); `mm9:goose` was
free. Source: the installed `assets_source/worlds/mm9/models/mm9_goose.glb` (sha256 3e80190e90fb, identical to
`../mm9_goose_claude/export/mm9_goose.glb`), copied to `before/` (the rollback source). `../mm9_goose_claude/` was only read.
No Meshy, no credits, no repaint. **Not installed.**

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 5,788 | 2,894 | 1,040 | 346 |
| **a54 (`export/cand_a2_r54/mm9_goose.glb`, sha256 aaa5fd8cc465)** | **4,414 (-23.7 %)** | 2,206 | 794 | 264 |
| fallback a66 (`export/cand_a_r66/mm9_goose.glb`, sha256 36230f8a0970; built, UV audit 0, not gated) | 4,772 (-17.6 %) | 2,386 | 858 | 286 |

Every LOD0 vertex is an installed vertex (half-edge collapse, index buffer swap): positions, normals, UVs, joints and weights are
the installed bytes. Clips (9), skin, nodes, materials (region mask and ramps), `KHR_materials_variants` (goose_a, goose_b, carried
to every LOD and shadow mesh by `carry_variants.py`) and all 4 images are byte-identical (`same_clips.py`).

## Measured first (`scripts/animal_sets.py`, `work/survey_a.txt`)
The body was decimated at the build (`reduce_body.py 0.3 0.6 0.5`): body edges 18-27 mm, the head 5 mm, feet and webs 10-11 mm;
eyes are two 90-face pieces. Set a: eye pieces, head-weighted skin (Xhead, Xbeak > 0.5: skull, eyes, bill, nostrils) + 2 rings,
feet and webs (dominant Xfoot/Xtoe*) + 1 ring, soles within 2 cm: exact 2,801 = **48.4 %**, free 2,987 (body, neck, wings, tail);
-15 % (868 tris) needs **29 %** of the free faces (1 ring: 47.5 % / 29 %).

## Ladders (set a, `scripts/mpqem.py`: the Ram/Dog pose-aware half-edge collapse over all 9 clips at 10 Hz, chart guard 12, texture
guard on the base colour and the region mask; limits for the 0.82 m GLB height p99 <= 2.46 mm, max <= 12.3 mm;
`work/selection_{a,a2}.json`, `review/ladder_sheet_{a,a2}.png`)
| ladder | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---:|---|---|---|
| a | r76 / r71 / r66 | 5,070 / 4,922 / 4,772 | 1.02/5.57, 1.20/5.57, 1.40/5.57 (Fidget:39) | .9983 / .9960 at r66 | pass / pass / pass |
| a2 | r60 / **r54** / r48 | 4,592 / **4,414** / 4,234 | 1.64/5.57, **1.83/5.57 (Fidget:39)**, 2.27/5.95 (Running:3) | .9977 / .9954 at r54 | pass / **PASS, picked** / pass |
r54 was picked over the lowest passing r48 (-26.8 %, p99 at 92 % of the limit and its worst moved to Running) for margin; the
viewer close-ups of r66 and r54 show the same small softening (`review/sheet_close_r66_vs_r54.png`), so the less cut step buys
nothing visible. Two ladders used.

## Candidate build (`scripts/build_cand.sh a2_r54`)
`swap_mp.py` -> `build_lods.py` (the snap-fixed builder, the tool's 0.5/0.18/0.06; protected: soles within 2 mm, top within 4 mm,
the tip vertex of Xtail and both Xtoea, ankle extremes, mesh extremes, the front- and rear-most vertex in 8 height bands, corpse
contact of Death/Dead: 54 points) -> the goose's own `shrink_shadow_lods.py` -> `carry_variants.py`. Clips unchanged, so the
floor pass is not re-run.
- UV chart audit (hard gate, `review/uv_audit_a2_r54.json`): **LOD0 0 escaping**; LOD1/2/3 165/165/71 against the installed
  113/170/107 (Blender decimate's own baseline).
- LODs (`review/lod_table_a54.txt`, every frame of every clip): top 0.807 m at every LOD; LOD0's lowest point identical to the
  installed in all 9 clips; LOD1 within 0.02 cm of LOD0; LOD2 as the installed LOD2 (AttackMelee -0.31, Running -1.09 cm, 0.13 below
  LOD0) and Dead 0.00 (installed +0.12); LOD3 within 0.05 cm of LOD0 except Death -0.44 and Running +0.20 cm against LOD0's
  -0.10 / -0.96 (installed LOD3 0.00 / -0.41; installed LOD3 floated +0.1-0.3 cm in the other clips). Stretched faces 0 at every LOD. No LOD vertex lies more
  than 1.1 mm outside LOD0's bounds.

## Gates (`scripts/gates.sh`, `review/gates_before/`, `review/gates_a54/`, `review/gates_compare_a54.txt`)
- Foot floor contact (`extra_clip_gates.py`, all 9 clips): floor min/max per frame identical in every clip (Standing -0.0/0.0,
  Walking -0.0/1.1, Running -0.6/2.6 cm); lowest point per clip identical (`gates.py`).
- Jitter p99 (mm/f2) within +0.0 to +2.4 % (Walking 54.3 -> 55.6, Running 297.0 -> 298.3); bone ratio identical; body-in-body 0 = 0.
- Edge ratio: min/max identical, p99 -0.04 to +0.07 (Walking 1.48 -> 1.56).
- Folds (`fold_measure.py`): folded face-frames 9,364 -> 5,949 (XneckA Fidget 1,302 -> 514, Xback Fidget 642 -> 371); faces over the
  stretch threshold 25,707 -> 28,872 (fewer, larger faces).
- Detached 0 (3 components); flat shading 0.01 -> 0.00; texture quality atlas 53.0 % unchanged, stretch p90 1.11 -> 1.12; winding 0.
  No arms, hands, held props or see-through fix.

## Review
Viewer (installed and reduced, both tiers, 9 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_goose_reduce_claude/review/viewer/
`run_creature_review.py check`: 36 switches (4 models x 9 clips), 0 failed, 0 console errors.
Sheets read at full size: `review/sheet_face_a54.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers, installed over
reduced; face box diff 0.00 % in every close-up, `review/face_diff_a54.txt`), `review/sheet_body_a54_{a,b}.png` (Standing
front/3-4/back, Walking, Running, Death), `review/sheet_close_a54_{a,b}1.png` (neck side, neck from above-front, wing and flank,
belly from below), `review/sheet_close_a54_{a,b}2.png` (back from the rear-above, tail in Fidget, feet),
`review/sheet_close_r66_vs_r54.png`. No visible change at party distance. Look at, at close range: the back between the wings from
the rear-above (`a2` r0: the shoulder relief is a little softer) and the flank crease under the wing tip (`a1` w0: a sharper
small shadow wedge).

## Rerun (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G="../claude_shared/gltf_venv/bin/python -W ignore"
REA_GLB=level_generation/creatures/mm9_goose_reduce_claude/before/mm9_goose.glb REA_NODE=Goose $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py before/mm9_goose.glb   # keep only work/tex_Goose_A_{B,M}.png
HEAD_BONES=Xhead,Xbeak FOOT_BONES=Xfoot,Xtoea,Xtoeb,Xtoec,Xfoot01,Xtoea01,Xtoeb01,Xtoec01 $G scripts/animal_sets.py before/mm9_goose.glb Goose a
GLB=mm9_goose.glb NODE=Goose SETS=a REA_HEIGHT_M=0.82 MP_GROUPS= scripts/run_mp.sh a 0.76,0.71,0.66   # and a2 0.6,0.54,0.48
scripts/build_cand.sh a2_r54
scripts/gates.sh before/mm9_goose.glb before; scripts/gates.sh export/cand_a2_r54/mm9_goose.glb a54; python3 scripts/gate_compare.py a54
REA_NODE=Goose $BL -P scripts/lod_check.py -- $PWD/before/mm9_goose.glb installed   # and the candidate as a54; python3 scripts/lod_table.py installed a54
$G scripts/viewer_tiers.py before/mm9_goose.glb inst; $G scripts/viewer_tiers.py export/cand_a2_r54/mm9_goose.glb red   # then make_viewer_manifest.py a54 ...
scripts/shots.sh; TIERS=ab python3 scripts/shot_sheets.py a54; python3 scripts/close_sheet.py a54 a n0 n1 w0 u0   # and r0 t0 h0, tier b
```
Install (orchestrator, after the pre-screen): `check_winding.py export/cand_a2_r54/mm9_goose.glb` (0), copy it to
`export/mm9_goose.glb`, `tools/install_model.py export/mm9_goose.glb --world mm9`, the `mm9_actor_models_build_every_binding`
regression, `floor_audit.py --world mm9`, and add to `../mm9_goose_claude/README.md`: "LOD0 reduced post-install on <date> by
`mm9_goose_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_goose.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (stills, gates and
the viewer check only); LOD1-3 and shadow meshes by eye (numbers only); the a66 fallback's gates and LOD table; the orientation,
gait and jitter gates of the creature project (they read only the clips, which are byte-identical); indoor light; Android.
