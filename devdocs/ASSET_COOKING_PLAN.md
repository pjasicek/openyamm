# Asset cooking plan: source → cook decision → runtime (2026-10-09)

Status: **the cooking tools and engine support (steps 1–2) are implemented and tested on scratch copies; nothing in
`assets_dev` or `assets_cooked` is cooked yet** (see §7). Describes how binary art moves from editable masters to the
compressed, deduplicated files the game loads. The first target is model textures (decorations and creatures).
The same pipeline later covers surface textures, icons and sprite atlases.

## 1. Why

Measured on the installed MM6 models (157 decoration GLBs, 25 creature GLBs; 2026-10-09):

| | Package (zip) | VRAM, everything resident |
|---|---:|---:|
| Today: PNG embedded in each GLB | ~800 MB (734 MB images, 68 MB geometry deflated) | ~2.8 GB (RGBA8 + mips) |
| Desktop quality: BC7 colour, BC5 normal, BC1 MR | ~430 MB | ~680 MB |
| Desktop lean: BC1 for opaque colour | ~330 MB | ~500 MB |
| Android: ETC2 / EAC (the atlas profile) | ~280 MB | ~500 MB |

- **Method:** 96 sampled unique textures, encoded with the project's own encoders (etcpak/bc7enc, uber level 2), then
  zstd level 9 as for `.oyatlas`, projected over the 531 Mpx of unique texture pixels with mips. Expect about ±10%.
- **Measured rates in bytes per pixel after zstd:**
  - Colour: BC7 0.61, BC1 0.28, ETC2 0.28, ETC2A 0.33.
  - Normal: BC5 0.54, EAC RG 0.45.
  - Metal/roughness: BC1 0.19, ETC2 0.16.
  - Today's PNGs average about 1.0.
- **Duplicates:** 201 MB of the 734 MB of images are byte-identical copies, such as the shared bark, corpse and torch
  sets embedded in every GLB that uses them. The renderer already uploads each identical image once
  (`ModelRenderer::m_sharedTextures`), but the package still stores every copy.
- **Encode cost:** BC7 takes 1.6 s for a 2048² texture on 16 threads; BC1, BC5 and ETC2 take about 0.2 s. A full model
  cook is a few minutes, and an incremental one takes seconds.

## 2. The three stages

```
assets_source/                 cook decision                    assets_dev/  (+ assets_cooked/<profile>/)
editable masters      ->  rules + per-asset overrides  ->  what the game loads (desktop profile)
lossless, any size        recorded in a cook ledger         android profile as an overlay
```

### 2.1 `assets_source/`: masters

- **Contents:** everything a builder or artist edits or regenerates:
  - Blender `.blend` files.
  - Lossless GLBs with full-resolution PNG textures (what the builders export today).
  - Meshy returns, Codex HD masters and sprite source frames. The last already live here
    (`assets_source/engine/sprites_new`, 32 GB).
- **Layout:** mirrors `assets_dev`, e.g. `assets_source/engine/models/mm6_deco_torch.glb`, so the mapping is one
  path, not a table.
- **The game never mounts it.** Builders (`--install`) write here instead of into `assets_dev`.
- **Git:** today `/assets_source/` is ignored, and `.gitattributes` already routes its PNG/BMP/TIFF/EXR/PSD/KRA/BLEND
  files to LFS when they are added explicitly. See decision D1.

### 2.2 The cook decision

The cooker decides deterministically from the source file and the rules. Nothing is chosen by hand per file unless an
override says so.

- **Inputs:**
  - The source asset and its content hash.
  - The global rules: `tools/cook/rules.yml`, versioned in git.
  - An optional sidecar override beside the source: `<name>.cook.yml`.
  - The profile: `desktop` or `android`.
  - The cooker version.
- **Texture role,** read from the glTF material slot: base colour, normal, metallic-roughness, emissive, occlusion, and
  OpenYAMM's region mask.
- **Measured properties:**
  - Alpha use: none, cutout or blend. 124 of 319 unique colour textures carry alpha, mostly leaves.
  - Channel count.
  - Texel density: texels per world unit, from the UV area against the mesh area at the binding height.
- **Default format by role and profile:**

  | Role | Desktop | Android | Notes |
  |---|---|---|---|
  | Colour, opaque | BC1 (BC7 for `quality: hero`) | ETC2 RGB | sRGB |
  | Colour with alpha | BC7 | ETC2A | Coverage-preserving mips for cutouts |
  | Normal | BC5 | EAC RG | The shader must rebuild z (§4) |
  | Metallic-roughness | BC1 | ETC2 RGB | Keeps glTF's G and B channels; no shader change |
  | Occlusion / emissive (one channel) | BC4 | EAC R | |
  | Region mask (colour tiers) | BC7, linear weights | ETC2A | Like the sprite atlas masks |

