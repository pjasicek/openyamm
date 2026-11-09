# MM6 pmn2 mage restoration

Restored the native staff-carrying male mage family: **Apprentice Mage (610), Journeyman Mage (611), Mage (612)**.
All 59 source filenames are covered, with 56 distinct restored tiles, seven actions, five stored directions,
eight native view aliases, and three selective palettes. The accepted art is also installed as custom monsters
904–906 in Brackenford: see [engine integration and play instructions](ENGINE_INTEGRATION.md).

Open [review.html](review.html) directly in a browser. It compares original and enhanced animation at matching logical
size, with palette, direction, frame stepping, zoom, background, mask-overlay and crop-bound controls.
[Variant comparison](review/standing_variants.png), [all frames](review/all_base_dark.png),
[all masks](review/all_masks_light.png), and [light/dark edge crops](review/edge_current.png) cover the complete set.

## Delivered files

- [atlas/](atlas/): three base RGBA PNG pages and three matching grayscale coverage-mask pages.
- [manifest.json](manifest.json): crops, placement, pages, native animation/timing/mirrors, palettes and recolor formula.
- [sheets/](sheets/): all-action review sheets for each stored direction; blank rows mean no native artwork at that view.
- [previews/](previews/): deterministic red/blue palette pages and mask overlays. These are review outputs, not separate runtime texture sets.
- `aligned_2x/`, `trimmed_2x/`, `masks_2x/`, `trimmed_masks_2x/`: aligned masters and minimal padded exports.
- `raw/`, `references/`, `prompts/submitted/`, [sources.json](sources.json), [generation.json](generation.json): provenance and reusable checkpoints.
- [validation.json](validation.json) and [edge audit](review/edge_current.json): deterministic export checks.

## Native behavior and placement

Standing has five views. Walking has six frames for each of those five views. Attack and hit each have six front
frames; death has five, followed by a separate corpse frame. Fidget retains its native six-entry sequence
`a,a,c,d,e,f`: the source `b` filename is unreferenced, but its identical pixels also occur in used frame `e`.
Exact native duplicates `d=c`, `e=b`, `f=a` share enhanced artwork and atlas rectangles. All original filenames remain
addressable; no missing-angle artwork or new inbetweens were invented. Views 5/6/7 mirror 3/2/1 for standing/walking;
`Image1` actions use the front art from every direction. Every source entry is 125 ms. Original frame scale is 0.699997.

Native BMP canvases vary in width and, for falling/prone poses, height. They have no `Center` flag. Preparation aligns
them to a 331×272 logical canvas about bottom-center, pivot (165.5,272). Export uses two physical pixels per logical
pixel; crop offsets preserve that shared origin. Registration uses a common scale per batch and native body/baseline
landmarks. Falling/prone poses use separate anatomical measurements. Extended canvases retain any silhouette beyond
the standard canvas. Do not independently stretch tight crops or apply a second scale factor in an eventual loader.

## Appearance, palettes and cleanup

Palette 802's green appearance is the enhanced base. One soft mask selects the cape, trousers and hanging pouches.
Face, hair/beard, brown leather tunic, ochre rope belt, wooden staff, and cool dark boots/bracers are protected.
Palettes 801/803 are deterministic red/blue recolors, fitted from the actual native palette entries.

The documented `masked_luminance_rgb_v1` operation works in normalized encoded RGB:
`Y=dot(rgb,[0.2126,0.7152,0.0722]); target=Y*variantVector; output=lerp(base,target,mask)`.
The base is an exact bypass and all variants preserve alpha. Vectors are fixed across every frame and fitted by
least squares to changed green native palette entries, retaining shade detail without frame-by-frame normalization.
See `process.py:recolor` for the reference operation. The shared runtime now explicitly supports this operation
alongside the crusader's green-chroma mode; `install_runtime.py` produces the compact runtime manifest and content wiring.

Ten built-in image-generation requests produced the base sheets, using the accepted five-view standing sheet as
identity reference. Nine returned 1536×1024; fidget returned 1254×1254. Per-figure raw detail is roughly 1.5–1.9× native
height, depending on the batch. **2× denotes the export tier**, not guaranteed twofold new image detail.

The raw sheets use a magenta matte. The deterministic helper estimates partial alpha and unmixes background RGB;
contour correction runs before premultiplied-alpha resizing and again on resized edges. The green base has no
intended purple material, making the calibrated 10/255 contour tolerance suitable here. It must not be blindly
applied to red/blue previews or another creature. Masks are authored on final enhanced pixels. Base and mask receive
matching three-pixel color extrusion and four-pixel crop padding. No mipmaps are supplied.

The death sheet needed extraction-only boundary adjustments: top-row boots passed the nominal row split, and the
falling pose's staff tip crossed a column split. Moving boundaries through empty gutters retained all artwork without
another AI call. Source bitmaps were not modified.

## Checks and footprint

All source hashes, 59-file coverage, exact crop reconstruction, exact atlas extraction, variant-alpha preservation,
protected zero-mask pixels and exact base bypass pass. Every cleaned and final atlas-extracted frame is included in
the edge audit: **zero candidates above 16/255 alpha-weighted magenta excess**. Complete contacts and worst-edge crops
were visually reviewed; the score alone is not proof of ground-truth alpha. The offline viewer was captured with
native/restored standing, mirrored blue walking and red death poses.

The three base-plus-R8-mask pages occupy **46.14 MiB decoded**, shared across every actor and all three colors.
Base RGBA is 36.91 MiB and masks 9.23 MiB. Original variable-sized BMP canvases would occupy 10.23 MiB decoded RGBA
for one palette; original indexed files total 2.65 MiB on disk. Atlas PNGs plus manifest are about 9.75 MiB on disk.
Baked variant previews, reference images, masters and review sheets are excluded from the runtime estimate.
No runtime FPS claim follows from these allocation figures.

Fine facial, hair and cloth details remain AI interpretations and vary slightly between poses. The long staff is
somewhat thicker/more textured than the low-resolution original. Alpha is estimated from a composite, not recovered
original transparency. [Engine integration](ENGINE_INTEGRATION.md) records the subsequent gameplay review.

## Rebuild and capture

Dependencies: Pillow, NumPy, SciPy, PyYAML; local Chrome for the optional browser capture.

```sh
python3 prepare.py       # source inventory and reference grids; no AI generation
python3 process.py       # reuse accepted raw sheets; matte, register, recolor masks
python3 package.py       # atlases, metadata, previews, contacts and automatic edge audit
python3 build_viewer.py
```

Run these from this directory. Accepted exact prompts live in `prompts/submitted/`; preparation's prompt templates
may evolve, so it never rewrites that checkpoint directory. The local matte helper is reused from the goblin project;
mask/ramp/registration settings are pmn2-specific.

For browser captures, use the already approved [local HTML helper](../../../tools/CAPTURE_LOCAL_HTML.md) directly
from the repository root:

```sh
./tools/capture_local_html.py level_generation/creatures/mm6_pmn2/review.html \
  level_generation/creatures/mm6_pmn2/review/viewer_capture.png \
  --query 'action=walk&view=6&palette=803&frame=3'
```

Reuse the saved `./tools/capture_local_html.py` command approval; do not construct new inline Chrome invocations.
