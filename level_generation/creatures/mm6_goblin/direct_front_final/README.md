# MM6 goblin: complete restored front animations

The [complete native-view restoration](../direct_complete/README.md) now reuses this accepted front set and adds
the missing standing/walking directions, selective palette masks, compact atlases and per-variant native timing.
Use that package for the full creature; this directory remains the original front-art checkpoint.

31 front poses across all seven native actions. Generated with the built-in imagegen tool, using native frames as
pose references and the accepted direct attack restoration as the shared character/material reference. No paid API
fallback, 3D rendering, runtime installation, or gameplay-table changes were used for this delivery.

Open [review.html](review.html) in a browser for offline playback, original/restored comparison, light/dark
backgrounds, frame stepping, zoom, and an aligned/compact-crop placement toggle.

A separate [darker color trial](toned_v1/README.md) responds to the `1257.png` brightness feedback. Its
[three-column comparison](toned_v1/comparison.png) shows native art, the restored master, and the deterministic grade.
The trial covers all 31 frames with identical alpha/placement; it does not replace this master delivery.

## Delivered art

- [Full transparent sheet, 2x](front_all_actions_2x.png): 4260 × 4046; six columns, seven action rows.
- [Full transparent sheet, 1x](front_all_actions_1x.png): 2130 × 2023; same layout.
- [Labeled dark contact](previews/all_actions_dark.png) and [light contact](previews/all_actions_light.png).
- `aligned_2x/`: 31 RGBA PNG frames, each **710 × 578**, retaining the native logical canvas.
- `aligned_1x/`: 31 RGBA PNG frames, each **355 × 289**, for original-resolution geometry/low memory use.
- `trimmed_2x/`, `trimmed_1x/`: minimal nonzero-alpha rectangles plus two logical pixels of transparent filter padding.
- [Compact 2x atlas](packed_front_2x.png) and [compact 1x atlas](packed_front_1x.png): rectangles in
  [manifest.json](manifest.json). These require an atlas/offset-aware consumer.
- `action_sheets_2x/`: one transparent horizontal strip per action.
- `previews/`: APNG and GIF playback, native comparisons, and all-frame comparison contacts.
- `raw/`, `cleaned_source/`, `references/`, `prompts/`: original generated outputs, unregistered clean art,
  native input grids, and exact generation/edit prompts.

The full seven-row sheet is for interchange/review, not an efficient runtime atlas; its empty cells deliberately
preserve the requested row layout. Do not upload that whole sheet as a single monster frame.

| Row | Action | Native front frames | Timing |
| --- | --- | --- | --- |
| 1 | Attack | `gobata0`–`gobatf0` (6) | 125 ms each; 750 ms |
| 2 | Death | `gobdya0`–`gobdye0` (5) | 125 ms each; 625 ms, then corpse |
| 3 | Walk | `gobwaa0`–`gobwaf0` (6) | 125 ms each; 750 ms loop |
| 4 | Hit | `gobwia0`–`gobwif0` (6) | 125 ms each; 750 ms |
| 5 | Fidget | `gobfia0`–`gobfif0` (6) | 125 ms each; 750 ms |
| 6 | Standing | `gobsta0` (1) | Held |
| 7 | Corpse | `gobdyf0` (1) | Held |

APNG preserves 125 ms intervals. GIF previews alternate 120/130 ms because GIF uses centiseconds; the five-frame death
preview is 620 ms. Manifests retain native timing. All preview clips repeat for inspection, including death/hit/attack;
that does not redefine their runtime looping behavior. Native standing/walk have other directions; this delivery
contains **front only**, not fabricated back/side views.

## What was corrected and how the scale was calibrated

1. Reused the accepted six-frame attack art and its accepted cleanup. Generated walk, hit, fidget, and death+corpse
   as separate 3×2 sheets, plus one standing image. This preserves substantially more detail per figure than asking
   for all 31 poses in one generation. The final seven-row sheet is assembled deterministically afterward.
