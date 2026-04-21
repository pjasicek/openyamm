# Progress

## Current status

- Overall completion: not complete for the projectile and actor AI subsystem refactor batch.
- Current focus: P1 - projectile coarse frame facts/result types.
- Last validated at: not yet validated for this batch.
- Hard blocker: NO

## Done definition satisfied: NO

## Authoritative subsystem plans

- Projectile: `docs/projectile_service_moderate_refactor_plan.md`
- Actor AI: `docs/actor_ai_shared_refactor_plan.md`

Architectural background:

- `docs/indoor_outdoor_shared_gameplay_extraction_plan.md`

## Chosen migration order

1. Finish the projectile service moderate refactor.
2. Then finish the shared actor AI refactor.

Reason:

- projectile refactor is smaller and establishes the coarse facts/result exchange style;
- actor AI is larger and crosses movement, collision, combat, FX, and persistent actor state.

## First ownership leaks to attack

Projectile:

- `GameplayProjectileService` public frame API exposes too many intermediate decision/result structs.
- `OutdoorWorldRuntime::updateProjectiles` is expected to be the first loop converted to facts/result exchange.

Actor AI:

- `GameplayActorService` public API exposes too many tiny actor-frame decision structs.
- `OutdoorWorldRuntime::updateMapActors` still owns the readable actor behavior frame.

## Validation history

- None for this batch yet.

## Manual smoke status

- Not run yet.
