# Population, buildings and landform

The [complete outdoor-decoration calibration](OUTDOOR_DECORATION_CALIBRATION.md) extends the selected studies below
to all 42 mounted MM6–MM8 ODMs. Use its interactive asset/location index for biome subregions, local coverage,
bare/snow/container variants and scenery groups with an explicit purpose. Historical counts below retain their
older broad categories; the new survey separates flowers, bare trees/stumps, ritual props and effects.

The [landscape-detail follow-up](LANDSCAPE_DETAIL_CALIBRATION.md) adds full bridge/terrain contact checks, sparse
native stone-detail tiles, land-normalized scenery heatmaps, rough urban/camp props and optional buff/stat pedestals.
A deck-normal check and global decoration totals alone missed visible defects in the previous revision.

Use this alongside the [generation playbook](README.md), [authoring contract](AUTHORING_CONTRACT.md) and
[case studies](case_studies/README.md). It records the 2026-09-07 review of all 30 original references plus
Harmondale, Alvar and Murmurwoods. Each case now includes a native decoration inventory, placement plot and
annotated Blender captures. The interpretations below describe what the arrangement suggests; they are not
claims about documented historical author intent.

## Inspect the whole visual vocabulary

Count and inspect four distinct things: native decoration sprites, modeled props, decorated face textures and
lights. A barrel, fountain, wall picture or torch can belong to different categories in different maps. A native
entity record can instead be a party start, hidden prop, fire/smoke emitter or gameplay target. Do not turn every
record into a visible mesh, infer zero detail from zero sprites, or export proxy markers as collision geometry.

Resolve decoration names and aliases through the active merged `decoration_data.txt`, retaining the descriptor
ID, native name, sprite family, collision radius/height, light radius/color, flags, event and initial visibility.
The numeric table row is one greater than the runtime descriptor index. A raw legacy index is not a substitute
for the authoritative name resolution. Resolve the frame table and world palette before judging colors or scale.
Sprite pixel size times frame scale determines the visible size; descriptor height is not a replacement for it.

Read the case's measured JSON and capture metadata. Inspect the highlighted sprite at its actual coordinates,
then compare the room/settlement context and full placement plan. Check initial hidden records and relevant
lifecycle/events when the brief involves restoration, flooding, lights or destruction. Balthazar's Lair, for example,
has 48 hidden brazier records in addition to its initially drawable population. Dagger Wound also has smoke
emitters that are not represented by the static first-frame sprite previews.

The study views use native source geometry and first-frame art, decoded palettes and alpha, with inspection
lighting. Indoor images label any height cut. They do not simulate gameplay lighting, animation, actors,
particles or post-load event state. Source anchors may be partly covered by a wall or tiny at this scale. Use a
closer/opposite view where needed. Complete-ceiling runtime views remain required for a generated map.

## Outdoor population by place and biome

The [wilderness follow-up](WILDERNESS_CALIBRATION.md) compares Ravenshore, Ravage Roaming and Shadowspire,
separates encounter markers from actors and conditional invasions, and measures coverage rather than global totals.
Use it to plan distinct hostile areas, quiet ground, pond margins and guarded/unguarded dungeon approaches.

Start with spatial masks for usable land, water, road clearance, town plots, gardens, wilderness groups, exposed
rock, slopes, encounters and landmarks. Author major groups deliberately; use deterministic variation inside those
groups. A seed and a global scatter density alone do not express a settlement or a biome.

| Context | Reference reading | Generation approach |
| --- | --- | --- |
| Town garden/civic pocket | Ravenshore plants cluster around houses and fountains; Erathia has a distinct dense garden | Place a few bounded beds or loose plant groups, with one or two suitable trees; keep the door approach and walking line open |
| Ordinary street | New Sorpigal and Free Haven combine open streets with occasional trees beside buildings | Orient houses toward approaches; use small accents at setbacks and corners rather than a tree at every doorway |
| Town edge | Harmondale and Ironfist use strong terrain edges and greener spaces outside built plots | Transition from tended pockets to loose groups; preserve views of the gateway and next road segment |
| Temperate countryside | Ravenshore has broadly spaced trees; Murmurwoods has much denser mixed woodland | Use coherent species, uneven groups and intentional clearings; do not impose woodland density on every grassland |
| Tropical coast | Dagger Wound combines multiple palms, tropical plants and varied thatch forms | Keep a tropical palette; place groups on viable land beside paths, buildings and shore shelves |
| Snow/high country | Frozen Highlands and Nighon use snow trees and sparse rocky open areas | Match species/art to terrain material and exposure; retain clear rock and snow surfaces |
| Desert | Dragonsand combines cactus-labelled plant families with fan-palm-like `6tree21`; Bracada uses cactus/yucca-like families, including branching silhouettes; Ironsand adds bones and ruined structures | Choose a specific desert reference palette, fitting rocks and deliberate empty ground; keep death/ruin props tied to a narrative location |
| Unnatural/barren region | Shadowspire uses bare trees/rune posts; Plane of Fire has no drawable decoration sprites | Let the chosen material, terrain and architecture carry the scene; vegetation is not mandatory |

