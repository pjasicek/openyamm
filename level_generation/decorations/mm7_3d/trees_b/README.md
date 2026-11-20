# MM7 3D trees, batch B (2026-10-15/16)

Eight MM7 outdoor tree sprites as static 3D models, built for the MM7 3D decorations project (`../BRIEF.md`,
`../README.md`). The seasonal families (7tree07–22, 7tree24, 7tree28, 7tree30, tree26, tree27) are the seasonal
builder's, not this batch's. All eight models are installed and bound in `assets_dev/engine/models/decorations.yml`
(engine content, not edited by this batch). The quality pass of 2026-10-16 (below) changed every model except 7tree06;
the binding values did not change.

| Sprite | Placements (maps) | Installed (`engine/models/`) | LOD triangles (0 / 1 / 2 / impostor) | Source GLB | Runtime (cooked) | Review sheet |
|---|---:|---|---|---:|---:|---|
| tree41 | 302 (7out05, out09, out11, out12) | `mm7_deco_tree41.glb` | 2600 / 1243 / 784 / 2 (LOD0, LOD1 reduced) | 6.8 MB | 0.20 MB | `review/tree41.png` |
| tree42 | 256 (7out05, out09, out11, out12) | `mm7_deco_tree42.glb` | 4238 / 2374 / 799 / 2 (LOD0 reduced) | 7.1 MB | 0.32 MB | `review/tree42.png` |
| 7tree06 | 1 (out11) | `mm7_deco_7tree06.glb` | 5511 / 2574 / 880 / 2 | 6.9 MB | 0.38 MB | `review/7tree06.png` |
| tree66 | 4 (7out01) | `mm7_deco_tree66.glb` | 6960 / 2680 / 660 / 2 | 10.2 MB | 0.81 MB | `review/tree66.png` |
| 7tree05 | 1 (out11) | `mm7_deco_7tree05.glb` | 6956 / 2680 / 792 / 2 | 9.9 MB | 0.80 MB | `review/7tree05.png` |
| 7tree29 | 1 (7out03) | `mm7_deco_7tree29.glb` | 6958 / 2680 / 408 / 2 | 9.7 MB | 0.78 MB | `review/7tree29.png` |
| tree23 | 1 (7out02) | `mm7_deco_tree23.glb` | 6956 / 2680 / 560 / 2 | 9.9 MB | 0.78 MB | `review/tree23.png` |
| tree69 | 1 (7out04, scale 8) | `mm7_deco_tree69.glb` | 6974 / 2674 / 888 / 2 | 10.0 MB | 0.79 MB | `review/tree69.png` |

The budgets are 6000 LOD0 triangles for tree41 and tree42 (100+ placements) and 7000 for the rest. The cut
impostor quad has 4 triangles. Each review sheet shows the native x2 sprite, then LOD0 from the front, three-quarter
and side, then every level from the front. Older per-step sheets are in `review/<id>/` and `review/dead_<id>/`
(`compare.png`, `lods.png` or `lod_consistency.png`).

## Bindings (outdoor, now in `assets_dev/engine/models/decorations.yml`)

Heights are the sprite's `art_height`, scaled by the model's bounds height over its height above the ground, because
the bare trees' root tips reach a few centimetres below the origin. So the visible tree is as tall as the sprite art.
No sprite is animated (one frame each), so no binding needs `still`. Wind sways the leaves and wood.

```yaml
  - name: tree41
    model: engine/models/mm7_deco_tree41.glb
    height: 1150
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree42
    model: engine/models/mm7_deco_tree42.glb
    height: 1288
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: 7tree06
    model: engine/models/mm7_deco_7tree06.glb
    height: 1198
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree66
    model: engine/models/mm7_deco_tree66.glb
    height: 1280
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: 7tree05
    model: engine/models/mm7_deco_7tree05.glb
    height: 1255
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: 7tree29
    model: engine/models/mm7_deco_7tree29.glb
    height: 1280
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree23
    model: engine/models/mm7_deco_tree23.glb
    height: 1280
    height_jitter: 0.12
    lod_pixels: [650, 320, 180]
  - name: tree69
    model: engine/models/mm7_deco_tree69.glb
    height: 2055
    height_jitter: 0.08
    lod_pixels: [650, 320, 180]
```

