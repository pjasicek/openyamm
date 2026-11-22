# Xeen: dressing rules for props

The user's rule (2026-11-20), for every Xeen map, indoor and outdoor:

- No prop blocks a door, a doorway, a passage or the walking line between them.
- Barrels, sacks, crates and the like stand near the walls or in the corners.
- Barrels usually come in pairs; only storerooms hold clumps.
- References:
  - **Warlord's Fortress** (MM6 `assets_dev/worlds/mm6/maps/6d16.blv`, its storeroom) for clumps;
  - **Castle Harmondale** (MM7 `7d29.blv`) for the normal case.
- Outdoors, the same holds by a house: against its wall, never in front of its door.

## Measurements

Owner: A7. Measured 2026-11-20 from the two reference maps' BLV files (`oymap export`, then
`output/studio_cal/a7/dressing/measure.py`: each floor prop's room by the floor polygon under it, 2D distances from its
centre to the nearest solid wall at its height, to the nearest door face and to the nearest portal, groups of one kind
whose centres are within 200 of each other). Game units, centre of the prop. The scene files add no props to either.

| | Warlord's Fortress (MM6 `6d16`) | Castle Harmondale (MM7 `7d29`) |
|---|---|---|
| Floor props | 26 barrels (`bigbarel`, radius 30), 28 sacks (`bag01`, `bag_A`): **all in two storerooms** (1.1 and 1.6 M square units), nothing elsewhere | 32 barrels (`7dec32`, radius 52) and 1 cask in 9 rooms; 8 trash heaps, 5 bones, 6 rocks in the caves and cells; 9 goblets and a fruit bowl on tables |
| Rooms with floor props | 2 of 39 | 17 of 66 |
| Barrel to nearest wall | median 128, 90 % within 320, max 384 | median 103, 90 % within 240, max 531 |
| Sack to nearest wall | median 128, 90 % within 256, max 320 | — |
| Heaps, bones, rocks to wall | — | medians 320-480 (loose rubble on cave floors, not set against walls) |
| Barrel to nearest door face | min 181, median 582 | min 136, median 869 |
| Barrel to nearest portal (an open doorway) | min 543, median 1,448 | min 373, median 1,242 |
| Sacks to door / portal | min 143 / 916 | — |
| Rocks and heaps to portal | — | min 160 / 256 (cave rubble) |
| Barrel groups (centres within 200) | singles 2, pairs 3, threes 2, a four, an eight | singles 27, pairs 3 |
| Nearest other barrel | 128-143 for 22 of 26 (touching rows) | median 277 (163-491; a few alone, 869-1,536) |
| Barrels per room | 8 and 18 (the storerooms) | 2-7 (median 3) in rooms of 0.8-2.6 M |
| Sack groups | singles 3, pairs 1, threes 2, fours 3, a five | — |

Read:

