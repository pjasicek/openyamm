# MM7 Elf Archer (`m214`, Elven Archer / Scout / Ranger) reduction (2026-10-20)

User: "do the tris reduction playbook on these 5" (the five MM7 batch-C humanoids; this project is m214 only). Default
route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that
keeps the UVs, so the textures, the three tier variants (`KHR_materials_variants`) and the region ramps stay valid. No
Meshy credits. **Not installed** (batch C: the user installs later).

[Review viewer](review/viewer/index.html) (source vs reduced, tiers A/B/C, all eight clips, bow and nocked arrow in
their sockets)

## Source

`../mm7_m214_claude/export/mm7_m214.glb`, `mm7_m214_bow.glb` and `mm7_m214_arrow.glb` (accepted 2026-10-20), copied to
`work/mm7_m214_source_pre_reduce.glb`, `work/mm7_m214_bow_source_pre_reduce.glb` and
`work/mm7_m214_arrow_source_pre_reduce.glb` (rollback sources). One skinned mesh node `Elf` with one merged body + head
atlas material per tier (`Elf_A/B/C`, 2080x1024), 60 joints, 4 influences at LOD0 (8 slots at LOD1-3), shadow LODs,
clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget, `Socket_Arrow_Release`. Bind height 1.73 m
(1.750 m with the quiver fletchings). The bowstring is part of the body (skinned tube, `Bow` ends, `StringNock` middle).
Weld: 6,143 -> 675 open edges, no coincident vertices with other weights, 8,037 triangles in and out (no two-sided
sheets). Scripts start from `../mm7_m406_reduce_claude/scripts/` with the elf's names, plus `shrink_shadow_lods.py` and
`clamp_lod_uv.py` from the source project.

## Where the triangles are (`scripts/m214_pieces.py`, `review/labels/pieces.png`)

| piece | faces | |
|---|---:|---|
| head piece (face, ears, scalp, neck, the chest and midriff skin under and between the vest) | 2,247 | 1,774 visible |
| hands (fingers; left fist holds the bow, right draws the string) | 1,506 | kept exactly |
| vest (with the upper arms) | 704 | |
| hair | 664 | |
| trousers | 502 | |
| pouches and belt bits (12 pieces) | 490 | pieces up to 80 faces kept |
| bare feet and calves | 387 | 251 sole faces |
| quiver arrows and fletchings (11 pieces) | 364 | kept exactly |
| quiver | 334 | |
| waist straps | 283 | |
| bowstring | 192 | kept exactly |
| forearms (tooled bracers, 2 pieces) | 152 | kept exactly |
| eyes, calf lacing, hair tie | 212 | kept exactly |

The source build had already cut the body 14.65k -> 7.87k with head and hands protected, so only about 3,100 faces
outside the protected parts were open to a cut.

## Keep set and groups (`scripts/m214_sets.py`, pick = set `f`, `review/labels/sets_f.png`)

