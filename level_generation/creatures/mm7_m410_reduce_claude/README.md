# MM7 Thief (`m410`, Thief / Rogue / Master Thief) reduction (2026-10-20)

User: "do the tris reduction playbook on these 5" (the five MM7 batch-C humanoids; this project is m410 only). Default
route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that
keeps the UVs, so the textures, the three tier variants (`KHR_materials_variants`) and the region ramps stay valid. No
Meshy credits. **Not installed** (batch C: the user installs later).

[Review viewer](review/viewer/index.html) (source vs reduced, tiers A/B/C, all eight clips, dagger on its joint)

## Source

`../mm7_m410_claude/export/mm7_m410.glb` and `mm7_m410_dagger.glb` (accepted 2026-10-20, after `despike.py`), copied
to `work/mm7_m410_source_pre_reduce.glb` and `work/mm7_m410_dagger_source_pre_reduce.glb` (rollback sources). One
merged body + head atlas material per tier (`Thief_A/B/C`, 2080x1024), node `Thief`, 57 joints (incl. `Dagger`), 4
influences at LOD0 (8 slots at LOD1-3), shadow LODs, clips Standing, Walking, Running, Attack, Hit, Death, Dead,
Fidget. Bind height 1.80 m (ladder limits p99 5.4 mm, max 27 mm). Weld: 5,814 -> 486 open edges, 2 coincident
vertices with other weights (kept apart by `decimate_tex.py`), 11,282 -> 11,281 triangles: the source holds one chest
triangle twice (LOD0 faces 6143/6145, the second copy reversed). The material is double-sided, so the single copy
renders the same; the faces around it are kept. Scripts start from `../mm7_m406_reduce_claude/scripts/` (paths, node
`Thief`, height, dagger); `decimate_tex.py` now skips an empty free part.

## Where the triangles are (`scripts/m410_pieces.py`, `review/labels/pieces.png`)

| piece | faces | |
|---|---:|---|
| torso shell (vest, bare arms, hands, neck, high collar) | 3,775 | hands 1,958 (hand + finger weight), vest 857 (region mask R), arms/neck/collar 960 |
| head (face, ears, scalp) | 1,276 | 548 visible (329 face front), 728 hidden under cap and mask |
| boots | 968 | 315 sole faces |
| shoulder caps | 948 | |
| trousers | 779 | already coarse (40 mm mean edge) |
| knitted cap | 733 | |
| coin pouch + its back piece | 567 + 350 | dense (13 / 9 mm mean edge) |
| wrist band + gold bangles | 562 | kept exactly |
| dagger sheath + mouth piece | 443 + 37 | kept exactly |
| belt with the chest strap | 322 | kept exactly |
| eyes, mask, buckle, boot ornament | 229, 138, 117, 37 | kept exactly |

The broad surfaces (vest, trousers, boots) were already coarse; the dense surfaces are the hands, the pouch, the
shoulder caps, the cap and the head.

## Keep set and groups (`scripts/m410_sets.py` + patches, pick = set `t`, `review/labels/sets_t.png`)

Kept exactly (`work/keep_t.npy`, 6,606 faces): the whole torso shell, i.e.
- both hands (every face touching a vertex with hand + finger weight > 0.3: the fist draws the dagger, the attack is
  authored);
- the vest (857 faces; the studded quilted pattern: at 75 % and 85 % the back seam bent into a diagonal and the studs
  stretched, `review/glbclose/sheet_vest_c76.png`; painted trims and studs touch 725 of its 857 faces with one ring);
- the bare arms, neck and high collar (at 60-70 % the upper-arm skin reached p99 9-13 mm and its max error moved from
  elbow to armpit to the back of the upper arm with every patch; at 80 % it still left visible slivers under the
  shoulder caps; keeping it costs about 100 triangles);

