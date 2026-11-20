# Frozen Highlands — MM6 `outc1.odm`

**Study focus:** Frozen Highlands; snow palette, relief and long connecting roads

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm6/outc1.json) · [Blender view metadata](../../evidence/mm6/outc1_blender.json)

## Layout and visual reading

Snow-covered regions, brown exposed slopes, lakes and elevated settlements are linked by a long road network. The native relief gives the snowy region its form; the biome cannot be recreated merely by painting a flat white plane.

![Measured plan of Frozen Highlands](../../evidence/mm6/outc1.png)

![Blender inspection view of Frozen Highlands](../../evidence/mm6/outc1_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 117 / 4224 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 3200 |
| Master tile / four lookup banks | 2 / 342, 126, 342, 774 |
| Distinct raw tile IDs / raw road-bank cells | 90 / 449 |
| Water-flag / burn-flag cells (may overlap) | 944 / 0 |
| Native entities / spawn records | 496 / 71 |
| Initial scene actors / chest records | 40 / 20 |
| Directly bound chest slots | 1, 2 (2 distinct) |
| Directly bound / declared map events | 81 / 91 |
| Selected face flags | secret: 0; invisible: 11; animated: 0; clickable: 157; pressure_plate: 0; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `CsBr128` (625); `SGstrSBW` (358); `BemTilA` (241); `CsWl128` (112); `vh2TrimB` (104); `cbMxbrck` (97); `SdknkRf` (96); `CsTr128` (87).

Common native tile assignments: `1` → `6dirttyl` (2547 cells); `90` → `snotyl` (2248 cells); `3` → `6dirttyl` (1303 cells); `2` → `6dirttyl` (1299 cells); `91` → `snotyl` (1196 cells); `92` → `snotyl` (1167 cells). Full resolution/flags are in the JSON.

Map-stat row: [143 / Frozen Highlands](../../../assets_dev/engine/data_tables/map_stats.txt#L146).

Treasure **6**, Perception difficulty **0**, disarm **4**, trap d20 count **6**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | BHarpy | 3 | 4-6 | 20 |
| 2 | Barbarian | 3 | 3-5 | 40 |
| 3 | BArcher | 3 | 3-5 | 20 |

The current merged MM6 treasure value is not evidence of original-game balance; choose new-map loot
deliberately and check chest-template remapping and active difficulty overrides.

## Event behavior to inspect

Many house/service handlers contrast with only two directly bound chest slots. Fountain events 102–104 demonstrate temporary attribute, armor and level effects. The terrain lookup repeats a bank value, a reminder that raw bank indices need actual palette resolution.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [102](../../../assets_dev/worlds/mm6/events/maps/outc1.lua#L389) | 6 | StatusText |
| [103](../../../assets_dev/worlds/mm6/events/maps/outc1.lua#L400) | 6 | StatusText |
| [104](../../../assets_dev/worlds/mm6/events/maps/outc1.lua#L410) | 6 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Snow-covered tree sprites and snowy terrain replace the temperate palette; the town still mixes small homes, larger halls, stepped roofs and a tower. Keep planting sparser in its usable streets. Snow-tree names do not all contain the literal word tree, so resolve descriptor hints and art as well as asset keys.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm6/outc1_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm6/outc1_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm6/outc1_decorations.png)

Native entity records: **496**; initially drawable sprite records: **491**; drawable decorations with descriptor light radius: **0**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| trees | 469 |
| plants | 9 |
| lights | 3 |
| rocks | 9 |
| props | 1 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `6tree17` | tree | 146 | 76 / 96 | 0 |
| `snotre01` | tree | 136 | 52 / 52 | 0 |
| `snotre03` | tree | 99 | 52 / 52 | 0 |
| `6tree04` | tree | 54 | 96 / 96 | 0 |
| `6tree18` | tree | 34 | 76 / 96 | 0 |
| `6rock03` | rock | 6 | 52 / 52 | 0 |
| `6flower07` | flowers | 5 | 0 / 0 | 0 |
| `6flower02` | flowers | 4 | 0 / 0 | 0 |
| `ckfyr00` | fire | 3 | 30 / 40 | 0 |
| `6rock07` | rock | 3 | 52 / 52 | 0 |
| `fla3__01` | flag | 1 | 30 / 40 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 68 / 469 | 332 | 50 |
| plants | 9 / 9 | 9 | 0 |
| rocks | 3 / 9 | 9 | 0 |
| lights | 1 / 3 | 3 | 0 |
| props | 1 / 1 | 1 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm6/outc1_decor_settlement.png)

Highlighted source anchors: #323 `snotre01` at [-7120, 14272, 96]; #457 `fla3__01` at [-6608, 15560, 2464].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm6/outc1_decor_landscape.png)

Highlighted source anchors: #375 `snotre03` at [-1632, 2080, 262]; #350 `snotre01` at [-4032, 2048, 228]; #415 `snotre03` at [-864, 4416, 246].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Choose snow/exposed-earth transitions deliberately and route roads through passes. Separate the settlement's relatively level pads from steep surrounding land. Use the map as a terrain/palette reference without inheriting all its service density.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Inspect snow transitions at tile scale, test long road continuity and hill approaches, and verify temporary fountain duration/state. Render ground views with actual decoration sprites, which are absent from the bundled terrain/BModel preview.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm6/maps/outc1.odm](../../../assets_dev/worlds/mm6/maps/outc1.odm)
- [assets_dev/worlds/mm6/maps/outc1.scene.yml](../../../assets_dev/worlds/mm6/maps/outc1.scene.yml)
- [assets_dev/worlds/mm6/events/maps/outc1.lua](../../../assets_dev/worlds/mm6/events/maps/outc1.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_3.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_3.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTC1.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTC1.txt)
- [assets_dev/worlds/mm6/events/maps/outc1_mmmerge.lua](../../../assets_dev/worlds/mm6/events/maps/outc1_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
