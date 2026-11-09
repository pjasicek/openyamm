# MM8 broadleaf trees in 3D (batch `trees_broadleaf`, 2026-10-15)

Static 3D replacements for the MM8 broadleaf tree sprites: `tree12`, `tree10`, `tree62a`, `tree11`, `tree18`,
`tree25`, `tree31`, `tree60a`, `tree13`, `tree59` (willow), `tree61a`. Brief: `../BRIEF.md`. The pipeline is the MM6
species pipeline (`../../mm6_new_sorpigal_3d/trees/`, copied, not edited) adapted for 12 m MM8 trees, a ~5k LOD0
budget and shared textures. Sprite overview: `review/sprites.png`.

```bash
python3 scripts/make_shared.py          # shared bark + leaf atlas (only when they must change: see "Shared textures")
./build.sh <id>                          # envelope -> tree -> LOD2 clump cards -> impostor -> export -> validate -> review
python3 tools/install_model.py level_generation/decorations/mm8_3d/trees_broadleaf/work/<id>/mm8_deco_<id>.glb \
    --engine --name mm8_deco_<id>.glb   # from the repository root (build.sh <id> --install does the same)
```

Review per species: `review/<id>/sheet.png` (top: x2 sprite | LOD0 front | three-quarter | side; below: every LOD at
a common size with mean colour and coverage, and at its in-game size), also `compare.png`, `lod_consistency.png`,
`occlusion.png`. Numbers: `work/<id>/lc_stats.json`, validation `work/<id>/validation.txt`.

## State (2026-10-16, fourth pass): shell colour, leaf floor, under-crown gate; all eleven re-installed

The user saw black crown hearts in game: the Shell material had no texture or factor, so its albedo was COLOR_0 alone
(0.02-0.05 linear), and the engine's leaf shader no longer adds sky reflection on alpha-tested leaves. Fixes, over
the same names (bindings unchanged; overdraw results and triangles unchanged):

1. **Shell texture**: the cores sample the shared leaf atlas (the same image, embedded once): each core maps onto the
   leafy hub of one of the species' cells (+-x / +-y to the cell's sides, +-z to its centre), times COLOR_0 = the leaf
   tint normalised to luminance `crown.shell.lum` (0.62 for tree12/tree10/tree60a/tree61a, otherwise tint x
   `shell.value` 0.55) x sky AO (floor 0.5): about 0.3-0.5. In Blender the leaf image now uses straight
   (channel-packed) alpha, as the engine samples it: premultiplied, the dilated colour of transparent texels went black
   on the opaque shell in the reviews, the impostor and the clump bakes.
2. **Leaf floor**: leaf COLOR_0 luminance floored at `occlusion.leaf_floor` 0.17 (tree60a 0.15) on the cards, the
   willow strands and the LOD2 clump cards. Leaf targets re-fitted afterwards so each crown's mean stays within about
   4.6/255 of its sprite.
