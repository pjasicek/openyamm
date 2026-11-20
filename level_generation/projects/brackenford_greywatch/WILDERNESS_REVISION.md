# Wilderness revision — Ravenshore calibration

This follows the accepted frontage/tile revision and the driver's `test_img/1231.png`–`1235.png` feedback.
The reusable findings and source references are in [WILDERNESS_CALIBRATION.md](../../WILDERNESS_CALIBRATION.md).
The town's buildings, arrival anchors and 29 resident/guard placements are unchanged.

## Composition changes

| Aspect | Starting frontage revision | Wilderness revision |
| --- | --- | --- |
| Hostile population | 14 enemies in two ogre camps | 73 enemies in 11 authored areas: 48 dire wolves, 11 centaurs, 14 ogres/mages |
| Encounter placement | Two remote cache guards | Northern/southern wolf areas, two loose eastern centaur areas, original ogre camps and cave guards; quiet town approaches, pond, obelisk route and castle forecourt |
| Native scenery | 285 trees / 336 plants / 96 rocks / 12 props | 373 trees / 416 plants / 173 rocks / 12 props; broader woodland coverage and southeast infill |
| Water | One river | River plus a small native-terrain pond in the north meadow, with its own level shore |
| Bridge | Stone parapets | Plank deck, open timber posts/rails and stone supports, retaining the original deck height and passage |
| Cave | Large contrasting rock collar | Smaller dirt-matched collar in a terrain cleft; nearby wolves and one relocated chest |

The reference population accounting matters: Ravenshore's 59 regular markers imply **118 expected actors** under its
current 1–3 count range. Its 78 normally hidden invasion actors are separate. This revision improves Brackenford's
encounter geography without claiming equal combat difficulty: 73 fixed enemies remain fewer than that expected total.
The final balance belongs to the driver. New fixed populations do not add duplicate native spawn markers or change
shared hostility, draw distance, AI, monster definitions or runtime code.

The eleven area centers have nearest-neighbor quartiles of approximately **5,818 / 6,212 / 6,684 units**. Ravenshore's
inferred wolf-patch centers are closer at roughly **3,777 / 4,049 / 5,293**; its centaurs use a different, looser marker
pattern. Brackenford therefore still has broader gaps, deliberately keeping its inhabited center and selected approaches
quiet. These figures compare authored area centers with inferred groups, not equal actor-level densities.

The northwest observation window rises from 38 to 72 trees, approaching Ravenshore's 77 in that window. The southeast
window rises from no trees/plants/rocks to **43 / 19 / 17**. Equal coordinate windows are not identical districts or
land-use samples; Ravenshore has more water and its southeastern window includes town.

The cave's nearest enemy begins about **1,790 units** from its active face, with two within 2,048. The castle's nearest
enemy starts about **7,209 units** away, with none within 2,048. Minimum initial hostile separation from checked town
positions is **11,209 units**. None of these static distances guarantees that a pulled/wandering enemy can never arrive.

Four chests and five loose items remain. The second southern-cache chest moves to the cave approach while preserving
its semantic identity `south_cache_chest_2`, event **204** and container **3**. The southern ogre cache still has one
chest and its loose items; the eastern cache retains two chests. No new chest script or reward behavior was introduced.
Use a fresh snapshot so old saved map-state positions do not mask new placements.

## Visual review and iteration

- [Written-map overview](review/brackenford_native_wilderness_region.png)
- [Northern woodland](review/brackenford_native_wilderness_north.png)
- [Southeast woodland and den](review/brackenford_native_wilderness_southeast.png)
- [Native pond shoreline](review/brackenford_native_wilderness_pond.png)
- [Native timber/stone bridge](review/brackenford_native_wilderness_bridge.png)
- [Native cave cleft and chest](review/brackenford_native_wilderness_den.png)
- [Encounter/scenery comparison plan](../../evidence/wilderness_calibration/brackenford.png)

Blender review imports the written ODM and native entity positions, with decoded MM8 sprite frames. Its lighting is
inspection lighting and its views omit rendered actors. Normal-game captures in `review/gameplay/` supplement this.

The first pond pass exposed ten grass/water corner mismatches. A full grid-corner dirt collar fixed them; the final
source and native readback have zero mismatches. The first cave pass still read as a freestanding grey rock mass,
with the chest on an awkward slope. Its capture is retained in `review/wilderness_revision/first_pass/`; the final
collar is smaller and uses the den reference's dirt material, and the chest now sits on the flatter approach.

Pond outlines remain limited by the native 512-unit grid and available shore variants. Dense woodland and open meadow
regions remain deliberately distinct. Driver review is still needed for combat pacing and any house-by-house art tweaks.

## Reproduce and validate

Run `author_brackenford_blender.py` through the existing Blender MCP connection, then normalize/reopen `source/lg01.blend`
using `verify_blend.py`. Run `check_frontage.py --source --review-directory wilderness_revision` before a native build.
Build with `build_brackenford.py`, then run:

```sh
python3 level_generation/projects/brackenford_greywatch/check_wilderness.py
python3 level_generation/projects/brackenford_greywatch/check_facade_revision.py --review-directory wilderness_revision
python3 level_generation/projects/brackenford_greywatch/check_frontage.py --review-directory wilderness_revision
python3 level_generation/scripts/measure_wilderness.py
```

These static checks take seconds. They cover native grounding, dry actor positions, no duplicate spawns, chest IDs,
level water, bridge floor/ceiling, preserved town/arrivals, texture keys, door/frontage clearance and tile corners.
No exhaustive outdoor scenario suite or engine rebuild is needed for these authored placements.

Run `review_wilderness_blender.py` through MCP to regenerate the automap and six focused views from one native import.
Stage the result and package it using [REBUILD.md](REBUILD.md). The fresh God snapshot is
`/tmp/openyamm-brackenford-playtest-wilderness`; run its `play.sh outdoor`, then choose **Load Game → Scenario**.
Earlier frozen snapshots and the accepted source backup in `review/wilderness_revision/before/` are preserved.

## Final artifacts and checks

Native outdoor SHA256: `6d4184a1d34301004417db201b716db4795a5d3cccfd3cba8ef5a320af327236`.
Indoor remains `b227608891142f1982f2cd6039124eaab2310775b6760760a8570baff8679fec`.
Package SHA256: `a0459885e663901c2d4678049e612889ccac28b42145be6530b48d053f07e942`.

- [Quick wilderness readback](review/wilderness_revision/wilderness_check.json): passed in about 0.1 seconds.
- [Native IDs/frontage/decorations](review/wilderness_revision/quick_check.json) and
  [tile/door comparison](review/wilderness_revision/frontage_check.json): passed; zero corner mismatches.
- [Cave at player height](review/gameplay/wilderness_den_final.png),
  [bridge at player height](review/gameplay/wilderness_bridge.png),
  [active wolves in northern woodland](review/gameplay/wilderness_north.png): opened and inspected. These are short
  visual observations, not completed combat encounters, bridge traversal or performance measurements.
- Editable Blender source independently reopened with packed images and no linked libraries.
- [Frozen God snapshot](review/playtest_snapshot.json): both starts reloaded with the copied executable.

The cave collar is reduced from 3,072 to 1,536 units across and its opening from 640 to 448 units high. Its material
now follows the surrounding dirt; the chest moved from the slope to the flatter approach. Geometry remains deliberately
simple and faceted. The full native captures preserve the final pond, bridge, woodland and cave composition for the
next driver review. Blender MCP remained connected and the previously active unrelated scene was restored.
