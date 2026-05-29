# MM9 LithTech Skybox Rendering Plan

This document records the local findings about Might and Magic IX / LithTech sky rendering and gives a concrete
implementation path for future OpenYAMM DAT-world rendering work.

Use the local files listed here as semantic references. Generate new OpenYAMM code; do not copy renderer code from
reference engines.

## Summary

MM9 sky rendering should be implemented as a DAT-world sky layer, not as a single MM6-MM8-style outdoor sky texture.
LithTech treats sky as authored world/model objects rendered by a special camera through sky portal regions:

- `DemoSkyWorldModel` and `SkyPointer` define sky view volume data.
- Sky objects are regular objects, most importantly world models such as `SkyBox0` and `TOD_Sky0`.
- Surface flag `SURF_SKY` marks sky portal surfaces.
- Compiled render blocks store sky portal polygons used to clip the sky to visible screen extents.
- The renderer draws sky objects in a separate pass with depth read/write disabled and sky fog distances applied.

OpenYAMM already preserves enough MM9 source data for a first implementation:

- `assets_dev/worlds/mm9/maps/*.dat_world.yml` classifies sky world models by role.
- `assets_dev/worlds/mm9/maps/*.raw_objects.yml` preserves `SkyPointer`, `DemoSkyWorldModel`, and `TOD_Sky` object
  properties.
- `game/mm9/Mm9DatWorld.*` preserves DAT world models, surfaces, surface flags, texture names, render-data offset, and
  render-role filters.

The first practical runtime step is to draw active sky world models in a dedicated sky pass over the full viewport,
behind ordinary DAT geometry. Later, decode DAT `render_data_pos` render blocks and their sky portal lists to clip sky
rendering like LithTech.

## Source References

Primary local references:

- `mm9/lithtech/sdk/inc/ltengineobjects.cpp`
  - Brush `Type` includes `SkyPortal`.
  - `DemoSkyWorldModel` and `SkyPointer` define `SkyDims`, `Index`, and `InnerPercentX/Y/Z`.
  - `DemoSkyWorldModel` sets a `SkyDef`, marks itself as a sky object, and adds itself to the sky list.
- `mm9/lithtech/sdk/inc/ltbasetypes.h`
  - Defines `SkyDef` as `m_Min`, `m_Max`, `m_ViewMin`, and `m_ViewMax`.
