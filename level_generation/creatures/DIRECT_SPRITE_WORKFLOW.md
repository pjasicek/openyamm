# Direct MM6–MM8 creature sprite restoration

For deployment and release files, use [Creature sprite deployment](SPRITE_RUNTIME_DEPLOYMENT.md).
Keep PNG exports in `assets_source`; `assets_dev/engine/sprites_new` contains cooked GPU pages only.


For scheduling several independent sheets, use [multi-request image-generation guidance](../sprites/PARALLEL_IMAGEGEN.md).
It records the measured ten-call trial, batching limits, dependency ordering and per-job checkpoints.

For **non-creature** decorations, ground items, projectiles, weather, FX and UI sprites, use the
[prepared restoration jobs](../sprites/restoration_jobs/README.md). Their soft-alpha and UI rules differ from
opaque creature matting; do not apply this creature workflow wholesale to spell effects.

For the concise end-to-end recipe including **selective masks/variants, atlas JSON, and future engine deltas**, start
with [SPRITE_ATLAS_VARIANTS_PIPELINE.md](SPRITE_ATLAS_VARIANTS_PIPELINE.md). This document supplies the detailed
restoration techniques when needed; do not turn every section into an extra per-frame generation/review pass.
The pipeline's lean default supersedes historical viewer/report requirements here. Read only the technique needed
for the current operation; reuse shared tools. Deterministic shared-template viewer export is fine; browser traces
and per-creature viewer coding are not required.

Use this workflow when the requested deliverable is enhanced 2D creature sprites for a given **view direction and
animation**, such as front Attack, side Walk or rear Fidget. Generate the enhanced frames directly from the original
art. A Blender model, rig and new 3D render are not required for this route. For those deliverables, use the separate
[sprite-to-3D workflow](SPRITE_TO_3D_WORKFLOW.md).

The working order is **audit native frames → pack one direction/action into a source sheet → AI-enhance the whole
sheet → static screen and visual pose/detail review → extract alpha and clean edge colors → pack and inspect**.

Use [Packed animation sheets with outline-only anatomy guides](PACKED_ANIMATION_OUTLINE_WORKFLOW.md) as the
preferred generation recipe. It records one complete animation per stored view, shared tight native cropping,
matching separate outlines, detailed appearance authority and the corrected Goblin prompt. Its whole-cycle scope
supersedes automatic splitting suggestions below; preserve and report actual resolution limitations.

The driver liked the [six-frame MM6 goblin attack restoration](mm6_goblin/direct_ai_attack/README.md), then accepted
the [deterministic edge cleanup](mm6_goblin/direct_ai_attack/edge_cleanup/README.md). This is the worked example.
Its six frames, magenta key, crop coordinates and cleanup thresholds are case-specific, not universal MM6–MM8 settings.

## 1. Establish which frames actually exist

Inspect local creature descriptors and sprite-frame data alongside the image files. A filename prefix does not by
itself establish creature identity, action ordering, palette or viewing angle. Exclude unrelated filename matches.
Record the following before generating:

| Field | Required information |
| --- | --- |
| Source | World/creature, descriptor/group names, image paths and hashes |
| Direction | Stored direction index and its observed front/oblique/profile/rear meaning |
| Animation | Ordered poses, source image for each pose, repeated/held frames and loop behavior |
| Timing | Per-frame durations, total duration, units/conversion and any contact/recovery markers |
| Geometry in the image | Canvas dimensions, common scale, ground/origin pivot, visible bounds and padding |
| Transparency/color | Native transparency index/key, palette variants, runtime scale/anchor flags |

An action may have only a frontal view, while another stores five views and mirrors the remaining directions.
Do not assume that every action has eight distinct images. If a requested view is missing, document that generating
it is an inferred new view, not restoration of an existing frame. Establish its anatomy/equipment orientation from
available neighboring views before expanding the task. Do not mirror a weapon into the other hand without review.

Keep the original pose count and timing by default. Directly enhancing six attack poses does not create sixteen
new animation poses. Additional in-between frames are a separate motion-authoring task requiring review.
Preserve originals and stage new art under the creature project; do not overwrite native assets or allocate live
frame-group IDs unless installation is requested.

## 2. Pack the original frames into one reference sheet

