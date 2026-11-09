# MM8 plants, flowers, cacti and stumps in 3D (`plant*`, 44 types, 1,297 placements)

Batch of the MM8 decorations project (`../BRIEF.md`, `../README.md`). All 44 placed `plant*` decorations get a
static 3D model (plant08 shares plant02's). Everything is procedural or CC0: numpy-painted atlases and Blender bmesh
geometry, plus one Poly Haven bark scan.

## Pipeline

```bash
python3 scripts/make_atlas.py flowers|leafy    # shared cut-out atlases (2048², normal 1024), layout JSON
python3 scripts/make_textures.py bark|wood|cactus   # tiling textures
./build.sh <id>... [--install]                  # sprite_maps -> Blender build.py -> post.py -> sheet.py
python3 scripts/stack.py <ids>                  # review/stack.png: top rows of several sheets
python3 scripts/report.py <ids>                 # README rows + suggested bindings
python3 ../animated/scripts/check_winding.py work/<id>/mm8_deco_<id>.glb   # before every install
```

- `scripts/paint_lib.py`: painter. Strips along bent spines are rasterised with (t along, s across) coordinates,
  and style functions add veins, midribs, margins, bands, speckles, serration and highlights. Heights give the normal
  map (no gradient across shape boundaries), colour is dilated into transparent texels, and cells are seeded by
  name. `make_atlas.py` asserts that no two cells overlap.
- `scripts/make_atlas.py`:
  - `flowers` holds 12 face-on flower heads (mapped radially onto lathed heads), a bud, 8 leaves, a strap leaf,
    stems, and 4 sprays (round puffs for shell cards);
  - `leafy` holds schefflera, broad, spotted, dieffenbachia, heart, sword, grass blade, corn, lance, fern frond,
    water lily, violets, anthurium, bud, stems, grass tuft, ivy spray, twig tangle, pothos spray, green and pink
    lily pads, and a ground spray.
- `scripts/make_textures.py`:
  - `bark`: Poly Haven `bark_willow_02` graded to a neutral grey-brown; COLOR_0 gives the hue;
  - `wood`: pale splintered wood for stump tops;
  - `cactus_green`, `cactus_saguaro`, `cactus_yellow`: rib tiles with areoles and spines.
- `scripts/sprite_maps.py` writes `work/<id>/sprite.json` per sprite: the radius profile per height band (a volume
  of revolution, since placements turn at random), flower and leaf pixel density grids, and part mean colours.
- `scripts/plant_lib.py` (Blender, adapted from MM6 `succ_lib.py` and the MM6 flowers):
  - `Geo` accumulator with COLOR_0 = tint x occlusion (an analytic `Clump`: darker toward the ground and inside the
    volume, with volume normals blended into the faces' own);
  - parts: `leaf` (a strip fitted to the painted outline's half-width profile and folded at the midrib; a plain card
    at segs=1), `card`, `head` (lathed: flat, dish, cup, trumpet, goblet, dome or star profiles, mapped radially)
    and `tube`;
  - materials, export, and Eevee review renders.
- `scripts/clump.py`: the sprite-guided clump builder for flowers, leafy plants and shrubs. Groups:
  - leaves from the base, the volume, whorls with stems, or up a stalk (corn);
  - `shell` spray cards tangent to an inner shell (the leafy mass);
  - ring `cards`;
  - `heads` on the surface with short stems;
  - a `trunk` following the sprite's radius profile to the waist, with root lobes, and fanned `branches`, both in
    the Bark material.

  One seeded layout feeds every LOD (keep fraction, enlargement, fewer segments; `plan()`).
- `scripts/cactus.py`: ribbed sweeps after MM6 `succ_lib.ribbed`: segments (50/51), a saguaro column and arms
  (52/53), and columns (54). Fruit and flowers are goblet and star heads from the flowers atlas.
- `scripts/stump.py`: broken stumps after MM6 `stump5a`. A radial grid with root lobes; a jagged rim with tall
  splinters in pale `Wood`; an inner wall and hollow; mossy-to-brown bark COLOR_0. Overgrowth: anthurium (43) and
  an ivy vine (46).
- `scripts/recipes.py`: specs per model and the lily pad builder (`pads()`). `scripts/post.py`: material modes,
  `tools/link_static_model_lods.py`, `tools/cut_foliage_cards.py`, validation and `work/<id>/stats.json`.
- `scripts/sheet.py` writes `review/<id>/compare.png`: the native x2 sprite, LOD0 front, three-quarter, side and
  high view; the LOD row at a common scale with colour and coverage deltas; small switch-size tiles. It prints the
  mean colours and the w/h aspect against the sprite.

Material contract:
- `Foliage` (MASK 0.5, double-sided, `openyamm_specular` 0.1, `openyamm_translucency` 0.3);
- `Bark`, `Wood`, `Body` (cactus): opaque, single-sided, specular 0.05-0.2.

Every material in a model carries the same `openyamm_wind`: flowers 0.02, shrubs and taller leafy plants 0.03, the
fern 0.04, corn 0.05; cacti and stumps have none. Shared atlases are byte-identical across models (checked against
the embedded images), so the cook stores each texture once.

## Sources and licences

- Poly Haven [bark_willow_02](https://polyhaven.com/a/bark_willow_02) (CC0), copied to `source/bark_willow_02/`
  from the MM6 trees project.
- Everything else (atlases, wood, cactus skins) is original procedural work for this project; no attribution needed.

## Status (2026-10-16)

All 44 placed types are covered by 43 installed models (plant08 binds plant02's model, since its sprite differs only
slightly). Not bound yet: the bindings below are suggestions for `assets_dev/worlds/mm8/models/decorations.yml`.
Every model passed `../animated/scripts/check_winding.py` (0 inverted closed parts) before install. Each shared
texture (flowers, leafy, bark, wood and three cactus skins) is byte-identical in all 43 sources, so the cook stores it
once. The cooked runtime models total 5.0 MB.

## Models

Installed as `assets_source/engine/models/<file>` (source) and `assets_dev/engine/models/<file>` (cooked runtime).
LOD triangles are after card cutting. The source size includes the embedded shared textures; the runtime size is the
cooked GLB without them.

| Sprite | Kind | Placements | Model | LOD triangles | Source | Runtime | Review sheet |
|---|---|---:|---|---|---:|---:|---|
| `plant01` | plants | 36 | `mm8_deco_plant01.glb` | 444 / 102 / 36 | 4.1 MB | 75 KB | `review/plant01/compare.png` |
| `plant02` | plant | 18 | `mm8_deco_plant02.glb` | 1156 / 380 / 90 | 4.3 MB | 201 KB | `review/plant02/compare.png` |
| `plant03` | plant | 12 | `mm8_deco_plant03.glb` | 384 / 104 / 26 | 4.1 MB | 68 KB | `review/plant03/compare.png` |
| `plant04` | plant | 54 | `mm8_deco_plant04.glb` | 858 / 162 / 46 | 4.2 MB | 136 KB | `review/plant04/compare.png` |
| `plant05` | fern | 53 | `mm8_deco_plant05.glb` | 232 / 40 / 12 | 4.0 MB | 40 KB | `review/plant05/compare.png` |
| `plant08` | plant | 18 | `mm8_deco_plant02.glb` | 1156 / 380 / 90 | 4.3 MB | 201 KB | `review/plant02/compare.png` |
| `plant09` | plant | 27 | `mm8_deco_plant09.glb` | 704 / 208 / 64 | 4.2 MB | 122 KB | `review/plant09/compare.png` |
| `plant10` | plant | 15 | `mm8_deco_plant10.glb` | 522 / 164 / 30 | 4.1 MB | 90 KB | `review/plant10/compare.png` |
| `plant11` | plant | 34 | `mm8_deco_plant11.glb` | 180 / 32 / 8 | 4.0 MB | 31 KB | `review/plant11/compare.png` |
| `plant13` | plant | 24 | `mm8_deco_plant13.glb` | 384 / 72 / 18 | 4.1 MB | 63 KB | `review/plant13/compare.png` |
| `plant15` | plant | 7 | `mm8_deco_plant15.glb` | 258 / 66 / 30 | 4.1 MB | 48 KB | `review/plant15/compare.png` |
| `plant16` | flower | 38 | `mm8_deco_plant16.glb` | 1424 / 408 / 120 | 3.2 MB | 238 KB | `review/plant16/compare.png` |
| `plant17` | flower | 49 | `mm8_deco_plant17.glb` | 1452 / 554 / 153 | 3.2 MB | 270 KB | `review/plant17/compare.png` |
| `plant19` | flower | 42 | `mm8_deco_plant19.glb` | 1628 / 568 / 99 | 3.2 MB | 282 KB | `review/plant19/compare.png` |
| `plant20` | flower | 12 | `mm8_deco_plant20.glb` | 1468 / 484 / 78 | 3.2 MB | 252 KB | `review/plant20/compare.png` |
| `plant21` | flower | 46 | `mm8_deco_plant21.glb` | 960 / 316 / 64 | 3.1 MB | 166 KB | `review/plant21/compare.png` |
| `plant22` | flower | 45 | `mm8_deco_plant22.glb` | 1380 / 436 / 73 | 3.2 MB | 236 KB | `review/plant22/compare.png` |
| `plant23` | flower | 75 | `mm8_deco_plant23.glb` | 1348 / 308 / 90 | 3.1 MB | 214 KB | `review/plant23/compare.png` |
| `plant24` | flower | 23 | `mm8_deco_plant24.glb` | 264 / 80 / 21 | 2.9 MB | 49 KB | `review/plant24/compare.png` |
| `plant25` | flower | 29 | `mm8_deco_plant25.glb` | 820 / 206 / 81 | 3.0 MB | 139 KB | `review/plant25/compare.png` |
| `plant26` | flower | 90 | `mm8_deco_plant26.glb` | 1828 / 548 / 131 | 3.3 MB | 306 KB | `review/plant26/compare.png` |
| `plant27` | flower | 121 | `mm8_deco_plant27.glb` | 556 / 142 / 47 | 3.0 MB | 95 KB | `review/plant27/compare.png` |
| `plant28` | shrub | 6 | `mm8_deco_plant28.glb` | 516 / 244 / 120 | 6.2 MB | 61 KB | `review/plant28/compare.png` |
| `plant29` | shrub | 8 | `mm8_deco_plant29.glb` | 948 / 328 / 165 | 6.2 MB | 132 KB | `review/plant29/compare.png` |
| `plant30` | shrub | 4 | `mm8_deco_plant30.glb` | 616 / 266 / 132 | 6.2 MB | 71 KB | `review/plant30/compare.png` |
| `plant31` | flower | 11 | `mm8_deco_plant31.glb` | 1000 / 338 / 196 | 6.3 MB | 135 KB | `review/plant31/compare.png` |
| `plant32` | shrub | 37 | `mm8_deco_plant32.glb` | 820 / 338 / 168 | 6.2 MB | 91 KB | `review/plant32/compare.png` |
| `plant33` | flower | 17 | `mm8_deco_plant33.glb` | 1588 / 482 / 248 | 6.4 MB | 216 KB | `review/plant33/compare.png` |
| `plant34` | corn | 43 | `mm8_deco_plant34.glb` | 254 / 46 / 22 | 4.1 MB | 43 KB | `review/plant34/compare.png` |
| `plant37` | lily pad | 2 | `mm8_deco_plant37.glb` | 48 / 30 / 6 | 4.0 MB | 15 KB | `review/plant37/compare.png` |
| `plant38` | lily pad | 2 | `mm8_deco_plant38.glb` | 148 / 94 / 20 | 4.0 MB | 37 KB | `review/plant38/compare.png` |
| `plant42` | plant | 2 | `mm8_deco_plant42.glb` | 984 / 376 / 170 | 6.2 MB | 80 KB | `review/plant42/compare.png` |
| `plant43` | tree stump | 1 | `mm8_deco_plant43.glb` | 1066 / 420 / 170 | 7.6 MB | 87 KB | `review/plant43/compare.png` |
| `plant44` | tree stump | 52 | `mm8_deco_plant44.glb` | 868 / 336 / 150 | 3.5 MB | 49 KB | `review/plant44/compare.png` |
| `plant46` | tree stump | 2 | `mm8_deco_plant46.glb` | 968 / 396 / 186 | 7.6 MB | 73 KB | `review/plant46/compare.png` |
| `plant47` | tree stump | 89 | `mm8_deco_plant47.glb` | 868 / 336 / 150 | 3.5 MB | 49 KB | `review/plant47/compare.png` |
| `plant48` | plant | 26 | `mm8_deco_plant48.glb` | 2640 / 786 / 336 | 3.4 MB | 158 KB | `review/plant48/compare.png` |
| `plant49` | tumbleweed | 4 | `mm8_deco_plant49.glb` | 2382 / 714 / 276 | 3.3 MB | 124 KB | `review/plant49/compare.png` |
| `plant50` | cactus | 46 | `mm8_deco_plant50.glb` | 1140 / 330 / 140 | 0.3 MB | 91 KB | `review/plant50/compare.png` |
| `plant51` | cactus | 8 | `mm8_deco_plant51.glb` | 1812 / 474 / 215 | 3.3 MB | 207 KB | `review/plant51/compare.png` |
| `plant52` | cactus | 3 | `mm8_deco_plant52.glb` | 1348 / 442 / 297 | 0.3 MB | 103 KB | `review/plant52/compare.png` |
| `plant53` | flowering cactus | 5 | `mm8_deco_plant53.glb` | 1684 / 502 / 327 | 3.2 MB | 161 KB | `review/plant53/compare.png` |
| `plant54` | cactus | 60 | `mm8_deco_plant54.glb` | 1632 / 624 / 288 | 0.3 MB | 116 KB | `review/plant54/compare.png` |
| `plant56` | plants | 1 | `mm8_deco_plant56.glb` | 1036 / 236 / 92 | 4.2 MB | 168 KB | `review/plant56/compare.png` |

Review sheets (`review/<id>/compare.png`) show the native x2 sprite, LOD0 front, three-quarter, side and high
views, and the LOD row. The rendered LOD0 width/height is within about 10 % of the sprite for most models (printed by
`sheet.py`); flat lily pads are bound by width instead.

## Suggested bindings

Heights are the inventory heights (sprite pixels x DSFT scale). The exception is the lily pads (plant37, plant38),
whose height is their real thickness, so the pad spans the sprite's width on the water. Every binding uses
`yaw: random` (the default); none is mounted, swung or still. Stumps and cacti sink 2 units, so their root flares
and bases meet uneven ground.

```yaml
  - name: plant01
    model: engine/models/mm8_deco_plant01.glb
    height: 70
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant02
    model: engine/models/mm8_deco_plant02.glb
    height: 130
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant03
    model: engine/models/mm8_deco_plant03.glb
    height: 44
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant04
    model: engine/models/mm8_deco_plant04.glb
    height: 40
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant05
    model: engine/models/mm8_deco_plant05.glb
    height: 143
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant08
    model: engine/models/mm8_deco_plant02.glb
    height: 130
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant09
    model: engine/models/mm8_deco_plant09.glb
    height: 61
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant10
    model: engine/models/mm8_deco_plant10.glb
    height: 126
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant11
    model: engine/models/mm8_deco_plant11.glb
    height: 66
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant13
    model: engine/models/mm8_deco_plant13.glb
    height: 41
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant15
    model: engine/models/mm8_deco_plant15.glb
    height: 55
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant16
    model: engine/models/mm8_deco_plant16.glb
    height: 72
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant17
    model: engine/models/mm8_deco_plant17.glb
    height: 73
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant19
    model: engine/models/mm8_deco_plant19.glb
    height: 67
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant20
    model: engine/models/mm8_deco_plant20.glb
    height: 67
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant21
    model: engine/models/mm8_deco_plant21.glb
    height: 73
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant22
    model: engine/models/mm8_deco_plant22.glb
    height: 61
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant23
    model: engine/models/mm8_deco_plant23.glb
    height: 71
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant24
    model: engine/models/mm8_deco_plant24.glb
    height: 40
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant25
    model: engine/models/mm8_deco_plant25.glb
    height: 81
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant26
    model: engine/models/mm8_deco_plant26.glb
    height: 106
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant27
    model: engine/models/mm8_deco_plant27.glb
    height: 51
    height_jitter: 0.15
    lod_pixels: [300, 120, 60]
  - name: plant28
    model: engine/models/mm8_deco_plant28.glb
    height: 112
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant29
    model: engine/models/mm8_deco_plant29.glb
    height: 112
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant30
    model: engine/models/mm8_deco_plant30.glb
    height: 127
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant31
    model: engine/models/mm8_deco_plant31.glb
    height: 100
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant32
    model: engine/models/mm8_deco_plant32.glb
    height: 165
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant33
    model: engine/models/mm8_deco_plant33.glb
    height: 127
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant34
    model: engine/models/mm8_deco_plant34.glb
    height: 236
    height_jitter: 0.15
    lod_pixels: [500, 200, 80]
  - name: plant37
    model: engine/models/mm8_deco_plant37.glb
    height: 2
    height_jitter: 0.1
    lod_pixels: [300, 120, 60]
  - name: plant38
    model: engine/models/mm8_deco_plant38.glb
    height: 24
    height_jitter: 0.1
    lod_pixels: [300, 120, 60]
  - name: plant42
    model: engine/models/mm8_deco_plant42.glb
    height: 109
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant43
    model: engine/models/mm8_deco_plant43.glb
    height: 93
    height_jitter: 0.15
    z_offset: -2
    lod_pixels: [400, 170, 70]
  - name: plant44
    model: engine/models/mm8_deco_plant44.glb
    height: 101
    height_jitter: 0.15
    z_offset: -2
    lod_pixels: [400, 170, 70]
  - name: plant46
    model: engine/models/mm8_deco_plant46.glb
    height: 109
    height_jitter: 0.15
    z_offset: -2
    lod_pixels: [400, 170, 70]
  - name: plant47
    model: engine/models/mm8_deco_plant47.glb
    height: 93
    height_jitter: 0.15
    z_offset: -2
    lod_pixels: [400, 170, 70]
  - name: plant48
    model: engine/models/mm8_deco_plant48.glb
    height: 116
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant49
    model: engine/models/mm8_deco_plant49.glb
    height: 120
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
  - name: plant50
    model: engine/models/mm8_deco_plant50.glb
    height: 120
    height_jitter: 0.15
    z_offset: -2
    lod_pixels: [400, 170, 70]
  - name: plant51
    model: engine/models/mm8_deco_plant51.glb
    height: 124
    height_jitter: 0.15
    z_offset: -2
    lod_pixels: [400, 170, 70]
  - name: plant52
    model: engine/models/mm8_deco_plant52.glb
    height: 246
    height_jitter: 0.1
    z_offset: -2
    lod_pixels: [500, 200, 80]
  - name: plant53
    model: engine/models/mm8_deco_plant53.glb
    height: 246
    height_jitter: 0.1
    z_offset: -2
    lod_pixels: [500, 200, 80]
  - name: plant54
    model: engine/models/mm8_deco_plant54.glb
    height: 250
    height_jitter: 0.1
    z_offset: -2
    lod_pixels: [500, 200, 80]
  - name: plant56
    model: engine/models/mm8_deco_plant56.glb
    height: 128
    height_jitter: 0.15
    lod_pixels: [400, 170, 70]
```

## Construction notes

- **Flowers (16-27):** sprite-guided clumps. Spray-card shells (round leafy puffs) form the mass; leaves come from
  the base, as whorls on stems, or from the volume; flower heads sit on the surface, facing out and up, on short
  stems. Head profiles by species: lotus dish (16), tulip goblet (17), star-tulip cup (19), petunia and peach
  trumpets (20, 21), floret domes (22), lily dish (23), daisy flat (24), impatiens dish (25), white star (26) and
  blossom dish (27).
- **Shrubs (28-33, 42):** a bark trunk that follows the sprite's profile up to its waist, with root lobes (28/29,
  42), or fanned bark stems (30-33). The crown is about 110-170 small tilted spray cards over an inner dark layer.
  Hibiscus heads use one cell tinted white (29), orange (31) or yellow (33); tints are chosen in linear space. plant42
  has a short trunk and 11 branches under box-leaf cards.
- **Leafy plants:**
  - 02 schefflera whorls on a short stalk;
  - 03 spotted aglaonema rosette;
  - 04 grass tuft cards plus blades;
  - 05 fern fronds (painted pinnate, curving strips);
  - 09 pothos heart leaves over pothos puffs;
  - 10 broad-leaf whorls on a brown trunk;
  - 11 snake plant (banded swords with yellow margins);
  - 13 grass blades;
  - 15 three red stalks with lance leaves and two lilac buds;
  - 34 corn (alternating leaves up a stalk);
  - 01 a mixed bed (dieffenbachia, yellow croton, dark spotted leaves, grass, violets);
  - 56 four snake-plant clumps with ground sprays and white water lilies.
- **Lily pads (37, 38):** lathed discs mapped radially from painted pads with a notch: one olive pad (37); three
  pink pads round a magenta bud (38).
- **Stumps (43, 44, 46, 47):** the radial grid has root lobes, a jagged rim with two or three tall pale splinters, an
  inner wall and a hollow. Bark COLOR_0 runs from moss green at the roots to grey-brown. plant43 adds red anthurium
  spathes on stalks with broad leaves; plant46 adds a woody vine with ivy sprays.
- **Cacti:**
  - 50/51: a stubby trunk into four elongated 6-rib segments; 51 adds orange fruit (goblet heads);
  - 52/53: a 10-rib saguaro with three curved arms; 53 adds pale pink star flowers on it and at the base;
  - 54: four 12-rib olive-yellow columns.

  Skins tile one rib per u.
- **Dry (48, 49), `scripts/woody.py`, bark tubes only (polish pass 2026-10-16):**
  - plant48: 11 stems from the base fork twice into thinning woody tips; a twig ends where it leaves the sprite's
    silhouette.
  - plant49: a loose ball of 34 curly twigs (partial great-circle arcs with wavy radius, smaller inner arcs, curled
    tips), light grey-tan, with gaps that show through.
- **Polish pass (2026-10-16):** plant04 has 70 blades and 9 tuft cards; plant15 has 18 lance leaves; plant02 has 16
  whorls of 8 leaflets. All reinstalled under the same names.

## Compromises

- **Lighting:** colours were matched in Eevee review lighting, not in the engine. Most foliage reads a little darker
  and more uniform than the sprites' strong painted highlights. Check in game once bound.
- **Flower heads** are lathed geometry: some are seen edge-on or from behind (paler, flatter). Flowers seen face-on
  read well. Tulips (17) have weaker red flames than the sprite. plant22's florets are domes rather than the sprite's
  loose clusters.
- **Spray-card shells** (shrubs, 19, 21, 09) show a few flat card edges from close up and small gaps from above.
- **plant25:** the red leaves form a cap over the green base; in the sprite they stick out on stems.
- **plant24:** the broad leaves are larger than the sprite's.
- **plant42:** the branches are straight tubes; the sprite's twisted, interwoven trunk is simplified.
- **plant48:** the branches are slightly darker and sparser than the sprite's pale, dense fan.
- **Stumps:** the hollow and splinters are uniformly pale; the sprite's darker weathered streaks and moss patches are
  simplified to a COLOR_0 gradient. plant46's ivy is small patches, not the sprite's large leaves across the front.
- **Cacti:** spines are painted only (geometric spines would be sliver triangles), so silhouettes are smooth.
  plant54's columns are more regular than the sprite's.
- **Lily pads:** their binding height is their real thickness (2 and 24 units), so height_jitter mostly varies the
  pad size.
- **Triangles:** plant26 (90 placements, 1,828 at LOD0) and plant54 (60 placements, 1,632) exceed the 1,500 guideline
  for hundreds of placements but fit the tens range. plant48 (26 placements, 2,640) and plant49 (4 placements, 2,382)
  are tube-only woody models within the tens range. Every flower's LOD2 is under 160 triangles.
