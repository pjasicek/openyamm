# MM7 plants: fern, cacti, Joshua tree, broad-leaved plant and potted plants (2026-10-15, revision 2 2026-10-16)

Static 3D replacements for fourteen MM7 outdoor plant decorations. Everything is procedural: Blender geometry from
scripts and textures painted with numpy/PIL. There are no scans, no external images and no paid generation. The
models are installed (`tools/install_model.py --engine`) and bound in `assets_dev/engine/models/decorations.yml`
(engine content; not edited here). Revision 2 (quality pass, 2026-10-16) is described below.

The sprites are read from `assets_legacy/decorations_x2_20261016/`. Revision 1 sheets are kept as
`review/<id>/sheet_rev1.png` and revision 1 GLBs in `work/rev1/`.

```bash
./build.sh                    # textures + all fourteen models, review sheets, finish and validate (about 2 min)
./build.sh --install bush03   # rebuild and reinstall some
python3 scripts/overview.py   # review/overview_bushes.png and review/overview_pots.png
```

`bush14` and `bush15` are not built here: they bind the MM6 models `mm6_deco_cac24` and `mm6_deco_cac7`.

## Models

Source GLBs in `assets_source/engine/models/`, cooked runtime copies in `assets_dev/engine/models/`. Triangles are
LOD0 / LOD1 / LOD2 after card cutting. Sizes are the source GLBs (textures embedded; the cooked copies are 40–240 KB
plus cooked textures).

| Model | Serves | Plant | Triangles | Source size |
|---|---|---|---|---:|
| `mm7_deco_bush03.glb` | `bush03` (200, 7out04, out09) | fern mound | 384 / 160 / 96 | 1.1 MB |
| `mm7_deco_bush10.glb` | `bush10` (94, 7out05, 7out06) | squat saguaro, two arms, spine rim | 1172 / 426 / 153 | 0.3 MB |
| `mm7_deco_bush11.glb` | `bush11` (56, 7out05) | tall pale column, spine fringe | 800 / 276 / 88 | 0.3 MB |
| `mm7_deco_bush13.glb` | `bush13` (43, 7out06) | candelabra, three arms | 958 / 578 / 239 | 0.2 MB |
| `mm7_deco_bush12.glb` | `bush12` (42, 7out05) | Joshua tree | 808 / 360 / 172 | 0.9 MB |
| `mm7_deco_bush16.glb` | `bush16` (31, 7out06) | upright prickly pear | 640 / 528 / 64 | 1.3 MB |
| `mm7_deco_bush02.glb` | `bush02` (5, 7out01) | dieffenbachia | 552 / 278 / 124 | 0.9 MB |
| `mm7_deco_plant01a.glb` | `plant01a` (8, 7out04) | glazed ochre amphora, leafy sprays | 688 / 412 / 248 | 1.5 MB |
| `mm7_deco_plant11a.glb` | `plant11a` (6, 7out04) | terracotta pot, small tree | 550 / 398 / 168 | 1.3 MB |
| `mm7_deco_plant02a.glb` | `plant02a` (2, 7out03) | terracotta pot, palm fronds | 560 / 380 / 172 | 1.6 MB |
| `mm7_deco_plant01b.glb` | `plant01b` (2, out09) | worn brass amphora with spout, withered fronds | 1000 / 480 / 256 | 1.7 MB |
| `mm7_deco_plant07b.glb` | `plant07b` (2, out09) | patinated amphora, dry grass | 908 / 434 / 238 | 1.3 MB |
| `mm7_deco_plant03b.glb` | `plant03b` (1, out09) | square marble planter, withered fronds | 144 / 100 / 84 | 1.5 MB |
| `mm7_deco_plant04b.glb` | `plant04b` (1, out09) | stone amphora, wilting leaves | 1452 / 684 / 302 | 1.5 MB |

Budgets (`scripts/common.py`): the fern stays lean for its 200 placements; the cacti with 50+ placements are within
300–1500; bush12, bush16 and the potted plants (few placements) are props with few placements (up to 2600 / 2400).

