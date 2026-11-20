# MM7 Griffin (`m258`, Griffin / Hunting Griffin / Royal Griffin) reduction (2026-10-20)

User request after accepting batch E: "do tris reduction now". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding, so the textures,
region mask and tier ramps stay valid. No Meshy credits. Scripts are copied from `mm8_m452_reduce_claude/` (ladder,
UV weights, error lock, LODs, checks); `make_groups.py`, `close_griffin.py`, `glb_close.py`, `build_lods.py`,
`viewer_tiers.py` and `update_viewer_manifest.py` are adapted to the griffin. Batch E rules: nothing installed, nothing
in `mm7_m258_claude/` written (it is read for its textures, ramps and native frames only).

Source: `../mm7_m258_claude/export/mm7_m258.glb` (the not-installed project export), copied to
`work/mm7_m258_source_pre_reduce.glb` (rollback source); its full-detail input `export/mm7_m258_lod0.glb` copied to
`work/mm7_m258_lod0_pre_reduce.glb`. One material `M258_A` (2K base colour, 1K normal and ORM) with the region mask and
three `KHR_materials_variants` tiers, one `M258` node, 29 bones, clips Fly, Attack, Hit, Death, Dead.

Pieces: one body with head, beak, crest, wings and lion hind legs (12,562 faces), the two eagle forelegs with talons
(1,558, 1,408), the tail tuft (387) and the two eyes (117, 94). Weld 48,330 -> 164 open edges (unchanged by every
step); no two-sided sheets (the weld kept all 16,126 triangles); 18 coincident vertices with other weights (separated
by `decimate_tex.py`).

## Ladder

Limits are scaled to `REA_HEIGHT_M=2.0` (the rest pose stands 2.75 m to the raised wing tips and spans 3.6 m; 2.0 is
the body height, the stricter choice): p99 6 mm, max 30 mm.

Region budgets (`make_groups.py`, dominant bone):
- **Kept exactly:** the eyes.
- **Head** (head feathers, beak, mouth): 55 %.
- **Wings** (Wing1-3): 70 %, their thin feathers are the silhouette.
- **Eagle forelegs and talons** (their own pieces): 50 %.
- **Tail tuft:** 60 %.
- **Body** (spine, neck, hind legs, tail chain): fills the rest.

| step | locks | groups head/wing/fore/tuft | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| u1 | eyes | uniform | 9,674 (60 %) | 5.33 / 47.3 | 0.995 | 0.997 | fail (max) |
| g1 | eyes | 65 / 70 / 60 / 65 | 10,478 (65 %) | 5.33 / 25.2 | 0.995 | 0.997 | pass |
| g1 | eyes | 65 / 70 / 60 / 65 | 8,866 (55 %) | 7.96 / 32.1 | 0.991 | 0.996 | fail |
| g2 | eyes | 55 / 65 / 50 / 60 | 8,864 (55 %) | 6.43 / 32.1 | 0.992 | 0.996 | fail |
| e1 | + error lock | 55 / 65 / 50 / 60 | 9,672 (60 %) | 5.70 / 51.2 | 0.992 | 0.996 | fail (wing tip) |
| s1 | e1 + wing-tip spot | 55 / 70 / 50 / 60 | 9,672 (60 %) | 5.33 / 15.6 | 0.993 | 0.996 | pass |
| s1 | e1 + wing-tip spot | 55 / 70 / 50 / 60 | 8,866 (55 %) | 6.24 / 17.6 | 0.992 | 0.996 | fail (p99) |
| **s1b** | e1 + wing-tip spot | 55 / 70 / 50 / 60 | **9,188 (57 %)** | **5.78 / 15.6** | **0.992** | **0.996** | **picked** (`Cand_56`) |

- **Weights:** UV weights (`uv_weights.py`, `REA_WEIGHTS=component`); source vertices keep their weights exactly.
- **Error lock** (`err_lock.py`, Cand_55 of g2, over 15 mm, 2.5 cm radius): 28 vertices at the wing roots and inner
  wings that fold in Death and Attack; 167 faces kept.
- **Wing-tip spot:** the lock moved the right wing's longest primary-feather tip into the decimated part, which then
  lost it (51 mm). `spot_lock.py` keeps 3 cm around it; one spot, no second lock round.
- **Worst point** at 57 %: 15.6 mm in Attack frame 12 (the max limit is 30).

Close-ups of `work/ladder_s1b.blend` (source | 58 % | 57 %), textured and clay: `review/close/sheet1_*.png` (head
front, three-quarter and right, beak, crest, both talons, hind paws, tail tuft, back, belly) and `sheet2_*.png` (both
wings from above and below, both wing tips, flank, Fly up-stroke, Attack, Death, head left). Feathers, talons, crest
spikes, the beak and the tuft keep their shape; the welded source renders faceted there because its custom normals are
cleared (see below).

Texture checks at 57 %:
- **Drift (`texture_drift.py`):** two faces over 40 (8.5 cm² in all, on a 3.6 m creature).
- **Slivers (`dark_slivers.py`, `REA_DARK_L=80 REA_DARK_N=4`):** 5 dark and 5 light faces, 1-8 cm² each, at the mouth
  corner and on the talon tips (dark claw against yellow scale). No change in the textured close-ups.

## Shading: smooth (default) or flat

