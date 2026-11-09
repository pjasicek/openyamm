# Visual calibration from the first generated town

For current new-map instructions start with [Accepted outdoor calibration](OUTDOOR_CALIBRATION.md).
This page retains the original rejected measurements to explain the scale and texture mistakes; the later approved
outdoor result is [the frontage revision](projects/brackenford_greywatch/FRONTAGE_REVISION.md).

Driver feedback, 2026-09-07. This is the default policy for the next generation run and supersedes the first
Brackenford/Greywatch project's extensive outdoor scenario gates. The playable first maps are **not remodeled by
this documentation/catalogue pass**. Their previous functional results do not establish visual acceptance.

Start with the [searchable textured catalogue](catalogues/mm8_ravenshore/index.html), its
[mapping and assemblies](catalogues/mm8_ravenshore/README.md), and the [short review checklist](REVIEW_CHECKLIST.md).
Use [population and composition](POPULATION_AND_COMPOSITION.md) for vegetation, props and terrain placement.

**Applied revision:** [Brackenford's facade revision](projects/brackenford_greywatch/FACADE_REVISION.md) now implements
this feedback in the outdoor map. The earlier measurements below deliberately retain the rejected baseline, stored
under that project's `review/facade_revision/before/`. For the driver's subsequent repetition request, read
[house variety](HOUSE_VARIETY.md): Ravenshore's 44 ordinary houses use 13 forms; the facade-stage town used 15 across five; the accepted infill revision uses 20 across those five.

## Default process: visual reference → prototype → town → quick wiring

1. Read the driver's brief and select a few actual reference buildings by **role, silhouette and size**. Look at
   their isolated textured views and in-game context. Inspect the map plan for streets, slopes and sight lines.
2. Build one compact home, one larger service and one joined service block before populating a town. Start from
   measured door/facade modules. Give each prototype a small palette of compatible wall, door, window, corner,
   cornice and roof textures. Make new geometry within this vocabulary; do not reproduce the reference town layout.
3. Compare the prototype at the **same game-unit scale**, with a ground/eye-height marker and a front/oblique view.
   Inspect the actual images. Reject the largest mismatch, fix it, then capture the same view again. This is the
   main quality gate; a plausible distant silhouette does not excuse a wrong facade at walking distance.
4. Populate with those reviewed forms. Vary orientation toward streets, footprint, roof composition, size appropriate
   to service, and small terrain/step differences. Connect service doors to clear paths. Review a street block before
   filling the entire settlement. Add biome-appropriate foliage/rocks after building and road placement is coherent.
5. Run **one quick native build/readback and static face → event → target check**. Confirm texture keys, declared
   handlers, service/destination IDs, arrival markers and requested content records. Existing project builders already
   provide much of this. Do not build a scenario for every synthetic face binding or reused MM8 service.
6. Deliver the native files, sources and a short visual review with unresolved defects stated. A brief game view is
   useful for appearance; repeated transaction, every-edge travel, refill, timed town-safety and performance scenarios
   are not default generation work. Use focused deeper checks for new runtime/compiler behavior, new mechanisms,
   observed defects or an explicit request. Repository regression requirements still apply to engine changes.

The agent reviews its prototypes itself; these gates do not require waiting for driver approval. Difficulty and
monster density may use the requested best judgment. Do not let a balance audit displace visual iteration.

## Screenshot findings and reference matches

The driver screenshots below are original game views; the catalogue pictures are Blender studies with native
vertices and UVs, neutral lighting, no terrain/actors and independently fitted cameras. Apparent image size is not
a physical scale measurement. Repeated native house forms prevent identifying every resident from appearance alone.

| Driver evidence | Native match / confidence | Instruction for the next run |
| --- | --- | --- |
| [gw_1](../test_img/_levelgen/gw_1.png) | Generated Needful Things; source building model 6 and door model 7 | Replace crate-window and boat-door choices in future prototypes. Calibrate the enlarged door and body separately. |
| [ravenshore_1](../test_img/_levelgen/ravenshore_1.png), [annotated _2](../test_img/_levelgen/ravenshore_2.png) | **Luodrin House, BModel 42**, event 31, house 834; named screenshot and matching geometry | Low chamfered main body, flat roof, narrow polygonal turret; matched wall/window/door panels and cornice. The turret is not a chimney. |
| [ravenshore_3](../test_img/_levelgen/ravenshore_3.png) | `delf_med1` form; **BModel 19 is the Hostel** in this family, event 77, house 900 | Compact chamfered stone body, posts and hipped shingle roof. The screenshot's shape agrees; repeated family members share this appearance. |
| [ravenshore_4](../test_img/_levelgen/ravenshore_4.png) | **Sanctum, parts 107–110**, event 185, house 304 | Religious landmark scale comes from the broad body, tall towers and raised site. Keep a normal entrance panel and a clear road approach. |
| [ravenshore_5](../test_img/_levelgen/ravenshore_5.png) | `delf_poor1` family, e.g. **26**, Jack's Hovel | Shingled upper walls align with the stone base; shallow doorstep and projecting roof. Exact resident cannot be proven from this unlabelled repeated form. |
| [ravenshore_6](../test_img/_levelgen/ravenshore_6.png) | `hcleric_poor1` family, e.g. **10**, Lathius' Home | Very simple rectangular body, low plain roof and coherent door/window panels. No extra architectural clutter is needed. |
| [ravenshore_7](../test_img/_levelgen/ravenshore_7.png) | `delf_rich2` family, e.g. **43**, another Hostel | Larger articulated footprint and hipped roof, normal-sized doors. Asset-family `rich` is not proof of the resident's wealth. |
| [ravenshore_8](../test_img/_levelgen/ravenshore_8.png) | **Kessel's Kantina frontage, 47**, with the neighbouring Gymnasium/Apothecary in **46–49** | Larger joined street block, multiple roof/body levels and tavern sign. It is a tavern/inn-like architectural reference; the service binding is Kessel's Kantina, not Adventurer's Inn. |
| [ravenshore_9](../test_img/_levelgen/ravenshore_9.png) | **Polished Shield 78 + Steele's Vault 79**; full south-east block includes **80** | Distinct armor and bank doors/signs share a block. The other side also has Self Guild, and model 80 has Guild Caravans. Preserve every logical entrance. |

Browse all forms in the contact sheets: [1](catalogues/mm8_ravenshore/images/contact_1.jpg),
[2](catalogues/mm8_ravenshore/images/contact_2.jpg), [3](catalogues/mm8_ravenshore/images/contact_3.jpg),
[4](catalogues/mm8_ravenshore/images/contact_4.jpg). All 84 selected parts were visually reviewed in these sheets;
important joined structures were also reviewed as full assemblies. Partial walls and roofs in an individual card
can be intentional BModel partitioning. Consult the assembly before interpreting an open side as a design feature.

## The Luodrin facade kit: exact textures and application

![Native wall, door, window, roof and service-sign examples](catalogues/mm8_ravenshore/images/texture_roles.png)

| Role | Native key | Bitmap | Application |
| --- | --- | --- | --- |
| Arched wood door | `t14a03` | 128×256 | BModel 42 face 13, event 31. The door and its surrounding wall are one panel. |
| Framed window | `t14a04c` | 128×256 | Window, upper rough wall and lower masonry are baked together; use a facade panel rather than a large floating window rectangle. |
| Plain wall | `t14a01` | 128×256 | Same lower/upper bands as the window/door kit. Align their world height and UV phase. |
| Corner/post variants | `t14a06`, `t14a07` | 128×256 | Place the painted post on the intended edge/corner. These are not arbitrary interchangeable plain walls. |
| Cornice/wall | `t14d01` | 128×256 | The trim is included in the bitmap; inspect which vertical section the face uses. |
| Main flat roof / tower cap | `t14a05b` | 128×128 | Flat main roof and polygonal cap use the native texture spans. Roof form is geometry; surface detail is texture. |
| Turret masonry | `t14c01b` | 128×256 | Narrow polygonal stone shaft attached to the low body. |
| Other coherent doors | `t14c03`, `t14d03` | 128×256 | Related stone/cornice variants, used by other houses and services. Select by the adjoining wall kit. |
| Service signs | `sgArm`, `sgBANK`, `sgWeap`, `sgTvrn` | 64×64 | Small visible signs near the appropriate door. Follow the reference's upper-right placement when facing that frontage. |

The generated facade used `cr_W128b`, a **crate bitmap**, as a window. Its 128×128 image was placed on a 192×256
rectangle. The generated `bdoorb` is demonstrably boat art: the same key appears on the native Wind/Dauntless cabin
parts 113/120. Neither is a suitable default for this town's house kit. This is a specific style rejection, not a
ban on these textures in appropriate boats, crates or other future settings.

For Luodrin's door, the stored UV texel bounds including deltas are `[-256,0] → [-128,256]`: one 128×256 repetition
on a 128×256 face, **1 game unit per texel**. Negative offsets are valid repetition, not a reason to normalize every
face independently. Preserve direction, phase and scale across adjoining panels; inspect seams and corners close up.
Do not manufacture separate wall bands where the native bitmap already carries those bands.

No chimneys are wanted in this requested house vocabulary. An occasional narrow tower, roof wing, porch, doorstep or
joined upper mass gives measured silhouette variety. Do not add decorative geometry merely to make a simple house
appear more detailed. The source cottages with blue-grey roofs and rough rubble walls use a different coherent kit;
they demonstrate variation within Ravenshore, not permission to mix unrelated surfaces on one facade.

## Scale: calibrate modules before overall building size

![Native and generated door panels at equal physical scale](catalogues/mm8_ravenshore/images/door_scale.png)

The catalogue extractor measured vertical visible faces with direct `EnterHouse` bindings and door-like texture
keys. This selects recognizable entrance panels, not broad hint facades or invisible transition planes. Transport
doors that match the selection remain included. It is a local sample, not a rule covering every MM6–MM8 doorway.

| Source | Selected panels | Median width × height, native units |
| --- | --- | --- |
| MM6 New Sorpigal, `oute3` | 36 | 128×256 |
| MM7 Harmondale, `7out02` | 4 | 128×256 |
| MM8 Ravenshore, `out02` | 70 | 128×256; all 70 samples have this size |
| Generated Brackenford, `lg01` | 24 authored service doors | 256×512; all 24 have this size |

The current MM8 outdoor eye-height default is **176 units** (`game/app/GameApplication.cpp`; no movement override
in `assets_dev/worlds/mm8/world.yml`). A native 256-high door is about **1.45 eye heights**; a generated 512-high door
is **2.91**. The generated bitmap is stretched to **2 units per texel**, so its lock, frame and panels also look larger.
Compare from an ordinary ground stance: eye height is relative to the local floor, not absolute world Z.

| Native example | BModel | XYZ bounds size in game units | How to use the measurement |
| --- | --- | --- | --- |
| Lathius' Home | 10 | 672×544×416 | Compact low house prototype. |
| Small Hostel | 19 | 768×896×480 | Chamfered stone house with hipped roof. |
| Jack's Hovel | 26 | 640×832×448 | Shingled upper wall, gable and step. |
| Lott's Family Home | 38 | 768×512×448 | Compact plain alternative. |
| Luodrin House | 42 | 640×896×768 | Height includes the turret; the main body is much lower. |
| Larger Hostel | 43 | 1280×1664×512 | Expanded footprint without an enlarged entrance. |
| Sanctum main body only | 110 | 2048×1792×1024 | Towers are separate parts; inspect the four-part assembly for landmark size. |
| Generated Needful Things body | 6 in `lg01` | 1408×1408×1696 | Includes below-door foundation and turret. Door is separately modeled in part 7. |

All bounds above come from **actual vertices**. Do not use the old diagnostic ODM header-bound field ordering, which
interleaves axes. Do not compare a partial native shop piece against an entire generated building, and do not infer
scale from automatically fitted catalogue thumbnails. Native large homes also exist: the `hcleric_med1` long-house
form reaches 2112×832×608. A uniform 50% shrink of every building would create a different mistake.

For the next town, use a 128×256 house-door panel as the initial module. Choose a compact-home footprint from the
measured examples above, then a different reference for a larger hostel, temple or civic block. Keep ordinary facade
features near their native texel scale while enlarging a service through extra bays, wings, floors or a tower. Compare
floor-to-eave, floor-to-ridge and floor-to-tower-top separately. Keep the doorstep/foundation small enough that the
door meets the finished quantized terrain. A house-talk facade does not need a walk-through opening behind it.

For a camera comparison, record local floor Z, eye offset, horizontal distance to the facade, view direction and FOV.
Use the same settings for the prototype and reference. Preserve the player's configured view distance; fix landform
and architectural scale rather than changing camera settings to conceal the problem.

## Purpose, residents and shared geometry

The extractor follows native BModel face IDs through `out02.scene.yml` face state and `out02.lua` into global
`house_data.txt`. It associates initial `npc.txt` resident candidates and their `npc_topic.txt` topic labels with
that house ID. This gives real service/resident provenance without guessing from a building's appearance.

For example, Luodrin's **face 13 → event 31 → house 834** has **Aerie Luodrin, NPC 112** as its initial resident
candidate, including Expert Sword as a topic. Event **32** only labels other surfaces; it is not another door.
The asset name `delf_rich1` suggests an art category. It does not prove Aerie's wealth or the original designer's
intention. Prefer descriptions such as “towered residence” or “compact cottage”; label narrative interpretations as
inferences. A quest giver need not occupy a mansion. The same named Hostel service appears in two different forms.

The joined block in screenshot 9 is a concrete multi-service example:

| Part / face | Active event | House / service | Sign |
| --- | --- | --- | --- |
| 78 / 5 | 173 | 37, The Polished Shield | Face 19, `sgArm` |
| 79 / 8 | 193 | 282, Steele's Vault | Face 48, `sgBANK` |
| 78 / 42 | 201 | 186, Self Guild, on another frontage | Faces 56/57, `sgSPELL` |
| 80 / 17 | 181 | 452, Guild Caravans (stables) | `SGstabl`; see native card for the full binding |

Use a logical `building/block → service doors[]` manifest. Each service door owns its event and sign even if several
doors share one mesh. Conversely, the Sanctum's four BModels share one establishment; the Adventurer's Inn spans two
parts and has two active doors into the same house. A label-only annex must not become a spurious service entrance.

The catalogue inventories **all 121 native BModels**, renders **83 event-associated parts plus the physically
associated Merchant House tower 56**, and records **67 parts with actual entry faces**. Ten assembly views explain
the joined blocks, temple, inns and boats. Remaining records are retained with their geometry/material/event data;
they have no resolved house/dungeon/transport association. Dungeon exteriors include Dire Wolf Den, Smuggler's Cove,
Merchant House of Alvar, Chapel of Eep, Tomb of Lord Brinne and Escaton's Crystal. A dark cave mouth or invisible
transition face must be interpreted with terrain/context; it is not a house doorway to resize to 128×256.

## Roads, terrain and surrounding props

Wells and fountains belong in **side pockets, gardens or widened squares outside the through-route**. Reserve the
road corridor and door approaches before placing props. Test the full footprint plus clearance against the road
exclusion mask, not only the object's origin. A fountain may organize a square only when clear routes go around it;
placing it on the road centerline and calling the result a square does not satisfy the brief.

At a sloped site, establish finished terrain first, then foundation/steps and the entrance threshold. Check road
continuity to raised services such as the Sanctum. Keep trees and rocks out of door approaches and narrow bridges.
Vary planted pockets and open streets using the existing decoration studies; do not scatter foliage uniformly through
town or use it to hide oversized architecture. Terrain ridges and bends should screen selected views and make journeys
unfold gradually while preserving the configured draw distance. These are visual/placement decisions, not a demand
for a scenario on every street segment.

## Reproduce and extend the catalogue

From the repository root:

```sh
python3 level_generation/scripts/catalogue_ravenshore.py
```

The extractor reads native ODM vertices/faces/UV deltas, applied scene face records, generated event registrations,
house/NPC/topic tables and the generated town's measured door geometry. It records file hashes. It does not execute
Lua: conditions, current quest occupancy and transport availability remain conditional. The MM8 overlay changes
Escaton event 504's condition while retaining its `d10.blv` destination; inspect overlays when extending this method.
Do not edit generated legacy Lua to make the catalogue mapping look simpler.

Use Blender MCP's code execution tool in short batches, keeping the caller's current scene:

```python
from pathlib import Path
p = Path('/home/pjasicek/github/OpenYAMM/level_generation/scripts/blender_building_catalogue.py')
exec(compile(p.read_text(), str(p), 'exec'), {
    'MODEL_IDS': [10, 19, 26, 42],
    'ASSEMBLIES': ['sanctum', 'armor_bank_guild', 'kessels_block'],
})
```

For all parts, take the `catalogue_building` indices from `catalogue.json` in batches of roughly 15–20; render each
`assembly_views[].id` once. The script uses an independently owned **Ravenshore building catalogue** scene, excludes
native invisible faces from beauty views, restores the original active scene in `finally`, and leaves study objects
available. It does not disconnect the MCP addon, restart Blender, clear existing scenes or change map sources.

```sh
python3 level_generation/scripts/build_catalogue_figures.py
python3 level_generation/scripts/validate_building_catalogue.py
python3 level_generation/scripts/build_case_studies.py
```

Open `catalogues/mm8_ravenshore/index.html` locally to search by model, service, resident or family. Markdown cards
list polygon counts, dimensions, texture keys, active/label face IDs and event/house/NPC provenance; JSON retains
every face's bounds, UV texel spans, deltas and texture scale. This is a read-only reference tool, not a new importer
or automatic architecture generator. Its quick validation checks the evidence and links; no game scenarios are
required for producing or updating this catalogue.

## Follow-up: corrected houses still need appropriate density

The driver accepted the revised house art but identified excessive spacing in `test_img/1218.png` versus Ravenshore
`test_img/1219.png`. Read [settlement spacing calibration](SETTLEMENT_DENSITY.md): native nearest-envelope gaps were
1,866 units in Brackenford versus 594 across Ravenshore houses. The density revision reduces Brackenford to 832 without
enlarging the house kit. Measure district spacing and inspect opposing street fronts as a separate visual gate.

## Follow-up: compose the settlement around the sketch

[Sketch layout calibration](SKETCH_LAYOUT_CALIBRATION.md) covers unequal loops, native diagonal roads, raised landmark
approaches, purposeful open pockets and the distinction between good spacing and a convincing composition.
