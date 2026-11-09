# MM7 Dwarf (`m190`, Dwarven Soldier / Lieutenant / Commander) reduction (2026-10-20)

User: "do the tris reduction playbook on these 5" (the five MM7 batch-C humanoids; this project is m190 only). Default
route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that
keeps the UVs, so the textures, the three tier variants (`KHR_materials_variants`) and the region ramps stay valid. No
Meshy credits. **Not installed** (batch C: the user installs later).

[Review viewer](review/viewer/index.html) (source vs reduced, tiers A/B/C, all eight clips, axe in its socket)

## Source

`../mm7_m190_claude/export/mm7_m190.glb` and `mm7_m190_axe.glb` (accepted 2026-10-20, after the skirt reweight),
copied to `work/mm7_m190_source_pre_reduce.glb` and `work/mm7_m190_axe_source_pre_reduce.glb` (rollback sources,
byte-identical). One merged body + head atlas material per tier (`Dwarf_A/B/C`, 2080x1024, head half u > 0.51), node
`Dwarf`, 57 joints, 4 influences at LOD0 (8 slots at LOD1-3), shadow LODs, clips Standing, Walking, Running, Attack,
Hit, Death, Dead, Fidget. Bind height 1.400 m (the horn tips; the helmet spike reaches 1.354 m). Weld (identical
weights only): 6,585 -> 718 open edges, 4 coincident vertices with other weights (kept apart by `decimate_tex.py`),
10,027 triangles in and out. Scripts start from `../mm7_m406_reduce_claude/scripts/` (paths, node and names adapted).

The source was already reduced once in its build (15.76k -> 10.03k with head and hands protected), so its surface is
lean: per-region budgets and a 70-80 % body cut failed the error limits everywhere (MM6 Dwarf lesson), and the free
faces take only a gentle shared cut.

## Where the triangles are (source shells from `scripts/source_pieces.py` + `m190_pieces.py`)

The runtime GLB drops the source's `piece`/`garment` attributes, so `source_pieces.py` reads them from the source
master `../mm7_m190_claude/work/rig_v6.blend` (read only) and `m190_pieces.py` maps them by rest position (max 0.0005
mm; `review/labels/pieces.png`).

| shells | faces | |
|---|---:|---|
| 0 torso, head, face, beard, back hair, collar | 2,592 | 1,698 in the head set |
| 4/5 hands (sixth finger removed by script) | 1,682 | kept exactly |
| 1/2 boots, 6 legs | 1,617 | 287 sole faces |
| 9/10 braids, 21/22 braid ends | 700 | kept exactly |
| 11/12 bracers | 500 | gold rims kept |
| 13/14 shoulder guards, 19/20 guard rims | 700 | rims kept |
| 8 helmet (rim, ridge, horn rings, top spike) | 488 | |
| 17/18 horns | 457 | tips kept |
| 7 mail skirt, 3 ragged skirt | 786 | |
| 15/16 bare upper arms | 322 | |
| 23 buckle, 24/25 eyes | 183 | kept exactly |

## Keep set (`scripts/m190_sets.py`, pick = set `j`, `review/labels/keep_j.png`)

Kept exactly (`work/keep_j.npy`, 5,113 faces): both hands and every face touching a vertex with hand + finger weight
> 0.3 (bracer ends); the eyes; braids and braid ends; the guard rims; the buckle; the boot soles (faces below 6 cm);
the gold (`work/gold.npy`, 961 faces by base-colour hue on helmet, horns, bracers, boots, legs and buckle: helmet rim
and ridge, horn rings, bracer and boot rims; `review/labels/gold.png`); the helmet top spike (helmet faces above
1.255 m); the horn tips (horn faces above 1.33 m); the face front (head-set faces within 7 cm of the face centre);
the mail-skirt hem band (within 3 cm of its lowest point per 15-degree sector: the shared cut dented the front hem,
`review/glbclose/sheet_i87_legs.png`); 3 cm patches at the max-error spots of the first ladders (beard front, lower
back, upper back under the hair, shoulder sides, both sides: `work/patch_i.npy`, `probe_max.py`).
Everything else (4,914 faces) takes one shared cut. The region groups (`groups_*.npy`: beard, hidden scalp, helmet
dome, horns, guards, skirts, hidden body, torso, arms) are kept for analysis only; every grouped config failed.

