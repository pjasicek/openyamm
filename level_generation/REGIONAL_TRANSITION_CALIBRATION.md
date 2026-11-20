# Regional exits: roads continue beyond travel bounds

Based on driver images [1243](../test_img/1243.png)–[1248](../test_img/1248.png), the native Ravenshore/Alvar maps,
and the current navigation table. The travel prompt belongs partway along a believable route. It is not the visible
end of the road or landscape. This applies to outdoor generation; indoor transition faces have different geometry.

**Driver clarification: continuation is required; curvature and terrain barriers are optional.** Straight roads across
flat or gently rolling open country are valid regional exits. Neighboring locations do not require mountains, hills,
or a valley between them. Choose the road shape and relief from the landscape; use bends and screening only where
they fit. The accepted Brackenford passes demonstrate one treatment, not the default shape for every future exit.

## Distinguish the travel trigger from the physical terrain edge

`assets_dev/engine/data_tables/map_navigation.txt` gives Ravenshore and Alvar travel bounds of **±23,143 units**.
Brackenford uses **±24,576**. These are gameplay boundaries, not the heightfield's extent. The renderer constructs
**127 × 127 quads from 128 × 128 height samples**, spaced 512 units apart. In this checkout, rendered terrain spans
X **−32,768…32,256**, Y **−32,256…32,768**. The last stored tile row/column has no corresponding rendered quad.
Do not mistake painting that unused row/column for extending visible geometry.

Consequently, several thousand units of native terrain remain visible beyond a travel prompt. Author that outer land
as part of the route: continue road paint, ground material, valley walls and skyline. Do not put required monsters,
rewards, services or arrival anchors out there. Keep actual destination, days, heading and return-arrival registration
separate from this visual composition. Do not move the gameplay boundary or shorten the view distance to hide an
unfinished road. Geometry near the trigger must also allow the player to turn around when cancelling travel.

## Native examples and measurements

[Annotated terrain/road plans](evidence/transition_calibration/exit_plans.png) mark native road cells red and the travel
trigger cyan. [Source-hashed measurements](evidence/transition_calibration/measurements.json) use rendered cells only;
distances below are outward coordinate distances to the last road tile's outer edge, not winding path lengths.

| Native exit | Road beyond trigger | Composition |
| --- | --- | --- |
| Ravenshore → Shadowspire, east | 9,113 | Deep rock cut; high flanks and staggered road segments continue to the eastern mesh edge. |
| Ravenshore → Alvar, north | 9,625 | Open rolling grassland beside the river; a bent approach becomes a long continuing road to the northern edge. |
| Ravenshore → Garrote Gorge, west | 8,089 | Narrow valley with staggered bends and projecting terrain shoulders; road stops at X=−31,232, 1,536 short of the mesh edge. |
| Alvar → Murmurwoods, west | 9,625 | Raised flanks frame a long outward road; native road reaches the western edge. |
| Alvar → Ironsand, east | 9,113 | Offset/diagonal road follows a broad low corridor between elevated terrain and reaches the eastern edge. |
| Alvar → Ravenshore, south | 9,113 | Road bends around high ground before continuing to the southern edge. |

Ravenshore's west route is an important exception to “every road reaches the absolute bounds.” The driver's walking
view [1247](../test_img/1247.png) shows the road bending behind a shoulder; its raised view
[1248](../test_img/1248.png) reveals the longer valley. The view supports the interpretation that the bend conceals the
cutoff at walking height. We can measure the native road ending; we cannot prove the original authors' intent.
The generation default is to continue to the final rendered cell. Screening is optional and must fit the landscape;
an open straight continuation does not fail review because it lacks an occluding hill. Never accept a visibly capped
road immediately behind the prompt merely because travel works.

Native textured studies:

- Ravenshore: [Shadowspire cut](evidence/transition_calibration/ravenshore_shadowspire.png),
  [Alvar rolling approach](evidence/transition_calibration/ravenshore_alvar.png),
  [Garrote valley](evidence/transition_calibration/ravenshore_garrote.png).
- Alvar: [Murmurwoods approach](evidence/transition_calibration/alvar_murmurwoods.png),
  [Ironsand approach](evidence/transition_calibration/alvar_ironsand.png),
  [Ravenshore approach](evidence/transition_calibration/alvar_ravenshore.png).

These Blender views import native terrain and BModels with inspection lighting and a composited water frame. They
omit actors and decoration sprites. Use the driver's normal-game images for walking-height atmosphere. Flying can
expose the finite mesh in original maps too; walking-eye screening is not an all-altitudes invisibility claim.

## Generation sequence

1. Read the target map's actual navigation bounds and terrain dimensions. Record both in the brief, along with each
   outgoing route and its incoming arrival/heading. Draw the trigger on the full heightfield plan.
2. Plan the road from inhabited land through the trigger to the final rendered cell. Choose a fitting treatment:
   straight open continuation across flat or rolling country, a valley, a shoulder bend or an S-shaped cut.
   Mountains/hills are not required separators between maps. Do not give every exit identical scenery.
3. Shape a continuous traversable floor and surrounding land together. A crest or projecting shoulder can screen the
   far edge while the visible road clearly turns onward. Avoid a wall across the road, a sudden terminal pit, steep
   road grades, or a road painted over an unwalkable ridge. Preserve the accepted inner approach when revising a map.
4. Select connected native road corners/diagonals and compatible dirt/rock transitions. At a physical edge, use an
   outward-continuing road tile, not an end cap. Do not wrap terrain-neighborhood masks onto the opposite map edge.
5. Review an annotated top-down crop spanning both sides of the trigger, an oblique whole-pass view, and the normal
   game just before/at the travel prompt. The prompt may crop the view differently from ordinary exploration.
6. Make quick readback checks: connected road cells through the trigger, appropriate final tile, road-floor grades,
   preserved interaction/arrival identities, and tile seams. Only require terrain occlusion when the chosen design
   explicitly calls for a screened pass. For open exits, review the continuing road and coherent horizon instead.
   A sampled terrain sightline supplements the screenshot for screened passes. One brief approach to each changed prompt is enough when travel
   registration and behavior are already implemented; do not rerun every service/encounter scenario.

## Brackenford correction and reproducibility

Both former roads extended only **1,024 units** past the ±24,576 trigger and then ended within enclosing hills.
They now extend **8,192 units** to the west/north terrain edges, with bent cuts screening the far road at walking eye
height. All terrain heights inside the travel square, BModels, actor/decor positions and arrivals remain identical.
Native road tile-corner checks have zero mismatches. See the [revision and playtest](projects/brackenford_greywatch/TRANSITION_REVISION.md).

Run `python3 level_generation/scripts/measure_transitions.py` for the native plans/metrics. Run
`level_generation/scripts/blender_transition_views.py` through Blender MCP for the six focused reference renders.
The reference render hook accepts `STUDY_VIEWS` and `OUTPUT_DIRECTORY`, preserving normal case-study images.
Brackenford uses `regional_exit_scenery` in its plan, `check_transitions.py` for quick checks, and
`review_transitions_blender.py` for native obliques and automap. The checker's required sightline obstruction is specific
to these two authored passes; do not copy it as a universal outdoor acceptance gate. Runtime structural references are
`game/outdoor/OutdoorRenderer.cpp` (terrain mesh), `game/outdoor/OutdoorMapData.h` (dimensions),
`game/outdoor/OutdoorInteractionController.cpp` (travel cancellation), and the native navigation table.
