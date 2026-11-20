# Meadow bushes (2026-10-16)

Four low temperate shrubs to fill the mid-height layer between the grass cards and the trees
([Meadow improvements](../../terrain/MEADOW_IMPROVEMENTS.md), section 1). Everything is procedural: headless Blender
scripts plus numpy/PIL textures cut from the CC0 sources the project's trees already use. No Meshy or Codex images
were used.

All four are installed with `tools/install_model.py --engine`:
- sources: `assets_source/engine/models/meadow_bushNN.glb`
- cooked runtime copies: `assets_dev/engine/models/meadow_bushNN.glb`

They are not bound in any `decorations.yml`. The engine refers to them as `engine/models/meadow_bushNN.glb`.

```bash
./build.sh                          # textures, models, review renders, finish and validate, sheet, lineup (~1 min)
./build.sh --install meadow_bush03  # rebuild and reinstall some
```

## Models

| Model | Shape | Height (game units) | Footprint (units) | Triangles LOD0 / LOD1 / LOD2 |
|---|---|---:|---|---|
| `meadow_bush01` | round dense shrub (box, hawthorn) | 125 | 146 x 137 | 698 / 356 / 128 |
| `meadow_bush02` | wide spreading shrub | 105 | 192 x 168 | 746 / 384 / 130 |
| `meadow_bush03` | young sapling bush: three thin leaning stems, side branches, open crown | 180 | 140 x 137 | 599 / 236 / 120 |
| `meadow_bush04` | low broadleaf clump (bramble, elder undergrowth) | 78 | 148 x 153 | 556 / 308 / 96 |

- **Units.** Models are in metres at 1/100 of the game size (1.25 m = 125 units). The engine scales a model to its
  binding height anyway.
- **Triangle counts.** These are after card cutting, which keeps the number of triangles.
- **LOD2 stems.** LOD2 of bush01, bush02 and bush04 has no stems, because they are hidden inside the foliage.

## Conventions (as for the tree and plant decorations)

- **Orientation.** Blender +Z up, exported with `export_yup`, so glTF +Y is up.
  - The origin is the base centre on the ground.
  - The shapes are radially irregular and have no front, so any yaw works.
  - Stem ends start 3 cm below the ground, so they never float on a slope.
