# MM7 Peasant Goblin Male (`7m452`, descriptors 439-447) reduction (2026-10-20)

User: "OK reduce tris count now" (the five MM7 batch-J peasants; this project is 7m452 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the nine palette looks (`KHR_materials_variants`) and the three region ramps stay valid. No
Meshy credits. **Not installed** (batch J: the user installs later).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_7m452_reduce_claude/review/viewer/) (source vs
reduced, all nine looks, six clips, billhook added under the `Sword` joint for review)

## Source

`../mm7_7m452_claude/export/mm7_7m452.glb` and `mm7_7m452_billhook.glb` (after the 2026-10-20 walk/ankle fix), copied
byte for byte to `work/mm7_7m452_source_pre_reduce.glb` and `work/mm7_7m452_billhook_source_pre_reduce.glb`
(rollback sources). One merged body + head atlas material per look (`Goblin_A1`…`Goblin_C3`, 2080x1024, region mask R
tunic / G trousers / B hair), node `Goblin`, 57 joints (incl. `Sword`), shadow LODs, clips Standing, Walking, Hit,
Death, Dead, Fidget. Bind height 1.800 m (ladder limits p99 5.4 mm, max 27 mm). Weld (identical weights only):
6,069 -> 401 open edges, no coincident vertices with other weights, 11,791 triangles in and out. Scripts start from
`../mm7_m410_reduce_claude/scripts/` (paths, node `Goblin`); piece labels come straight from the production master's
`piece` attribute (`master_pieces.py`, `g452_pieces.py`: nearest rest vertex, max distance 0.0015 mm).

## Where the triangles are (`scripts/g452_pieces.py`)

| piece | faces | |
|---|---:|---|
| head (face, ears, scalp, topknot) | 3,012 | 856 visible face front, 1,003 visible sides/back, 320 hidden, 833 crown and topknot |
| torso + bare arms | 2,400 | tunic top 523 (region mask R), fleece armhole trim 706, arms/neck/shoulders 1,171 |
| hands | 2,200 | the billhook grip is solved per finger: kept exactly |
| tunic skirt with the belt | 800 | belt band 198 |
| trousers | 799 | |
| boots | 1,000 | 279 sole faces |
| bracers | 600 | kept exactly |
| buckle | 350 | dense |
| eyes, mouth, neck bead | 424, 108, 98 | kept exactly |

The production build had already thinned the torso, trousers, skirt, boots and bracers (16.1k -> 11.8k with head and
hands protected), so most of the cut sits in the head (outside the face), the dense buckle and the bare arms.

## Keep set and groups (`scripts/g452_sets.py`, pick = set `g`)

Kept exactly (`work/keep_g.npy`, 4,787 faces): both hands (every face touching a vertex with hand + finger weight > 0.3),
both bracers, eyes, mouth, neck bead, the boot soles (faces below 6 cm), the visible face front (head faces seen in
some view, in front of y = -0.03 and below the topknot), the belt band (top 4.5 cm of the skirt piece) and 3 cm
patches at the back's max-error spots (`patch_keep.py`: lower back both sides, upper back; their source vertices carry
clavicle weights).

| group | faces | ratio |
|---|---:|---|
| 1 visible head sides and back (ears, temples, nape) | 1,003 | 55 % |
| 2 hidden head skin | 320 | 65 % (45 % gave p95 11 mm, invisible but dominating the error) |
| 3 crown and topknot | 833 | 50 % |
| 4 buckle | 350 | 30 % |
| 5 trousers | 799 | 60 % |
| 6 tunic skirt below the belt | 602 | 80 % (60 % smeared the printed pattern into a streak at the side slit) |
| 7 boots | 721 | 60 % |
| 8 tunic top (region mask R) | 523 | 80 % (the printed pattern drifted into skin-coloured flecks under the free cut) |
| 9 fleece armhole trim | 706 | 85 % (in the free cut the rolled rim flattened) |
| 0 bare arms, neck and shoulders | 1,147 | free, 50 % at the pick |

## Ladder (limits for 1.80 m: p99 5.4 mm, max 27 mm; IoU >= 0.98, SSIM >= 0.93)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 11,791 | | | | |
| a: torso free 80-60 % | r82-r78 | 9,751-9,269 | 3.30-4.16 / 20.1-24.0 | 0.996-0.995 | 0.997-0.994 | pass |
| b: harder groups, free 60-40 % | r75 / r73 | 8,903 / 8,663 | 4.58 / 23.97, 5.12 / 31.28 | | | pass / fail (max, lower back) |
| c: + back patches | r73 | 8,677 | 5.18 / 21.51 | 0.993 | 0.992 | pass, at the limit |
| d: hidden head 65 %, crown 50 % | r72 | 8,523 | 4.96 / 24.55 | 0.992 | 0.991 | pass; tunic flecks (19 visible drifted faces) |
| e: d + 3 cm drift lock | r74 | 8,813 | 5.00 / 21.51 | 0.992 | 0.991 | pass; the flecks moved to other spots |
| f: tunic and skirt own groups at 80 % | r73 | 8,705 | 5.07 / 21.15 | 0.993 | 0.993 | pass; clean tunic, armhole fleece flattened |
| **g: f + fleece trim at 85 %** | **r76** | **9,045** | **4.49 / 19.85** | **0.993** | **0.994** | **pick** |
| g | r75 / r74 | 8,929 / 8,815 | 5.42 / 27.04, 10.2 / 43.9 | | | fail (bare arms below 50 %) |

