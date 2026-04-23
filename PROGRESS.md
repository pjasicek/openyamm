# Progress

## Current status

- Overall completion: new Wiggum loop initialized for regression test suite refactoring.
- Current focus: migrate as many slow headless diagnostics as possible into fast doctest unit tests.
- Hard blocker: NO

## Done definition satisfied: NO

## Authoritative source

- `docs/headless_to_doctest_migration_inventory.md`

## Chosen migration order

1. Lock the loop to the headless inventory and record the baseline.
2. Exhaust the remaining `doctest-direct` families first.
3. Extract the smallest reusable fixtures needed for the highest-value `doctest-with-adaptation` families.
4. Only then optimize or condense the remaining headless coverage.
5. Close by recounting doctest/headless distribution and removing dead migrated headless cases.

Reason:

- the inventory already classifies what should move and what should stay;
- `doctest-direct` gives the best speedup for the least structural work;
- `doctest-with-adaptation` should be unlocked by a few reusable seams, not one-off hacks;
- headless condensation only makes sense after the pure/unit candidates are removed.

## Current baseline from inventory

- Original headless cases inventoried: 275
- Already moved to doctest: 19
- Remaining classified headless cases: 256
- Remaining `doctest-direct`: 40
- Remaining `doctest-with-adaptation`: 80
- Remaining `stay-headless`: 136

## First ownership / structure targets

- Move remaining `doctest-direct` cases out of `game/outdoor/HeadlessOutdoorDiagnostics.cpp` into `tests/`.
- Avoid duplicating test helpers in every doctest file; extract narrow reusable fixtures only when a family needs them.
- Treat `stay-headless` cases as intentionally integration-level until reclassified with explicit reason.
- If condensing headless sessions, preserve case identity and failure clarity.

## Expected first migration families

- chest / loot / item-use deterministic checks
- character-sheet / equip-rule checks
- recovery / experience / simple data-rule checks
- navigation-rule checks that do not require real map/world loading

## Validation baseline

Primary:

- `cmake --build build --target openyamm_unit_tests -j25`
- `ctest --test-dir build --output-on-failure`

Secondary when touching headless code:

- `cmake --build build --target openyamm -j25`
- targeted headless suite or targeted headless case relevant to the migrated batch

## Current slice evidence

- 2026-04-23: Reset `PLAN.md`, `ACCEPTANCE.md`, `TASK_QUEUE.md`, and `PROGRESS.md` to the test-suite refactoring loop.
- 2026-04-23: Set `docs/headless_to_doctest_migration_inventory.md` as the authoritative classification source.
- 2026-04-23: Replaced the old indoor-collision execution scaffolding in `scripts/run_refactor.sh` with the new
  test-suite migration loop prompt.
- 2026-04-23: Updated the last section of `AGENTS.md` so future refactor sessions follow the test-suite migration loop
  instead of the previous subsystem slices.
