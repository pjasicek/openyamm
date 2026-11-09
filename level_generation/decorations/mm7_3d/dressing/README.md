# MM7 dressing batch (2026-10-15/16)

Static 3D replacements for the MM7 dungeon dressing sprites, built after `../BRIEF.md` and the MM6 dungeon batches.
Every model is installed as `assets_source/engine/models/mm7_deco_<sprite>.glb` with `scripts/finish.py <prop>
--install` (which validates it and runs `tools/install_model.py --engine`). `work/installed.json` lists them.

- **This file:** barrel 7dec32, cask 7dec21, skeleton dec19, skull 7dec20, skull on a bone pile 7dec18 and the
  hanging cages 7dec05/06/07.
- **Helper reports:**
  - `REPORT_heaps_small_props.md`: 7dec10, 7dec11, 7dec16, 7dec46, dec96, dec97.
  - `REPORT_statues.md`: 7dec54, 7dec55, dec94, dec95.

## Shared scripts

| Script | Role |
|---|---|
| `scripts/dlib.py` | Paths. Imports the MM6 hanging batch's `hanging_lib` (read only) and the New Sorpigal `props_lib` as `pl`. `material()` looks in `textures/` here first. `save()` writes `work/<prop>.blend` and `_export.glb`. |
| `scripts/finish.py` | Material modes, LOD linking (`tools/link_static_model_lods.py`), validation and install. Its tables are `scripts/finish_<group>.py` (`barrels`, `cages`, `misc`, `statues`). |
| `scripts/review.py` | Renders LOD0 front, three-quarter and side, and every LOD. Default lighting is the dungeon light (white sky, weak sun, base colour × COLOR_0). `--outdoor` uses sky and sun; `--wide` makes landscape frames. |
| `scripts/sheet.py` | Builds `review/<prop>/compare.png` (native x2 sprite beside the renders, mean colours printed) and `lods.png`. `--tile WxH` sets the tile size. |
| `scripts/contact.py`, `peek_*.py` | Sprite contact sheets and quick looks at blends and GLBs. |

## Models

| GLB | Sprite (placements) | LOD triangles | File | Binding height |
|---|---|---|---|---|
| `mm7_deco_7dec32.glb` | 7dec32, barrel with a fishing net (208, dungeons) | 1498 / 760 / 220 / 168 | 2.9 MB | 121 |
| `mm7_deco_7dec21.glb` | 7dec21, cask on its side with a tap (1, 7d29) | 1008 / 620 / 130 / 42 | 2.1 MB | 91 |
| `mm7_deco_dec19.glb` | dec19, skeleton lying on its back (33 outdoor in out09, 3 in dungeons) | 3800 / 1590 / 586 / 226 | 3.9 MB | 31 |
| `mm7_deco_7dec20.glb` | 7dec20, large skull (1, 7d28) | 5329 / 2183 / 799 / 256 | 6.0 MB | 71 |
| `mm7_deco_7dec18.glb` | 7dec18, skull on a pile of bones (13, dungeons) | 3879 / 1816 / 662 / 232 | 5.5 MB | 58 |
| `mm7_deco_7dec05.glb` | 7dec05, empty hanging cage (4, 7d27) | 2096 / 1436 / 340 / 236 | 1.4 MB | 205 |
| `mm7_deco_7dec06.glb` | 7dec06, cage with a huddled skeleton (5, 7d27) | 4036 / 2547 / 654 / 383 | 3.7 MB | 205 |
| `mm7_deco_7dec07.glb` | 7dec07, cage with a living prisoner (1, 7d27) | 5249 / 2745 / 927 / 548 | 3.3 MB | 205 |

All the sprites in this table are static, except the cages, which get a binding `swing`.

### Barrel 7dec32 and cask 7dec21

The orchestrator's brief describes 7dec32 as a barrel in cobwebs. The sprite actually shows a fishing net draped
over the barrel's front right, a rope wound round its left side, and two ropes hanging to four iron net weights.

**Barrel geometry** (`build_barrel.py`, numbers in `barrel_spec.json`):
- Measured on the x2 sprite, seen from about 13° above: 121 units tall, radius 36.6 at the bulge and 28 / 29.5 at
  the ends.
- Four iron hoops, 1.4 units proud, with brass rivets on the top and bottom hoops. The lid is recessed 2.6 units
  inside a chime.
- Every LOD is a lathe with hoop steps (texture-only hoops at LOD2/3). All LODs share one UV layout: a side strip,
  the lid disc, an iron swatch and a painted washer face.

