# Alvar — MM8 `out03.odm`

**Study focus:** Alvar; conifer countryside, town planting and the Murmurwoods pass

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm8/out03.json) · [Blender view metadata](../../evidence/mm8/out03_blender.json)

## Layout and visual reading

Broad woodland and developed pockets are separated by water and substantial rock landforms. The westward road toward Murmurwoods passes through a narrow notch rather than crossing an exposed summit.

![Measured plan of Alvar](../../evidence/mm8/out03.png)

![Blender inspection view of Alvar](../../evidence/mm8/out03_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 99 / 5315 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 4064 |
| Master tile / four lookup banks | 0 / 90, 126, 342, 414 |
| Distinct raw tile IDs / raw road-bank cells | 99 / 514 |
| Water-flag / burn-flag cells (may overlap) | 1138 / 0 |
| Native entities / spawn records | 1043 / 65 |
| Initial scene actors / chest records | 26 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 5, 6, 7, 8, 10, 11 (10 distinct) |
| Directly bound / declared map events | 121 / 169 |
| Selected face flags | secret: 0; invisible: 72; animated: 0; clickable: 4468; pressure_plate: 2; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `t05a05` (483); `GWSPOTWL` (366); `T05a11` (337); `T05a10` (321); `HHR1P` (266); `T05a01c` (230); `Trim9_32` (223); `Trim9_32a` (187).

Common native tile assignments: `90` → `grastyl` (7669 cells); `162` → `rktyl` (1762 cells); `126` → `wtrtyl` (923 cells); `1` → `dirttyl` (809 cells); `109` → `grdrts` (298 cells); `108` → `grdrtn` (292 cells). Full resolution/flags are in the JSON.

Map-stat row: [3 / Alvar](../../../assets_dev/engine/data_tables/map_stats.txt#L6).

Treasure **1**, Perception difficulty **2**, disarm **2**, trap d20 count **1**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Dark Elf Warrior | 2 | 1-3 | 0 |
| 2 | Ogre Warrior | 1 | 1-3 | 50 |
| 3 | Wasp Warrior | 1 | 1-3 | 50 |

## Event behavior to inspect

The MM8 map navigation row links west to out07, east to out04 and south to out02. Preserve the correct side-specific arrival pose, time and heading when designing equivalent new routes.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [11](../../../assets_dev/worlds/mm8/events/maps/out03.lua#L144) | 1 | EnterHouse; houses: 509 |
| [12](../../../assets_dev/worlds/mm8/events/maps/out03.lua#L148) | 93 | none |
| [13](../../../assets_dev/worlds/mm8/events/maps/out03.lua#L150) | 1 | EnterHouse; houses: 510 |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

The countryside inventory is dominated by tree29/tree30 with a secondary leafy-tree family, while small plants and props supply other local accents. The west road threads a gap beside water and high rock. Screen the route with its flanks; do not assume that an imposing pass requires an exposed high road crest. Landscape-detail follow-up compares main-town/edge/wilderness heatmaps and sparse interior stone variants. dec26 cauldrons and dec46 Day of the Gods pedestal provide native camp/landmark references. Exclude distant southwestern rural houses when defining the main-town hull.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm8/out03_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm8/out03_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm8/out03_decorations.png)

Native entity records: **1043**; initially drawable sprite records: **1038**; drawable decorations with descriptor light radius: **5**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| trees | 616 |
| plants | 288 |
| rocks | 88 |
| props | 41 |
| lights | 5 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `tree29` | pine tree | 346 | 16 / 256 | 0 |
| `tree30` | pine tree | 112 | 16 / 256 | 0 |
| `plant27` | flower | 80 | 16 / 8 | 0 |
| `plant26` | flower | 59 | 16 / 8 | 0 |
| `tree10` | tree | 58 | 16 / 256 | 0 |
| `tree11` | tree | 58 | 16 / 256 | 0 |
| `tree12` | tree | 41 | 16 / 256 | 0 |
| `rock17` | rock | 41 | 16 / 8 | 0 |
| `plant22` | flower | 41 | 16 / 8 | 0 |
| `plant23` | flower | 35 | 16 / 8 | 0 |
| `plant17` | flower | 24 | 16 / 8 | 0 |
| `dec03` | dec03 | 20 | 16 / 64 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 28 / 616 | 422 | 12 |
| plants | 49 / 288 | 282 | 4 |
| rocks | 53 / 88 | 76 | 0 |
| lights | 0 / 5 | 5 | 0 |
| props | 36 / 41 | 38 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![town — annotated native decoration study](../../../level_generation/evidence/mm8/out03_decor_town.png)

Highlighted source anchors: #723 `dec23` at [15040, 12648, 128]; #725 `dec23` at [14216, 9672, 128]; #720 `dec23` at [17384, 13736, 128].

![murmurwoods_pass — annotated native decoration study](../../../level_generation/evidence/mm8/out03_decor_murmurwoods_pass.png)

Highlighted source anchors: #507 `tree11` at [-19776, -6656, 192]; #714 `dec23` at [-19144, 984, 1024].

![terrain_enclosure — annotated native decoration study](../../../level_generation/evidence/mm8/out03_decor_terrain_enclosure.png)

Highlighted source anchors: #492 `tree10` at [160, -160, 448]; #655 `plant09` at [-7360, 11704, 448]; #766 `rock28` at [6400, 15776, 288]; #715 `dec26` at [-6952, -14104, 178]; #710 `dec23` at [-19080, 1344, 1024].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Let terrain flanks screen a regional road while keeping its floor traversable. Separate the town planting palette from the larger woodland population and keep nearby landmarks legible. Distinguish travel bounds from terrain extent: regional roads continue 8,089–9,625 units past Ravenshore/Alvar prompts. Compare open straight/rolling approaches with bent rock cuts. Continue the road beyond the trigger; curvature and screening are optional, and mountains or hills are not required between neighboring maps. Require occlusion only for a deliberately screened pass. See REGIONAL_TRANSITION_CALIBRATION.md.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Review the west notch from both directions at eye height, road grade and terrain tile joins, and actual travel/return behavior. Do not infer walkability solely from the isometric.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm8/maps/out03.odm](../../../assets_dev/worlds/mm8/maps/out03.odm)
- [assets_dev/worlds/mm8/maps/out03.scene.yml](../../../assets_dev/worlds/mm8/maps/out03.scene.yml)
- [assets_dev/worlds/mm8/events/maps/out03.lua](../../../assets_dev/worlds/mm8/events/maps/out03.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data.txt](../../../assets_dev/engine/data_tables/terrain_tile_data.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Out03.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Out03.txt)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
