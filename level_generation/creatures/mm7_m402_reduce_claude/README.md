# MM7 Spider (`m402`, Giant Spider / Venomous Spider / Widowmaker) reduction (2026-10-20)

User request after accepting Batch E: "do tris reduction now". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: nothing needed rebuilding, so the Batch E
textures, region mask and tier ramps stay valid. No Meshy credits. Scripts are copied from `mm8_m452_reduce_claude/`
(ladder, UV weights, error/spot locks, LOD build) and `mm8_m492_reduce_claude/` (`carry_variants.py`, `drift_lock.py`);
`make_groups.py`, `close_spider.py`, `glb_close.py`, `build_lods.py` and `export_cand.py` are adapted to the spider.
Nothing is installed (Batch E rules); `mm7_m402_claude/` is not modified.

Source: `../mm7_m402_claude/export/mm7_m402.glb` (not installed), copied to `work/mm7_m402_source_pre_reduce.glb`
(rollback source). One material (`M402_A`: 2K base colour, 1K normal / ORM / region mask), one `M402` node, 28 bones,
three `KHR_materials_variants` tiers (abdomen green / blue / red), 8 clips. Leg span 2.4 m, height 0.74 m.

Pieces after the weld (41,282 -> 581 open edges, unchanged by every step; 18 coincident vertices with other weights
kept apart; one duplicated face pair merged): the body (cephalothorax + abdomen, 3,047 faces), eight legs (859-1,111
faces each), four chelicera/fang pieces (187-266), four eyes (~50), two palp-like pieces (176, 286) and the red
hair-fringe cards (8-110).

## Ladder

Limits scaled to the 2.4 m leg span (`REA_HEIGHT_M=2.4`): p99 7.2 mm, max 36 mm. UV weights (`REA_WEIGHTS=component`)
in every run. Kept exactly (`make_groups.py`): the chelicerae and fangs, the eyes and every piece of up to 80 faces
(1,430 faces).

| step | locks | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| u1 | pieces | 9,663 (70 %) | 2.63 / 11.9 | 0.995 | 0.994 | pass |
| u1 | pieces | 8,283 (60 %) | 3.37 / 19.8 | 0.993 | 0.994 | pass |
| u1 | pieces | 6,903 (50 %) | 4.59 / 25.8 | 0.990 | 0.993 | pass |
| u2 | pieces | 5,521 (40 %) | 6.76 / 25.8 | 0.984 | 0.991 | pass |
| e1 | + error lock (Cand_45, 12 mm, 3 cm) | 6,903 (50 %) | 4.78 / 9.8 | 0.988 | 0.993 | pass; 16 dark slivers |
| d1 | e1 + drift/sliver lock | 6,903 (50 %) | 5.43 / 20.2 | 0.987 | 0.992 | pass |
| **d3** | d1 + fang-rigid cards + fang-root spots | **6,903 (50 %)** | **5.53 / 10.5** | **0.987** | **0.992** | **picked** |

- Every uniform step passes the numbers, down to 40 %; the close-ups (`review/close/sheet_u_{tex,clay}.png`,
  source / r60 / r50 / r40) show no visible loss even at 40 %. The pick stays at **50 %**, the conservative step
  where the error and texture locks hold (the MM6 spider stopped at 55 % because r45 made its legs angular).
- **Error lock:** the 25.8 mm maximum came from fringe cards rigid on a fang bone (below) and from the thorax front
  where the chelicerae attach. One error-lock round, then one drift/sliver lock round (`texture_drift.py` +
  `dark_slivers.py REA_DARK_L=80 REA_DARK_N=4`, merged), then the three fang-rigid cards over 80 faces kept whole and
  4 cm spots at the left and right chelicera roots (`spot_lock.py`). Keep set 2,482 faces.
- **Texture at d3 r50:** drift over 40 on 5 faces (16 cm² in all, at the abdomen sides); 5 dark-sliver faces of
  2-5 cm² on the thorax top and the legs. Neither shows in the close-ups.

Close-ups (`close_spider.py`, welded blend, normals cleared): `review/close/sheet_d3_{tex,clay}.png` (source vs d3
r50): face, fangs open, eyes, knees, fringes, foot tips, abdomen, underside, Attack, Death, Dead, Running.

## Two changes beyond the cut (for review)

- **Smooth shading.** The Batch E export is flat-shaded (every triangle has its own vertices and face normal), which
  shows facets on the glossy abdomen and leg tubes. The reduced export is **smooth** (default); `REA_FLAT=1
  scripts/build_runtime.sh` builds the flat version to `work/mm7_m402_flat.glb` (9.4 MB against 6.9 MB smooth).
  Side by side straight from the GLBs: `review/glbclose/sheet_source_smooth_flat_{tex,clay}.png`.