**Barrel parts:**
- **Net:** a MASK, double-sided card that follows the wall over the hoops. Its edges are traced from the sprite. Its
  texture is a procedural knotted diamond net (`net_*`).
- **Ropes:** swept tubes on the MM6 leftovers' laid-rope texture, recoloured to the sprite's pale rope.
- **Net weights:** four short iron cylinders. They are LOD0/LOD1 only, as are the ropes.

**Cask** (`build_cask.py`): the same builders with spec `7dec21`.
- 104 long, 75 across the heads and 90 at the bulge.
- 16 wide staves. Riveted iron hoops: two at the head, one a third of the way along, one at the far end.
- A tap with a spout and a T handle. Both heads are closed.
- Laid on its side with the head turned 44° right of the view, as the sprite shows it.

**Textures** (`barrel_textures.py`, 1024 atlas):
- **Staves:** narrow slices of plank interiors from Poly Haven `weathered_planks`, one slice per stave, with dark
  seams and bevels.
- **Hoops:** Poly Haven `rust_coarse_01`.
- **Lid:** Poly Haven `wood_planks`.
- **Grading:** each region's luminance is rank-matched to the sprite's pixels of that region and coloured by their
  luminance-to-colour ramp. The region mean is then set to the sprite mean divided by the expected occlusion (0.70;
  the cask also gets a 0.8 gain).
- **COLOR_0:** vertex occlusion only.
- **Specular:** `openyamm_specular` 0.6 with `openyamm_specular_mask`. The red channel holds 0.35 for wood and 0.9
  for iron.

### Skeleton dec19

**Source:** the MM6 bones batch's Meshy skeleton with its grafted Meshy skull (read only).

**Posing** (`skel_pose.py -- lying`, a copy of that batch's `pose_skeleton.py`):
- Lying on its back, head at +x, seen from its left side.
- Its left arm lies along the side with the hand on the ground; its right hand rests on the pelvis. Legs straight,
  toes up, skull turned toward the viewer.
- Additions in the copy, because the sprite paints a chunkier skeleton:
  - `thicken` 1.4: every piece is scaled across its bone axis.
  - `chest_scale` (1.3, 1.5): the ribcage, about the spine.
  - `skull_scale` 1.4.
  - `skull_tris`.
- LODs come from per-piece decimation, so no bone collapses into a shard.

**Build** (`build_skeleton.py`):
- Grounds the LODs.
- COLOR_0 is vertex occlusion with the floor, times a darker, redder tint on the ribcage.

**Textures** (`bones_textures.py`: `dec19_bone`, `dec19_skull`):
- The Meshy base colour's detail is rank-matched to the sprite's pale bone pixels, at 0.6–0.7 contrast.
- Value-noise blotches carry the sprite's dried flesh and rust (40 % / 38 % coverage).
- It is graded for the outdoor review light (warm 1.0 / 0.93 / 0.8). The sprite is mostly outdoor.

**Measured:** the outdoor front mean is (85, 71, 63) against the sprite's (88, 68, 57).

### Skulls 7dec20 and 7dec18 (`build_bones.py`)

**7dec20:**
- The Meshy skull (cranium with its fused jaw, plus 21 separate teeth), widened 1.16 and shortened 0.94 toward the
  sprite's broader skull.
- Texture `big_skull` (2048): sparse fine brown spots (12 %).
- Occlusion strength 0.75 for dark sockets.
- The front mean is (104, 94, 75) against the sprite's (94, 85, 68).

**7dec18:** a dense, low heap of whole Meshy skeleton bones on a buried core mound, with the Meshy skull (2.8 ×,
cut at the bite) sitting in it and its jaw at the right front. See Revision 1 below for the current method.

### Hanging cages 7dec05, 7dec06, 7dec07 (`cage_*.py`, table `finish_cages.py`)

**Cage geometry:**
- Procedural iron cages adapted from the MM6 hanging batch's `build_cage.py`, measured on the x2 frames
  (`cage_measure.py`).
- 158 tall. Lid radius 47 (144–158, chamfered). Bottom band radius 46.5, 19 tall, round a floor slab that is
  closed underneath.
- 16 flat bars, 4.5 × 2.5, at radius 44. Six hoops. Three chain links up to the pivot at 205.

**Placements** (`cage_placements.py`, vertical rays against the 7d27 BLV): every cage entity is 378 above the floor
and 180 below the ceiling. The models keep the sprite's cage size and its 45-unit chain, and end 2 units inside the
ceiling: height 205, `z_offset: -23`, swing pivot at the bounds top.

**Animation:**
- The frames shift the silhouette by about 2 x2 pixels (12 frames ping-ponging over 1.5 s; 7dec07: 7 frames over
  0.875 s), so they are a creak.
- All three use `swing: [1.0, 1.5]`, as the MM6 cages do. The figures are static.

**Figures:**
- **7dec06:** the Meshy skeleton in the MM6 bone cage's sitting pose, scaled 0.66 and turned 45° toward the viewer
  (`cage_pose_skeleton.py -- cage_huddle`).
- **7dec07:** the project's MM6 `natm` creature (read only), posed with the leftovers batch's `corpse_pose.py`
  operations (`cage_prisoner.py`): legs apart, both arms up gripping bars. Its feathers are removed. It is widened
  1.25 × toward the painted bulk and tinted warm orange.

**Colour:** COLOR_0 is vertex occlusion × a tint per part group, toward the first frame's means (`hanging_lib`
`tag`/`tint`). Lit sheet means against the native ones:
- 7dec05: (18, 12, 9) against (19, 11, 8).
- 7dec06: (26, 17, 13) against (26, 16, 11).
- 7dec07: (34, 19, 14) against (33, 18, 13).

