# MM6 dungeon hanging decorations in 3D (2026-10-09)

Static glTF replacements for the MM6 dungeon cages and the chandelier, built after the common brief (`../BRIEF.md`)
and the pilot (`../scripts/`). Everything is procedural Blender modelling traced from the restored native sprites
(`assets_dev/engine/decorations_x2/`); proportions are in native world units (`units()`, 81.7 per metre). No paid
generation, no external assets. Rebuild with `./build.sh` (about 70 s); `./build.sh --install` also installs, and
`finish.py` refuses to overwrite an installed model.

| Model (`assets_dev/worlds/mm6/models/`) | Sprite (placements) | LOD triangles | File | Bounds height |
|---|---|---|---|---|
| `mm6_deco_hngncge2.glb` | `hngncge2` (8) | 3494 / 1766 / 420 / 174 | 1.76 MB | 321 (cage 249 + chain 72) |
| `mm6_deco_empty.glb` | `empty` (4) | 2616 / 1784 / 300 / 114 | 0.92 MB | 321 (cage 249 + chain 72) |
| `mm6_deco_bonecage.glb` | `bonecage` (19) | 2542 / 1398 / 376 / 168 | 1.73 MB | 247 (standing, no chain) |
| `mm6_deco_chndlir0.glb` | `chndlir0` (3) | 2560 / 1670 / 321 | 1.17 MB | 159 (wheel underside to chain top) |
| `mm6_deco_hngncge2_long.glb` | `hngncge2`, 6d20 (1) | 5958 / 2942 / 420 / 174 | 1.90 MB | 1159 (chain 910) |
| `mm6_deco_empty_long.glb` | `empty`, 6t8 (1) | 3832 / 2336 / 300 / 114 | 0.99 MB | 704 (chain 455) |

Review sheets: `review/<model>/compare.png` (native sprite, LOD0 front, three-quarter, side) and `lods.png`.

## Placements (measured in the BLV files)

- `hngncge2` and `empty` stand on the floor in every map except one (z = floor): 6d17 and cd3 under ceilings
  256 above the floor, 6d14 277, zddb10 320. The cage (249) fills the room height, so the standard models carry a
  72-unit chain up to 321 (the pivot): the chain reaches every one of these ceilings and the part above a ceiling is
  hidden (no room lies above any of these placements). 6d20's `hngncge2` stands beside a bone cage under a 1152
  ceiling, and 6t8's `empty` hangs 192 above a pit floor with the ceiling 640 above its base (391 above its top):
  the `_long` variants reach into those ceilings (per-map bindings), by 7 and 64 units.
- `bonecage`: all 19 stand on the floor (ceilings 256 to 1410 above): a standing, lidded cage, static (1 frame).
- `chndlir0` (6d19): placed 320 to 350 above the floor, its 181-unit sprite top reaching or entering the ceiling
  (ceilings 128, 162 and 192 above the placement).

## Models

