# Dragon's Lair — MM6 `zddb01.blv`

**Study focus:** Single cavern; smallest geometry baseline

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm6/zddb01.json) · [Blender view metadata](../../evidence/mm6/zddb01_blender.json)

## Layout and visual reading

A single elongated, tapered cavern with an uneven perimeter and sloping upper surfaces. The ceiling-free render exposes a broad floor surrounded by a few large wall bands. There is no portal graph beyond one occupied sector; this is a useful first native-room fixture, not a mechanism reference.

![Measured plan of Dragon's Lair](../../evidence/mm6/zddb01.png)

![Blender inspection view of Dragon's Lair](../../evidence/mm6/zddb01_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| Vertices / faces | 68 / 104 |
| Occupied sectors / portal faces | 1 / 0 |
| BSP nodes / automap outlines | 56 / 78 |
| Native door state records | 0 |
| Explicit lights / radius range | 11 / 64, 640 |
| Occupied-sector ambient values | 22 |
| XYZ bounds, game units | [-768, -1594, 0] to [1664, 2604, 968] |
| Native entities / spawn records | 11 / 0 |
| Initial scene actors / chest records | 1 / 20 |
| Directly bound chest slots | none (0 distinct) |
| Directly bound / declared map events | 1 / 1 |
| Selected face flags | secret: 0; invisible: 0; animated: 0; clickable: 2; pressure_plate: 0; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `d2ceil4` (83); `D2flor5` (19); `T3D2B` (1); `T3D2A` (1).

Map-stat row: [189 / Dragon's Lair](../../../assets_dev/engine/data_tables/map_stats.txt#L192).

Treasure **6**, Perception difficulty **0**, disarm **1**, trap d20 count **1**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | DragonCover | 2 | 1-2 | 0 |
| 2 | 0 | 1 | 1-4 | 0 |
| 3 | 0 | 1 | 1-4 | 0 |

The current merged MM6 treasure value is not evidence of original-game balance; choose new-map loot
deliberately and check chest-template remapping and active difficulty overrides.

## Event behavior to inspect

The directly bound interaction is the exterior exit. The scene contains one actor and placed objects, but no directly bound chest slot despite the legacy chest-record allocation. Do not invent a chest merely because a state slot exists.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [1](../../../assets_dev/worlds/mm6/events/maps/zddb01.lua#L19) | 2 | MoveToMap; destinations: outc3.odm |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

The lair uses nine wall torches and two floor campfires, with a broad clear interior. The fire pair supplies a focal point without filling the cavern with furniture. Treat this as one possible inhabited-lair treatment, not a rule that every dragon cave needs torches.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm6/zddb01_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm6/zddb01_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm6/zddb01_decorations.png)

Native entity records: **11**; initially drawable sprite records: **11**; drawable decorations with descriptor light radius: **11**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| lights | 11 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `6torch01` | torch | 9 | 8 / 52 | 256 |
| `dec04` | campfire | 2 | 16 / 0 | 128 |

![room — annotated native decoration study](../../../level_generation/evidence/mm6/zddb01_decor_room.png)

Highlighted source anchors: #5 `dec04` at [260, 1348, 0]; #3 `6torch01` at [944, 1832, 168]; #4 `6torch01` at [280, 2536, 168].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Start with an asymmetric footprint and a few height bands, then inspect wall slope and floor clearance at eye height. Keep the compact rock palette and avoid turning the perimeter into a regular cylinder. Add a chest or second entrance only as an explicit new design feature.

## Follow-up review

Verify entry/exit placement, full floor traversal, sloping-wall collision and appropriate creature clearance. Compare the complete-ceiling player view with the cutaway; the cutaway alone understates enclosure.

Scope runtime checks to new mechanisms or unresolved behavior using the [review policy](../../REVIEW_CHECKLIST.md).

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm6/maps/zddb01.blv](../../../assets_dev/worlds/mm6/maps/zddb01.blv)
- [assets_dev/worlds/mm6/maps/zddb01.scene.yml](../../../assets_dev/worlds/mm6/maps/zddb01.scene.yml)
- [assets_dev/worlds/mm6/events/maps/zddb01.lua](../../../assets_dev/worlds/mm6/events/maps/zddb01.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/ZDDB01.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/ZDDB01.txt)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
