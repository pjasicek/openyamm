# Generating MM6–MM8 levels with Codex and Blender

For restoring static dungeon and outdoor building textures at 2×/4×, start with the
[texture restoration playbook](terrain/TEXTURE_RESTORATION_PLAYBOOK.md): fresh-art quality checks, shared base
materials, true-alpha foreground layers, connected trims and native scale/continuity validation.

For outdoor minimap replacements, use [registered capture with light terrain noise](minimaps/README.md):
the user-selected New Sorpigal treatment, exact map bounds, retained masters/layers, and icons ledger/deployment workflow.

For outdoor scenery selection, read [the complete decoration calibration](OUTDOOR_DECORATION_CALIBRATION.md)
and [all-42-map catalogue](catalogues/outdoor_decorations/index.html): native asset palettes/locations, local density,
subregion contrasts, meaningful props and deliberate open space. Reuse this evidence when composing new maps.

For enhanced decoration artwork, see the [New Sorpigal restoration example](decorations/mm6_new_sorpigal/README.md):
complete map/frame inventory, AI references, transparent 2x exports, matched interactive states and native-animation
retention. Its comparison viewer includes animated props; the playtest installer uses an explicit map-scoped override.

For restoring decorations or other non-creature BMP sprites across MM6–MM8, use the
[prepared restoration job package](sprites/restoration_jobs/README.md), with exact prompts, palette references,
animation metadata and small resumable batches. Map placement and engine installation remain separate tasks.

Read [regional-transition calibration](REGIONAL_TRANSITION_CALIBRATION.md) for the separate travel/terrain bounds,
roads continuing beyond prompts, optional terrain screening, and focused exit review. Straight open exits are valid;
curves, hills and mountain barriers are not required between neighboring maps.
Roads also need a credible purpose: natural caves, monster camps and treasure normally remain off-road.

The [landscape-detail follow-up](LANDSCAPE_DETAIL_CALIBRATION.md) adds full bridge/terrain contact checks, sparse
native stone-detail tiles, land-normalized scenery heatmaps, rough urban/camp props and optional buff/stat pedestals.
A deck-normal check and global decoration totals alone missed visible defects in the previous revision.

This is the starting instruction for an agent asked to create a new OpenYAMM level, including a vague request such as
“make a cave like Ilsingore's, with two house entrances and a guarded chest.” Turn that request into a playable,
textured, scripted map through a repeatable build and visual review loop. Preserve the reference's design language;
do not assume that copying its topology, event IDs, or difficulty produces the requested experience.

**Tool:** Blender through Blender MCP for inspection, procedural modeling, UVs, materials, semantic markers, and
camera views. OpenYAMM's importers, native map writers, scene metadata, Lua runtime, and gameplay tests provide the
rest of the pipeline. A Blender render is an authoring preview, not proof that a level works in the game.

**Starting Blender:** follow [Blender MCP startup](BLENDER_MCP_STARTUP.md). Agent-launched GUI startup and automatic
connection on port 9876 were verified on this workstation; the driver does not need to open Blender or click Connect.
Reuse an existing working instance. After a restart, retry a stale closed connection once, then verify scene inspection,
Python execution and a viewport screenshot. Interactive MCP requires the GUI process, not `blender --background`.

**Current workflow:** visual authenticity first, with a single quick static wiring/build check. The driver’s
[visual calibration](VISUAL_CALIBRATION.md) supersedes the earlier exhaustive outdoor scenario gates. Ordinary
outdoor face → event → existing service/destination bindings do **not** require per-door, shop transaction, travel,
loot/refill, timed safety or performance scenarios. Use scenarios when changing shared runtime/compiler behavior,
fixing an observed gameplay failure, or explicitly requested. Reuse implemented synthetic events and inspect their
bindings; spend iteration time on scale, texture composition, placement and native-looking views.

