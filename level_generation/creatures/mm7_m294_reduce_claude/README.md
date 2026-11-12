# MM7 Necromancer (`m294`, Necromancer / Speaker for the Dead / Queen of the Dead) reduction (2026-10-21)

User request (batch F): "handle batch F ... check if they had their tris reduced". The Necromancer had not
(LOD0 12,015 / 6,006 / 2,161 / 719). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md),
no-retexture branch: no part needed rebuilding, so the textures, region mask, tier ramps, specular extras, rig and clips
stay as exported. No Meshy credits. **Not installed** (batch F rule: nothing in `assets_dev/` or `assets_source/`;
`mm7_m294_claude/` untouched). Every Blender/Python step runs memory-capped (`scripts/cap.sh`).

Scripts: ladder, UV weights, LOD build, LOD check, gate copies and viewer from `mm7_m262_reduce_claude/`; region
tooling (`vis_faces.py`, `spot_lock.py`, `visible_only.py`, `dark_slivers.py`, `group_error.py`, `close_human.py`,
`glb_close.py`) from `mm7_m426_reduce_claude/` (Warlock). The gates `gates.py`, `gates_summary.py`, `armik.py`,
`cfg.py` (+ `creature.json`), `sole_probe.py`, `stretch_where.py` and `shrink_shadow_lods.py` are copies from
`mm7_m294_claude/scripts/`. New: `master_labels.py` (garment/piece labels from the production master).

