# Real MM9 screenshots against our bakes and MM9's own data (measurements, 2026-10-31)

This file records measurements only. No map's lighting, profile or bake was changed: the per-map recalibration was
called off (user decision 2026-10-31). The goal is one global cause, found in MM9's renderer, our shaders' colour space
or MM9's player/dynamic lights, and applied the same way to every map. This table is the test data for that work.

## Method

- **Real shots** are YouTube frames: compressed, with unknown gamma and black level. The real 3D view is the box x 20–78 %,
  y 5–88 % of the frame, which leaves out the portraits and the minimap. The box also includes things we do not draw:
  Yanmir and a Forest Giant (Yanmir's Fort), status text and spell effects.
- **Our captures** come from each map's `make_real_tour.py` (desktop run, installed bake, `video.view_distance=unlimited`,
  `relight_tour.py ... baked`). Ours is 16:9 with a 60° vertical field. We assume MM9 is 4:3 with a 90° horizontal
  field. Our frame is measured over the same view directions (`real_shots.py ours_frac`: x 20.8–77.3 %, y 0–99.4 %) with
  our HUD masked. **Bands** are the box's upper, middle and lower thirds of the real frame, mapped the same way. The
  other boxes are given in real-frame fractions. Luma is Rec. 709 on the 8-bit values.
