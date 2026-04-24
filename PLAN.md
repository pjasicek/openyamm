# Plan

## Objective

Extract spell/projectile particle FX into a shared world FX subsystem used by both outdoor and indoor runtime/rendering.
Outdoor behavior should remain visually equivalent, while indoor gains the same projectile trail, projectile impact, and
party spell world particle FX path instead of renderer-local fallback quads.

Authoritative detailed plan:

- `docs/world_particle_fx_extraction_plan.md`

## Target Architecture

The end state should be easy to read in the frame loop:

```cpp
activeWorld->updateWorld(deltaSeconds);
worldFxSystem.update(gameSession, *activeWorld, cameraState, deltaSeconds, gameplayPaused);
activeWorld->renderWorldGeometry();
worldFxRenderer.render(worldFxSystem, cameraState);
gameplayUi.render();
```

Shared ownership:

- `WorldFxSystem` owns `ParticleSystem`, projectile trail cooldowns, seen impact ids, shared glow billboards, shared
  light emitters, shared contact shadows, party spell FX spawning, and projectile trail/impact particle spawning.
- `WorldFxRenderer` owns particle rendering against shared render resources, not `OutdoorGameView`.
- `WorldFxRenderResources` owns particle shaders, generated particle textures, material texture handles, and particle
  vertex batches.

World-specific ownership:

- outdoor/indoor provide camera state, render view ids, world visibility/floor facts where actually needed, and
  world-specific geometry/decal/collision behavior.
- outdoor/indoor do not own spell/projectile particle recipes or duplicate particle spawning logic.

## Current Priority

1. Make the renderer and resources independent of `OutdoorGameView`.
2. Move `ParticleSystem` ownership out of `OutdoorGameView` into shared FX runtime.
3. Move projectile trail/impact and party spell world FX spawning from `OutdoorFxRuntime`/indoor fallback into shared
   `WorldFxSystem`.
4. Wire outdoor first without visual regression, then wire indoor to the same shared path.
5. Remove obsolete indoor fallback FX and obsolete outdoor-only particle ownership.

## Rules

- Use `TASK_QUEUE.md` as the executable queue.
- Use `docs/world_particle_fx_extraction_plan.md` as the authoritative source of truth for this loop.
- Do not execute the detailed plan linearly if a different coherent slice is safer.
- Keep implementation coarse and readable; avoid micro-structs, `Decision`/`Patch`/`EffectDecision` vocabulary, and
  callback bags that only hide ownership.
- Do not copy OpenEnroth or mm_mapview2 code.
- Preserve outdoor visuals while moving ownership.
- Implement indoor using the same shared particle FX system, not an indoor-specific duplicate.
- Keep the repository buildable after each meaningful slice.
- Update `TASK_QUEUE.md` and `PROGRESS.md` after each meaningful slice.

## Validation

Primary validation:

- `cmake --build build --target openyamm_unit_tests -j25`
- `ctest --test-dir build --output-on-failure`
- `cmake --build build --target openyamm -j25`

Focused validation:

- `timeout 300s build/game/openyamm --headless-run-regression-suite projectiles`
- `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`

Manual smoke expected before final acceptance:

- outdoor projectile trails and impact particles still visible;
- outdoor party spell world FX still visible;
- indoor Fire Bolt / Sparks / Dragon Breath trails visible;
- indoor spell/projectile impact particles visible;
- indoor projectile billboards still render as before.

## Anti-Goals

- Do not rewrite projectile gameplay or collision as part of this slice.
- Do not introduce a large abstract FX graph.
- Do not add dozens of structs/enums to make the seam artificially pure.
- Do not add an indoor-only particle implementation.
- Do not move unrelated weather/decoration FX before projectile/spell parity is stable.
