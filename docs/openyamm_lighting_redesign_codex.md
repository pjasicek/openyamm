# OpenYAMM Lighting Redesign Implementation Plan

Date: 2026-05-21

Audience: Codex or another implementation agent working in this repository.

Scope: make OpenYAMM lighting scale to many dynamic FX lights while keeping the current bgfx forward renderer simple.
The target stress case is roughly 60 Sparks/projectile lights, 20 authored indoor lights, Torchlight, decoration lights,
and projectile impacts without severe CPU spikes or obvious light popping.

Read this together with `docs/current_lighting_implementation.md`, which documents the active implementation.

## 1. Current Facts

Do not rediscover these from scratch unless the code changed.

- Indoor geometry uses `IndoorLightingRuntime` and shader uniform arrays with `MaxIndoorDrawLights == 12`.
- Indoor can keep many visible lights in `IndoorLightingFrame`, but each geometry draw shades only 12.
- Indoor selection is per draw/batch and already has a weak omitted-light ambient tail.
- Indoor static lights are cached from BLV lights and decoration/glow metadata.
- Indoor FX lights come from `WorldFxSystem::lightEmitters()`.
- Indoor billboards use CPU-sampled lighting at one point.
- Outdoor geometry uses one global top-8 FX light list for terrain, BModels, and blood splats.
- Outdoor terrain is currently submitted as a large terrain draw, not as lighting-local chunks.
- Outdoor billboards are ambient-only. `computeBillboardLightContributionAbgr` currently returns black.
- Lights are unshadowed radial brightness. There are no normals, specular, cookies, shadow maps, deferred lighting,
  Forward+, clustered forward lighting, or GPU light culling.
- Particles are not lights. Projectile/trail/impact emitters are lights.

The main bottlenecks are renderer-side light selection, sorting, uniform upload, and per-pixel shader loops. Raising
shader light counts is not the solution.

## 2. Design Goal

Keep the renderer MM-like and forward-rendered:

- Static/authored lights define the room.
- Torchlight and key static lights should remain stable.
- Dense projectile/impact bursts should become a small number of clustered glow lights.
- Outdoor lights should be local to terrain chunks/BModels, not one camera-global top-eight list.
- Billboards should receive cheap CPU-sampled local lighting, not full per-pixel point lighting.
- Performance trace must explain where time goes.

Non-goals:

- No deferred renderer.
- No Forward+ or clustered forward renderer.
- No GPU-side light culling.
- No shadow maps.
- No normals/specular/PBR.
- No broad gameplay-owned lighting system.
- No adapter layer whose only purpose is to hide duplicated ownership.

## 3. Implementation Strategy

Do not introduce a giant `LightWorld` first.

Use the existing ownership and add shared helper code only where it removes real duplication:

- Keep indoor ownership in `game/indoor/IndoorLightingRuntime.*`.
- Add a small outdoor lighting runtime only when outdoor local selection starts.
- Add neutral shared structs/helpers under `game/render/lighting/` for light types, stats, scoring, clustering, and
  fixed-size top-N insertion.
- Keep `WorldFxSystem` as the source of transient FX emitters.
- Keep renderers responsible for bgfx uniforms and draw submission.

Recommended new files:

```text
game/render/lighting/RenderLight.h
game/render/lighting/LightingStats.h
game/render/lighting/LightSelection.h
game/render/lighting/LightSelection.cpp
game/render/lighting/FxLightClustering.h
game/render/lighting/FxLightClustering.cpp
game/outdoor/OutdoorLightingRuntime.h
game/outdoor/OutdoorLightingRuntime.cpp
```

Only create a file when the current phase needs it.

## 4. Shared Render Light Data

Add a neutral render-light kind. Keep it presentation-oriented, not gameplay-oriented.

```cpp
enum class RenderLightKind : uint8_t
{
    Static,
    Decoration,
    Torch,
    Projectile,
    Impact,
    ActorGlow,
    SpriteGlow,
    ClusteredFx,
    GenericFx,
};
```

