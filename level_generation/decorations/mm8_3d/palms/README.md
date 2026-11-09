# MM8 palms — static 3D decorations (2026-10-16, done)

Procedural Blender (bmesh) models for the MM8 palm sprites `tree01`–`tree09` (742 placements on Dagger Wound
Island `out01` and Regna `out13`). Pipeline adapted from the MM6 desert palms
(`../../mm6_new_sorpigal_3d/desert/`, scripts copied and changed here; MM6 files untouched). Brief: `../BRIEF.md`.
All nine are installed and bound by the coordinator.

```bash
./build.sh <id> [--install] [--textures]   # one palm (3-10 min depending on machine load); ./build.sh all
python3 scripts/make_textures.py           # shared atlas + barks (about 30 s); changing the atlas means
                                           # re-exporting every installed palm so they keep sharing one image
scripts/closeup.sh <id>                    # review/<id>/closeup.png: sprite | LOD0 front | three-quarter at 1000 px
python3 scripts/overview.py                # review/overview.png, review/overview_lods.png
blender --background --python scripts/crown_profile.py -- <id> ['{json trial settings}']   # crown reach vs sprite
python3 scripts/crown_search.py <id> '[{trial}, ...]'                                      # score trial settings
```

`post_process.py --install` validates, runs `../animated/scripts/check_winding.py` (0 inverted closed parts
required) and installs with `tools/install_model.py --engine --name mm8_deco_<id>.glb`.

## Models

All in `assets_source/engine/models/` (cooked runtime copy in `assets_dev/engine/models/`). Colour Δ = largest channel
difference of the LOD0 front mean against the sprite's mean (sRGB /255, Eevee review light; by design the target is
the sprite's mean lifted by +12 % saturation and +5 % value, clamped to 3.5/255, see Colour pass); LOD Δ = largest
colour / coverage change between neighbouring levels.

| Sprite | Palm | Placements | LOD triangles | Source / cooked | Colour Δ | LOD Δ |
|---|---|---:|---|---:|---:|---|
| `tree01` | coconut, leaning, ringed trunk | 201 | 2748 / 872 / 366 / 4 | 9.7 MB / 449 KB | 3.1 | 1.7 / 2.7 % |
| `tree04` | coconut, curved trunk | 159 | 2548 / 812 / 342 / 4 | 9.6 MB / 414 KB | 3.3 | 1.1 / 4.0 % |
| `tree02` | boot-lattice trunk, compact crown | 103 | 2748 / 872 / 366 / 4 | 9.3 MB / 449 KB | 3.4 | 0.5 / 7.2 % |
| `tree08` | coconut, bright green | 99 | 2548 / 812 / 342 / 4 | 9.6 MB / 414 KB | 3.2 | 1.0 / 5.3 % |
| `tree07` | crownshaft (petiole bundle), boot trunk | 68 | 3156 / 968 / 474 / 4 | 9.4 MB / 534 KB | 3.3 | 1.4 / 3.5 % |
| `tree06` | crownshaft, golden petioles, orange tips | 38 | 2916 / 896 / 438 / 4 | 9.4 MB / 490 KB | 3.6 | 1.4 / 1.9 % |
| `tree03` | crownshaft, boot trunk | 20 | 2916 / 896 / 438 / 4 | 9.4 MB / 491 KB | 3.7 | 3.0 / 0.9 % |
| `tree05` | Canary date palm, dense mop | 12 | 3236 / 1292 / 534 / 4 | 9.6 MB / 580 KB | 3.5 | 1.3 / 1.3 % |
| `tree09` | leaning, wind-swept crown, orange tips | 5 | 2548 / 812 / 342 / 4 | 9.5 MB / 414 KB | 3.5 | 2.1 / 3.9 % |

After the contrast pass the sources are 9.5-9.9 MB (cooked sizes unchanged). Every source embeds the same `tropical_basecolor` / `tropical_normal` pair (identical bytes, checked by hash after
the last re-export) and one of two barks, so the engine holds one copy; the per-model images are the impostor's two
512² maps. Changing `make_textures.py` means rebuilding or re-exporting all nine.

## Colour pass (2026-10-16, user-approved)

