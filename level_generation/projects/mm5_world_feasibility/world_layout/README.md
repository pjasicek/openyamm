# MM5 surface world layout — first proposal

**Use a coherent world terrain plan first, then derive six equal outdoor travel areas from it.** This is the right
stage between the feasibility inventory and detailed native map generation. The original MM5 surface supplies the
large-scale geography; MM6–MM8 assets and the calibrated level-generation workflow supply the eventual presentation.

Open the [interactive layout](index.html), [world terrain overview](world_map.png),
[foot-travel diagram](foot_travel.png) or [native material palette](tileset_palette.png).
The [editable layout](layout.json) records the region definitions, landmark anchors, connections and material choices.

**This surface overview contains six of the planned sixteen outdoor maps.** The
[complete outdoor index](other_outdoors.html) adds the **six Skyroad regions and four elemental planes**; see
[layer/access notes](OUTDOOR_LAYERS.md) for their arrangement, source previews and connections.

These are **minimap-style planning views**, not screenshots of generated ODMs. Ground textures come from local game
assets; hill shading is illustrative relief derived from MM5 mountain/scenery classes. MM5 did not supply a continuous
heightfield. Town symbols mark original entrances, not final town geometry. This makes the overview useful for choosing
biomes and routes without implying that detailed level design is finished.

## Reading the two reference images

- [1253.png](../../../../test_img/1253.png) provides the model for a simple regional foot-travel graph.
- [mm6_worldmap.jpg](../../../../test_img/mm6_worldmap.jpg) provides the model for a coherent joined terrain overview.

The new foot diagram shows connections between regions. The terrain view shows where those connections meet their
borders, and how snow, desert, forest, mountains and water continue across them. They answer different questions and
should remain separate views of the same editable layout.

## Equal map dimensions, different amounts of usable land

For the six **surface** ODMs, use the same starting dimensions:

| Quantity | Proposed common value |
| --- | --- |
| Stored native height samples | 128 × 128 |
| Sample spacing | 512 native units |
| Rendered terrain | 127 × 127 quads |
| Provisional travel square | X/Y −24,576 to +24,576; 49,152 units wide |
| MM5 source coverage per region | 32 × 32 source cells: four original squares |
| Simple planning ratio | 1 source cell spans 1,536 units, or 3 native terrain cells |
| Exported overview crop | 512 × 512 pixels per region |

The 1,536-unit ratio is a geographic planning ruler. It does not determine building size, road width, cliff height or
town-cell scale. Each original town is a symbolic wilderness entrance to a separate local map, so its new footprint
must be authored independently with calibrated houses and streets.

**The six squares in the joined view represent adjoining travel areas.** Each native terrain extends beyond the travel
square to supply scenery and roads continuing past the prompt. Those scenery aprons overlap conceptually with the next
region; concatenating six complete native meshes would count the apron geography twice. Generate edge terrain from a
shared world context, then fit regional arrivals and playable content inside each travel boundary. See
[regional transition calibration](../../../REGIONAL_TRANSITION_CALIBRATION.md).

The common default minimap/HTML crop is the travel envelope, including any water or void inside it; it is not an
all-walkable collision mask. Full terrain bounds are X −32,768…32,256 and Y −32,256…32,768, leaving buffers of
8,192 units west/north and 7,680 east/south. Authoring views may show those buffers separately. Fill them from actual
cardinal and diagonal neighbour cells; at a world edge, continue water where the source edge is water and preserve
Xeen's void where it is void. Keep required content inside the travel envelope. Share heights, materials and scenery
through the entire overlapping native terrain, not just one boundary line. The first detailed implementation is the
[Castleview–Kalindra buffer review](../../mm5_castleview_kalindra/landscape/buffer.html); other regions still need their
own native terrain generation and overlap verification.

Equal dimensions do not mean equal occupied area. Lakeside's water and mountains occupy space; Castleview's town
occupies space differently. Keep lakes, wilderness and exposure where they belong instead of filling all six squares
to the same density. Skyroads and planes are outside this surface overview and need separate composition studies.

## Surface arrangement and material direction

