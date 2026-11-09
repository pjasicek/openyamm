# Shadowspire — MM8 `out06.odm`

**Study focus:** Shadowspire; dark settlement, wetland and rough terrain

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm8/out06.json) · [Blender view metadata](../../evidence/mm8/out06_blender.json)

## Layout and visual reading

A compact settlement near water contrasts with broad dark terrain, many small wet areas and a region of rough elevated land. The mood depends on palette and native decorations/lighting, not simply lowering Blender exposure.

![Measured plan of Shadowspire](../../evidence/mm8/out06.png)

![Blender inspection view of Shadowspire](../../evidence/mm8/out06_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 84 / 4507 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 5632 |
| Master tile / four lookup banks | 0 / 702, 738, 666, 774 |
| Distinct raw tile IDs / raw road-bank cells | 94 / 315 |
| Water-flag / burn-flag cells (may overlap) | 1658 / 0 |
| Native entities / spawn records | 607 / 63 |
| Initial scene actors / chest records | 27 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 5, 6 (6 distinct) |
| Directly bound / declared map events | 110 / 138 |
| Selected face flags | secret: 0; invisible: 21; animated: 0; clickable: 4308; pressure_plate: 0; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `gn_mtl01` (502); `gn_mtl03` (500); `t19a05b` (407); `gn_mtl02` (402); `t05a01` (244); `t19b01` (169); `t19a02` (132); `bwoodb1` (118).

Common native tile assignments: `1` → `dirttyl` (7716 cells); `90` → `gstyl` (2469 cells); `126` → `wtrtyl` (1254 cells); `2` → `dirt1` (525 cells); `4` → `dirt2` (520 cells); `3` → `dirttyl` (515 cells). Full resolution/flags are in the JSON.

Map-stat row: [6 / Shadowspire](../../../assets_dev/engine/data_tables/map_stats.txt#L9).

Treasure **2**, Perception difficulty **4**, disarm **4**, trap d20 count **2**, refill **336 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Vampire (monster) | 2 | 1-3 | 50 |
| 2 | Skeletons Archer | 2 | 1-3 | 0 |
| 3 | Bone Dragon | 1 | 1-3 | 50 |

## Event behavior to inspect

House targets dominate the interaction inventory alongside wells and an obelisk. Event 101 is a capped attribute reward; event 104 is a mana-related fountain path whose exact conditions should be checked in the script; event 150 advances obelisk state. Copying a visual fountain does not copy its reset policy.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [101](../../../assets_dev/worlds/mm8/events/maps/out06.lua#L412) | 51 | StatusText |
| [104](../../../assets_dev/worlds/mm8/events/maps/out06.lua#L443) | 23 | StatusText |
| [150](../../../assets_dev/worlds/mm8/events/maps/out06.lua#L456) | 8 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Bare trees, rune posts, rocks and sparse ground plants accompany the town’s repeated green-roof material family. The roofs still vary in plan and size. Use biome and settlement identity together: consistent materials do not require identical buildings or dense green foliage. The wilderness follow-up compares 84 trees, 28 low plants, 159 rocks and 331 props against Ravenshore and Ravage Roaming. Use its bare-tree/rock/prop vocabulary and local coverage, not a temperate garden quota.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm8/out06_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm8/out06_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm8/out06_decorations.png)

Native entity records: **607**; initially drawable sprite records: **604**; drawable decorations with descriptor light radius: **2**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| rocks | 159 |
| plants | 28 |
| trees | 84 |
| props | 331 |
| lights | 2 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `dec05` | skeleton | 95 | 16 / 8 | 0 |
| `dec17` | rune post | 85 | 16 / 8 | 0 |
| `tree28` | dead tree | 84 | 16 / 256 | 0 |
| `dec15` | rune post | 45 | 16 / 8 | 0 |
| `dec13` | rune post | 36 | 16 / 8 | 0 |
| `rock22` | rock | 34 | 16 / 8 | 0 |
| `dec14` | rune post | 33 | 16 / 8 | 0 |
| `rock56` | rock | 31 | 16 / 8 | 0 |
| `rock52` | rock | 26 | 16 / 8 | 0 |
| `plant48` | plant | 26 | 16 / 8 | 0 |
| `dec16` | rune post | 26 | 16 / 8 | 0 |
| `rock51` | rock | 24 | 16 / 8 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 5 / 84 | 34 | 1 |
| plants | 8 / 28 | 12 | 1 |
| rocks | 14 / 159 | 90 | 0 |
| lights | 0 / 2 | 2 | 0 |
| props | 53 / 331 | 179 | 12 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm8/out06_decor_settlement.png)

Highlighted source anchors: #156 `tree28` at [-1536, -14272, 96]; #118 `plant48` at [-2432, -15712, 96]; #217 `rock56` at [-3904, -10144, 78]; #384 `dec17` at [-4864, -13952, 96].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm8/out06_decor_landscape.png)

Highlighted source anchors: #149 `tree28` at [2784, 288, 894]; #183 `plant48` at [288, 672, 1156]; #292 `dec13` at [-1280, 1856, 1228].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Use an explicit swamp/dark-earth palette, terrain masks and decoration distribution while retaining readable roads and service entrances. Differentiate environmental atmosphere from actual traversal hazards and gameplay effects.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Review water transitions, settlement lighting at player height, rough-ground routes and fountain conditions/repeats. Add real tree/decor sprites for the final atmosphere comparison; the bundled overview omits them.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm8/maps/out06.odm](../../../assets_dev/worlds/mm8/maps/out06.odm)
- [assets_dev/worlds/mm8/maps/out06.scene.yml](../../../assets_dev/worlds/mm8/maps/out06.scene.yml)
- [assets_dev/worlds/mm8/events/maps/out06.lua](../../../assets_dev/worlds/mm8/events/maps/out06.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data.txt](../../../assets_dev/engine/data_tables/terrain_tile_data.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/OUT06.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/OUT06.txt)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