The palms read a little muted next to the sprites. Changes: leaflets painted 1.35× brighter (linear,
`LEAF_BRIGHT`) so COLOR_0 tints sit below 1 and highlights do not clip; a yellow-green lift `highlight`
(1.14, 1.2, 0.72) on leaf vertices with high proxy sky visibility (the sunlit upper and outer fronds), on top of the
normal-facing `sun` two-tone; `calibrate_tint.py` aims at the sprite's mean lifted by +12 % saturation and +5 %
value (each channel within 3.5/255 of the sprite; tint clamp 0.3-1.6). The unused dead-frond cell `frondD` is now a
coconut frond with strong orange leaflet tips, used by tree06 (50 %) and tree09 (40 %); tree06's bark tint is
orange-gold (1.4, 0.98, 0.42). Native x2 sprites for the review sheets now come from
`assets_legacy/decorations_x2_mm8_20261016/` (retired from `assets_dev/engine/decorations_x2`).

## Contrast pass (2026-10-16, coordinator review)

The colour pass matched the means but read flat: the sprites' look is value contrast (near-black green gaps and
undersides against lit yellow-green tops). Widened the value range instead of lifting the mean:
- atlas: leaflets painted 2.0× brighter (`LEAF_BRIGHT`, COLOR_0 headroom; 31 % of leaf vertices clipped at 1 before)
  and a near-black green underlay beneath the inner 55 % of every leaflet (`UNDERLAY`), filling the gaps near the
  rachis with the sprites' dark mass while the tips stay open;
- COLOR_0 (leaves): sky-visibility occlusion with a lower floor (0.2) and a crown-depth AO (`inner_floor` 0.3 at the
  centre), the yellow-green `highlight` (1.32, 1.36, 0.7) on sky-visible fronds, then the leaf luminance raised to a
  per-palm contrast exponent about the LOD0 leaf mean (`leaf_contrast.json`, one reference for every LOD) with
  brightened values shifted toward yellow;
- `calibrate_contrast.py` fits the exponent (1-4; tree06 capped at 2: its unusually bright sprite cannot keep the
  mean at a higher exponent) to the sprite's luminance 10th-90th percentile spread, `calibrate_tint.py` the tint to
  the sprite's mean, both on the shadowed front review render (`scripts/contrast.py`); `scripts/calibrate_loop.sh`
  iterates both on quick builds before `build.sh`;
- leaf sheen `openyamm_specular` 0.15 (roughness 0.35); 0.06-0.1 on the very yellow tree09/tree05/tree02. Higher
  values (0.2-0.3 tried) lift every dark leaf with a grey-blue sky reflection (in the engine too: the sky reflection is
  not darkened by COLOR_0), costing contrast and putting the blue mean 8-21/255 over the sprite;
- trunk: ringbark with darker grooves and stronger band contrast, darker coconut bark tint (0.66, 0.52, 0.34).

Front review render (Eevee, sun shadows) against the sprite: Rec. 709 luma percentiles and mean Δ (sRGB /255):

| Sprite | sprite p10 / p50 / p90 (spread) | model p10 / p50 / p90 (spread) | before this pass | mean Δ (r, g, b) |
|---|---|---|---:|---|
| tree01 | 28 / 76 / 132 (104) | 34 / 82 / 119 (85) | 46 | −0.5, −0.2, +0.9 |
| tree04 | 28 / 67 / 140 (112) | 31 / 81 / 116 (86) | 43 | −0.8, −0.1, +2.4 |
| tree08 | 28 / 76 / 149 (121) | 32 / 87 / 118 (85) | 43 | +0.3, −4.5, +3.6 |
| tree02 | 22 / 60 / 126 (105) | 24 / 65 / 115 (92) | 46 | +0.1, +0.3, +1.0 |
| tree07 | 33 / 73 / 139 (106) | 23 / 83 / 118 (95) | 49 | −4.9, −5.0, +3.4 |
| tree06 | 33 / 89 / 157 (124) | 41 / 92 / 128 (86) | 53 | +0.2, −4.0, −0.1 |
| tree03 | 24 / 71 / 130 (106) | 19 / 79 / 116 (98) | 45 | −1.8, −2.2, +0.9 |
| tree05 | 18 / 62 / 151 (133) | 30 / 74 / 111 (82) | 32 | −1.2, −0.8, 0.0 |
| tree09 | 24 / 70 / 140 (117) | 20 / 85 / 117 (97) | 44 | −0.9, −0.6, +2.4 |

