# Visual review and quick completion checks

The driver’s 2026-09-07 calibration makes **visual authenticity the default priority**. A synthetically wired outdoor
face using an existing event/service does not need its own scenario. Do not inherit the long test matrix from the first
Brackenford/Greywatch run. Functional pass counts did not catch its oversized doors, crate windows or incoherent walls.
Use [VISUAL_CALIBRATION.md](VISUAL_CALIBRATION.md) and the [Ravenshore catalogue](catalogues/mm8_ravenshore/README.md).

For outdoor work, read [Accepted outdoor calibration](OUTDOOR_CALIBRATION.md) before selecting the kit or laying out
a town. Record reference district/biome and intentional deviations; numerical examples are starting evidence, not quotas.

## Default iteration

1. Choose a comparable building/room and name the quality being borrowed: scale, facade panels, roof, terrain, placement.
   For a settlement also measure [instances per architectural form](HOUSE_VARIETY.md), separating ordinary houses
   from unique services/landmarks. Rotation or a cosmetic texture change alone does not count as another form.
   Measure [settlement density by district](SETTLEMENT_DENSITY.md) as well: envelope gaps, center distances and
   coverage, with joined blocks counted once. Draw opposing frontages and deliberate open pockets before placement.
2. Make **one** representative textured prototype. Compare it to the reference at the same game-unit scale and eye height.
   Approve a small house, a larger service and a joined block before scattering a settlement. Do not decorate a bad prototype.
3. Inspect isolated oblique/front views, a plan and relevant eye-height context. Match door/window art, UV repetition,
   material bands, roof silhouette, service sign and terrain contact. For indoors also use a cutaway and full-ceiling view.
4. Fix the largest visible mismatch first. Keep before/after images with measured dimensions and brief observations.
5. Check [frontage and tile calibration](FRONTAGE_AND_TILE_CALIBRATION.md): resolve snapped road cells, measure real
   doors, remove unnecessary ordinary-house spurs, and inspect actual transition bitmap corners and local infill.
6. Run one quick native build/readback and static wiring summary. Recheck only changed geometry/bindings afterwards.
7. Deliver sources, native package, short visual review and the wiring report. State anything deferred or unimplemented.

## Quick wiring/build check — default

- [ ] Native file opens; exported bounds/terrain arrays and intended geometry counts are sensible.
- [ ] Required texture keys resolve; facade UVs use the intended bitmap dimensions.
- [ ] Each intended active face points to a declared event/handler; service/house and destination IDs resolve.
- [ ] Distinct doors in a shared building retain their own event/service IDs. Label-only hint faces are not active entrances.
- [ ] Party starts/arrival markers exist with coordinates, facing and clear planned space; no duplicate marker exports.
- [ ] Requested chests/actors/props have records at intended locations; synthetic handlers are assembled without losing
      authored logic or leaving required placeholders. Existing runtime behavior does not need to be re-proven here.
- [ ] No unresolved native export error or obvious blocked route/door. Static road-clearance masks exclude wells/fountains.

Keep this check short: parse once, report once. The existing project builders already verify native arrays and face/event
correspondence. Do not turn “quick wiring” into repeated game launches, every-house clicking, shop purchasing, every-edge
travel, multi-seed loot/refill audits, five-minute town observations or comparative FPS capture for routine content edits.
A brief game view/walkthrough is useful for appearance or a suspected collision issue, not an exhaustive scripted gate.

## Visual acceptance — the main gate

| Aspect | Concrete acceptance |
| --- | --- |
| Scale | Compare physical units, not independently fitted thumbnails. Ordinary house door starts at 128×256 in the measured Ravenshore kit; retain party eye-height reference. Larger services enlarge their body, not all features. |
| Texture authenticity | Match the building’s facade family: door, integrated window panel, blank wall, lower/upper band, corners, cornice and roof. Reject crate windows, default boat doors and stretched facade motifs. |
| Role and variety | Small homes stay compact; inns/temples/civic masses are larger where the reference supports it. Joined buildings have separate entrances. Source rich/poor asset labels are not proof of resident wealth. |
| Simplicity | Use a few well-proportioned masses and correct textures. No chimneys in the requested Ravenshore house vocabulary; a narrow turret is a different structure. |
| Roads and placement | Travel corridor and door approach remain empty. Wells/fountains sit in side pockets, gardens or widened squares outside the through-route. Check full footprint/clearance, not just prop origin. |
| Settlement density | Compare native-unit gaps and same-scale plans for the intended district type. Reject oversized plots around otherwise correct houses. Separate open villages, market blocks and enclosed courtyards. |
| Street frontage | Ordinary doors sit near the shared street; dedicated approaches align laterally with the actual door after snapping. No automatic spur per house. |
| Tile transitions | Correct one-corner versus three-corner artwork, dirt collars around incompatible materials, and visually continuous diagonal pairs. Validate actual native tile corners. |
| Occupied space | Fill intended court edges and local garden/verge gaps; count accepted placement per group, keeping roads and fountain approaches clear. |
| Terrain | Foundations/steps meet quantized ground; street slopes and screened approaches fit the scene. No floating corners or foundations engulfing doors. |
| Detail and lighting | Native vegetation/props belong to the biome and space; indoor lights/ambient remain coherent. Do not conceal poor architecture with dense scatter. |
| Scenery composition | Use the [all-outdoor calibration](OUTDOOR_DECORATION_CALIBRATION.md): reference a local patch, inspect the actual palette, record accepted groups and purposeful open space. Compare local coverage and route views; do not fill gaps to meet a global quota. |
| Evidence | Open the images and record specific comparisons. A successful export, a beauty shot or many passing tests is not visual approval. |

