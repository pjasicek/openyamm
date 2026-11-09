# HUD preparation queue

Portable external-chat handoff: see [CHAT_BUNDLES.md](CHAT_BUNDLES.md) for five assigned 200-target ZIPs,
master prompts, return contract and validation. Assigned cells are skipped by local scheduling but remain unfinished.

The target manifest, job definitions and fixed reference sheets passed the preparation audit; see `COMPLETION.md`.
The queue itself never invokes imagegen or installs runtime assets. Artwork-phase activity is recorded in the live
checkpoint and `ARTWORK_PROGRESS.md`. Do not interpret a successful structural check as visual acceptance of artwork.

**Current artwork scheduling:** use [BATCHING.md](BATCHING.md). Small compatible inventory assets default to
3×3 via `batch-payload CELL_ID ...`, which can span frozen jobs without rewriting them. Record the returned
master once with `record BATCH_ID --raw ...`, then review/accept each selected cell normally. Large assets and
dependent state/identity groups keep their specialized layouts. Frozen six-cell jobs are not a requirement
to make six-cell generation calls, and the experimental sheets are not automatically accepted queue work.

Finish the first pass before repair batches. `next` defaults to `--phase first-pass`, selecting only fresh
unattempted/non-deferred cells. `--phase review` lists retained cells still awaiting review; `--phase retry`
lists deferred cells with reasons and retained attempt paths. Review each returned sheet, accept its good cells,
`defer` its failures, and move on. Retry compatible failures together after fresh work is exhausted. Always honor
the returned `selected_cells` rather than resubmitting accepted/failed siblings from an entire frozen job.

The active checkpoint now includes the explicit `air_v1` preview layout revision. Frozen inventories and runtime
YAML are unchanged. Queue targets, page-crop payloads and acceptance use that hash-bound revision, and the isolated
preview copies its YAML. Old state/artwork survives under the original paths and `checkpoint/layout_revisions/air_v1/`
contains `before-state.json`, the revision, revised accepted/reconstructed assets and the current export manifest.
Read staged paths from the active state; do not install the older root `exports/` by assuming it is current.
The eight revised pilot states reused retained imagegen ink with explicit reassembly records and new visual review;
reassembly is not a generation call. `revise_air_layout.py --apply` was a one-time migration and must not be rerun.
See `review/spellbook_placement/README.md` for native and restored game evidence.

Run from the repository root:

```sh
python3 level_generation/ui/hud_inventory/queue.py validate
python3 level_generation/ui/hud_inventory/queue.py next --limit 3
python3 level_generation/ui/hud_inventory/queue.py show JOB_ID
python3 level_generation/ui/hud_inventory/queue.py target TARGET_ID
python3 level_generation/ui/hud_inventory/queue.py payload JOB_ID
python3 level_generation/ui/hud_inventory/queue.py payload JOB_ID --repair-note 'Specific observed defect'
python3 level_generation/ui/hud_inventory/test_preparation.py
```

`payload` writes exact tool arguments and submitted-prompt text under `prepared_payloads/JOB_ID/`. It does not call
imagegen. It refuses a spell-icon job until its page is accepted, and seed-dependent jobs until the seed is accepted.
Accepted page crops are made from the actual accepted artifact, with its hash recorded. Native reference sheets
are enlarged using nearest-neighbour only for legibility; they are not restored outputs or accepted artwork.
Arcomage glyph and uniform unused regions have deterministic jobs, whose payloads contain no imagegen arguments.
Spell crops and same-identity seeds are packed into compact reference sheets. Treatment pilots gate acceptance but
are not supplied as unrelated face/item references. Each recorded attempt retains copies of the submitted references.

When the user explicitly starts the artwork phase, inspect each job's source references and review checks, then
submit the payload using the imagegen skill and built-in tool. Fonts use `tools/font_upscale/README.md`.
No API/CLI fallback, automated generation, or runtime installation is provided by this queue.

The future worker loop is:

