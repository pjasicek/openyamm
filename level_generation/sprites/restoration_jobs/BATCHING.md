# Decoration restoration: minimum-call sheet workflow

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
unacceptable upscaled/pixelated appearance. New attempt 05 masters passed detail and placement review;
the rejected originals remain retained. Shape metrics are secondary diagnostics. Strong prompts reduce
failures but never replace visual review.


Prepare one sheet of compatible targets, make **one built-in imagegen call for that sheet**, retain its raw
return once, then extract the individual full native canvases. This is not the paid API/CLI batch service.
Preparation, planning, accounting, checks and extraction are local Python operations. Planning does not start generation.

## Readiness before spending a call

`readiness.json` / [READINESS.md](READINESS.md) are the strict readiness ledger. Refresh with:

```sh
python3 level_generation/sprites/restoration_jobs/readiness.py
```

The ledger covers every physical non-creature BMP in `assets_dev/engine/sprites`, including the explicitly
resolved triage files. Creature and unused-creature exclusions reconcile against the actual directory listing.
It distinguishes historical `accepted` from readiness: current acceptance/check/output/raw hashes, concrete
full-resolution `master_detail` observations, and measured master sampling **>=2.0 in both axes** are required.
Native placeholders and unused/utility originals are accounted for separately, never called restored artwork.
This is evidence verification, not a fresh visual review or proof of runtime installation.

Older `check` runs sometimes discarded extraction metadata. Missing provenance stays unknown; do not infer
resolution from a big PNG or nominal input grid. The old bounding-box exporter inverted its scale field;
`readiness.py` explicitly distinguishes that historical convention from current rectangle sampling.
Preserve all historical state/masters. Review existing full-resolution art first when evidence is missing.
Where extraction evidence is lost, create an explicit revision and reconstruct/check the mapping from the raw
master. Reprocessing creates fresh measurable evidence but still requires visual review before acceptance.
Do not regenerate a sound master just because an old review field or crop receipt is absent.

Reused Sorpigal art has no queue job. After inspecting a retained master/output, record
`audit/reuse_reviews/ASSET_KEY.json` with `raw_sha256` from its generation record, `output_sha256`, the current
`registration_sha256`, and `review` containing the normal concrete `master_detail`, light/dark, placement,
supports, anchor-kind and warning fields. This evidence is bound to the existing files; the strict resolution
gate still applies. Missing receipts are pending review, never a reason to silently regenerate all reused art.

## Pixel budget and packing

The [local measured experiments](../../ui/hud_inventory/experiments/dense_portraits_20260916/README.md)
returned about **1,572,000 pixels**, even for larger requested sizes. This is a conservative planning observation,
not a documented tool limit or promised future return size. No new calibration/API call is needed for preparation.

The planner uses:

- Full native width/height and **four native pixels of empty padding per side**; no alpha trimming or rotation.
- A common **2x reference scale**, with no independently resized targets.
- Predicted master sampling **>=2.2x**, leaving headroom above the hard 2.0x return/acceptance gate.
- Sheet aspect between **1:2 and 2:1**, and at most **64 targets** as a complexity ceiling, not a target count.
- Native-coordinate sheet area <= `1,572,000 / 2.2²`, approximately **324,793 pixels**, including padding/unused space.
- Deterministic shelf packing over multiple widths; compatible static props share sheets by profile.

Examples: 8 or 12 native 128x128 props fit; eight 256x256 props do not. Two 256x256 props fit. One 800x800
native image cannot reach the target under this measured budget, even alone. Do not shrink it or assume a
larger requested output solves that problem: report the size limitation and establish a larger measured return
or an explicitly reviewed specialized workflow. These are local packing checks, not artistic acceptance tests.

Related animation/view/state chunks keep all their job assets together and separate from unrelated jobs.
For one opaque 640x400 weather frame, use `queue.py payload JOB --full-frame-weather`: square reference
padding previously wasted enough pixels to miss 2x. This explicit layout uses the complete native field at
1280x800 reference size; the raw return must independently measure at least 1280x800. Bind a full-canvas
`--layout` receipt to the returned raw hash with `opaque_weather_field: true` before processing; this explicit
cleanup route preserves the native black field instead of estimating it as a removable matte. Two such
frames exceed the conservative pixel budget, so these frames require single-target calls. Validate the first
returned frame before extending the workflow to the sequence; preparation does not establish acceptance.
Weather uses only its own native-frame reference: supplying another particle frame as an identity image
caused phase copying. Compare bright-particle positions against each native frame locally before accepting;
matching density alone does not preserve animation.
Accepted dependency seeds accompany later chunks. Existing oversized chunks are reported for explicit splitting
with shared identity seeds; the planner never silently breaks the frozen animation contracts. Static foliage and
solid props use separate sheets. Single-frame solid world items without dependencies may share solid-prop
sheets under the same full-canvas and sampling rules. Soft FX, weather, water and UI retain their specialized workflows.

## Prepare and preflight

```sh
python3 level_generation/sprites/restoration_jobs/batching.py plan \
  --output level_generation/sprites/restoration_jobs/batches/RUN_NAME
```

