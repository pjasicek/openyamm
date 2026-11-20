# Redo insufficient MM6 creature art with actual 2x generated detail

Scope: the insufficient frames in [inventory.json](inventory.json), across the installed MM6 native creature,
peasant, animal and special-actor families. The user subsequently authorized the complete redo of insufficient art.
The redo acceptance requirement is now **strictly greater than 2x** in both axes, with a planning target of 2.2x.
The historical inventory retains its original below-2x classification; exactly-2x retained frames are outside this redo.
Keep the currently
installed packages usable until replacements have been reviewed and installation is requested.

Follow [Sprite Atlas and Variants Pipeline](../../SPRITE_ATLAS_VARIANTS_PIPELINE.md),
[Direct Sprite Workflow](../../DIRECT_SPRITE_WORKFLOW.md), and the creature-restore/imagegen skills.
Those documents own the full procedure; this document supplies the concrete redo gates and inventory usage.
Use the pipeline's lean default: shared tools, compact contacts and one acceptance record. Historical browser
playback, per-family scripts and separate notes are not mandatory for new work. Accepted checkpoints stay intact.

## Inventory and status ownership

- [INVENTORY.md](INVENTORY.md) lists every family and repair-scope count.
- [insufficient_frames.csv](insufficient_frames.csv) lists every failing frame, source and measured sampling.
- [inventory.json](inventory.json) includes sufficient frames to retain, native endpoints, canonical aliases,
  palette dependencies, native animation bindings/timing/mirrors, previous raw outputs/prompts/registration,
  padded native union crops, and resumable jobs. A job groups a previous batch/action; it is **not** one mandated
  future imagegen request. Its new batch layout remains to be chosen after crop and output-budget measurement.
- Each project has `quality_status.json`. The main `remaining_inventory.json` now evaluates MM6 generated
  sampling live, and `mm6_remaining/progress.json` marks affected families `insufficient`. Old acceptance records
  describe historical art approval; they do not override this quality gate.
- Five sparse/empty native Cactus endpoints remain deliberately preserved. Do not invent mass for them.
  Reuse adequate frames as identity/overlap references. They need regeneration only if a demonstrated defect or
  coherent sequence repair requires it, with that expansion recorded explicitly.

Refresh without generating:

```sh
python3 level_generation/creatures/mm6_remaining/quality_review/audit.py
python3 level_generation/creatures/mm6_remaining/redo_2x/build_inventory.py
python3 level_generation/creatures/inventory_remaining.py
python3 level_generation/creatures/mm6_remaining/prepare.py ledger
```

The job builder preserves attempts, selected checkpoints, blockers and resume steps when the input signature is
unchanged. Keep job execution states `pending`, `partial`, `validated` or `blocked`; keep `quality_status` separate.
A source change invalidates earlier job evidence and requires review. The full inventory has one row per native
frame name; canonical aliases avoid duplicate generation. Shared source hashes identify cross-family dependencies,
but do not by themselves prove that the intended palettes/materials are interchangeable. In particular, retain the
documented Demon/Demon Fly shared ash ownership and Cactus actor bottom-pivot export behavior.

The initial audit contains 3,114 insufficient names representing 3,086 distinct native poses within their families.
`derived_pixel_aliases` supplements declared aliases using identical native indexed pixels and dimensions.
Generate each `generation_required_frames` canonical pose once per family, even when several repair scopes refer
to it. Restore all alias bindings from that result. If a later refresh finds an adequate identical pose,
`reuse_sufficient_aliases` records the reuse opportunity instead of requiring another generation.

## Prepare a coherent native action/view

1. Inspect the job's original BMPs with their actual native palette, plus the retained enhanced identity reference.
   Decode index-zero transparency and preserve source canvases, native frame/actor scales, `Center` handling,
   native reuse/mirrors, action order, durations and unreferenced native poses. Do not generate mirrored views anew.
2. Select one action and stored view. Short mixed-view standing sets can share a request only if their measured
   budget and identity review support it. Separate unrelated actions currently grouped as `death_corpse` as needed;
   retain continuous death progression and its native held endpoint.