- **Resolution:**
  - Normal maps cook at half their source's power-of-two size by default (`normal_scale: 0.5`, overridable per class
    or model). They carry fine relief, not colour, so this saves about a third of the decoration texture bytes with
    no visible loss at MM6 viewing distances.
  - Creatures and their attachments (`worlds/*/models`, 2026-10-21, after the MM8 creature audit found them soft)
    keep full-size normal maps on desktop (`normal_scale: {desktop: 1, android: 0.5}`). Their weak Meshy relief is
    lifted at cook time: `normal_relief: {target: 0.25, max: 3}` multiplies each material's `normalTexture.scale`
    until the map's 90th-percentile tilt reaches 0.25, never weakening an already strong map (MM8 bodies were near
    0.1, about 6 degrees). Their colour mips below the first get an unsharp mask (`colour_mip_sharpening: 0.75`;
    terrain materials use 1 with wrapped neighbours), since the game samples those levels at most viewing distances.
  - Per-class `max_size` caps the rest. Texel-density caps are a future option (§8).
- **Mips:**
  - Always generated offline.
  - Colour is filtered in linear light.
  - Normals are renormalized per level.
  - Cutout alpha keeps its coverage at each level, so distant leaves do not thin out. This is the same idea as the
    atlas cook's alpha-aware filter.
- **Dedupe:** textures are content-addressed after cooking, and identical results are stored once.
- **Output of the decision:**
  - A ledger entry per texture: source hash, rules hash, chosen format, size, mips, output hash.
  - `--plan` prints the decisions and the projected size without writing anything. That is the reviewable "cook
    decision" step.

### 2.3 `assets_dev/`: what the game loads

- **Authored text stays authored where it is:** YAML, TXT, Lua, maps and manifests. Only derived binaries are cooked.
- **Model GLB:**
  - It keeps geometry, skins, animations and material parameters.
  - Each image becomes a plain glTF image URI to a cooked texture, `textures/<key>.oytex`. The key depends on the
    source image and how the model samples it (semantic, alpha cutoff, mips), never on the codec, so every profile
    shares one GLB.
  - `asset.extras.openyamm_cooked` records the source path and its SHA-256.
- **Cooked textures:**
  - One shared, content-addressed store per scope: `assets_dev/worlds/mm6/models/textures/<hash>.oytex`, and the
    equivalent under `engine/` for engine-owned models.
  - The 27 copies of a bark texture become one file.
- **`.oytex` container** (`engine/render/CookedTexture.h`), sharing the sprite atlases' codec ids
  (`engine/render/TextureBlockCodec.h`) and block encoders (`tools/TextureBlockEncode.cpp`):
  - Header: magic, version, codec, semantic, alpha cutoff, width, height, mip count, source hash, sizes and a content
    hash.
  - Body: zstd-compressed mip blocks (level 19).
  - It is not KTX2, because bimg cannot parse KTX2 with zstd supercompression, while the atlas container is already
    proven in this engine.
- **Power-of-two textures:** the cooker area-downscales any other source to the next smaller power of two (sRGB in
  linear light, normals renormalized, cutout coverage kept), so the 2080-wide creature atlases cook at 2048. On the
  OpenGL 3.3 path (NVIDIA), a non-power-of-two sRGB block texture with mips is left incomplete and samples black;
  linear formats at the same size and power-of-two sRGB were fine. Many GLES drivers restrict such textures too.
- **Profiles:**
  - `assets_dev` holds the desktop profile, so day-to-day runs show what desktop players get.
  - The Android profile is an overlay of only the files that differ, in `assets_cooked/android/`, as the sprite atlases
    already do. The packager builds `mm6.zip` from `assets_dev` plus the profile overlay.
- **Builds stay in sync:** the normal host build runs the cooker incrementally, as `openyamm_sprite_atlas_cook`
  already does, and `--verify` fails on stale or missing outputs. Like `STALE_LIGHTING_BAKES.txt`, a stale cook is
  reported, never silently regenerated at runtime and never masked by a fallback.

## 3. Interactions to get right

- **Outdoor bakes:**
  - The bake imports decoration GLBs into Blender, including their alpha for leaf shadows.
  - Cooked GLBs are not Blender-importable, so the bake reads the **source** GLB.
  - Its dependency hash becomes the source hash that the cooked GLB records. Re-encoding a texture, for example
    changing BC1 to BC7, then does not mark 15 maps stale, while any change to geometry or alpha still does.
  - `package_runtime_assets.py` reads that recorded hash from `assets_dev`, so packaging still works without
    `assets_source` present.
- **Model gallery:** the three.js viewer cannot read `.oytex`.
  - Keep it on the source GLBs for shape review.
  - Add a "cooked" toggle that loads decoded previews, which the cooker writes on request with `--preview`, so encoding
    artefacts can be judged.
- **Uncooked content:** MM9, mods and quick experiments may still ship PNG-in-GLB. That stays a supported input format,
  not a fallback. Release packaging for MM6–MM8 requires cooked textures and rejects PNG-in-GLB.
- **AGENTS "keep original formats":** the masters keep PNG and GLB. GPU block formats are a runtime derivative, like
  the atlases. The AGENTS line should say so once this lands.
- **Builders in `level_generation/`:** that directory is git-ignored, so the decoration builder scripts are not
  versioned. Anything that must stay reproducible (props_lib, the tree builders, finish/validate) belongs in `tools/`,
  or the masters must be kept, since `assets_dev` will no longer hold a lossless copy.

