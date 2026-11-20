# MM6 succulents: cacti, desert sage and dry weeds (2026-10-09)

Static 3D replacements for eight MM6 desert decorations. Everything is procedural: Blender geometry from scripts
and textures painted with numpy/PIL. There are no scans, no external images and no paid generation. The models are
installed but not yet bound in `decorations.yml`. Rebuild all of them in about a minute with
`./build.sh --install`, or rebuild some with `./build.sh --install cac8 cac5`.

| Model (`assets_dev/worlds/mm6/models/`) | Sprite (world height) | LOD triangles | File | Materials |
|---|---|---|---|---|
| `mm6_deco_cac8.glb` golden barrel | `cac8` (185, 197 placements) | 1464 / 872 / 470 / 160 | 1.0 MB | Body opaque, Spines MASK |
| `mm6_deco_cac5.glb` candelabra cluster | `cac5` (248, 81 placements) | 2352 / 1176 / 618 / 196 | 0.3 MB | Body opaque |
| `mm6_deco_cac16.glb` forked column | `cac16` (253) | 1408 / 928 / 320 / 170 | 0.4 MB | Body opaque |
| `mm6_deco_cac7.glb` long-pad prickly pear | `cac7` (137) | 2328 / 396 / 324 / 212 | 1.3 MB | Pads MASK |
| `mm6_deco_cac10.glb` spreading prickly pear | `cac10` (167) | 2876 / 1456 / 270 / 164 | 1.8 MB | Pads MASK |
| `mm6_deco_cac15.glb` low prickly pear, fruit | `cac15` (139) | 2898 / 1518 / 298 / 176 | 1.7 MB | Pads MASK |
| `mm6_deco_cac27.glb` silver sage on rock | `cac27` (139) | 604 / 310 / 174 / 78 | 2.3 MB | Rock opaque, Foliage MASK |
| `mm6_deco_snoweed1.glb` dry russet weeds | `snoweed1` (127) | 94 / 56 / 34 / 20 | 0.9 MB | Foliage MASK |

The models follow the same contract as the other decorations:

- glTF, Y-up, in metres, with the origin at the base centre on the ground.
- One mesh node (`Cactus` or `Shrub`) whose four-level LOD chain is in `openyamm_lods`
  (`tools/link_static_model_lods.py`).
- `COLOR_0` vertex occlusion on every primitive.
- Opaque bodies and rock are single-sided. Spines, pads and foliage are MASK 0.5 and double-sided.
- Extras: `openyamm_specular` is 0.2 on cactus bodies, 0.15 on pads and rock and 0.1 on spines and foliage. Only
  the shrub foliage has wind and translucency (`openyamm_wind` 0.02, `openyamm_translucency` 0.3).

The engine scales each model by its LOD0 height, so only proportions matter. Each model's width-to-height ratio is
within about 10 % of its sprite's (`scripts/bounds.py`). The exception is cac8, which was flattened on review
(revision 2): its bounds are 1.27 wide per unit of height, against 1.06 for the sprite's bounding box. That box
includes the sprite's tall spine tufts; the body itself is about 1.23 wide per unit of height.

## Suggested bindings

All of these use `yaw: random` and the default `lod_pixels`.

| name | height | height_jitter | z_offset |
|---|---|---|---|
| cac8 | 185 | 0.15 | -3 (the narrow bottom ring meets the ground) |
| cac5 | 248 | 0.12 | 0 |
| cac16 | 253 | 0.10 | 0 |
| cac7 | 137 | 0.15 | 0 |
| cac10 | 167 | 0.15 | 0 |
| cac15 | 139 | 0.15 | 0 |
| cac27 | 139 | 0.12 | -4 (the rock rim sits at ground level) |
| snoweed1 | 127 | 0.15 | 0 |

## Construction (`scripts/build_model.py`, helpers in `scripts/succ_lib.py`)

