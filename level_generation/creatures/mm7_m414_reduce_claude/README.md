# MM7 Titan (`m414`, Titan / Storm Titan / Blood Titan) reduction (2026-10-20)

User: "do the tris reduction playbook on these 5" (the five MM7 batch-C humanoids; this project is m414 only). Default
route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that
keeps the UVs, so the textures, the three tier variants (`KHR_materials_variants`) and the region ramps stay valid. No
Meshy credits. **Not installed** (batch C: the user installs later).

[Review viewer](review/viewer/index.html) (source vs reduced, tiers A/B/C, all eight clips, short sword in its socket)

## Source

`../mm7_m414_claude/export/mm7_m414.glb` (sha256 `2273cb17...481e`) and `mm7_m414_sword.glb` (accepted 2026-10-20),
copied to `work/mm7_m414_source_pre_reduce.glb` and `work/mm7_m414_sword_source_pre_reduce.glb` (rollback sources).
One merged body + head atlas material per tier (`Titan_A/B/C`, 2080x1024, head half u > 0.51), node `Titan`, 57
joints, 4 influences at LOD0 (8 slots at LOD1-3), shadow LODs, clips Standing, Walking, Running, Attack, Hit, Death,
Dead, Fidget. Rest height 1.908 m (crest top 1.900 m = 711 units at the binding scale 374.06, helmet top 1.7506 m =
655 units); ladder limits use the idle's 1.93 m. Weld: 5,844 -> 540 open edges, no coincident vertices with other
weights, 10,320 triangles in and out (no two-sided sheets). Scripts copied from `../mm7_m406_reduce_claude/scripts/`
(which keep `piece_weights` on by default in `reduce_ladder.py`: every candidate piece takes its weights from its own
source piece, the per-part weights of the MM6 Titan lesson, so skirt tiers and belt do not take the body's weights).

## Where the triangles are (`scripts/m414_pieces.py`)

| piece | faces | |
|---|---:|---|
| face + neck skin (head texture set of the main shell) | 2,382 | 1,198 visible, 1,184 never visible (under helmet and guards) |
| arms (stone skin, vambraces with gold bolts, hands; the right fist holds the sword) | 2,935 | 2,179 hand faces kept exactly |
| legs (greaves with gold bolts, sandals) | 1,225 | 284 sole faces |
| three skirt tiers | 1,200 | 592 / 319 / 289 |
| torso (sleeveless scale tunic, gold-edged shoulders and collar) | 858 | |
| helmet dome (gold trim, brim) | 436 | |
| belt (gold, lion buckle) | 421 | kept exactly |
| crest (thin fan, the model's top) | 387 | |
| cheek and neck guards | 367 | |
| eyes (2 pieces) | 109 | kept exactly |

Gold paint per face (`work/gold.npy`: 7 base-colour samples, hue 25-60 degrees, saturation > 0.35) touches 2,193
faces (21 %, `review/labels/gold.png`). The body was already reduced once in the source build (15.4k Smart Topology ->
10.3k), so it is lean: the torso and arms at 60 % already reach 9.5 mm p95 in the rest pose (`scripts/rest_error.py`,
ladder a), and the cut can only come from the hidden head skin and gentle per-region ratios.

## Keep set and groups (`scripts/m414_sets.py`, pick = set `k`, `review/labels/keep_c_head.png`)

Kept exactly (`work/keep_k.npy`, 5,487 faces): both hands (every face touching a vertex with hand + finger weight >
0.3); the eyes; the sandal soles (faces below 6 cm); every visible head-set face (face, the neck between the guards;
`scripts/visibility.py`, 6 px from the 26 of 42 sphere directions at most 15 degrees below the horizon); the painted
gold lines (faces with >= 2/7 gold samples) on helmet, guards, torso (shoulder and collar edges), vambraces and greaves
(lightning bolts), except fully gold faces inside broad gold areas (`work/gold_inner.npy`), which go into their
region's cut; the whole belt (lion; at 70-85 % it reached 6.4-7 mm p95); the helmet brim (faces within 2.5 cm of the
helmet's lowest point per 15-degree sector, the m406 rule: the gold test alone kept a zigzag of the band); the crest's
top band (within 2 cm of its outline per 10-degree sector of the fan: the model's top); 3 cm patches (with X mirrors)
at the max-error spots of the first ladders (`probe_max.py`): lower and upper back, chest, upper back centre, right
elbow and left armpit (`work/patch_e.npy`).

| group | faces | ratio |
|---|---:|---|
| 1 head skin within one vertex ring of a visible face (neck under the jaw beside the guards) | 358 | 70 % |
| 2 hidden head skin (scalp under the helmet, neck under the guards) | 776 | 40 % (30 % flattened the scalp 12-15 mm inward, p99 fail) |
| 3 helmet dome | 251 | 80 % |
| 4 cheek and neck guards (non-gold) | 198 | 85 % (75 %: p99 7.2 mm) |
| 5 crest (below the top band) | 230 | 70 % |
| 6 skirt tiers | 1,200 | 75 % (70 %: p99 7.8 mm in the rest pose) |
| 7 legs (greaves, non-gold) | 719 | 75 % |
| 0 torso and arms (free) | 1,101 | takes the ladder budget (75 % at the pick) |

## Ladder (limits for 1.93 m: p99 5.79 mm, max 28.95 mm; IoU >= 0.98, SSIM >= 0.93)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 10,320 | | | | |
| a: gold, face front, crest top, belt kept; free 60-30 % | r81 | 8,432 | 7.88 / 34.34 | 0.9899 | 0.9897 | fail (torso fans, `review/labels/cand_a78.png`) |
| b: free 90-85 %, skirt/legs 80-85 % | r87 | 9,020 | 3.70 / 18.97 | 0.9973 | 0.9942 | pass |
| c: face features only, broad gold and belt cut, brim kept | r84 | 8,756 | 4.37 / 21.84 | 0.9961 | 0.9936 | pass; r83 fails max (back, Death) |
| d/e: + back, chest, elbow, armpit patches | e82 | 8,564 | 5.03 / 23.13 | 0.9959 | 0.9933 | pass; belt 6.4 mm p95 |
| f: e with the belt kept, face rest 50 % | r82 | 8,560 | 4.98 / 23.13 | 0.9960 | 0.9933 | pass; **cheek crease** at the feature-patch border (`review/glbclose/face_src_f82_l85.png`) |
| g: f with the whole visible face front kept | r85 | 8,794 | 4.79 / 23.13 | 0.9960 | 0.9934 | pass; neck crease under the jaw (labelled hidden) |
| k: g with every visible head face kept + one-ring group | r86 | 9,042 | 4.66 / 23.13 | 0.9960 | 0.9934 | pass, clean neck |
| **l: k with skirt and legs at 75 %** | **r85** | **8,946** | **5.26 / 23.13** | **0.9951** | **0.9930** | **pick** |
| h: g with hidden skin at 30 % | r84 | 8,690 | 6.82 / 19.31 | 0.9957 | 0.9936 | fail (p99: hidden scalp) |

Lower free ratios fail on the max (26.9-33.5 mm in Attack/Death at the elbows and back). The pick is the lowest
passing step that also looks right in close-ups: f82 and g85 were lower but creased the cheek and the neck. The
23.1 mm maximum is Running frame 3 and the same at every step from e on. Texture drift (`texture_drift.py` +
`drift_visible.py l_r85`): 3 visible faces over 40 (3.9 cm2, none over 3 cm2), so no lock round.

## Build

`cand_glb.sh l Cand_85 kn` with `REA_KEPT_NORMALS=1` (source GLB normals on the 22,260 corners of unchanged source
faces and 2,152 kept smooth vertices) -> `export_cand.py` -> `swap_lod0.py` (`work/l85_lod0.glb`) -> `spike_points.py`
(52 points: the crest outline per 10-degree sector on both faces of the fan, every crest vertex above 1.85 m, the
helmet's top and its top on each side of the crest; with the sector points alone LOD1-3 rose 0.8 mm above the crest
top) and `floor_points.py` (24 Dead / Death floor contacts) -> `build_lods.py` (`tools/build_actor_lods.py`, 8
influence slots as the source, ratios 0.5 / 0.2 / 0.075, 76 protected points) -> `shrink_shadow_lods.py` (the source
project's script: shadow LODs inset) -> `carry_variants.py` -> `check_winding.py` (0 inverted closed parts):
`export/mm7_m414.glb`, 7.61 MB (source 7.74 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 10,320 | 5,159 | 1,857 | 617 |
| reduced body | 8,946 | 4,473 | 1,788 | 669 |
| short sword (`export/mm7_m414_sword.glb`, byte-identical copy) | 290 | 144 | 52 | 22 |

LOD ratios: 0.068 gave LOD3 607 triangles, which collapsed the helmet dome and pushed the brim over the eyes
(`review/lods/l85_3_head.png`); 0.075 (669, 52 above the source) keeps the dome and brim (`review/lods/sheet.png`,
`l85b_*`). Shadow LODs match the colour LOD counts.

Checks:
- `scripts/compare_glb.py` (`work/compare_glb.log`): node names and transforms, skin and inverse binds, materials and
  extras, images, textures, samplers, all eight clips (sampler data), mesh names/extras and the variants extension
  identical to the source ("DIFFERENCES none"); `KHR_materials_variants` (m414_a/b/c) on all 8 colour/shadow
  primitives; UVs within [0, 1] at every LOD.
- `scripts/grip_check.py` (`work/grip_check.log`): all 1,542 LOD0 vertices with hand + finger weight > 0.5 keep their
  bind positions (max 0.0005 mm) and weights exactly, so the solved sword grip and the re-authored walk carry are
  unchanged (`review/shots/sheet_sword.png`: Standing, Attack 0.75 s, Walking 0.25 s, source vs pick).
- Heights (`scripts/height_check.py`, `work/height_check.log`): every LOD keeps the crest top 1.9000 m (710.7 units)
  and the helmet top 1.7506 m (654.8 units) exactly; the source LODs did not (LOD2 crest 705.9 / helmet 651.0, LOD3
  706.8 / 638.1 units). `work/lod_check_{src,l85b}.json`: rest bounds equal the source's LOD0 at every LOD (source LOD2
  overshot to 1.9012 m and LOD3 dropped to 1.8948 m); lowest point per clip equals the source LOD0 in every clip at
  LOD0 except Death (-18.6 mm vs -23.0 mm: less below the floor), LOD1 is within 0.7 mm of LOD0, LOD2/3 within
  2.5 mm (Dead 1.2 mm above the floor vs 0.4 mm); no face stretches over 20x in any frame of any clip at any LOD.
- Close-ups straight from the GLBs, source vs pick, textured and clay (`scripts/glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_l85_head.png` (face, three-quarter, side, back of the head, helmet, crest),
  `sheet_l85_body.png` (tunic front/back, shoulder edge, belt lion, vambrace bolts, arm, elbow, greave, calves),
  `sheet_l85_legs.png` (both hands, greaves, sandals, knees, skirt side and back), `sheet_l85_poses.png` (Attack,
  Death, Death and Dead from below, skirt in Attack: no plate tears), `sheet_kl_skirt.png` (skirt at 80 % vs 75 %),
  `face_src_f82_l85.png` (the rejected cheek crease).
- Viewer: `review/viewer/` (source vs 85 % pick, tiers A/B/C baked, short sword added under the `Sword` joint for
  review only by `viewer_sword.py`); `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_m414_reduce_claude --token <lease> check`: 48 switches, no console errors.
  `review/shots/sheet_tiers_bc.png` (tiers B and C).

## Open points for review

- The reduction is modest (-13.3 %): over half of LOD0 is kept exactly (hands 2,179, visible head 1,198, gold lines,
  belt), and the lean source body fails the max error below 75 %.
- Skirt tiers at 75 % have slightly simpler hem strips in clay (`sheet_kl_skirt.png`); 80 % (`k86`, 9,042) is the
  fallback (`work/glb_k_86kn.glb` is its LOD0).
- LOD3 (669) keeps 52 more triangles than the source LOD3 for the helmet; its helmet is still crude at close range.
- The short sword was left byte-identical (290 triangles, a clean procedural mesh whose grip must stay exact).

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m414_reduce_claude/export/mm7_m414.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m414_reduce_claude/export/mm7_m414_sword.glb --world mm7
```

then the binding from `../mm7_m414_claude/README.md` (unchanged by this reduction: scale 374.06, clips, sword on node
`Sword`) and a [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install
`work/mm7_m414_source_pre_reduce.glb` (+ `work/mm7_m414_sword_source_pre_reduce.glb`) the same way. If the source
project re-exports its clips later, carry them over with `scripts/transplant_clips.py` as in the m406 reduction.

## Reproduce

`REA_GLB=<abs path of work/mm7_m414_source_pre_reduce.glb> REA_NODE=Titan import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m414_source_pre_reduce.glb` -> `m414_pieces.py`, `gold_inner.py` -> `REA_MIN_PIX=6
visibility.py 1.25 1.95` (copy to `work/visible_head.npy`) and `visibility.py -0.01 1.95` (`work/visible_all.npy`)
-> `REA_PATCH_R=0.03 patch_keep.py - work/patch_d.npy 0.121,0.069,1.154 0.064,0.136,1.276 0.153,-0.080,1.270
0.021,0.135,1.356` and `patch_keep.py work/patch_d.npy work/patch_e.npy -0.378,-0.025,1.185 0.190,0.084,1.242` ->
`M414_FRONT_Y=1 M414_VIS_RINGS=1 M414_EXTRA_KEEP=work/patch_e.npy M414_GOLD_INNER=1 M414_BELT=1 m414_sets.py k` ->
`TOKEN=<lease> run_ladder.sh l k "1:0.7,2:0.4,3:0.8,4:0.85,5:0.7,6:0.75,7:0.75" 0.85,0.75` -> `rest_error.py`,
`texture_drift.py`, `drift_visible.py`, `region_error.py`, `probe_max.py` -> `REA_KEPT_NORMALS=1 cand_glb.sh l
Cand_85 kn` (copy `work/glb_l_85kn.glb` to `work/l85_lod0.glb`) -> `spike_points.py`, `REA_NODE=Titan
floor_points.py` -> build as above -> `compare_glb.py`, `grip_check.py ... Titan`, `height_check.py`, `lod_check.py`
(REA_NODE=Titan), `lod_views.py`, `glb_close.py`, `viewer_variants.py`, `viewer_sword.py`, `viewer_manifest.py "MM7
Titan" r85 10320 8946`. Blender scripts run through `scripts/bl.sh` (lease wrapper, `TOKEN`). Ladder ratios must
differ by at least 1 % overall: `decimate_tex.py` names its outputs by `int(ratio * 100)`.

**Installed 2026-10-20** (user acceptance) with `../mm7_batches/BATCH_C_stage/install.sh`; bindings in `../mm7_m414_claude/integration/actors.yml`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Attack sinks to -8.9; Standing sinks to -8.5; dying sinks to -10.6; standing at -8.4.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m414.glb export/mm7_m414.glb --lift-joints Attack Dead Death Standing --lift-only 'B_Skirt*,Robe_*,…' --ground-loop Standing --raise Attack --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m414.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Heavy walk and march — 2026-10-21

User: walk rework. The Titan wanders at 0.53 and chases at 1.07 model units/s
(`claude_shared/postprocess/gait_gate.py`); its walk covers 1.91 per 1.0 s loop, so it played at 0.29x wandering and
0.58x chasing (slow motion). Two new clips derived from the installed `Walking` by `scripts/derive_walk.py`
(copied from `../mm6_ttn_reduce_claude/scripts/`, settings `scripts/gait_m414.json`; no Blender, no Meshy):

| clip | role | length | stride | authored speed | derivation from Walking |
|---|---|---:|---:|---:|---|
| `WalkHeavy` | walk | 2.00 s | 1.067 | 0.53 | forward travel x0.55, cycle stretched x2, feet 3 cm wider, lift x0.85, foot pitch x0.7, pelvis 4 cm higher than the source walk (knees 23-68 deg, not a crouch), sway x1.4, 1.2 cm settle per heel strike, 4 deg lean, arm swing x0.55 (sword arm x0.6), arms 4 deg out |
| `March` | run | 1.33 s | 1.457 | 1.09 | forward travel x0.75, cycle x1.33, feet 2 cm wider, full lift, pitch x0.85, pelvis 3.5 cm higher, sway x1.15, 2 deg lean, arm swing x0.8, arms 3 deg out |

Legs are re-solved by two-bone IK (knee in the source knee's direction carried onto the new hip-ankle line), each
foot's lowest vertex returned to the source's height, arms scaled about their cycle mean (the authored sword carry is
the mean, so the blade stays forward). Every other clip is unchanged. No floor pass was applied: the source walk
already dips 1.4 cm in places and `--ground-loop` would have turned that into per-key pelvis jitter; the floor audit
passes as is.

- Gate: `gait_gate.py --world mm7 --model mm7_m414.glb --candidate export/mm7_m414_gait.glb --set walking=WalkHeavy
  --set run=March --set stride_length=1.067 --set run_stride_length=1.457`: strides trusted (1.067 / feet 1.080,
  1.457 / 1.460), wander WalkHeavy x1.00, chase March x0.98 on all three tiers, floor ok. PASSED.
- `scripts/gait_probe.py`: no knee bends backward, loop seam 0. `scripts/gait_arms.py`: wrist <= 61 / 41 deg (source
  67 / 52), forearm/hand >= 3.1 cm from torso, pelvis and thighs (old walk 1.3 cm). `scripts/gait_sword.py`: blade
  >= 9.1 cm from the body (old walk 6.6 cm), lowest blade point 62 cm. `check_winding.py` 0 inverted.
- Review: `review/gait/v2.png` (clay sheet: old, heavy, march), `review/playback/` (viewer recordings of WalkHeavy,
  March and Walking with the sword, 1x and 0.5x), `review/gait/playback_sheet.png`. The viewer manifest now shows the
  gait export (`mm7_m414_*_gait.glb`); the reduction review's manifest is kept as `review/viewer/manifest_reduce.json`.
- Installed: `tools/install_model.py export/mm7_m414_gait.glb --world mm7 --name mm7_m414.glb` (the sword is
  unchanged). The `actors.yml` binding (walking WalkHeavy, run March, strides 1.067 / 1.457) is left to the
  coordinating agent; until then the game plays the unchanged Walking/Running. Rollback: install
  `export/mm7_m414.glb` the same way.
- Rebuild: `derive_walk.py export/mm7_m414.glb export/mm7_m414_gait.glb scripts/gait_m414.json`.
