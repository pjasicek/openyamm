# Ravenshore — MM8 `out02.odm`

**Study focus:** Ravenshore; regional hub, river routes and dense interaction content

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm8/out02.json) · [Blender view metadata](../../evidence/mm8/out02_blender.json)

## Layout and visual reading

A coastal town and larger rural landscape are connected by roads around a river and high enclosing terrain. Urban density contrasts with fields and encounter areas. Native terrain needs to support bridges and town foundations consistently.

![Measured plan of Ravenshore](../../evidence/mm8/out02.png)

![Blender inspection view of Ravenshore](../../evidence/mm8/out02_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 121 / 6095 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 6400 |
| Master tile / four lookup banks | 0 / 90, 126, 342, 414 |
| Distinct raw tile IDs / raw road-bank cells | 102 / 511 |
| Water-flag / burn-flag cells (may overlap) | 4197 / 0 |
| Native entities / spawn records | 825 / 59 |
| Initial scene actors / chest records | 143 / 20 |
| Directly bound chest slots | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 18, 19 (13 distinct) |
| Directly bound / declared map events | 160 / 185 |
| Selected face flags | secret: 0; invisible: 71; animated: 0; clickable: 5338; pressure_plate: 0; trigger_monster: 1; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `t14b05` (457); `t14c01b` (367); `t14a05` (279); `t14a05b` (252); `btrima1` (244); `bwoodb1` (236); `t14abcd10` (196); `cr_W128b` (172).

Common native tile assignments: `90` → `grastyl` (5297 cells); `126` → `wtrtyl` (3375 cells); `1` → `dirttyl` (953 cells); `162` → `rktyl` (738 cells); `91` → `grastyl` (347 cells); `93` → `grastyl` (337 cells). Full resolution/flags are in the JSON.

Map-stat row: [2 / Ravenshore](../../../assets_dev/engine/data_tables/map_stats.txt#L5).

Treasure **1**, Perception difficulty **1**, disarm **1**, trap d20 count **1**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Human Mercenary | 3 | 2-5 | 0 |
| 2 | Centaur | 1 | 1-3 | 50 |
| 3 | Dire Wolf | 1 | 1-3 | 50 |

## Event behavior to inspect

A large fixed-actor population and many house/event bindings make this a gameplay-density reference. Event 101 grants a temporary stat effect; event 102 is a harmful well, and event 104 combines town-portal/quest-related state with fountain behavior. Do not interpret all SetValue calls as restorative effects.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [101](../../../assets_dev/worlds/mm8/events/maps/out02.lua#L852) | 51 | StatusText |
| [102](../../../assets_dev/worlds/mm8/events/maps/out02.lua#L862) | 51 | StatusText |
| [104](../../../assets_dev/worlds/mm8/events/maps/out02.lua#L871) | 23 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Town gardens cluster small plants near houses, fountains and trees; countryside trees are much more broadly distributed. Buildings range from simple pitched roofs to extended, rounded and towered civic forms. The Shadowspire approach uses a narrow road notch between high rock flanks, screening the destination without relying on shorter draw distance. Follow WILDERNESS_CALIBRATION.md: 59 regular encounter markers (43 wolf, 16 centaur), 65 town actors and 78 normally hidden invasion actors are separate populations. Wolves form tight western patches with broad gaps; centaurs are looser. The den is guarded with a nearby chest, while Smuggler's Cove and Chapel of Eep have quiet approaches. Small native ponds, assembled timber/stone bridges and a tiny terrain-embedded den mouth provide additional composition references. LANDSCAPE_DETAIL_CALIBRATION.md distinguishes dirt/grass embedded-stone variants from boulders, records 12 contextual trash heaps, dec45 Earth Resistance and the dec43 challenge setting with small rock22 stones. Use explicit main-town membership and category heatmaps; inspect the entire bridge span against quantized terrain.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm8/out02_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm8/out02_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm8/out02_decorations.png)

Native entity records: **825**; initially drawable sprite records: **807**; drawable decorations with descriptor light radius: **15**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| plants | 269 |
| trees | 271 |
| rocks | 207 |
| lights | 15 |
| props | 45 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `tree12` | tree | 70 | 16 / 256 | 0 |
| `tree10` | tree | 56 | 16 / 256 | 0 |
| `tree11` | tree | 56 | 16 / 256 | 0 |
| `rock22` | rock | 39 | 16 / 8 | 0 |
| `tree60a` | tree | 38 | 16 / 256 | 0 |
| `plant32` | shrub | 37 | 16 / 8 | 0 |
| `rock17` | rock | 35 | 16 / 8 | 0 |
| `tree62a` | tree | 28 | 16 / 256 | 0 |
| `plant19` | flower | 27 | 16 / 8 | 0 |
| `rock16` | rock | 27 | 16 / 8 | 0 |
| `plant27` | flower | 25 | 16 / 8 | 0 |
| `plant17` | flower | 25 | 16 / 8 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 35 / 271 | 115 | 3 |
| plants | 231 / 269 | 255 | 1 |
| rocks | 90 / 207 | 118 | 7 |
| lights | 13 / 15 | 15 | 0 |
| props | 34 / 45 | 42 | 1 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![town_gardens — annotated native decoration study](../../../level_generation/evidence/mm8/out02_decor_town_gardens.png)

Highlighted source anchors: #469 `tree12` at [13728, -14792, 11]; #479 `plant29` at [16408, -15156, 0]; #322 `rock06` at [16376, -12256, 0]; #814 `dec03` at [11728, -14544, 192].

![rural_grove — annotated native decoration study](../../../level_generation/evidence/mm8/out02_decor_rural_grove.png)

Highlighted source anchors: #96 `tree11` at [-8864, 10656, 1060]; #316 `rock02` at [-8000, 9024, 624].

![shadowspire_pass — annotated native decoration study](../../../level_generation/evidence/mm8/out02_decor_shadowspire_pass.png)

Highlighted source anchors: #670 `tree13` at [18720, 3808, 64]; #331 `rock16` at [18496, -704, 80]; #575 `dec03` at [19152, 1504, 64].

![terrain_enclosure — annotated native decoration study](../../../level_generation/evidence/mm8/out02_decor_terrain_enclosure.png)

Highlighted source anchors: #527 `tree62a` at [-128, 2432, 592]; #640 `plant26` at [8080, -5072, 128]; #636 `rock26` at [-9520, -3824, 369]; #810 `dec25` at [4920, 16224, 534]; #605 `dec30` at [-4992, -15264, 0].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Building, facade and scale calibration

Use the [complete native building catalogue](../../catalogues/mm8_ravenshore/README.md):
all 121 BModels inventoried, active versus label-only faces, house/NPC/service bindings,
84 textured part views and 10 complete/context assemblies. The [calibration](../../VISUAL_CALIBRATION.md)
matches driver screenshots to measured door/window/roof kits and explains the generated town’s scale error.
Use [settlement spacing calibration](../../SETTLEMENT_DENSITY.md) for market/lane density,
opposing fronts and same-scale native plans; count multipart blocks once.
The [house variety measurement](../../HOUSE_VARIETY.md) counts 44 ordinary house/storage instances
across 13 forms, separately from the unique service/landmark assemblies. Match repetition as well as variety.
Approve representative textured prototypes before duplicating them. Keep wells/fountains outside roads.

## Apply to a new map

Keep service, travel, encounter and environmental interaction inventories separate but spatially coordinated. Use the hub's road/river structure to organize destinations, and author clear hints for wells whose behavior differs from ordinary healing. Compare market and lane districts separately, count physical service assemblies once, and keep ordinary doors near the shared road without adding a spur to every home. Inspect actual transition bitmap corners and diagonal joins after native snapping. Place bounded gardens near houses and fountains while keeping a more open countryside; evaluate accepted local placements, not only total foliage. Apply the accepted outdoor calibration with new geometry rather than copying Brackenford or Ravenshore. Distinguish travel bounds from terrain extent: regional roads continue 8,089–9,625 units past Ravenshore/Alvar prompts. Compare open straight/rolling approaches with bent rock cuts. Continue the road beyond the trigger; curvature and screening are optional, and mountains or hills are not required between neighboring maps. Require occlusion only for a deliberately screened pass. See REGIONAL_TRANSITION_CALIBRATION.md.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Test town thresholds and bridges, actual actor crowding/pathing, travel registration, harmful versus helpful wells and their state restoration. Check frame time with real actors and decorations; the static Blender view cannot validate runtime density.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm8/maps/out02.odm](../../../assets_dev/worlds/mm8/maps/out02.odm)
- [assets_dev/worlds/mm8/maps/out02.scene.yml](../../../assets_dev/worlds/mm8/maps/out02.scene.yml)
- [assets_dev/worlds/mm8/events/maps/out02.lua](../../../assets_dev/worlds/mm8/events/maps/out02.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data.txt](../../../assets_dev/engine/data_tables/terrain_tile_data.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Out02.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Out02.txt)
- [assets_dev/worlds/mm8/events/maps/out02_mmmerge.lua](../../../assets_dev/worlds/mm8/events/maps/out02_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
