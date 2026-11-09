# Goal: complete Castleview–Kalindra ODM and prepare the MM5 world

Status: **complete — all five milestones accepted on 2026-09-09**.

The accepted environment contains **326 independently authored BModels, 121 placeholder handlers and 728 entities
including the party-start marker**, with all 45 premises and 31 separate source features represented. There are no
actors or spawn records. [Consolidated acceptance evidence](COMPLETION.md) links local and regional game reviews,
all 24 native readback audits, the corrected gate decks and the final native minimap.

Native SHA-256: `87c61c78629b56761ad46ff0280d35a5129238f6f34b3f576f5b49e107e57f24`.
The [v9 minimap](review/native_minimap_v9/source_review.json) and [refreshed starting save](review/playtest/latest.json)
match it. The [accepted release](delivery/latest.json) has a persistent [play.sh](play.sh) launcher and installation under `local_playtest/`.
[Final installed entry, map-book, population and reload evidence](review/delivery_final/runtime_review.json) passes.
See [progress](PROGRESS.md), [rebuild instructions](REBUILD.md) and [delivery instructions](DELIVERY.md).

## Objective and completion boundary

Produce the complete first MM5 outdoor region, **Castleview–Kalindra / SW**, as a textured, walkable native ODM in
OpenYAMM, with all exterior architecture, terrain, water, roads, foliage, decorations and Lua interaction wiring.
Prepare a real `mm5` world mount and an isolated test installation that opens this map.

This goal implements the previously proposed steps 1–5 with the user's revised scope:

- Finish the **whole outdoor region**, including every town premises and countryside destination. The representative
  street is an intermediate visual check, not the final deliverable.
- Create all required BModels independently, using Alvar/Garrote textures and architectural references.
- Place **no NPC actors, monster actors, encounters or monster spawn points**. NPC/dialogue population is deferred.
- Wire intended clickable doors and entrances to authored, map-local Lua. A real click must reach its handler and show
  feedback such as `Milken Savings: not implemented yet.` Actual residents, dialogue and services are deferred.
- Finish the environment to the calibrated visual standard. Placeholder gameplay does not permit placeholder building
  boxes, absent roofs/props, untextured terrain or unfinished scenery buffers in the final result.

The result is an **environment-complete, gameplay-placeholder map**. Functional quests, scripted residents and connected
BLVs are not completion requirements for this milestone. Creating this document does not start map generation or claim
that a native map, world package or runtime evidence already exists.

## Authoritative inputs and calibration

Use the current source-backed design and preserve its semantic identities:

- [Project scope](README.md), [structured layout](layout.json), [resident assignments](RESIDENTS.md),
  [source objects](source_objects.json) and [attached interior contacts](interior_contacts.json).
- [Alvar comparison](ALVAR_STYLE_COMPARISON.md), [candidate measurements](alvar_style_candidates.json),
  [Garrote mapping](GARROTE_STYLE_MAPPING.md), and their linked Alvar/Garrote/Ravenshore catalogues.
- [Landscape specification](LANDSCAPE.md), [heightfield metadata](landscape/terrain.json),
  [decoration placements](landscape/decorations.json), [buffer contract](landscape/buffer.json) and
  [buffer scenery](landscape/buffer_scenery.json).
- [World integration findings](WORLD_INTEGRATION.md), interpreted according to this goal's reduced gameplay scope.
- [Implementation architecture](implementation/ARCHITECTURE.md) and [structured specification](implementation/architecture.json)
  consolidate the accepted Alvar civilian / Garrote fortified assignment over the historical all-Garrote sketch.

Follow these workflow references:

- [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md), [visual calibration](../../VISUAL_CALIBRATION.md),
  [house variety](../../HOUSE_VARIETY.md) and [settlement density](../../SETTLEMENT_DENSITY.md).
- [Sketch layout](../../SKETCH_LAYOUT_CALIBRATION.md), [frontage and tiles](../../FRONTAGE_AND_TILE_CALIBRATION.md),
  [landscape detail](../../LANDSCAPE_DETAIL_CALIBRATION.md) and [regional transitions](../../REGIONAL_TRANSITION_CALIBRATION.md).