- `mm9/lithtech/runtime/world/src/de_world.h`
  - Defines `SURF_SKY = (1 << 4)` and `SURF_PANNINGSKY = (1 << 15)`.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/common_draw.cpp`
  - Computes `m_SkyViewPos` by mapping the camera's position in main world extents into `SkyDef` inner view extents.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/drawsky.cpp`
  - Builds sky view/frustum and calls the renderer-specific sky object draw.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_drawsky.cpp`
  - Disables depth read/write, sets sky fog distances, and draws sky objects.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_renderblock.cpp`
  - Loads render-block sky portals and projects them to screen bounds.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_renderworld.cpp`
  - Extends sky bounds from visible render blocks and draws sky before normal world geometry.
- `mm9/ltjs/engine/runtime/render_a/src/sys/d3d/*`
  - Mirrors the same architecture in LTJS. Use it as corroborating context, not as MM9 binary authority.
- `mm9/godot-dat-reader/Models/DAT.gd`
  - Documents a render-data model containing `RenderSkyPortal`, `RenderBlock.sky_portals`, occluders, and light groups.
- `mm9/mm9_tools/PreFabs/*.ed`
  - Contain authored skybox prefabs with `SkyPortal`, `SkyPan`, `DemoSkyWorldModel`, `SkyDims`, and six-face DTX
    skybox textures.

OpenYAMM references:

- `docs/mm9/MM9_DAT_FORMAT_NOTES.md`
  - DAT v66 top-level layout and surface flag preservation.
- `docs/mm9/MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md`
  - Rendering should use DAT source structures directly for MM9.
- `docs/mm9/MM9_DAT_PHYSICS_COLLISION_CONTRACT.md`
  - `DatWorldView` should expose source world models by role, including sky.
- `docs/mm9/MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md`
  - Existing short sky-object note and render-data cautions.
- `game/mm9/Mm9DatWorld.h`
  - `Mm9DatWorld`, `Mm9DatModelRenderRole`, and `Mm9DatRenderFilterSky`.
- `game/mm9/Mm9DatWorld.cpp`
  - Parses surface flags, builds DAT render mesh, and marks sky triangles based on model roles.
- `game/outdoor/OutdoorRenderer.cpp`
  - Existing MM6-MM8 outdoor sky texture path. Useful for bgfx pass/resource patterns, not the MM9 sky model.
- `game/shaders/fs_indoor_textured_lit.sc`
  - Existing shader-side sky projection for MM6-MM8 indoor sky faces.
- `game/shaders/fs_outdoor_force_perspective.sc`
  - Existing force-perspective texture/fog shader for MM6-MM8 outdoor sky.

## Relevant Reference Code Sections

These sections are important for behavior. Use them as reference points, not as code to paste into OpenYAMM.

### Sky Definition

`mm9/lithtech/sdk/inc/ltbasetypes.h`:

```cpp
struct SkyDef
{
    LTVector m_Min, m_Max;
    LTVector m_ViewMin, m_ViewMax;
};
```

Meaning:

- `m_Min` / `m_Max`: authored sky-box bounds.
- `m_ViewMin` / `m_ViewMax`: smaller inner camera movement bounds used for parallax.

### DemoSkyWorldModel Behavior

`mm9/lithtech/sdk/inc/ltengineobjects.cpp`:

```text
DemoSkyWorldModel properties:
  SkyDims
  Flags
  Index
  InnerPercentX
  InnerPercentY
  InnerPercentZ

On object created:
  if SkyDims is non-zero:
    SkyDef.min = object_pos - SkyDims
    SkyDef.max = object_pos + SkyDims
    inner = SkyDims * InnerPercent
    SkyDef.view_min = object_pos - inner
    SkyDef.view_max = object_pos + inner
    SetSkyDef(SkyDef)

  set object flag FLAG2_SKYOBJECT
  AddObjectToSky(object, Index)
```

OpenYAMM implication:

- Parse typed sky definitions from raw MM9 objects.
- Sky objects should be sorted by `Index`.
- A `DemoSkyWorldModel` with non-zero `SkyDims` can define the active sky camera volume.

### SkyPointer Behavior

`SkyPointer` is similar to `DemoSkyWorldModel`, except it references another object by `SkyObjectName`.

OpenYAMM implication:

- A `SkyPointer` should register the referenced object as a sky object.
- If `SkyPointer.SkyDims` is non-zero, it can also define/override `SkyDef`.
- If multiple sky definitions exist, preserve all source data and choose the active one deterministically. LithTech
  expected only one object with non-zero sky dims for a given setup.

### Surface Flags

`mm9/lithtech/runtime/world/src/de_world.h`:

```text
SURF_SOLID        = 1 << 0
SURF_TRANSPARENT  = 1 << 3
SURF_SKY          = 1 << 4
SURF_PANNINGSKY   = 1 << 15
```

OpenYAMM implication:

- Preserve `SURF_SKY` separately from ordinary visible geometry.
- Do not treat `SURF_SKY` as a six-face skybox material. It marks a sky portal/opening.
- `SURF_PANNINGSKY`/`SkyPan` exists, but should be low priority unless a concrete MM9 map needs it.

### Sky Camera Position

`mm9/lithtech/runtime/render_a/src/sys/d3d/common_draw.cpp` computes sky view position by percent through the main world
extents:

```text
if normal draw mode:
  percent = (camera_position - main_world_extents_min) / (main_world_extents_max - main_world_extents_min)
else:
  percent = (0.5, 0.5, 0.5)

sky_view_pos = sky_def.view_min + percent * (sky_def.view_max - sky_def.view_min)
```

OpenYAMM implication:

- The MM9 sky camera keeps normal camera orientation.
- Camera translation is remapped into the smaller sky inner volume to create parallax.
- Use DAT world extents from `Mm9DatWorld.worldInfo.extentsMinLt/extentsMaxLt`, converted consistently with the existing
  MM9 coordinate mapping.

### Sky Draw Pass

`mm9/lithtech/runtime/render_a/src/sys/d3d/drawsky.cpp` and `d3d_drawsky.cpp`:

```text
if DrawSky disabled or no sky objects:
  skip

build sky frustum over requested screen extents
set sky transform
draw sky objects
restore normal transform

while drawing sky objects:
  disable depth write
  disable depth test/read
  set sky fog near/far
  draw visible sky world models, polygrids, and sprites
```

OpenYAMM implication:

- Add a separate bgfx view/pass before normal DAT world geometry.
- Disable depth read/write for the sky pass.
- Start with world-model sky objects. Polygrids and sprites can be later if MM9 data requires them.
- Use sky fog as a separate uniform set from normal world fog.

### Sky Portal Bounds

`mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_renderblock.cpp` and `d3d_renderworld.cpp`:

```text
render block load:
  read sky_portal_count
  read sky portal polygons

frame draw:
  collect visible render blocks
  for each visible block:
    project sky portal polygons to screen
    extend min/max sky bounds
  if bounds have area:
    draw sky only over those extents
  draw normal world
```

OpenYAMM implication:

- Full fidelity requires decoding MM9 DAT render data at `render_data_pos`.
- A full-viewport sky pass is acceptable as a first version because normal world geometry will cover the sky where there
  are walls/terrain, but it may overdraw or show through missing depth/alpha cases until portal clipping exists.

## Current MM9 Data Evidence

Example from `assets_dev/worlds/mm9/maps/bootcamp.dat_world.yml`:

```yaml
world_models:
- source_model_index: 0
  source_name: SkyBox0
  kind: sky
  textures:
  - TEXTURES\Skybox\SeaSky_Up.dtx
  - TEXTURES\Skybox\SeaSky_Right.dtx
  - TEXTURES\Skybox\SeaSky_Back.dtx
  - TEXTURES\Skybox\SeaSky_Left.dtx
  - TEXTURES\Skybox\SeaSky_Down.dtx
  - TEXTURES\Skybox\SeaSky_Front.dtx
  roles:
    sky: true
    movable: true
```

Example from `assets_dev/worlds/mm9/maps/bootcamp.raw_objects.yml`:

```yaml
objects:
  - name: SkyPointer
    properties:
      Name: SkyPointer0
      SkyObjectName: TOD_Sky0
      SkyDims: [0.0, 0.0, 0.0]
      InnerPercentX/Y/Z: 0.1
  - name: DemoSkyWorldModel
    properties:
      Name: SkyBox0
      SkyDims: [128.0, 128.0, 128.0]
      Index: 0
      InnerPercentX/Y/Z: 0.1
  - name: TOD_Sky
    properties:
      Name: TOD_Sky0
```

Notes:

- `SkyBox0` and `TOD_Sky0` are both classified as sky models in generated DAT sidecars.
- Some raw object properties currently expose generic decoded values. For typed runtime use, add explicit typed parsing
  for sky object properties instead of depending on generic `value_json` text.
- Several maps contain skybox DTX aliases such as `SnowMtns_*`, `SeaSky_*`, `Arslegaard*`, `RedSky_*`, `starfield`, and
  `Clouds1`.

## Current OpenYAMM State

### DAT World Parser

`game/mm9/Mm9DatWorld.h` currently stores:

- `Mm9DatWorld::renderDataPos`
- `Mm9DatWorld::worldInfo`
- `std::vector<Mm9DatWorldModel> worldModels`
- `Mm9DatModelRenderRole::sky`
- `Mm9DatRenderFilterSky`

`game/mm9/Mm9DatWorld.cpp` currently:

- reads surface flags in `readSurface`;
- preserves `surface.flags` into render triangles;
- marks render-filter entries with `Mm9DatRenderFilterSky` when the model role is sky.

This means a first DAT-world sky renderer can be built from existing source-model geometry and model roles.

### MM6-MM8 Sky Paths

OpenYAMM already has sky rendering, but the current paths are MM6-MM8-style:

- `OutdoorRenderer::renderOutdoorSky` draws a force-perspective screen-space sky texture.
- `fs_outdoor_force_perspective.sc` applies fog to that projected texture.
- `fs_indoor_textured_lit.sc` contains a special sky projection path for indoor sky-marked faces.

These are useful bgfx and shader examples, but MM9 should not be forced into them because MM9 sky is authored geometry
with parallax and object layering.

## Proposed Data Model

Add typed sky data either directly to `Mm9DatWorld` or to a sidecar/runtime projection owned by `DatWorldView`.
Preserve raw source data either way.

Suggested structs:

```cpp
struct Mm9DatSkyDef
{
    size_t sourceObjectIndex = 0;
    std::string sourceObjectName;
    Mm9DatVec3 positionLt;
    Mm9DatVec3 skyDimsLt;
    Mm9DatVec3 innerPercents = {0.1f, 0.1f, 0.1f};
    Mm9DatVec3 minLt;
    Mm9DatVec3 maxLt;
    Mm9DatVec3 viewMinLt;
    Mm9DatVec3 viewMaxLt;
    bool valid = false;
};

struct Mm9DatSkyObject
{
    size_t sourceObjectIndex = 0;
    std::string objectName;
    std::string skyObjectName;
    size_t sourceModelIndex = 0;
    int index = 0;
    bool hasModel = false;
};

struct Mm9DatSkyPortal
{
    size_t renderBlockIndex = 0;
    std::vector<Mm9DatVec3> verticesLt;
    Mm9DatVec3 planeNormalLt;
    float planeDistance = 0.0f;
};

struct Mm9DatSkyLayer
{
    std::vector<Mm9DatSkyDef> definitions;
    std::vector<Mm9DatSkyObject> objects;
    std::vector<Mm9DatSkyPortal> portals;
};
```

Implementation detail:

- Use existing coordinate conversion helpers when moving from LithTech LT coordinates to OpenYAMM world coordinates.
- Store source indexes everywhere. Runtime/editor ids can be generated, but source indexes are required for validation
  and regeneration.
- Treat model-name matching as a fallback only. Prefer object `Name` and `SkyObjectName` linkage when available.

## Import And Sidecar Changes

Update the MM9 generation pipeline, not hand-edited sidecars:

- `tools/mm9_import_discovery/generate_mm9_dat_native_sidecars.py`
  - Already classifies sky models using name prefixes.
  - Extend output with a typed `sky:` section.
- MM9 raw object generation
  - Add typed extraction for `SkyPointer`, `DemoSkyWorldModel`, and `TOD_Sky`.
  - Preserve the existing raw object records unchanged.
- DAT render-data parser
  - Eventually parse render blocks from `render_data_pos`.
  - Preserve raw render-data bytes and hashes until all render-data structures are verified.

Suggested generated sidecar projection:

```yaml
sky:
  definitions:
    - source_object_index: 1
      source_class: DemoSkyWorldModel
      source_name: SkyBox0
      position_lt: [24896.0, -192.0, 12096.0]
      sky_dims_lt: [128.0, 128.0, 128.0]
      inner_percent: [0.1, 0.1, 0.1]
      min_lt: [...]
      max_lt: [...]
      view_min_lt: [...]
      view_max_lt: [...]
  objects:
    - source_object_index: 1
      source_class: DemoSkyWorldModel
      source_name: SkyBox0
      source_model_index: 0
      index: 0
    - source_object_index: 0
      source_class: SkyPointer
      source_name: SkyPointer0
      sky_object_name: TOD_Sky0
      source_model_index: 1
      index: <typed-index>
  portals:
    decoded: false
```

When render data is decoded:

```yaml
sky:
  portals:
    decoded: true
    render_block_count: 123
    portal_count: 456
```

## Runtime Rendering Plan

### Phase 1: Full-Viewport Sky Model Pass

This is the recommended first implementation.

1. Load DAT sky world models through the same material/texture resolution used for normal DAT render models.
2. Build `Mm9DatSkyLayer` from typed raw objects and model roles.
3. Compute the active `SkyDef`.
4. Sort sky objects by `Index`.
5. Create a sky camera:
   - orientation equals the gameplay camera orientation;
   - position is the remapped `SkyDef.viewMin/viewMax` position;
   - near/far can follow LithTech defaults initially (`near` small, `far` enough for sky model bounds).
6. Submit a bgfx sky view before normal DAT world geometry:
   - clear only as needed;
   - no depth read;
   - no depth write;
   - write RGB/A;
   - culling/material states from sky model materials;
   - no gameplay picking/collision.
7. Submit normal DAT world geometry after the sky pass.

Expected behavior:

- Sky appears behind visible DAT world geometry.
- Sky world-model parallax works.
- Most open-map visuals should be materially closer to MM9 than using a flat projected sky texture.

Known limitations:

- Sky may overdraw in places where portal clipping should restrict it.
- Sky portal holes are not yet bounded by render-data portals.
- Sky sprites/polygrids are not handled unless added explicitly.
- `SkyPan` is not handled.

### Phase 2: Sky Portal Clipping

After render-data decoding exists:

1. Parse render blocks from `Mm9DatWorld.renderDataPos`.
2. Decode sky portal polygons into source-space vertices and plane data.
3. During frame culling, collect visible render blocks.
4. Project visible sky portals to screen-space bounds.
5. Render sky only over those bounds.

bgfx implementation options:

- Scissor rectangle per accumulated portal bounds for a first approximation.
- Stencil mask from projected portal polygons for closer fidelity.
- Multiple scissor rectangles if one large accumulated rectangle causes unacceptable overdraw.

LithTech used screen bounds, not a perfect portal stencil, so a scissor/bounds approach is historically consistent for
an initial portal implementation.

### Phase 3: Dynamic Sky Objects And Effects

Add only if MM9 content needs it:

- `TOD_Sky` animated time-of-day properties.
- Polygrid sky objects.
- Sprite/lens-flare objects attached to sky.
- `SURF_PANNINGSKY` / `SkyPan` overlay behavior.
- Sky fog values derived from world/object properties instead of a fixed default.

## DatWorldView Responsibilities

`DatWorldView` should expose sky as a world-format service, not as shared gameplay logic:

- `const Mm9DatSkyLayer &skyLayer() const`
- `std::vector<size_t> skyModelIndices() const`
- `std::optional<Mm9DatSkyDef> activeSkyDef() const`
- `Mm9DatVec3 computeSkyCameraPositionLt(const Mm9DatVec3 &cameraPositionLt) const`
- access to sky portals once render data is decoded;
- source-index lookups from sky object names to world model indexes.

`Mm9DatLevelView` or equivalent renderer should consume those services and submit bgfx sky passes. Shared gameplay should
not know about sky objects except for line-of-sight/raycast semantics where a ray hits `SURF_SKY`.

## Coordinate Mapping

MM9 DAT sidecars document the coordinate mapping:

```yaml
coordinate_system:
  source: lithtech_mm9
  openyamm_mapping:
  - x
  - z
  - y
  scale: 2.56
```

Rules:

- Perform sky-def math in LithTech coordinates first when using DAT source extents and raw object positions.
- Convert the resulting camera position to OpenYAMM coordinates for rendering.
- Convert sky model geometry through the same path as normal DAT geometry.
- Keep all stored source values in LT coordinates for lossless/debug output.

## Material And Texture Handling

Sky models use ordinary DTX textures through the DAT texture list. Examples include:

- `TEXTURES\Skybox\SeaSky_Up.dtx`
- `TEXTURES\Skybox\SeaSky_Right.dtx`
- `TEXTURES\Skybox\SnowMtns_N.dtx`
- `TEXTURES\Skybox\ArslegaardFront.dtx`
- `TEXTURES\Skybox\RedSky_Back.dtx`
- `TEXTURES\Skybox\starfield.dtx`

Renderer requirements:

- Use existing MM9 DTX decoding/material alias paths.
- Preserve DTX metadata and texture effects.
- Do not convert skyboxes to cubemaps as the authoritative path. Six-face cubemaps could be an optimization only if they
  are generated from original sky world-model materials and preserve orientation.
- Do not use MM6-MM8 `sky_textures` lookup for MM9 DAT sky unless there is an explicit fallback mode.

## Raycasts And Interaction Semantics

LithTech model setup has a helper that treats rays hitting `SURF_SKY` as sky hits. OpenYAMM should keep this semantic:

- A raycast hitting `SURF_SKY` should not behave like a solid wall unless the source data also marks it solid for a
  specific subsystem.
- Projectiles, clicks, and LOS should be checked against DAT collision policy. Sky portals are normally visual openings.
- `PhysicsBSP` / `VisBSP` remain separate from sky model rendering.

This belongs in `DatWorldView` collision/query services, not in the sky renderer.

## Validation Strategy

Add focused validation before broad runtime integration:

- Unit tests for typed sky object extraction from raw object properties.
- Unit tests for `SkyDef` construction:
  - zero `SkyDims` does not create an active definition;
  - non-zero `SkyDims` creates min/max and view min/max;
  - inner percent defaults are preserved.
- Unit tests for sky camera position:
  - world min maps to `viewMin`;
  - world max maps to `viewMax`;
  - world center maps to sky view center.
- Sidecar idempotency tests:
  - regenerated `sky:` sections are stable;
  - raw object records remain unchanged.
- Render smoke tests:
  - a sky map such as `bootcamp`, `thjorgard`, or `arslegardcity` renders nonblank sky pixels;
  - sky model is behind normal world geometry;
  - camera translation changes sky parallax subtly;
  - sky pass does not affect gameplay picking/collision.

For portal clipping:

- Add parser tests against known render-data blocks with nonzero sky portal counts.
- Validate portal polygon counts against local Godot DAT reader expectations where possible.
- Add screenshot comparison or pixel checks for sky not drawing through enclosed interior areas.

## Implementation Checklist

1. Add typed MM9 sky extraction.
   - Source: raw object records.
   - Output: generated `sky:` sidecar section or runtime projection.
   - Preserve raw records unchanged.

2. Add `Mm9DatSkyLayer` projection.
   - Link sky objects to world models by object/model name.
   - Sort by `Index`.
   - Preserve source indexes.

3. Add `DatWorldView` sky services.
   - Active `SkyDef`.
   - Sky object model list.
   - Sky camera position computation.

4. Add bgfx DAT sky render pass.
   - Full-viewport pass first.
   - Depth read/write disabled.
   - Uses DAT world-model geometry and DTX materials.

5. Wire sky pass before normal DAT world geometry.
   - Do not change MM6-MM8 outdoor/indoor sky behavior.
   - Keep MM9-specific logic under MM9 DAT runtime/view code.

6. Add tests and smoke coverage.
   - Typed extraction.
   - Sky camera math.
   - Render nonblank sky.

7. Decode render-data sky portals.
   - Parse from `render_data_pos`.
   - Preserve raw bytes/hash.
   - Add scissor/stencil clipping.

8. Consider optional effects.
   - `TOD_Sky`.
   - Polygrid/sprite sky objects.
   - `SkyPan`.

## Open Questions

- Which object should win when multiple objects define non-zero `SkyDims` in one map?
  - Recommended initial behavior: preserve all definitions, choose lowest sky `Index`, warn in diagnostics.
- Should `TOD_Sky` be rendered as a world model, scripted sky controller, or both?
  - Initial behavior: render linked sky world model if present; preserve `TOD_Sky` properties for later behavior.
- Are MM9 render-data sky portals byte-identical to the Godot DAT reader's v66 render-block structures?
  - Must be locally verified before treating render-data parsing as authoritative.
- Does MM9 use `SkyPan` in shipped maps in a visible way?
  - Current evidence suggests skybox world models are the main path. Keep `SkyPan` deferred until a map requires it.

## Recommended First Task

Implement typed sky extraction and a full-viewport DAT sky world-model pass for one representative map, preferably
`bootcamp` or `thjorgard`, because both have clear generated sky model/object data and skybox textures. Keep portal
clipping out of the first task, but design the data structures so decoded sky portals can be added without changing the
public renderer contract.
