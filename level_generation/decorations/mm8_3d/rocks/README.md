# MM8 rocks in 3D (2026-10-15/16, complete: all 33 installed)

Static 3D replacements for every MM8 rock that the MM6 models don't already cover: 28 scan rocks (`rock05`-`rock56`), the
tar rocks `rock61`/`rock62` and the rune stones `rock65`/`rock68`/`rock69`. Brief: `../BRIEF.md`; inventory:
`../inventory.json`. Installs go to `assets_source/engine/models/mm8_deco_<rock>.glb` via
`tools/install_model.py --engine` (through `scripts/finish.py --install`).

## Status

All 33 models are installed: `assets_source/engine/models/mm8_deco_<rock>.glb`, with the cooked runtime copy in
`assets_dev/engine/models/`. They are logged in `work/installed.json`. The coordinator binds them (suggested YAML:
`python3 scripts/report.py --yaml`).

- Height is the inventory height, and `height_jitter` is 0.15. The rune stones are one-offs: jitter 0, and a smaller
  sink because plants grow from their base.
- `z_offset` sinks the base about 4 % of the height into uneven terrain, like the MM6 rocks.
- No yaw, mount, free_model, swing or `lod_pixels` is set (default LOD switching). All the sprites are static, so
  there's no animation to replace.

## Native shading pass (2026-10-16, all 33 reinstalled, bindings unchanged)

The first pass matched each sprite's mean colour but read paler and flatter than the painted sprites. All 33 are now
built with the native shading transfer (after `../../../creatures/NATIVE_SHADING_TRANSFER.md` and
`claude_shared/native_shading.py`, read only), `native_shade()` in `scripts/build_rock.py`. It is the default;
`"native": false` in `rocks.json` restores the earlier palette-transfer route.

- **Profile:** the sprite's median luminance per (surface elevation, height) bin.
  - Each opaque pixel's elevation comes from a half-ellipsoid fitted to the silhouette: top pixels face up, rim
    pixels sideways.
  - Left out: the 2-px outline ring, moss and plant greens, and tar blacks.
  - The table prints in each build log.
- **Base colour:** the profile at each texel, compressed toward its median (`contrast` 0.9, because the engine
  lights the rock again). Texels are looked up by their smoothed facing (`facing_blur`) and height.
  - It is multiplied by the scan's local detail: a luma high-pass, log-compressed so big albedo patches don't turn
    black or white (`detail` 1.3), and by cavity AO (`cavity` 1.2).
  - A faint bright line sits on convex edges (`edge` 0.12, from the normal map's divergence), and the brightest
    values are capped near the sprite's brightest bin.
  - Colour comes by luminance through the sprite's own pixels: the median of the nearest-luminance pixels at 48
    stops. Saturation is boosted (`chroma` 1.3).
- **Moss, plants, tar and runes:** as before, applied on top. Moss stays only where the sprites have it.
- **Level:** the profile carries the sprite's brightness, so there's no mean-colour gain, except rock09, rock20 and
  rock33. For those, `match` (clamped 0.6-1.4) plus `lift` (0.85 / 0.85 / 0.9) bring flat, upward-facing rocks in
  line, since nearly all their visible surface faces the sun. rock33 also uses a softer `detail` of 0.8.
- **Review:**
  - Before/after sheets: `review/before_after_pilot.png` (out01 rocks plus rock16 and rock24) and
    `review/before_after_{1,2,3,4,fix}.png` (the rest).
  - Each row shows the native sprite, before under neutral light, after under neutral light and after top-lit
    (`review.py` now renders a top-lit view as `toplit_y*.png`), with the mean sRGB and the p10-p90 luminance of
    each.
  - Renders cull back faces as the engine does; `finish.py` runs `../animated/scripts/check_winding.py` before
    every install.
  - All 33 pass with 0 inverted closed parts.
- **Sources:** the MM8 x2 sprites were retired from `assets_dev/engine/decorations_x2` on 2026-10-16. The scripts
  read them from `assets_legacy/decorations_x2_mm8_20261016/` (read only) when the runtime copy is gone.
- **Compromises:**
  - The sprites' painted crack networks and veins are added by projection on rock07, rock16, rock24 and rock33 (see
    "Projected sprite detail"); the other rocks keep the scans' own surface detail.
  - rock53's cluster stays lower in contrast (64-96 vs the sprite's 20-128 luminance).
  - The baked top light is fixed: a light from below does not brighten the underside (accepted, as for the
    creatures).