Use simple verdicts: **revise**, **meets the reference brief**, or **intentional documented variation**. Avoid numerical
scores that imply precision without a concrete comparison. Camera and image type must be clear: native game capture,
Blender native reimport or authoring preview. Independently fitted catalogue views cannot establish relative scale.

## When deeper runtime checks are justified

Use focused unit/headless coverage when modifying compiler/runtime logic, implementing a new mechanism or scripting
behavior, resolving an observed failure, or when the driver explicitly asks for it. A new indoor lift needs a short
boarding/landing/recovery check; a copied ordinary outdoor service binding normally needs only a static ID/face check.
Preserve repository-required regression checks for engine changes. Do not repeat a broad scenario suite after a texture,
window, roof or prop-placement adjustment unless the change exposed a relevant failure.

Difficulty tuning and extensive combat, save/refill and stock-isolation audits are separate optional tasks. If they are
requested, record their scope and results honestly. The historical first-project reports remain useful diagnostics,
but their long execution checklist is not the template for the next generation run.

## Follow-up: compose the settlement around the sketch

[Sketch layout calibration](SKETCH_LAYOUT_CALIBRATION.md) covers unequal loops, native diagonal roads, raised landmark
approaches, purposeful open pockets and the distinction between good spacing and a convincing composition.

## Wilderness composition follow-up

Apply [wilderness calibration](WILDERNESS_CALIBRATION.md). Record initial fixed actors, placed spawn markers and their
MapStats count ranges, conditional/event populations, and named quiet areas separately. Compare same-scale encounter
patches and gaps; do not use uniform map-wide pack spacing. Check each entrance's intended guarding and optional reward.
Compare tree/rock/plant coverage on comparable usable land, not only totals; avoid filling deliberately open biomes.
Inspect native pond shoreline transitions, bridge deck/rail/support scale, and the cave mouth's contact with its terrain
cleft. Use focused visual captures and one fast native grounding/ID/clearance check; no blanket outdoor scenario suite.

## Landscape detail and native landmarks

Use [landscape-detail calibration](LANDSCAPE_DETAIL_CALIBRATION.md). Sample the whole bridge deck/rail footprint
against final native terrain, including both bank landings and onward road grades. Inspect a side view and an along-deck
player view. A correctly oriented floor can still be buried. Compare category-specific scenery heatmaps with explicit
town/edge/wilderness membership and usable-land denominators; distinguish small stones from large boulder silhouettes.
Inspect sparse interior ground-detail variants alongside broad dirt patches. Keep worn plots/refuse/cooking props
contextual and roads clear. For optional pedestals/challenges, record native effect, selected-character stat/tier, light,
standing area and whether completion is shared native entitlement or separately allocated custom state.

## Outdoor regional exits

Use [regional-transition calibration](REGIONAL_TRANSITION_CALIBRATION.md). Record travel bounds separately from the rendered heightfield extent.
Roads and their surrounding land must continue beyond the prompt. Check the final road tile (no end cap), native
corner continuity and a traversable floor. Straight open roads across flat or rolling land are valid; bends, hills and
mountain barriers are optional. Require sightline occlusion only for an explicitly screened-pass design. Review a full-pass plan, an oblique and
walking-height views immediately before/at the actual prompt. Preserve cancellation/arrival space. Do not count
unused final tile-array rows as rendered terrain or place required content outside the travel boundary.

Road-purpose check: town/services, castle approaches and regional routes may warrant roads. Natural caves,
monster camps and treasure are normally off-road. Do not automatically connect all POIs; removing a road must retain
its encounters/loot and restore coherent terrain materials and remaining junctions. See OUTDOOR_CALIBRATION.md.
