# MM9 Goat (`mm9_goat`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 83 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:goat` (owner goat-reduce-20261105, released); `mm9:goat` was
free. Source: the installed `assets_source/worlds/mm9/models/mm9_goat.glb` (sha256 89e690994931, identical to
`../mm9_goat_claude/export/mm9_goat.glb`), copied to `before/`. `../mm9_goat_claude/` was only read. No Meshy, no credits.
**Nothing exported or installed; the installed goat stays as it is (7,934 / 3,966 / 1,428 / 476).**

## Body already cut at the build
`../mm9_goat_claude/` decimated the solid body at the build (`reduce_mod.py ... 6500 0.2`, head factor 1.5 in the UV pass):
body edges are 40-58 mm, head edges 10-12 mm. The head bones (Xheadpiv, Xhead, Xjawpiv, Xjaw, ears) weight 5,650 of the
7,934 faces. Unlike the Cow there is no dense head-weighted neck behind the ears: behind z 0.40 the neck is sparse body mesh
(Xneck/Xneckpiv), and the dense head region is horns (Xheadpiv, rigid), ears, cranium, eyes, muzzle, nostrils, lips, the
862-face mouth cavity, jaw and beard (`review/head_plot.png`, by dominant bone).

## Protected share (`scripts/goat_sets.py`)
| set | exact | share | free | -15 % (1,190 tris) needs |
|---|---|---:|---:|---:|
| a: head-weighted skin > 0.5 + 2 rings, eye pieces, beard, hooves + 1 ring, soles | 6,122 | **77.2 %** | 1,812 | **66 % of the free faces** |
| a1: as a, 1 ring | 6,080 | 76.6 % | 1,854 | 64 % |
| b: as a but the back of the skull behind z 0.47 cut (takes horn roots too, `review/head_plot_b.png`; against the brief) | 5,622 | 70.9 % | 2,312 | 51 % |
For comparison the Ram needed 39 % of its free faces and sat on the p99 limit at 45 %.

## One confirming ladder (set a, `scripts/mpqem.py`: the Ram's pose-aware collapse, chart guard 12, texture guard on the base
colour; limits for the 0.963 m height p99 <= 2.89 mm, max <= 14.45 mm; `work/selection_a.json`, `review/ladder_sheet_a.png`)
| step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---:|---|---|---|
| r70 | 7,390 (-6.9 %) | 2.37 / 14.37 (AttackMelee:6) | .9968 / .9979 | pass (max at the limit) |
| r50 | 7,028 (-11.4 %) | 4.61 / 24.93 (Fidget:21) | .9901 / .9960 | fail |
| r34 | 6,792 (-14.4 %; guards stopped at 670 of the 616 target) | 14.66 / 55.75 (AttackMelee:6) | .9644 / .9892 | fail |
The only passing step saves 6.9 %, so the stop rule applies: **kept (no useful gain)**. One ladder used.

## Files
`scripts/` (Ram copies adapted to node Goat, one primitive, no horn primitive, base-colour guard; `goat_sets.py`, `survey.py`,
`head_plot.py` new), `work/` (source.blend, mesh_in.npz, sets, ladder), `review/` (head plots, ladder sheet), `before/mm9_goat.glb`.
