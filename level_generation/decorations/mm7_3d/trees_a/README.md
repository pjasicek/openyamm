# MM7 trees, batch A (2026-10-15/16)

Conifers tree36, tree33 and tree60, and broadleaf trees 7tree04, tree65, 7tree63, 7tree01 and 7tree10. They are
built with a copy of the MM6 New Sorpigal tree pipeline (`../../mm6_new_sorpigal_3d/trees/`), whose scripts are
copied into `scripts/` and extended; the MM6 folder is unchanged. All eight are installed.
[Overview: sprite above LOD0](review/overview.png).

## Models

| Model | Serves (placements) | LOD triangles (after the 2026-10-16 pass) | File (source) | Review |
|---|---|---|---:|---|
| `mm7_deco_tree36.glb` | tree36 (323) | 3490 / 2380 / 880 / 4 | 8.4 MB | `review/tree36/sheet.png`, `reduce_compare.png` |
| `mm7_deco_tree33.glb` | tree33 (241) | 3642 / 2380 / 880 / 4 | 8.3 MB | `review/tree33/sheet.png`, `reduce_compare.png` |
| `mm7_deco_7tree04.glb` | 7tree04 (129) | 4944 / 2380 / 888 / 4 | 8.8 MB | `review/7tree04/sheet.png`, `reduce_compare.png` |
| `mm7_deco_tree60.glb` | tree60 (57) | 4060 / 2380 / 880 / 4 | 8.6 MB | `review/tree60/sheet.png` |
| `mm7_deco_tree65.glb` | tree65 (55) | 6364 / 2780 / 808 / 4 | 10.1 MB | `review/tree65/sheet.png` |
| `mm7_deco_7tree63.glb` | 7tree63 (44) | 5216 / 2780 / 980 / 4 | 8.8 MB | `review/7tree63/sheet.png` |
| `mm7_deco_7tree01.glb` | 7tree01 (11; one indoors, 7d22) | 6250 / 2776 / 716 / 4 | 9.8 MB | `review/7tree01/sheet.png` |
| `mm7_deco_7tree10.glb` | 7tree10 (8) | 4926 / 2372 / 988 / 4 | 9.6 MB | `review/7tree10/sheet.png` |

Budgets are 6000 LOD0 triangles for trees with 100+ placements and 7000 for the others, with alpha cards included.
LOD3 is the MM6 impostor (one camera-facing quad, cut to its outline: 4 triangles). Each sheet shows the x2 sprite, then LOD0 from the front, at
three-quarter and from the side (Eevee, with shadow maps), then LOD0 from the front without shadow maps (the engine
default). Below that are every LOD at a common size and at its in-game size. The colour and coverage differences
between neighbouring LODs are at most 2.3/255 and 4.6 % (`work/<id>/lc_stats.json`). The exceptions are the
7tree01 impostor, with −6 % coverage, and tree36's LOD1 (+3.5 %).

- **tree36:** snow-laden spruce with a pale trunk that shows to the top. It has 24 whorls of drooping limbs from the
  ground and a narrow spire, with snow flecks on most fronds and more of them low down.
- **tree33:** a more open fir. Its upward-angled limbs droop at the tips, it has a bare leader at the top, darker
  green with less snow, and two small root flares.
- **tree60:** slim green hemlock-like conifer. The trunk is bare below a fifth of the height, and a column of
  short limbs carries fronds that partly hang as curtains.
- **7tree04:** dense oblong broadleaf crown from a quarter of the height to a flattish top, on a straight dark trunk.
- **tree65:** weeping broadleaf. A rounded crown sits on a tall bole, and curtains of small hanging leaf strands come
  from the outer clumps.
- **7tree63:** weeping crown with upward limbs hung with long drooping feathery fronds, widest near its top, on a
  thick trunk.
- **7tree01:** broad round crown. The bent red-brown trunk forks at a third of the height into four stems.
- **7tree10:** multi-stem tree. Five slender red-brown stems rise bundled from a short base and fan out through a
  loose crown, with the limbs visible between small leaf clumps.

## Quality pass (2026-10-16)

This pass followed the in-game captures in `output/mm7_deco_outdoor_20261016/`. The pre-pass sources and species
files are in `backup_pre_quality/`. All eight trees were rebuilt and reinstalled under the same names; every GLB
passes `check_winding.py` with 0 inverted parts. Total LOD0 went from 45,564 to 38,892 triangles (−15 %).

