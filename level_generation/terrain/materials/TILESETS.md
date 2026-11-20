# MM6–MM8 ground tilesets and their materials

Inventory of every native terrain tile drawn by the 42 MM6–MM8 outdoor maps (resolved per cell like the engine, through
each map's tileset lookups and the world's tile table; `tools/terrain_materials.py` `map_tiles`), grouped into
ground types, with the library material each uses on the outdoor terrain. Contact sheets of the
base and most-used transition tiles: [MM6](tilesets/mm6_tiles.jpg), [MM7](tilesets/mm7_tiles.jpg),
[MM8](tilesets/mm8_tiles.jpg) (magenta = tile alpha, the water or lava shown through shore tiles).

Every native transition is one ground type over dirt (or over hardpan, grey stone or lava in a few MM8 maps); the
weight tool classifies such tiles per pixel, so only the base ground types need materials. All 41 maps with terrain
have slot files (`worlds/mm6|mm7|mm8/terrain_materials/`); the Plane of Air has no terrain.

## Ground types

| Ground | Native tiles | Maps | Material (all CC0) |
| --- | --- | --- | --- |
| Grass | `6grastyl`; `7grastyl`; `grastyl`, `grastyl2` | 9 + 7 + 6 | `grass_meadow` with `grass_patchy` patches |
| Dirt | `6dirttyl` (cracked) | 15 | `dirt_cracked` |
| Dirt | `7dirttyl`, `dirttyl` (smooth earth) | 12 + 11 | `soil` (ambientCG Ground048) |
| Stony dirt | `7dirt1/2`, `dirt1/2`: scattered at random, a tenth of the dirt | 11 + 9 | `soil_stony` (Poly Haven rocky_trail) as the soil's variant |
| Dunes | `6sandtyl`; `plsatyl` (Ironsand) | 5 + 1 | `sand_ripples` at a large repeat |
| Flat sand | `7sand` | 5 | `sand_flat` (Poly Haven dense_sand) |
| Snow | `snotyl`; `7snow` | 3 + 5 | `snow` (ambientCG Snow008A, wind-carved drifts) |
| Badlands | `crktyl` (ochre); `7wastetile` (red-brown) | 2 + 3 | `dirt_cracked` |
| Hardpan | `plntyl` (Ironsand orange crust) | 1 | `dirt_cracked` at a small repeat |
| Swamp | `swmtyl`; `7swtyl` (moss with pools) | 2 + 2 | `swamp`: ambientCG Moss004 with standing water in its hollows, drawn as water |
| Volcanic | `6voltyl` (black rough) | 3 | `rock_ground` |
| Volcanic | `voltyl` (black gravel) | 3 | `gravel_volcanic` (ambientCG Gravel024) |
| Tropical | `troptyl` (Bootleg Bay, 3%) | 1 | `grass_patchy` |
| Rock ground | `rktyl` (grey layered rock) | 2 | `rock_layered` (ambientCG Rock023) |
| Dark stone | `gstyl` (Shadowspire) | 1 | `mud_cracked`, black, large plates |
| Grey dust | `gdtyl` (Shadowspire's ground: master tile 2 in its scene overlay) | 1 | `soil` tinted grey, with `mud_cracked` patches |
| Red rock | `rctyl` (Ravage Roaming) | 1 | `rock_red` (ambientCG Rock061, fine strata) |
| Cliffs | none (steep slopes) | all | `rock_cliff`, tinted per ground |
| Cobble roads | `6drsr*`, `7drsr*`, `drsr*`, `gdrd*` (shaped like the matching `drsr*` tile) | 34 | `road_pebbles` |
| Stepping stones | `plrd*` (Ironsand) | 1 | `road_flagstone` |

The MM7/MM8 variant tiles (`7dirt1/2`, `dirt1/2`, `grastyl2` and the 0.4–5% `x` variants of rock, gravel, dark
stone, red rock and dunes) are scattered one cell at a time to hide the repeat of a single tile; the weight tool
reads them as their base ground, and the variant patches (stony soil, patchy grass) or the anti-tiling sample do
that job without a cell grid. Lava (`lavtyl`) and tar (`tartyl`, Shadowspire) are drawn by the liquid renderer;
their rules say `shore: false`, so they get no beach or seabed.

Layer budget: Harmondale, Erathia, Emerald Island, Dagger Wound, Ravenshore and Alvar use all eight layers.

## Colour

The same ground differs between worlds and the per-world `reference_tile` tint follows the native tile (grass:
MM6 61,88,40; MM7 84,93,46; MM8 70,80,33; sand: MM6 219,171,89; MM7 147,117,47; MM8 dunes 180,114,48). Within a
world one native tile serves every map, so `world.yml` `maps:` gives a map its own `shade` (a tint multiplier that
also tints the variant) or any other material key, and can swap the beach for a desert map's own sand (`shore`):

```yaml
maps:
  outb3.odm:
    grass: {shade: [1.08, 1.0, 0.78]}   # drier Dragonsand grass
    shore: {material: desert}
```

Within one map, `macro_brightness`, `macro_tint` and the `variant` patches vary the ground over 250–16384 units.

## Maps

| Map | Name | Ground mix (% of cells, transitions counted with their ground) |
| --- | --- | --- |
| mm6/outa1.odm | Sweet Water | cracked 69, snow 18, dirt 10, road 2 |
| mm6/outa2.odm | Paradise Valley | cracked 56, sand 21, dirt 12, water 8, road 3 |
| mm6/outa3.odm | Hermit's Isle | water 43, sand 35, dirt 12, volcanic 6, shore 3 |
| mm6/outb1.odm | Kriegspire | snow 58, dirt 30, volcanic 9, road 2 |
| mm6/outb2.odm | Blackshire | dirt 60, sand 32, grass 3, road 2, water 1 |
| mm6/outb3.odm | Dragonsand | sand 57, water 33, grass 5, shore 4, dirt 1 |
| mm6/outc1.odm | Frozen Highlands | snow 51, dirt 38, water 6, road 3, shore 2 |
| mm6/outc2.odm | Free Haven | dirt 71, water 14, grass 5, shore 5, road 4, sand 2 |
| mm6/outc3.odm | Mire of the Damned | water 37, swamp 32, dirt 23, shore 5, road 2 |
| mm6/outd1.odm | Silver Cove | water 52, grass 26, dirt 15, shore 6, road 1 |
| mm6/outd2.odm | Bootleg Bay | water 63, dirt 15, grass 13, shore 4, tropical 3, road 2 |
| mm6/outd3.odm | Castle Ironfist | water 39, grass 20, dirt 18, swamp 13, shore 6, road 3 |
| mm6/oute1.odm | Eel Infested Waters | water 87, grass 10, shore 3 |
| mm6/oute2.odm | Misty Islands | water 84, grass 11, shore 4 |
| mm6/oute3.odm | New Sorpigal | water 69, grass 15, shore 6, dirt 6, volcanic 3 |
| mm7/7out01.odm | Emerald Island | water 93, grass 5, shore 1 |
| mm7/7out02.odm | Harmondale | grass 50, dirt 34, snow 12, road 2, shore 2, water 2 |
| mm7/7out03.odm | Erathia | grass 71, water 16, dirt 4, shore 4, snow 3, road 3 |
| mm7/7out04.odm | The Tularean Forest | grass 54, water 39, shore 4, dirt 2, road 2 |
| mm7/7out05.odm | Deyja | cracked 57, water 19, sand 18, dirt 5, shore 1, road 1 |
| mm7/7out06.odm | The Bracada Desert | sand 40, cracked 26, dirt 26, water 7 |
| mm7/7out13.odm | Tatalia | dirt 31, snow 27, water 26, swamp 13, shore 2 |
| mm7/7out15.odm | Shoals | sand 100 |
| mm7/out09.odm | Evenmorn Island | water 84, grass 12, shore 3 |
| mm7/out10.odm | Mount Nighon | dirt 65, snow 17, water 11, sand 6, shore 2 |
| mm7/out11.odm | The Barrow Downs | dirt 53, grass 29, water 9, shore 8 |
| mm7/out12.odm | The Land of the Giants | water 41, cracked 38, snow 13, dirt 6, shore 2 |
| mm7/out14.odm | Avlee | grass 65, water 29, shore 5, dirt 1 |
| mm8/elema.odm | Plane of Air | rock 100 |
| mm8/elemf.odm | Plane of Fire | lava 74, volcanic 18, lava shore 8 |
| mm8/elemw.odm | Plane of Water | dirt 100 |
| mm8/out01.odm | Dagger Wound Island | water 70, grass 16, shore 7, volcanic 4, dirt 2 |
| mm8/out02.odm | Ravenshore | grass 50, water 25, rock 11, dirt 7, shore 4, road 3 |
| mm8/out03.odm | Alvar | grass 60, rock 20, water 7, dirt 6, shore 5, road 3 |
| mm8/out04.odm | Ironsand Desert | hardpan 48, sand 31, lava 20, road 1 |
| mm8/out05.odm | Garrote Gorge | dirt 64, grass 30, shore 3, road 2, water 1 |
| mm8/out06.odm | Shadowspire | dirt 59, dark stone 26, water 9, tar 3, road 2 |
| mm8/out07.odm | Murmurwoods | grass 69, dirt 30, road 1 |
| mm8/out08.odm | Ravage Roaming | red rock 44, dirt 37, water 14, shore 4, road 1 |
| mm8/out13.odm | Regna | water 73, grass 23, shore 4 |
| mm8/out15.odm | Tutorial | dirt 100 |
| mm8/pbp.odm | Plane Between Planes | dirt 67, water 10, lava 9, volcanic 9, lava shore 3, shore 2 |

"Shore" is the water-over-dirt shore tiles; MM7's snow tile group also covers the high ground of Harmondale,
Tatalia and Mount Nighon. The MMerge Breach maps (`worlds/mmmerge`) are not included.
