# Acceptance Criteria

## Authoritative Target

- [x] `docs/indoor_outdoor_shared_gameplay_extraction_plan.md` is the only authoritative refactor target.
- [x] `docs/shared_gameplay_action_extraction_plan.md` is deprecated historical context only.

## Structural

- [ ] `GameApplication::renderFrame` follows the target frame shape from the authoritative plan.
- [ ] A shared `GameInputSystem` samples engine/SDL input once per frame outside indoor/outdoor views.
- [ ] Shared gameplay consumes a semantic `GameplayInputFrame`.
- [ ] Shared gameplay input paths do not call `SDL_GetKeyboardState`, `SDL_GetMouseState`, or
  `SDL_GetRelativeMouseState` from `OutdoorGameView`, `IndoorGameView`, or `OutdoorGameplayInputController`.
- [ ] `GameplaySession::updateGameplay(const GameplayInputFrame &, float)` is the shared gameplay frame entry point.
- [ ] `OutdoorGameView` and `IndoorGameView` do not call `GameplayInputController::updateSharedGameplayInputFrame`.
- [ ] `GameplayInteractionController::WorldInteractionFrameInput` callback bag is removed or reduced to non-behavioral
  plain data only.
- [ ] Shared gameplay pulls party, UI state, held item state, pending spell state, status text, spell service, and item
  service directly from `GameSession`.
- [ ] Shared gameplay calls `IGameplayWorldRuntime` directly for world facts/application.
- [ ] `OutdoorGameView::render` does not assemble gameplay interaction, pending spell, held-item, activation, or party
  attack lambdas.
- [ ] `IndoorGameView::render` does not assemble no-op gameplay interaction lambdas.
- [ ] `IGameplayWorldRuntime` exposes cohesive world methods for picking, interaction, held-item world use/drop,
  pending spell target facts, party attack world facts/application, world update, and world rendering.
- [ ] No shared gameplay controller includes outdoor or indoor view headers.
- [ ] No new adapter/callback layer merely hides the old view ownership.

## Behavioral

- [ ] Outdoor behavior remains unchanged for mouse-look/RMB cursor mode.
- [ ] Outdoor behavior remains unchanged for LMB attack cadence.
- [ ] Outdoor behavior remains unchanged for quick cast and quick-cast attack fallback.
- [ ] Outdoor behavior remains unchanged for attack-cast substitution.
- [ ] Outdoor behavior remains unchanged for pending targeted spell confirmation/cancel.
- [ ] Outdoor behavior remains unchanged for Space/E/mouse activation.
- [ ] Outdoor behavior remains unchanged for held-item transfer/use/drop.
- [ ] Outdoor behavior remains unchanged for chest-open-with-Space item-pickup suppression.
- [ ] Indoor uses the same shared gameplay decisions as outdoor where indoor world hooks exist.
- [ ] Missing indoor behavior is represented as missing active-world implementation, not duplicated gameplay logic.

## Validation

- [ ] `cmake --build build --target openyamm -j25`
- [ ] `ctest --test-dir build --output-on-failure`
- [ ] Manual smoke status is recorded in `PROGRESS.md` for touched behavior.

## Done Definition

This refactor is done only when:

- the target frame shape is implemented;
- input is owned by shared gameplay infrastructure;
- gameplay decisions live in `GameplaySession` and shared controllers/services;
- active world owns world facts/application;
- indoor/outdoor views no longer wire shared gameplay behavior;
- no giant callback bag replaces the old ownership leak;
- indoor and outdoor use the same shared gameplay flow;
- `PROGRESS.md` contains `## Done definition satisfied: YES`.