Add a neutral light representation for shared selection/clustering helpers:

```cpp
struct RenderLight
{
    bx::Vec3 position = {0.0f, 0.0f, 0.0f};
    float radius = 0.0f;
    uint32_t colorAbgr = 0xffffffffu;
    float intensity = 1.0f;
    int16_t sectorId = -1;
    RenderLightKind kind = RenderLightKind::Static;
    uint32_t stableId = 0;
    bool dynamic = false;
    bool important = false;
};
```

Stable IDs are required for hysteresis:

- BLV lights: deterministic hash of map id plus BLV light id.
- Decoration lights: deterministic hash of map id plus decoration/entity index.
- Torchlight: fixed stable id per map/runtime.
- Projectile trail lights: projectile id.
- Impact lights: impact effect id.
- Actor glow: actor index plus map id.
- Sprite object glow: sprite object index/id if available.
- Clusters: deterministic hash of sector/cell bucket, kind, and color bucket.

If a source cannot provide a stable id at first, set `stableId = 0` and do not apply hysteresis to it.

## 5. WorldFxSystem Light Metadata

Current `WorldFxLightEmitter` has no kind or stable id. Add metadata with defaults so current call sites remain simple.

```cpp
struct WorldFxLightEmitter
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float radius = 0.0f;
    uint32_t colorAbgr = 0xffffffffu;
    int16_t sectorId = -1;
    RenderLightKind kind = RenderLightKind::GenericFx;
    uint32_t stableId = 0;
    bool important = false;
};
```

Add an overload or optional parameters to `WorldFxSystem::addLightEmitter`:

```cpp
void addLightEmitter(
    float x,
    float y,
    float z,
    float radius,
    uint32_t colorAbgr,
    int16_t sectorId = -1,
    RenderLightKind kind = RenderLightKind::GenericFx,
    uint32_t stableId = 0,
    bool important = false);
```

Update high-value call sites:

- Projectile trail: `RenderLightKind::Projectile`, `stableId = projectile.projectileId`.
- Projectile impact: `RenderLightKind::Impact`, `stableId = impact.effectId`, `important = true` only if visually needed.
- Torchlight: `RenderLightKind::Torch`, fixed stable id, `important = true`.
- Actor glow: `RenderLightKind::ActorGlow`, actor index stable id.
- Decoration glow: `RenderLightKind::Decoration`, decoration/entity stable id.
- Sprite object glow: `RenderLightKind::SpriteGlow`, sprite object stable id if available.

Do not change visual behavior in the metadata phase.

## 6. Lighting Stats

Implement stats first. This is Phase 1 and must not change visuals.

Create `game/render/lighting/LightingStats.h`:

```cpp
struct LightingStats
{
    uint32_t inputLights = 0;
    uint32_t inputStaticLights = 0;
    uint32_t inputDynamicLights = 0;
    uint32_t clusteredFxLights = 0;
    uint32_t outputLights = 0;

    uint32_t visibleSectors = 0;
    uint32_t selectionCalls = 0;
    uint32_t candidateEvaluations = 0;
    uint32_t maxCandidatesPerSelection = 0;
    uint32_t selectedLights = 0;
    uint32_t omittedTailLights = 0;
    uint32_t billboardSamples = 0;

    uint64_t buildFrameNanoseconds = 0;
    uint64_t clusteringNanoseconds = 0;
    uint64_t selectionNanoseconds = 0;
    uint64_t billboardSampleNanoseconds = 0;
    uint64_t outdoorEmitterScanNanoseconds = 0;
    uint64_t outdoorUniformSelectionNanoseconds = 0;
};
```

Add helpers:

```cpp
void resetLightingStats(LightingStats &stats);
void addLightingStats(LightingStats &target, const LightingStats &source);
```

