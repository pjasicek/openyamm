# MM9 Cat (`mm9_cat`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 94 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:cat` (owner cat-reduce-20261105, released); `mm9:cat` was free.
Source: the installed `assets_source/worlds/mm9/models/mm9_cat.glb` (sha256 e432b01323ca, identical to
`../mm9_cat_claude/export/mm9_cat.glb`), copied to `before/`. `../mm9_cat_claude/` was only read. No Meshy, no credits.
**Nothing exported or installed; the installed cat stays as it is (6,968 / 3,484 / 1,254 / 418).**

## Body already cut at the build
`../mm9_cat_claude/scripts/reduce_body.py` decimated the body at the build (head denser): body edges 11-17 mm on the 0.275 m
model, the grafted head 3-5 mm. The head (Xhead dominant 3,476 faces, ears 590, two eyes 496) is half of the mesh.

## Protected share (`scripts/cat_sets.py`, `scripts/survey.py`, `review/head_plot.png`)
| set | exact | share | free | -15 % (1,045 tris) needs |
|---|---|---:|---:|---:|
| a: eyes, head-weighted skin > 0.5 (Xhead, both ears) + 2 rings, paws + 1 ring, soles 6 mm | 4,784 | **68.7 %** | 2,184 | **48 % of the free faces** |
| a1: as a, 1 ring | 4,598 | 66.0 % | 2,370 | 44 % |
| b: as a, back of the head behind the ear roots (z < 0.135) cut | 4,460 | 64.0 % | 2,508 | 42 % |

## One ladder (set a, `scripts/mpqem.py`: the Ram's pose-aware collapse over all 14 clips, chart guard 12, texture guard on the
base colour; limits for the 0.275 m GLB height p99 <= 0.83 mm, max <= 4.12 mm; `work/selection_a.json`, `review/ladder_sheet_a.png`)
| step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---:|---|---|---|
| r80 | 6,530 (-6.3 %) | 0.79 / 3.45 (Death:30) | .9986 / .9969 | pass |
| r65 | 6,204 (-11.0 %) | 1.54 / 4.63 (LieFidget2:81) | .9957 / .9891 | fail |
| r52 | 5,920 (-15.0 %) | 2.52 / 6.13 (LieFidget2:87) | .9865 / .9763 | fail |
Error at r52 (`err_by_bone.py`, 5.2 % of samples over the limit) is spread over the body (front legs, back, hips, tail), with
no spot a lock would fix; the ladder sheet shows a blockier haunch and flank at r52. Set b's extra 324 free faces would lower
the need from 48 % to 42 %, still beyond r65, which already fails p99 by 1.9x. The only passing step saves 6.3 %:
**kept (no useful gain)**. One ladder used.

## Files
`scripts/` (Goat/Ram copies adapted to node Cat; `cat_sets.py`, `survey.py`, `head_plot.py` env-driven; `build_lods.py` and
`gates.sh` (with the cat's `collapse_gate.py`) adapted but not run), `work/`, `review/`, `before/mm9_cat.glb`.