All other fields keep their defaults: random yaw, no `mount` or `free_model`, no `swing`, `z_offset` 0. Re-bake
7out01–7out05, out09, out11 and out12 once these are bound.


## Bark UV fix (2026-10-16)

`scripts/build_tree.py` (`branch_mesh`) had the MM6 pipeline's swapped bark UV axes: Blender's curve u runs along
the curve but was scaled as if it ran around, so the furrows ran around every trunk and limb. It now swaps them: u
runs around the branch (whole tiles) and v along it (1 tile per 0.8 m).

The five installed leafy trees (tree66, 7tree05, 7tree29, tree23, tree69) were fixed in place by
`../../mm6_new_sorpigal_3d/trees/scripts/fix_bark_uv.py`:
- Only the bark TEXCOORD_0 changed; every other byte is identical.
- Each model passes `check_winding.py` with 0 inverted parts.
- Previous sources are in `backup_pre_baruv/`. The before/after sheet is `review/bark_uv/bark_uv_before_after.png`
  (shared with trees_seasonal).

The bare trees tree41, tree42 and 7tree06 (`dead_build.py`, traced tubes) already map u around and v along. The
fixer found no swapped tubes on them, so they were not changed.

## Quality pass (2026-10-16)

The coordinator asked for improvements from the in-game captures (`output/mm7_deco_outdoor_20261016/`) and for
triangle reduction. The previous sources are backed up in `backup_20261016/`. Reference sprites now come from
`assets_legacy/decorations_x2_20261016/` (`SPRITES` in `scripts/common.py` and `scripts/dead_common.py`). Every
reinstalled GLB passed `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py` with 0 inverted parts.

| Model | LOD triangles before | LOD triangles after | Changes |
|---|---|---|---|
| tree41 | 4494 / 2144 / 793 / 2 | 2600 / 1243 / 784 / 2 | depth balanced and limited (side view as wide as the front); LOD0 reduced 45 %, LOD1 45 % |
| tree42 | 5937 / 2386 / 784 / 2 | 4238 / 2374 / 799 / 2 | main limbs thicker; the dark hollow at the fork; depth balanced; LOD0 reduced 29 % |
| tree66 | 6960 / 2680 / 660 / 2 | 6960 / 2680 / 660 / 2 | lighter crown interior; LOD2 tone matched |
| 7tree05 | 6956 / 2680 / 792 / 2 | 6956 / 2680 / 792 / 2 | lighter crown interior; LOD2 tone matched |
| 7tree29 | 6958 / 2680 / 408 / 2 | 6958 / 2680 / 408 / 2 | lighter crown interior; LOD2 tone matched |
| tree23 | 6962 / 2676 / 760 / 2 | 6956 / 2680 / 560 / 2 | lighter crown interior; two-lobed crown (crown masses); oranger palette; LOD2 tone matched |
| tree69 | 6962 / 2680 / 888 / 2 | 6974 / 2674 / 888 / 2 | lighter crown interior; separate crown masses with limbs between them |
| 7tree06 | 5511 / 2574 / 880 / 2 | unchanged | not touched (one placement) |

LOD0 against the sprite, in sRGB means:

| Tree | Before | After | Sprite |
|---|---|---|---|
| tree66 | 69/84/52 | 77/93/58 | 78/93/59 |
| 7tree05 | 68/68/27 | 76/76/30 | 81/74/31 |
| 7tree29 | 85/45/44 | 95/49/48 | 93/49/46 |
| tree23 | 100/72/21 | 107/66/21 | 120/73/8 |
| tree69 | 60/92/38 | 66/99/41 | 57/106/38 |

The leafy LODs stay within 5.8/255 of LOD0.