The spread is now 77-92 % of the sprites' (it was 30-45 %). The remaining gap is at the bright end: the sprites'
p90 (126-157) includes painted specular glints that a 0.15 sheen and an 8-bit atlas at full COLOR_0 do not reach.

## Leaf overdraw (2026-10-16)

`scripts/layers.py <id> [blend]` (Blender, Cycles): every Leaves fragment passing the alpha cutoff is a transparent
layer multiplying the light by 0.8 (bark and texels under the cutoff fully transparent; one ray per pixel, 512
transparent bounces, no Russian roulette), so layers = log(value)/log(0.8) per pixel with no depth test; front,
three-quarter and side, LOD0-2. `scripts/layer_sheet.py [tag]` writes the heat maps: `review/<id>/layers_<tag>.png`,
`review/layers_overview_before.png`, `review/layers_overview_after.png` (blue 1, cyan 2, green 3, yellow 4,
orange 6, red 8, white 12+).

Mean layers per covered pixel (range over the three views) and the largest 95th percentile:

| Palm | LOD0 | LOD1 | LOD2 before | LOD2 after |
|---|---|---|---|---|
| tree01 | 1.72-1.84, p95 4 | 1.80-1.94, p95 4 | 1.79-1.92, p95 4 | unchanged |
| tree04 | 1.71-1.87, p95 4 | 1.79-1.95, p95 4 | 1.77-1.94, p95 4 | unchanged |
| tree08 | 1.75-1.82, p95 4 | 1.83-1.92, p95 4 | 1.83-1.89, p95 4 | unchanged |
| tree02 | 1.93-2.21, p95 5 | 2.01-2.24, p95 5 | up to 2.18, p95 5 | 1.91-2.25, p95 5 |
| tree07 | 2.09-2.32, p95 5 | 2.15-2.33, p95 5 | up to 2.33, p95 5 | 1.95-2.19, p95 5 |
| tree06 | 2.04-2.38, p95 6 | 2.08-2.33, p95 5 | up to 2.32, p95 5 | 1.94-2.16, p95 4 |
| tree03 | 1.99-2.15, p95 5 | 2.05-2.17, p95 5 | up to 2.18, p95 5 | 1.91-2.05, p95 4 |
| tree05 | 1.85-2.09, p95 4 | 1.88-2.14, p95 4 | up to 2.11, p95 4 | 1.84-2.03, p95 4 |
| tree09 | 2.08-2.34, p95 6 | 2.18-2.43, p95 6 | up to 2.39, p95 6 | 2.07-2.32, p95 6 |

LOD0/LOD1 were already under the 2.5-3 target everywhere (open crowns: fronds overlap mostly near the heart) and are
unchanged. At LOD2 the boot/crownshaft palms, tree05 and tree09 were a little over the ~2 target: `lod2_drop`
leaves out their least-exposed fronds (20 % on BOOT, 15 % on tree05/tree09: lowest sky visibility along the
rachis, the hidden inner fronds at the heart), the rest grow by 1.05 + 0.4 × drop to keep the coverage (LOD2 within
8 % of LOD1), and a crownshaft bundle keeps every other petiole at LOD2 (the double-sided petiole tubes converging
at the trunk top were the 8-12-layer hot spot). No crown-heart shell: the heart is small and open on these crowns,
and the frond strips already hug the painted leaflets (no loose card area to cut). LOD2 triangles dropped to
306-462 (from 342-534).

## Crown-heart fix (2026-10-16, user bug report from out01)

