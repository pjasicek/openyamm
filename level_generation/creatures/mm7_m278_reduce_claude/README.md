# MM7 Manticore (`m278`, Minicore / Manticore / Scorpicore) reduction (2026-10-20)

The user accepted the Batch E models and asked for triangle reduction ("do tris reduction now"). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding, so the batch E
textures, region mask and tier ramps stay valid. No Meshy credits. Scripts are copied from `mm8_m452_reduce_claude/`
(and `carry_variants.py`, `probe_max.py`, `mouth_keep.py` from `mm8_m492_reduce_claude/`); `make_groups.py`,
`close_manticore.py`, `glb_close.py`, `build_lods.py`, `viewer_tiers.py` and `glb_stretch.py` are adapted to the
manticore. Batch E rules: nothing installed, nothing written to `assets_dev/`, `assets_source/` or `../mm7_m278_claude/`.

Source: the batch E export `../mm7_m278_claude/export/mm7_m278.glb`, copied to `work/mm7_m278_source_pre_reduce.glb`
(rollback source). One material (`M278_A`, variants `M278_B`/`M278_C` through `KHR_materials_variants`), one `M278`
node, 24 bones, `Socket_Stinger`, 8 clips.

Pieces: the skin (7,699 faces: lion body, face, legs, tail root), the five rigid chitin tail segments (Tail2–6,
488–1,004 faces; the stinger is Tail6) and 167 small pieces up to 200 faces (mane shingles, claws, teeth, eyes,
whiskers, ear and brow pieces; 5,127 faces).

## Ladder

Weld 48,112 -> 388 open edges (unchanged by every step; 137 coincident vertices with other weights kept apart).
Limits are scaled to 1.7 m (`REA_HEIGHT_M`; the body is 2.4 m long with the tail arch, 1.92 m high): p99 5.1 mm,
max 25.5 mm.

Region budgets (`make_groups.py`, dominant bone and connected piece):
- **Kept exactly:** the small pieces (mane shingles, teeth, eyes, whiskers, ear/brow pieces); claws only in the
  first three rounds.
- **Face** (Head-dominated skin): 70 %.
- **Tail segments:** 60 % (rigid pieces; no deformation risk).
- **Claws** (15 paw pieces of 80–110 faces, from round c1): 60 %.
- **Skin:** fills the rest.

| step | locks | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| g1 | small pieces | 12,034 (75 %) | 3.05 / 35.3 | 0.997 | 0.988 | fail (max) |
| e1 | + error lock | 12,034 (75 %) | 3.00 / 14.4 | 0.997 | 0.988 | pass |
| e1 | + error lock | 11,230 (70 %) | 4.31 / 29.3 | 0.996 | 0.987 | fail (max) |
| s2 | e1 + hip spot | 11,230 (70 %) | 4.31 / 18.6 | 0.996 | 0.987 | pass |
| **c1** | s2, claws at 60 % | **10,588 (66 %)** | **4.49 / 18.6** | **0.995** | **0.987** | **picked** |
| c1 | s2, claws at 60 % | 10,106 (63 %) | 5.69 / 26.0 | 0.995 | 0.986 | fail |

- **Weights:** UV weights (`uv_weights.py`, `REA_WEIGHTS=component`); source vertices keep theirs exactly.
- **Error lock** (`err_lock.py`, Cand_75, over 15 mm, 2.5 cm radius): 86 faces around 15 belly and inner-leg vertices
  (Spine1/Spine2, forearm) that the cut missed by up to 35 mm in Running and Walking.
