# MM6 male peasant 3 — restored `mep*.bmp`

[Offline native/enhanced viewer](review.html) · [Three appearances](review/standing_variants.png) ·
[Validation](validation.json) · [Review notes](review_notes.md) · [Overall index](../mm6_peasants/README.md).

All **59 native files / 59 unique images**, all referenced, are restored. Five stored standing/walking directions
retain eight native view aliases. Attack, hit, fidget, death and corpse preserve their single-view behavior, with
the second attack binding retained. Native entries keep 125 ms timing and scale `0.699997`.

The elderly staff carrier has a pale wrapped cap, white beard, weathered light coat, red buttons/tasseled sash,
blue-grey trousers and sandals. Base **804** produces **805** grey cap/orange sash and **806** cyan cap/dark sash.
The original 806 palette also shifts pale and warm materials toward green; a single garment mask cannot reproduce
these independent changes. One base atlas is shared by all appearances.

| Mask data channel | Region | Overlay color |
| --- | --- | --- |
| R | Red sash and buttons | Orange |
| G | Cool cap/trousers and cool shirt shading | Blue |
| B | Pale coat/shirt and white hair/beard | Magenta |
| A | Warm skin, wood and leather | Green |

**Mask alpha is coverage data, not opacity.** Base alpha controls the silhouette. Four soft weights sum to at most
one; fixed native-derived RGB vectors operate on encoded-RGB luminance. The base preset is an exact bypass.
The manifest documents `multi_mask_luminance_rgb_v1` and each variant's four vectors. Review previews are baked
deterministically; they are not additional shipping textures.

## Export and footprint

Logical canvas **248×256**, pivot **124,256**, at **2 physical pixels per logical pixel**. Native baselines, common
batch scale and crop offsets preserve logical placement. Three RGBA8 base/RGBA8 mask pairs are **1928×1564**,
**1875×1549**, **2038×1542**. Four-pixel crop padding, three-pixel transparent RGB/mask extrusion, no mipmaps.

Ten built-in imagegen requests produced ten accepted **1536×1024** sheets. The close death-sheet gap was corrected
by explicit cell ownership using saved art, with no AI reroll. Actual generated detail is separate from the 2× tier.

| Data | Footprint |
| --- | ---: |
| Original indexed BMP files | 3.63 MiB |
| Original decoded RGBA, one palette | 14.29 MiB |
| Enhanced RGBA8 base pages | 34.57 MiB |
| Shared RGBA8 masks | 34.57 MiB |
| Shared decoded total | 69.14 MiB |
| Shipping pages, masks and manifest | 11.88 MiB |

Memory is shared across actors and appearances. Shipping excludes masters, raw art, variant previews and review
sheets. **Staged only**: future installation needs a four-channel linear-data mask loader, four RGB vectors per
preset and the documented shader sum, plus explicit sprite/animation/descriptor registration. Current single-R8
`masked_luminance_rgb_v1` support is insufficient. This goal changes no runtime content.

## Checkpoints

[Sources](sources.json) · [Batches](batches.json) · [Generation provenance](generation.json) ·
[Registration](registration.json) · [Settings](config.json) · [Variant vectors](recolor_vectors.json).
Exact submitted prompts are in `prompts/submitted/`; standing predates the refined four-region description.

[All base frames](review/all_base_dark.png) · [All masks](review/all_masks_light.png) ·
[Light/dark contours](review/edge_current.png) · [All-frame edge audit](review/edge_current.json) ·
[Native/restored collapse](review/death_corpse_comparison.png).
Full action sheets are `sheets/view_0_all_actions_2x.png` through `view_4_all_actions_2x.png`.

```sh
python3 level_generation/creatures/mm6_peasants/process_family.py mep
python3 level_generation/creatures/mm6_peasants/package_family.py mep
python3 level_generation/creatures/mm6_peasants/build_viewer.py mep
```

Run from the repository root; no AI regeneration is needed. Browser captures use the
[approved helper](../../../tools/CAPTURE_LOCAL_HTML.md).
