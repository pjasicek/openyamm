# Placement/export calibration — 2026-09-10

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


Preserve generated masters. Padding/registration/alpha defects should first be repaired deterministically;
missing geometry, altered proportions already present in the master, or inconsistent rigid supports need a
targeted imagegen repair. A flag alone is not evidence that regeneration is needed.

## Confirmed exporter defect and correction

`register_cell` previously cropped the alpha >16 bounding box and independently stretched its width/height to
native visible bounds. One stray matte pixel could therefore compress an otherwise intact object. Correct x2
canvas dimensions and a matching overall bounding box did not prove correct internal geometry or placement.
The generated-detail ratio was also inverted in this branch, producing misleading low-resolution warnings.

Export now samples the prepared `native_rectangle`, accounting for returned sheet size and native canvas margins.
An explicit shared `--adjust SCALE DX DY` applies around each reference cell center, with translation in reference
pixels. No individual foreground fitting occurs. Premultiplied color/alpha sampling preserves clean edges.
Opaque pixels outside the native canvas are flagged before extraction so clipping cannot silently hide them.

Checks distinguish opaque geometry (alpha >=192) from faint visible edges. Named native-coordinate regions can
measure bases, poles and internal landmarks; animation checks compare errors relative to each original frame.
This preserves deliberate bobbing. There is no automatic semantic inference that every bottom-aligned sprite
has ground contact: suspended objects, water, effects and UI need their own observed anchors.

## Three existing-master trials

All used the original `attempt_01/raw.png`, copied byte-for-byte into a new attempt. No imagegen calls were made.
Light/dark frame contacts and native-relative opaque support measurements were reviewed.

| Job | Observed issue | Result |
| --- | --- | --- |
| `g00297_v0_s0` magic pedestal | Fourth exported frame became abnormally narrow although the master was intact. | New rectangle extraction restores all five globe/shaft/base proportions. Base/shaft regions pass. |
| `g17833_v0_s0` blue flag | Third exported frame shrank and shifted despite an intact pole and cloth in the master. | Pole location/length restored across four frames; native cloth motion retained. Pole regions pass. |
| `g17687_v0_s0` stakes | Historical alpha-coverage warning and incorrect low-detail warning. | Full-canvas export retains all four stakes and their different tips/bottoms; current checks pass. |

Proofs and acceptance evidence are under each job's `results/JOB_ID/attempt_02/`; the previous state is archived
there as `previous_state.json`. Raw images, older outputs and their exact submitted prompts are retained.

## Review queue and acceptance

The initial read-only scan after these repairs covered 697 accepted jobs, found 30 jobs with current opaque-geometry
or retained historical non-detail flags, and identified 694 acceptances predating the new checks. This scan has a
different scope from the previously mentioned 95 flags; it does not establish that those 95 were all export defects
or all art defects. `audit/placement_review.json` records the measured queue. Re-run the scanner for current counts.

Review flagged outputs first against the raw master, mask and original. For sound existing pixels, `revise` then
`check` preserves the canvas exactly. For faulty extraction, `revise` then `process` reuses the master. Use region
measurements where useful, and targeted imagegen only for defects present in the art. Inspect both contrast proofs
and animation contacts; do not auto-accept an entire batch because dimensions match or flags disappear.

Acceptance now needs concrete review fields and an explanation for every current warning. The checks hash binds
that decision to its report. Export leaves legacy acceptance pending verification rather than pretending it passed
the new review. This is a verification migration, not a request to regenerate all previous masters.

`payload` adds the placement block in `policy.py` to future requests and targeted repairs. It replaces the old
optional-alpha backdrop paragraph with mandatory flat magenta, records that choice with new candidates, and
recomputes collision handling for that actual backdrop. Old masters continue using their recorded original matte.
Keep the package's frozen references/prompts and historical submitted prompts unchanged.

Focused regression coverage includes frame movement with native bounds present, padding/stray faint pixels,
opaque-base loss hidden by faint alpha, native bobbing versus support drift, and rejection of unreviewed warnings.

## Continued review: pedestals, campfire and flags

[Second batch ledger](audit/placement_batch_02.json) records ten additional accepted existing-master revisions
(46 frames): four pedestal sheets, the first six campfire phases, and five blue/gold/green flag sheets. All kept
their raw masters byte-for-byte. Named bases, shafts, stone-ring or lower-pole regions passed; light/dark native
frame comparisons confirmed that rectangle extraction removed the prior compression/position faults.

The remaining two campfire phases (`g00225_v0_s1`) exposed an art defect: over-tall sparks and bright flames,
while ring/log placement was sound. Two built-in imagegen motion repairs reduced some brightness but failed the
native flame envelope, even with explicit 29–30% canvas top limits. They are deferred, with exact prompts and
both candidates retained under `results/g00225_v0_s1/attempt_03` and `attempt_04`. Do not count those attempts
as successful. Revisit by isolating the flame target rather than repeatedly preserving the flawed candidate.

Both beacon-fire sheets (`g00273_v0_s0`, `g00273_v0_s1`) have correctly registered bronze supports but still
need flame repair. Their reviewed findings are in `attempt_02/review_findings.json`. The combined native flame
60th-percentile luminance is 122.57 versus 150.3462 enhanced; a common gain of 0.81525 could correct that tonal
part without changing metal, but cannot fix sparks extending 6–7 native pixels above the reference envelope.
No tonal modification or acceptance has been applied to these sheets. Support checks passing is insufficient
when the moving portion is still wrong.

## Static-prop review and explicit returned-layout recovery