- **Cages** (`build_cage.py`): bands are flat rings (rectangular section), hoops thinner rings, bars four-sided
  flat strips whose ends hide in the bands, a floor slab; positions and counts measured on the x2 sprites (row
  coverage and bar runs): `hngncge2` 12 bars (the sprite's front and back bars coincide), four riveted hoops;
  `empty` 16 bars, six hoops, inner lips under/over the bands; `bonecage` 20 thin bars, riveted bands with front
  strap plates, four riveted hoops, a lid. Hanging cages: two crossed straps over the top meet at the chain, whose top
  link's upper end is the bounds top.
- **Skeletons**: posed from joint positions read off the sprites (limb bones with knobbed ends, a swept spine, six
  rib pairs and a sternum, a squashed-bowl pelvis, the skull pile's procedural skull on the `skull` texture).
  `hngncge2`'s prisoner hangs by its wrists in iron cuffs on short chains from the top band, head drooping, knees bent;
  the bone cage's sits huddled on the floor, knees drawn up, one arm over its skull, as the sprite shows it.
- **Chandelier** (`build_chandelier.py`): a flat iron wheel (radius 121, 13 high) braced by two crossed squares of
  bars, four arms curving from a hub, a 13-link chain, twelve candles of uneven height in dishes. The model's base is
  the wheel's underside (the sprite's wheel centres about 27 above its bottom), so it binds with `z_offset: 22`.
- **Flames**: the candles carry the shared CC0 flipbook `../textures/flame03_basecolor.png` (16 x 4 frames,
  `openyamm_flipbook [16, 4, 30]`, a 2.1 s loop) on two crossed cards each (one at LOD2), BLEND, double-sided,
  unlit. Card recipe from `../textures/FLAMES.md`: a native candle flame of 3.5 x 7 units gives a 5.8 x 8.2 card
  showing the frame's lower 80 % (v 0 to 0.8), its bottom 0.2 below the candle top. The restored native frames
  (the chandelier's flames are a few pixels; `cndlab0..3`) are not used: the upscales are too poor for fire.
- **LODs**: fewer segments, coarser links (LOD2: the chain is one strap), every second (third at LOD3) bar on the
  dense cages, two hoops at LOD2 and none at LOD3, simpler skeletons (LOD3: skull, trunk and four straight limbs).

## Colour

COLOR_0 = vertex occlusion x a tint per part group (`hanging_lib.tint`): linear(native mean) / linear(texture mean)
/ the group's mean occlusion, targets from `scripts/measure.py` (sRGB):

| Model | Bars, hoops, chain | Bands, floor, lid | Bones | Other |
|---|---|---|---|---|
| hngncge2 | (33, 27, 24) | (52, 45, 41) | (127, 97, 74) | |
| empty | (25, 23, 20) | (51, 47, 41) | | |
| bonecage | (19, 18, 20) | (23, 22, 25) | (94, 91, 88) | |
| chndlir0 | iron (28, 18, 14) | | | wax (251, 238, 187) |

The bone means include the bones' shaded pixels (warm or bright pixels above 40), not only the highlights.
`textures/bonelight` and `skulllight` are the props `bone`/`skull` textures brightened (linear x4, soft shoulder)
so the tints stay below one; `wax` is a generated cream white. The wax keeps a quarter of its occlusion; even so
its red channel clips slightly at one (COLOR_0 is stored normalised). The review renders (white sky, no specular,
weak sun) give whole-sprite means within a few levels of the native ones.

## Animation and suggested bindings

- Native: the cage sprites are static; MM7's swinging cages 7dec05/06 loop 12 frames a..g..b in 24/16 s = 1.5 s.
  Measured on their x2 frames, the silhouettes barely move: the cage bottom shifts about 2.5 x2 pixels (1.25 units)
  peak to peak under a 222-unit sprite, about 0.2 degrees, with the shading changing more (motion toward the
  camera the sprite cannot show). 1 degree at 1.5 s keeps MM7's timing and stays a creak (the standard cage's
  bottom moves about 5.6 units).
- `chndlir0`'s six frames have identical silhouettes and chain; they differ only in candle flames and shading
  shimmer, with zero frame lengths (the original engine shows frame 0). The flame flipbook carries the flicker; a
  slow, slight sway at the pendulum period of its chain is offered on top.

```yaml
- name: hngncge2
  model: mm6_deco_hngncge2.glb
  height: 321          # cage 249 (logical 249 x scale 1.0) + chain
  z_offset: 1          # clears the floor while it swings
  swing: [1.0, 1.5]
  maps: [6d14.blv, 6d17.blv, zddb10.blv]    # only with the per-map 6d20 binding below
- name: hngncge2
  model: mm6_deco_hngncge2_long.glb
  height: 1159         # chain to 6d20's ceiling
  swing: [0.4, 7.5]    # a 14 m pendulum: slow and small
  maps: [6d20.blv]
- name: empty
  model: mm6_deco_empty.glb
  height: 321
  z_offset: 1
  swing: [1.0, 1.5]
  maps: [cd3.blv]
- name: empty
  model: mm6_deco_empty_long.glb
  height: 704          # chain to 6t8's ceiling
  swing: [0.5, 5.5]    # an 8.6 m pendulum
  maps: [6t8.blv]
- name: bonecage
  model: mm6_deco_bonecage.glb
  height: 250          # logical 250 x 1.0; static, stands on the floor
- name: chndlir0
  model: mm6_deco_chndlir0.glb
  height: 159          # wheel underside to chain top; the sprite's top (181) stays at 181
  z_offset: 22
  swing: [0.75, 3.0]
```

Without the per-map bindings, single bindings of `hngncge2` and `empty` (no `maps`) work everywhere; 6d20's cage
then shows a 72-unit chain ending in mid-air above it, and 6t8's a 319-unit gap to the ceiling.

## Revision 2 (2026-10-09): Meshy skeletons

The user found the procedural skeletons not authentic. `hngncge2`, `hngncge2_long` and `bonecage` now carry the bones
batch's Meshy skeleton with its Meshy skull (`../bones/README.md`), posed by `../bones/scripts/pose_skeleton.py`
(hanging / sitting) and loaded by `build_cage.py`; the shackles follow its posed wrists. Triangles: hngncge2
4875 / 2495 / 656 / 262 (3.2 MB), hngncge2_long 7339 / 3671 / 656 / 262 (3.4 MB), bonecage 4206 / 2127 / 612 / 256
(3.2 MB); budgets raised in `finish.py`. The bone cage's bone target is (82, 79, 76), below the measured mean,
because the smooth Meshy bones read white at that mean. `finish.py --install --reinstall` replaces this batch's own
models with new files (hard links elsewhere keep the old bytes). The table above lists the first version.

## Compromises

- The native cages have no chain; the chain and straps are added so the cages can hang and swing from a pivot.
- The flames are crossed cards, not camera-facing: the engine's billboard turns a card about the model's own axis
  and keeps only its offset across the model, which would collapse twelve flames on a wheel into one plane. Seen
  edge-on from directly below, a crossed card thins out.
- Rivets are small pyramids; at the dungeon's light and without highlights they read less than the sprite's bright
  rivet heads. The iron texture is the props `iron` (warmer, less speckled than the sprite's metal), tinted.
- Chains pass through the ceiling plane to their pivot (nothing lies above any of these placements): the standard
  cages' by 1 to 65 units, 6d20's long one by 7, 6t8's by 64, so at the ceiling a chain shifts by about 1 unit at
  most while swinging.

Sources and licences: all geometry and the wax texture are procedural (this folder); `iron`, `bone`, `skull` come from
the New Sorpigal props textures (procedural/CC0, `../../mm6_new_sorpigal_3d/props/`); the flame flipbook is the
project's shared CC0 `flame03` (Unity Labs VFX source, licence in `../source/unity_labs_vfx/`).
