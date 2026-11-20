# Ironsand Desert — MM8 `out04.odm`

**Study focus:** Ironsand Desert; volcanic basin, sparse town and cave access

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm8/out04.json) · [Blender view metadata](../../evidence/mm8/out04_blender.json)

## Layout and visual reading

A large lava basin dominates the terrain, with desert ridges, sparse settlement and roads around its margins. The asymmetry gives the landscape a strong landmark. This is the outdoor context for the d48 cave study.

![Measured plan of Ironsand Desert](../../evidence/mm8/out04.png)

![Blender inspection view of Ironsand Desert](../../evidence/mm8/out04_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 48 / 2391 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 4064 |
| Master tile / four lookup banks | 0 / 594, 558, 450, 522 |
| Distinct raw tile IDs / raw road-bank cells | 84 / 222 |
| Water-flag / burn-flag cells (may overlap) | 2725 / 2725 |
| Native entities / spawn records | 585 / 74 |
| Initial scene actors / chest records | 33 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 (11 distinct) |
| Directly bound / declared map events | 50 / 79 |
| Selected face flags | secret: 0; invisible: 6; animated: 0; clickable: 2294; pressure_plate: 0; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `Trim9_32` (197); `PlnTyl` (146); `t13a10b` (145); `t13b10a` (145); `t13b11c` (128); `gn_mtl03` (126); `T65B04` (104); `gt002b` (92).

Common native tile assignments: `90` → `plsatyl` (3868 cells); `162` → `plntyl` (3498 cells); `126` → `lavtyl` (2215 cells); `165` → `plntyl` (513 cells); `164` → `plntyl` (491 cells); `163` → `plntyl` (451 cells). Full resolution/flags are in the JSON.

Map-stat row: [4 / Ironsand Desert](../../../assets_dev/engine/data_tables/map_stats.txt#L7).

Treasure **2**, Perception difficulty **3**, disarm **3**, trap d20 count **2**, refill **336 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Gog | 1 | 1-3 | 50 |
| 2 | Troll | 2 | 1-3 | 0 |
| 3 | Cyclops | 2 | 1-3 | 50 |

## Event behavior to inspect

Travel handlers connect local sites including d48 and the elemental-fire route. Event 150 is the obelisk interaction. The resolved terrain has 2725 water-flagged cells and the same 2725 burn-flagged cells: lava can carry both flags, so these are overlapping counts rather than separate water and lava regions.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [150](../../../assets_dev/worlds/mm8/events/maps/out04.lua#L289) | 8 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Cactus variants, dry trees, bones and skeletons establish a harsh desert character. Small rocks and sparse vegetation surround paths and ruined structures, with open sand preserving their silhouettes. The numerous skeleton props are contextual storytelling and should not be imported into a healthy grassland town.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm8/out04_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm8/out04_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm8/out04_decorations.png)

Native entity records: **585**; initially drawable sprite records: **582**; drawable decorations with descriptor light radius: **5**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| plants | 126 |
| rocks | 225 |
| trees | 81 |
| props | 145 |
| lights | 5 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `dec05` | skeleton | 118 | 16 / 8 | 0 |
| `plant54` | cactus | 60 | 16 / 64 | 0 |
| `rock07` | rock | 55 | 16 / 8 | 0 |
| `plant50` | cactus | 46 | 16 / 64 | 0 |
| `rock09` | rock | 39 | 16 / 8 | 0 |
| `rock30` | rock | 39 | 16 / 8 | 0 |
| `rock16` | rock | 36 | 16 / 8 | 0 |
| `rock18` | rock | 33 | 16 / 8 | 0 |
| `tree15` | tree | 29 | 16 / 256 | 0 |
| `tree20` | tree | 28 | 16 / 256 | 0 |
| `tree14` | tree | 24 | 16 / 256 | 0 |
| `rock10` | boulder | 10 | 16 / 24 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 0 / 81 | 3 | 48 |
| plants | 3 / 126 | 39 | 5 |
| rocks | 8 / 225 | 58 | 43 |
| lights | 3 / 5 | 4 | 0 |
| props | 40 / 145 | 54 | 18 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm8/out04_decor_settlement.png)

Highlighted source anchors: #228 `rock30` at [-4736, 4352, 128]; #415 `dec05` at [-4608, 7424, 128].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm8/out04_decor_landscape.png)

Highlighted source anchors: #531 `plant54` at [1952, 448, 466]; #203 `rock18` at [-1024, -1792, 752]; #449 `dec21` at [3600, 1952, 235].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Author volcanic landform and safe approach routes before placing the village and dungeon entrance. Use the native volcanic tile banks and validate hazard flags independently of material appearance. Preserve a clear, safe cave arrival/return anchor.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Walk the settlement-to-cave route and return, inspect lava shoreline/contact behavior, test all intended travel destinations and validate guarded chest placement against encounter territories. Magenta shore outlines in the Blender render are a preview limitation, not a missing texture report.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm8/maps/out04.odm](../../../assets_dev/worlds/mm8/maps/out04.odm)
- [assets_dev/worlds/mm8/maps/out04.scene.yml](../../../assets_dev/worlds/mm8/maps/out04.scene.yml)
- [assets_dev/worlds/mm8/events/maps/out04.lua](../../../assets_dev/worlds/mm8/events/maps/out04.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data.txt](../../../assets_dev/engine/data_tables/terrain_tile_data.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/OUT04.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/OUT04.txt)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
