# Sprite scale diagnosis and reversible correction

Recorded 2026-09-24 from the MM6 Cleric review and subsequent audit of the 60-family acceptance queue.
Use this reference when a restored animation appears to change size between frames or generation-sheet rows.
It preserves the investigation and proposed repair method; it does not start generation or authorize bulk repairs.

## Current state and where to resume

- The Cleric front-walk scale trial exists. The user viewed it and said it looks better. It has not been rebuilt
  from high-resolution sources, installed, or formally accepted into the production package.
- The broader MM6 audit is complete as a screening pass. Several examples were checked visually in static contacts.
  The candidate list is not a list of approved corrections.
- The [deterministic classifier](#6-deterministic-classifier-and-measurement-gated-solver) now screens every current
  MM6 frame and includes a body-dimension solver with explicit uncertainty and withheld checks. Existing annotations
  are screening evidence, not automatically verified body measurements. No bulk correction has been applied.
- The acceptance viewer now saves translation offsets, per-frame scale/anchor proposals, guides, notes, and
  regeneration flags. Its browser scale preview supports immediate measurement-based trials without changing PNGs.
  The earlier Cleric comparison remains a separately built trial package; see the viewer's interactive-size documentation.
- Original artwork and the main viewer's saved adjustments/decisions were preserved during the trial and audit.

Primary records:

| Record | Location |
| --- | --- |
| MM6 audit findings, inspected contacts, candidate table | [Audit summary](mm6_remaining/quality_review/row_scale_audit/SUMMARY.md) |
| Complete repair/review queue: creature, action, view, animation position, exact frame names | [Repair and review list](mm6_remaining/quality_review/row_scale_audit/REPAIR_REVIEW_LIST.md) |
| Measurements, source/manifest/registration hashes, visual-review notes | [Audit JSON](mm6_remaining/quality_review/row_scale_audit/audit.json) |
| Shared screening implementation | [audit_row_scale.py](mm6_remaining/quality_review/audit_row_scale.py) |
| Cleric correction factors, landmarks, hashes and preview limitations | [Trial comparison JSON](mm6_cle/redo_2x/review/uniform_scale_trial_v1/comparison.json) |
| Cleric original/current/trial still comparison | [Front-walk contact](mm6_cle/redo_2x/review/uniform_scale_trial_v1/front_walk_comparison.png) |
| Viewer operation and checkpoint semantics | [Acceptance viewer](mm6_remaining/acceptance_viewer/README.md) |

Keep this document as the durable interpretation. Rerunning the audit writes a fresh report and does not preserve
the manually added visual-review notes. Use a new output directory when rechecking changed assets:

```sh
python3 -B level_generation/creatures/mm6_remaining/quality_review/audit_row_scale.py \
  --output /tmp/mm6-row-scale-recheck
```

## 1. Distinguish pose height from character scale

Native frames can legitimately differ in height: crouching, walking, jumping, raising a sword, and an overhead
swing all change the silhouette. Equalizing the restored frames' heights would erase native motion.

Compare each restored frame against **its own corresponding native frame**, then compare the resulting ratios.
For a corresponding measurement in frame `f`, define:

```text
N_f = native measurement, in native logical pixels
P_f = restored measurement, in physical export pixels
T   = export pixels per native logical pixel (2 for these packages)
q_f = P_f / (T * N_f)

relative scale change of frame 4 versus frame 0 = q_4 / q_0
relative percentage change                     = 100 * (q_4 / q_0 - 1)
```

Example: original frame 0 is 200 pixels tall and its restoration is 400; original frame 4 crouches to 180 pixels
and its restoration is 324. Their normalized ratios are 1.0 and 0.9. The native crouch is already accounted for;
frame 4 is another 10% shorter than expected for that measurement. A matching 2× export would measure 360 pixels.

Frame 0 is a comparison baseline, not automatically ground truth for the restored character. It might itself be
mis-scaled. Check absolute native-normalized measurements and several good reference poses before choosing a target.
The inverse ratio gives a candidate correction: a ratio of 0.9 requires `1 / 0.9 = 1.111...`, not a 10% enlargement.

## 2. Which measurements can establish overall scale?

Whole-silhouette height is useful for screening, but equipment, hair, wings, flames, and pose changes can dominate it.
Even head-to-sole height can change because of different leg bending or body proportions. A height discrepancy alone
does not establish that the entire frame should be uniformly resized.

For a promising candidate:

1. Mark recognizable corresponding body features on the actual native and restored images. Depending on the
   creature/view, use head width/height, shoulder width, shoulder-to-pelvis distance, or visible joint distances.
   Compare every feature with its counterpart in the same pose; account for foreshortening and occlusion.
2. Inspect the marked points. A color detector can select a staff, sword, helmet ornament, or background fringe.
   Reuse existing valid annotations, but do not treat saved landmark names as proof of correct correspondence.
3. Calculate native-normalized ratios for several independent body dimensions, including a horizontal dimension
   where visible. If they consistently indicate approximately the same size error, uniform scaling is plausible.
4. Fit the candidate using a subset of points, then check at least one independently located feature withheld
   from that fit. Matching the points used to compute the adjustment only validates the fit arithmetic.
5. Compare neighboring frames and sheet boundaries at fixed coordinates, then inspect playback if motion or contact
   remains uncertain. Preserve the original movement of the head, planted/moving feet, and held equipment.

If the head matches but the torso is short, or height and width require different corrections, investigate a pose
or proportion defect. Do not automatically stretch axes separately or deform just the torso. Selective regeneration
may be appropriate after checking whether a uniform trial can actually preserve the already good features.

Small features have large relative pixel uncertainty. A one-pixel annotation error on a 20-pixel feature is 5%.
Use sufficiently separated points and record uncertainty; the audit's 2% threshold is a shortlist threshold,
not an acceptance tolerance or an automatic repair trigger.

### Original transparency and coordinates

Native BMP transparency may be represented by a palette entry that displays as magenta. Use the source format's
known transparency entry and existing extraction pipeline. Do not use a broad "magenta-looking RGB" removal rule;
that can remove genuine material colors. The viewer's `native_variants/*.png` already contain converted alpha.

These native references are already placed on the shared canvas with historical integer offsets. Apply only the
appropriate exact-anchor correction when drawing them; do not add the full `native_offset` a second time.
Preserve fractional native coordinates: half a native pixel is one pixel at 2×. Follow the manifest and
[exact anchor contract](SPRITE_ATLAS_VARIANTS_PIPELINE.md#exact-native-anchor-placement).

Measurements should use canonical, unmirrored asset coordinates and a known tier. Viewer zoom and the game's
per-frame scale are display transforms, not the generated-art scale. Compare both sides with identical display
transforms, or remove them before measurement. User translation nudges affect placement but not within-frame lengths.

## 3. How to calculate and apply an adjustment

| Diagnosis | Candidate action |
| --- | --- |
| Body dimensions match; landmarks have a common positional displacement | Translation in X/Y |
| Independent body dimensions agree on a common scale error | Uniform X/Y scale, then translation |
| Different features require incompatible scales or translations | Inspect pose/proportions; local art repair or selective regeneration may be needed |
| Uncertain landmarks, occlusion, or inconsistent evidence | Keep a review flag; do not invent a correction |

A simple fit uses native points `n_i` and restored points `p_i`, both in **native logical coordinates**:

```text
minimize sum_i w_i * || s * p_i + t - n_i ||²

s = one positive uniform scale (same in X and Y)
t = [tx, ty], translation in native logical pixels
```

With weighted centroids `p_bar` and `n_bar`, the unconstrained scalar fit is:

```text
s = sum_i w_i * dot(p_i - p_bar, n_i - n_bar)
    / sum_i w_i * ||p_i - p_bar||²
t = n_bar - s * p_bar
```

Require a nondegenerate set of points and a plausible positive result. Bad correspondences or changed poses can
produce a mathematical solution without a useful repair. Do not add a rotation merely to conceal a changed pose.
For a selected anchor `a`, an anchored trial can instead use `t = n_a - s * p_a`; choose the anchor according to
the native action. The Cleric trial used head-to-sole span for scale and the head for translation, with neck as
the independent check. That choice is not universal for walking, flying, or collapsing creatures.

### Production correction: resample from retained high-resolution artwork

Use the highest-resolution retained, correctly extracted and cleaned generated frame, before the final 2× export
resize. For an undersized figure, downsample it **less**. Keep the export tier at 2× and adjust how much of that
coordinate system the figure occupies.

Example: intended height 400 export pixels, current height 390. The candidate multiplier is
`k = 400 / 390 = 1.025641...`. Multiply the existing raw-to-export scale by `k`, equally in both axes, and recompute
translation against the selected original landmarks. A tighter crop or atlas rectangle may change size.

When a current mapping is `p = S * raw + b` and the proposed correction in the same physical coordinate system is
`p_new = k * p + d`, compose it once:

```text
S_new = k * S
b_new = k * b + d
```

Record whether coordinates refer to the raw sheet, extracted cell, aligned canvas, or atlas crop. Cropping offsets
and the native anchor correction must each be applied exactly once. Use padding before transforms and verify that
no opaque pixels or thin features were clipped at any stage.

Resample color with premultiplied alpha. Apply the same geometry to coverage masks and palette variants; mask channels
are material coverage, not ordinary RGBA color. Preserve the established color processing and rebuild aligned
masters, masks, crops, matching atlas placements, variant previews, and dependent metadata. If only final-resolution
masks exist, record that limitation rather than claiming a wholly high-resolution reconstruction.

Recalculate genuine generated sampling after enlargement. If `S` maps raw pixels to 2× physical pixels, sampling is
`2 / S`; after multiplier `k` it becomes `2 / (k * S)`. Enlarging a raster does not create source detail. Preserve
the applicable ≥2× or stricter >2× requirement and flag any proposed correction that would violate it.

Resizing an already exported 2× frame is useful for a quick reversible preview, as in the Cleric trial. Prefer
rebuilding from the retained high-resolution source when adopting the correction to avoid an extra resampling step.

## 4. Evidence from MM6

### Cleric front walk: completed preview

Frames a/b/c and d/e/f came from the top and bottom rows of the same retained sheet,
`mm6_cle/redo_2x/raw/walk_0_redo_01_v1.png`. All six used the same recorded raw-to-export scale,
`0.7855917667238422`. The diagnosis traced the exported pixels to that source; d/e/f had shorter native-relative
head-to-sole spans. Existing downward viewer nudges helped the feet but made the heads lower.

| Frame | Trial uniform enlargement | Previous saved offset, physical pixels |
| --- | ---: | --- |
| `clewald0` | +2.564771% | `[2, 13]` |
| `clewale0` | +1.482581% | `[0, 13]` |
| `clewalf0` | +2.477035% | `[1, 15]` |

The trial resized existing 2× artwork with a uniform premultiplied-alpha bicubic transform. It replaced those three
compensating offsets in its isolated checkpoint, leaving the main checkpoint intact. All other 56 Cleric masters
were unchanged. Head/sole Y residuals were below 0.2 native pixels; the independent neck Y residual was at most
1.34 native pixels. These are measured landmark residuals, not a universal quality guarantee.

The user reported that the preview looks better. The agent inspected still comparisons and mechanically verified
six-frame timed advancement in the browser; it did not claim to have watched the animation. The package remains
an experimental preview. Preserve the earlier checkpoint if preparing a high-resolution production rebuild.

The isolated viewer can be restarted from the repository root:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --port 8766 \
  --state-dir level_generation/creatures/mm6_cle/redo_2x/review/uniform_scale_trial_v1/viewer_state \
  --package level_generation/creatures/mm6_cle/redo_2x/review/uniform_scale_trial_v1/current/manifest.json \
  --package level_generation/creatures/mm6_cle/redo_2x/review/uniform_scale_trial_v1/trial/manifest.json
```

Open `http://127.0.0.1:8766/#mm6_cle_scale_trial`; choose current/trial using the family selector. Server availability
is session-dependent. Reuse the running server if already present.

### Broader row screening

The audit covered the current selected packages in the 60-family queue: 3,481 frames and 1,257 source sheets.
It mapped 3,478 frames to sheets; one retained Goblin checkpoint lacked a source rectangle and two Cactus endpoints
were empty. Completeness of this queue does not establish that every package meets the strict >2× sampling target.

- 588 sheets had multiple rows. Row identity came from retained extraction rectangles, not animation frame numbers.
- 275 sheets had a common usable saved landmark span and at least two distinct generated cells in compared rows.
  Reused pixel aliases counted once. **84 sheets across 32 families** crossed the 2% row-difference screen:
  68 had smaller later rows and 16 larger later rows.
- Including silhouette-only screening, the shortlist contained 131 sheets across 47 families. This broader set
  includes more possible false positives from effects, equipment, and changing poses.
- 83 of the 84 landmark candidates used one export scale across the sheet. This supports variation in generated
  geometry rather than a different export resize; it does not prove row layout caused that variation.
- The screen compared per-frame restored/native ratios before taking row medians. It did not assume native frames
  had equal heights. Saved landmark spans were prior annotations; the audit did not freshly locate multiple body
  features on every frame.

Examples inspected in current native/restored contacts:

| Family / sheet | Later row's native-normalized height relative to first row |
| --- | ---: |
| Dwarf standing | -3.21% |
| Dwarf fidget | -4.08% |
| Dwarf front walk, useful counterexample | -0.02% |
| PeasantM4 rear walk (`walk_4`) | -4.50% |
| Thief side walk (`walk_2`) | +3.58% |
| Fire Elemental `walk_3` | -7.06%; changing flame geometry needs separate interpretation |
| PeasantM3 hit | -3.64% |

These percentages describe **relative row differences**, not ready-to-apply enlargement factors. Different rows can
also contain different views or phases. The Thief's width trend disagrees with its height trend, illustrating why
uniform scale requires further checking. Start stronger body-feature diagnosis with Dwarf fidget/standing and
PeasantM4 rear walk; retain well-matching sheets such as Dwarf front walk as comparison evidence.

## 5. Checkpoint and review contract for future repairs

Reuse existing project registration/calibration, review, and acceptance records. For a proposed correction retain:

- Family, canonical frame, generation job, raw sheet/cell mapping, and source/artifact hashes.
- Named native/restored landmarks, coordinate units, uncertainty, fitting points, and withheld check points.
- Original transform and proposed uniform multiplier/translation, with the exact transform order and coordinate origin.
- The measurements supporting the diagnosis, independent residuals, and corrected generated sampling.
- Any existing viewer offsets superseded by the new placement; preserve unrelated edits and the original checkpoint.
- Candidate/trial/reviewed/adopted status, visual-review method, and regeneration flags for unresolved art defects.

The viewer now stores `scale_factor` and `scale_anchor` separately from translation. Existing `offset_px` still stores
translation only; do not silently reinterpret it as scale or apply old compensation twice. The viewer's immediate
resampling does not establish a production raw-to-export transform or replace the evidence requirements above.

For a demonstrated common row error, the existing `calibration_group` mechanism can hold one reviewed scale for its
members. Use a per-frame exception only when the evidence supports it. Continue using a common sequence scale by
default; never normalize all silhouettes independently or assign a fixed multiplier to every lower row.

Make corrections in an isolated package first. Check original timing, native anchors, independent body features,
width/proportions, neighboring-frame transitions, crop reconstruction, masks, variants, alpha edges, and sampling.
Do not infer visual acceptance from a numerical fit or a script advancing animation frames. An adopted rebuild
changes artifact hashes and requires affected review; keep previous artwork and decisions as historical checkpoints.

## 6. Deterministic classifier and measurement-gated solver

User scope: translation is handled manually in the acceptance app. The classifier does not propose translations,
alter artwork, save viewer edits, mark acceptance, or call imagegen. Confirmed proportion/pose defects may eventually
need regeneration; missing or occluded measurements alone do not establish a defect that regeneration would fix.

Run the shared [classify_scale.py](mm6_remaining/quality_review/classify_scale.py):

```sh
python3 -B level_generation/creatures/mm6_remaining/quality_review/classify_scale.py \
  --output /tmp/mm6-scale-classification-new
```

The output directory must not exist. `--family mm6:cle` limits an exploratory run; omit it for all 60 current
packages. The classifier uses the same package selection as the row audit, but freshly reads every master,
including single-row sheets, unbound masters, and frames absent from the row shortlist. It records current source,
manifest, registration, native-image and restored-image hashes. `classification.json` holds measurements, frame
decisions, sheet/row summaries, and all palette/action/view/position/mirror bindings. `frames.csv` is the compact
complete frame list; its action bindings collapse identical palette bindings for readability. `SUMMARY.md` gives
family counts. Source-cell aliases are deduplicated for row medians, but remain explicit frame records.

The initial complete run is saved in [scale_classification_v1/SUMMARY.md](mm6_remaining/quality_review/scale_classification_v1/SUMMARY.md).
It covers all 3,481 frame names. No verified multi-dimension annotations were supplied, so it proposes no new
production downsample factors. Its complete coverage is coverage of deterministic screening, not a completed
anatomical audit. The separately reviewed Cleric trial remains useful evidence and is not superseded by this screen.

### Screening is deterministic, anatomical identification is not solved

The first pass reuses named registration landmarks, excluding declared diagnostic landmarks. It compares X/Y
spans of at least 20 logical pixels with their own native counterparts. It also measures alpha>=128 silhouette
height and width directly from the images. Saved landmarks have not been freshly verified against these images;
silhouettes can include weapons, wings, hair and effects. Neither is silently promoted to a body measurement.

For screening, each endpoint is assumed uncertain by one native logical pixel, so a span has a conservative
two-pixel error on each image. These are explicit heuristic bounds, not empirically calibrated confidence intervals.
The correction interval for native span `N ± eN`, current exported span `P ± eP` and tier `T` is:

```text
[T * (N - eN) / (P + eP), T * (N + eN) / (P - eP)]
```

Landmark and silhouette screens are reported separately. Within a screen, incompatible intervals produce a
proportion/pose review flag. Compatible intervals excluding 1 and a median nominal correction at least 2% from
1 produce a size signal. Both X and Y evidence gives a uniform-scale candidate; otherwise it needs more body
measurements. The threshold is configurable with `--screen-percent`. It is a shortlist setting, not acceptance.

| Screen | Meaning |
| --- | --- |
| `uniform_scale_candidate` | Available proxy measurements permit a common scale change; verify actual anatomy. |
| `size_signal_needs_body_measurements` | A size discrepancy is detected, but horizontal/vertical evidence is incomplete. |
| `proportion_or_pose_review` | Some proxy dimensions disagree; inspect anatomy, correspondence, equipment and effects. |
| `no_scale_signal` | No discrepancy established by this screen; not a pass or complete anatomical verification. |
| `insufficient_evidence` | No usable screening dimensions. |
| `empty_endpoint` | Both native and restored alpha are exactly empty; retain the endpoint. |
| `missing_foreground_review` | At least one image has no alpha>=128 foreground and the pair is not exactly empty. |

The family summary prioritizes conflicting proxies over a scale candidate. Check the separate screens and exact
measurements in JSON to understand the reason. All sheets/rows receive summaries, but a row difference never
assigns the same correction to every member. A matching neighbor or first row is not treated as absolute truth.

Viewer offsets are ignored: translation cannot change these spans, and the user owns that work. Existing
regeneration flags/notes are included only when the viewer's full artifact digest matches. Historical note versions
are listed separately. No saved checkpoint is written or rebound to new artwork.

### When a downsample proposal is allowed

An optional `--measurements path.json` supplies visually verified body dimensions for selected frames. Its structure
is `{ "mm6:cle": { "clewald0": { ... } } }`. Each frame entry contains:

- `provenance`: copy the exact frame `provenance` object from `classification.json`. Stale hashes are an error.
- `verified: true` and `reviewer`: identify who checked the measurements against the actual art.
- `dimensions`: at least two fitting dimensions spanning X and Y, plus a separately located withheld feature.
  Each has a unique `name`, `axis` (`x` or `y`), `role` (`fit` or `check`), `native_length`,
  `restored_length_px`, `native_error`, and `restored_error_px`.

Measure native lengths in logical pixels, restored lengths in current physical export pixels, with display zoom,
mirroring, and game frame scale removed. Errors are positive absolute bounds on the entire span, not on each
endpoint. Use real anatomical correspondences, not silhouette width relabeled as shoulders. Fit dimensions should
cover different body features; the check feature must be separately measured, not a renamed/repeated fit span.
The solver cannot verify the semantic truth of these annotations. Low-confidence, obscured features belong in
manual review, not in a `verified` measurement record.

The solver fits `k * (P / T) ≈ N` using weights `1 / (eN + eP/T)^2`, constrained to the common fitting interval.
Those weights prioritize precise spans; they are not a statistical probability model. Withheld dimensions do not
affect the fitted factor. Every withheld dimension must support it within its own uncertainty interval.

| Decision | Action |
| --- | --- |
| `review_measurements` | Obtain adequate body measurements; no scale proposal. This is the default for legacy annotations. |
| `keep_scale` | A change beyond uncertainty and the deadband is not established; retain the factor. Not visual acceptance. |
| `proportion_or_pose_review` | Verified dimensions disagree or the withheld check fails; inspect for art repair/regeneration. |
| `source_review` | Source mapping, clipping, local deformation, or sampling prevents a supported export proposal. |
| `downsample_trial_candidate` | Propose `new_scale = old_scale * k`; create/review an isolated export before adoption. |

The default adjustment deadband is 1%, configurable with `--adjustment-deadband-percent`. A fit interval overlapping
that unchanged-scale band does not justify a correction. The default is an engineering restraint, not a perceptual
tolerance established for every creature. Neither the fit nor the deadband establishes correct pose or anatomy.

The generated-detail estimate after correction is `current_sampling / k`. Prefer recorded effective X/Y sampling;
otherwise record the nominal `T / old_scale` estimate explicitly. Current `redo_2x` replacements retain their >2×
requirement; other packages require ≥2×. Missing raw sources/transforms, recorded clipping, raw hash mismatches and
local geometric deformations block a direct scale proposal. Historical/native endpoint exceptions can appear in
source flags; do not treat those flags as automatic regeneration instructions.

A successful proposal gives a scale only. Rebuild from the retained source, retain the native anchor convention,
and let the user review placement in the app. Recheck actual rounded resize dimensions, clipping, independent body
features, masks, alpha, palette variants, sequence transitions and generated sampling before adoption. A proposed
factor does not perform that work and is not an accepted repair.

Focused logic tests:

```sh
python3 -B -m unittest discover \
  -s level_generation/creatures/mm6_remaining/quality_review -p 'test_classify_scale.py'
```
