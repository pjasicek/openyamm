# Native diagonal reconstruction v8

Rebuilds `drsrne1/2`, `drsrnw1/2` and their `gdrd` counterparts from original128px footprints and stone structure. Generated artwork supplies bounded surface detail only. No optical flow, geometric warp or transplanted straight-road strip is used.

Built-in imagegen produced four images. Exact prompt: `prompts/native_restoration.txt`; input masks and source guides: `inputs/`; retained generated outputs and hashes: `raw/` and `generation.json`.

Reproduce in order: `prepare_native.py`, `compose.py`, `match_boundaries.py`, `fixtures.py`, then `../v2/check.py --version v8`. Composition resets to retained v7 inputs before reconstruction; boundary correction runs once on fresh composition.

Contact shading is separate from coverage. Native endpoint RGB samples are averaged per axis and dirt family; a12px smooth additive colour correction makes all open road boundaries compatible without moving stone coordinates. This also changes the border of28 other road textures; their232px square interiors remain identical to v7. This is a colour compromise at endpoints, not exact preservation of every boundary pixel.

The initial uncorrected native reconstruction has a visible diagonal colour line in `captures/mm8_diagonal_v8_native_b.png`; it is not the delivered candidate. The corrected candidate is frozen in `/tmp/openyamm-mm8-terrain-review/diagonal_v8_boundaries` and named `boundaries`/`walk` in the captures.

Review `assembled_paths.png`: native / rejected v7 / reconstruction, both directions. The original irregular stone outlines remain; this is intentionally more faithful and less aggressively redrawn than v7. A passing seam metric alone does not establish visual acceptance. See `visual_review.json` for delivered hashes, evidence and limitations.