The folder contains 15 indoor and 18 outdoor reference studies, a focused Garrote Gorge density supplement, and a detailed
[Ravenshore building catalogue](catalogues/mm8_ravenshore/README.md). The Brackenford/Greywatch project demonstrates
an executed native build/package path; it is not a universal arbitrary-Blender-scene exporter. Its first outdoor
visual result was rejected by the driver despite extensive functional checks. Read the calibration before copying
its proportions or art choices, and [pipeline status](PIPELINE_STATUS.md) for implemented capabilities.

For a new outdoor map, first read [Accepted outdoor calibration](OUTDOOR_CALIBRATION.md). It combines the driver's
accepted house, density, frontage, tile, terrain and decoration findings into the working order below. The approved
Brackenford result is an example; its counts, palette and town layout are not universal targets.

Start with these files:

- [MM5 Castleview–Kalindra](projects/mm5_castleview_kalindra/README.md): source-backed town/regional wireframes,
  shared residents and services, Alvar/Garrote implementation mapping and an in-progress native environment.
  [Goal and completion scope](projects/mm5_castleview_kalindra/GOAL.md),
  [current checkpoint and visual evidence](projects/mm5_castleview_kalindra/PROGRESS.md).
- [Garrote Gorge building catalogue](catalogues/mm8_garrote_gorge/README.md): all 56 native parts, 40 physical assemblies, residents/proprietors, walls, keep, dimensions and material references.
- [Alvar building catalogue](catalogues/mm8_alvar/index.html): all 99 native parts, 68 assemblies, residents/proprietors, joined shops, civic buildings, material references and a [Castleview style comparison](projects/mm5_castleview_kalindra/ALVAR_STYLE_COMPARISON.md).
- [Animated creatures from low-resolution sprites](creatures/SPRITE_TO_3D_WORKFLOW.md): AI-restored references,
  Blender modeling/material iteration, rigging, animation and export review; calibrated through the `m242` ghost.
- [Direct creature sprite restoration](creatures/DIRECT_SPRITE_WORKFLOW.md): combine native frames for one direction
  and animation, AI-enhance the complete sheet, then clean edge colors, extract transparency and review playback.
- [Sprite atlas and selective-variant pipeline](creatures/SPRITE_ATLAS_VARIANTS_PIPELINE.md): concise generation
  recipe, region masks and shade ramps, placement JSON, focused checks, and future shared-renderer changes.
- [Blender MCP startup and reconnect](BLENDER_MCP_STARTUP.md): launch autonomously, verify the connection, preserve scenes.
- [Wilderness calibration](WILDERNESS_CALIBRATION.md): Ravenshore encounter areas and quiet gaps, biome-specific
  scenery coverage, small ponds, bridge assemblies and terrain-embedded cave mouths.
- [Accepted outdoor workflow](OUTDOOR_CALIBRATION.md): apply the complete calibration before planning a new town.
- [Frontage and native tile transitions](FRONTAGE_AND_TILE_CALIBRATION.md): snapped road centers, actual doors,
  single/three-corner artwork, diagonal pairs and local house/garden infill.
- [Visual calibration and scale rules](VISUAL_CALIBRATION.md): driver feedback, exact door/window keys, role-based
  building sizes, unobstructed roads and a faster review process.
- [Ravenshore building catalogue](catalogues/mm8_ravenshore/README.md): isolated textured BModels, active door/event/house
  mappings, resident candidates, facade UVs and multipart service assemblies.
- [House repetition and variety](HOUSE_VARIETY.md): count physical houses, recurring forms and unique service blocks;
  Ravenshore has 44 ordinary houses across 13 forms. Match a comparable repetition ratio when planning the new kit.
- [Settlement spacing and enclosure](SETTLEMENT_DENSITY.md): measure physical-building gaps by district, plan opposing
  street fronts and purposeful courtyards, and compare maps at the same unit scale before population.
- [Case-study index](case_studies/README.md): choose references by topology, art, and mechanics separately.
- [Population and composition](POPULATION_AND_COMPOSITION.md): decorations, biome palettes, varied buildings,
  terrain screening/terraces, native grounding, indoor fixtures and direct-click door/lift controls.
