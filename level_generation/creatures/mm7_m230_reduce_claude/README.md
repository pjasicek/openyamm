# MM7 Plate Fighter (`m230`, Initiate / Champion / Master of the Sword) reduction (2026-10-20)

User: "reduce tris on all 5" (the five MM7 batch-A humanoids; the other four are separate projects). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: the source textures, three tier variants and
region ramps stay valid. No Meshy credits. **Installed 2026-10-20** (batch A stage).

Source: the project export `../mm7_m230_claude/export/mm7_m230.glb` (rebuilt and accepted 2026-10-20; nothing is
installed yet), copied to `work/mm7_m230_source_pre_reduce.glb` (rollback source), and its sword
`work/mm7_m230_sword_source_pre_reduce.glb`. One merged body + helm atlas material (`M230_A/B/C`, 2080x1024), one
`M230` node, 57 joints, 4 influences on LOD0, 8 clips. Scripts are copied from `../mm8_m432_reduce_claude/scripts/`
(per-region groups, keep sets, `glb_close`, `grip_check`, fixed parenting order), `probe_max.py` from
`../mm6_ttn_reduce_claude/`, `patch_keep.py`/`region_error.py` from `../mm8_m656_reduce_claude/`, and
`shrink_shadow_lods.py` from the source project. `scripts/bl.sh` runs a Blender script through the lease wrapper.

## Where the triangles are

`import_source.py`: 8,898 triangles in and out; weld 5,554 -> 1,298 open edges (the Smart Topology plates are separate
open segments); 2 coincident vertices with other weights (kept apart by `decimate_tex.py`). No two-sided sheets.
Source shading is smooth (7 sharp normal groups, all on UV seams), so the candidates' smooth normals match it.

`scripts/m230_regions.py` (connected pieces): body plates 4,615 (cuirass/tabard, tabard skirt, thigh and leg plates,
arm plates, sabatons), gauntlets with fingers and vambraces 2,339, helm 650, eagle crest 324, plume strands 591,
small pieces (<= 80 faces) 379. Gold trims are painted on 37 % of the faces (3,316), so they cannot all be kept; plate
rims sit on the open segment borders, which the MeshLab cut keeps.

Limits for the 1.664 m bind height: p99 4.99 mm, max 24.96 mm.

## Keep sets and groups

`scripts/m230_sets.py`, `patch_keep.py`, `drift_lock.py`, `back_textile_keep.py` -> `work/keep_h.npy` (4,625 faces
kept exactly), `work/groups_h.npy`:
- every face touching a vertex with hand + finger weight > 0.5 (2,079: fingers, palms, gauntlet backs; the fitted
  sword grip), small pieces (379), soles (faces below 6 cm, 305);
- the helm front half (327: painted T visor, its gold edge and the brims in front);
- the plume strands (591): at 70 % the thin ribbons moved 8-11 mm at rest and up to 36 mm in Hit;
- 4 cm patches around four interior cuirass points (108; pieces 1 and 7 overlap inside the chest; these points gave
  the 24.5-30.5 mm maximum in Fidget and Hit at every step);
- one drift-lock round (`texture_drift.py` on config d r80: 26 faces / 237 cm2 over 40 on the tabard chest; +501
  faces), then 3 cm patches at the two spots it left (a gold fleck on the right shoulder front, the chest centre);
- the tabard back's cloth (green/white/red faces behind y = -0.05 above 0.9 m plus one ring, +284): at the body ratio
  the back leaf heraldry smeared and the white/green split moved, while the drift check stayed under 40.

Groups: rest of the helm 75 % (at 65 % a faint crease showed on the lower side in clay), crest 50 %, the body
(plates, gauntlet cuffs, vambraces, tabard front) takes the ladder budget: 68 % at the pick.

## Ladder

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 8,898 | | | | |
| a: hands, small, soles, visor; head groups 70 % | r80 / r75 | 7,152 / 6,694 | 4.97 / 24.53, 6.29 / 36.35 | 0.992 / 0.986 | 0.991 / 0.985 | pass / fail |
| b: + plume kept, helm/crest 80 % | r83 / r80 | 7,394 / 7,166 | 4.34 / 24.53, 4.95 / 30.53 | 0.994 / 0.992 | 0.991 / 0.989 | pass / fail |
| c: + interior chest patches | r80 | 7,204 | 4.90 / 14.23 | 0.993 | 0.989 | pass |
| d: helm 75 %, crest 60 % | r80 | 7,124 | 4.90 / 14.23 | 0.993 | 0.989 | pass; tabard chest heraldry smeared, gorget fleck |
| e: d + one drift lock | r83 | 7,416 | 4.92 / 21.40 | 0.992 | 0.991 | pass; gold fleck on the right shoulder |
| f2: c + tabard cloth as its own group at 85 % | r82 | 7,380 | 4.73 / 21.51 | 0.992 | 0.990 | pass; big chest faces drift 254 cm2 |
| g: e + shoulder/chest patches | r83 | 7,472 | 4.75 / 21.40 | 0.993 | 0.992 | pass; back heraldry smeared |
| h2: g + back cloth kept, helm 65 %, crest 50 % | r83 | 7,462 | 4.78 / 16.39 | 0.992 | 0.992 | pass; helm side crease in clay |
| **h3: h2 with the helm at 75 %** | **r84** | **7,492** | **4.72 / 16.39** | **0.992** | **0.992** | **pick** |
| h3 | r83 | 7,420 | 5.18 / 16.39 | 0.992 | 0.992 | fail (p99) |

