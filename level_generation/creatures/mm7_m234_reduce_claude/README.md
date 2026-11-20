# MM7 Gargoyle (`m234`, Stone / Marble / Obsidian Gargoyle) reduction (2026-10-20)

User request after the batch G review: "reduce tris count for all 5". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding, so the textures,
region mask (wing membranes), tier ramps and clips stay as exported. No Meshy credits. Scripts copied from
`mm7_m162_reduce_claude/` (ladder, component weights, LODs, LOD check, variants); `sole_flat.py` / `sole_probe.py` from
`mm7_m234_claude/scripts/`. Batch G rules: nothing installed, nothing in `assets_dev/` or `assets_source/`,
`mm7_m234_claude/` untouched. Every Blender/Python step runs memory-capped (`scripts/cap.sh`).

Source: `../mm7_m234_claude/export/mm7_m234.glb` (after the flat-feet fix), copied to
`work/mm7_m234_source_pre_reduce.glb` (rollback source). One material `M234_A` (body + head atlas 2080x1024) with the
tier variants `M234_B` / `M234_C`, one `M234` node, smooth shading. Weld 7,024 -> 322 open edges, 2 coincident
vertices with other weights. No two-sided reversed copies in the source (the import kept all 10,812 triangles).

Pieces: one stone shell (9,539 faces: body, head with horns and ears, clawed hands, wing arms, struts and membranes,
tail) and 19 small pieces (1,273 faces: the two eyes, 16 teeth, the tail spade).

## Ladder (limits for 1.913 m: p99 5.74 mm, max 28.7 mm; IoU >= 0.98, SSIM >= 0.93)

`make_groups.py`: small pieces and the 44 sole faces (every vertex within 3 cm of the rest floor) kept exactly; labels
by dominant bone (head, hands, feet, wings, tail, rest).

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a: head 70 %, hands 75 %, feet 80 %, wings 70 %, tail 75 % | 0.80 | 8,434 | 3.54 / 26.4 | 0.994 | 0.998 | pass |
| a | 0.75 | 8,106 | 6.00 / 35.2 | 0.989 | 0.996 | fail |
| u: uniform | 0.75 | 8,108 | 3.23 / 27.3 | 0.995 | 0.999 | pass |
| u | 0.70 | 7,568 | 4.10 / 39.0 | 0.993 | 0.998 | fail (Hit) |
| b: head 65 % | 0.70 | 7,566 | 4.40 / 20.8 | 0.991 | 0.998 | pass |
| b | 0.65 | 7,026 | 5.92 / 35.2 | 0.988 | 0.996 | fail |
| c: head 60 % | 0.68 | 7,350 | 4.54 / 20.8 | 0.991 | 0.998 | pass |
| **c** | **0.66** | **7,134** | **5.10 / 24.7** | **0.989** | **0.997** | **picked** |

The head (horns, ears, face: 3,412 faces, 32 % of the model; protected during the build) takes the larger share of the
cut; per-region budgets for wings, hands and feet did worse than one shared cut (the build had already reduced them).
Close-ups `review/close/sheet_c_tex.png`, `sheet_c_clay.png` (source | r70 | r66): face front, three-quarter and side,
horns from above, both hands, claws in the attack, both feet and their side, folded and spread wings front and back,
tail, chest, attack, death. No feature changed. Texture drift: 0 faces over 40 (p99 16.8); dark slivers: 0.

## Export and LODs

`scripts/build_export.sh Cand_66` -> `export/mm7_m234.glb` (7.4 MB): `export_cand.py` -> `swap_lod0.py` (materials,
variants, ramps, clips unchanged) -> `build_lods.py` (ratios 0.5 / 0.26 / 0.085; 0.22 left one stretched LOD2 face in
Attack and Fidget; protected: extremes and the floor contact of Death, Dead and Standing) -> `shrink_shadow_lods.py` ->
`carry_variants.py` (7 primitives).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch G export | 10,812 | 5,405 | 1,942 | 630 |
| reduced | **7,134** (-34 %) | 3,565 | 1,840 | 600 |

## Gates (source vs reduced, GLB imports `work/gate_*.blend`)

- **Flat feet** (`sole_flat.py`, `sole_probe.py`): identical to the source: planted sole spread 1.5 cm (rest 1.5), lowest
  sole 0.0-0.3 cm in Standing, Attack, Hit and Fidget; Walking hovers 2.3-8.0 cm as before.
- **`lod_check.py`** (every LOD, every frame): bounds kept at every LOD (2.84 x 1.08 x 2.00 m), no stretched face at any
  LOD; lowest points as the source (Death -10.0 cm, source -9.8; Dead -4.6, source -4.8).
- **Edge stretch** (`outliers.py`): the same maxima as the source in every clip (6.5-12.8, at a shoulder/jaw vertex
  split between B_Head and the clavicle that the source already has; the reduction kept it exactly).
- **Winding**: 0 inverted closed parts. **Viewer**: `run_creature_review.py ... check` 42 switches, no console errors.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m234_reduce_claude/review/viewer/`: batch G export (r100) and
the reduction (r66, default), tiers A, B and C. Shots: `review/shots/`.

## For the user to review

- The inner-membrane tears Meshy left (by the armpits) are unchanged, neither fixed nor worse.
- The shoulder/jaw stretch outlier (up to 12.8x in Fidget) is a source weight split between B_Head and the clavicle,
  not caused by the reduction.

## Install (installed 2026-10-21)

Replaces the batch G export of `mm7_m234_claude/` (same binding, clips, nodes and materials):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m234_reduce_claude/export/mm7_m234.glb --world mm7
```

Rollback: `work/mm7_m234_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_NODE=M234, REA_GLB=work/mm7_m234_source_pre_reduce.glb), `dump_mesh.py`,
`dump_faces.py`, `dump_weights.py`, `make_groups.py`; `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_small.npy
REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.6 scripts/run_ladder.sh c 0.72,0.70,0.68,0.66`; `close_m234.py --
ladder_c.blend Cand_66,Cand_70`, `pair_sheet.py`, `texture_drift.py r66`, `dark_slivers.py r66`; `cp work/ladder_c.blend
work/ladder.blend; scripts/build_export.sh Cand_66`; gates on `gate_import.py` copies; `viewer_tiers.py <glb> r100|r66`,
`viewer_manifest.py`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: corpse at -4.2; dying sinks to -9.4; living lowest at -2.7 (suggested hover 0.029246).
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m234.glb export/mm7_m234.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --hover 0.029246 Death Dead --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m234.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).
