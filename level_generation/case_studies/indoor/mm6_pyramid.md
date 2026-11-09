# Tomb of VARN — MM6 `pyramid.blv`

**Study focus:** Tomb of VARN; large vertical architecture and stateful gates

[Index](../README.md) · [Generation playbook](../../README.md) · [Measured JSON](../../evidence/mm6/pyramid.json) · [Blender view metadata](../../evidence/mm6/pyramid_blender.json)

## Layout and visual reading

A monumental central structure sits among dense corridors and stacked spaces. Its roughly 9700-unit vertical span makes the projected minimap heavily ambiguous. The overview reveals the large geometric silhouette but conceals much of the internal route behind floors and tall walls.

![Measured plan of Tomb of VARN](../../evidence/mm6/pyramid.png)

![Blender inspection view of Tomb of VARN](../../evidence/mm6/pyramid_blender.png)

The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study
lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore
transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.

## Measured structure

| Field | Value |
| --- | --- |
| Native container version | 8 (current imported assets, not original-world version) |
| Vertices / faces | 3853 / 3479 |
| Occupied sectors / portal faces | 215 / 234 |
| BSP nodes / automap outlines | 746 / 2571 |
| Native door state records | 23 |
| Explicit lights / radius range | 400 / 16, 3800 |
| Occupied-sector ambient values | 19, 21, 22, 28 |
| XYZ bounds, game units | [-26112, -19331, -1167] to [2560, 19456, 8545] |
| Native entities / spawn records | 446 / 128 |
| Initial scene actors / chest records | 1 / 20 |
| Directly bound chest slots | 1, 2, 3, 4, 5, 6 (6 distinct) |
| Directly bound / declared map events | 59 / 64 |
| Selected face flags | secret: 0; invisible: 0; animated: 0; clickable: 201; pressure_plate: 57; trigger_monster: 0; trigger_object: 0 |

Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,
fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts
include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.

## Materials and population

Most frequent mesh texture keys (face counts, not surface area): `egywlA` (856); `egyceilA` (343); `egyflorE` (252); `pending` (233); `egywlD` (178); `egyflorC` (143); `egybigB` (81); `OrErt64` (67).