## Projected sprite detail (2026-10-16: rock07, rock16, rock24, rock33)

For the rocks whose sprites carry painted surface patterns (cracks on rock07/rock16, the orange vein network on
rock24, veins on rock33), `project_detail()` in `scripts/build_rock.py` (`project` in `rocks.json`) projects the
sprite's own detail onto the model, on top of the native shading.

- **Camera:** the sprite's (front, yaw 0, which the scan's `view` turned toward it; 8 degrees up). The model's
  projected outline is framed onto the sprite's opaque box, so features land where the sprite paints them.
- **What is projected:** the per-channel high-pass of the x2 sprite (`assets_legacy/decorations_x2_mm8_20261016/`).
  - It is the colour over its alpha-normalised blur, `sigma` 3 px, sampled bilinearly, so the 1-2 px cracks
    survive and the veins keep their hue.
  - The 3-px outline ring is left out.
  - It multiplies the linear colour, so the low-frequency baked shading stays.
- **Weight:** by facing the camera (smoothed normals), full from about 15 degrees and fading to 0 toward the sides,
  where the scan detail continues. The back gets the mirror image at 0.7 strength. Front strength is 1.6.
- These four now use 1024 textures (rock16 and rock24 were 512), so the patterns resolve.
- **Review:** `review/project_before_after.png` (native | front before | front after | side before | side after).
  The fronts carry the sprites' cracks and veins at the same places, and the sides show no visible stretching. All
  four pass the winding check.
- **Compromises:**
  - The models' silhouettes differ a little from the sprites, so features land approximately, not pixel-exact.
  - Seen from the side, the projected half ends where the fade begins.
  - The projection is fixed to one direction; under random yaw it is just a richer pattern.

## Pipeline

`./build.sh [--install] [rock...]` runs, for each rock:

1. `scripts/build_rock.py`: Blender, settings in `scripts/rocks.json`. Adapted from the MM6 leftover-rock builder
   (`../../mm6_dungeons_3d/leftovers/scripts/build_rock.py`, read only). Scans (`scripts/rocks_lib.py` `SCANS`,
   with set pieces picked by node) are placed by `view` (the survey yaw that faces the front; `scripts/survey.py`,
   sheets `review/survey_*.png`), plus `scale`, `tilt`, `ramp`, `taper` and secondary `parts`. `fit` pulls the
   front aspect toward the sprite's width/height.
   - Geometry: loose scan crumbs are dropped, then an optional voxel `remesh` (needed for rock05), collapse
     decimation and a dome unwrap. Coarser LODs are decimated from LOD0.
   - Bake (Cycles on the CPU, because the GPU is shared): normal, diffuse, AO/roughness/metal, plus position and
     normal for the masks.
   - Colour: AO folded in, `grade`, then a **palette transfer** toward the sprite. The texel luma is mapped through
     the scan-to-sprite luma quantiles, with the sprite's spread scaled by `transfer.contrast` (0.6) because part of
     it is painted shading. Chroma blends toward the sprite's per-quantile chroma (`palette` 0.6).
   - Moss layers: value-noise masks (low skirt, up-facing, crevices, speckled edges), toned from the sprite's own
     green pixels.
   - Final gain: the visible rock texels' mean sRGB equals the sprite's rock pixels' mean (moss and tar pixels left
     out), the same convention as the MM6 leftover rocks.
   - Texture size by height (1024 / 512 / 256; rune stones 2048); the metallic-roughness map is half size.
   - COLOR_0 is contact occlusion against the parts and the ground.
   - Tar (`tar`): a 3D Voronoi border network plus crevices. It darkens the rock, carries bulges in the normal map
     and low roughness, and an offset shell (material `Tar`, MASK on the base colour alpha, `openyamm_specular` 1.0)
     raises the flows on LOD0-2.
   - Rune stones:
     - `stone_height`/`width`/`sprite_box` map sprite pixels onto the stone's front.
     - `runes`: carved strokes traced from the sprite by `scripts/make_runes.py` (`textures/runes_<rock>.png`),
       projected from the front. They darken the albedo and add relief in the normal map.
     - `plants` (`scripts/plants.py`): vines and roots as tubes (`Bark`), plus ivy and orange leaves, sprigs, grass
       and lilies as cards (`Plant`, MASK, double-sided, `openyamm_wind` 0.01, translucency 0.3, specular 0.15).
       Both materials use the procedural atlas from `scripts/make_plant_atlas.py` (`textures/plants_*`, our own
       work). Coarser LODs keep fewer, larger cards and thinner tubes.