The project export shades 93 % of its faces flat: Meshy's facets, which `uv_export.py` carried through (every
triangle has its own vertices). Batch decision (as the Rat reduction): **the reduced export is smooth-shaded**, which
also cuts the vertex data to about a quarter (7.3 MB file against 15.5 MB). `REA_FLAT=1 scripts/build_reduced.sh`
builds the flat alternative `export/mm7_m258_flat.glb` (each face takes the flat/smooth flag of the nearest source
face; 10.4 MB). Straight from the GLBs (`glb_close.py`, `review/glbclose/sheet_tex.png`, `sheet_clay.png`: source |
smooth | flat), the textured models look almost the same; in clay the smooth one loses the facets. The viewer has tier A
in both.

## Build

`scripts/build_reduced.sh` ([`REA_FLAT=1`]): `export_cand.py` (Cand_56 of `work/ladder_s1b.blend`, REA_NODE=M258) ->
`swap_lod0.py` into the pre-reduction export LOD0 (material, clips, node structure unchanged) ->
`tools/prepare_actor_glb.py` -> `build_lods.py` -> the Griffin's own `shrink_shadow_lods.py` ->
`claude_shared/region_variants.py` with the same ramps and `--extra` arguments as `mm7_m258_claude/scripts/build_runtime.sh`.
All 8 primitives (LOD0-3 and their shadows) carry the three tier variants; materials, textures, images, samplers,
nodes and animations match the pre-reduction export.

`build_lods.py`: ratios 0.5 / 0.25 / 0.1 of LOD0; protected points are the outer 2 cm at the top, both wing tips and
both ends (beak, tail tuft) and LOD0 vertices within 1 cm of the floor in any Death/Dead frame (on its back, wings flat).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| pre-reduction | 16,126 | 8,062 | 2,902 | 966 |
| reduced | **9,188** | 4,593 | 2,297 | 917 |

`lod_check.py` on every LOD of `export/mm7_m258.glb` (now also the largest edge stretch per clip):
- bounds kept at every LOD: 3.6 m wing span, 3.05 m long, 2.75 m high (same as pre-reduction);
- lowest point: Fly/Attack/Hit 2.0-2.4 cm above the floor (as before), Death and Dead at 0.0 at every LOD; the
  pre-reduction LOD3 corpse floated 1.1 cm;
- faces over 20x their rest area: none, except one in LOD3 Death (the pre-reduction LOD3 has the same one);
- edge stretch LOD0: Death 10.56 (identical to the pre-reduction model, the wing root in the fold), Attack 6.56, Fly
  6.72, Hit 5.71, Dead 5.64 (pre-reduction 6.56 / 6.72 / 6.38 / 6.32); LOD1-3 at most 6.7.

`review/lods/sheet.png`: every LOD at rest and in the Attack, pre-reduction and reduced.
`check_winding.py`: 0 inverted closed parts.

## Viewer

`review/viewer/`: http://127.0.0.1:8912/level_generation/creatures/mm7_m258_reduce_claude/review/viewer/index.html
Pre-reduction and reduced (smooth) for tiers A, B and C, plus reduced flat-shaded tier A; opens on the reduced tier A
in Fly. `run_creature_review.py check`: 35 switches, no console errors.

## For the user to review

- Smooth or flat shading (viewer tier A has both; `review/glbclose/`).
- The wing feathers at the far LOD3 are as blocky as before.

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m258_reduce_claude/export/mm7_m258.glb --world mm7
```

The `actors.yml` binding in `../mm7_m258_claude/README.md` is unchanged (same node, bones, clips, sockets and
variants). Rollback: `work/mm7_m258_source_pre_reduce.glb`.

Reproduce:
1. `REA_NODE=M258 REA_GLB=level_generation/creatures/mm7_m258_reduce_claude/work/mm7_m258_lod0_pre_reduce.glb blender -b -P scripts/import_source.py`;
2. `dump_mesh.py`, `dump_faces.py`, `dump_weights.py` (blender), `make_groups.py`;
3. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.55,2:0.65,3:0.5,4:0.6 run_ladder.sh g2 0.6,0.55`;
4. `cp work/ladder_g2.blend work/ladder.blend; REA_CAND=Cand_55 REA_ERR_MM=15 REA_LOCK_R=0.025 blender -b -P scripts/err_lock.py -- work/keep_base.npy work/keep_e1.npy`;
5. `spot_lock.py work/keep_e1.npy work/keep_s1.npy 0.03 -1.759,-0.48,1.752`;
6. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep_s1.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.55,2:0.7,3:0.5,4:0.6 run_ladder.sh s1b 0.6,0.58,0.57`
   (`run_ladder.sh` defaults to `REA_HEIGHT_M=2.0`);
7. `close_griffin.py -- ladder_s1b.blend Cand_57,Cand_56`, `pair_sheet.py`, `texture_drift.py r56`, `dark_slivers.py r56`;
8. `scripts/build_reduced.sh`, `REA_FLAT=1 scripts/build_reduced.sh`;
9. `lod_check.py -- export/mm7_m258.glb r57`, `LOD_SCALE=4.2 LOD_CZ=1.3 LOD_ATTACK_F=16 lod_views.py -- src,r57`,
   `glb_close.py -- source=...,smooth=export/mm7_m258.glb,flat=export/mm7_m258_flat.glb`;
10. `viewer_tiers.py r100=work/mm7_m258_lod0_pre_reduce.glb r57=work/pick_lod0_raw.glb r57flat=work/pick_lod0_raw_flat.glb`, `update_viewer_manifest.py`.
