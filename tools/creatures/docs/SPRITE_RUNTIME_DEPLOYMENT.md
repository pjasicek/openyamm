# Creature sprite deployment and release packages

`assets_dev/engine/sprites_new` is the desktop **cooked runtime installation**.
`assets_cooked/android/sprites_new` holds the separately cooked Android installation.
Both profiles belong in normal Git; authoring inputs remain local or in optional LFS banks.
Each release's engine content packs contain exactly one GPU texture profile. Windows/Linux use the same desktop
profile; Android uses its own profile. The files share a container/schema, not a combined payload.

## Authoring and installation

Keep accepted artwork, generation prompts, registration, reviews and masters in the creature's existing
project under `level_generation/creatures`. Export the runtime-ready source sheets to:

```
assets_source/engine/sprites_new/<family>/
  manifest.json                 # source/export schema_version: 1
  atlas/base_0.png               # accepted x2 RGBA art
  atlas/mask_0.png               # shared material masks
  atlas/palette_*.rgba32f        # only when required by the palette model
```

Include every required pose/direction, native aliases, crop origins, logical canvas/pivot, scale and
all palette variants. A family has one base/mask set shared by its variants; never create full color
atlases per variant. Frame timing, directional selection, mirroring and native actor scale remain in
the authoritative `engine/rendering` sprite tables. Do not change those bindings to compensate for compression.

After accepting the artwork, install it with the common cooker:

```sh
cmake --build build --target openyamm_sprite_atlas_cook -j25
python3 tools/cook_sprite_atlases.py --profile desktop --family mm6_gob
python3 tools/cook_sprite_atlases.py --profile android --family mm6_gob
# Omit --family to synchronize all accepted source exports.
python3 tools/cook_sprite_atlases.py --profile desktop --verify
```

The ordinary `openyamm` build validates prebuilt desktop pages without cooking. Authors explicitly
cook accepted changes for both profiles before committing the results. Source and output hashes plus
the cooker identity detect changes; build receipts live under the source root's ignored `.cook-cache`,
never in runtime assets. Replacement is staged and fully verified before the old family is retired.
An interrupted publication's `.previous` directory must be recovered explicitly, not silently ignored.

The existing MM6 installer and custom crusader/mage installers now export into `assets_source` and
invoke this deployment step before publishing their sprite-table bindings. Their authoring/acceptance
hashes still describe the lossless source exports. Cooked output has separate deployment receipts.

The initial migration preserves all 62 installed source packages outside runtime mounts. Its source
hash inventory is `assets_source/sprite_migration_20260927.json`. Source sheets are rebuild inputs,
not files shipped alongside the GPU textures. Keep them backed up with the authoring projects.

## What belongs in sprites_new

```
assets_dev/engine/sprites_new/<family>/
  manifest.json                 # schema_version: 2, texture_profile: desktop
  runtime/page-0.oyatlas        # both shared textures, mips and exact picking bits
  runtime/page-1.oyatlas
  atlas/palette_*.rgba32f        # only lookups referenced by the manifest
```

No PNG/BMP sheets, preview recolors, native duplicate sprites, generation grids, stamps, backups,
quality reports or alternate platform profiles belong in this directory. The verifier rejects extra
files, missing pages, wrong profiles, invalid frame coverage, corrupt/truncated compressed data and
oversized allocations. Runtime loading explicitly requires schema 2; it cannot silently rebuild a
stale package from PNGs. Standalone verification does not require `assets_source` to exist.

The shared indoor/outdoor atlas outline pass derives its ring from the existing colour texture's
alpha. It draws a two-screen-pixel outline using linear sampling and the existing frame-isolated
mips: one centre sample plus up to sixteen neighbour samples at two radii. Fully opaque interior
pixels exit after the centre sample. Soft alpha fringes participate in the ring instead of being
excluded by a near-zero-alpha cutoff. Uniformly translucent interiors do not become solid outlines.
This adds no creature files, texture allocations, loading work or preprocessing. The existing extra
billboard submission occurs only for outlined sprites; ordinary colour/material/palette draws are
unchanged. Quad padding follows projection and viewport size without moving the original pivot.
Standalone native bitmaps retain their existing outline path. Actual GPU cost depends on outlined
screen area and hardware; texture-fetch count is not an FPS measurement.

The distance-sidecar experiment is retired. The deployment wrapper explicitly migrates its verified
packages back to colour/mask-only packages, reusing original bytes only when source hashes, profile,
manifest and the complete installed inventory match the receipt. Obsolete `.oysdf` files are dropped
by staged replacement, and source-free verification rejects them as extra files. Subsequent cooker
upgrades, source changes or `--force` recook all payloads. Artwork acceptance hashes remain unchanged.

The schema-2 page entry replaces `base`/`mask` with `texture: runtime/page-N.oyatlas`. `size` and frame
`atlas_xywh` remain the source packing coordinate domain for stable authoring/placement comparisons.
The cooked page contains the checked GPU rectangles after gutter packing. Crop dimensions/origins,
logical scale and native frame identity stay unchanged.

## Texture profiles and loading

| Profile | Base RGBA | One mask channel | Two mask channels | Four mask channels |
| --- | --- | --- | --- | --- |
| `desktop` | BC7 | BC4 | BC5 | BC7, independent linear channel weights |
| `android` | ETC2 RGBA8 | EAC R11 | EAC RG11 | ETC2 RGBA8, independent RGBA channel error |

