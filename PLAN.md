# Plan

## Objective

Implement OE-like indoor BLV collision and physics structurally, not by portal-specific heuristics or reduced-radius
workarounds.

Authoritative detailed plan:

- `docs/indoor_oe_collision_physics_plan.md`

Architectural background:

- `docs/indoor_outdoor_shared_gameplay_extraction_plan.md`

## Target

Indoor movement should converge to an OE-shaped collision model:

```cpp
IndoorMoveResult result = indoorMovementController.resolveMove(request);
world.applyIndoorMoveResult(result);
sharedActorAi.updateActorAfterWorldMovement(worldMovementFacts);
```

The indoor movement controller owns BLV-specific physics:

- swept low/high body spheres;
- nearest collision along the movement segment;
- bounded iterative movement;
- face, portal, actor, party, decoration, and sprite-object collision categories;
- sector transitions through portals;
- floor/ceiling/step-up handling;
- moving mechanism / door blocking state.

Shared gameplay remains outside BLV collision:

- shared actor AI owns behavior decisions;
- indoor world provides movement/contact facts;
- indoor world applies movement results to BLV/DLV runtime state.

## Current Known Problem

The current indoor resolver still contains simplified destination-position collision logic. It was temporarily made
usable by giving non-flying indoor actors a reduced navigation radius. That unblocks Naga Vault portals, but it is not
the final structural solution.

The final implementation must remove the need for reduced-radius wall navigation by making the solver behave like OE:
move to nearest hit, respond, then continue with remaining movement.

## Current Priority

1. Build the OE-like swept indoor collision core.
2. Replace actor indoor movement first.
3. Replace party indoor movement second.
4. Remove temporary reduced-radius and noisy diagnostic code.
5. Validate Naga Vault and opened-door pocket cases.

## Anti-Goals

- Do not copy OpenEnroth code.
- Do not move BLV collision into shared gameplay.
- Do not create callback bags or adapter layers to hide ownership.
- Do not rewrite outdoor movement unless a clearly reusable primitive can be shared safely.
- Do not change actor AI decisions unless the collision result facts are insufficient.
- Do not keep `radius=40` indoor wall navigation as the final fix.

## Rules

- Use `TASK_QUEUE.md` as the executable queue.
- Use `docs/indoor_oe_collision_physics_plan.md` for detailed requirements and acceptance.
- Keep the repository buildable after each meaningful slice.
- Update `TASK_QUEUE.md` and `PROGRESS.md` after each meaningful slice.
- Prefer doctest coverage for pure collision math.
- Record manual smoke status for BLV integration cases in `PROGRESS.md`.
