# MM6 New Sorpigal tree `6tree01` — static 3D decoration

Installed as `assets_dev/worlds/mm6/models/mm6_deco_tree01.glb` (7.3 MB). It replaces the `6tree01` sprite, which
has 213 placements in `oute3.odm`; bound in `assets_dev/worlds/mm6/models/decorations.yml`
(in-game captures: [../review_ingame/](../review_ingame/)).

[Sprite comparison](review/tree01_compare.png) · [LOD sheet](review/tree01_lods.png)

## Rebuild

`scripts/build.sh --install` reruns everything from the downloaded sources:

1. inputs
2. leaf atlas
3. tree
4. impostor
5. export
6. LOD linking and validation (`work/validation.txt`), then install
7. review renders, sheets and per-LOD tone

## Sources and licences

| Use | Source | Licence |
|---|---|---|
| Leaves | ambientCG `LeafSet022` 1K-PNG (`source/leafset022/`) | CC0 |
| Bark | Poly Haven `bark_brown_02` 1k diffuse and GL normal, by Rob Tuytel (`source/bark_brown_02/`) | CC0 |
| Skeleton | Sapling Tree Gen 0.3.7, Blender extension (GPL-3.0); covers the tool only, not the generated geometry | GPL-3.0 |

## Construction

- **Skeleton** (`build_tree.py`, `SAPLING`): see the Sapling settings below. Each spline is converted on its own,
  with its UVs scaled to a 0.5 m bark tile. Parts outside the canopy envelope are cut. To meet the budget, the
  thinnest branches are dropped rather than decimated (decimation twisted the trunk).
- **Canopy envelope**: the upscaled sprite's half-width per height (`prepare_inputs.py` → `work/profile.json`),
  revolved about the trunk, from 0.36 H up.
- **Cards**:
  - LOD0 has 3,000 cluster quads of 0.62–0.92 m.
  - 85% sit round 48 lumps near the envelope surface; the rest fill the inside.
  - Cards face outward with a random tilt and roll.
  - Vertex normals are 70% lump-outward and 30% crown-outward, which gives the clumped shading.
  - Cards inside the crown use the darkened atlas row as baked occlusion.
- **Coarser LODs**: LOD1 and LOD2 use a farthest-point subset of the LOD0 cards, scaled up to keep the covered area
  and pulled inward. More of their cards use the dark row, so the mean tone matches LOD0.
- **Leaf atlas** (`make_leaf_atlas.py`):
  - Two clusters of about 230 small leaves each round a twig; the bottom row repeats them darkened.
  - Leaf colours are remapped to dark green (albedo about 36/84/32).
  - Leaf normals are rotated with their leaves.
  - RGB is dilated into transparent texels.
- **Impostor** (`bake_impostor.py`, `finish_impostor.py`):
  - Cycles orthographic side capture of LOD0, 512 px, frame S = 6.875 m, on a square quad.
  - Albedo includes a mild AO term (0.6 m reach, 45%).
  - The normal map is in camera space: R = right, G = up, B = toward the viewer.
- **Export** (`export_tree.py`, `post_process.py`):
  - Bark is opaque and single-sided; Leaves and Impostor are MASK 0.5 and double-sided.
  - Extras: `openyamm_wind` 0.03 (bark), 0.12 (leaves); `openyamm_billboard` true (impostor).
  - LODs are linked with `tools/link_static_model_lods.py`.

| LOD | Triangles | Content |
|---|---|---|
| 0 | 7,568 | bark 1,568 (14 splines, 8/6-sided) + 3,000 cards |
| 1 | 2,732 | bark 372 + 1,180 cards (×1.46) |
| 2 | 960 | bark 180 (trunk and fork limbs) + 390 cards (×2.5) |
| 3 | 2 | impostor quad, 6.875 × 6.875 m, glTF XY plane, bottom edge y = 0 |

Textures:

| Texture | Size | Format |
|---|---|---|
| Bark base colour | 1024 | sRGB |
| Bark normal | 1024 | |
| Leaves base colour | 1024 | RGBA |
| Leaves normal | 1024 | |
| Impostor base colour | 512 | RGBA |
| Impostor normal | 512 | |

The PNGs are embedded; the two 1024 bark PNGs account for 4.1 MB of the file.

Sapling settings: `levels 3, scale 4.6, baseSplits 2, splitHeight 0.42, shape 2 (hemispherical), branches 0/80/15/8,
length 1/0.3/0.35/0.3, downAngle 90/50/45/45 (V 0/25/10/10), segSplits 0.15/0.25/0.3, splitAngle 25/15/15,
baseSize 0.3, ratio 0.035, curve 0/-20, attractUp 0/0.6/0.3, rootFlare 1.5, seed 5`. The tree is 6.74 m tall in
the model; the engine scales it to the sprite height.

## Known limits

- The crown is denser and rounder than the sprite, with less highlight contrast in the Eevee review light. Final tone
  depends on the engine's sun/probe lighting and should be checked in game.
- Bark texture seams show where trunk splines join (lower trunk band). There are no root flares beyond Sapling's.
- LOD2 renders about 5/255 lighter and bluer than LOD0 in review (larger cards catch more sky). The impostor is about
  10% thinner in coverage because its alpha is cut at 0.5.

## v2 (2026-10-08) — clumped crown, canopy occlusion, consistent LODs

Installed over `mm6_deco_tree01.glb` (10.3 MB); v1 is kept as `work/mm6_deco_tree01_v1.glb`.
Rebuild: `scripts/build_v2.sh --install` (intermediates in `work_v2/`, sheets in `review_v2/`).