## 4. Engine work

1. **`CookedTexture` module:** `.oytex` write/read/validate, zstd and codec-to-bgfx format, with the codec ids
   shared with the sprite atlases. Unit tests: round trip, truncation, version, semantic and hash rejection.
2. **glTF loader:** accept `.oytex` image URIs; the renderer uploads block formats with their stored mips and keeps
   the shared-texture cache keyed by content.
3. **Shaders:**
   - The `fs_model` normal path rebuilds z from a two-channel normal (BC5 / EAC RG).
   - Colour samplers keep sRGB via `BGFX_TEXTURE_SRGB`.
   - Check the region-mask path against the linear BC7 mask.
4. **Capability checks:** BC formats on desktop, ETC2 on Android (GLES3 guarantees it). Missing support is a startup
   error naming the profile, not a decode to RGBA.
5. **Packager:**
   - Model textures join the profile overlay.
   - The ledger is verified before zipping.
   - `--report` prints sizes per class.

## 5. Order of work

| Step | What | Gate |
|---|---|---|
| 0 | Decide D1–D3 below | User |
| 1 | `CookedTexture` + `.oytex` + loader/shader support | Done: unit tests; cooked and source captures match (§7) |
| 2 | `tools/cook_models.py` + `openyamm_model_texture_cook` with `--plan`, `--verify`, `--force`, `--preview`; `tools/cook/model_textures.yml` | Done; next: `--plan` report for all MM6 models reviewed by the user |
| 3 | Pilot cook: torches, one tree (cutout leaves), one creature with colour tiers | Side-by-side captures (source vs desktop vs android) approved |
| 4 | Migration: move the 182 MM6 GLBs to `assets_source/worlds/mm6/models/`, point builders' `--install` there, cook all, switch bake dependencies to the recorded source hashes and the bake's Blender import to the source GLBs, re-bake | `stale_bakes.py` 0, decoration/creature regressions pass, package size and VRAM measured |
| 5 | Android profile overlay and release APK check | Release APK on device: memory, load time, visuals |
| 6 | Same pipeline: MM6–MM8 surface textures **done 2026-10-11 (§9)**; next `icons_x2`, then fold the sprite atlas cook in as one cook kind | Per kind |
| 7 | Optional: geometry compression (meshopt/quantization; 137 MB raw geometry) | Measured gain worth the decoder dependency |

## 6. Decisions needed

- **D1 Git:** what is versioned?
  - **(a) Recommended:** masters in `assets_source` via LFS; cooked output is a build product, git-ignored, made by the
    host build.
    - For: history stays clean, and any re-cook is reproducible.
    - Against: a fresh clone needs the sources (LFS) and a few minutes of cooking.
  - **(b)** Cooked `assets_dev` in git, masters kept locally or archived.
    - For: clone and run immediately.
    - Against: every re-cook adds hundreds of MB to `.git` (already 16 GB), and the masters can be lost.
  - **(c)** Both in git.
  - Note: today 268 `.oyatlas` pages are tracked although the loading notes call them derived.
- **D2 Desktop quality tier:**
  - Option 1: BC7 for all colour, the "desktop quality" row (~430 MB).
  - Option 2: BC1 for opaque colour, with `quality: hero` overrides for creatures and close-up props (~330 MB).
  - Recommended: option 2, chosen after the step 3 pilot captures.
- **D3 Android codec:** stay on ETC2/EAC like the atlases, or adopt ASTC, which has better quality per bit and is
  widely supported but not guaranteed by GLES3. Recommended: ETC2 now, and measure ASTC at step 5.

## 7. Implemented tools (2026-10-09)

Commands (the cooker is a host tool: `cmake --build build --target openyamm_model_texture_cook`):

```sh
tools/cook_models.py --plan [--only 'engine/models/mm6_deco_*.glb']   # decisions and projected sizes
tools/cook_models.py --profile desktop      # assets_source -> assets_dev (GLBs + textures)
tools/cook_models.py --profile android      # assets_source -> assets_cooked/android (textures only)
tools/cook_models.py --verify               # cooked GLBs, both profiles' textures, uses and leftovers
build/game/openyamm_model_texture_cook --preview <file.oytex> <out.rgba> [level]   # decode for review
```

- **Receipts:** `assets_source/.cook-cache/models/<profile>.json`. A texture re-cooks when its source image, decision,
  rules file or cooker binary changes. A full cook (no `--only`) removes cooked textures that no model references.
- **Decisions:**
  - Texture uses mirror `ModelRenderer::prepare`, including the float32 alpha-cutoff arithmetic.
  - Slots the engine does not sample (emissive, occlusion, textures in material extensions) are rejected, not
    dropped.
  - A texture shared by models of different classes takes the larger size and the higher-quality codec of its uses.
- **Engine:** `.oytex` images upload as block textures with their cooked mips. The renderer rejects a texture cooked
  for another use, and one whose codec the GPU cannot sample (naming the profile); there is no RGBA fallback. The
  model shader rebuilds normal z from x and y; full-colour PNG normals give the same result.
