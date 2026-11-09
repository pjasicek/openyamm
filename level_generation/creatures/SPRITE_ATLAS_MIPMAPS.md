# Enhanced actor atlas mipmaps

Mipmap construction now runs in the offline cooker before BC7/ETC2 compression. Runtime reads the
prepared levels; it does not read PNGs or build mipmaps. See [deployment](SPRITE_RUNTIME_DEPLOYMENT.md).


Enhanced `atlas:` sprites now use matching mipmaps for artwork and material masks in the shared indoor/outdoor
renderer. Terrain, BModels and sky already had CPU-generated mip chains. Native sprites and UI keep their existing
filtering policy.

bgfx's `createTexture2D(..., hasMips=true, ...)` allocates mip storage; it does not build smaller images from a PNG.
The offline cooker generates levels 0–4; the shared cache uploads their GPU blocks when each page is loaded. Billboard filtering
settings control sampling; disabling texture filtering selects level zero and nearest sampling.

Source atlas gutters were designed for full-resolution bilinear sampling. Offline repacking gives each distinct
frame a cell aligned to 16 pixels, with at least 16 pixels of edge extension on every side. Identical source
rectangles share the same GPU cell. This makes 2×2 reductions independent through level 4 (1/16 dimensions).
The shader derives one LOD from the sprite footprint, clamps it to 0–4, and uses it for both textures and outlines.
Deeper allocated levels are not uploaded or sampled: these compact atlases cannot safely mix entire poses into
one texel. Extremely distant sprites therefore stop gaining additional prefiltering past 16× minification.

Base color and all material weights are reduced using **base alpha** as weight; base alpha itself is averaged.
Each smaller level receives transparent edge colors within its own cell. A four-channel mask's alpha remains a
material weight, never sprite opacity. Base bypass and palette shading remain unchanged. Recoloring the filtered
base/masks can approximate small material boundaries; this is not a separate baked atlas per palette.

The original page PNGs remain in the authoring exports. Manifest crops, logical positions, frame dimensions,
animation data and full-resolution picking masks remain intact. Source pixels inside each level-zero frame are
copied exactly before lossy GPU compression. GPU rectangles change only texture coordinates and are stored in
the cooked page. Mips are generated once per cook, shared by all actors/palettes; runtime staging holds compressed
GPU blocks and releases them after upload. No new AI pass or source atlas rewrite is required.

## Historical uncompressed cost and validation

Mipmaps add roughly one-third storage plus padding. These measurements predate GPU compression and describe
the old raw texture allocations (base plus masks, all family pages resident; excludes driver bookkeeping):

| Family | Before | With padding and mip storage |
| --- | ---: | ---: |
| Female peasants | 33.71 MiB | 58.97 MiB |
| Male peasants | 32.87 MiB | 58.58 MiB |
| Mages | 46.14 MiB | 79.92 MiB |
| Goblins | 64.65 MiB | 111.65 MiB |
| Guards | 80.80 MiB | 141.97 MiB |

These are per-family shared allocations, not per actor. Current deployment stores prepared, GPU-compressed
pages and excludes authoring PNGs; see the [deployment guide](SPRITE_RUNTIME_DEPLOYMENT.md) for the release contract.
GPU motion review remains useful for shimmer and sharpness calibration. Asset generation should not run engine
scenarios just to produce art.

Focused tests cover odd-sized neighboring frames through every sampled level, duplicate frame sharing, exact
level-zero pixels, unchanged placement, opacity-weighted color, independent R/RG/RGBA mask values, transparent
edge colors and size-limit rejection. Run `sprite atlas*` tests after changes. The game and shader build and a
native New Sorpigal capture are separate renderer checks; never claim that a static capture measures motion aliasing.

This change passed the game build, desktop GLSL and GLES shader compilation, 14 atlas tests and five existing
billboard/upload tests. The [town capture](mm6_peasants/review/actor_mipmaps/sorpigal_actor_mips_view.png) shows
restored residents at several distances without visible neighboring-frame bleed. It is a desktop software-display
smoke check, not an Android device test or a motion/performance measurement. The New Sorpigal playtest executable
was updated; 42 save/settings/rendering-table/terrain files were verified unchanged. Restart enhanced mode to load it.

Implementation: [mip builder](../../game/render/SpriteAtlasMipmaps.cpp),
[shared cache](../../game/render/SpriteAtlasCache.cpp), [billboard shader](../../game/shaders/billboard_lit.sh).