Default selection includes new decoration work and masters measured below 2x. It excludes already verified work,
active requests, unverified dependency seeds, and existing masters needing inspection rather than a new image.
Explicit reviewed repair selection uses `--jobs JOB_ID ... --reason "specific art defect requiring generation"`.
The reason is mandatory for explicit selection of existing art. Do not select everything merely because it is pending.
For targeted repairs where a returned sheet copied the identity seed's phases or layout, add `--native-only`.
This requires explicit jobs and a repair reason. Verified family seeds remain hashed local review references,
but only the native target sheet is supplied to imagegen; compare the result against the family before acceptance.
Explicit selection also supports solid projectile view families, kept together in their own packed sheet.
Soft effects still use their profile workflow. Its `queue.py payload --repair ... --repair-note ... --native-only`
option omits failed candidates and identity images when they caused copying; dependency checks still apply.
The manifest records exclusions and source/state hashes, reference PNGs, slot mappings and exact prompts.
Preparation does not claim jobs, modify original jobs, invalidate historical acceptance or submit anything.

Before each call:

```sh
python3 level_generation/sprites/restoration_jobs/batching.py preflight PATH/manifest.json S001
python3 level_generation/sprites/restoration_jobs/batching.py payload PATH/manifest.json S001
python3 level_generation/sprites/restoration_jobs/batching.py claim PATH/manifest.json S001
```

Inspect the reference and any seed with `view_image` before submission. Use the exact returned `tool_args` with
the built-in tool. `claim` is immediately before the call, not while planning; it prevents the same original job
being submitted through another batch or the single-job path. Await the existing call; no speculative duplicates.
Start with one representative sheet and pass its actual per-cell layout/detail/anchor review before increasing
throughput. The measured pixel budget does not establish decoration fidelity at every packing density.

## Retain, check and extract the return

```sh
python3 level_generation/sprites/restoration_jobs/batching.py record PATH/manifest.json S001 /actual/returned.png
python3 level_generation/sprites/restoration_jobs/batching.py import PATH/manifest.json S001
python3 level_generation/sprites/restoration_jobs/queue.py process JOB_ID
```

`record` retains the original raw and prompt before checking actual dimensions, aspect, per-cell sampling,
true RGBA transparency, nonempty slots and contamination across gutters. Failed returns remain available;
they are not accepted or automatically resubmitted. `import` creates explicit revisions of the original jobs,
archives previous state, and binds each sampling mapping to its hash. Partial imports can resume without
duplicating completed job imports. The original raw sheet is shared, not recompressed/resized into fake masters.

Extraction uses **the full native rectangle**, not the generated alpha bounding box. The final output is exactly
`2*native_width` by `2*native_height`; logical dimensions, native empty margins and bottom/center anchor remain
unchanged. This prevents exporter-induced floating rocks, shifted roots and individually stretched objects.
Static checks also compare opaque bounds, coverage and explicitly selected support regions. A model can still
draw a displaced rock inside a correctly sized cell, so contact points and internal landmarks need visual review.
One common measured layout correction may be used through the existing raw-hash-bound `--layout` mechanism;
do not independently stretch silhouettes to hide art defects. Preserve margins and >=2x sampling after correction.

Inspect every crop in the full-resolution master, then the final 2x image on dark/light backgrounds. Check
continuous contours AND reconstructed internal texture/shading; smooth blur alone does not pass. Check actual
slot geometry, thin parts, holes, dark solid supports and native contact points. Whole-sheet size is insufficient:
generators can compress one row or move one object. No local size/alpha test can certify reconstructed detail.

Accept through the normal `queue.py accept JOB_ID --review FILE --note ...` path. In addition to the existing
review fields, batch reviews require an entry for **every asset in that job**, without blanket sheet approval:

```json
{
  "assets": {
    "ASSET_KEY": {
      "master_detail": "Specific observed contours and reconstructed material detail, not enlarged blocks.",
      "layout": "Specific observed cell identity, scale and intact boundaries in the returned master.",
      "placement": "Specific observed native-relative solid contact and internal landmarks."
    }
  }
}
```

These strings illustrate the schema, not an acceptance verdict. Sub-2x or unknown master resolution is a hard
failure, even if a warning was acknowledged. Approve good original jobs independently; repair only defective
jobs/cells using an explicit new batch. Never resend a whole successful sheet for one bad object. For a failed
sheet needing a changed mapping, retain it and explicitly recover its layout through a reviewed revision; do
not bypass return checks by rescaling the raw. `release ... --reason ...` releases claims only after terminal
call/cancellation evidence is known. It keeps the old sheet receipt and raw; use a new plan for a new request.

After acceptance, refresh `readiness.py` and `queue.py export`. Missing evidence and unresolved art remain pending.
Engine installation and game scenarios are separate scope. This workflow has no paid API fallback or automatic retries.

## Offline regression checks

Explicitly requested `soft_fx` jobs may use measured dense sheets too. Each effect family stays on its own
sheet with native phase order, detached particles and soft-opacity rules; unrelated effects are never mixed.
The regular soft-effect processor and per-frame visual review still apply. Weather retains its specialized workflow.
Companion masks refine delivered RGBA alpha without recoloring RGB. Inspect the returned mask's actual channels:
grayscale material shading is not an opacity verdict. Retain the original return and record any reviewed conversion;
verify that dark bars and occupants stay opaque and genuine holes are transparent on both backgrounds.

```sh
python3 -m unittest discover -s level_generation/sprites/restoration_jobs -p 'test_*.py'
```

Requires Pillow, NumPy, SciPy and PyYAML in the chosen Python environment, as does the existing processor.
Tests use synthetic images to check packing, minimum resolution, transparency/gutters, provenance conventions,
duplicate-claim prevention, resumable multi-job intake, native canvas preservation and per-asset acceptance.