### Indoor Phase 1 Instrumentation

Current indoor `performanceTrace` tracks broad render timings. Split lighting further:

- Time `IndoorLightingRuntime::buildFrame`.
- Time default selection.
- Time per-textured-batch selection inside the textured batch loop.
- Time CPU billboard lighting sampling for decoration, actor, and sprite-object billboard paths.
- Count:
  - total lights in `IndoorLightingFrame`;
  - static/global/FX lights;
  - selection calls;
  - candidate evaluations;
  - max candidates;
  - selected lights;
  - billboard samples.

Implementation detail:

- Add optional `LightingStats *pStats = nullptr` parameters to selection and sample functions.
- Preserve existing function behavior when `pStats == nullptr`.
- For static `selectDrawLightSetForBounds`, increment stats inside the function.
- For `sampleLightingRgbForSectors`, increment sample count and timing at call sites or inside the function.

Do not add extra allocations for stats.

### Outdoor Phase 1 Instrumentation

Current outdoor light selection is in `OutdoorRenderer::applyOutdoorFxLightUniforms`.

Add timing/counters for:

- emitter count before filtering;
- emitters filtered by radius/intensity;
- ranked candidates;
- selected uniform lights;
- time spent ranking/sorting/packing;
- number of times uniforms are applied.

Do not change the selection algorithm in Phase 1.

If outdoor does not have an equivalent performance log, add a small `settings.performanceTrace` gated log every 2 seconds.
Do not spam logs every frame.

Acceptance:

- Full unit tests pass.
- Visual output unchanged.
- `performanceTrace` exposes useful lighting counts and timings.

## 7. Indoor Sector Binning

This is Phase 2. It should improve indoor candidate gathering without changing shaders.

Current indoor already has `lightIndicesBySector`, `globalLightIndices`, and `fxLightIndices`, but FX lights can still be
scanned broadly for bounds overlap. Add explicit dynamic/FX sector bins:

```cpp
struct IndoorLightingFrame
{
    float ambient = 1.0f;
    std::vector<IndoorRenderLight> lights;
    std::vector<std::vector<uint32_t>> staticLightIndicesBySector;
    std::vector<std::vector<uint32_t>> dynamicLightIndicesBySector;
    std::vector<uint32_t> globalLightIndices;
};
```

If renaming existing fields is too disruptive, keep `lightIndicesBySector` as static/all-sector lights and add only:

```cpp
std::vector<std::vector<uint32_t>> dynamicLightIndicesBySector;
```

Rules:

- Static BLV and decoration lights go into their owning sector.
- Torchlight remains global and important.
- FX emitters with `sectorId >= 0` go into that sector's dynamic bin.
- FX emitters with invalid sector id go into global only as a temporary fallback.
- For portal-neighbor propagation, only add a light to a neighbor sector if its sphere intersects a portal bound. This is
  optional and can be skipped in the first binning patch.

Selection candidates for an indoor draw should come from:

- global important lights;
- current sector static lights;
- current sector dynamic lights;
- back sector static lights;
- back sector dynamic lights;
- optional propagated portal-neighbor dynamic lights.

Avoid scanning all FX lights for every batch.

Acceptance:

- Existing indoor lighting tests still pass.
- Add a focused unit test where many FX lights in unrelated sectors do not inflate candidate count for a draw.
- Indoor scenes are visually close to current output.

## 8. FX Light Clustering

This is Phase 3. It is the main scalability step for 60 Sparks.

Do not cluster everything. Cluster only dense dynamic FX lights:

- `Projectile`
- `Impact`
- `GenericFx` if it came from projectile/impact-like effects

Do not cluster:

- Torch
- Static BLV lights
- Decoration lights by default
- Actor glow by default
- Sprite glow by default

### Indoor Clustering

Cluster by sector plus coarse 3D bucket:

```cpp
constexpr float IndoorFxClusterCellSize = 256.0f;
constexpr uint32_t MaxFxClustersPerIndoorSector = 8;
constexpr uint32_t IndoorFxClusterThresholdPerSector = 8;
constexpr float MaxIndoorFxClusterRadius = 900.0f;
constexpr float MaxFxClusterIntensity = 2.5f;
```

Cluster key:

```cpp
struct IndoorFxClusterKey
{
    int16_t sectorId = -1;
    int32_t bucketX = 0;
    int32_t bucketY = 0;
    int32_t bucketZ = 0;
    RenderLightKind kind = RenderLightKind::GenericFx;
    uint32_t colorBucket = 0;
};
```

Only cluster a sector when clusterable FX count in that sector is above the threshold. Otherwise keep raw FX lights.

Cluster accumulation:

```cpp
struct FxLightCluster
{
    bx::Vec3 weightedPosition = {0.0f, 0.0f, 0.0f};
    float totalWeight = 0.0f;
    float energyRed = 0.0f;
    float energyGreen = 0.0f;
    float energyBlue = 0.0f;
    float maxRadius = 0.0f;
    bx::Vec3 boundsMin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 boundsMax = {0.0f, 0.0f, 0.0f};
    uint32_t count = 0;
};
```

Finalize radius from cluster bounds, not just `maxRadius * sqrt(count)`:

```cpp
const bx::Vec3 center = cluster.weightedPosition / cluster.totalWeight;
const float boundsRadius = distanceToFarthestClusterBound(center, cluster.boundsMin, cluster.boundsMax);
out.radius = std::min(MaxIndoorFxClusterRadius, boundsRadius + cluster.maxRadius);
```

Then clamp intensity:

```cpp
out.intensity = std::min(MaxFxClusterIntensity, energyToIntensity(cluster));
```

This avoids turning 60 small Sparks into one huge room-washing light.

### Outdoor Clustering

Do outdoor clustering after outdoor grid/chunks exist, or implement it only for the current global path as an interim
improvement. Preferred order:

1. Instrument.
2. Indoor bins.
3. Indoor clustering.
4. Stable selection.
5. Outdoor chunk/grid selection.
6. Outdoor clustering if not already done.

Suggested outdoor constants:

```cpp
constexpr float OutdoorFxClusterCellSize = 384.0f;
constexpr uint32_t OutdoorFxClusterThresholdPerCell = 8;
constexpr uint32_t MaxFxClustersPerOutdoorCell = 8;
constexpr float MaxOutdoorFxClusterRadius = 1200.0f;
```

Acceptance:

- 60 Sparks indoors reduces to a small number of clustered FX lights.
- The burst still visibly glows.
- Static/Torch lights remain stable.
- No obvious room-wide washout from clusters.

## 9. Per-Draw Budget And Scoring

Do not increase shader light counts as the primary solution.

Keep current budgets initially:

```cpp
constexpr size_t MaxIndoorDrawLights = 12;
constexpr size_t MaxOutdoorFxLights = 8;
```

Add explicit category reservations during selection.

Indoor starting budget:

```cpp
constexpr uint32_t MaxIndoorTorchLightsPerDraw = 1;
constexpr uint32_t MaxIndoorStaticLightsPerDraw = 4;
constexpr uint32_t MaxIndoorFxLightsPerDraw = 7;
```

Outdoor starting budget:

```cpp
constexpr uint32_t MaxOutdoorTorchLightsPerDraw = 1;
constexpr uint32_t MaxOutdoorStaticLightsPerDraw = 3;
constexpr uint32_t MaxOutdoorFxLightsPerDraw = 4;
```

If there are unused reserved slots, allow fallback fill from the best remaining lights.

Scoring inputs:

- sphere intersects draw bounds;
- distance to draw bounds;
- radius;
- intensity;
- light kind;
- sector/back-sector match indoors;
- view/front weighting indoors if still useful;
- previous selection stability.

