# Non-creature restoration: Luna worker package

For GUI overlays, a legacy BMP's copied panel backing is not necessarily part of the object. Follow
[GUI foreground transparency](../../ui/hud_inventory/MATTE_AND_FITTING.md#gui-foregrounds-over-separately-restored-backgrounds):
restore separable foregrounds with alpha over separately restored backgrounds, retaining native canvas/placement
and the object's own materials. Keep complete background artwork opaque and record compositing overrides.

**REJECT VISIBLE UPSCALED PIXELATION — even when resolution, alpha and placement checks pass.**
Inspect the full-resolution master at 1:1, both contours and interior shading. Enlarged texels, stepped
branches/bars, block-shaped highlights and source-grid dithering fail; blur, sharpening or added texture
over those blocks does not fix them. Require reconstructed material detail and appealing, coherent artwork.

**Modest shape differences are acceptable.** Slightly thicker branches, different leaf clusters or minor
contour changes alone are not rejection reasons when overall quality and identity are good. Alpha coverage
and bounds differences are review signals, not automatic aesthetic vetoes or pixelation detectors. Record
why a flagged variation is acceptable. Preserve native scale/canvas, actual contact or attachment anchors,
important supports and animation coherence; real floating, clipping or unstable supports still need repair.
The >=2x master sampling requirement remains necessary but never proves reconstructed detail.

The older coral `g00412_v0_s0` and cage `g07931_v0_s0` returns shown by the user are confirmed examples of
unacceptable upscaled/pixelated appearance. New attempt 05 masters passed detail and placement review in the
next session; the rejected originals remain retained. Shape metrics are secondary diagnostics.
Strong prompts reduce failures but never replace visual review.


Prepared 2026-09-09. Restoration is in progress. **Strict readiness is [READINESS.md](READINESS.md) /
[readiness.json](readiness.json)**; refresh with `python3 level_generation/sprites/restoration_jobs/readiness.py`.
`queue.py status` reports historical workflow states, which do not by themselves prove readiness.
For decoration generation, use the **[size-aware sheet workflow](BATCHING.md)** first: one built-in call per
compatible sheet, native-canvas extraction, >=2x actual master sampling, and per-asset detail/anchor review.
Missing historical review or crop evidence means inspect existing artwork, not automatically generate it again.
Start a future run with [GOAL.md](GOAL.md). Read this page once, then load only the next few jobs.
The complete [job list](JOB_LIST.md) is for lookup, not something to paste into model context.

Latest completed run: [500 / 500 newly ready images, batching and timing](runs/restore_500_20260920/README.md).
100 batched calls plus one targeted single-image repair; 427 fresh images accepted plus 73 retained-master
reviews. Active-session time: 2h 47m 26s across September 20–21, excluding the overnight pause.
That run ended at 1,957 ready original files and 620 pending.
Current [remaining-620 run](runs/restore_remaining_620_20260921/README.md): the 22 historical blockers were
restored with local Real-ESRGAN inference and individually reviewed on 2026-09-23. Full inventory:
**2,526 ready / 2,526 restoration targets**; 51 snow source files remain user-excluded. The original
checkpoint and refusal receipts remain historical evidence. See the [Real-ESRGAN follow-up](runs/restore_remaining_620_20260921/REALESRGAN_2026-09-23.md).
For a scrolling side-by-side decoration review with animation playback and exportable revisit flags,
open the [decoration review browser](../../decorations/browser/README.md).
Latest animation follow-up: the user selected native-frame Real-ESRGAN for all
[89 animated decoration groups](runs/flagged_animation_20260923/README.md).
Their 559 distinct assets have accepted 4x-master-backed revisions; the previous art remains in
earlier attempts. The current export and browser catalog point to the new 2x canvases.
All 2,723 non-creature originals are accounted for. See the linked run for batching, timing and resumable inventory.
The user approved the remaining non-creature review on 2026-09-23. The complete approved set was installed in
`assets_dev/engine/decorations_x2/` with 2,531 name/palette PNG bindings, including one transparent placeholder.
**Retired 2026-10-19:** decorations, ground items and projectiles came to draw 3D models and effects, so nothing drew
the pack; it and the game's lookup of it were removed (see `tools/DECORATION_PLACEMENT.md`). The rest of this section
is history.
The approved [installation plan](runs/remaining_review_20260923/approved-installation-plan.json) and
[installer](runs/remaining_review_20260923/install_approved.py) pin every candidate and source hash. The 2,520
restorable original BMPs moved to `assets_dev/_legacy/sprites_original/`; 51 user-excluded snow BMPs remain native.
Restored PNGs resolve at their original logical size regardless of the decoration quality setting, so the archived
BMPs are never needed for runtime sprite drawing. Map-local overrides still take precedence. Archived native BMPs
remain hash-checked sources for existing baked outdoor lighting and future provenance checks.

**User scope change (2026-09-21): skip all snow frames; they will not be used.**
All 51 snow source files remain accounted for as `user_excluded_keep_native`.
Originals and generated history are preserved. Do not generate, accept or export snow;
the queue and readiness ledger honor the explicit `user_excluded` state marker.
Historical snow acceptances are retained as evidence but excluded from current ready totals.

Previous completed run: [200 newly ready images, batching and timing](runs/restore_200_20260920/README.md)
(2026-09-20; 4 fresh generations accepted, 196 retained-master validations).

## What is already prepared

- Exact, fully expanded imagegen prompts and paletted input PNGs for every scheduled job.
- All **2,571 referenced BMP files** accounted for; **2,582 name/palette pairs → 2,482 distinct RGBA appearances**.
  Deduplication includes full native dimensions and rendered pixels, not just BMP hashes.
- **17 accepted New Sorpigal images reused**, one completely transparent native placeholder retained.
  Two historical ship views were explicitly migrated to job `g17832_v0_srepair`: old masters sampled below 2x;
  new batched masters passed at 4.05x. Original reuse records and artwork remain preserved.
- **1,382 generation/review jobs**, including ten existing benchmark drafts to inspect before redrawing.
  Large sequences/views are split with explicit accepted-seed dependencies. This is not a promised AI-call count:
  drafts can pass without a call; mask passes, necessary splitting and repairs can add calls.
- Seven prepared art directions: solid props/items, foliage, animated props, water props, soft effects, weather, UI.
- Native frame order, repeated drawings, octants/mirroring, raw timing, palette IDs, scale and flags in `groups.json`.
- **152 unreferenced files** have explicit source/usage triage jobs; **390 missing names** have a separate ledger.
  Neither queue is silently counted as finished artwork. Missing historical art is not invented.

The quality reference is the accepted [New Sorpigal restoration](../../decorations/mm6_new_sorpigal/README.md),
especially its [dark comparison](../../decorations/mm6_new_sorpigal/review/comparison_dark.png) and
[light comparison](../../decorations/mm6_new_sorpigal/review/comparison_light.png).
Keep the same faithful shapes, subdued material colors, clean contours and native world scale.
Original BMP bytes are retained unchanged in the explicit legacy archive described above.

## Fast worker loop

For decorations, start with [batch planning and static preflight](BATCHING.md). The single-job commands below
remain the review/repair/export backend and the path for incompatible/specialized art. Do not submit one
static decoration per call when compatible targets fit the measured pixel budget together.

Use the installed **imagegen skill and built-in imagegen tool**. No API key, paid CLI fallback, Blender or 3D phase.
Run commands from the repository root. Required Python packages are already used by the existing pipeline:
Pillow, NumPy, SciPy and PyYAML.

```sh
python3 level_generation/sprites/restoration_jobs/queue.py validate
python3 level_generation/sprites/restoration_jobs/queue.py next --limit 3
python3 level_generation/sprites/restoration_jobs/queue.py show JOB_ID
python3 level_generation/sprites/restoration_jobs/queue.py payload JOB_ID
```

1. Inspect the job reference and any dependency references with `view_image`. Read its short `review_checks`.
   `payload` supplies complete `tool_args`: use those exact prompt/reference arguments with the current built-in tool.
   Dependency identity references composite accepted alpha onto a flat reference matte at the master's original
   dimensions. This prevents invisible rejected RGB haze from resurfacing in tools that ignore alpha. The matte
   is reference-only; returned artwork still requires genuine RGBA. Original masters remain unchanged.
2. `claim JOB_ID` immediately before submission. Keep at most **2–4 independent requests** pending; follow
   [scheduling guidance](../PARALLEL_IMAGEGEN.md). Await all promises; retain the job ID with each result.
   A yielded call is still running. Never submit a second copy because the first has not returned yet.
   Use `Promise.allSettled` for concurrent calls and attribute each success/error to its job ID inside the callback.
   A fail-fast `Promise.all` can end the orchestration before a companion result is collected. Await every terminal
   result even when one fails. Record moderation rejections without retrying or rephrasing to bypass them.
3. Copy the returned image through `record`, then process it. Substitute the actual returned local filename:

```sh
python3 level_generation/sprites/restoration_jobs/queue.py record JOB_ID /actual/returned/image.png --prompt level_generation/sprites/restoration_jobs/state/JOB_ID.submitted.txt
python3 level_generation/sprites/restoration_jobs/queue.py process JOB_ID
```

4. Inspect the full-resolution `raw.png` first, then `review_dark.png`, `review_light.png` and, for animation,
   `motion.gif`/the frame contact. Reject enlarged source pixel blocks in contours AND internal shading, even if
   downsampling hides them. Record specific observations in `master_detail` in the review JSON. Resolution and
   placement checks cannot establish reconstructed detail; smooth blur alone is also insufficient.
   Check `checks.json`; warnings require inspection, not more scenarios. Judge the final 2x images, not just big masters.
5. Write a short review JSON as described below. Accept with that evidence, or repair the actual defect:

```sh
python3 level_generation/sprites/restoration_jobs/queue.py accept JOB_ID --review /path/review.json --note "Shape and dark material match; edges clean on both backgrounds; fixed support across frames."
python3 level_generation/sprites/restoration_jobs/queue.py payload JOB_ID --repair shape
```

Repairs available: `shape`, `pixel_steps`, `motion`, `spill`, `layout`, `tone`, `alpha_mask`.
For a reviewed defect, add `--repair-note "specific cell, observed defect, and required correction"` to
`payload --repair ...`. This note is included verbatim in the exact saved submission prompt; use it to
avoid spending a repair call on generic instructions that never identify the defect.
The note above is an example, not a preapproved verdict. Never accept without viewing the proofs.
Use a single common `process JOB_ID --adjust SCALE DX DY` only for measured sheet-wide alignment errors;
DX/DY are reference-cell pixels. Repair an individual wandering pose instead of stretching it to its own bounds.
Two failed corrective attempts: `defer JOB_ID --note "concrete defect and tried repair"`, continue independent work,
then revisit with `next --deferred`. Deferred/in-flight work is unfinished, not silently passed.

**Save worker tokens:** do not narrate/rewrite each prompt or read the 1,381-row list. The payload JSON can be parsed
inside `functions.exec` and its `tool_args` passed directly to built-in imagegen, without printing or transcribing
the long prompt. Store it between the reference-inspection call and the generation call. For example, preparation
only (replace the literal ID; inspect the emitted images before making the imagegen call):

```javascript
const result = await tools.exec_command({
  cmd: "python3 level_generation/sprites/restoration_jobs/queue.py payload g00165_v0_s0"
});
if (result.exit_code !== 0) throw new Error(result.output);
const payload = JSON.parse(result.output);
store("sprite:g00165_v0_s0", payload);
for (const path of payload.tool_args.referenced_image_paths) {
  image((await tools.view_image({path})).image_url);
}
```

After inspection and `claim`, call the available built-in imagegen tool with
`load("sprite:g00165_v0_s0").tool_args`. Use the current tool schema and normal image result handling.
Keep one stored payload per job, await all pending calls and checkpoint each actual returned file. A brief batch
progress update and one factual acceptance note per job suffice; no repeated essays about the pipeline.

## Placement checks and existing-master repairs

Read [placement calibration](PLACEMENT_CALIBRATION.md) before reviewing a flagged asset. A flag is a review
request, not a regeneration instruction. Preserve all raw masters. Inspect the raw sheet, extracted mask and
native comparison first; missing supports or inconsistent geometry require targeted art repair, while extraction
or registration faults should be corrected from the existing master.

`payload` appends the current placement constraints from `policy.py` to the frozen prompt. Do not submit the
frozen text directly or rewrite archived prompts. Export now inverts each prepared `native_rectangle` with a common
sheet transform. It never fits individual foreground bounds. Faint pixels cannot determine opaque geometry.

For an accepted asset, create a revision; the old state, files and master remain available:

```sh
python3 level_generation/sprites/restoration_jobs/queue.py revise JOB_ID --note "Measured export distortion; retain the existing generated master."
python3 level_generation/sprites/restoration_jobs/queue.py process JOB_ID
```

If the existing final pixels are already correct, use `check JOB_ID` instead of `process` in that new revision;
it validates the copied native canvas without resampling. This is also the route for imported benchmark drafts.
If a returned sheet has a different layout but contains the correct intact art, `process JOB_ID --layout FILE`
can use an explicitly reviewed source-cell/native-rectangle mapping. See [log-stack example](audit/g00224_v0_s0_layout.json).
The override is bound to the raw master hash, accounts for every job asset, preserves native sizes and is recorded
in `checks.json`. Keep the master and frozen job unchanged. Select only genuinely equivalent copies; never substitute
one animation phase for another or use layout correction to hide invented/missing geometry. Reuse the recorded layout
argument when reprocessing that master.
For flagged supports, add `--landmarks /path/landmarks.json` to either command. Example structure:

```json
{"regions":{"ASSET_KEY":[{"name":"base","box":[0,100,64,128]}]}}
```

Boxes use integer native coordinates; choose them after inspecting the source. Use the same name across frames
for the same support. Checks compare alpha >=192 bounds/coverage in each region and compare errors relative to
each native frame, retaining deliberate motion. They cannot identify a trunk, base, waterline or invented detail
semantically. Check those visually; bottom alignment alone does not prove ground contact.

Acceptance requires `--review /path/review.json` with concise, specific observations:

```json
{
  "anchor_kind":"grounded",
  "master_detail":"Describe observed reconstructed contours and material detail in the full-resolution raw master.",
  "light":"Observed opaque body and genuine openings on the light proof.",
  "dark":"Observed clean contour and preserved dark support on the dark proof.",
  "placement":"Describe actual contact points and native-relative size and margins.",
  "supports":"Describe trunk/canopy, pole/cloth or other relevant internal relationships.",
  "motion":"For animated assets: describe which parts stayed fixed and which moved.",
  "warnings":{}
}
```

Use `suspended`, `water`, `effect`, `ui` or `native_other` when appropriate; do not invent grounding. These strings
illustrate the fields, not preapproved verdicts. Each warning in `checks.json` needs its exact text as a key in
`warnings`, with concrete evidence explaining why the final output is acceptable. Fix actual defects first.
Acceptance records the checks hash. Export does not silently treat historical warning acknowledgements as current
acceptance: such assets stay pending verification, with all earlier work retained. No blanket regeneration.

`python3 level_generation/sprites/restoration_jobs/audit_placement.py` writes a read-only review inventory to
`audit/placement_review.json`. It never alters masters or job states. Prioritize flagged assets, then verify the
remaining old acceptances using the quick existing-canvas route. Reprocess only where evidence requires it.

## Existing art and difficult transparency

- `review_existing` → `import-draft JOB_ID`, inspect proofs, accept or repair. Do **not** run normal `process` on an
  imported benchmark raw: its old input placement differs from the new reference grid. The imported 2x draft is
  already registered. Run `check JOB_ID` before acceptance to inspect that existing canvas without resampling.
  For a corrective generation, use the current prepared reference and normal record/process.
  Known defects: `3amber` invented holes; `3apple` retained enlarged pixel steps. Neither is accepted as-is.
- Delivered alpha takes precedence. Otherwise the job chooses the least-conflicting magenta/cyan/yellow matte.
  Solid cleanup follows the calibrated Sorpigal method, with channel permutation for cyan/yellow.
- Soft FX/water/flame cleanup avoids the opaque-object seven-pixel erosion and hard fringe color clamp. It remains
  a **single-background estimate**, not perfect alpha recovery and not a declaration that the effect is additive.
- A job with `cleanup_route: delivered_alpha_or_companion_mask` cannot use blind chroma keying on opaque output.
  If alpha is absent, use its exact prepared `payload JOB_ID --repair alpha_mask`, inspect the references, generate
  the grayscale mask, `record-mask JOB_ID /actual/mask.png`, then `process JOB_ID`. Inspect mask registration and
  dark interiors especially carefully. Keep both masters. Do not desaturate real pink petals to remove a pink matte.
- A generated grayscale mask is an estimate, not verified opacity. If unmixing creates green/cyan from orange/blue,
  inspect mask underestimation before grading the artwork. For normalized RGB on pure magenta, physically feasible
  alpha must be at least `max(1-R, G, 1-B)`. Values below that produce negative recovered channels which clipping
  hides. Clamping to this bound alone does **not** recover correct opacity or color: reject visibly shifted results.
  Calibration examples: `g00593_v0_s1` and `g00605_v0_s0`, attempts 02–03 (`mask_feasibility.json` in attempt 02).
  For fading FX, also compare integrated visual energy with native frames; a smooth filled shape must not replace
  sparse native dithering at full opacity. Never accept a mask merely because its silhouette is aligned.
- Color-only drift often needs one deterministic, shared color grade, not another AI redraw. Preserve originals,
  record the grade, and compare all frames. Do not independently auto-normalize brightness on flame/FX frames.

### New-generation backdrop contract

The built-in imagegen tool returned genuine RGBA transparency in the 2026-09-14 candle test
(`results/g17778_v0_s0/attempt_03/raw.png`): 81.35% of raw pixels have alpha zero, and light/dark
composites show no painted checkerboard. New requests should ask for true transparent empty areas and holes.
Preserve opaque solid materials and soft flame/water/smoke alpha; do not paint a transparency preview.

`policy.py` now supplies that genuine-transparent-RGBA contract directly. Use `payload` and save/pass its exact
submitted prompt; no manual in-memory rewrite is required. Do not rewrite frozen references or archived prompts.

Verify the actual returned PNG alpha, then inspect light/dark composites. An RGBA label alone is insufficient:
an opaque checkerboard or opaque colored background is a failed transparency request. Hidden RGB beneath zero
alpha is not visible spill. Check solid interiors as well as empty corners; preserve natural antialiasing and
translucent effects instead of making every nonzero alpha opaque. The processor already prioritizes delivered alpha.

Keep all existing masters. Older magenta/cyan/yellow outputs still use their recorded cleanup route; genuine
transparency is not a reason to regenerate good artwork. For an explicitly chosen matte repair, use perfectly
flat pure magenta `RGB(255,0,255)`, record that contract, and inspect the resulting contour after cleanup.

## Finish and resume

`accept` and `export` require explicit master-detail review and measured **>=2.0 master pixels per native pixel
in both axes**. An acknowledged warning, a 2x output canvas, or an old accepted state cannot waive this gate.
`check` preserves existing extraction metadata; missing historical metadata remains a verification task.

`status` is compact; `state/` checkpoints each job and raw attempt separately. Run `export` for the current manifest;
it explicitly reports incomplete coverage. Outputs are full **2x native canvases**, with native logical dimensions
and per-use flags. No atlas/crop is required for this pass; a later installer may pack losslessly while preserving
canvas offsets, native UI placement and center/bottom anchoring. Do not use image dimensions as new world dimensions.

Process `triage --limit 5` after the main queue. `resolve-triage --help` records evidence and a final disposition;
restored/alias entries require an actual artifact. Refer to [review/calibration notes](REVIEW.md) for bounded triage.
The manifest is complete only when every scheduled job is accepted and every triage entry has an evidenced resolution.
The 390 missing-name references remain a documented source limitation, not fabricated successful outputs.

No engine builds, per-asset game scenarios, full inventory re-audits or repeated benchmarks are part of the worker loop.
For HTML review only when useful, use the approved `tools/capture_local_html.py` helper, not fresh Chrome launch commands.
`build.py` reconstructs this package offline; **do not rerun it during an active restoration** or rewrite frozen prompts
globally to repair one asset. Source drift should be resolved explicitly before resuming.

## Index

[Job list](JOB_LIST.md) · [Summary](summary.json) · [Coverage](coverage.json) · [Source/palette ledger](sources.json) ·
[Native animations](groups.json) · [Triage](triage.json) · [Contact-sheet audit](audit/) · [Review notes](REVIEW.md)
