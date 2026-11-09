# MM7 Behemoth — direct sprite restoration

Open [review.html](review.html) directly in a browser for native/restored playback, directions, palettes,
mask overlays and crop bounds. This is a staged asset package; it does not replace native sprites or add actors
to gameplay. Follow the shared [atlas pipeline](../SPRITE_ATLAS_VARIANTS_PIPELINE.md) and
[direct workflow](../DIRECT_SPRITE_WORKFLOW.md) for future work.

## Source and coverage

Sources are `assets_dev/worlds/mm7/sprites/m162*.bmp`, not the embedded BMP palette as displayed by an image viewer.
All 120 files are unique, indexed 256×256 images with transparent index 0. Native frame groups `m163`, `m164`,
and `m165` share these images and select MM7 palettes 163, 164 and 165 respectively. The monster descriptors are
208 Young Behemoth, 209 Behemoth and 210 Ancient Behemoth. Green palette 163 is the restored base;
purple 164 and red 165 are deterministic recolors. Source paths, hashes, palettes and original frame groups are
retained in [sources.json](sources.json).

| Action | Native sequence per stored view | Stored artwork |
| --- | --- | --- |
| Standing | One frame | Five views |
| Attack | Eight frames, 125 ms each | Five views |
| Walk | Eight frames, 125 ms each | Five views |
| Hit | `a,b,a,b,c,d`; 125,125,125,187.5,187.5,187.5 ms | Five views; unused `e` also restored |
| Fidget | Five frames, 125 ms each | Front reused in all directions |
| Death | `na0,nb0,da0,db0,dc0,dd0`, 125 ms each | Front reused in all directions |
| Corpse | `xa0` held | Front reused in all directions |

115 source filenames are referenced by native playback. Five `m162ne*.bmp` images are exported but remain unused.
Views 0–4 are stored; 5, 6 and 7 mirror 3, 2 and 1. Single-view actions retain native reuse without mirroring.
No extra inbetweens, camera angles or alternate AI-generated palette bodies were added.

## Generation and cleanup

The initial 18 built-in image-generation calls produced a five-view standing identity sheet, five attack sheets,
five walking sheets, five hit sheets, one fidget sheet and one death/corpse sheet. Native grids control the poses;
the accepted standing restoration controls identity and materials for subsequent batches. Exact submitted prompts,
reference hashes, selected raw outputs and actual dimensions are in [generation.json](generation.json).
Keep these checkpoints when iterating: color and matte fixes do not require another AI pass.

The restore preserves the hunched heavy body, long arms, gray/beige hide, dark recessed torso, green mane/beard,
and long ivory claws with rust-red tips. Raw sheets use uniform magenta. `process.py` finds empty gutters near
nominal cell divisions, because some generated claws/feet cross the nominal grid line while staying inside the
actual empty gutter. It extracts and unmixes the matte, corrects residual contour RGB, applies one fixed tonal
curve (`RGB *= encoded_luminance ** 0.10`), then resizes in premultiplied alpha. Alpha is preserved by the tonal
and contour corrections. The green base has no intended purple material; this cleanup must not be applied to
purple variant previews.

Sampling repair replaced the four undersized attack_1, attack_2, walk_2 and walk_4 sheets with nine compact
overlapping sheets. All 32 affected native frames now use the replacements; 88 previously reviewed frames
retain identical registration and deterministic processing. Twenty-three sheets are selected from 27 preserved
raw outputs. All 120 frames measure at least 2.0 generated pixels per native pixel before 2× runtime export.
Each action/direction
batch uses a shared scale; native lower-body position and alpha baseline register its frames. Falling/prone poses
use their corresponding native width/height references. [registration.json](registration.json) records every
transform. Extended silhouettes retain an expanded canvas instead of clipping.

## Atlas, placement and variants

[manifest.json](manifest.json) owns frame rectangles, crop offsets, page indices, timing, view aliases, native
bindings and palette parameters. `atlas/base_*.png` are shared RGBA pages; `atlas/mask_*.png` are identically packed
single-channel coverage pages. `previews/` contains baked variants for review only, not extra runtime requirements.
Aligned masters and tight crops remain in `aligned_2x/`, `masks_2x/`, `trimmed_2x/` and `trimmed_masks_2x/`.

