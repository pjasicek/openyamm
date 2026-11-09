# Accepted outdoor calibration for future maps

[The complete outdoor-decoration survey](OUTDOOR_DECORATION_CALIBRATION.md) adds all 42 MM6–MM8 ODM palettes,
coordinates and comparable coverage measurements. Select a local place/material palette and record the purpose
of scenery groups and open ground; a biome label or global decoration total is not a placement plan.

Read [regional-transition calibration](REGIONAL_TRANSITION_CALIBRATION.md) for the separate travel/terrain bounds,
roads continuing beyond prompts, optional terrain screening, and focused exit review. Straight open exits are valid;
curves, hills and mountain barriers are not required between neighboring maps.

The [landscape-detail follow-up](LANDSCAPE_DETAIL_CALIBRATION.md) adds full bridge/terrain contact checks, sparse
native stone-detail tiles, land-normalized scenery heatmaps, rough urban/camp props and optional buff/stat pedestals.
A deck-normal check and global decoration totals alone missed visible defects in the previous revision.

Read this before planning an MM6–MM8 outdoor settlement. The driver accepted the
[Brackenford frontage revision](projects/brackenford_greywatch/FRONTAGE_REVISION.md) after successive reviews of
house art, scale, repetition, density, composition, road placement, tile transitions and local decoration.
Use that result as an approved example of these relationships. Choose new geography and a fitting local art palette
for each brief; copying Brackenford's plan, counts or MM8 tile offsets is not the objective.

Start or reuse Blender with [the verified MCP startup procedure](BLENDER_MCP_STARTUP.md); the agent can launch the
application and verify automatic connection without waiting for the driver to press Connect.

## Working order

1. Select a reference **district, local terrain and biome** from the [decoration catalogue](catalogues/outdoor_decorations/index.html).
   Inspect its active service/house faces, native-unit building dimensions,
   recurring forms, road tiles, terrain shelves and local decoration groups. Use existing case studies; do not repeat
   the full MM6–MM8 survey for every map. Reinspect only missing or changed evidence.
2. Make a small coherent building kit: compact homes, a longer home/storage form, joined services and larger landmarks.
   Calibrate door/window/roof scale before placing a town. Enlarge important buildings through additional mass, bays or
   wings while retaining normal-sized doors and facade features.
3. Draw landforms and a road graph together with frontage bands, house groups and named open spaces. Give different
   districts their own spacing. Use unequal lengths, bends, forks, diagonal stretches and opposing fronts as appropriate;
   do not produce a uniform rectangular grid simply because the terrain is a grid.
4. Rasterize roads to the native cells. Move buildings using the **actual transformed entrance** and final road position.
   Set ordinary houses near shared streets; reserve dedicated lanes for deliberately recessed or raised sites.
   Fit foundations, steps and graded approaches to the quantized terrain. Keep joined buildings together.
5. Resolve categorical terrain materials and transition variants from actual bitmap artwork. Inspect corners, edges,
   bends, forks, diagonal pairs and shoreline joins. Correct source masks and selectors before paying for a native build.
6. Plan named wilderness encounter areas and deliberate quiet areas alongside inhabitants, arrivals and scenery.
   Separate spawn markers, fixed actors and conditional invasions in the reference census. Compare local woodland
   coverage as well as total counts; inspect guarded versus unguarded entrances, ponds, bridges and terrain clefts using
   [wilderness calibration](WILDERNESS_CALIBRATION.md). Check gardens separately from countryside coverage.
7. Inspect a textured plan with footprints/doors/decorations, an oblique native reimport and brief player-height views.
   Fix the largest visible mismatch, then run one quick native data/binding/clearance check. Refresh the automap and
   deliver reproducible sources, the native package and a new test snapshot if requested.

## Rules to carry forward