- **Packaging:**
  - `package_runtime_assets.py --profile android` substitutes `assets_cooked/android/<package>/**/models/textures`
    and fails when that set differs from the cooked textures in `assets_dev`. `.oytex` is stored without deflate.
  - Since 2026-10-15 (MM6 ships no sprites) release zips include each package's `models/`: every GLB, the cooked
    textures and the runtime manifests (`release_model_file`). README, review/stress manifests and fixtures stay out.
    MM8 shipped no `models/` until release 1.7 (its monsters kept sprites); since its sprites were retired, every world
    ships its models.
- **Shared encoder:** the sprite atlas cooker now uses `tools/TextureBlockEncode.cpp` too. Its output is
  byte-identical to before for both profiles (checked on `mm6_rat`), and the 60 installed packages verify.
- **BC1 fix:** etcpak can quantize both endpoints of a nearly uniform block to one colour. That selects BC1's
  three-colour mode, where index 3 is transparent black, and metallic-roughness maps are mostly such blocks. The shared
  encoder rewrites every BC1 block in four-colour form. Covered by the near-uniform case in
  `tests/CookedTextureTests.cpp`.
- **Tested on scratch copies** of seven MM6 models (torch, tree02, fountain, bear pedestal, corpse02, goblin, female
  peasant), loaded from a hard-linked copy of `assets_dev` via `--set assets.root`:
  - New Sorpigal captures (fountain, tree02, goblin and peasant) match the PNG versions: mean colour within 0.1/255.
  - Decoded textures differ from their sources by about 0.3–4.4/255 per channel on average.
  - Desktop textures cooked in 6 s. Android took about 4 minutes, since etc2comp at effort 80 (the atlas setting) is
    slow; a full MM6 Android cook could take most of an hour.
- **Not done:** the migration (step 4), the gallery's cooked toggle, texel-density caps, and the Android device check.

## 8. Future cook options (measured 2026-10-09, not enabled)

The MM6 totals with the current defaults (BC1/BC7 colour, half-size normal maps) are about 290 MB on desktop and
230 MB on Android for all 182 models: about 165 / 140 MB for decorations and 125 / 90 MB for creatures, geometry
included. The half-size normals took decorations from about 222 MB to 165 MB. For comparison, the 2D sprites these
models replace come to about 250 MB on desktop.

Further decoration savings, judged visually lossless, that the cooker could add as rules when needed:

| Option | Saves (desktop) | Notes |
|---|---:|---|
| Alpha-tested colour (leaves, clumps) as BC1 with 1-bit alpha, or ETC2 RGB A1 on Android, instead of BC7/ETC2A | ~24 MB | Alpha-tested foliage is already a hard cutout. Blended flames and water (3 MB) stay BC7. |
| Geometry quantization (KHR_mesh_quantization: 16-bit positions/UVs, 8-bit normals) | ~15–20 MB of 43 | Needs loader and vertex-layout support. Mesh compression (meshopt) would save another 10–15 MB but adds a decoder library. |
| Texel-density caps (texture side at most about 8 texels per world unit of the binding height) | ~12 MB | Trims textures larger than a small prop can ever show. Needs the binding heights from the manifests. |
| Near-constant metallic-roughness maps replaced by material factors (40 maps) | ~3 MB | Exact. |

Not recommended: cutting colour texture resolution broadly, or shrinking tree textures below their close-range
detail; that is where visible loss starts.

## 9. World surface textures (implemented 2026-10-11)

One cooked tier per platform, from sources in `assets_source` (Git LFS):

| Profile | Source | Cooked into | Codec |
| --- | --- | --- | --- |
| desktop | `assets_source/worlds/<w>/textures_x4/*.png` | `assets_dev/worlds/<w>/textures_x4/<stem>.oytex` | BC7 |
| android | `assets_source/worlds/<w>/textures_x2/*.png` | `assets_cooked/android/worlds/<w>/textures_x2/<stem>.oytex` | ASTC 4x4 |

`assets_dev` holds no x1 or x2 surface tier: the original x1 BMPs (MM6–MM8 worlds, and the engine `terrain` folder)
are source art in `assets_source` under the same relative paths, and the x1 `textures` folders keep
only the `.act` palettes. The game defaults to x4 surfaces on desktop and x2 on Android. The terrain loads no tile
art (since 2026-10-15 it is drawn from ground materials): the native `terrain_x2` tiles are source art in
`assets_source/worlds/<w>/terrain_x2`, read by `tools/terrain_materials.py` for the weights and liquid edge masks.

Liquids (water, tar, lava; `assets_dev/engine/liquids/liquids.yml`) have no tile or face art: the liquid shader draws
them from their kind and colour. The cooker skips liquid face textures, and the legacy liquid tiles and animation
frames (`*wtrtyl`, `lavtyl`, `tartyl`, `hdwtr`, `hdlav`, `hwoil`, ...) are source art in
`assets_source/worlds/<w>/terrain_x2`, with the edge overlays (`wtrdr*`, `lv*`, `tr*`), whose alpha the runtime
reads only as cooked coverage masks (`worlds/<w>/terrain_materials/liquid_edges`).

