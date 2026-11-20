# Terrain materials

The outdoor terrain is drawn from blended ground materials on a smoothed, subdivided terrain: the only terrain style
since 2026-10-15 (the classic per-cell tiles, `video.terrain_style` and the `terrain` asset tier are gone). Every map
with terrain needs its material file (`tools/terrain_materials.py weights`); a map without one fails to load.
In-game:

```text
terrain subdivision 4        (1, 2 or 4 rendered quads per native cell edge; saved)
terrain reload               (rebuild after editing a map's material file or weights)
terrain                      (status: triangles, smoothing deviation, GPU memory)
```

INI keys under `[video]`: `terrain_subdivision` (default 4; Android 2), `terrain_antitiling` (default true; Android
false; the Low and Medium graphics presets turn it off, since it costs about 0.1 ms at ground level) and
`terrain_anisotropy` (default 4x; Android 2x). Android also halves `water_reflection_size` (256), since the
reflection redraws the terrain; its settings profile 3 migrates installs still on the earlier defaults.

**Native tiles.** The runtime loads no tile art. Per map it keeps a tile table (`buildOutdoorTerrainTiles` in
`game/maps/MapAssetLoader.cpp`: each tile's name, liquid and edge role) for the weights, plants, liquid surfaces and
distant sea, plus the coverage mask of every liquid edge tile (`worlds/<world>/terrain_materials/liquid_edges/
<tile>.png`, 128×128, 255 where the liquid shows), cooked from the native tile's alpha by
`tools/terrain_materials.py edges --world <world>` (and by `weights` for its map). The native tiles are source art in
`assets_source/worlds/<world>/terrain_x2`; the weight tool and the editor's tile preview read them there.

## What the engine does

- **Mesh** (`game/outdoor/OutdoorTerrainMaterials.cpp`): indexed 16x16-cell chunks, frustum culled, subdivided
  `terrain_subdivision` times per cell. Heights are Catmull-Rom through every native vertex, kept within the cell's
  height range and softly capped to 32 units from the native triangles (`outdoorSmoothedTerrainHeight` in
  `OutdoorGeometryUtils`), so collision, actors and walls stay on the ground. Smooth per-vertex normals.
  The smoothed surface can reach a building floor laid at a cell's highest vertex (Ravenshore's crystal plaza), so
  `vs_outdoor_terrain_materials.sc` pushes terrain depth back by about 16 steps of a 24-bit buffer: the terrain loses
  those ties instead of z-fighting and showing its dark baked light through the floor.
  Open-water cells are a separate index range, skipped while the water renderer draws the water.
- **Materials**: two `Texture2DArray`s cooked from the library (BC7 desktop / ETC2 Android): albedo+height and
  normal(XY)+AO+roughness. Per layer: world-space repeat, height-blend contrast, normal strength, cavity
  (height-darkened albedo; photoscans are delit, the native tiles carried their shading) and a world tint.