- **Ribbed sweeps** (`succ_lib.ribbed`): rings along a centre line with a rib profile of 1, 2 or 4 vertices per rib
  (valley, flank, crest, flank). The texture repeats once per rib, valleys at whole u. Valleys are creased
  (face normals) and crests smooth, using custom split normals. Ring radii set the bulges and pinches, and an apex
  closes the top.
- **cac8 golden barrel** (budget about 1.5k):
  - Revision 2 (review 2026-10-09) made the shape a squat dome with the widest point low: 24 ribs over a `cos^0.62`
    profile whose lower half is 0.75 m and upper half 1.27 m high. The widest ring (R 1.2 m) sits at 0.35 of the
    body height, the base curves in to 0.59 R on the ground, and the crown is flattened with a slight dimple.
  - `barrel_skin` paints dark green flanks, six woolly areoles per rib-metre and long, irregularly curved
    pale-yellow spines that cross into the neighbouring ribs. A per-rib v offset breaks up the horizontal rows.
  - A cut-out spine shell (`barrel_spines`, same tiling, ten long curved spines per areole) sits 7 cm above the
    crests on LOD0–2. Its normals come from
    the body's ellipsoid.
  - Long spine fringes stand on the crests. They are fewer than before: every second band per rib on LOD0, every
    third on LOD1 and every fifth on LOD2. Each is 0.22–0.36 m long, leans at random up to ±0.7 rad (so neighbours
    cross) and droops on the lower half. Each one maps a band of the spine tile transposed (v along the crest, u from
    the crest out past the tile edge, random v shift), so the areoles' side spines stand out of the silhouette.
    Fringe points are kept above the ground.
  - LOD3 has 10 crest segments plus a 10-segment shell.
- **cac5 candelabra cluster**: five columns placed from the sprite's column positions. Each has four deep wing ribs
  (depth 0.55) and pinched segment joints (0.62 R). `organ_skin` paints rich green flanks and a pale toothed
  margin with brown spine pairs on each crest. The levels are:

  | Level | Vertices per rib | Rings per segment | Sides |
  |---|---|---|---|
  | LOD0 | 4 | 3 | 4 ribs |
  | LOD1 | 2 | 3 | 4 ribs |
  | LOD2 | 1 | 2 | 6 |
  | LOD3 | 1 | 1 | 4 |

  A per-level occlusion gain evens out the creased against the smooth levels.
- **cac16 forked column**: an 8-rib trunk forks into a left arm, a taller right arm and a short front arm (Bézier
  limbs that start inside the trunk, gently swelling along their length, with rounded caps).
  `saguaro_skin` paints grey-green mottling, tubercle bumps (in the normal map) and four felted cream areoles with
  white and brown spines per tile. Alternate ribs are offset half a tile.
- **Prickly pears** (`grow_pads`, `PAD_STYLES`):
  - Root pads sit round an elliptical footprint, leaning outward more toward its rim. Each pad carries 0–3 children
    on its upper rim, turned in the parent's plane and twisted about their own long axis. Inner roots get one extra
    generation.
  - The whole plant is scaled so the highest pad reaches the sprite height.
  - Each pad (`succ_lib.pad`) is a quad grid spanning one 512² atlas cell whose painted oval has the pad's size.
    Both faces bulge into a lens: 4×4 grid on LOD0 for cac10/cac15 (36 triangles) and 3×3 for cac7. Coarser levels
    use 3×3 grids and then single flat double-sided quads.
  - Shading normals lean out toward the rim. The back face's rim vertices sit 0.5 mm behind the front's, so the
    card cutter never pairs a front and a back triangle into one card.
  - An oval proxy per pad is the occluder for the ray-traced vertex occlusion.
  - Fruit are small ellipsoids on the upper rims of the outer pads, textured from cell 3's swatches. cac15 also has
    flower cards. A fruit is dropped at any level that drops its pad.
  - cac15's root pads near the centre use the corky cell 2. On review it was shifted from purple-brown to the
    sprite's dry brown/olive, with grey blotches.
  - Cards are cut to their outline by `tools/cut_foliage_cards.py`.