| Region | Original squares | Geographic / material direction |
| --- | --- | --- |
| NW — Alamar / Necropolis | A1, A2, B1, B2 | Northwestern lava and volcanic ridges; dry approaches; localized Shadowspire-like Necropolis; snow at the northeast fringe |
| NC — Desert / Northern Highlands | C1, C2, D1, D2 | Northern snow and snowy woodland; broad central desert; northern tower and pyramid approaches |
| NE — Blackfang / Lakeside | E1, E2, F1, F2 | Snow and mountains; snowy river; eastern lake and Lost Souls island; southern woodland and dry fringe |
| SW — Castleview / Kalindra | A3, A4, B3, B4 | Temperate grassland, Dark Grove, river/ponds, dry rocky northern fringe; main starting hub |
| SC — Sprite Forest / Southern Tower | C3, C4, D3, D4 | Desert fringe, rocky Gemstone Range, southern forest and watercourses |
| SE — Sandcaster / Eastern Forest | E3, E4, F3, F4 | Dry Sandcaster approaches, Crossroads, southern forests, River of Wrath and Venom Pond |

The source's biomes cross regional boundaries. Avoid treating one ODM as exclusively desert and its neighbor as
exclusively grass: that would create artificial seams and distort the original world. The northern snow belt and
central desert are particularly strong examples.

Selected donor families, with verified local texture paths in [palette_sources.json](palette_sources.json):

| Need | Starting assets |
| --- | --- |
| Temperate ground and towns | MM8 Ravenshore/Alvar: `grastyl`, `grastyl2`, `dirttyl` |
| Woodland | MM8 grass/dirt families, with Murmurwoods/Garrote-style canopy and decoration composition |
| Dirt badlands | MM8 Ravage Roaming: `dirttyl`, `rctyl` |
| Necropolis district | MM8 Shadowspire: dirt and `gstyl`; dead vegetation/ruins/architecture are equally important |
| Desert | MM8 Ironsand `plntyl` / `plsatyl`; lighter MM7 `7sand` is used in this overview |
| Volcanic terrain | MM8 Ironsand ground and `lavtyl` |
| Snow | **MM7 `7snow`**, present locally; Mount Nighon provides a native snow/dirt usage reference |
| Mountains | MM8 `rktyl` / `rctyl`, with cold or volcanic treatment where the source calls for it |
| Lakes and rivers | MM8 water family; shallow/deep distinctions retained in the overview |

These are art/material families, **not a completed native tile-bank assignment**. The native byte tile map and its
four configurable 36-tile banks constrain which transition families fit together. Before building each ODM, allocate
the actual base/lookup banks and check transitions from the bitmap artwork. The northern regions need particular
attention when combining snow, desert, water, rock and road families. Do not assume every attractive palette entry
can simply be added to one map. Follow the existing
[tile calibration](../../../FRONTAGE_AND_TILE_CALIBRATION.md).

The material plate includes Shadowspire's tar texture as a reference swatch; it does not introduce a new tar lake.
Future imports must retain normal MM5/world or shared-base ownership, rather than require the MM7 world to be mounted
merely to use a snow texture.

## Water, islands, lava and the world edge

The overview derives every water cell from the source. It retains the eastern Octopod Lake and Lost Souls island,
Snow River Rapids, River of Wrath, the southern watercourses and the separate Acid/Venom Pond anchors. Corners are
rounded slightly for presentation while retaining all source water-cell centers and the same connected water-body
count. This preserves topology at this stage; native shoreline and bridge construction will require a finer layout.

Acid and Venom Ponds are shown in the water family in this study; their final magical-water materials and effects are
still to be chosen. Do not merge them into ordinary unnamed lakes.

The northwest already contains lava and volcanic mountain classes. **A new large volcano is not part of this proposal**:
the terrain supports volcanic land, but a specific crater would be a new design choice. Likewise, **the dark world rim
is source space, not an ocean coast**. Do not wrap this flat world in an invented sea to resemble the MM6 example.

## Foot travel

