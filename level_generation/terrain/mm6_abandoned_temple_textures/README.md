# MM6 Abandoned Temple — complete static texture study, 2026-10-08

**Latest: material correction complete, 2026-10-08.** All 62 static materials were reviewed for brightness and
surface finish. **41 exports are corrected and 21 existing native 4× exports retained.**
[Open the corrected comparison](review/material_correction_x4/index.html): switch the baseline between current
ESRGAN 2× and the earlier complete 4× pack, with normal/Torch Light, 21 matching camera poses, wipe and 1:1 crops.
The 42 corrected screenshots are fresh captures; the 42 ESRGAN baselines are the frozen validated set.
[Corrected manifest](corrected_x4_manifest.json), [validation](review/material_correction_x4/demo_validation.json)
and [brightness measurements](review/material_correction_x4/brightness_audit.json) record the exact sources,
crops, shared-base assemblies, native pixel budgets, decisions and capture hashes.
[Download the complete corrected 62-texture review pack](review/material_correction_x4/mm6_abandoned_temple_corrected_x4_review.zip).

Masonry and rubble crevices are dark again. Chest wood has a subdued grey-brown palette; stone, paving and wood
have calmer matte detail. The dark `d2flor5` paving is distinct from `d2flor4`, and `bemsv32a/c` use their warmer
native timber family. Related wall pillars/relief and stained checker floor are rebuilt over the same corrected
bases. Thin stone trim retains the accepted matte body and uses a separately generated, registered centre-wrap
repair. Seven intermediate returns were rejected or refined for tonal drift, swollen grain, etched surface detail
or a broken repeat join; raw images and exact prompts remain preserved. No colour grading, blur or sharpening
was used to disguise enlarged artwork. The 62 static exports use no ESRGAN carriers.

| Matching screen patch | ESRGAN | Earlier 4× | Corrected 4× | Corrected / ESRGAN |
| --- | ---: | ---: | ---: | ---: |
| Masonry vault, normal | 14.46 | 33.66 | 14.99 | 1.036× |
| Masonry vault, Torch Light | 29.78 | 68.04 | 30.71 | 1.031× |
| Rubble floor, normal | 9.30 | 17.53 | 8.84 | 0.950× |
| Rubble floor, Torch Light | 44.79 | 81.73 | 43.06 | 0.961× |

These are stored RGB display-luma measurements in unchanged rectangles, not physical light multipliers.
The artwork was also inspected independently of its mean. Both 21-location tours use the same frozen binary,
map and per-lighting save/settings. Original map UVs, baked illumination and grading remain authoritative.

```sh
./level_generation/terrain/mm6_abandoned_temple_textures/play.sh corrected_x4 torch
```

The default `play.sh` now opens this corrected stage. Use `corrected_x4 normal` for ordinary lighting.
Exports: [runtime_corrected_x4/](runtime_corrected_x4/) and [same-art 2× reductions](runtime_corrected_demo_x2/).
Reproduce with `export_corrected_x4.py`, then `build_demo_review.py --corrected` after its capture tours.
The stage is `output/temple-textures-stage-20261008/corrected_x4/assets_dev`; the 62 exports are independent copies.
Other mounted files are read-only hard links. The sky and original `orwtrtyl` water are comparison context only,
carried in tier-sized containers to preserve their native logical scale, not newly generated 4× artwork.
The older complete-stage captures had omitted this water carrier and show black water; that historical difference
is not a lighting or shader change. The download contains only the 62 restored surfaces plus manifest/README.

**No renderer, normal-map, roughness-map, engine or production/release asset changes were made for this correction.**
Other maps sharing these names and GPU compression/performance have not been checked. The carpet's previously
recorded mirrored ornament-band construction remains unchanged. This pack is an isolated visual review result.

## Earlier complete 4× pack (before material correction)


**Latest: the complete 62-texture native 4× pack is prepared.**
[Open the full ESRGAN/4× comparison](review/full_x4/index.html): 21 matching camera positions, normal lighting
and Torch Light, 84 fresh native captures, a wipe slider, 1:1 details and all 62 texture/source/repetition proofs.
Masonry vault, Celtic stairs, stone hall floor and the large timber door now contain fresh artwork.
[Full 4× manifest](full_x4_manifest.json) records every source, crop, assembly and hash;
[capture validation](review/full_x4/demo_validation.json) checks matching fixtures/settings and the actual tiers.
[Download all 62 PNGs and the manifest](review/full_x4/mm6_abandoned_temple_x4_review.zip).

