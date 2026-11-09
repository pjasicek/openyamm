# MM9 Basilisk (`mm9_basilisk`, Basilisk / Fibrase Basilisk / King Basilisk) reduction: kept, no useful gain (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 77 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:basilisk` (owner basilisk-reduce-20261104).
Source: the installed `assets_source/worlds/mm9/models/mm9_basilisk.glb` (sha256 dfa6cf2385d6, identical to
`../mm9_basilisk_claude/export/mm9_basilisk.glb`), copied to `before/`. No Meshy, no credits, nothing exported or installed;
`../mm9_basilisk_claude/` was only read. **Result: kept** (LOD0 8,132 / 4,065 / 1,441 / 462 unchanged).

## Why
The creature's own build already decimated the Meshy body to 0.5 (head 0.7) after weighting (`reduce_body.py`, 15,606 -> 8,132),
so body, legs and tail are large faces on a curved surface: every further vertex removed moves the surface by several mm.

## Measured first: protected share (`scripts/survey.py`, `scripts/basil_sets.py`, `review/classes_f.png`)
One primitive (`Basilisk_A`, tiers by region ramps), 27 components: the body (7,016 faces) and 26 eye/teeth/gum pieces (1,116).
Exact (set f, 39.5 %): the pieces, the whole jaw (lower jaw, mouth floor, throat spike, lower frill plates: 537), the face in front
of z 1.42 (snout, nostrils, lips, eyes and lids, brows: 580), the two crown horns with their bases (195), claws (red-mask toe
faces: 682), soles (63) and an error lock of 131 faces. Free: body/legs/tail/neck 2,806 (ladder ratio), toes 1,213 (0.8, seam
slides), frill plates 681 (0.8), cranium/neck top 218 (0.75). A 15 % cut needs ~1,220 faces, i.e. ~25 % of the free faces.

## Route and ladders (pose-aware `scripts/mpqem.py`: the Lesser Demon's copy with seam slides, texture guard on the region mask and
## the shared base colour; every vertex an installed vertex). Limits for the 1.125 m standing height: p99 <= 3.38 mm, max <= 16.9 mm
| label | change | step | LOD0 | p99 / max mm (worst) | |
|---|---|---|---:|---|---|
| a | claws any corner, face z 1.36; toes .7, frill .8, cranium .75 | r65 / r55 / r45 | 6,626 / 6,334 / 6,226 | 11.7/41.6, 18.7/45.9, 27.8/115 | fail |
| b | a + seam slides on the body | r90 / r80 / r75 | 7,352 / 7,060 / 6,916 | 5.16/30.3, 6.46/30.3, 7.16/30.3 (AttackMelee, front foot) | fail |
| c | body only | r90 / r80 / r70 | 7,842 / 7,550 / 7,260 | 2.53/30.3, 5.21/30.3, 7.23/30.3 | fail (max at r90) |
| d | frill .8 + cranium .75 only | r100 | 7,932 (-2.5 %) | 0.81/12.2 | pass |
| e | toes .8 only | r100 | 7,938 (-2.4 %) | 0.87/16.0 | pass |
| f | claws by centroid, face z 1.42, horns kept, error lock (`keep_extra_e90`), toes/frill .8, cranium .75 | r90 / r85 / r80 | 7,416 / 7,276 / 7,136 | 4.38/15.5, 5.07/19.1, 5.84/19.4 | fail |
| g | MeshLab texture-aware collapse (texture weight 4) on set f | r90 / r85 / r80 | 7,314 / 6,908 / 6,502 | 6.1/50.0, 8.2/50.0, 11.2/50.0 | fail |

The error sits on legs, feet and flanks in every clip, rest pose included (`region_error.py` on a r65: 449 source vertices over
3.4 mm at Standing:0, spread over the leg pivots, XCENTER, head); no lock set fixes a spread error. The best passing combination
(d + e plus a body step under 0.9) is about -6 %. For reference only: the 3.5 m body length would allow p99 10.5 mm, where a r65
(-18.5 %) is still just over; the MM8 Thunder Lizard (`mm8_m516_reduce_claude/`) set the precedent of judging by standing height.

## Files
`work/survey.npz`, `work/glb_sets_{a,f}.npz`, `work/selection_{a..g}.json`, `work/mp_*.log`, `work/compare_*.log`,
`review/ladder_sheet_{a,b,c,f}.png`, `review/classes_{a,f}.png`. Many scripts in `scripts/` are copies from the Gezzampt and
Lesser Demon projects with the names replaced; only `survey.py`, `basil_sets.py`, `class_view.py`, `tex_extract.py`, `mpqem.py`,
`run_mp.sh`, `run_ladder.sh`/`decimate_tex.py` (`REA_TEXW`), `region_error.py`, `probe_err.py`, `err_lock.py` and `ledger_row.py`
were used.

## Not checked
No candidate was built, so no gates, LODs, viewer or face sheets; the ladder renders (`review/ladder/`) were not read beyond
the numbers.
