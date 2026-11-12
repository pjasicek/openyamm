# MM7 Ghost (`m242`, Shade / Specter / Ghost) reduction (2026-10-20)

User request after batch G: "reduce tris count for all 5". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: the texture-aware MeshLab ladder keeps UVs,
so the textures, region mask, tier ramps, clips and the hood fix stay as exported. No Meshy credits. Scripts are
copied from `mm7_m162_reduce_claude/` (ladder, LODs, LOD check, variants) and adapted; `ghost_gates.py` is the
production project's gate. Batch rules apply: nothing installed, nothing in `assets_dev/` or `assets_source/`,
`mm7_m242_claude/` untouched. Every Blender/Python step runs memory-capped (`scripts/cap.sh`, `scripts/b.sh`).

Source: `../mm7_m242_claude/export/mm7_m242.glb` (after the hood fix, not installed), copied to
`work/mm7_m242_source_pre_reduce.glb` (rollback source). One material `M242_A` (body and head merged into a
2080x1024 atlas) with tier variants `M242_B` / `M242_C` (one region: the robe), one `M242` node, 52 `B_*` bones +
24 robe chain bones, 4 influences, smooth shading.

Pieces (207 after the weld): the skull (1,100 faces), the hood/cape shell (900), the ribcage halves, sternum,
vertebral column and arm bones (rigid pieces), ~70 robe shreds and every phalanx as its own piece.

## Ladder

Weld 8,238 -> 2,127 open edges (unchanged by every step); 78 coincident vertices with other weights (bone pieces and
shreds touching) are separated for MeshLab and keep their exact source weights. Limits scaled to the 1.86 m height:
p99 5.58 mm, max 27.9 mm. Weights: nearest vertex of the matching source piece (rigid pieces stay rigid).

Region budgets (`make_groups.py`, `REA_GROUP_RATIOS`):
- **Kept exactly:** every piece of <= 30 faces (phalanges, claw tips, short shreds), every hand/finger piece (the
  claws), every robe shred (`keep_shreds.npy`) and the non-rigid bone pieces (sternum, front rib bands, vertebral
  column: a spine weight gradient; dominant bone under 90 % of the faces).
- **Skull:** 65 %. **Hood/cape shell:** 80 %. **Rigid trunk and arm bones:** the rest of the budget.

| step | config | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a | shreds 70 %, skull 75 %, cape 60 % | 6,358 (76 %) | 6.19 / 67.8 | 0.989 | 0.993 | fail (shreds collapse, 68 mm) |
| b/c | shreds kept, skull 75 %, cape 60 % | 6,532 (80 %) | 5.34 / 28.6 | 0.993 | 0.994 | fail (cape shoulders) |
| d | shreds kept, skull 80 %, cape 80 % | 6,696 (82 %) | 4.89 / 18.9 | 0.997 | 0.996 | pass |
| f | shreds kept, skull 65 %, cape 80 % | 6,370 (78 %) | 5.37 / 18.9 | 0.996 | 0.996 | pass, but bone stretch 1.85 (source 1.29) |
| g | f with UV-surface weights | 6,370 (78 %) | 5.37 / 20.3 | 0.996 | 0.996 | rejected: bone stretch 9.1 (fallback weights crossed pieces) |
| **h** | **f + non-rigid bone pieces kept** | **6,696 (82 %)** | **5.15 / 18.9** | **0.996** | **0.996** | **picked: every ghost gate equals the source** |
| h | | 6,532 (80 %) | 5.65 / 18.9 | 0.996 | 0.996 | fail |

- **Shreds cannot be cut:** at 70 % (a) they lose their tapered tips (68 mm). Kept exactly with the claws and small
  bones, about half of the mesh cannot be reduced; this ghost was already the lightest of the batch.
- **Non-rigid bone pieces:** step f passed the ladder but longer reduced edges on the sternum's spine gradient raised
  the bone stretch to 1.85; keeping those pieces (h) costs ~330 triangles and restores the source values.

