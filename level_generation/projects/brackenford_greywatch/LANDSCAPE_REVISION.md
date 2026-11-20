# Landscape detail and bridge revision

Responds to `test_img/1236.png`–`1242.png`. Reusable findings live in
[LANDSCAPE_DETAIL_CALIBRATION.md](../../LANDSCAPE_DETAIL_CALIBRATION.md), with native Ravenshore and Alvar evidence.

## Changes

- Raised the bridge deck from 640 to 1,152 and reshaped both landings/road approaches. The entire deck width and span
  clear terrain by at least 64 native units. Stone landings meet the timber edges without overlapping top faces.
- Added 11 irregular soil patches and sparse compatible interior tile variants: 67 `DIRT1`, 55 `DIRT2`, 462
  `Grastyl2`. Broad patches and fine stone detail are separate layers; transitions retain matching native corners.
- Filled the empty town-side meadows and bridge verge with clustered trees and rocks. Added a few rough yard pockets
  with six refuse heaps. Native scenery is now 487 trees, 416 plants, 239 rocks, 18 props and six lights: 1,166 total.
- Added native Earth Resistance and Day of the Gods pedestals, one high-tier stat challenge with an open stone border,
  and two campfires plus a cauldron at the humanoid camps. These reuse native descriptors, animation, lights and
  existing global interactions; no new generated-Lua edits or engine behavior changes.

Accepted houses, road-frontage positions, arrivals and all 102 fixed actor positions are preserved. The previous
wilderness revision already established encounter areas, quiet routes, the pond and embedded cave. This follow-up
adds scenery to quiet land without distributing enemies uniformly.

## Density calibration

[Heatmaps](../../evidence/landscape_calibration/heatmaps.png) compare trees, rocks and low plants separately with a
common scale per category. [Measurements](../../evidence/landscape_calibration/measurements.json) record native/source
hashes, explicit town membership, hulls and usable-land denominators. Town is an analytical building-envelope hull;
the edge is exterior land within 4,096 units of those buildings. These are comparison masks, not native city zones.

| Trees per 4,096 × 4,096 land area | Town | Town edge | Wilderness |
| --- | --- | --- | --- |
| Ravenshore | 1.56 | 0.60 | 2.80 |
| Alvar | 1.91 | 4.99 | 3.62 |
| Brackenford before | 3.31 | 1.36 | 2.73 |
| Brackenford revised | 3.31 | 4.15 | 3.36 |

The empty land near town was the important gap; whole-map totals obscured it. The revised edge is greener than
Ravenshore's largely open edge but within the range illustrated by Alvar. This follows the driver's desired wooded
meadow, rather than mechanically matching one number. Brackenford already has abundant low plants in town gardens,
so this pass adds trees/rocks where needed rather than another uniform flower layer. Rock counts include small border
stones and do not measure large-boulder silhouette coverage.

## Review and iteration

The preceding bridge check verified floor orientation and selected anchors but missed bank terrain intruding into the
span. The new check samples native terrain triangles across the entire span, plots three longitudinal profiles and
checks approach grades. A first revised render then exposed coplanar stone/timber overlap; shorter landings remove
that overlap, and native top-face checks prevent its return.

- [Bridge profiles before/after](review/landscape_revision/bridge_profiles.png)
- [Bridge oblique view](review/brackenford_native_landscape_bridge.png)
- [Town-side meadow](review/brackenford_native_landscape_meadow.png)
- [Town rough plots](review/brackenford_native_landscape_town.png)
- [Challenge setting](review/brackenford_native_landscape_challenge.png)
- [Humanoid camp setting](review/brackenford_native_landscape_camp.png)
- [Regional overview](review/brackenford_native_landscape_region.png)
- Player-height [bridge](review/gameplay/landscape_bridge.png),
  [buff pedestal](review/gameplay/landscape_pedestal.png), [challenge](review/gameplay/landscape_challenge.png).

Blender views use the written native map and decoded sprite frames with inspection lighting. Game views use the
normal executable and ordinary review party. They establish appearance/hover evidence, not complete bridge traversal,
new reward-behavior tests or combat balance. Native challenge `dec43` selects one stat at initialization, requires 200,
and grants ten skill points once per character for the shared native tier/stat entitlement.

## Rebuild and play

Run the author through Blender MCP, normalize/reopen `source/lg01.blend`, then check source before native export:

```sh
python3 level_generation/projects/brackenford_greywatch/check_landscape.py --source
python3 level_generation/projects/brackenford_greywatch/check_frontage.py --source --review-directory landscape_revision
python3 level_generation/projects/brackenford_greywatch/build_brackenford.py
python3 level_generation/projects/brackenford_greywatch/check_landscape.py
python3 level_generation/projects/brackenford_greywatch/check_frontage.py --review-directory landscape_revision
python3 level_generation/projects/brackenford_greywatch/check_facade_revision.py --review-directory landscape_revision
python3 level_generation/scripts/measure_landscape.py
```

Run `review_landscape_blender.py` through the connected MCP instance for one native import, automap and six views.
Stage/package using [REBUILD.md](REBUILD.md), then prepare a fresh God snapshot. Static geometry/binding checks and
focused views are the default review; an exhaustive outdoor scenario matrix is unnecessary for this change.

The new launcher is `/tmp/openyamm-brackenford-playtest-landscape/play.sh outdoor`.
Choose **Load Game → Scenario** for the God character. Use `indoor` for Greywatch. Prior snapshots remain frozen.
The previous source/native map is preserved under `review/landscape_revision/before/`.

## Native verification

[Landscape readback](review/landscape_revision/landscape_check.json),
[frontage/tile check](review/landscape_revision/frontage_check.json) and
[ID/clearance check](review/landscape_revision/quick_check.json) pass. Zero native tile-corner mismatches,
nonoverlapping deck/landing tops, maximum approach grades 0.188 / 0.375 / 0.110. All 87 BModels / 3,880 faces export.
The editable Blender file reopens with 1,367 objects, packed images and no linked libraries.
All 33 reference studies and their linked inventories/captures pass reference validation.

Native outdoor SHA256: `b33d797d47b29e80c83ce53a78e9f7d0fff93be139ed8e3085e9b830efd56fa2`.
Indoor unchanged: `b227608891142f1982f2cd6039124eaab2310775b6760760a8570baff8679fec`.


The six final Blender views and three final normal-game captures were opened and inspected. The bridge has continuous
visible planking with no buried surface or coplanar patches; the buff pedestal shows its native Earth Resistance hover
label and light, and the challenge's native animation/light appears within the open stone setting. Blender MCP remains
connected and the unrelated default scene was restored after review.

Package SHA256: `0f3be09546f887c36f424ef4ff23649567b423b02938e982691334b952f4e795`.

[Artifact verification](review/landscape_revision/artifacts.json) records the checked archive and fresh God snapshot.
Both starting saves reload with the copied executable, with the expected maps and party level.