## Revision 2 (quality pass, 2026-10-16)

The coordinator relayed this pass from the user: improve whatever would benefit, and reduce triangles where it makes
sense. No Meshy or Codex jobs were needed. Triangles are LOD0 / LOD1 / LOD2.

| Model | Revision 1 | Revision 2 | Change |
|---|---|---|---|
| bush03 | 448 / 204 / 76 | 384 / 160 / 96 | Rebuilt as a dome of arching fronds (below); w/h 1.33 → 1.08 (sprite 1.04) |
| bush02 | 552 / 250 / 56 | 552 / 278 / 124 | Pale leaves re-graded to cream; LOD2 keeps the leaf positions, folds and a round stem (coverage against LOD1 0.65 → 0.89) |
| bush10 | 1112 / 364 / 167 | 1172 / 426 / 153 | Sparse rim of black spine cards; trunk and arm rings 7/6/6 → 5/5/5 |
| bush16 | 1440 / 544 / 60 | 640 / 528 / 64 | Fleshy, lumpy, irregular pads; 3×3 lenses on LOD0 |
| bush11 | 992 / 276 / 88 | 800 / 276 / 88 | Column rings 10 → 7 |
| bush13 | 1186 / 706 / 265 | 958 / 578 / 239 | Trunk rings 11 → 8, arm rings 7/8/7 → 5/6/5 |
| plant01a | 964 / 448 / 248 | 688 / 412 / 248 | Pot 20 → 16 segments, belly 5 → 4 points per side, handles 6 × 8 → 5 × 6 |
| plant11a | 666 / 398 / 168 | 550 / 398 / 168 | Pot 20 → 16 segments |
| plant02a | 676 / 380 / 172 | 560 / 380 / 172 | Pot 20 → 16 segments |
| plant04b | 1620 / 684 / 302 | 1452 / 684 / 302 | Petiole tubes 6 → 4 segments (the pot keeps 20 segments) |
| plant01b, plant07b, plant03b | unchanged | unchanged | Rebuilt only for the shared atlases (fronds, leaves) |
| bush12 | unchanged | unchanged | Not reinstalled |

LOD0 total over the 14 models: 12,516 → 10,616 triangles. Weighted by placement: 400,654 → 344,834 (−14 %).

- **bush03 fern:** 64 fronds, each a quadratic Bézier from a ring of radius 0.12 H at the base to a tip on a dome
  shell (horizontal radius 0.52 H, height H, at least 0.38 of the radius out from the axis, lowest tips on the
  ground). The control point is raised above the chord, so every frond arches over and the outline is a rounded mound
  of frond backs. The fern strip has 36 overlapping lobed pinnae, leafy to the tip (taper 0.7).

  | Level | Fronds | Segments |
  |---|---|---|
  | LOD0 | 64 | 3 |
  | LOD1 | 62 % | 2 |
  | LOD2 | 38 % | 2 |

  Coarser levels widen the cards ×1.18 / ×1.36 and are 10 % brighter, to hold the colour.
