# MM7 Peasant Dwarf Male (`m302`, descriptors 322-330) reduction (2026-10-20)

User: "OK reduce tris count now" (the five MM7 batch-J peasants; this project is m302 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the nine colour looks (`KHR_materials_variants`) and the region ramps stay valid. No Meshy credits.
Scripts from batch C's dwarf, [`../mm7_m190_reduce_claude/`](../mm7_m190_reduce_claude/README.md) (paths, shells,
height and names adapted). **Not installed** (batch J: the user installs later; no REDUCTION_LEDGER row yet).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m302_reduce_claude/review/viewer/) (source vs
reduced, all nine looks, six clips, club under its `Sword` joint) · [close-ups](review/glbclose/sheet_head.png),
[body](review/glbclose/sheet_body.png), [legs](review/glbclose/sheet_legs.png) · [viewer shots](review/shots_sheet.png),
[heads](review/shots_heads.png)

## Source

`../mm7_m302_claude/export/mm7_m302.glb` and `mm7_m302_club.glb` (after the 2026-10-20 walk fix), copied byte for byte
to `work/mm7_m302_source_pre_reduce.glb` and `work/mm7_m302_club_source_pre_reduce.glb` (rollback sources; sha256
97b7090c... and 9441db26...). One merged body + head atlas material per look (`Dwarf_A1`...`Dwarf_C3`, 2080x1024, head
half u > 0.51), node `Dwarf`, 57 joints, shadow LODs, clips Standing, Walking, Hit, Death, Dead, Fidget. Bind height
1.35 m (ladder limits p99 4.0 mm, max 20.1 mm; IoU, SSIM as the shared ladder). Weld (identical weights only): 6,361 ->
417 open edges, no coincident vertices with other weights, 10,429 triangles in and out.

The source was already reduced once in its build (15.5k -> 10.4k per shell with head and hands protected), so its
surface is lean, as batch C found on its dwarf.

## Where the triangles are (`scripts/source_pieces.py` + `m302_pieces.py`, shells of the build's Smart Topology return)

| shell | faces | |
|---|---:|---|
| 0 skin (torso, arms with the painted bracers, hands, neck, face) | 4,999 | hands 1,608 and face front 1,342 kept |
| 1 vest with its fleece trim | 999 | |
| 2 beard | 999 | |
| 3 trousers (painted belt and buckle) | 900 | belt 139 kept |
| 4 cap | 700 | |
| 5 nape hair | 449 | |
| 6/7 boots with fleece cuffs | 998 | soles 364 kept |
| 8/9 eyes | 385 | kept |

1,717 faces are never seen from any view (`visibility.py`): mostly skin under the vest and beard, scalp under the cap.

## Keep set (`scripts/m302_sets.py`, pick = set `d`)

Kept exactly (4,253 faces): both hands and every face touching a vertex with hand + finger weight > 0.3 (the fitted fist
on the club); the eyes; the boot soles (below 6 cm); the face front (head-set skin within 7 cm of the face centre); the
painted belt and buckle (trouser faces above 0.60 m of dark leather or grey metal colour); the painted bracers
(forearm-dominant skin faces of leather colour); 3 cm patches (mirrored) at the max-error spots of the first ladders
(`patch_c.npy`, `patch_d.npy`: trouser crotch, hip below the vest, vest front at the armholes, chest under the beard,
upper back, left upper arm). Groups: hidden head skin and hidden body faces at 70 %, fleece trims (by colour) at 90 %;
everything else (visible head set: beard, cap, hair, face rest; vest leather, trousers, boots, visible skin) takes one
shared cut.

