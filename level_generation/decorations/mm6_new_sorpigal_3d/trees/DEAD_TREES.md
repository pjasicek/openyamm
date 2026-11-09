# MM6 dead trees, swamp tree and stump — bare-wood 3D decorations (2026-10-09)

Five bare-wood MM6 decorations, built by a procedural branch generator that is separate from the living-tree
Sapling pipeline (`scripts/common.py`, `species/` and the other `scripts/*.py` are unchanged). Not bound yet
(`decorations.yml` untouched). [Overview: every sprite next to LOD0 from three sides](review/dead_overview.png).

| Sprite | Installed GLB (`assets_dev/worlds/mm6/models/`) | LOD triangles | File | Look |
|---|---|---|---|---|
| `6tree28` | `mm6_deco_tree28.glb` | 5749 / 2455 / 849 / 2 (impostor) | 11.6 MB | grey pine snag, trunk snapped at 80 % with a pale stripped strip and broken top, thin leader above |
| `6tree27` | `mm6_deco_tree27.glb` | 6398 / 2563 / 852 / 2 (impostor) | 12.7 MB | grey snag, many drooping limbs with dense side twigs, pointed top |
| `6tree29` | `mm6_deco_tree29.glb` | 2360 / 896 / 320 / 2 (impostor) | 2.1 MB | dark grey shrub of bunched, forking upright stems |
| `swptree4` | `mm6_deco_swptree4.glb` | 8491 / 3362 / 1390 / 2 (impostor) | 7.5 MB | green gnarled tree on a root skirt with four black hollows; pitted bark, native shading in its vertex colours (revision 2) |
| `stump5a` | `mm6_deco_stump5a.glb` | 1820 / 630 / 234 / 81 (all geometry) | 6.9 MB | cut stump with a stepped top, end grain and nine flared root lobes |

Suggested bindings (heights from the sprite pixels × DSFT scale, as the other models):

| name | height | height_jitter | yaw | z_offset | lod_pixels |
|---|---:|---:|---|---:|---|
| `6tree28` | 287 | 0.12 | random | 0 | [650, 320, 180] |
| `6tree27` | 292 | 0.12 | random | 0 | [650, 320, 180] |
| `6tree29` | 117 | 0.15 | random | 0 | [360, 180, 90] |
| `swptree4` | 589 | 0.1 | random | 0 | [650, 320, 180] |
| `stump5a` | 72 | 0.15 | random | -2 | engine default (no impostor) |

## Build

```bash
cd level_generation/decorations/mm6_new_sorpigal_3d/trees/scripts
./dead_build.sh <id> [--install]       # 6tree28, 6tree27, 6tree29, swptree4, stump5a; ~1-2 min, ids run in parallel
```

Settings per id live in `scripts/dead_common.py` (`SPECIES`: kind, sprite, output, world height, bark source and
grade, twig colours, per-level tone, budgets, LOD tones, impostor tone). Work files: `work/dead_<id>/`; review sheets:
`review/dead_<id>/compare.png` (native sprite | LOD0 eye level | three-quarter | back) and `lods.png` (every level
without shadows at a common size with mean colour and coverage, and at about its in-game size; numbers in
`work/dead_<id>/lod_stats.json`).

Steps (`dead_build.sh`): `dead_fetch.py` (Poly Haven sets, skipped when present) → `dead_prepare.py` (sprite
profile, graded bark / wood maps, procedural twig atlas or stump end grain) → `dead_build.py` (Blender: skeleton,
tubes, cards, occlusion, LODs) → `dead_impostor.py` + `dead_finish_impostor.py` (trees only) → `dead_export.py` →
`dead_post.py` (material modes, `tools/link_static_model_lods.py`, validation, `tools/cut_foliage_cards.py`,
install) → `dead_review.py` (renders with `dead_render.py`, framed on the larger of height and width).

## Construction

- **Contract**: glTF Y-up metres, origin at the base centre, one node `Tree` with `openyamm_lods`, COLOR_0 on every
  primitive (linear occlusion × per-level tone). Materials: `Bark` and `Wood` opaque single-sided; `Twigs` and
  `Impostor` MASK 0.5 double-sided with `openyamm_specular` 0.1. Wind is the same on every wood and twig material
  (snags 0.04, shrub and swamp tree 0.03, stump none): the engine sways by height, so equal wind keeps twig cards on
  their branches. The impostor is the living trees' camera-facing quad (`openyamm_billboard`), 512².
