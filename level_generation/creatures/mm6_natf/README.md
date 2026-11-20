# MM6 female peasant 4 — restored `natf*.bmp`

[Offline native/enhanced viewer](review.html) · [Three appearances](review/standing_variants.png) ·
[Validation](validation.json) · [Review notes](review_notes.md) · [Overall index](../mm6_peasants/README.md).

All **59 native filenames / 58 unique images** are restored with every original action and view alias. Five stored
standing/walking directions supply eight views through native mirroring; attack, hit, fidget, death and corpse
retain their native single-view behavior. The second attack binding is preserved. `natffid0` shares `natffic0` pixels;
`natffib0` is unused by native playback but retained in the export. Entries retain 125 ms timing and scale `0.699997`.

Base **796** uses olive equipment. A shared **R8** mask produces **795** grey and **797** red for headband, chest armor,
waist/thigh/ankle bands, hanging panels and shield paint. Dark skin, curly hair, pale feather/bone trim, blade and
warm neck collar remain distinct. The olive selector was calibrated separately from the other families' green
cloth masks; see review notes for the blade/highlight correction. Fixed native-derived luminance vectors preserve
shading, with exact base bypass and unchanged alpha in every appearance.

## Export and placement

Native logical canvas **239×285**, pivot **119.5,285**, exported at **2 physical pixels per logical pixel**. Shared
batch scales and native baselines preserve size; recorded crop offsets preserve motion, including prone poses.
Three RGBA8/R8 page pairs are **1883×1620**, **2046×1555**, **1913×1435**. Crops have four pixels of padding and
three pixels of transparent RGB/mask extrusion. No mipmaps are generated.

Ten built-in imagegen requests produced ten accepted sheets, **1463–1464×1075** pixels. No AI batch was regenerated;
mask corrections reused the accepted raw art. Actual generated detail is separate from the 2× export tier.

| Data | Footprint |
| --- | ---: |
| Original indexed BMP files | 2.41 MiB |
| Original decoded RGBA, one palette | 9.29 MiB |
| Enhanced RGBA8 base pages | 34.25 MiB |
| Shared R8 masks | 8.56 MiB |
| Shared decoded total | 42.81 MiB |
| Shipping pages, masks and manifest | 10.34 MiB |

These page allocations are shared across actors and all three appearances. Shipping excludes generation sources,
masters, baked previews and review sheets. **Staged only**: the engine supports `masked_luminance_rgb_v1` and R8,
but installation needs explicit asset/animation/descriptor registration and loader validation.

## Checkpoints and reproduction

[Sources](sources.json) · [Batches](batches.json) · [Generation provenance](generation.json) ·
[Registration](registration.json) · [Settings](config.json) · [Variant vectors](recolor_vectors.json).
Exact accepted prompts are in `prompts/submitted/`.

[All base frames](review/all_base_dark.png) · [All masks](review/all_masks_light.png) ·
[Light/dark contours](review/edge_current.png) · [All-frame edge audit](review/edge_current.json).
Full action sheets are `sheets/view_0_all_actions_2x.png` through `view_4_all_actions_2x.png`.

```sh
python3 level_generation/creatures/mm6_peasants/process_family.py natf
python3 level_generation/creatures/mm6_peasants/package_family.py natf
python3 level_generation/creatures/mm6_peasants/build_viewer.py natf
```

Run from the repository root to rebuild offline from saved raw art. No AI regeneration is needed. Browser captures
use the [approved helper](../../../tools/CAPTURE_LOCAL_HTML.md); no engine build/scenario/installation was performed.
