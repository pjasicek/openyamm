# Xeen engine props: haybale2, 7dec12, 7dec41 (2026-11-20)

Static 3D models for three MM7 engine decorations that the Xeen maps place and nothing modelled before. They are
engine content (`assets_source/engine/models/`), bound for every world in `assets_dev/engine/models/decorations.yml`
(section "MM7 engine decorations first modelled for Xeen"). No Xeen dungeon (BLV) places them, so there are
no indoor bindings. Built after `../mm7_3d/BRIEF.md` and the MM7 dressing batch (`../mm7_3d/dressing/`). No Meshy, no Codex.

| GLB | Decoration (Xeen placements) | LOD triangles | Source file | Binding |
|---|---|---|---|---|
| `mm7_deco_haybale2.glb` | `haybale2` "Hay" (X1 3, X2 2, X3 1, X4 3, X5 2, D1 2, D3 2) | 1756 / 708 / 244 / 96 | 4.0 MB | height 188, jitter 0.08 |
| `mm7_deco_7dec12.glb` | `7dec12` "wood" (X1 2, X2 1, X3 2) | 1946 / 694 / 164 | 4.4 MB | height 118, jitter 0.06 |
| `mm7_deco_7dec41.glb` | `7dec41` "bottle" (X1 1, X2 1, X5 1, D2 3, D3 1) | 508 / 240 / 68 | 0.4 MB | height 92, jitter 0.05 |

All `yaw: random`, static (the sprites have one frame). The cooked runtime copies are 0.04-0.11 MB.

**Heights** are the sprites' drawn art heights: opaque rows of the x2 frame / 2 x the DSFT scale. haybale2 376 / 2 = 188
(scale 1), 7dec12 238 / 2 = 119 (model 118), 7dec41 123 / 2 x 1.5 = 92: the bottle's sprite frame carries DSFT scale
1.5, as the MM7 goblet 7dec46 (bound 46 the same way), so the native game drew a bottle about 1.1 m tall. The table
radius/height (127, 52, 16) is collision only. For a smaller bottle, lower its `height` (61 is the unscaled art).

## Models

- **haybale2** (`scripts/build_hay.py`): the upper half of a cube-sphere (no poles or fans) mapped onto the profile
  measured on the sprite (steep, slightly bulging sides over the lower half, then a rounded dome; 232 x 212 base),
  lumped with noise. Material `Hay`: tileable procedural straw (`hay`, one repeat per 1.2 m, cylindrical on the sides,
  planar on the top, seam ring at 62 % of the profile). Fringe: alpha-tested double-sided straw tuft cards (`Strands`,
  `haystrand` atlas of four tufts, MASK 0.5) at the base skirt, sticking out of the dome and on top: 110 / 54 / 14 / 0
  cards per LOD. COLOR_0: occlusion x damp brown patches (the sprite's blotches) x grade (1.02, 0.87, 0.76); the cards
  take the nearest body colour, lighter at the tips.
- **7dec12** (`scripts/build_wood.py`): 21 swept, noise-gnarled tubes traced from the sprite: two crossed forked
  uprights (antler-like U fork on the left, a split tip with a twiggy side branch on the right), a curling limb, a
  knotted log to the left, a root head with finger twigs to the right, logs fanning out in a star at the base so the
  pile reads from every side. Sides 7 / 5 / 4; twigs and forks are dropped at LOD1/LOD2. Material `Wood`: Poly Haven
  `rough_wood` pushed to silver-grey with a pink-brown cast in the dark grain (`driftwood`); whole repeats around each
  branch (seamless), one density along it. Logs sink 1.5 units so their undersides end flat on the ground. Grade
  (0.38, 0.29, 0.21) x occlusion.
- **7dec41** (`scripts/build_bottle.py`): three lathes meeting at hard steps (glass body with the shoulder and neck,
  lip ring, cork), 16 / 10 / 6 sides; sharp ring edges where the profile turns over 40 degrees. Glass as the shared MM7
  goblet (`../mm8_3d/props/build_goblet.py`): opaque, glossy (roughness 0.18, `openyamm_specular` 0.5), no blending.
  One material on the `bottle` unwrap (u around, v = height / 123): olive glass with fine sparkle, the yellow label on
  the front quarter (Blender -y), the pale lip, the cork.

Review sheets (native x2 sprite, LOD0 front / three-quarter / side, all LODs; outdoor review light):
`review/<prop>/compare.png` and `lods.png`. In-game captures (X1, isolated runs of `build-xeen`): `review/ingame/`
(`tour_x1.yml`, `tour_x1_b.yml`).

## Sources and licences

- Poly Haven `rough_wood` (CC0), read from `../mm6_new_sorpigal_3d/trees/source/rough_wood/` (2k diffuse, OpenGL
  normal, roughness).
- Everything else is our own: procedural textures (`scripts/make_textures.py`) and geometry.
- Scripts adapted from the MM7 dressing batch (read only, copied): `finish.py`, `review.py`, `sheet.py`, and
  `fix_winding`/`save`/`fbm` in `scripts/xlib.py`; the swept tube follows `../mm6_dungeons_3d/hanging/scripts/
  hanging_lib.py`. `xlib.py` imports `../mm6_new_sorpigal_3d/props/scripts/props_lib.py` (read only).

## Rebuild

From this folder, with the Xeen lane's Blender wrapper first on `PATH`:

```
python3 scripts/make_textures.py
blender --background --python scripts/build_hay.py -- 1.02 0.87 0.76
blender --background --python scripts/build_wood.py -- 0.38 0.29 0.21
blender --background --python scripts/build_bottle.py -- 0.93 0.92 0.9
blender --background work/<prop>.blend --python scripts/review.py -- <prop> 0 <elevation> --outdoor   # 8, 6, 6
python3 scripts/sheet.py <prop> <x2 sprite> --tile WxH   # haybale2_p547.png 400x360, 7dec12_p2.png 400x380, 7dec41_p3.png 240x420
python3 scripts/finish.py <prop> --install               # validation, check_winding.py, tools/install_model.py --engine
```

## Compromises

- Outdoor lighting bakes of the Xeen maps that place these decorations (X1-X5, D1-D3) may now be stale; check with
  `tools/lighting/stale_bakes.py`. Not re-baked here.
- haybale2: the open dome has no bottom (it rests on the ground; never seen). The straw is a tiling texture plus
  cards, coarser than the sprite's individually drawn stalks; the fringe thins out at LOD2 and is gone at LOD3. Width
  with the skirt cards is about 260 (sprite 220) at the bound height.
- 7dec12: log and branch ends are flat caps, not splintered; the knobbly masses of the sprite's limbs are only
  suggested by the noise.
- 7dec41: the glass is opaque (like the goblet) and less sparkly than the sprite; with random yaw the label faces
  anywhere.