The contrast pass baked near-black leaf COLOR_0 (a quarter to half of the leaf vertices at ~0), hidden from the side
by the sky sheen but black from below once the engine stopped adding the sky reflection on alpha-tested leaves.
Fixes: a soft floor on every leaf vertex at `LEAF_FLOOR` 0.2 of its own undarkened tint (luminance, applied after
the occlusion, crown-depth AO, highlight and contrast exponent; `MeshBuilder.base` keeps each vertex's tint);
ground bounce for undersides (the proxy occlusion's ground term 0.45, was 0.75); crown-depth AO floor 0.45 (was
0.3); the texture's under-leaflet layer deep green (0.022, 0.055, 0.011) × `LEAF_BRIGHT` instead of near-black;
tree02 and tree05 contrast exponent capped at 2.5 (their low tints put the relative floor too low in absolute terms).
The review render now matches the engine: no sheen on alpha-tested leaves (`render_review.py`), and the tint and
contrast were recalibrated without it. New gates (`scripts/gates.py <id> [tag]`, perspective, backface culling):
`under` (1.6 m from the trunk at 2 m height, 60° up) and `low_three_quarter` (eye height, 1.3 × H away), with the
side view: `review/<id>/gates_before.png`, `gates_after.png`.

| Palm | leaf COLOR_0 lum p5 / p25 / p50 before → after | under-view luma p5 before → after | side spread (sprite) |
|---|---|---:|---|
| tree01 | 0.000 / 0.001 / 0.100 → 0.149 / 0.171 / 0.216 | 2 → 30 | 80 (104) |
| tree04 | 0.000 / 0.001 / 0.124 → 0.139 / 0.159 / 0.208 | 2 → 28 | 81 (112) |
| tree08 | 0.000 / 0.002 / 0.214 → 0.233 / 0.269 / 0.340 | 2 → 33 | 67 (121) |
| tree02 | 0.000 / 0.000 / 0.019 → 0.055 / 0.066 / 0.088 | 1 → 21 | 89 (105) |
| tree07 | 0.003 / 0.024 / 0.150 → 0.234 / 0.267 / 0.311 | 7 → 38 | 67 (106) |
| tree06 | 0.026 / 0.140 / 0.379 → 0.291 / 0.329 / 0.388 | 31 → 48 | 68 (124) |
| tree03 | 0.001 / 0.013 / 0.121 → 0.168 / 0.192 / 0.227 | 3 → 34 | 72 (106) |
| tree05 | 0.000 / 0.000 / 0.044 → 0.063 / 0.076 / 0.116 | 10 → 28 | 73 (133) |
| tree09 | 0.000 / 0.000 / 0.082 → 0.095 / 0.113 / 0.137 | 2 → 25 | 81 (117) |

(COLOR_0 is absolute linear luminance; tints differ per palm because the shared atlas is painted 2× bright, so
tree02/tree05/tree09, the darkest and yellowest sprites, sit lower in absolute terms while their floor is 0.2 of
their tint.) Means stay within 1.5/255 of each sprite (front render, no sheen). The front/side luminance spread fell
from 82-98 to 67-89: the floor takes the near-black end, the dark gaps stay in the texture.

## Bindings (as bound by the coordinator; the decoration manifests live in `assets_dev/engine/models/`)

```yaml
  - name: tree01
    model: engine/models/mm8_deco_tree01.glb
    height: 980
    height_jitter: 0.1
    lod_pixels: [650, 320, 180]
```
Same pattern for the rest: tree02 944, tree03 924, tree04 972, tree05 972, tree06 920, tree07 936, tree08 972,
tree09 984 (heights = native opaque height × DSFT scale, `../inventory.json`). Origin at the trunk base on the ground,
no `z_offset`, random yaw, not animated natively (1 frame), so no `still`; the fronds sway with `openyamm_wind`.

## Review

`review/<id>/compare.png` (sprite | LOD0 front | three-quarter | back), `review/<id>/lods.png` (every level with
triangles, mean colour, coverage), `review/<id>/closeup.png` where made (tree01, 05, 06, 07, 09),
`review/overview.png`, `review/overview_lods.png`.

## Compromises

- Crowns are fitted to each sprite's reach per height band (`crown_search.py`); the frond-length fit is clamped to
  0.9–1.1 so it never widens a crown much. tree09's fit hit the clamp: it is scaled 0.915 overall, so its trunk is a
  little shorter than the sprite's.
- The luminance spread is 55-85 % of the sprites' after the crown-heart floor (bright end and near-black end both
  shorter: the sprites' glints and black gaps are painted; here the gaps are the texture's deep-green underlay).
