# Castle Ironfist — MM6 `outd3.odm`

**Study focus:** Castle Ironfist; elevated stronghold and connected settlements

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm6/outd3.json) · [Blender view metadata](../../evidence/mm6/outd3_blender.json)

## Layout and visual reading

A prominent fortified terrace contrasts with smaller settlements and branching roads around hills and water. Elevation and road placement establish hierarchy: the castle is a destination, not just another model dropped on a flat field.

![Measured plan of Castle Ironfist](../../evidence/mm6/outd3.png)

![Blender inspection view of Castle Ironfist](../../evidence/mm6/outd3_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 69 / 3177 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 4064 |
| Master tile / four lookup banks | 2 / 90, 126, 270, 774 |
| Distinct raw tile IDs / raw road-bank cells | 98 / 546 |
| Water-flag / burn-flag cells (may overlap) | 6575 / 0 |
| Native entities / spawn records | 275 / 80 |
| Initial scene actors / chest records | 44 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 6 (5 distinct) |
| Directly bound / declared map events | 68 / 85 |
| Selected face flags | secret: 0; invisible: 29; animated: 0; clickable: 129; pressure_plate: 9; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `HCWALL` (689); `CsBr128` (132); `Roof` (124); `RHCTR` (117); `BemOB2` (106); `CbRdbrck` (102); `TAVRF` (90); `HCW1CTR` (76).

Common native tile assignments: `126` → `6wtrtyl` (2637 cells); `128` → `6wtrtyl` (1318 cells); `127` → `6wtrtyl` (1290 cells); `1` → `6dirttyl` (1150 cells); `129` → `6wtrtyl` (1069 cells); `90` → `6grastyl` (761 cells). Full resolution/flags are in the JSON.

Map-stat row: [148 / Castle Ironfist](../../../assets_dev/engine/data_tables/map_stats.txt#L151).

Treasure **6**, Perception difficulty **0**, disarm **2**, trap d20 count **3**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | LizardArch | 1 | 3-5 | 20 |
| 2 | Bloodsucker | 3 | 3-6 | 40 |
| 3 | PeasantM3 | 1 | 4-6 | 40 |

The current merged MM6 treasure value is not evidence of original-game balance; choose new-map loot
deliberately and check chest-template remapping and active difficulty overrides.

## Event behavior to inspect

House/service and travel events are numerous. Fountain events 100–102 provide temporary stat and healing examples, distinct from permanent rewards. Five directly bound chest slots are a small subset of the map's interaction targets.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [100](../../../assets_dev/worlds/mm6/events/maps/outd3.lua#L374) | 6 | StatusText |
| [101](../../../assets_dev/worlds/mm6/events/maps/outd3.lua#L384) | 6 | StatusText |
| [102](../../../assets_dev/worlds/mm6/events/maps/outd3.lua#L391) | 6 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

The castle precinct rises on a strong terrain shelf. Pink/red ornamental trees and small planted features mark the gateway and civic approach, while ordinary trees occur outside. Reserve the largest silhouettes for the castle and temple; modest houses and repeated trees establish their scale.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm6/outd3_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm6/outd3_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm6/outd3_decorations.png)

Native entity records: **275**; initially drawable sprite records: **271**; drawable decorations with descriptor light radius: **0**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| trees | 230 |
| plants | 19 |
| props | 15 |
| lights | 1 |
| rocks | 6 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `6tree01` | tree | 98 | 96 / 96 | 0 |
| `swptree1` | tree | 50 | 52 / 52 | 0 |
| `6tree02` | tree | 35 | 96 / 96 | 0 |
| `6tree05` | tree | 32 | 96 / 96 | 0 |
| `6flower07` | flowers | 11 | 0 / 0 | 0 |
| `6tree04` | tree | 9 | 96 / 96 | 0 |
| `bouy0` | buoy | 9 | 30 / 40 | 0 |
| `6flower02` | flowers | 8 | 0 / 0 | 0 |
| `6rock01` | rock | 6 | 52 / 52 | 0 |
| `swptree3` | tree | 4 | 52 / 52 | 0 |
| `6tree03` | tree | 2 | 76 / 96 | 0 |
| `shp` | Ship | 2 | 378 / 512 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 34 / 230 | 180 | 12 |
| plants | 19 / 19 | 19 | 0 |
| rocks | 2 / 6 | 6 | 0 |
| lights | 1 / 1 | 1 | 0 |
| props | 6 / 15 | 15 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm6/outd3_decor_settlement.png)

Highlighted source anchors: #123 `6tree03` at [18208, 14880, 2080]; #122 `6flower07` at [16624, 15368, 2192]; #270 `fla1__01` at [18688, 16384, 3168].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm6/outd3_decor_landscape.png)

Highlighted source anchors: #249 `6tree05` at [3816, 2360, 96]; #250 `6tree05` at [5216, 4000, 96]; #243 `6tree05` at [3360, 6512, 96].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Shape the stronghold's terrace and approach first, fit architecture to the quantized heightfield, then connect road junctions and service entrances. Preserve the distinction between temporary bonuses, charged effects and unique rewards.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Walk castle access and settlement routes, inspect foundations at height changes, verify travel arrivals/returns and compare fountain behavior before/after repeat use. Roads crossing steep terrain need ground-level validation, not only a correct top-view line.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm6/maps/outd3.odm](../../../assets_dev/worlds/mm6/maps/outd3.odm)
- [assets_dev/worlds/mm6/maps/outd3.scene.yml](../../../assets_dev/worlds/mm6/maps/outd3.scene.yml)
- [assets_dev/worlds/mm6/events/maps/outd3.lua](../../../assets_dev/worlds/mm6/events/maps/outd3.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_3.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_3.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTD3.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTD3.txt)
- [assets_dev/worlds/mm6/events/maps/outd3_1.lua](../../../assets_dev/worlds/mm6/events/maps/outd3_1.lua)
- [assets_dev/worlds/mm6/events/maps/outd3_mmmerge.lua](../../../assets_dev/worlds/mm6/events/maps/outd3_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