- **Tubes**: polylines grown step by step (gravity, up-attraction, noise, sinuous curl), smoothed by two rounds of
  corner cutting, then swept with parallel-transport rings; u wraps the bark texture a whole number of times around,
  v follows the arc length. Ends taper in a short cone (blunt, not spiked); a branch whose children are all dropped at a
  coarser level tapers off instead of showing an open cut; broken ends get a jagged `Wood` cap.
- **Twig cards** (finest level): a 2 × 2 atlas of procedurally painted sprays (dark twigs with a pale lit edge, as the
  sprites draw them), base at the bottom centre of each cell, attached along the finest geometric twigs, rolled
  about the twig at random from the vertical plane; shading normals point outward and up. Each card belongs to its
  branch and disappears with it.
- **LODs**: sides and ring spacing coarsen per level; then branches are dropped by importance (length × base radius,
  lowest first, threshold raised in 8 % steps) until the budget holds, each dropped branch whose parent survives
  replaced by one card along its chord. LOD1/LOD2 keep 55 % / 20 % of the LOD0 cards, grown 1.3× / 1.9×.
- **Occlusion**: per vertex, 24 rays over the hemisphere around the normal against the LOD0 wood (the ground blocks
  downward rays), floor + range by kind, a ground term near the base; twig cards take it at their centre.
  Per-level tones (`tone_by_level`) darken limbs and twigs against the pale trunks, as in the sprites.
- **6tree28 / 6tree27 (snag)**: whorled level-1 branches on a golden-angle spiral whose length follows the sprite's
  smoothed silhouette, rising near the top and drooping below (27 droops more), ~20 % / 10 % broken stubs with pale caps,
  level-2 twigs alternating in the branch plane, cards at their tips and sides plus spurs on the limbs. 6tree28's
  trunk snaps at 80 % of the height (jagged pale cap) with a stripped pale strip on one side (`Wood`, Poly Haven
  `rough_wood` graded tan) and a thin leader continuing to the top; seven buttress roots.
- **6tree29 (shrub)**: eight stems bunched at a small base, upright with strong up-attraction, forking two or three
  levels deep into blunt Y tips, an occasional side shoot; 5-sided stems at LOD0; bark `rough_wood` graded to a
  mottled dark grey (contrast 2.3); maps 512².
- **swptree4 (gnarled)**: a concave root skirt (42 % of the height, lumpy in plan and height, toned 0.62 for the shade
  between roots) with five hollows pushed in and darkened to near black, each ringed by a thick root rim; 20 long
  roots from inside the trunk winding down the skirt round the hollows and out over the ground, 12 shorter ones in
  the lower band and five arches; a leaning S-curved trunk forking into four wavy knobby limbs that fork two or three
  ways down to twigs (sides by level 10/8/6/5/4/3). Roots count 0.4× in the importance ordering, so coarse levels keep
  the crown before the lesser roots. Bark (revision 2, below) Poly Haven `coral_mud_01`.