```sh
python3 level_generation/ui/hud_inventory/queue.py claim JOB_ID --note 'worker/run identification'
python3 level_generation/ui/hud_inventory/queue.py record JOB_ID --raw /absolute/path/to/returned-master.png
python3 level_generation/ui/hud_inventory/queue.py accept CELL_ID --artifact /absolute/path/to/registered-cell.png \
  --review /absolute/path/to/review.json --attempt ATTEMPT_ID
python3 level_generation/ui/hud_inventory/queue.py defer CELL_ID --reason 'specific defect to repair'
```

Claims prevent `next` from resubmitting work. A claim is **not** evidence of a live tool/process; inspect its actual
handle on resume. `release JOB_ID --reason 'observed terminal result or missing handle'` records an explicit release.
Recorded raw masters remain available; `next --phase review` identifies their pending cells as `review_retained_master`.
Accepted siblings are preserved when another cell fails. Queue state lives in `checkpoint/`, separately from
inventories and manifests. CLI mutations hold a checkpoint lock through read-modify-write and save atomically.
Use `--state /tmp/test-run/state.json` for isolated queue tests, including payloads and reconstructed artifacts.

For byte-identical native full canvases, `reuse CELL_ID --donor ACCEPTED_CELL_ID --review review.json` provides
explicit verified artwork reuse without inventing a generation attempt. Run `compare` against the donor artifact
under the destination cell id, inspect every comparison and complete sheet, and supply the normal visual review
plus `consumer_contract_notes`. Check both consumers; retain the destination's own filename, bindings and offsets.
The command requires identical source bytes, namespace, canvas, treatment and compositing contracts; page
dependencies and atlas regions are excluded. A declared seed dependency is allowed only when the donor belongs
to that exact accepted seed job; every seed cell remains a hash-checked dependency. Other seed dependencies are
excluded. It copies the accepted pixels, records the donor as a hash-checked
dependency, and exposes reuse provenance in the staged manifest. `validate` reports reused cells separately within
the accepted total. Reuse still needs reconstruction and full-canvas review before staging.

Identical siblings within the same job may also reuse an accepted sibling when that job has an
`accepted_seed_job` dependency. The donor must record every current shared dependency hash; both the seed and
donor remain dependencies of the reused result. Sharing a seed across different jobs does not authorize reuse,
and other dependency kinds remain excluded. Native/source, canvas, compositing and actual visual review checks
still apply. `test_reuse.py` covers seed changes, missing donor provenance and unrelated-job rejection.

Acceptance requires exact region dimensions and an explicit review JSON with `identity`, `registration`,
`compositing`, `detail_at_x2`, and `state_or_animation_consistency` all true. It also requires `notes`, an existing
`registration_record` file and a `review_images` list of existing visual evidence paths. These booleans record an
actual visual review; they must never be auto-filled because a file decoded or reached the right dimensions.
Accepted page/seed changes invalidate their dependent acceptance. Font-region review checks deterministic glyph
reconstruction instead of invented AI detail. Atlas-region acceptance is not yet whole-atlas export acceptance.

Artwork-phase fitting now also requires measured registration; see [MATTE_AND_FITTING.md](MATTE_AND_FITTING.md).
Run `queue.py compare CELL_ID --artifact /absolute/path/cell.png --output-dir /absolute/path/review`.
Inspect its comparisons, fill in the registration record's actual landmark measurements and visual notes, and
include every comparison in `review_images`. `accept` recomputes footprint measurements and checks the evidence
against the current source/output hashes. A correctly sized canvas containing shrunken or shifted artwork fails.
Opaque artwork still needs internal landmark inspection; matching alpha alone says nothing about internal scale.
Execution payloads append these fitting requirements and explicit pure-magenta cutout instructions to the frozen
job prompt. Existing manifests and reference sheets are preserved; the exact submitted prompt is retained per attempt.
Pure-cutout payloads supply a label-free native sheet on magenta at the same recorded coordinates. This avoids
the generator redistributing subjects while removing the old title and colored cell boxes. The prepared labelled
sheet remains available for identification; the exact submitted matte reference is retained with the attempt.