The log-stack master (`g00224_v0_s0`) repeated the same object in several positions. Its intact upper-middle copy
was recovered with a raw-hash-bound [layout mapping](audit/g00224_v0_s0_layout.json), one uniform sampling scale,
and the original empty native margins. This avoids resubmitting sound artwork. The helper now accepts `--layout`
for this explicit case, preserving all original jobs/masters and recording the override in the checks.

The checkerboard detector also falsely flagged gray trash touching a magenta sheet border. It now requires a
predominantly neutral border with two substantial separated flat gray levels; arbitrary gray material does not
qualify. This is a diagnostic correction, not acceptance of that trash master: both old attempts added flames to
the native unlit heap and still require targeted art repair.

Measured common corrections restored the horizontal sword and suspended noose views. The noose has less than
0.65 native pixels of lateral overshoot on its very tight 17/6-pixel canvases; the knot, rope endpoints and loop
were inspected and remain intact. This specific edge-rounding warning was reviewed explicitly.

Six stakes (`g17688_v0_s0`) still have excessive shaft thickness after their endpoints are restored, with alpha
coverage 1.834 times native. The red-leaf plant (`g17955_v0_s0`) and pink-flowered bush (`g17958_v0_s0`) still differ
in proportions after a uniform correction. Their measurement files and `review_findings.json` retain that evidence;
do not independently stretch axes to conceal the art defects. The white-flowered bush (`g17959_v0_s0`) passes
placement but needs a lower-foliage shadow/tone correction before acceptance.

The recovered log stack, rose bush (`g17957_v0_s0`), noose views and sword were accepted after light/dark comparison.
Thirteen focused tests now cover layout selection/master-hash validation as well as the earlier placement checks
and the gray-material checkerboard false positive.

## White-flowered bush tone correction

`g17959_v0_s0` is now accepted after a deterministic lower-foliage correction. The opaque lower shadow
luminance medians were 16.093 native and 37.381 enhanced; a 0.430513 gain was applied through a smooth
green-only, lower-region mask. White/pink flowers and alpha remain unchanged. Light/dark proofs confirm
the darker base while retaining leaf detail. Original pixels, measured grade and acceptance evidence are
preserved in `results/g17959_v0_s0/attempt_02/`; no imagegen repair was needed.

## Chandelier and blue torch review

The four-frame chandelier `g17865_v0_s0` now passes current acceptance after unchanged-master
rectangle extraction restored the compressed third/fourth frames. Chain and lower-frame landmarks
pass and the ordered light/dark contacts retain fixed supports with candle flicker.

Blue torch `g07988_v0_s0` had sound wooden supports but flames 4–6 native pixels too tall.
A targeted repair is preserved in `attempt_03`; its companion mask request failed with an output
moderation rejection, so this candidate remains pending cleanup and final review. No acceptance
was recorded and no completed artwork call needs resubmission.

## Sconce detail versus placement

`g17884_v0_s1` passes placement but its smooth final phase differs from the coarse earlier
`g17884_v0_s0` phases; keep sequence acceptance pending consistency review.
`g17891_v0_s0` also passed placement while retaining enlarged pixel blocks. Two targeted
repairs are preserved: `attempt_03` barely improved detail, while native-only `attempt_04`
restored curved metalwork but lengthened several flames by 4–6 native pixels and connected
native detached embers into wisps. It is deferred for flame-only repair. Do not crop tips or
resize the mount to hide this artwork defect. Passing bounds checks is not sufficient visual enhancement.

## Log fire and fountain

`g08012_v0_s0` is a log fire (not a barrel). Six phases were accepted after native-rectangle
extraction and a shared measured flame luminance gain of 145.4234/160.3168. All log-region
bounds match exactly. Minor thin spark-tip deviations up to 2.5 native pixels on the 64-pixel
canvas were explicitly reviewed; no whole-sprite resizing was used.

`g08071_v0_s0` fountain remains pending. Its first water-detail repair in `attempt_03`
retained coarse square spray chunks from the flawed master. Preserve the statue and master;
next repair should use the native water footprint without treating the enlarged blocks as style.

## Radial effect review

`g00896_v0_s0` was accepted after a shared blue midtone grade preserving white cores and alpha.
Measured core-center differences are below 0.76 native pixels per axis across all six phases.
Minor 3.5–4 pixel opaque tip differences on the 128-pixel effect canvas were reviewed as
soft-ray variation, not a displaced anchor. No per-frame fitting was applied.

`g00876_v0_s0` remains pending: the master extends some flames up to 10 native pixels and
changes the pale orange body to a darker red/orange effect. This requires targeted art repair,
not bounds fitting or automatic acceptance of effect warnings.

## Four parallel targeted repairs

Native-only repair references resolved `g00876_v0_s0` (six compact pale-orange phases) and
`g00215_v0_s0` (one unlit rubbish mound). Both passed light/dark and native placement review.
Four concurrent calls returned in 105.4 seconds. The thin-stake candidate now has 1.349 native
alpha area versus 1.834 previously, but still needs shaft/tone review. Fountain `attempt_04`
has finer water detail but lateral spray overshoot up to 9.5 native pixels, so remains deferred.
All candidates and exact prompts are preserved; see `audit/placement_batch_08.json`.

## Plant mask review

The burgundy plant and pink-flowered shrub now pass proportion and light/dark review after
native-only art repair. Generated companion masks shaded opaque leaves; these masks were
retained but replaced with reviewed boundary-derived alpha. Dark material must remain opaque,
not become translucent just because a mask renderer shaded it. See batch 09 and per-attempt
mask provenance. Six stakes remain deferred for shaft width and tonal correction.