Also tried (on c): MeshLab's planar quadric term (worse: r80 p99 5.51) and texture weights 0.5 / 2.0 (within noise of
1.0; kept 1.0 for texture fidelity). `scripts/region_error.py` on b r80: the body plates caused all of the over-p99
error (body p99 6.1 mm; helm/crest 2.8, cuffs 3.8). The body was already reduced once in the source build
(15k Smart Topology -> 8,898 with the gauntlets protected), so the plates do not go below about 65-68 % at these limits.

Pick: `h3 r84`. Texture drift after the lock: 6 faces over 40 (27.6 cm2, thigh plate side and tabard skirt edge),
p99 22.7. Close-ups straight from the GLBs (`scripts/glb_close.py`, file normals):
`review/glbclose/sheet_h3_head.png` (helm front, three-quarter, side, back), `sheet_h2_a.png` / `sheet_h2_b.png`
(torso, back, tabard, pauldron, hands, knees, boots, Attack, Death; h2 differs from the pick only in the helm-rest
ratio), `sheet_tiers.png` (source vs reduced in tiers A/B/C, textured and clay, including the sword grip standing and
in Attack), and the earlier rounds `sheet_de_*.png`, `sheet_g_body.png`. `review/ladder_sheet.png` is the h3 ladder.

## Build

`cand_glb.sh h3 Cand_84` (`export_cand.py` -> `swap_lod0.py` onto the source) -> `build_lods.py` -> `shrink_shadow_lods.py`
(inset shadow LODs, as the source build) -> `carry_variants.py`: `export/mm7_m230.glb`, 7.6 MB (source 7.7 MB).
Nodes, materials (incl. region mask/ramps extras), images, textures, skin, 8 clips and `KHR_materials_variants`
(`m230_a/b/c`) match the source; the variants are on all 8 colour/shadow primitives. Winding check: 0 inverted closed
parts.

LODs (`build_lods.py`, `tools/build_actor_lods.py` on the body alone, 8 influences on LOD1-3 like the source): ratios
0.5 / 0.18 / 0.07 with protected points (top 5 mm, vertices within 1 mm of the floor in any Death frame and within
12 mm in any Dead frame: 131 points). The playbook's side/end extremes and a 4 mm Death floor lock (193 points) made the
Blender decimation collapse the torso and thighs at LOD3; 0.06 gave 446
triangles that read worse than the source's 530.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source | 8,898 | 4,447 | 1,599 | 530 |
| reduced | 7,492 | 3,745 | 1,346 | 522 |

- `work/lod_check_final.json` (`lod_check.py`, every frame of every clip): every LOD keeps the 1.700 m top and LOD0's
  lowest point in every clip (Death -19.9 mm, Dead +1.0 mm, as LOD0; the source's LOD2/3 went to -7.7 / -2.0 mm in
  Dead); one face stretches over 20x in Death at LOD2 only. `work/lod_check_src.json` is the source.
- `review/lods/sheet.png`: source vs reduced LOD0-3 (standing, attack, corpse, helm).
- `scripts/grip_check.py`: all 1,519 LOD0 vertices with hand + finger weight > 0.5 keep their bind positions
  (max 0.0006 mm) and weights, so the fitted grip is unchanged at LOD0 (`work/grip_check.log`).

**Sword:** `export/mm7_m230_sword.glb` is byte-identical to the source attachment (654 / 326 / 116 / 38). The grip
faces would have to stay exact, so at most a few hundred triangles of blade and guard could go; not worthwhile.

## Viewer

`review/viewer/` (source vs reduced, tiers A/B/C; `viewer_variants.py` bakes the ramps; `viewer_sword.py` adds the
unchanged longsword under the `Sword` joint for review only). `tools/run_creature_review.py ... check`: 48 switches,
no console errors. http://127.0.0.1:8912/level_generation/creatures/mm7_m230_reduce_claude/review/viewer/index.html

## Open issues

- The saving is 16 % at LOD0 (8,898 -> 7,492): 52 % of the mesh is kept exactly (gauntlets and fingers 2,079, helm
  front, plume, tabard back, drift lock) and the plates were already reduced once by the source build.
- The source LOD3 is barely reduced (530 -> 522); below that the corpse and torso break up.
- Clay renders of the source show shading creases on the cuirass; the reduced plates are a little smoother there.

