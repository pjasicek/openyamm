# River and Reger-islet foot crossings

Both crossings are explicit MM6–8 accessibility adaptations recorded in the
[landscape contract](../LANDSCAPE.md). The river, islet and terrain remain at their planned locations and heights.
Geometry is original: timber decks on paired piles and longitudinal beams, two-height rails, and masonry bank ramps.
No donor bridge meshes are copied. Existing Alvar timber and Garrote masonry artwork remain at native resolution.

| Crossing | Deck | Bank connections |
| --- | --- | --- |
| South meadow | 512 wide, 4096 long, top Z 384; south to north | 512-unit ramps at both ends. Endpoint heights vary across the width to meet the existing terrain. |
| Reger islet | 320 wide, 3840 long, top Z 544; west to east | Short 192-unit western ramp rises to the islet at Z 608, ending 32 units before the corrected hermitage door. Eastern ramp runs 512 units to the meadow. |

The narrower bridge retains 256 units between its posts. Neither bank edge has a blocking rail across it.
Decks are continuous walking surfaces; small physical plank gaps are unnecessary. Bay lengths are 512 and 480 units
respectively. Piles reach below the actual ground under their entire footprints. Deck-mounted rail posts meet the
deck top; bank posts extend into the ground. Crossing bridges is ordinary movement, with no teleport or event shortcut.

## Sources and checks

[prepare_bridges.py](../prepare_bridges.py) derives [bridge_layout.json](bridge_layout.json) from the landscape
reservations and actual quantized heightfield. It checks each proposed surface triangle at native grid vertices
and intersections with grid/diagonal edges. These samples cover extrema of the piecewise-linear height difference.
Both complete decks clear terrain by at least 64/68 units; all ramp bank edges meet terrain without raising the islet.

[author_bridges.py](../author_bridges.py), called by the main Blender author, creates the meshes and records checked
face identities. [review_bridges.py](../review_bridges.py) reads those faces from the exported ODM and checks walking
surfaces, beam undersides and buried pile/abutment/rail feet. The native builder runs it after the environment audit.
Source OBJ checks currently cover [112 contacts](../review/bridges_v3/source_support.json).

To repeat Blender views, use `REVIEW_IDS: ['river_crossing', 'reger_crossing']`, `REVIEW_TERRAIN: True`, and a new
`REVIEW_VERSION` with the normal [rebuild procedure](../REBUILD.md). The terrain has neutral material in these views;
it includes the actual heights but does not depict native water or foliage.

## Visual iterations and acceptance limits

Actually inspected the first overview, ramp and support views. They exposed dark seams from coplanar rail/post faces.
Rails now sit inside wider posts; deck posts stop at the deck top and crossbeam ends tuck into the supporting piles.
The repeated [support view](../review/bridges_v2/river_crossing_supports.png) and
[eastern landing](../review/bridges_v2/reger_crossing_end_landing.png) show the dark patches corrected.
Those views also exposed inconsistent ramp texture scale: the native wood bitmap is 32×64, not 128×128.
The third revision uses the actual bitmap dimensions and one continuous UV origin across deck bays and ramps.
Inspected the repeated [southern ramp](../review/bridges_v3/river_crossing_start_landing.png) and
[eastern islet landing](../review/bridges_v3/reger_crossing_end_landing.png): the abrupt change in texel scale is gone.

Native build `1845ae6db8cb69b167c5bc67a9dc9ad31d45881c3b159ea0d953cb6b76aad5d9` contains the two bridges;
all [112 exported contact checks](../review/bridges_v3/native_support.json) pass. Actually inspected the native
[northbound river midspan](../review/gameplay/mm5_river_north_walk_v2_middle.png),
[southbound river landing](../review/gameplay/mm5_river_south_walk_v2_far_bank.png),
[islet-bound midspan](../review/gameplay/mm5_reger_west_walk_v2_middle.png),
[Reger door arrival](../review/gameplay/mm5_reger_west_walk_v2_far_bank.png), and
[eastbound midspan](../review/gameplay/mm5_reger_east_walk_v2_middle.png).
All four runs traverse by ordinary forward movement and restore their landing views after F9/F10.
The [capture/save report](../review/bridges_v3/native_traversal.json) records the reviewed middle, landing and restored
images for each direction, with native/binary hashes and decoded saves. Map, gold, food, health and inventories
remain unchanged. This establishes central walking access in both directions, including the islet doorway;
it is not exhaustive collision coverage of every rail face.

The first action holds were too long and the southbound party continued into the separate islet bridge's side rail
after crossing the river. Shorter v2 holds give useful landing views. Two-second reload waits caught loading screens;
ten-second waits produced the reviewed restored game views. Water and bank ramps are visible in the native captures.
The meadow foreground and exposed western world rim remain unfinished regional scenery, outside this local acceptance.
