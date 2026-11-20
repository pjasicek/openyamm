# MM6 female peasant 3 — restored `mfp*.bmp`

[Offline native/enhanced viewer](review.html) · [Three appearances](review/standing_variants.png) ·
[Validation](validation.json) · [Review notes](review_notes.md) · [Overall index](../mm6_peasants/README.md).

All **59 native images** are restored: standing, walking, attack, hit, fidget, death and corpse, with the native
second attack binding preserved. Five stored standing/walking directions supply eight view aliases; other actions
retain native single-view behavior. All files are referenced, with no exact pixel aliases. Native sequence entries
retain 125 ms timing and scale `0.699997`, recorded separately for each palette.

Palette **792** is the green blouse base. One **R8** soft coverage mask produces **793** red and **794** blue using
fixed native-derived luminance vectors. Skin, black braid, gold jewelry, pink patterned skirt and knife are protected.
The base preset bypasses recoloring exactly; every appearance shares geometry and alpha.

## Export and placement

The logical canvas is **281×257**, pivot **140.5,257**, exported at two physical pixels per logical pixel. Shared
batch scale, native baselines and recorded crop origins preserve world size and frame placement. Falling/prone
poses retain their native proportions. Four-pixel crop padding and three-pixel transparent RGB/mask extrusion
protect filtering. Page pairs are **2004×1581**, **2048×1851**, within 2048 pixels. No mipmaps are generated.

Ten accepted sheets were generated with built-in imagegen, once per batch. Their actual dimensions are recorded
in generation.json and registration.json (approximately 1599×984); these are independent of the final 2× export tier.
No separate palette redraws were generated. Cyan was used instead of magenta to preserve the skirt's pink pattern.

| Data | Footprint |
| --- | ---: |
| Original indexed BMP files | 4.03 MiB |
| Original decoded RGBA, one palette | 15.69 MiB |
| Enhanced RGBA8 base pages | 26.55 MiB |
| Shared R8 masks | 6.64 MiB |
| Enhanced shared decoded total | 33.18 MiB |
| Shipping pages, masks and manifest | 7.64 MiB |

Memory is shared across actors and three appearances. Shipping excludes raw sheets, aligned masters, baked variant
previews and review sheets. This package is **staged only**. The engine supports `masked_luminance_rgb_v1` and R8
masks; future installation still requires explicit asset/animation/descriptor registration and loader validation.

## Checkpoints and reproduction

[Sources](sources.json), [batches](batches.json), [generation provenance](generation.json),
[registration](registration.json), [settings](config.json) and [variant vectors](recolor_vectors.json) preserve the
accepted recipe. Exact submitted prompts are in `prompts/submitted/`.

[All frames](review/all_base_dark.png) · [All masks](review/all_masks_light.png) ·
[Light/dark contours](review/edge_current.png) · [All-frame spill scores](review/edge_current.json).
Full review sheets live in `sheets/view_0_all_actions_2x.png` through `view_4_all_actions_2x.png`.

Rebuild from saved accepted raw art, from the repository root:

```sh
python3 level_generation/creatures/mm6_peasants/process_family.py mfp
python3 level_generation/creatures/mm6_peasants/package_family.py mfp
python3 level_generation/creatures/mm6_peasants/build_viewer.py mfp
```

Do not rerun AI generation to reproduce these exports. Viewer captures use the
[approved helper](../../../tools/CAPTURE_LOCAL_HTML.md). No engine installation/build/scenarios were performed.
