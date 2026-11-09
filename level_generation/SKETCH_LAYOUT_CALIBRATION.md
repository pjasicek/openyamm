# From a driver's sketch to a coherent settlement

The [density revision](projects/brackenford_greywatch/DENSITY_REVISION.md) improved spacing but still produced parallel
streets around rectangular blocks. The driver accepted the closer houses and then supplied
[a contrasting sketch](../test_img/1221.png), marking roads, houses, wells/fountain, raised terrain and stat barrels.
**A good density number does not establish a good composition.** Keep the spacing lesson, and plan the shape separately.

## Read relationships before coordinates

Record the sketch's major relationships: a larger residence above town with its own approach; a smaller temple hill
inside the main loop; a street slanting around one side; a second, smaller residential loop; a short service lane;
small wells versus a larger fountain court; and four rewards beside important sites. Background color is not a terrain
material instruction. A pink mark represents an occupied site, not necessarily one BModel, service, or exact house count.
Resolve scale against the existing kit before converting pixels to game coordinates.

Use an explicit road graph and landmark/plateau anchors in the plan. Do not turn every edge into a full map-width road,
copy equal setbacks to every house, or place all roads before considering the frontages they serve. Use unequal block
lengths, small spurs, diagonal edges and landmark approaches where drawn. Retain the native map's more open countryside.
Compare a top-down render to the sketch before paying for a native build.

## Native diagonal roads

The terrain stays on its 512-unit grid. Inspect the actual bitmap and neighboring native tile IDs before assuming
that a road must turn at 90 degrees. MM8's road bank at table index 414 includes paired diagonal halves:
`drsrne1`/`drsrne2` (raw 217/218), and `drsrnw1`/`drsrnw2` (219/220), plus bend and junction variants.
Two half tiles form a continuous slanted strip across the terrain; they are not interchangeable corner tiles.
Ravenshore has concrete examples around raw grid row/column 21/76 and 10/59. Read adjacency and match the entry/exit
edges at each end. Recompute dirt/grass transitions and inspect the native result. Merely using a staircase path through
orthogonal road textures does not produce the same appearance.

## Raised sites and architectural hierarchy

Give each raised building an explicit pad height and a graded approach. A road texture over an abrupt plateau shoulder
is not a finished ascent. Preserve the flat ground immediately around the door, and inspect the approach at party eye
height. Rotate the temple toward its access spur instead of aligning it blindly with the map axes. Rotate collision,
road/prop exclusion and door-direction calculations with the building too; do not round sine/cosine to cardinal values.
Native vertex rounding can make a rotated 128-unit door about one unit different in its measured diagonal width.

For an important person's residence, increase the mass and hierarchy without enlarging the door: a projecting hall,
recessed lower wings, towers and separate roofs. Erathia's town hall and multipart castle supply massing references;
keep the target world's texture family coherent. Recessed wings require matching foundation footprints. An oversized
rectangular foundation can leave exposed dark strips in front of those wings; inspect native reimport close-ups.
Reuse a named native resident and suitable topics when requested rather than inventing a new character implicitly.

## Functional landmarks with quick checks

Distinguish small wells, a fountain, and stat barrels in the semantic plan. A multipart native fountain must keep all
parts in one shared coordinate frame; recentering each half separately breaks it. Give new effects local handlers and
saved state, with explicit target character, amount, use cap and reset rule. Ordinary inherited barrel behavior should
use native decoration identity and existing interaction state. Descriptor names are resolved by the runtime; raw
reference IDs and merged TXT indices are not interchangeable.

Brackenford's chosen interpretation is 15 HP plus 15 mana for the selected character, 40 shared uses per game day.
Four normal MM8 stat barrels grant +2 permanent stats and become empty through the existing system. A tiny Lua check
covers the new fountain counter and day boundary. Static checks cover native prop/face bindings, footprints and barrel
anchors. Do not expand this content iteration into every-service, travel, refill or combat scenario coverage.

Inspect a native overview, a raised-site close-up and a relevant game view, then rebuild the automap and distribute
fresh starts. [Completed sketch implementation](projects/brackenford_greywatch/SKETCH_REVISION.md).

Latest frontage/transition feedback (1222–1230): follow [FRONTAGE_AND_TILE_CALIBRATION.md](FRONTAGE_AND_TILE_CALIBRATION.md)
for road snapping, actual-door setbacks, dedicated-lane alignment, bitmap corner selection and occupied courtyard/garden sites.
