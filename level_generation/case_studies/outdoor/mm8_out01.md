# Dagger Wound Island — MM8 `out01.odm`

**Study focus:** Dagger Wound Islands; archipelago with linked progression

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm8/out01.json) · [Blender view metadata](../../evidence/mm8/out01_blender.json)

## Layout and visual reading

Several islands, a settlement, built links and a volcanic landmark form a route network across extensive water. The islands' connection order matters more than straight-line separation. The full-map plan should show transport links explicitly.

![Measured plan of Dagger Wound Island](../../evidence/mm8/out01.png)

![Blender inspection view of Dagger Wound Island](../../evidence/mm8/out01_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| BModels / BModel faces | 128 / 6740 |
| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |
| Terrain height range, game units | 0, 6432 |
| Master tile / four lookup banks | 0 / 198, 126, 90, 414 |
| Distinct raw tile IDs / raw road-bank cells | 97 / 128 |
| Water-flag / burn-flag cells (may overlap) | 11521 / 0 |
| Native entities / spawn records | 800 / 50 |
| Initial scene actors / chest records | 62 / 20 |
| Directly bound chest slots | 0, 1, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 (18 distinct) |
| Directly bound / declared map events | 115 / 140 |
| Selected face flags | secret: 0; invisible: 376; animated: 0; clickable: 4532; pressure_plate: 40; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `Trim9_32` (552); `bwoodb1` (439); `TRIM1_16a` (308); `gn_mtl03` (234); `t14a05b` (216); `btrima1` (200); `T03A05C` (168); `T03A11B` (164).

Common native tile assignments: `126` → `wtrtyl` (9309 cells); `162` → `grastyl` (1118 cells); `127` → `wtrtyl` (602 cells); `129` → `wtrtyl` (577 cells); `128` → `wtrtyl` (576 cells); `1` → `dirttyl` (317 cells). Full resolution/flags are in the JSON.

Map-stat row: [1 / Dagger Wound Island](../../../assets_dev/engine/data_tables/map_stats.txt#L4).

Treasure **0**, Perception difficulty **0**, disarm **0**, trap d20 count **0**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Lizardmen Warrior | 1 | 2-5 | 0 |
| 2 | Wimpy Pirate Warrior Male | 1 | 1-3 | 100 |
| 3 | Couatl (winged snake) | 1 | 1-3 | 0 |

## Event behavior to inspect

The map combines houses, many travel handlers, scripted spell effects and numerous chest bindings. Well events 101–103 illustrate temporary stats, a capped stat increase and a conditional gold reward. Their limits and party conditions make them distinct mechanics.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [101](../../../assets_dev/worlds/mm8/events/maps/out01.lua#L375) | 51 | StatusText |
| [102](../../../assets_dev/worlds/mm8/events/maps/out01.lua#L385) | 51 | StatusText |
| [103](../../../assets_dev/worlds/mm8/events/maps/out01.lua#L395) | 51 | StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

Palm species and tropical undergrowth accompany round, rectangular and extended thatched buildings. Small vegetation groups and a few trees mark individual buildings and civic spaces; open paths lead around them. The native inventory also includes smoke emitters, which this static sprite study does not simulate.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm8/out01_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm8/out01_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm8/out01_decorations.png)

Native entity records: **800**; initially drawable sprite records: **731**; drawable decorations with descriptor light radius: **3**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| trees | 367 |
| plants | 328 |
| rocks | 11 |
| lights | 3 |
| props | 22 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `tree01` | palm tree | 99 | 16 / 256 | 0 |
| `tree04` | palm tree | 95 | 16 / 256 | 0 |
| `plant05` | fern | 53 | 16 / 8 | 0 |
| `tree08` | palm tree | 43 | 16 / 256 | 0 |
| `plant34` | corn | 43 | 16 / 8 | 0 |
| `plant04` | plant | 42 | 16 / 8 | 0 |
| `tree06` | palm tree | 38 | 16 / 256 | 0 |
| `tree02` | palm tree | 38 | 16 / 256 | 0 |
| `plant01` | plants | 36 | 16 / 8 | 0 |
| `plant25` | flower | 22 | 16 / 8 | 0 |
| `tree03` | palm tree | 20 | 16 / 256 | 0 |
| `tree07` | palm tree | 18 | 16 / 256 | 0 |

| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |
| --- | --- | --- | --- |
| trees | 92 / 367 | 158 | 52 |
| plants | 180 / 328 | 223 | 28 |
| rocks | 4 / 11 | 5 | 5 |
| lights | 2 / 3 | 3 | 0 |
| props | 14 / 22 | 22 | 0 |

Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric
proximity measure, **not** a city boundary: it includes bridges, rocks and other models.
Use these measurements with the actual view and context; they are not universal scatter quotas.


![settlement — annotated native decoration study](../../../level_generation/evidence/mm8/out01_decor_settlement.png)

Highlighted source anchors: #14 `tree04` at [8392, 9216, 1344]; #423 `plant03` at [9584, 10640, 1344]; #422 `rock19` at [7040, 12376, 960]; #778 `dec03` at [8552, 7424, 960].

![landscape — annotated native decoration study](../../../level_generation/evidence/mm8/out01_decor_landscape.png)

Highlighted source anchors: #45 `tree06` at [-512, 960, 1632]; #409 `plant15` at [-3200, 128, 1632].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Design island progression and link activation as a graph before sculpting coastlines. Place settlements and encounters around safe arrivals and intended crossings. Keep local teleport, bridge and exterior travel edges distinct in metadata.

## Default visual and wiring review

Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,
road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):
choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local
garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the
[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.

## Optional deeper runtime diagnostics

Use the following only for new behavior, an observed defect or an explicit driver request:

Test progression and return between islands, bridge/arrival clearance, travel gates and reward repetition under qualifying/nonqualifying party states. Review shoreline transitions and volcanic hazard behavior in the game, not from preview colors.

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm8/maps/out01.odm](../../../assets_dev/worlds/mm8/maps/out01.odm)
- [assets_dev/worlds/mm8/maps/out01.scene.yml](../../../assets_dev/worlds/mm8/maps/out01.scene.yml)
- [assets_dev/worlds/mm8/events/maps/out01.lua](../../../assets_dev/worlds/mm8/events/maps/out01.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [assets_dev/engine/data_tables/terrain_tile_data.txt](../../../assets_dev/engine/data_tables/terrain_tile_data.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Out01.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Out01.txt)
- [assets_dev/worlds/mm8/events/maps/out01_intro.lua](../../../assets_dev/worlds/mm8/events/maps/out01_intro.lua)
- [assets_dev/worlds/mm8/events/maps/out01_mmmerge.lua](../../../assets_dev/worlds/mm8/events/maps/out01_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