## Ladder (limits for the 1.400 m height: p99 4.2 mm, max 21.0 mm; IoU >= 0.98, SSIM >= 0.93)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 10,027 | | | | |
| b: gold + one ring kept, groups 50-80 %, body 70 % | r83 | 8,449 | 8.73 / 34.39 | 0.9916 | 0.9840 | fail (hidden scalp, under-skirt skin, body) |
| c: no gold ring, groups 70-85 %, body 85 % | r88 | 8,879 | 5.72 / 34.48 | 0.9952 | 0.9898 | fail (rest pose alone p99 7.5) |
| d: groups 75-90 %, body 90 % | r90 | 9,071 | 4.12 / 30.43 | 0.9951 | 0.9894 | fail (max: beard front, Attack) |
| e: d + beard patch | r90 | 9,083 | 4.04 / 21.39 | 0.9950 | 0.9896 | fail (max) |
| f: torso/arms split, ragged hem kept, patches | r90 | 9,023 | 4.62 / 25.25 | 0.9958 | 0.9894 | fail |
| g: f keep set, one shared cut | r89 / r88 | 9,001 / 8,853 | 3.73 / 18.92, 4.09 / 21.29 | 0.9974 / 0.9966 | 0.9891 / 0.9878 | pass / fail (max) |
| h: g without the ragged hem kept | r89 / r87 | 8,937 / 8,781 | 3.84 / 18.92, 4.18 / 21.29 | 0.9971 / 0.9963 | 0.9888 / 0.9875 | pass / fail (max) |
| i: h + shoulder / upper-back patches | r87 | 8,803 | 4.08 / 18.92 | 0.9961 | 0.9876 | pass; mail-skirt front hem dented |
| **j: i + mail-skirt hem band (3 cm)** | **r89** | **8,995** | **3.83 / 18.92** | **0.9967** | **0.9897** | **pick** (free faces at 79 %) |
| j | r88 | 8,847 | 4.25 / 18.92 | 0.9961 | 0.9875 | fail (p99) |
| k: j with a 2 cm hem band | r89 / r88 | 8,981 / 8,831 | 3.86 / 18.92, 4.32 / 18.92 | | | pass / fail, no real gain |

The pick is the lowest passing step that also looks right in the close-ups: i87 (8,803) passed too but dented the
mail skirt's front hem. The 18.9 mm maximum is in Death frame 57 (falling, collar/upper back under the hair) at every
step. `scripts/err_map.py` (per-vertex error) showed that the worst error sits on never-visible surfaces (scalp under
the helmet, body under the beard and back hair, skin under the skirts) and that the visible error is spread thinly
over the whole lean surface, so no single region could take a deeper cut. Texture drift (`texture_drift.py` +
`drift_visible.py j_r89`, visible faces): 22 faces over 40 (325 cm2), all large mail-skirt and lower-back faces of
the same chain-mail print; the close-ups show only a slightly darker patch above the front hem, so no lock round.

## Build