There are seven neighboring region pairs. This follow-up checked both sides of representative borders, reciprocal
source map neighbors and connection to the Castleview exterior terrain component:

| Link | Treatment | Original representative crossing |
| --- | --- | --- |
| SW ↔ SC | Existing road | B3 (15,3) ↔ C3 (0,3) |
| SC ↔ SE | Existing road | D3 (15,1) ↔ E3 (0,1) |
| NC ↔ NE | Existing road | D2 (15,15) ↔ E2 (0,15) |
| NE ↔ SE | Existing road | F2 (0,0) ↔ F3 (0,15) |
| NW ↔ SW | Proposed off-road anchor on original dry ground | A2 (8,0) ↔ A3 (8,15) |
| NW ↔ NC | Proposed off-road anchor through original desert | B2 (15,7) ↔ C2 (0,7) |
| NC ↔ SC | Proposed off-road anchor through original desert | C2 (12,0) ↔ C3 (12,15) |

Thus **all seven can be kept as surface foot connections**, with four road links and three unpaved approaches.
The exact three off-road anchor selections are new authoring choices among multiple source-supported crossing cells.
This resolves the earlier feasibility study's terrain uncertainty at these representative crossings. It does not prove
that every border cell or route is safe or free of event restrictions.

The conservative static check excludes swimming, water walking, mountaineering, lava and space. It uses raw movement
wall codes separately from mapped visual scenery codes. Dynamic events, monsters, quest gates and travel time are
not simulated. Interpret movement through the primary
[ScummVM movement implementation](https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/interface.cpp);
surface/scenery names are cross-checked against its
[constants](https://github.com/scummvm/scummvm/blob/master/devtools/create_mm/create_xeen/constants.cpp).

Do not assign travel days yet. Record eventual bidirectional destination, arrival and heading independently; a drawn
line is not a runtime travel registration. Mirrors, Town Portal, boats, tower/sky travel and dungeon shortcuts remain
separate networks. Off-road links do not imply building roads to every mine or monster camp.

## First map: SW Castleview / Kalindra

**Start with SW.** It is the original starting hub and uses our strongest existing temperate settlement calibration.
It tests the question that matters most: whether Castleview, Kalindra, meaningful countryside and outward travel can
fit together at correct native scale. Starting with a simpler empty wilderness would postpone that question.

The next build should proceed as follows:

1. Lay out the complete SW travel square, water, dry northern fringe, both regional exits and reserved major anchors.
2. Fit Castleview's town footprint and its meaningful NPC/service sites using the existing building kit. Reserve the
   sewer access pattern, protected quest areas and Ellinger's entrance before detailing streets.
3. Build Castleview and the Kalindra approach as the first reviewable district within that region. Reserve Western
   Tower, Dark Grove, northern approach and eastern road even if their detailed content comes later.
4. Review a top-down plan, an oblique terrain view and player-height town/road views at the calibrated scale. Keep
   the 6-region partition provisional until this footprint test passes.

This task creates the world planning package. It does not yet generate SW's native ODM or its interiors, export the
quests, choose final combat balance, or solve Skyroad movement. Those remain subsequent implementation work.

## Files, reproduction and validation

- `layout.json`: editable design choices and original coordinate aliases.
- `world_map.svg` / `world_map.png`: annotated whole-world overview.
- `world_terrain.png`: uncluttered joined terrain view.
- `regions/*.png`: six exact, equal-size crops of that joined view.
- `foot_travel.svg` / `foot_travel.png`: regional connection diagram.
- `tileset_palette.png` / `palette_sources.json`: actual local material references.
- `foot_connections.csv`: source crossing coordinates and terrain checks.
- `verification.json`: source hashes, terrain counts and validation results.

Regenerate with:

```sh
python3 level_generation/projects/mm5_world_feasibility/world_layout/build_world_layout.py
```

The generator uses Pillow, NumPy, SciPy and the locally available Rsvg/Cairo bindings. It checks all seven crossings,
all 6,144 source cells, equal crop dimensions, source water topology and exact reconstruction of the whole terrain
image from the six region crops. This is cartographic validation; it is not a runtime traversal test.
