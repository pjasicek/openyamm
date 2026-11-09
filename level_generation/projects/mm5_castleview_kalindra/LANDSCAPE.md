# Castleview–Kalindra heightmap and decoration placement

[Open the landscape review](landscape/index.html) · [Town decoration map](landscape/town_decoration.png) · [Town heightmap](landscape/town_height.png) · [Regional decoration map](landscape/region_decoration.png) · [Regional heightmap](landscape/region_height.png) · [Full terrain buffer](landscape/buffer.html) · [Checks](landscape/verification.json)

This adds actual quantized terrain samples and individual foliage/decoration positions to the city/region wireframe. It remains an authoring draft: the new fountain, well, benches, crate stacks, bridges, buildings and walls need their native geometry, and the new interactions need event bindings. No live world tables or generated Lua were edited.

## Heightmap files and coordinates

| File | Meaning |
| --- | --- |
| [heightmap_u8.png](landscape/heightmap_u8.png) | 128×128 grayscale samples, native byte values; multiply by 32 for world elevation. It is intentionally dark when viewed without normalization. |
| [heightmap.raw](landscape/heightmap.raw) | The same 16,384 bytes, row-major, with no header. |
| [heightmap_units_u16.png](landscape/heightmap_units_u16.png) | 16-bit grayscale; pixel values are world elevation directly. Do not multiply this version by 32 again. |
| [terrain.json](landscape/terrain.json) | Sample orientation, exact pad vertices/elevations, water levels, source hashes and terrain-fit adjustments. |
| [surface_classes.png](landscape/surface_classes.png) | Categorical source geography: 0 rim/void, 1 grass, 2 dirt/road, 3 river, 4 Acid Pond, 5 desert, 6 snow, 7 lava, 8 scorched ground, 9 swamp, 10 rock. These are planning classes, not final native tile IDs. Only the first 127×127 cells form rendered quads. |
| [travel_edge_profiles.json](landscape/travel_edge_profiles.json) | North/east travel-edge elevations for matching the later neighbouring regions. Those neighbours have not been generated. |
| [buffer.json](landscape/buffer.json) | Exact crop/terrain bounds, neighbouring source maps and the overlap handoff contract. |
| [terrain_domain_mask.png](landscape/terrain_domain_mask.png) | 0 unused storage, 1 playable map crop, 2 scenery buffer; 128×128 storage, 127×127 actual quads. |
| [playable_crop_mask.png](landscape/playable_crop_mask.png) | 255 inside the travel envelope, 0 elsewhere. This includes water and void inside the envelope; it is not a collision/walkability mask. |
| [source_map_ids.png](landscape/source_map_ids.png) | Source maze number at each quad centre; 0 outside the source world or in unused storage. |
| [buffer_scenery.json](landscape/buffer_scenery.json) | Separate scenery-only tree/rock placements outside the travel envelope. No rewards, NPCs or other required content. |

Sample `(row, column)` corresponds to `x=(column−64)×512`, `y=(64−row)×512`. North is up. Sample bounds are X −32,768…32,256 and Y −32,256…32,768; the travel envelope remains ±24,576. The terrain uses the native triangle split, not bilinear interpolation. PNGs under `town_*` and `region_*` are labelled review pictures, not import height arrays.

The authored broad landforms are a higher northern shoulder, the northeastern dirt/rock shelf, a gentler southeastern woodland rise, the river valley and the city shelf. Original MM5 cells supply horizontal geography; they do not contain these recovered heights. Height reviews now explicitly overlay water, lava and void colours on the elevation palette. This fixes the misleading green Acid Pond in `test_img/1255.png`: its water was already constrained to elevation 768, but the earlier height-only tint looked like grass. The raw grayscale files remain elevations only.

There are 37 flattened premises pads. Every terrain vertex supporting a foundation has its recorded height. Adjacent footprints that share a native vertex share a shelf, avoiding contradictory flat-pad heights. Town pads span 640–864; the temple is at 864 and Ellinger at 832. This supersedes the initial isolated 1,152-height sketch. Architectural roof/tower targets remain measured above the local pad.

The natural river is flat at 256 and Acid Pond at 768. Xeen's black rim remains void, with an elevation drop toward zero, rather than becoming an ocean. Ordana's small constructed pool needs its own basin/water geometry; it does not carve an extra natural lake into the coarse terrain grid.

## Playable crop and outer scenery buffer

