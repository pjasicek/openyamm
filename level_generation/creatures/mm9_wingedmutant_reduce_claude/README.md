# MM9 Winged Mutant (`mm9_wingedmutant`, tiers A/B/C) LOD0 reduction

## Fix pass (2026-11-04 evening): chart-guarded mp85, ready for review — current candidate (below the ~15 % floor)
The s82 candidate below was installed and **rolled back**: 72 of its LOD0 faces (membrane 56, hair 14, body 2) had UV
triangles leaving the painted charts (`work/uv_audit_s82.json`; MeshLab's collapse cannot be guarded per collapse). The fix pass
uses the pose-aware half-edge collapse with the chart guard (`scripts/mpqem.py`, the Dwarf's copy: `MP_CHART=1`, every sample of
a new face's UV triangle on the installed charts; texture guard on the three tier base colours taken from the creature's approved
viewer bakes, `tex_extract.py`; 5-D texture weight `MP_W5=4`). Every output corner is an installed vertex, so positions, UVs,
normals and weights are exact (no mirroring, no weight transfer). Wing back copies are the "lining": the cut front sheet's
surviving faces re-emit their back faces from the exact source twins (`front_of` pairing; the normal-offset prediction missed
by 2-2.5 mm and opened 64 edges). Keep set as s82 (face set, body except feet, claw tips, helper-heavy membrane, knuckles) plus
the hair lock tips (`hair_tips.py 0.03`: 80 tips, 448 faces; ladder b without them shortened locks by up to 52 mm in Hit2).

`KEEP_EXTRA=work/lock_knuckles.npy,work/lock_hairtips_0.03.npy make_sets.py`, `glb_sets.py c`,
`SETS=c MP_GROUPS=1:0.6,3:0.85 MP_W5=4 scripts/run_mp.sh c 0.85,0.82` (group 0 = membrane), `scripts/build_mp.sh mp_c_r85`
(-> `export_mp/mm9_wingedmutant.glb`).

| run | step | LOD0 | all p99 / max mm | non-hair p99 / max | hair p99 / max | IoU / SSIM |
|---|---|---:|---|---|---|---|
| b (no hair tips) | r85 / r80 | 11,205 / 11,057 | 8.71 / 51.7, 9.42 / 51.7 | 4.12 / 11.7, 6.22 / 19.1 | 13.5 / 51.7 | .997/.995, .994/.994 |
| **c** | **r85** | **11,445 (-9.2 %)** | 7.63 / 25.0 | **4.03 / 11.7 (pass)** | 11.7 / 25.0 | **.997 / .995** |
| c | r82 | 11,357 (-9.9 %) | 8.14 / 25.0 | 5.18 / 19.1 (fail) | 11.7 / 25.0 | .994 / .994 |

The guards stop the cut early: hair 2,786 free faces -> 2,120 (target 0.6 = 1,672), membrane at 0.85 (0.82 fails the deviation
rule). **No guarded step saves ~15 %; best -9.2 % (11,445).** The orchestrator may record it as kept.

LODs 11,445 / 5,720 / 2,053 / 834 (installed 12,599 / 6,297 / 2,261 / 861). **UV audit (`review/uv_audit.json`): 0 escaping LOD0
faces in every primitive**; LOD1-3 at or below the installed counts except head LOD2 108 vs 95 and LOD3 62 vs 52 (Blender's
decimate). `same_check.py`/`same_clips.py`: images, materials, variants, skin, nodes and all 13 clips are the installed bytes.
Gates (`review/gates_before/` vs `review/gates_mp85/`): edge stretch min/max identical in every clip, p99 within +0.17
(AttackRanged 1.80 -> 1.97); lowest point identical in every clip; loop seams 0; LOD heights 1.664/1.659/1.610 m as installed,
LOD3 1.541 vs 1.563 m; death-clip floor 0.0 at every LOD (installed LOD2 -2.2, LOD3 -1.9 mm); stretched faces 3 as installed;
detached 0 (31 components); bone lengths, winding 0; flat shading 0.00; texture quality body 52.3 % / stretch 1.17 (installed
1.15), head 47.4 % / 1.43 (1.25); symmetry max 0.61 % (hair only).
Sheets read (installed above): `review/sheet_escapes_{a,b}.png` (the 12 spots where s82 escaped: wrist knuckles, membrane
folds, hair, both sides; identical), `review/sheet_face_c_tex.png` (face pixel-identical, hair tips intact), `review/sheet_body_a_tex.png`,
`review/pair_b_head_q_mp85.png` (viewer). Generated, not opened: the other tiers' escape/face/body sheets and clay versions,
`review/sheet_viewer_*.png`. Viewer: installed and mp85 per tier, 78 switches, 0 errors.

## Superseded: s82 (rolled back, UV chart escapes)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 monster,
relaxed keep set), ledger row 36 of "MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:wingedmutant` (wingedmutant-reduce-20261104). No-retexture branch of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
on the installed `assets_source/worlds/mm9/models/mm9_wingedmutant.glb` (sha256 441ffa7890ae, = `../mm9_wingedmutant_claude/export/`),
copied to `before/` (the rollback source). The creature project was only read. **Not installed. No Meshy credits.**