- **Bare-tree depth** (`dead_build.py` `make_traced`):
  - The children of each axis are signed heaviest first (drawn length × base radius), each leaning to the side that
    keeps their weighted depth sum nearest zero. Before, siblings simply alternated.
  - No limb reaches deeper than half the drawn crown width (`trace.depth_limit`, default 1). A long drawn limb with a
    steep slope had made tree41 lopsided.
  - tree41: depth extent −7.8…+5.6 m against a drawn width of −7.5…+8.1 m (before, 5 m deep at the side).
    `trace.depth` is now [0.5, 1.05].
- **tree42 limbs:** `trace.limb_scale` [1.3, 1.25, 1.12] multiplies the level-1/2/3 radii.
- **tree42 hollow:**
  - `trace.hollow` [0.09, 6.19, 0.75, 0.85] m sits at the sprite's near-black blob, at (236.7, 308.8) px. Its patch
    is an oval laid 5 cm in front of the bark on the model's front (−y), found by rays.
  - The patch is black at the centre and fades out over its rim. Its colours are applied after native shading
    (`MeshOut.paint`), so they stay dark.
  - 12/8/6 segments per LOD; the impostor bakes it.
- **Reduction (tree41, tree42):** the `mm6_reduce_pilot` route, copied into `scripts/reduce/` with path arguments.
  - Steps: `deco_dump.py` on the post-processed work GLB, then `deco_ladder.py` (pymeshlab texture-aware collapse,
    two-way Hausdorff), `deco_build.py` (reduced Bark faces, untouched twig cards, colour transferred) and
    `deco_swap_glb.py` (LOD0 swapped, LOD1–3 kept).
  - pymeshlab ran in a scratch venv (`python3 -m venv`, `pip install pymeshlab numpy`).
  - The pilot's limits are a maximum of 1.5 % and a mean of 0.15 % of the height.

    | Tree | Pick | Max / mean | Next step (fails) |
    |---|---|---|---|
    | tree41 | r55 | 0.95 % / 0.125 % | r45: 1.42 % / 0.175 % |
    | tree42 | r70 | 0.89 % / 0.084 % | r55: 1.66 % / 0.143 % |

  - Before/after renders: `work/reduce/{orig,red}4{1,2}_Tree_{eye,side}.png`. tree41 at r70 (3310) was rendered too
    and was indistinguishable from r55.
  - tree41's LOD1 was then reduced too, from 2263 to 1243 (follow-up, 2026-10-16). `scripts/reduce/lod_extract.py`
    writes LOD1 as a standalone GLB for the same ladder, and `scripts/reduce/lod_swap.py` swaps the reduced level
    back in.
    - The pick is r55: max 1.92 %, mean 0.24 % of the height. That is over the LOD0 limits but within double them,
      since LOD1 is shown at half LOD0's screen size or less (`lod_pixels` 650 → 320). r70 (1583) passed the LOD0
      limits but saved too little.
    - Against LOD0: coverage 0.945 and a colour difference of 2.6/255. The old LOD1 was at 0.997 and 4.5/255.
      LOD2 is at 0.892 and 1.8/255.
    - Sheet: `review/tree41_lod1_reduction.png` (LOD0, old LOD1, new LOD1, LOD2).
- **Leafy crown light** (`build_tree.py` `local_term`): `occlusion.local_floor` (default 0.28) and `core_floor`
  (default 0.6) brighten the clump undersides and cores. The five trees use floor 0.55, range 0.45, power 1,
  local 0.45, core 0.72. `lod.tone` [1.0, 0.92, 0.99] (LOD2 had been 6–7/255 brighter).
- **Crown masses** (`crown.masses`, `build_tree.py`):
  - Each mass is an ellipsoid `[x, y, z, r_horizontal, r_vertical]`, in fractions of the height, read off the
    sprite. Clump centres must lie inside one of them, and the crown envelope is widened to reach the off-centre
    masses.
  - tree23 has five masses: the main left lobe, the right lobe, a low left skirt, a small low right mass and a back
    mass for depth.
  - tree69 has five: left, centre-left, top, right and a back mass, so its clumps form separate groups with the
    limbs showing between them.
  - tree23's palette lost 14 % of its green, for a redder orange.

