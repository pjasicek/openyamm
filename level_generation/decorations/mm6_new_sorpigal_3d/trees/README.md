# New Sorpigal 3D trees — species pipeline (2026-10-08)

One species-configured pipeline for every New Sorpigal tree sprite, generalized from the user-approved 6tree01 v2
(`../tree01/` keeps that history). [Overview: every sprite next to its 3D LOD0](review/overview.png).

```bash
./build.sh <id> [--install]      # e.g. ./build.sh 6tree02 --install; species run independently, in parallel
```

`species/<id>.json` lists only what differs from the approved 6tree01 values (`DEFAULTS` in `scripts/common.py`):
Sapling settings and seed, tree height (world height ÷ 81.7 units/m, so leaves keep their real scale), crown start and
centre, clump count/radius/gap and card size, leaf colour/jitter/value (and blossoms), bark colour/budgets/roots,
occlusion curve, LOD budgets, card growth, per-LOD tone (scalar or per channel), LOD2 card scale, impostor tone and
dilation, fruit. Work files go to `work/<id>/`, review sheets to `review/<id>/`.

Steps (`build.sh`): `prepare.py` (crown envelope traced from the sprite, bark maps graded to the species' trunk) →
`make_leaf_atlas.py` → `build_tree.py` (Sapling skeleton, clumps, cards, sky-ray occlusion in COLOR_0, LOD subsets) →
`clump_cards.py` + `make_clump_atlas.py` + `clump_lod2.py` (LOD2 clump cards) → [`copy_base.py`, `add_fruit.py`] →
`bake_impostor.py` + `finish_impostor.py` → `export_tree.py` → `post_process.py` (materials, LOD link, validation,
install) → `review.py` (`compare.png`, `occlusion.png`) → `lod_check.py` (`lod_consistency.png`, `work/<id>/lc_stats.json`).
`render_review.py` also has an `under` view (below the crown, looking up).

## Changes against tree01 v2

- **Dark stars fixed** in the leaf-spray atlas: twigs start 30 % out from the hub, thinner and olive-brown, and five
  leaves cross the hub (their own rng: the rest of each spray is unchanged; per-cell coverage identical to 3
  decimals). [Below the crown, old | new](review/6tree01/under_old_vs_new.png).
- **LOD2 groups**: four clump cards per group within the LOD2 budget; a crown that fits keeps one group per clump
  (6tree01 rebuilds bit-identically); otherwise hidden inner clumps go first and the nearest groups merge, each card
  showing a render of its own group (leaf scale unchanged). Used by 6tree02 (164 clumps → 107 groups).
- Small trees: the Sapling `scaleV` must stay below `scale` (Sapling crashes on a negative radius); a finer trunk
  (`curveRes[0]` 16, 6tree04) lets the trunk split near the ground and keeps its ring spacing.

## Species

| Id | Placements | Output | LOD triangles | Max Δ colour / coverage between neighbouring LODs | File |
|---|---:|---|---|---|---:|
| 6tree01 | 213 | `mm6_deco_tree01.glb` | 7957 / 2980 / 860 / 2 | 2.0 / 2.8 % | 11.4 MB |
| 6tree02 | 103 | `mm6_deco_tree02.glb` | 7971 / 2956 / 988 / 2 | 2.3 / 4.0 % | 11.6 MB |
| 6tree19 | 18 | `mm6_deco_tree19.glb` | 5957 / 2380 / 476 / 2 | 4.1 / 4.1 % | 11.3 MB |
| 6tree05 | 16 | `mm6_deco_tree05.glb` | 7953 / 2980 / 852 / 2 | 2.5 / 1.6 % | 11.5 MB |
| 6tree03 | 13 | `mm6_deco_tree03.glb` | 5955 / 2378 / 572 / 2 | 4.0 / 4.9 % | 11.4 MB |
| 6tree04 | 8 | `mm6_deco_tree04.glb` | 7953 / 2980 / 972 / 2 | 2.1 / 4.4 % | 11.8 MB |
| 6tree06 | 6 | `mm6_deco_tree06.glb` | 7367 / 2730 / 816 / 2 | 3.2 / 2.1 % | 11.0 MB |
| tree06a | 9 | `mm6_deco_tree06a.glb` | 7911 / 2922 / 880 / 2 | 3.3 / 2.2 % | 11.0 MB |
| 6tree10 | (other maps) | `mm6_deco_tree10.glb` | 7959 / 2980 / 900 / 2 | 1.6 / 5.2 % | 10.0 MB |
| 6tree15 | (other maps) | `mm6_deco_tree15.glb` | 7957 / 2976 / 796 / 2 | 3.1 / 2.1 % | 10.2 MB |
| 6tree25 | (other maps) | `mm6_deco_tree25.glb` | 5968 / 2380 / 884 / 2 | 2.2 / 2.7 % | 9.9 MB |
| swptree1 | (other maps) | `mm6_deco_swptree1.glb` | 6955 / 2680 / 862 / 2 | 1.9 / 6.0 % | 9.8 MB |
| swptree3 | (other maps) | `mm6_deco_swptree3.glb` | 8956 / 3374 / 930 / 2 | 2.4 / 5.9 % | 10.7 MB |
| 6tree17 | (other maps) | `mm6_deco_tree17.glb` | 7950 / 2978 / 584 / 2 | 1.9 / 4.7 % | 10.5 MB |
| 6tree18 | (other maps) | `mm6_deco_tree18.glb` | 5964 / 2380 / 888 / 2 | 1.4 / 5.7 % | 9.5 MB |
| 6tree13 | (other maps) | `mm6_deco_tree13.glb` | 7961 / 2976 / 986 / 2 | 2.7 / 3.6 % | 10.1 MB |
| 6tree14 | (other maps) | `mm6_deco_tree14.glb` | 7961 / 2980 / 988 / 2 | 3.1 / 1.1 % | 10.2 MB |
| 6tree07 | (other maps) | `mm6_deco_tree07.glb` | 5954 / 2380 / 876 / 2 | 3.8 / 7.2 % | 10.0 MB |
| cac25 | (other maps) | `mm6_deco_cac25.glb` | 2555 / 1480 / 464 / 2 | 0.4 / 11.1 % | 8.7 MB |
| swptree2 | (other maps) | `mm6_deco_swptree2.glb` | 7962 / 2970 / 984 / 2 | 1.2 / 8.6 % | 9.8 MB |
| snotre01 | (other maps) | `mm6_deco_snotre01.glb` | 5958 / 2380 / 888 / 2 | 1.8 / 1.9 % | 9.6 MB |
| snotre03 | (other maps) | `mm6_deco_snotre03.glb` | 5962 / 2380 / 568 / 2 | 1.7 / 7.1 % | 9.7 MB |
| snotre05 | (other maps) | `mm6_deco_snotre05.glb` | 5946 / 2370 / 888 / 2 | 1.7 / 10.5 % | 9.6 MB |

Colour Δ in sRGB /255 (Eevee, no shadow maps, the engine default); review sheets `review/<id>/compare.png`,
`lod_consistency.png`, `occlusion.png`.

- **6tree02**: tall dense rounded crown from 17 % of the height, sage green with pale highlights, short thick trunk.
- **6tree19**: single trunk splitting into a few long limbs under a wide crown; limbs below the crown are clipped
  to its footprint (`clip_below_crown`).
- **6tree05**: oval crown, lighter yellow-green, single trunk.
- **6tree03**: crimson crown (`leaves.target_srgb` [235, 38, 20]) on one thick trunk.
- **6tree04**: blossom sprays (procedural five-petal flowers over dark crimson leaves), multi-stem.
- **Food tree**: `tree06a` (fruit) has `"base": "6tree06"` — it copies 6tree06's built tree and adds 34 / 24 / 16
  fruit (round 16-triangle balls / octahedra / tetrahedra, 7.5 cm radius, material Fruit, same wind as the leaves).
  Every non-fruit vertex attribute (positions, normals, COLOR_0, UVs) is byte-identical to 6tree06; only the fruit
  (and the impostor's baked texture) differ. Rebuild `6tree06` before `tree06a`.

- **6tree10** (2026-10-09): dense oblong crown reaching low, short dark reddish trunk.
- **6tree15**: tall oval crown on a long, straight, single grey-brown trunk (`clip_below_crown`, no low splits).
- **6tree25**: narrow, ragged, pointed blue-green crown from ~20 % of the height, widest low and tapering to a spire
  (`crown.radius_by_width`, `crown.spire`, `crown.lobes`), on a slim trunk forking low into leaders, no root spurs.
- **swptree1** (swamp cypress): green mossy trunk, four thin, wide, separated foliage pads (`crown.tiers`, `crown.flatten`,
  upward-facing cards `crown.card_up`) with trunk and limbs visible between them, and fine dark grey-green moss strands
  with ragged ends hanging under each pad (`crown.moss`: material `Moss`, procedural texture `moss_basecolor.png`,
  `fibres` / `fibre_width` / `fringe`).
- **swptree3** (banyan): broad crown on curving limbs, prop roots dropping from the limbs into the ground
  (`bark.aerial_roots`), large surface roots, some moss; a larger budget (9000 / 3400 / 1100).

- **Living trees, other MM6 maps (2026-10-09)**, `review/<id>/sheet.png` (sprite | LOD0 front | three-quarter | back,
  then the LOD sheet):
  - **6tree17**: autumn broadleaf, round crown in tan, peach, russet and olive patches over dark green (one leaf
    palette per atlas cell, so whole cards form colour patches), single grey-brown trunk.
  - **6tree18**: dark dense conifer-like tree: procedural needle branchlets (`kind: needles`), grey-green; ~170 small
    clumps (0.12-0.2 m, `radius_by_width`, ragged `lobes`) from 13 % of the height, so the crown is irregular, widest
    in the lower middle with a narrower rounded top and limbs showing in gaps, on a straight slim leader.
  - **6tree13**: dense round deep-green crown on a short trunk forking low into four stems.
  - **6tree14**: dense broadleaf with a triangular crown from a fifth of the height: `radius_by_width` 0.3 (clumps
    and cards shrink with the envelope's width, so the sides stay straight and the top pointed), `crown.spire`, larger
    base cards (0.5-0.62 m) to keep the crown dense.
  - **6tree07**: wide flat-topped crown on a short trunk forking into a few limbs (flattened clumps, lobes).
  - **cac25**: desert tree with distinct foliage pads: rosette cells of long narrow leaves (`kind: rosette`), large
    cards on small, widely spaced clumps (cheap: 2.6k LOD0), thick leaning trunk; LOD2 clump renders use a wider
    frame (`lod.clump_frame` 6).
  - **swptree2**: tall slim swamp cypress, swptree1's settings with six tiers in the upper 60 %, more and longer moss
    and a buttressed base (ten tall thin root spurs, `bark.root_rise` / `bark.root_radius`).
  - **snotre01 / snotre03 / snotre05**: snow spruces/firs built as tiered branch shelves around a straight trunk:
    flat pads (`crown.tiers` 8 / 5 / 11 bands, `flatten` 0.35-0.5, `card_up` 0.6-0.7, `radius_by_width`, `spire`)
    inside the sprite's narrow conical envelope, horizontal slightly drooping Sapling limbs. Needle branchlets with
    snow (`leaves.snow`): the snow atlas cells carry lumpy domed snow clumps; cards facing up (`up`: 0.55 / 0.2 /
    0.4, so the pads' upper faces) use them, turned further up (`tilt`) with their occlusion lifted toward white
    (`lift`, also in the LOD2 clump renders and their sky term), the rest are dark needles. snotre03 is the
    heavily laden one (snow on nearly every upper card, lift 0.88).
  - All ten use `transparent_bounces` 64 in the impostor and clump-card renders (dense or large cutout cards
    otherwise render black where Cycles runs out of transparent bounces: the dark rim seen on earlier impostors).

Optional species features (2026-10-09; absent = the approved behaviour, 6tree19 rebuilds bit-identically):
`crown.tiers` [[lo, hi], ...] (clump centres only in these height bands), `crown.flatten` (clumps squashed
vertically), `crown.moss` {strands, length, width, srgb, seed} (hanging strand cards; LOD1 keeps 60 %, LOD2 35 %, the
longest first; LOD2 clump cards keep them), `bark.aerial_roots` {count, z, reach, radius, seed} (part of the bark and
its budget), `crown.radius_by_width` (clump and card size follow the envelope width), `crown.spire`, `crown.lobes`
{fraction, slack} (clumps allowed past the envelope), `crown.card_up`. `clump_cards.py` counts every non-leaf face (bark and moss) against the LOD2 budget.
Later additions (living trees; 6tree19 and swptree1 still rebuild bit-identically): `leaves.palette` (per leaf, or a
list per atlas cell), `leaves.kind` `needles` (`leaves.needles` {length, width, spacing, twiglets}) and `rosette`
(`leaves.rosette` {count, length, width}), `leaves.snow` {cells, cover, radius, srgb, up, tilt, lift},
`bark.root_radius`, `bark.root_rise`, `lod.clump_frame`, `impostor_edge_fill` (grown impostor rim takes the nearest
original texel colour) and `transparent_bounces`.

## Bark UV fix (2026-10-16)

`build_tree.py` scaled Blender's curve UVs the wrong way round. Blender's u runs along the curve and v around the
bevel, but the old code multiplied u by the tiles around and v by the tiles along. Every Sapling tube therefore
tiled its bark `along` times around the branch and only `around` times along it. The furrows ran around the trunks
as chevrons, stretched along every limb; the root spurs and prop roots, built with their own correct UVs, did not
match. Found in the MM7 copy (`../../mm7_3d/trees_a/`).

- **Build fix.** `branch_mesh()` now swaps the axes: u runs around (`around` whole tiles, so the seam tiles) and v
  along (`along` = length / tile). The same fix is in the dungeon copy `../../mm6_dungeons_3d/leftovers/scripts/trees/`.
  The dead-tree generator (`dead_build.py`) builds its own tubes with u around and v along, so it was not affected.
  The species no longer rebuild bit-identically to their pre-fix GLBs: only the bark UVs differ.
- **Installed models fixed in place, not rebuilt** (18 of them carry the `mm6_reduce_pilot` LOD0 reduction).
  `scripts/fix_bark_uv.py <in.glb> <out.glb>`:
  - Takes every Bark primitive on LOD0–LOD2 (the impostor has no bark) and splits it into connected parts, with
    positions welded across the UV seam.
  - Classifies each part by which UV gradient runs along the part's main axis. Sapling tubes with the swapped mapping
    are fixed; root spurs and prop roots are already right and stay untouched.
  - New UVs: u' = v × around / along, where along = the part's v span (whole rings) and around =
    max(1, round(2π r_max × 0.8 / tile)), with r_max from the widest circumference (along / |∇v|). And
    v' = u / (median |∇u| × tile): one tile per 0.8 m along the branch, the build's density.
  - Only those TEXCOORD_0 floats are rewritten, in the file's own bytes. Geometry, normals, COLOR_0, leaf, fruit and
    impostor primitives, materials, images and bounds stay byte-identical, which is checked per file. The
    6tree06/tree06a LOD0 bounds are still identical.
  - Thin twigs keep one tile around (as the build does), so their texels are squeezed around the twig.
- **Food tree winding.** `scripts/fix_fruit_winding.py` flips the 16 LOD2 fruit tetrahedra of `mm6_deco_tree06a.glb`,
  whose faces pointed inward (`check_winding.py` reported 16 inverted parts before this fix). The fix swaps two
  indices per triangle, in place. `add_fruit.py`'s tetrahedron now lists its faces outward.
- **Reinstalled:** 27 models with `tools/install_model.py --engine`, each after `check_winding.py` reported 0.
  Previous sources are in `backup_pre_baruv/`. The models are cac25, snotre01/03/05, swptree1/2/3, tree01–07
  (06 and 06a), tree10, tree13–15, tree17–19, tree25, and the dungeon leftovers tree09, tree22, tree26, tree30.
- **Review:** `review/bark_uv/bark_uv_before_after.png` shows tree01, swptree3, snotre01, tree22 and tree15: the whole
  tree and a lower-trunk close-up, before and after. Renders are in `review/bark_uv/renders/`, made with
  `scripts/bark_uv_review.py`.
- **Not affected:** the dead trees (tree27, tree28, tree29, swptree4, stump5a), the desert palm tree21 and the other
  desert plants, which have their own tube UVs.

## Sources and licences

- Leaves: ambientCG [LeafSet022](https://ambientcg.com/view?id=LeafSet022) (CC0), `source/leafset022/`.
- Bark: Poly Haven [bark_brown_01](https://polyhaven.com/a/bark_brown_01) (CC0), `source/bark_brown_01/`.
- Blossoms, fruit, moss, conifer needles and snow: generated procedurally (needles and snow drawn in
  `make_leaf_atlas.py`); rosette pads reuse LeafSet022 leaves narrowed. Sapling Tree Gen (GPL) is a tool; its output is ours.

## Compromises

- 6tree19 and 6tree03 sit at the 4/255 limit in one channel at LOD2/LOD3 (saturated red barely responds to tone in
  the review render); the engine's 0.3 s dithered crossfade hides this.
- 6tree04's flowers are procedural rather than photographic; the multi-stem split is two stems, the sprite shows three.
- Fruit is low-poly (16 triangles) and slightly pinker in Eevee than the sprite's orange-red.
- Each GLB embeds its own copy of the shared bark/leaf maps (~11–12 MB each).
- Snow trees: LOD2 needs a raised tone (1.1-1.3) to match the snowy LOD0; on snotre03 43 % of the LOD2 COLOR_0
  values clamp at 1 in the GLB (measured with clamping: LOD2 within 1.2/255 of LOD0). Snow lies as white clumps on
  the pads' upper faces rather than the sprite's continuous drifts along each branch; snotre05's shelves read as a
  dense narrow column with a small gap below its spire.
- Needle sprays minify to a soft texture at review sizes; 6tree18 reads as a dark dense tree rather than a crisp
  needle crown. cac25's trunk is leaner and less twisted than the sprite's; 6tree13/6tree07 stems fork as a tighter
  bundle than the sprites' vase of thin stems.
- cac25's impostor coverage (−8.5 % vs LOD0) and snotre05's LOD2 (−10.5 % vs LOD1, −7 % vs LOD0) are a little
  outside the earlier species; the 0.3 s crossfade hides it. 6tree14 shows the trunk through a narrow gap in the
  upper crown from some angles.
