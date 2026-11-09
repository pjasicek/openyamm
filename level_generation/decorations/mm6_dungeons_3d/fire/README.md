# MM6 dungeon fire fixtures in 3D (2026-10-09)

Batch `fire` of the MM6 dungeon decorations project (brief: `../BRIEF.md`). Procedural Blender models traced from the
restored native frames (`assets_dev/engine/decorations_x2`, x2 pixels at 0.5 map units), no paid generation.
Rebuild, review and validate everything with `scripts/build.sh` (about 2 minutes); `scripts/build.sh --install`
also installs. Single props: `scripts/build.sh [--install] <prop> ...`.

| Model (`assets_dev/worlds/mm6/models/`) | Sprite | LOD triangles | Bounds (units, w x h) | File | Animation |
|---|---|---|---|---|---|
| `mm6_deco_brazier.glb` | `brzier00` (lit) | 1490 / 284 / 103 | 50 x 146 | 1.5 MB | Flame flipbook, glowing Glow bed (emission, pulse) |
| `mm6_deco_brazier_unlit.glb` | `brazir2f` (unlit) | 1404 / 212 / 80 | 49 x 146 | 0.4 MB | none (native single frame) |
| `mm6_deco_flambeaux.glb` | `flamb00` | 782 / 532 / 194 | 59 x 199 | 1.2 MB | Flame flipbook, unlit Embers |
| `mm6_deco_sconce2.glb` / `_free` | `scon200` | 1766 / 862 / 320 (free 1686 / 810 / 296) | 56 x 127 | 0.8 MB | Flame flipbook, unlit Embers |
| `mm6_deco_sconce1.glb` / `_free` | `scon100` | 986 / 594 / 208 (free 934 / 562 / 184) | 62 x 98 | 0.8 MB | Flame flipbook, unlit Embers |
| `mm6_deco_cauldron_pot.glb` | `cauld00` | 1510 / 870 / 268 | 101 x 94 | 4.0 MB | Fire flipbook (1 billboard + 5 fixed ring cards), Brew `openyamm_uv_scroll [0.035, 0.02]`, glowing Glow bed |
| `mm6_deco_candle.glb` | `cndlab0` | 970 / 648 / 194 | 36 x 60 (logical; bind at 36) | 1.2 MB | Flame flipbook |

Flames: every card uses the project's shared CC0 Unity Labs flipbooks in `../textures/` (`flame02` for the brazier,
flambeaux and cauldron, `flame03` for the sconces and candle; `openyamm_flipbook: [16, 4, 30]`; finish `FLAME`:
BLEND, double-sided, unlit). `fire_lib.flame_card` places a card so the flipbook's flame base (measured texture v
0.023 / 0.055) sits in the fixture's embers and its tip (median v 0.70) reaches the native flame's top; the card stops
at the tip, so no model rises above its sprite (the few frames whose wisps go higher are cut off there). The cards
are in the model's x/up plane at y = 0 with the flame axis at the origin (the cauldron's three cards keep their
offsets across the model). Flame atlases cut from the native frames were tried first and dropped (the x2 upscales
are too poor).

## Revision 2: real PBR surfaces (2026-10-09)