Android already requires OpenGL ES 3.0, which includes ETC2/EAC. Desktop requires native BC7 support
(including OpenGL BPTC); unsupported hardware gets an explicit error instead of an unexpected full-RGBA
allocation. ASTC is not part of this initial release contract.

Both profiles use `.oyatlas` version 2: a small little-endian header, a manifest binding and bounded,
checksummed Zstandard payload containing the native GPU blocks, mip dimensions, GPU rectangles and
one-bit picking masks. This extends OpenYAMM's existing container; it is **not KTX2**. The texture
codecs themselves are standard GPU formats. No transcoder or texture encoder is shipped to the game.

Mips 0–4 are prepared offline with alpha-weighted reduction and 16-pixel frame gutters. The shader
caps its LOD at 4, preserving frame isolation. The original alpha creates lossless picking masks before
GPU compression. GPU compression is lossy: inspect fine features, edges and palette variants after
cooking, on representative dark/light backgrounds. Mask alpha is material data, never transparency.
Desktop BC7 uses bc7enc; Android RGBA uses Etc2Comp at effort 80, and scalar masks use etcpak EAC.
The fast ETC2 color encoder was rejected during visual review because it lost fine detail.

Loading reads only metadata, cooked blocks and needed palette lookups. Bounded workers unpack and
validate Zstandard; the render thread uploads native blocks directly. There is no runtime PNG decode,
frame packing, texture encoding or mip generation. The existing loading readiness pass prewarms
referenced families and variants before gameplay. Residency stays bounded by the existing shared
cache, with active level resources pinned; visiting maps does not accumulate every family forever.

## Migration measurements — 2026-09-27

The converted installation has 62 packages, 237 pages and 3,654 frame entries. These are the installed
creatures, not an estimate for a future complete MM6+MM7+MM8 restoration. Decimal MB below include
the required manifests and palette lookups. ZIP sizes count sprite entries only, excluding unrelated
engine assets and ZIP directory overhead.

| Asset set | Files on disk | Sprite entries inside `engine.zip` |
| --- | ---: | ---: |
| Preserved lossless authoring exports | 747.6 MB | Not shipped |
| Desktop BC7/BC4/BC5 | 476.9 MB | 475.4 MB |
| Android ETC2/EAC | 343.4 MB | 341.9 MB |

The Goblin package is 8.88 MB on desktop and 7.86 MB on Android, with all variants sharing its four
pages. Neither runtime profile contains PNGs. All 610 preserved source files match the migration
inventory's SHA256 hashes.

New Sorpigal's resident creature atlas allocation fell from 448 MiB in the raw-atlas implementation
to 131 MiB with this desktop profile (about 71% less). This is creature atlas residency, not total
game VRAM. One warm desktop run recorded 129 ms for sprite preloading and 3.0 seconds for the whole
map load; this is not a controlled cold-start speed comparison.

Validation: normal desktop build; 18 atlas unit tests / 4,151 assertions; six deployment/package
tests; all pages verified without authoring images; packaged MM6 outdoor and indoor visual checks
on OpenGL with an RTX 3060 Ti; MM7/MM8 headless outdoor/indoor/return scenarios. Twelve representative
palette variants were compared against their source on light/dark backgrounds using independent
GPU-block decoders. Android asset cooking and packaging pass; an Android APK/device test remains
unverified in this historical migration record. The local Android SDK was installed separately in October.

## Release packaging

Release content packs come from `tools/package_runtime_assets.py`. A manual desktop build is:

```sh
cmake --build build --target openyamm_verify_sprite_atlases -j25
python3 tools/package_runtime_assets.py --profile desktop --output assets
```

Android packaging uses the checked-in Android profile and does not run texture encoding:

```sh
android/repack_runtime_assets.sh
# Reads assets_cooked/android/sprites_new; writes build/android-assets/index.json and packs/.
android/build_release_apk.sh
```

The engine packs keep the flat engine-relative paths (`sprites_new/...`) and a tiny
`sprite_texture_profile.json` marker. The Android override replaces the **entire** `sprites_new`
directory during packaging; it does not add another profile beside the desktop files. The packager
requires exactly the installed family set, identical animation/placement metadata and byte-identical
palette lookups across profiles, and validates all pages before writing the packs. Cooked
pages are stored without ZIP deflate because they already contain Zstandard; other normal assets
retain their ordinary ZIP compression. Android also marks `.oyatlas` as uncompressed APK entries.
Gradle rejects a content index of another profile.

For external Android content, pass `-Popenyamm.android.runtimeAssetsDir=/absolute/path` to Gradle. For the
repacking script, `OPENYAMM_ANDROID_ASSETS_DIR` selects its output; use the same path in Gradle.
World packs and native sprites still needed by unconverted content remain governed by their normal
asset pipeline. This change does not claim that every original bitmap across all three games is
already superseded or removable.

Installed outdoor lighting also validates hashes of its bake inputs. The packager reads those
dependency records and includes only referenced `assets_dev/_legacy/sprites_original` files in
the engine packs; omitting them breaks map loading. Unreferenced archives stay outside the release.

## Dependencies

Pinned build inputs are declared in `cmake/SpriteAtlasCodecs.cmake`: Zstandard 1.5.7 (BSD/GPL dual
license, BSD use), [etcpak](https://github.com/wolfpld/etcpak) (BSD, with bc7enc/bcdec licenses) and
[Etc2Comp](https://github.com/google/etc2comp) (Apache 2.0). Encoders are host-only dependencies;
Android cross builds need only the portable Zstandard runtime library. Host deployment scripts
require Python 3.11 or newer.
