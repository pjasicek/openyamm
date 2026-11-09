# Landscape detail, landmark settings and bridge contact

Use [the all-outdoor decoration calibration](OUTDOOR_DECORATION_CALIBRATION.md) for the complete MM6–MM8
vocabulary and distribution: 42 map palettes, spatial context, subregion contrasts and deliberate open-space roles.
The district-specific measurements below remain useful; do not replace them with whole-map density targets.

Follow-up to [wilderness calibration](WILDERNESS_CALIBRATION.md), based on the driver's `test_img/1236.png`–`1242.png`.
Read this before accepting a bridge or deciding that an outdoor map is sufficiently populated from global counts.
The changes and final captures are in [Brackenford's landscape revision](projects/brackenford_greywatch/LANDSCAPE_REVISION.md).

## Bridge geometry and terrain must be inspected together

The previous bridge passed a deck floor/ceiling check but still failed visually: bank elevations reached **960** under
parts of a deck at **640**. Testing two bank anchor points did not check the terrain between them. In
[1236](../test_img/1236.png), soil buries the ends, pieces of the deck and posts. This was a missed geometric defect,
not an intended low bridge style.

Author the span, water level, bank landings and graded approaches as one composition. Sample the complete deck width
and length against the **quantized native terrain triangles**, including rail feet and abutment edges. Make the visible
deck top clear of soil; buried foundation bottoms are acceptable, buried rail/deck surfaces are not. Join each bank to
the walking surface with a flat landing, ramp or deliberately small step. Check the next road segment as well: a clear
span does not compensate for a cliff immediately after its end.

Keep adjacent stone/timber tops nonoverlapping; coplanar faces can produce visible flicker or black patches.
Keep the upward floor/underside ceiling checks, but add a cross-section at the center and both sides, an oblique
side view, and a player-height view along the bridge. Brackenford now uses a deck at **1,152**, at least **64 units**
above terrain throughout its span, with stone landings and graded approaches. The terrain-water channel stays at 256.
See [before/after profiles](projects/brackenford_greywatch/review/landscape_revision/bridge_profiles.png).
These dimensions fit this crossing; do not copy the elevation to unrelated maps.

## Ground detail is separate from decoration sprites

The marks in [1238](../test_img/1238.png) combine embedded texture stones with separate boulder sprites. A landscape
needs both broad material shapes and occasional close-range detail. Repeating one clean grass/dirt bitmap everywhere
loses this layer even if its edge transitions are correct.

This checkout's MM8 terrain table resolves:

| Raw terrain tile | Actual texture | Role |
| --- | --- | --- |
| 1 | `DIRTtyl` | Plain dirt |
| 2 | `DIRT1` | Dirt with sparse embedded stones |
| 4 | `DIRT2` | Another stone-detail dirt slot; its current bitmap resembles DIRT1 closely |
| 90 | `GrasTyl` | Plain grass |
| 92 | `Grastyl2` | Small irregular dirt/stone detail within a grass-compatible tile |

Ravenshore contains **37 raw-2 and 53 raw-4 tiles** among 1,156 interior dirt-family tiles, and **332 raw-92 tiles**
among 6,562 interior grass-family tiles: about **7.8%** and **5.1%**, respectively. Alvar provides a second city reference:
38 raw-2 plus 35 raw-4 among 970 dirt-family tiles, and 123 raw-92 among 8,164 grass-family tiles. These are whole-grid
interior-family measurements, not a requirement to paint every district at the same rate. Native slots resolving to the
same bitmap do not add visible variety. Verify the active world's lookup and artwork rather than assuming these raw IDs
work in MM6/MM7 or another terrain bank.

Use a low, reproducible frequency of compatible interior variants, and place larger irregular soil patches where the
landscape calls for them: worn approaches, rough meadows, banks, exposed shoulders and landmark settings. Keep broad
patches separate from the fine detail variation. Preserve deliberate clear grass as part of the composition, without
leaving every quiet area featureless. Avoid turning every tree into a circular dirt stamp or every tile into a stone tile.

Select detail variants only after the material/shore/road masks are correct. Do not replace transition tiles, roads or
water with an interior detail slot. Extend the corner-material check to recognize the actual new variants, then inspect
the textured ground from above and at eye height. Native variant selection is the export mechanism; arbitrary Blender
texture rotations do not substitute for correct ODM tile IDs.

## Compare local coverage, inside and outside the settlement

[Heatmaps](evidence/landscape_calibration/heatmaps.png) and
[measurements](evidence/landscape_calibration/measurements.json) compare Ravenshore, Alvar, Brackenford before and after.
Regenerate with `python3 level_generation/scripts/measure_landscape.py` after the native build. It rejects stale generated
entity counts/positions. Each category shares a color scale across maps, using 1,536-unit Gaussian smoothing and
available-land normalization; values show local counts per 2,048 × 2,048 area.

Town masks are analytical, explicit and reviewable: hulls around active service/residence building envelopes, selecting
Ravenshore's main-town buildings south of Y=8,192 and Alvar's main-town buildings north of Y=8,192. This excludes the
remote windmill/rural houses but retains both sides of town rivers. Brackenford uses the authored town membership.
The exterior edge extends 4,096 units from those building envelopes; other land is wilderness. Full-water tiles are
excluded; shore tiles remain land. The JSON records mask polygons, building membership, land-cell counts and rates.
These masks are not native city boundaries, traversability/visibility models or historical author intent.

The driver's [1237](../test_img/1237.png) points at the empty town-side meadow, while [1240](../test_img/1240.png) shows
Ravenshore's mixture of trees, small bare-soil shapes and boulders near the settlement. Brackenford's earlier improvement
populated distant groves but left this intervening land too empty. Fill the specific low-coverage shoulder or verge,
not an already dense faraway grove. Quiet means no compulsory encounter; it need not mean no scenery.

Separate tree, low-plant and rock maps. Rock counts include tiny stones used to frame a garden as well as large boulders;
count density does not measure silhouette coverage. Inspect native names, sprite scale and the player view before
matching a quota. Likewise, terrain stones are not included in the decoration heatmap. Preserve the differing roles
of close-planted civic gardens, working yards, open pasture, rocky edges and woods.

## Rough urban detail and humanoid camps

[1239](../test_img/1239.png) shows small and large rocks plus refuse heaps around rough house plots. Ravenshore contains
**12 `dec23` trash heaps**, concentrated around its northern working/residential district, rather than spread across
all streets. It also has two `dec24` and two `dec25` campfires. Alvar contains `dec26` cauldrons, which supply a second
reference for camp/cooking detail.

Use a few rock groups and occasional refuse beside suitable rear/service plots. Keep prosperous forecourts and
important entrances coherent; do not distribute trash uniformly or obstruct roads. At a humanoid camp, one fire or
cauldron can give the group a readable center, with nearby supplies/bones if appropriate. A wolf pack need not have a
cooking area. Leave fighting space and access to loot. Some of these native descriptors are interactive and may grant
food or other effects; they are not necessarily inert visual props.

## Buff pedestals and stat challenges are optional landmarks

[1241](../test_img/1241.png) shows Ravenshore's glowing pedestal in open grassland. Its `dec45`
name resolves through the existing native interactive-decoration rules to global event **532**, Earth Resistance.
Other native pedestal appearances map to Haste, Day of the Gods, Shield, other resistances, Heroism, Immolation and
Stone Skin. In the MM8 `dec44`–`dec55` family, the global event is 531 plus the appearance's offset. Use the native
name/descriptor, animation, light and binding; no fake collision BModel or duplicate local event is needed.

For a map of this scope, **one or two buff pedestals** and **zero to two stat challenges** are useful optional planning
ranges, not mandatory quotas. Put one where it improves the route: a town departure, quiet hill, overlook or suitable
encounter approach. Frame it with a few fitting rocks/plants and a usable standing area. A focal point can add interest
without adding another enemy camp.

[1242](../test_img/1242.png) is Ravenshore's `dec43` challenge, framed by small `rock22` stones, flowers and trees.
The inspected neighborhood has 35 `rock22` instances within 1,600 units; this is a designed setting, not general
wilderness boulder density. An incomplete stone border can direct approach without fencing off the interaction.

Native `dec40`–`dec43` appearances select different test tiers; the stat is initialized by the native seeded binding.
The highest tier (`dec43`, global events 564–570) checks the selected character's **actual stat ≥200**, grants
**10 skill points**, and records completion on that character. Lower tiers have different thresholds/rewards. The
completion bits are shared native tier/stat entitlements: another standard challenge of the same kind is **not** an
independent extra reward. Reusing the native rule intentionally shares those bits. If the driver wants a separately
rewarding custom challenge, allocate scoped character state and authored behavior explicitly; do not silently collide
with the original game's completion bits or let every click farm skill points.

Behavior references: `game/gameplay/InteractiveDecorationRules.cpp`,
`game/outdoor/OutdoorInteractionController.cpp`, `assets_dev/engine/events/Global.lua` events 531–542 and 543–570,
and `reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Global.txt`. Generated legacy Lua remains untouched.
Brackenford uses Earth Resistance (`dec45`), Day of the Gods (`dec46`) and one native high-tier stat challenge (`dec43`).

## Carry these checks into the next map

Record ground-detail slots/frequencies, broad soil-patch roles, scenery heatmaps/sample membership, native landmark
bindings and full bridge-to-terrain contact in the brief and review. Confirm exact native IDs/positions/light descriptors,
road/door clearance, and bridge profiles in one quick readback. Use a few focused normal-game views for appearance and
hover/interaction evidence. Reusing already implemented native decorations does not require an exhaustive scenario
matrix; new custom reward logic or an observed interaction defect merits a focused behavioral check.