- tree08 changed most between LOD levels in colour (4.1/255 at one step; the others 1.3-3.5).
- The oldest fronds of the boot/crownshaft palms hang slightly less low than in the sprites (their reach is
  shortened by `length_age` to keep the crown width).
- tree05's leaflets are a stiff inverted V like the coconut fronds; a real Canary palm's leaflets rise in a V.
- Dead hanging fronds were dropped (in 3D they read as thin streaks); their atlas cell became the orange-tip frond.
- tree02's impostor covers 11 % more than its thinned LOD2 (the other LOD steps stay within 10 %).
- LOD0 budget: 2.5-3.2 k triangles (the brief's aim was ≤ ~4 k); LOD1 is about a third of LOD0, LOD2 an eighth,
  as the frond strips lose rows and the across-fold.

## Contract

glTF Y-up metres, origin at the trunk base on the ground, one node `Plant` with `openyamm_lods`
(`tools/link_static_model_lods.py`), alpha-tested strips cut where they pair into cards (`tools/cut_foliage_cards.py`;
the frond strips map trapezoids that hug the painted leaflets, so they are kept as built), COLOR_0 on every primitive.
Materials: `Bark` (opaque, single-sided, `ringbark` or `bootbark`), `Leaves` (MASK 0.5, double-sided, shared
`tropical` atlas, `openyamm_specular` 0.15 (0.06-0.1 on tree09/05/02), roughness 0.35, `openyamm_translucency` 0.35), `Impostor` (MASK, `openyamm_billboard`).
`openyamm_wind` is 0.15 m × H/12 m on every material (fronds stay on the trunk). LOD3 is a camera-facing impostor
(one quad cut to a 6-vertex outline = 4 triangles), alpha cut 0.5.

## Construction

- `scripts/palm_common.py`: atlas cells, budgets, and the species table (trunk centreline and diameters traced from
  the x2 sprites in fractions of the height; heart; frond count, length, width, elevation/droop ranges, leaflet hang
  angles, cell mix; `COCONUT` base and `BOOT` overrides).
- `scripts/make_textures.py`: `tropical` atlas 2048² (normal map 1024²): four pinnate frond cells 480×2048 (A green
  coconut, B with yellow/orange leaflet tips, C date palm, D strong orange tips) painted as ~90 lanceolate leaflets per side in
  loose groups of three, slanting toward the tip, lighter near the rachis; two petiole stalk strips (green-brown,
  golden). `tropical_env.json` stores each frond cell's painted reach along the rachis. Barks 512×1024 tileable:
  `ringbark` (uneven leaf-scar rings, vertical fissures), `bootbark` (overlapping cut leaf bases with shadowed rims).
- `scripts/palm_lib.py` `frond()`: a strip along the arched rachis; at each row the leaflets leave the rachis in a
  curved inverted V (inner half `hang_in`, outer half `hang_out` below the frond's side plane, both growing toward
  the tip), half-width = painted reach × frond width so the geometry hugs the texels; COLOR_0 darker at the hanging
  leaflet tips (`edge_shade`). LOD0 12 rows × 5 across, LOD1 7 × 3, LOD2 4 × 3.
- `scripts/build_palm.py`: Catmull-Rom trunk with a flared foot and (coconut) a cone of leaf bases at the heart;
  fronds on a golden-angle spiral, young upright and old hanging; crownshaft species grow long petioles from the
  trunk top. COLOR_0 = tint × proxy-sphere sky occlusion × sun/underside two-tone (`sun`). The frond length is fitted
  (clamped 0.9-1.1) so LOD0 reaches the binding height; any rest is a uniform scale (SCALE in the log). `calibrate_tint.py` folds the sprite/LOD0 mean colour ratio into `leaf_tint.json` (one rebuild in
  `build.sh`); `calibrate_impostor.py` the LOD0/impostor tone into `impostor_tone.json`.

## Sources and licences

All textures are generated by `scripts/make_textures.py` (numpy strokes, seeded): original work for this project, no
third-party images. Blender is the tool; its output is ours.
