# Drop-in x2 fitting and matte cleanup

## Restoration finish gate

Reject masters that merely redraw the native pixel grid as larger squares, mosaic patches, stair steps or
repeated dot highlights. Higher canvas resolution and passing registration do not prove restoration.
Inspect both the raw master and exact x2 export for continuous painted surfaces, faithful curved contours and
resolved material detail. Preserve intentional angular symbols and painted marks; do not blur them into smooth
shapes. A smoother result that changes the design also fails. `queue.py payload` adds this requirement to every
imagegen prompt, including individual repairs; recorded historical prompts remain unchanged.

Exact dimensions are necessary, not sufficient. The artwork must occupy the same logical coordinates as the
native image. A 32x32 source containing a 20x24 object needs a 64x64 export containing approximately 40x48 object
pixels at twice the original offset, not a smaller centered object surrounded by extra padding. Keep logical
anchors and equipment offsets. Never trim/recenter each variant or stretch it independently to alpha bounds.

## Measured and visual fitting

`queue.py compare CELL_ID --artifact /absolute/path/cell.png --output-dir /absolute/path/review` creates:

- Source/output hash-bound footprint measurements for every native consumer's transparency profile.
- Native x2 reference, restored x2, and overlay comparisons, plus views at native logical display size.
- An unapproved registration JSON requiring actual review notes and at least three named, spatially separated
  landmark pairs (`source_xy` in native region-local pixels; `restored_xy` in x2 region-local pixels).

`accept` recomputes the measurements. At alpha thresholds 16 and 128, bounds and centroid may differ by at most
two x2 pixels, occupied area must remain within 90–110%, and silhouette intersection-over-union must be at least
0.85. These are conservative rejection guards, not proof of visual quality. Blank/nonblank changes also fail.
Legitimate edge refinements can trip a guard: inspect the actual defect and source before changing a policy;
never forge measurements, flatten glows or force a native pixel mask over misplaced generated art to pass it.

Every named landmark must remain within two x2 pixels of twice its native coordinate. Measure actual rendered
features (blade tip/hilt/guard, boot opening/toe/heel, eye/mouth/chin, panel joins/glyph corners); do not simply
write expected coordinates. Alpha bounds cannot detect a small face on a full opaque portrait or a small symbol
on a full opaque button. Check internal scale and spacing visually and reject filler, lost components, padding,
changed framing or distorted proportions even if numeric limits pass. Uniform deterministic regions require
visual notes but no invented landmarks. Font regions use glyph geometry and joins.

Review every generated sheet and every cell at final size, related states together, and reconstructed atlases as
complete canvases. The isolated in-game preview remains required for attachment, layout and picking validation.
These checks do not constitute an independent automatic visual plausibility model.

## GUI foregrounds over separately restored backgrounds

User direction (2026-09-22): restore separable GUI foregrounds on **transparent PNG canvases** when they
will be drawn over a separately restored background. A legacy BMP containing copied wood, parchment or panel
pixels does not by itself make that backing part of the icon. Independently repainting that backing in every
animation frame can create rectangular seams and inconsistent backgrounds when composited.

Identify the compositing role from the native artwork and its consumer. For overlay objects such as the dagger,
globe, quill/scroll and hourglass controls, preserve the object and its own materials; omit the shared panel behind
it. A scroll's own parchment and an hourglass's wooden frame remain artwork. Complete pages, portraits, scenery
and background panels retain their intended opaque content. Do not apply background removal to all GUI assets.

Keep the full native canvas, object placement, margins, silhouette, internal landmarks and animation/state order.
Request genuine alpha outside the foreground, including internal holes; preserve appropriate soft glass/glow
edges without a painted checkerboard or baked matte. Review edges over both light/dark colors and the eventual
restored background. Transparency does not authorize trimming, recentering or changing object scale.

Keep native references and frozen contracts as provenance. Record an explicit user-authorized foreground-alpha
override in session-local payloads when the historical cleanup contract says `opaque_canvas`; do not silently
rewrite that contract. Preserve already submitted prompts and raw returns, and classify baked backing as an
`alpha_matte` / `page_composition` follow-up. Use a foreground-only repair when removal would damage or obscure
the object. Acceptance, compositing validation and runtime installation remain separate steps.

Suggested prompt clause: "Restore only the foreground object and its own materials. Omit the copied underlying
panel/background. Use genuine transparent alpha outside the object and through its holes. Preserve the complete
native canvas, exact object coordinates and state order; do not crop, recenter or enlarge the object."

## Magenta workflow requested for cutouts

For matte-based cutout jobs without the foreground-alpha override above, execution prompts explicitly request
an **opaque uniform #FF00FF / RGB(255,0,255) extraction matte**, no painted
checkerboard, gradient, shadow, colored bounce or magenta halo for `alpha_cutout_or_effect` cells. Do not remove
the artwork of opaque backgrounds. Spell pairs use the transparent-foreground policy below; multi-profile indexed sources must
retain their separate native key/index regions rather than collapsing them into a single mask.

