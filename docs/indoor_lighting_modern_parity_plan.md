# Indoor Lighting Modern Parity Plan

This document defines the implementation plan for indoor lighting parity with OpenEnroth behavior, adapted to
OpenYAMM's bgfx renderer and shared FX architecture.

This is a future implementation plan. It does not replace the current active refactor loop unless explicitly promoted
into `PLAN.md`, `ACCEPTANCE.md`, `TASK_QUEUE.md`, and `PROGRESS.md`.

## Goals

- Make indoor maps visually dark by default, using authored BLV/DLV sector ambient data.
- Render authored BLV lights and decoration light emitters on indoor geometry.
- Make the Torch spell illuminate indoor geometry and billboards.
- Make spell/projectile FX lights illuminate indoor geometry where practical.
- Apply the same lighting model to indoor actors, decorations, items, and other billboards.
- Keep the implementation simple, readable, and performance-bounded.
- Avoid fake parity through one-off indoor hacks.

## Non-Goals

- Do not copy OpenEnroth code.
- Do not implement a deferred renderer or shadow maps for this feature.
- Do not infer indoor torch/campfire lights from names if BLV/DLV data already provides authored lights.
- Do not create separate gameplay Torch spell behavior for indoor and outdoor.
- Do not add callback-heavy lighting adapters between gameplay and indoor rendering.
- Do not move world-geometry lighting into shared gameplay. Indoor lighting is world presentation, not gameplay rules.

## OpenEnroth Behavioral Reference

OpenEnroth uses a layered indoor lighting model:

- `BLVLight` records store position, radius, RGB color, type, attributes, and brightness.
- `BLVSector::lightIds` maps sectors to authored BLV lights.
- `BLVSector::minAmbientLightLevel` controls sector ambient darkness.
- Light attribute bit `0x08` disables face lighting for that BLV light.
- Event `SetLight` toggles that bit on BLV light records.
- Decoration descriptors with `uLightRadius` also push stationary lights, using colored or white light depending on the
  colored-lights setting.
- The Torch spell creates a mobile light at the party/camera position. Its radius is based on the Torchlight config and
  multiplied by buff power, with optional flicker.
- Spell/projectile effects can add mobile lights.
- Indoor BSP rendering uses a dedicated shader path and submits point lights to that shader.
- Indoor billboards get a dimming/light level from sector ambient plus nearby lights.

Relevant OE files for reference only:

- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.h`
- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp`
- `reference/OpenEnroth-git/src/Engine/Graphics/LightmapBuilder.cpp`
- `reference/OpenEnroth-git/src/Engine/Graphics/LightsStack.*`
- `reference/OpenEnroth-git/src/Engine/Graphics/Renderer/OpenGLRenderer.cpp`
- `reference/OpenEnroth-git/src/Engine/Engine.cpp`
- `reference/OpenEnroth-git/src/Engine/SpellFxRenderer.cpp`

## Current OpenYAMM State

OpenYAMM already has some required data:

- `game/indoor/IndoorMapData.h` has `IndoorLight`, sector `lightIds`, and `minAmbientLightLevel`.
- `game/indoor/IndoorMapData.cpp` parses light records and sector light membership.
- `game/events/EventRuntimeState` stores `indoorLightsEnabled` from `SetLight`.
- `game/fx/WorldFxSystem` owns shared dynamic light emitters for spell/projectile FX.
- Outdoor has a bounded FX light uniform path using `u_fxLightPositions`, `u_fxLightColors`, and `u_fxLightParams`.
- Indoor currently initializes `WorldFxSystem` and renders particles, but indoor geometry does not consume FX lights.

Main deltas:

- Indoor geometry uses the generic bgfx sample textured shader, not an indoor lit shader.
- Indoor ambient is not derived from sector `minAmbientLightLevel`.
- Parsed BLV lights do not affect indoor geometry.
- `SetLight` state is stored but not applied visually.
- Decoration descriptor light radii do not contribute to indoor lighting.
- Torchlight buff does not create an indoor geometry light.
- Indoor billboards are effectively full-bright or simple ambient, not OE-style sector/light sampled.

## Target Architecture

The target should be straightforward:

```cpp
IndoorRenderer::render(...)
{
    IndoorLightingFrame lighting = m_indoorLightingRuntime.buildFrame(
        mapData,
        eventRuntimeState,
        worldFxSystem,
        partyState,
        cameraState,
        visibleSectorMask,
        settings,
        elapsedTime);

    submitIndoorGeometry(lighting);
    submitIndoorBillboards(lighting);
    submitIndoorParticles();
}
```

The ownership is:

