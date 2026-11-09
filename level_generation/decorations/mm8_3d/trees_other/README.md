# MM8 conifers, dead and other trees in 3D (batch `trees_other`, 2026-10-15)

Static 3D replacements for twelve MM8 tree sprites: pines `tree29`, `tree30`; dead tree `tree28`; desert trees
`tree14`, `tree15`, `tree20` (Ironsand Desert out04); `tree16`, `tree19`, `tree21` (Garrote Gorge out05); `tree17`
(Murmurwoods); autumn maples `tree62c`, `tree63b` (out08). Brief: `../BRIEF.md`; plan: `../README.md`.

Status: all twelve installed and bound (2026-10-16). The six desert/gorge trees (tree14/15/16/19/20/21) were rebuilt
the same day as `sculpt` species after the coordinator's review (hand-traced skeletons, open pad crowns).

## Pipeline

Copied from the MM6 tree pipelines (`../../mm6_new_sorpigal_3d/trees/`, unchanged) and adapted in `scripts/`:

```bash
python3 scripts/make_shared.py bark needles     # shared bark + needle atlas (shared/)
python3 scripts/make_leaf_shared.py             # shared leaf atlas (shared/)
./build.sh <id> [--install]                     # conifer and clump species (species/<id>.json)
scripts/dead_build.sh tree28 [--install]        # the dead tree (scripts/dead_common.py)
```

