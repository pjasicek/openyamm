# Harmondale — MM7 `7out02.odm`

**Study focus:** Harmondale; town shelves, enclosing hills and planted civic space

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm7/7out02.json) · [Blender view metadata](../../evidence/mm7/7out02_blender.json)

## Layout and visual reading

The town sits in a northwestern pocket behind surrounding high ground. Roads connect its shelves to a broad central route and the southern lake country. Individual foundations occupy local pads; the entire settlement is not one flattened rectangle.

![Measured plan of Harmondale](../../evidence/mm7/7out02.png)

![Blender inspection view of Harmondale](../../evidence/mm7/7out02_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 114 / 5639 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 4000 |
| Master tile / four lookup banks | 1 / 90, 126, 342, 414 |
| Distinct raw tile IDs / raw road-bank cells | 99 / 342 |
| Water-flag / burn-flag cells (may overlap) | 248 / 0 |
| Native entities / spawn records | 568 / 49 |
| Initial scene actors / chest records | 142 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 (12 distinct) |
| Directly bound / declared map events | 96 / 112 |
| Selected face flags | secret: 0; invisible: 462; animated: 0; clickable: 3215; pressure_plate: 4; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `Ch1b1` (432); `TRIM2_32a` (414); `Ch1b1s` (341); `TRIM2_32` (319); `CHB1` (313); `Hhm3ch` (302); `Trim11_32` (302); `7t1books1` (248).

Common native tile assignments: `1` → `7dirttyl` (3078 cells); `90` → `7grastyl` (3047 cells); `3` → `7dirttyl` (927 cells); `2` → `7dirt1` (800 cells); `91` → `7grastyl` (706 cells); `92` → `7grastyl` (692 cells). Full resolution/flags are in the JSON.

Map-stat row: [63 / Harmondale](../../../assets_dev/engine/data_tables/map_stats.txt#L66).

Treasure **0**, Perception difficulty **2**, disarm **2**, trap d20 count **1**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Goblin | 3 | 2-5 | 100 |
| 2 | Swordsman | 3 | 1-3 | 0 |
| 3 | 0 | 1 | 1-3 | 0 |

## Event behavior to inspect

Use the native navigation table and map-local entry handlers for regional travel; geography alone does not create a destination or return arrival. House faces, outdoor props and the castle entrance are separate registrations.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [1](../../../assets_dev/worlds/mm7/events/maps/7out02.lua#L96) | 2 | none |
| [3](../../../assets_dev/worlds/mm7/events/maps/7out02.lua#L100) | 1 | EnterHouse, FaceAnimation, StatusText; houses: 9 |
| [4](../../../assets_dev/worlds/mm7/events/maps/7out02.lua#L109) | 88 | none |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

The town occupies local shelves within an enclosing bowl of high ground. Different roof shapes, a church, taller civic forms and planted garden rows create hierarchy. Use a few usable terrace levels and clear connecting streets, then plant the residual courtyards rather than flattening the whole town.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm7/7out02_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm7/7out02_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm7/7out02_decorations.png)

Native entity records: **568**; initially drawable sprite records: **564**; drawable decorations with descriptor light radius: **2**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| rocks | 41 |
| plants | 231 |
| trees | 287 |
| lights | 5 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `7tree16` | tree | 157 | 96 / 96 | 0 |
| `flower01` | flower | 146 | 0 / 0 | 0 |
| `7tree13` | tree | 102 | 96 / 96 | 0 |
| `flower06` | flower | 51 | 0 / 0 | 0 |
| `flower02` | flower | 34 | 0 / 0 | 0 |
| `7rock09` | rock | 20 | 0 / 0 | 0 |
| `7tree22` | tree | 14 | 96 / 96 | 0 |
| `7rock01` | rock | 11 | 0 / 0 | 0 |
| `7rock02` | rock | 7 | 0 / 0 | 0 |
| `tree38` | tree | 7 | 96 / 96 | 0 |
| `7rock08` | rock | 3 | 0 / 0 | 0 |
| `dec24x` | burned out fire | 3 | 16 / 16 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 21 / 287 | 91 | 19 |
| plants | 72 / 231 | 91 | 26 |
| rocks | 14 / 41 | 35 | 0 |
| lights | 4 / 5 | 5 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![town_terraces — annotated native decoration study](../../../level_generation/evidence/mm7/7out02_decor_town_terraces.png)

Highlighted source anchors: #237 `7tree13` at [-10864, 13488, 129]; #93 `flower01` at [-12480, 12032, 0]; #30 `7rock09` at [-12864, 16208, 0].

![terrain_enclosure — annotated native decoration study](../../../level_generation/evidence/mm7/7out02_decor_terrain_enclosure.png)

Highlighted source anchors: #548 `7tree16` at [1408, -864, 142]; #209 `flower06` at [-8448, 4320, 2256]; #215 `7rock08` at [-9472, -6784, 0]; #566 `dec24x` at [784, -20760, 640].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Use a few deliberate town elevation bands joined by walkable approaches. Keep local building pads stable, plant open courtyards, and retain enclosing terrain between town and countryside.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Walk each change of level, doorway and road junction with collision enabled. Inspect eye-height views from upper and lower streets and the entry passes.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm7/maps/7out02.odm](../../../assets_dev/worlds/mm7/maps/7out02.odm)
- [assets_dev/worlds/mm7/maps/7out02.scene.yml](../../../assets_dev/worlds/mm7/maps/7out02.scene.yml)
- [assets_dev/worlds/mm7/events/maps/7out02.lua](../../../assets_dev/worlds/mm7/events/maps/7out02.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_2.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_2.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT02.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT02.txt)
- [assets_dev/worlds/mm7/events/maps/7out02_mmmerge.lua](../../../assets_dev/worlds/mm7/events/maps/7out02_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