- `IndoorRenderer` owns render resources and submits bgfx draw calls.
- `IndoorLightingRuntime` owns indoor light selection, ambient calculation, and cached light uniforms.
- `IndoorMapData` remains the parsed BLV/DLV source of truth.
- `WorldFxSystem` remains the shared source of dynamic spell/projectile FX lights.
- `Party` remains the shared source of Torchlight buff state.
- `GameSettings` controls colored lights and shadows, but does not own light selection.

No gameplay controller should decide indoor render lighting.

## Shared Data Shapes

Keep this coarse and readable.

```cpp
struct IndoorRenderLight
{
    bx::Vec3 position = {};
    float radius = 0.0f;
    uint32_t colorAbgr = 0xffffffff;
    float intensity = 1.0f;
    IndoorRenderLightKind kind = IndoorRenderLightKind::Static;
};

struct IndoorLightingFrame
{
    float ambient = 1.0f;
    std::vector<IndoorRenderLight> lights;
};
```

Do not create many `Decision`, `Patch`, `Command`, or `Effect` micro-structs for this. The renderer needs an ambient
value and a bounded list of lights.

## Light Sources

### 1. BLV Authored Lights

For each visible or relevant sector:

- read `sector.lightIds`;
- resolve `IndoorMapData::lights[lightId]`;
- skip invalid light ids;
- skip lights disabled by runtime state;
- skip lights with no radius;
- respect the `0x08` no-face-light attribute;
- use BLV RGB if colored lights are enabled;
- use white or grayscale if colored lights are disabled;
- preserve radius and position from the map data.

Runtime light override semantics:

- If `indoorLightsEnabled` has no entry for a light id, use the map-authored attribute state.
- If override is `true`, force light enabled for face/geometry lighting.
- If override is `false`, force light disabled for face/geometry lighting.

This mirrors OE's `SetLight` behavior without mutating immutable map data.

### 2. Decoration Descriptor Lights

Indoor decorations should contribute stationary lights when their descriptor or sprite frame declares a light radius.

Rules:

- Use decoration descriptor `uLightRadius` or sprite frame glow radius if available in our loaded decoration data.
- Use the decoration position plus a sensible vertical offset, matching visual sprite height.
- Skip invisible or hidden decorations.
- Use colored decoration light when `settings.coloredLights` is true.
- Use white when colored lights are disabled.

This should be data-driven from decoration tables, not name heuristics.

### 3. Party Torchlight

Torchlight should be a mobile light at the camera or party eye position.

Rules:

- Active when `PartyBuffId::TorchLight` is active.
- Radius should derive from the same shared spell/buff power used by the party spell system.
- Include optional flicker only if we already have or intentionally add a setting for it.
- Give Torchlight priority in the selected-light list.
- Use neutral gray/white for OE-like behavior; optionally apply a subtle warm tint only if modern parity wants it and it
  is behind the colored-lights setting.

This should not be a new spell effect. It is a render-time light emitted from existing party buff state.

### 4. Spell And Projectile FX Lights

`WorldFxSystem::lightEmitters()` should feed indoor geometry lights.

Rules:

- Dynamic FX lights are selected after Torchlight and high-priority static lights.
- Reuse existing emitter radius/color/intensity.
- Do not duplicate projectile/spell rules in indoor renderer.
- If an impact/trail already creates a `WorldFxLightEmitter`, indoor lighting should simply consume it.

### 5. Future Scene YAML Lights

When BLV/DLV is converted to `.scene.yml`, preserve the same data model:

- authored point lights;
- sector/room membership or explicit visibility grouping;
- enabled/disabled event state;
- radius, color, type, brightness.

Do not design this feature around scene YAML first. BLV/DLV parity comes first.

## Ambient / Darkness

Initial implementation:

- Determine current party sector and visible sectors.
- Compute a single frame ambient from those sectors' `minAmbientLightLevel`.
- Start with OE-style mapping:

```cpp
ambient = (248.0f - float(minAmbientLevel << 3)) / 255.0f;
ambient = clamp(ambient, IndoorAmbientMin, IndoorAmbientMax);
```

Important: OE's OpenGL path appears to use the max `minAmbientLightLevel` across sectors for its current global
ambient. For OpenYAMM, current/visible-sector ambient is likely better visually and more correct for modern rendering,
but this should be tested against real maps.

Later refinement:

- Store ambient per face batch or per sector batch.
- Use the face's owning sector ambient when drawing geometry.
- Use billboard sector ambient for actors/items/decors.

Do not block initial parity on per-face ambient unless the global ambient looks obviously wrong.

## Shader Plan

Add dedicated indoor lit shaders instead of using bgfx sample textured shaders:

- `game/shaders/vs_indoor_textured_lit.sc`
- `game/shaders/fs_indoor_textured_lit.sc`

Uniforms should be simple and parallel to outdoor FX lighting:

