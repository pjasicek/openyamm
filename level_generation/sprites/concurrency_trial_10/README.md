# Ten-request image-generation timing trial

2026-09-09; built-in imagegen only. First ten confirmed entries in the non-creature CSV.

## Result

- All ten requests submitted within 0.005 seconds; all ten returned images.
- Batch: **272.238 seconds** (4.54 minutes); **27.22 seconds per delivered image**.
- One matching standalone request (32haxe, identical prompt/reference): **31.054 seconds**.
- Ten times that single sample: **310.54 seconds**, implying an **estimated 1.14x** throughput ratio.
- That ratio is not a measured ten-versus-ten speedup. Different assets, service variance and one control limit the comparison.
- Results arrived in approximately 24–32-second increments, consistent with a queued/effectively serial tool/service path.
  The client cannot distinguish tool scheduling from service-side scheduling. Ten simultaneous submissions did not yield ten simultaneous completions.
- Excludes preparation, review, cleanup, model/tool message handling after the result callback and export. Historical serial runs
  did not retain equivalent timings. Do not sum queued request latencies and call that the old serial runtime.

| Completion order | Asset | Seconds since submission |
| ---: | --- | ---: |
| 1 | `32haxe` | 29.120 |
| 2 | `32hsword` | 53.772 |
| 3 | `3amber` | 79.630 |
| 4 | `3ankh` | 111.271 |
| 5 | `3aldnlmp` | 139.631 |
| 6 | `3amulet` | 163.248 |
| 7 | `3apple` | 191.345 |
| 8 | `3belt` | 217.487 |
| 9 | `3axe` | 245.529 |
| 10 | `3bell` | 272.233 |

## Assets and checks

[Dark comparison](review/comparison_dark.png) · [Light comparison](review/comparison_light.png)

All 11 raw outputs (ten jobs and one control) were copied into `raw/`; exact prompts, inspected paletted references,
source hashes and per-job timing metadata are saved. Ten transparent 2x drafts are in `enhanced/`, with native
canvas/pivot metadata in `manifest.json`. Matte extraction, contour decontamination and premultiplied resizing ran.

These are **benchmark drafts**, not installed artwork. The amber gained holes and the apple retained coarse
pixel stepping; those need targeted correction before a full restoration goal accepts them. No extra repair calls
were mixed into the timing sample. Visual quality is a separate gate from a successful tool response.

## Reproduce offline processing

```sh
python3 level_generation/sprites/concurrency_trial_10/process.py
```

This reuses outputs and makes no image-generation calls. `prepare.py` regenerates the ten native references.
Live generation requires the agent built-in tool; use [the scheduling guidance](../PARALLEL_IMAGEGEN.md).

[Machine-readable timings](timing.json) · [Export manifest](manifest.json)
