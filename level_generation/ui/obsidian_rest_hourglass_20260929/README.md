# Obsidian rest hourglass — approved artwork, 2140 sand correction

The user accepted the first proof's seamless motion and requested a better hourglass and sand design on 2026-09-29.
The user then approved the painted design and requested conserved sand quantities after reviewing `test_img/2140.png`.
The [animated design preview](index.html) keeps that artwork and corrects the transfer between chambers.
The user approved the correction and requested native integration on 2026-09-29. It is now installed in the shared
rest screen; see the [native integration record](native/README.md) and [game captures](native/index.html).

## Design

- Carved dark supports, worn brass collars and engraved plinths replace the thin vector construction.
- The glass is empty in the master, with genuine translucent alpha. Dynamic sand is drawn behind its reflections.
- Fine champagne sand uses an irregular material texture, rounded pile contours, soft edge shading and a narrow
  falling stream with a few moving grains. It replaces the flat fill and regular dot pattern.
- The same master is used at every instant. The approved eight-second drain and one-second smooth half-turn remain.
  Completed orientations are retained, including their painted highlights. There are no independently generated
  animation frames and no per-frame size or registration changes.

The **Design** selector switches the rest-screen illustration between this refinement and the archived motion proof.
The comparison now holds the corrected 25% and 75% transfer states beside an animated detail. The light backdrop control
exposes the alpha edges and glass interior. The wider calendar block and exit-button placement remain as in the first
proposal. The game now uses that placement, its existing rest timer and the exported graphics.

## Saved artwork and exact prompts

Both assets were made with the **built-in imagegen tool**, then copied into this workspace without pixel changes:

| Asset | Source / generation prompt |
| --- | --- |
| [Empty hourglass master](art/v2/hourglass-master-v1.png), 1024 × 1536 RGBA | [Exact prompt](art/v2/prompt.json). The existing `obsidian_journal_icon_story.png` was the material/reference input. |
| [Fine sand material](art/v2/sand-material.png) | [Exact prompt](art/v2/sand-prompt.json). New opaque material texture for clipped sand shapes. |

[Receipt](art/v2/receipt.json) records dimensions, hashes, alpha and checks. No alpha extraction, colour correction,
resizing or repainting was applied to the generated files. Composition and shading are controlled by `app.js`;
`sand-volume.mjs` owns the shared glass/pile geometry and conserved transfer.
The previous drawing is retained in `wire-model.js`; its original source and screenshot are in `revisions/motion_v1/`.

## Animation and review

The glass mask follows the master in its original image coordinates. Sand has a separate gravity orientation inside
that mask, so it cannot extend through the frame or glass when the artwork is inverted. Each orientation's full upper
reservoir is the half-turn of the other orientation's full lower reservoir, including texture coordinates and shading.
The painted master rotates as one object and never changes its scale.

### 2140: conserved sand

The previous independent square-root height curves let the bottom pile grow faster than sand left the upper bulb.
The corrected model integrates slices of the actual glass-clipped sand outline as a solid of revolution, then uses
volume lookup tables to find both fill levels. A fraction `p` below leaves `1-p` above. The shared amount fits one
chamber and remains fixed when the differently sized painted bulbs exchange places.

The larger bulb's full pile is calibrated to that same volume while reaching the neck. Its slope steepens gradually
near full, so the inverted pile stays connected to the neck without an abrupt shape reset or suspended sand.
Tables are built once; animation frames only interpolate them and update paths.

- [Quarter](review/volume_2140/quarter.png), [half](review/volume_2140/half.png) and
  [three-quarter](review/volume_2140/three-quarter.png) fills reviewed, along with the
  [opposite orientation](review/volume_2140/half-inverted.png), [light backdrop](review/volume_2140/light.png),
  [full rest layout](preview.png) and [turn clearance](review/volume_2140/turn.png).
- `node level_generation/ui/obsidian_rest_hourglass_20260929/check_sand_volume.mjs` remeasures the displayed pile
  and clipped upper reservoir at 2,010 samples across both orientations. Maximum total-volume error is **0.00323%**
  with the two-image-pixel integration slices and interpolated table. Transfer is monotonic, endpoints are empty/full,
  and both full piles reach their respective necks.
- Browser captures at both loop boundaries are **pixel-identical** at 500 × 750. The exact sand paths, grain coordinates,
  crest and painted frame persist through each half-turn. Updated results are recorded in the receipt.

Repeatable preview queries: `?phase=0.42` for a still, `?view=detail&phase=0.42` for an isolated close-up,
`?phase=0.444444444444` for half transferred, `?backdrop=light` for the light backdrop, and `?phase=0&turns=1`
for the opposite orientation. The volume estimate assumes rounded bulbs; the narrow stream and loose grains are
decorative. This is an illustrated animation, not a physical granular simulation. Earlier `review/v2/` captures
preserve the approved art before the quantity correction; use `review/volume_2140/` for the current motion.

The original background/animation investigation and native integration options are retained in [RESEARCH.md](RESEARCH.md).
That document records the first proof, before this generated artwork existed. The native implementation uses a
separate static shell and a padded sand atlas baked from these exact curves, with continuous GPU rotation.