- [Pipeline status](../../PIPELINE_STATUS.md), [authoring contract](../../AUTHORING_CONTRACT.md) and
  [Brackenford rebuild path](../brackenford_greywatch/REBUILD.md).
- [Complete outdoor decoration calibration](../../OUTDOOR_DECORATION_CALIBRATION.md): select local palettes and
  purposeful compositions, review accepted placements and preserve deliberate open spaces.

This user-defined scope supersedes earlier proposals to require functional services, reward effects, a local quest,
NPC append support or exhaustive gameplay scenarios in steps 1–5. Brackenford's counts, raw terrain IDs and
project-specific art restrictions remain reference evidence, not universal MM5 requirements.

## Required complete environment

### Geography, water, roads and buffers

- Cover A3/A4/B3/B4 and the embedded Castleview town. Preserve the source-derived relationships of Kalindra, the river,
  Acid Pond, northern shelves, Dark Grove and all other named regional sites.
- Use native ODM ground: 128×128 stored samples, 512-unit spacing, 32-unit height quantization and 127×127 rendered
  quads. Preserve required serialized tile/attribute entries and the native triangle split.
- Keep travel bounds at X/Y ±24,576. Rendered terrain bounds are X −32,768…32,256 and Y −32,256…32,768. Finish the
  outer scenery buffer as part of the map, including its roads, ground materials, heights and foliage.
- Sample neighbouring A2/B2 to the north, C3/C4 to the east and C2 at the northeast corner. Acid Pond continues north
  and the river east. Continue the original western/southern void rim; do not invent an ocean.
- Convert material masks into actual supported terrain-bank selections. Resolve grass/dirt/rock/desert, the small
  scorched fringe and water against real bitmap artwork and mounted asset lookup. Handle unsupported material joins
  intentionally. An RGB preview is not an exported tile assignment.
- Use native water/shore rendering and flags. The starting river and Acid Pond levels are 256 and 768. Water behavior
  must not be inferred merely from terrain height or a blue preview colour.
- Preserve the irregular road graph and its purpose. Do not pave a lane to every natural cave, temporary camp or reward.
  Continue the eastern trade road through the travel boundary to the rendered edge; retain the northern off-road approach.
- Rasterize native roads before final door/frontage placement. Inspect corners, forks, diagonal pairs and shoreline joins.
  Fit actual foundations, steps, terraces and bridge landings to quantized terrain.
- Finish both bridge spans and their bank approaches. Check the entire deck width/length, abutments and rail feet against
  native terrain, not just two endpoint heights.
- Default minimaps/automaps and region-review HTML show only the travel-area crop, including its water and void.
  Provide a separate full-terrain authoring view. The crop is not a walkability mask.

The heightfield and positions are the starting design, not immutable coordinates if native tiles or authored geometry
expose a defect. Make bounded, purposeful source corrections and regenerate affected pads, doors, scenery and previews.
Document meaningful deviations; do not silently redesign the town or move the travel boundary to hide unfinished terrain.

### Architecture and destinations

- Account for all **24 town assemblies** and **21 countryside destinations** in a completion inventory. Natural sites,
  groves, sanctuaries, camps, caves and ropes receive appropriate environmental treatment rather than invented houses.
- Consolidate the implementation mapping: Alvar for most civilian architecture, Garrote for walls, gates, jail and royal
  fortifications. Preserve quality differences, shared households, distinct venues, working yards and useful courts.
- Create a coherent kit of recurring domestic forms, longer/shared homes, joined work/service premises and rarer civic
  landmarks. Resolve the eight oversized Alvar references by recomposition. Check the fourteen apparent footprint fits
  against actual roofs, doors and terrain; a bounding-box fit alone does not approve a placement.
- Keep ordinary doors near the measured 128×256 native scale. Add/remove wall bays, rooms and roof volumes instead of
  uniformly scaling an entire building or stretching facade textures.