- **stump5a**: a radial grid whose radius combines a slightly tapering trunk, a convex flare from 60 % of the height
  and nine root lobes (a smooth union: a plain max creased the bark), root ends rounding over onto the ground, gentle
  low-frequency lumps (the first version's high-frequency fibre noise aliased against the columns into spikes). Rows
  stay level up to the cut; the top ring follows a stepped cut with splinters, capped by an inset rim and a fan in
  `Wood` (procedural end grain: rings, radial cracks, a rotten dark centre, a weathered pale rim; 512²). LOD2/LOD3 put
  their columns on the root lobes (18 / 9 columns), so the lobes survive. Bark `bark_willow_02` graded grey-brown
  with high contrast.

### swptree4 revision 2: native shading and pitted bark (2026-10-09, gallery review)

The user found the model "flat green" next to the sprite's shaded roots and branches with holes, and suggested
native shading or more texture. Both, gated by `native_shading` in its `SPECIES` entry (the other ids are untouched:
a rebuild of `6tree29` after these changes reproduced its installed GLB byte for byte):
- **Bark texture**: Poly Haven `coral_mud_01` (CC0), a pitted, lumpy surface like the sprite's pocked bark, used as
  luminance detail only (`grey`), graded with AO² and height (`ao_gain`, `height_gain`), compressed (`contrast`
  0.85, below 1 needs the new zero guard in `dead_prepare.graded`) and scaled to the sprite's light green
  (86/164/96), tiled every 0.5 m. `moss_wood` read as planks with a few cracks.
- **Native shading transfer** (`level_generation/creatures/NATIVE_SHADING_TRANSFER.md`), adapted to a tiled bark
  where the texture cannot carry it: `dead_prepare.native_ramp` sorts the sprite's opaque core pixels by luminance
  into a 32-stop colour ramp (near black 1/10/2 to 100/177/110) and a height profile (the root mound is slightly
  darker); `dead_build.native_colours` gives every vertex a shading value (sky visibility and hollow tones, × an
  up-facing term `up` 0.7, × the height profile), ranks it by surface area against LOD0's values (every level uses
  LOD0's ranks, so levels match), and takes the sprite colour at that rank (`quantiles` 0–0.93, `chroma` 1.1 against
  the gallery's tone mapping). COLOR_0 = that colour / the bark texture mean, so the texture keeps only its fine
  pits; a slow positional noise (`moss` 0.12) shifts red and blue for moss patches. The skirt between the roots is
  toned 0.3 (`skirt`, was 0.62).
- **Black hollows** (`pit_cups`): a shallow black funnel over each hollow, its rim just outside the undented skirt
  under the root rim. The skirt's coarse rows put too few vertices in a hollow for vertex colour alone (the
  revision-1 renders showed dark hollows only through Eevee's occlusion, which the engine does not have).
- LOD tones `[1.0, 1.1, 1.14]` (mean colour Δ now 3.7 / 2.1 / 7.8 against the previous level; the impostor is
  +2 against LOD0).
Gallery before/after: `review/dead_swptree4_rev2/`. Re-bake `outa3` and `outc3` (its outdoor maps).

## LOD consistency (Eevee, no shadows, eye camera; mean colour Δ in sRGB /255, coverage vs the previous level)

| Id | LOD1 | LOD2 | LOD3 |
|---|---|---|---|
| 6tree28 | 0.4 / −7 % | 0.6 / −14 % | 0.5 / +49 % (impostor) |
| 6tree27 | 0.8 / −4 % | 2.7 / −11 % | 2.3 / +34 % (impostor) |
| 6tree29 | 2.0 / −3 % | 0.2 / −29 % | 2.8 / +48 % (impostor) |
| swptree4 | 3.7 / −7 % | 2.1 / −15 % | 7.8 / +6 % (impostor; +2 against LOD0) |
| stump5a | 1.3 / −3 % | 3.1 / +1 % | 1.7 / −2 % |

Bare branches thin out at a common render size more than leafy crowns do; at in-game sizes (lods.png, lower row) the
levels read alike. The impostor keeps LOD0's full twig network (no cutout dilation: a dilated cutout merged the twigs
into dark blobs), so it is fuller than LOD2.

## Sources and licences

- Bark/wood: Poly Haven [rough_wood](https://polyhaven.com/a/rough_wood),
  [bark_willow_02](https://polyhaven.com/a/bark_willow_02), [moss_wood](https://polyhaven.com/a/moss_wood),
  [coral_mud_01](https://polyhaven.com/a/coral_mud_01) (swptree4 bark since revision 2, by Rob Tuytel) (CC0,
  2k PNG in `source/<asset>/`, fetched by `dead_fetch.py`), and the existing
  [bark_brown_01](https://polyhaven.com/a/bark_brown_01) (CC0) in `source/`.
- Twig atlas and stump end grain: generated procedurally (`dead_prepare.py`). Poly Haven `tree_stump_01/02` scans
  were considered for the stump but include a ground mound and no flared roots.

## Compromises

- Snag root flares read as a few distinct buttress spurs rather than the sprites' gnarled splayed base.
- 6tree28's stripped strip and broken top are on one side only; under random yaw some placements show the plain
  grey side. 6tree27 is about 8 % taller than wide compared with the sprite (bound by height, it is slightly narrower).
- The shrub is cleaner and less bushy than the sprite's tangled mass; its LOD2 (320 triangles) loses about 30 % of the
  coverage at a common size (use a small `lod_pixels`).
- swptree4: the sprite's tangle of interwoven roots is approximated by draped tubes over a smooth skirt; from most
  sides one or two hollows show. LOD1/LOD2 lose the finest crown forks (LOD2 keeps the main limbs).
- The stump's flare stretches the bark texture radially on the lowest root lobes.
- Review lighting is Eevee, not the engine; check in game once bound (maps must be re-baked for shadows).
