# Preparation completion audit

The requested preparation objective is complete: classify the full source scope, finalize exact-x2 targets and
prepare resumable generation jobs. **No image generation was made during preparation.** This does not claim completion of GOAL.md's
subsequent artwork, export acceptance or restored in-game preview phases.

The artwork phase is now active; [ARTWORK_PROGRESS.md](ARTWORK_PROGRESS.md) and the live checkpoint supersede
this historical audit's zero-generation status. Its frozen manifest/source accounting remains unchanged.

## Requirements and evidence

| Preparation requirement | Authoritative evidence and result |
| --- | --- |
| Account for every recursive icon-root file | `scope.json` has 14,736 files. `audit_preparation.py` compares its paths with the current filesystem and checks one final classification per path. |
| Include dependencies outside the roots | 54 native MM9 map images, one authored dialogue background and the recovered native Shadow's Mask add 56 sources. Fonts and five generated/external categories have explicit owners. |
| Final dispositions, with no silent exclusions | `classification.json`: 14,780 restore targets, 12 retained non-target files. Unreferenced plausible UI remains included; the 12 exclusions have concrete documentation, replacement or loader-priority evidence. |
| Resolve missing names | Zero required missing sources. Four beard fields are metadata-only; seven pc30 fields are for the unavailable reserved character. The duplicate mobile `asiR08` dependency was removed and inventories reconciled. |
| Verify actual native baselines | `source_audit.json`, `import_audit.json` and `authored_audit.json` distinguish native files, authored native canvases and current MM9 promotions. The native mask override is 50x55. No existing file is claimed as accepted x2 artwork merely because it is generated or large. |
| Exact x2 for every state and variant | `expected_targets.json` freezes source/hash, native and exact-x2 canvases, namespace/output path and full-canvas origin. The audit checks all 14,780 targets and 14,966 scheduled region cells. |
| Preserve layout, aliases and fitting | Every YAML usage retains its ancestor/anchor chain; shared states have explicit aliases. Item/equipment bindings include native offsets and MM9 world-local rows. Five spell-state source canvases that differ from draw dimensions remain distinct. |
| Preserve animation and identity | Native raw durations, ticks, flags and expression mappings are frozen. Portraits use table-defined identities, including non-PC prefixes. Sequence and identity continuations require accepted seeds. |
| Preserve rendering and palette semantics | Native canvas/RGBA/palette/consumer fingerprints are retained. HUD, item, menu BMP and menu PCX keys differ; 2,223 multi-mask sources retain key/index-aware output contracts. No unverified generated sharing or reuse is approved. |
| Appropriate batching and exact prompts | `jobs.json`: 4,268 jobs, including 4,254 imagegen-sheet recipes and 14 deterministic jobs. Fixed cell rectangles, gutters, source references, cleanup rules, exact prompts, pilots and dependencies are prepared. Large backgrounds remain individual images. |
| Page-first spell icons | 222 states form 111 paired spells. Pairs stay adjacent; each depends on its actual accepted school page. Payloads retain page hashes, exact crop rectangles and context, with compact accepted-crop sheets. No draft page can satisfy the dependency. |
| Atlas completeness | All 102 active Arcomage card definitions have slot/name mappings. Four glyph regions and 66 uniform unused regions use deterministic jobs. Reconstruction covers the entire 1920x5000 canvas and preserves native RGB keys. |
| Resumable independent acceptance | `queue.py` retains raw masters, exact prompts and reference snapshots; locks CLI mutations; rejects stale input/state hashes; invalidates changed page/seed dependencies; and preserves accepted siblings when another cell is deferred. |
| Original and fidelity-reference inspection | `review/classification/visual_review.json` records inspected originals, native inventory screenshot, accepted decoration comparison and representative prepared sheets. Their role is faithful shape/material treatment, not approval of any generated art. |
| Verify the workflow without starting generation | Fourteen tests pass; see `review/classification/tests.log`. Synthetic fixtures validate page crops, concurrency, record/accept/defer/resume and complete atlas reconstruction in temporary checkpoints. `completion_audit.json` records the full structural audit and artifact hashes. |

The frozen inputs retain namespaced engine/world copies. Byte and rendered-appearance matches are candidates only;
there are no accepted reuse/alias artifacts in this preparation run. Future workers may approve shared work only
after checking the full canvas, appearance, compositing and namespace semantics, then trace every accepted alias.

The only runtime content change is the seven-line removal in `assets_dev/engine/ui/gameplay/gameplay_mobile.yml`.
`repairs/source_repairs.json` retains the before/after hashes; reversing the recorded patch reproduces the exact
original bytes. Both old indicators checked the same party Immolation buff, and the surviving `asiL10` indicator is
unchanged. No engine build was needed for this dependency cleanup; YAML extraction and all prepared bindings were
revalidated. Engine code, settings, saves, launchers and runtime bitmap files were not modified.

## Start the subsequent artwork phase

Use [QUEUE.md](QUEUE.md). Run `queue.py validate`, then `next`, `show` and `payload` for a bounded job. The payload
does not authorize or invoke imagegen; generation requires the user to start the restoration phase. Inspect source
and accepted dependency references before submission. Native nearest-neighbour reference sheets and synthetic test
fixtures are never acceptable restored artwork.

All artwork states are pending. Future acceptance must still check generated detail, registration, cleanup,
full-page spell transitions, animation continuity, reconstructed atlas joins and isolated in-game behavior as
specified by GOAL.md. `reconstruct` stages complete canvases but explicitly leaves them awaiting full-canvas review.
External `ui_x2` assets require the corresponding `ui=x2` preview tier; restored-icon preference covers `icons_x2`.
