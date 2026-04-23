# Acceptance Criteria

## Authoritative Plan

- [ ] `docs/headless_to_doctest_migration_inventory.md` is the active authoritative source for this loop.
- [ ] `TASK_QUEUE.md` is aligned with the inventory and drives execution by coherent migration batches.
- [ ] `PROGRESS.md` records moved cases, remaining blockers, and validation evidence after each meaningful slice.

## Structural Acceptance

- [ ] Remaining `doctest-direct` cases are steadily moved into `tests/` instead of remaining in headless by inertia.
- [ ] `doctest-with-adaptation` migrations use small reusable test seams or fixtures, not broad fake application layers.
- [ ] Reusable helpers extracted from `HeadlessOutdoorDiagnostics.cpp` are moved to test-friendly locations when needed
  by more than one migrated case.
- [ ] `stay-headless` cases remain headless unless their classification is intentionally re-evaluated and documented in
  `PROGRESS.md`.
- [ ] Headless condensation, when applied, preserves failure identity and does not hide which logical scenario failed.
- [ ] No OpenEnroth or mm_mapview2 code is copied.

## Suite-Shape Acceptance

- [ ] The doctest suite materially grows from the current baseline.
- [ ] The headless suite materially shrinks from the current baseline, except for cases explicitly recorded as still
  needing integration coverage.
- [ ] The execution cost of common validation shifts toward `openyamm_unit_tests` and away from full headless runs.
- [ ] Any remaining headless cases grouped into a condensed session are still individually named or individually
  reported on failure.

## Behavioral Acceptance

- [ ] Every migrated case preserves the original assertion intent.
- [ ] A headless case is removed only after equivalent doctest coverage or a documented replacement exists.
- [ ] Test-specific seams do not change gameplay behavior in production builds.
- [ ] No migrated test silently weakens coverage from integration behavior to a narrower unit assertion without that
  reduction being documented in `PROGRESS.md`.

## Validation Acceptance

- [ ] `cmake --build build --target openyamm_unit_tests -j25`
- [ ] `ctest --test-dir build --output-on-failure`
- [ ] `cmake --build build --target openyamm -j25` when headless code or shared runtime test seams change
- [ ] targeted headless validation for batches that still touch headless diagnostics or integrated behavior

## Done Definition

This loop is done only when:

- all remaining `doctest-direct` inventory items are moved or explicitly reclassified with reason;
- the highest-value `doctest-with-adaptation` families have been migrated or are blocked with concrete seam needs;
- the remaining headless suite is intentionally integration-level rather than a mixed bag of pure logic checks;
- validation evidence is recorded in `PROGRESS.md`;
- `PROGRESS.md` contains `## Done definition satisfied: YES`.
