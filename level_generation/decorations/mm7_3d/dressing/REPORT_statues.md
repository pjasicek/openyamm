# MM7 figure statues: report

Batch folder `level_generation/decorations/mm7_3d/dressing/`. The GLBs are in `assets_source/engine/models/`.

## Facing and yaw

- **Which way is front:** in `DecorationModelSet::placementFor`, the yaw is the map facing (degrees converted to radians) plus `yaw_offset` (radians). `gltfModelPlacement` turns glTF +Z into OpenYAMM +Y before applying that yaw.
- **Sprite view:** in `OutdoorInteractionController`, view a0 is drawn when the camera stands in the facing direction (cos θ, sin θ). So a model whose front matches a0 must point along the facing.
- **What that requires:** with no offset, a model's front must be glTF −X (Blender −X).
- **What these models have:** all four statues face Blender −Y (glTF +Z). The correct value is `yaw_offset: -1.5708` with `yaw: facing`, so I did not re-export anything.
- **Map placements:**
  - 7d34: 7dec54 at (416, 11360, 0); 7dec55 at (11136, 6400, −256), (8704, 13824, 0), (4892, 8968, −128), (−3408, 9816, −128), (1280, 3072, −128) and (−3784, 5280, −128). All seven have facing 0.
  - dec94 in 7out06 and dec95 in out14 also have facing 0.
  - With the offset, each model's front (a0) points to +X, which is where the original game shows a0.

## Models

| GLB | Serves | LOD triangles | Size | Binding |
|---|---|---|---|---|
| `mm7_deco_7dec55.glb` | 7dec55, dwarf with a club (6, indoor) | 3743 / 1811 / 525 / 269 | 3.74 MB | `indoor_decorations.yml` |
| `mm7_deco_7dec54.glb` | 7dec54, horned dwarf with a double axe (1, indoor) | 5672 / 2358 / 581 / 287 | 5.08 MB | `indoor_decorations.yml` |
| `mm7_deco_dec94.glb` | dec94, winged woman on a plinth (1, outdoor) | 5198 / 2490 / 540 / 248 | 3.70 MB | `decorations.yml` |
| `mm7_deco_dec95.glb` | dec95, knight with a sword on a plinth (1, outdoor) | 3470 / 1392 / 503 / 289 | 5.40 MB | `decorations.yml` |

Suggested bindings. Heights are the sprites' `art_height`; for 7dec54 the bounds top is the horn tips, and for dec94/dec95 the bounds include the plinth.

```yaml
  - name: 7dec55
    model: engine/models/mm7_deco_7dec55.glb
    height: 171
    yaw: facing
    yaw_offset: -1.5708
  - name: 7dec54
    model: engine/models/mm7_deco_7dec54.glb
    height: 169
    yaw: facing
    yaw_offset: -1.5708
  # outdoor (decorations.yml)
  - name: dec94
    model: engine/models/mm7_deco_dec94.glb
    height: 125
    yaw: facing
    yaw_offset: -1.5708
  - name: dec95
    model: engine/models/mm7_deco_dec95.glb
    height: 60
    yaw: facing
    yaw_offset: -1.5708
```

All four sprites are single-frame, so none needs `still`. Leave `mount`, `swing`, `z_offset` and `height_jitter` unset. dec94 and dec95 are not directional sprites, but `yaw: facing` keeps them deterministic and turns their sprite-like view toward the map facing.

Review sheets are in `review/<sprite>/compare.png` (sprite next to LOD0 front, three-quarter and side) and `lods.png`. The pose checks are in `review/<sprite>/pose/`.

## Method

- **Dwarves (7dec54, 7dec55)** (`scripts/statue_dwarf.py`):
  - **Base and reshaping:** the MM6 dwarf (`mm6_dwa1.glb`, read only) is reshaped in its rest pose: beard drawn down to the belt, arms, legs and torso thickened.
  - **Pose:** posed from all five sprite views and baked static.
  - **7dec55 extras:** a pointed cap and a knobbed cudgel; the helmet spike is removed.
  - **7dec54 extras:** gold helmet rim, spike and crescent horns, and a dark iron helmet dome. It also has gold rings fitted to the posed limbs and a procedural double axe with gold rings.
  - **The three fixes:**
    1. The gold mask is now hue 38–58°, saturation above 0.4, value above 0.45, grown by 2 texels. That is 35k texels instead of 457k, and the stone is no longer yellow.
    2. The blades use a light stone tile, so their tint no longer clips.
    3. The body target is 3950, which puts LOD0 at 5672.