- **cac27 silver sage**: a flat-shaded elliptical stone slab (radial rings with noisy rims and a steep front edge)
  textured with the tiled `rock_cac27`. On top are seven sage clumps of puff cards on a dome per clump, facing
  outward, plus darker crossed core cards. The texture paints dark lilac stems and needle leaves packed in a dome,
  silvery toward the rim. A grey dead branch tube rises to the right. The cards' occlusion rays also hit the rock.
- **snoweed1 dry weeds**: fan cards of thin branching russet stems with seed clusters at the tips: two clumps,
  one tall and one lower, plus low grass tufts (cell 3). The model is deliberately sparse, as the sprite is airy.

## Textures (`scripts/make_textures.py`)

All textures are original procedural work, so no attribution is needed. They are written to `textures/`:
basecolour plus an OpenGL normal map from a painted height field. Each texture has its own seed, so adding one
never changes the others. Rebuilds are byte-identical (checked by rebuilding everything twice).

| Texture | Size | Wrap |
|---|---|---|
| `barrel_skin`, `barrel_spines` | 256×1024 | tiles |
| `organ_skin`, `saguaro_skin` | 256×512 | tiles |
| `rock_cac27` | 512² | tiles |
| `pads_cac7`, `pads_cac10`, `pads_cac15`, `sage_cac27`, `weeds_snoweed1` | 1024² | atlases of 2×2 cells, colour dilated into transparent texels |

## Review

The renders are Eevee with an orthographic camera. Base colour is multiplied by `COLOR_0`, cut-outs are clipped at
0.5, and specular is scaled by `openyamm_specular` as the engine does it (`scripts/review.py`). For each model:

- `review/<id>/compare.png`: the native sprite, then LOD0 from the front, three-quarter and back.
- `review/<id>/lods.png`: every LOD from the front at the same scale.
- `review.py -- <id> --final` renders the finished, card-cut GLB's LOD0 (`final_front.png`) to check the cutting.

`scripts/sheet.py` prints the mean colour against the sprite's, and each level's colour and coverage against the
previous level.

| Model | Worst colour step between levels | Coverage between levels |
|---|---|---|
| cac8 | 4/255 | 0.93–0.96 |
| cac5 | 7/255 (green) | 0.93–1.08 |
| cac16 | 5/255 | 0.97 or more |
| cac7 | 2/255 | 0.95 or more |
| cac10 | 7/255 (flat pads at LOD2) | 0.97 or more |
| cac15 | 3/255 | 0.95 or more |
| cac27 | 3/255 | 0.90 or more |
| snoweed1 | 5/255 (LOD3) | 0.96 or more |

## Compromises

- **Lighting:** colours were matched under Eevee review lighting, not in the engine. Check them in game once the
  models are bound.
- **cac8:** the spines are painted on the body plus one shell and crest fringes. The fringes now cross and droop,
  but the body pattern is still more regular than the sprite's. The crown's dense pale wool is missing: the top
  reads darker. LOD3 (10 segments) looks slightly boxy, but it is only shown below about 80 px.
- **cac5:** the wing crests' teeth are painted, so the silhouette is smooth rather than toothed.
- **cac16:** the ribs read as regular stripes. The sprite's lumpy, yellow-blotched trunk is simplified.
- **Prickly pears:** some pads are seen edge-on as thin lenses. Pads at LOD2/3 are flat cards. The fruit are small
  ellipsoids. cac10 is slightly wider than the sprite (width/height 1.59 against 1.49).
- **cac27:** the sage puffs are rounder and more regular than the sprite's feathery mass. The dead branch is a plain
  tube. The rock is a single slab with no separate broken blocks.
- **snoweed1:** made from very few cards (94 triangles). It is denser in the middle and more uniformly russet than
  the sprite's open twigs.
- **Texture memory:** the pad and shrub atlases are 1024² (basecolour plus normal), so each prickly pear carries
  about 11 MB of GPU texture data with mipmaps. GPU texture compression would help.
