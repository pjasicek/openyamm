# MM7 Peasant Human2 Male (`m362`, descriptors 367-375) reduction (2026-10-20)

User: "do tris reduction on all 5" (the MM7 batch-K peasants; this project is m362 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the nine looks (`KHR_materials_variants`) and the region ramps stay valid. No Meshy credits.
**Not installed** (batch K: the user installs later). Scripts from batch J's elf peasant,
[`../mm7_m332_reduce_claude/`](../mm7_m332_reduce_claude/README.md) (paths, node `M362`, height; its piece/set scripts
replaced by `m362_pieces.py`, `m362_sets.py`).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m362_reduce_claude/review/viewer/) (source vs
reduced, all nine looks, six clips) · close-ups [head and torso](review/glbclose/sheet_h86_a.png),
[arms, rapier, boots, clips](review/glbclose/sheet_h86_b.png) · [viewer shots](review/shots_tiers.png)

## Source

`../mm7_m362_claude/export/mm7_m362.glb` (after the 2026-10-20 walk fix with Mixamo Standard Walk; sha256 930fbee9...),
copied to `work/mm7_m362_source_pre_reduce.glb` (rollback source, byte-identical). One merged body + head atlas material
per look (`M362_AA`…`M362_CC`, 2080x1024, region mask R doublet and shoulder rolls, G hair, B stubble), node `M362`,
56 joints, shadow LODs, clips Standing, Walking, Hit, Death, Dead, Fidget. Bind height 1.7007 m (ladder limits p99
5.1 mm, max 25.5 mm; IoU >= 0.98, SSIM >= 0.93). Weld (identical weights only): 6,030 -> 841 open edges, 4 coincident
vertices with other weights (kept apart), 9,448 triangles in and out.

The source was already reduced once in its build (14.3k -> 9.4k per garment with head and hands protected), so its
surface is lean: batch J's ratios (45-62 % per region) failed every region here (config a).

## Where the triangles are (`scripts/m362_pieces.py`: the production master's Smart Topology `piece` attribute, mapped by rest position, max 0.0004 mm)

| label | piece | faces | |
|---|---|---:|---|
| 1 | head, neck, chest skin P00 | 1,920 | face front 836 kept |
| 2 | doublet P04 | 408 | stripe edges kept |
| 3 / 4 | hands L / R (separate shells) | 1,110 / 1,078 | kept exactly |
| 5 | hair P07 and strands | 900 | |
| 6 | breeches P03 | 427 | |
| 7 | boots P05/P06 | 505 | soles 194 kept |
| 8 | shirt sleeves and cuffs | 552 | |
| 9 | shoulder rolls P08/P09 | 600 | |
| 10 | doublet skirt, collar, belt, boot cuffs | 800 | |
| 11 | sheathed rapier (hilt pieces, scabbard) | 500 | kept exactly |
| 12 | eyes and mouth | 497 | kept exactly |
| 13 | belt studs, chest laces | 151 | kept exactly |

## Keep set and groups (`scripts/m362_sets.py` + patches, pick = set `h`)

Kept exactly (`work/keep_h.npy`, 4,786 faces): both hands (every face touching a vertex with hand + finger weight > 0.3),
eyes and mouth, studs and laces, the whole rapier (thin scabbard tube and small hilt pieces taper at any cut), the soles
(boot faces below 6 cm), the visible face front (head skin seen in some view, y < -1 cm, |x| < 7.5 cm, above z 1.46;
836 faces), every face on a painted region edge (mask R between 0.1 and 0.9: the doublet and shoulder-roll stripes; G:
the hairline; 290 faces), and 3 cm patches (`patch_keep.py`, mirrored) at the shirt-sleeve hem beside the torso and the
torso side under the arm (the max-error spots of config c: 26 mm in Death, 20 mm in Hit).