Kept exactly (`work/keep_f.npy`, 4,915 faces): both hands and every face touching a vertex with hand + finger weight
> 0.3; both forearms (bracers; the right one's texture is mirrored from the left); the bowstring; every piece of up to
80 faces (eyes, arrows and fletchings, lacing, belt bits, hair tie); the visible face front (837) and both ears (212,
faces over 7.2 cm from the head axis); the waist straps; the whole feet; 4 cm patches at the back of both elbows, the
sternum and both knees (max error spots of the first ladder); a 3 cm drift lock around a dark patch on the vest's upper
back and one at the left hip (`texture_drift.py` on d83, one round); the vest, trouser and skin faces within 2 cm of a
strap, pouch or lacing vertex (`under_keep.py`: at e85 the decimated vest pushed through the kept upper strap at the
front, `review/glbclose/sheet_e85_waist.png`).

| group | faces | ratio |
|---|---:|---|
| 2 visible head sides (jaw, neck, under the chin) | 345 | 60 % |
| 3 hidden head-piece skin (scalp under the hair, skin under the vest) | 495 | 75 % (45-60 % flattened the scalp 12-14 mm inward and dominated p99) |
| 4 hair | 664 | 55 % (p99 4.7 mm; the open hair edge is preserved as a cut boundary) |
| 5 quiver | 274 | 60 % (50 % reached p99 5.4 mm) |
| 7 pouches (the two large ones) | 184 | 60 % |
| 8 visible chest and midriff skin | 261 | kept (85 % gave p99 7.4 mm in the poses) |
| 0 vest, trousers | 899 | free, takes the ladder budget (60 % at the pick) |

## Ladder (limits for the 1.73 m height: p99 5.19 mm, max 25.95 mm; IoU >= 0.98, SSIM >= 0.93)

| config | free | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 8,037 | | | | |
| a: hidden 45 %, chest 70 %, straps 75 % | 70 % | 6,645 | 7.78 / 24.24 | 0.9926 | 0.9942 | fail (hidden scalp, chest skin, straps) |
| b: + elbow/sternum/knee patches, hidden 75 %, chest 85 %, straps 90 % | 70 % | 6,893 | 4.27 / 20.40 | 0.9922 | 0.9949 | pass |
| b | 60 % | 6,767 | 5.22 / 20.82 | 0.9912 | 0.9932 | fail |
| c: hair, quiver, pouches 50-55 %, hidden 60 %, chest kept | 75 % | 6,761 | 5.10 / 16.68 | 0.9928 | 0.9949 | pass, hidden scalp p99 12.4 |
| d: hidden 75 %, quiver/pouches 55-60 %, chest kept | 62 % | 6,721 | 4.91 / 20.82 | 0.9912 | 0.9934 | pass; vest back blotch, straps wavy, feet faceted |
| d2 | 57 % | 6,595 | 6.03 / 20.90 | 0.9861 | 0.9907 | fail |
| e: d + drift lock, straps and feet kept | 60 % | 6,833 | 4.88 / 20.82 | 0.9919 | 0.9940 | pass; vest pokes through the upper strap |
| f: e + faces under straps, pouches, lacing | 65 % | 6,975 | 4.27 / 19.79 | 0.9933 | 0.9947 | pass |
| f | 55 % | 6,885 | 5.46 / 32.85 | 0.9902 | 0.9923 | fail |
| **f2: f** | **60 %** | **6,931** | **4.56 / 22.66** | **0.9925** | **0.9944** | **pick** (`work/selection_f2.json`, Cand_86) |

The pick is the lowest passing step of the first config that also looks right in the close-ups: d83 (6,721) and e85
(6,833) passed the numbers but showed the vest-back blotch / wavy straps and the vest poking through the upper strap.
The maximum (22.7 mm, Attack frame 30) sits on the right upper arm next to the vest in the deep draw. Texture drift
(`texture_drift.py` + `drift_visible.py f2_r86`, visible faces only): 6 faces over 40 (45 cm2), on a large vest-front
face and quiver faces; none shows in the close-ups.

## Build

`cand_glb.sh f2 Cand_86` with `REA_KEPT_NORMALS=1` (`kept_normals.py`: source GLB normals on the 17,475 corners of
unchanged source faces and on 1,315 kept smooth vertices, computed smooth normals elsewhere) -> `export_cand.py` ->
`swap_lod0.py` (`work/f86_lod0.glb`) -> `lod_points.py` (head crown, 11 arrow tips, 8 face landmarks, the string's
nock ring and both string tips) and `floor_points.py` (24 Dead / Death floor contacts) -> `build_lods.py`
(`tools/build_actor_lods.py`, 8 influence slots as the source, ratios 0.5 / 0.205 / 0.072, 52 protected points) ->
`shrink_shadow_lods.py` (the source project's script: shadow LODs inset as in the source export) ->
`carry_variants.py` -> `clamp_lod_uv.py` (a 0.0003 UV overshoot on LOD1, as in the source chain) -> `check_winding.py`
(0 inverted closed parts): `export/mm7_m214.glb`, 6.83 MB (source 6.87 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 8,037 | 4,008 | 1,427 | 455 |
| reduced body | 6,931 | 3,456 | 1,405 | 476 |
| bow (`export/mm7_m214_bow.glb`, byte-identical copy) | 1,328 | 664 | 238 | 78 |
| arrow (`export/mm7_m214_arrow.glb`, byte-identical copy) | 36 | 24 | 24 | 24 |

LOD ratios: 0.5 / 0.2 / 0.065 gave 1,370 / 427, and LOD2/LOD3 flattened the face into a box (worse than the source
LODs: the leaner reduced body leaves the uniform collapse to the dense face). 0.205 / 0.072 with the face landmarks
matches the source's LOD2/LOD3 look (`review/lods/sheet_ratios.png`: f86 = 0.065, f86b = final; `review/lods/sheet.png`: source vs final). LOD3 is 21 triangles
above the source; about as many go to the string, which the source LODs collapsed to 6 faces without a nock vertex
(the distant string stayed straight while the right hand drew it); every reduced LOD keeps the nock ring (22 string
faces, StringNock weights exact).

Checks:
- `scripts/compare_glb.py` (`work/compare_glb.log`): node names and transforms, skin and inverse binds, materials and
  extras, images, textures, samplers, all eight clips (sampler data), mesh names/extras and the variants extension
  are identical to the source; `KHR_materials_variants` (m214_a/b/c) on all 8 colour/shadow primitives.
- `scripts/grip_check.py` (`work/grip_check.log`): all 1,271 LOD0 vertices with hand + finger weight > 0.5 keep their
  bind positions (max 0.0007 mm) and weights exactly, so the solved left bow fist and the right drawing hand are the
  same; the string's 192 faces are kept exactly.
- `work/lod_check_{src,f86}.json` (`f86` = the final file): rest bounds of every LOD equal the source's same LOD;
  top 1.7504 m at LOD0/1 and 1.7517 m at LOD2/3 (1.3 mm over; source LOD2/3 sank to 1.7491 / 1.7479); lowest point
  per clip equals the source's LOD0 in every clip at LOD0, within 1 mm at LOD1 (source LOD1 up to 2 mm) and within
  -2..+4.7 mm at LOD2/3 (source -9.7..+4.7 mm: its LOD3 sank 1 cm in Dead); no face stretches over 20x in any frame
  of any clip at any LOD. The source's own Death dip (-3.7 cm) and Dead lift (3.0 cm) are unchanged.
- Close-ups straight from the GLBs, source vs pick, textured and clay (`scripts/glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_f86_head.png` (face, ears, hair, back of the head, quiver top and fletchings),
  `sheet_f86_body.png` (vest front and back, both waist sides, both hands, both bracers), `sheet_f86_legs.png` (legs,
  feet, full draw, draw hands, walk, Death); `sheet_d83_*.png` and `sheet_e85_*.png` show the rejected steps.
- Viewer: `review/viewer/` (source vs 86 % pick, tiers A/B/C, bow and nocked arrow added under the `Bow` and `Arrow`
  joints for review only by `viewer_props.py`); `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_m214_reduce_claude --token <lease> check`: 48 switches, no console errors.
  `review/shots/sheet_bow.png` (tier A standing, full draw at 1.0 s and walk, source vs pick: bow grip and string
  unchanged), `review/shots/sheet_tiers.png` (tiers A/B/C standing and full draw).

## Open points for review

- The gain is modest (-14 % at LOD0): the source body was already reduced once with head and hands protected, and the
  hands (1,506), face, ears, string, arrows and other small pieces (4,915 faces in all) are kept exactly.
- Clay renders show the vest a little more faceted at the collar beside the neck and at the upper back; textured they
  read unchanged.
- LOD3 (476) is 21 triangles above the source LOD3 (455), spent on the drawn string's nock.
- The bow and arrow attachments were left byte-identical (1,328 / 36 triangles; the bow's grip is fitted to the solved
  fist and the arrow is already minimal).

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m214_reduce_claude/export/mm7_m214.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m214_reduce_claude/export/mm7_m214_bow.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m214_reduce_claude/export/mm7_m214_arrow.glb --world mm7
```

then the binding from `../mm7_m214_claude/README.md` (unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m214_source_pre_reduce.glb` (+
`work/mm7_m214_bow_source_pre_reduce.glb`, `work/mm7_m214_arrow_source_pre_reduce.glb`) the same way. After a later
re-export of the source clips: `python3 scripts/transplant_clips.py ../mm7_m214_claude/export/mm7_m214.glb
export/mm7_m214.glb export/mm7_m214.glb`.

## Reproduce

`REA_GLB=<abs path of work/mm7_m214_source_pre_reduce.glb> REA_NODE=Elf import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m214_source_pre_reduce.glb`, `small_pieces.py` -> `m214_pieces.py` ->
`REA_MIN_PIX=6 visibility.py 1.25 1.76` (copy to `work/visible_head.npy`) and `visibility.py -0.01 1.76`
(`work/visible_all.npy`) -> `patch_keep.py - work/patch_b.npy -0.295,0.051,1.161 -0.008,-0.072,1.262 -0.129,-0.091,0.513`
-> set d and `run_ladder.sh d d ...` as in the table, `texture_drift.py d_r83`, `REA_LOCK_R=0.03 drift_lock.py
work/patch_b.npy work/lock_e.npy d_r83` -> `work/straps_feet.npy` (pieces 10 and 11), `under_keep.py work/under_f.npy`
-> `M214_EXTRA_KEEP=work/lock_e.npy,work/straps_feet.npy,work/under_f.npy m214_sets.py f` ->
`TOKEN=<lease> run_ladder.sh f2 f "2:0.6,3:0.75,4:0.55,5:0.6,7:0.6,8:1.0" 0.6` -> `region_error.py`, `probe_max.py`,
`texture_drift.py f2_r86`, `drift_visible.py f2_r86` -> `REA_KEPT_NORMALS=1 cand_glb.sh f2 Cand_86 kn` (copy
`work/glb_f2_86kn.glb` to `work/f86_lod0.glb`) -> `lod_points.py work/mesh_f2_r86.npz`, `REA_NODE=Elf floor_points.py
<abs work/f86_lod0.glb>` -> build as above -> `compare_glb.py`, `grip_check.py ... Elf`, `lod_check.py`
(REA_NODE=Elf), `lod_views.py`, `glb_close.py`, `viewer_variants.py`, `viewer_props.py`, `viewer_manifest.py "MM7 Elf
Archer" r86 8037 6931`. Blender scripts run through `scripts/bl.sh` (lease wrapper, `TOKEN`); the MeshLab step uses
the pymeshlab venv named in `run_ladder.sh`.

**Installed 2026-10-20** (user acceptance) with `../mm7_batches/BATCH_C_stage/install.sh`; bindings in `../mm7_m214_claude/integration/actors.yml`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: corpse at +3.6; dying sinks to -4.5.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m214.glb export/mm7_m214.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m214.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/h12`](../gait_rollout_20261031/h12/README.md) appended Walk2 (humanoid set Relax-Walk-Forward,
1.04 s, a slower wander walk) and Jog (Unarmed-Run-Forward, 0.80 s) to the installed
`assets_source/worlds/mm7/models/mm7_m214.glb` and installed it (existing clips, meshes, skins and materials
byte-identical; arms and bow from Walking / Running). Bindings for the coordinator (`h12/bindings.yml`, all three tiers):
walking: Walk2, stride_length 1.4323, run: Jog, run_stride_length 2.4562 (tier A no longer walks as it chases: its chase
is a run pace). `Walking` and `Running` stay in the GLB, no longer bound for locomotion.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h12/scripts/rebuild.sh m214` (from `h12/work/mm7_m214_pre_gait.glb`, the
rollback source). A far-LOD repair rerun, a floor fix or any re-export of this model must re-graft these clips: copy the
new source over `h12/work/mm7_m214_pre_gait.glb` and rerun the rebuild, then install with `tools/install_model.py`.
