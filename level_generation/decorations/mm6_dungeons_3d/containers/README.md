# MM6 dungeon containers, trash heap, mushrooms and crystal disk (2026-10-09)

Static 3D replacements for ten MM6 dungeon decoration sprites (brief: `../BRIEF.md`). Procedural Blender modelling
traced from the restored x2 sprites (`assets_dev/engine/decorations_x2/`), procedural textures generated here and
read-only outdoor props textures; since revision 2 (2026-10-09) the three sacks use CC0 Poly Haven hessian scans
(see Textures) with the native sprites' shading and colours baked in. No paid generation. All ten sprites have one
frame, so no binding needs `still: true`.

| Model (`assets_dev/worlds/mm6/models/`) | Sprite (placements) | LOD triangles | File | Binding height |
|---|---|---|---|---|
| `mm6_deco_bag_a.glb` | `bag_a` (123) | 1500 / 600 / 250 | 4.0 MB | 47 (79 x 0.6) |
| `mm6_deco_bag01.glb` | `bag01` (74) | 1500 / 600 / 250 | 3.5 MB | 92 |
| `mm6_deco_floursac.glb` | `floursac` (65) | 1499 / 599 / 249 | 3.5 MB | 82 |
| `mm6_deco_bucket.glb` | `bucket` (28) | 1276 / 540 / 176 | 1.8 MB | 67 |
| `mm6_deco_trasheap.glb` | `trasheap` (28) | 3724 / 1454 / 447 | 6.8 MB | 138 |
| `mm6_deco_mushrm01.glb` | `mushrm01` (1) | 1336 / 516 / 106 | 1.3 MB | 106 |
| `mm6_deco_mushrm02.glb` | `mushrm02` (6) | 1016 / 316 / 106 | 0.9 MB | 87 |
| `mm6_deco_mushrm03.glb` | `mushrm03` (3) | 1464 / 596 / 106 | 1.0 MB | 79 |
| `mm6_deco_mushrm05.glb` | `mushrm05` (2) | 1352 / 472 / 152 | 1.3 MB | 88 |
| `mm6_deco_crysdisc.glb` | `crysdisc` (5) | 470 / 234 / 100 | 0.3 MB | 6 (by width, see below) |

Rebuild one model: `scripts/review.sh <build script> <prop> <x2 sprite file>` (build, review renders, sheet), then
`scripts/finish.py <prop> [--install]`. Textures: `scripts/make_textures.py`. Sprite region colours:
`scripts/measure.py`. `finish.py` is a copy of `../scripts/finish.py` with this batch's FINISH table; it refuses to
overwrite an installed GLB this batch did not install itself (`work/installed.txt`).

## Method

- Shapes are traced from the sprites' half-widths per 5 % of the content height (`measure`-style row scans).
- Colour: COLOR_0 = vertex occlusion x a per-material (trash heap: per-part) linear tint that brings the texture's
  mean to the sprite region's mean sRGB colour (`containers_lib.tint_for`), with extra per-vertex shading where the
  sprite shows it (sack bottoms and mushroom stem feet darker, brown parasol crowns darker). Review renders use a
  neutral grey ambient and white key light; each sheet labels the mean colour of the native sprite and every render.
- Matte materials (burlap, suede, rope, straw, rag, staves, end grain, crystal) carry `openyamm_specular` 0.2-0.5:
  at the dungeon sprites' dark albedo, full dielectric specular greys them visibly.
- Sacks, revision 2 (`build_sacks.py`, `compose_sacks.py`; user review: "texturing, no roughness"). One soft body of
  revolution per sack, elliptical in depth, with broad soft lumps, explicit cloth folds (a soft ridge with a crease
  along one side, running diagonally over part of the height and fading at both ends; noise creases alone closed into
  loops) and noise gathers (twisted into `bag01`'s tip, radiating from `bag_a`'s neck, crumpled under `floursac`'s
  mouth). Texture coordinates are the body's own parameters (u around, v along the profile by arc length), so the
  three LODs, collapse-decimated from one geometric body, share one unique texture set. Pipeline:
  `blender ... build_sacks.py -- <prop> bake` (a dense body with fine crumples, about 100 000 triangles, baked onto
  LOD0 in Cycles: tangent and object-space normals, occlusion with the floor, fold/height/radius data; arrays in
  `work/bake/`, removed after use) -> `python3 scripts/compose_sacks.py <prop>` -> `blender ... build_sacks.py --
  <prop> export` -> `review.py`, `sheet.py`, `finish.py --install`.
  `compose_sacks.py` applies the native shading transfer (`level_generation/creatures/NATIVE_SHADING_TRANSFER.md`,
  helpers from `claude_shared/native_shading.py`) to a static prop: per texel a score from the sprite's median
  luminance at that height, the up-facing fold normal, fold convexity, baked occlusion, the hessian weave and (for
  `bag_a`) isotropic blotches; the base colour is the sprite's own colour ramp (all opaque texels sorted by
  luminance) at the texel's area-weighted rank of that score, times a linear gain of 0.65-0.8 (the engine lights the
  model on top of the painted light). Normals: baked folds with the hessian normal map blended in (UDN). Roughness:
  the hessian roughness remapped to 0.62-0.92 (`bag_a`) or 0.7-0.98 (burlap). COLOR_0 is white (occlusion and colour
  are in the unique texture). `bag_a` is a napped pouch (fine hessian at a 0.3 m repeat, blotched); `bag01` and
  `floursac` use the open-weave hessian at 0.85 / 0.8 m repeats, much coarser than real sackcloth because the sprites'
  weave is. `bag_a`'s rope (two turns, knot, hanging end, radius 0.017 of the height) is ray-cast onto the body; its
  texture is three twisted strands coloured from the sprite's rope texels. `floursac`'s mouth is pressed flat.
