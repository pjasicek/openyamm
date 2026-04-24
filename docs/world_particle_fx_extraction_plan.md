# World Particle FX Extraction Plan

This document is the authoritative detailed plan for the current refactor loop.

The goal is to make spell/projectile particle FX a shared indoor/outdoor system. Outdoor already has the real particle
stack. Indoor currently has only partial projectile billboard presentation plus simple renderer-local fallback quads
for spell and impact FX. The refactor must move the real particle path into shared FX code and make indoor use the
same path.

## Non-Negotiable Constraints

- Do not copy OpenEnroth or mm_mapview2 code.
- Use OpenEnroth only as behavioral reference if needed.
- Preserve outdoor FX behavior while moving ownership.
- Do not implement separate indoor particle recipes.
- Do not refactor projectile gameplay/collision unless it is required to expose existing presentation state to shared
  FX.
- Keep the shared FX API coarse and readable.
- Do not introduce a large graph of `Decision`, `Patch`, `EffectDecision`, `EffectCommand`, or similar micro-plumbing
  types.
- Do not add callback bags or adapters that only hide ownership.
- Prefer direct ownership in shared FX code.

## Current State

Outdoor has the real particle stack:

- `game/fx/ParticleSystem.*`
- `game/fx/ParticleRenderer.*`
- `game/fx/ParticleRecipes.*`
- `game/outdoor/OutdoorFxRuntime.*`
- `OutdoorGameView::m_particleSystem`
- particle shader handles, particle material texture handles, and particle vertex batches stored on `OutdoorGameView`

Outdoor owns shared behavior today:

- projectile trail particles;
- projectile impact particles;
- projectile glow/light/contact-shadow presentation;
- party spell world particles;
- decoration fire/smoke particles;
- weather particles.

Indoor has only partial FX:

- projectile and impact sprite billboards are appended in `IndoorRenderer::renderSpriteObjectBillboards`;
- `IndoorRenderer::PendingSpellWorldFx` renders simple colored quads/rings;
- indoor does not own/update a `ParticleSystem`;
- indoor does not initialize or call `ParticleRenderer`;
- indoor does not use `ParticleRecipes` for projectile trails or impact particles.

## Target Shape

The desired frame shape should be obvious:

```cpp
activeWorld->updateWorld(deltaSeconds);
worldFxSystem.update(gameSession, *activeWorld, cameraState, deltaSeconds, gameplayPaused);
activeWorld->renderWorldGeometry();
worldFxRenderer.render(worldFxSystem, cameraState);
gameplayUi.render();
```

Exact names can differ, but the ownership should not.

## Shared Classes

### `WorldFxSystem`

Owns particle FX runtime state:

- `ParticleSystem`;
- particle update accumulator and cadence;
- projectile trail cooldowns keyed by projectile id;
- seen projectile impact ids;
- shared glow billboards;
- shared light emitters;
- shared contact shadows;
- weather emission accumulators, once weather is moved;
- decoration emitter bookkeeping, once decoration FX is moved.

Public API should stay coarse:

```cpp
class WorldFxSystem
{
public:
    void reset();
    void beginFrame();
    void update(
        GameSession &session,
        IGameplayWorldRuntime &world,
        const WorldFxFrameContext &context);

    void triggerPartySpellFx(const PartySpellCastResult &result);

    const ParticleSystem &particles() const;
    ParticleSystem &particles();
    const std::vector<WorldFxGlowBillboard> &glowBillboards() const;
    const std::vector<WorldFxLightEmitter> &lightEmitters() const;
    const std::vector<WorldFxContactShadow> &contactShadows() const;
};
```

This is intentionally coarse. Do not split one frame into many public decision/command structs.

### `WorldFxRenderer`

Renders shared particle state:

```cpp
class WorldFxRenderer
{
public:
    static void initializeResources(WorldFxRenderResources &resources);
    static void shutdownResources(WorldFxRenderResources &resources);
    static void renderParticles(
        const WorldFxRenderResources &resources,
        const ParticleSystem &particles,
        uint16_t viewId,
        const float *pViewMatrix,
        const bx::Vec3 &cameraPosition,
        float aspectRatio);
};
```

The renderer should not know `OutdoorGameView` or `IndoorRenderer`.

### `WorldFxRenderResources`

Owns bgfx resources currently stored on outdoor view:

- particle program handle;
- particle parameter uniform;
- texture sampler handle used for particles;
- generated particle textures;
- material texture handle indices;
- reusable particle vertex batches.

It should expose simple resource accessors used by `WorldFxRenderer`.

## Minimal World Seam

Avoid callback-heavy design. The shared FX system should pull shared projectile presentation from `GameSession`
directly.

World hooks should only cover facts that are truly world-specific:

```cpp
struct WorldFxFrameContext
{
    float deltaSeconds = 0.0f;
    bool paused = false;
    bool refreshSpatialFx = false;
    bx::Vec3 cameraPosition = {};
};

struct WorldFxEnvironment
{
    bool allowWeather = false;
    float rainIntensity = 0.0f;
    float snowIntensity = 0.0f;
};
```

`IGameplayWorldRuntime` may get a small method only if required:

```cpp
virtual WorldFxEnvironment worldFxEnvironment() const;
virtual std::optional<float> resolveFxFloorZ(float x, float y, float z) const;
```

Do not add hooks for projectile trail/impact data. That data already lives in shared projectile/gameplay FX services.

## Implementation Plan

### Step 1 - Bootstrap Shared Files

Add shared files with small or empty implementations:

