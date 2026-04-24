# Acceptance Criteria

## Authoritative Plan

- [ ] `docs/world_particle_fx_extraction_plan.md` is the active authoritative source for this loop.
- [ ] `PLAN.md`, `TASK_QUEUE.md`, `PROGRESS.md`, `AGENTS.md`, and `scripts/run_refactor.sh` all point to the same
  particle FX extraction loop.
- [ ] `TASK_QUEUE.md` is concrete enough for autonomous execution in coherent slices.

## Structural Acceptance

- [ ] `ParticleRenderer` no longer depends on `OutdoorGameView`.
- [ ] Particle render resources live in shared FX code, not in outdoor-only view members.
- [ ] `ParticleSystem` ownership lives in shared FX runtime, not in `OutdoorGameView`.
- [ ] Projectile trail cooldowns and seen projectile impact ids live in shared FX runtime.
- [ ] Projectile trail particles and impact particles are spawned by shared FX code from shared projectile presentation
  state.
- [ ] Party spell world particles are spawned by shared FX code for both indoor and outdoor.
- [ ] Indoor does not keep a separate renderer-local spell/projectile FX fallback once the shared path is wired.
- [ ] Outdoor-specific FX code, if any remains, only handles truly outdoor-specific facts such as weather or decoration
  emitters.
- [ ] No new callback bag or adapter layer is added only to hide ownership.
- [ ] No OpenEnroth or mm_mapview2 code is copied.

## Readability Acceptance

- [ ] The shared FX frame update is readable as direct high-level steps: update particles, sync projectile FX, sync
  world emitters, render particles.
- [ ] New public types are coarse domain types, not phase/control-flow micro-structs.
- [ ] New names avoid `Decision`, `Patch`, `EffectDecision`, and similar extraction-plumbing vocabulary.
- [ ] Outdoor and indoor render loops show obvious shared FX update/render calls rather than large inline composition
  blocks.

## Behavioral Acceptance

- [ ] Outdoor projectile trails remain visible.
- [ ] Outdoor projectile impact particles remain visible.
- [ ] Outdoor party spell world FX remain visible.
- [ ] Indoor projectile trails are visible for representative spells such as Fire Bolt, Sparks, and Dragon Breath.
- [ ] Indoor projectile impact particles are visible.
- [ ] Indoor party spell world FX use the same shared particle recipes as outdoor.
- [ ] Indoor projectile sprite billboards and impact sprite billboards continue to render.
- [ ] `NoGravity` projectile behavior and projectile collision behavior are not changed by the FX refactor.
- [ ] Particle updates pause/resume consistently with current gameplay pause/cursor-mode behavior.

## Validation Acceptance

- [ ] `cmake --build build --target openyamm_unit_tests -j25`
- [ ] `ctest --test-dir build --output-on-failure`
- [ ] `cmake --build build --target openyamm -j25`
- [ ] `timeout 300s build/game/openyamm --headless-run-regression-suite projectiles`
- [ ] `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`
- [ ] Manual outdoor FX smoke recorded in `PROGRESS.md`.
- [ ] Manual indoor FX smoke recorded in `PROGRESS.md`.

## Done Definition

This loop is done only when:

- spell/projectile particle FX are shared by indoor and outdoor;
- outdoor no longer owns generic particle system/rendering state;
- indoor no longer uses a separate fallback for spell/projectile world FX;
- the shared architecture is documented as complete in `PROGRESS.md`;
- validation evidence is recorded in `PROGRESS.md`;
- `PROGRESS.md` contains `## Done definition satisfied: YES`.
