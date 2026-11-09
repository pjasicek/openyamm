# Enhanced sprites: atlas and selective variants

> **MM6 is retired from this pipeline (2026-10-15).** MM6 monsters are 3D-only and ship no atlases; see
> [3D models replace 2D sprites](../MM6_2D_RETIREMENT.md). The MM6 source bank is archived, outside every
> build, in the git-ignored `assets_legacy/sprites_new_mm6_20261015/`. Do not cook or deploy MM6 families.

Start here for `mXXX*.bmp`, `gob*.bmp`, or another native creature family → enhanced sprites with native animation,
compact atlases, placement JSON, and selective color variants. Use [DIRECT_SPRITE_WORKFLOW.md](DIRECT_SPRITE_WORKFLOW.md)
only for the detailed prompt, matte, or alignment procedure needed at a particular step. No Blender/3D work is needed.

For installation into `assets_dev` or release packaging, follow
[Creature sprite deployment](SPRITE_RUNTIME_DEPLOYMENT.md). Author lossless source exports under
`assets_source/engine/sprites_new`; deploy only schema-2 GPU pages and referenced metadata/lookups into
`assets_dev/engine/sprites_new`. Each `engine.zip` includes one desktop or Android texture profile.

For suspected size changes between animation frames or generation-sheet rows, use
[Sprite scale diagnosis and correction](SPRITE_SCALE_DIAGNOSIS.md). It records the MM6 findings, native-relative
measurement method, Cleric trial, and rebuilding from high-resolution sources while retaining the 2× export tier.

For manual-style anatomical scaling/offsets and agent-prepared checkpoint JSON, follow
[Anatomical placement proposals](ANATOMICAL_PLACEMENT_WORKFLOW.md). It derives the action-aware procedure from
the reviewed MM6 bank and supplies one shared compiler for explicit landmarks without changing approved assets.

The user-selected generation recipe is
[Packed animation sheets with outline-only anatomy guides](PACKED_ANIMATION_OUTLINE_WORKFLOW.md):
one complete animation per stored view, a tight untouched native colour sheet, a matching separate outline-only
geometry sheet and selected detailed appearance art. Preserve fine texture and natural shading while following
native anatomy and steps. Read that guide for packing, reference authority, the corrected prompt and final Goblin
evidence. The historical Dragon internal-contrast experiment is a different technique, not this preferred recipe.

## Lean default workflow

Minimize image calls and agent context while still checking the actual artwork. This section is the default for
new work and resumes; historical examples below do not mandate their viewers, browser runs or reports.
Read the relevant detailed section only when needed. Reuse accepted checkpoints and shared tools.

1. **Prepare once.** Resolve native frames, palette, aliases, timing and placement from the existing inventory.
   Inspect the paletted originals and accepted identity, if any. Measure one padded union crop per action/view;
   never fit each pose separately. Prefer one complete animation per stored view, optimizing its grid and safe
   padding for the measured detail budget. Use `sheet_checks.py plan` below as a diagnostic; do not silently adopt
   its reduced pose count in complete-animation mode. Include padding/gutters in cell dimensions. Reuse an adequate identity;
   otherwise make the first useful restoration batch establish it, without an extra disposable identity request.
2. **Generate.** Use the untouched native grid as pose/layout authority, its matching outline-only sheet as geometry
   guidance and selected detailed art as identity/material authority. Keep outlines separate from interior shading.
   Begin the prompt with the source game/version and explicit existing fantasy-game asset upscale/restoration context.
   Request faithful fine texture, shading and contours, native palette/proportions/equipment, exactly the ordered poses,
   true transparent PNG alpha, no painted checkerboard, pixel blocks, dithering, blur or sharpening halos.
   Save the raw result and exact submitted prompt/references once. Aim for ≥2× native in both axes before export
   enlargement, preferably ≥2.2×. In complete-animation mode, the user's 2026-10-01 decision prioritizes one whole
   animation/view sheet in and out; below-2× results can pass visual acceptance with the actual sampling reported.
   Do not split cycles or regenerate solely for that shortfall. Explicit strict-minimum requests override this policy.
3. **Screen cheaply, then look.** Run `sheet_checks.py check` on each return. It checks actual dimensions, alpha,
   occupied cells and grid budget, and flags border/background or repeated-pixel concerns. A flag is diagnostic;
   a passing screen is **not acceptance**. Inspect every selected pose against native in compact contacts and
   inspect representative faces/materials at 100% plus all flagged patches. Confirm reconstructed detail,
   correct pose/equipment, complete silhouettes and real transparency on light/dark composites. No reliable
   universal Python blur/pixelation score proves artistic quality: smooth effects can score poorly, while noisy
   upscales can score well. Do not add repeated AI judging passes or extensive metric experiments.