- `u_indoorLightPositions[MAX_INDOOR_LIGHTS]`: xyz position, radius;
- `u_indoorLightColors[MAX_INDOOR_LIGHTS]`: rgb color, intensity;
- `u_indoorLightParams`: light count, ambient, light scale, reserved.

Recommended first limit:

- `MAX_INDOOR_LIGHTS = 16` or `24`.

OE's OpenGL path submits up to 40 indoor point lights, but a smaller ranked list should be enough initially and cheaper.
If maps visibly need more, raise it after profiling.

Lighting formula:

- Start with ambient.
- Add point lights with smooth distance attenuation.
- Clamp final lighting to a sane range.
- Do not add normals/specular complexity unless needed. MM indoor lighting is mostly radial brightness, not physically
  correct lighting.

The shader should operate on world position. If current indoor vertices do not pass world position, extend the vertex
layout or shader varying explicitly.

## Billboard Lighting

Indoor actors, decorations, items, and sprite objects should not remain full-bright.

Initial implementation:

- Compute a CPU-side light sample at each billboard world position.
- Use the billboard sector ambient plus nearby selected lights.
- Feed this as `u_billboardAmbient` or per-vertex color.
- Keep outline/hover rendering unaffected.

Rules:

- `BILLBOARD_LIT`-equivalent assets should remain full-bright if we have that flag available.
- Actors/items/decors should use their own sector when known.
- If sector is unknown, fall back to current ambient rather than black.

This is closer to OE's `FindBillboardsLightLevels_BLV` behavior and avoids requiring many shader lights on billboard
draws immediately.

Later refinement:

- Use the same selected light list in the billboard shader for dynamic per-pixel lighting if the CPU sample is not good
  enough.

## Light Selection And Caching

Light selection must be bounded.

Per lighting refresh:

1. Add Torchlight first if active.
2. Add dynamic FX lights near/in front of the camera.
3. Collect BLV lights from visible sectors and current-sector bounding box overlap.
4. Collect visible decoration lights.
5. Rank candidates by contribution:

```cpp
score = intensity * radius / max(distanceToCamera, 1.0f);
```

6. Keep the top `MAX_INDOOR_LIGHTS`.

Refresh cadence:

- Static light candidate caches can be rebuilt on map load, sector reveal/visibility changes, and `SetLight`.
- Dynamic selected uniforms can refresh at 60 Hz, matching outdoor FX light uniform cadence.
- Torch flicker, if implemented, should also update at this cadence.

Do not rebuild all light candidates every draw call.

## Event And Save Integration

`SetLight` already writes to `EventRuntimeState::indoorLightsEnabled`.

Implementation should:

- consume that map in `IndoorLightingRuntime`;
- preserve existing save/load behavior;
- not mutate `IndoorMapData::lights`;
- invalidate static light cache when a light override changes.

If there is no explicit invalidation signal yet, start with cheap refresh-on-frame for the small override map, then add
cache invalidation once correctness is proven.

## Settings

Existing setting:

- `settings.coloredLights`

Behavior:

- `true`: use authored RGB colors for BLV and decoration lights.
- `false`: convert lights to white/grayscale while preserving radius/intensity.

Existing shadow setting:

- `settings.shadowsEnabled`

Behavior:

- Should not disable lighting.
- Should only affect contact shadows or future shadow-like FX.

No new setting is required for the first lighting parity pass.

## Implementation Steps

### Step 1 - Data Audit And Tests

- Add unit tests for BLV light enable/disable resolution:
  - default enabled light;
  - default disabled light via attribute `0x08`;
  - runtime override enabling a disabled light;
  - runtime override disabling an enabled light.
- Add unit tests for ambient mapping from `minAmbientLightLevel`.
- Add unit tests for light ranking and max-light truncation.

### Step 2 - Indoor Lighting Runtime

Add:

- `game/indoor/IndoorLightingRuntime.h`
- `game/indoor/IndoorLightingRuntime.cpp`

Responsibilities:

- build `IndoorLightingFrame`;
- resolve BLV light enabled state;
- collect current/visible sector BLV lights;
- collect Torchlight;
- collect `WorldFxSystem` light emitters;
- rank and truncate lights;
- compute frame ambient.

Keep public API small:

```cpp
IndoorLightingFrame buildFrame(const IndoorLightingFrameInput &input);
```

If `IndoorLightingFrameInput` grows too large, prefer grouping existing state references by domain, not adding many
micro-types.

### Step 3 - Indoor Shader Resources

- Add indoor lit shaders.
- Add shader compilation entries if required by CMake/runtime shader setup.
- Add uniform handles to `IndoorRenderer`.
- Replace indoor geometry program from `vs_shadowmaps_texture/fs_shadowmaps_texture` to the new indoor lit shader.
- Submit lighting uniforms before indoor geometry batches.

