# Acceptance Criteria

## Authoritative Plan

- [ ] `docs/indoor_oe_collision_physics_plan.md` is the active subsystem plan.
- [ ] `TASK_QUEUE.md` contains the executable Wiggum queue for this collision slice.
- [ ] `PROGRESS.md` records evidence after each meaningful slice.

## Structural Acceptance

- [ ] Indoor actor movement no longer uses destination-only wall collision as the primary solver.
- [ ] Indoor actor movement uses swept movement to the nearest collision point.
- [ ] Indoor movement uses low/high body spheres and midpoint/extra sphere checks where needed for BLV faces.
- [ ] Indoor movement uses a bounded iterative loop that adjusts velocity after each hit.
- [ ] Indoor face hits project remaining movement along a slide plane.
- [ ] Indoor sector/portal transitions are resolved inside the movement solver.
- [ ] Moving mechanism / door state is respected by the collision face set.
- [ ] Actor-vs-actor collision/contact uses OE-like override radius semantics for crowd probing.
- [ ] Party-vs-actor collision is handled by the indoor collision system, not by UI/gameplay code.
- [ ] Shared actor AI remains shared and receives only movement/contact facts.
- [ ] No callback bags, ownership-hiding adapters, or indoor/outdoor gameplay duplication are introduced.
- [ ] No OpenEnroth code is copied.

## Behavioral Acceptance

- [ ] Non-flying indoor actors can use authored BLV actor radius for wall/body collision without portal over-blocking.
- [ ] The temporary reduced indoor wall-navigation radius workaround is removed or no longer used for final behavior.
- [ ] Large actors in `blv18` Naga Vault can pass through portals without requiring perfect center alignment.
- [ ] Actors still cannot pass through closed doors, walls, or blocking mechanisms.
- [ ] Actors slide along walls instead of being pinned by portal frames.
- [ ] Actor-vs-actor crowding blocks overlap but does not jam every portal.
- [ ] Hostile actors collide with the party indoors.
- [ ] Party movement through opened door pockets does not jitter.
- [ ] Indoor buttons/mechanisms continue to open/close/move doors correctly.
- [ ] Indoor actor AI post-movement facts still trigger crowd steering/fallback behavior when blocked.

## Test Acceptance

- [ ] Unit/doctest tests are preferred over headless tests for deterministic collision primitives.
- [ ] Doctest coverage exists for pure swept collision math where practical.
- [ ] Doctest coverage exists for nearest-hit selection where practical.
- [ ] Doctest coverage exists for wall velocity projection where practical.
- [ ] Doctest coverage exists for portal-adjacent sector selection where practical.
- [ ] Doctest coverage exists for actor contact override radius where practical.
- [ ] Headless tests cover integrated BLV collision behavior where practical and not cheaply unit-testable.
- [ ] Headless or manual smoke for `blv18` Naga Vault is recorded in `PROGRESS.md`.
- [ ] Headless or manual smoke for opened-door pocket movement is recorded in `PROGRESS.md`.

## Validation

- [ ] `cmake --build build --target openyamm -j25`
- [ ] `ctest --test-dir build --output-on-failure`

## Done Definition

This slice is done only when:

- all structural acceptance criteria are satisfied;
- all behavioral acceptance criteria are satisfied or explicitly documented as intentionally different from OE;
- required validation commands pass;
- temporary noisy diagnostics are removed or gated;
- `PROGRESS.md` contains `## Done definition satisfied: YES`.