Use deterministic image processing to assemble the actual native images; this preparation is not AI enhancement.
For the preferred packed-outline method, pack **one direction × one complete animation** per sheet.
Follow the authoritative [crop and batch budget](SPRITE_ATLAS_VARIANTS_PIPELINE.md#crop-and-batch-for-at-least-2-generated-detail)
before choosing pose counts. Six frames in three columns and two
rows worked well for the goblin. A very wide 1×6 layout can waste the available output height; choose the layout
according to frame shape and current tool limits, not a fixed universal grid.

1. Decode native transparency correctly, preserving opaque foreground RGB. Never treat an unrelated palette color
   as transparent just because it resembles the background.
2. Retain a common logical canvas and source scale for every frame. Compute the union of visible bounds across the
   complete action/stored view, then remove only the empty exterior shared by all poses. Use that same native crop
   and padding for all cells, including overlapping batches. Record its offset from the original canvas and verify
   reconstruction of native alpha and premultiplied foreground RGB. Do not independently trim, center, stretch or
   fit each silhouette: that destroys motion and ground alignment.
3. Add equal padding sufficient for weapon tips, ears, raised limbs and motion extremes. Six native pixels is a
   starting point, not a universal requirement. If source art already touches
   or clips its canvas edge, record that limitation; extra blank padding does not restore missing art.
4. Arrange poses in an explicit order, normally left-to-right then top-to-bottom. Save cell rectangles, original
   canvas offsets and the pose-to-source mapping in a manifest. Keep labels in a separate review sheet.
5. If enlarging the low-resolution input for inspection, use nearest-neighbor to expose the original pixels. Keep
   that reference enlargement distinct from the AI-generated output and from final antialiased downsampling.
6. Save the native cell size and candidate grid dimensions. For each layout, divide the observed delivered width
   and height by the corresponding native sheet dimensions; both ratios must reach two, preferably 2.2 or more.
   Include safety margins and gutters. Try tighter common cropping and a better grid shape; preserve the complete
   cycle and record any remaining shortfall in packed-outline mode. If the chosen scope permits splitting,
   a 3×3 layout wastes a ninth cell for an eight-frame action; two 3×2 sheets can cover it using four
   overlapping poses (frames 1–6 and 3–8). Keep exactly eight selected runtime poses. Two 3×2 sheets are an example,
   not a fixed requirement; use the largest coherent group that meets the measured budget.

Prefer genuine alpha in the generated output, explicitly forbidding painted checkerboards. Native reference sheets
may retain a flat matte for readability; state that this reference background is not the requested output background.
For the fallback opaque-background route, fill transparent pixels with a flat key color absent from the subject.
Magenta separated the green/brass/iron goblin well. It would be inappropriate for a creature with intended purple or
magenta clothing, glow or translucent material. Choose and validate the matte method for the actual subject.
Ask for no colored spill, no halo, no ground shadow and no background gradient, but do not assume the model obeyed.

Worked preparation: [prepare_reference.py](mm6_goblin/direct_ai_attack/prepare_reference.py) and
[source layout](mm6_goblin/direct_ai_attack/source_layout.json).

### Native outlines and internal contrast guides

For the preferred **outline-only anatomy guide**, follow
[Packed animation sheets with outline-only anatomy guides](PACKED_ANIMATION_OUTLINE_WORKFLOW.md). Use untouched
native colour plus an identically packed thin alpha-boundary sheet and selected detailed enhanced appearance.
The guide controls geometry only; preserve wrinkles, texture, material wear and natural shading. Do not request
minimal texture or reduced contrast to remove artificial shading bands. The complete construction and corrected
prompt live in that guide rather than being duplicated here.

The following is the **historical internal-contrast experiment**, distinct from the preferred outline-only method.
Use it only when that contrast-guided method is explicitly requested. It addressed native anatomy drift, especially
shoulder/upper-arm thickness,
joint positions, or overlapping wing roots and forelegs. The driver found the MM6 DragonCover result much better
on 2026-09-25 and selected it for the main staging queue. This is one successful trial, not a controlled comparison
or a guarantee that all proportions are fixed. Placement corrections and visual acceptance remain separate.

1. **Make a deterministic native guide set.** Run the shared [native_guides.py](native_guides.py) against the existing
   family sources and manifest. It decodes the actual base palette, adds an inward silhouette contour, darkens
   existing internal creases and lightly brightens ridges. Alpha-normalized luminance smoothing detects contrast;
   the output uses scalar gain on original RGB, with no image blur, geometry changes or invented anatomy.
   Keep exact dimensions, alpha, native offsets, pivot and animation bindings. The helper verifies these and saves
   source/processor hashes and settings. It produces one base palette by default, not three generated variants.
2. **Inspect the guides against the untouched original.** Existing contrast is not anatomical segmentation. Make
   sure a shadow, wing membrane or equipment edge has not become a misleading apparent muscle boundary. Bypass
   disintegration/fire/corpse actions when body guides are inappropriate. The dragon used 47 guided body poses and
   eight unchanged death/corpse poses. Its guide settings were fine/coarse sigma 1.5/4 native pixels, inward contour
   width 1.45, contour/crease darkening 0.36/0.48 and ridge brightening 0.13; these are recorded trial settings,
   not universal thresholds. The current helper rejects half-pixel placement at 1×; use an exact 2× reference
   preparation path for those sources instead of rounding their offsets.
3. **Supply both versions of the target.** Use the guided native as boundary/layout guidance and the untouched
   native as pose, anatomy and color authority. Add an approved enhanced reference only for appearance/materials.
   Keep a shared padded union crop per action/view, even for single-frame calls. Choose batch size by the actual
   generated-detail budget. The large 512×413 dragon used one pose per call; this is not a new default for smaller
   creatures. Generate one master appearance and derive additional palettes only when in scope.
4. **Explicitly separate pose from identity.** Name the problematic parts and distinguish overlapping structures.
   If a whole enhanced reference causes the model to copy its wingbeat or limb pose, replace it with a cropped
   texture/torso identity reference and describe the target's visible joint and tip relationships. In the dragon
   trial, two wingbeat poses required this correction. Keep the failed returns and exact retry prompts/references.
5. **Register and review normally.** Preserve supplied alpha; inspect low-alpha scatter and actual clipped tips.
   Do not remove legitimate pink flame/mouth colors as matte spill. Use one anatomical scale per coherent living
   animation/view and a native landmark for each frame's translation. Independently check another limb feature;
   detector proposals need inspection on the actual art. Do not fit each silhouette or warp limbs to conceal
   generation drift. Review full native/restored sequences, shoulders and biceps in motion when needed, and retain
   original timing, mirrors and exact exported anchors. The dragon's 55-frame package measured ≥2.586× generated
   sampling at a 2× export tier. Human browser adjustments remain recorded proposals until explicitly rebuilt.

Example preparation (output must be a new directory; this does not replace native art or enhanced masters):

```sh
python3 -B level_generation/creatures/native_guides.py level_generation/creatures/mm6_cdr1 \
  --manifest redo_2x/manifest.json --output original_guides_v2 --preserve-actions death corpse
```

Prompt fragment to adapt to the observed problem:

```text
Image 1 is the target native pose with deterministic contour/contrast guides.
Image 2 is the untouched original of that SAME pose: anatomy, exact pose and color authority.
Image 3 is enhanced appearance/material guidance only; do not copy its pose or proportions.
Match native shoulder and upper-arm thickness, joint positions, forearm length, chest width and wing roots.
Do not mistake wing membranes or wing roots for foreleg biceps. Preserve near/far overlap and foreshortening.
The guides emphasize existing boundaries, not new anatomy or cartoon black strokes.
Preserve the target's native wing sweep, body bobbing, scale and empty margins within the recorded common crop.
```

Retained example: [native guide manifest](mm6_cdr1/original_guides_v1/manifest.json),
[exact prompts, references and selected returns](mm6_cdr1/guided_restore_v1/redo_2x/run.json), and
[staged master package](mm6_cdr1/guided_restore_v1/redo_2x/manifest.json).
Use these to reproduce the method; do not reuse their dragon-specific landmarks or thresholds blindly.

## 3. Enhance the complete sheet in one image-generation request

Read the current imagegen skill and inspect local input images before generation. Use the built-in image tool by
default. Supply the packed original sheet as the pose authority. For another direction or animation of the same
creature, additionally supply an accepted enhanced sheet as the identity/material reference, clearly distinguishing
its role from the new native pose sheet. It must not replace the requested poses.

Starting with all poses together gave useful consistency in the goblin experiment. One-by-one generation was not
tested as a controlled comparison, so do not claim a universal quality advantage. For a longer sequence that would
make each pose too small, use manageable batches with a shared accepted design reference and overlapping reference
poses. Keep only one selected version of each overlap in the final animation.

Adapt this prompt to the observed creature and requested change:

```text
Enhance the supplied original [game/creature] [animation] sprites viewed from [direction].
Input 1 is the exact pose/layout authority: [columns] columns × [rows] rows, ordered [frame sequence].
[Optional input 2 is the accepted identity/material reference only; do not copy its poses.]
Restore coherent high-resolution surface detail for the SAME creature throughout the entire sheet.
Reconstruct continuous contours and fine shading: no enlarged pixel blocks, dithering, blur, smeared features,
sharpening halos or crunchy invented texture. Actual generated detail must be at least twice native resolution.
Preserve each frame's head angle, torso rotation, limb positions, raised/planted feet, handedness,
weapon perspective and foreshortening. Keep proportions, clothing coverage, equipment, palette and lighting consistent.
Maintain equal cells, source-relative positions, common scale and margins. No per-frame recentering or zooming.
Keep every silhouette inside its assigned cell. No omitted/duplicated poses, extra figures, text or grid lines.
Backdrop: genuinely transparent PNG alpha, including empty cells. No painted checkerboard, opaque background,
cast shadows, colored reflections or edge halos. Any matte in the native reference is input guidance only.
Clarify the original design; do not invent accessories or replace the action with a generic animation.
```

Explicitly describe a few easily confused poses when needed. The goblin prompt called out lifted feet, the different
high-sword poses and strongly foreshortened follow-through. Save the exact prompt, input roles/paths, tool mode, raw
generated output and actual returned dimensions. A requested output resolution is not proof of the delivered size.
Never label ordinary interpolation as newly generated detail.
Measure sampling again after registration: divide raw pixels by the native-coordinate distance they represent,
using the shared anatomical scale. The minimum applies to generated detail as well as to 2× packaging. If a returned
sheet falls below it, retain the raw trial but repack the affected sequence into fewer whole poses. Use overlap and
the accepted identity reference to preserve consistency; do not automatically fall back to unrelated single-frame
generations or separately generated weapon/body fragments.

Worked request: [prompt_v1.txt](mm6_goblin/direct_ai_attack/prompt_v1.txt) and
[raw enhanced sheet](mm6_goblin/direct_ai_attack/attack_restored_v1.png).

## 4. Review identity and animation before accepting the sheet

Compare every generated cell against its corresponding original at common canvas scale. Inspect the full action in
order in shared-crop contacts; make a timed preview using native durations only when motion remains uncertain or
when requested. Check face and body consistency, armor/garment changes,
weapon length and hand, blade foreshortening, finger count, raised feet, ground contact, torso turn and recovery.
Review both enlarged detail and the intended display size. A good standalone pose does not establish a good animation.

Inspect generated grid placement before cropping. The goblin's frame-e sword crossed its nominal cell boundary.
An extraction boundary placed in existing empty space preserved the tip without including it in the neighboring
frame. Keep common output canvas origins, record the extraction rectangles and add equal padding. Do not independently
recenter frames to hide generation drift. If figures overlap, are clipped or no longer fit a coherent shared frame,
correct the offending generated cell rather than silently discarding art.

For demonstrated whole-frame position drift, a deterministic translation against visually verified native
landmarks can be sufficient. Follow the
[Dark Elf planted-foot case](SPRITE_ATLAS_VARIANTS_PIPELINE.md#deterministic-correction-of-planted-foot-drift)
for saved landmarks, identical base/mask shifts, clipping checks and before/after playback. Preserve the original
motion and established anatomical scale; this is not automatic silhouette centering or a fix for changed anatomy.

Check clipping at every processing stage, including normalization and shared affine registration before the
anchor correction. Use a padded temporary canvas for transforms and landmark measurement, then assert that the
final aligned crop reconstructs all transformed pixels. An exact inverse translation alone cannot detect anatomy
already clipped by an earlier transform. The Dragon Hunter falling-frame repair in the linked case documents this
failure and the deterministic padded-canvas correction.

Correct a drifting pose with its native frame and the accepted sheet as references, preserving already good cells.
Avoid repeatedly redrawing the whole accepted creature to solve a background-only problem. Retain previous versions
and identify the selected one explicitly. AI detail is a reviewed interpretation, not recovered original high-res art.

### Independent placement review

For apparent size drift, consult [Sprite scale diagnosis and correction](SPRITE_SCALE_DIAGNOSIS.md).
Compare each pose to its own native frame and verify several body features before choosing a uniform resize;
the document preserves the MM6 row audit and reversible Cleric trial, including their limits.

First apply the automatic [exact native anchor placement](SPRITE_ATLAS_VARIANTS_PIPELINE.md#exact-native-anchor-placement)
check to preparation/registration and exported placement. Preserve fractional native offsets in the displayed
references and landmark guides. Perform final visual review on those corrected coordinates, then freeze acceptance;
a later coordinate correction requires affected review and new acceptance hashes.

The MM6 Ogre attack exposed a circular check: brown sword pixels were selected as the crown, then translating
that selected point to the native crown produced a near-zero X residual. That number measured rounding, not
anatomical alignment. Exact atlas reconstruction faithfully preserved the wrong placement. A first fix covered
one raised-sword pose but missed another; unmarked, reduced contact sheets did not prevent premature acceptance.

- Choose anchors from the native action's mechanics. A planted foot is useful for a stationary strike or recoil;
  a moving head alone can introduce foot sliding. Walking, flying and collapsing actors need their own native
  motion references. Do not impose stationary feet or one silhouette center on every action.
- Draw the actual detected points on both images, at native logical size or larger, with the same pivot/ground
  guides in every cell. Review every pose and batch boundary. An unregistered, independently normalized detail
  contact assesses artwork only; it cannot validate gameplay placement. Small overview sheets are navigation aids.
- Check at least one independently located body feature that was not used to choose the transform. Compare its
  native-relative displacement in X and Y across the sequence. Distinguish solver/rounding residuals from this
  anatomical error. Preserve deliberate native motion; document family-appropriate tolerances rather than reuse
  the Ogre's pixel thresholds or color detector for other creatures.
- If a detector selects a weapon, debris, or the wrong body part, inspect all frames and calibration poses that
  use it, including neighboring sheets and overlapping poses. A filename-specific fix alone is not that audit.
- If marker identity, foot sliding or a transition remains uncertain, inspect timed playback before acceptance.
  Producing a GIF or mechanically exercising a browser animation does not establish that playback was watched.
  The acceptance method must state the actual review and its limits.

The shared `mm6_remaining/redo_2x/review_sequences.py` exports both overview and native-size placement contacts.
For explicit annotations, registration may store `review_landmarks` as a mapping from anatomical names to
`native: [x, y]` (logical pixels) and `restored_before_translation: [x, y]` (physical export pixels).
Include the transform anchor and independently measured check points; do not derive the latter from the former.
Existing `placement_landmarks.native_crown` / `restored_crown_before_translation` pairs are also drawn.
Markers expose what the detector selected; their existence is not automatic acceptance.

Mark known unreliable named points in `diagnostic_landmarks`. The shared acceptance freezer rejects a diagnostic
translation anchor or a diagnostic point used by an active annotated scale calibration. This includes a calibration
reference retained from another sheet; unused candidate calibrations do not block acceptance. Replace the invalid
calibration with independently reviewed evidence before reacceptance. The check enforces recorded decisions only:
unmarked or older unnamed landmarks still require visual correspondence review.

If a generation sheet has a demonstrated row-wide anatomical scale discrepancy, named frame annotations may
reference one shared `calibration_group` in the existing `calibration` mapping. Record its members and evidence,
retain the original generation job, and preserve the native anchor path. The registration records which group
actually supplied each frame's scale. This is for a verified common scale error, not per-frame silhouette fitting;
independent features and sequence transitions still need review.

## 5. Extract transparency and remove contaminated edge colors

First inspect the actual PNG mode and alpha values. Prefer supplied real transparency: preserve alpha and bypass
key-color extraction/unmixing entirely. Verify empty background/cells are transparent and composite the artwork on
light and dark backgrounds. A checkerboard shown by the viewer is fine; a checkerboard painted into visible image
pixels is not. Never infer transparency from its preview alone or from the mere presence of an opaque alpha band.
Save the returned background mode and selected extraction branch. Keep clean alpha/RGB unchanged; genuine alpha
still needs the edge, thin-feature and placement checks below. Do not apply a magenta-only extractor to RGBA art,
flatten good transparent art onto a key color, or regenerate it solely to recover the old matte workflow.

The following matte-recovery procedure applies to opaque outputs that actually require background removal.

Inspect the **raw generator output before any resizing**. Compare its RGB with the crop and extracted frame at the
same coordinates. This separates an existing generated fringe from a resampling or alpha-handling bug.

In the goblin case, the raw RGB sheet already contained pink contour pixels. The first extraction only changed alpha
and left those RGB values intact. All six crops were checked against the raw sheet; the contamination predated our
resizing. Replacing only exact magenta pixels cannot remove mixed edge colors or variations in the generated matte.

A flattened edge approximately follows:

```text
observed RGB = alpha × foreground RGB + (1 − alpha) × background RGB
```

For an opaque chroma-key source, use a deterministic **soft matte plus edge-color decontamination**:

1. Estimate confident foreground/background regions for this subject; retain holes between limbs and thin equipment.
2. Estimate partial alpha in uncertain edge pixels using local foreground and background samples.
3. Remove the estimated background contribution from edge RGB. Adjusting alpha alone leaves the key color underneath.
4. Preserve uncontaminated foreground RGB. Constrain spill removal to the uncertain colors/regions instead of globally
   desaturating or recoloring the character.
5. Inspect on both bright and dark backgrounds, especially sword guards, spikes, fingers, hair and other thin details.
   Tune or locally repair demonstrated failures; do not simply erode the whole silhouette until the fringe disappears.

The [goblin cleanup script](mm6_goblin/direct_ai_attack/clean_edges.py) uses NumPy, SciPy and Pillow, local color
estimates, an alpha fit, color unmixing and a remaining-magenta limit. Its thresholds and no-magenta-material assumption
must be recalibrated for another creature. It is a worked deterministic implementation, not a universal matting library.
The driver accepted its improvement; [before/after evidence](mm6_goblin/direct_ai_attack/edge_cleanup/guard_before_after.png)
shows the reported guard on dark/light backgrounds.

### Automatic residual spill check

Make this part of the creature's deterministic processing/export path, and run it without asking the driver:

1. Scan every cleaned frame before resizing, then repeat on frames extracted from the final atlas. Include both
   partially transparent pixels and a narrow opaque contour band: AI-painted spill can be fully opaque. Ignore RGB
   in fully transparent padding when scoring visible contamination. Record matte color and scale-dependent band width.
2. Rank suspect contour patches using the actual matte hue and nearby uncontaminated foreground colors. For a magenta
   matte, alpha-weighted `max(0, min(R,B) - G)` is a useful candidate score, not a universal rejection threshold.
   Protect intentional purple/pink materials and variant colors. Save one concise audit plus a small contact of the
   worst-ranked patches, magnified on light and dark backgrounds, with raw/cleaned/export comparisons as needed.
3. Inspect that contact and correct confirmed spill deterministically in the full-resolution base master. Use local
   foreground estimates to remove residual matte chroma, preserving alpha and uncontaminated interior RGB. Do not
   erode the silhouette, globally desaturate the creature, or recolor every magenta-looking pixel indiscriminately.
   Check the resulting chroma constraint numerically: reducing only blue may leave a magenta excess when red is the
   smaller channel. Choose the correction from the local foreground estimate and verify the resulting RGB.
4. Rebuild affected resizes, masks, crops, matching color/mask padding, atlases and variant previews. Keep native
   placement, alpha, timing and protected material colors intact. Recheck the final exported edges, including intended
   display size and variant previews, to catch contamination introduced by filtering or padding.

Keep this cheap: one all-frame scan and a compact visual review, followed by an affected-stage rerun when needed.
Color-only fringe repair does not need another AI generation. If local correction damages thin features or intended
colors, revise the local matte/foreground estimate; report any unresolved limitation rather than declaring success
from a lower score. Retain raw sheets and cleanup settings so the result is reproducible.

The m230 follow-up [edge audit](mm7_m230/review/edge_audit.json) and
[magnified comparisons](mm7_m230/review/edge_closeups.png) found small purple/pink remnants after the initial cleanup.
They were present before resizing and missed by the broad contact review. The subsequent
[corrective pass](mm7_m230/review/edge_correction.png) removes the shared red/blue excess and constrains additional
magenta created by resizing at base contours. The m230 [export audit](mm7_m230/edge_audit.py) now runs automatically
from its packager. Its 10/255 cleaned-base tolerance is calibrated for m230, not intended purple materials or recolored
variants. Successful extraction alone is not evidence that all visible spill has been removed.

Foreground color and alpha are not uniquely recoverable from a single flattened image. Painted colored reflections
may also resemble spill. Thin features without a trustworthy foreground core can lose opacity or acquire color bias.
Record such limits; lower measured magenta is not proof of a correct silhouette. A neutral background might reduce
colored spill but makes gray materials harder to separate. Independently AI-generated black/white versions are not
guaranteed pixel-aligned and cannot be assumed to form an exact pair for algebraic alpha recovery.

If the available generator can deliver actual alpha, preserve and inspect it instead of adding a key-color stage.
Check PNG bands and alpha values: a visible checkerboard proves nothing. Two goblin transparency requests returned
opaque RGB images with painted checkerboards; neither was a transparent asset. Tool/API capability and billing can
change, so verify the current interface and current official documentation before proposing another route. Do not
switch to a separately billed API to work around a missing parameter when the brief excludes extra API spending.

## 6. Resize, crop and package without reintroducing fringes

Preserve the approved original RGB and the cleaned full-resolution RGBA masters. Perform cleanup before final
downsampling. Filter **premultiplied color and alpha together**, then convert back to straight RGBA for PNG storage.
For Pillow, the worked path is `RGBA → RGBa → resize(LANCZOS) → RGBA`. Do not resize RGB against magenta and key it
afterward, or interpolate hidden key-colored RGB into visible contours.

Use identical cell sizes, scale and pivots throughout a sequence. Resize individual cells uniformly before packing,
or ensure atlas filtering cannot sample a neighboring frame. Record the final pivot and transparent bottom padding;
native bottom anchoring and `Center` flags must be inspected, not copied from another creature. Any additional
padding changes prospective runtime placement even if the art looks aligned in the sheet.

Deliver transparent PNG frames and an unlabeled usable sheet, separate from labeled contacts and GIF previews.
Record direction, pose order, timing, loop/hold behavior, dimensions, crop rectangles and generation/cleanup provenance.
Use manifests as the timing authority: GIF centisecond rounding must not silently redefine the animation.
If indexed BMP/native-style packaging is requested, use a shared palette with the audited transparent index, validate
the decoded mask and review the palette-reduced result at display size. A staged sheet does not install frame groups.

### Shared logical canvas, high-resolution tiers, and tight cropping

Use the [complete front goblin delivery](mm6_goblin/direct_front_final/README.md) as a worked example: all seven
actions, 31 poses, separate detailed generations, accepted edge cleanup, native-scale registration, aligned and
trimmed 1x/2x exports, an offline playback/placement viewer, and exact crop reconstruction checks.

The original `gob*.bmp` creature frames all use 355×289 canvases, although visible bounds vary greatly. The audited
`m242` and `m246` sets use 256×256. Do not assume all creatures share a universal image size. Inspect actual source
dimensions, image alpha/palette transparency, frame scale, actor scale, and `Center` flags before deciding placement.

Generate compact sheets per action with the same identity reference, then assemble the requested all-action sheet
deterministically. The earlier 31-pose single-call goblin sheet returned 1272×1237, making each figure smaller than
the original. Separate six-pose sheets returned about 1682×935 and roughly 380–410 pixels per upright figure.
Requested dimensions in a prompt are not guaranteed tool output dimensions. These historical delivery canvases
could include modest enlargement; that does not meet the current minimum of 2× actual generated sampling. For new
work, measure the shared crop and delivered grid, then split/repack and regenerate undersized batches as described
above. Record actual generated detail separately from packaging resolution; keep earlier accepted checkpoints
intact and label their measured limitations when comparing or selectively upgrading them.

Calibrate anatomical scale across actions against native landmarks, not each frame's overall bounding-box height.
Raised weapons, crouching, foot lifts, and corpse poses invalidate naive equal-height normalization. Use one uniform
scale within an action, record frame placement relative to source landmarks, and review transition poses. A prone
body must remain low and wide. If a longer restored weapon requires a minimal translation to stay in the logical
canvas, record and review that correction explicitly. Automated skin/head detection can mistake warm metal for skin;
inspect the marked landmarks before accepting registration.

Separate **logical canvas/pivot** from **physical stored rectangle**. Preserve cleaned unregistered art and an aligned
compatibility export. Then trim to the nonzero-alpha bounds with small filter padding and store canvas size,
pixels-per-logical-pixel, crop origin/size, pivot inside the crop, atlas rectangle if packed, and frame timing. Reconstruct
every aligned frame from its crop and assert exact pixel equality. Crop origins may be negative when padding extends
outside the logical canvas; pivots may lie outside a very small sprite rectangle. Do not clamp those offsets silently.

Current OpenYAMM sprite rendering uses image dimensions converted by the active asset scale tier, then applies frame
and actor scale. Goblin frames are bottom anchored. The audited billboard handles have no crop-origin/pivot fields,
and the draw paths do not read the generated crop manifests. Aligned 710×578 frames at a matching 2x tier retain
355×289 logical geometry. A cropped PNG alone does **not** preserve placement. Use aligned exports until shared
rendering/picking/outline/bounds paths consume the offset metadata consistently; re-padding at load time saves disk
space but not GPU allocation. Check current tier handling before using independently mixed category resolutions.

For crop `(cx,cy,cw,ch)` in physical pixels, tier `s`, and bottom-centered logical canvas `(W,H)`, local crop pixel
`(u,v)` maps to `x=(cx+u)/s-W/2`, `up=H-(cy+v)/s`. Apply existing world scale and camera basis. Mirroring must include
the logical offset. A `Center` sprite needs its own pivot rule. See the worked delivery for exact implementation
references; an atlas needs UV support and gutters as well as crop offsets.

Estimate GPU footprint from decoded format and allocated rectangle area, not compressed PNG/BMP file size.
The 31-frame goblin 2x example is 48.53 MiB aligned RGBA8 versus 18.23 MiB in individual padded tight crops, a 62.4%
reduction. Current billboard textures do not get mip chains in `TextureFiltering.cpp`; verify that before adding mip
overhead. Cropping can reduce upload/texture/transparent-fragment work, but does not reduce AI work or automatically
batch draw calls. Preserve true-color alpha for enhanced art; original indexed palette swaps do not automatically
recolor true-color PNG replacements.

## 7. Focused completion checks and handoff

- Every requested direction/action has the expected ordered poses, with source-backed versus inferred views identified.
- Figures/materials, poses, handedness and native-relative placement were visually reviewed in sequence contacts;
  use timed playback for unresolved motion questions and record the actual method, without overstating evidence.
- No unwanted clipping, neighboring-cell fragments, painted checkerboards, colored halos or lost thin details remain
  in the accepted result. Record any consciously accepted approximation.
- PNGs contain real varying alpha; clean foreground preservation and crop placement are checked where applicable.
- Scale, pivots, frame timing, sheet layout and any indexed-palette conversion are documented and verified.
- Retain source inventory, raw generation, selected prompts, shared cleanup settings, RGBA masters, usable frames/sheets
  and compact acceptance evidence. Do not create extra per-family scripts/reports/viewers by default.

Prioritize visual review and quick image/manifest checks. No Blender rig, engine build or exhaustive runtime scenario
suite is required for this direct restoration task unless the request also includes modeling or runtime integration.

Reuse the current project structure and ledger. New work needs selected provenance, runtime metadata, RGBA outputs
and one acceptance record; a separate README or duplicate report hierarchy is unnecessary.
Start from the [goblin project](mm6_goblin/direct_ai_attack/README.md) to inspect the complete example, then adapt its
assumptions to the actual MM6, MM7 or MM8 creature rather than copying its hardcoded crop geometry or color thresholds.

### Optional headless viewer capture

For local HTML review, invoke `./tools/capture_local_html.py` from the repository root using the saved approval for
that exact executable prefix. See [capture instructions](../../tools/CAPTURE_LOCAL_HTML.md) for paths, query options
and frame capture. Avoid new inline Chrome/shell-wrapper commands for every image; those require distinct approvals.