| group | faces | ratio |
|---|---:|---|
| 1 visible head sides and back | 354 | 50 % |
| 2 hidden head skin (under the hair) | 661 | 70 % |
| 3 doublet | 354 | 80 % |
| 4 hair | 900 | 70 % |
| 5 breeches | 427 | 75 % |
| 6 hidden body skin | 6 | 60 % |
| 7 shirt sleeves and cuffs | 445 | 80 % |
| 8 shoulder rolls | 400 | 85 % |
| 9 doublet skirt, collar, belt, boot cuffs | 770 | 72 % |
| 10 boot uppers | 311 | 75 % |
| free (visible neck/chest skin) | 61 | 80 % |

## Ladder (`review/ladder_sheet_<config>.png`)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 9,448 | | | | |
| a: batch J ratios (45-65 %) | r78 | 7,552 | 9.52 / 43.1 | 0.985 | 0.989 | fail (every region over; shoulder rolls 26 mm, hair top 25 mm even in Standing) |
| b: 60-85 % | r88 | 8,324 | 5.02 / 29.1 | 0.994 | 0.996 | fail (max: right sleeve hem, Hit) |
| c: hidden head 80 %, sleeves 85 %, rolls 90 % | r90 | 8,552 | 3.81 / 26.3 | 0.996 | 0.997 | fail (max: sleeve hem beside the torso, Death) |
| d: c + sleeve-hem/torso-side patches | r90 | 8,556 | 3.79 / 19.4 | 0.995 | 0.997 | pass |
| e: d's sets, 60-85 % | r87 | 8,278 | 4.72 / 20.8 | 0.993 | 0.995 | pass |
| f: d's sets, 55-80 % | r84 | 8,014 | 6.60 / 25.2 | 0.990 | 0.993 | fail (p99) |
| g: d's sets, 50-75 % | r82 | 7,786 | 7.94 / 31.4 | 0.988 | 0.991 | fail |
| **h: e + head sides 50 %, skirt/belt/cuffs 72 %** | **r86** | **8,180** | **4.80 / 20.8** | **0.9925** | **0.9948** | **pick** |

All candidates have 842 open edges against the source's 841: the extra one is on the kept single-triangle piece P45
between the eyes (`open_diff.py`), a weld-count artefact, not a hole; `compare_ladder.py` takes `REA_OPEN_TOL=1` for it.
Per region at the e step (`region_error.py`) the hair, sleeves, shoulder rolls and boot uppers sat at p99 7-8 mm, so only
the visible head sides and the skirt/belt/cuff group had headroom (h). Texture drift on the pick (`texture_drift.py`,
`drift_visible.py h_r86`): 2 visible faces over 40 (3.6 cm²), none over 3 cm²; no drift lock.

## Build