- **Format:** BC7, raw (non-sRGB) texels as the BModel path samples BGRA8, the runtime's box-filtered mip chain
  (`prepareBgraMipChain`, no cutout coverage), the magenta key applied as at load, exact source size (all sources are
  power-of-two). BC1 was measured on 48 sampled x2 textures: 33.8 dB mean PSNR (26.7 worst, visible block steps on
  ornament) against BC7's 45.5 dB, at 0.4 of BC7's size.
- **Container:** `.oytex` version 2 adds the source's alpha use (opaque, cutout, partial) and mean colour, so the loader
  needs no pixels for transparent batching or the water tint. Version 1 files (terrain materials) stay readable.
- **Runtime:** `Engine::findCookedOrImageAssetPath` prefers `.oytex` within each scale tier (a source in the active
  tier still beats a cooked file of another tier, as in `tex.py` review stages). `loadCookedSurfaceTexture`
  (MapAssetLoader, also used for event-script textures) rejects a corrupt file or one cooked for another use, never
  falling back to the source. Indoor 2D, outdoor 2D and outdoor texture arrays upload the blocks directly
  (`createCookedTexture2D`, `createCookedTexture2DArray`); a GPU without BC7 is an error naming the profile.
- **Tools read the sources in `assets_source`:** the lighting bake (`bake_assets.texture_paths` searches each package
  in `assets_dev` then `assets_source`; recorded dependency names stay relative to the runtime tree and resolve
  through `bake_assets.dependency_file`, so installed hashes stay valid), `stale_bakes.py`, the development stale
  check that `MapAssetLoader` once had (removed 2026-10-15), `tex.py`, the sky and minimap tools. The editor previews cooked x4 at the native mip.
  The cooked files are committed, since CI checks out neither `assets_source` nor the cook scripts; with the submodule
  checked out the `openyamm` build runs `openyamm_cook_surface_textures` incrementally (receipts in
  `assets_source/.cook-cache/surface_textures/`, about 0.4 s when nothing changed; bump `COOK_REVISION` when the
  cook's output changes). `tools/cook_surface_textures.py --verify` fails on a missing, stale or orphaned cooked file.
- **Packaging:** desktop world packages ship `textures_x4/*.oytex`, android packages the ASTC x2 overlay; both keep
  `hwsplat04.png` (the blood splat decal reads it as an image) and fail on a stale cook.
- **Measured** (`OPENYAMM_MAP_LOAD_TIMING=1`, x2 tier, two runs each, source → cooked):
  - outc2 "outdoor bmodel textures built" 457/429 → 125/155 ms; "world render resources initialized" 713/619 →
    490/572 ms.
  - 6d01 "indoor textures built" 275/274 → 113/103 ms.
  - Captures of both maps match the source renders (mean difference 0.25/255).
- **Sizes:** x2 791 MB of PNG → 485 MB cooked (−39%); x1 64 MB of BMP → 72 MB (BC7 is 8 bits per texel like the
  palettized BMPs, so x1 gains load time, not size). VRAM for surface textures drops to a quarter of RGBA8.
- **Android cook:** 3,857 x2 textures, ASTC 4x4 (medium preset), 763 MB of PNG → 491 MB.

## 10. HUD art: Obsidian illustrations and portrait face sets (implemented 2026-10-11)

`tools/cook_ui_textures.py` (run incrementally by the `openyamm` build for desktop, target
`openyamm_cook_ui_textures`) cooks BC7 into `assets_dev/engine/icons_x2` and, with `--profile android`, ASTC 4x4
into `assets_cooked/android/engine/icons_x2` (since 2026-10-15; 72 MB):

- **Obsidian art** (sources `assets_source/engine/icons_x2/obsidian_*.png` since 2026-10-15, 196 files, 57 MB of PNG
  → 31 MB): one `.oytex` each with mips (the `UiIllustration` profile). Only the HUD uses it, so `assets_dev` holds
  the committed desktop cook and no PNG; without the submodule the cook keeps those files as they are. About 67 are preloaded at the first gameplay map load of a session: "shared ui runtime
  initialized" on outc2 went from 1039/1122 ms to 306/307/409 ms.
- **Portrait face sets** (`pcNN-01..56`, `girla01..56`, ..., 53 sets, 2,968 frames, 102 MB of PNG → 39 MB), cooked
  from the PNGs in `assets_dev` (committed desktop outputs beside them): one atlas per set, `faces_<set>.oytex` with `faces_<set>.yml` (frame size, columns, frame names). The HUD loads a party
  member's whole set on its first frame and cuts each frame's blocks out as its own texture (no decode, no mips, as
  the `Ui` profile), so expression changes never decode a PNG.
- **Decode:** the HUD's colour keys and transparent-edge bleed (`Engine::bleedTransparentBgraEdgeColors`, shared with
  the runtime upload), then edge-replicated padding: to whole 4x4 blocks, and to power-of-two sides for mipped art,
  because NVIDIA's OpenGL 3.3 driver samples a mipped non-power-of-two block texture as black (seen with linear BC7
  too, on the first in-game capture). The `.oytex` v2 header records the content size; `GameplayUiRuntime` keeps a
  per-handle UV scale that every HUD submit path (quads, ellipses, arcs, rotated quads, both batches) applies.
