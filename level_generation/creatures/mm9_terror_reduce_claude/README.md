# MM9 Terror (`mm9_terror`, Amphibious / Desert / Reptilian Terror) reduction: kept (no useful gain), 2026-11-04

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 73 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:terror` (owner terror-reduce-20261104).
Source: the installed `assets_source/worlds/mm9/models/mm9_terror.glb` (sha256 8324935491f2, identical to
`../mm9_terror_claude/export/mm9_terror.glb`), copied to `before/`. Nothing exported or installed; `../mm9_terror_claude/` was
only read. No Meshy, no credits.

**Result: kept.** No ladder step that saves about 15 % passes the stop rule; the mildest steps tried (-11.6 % / -11.8 %) already
fail it. The body was cut to 0.48 at the build (`reduce_body.py`), so every further collapse on the legs and tentacles leaves
1-2 cm chords in the clips.

## Measured first: protected share (`scripts/terror_sets.py`, `review/classes_a.png`)
One primitive (Terror_A; B/C are the same mesh with other ramps), 8,441 faces. Exact: separate pieces 1,549 (4 eyeballs, 12
teeth/fangs, the tongue), the mouth bag 1,156 (head_fix.py cavity, found by its atlas island, `uv_v3_bag.npz`), the face 1,244
(head/jaw-weighted skin in front of z 0.2, every main face within 2 eyeball radii of an eye, within 6 cm of the bag, one ring),
tentacle-tip mouths 297, toe claws 85, soles 211: **53.6 %**. Free: torso, legs and tentacles 3,658, cranium 259.

## Ladders (`scripts/mpqem.py`: Lesser Demon copy with seam slides, texture guard on the region mask R/B/bone and the shared base
colour; limits for 2.934 m: p99 <= 8.8 mm, max <= 44 mm; `work/selection_{a,b,c}.json`, `review/ladder_sheet_{a,b,c}.png`)
| set | groups | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | tentacles 0.6 with seam slides, cranium 0.7, W5 3 | r60 / r50 | 6,899 (-18.3 %) / 6,715 | 15.3/50.3 (Fidget2:18), 22.5/65.6 | .986/.988 | fail |
| b | one group, cranium 0.7, W5 1 | r75 / r68 | 7,449 (-11.8 %) / 7,191 | 9.55/43.9 (Death2:15), 11.5/43.9 | .993/.994 | fail |
| c | calves/feet/toes 0.85, cranium 0.85 | r70 / r62 / r55 | 7,465 (-11.6 %) / 7,259 / 7,077 | 10.3/29.8, 12.0/50.3, 13.9/50.3 | .992/.993 | fail |

Where the error comes from (`scripts/err_by_bone.py`, samples over 8.8 mm, every 3rd frame of every clip): a r60 3.9 % of samples,
spread over thighs, calves, feet, every tentacle chain and the head; b r75 1.3 % (calves 0.35 %, cranium 0.13 % with the 43.9 mm
max, feet, cheek tentacles). No single spot to lock: the cut is too much everywhere at these counts.

Baseline gates of the installed model (for a later attempt): `review/gates_before/` (Terror's gates.py, collapse, seat_check,
detached, flat shading, texture quality, bone length, winding).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_terror_reduce_claude/before/mm9_terror.glb REA_NODE=Terror $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/explore.py
$G scripts/terror_sets.py a; TENT_GROUP=0 $G scripts/terror_sets.py b; TENT_GROUP=0 LEG_GROUP=3 $G scripts/terror_sets.py c
SETS=a MP_SEAM_GROUPS=1 MP_W5=3 MP_GROUPS=1:0.6,2:0.7 scripts/run_mp.sh a 0.6,0.5
SETS=b MP_SEAM_GROUPS=0 MP_W5=1 MP_GROUPS=2:0.7 scripts/run_mp.sh b 0.75,0.68
SETS=c MP_SEAM_GROUPS=0 MP_W5=1 MP_GROUPS=2:0.85,3:0.85 scripts/run_mp.sh c 0.7,0.62,0.55
scripts/gates.sh before/mm9_terror.glb before
```
`scripts/build_lods.py` (Terror protected points with the Blender snap) is written but was not run. Many other scripts are
unused copies from the Gezzampt project.
