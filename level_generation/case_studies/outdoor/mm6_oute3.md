# New Sorpigal — MM6 `oute3.odm`

**Study focus:** New Sorpigal; starter coastline, town and reusable well patterns

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm6/oute3.json) · [Blender view metadata](../../evidence/mm6/oute3_blender.json)

## Layout and visual reading

A compact coastal settlement occupies part of an irregular island/coast footprint, with small offshore landforms and a limited road network. Most native cells are water-flagged, so full-grid area greatly overstates playable land area. Town density must be judged locally.

![Measured plan of New Sorpigal](../../evidence/mm6/oute3.png)

![Blender inspection view of New Sorpigal](../../evidence/mm6/oute3_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 85 / 2882 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 4064 |
| Master tile / four lookup banks | 2 / 90, 126, 198, 774 |
| Distinct raw tile IDs / raw road-bank cells | 92 / 116 |
| Water-flag / burn-flag cells (may overlap) | 11435 / 0 |
| Native entities / spawn records | 479 / 56 |
| Initial scene actors / chest records | 43 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 (18 distinct) |
| Directly bound / declared map events | 93 / 111 |
| Selected face flags | secret: 0; invisible: 13; animated: 0; clickable: 161; pressure_plate: 1; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `RblBW` (410); `TewS` (376); `Cbeam5` (143); `Pxshings` (107); `PXSTRRE` (76); `PXSTRLE` (75); `CR64` (70); `TAV128WL` (67).

Common native tile assignments: `126` → `6wtrtyl` (4599 cells); `128` → `6wtrtyl` (2340 cells); `127` → `6wtrtyl` (2231 cells); `129` → `6wtrtyl` (1828 cells); `90` → `6grastyl` (1212 cells); `1` → `6dirttyl` (388 cells). Full resolution/flags are in the JSON.

Map-stat row: [151 / New Sorpigal](../../../assets_dev/engine/data_tables/map_stats.txt#L154).

Treasure **6**, Perception difficulty **0**, disarm **0**, trap d20 count **1**, refill **168 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | BGoblin | 1 | 3-5 | 50 |
| 2 | PeasantM2 | 1 | 3-5 | 50 |
| 3 | 0 | 1 | 1-4 | 0 |

The current merged MM6 treasure value is not evidence of original-game balance; choose new-map loot
deliberately and check chest-template remapping and active difficulty overrides.

## Event behavior to inspect

Numerous house targets coexist with 18 directly bound chest slots and fixed actors/spawn records. Well events 109/110 and fountain 131 illustrate poverty relief, bounded permanent-stat reward and charged healing respectively. Inspect reward ownership and reset conditions rather than treating all wells as interchangeable.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [109](../../../assets_dev/worlds/mm6/events/maps/oute3.lua#L398) | 1 | StatusText |
| [110](../../../assets_dev/worlds/mm6/events/maps/oute3.lua#L409) | 1 | StatusText |
| [131](../../../assets_dev/worlds/mm6/events/maps/oute3.lua#L527) | 1 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Small cottages, extended houses, courtyard forms, halls and a tower share a restricted material family. Ornamental colored trees cluster beside houses and civic points; greener trees surround the settlement, leaving the broad main street clear. Vary footprint, roof direction and prominence while preserving a coherent town style.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm6/oute3_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm6/oute3_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm6/oute3_decorations.png)

Native entity records: **479**; initially drawable sprite records: **477**; drawable decorations with descriptor light radius: **0**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| trees | 386 |
| plants | 32 |
| lights | 5 |
| rocks | 43 |
| props | 11 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `6tree01` | tree | 213 | 96 / 96 | 0 |
| `6tree02` | tree | 103 | 96 / 96 | 0 |
| `6rock01` | rock | 41 | 52 / 52 | 0 |
| `6tree19` | tree | 18 | 76 / 96 | 0 |
| `6flower02` | flowers | 16 | 0 / 0 | 0 |
| `6flower07` | flowers | 16 | 0 / 0 | 0 |
| `6tree05` | tree | 16 | 96 / 96 | 0 |
| `6tree03` | tree | 13 | 76 / 96 | 0 |
| `tree06a` | Empty Food Tree | 9 | 86 / 96 | 0 |
| `6tree04` | tree | 8 | 96 / 96 | 0 |
| `6tree06` | Food Tree | 6 | 86 / 96 | 0 |
| `ckfyr00` | fire | 5 | 30 / 40 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 95 / 386 | 202 | 37 |
| plants | 32 / 32 | 32 | 0 |
| rocks | 26 / 43 | 39 | 2 |
| lights | 2 / 5 | 5 | 0 |
| props | 9 / 11 | 11 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm6/oute3_decor_settlement.png)

Highlighted source anchors: #18 `6tree03` at [-10552, -6176, 160]; #212 `6flower02` at [-8552, -5648, 160]; #476 `fla3__01` at [-6144, -9224, 2528].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm6/oute3_decor_landscape.png)

Highlighted source anchors: #473 `6tree01` at [-216, -784, 873]; #406 `6rock01` at [2976, -2752, 122]; #339 `swrdstn` at [-1792, -5376, 960].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Start with shoreline and town approach, then place service entrances along readable routes. Allocate encounter/reward pockets outside the settlement and review their distance at walking scale. Reuse the well state patterns, not legacy global IDs or the imported treasure-level-6 row blindly.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Test roads/thresholds, shoreline tile behavior, starter encounter safety, all services and repeated well use across party members/day/save boundaries. Add a settlement close-up; the full-map isometric leaves individual doors too small.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm6/maps/oute3.odm](../../../assets_dev/worlds/mm6/maps/oute3.odm)
- [assets_dev/worlds/mm6/maps/oute3.scene.yml](../../../assets_dev/worlds/mm6/maps/oute3.scene.yml)
- [assets_dev/worlds/mm6/events/maps/oute3.lua](../../../assets_dev/worlds/mm6/events/maps/oute3.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_3.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_3.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTE3.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTE3.txt)
- [assets_dev/worlds/mm6/events/maps/oute3_1.lua](../../../assets_dev/worlds/mm6/events/maps/oute3_1.lua)
- [assets_dev/worlds/mm6/events/maps/oute3_intro.lua](../../../assets_dev/worlds/mm6/events/maps/oute3_intro.lua)
- [assets_dev/worlds/mm6/events/maps/oute3_mmmerge.lua](../../../assets_dev/worlds/mm6/events/maps/oute3_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
