# Acceptance Criteria

## Authoritative Plans

- [ ] `docs/projectile_service_moderate_refactor_plan.md` progress says `Done definition satisfied: YES`.
- [ ] `docs/actor_ai_shared_refactor_plan.md` progress says `Done definition satisfied: YES`.

## Projectile Structural Acceptance

- [ ] The main projectile loop uses `ProjectileFrameFacts` and `ProjectileFrameResult`.
- [ ] Shared projectile service owns projectile gameplay decisions.
- [ ] Active world owns projectile collision facts and world-specific application.
- [ ] Public projectile frame API no longer exposes the old micro-decision command layer.
- [ ] Projectile refactor does not merge indoor/outdoor runtime, renderer, or collision types.
- [ ] Projectile refactor does not introduce callback bags or ownership-hiding adapters.

## Projectile Behavioral Acceptance

- [ ] Projectile travel behavior remains unchanged.
- [ ] Bounce behavior remains unchanged.
- [ ] Collision and expiry behavior remains unchanged.
- [ ] Direct actor/party impact behavior remains unchanged.
- [ ] Area impact behavior remains unchanged.
- [ ] Impact FX/audio behavior remains unchanged.
- [ ] Spawned projectile behavior remains unchanged.
- [ ] Special paths are audited: Fire Spike, Meteor Shower, Starburst, and other special projectile paths.

## Actor AI Structural Acceptance

- [ ] Shared actor AI owns high-level actor behavior decisions.
- [ ] Outdoor produces coarse actor AI facts and applies coarse actor AI results.
- [ ] Indoor produces coarse actor AI facts and applies coarse actor AI results.
- [ ] Movement, collision, LOS, floor/sector/terrain, and representation-specific application remain world-owned.
- [ ] `GameplayActorService` is no longer the public micro-decision API for the actor frame.
- [ ] Actor AI refactor does not merge indoor/outdoor actor storage.
- [ ] Actor AI refactor does not introduce callback bags or ownership-hiding adapters.

## Actor AI Behavioral Acceptance

- [ ] Outdoor idle/wander behavior remains unchanged.
- [ ] Outdoor pursuit behavior remains unchanged.
- [ ] Outdoor melee attack behavior remains unchanged.
- [ ] Outdoor ranged attack/projectile spawn behavior remains unchanged.
- [ ] Outdoor actor-vs-actor hostility behavior remains unchanged.
- [ ] Fear, blind, stun, paralyze, and death transitions remain correct.
- [ ] Crowd steering remains at least as good as before the refactor.
- [ ] Indoor actor AI uses the same shared behavior decisions where indoor world hooks exist.

## Validation

- [ ] `cmake --build build --target openyamm -j25`
- [ ] `ctest --test-dir build --output-on-failure`
- [ ] Manual smoke status is recorded in `PROGRESS.md` for touched behavior.

## Done Definition

This subsystem refactor batch is done only when:

- projectile plan done definition is satisfied;
- actor AI plan done definition is satisfied;
- root acceptance criteria are checked;
- `PROGRESS.md` contains `## Done definition satisfied: YES`.
