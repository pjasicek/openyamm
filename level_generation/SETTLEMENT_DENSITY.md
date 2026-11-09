# Settlement spacing and enclosure calibration

The driver's comparison of [Brackenford](../test_img/1218.png) and [Ravenshore](../test_img/1219.png) exposed a
second problem after the house art was corrected: properly sized houses were still too far apart. **Calibrate
placement as well as the kit.** Smaller houses on the previous large plots made the town look especially empty.
Do not enlarge the houses again to fill those plots.

## Accepted follow-up

The driver accepted the [frontage/infill revision](projects/brackenford_greywatch/FRONTAGE_REVISION.md): 28 physical
structures, median nearest-envelope gap about 735 units, and 19.1% envelope coverage. Its ordinary doors also moved
closer to shared roads; building-to-building density alone had missed their excessive setbacks. See the
[current measured membership](projects/brackenford_greywatch/review/frontage_revision/measurements.json) and
[accepted outdoor workflow](OUTDOOR_CALIBRATION.md). The earlier revision numbers below are historical comparisons.

For future maps measure both neighbor gaps and actual entrance-to-road distances, with a clearly stated method.
Plan density, frontage and open-space composition together; do not increase house size or fill every opening to hit a ratio.

## Measured native references

Run `python3 level_generation/scripts/measure_settlement_density.py`. It reads actual ODM vertices, groups physical
assemblies, and writes [membership, source hashes and measurements](projects/brackenford_greywatch/review/density_revision/measurements.json).
It does not launch gameplay scenarios. Original Lua/house bindings and the [building catalogue](catalogues/mm8_ravenshore/README.md)
distinguish houses from gates, boats, props, walls and dungeon exteriors.

| Selected district | Physical buildings | Nearest building gap, median | Gap middle 50% | Nearest center, median | Envelope coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ravenshore, all houses | 51 | 594 | 316–773 | 1,604 | 12.7% |
| Ravenshore market district | 23 | 608 | 264–756 | 1,612 | 30.1% |
| Ravenshore northwestern lanes | 17 | 464 | 456–712 | 1,215 | 16.9% |
| Garrote Gorge outer village | 17 | 895 | 744–960 | 1,836 | 14.3% |
| Garrote Gorge compound service houses | 6 | 896 | 374–1,028 | 1,605 | 19.1% |
| Brackenford before density revision | 23 | 1,866 | 1,505–2,022 | 3,072 | 8.9% |
| Brackenford after density revision | 23 | 832 | 704–912 | 1,665 | 20.8% |

Distances are **native units**; one terrain cell is 512 units. Each building contributes its closest *other physical
building*. A joined block is one building, even if it has several doors or BModels. Gap means the shortest distance
between convex XY envelopes of all vertices, including roofs/steps. It is a conservative spatial proxy, not a wall-to-wall
collision distance. Center means bounding-box midpoint. Coverage is summed building-envelope area divided by their
collective convex-hull area; it is not occupied-map percentage or a density requirement by itself. A temple forecourt,
river or distant seer can radically change that denominator. The middle 50% is the 25th–75th percentile.

Ravenshore market selection is explicitly `X > 11000, -17500 < Y < 0`; northwestern lanes are `X < 12000,
-4000 < Y < 5000`, using assembly centers. These are reproducible working districts, not claimed original author labels.
Do not compare Brackenford's entire town against Ravenshore's whole outdoor map or count each service-block fragment.
Garrote compound statistics exclude its central dungeon keep and perimeter walls: six surrounding house/service
assemblies are measured. The separate training-house assembly at the village/compound approach is not in either sample.

![Matched spatial scale](projects/brackenford_greywatch/review/density_revision/matched_scale_comparison.png)

All three panels above use identical units per pixel. The detailed plans below are individually cropped, have native
coordinate axes, and show terrain contours every 256 height units. Brown identifies measured houses, grey other visible
BModel faces, darker tan road-bank cells and pale tan dirt. These are analysis plans, not rendered texture minimaps.

- [Ravenshore market](projects/brackenford_greywatch/review/density_revision/ravenshore_market_district.png)
- [Ravenshore northwestern lanes](projects/brackenford_greywatch/review/density_revision/ravenshore_northwestern_lanes.png)
- [Garrote outer village](projects/brackenford_greywatch/review/density_revision/garrote_outer_village.png)
- [Garrote compound](projects/brackenford_greywatch/review/density_revision/garrote_service_compound.png)
- [Brackenford before](projects/brackenford_greywatch/review/density_revision/brackenford_before.png)
  and [after](projects/brackenford_greywatch/review/density_revision/brackenford_after.png)

