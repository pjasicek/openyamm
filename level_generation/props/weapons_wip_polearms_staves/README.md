# Polearms and staves — 2026-10-18

All **60 assigned icons are rebuilt, installed and visually reviewed**: 45 spear-family weapons and 15 staves.
The desktop cook verification passed for each exact installed model. The remaining integration handoff is a
coordinator-owned bounds refresh for 58 bindings; their proposed values are recorded below. Binding lengths,
item IDs, mappings and the original test save are unchanged.

The assignment is [weapon session 03](../items_claude/weapons_parallel_20261018/03_polearms_staves.txt).
World items remain isolated WIP, with no release promotion, staging or commits.

## Review

Each contact sheet compares the inventory icon with the replacement from above, three-quarter, low side and
underside. Full-size renders are under `review/finished/`. Matching neutral clay and UV checker sets are under
`review/finished_clay/` and `review/finished_checker/`, with contact sheets for both.

| Icons 1–30 | Icons 31–60 |
| --- | --- |
| [01](review/finished_contact_1.png) | [06](review/finished_contact_6.png) |
| [02](review/finished_contact_2.png) | [07](review/finished_contact_7.png) |
| [03](review/finished_contact_3.png) | [08](review/finished_contact_8.png) |
| [04](review/finished_contact_4.png) | [09](review/finished_contact_9.png) |
| [05](review/finished_contact_5.png) | [10](review/finished_contact_10.png) |

Twenty-one complex models have one LOD at approximately half their base triangle count. Their base/LOD/low-side
comparisons are [01](review/lod_comparison_1.png), [02](review/lod_comparison_2.png) and
[03](review/lod_comparison_3.png). A quarter-resolution pilot damaged small sculptural features and was rejected.
The simpler models retain their adequate base mesh.

Native checks used the current desktop binary on **NVIDIA, OpenGL 3.3, Wayland**, in bounded isolated runs:

| Capture | Directly reviewed icons |
| --- | --- |
| [Outdoor A](review/native_outdoor_a/outdoor_a.png) | 7item031, 7item039, 7item225 |
| [Outdoor B](review/native_outdoor_b/outdoor_b.png) | item050, item250, item083 |
| [Outdoor C](review/native_outdoor_c/outdoor_c.png) | staff3, item082, item080 |
| [Outdoor low](review/native_outdoor_low/outdoor_low.png) | item041, 7item063, item045 |
| [Dim interior A](review/native_indoor_a/indoor_a.png) | 7item036, item045, staff3 |
| [Dim interior B](review/native_indoor_b/indoor_b.png) | 7item063, item080, item082 |

These cover round timber, forged blades and sockets, curved tines, wood thorns, gemstone fittings and cages,
sculpted heads, coiled organic bodies, ivory bone, leather, crystal, steel and gold. All six runs passed visual
review for physical depth, separated components, material colour and ground contact. Metals remain legible in
the dim interior; no renderer or material-brightness workaround was needed. These captures are visual checks,
not a performance benchmark. Native plans, run records and game logs are retained in `work/native_plan.json`,
[native review](receipts/native_review.json) and `receipts/native_runs/`.

An earlier pilot launch failed because the desktop executable did not recognize the coordinator's `bounds`
manifest key. The coordinator's updated binary resolved this; the pilot and all six final runs subsequently passed.

## Construction and textures

**Merlin / Power Staff socket correction (2026-10-18):** both already shared identical geometry, but the
ram head's socket was offset from the shaft because placement used the skull/horns' whole bounding box.
The builder now aligns the lower socket cross-section with the shaft axis, retaining the tenon's overlap.
Both 4,384-triangle bases and 2,192-triangle LODs were rebuilt, installed and scoped-cook verified.
Geometry equality and socket-contact assertions guard rebuilds. See the
[native pair capture](review/staff_socket_fix/native/merlin_and_power_staff.png) and
[validation receipt](review/staff_socket_fix/validation.json). No new generation or credits were needed.

Fifty models use Blender construction: closed round profiled hafts, separate sockets, ridged blade sections,
swept round tine cores, individual thorns and solid gemstone fittings. The four large gem staffs have a solid
gem, shaped neck and separate cage fingers. Blade cutting outlines follow the icon; source icon colours are
never projected unchanged as albedo.

Six models combine Blender hafts with five distinct Meshy heads. Four use three distinct Meshy whole-body
sculpts. All eight Smart Topology jobs succeeded at five credits each: **40 Meshy credits total**, no paid retries.
The worker's Meshy claim is released. Raw outputs, HD masters, requests, task IDs and receipts remain in `meshy/`.
The green skull's crossed internal sheets were reconstructed as a closed solid; the grapple's small local hole
was capped. Both were rebaked and passed the final topology checks.

Geometry/art reuse is limited to pixel-identical source designs:

- `6trident5` → `trident3`.
- `item331`, `item341` → `item045`.
- `6staff4` → `staff3`.
- `item335` → `item083`.

The result is 55 distinct designs. Base meshes range from **692 to 7,074 triangles**, totalling **180,840** across
the 60 bindings. LOD meshes total 49,366 triangles. Per-icon counts, bounds, material counts, hashes, source paths,
native coverage and job attribution are in [ledger.json](ledger.json).

Imagegen painted the cylindrical UV layouts and six-view sculptural guides. Shaded first-pass head paintings
were superseded by flat albedo revisions. The selected Ethric master retains its real lower blue gems; the
revision that removed them is retained as superseded. There were 81 image generations, including revisions.
Exact prompts and image hashes are retained under `receipts/image_*.json`.

Body atlases are 512×1024; sculptural atlases are 1024×1024. Maps use sRGB base colour, linear packed
occlusion/roughness/metallic and linear OpenGL +Y normals. Physical region masks keep wood, leather, bone,
keratin, enamel and gems nonmetal. Roughness follows surface class rather than pigment brightness. Gemstones
use opaque PBR surfaces; no refraction shader was added. Cylindrical wrap seams keep smooth radial normals
to avoid a visible weld line; cutting edges and sculptural hard corners keep deliberate sharp normals.

## Installation and handoff

Editable exports are `work/finished/pole_<icon>_export.glb`. Authoring blends are under `work/blend/`.
Original source models and baseline renders remain under `work/baseline/` and `review/baseline/`.

Each replacement was installed with `tools/install_model.py --world-items --name item_<icon>.glb`, then verified
with `tools/cook_models.py --verify --profile desktop --only engine/world_items/models/item_<icon>.glb`.
The installer guarded every source against its original or this worker's last installed hash. The 178 referenced
runtime textures occupy 37,674,516 bytes. Receipts: [installed models](receipts/installed.json),
[cooked textures](receipts/cooked_textures.json), [mesh checks](review/validation.json),
[final checks](receipts/final_checks.json), and the per-icon install logs.

**Coordinator action:** apply the 58 [proposed bounds updates](receipts/proposed_bounds_updates.json) to the
shared `assets_dev/engine/world_items/items.yml` after workers finish. Values were computed with
`item_model_shapes.item_bounds()` without modifying the manifest. Lengths stay unchanged. Stale bounds can affect
picking/collision boxes; this worker did not edit the coordinator-owned manifest.

[handoff.json](handoff.json) is the machine-readable handoff. All assigned art is present and reviewed, with no
remaining mesh/material defects. Android cooking/device checks and release packaging were not run.

The original `saves/Ground items test.oysav` still hashes to
`795fffeb87a7d95962e0e4e5af72b166ca9b6986400f43ad96c0d95edbe2fffa`.
