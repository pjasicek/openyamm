# Complete MM5 outdoor layout: 16 maps

The previous world terrain overview covered **6 of the 16 proposed outdoor maps**: the surface. The other ten are
**six Skyroad regions and four elemental planes**. They are included in the project scope; they are not ten further
surface wilderness regions.

Open the [complete visual index](other_outdoors.html), [all-16 overview](all_outdoors.png),
[sky map](sky_map.png), [elemental plane sheet](elemental_planes.png) or
[complete machine-readable manifest](outdoor_manifest.json).

**Visual revision:** the default sky/plane previews are now
[textured minimap concepts](MINIMAP_CONCEPTS.md), using the user's MM8 Plane of Air / MM7 Celeste references.
The original source schematics are retained separately as `sky_source_map.png` and `elemental_source_planes.png`.

| Layer | Proposed maps | Original outdoor logical maps | Geographic arrangement |
| --- | ---:| ---:| --- |
| Surface | 6 | 24 | The existing 3 × 2 regional world map |
| Skyroads | 6 | 24 | A second 3 × 2 layer aligned with the surface |
| Elemental planes | 4 | 4 | Four independent destinations reached from the sky layer |
| **Total** | **16** | **52** | Every original MM5 outdoor logical map assigned once |

## The six Skyroad regions

| Sky ODM | Source squares / map IDs | Principal access and landmarks |
| --- | --- | --- |
| Sky NW | A1, A2, B1, B2 / 89, 90, 93, 94 | Alamar upper entrance; Fire gateway |
| Sky NC | C1, C2, D1, D2 / 97, 98, 101, 102 | Olympus; Northern Tower; Great Pyramid summit |
| Sky NE | E1, E2, F1, F2 / 105, 106, 109, 110 | Blackfang upper entrance; Air gateway |
| Sky SW | A3, A4, B3, B4 / 91, 92, 95, 96 | Western Tower; Ellinger; Kalindra; Dark Grove rope; Water gateway |
| Sky SC | C3, C4, D3, D4 / 99, 100, 103, 104 | Southern Tower and sky routes |
| Sky SE | E3, E4, F3, F4 / 107, 108, 111, 112 | Eastern Tower; merchants; boatman; Earth gateway |

These should be composed as exposed elevated paths, cloud areas, platforms and special settlements. **Olympus belongs
in Sky NC.** Sparse occupied areas are expected; do not fill the rest with ordinary ground or houses. The revised
concept shows proposed platforms, architecture and cloud depth. The retained source sheet shows skyroad/cloud/open-sky
classes and interaction markers, not original object sprites or a full movement model.

Each sky region is geographically paired with its surface region. Access goes through specific towers/castles, the
rope and other scripted transport. Falling generally leads down toward the corresponding surface geography, but
special scripts and arrival/damage rules must be handled separately. Upper and ground entrances to a castle are
different access routes and may have different quest reachability.

Sharing a geographic grid does not imply seven ordinary road links in the sky. Sky boundary connectivity, cloud
traversal, flight, safe landing and fall behavior need the dedicated sky prototype and route audit. The surface's
validated foot-travel graph must not be copied onto this layer.

## The four elemental planes

| ODM | Source ID | Gateway in source sky | Starting presentation |
| --- | ---:| --- | --- |
| Fire | 25 | Sky A1 (2,13), Sky NW | Lava, volcanic material, heat and elemental landmarks |
| Air | 26 | Sky F1 (13,13), Sky NE | Clouds, exposed platforms and air-themed landmarks |
| Earth | 27 | Sky F4 (13,2), Sky SE | Dirt/rock, mineral formations and earth-themed landmarks |
| Water | 28 | Sky A4 (2,2), Sky SW | Water and elemental landmarks; traversal design is essential |

Each original plane is only **16 × 16 cells**, with a nearly uniform surface type. Their source schematics therefore
look much simpler than the surface world. They still have NPC/event/encounter content; uniform terrain does not imply
an empty gameplay map. The revised minimap concepts add proposed landforms and landmark settings; exact geometry,
encounters and event bindings still require detailed design.

Gateway and return destinations are directed records, not assumed symmetric links. The supplied Water plane's explicit
exit event at (13,13) targets **Sky A1** (map 89), although its entry is at **Sky A4** (map 92), and the runtime's general
Water-plane fall rule also targets A4. The manifest preserves the explicit source event; this discrepancy needs a
gameplay audit before authoring returns. Do not silently replace it with an inferred A4 return. The same distinction
between explicit events and general fall rules applies to the other planes.

Source evidence: the extracted DAT/EVT inventory, and the reference runtime's
[fall behavior](https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/interface.cpp) and
[explicit fall-to-map event](https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/scripts.cpp).

## Dimensions and scope

All 16 can use the standard ODM terrain storage dimensions, but **they should not all contain the same amount of
walkable land or content**. The six surface maps have the common provisional travel square documented in the surface
layout. Sky maps need geographic alignment and substantial empty space. Planes can use compact occupied areas inside
the native footprint; there is no requirement to stretch each original 16 × 16 plane into a full-density regional map.

The first implementation remains **SW Castleview / Kalindra**, with a small sky-route fixture as a separate technical
experiment. The ten special maps remain in the planned total. No native sky/plane ODMs were generated here.

## Reproduction

After regenerating the surface study if needed, run:

```sh
python3 level_generation/projects/mm5_world_feasibility/world_layout/build_other_outdoors.py
```

The script creates the ten source previews, concept viewport previews, overview sheets, HTML index and manifest.
It requires the reviewed raster concepts described in `MINIMAP_CONCEPTS.md`. It asserts that all 52 original outdoor
logical maps are covered exactly once by the 16 proposed maps.