User feedback on v1: the tree changed visibly between LODs, and the crown was "a merged green-ish blob" with no
shading in the leaves. v2 changes:

- **Leaves at real scale:** `make_leaf_atlas_v2.py` builds 4 whorl sprays of ~90–100 ambientCG LeafSet022 leaves
  (5–7 cm on a 0.36–0.46 m card), each leaf with its own normal plus a ±25° fold. Occlusion is no longer baked into
  the atlas.
- **Crown from clumps:** `build_tree_v2.py` places ~90 small clumps (0.4–0.7 m) on the Sapling branch tips and the
  outer shell of the sprite envelope. Clumps are kept apart (≥0.72 × the sum of radii, slightly irregular ellipsoids),
  so they don't merge and gaps, holes and limbs show. Each is a dense ball of cards with clump/crown blended normals.
- **Occlusion as COLOR_0**, from sky rays through the cards (each hit blocks 55%):
  `occ = (0.22 + 0.78·vis^1.4)` × a clump-local term (0.28–1 by height on the ball, 0.6–1 toward its core) × a
  per-clump tint (±12% value, ±10% red/blue). Bark is darkened the same way under the crown.
  Leaf extras: `openyamm_wind` 0.12, `openyamm_translucency` 0.35.
- **LOD1:** the most visible 70% of each clump's cards, farthest-point spread, at 1.3× size, LOD0 occlusion × 0.92.
- **LOD2 clump cards** (`clump_cards_v2.py` → `make_clump_atlas_v2.py` → `clump_lod2_v2.py`): each clump is three
  near-vertical cards and one near-horizontal card, showing Cycles renders of two real LOD0 clumps (side and top
  views, same leaf scale; atlas `clumps_*`, material `LeavesFar`). COLOR_0 = clump mean sky occlusion × tint × 0.9.
  Cards are tilted and the top card raised, so their intersections don't line up into a grid.
- **Impostor** (`bake_impostor_v2.py`, 1024²): LOD0 albedo × COLOR_0, unlit, with the shading normals in quad
  tangent space. The cutout is grown 2 px, and its albedo tone `(0.94, 0.80, 1.02)` is calibrated against the 3D
  levels by `lod_check_v2.py`.

| LOD | Triangles | Content |
|---|---|---|
| 0 | 7,972 | bark 1,568 + 3,202 cards |
| 1 | 2,980 | bark 372 + 1,304 cards (1.3×) |
| 2 | 908 | bark 180 + 364 clump cards |
| 3 | 2 | impostor |

Textures: bark 1024 (base + normal), leaves 1024 RGBA + normal, clumps 1024 RGBA + normal, impostor 1024 RGBA + normal.

**LOD consistency** (`lod_check_v2.py`: eye level, engine-like lighting with no shadow maps, common 300 px):

| LOD | Mean sRGB | Coverage vs LOD0 | Δ vs previous |
|---|---|---|---|
| 0 | 31.4 / 51.9 / 25.2 | 1.000 | — |
| 1 | 31.6 / 53.1 / 25.4 | 0.985 | ≤1.2, −1.5% |
| 2 | 32.2 / 50.5 / 27.4 | 1.014 | ≤2.6, +3.0% |
| 3 | 32.1 / 52.5 / 25.4 | 0.967 | ≤2.0, −4.7% |

Sprite vs v2 LOD0 (Eevee lit, mean / luminance 5-50-95): sprite 23.7/40.8/22.8, 1/28/89;
v2 24.4/43.4/20.5, 18/31/68.

Review: `review_v2/tree01_v2_compare.png`, `tree01_v2_lod_consistency.png` (common and in-game sizes),
`tree01_v2_lods_three_quarter.png`, `tree01_v2_occlusion.png`.

**Compromises:**
- Highlights and gaps are less extreme than the pre-rendered sprite's: its holes are black, ours show the sky.
- LOD2 clump cards still show faint card edges in a raised three-quarter view at 300 px; this is less visible at
  the ~160 px they are used at.
- The impostor tone is calibrated under Eevee, not the engine. Recheck in game; it is `IMPOSTOR_TONE` in
  `finish_impostor_v2.py`.

## v2 bark (2026-10-08)

User review: the trunk read as a plain brown slab (no relief, no roughness). Changes, all in the v2 pipeline
(`scripts/build_v2.sh --install`):

- Bark texture Poly Haven [bark_brown_01](https://polyhaven.com/a/bark_brown_01) (CC0, deep vertical furrows like
  the sprite's trunk), 2k sources reduced to 1024² (`scripts/prepare_bark_v2.py`): diffuse × ambient occlusion^1.5 ×
  a little height, so crevices stay dark in the crown's shade, graded to the sprite's trunk mean; OpenGL normal map at
  strength 1.6 (`normalTexture.scale`); roughness map as the glTF metallic-roughness texture. Repeat 0.8 m.
- Bark occlusion `0.55 + 0.45 × sky visibility` instead of the leaves' curve (the trunk had dropped to 0.3–0.5).
- Five root spurs flare from the trunk base into the ground (deterministic, so the clump layout is unchanged).
- LOD2 clump-card tone 0.9 → 1.05 to keep the LOD colour match after the brighter bark: neighbouring levels now
  differ by at most 2.1/255 (coverage within 3.2 %). File 11.4 MB; LOD triangles 7,957 / 2,980 / 860 / 2.

In game: [base](../review_ingame/tree01_v2_bark_base.png) · [roadside](../review_ingame/tree01_v2_bark_roadside.png) ·
[roots](../review_ingame/tree01_v2_bark_roots.png); before: [../review_ingame/v1/tree01_v2_bark_before.png](../review_ingame/v1/tree01_v2_bark_before.png).