- **CPU uses** of cooked art (tinted copies, opaque bounds, journal compositing, the hover hit test of art with no
  PNG) decode the texture's cell once with bimg (`decodeCookedTextureRegionBgra`, BC7 or ASTC) into
  `GameplayHudTextureData::bgraPixels`.
- **Not cooked:** item icons and other icons (CPU paperdoll compositing and hover tests read their PNGs), and the menu
  screens (`MenuScreenBase`, including character creation portraits) still read PNGs, so every package keeps those
  `icons_x2` PNGs. Android packages take the ASTC HUD art from the overlay (`overlay_model_textures`).

## 11. Effect sprite atlases (implemented 2026-10-12)

`tools/cook_effect_textures.py` cooks every authored effect sprite whose descriptor
(`assets_dev/engine/effects/authored/sprites/<name>.yml`) names an `atlas`, today the 15 melee sprites:

| Profile | Source | Cooked into | Codec |
| --- | --- | --- | --- |
| desktop | `assets_source/engine/effects/authored/textures/<name>_NN.png` | `assets_dev/engine/effects/authored/textures/<name>.oytex` | BC7 |
| android | the same | `assets_cooked/android/engine/effects/authored/textures/<name>.oytex` | ASTC 4x4 |

- **Sources:** procedural frames written by `tools/fx/generate_melee_effects.py`, which then runs the cook. They are
  local (`assets_source` is not tracked), so the cooked atlases of both profiles are committed and a checkout runs and
  packages without them. `--verify` checks presence, headers and orphans everywhere, and freshness where the sources
  exist.
- **Atlas** (`effect_atlas` job of `openyamm_model_texture_cook`): what `EffectRenderer::loadAtlas` builds at load from
  PNG frames: plain decode, frames row by row in `atlasColumns` columns of the frame size, the Billboard upload's
  transparent-edge bleed over the whole atlas, no mips (the Billboard profile has none), linear. Frame sides must be
  whole 4x4 blocks.
- **Descriptor:** `atlas` (a texture binding to the `.oytex`), `atlasColumns`, `frameCount`, `frameWidth` and
  `frameHeight` replace the `frames` list. The renderer uploads the blocks (`createCookedTexture2D`) and derives each
  frame's UVs with the same half-texel inset; an atlas whose header does not match its descriptor is an error, never
  a fallback. Ribbons still need uncooked sprites (the loader rejects a cooked one).
- **Packaging:** the android engine package takes the ASTC atlases from the overlay (`overlay_model_textures`), and
  fails when the overlay's set differs from the desktop one.
- **Sizes:** 35 source frames, 404 KB of PNG → 280 KB (BC7) and 288 KB (ASTC) on disk; about 2.1 MB of GPU memory
  instead of 8.6 MB of RGBA8, and no PNG decode on first use.

## 12. Geometry passes, incremental cook and migration (2026-10-12)

Prepared; the cook is not run yet: the user switches to cooked models later. Tested on scratch copies only.

