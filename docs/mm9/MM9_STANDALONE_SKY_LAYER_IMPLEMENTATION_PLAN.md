# MM9 Standalone Sky Layer Implementation Plan

This plan covers the MM9 skybox work that can be implemented now, independently of the future DAT world renderer.
The goal is a pure `game/mm9` sky data/model layer with tests, ready to plug into `DatWorldView` and the DAT renderer
later.

Do not implement bgfx rendering in this phase.

## Scope

Implement now:

- typed MM9 sky data structs;
- extraction from parsed DAT world models plus raw object records;
- name/index linking between sky objects and DAT world models;
- LithTech-style `SkyDef` construction;
- LithTech-style sky camera position mapping;
- focused unit tests.

Defer:

- bgfx sky pass;
- DAT world-model render buffers;
- DTX material binding;
- render-data sky portal decoding;
- stencil/scissor portal clipping;
- `TOD_Sky` animation behavior;
- `SkyPan` behavior.

## Intended Runtime Shape

The standalone layer should be usable like this:

```cpp
Mm9DatWorld world = ...;
std::vector<Mm9RawObject> rawObjects = ...;

Mm9SkyLayer skyLayer = buildMm9SkyLayer(world, rawObjects);

std::optional<Mm9SkyDef> skyDef = selectActiveMm9SkyDef(skyLayer);
std::optional<Mm9SkyCameraMap> skyCameraMap = buildMm9SkyCameraMap(world.worldInfo, *skyDef);
Mm9DatVec3 skyCameraLt = computeMm9SkyCameraPositionLt(*skyCameraMap, cameraPositionLt);
```

Later, `DatWorldView` can own/cache this projection and expose it to `Mm9DatLevelView`.

## Proposed Files

Add:

- `game/mm9/Mm9SkyLayer.h`
- `game/mm9/Mm9SkyLayer.cpp`
- `tests/mm9_sky_layer_tests.cpp` or equivalent repo-local doctest file

Only add additional files if existing test organization makes that necessary.

## Data Model

Create simple source-preserving structs:

```cpp
struct Mm9SkyDef
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    Mm9DatVec3 positionLt;
    Mm9DatVec3 skyDimsLt;
    Mm9DatVec3 innerPercentLt;
    Mm9DatVec3 minLt;
    Mm9DatVec3 maxLt;
    Mm9DatVec3 viewMinLt;
    Mm9DatVec3 viewMaxLt;
    int flags = 0;
    int index = 0;
    bool valid = false;
};

struct Mm9SkyObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string skyObjectName;
    size_t sourceModelIndex = 0;
    int flags = 0;
    int index = 0;
    bool hasSourceModel = false;
};

struct Mm9SkyLayer
{
    std::vector<Mm9SkyDef> definitions;
    std::vector<Mm9SkyObject> objects;
    std::vector<size_t> skyModelIndices;
};

struct Mm9SkyCameraMap
{
    Mm9DatVec3 worldMinLt;
    Mm9DatVec3 reciprocalWorldSizeLt;
    Mm9DatVec3 viewMinLt;
    Mm9DatVec3 viewSizeLt;
};
```

Adjust names/types to match existing `game/mm9` conventions after reading current raw-object types.

## Builder Responsibilities

`buildMm9SkyLayer(...)` should:

- scan raw objects for `DemoSkyWorldModel`;
- scan raw objects for `SkyPointer`;
- optionally preserve `TOD_Sky` object names as link targets;
- extract common properties:
  - `Name`;
  - `Pos`;
  - `SkyDims`;
  - `SkyObjectName`;
  - `Index`;
  - `InnerPercentX`;
  - `InnerPercentY`;
  - `InnerPercentZ`;
- link object names to `Mm9DatWorldModel::name` / source model index;
- include existing model-role sky models from `Mm9DatModelRenderRole` or equivalent projection if available;
- preserve source object indexes and source model indexes;
- sort sky objects by `Index`, then source object index for deterministic output.

Default behavior:

- default `InnerPercentX/Y/Z` to `0.1f` when absent;
- default `Index` to `0` when absent;
- a sky definition is valid only when all `SkyDims` components are non-zero;
- a `SkyPointer` with zero `SkyDims` registers a target sky object but does not define a `SkyDef`;
- preserve unlinked sky objects with `hasSourceModel = false` for diagnostics.

## Camera Math

Implement this as pure functions:

```cpp
Mm9SkyDef makeMm9SkyDef(...);

std::optional<Mm9DatVec3> computeMm9SkyCameraPositionLt(
    const Mm9DatWorldInfo &worldInfo,
    const Mm9SkyDef &skyDef,
    const Mm9DatVec3 &cameraPositionLt);

std::optional<Mm9SkyCameraMap> buildMm9SkyCameraMap(
    const Mm9DatWorldInfo &worldInfo,
    const Mm9SkyDef &skyDef);

Mm9DatVec3 computeMm9SkyCameraPositionLt(
    const Mm9SkyCameraMap &cameraMap,
    const Mm9DatVec3 &cameraPositionLt);
```

Formula:

```text
percent.x = (camera.x - world.extents_min.x) / (world.extents_max.x - world.extents_min.x)
percent.y = (camera.y - world.extents_min.y) / (world.extents_max.y - world.extents_min.y)
percent.z = (camera.z - world.extents_min.z) / (world.extents_max.z - world.extents_min.z)

sky_camera = skyDef.viewMin + percent * (skyDef.viewMax - skyDef.viewMin)
```

Implementation notes:

