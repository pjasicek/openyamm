# Xeen black basalt boulders (D-40), 2026-11-20

Lane S (session 5). Dressing for X7's Dragon Tower crag: three MM6 rock decorations (`mm6_deco_rock01/04/07`, engine
models) copied and retextured black basalt by `scripts/basalt.py` (mesh, UVs, normal and roughness maps kept; the base
colour's luminance mapped onto a near-black blue-grey ramp, linear 0.010-0.105). No Meshy.

| Decoration | Row / sprite | Model | Height | Collision radius |
|---|---|---|---|---|
| `xeen_basalt1` | 4005 / 27005 | `worlds/xeen/models/xeen_deco_basalt01.glb` | 300 (± 20 %) | 150 |
| `xeen_basalt2` | 4006 / 27006 | `xeen_deco_basalt04.glb` | 340 | 170 |
| `xeen_basalt3` | 4007 / 27007 | `xeen_deco_basalt07.glb` | 380 | 190 |

Bound in `assets_dev/worlds/xeen/models/decorations.yml` (`yaw: facing`, `height_jitter: 0.2`). The crag's own shape is
terrain or BModels (A5); a basalt terrain material, if wanted, is A6's (terrain materials library). Seen in game (debug
spawn on D2 beside the tan source rock: `review/ingame/rocks.png`): dark slate grey in full sun, near black in shade.

Rebuild: `python3 scripts/basalt.py assets_source/engine/models/mm6_deco_rockNN.glb export/xeen_deco_basaltNN.glb`,
`check_winding.py`, `tools/install_model.py <export> --world xeen`. The source GLBs keep the original colour image bytes
unreferenced in their buffer (the cook drops them).
