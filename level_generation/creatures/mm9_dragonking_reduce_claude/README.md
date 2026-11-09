# MM9 Dragon King (`mm9_dragonking`) LOD0 reduction: kept (no useful gain), 2026-11-05

Ledger row 35 of "MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) (prio 3 unique boss; user 2026-11-05 "do all").
Brief: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and the documents it names.
Lease `mm9reduce:dragonking` (released); the creature's `mm9:dragonking` lease was free and the creature project was only read.
Source: the installed `assets_source/worlds/mm9/models/mm9_dragonking.glb` (sha256 87f447240d7a), copied to `before/`.
**Nothing exported or installed; the installed model stays as it is. No Meshy credits.**

## Result
No step that passes the ladder's stop rule saves ~15 %. Three pose-aware ladders (the brief's limit) were run; the best passing
step is below -12.8 % (c r65 already fails the p99 rule by 7 %), and the steps that reach -15 % miss p99 by 38 % or more.

## Protected share (measured first)
`scripts/analyse.py`, `scripts/face_info.py`, `scripts/dk_sets.py`:
- head primitive `DragonKing_Head` 5,242 faces (head, horns, frills, eyes, 21 teeth, mouth cavity): kept whole, 41.4 % of LOD0;
- body primitive 7,433 faces in one connected surface (body, wing arms and membranes) plus four small wing-claw pieces;
  kept faces: neck seam/head-set border (0.15 units) 71, claws and horns (class map 4) 129, floor contact in any pose of any
  clip (within 0.05 of that pose's lowest point: feet, corpse side, wing tips on the downstroke) 735, wing attachment (vertices
  with wing and non-wing weight > 0.05) 340, helper-bone vertices (Ydbase*, Ywspanpiv*, Ybpart*: no rigid weights, summed
  weight >= 0.25) 70, rest extremes and spike/claw tips (angle sum < 250 deg) 314;
- protected share 52.9 % of LOD0 (57-58 % with the error locks of ladders b and c). UV/normal seams lock a further 3,495 of
  6,708 welded vertices unless seam slides are allowed (ladder c). To reach -15 % the body alone must lose about 26 %.
The body had already been reduced at the build (`reduce_body.py` 0.8 / 0.6 / 0.7 / 0.65 from 15,971).

## Ladders (`scripts/mpqem.py`, `scripts/mpqem2.py`; limits for an 18.2-unit model: p99 <= 54.6 mm, max <= 273 mm, every clip)
Pose-aware half-edge collapse (315 poses, every clip at 10 Hz), chart guard (MP_CHART=1) and the UV audit's own chart test on
every new face (MP_AUDIT=1, the Skeleton's), texture guard on the body base colour, MP_W5 4. Every output corner is an installed
vertex. Groups: 0 skin, 2 wing skin (spars), 3 membrane.

| ladder | sets / groups | step | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | a; wing 0.7, membrane 0.6 | r70 | 10,841 (-14.5 %) | 79.15 / 423.6 | .994 / .994 | fail |
| a | | r60 | 10,487 (-17.3 %) | 93.28 / 423.6 | .992 / .993 | fail |
| b | a + error lock 150 mm (637 faces); wing 0.8, membrane 0.7 | r60 | 11,019 (-13.1 %) | 68.68 / 264.4 | .993 / .996 | fail |
| b | | r50 | 10,927 (-13.8 %) | 97.56 / 484.8 | .989 / .994 | fail |
| c | a + error lock 200 mm (559 faces); seam slides on all groups; wing 0.8, membrane 0.75 | r65 | 11,051 (-12.8 %) | 58.32 / 217.4 | .994 / .996 | fail |
| c | | r55 | 10,727 (-15.4 %) | 75.18 / 217.4 | .993 / .995 | fail |
| c | | r45 | 10,651 (-16.0 %) | 91.25 / 311.8 | .991 / .994 | fail |

Where the error sits (`scripts/err_regions.py`, removed vertices over every clip at 5 Hz):
- a r70: the membrane at 0.6 moved up to 451 mm (p99 255; the Meshy membrane is wavy, not a flat sheet);
- b r60: the membrane is in range (max 193 mm), and the skin at 0.6 is the limit: p50 34 / p99 123 / max 278 mm. The scaly
  body relief is real geometry, and the guards stop the skin near 0.6 (b r50 removed only 92 more faces, max 485 mm).
Sheets: `review/ladder_sheet_{a,b,c}.png` (read: no visible silhouette change at full-body distance; the stop rule fails on
surface deviation, not on the silhouette).

## Not done (stop rule)
No candidate was exported, so there were no LODs, UV audit, gates, close-up sheets or reduction viewer. The baseline gates of the
installed model are in `review/gates_before/` (stretch, floor, seams, detached 0, flat 0.04, winding 0, bone 0, texture quality,
LOD bounds, wing attachment anchors 202, kept-vertex jitter maxima), for a later attempt. `review/viewer/` holds only the
copied page (no manifest). A later attempt would need a different route, such as rebuilding the membranes low-poly with a
projection bake or accepting a looser deviation for this one-off boss; both are the user's call.

## Reproduce (project folder)
```sh
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"; BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
(cd ../../.. && REA_GLB=level_generation/creatures/mm9_dragonking_reduce_claude/before/mm9_dragonking.glb REA_NODE=DragonKing \
  level_generation/creatures/mm9_dragonking_reduce_claude/scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 \
  -P level_generation/creatures/mm9_dragonking_reduce_claude/scripts/import_source.py)
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/face_info.py; $G scripts/dk_sets.py a
SETS=a MP_GROUPS=2:0.7,3:0.6 scripts/run_mp.sh a 0.7,0.6
$G scripts/err_regions.py work/mp_a_r60.npz a 5; $G scripts/err_regions.py work/mp_a_r70.npz a 5
$G scripts/err_keep.py errA 150 err_mp_a_r60.npz err_mp_a_r70.npz; $G scripts/dk_sets.py b errA
SETS=b MP_GROUPS=2:0.8,3:0.7 scripts/run_mp.sh b 0.6,0.5
$G scripts/err_keep.py errAB 200 err_mp_a_r60.npz err_mp_a_r70.npz err_mp_b_r60_copy.npz err_mp_b_r50.npz; $G scripts/dk_sets.py c errAB
MPQEM=mpqem2.py MP_SEAM_GROUPS=0,2,3 SETS=c MP_GROUPS=2:0.8,3:0.75 scripts/run_mp.sh c 0.65,0.55,0.45
scripts/gates.sh before/mm9_dragonking.glb before
```
