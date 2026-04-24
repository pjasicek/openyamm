# Progress

## Current status

- Overall completion: new overnight missing-features/bugfixes loop initialized.
- Current focus: BUG1, stabilizing active indoor combat hit reactions and confirming the correct owner for any
  remaining missing reaction behavior.
- Hard blocker: NO

## Done definition satisfied: NO

## Authoritative source

- `implementation_plan.md`

## Chosen migration order

1. Stabilize active indoor combat regressions and validate hit reactions.
2. Stabilize indoor corpse/world-item interaction parity.
3. Fix indoor event/status/dialogue activation gaps.
4. Implement shared wand attack behavior.
5. Implement Recharge Item and inventory item mixing.
6. Implement Lloyd's Beacon.
7. Implement remaining spell gaps: Summon Wisp, Prismatic Light, Soul Drinker, and indoor-only spell gates.
8. Implement monster relation overrides and unique actor guaranteed drops.
9. Implement save screenshot preview and dungeon transition dialogue.
10. Implement indoor save/load parity.
11. Cleanup, validation, and closeout.

Reason:

- active regressions should be removed before adding larger feature state;
- shared item/spell/combat mechanics should be implemented once before indoor-specific parity depends on them;
- save/load should be handled after the relevant runtime state is stable enough to serialize.

## First ownership leaks to attack

- Indoor actor hit reaction still risks living as indoor-only damage glue. Confirm whether the rule belongs in shared
  combat and leave indoor responsible only for applying world actor animation state.
- Indoor corpse/world-item interaction still risks diverging from outdoor. The shared item/interaction service should
  decide inspect, identify, repair, pickup, transfer, and loot actions; indoor should only supply hit facts and mutate
  BLV runtime storage.
- Indoor status/dialogue activation still risks bypassing shared UI. Event activation should feed shared status text
  and dialogue systems, with indoor only resolving faces/decor/mechanisms/events.
- Wand, Recharge Item, item mixing, Lloyd's Beacon, and spell gating are shared gameplay features and should not be
  implemented under outdoor or indoor views.

## Validation baseline

Default:

```bash
cmake --build build --target openyamm_unit_tests -j25
ctest --test-dir build --output-on-failure
cmake --build build --target openyamm -j25
```

Focused validation should be selected by the task:

- doctest/unit tests for pure item/spell/combat decision logic;
- focused headless tests for map/runtime/save/event behavior;
- manual BLV/ODM smoke notes only for behavior that cannot be validated automatically.

## Current slice evidence

- 2026-04-25: Reset the wiggum-loop control docs to the overnight missing-features/bugfixes loop.
- 2026-04-25: `implementation_plan.md` is now the authoritative detailed source.
- 2026-04-25: `TASK_QUEUE.md` defines the executable order and first concrete ownership leaks.