The user found the brazier pair, cauldron and candle "solid colours, no texture/roughness" in the gallery. Their
materials now use texture sets derived from CC0 Poly Haven scans (`scripts/fetch_textures.py` downloads them into
`source/polyhaven/`; `scripts/pbr.py` and `scripts/make_pbr_textures.py` derive `textures/ph_*`): base colour
(the scan's light and dark structure, desaturated and turned toward the native colour family, its contrast set to
the native sprite's measured luminance spread), the scan's OpenGL normal map (strengthened), and glTF
metallic-roughness from the scan's roughness map (low constant metal, as before). COLOR_0 still tints each material
to the measured native colours (`textures/means.json`). Glowing parts have their own lit material `Glow` (the ember
texture, normal and roughness) with a constant `emissiveFactor` and `openyamm_pulse`, replacing the unlit `Embers`.
Flambeaux and sconces are unchanged (they keep `fx_*`).

| Set | Poly Haven source (author) | Used for |
|---|---|---|
| `ph_ironpit` (256) | Rusty Metal 04 (Amal Kumar), high contrast | brazier bowl and chains, candlestick foot, wick |
| `ph_iron` (512) | Rust Coarse 01 (Dimitrios Savva, Rico Cilliers), grey | cauldron pot |
| `ph_pewter` (256) | Rusty Metal 02 (Rob Tuytel), spots flattened | candle drip pan |
| `ph_rock` (512) | Marble Rock 01 (Amal Kumar), pink | cauldron stones |
| `ph_wax` (256) | Leather White (Rob Tuytel), grain only, cream | candle and its wax pool |
| `ph_charwood` (256) | Bark Brown 02 (Rob Tuytel) | charred logs |
| `ph_charcoal` (256) | Marble Rock 02 (Amal Kumar), dark | charcoal lumps |
| `ph_ember` (256) | Marble Rock 01 through a fire ramp (its cracks glow) | Glow beds (brazier, cauldron) |

Model changes in this revision:
- Brazier pair: `ph_ironpit` with the bowl retiled (6 x around); the lit bowl's colours re-measured on `brzier00`
  (blue-lit bottom, near-black flank, fire-reddened upper wall). Glow bed: albedo (160, 70, 24), emission
  sRGB (170, 78, 26), pulse [0.18, 0.75].
- Cauldron: pot colours re-measured by 4-unit band; stones are now seeded convex-hull shards (16 / 12 / 9 points
  per LOD) with split facets, so COLOR_0 lights them apart (pale tops, dark flanks, darker toward the ground);
  14 charcoal lumps (20-triangle icosahedra) on a Glow bed that reaches into the gaps between the stones (emission
  sRGB (180, 70, 18), pulse [0.2, 0.6]); the fire is one camera-facing core card plus five fixed `Ring` cards between
  the stones facing outward (a billboard keeps only its offset across the model, so only fixed cards can stand in
  front of the pot's belly, where the sprite's flames lick up it; `Ring` has the same flipbook, no billboard).
- Candle: pan colours re-measured by radius (greyer toward a dark rim, dark outer side), a melted wax pool over
  the socket (the sprite's bright disc at the candle's foot), unoccluded.

Review: `review/<prop>/sheet.png` (Blender) and the gallery shots `review/rev2_before/` and `review/rev2_after/`
(`dungeon_<sprite>_side.png`, `shoot_gallery.mjs ... side`).

## Models

- **Brazier** (`build_brazier.py -- brazier|brazier_unlit`): one geometry for both sprites of the pair, traced from
  `brazir2f`: a hemispherical iron bowl 48 wide with a rolled lip, three chains (front, and two behind at 120
  degrees) from the lip to a ring at 64 units, and one chain from the ring to the ceiling end at 146 (the bounds
  top: a `swing` would pivot there). LOD0 chains are interlocking 6 x 3 oval links (12 + 3 x 7, 4.8 wide, heavy
  wire like the sprite's); LOD1/LOD2 replace each chain by a thin tube. The lit model adds an unlit ember bed rising
  up the bowl's inside and the flame card (base 16, tip 72, like the lit sprite's flame). COLOR_0: the unlit
  sprite's near-black iron, or the lit sprite's fire-warmed chains and bowl (dark brown, cooler at the bottom).
  Chain and bowl share one material (`fire_lib.merge_materials` after tinting).
- **Flambeaux** (`build_flambeaux.py`): free-standing (the frames show a floor plinth): stepped octagonal plinth (flat
  shaded), pole with collars, shallow dish (rim top 158), ember bed, flame from 155.5 to the sprite top 199. Violet
  pole and plinth, deep blue dish underside, fire-lit pink rim top.
- **Sconces** (`build_sconce.py -- sconce2|sconce2_free|sconce1|sconce1_free`): `scon200` a gold goblet cup with
  two loop handles, six leaf lobes on its bell, ringed stem and spike; `scon100` a squat spinning-top bowl whose domed
  top steps up in gold rings with dark grooves to the flame opening. The wall variants add a gold arm (and, for
  scon200, a brace) to a wall plate at Blender +y (glTF -z; back face 28 / 34 units behind the flame axis), kept
  within the sprite's height; the `_free` variants are the fixture alone, as the sprites show it.
- **Cauldron** (`build_cauldron.py`): the dungeon `cauld00`, a different and smaller pot than the outdoor `ckfyr00`
  tripod model: bulbous black pot on five pink-grey stones (three in front where the sprite has them), two charred
  logs across under it, coals, an unlit ember bed and three flame cards in the gaps between the stones. The native
  animation is the fire under the pot (the pot itself is static in all six frames); the brew surface under the rim
  scrolls (the procedural `brew` texture) so the contents churn as the plan asked.
- **Candle** (`build_candle.py`): black bell foot, neck, pewter drip pan with socket, cream wax candle with four drips,
  wick and a small flame (base on the wick, tip at the sprite top). Built in logical units: bind at 60 x 0.6 = 36.

## Colour

COLOR_0 = vertex occlusion x a per-material tint linear(native sRGB) / linear(texture mean), measured from the
native frames by height (`fire_lib.tint`, `fire_lib.stops`; texture means in `textures/means.json`). Tints are
clamped to one (the brightest gold highlights and the wax top are slightly under the native). Native dungeon
colours are kept dark (the unlit brazier is near black).

## Textures and licences

- Revision 2 (`textures/ph_*`, see above): derived from CC0 Poly Haven textures (https://polyhaven.com/license,
  no attribution required; authors listed above for credit), downloaded at 1k PNG into `source/polyhaven/<asset>/`
  with each asset's `files.json` listing. Used by the brazier pair, cauldron and candle.

Earlier sets (still used by the flambeaux and sconces, and the cauldron's `brew`):

- `textures/fx_iron`, `fx_gold`, `fx_steel`, `fx_rock`: the outdoor props' procedural iron, gold, steel and stone
  (`../../mm6_new_sorpigal_3d/props/textures`, generated by that project, read only) copied with brighter base colour
  where needed (iron x2, gold x1.3, rock x1.6) and a new metallic-roughness map of low metal (0.2-0.25; rock 0):
  the engine's indoor ambient lights only the (1 - metallic) diffuse part, so the props' fully metallic gold would
  render near black.
- `textures/wax`, `textures/brew`: procedural, tileable (`scripts/make_textures.py`, FFT noise).
- `logs`, `embers`: the outdoor props textures, unchanged.
- Flames: `../textures/flame02`, `flame03` (CC0 Unity Labs flipbooks, shared by the project).

## Scripts

`fetch_textures.py` (Poly Haven download), `pbr.py` + `make_pbr_textures.py` (revision 2 sets, means),
`make_textures.py` (earlier textures, means), `fire_lib.py` (materials, tints, flame cards, chain links, LOD loop; uses
`../scripts/dungeon_lib.py`), `build_brazier.py`, `build_flambeaux.py`, `build_sconce.py`, `build_cauldron.py`,
`build_candle.py`, `review.py` + `sheet.py` (review renders and sheets), `finish.py` (the pilot's finish with this
batch's FINISH table: material modes, LOD link, validation, install), `build.sh`.

## Review

`review/<prop>/sheet.png`: native first frame | LOD0 front | three-quarter | side, and every LOD. Renders use a white
environment at strength one, a weak key light and no specular (diffuse albedo comparable with the sprite; flame
cards emissive on their first frame and turned toward the camera, as the engine turns them).

## Known compromises

- `brazir2f` is the unlit brazier (one frame, light 0) and `brzier00` the lit one (six frames, light 256 in
  `decoration_data.txt`); all 111 placements start unlit. Both models share the unlit sprite's proportions
  (146 units visible, bowl bottom 3.5 units above the placement point), so lighting a brazier switches only the fire
  and colours; the native lit sprite is 4 % smaller and starts at the placement point.
- The flame cards show one shared flipbook (not the native flame shapes); scon200/scon100 flames are narrowed and
  stretched (about 0.2 width/height) to match the sprites' tall thin flames.
- scon200's fleur-de-lis scrolls are approximated by six simple leaf lobes; scon100's cracked-plate pattern on the
  lower cone is not modelled (gradient only).
- The cauldron's pot-bottom fire glow is a COLOR_0 gradient (no light from the cards). Its fixed ring cards show
  edge-on between the camera-facing ones from some angles, and all its cards play the flipbook in step.
- Glow emission is constant per material (the engine has no emissive texture), so the beds glow evenly and their
  crack detail comes from the lit ember texture on top.
- Chains at LOD1/LOD2 are plain tubes.
