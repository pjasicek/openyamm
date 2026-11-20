# MM9 Igrid, Wyrde of the Known (`mm9_wyrdold`) reduction: kept, no useful gain (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 4. Lease
`mm9reduce:wyrdold` (owner wyrdold-reduce-20261104). No-retexture branch of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
on the installed r45 (`assets_source/worlds/mm9/models/mm9_wyrdold.glb`, sha256 4f382ac9030c, copied to `before/`).
**Nothing was exported or installed; the creature project `../mm9_wyrdold_claude/` was only read.**

## Why nothing could be cut
LOD0 is 15,101 triangles: body primitive `Igrid` 11,163 + head primitive `IgridHead` 3,938. Part labels come from the creature's own
final rest mesh (`../mm9_wyrdold_claude/work/uv_tex.npz`, matched to the GLB faces exactly, `scripts/glb_parts.py`):

| part | faces | lining twins + rim strips | lined outer faces | rest |
|---|---:|---:|---:|---:|
| robe (shell, hood, sleeves, bodice) | 7,012 | 1,390 + 400 | 1,390 | 3,832 |
| head set (face, coif, eyes) | 3,382 | 26 + 2 | 26 | 3,328 |
| gown (skirt) | 1,462 | 654 + 116 | 654 | 38 |
| hands (MPFB) | 1,470 | | | 1,470 |
| jewel (clasp ribbons, brooches) | 699 | | | 699 |
| braids | 556 | | | 556 |
| legs (shoes, shin tubes) | 520 | | | 520 |

What the brief keeps exactly (face/head set, hands, braids, jewel, soles, linings with their outer faces and rim strips, sleeve ends
within 25 cm of the wrist with the r42-r45 taper, rim, recentred bell, undersleeve tubes, the hood opening round the face, small
pieces; `scripts/make_sets.py`) is 12,118 of 15,098 welded faces. Only 2,980 remain: the robe's torso/back/upper sleeves and
bodice (2,239), the hood away from the face (519) and the shins (222). The creature's own assembly had already reduced the robe to
5k (`assemble_wo.py`), so it has no slack: a cut of its free part loses 1-2.5 cm folds at rest and the bodice's painted gold
swirls blob.

## Ladders (`scripts/run_ladder.sh`; limits for 1.69 m: p99 <= 5.07 mm, max <= 25.4 mm; hood group 75 %, shins 60 %)

| route | step | LOD0 | saving | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---:|---:|---|---|---|
| A (brief: linings kept) | r94 | 14,190 | 6.0 % | 4.96 / 38.4 (Hit 6) | 0.995 / 0.991 | fail (max) |
| A | r92 | 13,888 | 8.0 % | 8.59 / 55.6 (Hit 6) | 0.985 / 0.985 | fail |
| A | r90 | 13,586 | 10.0 % | 16.2 / 70.3 (Hit 9) | 0.975 / 0.978 | fail |
| B (twins over the cut cloth dropped, to be re-derived) | r84 | 12,680 + ~1,050 relined | ~9 % | 4.70 / 34.4 (Hit 18) | 0.997 / 0.992 | fail (max) |
| B | r80 | 12,076 + ~850 relined | ~14 % | 8.82 / 55.4 (Hit 12) | 0.993 / 0.984 | fail |
| B | r78 | 11,774 + ~750 relined | ~17 % | 11.0 / 55.4 (Hit 12) | 0.989 / 0.978 | fail |

Weights by UV (`REA_WEIGHTS=component`, `uv_weights.py`) gave the same errors as nearest-piece weights: the errors are geometry, not
skinning (`probe_err.py`: 12-25 mm at rest in Standing 0 on the sides of the torso under the sleeves, the back and the bodice).
Route A cannot usefully reach 15 % (all 2,980 free faces are 19.7 % of LOD0) and no step passes: the mildest, r94 (6 %), already fails the max error. Route B (which would also break
the brief's "linings exactly") saves under 15 % at its mildest steps once the twins are re-derived, and its steps at 14-17 % fail p99 by
1.7-2.2x (the relining itself, `reline.py`, was therefore not written).

Sheets (read): `review/ladder_sheet_A.png`, `review/ladder_sheet_B.png` (front 3/4, side, front, top; source above each step).

## Result
**Kept (no useful gain)**: the installed r45 stays. Rollback source not needed; `before/mm9_wyrdold.glb` is the untouched copy.

## Scripts
Copied from `../hes_villager_f_reduce_claude/` (exact weights, coincident-seam handling, UV weights); `export_cand.py` uses the
source's lowest point as the floor (Igrid's bind pose has the pelvis at the origin, so the default lift to z = 0 would have flattened
everything below the waist); `decimate_tex.py` takes `REA_DROP_FACES` (route B). New: `glb_parts.py` (creature part and lining labels on
the GLB faces), `make_sets.py` (keep, group and drop sets; `ROUTE=B`).
