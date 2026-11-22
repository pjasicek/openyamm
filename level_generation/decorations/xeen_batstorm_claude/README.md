# Xeen bat storm (D-36), 2026-11-20

Lane S (session 5). A storm of bats circling over Castle Blackfang (D4; A6 places two copies). One skinned
decoration model with one seamless loop (`devdocs/ANIMATED_DECORATIONS.md`, the `animated:` kind), made from the
installed Xeen bat `xeen_bat.glb` (the MM6 bat with Xeen tiers). No Meshy.

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_deco_batstorm.glb` | the skinned storm, clip `storm` (12 s loop); = `export/xeen_deco_batstorm.glb` |
| `assets_source/worlds/xeen/models/xeen_deco_batstorm_static.glb` | its rigid rest copy: the binding's static `model` (picking only; decoration models must be rigid) |
| `assets_dev/worlds/xeen/models/decorations.yml` | binding `xeen_batstorm`: `model` the static copy, `animated` the storm, `idle: storm`, `height: 666.4`, `yaw: facing` |
| `assets_dev/worlds/xeen/models/decoration_data.txt` | row 4003 `xeen_batstorm` (radius 0, no light, sprite 27003) |
| `assets_dev/worlds/xeen/rendering/sprite_frame_data_world_decorations.yml` | sprite 27003 (`pending`, never drawn) |
| `scripts/bake_colour.py` | the bat's base colour through the `xbat_a` ramps (Giant Bat, charcoal grey) into one 512 texture, plus its normal map |
| `scripts/build_storm.py` | Blender: reduce, place, animate, export both GLBs |
| `review/ingame/` | `sheet.jpg` (debug `model spawn` on D2, four moments), `placed/sheet.jpg` (placed as a decoration on D2 from a scratch root) |

## Model

- One bat: the installed bat's LOD0 (3,537 triangles) collapse-decimated to **249**, ears and legs folded onto the head
  and spine (20 joints per bat). One blended material (alpha 0.98, double-sided, roughness 0.8): neither the runtime
  shadows nor the outdoor bake cast blended faces, so the storm casts no shadow.
- **24 bats, 5,976 triangles, 480 joints**, three rings around the origin (asset metres x 100 = world units):

| Ring | Bats | Radius | Height | Turns per loop | Wing beats per loop | Bobs | Bank |
|---|---|---|---|---|---|---|---|
| inner | 7 | 7 m (± 0.6) | 0 (± 0.5) | 2 (counter-clockwise) | 17 | 3 | 24° |
| middle | 8 | 10 m | 2.6 m | -1 (clockwise) | 16 | 2 | 18° |
| outer | 9 | 13 m | 5 m | 1 | 15 | 2 | 14° |

  Uneven spacing, per-bat radius, height, bob amplitude (0.25-0.55 m) and wing phase jitter (seed 36). Every bat
  beats with the bat's own `Fly` clip time-warped to its ring's beat count, heads along its path and banks inward.
  Whole turns, beats and bobs per loop make the last frame meet the first.
- Clip `storm`: 12 s, 30 fps, 361 frames. Rest bounds x/z ±13.1 m, y -0.70 to 5.96 m (height 666.4 world units, so
  the binding scales 1 m to 100 units; one bat spans 155 units, as the Giant Bat actor).
- Sizes: storm GLB 4.5 MB (the clip), static 1.1 MB; 512 colour and normal maps.

## Placement (for A6)

Name `xeen_batstorm` (row 4003; a scene entity's `decoration_list_id` is 4002). Origin = the storm's centre at the
lowest ring: place it about 300-500 above the keep's top; the bats fly from -70 to +600 around it and about 2,650
across. No collision (radius 0). Facing turns the storm (it is round). Two copies: offset them by at least ~1,500 or
at different heights so the rings do not merge.

## Checks

- Winding 0 inverted (both GLBs); installed `tools/install_model.py --world xeen`.
- In game (build-xeen, D2): `model spawn` + `model play 0 storm`, then placed as a decoration in a hard-link scratch root
  (`work/root`, deleted after): the idle loop plays, charcoal bats flap out of step and circle in three rings.

## Rebuild

```sh
cd level_generation/decorations/xeen_batstorm_claude
python3 scripts/bake_colour.py ../../../assets_source/worlds/xeen/models/xeen_bat.glb work/tex
../../creatures/xeen_tiers_claude/bin/blender --background --factory-startup --python scripts/build_storm.py -- \
  ../../../assets_source/worlds/xeen/models/xeen_bat.glb work/tex export/xeen_deco_batstorm.glb
# then check_winding.py and tools/install_model.py --world xeen on both export GLBs
```

Notes: Blender's glTF import drops the bat's LOD meshes (they hang off extras), so the reduction starts from LOD0. The
bat's region mask has alpha 0: resize its channels one by one (an RGBA resize premultiplies them to black).
