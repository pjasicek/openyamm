# Angel Statuette (`7item263`) — 2026-10-18

**Installed.** The one icon the [sculpture batch](../items_wip_sculpture/README.md#deferred-angel) deferred: image
generation refused this nude classical statue twice, so it is built entirely in Blender with no generated images.

[Review views beside the icon](review/final_contact.png) · [in game beside the Knight Statuette](review/native_outdoor_contact.jpg)

| | |
|---|---|
| Design | Standing winged woman in contrapposto (left hand on hip, right arm hanging, head turned up), wings swept back and up, on a two-tier plinth; faces glTF +Z like the other statuettes |
| Geometry | 2,858 triangles, one closed manifold mesh; zero exposed back faces from 60 sampled directions, no inverted corner normals, winding check 0 |
| Materials | 512 px base colour, packed metallic/roughness and OpenGL tangent normal maps baked from a 208k-face source: bronze (metallic 1) with mottled darker patina patches (roughness 0.34-0.62 following them), lighter worn edges and baked occlusion darkening recesses; dark pitted stone plinth (metallic 0, roughness 0.85). The normal map carries feather-barb and hair striations, cast-bronze grain and stone pits. Single-sided. [Close-up](review/final_closeup.jpg) |
| Binding | Height 112.5 (the icon's opaque height x 0.9), so length 91.2 (longest horizontal side, the swept-back wings); bounds from `tools/item_model_shapes.py` |

The old binding (length 112.5) belonged to a flat relief lying down; kept as a horizontal length it would have
made the standing statue about 190 units tall. Source and runtime baselines are in `references/`.

## Rebuild

```sh
blender --background --python level_generation/props/sculpture_angel_20261018/scripts/build_angel.py
blender --background --python level_generation/props/sculpture_angel_20261018/scripts/review_angel.py -- \
  level_generation/props/sculpture_angel_20261018/work/angel_export.glb level_generation/props/sculpture_angel_20261018/review/final
python3 tools/install_model.py level_generation/props/sculpture_angel_20261018/work/angel_export.glb --world-items --name item_7item263.glb
```

`build_angel.py` builds a skin-modifier figure with head, hair bun and anatomy volumes, individually modelled wing
feathers and a bevelled plinth, voxel-merges them (0.0032), collapse-reduces a copy to the budget, removes
crossings with an exact self-union (separating touching folds with the helper from
`items_wip_equipment_geometry_finish/scripts/resolve_self_intersections.py`) and bakes the source onto it. The
source material carries the bronze mask only as emission for the metallic bake, because Cycles bakes diffuse colour
as albedo x (1 - metallic). Earlier review iterations `review/v1`–`v4` are retained.

Checks: desktop cook verify passed; `*Item model*` unit tests pass; MM7 review-save outdoor run on NVIDIA/OpenGL 3.3
exited 0 (`receipts/`). No indoor run, Android cook, build or commit.
