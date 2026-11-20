# MM7 scan rocks (2026-10-15/16)

Static 3D replacements for the eight MM7 rock sprites (509 placements, 503 outdoors). They are built from Poly Haven
CC0 scans with the MM6 scan-rock route (`../../mm6_new_sorpigal_3d/scripts/build_prop.py`, decimate mode), adapted in
`scripts/build_rock.py`. Settings are in `rocks.json`. All eight are installed as engine models.

| Sprite (placements) | Installed GLB | Scans | View (yaw / elev.) | LOD triangles | File |
|---|---|---|---|---|---|
| 7rock09 (135), three brown blocks | `engine/models/mm7_deco_7rock09.glb` | `nb03` slab and block, `nb04` rounded stone | 0° / 15° | 900 / 420 / 220 / 110 | 3.8 MB |
| 7rock08 (123), dark grey crag | `engine/models/mm7_deco_7rock08.glb` | Meshy multi-image-to-3D from Codex HD masters (`rock08_meshy/`) | 290° / 20° | 900 / 400 / 180 / 90 | 2.8 MB |
| 7rock01 (92), wedge block | `engine/models/mm7_deco_7rock01.glb` | `nb03` | 105° / 20° | 900 / 400 / 180 / 90 | 3.6 MB |
| 7rock02 (37), big rounded boulder | `engine/models/mm7_deco_7rock02.glb` | `nb05`, mirrored | 105° / 10° | 900 / 400 / 180 / 90 | 3.3 MB |
| 7rock03 (37), low rounded block | `engine/models/mm7_deco_7rock03.glb` | `nb06`, mirrored | 165° / 10° | 898 / 400 / 180 / 90 | 3.7 MB |
| 7rock05 (32), rounded block | `engine/models/mm7_deco_7rock05.glb` | `nb06` | 15° / 10° | 898 / 400 / 180 / 90 | 3.7 MB |
| 7rock04 (30), tall rounded block | `engine/models/mm7_deco_7rock04.glb` | `nb04` | 210° / 10° | 900 / 400 / 180 / 90 | 3.3 MB |
| 7rock07 (23), leaning slab | `engine/models/mm7_deco_7rock07.glb` | `nr_d`, mirrored, tilted 20° | 20° / 15° | 898 / 400 / 180 / 90 | 3.5 MB |

"View" is the side and camera elevation from which the model reads like the sprite (the review yaw; the camera sits
at `(sin yaw, -cos yaw)` in Blender, as in `../../mm6_new_sorpigal_3d/scripts/deco_common.py`). Placements use
random yaw.

