# Compact runtime atlas format review — 27 September 2026

The uncompressed v1 `.oyatlas` cache is unsuitable as the final shipping format. It removed expensive load-time
packing/filtering, but the disk cost was not constrained adequately. Preserve that offline work and the improved loading
ordering while replacing the runtime representation. This review measures alternatives; it does not migrate runtime code
or accepted artwork.

## Current footprint

The installed collection has 62 creature packages and 237 atlas pages, predominantly MM6, plus the crusader and pmn2
packages. It already uses the intended architecture: compact pages containing multiple poses/directions, frame metadata,
native mirrors/aliases and palette variants. There are 3,654 frame names referring to 3,608 distinct crops. A separate
full atlas is not generated for every palette variant. One or a few bounded pages per creature family is appropriate;
forcing a large family into one giant texture would not remove its pixels and would hurt device compatibility.

| Existing data | Bytes | Approximate footprint |
| --- | ---: | ---: |
| Base atlas PNGs | 633,889,480 | 604.5 MiB |
| Material-mask PNGs | 110,913,882 | 105.8 MiB |
| JSON and palette lookup data | 2,823,077 | 2.7 MiB |
| Additional raw runtime pages and stamps | 8,334,336,098 | 7.76 GiB |

The raw runtime payload contains 4.96 GB of base-color mip pixels, 3.29 GB of mask mip pixels and 80.8 MB of hit masks,
plus metadata. Five mip levels add approximately one third to the base level. Alignment, filtering gutters and repacking
increase base-level allocated pixels from 721 million in the PNG pages to 931 million in the cooked pages. These gutters
protect filtering and cannot simply be removed without replacing their protection against sampling adjacent frames.

The loose combined collection is about 8.46 GiB. ZIP/APK compression reduces shipped bytes, so the loose raw size is not
itself an APK-size measurement. However, the current packager includes both PNG sources and cooked copies. A shipping
texture format should be compact on its own, and packaging should contain only the selected runtime representation.

## Measured alternatives

All 237 current cooked pages were compressed independently and decoded back to exactly the original bytes:

| Whole collection, runtime pages only | Bytes | GiB |
| --- | ---: | ---: |
| Current uncompressed pages | 8,334,316,365 | 7.76 |
| DEFLATE level 6 | 1,347,632,436 | 1.26 |
| Zstandard level 3 | 1,337,628,083 | 1.25 |
| Zstandard level 9 | 1,257,582,591 | 1.17 |

Lossless Zstandard is a viable intermediate or exact-pixel profile: it retains precomputed filtering and all original
pixels. It does not reduce GPU allocations, because those bytes still expand into ordinary color and mask textures.
A desktop microbenchmark across 11 differently sized pages measured about 1,204 MiB/s of decoded output. This is not
an in-game loading result or a mobile decompression result; no unchanged-loading-time claim follows from it.

A separate native ASTC probe used the existing vendored Arm encoder at medium quality on page 0 of `mm6_gob` and
`mm6_wel`, including both color and material masks and all five mip levels. The comparison below adds losslessly
compressed mapping/hit-mask/header data to texture bytes; final container overhead is not included.

| Same two pages | Disk bytes, approximately | GPU texture payload |
| --- | ---: | ---: |
| Current raw pages | 84.61 MiB | 83.86 MiB |
| Lossless Zstandard 9 | 15.13 MiB | 83.86 MiB |
| ASTC 4×4 + Zstandard 9 | 6.01 MiB | 23.75 MiB |
| ASTC 6×6 + Zstandard 9 | 2.98 MiB | 10.57 MiB |

These are two-page measurements, not a full-library forecast. ASTC is lossy. The decoded Goblin and Water Elemental
frames were inspected at their output size on light and dark backgrounds: 6×6 coarsens fine details and edges visibly;
4×4 is the safer starting point. This does not accept compressed masks, recolored variants, every pose or distant
mip rendering. The samples are native ASTC, not Basis/UASTC encodes. No Android binary or native compressed GPU upload
was tested. A [temporary comparison image](/tmp/openyamm-atlas-footprint/astc-comparison.png) shows the selected crops.

## Shipping size of the current restored collection