2. `scripts/review.py`: Eevee, neutral grey sky plus sun. Renders LOD0 front, three-quarter and side, and every LOD.
3. `scripts/sheet.py`: `review/<rock>/compare.png` (native x2 sprite, the views and the LODs with triangle counts).
4. `scripts/finish.py`: material settings, `tools/link_static_model_lods.py`, then validation (LOD chain, budgets,
   COLOR_0, base on the ground, material count). With `--install`, it runs `tools/install_model.py --engine --name
   mm8_deco_<rock>.glb` and refuses to overwrite models this batch didn't install.

Budgets (LOD0): hundreds of placements ≤ 800 (rock16: 700), tens ≤ 1500, one-offs ≤ 3000, pebbles 200-300 with
three LODs. Other levels are about 0.42 / 0.16 / 0.06 of LOD0. The tar shell and the plants add to the rock's budget
(see `budget` in `rocks.json`).

## Sources and licences

All Poly Haven, CC0:
- Read in place from the MM6 projects (read only): `boulder_01` (Rico Cilliers); `namaqualand_boulder_03`,
  `_04`, `_05` and `_06`, and `namaqualand_boulders_01` (Jenelle van Heerden; photography Dario Barresi or Greg Zaal,
  see `../../mm6_new_sorpigal_3d/rocks/README.md`).
- Downloaded into `source/` (`scripts/fetch_scans.py`, md5-checked):
  - `rock_moss_set_01` and `rock_moss_set_02` (Kless Gyzen);
  - `namaqualand_stones_01` and `namaqualand_rocks_01` (modelling Jenelle van Heerden, photography Greg Zaal);
  - `rock_07` and `stone_01` were surveyed and not used; their downloads are removed.

The plant atlas, rune masks (traced from the native sprites), tar and moss are generated here.

## Models

Rebuild everything with `./build.sh` (CPU bakes, about 1-2 min per rock, about 4 min per rune stone). Review sheets:
`review/<rock>/compare.png` (native x2 sprite | LOD0 front | three-quarter | side, over the LODs with triangle
counts); stacked overviews: `review/overview_*.png`. Scan survey: `review/survey_{a,b,c}.png`. Sprites:
`review/sprites_all_{1,2}.png`.

