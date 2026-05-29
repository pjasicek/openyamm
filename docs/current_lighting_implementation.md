# Current Lighting Implementation

This document describes the current OpenYAMM indoor and outdoor lighting implementation as of May 21, 2026. It is meant
as a technical handoff for analysis and redesign proposals, especially for scenarios with many simultaneous dynamic
lights such as 60 Sparks projectiles plus authored indoor lights plus projectile impacts.

The short version: OpenYAMM currently uses forward-style point lighting through fixed-size bgfx uniform arrays. Indoor
has a more advanced per-draw light selection path with a 12-light shader budget. Outdoor has a simpler global FX-light
selection path with an 8-light shader budget for all terrain and BModel geometry. Billboards are mostly ambient sampled
on CPU and do not use full per-pixel dynamic lights.

## Main Files

- `game/indoor/IndoorLightingRuntime.h`
- `game/indoor/IndoorLightingRuntime.cpp`
- `game/indoor/IndoorRenderer.cpp`
- `game/outdoor/OutdoorRenderer.cpp`
- `game/outdoor/OutdoorBillboardRenderer.cpp`
- `game/outdoor/OutdoorSpatialFxRuntime.cpp`
- `game/fx/WorldFxSystem.h`
- `game/fx/WorldFxSystem.cpp`
- `game/gameplay/GameplayTorchLight.h`
- `game/shaders/fs_indoor_textured_lit.sc`
- `game/shaders/vs_indoor_textured_lit.sc`
- `game/shaders/fs_outdoor_textured_fog.sc`
- `game/shaders/vs_outdoor_textured_fog.sc`
- `game/shaders/fs_outdoor_billboard_lit.sc`
- `game/shaders/vs_outdoor_billboard_lit.sc`

## Light Source Model

### Shared FX Lights

`WorldFxSystem` owns transient render FX state:

```cpp
struct WorldFxLightEmitter
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float radius = 0.0f;
    uint32_t colorAbgr = 0xffffffffu;
    int16_t sectorId = -1;
};
```

Lights are appended with `WorldFxSystem::addLightEmitter(...)`. There is no hard cap at insertion time. The cap is
applied later by the renderer when packing shader uniforms.

Current shared FX light producers include:

- active projectiles, from `WorldFxSystem::syncProjectileTrails`;
- projectile impacts, via `PersistentImpactLight` in `WorldFxSystem`;
- outdoor party Torchlight, from `OutdoorSpatialFxRuntime::syncPartyTorchLight`;
- outdoor actors with sprite glow radius;
- outdoor decorations with descriptor light radius or sprite glow radius;
- outdoor sprite objects with glow radius;
- indoor party Torchlight, produced by `IndoorLightingRuntime::buildFrame`;
- indoor FX projectiles/impacts, consumed from `WorldFxSystem::lightEmitters()`;
- indoor static/decoration lights, built from indoor map data and decoration data.

Particles themselves are not lights. For example, a Sparks visual can spawn many particles, but lighting comes from
projectile and impact emitters, not from each particle. If 60 Sparks projectiles exist simultaneously, they can create
up to roughly one dynamic light emitter per active projectile during a spatial refresh, before renderer-side selection.

### Torchlight

Torchlight is shared in `GameplayTorchLight.h`:

```cpp
inline float gameplayTorchLightBaseRadius(bool outdoor)
{
    return outdoor ? 1024.0f : 800.0f;
}

inline std::optional<GameplayTorchLight> resolveGameplayTorchLight(
    const Party &party,
    bool outdoor,
    bool outdoorNight)
```

Outdoor Torchlight is suppressed during daytime. Indoor Torchlight is always active while the buff exists. Radius is
`baseRadius * buffPower`. Indoor multiplies Torchlight intensity by `1.5`.

## Indoor Lighting

### Data Flow

Indoor lighting is centralized in `IndoorLightingRuntime`.

Each render frame, `IndoorRenderer::render` does:

