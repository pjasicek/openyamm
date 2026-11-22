# Xeen Enchanted Boulder (D5 Desert of Doom: D-49 Q3), 2026-11-21

Lane S (session 10). The world decoration `xeen_boulder` (row 4014, sprite 27014): a great desert sandstone rock with a
weathered bearded face carved half sunk into its front. D5 has seven, in two chained rings (the sign and boulders 3-6
east, 1, 2 and 7 west; 7 asks "What am I?"); the others crumble to sand after the answer, all hover "An Enchanted
Boulder". Static. Hand-built from shipped models and textures: **no Meshy, no Codex, 0 credits**.

| | |
|---|---|
| Installed source | `assets_source/worlds/xeen/models/xeen_deco_boulder.glb` (`tools/install_model.py --world xeen`) |
| Runtime copy | `assets_dev/worlds/xeen/models/xeen_deco_boulder.glb` (cooked) |
| Binding | `assets_dev/worlds/xeen/models/decorations.yml`: `xeen_boulder`, height 279.7, `yaw: facing`, `yaw_offset: -1.570796327`, `lod_pixels: [300, 150, 60]` |
| Size (units, 1:1) | 300 across (x), 330 front to back, 264 above the origin, a 16 skirt below it |
| LOD triangles | 6,199 / 3,099 / 1,548 / 773 (about 2,100 of LOD0 on the face) |
| Texture | one material: base colour 2048 (sRGB), normal 2048, metallic-roughness 1024 |

## Sources

- Rock: `assets_source/engine/models/mm8_deco_rock26.glb` (shipped MM8 great rock; only its shape, LOD0, welded,
  scaled to 300 x 331 x 291, flat-cut underside).
- Face: the MM6 mage `assets_source/worlds/mm6/models/mm6_pmn2.glb` (bearded; rest pose). Surveyed and not used:
  the titan (helmeted), the djinn, peasant, nobleman, ogre and others (`work/heads_sheet.jpg`; rocks in
  `work/survey_sheet.jpg`).
- Stone: `assets_source/worlds/mm6/textures_x4/egywalh.png` (the weathered sandstone of D5's egy BModels), as colour
  grain and as bump in the normal bake.

## Route (`build.sh`, all scripts in `scripts/`, settings in `scripts/boulder.json`)

1. `build_mesh.py` (Blender): the rock; the mage's head scaled to 210 chin to crown, depth x1.5 (bolder carving),
   leaned back 8 degrees, the nose tip 26 in front of the rock's surface. The head becomes a **relief**: its front
   surface read as a height field by rays every unit over the front view, inside an ellipse around brow, cheeks and
   beard; toward the ellipse's rim it sinks smoothly to 25 inside the rock (no ledge), outside it is rock; a 1.6-unit
   blur weathers it (strands, lids and lips soften; brow, nose, mouth line and beard mass stay). Relief slab and rock
   are united by a 1.1-unit voxel remesh, the joint smoothed, the face eroded (2 Laplacian passes), and two octaves of
   value noise displaced along the normals (5 units at 60, 1.2 at 14; the face takes 0.6 / 0.5 of them). The
   underside below -15 is open. LOD0: collapse decimation to 6,200 with the face weighted denser (rock weight 1, face
   0.5 in the decimate vertex group).
2. `lowbake.py`: UVs by `claude_shared/uv_atlas.py` (PartUV, seam pass, sparrow packing, 4-texel margin, face x1.4),
   Cycles bakes from the 735k-triangle high: tangent normal (egywalh bump), AO over 2 m and 0.35 m with a ground plane.
3. `finish_maps.py`: per texel position and normal; egywalh triplanar (128 and 480 per tile) on a weathered sandstone
   ramp (110,76,46)-(208,164,110), strata, broad patches, dark streaks down steep faces, AO darkening (eye sockets,
   mouth), wind-blown sand in up-facing crevices, on tops and at the foot; chroma 1.3, gain 0.84 (the in-game sky
   ambient greys warm stone, as on the sphinxes); roughness 0.86-0.97, metal 0; normal misses flattened; nearest-texel
   gutter fill last on every map.
4. `export_boulder.py`: LOD1-3 by collapse decimation of LOD0 at 0.5 / 0.25 / 0.125 (hard edges above 60 degrees),
   one material; `tools/link_static_model_lods.py`; `check_winding.py`: **0 inverted closed parts**.

Texture measures (`texture_quality.py`, `work/texture_quality.json`): atlas 66.8 %, density spread 1.12, stretch p90
1.16, 26 islands (fragments 0.1 %); about 2.9 texels per unit. LOD0 shading is smooth (as baked); the UV seams lie on
smooth rock, so they carry no hard edge (the normal bake was made against those normals).

```sh
cd level_generation/decorations/xeen_boulder_claude
./build.sh [--review]              # about 10 min; --from maps reuses the mesh and bakes
python3 ../../../tools/install_model.py level_generation/decorations/xeen_boulder_claude/export/xeen_deco_boulder.glb \
    --world xeen --name xeen_deco_boulder.glb       # from the repository root
```
Sparrow packing is stochastic: a full rebuild changes the UV layout (the bakes follow). Set the binding height to the
new LOD0 bounds if the mesh changes.

## Origin, facing, footprint

- Origin: the ground under the rock's middle (x 0, z 0); the model spans z -15.7 (skirt) to 264.0, so the binding
  height 279.7 keeps it at 1:1. Place **z = the terrain height** there; no `z_offset` (the skirt covers up to about 15
  of slope under the rim; on steeper ground sink it a little).
- The face is on glTF +Z. With the binding's `yaw_offset` the map facing is the way the face looks: **facing 0 east,
  90 north, 180 west, 270 south** (checked in game: facing 270 shows the face to a camera south of it).
- Footprint: x -150..150, front to back -167..164; at the ground the outline's p90 radius is 168, its farthest corner
  189; above 120 the p90 radius is 144.

## For A2 (decoration_data.txt row 4014, not edited here)

Radius **165** (the ground outline's p90; corners reach 189) and height **280** (the model's 264 above the ground plus
the skirt; 264 if the height is meant above the ground). The row's current 210 / 420 are larger than the model.

## For A6 (D5 placement, `output/studio_cal/d5/tools/gen.py`)

- The binding's name contains "boulder", so `BOULDER_MODEL` now finds `xeen_boulder`; give each boulder a facing.
  Suggested: **outward from its ring's centre** (`atan2(y - cy, x - cx)` in world axes, degrees; the scene check used
  west ring 270, 150, 30 for boulders 1, 2, 7 and east ring 88, 16, 304, 232 for 3-6), or boulder 7 toward the west
  road so the riddle face greets the party.