## Ladder

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 10,429 | | | | |
| a: hidden 40 %, fleece 85 %, shared 85-70 % | r86-r79 | 9,007-8,311 | 9.68-10.0 / 38.95 | 0.994-0.990 | 0.993-0.991 | fail (hidden head skin p99 24 mm) |
| b: hidden 70 %, fleece 90 %, shared 90-80 % | r91 / r89 / r87 | 9,569 / 9,289 / 9,103 | 2.60 / 2.86 / 3.08 ... 3.46 / 24.2 | | | pass / pass / fail (max: crotch, Death) |
| c: b + 5 patches | r90-r84 | 9,411-8,863 | 2.75-3.78 / 20.58 | | | fail (max: vest front at the armhole, Walking) |
| d: c + 6 patches | r90 / r88 / r87 / r85 | 9,463 / 9,287 / 9,111 / 8,933 | 2.59 / 2.94 / 3.22 / 3.56, max 16.8-18.1 | 0.996-0.993 | 0.994-0.993 | pass |
| **e: d's sets, shared 70-58 %** | **r83** | **8,755** | **3.90 / 18.12** | **0.9915** | **0.9916** | **pick** |
| e | r82 / r80 / r78 | 8,579 / 8,401 / 8,225 | 4.25 / 4.98 / 5.63 | | | fail (p99) |
| f: per region (vest 60 %, hidden head 50 %, visible skin 88 %) | r86-r81 | 9,057-8,527 | 3.94-4.39 / 25.5 | | | fail |

Per region at r83 (`region_error.py`): visible arm/torso skin p99 8.1 mm, trousers 5.3, head set 4.5, vest leather 2.8,
hidden head skin 2.1. Budgets per region (config f) did worse than the shared cut, as on batch C's dwarf. The pick is the
lowest passing step; the 85 % step (8,933) looked the same in every close-up.

Texture drift on the pick (`texture_drift.py`, `drift_visible.py e_r83`): 3 visible faces over 40 (18.3 cm²), at the
beard tip; the textured close-ups show no change, so no drift lock.

## Build

