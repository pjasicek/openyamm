# Castle Kalindra: restored royal exterior

The castle keeps the source-backed reservation at (-16128,-2304), west of Castleview, and faces east toward the
existing approach. The entire reservation lies on native ground Z480. Its original geometry uses Garrote's green
masonry and tiled roofs, with warm formal windows and a new blue/ochre crown banner. The native camp keep was
reviewed as a material and composition reference; none of its vertices are reused.

An open 768-unit arch leads into a paved court. A taller, offset keep closes its far end, with unequal lower wings
and two polygonal towers. The south tower stands toward the entrance; the north tower rises beside the keep.
This preserves the planned royal height hierarchy without enlarging ordinary doors or facade artwork.

| Component | Height above pad | Purpose |
| --- | --- | --- |
| Main keep | Eave 2048; roof 2560 | Main royal volume; single future BLV entrance |
| South wing | Eave 768; roof 1024 | Lower enclosure beside the approach |
| North wing | Eave 1024; roof 1280 | Unequal court enclosure |
| South tower | Parapet top 3584 | Principal landmark |
| North tower | Parapet top 3328 | Secondary landmark behind the court |
| Entry arch | Spring 576; opening peak 768; top cap 1056 | Unblocked entry, with no gate leaf or extra handler |
| Court paving | Walking face 6; bottom -32 | Six-unit step above native terrain; no coplanar ground |

Two stone benches face inward from unequal positions along the court sides. The clear middle leads to the keep's
128×256 door at (-15648,-2176,480), identified by `mm5:sw/kalindra/entrance`. Its lower six units meet the paving.
There is no outdoor shop/teacher doorway for each castle contact. The 15 contacts retained in `interiorContacts`
remain assigned to the original castle interior: Queen Kalindra, Errol, Gem, Audrey, Carl, James, Terry, Kenneth,
Dimitri, Megan, Guido, and the four service sites. No resident actors or global dummy NPC rows are created.

The original route runs from A4 (map 4,5,14) to Castle Kalindra Level 1 (map 41,15,7); its return arrives at A4 (6,14).
[The retained source record](kalindra_routes.json) includes the original unavailable/out-of-phase label and transfer
provenance. Restoration stages and interior travel remain deferred. The future outdoor return marker
`mm5:sw/kalindra/ground_return` is inactive at (-13600,-2304,480), outside the arch. The present door is status-only.

## Sources and review

[prepare_architecture.py](../prepare_architecture.py) owns the component dimensions, venue position, retained
interior contacts and arrival marker. [author_castle.py](../author_castle.py) constructs the polygonal towers,
arch, paving and benches. The shared author supplies the keep, wing roofs and ordinary entrance panel.
The original [crown SVG](art/mm5royal.svg) is rendered at native 128×256 by the specification command; its SVG/PNG
hashes join the material provenance. Native `t18a04a` provides paired tower windows, while existing `t18a04c`
provides the keep/wing windows. No texture upscaling is required for this environment milestone.

Inspected the five first renders. The initial eye/rear cameras cropped tower tops, and the first court view framed
only the keep door. Corrected the cameras and reviewed the repeated [full eye view](../review/kalindra_v2/kalindra_eye.png),
[court bench](../review/kalindra_v2/kalindra_court.png), [open exit](../review/kalindra_v2/kalindra_court_return.png)
and [rear composition](../review/kalindra_v2/kalindra_rear.png). Checking the distant camera's ground contact then
found it only 16 units above that higher terrain: its Z was incorrectly based on the castle pad. Grounded terrain
eye cameras now use the height at the camera position. Inspected the repeated
[true player-height view](../review/kalindra_v3/kalindra_eye.png), 176 units above its native ground.
The initial oblique and close door views show the
same unchanged geometry. These are actual-heightfield Blender views with neutral terrain and shaded lighting;
native illumination, foliage, movement and interaction acceptance are separate requirements.

All 219 previous OBJ files remain byte-identical; Kalindra adds nine models. An isolated road regeneration preserves
all 287 cells, every path, frontage and adjustment. The approach still terminates outside the entry arch; the ordinary
keep door sits farther inside the same castle reservation.

[review_castle.py](../review_castle.py) reads the exported courtyard, two buried pier feet and four buried bench feet
against actual native triangles, and verifies the ordinary door quad and event binding. The main keep, wings and
towers also use the normal foundation audit. Native
`ed3ce45b886943de5a566de164691a23de55d56aeb7fe37f2804a6735b9641db` contains the nine castle models;
[native geometry evidence](../review/kalindra_v2/native_geometry.json) passes all seven contact checks and the door binding.

Actually inspected the [native overview](../review/gameplay/mm5_kalindra_context_v1.png),
[outside approach](../review/gameplay/mm5_kalindra_walk_v1_outside.png),
[courtyard after walking](../review/gameplay/mm5_kalindra_walk_v1_passage.png),
[door click](../review/gameplay/mm5_kalindra_walk_v1_click.png),
[restored doorway](../review/gameplay/mm5_kalindra_walk_v1_restored.png),
[outward court view](../review/gameplay/mm5_kalindra_exit_v1_court.png),
[road after exiting](../review/gameplay/mm5_kalindra_exit_v1_outside.png), and
[bench contact](../review/gameplay/mm5_kalindra_bench_v1.png). Ordinary movement crosses the arch both ways.
The real click displays `Castle Kalindra: not implemented yet.`; F9/F10 restores the doorway view. Decoded save
fields retain map, gold, food, held item, health and inventories. Runtime load/reload reports zero actors.
[Review provenance](../review/kalindra_v2/native_review.json) retains capture/native/binary hashes and decoded saves.
The [isolated starting save](../review/playtest/start_kalindra.json) is refreshed to this native checkpoint.
Surrounding meadow/road-edge composition and the complete regional skyline still require the environment pass.