The default regional PNG/SVG and HTML views show the **49,152×49,152 travel envelope**, not the whole mesh. Water, cliffs and void within that envelope remain visible; actual walking depends on collision, water rules and terrain. The [separate authoring view](landscape/buffer.html) shows all **65,024×65,024 rendered terrain units**, with the travel boundary dashed. The line is a review overlay, not a proposed physical wall.

There are 96×96 terrain quads inside the travel envelope and 6,913 quads in the buffer. The buffer extends 8,192 units west/north and 7,680 east/south. The asymmetry comes from 128 stored samples forming 127 rendered quads; the final stored tile row/column must not be treated as another terrain strip.

`geography.py` samples adjoining original maps directly instead of clamping the four SW maps' edge cells:

| Side | Actual geography in the buffer |
| --- | --- |
| North → Alamar / Necropolis (NW) | Southern A2/B2 cells. Acid Pond continues across the travel boundary, narrows and closes. Surrounding dirt/rock/desert and a small scorched fringe follow the local source cells rather than a uniform Necropolis biome; lava lies farther north. |
| East → Sprite Forest / Southern Tower (SC) | Western C3/C4 cells. Continue river bends, dry ground and forest scenery. The eastbound trade road reaches X=32,256, the actual rendered terrain edge. |
| Northeast corner → Desert / Northern Highlands (NC) | Southwestern C2 desert. Corners use their diagonal neighbour rather than stretching a cardinal edge. |
| West / south | Outside the original world: continue its void rim. The general rule extends water when an original world-edge cell is water; these local outer shores terminate at void, so no sea is invented. |

Acid Pond is identified by its connected source water cells rather than latitude. Water-cell support vertices remain on their exact plane, including where river and void share a shoreline vertex; the void side can fall away. No lava cells occur within this particular buffer. All fluid quads are checked after pad placement and quantization.

Source forest cells receive temperate trees; dry/desert/rock cells receive sparse rocks. These placements are separate from the playable decoration inventory and have no interactions. Native visual radii, terrain slopes, water/void, road widths, travel approaches and existing scenery constrain them. Canopies may cross the travel line so it does not become a conspicuous clearing. No extra encounters, loot, residents or required objectives are placed in the apron.

All six surface maps should follow this same crop policy. The joined world overview concatenates only the playable squares. Native neighbour centres are offset by 49,152 units, so full meshes overlap: future neighbours must reuse world-aligned heights, materials and scenery throughout that overlap, not merely match the travel-edge height profile. Neighbouring native terrains have not been generated yet. This buffer provides their source context and height handoff; it does not certify an invisible cutoff. Check normal player-height views, flying views, final tile transitions and prop continuity during native blockout using the [regional transition calibration](../../REGIONAL_TRANSITION_CALIBRATION.md).

## Terrain-fit changes and crossings

Four gemsmith premises move 256 units landward to obtain complete dry support triangles. Justine's shelter moves 512 units north and remains outside the south gate. Original and adjusted centres are both recorded in `terrain.json` and `layout.json`; NPC identities and original source coordinates remain intact. No city building footprint moves.

Reger's source site is a tiny river islet. His newly authored hermitage uses a compact 448×384 foundation inside the earlier 832×640 planning reservation. Its larger reservation includes roof/shore clearance, not a solid foundation extending into the water.

The existing north–south river crossing reaches the southern meadow. A second, narrow **islet crossing** is reserved from Reger's east shore to that meadow's western bank. This is an explicit MM6–8 accessibility adaptation. Each entire reserved deck footprint is sampled against the generated terrain; the report gives a deck height with at least 64 units of soil clearance. Abutments, rail feet, both bank ramps and their final walking surfaces still need authored mesh and runtime checks. The report does not claim that two bank-centre samples prove a finished bridge.

## Foliage and scenery

`descriptorId` is the zero-based native descriptor index (the TXT table’s numbered column minus one), not the one-based printed row ID. Runtime export must resolve the canonical asset name against the active registry.

[decorations.json](landscape/decorations.json) records every accepted point, asset/reference identity, native-triangle Z, visual/collision radius, group, purpose and source binding where applicable. [decorations.csv](landscape/decorations.csv) provides the same placement coordinates in a compact form. Per-category `*_density_u8.png` files count placements in each 512-unit cell; they are density masks, not opacity masks or terrain tile IDs.

The palette uses the existing temperate trees `tree10`–`tree13`, selected low plants and small rocks already studied for Brackenford. [The palette sheet](landscape/sprite_palette.png) shows unchanged source art and native scale. Ground textures will still use the calibrated grass/dirt/road transition banks; this pass does not guess the final four-bank tile selectors.

