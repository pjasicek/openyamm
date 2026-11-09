# Mount Nighon — MM7 `out10.odm`

**Study focus:** Nighon; mountain enclosure and restricted ground routes

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm7/out10.json) · [Blender view metadata](../../evidence/mm7/out10_blender.json)

## Layout and visual reading

Large steep ridges and high peaks enclose lower traversable regions and settlements. Snow appears on selected high terrain rather than covering the whole map. This is a strong reference for making terrain control navigation.

![Measured plan of Mount Nighon](../../evidence/mm7/out10.png)

![Blender inspection view of Mount Nighon](../../evidence/mm7/out10_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 69 / 3651 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 8000 |
| Master tile / four lookup banks | 1 / 342, 126, 234, 414 |
| Distinct raw tile IDs / raw road-bank cells | 92 / 39 |
| Water-flag / burn-flag cells (may overlap) | 1698 / 0 |
| Native entities / spawn records | 236 / 80 |
| Initial scene actors / chest records | 32 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 5, 6, 8, 9 (8 distinct) |
| Directly bound / declared map events | 54 / 71 |
| Selected face flags | secret: 0; invisible: 23; animated: 0; clickable: 3304; pressure_plate: 12; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `7t1butts` (286); `Trim11_32` (279); `Ckb` (263); `Hkp1rf` (258); `Hhm3ch` (199); `Hhp2b2` (189); `T2BEDSHT` (160); `Hkm1b1` (133).

Common native tile assignments: `1` → `7dirttyl` (8633 cells); `126` → `7wtrtyl` (1354 cells); `90` → `7snow` (977 cells); `162` → `7sand` (619 cells); `3` → `7dirttyl` (538 cells); `4` → `7dirt2` (532 cells). Full resolution/flags are in the JSON.

Map-stat row: [69 / Mount Nighon](../../../assets_dev/engine/data_tables/map_stats.txt#L72).

Treasure **3**, Perception difficulty **10**, disarm **10**, trap d20 count **5**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Warlock | 2 | 1-3 | 40 |
| 2 | Roc | 3 | 1-3 | 30 |
| 3 | Hydra | 1 | 1-3 | 30 |

## Event behavior to inspect

House/travel targets, eight bound chest slots and dangerous encounter families occupy the accessible areas. Event 206 illustrates a bounded per-character attribute reward; event 453 contributes obelisk progress. The route constraints and reward policy must be evaluated together.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [206](../../../assets_dev/worlds/mm7/events/maps/out10.lua#L329) | 8 | none |
| [453](../../../assets_dev/worlds/mm7/events/maps/out10.lua#L372) | 12 | ForPlayer |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Snow trees concentrate on snow-bearing slopes and edges while the rocky town pocket remains comparatively open. Large height differences split usable areas into shelves. Use the landform and material boundaries to guide species placement, with sparse rocks between the buildings.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm7/out10_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm7/out10_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm7/out10_decorations.png)

Native entity records: **236**; initially drawable sprite records: **235**; drawable decorations with descriptor light radius: **4**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| rocks | 102 |
| trees | 129 |
| lights | 4 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `tree33` | tree | 70 | 96 / 96 | 0 |
| `tree36` | tree | 59 | 96 / 96 | 0 |
| `7rock01` | rock | 32 | 0 / 0 | 0 |
| `7rock03` | rock | 19 | 0 / 0 | 0 |
| `7rock02` | rock | 16 | 0 / 0 | 0 |
| `7rock07` | rock | 16 | 0 / 0 | 0 |
| `7rock04` | rock | 13 | 0 / 0 | 0 |
| `7rock05` | rock | 6 | 0 / 0 | 0 |
| `dec63` | beacon fire | 1 | 64 / 160 | 128 |
| `dec69` | magic pedastal | 1 | 64 / 190 | 64 |
| `dec75` | magic pedastal | 1 | 64 / 190 | 64 |
| `dec70` | magic pedastal | 1 | 64 / 190 | 64 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 35 / 129 | 72 | 31 |
| rocks | 6 / 102 | 78 | 0 |
| lights | 2 / 4 | 3 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm7/out10_decor_settlement.png)

Highlighted source anchors: #154 `tree33` at [2864, -14376, 512]; #233 `dec69` at [3312, -9488, 512].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm7/out10_decor_landscape.png)

Highlighted source anchors: #155 `tree33` at [-376, -5816, 666]; #38 `7rock02` at [1296, -384, 527].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Build ground connectivity from passes and valleys first, then sculpt enclosing heights within native limits. Explicitly define optional flight access rather than assuming every point on a painted minimap is walkable.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Walk required valley routes, check dungeon/house arrivals against steep terrain, test flight over ridges if intended, and inspect snow transitions. Test repeated per-character rewards and global quest persistence.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm7/maps/out10.odm](../../../assets_dev/worlds/mm7/maps/out10.odm)
- [assets_dev/worlds/mm7/maps/out10.scene.yml](../../../assets_dev/worlds/mm7/maps/out10.scene.yml)
- [assets_dev/worlds/mm7/events/maps/out10.lua](../../../assets_dev/worlds/mm7/events/maps/out10.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_2.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_2.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT10.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT10.txt)
- [assets_dev/worlds/mm7/events/maps/out10_mmmerge.lua](../../../assets_dev/worlds/mm7/events/maps/out10_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