- **bush02:** the `leaf_var` cell is now cream (232, 230, 182) over most of the blade, with green margins and veins
  (the sprite's light quartile is 188, 201, 148). LOD0 front mean: 75, 84, 61 → 89, 95, 72, against the sprite's
  83, 91, 68.
- **bush10 spine rim:** a `Spines` material (MASK) with the `bush10_spines` tile: two areoles, each with three or four
  long, black-brown, curving spines. Each rib crest is resampled every 0.24 m, and 80 % of the pieces get a card
  0.05 H long, in the plane of the crest and its outward direction (`spine_fringe`). LOD1 has half of them; LOD2 has
  none. The spines now break the outline as the sprite's do.
- **bush16 pads:** `lumpy_pad` replaces the MM6 pad painter. Each pad has a wobbling obovate outline, light from the
  upper left, large lumps in the height field (normal strength 6), glossy pale tops, a soft dark rim and 45 jittered
  areole bumps. In the geometry, each pad bends (±0.3 of its half-height) and twists (±0.2). Pad widths vary
  ±15 %, and chains twist more (0.9). LOD0 uses 3×3 lenses, LOD1 82 % of the pads at 3×3, and LOD2 80 % as flat
  quads.

### Reduction check

`scripts/reduce_check.py` adapts the reduction pilot's ladder (`../../mm6_reduce_pilot/scripts/deco_ladder.py`):
- It reads the GLB directly and welds the opaque LOD0 surfaces (Body, Pot, Bark).
- It collapses them texture-aware at 70/55/45/35/25 % and measures the two-way Hausdorff distance in % of the
  model's height.
- It passes, as in the pilot, at max ≤ 1.5 % and mean ≤ 0.15 %.
- Its `compare` mode measures a procedural cut against revision 1 with the same limits.
- It runs in a pymeshlab venv.

The ladder on revision 1 found little room: only bush13 and plant01b pass at 70 %. These meshes are already
procedurally lean, and collapse breaks the rib creases and pot silhouettes first. So the cuts were made in the
builder instead (fewer rings or segments), and each one was measured with `compare`:

| Model | Max | Mean | Result |
|---|---|---|---|
| bush10 | 0.56 % | 0.049 % | pass |
| bush11 | 0.16 % | 0.025 % | pass |
| bush13 | 0.36 % | 0.013 % | pass |
| plant01a | 0.59 % | 0.096 % | pass |
| plant11a | 0.41 % | 0.074 % | pass |
| plant02a | 0.42 % | 0.077 % | pass |

The same 16-segment pot failed on the big amphorae, where the pot is more than half the model's height: plant01b
(mean 0.19 %), plant07b (max 2.2 %) and plant04b (mean 0.17 %). Those keep 20 segments. The sheets show no visible
difference for the kept cuts.

### Checks

- `../../mm8_3d/animated/scripts/check_winding.py` reports 0 inverted closed parts on all 14 GLBs.
- `finish.py` validates every model.
- The models were reinstalled under the same names with `--engine`.
- Model heights barely change (bush03 is now 1.38 m tall, against 1.49 m before), and the engine scales each model
  to its binding, so the binding heights stay as they are.
- Before/after sheets: `review/<id>/sheet_rev1.png` against `review/<id>/sheet.png`, and
  `review/overview_rev2_before_after.png` for bush03, bush10, bush16 and bush02.
- `review.py` now retries, then falls back to Cycles on the CPU, when Eevee crashes on a full GPU.
- I could not take gallery screenshots. `build_gallery.py --world mm7` builds the gallery, but the viewer shows
  "Viewer could not load" for every MM7 item, including the MM6 models. The manifest's sprite frames still point
  to `assets_dev/engine/decorations_x2/`, which has moved to `assets_legacy/decorations_x2_20261016/`.

## Suggested bindings (all outdoor)

All use `yaw: random` and the default `lod_pixels` (500 / 200 / 80). None needs `mount`, `free_model`, `swing`,
`still` or `z_offset`: every sprite has one frame, and every model stands on y = 0.

```yaml
  - name: bush03
    model: engine/models/mm7_deco_bush03.glb
    height: 122
    height_jitter: 0.15
  - name: bush10
    model: engine/models/mm7_deco_bush10.glb
    height: 163
    height_jitter: 0.12
  - name: bush11
    model: engine/models/mm7_deco_bush11.glb
    height: 154
    height_jitter: 0.12
  - name: bush13
    model: engine/models/mm7_deco_bush13.glb
    height: 273
    height_jitter: 0.10
  - name: bush12
    model: engine/models/mm7_deco_bush12.glb
    height: 256
    height_jitter: 0.12
  - name: bush16
    model: engine/models/mm7_deco_bush16.glb
    height: 129
    height_jitter: 0.15
  - name: bush02
    model: engine/models/mm7_deco_bush02.glb
    height: 190
    height_jitter: 0.12
  - name: plant01a
    model: engine/models/mm7_deco_plant01a.glb
    height: 252
    height_jitter: 0.05
  - name: plant11a
    model: engine/models/mm7_deco_plant11a.glb
    height: 256
    height_jitter: 0.05
  - name: plant02a
    model: engine/models/mm7_deco_plant02a.glb
    height: 246
    height_jitter: 0.05
  - name: plant01b
    model: engine/models/mm7_deco_plant01b.glb
    height: 141
    height_jitter: 0.05
  - name: plant07b
    model: engine/models/mm7_deco_plant07b.glb
    height: 170
    height_jitter: 0.05
  - name: plant03b
    model: engine/models/mm7_deco_plant03b.glb
    height: 142
    height_jitter: 0.05
  - name: plant04b
    model: engine/models/mm7_deco_plant04b.glb
    height: 158
    height_jitter: 0.05
```

The heights are the inventory's `art_height`. The models were built at that height in metres (/ 81.7), so a model's
bounds match its art. The pots get a small jitter because they are made objects, and potted-plant pairs on one map
should stay alike. Bind them in 7out01, 7out03, 7out04, 7out05, 7out06 and out09; those maps then need a lighting
re-bake (`tools/lighting/stale_bakes.py`).

## Contract

- glTF, Y-up, metres, origin at the base centre on the ground. One mesh node (`Plant` or `Cactus`), three levels
  linked as `openyamm_lods` (`tools/link_static_model_lods.py`). No level is taller than LOD0: coarser levels with
  enlarged cards are squashed in height to LOD0's top, because the engine scales by LOD0's bounds.
- `COLOR_0` on every primitive (analytic height/depth occlusion times ray-traced occlusion against the solid parts and
  the ground).
- Materials:
  - `Body` (cactus skins), `Bark` (Joshua trunk) and `Pot` are opaque and single-sided.
  - `Fronds`, `Leaves`, `Pads` and `Spines` are MASK 0.5 and double-sided, and cut to their texels by
    `tools/cut_foliage_cards.py`.
- Extras:
  - `openyamm_specular`: cactus bodies and pads 0.2, foliage and spines 0.1, bark 0.1. Pots: glazed ochre 0.45,
    brass 0.35, patina and marble 0.25, clay and stone 0.15.
  - Foliage has `openyamm_wind` and `openyamm_translucency` 0.3. The wind is 0.03 for bush03, bush02 and bush12, and
    0.02 for the potted plants. The wind value is the same on every material of a model (pot and Joshua bark
    included), so leaves stay attached. The cacti have no wind.

## Construction (`scripts/build_model.py`, helpers in `scripts/plants_lib.py`)

The builder reuses the MM6 succulents library (`../../mm6_new_sorpigal_3d/succulents/scripts/succ_lib.py`:
geometry accumulator, ray-traced vertex occlusion, ribbed sweeps, pad lenses, cards, materials, export). It is
imported unchanged, with its texture and work folders pointed here. `plants_lib.py` adds:
- bent foliage strips (each quad one texture rectangle, so the cutter can cut it), with an optional folded midrib;
- tubes mapped into an atlas strip or a tiling texture;
- lathes for the pots;
- crossed star cards.

`scripts/profile.py <id>` prints a sprite's opaque runs per height band, which were used to place limbs, rosettes and
pot profiles.

- **bush03 fern:** see Revision 2 (a dome of 64 arching Bézier fronds).
- **bush10:** a 12-rib trunk (radius 0.175 H) with a domed top, and two arms traced from the sprite: left from
  0.58 H to 0.81 H, right from 0.36 H to 0.61 H. Each arm is a Bézier elbow starting inside the trunk. The crests
  carry a spine rim (Revision 2).
  - LOD0: two vertices per rib (creased valleys).
  - LOD1: one vertex per rib.
  - LOD2: about 60 % of the ribs.
- **bush11:** one column with 16 shallow ribs, a narrow foot, a bulge in the middle, a slight lean and a domed top.
  Each crest carries a fringe of spine cards, one `bush11_spines` tile (0.24 m) per card, in the plane through the
  axis: 96 cards on LOD0 and half of them on LOD1. LOD2 is the bare column.
- **bush13:** a 7-rib trunk (radius 0.085 H, deep ribs, pale crests) with a short left arm, a front arm over the
  trunk and a right arm. The arms rise from 0.42–0.5 H to 0.66–0.74 H.
- **bush16:** prickly-pear chains as in the MM6 succulents (`grow_pads`, adapted): 9 roots on a small footprint,
  growing up to five pads high, mostly upright. The pads bend and twist; see Revision 2 for the levels.
- **bush12 Joshua tree:** a trunk and five branches traced from the sprite (pixels → metres), as 8-sided tubes with
  the `joshbark` tile. Five rosettes are spiky balls of crossed `burst` star cards (12 / 7 / 4 per rosette), plus
  upward `half` stars under them on LOD0/1.
- **bush02:** a short green stalk with 24 leaves on petioles:
  - The lower and middle leaves are pale and variegated; they spread and droop.
  - Most of the top leaves are dark and raised.
  - LOD0 leaves are folded blades (two quads across, four segments). LOD1 has 70 % of the leaves with two segments;
    LOD2 has 50 % of them, flat with two segments and no petioles.
- **Pots (one lathe family):**

  | Pot | Plants | Shape | Texture |
  |---|---|---|---|
  | Amphora | plant01a, 01b, 07b, 04b | Rounded belly (sampled 5 / 3 / 2 points per side), neck, flared lip, inner wall, soil disc; two loop handles; a spout on 01b | `pot_gold`, `pot_brass`, `pot_patina`, `pot_stone` |
  | Terracotta pot | plant11a, 02a | Rolled rim on a separate saucer | `pot_clay` |
  | Square planter (4-segment lathe, flat normals) | plant03b | Plinth, a body widening upward, a lipped top slab | `pot_marble` |

  The amphora proportions per sprite are in `POTS`.
- **Plants in the pots:**

  | Plant | Content |
  |---|---|
  | plant01a | Two tall leafy sprays (`spray` strip) facing the front, with shorter sprays and palm fronds |
  | plant02a | Twelve upright palm fronds |
  | plant11a | A thin woody stem and a side stem, three large crossed cards of the `clump` cell (a small tree with twigs) round the stem, and eight smaller clump cards |
  | plant01b, plant03b | Seven withered fronds (cubic Béziers): each rises out of the mouth, turns over the rim and hangs outside the belly (plant03b biased to the front) |
  | plant07b | Eight `grass` fan cards round the mouth, tilted outward |
  | plant04b | Fourteen green petioles arching out of the mouth, each with a hanging green or brown wilting leaf |

## Textures (`scripts/make_textures.py`)

The paint surface is imported from the MM6 succulents painter
(`../../mm6_new_sorpigal_3d/succulents/scripts/make_textures.py`: `Canvas`, `rib_base`, `radial_spines`, `pad`),
with its output folder pointed at `textures/`. Each texture has its own seed. Each writes a basecolour and an OpenGL
normal map from a painted height field; linking converts the normal map to the glTF convention. Colours are measured
from the native sprites. A preview is in `review/textures_preview.png`.

| Texture | Size | Content |
|---|---|---|
| `fronds` | 1024², four 256 × 1024 strips | fern, leafy spray, palm frond, withered frond |
| `leaves` | 1024² | Variegated, dark, green and wilted broad leaves, the small-tree `clump` cell, dry `grass` fan and two opaque stem strips |
| `bush10_skin`, `bush11_skin`, `bush13_skin` | 256 × 512 | Rib tiles |
| `bush10_spines`, `bush11_spines` | 256 × 512 | Spine fringe tiles, cut out |
| `pads_bush16` | 1024² | Four pad cells |
| `joshua` | 1024 × 512 | `burst` and `half` star rosettes |
| `joshbark` | 512² | Tile |
| `pot_gold`, `pot_brass`, `pot_patina`, `pot_stone`, `pot_clay`, `pot_marble` | 512² | Wrap round the pot. v runs down the profile from the lip, so bands sit on the shoulder; the top rows are the soil swatch. Built from mottle, crackle, flaking patches, throwing rings, marble veins and star-shaped broken holes |

## Sources and licences

All geometry and textures are original procedural work for this project. They contain no third-party images, so no
attribution is needed. The code derives from the project's own MM6 succulents pipeline, which is imported, not
copied. Blender is the tool.

## Review

- `review/<id>/sheet.png`: the native x2 sprite, LOD0 from the front, three-quarter and side, then LOD0–LOD2 from
  the front at one scale with their triangle counts.
- `review/overview_bushes.png` and `review/overview_pots.png` stack all the sheets.
- `review/native_sprites_*.png` show the sprites together.

The renders are Eevee with an orthographic camera (`scripts/review.py`, adapted from the MM6 succulents). The base
colour is multiplied by `COLOR_0`, cut-outs are clipped at 0.5, and specular is scaled by `openyamm_specular`.

LOD0 front mean colour against the sprite's (sRGB, Eevee review lighting):

| Model | Sprite | LOD0 | Model | Sprite | LOD0 |
|---|---|---|---|---|---|
| bush03 | 55 100 28 | 63 100 36 | plant01a | 113 96 40 | 113 97 47 |
| bush10 | 75 112 62 | 69 104 57 | plant11a | 53 47 21 | 65 60 29 |
| bush11 | 96 131 78 | 100 124 81 | plant02a | 71 72 40 | 70 69 41 |
| bush13 | 41 65 28 | 40 64 30 | plant01b | 79 68 33 | 87 75 45 |
| bush12 | 74 82 52 | 72 80 51 | plant07b | 54 46 32 | 57 54 40 |
| bush16 | 50 83 34 | 53 89 43 | plant03b | 72 62 42 | 64 60 43 |
| bush02 | 83 91 68 | 75 84 61 | plant04b | 63 62 40 | 57 60 39 |

Neighbouring levels differ by at most about 8/255 in mean colour, and coverage stays within about 10 %
(`work/logs/<id>_sheet.txt`).

## Compromises

- **Lighting:** colours were matched under Eevee review lighting, not in the engine. Check them in game once the
  models are bound (the gallery shows them only after binding).
- **bush03:** since revision 2 a rounded mound (w/h 1.08). The pinnae are still more regular than the sprite's
  feathery fronds, and the top fronds still rise a little. LOD2 (96 triangles) is at the lower end of the budget,
  for 200 placements.
- **bush10, bush13:** bush10 has a spine rim of cards since revision 2. bush13's spines are still painted. The arms
  are smooth Bézier elbows.
- **bush11:** the spine fringe is subtler than the sprite's pale halo. LOD2 has no fringe.
- **bush16:** since revision 2 the pads are lumpy and uneven. The clump is still sparser than the sprite's, with a
  few edge-on pads in the left chain. LOD2 (64 triangles) uses flat pads.
- **bush12:** the rosettes are crossed star cards. They read as spiky balls but have less dark-centre / bright-tip
  contrast than the sprite.
- **bush02:** the dark leaves are flatter than the sprite's. w/h is 1.21 against 1.07.
- **Pots:** the surfaces are procedural (no Poly Haven set fits glazed or patinated pottery). The broken holes are
  painted dark stars, not geometry. The glazed amphora (plant01a) has no painted highlights. plant11a is brighter
  than its dark sprite.
- **Plants in the pots:** the withered fronds hang as smooth curves. plant07b's grass is a denser tuft than the
  sprite's airy, drooping strands. plant04b is the heaviest potted plant (1620 LOD0 triangles), because each wilting
  leaf has its own petiole tube.
- **Texture memory:** each source GLB embeds its own copy of the shared atlases (fronds or leaves 1024², pot 512²).
