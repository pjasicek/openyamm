# Plan

## Objective

Refactor the current shared gameplay state for two subsystems:

- projectile service: `docs/projectile_service_moderate_refactor_plan.md`
- shared actor AI: `docs/actor_ai_shared_refactor_plan.md`

The runtime-boundary extraction is treated as the architectural baseline. These
subsystem refactors must respect that boundary:

- shared gameplay owns decisions;
- active world owns world facts and world-specific application;
- no callback bags or thin adapters that only hide ownership.

## Current Priority

1. Projectile service moderate refactor.
2. Shared actor AI refactor.

Projectile comes first because it is smaller, more mechanical, and establishes
the facts/result exchange style before actor AI uses the same pattern at a
larger scale.

## Projectile Target

The projectile frame should converge to:

```cpp
ProjectileFrameFacts facts = world.collectProjectileFrameFacts(projectile, deltaSeconds);
ProjectileFrameResult result = projectileService.updateProjectileFrame(projectile, facts);
world.applyProjectileFrameResult(projectile, result);
```

Shared projectile service owns projectile gameplay decisions. Active world owns
collision facts and application to ODM/BLV representation.

## Actor AI Target

The actor AI frame should converge to:

```cpp
ActorAiFrameFacts facts = world.collectActorAiFrameFacts(deltaSeconds);
ActorAiFrameResult result = actorAiSystem.updateActors(facts);
world.applyActorAiFrameResult(result);
```

Shared actor AI owns behavior decisions. Active world owns actor storage,
active-list construction, LOS, movement/collision, and result application.

## Anti-Goals

- Do not copy OpenEnroth code.
- Do not merge indoor/outdoor world representations.
- Do not create callback bags as a replacement for micro-structs.
- Do not rewrite behavior unless fixing a clear bug.
- Do not move terrain, BLV sectors, collision, LOS, or renderer internals into
  shared gameplay.

## Rules

- Use `TASK_QUEUE.md` as the executable queue.
- Use the relevant subsystem plan for detailed instructions.
- Finish one coherent slice before starting another.
- Keep behavior unchanged unless the task explicitly fixes a bug.
- Keep the repository buildable after each meaningful slice.
- Update `PROGRESS.md` after each meaningful slice.