1. Build the visible sector mask and portal-clipped sector frustums.
2. Build an `IndoorLightingFrame`.
3. Select a default light set at the camera.
4. For every visible textured geometry batch, select a batch-local light set.
5. Submit the geometry with `u_indoorLightPositions`, `u_indoorLightColors`, and `u_indoorLightParams`.
6. Render billboards using CPU-sampled ambient/light contribution, not full per-pixel shader light arrays.

Important shape:

```cpp
static constexpr size_t MaxIndoorDrawLights = 12;

struct IndoorLightingFrame
{
    float ambient = 1.0f;
    std::vector<IndoorRenderLight> lights;
    std::vector<std::vector<uint32_t>> lightIndicesBySector;
    std::vector<uint32_t> globalLightIndices;
    std::vector<uint32_t> fxLightIndices;
};

struct IndoorDrawLightSet
{
    std::array<float, MaxIndoorDrawLights * 4> positions = {};
    std::array<float, MaxIndoorDrawLights * 4> colors = {};
    std::array<float, 4> params = {};
    size_t lightCount = 0;
};
```

The frame can contain more than 12 lights. Only each draw call's shader light set is capped to 12.

### Indoor Static Cache

`IndoorLightingRuntime::rebuildStaticCache` builds a cache for:

- BLV/DLV authored lights referenced by each sector's `lightIds`;
- decoration lights from `DecorationEntry::lightRadius`;
- sprite-frame glow radii from `SpriteFrameEntry::glowRadius`.

The cache stores source position, radius, color, sector id, kind, attributes, and runtime keys. It is rebuilt when the
indoor renderer initializes or clears render assets. This avoids re-scanning all static lights and decoration metadata
from scratch every frame.

Runtime filtering is still applied every frame:

- `EventRuntimeState::indoorLightsEnabled` can force a BLV light on/off.
- Decoration sprite overrides can hide a decoration light.
- Consumable/interactive decorations can hide light when their decor var reaches the cleared state.
- Visible sector mask and portal frustum tests cull static lights.

### Indoor Ambient

Ambient is derived from the highest visible sector `minAmbientLightLevel`:

```cpp
const int clampedLevel = std::clamp(minAmbientLightLevel, 0, 31);
const float ambient = (248.0f - static_cast<float>(clampedLevel << 3)) / 255.0f;
return std::clamp(ambient, 0.18f, 1.0f);
```

This is a single frame-wide ambient value, not per-sector ambient in the shader. Billboards sample from the same
`IndoorLightingFrame`.

### Indoor Light Selection

Geometry batches call:

```cpp
IndoorLightingRuntime::selectDrawLightSetForBounds(
    lightingFrame,
    eye,
    viewForward,
    batch.sectorId,
    batch.backSectorId,
    bounds);
```

Candidate lights include:

- global lights, such as Torchlight;
- lights from the batch sector;
- lights from the back sector for portal/two-sided faces;
- FX lights from other sectors if their sphere touches the batch bounds.

Candidates are scored by:

- whether the light affects the reference point;
- whether it matches the sector/back-sector;
- whether it is in front of the view direction;
- radius, intensity, and distance;
- kind weight: FX `12`, Torch `10`, Decoration `4`, Static `1`.

There is also a reservation step:

```cpp
constexpr size_t ReservedNonFxDetailLights = 4;
```

Up to four high-ranked non-FX lights are selected first, then the remaining slots are filled by all ranked lights. This
is meant to stop a burst of FX lights from completely evicting important static/detail lights.

Lights that touch the batch but do not fit into the 12 shader slots are folded into an approximate ambient tail:

- non-FX tail scale: `0.28`;
- FX tail scale: `0.10`;
- tail contribution clamp: `0.45` per RGB channel.

This is a useful visual fallback, but it is not the same as shading all omitted lights spatially.

### Indoor Shader

The indoor geometry shader is `fs_indoor_textured_lit.sc`.

Current lighting loop:

```glsl
uniform vec4 u_indoorLightPositions[12];
uniform vec4 u_indoorLightColors[12];
uniform vec4 u_indoorLightParams;

vec3 getIndoorLighting(vec3 worldPosition)
{
    vec3 lighting = u_indoorLightParams.yzw;

    for (int i = 0; i < 12; ++i)
    {
        if (float(i) >= u_indoorLightParams.x)
        {
            break;
        }

        vec3 toLight = u_indoorLightPositions[i].xyz - worldPosition;
        float radius = max(u_indoorLightPositions[i].w, 1.0);
        float distanceSquared = dot(toLight, toLight);
        float inverseRadiusSquared = 1.0 / (radius * radius);
        float attenuation = 1.0 - clamp(distanceSquared * inverseRadiusSquared, 0.0, 1.0);
        attenuation *= attenuation;
        lighting += u_indoorLightColors[i].rgb * (u_indoorLightColors[i].w * attenuation);
    }

    return clamp(lighting, vec3(0.0, 0.0, 0.0), vec3(2.0, 2.0, 2.0));
}
```

This is unshadowed, normal-free radial brightness. It does not use surface normals, light direction, specular, normal
maps, shadow maps, or light cookies. Final light is clamped to 2.0.

### Indoor Billboards

Indoor billboards use `fs_outdoor_billboard_lit.sc`, but their lighting uniform is computed on CPU:

```cpp
IndoorLightingRuntime::sampleLightingRgbForSectors(lightingFrame, position, sectorId)
```

If a sprite frame has `SpriteFrameFlag::Lit`, it is rendered full-bright with ambient `1.0`. Otherwise the CPU samples
ambient plus nearby lights at a single point, usually the billboard center. This means:

- actors/items/decorations do not receive per-pixel point-light falloff across their sprite;
- large billboards can look uniformly lit even if only one side is near a light;
- sampling cost is CPU-side and grows with relevant sector/global lights.

### Indoor Current Limits

- Maximum shader lights per indoor geometry draw: `12`.
- Maximum indoor light frame size: no explicit cap, limited by visible static lights plus FX emitters.
- Static cache inline candidate capacity: `128`, with vector overflow after that.
- Tail approximation softens dropped lights but loses spatial detail.
- Ambient is frame-wide, not per-sector in shader.
- Billboard lighting is single-point CPU sampled.
- No occlusion within a sector: lights can affect through local walls unless sector/frustum/bounds filtering excludes them.
- FX lights can cross sector portals only by the batch-bounds overlap path; this is approximate.
- Static lights are sector-scoped, which is cheap, but not physically robust for complex portal visibility.

### Indoor Performance Hogs

Likely hot spots when many dynamic lights exist:

- Per-frame construction of `IndoorLightingFrame`, especially copying/appending many FX lights.
- Per-batch `selectDrawLightSetForBounds`, because every visible textured batch ranks candidate lights.
- Candidate gathering for FX lights in other sectors when bounds are valid.
- CPU sampling for every billboard.
- Uniform updates per visible textured batch: positions array, colors array, and params.
- Fragment shader cost: every lit geometry pixel loops over up to 12 lights.

The renderer already records `renderLightingNanoseconds` when `settings.performanceTrace` is enabled. This only captures
frame building/default selection, not necessarily all per-batch light selection work inside textured submission.

## Outdoor Lighting

### Data Flow

Outdoor dynamic lighting is simpler than indoor:

1. `OutdoorSpatialFxRuntime::beginFrame` refreshes spatial FX at 60 Hz.
2. On refresh it clears `WorldFxSystem` spatial FX and appends current emitters.
3. `WorldFxSystem::syncProjectileFx` also appends projectile trail and impact lights.
4. `OutdoorRenderer::applyOutdoorFxLightUniforms` globally ranks all current emitters.
5. It packs the top eight lights into shader uniforms.
6. Terrain, BModels, and blood splats use those same eight lights.
7. Outdoor billboards do not currently receive those dynamic lights.

Important constants:

```cpp
constexpr size_t MaxOutdoorFxLights = 8;
constexpr float OutdoorFxLightRefreshIntervalSeconds = 1.0f / 60.0f;
constexpr float OutdoorFxLightingAmbient = 1.0f;
constexpr float OutdoorFxLightingScale = 1.6f;
```

Outdoor uniform arrays are also declared as eight in `OutdoorGameView`.

### Outdoor Emitter Producers

`OutdoorSpatialFxRuntime` appends:

- party Torchlight at camera target when outdoors and night;
- actor contact shadows and actor glow-radius lights;
- decoration lights, with decoration light radius doubled for readability;
- decoration fire/smoke particles;
- sprite object lights/glow billboards.

`WorldFxSystem` appends:

- projectile trail lights when `refreshSpatialFx` is true;
- persistent impact lights with fade;
- projectile glow billboards.

Decoration emitters are pulsed for fire/magic styles by changing radius and alpha each refresh.

### Outdoor Light Selection

Outdoor selection is global, not per draw region:

```cpp
const float score = (light.radius * intensity) / std::max(distance, 64.0f);
```

The renderer sorts every emitter by this score relative to the camera position, then takes the first eight. It does not
consider:

- terrain tile or BModel bounds;
- screen-space coverage;
- whether a light affects the current draw;
- occlusion by world geometry;
- sector/portal relationships;
- whether a projectile light is more important than a decoration light.

The selected eight lights are cached and refreshed at 60 Hz.

### Outdoor Shader

The outdoor geometry shader is `fs_outdoor_textured_fog.sc`.

Current lighting loop:

```glsl
uniform vec4 u_fxLightPositions[8];
uniform vec4 u_fxLightColors[8];
uniform vec4 u_fxLightParams;

vec3 getFxLighting(vec3 worldPosition)
{
    vec3 lighting = vec3(u_fxLightParams.y, u_fxLightParams.y, u_fxLightParams.y);

    for (int i = 0; i < 8; ++i)
    {
        if (float(i) >= u_fxLightParams.x)
        {
            continue;
        }

        vec3 toLight = u_fxLightPositions[i].xyz - worldPosition;
        float radius = max(u_fxLightPositions[i].w, 1.0);
        float dist = length(toLight);
        float attenuation = 1.0 - safeSmoothstep(0.0, radius, dist);
        lighting += u_fxLightColors[i].rgb * (u_fxLightColors[i].w * attenuation * u_fxLightParams.z);
    }

    return clamp(lighting, vec3(0.0, 0.0, 0.0), vec3(2.0, 2.0, 2.0));
}
```

Again, this is unshadowed radial brightness with no normals. It uses `length`, which is more expensive than the indoor
squared-distance attenuation loop.

### Outdoor Billboards

Outdoor billboards use ambient-only lighting today:

```cpp
uint32_t OutdoorBillboardRenderer::computeBillboardLightContributionAbgr(
    const OutdoorGameView &view,
    float x,
    float y,
    float z)
{
    // Billboard lighting is intentionally ambient-only for now.
    // Terrain and textured bmodels still receive the shader-backed FX light contribution.
    return 0xff000000u;
}
```

`BillboardAmbientLight` is `0.85`. `BillboardLightContributionScale` exists but is effectively unused because the
contribution function returns black. This means outdoor actors, items, projectiles, decorations, and glow billboards do
not get dynamic point-light shading. Only terrain/BModels/blood splats receive the eight FX lights.

### Outdoor Current Limits

- Maximum shader lights for all outdoor geometry: `8`.
- Selection is global for the camera, not local to a terrain chunk or BModel.
- No explicit cap on emitter count before sorting.
- No spatial acceleration for light ranking; all emitters are scanned and sorted.
- Billboards are ambient-only.
- Outdoor ambient is fixed at `1.0` for textured geometry before FX contribution.
- No real day/night darkening in the FX light baseline path beyond fog/atmosphere systems.
- No occlusion or shadows for lights.
- Decoration light sync loops over all outdoor decoration billboards on each spatial refresh.

### Outdoor Performance Hogs

Likely hot spots:

- Sorting all `WorldFxLightEmitter`s every uniform refresh.
- Applying the same eight-light shader loop to every visible terrain/BModel pixel even when a given light is nowhere
  near most of the geometry.
- Repeated uniform application for terrain and each BModel draw.
- Outdoor decoration emitter scan every 1/60 second.
- Fragment shader `length` per light per pixel.
- Particle/weather systems are separate but can compete for frame time; snow prewarm and heavy weather are large particle
  producers, although not lighting-specific.

## 60 Sparks + 20 Indoor Lights Scenario