Use fixed-size top-N insertion. Do not use full `std::sort` for every draw.

## 10. Stable Selection And Cache Rules

This is Phase 4.

Add stable IDs for lights first, then stable IDs for draws.

Indoor draw stable ID:

- Add `uint32_t stableId` to `IndoorRenderer::TexturedBatch`.
- Assign during textured batch rebuild from deterministic inputs:
  - sector id;
  - back sector id;
  - texture name hash;
  - batch index within the rebuild.
- If mechanisms rebuild batches, increment a lighting selection generation and clear stale cache.

Outdoor draw stable ID:

- Terrain chunk: chunk grid coordinate.
- BModel resolved group: BModel index plus animation/material key.
- Runtime mechanism transient BModel batch: BModel index plus face index plus current generation.

Cache shape:

```cpp
template <size_t MaxLights>
struct PreviousDrawLightSelection
{
    uint64_t generation = 0;
    uint32_t drawStableId = 0;
    std::array<uint32_t, MaxLights> lightIds = {};
    uint32_t lightCount = 0;
    uint32_t lastSeenFrame = 0;
};
```

Rules:

- Clear all selection caches on map load/shutdown.
- Increment generation when render batches are rebuilt in a way that can invalidate draw IDs.
- Mark entries seen each frame and erase entries not seen for a few frames.
- Do not apply hysteresis to lights with `stableId == 0`.
- New light replaces an old light only if:

```cpp
newScore > oldScore * 1.20f
```

Acceptance:

- Dense projectile bursts show less light popping.
- Cache does not grow without bound.
- Moving mechanisms and map reloads do not keep stale selections.

## 11. Aggregate Tail Lighting

Dropped lights should contribute softly, but must not darken existing ambient.

Do not do this:

```cpp
drawAmbientRgb = min(drawAmbientRgb, Vec3f(MaxTailRgb));
```

That clamps the entire ambient and can make bright scenes darker.

Do this instead:

```cpp
Vec3f tailRgb = {};
tailRgb += omittedStaticRgb * OmittedStaticTailScale;
tailRgb += omittedFxRgb * OmittedFxTailScale;
tailRgb = min(tailRgb, Vec3f(MaxTailRgb));
drawAmbientRgb = min(baseAmbientRgb + tailRgb, Vec3f(2.0f));
```

Starting constants:

```cpp
constexpr float OmittedStaticTailScale = 0.20f;
constexpr float OmittedFxTailScale = 0.10f;
constexpr float MaxTailRgb = 0.40f;
```

For indoor, compute omitted tail for candidates touching the draw bounds but not selected. Current behavior already does
something close to this. Preserve it and move it into shared selection only when useful.

For outdoor, compute tail per local cell/chunk only after outdoor grid selection exists.

## 12. Outdoor Local Lighting Requires Terrain Chunks

This is the biggest prerequisite missing from many high-level plans.

Current outdoor terrain uses one large textured terrain buffer, so per-draw local light selection for terrain cannot work
until terrain is split into local draw chunks.

Phase 5A: split textured terrain into chunks.

Add a chunk representation to `OutdoorGameView`, for example:

```cpp
struct TexturedTerrainChunk
{
    bgfx::VertexBufferHandle vertexBufferHandle = BGFX_INVALID_HANDLE;
    uint32_t vertexCount = 0;
    bx::Vec3 boundsMin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 boundsMax = {0.0f, 0.0f, 0.0f};
    int32_t cellX = 0;
    int32_t cellY = 0;
    uint32_t stableId = 0;
};
```

Requirements:

- Preserve current terrain texture atlas and shader.
- Chunk by outdoor world X/Y grid. Start with 1024 or 2048 world-unit chunks, then tune.
- Each chunk has bounds.
- Render each visible chunk with the current outdoor shader and local light uniforms.
- Keep the old whole-terrain path behind a debug/fallback flag only during rollout, then remove it.
- Watch draw call count. If chunk count is too high, use larger chunks.

