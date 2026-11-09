# MM9 Dog (`mm9_dog`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 91 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:dog` (owner dog-reduce-20261105, released); `mm9:dog` was free.
Source: the installed `assets_source/worlds/mm9/models/mm9_dog.glb` (sha256 d637b29e125a, identical to
`../mm9_dog_claude/export/mm9_dog.glb`), copied to `before/`. `../mm9_dog_claude/` was only read. No Meshy, no credits.
**Nothing exported or installed; the installed dog stays as it is (7,177 / 3,582 / 1,256 / 395).**

## Body already cut at the build
`../mm9_dog_claude/scripts/reduce_body.py` decimated the voxelised Meshy body at the build (two passes, head kept denser):
body edges 30-50 mm, head 9-14 mm, ears 10 mm. 981 faces are separate small pieces (46 teeth 460, tongue 100, eyes 40,
claws about 380).

## Protected share (`scripts/dog_sets.py`, `scripts/survey.py`, `review/head_plot.png`)
| set | exact | share | free | -15 % (1,077 tris) needs |
|---|---|---:|---:|---:|
| a: small pieces, head-weighted skin > 0.5 (Xheadpiv, Xhead, Xmouth, Xjawpiv, both ears) + 2 rings, paws + 1 ring, soles 2 cm | 4,789 | **66.7 %** | 2,388 | **45 % of the free faces** |
| a1: as a, 1 ring | 4,735 | 66.0 % | 2,442 | 44 % |
| t: as a, throat under the jaw (y < 0.72, behind z 0.46) cut | 4,701 | 65.5 % | 2,476 | 43 % (gains only 76 faces) |
Unlike the Cow there is no dense head-weighted neck behind the ears: behind the skull the neck is sparse body mesh.

## Ladders (set a, `scripts/mpqem.py`: the Ram's pose-aware collapse, chart guard 12, texture guard on the base colour;
limits for the 0.93 m GLB height p99 <= 2.79 mm, max <= 13.95 mm; `work/selection_{a,b}.json`, `review/ladder_sheet_{a,b}.png`)
| ladder | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---:|---|---|---|
| b | r85 | 6,819 (-5.0 %) | 1.28 / 7.0 (Running:0) | .9971 / .9987 | pass |
| b | r75 | 6,579 (-8.3 %) | 2.80 / 29.3 (Running:0) | .9950 / .9982 | fail |
| a | r60 | 6,221 (-13.3 %) | 4.60 / 29.3 | .9893 / .9965 | fail |
| a | r55 | 6,101 (-15.0 %) | 5.69 / 32.5 | .9865 / .9955 | fail |
| a | r50 | 5,983 (-16.6 %) | 7.37 / 32.5 | .9799 / .9941 | fail |
Error at r60 (`err_by_bone.py`, 2.73 % of samples over the limit) is spread over the whole body (XCENTER, hips, shoulders,
back, tail, legs, each 0.04-0.29 %), so a lock round the worst spot (the Xfleg 29 mm in Running) cannot bring p99 from 4.6 to
2.79; the ladder sheet shows the blockier back and belly outline at r55. The only passing step saves 5.0 %:
**kept (no useful gain)**. Two ladders used.

## Files
`scripts/` (Goat/Ram copies adapted to node Dog; `dog_sets.py`, `survey.py` and `head_plot.py` take HEAD_BONES / EAR_BONES /
HP from the environment; `build_lods.py` and `gates.sh` adapted but not run), `work/` (source.blend, mesh_in.npz, sets,
ladders), `review/` (head plot, ladder sheets), `before/mm9_dog.glb`.
