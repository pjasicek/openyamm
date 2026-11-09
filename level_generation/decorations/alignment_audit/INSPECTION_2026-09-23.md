# Ground-contact inspection — 2026-09-23

Follow-up: the raised supports were corrected and reaccepted; see
[CORRECTIONS_2026-09-23.md](CORRECTIONS_2026-09-23.md). The counts below describe the initial snapshot.

I inspected all 113 accepted grounded appearances in `ground_contact_review.csv` using native/restored
bottom-aligned pairs, then inspected the five largest vertical shifts at full-canvas scale. The per-appearance
disposition is in [inspection_2026-09-23.csv](inspection_2026-09-23.csv). The source/output paths and exact
measurements are in [report.json](report.json); [index.html](index.html) provides live side-by-side proofs.

| Observation | Appearances | Meaning |
| --- | ---: | --- |
| Contact preserved, horizontal base-shape flag | 40 | The visible lower edge remains within one native pixel of its original height. Shape or distribution changed, but this flag does not indicate vertical floating. |
| Small visible base inset, 1.5–2.5 native pixels | 68 | The restored visible and opaque lower edges both end above the native lower edge. Review/correct anchor before claiming native ground contact. |
| Clear visible base inset, 3–4 native pixels | 5 | The raised lower edge is visible in full-canvas comparisons; these should be corrected before installation. |

The five clear cases are `6tree27` (`g17943_v0_s0`, 4 px), `6flower10` (`g17956_v0_s0`, 3.5 px),
`cac13` (`g17973_v0_s0`, 3 px), `plant07a` (`g08182_v0_s0`, 3 px), and `6tree13`
(`g17930_v0_s0`, 3 px). Their acceptance notes record inward lower bounds; exact 2x canvas dimensions and
correct hashes did not remove that inset. In `6tree27` and `6tree13`, the tree roots visibly stop above the
original ground line. The flower bed, cactus and pot similarly sit above their original lower edge.

The 68 smaller insets include repeated animation phases (for example `flamb00`–`flamb05`, `ckfyr00`–`ckfyr05`,
and `brnrock0`–`brnrock5`). They are measurable placement differences, not automatically broken artwork.
Correct a shared sequence consistently; do not shift frames independently or stretch foreground bounds. For a
static output whose art and top margin allow it, a deterministic whole-image downward translation is preferable
to another image-generation call. Recheck clipping, the source-relative center, hashes and acceptance after any
correction. This inspection changed no exported PNGs or queue acceptance state.

The audit compares asset canvases, not the terrain and placement of every map instance. It also does not judge
pixelation or texture quality. A final map capture remains necessary if exact in-game seating is required.