The subsequent full-library probe encoded and decoded all 237 pages in all 62 installed packages, including base color,
material masks and all five mip levels, using the same ASTC settings. The following totals use decimal MB/GB and describe
compressed shipping payloads, not RAM or VRAM. Source PNGs and raw v1 cooked copies are excluded from the proposed release.

| Current enhanced creatures, complete payload | ASTC 4×4 + Zstandard 9 | ASTC 6×6 + Zstandard 9 |
| --- | ---: | ---: |
| Compressed GPU texture data | 497,309,594 bytes | 244,569,119 bytes |
| Compressed page mappings, hit masks and headers | 10,432,521 bytes | 10,432,521 bytes |
| Compressed manifests and palette lookup data | 1,377,437 bytes | 1,377,437 bytes |
| Total | **509,119,552 bytes (509 MB)** | **256,379,077 bytes (256 MB)** |

Keeping every original BMP gives a conservative comparison without assuming that frame-name matches prove safe removal:

| Shipping content | Compressed payload |
| --- | ---: |
| Original sprite collection, existing ZIP representation | 195,791,337 bytes (196 MB) |
| Original collection + current enhanced creatures, ASTC 4×4 profile | 704,910,889 bytes (705 MB) |
| Above + current restored decorations | **888,539,661 bytes (889 MB)** |

The 2,532 files under `engine/decorations_x2` contribute 183,628,772 compressed bytes. They are retained in their current
PNG/metadata representation; this probe does not claim further savings from cooking them. The table covers sprite art,
not the whole game: maps, world textures, UI, audio, video, executable and other packages remain outside this comparison.

The installed creature manifests reference 3,590 unique original frame names; 3,496 match current original BMP filenames,
representing 48,023,519 compressed bytes. If a runtime-reference audit proves these originals unnecessary, removing them
would reduce the 4×4 creature-inclusive total to 656,887,370 bytes, or 840,516,142 bytes including restored decorations.
The 94 unmatched names and shared/fallback references need explicit handling before stripping originals.

For these current assets, approximately **0.9 GB is a realistic shipping target** with the 4×4 profile, allowing for small
final-container overhead. This is a measured full-current-library encoding, not an extrapolation from the Goblin.
It is not a size forecast for an eventual fully restored MM6/MM7/MM8 collection. The more aggressive 6×6 profile would
bring the conservative total including decorations to 635,799,186 bytes, but its visible detail loss makes 4×4 the safer
starting point. No desktop BC7 or universal Basis payload size was measured here.

These remain codec probes: all encoded mip images decoded with the expected dimensions, but complete visual acceptance,
recoloring/mip checks, compressed GPU upload, shipping-container integration and Android testing remain necessary.
The total GPU block payload across the entire enhanced library is 2,480,777,696 bytes for 4×4 or 1,105,816,800 bytes for
6×6. Those are whole-library totals, not a claim that every atlas should be resident during gameplay.

## Full MM6/MM7/MM8 replacement-only projection

The user's intended release comparison is the complete trilogy with only its needed restored sprites, replacing native
bitmaps. The earlier 705/889 MB totals describe the partly restored installation and do not answer that scope.

Current native descriptor/action bindings identify 60 MM6, 72 MM7 and 61 MM8 creature-family entries, with one shared art
family: 192 distinct families overall. Palette variants share geometry/art. This projection counts frames reachable from
the eight descriptor actions and stored directions, excluding unreferenced source poses and custom descriptors 901+.
It includes the installed non-creature restoration set: decorations, world items, effects and sprite-based overlays.

| Complete trilogy sprite content | Compressed shipping payload |
| --- | ---: |
| Needed original creature BMPs | 178,021,140 bytes |
| Needed original non-creature BMPs corresponding to the restored set | 12,557,710 bytes |
| Needed original bitmap-style total | **190,578,850 bytes (about 0.19 GB)** |
| Needed x2 creatures, projected ASTC 4×4 + Zstandard | **about 1.7 GB** |
| Restored non-creatures in their existing PNG representation | **about 0.18 GB** |
| Needed x2 trilogy sprite total, projected | **about 1.9 GB; budget approximately 2 GB** |

