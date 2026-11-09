# Erathia — MM7 `7out03.odm`

**Study focus:** Erathia; capital, roads, river and steep fortress terrain

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm7/7out03.json) · [Blender view metadata](../../evidence/mm7/7out03_blender.json)

## Layout and visual reading

A large organized settlement and major fortified structure are embedded in a landscape with rivers, bridges and very high terrain. The heightfield reaches close to the native maximum, requiring deliberate separation of traversable roads from surrounding slopes.

![Measured plan of Erathia](../../evidence/mm7/7out03.png)

![Blender inspection view of Erathia](../../evidence/mm7/7out03_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 124 / 6242 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 7872 |
| Master tile / four lookup banks | 1 / 90, 126, 342, 414 |
| Distinct raw tile IDs / raw road-bank cells | 99 / 417 |
| Water-flag / burn-flag cells (may overlap) | 2655 / 0 |
| Native entities / spawn records | 547 / 62 |
| Initial scene actors / chest records | 40 / 20 |
| Directly bound chest slots | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 18, 19 (12 distinct) |
| Directly bound / declared map events | 117 / 141 |
| Selected face flags | secret: 0; invisible: 145; animated: 0; clickable: 4647; pressure_plate: 0; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `7t1books1` (621); `TRIM2_32` (383); `Hhm3ch` (335); `Ch1b1` (267); `CWB` (251); `Hhp2b2` (240); `7t1butts` (234); `7t1beds2` (208).

Common native tile assignments: `90` → `7grastyl` (9201 cells); `126` → `7wtrtyl` (2127 cells); `1` → `7dirttyl` (494 cells); `106` → `7grdrte` (326 cells); `107` → `7grdrtw` (315 cells); `108` → `7grdrtn` (313 cells). Full resolution/flags are in the JSON.

Map-stat row: [64 / Erathia](../../../assets_dev/engine/data_tables/map_stats.txt#L67).

Treasure **1**, Perception difficulty **4**, disarm **4**, trap d20 count **2**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Fighter Leather | 2 | 1-3 | 50 |
| 2 | Griffin | 1 | 1-3 | 50 |
| 3 | 0 | 1 | 1-3 | 0 |

## Event behavior to inspect

House/service, travel and seasonal decoration logic coexist with numerous chest slots. Events 202/203 illustrate poverty relief and per-player stat rewards. Seasonal scene changes mean a static geometry preview cannot show the full visual state.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [202](../../../assets_dev/worlds/mm7/events/maps/7out03.lua#L466) | 1 | StatusText |
| [203](../../../assets_dev/worlds/mm7/events/maps/7out03.lua#L485) | 1 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

House forms vary around a strong road grid and a larger civic building. A concentrated planted garden contrasts with looser individual trees and scattered small plants. Treat a garden as an authored patch with an edge, not as the same density used across the countryside.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm7/7out03_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm7/7out03_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm7/7out03_decorations.png)

Native entity records: **547**; initially drawable sprite records: **523**; drawable decorations with descriptor light radius: **3**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| rocks | 68 |
| plants | 270 |
| props | 8 |
| trees | 173 |
| lights | 4 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `7tree19` | tree | 80 | 96 / 96 | 0 |
| `flower05` | flower | 74 | 0 / 0 | 0 |
| `flower04` | flower | 63 | 0 / 0 | 0 |
| `7tree28` | tree | 43 | 96 / 96 | 0 |
| `7rock08` | rock | 41 | 0 / 0 | 0 |
| `flower08` | flower | 39 | 0 / 0 | 0 |
| `flower11` | flower | 39 | 0 / 0 | 0 |
| `7tree25` | tree | 34 | 96 / 96 | 0 |
| `flower03` | flower | 30 | 0 / 0 | 0 |
| `7rock09` | rock | 27 | 0 / 0 | 0 |
| `flower02` | flower | 13 | 0 / 0 | 0 |
| `flower01` | flower | 10 | 0 / 0 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 32 / 173 | 111 | 6 |
| plants | 146 / 270 | 171 | 40 |
| rocks | 24 / 68 | 49 | 5 |
| lights | 3 / 4 | 3 | 1 |
| props | 1 / 8 | 8 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm7/7out03_decor_settlement.png)

Highlighted source anchors: #296 `7tree19` at [-13856, 2880, 898]; #103 `flower05` at [-12688, 5152, 699]; #73 `7rock09` at [-11600, 2320, 960].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm7/7out03_decor_landscape.png)

Highlighted source anchors: #311 `7tree25` at [320, 224, 544]; #206 `flower04` at [-768, 1840, 531]; #33 `7rock08` at [3024, 896, 661].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Design city streets and regional roads as connected graphs, then grade the terrain and place foundations. Keep decorative seasonal state separate from permanent map geometry and persistent reward state.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Test bridge approaches, steep routes, fortress entrances and boundary/dungeon travel. Review appropriate seasons in engine, check reward scope, and ensure terrain quantization near the height ceiling does not silently clip peaks or entrances.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm7/maps/7out03.odm](../../../assets_dev/worlds/mm7/maps/7out03.odm)
- [assets_dev/worlds/mm7/maps/7out03.scene.yml](../../../assets_dev/worlds/mm7/maps/7out03.scene.yml)
- [assets_dev/worlds/mm7/events/maps/7out03.lua](../../../assets_dev/worlds/mm7/events/maps/7out03.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_2.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_2.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT03.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT03.txt)
- [assets_dev/worlds/mm7/events/maps/7out03_mmmerge.lua](../../../assets_dev/worlds/mm7/events/maps/7out03_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