- **One node, LODs in extras.**
  - Blender exports objects `<id>`, `<id>_LOD1` and `<id>_LOD2`.
  - `tools/link_static_model_lods.py` lists the LOD meshes in the base mesh's `extras.openyamm_lods` (coarsest last)
    and removes the LOD nodes.
  - The node has no transform.
  - There is no impostor level (the trees' LOD3), because bushes are small enough to fade out.
- **Materials.** Each LOD is one mesh with two primitives. In-engine this is one draw per material per LOD.
  - `Bark`: opaque, single-sided, roughness 0.9. Extras: `openyamm_wind` = a quarter of the leaves' value,
    `openyamm_specular` 0.1.
  - `Leaves`: `alphaMode` MASK with a cutoff of 0.5, double-sided, roughness 0.85. Extras: `openyamm_wind` (0.025 /
    0.02 / 0.04 / 0.015 model units at the top, about 2 % of the height), `openyamm_translucency` 0.35,
    `openyamm_specular` 0.1.
  - Transparent leaves are their own primitive and material within the one mesh, as in every decoration model. The
    creature rule of a separate mesh node is not needed: static decorations cast no merged shadows.
- **COLOR_0** (linear, multiplied into base colour) carries the occlusion:
  - sky rays through the LOD0 cards (each hit passes 45 %);
  - lit clump tops and shaded undersides;
  - darkening toward the ground (to 0.72 at the base);
  - a ±7 % per-clump tint.

  Every primitive has COLOR_0, NORMAL and TEXCOORD_0.
- **Shading normals.** Custom normals on the cards, 60 % from the clump centre and 40 % from the bush centre, so the
  bush shades as one soft mass. Stem normals are radial.
- **Card cutting.** `tools/cut_foliage_cards.py` cuts the cards to their texels and keeps 4 vertices per card.
  - Cutting lowers the top slightly, so `finish.py` then rescales all levels uniformly until LOD0's cut top is the
    target height again.
  - It clamps coarser levels to that height, so no LOD pops above LOD0.
- **Top coverage.** Clumps cover the whole envelope, including the top, and cards face outward plus `card_up`.
  Seen from above, every bush is a closed leafy mass, not a cross (`review/lineup_air.png`, the top-view columns of
  the sheet).

## Textures (one shared set; the cook stores them once for all four)

| File | Size | Content |
|---|---|---|
| `textures/leaves_basecolor.png` | 1024² RGBA | four 512 px cells (below), alpha cut-out, RGB dilated into the transparent texels |
| `textures/leaves_normal.png` | 1024² | per-leaf tangent normals with a fold, OpenGL +Y |
| `textures/bark_basecolor.png` | 512² | grey-brown stem bark, mean sRGB 79/67/53 |
| `textures/bark_normal.png` | 512² | OpenGL +Y |

**Atlas cells.** Cell k is at row k // 2, column k % 2.

| Cell | Content | Leaf size |
|---|---|---|
| 0 | dense small-leaved spray | 3–4 cm |
| 1 | the same with lighter young tips | 3–4 cm |
| 2 | broadleaf clump of three- and five-leaflet compound leaves (bush04) | 8–12 cm |
| 3 | open medium spray (sapling) | 5–6 cm |

Preview: `review/atlas_preview.png`.

**Colour.** The base leaf colour is sRGB 100/156/72, a natural mid green. The cells average about 90/145/64, within
the 30–243 range. The game tints bushes per instance. In the lineup, the bushes match the 7tree04 crown in the same
lighting.

**Sources** (our own processing of CC0 material already in the project, `../mm6_new_sorpigal_3d/trees/source/`):
- Leaves: ambientCG **LeafSet022** (CC0), the leaves of every tree atlas. The two most blotched leaves are left out.
- Bark: Poly Haven **bark_brown_01** (CC0), the trees' bark: diffuse x AO^1.5, graded.

**Texel density.** About 1,280 px/m on the leaves (512 px per 0.36–0.52 m card) and 1,024 px/m on the bark
(512 px per 0.5 m tile).

## Scripts (`scripts/`)

- `bushes.py`: per-bush settings (envelope, clumps, cards, cells, stems, budgets, LOD keep and grow, wind).
- `make_textures.py`: the shared atlas and bark.
- `build_bush.py` (Blender): stems, clumps, cards, occlusion, LOD subsets, export to `work/<id>_export.glb` and
  `work/<id>.blend`.
- `finish.py`: material modes, LOD link, card cut, height fit, then validation:
  - one node and a decreasing three-level chain within budget;
  - ground base and height;
  - extras and attributes.

  It writes `work/<id>.glb` and `work/<id>_final.json`. `--install` installs the model.
- `render_review.py` (Blender): the review renders, with the engine's vertex-colour rule and no shadow maps.
- `sheet.py`: composes the renders into the sheets.
- `lineup.py` (Blender): re-imports the finished GLBs at game scale beside `mm7_deco_7tree04` and the fern
  `mm7_deco_bush03`.

## Review

- `review/sheet.png`: per bush, LOD0 front, three-quarter and top views, then LOD1 and LOD2 front and top views,
  all at one camera distance.
- `review/meadow_bushNN.png`: each bush's row of the sheet.
- `review/lineup.png` (eye height) and `review/lineup_air.png` (flying view): the bushes beside the tree and fern.

**LOD consistency.** Mean colour is within 4/255 between levels, front and top. Coverage grows with the level:
- LOD1: +2 to +11 %;
- LOD2: +9 to +29 % (largest on bush04 front, 0.117 → 0.151).

This is deliberate. The cards grow 1.3x / 1.7x as on the trees, to offset alpha-test thinning in the far mips. If
in-game switches show a fuller silhouette, lower `grow`.

**Revision 1.** The first build looked like small trees, so two changes were made:
- bush01 and bush02 now have foliage down to the ground (`under`);
- the sapling's crown was opened up: 175 cards instead of 210, smaller clumps and longer side branches.

**Winding.** `../mm8_3d/animated/scripts/check_winding.py` finds 0 inverted parts in all four.

## Deviations from the modelling guidelines

- **Thin stems.** Stems of 1–2.6 cm radius with 4–5 sides and 15–30 cm segments give long thin triangles. This is
  inherent to thin cylinders: more rings would only add triangles. The bark is rough (no specular flicker), and the
  stems are a few pixels wide in game. The trees have the same.
- **Not seen in game.** Nothing is checked in game yet: the game was not launched for this task.