`REA_KEPT_NORMALS=1 cand_glb.sh h Cand_86 kn` (source GLB normals on unchanged faces and kept smooth vertices) ->
`work/h86_lod0.glb` -> `REA_CAP_Z=1.68 cap_points.py` (13 hair-top points) and `REA_FLOOR_MM=30 floor_points.py` (24
Dead/Death floor contacts) -> `REA_LOD_RATIOS=0.5,0.2,0.066 build_lods.py` (`tools/build_actor_lods.py`, 37 protected
points) -> `MESH_NODE=M362 shrink_shadow_lods.py` (shadow LODs inset up to 15 mm) -> `carry_variants.py` (7 primitives)
-> `check_winding.py` (0 inverted closed parts): `export/mm7_m362.glb`, 6.84 MB (source 7.06 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 9,448 | 4,718 | 1,695 | 558 |
| reduced body | **8,180** | **4,085** | **1,630** | **532** |

Checks:
- `compare_glb.py`: nodes, skin, materials and extras, images, all six clips and the variants identical to the source;
  `KHR_materials_variants` on all colour and shadow primitives. `DIFFERENCES none`.
- `grip_check.py` + `grip_exact.py`: all 1,546 hand vertices keep their bind positions (max 0.0004 mm) and weights (the
  plain check's 2 "differences" are coincident source pairs with other weights; every vertex has an exact match).
  `kept_check.py` (`work/kept_check.log`): rapier, eyes and mouth, studs and laces unchanged (<= 0.0003 mm, same weights).
- `lod_check.py`: lowest point per clip at every LOD within 3 mm of the source's (LOD3 Dead -2.8 mm vs +11.4 mm in the
  source); top 1.7035 m at every LOD (source 1.7003-1.706); one LOD3 face stretches over 20x in Dead/Death/Fidget, as
  in the source's LOD3.
- Close-ups straight from the GLBs, source vs pick, textured and clay (`glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_h86_a.png` (head front/three-quarter/side/back, torso, back, shoulder roll),
  `sheet_h86_b.png` (shoulder back, arm, rapier, boots, walk, hit, death). No visible change; a slightly darker crease at
  the right boot cuff in clay only.
- Viewer (`viewer_variants.py`, `viewer_manifest.py`): `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_m362_reduce_claude check`: 108 switches (9 looks x source/reduced x 6 clips), no
  console errors; shots of looks AA, BC, CC standing and walking (`review/shots_tiers.png`).

## Open points for review

- The cut is modest (-13 %): 51 % of the mesh is kept exactly (hands 2,188, rapier 500, eyes/mouth 497, face front 836).
  The source was already reduced once in its build; deeper steps failed the error gate in the hair, sleeves and
  shoulder rolls (config f/g).
- A slightly darker crease at the right boot cuff in the clay close-up (not visible textured).

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m362_reduce_claude/export/mm7_m362.glb --world mm7
```

then the binding from `../mm7_m362_claude/integration/actors.yml` (unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m362_source_pre_reduce.glb` the same way.

## Reproduce

`REA_GLB=<abs path of work/mm7_m362_source_pre_reduce.glb> REA_NODE=M362 import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m362_source_pre_reduce.glb` -> `dump_master_pieces.py` ->
`m362_pieces.py` -> `visibility.py -0.01 1.71` (copy to `work/visible_all.npy`) and `REA_MIN_PIX=6 visibility.py 1.40
1.71` (`work/visible_head.npy`) -> `m362_sets.py a` -> `REA_PATCH_R=0.03 patch_keep.py work/keep_a.npy work/keep_d.npy
-0.242,-0.016,1.086 -0.217,0.003,1.138 -0.164,0.016,1.118` (groups_d = groups_a with the kept faces at 0; keep_h /
groups_h copies) -> `TOKEN=<lease> run_ladder.sh h h "1:0.5,2:0.7,3:0.8,4:0.7,5:0.75,6:0.6,7:0.8,8:0.85,9:0.72,10:0.75"
0.8` -> build as above. Blender scripts run through `scripts/bl.sh` (lease wrapper, `TOKEN`); `decimate_tex.py` uses the
batch's MeshLab venv (path in `run_ladder.sh`).

## Installed 2026-10-20

`tools/install_model.py export/mm7_m362.glb --world mm7` (winding check 0 inverted closed parts first); the
nine bindings from `../mm7_m362_claude/integration/actors.yml` appended to `assets_dev/worlds/mm7/models/actors.yml`
(explicit scale, no `scale_reference`); ledger row in `../REDUCTION_LEDGER.md`. Boot check on Harmondale with two looks
spawned: no load errors, no missing models (`output/batchK_boot/`). Rollback: reinstall
`work/mm7_m362_source_pre_reduce.glb` (the batch export) the same way.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -2.5.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m362.glb export/mm7_m362.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m362.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31, package h14)

The installed source (`assets_source/worlds/mm7/models/mm7_m362.glb`) gained new in-place locomotion clips appended by
[`../gait_rollout_20261031/h14/`](../gait_rollout_20261031/h14/README.md): Jog (Mixamo Running (5), 0.72 s, stride 2.0639; arms from Walking with a forward elbow). Existing clips, meshes, skins and
materials are byte-identical (prefix check). Bindings for all nine descriptors (for the coordinator,
`h14/bindings.yml`): run: Jog, run_stride_length 2.0639. Rollback: reinstall `../gait_rollout_20261031/h14/work/mm7_m362_pre_gait.glb`.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h14/scripts/rebuild.sh m362`, then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h14/export/mm7_m362.glb --world mm7
--name mm7_m362.glb`. A far-LOD repair rerun, a head-bob fix or any re-export of this model must re-graft these clips
(copy the new source over the pre-gait copy and rerun the rebuild).
