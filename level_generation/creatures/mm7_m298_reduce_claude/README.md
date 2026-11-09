# MM7 Ooze (`m298`, Emerald / Sapphire / Bloodstone Ooze) reduction (2026-10-20)

The user asked for triangle reduction of the five batch I models ("do the tri reduction on all 5"). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding, so the batch I
textures, region mask and tier ramps stay valid. No Meshy credits. Scripts are copied from `mm7_m278_reduce_claude/`
and adapted to the ooze (node `Ooze`, Ooze spots and views); `shrink_shadow_lods.py` is the batch I project's own.
Batch rules: nothing installed, nothing written to `assets_dev/` or `assets_source/`; in `../mm7_m298_claude/` only the
"Reduced version" note in its README.

Source: the batch I export `../mm7_m298_claude/export/mm7_m298.glb`, copied to `work/mm7_m298_source_pre_reduce.glb`
(rollback source). One material `Ooze_A` (variants `Ooze_B`/`Ooze_C` through `KHR_materials_variants`, tiers
`m298_a/b/c`), one `Ooze` node, 30 bones + `Socket_Spit`, 9 clips. Smooth-shaded, as the reduced export.

Pieces (14 separate shells, `make_groups.py`): the blob (3,294 faces, lump weights), the pseudopod (stalk 360 faces on
PodRoot/Pod1–5, onion knob 240 faces rigid on Knob) and 12 globules (64 faces each, rigid on Glob_NN). The weld found
no coincident vertices with other weights.

## Ladder