3. Place originals at their native logical offsets, then compute the **union** of visible bounds across the entire
   sequence, including weapons, tails and raised limbs. Use a common crop and initially six native pixels of padding
   on each side. Inventory crops are measured starting points for previous batch scopes; recompute when the new
   sequence grouping differs. Verify original foreground reconstructs exactly after putting the crop back.
4. Keep the same crop/origin/scale for all poses and overlap frames. Never independently fit each frame to a cell,
   center its silhouette, normalize its height, or derive scale from a raised sword or collapsing body.

## Budget before calling imagegen

For a padded native cell `w × h`, grid `c × r`, and an **actually observed** output `W × H`:

```text
budget_x = W / (c * w)
budget_y = H / (r * h)
minimum_budget = min(budget_x, budget_y)
```

Include additional gutters in the denominators. Aim for **at least 2.2** to leave about 10% headroom; the acceptance
minimum for replacements is strictly above 2.0 in both axes. A requested output size or an enlarged native reference proves nothing about delivery.

Example from the pipeline: eight poses with a 232×232 native cell in a 3×3 grid returned 1254×1254, only 1.80x.
A six-pose 3×2 grid returned 1536×1024, giving 2.21x. Those are measured examples, not guaranteed tool sizes.

Try tighter common empty-margin cropping and another grid aspect first. If the sequence does not fit, split it
into consecutive groups of **whole poses**, with overlapping transition poses. Use fewer poses per request for
large dragons and wide wings. Keep native pose authority plus the accepted identity reference; select exactly one
version of each overlap in the assembled sequence. Do not generate separately tiled body parts or weapons to evade
the budget. Do not simply repeat the old full-canvas 3×2 references that caused this deficiency.

## Generate and measure the actual result

Use the built-in imagegen tool through its skill. Save exact submitted prompts, reference roles/paths/hashes,
raw output hashes and actual dimensions. Preserve native appearance, palette and tonal weight. The user updated background preference on 2026-09-14: request true RGBA transparency and preserve supplied alpha. Never accept a painted checkerboard. Earlier magenta-key sheets remain valid checkpoints and use their recorded matte extraction; do not regenerate them solely to change background. If a new output has genuine alpha, skip matte extraction but still inspect alpha integrity and edge RGB. No background gradients or painted ground patch. Keep earlier trials.

Inspect cell ownership and clipping, then register raw artwork to native coordinates with a **uniform anatomical
scale**. Record the complete transform chain, including any earlier resizing. The measured minimum is:

```text
raw-to-native uniform scale t:  generated_sampling = 1 / t
raw-to-2x export scale s:        generated_sampling = 2 / s
```

For a direct raw-to-2x path, `s > 1` fails. Upscaling an intermediate first does not reset this calculation:
multiply all transforms from the original imagegen raster. Report both axes if a special-case transform exists;
anisotropic stretching is not an acceptable general restoration method. A large sheet with small figures can fail.
Retain failed output as a trial, change crop/grid/pose count, and regenerate the affected complete poses. Neither
Lanczos nor ESRGAN enlargement earns additional generated-detail credit for this task.

For every selected frame, save `raw_path`, `raw_sha256`, `raw_cell_rect`, delivered raster dimensions, native
sequence crop/offset, full registration chain, measured X/Y sampling, and selected checkpoint. Do not mark the
job sufficient from `pixels_per_logical_pixel: 2` or atlas page dimensions.

## Validate motion, matte and variants before acceptance

