# Task Queue

## Execution Rules

- Use this file as the executable queue.
- Use `docs/world_particle_fx_extraction_plan.md` as the authoritative detailed source.
- Do not execute the detailed plan linearly if a smaller coherent slice is safer.
- Keep slices reviewable and buildable.
- Preserve outdoor behavior before wiring indoor.
- Prefer coarse, direct shared ownership over callback-heavy purity.
- Do not add indoor-only particle recipe code.
- Do not refactor projectile gameplay/collision unless required by FX presentation wiring.
- Run validation relevant to each slice.
- Update this file and `PROGRESS.md` after each meaningful slice.
- Do not copy OpenEnroth or mm_mapview2 code.

## Current Migration Order

1. FX1 - Bootstrap shared world FX files and document current ownership leaks.
2. FX2 - Extract particle render resources and renderer API away from `OutdoorGameView`.
3. FX3 - Move `ParticleSystem` ownership and particle update cadence into shared `WorldFxSystem`.
4. FX4 - Move projectile trail and impact particle spawning into shared `WorldFxSystem`.
5. FX5 - Move party spell world FX spawning into shared `WorldFxSystem`.
6. FX6 - Wire indoor rendering/update to the shared FX path.
7. FX7 - Remove obsolete outdoor/indoor fallback ownership and simplify loops.
8. FX8 - Validate, manually smoke indoor/outdoor FX, and close acceptance.

## Ready

### FX1 - Bootstrap Shared World FX Plan And Ownership Audit

- [ ] Add shared files if needed:
  - `game/fx/WorldFxSystem.h`
  - `game/fx/WorldFxSystem.cpp`
  - `game/fx/WorldFxRenderer.h`
  - `game/fx/WorldFxRenderer.cpp`
  - `game/fx/WorldFxRenderResources.h`
  - `game/fx/WorldFxRenderResources.cpp`
- [ ] Register new files in `game/CMakeLists.txt`.
- [ ] Keep bootstrap empty/light if that makes the first slice easier to review.
- [ ] Record current ownership leaks in `PROGRESS.md`:
  - `OutdoorGameView::m_particleSystem`
  - `ParticleRenderer` taking `OutdoorGameView &`
  - particle shader/resource handles stored in outdoor view
  - `OutdoorFxRuntime::syncRuntimeProjectiles`
  - `OutdoorFxRuntime::triggerPartySpellFx`
  - indoor `PendingSpellWorldFx`
- [ ] Build if code changed.
- [ ] Update `PROGRESS.md`.

### FX2 - Extract Particle Renderer Resources

- [ ] Introduce `WorldFxRenderResources` with:
  - particle program handle;
  - particle parameter uniform;
  - texture sampler handle needed by particles;
  - generated particle material textures;
  - particle material texture handle indices;
  - reusable particle vertex batches.
- [ ] Change particle resource initialization to operate on `WorldFxRenderResources`, not `OutdoorGameView`.
- [ ] Keep generated particle textures shared and still sourced from current procedural builders.
- [ ] Make outdoor initialize and shutdown the shared render resources.
- [ ] Keep outdoor rendering unchanged visually.
- [ ] Build `openyamm`.
- [ ] Update `PROGRESS.md`.

### FX3 - Extract Particle Renderer API

- [ ] Replace `ParticleRenderer::renderParticles(OutdoorGameView &, ...)` with a shared renderer call taking:
  - `WorldFxRenderResources &`;
  - `const ParticleSystem &`;
  - view id;
  - view matrix;
  - camera position;
  - aspect ratio.
- [ ] Keep the render batching and sorting logic in shared renderer code.
- [ ] Remove direct access to outdoor billboard texture arrays from particle rendering.
- [ ] Keep outdoor render loop readable with a single shared particle render call.
- [ ] Build `openyamm`.
- [ ] Run `ctest --test-dir build --output-on-failure` if unit-test build is affected.
- [ ] Update `PROGRESS.md`.

### FX4 - Move ParticleSystem To Shared WorldFxSystem

- [ ] Add `WorldFxSystem` ownership for `ParticleSystem`.
- [ ] Move particle update accumulator/cadence out of `OutdoorGameView`.
- [ ] Preserve current cadence:
  - update at `1.0f / 30.0f`;
  - clamp accumulated particle time to `0.25f`;
  - do not update while gameplay cursor-mode pause is active.
