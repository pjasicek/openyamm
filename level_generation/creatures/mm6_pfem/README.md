# MM6 female peasant 1 — restored `pfem*.bmp`

Enhanced direct sprite restoration, staged offline. [Open the native/enhanced viewer](review.html),
[compare all three appearances](review/standing_variants.png), or inspect the [validation report](validation.json).
This package does not replace native assets or create gameplay monsters.

All **59 native source filenames** have enhanced images. Standing and walking retain five stored directions and
three mirrored directions. Attack, hit, fidget, death and corpse retain their native single-view behavior.
The second attack binding reuses the first attack sequence. All native entries are 125 ms with scale `0.699997`;
these values remain recorded per entry and per palette in [manifest.json](manifest.json).
The fidget sequence repeats `pfemfia0` in its first two entries; the unused but distinct `pfemfib0` is still supplied
as artwork without inserting it into playback. There are no exact native pixel aliases in this family.

The base is palette **786**, green bodice and skirt bands. One soft **R8** mask recolors those materials to **787**
(brown) or **788** (blue). Skin, auburn hair, off-white cloth, leather and the knife remain protected. Variant colors
are fitted from native used indices that actually change between palettes, with fixed parameters across poses.
The base is an exact bypass, and all variants retain identical alpha. Review previews are deterministic outputs;
they do not need to ship as three sets of textures.

## Placement and package

The native files have variable canvas dimensions. Their common logical canvas is **218×253**, pivot **109,253**.
Native offsets are recorded explicitly; centered odd-width differences use integer floor placement. Final art uses
**2 physical pixels per logical pixel**, with shared scale within upright action batches and native body-center/
baseline registration. Falling/prone poses retain native silhouette proportions. Tight rectangles include four
pixels of padding and three pixels of transparent RGB/mask extrusion. No mipmaps are generated.

Ten built-in AI requests produced **1536×1024** raw sheets each. That is the actual generation size; the 2× export
tier describes final placement/resampling and is not a claim that every figure contains twice the native detail.
The two atlas page pairs are **1977×1576** and **1956×2021**. Current byte counts are authoritative in validation:

| Data | Footprint |
| --- | ---: |
| Original 59 indexed BMP files | 2.18 MiB on disk |
| Original files decoded RGBA, one palette | 8.39 MiB |
| Enhanced base pages, RGBA8 | 26.97 MiB |
| Shared selective masks, R8 | 6.74 MiB |
| Enhanced shared decoded total | 33.71 MiB |
| Shipping base pages + masks + manifest | about 7.94 MiB |

These atlas bytes are shared by all actors using the family, not multiplied by the number of peasants on screen.
Raw references, aligned masters, native comparisons, action sheets and baked variant previews are review/source
artifacts and excluded from shipping totals. The current engine already supports `masked_luminance_rgb_v1` with
R8 masks (`engine/SpriteAtlas.cpp`, `game/render/SpriteAtlasCache.cpp`). A future explicit installation still needs
asset placement and descriptor/animation registrations; this goal performs neither.

## Evidence and reproduction

- [Source inventory and palettes](sources.json), [batch layouts](batches.json), [generation provenance](generation.json).
- Exact submitted prompts in `prompts/submitted/`; accepted raw sheets in `raw/`.
- [Registration and extraction parameters](registration.json), [family-specific material settings](config.json).
- [All enhanced frames](review/all_base_dark.png), [all mask overlays](review/all_masks_light.png),
  [worst contour patches on light/dark](review/edge_current.png), [all-frame contour audit](review/edge_current.json).
- [Visual review notes](review_notes.md), including the local knife-mask repair and remaining approximations.
- Full action sheets: `sheets/view_0_all_actions_2x.png` through `view_4_all_actions_2x.png`.

From the repository root, reprocess saved accepted art without AI calls:

```sh
python3 level_generation/creatures/mm6_peasants/process_family.py pfem
python3 level_generation/creatures/mm6_peasants/package_family.py pfem
python3 level_generation/creatures/mm6_peasants/build_viewer.py pfem
```

Preparation is separate and rewrites prompt templates; the exact submitted attack prompt explicitly preserves the
native right-hand knife. Use the saved submitted prompt for any targeted regeneration. Do not rerun accepted AI
batches merely to reproduce deterministic exports. Browser evidence uses the [approved capture helper](../../../tools/CAPTURE_LOCAL_HTML.md).

Part of the [eight-family restoration goal](../MM6_PEASANTS_RESTORATION_GOAL.md) and [overall index](../mm6_peasants/README.md).
