# Acceptance Criteria

## Authoritative Loop

- [x] `implementation_plan.md` is the active authoritative plan for this overnight loop.
- [x] `PLAN.md`, `TASK_QUEUE.md`, `PROGRESS.md`, `AGENTS.md`, and `scripts/run_refactor.sh` point to the same loop.
- [x] `TASK_QUEUE.md` is concrete enough for autonomous execution without reading the plan linearly.

## Structural Acceptance

- [ ] Shared gameplay fixes are implemented in shared gameplay systems unless the behavior depends on BLV/ODM world
  representation.
- [ ] Indoor/outdoor-specific changes are limited to world hooks, data collection, collision/picking/LOS/floor facts,
  map loading, geometry, mechanisms, decals, and world collision.
- [ ] No new callback bag, forwarding adapter, or duplicate indoor/outdoor gameplay path is introduced only to hide
  ownership.
- [ ] No OpenEnroth or mm_mapview2 code is copied.
- [ ] Temporary diagnostics, noisy logs, local debug spawn skips, and profiling-only branches are removed before a task
  is marked done.

## Feature Acceptance

- [ ] Lloyd's Beacon has a shared gameplay implementation, save data support, and the requested YML-driven screen.
- [ ] Wands can be equipped and fired through the shared attack/spell action path, consume charges, and handle empty
  charges correctly.
- [ ] Recharge Item targets wand items and restores charges according to spell skill/mastery behavior.
- [ ] Inventory item mixing supports valid potion/reagent combinations and invalid-combination reactions.
- [ ] Summon Wisp creates one wisp per cast and respects the summon limit.
- [ ] Monster faction/relation overrides work for authored special actors such as the out05 Dragon Hunter Pet case.
- [ ] Unique actor guaranteed drops work for authored special actors such as Jeric Whistlebone.
- [ ] Save game and load game screens display saved screenshot previews consistently.
- [ ] Dungeon transition dialogue uses the shared dialogue/video screen path and consumes MoveToMap transition data.

## Indoor Parity Acceptance

- [ ] Indoor-only spell restrictions are enforced through shared spell rules, not duplicated UI/world checks.
- [ ] Prismatic Light works indoors with correct victim collection, damage rules, and FX.
- [ ] Soul Drinker works indoors through shared spell logic with indoor-specific victim collection only where needed.
- [ ] Indoor Lua/status text events display through the shared status bar path.
- [ ] Indoor face/decor/event dialogue activation opens the shared dialogue/house/NPC UI path.
- [ ] Indoor save/load preserves spawned actors, placed actors, corpse state, NPC animation state, mechanisms, and
  relevant runtime data.
- [ ] Indoor non-lethal actor damage shows appropriate hit reaction when it is not blocked by dying/dead/active attack
  state.
- [ ] Indoor projectile damage, impact FX, impact status text, corpse loot, world-item inspect/identify/repair, and
  outlines behave through the same shared gameplay services as outdoor.

## Validation Acceptance

- [ ] `cmake --build build --target openyamm_unit_tests -j25`
- [ ] `ctest --test-dir build --output-on-failure`
- [ ] `cmake --build build --target openyamm -j25`
- [ ] Relevant doctest coverage is added or updated for pure gameplay logic changed in this loop.
- [ ] Relevant focused headless coverage is added or updated for map/runtime behavior that cannot be unit-tested.
- [ ] Manual smoke notes are recorded in `PROGRESS.md` for behavior that cannot be validated headlessly.
- [ ] Any intentionally deferred issue is recorded in `PROGRESS.md` with the reason it was not safe to continue.

## Done Definition

This loop is done only when:

- the executable queue in `TASK_QUEUE.md` has no unfinished high-priority tasks;
- implemented gameplay fixes respect the shared indoor/outdoor architecture;
- build, unit, and relevant focused runtime validation evidence is recorded in `PROGRESS.md`;
- root `PROGRESS.md` contains `## Done definition satisfied: YES`.