`REA_KEPT_NORMALS=1 cand_glb.sh e Cand_83 kn` (source normals on unchanged faces and kept smooth vertices) ->
`work/e83_lod0.glb` -> `tip_points.py e_r83` (cap tip, cap top, beard tip) and `floor_points.py` (`REA_FLOOR_MM=30`,
24 Death/Dead floor contacts) -> `build_lods.py` (`tools/build_actor_lods.py`, ratios 0.5 / 0.21 / 0.07, 27 protected
points) -> `shrink_shadow_lods.py` (the source project's) -> `carry_variants.py` (in place) -> `check_winding.py` (0
inverted closed parts): `export/mm7_m302.glb`, 6.51 MB (source 6.69 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 10,429 | 5,213 | 1,875 | 623 |
| reduced body | 8,755 | 4,376 | 1,837 | 612 |
| club (`export/mm7_m302_club.glb`, byte-identical copy) | 1,104 | 552 | 198 | 66 |

The club stays byte-identical: a clean 12-sided lathe with its own LODs; reducing it gains little and would touch the
fitted grip band.

## Checks

- `compare_glb.py` (`work/compare_glb.log`): nodes, skin, materials and extras, images, all six clips and the variants
  extension identical to the source; `KHR_materials_variants` on all eight colour/shadow primitives; only the mesh
  geometry differs.
- `grip_check.py` (`work/grip_check.log`): all 1,167 LOD0 vertices with hand + finger weight > 0.5 keep their bind
  positions (max 0.0004 mm) and weights exactly: the fist on the club is unchanged.
- `lod_check.py` (source and pick): the top is 1.3522 m at every LOD (source 1.3501; the cut moved one cap vertex 2 mm
  up), every LOD keeps the cap tip (the source LOD3 had lost 2 cm of it: rest max y 0.279 vs 0.299), the lowest point per
  clip equals the source LOD0's, Dead lies on the floor at every LOD (0.5 mm), no face stretches over 20x at any LOD.
- Close-ups straight from the GLBs, source vs 85 % vs 83 %, textured and clay (`glb_close.py`, `glb_sheet.py`): face,
  beard, cap from every side, vest and fleece, both hands, arms, belt and trousers, walk, boots, fidget, death.
- Viewer: `review/viewer/` (source vs pick, all nine looks, the club added under `Sword` for review only by
  `viewer_club.py`); `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m302_reduce_claude
  check`: 108 switches, no console errors. Shots of looks b1 (source and pick), a1 and c2.

## Open points for review

- The saving is modest (16 % at LOD0): over 40 % of the mesh is kept exactly (hands, face, belt, bracers, soles, eyes,
  patches) and the rest was already reduced in the build; the next step down fails p99.
- The model top is 2 mm higher (cap vertex); the actors.yml scale of the source binding stays valid.

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m302_reduce_claude/export/mm7_m302.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m302_reduce_claude/export/mm7_m302_club.glb --world mm7
```

then the binding from `../mm7_m302_claude/README.md` (nine descriptors, scale 89.57, unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m302_source_pre_reduce.glb` (+ the club
source) the same way.

## Reproduce

`REA_GLB=<abs path of work/mm7_m302_source_pre_reduce.glb> REA_NODE=Dwarf import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m302_source_pre_reduce.glb` -> `source_pieces.py` -> `m302_pieces.py`
-> `visibility.py -0.01 1.36` (copy to `work/visible_all.npy`) -> `REA_PATCH_R=0.03 patch_keep.py - work/patch_c.npy
-0.019,-0.08,0.408 0.135,-0.065,0.756 -0.107,-0.177,0.818 0.0,-0.139,0.976 0.092,0.073,0.888`, then `patch_keep.py
work/patch_c.npy work/patch_d.npy 0.127,-0.156,0.918 0.063,-0.178,0.919 -0.005,0.067,0.975 0.222,-0.096,0.795
0.078,0.081,0.936 0.097,0.05,0.805` -> `M302_EXTRA_KEEP=work/patch_d.npy m302_sets.py d` (copy keep/groups to `e`) ->
`TOKEN=<lease> run_ladder.sh e e "2:0.7,8:0.7,3:0.9" 0.7,0.66,0.62,0.58` -> `region_error.py`, `probe_max.py`,
`texture_drift.py`, `drift_visible.py` -> `REA_KEPT_NORMALS=1 cand_glb.sh e Cand_83 kn` (copy to `work/e83_lod0.glb`) ->
`tip_points.py e_r83`, `REA_NODE=Dwarf REA_FLOOR_MM=30 REA_FLOOR_N=24 floor_points.py` -> build as above ->
`compare_glb.py`, `grip_check.py <src> <glb> Dwarf`, `REA_NODE=Dwarf lod_check.py`, `glb_close.py`, `viewer_variants.py`
(r100 and r83), `viewer_club.py`, `viewer_manifest.py "MM7 Peasant Dwarf Male" r83 10429 8755`. Blender scripts run
through `scripts/bl.sh` (lease wrapper, `TOKEN`). The MeshLab step uses the pymeshlab venv named in `run_ladder.sh`.

## Installed (2026-10-20)

User: "OK accept all, to assets_source, assets_dev". `check_winding.py` 0 inverted closed parts; installed with
`tools/install_model.py ... --world mm7` (sources in `assets_source/worlds/mm7/models/` equal the exports; cooked
runtime copies in `assets_dev/worlds/mm7/models/`). Nine `actors.yml` bindings added to
`assets_dev/worlds/mm7/models/actors.yml` from the production README's template (descriptor -> palette -> skin from
`../mm7_m302/variants.json` and the ramps file); every skin, clip, look node and attachment checked against both GLBs.
Boot check: `7out02.odm` (Harmondale) with spawned peasants of all five batch J models, 185 outdoor actors textured,
no missing models and no errors in the log (`output/batchJ_boot/`). Ledger row added to `../REDUCTION_LEDGER.md`.

## Gait rollout (2026-10-31)

Package [h13](../gait_rollout_20261031/h13/README.md) appended one clip to the installed source
`assets_source/worlds/mm7/models/mm7_m302.glb` (every existing clip, mesh, skin and material byte-identical): `Jog`
(humanoid set Unarmed-Run-Forward legs; arms and club from Walking; 0.70 s), bound for the peasants' flight (Wimps flee at 2x Spd in both rulesets) as `run: Jog`,
`run_stride_length: 2.2249` (the package's `bindings.yml`, applied by the coordinator). The club arm bends only 30 deg forward so the club stays at hip height.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h13/scripts/rebuild.sh m302`, then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h13/export/mm7_m302.glb --world mm7
--name mm7_m302.glb`. A far-LOD repair, head-bob or reduction rerun that re-exports this model must re-graft the Jog: copy
the new source over `h13/work/mm7_m302_pre_gait.glb` and rerun the rebuild.
