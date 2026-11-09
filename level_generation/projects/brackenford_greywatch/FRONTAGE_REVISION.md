# Brackenford frontage and tile correction

This revision follows the driver's screenshots `test_img/1222.png` through `1230.png`. The accepted house artwork and
irregular town composition remain the basis. [Reusable calibration](../../FRONTAGE_AND_TILE_CALIBRATION.md) and the
[review checklist](../../REVIEW_CHECKLIST.md) now make frontage, bitmap seams and local infill explicit gates.

## Changes by finding

| Finding | Authored correction |
| --- | --- |
| 1222: ordinary houses stand too far from the street | Move frontages toward the shared streets; compare actual active door positions against native road cells. |
| 1223: wrong grass/dirt edges and corners | Correct the one-corner/three-corner mapping in all three transition banks; reserve dirt collars between roads/water and rock. |
| 1224: western diagonal frontage too distant | Move the two rotated houses toward the diagonal street; measure clearance in their rotated local coordinates. |
| 1225–1226: northern door/spur mismatch | Move the northern homes to direct street frontage and remove their individual paved spurs. |
| 1227: eastern houses need no little access roads | Move stables, training court, alchemist and northeastern homes close to the existing shared road. |
| 1228: inn door offset from its lane | Move the inn to the snapped lane center; also align the manor and rotated temple with their final approach segments. |
| 1229: empty court edges | Add five inhabited buildings around the fountain court and well lane, with varied compact/long footprints and real separate doors. |
| 1230: sparse town interiors | Add twelve authored infill garden/verge groups, including plants, occasional trees and rocks, with road/door/landmark clearance. |

Ordinary houses have `approach_kind: street_frontage`; only the manor, temple and recessed inn have dedicated lanes.
The conjoined weapon/armor shops move as one assembly. Native doors remain 128×256 with their calibrated facade art.

The five new homes reuse Elsie Apple, Jillian Applebee, Chadric Benson, Benjamin Greenstorm and Julian Greensward,
with audited existing message-only MM8 topics. House IDs 12024–12028, NPC IDs 12016–12020 and events 124–128 append
to the existing allocations. Existing logical event/house/NPC identities remain stable; later native BModel indices
are regenerated from semantic names. See [TOWN_REUSE.md](TOWN_REUSE.md) for the full binding inventory.

## Calibration evidence

The before/after source/native snapshot is preserved in `review/frontage_revision/before/`.
[Frontage report](review/frontage_revision/frontage_check.json) records each measured entrance, the actual corner
material classification and the transformed lane alignment. Distances are nearest **road-cell-center** proxies,
not exact painted-edge setbacks. Reference entries use the catalogue's active house faces, excluding label-only walls.

| Population / method | P25 / median / P75 native units |
| --- | --- |
| Ravenshore: 61 active house entrances to nearest road tile center | 429 / 516 / 955 |
| Previous Brackenford: ordinary entrances to shared streets, excluding individual spurs | 570 / 688 / 807 |
| Revised Brackenford: ordinary entrances to shared streets | 319 / 371 / 408 |

Including the previous automatic spurs would hide the original large setback: the previous all-entrance median to
*any* road cell was only 410. The revised closer frontage is intentional for this town, following the driver's feedback;
Ravenshore's full-map distribution includes varied districts and remote/raised sites and is not a universal target.

The actual bitmap-corner adjacency check finds **3,258 mismatched adjoining edges before, zero after**. It covers
shared corner materials across the 127×127 rendered terrain cells, not every painted pixel or road connectivity.
The three dedicated-lane lateral errors are zero after integer native rounding. Ordinary road/house footprint overlaps
are rejected in local rotated coordinates. [Transition contact sheet](review/frontage_revision/transition_artwork.png)
shows the source artwork independently of the generator's selector.

[Textured plan](review/frontage_revision/frontage_plan.png) shows house footprints, cyan door normals, landmarks and
accepted decoration positions. The revised source has 29 houses in 28 structures, 87 BModels, 3,748 faces and 325 road
cells. Decorations: 285 trees, 336 plants, 96 rocks and 12 props; 729 total versus 564 before. Three requested extra trees
were rejected in crowded infill groups, deliberately preserving their clearances. Population remains 9 guards,
20 villagers and 14 remote ogres; four chests, five loose items and four stat barrels retain their behavior.

## Build and review

Run `check_frontage.py --source` before a native build. After Blender MCP authoring, regenerate town registrations,
build the native ODM, then run `check_frontage.py` and `check_facade_revision.py --review-directory frontage_revision`.
`review_frontage_blender.py` reimports the written native map once for its automap and three focused views. The packed
source is verified with `verify_blend.py`. Short gameplay captures review appearance; no broad outdoor scenario suite.

Native [overview](review/brackenford_native_frontage_overview.png), [court](review/brackenford_native_frontage_court.png)
and [west street](review/brackenford_native_frontage_west.png) were opened and inspected. The court now has buildings
along its edges and usable open space at the fountain; the west houses face a continuous diagonal strip without spurs.
The [game street view](review/gameplay/frontage_north.png) shows the real doorstep near the stones at party eye height.
Blender views use neutral inspection lighting, not the game's lighting.

The density readback now includes all appended houses: nearest physical-envelope gap median 1,088 → 735 units,
coverage 15.5% → 19.1%, and 28 assemblies. The manor's large plot remains intentional. See
[measurements](review/frontage_revision/measurements.json). This complements frontage checks rather than replacing them.

The packed Blender source reopens independently with 871 objects, 729 native-decoration previews and all file images
packed. Native [quick checks](review/frontage_revision/quick_check.json) pass in under a second; the independent bitmap
and plan check takes about one second. Existing indoor content remains unchanged.

Play the fresh God snapshot with:

```sh
/tmp/openyamm-brackenford-playtest-frontage/play.sh outdoor
```

Choose **Load Game → Scenario**. Previous snapshots and their saves remain frozen. `indoor` starts the existing vault.
The package is `dist/brackenford_greywatch_content.zip`; current checksums and starting-save verification are recorded
in `progress.json` and `review/playtest_snapshot.json`.

The [game court view](review/gameplay/frontage_court.png) was also inspected: flowers/rocks and trees now occupy the
spaces between its houses, the fountain is reachable and its existing interaction hint resolves. Both fresh God starts
reload successfully using the copied executable. Blender MCP is still connected with the current authoring scene active.