- Author roofs, facade bands, corners, windows, doors, foundations, annexes and visible service props. Original Alvar,
  Garrote or Ravenshore BModels may be inspected/rendered as references, but must not be copied, transformed or
  retextured into the new MM5 buildings.
- Complete the irregular Castleview curtain, towers and **both south and west gates**, with usable passages and streets.
  Both gates remain traversable for this milestone. Preserve future pass conditions in the design without implementing
  the pass quest or trapping the test party behind a placeholder handler.
- Complete Castle Kalindra's friendly restored exterior and Ellinger's distinct tower. Initial targets above their pads
  remain Kalindra roof 2,560 / principal towers 3,584, and Ellinger 3,072. Refine silhouettes in context while retaining
  that hierarchy. Restoration/quest visibility states remain documented and deferred.
- Finish the Western Tower, mine, troll holes, sewer outfall/connectors, caravan yard and other planned exterior sites.
  Separate BLVs and walkable indoor rooms are outside this goal; their entrances and future return markers are included.

### Foliage and decorations

- Populate all planned environmental groups: town gardens/verges, orchard, Dark Grove, southern woods, dry shelves,
  countryside sites and outer buffer. Respect deliberate quiet areas and clear sightlines.
- The current baseline is **467 playable-area decoration records and 231 buffer scenery records**. These are inventories,
  not density quotas. Refit accepted placements after final architecture and inspect local coverage rather than totals alone.
- Preserve **all 55 source orchard identities**, including their future ordinary/food/reward distinctions. Their gameplay
  is deferred; do not substitute an arbitrary cosmetic tree count for the source inventory.
- Include the central HP-fountain geometry, secret back-court well, six stat barrels, benches, stock props and visible
  outdoor chests/landmarks already assigned in the plan. Interior beds and puzzle-chest arrangements remain attached-
  interior design records; do not scatter them outdoors merely to satisfy a count.
- Resolve native foliage/decoration names, sprite scale, visual/collision bounds and native-triangle grounding. Build the
  custom architectural props independently. Include subtle compatible terrain detail and contextual yard/camp scenery.
- Keep actual door approaches, roads, gate passages, bridge decks, foundations, arrival clearings and interaction standing
  spaces usable. Required destinations stay inside the travel envelope; buffer placements are scenery only.

## Interaction contract: real Lua dispatch, placeholder gameplay

Maintain a source inventory mapping:

`semantic premises / venue ID → authored object and active face → exported event ID → map-local Lua handler`.

Retain future resident/service identities alongside this mapping without instantiating those NPCs or services.

1. Every intended clickable house/service door and dungeon entrance has a meaningful hover label, active native
   interaction face and resolvable local handler. Explicitly distinguish decorative doors/windows in the inventory.
2. Distinct venues within one building retain distinct handlers. Multiple residents sharing one venue do not imply
   multiple exterior doors or dummy NPC definitions. Several faces may intentionally dispatch to the same venue.
3. Use normal authored map Lua. A handler may call the existing API, for example
   `evt.StatusText("Milken Savings: not implemented yet.")`. Feedback identifies the selected premises. A label-only
   face, generic map-load message or test calling Lua directly does not by itself prove native click wiring.
4. Do not enter original MM8 houses as stand-ins. Do not transition to original dungeons, nonexistent MM5 interiors or
   unrelated test maps. Purchasing, teaching, recruitment and dialogue trees are deferred.
5. Use the same explicit placeholder policy for planned interactive props in this milestone: fountain, charity well,
   stat barrels, source reward trees, chests and quest sites retain their future rules but grant no rewards yet. Inspect
   native descriptors so implicit MM8 global effects do not bypass a local stub. Use supported instance-local bindings
   or authoring data; never disable shared native effects globally to achieve this.
6. Preserve distinct regional, dungeon-return, mirror, rope and tower-roof arrival markers in source data. Activate only
   arrivals needed for the standalone map. Unbuilt routes get explicit unavailable feedback or supported cancellation
   behavior, leaving the party on valid terrain. Preserve future destinations and unresolved travel days; do not invent
   zero-day routes or attempt to load missing maps.
