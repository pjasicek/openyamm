# MM8 desert stepping paths

Twelve 256px runtime candidates restore the separate brown stepping stones used by
Alvar (`out04`). These are intentionally disconnected stone faces on orange earth.
Do not turn their masks into continuous cobble-road envelopes or fill the earth gaps.

`generation_receipts.json` records 24 built-in imagegen outputs: one restored artwork
and one silhouette extraction for each native tile. Exact prompts, frozen input
references, cache paths and copied raw output hashes are retained. The compositor
verifies those hashes before building. Raw generated earth is not used: exposed soil
comes from the accepted `masters/v1/materials/plains.png` at the same tile phase.
Generated stone paint is matched to native face colour statistics, registered by broad
forms, and combined with native-derived contact shading around each individual stone.
Each stone interior is filled independently; the native stone counts remain 8–12 per
tile. Some outlines are slightly rounder/inset than the original blur.

A first family check found clipped dark contact shadows on `plrdne1` west and
`plrdnw1` south. Both physical masks stop inside the tile, but faint antialiasing was
mistaken for a crossing face. The compositor now distinguishes physical coverage
from its antialiasing tail before meeting the unshaded periodic earth at the boundary.
No stone is removed and no soil gap is filled to make the checks pass.

The current validation covers:

- All 12 names, 256px sizes, reviewed native stone counts and hole-free individual faces.
- 338 ordered shared-earth edge checks, including the plains master: zero failures.
- All 84 native neighbour pairs touching these paths, at 666 Alvar placements: zero
  RGB continuity failures. This includes adjacent sand-transition candidates.
- Visual inspection of every native/raw/composite/mask comparison and all 12 repeated
  layouts. Cap and turn self repeats screen soil continuity, not connected path design.

See [the review gallery](index.html), `offline_review.json` and `validation.json`.
`pilot_validation.json`, `pilot_repeats.png`, `preliminary_pairs.json` and
`edge_diagnostic.png` are historical diagnostics; they do not describe the latest
family build. Numerical continuity alone does not certify stone shape, all native
perspectives, mip behaviour or movement. Native capture review is recorded separately.

Reproduce from the repository root:

```sh
python3 level_generation/terrain/mm8/roads/stepping_v1/compose.py
python3 level_generation/terrain/mm8/roads/stepping_v1/check.py
python3 level_generation/terrain/mm8/roads/stepping_v1/prepare_native.py
python3 level_generation/terrain/mm8/stage_candidates.py --grey-family --stepping-paths
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm8/capture_native.py stepping_ew stepping_ns_south --quality x1
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm8/capture_native.py stepping_ew stepping_ns_south --quality x2
```

The virtual screen size is required by the capture helper's fixed menu coordinates;
the default Xvfb screen crops the menu and cannot start the review save. The staged
pack has 194 PNGs, with both grey-family and stepping-path overrides. Production
assets are untouched. Final integration and controlled flat/movement review remain
part of the full MM8 goal; these are candidates, not a completed terrain pack.
