# Progress

## Current status

- Overall completion: not complete for the runtime-boundary refactor.
- Current focus: establish the cohesive frame/input/world boundary from
  `docs/indoor_outdoor_shared_gameplay_extraction_plan.md`.
- Last validated at: 2026-04-21 during the previous shared action extraction review.
- Hard blocker: NO

## Done definition satisfied: NO

## Authoritative target

The only authoritative refactor document is:

- `docs/indoor_outdoor_shared_gameplay_extraction_plan.md`

`docs/shared_gameplay_action_extraction_plan.md` is deprecated historical context only.

## Current reality

- Shared action/input/interaction controllers exist and are real, but the runtime boundary is still transitional.
- `GameApplication::renderFrame` still branches into outdoor and indoor view render methods.
- Outdoor and indoor still participate in input sampling or raw input passing for shared gameplay.
- `GameplayInteractionController::WorldInteractionFrameInput` still represents a callback-heavy world interaction seam.
- `OutdoorGameView::render` still assembles gameplay interaction callbacks.
- Indoor still has safe no-op world interaction callback seams.
- `IGameplayWorldRuntime` exists, but it is not yet the cohesive active-world update/render and world-fact/application
  seam required by the authoritative plan.

## Chosen migration order

1. Introduce `GameInputSystem` and `GameplayInputFrame`.
2. Add `GameplaySession::updateGameplay`.
3. Replace the world interaction callback bag with direct `GameSession` state access and active-world calls.
4. Move outdoor callback bodies into active-world methods.
5. Implement indoor active-world seam methods.
6. Move world update/render entry behind active world.
7. Continue shared-system extraction under the new boundary.

## First ownership leaks to attack

- `game/outdoor/OutdoorGameplayInputController.cpp`: samples SDL input and runs shared gameplay input from the outdoor
  side.
- `game/indoor/IndoorGameView.cpp`: runs shared gameplay input and world interaction from the indoor view.
- `game/outdoor/OutdoorGameView.cpp`: assembles `GameplayInteractionController::WorldInteractionFrameInput` callbacks.
- `game/gameplay/GameplayInteractionController.h`: exposes a large callback-heavy `WorldInteractionFrameInput`.
- `game/app/GameApplication.cpp`: calls outdoor/indoor view render paths directly instead of the target frame shape.

## Validation history

- `cmake --build build --target openyamm -j25` passed on 2026-04-21 during the previous review.
- `ctest --test-dir build --output-on-failure` passed on 2026-04-21 during the previous review; no tests were
  configured.

## Manual smoke status

- No manual smoke has been run for the new runtime-boundary refactor yet.