The Ravenshore measurement illustrates why placement context matters: 231/269 plant sprites are within 1,024
units of a BModel XY bounding box, versus 35/271 trees. Also, 255/269 plants lie on source triangles with grade
at most 0.125, versus 115/271 trees. These are observations, **not universal quotas**. Bounding boxes include
non-building BModels; grade is rise/run, not an angle. Dagger Wound and Harmondale place more vegetation on
slopes, so a blanket “no vegetation on slopes” rule would also be wrong.

For each authored placement, sample the native triangle height after terrain quantization. Ground a tree, plant or
rock at the surface it actually occupies; use a BModel surface for a terrace or roof prop. Inspect from two low
directions for floating roots, buried plants and billboards cutting through slopes. Keep larger silhouettes on
credible ground or ledges; steep exposed faces generally need terrain texture and a few deliberate rock accents.
Do not rotate a camera-facing billboard to pretend it conforms to the ground like a mesh.

Wells and fountains belong beside the road in a courtyard, garden pocket or side of a square. Keep the whole
prop footprint plus approach clearance outside the road corridor; a clear origin point is not enough. Keep roads
and door approaches unobstructed by trees, rocks, props or oversized steps. Reserve that exclusion mask before
scatter and road rasterization, then inspect the resulting plan and street view.

Reserve clearance for the party, actor radius, doors, bridge, travel arrivals, loot interaction and combat routes.
Small ground plants may be visually harmless while a descriptor's collision radius still blocks movement. Inspect
and test the chosen descriptor flags; do not globally disable decoration collision to conceal poor placement.

### Calibration from the accepted town

The [accepted outdoor revision](projects/brackenford_greywatch/FRONTAGE_REVISION.md) needed planting within the town,
not only perimeter gardens and distant groves. Plan bounded groups for each intended court edge, rear garden, verge
or slope accent, then record requested versus accepted placements and rejection reasons. If a group stays empty,
revisit its location or role instead of shrinking all clearances. Avoid uniform tree rows and identical flower patches.

Review large sprite crowns as well as collision radii: a clear trunk can still hide a door or important landmark.
Keep usable fountain space and short door approaches. Distinguish accepted empty space from an unpopulated site;
open ground is appropriate where the biome or the district calls for it. Recompute grounding and exclusions after
moving houses or changing roads. Apply [the full calibrated workflow](OUTDOOR_CALIBRATION.md) before scattering.

## Building variety within a coherent style

Make a small family of source forms before populating the town. The references repeatedly combine compact houses,
long halls, L/U-shaped or extended plans, round/octagonal forms and larger civic landmarks. Roof ridge direction,
height, porch, annex and foundation treatment vary within a related material palette. Omit chimneys in the
requested Ravenshore house style; narrow towers/turrets are a separate massing feature. Use the
[Ravenshore catalogue](catalogues/mm8_ravenshore/README.md) for exact facade/door/window kits and measured scale.

For a town of roughly 24 buildings, a useful starting brief is four to six ordinary forms plus distinct civic,
stable and temple/service landmarks. This is a design choice for the new map, not a measured original-game rule.
Choose measured prototype sizes by role and parcel shape. Ordinary Ravenshore doors are 128×256 units in
the measured kit; their window/blank/door facade panels already encode aligned lower/upper material bands.
Do not stretch crate faces into windows or default boat doors into town houses. Approve a small residence, a
larger service and a joined block at the same physical scale before expanding to the whole town. Avoid both a field of
identical boxes and unrelated architectural styles at every plot.

Orient the main entrance toward its approach, road or courtyard. Rotation must transform the entire building,
event face, entrance normal, doorstep and test pose together. Build road spurs from those actual door positions.
Use local flat pads beneath buildings, with sloped streets or a few connected shelves between town blocks.
Recompute foundation depth and threshold clearance after terrain changes. An isometric can conceal a doorway
facing away from the road, a buried foundation or an unwalkable step.

Give the imposing dungeon exterior an original recognizable silhouette: massing, height hierarchy, roof/trim,
entry court and approach. Reusing MM8 textures does not require copying an entire castle BModel. Keep the cave
entrance integrated into the terrain's rock mass, with an irregular mouth and clear approach rather than a loose
rectangular facade.

## Terrain as a sequence of views

Plan the terrain's large forms before small noise: town basin/shelves, river valley, woodland fold, loot clearings,
castle shoulder and regional passages. Sketch what should be visible from each important route position. Use
ridges, spurs and bends to reveal destinations progressively while preserving the engine's current view distance.
Do not hide an unfinished map by reducing draw distance or increasing fog.

The Ravenshore–Shadowspire and Alvar–Murmurwoods captures show narrow road notches with high rock flanks. An
imposing passage need not put the road on a high exposed crest. Record a centerline height profile and usable
width, then compare it with the flanking heights. Include both sides of the transition, arrival pose, camera heading
and retreat space. Native navigation rows and events still have to bind the destination and return route.