Phase 5B: add outdoor light grid.

```cpp
constexpr float OutdoorLightCellSize = 512.0f;

struct OutdoorCellLightBin
{
    std::vector<uint32_t> staticLights;
    std::vector<uint32_t> dynamicLights;
};
```

Insert each outdoor light into all cells overlapped by its sphere. Query cells overlapped by:

```cpp
expandedBounds = expand(drawBounds, maxRelevantLightRadius);
```

Use local selection for:

- terrain chunks;
- resolved BModel groups;
- runtime/transient BModel batches, after bounds are available;
- blood splats;
- billboard CPU sampling.

Do not keep one global top-eight list after this phase.

Acceptance:

- Outdoor lights affect nearby terrain/BModels.
- Dense outdoor FX no longer selects only the camera-nearest global eight.
- Draw calls do not explode in normal outdoor scenes.

## 13. Outdoor Static/Decoration Light Ownership

Define outdoor decoration/glow ownership before implementing grid bins.

Current behavior rebuilds decoration and sprite glow lights as spatial FX every refresh in `OutdoorSpatialFxRuntime`.
That is acceptable initially, but long-term it is wasteful for static decorations.

Implementation order:

1. Keep current spatial emitter production for compatibility.
2. During outdoor grid phase, classify decoration and sprite glow emitters as `Decoration` or `SpriteGlow`.
3. Later, optionally cache static outdoor decoration lights in `OutdoorLightingRuntime` and only apply runtime hidden
   state each refresh.

Do not move this into gameplay. It is presentation data.

## 14. Billboard Lighting

This is Phase 6.

Do not add per-pixel billboard point-light loops.

Use CPU sampling:

- Indoor: sample from sector/back-sector bins plus aggregate tail.
- Outdoor: sample from nearby outdoor light grid cells plus aggregate tail.

Outdoor implementation detail:

The current billboard shader uses:

```glsl
vec3 litColor = textureColor.rgb * (u_billboardAmbient.rgb + v_color0.rgb);
```

Simplest compatible path:

- Set `u_billboardAmbient` per billboard or per draw item to the sampled RGB.
- Keep `v_color0.rgb` black unless using optional gradient/contribution.
- Keep alpha in vertex color.

If a billboard batch groups multiple items in one draw, either:

- split by sampled light if needed; or
- encode sampled light in vertex color and keep uniform ambient global.

Start simple. Outdoor billboards are currently ambient-only, so even center-sampled per-item lighting is a visible
improvement.

Acceptance:

- Outdoor actors/items/decorations near a projectile impact no longer remain completely ambient.
- Indoor billboards stay visually compatible with geometry.
- Billboard sample time is included in lighting stats.

## 15. Shader Changes

Keep shaders simple. Do not add normals/specular/shadows.

Change outdoor attenuation from `length()` to the indoor squared-distance style:

```glsl
vec3 toLight = lightPosition - worldPosition;
float radius = max(lightRadius, 1.0);
float distanceSquared = dot(toLight, toLight);
float inverseRadiusSquared = 1.0 / (radius * radius);
float attenuation = 1.0 - clamp(distanceSquared * inverseRadiusSquared, 0.0, 1.0);
attenuation *= attenuation;
lighting += lightColor.rgb * (lightIntensity * attenuation);
```

Keep shader array sizes unchanged initially:

- indoor: 12;
- outdoor: 8.

Acceptance:

- Outdoor shader no longer uses `length()` for FX light attenuation.
- Visual brightness is tuned to remain close to current output.
- No light-count increase is used to solve dense-light scenes.

## 16. Detailed Phase Plan

### Phase 1: Metrics Only

Files:

- `game/render/lighting/LightingStats.h`
- `game/indoor/IndoorLightingRuntime.h`
- `game/indoor/IndoorLightingRuntime.cpp`
- `game/indoor/IndoorRenderer.cpp`
- `game/outdoor/OutdoorRenderer.cpp`
- optionally `game/outdoor/OutdoorGameView.h`