Close-ups (source vs reduced, from the ladder blend and straight from the GLBs): `review/close/sheet_r78_{tex,clay}.png`
(step f) and `review/glbclose/sheet_{tex,clay}.png` (final): skull front and three-quarter, hood from behind and in the
Fidget, ribs, both claw hands, robe shreds front and back, Attack, Walking, Death / Dead heap. No feature changed.
Texture drift (`texture_drift.py r82`): 21 faces over 40 levels (69 cm2 in all, p99 25.5), not visible in the close-ups.

## Export and LODs

`scripts/build_export.sh` (defaults `ladder_h.blend Cand_82`): `export_cand.py` -> `swap_lod0.py` (into the rollback
source: materials, variants, ramps, clips unchanged) -> `build_lods.py` (ratios 0.5 / 0.2 / 0.07; the bounding
extremes and the Death/Dead floor contacts protected) -> `shrink_shadow_lods.py` -> `carry_variants.py` (7 primitives).
LOD3 at 0.06 (249) sank the corpse 6.6 cm under the floor; 0.07 keeps it at the source's -0.2 cm.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch G export | 8,168 | 4,036 | 1,344 | 353 |
| reduced | **6,696** | 3,292 | 1,214 | 335 |

`export/mm7_m242.glb` 8.3 MB (source 8.9 MB).

## Gates (final export)

- **`ghost_gates.py`** on gate copies of both GLBs (`ghost_gate_copy.py`: the master's cloth/piece labels by nearest
  vertex), every frame incl. half frames — reduced = source in every clip: hood stretch p99 <= 1.82 / max 2.08
  (Attack; source 1.73 / 2.08), bone stretch <= 1.33 (same as source), cloth p99 <= 2.05 (source 2.07), floors
  bones -0.22 cm and cloth -0.17 cm (Death), hover range and jerk unchanged; fins: none.
- **`lod_check.py`** (every LOD, every clip): bounds unchanged; lowest points equal to the source's at every LOD; one
  stretched face at LOD0 in Attack/Fidget as in the source; LOD2 one face in Death/Dead (source none).
- **Winding:** 0 inverted closed parts.
- **Viewer:** `tools/run_creature_review.py ... check`: 6 models x 7 clips (42 switches), no console errors.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m242_reduce_claude/review/viewer/`: the batch G export (r100)
and the reduction (r82, default) for tiers A, B and C (`viewer_tiers.py` bakes the tier ramps for three.js into this
project only; `viewer_manifest.py`).

## For the user to review

- A modest cut (-18 %): the shreds, claws and non-rigid bone pieces are kept exactly; cutting them lost features.
- LOD2 has one stretched face in the lying Death/Dead.

## Install (installed 2026-10-21)

Replaces the batch G export of `mm7_m242_claude/` (same binding `../mm7_m242_claude/export/actors_binding.yml`, same
clips, nodes and materials):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m242_reduce_claude/export/mm7_m242.glb --world mm7
```

Rollback: `work/mm7_m242_source_pre_reduce.glb`.

Reproduce (TOKEN = the workspace lease):
1. `REA_NODE=M242 REA_GLB=level_generation/creatures/mm7_m242_reduce_claude/work/mm7_m242_source_pre_reduce.glb scripts/b.sh import_source.py`;
2. `REA_PROTECT=B_Head scripts/b.sh dump_mesh.py`, `dump_faces.py`, `dump_weights.py`; `scripts/cap.sh python3 scripts/make_groups.py`, then
   `keep_shreds.npy` = `keep_small.npy | (groups == 4)`;
3. `REA_KEEP_FACES=work/keep_shreds.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.65,2:0.8 scripts/run_ladder.sh h 0.82,0.80,0.78`;
4. `close_m242.py -- ladder_h.blend Cand_82`, `pair_sheet.py`, `texture_drift.py r82`;
5. `scripts/build_export.sh`;
6. `lod_check.py`, `glb_close.py`, `ghost_gate_copy.py` + `ghost_gates.py` on both GLBs, `check_winding.py`;
7. `viewer_tiers.py <glb> r100|r82`, `viewer_manifest.py`.

## Anim fix (2026-11-11, MM6–MM8 audit)

Walking loop seam closed (pop 0.0648 H -> 0) with `loop_close.py`; details: [mm7_m242_animfix_claude](../mm7_m242_animfix_claude/README.md).
