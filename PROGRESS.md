# Progress

## Current status

- Overall completion: reopened for OE-like indoor BLV collision/physics implementation.
- Current focus: replace simplified indoor destination collision with swept iterative OE-like collision.
- Last validated at: not yet validated for this slice.
- Hard blocker: NO

## Done definition satisfied: NO

## Authoritative subsystem plan

- Indoor collision/physics: `docs/indoor_oe_collision_physics_plan.md`

Architectural background:

- `docs/indoor_outdoor_shared_gameplay_extraction_plan.md`

## Chosen migration order

1. Audit OE/OpenYAMM indoor collision deltas.
2. Build private indoor swept collision primitives and state shape.
3. Add pure primitive tests where practical.
4. Implement portal-aware sector candidate collection.
5. Implement iterative face collision loop.
6. Convert indoor actor movement.
7. Restore authored actor wall/body radius and keep OE-like actor contact radius.
8. Convert indoor party movement.
9. Finalize collision category responses.
10. Remove temporary heuristics/noisy diagnostics and close acceptance.

Reason:

- outdoor actor movement is already structurally close to OE's swept iterative approach;
- indoor actor movement is the current larger parity gap;
- reduced indoor actor navigation radius currently works as a gameplay unblocker but is not a structural fix;
- the correct long-term fix is an OE-like swept BLV resolver inside indoor world-specific code.

## Current slice evidence

- 2026-04-22: Created the active indoor collision/physics Wiggum plan. The new authoritative subsystem document is
  `docs/indoor_oe_collision_physics_plan.md`.
- 2026-04-22: Reset `PLAN.md`, `ACCEPTANCE.md`, `TASK_QUEUE.md`, and `PROGRESS.md` to the indoor OE-like collision
  implementation slice.

## First ownership leaks / temporary workarounds to attack

- `IndoorMovementController::resolveMove` still contains destination-position wall collision plus wall/axis fallback
  logic. This should be replaced by swept nearest-hit iteration.
- Indoor actor movement currently uses a reduced non-flying navigation radius for wall movement. This must not remain
  the final solution once the swept resolver is active.
- `IndoorActorMoveBlocked` diagnostics are useful during implementation but should be removed or gated before
  completion.
- Indoor actor movement and party movement should converge on the same indoor collision engine rather than separate
  ad-hoc code paths.

## Validation history

- No validation run yet after resetting this slice.

## Manual smoke status

- Pending: `blv18` Naga Vault large actors passing through portals.
- Pending: opened door pocket movement without party jitter.
- Pending: actors blocked by closed doors/walls.
- Pending: hostile actor collision with indoor party.