- The rings put neighbours 353-364 apart; at 300 across and 330 deep the boulders nearly touch (gaps about 30-60, see
  `review/ingame_v2/06-west_ring_700.png`, `08-east_ring_900.png`). D-49's 400 chain allows at most about 40 more
  between neighbours (west ring radius up to 230, east up to 340), which opens gaps of about 70-100; beyond that the
  rings would break the chain.
- The outdoor bake must be redone once the boulders replace rock24 (they cast into it); A6 bakes
  (`tools/lighting/stale_bakes.py`).

## Checks (`review/`)

- `renders/` and `renders_sheet.jpg` (Cycles, eye 170, desert sun): head-on from 300, 1,000 and 3,000, a face close-up,
  three-quarter, side, back, LOD0-3.
- In game (`build-xeen`, D5 from assets_dev with an overlay scene that turns A6's rock24 stand-ins of both rings into
  `xeen_boulder` facing outward: `scripts/ingame_scene.py`, `--extra-mount work/ingame/mount`, screenshot tour
  `work/ingame/tour.yml`, noon, clear sky): `ingame_v2/` (final colour) and `ingame/` (the first, paler colour).
  Boulder 1 head-on from 300, 1,000 and 3,000 (`01`-`03`), three-quarter (`04`), boulder 7 (`05`), the west ring
  (`06`), side (`07`), the east ring on the sand (`08`). The face reads (brow, eyes, nose, beard) at 300 and 1,000; at
  3,000 it is a great rock. No model or table warnings in the run logs.

## Known limits

- The face is the MM6 mage's, softened: calm, not expressive; the mouth hides under the moustache, so the riddle face
  reads as brow, nose and beard.
- 5.5 % of the normal map's island texels (mostly the underground skirt and the open underside's rim) are flat-filled.
- `ingame` shots use the debug scene overlay, not A6's build; the 18:00 shot is still full daylight in D5.
- `level_generation/update_gitignore.py` also listed another lane's `sounds/xeen_20261120/picks.yml` (over 256 KB) in
  `level_generation/.gitignore` when run for this project.
