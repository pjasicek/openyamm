# MM9 Dagrell (`mm9_dagrell`, Dagrell / Venomous / Spectre Dagrell) reduction: kept (no useful gain), 2026-11-04

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 87 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:dagrell` (owner dagrell-reduce-20261104; `mm9:dagrell`
was free). Source: the installed `assets_source/worlds/mm9/models/mm9_dagrell.glb` (sha256 cef0f1ca0c18, identical to
`../mm9_dagrell_claude/export/mm9_dagrell.glb`), copied to `before/`. Nothing exported or installed; `../mm9_dagrell_claude/` was only
read. No Meshy, no credits.

**Result: kept.** No ladder step near -15 % passes the stop rule; even -13.4 % fails. The build already decimated this body
(`../mm9_dagrell_claude/scripts/reduce_body.py 0.45 0.6 0.55`: Meshy's 14,920 -> 7,564, `work/reduced_v2.json` there), and it is a
skeleton of 136 thin rigid bone pieces, so every further collapse thins limb bones and ribs, which shows in the silhouette IoU at once.

## Measured first: protected share (`scripts/dagrell_sets.py`, `scripts/explore_dagrell.py`)
One primitive (Dagrell_A; B/C are the same mesh with other ramps), 7,518 faces, 136 pieces. Exact: head and neck pieces (faces
dominated by Xheadpiv / Xjawbase / Xjawpiv / Xnose / XneckB: skull with eye sockets, mandible, teeth, head spikes) 2,843; pieces of at
most 20 faces (teeth, spurs) 442; thin spikes (pieces under 60 faces, shortest extent < 0.3 of the longest) 852; claws and toes
(digit-bone dominated) 332; soles 74: **51.4 %** (3,865). Free: spine, ribs, pelvis, limb bones, feet, tail 3,653, so -15 % needs
those at about 0.70 on top of the build's 0.45.

## Ladders (`scripts/mpqem.py`: the Terror's copy with seam slides, texture guard on the region mask R bone / G spikes and the shared
base colour; limits for 1.866 m (Standing height): p99 <= 5.6 mm, max <= 28 mm, IoU >= 0.98; `work/selection_{a,b}.json`,
`review/ladder_sheet_{a,b}.png`)
| set | groups | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | body one group, head exact, W5 5 | r70 / r65 | 6,422 (-14.6 %) / 6,238 (-17.0 %) | 7.41/17.9 (Jump:0), 8.78/29.9 (Death:63) | .980/.995, .966/.995 | fail |
| b | a + cranium (head pieces behind z 0.8, not XneckB) 0.7, W5 3 | r76 / r72 | 6,510 (-13.4 %) / 6,364 (-15.4 %) | 6.07/16.0 (Crouch:0), 6.76/16.0 | .984/.996, .982/.996 | fail |

At party distance the ladder sheet shows no visible change, but the p99 deviation is 8-30 % over the limit at every useful step.
Not checked: per-bone error attribution (`err_by_bone.py` not run), gates, viewer: nothing reached a candidate.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_dagrell_reduce_claude/before/mm9_dagrell.glb REA_NODE=Dagrell $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/explore_dagrell.py
$G scripts/dagrell_sets.py a; CRANIUM_Z=0.8 $G scripts/dagrell_sets.py b
SETS=a MP_W5=5 MP_GROUPS= scripts/run_mp.sh a 0.7,0.65
SETS=b MP_W5=3 MP_GROUPS=2:0.7 scripts/run_mp.sh b 0.76,0.72
```
Most other scripts are unused copies from the Terror project.