plus the sheath and its mouth piece (the `Dagger` bone follows the sheath's deformed vertices), the wrist band and
bangles, belt and strap, buckle, mask, eyes, boot ornament, the soles (faces below 6 cm), the visible face front, the
doubled chest triangle, the cap brim (faces within 2.5 cm of the cap's lowest point per 15-degree sector:
`rim_keep.py`), and 2-3 cm patches (`patch_keep.py`, mirrored) at the max-error and sliver spots of the earlier
ladders: armpits, elbow fronts and backs, upper-arm backs under the shoulder caps, the front of the neck, the front
inner edge of the left shoulder cap, and the back of the right boot cuff.

| group | faces | ratio |
|---|---:|---|
| 1 visible head sides (ears, temples) | 219 | 65 % |
| 2 hidden head skin (under cap and mask) | 728 | 50 % |
| 3 knitted cap (brim kept) | 601 | 70 % (55 % softened the knit and folded the brim) |
| 4 shoulder caps | 826 | 55 % (40 % left slivers along the inner rim) |
| 5 coin pouch | 567 | 25 % |
| 6 pouch back piece | 350 | 25 % |
| 8 trousers | 763 | 65 % |
| 9 boots | 621 | 60 % |

## Ladder (limits for 1.80 m: p99 5.4 mm, max 27 mm; IoU >= 0.98, SSIM >= 0.93)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 11,281 | | | | |
| a: arms/legs free 60-40 %, vest 80 % | r77-r73 | 8,701-8,237 | 5.09-7.49 / 33-41 | 0.990-0.983 | | fail (max: elbows, armpits) |
| b: legs and boots own groups, free 80-60 % | r78-r76 | 8,835-8,665 | 3.68-4.95 / 27.03-28.91 | 0.995 | 0.996 | fail (neck front, upper arm) |
| c: + patches, free 90 % | r77 / r76 | 8,689 / 8,647 | 4.03 / 20.93 | 0.993 | 0.995 | pass; vest seam bent |
| d: harder groups, vest 75 % | r74 | 8,375 | 4.44 / 20.5 | 0.991 | 0.994 | pass; vest torn, cap soft |
| e/f/g/h: vest kept, cap 70 %, free 85-65 % | r77-r76 | 8,701-8,585 | 4.21-4.87 / 18.9-26.2 | 0.993 | 0.995 | pass; h76 (8,643): dark wedge above the right band |
| i / j: legs 50-60 %, hidden head 40-45 % | r73 / r75 | 8,275 / 8,505 | 6.75 / 5.57 | | | fail (p99) |
| k: h + 3 cm drift lock | r77 | 8,683 | 4.97 / 22.32 | 0.991 | 0.995 | pass; gold streak above the left bangles |
| n: + forearm skin by the bands kept (`cuff_keep.py`), free 80 % | r77 | 8,763 | 4.32 / 18.89 | 0.994 | 0.996 | pass; 6 visible new slivers (arms, shoulder caps, boot cuff) |
| q/r: arms kept, shoulder caps 55 %, sliver patches | r79 / r80 | 9,003 / 9,045 | 4.01 / 18.89 | 0.995 | 0.997 | pass; 1-3 visible slivers left |
| **t: r + shoulder-cap rim patches** | **r80** | **9,077** | **3.95 / 18.89** | **0.9943** | **0.9968** | **pick: no visible new slivers or long faces** |

The pick is the lowest configuration that passes the ladder, looks like the source in the textured and clay close-ups
and adds no visible sliver: the 8.4-8.7k steps passed the error gates but tore the vest pattern, smeared band colour
onto the forearms or left visible slivers. The 18.9 mm maximum is in Death frame 30, the same at every step. Texture
drift (`texture_drift.py` + `drift_visible.py t_r80`, visible faces): 10 faces over 40 (17.9 cm2), largest 3.7 cm2 (back
of the right shoulder cap); none shows in the close-ups.

Slivers and long faces (`scripts/sliver_probe.py`, the criteria of the source project's `find_slivers.py` and
`find_long_faces.py`, copied beside it; `scripts/sliver_vis.sh t_r80` adds each face's visibility from 26 views):
source 27 slivers and 48 long faces; pick 34 and 43. 8 slivers are new (2.6-5.1 cm long, 1.5-3.9 mm high), all in
faces never visible from any of the 26 views: the head skin under the cap and mask (6) and two faces at the back of the head under the cap brim (2). No new long
face, so the despiked mask-to-arm sliver does not come back.

## Build

`cand_glb.sh t Cand_80 kn` with `REA_KEPT_NORMALS=1` (source GLB normals on the 21,852 corners of unchanged source
faces and on 1,925 kept smooth vertices, computed smooth normals elsewhere) -> `export_cand.py` -> `swap_lod0.py`
(`work/t80_lod0.glb`) -> `cap_points.py` (13 cap-tip points, replaces the Swordsman's `spike_points.py`) and
`REA_NODE=Thief floor_points.py` (24 Dead/Death floor contacts) -> `build_lods.py` (`tools/build_actor_lods.py`, 8
influence slots as the source, ratios 0.5 / 0.22 / 0.074, 37 protected points) -> `shrink_shadow_lods.py` (the source
project's script: shadow LODs inset 13-15 mm) -> `carry_variants.py` (7 primitives) -> `check_winding.py` (0 inverted
closed parts): `export/mm7_m410.glb`, 7.81 MB (source 8.00 MB). All LOD UVs stay inside [0, 1] (no
`clamp_lod_uv.py` needed).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 11,282 | 5,639 | 2,029 | 676 |
| reduced body | **9,077** | **4,537** | **1,995** | **671** |
| dagger (`export/mm7_m410_dagger.glb`, byte-identical copy) | 282 | 140 | 50 | 23 |

The source's 0.18 / 0.06 would give 1,634 / 545; 0.22 / 0.074 keeps LOD2/LOD3 just below the source's counts
(`review/lods/sheet.png`: LOD3 face and cap read as well as the source LOD3).

Checks:
- `scripts/compare_glb.py`: node names and transforms, skin and inverse binds, materials and extras, images, textures,
  samplers, all eight clips (sampler data), mesh names/extras and the variants extension identical to the source;
  `KHR_materials_variants` (m410_a/b/c) on all 8 colour/shadow primitives. `DIFFERENCES none`.
- `scripts/grip_check.py` (`work/grip_check.log`): all 1,444 LOD0 vertices with hand + finger weight > 0.5 keep their
  bind positions (max 0.0004 mm) and weights exactly. `scripts/kept_check.py` (`work/kept_check.log`): sheath (250
  vertices), bands (285), belt and strap (219), buckle, mask, eyes and boot ornament keep their positions (<= 0.0004 mm)
  and weights (the one belt "difference" is a coincident duplicate matched to its twin; every belt vertex has an exact
  copy). The sheathed dagger, its track and the draw are therefore unchanged
  (`review/glbclose/sheet_viewer_dagger_tiers.png`).
- `work/lod_check_{src,t80}.json`: every LOD keeps the 1.7996 m top (source 1.800 / 1.7999 / 1.8008 / 1.7988) and the
  source's bounds; lowest point per clip equals the source's at LOD0 (Dead 0.4 vs 1.0 mm) and is within 0-8 mm at
  LOD1-3 (largest: LOD3 Hit -12.3 vs -4.6 mm, a foot in the hit stagger); faces stretching over 20x per clip are the
  same counts as the source at every LOD (LOD0 Attack 8, Hit 8: source faces in kept areas).
- Close-ups straight from the GLBs, source vs pick, textured and clay (`scripts/glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_t80_head.png` (face, mask, cap, collar, shoulder caps), `sheet_t80_body.png` (vest front,
  back and side, pouch, belt, arms, elbows), `sheet_t80_legs.png` (hands, bands, forearms, knees, boots, draw, Attack,
  Death); `sheet_vest_c76.png` (why the vest is kept), `sheet_hk_forearm.png` (band colour on the forearm at h76/k77).
- Viewer: `review/viewer/` (source vs 80 % pick, tiers A/B/C with the ramps baked by `viewer_variants.py`, dagger
  added under the `Dagger` joint for review only by `viewer_dagger.py`); `python3 tools/run_creature_review.py
  --project level_generation/creatures/mm7_m410_reduce_claude --token <lease> check`: 48 switches, no console errors.

## Open points for review

- The cut is modest (-19.5 %): two thirds of the mesh is kept exactly (hands 1,958, the patterned vest, bands, sheath,
  belt, mask, eyes, face front). Cutting the vest would need a retexture or a vest-specific UV-locked decimation.
- Shoulder caps at 55 %: in clay their lower rim reads a little harder; textured it is unchanged.
- The coin pouch at 25 % is slightly more faceted in clay; textured it reads the same.
- The source's mask slits and the thin vertical shard down the mask front are unchanged (source geometry).
- Inherited from the source (unchanged): hand/forearm touch the belt at the draw and sheathing; the sheathed dagger
  touches the thigh in the run and the lying death; tier C runs (270 vs 269.5), A and B walk.

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m410_reduce_claude/export/mm7_m410.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m410_reduce_claude/export/mm7_m410_dagger.glb --world mm7
```

then the binding from `../mm7_m410_claude/README.md` (unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m410_source_pre_reduce.glb` (+
`work/mm7_m410_dagger_source_pre_reduce.glb`) the same way.

## Reproduce

`REA_GLB=<abs path of work/mm7_m410_source_pre_reduce.glb> REA_NODE=Thief import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m410_source_pre_reduce.glb` -> `m410_pieces.py` ->
`REA_MIN_PIX=6 visibility.py 1.40 1.81` (copy to `work/visible_head.npy`) and `visibility.py -0.01 1.81`
(`work/visible_all.npy`) -> `REA_PATCH_R=0.03 patch_keep.py - work/patch_b.npy 0.134,0.011,1.210 0.186,0.038,1.236
0.323,0.084,1.155`, then `work/patch_c.npy` (+ 0.052,-0.038,1.465), `work/patch_f.npy` (+ 0.244,0.102,1.146),
`work/patch_h.npy` (+ 0.237,0.050,1.315 0.206,0.123,1.234) -> `m410_sets.py c` (vest = its group 7, saved as
`work/vest_all.npy`), `rim_keep.py work/rim_g.npy`, `M410_EXTRA_KEEP=work/patch_h.npy,work/vest_all.npy,work/rim_g.npy
m410_sets.py h` -> `cuff_keep.py work/keep_h.npy work/keep_m.npy` -> `REA_PATCH_R=0.03 patch_keep.py work/keep_m.npy
work/keep_n.npy 0.260,0.030,1.170` -> keep_q = keep_n | all remaining free faces -> `REA_PATCH_R=0.025 patch_keep.py`
(`keep_q` -> `keep_r`: 0.227,0.002,1.364 0.143,0.077,0.408; `keep_r` -> `keep_t`: 0.19,-0.018,1.365 0.206,0.0,1.384),
groups = groups_h with kept faces set to 0 -> `TOKEN=<lease> run_ladder.sh t t
"1:0.65,2:0.5,3:0.7,4:0.55,5:0.25,6:0.25,8:0.65,9:0.6" 1.0` -> `texture_drift.py t_r80`, `drift_visible.py t_r80`,
`sliver_vis.sh t_r80` -> `REA_KEPT_NORMALS=1 cand_glb.sh t Cand_80 kn` (copy `work/glb_t_80kn.glb` to
`work/t80_lod0.glb`) -> `cap_points.py`, `REA_NODE=Thief floor_points.py` -> build as above -> `compare_glb.py`,
`grip_check.py ... Thief`, `kept_check.py`, `lod_check.py` (REA_NODE=Thief), `lod_views.py`, `glb_close.py`,
`viewer_variants.py`, `viewer_dagger.py`, `viewer_manifest.py "MM7 Thief" r80 11282 9077`. Blender scripts run
through `scripts/bl.sh` (lease wrapper, `TOKEN`).

## Textures updated (2026-10-20)

The source project's body textures were recomposed after this reduction (arm and trouser patches,
`../mm7_m410_claude/README.md`). `work/mm7_m410_source_pre_reduce.glb` is now that re-export, and
`scripts/transplant_images.py` copied its four images and the materials' region ramps into `export/mm7_m410.glb`
(geometry, LODs, clips and variants unchanged; `compare_glb.py`: no differences). The viewer GLBs were rebuilt
(`viewer_variants.py`, `viewer_dagger.py`, `viewer_manifest.py`); viewer check 48 switches, no errors.
Second review: the source's despike unfold moved 78 vertices at the right biceps and the mask; `scripts/carry_positions.py`
gave the 130 reduced-mesh vertices at those source positions (all LODs) their new positions, and the repainted images
were transplanted again (`compare_glb.py`: no differences); viewer check 48 switches, no errors.

**Installed 2026-10-20** (user acceptance) with `../mm7_batches/BATCH_C_stage/install.sh`; bindings in `../mm7_m410_claude/integration/actors.yml`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -3.3.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m410.glb export/mm7_m410.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m410.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package h08 of [the gait rollout](../gait_rollout_20261031/README.md) appended `Jog` (humanoid set
Unarmed-Run-Forward, 0.74 s, stride 3.2109) and `Sprint` (Unarmed-Sprint, 0.60 s, stride 4.3333) to the installed
`mm7_m410.glb` (existing clips byte-identical) and installed it; the `Dagger` node follows its sheath in both. Bindings
for the coordinator: `run: Jog`, `run_stride_length: 3.2109`, `sprint: Sprint`, `sprint_stride_length: 4.3333`
(`../gait_rollout_20261031/h08/bindings.yml`). Rebuild: `../gait_rollout_20261031/h08/scripts/rebuild.sh m410`;
details and gates in [the package README](../gait_rollout_20261031/h08/README.md). A far-LOD repair rerun or any
re-export of this model must re-graft these clips (rerun that rebuild on the new source).