The public orchard contains **all 55 original tree identities**: 30 ordinary, 13 reward-bearing and 12 food trees. These use the smaller native `tree13` crowns; they are not extra trees added on top of 55 cosmetic placeholders. Each tree's original source feature and effect is attached to its individual position. Keep those effects when binding the new world events.

The earlier sketch used blanket 320/512-unit foliage buffers. This pass explicitly replaces them with category-specific distances measured from the actual visual radius and route width; `placementRules` records the values and `initialSketchExclusion` retains the earlier proposal. Small flowers can approach house gardens more closely, while large tree crowns require considerably more room.

Placement uses full source-frame width multiplied by native scale as a conservative visual crown. Tree crowns may overlap by up to 28% of their summed radii; trunks and circulation remain separated. The generator excludes buildings, primary approaches, road widths, wall thickness, source water/void, interaction spaces, arrival clearings and encounter cores. The orchard walk remains clear. This is more conservative near buildings than checking only a tree's small collision cylinder.

The initial cosmetic budgets do not all fit: the temple strip accepts one of five large trees, the town edge five of fourteen, and one small infill pocket six of eight details. Those shortfalls are recorded rather than silently reducing clearances. The mandatory source orchard is complete. These retained quiet gaps are suitable for walking, sight lines and later eye-height review.

Nine original **non-event benches** now have individual outdoor placements, linked back to the MOB records. Six plain crate stacks occupy working/service courts. The other source bench-like objects attached to moved indoor NPC venues, interior beds, puzzle chests and already-open empty chest props remain in their premises inventories for room/mesh authoring; they are not duplicated as random loot. Small stock piles have no invented reward interaction.

Custom fountain/well/bench/crate records specify native terrain support ranges and platform/skirt levels for newly authored foundations. Native sprite pivots sit on the sampled terrain triangle. These foundation specifications are not a claim that custom meshes have already been produced.

## New interactions

All three additions below are requested adaptations. Original MM5 springs, chests, food, puzzle and tree effects remain separately owned.

| Addition | Placement and purpose | Draft rule |
| --- | --- | --- |
| Central HP fountain | Central bank/boarding court, with an unobstructed approach from the street; 512-unit basin reservation | Restore the selected living, non-eradicated character's HP to their current maximum, without reducing over-max HP. Unlimited uses. No spell points, condition cures or resurrection. |
| Secret charity well | Quiet back court between the diviners, workers and Nadia; ordinary player-facing hint **Well** | If carried party gold is below 200, add 200. Once per game day, party-wide. Bank gold is ignored; a failed eligibility check does not consume the day's reward. Thus 0→200, 199→399, and 200→no reward. |
| Six stat barrels | B1 forge stock area, B2 lodging yard, B3 mapmakers' side yard, B4 workers/diviners court, B5 temple side, B6 keeper's rear yard | Use native `dec03`: the initial seed selects one stat; drinking gives the selected character +2 permanent stat and empties that barrel. No repeated click reward. Proposed no refill for these six authored rewards. |

The barrel family and reward behavior were checked in [InteractiveDecorationRules.cpp](../../../game/gameplay/InteractiveDecorationRules.cpp) and the shared generated [Global.lua](../../../assets_dev/engine/events/Global.lua), events 268–275. These files were read only. New fountain/well state is specified under stable `mm5:sw/...` identities; no numeric event/QBit IDs were allocated. Their actual overlays and persistence tests belong to the playable-world implementation.

The well's once-per-day policy and fountain's full-HP policy are explicit design choices for this draft. Their balance can be adjusted without changing the scenery placement.

## Verification and rebuild

The landscape report checks all 16,384 quantized samples, all flattened supporting pad vertices, every road centreline at 64-unit spacing, primary frontage routes at 32-unit spacing, complete reserved bridge footprints and placement constraints. It also checks the 127×127 rendered domain, 96×96 playable crop, neighbouring source-map coverage, flat fluid quads and connected pond/river strips across north/east travel lines. Road/frontage longitudinal grades must stay at or below 0.5. It does not certify final road tile painting, transverse road banking, native geometry collision, AI, every secondary door approach, sprite-facing occlusion, bridge ramp meshes, event execution or saves.

Rebuild the whole review with:

```sh
python3 level_generation/projects/mm5_castleview_kalindra/build_review.py
```

`build_landscape.py` is the landscape stage. The full command rebuilds the source plan first, preserving provenance of terrain-driven changes instead of repeatedly shifting already-adjusted data. Review the new terrain and scenery from normal player height when the first native geometry is built.