The original selected files total 1,319,862,764 bytes loose. Their compressed total uses matching existing ZIP-entry
sizes, or equivalent per-file DEFLATE-6 payloads when an entry is unavailable. Shared physical BMPs are counted once.
This is the OpenYAMM bitmap representation, not the original games' LOD-container footprint. Snow excluded by the user's
restoration scope remains excluded here. Historical missing source names do not acquire invented images in this estimate.

The x2 projection uses the measured 60 installed MM6 package encodes as calibration: 491,957,549 compressed page bytes
for 620,014,581 unique enhanced crop pixels, approximately 0.793 compressed bytes per cropped pixel. That cost includes
the measured packing/gutters, base and material-mask mip levels, page metadata and picking masks. It is applied to the
needed crop rectangles in available enhanced manifests for 60 MM6, 67 MM7 and 30 MM8 family entries; these candidates
are geometry evidence, not a declaration that all artwork has passed final acceptance. Missing-family crop area is
estimated from native foreground bounds using the measured enhanced/native area ratio of approximately 4.316.

Before deducting shared art, the projected creature contributions are approximately 462 MB for MM6, 575 MB for MM7 and
691 MB for MM8. The shared air-elemental artwork reduces this by roughly 10 MB. Small manifest/container overhead does
not change the rounded 1.9 GB total including the 184 MB non-creature set. It contains one selected runtime representation
per restored asset, required palette metadata and needed animation frames; native backups, authoring masters, discarded
poses and duplicate platform formats are outside the release projection.

Use **1.5–2.5 GB as a planning range**, not a statistical confidence interval or a promised release size. Compression
entropy, final masks, packing and artwork revisions vary; the calibration comes from one installed world. A full trilogy
runtime cook and visual acceptance are still necessary. This is roughly a tenfold compressed-size increase over the
original native-resolution indexed BMPs. It compares different-resolution artwork, not an intrinsic atlas-format penalty.
Maps, world surface textures, UI packages, audio, video and executable sizes are outside both totals.

## Complete MM6 Goblin example

The follow-up measured all four Goblin pages: 59 frame names, 58 distinct crops and three shared palette variants
(745/746/747). This covers the full installed family, not only the page-0 sample above.

| Representation of the complete Goblin family | Disk footprint |
| --- | ---: |
| Original 59 indexed BMPs, loose | 5.85 MiB |
| Those same BMPs inside the existing `engine.zip` | 0.784 MiB |
| Current x2 PNG atlas pages, masks and JSON | 13.50 MiB |
| Additional current raw cooked pages | 110.26 MiB |
| Current x2 PNGs + masks + JSON + raw cooked pages | 123.77 MiB |
| Replacement lossless Zstandard cooked pages + JSON | 21.41 MiB |
| Replacement ASTC 4×4 + Zstandard, including metadata | approximately 9.10 MiB |
| Replacement ASTC 6×6 + Zstandard, including metadata | approximately 4.63 MiB |

The PNG total contains 10.01 MiB of color, 3.48 MiB of masks and 12,311 bytes of JSON. The native ZIP entries were
verified against all 59 loose files by size and CRC. Their size is the existing OpenYAMM ZIP contribution, not a measured
portion of the original game's LOD. Shared native gameplay/sprite tables and palette registries are outside that count.

The full current `engine/sprites` folder contains 20,498 BMPs occupying 1,393,657,556 bytes loose (about 1.4 GB).
Its corresponding entries in the existing `engine.zip` occupy 195,791,337 compressed bytes (about 196 MB), matched by
path and uncompressed size. A compressed-Goblin size ratio must not be multiplied by the loose 1.4 GB folder size.
The Goblin 4×4 prototype is approximately 11.6 times its original ZIP contribution. Applying that ratio to the entire
original collection would give approximately 2.27 GB compressed, but that is only a mathematical illustration: creature,
decoration and effect compression ratios differ, and the enhanced collection's coverage is different. It is not a measured
shipping-size forecast for all MM6/MM7/MM8 artwork.

All four pages were encoded for both ASTC profiles with the same medium-quality settings as the earlier probe. The
compressed totals include all color/mask mip levels, losslessly compressed existing mapping/hit-mask/header data and
the current manifest. Final shipping-container overhead remains additional. The corresponding GPU texture payloads are
36.35 MiB for ASTC 4×4 and 16.20 MiB for ASTC 6×6. These are codec probes, not an installed runtime conversion or a new
visual acceptance of every frame and recolored variant.