Tasks:

- Add stats structs/helpers.
- Add optional stats pointers to indoor selection/sample functions.
- Split indoor build/selection/billboard timing.
- Add outdoor global ranking counters/timing.
- Log stats under `settings.performanceTrace`.

Tests:

- Unit tests for stats helper accumulation/reset.
- Existing full unit suite.

No visual behavior changes.

### Phase 2: Light Metadata

Files:

- `game/render/lighting/RenderLight.h`
- `game/fx/WorldFxSystem.h`
- `game/fx/WorldFxSystem.cpp`
- `game/outdoor/OutdoorSpatialFxRuntime.cpp`
- `game/indoor/IndoorLightingRuntime.cpp`

Tasks:

- Add `RenderLightKind`.
- Add kind/stableId/important metadata to `WorldFxLightEmitter`.
- Update important emitter call sites.
- Preserve default behavior for call sites not yet updated.

Tests:

- Unit test that projectile emitter preserves stable id/kind if practical.
- Existing full unit suite.

No intended visual behavior changes.

### Phase 3: Indoor Sector Dynamic Bins

Files:

- `game/indoor/IndoorLightingRuntime.h`
- `game/indoor/IndoorLightingRuntime.cpp`
- `tests/IndoorLightingRuntimeTests.cpp`

Tasks:

- Add dynamic light bins by sector.
- Stop broad FX scans during per-draw selection where possible.
- Keep existing uniforms and shader.

Tests:

- Many unrelated-sector FX lights do not increase candidate count for a sector draw.
- Existing indoor lighting tests.

### Phase 4: Indoor FX Clustering

Files:

- `game/render/lighting/FxLightClustering.h`
- `game/render/lighting/FxLightClustering.cpp`
- `game/indoor/IndoorLightingRuntime.cpp`
- `tests/IndoorLightingRuntimeTests.cpp`

Tasks:

- Cluster dense projectile/impact FX lights per sector and 3D bucket.
- Keep raw FX lights below threshold.
- Use cluster bounds plus max radius for cluster radius.
- Clamp cluster intensity and radius.

Tests:

- 60 same-sector FX lights reduce to bounded cluster count.
- Cluster does not exceed max radius/intensity.
- Torch/static lights remain present in selected set.

### Phase 5: Stable Selection

Files:

- `game/render/lighting/LightSelection.h`
- `game/render/lighting/LightSelection.cpp`
- `game/indoor/IndoorLightingRuntime.*`
- `game/indoor/IndoorRenderer.*`
- tests as needed

Tasks:

- Add stable light ids where not already present.
- Add stable draw ids for indoor textured batches.
- Cache previous selected lights with generation and eviction.
- Add hysteresis.
- Add explicit reserved category budgets.

Tests:

- Previously selected light is retained when a new light is only marginally better.
- New light replaces old when it beats hysteresis threshold.
- Cache clears on generation change.

### Phase 6: Outdoor Terrain Chunks

Files:

- `game/outdoor/OutdoorGameView.h`
- `game/outdoor/OutdoorGameView.cpp`
- `game/outdoor/OutdoorRenderer.cpp`

Tasks:

- Split textured terrain into bounded chunks.
- Submit chunks with current shader and current global light uniforms first.
- Preserve visual behavior before local lighting is added.
- Track draw count/performance.

Tests:

- Basic outdoor render resource tests if available.
- Headless or focused outdoor smoke test if available.
- Full unit suite.

### Phase 7: Outdoor Grid Local Selection

Files:

- `game/outdoor/OutdoorLightingRuntime.h`
- `game/outdoor/OutdoorLightingRuntime.cpp`
- `game/outdoor/OutdoorRenderer.cpp`
- `game/outdoor/OutdoorGameView.h`
- `tests` as practical

