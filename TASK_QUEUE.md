# Task Queue

## Execution Rules

- Use this file as the executable queue.
- Use `docs/headless_to_doctest_migration_inventory.md` as the authoritative classification source.
- Do not execute the inventory linearly from top to bottom.
- Work in coherent batches by fixture family or subsystem.
- Prefer moving `doctest-direct` cases first.
- For `doctest-with-adaptation`, extract the smallest seam that unlocks multiple cases.
- Keep changes coherent and reviewable.
- Keep the repository buildable after each meaningful slice.
- Run `cmake --build build --target openyamm_unit_tests -j25` after each meaningful doctest migration slice.
- Run `ctest --test-dir build --output-on-failure` after each meaningful doctest migration slice.
- Run `cmake --build build --target openyamm -j25` and targeted headless validation when headless code changes.
- Update this file and `PROGRESS.md` after each meaningful slice.
- Do not weaken assertion scope silently.
- Do not copy OpenEnroth code.

## Current Migration Order

1. TS1 - Lock the execution loop to the inventory and record current counts/baseline.
2. TS2 - Move the remaining `doctest-direct` chest, item-use, character-sheet, and equip-rule cases.
3. TS3 - Move the remaining `doctest-direct` navigation, recovery, experience, audio-safety, and simple event-rule
   cases.
4. TS4 - Extract reusable Arcomage doctest harnesses and migrate the Arcomage `doctest-with-adaptation` set.
5. TS5 - Extract reusable spell backend / fake-world fixtures and migrate spell backend cases.
6. TS6 - Extract reusable house/dialogue fixtures and migrate the highest-value dialogue/service cases.
7. TS7 - Re-evaluate remaining headless suites and condense startup/session cost where it does not blur failure
   identity.
8. TS8 - Recount doctest/headless distribution, remove obsolete duplicated headless cases, and close acceptance.

## Ready

### TS1 - Inventory Lock And Baseline

- [ ] Confirm `docs/headless_to_doctest_migration_inventory.md` is the active source of truth.
- [ ] Record the current inventory counts in `PROGRESS.md`:
  - remaining `doctest-direct`
  - remaining `doctest-with-adaptation`
  - remaining `stay-headless`
- [ ] Record the current test entry points and default validation commands in `PROGRESS.md`.
- [ ] Identify the first concrete `doctest-direct` family to migrate.
- [ ] Build only if code changed.
- [ ] Update `PROGRESS.md`.

### TS2 - Direct Migration Batch A

- [ ] Move a coherent batch of remaining `doctest-direct` cases into `tests/`.
- [ ] Prefer chest, item-use, character-sheet, equip-rule, and similar deterministic rule checks first.
- [ ] Keep migrated tests grouped in sensible files; do not dump unrelated checks into one giant file.
- [ ] Remove the migrated headless cases or mark them inactive once equivalent doctest coverage exists.
- [ ] Build `openyamm_unit_tests`.
- [ ] Run ctest.
- [ ] If headless definitions were touched, build `openyamm`.
- [ ] Update `PROGRESS.md`.

### TS3 - Direct Migration Batch B

- [ ] Move another coherent `doctest-direct` batch.
- [ ] Prefer navigation-rule, recovery, experience, simple event-rule, and audio-safety checks.
- [ ] Reuse fixtures created in TS2 where practical.
- [ ] Remove or deactivate superseded headless cases.
- [ ] Build `openyamm_unit_tests`.
- [ ] Run ctest.
- [ ] If headless definitions were touched, build `openyamm`.
- [ ] Update `PROGRESS.md`.

### TS4 - Arcomage Adaptation Batch

- [ ] Extract a small reusable Arcomage test harness from headless diagnostics or equivalent shared helper.
- [ ] Migrate multiple Arcomage `doctest-with-adaptation` cases in one coherent slice.
- [ ] Keep card-effect expectations readable and local to the tests.
- [ ] Remove or deactivate superseded headless cases.
- [ ] Build `openyamm_unit_tests`.
- [ ] Run ctest.
- [ ] Build `openyamm` if headless harness code changed.
- [ ] Update `PROGRESS.md`.

### TS5 - Spell Backend Adaptation Batch

- [ ] Extract a minimal fake/shared world runtime fixture for spell backend tests.
- [ ] Migrate the spell backend `doctest-with-adaptation` cases that do not require full authored map integration.
- [ ] Keep projectile/world assertions limited to what the backend actually owns.
- [ ] Keep full map/runtime projectile integration headless when still needed.
- [ ] Build `openyamm_unit_tests`.
- [ ] Run ctest.
- [ ] Build `openyamm` if headless or shared test seams changed.
- [ ] Update `PROGRESS.md`.

### TS6 - House / Dialogue Adaptation Batch

- [ ] Extract reusable house/dialogue fixtures only where they unlock multiple cases.
- [ ] Migrate a coherent subset of house/dialogue `doctest-with-adaptation` cases.
- [ ] Keep real map-script and application-lifecycle dialogue cases headless when required.
- [ ] Remove or deactivate superseded headless cases.
- [ ] Build `openyamm_unit_tests`.
- [ ] Run ctest.
- [ ] Build `openyamm` if headless code changed.
- [ ] Update `PROGRESS.md`.

### TS7 - Headless Condensation

- [ ] Audit remaining `stay-headless` suites for startup/session duplication.
- [ ] Condense only where multiple assertions can share one session without weakening per-case identity.
- [ ] Preserve clear case naming and failure reporting.
- [ ] Do not collapse unrelated world/application scenarios into one opaque mega-case.
- [ ] Build `openyamm`.
- [ ] Run targeted headless validation for condensed groups.
- [ ] Update `PROGRESS.md`.

### TS8 - Final Recount And Cleanup

- [ ] Recount doctest/headless totals against the inventory.
- [ ] Remove dead migrated headless cases and dead helper code.
- [ ] Verify remaining headless cases are truly integration-level.
- [ ] Update `ACCEPTANCE.md`.
- [ ] Set `PROGRESS.md` to `## Done definition satisfied: YES` only when acceptance is satisfied.