- **Hip spot** (`spot_lock.py`, 3 cm at (0.105, 0.329, 0.53)): the one vertex over 20 mm at 70 % (inner left hip,
  Death frame 14). No second error-lock round (the playbook's warning).
- **Why only 66 %:** a third of the mesh is small separate pieces (mane shingles of 20–30 faces each, teeth, eyes)
  kept exactly; their ends taper into points at any cut. The skin itself is cut to about 45 %.

Close-ups (`close_manticore.py` on `work/ladder_c1.blend`; `review/close/sheet_r66_tex.png`, `sheet_r66_clay.png`):
face front, three-quarter and both sides, mouth, mane from above, Attack, all four paws, tail root, tail segments,
stinger, back, flank, belly, Death, Running and Walking. Face, teeth, mane, tail segments and stinger match; the claws
at 60 % are smooth cones (the source claws had white specular slivers).

Texture checks (on the batch E 2K base colour and on the region mask):
- **Drift (`texture_drift.py`):** two faces over 40 (12.6 cm² in all on a 2.4 m creature); mask drift: one 3.7 cm²
  face on a head piece.
- **Slivers (`dark_slivers.py`, `REA_DARK_L=80 REA_DARK_N=4`):** 10 hits under 5 cm² each, on the lip line and one tail
  segment. The close-ups show no change there.

## Build

`scripts/build_reduced.sh export/mm7_m278.glb`: `export_cand.py` (Cand_66 of `work/ladder_c1.blend`, node `M278`) ->
`swap_lod0.py` (onto the rollback source; materials, variants, clips, `Socket_Stinger` byte for byte) -> `build_lods.py`
(ratios 0.5 / 0.25 / 0.1; protected: bounding extremes within 5 mm including the stinger tip, and LOD0 vertices within
6 mm of the floor in any Death/Dead frame) -> `shrink_shadow_lods.py` (the batch E project's own step) ->
`carry_variants.py` (the LOD builder drops the tier mapping from LOD and shadow primitives: carried to 7 primitives).
Materials, variant list, nodes and clips are identical to the batch E file.

| | LOD0 | LOD1 | LOD2 | LOD3 | file |
|---|---:|---:|---:|---:|---:|
| batch E | 16,048 | 8,020 | 2,820 | 831 | 14.7 MB |
| reduced (smooth) | **10,588** | 5,286 | 2,585 | 933 | 6.9 MB |
| reduced (flat, `REA_FLAT=1`) | 10,588 | 5,286 | 2,585 | 933 | 10.5 MB (`work/mm7_m278_flat.glb`) |

### Shading: smooth (default) or flat

The batch E export is **flat-shaded** (every triangle has its own vertices and face normal; Meshy's mesh was never set
smooth). The reduced export is **smooth-shaded** by default: a quarter of the vertex data, and textured it looks almost
the same (the claws and stinger lose their faceted glints; the mane shingles read a little rounder and darker in
places). `REA_FLAT=1 scripts/build_reduced.sh <out>` builds the flat version. Side by side (batch E | reduced smooth |
reduced flat): `review/glbclose/source_smooth_flat_tex.png` and `_clay.png`. **The user chooses.**

## Gates

- **`lod_check.py`** (every LOD): bounds kept (1.02 × 2.40 × 1.92 m); no face stretches over 20× in any clip; lowest
  point equal to the batch E model (Walking −25 mm at every LOD as in batch E, every other clip ≥ −5 mm). The batch E
  LOD2/LOD3 corpse floated 36–43 mm in Dead; the reduced LODs do not.
- **Edge stretch** (`glb_stretch.py`, the batch E `outliers.py` gate on the exported LOD0): identical to batch E in every
  clip (max 4.95× Running, the err-locked belly vertex; Dead 2.63× against 2.50×).
- **`check_winding.py`:** 0 inverted closed parts.
- **Viewer:** `run_creature_review.py check`: 48 switches (6 models × 8 clips), no console errors.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m278_reduce_claude/review/viewer/index.html`: batch E and reduced
for tiers A, B and C (ramps baked by `scripts/viewer_tiers.py`, which writes only into this project), opening on the
reduced tier A. Native reference frames from `../mm7_m278/trimmed_2x/`. Shots: `review/viewer_shots.png`.
LOD renders: `review/lods/` (`lod_views.py`, Standing and Attack per LOD).

## For the user to review

- Smooth versus flat shading (above).
- The mane at 66 %: the shingles are kept, only the shading changes with the smooth option.

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m278_reduce_claude/export/mm7_m278.glb --world mm7
```

The `actors.yml` binding in `../mm7_m278_claude/README.md` is unchanged (same file name, nodes, clips, socket).
Rollback: `work/mm7_m278_source_pre_reduce.glb`.

Reproduce:
1. `REA_NODE=M278 REA_GLB=level_generation/creatures/mm7_m278_reduce_claude/work/mm7_m278_source_pre_reduce.glb blender -b -P scripts/import_source.py`;
2. `dump_mesh.py`, `dump_faces.py`, `dump_weights.py` (blender), `make_groups.py`;
3. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.6 run_ladder.sh g1 0.8,0.75,0.7,0.65`;
4. `REA_CAND=Cand_75 REA_ERR_MM=15 REA_LOCK_R=0.025 err_lock.py -- work/keep_base.npy work/keep_e1.npy`;
5. `spot_lock.py work/keep_e1.npy work/keep_s2.npy 0.03 0.105,0.329,0.53`;
6. claw group 3 added to `work/groups_c.npy` / `work/keep_c.npy` (paw-dominant pieces of 80–110 faces), then
   `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_c.npy REA_GROUPS=work/groups_c.npy REA_GROUP_RATIOS=1:0.7,2:0.6,3:0.6 run_ladder.sh c1 0.66,0.63`
   (`run_ladder.sh` defaults to `REA_HEIGHT_M=1.7`);
7. `close_manticore.py -- ladder_c1.blend Cand_66`, `pair_sheet.py`, `texture_drift.py r66`, `dark_slivers.py r66`;
8. `build_reduced.sh export/mm7_m278.glb` (and `REA_FLAT=1 ... work/mm7_m278_flat.glb`);
9. `lod_check.py -- <glb> <label>`, `glb_stretch.py -- <glb> M278`, `lod_views.py`, `glb_close.py`, `viewer_tiers.py`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Walking sinks to -2.5; Walking sinks to -2.9; walking lifts every foot by +2.6; walking lifts every foot by +3.0; walking sinks to -2.5; walking sinks to -2.9.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m278.glb export/mm7_m278.glb --lift-joints Walking --lift-only 'B_Skirt*,Robe_*,…' --ground-loop Walking`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m278.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/q3`](../gait_rollout_20261031/q3/README.md) added **Walk2**, a faster lateral-sequence
walk for Standard's wandering:
- 0.7667 s, stride 1.6713, authored speed 2.18;
- Walking played ×1.57 on Manticore A, Walk2 plays ×0.99-1.14.

Walk2 was grafted onto the installed GLB; everything else is byte for byte. Binding: `walking: Walk2`,
`stride_length: 1.6713`.

Rebuild: `blender -b --factory-startup -P scripts/quad_gait.py -- m278 work/m278_clips.glb`, then `graft_clips.py`
(see the q3 README). A far-LOD repair rerun or any re-export must re-graft Walk2. The viewer (`manticore-walk2-1`)
plays the installed clips plus Walk2.
