# Street frontage, terrain seams and occupied town space

The driver accepted the corrected [Brackenford revision](projects/brackenford_greywatch/FRONTAGE_REVISION.md).
Use [Accepted outdoor calibration](OUTDOOR_CALIBRATION.md) to apply these findings alongside architecture, density,
terrain and biome decisions when starting a new map.

Feedback [1222–1230](../test_img/1222.png) adds three separate checks after scale, house variety and settlement density.
A plausible house and a connected road graph can still make a poor street. Use this alongside
[sketch composition](SKETCH_LAYOUT_CALIBRATION.md), [density](SETTLEMENT_DENSITY.md), and the
[Ravenshore building catalogue](catalogues/mm8_ravenshore/README.md).

## Place the actual entrance relative to the actual road

Native terrain cell centers are `x=(column-64)*512+256`, `y=(64-row)*512-256`. An intended road at a multiple of 512
can move sideways by 256 when snapped to this grid. Resolve the road cells first, then position the building using its
actual transformed door center, outward normal, local footprint and any offset door. A building center is not its door.
For a shared block, move the entire assembly together and retain separate door events.

Declare `street_frontage` or `dedicated_lane` for each building. Ordinary homes can stand close to a shared street with
a short unpaved approach; do not automatically pave a spur to every door. Reserve dedicated approaches for sites such
as a raised manor, temple or recessed inn. Where a lane terminates at a building, align the door with its final segment;
move the house when the native terrain grid cannot place the road accurately. Check diagonal streets in the building's
rotated coordinates; axis-aligned exclusion boxes overestimate their corners.

The Brackenford correction targets roughly 280–430 units from ordinary doors to the street centerline, leaving a narrow
verge outside the painted stones. This is a project choice from the driver's feedback, not a universal MM8 constant.
Measure reference active entrance faces through their event/house mapping; most MM8 door textures do not contain the
word `door`. Label-only wall events and roofs must not enter the measurement. Record whether a distance uses cell
centers, continuous centerlines, full tile bounds or the painted bitmap edge: these are different quantities.

## Read the transition artwork, not only its filename

The MM8 grass/dirt, water/dirt and rock/dirt banks share a variant pattern. With bits NW=1, NE=2, SW=4, SE=8 indicating
**dirt**, the correct mapping is:

| Dirt corner mask | Variant offset | Meaning |
| --- | --- | --- |
| 1, 2, 4, 8 | 22, 20, 23, 21 | One dirt corner: XNW, XNE, XSW, XSE |
| 3, 5, 10, 12 | 18, 17, 16, 19 | Dirt north, west, east, south |
| 7, 11, 13, 14 | 14, 12, 15, 13 | Three dirt corners: NW, NE, SW, SE |
| 0 | 0 | Base grass/water/rock |
| 15 | Direct dirt tile | All dirt |

The original Brackenford selector confused one-corner and three-corner artwork. Texture keys resolved successfully,
but the corners could not meet. Inspect a contact sheet and classify the actual bitmap corners independently of the
generator's dictionary. Compare both endpoints of every adjoining edge in the written native tile array. Water's base
tile is animated; the keyed magenta shore overlay is only part of its rendered appearance.

Masks 6 and 9 are saddles with no matching tile in these banks; resolve them in the material mask before selection.
Reserve dirt between water and rock, and between stone roads and rock: these banks have no direct rock/water or
rock/road transition. Fix the authoritative material masks instead of patching random individual output tiles. Retain
paired diagonal road halves and inspect their painted joins separately; corner-material agreement alone does not prove
that a painted road strip is connected. Do not infer arbitrary tile rotation support from Blender UV controls.

## Fill the intended gaps, preserve useful openings

Treat the driver's marked gaps as specific sites. Frame a fountain court with varied small homes or a longer residence,
keeping enough clear space to approach the fountain. Use existing MM8 inhabitants and topic handlers, with new scoped
house/NPC IDs and real active door faces. Do not use unbound fake doors to raise a house count.

Add authored vegetation groups inside the settlement as well as outside its perimeter: small gardens behind houses,
a few trees between buildings, flowers along a verge, and rocks near a slope. Count **accepted** placements per group;
clearance rejection can leave an intended district empty even when global decoration totals look high. Preserve roads,
door approaches, well/fountain footprints, arrivals and actor standing space. Review sprite size in a game view, not
just point markers on a plan. A major court should remain a usable opening rather than becoming a dense woodland.

## Fast acceptance loop

1. Draw the textured native-grid plan with footprints, door normals, landmarks and accepted decorations.
2. Check ordinary setbacks, dedicated-lane lateral error, and rotated footprint/road clearance.
3. Classify actual tile corners and check shared material endpoints; visually inspect diagonal road joins and banks.
4. Build once the source plan passes; parse the native file and verify arrays and active face bindings.
5. Inspect a native oblique view plus brief game views of the changed street/court. Iterate on visible failures.
6. Refresh the automap and documentation; when delivering a playable snapshot, use the requested test party (God for
   this project). Preserve earlier snapshots and saves.

No every-door scenarios, shop transactions, travel loops or broad gameplay suite are needed for this content revision.
The project [check_frontage.py](projects/brackenford_greywatch/check_frontage.py) records reference distances, native
corner-material seams, lane alignment and a textured plan; [check_facade_revision.py](projects/brackenford_greywatch/check_facade_revision.py)
checks the existing event/registry and placement contract.
