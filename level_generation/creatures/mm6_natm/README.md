# MM6 male peasant 4 — restored `natm*.bmp`

[Offline native/enhanced viewer](review.html) · [Three appearances](review/standing_variants.png) ·
[Validation](validation.json) · [Review notes](review_notes.md) · [Overall index](../mm6_peasants/README.md).

All **59 native files / 59 unique images** are restored. Five stored standing/walking directions retain eight
native view aliases. Attack, hit, fidget, death and corpse preserve their single-view behavior, including the
second attack binding. Unused `natmfib0` is retained as artwork. Entries keep 125 ms timing and scale `0.699997`.

This native peasant family depicts a muscular bald man with feather/bone mantle, bare torso, loincloth, spear and
buckler. Base **796** olive equipment produces **795** grey and **797** red using one shared **R8** mask. Coverage
includes colored cloth panels, armbands, bindings and shield paint; dark skin, pale feathers, metal blade, gold
neck collar and brown wood/inner straps remain distinct. The family-specific olive-to-green selector includes
cooler side-view cloth folds. Fixed native-derived luminance vectors preserve shading, base bypass and alpha.

## Export and footprint

Logical canvas **363×313**, pivot **181.5,313**, at **2 physical pixels per logical pixel**. Native baselines,
shared batch scales and crop offsets preserve logical size and motion. Five RGBA8/R8 page pairs are **1938×1670**,
**1879×1572**, **1855×1556**, **2002×1987**, **1963×428**. Four-pixel crop padding, three-pixel transparent RGB/mask
extrusion, no mipmaps. Wider spear poses account for substantial transparent space inside some tight rectangles.

Ten built-in imagegen requests produced ten accepted **1643–1644×957** sheets. No AI rerolls; mask calibration
reuses saved raw art. Actual generated detail is distinct from the 2× physical export tier.

| Data | Footprint |
| --- | ---: |
| Original indexed BMP files | 4.86 MiB |
| Original decoded RGBA, one palette | 19.15 MiB |
| Enhanced RGBA8 base pages | 53.00 MiB |
| Shared R8 masks | 13.25 MiB |
| Shared decoded total | 66.26 MiB |
| Shipping pages, masks and manifest | 11.42 MiB |

Allocations are shared across actors and all appearances. Shipping excludes raw art, masters, variant previews
and review sheets. **Staged only**: the engine supports the `masked_luminance_rgb_v1`/R8 operation, but future
installation requires explicit asset/animation/descriptor registration and loader validation.

## Checkpoints

[Sources](sources.json) · [Batches](batches.json) · [Generation provenance](generation.json) ·
[Registration](registration.json) · [Settings](config.json) · [Variant vectors](recolor_vectors.json).
Exact submitted prompts are in `prompts/submitted/`.

[All base frames](review/all_base_dark.png) · [All masks](review/all_masks_light.png) ·
[Light/dark contours](review/edge_current.png) · [All-frame edge audit](review/edge_current.json) ·
[Native/restored attack](review/attack_comparison.png) · [Collapse](review/death_corpse_comparison.png).
Full action sheets are `sheets/view_0_all_actions_2x.png` through `view_4_all_actions_2x.png`.

```sh
python3 level_generation/creatures/mm6_peasants/process_family.py natm
python3 level_generation/creatures/mm6_peasants/package_family.py natm
python3 level_generation/creatures/mm6_peasants/build_viewer.py natm
```

Run from the repository root; no AI regeneration is needed. Browser captures use the
[approved helper](../../../tools/CAPTURE_LOCAL_HTML.md). No engine installation or gameplay changes.