Harmondale demonstrates local town shelves inside a larger enclosing landform. Tularean Forest demonstrates
raised platforms and linked circulation, which requires proper support/bridge geometry as well as terrain.
Use these distinctions intentionally. Native ODM terrain remains a 128×128 heightfield: 512-unit XY spacing and
32-unit height quantization. Terrain cannot contain caves, vertical overhangs or arbitrary stacked surfaces;
use native BModels for those features and verify the joins.

Review height contours, native material/tile transitions, the complete map, close street views and eye-height
approaches. Reject checkerboard road joins, sudden terrain steps across roads, exposed bridge undersides, uniform
rolling noise that does not screen anything, and useful landmarks hidden behind accidental hill placement.

## Indoor decoration, material continuity and controls

Choose props by room purpose: an armory needs organized storage, a records room shelves/table-like forms, a
barracks domestic fixtures, a cave perhaps bones or a small campfire. Inspect original modeled furnishings before
assuming each should be a sprite. Preserve the room's usable floor and combat lanes; leave some spaces spare.
MM7's dragon lair uses a small entry-side bone group, while MM8 Ilsingore's Cave has no drawable decoration sprites.

Use torch/brazier spacing to reinforce turns, thresholds, important walls and destinations. Naga Vault uses 20
dec56 torch sprites, while its tables/containers are geometry. Keep visual fixtures, descriptor emission and explicit
map lights distinct. A light radius copied blindly into every room can overlap, leak or flatten the scene.
Compare native ambient values, explicit radius and source placement, then inspect the generated map with its
complete ceiling, normal settings and light on/off state where applicable.

Maintain wall/floor/trim continuity across ordinary connected rooms. A special entry material should communicate
a real change of construction or environment, not an arbitrary first-room exception. A cave-to-fortress threshold
can justify a change; review it at eye height and keep the transition deliberate.

Ordinary doors should open by clicking their visible leaf. Buttons belong to deliberate puzzles, remote gates or
necessary call/return controls. A moving leaf may retract out of reach, so explicitly design how it can be closed or
reopened from both sides. Avoid trapping the party to satisfy a purely visual preference.

A lift pressure plate can share the button's event. Make repeated contact safe: check platform endpoint/motion,
use an occupancy/contact latch or an explicit call direction, and avoid toggling on every contact frame. Test
boarding, travel, disembarkation, return calling and save/load during motion with actors active. Keep pressure-plate
trap/secret flags and Perception behavior separate from the visible floor texture.

## Author, export, inspect, iterate

1. Select reference palettes and groups; record native asset IDs and why each belongs in that location.
2. Store placement rules, exclusion masks, building variants/orientations, terrain centerlines and fixed accents in
   the structured source plan. Preserve stable semantic/runtime IDs as the scene evolves.
3. Author the forms and markers through Blender MCP. Inspect a plan, street/room close views and route perspectives
   with the actual decoration art visible. Correct placement before increasing density.
4. Export native terrain/BModels or BLV geometry plus native decoration/entity/light records. Reopen the native files
   and compare counts, coordinates, identities, flags and events against the source. No manual binary repairs.
5. Inspect reimported visual output and useful in-game views. For ordinary outdoor content, one quick static
   face/event/target check is enough; do not run per-house scenarios, timed town safety or FPS audits by default.
   Reserve focused runtime checks for new behavior or observed defects. If performance is specifically investigated,
   measure comparable workloads rather than inferring cost from BModel/triangle counts.
6. Record each rejected image or route with location, reason and source fix. Rebuild and rerun affected checks.
   A populated Blender render does not certify untested gameplay; record that limit without inventing a broad test gate.

## Reproduce the reference evidence

Run `python3 level_generation/scripts/inspect_decoration_references.py` from the repository. It writes all 33
inventories, decoded native first frames and placement plots; `--map mm8/out02` restricts it to one reference.
The inventory uses the native map, scene initial overrides, merged decoration table and common sprite frame table.
It does not execute Lua or infer city limits from geometry.

Through Blender MCP, execute the existing reference-view script with the decoration extension enabled:

```python
exec(compile(open('/home/pjasicek/github/OpenYAMM/level_generation/scripts/blender_reference_view.py').read(),
             'blender_reference_view.py', 'exec'),
     {'WORLD': 'mm8', 'MAP': 'out02', 'KIND': 'outdoor',
      'REPO': '/home/pjasicek/github/OpenYAMM', 'DECORATION_REVIEW': True})
```

Use the user's actual goal verbatim in the tool's `user_prompt`. Explicit camera poses live in
[decoration_views.json](decoration_views.json); other views are selected from source geometry/decorations.
Inspect the saved images, correct a poor pose or section, and rerender. Preserve user authoring scenes when
disposing of temporary reference scenes. Update `reference_notes.json`, run `build_case_studies.py`, then
`validate_references.py`. The validator checks artifacts and provenance, not gameplay.

## Settlement spaces before population

Use [SETTLEMENT_DENSITY.md](SETTLEMENT_DENSITY.md) before scatter: compact streets, open villages and fortified courtyards
need different patterns. Establish house groups and intentional open pockets first; trees cannot rescue oversized empty
plots. Move residents, guards, gardens, props and arrival approaches with a revised town layout.
