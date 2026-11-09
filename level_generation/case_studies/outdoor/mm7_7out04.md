# The Tularean Forest — MM7 `7out04.odm`

**Study focus:** Tularean Forest; strong relief, water and forest settlement

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm7/7out04.json) · [Blender view metadata](../../evidence/mm7/7out04_blender.json)

## Layout and visual reading

Steep raised terrain contrasts with low routes, an island/water region and built connections. Tree decoration density is central to the forest experience but is absent from this terrain/BModel-only preview; terrain shape alone is only part of the reference.

![Measured plan of The Tularean Forest](../../evidence/mm7/7out04.png)

![Blender inspection view of The Tularean Forest](../../evidence/mm7/7out04_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 128 / 6905 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 8000 |
| Master tile / four lookup banks | 1 / 90, 126, 162, 414 |
| Distinct raw tile IDs / raw road-bank cells | 74 / 260 |
| Water-flag / burn-flag cells (may overlap) | 6396 / 0 |
| Native entities / spawn records | 469 / 54 |
| Initial scene actors / chest records | 35 / 20 |
| Directly bound chest slots | 0, 1, 2, 3, 4, 5, 6 (7 distinct) |
| Directly bound / declared map events | 83 / 104 |
| Selected face flags | secret: 0; invisible: 263; animated: 0; clickable: 2985; pressure_plate: 3; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `TRIM2_32` (1183); `Her1rf` (741); `7t1books1` (582); `CHB1` (488); `7t1beds2` (429); `7trimd` (391); `7gt003a` (233); `7t1beds` (217).

Common native tile assignments: `90` → `7grastyl` (6453 cells); `126` → `7wtrtyl` (5170 cells); `128` → `7wtrtyl` (363 cells); `127` → `7wtrtyl` (314 cells); `129` → `7wtrtyl` (307 cells); `1` → `7dirttyl` (241 cells). Full resolution/flags are in the JSON.

Map-stat row: [65 / The Tularean Forest](../../../assets_dev/engine/data_tables/map_stats.txt#L68).

Treasure **1**, Perception difficulty **4**, disarm **4**, trap d20 count **2**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Treant | 1 | 1-1 | 0 |
| 2 | Elf Spearman | 2 | 1-3 | 100 |
| 3 | Fighter Chain | 2 | 1-3 | 0 |

## Event behavior to inspect

The map includes house access, wells/fountains and seasonal decoration changes. Encounter families can be listed with zero random weight while still participating through explicit content. Read placement and event state together with map stats.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [202](../../../assets_dev/worlds/mm7/events/maps/7out04.lua#L396) | 1 | StatusText |
| [203](../../../assets_dev/worlds/mm7/events/maps/7out04.lua#L415) | 20 | none |
| [204](../../../assets_dev/worlds/mm7/events/maps/7out04.lua#L417) | 1 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Oversized trees and raised platforms dominate the settlement view; houses differ in roof and footprint while sharing the local style. Stairs, ramps and bridges link distinct elevations. Preserve open land below and between platforms and use trees as compositional masses, not a substitute for valid support geometry.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm7/7out04_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm7/7out04_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm7/7out04_decorations.png)

Native entity records: **469**; initially drawable sprite records: **465**; drawable decorations with descriptor light radius: **3**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| lights | 7 |
| props | 3 |
| rocks | 35 |
| plants | 188 |
| trees | 232 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `7tree25` | tree | 144 | 96 / 96 | 0 |
| `bush03` | bush | 102 | 0 / 0 | 0 |
| `7tree07` | tree | 73 | 96 / 96 | 0 |
| `flower05` | flower | 47 | 0 / 0 | 0 |
| `flower03` | flower | 25 | 0 / 0 | 0 |
| `7rock01` | rock | 24 | 0 / 0 | 0 |
| `tree37` | tree | 10 | 96 / 96 | 0 |
| `plant01a` | plant | 8 | 0 / 0 | 0 |
| `7rock09` | rock | 7 | 0 / 0 | 0 |
| `plant11a` | plant | 6 | 0 / 0 | 0 |
| `7dec02` | campfire | 4 | 52 / 52 | 0 |
| `7rock08` | rock | 4 | 0 / 0 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 50 / 232 | 98 | 37 |
| plants | 75 / 188 | 94 | 9 |
| rocks | 26 / 35 | 25 | 0 |
| lights | 6 / 7 | 7 | 0 |
| props | 0 / 3 | 3 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm7/7out04_decor_settlement.png)

Highlighted source anchors: #241 `7tree07` at [-13616, -11712, 1084]; #59 `flower05` at [-16144, -8736, 1144]; #392 `7rock01` at [-15392, -11648, 1024].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm7/7out04_decor_landscape.png)

Highlighted source anchors: #285 `7tree25` at [-1376, -4416, 1260]; #33 `flower03` at [-272, -2896, 1860]; #5 `7dec02` at [1168, -4896, 1056].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Plan the ground routes and bridge connections before tree distribution. Use density masks to preserve sightlines and service access when adding native tree sprites. Keep high ridges purposeful, with explicit intended foot and flight routes.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Check terrain/bridge contact, travel connectivity, sprite occlusion at player height and seasonal variants. Verify actual water/shore flags and low/high elevation accessibility instead of treating all green terrain as traversable.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm7/maps/7out04.odm](../../../assets_dev/worlds/mm7/maps/7out04.odm)
- [assets_dev/worlds/mm7/maps/7out04.scene.yml](../../../assets_dev/worlds/mm7/maps/7out04.scene.yml)
- [assets_dev/worlds/mm7/events/maps/7out04.lua](../../../assets_dev/worlds/mm7/events/maps/7out04.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_2.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_2.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT04.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT04.txt)
- [assets_dev/worlds/mm7/events/maps/7out04_mmmerge.lua](../../../assets_dev/worlds/mm7/events/maps/7out04_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