Sizes are the installed sources in `assets_source/engine/models/`; the desktop runtime copies in `assets_dev` are
cooked, at about 60–70 KB each plus cooked textures. Each model has three 1024² textures: base colour, normal and
metal-roughness. Review sheets (x2 sprite | LOD0 at the sprite's view | turntable +90/180/270 | LOD1–3) are in
`review/<rock>_review.png`, with all eight in `review/all_rocks.png`.

Bindings (engine content since 2026-10-16: `assets_dev/engine/models/decorations.yml`, and `indoor_decorations.yml`
for 7rock03/05; heights are the inventory `art_height`). As bound, except 7rock08's suggested -4:

```yaml
  - {name: 7rock09, model: engine/models/mm7_deco_7rock09.glb, height: 66, height_jitter: 0.15, z_offset: -3}
  - {name: 7rock08, model: engine/models/mm7_deco_7rock08.glb, height: 93, height_jitter: 0.15, z_offset: -4}
  - {name: 7rock01, model: engine/models/mm7_deco_7rock01.glb, height: 100, height_jitter: 0.15, z_offset: -4}
  - {name: 7rock02, model: engine/models/mm7_deco_7rock02.glb, height: 128, height_jitter: 0.15, z_offset: -4}
  - {name: 7rock03, model: engine/models/mm7_deco_7rock03.glb, height: 88, height_jitter: 0.15, z_offset: -4}
  - {name: 7rock05, model: engine/models/mm7_deco_7rock05.glb, height: 120, height_jitter: 0.15, z_offset: -4}
  - {name: 7rock04, model: engine/models/mm7_deco_7rock04.glb, height: 116, height_jitter: 0.15, z_offset: -4}
  - {name: 7rock07, model: engine/models/mm7_deco_7rock07.glb, height: 177, height_jitter: 0.15, z_offset: -14}
```

The binding defaults apply to everything left out: random yaw, ground mount, default `lod_pixels`. No swing.
All eight sprites have one frame, so `still` is not needed.

`z_offset` is in world units; `game/maps/DecorationModelSet.cpp` parses it, and the MM6 rocks use -4. 7rock07 leans,
so it rests on a narrow edge: only about 1.0 × 1.6 m of its 3.3 × 2.5 m footprint lies within 8 % of the ground.
-14 units sinks it by that 8 %. 7rock08 is bound at -6 for the old scan composite's lifted base. The Meshy crag stands
flat over its whole footprint, so -4 would match the others; -6 only sinks it 2 units more.

7rock03 (4) and 7rock05 (2) are also placed in the dungeon `7d29.blv`. For `indoor_decorations.yml`, the same
models can be bound with the same heights. Their albedo is graded for the outdoor sun, though, and is not tinted down
for dungeon light. That is a compromise for 6 placements.

## Sources and licences

7rock08 is not a scan; it comes from our own paid generations (see "Quality pass" below). The others are Poly
Haven, CC0 (no attribution required), 2K glTF:
- [namaqualand_boulder_03](https://polyhaven.com/a/namaqualand_boulder_03) (`nb03`), modelling Jenelle van Heerden,
  photography Dario Barresi.
- [namaqualand_boulder_04](https://polyhaven.com/a/namaqualand_boulder_04) (`nb04`), Jenelle van Heerden.
- [namaqualand_boulder_05](https://polyhaven.com/a/namaqualand_boulder_05) (`nb05`), modelling Jenelle van Heerden,
  photography Dario Barresi.
- [namaqualand_boulder_06](https://polyhaven.com/a/namaqualand_boulder_06) (`nb06`), modelling Jenelle van Heerden,
  photography Greg Zaal.
- [namaqualand_rocks_01](https://polyhaven.com/a/namaqualand_rocks_01) (piece d, for 7rock07), Jenelle van Heerden
  and Greg Zaal. Its piece c and [namaqualand_stones_01](https://polyhaven.com/a/namaqualand_stones_01) pieces b/c
  were the old 7rock08 composite.

The four `nb*` scans are read in place from the MM6 pipeline (`../../mm6_new_sorpigal_3d/rock*/source/`, read only).
The others are in `source/`, downloaded with `scripts/fetch_scans.py`. Also surveyed but not used:
namaqualand_boulder_02 (shredded into dozens of loose shards), namaqualand_boulders_01, boulder_01, rock_07, rock_09,
stone_01, rock_moss_set_01 (no ARM map), namaqualand_rocks_01 a/b and moon_rock_01–07.

## Choice

- **Survey.** `scripts/survey.py` renders every candidate silhouette from 24 yaws at 10° and 20° elevation.
  `scripts/score_survey.py` scores each against the sprite's alpha, mirrored views too, by IoU minus the contour
  difference (`work/score_*.png`). Rounded boulders all score about 0.9 IoU, so the final picks were made from shaded
  views beside each sprite (`scripts/views.py`, `scripts/compare_sheet.py`, `work/cmp_*.png`), weighing:
  - the silhouette features: the peak side, a level top, a leaning slab;
  - the texture character: the sprites share one pinkish granite with ochre streaks and foliation, close to the
    Namaqualand boulders.
- **Footprints.** Long scans were squashed (`scale`) so that random yaw never shows a much longer rock than the
  sprite: 7rock02 x 0.65, 7rock03 y 0.7, 7rock05 y 0.7.
- **7rock07** is `nr_d` (a small banded stone) mirrored and tilted 20° about y (`rotation_deg`). It is widened after
  the tilt (`post_scale [1.4, 1.25, 1]`) to the sprite's chunky slab, with its peak at the upper left and diagonal
  banding.
- **7rock09** is a cluster of three scans (`parts`, not fused):
  - `nb03` stood on end, as the tall left slab, thickened (`post_scale` y 1.7);
  - a smaller upright `nb03` block at the top right;
  - a flattened `nb04` stone at the bottom right.
- **7rock08** (since 2026-10-16) is a Meshy model of one crag with two crests and a hollow; see "Quality pass".
  The two scan composites before it are kept as settings only:
  - `work/7rock08/rocks_scan_composite.json`: an `nr_c` base with `ns_b`/`ns_c` horns, installed until 2026-10-16;
  - `work/7rock08/rocks_moon2_base.json`: a `moon2` base with `moon5` horns, closer in form but reading as plaster.

## Colour

The sprites are painted with strong light and shadow (luma p10/p90 of about 32/174). Eevee review light is soft
(56/126), so matching the overall mean left the lit faces dull orange instead of pale pinkish-tan. The grade is
therefore calibrated on the lit-face colour: the mean of the pixels above the median luma, in the LOD0 render at the
sprite's view. `review_sheet.py --calibrate` scales the linear gain by sprite / render, then `build_rock.py --regrade`
re-grades from the stored raw bakes. After 2–3 passes all eight are within 1/255 (blue within 3/255).

Lit-face colour, sprite = render: 7rock01 158/131/104, 7rock02 168/134/106, 7rock03 123/98/80, 7rock05 155/123/99,
7rock07 148/122/103, 7rock09 133/96/60.

7rock04 and 7rock08 are calibrated `mid` instead: on the midpoint of the overall mean and the lit-face colour, which
gives a darker result. 7rock04 matches 138/115/94 and 7rock08 84/83/74. Both read too pale or flat with the lit
calibration (7rock04 in game).

The grade, applied in this order:
- AO folded in (0.6–0.7);
- luma contrast 1.2–1.8 about the mean, so the texture shows;
- 7rock04 only: `tint_mix` 0.8, which replaces 80 % of each texel's colour by its luma times the rock's mean tint;
  this removes the orange lichen face and keeps the light-dark texture;
- a luma cap: 1.8 × the mean on 7rock04 (its pale lichen cap) and 1.7 × on 7rock08 (white veins);
- saturation: 1.0 for the boulders, 0.85 for 7rock09, 0.35 for the crag;
- the calibrated linear gain.

COLOR_0 darkens each model toward its base (`base_shade` 0.65, smoothstep over the lower 35 % of its height), like
the sprites' dark undersides.

## Build

```bash
cd level_generation/decorations/mm7_3d/rocks
./build.sh [--install] [--regrade] [rock...]     # no names: all eight
# colour calibration pass (repeat 2-3 times):
(cd scripts && python3 review_sheet.py 7rock07 --calibrate) && ./build.sh --regrade 7rock07
# composite layout check before a bake:
(cd scripts && blender --background --python build_rock.py -- 7rock09 --preview)   # work/7rock09/preview.png
```

`build.sh` runs `build_rock.py`, then `review_render.py` and `review_sheet.py`, then
`tools/link_static_model_lods.py` and `validate_glb.py`. With `--install` it also runs
`tools/install_model.py --engine --name mm7_deco_<rock>.glb`.

Set `ROCK_BAKE_CPU=1` to bake on the CPU. The builder also chooses the CPU by itself when less than 3 GiB of GPU
memory is free: the GPU is shared, and a failed CUDA context cannot be retried in the same Blender run. Blender runs
with `--python-exit-code 1`, so a failed bake stops the chain.

What `build_rock.py` adds to the MM6 builder:
- picking a set piece by its node, and `mirror`;
- `rotation_deg` and `post_scale` (scaling after the tilt);
- `height_m` (the art height in metres);
- `fuse: false`: unfused parts with a dome seam per piece, so collapses never smear across stones;
- `sink`: a flat ground cut of LOD0 (unused; see below);
- grade `luma_cap`;
- COLOR_0;
- raw bakes stored as `.npy`, for `--regrade`;
- `--preview`.

## Quality pass (2026-10-16)

The user asked for improvements and a triangle reduction, after in-game captures in
`output/mm7_deco_outdoor_20261016/`. Meshy and Codex were allowed for this pass.

- **7rock08: Meshy route.**
  - Two Codex runs from the native bitmap `7rock08.bmp` (enlarged 3x on magenta) and the x2 frame (surface only)
    gave five HD masters, 1536 × 1024 (`codex exec`, model_reasoning_effort=medium). The brief, records and images
    are in `rock08_meshy/references_hd/`; the contact sheet is `review/7rock08_hd_references.png`.
    - Run 1: the primary `00_three_quarter`, gated against the sprite.
    - Run 2: 01–04, with the primary as input.
  - One Meshy job, `crag_multiview_v1`: multi-image-to-3D, `meshy-7.1`, textured PBR 2k, no remesh, from 00/03/02/04.
    Task 01a14360-b281-7305-af6c-33180fb64741, 30 credits (budget 60). The receipt is in
    `rock08_meshy/meshy_progress.json`, the request in `rock08_meshy/requests/`, the outputs in `rock08_meshy/meshy/`.
  - The Meshy mesh (227k triangles) is the high mesh for the usual decimation, dome unwrap (one piece, 79 underside
    faces), 1024 bake and grade.
  - `build_rock.py` now reads a model without Poly Haven map names by its BSDF links: base colour and
    metallic-roughness, with AO baking white (`ao_strength` 0).
  - Its best silhouette survey score is 0.94 IoU, against 0.91 for the best scan. It is viewed from yaw 290.
  - The geometry and textures are paid generations on the project's Meshy account, under Meshy's terms, driven by
    Codex images derived from the original MM7 sprite. No third-party assets were used.
- **7rock04: re-grade.** `tint_mix` 0.8 removes the orange lichen face (turntable +180), and `mid` calibration
  removes the paleness. The before sheet is `review/before/7rock04_review_v1.png`.
- **Reduction.**
  - LOD0 went from 1200 to 900 triangles on all eight. The chains are 900 / 400 / 180 / 90, and 900 / 420 / 220 / 110
    for the 7rock09 cluster; they were 1200 / 480 / 200 / 96 and 1200 / 500 / 260 / 120.
  - `scripts/compare_lods.py` compared the renders with the 1200 builds. LOD0 at the sprite's view and the three
    turntable views: silhouette IoU 0.987–0.994, mean luma difference 2.8–6.4/255. LOD3 at 90 triangles: IoU
    0.95–0.975.
  - All read the same. The sheets are in `review/before/<rock>_review_1200.png` and
    `<rock>_compare_1200_vs_900.png` (1200 row above the 900 row).
- **Fixes.**
  - The ground band (copied from MM6) only reached the ground when a level's lowest point was near 0. It now maps the
    lowest vertex to 0 exactly; 7rock02's LOD3 floated 5 cm before the fix.
  - The x2 reference sprites moved to `assets_legacy/decorations_x2_20261016/`.
  - All eight pass `../../mm8_3d/animated/scripts/check_winding.py` with 0 inverted parts.

## Compromises

- As with the MM6 rocks, no scan has the sprites' painted contrast. In the review light the shadow sides read lighter
  and the shapes rounder than in the sprites. Check them under engine lighting once bound.
- Scans are reused across sprites: `nb06` for 7rock03 and 7rock05, `nb03` for 7rock01 and 7rock09, `nb04` for
  7rock04 and 7rock09. The MM6 rocks use some of the same scans too. Each reuse has its own yaw, scale and grade.
- 7rock01 is blockier than the sprite's rounded wedge, and keeps the scan's dark lichen patch on top.
- 7rock02 keeps darker scan patches on its lower half (contrast lowered to 1.2 for it). It lacks the sprite's knob on
  top.
- 7rock04 is a more uniform tan than the sprite, which has ochre streaks (the cost of `tint_mix`).
- 7rock09:
  - its shaded faces are more maroon than the sprite's brown (the `nb03` scan's dark faces);
  - its three stones interpenetrate, so hidden contact faces cost some of the triangles.
- 7rock08 (Meshy):
  - its texture is softer than a scan's, and taupe-grey where the sprite is charcoal;
  - its crests and hollow are shallower than the sprite's painted ones;
  - at LOD2/LOD3 the hollow becomes a dark smeared patch, which is used below 200 px;
  - its footprint (1.7 × 1.8 m at 1.14 m height) is a little wider than the sprite.
- 7rock07 rests on an edge and needs its `z_offset`. Two attempts to flatten it in the model both smeared the texture
  and were dropped:
  - a flat ground cut (`sink`): the cap collapsed to a short dome seam;
  - a voxel remesh.
- 7rock03 and 7rock05 in `7d29.blv` would use outdoor-graded albedo; see the bindings above.