## Revision 1 (2026-10-16, orchestrator review of the sheets)

**7dec32 net.** The net was a bright, regular lattice that read as wire. It is now darker, thinner and looser.
- **Cord colour:** the sprite's shaded beige-grey (140, 126, 106), no longer lifted for occlusion. The ropes get
  the same treatment, at (150, 134, 108).
- **Mesh:** 8 cells per repeat at 46 units, drawn out 1.25 × vertically. A periodic domain warp makes the cells
  uneven, the knots vary in size and a few cords are broken.
- **Card:** 14 × 6 cells with ragged edges and jittered columns. It stands off the staves in vertical folds and
  sags toward its tail. LOD0 rises from 1388 to 1446 triangles.

**Stains on dec19, 7dec20 and 7dec18.** The stains were large, hard blotches. They are now small, soft spots of
fine value noise, at most 70 % strength.
- `bake_weights.py` rasterises per-vertex cavity (1 − self-occlusion) and the skull's crown height into texture
  space (`work/weight_<source>.npy`).
- `bones_textures.py` gathers the spots where that weight is high: in sockets, sutures and between bones, and on
  the crown, as the sprites show.

**7dec18 pile, rebuilt.** It read as a sparse spray of shards; it is now a dense, low heap of whole bones.
- **Bones:** 34 pieces of the Meshy skeleton: three femurs, three tibias, two fibulae, four humeri, five forearm
  bones, seven vertebrae, and hand and foot bones. The Meshy ribs read as strips at these counts, so the heap has
  none.
- **Long bones:** they lie within 35° of the sprite's horizontal.
- **Packing:** each piece takes the lowest of 12 spots in an 80 × 34 elliptical footprint. It rests on a buried
  core mound (a dome 64 × 24 × 11), which closes the gaps and is shaded to 0.4 so that only dark crevices show.
- **Skull:** sits 9 units into the heap; the jaw lies at the right front.
- **Decimation:** the bones (2700 at LOD0, at least 24 triangles per bone) and the skull (1100) are decimated
  separately, so no bone collapses to a shard.
- **Grime:** occlusion strength 0.75 plus the cavity-weighted stains.
- **Bounds:** about 115 × 68 × 60; it binds at 58 as before.

**Face orientation (2026-10-16).** `dlib.save()` now turns every closed loose part outward (positive signed
volume) before export. The engine culls the back faces of single-sided materials, and the cage lid disc,
7dec06's and dec19's small far bones and a prisoner shard were inside-out. `finish.py` now refuses a model unless
`../../mm8_3d/animated/scripts/check_winding.py` reports `inverted closed parts: 0`. 7dec05, 7dec06, 7dec07 and
dec19 were rebuilt and reinstalled. All eight models in this file now report 0.

## Stat barrel liquids (2026-10-16)

7dec32 is MM7's stat barrel: state 1-7 is the contents and 0 is empty once drunk. It now matches the MM6 open
barrel.

**Open top** (`barrel_spec.json` `open`; `build_barrel.py` `open_top`), on every LOD:
- A rim ring 1.4 units thick.
- An inner stave wall following the bulge (`inner_radius`), with a ring at the liquid surface. Its texture is a
  hoop-free band of the side strip.
- A floor at z 8 on the lid planks. The lid region's specular mask is 0.1, so the floor does not reflect the sky.
- COLOR_0 inside shades by depth from 0.62 at the rim to 0.18 at the floor, as the MM6 barrel.

**Outer shape:** the outer size is unchanged, so the binding (height 121) still fits. LOD2 and LOD3 gained a
profile ring at the surface, and LOD3 now has 10 sides. LOD0 drops a net row and two sides per weight to stay at
1498 triangles.

