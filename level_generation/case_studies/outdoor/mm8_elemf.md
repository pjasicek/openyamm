# Plane of Fire — MM8 `elemf.odm`

**Study focus:** Plane of Fire; native terrain causeways above hazardous lava

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm8/elemf.json) · [Blender view metadata](../../evidence/mm8/elemf_blender.json)

## Layout and visual reading

Tall islands and narrow connecting landforms occupy a lava-dominated map. The terrain heightfield itself contributes much of the causeway-like network; not every bridge-shaped silhouette is a BModel. A small number of structures mark major destinations.

![Measured plan of Plane of Fire](../../evidence/mm8/elemf.png)

![Blender inspection view of Plane of Fire](../../evidence/mm8/elemf_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 30 / 1426 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 5184 |
| Master tile / four lookup banks | 0 / 198, 378, 198, 414 |
| Distinct raw tile IDs / raw road-bank cells | 55 / 0 |
| Water-flag / burn-flag cells (may overlap) | 12192 / 12192 |
| Native entities / spawn records | 1 / 70 |
| Initial scene actors / chest records | 0 / 20 |
| Directly bound chest slots | none (0 distinct) |
| Directly bound / declared map events | 17 / 52 |
| Selected face flags | secret: 0; invisible: 0; animated: 4; clickable: 1168; pressure_plate: 0; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `GsTyl` (288); `GNecWal1` (272); `gn_mtl03` (178); `t09a05` (156); `t09a01` (138); `LavTyl` (74); `t09a02a` (69); `GCav1flr` (54).

Common native tile assignments: `126` → `lavtyl` (9867 cells); `90` → `voltyl` (1165 cells); `127` → `lavtyl` (631 cells); `128` → `lavtyl` (610 cells); `129` → `lavtyl` (585 cells); `109` → `vols` (262 cells). Full resolution/flags are in the JSON.

Map-stat row: [11 / Plane of Fire](../../../assets_dev/engine/data_tables/map_stats.txt#L14).

Treasure **4**, Perception difficulty **10**, disarm **10**, trap d20 count **5**, refill **336 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Fire Elemental | 3 | 1-3 | 50 |
| 2 | Efreeti | 3 | 1-3 | 25 |
| 3 | Salamander | 3 | 1-3 | 25 |

## Event behavior to inspect

There are no directly bound chest slots and no fixed scene actors in the measured state, but Fire Elemental/Efreet/Salamander encounters still populate through spawn settings. Travel events 501/502 lead to d29/d30 and 505 returns to out04. Water and burn flags overlap on 12192 cells.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [501](../../../assets_dev/worlds/mm8/events/maps/elemf.lua#L240) | 1 | MoveToMap; destinations: d29.blv |
| [502](../../../assets_dev/worlds/mm8/events/maps/elemf.lua#L244) | 1 | MoveToMap; destinations: d30.blv |
| [505](../../../assets_dev/worlds/mm8/events/maps/elemf.lua#L248) | 58 | MoveToMap; destinations: out04.odm |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

No drawable native decoration sprites are present. Lava, dark island terrain and the clustered fortress silhouette establish the scene. This is a useful counterexample to adding trees and rocks automatically; absence can be purposeful, but the underlying landform and focal architecture must carry the view.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm8/elemf_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm8/elemf_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm8/elemf_decorations.png)

Native entity records: **1**; initially drawable sprite records: **0**; drawable decorations with descriptor light radius: **0**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| No initially drawable sprites | 0 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm8/elemf_decor_settlement.png)

Highlighted source anchors: none in this view.

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Use native heightfield ridges and islands where the shape is representable; reserve BModels for actual overhangs/structures. Define intended protected/unprotected movement and encounter space explicitly. Sparse structures can be sufficient when terrain and hazards dominate.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Test narrow-route collision and actor movement, falls/escape, lava effects with relevant protections, and each destination/return. Inspect rendered-triangle contact on quantized ridge edges and measure runtime behavior before replacing native terrain with mesh ground.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm8/maps/elemf.odm](../../../assets_dev/worlds/mm8/maps/elemf.odm)
- [assets_dev/worlds/mm8/maps/elemf.scene.yml](../../../assets_dev/worlds/mm8/maps/elemf.scene.yml)
- [assets_dev/worlds/mm8/events/maps/elemf.lua](../../../assets_dev/worlds/mm8/events/maps/elemf.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data.txt](../../../assets_dev/engine/data_tables/terrain_tile_data.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/ElemF.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/ElemF.txt)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