Current behavior for a burst-heavy indoor scenario:

- If 60 active projectiles each produce a glow light, `WorldFxSystem::lightEmitters()` can hold roughly 60 FX lights.
- `IndoorLightingFrame` can include all visible/projected FX lights plus static/decoration/Torch lights.
- Each geometry batch selects only 12 lights for shader detail.
- Up to four non-FX lights are reserved before FX fills remaining slots.
- Dropped touching lights contribute only a weak ambient tail.
- Billboards sample CPU lighting at one point; they do not get the same 12 per-pixel shader lights.

This means the scene should not explode purely from a hard insert cap, but the visual result is approximate and the CPU
selection cost can rise with dynamic-light count and visible batch count. Many FX lights near the camera can also cause
visible popping as lights enter/leave the selected 12.

Current behavior for the same scenario outdoors:

- All active projectile, impact, Torch, actor, decoration, and sprite-object lights are globally ranked.
- Only eight lights affect all terrain/BModels.
- Billboards remain ambient-only.
- With 60 projectile lights, most lights are dropped completely from terrain/BModel shading.

Outdoor is therefore not suitable for visually faithful tens-of-dynamic-lights scenarios in its current form.

## Known Architectural Limitations

- This is forward lighting with fixed uniform arrays. It cannot scale to many visible lights without either dropping
  lights or increasing per-pixel loop cost.
- There is no tiled/clustered/forward+ light list.
- There is no deferred light accumulation pass.
- There is no light volume rendering path.
- There is no GPU-side light culling.
- There is no spatial light grid for CPU selection.
- There is no light occlusion, shadow maps, portal-aware shadowing, or depth-aware light clipping.
- There are no normals in the current world geometry lighting model, so lights are radial brightness overlays, not
  directional illumination.
- Billboards and geometry use different lighting paths, causing visual mismatch.
- Indoor and outdoor share `WorldFxSystem` emitters but have very different renderer-side selection.
- Outdoor global top-eight selection is the most severe many-light bottleneck.

## Things A Redesign Should Consider

The current need is to support tens of dynamic lights with little to no extra performance cost. The current design cannot
do this by just raising `MaxIndoorDrawLights` or `MaxOutdoorFxLights`; that would directly increase fragment shader cost
and uniform bandwidth.

Candidate redesign directions to evaluate:

- Forward+ or clustered forward lighting with a light grid/list built per screen tile or depth cluster.
- CPU spatial bins per indoor sector and outdoor world cell, with per-draw local lists.
- Separate cheap additive light-volume pass for dynamic FX lights.
- Low-resolution light buffer for FX lights, upsampled/composited into world rendering.
- Deferred or mini-deferred light accumulation only for world geometry, if bgfx backend constraints are acceptable.
- Keep static authored indoor lights in current per-batch path, but move high-count dynamic FX lights to a separate pass.
- Treat projectile bursts as aggregate area/glow fields instead of one point light per projectile when many are close.
- Add a light importance policy by source kind, screen-space size, and contribution, not only camera distance.
- Make outdoor selection local to terrain chunks/BModels instead of global top eight.
- Bring billboard lighting into the same system or explicitly design a cheaper matched approximation.

## Minimal Metrics To Gather Before Rehaul

Useful instrumentation:

- Number of `WorldFxLightEmitter`s per frame.
- Indoor: number of lights in `IndoorLightingFrame`.
- Indoor: candidate count and selected count per textured batch.
- Indoor: visible textured batch count and total candidate evaluations.
- Outdoor: emitter count before ranking and selected count after ranking.
- Outdoor: number of terrain/BModel pixels is hard to know directly, but draw counts and visible geometry counts help.
- Time spent in light frame build, per-batch selection, and outdoor ranking separately.
- Visual stress scenes:
  - 60 Sparks projectiles indoors with 20 static lights.
  - 60 Sparks projectiles outdoors near the party.
  - decoration-heavy outdoor town at night.
  - dense indoor dungeon with many visible sectors through portals.

Current indoor `performanceTrace` already tracks `renderLightingNanoseconds`, but it should be split so batch light
selection and billboard CPU sampling are visible separately.