## Install (later, user decision; not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m230_reduce_claude/export/mm7_m230.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m230_reduce_claude/export/mm7_m230_sword.glb --world mm7
```

then the actor binding from `../mm7_m230_claude/integration/actors.yml` and its README. Rollback: install
`work/mm7_m230_source_pre_reduce.glb` (+ `_sword`). Record the result in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md)
when installed.

## Reproduce

`REA_GLB=<project>/work/mm7_m230_source_pre_reduce.glb REA_NODE=M230 bl.sh import_source.py` -> `REA_PROTECT=B_Head
bl.sh dump_mesh.py`, `bl.sh dump_groups.py`, `extract_basecolor.py work/mm7_m230_source_pre_reduce.glb`,
`REA_SMALL=80 small_pieces.py` -> `m230_regions.py`, `textile_frac.py` -> plume set (`regions == 4`) and
`patch_keep.py - work/patch1.npy 0.114,0.011,1.185 0.017,0.027,1.149 0.02,0.037,1.153 -0.049,0.024,1.221` ->
`m230_sets.py c work/plume.npy work/patch1.npy` (copied to d) -> `REA_GROUP_RATIOS=2:0.75,3:0.6 run_ladder.sh d ...`
-> `texture_drift.py r80`, `drift_lock.py work/keep_d.npy work/keep_e.npy r80` ->
`REA_PATCH_R=0.03 patch_keep.py work/keep_e.npy work/keep_g.npy -0.271,-0.101,1.121 -0.013,-0.272,1.113` ->
`back_textile_keep.py work/keep_g.npy work/keep_h.npy` -> `REA_KEEP_FACES=work/keep_h.npy REA_GROUPS=work/groups_h.npy
REA_GROUP_RATIOS=2:0.75,3:0.5 REA_HEIGHT_M=1.664 run_ladder.sh h3 $(REA_GROUP_RATIOS=2:0.75,3:0.5 totals.py h
0.70,0.68,0.66)` -> `cand_glb.sh h3 Cand_84`, copy to `work/pick_lod0.glb` -> `REA_LOCK_SIDES=0 REA_FLOOR_M=0.001
REA_FLOOR_DEAD_M=0.012 REA_LOD_RATIOS=0.5,0.18,0.07 REA_LODS_OUT=work/lfd.glb bl.sh build_lods.py` ->
`shrink_shadow_lods.py`, `carry_variants.py` -> `export/mm7_m230.glb`; checks `grip_check.py`, `lod_check.py`
(REA_NODE=M230), `lod_views.py`, `glb_close.py`, `viewer_variants.py`, `viewer_sword.py`, `viewer_manifest.py`.

## Clips updated (2026-10-20)

The source project's walk/run ankle twitch was fixed after this reduction (`../mm7_m230_claude/scripts/foot_level.py`). `scripts/transplant_clips.py` copied the re-exported clips into `export/mm7_m230.glb` and every `review/viewer/*.glb` (geometry, LODs, materials and variants unchanged), and `work/mm7_m230_source_pre_reduce.glb` is now that re-export. After any later re-export of the source, run `python3 scripts/transplant_clips.py ../mm7_m230_claude/export/mm7_m230.glb export/mm7_m230.glb export/mm7_m230.glb`.
The walk bob fix (`walk_bob.py`, same day) was carried over the same way.

**Accepted 2026-10-20**; installed 2026-10-20 from `../mm7_batches/BATCH_A_stage/` (listed in REDUCTION_LEDGER.md).
So was the Hit/Death foot-roll fix (flatness-weighted, smoothed roll; same day); the stage was rebuilt.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -3.1.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m230.glb export/mm7_m230.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m230.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/h07`](../gait_rollout_20261031/h07/README.md) appended Walk2 (humanoid set Armed-Walk, 0.80 s, arms turned out 7/6 deg past the thigh plates), Jog (Unarmed-Run-Forward, 0.70 s) and Sprint (Unarmed-Sprint, 0.58 s) to the installed
`assets_source/worlds/mm7/models/mm7_m230.glb` and installed it (existing clips, meshes, skins and materials
byte-identical). The sword arm is lifted (eased, up to 25 deg) in the half of the run loop where the right knee comes
through, so the blade clears the thigh. Bindings for the coordinator (`h07/bindings.yml`): walking: Walk2, stride_length 1.8664, run: Jog, run_stride_length 3.2987, sprint: Sprint, sprint_stride_length 4.3344. `Running` is kept in
the GLB but no longer bound for locomotion. Rebuild: `level_generation/creatures/gait_rollout_20261031/h07/scripts/rebuild.sh m230`
(from `h07/work/mm7_m230_pre_gait.glb`, the rollback source). A far-LOD repair rerun, a floor fix or any re-export of this
model must re-graft these clips: copy the new source over `h07/work/mm7_m230_pre_gait.glb` and rerun the rebuild, then
install with `tools/install_model.py`.