The pick is the lowest configuration that passes the ladder and looks like the source in the textured and clay
close-ups: the 8.5-8.8k steps passed the gates but flecked the tunic's printed pattern or flattened the rolled fleece
rim (`review/glbclose/sheet_fleece.png`: source / f73 / g76). The 19.9 mm maximum is in Hit frame 6.
Texture drift (`texture_drift.py` + `drift_visible.py g76`, visible faces): 13 faces over 40 (45.8 cm²), the largest a
trouser face under the skirt hem (hidden by the skirt in every clip); none shows in the close-ups.
Slivers and long faces (`scripts/sliver_vis.sh g76`): source 62 slivers and 11 long faces, pick 32 and 7. New: 6
slivers (3 never visible; 3 seen from 3-12 of 26 views: right armpit, right shoulder front, back of the head, 2.5-4.5 cm
long, 3-4 mm high) and 3 long faces (two under the right armpit, one on the tunic back); none shows in the close-ups.

## Build

`cand_glb.sh g Cand_76 kn` with `REA_KEPT_NORMALS=1` (source GLB normals on the unchanged source faces and kept smooth
vertices, computed smooth normals elsewhere) -> `export_cand.py` -> `swap_lod0.py` (`work/g76_lod0.glb`) ->
`cap_points.py` (`REA_CAP_Z=1.72`: 13 topknot points) and `REA_NODE=Goblin floor_points.py` (24 Dead/Death floor
contacts) -> `build_lods.py` (`tools/build_actor_lods.py`, ratios 0.5 / 0.23 / 0.077, 37 protected points) ->
`MESH_NODE=Goblin shrink_shadow_lods.py` (the source project's script) -> `carry_variants.py` (7 primitives) ->
`check_winding.py` (0 inverted closed parts): `export/mm7_7m452.glb`, 7.20 MB (source 7.51 MB). All LOD UVs stay
inside [0, 1].

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 11,791 | 5,895 | 2,121 | 706 |
| reduced body | **9,045** | **4,521** | **2,080** | **694** |
| billhook (`export/mm7_7m452_billhook.glb`, byte-identical copy) | 854 | 426 | 152 | 50 |

LOD2/LOD3 ratios keep the counts just below the source's (`0.18 / 0.06` would give 1,628 / 543).

Checks:
- `scripts/compare_glb.py`: node names and transforms, skin and inverse binds, materials and extras, images, textures,
  samplers, all six clips (sampler data), mesh names/extras and the variants extension identical to the source;
  `KHR_materials_variants` (nine looks) on all 8 colour/shadow primitives. `DIFFERENCES none`.
- `scripts/grip_check.py` (`work/grip_check.log`): all 1,689 LOD0 vertices with hand + finger weight > 0.5 keep their
  bind positions (max 0.0003 mm) and weights exactly, so the billhook grip is unchanged.
- `work/lod_check_{src,g76}.json`: every LOD keeps the 1.800 m topknot top (source LOD2/LOD3 1.799 / 1.797) and the
  source's bounds; the lowest point per clip equals the source's at LOD0/LOD1 and is within 0-3 mm at LOD2/LOD3
  (the source's own -19.5 mm Standing / -18.2 mm Hit soles are unchanged, inherited); no face stretches over 20x in
  any frame of any clip at any LOD.
- Close-ups straight from the GLBs, source vs pick, textured and clay (`scripts/glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_g76_head.png` (face, ears, topknot, back of the head), `sheet_g76_body.png` (tunic front,
  back and side, belt and skirt, both hands), `sheet_g76_legs.png` (knees, boots, death, whole), `sheet_g76_trims.png`
  and `sheet_fleece.png` (armhole fleece), `sheet_e74_body.png` (the drift-lock flecks).
- Viewer: `review/viewer/` (source r100 vs 76 % pick, nine looks with the ramps baked by `viewer_variants.py`, the
  billhook added under `Sword` by `viewer_billhook.py`); `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_7m452_reduce_claude check`: 108 switches, no console errors; shots in
  `review/shots_sheet.png`.

## Open points for review

- The cut is -23 % (11,791 -> 9,045): hands (2,200), face front, bracers and the patterned tunic hold half the mesh.
- The boot cuffs lose a few folds in clay (boots at 60 %); textured they read the same.
- 3 small new slivers and 3 long faces at the right armpit, right shoulder and tunic back (see Ladder); not visible in
  the close-ups.
- The viewer's `head` focus is framed for the Thief and shows the topknot; use `body` or orbit.
- Inherited from the source (unchanged): soles 19.5 mm below the floor in Standing at LOD0 (`lod_check`, rest-pose
  heel), the billhook dips into the left thigh in one Death frame.

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_7m452_reduce_claude/export/mm7_7m452.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_7m452_reduce_claude/export/mm7_7m452_billhook.glb --world mm7
```

then the binding from `../mm7_7m452_claude/README.md` (unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_7m452_source_pre_reduce.glb` (+
`work/mm7_7m452_billhook_source_pre_reduce.glb`) the same way.

## Reproduce

`REA_GLB=<abs path of work/mm7_7m452_source_pre_reduce.glb> REA_NODE=Goblin import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_7m452_source_pre_reduce.glb` -> `master_pieces.py` (Blender) ->
`g452_pieces.py` (pieces, soles, hand faces, region mask) -> `REA_MIN_PIX=6 visibility.py 1.2 1.81` (copy to
`work/visible_head.npy`) -> `fleece_faces.py` (`work/fleece.npy`) -> `REA_PATCH_R=0.03 patch_keep.py - work/patch_c.npy
0.098,0.116,1.164 -0.098,0.116,1.164 -0.001,0.184,1.33` -> `G452_EXTRA_KEEP=work/patch_c.npy g452_sets.py g` ->
`TOKEN=<lease> run_ladder.sh g g "1:0.55,2:0.65,3:0.5,4:0.3,5:0.6,6:0.8,7:0.6,8:0.8,9:0.85" 0.5,0.4,0.3` ->
`texture_drift.py g76`, `drift_visible.py g76`, `sliver_vis.sh g76` -> `REA_KEPT_NORMALS=1 cand_glb.sh g Cand_76 kn`
(copy `work/glb_g_76kn.glb` to `work/g76_lod0.glb`) -> build as above -> `compare_glb.py`, `grip_check.py ... Goblin`,
`lod_check.py` (REA_NODE=Goblin), `glb_close.py`, `viewer_variants.py`, `viewer_billhook.py`,
`viewer_manifest.py "MM7 Peasant Goblin Male" r76 11791 9045`. Blender scripts run through `scripts/bl.sh` (lease
wrapper, `TOKEN`).

## Installed (2026-10-20)

User: "OK accept all, to assets_source, assets_dev". `check_winding.py` 0 inverted closed parts; installed with
`tools/install_model.py ... --world mm7` (sources in `assets_source/worlds/mm7/models/` equal the exports; cooked
runtime copies in `assets_dev/worlds/mm7/models/`). Nine `actors.yml` bindings added to
`assets_dev/worlds/mm7/models/actors.yml` from the production README's template (descriptor -> palette -> skin from
`../mm7_7m452/variants.json` and the ramps file); every skin, clip, look node and attachment checked against both GLBs.
Boot check: `7out02.odm` (Harmondale) with spawned peasants of all five batch J models, 185 outdoor actors textured,
no missing models and no errors in the log (`output/batchJ_boot/`). Ledger row added to `../REDUCTION_LEDGER.md`.

## Clip update (2026-10-20, reinstalled)

The production project fixed the Standing floor (−1.9 cm → 0) and replaced the death (the billhook went through the left
thigh) after this reduction. The reduced mesh is unchanged: `scripts/transplant_clips.py` copies the new production
export's clips into the reduced GLB (same nodes, skin and inverse binds checked; old animation data dropped, buffer
repacked). `compare_glb.py` against the new production export: `DIFFERENCES none` (triangle counts aside);
`lod_check.py`: every LOD's Standing lowest point −0.15 cm, no stretched faces in any clip. Viewer rebuilt (108
switches, no console errors), `check_winding.py` 0, reinstalled with `tools/install_model.py --world mm7`
(the billhook is unchanged). Boot check `output/batchJ_goblinfix/`: no errors, the death plays in game.
Previous reduced export: `work/mm7_7m452_reduced_prefix_clips.glb`.

## Gait rollout (2026-10-31)

The installed `mm7_7m452.glb` carries a new `Jog` (Mixamo Running (5), 0.72 s, stride 1.7791) appended by
[gait rollout package h15](../gait_rollout_20261031/h15/README.md) for the peasants' flight (2.6 u/s; Walking played
x1.55); binding `run: Jog`, `run_stride_length: 1.7791` on all nine descriptors. Rebuild:
`gait_rollout_20261031/h15/scripts/rebuild.sh mm7_7m452`. A far-LOD repair rerun or any re-export here must re-graft
that clip (copy the new source over `h15/work/mm7_7m452_pre_gait.glb` and rebuild).