**Open visual issue: brightness, 2026-10-08.** The new artwork makes the sampled masonry-vault wall about
2.3× and rubble-floor patch about 1.8–1.9× brighter than the current ESRGAN captures, under matched lighting.
This was not an intended lighting change. [Brightness audit and normal-map feasibility](review/full_x4/brightness_audit.json)
records all 62 source measurements, exact screen rectangles and checks. Coverage is complete; tonal calibration
and crevice contrast still need correction before visual acceptance. Ordinary BLV/BModel materials currently
have no normal-map support; see the [playbook investigation](../TEXTURE_RESTORATION_PLAYBOOK.md#9-brightness-and-material-relief).

All static outputs are exactly four times their native width and height, with unchanged logical map scale.
No static ESRGAN carriers remain. The exporter refuses insufficient source pixels on either axis. Long wood
strips use a fresh continuous body in both orientations; the ten chest pieces reuse connected source masters.
The tall plaster repeats native-detail material, and the large stained floor repeats the exact new checkerboard
under a separate real-alpha stained-light layer. Pillar/grate/relief variants share their wall material exactly.
The wide carpet uses registered new halves, a separately redrawn centre and shared horizontal ornament bands;
those bands mirror one side, so native asymmetric wear is not reproduced exactly. Wrap repairs for paving,
pale stone and irregular masonry use new imagegen artwork from offset guides, never blur or artificial sharpening.

```sh
./level_generation/terrain/mm6_abandoned_temple_textures/play.sh full_x4 torch
```

Use `full_x4 normal` for ordinary lighting. Reproduce exports with `export_full_x4.py`, and assemble/validate fresh
captures with `build_demo_review.py --full`. Tours are `tours/full_x4_*.yml`;
PNG exports are in [runtime_full_x4/](runtime_full_x4/), with same-art 2× reductions in
[runtime_full_demo_x2/](runtime_full_demo_x2/). The new raw returns and exact prompts are in
[generated/full_x4/](generated/full_x4/) and [prompts/full_x4/](prompts/full_x4/).

Production assets, map geometry and release bundles are unchanged. Renderer-owned animated water, the sky and
invisible portal surfaces are outside this static-texture set. Original UV phase and baked lighting still apply.
These are art comparisons; GPU compression/performance and other maps sharing these names have not been tested.

## Previous partial 4× demo and 2× study

The following records describe earlier stages; use the full gallery above for current coverage.

**4× demos are now playable:** [ESRGAN versus fresh 4× gallery](review/x4/index.html) contains 12 candidate textures,
12 matching native camera locations, normal/Torch Light and **48 captures**. It opens side by side, with an optional
wipe slider, full-resolution comparison PNGs and unscaled screen-detail crops. Start with the tapestry, near window,
carpet and timber views. [Demo manifest](demo_x4_manifest.json) records the exact sources, crops and construction;
[demo validation](review/x4/demo_validation.json) checks the active tiers, saves/settings, output sizes and hashes.

The new plaster, shared dado, tapestry and painted glass follow the playbook. `wywt` and `stabig2` use the exact same
`wywl` base; `wywl2` is its lower section, and `wltil2` uses the same plaster. Both exposed composite backgrounds are
pixel-identical to the base outside their native artwork bounds. Separate retained overlays have alpha 0 outside
the artwork and 255 inside their originally opaque rectangular panels; dark painted glass remains opaque.
Raw returns and their alpha are preserved. The tightly framed selected window return fills its canvas and has
partially transparent edge coverage rather than a padded zero-alpha border; placement supplies the transparent
surround in the saved authoring layer. Its complete 1083×1452 source reduces to the 1024×1372 native foreground.
The padded follow-up was rejected for insufficient usable crop size.

The demo also includes the wood body in both orientations, two stone trims, the star floor and newly restored
checkerboard. The carpet is a symmetric candidate made from the cleaner redrawn half and its mirror; it retains
the native dimensions but reinterprets ornament and does not reproduce asymmetrical native wear. These are visual
candidates for review, not a claim that the whole 62-texture pack has been accepted.

Other static surfaces retain ESRGAN artwork. For this isolated mount only, 50 unchanged static texture PNGs have
their pixels duplicated into 4× containers so the existing uniform texture tier preserves their native logical
size. Those carriers are **not new 4× artwork**. This workaround is documented in the manifest and is not installed
in production. Existing face U/V phase and baked lighting differences remain visible. The stage uses PNG uploads;
the captures are not a compressed-texture performance benchmark.

```sh
./level_generation/terrain/mm6_abandoned_temple_textures/play.sh x4 torch
```

This opens the focused 4× stage at the tapestry. Use `x4 normal` for ordinary lighting. To reproduce the art export
and review assemblies, run `export_demo_x4.py` and `build_demo_review.py` from this directory with Python; captures
are defined in `tours/demo_*.yml`. Their launch receipts and original sources remain in the study.

**Earlier quality review:** the larger-section 4× trial was rejected for coarse, pixel-like stippling, especially on plaster,
carpet and tapestry. Several earlier material crops have the same issue. The 62-texture coverage and old validation
records establish export/capture coverage, not current visual approval or production acceptance. The frozen 2×
stage remains available for comparison; its selected masters are not automatically approved for 4×.

Follow the [2×/4× static texture playbook](../TEXTURE_RESTORATION_PLAYBOOK.md) for the revised workflow: shared base
materials, separate true-alpha decoration overlays, fresh continuous detail and independent quality/placement/seam
checks. [Rejected trial status](review/x4/candidate_status.json),
[cleaner sample status](review/x4/clean_sample_status.json) and the
[1:1 comparison](review/x4/quality_comparison.png) retain the evidence. The initial cleaner samples were style trials;
the focused native demos validate the revised composition/export path. The complete 4× preparation is documented
at the top of this page; these earlier exports remain preserved as comparison history.

[Open the before/after comparison](review/index.html). It covers **all 62 static textures** in `6d02.blv`,
17 fixed camera locations, normal lighting and actual Torch Light. Use the texture selector for the native,
current and candidate 3×3 proofs, and expand the generated master to inspect it at original pixel size.

The six-texture pilot is now expanded to the complete static set: rock, rubble, paving, masonry, plaster, timber,
trim, all ten chest pieces, door paintings, reliefs, carpet, glass and mural. Renderer-owned `orwtrtyl` water and
`sky_nit2` sky are excluded, as are the 61 invisible `pending` portal faces. [Full manifest](full_manifest.json) records every name, face count, dimensions,
shared-map usage, selected raw result, prompt and export hash.

Generated with the **built-in imagegen tool**, using native MM6 bitmaps for layout and approved generated family
references for material matching. [Exact prompts](prompts/), [unaltered returned masters](generated/),
[native/current references](references/) and [runtime exports](runtime/) are retained. Original references come
from `reference/mmerge_data_forus/Data/mm6.bitmaps.lod/`.

This is an isolated, launchable stage. Production `assets_dev` textures, BLV data and release ZIPs are unchanged.
The previous six-texture captures and validation record remain as pilot history; the current complete-set record
is [full validation](review/full_validation.json).

## Detail and alpha acceptance

The quality gate is fresh high-definition material, not enlarged pixel art. Inspect selected masters at 1:1 for
blocky grain, dither, stair-step edges and crunchy invented detail. Chest pieces and narrow beams received further
edits when they failed this check; rejected iterations remain preserved, but are not selected in the manifest.
[Full-size crop boards](review/full_hd_crops_1.png) and the
[alpha/master extraction crops](review/full_alpha_hd_crops.png) accompany the unscaled master viewer.

All **14 padded narrow textures** were requested with `transparent_background: true` and explicit real PNG alpha.
Selected raw PNGs have transparent padding, rather than painted magenta or a checkerboard. Alpha counts and crop
rectangles are recorded in the manifest. Generated interiors can have alpha 251–254; the exporter crops the
rectangular material footprint (retaining dark keyhole colour), converts it to an opaque RGBA texture and reduces
it to the original X2 size. The connected masters are cut at registered fractional regions; source alpha in dark
details remains in the raw masters and becomes opaque in the colour-plane exports. No transparent padding enters
the wall/floor exports. Their alpha is 255 throughout, as required by these originally
opaque surfaces. This does not introduce cutouts into walls or remove painted stained-glass backgrounds.

Deterministic processing is limited to alpha-based rectangular extraction, format conversion, Lanczos reduction
and review assembly. No procedural repainting, edge blending, sharpening, colour grading, normal maps or renderer changes.
Run `python3 level_generation/terrain/mm6_abandoned_temple_textures/export_review.py` to reproduce exports/proofs;
it includes horizontal/vertical alpha-extraction self-checks and asserts dimensions and opacity for every export.

## Connected pieces and repeating strips

Following the requested `<====>` approach, the chest front, back and lid are generated as **three connected masters**,
then cut into the nine existing cap/body texture names. Shared boards, iron bands and colour cross the extraction
cuts within one image. The chest side retains its accepted independent master. Compare the assembled
[front](review/chest_front_assembled_proof.png), [back](review/chest_back_assembled_proof.png) and
[lid](review/chest_lid_assembled_proof.png) at the actual runtime dimensions, enlarged three times for inspection.
[Family edge diagnostics](review/full_family_join_metrics.json) supplement these visual checks.

Repeating wood and the two stone trims use extended masters with **three registered body periods and separate
outer end regions**. The centre body is cut for `beamplnh`, `gset06` and `gset05`; `beamplnv` uses a 90-degree rotation
of the same wood body. The original map consumes these repeating bodies; the outer end regions remain review
material. The explicit extraction regions and rotation are recorded in the full manifest.

Generating a larger material and cutting it improves shared joins, but an arbitrary crop does not guarantee a
seamless repeat. The middle must have matching boundary phase; inspect the repeated
[wood](review/beamplnh_extended_core_repeat.png), [stone border](review/gset06_extended_core_repeat.png) and
[thin stone courses](review/gset05_extended_core_repeat.png). Caps are kept outside the repeated body. For large
wall/floor fields, both texture axes require wrap continuity. This same-master approach is the default for future
connected trim/end/corner families, while existing UVs and texture dimensions stay authoritative.

## Continuity and mapping

Original face U/V values and offsets are retained. `IndoorRenderer.cpp` normalizes them by logical texture size;
`MapAssetLoader.cpp` divides X2 physical dimensions by two. Every PNG keeps its original X2 dimensions and aspect,
so the replacement does not change its world scale. Existing mipmaps and anisotropic filtering remain active.

The review separates a tile's own repetition, shared geometry-edge UV phase, and neighbouring material families.
[All tile metrics](review/full_seam_metrics.json) are diagnostic only: low edge differences do not establish
correct alignment. Finite doors, murals and chest pieces retain their registered borders; they are not forced to
repeat as wallpaper. Wood strips follow their long-axis repeat contract. Inspect matching stone courses and the
left/right relief surrounds, chest iron/wood joins, doorframes, plaster bands and floor motifs in the captures.

[Full native UV audit](review/full_native_uv_audit.json) recomputes face normals from nondegenerate vertex triangles
and checks same-texture coplanar shared edges, including original face offsets, modulo native dimensions with a
one-texel tolerance. It reports 983 aligned edges and 337 phase flags. These are original authored offsets or
projection changes, not 337 confirmed renderer defects. Its normal calculation differs from the earlier pilot
measurement; compare this full audit within its own stated method. No BLV or UV corrections are included.

## Fixed game checks

Each of four passes captures 17 matching poses at 1600×900: **68 screenshots**, with the same copied executable,
party fixture, rendering settings and camera tours. The renderer is OpenGL 3.3 on NVIDIA hardware. Torch Light is
the actual Master party buff, power 3, using a private round-trip-checked save. The tour holds gameplay simulation
while posing the camera. Animation frames and HUD clocks can vary slightly between passes.

Positions are party-foot coordinates; yaw/pitch are radians. Full tours are in [tours/](tours/).

| Check | Position | Yaw | Pitch | Inspect |
| --- | --- | --- | --- | --- |
| cave-near | `[-24644, -10305, -2200]` | 2.600000 | 0.100 | Rock continuity across slopes and the rubble junction |
| rubble-floor | `[-17100, -9839, -1681]` | 2.300000 | -0.500 | Pebble scale, floor triangle joins and distant repetition |
| masonry-stairs | `[16384, -15136, 225]` | 1.570796 | 0.080 | Large masonry courses, corners and neighbouring floor |
| masonry-vault | `[7808, 9972, -1879]` | 1.570796 | 0.150 | Thin courses, ledges and door surrounds |
| mosaic-ceiling | `[16384, -15603, 225]` | 1.570796 | 0.550 | Motif continuation across the vault and trim |
| sandstone-sanctum | `[16336, -18208, 753]` | 0.000000 | 0.150 | Plaster/sandstone, tile bands and artwork boundaries |
| timber-entrance | `[-29230, -10240, -2200]` | 3.141593 | 0.000 | Beam grain, planks and doorway transitions |
| chest-corners | `[-30200, -10200, -2218]` | 3.260000 | -0.360 | Chest front/side/lid material and registered iron borders |
| monk-relief | `[7808, 9230, -1880]` | 1.570796 | -0.080 | Relief and matching left/right masonry borders |
| painted-door | `[15040, -15616, 224]` | 3.141593 | -0.100 | Painted artwork, door edges and adjacent plaster |
| gold-door | `[16690, -16000, 224]` | 0.000000 | 0.120 | Gilding and door-frame continuity |
| chapel-mural | `[16400, -18592, 752]` | 3.141593 | 0.400 | Mural figures, architecture and surround |
| chapel-floor | `[16400, -18592, 752]` | 3.900000 | -0.700 | Checkerboard and decorated floor joins |
| stained-windows | `[16400, -18208, 752]` | 3.141593 | 0.220 | Glass painting, lead lines and stone/plaster surround |
| celtic-stairs | `[16384, -19080, 752]` | -1.570796 | -0.180 | Patterned floor, risers and plaster/wood junctions |
| timber-stairs | `[16384, -17090, 560]` | 1.570796 | 0.180 | Vault motif and plaster/timber transitions |
| stone-hall-floor | `[3360, 8290, -896]` | 1.570796 | -0.450 | Paving scale and triangle joins below masonry |

## Modern dungeon texturing

Repeating materials and UV-based mapping remain valid approaches. Modern material systems commonly separate
base colour, roughness and normal detail so lighting can react to the surface rather than baking directional
highlights into the colour image. See Epic's [physically based material guidance](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)
and [material inputs](https://dev.epicgames.com/documentation/en-us/unreal-engine/material-inputs-in-unreal-engine).

Our ordinary indoor shader currently samples the colour texture and multiplies it by lighting; it does not sample
material normal or roughness textures. Imagegen can improve appearance within that system, but colour-only
replacement cannot make a torch move correctly over small bumps. Avoid strong painted directional shadows.

Epic documents [detail textures and world-aligned projection](https://dev.epicgames.com/documentation/en-us/unreal-engine/texturing-material-functions-in-unreal-engine)
as ways to add close-range detail or give materials a consistent world scale. World-aligned projection is a plausible
separate study for natural cave rock; a blanket conversion would disturb authored doors, trims and mosaic placement,
and world-space projection can swim on moving doors. My recommendation is to retain authored mapping for this study,
evaluate its art, then consider explicit UV corrections and a small material-normal/detail trial if the lighting
benefit justifies the renderer work.

## Cost of 4× textures and GPU compression

Here, 4× means four times the native width and height, so twice the current X2 dimensions and **four times its
texel count**. The 62 static textures contain 9,199,616 texels at X2 and 36,798,464 at X4. The largest grows from
1024×1024 to 2048×2048. These totals exclude water, sky, actors, UI, geometry, render targets and driver overhead.

| Resolution / actual GPU format | Texture data including all mips | Relative to current X2 PNG upload |
| --- | ---: | ---: |
| X2 PNG → BGRA8/RGBA8, current path | 46.79 MiB | 1× |
| X2 BC7 or ASTC 4×4 | 11.70 MiB | 0.25× |
| X4 PNG → BGRA8/RGBA8 | 187.17 MiB | 4× |
| X4 BC7 or ASTC 4×4 | **46.79 MiB** | **approximately 1×** |
| X4 BC1 | 23.40 MiB | 0.50× |

BC7 and BC3 store 16 bytes per 4×4 block; BC1 stores eight, per
[Microsoft's block-format table](https://learn.microsoft.com/en-us/windows/win32/direct3d11/texture-block-compression-in-direct3d-11).
ASTC 4×4 has the same 16-byte block footprint, per the
[Khronos specification](https://registry.khronos.org/webgl/extensions/WEBGL_compressed_texture_astc/).
The calculation rounds every mip to whole compressed blocks rather than simply multiplying by 4/3.
BC7 is the desktop quality candidate; ASTC 4×4 is the corresponding mobile candidate where supported. BC1 and
BC3 have the stated footprints but would need stricter visual review for these detailed paintings and materials.
Resolution alone does not guarantee better artwork; a genuine X4 source is necessary.
The current registered source crops have enough pixels for X4 exports for 53 of 62 textures. Nine need larger
masters/crops: `beamplnv`, `beamplnh`, `gset06`, `gset05`, `wywl`, `stabig2`, `stain512`, `carpt01` and `wywt`.
This is a dimension check, not acceptance of their appearance at X4; no enlarged X2 files are proposed.

PNG compresses files on disk, then the current loader expands them to four bytes per texel and builds mipmaps
on the CPU. One decoded base-level copy grows from **35.09 MiB to 140.38 MiB**; that is not a whole-process RAM
estimate, since caches, copied texture sets and temporary mip/upload buffers also contribute. Direct upload of
offline-compressed mip chains could avoid those expanded wall-texture copies and runtime PNG decoding/mip work.
Renaming PNGs to DDS/KTX would not achieve this: the indoor upload path needs explicit compressed-texture support.
Current candidate X2 PNG files total 21.83 MiB on disk; BC7's fixed GPU payload and final ZIP/KTX download size are
different quantities. No X4 PNG or shipping-container size is inferred from the X2 PNG size.

**An FPS percentage cannot be calculated from image dimensions or VRAM bytes.** Meshes, draw calls, output
pixels and shader samples stay the same. Mipmaps usually select the added lower level at the same distant view,
while close-up detail can increase texture working sets/cache misses. Compression reduces storage and fetched
block bytes relative to X4 uncompressed data, but equal total residency does not guarantee equal per-frame
bandwidth or speed. CPU-bound views might show little change; texture-limited views need measurement.

For an illustrative frame-time model, if texture work accounted for 10% of the old frame and its cost rose by
50%, total frame time would rise 5%, meaning 4.76% lower FPS. If that part doubled, FPS would fall 9.09%; if it
quadrupled, 23.08%. These are conditional examples, **not predictions for OpenYAMM**. The formula is
`FPS_new/FPS_old = 1 / (1 + f * (r - 1))`, where `f` is the affected share of frame time and `r` its cost ratio.
The screenshot tours mix views, capture work and warmup; their FPS logs are not a controlled format benchmark.

[Exact calculated bytes and assumptions](review/full_texture_cost.json) are reproducible with
`python3 level_generation/terrain/mm6_abandoned_temple_textures/calculate_texture_cost.py`, including assertions
for small-mip block rounding. A useful benchmark needs real X4 art, compressed direct upload, identical fixed
camera/settings, GPU frame timings after warmup and CPU RAM/VRAM observations on desktop and Android. No engine
or runtime compression migration is included in this texture study.

## Play and repeat

From the repository root:

```sh
./level_generation/terrain/mm6_abandoned_temple_textures/play.sh after torch
```

Use `before torch` for the current upscales, or `before normal` / `after normal` for ordinary lighting.
The launcher starts at the cave check; `tp X Y Z` in the debug console moves to another location.
Automatic capture commands and file hashes are retained in [full validation](review/full_validation.json).
Close the interactive game before running captures.

The stage is `output/temple-textures-stage-20261008/`. Its MM6 `textures_x2` files are independent copies; other
mounted files are read-only hard links and must not be edited there. [Stage receipt](stage.json) records hashes.
The candidate files and review package stay in this study directory until a separate production rollout.

Limits: other maps sharing these texture names have not been visually checked. Existing UV-phase/projection joins
can remain visible despite improved artwork; 17 cameras sample the dungeon rather than proving every face join.
The shader still uses colour textures without material normals or roughness.
