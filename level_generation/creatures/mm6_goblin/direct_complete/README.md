# MM6 Goblin — complete direct restoration

Open [review.html](review.html) directly in a browser. It compares native and enhanced art, with action, angle,
palette, frame stepping, background, mask and crop controls. The art package retains its offline source manifest.
An explicit export is now available in the [isolated New Sorpigal playtest](../../mm6_peasants/PLAYTEST.md),
without replacing development assets.

The [creature-restore skill](../../../../.agents/skills/creature-restore/SKILL.md),
[atlas pipeline](../../SPRITE_ATLAS_VARIANTS_PIPELINE.md), and [direct workflow](../../DIRECT_SPRITE_WORKFLOW.md)
own the general procedure. This directory completes the existing goblin project by reusing its accepted
[darker front restoration](../direct_front_final/toned_v1/README.md) and generating only missing native directions.

## Coverage and native behavior

`assets_dev/engine/sprites/gob*.bmp` matches 59 creature images plus `goblet.bmp`, an unrelated object that is excluded.
All creature images are indexed 355×289 BMPs, with transparent index 0. There are **58 unique pixel images**:
corpse `gobdyf0` is identical to death `gobdyd0` and shares its restored tile. Palettes 745/746/747 are loaded from
`assets_dev/worlds/mm6/textures/`. Merged monster descriptors 550/551/552 refer to group families `gob*`, `gbb*`,
and `gcb*` respectively; descriptor capitalization is case-insensitive at lookup.

| Action | Frames per sequence | Native views |
| --- | ---: | --- |
| Standing | 1 | Five stored, three mirrored aliases |
| Walk | 6 | Five stored, three mirrored aliases |
| Attack | 6 | Front reused for every angle |
| Hit | 6 | Front reused for every angle |
| Fidget | 6 | Front reused for every angle |
| Death | 5 | Front reused for every angle |
| Corpse | 1 | Front held for every angle |

The 31 front frames reuse accepted artwork with the reviewed integer ground-contact correction. Four standing views and 24 walking frames are new,
generated in **five built-in imagegen calls**. Native views 5/6/7 mirror 3/2/1 only for standing and walking.
There are no invented side attacks, deaths, or extra inbetweens.

Ordinary frame durations are 125 ms. The blue Shaman walk is specifically
`125,187.5,62.5,125,125,125` ms; the other walk variants use six 125 ms frames. All walk cycles total 750 ms.
Death totals 625 ms. Native frame scales are approximately 0.65, 0.70 and 0.75 for green, blue and red.
The manifest preserves each palette's own groups, timing and scale in `animations_by_palette` and
`native_group_bindings`; `animations` is only the green default. The viewer uses the selected palette's timing,
and displays its native scale while comparing both images at the same logical zoom.

## Outputs and provenance

- [manifest.json](manifest.json): schema v2, packed rectangles, crop origins, pivots, animation groups and variants.
- `atlas/base_*.png` and `atlas/mask_*.png`: shared art plus identically packed two-region masks.
- `aligned_2x/`, `masks_2x/`: aligned masters; `trimmed_2x/`, `trimmed_masks_2x/`: padded tight crops.
- `previews/`: deterministic blue/red atlas previews and colored mask overlays, for review rather than runtime copies.
- `sheets/view_*_all_actions_2x.png`: transparent review/interchange grids, not efficient runtime allocations.
- [sources.json](sources.json): source hashes, original table data, palettes, and accepted front checkpoint hashes.
- [generation.json](generation.json): selected raw outputs, actual dimensions, exact submitted prompts and input hashes.
- [registration.json](registration.json): extraction rectangles, shared scale and placement transforms.
- [validation.json](validation.json): all-frame completion checks and memory accounting.

New standing art returned 1374×1145; each six-frame walking sheet returned 1683×935. Two times is the physical
export tier, not a claim of uniform two-times newly generated detail. Original raw output paths are recorded and
copies remain in `raw/`. Earlier front raw sheets, exact prompts, grading and reviewed placement remain under
`../direct_front_final/`; this run does not overwrite that accepted delivery.

## Extraction, placement and edge cleanup

Native pose grids control the new views; the accepted darker front and restored standing sides control identity.
Empty gutters are measured near nominal grid boundaries before extracting sprites. The existing goblin matte fitter
estimates alpha and removes magenta RGB contamination. A narrow contour correction also removes residual shared
red/blue excess before and after premultiplied-alpha resampling. The green base has no intended fuchsia material;
this correction must never run on recolored blue/red variants. Warm blade interiors are retained.

Accepted front aligned art receives this local edge correction and an integer downward registration adjustment,
retaining its pixels, alpha and accepted grade. New art is generated against that tonal reference without an additional grade. New standing/walk sheets use
one scale per sheet, native olive-head horizontal landmarks and each native frame's alpha baseline. Oversized
silhouettes expand the aligned canvas rather than being clipped. Native placement is approximate anatomical
registration, not pixel-identical geometry.

Logical canvas: **355×289**, bottom-center pivot **(177.5,289)**, no native `Center` flag. At 2× export:

```text
local_x  = (crop_origin_x + pixel_x) / 2 - 177.5
local_up = 289 - (crop_origin_y + pixel_y) / 2
```