The PNG sheets are already atlases; the cooked textures are another encoding of the same artwork. A correctly packaged
release would carry the chosen cooked representation and metadata only. For example, the 4×4 prototype is about 9.1 MiB
total for the family, not 13.5 MiB plus 9.1 MiB. Keep PNG masters for editing/rebuilding outside the shipped package.
The existing runtime source-PNG stat check must be replaced with cooked-payload validation before omitting those files.

## Recommended replacement

1. **Keep the source atlas pipeline and native presentation data.** Preserve the x2 dimensions, alpha-aware filtering,
   poses, directions, placement, timing and shader-driven variants. Group frames into tightly packed bounded pages;
   file count or one-page-per-direction rules are not the main savings opportunity.
2. **Cook compressed GPU textures offline.** Start quality evaluation with ASTC 4×4 for compatible mobile GPUs and BC7
   for compatible desktop GPUs. Consider 6×6 only for assets whose detail/edges survive it. Select formats through GPU
   capabilities and package profiles; Android GLES 3 guarantees ETC2/EAC, not ASTC. Treat material masks as independent
   data with their own quality checks; preserve them losslessly if block artifacts damage recoloring.
3. **Ship one representation per device.** A standard KTX2 container can hold precomputed mip levels and compressed
   payloads. Native format packages minimize load work; KTX2/Basis Universal is an alternative when one asset set
   must cover different GPU families. Android texture-format targeting can deliver one applicable variant. Sideloaded
   APKs need an explicit compatible profile or universal transcoding, rather than an assumption that every GPU has ASTC.
   Do not install desktop and multiple mobile texture copies together.
4. **Remove the runtime dependency on authoring PNGs.** The current cache explicitly stats the source PNGs to validate
   cooked files. Source fingerprint validation belongs in the cooker/packager; the shipped game must validate its cooked
   payload and runtime metadata without those PNGs. Retain compact hit masks for picking so CPU logic does not need to
   expand compressed GPU textures. Keep source art in the authoring tree and omit it from release packages. Preserve
   world-package separation so new MM7/MM8 art does not force every mobile installation to carry unused worlds.
5. **Keep loading readiness and enforce size/quality gates.** Worker threads should read/decompress or transcode only
   the requested pages, then publish their GPU-ready payloads before gameplay. Keep bounded residency. Package already
   supercompressed files without a redundant outer compression pass. Reject raw v1 pages and duplicate source atlases
   in release packaging. Record per-world installed/download sizes and validate actual game loading, RAM and GPU memory
   on desktop plus an Android Release build. Review close/distant animation, thin silhouettes, effects and every palette
   variant before accepting the codec settings. The full-library probe above establishes a payload-size target for the
   current collection; each final platform profile and future collection still needs its own cook and release validation.

The existing renderer already has native compressed-texture format support through bgfx, and the desktop build includes
the Arm ASTC encoder. Its bimg loader handles KTX1, not KTX2/Basis, so selecting KTX2 requires an explicit loader
integration; changing the extension alone is insufficient. The parallel loading, atlas residency and readiness work can
remain while this representation changes.

## References and receipts

- [Machine-readable measurements](../../tools/asset_loading/atlas_footprint_20260927.json).
- [Khronos KTX](https://www.khronos.org/ktx/) documents compressed texture containers and universal transcoding.
- [Khronos texture-quality guidance](https://github.com/KhronosGroup/3D-Formats-Guidelines/blob/main/KTXArtistGuide.md)
  distinguishes compact transmission, GPU memory and visual-quality tradeoffs; compressed GPU textures are not always
  smaller than PNGs on disk.
- [Android texture-format targeting](https://developer.android.com/guide/playcore/asset-delivery/texture-compression)
  describes capability coverage and delivery of device-appropriate formats.
- [Arm ASTC format overview](https://github.com/ARM-software/astc-encoder/blob/main/Docs/FormatOverview.md)
  documents block sizes and their lossy quality/bitrate tradeoff.

Private compression probes and raw measurement details are under `/tmp/openyamm-atlas-footprint/`. No production
runtime files, installed atlases or accepted artwork were changed by this review.
