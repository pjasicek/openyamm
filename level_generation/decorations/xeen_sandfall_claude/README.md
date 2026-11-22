# Xeen sand-fall (X6 west rim, D-31), lane S

Decision D-31 (`devdocs/xeen/DECISIONS.md`): one static, translucent, scrolling decoration model of dune sand pouring
over the world rim into the stars; A5 places 3-5 along X6 Desert of the Sphinx's west lip. No Meshy, no particles, no
rig, no Codex (0 credits). Built and installed 2026-11-20 as `assets_source/worlds/xeen/models/xeen_deco_sandfall.glb`
(runtime copy cooked into `assets_dev/worlds/xeen/models/`), bound in `assets_dev/worlds/xeen/models/decorations.yml`
(`xeen_sandfall`, decoration row 4002, sprite 27002).

## Rebuild

```bash
cd level_generation/decorations/xeen_sandfall_claude
python3 scripts/build_fall.py sandfall      # textures + GLB + work/sandfall/report.json (a second, pure Python)
PATH=$PWD/../../creatures/xeen_tiers_claude/bin:$PATH blender --background --python scripts/review_render.py -- \
    $PWD/work/sandfall/xeen_deco_sandfall.glb $PWD/review/final 1500 [bright]   # mock-rim review renders
python3 ../mm8_3d/animated/scripts/check_winding.py work/sandfall/xeen_deco_sandfall.glb   # 0 inverted
# from the repository root:
python3 tools/install_model.py level_generation/decorations/xeen_sandfall_claude/work/sandfall/xeen_deco_sandfall.glb \
    --world xeen --name xeen_deco_sandfall.glb
```

After a rebuild set the binding's `height` to `report.json` `height_units` (the engine scales by the bounds' height;
the exact value keeps the model at 1:1 in map units). An install whose texture changed leaves the old cooked
`.oytex` in `assets_dev/worlds/xeen/models/textures/`: delete it by name once no GLB refers to it.

## The model

All parameters are in `scripts/presets.py` (`SANDFALL`); `scripts/build_fall.py` writes the GLB directly (numpy).

- **Origin** at the lip: the rim edge's top, mid-width. The land is behind (-out), the drop in front (glTF +Z; at
  `facing: 90` the fall pours toward -x, west). The engine places the model origin at the decoration's z
  (`DecorationModelSet::placementFor`, `z = entity z + z_offset`), scaled by `height / bounds height`.