The logical canvas is 256×256, with bottom-center pivot `(128,256)`. A cropped pixel `(u,v)` is placed using
`local_x = (crop_x + u)/2 - 128`, `local_up = 256 - (crop_y + v)/2`. Mirror the geometry and UV consistently.
Native `Center` flags are retained as provenance; current actor rendering bottom-anchors the full canvas.
Native frame scale is **2.0**, separately applied by the engine. The offline comparison displays both originals
and enhancements at the same logical zoom. Do not multiply actor size again just because export resolution doubled.

One soft coverage mask selects green mane and beard from the enhanced pixels. It protects hide, teeth, claws,
rust tips, mouth and eyes. Variant RGB uses the existing `masked_luminance_rgb_v1` operation:

```text
Y = dot(base.rgb, [0.2126, 0.7152, 0.0722])
target = Y * variant.luminance_vector
output.rgb = lerp(base.rgb, target, mask)
output.a = base.a
```

Inputs are encoded sRGB values, with linear mask coverage. Fixed vectors in the manifest are least-squares fits
from corresponding changed native palette entries. Palette 163 bypasses recoloring exactly. The runtime already
supports this operation; installing this family and binding its groups remains separate work.

Four pixels of crop padding and three pixels of transparent RGB/mask extrusion protect filtering. Mipmaps are
disabled in this export contract. Tight crops reconstruct aligned masters exactly and extracted atlas rectangles
match both base and mask. Decoded memory, including packing and mask cost, is in [validation.json](validation.json).
Actor instances share these resources; 60 Behemoths do not require 60 copies of the atlas.

Current packing uses five base/mask page pairs: **69.85 MiB decoded** (55.88 MiB RGBA + 13.97 MiB R8; 73,245,705 bytes total),
compared with 30 MiB for all original full canvases decoded as RGBA for one palette. These figures exclude mipmaps
and transient upload/CPU copies. Base and mask PNGs total 17.75 MiB on disk; review images and intermediate masters
are excluded from this shipping-asset figure.

## Review and reproduction

Review [all base frames](review/all_base_dark.png), [all masks](review/all_masks_light.png),
[palette comparison](review/standing_variants.png), and [worst contour crops](review/edge_current.png).
Per-batch native/restored comparisons are in `review/*_comparison.png`; full action review sheets are in `sheets/`.
The full sheets are presentation artifacts; use manifest atlas rectangles for rendering.

From the repository root, the deterministic stages are:

```sh
python3 level_generation/creatures/mm7_m162/process.py
python3 level_generation/creatures/mm7_m162/package.py
python3 level_generation/creatures/mm7_m162/build_viewer.py
python3 level_generation/creatures/mm7_m162/review_repair.py
```

These commands reuse `raw/`; they do not invoke AI. Python requires Pillow, NumPy, SciPy and PyYAML.
Do not rerun prepare.py or prepare_repair.py over the repaired batch plan. Versioned repair outputs are recorded
with ../mm7_m514/record_generation.py --project level_generation/creatures/mm7_m162; generation.json retains
both original records and versioned selections.
Submitted prompt checkpoints are separate from regenerated prompt templates.

Capture the viewer through the [approved helper](../../../tools/CAPTURE_LOCAL_HTML.md), called directly:

```sh
./tools/capture_local_html.py level_generation/creatures/mm7_m162/review.html \
  level_generation/creatures/mm7_m162/review/viewer_front.png \
  --query 'action=attack&view=0&palette=163&frame=2'
```

Quick checks cover source coverage, original hashes, crop reconstruction, atlas extraction, alpha/mask invariants
and magenta residue on **every cleaned and atlas-extracted frame**. Inspect the worst-edge contact on both light
and dark backgrounds as well; a low score alone is insufficient. No engine build or gameplay scenario is needed
for this staged art package.

Repair acceptance inspected all 32 replacements against native poses and placement, all 96 replacement palette
appearances and mane/beard masks, ordered claw/foot motion, light/dark edges, and final mirrored purple attack
and playing red rear walk browser captures. All package checks pass; zero edge candidates above 16.
Current artifact hashes are pinned in review/acceptance.json.

Remaining limitations: alpha is estimated from a colored matte, not recovered original transparency. AI adds
interpreted cracked hide, fur and facial detail; fine details and claw curvature vary between poses. Registration
preserves native placement approximately, not anatomical correspondence at every pixel. The recolor approximates
native palette appearance on new continuous-tone art rather than reproducing every indexed color exactly.
