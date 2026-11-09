# Emerald Island — MM7 `7out01.odm`

**Study focus:** Emerald Island; small playable island inside the full terrain grid

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm7/7out01.json) · [Blender view metadata](../../evidence/mm7/7out01_blender.json)

## Layout and visual reading

A small island occupies a tiny portion of the fixed-size ocean grid. Its local settlement, landmarks and cave approach need a zoomed plan; the full-map render is useful for coastline scale but insufficient for placement quality.

![Measured plan of Emerald Island](../../evidence/mm7/7out01.png)

![Blender inspection view of Emerald Island](../../evidence/mm7/7out01_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 98 / 3905 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 2176 |
| Master tile / four lookup banks | 1 / 90, 126, 270, 414 |
| Distinct raw tile IDs / raw road-bank cells | 80 / 67 |
| Water-flag / burn-flag cells (may overlap) | 15193 / 0 |
| Native entities / spawn records | 147 / 11 |
| Initial scene actors / chest records | 32 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 6, 7 (6 distinct) |
| Directly bound / declared map events | 73 / 87 |
| Selected face flags | secret: 0; invisible: 116; animated: 0; clickable: 2415; pressure_plate: 21; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `Trim11_32` (381); `TRIM2_32a` (361); `Hhm3ch` (294); `7t1books1` (247); `TRIM2_32` (244); `7t1beds2` (199); `7t1beds` (197); `Cwb1` (193).

Common native tile assignments: `126` → `7wtrtyl` (6119 cells); `128` → `7wtrtyl` (3028 cells); `127` → `7wtrtyl` (2954 cells); `129` → `7wtrtyl` (2423 cells); `90` → `7grastyl` (353 cells); `136` → `7wtrtyl` (96 cells). Full resolution/flags are in the JSON.

Map-stat row: [62 / Emerald Island](../../../assets_dev/engine/data_tables/map_stats.txt#L65).

Treasure **0**, Perception difficulty **0**, disarm **0**, trap d20 count **1**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Dragonfly | 1 | 2-5 | 100 |
| 2 | 0 | 1 | 1-3 | 0 |
| 3 | 0 | 1 | 1-3 | 0 |

## Event behavior to inspect

Scavenger-hunt NPC interactions are a major part of the map. Events 110/112 illustrate temporary resistance and healing behavior. Six chest slots are directly bound. Many clickable faces reuse a much smaller set of event identities.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [110](../../../assets_dev/worlds/mm7/events/maps/7out01.lua#L254) | 1 | StatusText |
| [112](../../../assets_dev/worlds/mm7/events/maps/7out01.lua#L269) | 1 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

The small settlement uses varied house silhouettes, isolated trees and planted pockets around services. Shorelines and the raised waterfall bank constrain the available land. Keep the central approach and water edge legible; use plants to mark small civic spaces without hiding doors.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm7/7out01_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm7/7out01_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm7/7out01_decorations.png)

Native entity records: **147**; initially drawable sprite records: **141**; drawable decorations with descriptor light radius: **4**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| lights | 6 |
| rocks | 22 |
| plants | 51 |
| props | 9 |
| trees | 53 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `flower10` | flower | 16 | 0 / 0 | 0 |
| `flower01` | flower | 14 | 0 / 0 | 0 |
| `7tree04` | tree | 14 | 96 / 96 | 0 |
| `7rock09` | rock | 12 | 0 / 0 | 0 |
| `tree65` | tree | 11 | 96 / 96 | 0 |
| `7rock08` | rock | 10 | 0 / 0 | 0 |
| `flower09` | flower | 10 | 0 / 0 | 0 |
| `7tree01` | tree | 10 | 96 / 96 | 0 |
| `7dec33` | buoy | 9 | 52 / 52 | 0 |
| `7tree10` | tree | 8 | 96 / 96 | 0 |
| `flower03` | flower | 6 | 0 / 0 | 0 |
| `tree60` | tree | 6 | 96 / 96 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 18 / 53 | 37 | 0 |
| plants | 42 / 51 | 38 | 0 |
| rocks | 10 / 22 | 18 | 1 |
| lights | 4 / 6 | 2 | 0 |
| props | 0 / 9 | 9 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm7/7out01_decor_settlement.png)

Highlighted source anchors: #64 `7tree10` at [9904, 8464, 104]; #25 `flower09` at [12448, 8880, 33]; #8 `7rock08` at [8224, 5568, 0].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm7/7out01_decor_landscape.png)

Highlighted source anchors: #34 `7dec33` at [-992, 5216, 0].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Budget playable land and route length rather than filling the entire 128-grid with content. Fit early encounters and quest targets to a compact loop. Use separate house, NPC and item-goal identities even when their visible locations are adjacent.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Zoom to the island for all placement decisions; walk the quest loop and cave approach, check starter encounter clearance, and test NPC conditions/rewards and healing repeats. The preview's magenta shore edges are uncomposited transparency, not intended terrain color.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm7/maps/7out01.odm](../../../assets_dev/worlds/mm7/maps/7out01.odm)
- [assets_dev/worlds/mm7/maps/7out01.scene.yml](../../../assets_dev/worlds/mm7/maps/7out01.scene.yml)
- [assets_dev/worlds/mm7/events/maps/7out01.lua](../../../assets_dev/worlds/mm7/events/maps/7out01.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_2.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_2.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT01.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT01.txt)
- [assets_dev/worlds/mm7/events/maps/7out01_mmmerge.lua](../../../assets_dev/worlds/mm7/events/maps/7out01_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