- **Against the wall.** A barrel or sack stands with its centre about 100-130 from the wall (one radius plus a hand's
  breadth); nine in ten within 240 (a living room) or 320 (a storeroom's second row). Nothing of the kind stands in the
  middle of a room.
- **Pairs and rows outside storerooms.** In Harmondale a room holds two to seven barrels spread along its walls, the
  nearest neighbour usually 190-300 away: "pairs" there are two barrels a stride apart along one wall, seldom touching.
  Touching rows and clumps of 3-8 (barrels) and 3-5 (sacks) occur only in Warlord's storerooms, where they fill the
  room's sides and corners and leave its middle and its door free.
- **Doors and doorways stay clear.** No barrel or sack centre is nearer than 136 to a door face or 373 to an open
  doorway in either map (cave rubble excepted: 160-256 from a cave portal, off the walking line).

## The rule for the check (decision D-7.1, 2026-11-20)

The measurements above set the numbers; decider D-7 fixed how the check reads them. `oymap audit --world xeen` (A1)
applies them by default to world `xeen` maps only (D-7.2: shipped MM6-MM8 maps are untouched; their findings,
`output/xeen_a1/dressing_mm678.txt`, are the calibration record; `--dressing` checks any other map).

**Containers** are barrels, kegs, casks, sacks, bags, crates, boxes and buckets standing on the floor. A decoration
that is clicked or bound to an event is a **set piece**, whatever its picture. **Set pieces** also include trees,
statues, pillars, altars, hearths, fires, braziers, cauldrons and vats.

A **storeroom** is a room with 8 or more containers, or a room tagged `store: true` in rooms.yml (carried to the
audit by the installed map's studio sidecar; D-7.5).

| Check | Level | Rule |
|---|---|---|
| `dressing.door` | error | a container's centre within 192 of a door face (the leaf's plane), within the door's width plus 64 on each side |
| `dressing.doorway` | error | a container's centre within 320 in front of an open doorway (sideways within half its width plus 64); beside the opening, along its wall, only under 192 |
| `dressing.walking_line` | error | a container, a piece of furniture or rubble, bones or a heap that blocks movement, stands on the floor and has a radius of 24 or more, within its radius plus 64 of the walking line between two openings of its room (side-by-side openings count as one) |
| `dressing.walking_line` | error | any blocking floor prop that leaves less than 128 free on both sides of it |
| `dressing.walking_line` | warning | a set piece within its radius plus 64 of a walking line |
| `dressing.wall` | warning | a container's centre more than 240 from the nearest wall (320 in a storeroom) |
| `dressing.clump` | warning | 3 or more containers together outside a storeroom |

Both references stay flagged once each by these numbers (Warlord's Fortress's sack 143 from a door, Castle
Harmondale's barrel 215 from a doorway): the rule is a little stricter than the shipped maps, on purpose.

What a map lane does with the findings (D-7.3): **every error is fixed** (no exception for containers); a warning is
fixed, or kept with one line under "Dressing exceptions" in the map's NOTES.md saying what the prop is and why it
stands there. Outside storerooms, keep singles and pairs along the walls, 2-7 containers per room.

## Outdoors (decision D-7.6, from D-14, 2026-11-20)

Outdoors the same classes are judged by the houses (A1's extension of D-7.1, confirmed by decider D-14). A **house
door** is a model's faces whose event enters a house; it counts as a doorway. A prop is **by a house** when it stands
within 512 of a model's wall. There are no storerooms outdoors.

| Check | Level | Rule |
|---|---|---|
| `dressing.door` | error | a container's centre within 320 in front of a house door, or within 192 beside it |
| `dressing.door` | error | any other floor prop of radius 24 or more within its radius plus 128 in front of a house door |
| `dressing.door` | warning | a set piece within its radius plus 128 in front of a house door |
| `dressing.wall` | warning | a container by a house more than 240 from the model's wall |
| `dressing.walking_line` | error | the indoor rule on the line from 64 in front of one house door to 64 in front of another, for doors up to 2,048 apart with no wall between; a prop standing against a model wall (within its radius plus 64 of it) is skipped, but the 128 free-gap error still applies to it |
| `dressing.road` | error | a floor prop of radius 24 or more, not against a wall, whose body comes within 64 of a road's middle line |
| `dressing.clump` | warning | 3 or more containers with centres within 200 of each other |
| `dressing.outdoor` | info | counts the props, doors and lines checked |

Classes added by D-14 (indoors and outdoors):

- **Containers** also include firewood and log piles (hint `wood`; words firewood, woodpile, log pile).
- **Set pieces** also include stalls, rocks and boulders.
- Hay stays "other" (neither container nor set piece).

The same handling as D-7.3: every error fixed, a warning fixed or kept with one line under "Dressing exceptions" in the
map's NOTES.md.

## Check

Every map lane runs `oymap audit <installed map> --world xeen --assets <root> --reach --solve` before reporting a map
done (ROADMAP §5.1); the audit reads the installed map by its stem from the root it is given. Outdoors the audit
applies D-7.6 above (A1's `core/Audit` constants and patterns; `openyamm-studio/README.md`, "audit").

## Support under props and the chests (F3, F6; 2026-11-21)

The user's play feedback (`reviews/USER_FEEDBACK_20261121.md` F3, F6): a barrel stood on a terrace's lip, half over
the drop; chests looked unlike MM8's and one stood in a cave mouth with a place's name. For every Xeen map:

- **Level ground.** A container stands with its whole footprint on level ground or floor: no part more than 24 over
  it, no drop deeper than 64 within 48 of it (a terrace's lip, a platform's or bridge's side, a pit's rim, a cliff).
  Other floor props the same indoors (things on tables only past a 128 drop); outdoors a bone pile or skull pole may
  lie on a hillside (48 over, a 96 drop). Trees, plants and natural rocks are not judged; hung decorations neither.
- **Chests are the shipped chests.** MM7's or MM8's chest (19 faces of the `7gt002` / `gt002` pieces), MM6's chest
  kinds (`ch1` to `ch5`, `ch001` to `ch006`), a crate, or furniture that opens (a cabinet, a sarcophagus). Indoors a
  chest without a `surface` is its world's plain chest; never a box of a wall texture. Outdoors the studio's chest is
  the shipped one once A1's request F6-R1 lands (until then 9 faces with a tiled plank picture).
- **Chests stay out of openings**: not within 320 in front of (192 beside) a house door, an exit, a door or a teleport,
  and outdoors not on a cave mouth's line (its dark door face's opening reaches 256 further out). A chest's hover
  title says what opens ("The orcs' stash"), never a place ("The orcs' den").

Check: `python3 tools/xeen/check_props_support.py [--maps xeen_x1,...] [--file <built map> --scene <its scene>]`
(`support.overhang`, `support.edge`, `support.floating`, `chest.look`, `chest.entrance`, `chest.title`; `--regrounded`
judges outdoor props as the studio stands them once A1's F6-R2 lands). Every error is fixed before a map is reported
done; it moves into `oymap audit` with A1's F6-R4.
