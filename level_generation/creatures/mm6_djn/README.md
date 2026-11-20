# MM6 Genie — validated, staged only

All 60 unique native images restored for descriptor IDs 544–546 and palettes 739/740/741. Native actions, timings, stored/mirrored views, logical placement and scale are preserved. The missing fidget sheet succeeded with a clearer prompt on 2026-09-13. Final review also repaired missing late-death jewelry and finger-gap matte residue.

Open [review.html](review.html) directly for native/restored playback, variants and mask overlays. Runtime-facing outputs are [manifest.json](manifest.json) and matching base/mask pages in atlas/. Aligned 2x frames, exact prompts, raw outputs, rejected checkpoints, source hashes and deterministic settings are retained. See [review notes](review_notes.md) and [validation](validation.json).

Reproduce from the repository root:

```sh
python3 level_generation/creatures/mm6_djn/process.py
python3 level_generation/creatures/mm6_djn/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py djn
```

Processing starts from raw sheets, applies local matte cleanup and fixed 0.84 tone, then registers the late distant figure and fallen jewelry separately. Masks select enhanced blue skin and green jewels; fixed native luminance LUTs derive purple/red variants. Package rebuilding resets visual acceptance and requires renewed review before updating acceptance.json.

Total decoded base, matching RGBA masks and float32 recolor LUTs: 63,319,000 bytes (60.39 MiB), excluding optional preview pages. The LUT recolor contract needs suitable runtime support or offline variant baking before installation. Everything here remains staged; originals and gameplay were not changed.