| | LOD0 | body `Wmut` | wings `Wmut_Wing` (front + back copies) | head `Wmut_Head` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,599 | 1,795 | 4,068 (2,090 + 1,978) | 6,736 | 6,297 | 2,261 | 861 |
| **candidate s82** (`export/mm9_wingedmutant.glb`) | **10,733 (-14.8 %)** | 1,747 | 3,544 | 5,442 | 5,365 | 1,924 | 767 |

Images, materials, textures, `KHR_materials_variants` (every primitive of every LOD and shadow mesh), skin, inverse binds,
nodes and all 13 clips are byte-identical to the installed file (`scripts/same_check.py`: ALL SAME). Only geometry changed.

**Why only ~15 %.** Measured first (`scripts/analyse.py`, `make_sets.py`): the face set (skin 2,366 incl. scalp, eyes 570,
teeth 528, neck bridge 38 = 3,502, 28 %) is exact by rule; the body (1,795) had already been cut to 0.4 at assembly and any
further cut costs centimetres (uniform ladder c: pelvis/spine/thigh misses of 15-20 mm at 0.8); the membranes are driven by
the finger helpers `Yw*piv`/`Yw*mid` (528 faces with a vertex over 0.75 kept). What can go: hair (3,234) and the free
membrane. The orchestrator may call this "kept" against the ~15 % floor; it sits at 14.8 %.

