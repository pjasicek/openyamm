# MM8 cobble roads — candidates for native review

This is the current36-file cobble set:19 brown-dirt and17 grey-dirt roads.
The12 orange desert stepping-stone paths are a separate, unfinished family.
These files are staged for review, not installed or finally accepted.

## Artwork and fixes

Two straight donors originate in `../v1/`. Their half-offset imagegen repairs reconnect
cut stones; local Poisson insertion preserves about80% of each donor. Both longitudinal
repeat checks pass. The17 other shapes have individual imagegen restorations under
`../v2/raw/`, with native smooth references and the finished donor as a style reference.
Exact prompts, input hashes, cache receipts and retained raw outputs are recorded there.

`../v1/native_reuse_audit.json` measures the shared stone designs across substrates.
Native grey roads differ by about1.4–2.8 RGB MAE in stone interiors after alignment;
some straight/cap shapes have2–4px source offsets. The restored family uses common
finished openings and the appropriate periodic earth substrate.

Stretching straight donor contours into diagonal artwork was rejected: it folded stones
and produced mask holes despite passing tile-edge statistics. That source is retained
under `../v2/rejected/` only as failure evidence. The active compositor quilts finished
donor strips through a minimum-error overlap cut. It penalizes coverage disagreement,
preserves stone shapes and uses a4-authoring-pixel blend across the cut.

Four diagonal shapes still needed local outline painting. Their imagegen edits and solid
coverage guides are in `../v2/outline_repairs/`. Local Poisson insertion changes only the
outer road/contact region, leaving the first8 authoring border pixels and the central
interior protected. The same edits serve both substrates. Coverage follows the guide:
reclassifying dark joints as earth after painting creates false holes.

Grey contact shade uses brightness only. Transferring brown earth's per-channel ratio
created a cyan fringe. Exposed brown earth in the narrow road fringe is replaced with
the grey master and local scalar shade. Stone colour and the main footprint remain.

Export is256px. Directional road artwork extends into the reduction gutter; exposed
earth wraps in its master phase. Wrapping the opposite side of a mixed road tile into
its gutter is not a valid neighbour model.

## Rebuild and evidence

From the repository root:

```sh
python3 level_generation/terrain/mm8/roads/v1/prepare_pilots.py
python3 level_generation/terrain/mm8/roads/v1/compose_pilot.py
python3 level_generation/terrain/mm8/roads/v1/finish_donors.py
python3 level_generation/terrain/mm8/roads/v2/compose.py
python3 level_generation/terrain/mm8/roads/v2/finish_outlines.py
python3 level_generation/terrain/mm8/roads/v2/check.py --version v3
python3 level_generation/terrain/mm8/roads/v3/review.py
```

Retained imagegen inputs are authoritative: do not overwrite them after changing a
dependent source. `prepare_outline_repairs.py` prepares those inputs before generation;
`finish_outlines.py` verifies their source hashes before inserting the saved edits.

`validation.json` currently has724 compatible checks with no failures, one component
and no interior holes for every mask. This only covers the cobble family and its two
substrates. It does not certify all terrain joins, every native placement, camera motion,
hardware performance, or the unfinished stepping-stone/liquid families.

`include_roads.py` in the MM8 project verifies current build/check hashes and copies
these36 candidates into the partial runtime union. `stage_candidates.py` creates the
isolated review stage, preserving production assets. Final installation remains gated
on the complete238-texture goal and native/animation/movement review.
