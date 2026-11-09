# Daggers and axes — completed isolated WIP

All **69 assigned icons** (31 daggers, 38 axes) have replacement source GLBs and verified desktop runtime models.
The [per-icon ledger](ledger.json) records exports, authoring scenes, original bindings, triangles, materials,
Meshy receipts, exact hashes and review evidence. [handoff.json](handoff.json) is the coordinator handoff.
Shared bindings, item IDs, lengths, pickup/save behavior and engine code were not changed.

48 icons use closed Blender components: diamond-section blades, distinct guards and pommels, round or oval
hafts, thick axe cheeks tapering to their edges, and physical sockets. 17 Meshy Smart Topology jobs cover
21 ornate icons, followed by topology cleanup, six-view generated paint and explicit mixed-material PBR.
Sharktooth received a closed leather grip/collars; Amuck received a reconstructed crescent/socket/fork while
retaining its sculptural handle and dragon poll. The dagger and long axe pilots preceded the batch.

The eight reused variant pairs have pixel-identical reference icons; all pairs are listed in the handoff.
There are 61 distinct reference designs. Meshy consumed **85 credits**; all 17 paid jobs succeeded.
Original HD masters, requests, job results, paint/mask atlases, prompts and receipts remain in this project.

## Review

- [Icon / clay / PBR comparisons, page 1](review/contact_01.png), pages 02–09 alongside it; every icon has
  individual above, three-quarter, low, back and underside renders under `review/clay` and `review/revised`.
- [Native outdoor contact sheet 1](review/native_final_contact_01.jpg), sheets 02–08 alongside it;
  `review/native_final` retains 69 ordinary-distance and 17 lower-angle captures.
- [Dim interior, ordinary](review/native_indoor_final_ordinary/settled_weapons.png) and
  [lower angle](review/native_indoor_final_low/settled_weapons.png): 12 representative steel, gold,
  dark iron, leather, coated and sculptural items, captured after physics settled.
- [LOD silhouette comparison](review/lod_contact_final.jpg): all 17 sculptural masters at both reduced levels.
- `review/baseline` preserves the original five-angle renders; `baseline` preserves original GLBs.

Final native runs used the existing desktop build on NVIDIA/OpenGL under Wayland, MM7's ground-item save
and MM6 `6d19.blv`. Their logs/run records are retained in `review/native_runs`.
Final runs have no model-load failures or placeholders. Earlier trial captures are retained as work history;
use the `native_final` and `native_indoor_final_*` directories for acceptance evidence.

## Technical results

All 69 exports pass [geometry validation](review/validation.json): finite vertices, closed boundaries on
every LOD, positive component winding, nondegenerate triangles, valid UVs, identity mesh nodes, centred
footprints and real contact at zero. The [authoring audit](review/geometry_audit.json) reports no missing
UV seams on hard edges. Mordred has one coincident contact edge between closed components, with no open boundary.
No global thickening or source-icon albedo projection was used.

LOD0 totals 159,728 triangles across 69 icons, ranging from 276 to 5,500 per icon. Sculptural models include
approximately half/quarter static LODs, for 238,520 triangles across all serialized levels and icons.
The 48 simpler Blender icons already have 276–2,038 triangles and retain one mesh. No engine-driven LOD exception.

[Material validation](review/material_validation.json) covers 55 unique embedded PNGs: 54 at 1024² and one
256² stone map, totalling 27,359,735 PNG bytes before runtime cooking. These are shared texture payloads,
not a per-instance memory estimate. Binary metallic masks distinguish metal from leather/wood/gems/coating;
roughness is fixed by physical material, independent of brightness. Base texture channels are within 30–243.
Faceted gems use constant dielectric material factors; stone roughness is .83. Every normal-map orientation
measurement was positive ([log](review/normal_convention.log)); no engine material adjustment was needed.

Six-view paint projection directly covers 61.8–98.8% of occupied UV texels. Self-occluded coil/socket interiors
receive nearest covered material texels; the handoff records each coverage measurement. Above, side, back
and underside renders were inspected after painting. The rejected second Hell's Cleaver mask is retained
as provenance; the original physically valid smooth-dielectric neck classification was selected.

All 69 installed source/runtime hashes and exact scoped desktop cooks pass
[installation verification](review/cook_verification.json). No blanket cook, engine build, Android/Vulkan
check or release promotion was performed. `world_items` remains isolated WIP.

## Reproduce checks

From the repository root:

```sh
python3 level_generation/props/weapons_wip_daggers_axes/scripts/validate_weapons.py --complete
python3 level_generation/props/weapons_wip_daggers_axes/scripts/verify_materials.py
python3 level_generation/props/weapons_wip_daggers_axes/scripts/verify_installed.py
```

Authoring scripts live in `scripts`; `designs.json` records distinct construction decisions.
Use `scripts/install_reviewed.py` only for this ownership list and only after renewed validation/review.