- Do this math in LithTech coordinates.
- Do not clamp percent in the normal path. `mm9/lithtech/runtime/render_a/src/sys/d3d/common_draw.cpp`
  computes raw `(camera - worldMin) / (worldMax - worldMin)` percents and applies them directly.
- Cache `Mm9SkyCameraMap` at `DatWorldView`/map-load time so the frame path avoids divisions and optionals.
- Return `nullopt` from `buildMm9SkyCameraMap` if any world extent axis is degenerate.
- Keep coordinate conversion out of this helper; renderer/view code can convert LT coordinates later.

## Performance Constraints

- Run `buildMm9SkyLayer` only when a DAT world or sky-relevant object/model data changes.
- Keep property scans, string normalization, sorting, and unordered-map lookups out of the per-frame path.
- Store `Mm9SkyCameraMap` beside the active sky definition after load/setup. Rebuild it only when the active sky
  definition or DAT world extents change.
- The per-frame sky camera calculation should be only subtract/multiply/add per axis.
- Skip the sky pass completely when `skyModelIndices` is empty or there is no active cached camera map.
- Future renderer work should render only the collected sky model indices in the sky pass, not rescan all DAT models.
- LithTech clips sky drawing to sky portal screen bounds in
  `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_renderworld.cpp`; keep that as a later optimization after DAT
  render-data sky portals are decoded.
- Coordinate conversion should happen once at the renderer boundary. Keep `Mm9SkyLayer` values in LithTech coordinates
  so this pure layer never pays conversion cost or risks mixed-coordinate math.

## Checklist

### 1. Read Existing Types

- [ ] Inspect `game/mm9/Mm9DatWorld.h`.
- [ ] Find current raw object/property structs used by MM9 event/dialogue generation.
- [ ] Confirm whether runtime C++ has raw object loading available or only generated YAML sidecars.
- [ ] Choose the narrowest input type for the sky builder.

### 2. Add Pure Sky Layer API

- [ ] Add `Mm9SkyLayer.h`.
- [ ] Add `Mm9SkyLayer.cpp`.
- [ ] Define `Mm9SkyDef`.
- [ ] Define `Mm9SkyObject`.
- [ ] Define `Mm9SkyLayer`.
- [ ] Add `makeMm9SkyDef`.
- [ ] Add `computeMm9SkyCameraPositionLt`.
- [ ] Add `buildMm9SkyCameraMap` for cached per-frame camera mapping.
- [ ] Add `selectActiveMm9SkyDef`.

### 3. Add Property Extraction

- [ ] Add helpers for string property lookup.
- [ ] Add helpers for vec3 property lookup.
- [ ] Add helpers for int property lookup.
- [ ] Add helpers for float property lookup.
- [ ] Treat missing optional properties with explicit defaults.
- [ ] Do not parse from generated YAML text if a typed raw property API exists.

### 4. Add Object/Model Linking

- [ ] Build case-insensitive map from DAT world model name to source model index.
- [ ] Link `DemoSkyWorldModel.Name` to a world model.
- [ ] Link `SkyPointer.SkyObjectName` to a world model.
- [ ] Preserve unlinked object entries.
- [ ] Collect model-role sky models even if no raw object references them.
- [ ] Sort output deterministically.

### 5. Add Tests

- [ ] Test non-zero `SkyDims` creates valid `SkyDef`.
- [ ] Test zero `SkyDims` does not create valid `SkyDef`.
- [ ] Test default inner percents are `0.1`.
- [ ] Test explicit inner percents affect `viewMin/viewMax`.
- [ ] Test world min maps to `viewMin`.
- [ ] Test world max maps to `viewMax`.
- [ ] Test world center maps to sky view center.
- [ ] Test cached camera mapping matches the convenience helper.
- [ ] Test camera movement outside world extents remains unclamped.
- [ ] Test degenerate world extents return `nullopt`.
- [ ] Test `DemoSkyWorldModel` links by `Name`.
- [ ] Test `SkyPointer` links by `SkyObjectName`.
- [ ] Test unknown target is preserved as unlinked.
- [ ] Test output ordering by `Index`.

### 6. Build Integration

- [ ] Add new source file to `game/CMakeLists.txt`.
- [ ] Add test file to the repo's test target.
- [ ] Run focused tests.
- [ ] Run `cmake --build build --target openyamm -j25` if the test path does not compile all game sources.

## Deferred Plug-In Points

When `DatWorldView` exists:

- [ ] Store/cache `Mm9SkyLayer`.
- [ ] Expose `skyLayer()`.
- [ ] Expose active sky definition.
- [ ] Expose sky camera calculation.
- [ ] Expose sky model indices for the renderer.

When DAT rendering exists:

- [ ] Add sky bgfx view before normal DAT world view.
- [ ] Render sky model indices using normal DAT model/material buffers.
- [ ] Disable depth read/write in sky pass.
- [ ] Convert computed LT sky camera position to OpenYAMM coordinates.

When render-data decoding exists:

- [ ] Decode render-block sky portals from `render_data_pos`.
- [ ] Add portal bounds or stencil clipping.
- [ ] Add regression screenshots for enclosed spaces and sky openings.

## Acceptance Criteria For This Standalone Phase

- The new `game/mm9` API compiles without any renderer dependency.
- Tests cover sky definition construction, object linking, and camera mapping.
- The API can be called by future `DatWorldView` without changing its public data model.
- No MM6-MM8 sky rendering behavior changes.
- No generated sidecars are hand-edited.
