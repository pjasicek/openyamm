# Task Queue

## Execution Rules

- Use this file as the executable queue.
- Use `docs/indoor_oe_collision_physics_plan.md` as the authoritative detailed plan.
- Use `docs/indoor_outdoor_shared_gameplay_extraction_plan.md` only for ownership background.
- Do not execute the detailed plan linearly from top to bottom; execute the next coherent unfinished task here.
- Keep changes coherent and reviewable.
- Keep the repository buildable after each meaningful slice.
- Run `cmake --build build --target openyamm -j25` after each meaningful implementation slice.
- Run `ctest --test-dir build --output-on-failure` after each meaningful implementation slice.
- Prefer doctest/unit tests for deterministic collision math and resolver pieces.
- Add headless tests only for integrated BLV behavior that cannot be isolated cleanly in doctest.
- Update this file and `PROGRESS.md` after each meaningful slice.
- Do not copy OpenEnroth code.
- Do not move BLV collision into shared gameplay.
- Do not add callback bags or adapters that hide ownership.
- Do not keep the temporary reduced indoor actor navigation radius as the final solution.

## Current Migration Order

1. IC1 - Audit and document OE/OpenYAMM indoor collision deltas.
2. IC2 - Introduce private indoor swept collision state/result types.
3. IC3 - Implement pure swept sphere/face collision helpers with doctest coverage.
4. IC4 - Implement sector-limited face candidate collection with portal-adjacent sector inclusion.
5. IC5 - Implement the iterative indoor face collision loop.
6. IC6 - Convert indoor actor movement to the swept iterative resolver.
7. IC7 - Restore authored actor wall/body radius for indoor actor movement and keep OE-like actor contact radius.
8. IC8 - Convert indoor party movement to the swept iterative resolver.
9. IC9 - Add collision category responses for actor, party, decoration, sprite object, floor, steep face, and portal.
10. IC10 - Remove temporary heuristics/noisy diagnostics and finalize acceptance.

## Ready

### IC1 - Collision Delta Audit

- [ ] Inspect OE reference behavior in `reference/OpenEnroth-git/src/Engine/Graphics/Collisions.cpp`.
- [ ] Inspect current OpenYAMM indoor movement paths in `game/indoor/IndoorMovementController.*`,
  `game/indoor/IndoorWorldRuntime.*`, and `game/indoor/IndoorPartyRuntime.*`.
- [ ] Record conceptual deltas in `PROGRESS.md`.
- [ ] Identify current temporary workarounds to remove later, including reduced indoor actor wall-navigation radius and
  noisy `IndoorActorMoveBlocked` diagnostics.
- [ ] Do not change behavior unless the audit finds a tiny cleanup that is required before implementation.
- [ ] Build only if code changed.
- [ ] Update `PROGRESS.md`.

### IC2 - Private Indoor Collision Shape

- [ ] Add private or indoor-owned collision request/state/result types.
- [ ] Represent low sphere, high sphere, movement direction, move distance, adjusted move distance, hit type, hit face,
  hit collider, collision point, height offset, and sector id.
- [ ] Keep headers minimal; prefer implementation-private types unless callers need them.
- [ ] Keep existing public movement calls working initially.
- [ ] Do not introduce callback bags.
- [ ] Build `openyamm`.
- [ ] Run ctest.
- [ ] Update `PROGRESS.md`.

### IC3 - Swept Sphere / Face Primitives

- [ ] Implement swept sphere against indoor face geometry.
- [ ] Select nearest hit along movement distance.
- [ ] Support low sphere, high sphere, midpoint sphere, and face-center-height sphere checks.
- [ ] Respect untouchable/ethereal/non-blocking faces.
- [ ] Add doctest coverage for miss, direct hit, nearest-hit selection, and velocity projection primitives.
- [ ] Do not defer pure geometry behavior to headless tests.
- [ ] Build `openyamm`.
- [ ] Run ctest.
- [ ] Update `PROGRESS.md`.

### IC4 - Portal-Aware Sector Candidate Collection