Use the established [creature cleanup procedure](../../creatures/DIRECT_SPRITE_WORKFLOW.md#5-extract-transparency-and-remove-contaminated-edge-colors):

1. Inspect and retain the raw sheet before resizing. Identify actual matte variation, real pink/purple materials,
   thin features, holes and soft effects. A painted checkerboard is a failed matte, not transparency.
2. Extract soft alpha using local foreground/background estimates and unmix matte contribution from edge RGB.
   Removing exact #FF00FF pixels alone is insufficient. The worked implementation is
   [clean_edges.py](../../creatures/mm6_goblin/direct_ai_attack/clean_edges.py); its no-magenta-material assumption
   must be checked for each batch before reuse. Do not run its global chroma assumptions on pink gems or glows.
3. Inspect partially transparent edges and a narrow opaque contour band on light and dark backgrounds. Rank
   candidate spill with alpha-weighted `max(0,min(R,B)-G)`; confirm against native/intended colors. Repair confirmed
   contamination locally, preserving alpha and clean interior RGB. No global desaturation or erosion.
4. Resize premultiplied `RGBA -> RGBa -> resize -> RGBA` after cleanup. Repeat the contour audit on final x2 exports;
   filtering can reintroduce spill. Retain raw/cleaned/final evidence and exact cleanup parameters in the attempt.
5. Check fine strokes, holes, glow falloff, fitting and state continuity after cleanup. Keep an unresolved cell
   deferred rather than removing intended material to obtain a low chroma score. Accepted siblings remain intact.

Color contamination repair is deterministic postprocessing of generated art, as in creature restoration. It does
not need a new imagegen call unless the art itself is defective. Matting is an estimate; a single flattened
magenta image cannot uniquely separate a genuinely magenta translucent foreground from its background. Such
cells need source-informed protected regions and individually reviewed cleanup, not blanket chroma removal.

This policy is applied by `queue.py payload`; do not submit the older frozen `jobs.json` prompt directly.

For opaque cutouts with intentional purple interiors, `matte.py` implements spatial foreground-core selection
followed by local alpha estimation and RGB unmixing. It preserves the core's original RGB instead of assuming all
purple is spill. The Lich Jar pilot is the first reviewed use. Inspect/tune its explicit seed/fringe parameters for
each new material; it does not automatically solve magenta translucent effects. `test_matte.py` checks opaque
purple preservation, soft-edge unmixing and refusal of an all-matte input.

## Page-backed spell artwork

### Transparent foreground generation — user direction, 2026-09-22

Generate spell illustrations **and their glyphs on transparent backgrounds**, preserving their full native
canvas, offsets, paired-state geometry and faint ink. Do not generate parchment, book folds, page ornaments or
rectangular paper patches into the foreground. Restore/upscale the spellbook background separately so generated
paper cannot create seams against it. Native pages/crops are reference-only inputs for separating ink from paper;
they are not extra output targets or evidence of acceptance.

Request actual RGBA transparency, not a painted checkerboard. Verify the returned alpha and inspect fine glyphs,
hatching and soft ink edges on light/dark backgrounds. A matte return requires reviewed cleanup before it qualifies
as a transparent foreground. Preserve raw returns and prompts. Previously generated paper-backed masters remain
unaccepted foregrounds until their paper is removed and their edges, geometry and symbols are reviewed.

Apply the same separation to analogous overlays whose backing panel/page is restored separately, after checking
the consumer contract. Do not remove intrinsic opaque scenes or collapse multi-profile key/index regions.
Final composition/export must still follow the consumer's format and the exact reviewed page placement; this
generation policy does not change frozen runtime contracts or automatically accept foreground artwork.

The first Air spell sheet failed full-page review because generated paper produced rectangular seams. A smaller
pair retained geometry but still changed paper. Air Resistance then used `payload --pair-index 0 --spell-ink-matte`:
the accepted page/crop remained an input, while imagegen extracted the restored drawing on magenta. Creature
cleanup, premultiplied resizing, measured per-state translation and a common ink-opacity adjustment preceded
composition over the exact accepted crop. A second contour audit repaired residual pink specks after resampling.

`pilots/air_spells/process_pair.py` supports explicitly reviewed per-spell entries for Air Resistance, Feather Fall,
Fly, Implosion, Invisibility, Jump, Lightning Bolt and Shield. Each has its own landmark patches; the lack of intentional
purple was checked in their native references. A processor entry is not visual acceptance; consult the checkpoint for
the accepted attempt and review status. These
spells. Do not reuse their coordinates or chroma assumptions on other spells. Each accepted assessment directory
retains a script snapshot, parameters, page dependency hash and actual visual notes. Feather Fall excludes baked
book-border fragments from generated ink so assembly retains the accepted ornament. Fly excludes the book fold.

Native spell key rectangles reserve overlapping UI regions. Restoring those rectangles as a canvas contract is
different from fitting the drawing. Record whether any generated ink enters the reserved regions; do not use the
native mask to conceal cropped or misplaced art. Final footprint checks are trivial for much of a page-backed
icon, so the actual internal landmarks, glyphs, ink edges and full-page state comparison are mandatory. Untouched
page pixels must match the accepted page and remain identical between states. This does not approve unrelated
paper, glow, or multi-profile assets for generic ink extraction.

The active `air_v1` preview layout revision uses native parchment correspondence and original/mixed runtime review
to correct the Air positions. Existing accepted ink was deterministically recomposed with `--current-layout` and
new hash-bound reassembly/registration reviews, preserving its original attempts and pre-revision outputs. New
generation uses the current `queue.py payload` crops directly. Never apply current positions to old assembled paper
without revising its crop, and never count deterministic reassembly as a new imagegen call.

Jump (`sba05a/b`, incorrectly called Water Walk in earlier handoffs) has native widths 125/126. Its exports remain
250x274 and 252x274; the engine draws both complete textures into the declared 126x137 button. The processor samples
the same accepted page region into each physical canvas, and models the full-quad bilinear draw for page review.
This introduces a small, explicitly measured background sampling difference; it does not meet literal pixel identity
between states. Record both the difference and deviations from that expected sampling baseline, then inspect actual
selected/unselected game states for seams/flicker. Jump passed that review (mean channel difference about 0.495 and
maximum 7 in the x2 simulation; no extra background difference away from ink). Equal-size pairs still require exact
unpainted-page equality. Never pad or stretch an exported native canvas to force both states to the same dimensions.
