# Task Queue

## Execution Rules

- Use this file as the executable queue.
- Use `docs/projectile_service_moderate_refactor_plan.md` for projectile task details.
- Use `docs/actor_ai_shared_refactor_plan.md` for actor AI task details.
- Use `docs/indoor_outdoor_shared_gameplay_extraction_plan.md` only for architectural ownership background.
- Do not execute any plan linearly from top to bottom.
- Work on one coherent slice at a time.
- Prefer projectile cleanup before actor AI unless the user explicitly redirects.
- Do not introduce callback bags or adapters that hide ownership.
- Build after each meaningful implementation slice with `cmake --build build --target openyamm -j25`.
- Run `ctest --test-dir build --output-on-failure` after each meaningful implementation slice.
- Update this file and `PROGRESS.md` after each meaningful implementation slice.

## Current Migration Order

1. Projectile Step P1 - add coarse frame facts/result types.
2. Projectile Step P2 - add outdoor projectile frame fact builder.
3. Projectile Step P3 - implement `updateProjectileFrame`.
4. Projectile Step P4 - switch outdoor projectile loop to facts/result.
5. Projectile Step P5 - remove or privatize old frame-decision layer.
6. Projectile Step P6 - rename misleading presentation terms.
7. Projectile Step P7 - re-audit Fire Spike and shower projectile paths.
8. Actor AI Step A1 - freeze the micro-struct direction.
9. Actor AI Step A2 - split outdoor actor frame into named phases.
10. Actor AI Step A3 - add coarse actor AI facts/result types.
11. Actor AI Step A4 - introduce `GameplayActorAiSystem`.
12. Actor AI Step A5 - move outdoor decisions behind shared AI loop.
13. Actor AI Step A6 - demote `GameplayActorService`.
14. Actor AI Step A7 - add indoor runtime AI state.
15. Actor AI Step A8 - implement indoor fact collection.
16. Actor AI Step A9 - apply shared AI to indoor.

## Ready

### P1 - Projectile coarse frame facts/result types
- [ ] Audit current public projectile structs in `GameplayProjectileService.h`.
- [ ] Add `ProjectileFrameFacts` beside existing types.
- [ ] Add `ProjectileFrameResult` beside existing types.
- [ ] Keep new types free of indoor/outdoor representation details.
- [ ] Do not change call sites yet.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the projectile plan progress section.

### P2 - Outdoor projectile frame fact builder
- [ ] Audit `OutdoorWorldRuntime::updateProjectiles`.
- [ ] Add a helper that collects all world facts needed for one projectile frame.
- [ ] Reuse existing collision, bounce, and area-impact helpers internally.
- [ ] Keep behavior unchanged.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the projectile plan progress section.

### P3 - Implement `updateProjectileFrame`
- [ ] Implement the new frame API in `GameplayProjectileService`.
- [ ] Delegate to existing internal decision builders initially if that reduces risk.
- [ ] Convert old decision output into `ProjectileFrameResult`.
- [ ] Keep helper names domain-oriented.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the projectile plan progress section.

### P4 - Switch outdoor projectile loop to facts/result
- [ ] Change outdoor projectile loop to collect facts, call `updateProjectileFrame`, then apply result.
- [ ] Add `OutdoorWorldRuntime::applyProjectileFrameResult`.
- [ ] Preserve logging, audio, FX, bounce, damage, expiry, and spawned projectile behavior.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the projectile plan progress section.

### P5 - Remove or privatize old projectile frame-decision layer
- [ ] Remove obsolete intermediate decision structs from the public header where no longer used.
- [ ] Keep old helpers private only if still useful.
- [ ] Remove public command enums that are only frame-update plumbing.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the projectile plan progress section.

### P6 - Rename misleading projectile presentation terms
- [ ] Rename result/effect types that use "presentation" for audio/log/impact orchestration.
- [ ] Reserve "presentation" for actual render-facing state.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the projectile plan progress section.

### P7 - Re-audit Fire Spike and shower projectile paths
- [ ] Audit Fire Spike, Meteor Shower, Starburst, and special projectile paths.
- [ ] Record whether they fit the new frame shape or need a separate follow-up.
- [ ] Avoid refactoring them unless the main projectile loop is already stable and the change is small.
- [ ] Build and run ctest if code changed.
- [ ] Update `PROGRESS.md` and the projectile plan progress section.

### A1 - Actor AI micro-struct freeze
- [ ] Audit public structs in `GameplayActorService.h`.
- [ ] Record which micro-struct groups are candidates for removal or privatization.
- [ ] Do not add new public micro-decision structs for actor AI work.
- [ ] Build and run ctest if code changed.
- [ ] Update `PROGRESS.md` and the actor AI plan progress section.

### A2 - Split outdoor actor frame into named phases
- [ ] Audit `OutdoorWorldRuntime::updateMapActors`.
- [ ] Extract behavior-preserving named phase helpers.
- [ ] Keep behavior unchanged.
- [ ] Do not introduce shared AI yet if the frame is still unreadable.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the actor AI plan progress section.

### A3 - Add coarse actor AI facts/result types
- [ ] Add `ActorAiFrameFacts`.
- [ ] Add `ActorAiFacts`.
- [ ] Add `ActorAiUpdate`.
- [ ] Add `ActorAiFrameResult`.
- [ ] Keep types free of outdoor/indoor storage details.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the actor AI plan progress section.

### A4 - Introduce `GameplayActorAiSystem`
- [ ] Add a shared actor AI system class.
- [ ] Add `updateActors(const ActorAiFrameFacts &facts)`.
- [ ] Implement an initial behavior-readable loop.
- [ ] It may call existing `GameplayActorService` rules internally.
- [ ] Do not expose the current micro-decision API through the new system.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the actor AI plan progress section.

### A5 - Move outdoor decisions behind shared AI loop
- [ ] Add outdoor fact collection for active/background actors.
- [ ] Call `GameplayActorAiSystem::updateActors` from outdoor actor update.
- [ ] Apply result back to outdoor actor state.
- [ ] Keep outdoor terrain/collision/movement integration outdoor-owned.
- [ ] Preserve crowd steering, target choice, attacks, status locks, death transitions, timers, and projectiles.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the actor AI plan progress section.

### A6 - Demote `GameplayActorService`
- [ ] Move obsolete public micro-decision structs into private implementation detail where possible.
- [ ] Keep reusable rule helpers small and named by behavior.
- [ ] Remove or privatize public methods no longer used outside shared AI.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the actor AI plan progress section.

### A7 - Add indoor runtime AI state
- [ ] Audit indoor actor runtime state needs.
- [ ] Add persistent indoor AI state comparable to outdoor where missing.
- [ ] Keep BLV representation separate from outdoor actor storage.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the actor AI plan progress section.

### A8 - Implement indoor fact collection
- [ ] Build indoor active actor facts using BLV-specific data.
- [ ] Include distance, sector, portal activation, detection, LOS, floor/height, and reachable target facts.
- [ ] Keep indoor detection/LOS world-owned.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the actor AI plan progress section.

### A9 - Apply shared AI to indoor
- [ ] Indoor calls the same `GameplayActorAiSystem::updateActors` path.
- [ ] Indoor applies AI results to indoor actor runtime state.
- [ ] Indoor applies movement through BLV collision/floor/sector logic.
- [ ] Indoor spawns projectiles/audio/FX through indoor world application.
- [ ] Build and run ctest.
- [ ] Update `PROGRESS.md` and the actor AI plan progress section.

## In Progress
- [ ] None

## Blocked
- [ ] None
