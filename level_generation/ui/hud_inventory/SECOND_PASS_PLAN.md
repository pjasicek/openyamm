# Second pass: inspect retained artwork, stage passing assets, prepare specific repairs

Created 2026-09-22 at the user's request. This is the consolidated plan for the next restoration pass;
creating it does not start review, image generation, session assignments or runtime installation.

## Objective and scope

### Scope correction — runtime usage first (2026-09-22)

The user superseded the whole-folder restoration scope: do not restore unused MM6/MM7 interface artwork,
menu text or texture leftovers merely because they exist in an icons directory. First audit actual shared
tables, authored UI and runtime lookups. Preserve needed NPC portraits, inventory/world items and map
presentation. Data-driven player portraits, paperdolls and fitted equipment remain protected while their
actual consumer reachability is checked; a `6`/`7` filename prefix alone is not an exclusion.

`review/second_pass/usage_scope.json` is the current usage-gating overlay. Its per-file evidence and
`USAGE_SCOPE.md` take precedence over old whole-folder assignments. The historical census, decisions,
raw masters, frozen submissions and existing acceptance records remain audit history, not a work mandate.
No more visual review until the usage audit has resolved which remaining families merit restoration.
Unknown usage is a usage-audit hold, not a claim of disuse. Same-name byte-identical aliases share restoration
work without automatically accepting their destination contracts. Physical deletion/consolidation requires
checking explicit paths, mounted-package availability, scaled tiers and data-derived/binary references.
Do not delete world textures, sprites, maps or source icons based on a filename/prefix or missing text match.

The original 1,882-file hold cohort is now resolved for restoration selection in
`review/second_pass/usage_hold_review.json`: 1,829 current-scope exclusions and 53 protected dynamic
context/fallback button states. There are zero remaining usage holds in this census. This is not a claim
that all conservatively retained reference candidates are reachable, or authorization to delete native files.
The exact-path/hash review is bounded to that cohort; new unknown assets still require a fresh usage audit.

Review every unfinished retained result in the engine/world `icons/` restoration inventory, including older
returns and experiments, not only the latest sessions. Produce verified exact-x2 exports where the artwork
passes, and actionable repair or investigation records everywhere else. Include HUD controls, buttons and
states, spell icons, portraits, inventory/equipment art, UI animations, panels, pages and backgrounds according
to their own contracts. Folder coverage is broader than the currently visible HUD.

A generated master is not a restored asset. A completed second-pass review is not necessarily an accepted asset.
Keep those counts separate. Existing valid acceptances and staged files survive; review their dependencies and
provenance, reopening artwork only for demonstrated defects or invalidated evidence.

User clarification, 2026-09-22: continue the full review so every original icon is checked in some way, primarily
for warping, enlarged/pixelated source detail, correct width-to-height ratio and logical direct-replacement fit.
Perform whole-inventory technical checks as well as visual screening; do not let ornamental exactness displace
these practical priorities. Publish the technical coverage separately from individual visual review and canonical
readiness. A correct exported rectangle does not prove correct internal proportions. Retained raw art without a
verified extraction remains unresolved, not visually approved because its source file passed a dimension check.

Use [MATTE_AND_FITTING.md](MATTE_AND_FITTING.md) for visual/registration/compositing requirements,
[QUEUE.md](QUEUE.md) for actual acceptance/reconstruction/staging APIs and
[BATCHING_DENSE64.md](BATCHING_DENSE64.md) for any later generation packing. Older nine-cell defaults in
historical goal/queue prose are superseded by Dense64. The first-pass permission to generate before pilot/seed
acceptance does not waive acceptance dependencies. C++ changes do not invalidate queue inputs.

## Keep good artwork: severity-based review

User clarification, 2026-09-22: **keep artwork whose overall quality is good/high when its differences are minor
and are not obvious bugs or artifacts.** Faithfulness does not mean pixel-perfect duplication of decorative detail.
This instruction takes precedence over stricter historical wording that treats every changed mark as a repair.

Judge the result first at its intended UI display size, then at exact x2. Inspect raw 1:1 for actual pixelation,
edge contamination and artifacts, not to manufacture objections to otherwise good artwork. Native comparisons
establish identity, meaning, placement and state behavior; they are not a demand to reproduce every texture fleck.

| Severity | Examples | Decision |
| --- | --- | --- |
| Acceptable variation | Different fine grain, cloth folds, hair strands, brushwork, tiny nonsemantic ornament, or slight shading differences; artwork remains coherent, recognizable and fits its intended use | KEEP. Optionally note `acceptable_variation`; do not create a repair task or block acceptance for this difference. |
| Material defect | Obvious malformed/extra/missing parts, corrupted text or meaningful symbols, changed character/item identity, lost button-state distinction, visible seams/halos, clipped artwork, wrong placement/scale, or distracting unintended palette/style mismatch | REPAIR the identified problem. Explain the visible or functional impact. |
| Failed restoration | Enlarged pixel blocks, mosaic shading, insufficient actual sampling, severe distortion or unusable composition | REJECT the candidate; retain evidence for targeted regeneration. |