- **Fringe cards re-rigged on their legs** (`card_list.py`, `export_cand.py REA_FIX_CARDS=1`). The original rig left
  seven fringe cards (280 vertices on legs R1, R2, L1, L4) rigid on `Fang_R`, `Fang_L` or `Abdomen`: its fang
  detection took every small piece in front of the body, and cards over 10 cm from a leg fell back to the body. They
  stayed behind when their leg moved, up to 0.9 m off the leg in Death (`card_gap.py`;
  `review/glbclose/death9_cards.png`, source left). Each card now takes the weights of the leg vertex nearest its
  centroid, as `rig_spider.py` intended. Side effect: in Death and Dead two of them now dip 3-6 cm under the floor
  with their leg (hair on the ground; the source's lowest point there was 0).
  **The same defect is in `mm7_m402_claude/`** (not fixed there; Batch E rules).

## Build

`scripts/build_runtime.sh`: `export_cand.py` (Cand_50 of `work/ladder_d3.blend`, cards fixed, smooth) ->
`swap_lod0.py ... M402` -> `build_lods.py` -> `shrink_shadow_lods.py` (the original build's step) ->
`carry_variants.py`: **`export/mm7_m402.glb`, 6.9 MB** (source 13.1 MB). Materials, variants, clips and node
structure are byte-for-byte the source's; the three tier variants are on every LOD and shadow primitive.

`build_lods.py`: ratios 0.5 / 0.25 / 0.12 of LOD0 (LOD3 at the source's count); protected points: the bounding
extremes (5 mm: leg tips, top) and LOD0 vertices within 4 mm of the floor in any Death, Dead or Standing frame (the
foot tips).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source | 13,808 | 6,899 | 2,479 | 822 |
| reduced | **6,903** | 3,446 | 1,719 | 821 |

## Gates

- `lod_check.py` (every LOD, every frame): bounds kept (2.40 x 2.40 m, top 0.741 m against 0.743); no stretched
  faces. Lowest point: Standing -2.1 cm (source -2.2, an existing dip), Hit -0.4 cm, Death/Dead -6.3 / -3.1 cm (the
  re-rigged cards, above); the rest as the source.
- Edge stretch (`glb_stretch.py`, the original project's gate on the GLB): max 1.82 (Death/Dead) against 1.96 in the
  source.
- `check_winding.py`: 0 inverted closed parts.
- Viewer `review/viewer/`: original vs reduced for tiers A/B/C, all 8 clips; `run_creature_review.py check`: 48
  switches, no console errors. `review/viewer_tiers.png`: original A, reduced A/B/C.

Viewer: http://127.0.0.1:8912/level_generation/creatures/mm7_m402_reduce_claude/review/viewer/index.html

## For the user to review

- Smooth vs flat shading (`review/glbclose/sheet_source_smooth_flat_tex.png`).
- The fringe-card fix, and the 3-6 cm floor dip of two cards in Death/Dead that comes with it.

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m402_reduce_claude/export/mm7_m402.glb --world mm7
```

The `actors.yml` binding in `../mm7_m402_claude/README.md` is unchanged (same file name, scale, clips, strides).
Rollback: install `work/mm7_m402_source_pre_reduce.glb`.

Reproduce:
1. `REA_NODE=M402 REA_GLB=level_generation/creatures/mm7_m402_reduce_claude/work/mm7_m402_source_pre_reduce.glb blender -b -P scripts/import_source.py`;
2. `dump_mesh.py`, `dump_faces.py`, `dump_weights.py` (blender), `make_groups.py`;
3. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_base.npy run_ladder.sh u2 0.45,0.4`, then
   `REA_CAND=Cand_45 REA_ERR_MM=12 REA_LOCK_R=0.03 blender -b -P err_lock.py -- work/keep_base.npy work/keep_e1.npy`;
4. `run_ladder.sh e1 0.5,0.45,0.4`, `texture_drift.py r50` + `dark_slivers.py r50` (merged max into
   `work/drift_r50.npy`), `drift_lock.py work/keep_e1.npy work/keep_d1.npy r50`;
5. fang-rigid cards over 80 faces added (`work/keep_d2a.npy`), `spot_lock.py work/keep_d2a.npy work/keep_d3.npy 0.04
   0.065,-0.487,0.27 -0.065,-0.487,0.27`, `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_d3.npy run_ladder.sh d3 0.5`;
6. `card_list.py` (pieces from `make_groups.py`), `scripts/build_runtime.sh`;
7. `lod_check.py`, `glb_stretch.py`, `glb_close.py`, `check_winding.py`, viewer (`swap_lod0.py` of the original
   viewer tier GLBs with `work/cand_export.glb`).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: corpse at -3.1; dying sinks to -6.4.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m402.glb export/mm7_m402.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m402.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait pass (2026-10-21)

`export/mm7_m402_gait.glb` is the floor-fixed `export/mm7_m402.glb` with `Walk2` and `Run2` grafted on; it is
installed as `mm7_m402.glb`. The clips come from `../mm7_m402_claude/scripts/gait2_m402.py` (see
[its README](../mm7_m402_claude/README.md#gait-pass-walk2-and-run2-2026-10-21)).
- Meshes, LODs, variants and the old clips are unchanged.
- Binding: `walking: Walk2`, `run: Run2`, `stride_length: 1.0917`, `run_stride_length: 1.572`.
- The re-rigged fringe cards hang to the floor from their tibiae. The gait raises a planted foot by up to 3.5 cm
  rather than push a card through the floor.
- `check_winding.py`: 0 inverted.
- The viewer is now revision `gait-1`: tier A/B/C with the old and the new clips; the previous manifest is
  `review/viewer/manifest_reduce-1.json`.
- Recordings: `review/playback/` and `review/shots/`.
