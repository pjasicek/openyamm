# Dark Elf Warrior front attack: common-crop grid trial

This is the active approach experiment requested by the user. It covers **eight front attack poses only**,
`m432aa0` through `m432ah0`. The family remains partial; earlier parent and `detail_upgrade/` checkpoints are retained.
Open [the offline comparison](viewer.html) for native, restored before alignment and corrected restored art at identical
logical placement, native 125 ms frame durations and once/hold playback. Review repetition is explicitly optional.

## Deterministic foot correction

The current viewer includes the user's requested placement fix. All eight originals have the same two planted
feet. `foot_alignment.json` freezes their measured landmarks, source hashes and per-frame integer XY translations.
The entire restored frame moves as one unit, with the same shift applied to masks, palettes and atlas pixels.
There is no redraw, resampling, per-frame scale change or timing change. Ground error is now zero; stance-center
error is at most 0.5 physical pixel at 2×. Generated differences in foot width, leg shape, head turn and weapons remain.

`before_alignment/` preserves the previous exports, viewer and review checkpoint. Cyan viewer guides show the
fixed native bottom-center anchor [288,544] in the padded 576×576 canvas. `review/feet_alignment.png` compares
all native, before and after feet. `review/foot_alignment_checks.json` verifies exact pixel translations for base,
mask and all three variants, including no clipping; the browser check decodes all 56 comparison images and checks timing.

To reproduce, reuse `foot_alignment.json` and run `export_review.py`, then `check_review.py` with the commands below.
The exporter validates the selected-master hash before applying saved shifts, so changed artwork requires a new
landmark audit. `foot_alignment.py` prepares the initial preserved checkpoint and settings; it reuses them if present.
Translations are already baked into exported images; metadata records them for audit, not an additional runtime shift.

## Measured result

All originals are 256×256, pivot [128,256]. Their sequence-wide foreground union, plus six native pixels on each
side, gives common crop **[28,30,260,262] = 232×232**. This removes shared empty exterior without moving individual
poses or cutting off the sword. Padding beyond the original canvas preserves, but cannot repair, native clipping.
`source_layout.json` preserves hashes, exact source records and native animation steps.

| Request | Native grid | Delivered raw | Sampling before registration |
| --- | --- | --- | --- |
| 3×3, all eight poses plus empty cell | 696×696 | 1254×1254 | 1.80×; retained below-minimum layout trial |
| 3×2 start, aa0–af0 | 696×464 | 1536×1024 | 2.21× |
| 3×2 end, ac0–ah0 | 696×464 | 1536×1024 | 2.21× |

The two landscape sheets overlap in four poses. The review selection keeps aa0–af0 from start, ag0/ah0 from end;
there are exactly eight unique runtime poses. Native grids control poses; enhanced references control identity.
Both sheets share one isotropic registration scale, with one translation per row of three poses. The fitted scale
is approximately 0.90146 after initial raw-to-2× normalization, giving 2.448 generated pixels per native pixel.
This numerical detail pass does **not** establish correct anatomy or placement.

Raw row spacing drifted. Extraction cuts were moved through inspected empty space to retain start-row sole
antialiasing, the end af0 blade tip and end ah0 raised tip. Their offsets are preserved in `registration.json`;
no individual silhouette fitting, stretching or recentering is used. Tone uses native coarse color with generated
fine detail, preserving generated alpha. Unmodified raw and ungraded registered masters remain available.

## Acceptance and remaining corrections

**Partial visual trial, not accepted production artwork.** It demonstrates improved detail at the same output size,
but the contacts show remaining head-angle differences, stance-width/anatomy differences and blade foreshortening changes
(especially ae0). The overlap contact also shows that matching style does not guarantee matching pose geometry.
These defects must be repaired and the assembled animation reviewed before accepting the sequence.

All eight base frames passed the native-aware residual matte metric; atlas and mask reconstruction, alpha preservation
and palette-433 exact bypass are asserted by `export_review.py`. Three deterministic palette previews and enhanced-art
mask overlays are retained for review. Variant edge scores currently use **base-palette allowances**, so they are
diagnostic candidates, not a variant acceptance gate; inspect with each native variant's intended colors before final
acceptance. Recheck protected hand/hilt pixels in ac0 after geometry repair. No family completion gate is advanced.

The 1728×1728 review atlas and matching R8 mask use aligned cells and consume 14,929,920 decoded bytes together.
Tight production packing is deliberately deferred until pose acceptance. `manifest.json` preserves the 256×256
logical canvas, pivot, 2× tier, padded canvas origin, exact timing, palettes and explicit partial status.

## Resume

1. Review `review/start_registration.png`, `end_registration.png`, `overlap.png` and `viewer.html`.
2. Review the deterministic foot fix first. Repair remaining pose differences using the same native common-crop sequence grids and enhanced identity.
   Keep the 3×2 coherent batches and overlaps; do not resume unrelated single-frame refinement automatically.
   Save a new raw/prompt version, source/reference hashes and selection in `sequence_jobs.json`.
3. Run `python3 level_generation/creatures/mm8_m432/front_attack_grid_trial/process_trial.py`, then
   `python3 level_generation/creatures/mm8_m432/front_attack_grid_trial/export_review.py`.
   The former honors `selected_raw`; update the job prompt path when selecting a repair. Inspect and explicitly
   freeze shared calibration only when anatomical scale/ground placement pass. Minimum sampling must remain ≥2.
4. Run `python3 level_generation/creatures/mm8_m432/front_attack_grid_trial/check_review.py`, inspect playback,
   native comparisons, variants/masks and `review/edges_light_dark.png`. Correct defects before acceptance.
5. Once this sequence passes, apply the measured crop/layout policy to the remaining action/view sequences while
   reusing valid earlier checkpoints. Keep m432 partial until all 160 unique native frames and family gates pass.

`prepare.py` documents the original native crop and first request; do not rerun it over reviewed metadata.
`processing_settings.json` and the two processing scripts preserve the deterministic extraction, registration,
tone and recoloring recipe. Their parent imports are required. All files are staged; nothing is installed in gameplay.