7. Placeholder clicks do not alter gold, HP, stats, items, QBits or future quest progress. Dummy global NPC/house/topic
   rows and quest bits are not necessary merely to display local status text.
8. Regeneration preserves authored handlers and stable semantic IDs. Generate numeric model/face assignments from source;
   do not patch native output or edit generated legacy MM6–8 Lua.

Placeholder behavior is intentional completion for this milestone. Keep full future interaction/quest rules in the
planning data, and report them as deferred rather than implemented.

## MM5 world and ownership

Prepare a real world using the supported manifest, asset mounting and map-loading architecture:

```text
assets_dev/worlds/mm5/
  world.yml
  maps/mm5_sw.odm
  maps/mm5_sw.scene.yml
  events/maps/mm5_sw.lua
  ... required presentation and genuinely world-local assets
```

`mm5_sw` is the intended basename, subject to loader/exporter naming constraints and collision checks. Preserve the
semantic identity `mm5:sw` if another physical filename proves necessary.

- Resolve donor textures, sprites and terrain banks through supported dependencies and canonical ownership. Catalogue
  labels are not automatically working asset aliases in an MM5 mount.
- Register the map, display/start metadata, minimap, navigation bounds and required lookup data using supported
  composition/staging. The supplied test setup must explicitly open the world as MM5. Replacing an original MM8 map
  with the new ODM is not completion.
- Keep one authoritative engine/base registry. Do not introduce world-owned copies of whole NPC, house or gameplay
  tables. Use an explicit isolated composed base when required by the existing staging path.
- **Generic NPC/dialogue append support is not a prerequisite** for status-only handlers. Implement only mounting and
  map/asset registration support required here; defer NPC population and broader dialogue registry work.
- Collision-check and record numeric registrations actually needed. Do not reuse Brackenford ranges by assumption or
  allocate future quest/NPC ranges merely to make a placeholder package look complete.
- Supply an isolated test installation with its own settings/saves and a reliable party start outside the south gate.
  Preserve existing worlds, ordinary starts, unrelated workspace changes and earlier snapshots.

## Explicit population exclusion

The exported map and test setup have **zero NPC actors, zero monster actors and zero runtime monster spawn records**.
Disable random encounters and inherited on-load, refill, timer, summon or invasion behavior for this map through its
own authoritative content settings. Do not accidentally inherit populated MM8 scene data or encounter defaults.

Keep original source-monster records, future encounter areas and resident assignments in planning data only.
Editor-only population markers must be excluded from runtime export. A test party is required to explore the map and
is not an NPC population. Houses and camps may look inhabited while containing no actors.

## Execution milestones: complete all five

### 1. Consolidate the architectural specification

- [x] Record the chosen material families and Alvar/Garrote assignment for every premises.
- [x] Define recurring new forms, complete footprints, roofs, transformed doors, quality and venue ownership.
- [x] Recompose oversized examples while preserving all town/countryside/source-interaction identities.
- [x] Establish reproducible source/build/review paths and the placeholder/population policy.

[Specification audit and retained identity evidence](review/architecture_specification/README.md) establish milestone 1;
final native placement and contextual appearance remain in the later milestones.

### 2. Build complete native terrain and architectural blockout

- [x] Resolve the full terrain grid, material/road/shore tiles, water flags and scenery buffers.
- [x] Place every building/fortification/landmark mass at its actual site, including Kalindra and both gates.
- [x] Snap roads, then fit doors/frontages, foundations, steps and both bridge approaches.
- [x] Compile and reopen an initial native map to expose source/export/scale problems early.

[Current native build and readbacks](review/native/build.json), [exact written geometry/entity preservation](review/region_composition_v1/native_readback.json)
and [native terrain/building overviews](review/native_minimap_v9/source_review.json) establish milestone 2.
Final scene composition, remaining player-view checks and delivery remain in milestones 3–5.

### 3. Calibrate a representative section, then finish the entire environment