- [ ] Outdoor uses `WorldFxSystem::updateParticles(...)` or equivalent direct readable method.
- [ ] Remove `OutdoorGameView::m_particleSystem`.
- [ ] Remove `OutdoorWorldRuntime::setParticleSystem` if only generic spell FX still needs it.
- [ ] Build `openyamm`.
- [ ] Update `PROGRESS.md`.

### FX5 - Move Projectile Trail / Impact Particles To Shared WorldFxSystem

- [ ] Move projectile trail cooldown map from `OutdoorFxRuntime` to `WorldFxSystem`.
- [ ] Move seen impact id set from `OutdoorFxRuntime` to `WorldFxSystem`.
- [ ] Move projectile trail particle spawning from `OutdoorFxRuntime::syncRuntimeProjectiles` to shared FX code.
- [ ] Move dedicated projectile impact particle spawning from `OutdoorFxRuntime::syncRuntimeProjectiles` to shared FX
  code.
- [ ] Pull projectile presentation state from `GameplayFxService` or `GameplayProjectileService` directly.
- [ ] Keep contact shadows/lights/glow as shared renderable FX state if they are still used by outdoor.
- [ ] Do not add a large projectile-FX request/decision API.
- [ ] Build `openyamm`.
- [ ] Run `timeout 300s build/game/openyamm --headless-run-regression-suite projectiles`.
- [ ] Update `PROGRESS.md`.

### FX6 - Move Party Spell World FX To Shared WorldFxSystem

- [ ] Move `OutdoorFxRuntime::triggerPartySpellFx(ParticleSystem &, const PartySpellCastResult &)` into shared FX code.
- [ ] Expose a direct shared call such as `WorldFxSystem::triggerPartySpellFx(const PartySpellCastResult &)`.
- [ ] Outdoor successful spell casts call the shared FX system.
- [ ] Indoor `applyPendingSpellCastWorldEffects` calls the same shared FX system.
- [ ] Keep portrait spell FX in shared UI/gameplay UI code; this task is only world particles.
- [ ] Build `openyamm`.
- [ ] Update `PROGRESS.md`.

### FX7 - Wire Indoor Shared Particle Rendering

- [ ] Indoor initializes `WorldFxRenderResources`.
- [ ] Indoor calls shared `WorldFxSystem` update once per frame with the same pause/cursor-mode behavior as outdoor.
- [ ] Indoor render loop calls shared particle renderer after indoor world geometry/billboards and before HUD.
- [ ] Indoor projectile trails appear from shared projectile presentation state.
- [ ] Indoor impact particles appear from shared impact presentation state.
- [ ] Indoor party spell world particles appear from shared spell FX calls.
- [ ] Build `openyamm`.
- [ ] Run `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`.
- [ ] Update `PROGRESS.md`.

### FX8 - Cleanup Obsolete FX Ownership

- [ ] Remove indoor `PendingSpellWorldFx` data, update, render, and trigger methods if the shared path replaces them.
- [ ] Delete or reduce `OutdoorFxRuntime` to only truly outdoor-specific weather/decoration emitters.
- [ ] Remove unused outdoor particle members, friend declarations, and resource plumbing.
- [ ] Remove redundant projectile impact fallback paths that now duplicate shared FX.
- [ ] Static-audit for dead references:
  - `rg "PendingSpellWorldFx|triggerPendingSpellWorldFx|m_particleSystem|setParticleSystem|syncRuntimeProjectiles"`
- [ ] Build `openyamm_unit_tests`.
- [ ] Run ctest.
- [ ] Build `openyamm`.
- [ ] Update `PROGRESS.md`.

### FX9 - Final Validation And Manual Smoke

- [ ] Run `cmake --build build --target openyamm_unit_tests -j25`.
- [ ] Run `ctest --test-dir build --output-on-failure`.
- [ ] Run `cmake --build build --target openyamm -j25`.
- [ ] Run `timeout 300s build/game/openyamm --headless-run-regression-suite projectiles`.
- [ ] Run `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`.
- [ ] Record manual outdoor smoke:
  - projectile trails visible;
  - projectile impacts visible;
  - party spell world FX visible.
- [ ] Record manual indoor smoke:
  - Fire Bolt / Sparks / Dragon Breath trails visible;
  - impacts visible;
  - party spell world FX visible;
  - projectile billboards still visible.
- [ ] Mark acceptance done only if all criteria are satisfied.
