# Restore the inventoried MM6–MM8 non-creature sprites

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


Execute the prepared [Luna worker package](README.md). Use the **imagegen skill** and the **built-in imagegen tool**
with the per-job `payload` prompts (including current placement constraints) and reference images. This is faithful 2D enhancement like the accepted
New Sorpigal decorations. No Blender/3D phase, creature restoration, engine installation or paid API/CLI fallback.

For decorations, the [size-aware batching workflow](BATCHING.md) supersedes one-job-per-call submission.
Refresh the strict [readiness ledger](READINESS.md); reuse/review existing masters before planning new generation.
One call restores one compatible sheet; static Python preflight rejects impossible packing before submission.
Preserve native canvases/anchors and require >=2x actual master sampling in both axes. Never upscale a small
return to satisfy the gate or accept pixel-block enlargement as reconstructed detail.

## Scope and deliverables

Restore all scheduled decorations, ground items, projectiles, effects, weather and interface sprites listed in
`index.json`. Preserve original identity, proportions, native tonal weight, palette colors and animation behavior.
Reuse the 19 accepted New Sorpigal exports. Review the ten benchmark drafts; repair actual defects instead of
blindly regenerating or accepting all ten. Keep the empty native placeholder empty.

Produce reviewed transparent 2x PNGs, raw masters, exact submitted prompts, cleanup/registration checks, frame
contact sheets and brief visual acceptance notes. Export a source-name/palette → enhanced-image mapping while
preserving the native group timing, octants, mirrors, scale, flags and logical canvas information already prepared.
Do not crop/resize frames independently or install globally. Genuine motion, bobbing, glow and quiet FX frames stay.

Resolve all 152 source/usage triage entries with concrete evidence: restore/alias proven art, or explicitly retain
unused/utility originals. Unknown references stay honestly unresolved. The 390 missing native image names are a
recorded input limitation; do not invent art or repair gameplay tables just to make this ledger empty.

## Execution

0. Complete the [placement calibration](PLACEMENT_CALIBRATION.md) export/acceptance correction first. Preserve
   existing masters; review flags and deterministically repair exports before choosing targeted imagegen repairs.
1. Read README once, inspect the Sorpigal quality references, run `queue.py validate` and refresh `readiness.py`.
   For decoration generation, prepare/preflight compatible sheets through `batching.py`; inspect existing masters
   with missing review/provenance before spending calls. Other profiles use `next --limit 3`.
2. Read only those jobs/sheets. View every reference, use `payload`, claim the jobs/sheet and call built-in imagegen with the
   supplied arguments. Use at most 2–4 independent pending calls, checkpoint returned files and await every call.
3. Use record/process/import-draft helpers. Inspect the final light/dark proofs and native-timed animation contacts.
   Preserve shared prop structure, clean edges, soft effects and source-relative size/placement. Fix only actual defects.
4. Prefer deterministic cleanup/alignment/tone corrections where appropriate. Prepared targeted AI repairs and
   alpha-mask extraction are available. Never apply opaque-object matting to translucent glows or erase real colors.
5. Accept with a short truthful review JSON and note, addressing each current warning explicitly. After two unsuccessful corrective attempts, defer the asset with its
   specific defect, continue independent work, and return to deferred jobs before declaring completion.
6. Finish triage and run `queue.py validate` and `queue.py export`. Inspect the export's remaining counts.

Keep work resumable through `state/`; do not regenerate accepted work after a restart. A claimed/in-flight job
requires checking the existing call/result before resubmission. Tool unavailability or quota exhaustion does not
authorize an API switch or a fabricated success. Preserve progress and report the actual blocker.

## Completion gate

- Every restored asset passes strict readiness: accepted hashes, explicit full-resolution detail review and
  measured >=2x master sampling. Historical accepted labels alone are insufficient. No pending work forgotten.
- Source/palette coverage complete; every triage entry has evidence and an appropriate final disposition.
- Shared animations retain native timing/order/repeats/views and do not breathe or jump because of registration.
- Final contours work on light and dark backgrounds; thin geometry survives; glows/smoke retain their intended softness.
- Export manifest says complete and references real, hash-checked artifacts. Report accepted/reused/retained counts
  and remaining source limitations succinctly, with output paths. No engine scenarios or installation are required.