## Bare trees: traced from the sprite (tree41, tree42, 7tree06)

MM7's bare trees draw every limb, so each model follows its own drawing rather than a generic branch generator:
- **`scripts/trace_skeleton.py`** finds the branches in the sprite:
  - It thins the sprite's mask (alpha ≥ 96, pin holes filled) and builds a graph of forks, tips and segments, with
    short spurs pruned.
  - From the trunk foot, it keeps the cheapest paths, where a segment's cost is its length divided by its thickness
    squared. So the tree runs through the thick limbs, and the loops made by crossing branches open at their thinnest
    segment. Each loop segment is split into two tapering twigs.
  - At every fork, the thickest and best-aligned child continues the parent's axis. Radii come from the distance
    transform (×1.2, ×1.1 for tree42, ×1.0 for 7tree06). Drawn tips are extended to the drawn end, and axes that end
    thick taper off.
  - The output is `work/dead_<id>/skeleton.json`, with a debug overlay in `skeleton.png`.
- **`dead_build.py`, kind `traced`**, turns the skeleton into 3D:
  - The drawn x and z are kept, so the front view keeps the sprite's silhouette and branching.
  - Each axis leans out of the picture plane by its own slope (`trace.depth`). The signs are balanced by limb weight,
    axes that start far off the plane lean back toward it, and depth is limited to half the drawn width (see the
    quality pass). tree42 also has thicker main limbs (`limb_scale`) and its painted hollow (`hollow`).
  - Tubes take their side count and ring spacing from the axis' mean radius. Knobby radius noise (`knob`,
    `knob_freq`) gives the gnarl, and a few root spurs flare the base.
  - The rest is the MM6 dead-tree code: LOD branch dropping by importance (each dropped branch becomes a twig card),
    sky occlusion, impostor, export and validation.
- **Colour.** Bark texture is Poly Haven `coral_mud_01`, used as luminance only and tiled every 2.2 m for the sprite's
  pitted lumps. 7tree06 uses `bark_willow_02`. The colour comes from native shading transfer (`native_shading`, as in
  the MM6 swamp tree): each vertex's sky visibility and up-facing value picks a colour from the sprite's own
  luminance ramp. LOD0 against the sprite, in sRGB means:
  - tree41: 58/37/29 against 60/39/28;
  - tree42: 67/43/32 against 73/45/32 (darker since the hollow and thicker limbs);
  - 7tree06: 95/66/51 against 89/58/44.
- **Twig cards.** Atlas cards stand in for dropped branches only, with thicker, crooked twigs than the MM6 snags.
  tree41 needs no cards at LOD0. tree42 drops 97 of its finest twigs at LOD0 to stay within 6000 triangles.
- Settings are in `scripts/dead_common.py`. Rebuild with `cd scripts && ./dead_build.sh <id>`. tree41 and tree42 are
  then reduced and installed as follows, with `V` a venv with pymeshlab and `W` the absolute path of `work/`:

  ```bash
  blender -b -P scripts/reduce/deco_dump.py -- tree41=$W/dead_tree41/mm7_deco_tree41.glb tree42=$W/dead_tree42/mm7_deco_tree42.glb
  $V/bin/python scripts/reduce/deco_ladder.py tree41 tree42
  blender -b -P scripts/reduce/deco_build.py -- tree41:r55:$W/dead_tree41/mm7_deco_tree41.glb tree42:r70:$W/dead_tree42/mm7_deco_tree42.glb
  python3 scripts/reduce/deco_swap_glb.py work/dead_tree41/mm7_deco_tree41.glb work/reduce/tree41_lod0.glb work/reduce/mm7_deco_tree41_reduced.glb
  python3 scripts/reduce/deco_swap_glb.py work/dead_tree42/mm7_deco_tree42.glb work/reduce/tree42_lod0.glb work/reduce/mm7_deco_tree42_reduced.glb
  tools/install_model.py work/reduce/mm7_deco_tree41_reduced.glb --engine --name mm7_deco_tree41.glb   # same for tree42
  ```

  `python3 scripts/review_sheet.py tree41 --reduced <installed source>` renders LOD0 from the reduced GLB.

