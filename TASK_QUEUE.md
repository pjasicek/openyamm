# Task Queue

## Execution Rules

- `docs/indoor_outdoor_shared_gameplay_extraction_plan.md` is the only authoritative refactor target.
- `docs/shared_gameplay_action_extraction_plan.md` is deprecated historical context only.
- Use this file as the executable queue.
- Do not execute the master plan linearly.
- Finish one ownership transfer path before starting another.
- Prefer moving ownership into shared gameplay over adding forwarding methods to
  `OutdoorGameView` or `IndoorGameView`.
- Do not replace callback-heavy view wiring with another callback-heavy adapter.
- Shared gameplay should access `GameSession` state directly.
- Shared gameplay should call `GameSession::activeWorldRuntime()` directly for
  world facts/application.
- Build after each meaningful implementation slice with `cmake --build build --target openyamm -j25`.
- Run `ctest --test-dir build --output-on-failure` after each meaningful implementation slice.
- Update `PROGRESS.md` after each meaningful implementation slice.

## Current Migration Order

1. Introduce `GameInputSystem` and `GameplayInputFrame`.
2. Add `GameplaySession::updateGameplay`.
3. Replace `GameplayInteractionController::WorldInteractionFrameInput` callback bag.
4. Move outdoor callback bodies into active-world methods.
5. Implement indoor active-world seam methods.
6. Move world rendering behind active world.
7. Continue shared-system extraction under the new boundary.

## Ready

### Step 16 - Shared input system owns gameplay input sampling
- [ ] Audit SDL input reads in `OutdoorGameView`, `IndoorGameView`, `OutdoorGameplayInputController`,
  shared gameplay controllers, and UI overlay input paths.
- [ ] Add `GameplayInputFrame` with semantic actions, pointer facts, relative mouse facts, wheel facts, and held/pressed
  edge state.
- [ ] Add `GameInputSystem` owned outside indoor/outdoor views.
- [ ] Move shared gameplay SDL sampling into `GameInputSystem::updateFromEngineInput`.
- [ ] Preserve keybind resolution in one place.
- [ ] Route existing shared UI/gameplay input controllers from `GameplayInputFrame`.
- [ ] Leave only explicitly world-debug input in world code if needed, and record it as temporary.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md`.

### Step 17 - GameplaySession becomes the gameplay frame owner
- [ ] Add `GameplaySession::updateGameplay(const GameplayInputFrame &, float)`.
- [ ] Move shared input/UI/modal gating calls into `GameplaySession::updateGameplay`.
- [ ] Move quick-cast, attack-cast, action cadence, pending targeted spell, and world-interaction update entry calls into
  `GameplaySession::updateGameplay`.
- [ ] Make outdoor and indoor stop calling `GameplayInputController::updateSharedGameplayInputFrame` directly.
- [ ] Keep world movement/camera integration behind active-world methods.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md`.

### Step 18 - Remove the world interaction callback bag
- [ ] Audit all fields in `GameplayInteractionController::WorldInteractionFrameInput`.
- [ ] Delete callbacks that only expose `GameSession` state already owned by gameplay.
- [ ] Replace world-fact callbacks with direct calls to `IGameplayWorldRuntime`.
- [ ] Replace world-application callbacks with direct calls to `IGameplayWorldRuntime`.
- [ ] Ensure `OutdoorGameView::render` does not assemble interaction, pending spell, held-item, activation, or attack
  lambdas.
- [ ] Ensure `IndoorGameView::render` does not assemble no-op interaction lambdas.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md`.

### Step 19 - Outdoor implements the active-world seam
- [ ] Move outdoor ray/pick facts behind outdoor active-world methods.
- [ ] Move outdoor pending spell target facts behind outdoor active-world methods.
- [ ] Move outdoor keyboard interaction picking behind outdoor active-world methods.
- [ ] Move outdoor activation range/application behind outdoor active-world methods.
- [ ] Move outdoor held-item world use/drop behind outdoor active-world methods.
- [ ] Move outdoor party attack world facts/application behind outdoor active-world methods.
- [ ] Keep `OutdoorInteractionController` only as a world implementation helper if still useful.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md`.

### Step 20 - Indoor implements the active-world seam
- [ ] Add indoor pick/raycast facts for actors, world items, event faces, mechanisms, and ground/world target points.
- [ ] Add indoor keyboard interaction target selection.
- [ ] Add indoor activation range/application.
- [ ] Add indoor held-item world use/drop.
- [ ] Add indoor pending spell world target facts and spell FX application.
- [ ] Add indoor party attack world facts/application.
- [ ] Remove safe no-op indoor seams once real hooks exist.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md`.

### Step 21 - Active world owns world update/render entry
- [ ] Add or finalize `IGameplayWorldRuntime::updateWorld`.
- [ ] Add or finalize `IGameplayWorldRuntime::renderWorld`.
- [ ] Move outdoor world update/render entry behind active world.
- [ ] Move indoor world update/render entry behind active world.
- [ ] Refactor `GameApplication::renderFrame` toward the target frame shape.
- [ ] Render shared gameplay UI after active world rendering.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md`.

### Step 22 - Continue shared-system extraction under the new boundary
- [ ] Re-audit UI rendering, UI screens, item flow, spell flow, projectiles, particles, actor AI, and static data
  ownership against the authoritative plan.
- [ ] Add follow-up queue items only after Steps 16-21 are complete or blocked.

## In Progress
- [ ] None

## Blocked
- [ ] None