Tasks:

- Build outdoor light grid per frame/refresh.
- Query local lights for terrain chunks and BModel bounds.
- Replace global top-eight selection for geometry.
- Use fixed-size top-N insertion.
- Keep current global path behind a debug flag only during rollout.

Tests:

- Local query returns nearby lights and excludes far lights.
- Many emitters do not require full global sort for each draw.

### Phase 8: Outdoor FX Clustering

Files:

- `game/render/lighting/FxLightClustering.*`
- `game/outdoor/OutdoorLightingRuntime.*`

Tasks:

- Cluster dense outdoor projectile/impact lights per grid/bucket.
- Use clusters in local selection.

Tests:

- 60 outdoor FX lights reduce to bounded cluster count per cell.
- Local terrain chunk receives nearby cluster.

### Phase 9: Billboard Sampling

Files:

- `game/indoor/IndoorRenderer.cpp`
- `game/outdoor/OutdoorBillboardRenderer.cpp`
- `game/indoor/IndoorLightingRuntime.*`
- `game/outdoor/OutdoorLightingRuntime.*`

Tasks:

- Route indoor billboard samples through stats-aware local sampling.
- Replace outdoor ambient-only contribution with local CPU sample.
- Keep shader simple.

Tests:

- Outdoor billboard near a light receives brighter sample than far billboard.
- Indoor billboard sampling still respects sector lights.

### Phase 10: Shader Cleanup

Files:

- `game/shaders/fs_outdoor_textured_fog.sc`
- possibly tests/build scripts

Tasks:

- Replace outdoor `length()` attenuation with squared-distance attenuation.
- Tune `OutdoorFxLightingScale` if needed.

Tests:

- Build runtime shaders through normal build.
- Visual smoke test where possible.

## 17. Stress Scenes And Acceptance

Use or create stress coverage for:

1. Indoor dense FX:
   - 60 Sparks/projectile lights.
   - 20 authored/static lights.
   - Torchlight active.
   - Multiple visible sectors.

2. Indoor static-heavy dungeon:
   - Many authored lights.
   - Few dynamic lights.
   - Verify room ambience and authored lights remain stable.

3. Outdoor dense FX near party:
   - 60 projectile lights near player.
   - Verify local terrain/BModels receive clustered/local lighting.

4. Outdoor decoration-heavy town at night:
   - Many decoration glow emitters.
   - Verify no global top-eight artifacts.

5. Billboard consistency:
   - Actor/sprite next to projectile impact indoors and outdoors.
   - Billboard should not remain completely ambient while nearby geometry glows.

Final acceptance:

- Existing indoor/outdoor scenes still render correctly.
- 60 Sparks indoors does not cause severe CPU selection spikes.
- Dynamic FX lights are clustered when dense.
- Authored/static lights are not completely evicted by FX bursts.
- Outdoor lighting is local per terrain chunk/BModel, not one global top-eight list.
- Outdoor billboards receive approximate local lighting.
- Performance trace reports detailed lighting costs.
- Shader light count is not increased as the primary solution.
- Code remains contained and understandable.

## 18. Build And Verification Commands

Use normal project commands:

```bash
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests
cmake --build build --target openyamm -j25
git diff --check
```

For shader-affecting phases, make sure the runtime shader target is rebuilt by the normal app build.

If focused tests exist or are added, run them before the full suite.

## 19. First Codex Task

Start with Phase 1 only.

Task:

```text
Add lighting instrumentation and counters around the current lighting implementation without changing visual behavior.
Split indoor timing into frame build, per-draw selection, and billboard sampling. Add outdoor counters/timing for
current emitter filtering, global ranking, selected uniform lights, and uniform application. Wire the stats into the
existing performanceTrace output with low-frequency logging. Add focused unit tests for stats helpers, then run the full
unit suite and app build.
```

Do not start by rewriting lighting. Make the current cost visible first.