- **Weights**: RGBA images over the 128x128 cell map (16 texels per cell); the two strongest layers blend by height.
  A slope layer replaces steep ground (1 - normal.z of the terrain box-blurred over about a cell, stored per
  vertex and roughened by the macro noise, between `start` and `end`; the raw normal traced the native triangles
  as sawtooth edges) with side projections (from above where the surface itself is level, as on the flat strip at
  a cliff's foot that the broad blur still counts as steep; side projections smeared it into streaks), tinted
  per dominant ground layer (`cliff_from`), so a volcanic island gets dark cliffs and meadows earthy ones.
- **Edge fringe**: the weight tool blurs transitions over `edge_softness` world units; inside that band, fine noise
  (`fringe.strength`, and `fringe.scale` = the world size of one repeat of the macro noise used, 2048 giving ~32-unit
  clumps and ~128-unit islands) tips the balance between the two layers, scattering grass islands into dirt and
  dirt holes into grass; the materials' heights then fray the result. Artist feedback 2026-10-11: smaller seed,
  noisier edges with holes and islands, less pronounced large shapes.
- **Shores** (`shore:` in `world.yml`, needs the water shader): the weight tool turns open-water tiles and the
  alpha of shore tiles into a signed waterline distance (`<map>_shore.png`) and lays `sand` (ambientCG Ground097,
  small ripples) under the water and along `beach_width` units of beach. The mesh sinks a seabed below each cell's
  water level (`seabed_slope`, `seabed_depth`) and rises gently inland (`beach_slope`, blending into the native
  heights over `beach_blend`); collision keeps the native heights. The water renderer then draws shore and open
  water as flat planes at the water level (shoreline flag 2) whose opacity follows the depth to the rendered seabed
  (an R16F height texture): see-through shallows over wet sand with caustics, a swash foam edge that creeps up and
  down the beach and wave lines rolling in. Horizontal BModel water faces at the level of the terrain water they
  cover (Smuggler's Cove's mouth in Ravenshore, out03's waterfall top, out14's culvert) count as that water, so the
  seabed sinks under them; otherwise the beach rose through them, black from the bake under the face.
- **Caustics**: `engine/terrain_materials/caustics.png` (`tools/terrain_materials.py caustics`) holds two tileable
  Voronoi webs (artist feedback 2026-10-11: cell borders of varying thickness and brightness, soft glow, slight
  chromatic fringe). The seabed samples the main web with its lines bent by a few sine waves and a faint finer web
  drifting the other way; the 2-layer array takes stage 0.
- **Seabed cost**: the water turns opaque at `opaque_depth` (72), so only open-water cells with some vertex
  shallower than that draw their seabed; the water's opacity reads the same rendered heights, so it is already
  opaque wherever the seabed stops (no cell edge can show). Below `detail_depth` (24) the seabed is plain: one sand
  sample, the bake as it is, no detail normals, anti-tiling, relighting or mesh shadows; the full path fades into
  it over the half depth above, so there is no seam. Drawing the full seabed under all the sea cost +0.3 ms at a
  shore pose looking out to sea.
- **Crisp roads**: a material with its own smaller `edge_softness` (roads: 24) is softened alone and laid over the
  blurred rest, and its `fringe` factor (roads: 0.15) keeps the edge noise off it, so roads stay roads with only a
  narrow blend into the dirt.
- **Reflections**: water reflection views draw the terrain with the same helper as the main view, but every
  triangle with the single-material program, without anti-tiling or mesh sun shadows: blends, detail and shadows
  are lost in the ripples, and on phones the reflection is the terrain's second-largest cost. Shallow water keeps
  Fresnel reflection at
  grazing angles and fades to nothing at the waterline (no hard intersection line); its foam is lacy and broken.
- **Macro variation** (UE-style): `engine/terrain_materials/macro_variation.png` (`tools/terrain_materials.py
  macro`) is tileable cloudy noise over 16384 world units, sampled once per pixel. Per layer it varies brightness
  (`macro_brightness`) and tints large patches (`macro_tint`, e.g. dry yellowish grass), so fields keep structure
  from the air where the fine detail has averaged out.
- **Variants** (mid-scale variety): a layer may name a `variant` material that takes its second, rotated sample,
  mixed in macro-noise patches (250–1000 units) by height with `variant_amount` coverage. Uniform photoscanned
  grass averages to one green from the air; New Sorpigal grass mixes lush `grass_meadow` with mossy, patchy
  `grass_patchy` (ambientCG Ground037). A variant keeps its own tones under its parent's tint, so its patches read lighter and mossier.
- **Anti-tiling**: without a variant, the second sample is the layer itself, rotated and rescaled. Disabled by `terrain_antitiling=false` (the cheaper mobile path; uniform branch, no shader variant).
- **Lighting**: the bake lit the native flat triangles. The shader keeps the baked indirect/sky light and cast
  shadows, but relights the bake's direct-only sun page (v5 lighting) from the native facet normal to the smooth,
  normal-mapped one, and scales sky light by facing and material AO. Mesh sun shadows, point lights, wetness and fog
  work as before.
- **Liquid edges**: without a seabed (tar and lava, whose rules say `shore: false`), an edge cell discards the ground
  where its coverage mask is full liquid; the liquid renderer draws the liquid with the same mask.
- **Plants**: terrain decorations are scattered on the smoothed surface.
- **Emissive ground** (2026-10-22): a library material with `emissive: {color: [r, g, b], threshold: t}` glows where
  its untinted albedo is warmer than `t` (red minus blue, over a 0.25 ramp): the glow is that albedo times `color`,
  added to the lit colour before the fog, by day and night alike (`u_terrainLayerEmissive`, `terrainLayerGlow`). No
  shipped MM6-MM8 material has it; their layers carry zero, the per-pixel branch is skipped and the image is
  unchanged. Hesper's `creep_resin` (ambientCG Lava001 under a violet tint) uses it for its orange veins
  (`level_generation/projects/hesper_stage/terrain_library.yml`). `tools/terrain_materials.py prepare` carries an
  `emissive` entry of `sources.yml` into the library.

Shaders: `game/shaders/outdoor_terrain_materials.sh` (`fs_outdoor_terrain_materials[_baked][_shadow]`,
`vs_outdoor_terrain_materials`).

## Content

| Path | Contents |
| --- | --- |
| `assets_source/engine/terrain_materials/<id>/download/` | Downloaded CC0 maps (untracked source bank) |
| `assets_source/engine/terrain_materials/sources.yml` | Origin, licence, physical size and map files per material |
| `assets_dev/engine/terrain_materials/library.yml` | Runtime library: cooked files, mean colour, provenance |
| `assets_dev/engine/terrain_materials/<id>/*.oytex` | Desktop cooked arrays (Android: `assets_cooked/android/…`) |
| `assets_dev/worlds/<world>/terrain_materials/world.yml` | Hand-authored: world materials and tile rules |
| `assets_dev/worlds/<world>/terrain_materials/<map>.yml`, `<map>_weights0.png` | Generated per map |
| `assets_dev/worlds/<world>/terrain_materials/liquid_edges/<tile>.png` | Generated liquid edge coverage masks |
| `assets_source/worlds/<world>/terrain_x2/<tile>.png` | Native tiles (source art for the weights and masks) |

Library (all CC0; [MM6–MM8 tilesets](TILESETS.md) maps every native ground to one): `grass_meadow` (ambientCG
Grass004), `grass_patchy` (Ground037), `dirt_cracked` (Poly Haven cracked_red_ground), `soil` (Ground048),
`soil_stony` (rocky_trail), `road_pebbles` (large_pebbles: rounded grey fieldstones with deep joints like the native
road, tinted to its grey with `tint_scale`), `road_flagstone` (stone_pathway: Ironsand's stepping stones),
`rock_ground` (rock_ground_02), `rock_layered` (Rock023), `rock_red` (Rock061), `rock_cliff` (rock_face),
`gravel_volcanic` (Gravel024), `sand_ripples` (Ground097), `sand_flat` (dense_sand), `snow` (Snow008A) and `swamp`
(Moss004 with standing water: a `pools` entry in `sources.yml` fills that share of its broad hollows with flat,
dark, smooth water when it is prepared; the library marks it `pools`, and on level ground the shader draws its
smoothest texels as water that mirrors the sky at grazing angles, ripples and glints).

Coastlines: the weight tool smooths the water mask over half a cell before measuring the waterline, so diagonal
coasts built from square tiles become lines instead of staircases; one-cell rivers and inlets keep their water.

Lava and tar are drawn by the liquid renderer like water; their tile rules say `shore: false`, so the weight tool
puts no beach or seabed around them.

**World liquids and shallow liquids** (2026-10-22, `engine/liquids/liquids.yml`): a liquid with `worlds: [<id>]`
applies only to that world's maps and is matched there before the shared liquids (`LiquidTable::forWorld`), so a
world can give a shared tile its own liquid and colour. `depth: shallow` makes its terrain cells waded rather than
deep water: the loader clears their water bit and land-mask entry (`applyShallowLiquidTerrainAttributes`,
`buildOutdoorLandMask` in `MapAssetLoader.cpp`), so there is no drowning, no blocked entry, monsters walk in it and
dropped items stay. `reflections: false` keeps its surfaces out of the planar reflections (an opaque, matte liquid,
one look on level and sloping cells). Hesper's rust brine uses all three, on the MM8 water tiles with their shore masks
(`level_generation/projects/hesper_stage/liquids.yml`). A harmful variant (D2's cistern, the acid marsh) would add a
damage key beside `depth`; none exists yet. No MM6-MM8 liquid uses these keys.

## Adding a map or world

1. Write or extend `worlds/<world>/terrain_materials/world.yml`: map each tile family to one material or a
   `[foreground, background]` pair (transition tiles are classified per pixel against the reference colours;
   shore tiles keep their alpha as water), and give each material a `reference_tile` for its tint. Where the two
   parts of a pair are too alike in colour, `shape_from: [prefix, other_prefix]` takes the shape from the tile of
   the same layout under the other prefix (Shadowspire's roads over grey dust: `[gdrd, drsr]`). The tool resolves
   tiles like the engine, including a map's `<map>_1.scene.yml` overlay (Shadowspire's master tile). Beaches and
   seabeds use the native shore tiles' dirt, lightened (`sand` with the dirt `reference_tile`).
2. `python3 tools/terrain_materials.py weights --world <world> --map <map>.odm --preview /tmp/preview.png`
   writes the map's slot file and weights; check the preview against the native tile map.
3. New library material: download the CC0 maps under `assets_source/engine/terrain_materials/<id>/download/`, add it
   to `sources.yml`, then `tools/terrain_materials.py prepare <id>`, `cook --profile desktop` and
   `cook --profile android`. The Android package overlays its cooked arrays (`tools/package_runtime_assets.py`).
4. Tune `repeat`, `cavity`, `normal_strength`, `height_contrast` and the slope band in `world.yml`, regenerate,
   then `terrain reload` in-game. A map's own shade of a material (lusher grass, paler sand) goes under
   `maps: {<map>.odm: {<material>: {shade: [r, g, b]}}}`; any other material key, and the `shore` and `slope`
   sections (a desert map's beach of its own sand), can be overridden there too.

[MM6–MM8 tilesets](TILESETS.md) lists every native ground tile the outdoor maps use and the material each needs.

## Pilot measurements (New Sorpigal, desktop NVIDIA, OpenGL)

Subdivision 4: 516k triangles in 64 chunks; smoothing deviation from the native triangles mean 7.4, max 32 units;
88 MB GPU memory (five 2K BC7 material pairs 56 MB, weights with mips 21 MB, mesh 9 MB, baked-normal page 4 MB).

| Pose | Main view classic | Main view materials | Frame GPU p50 classic → materials |
| --- | --- | --- | --- |
| Overview (two runs each) | 120–137 µs | 346–350 µs | 293–317 → 455–461 µs |
| Ground level | 308 µs | 627 µs (419 µs without anti-tiling) | single samples |

After the 2026-10-11 additions (macro variation, grass variant, sand/shore, seabed water, edge fringe): overview
main view 394 µs (frame p50 494 µs), GPU memory 142 MB (seven 2K material pairs, two weight images, shore and
seabed textures).

All MM6–MM8 maps (2026-10-11): Harmondale, eight layers, main view classic → materials 102–113 → 313–350 µs from
above and 222–235 → 492–497 µs at ground level; the shader samples only the two strongest layers, so the layer
count does not change the per-pixel cost. GPU memory 63–156 MB per map (eight 2K layers at most).

So about +0.2 ms over the whole map from above and +0.1–0.3 ms at ground level on this GPU. Single-frame
`[GpuViewPerf]` samples are noisy; Android release-APK timing has not been measured yet.

Performance pass (2026-10-11, 1600×900, main view at the gate/hills/shore/field poses):
- The materials terrain draws after the opaque buildings, so the depth test rejects ground hidden behind them
  (gate 748 → 485 µs, same image). The baked direct-sun pages stay resident while it is active (decoding one per
  frame had cut New Sorpigal to ~300 FPS).
- `terrain_anisotropy` now sets the anisotropy level (it was always the GPU maximum, 16×); the default is 4×.
  Hills main view: 16× 608, 8× 548, 4× 487, off 404 µs (off softens distant slopes slightly).
- The FX light loop stops at the light count: −10 to −25 µs, same image.
- Result with terrain anisotropy off, materials vs classic: 340/378/261/507 µs vs 300/201/182/410 µs
  (1630/1580/1980/1310 vs 1750/1830/2340/1520 FPS); 4× adds about 60–100 µs.
- Single-material triangles: `createMesh` puts land quads whose pixels can read only one ground layer first in each
  chunk (no other layer has weight in the weight texels they reach, two texels more for the coarser mips, and the
  cliff layer cannot blend in), and `submitTerrainMaterials` draws them with the `SINGLE_MATERIAL` program, which
  samples one layer. A layer's height-blend amount fades out with its weight (×10, so below 0.1), so a layer
  without weight no longer shows through the low spots of another and both programs agree at their seam. The
  quad test relies on the shader's macro noise moving the steepness by 0.1 at most. NS_PROF_1 (a dirt field seen
  from above): main view 455 → 391 µs, identical image.
- Trilinear normal array (2026-11-03): only the albedo/height array keeps the anisotropic filter; the normal,
  occlusion and roughness array, read as often, is trilinear (`TerrainMaterialSet::bind`). On the Isle of Ashes'
  open-air BLV, looking along the ground, it took about half the anisotropy's cost (frame GPU time 816 → 710 µs; all
  terrain linear 613 µs); the relief of grazing ground and cliffs is a shade softer. New Sorpigal at the
  tools/RUN_GAME.md example pose, mostly grass, did not change.
- Sharpened mips (2026-10-11): `tools/terrain_materials.py cook` sends `terrain_material` jobs, and the cooker
  (`sharpenTileableMips`) applies a wrapped unsharp mask (strength 3) to every mip below the first, each still
  filtered from the unsharpened level above. At eye-level grazing views the cracked dirt keeps its mid-distance
  detail (gate pose edge energy 14.2 → 17.3, classic 20.0, about a -0.7 mip bias) with no runtime cost. The
  flattened broad shading and long repeats still make materials softer than classic up to a point; that is a
  content choice.
- Sharpening strength 1 (2026-10-14): strength 3 shimmered in the mid-range dirt while moving, because the
  sharpened heights and normals feed the height blends and the relighting. Aliasing was measured as the difference
  between an 800×450 render and a 1600×900 render of the same pose downsampled 2×, on ground-only regions at the
  New Sorpigal gate (`-9728 -10480 230`, yaw 1.5708, pitch -0.12): mid-range error 3.38 at strength 3, 2.04 at 1,
  1.77 at 0.5 and 1.64 unsharpened, with detail (mean |Laplacian|) 21.1, 15.5, 14.2 and 12.7. Sharpening the albedo
  alone added almost nothing, since the visible crack detail comes from the heights and normals. Strength 1 keeps
  about three quarters of the detail with 40 % less aliasing; unsharpened mips looked visibly flat at mid range.
  16× anisotropy changed neither number at this pose.
- Rejected: sampling the detail normal/AO/roughness array without anisotropy. It saved 39 µs looking down
  (NS_PROF_1), where it was invisible, but at eye-level grazing angles it removed most of the crack relief.
- Measured and rejected: distance-based detail level (no saving: distant samples hit small cached mips), per-pixel
  branches that skip the second layer or projection where the height blend cannot show it (no saving: the texel
  heights vary, so neighbouring pixels split), drawing trees before the terrain (−14 µs).
- Upper bounds at the hills pose: anti-tiling −58, second layer −50, detail-normal relighting −49, detail normal
  samples −34 µs. Each is a visible feature.
- Depth pre-pass (2026-11-10): `submitTerrainMaterials` first draws the main view's visible chunks with
  `fs_outdoor_terrain_depth` (`TERRAIN_DEPTH_ONLY`: depth only, the same cells, open liquid and liquid edge coverage
  cut as the shaded programs), then the shaded programs test that depth without writing it. Each pixel is shaded once
  (the chunks draw in map order, so hills behind hills were shaded too), and their `discard`s no longer turn off the
  early depth test, since they write no depth. Water reflections keep the single pass. Same image (the terrain was
  pixel-identical at the oute3 field pose and the 7out02 and out01 start views; the oute3 and out01 coasts, seen from
  above, kept their liquid edges). Frame GPU p50 at
  1600×900, Medium/High preset: New Sorpigal field pose 600 → 556 / 1530 → 1481 µs, 7out02 874 → 808 /
  1842 → 1765 µs, out01 679 → 684 / 1372 → 1238 µs.
- Rejected (2026-11-10): skipping a layer's own projection where the bank's vertical planes (bank 1) or, for the slope
  layer, the view from above replace it entirely. Exact in principle and −35/−84 µs (Medium/High) on Sturmford's
  open-air BLV, where 32 % of the terrain pixels are that steep, but neighbouring pixels split at triangle edges and
  towards the horizon, and the implicit derivatives of the skipped lanes sparkled along those lines. Explicit
  gradients would fix it, but bgfx's OpenGL path has no gradient sampling of texture arrays.
- Ground highlights (2026-10-16, lighting plan phase 6, `video.terrain_specular`): a GGX highlight from the baked sun
  and the light grid's dynamic lights. A material's `specular` in `library.yml` (from `sources.yml` through
  `tools/terrain_materials.py prepare`) sets how much it glints: rock, gravel, flagstones and swamp do, soil and grass
  do not (their roughness maps are not reliable enough to decide it). Rain-wet level ground takes a damp sheen, scaled by
  the material's `wet_sheen` (grass 0.25: blades scatter instead of forming a film).
- One weight array (2026-10-16, lighting plan phase 4): the two weight images are the two layers of one 2D array
  (`s_terrainWeights`, stage 10), which freed stage 11 for the clustered light grid (`light_grid.sh`; the baked
  shadowed program had used all 16 stages). The terrain's dynamic lights (torch, spells, effects) now come from the
  grid in the main view; water reflections keep the shared 8-light list, and baked maps keep their authored lights in
  the bake. Same image (pixel difference ≤ 0.13/255 at the 7out02, out11 and oute3 reference views), and faster:
  main-view frame GPU p50 at noon 700 → 671 (7out02), 633 → 547–559 (out11) and 1525 → 1350–1355 µs (7out13), an
  A/B with only the weights reverted.

## Rejected: far ground composite

Tried and removed 2026-10-29: the blended ground drawn once per map from above into a 4096 two-layer RGBA8 array
(albedo and occlusion, shading normal and standing water; 170 MB with mips), which distant ground read instead of the
materials, with lighting, shadows, shore, wetness, grass colour and fog still per pixel. On the MAW_PERF Harmondale
view (RTX 3060 Ti, 1600x900, frame GPU p50 1051-1080 µs) it saved little without visible blur: a composite texel
covers 16 units, so ground a few thousand units away facing the camera softens. Gating by composite texels per pixel
on the least compressed screen axis: 0.35-0.5 gave 1035-1045 µs (no visible change), 0.25-0.35 1006-1009 µs (upper
hillsides slightly softer), 0.15-0.25 950-957 µs (mid-distance hillsides and roads visibly blurred); a distance gate
(2500-3500 units) saved as much as the last and blurred the same way. About 5% without blur was not worth the memory
and eight extra shader variants.

## Known limits and next steps

- Fountains and pools (BModel water) still have no floor texture, refraction or caustics on nearby walls; the
  artist's suggestion (tiled floor under distorted water, caustics on vertical surfaces) is separate water work.
- Toggling the water shader while the materials terrain is active needs `terrain reload`: the seabed is built only
  with rendered water.

- Materials are generic CC0 photoscans tinted to the native palette; they read more photographic than the
  restored tiles. MM-specific materials (dead/necromancer ground, lava, swamp) would come from Codex generation
  with derived height/normal maps through the same library and cook path.
- Transition shapes follow the native tile art at 16 texels per cell; identical transition tiles still repeat
  their outline (a small domain warp in the weight tool would break it, at the cost of plant/coverage agreement).
- No settings-screen row yet (INI key and `terrain` console command only).