Single opaque page/background/map jobs submit the complete native x2 canvas without sheet labels or gutters.
For an individual equipment or inventory-icon repair, use `payload JOB --cell CELL_ID`. This selects one cutout,
supplies its full native x2 canvas without gutters, and records its own `execution_layout`. Extract using that
layout rather than the frozen multi-cell sheet coordinates. The recorded attempt cannot accept unsubmitted
siblings. Spell states still use `--pair-index`; single-cell selection cannot split a spell pair.
The same full-canvas selection supports a one-member `legacy_ui_art` cutout whose only dependencies are
treatment pilots. It cannot split a legacy state group or bypass seed/page dependencies. The fountain-tab
pilot repairs illustrate why a successful payload, smooth master and passing footprint still do not establish
acceptance: retain internal-landmark and complete-background review.
Their payload's `execution_layout` records the whole output rectangle, superseding the labelled reference layout
for that attempt. `payload --repair-note 'observed defect' --repair-reference /path/previous-master.png` supplies
the previous generated master alongside the authoritative native image. Optional `--detail-reference /path/native-crop.png`
adds an inspected native close-up for ambiguous small lettering/features. Inspect these images before submission;
all references and exact prompts are retained by `record`. Repairs do not modify the frozen jobs or accepted art.

For spell retries, `payload JOB --pair-index 0` selects one zero-based adjacent colored/sepia pair and supplies a
label-free native pair with explicit `execution_layout`. The attempt records `selected_cells`; it cannot accept
an unsubmitted sibling. All original dependency versions remain checked. Add `--spell-ink-matte` to request only
the artwork/ink on magenta while keeping the accepted page crop as lighting/context reference. This mode is useful
when generated parchment fails full-page seam review. Composite cleaned ink over the exact accepted page crop,
preserve the native canvas/key contract, and inspect the actual ink geometry independently of that contract.
Never flatten a mismatched generated parchment rectangle over the accepted page. See the Air Resistance pilot's
processing/review notes before applying this to different spell art; pale fills and fine hatch strokes need review.

`expected_targets.json` records every source hash, native/x2 canvas, output namespace, usage/anchor chain, native
table row, state alias and compositing profile. Multiple rendered appearances can require preserving indexed/key
semantics in BMP/PCX rather than flattening to one incompatible RGBA mask. Repeated source bytes and even matching
render fingerprints are only candidates: shared generated work is not approved automatically.

The mobile duplicate Immolation reference to absent `asiR08` was removed during source cleanup.
`repairs/source_repairs.json` retains before/after hashes and the patch; the existing `asiL10` body indicator remains.
All inventories were explicitly reconciled. There are no unresolved required image sources in the handoff.

Before regenerating `classification.json`, `expected_targets.json` or `jobs.json`, reconcile any existing checkpoint.
The queue refuses mismatched manifest/state hashes. Regeneration must not erase accepted work. The preparation
builders do not write checkpoint state; keep source changes and state migration explicit.

`reconstruct TARGET_ID` requires accepted constituent cells and stages a full native-registered x2 bitmap under
the checkpoint's `reconstructed/` directory. The Arcomage atlas preserves RGB keys across its complete 1920x5000
canvas. Reconstruction remains `reconstructed_awaiting_full_canvas_review`; it is not automatic visual acceptance
or runtime installation. Review joins, glyphs and states before exporting to the manifest's final staging path.

After full-canvas inspection, `stage TARGET_ID --review /absolute/path/canvas-review.json` copies that exact
reconstruction to the manifest's project-local `exports/` path and updates `exports/manifest.json`. The review must
contain `full_canvas_review: true`, `artifact_sha256`, `notes`, and existing `review_images`. Staging checks every
constituent acceptance, reconstruction hash and exact full size. It never writes to `assets_dev/` or installs into
normal launchers. Temporary-checkpoint tests also stage only under their temporary directory.

`prepare_preview.py` builds a disposable asset root from validated staged targets plus the original fallbacks and
creates private settings and a private inventory fixture save. Its JSON output identifies the assets/settings/save
for the approved run/capture wrappers. It does not modify ordinary settings or saves. See `ARTWORK_PROGRESS.md`
for actual preview validation status; successfully creating a fixture is not a visual approval.

For a new inventory batch, `prepare_preview.py --items MERGED_ID ...` grants those item-table IDs only
to the disposable save. Include at least one original fallback alongside the restored batch, then review
appearance and representative picking in both restored/original modes. See `review/helmets_3x3/README.md`.