| Aspect | Default generation rule | Evidence and detail |
| --- | --- | --- |
| House art | Use related wall bands, integrated window panels, doors, cornices and roofs at native texel scale. No crate-window substitutes or boat doors on ordinary Ravenshore-style homes; no chimneys in this requested vocabulary. | [Facade calibration](VISUAL_CALIBRATION.md), [catalogue](catalogues/mm8_ravenshore/README.md) |
| Variety | Count ordinary instances/forms and physical service assemblies separately. Repeat several common forms with rarer exceptions, different sizes and orientations. Rotation alone is not a new form. Shared buildings can serve multiple establishments through distinct doors. | [House variety](HOUSE_VARIETY.md) |
| Density | Measure nearest envelope gaps and coverage for comparable districts at the same game-unit scale. Smaller correctly scaled houses require smaller plots. Preserve deliberate courts, gardens and countryside openings. | [Density](SETTLEMENT_DENSITY.md) |
| Street frontage | Resolve native road snapping first; use the door's transformed center, offset and outward normal. Do not pave a spur to every ordinary door. Align a terminating lane with its door, moving the house when necessary. | [Frontage](FRONTAGE_AND_TILE_CALIBRATION.md) |
| Terrain tiles | Use the active world's bank lookup, not guessed raw IDs or arbitrary Blender UV rotations. Inspect real one-corner versus three-corner artwork, both ends of adjacent edges, diagonal road halves and junction openings. Separate incompatible materials with supported transitions. | [Tile mapping and limits](FRONTAGE_AND_TILE_CALIBRATION.md#read-the-transition-artwork-not-only-its-filename) |
| Terrain shape | Make broad ridges, shoulders, valleys and local terraces that screen selected destinations from eye height. Give raised temples/manors graded approaches. Preserve configured view distance; noisy height variation alone does not create a convincing journey. | [Composition](SKETCH_LAYOUT_CALIBRATION.md), [landform](POPULATION_AND_COMPOSITION.md) |
| Local foliage | Put small plants/flowers in bounded gardens and verges, occasional trees between suitable buildings, and rocks near fitting slopes/edges. Use a biome-specific palette and deliberate countryside groves/clearings. Inspect accepted placements per group. | [Population by context](POPULATION_AND_COMPOSITION.md#outdoor-population-by-place-and-biome) |
| Decorations | Resolve native names/descriptors, sprite frame scale, visibility, collision and any light/event behavior. Ground on the final native triangle. Wells/fountains and the full footprint of other props stay outside roads and door approaches. | [Population and composition](POPULATION_AND_COMPOSITION.md) |
| Wilderness | Compose unequal encounter areas with quiet gaps. Match biome-specific scenery coverage on comparable land. Fit occasional ponds, timber/stone crossings and small cave mouths to native terrain. | [Wilderness study](WILDERNESS_CALIBRATION.md) |
| Gameplay | Retain real service/resident bindings, distinct shared-building doors, clear arrival markers and remote hostile groups. Allocate stable scoped IDs; regenerate numeric BModel indices from semantic identities. | [Authoring contract](AUTHORING_CONTRACT.md), [scripting](GAMEPLAY_AND_SCRIPTING.md) |

## Numbers are calibration evidence, not universal requirements

- Ravenshore ordinary houses: **44 instances / 13 recurring forms**. Accepted Brackenford: **20 / 5**, with
  **29 logical house/service doors in 28 physical structures** overall. This supports modest repetition within a coherent
  kit, not an exact ratio to enforce for islands, compounds, villages and cities alike.
- Ravenshore market and northwestern-lane median nearest-building-envelope gaps are **608** and **464** native units.
  Accepted Brackenford's whole-town median is about **735**, including its intentionally separate manor plot. Record
  sample membership and the effect of large landmarks instead of trying to match a whole-map average.
- Ordinary Brackenford entrances moved from a median **688 to 371 units** from shared-road **cell centers**. This is
  distinct from the painted stone edge or continuous centerline. Including old individual spurs hid the wide setback.
- The inspected MM8 transition banks use XNE/XNW/etc for **one dirt corner**, and NE/NW/etc for **three dirt corners**.
  The corrected native map has **zero mismatched corner-material edges**, down from 3,258. This does not establish
  pixel-perfect seams, connected painted roads or correct mappings for another tile bank; inspect those separately.
- Decoration count rose from **564 to 729**, but the transferable change is **where** it was placed: previously empty
  town interiors, court edges and verges. Do not import this total or its temperate palette as another biome's target.

A raised service may need a forecourt; a military compound may need a broad working yard; a desert may need extensive
bare ground. Record a purpose for open space and verify it from the player's view. Do not fill every gap blindly.

## Completion policy

Use [the review checklist](REVIEW_CHECKLIST.md) and record these decisions in the
[brief](templates/brief.yml) and [review](templates/review.md). Prioritize visible proportions, placement and coherence.
One fast native readback can check arrays, texture keys, face/event/target IDs, arrivals and obvious clearance mistakes.
Existing builder reports count; do not duplicate them or run every house/shop/travel/loot scenario. Use focused runtime
checks for new behavior, compiler/engine changes, an observed defect or an explicit request. Combat balance can remain
with the driver when that is the agreed scope.

Preserve previous review evidence and test saves. Keep the Blender MCP connection running, preserve unrelated scenes,
and save editable project sources. God-character starts are a playtest preference, not a mandatory map-generation rule.

## Roads need a settlement or travel purpose

Driver feedback in [1249](../test_img/1249.png): remove Brackenford's roads to the natural cave and ogre camps,
while retaining town streets, the castle approach and regional connections. Chests, loose loot and encounters stay
in the wilderness. Do not connect every point of interest to the road graph. A natural cave or temporary monster
camp normally needs accessible terrain, not a constructed road. Add a road only when its use fits the setting or the
brief explicitly calls for one. Keep off-road exploration legible through terrain and landmarks. When removing a
road, regenerate its ground masks and junction tiles too; do not leave the former road's dirt stripe or dangling spur.