- **Core** (`Core`, blended, lit, double-sided, 1,178 triangles): one sheet from a tongue buried 450 units inland,
  bulging up to 60 over the edge (a mound, its sides sunk into the ground), down an outward chute (run about 0.55 per
  unit of drop: about 100 units clear of a 512-unit rim cell's terrain slope), vertical below about 1,600. Seven lanes
  across its texture (alpha 0 at every lane border, the outer 14 % faded) fray into strands: each lane squeezes to a
  point between 920 and 1,300 below the lip, keeping its whole texture width (a soft-sided strand thinning out).
- **Haze** (`Haze1`, `Haze2`, additive, 544 + 312 triangles): two wider sheets 40 and 95 units outside the core, from
  the edge to 2,250-2,300 below it, faded in at the top, at the sides and to nothing at the bottom through COLOR_0.
- **Plume** (dust lifting off the lip, additive): built when the preset has a `plume` entry; off (`plume_off`):
  an additive plume can only lighten, and over X5's bright sky it read as white spray (review/ingame1).
- **Texture V is travel time**: speed starts at 45 units/s at the tongue's inland end, 148 at the edge (tongue
  acceleration 22), then gravity 520 units/s² along the path (575 at 300 below the lip, 1,125 at 1,200, 1,450 at
  2,000); V = scroll x time, so one constant `openyamm_uv_scroll` moves the grains with the flow: creeping on the
  tongue, accelerating down the drop, streaks stretching as they fall. Scrolls (texture units/s): core [0, -0.30],
  Haze1 [0, -0.22] (gravity 380), Haze2 [0.012, -0.15] (gravity 300). A negative v moves the texture toward larger
  glTF v, which runs down the fall (as the MM6 fountain's water).
- **Textures** (procedural, `work/sandfall/textures/`): `core.png` 512 x 1024, the lanes, anisotropic periodic noise
  (streaks, clumps, grains), X6's sand (sRGB 0.80 0.67 0.49, after `sand_ripples` 0.76 0.63 0.47), U clamped, V
  tiling; `haze.png` 512 x 1024 tiling, a darker, more saturated sand so the added light stays sand-coloured.
- **Normals**: one for every vertex, mostly up and a little outward (0.35 out, 0.94 up): both sides of a veil of grains
  light alike (the shader does not flip normals on back faces). Specular 0.05 (core), 0 (haze); translucency 0.45 and
  0.15.
- **Size**: 2,034 triangles, one mesh, no LODs (simple, all blended; guidelines §7). Width 800 at the lip (560 at the
  tongue's inland end, 980 at the bottom; haze up to 1,350), tongue 450 inland, outward reach about 1,080, bounds
  2,393 high (98 above the lip to 2,295 below).

### Why strands

The static model shader multiplies the base colour by COLOR_0's RGB but never its alpha (alpha is the flutter weight),
and a scrolling texture cannot carry a fade along the scroll direction. So an additive layer fades anywhere through
COLOR_0, while a blended layer fades only across the scroll (texture U, fixed) or by its geometry. The blended core
therefore ends in strands that taper to points, and the additive haze carries the soft fade to nothing.

## Placement (for A5)

- Entity at the lip: x, y on the rim edge (the last land vertex column; X6/X5: x = (24 - 64) x 512 = -20480), z = the
  edge's terrain height, `facing: 90` (pours west). `z_offset` 0. Decoration list id 4001 (row 4002 - 1).
- Spacing: at least 1,500 between centres (the tongues are 800 wide); 3-5 along the lip, varied spacing, best where a
  dune tongue meets the edge; keep about 400 inland of the edge free of other decorations (the tongue).
- The lip's terrain should be level with or slightly above the edge for 450 inland, so the tongue's end stays buried.
- The terrain water at 0 (the stars) cuts whatever reaches it: with a lip at 1,300-1,700 the strands end above it and
  only the faint haze meets the water. X5's 1,024 lip (the test) lets the longest strands touch the water.

## In-game check (2026-11-20)

Scratch root `../xeen_greattree_claude/work/ingame/root` with three sand-falls on X5's west lip (x -20480,
y 7072 / 4128 / 1184, z 1024, facing 90; the root's `xeen_x5.scene.yml` only). Captures in `review/ingame1` (first
version: haze and plume read as white water spray), `review/ingame2`, `review/ingame3` (final). The falls sit on the
lip and pour west, clear the rim face, show no sorting artefacts against sky or water, and read as sand by day and
dimly at night. Scroll: frame pairs (`review/ingame_scroll`, `ingame3` 03-06) measured by low-pass correlation: the
veil's features move down the screen (4 px near the top, 7 px lower: accelerating), the tongue's toward the edge.

## X7's lava falls (D-40, session 5)

`presets.py` `LAVAFALL` (`python3 scripts/build_fall.py lavafall`; `build_fall.py` gained per-layer `emissive`:
the layer's texture as `emissiveTexture`, `emissiveFactor` and `KHR_materials_emissive_strength`; the sand-fall
rebuilds byte-identical). Installed `assets_source/worlds/xeen/models/xeen_deco_lavafall.glb` (1,609 triangles,
height 2,385.06 units), world decoration `xeen_lavafall` (row 4004, sprite 27004), bound in
`worlds/xeen/models/decorations.yml` (`yaw: facing`). The sand-fall's shape with a 300 tongue, three wide lanes
(an unbroken sheet to 900-1,200, frayed by 1,500-2,100), slower flow (gravity 300, scroll 0.16), molten orange with
dark crust streaks, emission factor (1.0, 0.42, 0.10) x 1.6, the haze as additive heat glow. Seen glowing and
scrolling in game (debug spawn on D2, scale 81.7: `review/lava_ingame/sheet.jpg`). A5 places it as the sand-fall.

## Reuse for X7's lava falls (the plan, done above)

Add a preset in `presets.py`: lava colours in `textures` (rgb, spread, alpha, weights), an emissive or unlit core (add
`emissiveFactor` or `KHR_materials_unlit` in `GlbWriter.material` behind a preset flag), slower `gravity` and `scroll`
for viscous lava, wider and fewer `lanes` (or `split`/`end` past the drop for an unbroken sheet), the haze as rising
heat glow (or a `plume` entry, which suits glowing lava as additive light), and the `path`, `width`, `bulge` and
`sink` tables for X7's north rim. `review_render.py` takes any preset's GLB.