- Bucket (`build_bucket.py`): tapered stave lathe, end-grain rim, inner wall, dark water below the rim, plank
  floor, three riveted hoops at the sprite's heights.
- Trash heap (`build_trasheap.py`): noise-lumped elliptical straw mound (1.86 x the height across, 1.1 deep), with
  the sprite's debris each rested on the mound where the sprite shows it: broken barrel tipped back (staves
  missing), split orange half keg, conical riveted iron pot, loose hoop, tipped grey crate with brass corners, a
  bundle of red-brown boards, rusty block and plate, clinker rocks, charred log, rusty pot shell, brass bone, hammer,
  pewter spoon, rags and pottery shards. Each part has its own tint in a temporary `Tint` attribute, multiplied into
  COLOR_0 after the heap's occlusion, so eleven materials cover all the coloured parts.
- Mushrooms (`build_mushrooms.py`): caps are bodies of revolution with a slightly waved rim (top skin and a
  separate downward-facing gill or skin underside), stems tubes swept along curved paths with a radius profile
  (foot bulb, ring swelling), `mushrm01`/`mushrm03` a ring skirt.
- Crystal disk (`build_crysdisc.py`): thin violet-grey rim lathe holding a flat-shaded faceted crystal dome (convex
  hull of turned facet rings).

## Textures

Sacks (revision 2): `textures/<prop>_{basecolor,normal,mr}.png` (1024, mr 512) and `bag_a_rope_*` (512), written by
`compose_sacks.py` from CC0 Poly Haven textures by Rico Cilliers (processing) and colormass (photography):
[Hessian 230](https://polyhaven.com/a/hessian_230) (`bag01`, `floursac`) and
[Hessian 380](https://polyhaven.com/a/hessian_380) (`bag_a`), 1k diffuse, OpenGL normal and roughness, stored as
8-bit copies in `textures/polyhaven/` (licence CC0, https://polyhaven.com/license). Colours come from the native
sprites only (the hessian contributes luminance, normal and roughness).

Other models (`textures/`, generated by `scripts/make_textures.py`, procedural, no external sources):

burlap, suede, rope, straw, rust, rag, crockery, capbrown, caporange, capred, gills, stem, crystal, staves,
endgrain. Read-only outdoor props textures (`../../mm6_new_sorpigal_3d/props/textures/`, also procedural): hoop,
water, wood, iron, granite, logs, bone, pewter.

## Compromises

- `crysdisc`: the sprite (40 x 15) is a high view of a flat disc. Bound at the sprite's 15 units it would be about
  97 units across; the model is built to its true shape (40 across, 6.2 high), so bind it by width: height 6.
- Sacks: the painted light is baked from above and from the folds only (rotation invariant), so the sprites' strong
  key light from the upper left is not reproduced; the engine lights the folds through the normal maps on top.
  Placements of the same sack look alike (one unique texture). The files are larger (3.5-4 MB: a unique 1024
  base colour and normal map each); `floursac` from the side is a narrow wedge (mouth pressed shut). LOD1/LOD2 reuse
  LOD0's normal map (baked against LOD0), slightly off on their coarser silhouettes.
- Before/after in the gallery (studio light, LOD0 three-quarter): `review/gallery_before/dungeon_<prop>_side.png`,
  `review/gallery_after/dungeon_<prop>_{side,model}.png`; Blender sheets `review/<prop>/sheet.png`.
- Trash heap: a dome of straw with fewer, larger items than the sprite's dense clutter, and a lighter, more uniform
  mound; the sprite's small sword hilt is omitted. The file is the largest (6.8 MB) because eleven materials each
  embed three 512 x 512 maps; LOD1/LOD2 drop the hoop, bone, hammer, spoon, rags and shards.
- Mushrooms: feet are smooth bulbs, not the sprites' ragged volvas and rootlets; caps are slightly glossy procedural
  skins, not photographic. `mushrm05`'s stems are smooth rather than gnarled.
- Bucket hoops are plain dark bands with faint rivets; the sprite's studded highlights are softer here.
