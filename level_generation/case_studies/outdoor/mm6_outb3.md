# Dragonsand — MM6 `outb3.odm`

**Study focus:** Dragonsand; sparse desert landmarks and dangerous open space

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm6/outb3.json) · [Blender view metadata](../../evidence/mm6/outb3_blender.json)

## Layout and visual reading

Broad dunes and long distances surround a small number of architectural landmarks, with water and islands along part of the boundary. The sparse BModel count is an intentional contrast with Free Haven; terrain and encounter territories carry much of the experience.

![Measured plan of Dragonsand](../../evidence/mm6/outb3.png)

![Blender inspection view of Dragonsand](../../evidence/mm6/outb3_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 27 / 867 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 2560 |
| Master tile / four lookup banks | 2 / 90, 126, 234, 774 |
| Distinct raw tile IDs / raw road-bank cells | 90 / 131 |
| Water-flag / burn-flag cells (may overlap) | 5448 / 0 |
| Native entities / spawn records | 450 / 74 |
| Initial scene actors / chest records | 0 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 5, 6, 7 (7 distinct) |
| Directly bound / declared map events | 26 / 29 |
| Selected face flags | secret: 0; invisible: 8; animated: 0; clickable: 99; pressure_plate: 0; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `egywlA` (163); `egywalHb` (81); `T1wl8ctB` (70); `BdkSH16a` (32); `t1f1` (32); `egybigB` (29); `BemStrT1` (29); `T1trimA` (28).

Common native tile assignments: `162` → `6sandtyl` (3458 cells); `126` → `6wtrtyl` (2164 cells); `164` → `6sandtyl` (1668 cells); `163` → `6sandtyl` (1655 cells); `165` → `6sandtyl` (1413 cells); `128` → `6wtrtyl` (1118 cells). Full resolution/flags are in the JSON.

Map-stat row: [142 / Dragonsand](../../../assets_dev/engine/data_tables/map_stats.txt#L145).

Treasure **6**, Perception difficulty **0**, disarm **8**, trap d20 count **10**, refill **168 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | DragonLand | 5 | 2-4 | 30 |
| 2 | DragonCover | 5 | 2-3 | 40 |
| 3 | DragonCave | 5 | 2-4 | 30 |

The current merged MM6 treasure value is not evidence of original-game balance; choose new-map loot
deliberately and check chest-template remapping and active difficulty overrides.

## Event behavior to inspect

The scene has no fixed actors in the measured state, but map encounters and spawn records still define danger. Seven chest slots are directly bound. Events 100/101 demonstrate guarded permanent resistance/stat rewards; the ownership and one-use conditions matter.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [100](../../../assets_dev/worlds/mm6/events/maps/outb3.lua#L129) | 6 | StatusText |
| [101](../../../assets_dev/worlds/mm6/events/maps/outb3.lua#L144) | 6 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Cactus variants and dry tree forms replace lush grassland planting, with substantial empty sand between groups. Shore-rock records also exist and should not be used as inland boulders indiscriminately. Inspect a dry-land patch as well as the coast before choosing a desert palette.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm6/outb3_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm6/outb3_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm6/outb3_decorations.png)

Native entity records: **450**; initially drawable sprite records: **446**; drawable decorations with descriptor light radius: **0**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| plants | 290 |
| trees | 86 |
| props | 1 |
| rocks | 69 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `6tree21` | tree | 86 | 76 / 96 | 0 |
| `cac16` | cactus | 60 | 52 / 52 | 0 |
| `cac3` | cactus | 49 | 52 / 52 | 0 |
| `cac25` | cactus | 43 | 52 / 52 | 0 |
| `cac24` | cactus | 42 | 52 / 52 | 0 |
| `searka01` | rock | 41 | 52 / 52 | 0 |
| `cac19` | cactus | 40 | 52 / 52 | 0 |
| `cac10` | cactus | 22 | 52 / 52 | 0 |
| `searkb01` | rock | 20 | 52 / 52 | 0 |
| `cac18` | cactus | 14 | 52 / 52 | 0 |
| `cac15` | cactus | 14 | 52 / 52 | 0 |
| `6rock13` | rock | 7 | 52 / 52 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 14 / 86 | 51 | 7 |
| plants | 43 / 290 | 190 | 12 |
| rocks | 0 / 69 | 63 | 0 |
| props | 0 / 1 | 1 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![desert_plants — annotated native decoration study](../../../level_generation/evidence/mm6/outb3_decor_desert_plants.png)

Highlighted source anchors: #312 `cac10` at [-4944, 15296, 480]; #140 `cac16` at [-2496, 16640, 276]; #300 `cac10` at [-4736, 12304, 480].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Design silhouettes, approach distances and guarded reward sites before adding decorative structures. Retain open combat space suitable for dragons while providing intentional navigation cues. Do not populate solely from scene actor count or copy a high-difficulty encounter table into a starter desert.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Test encounter generation and approach safety, reward access/return, permanent reward repetition and flight-versus-foot routes. Review dune quantization and distant landmark readability from player height.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm6/maps/outb3.odm](../../../assets_dev/worlds/mm6/maps/outb3.odm)
- [assets_dev/worlds/mm6/maps/outb3.scene.yml](../../../assets_dev/worlds/mm6/maps/outb3.scene.yml)
- [assets_dev/worlds/mm6/events/maps/outb3.lua](../../../assets_dev/worlds/mm6/events/maps/outb3.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_3.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_3.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTB3.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTB3.txt)
- [assets_dev/worlds/mm6/events/maps/outb3_mmmerge.lua](../../../assets_dev/worlds/mm6/events/maps/outb3_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
