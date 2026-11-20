# Free Haven — MM6 `outc2.odm`

**Study focus:** Free Haven; dense city, rivers and surrounding approaches

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm6/outc2.json) · [Blender view metadata](../../evidence/mm6/outc2_blender.json)

## Layout and visual reading

A dense urban cluster sits within a larger road/river landscape with rural approaches and separate nearby structures. The settlement's local street graph is much denser than the map-wide minimap suggests. River crossings and thresholds must be aligned with the terrain.

![Measured plan of Free Haven](../../evidence/mm6/outc2.png)

![Blender inspection view of Free Haven](../../evidence/mm6/outc2_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 127 / 5475 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 3072 |
| Master tile / four lookup banks | 2 / 90, 126, 234, 774 |
| Distinct raw tile IDs / raw road-bank cells | 90 / 577 |
| Water-flag / burn-flag cells (may overlap) | 2291 / 0 |
| Native entities / spawn records | 461 / 48 |
| Initial scene actors / chest records | 58 / 20 |
| Directly bound chest slots | 1, 2 (2 distinct) |
| Directly bound / declared map events | 139 / 155 |
| Selected face flags | secret: 0; invisible: 20; animated: 0; clickable: 215; pressure_plate: 0; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `BemV` (325); `pbRoof` (292); `BemTilA` (226); `Pbrle` (207); `TAV128WL` (193); `Gset04` (189); `GBCNT` (183); `Pbrre` (179).

Common native tile assignments: `1` → `6dirttyl` (4642 cells); `2` → `6dirttyl` (2375 cells); `3` → `6dirttyl` (2350 cells); `4` → `6dirttyl` (1794 cells); `126` → `6wtrtyl` (894 cells); `127` → `6wtrtyl` (490 cells). Full resolution/flags are in the JSON.

Map-stat row: [144 / Free Haven](../../../assets_dev/engine/data_tables/map_stats.txt#L147).

Treasure **6**, Perception difficulty **0**, disarm **4**, trap d20 count **6**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | BArcher | 2 | 3-5 | 30 |
| 2 | PeasantM2 | 5 | 4-6 | 70 |
| 3 | 0 | 0 | 0 | 0 |

The current merged MM6 treasure value is not evidence of original-game balance; choose new-map loot
deliberately and check chest-template remapping and active difficulty overrides.

## Event behavior to inspect

The scan finds many more house/service interactions than chests. Events 161 and 163 demonstrate a bounded stat reward and charged healing; event 213 is an obelisk contribution to broader quest/autonote state. Global progress must remain distinct from local fountain charges.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [161](../../../assets_dev/worlds/mm6/events/maps/outc2.lua#L695) | 1 | StatusText |
| [163](../../../assets_dev/worlds/mm6/events/maps/outc2.lua#L723) | 8 | StatusText |
| [213](../../../assets_dev/worlds/mm6/events/maps/outc2.lua#L772) | 1 | SetMessage, _PressAnyKey |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Dense town blocks contain L-shaped, U-shaped, long and compact roofs; a shared texture family makes them belong together. Small trees sit beside houses and larger planted green patches break up the built area. Preserve wide traversable streets rather than filling every space with foliage.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm6/outc2_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm6/outc2_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm6/outc2_decorations.png)

Native entity records: **461**; initially drawable sprite records: **455**; drawable decorations with descriptor light radius: **1**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| props | 5 |
| trees | 319 |
| plants | 87 |
| lights | 3 |
| rocks | 41 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `6tree01` | tree | 127 | 96 / 96 | 0 |
| `6tree10` | tree | 91 | 96 / 96 | 0 |
| `6tree18` | tree | 80 | 76 / 96 | 0 |
| `cac8` | cactus | 78 | 52 / 52 | 0 |
| `6tree06` | Food Tree | 19 | 86 / 96 | 0 |
| `6rock13` | rock | 16 | 52 / 52 | 0 |
| `6flower06` | flowers | 9 | 0 / 0 | 0 |
| `6rock12` | rock | 7 | 52 / 52 | 0 |
| `6rock04` | rock | 7 | 52 / 52 | 0 |
| `searkb01` | rock | 7 | 52 / 52 | 0 |
| `searka01` | rock | 4 | 52 / 52 | 0 |
| `smlbarel` | keg | 3 | 30 / 40 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 68 / 319 | 227 | 11 |
| plants | 7 / 87 | 50 | 21 |
| rocks | 7 / 41 | 40 | 0 |
| lights | 1 / 3 | 3 | 0 |
| props | 4 / 5 | 5 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm6/outc2_decor_settlement.png)

Highlighted source anchors: #4 `6tree06` at [6816, 12984, 96]; #346 `6rock04` at [4352, 11568, 256].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm6/outc2_decor_landscape.png)

Highlighted source anchors: #137 `6tree10` at [-240, -3120, 169]; #436 `6rock13` at [-144, -192, 0].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Author urban blocks around connected streets and usable entrances, then integrate bridges and exterior approach routes. Use a service/house manifest to prevent attractive but nonfunctional doors. Share a restrained building palette while varying footprint and placement.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Inspect a dedicated city plan and several street-height views, test every intended service target, bridge contact and travel link, and verify global obelisk state does not reset with the local map.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm6/maps/outc2.odm](../../../assets_dev/worlds/mm6/maps/outc2.odm)
- [assets_dev/worlds/mm6/maps/outc2.scene.yml](../../../assets_dev/worlds/mm6/maps/outc2.scene.yml)
- [assets_dev/worlds/mm6/events/maps/outc2.lua](../../../assets_dev/worlds/mm6/events/maps/outc2.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data_3.txt](../../../assets_dev/engine/data_tables/terrain_tile_data_3.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTC2.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/OUTC2.txt)
- [assets_dev/worlds/mm6/events/maps/outc2_mmmerge.lua](../../../assets_dev/worlds/mm6/events/maps/outc2_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