Map-stat row: [184 / Tomb of VARN](../../../assets_dev/engine/data_tables/map_stats.txt#L187).

Treasure **6**, Perception difficulty **0**, disarm **8**, trap d20 count **8**, refill **672 days**, encounter chance **10**.

| Encounter slot | Family | Difficulty selector | Count range | Weight |
| --- | --- | --- | --- | --- |
| 1 | Jackalman | 4 | 3-4 | 100 |
| 2 | BGenie | 4 | 2-3 | 0 |
| 3 | BRobot | 1 | 1-2 | 0 |

The current merged MM6 treasure value is not evidence of original-game balance; choose new-map loot
deliberately and check chest-template remapping and active difficulty overrides.

## Event behavior to inspect

The event program combines code questions, inventory/quest checks, map variables, wells, doors and damaging switches. Event 1 gates the central progression; events 8/9 illustrate harmful controls. Follow the code/well sequence through its state conditions rather than copying event numbers into a new map.

| Selected event | Direct binding count | Calls / targets from scan |
| --- | --- | --- |
| [1](../../../assets_dev/worlds/mm6/events/maps/pyramid.lua#L69) | 11 | AskQuestion, FaceExpression, SetDoorState, SetMessage, StatusText; doors: 1 |
| [8](../../../assets_dev/worlds/mm6/events/maps/pyramid.lua#L130) | 5 | DamagePlayer, SetDoorState, StatusText; doors: 8 |
| [9](../../../assets_dev/worlds/mm6/events/maps/pyramid.lua#L136) | 6 | DamagePlayer, SetDoorState, StatusText; doors: 9 |
| [21](../../../assets_dev/worlds/mm6/events/maps/pyramid.lua#L260) | 1 | AskQuestion, FaceExpression, ForPlayer, SetMessage, StatusText |
| [22](../../../assets_dev/worlds/mm6/events/maps/pyramid.lua#L285) | 1 | AskQuestion, FaceExpression, ForPlayer, SetMessage, StatusText |
| [23](../../../assets_dev/worlds/mm6/events/maps/pyramid.lua#L310) | 1 | AskQuestion, FaceExpression, ForPlayer, SetMessage, StatusText |
| [24](../../../assets_dev/worlds/mm6/events/maps/pyramid.lua#L335) | 1 | AskQuestion, FaceExpression, ForPlayer, SetMessage, StatusText |
| [25](../../../assets_dev/worlds/mm6/events/maps/pyramid.lua#L360) | 1 | AskQuestion, FaceExpression, ForPlayer, SetMessage, StatusText |

Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior
that the direct `evt.*` scan does not list. Declared handlers can be unused templates.

## Decoration, architecture and terrain study

The large native torch inventory belongs to many stacked spaces. An ordinary ceiling toggle leaves the outer pyramid and upper geometry covering lower halls; use a labeled height section and a chosen floor. Distribute lights by room and route length, not by dividing the total count uniformly over the minimap.

This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.

[Native placement and palette records](../../evidence/mm6/pyramid_decorations.json) · [Capture poses and highlighted IDs](../../evidence/mm6/pyramid_decor_views.json) · [Generation rules](../../POPULATION_AND_COMPOSITION.md)

![Decoration placement plan](../../evidence/mm6/pyramid_decorations.png)

Native entity records: **446**; initially drawable sprite records: **445**; drawable decorations with descriptor light radius: **445**.

These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,
modeled furnishings, face textures, explicit map lights and later scripted changes are separate.

| Group | Drawable records |
| --- | --- |
| lights | 445 |

| Asset | Hint | Count | Collision radius / height | Descriptor light radius |
| --- | --- | --- | --- | --- |
| `6torch01` | torch | 445 | 8 / 52 | 256 |

![room — annotated native decoration study](../../../level_generation/evidence/mm6/pyramid_decor_room.png)

Highlighted source anchors: #355 `6torch01` at [-9728, -219, 1099]; #402 `6torch01` at [-8163, -354, 2810].

The annotated captures include native first-frame sprite art at source scale and coordinates, with
decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;
geometry above that plane is omitted. They are Blender captures, not game screenshots or proof
of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling
player views and active native state before final acceptance.

## Apply to a new map

Use hierarchical plans: whole structure, floor-specific graphs and local puzzle diagrams. Generate sector/BSP/outline data as first-class output. Reserve a distinctive architectural texture palette and control its repetition on very tall walls.

## Follow-up review

Require floor slices and player-height routes in addition to this cutaway. Test wrong/correct answers, missing prerequisites, recovery after leaving the map, secret/reward accessibility and culling through stacked passages. Do not begin exporter development at this scale.

Scope runtime checks to new mechanisms or unresolved behavior using the [review policy](../../REVIEW_CHECKLIST.md).

These are review suggestions, not gameplay tests executed by this survey.

## Sources and provenance

Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior
references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.

- [assets_dev/worlds/mm6/maps/pyramid.blv](../../../assets_dev/worlds/mm6/maps/pyramid.blv)
- [assets_dev/worlds/mm6/maps/pyramid.scene.yml](../../../assets_dev/worlds/mm6/maps/pyramid.scene.yml)
- [assets_dev/worlds/mm6/events/maps/pyramid.lua](../../../assets_dev/worlds/mm6/events/maps/pyramid.lua)
- [assets_dev/engine/data_tables/map_stats.txt](../../../assets_dev/engine/data_tables/map_stats.txt)
- [reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/Pyramid.txt](../../../reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/Pyramid.txt)
- [assets_dev/worlds/mm6/events/maps/pyramid_mmmerge.lua](../../../assets_dev/worlds/mm6/events/maps/pyramid_mmmerge.lua)

Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,
then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.
