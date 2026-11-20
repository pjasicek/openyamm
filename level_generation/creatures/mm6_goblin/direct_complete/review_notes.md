# Goblin ground-contact correction — 2026-09-13

The inherited accepted front checkpoint had 1–2.5 native logical pixels of extra foot clearance. `process.py --front-only` now translates each of its 31 source-name frames down by 2–5 physical pixels, using the native alpha>=128 baseline. The original accepted artwork remains untouched in `direct_front_final/toned_v1`. No AI generation, resizing, per-pose scaling, color change or alteration to raised-foot gait was needed.

The aligned canvas expands downward rather than clipping displaced pixels. Matching masks are rebuilt from the identically positioned art, then crops/atlas pages and the offline viewer are regenerated. The 28 side/rear frames are unchanged. The native corpse alias still shares its canonical death image. Every corrected front frame now has zero baseline error at alpha>=128; the whole family is within 0.5 native pixel. Native palette timing, scale, mirrored views, crop reconstruction, atlas extraction, alpha and mask checks pass; residual spill candidates remain zero.

Inspected `review/ground_fixed_walk.png` against the native walk, confirming the planted foot meets the baseline while the other foot remains raised. Existing full-family art and variants were previously reviewed; this change only translates accepted art by integer pixels. `review/ground_alignment_corrected.json` records all measured frame baselines. The original ground audit's gap finding is resolved.

All MM6 families are installed through `mm6_remaining/install_runtime.py`; shipping package is `assets_dev/engine/sprites_new/mm6_gob`. Originals and the older raw/accepted checkpoints are preserved. See the installation report for runtime validation.