Limits for the 1.0 m blob width (the creature's largest dimension; `REA_HEIGHT_M=1.0`): p99 3 mm, max 15 mm,
IoU >= 0.98, SSIM >= 0.93. Views: the six Standing views (pod and globules hidden), the pod at its tallest (Attack frame
12, side and three-quarter) and the scattered globules (Dead). UV weights (`uv_weights.py`, `REA_WEIGHTS=component`),
restricted here to the vertex's own region: the pod and globule UVs lie on a disc of the blob's underside island, so an
unrestricted UV hit could hand a pod vertex underside lump weights. Source vertices keep their weights exactly.

| run | blob | stalk / knob / globules | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| b1 | 79 % | kept | 3,682 | 3.72 / 7.08 | 0.992 | 0.980 | fail (p99) |
| b1 | 72 % / 65 % / 57 % | kept | 3,356 / 3,030 / 2,702 | 4.51 / 5.42 / 6.61 | 0.990–0.985 | 0.976–0.966 | fail |
| t0.2 (UV weight 0.2) | 79 % / 72 % / 65 % | kept | 3,682 / 3,356 / 3,030 | 3.60 / 4.18 / 5.09 | 0.992–0.987 | | fail |
| p1 | kept | 80 / 65 / 75 % | 4,314 | 1.33 / 10.8 (Dead p99 5.8) | **0.975** (Dead) | 0.986 | fail: globules |
| p2 | kept | 70 / 50 / 60 % | 4,124 | 2.02 / 16.0 | 0.953 (Dead) | 0.985 | fail |
| q1 | kept | 70 / 50 % / kept | 4,432 | 1.16 / 10.4 | 0.996 | 0.986 | pass |
| e4 / e5 (error locks) | rest at 80 % overall | 70 / 50 % / kept | 3,728 | 4.08 / 3.37 | 0.993 | 0.981 | fail |
| g0.2 | 84 % | 70 / 50 % / kept | 3,904 | 2.90 / 10.4 | 0.994 | 0.983 | pass, **knob rejected** |
| h | 86 % | 70 / 75 % / kept | 3,966 | 2.81 / 5.61 | 0.995 | 0.984 | pass |
| **h** | **82 %** | **70 / 75 % / kept** | **3,904** | **2.87 / 5.61** | **0.995** | **0.983** | **picked** |
| h2 | 80 % | 70 / 75 % / kept | 3,844 | 2.98 / 5.73 | 0.995 | 0.983 | pass overall, Attack/Cast/Running p99 3.02–3.09 |
| h2 | 78 % | 70 / 75 % / kept | 3,774 | 3.13 / 5.73 | 0.994 | 0.982 | fail |

- **The blob is already lean.** The batch I build cut it to 3,294 triangles (mean edge 33 mm). The error is static,
  not deformation: Standing has the same p99 as every clip. Every 1 % of blob triangles removed costs about 0.06 mm
  of p99. Error locks (`err_lock.py` on Cand_72, misses over 4 or 5 mm, 1 cm) only moved the error elsewhere (the
  playbook's warning). The 2.5–3.5k target is not reachable without measured loss: 3,030 triangles (blob 65 %) looked
  the same in the ladder sheet, but its p99 was 5.4 mm.
- **Collapse weights:** `REA_TEXW=0.2` (the MeshLab UV term at 0.2 instead of 1.0) lowers the p99 about 0.1 mm per step.
  The slime texture is uniform noise, and drift stays low (below).
- **Globules stay exact:** they are 64-face spheres, and any cut dents them (Dead p99 5.8 mm, IoU 0.975 at 75 %).
- **Knob at 75 %, not 50 %:** at 50 % the swollen Cast knob had a visibly polygonal outline and a facet on its
  silhouette (`review/close/` g0.2 run, removed). At 75 % it matches the source's own faceting.
- **Pick 83.8 % (`Cand_83` of `work/ladder_h.blend`)**, not the lowest overall pass (3,844): that step goes just over
  3 mm p99 in three clips. The pick stays at or under 2.99 mm in every clip (Attack 2.98, Cast 2.99, Running 2.90).

Close-ups (`close_ooze.py`; `review/close/sheet_r83_tex.png`, `sheet_r83_clay.png`): blob top, front, side, back, both
rims, Walking, Hit, the pod at its tallest, the knob, the lash, the swollen Cast knob, Death column, Dead globules,
Fidget bubbles. They match the source. From the GLBs directly (`glb_close.py`, the files' own normals):
`review/glbclose/sheet_tex.png`, `sheet_clay.png`. Ladder sheet: `review/ladder_sheet.png` (last run).

Texture checks (batch I 2K base colour; the region mask is 1 everywhere):
- **Drift (`texture_drift.py r83`):** 0 faces over 40, p99 14.5. The largest drifts (17–20) are on the knob, whose
  texture is mapped onto the underside disc.
- **Dark slivers (`dark_slivers.py`, `REA_DARK_L=80 REA_DARK_N=4`):** none.

## Build

`scripts/build_reduced.sh export/mm7_m298.glb`: `export_cand.py` (Cand_83, node `Ooze`) -> `swap_lod0.py` (onto the
rollback source; materials, variants, clips and `Socket_Spit` byte for byte) -> `build_lods.py` (the tool's default
ratios 0.5 / 0.18 / 0.06, as the batch I build; protected: bounding extremes within 5 mm, including the knob tip, and
LOD0 vertices within 4 mm of the floor in any Death/Dead frame) -> `shrink_shadow_lods.py` -> `carry_variants.py`
(tier mapping carried to the 7 LOD/shadow primitives). Materials, variants, nodes, images and clips are identical to
the batch I file.

| | LOD0 | LOD1 | LOD2 | LOD3 | file |
|---|---:|---:|---:|---:|---:|
| batch I | 4,662 | 2,330 | 838 | 273 | 8.57 MB |
| reduced | **3,904** | 1,952 | 702 | 232 | 8.29 MB |

LOD0 parts: blob 2,706 (82 %), stalk 250, knob 180, globules 768 (kept). The file is mostly the 2K/1K maps.
LOD renders: `review/lods_sheet.png` (Standing three-quarter and Attack frame 12 per LOD, batch I and reduced).

## Gates

- **Separate pieces** (`piece_check.py`, every colour and shadow LOD): 14 pieces in each, none mixing blob, pod and
  globule bones or two globules. PASS (batch I: PASS).
- **Floor, blob only** (`blob_floor.py`, every frame of every clip): never below the floor and never lifted, except the
  intentional 68.5 mm Death hop; identical to batch I.
- **Floor, every LOD** (`lod_check.py`, every frame): LOD0, LOD1 and LOD3 never below 0. **LOD2 has one globule vertex
  (Glob_00) 4.5 mm under the floor** in the bind pose, Death and Dead. A collapse placed it there; the floor lock does
  not stop it (1 cm and 6 mm locks gave the same dip, and the 1 cm lock pushed LOD3 to 442 triangles). Batch I LOD2
  and LOD3 sank 7.7 and 13.5 mm, so the reduced chain is better.
- **Stretch:** no face stretches over 20× in any clip at any LOD. Edge stretch on LOD0 (`glb_stretch.py`) matches
  batch I in every clip (max 2.02 Fidget, 1.67 Running, 1.65 Cast against 1.66).
- **Bounds:** every LOD keeps the batch I bounds (pod tip 0.85 m, globule ring −0.64 … 0.77 m).
- **`check_winding.py`:** 0 inverted closed parts.
- **Viewer:** `run_creature_review.py check`: 54 switches (6 models × 9 clips), no console errors, failed [].

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m298_reduce_claude/review/viewer/index.html`: batch I (`r100`)
and reduced (`r83`) for tiers A, B and C (ramps baked by `scripts/viewer_tiers.py`, which writes only into this
project), opening on the reduced tier A. Shots: `review/viewer_shots.png`.

## For the user to review

- The saving is modest (4,662 -> 3,904, 16 %); the lumpy blob does not go lower without measured loss. The 3,030
  step (blob 65 %, p99 5.4 mm) looked the same in the ladder sheet. If you accept that error, rerun
  `run_ladder.sh` with a lower ratio and rebuild.
- The knob at 75 % up close in Cast (the swell).
- LOD2's 4.5 mm globule dip under the floor (Dead corpse at distance; the batch I LODs dipped more).

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m298_reduce_claude/export/mm7_m298.glb --world mm7
```

The `actors.yml` binding in `../mm7_m298_claude/README.md` is unchanged (same file name, nodes, clips, socket; scale
178). Rollback: `work/mm7_m298_source_pre_reduce.glb`.

Reproduce (from this directory; Blender through `tools/run_creature_blender.sh` with the lease token, venv with
pymeshlab/scipy/PIL as `REA_VENV`):
1. `REA_NODE=Ooze REA_GLB=level_generation/creatures/mm7_m298_reduce_claude/work/mm7_m298_source_pre_reduce.glb` `import_source.py`;
2. `dump_mesh.py`, `dump_faces.py`, `dump_weights.py` (Blender), `make_groups.py`;
3. `REA_TEXW=0.2 REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.75 REA_WEIGHTS=component REA_KEEP_FACES=work/keep_glob.npy scripts/run_ladder.sh h 0.838`;
4. `close_ooze.py ladder_h.blend Cand_83`, `pair_sheet.py`, `texture_drift.py r83`, `dark_slivers.py r83`;
5. `scripts/build_reduced.sh export/mm7_m298.glb`;
6. `piece_check.py`, `lod_check.py <glb> red` (`REA_NODE=Ooze`), `glb_stretch.py <glb> Ooze`, `blob_floor.py`,
   `check_winding.py`, `glb_close.py`, `lod_views.py`, `review_sheets.py`, `viewer_tiers.py`, `run_creature_review.py check`.