Source: `../mm7_m294_claude/export/mm7_m294.glb` (sha256 `025522da...`; the latest export: `export_info.json`,
`lods.json` and the GLB are all from the 13:08-13:09 build of 2026-10-20, after the last review change), copied to
`work/mm7_m294_source_pre_reduce.glb` (rollback). One node `M294`, one merged material `M294_A` (body + head atlas
2080x1024), tier variants `M294_B` / `M294_C` (one region: the tunic's purple), 114 joints, 4 influences, seven clips
(Standing, Walking, Cast, Hit, Death, Dead, Fidget), palm sockets. No attachment.

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch F export | 12,015 | 6,006 | 2,161 | 719 |
| **reduced** | **9,125** | 4,562 | 1,641 | 547 |

LOD0 -24.1 %. The 25-35 % aim was reached only by cutting things that showed (r75, 9,005, failed the error limit;
see the ladder): the production chain had already reduced the cape, hair and legs (`reduce_rigged.py`: 3,974 -> 2,199,
1,722 -> 1,299, 2,066 -> 1,500), and 4,741 triangles (39 %) must stay exact: the dense Meshy face (1,601), the cape's
ragged panel edges (856), circlet, eyes, knee chevrons, hem, soles, thumbs and the lock rounds below. The rest is cut to
about half on average already (the tunic with the palms to 44 %).

## Regions (`make_groups.py`)

Weld 8,089 -> 1,565 open edges, 4 coincident vertices with other weights kept apart, 12,015 triangles (no two-sided
doubles). The GLB carries no part labels: each vertex takes `garment` and `piece` from the production master
(`master_labels.py`, `../mm7_m294_claude/work/rig_v6.blend` read only, max 0.001 mm apart), majority per face;
rest-pose visibility from `vis_faces.py` (9,855 of 12,015 visible).

| label | region | free faces | ratio |
|---|---|---:|---|
| 0 | tunic, sleeves and the palms (shared cut, the ladder ratio) | 2,294 | 44 % (fills the budget) |
| 1 | visible neck skin outside the face front | 168 | 75 % |
| 2 | head skin hidden in the rest pose (scalp under the hair) | 463 | 35 % |
| 4 | fingers and claws (hand faces over 7.5 cm from the wrist) | 848 | 60 % |
| 5 | cape interior (panels, lining) | 988 | 85 % |
| 6 | hair shell below the head | 676 | 75 % |
| 7 | legs and boots | 727 | 65 % |
| 8 | other faces hidden in the rest pose | 523 | 80 % |
| 9 | hidden backs of the eyes, inner lips and the circlet's inner side (`groups_n.npy`) | 587 | 60 % |

Kept exactly (`work/keep_q.npy`, 4,741 faces):
- the whole face front (1,601: brows to chin; a cut of the cheeks/temples at 70 % gave dark blotches on the cheeks,
  ladder d), the visible eyes, circlet and lips, pieces of up to 300 faces (cape strips, front flap);
- the cape's open-edge ring (856 faces: ragged panel edges and strip tips), the tight hem and front flap (garment 17),
  gold texels (the knee chevrons), the soles (below 6 cm);
- the hair cap above 1.45 m (408: the hair around the face and crown picked up dark slivers at the circlet and
  temples at 75-80 %);
- one error lock (`err_lock.py`, 12 mm, 2 cm, Cand_77 of ladder b: back cape at the hips in Death, hair at the nape in
  Hit), one drift/sliver lock round (`texture_drift.py` + `dark_slivers.py` dark and light + `visible_only.py`, 1.5 cm),
  spot locks for a light fleck on the back (-0.181, 0.076, 1.319), the wrist cuff edges (8 points, 2 cm), both thumbs
  (3 cm: the thumb tips came back pinched) and both armpit fronts (3 cm, ±0.154, -0.092, 1.273: a short new edge
  stretched 4.1x in Death and 3.4x in Cast).

## Ladder (REA_HEIGHT_M 1.70: p99 <= 5.1 mm, max <= 25.5 mm)

| step | config | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a | cape 80 %, hair 70 %, face front kept | 9,127 | 4.57 / 34.0 | 0.994 | 0.997 | fail (cape 34 mm in Death) |
| d | b + error lock, cape 85 %, face rim 70 %, hands 45 % | 8,765 | 4.49 / 23.9 | 0.995 | 0.997 | pass; cheek blotches, hair slivers |
| e/f | face front kept, + drift lock | 9,007 | 4.69 / 23.9 | 0.995 | 0.997 | pass; slivers moved to the hair cap |
| h | + hair cap kept, back fleck | 9,007 | 4.99 / 23.9 | 0.995 | 0.997 | pass; tunic at 38 %, fingertips blunt (hands 45 %) |
| j | hands 40 %, hidden head 35 % | 9,005 | 4.87 / 23.9 | 0.996 | 0.997 | pass; thumbs and fingertips pinched |
| l | palms in the shared cut, fingers 60 % | 9,125 | 5.07 / 23.9 | 0.995 | 0.997 | pass; wrist cuff slivers |
| n | + wrist locks, hidden eye/lip/circlet backs 60 % | 9,005 | 4.99 / 23.9 | 0.996 | 0.997 | pass; thumb tips pinched |
| p | + thumbs kept | 9,125 | 4.91 / 23.9 | 0.996 | 0.997 | pass (r75 9,005: 5.30, fail); armpit edge 4.1x |
| **q r76** | **+ armpit fronts kept** | **9,125** | **5.00 / 23.9** | **0.996** | **0.997** | **picked** (r75 9,005: 5.40, fail) |

Per region (`group_error.py`, Cand_76 of q, every 4th frame; `work/group_error_p76.log` for p): tunic p99 6.4 / max
15.3 mm (Hit), face side 2.4, hidden head 6.9, palms 3.1, fingers 2.3, cape 10.1 / 19.6 (Death: the robe chains of the
lying cape), hair 8.4 / 23.0 (Death), legs 5.8, hidden 5.3, kept 0. Flecks (`texture_drift.py`, `dark_slivers.py`
dark and light, each through `visible_only.py`): 0 / 0 / 0 visible.

Close-ups (source / r76, back faces culled, textured and clay): `review/close/sheet_r76_head.png` (face front, 3/4,
side, head and hair back), `sheet_r76_hands.png` (both hands, the left hand in the Cast, both shoulders),
`sheet_r76_body.png` (tunic front and back, hem, knee chevrons, boots, cape side, back and hem),
`sheet_r76_poses.png` (Walking front/back, Cast at the release and frame 16, Hit, Death 8/16/24 from the back, Dead).
Straight from the GLBs (`glb_close.py`): `review/glbclose/sheet_r76.png`. No feature changed in the textured views.

## Build

`TOKEN=<lease> scripts/build_export.sh ladder_q.blend Cand_76`: `export_cand.py` (floor clamp at the source's own
lowest rest point, -2.0 mm; 0 vertices moved) -> `swap_lod0.py` (into the rollback source) -> `build_lods.py`
(`tools/build_actor_lods.py`, the source chain's ratios 0.5 / 0.18 / 0.06, 4 influences; 194 protected points: the
bounding extremes and every vertex within 4 mm of the floor in Death/Dead) -> the source chain's
`shrink_shadow_lods.py` -> `carry_variants.py` -> `export/mm7_m294.glb` (sha256 `599fce64d1ba3bf0...`, 7.2 MB;
source 8.2 MB).

Against the source: nodes (sockets included), skin joints and inverse bind matrices, materials (variants, region
mask/ramps, specular extras), textures and images, and every animation sampler's input and output bytes are
identical; only the mesh primitives changed. The staged binding therefore applies unchanged.

## Checks

| check | source | reduced |
|---|---|---|
| arm stretch p99 L / R (`gates.py`, `BODY_GARMENTS=0,1,2,13,17`, every half frame): Standing | 1.16 / 1.21 | 1.17 / 1.22 |
| Walking | 1.24 / 1.22 | 1.30 / 1.22 |
| Cast | 2.35 / 1.96 | 2.26 / 2.17 |
| Hit | 2.18 / 1.85 | 2.14 / 2.01 |
| Death | 2.36 / 2.28 | 2.31 / 2.52 |
| Fidget | 1.55 / 1.48 | 1.57 / 1.49 |
| arm stretch max, worst clip (Death) L / R | 3.30 / 2.85 | 3.30 / 2.86 |
| robe/cape stretch p99 (max), worst clip (Death) | 2.38 (5.45) | 2.38 (5.45) |
| hand stretch (G5, rigid hands) | 1.00 | <= 1.01 |
| wrist swing, twist range | as listed in `review/gates_g_source.json` | identical (same rig and clips) |
| hand in body (G6, closed skin) | <= 8 cm proximity to the open cape, no penetration | the same |
| soles (`sole_probe.py`): Standing / Walking / Cast / Hit / Fidget | 0.3 / -0.3..2.0 / 0..0.6 / -0.6..1.1 / 0.3 cm | identical |
| LOD check: height, width (all LODs) | 1.70 m, 0.94-0.96 m | 1.70 m, 0.96 m |
| LOD check: lowest point Dead / Death, LOD0-3 (cm) | -2.8/-2.8/-2.8/-2.1, -4.4/-4.4/-4.4/-4.1 | -2.8 at every LOD, -4.4 at every LOD |
| LOD check: faces stretched over 20x per clip, LOD0 / 1 / 2 / 3 | 0-1 / 0-2 / 0-1 / 0 | 0-1 / 0-2 / 1-2 / 0 |
| `check_winding.py` | 0 inverted | 0 inverted |

Gate copies: `gate_import.py` + `gate_attrs.py` (garment per vertex from `../mm7_m294_claude/work/rig_v5.blend`, the
master the source gates ran on; `piece` by majority per connected part). Reports: `review/gates_g_source.json`,
`review/gates_g_reduced.json`, `work/lod_check_{source,reduced}.json`. The source's lowest points below the floor
(Walking -7.0 cm, Cast -4.8 cm) are cape strip tips and are unchanged.

## Viewer

http://127.0.0.1:8912/level_generation/creatures/mm7_m294_reduce_claude/review/viewer/ : batch F export (r100) and
reduced (r76, default) for tiers A, B and C, tier ramps baked by `viewer_tiers.py`, clips from the source viewer
manifest (`viewer_manifest.py`). `tools/run_creature_review.py ... check`: 42 clip switches, no console errors.

## For the user to review

- 24 % off LOD0 (12,015 -> 9,125), short of the 25-35 % aim: the face, the cape's ragged edges, circlet, eyes, thumbs
  and lock rounds keep 39 % of the mesh exact, and the cape, hair and legs were already reduced in production. The
  next step down (9,005) failed the error limit; earlier variants at that count pinched the thumbs or put dark slivers
  on the hair.
- The tunic and palms carry the cut (44 %). Textured they match the source; in untextured views the collarbones and
  the chest folds are a little softer and the elbows slightly faceted.
- Right arm stretch p99 rises slightly in Death (2.28 -> 2.52) and Cast (1.96 -> 2.17); the maxima equal the source's.
- Shading: the reduced mesh uses plain smooth normals (the source had custom normals); the face is kept exactly, but
  in untextured GLB views its eye and mouth creases read a little differently.
- LOD2 has 1-2 faces per clip stretched over 20x (source 0-1); LOD1 and LOD3 match the source.

## Install (NOT run; batch F rule)

Replaces the batch F export of `mm7_m294_claude/` (same node names, materials, variants, sockets and clips; no
attachment):

```sh
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py level_generation/creatures/mm7_m294_reduce_claude/export/mm7_m294.glb   # 0 inverted (checked)
python3 tools/install_model.py level_generation/creatures/mm7_m294_reduce_claude/export/mm7_m294.glb --world mm7
```

The `actors.yml` binding is the source project's staged one, unchanged:
`../mm7_m294_claude/export/actors_binding.yml` (= `../mm7_m294_claude/actors_m294_binding.yml`; descriptors
Necromancer A/B/C, model `worlds/mm7/models/mm7_m294.glb`, scale 120.0, attacks play Cast), appended to
`assets_dev/worlds/mm7/models/actors.yml` when the model is installed.

Rollback: `work/mm7_m294_source_pre_reduce.glb` (= `../mm7_m294_claude/export/mm7_m294.glb`, sha256 `025522da...`).

## Reproduce

`REA_GLB=<rollback source> REA_NODE=M294 import_source.py` -> `dump_mesh.py`, `dump_faces.py`, `dump_weights.py`,
`vis_faces.py`, `master_labels.py` -> `make_groups.py` (groups.npy, keep_base.npy, garment_face.npy) -> keep_b
(keep_base without the face rim) -> ladder b (`REA_GROUP_RATIOS=1:0.75,2:0.45,3:0.5,5:0.9,6:0.75,7:0.7,8:0.8,9:0.7`) ->
`REA_CAND=Cand_77 REA_ERR_MM=12 REA_LOCK_R=0.02 err_lock.py -- work/keep_b.npy work/keep_d.npy` -> keep_e = keep_d +
face rim -> ladder e at 0.74 -> `REA_MIN_AREA=0 REA_LOCK_R=0.015 drift_lock.py keep_e keep_f e74` (visible drift,
dark and light slivers combined) -> keep_g = keep_f + hair above 1.45 m -> `spot_lock.py keep_g keep_h 0.02
-0.181,0.076,1.319` -> groups_l (palm label 3 -> 0) -> `spot_lock.py keep_h keep_m 0.02` (8 wrist points, see above) ->
keep_n = keep_m without the hidden eye/lip/circlet faces, groups_n (those faces -> 9) -> `spot_lock.py keep_n keep_p 0.03
-0.33,-0.19,0.814 0.278,-0.193,0.807` -> `spot_lock.py keep_p keep_q 0.03 -0.154,-0.092,1.273 0.154,-0.092,1.273` ->
`REA_WEIGHTS=component REA_KEEP_FACES=work/keep_q.npy REA_GROUPS=work/groups_n.npy
REA_GROUP_RATIOS=1:0.75,2:0.35,4:0.6,5:0.85,6:0.75,7:0.65,8:0.8,9:0.6 TOKEN=<lease> run_ladder.sh q 0.77,0.76,0.75` ->
checks (`texture_drift.py`, `dark_slivers.py`, `REA_LIGHT=1 dark_slivers.py`, `visible_only.py`, `group_error.py`,
`CULL=1 close_human.py`, `close_sheet.py`) -> `build_export.sh ladder_q.blend Cand_76` -> `lod_check.py`,
`check_winding.py`, gate copies + `gates.py` + `sole_probe.py`, `glb_close.py` -> `viewer_tiers.py` (r100, r76),
`viewer_manifest.py`. The MeshLab venv is `REA_VENV` in `run_ladder.sh` (pymeshlab, numpy, scipy).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Cast sinks to -5.7; Fidget sinks to -5.0; Hit sinks to -3.8; Standing sinks to -3.2; Walking sinks to -8.4; corpse at -3.3; dying sinks to -4.5; standing at -3.0; walking sinks to -8.4.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m294.glb export/mm7_m294.glb --lift-joints Cast Dead Death Fidget Hit Standing Walking --lift-only 'B_Skirt*,Robe_*,…' --ground-loop Standing --ground-loop Walking --raise Cast --raise Fidget --raise Hit --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m294.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [h11](../gait_rollout_20261031/h11/README.md) appended `Jog` (chase) to the installed
`assets_source/worlds/mm7/models/mm7_m294.glb` (library-loop legs, this model's own `Walking` arms, robe/cape chains
re-simulated on the new motion); existing clips are unchanged and the bindings are in
`../gait_rollout_20261031/h11/bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h11/scripts/rebuild.sh m294`
(from `h11/work/mm7_m294_pre_gait.glb`). A far-LOD repair, head-bob, floor-fix or reduction rerun, or any re-export
of this model, must re-graft these clips (copy the new source over the pre-gait copy and rerun that rebuild, or graft
them with `claude_shared/graft_clips.py`).

## Anim fix (2026-11-11, MM6–MM8 audit)

Jog recomposed with a lower knee and shorter strides (cape cloth bad 24.0 -> 14.2 %; `run_stride_length` 2.2003).
Details: [mm7_m294_animfix_claude](../mm7_m294_animfix_claude/README.md).