## Leafy trees: Sapling pipeline (tree66, 7tree05, 7tree29, tree23, tree69)

These use the MM6 New Sorpigal species pipeline, copied into `scripts/`, with its defaults from 6tree01. The settings
are in `species/<id>.json`.
- Each tree is built 7–8 m tall rather than the sprite's 15–25 m. The engine scales by height, so MM7's oversized
  painted leaves keep about the proportion they have in the sprite, and the crowns cost no more cards than an MM6
  tree.
- The changes against MM6 are brighter canopy occlusion (floor 0.55, range 0.45, power 1, `local_floor` 0.45,
  `core_floor` 0.72), because MM7's sprites are much lighter than MM6's, per-cell autumn palettes and, for tree23 and
  tree69, `crown.masses`. Rebuild with `./build.sh <id> [--install]`.
- **tree66**: tall narrow crown of light-green sprays from a fifth of the height, drooping limbs, a straight pale
  trunk.
- **7tree05**: a dense oblong crown in olive and yellow patches on a short dark trunk.
- **7tree29**: a red and rose maple crown of loose clumps, with the trunk and limbs showing in the gaps.
- **tree23**: a wide orange and gold crown in two lobes, the main left one and a smaller right one, on a slim
  straight trunk.
- **tree69**: a broad bright-green crown in separate masses with limbs showing between them, on a short thick trunk
  branching into spreading limbs.
- LOD0 against the sprite, in sRGB means:

  | Tree | LOD0 | Sprite |
  |---|---|---|
  | tree66 | 77/93/58 | 78/93/59 |
  | 7tree05 | 76/76/30 | 81/74/31 |
  | 7tree29 | 95/49/48 | 93/49/46 |
  | tree23 | 107/66/21 | 120/73/8 |
  | tree69 | 66/99/41 | 57/106/38 |

- Every level stays within 5.8/255 of LOD0 in mean colour, and coverage stays within 10 %.

## Sources and licences

- Bark: Poly Haven [coral_mud_01](https://polyhaven.com/a/coral_mud_01),
  [bark_willow_02](https://polyhaven.com/a/bark_willow_02) and [bark_brown_01](https://polyhaven.com/a/bark_brown_01)
  (living trees), all CC0.
- Leaves: ambientCG [LeafSet022](https://ambientcg.com/view?id=LeafSet022), CC0.
- All textures are read from `../../mm6_new_sorpigal_3d/trees/source/`, and nothing was downloaded.
- Twig atlas, skeleton tracing and all geometry: our own work. Sapling Tree Gen (GPL) is used as a tool, and its
  output is ours.

## Compromises

- **Bare trees:**
  - The front view follows the sprite. The other sides are an invented spread in depth, and tree41's side view is
    narrower than its front.
  - The sprites' many tiny antler-like twig forks are partly lost: forks shorter than about a limb radius are pruned
    as thinning noise, and tips taper to points.
  - tree42's tangle of fine twigs is thinner than the sprite at LOD0, because 97 of the finest twigs are replaced by
    faint twig cards to stay within 6000 triangles before reduction. Its hollow is a painted patch, not a recess:
    under random yaw it faces a random side, and it shows a thin dark edge seen from the side.
  - Root spurs read as a few small spikes rather than the sprites' flared base.
  - Branches drawn crossing the trunk are attached to it.
- **Leafy trees:**
  - Leaves are LeafSet022 sprays, not the sprites' star-shaped maple leaves.
  - tree23's lower left skirt is thinner than the sprite's, because the mass shrinks by part of each clump's radius.
  - A few of tree69's thin limbs poke out past its masses in the side view.
  - tree23 stays about 13 levels less red than its saturated orange sprite; the other means are within 8 levels.
  - tree23's crown starts a little higher than the sprite's.
- Each source GLB embeds its own bark and leaf maps (7–10 MB). The cooked runtime copies are 0.3–0.8 MB.
- Review lighting is Eevee, not the engine. Check in game once bound.