- [x] Finish the south-gate/guild/forge/training group, a modest shared home and fountain-court sample in context.
- [x] Review native texture scale, roof forms, door/window proportions, street density and terrain contact.
- [x] Correct the reusable kit, then finish **all remaining town and countryside exterior architecture**.
- [x] Complete region-wide foliage, props, source orchard identities, bridges and outer scenery.
- [x] Remove runtime greyboxes/diagnostic objects; retain labelled historical review evidence separately.

### 4. Review the exported map at native and player scale

- [x] Build from a fresh source package and reopen the written ODM/scene data; do not reuse stale binary geometry.
- [x] Check arrays, texture resolution, tile joins, actual door approaches, winding and complete prop grounding.
- [x] Inspect main streets, both gates, public courts, raised sites, castle approach, crossings, countryside landmarks
  and regional exits from normal game viewpoints.
- [x] Inspect buffer continuation without shortening view distance or moving travel bounds to conceal defects. Flying
  views are useful diagnostics, not a promise of an infinite mesh at every altitude.
- [x] Generate the final native minimap with the travel-area crop and a separate full-terrain review.

### 5. Mount MM5, wire placeholders and deliver

- [x] Install the complete map in a valid MM5 world with resolved dependencies and the correct initial arrival.
- [x] Export the interaction inventory; wire every intended door/entrance to its corresponding local Lua stub.
- [x] Apply the placeholder policy to interactive props and unavailable routes without inherited rewards.
- [x] Confirm zero runtime NPCs, monsters, encounters/spawn records and population-producing scripts/defaults.
- [x] Demonstrate real representative clicks and unavailable-route behavior; save/reload the standalone map.
- [x] Deliver editable sources, native/runtime outputs, rebuild instructions, review evidence and an isolated test
  launcher/package with dependency and build provenance.

Do not stop after the sample street, an empty MM5 mount or Blender-only previews. All five milestones deliver the
complete outdoor environment and its deliberately limited Lua behavior.

## Completion evidence and focused checks

Follow the calibrated visual-first loop. One full static/readback audit should establish:

- All 24 town assemblies and 21 regional destinations are accounted for, with artifact links and natural/non-building
  interpretations explicit. BModel count may exceed assembly count and is not a target by itself.
- Every declared interaction resolves to real native faces/instances and its intended Lua handler, with no accidental
  venue collisions, missing functions, original-world destinations or unbound intended doors.
- Native arrays, texture keys, tile transitions, transforms, world dependencies and navigation bounds are valid.
  Water continuity and the full outer buffer appear in the exported map.
- Full bridge/prop/foundation contact and clear access routes are checked against native triangles.
- Every runtime population channel is empty/disabled; future population data remains outside runtime export.

Use actual game clicks for representative single-house, shared-building/distinct-venue, service and dungeon-entry
placeholders, an interactive prop and an unavailable outgoing route. Show the matching status feedback and absence of
unintended travel/reward/population effects. A small handler smoke check can cover every registered stub without a
separate gameplay scenario for every door. Check a normal save/reload for map/world stability.

Use focused unit/runtime checks when changing shared compiler, loader or interaction behavior, or fixing an observed
failure. Validate affected existing-world paths alongside shared changes. Unchanged service, combat, quest and loot
systems do not require exhaustive testing for this environment-only milestone.

Keep a completion inventory, binding report, population audit, build/source provenance and labelled plan/oblique/
player-height images in this project. Missing required geometry, broken click dispatch, a non-loading MM5 mount or
accidental population prevents completion. Record unresolved issues rather than declaring success from a render alone.

## Deferred to the gameplay phase

- NPC actors, dialogue portraits, greetings/topics, resident scripts and recruitment.
- Functional shops, teachers, bank/guild services, economy and MM5 skill conversions.
- Monster definitions/population, encounters, combat balance, spawning, invasions and respawn design.
- Quests, restoration/pass logic, rewards, chest contents, stat/HP/gold effects and their saved progression.
- Playable dungeon BLVs, other surface regions, Skyroads, elemental planes and working cross-region travel.

Preserve their existing identities, spatial reservations and behavior notes so later gameplay work can bind them
without redistributing the residents or rebuilding the environment.