- `common.py`: sprites are the restored x2 images (`assets_dev/engine/decorations_x2/`), heights from
  `../inventory.json` (binding height / 81.7 units per metre), kinds `conifer` | `clump`, shared atlases, COLOR_0
  tints (species target colour / the shared texture's mean). Install through `tools/install_model.py --engine`.
- **Shared textures** (`shared/`), embedded byte-identical in every GLB so the cooker (keys textures by content) stores
  them once: `bark_*` (Poly Haven bark_brown_01 graded to a neutral light brown), `needles_*` (procedural conifer
  atlas: four 512x1024 branch-spray fronds for the pines, eight 512² dense pads for tree16, four of them with
  yellow-olive fronds) and
  `leaves_*` (4x4 maple sprays from ambientCG LeafSet010/LeafSet027: cells 0-3 olive green, 4-7 orange autumn, 8-11
  red autumn, 12-13 green with autumn sprinkles, 14-15 yellow-olive). Every species' colour is in COLOR_0.
- **Conifers** (`conifer_build.py`, new): a tapered trunk, whorls of branches from the crown base to the top (spacing
  shrinking upward, elevation rising, quadratic droop with a lifted tip), each branch length fitted to the sprite's
  smoothed silhouette at its tip height. Every branch carries two crossed frond cards rolled +-roll degrees about it
  (3-segment strips that follow its curve) and secondary sprays leaving it sideways and hanging down (2-segment
  strips); the secondary count fills the LOD0 budget by branch length squared. Shading normals point out of the cone
  and up. COLOR_0 = sky visibility through the LOD0 cards x a term darker toward the trunk x per-branch jitter x
  species tint. LOD1/LOD2 keep the main cards with fewer segments plus the most important secondary sprays, grown a
  little; LOD3 is the camera-facing impostor.
- **Clump species** (`build_tree.py` and the LOD2 clump-card steps): the MM6 Sapling + clump pipeline with the shared
  leaf (or needle-pad) atlas at MM8 scale (12 m trees, 1.0-1.5 m cards, 0.2 m leaves as the sprites draw them).
  MM8 options (absent = MM6 behaviour): `crown.coverage` / `crown.local` (softer occlusion and per-clump shading, so
  large crowns are not dark balls), `crown.follow_centre` (the envelope measured from each sprite row's centre:
  lopsided crowns), `crown.centre_line` (the skeleton sheared along the trunk's path: leaning trunks; `crown.shear`
  false keeps it upright), `crown.exclude` (no foliage in a box: tree20's bare limb), `bark.clip_from` (no envelope
  clipping below this height), `bark.truncate` (branches end at their first point outside the envelope, tapered;
  detached islands dropped), `bark.sides` (tube sides by thickness), plus `impostor_dilate` / `impostor_edge_fill`.
  Nothing near the trunk line is clipped (lopsided envelopes otherwise cut box-like stubs out of the trunk).
- **Sculpted trees** (`sculpt_build.py`, kind `sculpt`: tree14/15/16/19/20/21): no generator. Each species file
  lists its trunk and limbs as centre lines traced from the sprite (`review/trace/<id>_grid.png`: x and z in
  fractions of the height from the trunk foot, radii per point, an authored depth per limb, `depth_scale` 1.8), skinned
  as Catmull-Rom tubes with parallel-transport frames, ridges that spiral along the limb (`ridges`, `ridge_amp`,
  `twist`), knots, a lobed root flare, analytic outward normals (no shading seam) and bark UVs that twist with the
  ridges. Foliage is compact, lobed card clusters (`pads`: [x, z, r], matching the sprite's pad count and positions)
  only at limb tips; a pad that no limb reaches gets a thin stem from the nearest live limb (never from a `dead`
  limb), so nothing floats and the sky shows between pads. COLOR_0: sky visibility through the cards, a pad-local
  term and tint; bark the same rays x a ridge-valley crevice term (`crevice` 0.5) x per-limb `tone` (tree20's pale dead
  limb). Bark: shared `bark2_*` (Poly Haven bark_willow_02, AO^2 x height, contrast 2.1, warm light neutral), so the
  trunks read warm and high-contrast like the sprites. `scripts/check_bark_facing.py` confirms every single-sided
  bark face faces outward (0 inverted on all LODs).
- **Re-export** (`reexport.sh <id> --install`): a built species against the current shared atlases (no renders), so
  every GLB embeds the same atlas bytes; all twelve were checked to embed the current `shared/` files.
- **Dead tree** (`dead_*.py`): the MM6 bare-wood generator with a new kind `broad` (central leader, limbs on a
  golden-angle spiral arching out to the silhouette, recursive forks to twig cards, side shoots, low sprouts, roots;
  every limb scaled to fit the silhouette and height) and buds on the procedural twig atlas.

## Installed models

Installed with `tools/install_model.py --engine` (source `assets_source/engine/models/`, cooked runtime GLB in
`assets_dev/engine/models/`, textures cooked once per content: the bark, leaf and needle atlases are shared). Each
passes `../animated/scripts/check_winding.py` (0 inverted closed parts). LOD colour Δ = the largest mean-colour step
between neighbouring levels (sRGB /255, eye camera, no shadows); coverage of LOD1 / LOD2 / LOD3 against LOD0.
Triangles: LOD0 / LOD1 / LOD2 / impostor (2 triangles, cut to 4 by `cut_foliage_cards.py`).

| Model | Sprite (placements; maps) | LOD triangles | Source / cooked GLB | LOD Δ max; coverage | Review sheet |
|---|---|---|---|---|---|
| `mm8_deco_tree29.glb` | tree29 (397; out03.odm, out07.odm) | 2980 / 1298 / 499 / 4 | 15.0 MB / 0.41 MB | 3.3; 1.04, 0.95, 1.01 | `review/tree29/sheet.png` |
| `mm8_deco_tree30.glb` | tree30 (209; out03.odm, out07.odm) | 2980 / 1298 / 499 / 4 | 15.0 MB / 0.41 MB | 3.6; 1.04, 0.93, 1.03 | `review/tree30/sheet.png` |
| `mm8_deco_tree28.glb` | tree28 (115; out06.odm, out08.odm) | 4350 / 1974 / 893 / 4 | 8.0 MB / 0.41 MB | 6.0; 0.90, 0.73, 1.07 | `review/dead_tree28/sheet.png` |
| `mm8_deco_tree62c.glb` | tree62c (72; out08.odm) | 2994 / 1296 / 496 / 4 | 14.5 MB / 0.25 MB | 3.3; 1.01, 0.98, 1.07 | `review/tree62c/sheet.png` |
| `mm8_deco_tree21.glb` | tree21 (96; out07.odm, out05.odm) | 3793 / 1395 / 495 / 4 | 14.7 MB / 0.37 MB | 2.5; 1.02, 1.05, 1.07 | `review/tree21/sheet.png` |
| `mm8_deco_tree20.glb` | tree20 (65; out05.odm, out04.odm) | 3787 / 1395 / 493 / 4 | 14.7 MB / 0.36 MB | 3.4; 1.02, 0.96, 1.05 | `review/tree20/sheet.png` |
| `mm8_deco_tree63b.glb` | tree63b (63; out08.odm) | 2990 / 1294 / 496 / 4 | 14.3 MB / 0.24 MB | 3.4; 1.06, 1.04, 1.10 | `review/tree63b/sheet.png` |
| `mm8_deco_tree17.glb` | tree17 (39; out07.odm) | 2987 / 1293 / 494 / 4 | 14.5 MB / 0.27 MB | 2.1; 1.02, 1.03, 1.10 | `review/tree17/sheet.png` |
| `mm8_deco_tree15.glb` | tree15 (30; out04.odm, out02.odm) | 3791 / 1396 / 495 / 4 | 14.8 MB / 0.40 MB | 2.6; 1.02, 0.99, 1.00 | `review/tree15/sheet.png` |
| `mm8_deco_tree16.glb` | tree16 (30; out05.odm) | 3793 / 1396 / 495 / 4 | 15.0 MB / 0.38 MB | 1.9; 1.02, 1.03, 1.02 | `review/tree16/sheet.png` |
| `mm8_deco_tree14.glb` | tree14 (24; out04.odm) | 3795 / 1395 / 493 / 4 | 14.6 MB / 0.39 MB | 3.9; 1.03, 0.98, 1.04 | `review/tree14/sheet.png` |
| `mm8_deco_tree19.glb` | tree19 (18; out05.odm) | 3798 / 1395 / 495 / 4 | 14.5 MB / 0.38 MB | 3.0; 1.00, 0.94, 1.04 | `review/tree19/sheet.png` |

Front-view mean colour, model vs sprite (sRGB): tree29 [60,67,26] / [61,68,22]; tree30 [56,65,27] / [54,64,21];
tree28 [76,65,51] / [73,61,43]; tree62c [97,55,23] / [94,56,20]; tree63b [89,32,21] / [87,37,21]; tree17 [74,86,36] /
[74,87,40]; tree19 [63,87,21] / [61,86,23]; tree21 [91,82,24] / [95,83,24]; tree14 [80,87,31] / [80,87,40]; tree15
[79,85,32] / [79,87,37]; tree20 [79,90,29] / [72,87,33]; tree16 [60,68,29] / [66,71,33].

Suggested bindings (`assets_dev/worlds/mm8/models/decorations.yml`): yaw random (the default), no z_offset, mount,
swing or free model; not `still` (`openyamm_wind` on leaves 0.12 and bark 0.03; tree28 0.05 on wood and twigs).

```yaml
- name: tree29
  model: engine/models/mm8_deco_tree29.glb
  height: 976
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree30
  model: engine/models/mm8_deco_tree30.glb
  height: 1000
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree28
  model: engine/models/mm8_deco_tree28.glb
  height: 1008
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree62c
  model: engine/models/mm8_deco_tree62c.glb
  height: 1000
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree21
  model: engine/models/mm8_deco_tree21.glb
  height: 488
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree20
  model: engine/models/mm8_deco_tree20.glb
  height: 500
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree63b
  model: engine/models/mm8_deco_tree63b.glb
  height: 956
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree17
  model: engine/models/mm8_deco_tree17.glb
  height: 1016
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree15
  model: engine/models/mm8_deco_tree15.glb
  height: 820
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree16
  model: engine/models/mm8_deco_tree16.glb
  height: 908
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree14
  model: engine/models/mm8_deco_tree14.glb
  height: 416
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
- name: tree19
  model: engine/models/mm8_deco_tree19.glb
  height: 420
  height_jitter: 0.12
  lod_pixels: [650, 320, 180]
```

## Reduction and open-crown pass (2026-10-16)

Triangles (LOD0 / LOD1 / LOD2 / impostor) before and after; gates from `scripts/reduction_gate.py` against the
previous build rendered with the same camera (`lod_check.py <id> before`): fill = opaque pixels / (tree height in
pixels)², which does not depend on the framing (the open crowns are wider, so plain pixel counts are not comparable);
LOD0 coverage change; LOD0 mean colour change (max channel, sRGB /255; it includes the deliberate sunlit-leaf lift);
largest colour step between neighbouring levels. Sheets: `review/<id>/before_after.png` (before above after).

| Id | Before | After | Fill before / after / sprite | LOD0 coverage | LOD0 colour | LOD step |
|---|---|---|---|---|---|---|
| tree29 | 4988 / 1998 / 697 / 4 | 2980 / 1298 / 499 / 4 | 0.427 / 0.429 / 0.369 | +0.007 | 0.7 | 3.3 |
| tree30 | 4996 / 1998 / 697 / 4 | 2980 / 1298 / 499 / 4 | 0.399 / 0.382 / 0.360 | -0.042 | 2.1 | 3.6 |
| tree62c | 5968 / 2378 / 696 / 4 | 2994 / 1296 / 496 / 4 | 0.561 / 0.547 / 0.525 | -0.026 | 6.3 | 3.3 |
| tree63b | 5968 / 2378 / 724 / 4 | 2990 / 1294 / 496 / 4 | 0.642 / 0.532 / 0.538 | -0.172 | 5.4 | 3.4 |
| tree17 | 5958 / 2378 / 516 / 4 | 2987 / 1293 / 494 / 4 | 0.516 / 0.442 / 0.406 | -0.143 | 6.6 | 2.1 |
| tree14 | 5991 / 2396 / 794 / 4 | 3795 / 1395 / 493 / 4 | 0.401 / 0.441 / 0.428 | +0.100 | 2.4 | 3.9 |
| tree15 | 5990 / 2394 / 796 / 4 | 3791 / 1396 / 495 / 4 | 0.288 / 0.304 / 0.261 | +0.054 | 3.7 | 2.6 |
| tree16 | 5989 / 2393 / 795 / 4 | 3793 / 1396 / 495 / 4 | 0.442 / 0.473 / 0.481 | +0.070 | 2.7 | 1.9 |
| tree19 | 5989 / 2396 / 795 / 4 | 3798 / 1395 / 495 / 4 | 0.493 / 0.602 / 0.657 | +0.221 | 1.4 | 3.0 |
| tree20 | 5992 / 2395 / 795 / 4 | 3787 / 1395 / 493 / 4 | 0.352 / 0.395 / 0.398 | +0.123 | 2.3 | 3.4 |
| tree21 | 5990 / 2394 / 791 / 4 | 3793 / 1395 / 495 / 4 | 0.358 / 0.375 / 0.357 | +0.045 | 2.3 | 2.5 |

- **Pines** (`conifer_build.py`: main cards 2/1/1 segments, sprays 25-30 % longer, `seg_main`, `spray.scale`): same
  density and colour within the gates (tree30 4 % less fill, still above the sprite's); LOD tones re-measured; leaf
  translucency 0.35 -> 0.2 and leaves 6 % darker so the firs stay dark under the engine's sun (an out07 capture read
  the previous pines lighter than the review renders; translucency is not in the Eevee review).
- **Maples tree62c, tree63b, tree17**: rebuilt as `sculpt` species (traced skeletons, `review/trace/<id>_grid.png`):
  16-17 separate leaf masses with sky and limbs between them instead of the dense clump crowns. Fill now matches
  the sprites (0.547 / 0.525, 0.532 / 0.538, 0.442 / 0.406) and so differs from the old blobs by design (-3 % / -17 %
  / -14 %); their mean colour moved 5-7 /255 against the old builds because limbs now show, while the front view
  matches the sprite (tree62c [94,57,28] / [94,56,20], tree63b [87,35,25] / [87,37,21], tree17 [76,85,43] / [74,87,40]).
- **Desert/gorge trees**: leaf cards cut by half (bark kept: the trunks carry the character), far LODs coarsen the
  bark (`SIDES_RANGE` / `RING` per LOD, sub-pixel twigs and pad stems dropped at LOD2), ragged pads (`pad_lobes` 5,
  `lobe_amp` 0.7, 10 % stray sprigs past the outline, no deep interior cards). Raggedness pushes the outline out, so
  fill rose 5-12 % against the previous builds and now matches the sprites (tree14 0.441 / 0.428, tree16 0.473 /
  0.481, tree20 0.395 / 0.398, tree21 0.375 / 0.357); tree19 rose 22 % towards its dense sprite (0.602 / 0.657).
  This misses the 3 % gate against the old models on purpose: the old pads were smoother and thinner than the sprites.
- **Sunlit leaves** (`leaves.sun`: value +7-12 %, chroma +8 % on the brightest vertices): mean shift within 4 /255 except
  where the crown itself changed (maples).
- **Bark faces**: coarse far-LOD rings can fold at sharp bends; `sculpt_build.py` flips any face whose winding
  disagrees with its outward normals (tree19 LOD2: 4 faces), and `scripts/check_bark_facing.py` reports 0 inverted on
  every LOD of every sculpt species.
- Sprites: the restored x2 images moved to `assets_legacy/decorations_x2_mm8_20261016/`; `common.py` and
  `dead_common.py` read them there.

### Pine colour pass and bark UV check (2026-10-16)

- In game (`../review/ingame/out03_pines/`) the pines read lime: crown pixels about [74,83,25] against the sprite's
  [61,68,22]. Changes: `openyamm_translucency` 0.35 -> 0.09 (the Eevee review has no translucency), needle target
  about 15 % darker and a little bluer (tree29 [138,157,25] after the darkening below, tree30 [131,152,25]), and a new
  `conifer.cone_ao` term in `conifer_build.py` {floor 0.45, power 1.4, low 0.72}: cards deep in the cone (radius from
  the trunk / envelope radius) and low on the tree darken, so lit tier edges separate from shadowed gaps as on the
  sprite. Leaf `openyamm_specular` stays 0.1. Review front view now about the sprite minus 10 %: tree29 [53,61,26]
  (sprite [61,68,22]), tree30 [51,60,26] (sprite [54,64,21]); LOD tones re-measured ([1, 0.80, 0.765], impostor 1.03),
  LOD steps 3.8 or less, triangles unchanged (2980 / 1298 / 499 / 2). Sheets `review/tree29/sheet.png`,
  `review/tree30/sheet.png`. Reinstalled.
- Bark UVs: `build_tree.py` (Sapling curves) scaled Blender's curve u (along) by the around-count and v (around) by
  the along-count, stretching the bark along every branch; fixed (u and v swapped, as in the MM7 trees_a copy). No
  installed tree of this batch uses `build_tree.py` any more (pines: `conifer_build.py`; the others `sculpt_build.py`,
  tree28 `dead_build.py`), and those three write u around and v along the limb themselves: `scripts/check_bark_uv.py`
  (tree29 |dv/dz| 0.83 = 1 / tile 1.2, |du/dz| 0.12) and close trunk renders `review/trunk_uv/sheet.png` (tree29,
  tree30, tree14, tree62c, tree28: furrows along the trunk) confirm it, so nothing needed reinstalling for it.

### Leaf overdraw pass (2026-10-16)

The out07 forest spent about half its GPU frame on stacked alpha-tested leaf cards. Gate: `scripts/overdraw.py
<glb>` rasterises the exported GLB (the cut cards the engine draws) orthographically from the front, three-quarter
and side, samples each card's texture alpha (cutoff 0.5) and counts passing fragments per covered pixel: `layers`
with no depth test, and `front` = only fragments in front of the opaque depth (bark and shells; what is left once
the engine draws opaque parts into the depth prepass first). `overdraw_summary.py <id> <glb> [tag]` averages the
views; `overdraw_sheet.py <id>` writes `review/<id>/overdraw_before_after.png` (compare sheet and LOD0/1/2 front heat
maps, blue 1 layer -> red 8+, grey = shell or bark visible with no card in front). Heat maps: `review/overdraw/`.

- **Crown shells** (material `Shell`: opaque, single-sided, closed, outward winding; white 8x8 base colour and a flat
  normal map shared byte-identical across GLBs, colour all in COLOR_0 = species leaf colour x `dark` x sky
  visibility through the cards; `openyamm_wind` = the leaves' 0.12; `openyamm_specular` 0.05; none on the impostor):
  pines a lathed cone inside the needles (`conifer.shell` {inset 0.6, dark 0.35, z1 0.88}: 160 / 80 / 36 tris), sprays
  lying wholly inside it dropped; sculpt trees one core per pad (`sculpt.shell` {inset, dark}: icosahedron 20 tris,
  octahedron 8 at LOD2) on the pad's own lobed ellipsoid - desert pads inset 0.58, dark 0.3; the open maples and tree17
  inset 0.36, dark 0.25 with interior cards kept (`pad_inner` 0.4), so a core never reads as a box through the gaps.
- **Fewer, surface-only cards** (sculpt `layers_target`: cards per pad = 2 x target x pi (1.15 r)^2 / (atlas cell
  coverage x mean card area), capped by the budget; desert `pad_inner` 0.75 puts them on the pad surface outside the
  core). Desert LOD1 budget 1250 (tree19 1450).

Results (installed; mean card layers per covered pixel over the three views, before -> after, and in brackets the
layers in front of the opaque depth; triangles LOD0 / LOD1 / LOD2 / impostor, of which shell):

| Id | Triangles | Shell tris | LOD0 layers | LOD1 layers | LOD2 layers |
|---|---|---|---|---|---|
| tree29 | 2896 / 1298 / 499 / 4 | 160 / 80 / 36 | 3.10 -> 3.01 (1.93) | 3.25 -> 3.17 (2.08) | 2.45 -> 2.29 (1.76) |
| tree30 | 2900 / 1298 / 499 / 4 | 160 / 80 / 36 | 2.88 -> 2.75 (1.86) | 3.04 -> 2.89 (1.91) | 2.28 -> 2.19 (1.63) |
| tree62c | 2974 / 1292 / 496 / 4 | 320 / 320 / 128 | 2.75 -> 2.26 (2.05) | 2.69 -> 1.83 (1.71) | 2.00 -> 1.59 (1.53) |
| tree63b | 2976 / 1290 / 496 / 4 | 340 / 340 / 136 | 2.41 -> 1.89 (1.76) | 2.55 -> 1.61 (1.54) | 1.96 -> 1.43 (1.38) |
| tree17 | 2981 / 1293 / 492 / 4 | 320 / 320 / 128 | 3.42 -> 3.15 (2.77) | 2.90 -> 2.16 (2.00) | 1.93 -> 1.76 (1.67) |
| tree14 | 2363 / 1237 / 495 / 4 | 220 / 220 / 88 | 9.34 -> 2.98 (2.56) | 5.21 -> 2.95 (2.59) | 2.39 -> 2.05 (1.94) |
| tree15 | 2461 / 1242 / 495 / 4 | 280 / 280 / 112 | 8.59 -> 3.11 (2.52) | 4.91 -> 2.68 (2.33) | 2.66 -> 2.09 (1.90) |
| tree16 | 2369 / 1246 / 493 / 4 | 220 / 220 / 88 | 10.85 -> 3.23 (2.83) | 6.03 -> 3.13 (2.76) | 2.97 -> 2.25 (2.08) |
| tree19 | 3272 / 1445 / 495 / 4 | 300 / 300 / 120 | 6.30 -> 3.75 (2.98) | 3.66 -> 2.70 (2.27) | 2.33 -> 1.82 (1.68) |
| tree20 | 2807 / 1245 / 495 / 4 | 260 / 260 / 104 | 8.12 -> 3.06 (2.57) | 4.69 -> 2.46 (2.18) | 2.23 -> 1.66 (1.57) |
| tree21 | 2685 / 1245 / 493 / 4 | 300 / 300 / 120 | 8.21 -> 2.86 (2.43) | 4.67 -> 2.19 (1.96) | 2.45 -> 1.81 (1.70) |
| tree28 | 4350 / 1974 / 893 / 4 | none (no leaves) | twigs 1.25 | 1.19 | 1.12 |

Gates against the previous installed build (fill before / after, LOD0 coverage, LOD0 colour /255, largest LOD step):

| Id | Fill before / after | LOD0 coverage | LOD0 colour | LOD step |
|---|---|---|---|---|
| tree29 | 0.429 / 0.422 | -0.016 | 2.9 | 2.7 |
| tree30 | 0.382 / 0.377 | -0.013 | 2.2 | 1.8 |
| tree62c | 0.547 / 0.520 | -0.049 | 1.8 | 3.3 |
| tree63b | 0.532 / 0.519 | -0.024 | 1.4 | 3.1 |
| tree17 | 0.442 / 0.446 | +0.009 | 0.7 | 3.7 |
| tree14 | 0.441 / 0.422 | -0.043 | 2.1 | 2.7 |
| tree15 | 0.304 / 0.284 | -0.065 | 1.4 | 3.8 |
| tree16 | 0.473 / 0.456 | -0.035 | 2.1 | 2.7 |
| tree19 | 0.602 / 0.597 | -0.008 | 1.0 | 4.0 |
| tree20 | 0.395 / 0.378 | -0.043 | 1.6 | 3.7 |
| tree21 | 0.375 / 0.363 | -0.030 | 3.2 | 2.9 |

Sprite fills for reference: tree29 0.369, tree30 0.360, tree62c 0.525, tree63b 0.538, tree17 0.406, tree14 0.428,
tree15 0.261, tree16 0.481, tree19 0.657, tree20 0.398, tree21 0.357. Coverage changes beyond 3 % (tree15 -6.5 %,
tree62c -4.9 %, tree14 / tree20 -4.3 %) leave the fill at or above the sprite's, except tree20 (0.378 vs 0.398).
tree19 stays above the layer target (3.75, 2.98 in front of the cores): its dense umbrella sprite needs the cover.

### Shell colour fix (2026-10-16)

The untextured shells (white 8x8 texture, COLOR_0 0.02-0.08) read as black crown hearts in game. Now:
- shells use `shared/<atlas>_shell.png` (`scripts/make_shell_atlas.py`: the leaf or needle atlas with only foliage
  texels kept - twig and stem strokes removed - and every other texel filled from the nearest leaf, lightly blurred),
  UV-projected into the middle of one atlas cell, opaque, with the flat normal map; COLOR_0 = the leaves' tint x pad
  tint x `dark` x (0.6 + 0.4 sky visibility) (desert 0.75, maples 0.7, tree16 0.9, pine cone 0.7), and the cards'
  own shading normals (pine `crown_normal`, pads `shading_normal`), so a core lights like the foliage around it;
- leaf vertex darkening floors at `leaves.floor` 0.18 (sculpt and conifer); the pines' needle tint dropped (tree29
  [115,131,21], tree30 [109,126,21]) so the dark-fir front view stays where the in-game pass left it (tree29
  [54,62,24], tree30 [52,61,25]);
- gate `scripts/gate_views.py <tree.blend> <prefix>`: LOD0 and LOD1 from under the crown (2 m up, at most 0.35 of the
  height, 1 m from the trunk, 60 degrees up) and a low three-quarter view, back faces culled on opaque materials, no
  shadow maps; reports the fraction of covered pixels darker than 20/255. Sheet `review/gate_views/sheet_after.png`.
COLOR_0 percentiles before / after: `work/color0_before.txt`, `work/color0_after.txt` (`scripts/color0_stats.py`).

### Pine needle atlas (2026-10-16)

In game the shell-fixed pines read lighter and more lime from the side than the approved pass (out03_pines2): the
lighter cone showed through. The pines now use their own needle atlas `shared/needles_pine_*`
(`scripts/make_pine_atlas.py`: the shared needle colour scaled per channel in linear light, [0.558, 0.592, 0.203],
blue lifted 1.25x, so the darkness lives in the texture and the COLOR_0 tint is 0.85-0.95; normals byte-identical
to the shared needle normals) and its shell copy `needles_pine_shell.png`; cone shell `dark` 0.45; needle floor 0.17.
No-shadow LOD0 mean (the in-game side view) against the approved pines2 build: tree29 [64.0,72.2,28.5] /
[63.4,71.1,30.0], tree30 [61.0,69.8,29.2] / [59.9,68.7,30.2]; needle COLOR_0 p5 0.146 / 0.135 (was 0.087 / 0.080),
shell p50 0.295 / 0.271; overdraw unchanged; LOD steps 3.0 / 2.4; low three-quarter view 0 % black, under view as the
build confirmed in game. Reinstalled.

### Pine cone shell pulled in (2026-11-08)

Close up (MM9 Frosgard, which uses both pines at 1000-1900 high, and MM8 out03) the cone shell read as a smooth olive
cone behind the needles. `conifer.shell` for tree29 and tree30: inset 0.6 -> 0.4, dark 0.45 -> 0.25 (z1 0.88 kept), so
the core reads as shade between the sprays. More sprays survive outside the smaller cone; layers in front of the opaque
depth at LOD0 / LOD1 / LOD2: tree29 1.93 / 2.08 / 1.76 -> 2.44 / 2.58 / 2.04, tree30 1.86 / 1.91 / 1.63 -> 2.27 / 2.35
/ 1.89 (target 2.5-3); triangles 2996 / 2968 at LOD0, winding 0 inverted. The shell keeps its blurred atlas cell: one
stretched cell cannot tile needle detail, and at this darkness it does not show. Remaining: looking straight up from
inside the crown shows the cone's flat side. Previous builds and species files: `work/_shell_v1_backup/`.

## Compromises

- Pines (tree29, tree30): the frond cards read as feathery sprays at game distance; the sprite's reddish tip buds
  are only a faint fringe. Contrast is a little lower than the sprite (luminance 5/50/95 33/56/102 against 11/57/121
  on tree29). The lowest sprays are clamped 1 % above the ground: the engine scales a model by its LOD0 bounds height,
  so nothing may hang below the origin.
- tree28: a generated branching system inside the sprite's silhouette, not the sprite's exact limbs; LOD2 keeps 73 %
  of LOD0's coverage at a common size (bare twigs thin out; it reads alike at its ~160 px switch size), the impostor
  is 7 % fuller. Its own bark (Poly Haven bark_willow_02) and twig textures, not the shared set.
- Maples and tree17 (open crowns since the reduction pass): masses are rounded lobed clusters; the sprites' crowns
  are more continuous at their edges, with finer gaps.
- Sculpted desert/gorge trees (tree14/15/16/19/20/21, rework 2026-10-16): skeletons follow the sprites' trunks and
  limbs in the front view; depth is authored (the sprite has none), so the side view is plausible rather than traced.
  Pads are rounded lobed clusters, slightly smoother than the sprites' ragged leaf masses; tree19's dense umbrella is
  built from 15 flattened pads, so it is more open than its sprite. The earlier light/dark bands on the lower trunks
  (Sapling tube UVs) are gone: the tubes are new geometry with continuous twisted UVs. Heights unchanged.
- Leaf colour per card comes from the shared atlas plus a COLOR_0 tint: a few bright cards clamp at COLOR_0 = 1 on
  tree14/tree17/tree20 (tints up to 1.3 against an occlusion maximum of 0.6-0.8).
- Each GLB embeds its own impostor and LOD2 clump atlas (512²); the shared atlases are stored once after cooking.

## Sources and licences

- Bark: Poly Haven [bark_brown_01](https://polyhaven.com/a/bark_brown_01) and
  [bark_willow_02](https://polyhaven.com/a/bark_willow_02) (CC0), `source/`.
- Leaves: ambientCG [LeafSet010](https://ambientcg.com/view?id=LeafSet010) and
  [LeafSet027](https://ambientcg.com/view?id=LeafSet027) (CC0), `source/`.
- Needles, fronds, twigs and buds: procedural (`make_shared.py`, `dead_prepare.py`). Sapling Tree Gen (GPL) is a
  tool; its output is ours.