- [ ] Implement swept-body bounds for face candidate collection.
- [ ] Include current sector and portal-adjacent sector when swept body touches portal bounds/plane closely enough.
- [ ] Preserve moving mechanism adjusted vertices and door blocking masks.
- [ ] Add doctest coverage where geometry can be isolated.
- [ ] Add or adapt a headless test only if the portal behavior requires loaded BLV data.
- [ ] Build `openyamm`.
- [ ] Run ctest.
- [ ] Update `PROGRESS.md`.

### IC5 - Iterative Indoor Face Collision Loop

- [ ] Add an internal iterative loop that advances to adjusted collision distance.
- [ ] On face hit, compute OE-like slide-plane projection for remaining velocity.
- [ ] Apply damping where appropriate.
- [ ] Handle floor hits, step-up, ceiling hits, and unsupported moves.
- [ ] Keep the current destination resolver available only as fallback during this step if needed.
- [ ] Build `openyamm`.
- [ ] Run ctest.
- [ ] Update `PROGRESS.md`.

### IC6 - Actor Movement Conversion

- [ ] Route `IndoorWorldRuntime::applyIndoorActorMovementIntegration` through the swept iterative resolver.
- [ ] Preserve shared AI post-movement fact reporting: contacted actor count, movement blocked, target edge distance,
  and movement intent updates.
- [ ] Preserve party collider participation.
- [ ] Preserve actor sector id updates.
- [ ] Validate manually or with focused diagnostics in `blv18` Naga Vault.
- [ ] Add headless coverage for `blv18` actor portal movement if it can be asserted without fragile timing.
- [ ] Build `openyamm`.
- [ ] Run ctest.
- [ ] Update `PROGRESS.md`.

### IC7 - Restore Authored Actor Wall Radius

- [ ] Remove or bypass the temporary reduced indoor wall-navigation radius workaround.
- [ ] Use authored actor radius for BLV actor-vs-wall/body collision once the swept resolver is active.
- [ ] Keep OE-like `40` override radius for actor-vs-actor contact/crowd probing.
- [ ] Confirm Naga Warrior / Naga Queen movement logs no longer need `radius=40` for wall collision to pass portals.
- [ ] Build `openyamm`.
- [ ] Run ctest.
- [ ] Update `PROGRESS.md`.

### IC8 - Party Movement Conversion

- [ ] Route indoor party movement through the swept iterative resolver or a shared variant of it.
- [ ] Preserve current input semantics, jump, gravity, and camera-independent gameplay behavior.
- [ ] Preserve party-vs-hostile-actor blocking.
- [ ] Validate opened-door pocket movement does not jitter.
- [ ] Add headless coverage for opened-door pocket movement if it can be asserted deterministically.
- [ ] Build `openyamm`.
- [ ] Run ctest.
- [ ] Update `PROGRESS.md`.

### IC9 - Collision Category Responses

- [ ] Finalize response handling for face, actor, party, decoration, sprite object, and portal hits.
- [ ] Ensure actor/party contacts produce world movement facts, not gameplay behavior duplication.
- [ ] Ensure floor/steep-face responses match OE-like behavior closely enough for indoor gameplay.
- [ ] Validate closed/open doors and moving mechanisms.
- [ ] Build `openyamm`.
- [ ] Run ctest.
- [ ] Update `PROGRESS.md`.

### IC10 - Cleanup And Acceptance

- [ ] Remove obsolete destination-only wall-slide and axis-fallback code.
- [ ] Remove or explicitly gate temporary `IndoorActorMoveBlocked` diagnostics.
- [ ] Remove temporary radius workaround constants if no longer needed.
- [ ] Run static scans for leftover collision hacks.
- [ ] Run `cmake --build build --target openyamm -j25`.
- [ ] Run `ctest --test-dir build --output-on-failure`.
- [ ] Record manual smoke status in `PROGRESS.md`.
- [ ] Update `ACCEPTANCE.md`.
- [ ] Set `PROGRESS.md` to `## Done definition satisfied: YES` only when all acceptance criteria are satisfied.