| Rock | Sprite | Scans | LOD triangles | Texture | File | Installed |
|---|---|---|---|---|---|---|
| `rock05` | rock, h 69 w 118, 26 placed | ms1_2 | 1499 / 629 / 239 / 89 | 1024 | 2.72 MB | yes |
| `rock07` | rock, h 33 w 62, 57 placed | nb05 | 700 / 294 / 112 / 42 | 1024 | 3.02 MB | yes |
| `rock08` | rock, h 36 w 59, 6 placed | ns_c | 700 / 294 / 112 / 42 | 512 | 0.81 MB | yes |
| `rock09` | rock, h 15 w 45, 42 placed | nbs01a | 250 / 112 / 50 | 256 | 0.22 MB | yes |
| `rock12` | boulder, h 105 w 124, 1 placed | ns_b | 2500 / 1050 / 400 / 150 | 1024 | 2.85 MB | yes |
| `rock14` | rock, h 56 w 120, 20 placed | nb06 | 1200 / 502 / 192 / 72 | 1024 | 2.50 MB | yes |
| `rock16` | rock, h 26 w 61, 213 placed | nbs01a | 700 / 294 / 112 / 42 | 1024 | 2.64 MB | yes |
| `rock17` | rock, h 14 w 28, 88 placed | ms2_12 | 199 / 89 / 39 | 256 | 0.20 MB | yes |
| `rock18` | rock, h 33 w 60, 35 placed | ns_b | 700 / 294 / 112 / 42 | 512 | 0.89 MB | yes |
| `rock19` | rock, h 30 w 57, 1 placed | ns_a | 800 / 336 / 128 / 48 | 512 | 0.75 MB | yes |
| `rock20` | rock, h 15 w 42, 11 placed | ms2_10 | 250 / 112 / 50 | 256 | 0.21 MB | yes |
| `rock22` | rock, h 29 w 59, 82 placed | nr_b | 798 / 336 / 128 / 48 | 512 | 0.85 MB | yes |
| `rock24` | rock, h 36 w 41, 81 placed | nbs01a | 700 / 294 / 112 / 42 | 1024 | 2.85 MB | yes |
| `rock25` | rock, h 17 w 29, 16 placed | nbs01b | 200 / 90 / 40 | 256 | 0.23 MB | yes |
| `rock26` | boulder, h 106 w 117, 16 placed | nb04 | 1500 / 630 / 240 / 90 | 1024 | 2.80 MB | yes |
| `rock27` | rock, h 56 w 118, 7 placed | nb04 | 1500 / 630 / 240 / 90 | 1024 | 2.99 MB | yes |
| `rock28` | rock, h 29 w 59, 18 placed | ms1_5 | 600 / 250 / 96 / 36 | 512 | 0.85 MB | yes |
| `rock30` | rock, h 39 w 53, 39 placed | nb03 | 700 / 294 / 112 / 42 | 512 | 0.81 MB | yes |
| `rock33` | rock, h 54 w 95, 5 placed | nr_b | 1500 / 630 / 240 / 90 | 1024 | 2.87 MB | yes |
| `rock34` | rock, h 39 w 105, 3 placed | ms2_8 | 1200 / 502 / 192 / 72 | 512 | 0.77 MB | yes |
| `rock35` | rock, h 58 w 107, 4 placed | nbs01b | 1200 / 502 / 192 / 72 | 1024 | 2.75 MB | yes |
| `rock44` | rock, h 22 w 55, 27 placed | nbs01b | 300 / 134 / 60 | 256 | 0.23 MB | yes |
| `rock47` | rock, h 89 w 117, 6 placed | ns_b | 2000 / 840 / 320 / 120 | 1024 | 2.92 MB | yes |
| `rock51` | rock, h 27 w 64, 24 placed | boulder_01 | 600 / 250 / 96 / 36 | 512 | 0.79 MB | yes |
| `rock52` | rock, h 50 w 112, 29 placed | ms2_8 | 1200 / 502 / 192 / 72 | 1024 | 2.38 MB | yes |
| `rock53` | rock, h 68 w 113, 24 placed | nbs01a + nbs01b + nbs01a + nbs01b | 1498 / 624 / 240 / 88 | 1024 | 3.25 MB | yes |
| `rock54` | rock, h 63 w 125, 7 placed | nb06 | 1500 / 630 / 240 / 90 | 1024 | 2.91 MB | yes |
| `rock56` | rock, h 54 w 122, 31 placed | ms2_7 | 1200 / 502 / 192 / 72 | 1024 | 2.11 MB | yes |
| `rock61` | tar rock, h 69 w 118, 3 placed | nbs01b + nbs01a + nbs01b + ns_c + nbs01a + ns_b + nbs01b + ns_a | 2882 / 1220 / 472 / 94 | 1024 | 3.46 MB | yes |
| `rock62` | tar rock, h 100 w 123, 10 placed | nb04 | 2936 / 1258 / 476 / 102 | 1024 | 2.55 MB | yes |
| `rock65` | ancient rune stone, h 319 w 160, 1 placed | ms1_3 | 2582 / 1294 / 580 / 232 | 2048 | 10.75 MB | yes |
| `rock68` | ancient rune stone, h 91 w 120, 1 placed | nbs01b | 2118 / 957 / 392 / 155 | 2048 | 11.50 MB | yes |
| `rock69` | ancient rune stone, h 128 w 254, 1 placed | nb03 + nbs01a + nbs01a + nbs01b + nbs01b | 2530 / 1174 / 498 / 182 | 2048 | 15.59 MB | yes |

The file size is the uncooked source GLB; the cook stores BC1/BC5 textures, and the normal map at half size.

