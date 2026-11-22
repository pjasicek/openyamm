# Light fixtures: where they hang

The user (2026-11-20): "make a check for the dungeons to make sure that lights are actually hanging where they should
(e.g. suspended on ceilings are suspended on ceiling not on floor, lamps are on walls and not in mid-doorways or in
the air etc.)". `oymap audit` runs the check on every Xeen indoor map (others with `--lights`; `--lights-measure`
prints each fixture's numbers). Code: `openyamm-studio/core/LightAudit.cpp`; data:
`assets_dev/engine/models/light_fixtures.yml` (a world adds `worlds/<world>/models/light_fixtures.yml`).

## Mounts

Each decoration is a light fixture of one mount, or none:

| Mount | Examples | Where it comes from |
| --- | --- | --- |
| ceiling | chandeliers, MM6's chained brazier (`brazir2f`, `brzier00`) | the fixture list; a binding with `swing` and a lamp hint; hint "chandelier", "censer" |
| wall | torches, sconces, torch brackets | a binding with `mount: wall`; hint "torch", "sconce" |
| floor | braziers on feet, candles, campfires, beacons, cauldrons, magic pedestals | hint "brazier", "candle", "fire", "beacon"; the list |
| free | invisible lights, origin matter, glows | the list; hint "glow", "wisp" |
| none | bowls, everything without a fire | the list, or no word |

A decoration that gives light (LightRadius) and has no mount is reported as `lights.unclassified` (info): add it to the
list.

## Checks (numbers measured on the shipped MM6–MM8 dungeons)

Measured over 161 shipped BLVs: 7,648 fixtures, 9,128 map lights, 7,467 decoration lights
(`output/xeen_a1/lights_mm678.txt` lists every finding there; the shipped maps stay as they are, D-7.2).

| Code | Severity | Rule | Shipped |
| --- | --- | --- | --- |
| `lights.in_solid` | error (warning 16–32) | a fixture's middle lies more than 16 behind the faces round it and in no sector | 19 + 2 |
| `lights.ceiling_on_floor` | error | a hung fixture's foot within 8 of the floor and its top more than 160 under the ceiling (or none) | 0 |
| `lights.ceiling_gap` | warning (error past 160 or no ceiling) | a hung fixture's top more than 48 under the ceiling, or more than 48 into it | 40 + 15 |
| `lights.in_doorway` | error | a hung fixture in an opening's slab (24 either side of the portal) with its foot under 224 over the opening's floor; a wall fixture inside the slab more than 32 in from the jambs; a standing one in the slab | 0 |
| `lights.wall_missing` | error | a wall fixture with no wall within 64 of its middle (the game's `findIndoorDecorationWall`: it draws the free-standing model, in the air) | 65 |
| `lights.on_moving_face` | error | a wall fixture's wall is a face a door moves whole | 0 |
| `lights.wall_height` | warning | a wall fixture's foot under 16 over the floor (it stands on the floor; torches over pits hang thousands up, so no upper bound) | 51 |
| `lights.floating` | error over 32, warning over 8 | a standing fixture over the floor, unless it rests on a decoration (its foot within 24 of the other's top, within 32 of its middle) or hangs with its top at the ceiling | 1 |
| `lights.sunk` | warning | a standing fixture more than 8 into the floor | 1 |
| `lights.light_in_solid` | error over 32, warning 16–32 | a map light, or a decoration's light (at half its row's height), inside the rock and in no sector | 33 + 2 |

Measured distances: wall torches stand 7–17 from their wall (5th to 95th percentile, 3,385 MM6 torches), their foot
80–256 over the floor; 228 shipped map lights lie within 4 behind a wall and pass. A studio map's `lights[].height`
is over the room's floor, not absolute (XD-26's lights at 2,264–3,636 lie 850–1,380 above their rooms).
