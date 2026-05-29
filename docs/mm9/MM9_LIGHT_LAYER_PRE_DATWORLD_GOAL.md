# MM9 Light Layer Pre-DatWorld Goal

Status: implementation goal for renderer-neutral MM9 light work that can be completed before a real in-game
`DatWorldView` renderer exists.

## Objective

Tighten `game/mm9/Mm9LightLayer.*` so it matches the locally checked LithTech lighting semantics for authored light
objects, world-info ambient data, and static-object-light eligibility. The output should remain source-preserving and
renderer-neutral, but future DAT rendering should be able to consume it without another semantic cleanup pass.

This goal does not implement bgfx DAT world rendering, baked lightmap rendering, runtime light-grid sampling,
light-group animation, or final spatial light queries in the game runtime.

## Read First

- [MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md](MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md): current reference findings,
  LithTech property semantics, and performance model.
- [MM9_DAT_FORMAT_NOTES.md](MM9_DAT_FORMAT_NOTES.md): byte-level DAT parser authority.
- [MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md](MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md): source-preservation and
  DAT/DTX runtime constraints.
- `mm9/lithtech/sdk/inc/ltengineobjects.cpp`: authored light class/property definitions.
- `mm9/lithtech/runtime/world/src/world_shared_bsp.cpp`: runtime static-light extraction.
- `mm9/lithtech/runtime/world/src/light_table.cpp`: light-grid load and trilinear sampling semantics.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/setupmodel.cpp`: model lighting query path.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/setuptouchinglights.cpp`: object/particle touching-light query path.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_rendershader_dynamiclight.cpp`: dynamic-light render pass behavior.

## Current Gap

The existing OpenYAMM light layer is useful, but it is currently a loose projection:

- `ConvertToAmbient` is represented as a boolean, while LithTech treats it as a real value.
- `Attenuation` is represented as a numeric list, while LithTech treats it as a string enum.
- `DirLight` conversion depends on `LightColor`, while LithTech's authored `DirLight` uses `InnerColor`.
- Static `RenderLight` conversion accepts any light with position, color, and radius, while LithTech only creates
  static object lights when `LightObjects=true` and `FastLightObjects=false`.
- Brightness and attenuation derived values are not computed the same way LithTech computes static object lights.

## Architecture

Keep the layer pure `game/mm9` and renderer-neutral:

- Raw DAT and generated raw-object sidecars remain authoritative.
- Typed light data is a convenience projection over source data, not a replacement for it.
- Unsupported properties must stay visible through raw/source property preservation or diagnostics.
- Renderer-facing helpers must be stricter than source projection. Project all authored lights, but only convert
  LithTech-eligible static object lights into `RenderLight`.
- Do not add MM6-MM8 lighting behavior or shared renderer changes for this goal.

Prefer small helpers close to `Mm9LightLayer` and the MM9 raw-object projection. Do not add a broad adapter layer.

## LithTech-Aligned Semantics

Implement these typed fields and defaults:

- `LightObjects`: boolean, default true for `Light` and `DirLight`; false or absent for classes that do not declare it.
- `FastLightObjects`: boolean, default true for `Light`, `DirLight`, and `ObjectLight`.
- `CastShadows`: boolean, default true.
- `ClipLight`: boolean, default true for `Light` and `DirLight`.
- `BrightScale`: float, default `1.0`.
- `ObjectBrightScale`: float, default `1.0` where the class declares it.
- `ConvertToAmbient`: float, default `0.0`.
- `AttCoefs`: vec3/list, default `1.0 0.0 19.0`.
- `AttExps`: vec3/list, default `0.0 0.0 -2.0`.
- `Attenuation`: enum/string, default `Quartic`, valid known values `D3D`, `Linear`, and `Quartic`.
- `FOV`: authored degrees, with derived runtime value `cos(FOV * pi / 360)`.
- `LightGroup`: authored string, preserved as string; hashing or runtime binding is deferred.
- `LightColor`: primary color for `Light` and `ObjectLight`.
- `InnerColor`: primary color for `DirLight`; also accepted as an effective color fallback like LithTech's runtime scan.
- `OuterColor`, `Size`, `AttType`, and `CastShadowMesh`: known source properties to preserve and avoid noisy
  unsupported-property diagnostics.

Do not emulate the later runtime parser's uncertain sticky `FastLightObjects` behavior unless local MM9 DAT evidence
proves it is required. Use authored class defaults for deterministic projection.

## Derived Values

Add renderer-neutral derived data or helper functions:

- `effectiveLightObjects`
- `effectiveFastLightObjects`
- `effectiveCastShadows`
- `effectiveColor`
- `effectiveObjectLightColor = effectiveColor * BrightScale * ObjectBrightScale`
- `effectiveAttCoefs = AttCoefs * pow(LightRadius, AttExps)`
- `effectiveFovCos`
- `staticObjectLightEligible = effectiveLightObjects && !effectiveFastLightObjects`
- `fastObjectLightingSource = effectiveLightObjects && effectiveFastLightObjects`

The derived values should be available without a world renderer and should be deterministic for tests and editor
diagnostics.

## Static RenderLight Helper

Update `convertMm9LightObjectToRenderLight` and `buildMm9StaticRenderLights` so they reflect the LithTech static-light
path:

- Reject missing position, effective color, radius, or nonpositive radius.
- Reject `LightObjects=false`.
- Reject `FastLightObjects=true`.
- Use effective object-light color after brightness scaling.
- Preserve source id and static classification.
- Preserve or expose `ConvertToAmbient`, attenuation enum, computed attenuation coefficients, cast-shadow flag, FOV
  cosine, and light group through MM9-specific data even if generic `RenderLight` cannot express all of them yet.

If generic `RenderLight` cannot represent a field, do not force it into an unrelated field. Keep the value in MM9 light
data and document the renderer boundary.

## Performance Constraints

Follow LithTech's performance model when shaping APIs:

- Precompute derived light values once when the layer is built; avoid per-frame recomputation later.
- Keep static-eligible lights separable from fast-object-lighting sources.
- Expose source indices and stable ids so a future DAT runtime can build a spatial index once.
- Do not design APIs that require scanning every light for every model every frame.
- Keep light-grid/lightmap data separate from static object lights; they are separate systems in LithTech.
- Keep dynamic runtime lights separate from baked/static MM9 lighting; dynamic lights are an additive effect path, not a
  replacement for baked lighting.

The future renderer should be able to build:

- A static-light spatial index for `LightObjects=true && FastLightObjects=false` records.
- A fast-lighting/light-grid sampler if MM9 v66 render bytes are decoded.
- A baked lightmap renderer from render blocks.
- A dynamic-light pass for runtime FX.

This goal only prepares the data contracts.

## Implementation Checklist

- [ ] Change `Mm9LightObject::convertToAmbient` from bool to float while preserving source property availability.
- [ ] Change `Mm9LightObject::attenuation` from numeric list to a string/enum representation.
- [ ] Preserve `AttCoefs` and `AttExps` as vector/list fields with explicit defaults.
- [ ] Add known-property handling for `Size`, `AttType`, and `CastShadowMesh`.
- [ ] Apply class-aware defaults for `Light`, `DirLight`, and `ObjectLight`.
- [ ] Add effective color resolution with `DirLight.InnerColor` support.
- [ ] Add derived static eligibility and fast-object-lighting classification.
- [ ] Add derived object-light color and attenuation coefficients.
- [ ] Clamp parsed `AmbientLight` to `0..255` while preserving diagnostics for malformed values.
- [ ] Make `RenderLight` conversion strict about static-object-light eligibility.
- [ ] Keep raw/source properties available for every projected light.
- [ ] Keep the implementation independent from MM6-MM8 lighting paths.

## Tests

Use focused unit coverage in `tests/Mm9LightLayerTests.cpp` and raw-sidecar projection coverage in
`tests/Mm9EditorDatLevelMetadataTests.cpp`.

Required tests:

- `WorldInfo.property_string` preserves raw text and clamps valid numeric ambient values to `0..255`.
- Malformed world-info values produce stable diagnostics.
- `ConvertToAmbient` decodes and preserves float values.
- `Attenuation` decodes string values and rejects or diagnoses invalid values.
- Missing authored defaults match the LithTech class definitions.
- `DirLight` with only `InnerColor` has an effective color.
- `Light` and `ObjectLight` use `LightColor` as effective color.
- `LightObjects=false` prevents static conversion.
- `FastLightObjects=true` prevents static conversion.
- `LightObjects=true && FastLightObjects=false` allows static conversion.
- Static conversion applies `BrightScale * ObjectBrightScale`.
- Derived attenuation coefficients use `AttCoefs * pow(radius, AttExps)`.
- Derived FOV cosine uses `cos(FOV * pi / 360)`.
- `Size`, `AttType`, and `CastShadowMesh` are known/preserved properties.
- Raw sidecar projection maps real-ish YAML values into the corrected typed fields.

## Build And Verification

Use focused tests first:

```bash
cmake --build build --target openyamm_unit_tests/fast -j25
./build/tests/openyamm_unit_tests --test-case="MM9 light layer*" --success=false
```

If raw sidecar projection tests are changed, include:

```bash
./build/tests/openyamm_unit_tests --test-case="MM9 raw objects*" --success=false
```

Run the normal build only if CMake metadata or shared headers require it:

```bash
cmake --build build --target openyamm -j25
```

## Deferred

- DAT render-block parsing and bgfx world rendering.
- Baked MM9 lightmap/shadow-map rendering.
- Runtime light-grid byte discovery and sampling.
- Light-group animation/state binding.
- Static-light spatial index construction in the in-game DAT runtime.
- Dynamic bgfx light pass for MM9 DAT world geometry.
- Screenshot/headless visual parity coverage.

## Done Criteria

- `Mm9LightLayer` exposes LithTech-aligned property types, defaults, and derived semantics.
- Static `RenderLight` conversion is strict and only covers non-fast object-lighting sources.
- Effective color, brightness, attenuation, FOV, and classification behavior are unit-tested.
- Raw source properties remain available.
- No generated MM9 sidecars, original `mm9/source` files, or MM6-MM8 lighting paths are modified.
