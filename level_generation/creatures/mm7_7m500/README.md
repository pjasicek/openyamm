# MM7 ambient cat — staged restoration

Open [viewer.html](viewer.html) directly for native/restored animation, all eight view aliases and light/dark review.

All **51 native unique frames** are restored, including 5 unused walk-e poses.
Unused art is exported without inserting it into the descriptor-defined seven-frame walking timeline.
Five stored standing/walking views and native collapse/corpse poses retain their source placement.
The original logical canvas is [256, 256]; pivot is [128.0, 256]; export scale is exactly 2×.
Native action reuse, 125 ms frame timings, mirror flags and descriptor bindings are recorded in the manifest.

An ordinary slender dark charcoal-black short-haired cat, faint smoky gray-brown fur markings, green eyes, pointed triangular ears, long slim legs and a long downward-curving tail. Preserve its narrow feline face, erect alert posture and very dark original tonal weight; no white markings, collar or accessories.

Seven accepted imagegen sheets supply base artwork once. Exact prompts, native references, accepted identity crops,
raw outputs and selection provenance remain in `prompts/`, `references/`, `raw/` and `generation.json`.
Raw dimensions used: [(1541, 1020), (1542, 1020), (1888, 833)]. Physical 2× output is resampled from generated detail, not native nearest-neighbor art.

A fixed RGB multiplier of 0.82 is applied to every pose. Magenta extraction estimates edge alpha, locally removes
confirmed fringe color, and resizes in premultiplied alpha. Common source-window inversion and native alpha baseline
translation preserve logical placement without individually stretching silhouettes. `processing_settings.json` and
`registration.json` preserve the exact settings and per-frame transforms.

All native descriptor appearances share palette 545. The matching R8 masks are zero and every variant is an exact
base bypass; no recolored art was independently generated. Base RGBA8 plus mask R8 use
**12,943,360 bytes (12.34 MiB)** decoded including packing;
page size is [1024, 2528]. Preview images are excluded from runtime memory totals.

Visual review covers every native/restored pose in [all-frame comparisons](review/all_comparison.png), native walking
and collapse sequence order, mirrored walking placement in [viewer capture](review/viewer_walk.png), and
[worst light/dark contour crops](review/edge_closeups.png). No broad magenta halo or clipped anatomy was found.
Source hashes, complete coverage, reversible crops, exact atlas extraction, native timelines and zero-mask/alpha
checks pass [validation.json](validation.json). The reviewed artifact hashes are in `review/acceptance.json`.

Reproduce offline (run from repository root):

```sh
python3 level_generation/creatures/mm7_ambient/prepare.py mm7_7m500
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_7m500 --tone 0.82
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_7m500
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_7m500
```

Limitations: fine fur/feather detail and small anatomy differences are interpretations of native pixels.
Thin-feature opacity is estimated from one matte; exact subpixel opacity cannot be recovered.
Keep staged; gameplay installation is separate work.