2. Corrected walk frame `gobwad0`: the first result lifted the wrong foot. The targeted AI edit lifts the screen-right
   foot and plants the screen-left foot, following the original. The larger edit output is normalized before alignment.
3. Applied the accepted local chroma-matte estimation and edge-RGB unmixing from
   [clean_edges.py](../direct_ai_attack/clean_edges.py). The raw images already have blended magenta contour pixels;
   replacing only exact magenta or setting alpha without cleaning RGB would retain a fringe.
4. Recorded native and generated head/ground landmarks in [landmarks.json](landmarks.json). An olive-color detector
   supplies initial estimates; three generated head landmarks were manually corrected where warm sword highlights
   fooled the detector. [Landmark contact](landmark_review.png) preserves the audit.
5. Used one uniform anatomical scale per action, with source-based horizontal head placement and each native frame's
   actual bottom silhouette position. This avoids recentering every pose or fitting every sprite to the same height.
   Prone death/corpse poses share a width-based calibration against the original prone bodies. Their low height is
   retained. The attack scale is slightly limited by the raised sword fitting the native canvas. Attack frame `e`
   receives a recorded **12 logical pixel rightward translation** to preserve its extended sword without clipping.
6. Resampled cleaned RGBA in premultiplied color space, then exported straight RGBA PNG. The logical canvas remains
   355×289, with bottom-center pivot **(177.5, 289)**. All transformations are recorded in `manifest.json`.
7. Trimmed only after registration, adding two logical pixels of filter padding, and recorded the removed rectangle
   and pivot. Every crop reconstructs its aligned frame **pixel-for-pixel**, including negative crop origins/padding
   beyond the logical canvas. Atlas extraction is also verified pixel-for-pixel.

The 3×2 raw sheets are about 1682×935, not the requested 3456×1920. Typical upright figures contain roughly 380–410
generated pixels in height. Thus **2x is the delivery/placement tier, not a claim of native 2x generated detail**;
most six-frame artwork is mildly enlarged into that tier. The single standing/edit outputs are larger. Unresampled
cleaned outputs and raw generations remain available. The restoration infers detail and changes some anatomy,
equipment perspective, and material highlights; it is not a pixel-exact reconstruction of a missing original model.

## Current OpenYAMM behavior: why cropping needs metadata

Audited the current local implementation, not assumptions from another engine:

- [Outdoor sprite loading/rendering](../../../../game/outdoor/OutdoorBillboardRenderer.cpp) converts physical image
  dimensions to logical dimensions using the active asset scale tier, then calculates world width/height from those
  logical dimensions × sprite frame scale × actor height scale. The actor quad is bottom anchored.
- [Indoor sprite loading/rendering](../../../../game/indoor/IndoorRenderer.cpp) also distinguishes physical/logical
  dimensions. Its frame-aware positioning helper respects `Center`; the goblin's native rows do not use that flag.
- [AssetScaleTier](../../../../engine/AssetScaleTier.cpp) supports 1x/2x/4x; directory suffixes are `_x2`/`_x4`.
  710×578 at the matching 2x tier becomes 355×289 logically. Putting a 2x image into a 1x setup would double world size.
  Renderer calls currently use the global tier in these paths; independently mixed category tiers need an integration
  audit before assuming they behave identically. This art task does not change tier configuration.
- The current indoor/outdoor `BillboardTextureHandle` contains physical/logical sizes and opacity masks, but no trim
  origin or pivot. The existing full-quad rendering paths do not consume this delivery's manifest or packed atlas.
- [ImageAssetLoader](../../../../engine/ImageAssetLoader.cpp) supports PNG alpha and searches PNG before BMP/PCX for
  a sprite stem. True-color PNG bypasses the indexed BMP palette substitution. Original goblin palette variants
  therefore need separately authored variants or an intentional recoloring mechanism before replacing all tiers.