- **Geometry passes** (`tools/cook_model_geometry.py`, before the textures): hidden back faces culled (single-sided
  materials; reversed copies for triangles whose back can be seen; see `engine/render/MODEL_RENDERING.md`), then
  vertex cache order. The ray tests and the ordering run in the cooker (`openyamm_model_texture_cook --geometry`,
  `tools/CookModelGeometry.cpp`: own BVH, all cores, meshoptimizer from bgfx's `3rdparty`); no Blender. Results match
  the first Blender version triangle for triangle on six creatures. The cooked GLB records them in
  `asset.extras.openyamm_cooked.geometry`; the loader then skips its own vertex cache ordering.
- **Incremental and idempotent:** a model receipt (`model:<path>` in `assets_source/.cook-cache/models/<profile>.json`)
  holds the source hash, the `.cook.yml` sidecar hash, the rules, the cooker binary, the cook scripts and the geometry
  parameters, the cooked GLB's hash and its textures' decisions. An unchanged model with intact outputs is skipped
  without parsing; anything else is cooked again; the same inputs give byte-identical files (checked: a fresh cook of
  ten models matched file for file). A full run also removes cooked GLBs whose source is gone. Measured on ten models:
  first cook 18 s (mostly BC7), one changed model 7 s, nothing changed 0.4 s.
- **Build (2026-10-15, user decision):** desktop cooks stay automatic and incremental: `tools/install_model.py` cooks
  each install, and every `openyamm` build runs `openyamm_cook_assets` (model, surface, HUD and sky cooks into
  `assets_dev`; `-DOPENYAMM_COOK_ON_BUILD=OFF` skips them). Android cooks only on demand, before a release or push:
  `tools/cook_android.sh` (all Android cooks, incremental, then `--verify`). Receipts record `COOKER_REVISION` in
  `tools/cook_models.py` (bump it when the cooker's output changes) instead of the cooker binary's hash, which
  changed with every engine rebuild and made the next cook redo every texture (about an hour for Android).
- **Sources (done 2026-10-12, user decision):** every accepted model GLB is a source in
  `assets_source/worlds/mm6/models/` (233) and `assets_source/engine/models/` (6 satchels); `assets_dev` keeps
  uncooked runtime copies at the same paths until the switch. Creatures processed in place earlier that day were
  restored from their pre-processing copies (30); the harpy's only versions were processed (`openyamm_backface_split`),
  which the cook accepts. All installs go through `tools/install_model.py` (AGENTS.md), which writes the source and,
  until the switch, the runtime copy with hidden back faces culled (`tools/model_backface_split.py`, now a thin wrapper
  over the cook's pass: 0.25 s per creature). The sources are git-ignored like the rest of `assets_source` (D1 open).
- **Decorations cooked (2026-10-12, user decision):** the 157 `mm6_deco_*` models in `assets_dev` are the cook's
  output (`--only 'worlds/mm6/models/mm6_deco_*.glb'`, 19 s, 613 textures); creatures, attachments and satchels stay
  uncooked copies. Disk 642 → 172 MB. New Sorpigal: bgfx texture allocation 2.40 → 1.37 GB (model textures 1,412 →
  382 MB, the rest of that being the uncooked creatures); the same view matches the uncooked one (mean difference
  1.5/255, wind and clouds). Bake dependencies on models now resolve to the sources (`bake_assets.dependency_file`,
  `bake_outdoor.py`'s model import, the game's stale-bake check in `MapAssetLoader.cpp`), so the cooked runtime
  copies leave the bakes current. `tools/install_model.py` cooks decorations (`COOKED_MODELS`). Open: the Android
  textures for them (`--profile android`), which the Android packager requires for every cooked model texture.
- **The switch** (when the user decides): `tools/cook_models.py --migrate` (lists models found only in `assets_dev`;
  `--apply` moves them), `tools/cook_models.py --profile desktop` (replaces the runtime copies with cooked ones),
  `--profile android`, then set `COOKED_MODELS = True` in `tools/install_model.py` (cooking itself runs on demand,
  see Build above).
- **Still open for step 4:** the lighting bake dependencies (decoration GLB hashes in `stale_bakes.py` and the bake's
  Blender import) must switch to the sources; D1 (what git versions) decides `.gitignore`; the Android cook is slow
  (etc2comp at effort 80: 6 minutes for one creature's four textures).

## 13. The switch for creatures (2026-10-14, user decision)

Every model is cooked now (desktop). `tools/cook_models.py --profile desktop` (about 70 s on all cores) writes the 95
creature, attachment and satchel GLBs and their textures into `assets_dev`; the 164 decorations are unchanged. The MM6
actor regression suite matches the uncooked state (61/64; the three failures predate the switch). `--verify`: desktop
clean (Android textures still missing for every model). `tools/install_model.py` cooks every install
(`COOKED_MODELS = ("*",)`) and a normal build keeps `assets_dev` current (an unchanged run skips all 259 models). The previous uncooked runtime copies are hard-linked in
`output/precook_backup_20261014/`.

Two engine rules the first attempts broke (each rejected the whole MM6 actor registry; rolled back automatically):
- `openyamm_burn_map` (material extras, added for burn deaths) is a texture slot the cook did not know; it now
  collects it.
- Burn maps were read on the CPU (`game/fx/WorldFxSystem.cpp`, burn death vertex sampling), so the cook first kept
  them as embedded PNGs. That cost every burning creature (demon, dragons, drake, wyrm) 250–340 ms of PNG decoding
  and mip building at load, twice-decoded maps and about 5.6 MB of RGBA8 per map. Since 2026-10-15 the geometry pass
  bakes the only value the CPU needs, the red channel at each vertex, into a `_BURN_ORDER` vertex attribute, and the
  burn map cooks as `burn_map` (BC5 desktop, EAC RG android: the shaders read red and green). Cooked GLBs embed no
  images.
A new material extras texture field must be added to `texture_uses` before it can be cooked. If the game needs its
values on the CPU, bake them into the cooked GLB (as the burn order) rather than keeping the image uncooked.

Not changed then: the Android cook (`--profile android`, run in full on 2026-10-15) and D1. Release zips ship
models since 2026-10-15.
Visually lossless reductions are cook decisions (`reductions` in `tools/cook/model_textures.yml`, classes with
`reduce: true`; creature class cap 2048): textures sampled only by LOD1/2/3 meshes, held attachments (1024), flat
maps, roughness maps that measure >= 38 dB at half size, and mostly empty colour maps. The plan estimate went from
about 554 to 503 MB desktop and 358 to 320 MB Android. They replace `tools/minimize_model_textures.py` (removed), which
edited runtime copies the cook overwrites.

## 14. Decoration models are engine content (2026-10-15, user decision)

Decoration models of every world (`mm6_deco_*`, `mm7_deco_*`, `mm8_deco_*`) are sources in
`assets_source/engine/models/`, so any world, including future ones, can bind them. Each world's
`decorations.yml`/`indoor_decorations.yml` keeps its bindings and names them as `engine/models/...`.
- **Migration.** The 164 `mm6_deco_*` sources moved there from `assets_source/worlds/mm6/models/`. The cook class is
  `engine/models/mm*_deco_*.glb`, and the desktop cook moved their cooked copies and textures. The Android overlay
  still has them under `worlds/mm6/models/textures/` until the next on-demand Android cook (`tools/cook_android.sh`).
- **Installs.** `tools/install_model.py` refuses a `mm*_deco_*` name without `--engine`. It also serialises installs
  with an exclusive lock on `assets_source/.cook-cache/install.lock`, because several sessions install at once.
- **Bakes.** The MM6 outdoor bakes record their model dependencies by path, so they turned stale with the move and
  need a re-bake.

## 15. MM9 size pass (2026-11-06, user decision)

MM9's cooked creature textures were 1,243 MB against MM6's 382 MB and MM8's 315 MB: each MM9 tier is its own MM9 skin
(a full colour and normal set per tier, not a region mask and ramps), and most humanoids carried a 2048 head colour
map beside the 2048 body.
- **Head colour at 1K.** 56 `assets_source/worlds/mm9/models/<model>.cook.yml` sidecars cap 77 head colour images
  (materials named `*head*`, plus the banshee necks and the Lich King's staff skull, which share their head maps) at
  1024, the 1K head set of `CLAUDE_CREATURE_TEXTURES.md`. The 2048 level of a head map is sampled only when a face
  nearly fills the screen. A new MM9 humanoid with a 2K head map needs the same sidecar entry. A shared texture cooks
  at the larger size of its uses, so the 12 engine corpse, seated and figure decorations that reuse a head map
  (`assets_source/worlds/mm9/models/mm9_deco_*{dead,seated,figure}.cook.yml`) carry the same cap.
- **Kept.** Body colour stays 2048 BC7: a halve-and-restore test of the 143 body maps measured a median of 28 dB
  (heads 30 dB), so the 2K detail is real at close range. Full-size creature normal maps stay (§2.2, 2026-10-21), and
  the x4 surface tier stays exactly 4x native, as in MM6–MM8.
- **x1 BMPs.** The 1,002 native BMPs with an x4 cook moved to `assets_source/worlds/mm9/textures` (95 MB), as §9 has
  it for MM6–MM8. The other 199 (21 MB: skies, animated frame groups, fire, water, invisible and liquid faces) stay in
  `assets_dev/worlds/mm9/textures`, because MM9 faces still load them from the x1 tier; they leave once they have x4
  masters. `tex.py` and the lighting bake read both places.
- **x4/x2 PNG sources (2026-11-07).** MM9's surface tiers have sources in `assets_source` like MM6–MM8:
  `worlds/mm9/textures_x4/<stem>.png` (the 1,002 accepted masters, hard-linked, and the 23 `*opq` opaque variants)
  and `textures_x2/<stem>.png` (their Lanczos halves). `mm9` is in `cook_surface_textures.py`'s default worlds, so
  the build cooks the 1,025 x4 files into `assets_dev` (byte-identical to the review roots' cook).
- **Cooked only (2026-11-09, user decision: "let it use only the baked textures").** `assets_dev/worlds/mm9` holds no
  surface BMP or PNG. The 222 remaining x1 BMPs moved to `assets_source/worlds/mm9/textures`: 28 are liquids (never
  cooked; the bake reads them there), 44 have an x4 master (opaque variants, the Thjorad Mine frames), and 150 are
  faces without one (fire, slime, sky backdrops, invisible helpers, banners, ...). Those cook at their native size into
  the x1 folder (`cook_surface_textures.py` `NATIVE_WORLDS`): BC7 `assets_dev/worlds/mm9/textures/<stem>.oytex`
  (6 MB) and ASTC `assets_cooked/android/worlds/mm9/textures` (5.5 MB). The runtime takes the x1 tier from the folder,
  so the faces keep their size; a texture that later gets an x4 master loses its x1 cook as an orphan. The Android
  cook of the 1,047 x2 sources ran (130 MB, git-ignored like `assets_dev/worlds/mm9`), and the 1,025 x2 PNGs left
  `assets_dev` (identical to their sources; copy in `output/mm9_precook_backup_20261109/`). The Android packager
  takes the x1 files from the overlay too. `opaque_textures.py` and `liquids.py` (mm9r_common) write their bitmaps
  into `assets_source` as well as the review roots, and promotions copy no raw texture into `assets_dev`. Checked:
  captures of five maps match the BMP versions (Hall of the Gods' sky backdrop draws from the x1 cook and is black
  without it), `--verify` of both profiles, `stale_bakes.py` unchanged.
- **Android models (2026-11-09).** `cook_models.py --profile android --only 'worlds/mm9/**'`: 943 models (creatures,
  attachments, decorations, ground items), 3,646 textures, 2 h 40 min (etc2comp, about 23 textures a minute):
  669 MB in `worlds/mm9/models/textures`, 26 MB in `worlds/mm9/world_items/models/textures`. `--verify` reports no
  MM9 problem.
