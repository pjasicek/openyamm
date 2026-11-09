# MM7 seasonal trees in 3D (batch `trees_seasonal/`, started 2026-10-15)

MM7 map events switch a placed tree's sprite through the seasons, so each family is one tree: the same Sapling skeleton
(trunk, limbs, root spurs, height) with summer leaves, autumn leaves or no leaves. Families (sprite → season):

| Family | Summer | Autumn | Winter (bare) |
|---|---|---|---|
| A | 7tree13 (164) | 7tree14 (2) | 7tree15 (2) |
| B | 7tree16 (198) | 7tree17 (2) | 7tree18 (2) |
| C | 7tree19 (233) | 7tree20 (2) | 7tree21 (3) |
| D | 7tree07 (73) | 7tree08 (1) | 7tree09 (1) |
| E | 7tree25 (288) | tree26 (3) | tree27 (3) |
| F | 7tree22 (14) | – | 7tree24 (1) |
| G | 7tree28 (43) | – | 7tree30 (65, also standalone and tree38's winter sprite) |
| H | tree37 (22, picked) / tree38 (24, with apples; `base` tree37 + `add_fruit.py`) | – | 7tree30 (native: a different tree) |

7tree22/24 are this batch's (the orchestrator confirmed; `trees_b/` does not build them).

## Status (2026-10-16): all 21 models installed

Installed with `tools/install_model.py --engine` as `engine/models/mm7_deco_<sprite>.glb` (source in
`assets_source/engine/models/`, cooked runtime copy in `assets_dev/engine/models/`). Every family shares its LOD0
bounds height to the millimetre (`scripts/family_check.py`: "FAMILIES consistent"), so one binding height gives every
season the same trunk. Review sheets: `review/family_<summer>.png` (one row per season: native x2 sprite at the
model's rendered height | LOD0 eye, three-quarter, side | LOD1 | LOD2 | LOD3), plus `review/<id>/compare.png`,
`occlusion.png` and `lod_consistency.png` per model, and `review/families_sprites.png` (all native sprites).

First install (2026-10-16 morning); the quality pass below replaced 20 of these (new LOD0 counts there; 7tree28 and
7tree30 are now 7.833 m).

| Sprite | Season | Placements | Model | LOD triangles | Source GLB | LOD0 height (m) |
|---|---|---:|---|---|---:|---:|
| 7tree13 | summer | 164 | `mm7_deco_7tree13.glb` | 5963 / 2380 / 756 / 2 | 9.5 MB | 7.616 |
| 7tree14 | autumn | 2 | `mm7_deco_7tree14.glb` | 5963 / 2380 / 756 / 2 | 9.6 MB | 7.616 |
| 7tree15 | winter | 2 | `mm7_deco_7tree15.glb` | 5362 / 2102 / 742 / 2 | 7.8 MB | 7.616 |
| 7tree16 | summer | 198 | `mm7_deco_7tree16.glb` | 5965 / 2372 / 884 / 2 | 9.6 MB | 7.959 |
| 7tree17 | autumn | 2 | `mm7_deco_7tree17.glb` | 5965 / 2372 / 884 / 2 | 9.7 MB | 7.959 |
| 7tree18 | winter | 2 | `mm7_deco_7tree18.glb` | 5678 / 2318 / 758 / 2 | 7.8 MB | 7.959 |
| 7tree19 | summer | 233 | `mm7_deco_7tree19.glb` | 5968 / 2380 / 872 / 2 | 9.5 MB | 7.867 |
| 7tree20 | autumn | 2 | `mm7_deco_7tree20.glb` | 5968 / 2380 / 872 / 2 | 9.4 MB | 7.867 |
| 7tree21 | winter | 3 | `mm7_deco_7tree21.glb` | 5027 / 2082 / 670 / 2 | 7.6 MB | 7.867 |
| 7tree07 | summer | 73 | `mm7_deco_7tree07.glb` | 6962 / 2680 / 936 / 2 | 9.8 MB | 8.714 |
| 7tree08 | autumn | 1 | `mm7_deco_7tree08.glb` | 6962 / 2680 / 936 / 2 | 10.0 MB | 8.714 |
| 7tree09 | winter | 1 | `mm7_deco_7tree09.glb` | 5287 / 2160 / 724 / 2 | 7.5 MB | 8.714 |
| 7tree25 | summer | 288 | `mm7_deco_7tree25.glb` | 5955 / 2358 / 884 / 2 | 9.8 MB | 8.030 |
| tree26 | autumn | 3 | `mm7_deco_tree26.glb` | 5955 / 2358 / 884 / 2 | 9.8 MB | 8.030 |
| tree27 | winter | 3 | `mm7_deco_tree27.glb` | 3468 / 814 / 464 / 2 | 7.2 MB | 8.030 |
| 7tree22 | summer | 14 | `mm7_deco_7tree22.glb` | 6951 / 2674 / 828 / 2 | 10.0 MB | 7.917 |
| 7tree24 | winter | 1 | `mm7_deco_7tree24.glb` | 4932 / 1944 / 726 / 2 | 7.7 MB | 7.917 |
| 7tree28 | summer | 43 | `mm7_deco_7tree28.glb` | 6958 / 2674 / 624 / 2 | 9.9 MB | 8.055 |
| 7tree30 | winter (and standalone) | 65 | `mm7_deco_7tree30.glb` | 5637 / 2368 / 746 / 2 | 7.6 MB | 8.055 |
| tree38 | apples | 24 | `mm7_deco_tree38.glb` | 6976 / 2608 / 864 / 2 | 9.7 MB | 6.156 |
| tree37 | picked | 22 | `mm7_deco_tree37.glb` | 6448 / 2480 / 824 / 2 | 9.7 MB | 6.156 |

Cooked runtime copies are 0.2–0.8 MB. LOD3 is the camera-facing impostor (`openyamm_billboard`). Bindings
(outdoor; height = the summer sprite's art height, equal within each family; MM6 tree LOD distances):

| Family | height | height_jitter | yaw | lod_pixels |
|---|---:|---:|---|---|
| 7tree13 / 14 / 15 | 1238 | 0.12 | random | [650, 320, 180] |
| 7tree16 / 17 / 18 | 1280 | 0.12 | random | [650, 320, 180] |
| 7tree19 / 20 / 21 | 1272 | 0.12 | random | [650, 320, 180] |
| 7tree07 / 08 / 09 | 1407 | 0.12 | random | [650, 320, 180] |
| 7tree25 / tree26 / tree27 | 1280 | 0.12 | random | [650, 320, 180] |
| 7tree22 / 7tree24 | 1280 | 0.12 | random | [650, 320, 180] |
| 7tree28 / 7tree30 | 1280 | 0.12 | random | [650, 320, 180] |
| tree38 / tree37 | 990 | 0.12 | random | [650, 320, 180] |

No `mount`, `swing`, `z_offset` or `still`: the sprites have one frame, and the models sway with `openyamm_wind`
(leaves 0.12, wood and twig cards 0.03) as the MM6 trees do. Random yaw and the jitter are seeded by the placement
position, so a season switch keeps the tree's size and orientation.

LOD consistency (Eevee, no shadows; mean colour Δ against the previous level in sRGB /255, worst channel; coverage
against LOD0): summers 7tree13 5.3 / 3.7 / 3.7 (0.97 / 0.95 / 0.93), 7tree16 5.1 / 8.1 at LOD2/3 (1.04 / 1.00),
7tree19 4.6 at most, 7tree07 7.5 / 11.1 at LOD2/3 (0.96 / 1.01), 7tree25 5.2, 7tree22 4.3, 7tree28 6.8 (LOD2
coverage 0.92), tree37/38 2.9. Bare trees: LOD1 keeps 72–83 % of LOD0's coverage at a common size (thin branches
become narrow cards), impostors 1.0–1.25×.


## Bark UV fix (2026-10-16)

`scripts/build_tree.py` (`branch_mesh`) and `scripts/bare_build.py` (`tube`) had the MM6 pipeline's swapped bark UV
axes. Blender's curve u runs along the curve, but it was scaled as if it ran around, so the furrows ran around every
trunk and limb (chevrons). Both scripts now swap the axes: u runs around the branch (whole tiles) and v along it
(1 tile per 0.8 m).

The 21 installed models (7tree07–09, 7tree13–25, 7tree28, 7tree30, tree26, tree27, tree37, tree38) were fixed in
place by `../../mm6_new_sorpigal_3d/trees/scripts/fix_bark_uv.py`, not rebuilt:
- Only the bark primitives' TEXCOORD_0 changed, on LOD0–2; root spurs were already right and stayed. Every other
  byte is identical, which keeps the reduction and the family bounds: every family's LOD0 bounds are unchanged and
  heights still match.
- Each model passes `check_winding.py` with 0 inverted parts.
- Previous sources are in `backup_pre_baruv/`. The before/after sheet is `review/bark_uv/bark_uv_before_after.png`.

## Quality pass (2026-10-16)

User: improve what benefits, and reduce triangles where it makes sense. 20 models reinstalled under the same names
(`--engine`, `check_winding.py`: 0 inverted closed parts on each); 7tree22 unchanged. Previous sources:
`backup_pre_quality/`. Sheets: `review/quality_pass_summer.png`, `review/quality_pass_winter.png` (sprite | before
| after, eye and three-quarter, from the GLBs: `scripts/glb_check.py`, `scripts/before_after_sheet.py`),
`review/winter_trees.png`, `review/family_*.png`. Bindings unchanged (heights and jitter as before); every family's
LOD0 heights still match (`scripts/family_check.py`).

**Reduction** (the seven common summer trees, their autumn twins and tree38; `reduce_family.sh`):
- Leaf cards: the darkest 15 % by COLOR_0 (the most hidden, inside the crown) dropped from LOD0
  (`scripts/thin_cards.py`), never a card at the LOD0 top or bottom; twins drop exactly the same cards.
- Bark: copies of the `../../mm6_reduce_pilot/` scripts (`deco_dump`, `deco_ladder` with a per-model temporary
  folder, `deco_build`, `deco_swap_glb`, which keeps the alpha primitives byte for byte); the ladder's lowest passing
  step (max ≤ 1.5 %, mean ≤ 0.15 % of the height); twins take the summer's reduced bark (and tree38 keeps `Fruit`).
- `scripts/pin_bounds.py`: the collapse lifted the lowest root tip by 3–21 mm; that vertex goes back to the original
  bottom so the family height rule holds. pymeshlab came from a scratch venv (`MESH_VENV`).
- LOD0 eye coverage −2.2 … −3.8 % (7tree28 +1 %, rebuilt), mean colour within 1.5 /255. LOD1–LOD3 unchanged.

| Model | LOD0 before | after | Ladder step (bark) |
|---|---:|---:|---|
| 7tree25 (+ tree26) | 5955 | 4867 | r70 |
| 7tree19 (+ 7tree20) | 5968 | 4464 | r45 |
| 7tree16 (+ 7tree17) | 5965 | 4645 | r55 |
| 7tree13 (+ 7tree14) | 5963 | 4423 | r35 |
| 7tree28 | 6958 | 5346 | r45 (also a slimmer trunk, below) |
| tree37 / tree38 | 6448 / 6976 | 4906 / 5434 | r45 |
| 7tree07 (+ 7tree08) | 6962 | 5272 | r35 |

**Winter trees** (`bare.gnarl` in `bare_build.py`, `bare_prepare.py`, `grade_bare.py`): below the fork the trunk and
root flare are unchanged; above it (ramped in over 1 m) the limbs are pulled toward the native bare sprite's
silhouette (`work/<id>/bare_profile.json`, per-height scale clamped 0.5–1.2), crooked by a smooth displacement field
(0.10–0.14 m, wavelength 0.9 m) and thickened 1.15–2.2×; splines thinner than 8–16 mm are dropped (fewer, heavier
branches); twig sprays are stubbier (two levels, 38 px strokes, kinked) and sit at branch ends. Bark graded to each
sprite (`grade_bare.py`: linear ratio of the sprite's mean colour to the LOD0 render, then rebuilt; contrast 1.6),
so they are darker and redder (e.g. 7tree30 eye mean 76/52/41 → 65/40/32 against the sprite's 62/36/27).
7tree28's trunk is slimmer (Sapling ratio 0.06 → 0.045, root flare 1.4 → 1.2): the 7tree30 sprite (65 placements)
has a slender trunk; 7tree28 was rebuilt and reduced again.

| Model | LOD0 before | after |
|---|---:|---:|
| 7tree15 | 5362 | 4924 |
| 7tree18 | 5678 | 5278 |
| 7tree21 | 5027 | 5165 |
| 7tree09 | 5287 | 4997 |
| tree27 | 3468 | 4306 (heavier limbs; was the sparse one) |
| 7tree24 | 4932 | 5238 |
| 7tree30 | 5637 | 5167 |

Stale lighting bakes: every MM7 map with these trees (7out02, 7out03, 7out04, out11, out14, 7d22) needs a re-bake.

## Compromises

- **Bare trees** are the summer skeleton, reshaped above the fork (quality pass): their limbs still taper to
  points and fork more regularly than the sprites' hand-painted ones. The bark texture is the family's own (shared with summer), tinted redder and darker
  through COLOR_0 (`bare.tone` 0.9 / 0.78 / 0.72), still lighter than the very dark red-brown sprites. Each bare tree
  ends in a thin tapered leader tube 0.35–0.97 m long so it reaches its summer model's top exactly (the height rule).
  tree27 (the slender 7tree25 skeleton) has few tube splines: LOD0 3468, LOD1 814 triangles.
- Native bare sprites are 86–96 % of their summer sprite's height in the game; ours keep one height per family.
- 7tree07's family: the native summer sprite is scaled 6 (1407 units) and its autumn/winter sprites 5 (1230/1280);
  one height (1407) for the family.
- tree38's winter switch goes to 7tree30, a different tree (as in the native game).
- Crown envelopes are symmetric (traced half-widths): lobed one-sided crowns (7tree13's low left lobe, 7tree22's two
  arms) become rounder; 7tree22 reads as a round crown. Summer crowns hide limbs that the sprites show between lobes.
- Autumn models keep the summer cards (same geometry), so their foliage is as dense as summer's; 7tree08 and tree26
  read slightly less saturated than their sprites in the review lighting.
- Apples (revision 2026-10-16, after the in-game check showed head-sized faceted polyhedra; the model is drawn at
  about 12 m, twice its 6.16 m build size): 22 / 16 / 10 apples of 6.5 cm radius (13 cm in game, half the previous
  size), LOD0 smooth UV spheres of 24 triangles (6 segments x 3 rings), LOD1 octahedra (8), LOD2 tetrahedra (4);
  placed on the crown's outer leaf shell (`fruit.shell`: rays from outside toward the crown centre, each apple centred
  on the first leaf card it meets, 0.7 m apart), so none floats past the outline; deep red [210, 14, 10], roughness
  0.6. Every fruit face winds outward (the MM6 `add_fruit.py` LOD2 tetrahedra were inside-out; checked with
  `../../mm8_3d/animated/scripts/check_winding.py`: 0 inverted closed parts). Close view: `review/tree38/fruit_close.png`
  (`scripts/close_fruit.py`). The apples still render a little pinker than the sprite's in Eevee.
- 7tree07 LOD2 needed a strong tone (1.40–1.47, per channel) to match LOD0's brightness; its LOD2/LOD3 green is
  7–11 /255 apart at a common size.
- Review renders fall back to Cycles on the CPU when the GPU has less than 2.5 GB free (`common.review_env`); those
  previews render the LOD2 clump cards about 30 % darker, so LOD statistics are only valid from Eevee runs (all
  numbers above are Eevee).
- Indoor placements: 7tree25 (3), 7tree19 (17), 7tree16 (5), tree38 (2), tree37 (1) also stand in `7d22.blv`; the
  models are lit for outdoors (no dungeon tint).
- Each GLB embeds its own bark/leaf maps (as the MM6 trees).

## Pipeline

A copy of the MM6 New Sorpigal species pipeline (`../../mm6_new_sorpigal_3d/trees/`, Sapling skeleton, leaf atlas,
clump cards, LOD2 clump cards, impostor LOD3) with these changes (`scripts/`):
- `common.py`: this batch's paths; sprites from `assets_dev/engine/decorations_x2/`; sources (bark, leaves) read from
  the MM6 `trees/source/`. A seasonal variant names its summer species in `family` and inherits all its settings
  (skeleton, crown, bark, envelope sprite); it overrides only its leaves (autumn palette) or sets `season: bare`.
  The rebuild is deterministic, so a variant's trunk, clumps and cards are identical to the summer's.
- Models are built at half world scale (`height_m` = art height ÷ 163.4 m): the sprites paint leaves about twice real
  size, and the MM6 crown settings (clump radii, card sizes) then apply unchanged. The engine scales to the binding
  height anyway.
- `bare_prepare.py` + `bare_build.py`: the winter state from the family's own Sapling skeleton: tubes as in
  `build_tree.py` (no crown-envelope cut, budget by a rising minimum thickness), the summer root spurs, twig cards
  (procedural twig atlas after the MM6 `dead_prepare.py`) along thin branches and at thin branch ends, sky-ray
  occlusion against the wood. **Height rule**: the engine scales a model so its LOD0 bounds height is the binding
  height, and a family shares one binding height, so the bare tree must reach exactly the summer model's LOD0 top
  after the card cut (`work/<family>/model.json`): cards stay under it and a thin tapered leader tube grows from the
  highest branch end to exactly that top. Root spurs give the same lower bound.
- `bake_impostor.py`: the square impostor frame covers crowns wider than tall. `finish_impostor.py`:
  `impostor_dilate` 0 keeps the cutout undilated (bare trees: a dilated twig network doubled the far coverage).
- `post_process.py`: bare-tree materials (`Bark`, `Twigs`, `Impostor`), LOD0 bounds after the card cut in
  `model.json`, install through `tools/install_model.py --engine`.
- `shrink_far_maps.py`: bare impostors keep 1024².
- `review.py`, `lod_check.py`: Cycles CPU fallback when the GPU is short of memory (`common.review_env`).
- Tools: `family_check.py` (equal LOD0 heights per family, suggested bindings), `skeleton_preview.py` / `skel.sh` (skeleton silhouettes against the family's sprites), `fit_scale.sh` (Sapling
  scale so the skeleton top is 0.96 of the height; Sapling's `baseSplits` always fork at the first trunk segment, so a
  mid-trunk fork uses `segSplits[0]` > 0 with `splitHeight`), `family_strip.py`, `sprite_families.py`
  (`review/families_sprites.png`), `family_sheet.py`, `build_many.sh`.

```bash
./build.sh <id> [--install]            # one model; bare and fruit variants need their family's built summer
JOBS=3 ./build_many.sh <id>... [-- --install]
python3 scripts/family_check.py         # every family: equal LOD0 heights; prints the bindings
python3 scripts/family_sheet.py <summer> [<autumn>] <bare>
```
Rebuild order: a summer species first (its `model.json` sets the bare tree's top), then its autumn and bare variants;
tree37 before tree38. A summer settings change (skeleton, crown, tone) means rebuilding the whole family.

## Sources and licences

- Leaves: ambientCG LeafSet022 (CC0); bark: Poly Haven bark_brown_01 (CC0), both from the MM6 trees `source/`.
- Twig atlas, fruit: procedural (ours). Sapling Tree Gen (GPL) is a tool; its output is ours.