**Liquids** (`barrel_liquids.py`, a copy of the MM6 `build_liquids.py`):
- Seven discs, `mm7_deco_7dec32_liquid_<red|yellow|blue|orange|green|purple|white>.glb`, in the barrel's asset
  space, each 288 triangles.
- Palette, foam, ripple `openyamm_uv_scroll`, COLOR_0 shadow and 50 % alpha are unchanged.
- The surface is at z 112.5 map units (1.37699 m in the glTF), 8.5 below the 121-unit rim.
- The radius is 29.70 units (0.36351 m): the inner wall's 24-sided flats at that height. On LOD1–LOD3 (16 and 10
  sides) the disc edge stays inside the 1.4-unit staves; the 10-sided levels' outer flats are at 29.82.

**Review:** `barrel_liquid_review.py` and `barrel_liquid_sheet.py` produce `review/7dec32_liquids/sheet.png`.

## Rebuild

```sh
cd level_generation/decorations/mm7_3d/dressing
python3 scripts/barrel_textures.py all
blender -b --python scripts/build_barrel.py   # then review.py -- 7dec32 0 12; sheet.py 7dec32 7dec32_p2.png
python3 scripts/barrel_liquids.py              # work/liquids/; install each with tools/install_model.py --engine
blender -b --python scripts/barrel_liquid_review.py && python3 scripts/barrel_liquid_sheet.py
blender -b --python scripts/build_cask.py     # review.py -- 7dec21 0 18
blender -b --python scripts/bake_weights.py -- skull skeleton
python3 scripts/bones_textures.py
blender -b --python scripts/skel_pose.py -- lying
blender -b --python scripts/build_skeleton.py # review.py -- dec19 0 10 --outdoor --wide; sheet.py ... --tile 450x200
blender -b --python scripts/build_bones.py -- 7dec20
blender -b --python scripts/build_bones.py -- 7dec18   # review.py -- 7dec18 0 14 --wide; sheet.py ... --tile 450x260
python3 scripts/cage_textures.py
blender -b --python scripts/cage_pose_skeleton.py -- cage_huddle
blender -b --python scripts/cage_prisoner.py
for p in 7dec05 7dec06 7dec07; do blender -b --python scripts/cage_build.py -- $p; done
python3 scripts/finish.py <prop> --install
```

## Sources and licences

**Poly Haven (CC0, https://polyhaven.com/license), read from other projects' local copies:**
- `weathered_planks`: `../../mm8_3d/props/source/`.
- `wood_planks`: `../fire/source/polyhaven/`.
- `rust_coarse_01`: `../../mm6_dungeons_3d/torch_textures/source/`.
- `rusty_metal_04`: `../../mm6_dungeons_3d/fire/source/polyhaven/`.

**Our own work:**
- The net texture and all geometry except the bones and figures.
- The rope texture, which is the MM6 leftovers' procedural rope, recoloured.

**Bones:** the Meshy skeleton and skull are the project's paid Meshy generations from the MM6 bones batch (output
owned by the account). No new Meshy jobs were made.

**7dec07's prisoner:** the project's MM6 `natm` creature.

## Compromises

**7dec32:**
- The net is a regular diamond card, cleaner than the sprite's loose, knotted mesh. Ropes and weights stop at
  LOD1.
- Bound at 121, the model is the barrel's true height: the sprite's 128 includes its lid seen from above.

**7dec21:** the hoop rivets are painted, not modelled.

**dec19:**
- The bones are thickened rigidly, and some far pieces facet.
- LOD3 (226) breaks into shards, as the MM8 skeleton's far levels do.
- The ribs' dried flesh is a COLOR_0 tint plus texture blotches, not geometry.
- The same model serves the 3 dungeon placements, graded for outdoor light.

**7dec20:**
- The jaw is fused and closed; the sprite's is slightly open.
- The skull's 2048 texture makes a 6.3 MB file.

**7dec18:**
- The pile is about 14 % wider than the sprite at height 58.
- No pelvis: it stood too tall.
- The jaw is the Meshy skull's front half cut off at the bite.
- No ribs: the Meshy ribs read as strips.

**Cages:**
- The cage hangs 38 units lower than the sprite's art, so its lid clears the 7d27 ceiling.
- The prisoner is bald, where the sprite's has dark hair, and keeps a few mantle cords.
- 7dec07's LOD2 and LOD3 stay above 300 triangles, because decimation stalls on the posed body.
- The huddled skeleton's pose is an interpretation: the sprite's pose cannot be read at its resolution.
