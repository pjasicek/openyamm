# MM6 male peasant 1 — restored `pman*.bmp`

[Offline native/enhanced viewer](review.html) · [Three appearances](review/standing_variants.png) ·
[Validation](validation.json) · [Review notes](review_notes.md) · [Overall index](../mm6_peasants/README.md).

All **59 native files / 59 unique images** are restored. Five stored standing/walking directions retain eight
native view aliases; attack, hit, fidget, death and corpse retain their front-only behavior. The second attack
binding is preserved. `pmanfib0` and `pmanwif0` are unused by native playback but retained as artwork. Native
125 ms entries and scale `0.699997` remain unchanged.

Base **798** is the green tunic. One shared **R8** coverage mask produces **799** charcoal and **800** muted red.
Skin, auburn hair, leather belt/cuffs/shoes, brass buckle, pale leggings and silver dagger are protected. Fixed
native-derived luminance vectors retain shading; base bypass and alpha preservation are exact. Small blade-only
polygons correct demonstrated green contamination and exclude metal from the tunic mask.

## Export and footprint

Logical canvas **293×255**, pivot **146.5,255**, at **2 physical pixels per logical pixel**. Shared batch scale,
native baselines and crop origins preserve logical size and motion. RGBA8/R8 page pairs are **2030×1579** and
**1999×1845**, with four-pixel crop padding and three-pixel transparent RGB/mask extrusion. No mipmaps.

Ten accepted built-in imagegen sheets are **1629–1632×963–965** pixels. No AI rerolls; the dagger correction reuses
saved raw art. Generated detail and physical export resolution are separate quantities.

| Data | Footprint |
| --- | ---: |
| Original indexed BMP files | 1.55 MiB |
| Original decoded RGBA, one palette | 5.86 MiB |
| Enhanced RGBA8 base pages | 26.30 MiB |
| Shared R8 masks | 6.57 MiB |
| Shared decoded total | 32.87 MiB |
| Shipping pages, masks and manifest | 7.52 MiB |

Allocations are shared across actors and all three appearances. Shipping excludes raw art, masters, deterministic
variant previews and review sheets. **Staged only**: the engine's `masked_luminance_rgb_v1`/R8 operation is compatible,
but installation requires explicit asset/animation/descriptor registration and loader validation.

## Checkpoints

[Sources](sources.json) · [Batches](batches.json) · [Generation provenance](generation.json) ·
[Registration](registration.json) · [Settings](config.json) · [Variant vectors](recolor_vectors.json).
Exact accepted prompts are in `prompts/submitted/`.

[All base frames](review/all_base_dark.png) · [All masks](review/all_masks_light.png) ·
[Light/dark contours](review/edge_current.png) · [All-frame edge audit](review/edge_current.json) ·
[Corrected attack variants](review/dagger_corrected.png).
Full action sheets are `sheets/view_0_all_actions_2x.png` through `view_4_all_actions_2x.png`.

```sh
python3 level_generation/creatures/mm6_peasants/process_family.py pman
python3 level_generation/creatures/mm6_peasants/package_family.py pman
python3 level_generation/creatures/mm6_peasants/build_viewer.py pman
```

Run from the repository root. Offline reproduction uses saved art and needs no AI calls. Browser captures use
the [approved helper](../../../tools/CAPTURE_LOCAL_HTML.md). No engine installation or gameplay changes.
