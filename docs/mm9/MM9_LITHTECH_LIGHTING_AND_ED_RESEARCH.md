# MM9 LithTech Lighting And ED Research

This document records current local findings about Might and Magic IX LithTech lighting, shadows, compiled light data,
and the `.ed` files found beside some world DATs. Treat this as research guidance for future lossless MM9 DAT runtime
integration. The byte-level DAT layout authority remains `MM9_DAT_FORMAT_NOTES.md`.

## Summary

MM9 lighting is not defined in one place. It is split across authored editor data, runtime object data, world metadata,
BSP surface/poly metadata, and compiled render data.

- `.ed` files are authored LithTech/DEdit editor source files, not runtime map files.
- `.dat` files are compiled runtime worlds and remain the runtime source of truth for OpenYAMM.
- Light objects and light properties are authored in `.ed` and compiled into the DAT object section.
- Ambient/default lighting settings are stored in the DAT `WorldInfo.property_string`.
- Per-surface and per-poly lighting participation is stored in BSP surface flags and MM9 poly lightmap fields.
- Baked lightmaps, light groups, and shadow-map-like products are expected in the DAT render data region.
- MM9 DAT v66 does not expose the later LithTech `lightgrid_pos` header field, so any v66 light grid or equivalent
  data must be discovered from `render_data_pos`, object data, or older packed layout rules.

OpenYAMM currently preserves several lighting-related source fields, but it does not yet decode and render the original
MM9 baked lighting products.

## Source Files Checked

Primary OpenYAMM/MM9 documents:

- `docs/mm9/MM9_DAT_FORMAT_NOTES.md`
- `docs/mm9/MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md`
- `tools/mm9_import_discovery/`
- `game/mm9/Mm9DatWorld.cpp`

Primary local LithTech references:

- `mm9/lithtech/runtime/world/src/world_shared_bsp.cpp`
- `mm9/lithtech/runtime/world/src/light_table.cpp`
- `mm9/lithtech/runtime/world/src/de_world.h`
- `mm9/lithtech/runtime/client/src/world_client_bsp.cpp`
- `mm9/lithtech/runtime/shared/src/parse_world_info.cpp`
- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_rendershader_dynamiclight.cpp`
- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_rendershader_lightmap.cpp`
- `mm9/lithtech/runtime/render_a/src/sys/d3d/setupmodel.cpp`
- `mm9/lithtech/runtime/render_a/src/sys/d3d/setuptouchinglights.cpp`
- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_drawsky.cpp`
- `mm9/lithtech/tools/PreProcessor/Packer_PC/PCWorldPacker.cpp`
- `mm9/lithtech/tools/PreProcessor/Processing.cpp`
- `mm9/lithtech/tools/PreProcessor/LightMapMaker.cpp`
- `mm9/lithtech/tools/shared/world/EditRegion.cpp`
- `mm9/lithtech/tools/DEdit/Lightmap/`
- `mm9/lithtech/tools/DEdit/res/CLASSHLP.BUT`
- `mm9/lithtech/sdk/inc/ltengineobjects.cpp`

Useful MM9 source examples:

- `mm9/extracted/WORLDS/WORLDS/*.dat`
- `mm9/extracted/WORLDS/WORLDS/*.ed`
- `mm9/mm9_tools/PreFabs/**/*.ed`
- `assets_dev/worlds/mm9/maps/*.dat_world.yml`
- `assets_dev/worlds/mm9/maps/*.raw_objects.yml`

## DAT Lighting Storage

The observed MM9 DAT v66 top-level layout is:

```text
uint32 version                  // 66
uint32 object_data_pos
uint32 render_data_pos
uint32 dummy[8]
WorldInfo
WorldTree
WorldModelHeader
WorldModel[]
ObjectData at object_data_pos
```

`WorldInfo` includes:

```text
uint32 property_string_length
char[property_string_length] property_string
float light_map_grid_size
vec3 extents_min
vec3 extents_max
```

Observed world info strings contain lighting settings such as:

```text
PBlockSize 8096 ; LMGridSize 64; MaxLMSize 64 ; AmbientLight 60 60 60
```

The important fields are:

- `AmbientLight`: world ambient RGB used by LithTech runtime/editor code.
- `LMGridSize`: world default lightmap grid scale.
- `MaxLMSize`: likely maximum lightmap page/block dimension used by preprocessing/render data.
- `PBlockSize`: preprocessing/render packing block size, not directly lighting but part of the same world info string.

The current OpenYAMM sidecar already preserves `property_string` and `light_map_grid_size`. Do not replace this with
only parsed fields. Parsed fields should be convenience projections over the original string.

## Object Light Data

LithTech runtime code scans DAT object data for light-like objects. The later local LithTech source explicitly handles:

- `Light`
- `DirLight`
- `ObjectLight`

MM9 generated `*.raw_objects.yml` sidecars also contain object records named `Light`, `DirLight`, and `ObjectLight`,
with source properties such as:

- `Pos`
- `Rotation`
- `LightRadius`
- `LightColor`
- `InnerColor`
- `BrightScale`
- `ObjectBrightScale`
- `AttCoefs`
- `AttExps`
- `Attenuation`
- `LightObjects`
- `FastLightObjects`
- `CastShadows`
- `ClipLight`
- `ConvertToAmbient`
- `FOV`
- `LightGroup`

Local LithTech class definitions and runtime loaders establish the following property types and defaults:

- `LightObjects` is a boolean and defaults to true for `Light` and `DirLight`.
- `FastLightObjects` is a boolean and defaults to true for `Light`, `DirLight`, and `ObjectLight`.
- `CastShadows` is a boolean and defaults to true.
- `ConvertToAmbient` is a real value and defaults to `0.0`, not a boolean.
- `BrightScale` and `ObjectBrightScale` are real values and default to `1.0`.
- `AttCoefs` and `AttExps` are 3-component vectors with defaults roughly `(1, 0, 19)` and `(0, 0, -2)`.
- `Attenuation` is a string enum with values `D3D`, `Linear`, and `Quartic`; `Quartic` is the authored default.
- `FOV` is authored in degrees, while runtime `StaticLight::m_FOV` stores `cos(FOV * pi / 360)`.
- `LightGroup` is a string in the authored object data and is hashed to a light-group id at runtime.
- `DirLight` declares `InnerColor` instead of `LightColor`; the runtime static-light scan accepts either
  `LightColor` or `InnerColor` as the effective static-light color.
- `Light` also declares `Size`, `AttType`, and `CastShadowMesh`; these are relevant to tooling/preprocessing even if
  the runtime static-light scan ignores some of them.

The later LithTech runtime distinguishes at least two object-lighting paths:

- `FastLightObjects` contributes to preprocessing/light-grid/lightmap-style products.
- `LightObjects` without `FastLightObjects` creates static runtime lights for object/model lighting.

The runtime static-light path is intentionally narrow. It only creates a `StaticLight` when the effective
`LightObjects` value is true and the effective `FastLightObjects` value is false. Before insertion, it multiplies the
color by `BrightScale * ObjectBrightScale`, folds attenuation coefficients by `pow(radius, AttExps)`, stores
`ConvertToAmbient`, `CastShadows`, direction/FOV, and light-group id, then inserts the result into the world tree.
`ObjectLight` participates in object lighting but is excluded from world lightmap generation by the preprocessor.

One runtime implementation detail should not be copied blindly: the later `world_shared_bsp.cpp` parser keeps a
function-local `do_fast_light_objects` value and comments that missing `FastLightObjects` properties reuse the previous
light object's value. The same comment says it is unknown whether this is proper behavior. OpenYAMM should prefer the
authored class defaults unless local MM9 DAT evidence proves the sticky parser behavior is required.

For OpenYAMM, generated light sidecars should preserve both the typed interpretation and the raw object/property record.
The typed projection must not become the only copy of source light data.

## Surface And Polygon Lighting Metadata

MM9 DAT surfaces include:

```text
vec3 uv_origin
vec3 uv_u
vec3 uv_v
uint16 texture_index
uint32 unknown
uint32 flags
uint32 unknown2
uint8 use_effects
optional effect strings
uint16 texture_flags
```

Lighting-related LithTech surface flags seen in local references include:

- `SURF_BRIGHT`
- `SURF_LIGHTMAP`
- `SURF_DIRECTIONALLIGHT`
- `SURF_GOURAUDSHADE`
- `SURF_RECEIVELIGHT`
- `SURF_RECEIVESHADOWS`
- `SURF_RECEIVESUNLIGHT`
- `SURF_SHADOWMESH`
- `SURF_CASTSHADOWMESH`
- `SURF_CLIPLIGHT`

Use exact bit definitions only after confirming which `de_world.h` branch matches MM9 DAT v66. The local LithTech tree
contains later-version references, so semantic names are useful but byte layout must remain locally verified.

MM9 poly records parsed by `game/mm9/Mm9DatWorld.cpp` include fields that are likely connected to compiled lightmap
storage:

```text
center
lightmap_width
lightmap_height
unknown_flag
unknown_list[unknown_flag * 2]
surface_index
plane_index
vertices: point_index + 3 raw dummy bytes
```

OpenYAMM must preserve `lightmap_width`, `lightmap_height`, `unknown_flag`, `unknown_list`, and the per-vertex dummy
bytes even before their meaning is fully decoded. These are part of the lossless lighting/render data surface.

## Render Data And Light Grid

Later LithTech source has a richer world header than MM9 DAT v66:

```text
version
object_data_pos
blind_object_data_pos
lightgrid_pos
collision_data_pos
particle_blocker_data_pos
render_data_pos
...
```

That later layout is not MM9's observed DAT v66 layout. It is useful for semantics only.

The later runtime load flow is:

1. Parse world info string for ambient light.
2. Scan object data and add static lights.
3. Insert static lights into the world tree.
4. Seek to `lightgrid_pos` and load `CLightTable`.
5. Seek to `render_data_pos` and load render data.

`CLightTable` stores:

- world base position
- grid/block size
- grid dimensions
- compressed RGB sample data

The packer writes light grid data as RLE-compressed RGB samples. The renderer can trilinearly sample the table for
object/model lighting.

For MM9 DAT v66, there is no explicit `lightgrid_pos`. Therefore:

- Do not assume the later header layout.
- Do not invent a light grid section until the bytes are verified.
- Treat `render_data_pos` as the likely entry point for compiled render/lightmap/lightgroup data.
- Preserve raw bytes for any undecoded render data section until it can be parsed and validated.

## Runtime Lighting Pipeline

The later LithTech runtime load order is important because it shows which lighting systems are independent services:

1. Parse `AmbientLight` from the `WorldInfo` string into a 0-255 RGB vector.
2. Precalculate BSP/world-model bounding spheres.
3. Scan object data for authored `Light`, `DirLight`, and `ObjectLight` records.
4. Convert non-fast object lights into `StaticLight` records and insert them into the world tree.
5. Load fast object-lighting samples from the light grid, when the world version has a light-grid section.
6. Load renderer-owned world data and any light-group data from the render data section.

`LightObjects` and `FastLightObjects` are not interchangeable:

- `LightObjects=false` means the authored light should not affect object/model lighting.
- `FastLightObjects=true` routes object lighting through precomputed samples in later LithTech.
- `LightObjects=true` and `FastLightObjects=false` creates a runtime `StaticLight` containing position, radius, color,
  direction/FOV, attenuation coefficients, shadow flag, convert-to-ambient amount, and light-group id.

For renderer-neutral OpenYAMM code, this split should be represented as derived metadata before final rendering exists:

- `effectiveLightObjects`
- `effectiveFastLightObjects`
- `effectiveCastShadows`
- `effectiveColor`
- `effectiveObjectLightColor`
- `effectiveAttCoefs`
- `effectiveFovCos`
- `staticObjectLightEligible`
- `fastObjectLightingSource`

OpenYAMM should keep this split. A DAT world runtime should expose ambient light, baked surface lighting, fast object
lighting samples if MM9 v66 contains them, non-fast static object lights, and dynamic runtime FX lights as separate
services.

## Dynamic Runtime Lights

LithTech's dynamic world lighting is a separate render pass, not the main way static MM9 levels are lit. The checked D3D
shader creates two small attenuation textures:

- an XY texture holding roughly `1 - (x^2 + y^2)`
- a Z texture holding `z^2`

It uses generated texture coordinates from camera/world position, subtracts the Z term from the XY term, modulates by
the light color, then additively blends only matching-depth world geometry. The implementation explicitly notes that
angular attenuation is not supported in this pass. It also filters triangles facing away from the light before issuing
dynamic light draw calls.

For OpenYAMM, dynamic lights should be treated as runtime effects layered on top of the DAT baked world lighting. They
should not be used as a substitute for decoding MM9 render lightmaps/shadows.

## Sky Objects

The sky path is object-driven, not just a texture name on a polygon. Authoring classes such as `DemoSkyWorldModel` and
`SkyPointer` define a `SkyDef` volume from `SkyDims` and inner view percentages, mark world models as sky objects, and
register them with a sky index. The renderer draws sky objects through a separate sky view with depth read/write
disabled and sky fog distances applied. Sky objects can be world models, polygrids, or sprites.

For MM9 DAT support, preserve both sky-related surface flags such as `SURF_SKY` and sky object records. `DatWorldView`
should eventually expose sky definitions and sky render objects separately from normal world geometry.

## Performance Model

LithTech's performance model is to bake or precompute almost everything static:

- Lightmaps and shadow products are produced by the preprocessor and packed into render data.
- `LMGridSize` and `MaxLMSize` are parsed from the world info string before lighting and packing.
- Fast object lighting is stored as compressed RGB grid samples in later versions. Runtime lookup converts world
  position to grid coordinates and trilinearly samples eight decompressed RGB samples.
- Light grid compression is RLE over RGB samples, but the runtime keeps the decompressed RGB table in memory for cheap
  per-object sampling.
- Light groups store color/state plus per-grid or per-render-data deltas so lighting can change without relighting the
  whole world.
- Non-fast static object lights are spatially inserted into the world tree once, then queried by model/object bounding
  boxes instead of scanned linearly every frame.
- Model and particle/object lighting query only lights touching a bounding sphere or box, then hand the small resulting
  set to the renderer.
- Dynamic lights are limited to a separate additive pass over affected triangles. The D3D implementation precomputes
  two attenuation textures, uses depth-equal additive blending, and filters back-facing triangles before drawing.
- Lightmap textures are decompressed and uploaded per render section, then updated only when section lightmap data
  changes.

This means the native MM9 path should prioritize decoding and rendering the original baked products before adding broad
real-time lighting approximations. Approximation is acceptable as a temporary visualization fallback, but it must not
become the authoritative lighting model.

## Shadows

Shadows are controlled by several authored and compiled mechanisms:

- Light object properties such as `CastShadows`.
- Brush/surface properties such as `ReceiveShadows`, `ReceiveLight`, `LMGridSize`, and `AmbientLight`.
- Editor lightmap generation options under `mm9/lithtech/tools/DEdit/Lightmap/`.
- Surface flags such as `SURF_RECEIVESHADOWS`, `SURF_SHADOWMESH`, `SURF_CASTSHADOWMESH`, and `SURF_CLIPLIGHT`.
- Compiled render/lightmap/shadow products in DAT render data.

The local packer version history explicitly notes:

- version 46: lightmapping info
- version 57: `LMGridSize`
- version 61: lightmap animations
- version 63: shadow maps
- version 67: 24-bit lightmaps and per-surface lightmap grid sizes
- version 70: light grid array
- version 76: light groups
- version 77: ambient light table to light groups

MM9 DAT v66 sits after shadow maps and before the later 24-bit/per-surface-grid/light-group revisions. That suggests
MM9 may have baked shadow/lightmap data, but not the later v67+ layout. The only acceptable integration path is to
decode the v66 bytes instead of copying assumptions from v85-era code.

## What The ED Files Are

The `.ed` files are legacy LithTech/DEdit editor source files. They are not runtime DATs and they are not the newer
text `.lta` format.

Observed extracted world `.ed` files:

- `1000TERRORS.ed`
- `AFTERWORLD.ed`
- `ANSKRAMKEEP.ed`
- `ARSLEGARDCITY.ed`
- `BATHHOUSE.ed`
- `BEETHOVEN.ed`
- `BOOTCAMP.ed`
- `CHASMOFTHEDEAD.ed`

Only a subset of extracted worlds currently has a matching `.ed`, so `.ed` cannot be treated as complete runtime
authority for all MM9 maps.

Observed properties:

- World `.ed` files contain visible world info strings near the header, including `PBlockSize`, `LMGridSize`,
  `MaxLMSize`, and `AmbientLight`.
- Prefab `.ed` files contain readable binary-embedded object/property data, including lights, model paths, skin paths,
  particle properties, and fire/torch-style object definitions.
- `mm9/mm9_tools/Lith21tools/` contains legacy tools such as `dedit.exe` and `Processor.exe`, which supports `.ed`
  being an older LithTech 2.1 authoring format.

The later checked LithTech editor source can load/save text `.lta`/`.ltc` and binary `.tbw`, and has historical `.ed`
references in UI/resource text. That source branch should not be assumed to parse MM9 `.ed` directly.

OpenYAMM should preserve `.ed` files as original authoring artifacts when present, but DAT remains the runtime source
of truth.

## Runtime Integration Requirements

The lossless MM9 lighting path should be:

1. Keep source DAT bytes and current decoded DAT sidecars authoritative.
2. Preserve `.ed` files as optional authoring-source artifacts, not required runtime assets.
3. Parse `WorldInfo.property_string` into typed convenience fields while preserving the exact source string.
4. Typed-extract light objects from DAT object data into generated YAML, preserving raw object/property records.
5. Preserve BSP surface flags, DTX texture/user flags, poly lightmap dimensions, and all unknown lightmap-adjacent
   fields.
6. Decode `render_data_pos` for MM9 DAT v66 instead of relying on later LithTech v85 layout.
7. Preserve undecoded render data bytes and hashes until every substructure is known.
8. Feed decoded baked lighting into the native MM9 DAT world runtime, not into ODM/BLV-only assumptions.
9. Make the native MM9 DAT runtime/view consume the same lighting data independent of indoor/outdoor compatibility
   artifacts.
10. Expose sky definitions/sky objects from the DAT world path instead of treating sky as ordinary visible geometry.
11. Keep dynamic runtime lights as an overlay service; do not use them to replace baked DAT lighting.

Do not collapse authored lights, static object lights, baked lightmaps, ambient world light, and dynamic FX lights into
one generic point-light list. They are different source domains and need distinct preservation.

## Proposed Generated Assets

The eventual generated asset set should stay under `assets_dev/worlds/mm9/maps/` and should be deterministic:

```text
<map>.dat_world.yml          # existing DAT structural sidecar
<map>.raw_objects.yml        # existing raw DAT object/property sidecar
<map>.lighting.yml           # proposed typed lighting projection
<map>.render_data.yml        # proposed decoded render/lightmap/lightgroup metadata
<map>.render_data.bin        # optional raw undecoded payload preservation if needed
```

`<map>.lighting.yml` should include:

- source DAT path/hash
- source `WorldInfo.property_string`
- parsed ambient light and lightmap defaults
- typed light objects with source object indexes
- all original light property values and raw property payload evidence
- unresolved/unknown light properties
- references to surface/poly/render-data structures when known

`<map>.render_data.yml` should include:

- `render_data_pos`
- render data byte range and hash
- decoded lightmap pages or blocks when known
- decoded shadow map structures when known
- decoded light-grid or equivalent object-lighting samples when known
- light animation/light group structures if MM9 v66 contains them
- raw unknown spans with offsets and hashes

## Test Requirements

Add tests before treating generated lighting data as complete:

- DAT world info parse and roundtrip: parsed fields must reconstruct no source authority; the original string must
  survive byte-for-byte.
- Raw object preservation: every light object/property in DAT object data must appear in both raw and typed outputs.
- Typed projection: `Light`, `DirLight`, and `ObjectLight` properties must decode into stable typed fields without
  dropping unknown properties.
- Render data bounds: `render_data_pos` must point to a bounded section whose raw bytes can be hashed and preserved.
- Lightmap metadata: every parsed poly `lightmap_width`/`lightmap_height` must be preserved and cross-checked against
  decoded render data once the render-data parser exists.
- Surface flag preservation: DAT surface flags and DTX texture/user flags must remain separate fields.
- Idempotency: regenerating MM9 lighting sidecars twice from the same source must produce byte-identical outputs.
- Runtime neutrality: loading MM6-MM8 maps must not require or inspect MM9 lighting sidecars.
- Native MM9 view: opening a native MM9 DAT level should load lighting sidecars through the DAT world path, not through
  ODM/BLV-specific lighting assumptions.

## Current OpenYAMM Gap

OpenYAMM currently has enough parsed data to avoid throwing away known lighting metadata, but not enough to reproduce
original MM9 lighting faithfully. The main missing piece is MM9 DAT v66 render data decoding. Until that exists, native
MM9 rendering can display geometry and source textures, but baked lightmaps/shadows/light-grid-style object lighting
should be considered incomplete.
