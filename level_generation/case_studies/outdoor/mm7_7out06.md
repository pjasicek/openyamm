# The Bracada Desert — MM7 `7out06.odm`

**Study focus:** Bracada Desert; broken plateaus and local teleport network

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm7/7out06.json) · [Blender view metadata](../../evidence/mm7/7out06_blender.json)

## Layout and visual reading

A fractured plateau landscape and desert patches support widely separated built sites. Ground distance and apparent proximity are unreliable guides to travel because height changes and local teleport links shape the route network.

![Measured plan of The Bracada Desert](../../evidence/mm7/7out06.png)

![Blender inspection view of The Bracada Desert](../../evidence/mm7/7out06_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 94 / 4776 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 2400 |
| Master tile / four lookup banks | 1 / 306, 126, 234, 414 |
| Distinct raw tile IDs / raw road-bank cells | 94 / 102 |
| Water-flag / burn-flag cells (may overlap) | 1164 / 0 |
| Native entities / spawn records | 264 / 49 |
| Initial scene actors / chest records | 31 / 20 |
| Directly bound chest slots | 0, 1, 2, 3, 4, 19 (6 distinct) |
| Directly bound / declared map events | 75 / 99 |
| Selected face flags | secret: 0; invisible: 133; animated: 0; clickable: 3587; pressure_plate: 21; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `Hwm2WALL` (588); `7t1butt` (328); `TRIM1_32a` (320); `HWP1Rf` (299); `HWM2RF` (252); `7t1books1` (246); `Tws1d` (240); `7t1beds2` (237).

Common native tile assignments: `162` → `7sand` (4624 cells); `1` → `7dirttyl` (3368 cells); `90` → `7wastetile` (1103 cells); `126` → `7wtrtyl` (776 cells); `108` → `7wstdrtn` (371 cells); `109` → `7wstdrts` (350 cells). Full resolution/flags are in the JSON.

Map-stat row: [67 / The Bracada Desert](../../../assets_dev/engine/data_tables/map_stats.txt#L70).

Treasure **2**, Perception difficulty **6**, disarm **6**, trap d20 count **3**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Golem | 2 | 1-3 | 50 |
| 2 | Griffin | 2 | 1-3 | 50 |
| 3 | 0 | 1 | 1-3 | 0 |

## Event behavior to inspect

Numerous MoveToMap handlers include local travel, so a count of those calls is not a count of exits. Event 452 is an inventory/quest-gated altar interaction with a sprite-state change; event 453 is an obelisk. Both require more than a decorative model.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [452](../../../assets_dev/worlds/mm7/events/maps/7out06.lua#L450) | 25 | ForPlayer, SetSprite |
| [453](../../../assets_dev/worlds/mm7/events/maps/7out06.lua#L461) | 24 | ForPlayer, StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Dry shrubs and cactus-like sprites punctuate broad yellow ground and stepped rocky shelves. Narrow raised routes carry buildings and landmarks. Keep steep exposed faces relatively spare and place small plants on believable ledges; do not cover the terrain structure with a forest palette.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm7/7out06_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm7/7out06_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm7/7out06_decorations.png)

Native entity records: **264**; initially drawable sprite records: **260**; drawable decorations with descriptor light radius: **3**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| plants | 204 |
| rocks | 53 |
| lights | 3 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `bush14` | cactus | 81 | 40 / 96 | 0 |
| `bush13` | cactus | 43 | 40 / 96 | 0 |
| `bush16` | cactus | 31 | 40 / 96 | 0 |
| `7rock09` | rock | 29 | 0 / 0 | 0 |
| `bush15` | cactus | 25 | 40 / 96 | 0 |
| `bush10` | cactus | 24 | 40 / 96 | 0 |
| `7rock08` | rock | 24 | 0 / 0 | 0 |
| `dec61` | beacon fire | 1 | 64 / 160 | 128 |
| `dec65` | magic pedastal | 1 | 64 / 190 | 64 |
| `dec67` | magic pedastal | 1 | 64 / 190 | 64 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| plants | 7 / 204 | 176 | 4 |
| rocks | 2 / 53 | 49 | 0 |
| lights | 2 / 3 | 3 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm7/7out06_decor_settlement.png)

Highlighted source anchors: #203 `bush10` at [-4832, 13312, 0]; #228 `7rock09` at [-5920, 11200, 0]; #263 `dec67` at [-7376, 12976, 0].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm7/7out06_decor_landscape.png)

Highlighted source anchors: #106 `bush13` at [4224, -1408, 800]; #76 `bush14` at [2688, -4992, 800]; #184 `bush10` at [5216, 2304, 22].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Maintain a transport graph alongside roads and terrain paths. Label every teleport's source, target, facing and return relation, and define which destinations are reachable without flight. Use prominent sites to make the fractured landscape legible.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Test every local teleport and return, arrival collision, foot-only routes and altar state before/after the required item. Verify the obelisk's global progress separately from local map variables.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm7/maps/7out06.odm](../../../assets_dev/worlds/mm7/maps/7out06.odm)
- [assets_dev/worlds/mm7/maps/7out06.scene.yml](../../../assets_dev/worlds/mm7/maps/7out06.scene.yml)
- [assets_dev/worlds/mm7/events/maps/7out06.lua](../../../assets_dev/worlds/mm7/events/maps/7out06.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_2.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_2.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT06.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT06.txt)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