A first-pass `needs_repair` label is a finding to reassess, not an automatic second-pass failure. Downgrade harmless
differences to acceptable variation and keep the candidate. Reuse candidates inherit the reviewed donor's quality
judgment but still need destination checks. Reassess family holds whose only evidence is minor acceptable variation;
do not retain such a hold solely because an earlier reviewer demanded decorative exactness.

No fixed acceptance/rejection quota applies. Each repair must name a meaningful visual or functional problem,
not merely say that the generated image differs from the source. If a numeric guard flags harmless contour/detail
variation, inspect whether the measurement actually tracks a stable placement feature. Never invent coordinates
or falsely claim canonical acceptance: if the current validator still prevents an otherwise acceptable result,
record `candidate_pending_acceptance` with a specific validator-policy issue for explicit reconciliation. Do not
send good art for regeneration just to satisfy a measurement unrelated to a real defect.

## Starting inventory and authoritative evidence

Build the review inventory from these sources together:

- `expected_targets.json` and `jobs.json`: namespaced IDs, native baselines, canvas/regions, treatment,
  consumer profiles, placement and dependency contracts.
- `checkpoint/state.json`: attempts, accepted cells, staging, deferrals, exclusions, submission holds and
  `restoration_inventory`. Read live state; do not replace it with historical catalogue flags.
- [Chat bundle index](CHAT_BUNDLES.md): older retained returns, experiments and imported session ledgers.
- [Session 2 next 1,000](chat_bundles/remaining_icons_dense_v2_20260922/runs/restore-part-2/v5-next-1000/processed/STATUS.md)
  and [session 4 next 271](chat_bundles/remaining_icons_dense_v2_20260922/runs/restore-part-4/v5-next-271/processed/STATUS.md):
  latest canonical imports, per-cell observations, unresolved checks and donor links.
- `output/restoration_handoff_v3/ownership.json` from the repository root: historical owners. Reconcile them
  before reserving second-pass work; first-pass ownership is not evidence of an active worker.

The 2026-09-22 audit found 913 quality-held assets without a generated result, 101 tool/uncertain cases,
two other ungenerated deferrals and 879 user-skipped MM9 inventory/doll assets. Two further oversized assets,
`engine--icons--seg_scrl.pcx` and `engine--icons--title.png`, require a demonstrated larger-output approach.
These are starting context, not live totals or review completion. Recompute counts when preparing assignments.
The latest 147 masters cover 1,037 directly generated cells; they are only part of the retained inventory.

Preserve MM9 skips. Keep reuse candidates distinct from independent generations, and keep failed/uncertain calls
distinct from unsubmitted family holds. A held cell with a donor ID but no raw image remains held.

## Work order and assignment preparation

1. Reconcile all source, raw, prompt and receipt links before distributing work. Select the best evidenced
   candidate per cell for review, retaining every alternative/rejected attempt and the selection reason.
   Do not assume the latest attempt is best. Resolve unknown slot identity before exporting it.
2. Triage known failed masters and investigate a representative result from each held family. This identifies
   specific defects and repair experiments; it does not accept uninspected siblings or reopen a whole family.
3. Review retained dependency artwork early: page/background layers, portrait identity seeds and treatment
   pilots that unlock acceptance of many followers. Followers may still be inspected while dependencies remain
   unresolved; record that separate blocker rather than stopping the review queue.
4. Prioritize shared HUD/buttons and their complete states, then associated foreground animations and spell
   groups. Continue through portraits, inventory/equipment variants, other panels/backgrounds and legacy art.
   Include every remaining in-scope target regardless of this priority order.
5. Review donor artwork once, then validate each destination's own consumer, namespace, placement and dependency
   contract. Source equality alone does not authorize cross-namespace reuse or bypass canonical reuse limits.

Prepare `review/second_pass/` when execution starts, with a timestamped inventory snapshot, exclusive per-cell
assignments, family/context links and worker status files. Snapshot counts must account for accepted/staged,
retained pending review, reuse candidates, no-return holds, exclusions and oversized work without double-counting.
Keep attempt counts, cell/atlas-region counts and unique target/file counts separate.

Review assignments are organized by retained master and related family, with explicit selected cells and
context-only siblings. Size assignments by expected inspection effort; a large background is not equivalent
to a tiny button. Do not repack images merely to inspect them. Do not claim all retained cells in a frozen job
when only a subset is assigned. Unresolved work gets a named next action and remains unfinished.

## Per-cell review procedure