- `game/fx/WorldFxSystem.h`
- `game/fx/WorldFxSystem.cpp`
- `game/fx/WorldFxRenderer.h`
- `game/fx/WorldFxRenderer.cpp`
- `game/fx/WorldFxRenderResources.h`
- `game/fx/WorldFxRenderResources.cpp`

Register them in `game/CMakeLists.txt`.

Acceptance:

- repository builds;
- new files do not yet change runtime behavior unless the slice intentionally wires one safe piece;
- ownership leaks are recorded in `PROGRESS.md`.

### Step 2 - Extract Render Resources

Move particle render resources from `OutdoorGameView` into `WorldFxRenderResources`.

Likely outdoor members to move:

- particle program handle;
- particle parameter uniform;
- particle texture handle indices;
- particle vertex batches.

Keep this step behavior-preserving. Outdoor should still render particles exactly as before.

Acceptance:

- `ParticleRenderer::initializeResources` no longer writes generated particle resources into `OutdoorGameView`;
- outdoor initializes `WorldFxRenderResources`;
- outdoor still renders particles.

### Step 3 - Make Particle Renderer View-Agnostic

Change particle rendering so it takes:

- `WorldFxRenderResources`;
- `ParticleSystem`;
- view id;
- view matrix;
- camera position;
- aspect ratio.

Remove `OutdoorGameView &` from `ParticleRenderer` / `WorldFxRenderer`.

Acceptance:

- `game/fx/ParticleRenderer.h` no longer includes/forwards `OutdoorGameView`;
- particle rendering has no direct outdoor dependency;
- outdoor render loop has one obvious shared particle render call.

### Step 4 - Move ParticleSystem Ownership

Move `ParticleSystem` and update cadence from outdoor view into `WorldFxSystem`.

Preserve current behavior:

- particle update step: `1.0f / 30.0f`;
- max accumulation: `0.25f`;
- do not update while cursor-mode/gameplay pause is active;
- call `beginFrame()` once per frame.

Acceptance:

- `OutdoorGameView::m_particleSystem` is removed;
- outdoor uses shared `WorldFxSystem`;
- no particle behavior change intended.

### Step 5 - Move Projectile Trail / Impact Particles

Move the generic projectile FX parts of `OutdoorFxRuntime::syncRuntimeProjectiles` into `WorldFxSystem`:

- classify projectile recipe;
- spawn trail particles through `FxRecipes::spawnProjectileTrailParticles`;
- enforce projectile trail cooldowns;
- process seen projectile impacts;
- spawn dedicated impact particles through `FxRecipes::spawnImpactParticles`;
- create shared light/glow/contact-shadow state if still needed by outdoor renderers.

Keep the code direct and readable:

```cpp
void WorldFxSystem::syncProjectileFx(GameSession &session, bool refreshSpatialFx)
{
    syncProjectileTrails(session, refreshSpatialFx);
    syncProjectileImpacts(session, refreshSpatialFx);
}
```

No public command vectors. No decision structs.

Acceptance:

- projectile trail/impact particle recipe spawning is no longer outdoor-owned;
- outdoor still sees projectile trails and impact particles;
- projectile headless suite passes.

### Step 6 - Move Party Spell World FX

Move party spell world particle spawning from `OutdoorFxRuntime` to `WorldFxSystem`.

Outdoor successful spell casts and indoor pending spell cast world effects should call the same method:

```cpp
worldFxSystem.triggerPartySpellFx(castResult);
```

Acceptance:

- outdoor party spell particles still render;
- indoor can trigger the same spell particles after Step 7;
- portrait spell FX remain in shared UI/runtime code and are not moved here.

### Step 7 - Wire Indoor

Indoor should initialize and use shared FX:

- initialize `WorldFxRenderResources`;
- update `WorldFxSystem` once per frame with same pause/cursor-mode policy;
- render particles using `WorldFxRenderer`;
- trigger spell FX via shared `WorldFxSystem`;
- use shared projectile presentation state for projectile trail/impact particles.

Acceptance:

- indoor Fire Bolt / Sparks / Dragon Breath trails visible;
- indoor projectile impact particles visible;
- indoor party spell world FX visible;
- indoor projectile and impact sprite billboards still render.

### Step 8 - Cleanup

Remove obsolete pieces:

- indoor `PendingSpellWorldFx` fallback;
- `IndoorRenderer::triggerPendingSpellWorldFx`;
- `IndoorRenderer::triggerProjectileImpactWorldFx` if replaced by shared FX;
- `OutdoorWorldRuntime::setParticleSystem` if no longer needed;
- generic projectile/spell particle logic from `OutdoorFxRuntime`;
- outdoor view particle resource members.

`OutdoorFxRuntime` may remain temporarily only for outdoor-specific weather/decorations. If it remains, its name and
scope should make that clear in a later cleanup.

Acceptance:

- static search shows no obsolete generic particle ownership remains;
- no duplicate indoor/outdoor spell/projectile particle recipe code.

## Validation

Always run after meaningful slices:

- `cmake --build build --target openyamm_unit_tests -j25`
- `ctest --test-dir build --output-on-failure`
- `cmake --build build --target openyamm -j25`

Run focused headless when projectile/indoor runtime wiring changes:

- `timeout 300s build/game/openyamm --headless-run-regression-suite projectiles`
- `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`

Manual smoke is required before closing acceptance:

- outdoor projectile trail/impact FX;
- outdoor party spell world FX;
- indoor projectile trail/impact FX;
- indoor party spell world FX.

## Completion

The loop is complete only when `PROGRESS.md` records:

- shared FX ownership is complete;
- outdoor generic particle ownership removed;
- indoor fallback FX removed;
- validation and manual smoke evidence;
- `## Done definition satisfied: YES`.