4. **Stage checked batches.** Keep selected raw art and cleaned masters in the existing project. Register with
   one anatomical scale per coherent sequence; record the full raw-to-native transform and measure sampling again.
   Automatically preserve [exact native anchor placement](#exact-native-anchor-placement), including half pixels,
   before generating the final placement contacts; verify it again on exported frames before acceptance.
   Mark detected landmarks on native/restored art and independently check another body feature, as described in
   [independent placement review](DIRECT_SPRITE_WORKFLOW.md#independent-placement-review).
   Canvas dimensions alone cannot pass this gate. Fix demonstrated drift by translation; preserve native motion.
   Reuse clean supplied alpha. Repair only confirmed defects, rerunning only affected stages. Archive failed raw
   trials for resume, but do not count them as accepted coverage. A batch is partial work until the family gate.
5. **Assemble once.** When all required poses are ready, use the existing packer for 2× physical masters, base/mask atlases,
   native placement/animation metadata and deterministic palette variants. Check frame/alias coverage, exact crop
   and atlas reconstruction, matching masks, palette alpha/base bypass and residual edges. Review the assembled
   sequences in native order with a shared crop/pivot, plus compact mask/variant and worst-edge contacts. Inspect
   every pose without shrinking it beyond usefulness; split contacts when necessary. Generate a short timed
   preview only if motion remains uncertain or the user asks. Static contacts do not certify watched playback.
6. **Accept and inventory.** Record the selected artifact hashes, measured minimum sampling, complete coverage and
   the actual visual-review method in the existing acceptance record. Then refresh the existing ledger once.
   Only full coverage with both technical checks and visual acceptance counts as done. Report staged/installed
   separately. Installation and generation still require the user's task scope; changing this workflow starts neither.

An existing shared-template HTML viewer may be generated automatically by a local Python call: this uses no
model/API calls. Do not write or customize viewer code per creature. Browser traces, repeated viewer captures and
separate review documents are not completion requirements. Do not create a per-creature Python suite, README,
duplicate JSON reports, or per-frame prose. Retain the small amount of machine metadata needed for
reproducibility, placement, palette variants and truthful completion; a bare spritesheet cannot supply those.
Keep source/raw hashes, exact prompts, selected transforms, masters, runtime manifest and one acceptance record.
Use existing project formats instead of migrating accepted work. Review contacts are working evidence, not a
separate deliverable suite. Print summaries/failures rather than large manifests; load only affected project records.

Shared helpers, from repository root (Pillow/NumPy already used by the pipeline):

```sh
python3 level_generation/creatures/sheet_checks.py plan --poses 8 --cell 232 232
python3 level_generation/creatures/sheet_checks.py check /path/to/raw.png --cell 232 232 --grid 3 2 --poses 6
```

The planner's 1536×1024, 1024×1536 and 1254×1254 envelopes are **historical observations, not maximum dimensions
or guarantees**. Override with repeated `--envelope WIDTH HEIGHT` when current outputs justify another envelope.
The example fits six poses at about 2.21×. In the preferred complete-animation mode, preserve the whole cycle and
report delivered shortfalls accurately. Complete sheets below 2× can be accepted after normal visual and technical
review under the recorded user policy. Splitting with shared transition poses is an alternative only when the chosen
task scope permits it. A reduced planner pose count does not change the user's scope. Budget formula:
`min(delivered_width / (columns * native_cell_width), delivered_height / (rows * native_cell_height))`.
After uniform registration, actual sampling is `1 / raw_to_native_scale` (or `2 / raw_to_2x_scale`), including all
intermediate resizes. The check command accepts `--raw-to-native-scale` for this additional numeric gate.
It writes no files; the MM6 staging tool stores its compact result in the existing run ledger automatically.

For the existing MM6 redo, use `prepare_run.py`, `stage_result.py`, the applicable extraction/registration tools,
`export_run.py`, and `freeze_review.py` under `mm6_remaining/redo_2x/`. Export and freeze build the existing
shared-template viewer deterministically; `--skip-viewer` omits it. Neither invokes a model or browser.
[The redo workflow](mm6_remaining/redo_2x/WORKFLOW.md#lean-acceptance-record) defines the
small contact-review decision record accepted by the freezer. No browser or separate notes file is needed for it.
Then run `refresh_progress.py` and `inventory_remaining.py` once; the inventory no longer requires a viewer.

For a small interior defect, `extract_run.py` supports `processing.json` → `local_rgb_patches[frame]`.
Record the generated donor `source` and `source_sha256`, the pre-patch cleaned RGBA byte hash
`input_rgba_sha256`, integer `source_rect` and `target_rect` bounds, optional `feather_px`, and a review `reason`.
The donor must have at least as many pixels as the target in both axes; both regions must be near-opaque.
Only RGB inside the target rectangle changes. Original alpha, framing, and all surrounding pixels are retained.
Keep the donor's generation prompt/reference provenance, review the seam and detail at export size, regenerate
material masks, and bind acceptance to the donor and processing settings. This does not authorize automated repairs
or changing existing registration landmarks without checking that their underlying features are unchanged.

## Exact native anchor placement

This is an automatic preparation/export requirement for every restoration, before final placement review and
acceptance. An artwork screening pass may precede it; the accepted placement evidence and artifact hashes must
describe the corrected outputs. Do not shift frames after acceptance while retaining the old acceptance record.

- Derive placement from each native frame's actual dimensions and verified actor anchor, not its opaque bounds.
  Native frames need not share dimensions. In general, `offset = sharedPivot - nativePivot`, in logical pixels.
  For bottom-center anchoring, `offsetX = (sharedWidth - nativeWidth) / 2` and
  `offsetY = sharedHeight - nativeHeight`. Preserve fractional values; never floor or round this centering step.
  Use the verified runtime convention for other anchors; a `Center` flag alone does not establish actor behavior.
- Use the same exact coordinates for native references, registration, landmarks, aligned masters and review guides.
  At 2×, half a logical pixel is exactly one physical pixel: render reference canvases at 2× when needed instead of
  forcing fractional offsets through an integer-only 1× paste. Reference enlargement is not generated-detail sampling.
  Preserve native motion, timing and actor scale; this step must not normalize silhouettes or planted-foot heights.
- Preserve the mapping through cropping and packing. Base, masks and variants must share the transform; mirror
  placement around the actor pivot together with UVs. Automatically verify native-to-logical placement and the
  equivalent exported crop-origin/pivot mapping for every frame, including odd/even source dimensions and mirrored
  aliases. Require zero anchor-bookkeeping error; anatomical landmark uncertainty is a separate measurement.
  If the selected tool cannot represent the offset, fix its shared placement path before accepting the output.
- For an authorized repair of an existing package, calculate `exactOffset - recordedOffset` from its provenance.
  Apply that correction once in the authoritative registration/canvas placement and regenerate dependent outputs.
  A metadata-only translation is valid when all consumers use it consistently, including master and review placement;
  do not patch only a runtime manifest or apply the same correction again to pixels. Record the migration in existing
  project metadata, preserve the prior checkpoint, rerun affected placement/export checks, and renew acceptance hashes.
  Do not infer a correction from silhouette differences or migrate unrelated accepted packages automatically.

The MM6 [accepted anchor inventory](mm6_remaining/ground_anchor_review/accepted/INVENTORY.md) records the diagnosed
integer-centering fault. Its audit is diagnostic, not a universal exporter or automatic repair command. Updating this
workflow does not itself migrate those packages. Exact arithmetic does not certify anatomy or animation fidelity;
the independent placement review remains required.

The shared MM6 exporter now uses `exact_placement.py` and the redo acceptance tool validates its mapping. Saved
native animation bindings are also checked before acceptance: exported frame order, all eight view bindings,
mirror flags, native scale, per-frame duration and native no-image actions must match the saved source groups.
This includes the legacy Goblin action-level scale and the shared exporter's per-frame scale fields.
These checks validate metadata; they do not certify that a restored jaw, limb or effect core follows the native pose.

Historical registration/reference coordinates remain explicit as `registration_native_offset`; the exported canvas origin
adds `anchor_correction_px` exactly once. Masters retain their original pixels. Review current placement through
`mm6_remaining/repair_placement.py contacts`, which draws native BMPs at exact 2× coordinates against actual atlas
pixels. Historical reference sheets are provenance, not corrected placement evidence. The repair command's
`migrate` operation checkpoints and updates the inventoried packages only when that repair scope is authorized.

## Detailed reference and worked examples

The repository [Creature Restore skill](../../.agents/skills/creature-restore/SKILL.md) supplies defaults for
`$creature-restore m230*.bmp` or `CREATURE_RESTORE m230*.bmp`. Add natural-language scope overrides such as
`front attack only`, `resume existing work`, or `inspect and plan only; do not generate`.

**Status:** AI restoration, cleanup, alignment, cropping, manifests and previews have a
[worked goblin implementation](mm6_goblin/direct_front_final/README.md). Its
[darker grade](mm6_goblin/direct_front_final/toned_v1/README.md) was accepted by the driver.
Selective enhanced masks and staged variant atlases have a [worked m230 example](mm7_m230/README.md), including
a deterministic corrective pass for residual matte spill and an automatic export contour audit.
The [crusader runtime integration](mm7_m230/ENGINE_INTEGRATION.md) implements the first opt-in atlas/shader path.
The [pmn2 mage restoration](mm6_pmn2/README.md) adds a worked variable-canvas family with native pixel aliases and
a fitted luminance recolor, now supported by the [shared runtime shader](mm6_pmn2/ENGINE_INTEGRATION.md).
A general exporter and broader recolor operations remain proposed extensions.

The [complete MM6 goblin package](mm6_goblin/direct_complete/README.md) extends the accepted front art to all native
views with two selective mask regions. It preserves the blue variant's distinct walk timing and native corpse pixel
alias. Its two-region recolor now uses the shared RG8 loader/cache/shader path through the explicit
[New Sorpigal playtest exporter](mm6_peasants/PLAYTEST.md). Art generation alone still does not install assets.
Existing goblin and m230 scripts contain creature-specific assumptions; do not apply them blindly.

The [MM6 guard package](mm6_gua/README.md) is a worked four-mask restoration with a strongly foreshortened polearm
and three native material palettes. It uses its own inventory through the shared preparation/packing helpers.
Its four-channel operation is supported by the shared atlas renderer and installed in the isolated New Sorpigal
playtest. See its [runtime contract and installation](mm6_gua/ENGINE_INTEGRATION.md); mask alpha is material data,
not opacity.

## Generation recipe

| Step | Do once, then reuse | Output / quick check |
| --- | --- | --- |
| 1. Inventory | Resolve descriptors → frame groups → actual files and palettes, case-insensitively. Read dimensions, alpha index, directions/mirrors, timings, frame scale and anchor flags. | Source manifest with hashes. Exclude unrelated prefix matches. |
| 2. Variant reference | Render one useful native pose with every original palette; add another pose only if it reveals a hidden recolorable area. Identify independent color regions and protected details. | One variant contact; short region list and target colors. |
| 3. Enhance base | Follow the packed outline workflow: one complete animation per view, shared native union crop, compact grid, matching outline-only sheet and detailed appearance reference. Preserve whole-cycle scope and report resolution shortfalls; splitting is an alternative only when scope permits. | Raw sheet, prompt, actual dimensions, crop/registration transforms and measured generated sampling. Target ≥2 per native pixel; accept lower sampling under the recorded complete-animation policy after visual and technical review. Check all poses and fine detail. |
| 4. Clean and align | Preserve supplied real alpha; only estimate/unmix a matte for opaque outputs. Automatically audit every frame for residual spill; correct confirmed contamination before resizing or mask generation. Register to native logical coordinates; use anatomical scale, not equal bounding-box heights. Apply an accepted overall tone grade consistently. | Clean aligned masters; compact worst-edge crops on light/dark backgrounds. Keep held/prone poses correctly sized. |
| 5. Author masks | Mark only the enhanced pixels belonging to each recolorable region. Use the original palette changes as guidance; create masks on the enhanced artwork itself. | Soft coverage masks aligned exactly with the base; mask overlay review. See the rules below. |
| 6. Define variants | Choose a shadow/midtone/highlight color ramp per region and variant. Bake deterministic previews using the intended shader operation. | Same geometry, alpha and timing for all variants; no separate AI redraws. Review a variant contact and playback for leakage/flicker. |
| 7. Export | Choose a physical tier while preserving logical size. Resample color/alpha correctly; transform masks identically. Crop once from base alpha, then pack base and masks with exactly the same rectangles. | Atlas pages + JSON; retain aligned compatibility exports. Record actual generated detail separately from export dimensions. |
| 8. Check and hand off | Repeat the edge audit on final atlas-extracted frames; run the small checks below and inspect combined sequence/variant/edge contacts. Record selected versions and any remaining visible approximation. | Compact acceptance record, manifest, footprint totals, and a clear installed/staged status; viewer optional. |

Keep original pose counts, durations, native mirrors and requested scope. Missing views or extra in-between poses
are additional authoring work, not silently invented restoration. Runtime atlas pages can mix actions/directions;
generation grids are optimized for image quality, while runtime pages are optimized for allocation and loading.

Residual edge cleanup is a default agent-run stage, without a separate driver request. Follow
[the residual spill procedure](DIRECT_SPRITE_WORKFLOW.md#automatic-residual-spill-check) and include it in the
creature's deterministic processing/export scripts. A successful alpha extraction alone does not pass this check.
Reuse raw AI sheets; repair confirmed fringe RGB locally while preserving alpha, thin features, and intended colors.
Rebuild affected masks, padding, atlases and previews after correction. This is workflow guidance for the agent;
the m230 scripts now implement this for their green base, but are not a universal spill detector or repair command.

### Prefer genuine transparency; never painted checkerboards

Request a transparent PNG background with actual alpha, including empty grid cells. Explicitly forbid a painted
checkerboard, grid, shadow or halo. A viewer's checkerboard behind transparent pixels is harmless; checkerboard RGB
painted into visible pixels is a failed output. Inspect the PNG bands, background alpha and light/dark composites
to distinguish them. An alpha channel by itself is not sufficient if the background remains opaque.

When imagegen supplies genuine transparency, preserve its alpha and skip key-color extraction and matte unmixing.
Do not flatten it onto magenta or regenerate good artwork just to obtain a keyed sheet. Native input references
may still use a flat matte for readability; explicitly distinguish the reference matte from the requested output.
Use an opaque, subject-appropriate matte only when genuine transparency is unavailable. Record the actual returned
background mode with the raw output and processing settings. Retain accepted historical RGB/matte sheets on resume.

Real alpha avoids matte recovery, but does not waive checks for missing thin details, visible halos, stray pixels,
cell clipping, sampling, variants or anchoring. Leave clean pixels unchanged; repair only demonstrated defects.
See [transparency handling](DIRECT_SPRITE_WORKFLOW.md#5-extract-transparency-and-remove-contaminated-edge-colors).

### Crop and batch toward 2× generated detail

For the installed MM6 redo, start with the [insufficient-asset inventory](mm6_remaining/redo_2x/INVENTORY.md)
and [measured-detail replacement workflow](mm6_remaining/redo_2x/WORKFLOW.md). That inventory records the earlier
strict-detail audit: a historical 2× export or acceptance flag does not prove 2× generated detail. For current packed
complete-animation restorations, apply the user's 2026-10-01 complete-sheet policy instead of treating that historical
resolution classification as an automatic rejection.

The detail target is **2 actual generated pixels per native pixel in both axes**, before any enlargement for export.
One complete original animation at one stored view on one submitted and one returned sheet takes priority. Below-2×
results may pass the normal visual and technical review; record their measured sampling and physical export scale
separately. A strict minimum applies only when the user explicitly requests it for that run. Requesting a large raster
or exporting a 2× atlas does not establish generated detail, and no result below the target may be described as meeting it.

1. Decode the original palette/transparency and place every frame of one action/stored view in its native logical
   coordinates. Measure the **union of visible bounds across that entire sequence**, including weapon tips, tails,
   raised limbs and prone poses. Crop away only the common empty exterior. Add equal safety padding, initially
   about six native pixels, adjusted for the subject. Use that same crop origin/size for every pose and overlapping
   batch. Retain canvas size, pivot, crop offsets, timings and mirrors. Verify lossless foreground reconstruction;
   do not independently center or fit silhouettes. Native edge clipping remains a documented source limitation.
2. Enumerate compact layouts such as 3×2, 2×3, 3×3 and 4×2 using the **measured cell shape**, not a fixed pose count.
   For a native crop `w×h`, columns `c`, rows `r`, and an actually observed output envelope `W×H`, budget
   `min(W/(c*w), H/(r*h))` generated pixels per native pixel. Include all cell padding and any separate gutters
   in the denominator. At 2×, the largest native cell is `W/(2*c)` by `H/(2*r)`; prefer about 10% headroom
   (budget ≥2.2) for delivered-size/registration variation. Empty cells still consume the pixel budget.
3. The preferred packed-outline method keeps the complete sequence in one request. If its budget fails, first remove
   demonstrably empty shared margins, select a better-fitting aspect ratio or request a larger master. Preserve the
   complete cycle and report remaining shortfalls as measured resolution tradeoffs under the complete-animation
   policy. A shortfall alone does not prevent visual acceptance in that mode. When the user's chosen scope permits splitting,
   split the **sequence into consecutive groups
   of complete poses**, using one or more shared transition poses. Carry the accepted previous sheet as an identity
   reference while the new native grid remains pose authority. Inspect overlap and the assembled animation, select
   one version of each overlap, and retain native timing exactly. Do not split a character or sword into separately
   generated body-part tiles merely to fit a workload. Use fewer complete poses if one pose needs more space.
4. Treat tool dimensions as empirical, not a universal hardcoded maximum. Save the requested shape and actual
   returned width/height. If output dimensions, unequal grid placement or anatomical scale differ, recompute the
   sampling from the **actual raw cell and uniform native registration**. If `t` is the full scale from raw pixels
   to a native-sized canvas, sampling is `1/t`; if registering to 2×, it is `2/t`. Reject anisotropic stretching.
   Inspect body/face and weapon detail too: a large raster containing a small character can still fail. When the
   measured sampling is below two, report it accurately. Complete-animation mode accepts that pixel-budget tradeoff
   after visual review; a run with an explicitly strict minimum must repack/regenerate rather than interpolate into a pass.
   Adequate sampling can also fail visually when imagegen imitates enlarged pixel blocks, dithering or crunchy
   surface noise. Inspect at 100% before freezing identity. Request reconstructed fine shading and contours while
   retaining native design and tonal weight; do not substitute blur or sharpening. The MM8 Human Male Cleric
   identity V1 and V2 both returned 1335×1178, but only V2 resolved the blocky face/hair and coarse fabric rendering.
5. Save candidate dimensions, common crop, selected layout, overlap mapping, exact prompts/references, raw hashes,
   actual dimensions and registration/sampling in the resumable project. Keep generation-sheet packing separate
   from the final tightly packed runtime atlas. Check raw cell boundaries before extraction; a boundary may move
   through verified empty space with recorded offsets, but never cut off a tip or normalize poses independently.

#### Case: MM8 Dark Elf Warrior front attack

Measured [front-attack trial](mm8_m432/front_attack_grid_trial/README.md): eight 256×256
native frames share a sword-inclusive 232×232 crop. These returned dimensions are observations from this run,
**not guarantees for another tool/model call**:

| Layout | Native reference | Returned raster | Raw sampling before registration | Decision |
| --- | --- | --- | --- | --- |
| 3×3, eight poses + empty cell | 696×696 | 1254×1254 | 1.80× | Retain as layout reference; below minimum |
| 3×2, six poses | 696×464 | 1536×1024 | 2.21× | Detail budget fits; still requires pose/animation review |
| 4×2, eight poses | 928×464 | Not tested | 1.66× width **if** returned width were 1536 | Does not fit that observed width budget |

At the observed 1536×1024 landscape output, a 3×2 grid allows at most 256×256 native cells at exactly 2×,
or about 232×232 with 10% headroom. At the observed 1254×1254 square output, a 3×3 grid allows only
209×209 native cells at exactly 2×. A portrait layout needs its own observed output dimensions; do not assume
rotating the reference guarantees a corresponding service output. See the detailed
[preparation procedure](DIRECT_SPRITE_WORKFLOW.md#2-pack-the-original-frames-into-one-reference-sheet).

##### Deterministic correction of planted-foot drift

The compact sheets improved detail but moved characters within their cells. Correct shared anchor metadata did
not eliminate this: before correction, the restored ground line varied by 18 physical pixels at 2×. Native review
confirmed that **both feet stay planted at identical positions in all eight original poses**. This supports a
translation-only correction using native foot landmarks, without another image-generation request.

1. Preserve the previous exports and inspect corresponding native/restored feet. Keep the established common
   anatomical scale. For this case, use alpha ≥128 and the bottom 20 physical pixels to identify two separate
   occupied column runs. Take each run's midpoint as a foot center, their mean as the stance center, and the
   bottom opaque boundary as the ground landmark. These thresholds and the two-foot assumption are case-specific.
2. For each pose, calculate `dx = round(native stance center - restored stance center)` and
   `dy = native ground - restored ground`. Save measured landmarks, input hashes, integer shifts and the rounding
   rule. Translate the **whole frame**, with no resizing, rotation, warping, redrawing or independent body-part edits.
   Apply the identical shift to base pixels, masks and deterministic variants; rebuild matching atlas placement.
   Keep the native logical pivot, scale, timing and mirrors unchanged. Record that translations are already baked
   into exported pixels so a future runtime loader does not apply them twice.
3. Verify exact inverse-translation equality for base, mask and every variant; this proves that the translation
   itself did not change or clip pixels. It does not detect clipping in earlier normalization or affine transforms.
   Run those steps on a sufficiently padded temporary canvas, measure the native-contact translation there, and
   verify exact reconstruction after the final aligned crop. A falling Dragon Hunter pose exposed this failure:
   an early 576×576 affine canvas cut through the body even though the later inverse-translation check passed.
   Retaining 224 pixels of temporary padding on each side preserved the full pose without changing its logical
   size or anchor. Audit earlier processed poses when this defect is found; padding is working space, not a reason
   to shrink artwork or change native placement. Check atlas reconstruction and residual edges, then inspect native/before/after playback with fixed
   anchor and ground guides. Here, all eight ground errors became zero and stance-center error is at most
   0.5 physical pixel at 2× because shifts use whole pixels. Generated stance widths and anatomy still differ.

Reproduce this case with [foot_alignment.py](mm8_m432/front_attack_grid_trial/foot_alignment.py), the frozen
[landmarks and settings](mm8_m432/front_attack_grid_trial/foot_alignment.json), then the project's
`export_review.py` and `check_review.py`. The exporter checks selected-art hashes before reusing shifts.
See the [before/after viewer](mm8_m432/front_attack_grid_trial/viewer.html) and
[all-frame foot contact](mm8_m432/front_attack_grid_trial/review/feet_alignment.png).

This corrects demonstrated placement drift, not intentional motion. For walking, jumping, lifted feet or changing
contacts, use each original pose's actual landmarks; never force every pose onto one ground line or center by its
full silhouette. Ambiguous landmarks require visual verification. Head turns, limb shapes and sword foreshortening
are separate art defects; passing this placement check does not complete the animation or family.

### Mask and shading rules

- Choose **recolorable regions**, not necessarily whole materials: skin, garment panels, armor trim/plume, etc.
  Keep protected areas such as face, blade or highlights outside masks when the reference calls for that.
- Use a small number of soft mask channels; three independent coverage channels are a useful starting point.
  Their weights sum to at most one; the remaining weight keeps base color. Mask RGB denotes coverage, not visible
  paint. Base alpha remains separate and unchanged by recoloring. One-channel coverage is enough for a single region.
- A hue/color selection can propose masks quickly, aided by the native palette-region reference. Check the enhanced
  anatomy and locally repair errors. Copying enlarged native masks directly fails when AI changes silhouettes/poses.
  AI segmentation is optional assistance for a difficult sheet, not a mandatory second generation for every frame;
  its output must register to the existing pixels and must never replace the accepted base artwork.
- Inspect the masks as overlays on **all** frames in a contact/playback. Similar colors in skin, leather, gold and
  reflected light can cause leakage. Correct selected pixels offline; never run segmentation per monster at runtime.
- A variant changes each selected region through its own tonal ramp, retaining the base's fine shading information.
  Avoid flat replacement colors or a whole-creature multiplier. Protect bright metal highlights with mask coverage
  or a documented highlight-preservation rule. This is recoloring of baked lighting, not recovery of normals/relighting.
- Make the base variant an exact bypass. Share one explicitly specified color-space/ramp/mask operation between the
  preview baker and eventual shader. Decide shade normalization and highlight treatment once per region, then freeze
  them across frames; per-frame histogram matching causes animation flicker.
- Resample soft masks as **linear data**, with alpha-weighted coverage near silhouettes to avoid background dilution.
  Apply the exact same transforms/crops as the base, normalize overlapping weights, and handle padding consistently.
  Do not bilinearly interpolate integer material labels; use soft channels or a separately specified label-sampling path.

### Keep iteration short

Follow [multi-request scheduling](../sprites/PARALLEL_IMAGEGEN.md) for ready independent action/view sheets.
Establish the accepted identity reference first. Small batches reduce submission overhead, but the measured
ten-call trial largely queued results; do not assume proportional image-service speedup. Preserve per-job
checkpoints and normal visual acceptance, and fall back to serial submission on service limits.

One AI call per useful base direction/action sheet is the default, followed by targeted repair only for visible faults.
Reuse the accepted identity reference; do not regenerate three appearances of the same poses. Raw sheets, source
hashes, tone settings and mask/ramp settings are checkpoints: rerun only the affected stage. After a repeated failure,
change the batch layout, reference or extraction method instead of repeating the same request indefinitely.

The default review is **compact sequence contacts, light/dark edges, and mask/variant overlays**. Timed previews
are for unresolved motion questions or explicit requests. Shared-template HTML export is cheap and may run by
default; browser traces are optional. No separate
report per frame, repeated broad audits, Blender setup, engine build, or gameplay scenario suite for each asset batch.
Proceed autonomously through routine reversible steps; this checklist is not a series of driver approval gates.
Do not ship clipped art or misplaced masks to meet a time target. Record the specific remaining fault if it cannot be
resolved. Tool latency and difficult mask authoring prevent a guaranteed wall-clock limit; avoid unnecessary work,
especially making mask generation another unexamined full AI pass per animation.

### Lossless source export contract (schema 1)

Keep one source/audit manifest for provenance and one compact runtime-facing manifest. The latter needs:

| Record | Fields |
| --- | --- |
| Package | Schema version, namespaced creature ID, physical pixels per logical pixel, logical canvas/pivot convention |
| Pages | Base image, corresponding mask image(s), dimensions, formats/color spaces, padding/filter policy |
| Frames | Stable frame ID, page index, physical atlas rectangle, physical crop origin within the aligned canvas; per-frame canvas/pivot overrides if needed |
| Animations | Direction/action → ordered frame IDs, durations, hold/loop semantics, native group mapping and explicit mirror aliases |
| Regions | Channel/coverage meaning, shading/ramp parameters, protected-highlight rule |
| Variants | Stable variant ID → per-region ramps/parameters; default variant bypass |

Example frame fragment; coordinates are illustrative, top-left origin, not a currently supported engine schema:

```json
{
  "schema_version": 1,
  "creature": "mm6:goblin",
  "pixels_per_logical_pixel": 2,
  "logical_canvas": [355, 289],
  "logical_pivot": [177.5, 289],
  "frames": {
    "front.attack.a": {
      "page": 0,
      "atlas_xywh": [4, 4, 240, 500],
      "crop_origin_px": [240, 82]
    }
  }
}
```

At tier `s`, cropped pixel `(u,v)` maps to local logical position
`x=(cropX+u)/s-pivotX`, `up=pivotY-(cropY+v)/s`. Apply the existing frame/actor scale and camera basis afterward.
Allow negative crop origins and pivots outside the crop. Mirror placement around the logical pivot along with UVs.
Base and mask atlas rectangles must match; no independent mask packing. Choose page sizes supported by target
hardware, avoiding power-of-two padding unless required. Do not use the sparse all-action review grid as the runtime atlas.

### Small completion gate

1. Expected poses/directions/timing and source hashes match; no omitted cells or clipped accepted silhouettes.
2. Crops reconstruct aligned RGBA exactly; atlas extraction matches frame exports; base/mask coordinates and sizes match.
3. Mask values/weight sums are valid; variant alpha equals base alpha; default variant reproduces base RGB exactly.
4. The all-frame edge audit and magnified worst-case light/dark crops show no confirmed visible matte fringe after
   final export. Sequence contacts also show consistent native-relative placement, coherent shading, and correctly
   selected regions; inspect timed motion when contacts leave uncertainty. Record the method actually used.
   A chroma score alone cannot establish clean edges; record any unresolved fault explicitly.
5. Report decoded base **plus mask plus packing** memory per resident page/set. Do not multiply shared art by actor count.

Worked scale: the current 31-frame goblin front set is 12.13 MiB for original full RGBA canvases, 18.23 MiB for enhanced
2x individual tight crops, or 21.28 MiB for its packed 2x base atlas. **These last two exclude future masks.** Actual mask
formats affect overhead. Sixty goblins share textures; additional resident pages/variants, not actor count alone,
determine texture allocation. No FPS claim follows from these allocation calculations.

## Future engine deltas — not required during generation

**Implemented first integration (2026-09-08):** [MM7 crusader runtime](mm7_m230/ENGINE_INTEGRATION.md)
provides opt-in `atlas:crusader/<frame>` references, shared base/R8-mask pages, cropped actor placement/picking,
selective color presets, and native animation groups in both renderers. Use its smaller runtime manifest as the
historical v1 source contract. The deployed format is now schema 2; see the deployment guide.
The remaining proposals below are optional extensions; ordinary creature generation
still does not require rebuilding or testing the engine. Actor placement follows the current renderer’s native
bottom-anchor convention; do not introduce a second pivot subtraction because the original table has `Center`.

Implement incrementally in shared asset/rendering code, retaining the existing native sprite path:

| Delta | Required behavior and likely touch points |
| --- | --- |
| 1. Asset contract/resolution | Add a validated, versioned atlas manifest loader under `engine/`; resolve optional enhanced packages through normal mounted world/mod assets. Resolve existing sprite names/groups to frame records. Missing optional enhancement can select native art; a selected malformed package must report its error. Do not silently conceal broken metadata. |
| 2. Shared page ownership | Cache enhanced base/mask pages by package/page/resolution, not by monster instance or color preset. Today palette decoding creates full-color textures per palette ID. Preserve that native behavior while giving enhanced variants shared pages. Scope warmup to needed creature sets and bound resident pages. |
| 3. Shared frame geometry | Add logical canvas/pivot, crop offset, atlas UVs and physical tier to a shared sprite-frame resource/helper. Both indoor/outdoor billboards must use the same coordinate conversion, mirror handling and frame/actor scale. Audit mixed per-category tiers; do not divide by both manifest scale and global tier. |
| 4. Picking and presentation | Apply that transform to opacity picking, hover outlines, visibility bounds and sprite-derived health-bar placement. Preserve appropriate logical bounds for UI while sampling only the cropped frame. Keep gameplay collision/reach/stat definitions independent of crop dimensions. |
| 5. Selective-variant shader | Bind shared base/masks and small ramp/preset data. Pass variant selection per actor/vertex or instance; do not allocate a new full-color texture per preset. Decode color in the chosen space, read masks as linear data, preserve alpha and protected highlights, then apply existing scene lighting/fog/effects. Base variant is exact bypass. |
| 6. Atlas filtering/batching | Constrain sampling and outlines to each frame rectangle with appropriate gutters/edge-color bleed. Prevent mask or neighboring-frame contamination. Preserve transparent sorting/depth behavior; shared pages enable batching but do not justify arbitrary reordering. The offline cooker builds matching base/mask mip levels 0–4 before GPU compression, with 16-pixel aligned cells/gutters and alpha-weighted reduction. Shader LOD is capped at 4 to prevent cross-frame contamination. Native billboards retain their existing policy. See [runtime mipmaps](SPRITE_ATLAS_MIPMAPS.md). |
| 7. Animation/content wiring | Keep native timing, direction selection, mirrored handedness, `Center`, scale, hit/death/corpse behavior and table IDs. Use an explicit enhanced variant mapping; legacy palette IDs do not recolor PNGs. Avoid a second independent animation state machine or duplicate authoritative timing tables. New authored timing must enter the existing shared animation path deliberately. |

Relevant current implementation: [image decoding](../../engine/ImageAssetLoader.cpp),
[asset scaling](../../engine/AssetScaleTier.cpp), [outdoor billboards](../../game/outdoor/OutdoorBillboardRenderer.cpp),
[indoor renderer](../../game/indoor/IndoorRenderer.cpp), [opacity masks](../../game/render/BillboardOpacityMask.h),
and [texture filtering](../../game/render/TextureFiltering.cpp). These are inspection points, not permission to
duplicate indoor/outdoor gameplay logic or copy another engine's implementation.

Engine-only validation: focused unit coverage for crop/pivot/mirror/tier and manifest validation; compare a small GPU
variant render against the offline reference; one representative indoor/outdoor visual check covering picking,
outlines and scene lighting; a representative 60-actor crowd capture for frame time, page count and texture memory.
Include native indexed sprites/palettes in regression checks. Run these when implementing/changing renderer behavior,
not for every generated creature or every synthetic event. Frame-rate performance must be measured on target hardware.

## Calibration references

The [original palette comparison](palette_reference_audit/comparison.png) applies native palettes to identical pixels:
MM6 `gobsta0` with 745/746/747, and MM8 `m456Sa0` with 457/458/459 (Dragon Hunter/Crusader/Dragonslayer).
The dragon hunter standing frame changes about 39% of opaque pixels; cloth/plume and colored armor areas vary while
the face and much bright silver remain consistent. Goblin skin changes green/blue/red and other materials also shift.
Exact RGB difference marks almost all goblin pixels because palettes also contain subtle changes; a binary palette
difference image is **not** automatically a semantic mask. See [audit data](palette_reference_audit/audit.json).
This supports independently selected regions and shade ramps, rather than a whole-image tint.

## Local viewer captures

Use [tools/capture_local_html.py](../../tools/capture_local_html.py) directly from the repository root; see
[its instructions](../../tools/CAPTURE_LOCAL_HTML.md). The driver approved this executable prefix for reusable
headless Chrome captures. Change arguments on that command instead of assembling inline Chrome commands or shell
wrappers, which can trigger repeated approval prompts. This is an optional visual check, not an engine test suite.
