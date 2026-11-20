# MM6 female peasant 2 — restored `fmp*.bmp`

[Offline native/enhanced viewer](review.html) · [Three appearances](review/standing_variants.png) ·
[Validation](validation.json) · [Review notes](review_notes.md) · [Overall index](../mm6_peasants/README.md).

All **59 native images** are restored, covering standing, walking, attack, hit, fidget, death and corpse.
The native second attack binding reuses the first attack. Five stored standing/walking views supply eight view
aliases with native mirroring; other actions retain their native single-view behavior. All 59 files are referenced,
with no exact pixel aliases. Descriptor groups use `fmA`/`fmb`/`fmc` names while the actual BMP prefix is `fmp`.
All native entries retain 125 ms timing and scale `0.699997`, recorded separately for each palette.

Palette **790** is the enhanced blue base. One **R8** coverage mask changes its apron, thin waist tie and cap to
palette **789** (pale lavender/white) or **791** (ochre/orange). Brown overdress, tan blouse, skin, dark hair,
leather shoes and the attack's wooden rolling pin are protected. Fixed native-derived luminance vectors preserve
shading. Base bypass, alpha preservation and zero-mask protection are checked for every frame and palette.

## Export and placement

The native canvases are **215×256**, with logical pivot **107.5,256**. The export uses two physical pixels per logical
pixel, preserving native size, motion and feet placement through registered masters and crop offsets. Atlas crops
have four pixels of padding and three pixels of transparent RGB/mask extrusion. The three page pairs are
**1972×1549**, **2044×2045** and **1358×468**, all within 2048 pixels. No mipmaps are generated.

Ten accepted raw sheets are **1536×1024** each. Eleven AI requests were made: the first hit sheet incorrectly added
a rolling pin and was retained under `raw/rejected/`; its replacement restores the native empty hands. This was the
only regenerated batch. Actual generation dimensions are separate from the final 2× export tier.

| Data | Footprint |
| --- | ---: |
| Original indexed BMP files | 3.17 MiB on disk |
| Original decoded RGBA, one palette | 12.39 MiB |
| Enhanced RGBA8 base pages | 30.02 MiB |
| Shared R8 masks | 7.51 MiB |
| Enhanced shared decoded total | 37.53 MiB |
| Shipping pages, masks and manifest | 9.51 MiB |

Atlas memory is shared across actors and the three appearances. Source sheets, aligned/cropped masters, baked
variant previews and large review sheets are excluded from shipping totals. Exact current bytes are in validation.
The package is **staged only**. The engine already implements the selected `masked_luminance_rgb_v1` operation and
R8 upload; future installation requires explicit asset and animation/descriptor registration, not another shader.

## Checkpoints and reproduction

[Sources](sources.json), [batches](batches.json), [generation provenance](generation.json),
[registration](registration.json), [family settings](config.json) and [variant vectors](recolor_vectors.json)
record the native inputs and accepted processing. Exact submitted prompts are in `prompts/submitted/`.
Generation provenance retains the rejected hit version and its reason, without selecting it for export.

Review [all frames](review/all_base_dark.png), [all masks](review/all_masks_light.png),
[worst light/dark contour patches](review/edge_current.png), and [all-frame spill scores](review/edge_current.json).
Full review sheets are `sheets/view_0_all_actions_2x.png` through `view_4_all_actions_2x.png`.

Rebuild offline from accepted raw art, from the repository root:

```sh
python3 level_generation/creatures/mm6_peasants/process_family.py fmp
python3 level_generation/creatures/mm6_peasants/package_family.py fmp
python3 level_generation/creatures/mm6_peasants/build_viewer.py fmp
```

Use the saved submitted hit prompt if regenerating that action: it explicitly requires empty hands. Do not rerun
preparation or AI calls just to reproduce these exports. Browser captures use the
[approved local helper](../../../tools/CAPTURE_LOCAL_HTML.md); no engine builds/scenarios or installation were performed.
