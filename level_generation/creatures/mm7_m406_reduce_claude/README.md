# MM7 Swordsman (`m406`, Swordsman / Guard / Adventurer) reduction (2026-10-20)

User: "reduce tris on all 5" (the five MM7 batch-A humanoids; this project is m406 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the three tier variants (`KHR_materials_variants`) and the region ramps stay valid. No Meshy
credits. **Installed 2026-10-20** (batch A stage).

[Review viewer](review/viewer/index.html) (source vs reduced, tiers A/B/C, all eight clips, longsword in its socket)

## Source

`../mm7_m406_claude/export/mm7_m406.glb` and `mm7_m406_sword.glb` (rebuilt and accepted 2026-10-20), copied to
`work/mm7_m406_source_pre_reduce.glb` and `work/mm7_m406_sword_source_pre_reduce.glb` (rollback sources). One
merged body + head atlas material per tier (`M406_A/B/C`, 2080x1024, head half u > 0.51), node `M406`, 57 joints, 4
influences at LOD0 (8 slots at LOD1-3), shadow LODs, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget.
Bind height 1.711 m. Weld: 5,588 -> 484 open edges, no coincident vertices with other weights, 10,294 triangles in
and out (no two-sided sheets). Scripts start from `../mm8_m432_reduce_claude/scripts/` (parent-before-transform fix,
per-region groups, `grip_check.py`, `glb_close.py`) plus `region_error.py`, `patch_keep.py`, `floor_points.py` from
`../mm8_m632_reduce_claude/` and `kept_normals.py` from `../mm8_m656_reduce_claude/`.

## Where the triangles are (`scripts/m406_pieces.py`)

| piece | faces | |
|---|---:|---|
| gauntlets (hands, fingers; the sword grip is fitted) | 2,505 | kept exactly |
| head piece (face, ears, scalp, neck; beard painted) | 2,314 | 1,333 visible, 981 never visible |
| legs and boots (incl. gold knee cops) | 1,317 | 225 sole faces |
| torso with the tabard | 1,145 | |
| arms (bare upper arms, vambraces) | 1,119 | |
| helmet (closed shell, rim, spike) | 728 | |
| knee side discs (4 pieces) | 456 | |
| mail coif (hugs cheeks, back of the head) | 326 | |
| belt buckle | 212 | |
| eyes (2 pieces) | 172 | kept exactly |

The head set is over a third of the mesh, so only the face is protected: `scripts/visibility.py` (face-id
z-buffers from the 26 of 42 sphere directions at most 15 degrees below the horizon) splits the head piece into the visible face
front, the visible sides (ears, jaw, under the chin) and the hidden skin under the helmet, coif and collar
(`review/labels/head_visibility_only.png`).

## Keep set and groups (`scripts/m406_sets.py`, pick = set `h`, `review/labels/sets_d_head.png`)

Kept exactly (`work/keep_h.npy`, 4,747 faces): both gauntlets; every face touching a vertex with hand + finger
weight > 0.3 (vambrace ends); the eyes; the boot soles (faces below 6 cm); the helmet spike (faces above 1.585 m) and
the helmet rim (faces within 2.5 cm of the helmet's lowest point per 15-degree sector; a 60 % cut made the rolled rim
wavy and lifted it off the coif at the back, `review/glbclose/sheet_c_head.png`); the whole visible face front
(eyes, nose, mouth, beard front, cheeks; at 70 % it creased the cheeks in clay, geometry not normals); 4 cm patches at
the back of both elbows, the upper back and the back of the collar (the max error spots of the first ladders,
`probe_max.py`).

| group | faces | ratio |
|---|---:|---|
| 2 visible head sides (ears, jaw, under the chin) | 332 | 65 % |
| 3 hidden head skin (scalp, neck) | 759 | 50 % (35 % flattened the hidden scalp 18 mm inward and dominated p99) |
| 4 helmet dome | 403 | 80 % (50-60 % softened the raised ribs and streaked rivets) |
| 5 mail coif | 326 | 75 % (60 % faceted the cheeks in clay) |
| 6 knee side discs | 456 | 35 % |
| 7 belt buckle | 212 | 40 % |
| 0 torso, arms, legs | 3,056 | free, takes the ladder budget (63 % at the pick) |

`region_error.py` (d79): torso, arms and legs at 65 % already reach p95 4.5-5.1 mm (limit p99 5.13 mm): the body was
reduced once in the source build (16k Smart Topology -> 10.3k with head and hands protected), so the cut sits in the
small regions and the hidden skin.

## Ladder (limits for the 1.711 m height: p99 5.13 mm, max 25.67 mm; IoU >= 0.98, SSIM >= 0.93)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 10,294 | | | | |
| a: features r 2.2 cm, face front 75 %, hidden 35 %, helmet 65 % | r82 | 8,498 | 4.58 / 23.89 | 0.9956 | 0.9950 | pass; r79 fails max (elbows) |
| b: features r 1.8 cm, hidden 50 %, small regions 50-60 % | r81 | 8,348 | 3.73 / 23.89 | 0.9955 | 0.9948 | pass |
| b2: body 65-60 % | r79 / r76 | 8,194 / 7,882 | 4.02 / 29.47, 4.75 / 33.16 | 0.993 / 0.988 | | fail (max: elbow backs, upper back) |
| c: + elbow/back patches | r76 | 7,900 | 4.85 / 19.79 | 0.9927 | 0.9901 | pass; cheeks creased, helmet rim wavy |
| d: + face front and helmet rim kept | r79 | 8,166 | 4.78 / 19.79 | 0.9928 | 0.9901 | pass; coif faceted |
| e: coif 75 %, helmet 50 %, discs 35 %, buckle 40 % | r77 | 8,014 | 5.08 / 19.79 | 0.9923 | 0.9899 | pass; helmet ribs softened |
| g: e + 1.2 cm drift lock, hidden 45 %, helmet 60 % | r79 | 8,164 | 5.04 / 18.87 | 0.9926 | 0.9919 | pass, no gain |
| **h: e with the helmet dome at 80 %** | **r78** | **8,072** | **5.07 / 19.79** | **0.9924** | **0.9896** | **pick** |
| h | r77 | 7,982 | 5.22 / 19.79 | 0.9920 | 0.9889 | fail (p99) |

The pick is the lowest passing step of the config that also looks right in the close-ups: e77 (8,014) passed too but
softened the helmet's raised ribs. The 19.8 mm maximum is in Death frame 24, the same at every step. Texture drift
(`texture_drift.py` + `drift_visible.py h78`, visible faces only): 25 faces over 40 (111 cm2), all on large torso,
collar and shin faces with colour differences 34-53; none shows in the close-ups, so no lock round (a 3 cm lock added
339 kept faces and pushed the free cut over the limit).

## Build

`cand_glb.sh h Cand_78` with `REA_KEPT_NORMALS=1` (`kept_normals.py`: source GLB normals on the 17,370 corners of
unchanged source faces and on 2,817 kept smooth vertices, computed smooth normals elsewhere) -> `export_cand.py` ->
`swap_lod0.py` (`work/h78_lod0.glb`) -> `spike_points.py` (tip + 4 x 4 spike points) and `floor_points.py` (24 Dead /
Death floor contacts) -> `build_lods.py` (`tools/build_actor_lods.py`, 8 influence slots as the source, ratios
0.5 / 0.21 / 0.075, 38 protected points) -> `shrink_shadow_lods.py` (the source project's script, copied: shadow LODs
inset as in the source export) -> `carry_variants.py` -> `check_winding.py` (0 inverted closed parts):
`export/mm7_m406.glb`, 7.96 MB (source 8.20 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 10,294 | 5,146 | 1,852 | 614 |
| reduced body | 8,072 | 4,036 | 1,694 | 603 |
| longsword (`export/mm7_m406_sword.glb`, byte-identical copy) | 454 | 226 | 80 | 25 |

LOD ratios: the source's 0.5 / 0.18 / 0.06 gave LOD3 481 triangles, which pushed the helmet brim into the face
(worse than the source LOD3); 0.21 / 0.075 keeps LOD2/LOD3 just below the source's counts (`review/lods/sheet.png`).
A strict 50 % per level (0.25 / 0.125) would have raised LOD2/LOD3 above the source (2,018 / 1,009).

Checks:
- `scripts/compare_glb.py`: node names and transforms, skin and inverse binds, materials and extras, images, textures,
  samplers, all eight clips (sampler data), mesh names/extras and the variants extension are identical to the source;
  `KHR_materials_variants` (m406_a/b/c) on all 8 colour/shadow primitives.
- `scripts/grip_check.py` (`work/grip_check.log`): all 2,025 LOD0 vertices with hand + finger weight > 0.5 keep their
  bind positions (max 0.0005 mm) and weights exactly, so the fitted sword grip (and the source's 5.69x right-fist web
  edge, unchanged) is the same.
- `work/lod_check_{src,h78}.json`: every LOD keeps the 1.700 m top (spike; source LOD3 overshot to 1.704 m) and the
  source's bounds; lowest point per clip equals the source's LOD0 in every clip at LOD0/1 (Dead 1.6 mm vs 0.2 mm) and
  is within 0.5-4 mm at LOD2/3; no face stretches over 20x in any frame of any clip at any LOD.
- Close-ups straight from the GLBs, source vs pick, textured and clay (`scripts/glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_h78_head.png` (face, helmet, coif, back of the head), `sheet_h78_body.png` (tabard front,
  back and side, shoulder, arm, elbow), `sheet_h78_legs.png` (both hands, knees, boots, Attack, Death),
  `helmet_src_e77_h78.png` (helmet dome at 50 % vs 80 %).
- Viewer: `review/viewer/` (source vs 78 % pick, tiers A/B/C, longsword added under the `Sword` joint for review only
  by `viewer_sword.py`); `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_m406_reduce_claude --token <lease> check`: 48 switches, no console errors.
  `review/shots/sheet_sword.png` (tier A standing and Attack 0.9 s, grip unchanged), `sheet_tiers_bc.png`.

## Open points for review

- Clay renders show a faint line on the coif beside the ears (coif at 75 %); textured, the mail hides it.
- Knee cops and calves are slightly more faceted in clay; textured they read unchanged.
- LOD3 (603) is as crude as the source LOD3 (614): face under the brim, a red streak on the tabard front.
- The longsword was left byte-identical (454 triangles; a clean procedural mesh whose grip must stay exact).

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m406_reduce_claude/export/mm7_m406.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m406_reduce_claude/export/mm7_m406_sword.glb --world mm7
```

then the binding from `../mm7_m406_claude/integration/actors.yml` (unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m406_source_pre_reduce.glb` (+
`work/mm7_m406_sword_source_pre_reduce.glb`) the same way.

## Reproduce

`REA_GLB=<abs path of work/mm7_m406_source_pre_reduce.glb> REA_NODE=M406 import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m406_source_pre_reduce.glb` -> `m406_pieces.py` ->
`REA_MIN_PIX=6 visibility.py 1.25 1.75` (copy to `work/visible_head.npy`) and `visibility.py -0.01 1.75`
(`work/visible_all.npy`) -> `patch_keep.py - work/patch_c.npy -0.300,0.074,1.030 0.007,0.171,1.190 0.038,0.148,1.303`
-> `M406_FEATURE_R=0.018 M406_KEEP_FACE=1 M406_EXTRA_KEEP=work/patch_c.npy m406_sets.py h` ->
`TOKEN=<lease> run_ladder.sh h h "2:0.65,3:0.5,4:0.8,5:0.75,6:0.35,7:0.4" 0.66,0.63,0.6` -> `texture_drift.py`,
`drift_visible.py`, `region_error.py`, `probe_max.py` -> `REA_KEPT_NORMALS=1 cand_glb.sh h Cand_78 kn` (copy
`work/glb_h_78kn.glb` to `work/h78_lod0.glb`) -> `spike_points.py`, `REA_NODE=M406 floor_points.py` -> build as above
-> `compare_glb.py`, `grip_check.py`, `lod_check.py` (REA_NODE=M406), `lod_views.py`, `glb_close.py`,
`viewer_variants.py`, `viewer_sword.py`, `viewer_manifest.py "MM7 Swordsman" r78 10294 8072`. Blender scripts run
through `scripts/bl.sh` (lease wrapper, `TOKEN`).

## Clips updated (2026-10-20)

The source project's walk/run ankle twitch was fixed after this reduction (`../mm7_m406_claude/scripts/foot_level.py`). `scripts/transplant_clips.py` copied the re-exported clips into `export/mm7_m406.glb` and every `review/viewer/*.glb` (geometry, LODs, materials and variants unchanged), and `work/mm7_m406_source_pre_reduce.glb` is now that re-export. After any later re-export of the source, run `python3 scripts/transplant_clips.py ../mm7_m406_claude/export/mm7_m406.glb export/mm7_m406.glb export/mm7_m406.glb`.
The walk bob fix (`walk_bob.py`, same day) was carried over the same way.

**Accepted 2026-10-20**; installed 2026-10-20 from `../mm7_batches/BATCH_A_stage/` (listed in REDUCTION_LEDGER.md).
So was the Hit/Death foot-roll fix (flatness-weighted, smoothed roll; same day); the stage was rebuilt.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -2.9.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m406.glb export/mm7_m406.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m406.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/h07`](../gait_rollout_20261031/h07/README.md) appended Jog (humanoid set Unarmed-Run-Forward, 0.74 s) and Sprint (Unarmed-Sprint, 0.60 s); Walking unchanged to the installed
`assets_source/worlds/mm7/models/mm7_m406.glb` and installed it (existing clips, meshes, skins and materials
byte-identical). The sword arm is lifted (eased, up to 25 deg) in the half of the run loop where the right knee comes
through, so the blade clears the thigh. Bindings for the coordinator (`h07/bindings.yml`): run: Jog, run_stride_length 2.9094, sprint: Sprint, sprint_stride_length 4.0482. `Running` is kept in
the GLB but no longer bound for locomotion. Rebuild: `level_generation/creatures/gait_rollout_20261031/h07/scripts/rebuild.sh m406`
(from `h07/work/mm7_m406_pre_gait.glb`, the rollback source). A far-LOD repair rerun, a floor fix or any re-export of this
model must re-graft these clips: copy the new source over `h07/work/mm7_m406_pre_gait.glb` and rerun the rebuild, then
install with `tools/install_model.py`.