### Player-portrait family review — user direction after checkpoint 1,157

Prepare **all table-referenced character portrait families** before further portrait analysis. Use the
`character_data.txt` face-prefix column and `portrait_frame_data.txt` texture indices, including non-`pc`
prefixes. Review an entire character's expressions coherently using paired native/candidate exact-x2 sheets
and a frame viewer; individual inspection is for suspicious exceptions, not repetitive notes for every frame.
The preparation entry point is `prepare_portrait_families.py`; the gallery is
`review/second_pass/portrait_families/index.html`. `validate_portrait_families.py` checks coverage, source/raw
hashes and every pasted diagnostic pixel. These checks do not decide artwork quality.

Whole-family visual findings may be recorded against all explicitly included frames, with an exception list.
No family approval can silently clear missing mappings, insufficient sampling, unresolved native placement,
known repair findings or acceptance dependencies. Preserve all alternative/raw evidence and previous decisions.
Current request is **collection/preparation only**, not analysis, new generation or canonical acceptance.
Provisional raw views retain aspect using uniform downsampling and padding; they are not fitted exports.
The numeric-order slideshow is a diagnostic viewer, not game animation timing or a runtime validation.

| Check | Required evidence and failure handling |
| --- | --- |
| Provenance and extraction | Verify native and raw hashes, exact submitted prompt and selected-cell mapping. Inspect the complete master for missing, duplicated, reordered or merged slots. Locate actual returned full-canvas rectangles; do not trust uniform grid ratios alone. Save raw crop coordinates and extraction parameters. |
| Actual sampling | Measure returned canvas dimensions against the native region in both axes, and inspect internal subject scale. Require at least 2 actual generated pixels per native pixel in both axes. Empty padding, interpolation or later upscaling cannot repair insufficient sampling. |
| Genuine restoration | Inspect raw detail at 1:1 and final exact-x2 appearance alongside native references. Reject enlarged source-pixel blocks, stair steps, tiled/mosaic shading, blur/sharpen-only processing and coarse faceted replacements. Preserve intentional sharp symbols, flat colors and painted marks. Smooth artwork still fails if it changes recognizable identity, meaning or intended function; harmless decorative variation is allowed. |
| Fidelity and artifacts | Check silhouette, identity, expression, age/gaze, part count, holes, thin lines, lettering/glyphs, ornament, palette, materials and lighting. Distinguish harmless variation from materially invented/missing features, corrupted text, obvious texture artifacts and neighbor contamination. Record specific locations and visible impact for failures. |
| Registration | Preserve complete native canvas, margins and anchors; no trimming/recentering or fitting to alpha bounds. Run canonical comparisons and measure actual internal landmarks. Matching an opaque rectangle does not prove matching face/icon scale. |
| Compositing | Inspect alpha on light/dark backgrounds and the intended panel. Remove unwanted copied backing only for separable foregrounds; preserve their own materials and complete opaque backgrounds. Check halos, matte spill, painted checkerboards, holes, glass/glow edges and every indexed/key consumer profile. |
| Family consistency | Compare normal/hover/pressed/selected/disabled states actually present, animation sequences, portrait expressions and equipped variants together. Preserve timing, pose differences and alignment; reject flicker, altered identity and disappearing details. |
| Composition and destination | Check foregrounds against their restored page/panel, equipment against its doll/pose, and atlas regions in the full canvas. Validate every reuse destination separately. Record unresolved dependencies even when local visual checks pass. |

Generate native-at-x2, restored-at-x2, overlay and native-logical-size comparison images. Preserve raw 1:1
problem crops and highlight the exact defect locations. Contact sheets help navigation but never substitute
for inspecting every final cell. Automated checks may detect dimensions, hashes and geometry failures;
they must not set visual approval fields automatically.

Use `queue.py compare` and its hash-bound registration records. Current canonical fitting guards include alpha-16/128
bounds and centroid within two x2 pixels, occupied area 90–110%, silhouette IoU at least 0.85, and at least three
spatially separated actual landmarks within two x2 pixels of their native doubled positions. Apply documented
font/uniform-region exceptions rather than inventing landmarks. These are rejection guards, not proof of fidelity.
Do not paste the native mask over misplaced art to make a candidate pass. Handle harmless guard failures through the explicit validator-policy reconciliation above.

## Classification and required records

Retain original first-pass classifications as historical evidence. Add a dated second-pass decision referencing
its candidate attempt, rather than silently replacing that history. Keep generation history, local review result,
acceptance dependency status, staging and runtime installation as separate fields.

Use existing review categories:

- `needs_review`: identify the exact remaining test, ambiguity or missing evidence and who/what can resolve it.
- `needs_repair`: name the material defect, visible/functional impact, affected region, evidence, intended correction and how the repair will be tested. Minor acceptable variation does not belong here.
- `rejected_pixelation`: no acceptable reconstructed detail; retain raw evidence and plan a genuine regeneration.
- `candidate_pending_acceptance`: local visual/geometry/compositing checks passed, but named dependency or canonical
  acceptance evidence is still outstanding. Do not use this for an uninspected candidate.
- `accepted`: only after the canonical acceptance operation succeeds with genuine evidence.

For each cell record: target/cell ID, native source hash, candidate attempt/raw hash, actual crop, measured sampling,
final candidate path/hash, source/return comparison paths, registration measurements, individual check results,
observed material defects, acceptable variations (optional), follow-up types, precise next action, related family/dependency IDs, donor provenance if any,
reviewer/run identity and date. Preserve generation status and holds for cells with no image to inspect.

Use the established follow-up tags: `detail_at_x2`, `sampling`, `slot_extraction`, `native_geometry`, `identity`,
`variant_consistency`, `animation_consistency`, `ornament_fidelity`, `alpha_matte`, `page_composition`, `palette`,
`dependency_acceptance`, `missing_source`, `tool_block` and `submission_reconciliation`. Record specific text
beneath the tags: “needs individual review” alone is not a completed second-pass decision.

## Passing artwork, repairs and holds

For passing cells, complete real `identity`, `registration`, `compositing`, `detail_at_x2` and
`state_or_animation_consistency` evidence, satisfy current dependencies, then use canonical `accept`.
Reconstruct complete targets, inspect the full canvases/joins and use canonical `stage` with full-canvas evidence.
Keep staged exports separate from runtime installation. A target is ready to use only when its required regions,
states and dependencies pass—not because one region was accepted.

For failed results, prepare the third-pass repair queue grouped by compatible treatment, defect and native family:

- Extraction/cleanup errors: first determine whether retained detail can be preserved through corrected processing.
- Material geometry/design/detail failures: specify targeted regeneration using native authority plus the failed comparison.
- Quality-held families: inspect failed evidence and prepare a small representative correction experiment. Generate
  the unattempted remainder only after the correction is demonstrated. Held cells remain first generations, not repairs.
- Tool/uncertain cases: reconcile receipts and recover an existing return if available. Preserve terminal rejection
  records; no automatic retry or prompt changes intended to evade a rejection.
- Oversized assets: require measured feasible output sampling; never shrink the source or upscale an inadequate return.

Third-pass generation is a separate execution step. Use the imagegen skill when it is started. Pack at most 64
compatible selected targets, fewer as native size requires, with at least 2.15 predicted sampling under the measured
pixel budget. Preserve complete native canvases and appropriate paired states. Carry exact repair notes per cell;
do not bulk-regenerate good siblings. Inspect each repair against both native and previous evidence before continuing
the recipe. If it fails again, record what failed and the next experiment rather than repeatedly cycling unchanged work.

## Publication, validation and finish criteria

Publish a searchable `review/second_pass/index.html`, machine-readable inventory, CSV, per-cell evidence,
repair batches (preparation only), hold investigation list, status report and an accepted/staged manifest link.
These are planned deliverables, not files claimed to exist at plan creation.

For shared updates, acquire `checkpoint/state.lock`, reload Queue inside the lock, change only owned records and
save promptly. Never hold the lock during visual review or image generation. Preserve previous acceptances,
raw masters, exact prompts and original contracts. Do not regenerate frozen inventories or silently amend submitted
payloads. Resolve actual source/reference drift explicitly; descriptive consumer C++ edits are not input drift.

Validate unique ownership, complete scope accounting, unchanged source/retained hashes, actual crop mappings,
export dimensions and links to all claimed evidence. Run focused queue/registration checks appropriate to changed
processing; this is asset work, not an engine rebuild. Use isolated representative UI previews for layout, attachment,
state/animation and picking validation of staged families, following QUEUE.md and repository capture instructions.
Do not install into normal runtime assets or treat successful screenshot capture as visual approval.

The second pass is complete when:

1. Every in-scope retained candidate has an evidence-backed decision; no generic unperformed per-cell review remains
   hidden behind a claim of completion. Any genuinely unresolved case is listed as outstanding with its exact blocker.
2. Every accepted/staged claim has canonical evidence, and prior valid work is preserved.
3. Every repair has a specific defect, testable correction and selected-cell assignment ready for the next pass.
4. Every no-return hold has an investigated cause, evidence and explicit next action; skips remain visible.
5. Counts reconcile by unique asset as well as cell, and the report distinguishes reviewed, accepted, staged,
   repair-needed, unresolved, held, excluded and never-generated work.

A fully restored folder is a later completion condition: all non-excluded required assets accepted/staged and
composition checks passed. A completed classification ledger alone must never be reported as universal verified x2 art.
