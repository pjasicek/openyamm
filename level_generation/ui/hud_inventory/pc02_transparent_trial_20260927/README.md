# pc02 transparent imagegen trial — 2026-09-27

User-requested experiment after rejecting deterministic removal from the accepted PC art.
Two fresh **28-frame** built-in imagegen calls restore `pc02-01` through `pc02-56` from archived originals.
This is **pc02**, not `7pc02`. These are review candidates; accepted records and runtime assets are untouched.

Preview: <http://127.0.0.1:9100/level_generation/ui/hud_inventory/pc02_transparent_trial_20260927/index.html>

## Inputs and masters

- Native BMPs: `assets_legacy/icons_20260926/engine/icons/pc02-01.bmp` through `pc02-56.bmp`.
- Each original is 59×79. References use nearest-neighbor 2× originals in a 7×4 grid,
  1092×728 total, 156×182 slots, 118×158 panels with 19px horizontal / 12px vertical inset.
  Only the sheet gutters were made transparent in the references; all original RGB remains intact.
- Exact submitted prompts: [A](A/attempt_01/prompt.txt), [B](B/attempt_01/prompt.txt).
  Original-only references: [A](A/reference.png), [B](B/reference.png).
- Unmodified returned RGBA masters: [A](A/attempt_01/raw.png), [B](B/attempt_01/raw.png).
  Both are 1536×1024. `masters.json` pins their SHA-256, prompts and references.
  There was one call per sheet, no CLI/API fallback and no reused generated artwork.
- Generated files in the tool's default directory were copied here. Masters remain immutable.

## Placement and alpha

`frames/` contains all 56 transparent PNGs on identical **118×158** canvases. The shared canvas
centerline is x=59, and the bottom edge is y=158 (the last pixel row is y=157 in top-down PNG coordinates).

Extraction uses measured transparent gutters, including the shifted last row of sheet A.
`geometry.json` records each actual crop rectangle and archived-native silhouette bounds. The native
guide PNGs in `native_geometry/` were measured with the shared-backing estimate from the preceding
background-removal investigation. These guides are used **only to measure placement**, never to
cut the generated images or assign their opacity.

After the height correction requested from screenshot 2059, vertical scale maps the native crown
and bottom independently of horizontal fitting. Its silhouette center is placed on x=59; its
nearly opaque lower boundary meets the native bottom. Horizontal scale retains the earlier width
and hair-fringe fit. This is an explicit independent X/Y rescale, not uniform shrink-to-fit.
There is no skin/hair classification, color key, oval stencil, or painted repair.
Premultiplied-alpha Lanczos performs subpixel translation and downsampling together. Generated alpha
is retained, including fine hair and outline softness. The masters' solid interiors are mostly
alpha 252–253 rather than exactly 255; they have not been rethresholded.

`uncorrected/` shows extraction using the nominal input grid, before per-frame placement repair.
The preview compares originals, nominal extraction, aligned output, and selection-ring composition.
Both basebar and character-selection layouts use the corresponding renderer placement rules.
The preview is a local canvas composite, not an engine screenshot.

### Original/aligned comparison and global offsets

The first two preview panels show the **old original + ring** and **new aligned + ring** side by side.
Both follow the selection-ring checkbox and HUD-layout selector. Center/bottom guides mark the same
fixed icon origin in each panel.

Global X/Y sliders and numeric inputs move every aligned portrait, including the thumbnail gallery,
inside its fixed 118×158 canvas. Units are x2 image pixels, with half-pixel steps; positive X moves right
and positive Y moves down. The original portrait, facemask and selection ring stay fixed. Overflow is
clipped at the icon boundary before HUD scaling. Offsets persist across frames/playback and are stored
in `offsetX` / `offsetY` URL parameters for reloads and sharing. **Reset offset** returns both to zero.

**Download shown PNG** includes the current offset on a transparent 118×158 canvas. The base-alpha link
still opens the original aligned alpha for inspection. Offsets are preview/download settings; they
do not rewrite this trial's source PNGs, masters, or runtime assets.

## Findings and limits

- All 56 generated subjects have more than 2× actual native sampling in both axes; the minimum is **2.7222×**.
- Fresh alpha retains the gray stone head and pale hair/accessory edges without green-background erosion.
- The raw sheet grid still drifts; measured registration fixes the shared canvas and lower anchor.
  Horizontal corrections remain **−4.6% to −15.4%** relative to nominal extraction. Vertical scale
  now matches each native height independently, with crown error at most one output pixel across all 56 frames.
  The rejected width-limited export is retained in `history/width_limited_v1/`.
- Identity and state still require visual approval. Generator changes to expression, facial features and silhouette
  cannot be repaired by registration alone. Native frame 36's fragment is about 22% wider relative to its height
  than the original; frame 38 differs by about 10%. Both are marked in the viewer. Native frame 37 is tilted and
  does not have a fully opaque bottom-center contact even in its original silhouette.
- The lower states remain low fragments rather than being expanded into normal full heads.
- No ring-shaped mask clips the exported portraits. The runtime facemask/ring overlays can cover their edges,
  as demonstrated by the preview. The separate aligned portrait shows the complete export.

## Rebuild and checks

```sh
python3 level_generation/ui/hud_inventory/pc02_transparent_trial_20260927/build.py
```

This reads the pinned masters and measured geometry, checks all 56 native/accepted/runtime hashes,
then rebuilds only this trial's exports, contacts and manifest. It does not call imagegen.
Pillow and NumPy are required and were already available locally.

`manifest.json` contains every transform, alpha and sampling measurement, output hash, and review note.
`comparison.png`, `A/contact.png`, and `B/contact.png` are flat inspection plates, not runtime assets.
