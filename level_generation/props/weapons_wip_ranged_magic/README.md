# Ranged and magic ground weapons — 2026-10-18

All **56 assigned WIP models** rebuilt and installed: 36 bows/crossbows, five blasters and 15 wands.
The authoritative per-icon results are in [ledger.json](ledger.json) and [handoff.json](handoff.json).
Source item IDs, icon/model mappings and binding lengths are preserved. Shared bindings and engine code were not edited.

## Review

Every design has four clay and four textured views alongside its original inventory icon:
[1](review/contact_01.png), [2](review/contact_02.png), [3](review/contact_03.png),
[4](review/contact_04.png), [5](review/contact_05.png), [6](review/contact_06.png), [7](review/contact_07.png).
[Acceptance records](review/acceptance.json) bind visual review to the exact exported GLB hashes.

Native review contains 110 final captures on NVIDIA/OpenGL 3.3: all 56 actual ground items in the supplied
MM7 save, plus ordinary and low-angle views of 25 representative construction/material combinations outdoors
and in the dim MM6 dragon cave. Indoor material checks use console model instances at the actual binding lengths
on verified flat floor face 12, replacing each instance in an unobstructed spot. Outdoor checks use actual world
items, including their native ground placement and item renderer. No renderer or material exceptions were needed.

| Native review | Contact sheets |
|---|---|
| All 56 installed ground items | [Coverage](review/native_coverage_contact.png) |
| Outdoor representatives | [1](review/native_outdoor_1_contact.png), [2](review/native_outdoor_2_contact.png), [3](review/native_outdoor_3_contact.png), [4](review/native_outdoor_4_contact.png), [5](review/native_outdoor_5_contact.png) |
| Dim indoor representatives | [1](review/native_indoor_1_contact.png), [2](review/native_indoor_2_contact.png), [3](review/native_indoor_3_contact.png), [4](review/native_indoor_4_contact.png), [5](review/native_indoor_5_contact.png) |

[Native coverage and fixture](review/native_coverage.json), [accepted runs](review/accepted_native_runs.json)
and [native receipts](receipts/native/) preserve exact tours, logs, binary hashes and screenshot hashes.
Earlier ramp/obstructed placement experiments and pilot captures are superseded by these accepted runs.
The final runs use the normal shared assets root and a preserved copy of the matching coordinator-built binary,
so another session relinking the executable cannot interrupt a tour. The private asset-mount experiment recorded
in receipts/review_asset_mount.json is superseded.

## Construction and materials

Blender component construction replaces the old icon reliefs: rounded bow limbs and real strings, transverse
crossbow prods with stocks and mechanisms, complete blaster barrels/housings, and solid wand shafts, heads,
gems, skulls and antlers. A component intersection/touch audit verifies one supported assembly per weapon;
individual parts are closed and outward-facing. Ground support is selected from the convex hull using the
volume-weighted centre of mass, then normalized to footprint centre and zero lowest contact.

There are **50 construction/material configurations**, **101,092 LOD0 triangles** in total and a maximum
of **3,634 triangles** per item. Ten models have an approximately half-size LOD1. Remaining models have at most
2,688 triangles. Matching reused variants are 6bow6/6bow7/bow5 (Stellar), 7item045/7item300/7item301
(Compound), item059/item336 (Warbow), and item060/item344 (Devilbone).

Each model uses one mixed PBR material and a shared 2048-square base-colour, normal and metallic/roughness set.
[UV guide](textures/material_uv_guide.png), [exact imagegen prompt](textures/PROMPT.txt),
[raw generated painting](textures/material_atlas_raw.png), [surface semantics](textures/surface_semantics.json)
and [generation receipts](textures/generation_runs.json) are retained. The original icons guide design and colours;
they are not projected onto the mesh. Metal/wood/leather/bone/gem separation uses a semantic binary mask.
Roughness follows material identity; the +Y normal map uses fine surface grain rather than the icon's lighting.
One built-in imagegen call; **zero Meshy jobs and zero Meshy credits**.

## Validation and handoff

[Validation](receipts/validation.json) covers exported winding, normals, UVs, nondegenerate triangles, image
encoding, material mask, dimensions, ground contact and LOD linkage. [Assembly](receipts/assembly.json) and
[Blender reimport](receipts/reimport.json) additionally check supported components, all 56 reimported GLBs,
checker pilots and LOD previews. Every owned install used the serialized authoritative installer and passed its
scoped desktop cook verification with zero problems: [install receipts](receipts/installed.json).
Original source models and their hashes remain in references/baseline/ and ledger.json.

The generator and checks live in scripts/. Rebuild only selected icons with Blender's
`-- --icons <icons...> --render`; check selected exports with `scripts/check_weapons.py`, then use
`scripts/install_owned.py` for owned-only installation. `scripts/finish_handoff.py` rechecks every final source,
runtime, acceptance and baseline hash before writing the handoff. Do not run a whole-family installer.

[Proposed bindings with bounds](proposed_bindings_with_bounds.json) supplies final LOD0 engine-axis bounds for
coordinator merge. It preserves every assigned length and model/icon mapping; no length corrections are proposed.
The worker has not applied these coordinator-owned manifest edits.

Android cooking/device rendering was not checked. This remains isolated WIP: no release promotion, global build
or global cook was performed. The retained item-model unit-test receipt records two cases and 932 assertions
from the available binary before concurrent coordinator engine changes; it is not a fresh validation of those changes.
