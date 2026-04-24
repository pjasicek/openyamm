# Progress

## Current status

- Overall completion: not started.
- Current focus: shared world particle FX extraction for indoor/outdoor parity.
- Hard blocker: NO

## Done definition satisfied: NO

## Authoritative source

- `docs/world_particle_fx_extraction_plan.md`

## Chosen migration order

1. Bootstrap shared FX files and lock ownership expectations.
2. Extract particle render resources/API out of `OutdoorGameView`.
3. Move `ParticleSystem` ownership and update cadence into shared `WorldFxSystem`.
4. Move projectile trail/impact particle spawning into shared `WorldFxSystem`.
5. Move party spell world FX spawning into shared `WorldFxSystem`.
6. Wire indoor to the same shared update/render path.
7. Remove obsolete outdoor/indoor fallback ownership.
8. Validate with unit, focused headless, and manual smoke.

Reason:

- outdoor currently has the only real particle stack;
- indoor currently has only renderer-local fallback quads for spell/impact FX;
- projectile/spell FX are gameplay presentation systems and should be shared by default;
- extracting render resources first reduces risk because outdoor can stay visually stable while ownership moves;
- indoor should plug into the finished shared path rather than receive duplicate particle recipe code.

## First ownership leaks to attack

- `game/outdoor/OutdoorGameView.h`: `m_particleSystem` is outdoor-owned even though particles are shared gameplay FX.
- `game/fx/ParticleRenderer.h`: renderer API takes `OutdoorGameView &`.
- `game/outdoor/OutdoorGameView.h`: particle shader handles, texture indices, and vertex batches are outdoor-owned.
- `game/outdoor/OutdoorFxRuntime.cpp`: projectile trail/impact particles are outdoor-owned in
  `syncRuntimeProjectiles`.
- `game/outdoor/OutdoorFxRuntime.cpp`: party spell world particles are outdoor-owned in `triggerPartySpellFx`.
- `game/indoor/IndoorRenderer.cpp`: `PendingSpellWorldFx` is an indoor-only fallback and should disappear after shared
  particle FX are wired.
- `game/indoor/IndoorWorldRuntime.cpp`: indoor routes impact visuals to the fallback renderer path instead of shared
  particle FX.

## Current expected end state

- `WorldFxSystem` owns `ParticleSystem`, projectile trail cooldowns, seen impact ids, and shared FX renderable state.
- `WorldFxRenderer` renders particles from `ParticleSystem` without knowing indoor/outdoor view classes.
- `WorldFxRenderResources` owns particle shaders, uniforms, procedural particle textures, material texture handles, and
  render batches.
- Outdoor and indoor call the same shared FX update/render functions.
- Indoor and outdoor spell/projectile particle FX are visually driven by the same `FxRecipes`.

## Validation baseline

Primary:

- `cmake --build build --target openyamm_unit_tests -j25`
- `ctest --test-dir build --output-on-failure`
- `cmake --build build --target openyamm -j25`

Focused:

- `timeout 300s build/game/openyamm --headless-run-regression-suite projectiles`
- `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`

Manual:

- outdoor projectile trail/impact/party spell FX smoke;
- indoor projectile trail/impact/party spell FX smoke.

## Current slice evidence

- 2026-04-24: Reset `PLAN.md`, `ACCEPTANCE.md`, `TASK_QUEUE.md`, `PROGRESS.md`, `scripts/run_refactor.sh`, and the
  current subsystem section of `AGENTS.md` to the world particle FX extraction loop.
- 2026-04-24: Added `docs/world_particle_fx_extraction_plan.md` as the authoritative detailed source for this loop.
- 2026-04-24: No implementation refactor has started yet.