**Use aligned frames for compatibility today.** Their canvas and tier preserve the expected size/anchor calculations;
that is a geometry guarantee, not a claim these staged files are installed or play-tested. Keep native monster IDs,
frame groups, timing, actor height scale, and frame scale unchanged for an eventual same-size replacement.

**Use trimmed frames with their offsets for the efficient final renderer.** Do not merely copy a cropped PNG over
the native bitmap: it would center horizontally and bottom-anchor using the smaller rectangle, shifting the body
and changing the quad size. Re-padding during loading restores appearance, but also restores the GPU allocation.

For a logical canvas `(W,H)`, tier `s`, physical crop `(cx,cy,cw,ch)`, and source top-left image coordinates:

```text
pivot_in_crop = (s*W/2 - cx, s*H - cy)
local_x(u) = (cx + u)/s - W/2
local_up(v) = H - (cy + v)/s
```

Multiply these local coordinates by the existing sprite/actor scale and apply the camera-right/camera-up basis
around the actor position. `u,v` are coordinates within the trimmed image. Mirroring must mirror the complete logical
placement, including offsets, not just swap UVs. An implementation must use the same transform for drawing, hover
outlines, opacity picking, and bounds/health bars. Center-anchored sprites require a different logical pivot. A packed
atlas additionally needs its rectangle UVs and filter gutters. No such engine feature is implemented by this delivery.

## Measured footprint

For these **31 frames**, uncompressed RGBA8 base-level texture storage, excluding allocator/driver overhead:

| Packaging | 1x | 2x |
| --- | ---: | ---: |
| Aligned individual frames | 12.13 MiB | 48.53 MiB |
| Individually cropped, including filter padding | 4.63 MiB | 18.23 MiB |
| Packed atlas, including unused packing space | 5.38 MiB | 21.28 MiB |

Individual crops save **61.8% / 62.4%** at 1x/2x. Atlas sizes are 969×1455 and 1528×3651. The full seven-row review
sheet is larger still and should not be the runtime allocation. Source indexed BMP files are decoded into four-byte
pixels for upload, so their indexed on-disk size does not equal GPU usage. Transparent PNG margins compress well on
disk but still occupy decoded texture memory. [TextureFiltering](../../../../game/render/TextureFiltering.cpp)
currently generates mipmaps for terrain/bmodels/sky, **not billboards**; the table does not add an imaginary mip chain.

Cropping can reduce texture upload/decode work, alpha-mask area, bandwidth, and transparent fragment work. It does
not reduce monster AI work, actor count, or automatically reduce draw calls. An atlas can enable batching, but the
renderer has to support that. The figures above are allocation calculations, not measured FPS claims.

Recommendation: keep the 2x aligned/cleaned masters; use 1x aligned frames for an inexpensive current-engine trial.
For a future enhanced runtime package, consume the 2x trimmed frames/atlas and metadata directly. Choose additional
resolution only when actual display distance warrants it, rather than preserving arbitrary large empty canvases.

## Rebuild and checks

From the repository root, with Pillow, NumPy and SciPy available:

```bash
python3 level_generation/creatures/mm6_goblin/direct_front_final/prepare_clean.py
python3 level_generation/creatures/mm6_goblin/direct_front_final/registration.py
python3 level_generation/creatures/mm6_goblin/direct_front_final/package.py
python3 level_generation/creatures/mm6_goblin/direct_front_final/build_review.py
```

These commands rebuild from saved raw AI outputs; they do not rerun image generation. All 31 native input hashes
are checked. Source extraction and final registration reject clipped silhouettes; each cropped frame and packed
atlas rectangle must reconstruct exactly. Visual review covered full action contacts, original/restored size
comparisons, the corrected gait, collapsed silhouettes, and light/dark backgrounds. Timing is verified from APNG
metadata. These focused asset checks do not require an engine build or scenario runs.

The matte is estimated, not recovered ground-truth alpha. Thin features without clean foreground samples can lose
some opacity; minor material/edge color bias remains possible. The preview is the appropriate place to assess the
restoration's appearance before integrating it. No unused back/side art or indexed palette variants are implied.