3. **Under-crown gate** `scripts/undergate.py <id> <tag>`: LOD0 from 2 m up, 1.5 m from the trunk, pitched 60 degrees up
   (`upward`, 24 mm), and a low three-quarter view (`low34`), opaque back faces culled, engine-like light (no shadow
   maps or screen-space occlusion: Eevee's blacken any surface deep in the crown); share of covered pixels below
   sRGB luminance 16 (`black16`) and 28. Sheets `review/<id>/under_after_ns.png`, all together
   `review/under_crown_gate_all.png`; `before_ns` for the ten whose previous blends were still on disk.

COLOR_0 luminance (linear, p5/p50/p95, LOD0) before -> after, and the near-black share after (upward / low 3/4):

| Id | Shell before | Shell after | Leaves before | Leaves after | black16 after |
|---|---|---|---|---|---|
| tree12 | 0.03/0.03/0.03 | 0.30/0.30/0.33 | 0.07/0.19/0.62 | 0.17/0.18/0.53 | 0.02 % / 0.01 % |
| tree10 | 0.04/0.04/0.05 | 0.30/0.30/0.32 | 0.06/0.17/0.70 | 0.17/0.18/0.61 | 0.03 % / 0.00 % |
| tree62a | 0.03/0.03/0.04 | 0.29/0.31/0.35 | 0.07/0.20/0.67 | 0.15/0.18/0.62 | 0.01 % / 0.02 % |
| tree11 | 0.04/0.04/0.04 | 0.36/0.36/0.38 | 0.07/0.22/0.79 | 0.17/0.21/0.74 | 0.03 % / 0.00 % |
| tree18 | 0.04/0.04/0.04 | 0.46/0.47/0.48 | 0.19/0.43/0.97 | 0.19/0.43/0.97 | 0.51 % / 0.00 % |
| tree25 | 0.04/0.04/0.04 | 0.49/0.49/0.50 | 0.24/0.52/1.00 | 0.24/0.52/1.00 | 0.06 % / 0.00 % |
| tree31 | 0.04/0.05/0.05 | 0.36/0.36/0.39 | 0.16/0.35/0.83 | 0.17/0.35/0.83 | 0.03 % / 0.00 % |
| tree60a | 0.02/0.02/0.02 | 0.29/0.30/0.32 | 0.04/0.13/0.47 | 0.15/0.15/0.35 | 0.03 % / 0.00 % |
| tree13 | 0.03/0.03/0.03 | 0.33/0.33/0.33 | 0.09/0.25/0.74 | 0.17/0.25/0.74 | 0.17 % / 0.00 % |
| tree59 | 0.03/0.03/0.04 | 0.31/0.32/0.37 | 0.06/0.23/0.78 | 0.17/0.22/0.76 | 0.01 % / 0.00 % |
| tree61a | 0.04/0.04/0.06 | 0.30/0.32/0.39 | 0.09/0.21/0.66 | 0.16/0.18/0.55 | 0.03 % / 0.01 % |

Final gates: crown colour within 4.6/255 of the sprite (tree60a +4.6 in green: the darkest sprite against the floor),
LOD steps as before, `check_winding.py` 0 inverted everywhere, overdraw as in the third pass.

## State (2026-10-16, third pass): leaf overdraw cut, inner shell, all eleven re-installed

Coordinator pass (user-approved): the out07 forest spent about half the GPU frame on leaf cards (stacked alpha-tested
layers). Over the same names, bindings unchanged:

1. **Overdraw gate** `scripts/overdraw.py <id> [tag]` (renders with `overdraw_render.py`): every LOD from the front,
   three-quarter and side review cameras, Cycles 1 sample per pixel without pixel filter; every card material
   (Leaves, LeavesFar, Moss, Impostor) becomes transparent plus an emission of 1 where its texel passes the 0.5
   cutoff, so each camera ray sums one per surviving card fragment (no depth test between cards); opaque materials
   (Bark, Shell) stop the ray, as the engine's opaque depth prepass rejects the cards behind them. Mean and 95th
   percentile of layers over covered pixels per LOD -> `work/<id>/overdraw_<tag>.json` and heat maps
   `review/<id>/overdraw_<tag>.png` (0 grey, 1 blue ... 6+ red). The impostor is billboarded toward each camera.
   It counts passing fragments only; the alpha-rejected fragments of large cards also cost in the prepass and fall
   with the card count.
2. **Inner shell** (`crown.shell`, material `Shell`: opaque, single-sided, `openyamm_wind` 0.12 as the leaves,
   `openyamm_specular` 0.1, COLOR_0 = the species' leaf colour x 0.16 x sky AO through the cards, floor 0.3; none on
   the impostor, which bakes LOD0 with it). Mode `cores` (default): one smooth octahedron at 0.45 x the clump
   ellipsoid (0.4 for the open crowns tree18/tree25/tree31/tree13) inside each of the 40 / 20 / 8 largest clumps
   (60 / 30 / 12 for tree25/tree31/tree13), 320 / 160 / 64 triangles. A crown-wide star-shaped wrap (mode `wrap`,
   still in `build_tree.py`) was tried first: it read as flat dark facets through the gaps of open crowns and from
   below, so it is not used. Close-ups (below the crown and a near three-quarter, LOD0) for all eleven:
   `review/closeups_shell_cores.png`.
3. **Fewer cards**: the view cull (32 -> 40 directions, now also -70 degrees so cards seen from below the crown
   stay) treats the shell as opaque, so cards inside or behind it go first; `crown.keep` sets the kept fraction of the
   generated cards (0.37-0.6 per species), `lod.card_frac` [1, 0.9 (0.8), 1] trims LOD1, LOD1 cards grow 5 % less;
   LOD2 clump groups have two crossed verticals plus the top card (`lod.lod2_vertical` 2), 85 % of the groups
   (`lod.lod2_capacity`), card scale and LOD tones re-fitted per species. LOD1/LOD2 subsets rank cards by the view
   score first.
4. Gates: front LOD0 coverage against v2 (`scripts/gate.py <id> v2`, baselines `gate_baseline.py <id> v2` from the v2
   exports), colour against the sprite (review eye render), LOD steps, `check_winding.py` (0 inverted everywhere), the
   overdraw targets. Before/after sheets with heat maps: `review/<id>/overdraw_before_after.png`
   (`scripts/overdraw_sheet.py`); v2 sheets kept as `review/<id>/v2_before_after.png`.

| Id | LOD triangles | Layers LOD0/1/2 before (v2) | after | LOD0 coverage vs v2 | Crown colour max Δ vs sprite | LOD steps colour / coverage |
|---|---|---|---|---|---|---|
| tree12 | 2624/1198/402/2 | 4.57/3.78/3.87 | 3.07/2.70/2.52 | -0.9 % | 4.5 | 2.2 / 6.2 % |
| tree10 | 2694/1200/400/2 | 4.38/3.38/4.19 | 3.16/2.45/2.56 | -1.6 % | 2.7 | 5.4 / 3.8 % |
| tree62a | 3260/1200/400/2 | 3.11/2.25/3.32 | 2.55/1.82/2.00 | -0.7 % | 1.5 | 4.0 / 5.7 % |
| tree11 | 2628/1200/400/2 | 4.58/3.62/3.84 | 3.10/2.57/2.38 | -2.0 % | 3.2 | 2.6 / 4.0 % |
| tree18 | 2786/1204/418/2 | 4.19/3.30/3.60 | 3.15/2.37/2.16 | -2.6 % | 3.2 | 2.0 / 3.4 % |
| tree25 | 2118/1010/390/2 | 5.92/4.92/4.05 | 3.76/2.46/2.53 | -2.8 % | 2.1 | 3.5 / 1.4 % |
| tree31 | 2882/1212/434/2 | 4.66/3.47/3.29 | 3.39/2.22/2.19 | -4.0 % | 3.7 | 1.8 / 2.9 % |
| tree60a | 2806/1198/402/2 | 4.09/3.36/3.81 | 3.03/2.36/2.36 | -1.3 % | 3.5 | 2.4 / 4.9 % |
| tree13 | 2044/1032/390/2 | 5.99/4.91/3.06 | 3.57/2.63/2.15 | -5.2 % | 3.4 | 3.6 / 2.7 % |
| tree59 | 2700/1276/468/2 | 5.86/4.52/4.17 | 3.93/3.65/2.86 | -2.7 % | 2.6 | 2.9 / 10.0 % |
| tree61a | 3260/1200/400/2 | 3.01/2.26/2.80 | 2.59/1.85/1.85 | -2.3 % | 4.0 | 1.9 / 6.5 % |

The impostor is 1.0 layer everywhere. LOD-step coverage excludes the impostor (it sits within about 5 % of LOD0 but
can be 10-16 % above a thinner LOD2). Compromises: the open crowns (tree25, tree31, tree13) trade coverage against
layers almost one for one, so they sit slightly outside one gate each (tree25 LOD0 3.76 layers; tree31 -4.0 % and
3.39; tree13 -5.2 % and 3.57); the willow's hanging strands are outside any shell (LOD0/LOD1 3.9/3.7, LOD2 -10 %).

## State (2026-10-16, second pass): reduced and colour-lifted, all eleven re-installed

Second pass (coordinator, user-approved), over the same names, bindings unchanged:
1. **Triangle reduction** to ~3,000 at LOD0 (tree25 2,460, tree13 2,560, tree62a/tree61a 3,260, willow 3,360),
   ~1,130-1,330 at LOD1 and ~370-500 at LOD2, impostor unchanged. Each species generates exactly the v1 crown
   (`crown.gen_cards` pins the v1 card count, so the same rng sequence and the same clumps, cards and occlusion), then
   culls the cards least visible from outside (32 view rays per card, 8 azimuths x -25/0/25/50 degrees, through the
   other cards; best direction kept) down to the LOD0 budget; LOD1/LOD2 subsets come from the kept cards; the LOD2
   clump atlas still renders every generated card. Bark: one ring per Sapling segment at LOD0 (`bark.res_big` 1),
   8 sides only above 0.5 m and 6 above 0.25 m (`bark.sides`), lighter root spurs (`bark.root_mesh`), LOD2 bark
   4-sided, and the splines chosen thickest-first as the longest prefix that fits the budget (the old 12 % thickness
   steps dropped whole groups of similar limbs, leaving LOD2 a bare trunk). Gate (`scripts/gate.py` against
   `scripts/gate_baseline.py`, the v1 export rendered with the same framing): front LOD0 coverage within 3 % and mean
   colour within 2/255 of v1 before the colour lift; all eleven pass (coverage -0.5 to -2.5 %; tree62a/tree61a need
   `lod.tone[0]` 0.91/0.94 and LOD0 cards 5-6 % larger, `lod.grow[0]`, because their culled cards were partly visible).
2. **Colour lift** (`leaves.lift`, default for all): leaf tint +10 % saturation and +5 % value, and the most sunlit
   35 % of the cards ramp toward the sprites' yellow-green highlights (x 1.08 / 1.06 / 0.85; autumn, yellow and willow
   species keep more blue: 0.95-0.97). Leaf targets re-tuned so every crown's mean is within ~4/255 of its sprite.