- **Snow (tree36, tree33).** Snow cards have their own material, `LeavesSnow`, using the same atlas, so shaded snow
  stays near-white:
  - `emissiveFactor` 0.06 (linear), a small lift that does not glow;
  - `openyamm_translucency` 0.6 (sunlight through the snow);
  - shading normals nearly straight up (`fronds.snow_up` 2.5);
  - COLOR_0 occlusion fully lifted (`snow.lift` 1.0);
  - a brighter, less blue snow layer in the atlas (`snow.shade_floor` 0.88, `edge_tint` 0.4, sRGB 252/252/248).

  The LOD0 mean without shadow maps is now 166/177/163 for tree36 and 136/145/136 for tree33. It is a little
  brighter than the sprites (134/148/131 and 101/114/100); with shadow maps it is 130/141/133 and 109/118/113.
- **tree65.**
  - The trunk is a thick bole (Sapling `ratio` 0.11, `bark.trunk` top 0.62, taper 0.6) with pale lichen mottling
    over dark brown bark (`bark.mottle`, tileable noise in `prepare.py`).
  - The hanging leaf strands now drape over the crown's sides (`moss.drape`). They hang from the upper outer face of
    the outer clumps between 36 % and 72 % of the height, facing outward, instead of forming a fringe under the
    crown.
- **7tree63.**
  - The trunk is twisted: spiral bark grain (`bark.twist` 0.3) and a slow spiral bend in the bole below the crown
    (`skeleton.wobble`).
  - It is thicker (0.27 m radius) with four root flares.
  - The crown is less boxy: whole whorls vary in reach (`skeleton.whorl_reach` 0.75–1.05, limb `reach` 0.55–1.0).
- **Bark UV fix (all trees).** Blender's curve UVs run u along the curve and v around it. The MM6 pipeline scaled
  them the other way, which stretched the bark texture along every branch and trunk; that is what the smooth,
  streaky trunks were. `build_tree.py` now swaps the axes (bark tiles about 0.8 m both ways, grain along the
  branch). The MM6 New Sorpigal and dungeon-leftover trees had the same bug. They were fixed in place on 2026-10-16 (see `../../mm6_new_sorpigal_3d/trees/README.md`, "Bark UV fix"); the other MM7 and MM8 batch copies of the pipeline are their builders' to check.
- **Card thinning (`lod.thin0`).** The least sky-visible LOD0 cards are dropped: they are buried in the crown and
  covered by the cards around them. The bark's sky rays use the thinned crown. Rates are 15 % on tree36, tree33 and
  7tree04 and 12 % on the other five. LOD0 coverage at eye level fell by 1–3 %, and every LOD stays within
  3.7/255 in mean colour and 4.5 % in coverage of its neighbour. The exceptions are the impostors of 7tree01 (−6 %)
  and tree60 (+6 %).
- **Bark reduction (tree36, tree33, 7tree04).** This uses `reduce.sh <id>`, a copy of the `mm6_reduce_pilot` route
  in `scripts/reduce/`: dump, pymeshlab texture-aware ladder, rebuild, swap with the alpha primitives
  byte-for-byte, winding check, then `review/<id>/reduce_compare.png`. With `DECO_RATIOS` set to
  0.85…0.40, the lowest step within 1.5 % max and 0.15 % mean surface distance was:

  | Tree | Step | Bark triangles |
  |---|---|---|
  | tree36 | r55 | 1480 → 814 |
  | tree33 | r70 | 1466 → 1026 |
  | 7tree04 | r78 | 1688 → 1316 |

  The other five keep their bark as built.
- **Changed draw count.** tree36 and tree33 now have three LOD0–LOD2 primitives (Bark, Leaves, LeavesSnow) instead of
  two.
- **Shapes.** The conifer skeleton now draws the whorl-reach value from its random stream, so tree36, tree33 and
  tree60 are new random trees with the same settings; their silhouettes and proportions are unchanged.
- **Bindings unchanged:** the same names and heights. `still: true` remains the suggestion for all eight.

Per model, LOD triangles before → after:

| Model | Before | After | Changes |
|---|---|---|---|
| tree36 | 4672 / 2380 / 880 / 4 | 3490 / 2380 / 880 / 4 | snow material; 15 % cards; bark r55; bark UVs |
| tree33 | 4634 / 2380 / 880 / 4 | 3642 / 2380 / 880 / 4 | snow material; 15 % cards; bark r70; bark UVs |
| 7tree04 | 5956 / 2378 / 888 / 4 | 4944 / 2380 / 888 / 4 | 15 % cards; bark r78; bark UVs |
| tree60 | 4428 / 2380 / 880 / 4 | 4060 / 2380 / 880 / 4 | 12 % cards; bark UVs |
| tree65 | 6962 / 2780 / 858 / 4 | 6364 / 2780 / 808 / 4 | thick mottled bole; draped strands; 12 % cards; bark UVs |
| 7tree63 | 6492 / 2780 / 980 / 4 | 5216 / 2780 / 980 / 4 | twisted, thicker trunk, root flares; lobed crown; 12 % cards; bark UVs |
| 7tree01 | 6966 / 2780 / 716 / 4 | 6250 / 2776 / 716 / 4 | 12 % cards; bark UVs |
| 7tree10 | 5454 / 2346 / 988 / 4 | 4926 / 2372 / 988 / 4 | 12 % cards; bark UVs |

The reduction needs a Python with pymeshlab (`MESHPY`; this batch used a session venv). The sprites are now read
from `assets_legacy/decorations_x2_20261016/`.

## Suggested bindings

All eight are outdoor trees with single-frame sprites, so they have no native animation and the bindings say
`still: true`. Leaves and bark still sway through their `openyamm_wind` material extras. Height is the sprite's
`art_height`.

```yaml
  - name: tree36
    model: engine/models/mm7_deco_tree36.glb
    height: 1252
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
    still: true
  - name: tree33
    model: engine/models/mm7_deco_tree33.glb
    height: 1260
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
    still: true
  - name: tree60
    model: engine/models/mm7_deco_tree60.glb
    height: 1280
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
    still: true
  - name: 7tree04
    model: engine/models/mm7_deco_7tree04.glb
    height: 1255
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
    still: true
  - name: tree65
    model: engine/models/mm7_deco_tree65.glb
    height: 1278
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
    still: true
  - name: 7tree63
    model: engine/models/mm7_deco_7tree63.glb
    height: 1280
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
    still: true
  - name: 7tree01          # also one indoor placement (7d22.blv): the same model in indoor_decorations.yml
    model: engine/models/mm7_deco_7tree01.glb
    height: 1280
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
    still: true
  - name: 7tree10
    model: engine/models/mm7_deco_7tree10.glb
    height: 1280
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
    still: true
```

No binding needs `mount`, `free_model`, `swing` or `z_offset`; the base centre is on the ground at the origin.

## Pipeline

```bash
./quick.sh <id>              # inputs, leaf atlas, tree, review/<id>/quick.png (LOD0 views, engine-like colour stats)
./build.sh <id> [--install]  # full build: LODs, impostor, export, validation, install, review/<id>/sheet.png
python3 scripts/overview.py tree36 tree33 tree60 7tree04 tree65 7tree63 7tree01 7tree10   # (from scripts/)
```

To rebuild all eight, run `./build.sh <id> --install` for each id. Each species takes 2–10 minutes, depending on
machine load.

Changes against the MM6 scripts are all opt-in per species; absent keys build exactly as in MM6.
- **`common.py`:**
  - The sprite is the restored x2 frame from `assets_dev/engine/decorations_x2/`, looked up in `../inventory.json`.
  - CC0 sources are read from the MM6 `source/` folder.
  - `post_process.py --install` calls `tools/install_model.py --engine --name <output>`.
- **`skeleton.kind: conifer`** (`build_tree.py`) replaces Sapling's splines with an explicit spruce skeleton fitted to
  the sprite envelope. It has a straight tapering trunk and `whorls` × `per_whorl` limbs that reach the envelope,
  rise and droop. Sapling only supplies the curve settings.
- **`skeleton.kind: forked`** builds a broadleaf skeleton. A bent trunk forks at `fork` × H into `stems` stems
  (`mid_spread` < 1: they rise first, then fan out), with side limbs in the crown. `fork` near 0 gives a multi-stem
  tree (7tree01, 7tree10).
- **`bark.trunk`** stretches a Sapling trunk to a set height with a gentle taper, moving its limbs up with it
  (tree65). **`bark.bare_below`** leaves out limbs that start below that height.
