# Plan

## Objective

Refactor the regression test suite so that as many current slow headless diagnostics as possible become fast doctest
unit tests, while preserving only the headless cases that truly need full application/world integration.

Authoritative detailed plan:

- `docs/headless_to_doctest_migration_inventory.md`

## Target

The end state should look like this:

- deterministic pure-rule, table, party, item, service, and small runtime checks live in `tests/`
- headless regression remains only for real integration scenarios:
  - application startup/lifecycle
  - real map/world loading
  - real BLV/ODM geometry and collision
  - save/load roundtrips
  - cross-map transitions
  - event-script execution that still requires full runtime wiring
- remaining headless execution is more condensed where safe:
  - multiple related assertions may run in one headless session only if that does not blur failure identity
  - if condensation would make failures ambiguous, keep separate cases

## Current Priority

1. Move the remaining `doctest-direct` cases first.
2. Extract the smallest reusable seams needed for `doctest-with-adaptation`.
3. Keep `stay-headless` cases headless, but reduce redundant startup/session cost where structurally safe.
4. Reduce total wall-clock regression time without weakening coverage identity.

## Migration Rules

- Use `TASK_QUEUE.md` as the executable queue.
- Use `docs/headless_to_doctest_migration_inventory.md` as the authoritative classification source.
- Do not execute the inventory linearly from top to bottom.
- Work in coherent batches by subsystem or fixture family.
- Prefer moving tests before inventing new headless helpers.
- Extract reusable test helpers only when they unlock multiple doctest migrations.
- Do not keep behavior assertions duplicated in both doctest and headless unless the headless version is still needed as
  a genuine integration smoke.
- Keep the repository buildable after each meaningful slice.
- Update `TASK_QUEUE.md` and `PROGRESS.md` after each meaningful slice.

## Validation

Primary validation:

- `cmake --build build --target openyamm_unit_tests -j25`
- `ctest --test-dir build --output-on-failure`

Secondary validation when headless code or migrated coverage is touched:

- `cmake --build build --target openyamm -j25`
- targeted headless suite or targeted headless case relevant to the migrated batch

## Anti-Goals

- Do not rewrite gameplay/runtime architecture just to move tests.
- Do not keep large callback bags or fake application layers only for tests.
- Do not condense headless coverage so aggressively that failures lose clear identity.
- Do not move real integration coverage out of headless when the inventory says it should stay there.
