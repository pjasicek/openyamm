# MM6 scan rocks (2026-10-09)

Static 3D replacements for the MM6 rock sprites `6rock03`–`6rock09`, `6rock12`–`6rock14` (images `rok3`…`rok14`),
built with the scan route of `../scripts/build_prop.py` (settings in `rocks.json`, same contract and budgets as `rock/`,
see the [top-level README](../README.md)). `rock07` and `rock14` came first (Misty Islands, Silver Cove, Castle
Ironfist, Eel Infested Waters); the other eight were added later the same day and are not bound yet.

| Sprite | Installed GLB | Sources | LOD triangles | File |
|---|---|---|---|---|
| `rok7` (rounded tan boulder, slab on top) | `assets_dev/worlds/mm6/models/mm6_deco_rock07.glb` | `namaqualand_boulder_05` ×2 | 2400 / 960 / 290 / 96 | 3.2 MB |
| `rok14` (angular wedge, dark crevice) | `assets_dev/worlds/mm6/models/mm6_deco_rock14.glb` | `boulder_01` | 2400 / 960 / 290 / 96 | 3.8 MB |
| `rok3` (long low flat grey rock) | `…/mm6_deco_rock03.glb` | `rock_09` | 2400 / 960 / 290 / 96 | 3.0 MB |
| `rok4` (big rounded sandstone, warm tan) | `…/mm6_deco_rock04.glb` | `namaqualand_boulder_03` | 2400 / 960 / 290 / 96 | 3.5 MB |
| `rok5` (sandy tan boulder, lobes at the left) | `…/mm6_deco_rock05.glb` | `namaqualand_boulder_04` ×3 | 2398 / 958 / 288 / 94 | 3.2 MB |
| `rok6` (angular brown boulder) | `…/mm6_deco_rock06.glb` | `namaqualand_boulder_06` | 2400 / 960 / 290 / 96 | 3.7 MB |
| `rok8` (rounded grey-tan boulder) | `…/mm6_deco_rock08.glb` | `namaqualand_boulder_05` | 2400 / 960 / 290 / 96 | 3.3 MB |
| `rok9` (two dark grey stones) | `…/mm6_deco_rock09.glb` | `namaqualand_boulders_01` a + b | 2400 / 960 / 290 / 96 | 3.5 MB |
| `rok12` (pale tan rounded boulder) | `…/mm6_deco_rock12.glb` | `namaqualand_boulders_01` b | 2400 / 960 / 290 / 96 | 3.2 MB |
| `rok13` (low flat grey-brown rock) | `…/mm6_deco_rock13.glb` | `boulder_01` | 2400 / 960 / 290 / 96 | 3.6 MB |

Binding heights (native sprite height × DSFT scale): 113 units (rock07), 107 units (rock14), 53 (rock03),
111 (rock04), 107 (rock05), 92 (rock06), 85 (rock08), 63 (rock09), 87 (rock12), 52 (rock13). Suggested binding for
the new eight like the existing rocks: `height_jitter: 0.15`, random yaw, `z_offset: -4` (−3 for the low rock03/rock13).

## Sources and licences

