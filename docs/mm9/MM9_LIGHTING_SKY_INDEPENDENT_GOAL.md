# MM9 Lighting And Sky Independent Goal

Status: implementation goal for work that can be done before the playable DAT world view is complete.

## Objective

Implement the renderer-neutral MM9 sky and lighting data layers under `game/mm9/*`, with focused unit tests, so future
`DatWorldView` and DAT rendering work can consume typed, source-preserving sky and light services without reparsing raw
DAT object data.

This goal intentionally does not implement final bgfx rendering, baked lightmaps, DAT render-block sky portal clipping,
or full LithTech light-grid parity.

## Read First

- [MM9_DAT_FORMAT_NOTES.md](MM9_DAT_FORMAT_NOTES.md): current byte-level DAT parser authority.
- [MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md](MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md): lighting, `.ed`, light object,
  render-data, and test requirements.
- [MM9_LIGHT_LAYER_PRE_DATWORLD_GOAL.md](MM9_LIGHT_LAYER_PRE_DATWORLD_GOAL.md): current follow-up goal for tightening
  the renderer-neutral light layer before real `DatWorldView` integration.
- [MM9_STANDALONE_SKY_LAYER_IMPLEMENTATION_PLAN.md](MM9_STANDALONE_SKY_LAYER_IMPLEMENTATION_PLAN.md): standalone sky
  data/model plan.
- [MM9_LITHTECH_SKYBOX_RENDERING_PLAN.md](MM9_LITHTECH_SKYBOX_RENDERING_PLAN.md): sky rendering semantics and deferred
  renderer integration.
- [MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md](MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md): DAT/DTX runtime authority,
  validation rules, and source-preservation constraints.

## Scope

Implement now:

- Pure `game/mm9` sky layer structs and builders.
- Pure `game/mm9` lighting layer structs and builders.
- Parsed convenience projection of `WorldInfo.property_string` lighting fields while preserving the raw string.
- Typed projection of DAT object light classes: `Light`, `DirLight`, and `ObjectLight`.
- Source-preserving diagnostics for missing/invalid optional light and sky fields.
- Conversion helpers from MM9 light data to renderer-neutral `RenderLight` records where current shared lighting types
  fit.
- Unit tests for sky definition construction, sky camera mapping, object/model linking, world-info parsing, light object
  projection, and source-preserving defaults.

Defer:

- bgfx sky pass.
- DAT world-model render buffers and material binding.
- DAT `render_data_pos` decoding beyond preserving bounded raw spans/hashes if already available.
- Baked lightmap/shadow-map rendering.
- Light-grid or equivalent object-lighting sampling.
- Sky portal clipping/scissor/stencil from render blocks.
- `TOD_Sky` animation and `SkyPan` behavior.
- Spatial runtime light indexing and renderer-owned light selection.
- Final `DatWorldView` ownership and frame rendering.

## Architecture

Keep this work MM9-specific for now. The existing MM6-MM8 lighting and sky paths should not be changed by this goal.

Use source-preserving projections:

- Raw DAT world/object data remains authoritative.
- Typed sky/light structs are convenience/runtime projections.
- Unknown or unsupported raw properties must remain reachable through the raw object/property records.
- Missing optional fields should produce explicit defaults and, where useful, diagnostics. Do not add broad fallbacks
  that hide stale DAT parsing or broken sidecars.

Prefer narrow inputs:

- If existing parsed `Mm9DatWorld` and raw object types expose typed properties, use those APIs.
- Do not parse generated YAML text if a typed raw-object API exists.
- If required typed accessors are missing, add small helpers close to the MM9 raw-object model rather than a broad
  adapter layer.

## Proposed Files

Expected new files:

- `game/mm9/Mm9SkyLayer.h`
- `game/mm9/Mm9SkyLayer.cpp`
- `game/mm9/Mm9LightLayer.h`
- `game/mm9/Mm9LightLayer.cpp`
- `tests/Mm9SkyLayerTests.cpp`
- `tests/Mm9LightLayerTests.cpp`

Use existing test files instead if the repo already has a more specific MM9 test organization by the time this is
implemented.

## Sky Layer Requirements

Implement the standalone sky plan first:

- Define `Mm9SkyDef`, `Mm9SkyObject`, `Mm9SkyLayer`, and `Mm9SkyCameraMap`.
- Extract `DemoSkyWorldModel`, `SkyPointer`, and relevant `TOD_Sky` link targets from raw objects.
- Extract `Name`, `Pos`, `SkyDims`, `SkyObjectName`, `InnerPercentX/Y/Z`, `Flags`, and `Index`.
- Construct LithTech-style sky definition bounds:
  - `min = pos - SkyDims`
  - `max = pos + SkyDims`
  - `viewMin/viewMax` from `InnerPercent*`
- Default missing inner percents to `0.1`.
- Treat zero `SkyDims` as a preserved object but not a valid active sky definition.
- Link sky objects to DAT world models by source model name, case-insensitively.
- Preserve unlinked sky objects for diagnostics.
- Collect already-classified sky model indices from the DAT model role projection when available.
- Sort output deterministically by `Index`, then source object index.
- Provide cached sky camera mapping from main world extents to active sky view extents.
- Leave coordinate conversion to the future renderer boundary; keep this layer in LithTech coordinates.

## Light Layer Requirements

Add a renderer-neutral MM9 light projection:

- Define a world lighting info struct that preserves the raw `WorldInfo.property_string`.
- Parse convenience fields when present:
  - `AmbientLight r g b`
  - `LMGridSize`
  - `MaxLMSize`
  - `PBlockSize`