Then apply native frame scale and actor scale. Mirror the complete placement with the UVs. Cropping must not
recenter the monster or change its world size. Four pixels of crop padding and three pixels of transparent
RGB/mask extrusion support filtering. Mipmaps are not included. Crops reconstruct aligned RGBA exactly, and atlas
extraction matches each tight base/mask image exactly.

## Selective palette variants

The base is green Goblin, palette 745. RGB mask PNGs carry two useful linear coverage channels:

| Channel | Region | Review overlay |
| --- | --- | --- |
| R | Olive skin and yellow/gold accents | Orange |
| G | Brown leather and warm equipment/blade accents | Cyan |
| B | Unused, zero | — |

These masks are authored on enhanced pixels using calibrated color separation. Gray steel and neutral highlights
largely remain unselected. Original native palettes change skin, colored spikes/guard, leather, and some blade tones;
they are not whole-body multipliers. Color overlap means warm scars and small highlights can have partial coverage
in either region. This is an approximation of new continuous-tone materials, not a recovery of native palette indices.

Fixed RGB vectors come from native palette correspondence. Skin fitting weights actual native front face/torso
pixels so unused palette entries and gold do not pull red skin toward brown. Equipment uses the selected warm native
entries. Parameters are fixed across every pose; no per-frame histogram matching or palette AI redraws occur.

```text
Y = dot(base.rgb, [0.2126, 0.7152, 0.0722])
output.rgb = base.rgb * (1 - R - G)
           + Y * (R * skin_vector + G * equipment_vector)
output.a = base.a
```

RGB math is in encoded sRGB values, mask weights are linear coverage, and `R+G <= 1`. Green is an exact bypass.
Vectors and the `masked_regions_luminance_rgb_v1` model name are in the manifest. Baked preview atlases implement
this exact operation. All variants preserve alpha; zero-mask pixels retain base RGBA exactly.

The shared engine loader/cache/shader now supports this two-region operation with an RG8 mask and two vectors.
The [New Sorpigal exporter](../../mm6_peasants/prepare_playtest.py) produces compact runtime schema v1 from this
offline art schema v2, retaining per-palette animation groups/scales through native texture-reference replacements.
Do not reduce this package to one mask or install three duplicated full-color runtime atlases.

## Review and resource use

Inspect [all frames](review/all_base_dark.png), [all masks](review/all_masks_light.png),
[variants](review/standing_variants.png), [edge crops](review/edge_current.png), and native/restored
`review/*_comparison.png`. Edge checks cover every cleaned and final atlas-extracted frame. No candidates exceed
the configured 16/255 alpha-weighted magenta-excess threshold; visual light/dark review remains necessary alongside
that metric. There are no clipped extraction cells, altered variant alpha, or crop/atlas reconstruction failures.

The decoded base is about **43.10 MiB**. The current RGB mask files decode to **32.32 MiB**, totaling **75.42 MiB**
with atlas packing. The RG8 runtime mask totals about **64.65 MiB** with the base; uploading masks as RGBA8
would instead total **86.20 MiB**. The New Sorpigal integration uses RG8. Original full
canvases decoded as RGBA for one palette total **23.09 MiB**. Review variants, intermediate masters, mipmaps and
transient CPU/driver copies are excluded. Multiple actors share the pages; allocation is not multiplied by actor count.
The four base/mask page pairs total about **12.47 MiB on disk**, excluding review assets and intermediate masters.

Remaining visible differences include slightly changing sword notches, armor perspective, highlights and skin
microdetail between independently restored poses. Native colors on newly shaded materials are approximate.
Matte alpha is estimated, not recovered ground-truth transparency.

## Reproduce from saved checkpoints

Run from the repository root with Pillow, NumPy, SciPy and PyYAML:

```sh
python3 level_generation/creatures/mm6_goblin/direct_complete/prepare.py
python3 level_generation/creatures/mm6_goblin/direct_complete/process.py
python3 level_generation/creatures/mm6_goblin/direct_complete/package.py
python3 level_generation/creatures/mm6_goblin/direct_complete/build_viewer.py
```

These stages reuse saved AI sheets; no AI calls or paid API are made. `record_generation.py` records selected
generation provenance without overwriting existing submitted prompt checkpoints. Matting and geometry helpers
reuse the existing goblin/Behemoth deterministic project scripts; this is a creature-specific exporter.

Use the [approved capture helper](../../../../tools/CAPTURE_LOCAL_HTML.md) directly for browser screenshots:

```sh
./tools/capture_local_html.py level_generation/creatures/mm6_goblin/direct_complete/review.html \
  level_generation/creatures/mm6_goblin/direct_complete/review/viewer_blue_walk.png \
  --query 'action=walk&view=6&palette=746&frame=1'
```

No Blender setup, build or gameplay scenario is required for this art batch.

## Installation and ground correction — 2026-09-13

The complete MM6 set is installed in `assets_dev/engine/sprites_new/`. [Ground correction notes](review_notes.md) supersede the earlier front-placement checkpoint: the 31 front images now meet the native visible baseline. The old isolated playtest must be updated separately if used; normal repository launches use the installed pack.