Poly Haven, CC0 (no attribution required), 2K glTF in `source/`:
- [namaqualand_boulder_05](https://polyhaven.com/a/namaqualand_boulder_05) — modelling Jenelle van Heerden,
  photography Dario Barresi.
- [boulder_01](https://polyhaven.com/a/boulder_01) — Rico Cilliers.
- [namaqualand_boulder_06](https://polyhaven.com/a/namaqualand_boulder_06) — modelling Jenelle van Heerden,
  photography Greg Zaal.
- [namaqualand_boulders_01](https://polyhaven.com/a/namaqualand_boulders_01) — modelling Jenelle van Heerden,
  photography Greg Zaal. Its two stones are split into `namaqualand_boulders_01_{a,b}_2k.gltf` (one node each,
  same `.bin` and textures) so they can be placed separately.
- [rock_09](https://polyhaven.com/a/rock_09) — Jenelle van Heerden.
- From `../rock/source/` (see the top-level README): `namaqualand_boulder_03` (modelling Jenelle van Heerden,
  photography Dario Barresi) and `namaqualand_boulder_04` (Jenelle van Heerden).

Also surveyed for the later eight (not kept): `moon_rock_01`–`07` (good silhouettes, but a flat regolith albedo,
luma std 4–8 vs 20+; a contrast boost turned their pits black and still read as plaster), `namaqualand_boulder_02`
(separate blocks rather than one boulder), `rock_07` (glossy, roughness 0.3) and `coast_rocks_05` (includes its ground
patch). Sources are reused across rocks on purpose: the MM6 sprites `rok6`/`rok13`/`rok14` share one craggy brown
texture, and the scans read as different rocks under other yaws, scales and grades.

## Build

`./build.sh [--install] [rock...]` (from this folder; no names: all ten). Per rock: `build_prop.py` → `review_render.py` at the review yaw
(rock07 315°, rock14 330°) → `review_sheet.py` → `tools/link_static_model_lods.py` → `validate_glb.py` → install.

- rock07: `namaqualand_boulder_05` scaled ×1.3 in height as the rounded base; a second copy of the same scan, centred,
  scaled 0.48 × 0.52 × 0.3, tilted 22° toward the review camera, rests on the upper front as the slab (`parts` in
  `rocks.json`). The joined scans are voxel-remeshed (6 mm) for LOD0 only, so the dome unwrap keeps one visible
  island; the bake reads both scans. Grade: saturation 0.6, gain 0.67 / 0.57 / 0.48.
- rock14: `boulder_01` ×1.2 in height; its wedge rises to the right from the 330° side with the deep crevice in front.
  Grade: saturation 0.6, gain 1.05 / 0.83 / 0.47; AO 0.8.
- Both: `ground_band` 0.12 lowers each level's base band back onto the ground (decimation lifted it 2–3 cm).
- Later eight (review yaw in `build.sh`; native sprites `../../mm6_new_sorpigal/native/rok*.png` are the legacy BMPs
  with palette index 0 transparent, `enhanced/` copies `decorations_x2`):
  - rock03 (65°): `rock_09` ×8, ×10 in height; `roughness_min` 0.8 (new optional key) removes the scan's wet sheen.
  - rock04 (300°): `namaqualand_boulder_03` ×1.35 in height.
  - rock05 (315°): `namaqualand_boulder_04` ×1.35 / 1.15 / 0.85 as the long rounded mass, plus two smaller copies
    of the same scan (`parts`) as the low lobes at its left front.
  - rock06 (300°): `namaqualand_boulder_06` ×1.25 in height; peak at the left, steep right face.
  - rock08 (150°): `namaqualand_boulder_05` ×1.4 in height (a dome; rock07 shows its other side with a slab).
  - rock09 (120°): stone a (granite) ×2.2 on the left, stone b (smooth) stretched to 0.8 m tall on the right;
    grade with luma `contrast` 1.5 (new optional grade key) and saturation 0.2 for dark grey.
  - rock12 (90°): stone b ×1.6 in height, graded pale tan.
  - rock13 (225°): `boulder_01` ×0.55 in height (low, craggy).
  - Lit mean in the review render vs enhanced sprite (all within ~6/255 except rock09's deliberate grey):
    rock03 138/115/98 vs 138/117/98, rock04 137/107/75 vs 139/109/73, rock05 139/114/84 vs 137/112/81,
    rock06 95/76/60 vs 92/77/62, rock08 132/110/85 vs 133/112/87, rock09 80/77/76 vs 82/71/62 (the sprite's mean is
    warmed by orange rim light), rock12 189/165/128 vs 191/165/127, rock13 88/72/57 vs 87/70/50.
- The two new builder keys (`grade.contrast`, `roughness_min`) are inactive when absent: a scratch rebuild of rock14
  gave identical geometry and textures within the Cycles bake noise (max 1–2 levels, same as two runs of one build);
  the installed rock07/rock14 GLBs were not rebuilt.
- Lit mean in the review render vs sprite: rock07 120/107/94 vs 116/102/88; rock14 111/95/75 vs 109/94/76.

## Review

`rock*/review/`: `sprite_compare.png` (native | enhanced | 3D LOD0), `lods.png`,
`turntable.png`.

## Compromises

- The sprites are painted with strong light-and-shadow contrast; the scans' albedo is flatter and Eevee lighting soft,
  so the crevice and the slab's shadow read weaker than in the sprites (check under engine lighting once bound).
- rock07's slab has the same granite texture as its base and is fused into it; at LOD3 it becomes a flat sheet.
  The base's own scan has a few darker patches the sprite does not show.
- rock14 keeps some rust-pink patches of the scan under the tan grade. Both are narrower from the side than from the
  review yaw.
- Later eight: none of the scans has the strong painted light-and-shadow of the sprites. rock08 lacks the sprite's
  pits (granite speckle instead); rock13 is flatter and more ragged than the sprite's hump; rock04 is blockier than
  the sprite's rounded top; rock05's lobes are separate rounded stones where the sprite's are cracked-off parts of one
  mass; rock12 keeps an orange stain on its lower front from the scan. rock03 and rock12 have narrow footprints
  (long slab / tall stone), so they read narrower from their ends under random yaw.