### Notes per model

- **Moss** (rock05, rock26, rock27, rock28; light on rock12 and the rune stones): the tone comes from the sprite's
  own green pixels.
- **Tar rocks** (rock61, rock62), second pass after the coordinator's review (2026-10-16):
  - Tar: thick raised ropes. The tar mask (3D Voronoi borders plus crevices) is thinned to centre lines in UV space;
    the dome unwrap keeps the visible surface on one island, so the lines are continuous. Spurs and crumbs are
    dropped, and the lines are lifted to 3D through the baked position and normal maps.
  - Each rope is a smooth half-tube, sunk 30 % of its radius into the rock: about 1.5 x the mask's local half
    width, 0.85 x as high, meandering gently sideways and tapered at its ends.
  - The ropes are opaque material `Tar` with no textures, so there is no alpha edge and no normal-map grain:
    near-black, roughness 0.2, `openyamm_specular` 1.0. The smooth tubes give a broad soft highlight along each
    rope.
  - Under and around the ropes the rock is darkened, with a flat-plus-bulge normal and matte roughness 0.55, so
    there's no grazing sheen. LOD3 has no ropes; the texture carries the tar.
  - Coarser levels keep the longest ropes (70 / 45 %) with fewer sides (6 / 4 / 3) and a sampling step solved
    against the tar budget (1300 / 550 / 220).
  - rock61 is now eight stones: one stacked on top, two dropped at LOD3.
  - Both rocks pass `../animated/scripts/check_winding.py`. `finish.py` runs it before every install, and the review
    renders cull back faces like the engine.
- **Rune stones** (rock65, rock68, rock69):
  - The runes are traced from the native sprite (`textures/runes_<rock>.png`) and carved into the albedo and normal
    map.
  - The `Bark` material (opaque) is used by vines and roots. The `Plant` material (MASK 0.5, double-sided,
    `openyamm_wind` 0.01, `openyamm_translucency` 0.3, `openyamm_specular` 0.15) is used by the ivy, orange leaves,
    lilies, sprigs and grass, on the shared procedural `plants_*` atlas (1024).
  - Each rune stone has three materials, so three draws per LOD.
  - Vines are gnarled: knotty thickness, a slight meander and the bark twisted round them. rock68's root uses the
    atlas's grey-green `root` strip (2026-10-16 polish).
  - rock65 is a `rock_moss_set_01` slab stood up; rock68 is a `namaqualand_boulders_01` dome with a root arching
    over its right side; rock69 is a `namaqualand_boulder_03` block between two tapered stones plus two pebbles.

### Compromises

- Colour and lighting:
  - The scans have none of the sprites' painted light and shadow. The albedo mean matches each sprite's mean (the
    convention of the MM6 leftover rocks), so the review renders under neutral light look paler and flatter than
    the sprites. Check under the engine's lighting.
  - The palette transfer brings each rock toward the sprite's tonal range and hues, but not its painted crack
    networks: rock24's dark vein network and rock16's crack pattern are missing.
- Shapes:
  - Shapes come from scans seen from the side that best matches the sprite. Under random yaw they read as other,
    similar rocks.
  - rock33 is blockier than its rounded sprite, and rock30 lighter and sharper.
  - rock51 and rock12 are craggier than their smooth sprites.
  - rock53's four boulders are separate scans, more spread out than the sprite's tight pile.
  - rock61's pile has four stones where the sprite has about eight.
- Pebble budgets: the pebbles (rock09, 17, 20, 25, 44) are 200-300 triangles with three LODs and 256 textures.
- Tar: the ropes follow cell borders, so they form a more regular network than the sprites' hand-painted flows,
  with no drips running down the sides. rock61's top stone peaks right of the sprite's peak.
- Rune stones:
  - Plants are cards on a procedural atlas, simpler than the sprites' painted ivy.
  - rock69's side stones are smooth cones.
  - Leaf cards thin out at LOD1-3 and the vine loses sides; LOD3 keeps a few large cards.
- Texture memory:
  - Every rock bakes its own texture set (1024 for heights from 50 units, 512 from 25, 256 below; rune stones
    2048), so scans reused across rocks don't share texture memory.
  - Texture sizes follow on-screen size instead: the 213-placement rock16 is 512.
