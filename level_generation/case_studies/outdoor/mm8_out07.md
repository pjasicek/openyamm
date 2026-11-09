# Murmurwoods — MM8 `out07.odm`

**Study focus:** Murmurwoods; dense mixed woodland with clearings and travel corridors

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm8/out07.json) · [Blender view metadata](../../evidence/mm8/out07_blender.json)

## Layout and visual reading

Large native tree groups dominate the countryside around roads and occasional buildings. Open patches and distinct tree silhouettes break up the woodland. Terrain and foliage together control how much the route reveals.

![Measured plan of Murmurwoods](../../evidence/mm8/out07.png)

![Blender inspection view of Murmurwoods](../../evidence/mm8/out07_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 31 / 1321 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 3712 |
| Master tile / four lookup banks | 0 / 90, 126, 162, 414 |
| Distinct raw tile IDs / raw road-bank cells | 50 / 191 |
| Water-flag / burn-flag cells (may overlap) | 0 / 0 |
| Native entities / spawn records | 1850 / 81 |
| Initial scene actors / chest records | 19 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 5 (5 distinct) |
| Directly bound / declared map events | 46 / 76 |
| Selected face flags | secret: 0; invisible: 0; animated: 0; clickable: 1196; pressure_plate: 0; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `Grastyl` (109); `t32a05a` (100); `T68A03B` (93); `T66e01s1` (87); `t32a05b` (79); `t32a11b` (68); `t32a02` (59); `GNecClg2` (52).

Common native tile assignments: `90` → `grastyl` (9675 cells); `1` → `dirttyl` (3972 cells); `3` → `dirttyl` (265 cells); `2` → `dirt1` (247 cells); `4` → `dirt2` (241 cells); `92` → `grastyl2` (222 cells). Full resolution/flags are in the JSON.

Map-stat row: [7 / Murmurwoods](../../../assets_dev/engine/data_tables/map_stats.txt#L10).

Treasure **3**, Perception difficulty **4**, disarm **4**, trap d20 count **2**, refill **336 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Will ' O Wisp | 3 | 1-3 | 60 |
| 2 | Thunder Lizard | 3 | 1-3 | 20 |
| 3 | Unicorn | 3 | 1-3 | 20 |

## Event behavior to inspect

The MM8 navigation row links east to Alvar and south to Shadowspire. The visible settlement-like objects are not interchangeable service instances; trace each event registration before reuse.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [11](../../../assets_dev/worlds/mm8/events/maps/out07.lua#L110) | 1 | EnterHouse; houses: 610 |
| [12](../../../assets_dev/worlds/mm8/events/maps/out07.lua#L114) | 34 | none |
| [13](../../../assets_dev/worlds/mm8/events/maps/out07.lua#L116) | 2 | EnterHouse; houses: 611 |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

The countryside has 1,621 tree sprites in several silhouettes and colors. Dense irregular groups alternate with clearings and a readable road, with rocks as secondary accents. This is a density reference for woodland, not a target count for every grassland map; preserve gaps and test actual runtime cost.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm8/out07_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm8/out07_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm8/out07_decorations.png)

Native entity records: **1850**; initially drawable sprite records: **1847**; drawable decorations with descriptor light radius: **3**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| trees | 1621 |
| rocks | 208 |
| props | 15 |
| lights | 3 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `tree12` | tree | 278 | 16 / 256 | 0 |
| `tree62a` | tree | 232 | 16 / 256 | 0 |
| `tree10` | tree | 228 | 16 / 256 | 0 |
| `rock16` | rock | 150 | 16 / 8 | 0 |
| `tree18` | tree | 137 | 16 / 256 | 0 |
| `tree11` | tree | 136 | 16 / 256 | 0 |
| `tree25` | tree | 100 | 16 / 256 | 0 |
| `tree30` | pine tree | 97 | 16 / 256 | 0 |
| `plant47` | tree stump | 89 | 16 / 24 | 0 |
| `tree31` | tree | 78 | 16 / 256 | 0 |
| `tree21` | tree | 65 | 16 / 256 | 0 |
| `rock24` | rock | 56 | 16 / 8 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 38 / 1621 | 607 | 31 |
| rocks | 27 / 208 | 75 | 6 |
| lights | 0 / 3 | 1 | 0 |
| props | 10 / 15 | 13 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm8/out07_decor_settlement.png)

Highlighted source anchors: #840 `tree11` at [-1024, -10496, 640]; #1847 `dec03` at [-1152, -13896, 608].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm8/out07_decor_landscape.png)

Highlighted source anchors: #597 `tree10` at [-640, -128, 888]; #192 `rock16` at [-672, 4088, 446].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Use coherent mixed tree species in uneven groups, with deliberate clearings and protected road/entrance clearance. Dense foliage should frame a route without blocking party and monster movement.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Compare actual populated frame time and visibility with a fair reference setup. Walk between tree groups and test road/house access; a Blender billboard preview cannot validate collision or performance.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm8/maps/out07.odm](../../../assets_dev/worlds/mm8/maps/out07.odm)
- [assets_dev/worlds/mm8/maps/out07.scene.yml](../../../assets_dev/worlds/mm8/maps/out07.scene.yml)
- [assets_dev/worlds/mm8/events/maps/out07.lua](../../../assets_dev/worlds/mm8/events/maps/out07.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data.txt](../../../assets_dev/engine/data_tables/terrain_tile_data.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Out07.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Out07.txt)
- [assets_dev/worlds/mm8/events/maps/out07_mmmerge.lua](../../../assets_dev/worlds/mm8/events/maps/out07_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