- [Authoring contract](AUTHORING_CONTRACT.md): proposed semantic names, properties, geometry and build outputs.
- [Start and spawn markers](AUTHORING_CONTRACT.md#party-starts-arrivals-and-spawn-markers): default party start,
  separate travel/teleport arrivals, encounters, fixed actors, scripted summons and loose items.
- [Gameplay and scripting](GAMEPLAY_AND_SCRIPTING.md): chests, encounters, bosses, houses, flags, mechanisms, Lua.
- [Review gates](REVIEW_CHECKLIST.md): what to inspect, test, fix, and record before calling the result finished.
- [Brief template](templates/brief.yml) and [iteration log](templates/review.md).
- [Survey report](SURVEY_REPORT.md): completed inspection, validation and evidence limits.

These games combine low-polygon static geometry, repeated bitmap textures, sprite decorations and creatures, modest
lighting, and event-driven interactions. Caves use uneven floors, sloping wall bands and roofs; architectural dungeons
use more regular rooms, corridors and moving geometry. A painted doorway can open a house dialogue without being a
walkable room. A pressure plate, secret face, chest, light, and doorway are different kinds of data even when they share
one visible mesh. Much of the recognizable style comes from proportions, texture scale, restricted palettes and pacing.

Both map types also need scene state, map statistics, events, content registrations, and travel integration. The current
checkout stores the surveyed MM6/MM7 imports in version-8 native containers. World identity and binary version are
separate decisions. “Native” here means native BLV/ODM geometry with OpenYAMM scene/Lua content, not verified compatibility
with an original MM6/MM7/MM8 executable and its EVT/DLV/DDM files.

## Indoor generation: BLV rooms, faces, portals and mechanisms

### 1. Resolve the brief and inspect comparable maps

Create a work directory under `level_generation/projects/<id>/` with `brief.yml`, `source/`, `build/`, and `review/`.
Record the world/mod namespace, target binary version, difficulty, expected traversal time, requested features, and
acceptance criteria. Resolve vague choices using references and state assumptions; ask only about missing decisions
that materially change the user's intended result. Do not pause for approval of routine modeling choices.

Use at least one simple spatial reference and one reference for each unusual requested mechanic. The first recommended
exercise is [Ilsingore's Cave](case_studies/indoor/mm8_d48.md): three occupied sectors, two portals, one bound chest,
one house entrance, and an exterior exit. It is **not** a two-house reference. If the brief asks for two houses, add two
distinct house identities and event bindings intentionally. For a smaller single cavern use
[MM6 Dragon's Lair](case_studies/indoor/mm6_zddb01.md); for lifts and stateful puzzles study the larger examples.

Read the map's study, measured JSON, scene and map-stat row; trace relevant bound events in local Lua and GrayFace's
readable reference scripts. GrayFace is a behavioral reference, not code to copy. Generated legacy Lua is evidence;
never edit it to implement a new map. Inspect overlays when present. Distinguish directly bound handlers, lifecycle
handlers and transitively called events from unused exported templates.

Save and inspect these views before modeling:

1. Orthographic plan, with ceilings excluded and room/sector colors, portals, elevations, exits and interaction IDs.
2. Two opposite isometric cutaways, plus a close view of each important entrance or mechanism.
3. Vertical sections or separate floor plans wherever the top projection overlaps. VARN and Lincoln demonstrate why
   one minimap cannot explain a multilevel dungeon.
4. Eye-height views of entrance, narrow passage, main room, reward approach and return route. Use original textures.

The bundled studies include a plan and one isometric render per map. Generate the extra views needed for the chosen
project. The study script hides ceiling facet types 5/6 in a separate collection; it does not remove walls blocking the
camera. Hide near walls only in a review scene, label the view, and retain the complete playable shell in source.

### 2. Design the route before detailed geometry

Build a room-and-connection graph and a scaled plan together. Give rooms stable semantic IDs, floor elevations,
footprints and intended roles: arrival, orientation, combat, side reward, secret, boss, exit. Mark house faces,
chests, monster groups, moving doors, switches, plates and lights on the plan. Add a state graph for keys, switches,
elevators and quest gates. Every mandatory destination must remain reachable in its intended states, including return.

A custom wireframe is useful as a constrained layout, not as an image that the exporter guesses geometry from. Store
coordinates and graph IDs in structured data; draw the minimap from that data. Use reference proportions to choose
corridor width, party clearance, slope and room size, then test these dimensions in the engine. Do not invent movement
limits from a screenshot. Plan sightlines and encounter pull distances, and avoid putting a boss directly in an arrival
trigger unless requested. Give secret branches a readable clue and a safe return route.

### 3. Make a playable greybox with explicit sectors

Model floors, wall bands and ceilings in Blender using the [contract](AUTHORING_CONTRACT.md). Pre-mark occupied rooms
and portal openings. The compiler must produce sector membership and visibility data deterministically; it must not
infer all room relationships from object bounding boxes. A visual “room” can need several sectors at bends, level
changes or occlusion boundaries. Preserve the empty sector-0 convention and validate links to occupied sectors.

For caves, vary the horizontal cross-section at successive heights: uneven floor perimeter, wider/narrower middle
bands and a sloping crown. Use controlled asymmetric rings and a few large rock masses, not identical vertical
extrusions or noisy displacement everywhere. Keep walkable surfaces and clearances intentional. Split non-planar
polygons into valid planar faces. Avoid cracks, reversed winding, degenerate/sliver faces and accidental vertical steps.

Portals are oriented, non-rendering apertures shared by two known sectors. They do not replace a closed wall or act as
a gameplay door. Model the physical doorway and moving leaf separately. Keep vertices of moving mechanisms independent
from static walls; record movement axis, extent, speed, endpoints and memberships. Start with supported linear motion.
Rotating doors or unusual multi-part mechanisms require verified runtime/compiler support before authoring them.

Compile and load this greybox before spending time on final textures. Test walking, collision, stairs, lifts, portal
culling, targeting and line of sight. Fix source data or the compiler when wrong; do not patch the built BLV by hand.

### 4. Apply the reference's art and gameplay language

Use a short explicit palette of existing texture keys, with verified dimensions and UV scale. Match wall/floor/ceiling
roles and apparent repetition at party eye height. Preserve irregular cave walls while keeping door and chest surfaces
legible. UV seams, texture direction, stretched corners and repeats need close views. Architectural floors often need
grid alignment; cave surfaces benefit from coherent, larger-scale bands. Do not import a photorealistic asset pack by
default. Blender node graphs, procedural materials and normal maps do not automatically become legacy bitmap textures.

Place decorations deliberately: recognizable focal objects, occasional wall pictures, and torches where their supports
and illumination make sense. Use native sprite decorations when appropriate. Use explicit radius/color and sector
ambient values for lighting; check whether a decoration already emits light before adding another source. Inspect in
the engine with the party torch off and on. A bright cutaway with a study sun is not an in-game lighting reference.
The survey found zero explicit lights in d48 and zero-radius imported lights in the sampled MM7 interiors: neither is
a reason to prescribe black rooms or zero-radius lights for new content.

Add gameplay using [the shared gameplay checklist](GAMEPLAY_AND_SCRIPTING.md). Map stats and chest templates together
control random loot; encounter families/weights and placed spawns are separate; stronger named monsters require a
deliberate stat definition and explicit loot behavior. Allocate and bind every interaction, not just the visible
doorways. Secret detection, activation, collision and persistence are separate requirements.

### 5. Export, script, inspect and iterate

Export semantic geometry and a manifest, compile native BLV data and scene state, and emit an event inventory with a
Lua placeholder for **every** interaction and lifecycle hook. The agent then writes the Lua logic. Regeneration must
preserve authored handlers and stable IDs. Missing implementations fail the release validation gate; placeholders
are allowed only in an explicitly marked draft. See the [contract](AUTHORING_CONTRACT.md) for build ownership.

Reopen the written BLV through the runtime reader and compare bounds, faces, texture keys, sectors, portals, mechanisms,
events, spawns and chest bindings against the manifest. Render the **reimported** result as well as the Blender source.
Capture engine views and test the state transitions. After each pass record specific faults with camera/state and fix
the largest gameplay or visual problem first. Repeat until [all relevant review gates](REVIEW_CHECKLIST.md) pass.

Deliver the editable `.blend`, structured brief and manifest, source geometry, native map package, authored Lua,
reproducible build command, event/ID report, screenshots and test results. The user should not need to mark sectors,
repair UVs, wire events, or finish doors manually after export.

## Outdoor generation: ODM heightfield, tiles and BModels

### 1. Choose the landform, tile palette and route network

Study five contrasting kinds of space, not just five grass maps: starter island, settlement/roads, steep mountain,
desert, and hazardous/special environment. The [outdoor case studies](case_studies/README.md#outdoor) cover those cases
across all three worlds. Pick the project's closest landform and settlement references, and inspect both tiled plan
and height heatmap. Add oblique views and ground-level approaches; a top-down texture map hides slopes and blocked roads.

Draft a scaled minimap from structured data: coastline, elevation regions, ridges, valleys, road graph, village lots,
dungeon entrances, wells/fountains, treasure areas, encounter territories and travel anchors. Define foot routes,
optional flight access, bridges and scripted teleport links separately. Dagger Wound's islands and Bracada's local
teleports show why distance on the minimap is not the same as travel cost. Place interesting destinations before detail.

Choose the comparable district separately from the map: market blocks, village lanes, open clusters and enclosed
compounds need different spacing. Record physical assemblies, ordinary instances/forms and deliberate open spaces.
Plan opposing frontage bands with the road graph; avoid equal plots and a long access spur for every house.

### 2. Author native terrain in Blender

**Default to ODM terrain for the continuous ground.** The current renderer and collision system already understand
its heightfield, tile identities and water/lava flags. This is a semantic and compatibility choice; no relative BModel
terrain performance benchmark was performed for this study. Use BModels for buildings, bridges, overhangs and other
shapes a single-valued heightfield cannot represent. Do not duplicate the entire ground as collision-heavy BModels.

The native grid is 128 × 128 height samples with 512 game units between samples and unsigned-byte heights scaled by
32. Game-space coordinates are `X = (gx - 64) * 512`, `Y = (64 - gy) * 512`, `Z = heightByte * 32`, so representable
elevations are 0–8160. The renderer draws 127 × 127 cells from those samples. Preserve the extra boundary samples and
all serialized 128 × 128 tile/attribute entries; do not export a 127 × 127 array accidentally.

Use a constrained grid mesh or resample a sculpt onto this exact lattice. Apply an explicit authoring-to-game transform.
Quantize heights deterministically, report maximum and RMS error, and reject out-of-range values instead of silently
clipping them. Keep the source sculpt if useful, but review the quantized mesh before accepting it. The rendered cell
splits along the anti-diagonal (`fracX + fracY <= 1` selects the first triangle); matching a bilinear preview alone is
insufficient for terrain contact. The [contract](AUTHORING_CONTRACT.md) specifies the proposed authoring properties.

Build large landforms first, then walkable passes and town terraces, then shorelines and local relief. Native terrain
cannot contain caves under the ground or vertical overhangs; use BLV entrances or deliberately bounded BModels there.
Do not “smooth away” the steep relief that makes Nighon or Tularean Forest recognizable, and inspect all required routes in the plan and relevant eye-height views.

### 3. Paint tile identities and make roads continuous

Select the world-appropriate tile table and map terrain-bank lookup. Grass, desert, snow, swamp and volcanic terrain
are tile families with variants and transitions, not arbitrary RGB paint. Assign categorical tile IDs per native cell
using a terrain mask and adjacency rules. Resolve each ID through the runtime's table logic to verify the actual texture
and water/lava/shore/transition flags. A Blender material color or vertex color is not a complete exported tile assignment.

Create roads as a graph with explicit widths and junction types, rasterize to native cells, and select matching straight,
corner, junction and transition tiles available in that palette. Check intersections, slopes, shore crossings and building
thresholds in the resolved tile preview. Settlement paving can use BModel geometry when fine detail requires it, but
avoid coplanar overlap and keep movement/floor behavior valid. Do not use a high-resolution texture painting to hide a
wrong native tile map. Water is tile behavior, not “height equals zero”; lava can carry both water and burn flags.

Before accepting the selector, inspect the actual transition bitmaps: one-corner and three-corner variants can have
misleadingly similar names. Compare both endpoints of adjoining native tile edges independently of the generator's
lookup dictionary. Resolve unsupported material combinations with supported transition collars; inspect road bends,
forks and paired diagonals for painted-strip continuity too. The verified MM8 mapping and its limits are in
[frontage and tile calibration](FRONTAGE_AND_TILE_CALIBRATION.md); verify other worlds/palettes rather than reusing raw IDs.

### 4. Place BModels, sprites and playable content

Select a measured building archetype and its facade kit from the catalogue before populating lots. Keep ordinary
Ravenshore doors near 128 × 256 game units; expand the building body for larger services. House windows are coherent
facade textures, not crate panels. Omit chimneys in this requested style. One establishment may span BModels, and
one BModel may carry multiple service doors; preserve a separate logical door/event per service.

After rasterizing the road, place each house using its actual door center, outward normal and offset. Record ordinary
`street_frontage` versus `dedicated_lane`: ordinary houses usually need only a short unpaved verge, while a deliberately
recessed inn or raised landmark may need a lane. Snap first, then align the final lane with the door; move the house
when the tile grid cannot move the road accurately. Rotate clearance checks with the building and move joined blocks together.

Use separate stable BModel identities for coherent buildings and structural objects, with applied transforms and valid
face winding, UVs, bounds and event bindings. Place foundations against the quantized terrain; inspect buried doorways,
floating corners and road lips. Native terrain supplies ground, BModels supply architecture, sprites supply suitable
trees/decorations, and explicit records supply spawns and lights. Keep their ownership unambiguous.

Plan a village around approach routes, landmarks and service access. House entrances are event faces with house-table
and NPC/dialogue registrations; a dungeon entrance is usually a MoveToMap destination with a safe arrival anchor. Wells,
fountains and obelisks require a visible target, hint, event and scoped state for charges, conditions or quest progress.
Keep wells, fountains, trees and other obstacles off road corridors and door approaches; use side pockets/courtyards.
Place treasure with readable guardians and a return route. Configure map-stat encounter slots plus actual spawn markers;
zero authored actors does not imply a peaceful map. Define unique actors and guaranteed rewards explicitly.

Populate named spaces inside the settlement as well as its perimeter: gardens, court edges, tree pockets, flowers
beside verges and rocks near suitable slopes. Use the local biome's native palette. Inspect accepted counts per group
and sprite silhouettes at eye height; a large global count can coexist with an empty town. Preserve usable openings,
full prop clearances and grounding on final native triangles. See [population and composition](POPULATION_AND_COMPOSITION.md).

Boundary travel needs the existing navigation/travel metadata, destination map, arrival/facing and any world context.
Quickly check destination/arrival records and return bindings without running an outdoor scenario for every edge.
Mark local teleports as local in the manifest even if their Lua uses MoveToMap. Inspect terrain contact, flight access
and water/lava placement visually; execute focused runtime checks only for new behavior or an observed defect. Do not assume indoor door mechanisms can be reused for moving outdoor BModels; verify support or use
a supported scripted interaction/indoor transition and disclose any scope adjustment.

### 5. Compile, round-trip and review at several scales

Build the terrain arrays, native ODM BModels and bounds/indexing, scene entities and spawn/state records, map metadata,
travel integration and event/Lua inventory through authoritative writers. The game draws the terrain from ground
materials only: run `tools/terrain_materials.py weights --world <world> --map <map>.odm` (a map without its material
file does not load; see [Terrain materials](terrain/materials/README.md)). Open the result in OpenYAMM, not just Blender.
Compare the written height/tile/attribute arrays to the intended quantized source; verify palette resolution and BModel
placement after reimport. Validate all interaction bindings and world/package references.

Review a full-map minimap, tiled plan, height heatmap, oblique overview, road/settlement close-ups and player-height route
captures. Evaluate recognizable biome, useful landform, destination spacing, navigation, encounter pacing and reward
placement separately. Inspect the approach and street views before multiplying an unapproved building prototype.
A brief visual walkthrough can help; exhaustive outdoor route scenarios are not a default gate. Repeat using recorded camera positions,
time/lighting and party state so fixes are comparable. Apply [the review gates](REVIEW_CHECKLIST.md) and deliver the same
editable sources, reproducible native package, scripts and evidence as for indoor maps.

## Reproduce and extend the reference inspection

From the repository root, with Python packages NumPy, Matplotlib, Pillow and PyYAML available:

```sh
python3 level_generation/scripts/inspect_references.py
python3 level_generation/scripts/build_case_studies.py
python3 level_generation/scripts/build_overviews.py
python3 level_generation/scripts/validate_references.py
```

The inspector accepts `--kind indoor|outdoor`, `--world mm6|mm7|mm8`, and `--map d48` filters. It reads existing assets
and writes only this folder's evidence. Source hashes are in each JSON. Reinspect changed references; do not assume
an old case study remains an exact description after asset regeneration.

Curated interpretations live in `reference_notes.json`; `build_case_studies.py` combines them with measured data.
Edit those notes when updating a study, then regenerate its Markdown. The validator checks coverage, source hashes,
selected event IDs, missing textures, image presence and local links; it does not execute gameplay. Fresh Blender
renders require MCP execution for each map before rebuilding the Blender overview sheets.

Through Blender MCP `execute_blender_code`, using the checkout's absolute path:

```python
exec(compile(open('/repo/level_generation/scripts/blender_reference_view.py').read(),
             'blender_reference_view.py', 'exec'),
     {'WORLD': 'mm8', 'MAP': 'd48', 'KIND': 'indoor', 'REPO': '/repo'})
```

Run the inspector first. The Blender script creates a separate scene, switches to it, and writes an isometric PNG and
view metadata. It keeps existing scenes, but does not save a `.blend`; save a project file explicitly when authoring.
Use MCP scene/object inspection and viewport screenshots during edits, then open saved renders with the image viewer
to actually assess them. Rerunning creates another scene; manage study scenes deliberately during long sessions.

The evidence previews omit actors and decoration billboards. Blender uses neutral inspection lighting and does not
reproduce animated water, palette transparency or runtime state. The outdoor 2D preview composites magenta-key tile
areas over an approximate water color and substitutes a recorded water animation frame. Its road count is the number
of raw road-bank cells, not a measured road surface area. Event extraction is a direct-binding scan, not Lua execution
or a complete call graph. These limitations are reasons to add engine review, not to hide missing evidence.

Follow repository AGENTS.md. Generate original code; use local OpenEnroth and GrayFace only as structural/behavioral
references. Keep map content world/mod-scoped and shared registries engine-owned. Reference images contain locally
available game art; this study makes no claim that original assets may be redistributed with a new project.

## Follow-up: compose the settlement around the sketch

[Sketch layout calibration](SKETCH_LAYOUT_CALIBRATION.md) covers unequal loops, native diagonal roads, raised landmark
approaches, purposeful open pockets and the distinction between good spacing and a convincing composition.