- **`crown.along`** places clump or frond points along the limbs. **`crown.fronds`** gives each point frond cards:
  - the card's u axis runs along the limb, and the card is rolled about the limb and droops;
  - optional `hang` makes weeping branchlets, `leader` adds spire tufts and `size_by_width` shrinks fronds near a
    pointed top;
  - fronds get upward shading normals, stronger on snow cards;
  - `leaves.snow.by_height` chooses snow cells by height.
- **`leaves.kind: fronds`** (`make_leaf_atlas.py`) draws a conifer branch end along the cell's u axis: a spine,
  alternate branchlets and needles, with snow flecks on the snow cells.
- **`crown.moss.kind: leafy`** draws hanging strands of small LeafSet022 leaves instead of moss. `crown.moss.side_power`
  hangs them mostly from the outer clumps (tree65).
- **`lod.lod2: subset`** makes LOD2 a frond subset like LOD1 and skips the clump-card renders (frond trees). Where a
  tree has many small clumps, `clump_cards.py` groups them by numpy k-means instead of the cubic pairwise merge.
- **2026-10-16 additions:**
  - `leaves.snow.material` (the `LeavesSnow` material), `snow.shade_floor` and `snow.edge_tint`;
  - `lod.thin0`;
  - `bark.mottle`, `bark.twist`;
  - `skeleton.wobble`, `skeleton.whorl_reach`;
  - `crown.moss.drape` and `crown.moss.band`;
  - `reduce.sh` (bark reduction).
- **Review scripts:** `render_review.py` takes `TREE_ONLY`, which hides the other levels, and there are `quick.py`,
  `review_sheet.py` and `overview.py`.

**Design height.** The models are 6.2–6.6 m tall in Blender, and the engine scales each to its binding height (about
1280 units, 15.7 m). Leaves and needles are therefore 2.4× real scale. This matches the sprites' large leaf
clusters and keeps the MM6 pipeline's metre constants valid. Wind amplitude is in model units, so it scales the same
way.

**Colour grading.** The species colour is tuned until the LOD0 mean without shadow maps (the engine default) is
within about 10/255 of the sprite mean. The shadowed review render is darker; both stats are on each sheet. LOD tones
and impostor tones are then set from `lod_check.py` so the levels match LOD0.

## Sources and licences

- Bark: Poly Haven [bark_brown_01](https://polyhaven.com/a/bark_brown_01) (CC0), read from
  `../../mm6_new_sorpigal_3d/trees/source/` and graded per species.
- Leaves: ambientCG [LeafSet022](https://ambientcg.com/view?id=LeafSet022) (CC0), from the same folder. It supplies
  the broadleaf sprays and tree65's hanging strands.
- Conifer fronds, needles and snow: procedural, our own (`make_leaf_atlas.py`). Sapling Tree Gen (GPL) is a tool;
  its output and the skeletons are ours.

## Compromises

- **Snow (tree36, tree33):** since the 2026-10-16 pass, shaded snow stays near-white through `LeavesSnow`'s small
  emissive lift. At night it shows as a faint grey; the engine has no emissive texture, so the lift also brightens
  the green needles of snow cards a little. The two trees share one recipe and differ in openness, limb angle, snow
  amount and colour.
- **tree33:** its root flares are two small spurs, not the sprite's bulging pair.
- **Conifer LOD2:** frond trees use a frond subset (1.65–1.85× cards), not MM6's clump cards, which turned a frond
  crown into box-shaped patches.
- **tree65:** the crown is rounder than the sprite's, and the draped strands are a regular curtain where the sprite's
  weeping sprays are looser.
- **7tree63:** the crown flares out toward the top (a V), whereas the sprite's is a broad mass of drooping lobes. The
  trunk twist is a texture spiral plus a gentle bend, without the sprite's bold spiral ridges.
- **7tree04:** a small gap in the crown shows from the front at some angles.
- **7tree01:** the impostor has 6 % less coverage than LOD0 (the 0.3 s crossfade hides this). Its leaves are a
  little greyer than the sprite's vivid green with lime highlights.
- **7tree10:** the crown is more open than the sprite's, which is deliberate so the limbs show. LOD0 has 5454
  triangles.
- **All:** the cards are alpha-tested; minified needle and leaf sprays read softer than the painted sprites. Each GLB
  embeds its own bark and leaf maps (8.7–10.6 MB).
- **7tree01 indoors:** the model is graded for outdoor light, not tinted for dungeon light, at its single indoor
  placement.