- Preserve `light_map_grid_size` from the parsed DAT world info separately from `LMGridSize`.
- Define typed light records for raw object classes:
  - `Light`
  - `DirLight`
  - `ObjectLight`
- Preserve source object index, class, name, position, rotation, and raw property availability.
- Apply LithTech-aligned authored defaults in the typed projection:
  - `LightObjects`: true for `Light` and `DirLight`
  - `FastLightObjects`: true for `Light`, `DirLight`, and `ObjectLight`
  - `CastShadows`: true
  - `BrightScale`: `1.0`
  - `ObjectBrightScale`: `1.0`
  - `ConvertToAmbient`: `0.0`
  - `AttCoefs`: `1.0 0.0 19.0`
  - `AttExps`: `0.0 0.0 -2.0`
  - `Attenuation`: `Quartic`
- Extract known fields where present:
  - `LightRadius`
  - `LightColor`
  - `InnerColor`
  - `OuterColor`
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
  - `Size`
  - `AttType`
  - `CastShadowMesh`
- Distinguish source intent:
  - `FastLightObjects` likely participates in precomputed/light-grid/lightmap-style products.
  - `LightObjects` without `FastLightObjects` can feed static runtime object/model lighting.
- Preserve `Attenuation` as a string or enum with values `D3D`, `Linear`, and `Quartic`; do not model it as a numeric
  list.
- Preserve `ConvertToAmbient` as a float; do not model it as a boolean.
- Use `LightColor` or `InnerColor` as the effective light color, because LithTech's runtime static-light scan accepts
  either and `DirLight` declares `InnerColor`.
- Expose derived, renderer-neutral semantics for future runtime use: effective color, object-light color after
  `BrightScale * ObjectBrightScale`, radius-adjusted attenuation coefficients, `cos(FOV / 2)`, static-object-light
  eligibility, and fast-object-lighting source classification.
- Provide stable diagnostics for missing required typed fields, invalid numeric/vector values, and unsupported raw
  properties.
- Add a helper that converts only static-object-light-eligible records into `RenderLight` values without requiring a
  world renderer.

## Tests

Sky tests:

- Non-zero `SkyDims` creates a valid `Mm9SkyDef`.
- Zero `SkyDims` preserves the source object but does not create a valid active definition.
- Default inner percents are `0.1`.
- Explicit inner percents affect `viewMin/viewMax`.
- World min maps to sky `viewMin`.
- World max maps to sky `viewMax`.
- World center maps to sky view center.
- Cached camera mapping matches the direct helper.
- Degenerate world extents return `nullopt`.
- `DemoSkyWorldModel.Name` links to a DAT world model.
- `SkyPointer.SkyObjectName` links to a DAT world model.
- Unknown sky target is preserved as unlinked.
- Output ordering is deterministic.

Light tests:

- `WorldInfo.property_string` parser extracts `AmbientLight`, `LMGridSize`, `MaxLMSize`, and `PBlockSize`.
- The raw property string remains byte-for-byte available after parsing.
- Missing world-info fields keep explicit defaults.
- `Light`, `DirLight`, and `ObjectLight` raw objects produce typed records without dropping source identity.
- Known light properties decode into stable typed fields.
- Unknown properties remain visible through source/raw property access or diagnostics.
- `FastLightObjects` and `LightObjects` are preserved distinctly.
- `ConvertToAmbient` remains a float and `Attenuation` remains a string/enum.
- `DirLight` with only `InnerColor` has an effective color.
- Static light conversion rejects `LightObjects=false` and `FastLightObjects=true` records.
- Static light conversion to `RenderLight` preserves position, radius, effective color/intensity, source id, and
  dynamic/static classification.
- Runtime neutrality: these tests do not load or mutate MM6-MM8 lighting paths.

## Build And Verification

Use focused unit coverage first:

```bash
cmake --build build --target openyamm_unit_tests/fast -j25
./build/tests/openyamm_unit_tests --test-case="MM9 sky layer*" --success=false
./build/tests/openyamm_unit_tests --test-case="MM9 light layer*" --success=false
```

If new files are not covered by the fast target or CMake metadata changed, run the normal project build when the
worktree is not broken by unrelated sessions:

```bash
cmake --build build --target openyamm -j25
```

If unrelated sessions break broad builds, do not fix their changes. Report the unrelated blocker and provide the focused
test results that are available.

## Done Criteria

- New sky and light layer APIs compile under `game/mm9`.
- Sky layer has no renderer dependency and exposes active sky definitions, sky objects, sky model indices, and cached
  sky camera mapping.
- Light layer has no renderer dependency and exposes parsed world lighting info, typed light objects, diagnostics, and
  renderer-neutral static light conversion.
- Tests cover the sky and light behavior listed above.
- Existing MM6-MM8 sky/lighting paths are not modified.
- No generated MM9 sidecars, Lua files, or original `mm9/source` files are hand-edited.

## Follow-Up Goals

After DAT world rendering exists:

- Store/cache `Mm9SkyLayer` and `Mm9LightLayer` in the DAT world runtime/view.
- Render sky model indices in a dedicated sky pass with depth read/write disabled.
- Feed typed static lights and dynamic request lights into the active DAT renderer.
- Add point-shade or object-light query services for actors/models.

After DAT `render_data_pos` decoding exists:

- Decode baked lightmaps, shadow-map-like data, light groups, and light-grid/equivalent samples.
- Cross-check poly `lightmap_width`/`lightmap_height` metadata against decoded render data.
- Clip sky drawing to decoded sky portal bounds.
- Add screenshot/headless coverage for MM9 maps with enclosed spaces, sky openings, static lights, and dynamic effects.