3. **Bark UV fix** (from the MM7 trees_a session): Blender's curve UVs run u along the curve and v around it; the copy
   scaled them the other way, stretching the bark along every branch. Now swapped, bark tile 0.8 m both ways for
   every species (the per-species tiles, including tree18's 2 m workaround, are gone). Shared bark: low-frequency
   flattening widened (sigma 100 -> 400 px) to keep the mid-scale mottling, contrast exponent 0.25 -> 0.4; the shared
   leaf atlas is byte-identical to v1.

Sprites: the restored x2 images were retired from `assets_dev/engine/decorations_x2`; `common.SPRITES` now reads
`assets_legacy/decorations_x2_mm8_20261016/`. Before/after sheets: `review/<id>/before_after.png` (v1 row above the
current row, both with their LOD triangle counts); v1 sheets kept as `review/<id>/v1_*.png`, v1 configs as
`work/<id>/species_v1.json`. To change a species: edit `species/<id>.json`, `./build.sh <id>`, look at the sheets,
run `../animated/scripts/check_winding.py`, install. **Do not edit `build.sh` while a build runs.** Re-running
`make_shared.py` requires rebuilding and re-installing every species.

## Changes against the MM6 pipeline

- **Shared textures** (`scripts/make_shared.py` -> `shared/`): one 1024 bark set (Poly Haven bark_brown_01 graded to
  a light neutral brown; its low-frequency luminance divided out, since the scan's left half is lit brighter and
  wrapped a trunk with a light/dark split) and one 2048 leaf atlas of 4×4 cells of 512 px, each a maple spray for a
  ~1.2 m card (leaves 25–32 cm, the sprites' oversized maple leaves): cells 0–7 green maple (LeafSet010), 8–11 yellow
  maple (LeafSet027), 12–15 autumn mix (both sets: green, olive, yellow, orange, red). Leaves are recoloured per leaf
  from a palette keeping part of each leaf's own veins and blotches. Every GLB embeds the same bytes, so
  `tools/cook_models.py` (content-keyed textures) stores bark + leaves once for the whole batch; only the LOD2 clump
  atlas and the impostor (512² each) are per species. `atlas.json` holds each cell's mean colour.
- **Colour through COLOR_0**: `common.tints()` = species `leaves.target_srgb` / mean of its cells, and
  `bark.target_srgb` / bark mean (linear), multiplied into the occlusion vertex colours (leaves, bark, LOD2 clump
  cards, and so the impostor bake). Card occlusion peaks at ~0.6, so tints up to ~1.3 do not clamp.
- `occlusion.hue`: per-channel exponent on the leaf occlusion (red darkens faster), so shade turns deep green and lit
  tips yellow-green, as in the pre-rendered sprites.
- Crown options: `crown.underside` (the clump floor rises from `canopy_low` at the rim to this height at the axis:
  an open underside with the limbs showing), `crown.shell_radial` (shell clumps below the crown centre stay near the
  envelope), `crown.low_keep` (sparser lower crown); MM6's `flatten` / `card_up` give layered sprays.
- Bark: `bark.sides` thresholds scaled for 12 m trees (8 sides above 0.4 m, 6 above 0.15 m; the MM6 0.08 m threshold
  dropped every limb), `bark.root_lods` (no root spurs at LOD2, so its budget keeps the fork limbs).
- Impostor frame = 1.02 × max(height, width) (MM8 crowns can be wider than tall); the engine scales by LOD0's node
  bounds only, so the larger quad does not change the binding height. `impostor_edge_fill` on (no dark rim).
- LOD2 clump renders framed at 4.5 × clump radius (`lod.clump_frame`): large cards on small clumps were clipped at
  3 ×, showing straight edges.
- `bark.bend` [amplitude, cycles]: a lateral S-offset of the Sapling skeleton by height (tree13; Sapling's own
  trunk `curve`/`curveBack` left it straight). Willow strands (`crown.moss`, MM6 hanging strand cards): `anywhere`
  (start anywhere on a clump, draping over it), `keep` / `grow` (per-LOD strand share and width), `value` (per-strand
  value jitter), `depth` (darker toward the curtain's inside); strands take the species leaf tint and `occlusion.hue`.
- Budgets: LOD0 5000 (bark ≤1300), LOD1 2000 (bark ≤480), LOD2 800 (bark ≤330), LOD3 impostor quad.
- Sprites: restored x2 `assets_dev/engine/decorations_x2/<tex>_p337.png`; height from `../inventory.json` / 81.7.
- Install through `tools/install_model.py --engine` (`post_process.py --install`).

## Species

LOD triangles after `tools/cut_foliage_cards.py` (the impostor quad becomes 4 triangles cut to its outline). Δ = the
largest mean-colour difference (sRGB /255) and coverage change between neighbouring LODs (`work/<id>/lc_stats.json`).
Source GLBs are ~15.5-16.4 MB each (mostly the shared 2048 atlas and 1024 bark, stored once after cooking); the
cooked runtime GLBs are 0.42-0.61 MB plus their per-species textures.

| Id | Placements | Height | LOD triangles v1 -> now | Δ colour / coverage (LOD steps) | Crown mean vs sprite |
|---|---:|---:|---|---|---|
| tree12 | 389 | 944 | 4968/1968/784/2 -> 2960/1280/488/2 | 1.8 / 5.2 % | 59/79/26 vs 63/75/27 |
| tree10 | 342 | 992 | 4966/1976/784/2 -> 2960/1280/488/2 | 2.4 / 5.1 % | 54/88/19 vs 56/85/17 |
| tree62a | 260 | 1000 | 4960/1980/784/2 -> 3260/1280/488/2 | 1.7 / 3.3 % | 63/76/32 vs 63/75/33 |
| tree11 | 250 | 988 | 4960/1980/784/2 -> 2960/1280/488/2 | 2.2 / 5.0 % | 58/85/28 vs 60/83/30 |
| tree18 | 138 | 1000 | 4350/1870/884/2 -> 2960/1280/504/2 | 4.3 / 2.6 % | 95/88/31 vs 95/86/34 |
| tree25 | 111 | 500 | 3561/1474/608/2 -> 2460/1128/448/2 | 2.7 / 5.9 % | 98/86/41 vs 97/85/43 |
| tree31 | 79 | 952 | 4358/1880/888/2 -> 2960/1280/504/2 | 2.7 / 5.6 % | 100/87/19 vs 102/88/23 |
| tree60a | 77 | 1004 | 4970/1980/784/2 -> 2960/1280/488/2 | 3.4 / 4.0 % | 54/66/25 vs 52/62/25 |
| tree59 | 10 | 960 | 5156/2078/890/2 -> 3360/1330/506/2 | 2.4 / 5.7 % | 65/82/36 vs 63/79/38 |
| tree13 | 9 | 492 | 3959/1578/496/2 -> 2560/1178/368/2 | 4.2 / 7.3 % | 69/82/30 vs 71/81/31 |
| tree61a | 4 | 920 | 4964/1966/784/2 -> 3260/1280/488/2 | 2.3 / 4.8 % | 68/75/24 vs 67/72/28 |

The impostor counts as 2 triangles before `tools/cut_foliage_cards.py` cuts it to its outline (4 in the GLB).
Crown mean = LOD0 eye render (Eevee, sun + sky) against the sprite, sRGB. Review: `review/<id>/sheet.png`,
`before_after.png`.

- **tree12**: wide rounded crown from 31 % of the height, the underside rising to 52 % at the trunk so the
  spreading limbs show; thick straight trunk; olive leaves with yellow-green tips, deep green shade.
- **tree10**: tall oval crown of flattened lime sprays reaching low (19 %), conical top; thick brown trunk.
- **tree11**: tall dense oval crown from a quarter of the height, cooler mid-green; dark grey trunk, small flare.
- **tree62a**: round open crown of smaller sprays (1.0 m cards) on many thin limbs; slim light tan trunk.
- **tree60a**: as tree12 but darker olive-green and denser at the top, thick trunk with visible spreading limbs.
- **tree61a**: wide low dome from 13 % of the height on a short trunk forking into many upright stems.
- **tree18**: autumn multi-stem tree: four or five curving pale grey stems with side branches, an open crown of
  separate clusters; green maple cells mixed with the autumn cells (yellow-green with orange and red specks).
  Bark fix (2026-10-16, re-installed): the first target (160/152/142) gave a cool tint above 1 in blue that read as
  flat grey in game; now a warm grey-brown (156/134/112, tint 0.83/0.76/0.68) and a 2 m bark tile, so the furrows
  read as large flecks on the thin stems as in the sprite (at 0.8 m they averaged to one tone).
- **tree25**: small (6 m) autumn tree, reddish flared trunk forking at a quarter of the height, 0.7-0.85 m cards
  (smaller leaves), same green/autumn cell mix; a lower budget (3.6k).
- **tree31**: yellow maple: a see-through oval crown nearly to the ground around a slim dark leader.
- **tree13**: bonsai-like: an S-curved leaning trunk (`bark.bend`), separate flat pads in two height bands
  (`crown.tiers`), splayed roots; 4k budget.
- **tree59** (willow): arching limbs, ~55 small clumps in the upper crown and 1,050 hanging strand cards (2.1k
  triangles at LOD0; LOD1/LOD2 keep 45 % / 15 %, 1.45× / 2.4× wider) with a generated willow strand texture
  (`scripts/make_willow.py`, LeafSet018 leaves narrowed down hanging twigs), darker toward the curtain's inside.

Suggested bindings (`assets_dev/worlds/mm8/models/decorations.yml`), heights from the inventory; z_offset 0, random
yaw, no mount, swing or still (static models with leaf wind):

```yaml
  - name: tree12
    model: engine/models/mm8_deco_tree12.glb
    height: 944
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree10
    model: engine/models/mm8_deco_tree10.glb
    height: 992
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree62a
    model: engine/models/mm8_deco_tree62a.glb
    height: 1000
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree11
    model: engine/models/mm8_deco_tree11.glb
    height: 988
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree18
    model: engine/models/mm8_deco_tree18.glb
    height: 1000
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree25
    model: engine/models/mm8_deco_tree25.glb
    height: 500
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree31
    model: engine/models/mm8_deco_tree31.glb
    height: 952
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree60a
    model: engine/models/mm8_deco_tree60a.glb
    height: 1004
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree13
    model: engine/models/mm8_deco_tree13.glb
    height: 492
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree59
    model: engine/models/mm8_deco_tree59.glb
    height: 960
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree61a
    model: engine/models/mm8_deco_tree61a.glb
    height: 920
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
```

## Sources and licences

- Leaves: ambientCG [LeafSet010](https://ambientcg.com/view?id=LeafSet010) (green maple) and
  [LeafSet027](https://ambientcg.com/view?id=LeafSet027) (autumn maple), CC0, 1K PNG in `source/`.  The willow strands
  use [LeafSet018](https://ambientcg.com/view?id=LeafSet018) (CC0, narrowed). Also downloaded for evaluation, unused:
  LeafSet006/009/014/023/024 (CC0).
- Bark: Poly Haven [bark_brown_01](https://polyhaven.com/a/bark_brown_01), CC0, copied from the MM6 project's
  `source/`.
- Skeletons: Sapling Tree Gen (GPL tool; its output is ours). Atlases and everything else generated by the scripts.

## Compromises

- Review renders are Eevee (sun + sky); the sprites are pre-lit renders whose brightest lime/yellow tips exceed what
  an albedo ≤ 243 reaches under that light, so the brightest tips are a little duller (tree10 lum95 136 vs 179) and the
  deepest gaps less black (the sprites' holes are black, ours show the sky). In-game lighting decides the final look.
- Top bounds are 2-3 % above the sprite height (top cards); the engine scales by bounds, so the crown is ~3 % shorter
  relative to the trunk.
- Crowns are revolved envelopes: tree25's lopsided crown and tree13's one-sided pads become symmetric about the
  trunk (the trunk bend is in one plane, so tree13's lean follows its yaw).
- tree13's limbs are shorter and straighter than the sprite's long sweeping limbs; its pads read as round clumps.
  Tried 2026-10-16: longer, flatter Sapling limbs get clipped by the crown envelope into stubby cut ends; a real fix
  needs pads placed at the limb tips instead of in the envelope (not done). tree25's lopsided crown likewise needs a
  non-revolved envelope (not done).
- tree59 (willow): the upper crown carries maple sprays under the strands where the sprite has arched strands; the
  strand curtain is straight-hanging cards (edge-on from some angles).
- tree18's stems split at ground level rather than after the sprite's short common trunk.
- LOD2 clump cards read as flatter patches at close range; at their ~160-250 px switch sizes they match (as in MM6).
- Edge-on leaf cards show as short streaks in some views (as in the MM6 trees).
- Source GLBs are ~16 MB each because each embeds the shared 2048 atlas and 1024 bark; cooked, those are stored once.