## Layout patterns to borrow

**Ravenshore market:** joined service blocks and nearby houses form streets and partially enclosed spaces. Its buildings
cover about 30% of the selected district envelope. Leave a named square or planted pocket, not a large vacant lot around
every building. Larger service masses can close a view and give orientation without widening every street.

**Ravenshore lanes:** smaller houses can have lower area coverage yet short neighbor gaps. Opposing frontages and small
side gaps produce a village street even without continuous urban blocks. Plan the road and its two edges together;
avoid scattering independent house centers and then attaching each to a distant road by a long spur.

**Valleys and slopes:** distinguish a street enclosed by buildings from one enclosed by terrain. The measured Ravenshore
market buildings themselves occupy a comparatively low, level band (geometry bases 0–64); the screenshot's enclosing
hills are outside that band. Do not infer that every house stands on a steep slope just because a mountain frames it.
Keep walkable streets and local pads, place slopes behind selected rows, and let a bend, shoulder or landmark interrupt
some views. Avoid a huge rectangular flat pad. An enclosure should be visible from party eye height; an attractive
heightfield viewed from above is insufficient. Terrain and wall screening complement density and cannot substitute for it.

**Garrote Gorge outer village:** houses stand in irregular, open clusters across varied ground (geometry bases 32–448).
The larger typical gap is appropriate here. Keep some grass and space between homes instead of forcing a city block.

**Garrote Gorge compound:** tall perimeter walls and the central keep frame a broad working yard. Six surrounding
services share the level base at 640. Contrary to the initial recollection, there **are stone paths** inside: native
road-bank cells form an entry approach and a partial circuit around the keep. Most of the remaining courtyard is dirt.
The [game view](projects/brackenford_greywatch/review/gameplay/density_garrote_inner.png) shows the keep at left,
inn ahead, bordering wall behind the service houses, and stone strips within the dirt yard. This supports a military
courtyard layout, not a rule that each service needs a separate residential lane.

These are interpretations of geometry, bindings, tiles and views, not a claim to know the original authors' intentions.

## Agent workflow and quick review

1. Choose the **district type**: compact market, village street, open rural cluster, enclosed compound, or a stated mix.
   Record physical buildings, logical doors and kit forms separately; retain the [house-variety calibration](HOUSE_VARIETY.md).
2. Measure a comparable reference subset. Record membership and merged assemblies, center spacing, envelope gaps and
   coverage. For a Ravenshore-inspired small town, a median nearest-envelope gap roughly **450–950 units** is a useful
   initial range from these samples, not a universal acceptance threshold. Brackenford retains more space than the market.
3. Draw street spines, opposing frontage bands, junctions, forecourts and purposeful open pockets on a map-unit plan.
   Place houses at correct sizes, then connect their thresholds with short approaches. Joined shops move as one assembly.
   Vary setbacks and groups where the reference supports it; a repetition ratio does not justify endless uniform rows.
4. Fit native terrain around the compact settlement. Keep foundations grounded and slopes clear of doors. Place enclosure
   behind selected rows, preserve countryside approaches, and decide which spaces should feel open before scattering trees.
5. Reposition residents, guards, props, gardens and arrivals with the buildings. Roads and well/fountain footprints remain
   clear. Keep distant hostile packs outside the occupied-town buffer. Stable arrivals must still lead to the stable.
6. Compare **same-scale** before/after plans and one or two native game views. Inspect along a street, across opposing
   fronts, and toward a landmark or edge. Independently zoomed screenshots cannot establish numerical spacing.
7. Parse the final native file once for geometry/event/terrain agreement and simple footprint/actor/route clearance.
   Rebuild the automap, preserve event identities, and create fresh starts when distributing a new snapshot. Do not run
   every house, shop, travel or combat scenario for a placement revision.

[Brackenford implementation and playable snapshot](projects/brackenford_greywatch/DENSITY_REVISION.md).

## Follow-up: compose the settlement around the sketch

[Sketch layout calibration](SKETCH_LAYOUT_CALIBRATION.md) covers unequal loops, native diagonal roads, raised landmark
approaches, purposeful open pockets and the distinction between good spacing and a convincing composition.