Automatically preserve and check [exact native anchor placement](../../SPRITE_ATLAS_VARIANTS_PIPELINE.md#exact-native-anchor-placement)
before final placement contacts and again after export. Integer centering of differently sized native canvases must
not discard half logical pixels. At 2× these offsets are exact physical pixels, not an allowed rounding tolerance.
Any correction after a review invalidates its affected placement evidence and acceptance hashes; rerun those checks
before freezing acceptance. The existing inventory audit identifies faults but does not automatically repair them.

The old lowest-visible-pixel scan is a screening tool, **not a complete anchoring test**. For each native sequence:

Apply [independent placement review](../../DIRECT_SPRITE_WORKFLOW.md#independent-placement-review): annotated
native-size contacts, an anatomical check independent of the transform, and an audit of all consumers when a
landmark detector fails. Solver residuals and unchanged animation metadata do not certify visual alignment.

1. Compare source and restored frames in actor-local coordinates at the same pivot, native timing and scale.
   Record frame-specific anatomical landmarks: planted foot/stance center, head or torso reference, and intentional
   lifts/turns. Staff tips, tails and particles must not masquerade as foot contact. For floating actors, preserve
   native clearance rather than forcing ground contact.
2. Screen the excess displacement against the original motion in both X and Y. Target zero registration error;
   integer placement can quantize to 0.5 physical pixel. Flag larger discrepancies for visual adjudication, not
   automatic acceptance. Correct proven whole-frame drift with deterministic translation. Do not force an entire
   walk cycle onto one static ground line or hide anatomical inconsistency by per-frame rescaling.
3. Inspect **every** selected pose in assembled native-order sequence contacts, including overlaps, death/corpse
   holds, mirrors and variants. Check excess native-relative displacement, scale breathing, stance width,
   equipment/face consistency and clipping at viewing scale and in 100% detail crops. Use timed playback only
   when motion remains uncertain or when requested. Record the actual method; contacts are not watched playback.
4. Repair matte RGB before premultiplied-alpha resizing; run residual-spill checks on each cleaned frame and the
   final atlas-extracted frame. Inspect worst edges against both light and dark backgrounds. Keep thin features.
5. Author masks against the **new enhanced pixels**. Derive native palette variants deterministically from one base;
   do not reuse old mask rectangles on changed anatomy. Preserve alpha, protected materials and exact base bypass.
6. Export 2x runtime base/mask atlases with identical placement, logical canvases/pivots, crop offsets and native
   animation metadata. Verify exact crop reconstruction and atlas extraction. Retain prompts, raw outputs, accepted
   masters, settings, compact acceptance evidence and decoded memory accounting. Shared-template viewer export
   is an inexpensive local operation and may run automatically; no model calls or per-creature viewer code.

Stage revised work in each project's `redo_2x/`. Do not overwrite original BMPs or the installed `assets_dev`
package during generation. Acceptance requires full native coverage, every selected frame meeting generated
sampling in both axes, documented motion review, clean edges and correct palette variants. Update the selected
project manifest/provenance and acceptance together, preserving the previous installed checkpoint; then refresh
the inventory. Installation is a separate reviewed step.

## Lean acceptance record

The existing `review/decision.json` is sufficient for the reviewer's decision; no separate `review_notes.md`, HTML
viewer or browser trace is required. After actually reviewing the final contacts, record:

- `status: "accepted_after_visual_review"`, `review_mode: "static_contacts"` and a short truthful `method`.
- `reviewed_manifest_sha256`: the hash of the final candidate manifest.
- `reviewed_frames`: all selected native frame names, including aliases/unbound poses covered by the review.
- `checks`: `faithful_detail`, `poses_and_placement`, `edges_and_alpha`, `masks_and_variants`, each true only after
  actual visual review. Fine-detail inspection must reject pixelated/blurred enlargement even if sampling passes.
  For `poses_and_placement`, describe the transform anchor and independent anatomical check in `method`; include
  the inspected placement contacts in `evidence_artifacts`. Report unresolved displacement instead of accepting it.
- `evidence_artifacts`: relative contact-image paths mapped to hashes, binding the decision to what was inspected.

Run `freeze_review.py PROJECT` to verify the decision, coverage, native metadata, measured >2× sampling and numeric
validation, and write the existing hash-bound acceptance files. The script cannot perform or infer artistic approval.
`export_run.py PROJECT` and `freeze_review.py PROJECT` create the shared-template viewer deterministically unless
`--skip-viewer` is set; neither invokes a model or browser. The historical
browser-backed decision format remains supported for existing work. Do not rerun accepted packages just to adopt
the lean record. Refresh the progress and combined inventory once after acceptance.

When browser review is required, the browser-backed decision must also contain
`checks.watched_playback: true`, set only after actually inspecting timed playback of the final artifacts.
The freezer checks this declaration separately from `browser_playback.json`, which records mechanical
coverage and cannot establish visual acceptance. Static contacts cannot satisfy an explicit timed-review goal.