- **Knight (dec95)** (`scripts/statue_knight.py`):
  - **Base and cleanup:** `mm6_kni.glb`, read only. The crest plume, helmet side rings and small ornaments are cut away, and the figure is widened 1.14× to match the stockier sprite.
  - **Pose:** the right hand rests on the pommel.
  - **Added geometry:** a procedural flat-topped great helm with a dark visor slit, a straight longsword point-down on the plinth, and a sloped granite plinth.
- **Winged woman (dec94)** (`scripts/statue_angel.py`):
  - **Base and rig fix:** an MPFB2 female (CC0), built headless with the Mixamo rig. That rig's arms rest in a T-pose while the base mesh is in an A-pose, so the arm bones' rest is first refitted to the mesh. The joints are placed at the boundaries between neighbouring bones' weights.
  - **Pose:** hands on hips, head turned up.
  - **Added geometry:** a hair cap and bun, procedural feathered wings (an arm plus covert, secondary and primary feathers), and a two-tier plinth.
- **Surface:**
  - **Bake:** `--stage bake` bakes occlusion, the upward-facing direction and a box-projected Poly Haven stone grain onto the model's own texture layout. The grain is `rock_01` for the dwarves and knight, `rock_surface` for dec94.
  - **Compose:** `scripts/statue_compose.py` maps a score through the sprite's own colour ramp, taken from the figure rows only. The score combines that bake with fine painted detail.
  - **COLOR_0 tint:**
    - Each part is tinted to the sprite's mean colour, measured over the texels that are visible; the boots are darkened.
    - The outdoor statues get a per-channel gain of (0.88, 0.85, 0.8), so their render under outdoor review light matches the sprite mean. dec95 renders at (121, 115, 103) against the sprite's (120, 113, 100), and dec94 at (94, 88, 78) against (95, 85, 73).
- **LOD2 and LOD3:**
  - The figure is remeshed: an octree pass closes the creature's open surfaces, then a voxel pass evens it out, then it is decimated.
  - Colour moves into COLOR_0 from the nearest LOD1 texel, on a neutral stone tile.
  - The plinths stay simple boxes. Thin parts (axe, sword, wings) come back as coarse builds.

## Compromises

- The outfits are the creatures' own, not the sprites': a tunic instead of the fur vest or chainmail skirt, and spiky pauldrons on the knight.
- 7dec55's back view (a4) is painted in colour in the original, which looks like an art error. The model is stone all round.
- dec94's hair is a simple cap and bun.
- Under review light the models read flatter than the sprites' painted key light.
- The far LODs are coarse and carry only vertex colour. dec95's LOD3 figure is a rough shape at about 220 triangles.
- dec95's LOD1 has some leftover small parts at the back of the helmet.
- File sizes are high at 3.7–5.4 MB, each with a unique base colour of 1024 or 1536 px plus shared tiles.

## Rebuild

From `dressing/`. The `--stage bake` step needs no GPU (Cycles on the CPU).

```sh
python3 scripts/statue_compose.py stone                 # shared tiles: stone, stonelight, granite
blender -b --python scripts/statue_dwarf.py -- 7dec55 --stage bake && python3 scripts/statue_compose.py 7dec55 && blender -b --python scripts/statue_dwarf.py -- 7dec55
blender -b --python scripts/statue_dwarf.py -- 7dec54 --stage bake && python3 scripts/statue_compose.py 7dec54 && blender -b --python scripts/statue_dwarf.py -- 7dec54
blender -b --python scripts/statue_knight.py -- --stage bake && python3 scripts/statue_compose.py dec95 && blender -b --python scripts/statue_knight.py
blender -b --python scripts/statue_angel.py -- --stage bake && python3 scripts/statue_compose.py dec94 && blender -b --python scripts/statue_angel.py
scripts/statue_review.sh <prop> <yaw> <elev> [--outdoor] -- <x2 sprites>    # 7dec5x: 0 6; dec95: 0 8 --outdoor; dec94: -60 10 --outdoor
python3 scripts/finish.py <prop> --install                                   # budgets in scripts/finish_statues.py
```

Pose checks: `--preview` on each script, then `scripts/statue_posecmp.py`.

## Sources and licences

- **Creatures, read only:** `mm6_dwa1.glb` and `mm6_kni.glb` are the project's own MM6 models. The MPFB2/MakeHuman base mesh and rig are CC0.
- **Textures:** Poly Haven `rock_01` and `rock_surface` (both CC0), stored in `textures/source/`. Gold is the New Sorpigal props texture, which is procedural.
- No paid generation was used.
