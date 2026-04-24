# Plan

## Objective

Execute the overnight missing-features and bugfix loop from `implementation_plan.md` in coherent, reviewable slices.
The target is not broad architecture churn; it is closing concrete gameplay gaps while preserving the shared
indoor/outdoor ownership model.

Authoritative detailed plan:

- `implementation_plan.md`

Executable queue:

- `TASK_QUEUE.md`

## Current Scope

This loop covers the missing gameplay features and regressions currently blocking indoor/outdoor parity work:

- shared spell/item feature gaps such as Lloyd's Beacon, wands, Recharge Item, item mixing, Summon Wisp, monster
  relations, unique actor drops, save screenshot handling, and dungeon transition dialogue;
- indoor parity gaps such as disabled-indoor spell gates, Prismatic Light, Soul Drinker, status text from events,
  dialogue activation, and save/load runtime state;
- active indoor combat and interaction regressions discovered during BLV work, including hit reactions, projectile
  impact feedback, corpse/world-item interaction, actor picking/outline behavior, and event/mechanism behavior.

## Architecture Rules

- Treat shared gameplay as shared by default.
- Do not add indoor-only or outdoor-only gameplay fixes unless the behavior truly depends on BLV/ODM world data.
- Prefer fixing shared gameplay services or active-world hooks over adding branches to `IndoorGameView` or
  `OutdoorGameView`.
- Keep world-specific code limited to map loading, geometry, visibility, picking, LOS, collision, floor resolution,
  movement integration, projectile collision against world geometry, mechanism/event/decor lookup, and decal placement.
- Do not add adapter/callback layers that only hide duplicated ownership.
- Use local OpenEnroth only as a behavioral reference. Do not copy code.

## Execution Rules

- Do not execute `implementation_plan.md` linearly.
- Use `TASK_QUEUE.md` as the executable migration order.
- Work one coherent task or tightly related micro-batch at a time.
- Update `PROGRESS.md` after each meaningful slice with behavior changed, files touched at a high level, validation,
  and residual risk.
- Update `ACCEPTANCE.md` only when criteria are actually satisfied.
- Prefer doctest/unit coverage for pure logic. Use headless tests for runtime/map behavior that cannot be isolated.
- Remove temporary diagnostics, noisy logs, and profiling hooks before considering a slice done.

## Validation

Default validation after runtime C++ changes:

```bash
cmake --build build --target openyamm_unit_tests -j25
ctest --test-dir build --output-on-failure
cmake --build build --target openyamm -j25
```

Focused validation should match the touched subsystem:

- spell/item logic: unit tests first, then focused headless spell/item coverage if available;
- indoor world behavior: focused indoor headless coverage where possible, plus manual BLV smoke notes in `PROGRESS.md`;
- dialogue/save/event behavior: focused headless coverage where available;
- performance-sensitive fixes: capture the relevant `gprof.txt` observation before and after only when performance is
  the task.

## Anti-Goals

- Do not run a broad cleanup/refactor without a direct bugfix or feature target.
- Do not duplicate outdoor gameplay paths into indoor.
- Do not add speculative rendering/physics rewrites while implementing unrelated gameplay features.
- Do not leave debug behavior enabled by default.
