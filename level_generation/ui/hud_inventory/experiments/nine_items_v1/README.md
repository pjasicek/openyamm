# Nine inventory items in one imagegen call

## Adoption into the live queue

Eight cells are now accepted and staged in the separate preview exports. `adoption.json` records the
single retained attempt `00a6085478a74e16b287ef773cb64f08`; this was an explicit historical import,
not another generation call. The exact original prompt/reference/raw were retained, and all source
hashes, registration comparisons and measured landmarks were reviewed. Originals are untouched.

`7item089` remains deferred. `7item089-fitting-v2` fixes the global footprint guard with a uniform
0.99 scale and small translation, but its left outer horn tip remains 3 x2 pixels above the native
landmark. That candidate is not accepted. A targeted imagegen correction should preserve the other
eight accepted cells. The historical benchmark observations below describe the initial candidates.

Requested 2026-09-10 as the next throughput experiment after `eight_items_v1`.
Selected nine distinct, previously unrestored inventory targets: `6helm3`, `6helm4`, `6helm5`,
and `7item089` through `7item094`. Selection checked queue cell state and excluded the prior experiment's
source hashes. Originals and frozen queue jobs remain untouched.

One built-in imagegen call used `reference.png` (960×960, 3×3 cells) and `prompt.txt`.
Tool wall time was 35.3 seconds. Actual output is 1254×1254; extraction uses actual dimensions,
not the requested 1920×1920. All nine items occupy their expected cells without overlap.

`process.py` reuses the existing HUD matte and uniform scale/translation fitting, saving individual
transparent PNGs at exactly 2× each native width and height. Processing and proof creation took
5.74 seconds. These timings exclude preparation and human/agent review.

```sh
python3 level_generation/ui/hud_inventory/experiments/nine_items_v1/process.py
```

`comparison.png` shows original x2 versus restored x2, with light/dark matte previews.
Eight exports pass existing footprint checks. `7item089` fails the alpha-16 footprint/margins guard;
it is explicitly flagged, not accepted. The raw sheet, final comparison and enlarged comparison were
visually reviewed. Smooth detail is present, but some gold, rivets and ornament are more pronounced
than native. Per-item observations and limits are in `review.json`.

All outputs are experimental candidates, not installed or counted as accepted queue assets.
Source hashes, frozen job membership, actual output hash, matte/fitting provenance and registration
reports are retained. This test supports 3×3 batching as practical; it does not measure sustained
throughput or establish that every candidate is production-ready.