`cand_glb.sh j Cand_89 kn` with `REA_KEPT_NORMALS=1` (21,654 corners from unchanged source faces, 2,650 from kept
smooth vertices, 2,681 computed) -> `export_cand.py` -> `swap_lod0.py` (`work/j89_lod0.glb`) -> `spike_points.py
j_r89` (helmet spike tip + 4 x 4 spike points, each horn's tip cluster within 1.5 cm and 3 x 2 curve points; 27) and
`floor_points.py` (`REA_FLOOR_MM=30`, 24 Dead/Death floor contacts) -> `build_lods.py` (`tools/build_actor_lods.py`, 8
influence slots as the source, ratios 0.5 / 0.2 / 0.066, 51 protected points) -> `shrink_shadow_lods.py` (the source
project's script) -> `carry_variants.py` -> `check_winding.py` (0 inverted closed parts): `export/mm7_m190.glb`,
7.65 MB (source 7.71 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 10,027 | 5,013 | 1,803 | 598 |
| reduced body | 8,995 | 4,497 | 1,799 | 590 |
| axe (`export/mm7_m190_axe.glb`, byte-identical copy) | 1,016 | 508 | 182 | 60 |

LOD protected points: with only the horn tip, the collapse placed a neighbour 0.8-2.3 mm above it (LOD1/LOD2 taller
than LOD0), so the tip cluster is protected; with 53 horn/spike points plus 40 floor points (93 of LOD3's ~590
triangles) the LOD3 helmet shell collapsed into the face; the final 51 points keep it intact
(`review/lods/sheet.png`). The 10 mm floor band left the back of the left thigh 4.9 cm under the floor in the Death
fall at LOD3; the 30 mm band fixes it.

The axe stays byte-identical: a clean procedural mesh (8-sided haft at the fist's radius with gold bands, two
crescent blades as thin wedges that go wavy at any cut), already light next to the body and with its own LODs.

Checks:
- `scripts/compare_glb.py` (`work/compare_glb.log`): node names and transforms, skin and inverse binds, materials and
  extras, images, textures, samplers, all eight clips (sampler data), mesh names/extras and the variants extension
  are identical to the source; `KHR_materials_variants` (m190_a/b/c) on all 8 colour/shadow primitives. UVs stay in
  [0, 1] and no LOD face straddles the body/head atlas split.
- `scripts/grip_check.py` (`work/grip_check.log`): all 1,398 LOD0 vertices with hand + finger weight > 0.5 keep their
  bind positions (max 0.0005 mm) and weights exactly, so the fitted fist on the axe haft and the six-finger fix are
  unchanged.
- `work/lod_check_{src,j89}.json`: every LOD keeps the 1.4004 m top (source LODs: 1.4008 / 1.4029 / 1.3992) and the
  source's bounds (LOD3 0.9 cm narrower at the right hand); the lowest point per clip equals the source LOD0's at
  LOD0/LOD1, and Dead lies on the floor at every LOD (0.0001-0.0018 m; source LOD3 0.94 cm above it). Faces stretching
  over 20x: LOD0 as the source; one 7.7 mm2 sliver by the belt (LOD1) and one 12.8 mm2 boot-side sliver (LOD2/3) reach
  20-24x in a few Death/Running/Walking frames (`scripts/lod_probe.py`), the source LODs had none.
- Skirts (`scripts/skirt_poke_glb.py`, the source project's `skirt_poke.py` on the runtime GLB, shells mapped from
  `work/source_pieces.npz`; `work/skirt_poke_export.log`): Walking 0.3 cm (mail) / 0.0 cm (ragged), the same as the
  source GLB; Standing, Attack, Fidget, Hit <= 0.1 cm (source Hit 0.8 cm). Running: ragged skirt 5.7 cm (source GLB
  5.6 cm; the source README's 1.3 cm was measured on the blend before the export's 4-influence limit), mail 0.6 cm
  (source 1.2 cm). No tier runs in game.
- Close-ups straight from the GLBs, source vs pick, textured and clay (`scripts/glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_j89_head.png` (face, beard, braids, helmet, horns, back of the head),
  `sheet_j89_body.png` (torso, back, shoulder guard, both hands, arm, Attack), `sheet_j89_legs.png` (skirts front,
  back and side, Walking, boots, Death).
- Viewer: `review/viewer/` (source vs 89 % pick, tiers A/B/C, axe added under the `Sword` joint for review only by
  `viewer_axe.py`); `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m190_reduce_claude
  --token <lease> check`: 48 switches, no console errors. `review/shots/sheet_tiers_axe.png` (source A and pick A/B/C:
  Standing, Walking 0.5 s, Attack 0.9 s).

## Open points for review

- The saving is modest (10.3 % at LOD0) because over half the mesh is kept exactly (hands 17 %, braids, gold rims,
  face, soles, hems) and the rest was already reduced in the source build; the next step down fails p99.
- A slightly darker patch on the mail skirt just above the front hem (texture drift on large mail faces).
- LOD3 (590) is as crude as the source LOD3 (598); its horns keep their curve (the source LOD3 horns were straight).
- The axe is unchanged (byte-identical).

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m190_reduce_claude/export/mm7_m190.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m190_reduce_claude/export/mm7_m190_axe.glb --world mm7
```

then the binding from `../mm7_m190_claude/README.md` (three descriptors with scales 104.69 / 109.92 / 115.16,
unchanged by this reduction: the model height is the same) and a [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row.
Rollback: install `work/mm7_m190_source_pre_reduce.glb` (+ `work/mm7_m190_axe_source_pre_reduce.glb`) the same way.

## Reproduce

`REA_GLB=<abs path of work/mm7_m190_source_pre_reduce.glb> REA_NODE=Dwarf import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m190_source_pre_reduce.glb` -> `source_pieces.py` ->
`m190_pieces.py` -> `REA_MIN_PIX=6 visibility.py 0.95 1.42` (copy to `work/visible_head.npy`) and `visibility.py -0.01
1.42` (`work/visible_all.npy`) -> `gold_faces.py` (`work/facecol.npy`, `work/gold.npy`) -> `REA_PATCH_R=0.03 patch_keep.py - work/patch_e.npy
-0.034,-0.173,0.967`, then `patch_keep.py work/patch_e.npy work/patch_f.npy -0.079,0.12,0.759 -0.002,0.113,0.744
0.222,-0.06,0.751 -0.03,0.204,0.995` and `patch_keep.py work/patch_f.npy work/patch_i.npy -0.145,0.041,1.022
-0.057,0.142,1.016` -> `M190_HEM=0 M190_EXTRA_KEEP=work/patch_i.npy m190_sets.py j` -> `TOKEN=<lease> run_ladder.sh j j
"" 0.79,0.76,0.73,0.70` -> `err_map.py`, `texture_drift.py`, `drift_visible.py`, `region_error.py`, `probe_max.py` ->
`REA_KEPT_NORMALS=1 cand_glb.sh j Cand_89 kn` (copy `work/glb_j_89kn.glb` to `work/j89_lod0.glb`) -> `spike_points.py
j_r89`, `REA_NODE=Dwarf REA_FLOOR_MM=30 REA_FLOOR_N=24 floor_points.py` -> build as above -> `compare_glb.py`,
`grip_check.py`, `lod_check.py` (REA_NODE=Dwarf), `lod_probe.py`, `lod_views.py`, `skirt_poke_glb.py <glb> 3,7 Walking
...`, `glb_close.py`, `viewer_variants.py`, `viewer_axe.py`, `viewer_manifest.py "MM7 Dwarf" r89 10027 8995`. Blender
scripts run through `scripts/bl.sh` (lease wrapper, `TOKEN`). After a later re-export of the source clips:
`python3 scripts/transplant_clips.py ../mm7_m190_claude/export/mm7_m190.glb export/mm7_m190.glb export/mm7_m190.glb`.

**Installed 2026-10-20** (user acceptance) with `../mm7_batches/BATCH_C_stage/install.sh`; bindings in `../mm7_m190_claude/integration/actors.yml`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Attack sinks to -3.1; Attack sinks to -3.2; Attack sinks to -3.4; dying sinks to -2.5; dying sinks to -2.6; dying sinks to -2.8.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m190.glb export/mm7_m190.glb --lift-joints Attack Dead Death --lift-only 'B_Skirt*,Robe_*,…' --raise Attack --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m190.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [h10](../gait_rollout_20261031/h10/README.md) appended `Walk2` (Armed-Walk, 0.76 s, stride 1.1715) and `Sprint` (0.48 s, stride 2.9071) to the installed `assets_source/worlds/mm7/models/mm7_m190.glb`
(existing clips, meshes, skins and materials byte-identical; pre-gait copy `../gait_rollout_20261031/h10/work/mm7_m190_pre_gait.glb`)
and installed it; the bindings (`walking: Walk2`, `sprint: Sprint`; `Running` stays the run) are applied by the rollout coordinator from `h10/bindings.yml`. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h10/scripts/rebuild.sh m190`. A far-LOD repair, head-bob, reduction or
texture rerun that rebuilds this source must keep or re-graft these clips (copy the new source over the pre-gait copy
and rebuild).