- **Poses** were found from the compass (MM9's north is LT +z), doors, lamps, pillars and the bone piles. Each pose is
  close to the shot, not exact; the `alt` rows are neighbouring poses and give the spread. Dungeon of Secrets shot 3
  looks through an open axe door, and our tour cannot open it. Row 3a is therefore the near wall with our door shut, and
  row 3b is the room behind it, seen from the threshold.
- **MM9 prediction** (`real_context.py`) casts 64×48 rays through the real box from our eye, which is 160 native units
  above our floor. Each ray stops at the nearest DAT polygon (every world model, invisible surfaces skipped). There it
  takes the DTX texel (the import's bitmap at MM9's surface mapping) **× the DAT lightmap texel, ×1**
  (`MM9_RENDER_LIGHTING_RE.md`). Not in the prediction: models, props, actors, dynamic lights and the player light, and
  surfaces without a lightmap (Dungeon of Secrets' water, `WaterMarker`, 37 % of shot 2's rays; a perception brush in
  shot 4).
- Files: `measurements/measurements.json` holds every number below, the prediction by surface kind and texture, and the
  light lists. `measurements/<map>_context.json` holds the per-shot context. The sheets are real | ours | alts:
  `yanmirsfort_real_vs_ours.jpg`, `dungeonofsecrets_real_vs_ours.jpg` and `dragonstadium_real_vs_ours.jpg`, all looked
  at. Tools are in `level_generation/projects/mm9r_common/`: `real_shots.py`, `real_context.py`, `real_measure.py`.
  Each map also has its own `make_real_tour.py`.

Reproduce:
```
python3 level_generation/projects/mm9r_<map>/make_real_tour.py real01        # (Dungeon of Secrets: real03)
python3 level_generation/projects/mm9r_common/relight_tour.py level_generation/projects/mm9r_<map> \
    level_generation/projects/mm9r_<map>/review_tour_real01.yml real01 baked --set video.view_distance=unlimited
python3 level_generation/projects/mm9r_common/real_context.py level_generation/projects/mm9r_<map> \
    level_generation/projects/mm9r_<map>/review_tour_real01.yml --json devdocs/.../measurements/<map>_context.json
python3 level_generation/projects/mm9r_common/real_measure.py
```

## World settings

| Map | WorldInfo | WorldProperties |
| --- | --- | --- |
| yanmirsfort | `LMGridSize 32; MaxLMSize 32; AmbientLight 35 35 40` | LightScale 255, **PlayerLightOn 1**, DynamicLightDist 2500 |
| dungeonofsecrets | `PBlockSize 2048; AmbientLight 42 32 32` (grid 20) | LightScale 255, **PlayerLightOn 0**, DynamicLightDist 2500 |
| dragonstadium | `AmbientLight 45 45 45` (grid 20) | LightScale 255, **PlayerLightOn 1**, DynamicLightDist 2500 |
| klusoshouse (earlier shots) | `AmbientLight 60 60 60` | LightScale 255, PlayerLightOn 1 |
| verhoffinruins (earlier shot) | `PBlockSize 1024; AmbientLight 50 50 50` | LightScale 255, PlayerLightOn 1 |

## Table (this session's 7 shots)

Columns: luma (median) (mean RGB) B/R. "real / MM9" is the real luma divided by the MM9 prediction. The bands are the
upper / middle / lower thirds.

| Real shot | Our pose | Real | Ours (x real) | MM9 tex×lm ×1 | real / MM9 | Real bands | Ours bands | MM9 bands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| yanmirsfort 1 | `y1_great_hall_south` | 69.0 (69.5) (38,73,123) 3.24 | 97.0 (101.1) (52,104,160) 3.08 x1.41 | 69.1 (31,75,124) 4.00 | **1.00** | 78.9/61.3/66.7 | 94.0/92.4/107.7 | 83.6/61.2/62.3 |
| ″ alt | `y1_alt_west` | | 98.6 (101.6) (51,106,166) 3.25 x1.43 | 67.7 (32,73,123) 3.84 | 1.02 | | 106.0/89.7/103.9 | 87.1/56.5/59.7 |
| ″ alt | `y1_alt_east` | | 99.2 (102.5) (51,107,167) 3.27 x1.44 | 67.8 (32,73,124) 3.88 | 1.02 | | 105.1/91.0/105.4 | 84.7/58.3/60.3 |
| yanmirsfort 2 | `y2_great_hall_southwest` | 82.5 (87.9) (47,85,158) 3.36 | 98.1 (101.8) (52,105,171) 3.29 x1.19 | 64.0 (31,68,119) 3.84 | **1.29** | 75.2/79.7/92.6 | 99.3/97.3/97.8 | 78.0/58.3/55.8 |
| ″ alt | `y2_alt_northeast` | | 119.8 (129.7) (70,128,185) 2.64 x1.45 | 71.5 (36,75,138) 3.83 | 1.15 | | 102.8/116.1/145.1 | 72.1/64.9/77.5 |
| ″ alt | `y2_alt_east` | | 110.2 (112.5) (53,120,184) 3.47 x1.34 | 64.7 (34,68,125) 3.68 | 1.28 | | 99.5/110.7/121.7 | 66.5/62.7/65.0 |
| dungeonofsecrets 1 corridor | `d1_west_corridor` | 40.1 (36.4) (55,36,35) 0.64 | 28.6 (19.4) (33,27,27) 0.82 x0.71 | 24.1 (31,22,22) 0.71 | **1.66** | 40.3/51.1/29.1 | 15.7/41.3/23.5 | 20.3/33.2/18.7 |
| ″ alt | `d1_alt_back` | | 20.6 (13.1) (23,20,20) 0.87 x0.51 | 16.3 (20,15,17) 0.85 | 2.46 | | 14.3/30.5/12.2 | 15.3/23.5/9.9 |
| dungeonofsecrets 2 purple room | `d2_pool_room_w` | 8.8 (3.4) (7,6,40) 5.71 | 16.2 (14.1) (16,15,26) 1.62 x1.84 | 15.7 (17,13,35) 2.06 (walls only) | **0.56** | 11.1/5.9/9.2 | 20.7/16.2/11.0 | 18.0/13.1/– (water) |
| ″ alt | `d2_alt_south` | | 14.3 (13.4) (15,14,15) 1.00 x1.62 | 11.4 (14,11,12) 0.86 | 0.77 | | 13.8/15.5/12.8 | 11.0/12.7/10.0 |
| dungeonofsecrets 3 doorway | `d3a_hub_door_s10` (door shut) | 45.8 (42.5) (62,42,40) 0.65 | 71.2 (68.1) (82,68,66) 0.80 x1.55 | 56.1 (69,53,50) 0.72 | **0.82** | 50.2/51.6/35.5 | 80.8/75.8/53.0 | 62.2/61.7/44.4 |
| ″ room behind | `d3b_s10_room` | | 62.6 (60.5) (72,60,58) 0.81 x1.37 | 52.1 (65,49,46) 0.71 | 0.88 | | 66.7/69.3/47.4 | 55.9/63.3/37.2 |
| dungeonofsecrets 4 corridor | `d4_s04_corridor_w` | 41.8 (42.9) (47,40,46) 0.98 | 15.1 (14.7) (15,15,19) 1.27 x0.36 | 11.1 (13,10,16) 1.23 | **3.77** | 38.7/42.5/44.2 | 13.1/17.3/14.0 | 10.0/13.4/9.8 |
| ″ alt | `d4_alt_back` | | 14.8 (14.9) (15,14,17) 1.13 x0.35 | 12.4 (15,11,15) 1.00 | 3.37 | | 13.0/16.6/13.9 | 11.7/14.1/11.2 |
| dragonstadium 1 floor | `s1_floor_southwest` | 66.9 (66.8) (70,66,69) 0.99 | 36.9 (30.2) (38,36,38) 1.00 x0.55 | 32.9 (34,32,34) 1.00 | **2.03** | 24.7/75.5/100.6 | 14.9/42.0/53.9 | 11.6/37.2/49.8 |
| ″ alt | `s1_alt_closer` | | 37.7 (30.4) (38,37,39) 1.03 x0.56 | 32.1 (33,32,33) 1.00 | 2.08 | | 15.1/44.2/53.2 | 11.5/35.2/49.6 |
| ″ alt | `s1_alt_north` | | 35.5 (28.3) (37,35,36) 0.97 x0.53 | 31.0 (32,31,32) 1.00 | 2.16 | | 15.1/42.5/48.2 | 11.7/35.9/45.6 |

### Regions (real-frame boxes, mean luma and RGB; ours measured over the same view directions)

| Shot | Region (x0–x1, y0–y1) | Real | Ours |
| --- | --- | --- | --- |
| dungeonofsecrets 1 | far end wall by the lamp (.33–.54, .33–.63) | 54.5 (72,50,48) | 44.3 (50,43,41) |
| dungeonofsecrets 1 | near left wall (.20–.30, full height) | 51.1 (69,46,45) | 17.7 (19,17,17) |
| dungeonofsecrets 2 | banners (upper .05–.30) | 12.0 (15,6,60) | 21.5 (20,20,41) |
| dungeonofsecrets 2 | passage, lit doorway (.45–.54, .35–.55) | 30.2 (41,27,29) | 25.6 (28,25,26) |
| dungeonofsecrets 2 | water (lower .60–.88) | 9.2 (3,8,40) | 11.0 (10,10,19) |
| dungeonofsecrets 3 | doorway, the room behind (.34–.68, .23–.85) | 50.6 (68,46,45) | 3a door leaf 76.8 (87,74,72); 3b room 69.1 (78,67,64) |
| dungeonofsecrets 3 | near wall left / right of the doorway | 39.6 / 39.5 (54,36,35) | 58.9 (75,55,53) / 72.6 (80,71,69) |
| dungeonofsecrets 4 | purple room at the end (.37–.55, .20–.48) | 9.0 (10,3,60) | 15.7 (15,15,28) |
| dungeonofsecrets 4 | near corridor wall (.20–.33, full height) | 46.1 (52,45,42) | 14.5 (15,14,14) |
| dungeonofsecrets 4 | floor (.35–.60, .60–.88) | 34.0 (41,32,32) | 15.4 (16,15,22) |
| dragonstadium 1 | wall (upper third) / floor (lower third) | 24.7 / 100.6 | 14.9 / 53.9 |

### MM9 surfaces in view (prediction by surface; lightmap RGB 0–255, texture luma)

- yanmirsfort 1: floor `yanmiricenoise` 31 % (lightmap 74,110,152; texture 153), walls `yanmiricewall2h256` 34 %
  (lightmap 70,154,184; texture 112), ceiling 27 % (lightmap 80,211,226; texture 117).
- yanmirsfort 2: floor 43 % (lightmap 71,108,149), walls and pillars 48 % (lightmap 70,150,177).
- dungeonofsecrets 1: walls `dungeonsecretwall2` 47 % (lightmap 118,88,88; texture 82), ceiling 30 % (113,86,85),
  floor 23 % (109,81,81).
- dungeonofsecrets 2: walls `dungeonsecretwall1a` 49 % (lightmap 44,36,103; texture 91), water 37 % (no lightmap).
- dungeonofsecrets 3a: door and wall (lightmap 200,150,146; texture 90). 3b: walls (224,175,171), floor (217,163,163).
- dungeonofsecrets 4: corridor walls `dungeonsecretwall2` 57 % (lightmap 43,33,35; texture 84), ceiling 22 % (41,33,75).
- dragonstadium 1: floor `cave_wall_lava` 54 % (**lightmap 251, saturated; texture luma 50**), wall `rough_cliff_t` 46 %
  (lightmap 47; texture 72).

### MM9 lights at each eye (LT units; full lists in the JSON)

| Shot | Lights whose radius reaches the eye: dist/radius, colour, BrightScale | Nearest dynamic sources (`Fire`, `CandleProp`) |
| --- | --- | --- |
| yanmirsfort 1 | Light2 741/1536 (91,173,255) 0.8 | Lamp0 (blue claw lamp) 844, Torch6 1213, YanmirDust (Fire, r 80) 1243 |
| yanmirsfort 2 | Light8 638/1200 (91,173,255) 0.8; Light2 1275/1536 0.8 | Torch3 649, Torch6 731 |
| dungeonofsecrets 1 | Light35/33 (0,0,128–160) 0.6 at 303–319/500; Light67/37 (255,193,193) 0.55 at 354–412/500; Light2 (0,0,128) 0.4; Light93 (138,0,0) 0.6 700/1000 | none (the map has no Fire or CandleProp; its claw torches are plain props) |
| dungeonofsecrets 2 | Light1/0/2 (0,0,128) 0.4 at 236–348/400; Light29/31 (0,0,128) 0.6; Light43 (255,193,193) 0.55 491/500 | none |
| dungeonofsecrets 3a/3b | Light4 88/100 (255,201,147) 0.45; Light5/7/15/17 (255,193,193) 0.55 at 88–331/500 | none |
| dungeonofsecrets 4 | Light29/31 (0,0,128) 0.6 at 253–275/500; Light65/27 (255,193,193) 0.55 at 425–470/500 | none |
| dragonstadium 1 | ObjectLight0 724/3500 (255,255,255) 0.8 (an ObjectLight: models only in LithTech); the sun DirLight0 (StaticSunLight, lightmap bake only); tunnel lights (bs 0.15) 2400+ away | none |

## Earlier real shots (from READMEs and the ledger; prediction rerun on their review views now)

| Real shot | Our view | Real (this crop) | Ours (this crop; capture of the installed calibration) | MM9 tex×lm ×1 | real / MM9 | Dynamic sources near the eye |
| --- | --- | --- | --- | --- | --- | --- |
| klusoshouse 1 corridor guard | `review/real09` r1 | 64.4 (73,64,41) | 61.4 (71,61,38) | 38.9 (44,39,24) | 1.66 | WallTorch64 89, WallTorch60 185, WallTorch68 271 |
| klusoshouse 2 doorway | r2 | 48.9 (54,49,35) | 47.1 (53,47,31) | 33.9 (39,34,21) | 1.44 | WallTorch68 161, WallTorch60 179, WallTorch69 222 |
| klusoshouse 3 dark room | r3 | 36.2 (40,36,28) | 32.4 (37,32,24) | 22.1 (24,22,17) | 1.64 | WallTorch74 137, CandleProp16 179 |
| klusoshouse 4 Count's room | r4 | 90.0 (103,90,51) | 77.5 (87,78,47) | 61.4 (68,62,36) | 1.47 | CandleProp13 176, Fire4 221 (r 80) |
| verhoffinruins spawn | `review/v09` a01 | 61.1 (66,61,43) | 54.3 (60,54,40) | 48.4 (54,48,32) | 1.26 | BreakOutDust1 (Fire, r 80) 495; DirLight3 reaches the eye |
| beethoven start (`../mm9_real_beethoven_start_youtube.png`) | spot not identified (Beethoven README) | 7.9 (4,10,1) | – | – | – | – |

The Klusos House "ours" numbers are from its calibration, which is ×1.2–1.37 over its lightmaps (README). The README
numbers use another crop (x 18–82 %, y 15–90 %): there, real 64.7, 47.6, 37.0, 92.4 against ours 65.7, 48.0, 35.4,
82.2. For Verhoffin Ruins the README gives real 62, ours 57.

## What the numbers show (observations, not a model)

- **real / MM9-predicted** varies from 0.56 to 3.8. Yanmir 1 is 1.00, matching hue too: (38,73,123) against
  (31,75,124). Yanmir 2 is 1.29, Verhoffin 1.26, Klusos 1.44–1.66, Dungeon of Secrets 1 is 1.66, Dragon Stadium is
  2.03, Dungeon of Secrets 4 is 3.77, and Dungeon of Secrets 2 and 3 are 0.56–0.88. A single ×1 formula does not fit
  every shot, and no single multiplier does either.
- **Close dynamic sources go with the excess:** Klusos has CandleProps 90–180 LT from the eye at ×1.44–1.66. Yanmir 1
  has none within 840 LT, and its ratio is 1.00.
- **Dungeon of Secrets 1 and 4 do not fit that pattern.** They have no Fire or CandleProp, and PlayerLightOn is 0. Yet
  the real near walls are 3× ours and 3× the prediction: shot 4's near wall reads 46 where we have 14.5, and shot 1's
  near left wall 51 where we have 18. The far surfaces are close to ours: shot 1's far end 54 against our 44. This looks
  like a light carried by the party (a Torch Light spell or MM9's player light despite the flag). It is a guess, worth
  testing.
- **Dragon Stadium cannot be reached by a ×1 modulate:** the floor's DAT lightmap is saturated (251/255) and the floor
  texture averages luma 50, yet the real floor's lower third reads 100.6. Its walls are 24.7 against 11.6 predicted.
  The real shot is ≈2× MM9's own texture × lightmap on both floor and walls, while Yanmir 1 is exactly ×1. Candidates:
  a brighter texture in MM9 than the import's bitmap (detail texture, other mip), a modulate2x path, an added light not
  limited by the lightmap's clip (ObjectLight0, the sun), or the video's levels.
- **Dark places are dark in real MM9:** Dungeon of Secrets 2 (the purple room) reads 8.8, below both the prediction
  (15.7 on its walls) and ours (16.2). It is also far bluer: B/R 5.7 against our 1.6.
- **Our renderer on screen relative to the DAT prediction:** ours / MM9-predicted is 1.40 at Yanmir 1, 1.53 at Yanmir 2,
  1.19 at Dungeon of Secrets 1, 1.03 at 2, 1.27 at 3a, 1.20 at 3b, 1.36 at 4 and 1.12 at Dragon Stadium. At Yanmir's
  Fort ours is **brighter and paler** than real MM9: (52,104,160) against (38,73,123) on shot 1. That is the reverse of
  the ledger's "deep saturated cyan" worry. Part of our excess is the bake's own zone ratio (great hall 1.16, README).
  The rest may be the renderer or the x2/x4 textures in the review root; this was not separated here.
- Poses are approximate (see the alt rows). Compression and YouTube gamma make single numbers uncertain by roughly
  ±10–15 %. Treat ratios under 1.2× as "the same".