### Step 4 - BLV Lights On Geometry

- Feed `IndoorLightingFrame` lights to shader uniforms.
- Validate on a BLV with authored lights.
- Validate `SetLight` events visibly toggle light contribution.
- Confirm colored-lights setting changes RGB vs white light behavior.

### Step 5 - Indoor Darkness

- Apply frame ambient from `minAmbientLightLevel`.
- Tune minimum ambient so the scene is dark but playable.
- Compare against OE on:
  - dark dungeon with no Torch;
  - same dungeon with Torch;
  - room with authored lights;
  - room with disabled/toggled lights.

### Step 6 - Decoration Lights

- Add decoration descriptor light extraction.
- Skip invisible/hidden decorations.
- Cache static decoration lights on indoor load or map state changes.
- Verify torches/campfires/pedestals emit light without name heuristics.

### Step 7 - Torchlight

- Add Torch mobile light from party buff state.
- Match radius scaling to spell power.
- Add optional flicker only if existing settings or gameplay data support it cleanly.
- Ensure Torchlight affects geometry and billboards.

### Step 8 - Dynamic FX Lights

- Feed `WorldFxSystem::lightEmitters()` to indoor lighting frame.
- Verify projectile trails and impact effects visibly illuminate indoor walls/floors.
- Ensure this does not duplicate projectile or particle code.

### Step 9 - Billboard Light Sampling

- Add CPU light sampling helper in `IndoorLightingRuntime`.
- Apply sampled ambient/light intensity to:
  - actor billboards;
  - decoration billboards;
  - world item billboards;
  - projectile billboards, unless intentionally full-bright.
- Keep hover outlines and selection outlines visually readable.

### Step 10 - Performance Pass

Profile on `blv18` and at least one light-heavy dungeon.

Acceptance targets:

- no per-frame full-map light scan if visible sector/light cache is available;
- light uniform refresh no faster than 60 Hz unless needed;
- no measurable overhead when no lights are visible beyond shader cost;
- no large CPU cost in billboard light sampling.

If needed:

- cache static light candidates by sector;
- cache billboard light sample for static decorations;
- only resample actors/items when they move or lighting changes.

## Validation Matrix

Required manual checks:

- Indoor map with no Torch is visibly darker than current.
- Torch spell brightens nearby walls, floors, actors, and items.
- Torchlight follows the party.
- Colored-lights setting affects authored colored lights.
- `SetLight` event toggles visible light contribution.
- Fire/torch decorations emit light if their descriptor has a light radius.
- Projectiles/impacts with FX light emitters illuminate indoor geometry.
- Actors/items do not look full-bright in dark rooms.
- Hover outlines remain visible.
- FPS in `blv18` stays within expected release-build range.

Required automated checks:

- unit tests for light enabled-state resolution;
- unit tests for ambient mapping;
- unit tests for light ranking/truncation;
- unit tests for Torchlight radius calculation if extracted into a pure helper;
- targeted headless diagnostic for `SetLight` state persistence if practical.

## Acceptance Criteria

- Indoor renderer uses an indoor lit shader for geometry.
- BLV authored lights affect indoor geometry.
- Decoration descriptor lights affect indoor geometry.
- Torch spell affects indoor geometry and billboards.
- Indoor ambient/darkness comes from sector `minAmbientLightLevel`.
- Event `SetLight` state affects rendered lights.
- Dynamic `WorldFxSystem` light emitters affect indoor geometry.
- Indoor actors/items/decorations receive lighting/dimming consistent with their sector and nearby lights.
- Implementation is bounded and readable, with no callback-heavy adapter layer.
- Outdoor lighting behavior is unchanged except for shared helper extraction if explicitly needed.

## Risks

- OE has multiple light paths: legacy lightmap-style dimming, stationary/mobile stacks, and the newer OpenGL shader path.
  The modern OpenYAMM implementation should match visual behavior, not reproduce every internal path.
- Global ambient from visible sectors may differ from OE's current max-across-map shader behavior. Prefer visual parity
  and test real maps before overfitting to one code path.
- Billboard lighting can become CPU-heavy if sampled naively for every billboard every frame.
- Too many shader lights can hurt GPU performance. Start bounded and raise only with profiling evidence.
- Decoration light data may not be loaded in the exact shape needed yet; if missing, extend data loading rather than
  adding name heuristics.

## Recommended First Slice

The first implementation slice should be:

1. Add `IndoorLightingRuntime` with pure tests for ambient, light enabled state, and light ranking.
2. Build an `IndoorLightingFrame` containing Torchlight, BLV lights, and `WorldFxSystem` lights.
3. Do not touch shaders yet except for plumbing if needed.

This gives a safe, testable foundation before changing visual output.