## What is kept, what is cut
- **Mirror symmetric** (`scripts/decimate_sym.py`): the model is exactly symmetric about x = 0 (the user's rework request) and
  body/wing halves share texels, so the +x half of body, wings and feet is decimated and mirrored (source vertices to their
  mirror twins, plane vertices shared, open edges 990 as installed). The **head set's charts are cut differently per side**
  (51 of 169 +x islands have no affine map to the -x layout), so the hair is decimated over both sides as is (not mirrored):
  hair symmetry max 1.33 % of the size (gates `symmetry.log`); body, wings and face stay 0.00.
- **Wing back copies** (1,978, the creature's `add_backfaces.py` offset sheets) are not decimated: they are rebuilt from the
  reduced front sheet the same way (components with an open edge, flipped, 2 mm behind along the normal, same UVs/weights); a
  back vertex whose front vertex is unchanged takes its installed twin exactly.
- Exact: face set (skin, eyes, teeth, neck bridge), the whole body except the feet, claw tips, membrane faces touching a vertex
  the finger helpers weight over 0.75, the wing knuckles (faces within 5 cm of the YwingA-E joints, `knuckle_lock.py`; r82
  without them flattened the wrist knuckle, `review/sheet_body_a_clay.png` history), the one plane face.
- Cut: hair 0.6 (brief range 0.6-0.8, judged visually), free membrane 0.82, feet 0.85.
- Weights (`uv_weights.py`): source vertices exact; new vertices from the source triangle holding their UV within 1 cm, else
  Ebora's piece-aware closest-triangle blend (5,549 UV hits, 191 fallbacks). Normals (`keep_normals.py`, KEEP_ANY): every
  vertex of an unchanged face takes the installed normal: 0 vertices of kept faces differ by more than 1 deg in any primitive.

## Ladder (REA_HEIGHT_M 1.67 bind height: p99 <= 5.01 mm, max <= 25.05 mm; every clip, every 3rd frame, both ways)
The brief judges hair at party distance and in the front close-up, so `eval_split.py` also reports the rule without the hair.

| run | change | step | LOD0 | all p99 / max | non-hair p99 / max | hair p99 / max | IoU / SSIM |
|---|---|---|---:|---|---|---|---|
| c | uniform (body too) | r90 / r80 | 11,791 / 10,995 | 4.38 / 20.5, 6.51 / 20.7 | | | .996/.995, .985/.993 |
| e | hair only | r80 / r60 | 11,951 / 11,303 | 4.54, 7.44 | 0 | 6.87 / 20.5, 10.64 / 32.0 | .999 / .996 |
| f | membrane only | r80 / r70 | 11,971 / 11,667 | 4.84, 8.24 | 5.54 / 18.5, 9.20 / 22.8 | 0 | .987, .981 |
| h | + spar tube kept | r70-50 | 11,339-10,691 | 7.8-12.0 / 96.9 | | | wing tip spike vanished (`review/diag/tip_sheet.png`) |
| n | hair 0.55, membrane | r85 / r80 | 10,675 / 10,515 | 8.52 / 8.76 | 4.33 / 14.2, 5.54 / 18.5 | 12.56 / 32.0 | .989 / .994 |
| p | hair 0.6, feet 0.85 | r82 | 10,691 | 7.75 / 32.0 | 4.90 / 14.3 | 10.64 / 32.0 | .988 / .994 |
| **s** | **p + knuckles kept** | **r82** / r80 | **10,733** / 10,669 | **7.58 / 32.0** | **4.93 / 15.0** (pass) / 6.01 | 10.69 / 32.0 | **.992 / .994** |

Picked **s r82**: the lowest step whose non-hair deviation passes, with the knuckles intact. Error locks from the posed
misses (`err_lock.py`, k/m) fragmented the membrane so MeshLab could not reach its target and moved the error elsewhere.

## Gates (installed -> s82; `scripts/gates.sh`, `review/gates_before/`, `review/gates_s82/`)
| gate | installed | s82 |
|---|---|---|
| edge stretch min / max (every clip) | 0.03-0.174 / 3.96-10.45 | identical in every clip |
| edge stretch p99 (worst clip) | 2.08 | 2.71 (Hit2): a percentile effect, the same ~100 neck-bridge edges over 2x in a smaller head primitive (`stretch_prims.py`, `work/stretch_where.py`); body and wing p99 unchanged |
| loop seams Standing/Walking/Running | 0 | 0 |
| lowest point per clip | Hit2 0.0, others as listed | Hit2 +0.9 mm, AttackMelee +2.7 mm, Running/Walking +4 mm, rest identical |
| LOD heights 0-3 | 1.664 / 1.659 / 1.610 / 1.563 m | 1.665 / 1.660 / 1.607 / 1.563 m |
| LOD min z in Death/Dead/Death2 | LOD2 -2.2 mm, LOD3 Dead +24 mm, Death2 -1.9 mm | 0.0 / 0.0 / +0.6 mm at every LOD (`build_lods.py` floor contacts + `fix_lod_floor.py`: LOD3 had sunk 8.1 cm in Death2) |
| stretched faces >20x (any LOD) | 3 | 3 |
| detached parts | 0 detached (31 components) | 0 detached (31) |
| bone lengths, winding | 0, 0 | 0, 0 |
| flat shading | 0.00 all | 0.00 all |
| symmetry | 0.00 % | body/wing/face 0.00 %, hair max 1.33 % |
| texture quality body / head | 52.3 %, stretch 1.15 / 47.4 %, stretch 1.25, fragments 6.8 % | 51.7 %, 1.28 / 45.2 %, 1.93, fragments 19.0 % (UV-keeping hair collapse; looks the same in the sheets) |

## Review
- Viewer (installed and s82, all three tiers, 13 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_wingedmutant_reduce_claude/review/viewer/
  (`run_creature_review.py check`: 78 switches, 0 console errors). Tier textures are the creature's approved r5 viewer bakes.
- Sheets: `review/sheet_face_{a,b,c}_{tex,clay}.png` (front, 3/4, profile, low 3/4, party, back of head, hair top),
  `review/sheet_body_{a,b,c}_{tex,clay}.png` (full body front/3-4/back, wing front/back, knuckle, flap, attack, corpse),
  `review/sheet_viewer_{a,b,c}.png` (viewer shots), `review/check_s82_face_knuckle.png`; difference maps
  `review/glbclose/diff_<t>_<spot>_<mode>.png`: face skin, eyes and teeth black (unchanged), only hair pixels differ.
- Alternative without the knuckle lock: `work/candidate_r82.glb` (10,693, knuckles flattened; not recommended).

## Install (not run; on the user's OK)
`check_winding.py export/mm9_wingedmutant.glb` (0), `tools/install_model.py export/mm9_wingedmutant.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression and `floor_audit.py --world mm9 --match "MM9 Winged Mutant*"`, then add to
`../mm9_wingedmutant_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_wingedmutant_reduce_claude`; a rebuild
from this project must re-run that reduction". Rollback: `before/mm9_wingedmutant.glb`.

## Reproduce (project folder; Blender and MeshLab under `scripts/cap.sh`)
`REA_GLB=level_generation/creatures/mm9_wingedmutant_reduce_claude/before/mm9_wingedmutant.glb REA_NODE=Wmut`: Blender
`import_source.py`, `dump_mesh.py`, `dump_weights.py`; `python3 scripts/analyse.py` (labels), `knuckle_lock.py 0.05
work/lock_knuckles.npy`, `KEEP_EXTRA=work/lock_knuckles.npy python3 scripts/make_sets.py`, `REA_WEIGHTS=component
REA_GROUP_RATIOS=0:1,1:0.6,2:r,3:0.85 scripts/run_ladder.sh s 0.82` (decimate_sym -> uv_weights -> reduce_ladder ->
compare_ladder), Blender `eval_split.py -- ladder_s.blend Cand_82`, keep mask of unchanged faces (`work/queue_s82.sh`), then
`REA_BLEND=ladder_s.blend REA_KEEP=work/keep_s82.npy scripts/build_export.sh Cand_82` (export_cand -> swap_lod0 ->
keep_normals -> build_lods -> creature shrink_shadow_lods -> carry_variants -> creature fix_winding -> fix_lod_floor ->
check_winding), `same_check.py`, `gates.sh export/mm9_wingedmutant.glb s82`, `viewer_tiers.py export/mm9_wingedmutant.glb s82`,
`make_viewer_manifest.py`, `shots_queue.sh`, `glb_close.py`, `pair_sheets.py`, `viewer_sheets.py`.

## Not checked
In game; the binding regression and floor audit (run after install); LODs only by numbers (no LOD renders); hair in motion only
in the viewer stills (walk, attack, death), not frame by frame; the shadow LODs beyond winding and the floor repair.
